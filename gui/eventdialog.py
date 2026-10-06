from dataclasses import dataclass

import lovely_logger as log

from PySide6.QtCore import QModelIndex, Qt, QDate, QObject, Signal, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QDialog, QButtonGroup, QCompleter, QLineEdit, QMenu, QToolButton, QComboBox
from decimal import Decimal

from base.casting import str_bool
from base.date import date_str, MONTHS_RU
from base.dbhandler import DBHandler
from gui.eventsqlmodel import LiabilitySqlTableModel, Col
from gui.common import model_atlevel, map_to_source
from gui.commonwidgets.eventfilter import NoWheelFilter
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.paymenthistorymodel import PaymentHistoryTableModel
from gui.responsiblemodels import ResponsibleCategorySortModel
from gui.settings import SettingsHandler
from gui.ui.eventdialog_ui import Ui_EventDialog
from base.liability import LiabilityCategory, LiabilityFinanceSubcategory, CATEGORY_NAMES, NDS_VALUE, FilterFlags, RowType, PaymentType, calculate_filterflags
from base.contract import PaymentDueType, SavedContractValues
from base.paymentdate import calculate_payment_date
from base.workcalendar import WEEKDAY_ABBR


class ContractSelector(QObject):

    documentIdChanged = Signal(object)

    def __init__(self, db: DBHandler, cmb_contractor: QComboBox, cmb_contract: QComboBox, cmb_document: QComboBox, parent=None):
        super().__init__(parent)
        self.db = db
        self.cmb_contractor = cmb_contractor
        self.cmb_contract = cmb_contract
        self.cmb_document = cmb_document
        self.doc_id = None

        self._setup_contractor_combo()

        self.cmb_contract.setEnabled(False)
        self.cmb_document.setEnabled(False)

        self.cmb_contractor.currentIndexChanged.connect(self._on_contractor_changed)
        self.cmb_contract.activated.connect(self._on_contract_activated)
        self.cmb_document.currentIndexChanged.connect(self._emit_if_changed)

        self.reload()

    def selected_document_id(self) -> int | None:
        return self.doc_id

    def reload(self):
        cmb = self.cmb_contractor
        cmb.blockSignals(True)
        cmb.clear()
        for cid, name in self.db.load_contractors_for_combobox() or []:
            cmb.addItem(name, cid)
        cmb.setCurrentIndex(-1)
        cmb.blockSignals(False)
        self._reload_contracts(None)

    # ---------- комбобокс контрагентов ----------
    def _setup_contractor_combo(self):
        cmb = self.cmb_contractor
        cmb.setEditable(True)
        cmb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        completer = QCompleter(cmb.model(), cmb)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        cmb.setCompleter(completer)

        cmb.lineEdit().editingFinished.connect(self._on_contractor_text_committed)

    def _on_contractor_text_committed(self):
        cmb = self.cmb_contractor
        text = cmb.lineEdit().text().strip()
        if not text:
            cmb.setCurrentIndex(-1)
            return
        idx = cmb.findText(text, Qt.MatchFlag.MatchFixedString)
        if idx >= 0:
            cmb.setCurrentIndex(idx)
        else:
            cur = cmb.currentIndex()
            cmb.lineEdit().setText(cmb.itemText(cur) if cur >= 0 else "")

    def _on_contractor_changed(self, index: int):
        contractor_id = self.cmb_contractor.itemData(index) if index >= 0 else None
        self._reload_contracts(contractor_id)

    # ---------- комбобокс договоров ----------
    def _reload_contracts(self, contractor_id: int | None,
                          prefer_contract_id: int | None = None,
                          prefer_document_id: int | None = None):
        cmb = self.cmb_contract
        cmb.blockSignals(True)
        cmb.clear()

        rows = []
        if contractor_id is not None:
            rows = self.db.load_contracts_for_combobox(contractor_id) or []
        for cid, name in rows:
            cmb.addItem(name, cid)

        if rows:
            idx = -1
            if prefer_contract_id is not None:
                idx = cmb.findData(prefer_contract_id)
            if idx < 0:
                last = self.db.load_last_contract_id(contractor_id)
                if last is not None:
                    idx = cmb.findData(last)
            cmb.setCurrentIndex(idx if idx >= 0 else 0)
            cmb.setEnabled(True)
        else:
            cmb.setCurrentIndex(-1)
            cmb.setEnabled(False)
        cmb.blockSignals(False)

        self._reload_documents(prefer_document_id)

    def _on_contract_activated(self, index: int):
        contract_id = self.cmb_contract.itemData(index)
        contractor_id = self.cmb_contractor.currentData()
        if contract_id is not None and contractor_id is not None:
            self.db.save_last_contract_id(contractor_id, contract_id)
        self._reload_documents()

    # ---------- комбобокс документов ----------
    def _reload_documents(self, prefer_document_id: int | None = None):
        cmb = self.cmb_document
        contract_id = (self.cmb_contract.currentData() if self.cmb_contract.isEnabled() else None)

        cmb.blockSignals(True)
        cmb.clear()
        rows = []
        if contract_id is not None:
            rows = self.db.load_contract_documents_for_combobox(contract_id) or []
        for did, name in rows:
            cmb.addItem(name, did)

        idx = cmb.findData(prefer_document_id) if prefer_document_id is not None else -1
        if rows:
            cmb.setCurrentIndex(idx if idx >= 0 else 0)
        else:
            cmb.setCurrentIndex(-1)
        cmb.setEnabled(bool(rows))
        cmb.blockSignals(False)

        self._emit_if_changed()

    # ---------- сигнал ----------
    def _emit_if_changed(self, *_):
        cmb = self.cmb_document
        new_id = cmb.currentData() if (cmb.isEnabled() and cmb.currentIndex() >= 0) else None
        if new_id != self.doc_id:
            self.doc_id = new_id
            self.documentIdChanged.emit(new_id)

    def set_document_id(self, document_id: int | None) -> bool:
        if document_id is None:
            self.cmb_contractor.setCurrentIndex(-1)
            return True

        parents = self.db.load_document_parents(document_id)
        if parents is None:
            return False
        contractor_id, contract_id = parents

        idx = self.cmb_contractor.findData(contractor_id)
        if idx < 0:
            return False

        self.cmb_contractor.blockSignals(True)
        self.cmb_contractor.setCurrentIndex(idx)
        self.cmb_contractor.blockSignals(False)

        self._reload_contracts(contractor_id, prefer_contract_id=contract_id, prefer_document_id=document_id)
        return self.doc_id == document_id


