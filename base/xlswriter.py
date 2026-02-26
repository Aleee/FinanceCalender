import os
import random
import string
from decimal import Decimal
from enum import IntEnum, auto
from pathlib import Path

import pywintypes
import win32com.client
from PySide6.QtCore import QDate, QModelIndex, Qt, QTime
from PySide6.QtWidgets import QTableView
from xlsxwriter.worksheet import Worksheet

from base.casting import str_bool
from base.date import date_purestr, date_displstr
from base.event import EventField, RowType, TermRoleFlags, Event
from gui.common import model_atlevel
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.eventproxymodel import EventListFinalFilterModel
from gui.eventmodel import EventTableModel, HeaderFooterField, HeaderFooterSubtype, RowFormatting
from gui.settings import SettingsHandler
from gui.commonwidgets.itemdelegate import EventItemDelegate
from typing import get_type_hints
from xlsxwriter import Workbook
from xlsxwriter.exceptions import FileCreateError
from xlsxwriter.format import Format


def xlsx_to_pdf_win32(xlsx_path, pdf_path):
    try:
        excel = win32com.client.Dispatch("Excel.Application")
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
        if wb:
            wb.Close()
        excel.Quit()
        del wb
        del excel


class ExportFormat(IntEnum):
    XLSX = auto()
    PDF = auto()


class XlsWriter:
    DEFAULT_XLSCOLUMN_WIDTH = {
        EventField.RECEIVER: 28,
        EventField.TYPE: 0,
        EventField.ID: 0,
        EventField.CATEGORY: 0,
        EventField.NAME: 65,
        EventField.REMAINAMOUNT: 17,
        EventField.TOTALAMOUNT: 17,
        EventField.PERCENTAGE: 0,
        EventField.DUEDATE: 18,
        EventField.PAYMENTTYPE: 15,
        EventField.CREATEDATE: 0,
        EventField.DESCR: 51,
        EventField.RESPONSIBLE: 21,
        EventField.TODAYSHARE: 17,
        EventField.TERMFLAGS: 0,
    }

    BORDER_COLOR: str = "#D0D0D0"
    HEADER_ROWS_NUMBER: int = 4

    def __init__(self, model: EventListFinalFilterModel, view: QTableView, settings_handler: SettingsHandler):
        self.model: EventListFinalFilterModel = model
        self.view: QTableView = view
        self.settings_handler: SettingsHandler = settings_handler
        self.last_path: str = ""

        # Индексы столбцов с финансовыми данными
        type_hints: list = list(get_type_hints(Event).values())
        self.decimalcolumns_numbers = [index for index, datatype in enumerate(type_hints) if datatype == Decimal]

    def write(self, export_format: ExportFormat, columns_to_export: list[bool]) -> bool:

        row_formatting: RowFormatting = model_atlevel(-2, self.model).row_formatting

        export_dir: str = self.settings_handler.settings.value("Export/path", os.getcwd())
        xls_file_path: str = os.path.join(export_dir, rf"ПлатежныйКалендарь_{date_purestr(QDate().currentDate())}.xlsx")
        temp_file_path: str = os.path.join(os.getcwd(), ''.join(random.choices(string.ascii_uppercase + string.digits, k=14)) + ".pdf")
        pdf_file_path: str = os.path.join(export_dir, rf"ПлатежныйКалендарь_{date_purestr(QDate().currentDate())}.pdf")

        if export_format == ExportFormat.XLSX and Path(xls_file_path).exists():
            xls_file_path = xls_file_path[:-5] + "_" + QTime().currentTime().toString("hhmmss") + ".xlsx"

        workbook: Workbook = Workbook(xls_file_path) if export_format == ExportFormat.XLSX else Workbook(temp_file_path)

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

        ### ЗАГОЛОВОЧНАЯ ЧАСТЬ ###
        # Заголовок
        worksheet.merge_range(0, 0, 0, len(columns_to_export) - 1, "ПЛАТЕЖНЫЙ КАЛЕНДАРЬ", f_fileheader1)
        worksheet.merge_range(1, 0, 1, len(columns_to_export) - 1, f"по состоянию на {date_displstr(QDate().currentDate())}", f_fileheader2)
        # Заголовочная строка
        for col in range(len(columns_to_export)):
            worksheet.write(self.HEADER_ROWS_NUMBER - 1, col, EventTableModel.HEADERS[col])
        ##########################

        ### ОСНОВНАЯ ЧАСТЬ ###
        for row in range(self.model.rowCount()):

            # Определяем формат для строки
            row_type: RowType = self.model.index(row, EventField.TYPE, QModelIndex()).data(EventTableModel.internalValueRole)
            if row_type == RowType.EVENT:
                term_flags: TermRoleFlags = self.model.index(row, EventField.TERMFLAGS, QModelIndex()).data(EventTableModel.internalValueRole)
                if TermRoleFlags.DUE in term_flags:
                    row_format: Format = f_event_due
                elif TermRoleFlags.TODAY in term_flags:
                    row_format: Format = f_event_today
                else:
                    row_format: Format = f_event_normal
            elif row_type == RowType.HEADER:
                row_subtype: HeaderFooterSubtype = self.model.index(row, HeaderFooterField.SUBTYPE, QModelIndex()).data(EventTableModel.internalValueRole)
                if row_subtype == HeaderFooterSubtype.NEXTLEVEL:
                    row_format: Format = f_header_sub
                else:
                    row_format: Format = f_header_top
            elif row_type == RowType.FOOTER:
                row_subtype: HeaderFooterSubtype = self.model.index(row, HeaderFooterField.SUBTYPE, QModelIndex()).data(EventTableModel.internalValueRole)
                if row_subtype == HeaderFooterSubtype.NEXTLEVEL:
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
                            value = self.model.index(row, col, QModelIndex()).data(EventTableModel.internalValueRole)
                        if value == 0 and self.decimalcolumns_numbers.index(col) == len(self.decimalcolumns_numbers) - 1:
                            value = ""
                        else:
                            row_format.set_num_format("# ##0.00")
                        worksheet.write(row + self.HEADER_ROWS_NUMBER, col, value, row_format)
                    else:
                        worksheet.write(row + self.HEADER_ROWS_NUMBER, col, self.model.index(row, col, QModelIndex()).data(Qt.ItemDataRole.DisplayRole), row_format)
        #####################

        if str_bool(self.settings_handler.settings.value("Export/frozenheader")):
            worksheet.freeze_panes(self.HEADER_ROWS_NUMBER, 0)

        try:
            workbook.close()
            del worksheet
            del workbook
            self.last_path = xls_file_path
            if export_format == ExportFormat.PDF:
                if Path(pdf_file_path).exists():
                    pdf_file_path = pdf_file_path[:-4] + "_" + QTime().currentTime().toString("hhmmss") + ".pdf"
                xlsx_to_pdf_win32(temp_file_path, pdf_file_path)
                os.remove(temp_file_path)
                self.last_path = pdf_file_path
        except FileCreateError as e:
            msg_box: ErrorInfoMessageBox = ErrorInfoMessageBox(f"Не удалось записать файл \"ПлатежныйКалендарь_"
                                                               f"{xls_file_path if export_format == ExportFormat.XLSX else pdf_file_path}\". Возможно, файл "
                                                               f"с таким именем используется другим приложением или в настройках указан неверный путь.")
            msg_box.exec_()
            raise FileCreateError

        return True
