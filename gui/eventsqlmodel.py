import decimal
from dataclasses import dataclass, astuple
from decimal import Decimal
from enum import IntEnum, auto, IntFlag
from typing import Any

from PySide6.QtCore import Qt, QModelIndex, Signal, QDate
from PySide6.QtSql import QSqlTableModel, QSqlDatabase, QSqlQuery

from base.date import date_displstr, str_date, date_str, get_date_diff, days_to_weekend, days_to_month
from base.formatting import dec_strcommaspace
from base.liability import CATEGORY_NAMES
from gui.filterwidget import TermCategory


@dataclass()
class RowFormatting:
    due_textbold: bool = False
    today_textbold: bool = True
    due_forecolor: str = "#aa0000"
    today_forecolor: str = "black"
    due_backcolor: str = "white"
    today_backcolor: str = "white"

    header_textbold: bool = False
    header_section_forecolor: str = "black"
    header_section_backcolor: str = "#ccdce3"
    header_subsection_forecolor: str = "black"
    header_subsection_backcolor: str = "#e4e0d9"

    footer_textbold: bool = False
    footer_section_forecolor: str = "black"
    footer_section_backcolor: str = "#decbc9"
    footer_subsection_forecolor: str = "black"
    footer_subsection_backcolor: str = "#e9dcdb"

    vertical_grid: bool = True
    zebra_style: bool = True


class FilterFlags(IntFlag):
    PAID = auto()
    NOTPAID = auto()
    DUE = auto()
    TODAY = auto()
    WEEK = auto()
    MONTH = auto()
    NONE = 0


class Col(IntEnum):
    RECEIVER = 0
    ID = 1
    TYPE = 2
    CATEGORY = 3
    SUBCATEGORY = 4
    NAME = 5
    REMAINAMOUNT = 6
    TOTALAMOUNT = 7
    NDS = 8
    DUEDATE = 9
    CREATEDATE = 10
    PAYMENTTYPE = 11
    DESCR = 12
    RESPONSIBLE = 13
    NOTES = 14
    TODAYSHARE = 15
    LASTPAYMENTDATE = 16
    FILTERFLAGS = 17
    FEATURED = 18
    HIDDEN = 19
    RECEIVERNOCASE = 20
    RESPONSIBLENOCASE = 21


class RowType(IntEnum):
    HEADER = auto()
    LIABILITY = auto()
    FOOTER = auto()
    FINALFOOTER = auto()


class HeaderFooterSubtype(IntEnum):
    ORDINARY = auto()
    TOPLEVELWITHEVENTS = auto()
    TOPLEVELNOEVENTS = auto()


class PaymentType(IntEnum):
    NORMAL = auto()
    ADVANCE = auto()


