from decimal import Decimal
from typing import *
from enum import auto, IntEnum
from dataclasses import dataclass, fields, astuple

import lovely_logger as log
from PySide6.QtCore import QModelIndex, Qt, QAbstractItemModel, Signal, QAbstractTableModel, QDate
from PySide6.QtGui import QFont

from base.date import date_displstr
from base.event import Event, TermRoleFlags, PaymentType, EventCategory, EventField, RowType
from base.formatting import float_strpercentage, dec_strcommaspace
from gui.filterwidget import TermCategory


class HeaderFooterField(IntEnum):
    NAME = 0
    TYPE = 1
    SUBTYPE = 2
    CATEGORY = 3
    ID = 4


class HeaderFooterSubtype(IntEnum):
    TOPLEVELNOEVENTS = auto()
    TOPLEVELWITHEVENTS = auto()
    NEXTLEVEL = auto()


# Атрибуты name, type и category должны иметь те же индексы, что и в классах Event и HeaderFooterField
@dataclass()
class EventHeader:
    name: str
    type: int
    subtype: int
    category: int
    id: int


# Атрибуты name, type и category должны иметь те же индексы, что и в классах Event и HeaderFooterField
@dataclass()
class EventFooter:
    name: str
    type: int
    subtype: int
    category: int
    id: int


# Атрибуты name, type и category должны иметь те же индексы, что и в классах Event и HeaderFooterField
@dataclass()
class FinalFooter:
    name: str
    type: int
    subtype: int
    category: int
    id: int


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


