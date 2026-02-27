from decimal import Decimal

from PySide6.QtCore import QModelIndex, Qt, QDate
from PySide6.QtWidgets import QDialog, QButtonGroup, QCompleter

from base.event import EventField, PaymentType, RowType, term_filter_flags, TermRoleFlags, EventFinanceSubcategory, EventCategory
from gui.common import model_atlevel, map_to_source
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.eventmodel import EventTableModel
from gui.ui.eventdialog_ui import Ui_EventDialog


class EventDialog(QDialog):

    NDS_COMBOBOX = [("нет", 0), ("10%", 10), ("20%", 20), ("25%", 25)]
    SUBCATEGORY_COMBOBOX = [("", 0), ("Погашение кредита", int(EventFinanceSubcategory.LOAN)), ("Погашение лизинга", int(EventFinanceSubcategory.LEASING)),
                            ("Погашение процентов", int(EventFinanceSubcategory.INTEREST)), ("Погашение займов учредителям", int(EventFinanceSubcategory.FOUNDERLOAN))]

    DESCR_COMPLETER_LIST = ["Акт сдачи-приемки оказанных услуг №", "ТТН №", "ТН №", "Договор №", "Приложение №", "Счет на оплату №",
                            "Договор аренды №", "Счет №", "Акт выполненных работ №", "Счет на оплату №", "Акт сдачи-приемки оказанных услуг №",
                            "Акт оказания услуг №", "Акт №", "Акт сдачи-приемки выполненных работ №", "Счет-акт оказанных услуг", "Реестр №",
                            "Счет-фактура №", "Договор финансового лизинга №", "Договор лизинга №", "Кредитный договор №", "Договор поставки №"]

    def __init__(self, final_proxy_model, edit_mode: bool = False, copy_mode: bool = False, current_index: QModelIndex | None = None, parent=None):
        super(EventDialog, self).__init__(parent)
        self.ui = Ui_EventDialog()
        self.ui.setupUi(self)

        if not current_index or not current_index.isValid():
            self.reject()

        self.model = final_proxy_model
        self.edit_mode: bool = edit_mode
        self.copy_mode: bool = copy_mode
        self.non_editable_values: dict = {"id": 0, "paidamount": Decimal(0), "createdate": QDate(), "todayshare": Decimal(0)}

        self.index: QModelIndex = current_index

        self.button_group: QButtonGroup = QButtonGroup(self)
        self.button_group.addButton(self.ui.rb_typenormal, PaymentType.NORMAL)
        self.button_group.addButton(self.ui.rb_typeadvance, PaymentType.ADVANCE)
        self.ui.pb_accept.clicked.connect(self.accept)
        self.ui.pb_cancel.clicked.connect(self.reject)

        self.set_completers()

        # Заполнение комбобоксов
        for cat_id, cat_name in EventTableModel.CATEGORY_NAMES.items():
            if cat_id % 1000 != 0:
                self.ui.cmb_category.addItem(cat_name, int(cat_id))
        for row in self.NDS_COMBOBOX:
            self.ui.cmb_nds.addItem(row[0], row[1])
        for row in self.SUBCATEGORY_COMBOBOX:
            self.ui.cmb_subcategory.addItem(row[0], row[1])

        self.ui.cmb_category.currentIndexChanged.connect(lambda row_num: self.ui.wdg_subcategory.setVisible(
            self.ui.cmb_category.currentData() == EventCategory.TOP_FINANCES))

        if self.edit_mode:
            self.setWindowTitle("Редактирование платежа")
            self.ui.pb_accept.setText("Применить")
            # Сохранение значений, которые не будут напрямую редактироваться
            self.non_editable_values["id"] = self.index.siblingAtColumn(EventField.ID).data(EventTableModel.internalValueRole)
            self.non_editable_values["paidamount"] = (self.index.siblingAtColumn(EventField.TOTALAMOUNT).data(EventTableModel.internalValueRole)
                                                      - self.index.siblingAtColumn(EventField.REMAINAMOUNT).data(EventTableModel.internalValueRole))
            self.non_editable_values["createdate"] = self.index.siblingAtColumn(EventField.CREATEDATE).data(EventTableModel.internalValueRole)
            self.non_editable_values["todayshare"] = self.index.siblingAtColumn(EventField.TODAYSHARE).data(EventTableModel.internalValueRole)
            self.non_editable_values["lastpaymentdate"] = self.index.siblingAtColumn(EventField.LASTPAYMENTDATE).data(EventTableModel.internalValueRole)

        if self.edit_mode or self.copy_mode:
            # Заполнить имеющимися значениями
            self.ui.le_receiver.setText(self.index.siblingAtColumn(EventField.RECEIVER).data(EventTableModel.internalValueRole))
            self.ui.le_name.setText(self.index.siblingAtColumn(EventField.NAME).data(EventTableModel.internalValueRole))
            self.ui.dsb_totalamount.setValue(self.index.siblingAtColumn(EventField.TOTALAMOUNT).data(EventTableModel.internalValueRole))
            self.ui.de_duedate.setDate(self.index.siblingAtColumn(EventField.DUEDATE).data(EventTableModel.internalValueRole))
            cmb_index: int = self.ui.cmb_category.findData(self.index.siblingAtColumn(EventField.CATEGORY).data(EventTableModel.internalValueRole))
            self.ui.cmb_category.setCurrentIndex(cmb_index)
            cmb_index: int = self.ui.cmb_subcategory.findData(self.index.siblingAtColumn(EventField.SUBCATEGORY).data(EventTableModel.internalValueRole))
            self.ui.cmb_subcategory.setCurrentIndex(cmb_index)
            if self.index.siblingAtColumn(EventField.PAYMENTTYPE).data(EventTableModel.internalValueRole):
                self.button_group.button(self.index.siblingAtColumn(EventField.PAYMENTTYPE).data(EventTableModel.internalValueRole)).setChecked(True)
            else:
                self.button_group.button(PaymentType.NORMAL).setChecked(True)
            cmb_index: int = self.ui.cmb_nds.findData(self.index.siblingAtColumn(EventField.NDS).data(EventTableModel.internalValueRole))
            self.ui.cmb_nds.setCurrentIndex(cmb_index)
            self.ui.le_responsible.setText(self.index.siblingAtColumn(EventField.RESPONSIBLE).data(EventTableModel.internalValueRole))
            self.ui.te_descr.setPlainText(self.index.siblingAtColumn(EventField.DESCR).data(EventTableModel.internalValueRole))
            self.ui.te_notes.setPlainText(self.index.siblingAtColumn(EventField.NOTES).data(EventTableModel.internalValueRole))
            self.ui.wdg_subcategory.setVisible(self.ui.cmb_category.currentData() == EventCategory.TOP_FINANCES)
            self.ui.dsb_totalamount.setFocus()
        else:
            self.ui.de_duedate.setDate(QDate.currentDate())
            self.ui.rb_typenormal.setChecked(True)
            self.ui.wdg_subcategory.setVisible(False)
            self.ui.le_receiver.setFocus()


        # Сигнал: изменение НДС при изменении категории
        self.ui.cmb_category.currentIndexChanged.connect(lambda row_num: self.change_nds(row_num))

    def set_completers(self):
        origin_model: EventTableModel = model_atlevel(-2, self.model)
        name_compl_list, receiver_compl_list, responsible_compl_list = [], [], []
        for row in range(origin_model.rowCount()):
            if origin_model.index(row, EventField.TYPE).data(EventTableModel.internalValueRole) == RowType.EVENT:
                name_compl_list.append(str(origin_model.index(row, EventField.NAME).data(EventTableModel.internalValueRole)))
                receiver_compl_list.append(str(origin_model.index(row, EventField.RECEIVER).data(EventTableModel.internalValueRole)))
                responsible_compl_list.append(str(origin_model.index(row, EventField.RESPONSIBLE).data(EventTableModel.internalValueRole)))
        name_compl = QCompleter(list(set(name_compl_list)))
        receiver_compl = QCompleter(list(set(receiver_compl_list)))
        responsible_compl = QCompleter(list(set(responsible_compl_list)))
        for compl in (name_compl, receiver_compl, responsible_compl):
            compl.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            compl.setFilterMode(Qt.MatchFlag.MatchContains)
        self.ui.le_name.setCompleter(name_compl)
        self.ui.le_receiver.setCompleter(receiver_compl)
        self.ui.le_responsible.setCompleter(responsible_compl)
        self.ui.te_descr.completions.setStringList(self.DESCR_COMPLETER_LIST)

    def change_nds(self, row: int):
        cmb_index: int = self.ui.cmb_nds.findData(model_atlevel(-2, self.model).NDS_VALUE[self.ui.cmb_category.currentData()])
        self.ui.cmb_nds.setCurrentIndex(cmb_index)

    def check_integrity(self) -> bool:
        text = ""
        if self.ui.le_name.text().strip() == "":
            text = "Наименование платежа должно быть указано"
        elif self.ui.le_receiver.text().strip() == "":
            text = "Получатель платежа должен быть указан"
        elif self.ui.dsb_totalamount.value() == 0.0:
            text = "Сумма платежа не может быть равна нулю"
        if self.non_editable_values["paidamount"] > Decimal(self.ui.dsb_totalamount.value()):
            text = "Новая общая сумма платежа превышает сумму уже сделанных по нему оплат"
        if self.ui.cmb_subcategory.isVisible() and self.ui.cmb_subcategory.currentData() == 0:
            text = "Подкатегория платежа не выбрана"
        if text:
            msg = ErrorInfoMessageBox(text, parent=self)
            msg.exec()
            return False

        text = ""
        if (self.ui.de_duedate.date() < QDate.currentDate() and self.index.isValid() and
                TermRoleFlags.DUE not in self.index.siblingAtColumn(EventField.TERMFLAGS).data(EventTableModel.internalValueRole)):
            text += "Дата платежа меньше текущей даты. "
        if self.ui.le_responsible.text().strip() == "":
            text += "Ответственное лицо не указано. "
        if self.ui.te_descr.toPlainText().strip() == "":
            text += "Основание платежа не указано. "
        if text:
            txt = f"{text}Вы уверены, что хотите продолжить?"
            msg = YesNoMessagebox(txt)
            if msg.exec() == YesNoMessagebox.NO_RETURN_VALUE:
                return False
        return True

    def accept(self, /):
        if self.check_integrity():
            data: list = list()
            data.append(self.ui.le_receiver.text())
            data.append(RowType.EVENT)
            # ID
            if self.edit_mode:
                data.append(self.non_editable_values["id"])
            else:
                data.append("<PLACEHOLDER>")
            data.append(self.ui.cmb_category.currentData())
            data.append(self.ui.cmb_subcategory.currentData() if self.ui.cmb_category.currentData() == EventCategory.TOP_FINANCES else 0)
            data.append(self.ui.le_name.text())
            total_amount = Decimal(str(self.ui.dsb_totalamount.value()))
            # Остаток задолженности
            if not self.edit_mode:
                remain_amount: Decimal = total_amount
            else:
                remain_amount: Decimal = total_amount - self.non_editable_values["paidamount"]
            data.append(remain_amount)
            data.append(total_amount)
            data.append(float(total_amount - remain_amount) / self.ui.dsb_totalamount.value())
            data.append(self.ui.de_duedate.date())
            data.append(self.button_group.checkedId())
            # Дата создания
            if not self.edit_mode:
                data.append(QDate.currentDate())
            else:
                data.append(self.non_editable_values["createdate"])
            data.append(self.ui.te_descr.toPlainText())
            data.append(self.ui.le_responsible.text())
            # Сегодняшние оплаты
            if not self.edit_mode:
                data.append(Decimal(0))
                today_payments: bool = False
            else:
                data.append(self.non_editable_values["todayshare"])
                today_payments: bool = (self.non_editable_values["todayshare"] != 0)
            data.append(term_filter_flags(remain_amount, self.ui.de_duedate.date(), today_payments))
            data.append(self.ui.te_notes.toPlainText())
            if self.edit_mode:
                data.append(self.non_editable_values["lastpaymentdate"])
            else:
                data.append(QDate())
            data.append(self.ui.cmb_nds.currentData())

            original_model: EventTableModel = model_atlevel(-2, self.model)

            if not self.edit_mode:
                original_model.append_row(data)
            else:
                original_model.edit_row(map_to_source(-2, self.index), data)

            QDialog.accept(self)
