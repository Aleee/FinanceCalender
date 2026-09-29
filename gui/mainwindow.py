from datetime import date
from decimal import Decimal
from enum import IntEnum, auto
from typing import Any
import time
import lovely_logger as log

from PySide6.QtCore import QModelIndex, Qt, QDate, QItemSelectionModel, QDateTime, QTimer
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtSql import QSqlTableModel, QSqlQuery
from PySide6.QtWidgets import QMainWindow, QDialog, QLabel, QWidget, QListView, QToolButton, QDateEdit

from base.backup import clean_backup_folder, save_backup
from base.chart import DebtChartWidget
from base.date import date_displstr, date_str
from base.dbhandler import DBHandler
from base.debtcalculator import DebtTimelineBuilder, DebtRepository
from base.formatting import dec_strcommaspace, str_rubstr
from base.payment import PaymentField
from base.xlswriter import LiabilityXlsWriter
from gui.chartchoicedialog import ChartChoiceDialog
from gui.common import map_to_source
from gui.commonwidgets.common import is_selection_filteredout, StatusBarSeparator
from gui.commonwidgets.eventfilter import RightClickFilter
from gui.commonwidgets.messagebox import YesNoMessagebox, ErrorInfoMessageBox
from gui.commonwidgets.persistentheader import PersistentHeader
from gui.contractordialog import ContractorDialog
from gui.eventdialog import EventDialog
from gui.eventproxymodel import LiabilitySortFilterProxyModel, Filter, LiabilityTotalsProxyModel
from gui.eventsqlmodel import LiabilitySqlTableModel, Col
from base.liability import FilterFlags, RowType, PaymentType
from gui.feedialog import FeeDialog
from gui.finplandialog import FinPlanDialog
from gui.fulfillmentoptiondialog import FulfillmentOptionDialog
from gui.matchingdialog import MatchingDialog
from gui.paymenthistorymodel import PaymentHistoryTableModel
from gui.paymenthistoryproxymodel import PaymentHistoryProxyModel
from gui.recoverydialog import RecoveryDialog
from gui.responsiblemodels import ResponsibleModel, ResponsibleCategorySortModel
from gui.settings import SettingsHandler
from gui.settingsdialog import SettingsDialog
from gui.ui.mainwindow_ui import Ui_MainWindow
from gui.ui.yearinputdialog_ui import Ui_YearInputDialog
from gui.filterwidget import TermCategory
from gui.exportdialog import ExportDialog


class BackupAutosaveStatus(IntEnum):
    SUCCESS = auto()
    ERROR = auto()
    NOCHANGE = auto()


