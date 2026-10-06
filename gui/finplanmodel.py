from typing import Any, Iterable, NamedTuple, Optional

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QFont, QColor

from base.formatting import int_strspace


class CategoryDef(NamedTuple):
    children: tuple[int, ...]
    row_label: str
    title: str
    bold: bool
    counts_execution: bool


class FinPlanTableModel(QAbstractTableModel):

    MONTHS_COUNT = 12

    FINPLAN_STRUCTURE = {
        10000: CategoryDef((), "1.", "Остаток средств на начало периода", True, False),
        20000: CategoryDef((21000, 22000, 23000), "2.", "Поступление денежных средств", True, True),
        21000: CategoryDef((), "2.1.", "выручка от реализации услуг", False, True),
        22000: CategoryDef((), "2.2.", "прочие доходы", False, True),
        23000: CategoryDef((23100, 23200), "2.3.", "кредиты и займы", False, True),
        23100: CategoryDef((), "2.3.1.", "овердрафт", False, True),
        23200: CategoryDef((), "2.3.2.", "кредит", False, True),
        30000: CategoryDef((31000, 32000, 33000), "3.", "Расходование денежных средств", True, True),
        31000: CategoryDef((31100, 31200), "3.1.", "текущая деятельность", True, True),
        31100: CategoryDef((31101, 31102, 31103), "3.1.1.", "переменные затраты", True, True),
        31101: CategoryDef((), "3.1.1.1.", "заработная плата с налогами", False, True),
        31102: CategoryDef((), "3.1.1.2.", "материалы", False, True),
        31103: CategoryDef((), "3.1.1.3.", "услуги сторонних организаций", False, True),
        31200: CategoryDef(
            (31201, 31202, 31203, 31204, 31205, 31206, 31207, 31208, 31209, 31210, 31211, 31212, 31213),
            "3.1.2.", "постоянные затраты", True, True,
        ),
        31201: CategoryDef((), "3.1.2.1", "налоги", False, True),
        31202: CategoryDef((), "3.1.2.2", "энергоносители", False, True),
        31203: CategoryDef((), "3.1.2.3", "маркетинг", False, True),
        31204: CategoryDef((), "3.1.2.4", "аренда офиса", False, True),
        31205: CategoryDef((), "3.1.2.5", "аренда помещений", False, True),
        31206: CategoryDef((), "3.1.2.6", "IT обслуживание", False, True),
        31207: CategoryDef((), "3.1.2.7", "обеспечение текущей деятельности", False, True),
        31208: CategoryDef((), "3.1.2.8", "обслуживание здания", False, True),
        31209: CategoryDef((), "3.1.2.9", "банковские расходы", False, True),
        31210: CategoryDef((), "3.1.2.10", "услуги связи", False, True),
        31211: CategoryDef((), "3.1.2.11", "комиссионное вознаграждение", False, True),
        31212: CategoryDef((), "3.1.2.12", "обучение персонала", False, True),
        31213: CategoryDef((), "3.1.2.13", "техническое обслуживание и страхование оборудования", False, True),
        32000: CategoryDef((32100, 32200, 32300), "3.2.", "финансовая деятельность", True, True),
        32100: CategoryDef((32101, 32102), "3.2.1.", "погашение кредитных обязательств", False, True),
        32101: CategoryDef((), "3.2.1.1", "погашение кредитов", False, True),
        32102: CategoryDef((), "3.2.1.2", "погашение лизинга", False, True),
        32200: CategoryDef((), "3.2.2", "погашение процентов по кредитам, займам", False, True),
        32300: CategoryDef((), "3.2.3", "погашение займов учредителям", False, True),
        33000: CategoryDef((), "3.3.", "инвестиционная деятельность", True, True),
        40000: CategoryDef((), "4.", "Остаток средств на конец периода", True, False),
    }

    HORIZONTAL_HEADER_LABELS = [
        "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
    ]

    EDGE_CATEGORIES = frozenset({10000, 40000})

    COLOR_EDGE_ROW = "#E2D5B8"
    COLOR_TOP_LEVEL_ROW = "#9EC1A3"
    COLOR_SECTION_ROW = "#EAF1E4"
    COLOR_SUBSECTION_ROW = "#F5F8F2"

    EditableRole: int = Qt.ItemDataRole.UserRole + 1
    internalValueRole: int = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent=None):
        super(FinPlanTableModel, self).__init__(parent)

        self.categories: list[int] = list(self.FINPLAN_STRUCTURE.keys())
        self.values: dict[int, list[Optional[int]]] = {
            category: [None] * self.MONTHS_COUNT for category in self.categories
        }

    # -- внутренние помощники -------------------------------------------------

    def _category_at_row(self, row: int) -> int:
        return self.categories[row]

    def _definition_at_row(self, row: int) -> CategoryDef:
        return self.FINPLAN_STRUCTURE[self._category_at_row(row)]

    def _row_background(self, category: int, definition: CategoryDef) -> Optional[QColor]:
        if category in self.EDGE_CATEGORIES:
            return QColor(self.COLOR_EDGE_ROW)
        if category % 10000 == 0:
            return QColor(self.COLOR_TOP_LEVEL_ROW)
        if definition.children:
            if category % 1000 == 0:
                return QColor(self.COLOR_SECTION_ROW)
            return QColor(self.COLOR_SUBSECTION_ROW)
        return None

    # -- расчёты ----------------------------------------------------------------

    def calculate_add_totals(self) -> None:
        def total_for(category: int) -> list[Optional[int]]:
            definition = self.FINPLAN_STRUCTURE[category]
            if not definition.children:
                return self.values[category]
            totals = [0] * self.MONTHS_COUNT
            for child in definition.children:
                child_values = total_for(child)
                for month, amount in enumerate(child_values):
                    if amount is not None:
                        totals[month] += amount
            self.values[category] = totals
            return totals

        for category in self.FINPLAN_STRUCTURE:
            total_for(category)

    # -- загрузка данных ----------------------------------------------------------

    def load_values(self, values: dict[int, list[Optional[int]]]) -> None:
        self.beginResetModel()
        for category in self.categories:
            loaded = values.get(category)
            if loaded is not None:
                self.values[category] = list(loaded)
        self.calculate_add_totals()
        self.endResetModel()

    # -- Qt model interface -------------------------------------------------------

    def rowCount(self, /, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.categories)

    def columnCount(self, /, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self.MONTHS_COUNT + 1

    def data(self, index, /, role=...) -> Any:
        if not index.isValid():
            return None

        category = self._category_at_row(index.row())
        definition = self._definition_at_row(index.row())
        is_label_column = index.column() == 0

        if role == Qt.ItemDataRole.DisplayRole:
            if is_label_column:
                return definition.title
            value = self.values[category][index.column() - 1]
            return int_strspace(value) if value is not None else ""

        elif role == self.internalValueRole:
            if is_label_column:
                return definition.title
            value = self.values[category][index.column() - 1]
            return value if value is not None else ""

        elif role == Qt.ItemDataRole.EditRole:
            if is_label_column:
                return None
            value = self.values[category][index.column() - 1]
            return value if value is not None else ""

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignLeft if is_label_column else Qt.AlignmentFlag.AlignRight

        elif role == Qt.ItemDataRole.FontRole:
            font = QFont()
            font.setBold(definition.bold)
            return font

        elif role == self.EditableRole:
            if is_label_column:
                return False
            return not bool(definition.children)

        elif role == Qt.ItemDataRole.BackgroundRole:
            return self._row_background(category, definition)

        return None

    def headerData(self, section, orientation, /, role=...) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.HORIZONTAL_HEADER_LABELS[section]
            if orientation == Qt.Orientation.Vertical:
                return self.FINPLAN_STRUCTURE[self.categories[section]].row_label
        return None

    def _assign_value(self, index: QModelIndex, value: Any) -> bool:
        if index.column() == 0:
            return False

        category = self._category_at_row(index.row())
        if self.FINPLAN_STRUCTURE[category].children:
            return False

        if value == "" or value is None:
            self.values[category][index.column() - 1] = None
        else:
            try:
                int_value = int(str(value).replace(" ", ""))
            except ValueError:
                return False
            self.values[category][index.column() - 1] = int_value

        return True

    def setData(self, index, value, /, role=...) -> bool:
        if role != Qt.ItemDataRole.EditRole:
            return False
        if not self._assign_value(index, value):
            return False

        self.calculate_add_totals()
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))
        return True

    def clear_values(self, indexes: Iterable[QModelIndex]) -> bool:
        changed = False
        for index in indexes:
            if self._assign_value(index, None):
                changed = True

        if changed:
            self.calculate_add_totals()
            self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))
        return changed

    def flags(self, index) -> Qt.ItemFlag:
        if index.data(self.EditableRole):
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
