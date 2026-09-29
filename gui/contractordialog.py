from enum import IntEnum

from PySide6 import QtCore
from PySide6.QtCore import QDate
from PySide6.QtGui import QStandardItem, Qt
from PySide6.QtWidgets import QDialog, QListWidgetItem, QInputDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, \
    QDateTimeEdit, QDialogButtonBox, QDateEdit

from base.contract import ContractInfo
from base.date import str_date, date_displstr, date_str
from base.dbhandler import DBHandler
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.contractdialog import ContractDocumentDialog
from gui.ui.contractordialog_ui import Ui_ContractorDialog


class ContractInputDialog(QDialog):
    def __init__(self, parent=None, title="Ввод данных договора"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(300)
        main_layout = QVBoxLayout(self)

        num_layout = QHBoxLayout()
        self.num_label = QLabel("Номер договора:", self)
        self.num_input = QLineEdit(self)
        num_layout.addWidget(self.num_label)
        num_layout.addWidget(self.num_input)
        main_layout.addLayout(num_layout)

        date_layout = QHBoxLayout()
        self.date_label = QLabel("Дата договора:", self)
        self.date_input = QDateEdit(self)
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_label)
        date_layout.addWidget(self.date_input)
        main_layout.addLayout(date_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                        self)

        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("ОК")
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        main_layout.addWidget(self.buttons)

    def get_data(self):
        return self.num_input.text().strip(), self.date_input.date()

    @staticmethod
    def get_contract_info(parent=None, title="Данные договора"):
        dialog = ContractInputDialog(parent, title)
        result = dialog.exec()
        contract_num, contract_date = dialog.get_data()
        return contract_num, contract_date, result == QDialog.DialogCode.Accepted


class StackwidgetPage(IntEnum):
    contractors = 0
    contracts = 1
    documents = 2