class YearInputDialog(QDialog):
    def __init__(self, default_year: int, parent=None):
        super(YearInputDialog, self).__init__(parent)
        self.ui = Ui_YearInputDialog()
        self.ui.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background-color: #D5D6D8")
        self.ui.spinBox.setValue(default_year)
        self.ui.pushButton.clicked.connect(self.accept)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.settings_handler: SettingsHandler = SettingsHandler(self)
        self.db_handler: DBHandler = DBHandler(self.settings_handler)

        self.saved_before_exit: bool = False
        self.nosave_exit: bool = False

        # Загрузка данных из БД
        ## Проверка на наличие файла
        if not self.db_handler.check_db_files_exists():
            recover_dlg = RecoveryDialog(self.settings_handler, self.db_handler,
                                         text="К сожалению, найти файл базы данных в стандартном расположении не удалось. "
                                              "Выберите файл для восстановления",
                                         cancel_available=False, parent=self)
            recover_dlg.exec()
        ## Проверка файла
        if not self.db_handler.check_db_file_integrity():
            recover_dlg = RecoveryDialog(self.settings_handler, self.db_handler,
                                         text="К сожалению, при проверке файла базы данных обнаружены ошибки (подробности см. в логе). "
                                              "Выберите файл для восстановления",
                                         cancel_available=False, parent=self)
            recover_dlg.exec()

        self.db_handler.open_db_connection()

        self.base_model: LiabilitySqlTableModel = LiabilitySqlTableModel(self.db_handler, self)
        self.base_model.setTable("event")
        self.base_model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        self.base_model.select()

        self.proxy1_model = LiabilitySortFilterProxyModel()
        self.proxy1_model.setSourceModel(self.base_model)

        self.proxy2_model = LiabilityTotalsProxyModel()
        self.proxy2_model.setSourceModel(self.proxy1_model)

        self.ui.trw_event.setModel(self.proxy2_model)
        self.ui.trw_event.hide_columns()
        self.ui.trw_event.span_columns()

        self.payment_model: PaymentHistoryTableModel = PaymentHistoryTableModel(self)
        self.payment_model.setTable("payment")
        self.payment_model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.payment_model.select()

        self.payment_proxy_model = PaymentHistoryProxyModel()
        self.payment_proxy_model.setSourceModel(self.payment_model)

        self.responsible_partial_model: ResponsibleModel | None = None
        self.responsible_full_model: ResponsibleModel | None = None
        self.responsible_partial_sorted_model: ResponsibleCategorySortModel | None = None

        self.ui.tv_payment.setModel(self.payment_proxy_model)

        # Инициализация экспортера
        self.xls_writer: LiabilityXlsWriter = LiabilityXlsWriter(self.proxy2_model, self.ui.tv_payment, self.settings_handler)

        # Пересчет итоговых строк
        self.proxy1_model.layoutChanged.connect(self.proxy2_model.recalculate_totals)
        # Отображение и скрытие фильтров
        self.ui.spb_term.switch_status_changed.connect(lambda sw_status: self.ui.lw_term.setVisible(sw_status))
        self.ui.spb_category.switch_status_changed.connect(lambda sw_status: self.ui.lw_category.setVisible(sw_status))
        self.ui.spb_receiver.switch_status_changed.connect(lambda sw_status: self.ui.le_receiverfilter.setVisible(sw_status))
        self.ui.spb_responsible.switch_status_changed.connect(lambda sw_status: self.ui.cmb_responsiblefilter.setVisible(sw_status))

        # Подписи заголовков фильтров
        self.ui.spb_term.set_button_label("🡆 СРОК ПОГАШЕНИЯ", "🡇 СРОК ПОГАШЕНИЯ")
        self.ui.spb_category.set_button_label("🡆 КАТЕГОРИЯ", "🡇 КАТЕГОРИЯ")
        self.ui.spb_receiver.set_button_label("🡆 ПОЛУЧАТЕЛЬ", "🡇 ПОЛУЧАТЕЛЬ")
        self.ui.spb_responsible.set_button_label("🡆 ОТВЕТСТВЕННЫЙ", "🡇 ОТВЕТСТВЕННЫЙ")

        # Изменение цвета заголовков фильтров при скрытии активных фильтров
        self.ui.spb_term.switch_status_changed.connect(lambda sw_status:
                                                       self.ui.spb_term.change_style_on_hiding_activefilter(
                                                           sw_status, self.ui.lw_term.currentRow() != 0))
        self.ui.spb_category.switch_status_changed.connect(lambda sw_status:
                                                           self.ui.spb_category.change_style_on_hiding_activefilter(
                                                               sw_status, self.ui.lw_category.currentRow() != 0))
        self.ui.spb_receiver.switch_status_changed.connect(lambda sw_status:
                                                           self.ui.spb_receiver.change_style_on_hiding_activefilter(
                                                               sw_status, bool(self.ui.le_receiverfilter.text())))
        self.ui.spb_responsible.switch_status_changed.connect(lambda sw_status:
                                                              self.ui.spb_responsible.change_style_on_hiding_activefilter(
                                                                  sw_status, self.ui.cmb_responsiblefilter.currentData(Qt.ItemDataRole.UserRole) != 0))

        # Новые сигналы фильтров
        self.ui.lw_term.currentRowChanged.connect(self.update_filters_and_select)
        self.ui.lw_category.currentRowChanged.connect(self.update_filters_and_select)
        self.ui.le_receiverfilter.textChanged.connect(self.update_filters_and_select)
        self.ui.cmb_responsiblefilter.currentIndexChanged.connect(self.update_filters_and_select)
        self.ui.chb_paytoday.checkStateChanged.connect(self.update_filters_and_select)

        # Действия при переключении избранного
        self.ui.act_featured.triggered.connect(self.update_filters_and_select)
        self.ui.act_featured.triggered.connect(lambda: self.actions_on_selection_visibility_changed(True) if not self.current_data(Col.FEATURED) and self.ui.act_featured.isChecked() else None)
        self.ui.trw_event.filter_conditions_changed.connect(self.update_filters_and_select)
        self.ui.trw_event.filter_conditions_changed.connect(lambda: self.actions_on_selection_visibility_changed(True) if self.ui.act_featured.isChecked() else None)

        self.ui.lw_term.currentRowChanged.connect(lambda row: self.proxy1_model.set_filter(Filter.TERM, list(TermCategory)[row]))
        self.ui.lw_category.currentRowChanged.connect(lambda row: self.proxy1_model.set_filter(Filter.CATEGORY, row))
        self.ui.chb_paytoday.checkStateChanged.connect(lambda state: self.proxy1_model.set_filter(Filter.PAYTODAY, state))

        ## Действия после перезагрузки модели
        # Сохранение выделения
        self.base_model.beforeSelect.connect(self.ui.trw_event.save_selection)
        self.base_model.afterSelect.connect(self.ui.trw_event.restore_selection)
        # Расширение заголовочных строк
        self.base_model.afterSelect.connect(self.ui.trw_event.span_columns)
        ## Сигнал для обновления имен категорий
        self.base_model.filterwidget_labels_changed.connect(lambda term_labeldata, category_labeldata: self.ui.lw_term.update_labels(term_labeldata))
        self.base_model.filterwidget_labels_changed.connect(lambda term_labeldata, category_labeldata: self.ui.lw_category.update_labels(category_labeldata))

        # Обновление отображения при фильтрации/сортировке/изменении
        self.proxy1_model.layoutChanged.connect(self.check_event_selection_visibility)
        # События при смене выбранного ивента
        self.ui.trw_event.selectionModel().currentChanged.connect(self.on_currentevent_change)
        # Сигналы таблицы платежей
        self.ui.tv_payment.selectionModel().selectionChanged.connect(self.check_payment_selection_visibility)
        # Cигналы информационной панели
        self.ui.pb_addpayment.clicked.connect(self.make_new_payment)
        self.ui.pb_deletepayment.clicked.connect(self.delete_payment)
        self.ui.tb_savenote.clicked.connect(self.save_note)
        self.ui.te_notes.textChanged.connect(lambda: self.ui.tb_savenote.setEnabled(True))
        # Сигналы тулбара
        self.ui.act_new.triggered.connect(lambda: self.open_event_dialog())
        self.ui.act_copy.triggered.connect(lambda: self.open_event_dialog(copy=True))
        self.ui.act_edit.triggered.connect(lambda: self.open_event_dialog(edit=True))
        self.ui.act_delete.triggered.connect(self.delete_event)
        self.ui.act_finplan.triggered.connect(self.open_finplan_dialog)
        self.rmb_finplan_filter = RightClickFilter(self)
        self.rmb_finplan_filter.rightmousebutton_clicked.connect(lambda: self.open_finplan_dialog(ask_year=True))
        self.ui.tlbr.widgetForAction(self.ui.act_finplan).installEventFilter(self.rmb_finplan_filter)
        self.ui.act_fulfillment.triggered.connect(self.open_fulfillment_dialog)
        self.ui.act_chart.triggered.connect(self.open_chart_dialog)
        self.ui.act_fees.triggered.connect(self.open_fees_dialog)
        self.ui.act_matching.triggered.connect(self.open_matching_dialog)
        self.ui.act_export.triggered.connect(self.open_export_dialog)
        self.ui.act_contracts.triggered.connect(self.open_contractor_dialog)
        self.ui.act_settings.triggered.connect(lambda: self.open_settings_dialog(True))
        self.ui.act_toggleheaders.toggled.connect(lambda checked: self.proxy1_model.set_filter(Filter.HEADER, checked))
        self.ui.act_toggleheaders.toggled.connect(lambda checked: self.ui.trw_event.span_columns() if checked else None)
        self.ui.act_togglefooters.toggled.connect(lambda checked: self.proxy1_model.set_filter(Filter.FOOTER, checked))

        # Сигналы обновления кэша стилей
        # self.proxy1_model.modelInvalidated.connect(self.proxy2_model.refresh_style_cache)
        self.base_model.cacheUpdateNeeded.connect(self.proxy1_model.invalidate_style_cache)
        # Сигналы обновления кэша сортировки
        self.base_model.cacheUpdateNeeded.connect(self.base_model.invalidate_sort_cache)

        # Строка состояния
        self.la_sbar_backup = QLabel("")
        self.separator1 = StatusBarSeparator(self)
        self.separator2 = StatusBarSeparator(self)
        self.spacer = QWidget()
        self.spacer.setFixedWidth(10)
        self.ui.statusBar.addPermanentWidget(self.separator1)
        self.ui.statusBar.addPermanentWidget(self.la_sbar_backup)
        self.ui.statusBar.addPermanentWidget(self.separator2)
        self.ui.statusBar.addPermanentWidget(self.spacer)

        # Косметика
        self.ui.tv_payment.set_columns_visibility()
        self.ui.tlbr.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.ui.cmb_responsiblefilter.setView(QListView())  # переключение на натив (белая заливка на hover - баг?)
        # Постоянный вертикальный header
        self.ui.tv_payment.setVerticalHeader(PersistentHeader(Qt.Orientation.Vertical, self.ui.tv_payment))
        # Кнопка очистки комбобокса поиска по ответственному
        self.ui.cmb_responsiblefilter.setEditable(True)
        self.ui.cmb_responsiblefilter.lineEdit().setReadOnly(True)
        self.ui.cmb_responsiblefilter.lineEdit().setClearButtonEnabled(True)
        clear_button = self.ui.cmb_responsiblefilter.lineEdit().findChild(QToolButton)
        if clear_button:
            clear_button.setEnabled(True)
        self.ui.cmb_responsiblefilter.lineEdit().textChanged.connect(lambda text: self.ui.cmb_responsiblefilter.setCurrentIndex(0) if text == "" else None)

        # Резервное копирование
        self.make_backup()

        # Начальные действия
        self.settings_handler.apply_settings()
        self.ui.stw_eventinfo.setCurrentIndex(1)


    def make_backup(self):
        # Очистка папки с резервными копиями
        result: bool = clean_backup_folder(self.settings_handler)
        if not result:
            error_msg = ErrorInfoMessageBox("Не удалось очистить папку с резервными копиями (см. подробности в логе)")
            error_msg.exec()
        result: QDateTime = save_backup(self.settings_handler, self.db_handler)
        if result.isValid():
            self.la_sbar_backup.setText(f"Резервная копия: {date_displstr(result)}")
        else:
            self.la_sbar_backup.setText("Резервная копия: ОШИБКА СОЗДАНИЯ")


    def update_filters_and_select(self):
        self.base_model.set_filters(self.ui.lw_term.current_term(),
                                    self.ui.lw_category.current_category(),
                                    self.ui.le_receiverfilter.text().replace("'", "''"),
                                    self.ui.cmb_responsiblefilter.currentData(),
                                    self.ui.chb_paytoday.isChecked(),
                                    int(self.settings_handler.settings.value("Common/paidloadperiod", 3)),
                                    self.ui.act_featured.isChecked())
        self.proxy2_model.recalculate_totals()

    def update_labels(self):
        self.base_model.update_labels(self.ui.lw_term.current_term(),
                                    self.ui.lw_category.current_category(),
                                    self.ui.le_receiverfilter.text().replace("'", "''"),
                                    self.ui.cmb_responsiblefilter.currentData(),
                                    self.ui.chb_paytoday.isChecked(),
                                    int(self.settings_handler.settings.value("Common/paidloadperiod", 3)),
                                    self.ui.act_featured.isChecked())

    def get_current_event_index(self, source_model_index: bool = False) -> QModelIndex:
        if source_model_index:
            return map_to_source(-2, self.ui.trw_event.selectionModel().currentIndex())
        else:
            return self.ui.trw_event.selectionModel().currentIndex()
        
    def current_data(self, column, role=LiabilitySqlTableModel.dbValueRole) -> Any:
        curr_index: QModelIndex = self.get_current_event_index()
        if not curr_index.isValid():
            return None
        return curr_index.siblingAtColumn(column).data(role)

    def check_event_selection_visibility(self) -> None:
        filtered_out = not bool(self.ui.trw_event.currentIndex().isValid())
        self.actions_on_selection_visibility_changed(filtered_out)

    def actions_on_selection_visibility_changed(self, filtered_out: bool) -> None:
        self.ui.act_copy.setDisabled(filtered_out)
        self.ui.act_edit.setDisabled(filtered_out)
        self.ui.act_delete.setDisabled(filtered_out)
        if filtered_out or self.current_data(Col.TYPE) != RowType.LIABILITY:
            self.ui.stw_eventinfo.setCurrentIndex(1)

    def check_payment_selection_visibility(self) -> None:
        if self.current_data(Col.PAYMENTTYPE) == PaymentType.REFUND:
            self.ui.pb_deletepayment.setDisabled(True)
        else:
            QTimer.singleShot(0, self.check_payment_selection_visibility_delayed)

    def check_payment_selection_visibility_delayed(self):
        filtered_out = not bool(self.ui.tv_payment.currentIndex().isValid())
        self.ui.pb_deletepayment.setDisabled(filtered_out)

    def on_currentevent_change(self) -> None:
        row_type: RowType = self.current_data(Col.TYPE)
        payment_type: PaymentType = self.current_data(Col.PAYMENTTYPE)
        # Активировать/деактивировать кнопку удаления платежа и
        self.check_payment_selection_visibility()
        # Отобразить только оплаты, относящиеся к текущему платежу
        self.payment_model.update_filter(self.current_data(Col.ID, LiabilitySqlTableModel.qtValueRole))
        self.check_event_selection_visibility()
        if row_type != RowType.LIABILITY:
            for act in (self.ui.act_copy, self.ui.act_edit, self.ui.act_delete):
                act.setEnabled(False)
        if payment_type == PaymentType.REFUND:
            self.ui.act_edit.setEnabled(False)
            self.ui.pb_addpayment.setEnabled(False)
            self.ui.pb_deletepayment.setEnabled(False)
        else:
            self.ui.pb_addpayment.setEnabled(True)
        self.update_eventinfo()
        self.ui.tb_savenote.setEnabled(False)

    def update_eventinfo(self) -> bool:
        current_index: QModelIndex = self.get_current_event_index()
        if not current_index.isValid():
            self.ui.stw_eventinfo.setCurrentIndex(1)
            return False
        row_type: int = current_index.siblingAtColumn(Col.TYPE).data(LiabilitySqlTableModel.dbValueRole)
        is_event_selected: bool = (row_type == RowType.LIABILITY)
        # Информационная часть отображается только для платежей
        self.ui.stw_eventinfo.setCurrentIndex(int(not is_event_selected))
        # Значения для информационной части
        if row_type == RowType.LIABILITY:
            self.ui.la_remainsum.setText(str_rubstr(current_index.siblingAtColumn(Col.REMAINAMOUNT).data()))
            self.ui.la_totalsum.setText(str_rubstr(current_index.siblingAtColumn(Col.TOTALAMOUNT).data()))
            percentage: str = ((current_index.siblingAtColumn(Col.TOTALAMOUNT).data(LiabilitySqlTableModel.qtValueRole) -
                               current_index.siblingAtColumn(Col.REMAINAMOUNT).data(LiabilitySqlTableModel.qtValueRole)) /
                               current_index.siblingAtColumn(Col.TOTALAMOUNT).data(LiabilitySqlTableModel.qtValueRole))
            self.ui.la_percentage.setText(f"{percentage:.1%}")
            self.ui.la_createdate.setText(str(current_index.siblingAtColumn(Col.INCURRENCEDATE).data()))
            self.ui.la_paymenttype.setText(str(current_index.siblingAtColumn(Col.PAYMENTTYPE).data()).lower())
            self.ui.la_responsible.setText(str(current_index.siblingAtColumn(Col.RESPONSIBLE).data()))
            self.ui.te_descr.setPlainText(str(current_index.siblingAtColumn(Col.DESCR).data()))
            self.ui.te_notes.setPlainText(str(current_index.siblingAtColumn(Col.NOTES).data()))
            # Сумма платежа по умолчанию равна остатку
            self.ui.dsb_paymentsum.setValue(current_index.siblingAtColumn(Col.REMAINAMOUNT).data(LiabilitySqlTableModel.qtValueRole))
            # Обновить дату платежа по умолчанию
            self.ui.de_paymentdate.setDate(QDate.currentDate())
        return True

    def set_data_to_current_event(self, column, value) -> bool:
        curr_index_source: QModelIndex = self.get_current_event_index(source_model_index=True)
        if not curr_index_source.isValid():
            return False
        return self.base_model.setData(curr_index_source.siblingAtColumn(column), value)

    def save_note(self) -> bool:
        self.ui.tb_savenote.setEnabled(False)
        return self.set_data_to_current_event(Col.NOTES, self.ui.te_notes.toPlainText())

    def make_new_payment(self) -> bool:
        date: QDate = self.ui.de_paymentdate.date()
        amount: Decimal = Decimal(str(self.ui.dsb_paymentsum.value()))

        if amount == 0:
            return False
        if (amount - self.current_data(Col.REMAINAMOUNT, LiabilitySqlTableModel.qtValueRole)) > 0.01:
            msg_box = YesNoMessagebox(f"Сумма оплаты ({dec_strcommaspace(amount)}) превышает остаток задолженности ({dec_strcommaspace(
                self.current_data(Col.REMAINAMOUNT))}). Уверены, что хотите продолжить?")
            if msg_box.exec() == YesNoMessagebox.NO_RETURN_VALUE:
                return False
        if date > QDate.currentDate():
            msg_box = YesNoMessagebox(f"Выбранная дата ({date_displstr(date)}) больше текущей даты. Уверены, что хотите продолжить?")
            if msg_box.exec() == YesNoMessagebox.NO_RETURN_VALUE:
                return False
        if self.payment_model.append_row([self.current_data(Col.ID),
                                         date_str(date),
                                         str(amount),
                                         date_str(QDate.currentDate())]):
            last_payment_date: QDate = self.payment_proxy_model.get_last_paymentdate(date)
            self.base_model.recalculate_values_on_newpayment(self.get_current_event_index(source_model_index=True), amount, date, last_payment_date)
            self.proxy2_model.recalculate_totals()
            self.update_filters_and_select()
            self.update_eventinfo()
            return True
        else:
            return False

    def delete_payment(self) -> bool:
        current_index: QModelIndex = self.payment_proxy_model.mapToSource(self.ui.tv_payment.selectionModel().currentIndex())
        amount: Decimal = current_index.siblingAtColumn(PaymentField.SUM).data(PaymentHistoryTableModel.qtValueRole)
        date: QDate = current_index.siblingAtColumn(PaymentField.PAYMENT_DATE).data(PaymentHistoryTableModel.qtValueRole)
        origin_index_row: int = current_index.row()

        if is_selection_filteredout(self.payment_proxy_model, self.ui.tv_payment):
            return False
        msg_box = YesNoMessagebox(f"Вы уверены, что хотите удалить запись об оплате?")
        if msg_box.exec() == YesNoMessagebox.NO_RETURN_VALUE:
            return False

        if self.payment_model.removeRow(origin_index_row):
            self.payment_model.submitAll()
            last_payment_date: QDate = self.payment_proxy_model.get_last_paymentdate(date)
            self.base_model.recalculate_values_on_paymentdelete(self.get_current_event_index(source_model_index=True), amount, date, last_payment_date)
            self.proxy2_model.recalculate_totals()
            self.update_filters_and_select()
            self.update_eventinfo()
            return True
        else:
            return False

    def open_settings_dialog(self, reject_possible: bool = True):
        settings_dialog: SettingsDialog = SettingsDialog(self.settings_handler, self.db_handler, reject_possible, self)
        settings_dialog.exec()
        self.on_currentevent_change()
        self.update_filters_and_select()
        self.base_model.cacheUpdateNeeded.emit()

    def open_fees_dialog(self):
        fees_dialog: FeeDialog = FeeDialog(self.settings_handler, self.db_handler, self.base_model, self.payment_model, self)
        fees_dialog.exec()
        self.update_filters_and_select()

    def open_matching_dialog(self):
        matching_dialog: MatchingDialog = MatchingDialog(self.settings_handler, self.db_handler, self)
        matching_dialog.exec()
        self.update_filters_and_select()

    def open_event_dialog(self, edit: bool = False, copy: bool = False):
        curr_index: QModelIndex = self.get_current_event_index()

        if edit or copy:
            if not curr_index.isValid():
                return False
            selection_not_visible: bool = is_selection_filteredout(self.proxy2_model, self.ui.trw_event, two_proxies=True, current_instead=True)
            if selection_not_visible:
                return False

            is_current_paid = True if FilterFlags.PAID in curr_index.siblingAtColumn(Col.FILTERFLAGS).data(LiabilitySqlTableModel.qtValueRole) else False

        responsible_model: ResponsibleCategorySortModel = self.responsible_partial_sorted_model
        if edit or copy:
            responsible_id = self.current_data(Col.RESPONSIBLE, LiabilitySqlTableModel.qtValueRole)
            matches = self.responsible_partial_model.match(self.responsible_partial_model.index(0, 0), Qt.ItemDataRole.UserRole,
                                                           responsible_id, hits=1, flags=Qt.MatchFlag.MatchExactly)
            if not matches:
                responsible_model = self.responsible_full_sorted_model
        if not responsible_model:
            return False

        event_dialog: EventDialog = EventDialog(final_proxy_model=self.proxy2_model, responsible_model=responsible_model, payment_model= self.payment_model,
                                                db_handler=self.db_handler, edit_mode=edit, copy_mode=copy, current_index=curr_index, parent=self)
        if event_dialog.exec():
            if not edit:
                set_due_filter = False
                if copy:
                    if is_current_paid:
                        set_due_filter = True
                self.base_model.submitAll()
                self.ui.trw_event.selectionModel().clear()
                if set_due_filter:
                    # автоматически запустит self.update_filters_and_select()
                    self.ui.lw_term.setCurrentRow(0)
                else:
                    self.update_filters_and_select()
                # ищем и выделяем новую строку
                query = QSqlQuery()
                query.exec("SELECT last_insert_rowid()")
                if query.next():
                    last_id = query.value(0)
                else:
                    last_id = 0

                base_index_to_select = None
                for row in range(self.base_model.rowCount() - 1, -1, -1):
                    if self.base_model.record(row).value("id") == last_id:
                        base_index_to_select = self.base_model.index(row, 0)
                if base_index_to_select:
                    index_to_select: QModelIndex = self.proxy2_model.mapFromSource(self.proxy1_model.mapFromSource(base_index_to_select))
                    if index_to_select.isValid():
                        self.ui.trw_event.skip_restore_selection = True
                        self.ui.trw_event.selectionModel().setCurrentIndex(index_to_select, QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows)
            else:
                self.proxy2_model.recalculate_totals()
            self.proxy1_model.invalidate()
            return True
        else:
            return False

    def open_export_dialog(self) -> bool:
        if self.proxy2_model.rowCount() == 0:
            return False
        dlg: ExportDialog = ExportDialog(self.xls_writer, self.ui.trw_event.get_columnvisibility_list(), self)
        return dlg.exec() == QDialog.DialogCode.Accepted

    def open_finplan_dialog(self, ask_year: bool = False):
        current_year: int = QDate().currentDate().year()
        if ask_year:
            tdlg: YearInputDialog = YearInputDialog(current_year, self)
            tdlg.exec()
        dlg: FinPlanDialog = FinPlanDialog(self.db_handler, self.settings_handler, tdlg.ui.spinBox.value() if ask_year else current_year, self)
        dlg.exec()

    def open_fulfillment_dialog(self):
        dlg: FulfillmentOptionDialog = FulfillmentOptionDialog(self.db_handler, self.settings_handler, self)
        dlg.exec()

    def delete_event(self) -> bool:
        curr_index: QModelIndex = self.get_current_event_index()
        if not curr_index.isValid():
            return False
        selection_not_visible: bool = is_selection_filteredout(self.proxy2_model, self.ui.trw_event, two_proxies=True, current_instead=True)
        if selection_not_visible:
            return False
        msg_box = YesNoMessagebox("Удаление платежа - необратимое действие. Уверены, что хотите продолжить?")
        if msg_box.exec() == YesNoMessagebox.YES_RETURN_VALUE:
            deleted_event_id: int = self.base_model.delete_row(self.proxy1_model.mapToSource(self.proxy2_model.mapToSource(curr_index)).row())
            if deleted_event_id == 0:
                return False
            # Удаление строки не вызывает currentChanged
            self.on_currentevent_change()
            self.payment_model.delete_rows_byeventid(deleted_event_id)
            self.update_filters_and_select()
            return True
        return False

    def open_chart_dialog(self):
        self.chart_choice_dialog = ChartChoiceDialog()
        self.chart_choice_dialog.exec()

    def open_contractor_dialog(self):
        self.contractor_dialog = ContractorDialog(self.db_handler, self)
        self.contractor_dialog.exec()

    def update_responsible_models(self, update_widgets: bool) -> bool:
        personal_data = self.db_handler.load_personal_data(as_dict=True)
        if not (personal_data and self.base_model):
            log.w("Не удалось обновить модели ответственных: данные персонала недоступны")
            return False

        self.base_model.personal_dict = personal_data[0]
        self.personal_frequency_bycategory_dict = personal_data[1]

        self.responsible_partial_model = ResponsibleModel(only_active_personal=True)
        self.responsible_partial_model.setup_model(self.base_model.personal_dict)
        self.responsible_full_model = ResponsibleModel(only_active_personal=False)
        self.responsible_full_model.setup_model(self.base_model.personal_dict)

        self.responsible_partial_sorted_model: ResponsibleCategorySortModel = ResponsibleCategorySortModel(
            self.personal_frequency_bycategory_dict)
        self.responsible_partial_sorted_model.setSourceModel(self.responsible_partial_model)
        self.responsible_full_sorted_model: ResponsibleCategorySortModel = ResponsibleCategorySortModel(
            self.personal_frequency_bycategory_dict)
        self.responsible_full_sorted_model.setSourceModel(self.responsible_full_model)
        self.responsible_full_sorted_model.sort(0, Qt.SortOrder.AscendingOrder)
        self.responsible_partial_sorted_model.sort(0, Qt.SortOrder.AscendingOrder)

        if update_widgets:
            self.responsible_full_model.sort(0)
            self.ui.cmb_responsiblefilter.setModel(self.responsible_full_model)

        return True

    def closeEvent(self, event, /):
        self.settings_handler.save_settings()
        event.accept()
