import os
import random
import shutil
import string
import platform
import subprocess
import tempfile
import textwrap
import lovely_logger as log

from abc import ABC, abstractmethod
from enum import IntEnum, auto
from pathlib import Path
from typing import Optional

from gui.fulfilmentmodel import FulfilmentModel, TablePalette, TreeItem

if platform.system() == "Windows":
    import pywintypes
    import win32com.client

from PySide6.QtCore import QDate, QModelIndex, Qt
from PySide6.QtWidgets import QTableView, QFileDialog, QTreeView

from base.casting import str_bool
from base.date import date_purestr, date_displstr
from gui.common import model_atlevel
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.eventproxymodel import LiabilityTotalsProxyModel
from gui.eventsqlmodel import LiabilitySqlTableModel, Col, RowFormatting
from base.liability import FilterFlags, RowType, HeaderFooterSubtype
from gui.settings import SettingsHandler
from gui.commonwidgets.itemdelegate import EventItemDelegate
from xlsxwriter import Workbook
from xlsxwriter.format import Format
from xlsxwriter.worksheet import Worksheet


class ExportFormat(IntEnum):
    XLSX = auto()
    PDF = auto()


class HiddenDisplayMode(IntEnum):
    NONE = auto()
    SUMONLY = auto()
    FULL = auto()


# =============================================================================
# PDF conversion backends
#
# XLSX->PDF conversion is delegated to a locally installed copy of Microsoft
# Excel, automated differently depending on OS:
#   - Windows: COM automation via pywin32
#   - macOS:   AppleScript automation via osascript (no extra dependency)
# =============================================================================

class PdfConversionError(Exception):
    """Raised whenever conversion of an xlsx file to pdf fails."""


class BasePdfConverter(ABC):

    @abstractmethod
    def is_available(self) -> bool:
        """Whether this converter can run on the current machine right now."""

    @abstractmethod
    def convert(self, xlsx_path: str, pdf_path: str) -> None:
        """Convert xlsx_path into pdf_path. Raises PdfConversionError on failure."""


class WindowsExcelPdfConverter(BasePdfConverter):
    """Converts via COM automation of the locally installed Excel (Windows only)."""

    def is_available(self) -> bool:
        if platform.system() != "Windows":
            return False
        try:
            win32com.client.Dispatch("Excel.Application").Quit()
            return True
        except Exception:
            return False

    def convert(self, xlsx_path: str, pdf_path: str) -> None:
        excel = None
        wb = None
        try:
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False
            wb = excel.Workbooks.Open(os.path.abspath(xlsx_path))
            wb.ActiveSheet.ExportAsFixedFormat(0, os.path.abspath(pdf_path))
        except pywintypes.com_error as e:
            raise PdfConversionError(
                "Не удалось записать файл. Возможно, файл с таким же именем используется "
                "другим приложением или в настройках указан неверный путь"
            ) from e
        finally:
            if wb is not None:
                try:
                    wb.Close(False)
                except Exception:
                    pass
            if excel is not None:
                excel.Quit()
            del wb
            del excel


