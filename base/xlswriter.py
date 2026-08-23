import os
import random
import shutil
import string
import platform
import posixpath
import lovely_logger as log

from enum import IntEnum, auto
from pathlib import Path

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


def xlsx_to_pdf_win32(xlsx_path, pdf_path):
    excel = win32com.client.Dispatch("Excel.Application")
    try:
        excel.Visible = False
        wb = excel.Workbooks.Open(os.path.abspath(xlsx_path))
        wb.ActiveSheet.ExportAsFixedFormat(0, os.path.abspath(pdf_path))
        return True
    except pywintypes.com_error:
        msg_box: ErrorInfoMessageBox = ErrorInfoMessageBox("Не удалось записать файл. Возможно, файл с таким же именем используется "
                                                           "другим приложением или в настройках указан неверный путь")
        msg_box.exec()
        return False
    finally:
        try:
            wb.Close()
        except NameError:
            pass
        excel.Quit()
        del wb
        del excel


class ExportFormat(IntEnum):
    XLSX = auto()
    PDF = auto()


class HiddenDisplayMode(IntEnum):
    NONE = auto()
    SUMONLY = auto()
    FULL = auto()


class LiabilityXlsWriter:
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

    BORDER_COLOR: str = "#D0D0D0"
    HEADER_ROWS_NUMBER: int = 4

    def __init__(self, model: LiabilityTotalsProxyModel, view: QTableView, settings_handler: SettingsHandler):
        self.model: LiabilityTotalsProxyModel = model
        self.view: QTableView = view
        self.settings_handler: SettingsHandler = settings_handler
        self.last_path: str = ""

        # Индексы столбцов с финансовыми данными
        self.decimalcolumns_numbers = LiabilitySqlTableModel.DECIMAL_COLUMNS

    def write(self, export_format: ExportFormat, columns_to_export: list[bool], show_hidden: HiddenDisplayMode) -> bool:

        if platform.system() != "Windows":
            msg_box = ErrorInfoMessageBox("Экспорт для этой платфоры недоступен")
            msg_box.exec()
            return False

        row_formatting: RowFormatting = model_atlevel(-2, self.model).row_formatting

        last_path_str = self.settings_handler.settings.value("Export/lastpath")
        current_date_str = date_purestr(QDate().currentDate())

        if last_path_str and Path(last_path_str).is_dir():
            base_dir = Path(last_path_str)
            default_xls_filename = str(base_dir / f"ПлатежныйКалендарь_{current_date_str}.xlsx")
            default_pdf_filename = str(base_dir / f"ПлатежныйКалендарь_{current_date_str}.pdf")
        else:
            default_xls_filename = f"ПлатежныйКалендарь_{current_date_str}.xlsx"
            default_pdf_filename = f"ПлатежныйКалендарь_{current_date_str}.pdf"

        temp_dir = Path.cwd() / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=14))
        temp_xls_file_path = str(temp_dir / f"{random_suffix}.xlsx")
        temp_pdf_file_path = str(temp_dir / f"{random_suffix}.pdf")

        workbook: Workbook = Workbook(temp_xls_file_path)

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
        # Ширина
        for col in range(len(columns_to_export)):
            if columns_to_export[col]:
                worksheet.set_column(col, col, self.DEFAULT_XLSCOLUMN_WIDTH[col], f_tableheader)
            else:
                worksheet.set_column(col, col, 0)
        ###############################

        ### Временная смена фильтров модели  ###
        if show_hidden == HiddenDisplayMode.NONE:
            model_atlevel(-2, self.model).modify_filter("AND hidden = 0")
        ###############################

        ### ЗАГОЛОВОЧНАЯ ЧАСТЬ ###
        # Заголовок
        worksheet.merge_range(0, 0, 0, len(columns_to_export) - 1, "ПЛАТЕЖНЫЙ КАЛЕНДАРЬ", f_fileheader1)
        worksheet.merge_range(1, 0, 1, len(columns_to_export) - 1, f"по состоянию на {date_displstr(QDate().currentDate())}", f_fileheader2)
        # Заголовочная строка
        for col in range(len(columns_to_export)):
            worksheet.write(self.HEADER_ROWS_NUMBER - 1, col, LiabilitySqlTableModel.COLUMN_DATA[col][0])
        ##########################

        ### ОСНОВНАЯ ЧАСТЬ ###
        for row in range(self.model.rowCount()):

            # Определяем формат для строки
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
                if row_subtype == HeaderFooterSubtype.ORDINARY:
                    row_format: Format = f_header_sub
                else:
                    row_format: Format = f_header_top
            elif row_type == RowType.FOOTER:
                row_subtype: HeaderFooterSubtype = self.model.index(row, Col.SUBCATEGORY, QModelIndex()).data(LiabilitySqlTableModel.qtValueRole)
                if row_subtype == HeaderFooterSubtype.ORDINARY:
                    row_format: Format = f_footer_sub
                else:
                    row_format: Format = f_footer_top
            elif row_type == RowType.FINALFOOTER:
                row_format: Format = f_footer_final
            else:
                row_format: Format = f_event_normal

            # Заполнение строки
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
        #####################

        ### Возврат фильтра модели  ###
        if show_hidden == HiddenDisplayMode.NONE:
            model_atlevel(-2, self.model).restore_modified_filter()
        ###############################

        if str_bool(self.settings_handler.settings.value("Export/frozenheader")):
            worksheet.freeze_panes(self.HEADER_ROWS_NUMBER, 0)

        try:
            workbook.close()
            del worksheet
            del workbook
        except Exception as e:
            log.w(f"Ошибка при закрытии или удалении XLSX-файла: {e}")

        if export_format == ExportFormat.XLSX:
            file_path = QFileDialog.getSaveFileName(self.view, "Сохранить как Excel-таблицу", default_xls_filename, "Таблица Excel (*.xlsx)")[0]
        elif export_format == ExportFormat.PDF:
            file_path = QFileDialog.getSaveFileName(self.view, "Сохранить как PDF-файл", default_pdf_filename, "Документ PDF (*.pdf)")[0]
        else:
            file_path = ""
        if not file_path:
            return False
        if export_format == ExportFormat.XLSX and not file_path.lower().endswith(".xlsx"):
            file_path += ".xlsx"
        if export_format == ExportFormat.PDF and not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"

        if Path(file_path).exists():
            if not YesNoMessagebox("Файл с таким именем уже существует. Уверены, что хотите его перезаписать?"):
                return False
        try:
            if export_format == ExportFormat.XLSX:
                shutil.copy2(temp_xls_file_path, file_path)
                Path(temp_xls_file_path).unlink()
            elif export_format == ExportFormat.PDF:
                xlsx_to_pdf_win32(temp_xls_file_path, temp_pdf_file_path)
                shutil.copy2(temp_pdf_file_path, file_path)
                Path(temp_xls_file_path).unlink()
                Path(temp_pdf_file_path).unlink()
        except Exception as e:
            ErrorInfoMessageBox("Во время записи, переноса или удаления файлов произошла ошибка (см. подробности в логе)").exec()
            log.c(f"Ошибка в процессе экспорта: {e}")
            return False
        self.settings_handler.settings.setValue("Export/lastpath", str(Path(file_path).parent))
        self.last_path = file_path
        return True