class ContractorDialog(QDialog):


    def __init__(self, dbh: DBHandler, parent=None):
        super(ContractorDialog, self).__init__(parent)
        self.ui = Ui_ContractorDialog()
        self.ui.setupUi(self)

        self.dbh = dbh

        self.load_contractors()
        self.ui.le_filter.textChanged.connect(self.on_filter_change)

        self.ui.pb_cancel.clicked.connect(lambda: self.reject())
        self.ui.pb_continue_to_contracts.clicked.connect(self.on_continue_to_contracts)
        self.ui.pb_back_to_contractors.clicked.connect(self.on_back_to_contractors)
        self.ui.pb_continue_to_documents.clicked.connect(self.on_continue_to_documents)
        self.ui.pb_back_to_contracts.clicked.connect(self.on_back_to_contracts)
        self.ui.pb_accept.clicked.connect(self.accept)

    @staticmethod
    def _select_by_id(list_widget, item_id: int | None):
        if item_id:
            for i in range(list_widget.count()):
                if list_widget.item(i).data(Qt.ItemDataRole.UserRole) == item_id:
                    list_widget.setCurrentRow(i)
                    return
        list_widget.setCurrentRow(0)

    def load_contractors(self):
        contractors = self.dbh.load_contractors()
        if contractors is None:
            self.ui.pb_continue_to_contracts.setEnabled(False)
            return
        else:
            top_item = QListWidgetItem("< НОВЫЙ КОНТРАГЕНТ >")
            top_item.setData(Qt.ItemDataRole.UserRole, 0)
            self.ui.lw_contractor.addItem(top_item)
        for contractor in contractors:
            new_item = QListWidgetItem(contractor[1])
            new_item.setData(Qt.ItemDataRole.UserRole, contractor[0])
            self.ui.lw_contractor.addItem(new_item)
        self.ui.lw_contractor.sortItems(Qt.SortOrder.AscendingOrder)
        self.ui.lw_contractor.setCurrentRow(0)

    def on_filter_change(self):
        for i in range(1, self.ui.lw_contractor.count()):
            item = self.ui.lw_contractor.item(i)
            item.setHidden(self.ui.le_filter.text().lower() not in item.data(Qt.ItemDataRole.DisplayRole).lower())
        current_item = self.ui.lw_contractor.currentItem()
        if not current_item or current_item.isHidden():
            self.ui.lw_contractor.setCurrentRow(0)

    def on_continue_to_contracts(self):
        selected_item = self.ui.lw_contractor.selectedItems()[0]
        if selected_item.data(Qt.ItemDataRole.UserRole) == 0:
            text, ok = QInputDialog.getText(
                self,
                "Новый контрагент",
                "Введите название контрагента:"
            )
            if text and ok:
                if self.ui.lw_contractor.findItems(text, QtCore.Qt.MatchFlag.MatchExactly):
                    msg_box = ErrorInfoMessageBox("Контрагент с таким именем уже есть в списке", False, self)
                    msg_box.exec()
                    return
                new_id = self.dbh.add_contractor(text)
                if new_id:
                    new_item = QListWidgetItem(text)
                    new_item.setData(Qt.ItemDataRole.UserRole, new_id)
                    self.ui.lw_contractor.addItem(new_item)
                    self.ui.lw_contractor.setCurrentItem(new_item)
        else:
            self.load_contracts(self.ui.lw_contractor.selectedItems()[0].data(Qt.ItemDataRole.UserRole))
            self.ui.stw_main.setCurrentIndex(StackwidgetPage.contracts)

    def load_contracts(self, contractor_id: int, select_id: int | None = None):
        self.ui.lw_contract.clear()
        contracts = self.dbh.load_contracts(contractor_id) or []
        for contract in contracts:
            new_item = QListWidgetItem(f"{contract[1]} от {date_displstr(str_date(contract[2]))}")
            new_item.setData(Qt.ItemDataRole.UserRole, contract[0])
            new_item.setData(Qt.ItemDataRole.UserRole + 1, contract[1])
            new_item.setData(Qt.ItemDataRole.UserRole + 2, str_date(contract[2]))
            self.ui.lw_contract.addItem(new_item)
        self.ui.lw_contract.sortItems(Qt.SortOrder.AscendingOrder)

        top_item = QListWidgetItem("< НОВЫЙ ДОГОВОР >")
        top_item.setData(Qt.ItemDataRole.UserRole, 0)
        self.ui.lw_contract.insertItem(0, top_item)

        self._select_by_id(self.ui.lw_contract, select_id)

    def on_back_to_contractors(self):
        self.ui.stw_main.setCurrentIndex(StackwidgetPage.contractors)

    def on_continue_to_documents(self):
        selected_item = self.ui.lw_contract.selectedItems()[0]
        if selected_item.data(Qt.ItemDataRole.UserRole) == 0:
            number, date, ok = ContractInputDialog.get_contract_info(None, "Новый договор")
            if ok:
                if self.ui.lw_contract.findItems(f"{number} от {date_displstr(date)}", QtCore.Qt.MatchFlag.MatchExactly):
                    msg_box = ErrorInfoMessageBox("Договор с таким номером уже есть в списке", False, self)
                    msg_box.exec()
                    return
                new_id = self.dbh.add_contract(self.ui.lw_contractor.selectedItems()[0].data(Qt.ItemDataRole.UserRole), number, date_str(date))
                if new_id:
                    new_item = QListWidgetItem(f"{number} от {date_displstr(date)}")
                    new_item.setData(Qt.ItemDataRole.UserRole, new_id)
                    new_item.setData(Qt.ItemDataRole.UserRole + 1, number)
                    new_item.setData(Qt.ItemDataRole.UserRole + 2, date)
                    self.ui.lw_contract.addItem(new_item)
                    self.ui.lw_contract.setCurrentItem(new_item)
        else:
            self.load_documents(self.ui.lw_contract.selectedItems()[0].data(Qt.ItemDataRole.UserRole))
            self.ui.stw_main.setCurrentIndex(StackwidgetPage.documents)

    def load_documents(self, contract_id: int, select_id: int | None = None):
        self.ui.lw_document.clear()
        documents = self.dbh.load_documents(contract_id) or []
        for document in documents:
            new_item = QListWidgetItem(document[1])
            new_item.setData(Qt.ItemDataRole.UserRole, document[0])
            self.ui.lw_document.addItem(new_item)
        self.ui.lw_document.sortItems(Qt.SortOrder.AscendingOrder)

        top_item = QListWidgetItem("< НОВЫЙ ДОКУМЕНТ >")
        top_item.setData(Qt.ItemDataRole.UserRole, 0)
        self.ui.lw_document.insertItem(0, top_item)

        self._select_by_id(self.ui.lw_document, select_id)

    def on_back_to_contracts(self):
        self.ui.stw_main.setCurrentIndex(StackwidgetPage.contracts)

    def accept(self, /):
        contractor_item = self.ui.lw_contractor.selectedItems()[0]
        contract_item = self.ui.lw_contract.selectedItems()[0]
        document_item = self.ui.lw_document.selectedItems()[0]

        info = ContractInfo(
            contractor_id=contractor_item.data(Qt.ItemDataRole.UserRole),
            contractor_name=contractor_item.text(),
            contract_id=contract_item.data(Qt.ItemDataRole.UserRole),
            contract_number=contract_item.data(Qt.ItemDataRole.UserRole + 1),
            contract_date=contract_item.data(Qt.ItemDataRole.UserRole + 2),
        )
        dialog = ContractDocumentDialog(
            self.dbh, document_item.data(Qt.ItemDataRole.UserRole), info, self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_documents(info.contract_id, select_id=dialog.document_id)