class EventDialog(QDialog):

    NDS_COMBOBOX = [("нет", 0), ("10%", 10), ("20%", 20), ("25%", 25)]
    SUBCATEGORY_COMBOBOX = [("", 0), ("Погашение кредита", int(LiabilityFinanceSubcategory.LOAN)), ("Погашение лизинга", int(LiabilityFinanceSubcategory.LEASING)),
                            ("Погашение процентов", int(LiabilityFinanceSubcategory.INTEREST)), ("Погашение займов учредителям", int(LiabilityFinanceSubcategory.FOUNDERLOAN))]

    DOCUMENT_NAME_MAX_LEN = 30

    DESCR_COMPLETER_LIST = ["Акт сдачи-приемки оказанных услуг №", "ТТН №", "ТН №", "Договор №", "Приложение №", "Счет на оплату №",
                            "Договор аренды №", "Счет №", "Акт выполненных работ №", "Счет на оплату №", "Акт сдачи-приемки оказанных услуг №",
                            "Акт оказания услуг №", "Акт №", "Акт сдачи-приемки выполненных работ №", "Счет-акт оказанных услуг", "Реестр №",
                            "Счет-фактура №", "Договор финансового лизинга №", "Договор лизинга №", "Кредитный договор №", "Договор поставки №"]

    def __init__(self, final_proxy_model, responsible_model: ResponsibleCategorySortModel, payment_model: PaymentHistoryTableModel, db_handler: DBHandler,
                 settings_handler: SettingsHandler, edit_mode: bool = False, copy_mode: bool = False, current_index: QModelIndex | None = None, parent=None):
        super(EventDialog, self).__init__(parent)
        self.ui = Ui_EventDialog()
        self.ui.setupUi(self)

        self.model = final_proxy_model
        self.responsible_model: ResponsibleCategorySortModel = responsible_model
        self.payment_model: PaymentHistoryTableModel = payment_model
        self.dbh = db_handler
        self.sh = settings_handler
        self.edit_mode: bool = edit_mode
        self.copy_mode: bool = copy_mode
        self.non_editable_values: dict = {"id": 0, "paidamount": Decimal(0), "todayshare": Decimal(0)}
        self.sidepanel_visibility: bool = False

        self.index: QModelIndex = current_index if current_index is not None else QModelIndex()
        self.contractdocument_id = (self.index.siblingAtColumn(Col.CONTRACTDOCUMENTID).data(LiabilitySqlTableModel.qtValueRole)
                                    if (edit_mode or copy_mode) else 0)

        self.tb_position_menu = QMenu(self)

        self.button_group: QButtonGroup = QButtonGroup(self)
        self.button_group.addButton(self.ui.rb_typenormal, PaymentType.NORMAL)
        self.button_group.addButton(self.ui.rb_typeadvance, PaymentType.ADVANCE)
        self.button_group.addButton(self.ui.rb_typerefund, PaymentType.REFUND)
        self.ui.cmb_category.activated.connect(lambda: self.resort_responsible_cmb(self.ui.cmb_category.currentData(Qt.ItemDataRole.UserRole), auto_choice=True))
        self.ui.pb_toggle.clicked.connect(lambda: self.change_sidepanel_visibility(not self.sidepanel_visibility, True))
        self.ui.pb_applypaymentdate.clicked.connect(self.apply_payment_date)
        self.ui.pb_bindcontract.clicked.connect(self.bind_contract)
        self.ui.pb_fillwithvalues.clicked.connect(self.fill_with_contract_values)
        self.ui.pb_savevalues.clicked.connect(self.save_contract_values)
        self.ui.tb_unbindcontract.clicked.connect(self.unbind_contract)
        self.ui.pb_accept.clicked.connect(self.accept)
        self.ui.pb_cancel.clicked.connect(self.reject)

        self.no_wheel_filter = NoWheelFilter(self)
        for widget in (self.ui.dsb_totalamount, self.ui.de_incurrencedate, self.ui.de_duedate, self.ui.cmb_category,
                       self.ui.cmb_subcategory, self.ui.cmb_nds, self.ui.cmb_responsible):
            widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            widget.installEventFilter(self.no_wheel_filter)

        self.set_completers()
        self.fit_textedit_height(self.ui.te_name, self.ui.te_descr)

        # Заполнение комбобоксов
        self.ui.cmb_category.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.ui.cmb_category.setMinimumContentsLength(18)
        for cat_id, cat_name in CATEGORY_NAMES.items():
            if cat_id % 1000 != 0:
                self.ui.cmb_category.addItem(cat_name, int(cat_id))
        for row in self.NDS_COMBOBOX:
            self.ui.cmb_nds.addItem(row[0], row[1])
        for row in self.SUBCATEGORY_COMBOBOX:
            self.ui.cmb_subcategory.addItem(row[0], row[1])
        self.ui.cmb_responsible.setModel(self.responsible_model)
        self.positions: list = self.dbh.load_positions() or []

        self.ui.tb_responsible.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.ui.tb_responsible.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        self.populate_position_toolbutton()

        self._doc_terms = None
        self.calculated_payment_date: QDate | None = None

        self.ui.de_paymenttrigger.setDate(QDate.currentDate())

        self.ui.cmb_paymentperiodmonth.currentIndexChanged.connect(self.recalc_payment_date)
        self.ui.spb_paymentperiodyear.valueChanged.connect(self.recalc_payment_date)
        self.ui.de_paymenttrigger.dateChanged.connect(self.recalc_payment_date)

        self.ui.wdg_contractterms.hide()

        # TEMP
        # self.ui.widget.hide()

        self.selector = ContractSelector(self.dbh,
                                         self.ui.cmb_contractor,
                                         self.ui.cmb_contract,
                                         self.ui.cmb_document,
                                         self)
        self.selector.documentIdChanged.connect(self.on_document_changed)
        for cmb in (self.ui.cmb_contractor, self.ui.cmb_contract, self.ui.cmb_document):
            cmb.currentTextChanged.connect(cmb.setToolTip)

        self.ui.cmb_category.currentIndexChanged.connect(lambda row_num: self.set_subcategory_visible(
            self.ui.cmb_category.currentData() == LiabilityCategory.TOP_FINANCES))
        for month_num, month_name in enumerate(MONTHS_RU, start=1):
            self.ui.cmb_paymentperiodmonth.addItem(month_name, month_num)

        today = QDate.currentDate()
        self.ui.cmb_paymentperiodmonth.setCurrentIndex(today.month() - 1)
        self.ui.spb_paymentperiodyear.setValue(today.year())

        if self.edit_mode:
            self.setWindowTitle("Редактирование платежа")
            self.ui.pb_accept.setText("Применить")
            # Сохранение значений, которые не будут напрямую редактироваться
            self.non_editable_values["id"] = self.index.siblingAtColumn(Col.ID).data(LiabilitySqlTableModel.qtValueRole)
            self.non_editable_values["paidamount"] = (self.index.siblingAtColumn(Col.TOTALAMOUNT).data(LiabilitySqlTableModel.qtValueRole)
                                                      - self.index.siblingAtColumn(Col.REMAINAMOUNT).data(LiabilitySqlTableModel.qtValueRole))
            self.non_editable_values["todayshare"] = self.index.siblingAtColumn(Col.TODAYSHARE).data(LiabilitySqlTableModel.qtValueRole)
            self.non_editable_values["lastpaymentdate"] = self.index.siblingAtColumn(Col.LASTPAYMENTDATE).data(LiabilitySqlTableModel.qtValueRole)
            self.non_editable_values["featured"] = self.index.siblingAtColumn(Col.FEATURED).data(LiabilitySqlTableModel.qtValueRole)

        if self.edit_mode or self.copy_mode:
            # Заполнить имеющимися значениями
            self.ui.le_receiver.setText(self.index.siblingAtColumn(Col.RECEIVER).data(LiabilitySqlTableModel.qtValueRole))
            self.ui.te_name.setPlainText(self.index.siblingAtColumn(Col.NAME).data(LiabilitySqlTableModel.qtValueRole))
            self.ui.dsb_totalamount.setValue(self.index.siblingAtColumn(Col.TOTALAMOUNT).data(LiabilitySqlTableModel.qtValueRole))
            self.ui.de_duedate.setDate(self.index.siblingAtColumn(Col.DUEDATE).data(LiabilitySqlTableModel.qtValueRole))
            if self.edit_mode:
                self.ui.de_incurrencedate.setDate(self.index.siblingAtColumn(Col.INCURRENCEDATE).data(LiabilitySqlTableModel.qtValueRole))
            else:
                self.ui.de_incurrencedate.setDate(QDate.currentDate())
            # Сортировка персонала по категории (начальная)
            self.resort_responsible_cmb(self.index.siblingAtColumn(Col.CATEGORY).data(LiabilitySqlTableModel.qtValueRole), auto_choice=False)
            cmb_index: int = self.ui.cmb_category.findData(self.index.siblingAtColumn(Col.CATEGORY).data(LiabilitySqlTableModel.qtValueRole))
            self.ui.cmb_category.setCurrentIndex(cmb_index)
            cmb_index: int = self.ui.cmb_subcategory.findData(self.index.siblingAtColumn(Col.SUBCATEGORY).data(LiabilitySqlTableModel.qtValueRole))
            self.ui.cmb_subcategory.setCurrentIndex(cmb_index)
            if self.index.siblingAtColumn(Col.PAYMENTTYPE).data(LiabilitySqlTableModel.qtValueRole):
                self.button_group.button(self.index.siblingAtColumn(Col.PAYMENTTYPE).data(LiabilitySqlTableModel.qtValueRole)).setChecked(True)
            else:
                self.button_group.button(PaymentType.NORMAL).setChecked(True)
            cmb_index: int = self.ui.cmb_nds.findData(self.index.siblingAtColumn(Col.NDS).data(LiabilitySqlTableModel.qtValueRole))
            self.ui.cmb_nds.setCurrentIndex(cmb_index)
            cmb_index: int = self.ui.cmb_responsible.findData(self.index.siblingAtColumn(Col.RESPONSIBLE).data(LiabilitySqlTableModel.qtValueRole))
            self.ui.cmb_responsible.setCurrentIndex(cmb_index)
            self.ui.chb_hidden.setChecked(bool(self.index.siblingAtColumn(Col.HIDDEN).data(LiabilitySqlTableModel.qtValueRole)))
            self.ui.te_descr.setPlainText(self.index.siblingAtColumn(Col.DESCR).data(LiabilitySqlTableModel.qtValueRole))
            self.ui.te_notes.setPlainText(self.index.siblingAtColumn(Col.NOTES).data(LiabilitySqlTableModel.qtValueRole))
            self.set_subcategory_visible(self.ui.cmb_category.currentData() == LiabilityCategory.TOP_FINANCES)
            self.ui.dsb_totalamount.setFocus()
            QTimer.singleShot(0, self.ui.dsb_totalamount.selectAll)
            if self.contractdocument_id:
                if self.selector.set_document_id(self.contractdocument_id):
                    self.show_bound_contract(self.selected_document_title())
                else:
                    self.show_bound_contract("документ не найден")
            else:
                self.show_bound_contract("")

        else:
            self.resort_responsible_cmb(self.ui.cmb_category.currentData(Qt.ItemDataRole.UserRole), auto_choice=True)
            self.ui.de_duedate.setDate(QDate.currentDate())
            self.ui.de_incurrencedate.setDate(QDate.currentDate())
            self.ui.rb_typenormal.setChecked(True)
            self.set_subcategory_visible(False)
            self.show_bound_contract("")
            self.ui.le_receiver.setFocus()

        self.ui.de_paymenttrigger.setDate(self.ui.de_incurrencedate.date())
        self.ui.de_incurrencedate.dateChanged.connect(self.ui.de_paymenttrigger.setDate)
        self.update_contract_buttons()

        # Сигнал: изменение НДС при изменении категории
        self.ui.cmb_category.currentIndexChanged.connect(self.change_nds)
        # Сигнал: корректировка даты создания при изменении даты платежа пользователем
        self.ui.de_duedate.dateChanged.connect(lambda new_date: self.adjust_incurrencedate(new_date))

        self.sidepanel_visibility = str_bool(self.sh.settings.value("Eventdialog/sidepanel"), False)
        self.change_sidepanel_visibility(self.sidepanel_visibility)

    @staticmethod
    def fit_textedit_height(*text_edits, lines: int = 2, reserve: int = 4) -> None:
        for text_edit in text_edits:
            text_edit.ensurePolished()
            height = (lines * text_edit.fontMetrics().lineSpacing()
                      + 2 * int(text_edit.document().documentMargin())
                      + 2 * text_edit.frameWidth() + reserve)
            text_edit.setFixedHeight(height)

    def adjust_incurrencedate(self, new_date: QDate):
        if new_date < QDate.currentDate() and self.ui.de_incurrencedate.date() > new_date:
            self.ui.de_incurrencedate.setDate(new_date)

    def resort_responsible_cmb(self, new_category: int, auto_choice: bool):
        self.responsible_model.resort(new_category)
        if auto_choice:
            try:
                self.ui.cmb_responsible.setCurrentIndex(1)
            except IndexError:
                pass

    @staticmethod
    def _stripped(text: str) -> str:
        # убираем пробелы и переносы строк по краям, чтобы в БД не попадали "хвосты" от Enter/пробела
        return text.strip()

    def set_completers(self):
        self.ui.te_descr.completions.setStringList(self.DESCR_COMPLETER_LIST)
        self.install_standard_completer("receiver", self.ui.le_receiver)
        self.ui.te_name.ignore_return = True
        self.ui.te_name.whole_text_completion = True
        self.ui.te_name.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.ui.te_name.completions.setStringList(sorted(self.dbh.load_column_values("name", as_set=True) or []))

    def install_standard_completer(self, db_column: str, lineedit: QLineEdit):
        receiver_set: set | list | None = self.dbh.load_column_values(db_column, as_set=True)
        if not receiver_set:
            return
        receiver_compl = QCompleter(list(receiver_set))
        receiver_compl.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        receiver_compl.setFilterMode(Qt.MatchFlag.MatchContains)
        lineedit.setCompleter(receiver_compl)

    def populate_position_toolbutton(self) -> None:
        for pos_id, dept_id, pos_name in self.positions:
            action = QAction(pos_name, self)
            action.setData(pos_id)
            self.tb_position_menu.addAction(action)
        self.ui.tb_responsible.setMenu(self.tb_position_menu)
        self.tb_position_menu.triggered.connect(self.pick_responsible_by_position)

    def pick_responsible_by_position(self, action: QAction) -> None:
        position_id = action.data()
        if not position_id:
            return
        person_id = self.dbh.resolve_position_to_personal(position_id)
        if person_id is None:
            ErrorInfoMessageBox("На эту должность сейчас никто не назначен. Выберите ответственного вручную.").exec()
            return
        cmb_index = self.ui.cmb_responsible.findData(person_id)
        if cmb_index == -1:
            ErrorInfoMessageBox("Работник, занимающий эту должность, отсутствует в текущем списке ответственных.").exec()
            return
        self.ui.cmb_responsible.setCurrentIndex(cmb_index)

    def change_nds(self):
        cmb_index: int = self.ui.cmb_nds.findData(NDS_VALUE[self.ui.cmb_category.currentData()])
        self.ui.cmb_nds.setCurrentIndex(cmb_index)

    def apply_payment_date(self):
        if not self.selector.doc_id or self.calculated_payment_date is None:
            return
        if self.selector.doc_id != self.contractdocument_id:
            ErrorInfoMessageBox("Этот договор не привязан к текущему платежу").exec()
            return
        trigger_date = self.ui.de_paymenttrigger.date()
        self.ui.de_duedate.setDate(self.calculated_payment_date)
        if self.ui.wdg_relative.isVisible():
            self.ui.de_incurrencedate.setDate(trigger_date)

    def bind_contract(self):
        if not self.selector.doc_id:
            return
        receiver = self._stripped(self.ui.le_receiver.text())
        contractor = self.ui.cmb_contractor.currentText().strip()
        if receiver and contractor and receiver.lower() != contractor.lower():
            msg = YesNoMessagebox(f"Получатель платежа «{receiver}» не совпадает с контрагентом «{contractor}». Привязать договор?")
            if msg.exec() == YesNoMessagebox.NO_RETURN_VALUE:
                return
        self.contractdocument_id = self.selector.doc_id
        self.show_bound_contract(self.selected_document_title())
        self.update_contract_buttons()

    def unbind_contract(self):
        self.contractdocument_id = 0
        self.show_bound_contract("")
        self.update_contract_buttons()

    def selected_document_title(self) -> str:
        document_name = self.ui.cmb_document.currentText()
        if len(document_name) > self.DOCUMENT_NAME_MAX_LEN:
            document_name = document_name[:self.DOCUMENT_NAME_MAX_LEN].rstrip() + "…"
        return f"{self.ui.cmb_contract.currentText()} ({document_name})"

    def show_bound_contract(self, title: str) -> None:
        self.ui.la_contract.setText(title or "не привязан")
        is_found = bool(self.contractdocument_id) and self.selector.doc_id == self.contractdocument_id
        self.ui.la_contract.setToolTip(f"{self.ui.cmb_contract.currentText()} ({self.ui.cmb_document.currentText()})" if is_found else "")
        self.ui.la_contract.setEnabled(bool(title))
        self.ui.tb_unbindcontract.setEnabled(bool(title))

    def update_contract_buttons(self) -> None:
        doc_id = self.selector.doc_id
        is_bound = bool(doc_id) and doc_id == self.contractdocument_id
        self.ui.pb_bindcontract.setEnabled(bool(doc_id) and not is_bound)
        self.ui.pb_bindcontract.setText("Платеж привязан к этому документу" if is_bound else "Привязать платеж к документу")
        self.ui.pb_applypaymentdate.setEnabled(is_bound and self.calculated_payment_date is not None)
        self.ui.pb_fillwithvalues.setEnabled(bool(doc_id))
        self.ui.pb_savevalues.setEnabled(bool(doc_id))

    def set_subcategory_visible(self, visible: bool) -> None:
        self.ui.formLayout.setRowVisible(self.ui.cmb_subcategory, visible)

    def save_contract_values(self):
        doc_id = self.selector.doc_id
        if not doc_id:
            return
        contract_values = SavedContractValues(
            doc_id,
            self._stripped(self.ui.le_receiver.text()),
            self.ui.cmb_category.currentData(),
            self.ui.cmb_subcategory.currentData() if self.ui.cmb_category.currentData() == LiabilityCategory.TOP_FINANCES else 0,
            self._stripped(self.ui.te_name.toPlainText()),
            self.ui.cmb_nds.currentData(),
            self.button_group.checkedId(),
            self._stripped(self.ui.te_descr.toPlainText()),
            self.ui.cmb_responsible.currentData(),
            int(self.ui.chb_hidden.isChecked()))
        if self.dbh.save_contractdocumentvalues(contract_values):
            ErrorInfoMessageBox("Данные успешно сохранены", is_info=True).exec()
        else:
            ErrorInfoMessageBox("Ошибка при попытке сохранения данных (подробнее см. лог)").exec()

    def fill_with_contract_values(self):
        doc_id = self.selector.doc_id
        if not doc_id:
            return
        contract_values = self.dbh.load_contractdocumentvalues(doc_id)
        if contract_values is None:
            ErrorInfoMessageBox("Для этого договора ранее не сохранялись значения").exec()
            return

        self.ui.le_receiver.setText(contract_values.receiver)
        self.ui.te_name.setPlainText(contract_values.name)
        self.resort_responsible_cmb(contract_values.category, auto_choice=False)
        cmb_index: int = self.ui.cmb_category.findData(contract_values.category)
        self.ui.cmb_category.setCurrentIndex(cmb_index)
        cmb_index: int = self.ui.cmb_subcategory.findData(contract_values.subcategory)
        self.ui.cmb_subcategory.setCurrentIndex(cmb_index)
        if contract_values.paymenttype:
            self.button_group.button(contract_values.paymenttype).setChecked(True)
        else:
            self.button_group.button(PaymentType.NORMAL).setChecked(True)
        cmb_index: int = self.ui.cmb_nds.findData(contract_values.nds)
        self.ui.cmb_nds.setCurrentIndex(cmb_index)
        cmb_index: int = self.ui.cmb_responsible.findData(contract_values.responsible)
        self.ui.cmb_responsible.setCurrentIndex(cmb_index)
        self.ui.chb_hidden.setChecked(bool(contract_values.hidden))
        self.ui.te_descr.setPlainText(contract_values.descr)
        self.set_subcategory_visible(self.ui.cmb_category.currentData() == LiabilityCategory.TOP_FINANCES)

    def on_document_changed(self, new_document_id: int | None) -> None:
        data = self.dbh.load_document_data(new_document_id) if new_document_id else None
        self._doc_terms = data

        self.ui.wdg_contractterms.setVisible(data is not None)
        if data is None:
            self.ui.te_paytermsdescr.clear()
            self.recalc_payment_date()
            return

        self.ui.te_paytermsdescr.setPlainText(data.description or "")
        self.ui.wdg_relative.setVisible(self._has_relative_part(data))
        self.ui.wdg_fixedmonth.setVisible(self._has_fixed_month_part(data))
        self.recalc_payment_date()

    def recalc_payment_date(self, *_) -> None:
        result = None
        if self._doc_terms is not None:
            result = calculate_payment_date(
                self.dbh,
                self._doc_terms,
                self.ui.de_paymenttrigger.date(),
                self.ui.spb_paymentperiodyear.value(),
                self.ui.cmb_paymentperiodmonth.currentData(),
            )

        if result is None or not result.isValid():
            self.calculated_payment_date = None
            self.ui.la_calculatedpaymentdate.setText("—")
        else:
            self.calculated_payment_date = result
            self.ui.la_calculatedpaymentdate.setText(f"{result.toString('dd.MM.yyyy')} ({WEEKDAY_ABBR[result.dayOfWeek()]})")
        self.update_contract_buttons()

    @staticmethod
    def _has_relative_part(data) -> bool:
        return data.payment_type == PaymentDueType.RELATIVE

    @staticmethod
    def _has_fixed_month_part(data) -> bool:
        if data.payment_type == PaymentDueType.FIXED:
            return True
        return data.payment_type == PaymentDueType.RELATIVE and bool(data.has_calendar_condition)

    def change_sidepanel_visibility(self, visible: bool, by_user: bool = False) -> None:
        self.ui.wdg_contract.show() if visible else self.ui.wdg_contract.hide()
        self.adjustSize()
        self.ui.pb_toggle.setIcon(QIcon(":/designer/icons/left.svg" if visible else ":/designer/icons/right.svg"))
        self.sidepanel_visibility = visible
        if by_user:
            self.sh.settings.setValue("Eventdialog/sidepanel", int(self.sidepanel_visibility))

    def check_integrity(self) -> bool:
        text = ""
        focus_widget = None
        if self.ui.le_receiver.text().strip() == "":
            text, focus_widget = "Получатель платежа должен быть указан", self.ui.le_receiver
        elif self.ui.te_name.toPlainText().strip() == "":
            text, focus_widget = "Наименование платежа должно быть указано", self.ui.te_name
        elif self.ui.dsb_totalamount.value() == 0.0:
            text, focus_widget = "Сумма платежа не может быть равна нулю", self.ui.dsb_totalamount
        elif self.non_editable_values["paidamount"] > Decimal(str(self.ui.dsb_totalamount.value())):
            text, focus_widget = "Новая общая сумма платежа превышает сумму уже сделанных по нему оплат", self.ui.dsb_totalamount
        elif self.ui.de_incurrencedate.date() > self.ui.de_duedate.date():
            text, focus_widget = "Дата возникновения платежа не может быть больше даты оплаты", self.ui.de_incurrencedate
        elif self.ui.rb_typerefund.isChecked() and self.ui.de_duedate.date() > QDate.currentDate():
            text, focus_widget = "Дата возврата не может быть больше сегодняшней даты", self.ui.de_duedate
        elif self.ui.cmb_subcategory.isVisible() and self.ui.cmb_subcategory.currentData() == 0:
            text, focus_widget = "Подкатегория платежа не выбрана", self.ui.cmb_subcategory
        elif self.ui.cmb_responsible.currentData() == 0:
            text, focus_widget = "Ответственное лицо не назначено", self.ui.cmb_responsible
        if text:
            msg = ErrorInfoMessageBox(text, parent=self)
            msg.exec()
            focus_widget.setFocus()
            return False

        text = ""

        is_source_paid: bool = ((self.edit_mode or self.copy_mode) and
                                FilterFlags.PAID in self.index.siblingAtColumn(Col.FILTERFLAGS).data(LiabilitySqlTableModel.qtValueRole))
        if self.ui.de_duedate.date() < QDate.currentDate() and not self.ui.rb_typerefund.isChecked() and not is_source_paid:
            text += "Дата платежа меньше текущей даты. "
        if self.ui.te_descr.toPlainText().strip() == "":
            text += "Основание платежа не указано. "
        if text:
            txt = f"{text}Вы уверены, что хотите продолжить?"
            msg = YesNoMessagebox(txt)
            if msg.exec() == YesNoMessagebox.NO_RETURN_VALUE:
                return False
        return True

    def accept(self, /):
        if not self.check_integrity():
            return
        data: list = list()
        # receiver
        data.append(self._stripped(self.ui.le_receiver.text()))
        # ID
        if self.edit_mode:
            data.append(self.non_editable_values["id"])
        else:
            # Будет пропущено моделью
            data.append(0)
        # type
        data.append(int(RowType.LIABILITY))
        # contractdocument id
        data.append(self.contractdocument_id)
        # category
        data.append(self.ui.cmb_category.currentData())
        # subcategory
        data.append(self.ui.cmb_subcategory.currentData() if self.ui.cmb_category.currentData() == LiabilityCategory.TOP_FINANCES else 0)
        # name
        data.append(self._stripped(self.ui.te_name.toPlainText()))
        # remainamount
        if not self.ui.rb_typerefund.isChecked():
            total_amount = Decimal(str(self.ui.dsb_totalamount.value()))
            if not self.edit_mode:
                remain_amount: Decimal = total_amount
            else:
                remain_amount: Decimal = total_amount - self.non_editable_values["paidamount"]
        else:
            total_amount = -Decimal(str(self.ui.dsb_totalamount.value()))
            remain_amount: Decimal = Decimal(str("0.0"))
        data.append(str(remain_amount))
        # totalamount
        data.append(str(total_amount))
        # nds
        data.append(self.ui.cmb_nds.currentData())
        # duedate
        data.append(date_str(self.ui.de_duedate.date()))
        # createdate
        data.append(date_str(self.ui.de_incurrencedate.date()))
        # paymenttype
        data.append(self.button_group.checkedId())
        # descr
        data.append(self._stripped(self.ui.te_descr.toPlainText()))
        # responsible
        data.append(self.ui.cmb_responsible.currentData())
        # notes
        data.append(self._stripped(self.ui.te_notes.toPlainText()))
        # todayshare
        if not self.ui.rb_typerefund.isChecked():
            if not self.edit_mode:
                data.append("0.0")
                today_payments: bool = False
            else:
                data.append(str(self.non_editable_values["todayshare"]))
                today_payments: bool = (self.non_editable_values["todayshare"] != 0)
        else:
            data.append("0.0")
            today_payments: bool = False
        # lastpaymentdate
        if not self.ui.rb_typerefund.isChecked():
            if self.edit_mode:
                data.append(self.non_editable_values["lastpaymentdate"])
            else:
                data.append("")
        else:
            data.append(date_str(self.ui.de_duedate.date()))
        # filterflags
        original_model: LiabilitySqlTableModel = model_atlevel(-2, self.model)
        filter_flags: FilterFlags = calculate_filterflags(remain_amount, self.ui.de_duedate.date(), today_payments, original_model.current_date)
        data.append(int(filter_flags))
        # featured
        if not self.edit_mode:
            data.append(0)
        else:
            data.append(self.non_editable_values["featured"])
        # hidden
        data.append(int(self.ui.chb_hidden.isChecked()))
        # receivernocase
        data.append(self._stripped(self.ui.le_receiver.text()).lower())

        if not self.edit_mode:
            new_row = original_model.insert_row(data)
            if new_row is None:
                log.e(f"Не удалось вставить новую строку в таблицу event со следующими данными: {data}")
                return
            if self.ui.rb_typerefund.isChecked():
                original_model.submitAll()
                self.payment_model.append_row([original_model.index(new_row, Col.ID).data(LiabilitySqlTableModel.qtValueRole),
                                               date_str(self.ui.de_duedate.date()),
                                               str(total_amount),
                                               date_str(QDate.currentDate())])
            QDialog.accept(self)
        else:
            original_model.edit_row(map_to_source(-2, self.index).row(), data)
            QDialog.accept(self)