class FulfilmentXlsWriter:

    BORDER_COLOR: str = "#D0D0D0"
    HEADER_ROWS_NUMBER: int = 4
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
        self.model: FulfilmentModel = model
        self.view: QTreeView = view
        self.settings_handler: SettingsHandler = settings_handler
        self.last_path: str = ""

    def write(self, is_fulfilment: bool, begin_date: QDate, end_date: QDate, export_format: ExportFormat) -> bool:

        column_count = self.model.columnCount(QModelIndex())
        row_count = self.model.rowCount(QModelIndex())

        if platform.system() != "Windows":
            msg_box = ErrorInfoMessageBox("Экспорт для этой платфоры недоступен")
            msg_box.exec()
            return False

        last_path = self.settings_handler.settings.value("Export/fulfilmentlastpath")
        xls_filename: str = rf"{'ИсполнениеПлана' if is_fulfilment else 'ПереченьЗатрат'}_{date_purestr(begin_date, short=True)}_{date_purestr(end_date, short=True)}.xlsx"
        pdf_filename: str = rf"{'ИсполнениеПлана' if is_fulfilment else 'ПереченьЗатрат'}_{date_purestr(begin_date, short=True)}_{date_purestr(end_date, short=True)}.pdf"
        if not last_path or not Path(last_path).is_dir():
            default_xls_filename: str = xls_filename
            default_pdf_filename: str = pdf_filename
        else:
            default_xls_filename: str = posixpath.join(last_path, xls_filename)
            default_pdf_filename: str = posixpath.join(last_path, pdf_filename)
        temp_xls_file_path: str = posixpath.join(os.getcwd(), "temp", ''.join(random.choices(string.ascii_uppercase + string.digits, k=14)) + ".xlsx")
        temp_pdf_file_path: str = posixpath.join(os.getcwd(), "temp", ''.join(random.choices(string.ascii_uppercase + string.digits, k=14)) + ".pdf")

        workbook: Workbook = Workbook(temp_xls_file_path)
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

        # Форматирование столбцов #
        for col in range(column_count):
            worksheet.set_column(col, col, self.COLUMN_WIDTH[is_fulfilment][col], f_tableheader)

        # Заголовок
        text = "ИСПОЛНЕНИЕ ФИНАНСОВОГО ПЛАНА" if is_fulfilment else "ПЕРЕЧЕНЬ ЗАТРАТ"
        worksheet.merge_range(0, 0, 0, column_count - 1, text, f_fileheader1)
        worksheet.merge_range(1, 0, 1, column_count - 1,
                              f"за период с {date_displstr(begin_date)} по {date_displstr(end_date)}", f_fileheader2)
        # Заголовочная строка
        headers = [self.model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) for col in range(column_count)]
        for col in range(column_count):
            worksheet.write(self.HEADER_ROWS_NUMBER - 1, col, headers[col])

        # ОСНОВНАЯ ЧАСТЬ #
        for row in range(row_count):
            # Определяем формат для строки
            item: TreeItem = self.model.index(row, 0, QModelIndex()).internalPointer()
            categorie = item.get_categorie()
            if self.model.categorie_level(categorie) == 2:
                pre_format: dict = pf_level2
            elif self.model.categorie_level(categorie) == 1:
                pre_format: dict = pf_level1
            else:
                pre_format: dict = pf_normal

            # Заполнение строки
            for col in range(column_count):
                row_format_aligned: Format = workbook.add_format(pre_format | {'align': f'{self.HALIGN[col]}'})
                if col in self.NUM_FORMAT.keys():
                    value = self.model.index(row, col, QModelIndex()).data(FulfilmentModel.internalValueRole)
                    if value is None or (col == 5 and value == -1):
                        worksheet.write(row + self.HEADER_ROWS_NUMBER, col, self.model.index(row, col, QModelIndex()).data(Qt.ItemDataRole.DisplayRole), row_format_aligned)
                    else:
                        row_format_aligned.set_num_format(self.NUM_FORMAT[col])
                        worksheet.write_number(row + self.HEADER_ROWS_NUMBER, col, self.model.index(row, col, QModelIndex()).data(FulfilmentModel.internalValueRole), row_format_aligned)
                else:
                    worksheet.write(row + self.HEADER_ROWS_NUMBER, col, self.model.index(row, col, QModelIndex()).data(Qt.ItemDataRole.DisplayRole), row_format_aligned)

        try:
            workbook.close()
            del worksheet
            del workbook
        except Exception as e:
            log.w(f"Ошибка при закрытии или удалении XLSX-файла: {e}")

        if export_format == ExportFormat.XLSX:
            file_path = QFileDialog.getSaveFileName(self.view, "Сохранить как Excel-таблицу", default_xls_filename,
                                                    "Таблица Excel (*.xlsx)")[0]
        elif export_format == ExportFormat.PDF:
            file_path = QFileDialog.getSaveFileName(self.view, "Сохранить как PDF-файл", default_pdf_filename,
                                                    "Документ PDF (*.pdf)")[0]
        else:
            file_path = ""
        if not file_path:
            return False
        if export_format == ExportFormat.XLSX and not file_path.lower().endswith(".xlsx"):
            file_path += ".xlsx"
        if export_format == ExportFormat.PDF and not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"

        if Path(file_path).exists():
            if not YesNoMessagebox("Файл с таким именем уже существует. Уверены, что хотите его перезаписать?"):
                return False
        try:
            if export_format == ExportFormat.XLSX:
                shutil.copy2(temp_xls_file_path, file_path)
                Path(temp_xls_file_path).unlink()
            elif export_format == ExportFormat.PDF:
                xlsx_to_pdf_win32(temp_xls_file_path, temp_pdf_file_path)
                shutil.copy2(temp_pdf_file_path, file_path)
                Path(temp_xls_file_path).unlink()
                Path(temp_pdf_file_path).unlink()
        except Exception as e:
            ErrorInfoMessageBox("Во время записи, переноса или удаления файлов произошла ошибка (см. подробности в логе)").exec()
            log.c(f"Ошибка в процессе экспорта: {e}")
        self.settings_handler.settings.setValue("Export/fulfilmentlastpath", str(Path(file_path).parent))
        self.last_path = file_path

        return True
