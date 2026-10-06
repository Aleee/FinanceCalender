from enum import IntEnum

from PySide6.QtCore import QDate, QSettings
from PySide6.QtGui import Qt, QIcon
from PySide6.QtWidgets import QDialog, QListWidgetItem, QInputDialog, QFormLayout, QLineEdit, QDialogButtonBox, \
    QDateEdit, QListWidget

from base.contract import ContractInfo
from base.date import str_date, date_displstr, date_str
from base.dbhandler import DBHandler
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.contractdialog import ContractDocumentDialog
from gui.ui.contractordialog_ui import Ui_ContractorDialog


class ContractInputDialog(QDialog):
    def __init__(self, parent=None, title="Данные договора"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(300)
        main_layout = QFormLayout(self)

        self.num_input = QLineEdit(self)
        main_layout.addRow("Номер договора:", self.num_input)

        self.date_input = QDateEdit(self)
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        main_layout.addRow("Дата договора:", self.date_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                        self)

        self.ok_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText("ОК")
        self.ok_button.setEnabled(False)
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")

        self.num_input.textChanged.connect(lambda text: self.ok_button.setEnabled(bool(text.strip())))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        main_layout.addRow(self.buttons)

    def get_data(self) -> tuple[str, QDate]:
        return self.num_input.text().strip(), self.date_input.date()

    @staticmethod
    def get_contract_info(parent=None, title="Данные договора") -> tuple[str, QDate, bool]:
        dialog = ContractInputDialog(parent, title)
        result = dialog.exec()
        contract_num, contract_date = dialog.get_data()
        return contract_num, contract_date, result == QDialog.DialogCode.Accepted


class StackwidgetPage(IntEnum):
    contractors = 0
    contracts = 1
    documents = 2


class ContractorDialog(QDialog):

    STEP_NAMES = ("Контрагент", "Договор", "Документ")

    def __init__(self, dbh: DBHandler, settings: QSettings, parent=None):
        super(ContractorDialog, self).__init__(parent)
        self.ui = Ui_ContractorDialog()
        self.ui.setupUi(self)

        self.dbh = dbh
        self.settings = settings

        self.load_contractors()
        self.ui.le_filter.textChanged.connect(self.on_filter_change)

        for button in (self.ui.pb_cancel, self.ui.pb_cancel_2, self.ui.pb_cancel_3):
            button.clicked.connect(self.reject)
        self.ui.pb_continue_to_contracts.clicked.connect(self.on_continue_to_contracts)
        self.ui.pb_back_to_contractors.clicked.connect(self.on_back_to_contractors)
        self.ui.pb_continue_to_documents.clicked.connect(self.on_continue_to_documents)
        self.ui.pb_back_to_contracts.clicked.connect(self.on_back_to_contracts)
        self.ui.pb_accept.clicked.connect(self.accept)

        self.ui.lw_contractor.itemDoubleClicked.connect(self.on_continue_to_contracts)
        self.ui.lw_contract.itemDoubleClicked.connect(self.on_continue_to_documents)
        self.ui.lw_document.itemDoubleClicked.connect(self.accept)
        self.ui.lw_document.currentItemChanged.connect(self.update_accept_button)

        self.show_page(StackwidgetPage.contractors)
        self.ui.le_filter.setFocus()

    @staticmethod
    def _select_by_id(list_widget, item_id: int | None):
        if item_id:
            for i in range(list_widget.count()):
                if list_widget.item(i).data(Qt.ItemDataRole.UserRole) == item_id:
                    list_widget.setCurrentRow(i)
                    return
        list_widget.setCurrentRow(0)

    @staticmethod
    def _current_id(list_widget: QListWidget) -> int | None:
        item = list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    @staticmethod
    def _make_new_item(text: str) -> QListWidgetItem:
        item = QListWidgetItem(QIcon(":/designer/icons/add.svg"), text)
        item.setData(Qt.ItemDataRole.UserRole, 0)
        font = item.font()
        font.setItalic(True)
        item.setFont(font)
        return item

    @staticmethod
    def _sort_below_new_item(list_widget: QListWidget) -> None:
        top_item = list_widget.takeItem(0)
        list_widget.sortItems(Qt.SortOrder.AscendingOrder)
        list_widget.insertItem(0, top_item)

    def show_page(self, page: StackwidgetPage) -> None:
        self.ui.stw_main.setCurrentIndex(page)
        steps = []
        for i, name in enumerate(self.STEP_NAMES):
            if i == page:
                steps.append(f"<b>{name}</b>")
            else:
                steps.append(f"<span style='color: gray'>{name}</span>")
        self.ui.lbl_steps.setText(" → ".join(steps))

        page_widgets = {
            StackwidgetPage.contractors: (self.ui.pb_continue_to_contracts, self.ui.lw_contractor),
            StackwidgetPage.contracts: (self.ui.pb_continue_to_documents, self.ui.lw_contract),
            StackwidgetPage.documents: (self.ui.pb_accept, self.ui.lw_document),
        }
        default_button, list_widget = page_widgets[page]
        default_button.setDefault(True)
        list_widget.setFocus()

    def load_contractors(self) -> None:
        contractors = self.dbh.load_contractors()
        if contractors is None:
            ErrorInfoMessageBox("Не удалось загрузить список контрагентов (см. подробнее лог)", False, self).exec()
            self.ui.pb_continue_to_contracts.setEnabled(False)
            return
        self.ui.lw_contractor.addItem(self._make_new_item("Новый контрагент"))
        for contractor in contractors:
            new_item = QListWidgetItem(contractor[1])
            new_item.setData(Qt.ItemDataRole.UserRole, contractor[0])
            self.ui.lw_contractor.addItem(new_item)
        self._sort_below_new_item(self.ui.lw_contractor)
        self.ui.lw_contractor.setCurrentRow(0)

    def on_filter_change(self) -> None:
        filter_text = self.ui.le_filter.text().lower()
        for i in range(1, self.ui.lw_contractor.count()):
            item = self.ui.lw_contractor.item(i)
            item.setHidden(filter_text not in item.data(Qt.ItemDataRole.DisplayRole).lower())
        current_item = self.ui.lw_contractor.currentItem()
        if not current_item or current_item.isHidden():
            self.ui.lw_contractor.setCurrentRow(0)

    def ask_contractor_name(self) -> str | None:
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Новый контрагент")
        dialog.setLabelText("Введите название контрагента:")
        dialog.setTextValue(self.ui.le_filter.text().strip())
        dialog.setOkButtonText("ОК")
        dialog.setCancelButtonText("Отмена")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialog.textValue().strip()

    def on_continue_to_contracts(self) -> None:
        contractor_id = self._current_id(self.ui.lw_contractor)
        if contractor_id is None:
            return
        if contractor_id == 0:
            text = self.ask_contractor_name()
            if not text:
                return
            for i in range(1, self.ui.lw_contractor.count()):
                if self.ui.lw_contractor.item(i).text().casefold() == text.casefold():
                    ErrorInfoMessageBox("Контрагент с таким именем уже есть в списке", False, self).exec()
                    return
            new_id = self.dbh.add_contractor(text)
            if not new_id:
                ErrorInfoMessageBox("Не удалось сохранить контрагента в базе данных (см. подробнее лог)", False, self).exec()
                return
            new_item = QListWidgetItem(text)
            new_item.setData(Qt.ItemDataRole.UserRole, new_id)
            self.ui.lw_contractor.addItem(new_item)
            self._sort_below_new_item(self.ui.lw_contractor)
            self.on_filter_change()
            self.ui.lw_contractor.setCurrentItem(new_item)
            contractor_id = new_id

        self.ui.label_2.setText(f"Договоры контрагента «{self.ui.lw_contractor.currentItem().text()}»:")
        self.load_contracts(contractor_id)
        self.show_page(StackwidgetPage.contracts)

    def load_contracts(self, contractor_id: int, select_id: int | None = None) -> None:
        self.ui.lw_contract.clear()
        contracts = self.dbh.load_contracts(contractor_id)
        if contracts is None:
            ErrorInfoMessageBox("Не удалось загрузить список договоров (см. подробнее лог)", False, self).exec()
            contracts = []
        for contract in contracts:
            new_item = QListWidgetItem(f"{contract[1]} от {date_displstr(str_date(contract[2]))}")
            new_item.setData(Qt.ItemDataRole.UserRole, contract[0])
            new_item.setData(Qt.ItemDataRole.UserRole + 1, contract[1])
            new_item.setData(Qt.ItemDataRole.UserRole + 2, str_date(contract[2]))
            self.ui.lw_contract.addItem(new_item)
        self.ui.lw_contract.sortItems(Qt.SortOrder.AscendingOrder)

        self.ui.lw_contract.insertItem(0, self._make_new_item("Новый договор"))

        self._select_by_id(self.ui.lw_contract, select_id)

    def on_back_to_contractors(self) -> None:
        self.show_page(StackwidgetPage.contractors)

    def on_continue_to_documents(self) -> None:
        contract_id = self._current_id(self.ui.lw_contract)
        if contract_id is None:
            return
        if contract_id == 0:
            number, date, ok = ContractInputDialog.get_contract_info(self, "Новый договор")
            if not ok:
                return
            for i in range(1, self.ui.lw_contract.count()):
                item = self.ui.lw_contract.item(i)
                if (item.data(Qt.ItemDataRole.UserRole + 1).casefold() == number.casefold()
                        and item.data(Qt.ItemDataRole.UserRole + 2) == date):
                    ErrorInfoMessageBox("Договор с таким номером и датой уже есть в списке", False, self).exec()
                    return
            new_id = self.dbh.add_contract(self._current_id(self.ui.lw_contractor), number, date_str(date))
            if not new_id:
                ErrorInfoMessageBox("Не удалось сохранить договор в базе данных (см. подробнее лог)", False, self).exec()
                return
            new_item = QListWidgetItem(f"{number} от {date_displstr(date)}")
            new_item.setData(Qt.ItemDataRole.UserRole, new_id)
            new_item.setData(Qt.ItemDataRole.UserRole + 1, number)
            new_item.setData(Qt.ItemDataRole.UserRole + 2, date)
            self.ui.lw_contract.addItem(new_item)
            self._sort_below_new_item(self.ui.lw_contract)
            self.ui.lw_contract.setCurrentItem(new_item)
            contract_id = new_id

        self.ui.label_3.setText(f"Документы по договору «{self.ui.lw_contract.currentItem().text()}»:")
        self.load_documents(contract_id)
        self.show_page(StackwidgetPage.documents)

    def load_documents(self, contract_id: int, select_id: int | None = None) -> None:
        self.ui.lw_document.clear()
        documents = self.dbh.load_documents(contract_id)
        if documents is None:
            ErrorInfoMessageBox("Не удалось загрузить список документов (см. подробнее лог)", False, self).exec()
            documents = []
        for document in documents:
            new_item = QListWidgetItem(document[1])
            new_item.setData(Qt.ItemDataRole.UserRole, document[0])
            self.ui.lw_document.addItem(new_item)
        self.ui.lw_document.sortItems(Qt.SortOrder.AscendingOrder)

        self.ui.lw_document.insertItem(0, self._make_new_item("Новый документ"))

        self._select_by_id(self.ui.lw_document, select_id)

    def update_accept_button(self) -> None:
        self.ui.pb_accept.setText("Создать" if self._current_id(self.ui.lw_document) == 0 else "Открыть")

    def on_back_to_contracts(self) -> None:
        self.show_page(StackwidgetPage.contracts)

    def accept(self, /) -> None:
        contractor_item = self.ui.lw_contractor.currentItem()
        contract_item = self.ui.lw_contract.currentItem()
        document_item = self.ui.lw_document.currentItem()
        if not (contractor_item and contract_item and document_item):
            return

        info = ContractInfo(
            contractor_id=contractor_item.data(Qt.ItemDataRole.UserRole),
            contractor_name=contractor_item.text(),
            contract_id=contract_item.data(Qt.ItemDataRole.UserRole),
            contract_number=contract_item.data(Qt.ItemDataRole.UserRole + 1),
            contract_date=contract_item.data(Qt.ItemDataRole.UserRole + 2),
        )
        dialog = ContractDocumentDialog(
            self.dbh, self.settings, document_item.data(Qt.ItemDataRole.UserRole), info, self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_documents(info.contract_id, select_id=dialog.document_id)
