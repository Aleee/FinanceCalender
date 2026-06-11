import lovely_logger as log

from PySide6.QtCore import QModelIndex, Qt, QDate
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QDialog, QButtonGroup, QCompleter
from decimal import Decimal

from base.date import date_str
from gui.eventsqlmodel import PaymentType, RowType, LiabilitySqlTableModel, Col, FilterFlags
from gui.common import model_atlevel, map_to_source
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.ui.eventdialog_ui import Ui_EventDialog
from base.liability import LiabilityCategory, LiabilityFinanceSubcategory, CATEGORY_NAMES, NDS_VALUE


class EventDialog(QDialog):

    NDS_COMBOBOX = [("нет", 0), ("10%", 10), ("20%", 20), ("25%", 25)]
    SUBCATEGORY_COMBOBOX = [("", 0), ("Погашение кредита", int(LiabilityFinanceSubcategory.LOAN)), ("Погашение лизинга", int(LiabilityFinanceSubcategory.LEASING)),
                            ("Погашение процентов", int(LiabilityFinanceSubcategory.INTEREST)), ("Погашение займов учредителям", int(LiabilityFinanceSubcategory.FOUNDERLOAN))]

    DESCR_COMPLETER_LIST = ["Акт сдачи-приемки оказанных услуг №", "ТТН №", "ТН №", "Договор №", "Приложение №", "Счет на оплату №",
                            "Договор аренды №", "Счет №", "Акт выполненных работ №", "Счет на оплату №", "Акт сдачи-приемки оказанных услуг №",
                            "Акт оказания услуг №", "Акт №", "Акт сдачи-приемки выполненных работ №", "Счет-акт оказанных услуг", "Реестр №",
                            "Счет-фактура №", "Договор финансового лизинга №", "Договор лизинга №", "Кредитный договор №", "Договор поставки №"]

    def __init__(self, final_proxy_model, responsible_model: QStandardItemModel, edit_mode: bool = False, copy_mode: bool = False, current_index: QModelIndex | None = None, parent=None):
        super(EventDialog, self).__init__(parent)
        self.ui = Ui_EventDialog()
        self.ui.setupUi(self)

        if not current_index or not current_index.isValid():
            self.reject()

        self.model = final_proxy_model
        self.responsible_model: QStandardItemModel = responsible_model
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
        for cat_id, cat_name in CATEGORY_NAMES.items():
            if cat_id % 1000 != 0:
                self.ui.cmb_category.addItem(cat_name, int(cat_id))
        for row in self.NDS_COMBOBOX:
            self.ui.cmb_nds.addItem(row[0], row[1])
        for row in self.SUBCATEGORY_COMBOBOX:
            self.ui.cmb_subcategory.addItem(row[0], row[1])
        self.ui.cmb_responsible.setModel(self.responsible_model)

        self.ui.cmb_category.currentIndexChanged.connect(lambda row_num: self.ui.wdg_subcategory.setVisible(
            self.ui.cmb_category.currentData() == LiabilityCategory.TOP_FINANCES))

        if self.edit_mode:
            self.setWindowTitle("Редактирование платежа")
            self.ui.pb_accept.setText("Применить")
            # Сохранение значений, которые не будут напрямую редактироваться
            self.non_editable_values["id"] = self.index.siblingAtColumn(Col.ID).data(LiabilitySqlTableModel.qtValueRole)
            self.non_editable_values["paidamount"] = (self.index.siblingAtColumn(Col.TOTALAMOUNT).data(LiabilitySqlTableModel.qtValueRole)
                                                      - self.index.siblingAtColumn(Col.REMAINAMOUNT).data(LiabilitySqlTableModel.qtValueRole))
            self.non_editable_values["createdate"] = self.index.siblingAtColumn(Col.CREATEDATE).data(LiabilitySqlTableModel.qtValueRole)
            self.non_editable_values["todayshare"] = self.index.siblingAtColumn(Col.TODAYSHARE).data(LiabilitySqlTableModel.qtValueRole)
            self.non_editable_values["lastpaymentdate"] = self.index.siblingAtColumn(Col.LASTPAYMENTDATE).data(LiabilitySqlTableModel.qtValueRole)
            self.non_editable_values["featured"] = self.index.siblingAtColumn(Col.FEATURED).data(LiabilitySqlTableModel.qtValueRole)

        if self.edit_mode or self.copy_mode:
            # Заполнить имеющимися значениями
            self.ui.le_receiver.setText(self.index.siblingAtColumn(Col.RECEIVER).data(LiabilitySqlTableModel.qtValueRole))
            self.ui.le_name.setText(self.index.siblingAtColumn(Col.NAME).data(LiabilitySqlTableModel.qtValueRole))
            self.ui.dsb_totalamount.setValue(self.index.siblingAtColumn(Col.TOTALAMOUNT).data(LiabilitySqlTableModel.qtValueRole))
            self.ui.de_duedate.setDate(self.index.siblingAtColumn(Col.DUEDATE).data(LiabilitySqlTableModel.qtValueRole))
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
            self.ui.wdg_subcategory.setVisible(self.ui.cmb_category.currentData() == LiabilityCategory.TOP_FINANCES)
            self.ui.dsb_totalamount.setFocus()
        else:
            self.ui.de_duedate.setDate(QDate.currentDate())
            self.ui.rb_typenormal.setChecked(True)
            self.ui.wdg_subcategory.setVisible(False)
            self.ui.le_receiver.setFocus()

        # Сигнал: изменение НДС при изменении категории
        self.ui.cmb_category.currentIndexChanged.connect(lambda row_num: self.change_nds(row_num))

    def set_completers(self):
        # through SQL?
        origin_model: LiabilitySqlTableModel = model_atlevel(-2, self.model)
        receiver_compl_list = []
        for row in range(origin_model.rowCount()):
            if origin_model.index(row, Col.TYPE).data(LiabilitySqlTableModel.qtValueRole) == RowType.LIABILITY:
                receiver_compl_list.append(str(origin_model.index(row, Col.RECEIVER).data(LiabilitySqlTableModel.qtValueRole)))
        receiver_compl = QCompleter(list(set(receiver_compl_list)))
        receiver_compl.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        receiver_compl.setFilterMode(Qt.MatchFlag.MatchContains)
        self.ui.le_receiver.setCompleter(receiver_compl)
        self.ui.te_descr.completions.setStringList(self.DESCR_COMPLETER_LIST)

    def change_nds(self, row: int):
        cmb_index: int = self.ui.cmb_nds.findData(NDS_VALUE[self.ui.cmb_category.currentData()])
        self.ui.cmb_nds.setCurrentIndex(cmb_index)

    def check_integrity(self) -> bool:
        text = ""
        if self.ui.le_name.text().strip() == "":
            text = "Наименование платежа должно быть указано"
        elif self.ui.le_receiver.text().strip() == "":
            text = "Получатель платежа должен быть указан"
        elif self.ui.dsb_totalamount.value() == 0.0:
            text = "Сумма платежа не может быть равна нулю"
        if self.non_editable_values["paidamount"] > Decimal(str(self.ui.dsb_totalamount.value())):
            text = "Новая общая сумма платежа превышает сумму уже сделанных по нему оплат"
        if self.ui.cmb_subcategory.isVisible() and self.ui.cmb_subcategory.currentData() == 0:
            text = "Подкатегория платежа не выбрана"
        if self.ui.cmb_responsible.currentData() == 0:
            text = "Ответственное лицо не назначено"
        if text:
            msg = ErrorInfoMessageBox(text, parent=self)
            msg.exec()
            return False

        text = ""
        if (self.ui.de_duedate.date() < QDate.currentDate() and self.index.isValid() and
                FilterFlags.PAID not in self.index.siblingAtColumn(Col.FILTERFLAGS).data(LiabilitySqlTableModel.qtValueRole)):
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
        data.append(self.ui.le_receiver.text())
        # ID
        if self.edit_mode:
            data.append(self.non_editable_values["id"])
        else:
            # Будет пропущено моделью
            data.append(0)
        # type
        data.append(int(RowType.LIABILITY))
        # category
        data.append(self.ui.cmb_category.currentData())
        # subcategory
        data.append(self.ui.cmb_subcategory.currentData() if self.ui.cmb_category.currentData() == LiabilityCategory.TOP_FINANCES else 0)
        # name
        data.append(self.ui.le_name.text())
        # remainamount
        total_amount = Decimal(str(self.ui.dsb_totalamount.value()))
        if not self.edit_mode:
            remain_amount: Decimal = total_amount
        else:
            remain_amount: Decimal = total_amount - self.non_editable_values["paidamount"]
        data.append(str(remain_amount))
        # totalamount
        data.append(str(total_amount))
        # nds
        data.append(self.ui.cmb_nds.currentData())
        # duedate
        data.append(date_str(self.ui.de_duedate.date()))
        # createdate
        if not self.edit_mode:
            # ВРЕМЕННОЕ
            # data.append(date_str(QDate.currentDate()))
            data.append(self.parent().date_edit.date())
        else:
            data.append(self.non_editable_values["createdate"])
        # paymenttype
        data.append(self.button_group.checkedId())
        # descr
        data.append(self.ui.te_descr.toPlainText())
        # responsible
        data.append(self.ui.cmb_responsible.currentData())
        # notes
        data.append(self.ui.te_notes.toPlainText())
        # todayshare
        if not self.edit_mode:
            data.append("0.0")
            today_payments: bool = False
        else:
            data.append(str(self.non_editable_values["todayshare"]))
            today_payments: bool = (self.non_editable_values["todayshare"] != 0)
        # lastpaymentdate
        if self.edit_mode:
            data.append(self.non_editable_values["lastpaymentdate"])
        else:
            data.append("")
        # filterflags
        original_model: LiabilitySqlTableModel = model_atlevel(-2, self.model)
        filter_flags: FilterFlags = original_model.calculate_filterflags(remain_amount, self.ui.de_duedate.date(), today_payments, original_model.current_date)
        data.append(int(filter_flags))
        # featured
        if not self.edit_mode:
            data.append(0)
        else:
            data.append(self.non_editable_values["featured"])
        # hidden
        data.append(int(self.ui.chb_hidden.isChecked()))
        # receivernocase
        data.append(str.lower(self.ui.le_receiver.text()))

        if not self.edit_mode:
            if original_model.insert_row(data) is None:
                log.c(f"Не удалось вставить новую строку в таблицу event со следующими данными: {data}")
                return
            QDialog.accept(self)
        else:
            original_model.edit_row(map_to_source(-2, self.index).row(), data)
            QDialog.accept(self)