class EventTableModel(QAbstractTableModel):

    HEADERS = {
        EventField.ID: "",
        EventField.TYPE: "",
        EventField.CATEGORY: "Категория",
        EventField.RECEIVER: "Получатель платежа",
        EventField.NAME: "Наименование (предмет) платежа",
        EventField.TOTALAMOUNT: "Сумма платежа",
        EventField.REMAINAMOUNT: "Остаток платежа",
        EventField.PERCENTAGE: "Погашено",
        EventField.DUEDATE: "Дата платежа",
        EventField.PAYMENTTYPE: "Вид платежа",
        EventField.CREATEDATE: "Дата создания",
        EventField.DESCR: "Основание платежа",
        EventField.RESPONSIBLE: "Ответственное лицо",
        EventField.TODAYSHARE: "Оплата сегодня",
        EventField.TERMFLAGS: "",
        EventField.NOTES: "",
        EventField.LASTPAYMENTDATE: "",
        EventField.NDS: "",
    }

    ALIGNMENT = {
        EventField.ID: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        EventField.TYPE: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        EventField.CATEGORY: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        EventField.RECEIVER: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        EventField.NAME: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        EventField.REMAINAMOUNT: Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        EventField.TOTALAMOUNT: Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        EventField.PERCENTAGE: Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
        EventField.DUEDATE: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        EventField.PAYMENTTYPE: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        EventField.CREATEDATE: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        EventField.DESCR: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        EventField.RESPONSIBLE: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        EventField.TODAYSHARE: Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        EventField.TERMFLAGS: Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        EventField.NOTES: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        EventField.LASTPAYMENTDATE: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        EventField.NDS: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
    }

    CATEGORY_NAMES = {
        EventCategory.TOP_CURRENT: "1.   Текущая деятельность",
        EventCategory.SALARIES: "1.1.  Заработная плата с налогами на з/п",
        EventCategory.TAXES: "1.2.  Налоги и сборы",
        EventCategory.CONSUMABLES: "1.3.  Расходные материалы для медицинских центров",
        EventCategory.ENERGY: "1.4.  Энергоносители",
        EventCategory.MARKETING: "1.5.  Расходы на маркетинг",
        EventCategory.OFFICERENT: "1.6.  Расходы по аренде офисов",
        EventCategory.ROOMRENT: "1.7.  Расходы по аренде помещений",
        EventCategory.EQUIPMENT: "1.8.  Обслуживание оргтехники",
        EventCategory.CURRENT: "1.9.  Текущие расходы",
        EventCategory.BUILDINGMAINT: "1.10.  Расходы на обслуживание зданий и помещений",
        EventCategory.BANKING: "1.11.  Банковские расходы",
        EventCategory.TELECOM: "1.12.  Услуги связи",
        EventCategory.TRAINING: "1.13.  Расходы на обучение и повышение квалификации",
        EventCategory.THIRDPARTYSERVICES: "1.14.  Услуги сторонних организаций",
        EventCategory.COMMISSION: "1.15.  Комиссионные расходы",
        EventCategory.MEDEQREPAIR: "1.16.  Ремонт, обслуживание и страхование мед. оборудования",
        EventCategory.TOP_FINANCES: "2.    Финансовая деятельность",
        EventCategory.TOP_INVESTMENT: "3.    Инвестиционная деятельность",
    }

    NDS_VALUE = {
        EventCategory.TOP_CURRENT: 0,
        EventCategory.SALARIES: 0,
        EventCategory.TAXES: 0,
        EventCategory.CONSUMABLES: 10,
        EventCategory.ENERGY: 20,
        EventCategory.MARKETING: 20,
        EventCategory.OFFICERENT: 20,
        EventCategory.ROOMRENT: 20,
        EventCategory.EQUIPMENT: 20,
        EventCategory.CURRENT: 20,
        EventCategory.BUILDINGMAINT: 20,
        EventCategory.BANKING: 0,
        EventCategory.TELECOM: 25,
        EventCategory.TRAINING: 20,
        EventCategory.THIRDPARTYSERVICES: 20,
        EventCategory.COMMISSION: 20,
        EventCategory.MEDEQREPAIR: 20,
        EventCategory.TOP_FINANCES: 0,
        EventCategory.TOP_INVESTMENT: 20,
    }

    PAYMENTTYPE_NAMES = {
        PaymentType.NORMAL: "По факту",
        PaymentType.ADVANCE: "Предоплата",
    }

    internalValueRole: int = Qt.ItemDataRole.UserRole + 1
    customSpanRole: int = Qt.ItemDataRole.UserRole + 2   # True - объединить все столбцы с первым
    sortRole: int = Qt.ItemDataRole.UserRole + 3

    stats_recalculated = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.column_count = len(fields(Event))
        if self.column_count != len(EventField):
            log.c("Число столбцов в модели не совпадает с числом столбцов, объявленных для описания данных")
            raise ValueError

        self.event_list: List = []
        self.events_loaded: bool = False
        self.last_id: int = 0
        self.paid_minimum_date: QDate | None = None

        self.row_formatting: RowFormatting | None = None
        self.type_hints = list(get_type_hints(Event).values())

        # Создание пустого словаря для сбора статистики
        filter_term_emptydict = {TermCategory.UNPAID: [], TermCategory.DUE: [], TermCategory.TODAY: [],
                                 TermCategory.WEEK: [], TermCategory.MONTH: [], TermCategory.PAID: []}
        category_filter_notpaid_emptydict, category_filter_paid_emptydict = {0: []}, {0: []}
        for category in [c.value for c in EventCategory]:
            if category % 1000 != 0:
                category_filter_notpaid_emptydict[category] = []
                category_filter_paid_emptydict[category] = []
        self.stats = {
            "term_filter": filter_term_emptydict,
            "category_filter_notpaid": category_filter_notpaid_emptydict,
            "category_filter_paid": category_filter_paid_emptydict,
        }

        self.create_headersfooters()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.event_list)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self.column_count

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole) -> Any:
        try:
            if orientation == Qt.Orientation.Horizontal:
                if role == Qt.ItemDataRole.DisplayRole:
                    return self.HEADERS[section]
                elif role == Qt.ItemDataRole.ToolTipRole:
                    return ""
                elif role == Qt.ItemDataRole.TextAlignmentRole:
                    if section == EventField.PERCENTAGE:
                        return Qt.AlignmentFlag.AlignLeft
                    else:
                        return self.ALIGNMENT[section]
            return QAbstractItemModel.headerData(self, section, orientation, role)
        except KeyError:
            log.x("Для одного из стоблцов не заданы мета-данные")

    def display_value(self, event: Event, column) -> Any:
        if column == EventField.ID or column == EventField.TYPE:
            return ""
        elif column == EventField.CATEGORY:
            return self.CATEGORY_NAMES[event.category]
        elif column == EventField.RECEIVER:
            return event.receiver
        elif column == EventField.NAME:
            return event.name
        elif column == EventField.REMAINAMOUNT:
            return dec_strcommaspace(event.remainamount)
        elif column == EventField.TOTALAMOUNT:
            return dec_strcommaspace(event.totalamount)
        elif column == EventField.PERCENTAGE:
            return float_strpercentage(event.percentage)
        elif column == EventField.DUEDATE:
            return date_displstr(event.duedate)
        elif column == EventField.PAYMENTTYPE:
            return self.PAYMENTTYPE_NAMES[event.paymenttype]
        elif column == EventField.CREATEDATE:
            return date_displstr(event.createdate)
        elif column == EventField.DESCR:
            return event.descr
        elif column == EventField.RESPONSIBLE:
            return event.responsible
        elif column == EventField.TODAYSHARE:
            if event.todayshare == Decimal("0"):
                return ""
            else:
                return dec_strcommaspace(event.todayshare)
        elif column == EventField.NOTES:
            return event.notes
        elif column == EventField.LASTPAYMENTDATE:
            if event.lastpaymentdate.isValid():
                return date_displstr(event.lastpaymentdate)
            else:
                return ""
        else:
            return "<NO DISPLAY VALUE>"

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        try:
            entry = self.event_list[index.row()]
        except IndexError:
            return None

        if isinstance(entry, Event):
            if role == Qt.ItemDataRole.DisplayRole:
                return self.display_value(entry, index.column())
            elif role == self.internalValueRole:
                return list(vars(entry).values())[index.column()]
            elif role == self.sortRole:
                return entry.category
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return self.ALIGNMENT[index.column()]
            elif role == self.customSpanRole:
                return False
            elif role == Qt.ItemDataRole.FontRole:
                term_flags = index.siblingAtColumn(EventField.TERMFLAGS).data(self.internalValueRole)
                if TermRoleFlags.DUE in term_flags:
                    font = QFont()
                    font.setBold(self.row_formatting.due_textbold)
                    return font
                if TermRoleFlags.TODAY in term_flags:
                    font = QFont()
                    font.setBold(self.row_formatting.today_textbold)
                    return font

        elif isinstance(entry, EventHeader):
            if role == Qt.ItemDataRole.DisplayRole:
                if index.column() == HeaderFooterField.NAME:
                    return self.CATEGORY_NAMES[entry.category]
            elif role == self.internalValueRole:
                try:
                    return list(vars(entry).values())[index.column()]
                except IndexError:
                    return None
            elif role == self.sortRole:
                return entry.category
            elif role == self.customSpanRole:
                return True
            elif role == Qt.ItemDataRole.FontRole:
                font = QFont()
                font.setBold(self.row_formatting.header_textbold)
                return font
            else:
                return None

        elif isinstance(entry, EventFooter):
            if role == Qt.ItemDataRole.DisplayRole:
                if index.column() == 0:
                    return f"Всего по {self.CATEGORY_NAMES[entry.category][:5]}"
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return self.ALIGNMENT[index.column()]
            elif role == self.internalValueRole:
                try:
                    return list(vars(entry).values())[index.column()]
                except IndexError:
                    return None
            elif role == self.sortRole:
                return entry.category
            elif role == self.customSpanRole:
                return False
            elif role == Qt.ItemDataRole.FontRole:
                font = QFont()
                font.setBold(self.row_formatting.footer_textbold)
                return font
        elif isinstance(entry, FinalFooter):
            if role == Qt.ItemDataRole.DisplayRole:
                if index.column() == 0:
                    return "ВСЕГО"
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return self.ALIGNMENT[index.column()]
            elif role == self.internalValueRole:
                try:
                    return list(vars(entry).values())[index.column()]
                except IndexError:
                    return None
            elif role == self.sortRole:
                return 0
            elif role == Qt.ItemDataRole.FontRole:
                font = QFont()
                font.setBold(True)
                return font

        else:
            raise NotImplementedError(f"data() для класса {entry.__class__.__name__} не реализована")

    def setData(self, index, value, /, role=..., emit_datachanged: bool = True):
        if not index.isValid():
            return False
        try:
            entry = self.event_list[index.row()]
        except IndexError:
            return False
        if isinstance(entry, Event):
            if role == self.internalValueRole:
                if not isinstance(value, self.type_hints[index.column()]):
                    return False
                attr_name = fields(entry)[index.column()].name
                setattr(entry, attr_name, value)
                if emit_datachanged:
                    self.dataChanged.emit(index, index)
                return True
            else:
                return False
        else:
            return False

    def flags(self, index, /):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        entry = self.event_list[index.row()]
        if isinstance(entry, EventHeader) or isinstance(entry, EventFooter):
            flags = QAbstractItemModel.flags(self, index)
            return flags & ~Qt.ItemFlag.ItemIsSelectable
        else:
            return QAbstractItemModel.flags(self, index)

    def insertRows(self, row, count, /, parent = ...):
        if not self.last_id:
            return False
        self.beginInsertRows(parent, row, row + count - 1)
        for i in range(count):
            default_row = Event("", 0, self.last_id + 1, 0, "", Decimal(0), Decimal(0), 0.0, QDate(), 0, QDate(), "", "", Decimal(0), TermRoleFlags.NONE, "", QDate(), 0)
            self.event_list.append(default_row)
        self.endInsertRows()
        self.last_id += 1
        return True

    def removeRows(self, row, count, /, parent=...):
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        for i in range(count):
            self.event_list.pop(row + i)
        self.endRemoveRows()
        return True

    def append_row(self, data: list) -> bool:
        if len(data) != len(fields(Event)):
            raise IndexError("Набор передаваемых в append_row данных должен охватывать все атрибуты класса-хранителя, на месте ID ожидается <PLACEHOLDER>")
        position = self.rowCount(QModelIndex())
        if self.insertRows(position, 1, QModelIndex()):
            for column, value in enumerate(data):
                if column == EventField.ID:
                    continue
                index = self.index(position, column, QModelIndex())
                if not self.setData(index, value, self.internalValueRole):
                    self.removeRows(self.rowCount() - 1, 1)
                    raise ValueError(f"Не удалось записать данные {value} в столбец {list(EventField)[column]}")
            self.recalculate_stats()
            return True
        return False

    def edit_row(self, rindex: QModelIndex, data: list) -> bool:
        if len(data) != len(fields(Event)):
            raise IndexError("Набор передаваемых в edit_row данных должен охватывать все атрибуты класса-хранителя")
        for col, value in enumerate(data):
            index = rindex.siblingAtColumn(col)
            if not self.setData(index, value, self.internalValueRole):
                log.c(f"Не удалось записать данные {value} в столбец {list(EventField)[col]}")
                continue
        self.recalculate_stats()
        return True

    def delete_row(self, index: QModelIndex) -> int:
        event_id: int = index.siblingAtColumn(EventField.ID).data(EventTableModel.internalValueRole)
        if self.removeRow(index.row()):
            self.recalculate_stats()
            return event_id
        else:
            return 0

    def set_row_formatting(self, row_formatting: RowFormatting) -> bool:
        for var in astuple(row_formatting):
            if var is None:
                return False
        self.row_formatting = row_formatting
        return True

    def create_headersfooters(self) -> None:
        # К каждой категории (разделу и подразделу) создается по одному заголовку и одному футеру
        _id = 0
        for cat_id, name in self.CATEGORY_NAMES.items():
            # Подтипы: раздел без ивентов, раздел с ивентами, подраздел
            if cat_id % 1000 == 0:
                subtype = HeaderFooterSubtype.TOPLEVELNOEVENTS
            elif cat_id % 100 == 0:
                subtype = HeaderFooterSubtype.TOPLEVELWITHEVENTS
            else:
                subtype = HeaderFooterSubtype.NEXTLEVEL
            header = EventHeader(name, RowType.HEADER, subtype, cat_id, _id)
            self.event_list.append(header)
            footer = EventFooter(name, RowType.FOOTER, subtype, cat_id, _id)
            self.event_list.append(footer)
            _id += 1
        # Финальный футер
        self.event_list.append(FinalFooter("", RowType.FINALFOOTER, 0, 0, _id))

    def get_last_id(self) -> int:
        return max(self.event_list, key=lambda event: event.id).id

    def load_events(self, events: list[Event]) -> bool:
        if events and not self.events_loaded:
            self.event_list.extend(events)
            self.last_id = self.get_last_id()
            self.events_loaded = True
            return True
        else:
            return False

    def recalculate_stats(self) -> None:
        # Сброс текущих значений
        for stats_dict in ("term_filter", "category_filter_notpaid", "category_filter_paid"):
            for key in self.stats[stats_dict].keys():
                self.stats[stats_dict][key] = []

        for row in range(self.rowCount()):
            if self.index(row, EventField.TYPE, QModelIndex()). data(self.internalValueRole) == RowType.EVENT:
                term_flags = self.index(row, EventField.TERMFLAGS, QModelIndex()).data(self.internalValueRole)
                category = self.index(row, EventField.CATEGORY, QModelIndex()).data(self.internalValueRole)
                # Проверка на оплаченность
                if TermRoleFlags.PAID in term_flags:
                    last_payment_date = self.index(row, EventField.LASTPAYMENTDATE, QModelIndex()).data(self.internalValueRole)
                    if last_payment_date.isValid() and last_payment_date >= self.paid_minimum_date:
                        self.stats["term_filter"][TermCategory.PAID].append(category)
                        is_paid = True
                    else:
                        continue
                else:
                    self.stats["term_filter"][TermCategory.UNPAID].append(category)
                    is_paid = False

                    # Проверка на срок
                    if TermRoleFlags.DUE in term_flags:
                        self.stats["term_filter"][TermCategory.DUE].append(category)
                    elif TermRoleFlags.TODAY in term_flags:
                        self.stats["term_filter"][TermCategory.TODAY].append(category)
                    if TermRoleFlags.WEEK in term_flags:
                        self.stats["term_filter"][TermCategory.WEEK].append(category)
                    if TermRoleFlags.MONTH in term_flags:
                        self.stats["term_filter"][TermCategory.MONTH].append(category)

                # Проверка по категории
                event_category = self.data(self.index(row, EventField.CATEGORY, QModelIndex()), self.internalValueRole)
                if event_category in self.stats["category_filter_notpaid"].keys():
                    if is_paid:
                        self.stats["category_filter_paid"][event_category].append(category)
                        self.stats["category_filter_paid"][0].append(category)
                    else:
                        self.stats["category_filter_notpaid"][event_category].append(category)
                        self.stats["category_filter_notpaid"][0].append(category)

        # Передать новую статистику виджетам и прокси-модели
        self.stats_recalculated.emit(self.stats)