class MacExcelPdfConverter(BasePdfConverter):
    """Converts via AppleScript automation of the locally installed Microsoft Excel (macOS only)."""

    EXCEL_APP_PATH = "/Applications/Microsoft Excel.app"
    TIMEOUT_SECONDS = 120

    def is_available(self) -> bool:
        return platform.system() == "Darwin" and Path(self.EXCEL_APP_PATH).exists()

    def convert(self, xlsx_path: str, pdf_path: str) -> None:
        xlsx_abs = os.path.abspath(xlsx_path)
        pdf_abs = os.path.abspath(pdf_path)

        # file format 17 == PDF in Excel's "save workbook as" enum
        script = f'''
        set xlsxPath to POSIX file "{xlsx_abs}"
        set pdfPath to POSIX file "{pdf_abs}"
        tell application "Microsoft Excel"
            open xlsxPath
            set theWorkbook to active workbook
            save workbook as theWorkbook filename pdfPath file format PDF file format
            close theWorkbook saving no
        end tell
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as e:
            raise PdfConversionError(
                "Превышено время ожидания экспорта в PDF через Microsoft Excel"
            ) from e
        except FileNotFoundError as e:
            raise PdfConversionError("Не удалось запустить osascript") from e

        if result.returncode != 0 or not Path(pdf_abs).exists():
            details = result.stderr.strip() if result.stderr else ""
            raise PdfConversionError(
                f"Не удалось записать PDF-файл через Microsoft Excel.{(' ' + details) if details else ''}"
            )


def get_pdf_converter() -> Optional[BasePdfConverter]:
    """Returns a usable PDF converter for the current OS, or None if none is available."""
    system = platform.system()
    if system == "Windows":
        converter: BasePdfConverter = WindowsExcelPdfConverter()
    elif system == "Darwin":
        converter = MacExcelPdfConverter()
    else:
        return None
    return converter if converter.is_available() else None


# =============================================================================
# Common base writer
# =============================================================================

class BaseXlsWriter:
    """
    Shared functionality for all xlsx/pdf exporters: temp file handling, the
    save dialog, overwrite confirmation, final copy/cleanup and PDF
    conversion dispatch. Subclasses only build the workbook content.
    """

    BORDER_COLOR: str = "#D0D0D0"
    HEADER_ROWS_NUMBER: int = 4

    # Excel's column-width "characters" unit is calibrated against the width
    # of a digit in the *workbook's default font* — normally ~11pt Calibri.
    # Data cells here use a larger font and mostly Cyrillic text, both wider
    # per character than that baseline, so fewer real characters fit per
    # line than the raw column-width number suggests. These two knobs let
    # you retune the wrap estimate without touching the calculation itself:
    #   - BASELINE_FONT_SIZE: the font size the "characters" unit assumes
    #   - CYRILLIC_WIDTH_FACTOR: extra shrink for wider/bold glyphs (<1
    #     narrows the effective width further, i.e. predicts wrapping
    #     earlier; increase it toward 1.0 if rows now come out a bit tall)
    BASELINE_FONT_SIZE: float = 11.0
    CYRILLIC_WIDTH_FACTOR_LIABILITY: float = 0.87
    CYRILLIC_WIDTH_FACTOR_FULFILMENT: float = 0.93

    SAVE_XLSX_CAPTION = "Сохранить как Excel-таблицу"
    SAVE_XLSX_FILTER = "Таблица Excel (*.xlsx)"
    SAVE_PDF_CAPTION = "Сохранить как PDF-файл"
    SAVE_PDF_FILTER = "Документ PDF (*.pdf)"

    def __init__(self, settings_handler: SettingsHandler, settings_key: str):
        self.settings_handler: SettingsHandler = settings_handler
        self.settings_key: str = settings_key
        self.last_path: str = ""

    # -- temp files -----------------------------------------------------

    @staticmethod
    def _random_suffix(length: int = 14) -> str:
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

    def _make_temp_paths(self) -> tuple[str, str]:
        """
        Returns (temp_xlsx_path, temp_pdf_path) inside the OS temp directory.
        Using tempfile.gettempdir() instead of the working directory avoids
        problems with read-only bundle directories once packaged with PyInstaller.
        """
        temp_dir = Path(tempfile.gettempdir()) / "PlatezhnyiKalendarExport"
        temp_dir.mkdir(parents=True, exist_ok=True)
        suffix = self._random_suffix()
        return str(temp_dir / f"{suffix}.xlsx"), str(temp_dir / f"{suffix}.pdf")

    # -- last used directory / default filenames -------------------------

    def _get_last_dir(self) -> Optional[str]:
        last_path_str = self.settings_handler.settings.value(self.settings_key)
        if last_path_str and Path(last_path_str).is_dir():
            return last_path_str
        return None

    def _set_last_dir(self, file_path: str) -> None:
        self.settings_handler.settings.setValue(self.settings_key, str(Path(file_path).parent))
        self.last_path = file_path

    def _default_file_path(self, filename: str) -> str:
        last_dir = self._get_last_dir()
        return str(Path(last_dir) / filename) if last_dir else filename

    # -- save dialog / finalisation --------------------------------------

    def _ask_save_path(self, view, export_format: ExportFormat,
                        default_xls_filename: str, default_pdf_filename: str) -> str:
        if export_format == ExportFormat.XLSX:
            file_path, _ = QFileDialog.getSaveFileName(
                view, self.SAVE_XLSX_CAPTION, default_xls_filename, self.SAVE_XLSX_FILTER
            )
        elif export_format == ExportFormat.PDF:
            file_path, _ = QFileDialog.getSaveFileName(
                view, self.SAVE_PDF_CAPTION, default_pdf_filename, self.SAVE_PDF_FILTER
            )
        else:
            file_path = ""

        if not file_path:
            return ""

        suffix = ".xlsx" if export_format == ExportFormat.XLSX else ".pdf"
        if not file_path.lower().endswith(suffix):
            file_path += suffix

        if Path(file_path).exists() and not YesNoMessagebox(
            "Файл с таким именем уже существует. Уверены, что хотите его перезаписать?"
        ):
            return ""

        return file_path

    def _finalize_export(self, export_format: ExportFormat, temp_xlsx_path: str,
                          temp_pdf_path: str, file_path: str) -> bool:
        """Converts to PDF if needed, copies the result to file_path and cleans up temp files."""
        success = False
        try:
            if export_format == ExportFormat.XLSX:
                shutil.copy2(temp_xlsx_path, file_path)
                success = True
            elif export_format == ExportFormat.PDF:
                converter = get_pdf_converter()
                if converter is None:
                    ErrorInfoMessageBox(
                        "Для экспорта в PDF требуется установленный Microsoft Excel"
                    ).exec()
                    return False
                converter.convert(temp_xlsx_path, temp_pdf_path)
                shutil.copy2(temp_pdf_path, file_path)
                success = True
        except PdfConversionError as e:
            ErrorInfoMessageBox(str(e)).exec()
            log.c(f"Ошибка при конвертации в PDF: {e}")
        except Exception as e:
            ErrorInfoMessageBox(
                "Во время записи, переноса или удаления файлов произошла ошибка (см. подробности в логе)"
            ).exec()
            log.c(f"Ошибка в процессе экспорта: {e}")
        finally:
            for temp_path in (temp_xlsx_path, temp_pdf_path):
                try:
                    Path(temp_path).unlink(missing_ok=True)
                except Exception as e:
                    log.w(f"Не удалось удалить временный файл {temp_path}: {e}")

        if success:
            self._set_last_dir(file_path)
        return success

    @staticmethod
    def _close_workbook(workbook: Workbook, worksheet: Worksheet) -> None:
        try:
            workbook.close()
            del worksheet
            del workbook
        except Exception as e:
            log.w(f"Ошибка при закрытии или удалении XLSX-файла: {e}")

    # -- minimal-fit row height -------------------------------------------

    def _effective_char_width(self, column_width_chars: float, font_size: int, fulfilment_exported: bool = False) -> float:
        """
        Scales a raw column width (in Excel's "characters" unit) down to the
        number of characters that actually fit at the given font size, to
        correct for the font-size/Cyrillic mismatch described above.
        """
        size_factor = self.BASELINE_FONT_SIZE / max(font_size, 1)
        if fulfilment_exported:
            return max(1.0, column_width_chars * size_factor * self.CYRILLIC_WIDTH_FACTOR_FULFILMENT)
        else:
            return max(1.0, column_width_chars * size_factor * self.CYRILLIC_WIDTH_FACTOR_LIABILITY)

    def _estimate_line_count(self, text, column_width_chars: float, font_size: int = 11, fulfilment_exported: bool = False) -> int:
        """
        Estimates how many lines a wrapped text cell will occupy, given a
        column width expressed in "characters" (the same unit xlsxwriter's
        set_column width uses) and the font size the cell is actually
        rendered with. This lets us compute a per-row height that fits the
        actual content instead of a single height shared by all rows
        regardless of how much text they hold.
        """
        if text is None:
            return 1
        text = str(text)
        if not text:
            return 1
        effective_width = self._effective_char_width(column_width_chars, font_size, fulfilment_exported)
        width = max(1, int(round(effective_width)))
        lines = 0
        for physical_line in text.split("\n"):
            wrapped = textwrap.wrap(physical_line, width=width) or [""]
            lines += len(wrapped)
        return max(1, lines)

    @staticmethod
    def _calc_row_height(line_count: int, font_size: int,
                          line_height_factor: float = 1.25, padding: float = 3.0) -> float:
        """
        Converts a number of wrapped lines into a row height in points.
        line_height_factor / padding are tuned to roughly match how Excel
        sizes a single line of text for a given font size; adjust if real
        rows still come out a little short or tall for your font.
        """
        single_line_height = font_size * line_height_factor
        return round(line_count * single_line_height + padding, 1)


# =============================================================================
# LiabilityXlsWriter
# =============================================================================

class LiabilityXlsWriter(BaseXlsWriter):
    DEFAULT_XLSCOLUMN_WIDTH = {
        Col.RECEIVER: 28,
        Col.ID: 0,
        Col.TYPE: 0,
        Col.CATEGORY: 0,
        Col.SUBCATEGORY: 0,
        Col.NAME: 65,
        Col.REMAINAMOUNT: 17,
        Col.TOTALAMOUNT: 17,
        Col.NDS: 0,
        Col.DUEDATE: 18,
        Col.INCURRENCEDATE: 0,
        Col.PAYMENTTYPE: 15,
        Col.DESCR: 51,
        Col.RESPONSIBLE: 21,
        Col.NOTES: 0,
        Col.TODAYSHARE: 17,
        Col.LASTPAYMENTDATE: 0,
        Col.FILTERFLAGS: 0,
        Col.FEATURED: 0,
        Col.HIDDEN: 0,
        Col.RECEIVERNOCASE: 0,
    }

    def __init__(self, model: LiabilityTotalsProxyModel, view: QTableView, settings_handler: SettingsHandler):
        super().__init__(settings_handler, settings_key="Export/lastpath")
        self.model: LiabilityTotalsProxyModel = model
        self.view: QTableView = view
        # Индексы столбцов с финансовыми данными
        self.decimalcolumns_numbers = LiabilitySqlTableModel.DECIMAL_COLUMNS

    def write(self, export_format: ExportFormat, columns_to_export: list[bool], show_hidden: HiddenDisplayMode) -> bool:
        row_formatting: RowFormatting = model_atlevel(-2, self.model).row_formatting
        current_date_str = date_purestr(QDate().currentDate())

        default_xls_filename = self._default_file_path(f"ПлатежныйКалендарь_{current_date_str}.xlsx")
        default_pdf_filename = self._default_file_path(f"ПлатежныйКалендарь_{current_date_str}.pdf")

        temp_xlsx_path, temp_pdf_path = self._make_temp_paths()

        workbook: Workbook = Workbook(temp_xlsx_path)
        worksheet: Worksheet = workbook.add_worksheet()
        worksheet.set_landscape()
        worksheet.fit_to_pages(1, 0)

        ### Форматы ###
        f_fileheader1: Format = workbook.add_format({"font_size": 22, "bold": True, "align": "center", "valign": "vcenter"})
        f_fileheader2: Format = workbook.add_format({"font_size": 16, "bold": True, "align": "center", "valign": "vcenter"})
        f_tableheader: Format = workbook.add_format({"font_size": 14, "bold": True, "align": "center", "valign": "vcenter", 'text_wrap': True})
        f_event_normal: Format = workbook.add_format({"font_size": 14, "bold": False, 'text_wrap': True, "valign": "vcenter", "border": 1,
                                                       "border_color": self.BORDER_COLOR})
        f_event_due: Format = workbook.add_format({"font_size": 14, "bold": row_formatting.due_textbold, 'text_wrap': True, "valign": "vcenter",
                                                    "font_color": f"{row_formatting.due_forecolor}", "bg_color": f"{row_formatting.due_backcolor}",
                                                    "border": 1, "border_color": self.BORDER_COLOR})
        f_event_today: Format = workbook.add_format({"font_size": 14, "bold": row_formatting.today_textbold, 'text_wrap': True, "valign": "vcenter",
                                                      "font_color": f"{row_formatting.today_forecolor}", "bg_color": f"{row_formatting.today_backcolor}",
                                                      "border": 1, "border_color": self.BORDER_COLOR})
        f_header_top: Format = workbook.add_format({"font_size": 16, "bold": False, "font_color": f"{row_formatting.header_section_forecolor}",
                                                     "bg_color": f"{row_formatting.header_section_backcolor}", "border": 1, "border_color": self.BORDER_COLOR,
                                                     "top_color": "#000000", "align": "center"})
        f_header_sub: Format = workbook.add_format({"font_size": 16, "bold": False, "font_color": f"{row_formatting.header_subsection_forecolor}",
                                                     "bg_color": f"{row_formatting.header_subsection_backcolor}", "border": 1, "border_color": self.BORDER_COLOR,
                                                     "top_color": "#000000", "align": "center"})
        f_footer_top: Format = workbook.add_format({"font_size": 14, "bold": True, "font_color": f"{row_formatting.footer_section_forecolor}",
                                                     "bg_color": f"{row_formatting.footer_section_backcolor}", "border": 1, "border_color": self.BORDER_COLOR})
        f_footer_sub: Format = workbook.add_format({"font_size": 14, "bold": True, "font_color": f"{row_formatting.footer_subsection_forecolor}",
                                                     "bg_color": f"{row_formatting.footer_subsection_backcolor}", "border": 1, "border_color": self.BORDER_COLOR})
        f_footer_final: Format = workbook.add_format({"font_size": 14, "bold": True, "bg_color": f"{EventItemDelegate.FINALFOOTER_BACK_COLOR.name()}",
                                                       "border": 1, "border_color": self.BORDER_COLOR, "top_color": "#000000"})
        ###############

        ### Форматирование столбцов ###
        for col in range(len(columns_to_export)):
            if columns_to_export[col]:
                worksheet.set_column(col, col, self.DEFAULT_XLSCOLUMN_WIDTH[col], f_tableheader)
            else:
                worksheet.set_column(col, col, 0)
        ###############################

        ### Временная смена фильтров модели ###
        if show_hidden == HiddenDisplayMode.NONE:
            model_atlevel(-2, self.model).modify_filter("AND hidden = 0")
        ########################################

        ### ЗАГОЛОВОЧНАЯ ЧАСТЬ ###
        worksheet.merge_range(0, 0, 0, len(columns_to_export) - 1, "ПЛАТЕЖНЫЙ КАЛЕНДАРЬ", f_fileheader1)
        worksheet.merge_range(1, 0, 1, len(columns_to_export) - 1, f"по состоянию на {date_displstr(QDate().currentDate())}", f_fileheader2)
        for col in range(len(columns_to_export)):
            worksheet.write(self.HEADER_ROWS_NUMBER - 1, col, LiabilitySqlTableModel.COLUMN_DATA[col][0])
        ##########################

        ### ОСНОВНАЯ ЧАСТЬ ###
        for row in range(self.model.rowCount()):
            row_type: RowType = self.model.index(row, Col.TYPE, QModelIndex()).data(LiabilitySqlTableModel.qtValueRole)
            if row_type == RowType.LIABILITY:
                term_flags: FilterFlags = self.model.index(row, Col.FILTERFLAGS, QModelIndex()).data(LiabilitySqlTableModel.qtValueRole)
                if FilterFlags.DUE in term_flags:
                    row_format: Format = f_event_due
                elif FilterFlags.TODAY in term_flags:
                    row_format: Format = f_event_today
                else:
                    row_format: Format = f_event_normal
            elif row_type == RowType.HEADER:
                row_subtype: HeaderFooterSubtype = self.model.index(row, Col.SUBCATEGORY, QModelIndex()).data(LiabilitySqlTableModel.qtValueRole)
                row_format: Format = f_header_sub if row_subtype == HeaderFooterSubtype.ORDINARY else f_header_top
            elif row_type == RowType.FOOTER:
                row_subtype: HeaderFooterSubtype = self.model.index(row, Col.SUBCATEGORY, QModelIndex()).data(LiabilitySqlTableModel.qtValueRole)
                row_format: Format = f_footer_sub if row_subtype == HeaderFooterSubtype.ORDINARY else f_footer_top
            elif row_type == RowType.FINALFOOTER:
                row_format: Format = f_footer_final
            else:
                row_format: Format = f_event_normal

            for col in range(self.model.columnCount()):
                if not columns_to_export[col]:
                    continue
                if row_type == RowType.HEADER and col == 0:
                    worksheet.merge_range(row + self.HEADER_ROWS_NUMBER, 0, row + self.HEADER_ROWS_NUMBER, len(columns_to_export) - 1,
                                           self.model.index(row, 0, QModelIndex()).data(Qt.ItemDataRole.DisplayRole), row_format)
                else:
                    if col in self.decimalcolumns_numbers:
                        if row_type in (RowType.FOOTER, RowType.FINALFOOTER):
                            value = self.model.index(row, col, QModelIndex()).data(self.model.decimalValueRole)
                        else:
                            value = self.model.index(row, col, QModelIndex()).data(LiabilitySqlTableModel.qtValueRole)
                        if value == 0 and self.decimalcolumns_numbers.index(col) == len(self.decimalcolumns_numbers) - 1:
                            value = ""
                        else:
                            row_format.set_num_format("# ##0.00")
                        worksheet.write(row + self.HEADER_ROWS_NUMBER, col, value, row_format)
                    else:
                        if show_hidden == HiddenDisplayMode.SUMONLY and self.model.index(row, Col.HIDDEN).data(LiabilitySqlTableModel.qtValueRole) == 1:
                            value = ""
                        else:
                            value = self.model.index(row, col, QModelIndex()).data(Qt.ItemDataRole.DisplayRole)
                        worksheet.write(row + self.HEADER_ROWS_NUMBER, col, value, row_format)

            ### Минимальная высота строки по содержимому ###
            if row_type == RowType.HEADER:
                merged_width = sum(self.DEFAULT_XLSCOLUMN_WIDTH[c] for c in range(len(columns_to_export)) if columns_to_export[c])
                header_text = self.model.index(row, 0, QModelIndex()).data(Qt.ItemDataRole.DisplayRole)
                max_lines = self._estimate_line_count(header_text, merged_width, font_size=row_format.font_size, fulfilment_exported=False)
            else:
                max_lines = 1
                for col in range(self.model.columnCount()):
                    col_width = self.DEFAULT_XLSCOLUMN_WIDTH[col]
                    if not columns_to_export[col] or col_width <= 0:
                        continue  # столбец скрыт (нулевая ширина) — на высоту строки не влияет
                    cell_text = self.model.index(row, col, QModelIndex()).data(Qt.ItemDataRole.DisplayRole)
                    max_lines = max(max_lines, self._estimate_line_count(cell_text, col_width, font_size=row_format.font_size, fulfilment_exported=False))
            worksheet.set_row(row + self.HEADER_ROWS_NUMBER, self._calc_row_height(max_lines, row_format.font_size))
            ##################################################
        #####################

        ### Возврат фильтра модели ###
        if show_hidden == HiddenDisplayMode.NONE:
            model_atlevel(-2, self.model).restore_modified_filter()
        ###############################

        if str_bool(self.settings_handler.settings.value("Export/frozenheader")):
            worksheet.freeze_panes(self.HEADER_ROWS_NUMBER, 0)

        self._close_workbook(workbook, worksheet)

        file_path = self._ask_save_path(self.view, export_format, default_xls_filename, default_pdf_filename)
        if not file_path:
            return False

        return self._finalize_export(export_format, temp_xlsx_path, temp_pdf_path, file_path)


# =============================================================================
# FulfilmentXlsWriter
# =============================================================================

class FulfilmentXlsWriter(BaseXlsWriter):
    COLUMN_WIDTH = {
        False: [11, 65, 15, 15],
        True: [11, 65, 15, 15, 15, 15],
    }
    HALIGN = {
        0: 'left',
        1: 'left',
        2: 'right',
        3: 'right',
        4: 'right',
        5: 'center',
    }
    NUM_FORMAT = {
        2: '# ##0',
        3: '# ##0',
        4: '# ##0',
        5: '0.0%',
    }

    def __init__(self, model: FulfilmentModel, view: QTreeView, settings_handler: SettingsHandler):
        super().__init__(settings_handler, settings_key="Export/fulfilmentlastpath")
        self.model: FulfilmentModel = model
        self.view: QTreeView = view

    def write(self, is_fulfilment: bool, begin_date: QDate, end_date: QDate, export_format: ExportFormat) -> bool:
        column_count = self.model.columnCount(QModelIndex())
        row_count = self.model.rowCount(QModelIndex())

        xls_filename = f"{'ИсполнениеПлана' if is_fulfilment else 'ПереченьЗатрат'}_{date_purestr(begin_date, short=True)}_{date_purestr(end_date, short=True)}.xlsx"
        pdf_filename = f"{'ИсполнениеПлана' if is_fulfilment else 'ПереченьЗатрат'}_{date_purestr(begin_date, short=True)}_{date_purestr(end_date, short=True)}.pdf"
        default_xls_filename = self._default_file_path(xls_filename)
        default_pdf_filename = self._default_file_path(pdf_filename)

        temp_xlsx_path, temp_pdf_path = self._make_temp_paths()

        workbook: Workbook = Workbook(temp_xlsx_path)
        worksheet: Worksheet = workbook.add_worksheet()
        worksheet.set_portrait()
        worksheet.fit_to_pages(1, 0)

        ### Форматы ###
        f_fileheader1: Format = workbook.add_format({"font_size": 22, "bold": True, "align": "center", "valign": "vcenter"})
        f_fileheader2: Format = workbook.add_format({"font_size": 16, "bold": True, "align": "center", "valign": "vcenter"})
        f_tableheader: Format = workbook.add_format({"font_size": 14, "bold": True, "align": "center", "valign": "vcenter", 'text_wrap': True})

        palette = TablePalette()
        pf_normal: dict = {"font_size": 13, "bold": False, 'text_wrap': True, "valign": "vcenter",
                            "bg_color": f"{palette.base.name()}", "border": 1, "border_color": self.BORDER_COLOR}
        pf_level1: dict = {"font_size": 13, "bold": True, 'text_wrap': True, "valign": "vcenter",
                            "bg_color": f"{palette.mid.name()}", "border": 1, "border_color": self.BORDER_COLOR}
        pf_level2: dict = {"font_size": 13, "bold": True, 'text_wrap': True, "valign": "vcenter",
                            "bg_color": f"{palette.high.name()}", "border": 1, "border_color": self.BORDER_COLOR}
        ###############

        ### Форматирование столбцов ###
        for col in range(column_count):
            worksheet.set_column(col, col, self.COLUMN_WIDTH[is_fulfilment][col], f_tableheader)
        ###############################

        ### ЗАГОЛОВОЧНАЯ ЧАСТЬ ###
        text = "ИСПОЛНЕНИЕ ФИНАНСОВОГО ПЛАНА" if is_fulfilment else "ПЕРЕЧЕНЬ ЗАТРАТ"
        worksheet.merge_range(0, 0, 0, column_count - 1, text, f_fileheader1)
        worksheet.merge_range(1, 0, 1, column_count - 1,
                               f"за период с {date_displstr(begin_date)} по {date_displstr(end_date)}", f_fileheader2)
        headers = [self.model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) for col in range(column_count)]
        for col in range(column_count):
            worksheet.write(self.HEADER_ROWS_NUMBER - 1, col, headers[col])
        ##########################

        ### ОСНОВНАЯ ЧАСТЬ ###
        for row in range(row_count):
            item: TreeItem = self.model.index(row, 0, QModelIndex()).internalPointer()
            categorie = item.get_categorie()
            if self.model.categorie_level(categorie) == 2:
                pre_format: dict = pf_level2
            elif self.model.categorie_level(categorie) == 1:
                pre_format: dict = pf_level1
            else:
                pre_format: dict = pf_normal

            for col in range(column_count):
                row_format_aligned: Format = workbook.add_format(pre_format | {'align': f'{self.HALIGN[col]}'})
                if col in self.NUM_FORMAT.keys():
                    value = self.model.index(row, col, QModelIndex()).data(FulfilmentModel.internalValueRole)
                    if value is None or (col == 5 and value == -1):
                        worksheet.write(row + self.HEADER_ROWS_NUMBER, col,
                                         self.model.index(row, col, QModelIndex()).data(Qt.ItemDataRole.DisplayRole), row_format_aligned)
                    else:
                        row_format_aligned.set_num_format(self.NUM_FORMAT[col])
                        worksheet.write_number(row + self.HEADER_ROWS_NUMBER, col,
                                                self.model.index(row, col, QModelIndex()).data(FulfilmentModel.internalValueRole), row_format_aligned)
                else:
                    worksheet.write(row + self.HEADER_ROWS_NUMBER, col,
                                     self.model.index(row, col, QModelIndex()).data(Qt.ItemDataRole.DisplayRole), row_format_aligned)

            ### Минимальная высота строки по содержимому ###
            max_lines = 1
            widths = self.COLUMN_WIDTH[is_fulfilment]
            for col in range(column_count):
                if widths[col] <= 0:
                    continue  # столбец скрыт (нулевая ширина) — на высоту строки не влияет
                cell_text = self.model.index(row, col, QModelIndex()).data(Qt.ItemDataRole.DisplayRole)
                max_lines = max(max_lines, self._estimate_line_count(cell_text, widths[col], font_size=13, fulfilment_exported=True))
            worksheet.set_row(row + self.HEADER_ROWS_NUMBER, self._calc_row_height(max_lines, font_size=13))
            ##################################################
        #####################

        self._close_workbook(workbook, worksheet)

        file_path = self._ask_save_path(self.view, export_format, default_xls_filename, default_pdf_filename)
        if not file_path:
            return False

        return self._finalize_export(export_format, temp_xlsx_path, temp_pdf_path, file_path)