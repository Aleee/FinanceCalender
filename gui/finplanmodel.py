from decimal import Decimal
from typing import Any, Iterable, Optional

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, Signal
from PySide6.QtGui import QFont, QColor

from base.finplan import FINPLAN_STRUCTURE, MONTHS_COUNT, CategoryDef, stored_amount, to_amount
from base.formatting import dec_strcommaspace


class FinPlanTableModel(QAbstractTableModel):

    MONTHS_COUNT = MONTHS_COUNT

    FINPLAN_STRUCTURE = FINPLAN_STRUCTURE

    HORIZONTAL_HEADER_LABELS = [
        "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
    ]

    EDGE_CATEGORIES = frozenset({10000, 40000})

    COLOR_EDGE_ROW = "#E2D5B8"
    COLOR_TOP_LEVEL_ROW = "#9EC1A3"
    COLOR_SECTION_ROW = "#EAF1E4"
    COLOR_SUBSECTION_ROW = "#F5F8F2"

    invalidInput = Signal()

    EditableRole: int = Qt.ItemDataRole.UserRole + 1
    internalValueRole: int = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent=None, read_only: bool = False):
        super(FinPlanTableModel, self).__init__(parent)

        self.read_only: bool = read_only

        self.categories: list[int] = list(self.FINPLAN_STRUCTURE.keys())
        self.values: dict[int, list[Optional[Decimal]]] = {
            category: [None] * self.MONTHS_COUNT for category in self.categories
        }

    # -- внутренние помощники -------------------------------------------------

    def _category_at_row(self, row: int) -> int:
        return self.categories[row]

    def _definition_at_row(self, row: int) -> CategoryDef:
        return self.FINPLAN_STRUCTURE[self._category_at_row(row)]

    to_amount = staticmethod(to_amount)

    @staticmethod
    def amount_text(amount: Decimal) -> str:
        return dec_strcommaspace(amount)

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
        def total_for(category: int) -> list[Optional[Decimal]]:
            definition = self.FINPLAN_STRUCTURE[category]
            if not definition.children:
                return self.values[category]
            totals = [Decimal(0)] * self.MONTHS_COUNT
            for child in definition.children:
                child_values = total_for(child)
                for month, amount in enumerate(child_values):
                    if amount is not None:
                        totals[month] += amount
            totals = [self.to_amount(amount) for amount in totals]
            self.values[category] = totals
            return totals

        for category in self.FINPLAN_STRUCTURE:
            total_for(category)

    # -- загрузка данных ----------------------------------------------------------

    def load_values(self, values: dict[int, list[Optional[Decimal]]]) -> None:
        self.beginResetModel()
        for category in self.categories:
            loaded = values.get(category)
            if loaded is not None:
                self.values[category] = [self.to_amount(amount) for amount in loaded]
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
            return self.amount_text(value) if value is not None else ""

        elif role == self.internalValueRole:
            if is_label_column:
                return definition.title
            value = self.values[category][index.column() - 1]
            return "" if value is None else stored_amount(value)

        elif role == Qt.ItemDataRole.EditRole:
            if is_label_column:
                return None
            value = self.values[category][index.column() - 1]
            return str(value).replace(".", ",") if value is not None else ""

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
        if self.read_only or index.column() == 0:
            return False

        category = self._category_at_row(index.row())
        if self.FINPLAN_STRUCTURE[category].children:
            return False

        amount = self.to_amount(value)
        if amount is None and not (value == "" or value is None):
            self.invalidInput.emit()
            return False
        self.values[category][index.column() - 1] = amount

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
        if index.data(self.EditableRole) and not self.read_only:
            return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