class LiabilitySqlTableModel(QSqlTableModel):

    beforeSelect = Signal()
    afterSelect = Signal()
    filterwidget_labels_changed = Signal(object, object)

    # 0 = заголовок, #1 = видимость
    COLUMN_DATA = {
        Col.RECEIVER: ("Получатель платежа", True),
        Col.ID: ("", False),
        Col.TYPE: ("", False),
        Col.CATEGORY: ("Категория", False),
        Col.SUBCATEGORY: ("", False),
        Col.NAME: ("Наименование (предмет) платежа", True),
        Col.REMAINAMOUNT: ("Остаток платежа", True),
        Col.TOTALAMOUNT: ("Сумма платежа", True),
        Col.NDS: ("", False),
        Col.DUEDATE: ("Дата платежа", True),
        Col.CREATEDATE: ("Дата создания", True),
        Col.PAYMENTTYPE: ("Вид платежа", True),
        Col.DESCR: ("Основание платежа", True),
        Col.RESPONSIBLE: ("Ответственное лицо", True),
        Col.NOTES: ("", False),
        Col.TODAYSHARE: ("Оплата сегодня", True),
        Col.LASTPAYMENTDATE: ("", False),
        Col.FILTERFLAGS: ("", False),
        Col.FEATURED: ("", True),
        Col.HIDDEN: ("", True),
        Col.RECEIVERNOCASE: ("", False),
        Col.RESPONSIBLENOCASE: ("", False),
    }

    DECIMAL_COLUMNS = [
        Col.REMAINAMOUNT, Col.TOTALAMOUNT, Col.TODAYSHARE
    ]

    PAYMENTTYPE_NAMES = {
        PaymentType.NORMAL: "По факту",
        PaymentType.ADVANCE: "Предоплата",
    }


    dbValueRole = Qt.ItemDataRole.UserRole + 1
    qtValueRole = Qt.ItemDataRole.UserRole + 2

    afterRowRemoval = Signal()


    def __init__(self, parent=None):
        super(LiabilitySqlTableModel, self).__init__(parent)

        self.current_date: QDate = QDate().currentDate()
        self.paid_minimum_date: QDate = QDate()
        self.next_select_norecalc: bool = False
        # temp
        self.row_formatting = RowFormatting()

        for key, val in self.COLUMN_DATA.items():
            self.setHeaderData(key, Qt.Orientation.Horizontal, val)


    def data(self, idx, /, role=...):
        if not idx.isValid():
            return None

        if role == self.dbValueRole:
            return super(LiabilitySqlTableModel, self).data(idx, Qt.ItemDataRole.DisplayRole)

        elif role == self.qtValueRole:
            try:
                if idx.column() in (Col.REMAINAMOUNT, Col.TOTALAMOUNT, Col.TODAYSHARE):
                    try:
                        return Decimal(idx.data(self.dbValueRole))
                    except decimal.InvalidOperation:
                        return Decimal(0)
                elif idx.column() in (Col.ID, Col.TYPE, Col.CATEGORY, Col. SUBCATEGORY, Col.PAYMENTTYPE, Col.NDS, Col.FEATURED):
                    return int(idx.data(self.dbValueRole))
                elif idx.column() in (Col.DUEDATE, Col.CREATEDATE):
                    return str_date(idx.data(self.dbValueRole))
                elif idx.column() == Col.FILTERFLAGS:
                    return FilterFlags(idx.data(self.dbValueRole))
                else:
                    return idx.data(self.dbValueRole)
            except (ValueError, TypeError):
                return None

        elif role == Qt.ItemDataRole.DisplayRole:
            # Итоговые строки
            if idx.siblingAtColumn(Col.TYPE).data(self.dbValueRole) == RowType.FOOTER:
                if idx.column() == Col.RECEIVER:
                    return f"Всего по {CATEGORY_NAMES[idx.siblingAtColumn(Col.CATEGORY).data(self.dbValueRole)][:5]}"
                else:
                    return ""
            elif idx.siblingAtColumn(Col.TYPE).data(self.dbValueRole) in (RowType.HEADER, RowType.FINALFOOTER) and idx.column() != Col.RECEIVER:
                return ""

            # Все строки
            if idx.column() == Col.PAYMENTTYPE:
                return self.PAYMENTTYPE_NAMES[idx.data(self.dbValueRole)]
            elif idx.column() in (Col.REMAINAMOUNT, Col.TOTALAMOUNT):
                return dec_strcommaspace(self.data(idx, self.qtValueRole))
            elif idx.column() in (Col.DUEDATE, Col.CREATEDATE):
                return date_displstr(self.data(idx, self.qtValueRole))
            elif idx.column() == Col.TODAYSHARE:
                try:
                    return dec_strcommaspace(idx.data(self.qtValueRole))
                except KeyError:
                    return ""

        return super(LiabilitySqlTableModel, self).data(idx, role)

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return self.COLUMN_DATA[section][0]
            elif role == Qt.ItemDataRole.ToolTipRole:
                return ""
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return Qt.AlignmentFlag.AlignHCenter
        return super(LiabilitySqlTableModel, self).headerData(section, orientation, role)

    def flags(self, index, /):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        if index.siblingAtColumn(Col.TYPE).data() != RowType.LIABILITY:
            return super(LiabilitySqlTableModel, self).flags(index) & ~Qt.ItemFlag.ItemIsSelectable
        else:
            return super(LiabilitySqlTableModel, self).flags(index)

    def select(self, recalculate_manual_data: bool = True):
        self.beforeSelect.emit()
        if not self.next_select_norecalc and recalculate_manual_data:
            self.calculate_manual_data()
            super(LiabilitySqlTableModel, self).select()
            self.insert_filterflags()
        result = super(LiabilitySqlTableModel, self).select()
        self.next_select_norecalc = False
        self.afterSelect.emit()
        return result

    def insert_row(self, data: list) -> bool:
        new_row_position: int = self.rowCount()
        self.insertRow(new_row_position)
        if len(data) != self.columnCount():
            raise IndexError("В новую строку передано неверное количество данных")
        return self.insert_data_in_row(new_row_position, data)

    def edit_row(self, row: int, data: list) -> bool:
        return self.insert_data_in_row(row, data)

    def insert_data_in_row(self, row: int, data: list) -> bool:
        for column, value in enumerate(data):
            if column == Col.ID:
                continue
            if not self.setData(self.index(row, column), value):
                return False
        return True

    # Функция возвращает ID удаленной строки (0 в случае неудачи)
    def delete_row(self, row: int) -> int:
        deleted_id: int = self.index(row, Col.ID).data(self.qtValueRole)
        return deleted_id if self.removeRow(row)else 0

    def removeRow(self, row, parent=QModelIndex()):
        result = super(LiabilitySqlTableModel, self).removeRow(row, parent)
        self.submitAll()
        return result

    def set_filters(self, term: TermCategory, category: int, receiver: str, responsible: str, paid_today: bool, paid_months_toshow: int, featured: bool) -> None:
        filt: str = f"(((filterflags = {int(FilterFlags.NONE)}) OR ("
        if term == TermCategory.PAID:
            filt += f"filterflags & {int(FilterFlags.PAID)} AND lastpaymentdate > '{date_str(self.current_date.addMonths(-paid_months_toshow))}' AND "
        else:
            filt += f"filterflags & {int(FilterFlags.NOTPAID)} AND "
            if term == TermCategory.DUE:
                filt += f"filterflags & {int(FilterFlags.DUE)} AND "
            elif term == TermCategory.TODAY:
                filt += f"filterflags & {int(FilterFlags.TODAY)} AND "
            elif term == TermCategory.WEEK:
                filt += f"filterflags & {int(FilterFlags.WEEK)} AND "
            elif term == TermCategory.MONTH:
                filt += f"filterflags & {int(FilterFlags.MONTH)} AND "
        filt = filt[:-5] + ")) AND "
        if category % 1000 != 0:
            filt += f"category = {category} AND "
        if receiver:
            filt += f"receivernocase LIKE '%{receiver.lower()}%' AND "
        if responsible:
            filt += f"responsiblenocase LIKE '%{responsible.lower()}%' AND "
        if paid_today:
            filt += f"todayshare <> '0.0' AND "
        if featured:
            filt += f"featured = 1 AND "
        filt = filt[:-5] + ")"

        self.send_filterwidget_labeldata(term, category, receiver, responsible, paid_today, paid_months_toshow, featured)
        self.next_select_norecalc = True
        self.setFilter(filt)

    def send_filterwidget_labeldata(self, term: TermCategory, category: int, receiver: str, responsible: str, paid_today: bool, paid_months_toshow: int, featured: bool) -> None:
        term_labels_dict = {}
        for term_category in TermCategory:
            filt = "WHERE "
            if term_category == TermCategory.PAID:
                filt += f"filterflags & {int(FilterFlags.PAID)} AND lastpaymentdate > '{date_str(self.current_date.addMonths(-paid_months_toshow))}' AND "
            else:
                filt += f"filterflags & {int(FilterFlags.NOTPAID)} AND "
                if term_category == TermCategory.DUE:
                    filt += f"filterflags & {int(FilterFlags.DUE)} AND "
                elif term_category == TermCategory.TODAY:
                    filt += f"filterflags & {int(FilterFlags.TODAY)} AND "
                elif term_category == TermCategory.WEEK:
                    filt += f"filterflags & {int(FilterFlags.WEEK)} AND "
                elif term_category == TermCategory.MONTH:
                    filt += f"filterflags & {int(FilterFlags.MONTH)} AND "
            if category % 1000 != 0:
                filt += f"category = {category} AND "
            if receiver:
                filt += f"receivernocase LIKE '%{receiver.lower()}%' AND "
            if responsible:
                filt += f"responsiblenocase LIKE '%{responsible.lower()}%' AND "
            if paid_today:
                filt += f"todayshare <> '0.0' AND "
            if featured:
                filt += f"featured = 1 AND "
            filt = filt[:-5]
            query = QSqlQuery(f"SELECT COUNT(id) from event {filt}")
            query.next()
            term_labels_dict[term_category] = query.value(0)

        category_labels_dict = {}
        for category in list(CATEGORY_NAMES.keys()):
            filt = "WHERE "
            if term == TermCategory.PAID:
                filt += f"filterflags & {int(FilterFlags.PAID)} AND "
            else:
                filt += f"filterflags & {int(FilterFlags.NOTPAID)} AND "
                if term == TermCategory.DUE:
                    filt += f"filterflags & {int(FilterFlags.DUE)} AND "
                elif term == TermCategory.TODAY:
                    filt += f"filterflags & {int(FilterFlags.TODAY)} AND "
                elif term == TermCategory.WEEK:
                    filt += f"filterflags & {int(FilterFlags.WEEK)} AND "
                elif term == TermCategory.MONTH:
                    filt += f"filterflags & {int(FilterFlags.MONTH)} AND "
            if category % 1000 != 0:
                filt += f"category = {category} AND "
            if receiver:
                filt += f"receivernocase LIKE '%{receiver.lower()}%' AND "
            if responsible:
                filt += f"responsiblenocase LIKE '%{responsible.lower()}%' AND "
            if paid_today:
                filt += f"todayshare <> '0.0' AND "
            if featured:
                filt += f"featured = 1 AND "
            filt = filt[:-5]
            query = QSqlQuery(f"SELECT COUNT(id) from event {filt}")
            query.next()
            category_labels_dict[category] = query.value(0)
        self.filterwidget_labels_changed.emit(term_labels_dict, category_labels_dict)

    def calculate_manual_data(self):
        query = QSqlQuery("UPDATE event SET remainamount = event.totalamount, todayshare = '0.0', lastpaymentdate = ''")
        query = QSqlQuery()
        query.prepare("UPDATE event "
                      "SET remainamount = remain_amount, todayshare = today_share, lastpaymentdate = lastpayment_date "
                      "FROM ("
                      "SELECT event.id AS event_id, "
                      "CAST(event.totalamount AS REAL) - SUM(CAST(payment.sum AS REAL)) AS remain_amount, "
                      "SUM(CASE WHEN payment.paymentdate = ? THEN CAST(payment.sum AS REAL) ELSE 0.0 END) AS today_share, "
                      "MAX(payment.paymentdate) AS lastpayment_date "
                      "FROM payment "
                      "INNER JOIN event ON event.id = payment.eventid "
                      "GROUP BY event.id) "
                      "WHERE id = event_id")
        query.addBindValue(f"'{date_str(self.current_date)}'")
        query.exec()

    def insert_filterflags(self):
        flags = []
        for row in range(self.rowCount()):
            row_id = self.index(row, Col.ID).data(self.dbValueRole)
            if self.index(row, Col.TYPE).data(self.dbValueRole) != RowType.LIABILITY:
                flags.append((row_id, FilterFlags.NONE))
            else:
                remain_amount = self.index(row, Col.REMAINAMOUNT).data(self.qtValueRole)
                duedate = self.index(row, Col.DUEDATE).data(self.qtValueRole)
                are_today_payments_present = self.index(row, Col.TODAYSHARE).data(self.qtValueRole) != Decimal(0.0)
                flags.append((row_id, self.calculate_filterflags(remain_amount, duedate, are_today_payments_present)))
        con = QSqlDatabase.database()
        con.transaction()
        query = QSqlQuery()
        query.prepare("UPDATE event SET filterflags = ? WHERE id = ?")
        for row_id, flag in flags:
            query.addBindValue(int(flag))
            query.addBindValue(row_id)
            if not query.exec():
                print(query.lastError().text())
        con.commit()

    def calculate_filterflags(self, remainamount: Decimal, duedate: QDate, are_today_payments_present: bool, current_date: QDate | None = None) -> FilterFlags:
        if not current_date:
            current_date = self.current_date
        filter_flags: FilterFlags = FilterFlags.NONE
        # Проверка на оплаченность
        if remainamount <= 0 and not are_today_payments_present:
            filter_flags |= FilterFlags.PAID
        else:
            filter_flags |= FilterFlags.NOTPAID
            # Проверка по дате
            date_diff = get_date_diff(current_date, duedate)
            if date_diff < 0:
                filter_flags |= FilterFlags.DUE
            if date_diff == 0:
                filter_flags |= FilterFlags.TODAY
            if -1 < date_diff <= days_to_weekend(current_date):
                filter_flags |= FilterFlags.WEEK
            if -1 < date_diff <= days_to_month(current_date):
                filter_flags |= FilterFlags.MONTH
        return filter_flags

    def recalculate_values_on_newpayment(self, index: QModelIndex, amount: Decimal, date: QDate, last_payment_date: QDate):

        old_remain: Decimal = index.siblingAtColumn(Col.REMAINAMOUNT).data(self.qtValueRole)
        new_remain: Decimal = old_remain - amount if old_remain - amount > 0.001 else Decimal(0)
        self.setData(index.siblingAtColumn(Col.REMAINAMOUNT), str(new_remain))

        old_today_amount: Decimal = index.siblingAtColumn(Col.TODAYSHARE).data(self.qtValueRole)
        if date == QDate.currentDate():
            today_share: Decimal = old_today_amount + amount
        else:
            today_share: Decimal = old_today_amount
        self.setData(index.siblingAtColumn(Col.TODAYSHARE), str(today_share))

        self.setData(index.siblingAtColumn(Col.LASTPAYMENTDATE), date_str(last_payment_date))

        new_filter_flags: FilterFlags = self.calculate_filterflags(new_remain, index.siblingAtColumn(Col.DUEDATE).data(self.qtValueRole), bool(today_share))
        self.setData(index.siblingAtColumn(Col.FILTERFLAGS), int(new_filter_flags))

    def recalculate_values_on_paymentdelete(self, index: QModelIndex, amount: Decimal, date: QDate, last_payment_date: QDate):

        old_remain: Decimal = index.siblingAtColumn(Col.REMAINAMOUNT).data(self.qtValueRole)
        new_remain: Decimal = old_remain + amount
        total_amount: Decimal = index.siblingAtColumn(Col.TOTALAMOUNT).data(self.qtValueRole)
        if new_remain > total_amount:
            new_remain = total_amount
        self.setData(index.siblingAtColumn(Col.REMAINAMOUNT), str(new_remain))

        old_today_amount: Decimal = index.siblingAtColumn(Col.TODAYSHARE).data(self.qtValueRole)
        if date == QDate.currentDate():
            today_share: Decimal = old_today_amount - amount
            self.setData(index.siblingAtColumn(Col.TODAYSHARE), str(today_share))
        else:
            today_share: Decimal = old_today_amount

        self.setData(index.siblingAtColumn(Col.LASTPAYMENTDATE), date_str(last_payment_date))

        new_filter_flags: FilterFlags = self.calculate_filterflags(new_remain, index.siblingAtColumn(Col.DUEDATE).data(self.qtValueRole), bool(today_share))
        self.setData(index.siblingAtColumn(Col.FILTERFLAGS), int(new_filter_flags))

    def set_row_formatting(self, row_formatting: RowFormatting) -> bool:
        for var in astuple(row_formatting):
            if var is None:
                return False
        self.row_formatting = row_formatting
        return True
