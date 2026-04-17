import os
import shutil
import sqlite3
import traceback

import lovely_logger as log
from decimal import Decimal
from enum import IntEnum, auto
from pathlib import Path
from typing import Any

from PySide6.QtCore import QModelIndex, Qt, QDate, QItemSelectionModel, QTime, QDateTime, QTimer, QCoreApplication
from PySide6.QtSql import QSqlDatabase, QSqlTableModel
from PySide6.QtWidgets import QMainWindow, QDialog, QVBoxLayout, QApplication, QLabel, QSizePolicy, QWidget

from base.date import date_displstr, date_str
from base.dbhandler import DBHandler
from base.formatting import dec_strcommaspace, str_rubstr
from base.payment import PaymentField
from base.xlswriter import XlsWriter
from gui.common import map_to_source, model_atlevel
from gui.commonwidgets.common import is_selection_filteredout
from gui.commonwidgets.eventfilter import RightClickFilter
from gui.commonwidgets.messagebox import YesNoMessagebox, ErrorInfoMessageBox
from gui.commonwidgets.persistentheader import PersistentHeader
from gui.eventdialog import EventDialog
from gui.eventproxymodel import LiabilitySortFilterProxyModel, Filter, LiabilityTotalsProxyModel
from gui.eventsqlmodel import LiabilitySqlTableModel, RowType, Col
from gui.finplandialog import FinPlanDialog
from gui.fulfillmentdialog import FulfillmentDialog
from gui.fulfillmentoptiondialog import FulfillmentOptionDialog
from gui.plot import PaymentHistoryGraph
from gui.paymenthistorymodel import PaymentHistoryTableModel
from gui.paymenthistoryproxymodel import PaymentHistoryProxyModel
from gui.recoverydialog import RecoveryDialog
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

        self.plot_available: bool = False

        # Загрузка данных из БД
        ## Проверка на наличие файла
        if not self.db_handler.check_if_db_files_exists():
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

        self.base_model: LiabilitySqlTableModel = LiabilitySqlTableModel(self)
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

        self.ui.tv_payment.setModel(self.payment_proxy_model)

        # # Инициализация экспортера
        # self.xls_writer: XlsWriter = XlsWriter(self.event_finalfilter_model, self.ui.tv_payment, self.settings_handler)
        # # Сохранение текста заметок
        # self.ui.te_notes.textChanged.connect(self.save_notes)

        # # График оплат
        # self.payment_plot: PaymentHistoryGraph = PaymentHistoryGraph()
        # self.ui.wdg_graph.setLayout(QVBoxLayout())
        # self.ui.wdg_graph.layout().addWidget(self.payment_plot.canvas)

        # Пересчет итоговых строк
        self.proxy1_model.layoutChanged.connect(self.proxy2_model.recalculate_totals)
        # Отображение и скрытие фильтров
        self.ui.spb_term.switch_status_changed.connect(lambda sw_status: self.ui.lw_term.setVisible(sw_status))
        self.ui.spb_category.switch_status_changed.connect(lambda sw_status: self.ui.lw_category.setVisible(sw_status))
        self.ui.spb_receiver.switch_status_changed.connect(lambda sw_status: self.ui.le_receiverfilter.setVisible(sw_status))
        self.ui.spb_responsible.switch_status_changed.connect(lambda sw_status: self.ui.le_responsiblefilter.setVisible(sw_status))

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
                                                                  sw_status, bool(self.ui.le_responsiblefilter.text())))

        # Новые сигналы фильтров
        self.ui.lw_term.currentRowChanged.connect(self.update_filters_and_select)
        self.ui.lw_category.currentRowChanged.connect(self.update_filters_and_select)
        self.ui.le_receiverfilter.textChanged.connect(self.update_filters_and_select)
        self.ui.le_responsiblefilter.textChanged.connect(self.update_filters_and_select)
        self.ui.chb_paytoday.checkStateChanged.connect(self.update_filters_and_select)
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

        # ## Обновление отображения при фильтрации/сортировке/изменении
        # self.event_proxy_model.layoutChanged.connect(self.ui.trw_event.regain_state_after_model_changes)
        self.proxy1_model.layoutChanged.connect(self.check_event_selection_visibility)
        # События при смене выбранного ивента
        self.ui.trw_event.selectionModel().currentChanged.connect(self.on_currentevent_change)
        # Новая выборка из базы должна запускать те же проверки (не уверен)
        # self.base_model.afterSelect.connect(self.on_currentevent_change)
        # Сигналы таблицы платежей
        self.ui.tv_payment.selectionModel().selectionChanged.connect(self.check_payment_selection_visibility)
        # # Cигналы информационной панели
        self.ui.pb_addpayment.clicked.connect(self.make_new_payment)
        self.ui.pb_deletepayment.clicked.connect(self.delete_payment)
        # Сигналы тулбара
        self.ui.act_new.triggered.connect(lambda: self.open_event_dialog())
        self.ui.act_copy.triggered.connect(lambda: self.open_event_dialog(copy=True))
        self.ui.act_edit.triggered.connect(lambda: self.open_event_dialog(edit=True))
        self.ui.act_delete.triggered.connect(self.delete_event)
        # self.ui.act_finplan.triggered.connect(self.open_finplan_dialog)
        # self.rmb_finplan_filter = RightClickFilter(self)
        # self.rmb_finplan_filter.rightmousebutton_clicked.connect(lambda: self.open_finplan_dialog(ask_year=True))
        # self.ui.tlbr.widgetForAction(self.ui.act_finplan).installEventFilter(self.rmb_finplan_filter)
        # self.ui.act_fulfillment.triggered.connect(self.open_fulfillment_dialog)
        # self.ui.act_export.triggered.connect(self.open_export_dialog)
        self.ui.act_settings.triggered.connect(lambda: self.open_settings_dialog(True))
        self.ui.act_toggleheaders.toggled.connect(lambda checked: self.proxy1_model.set_filter(Filter.HEADER, checked))
        self.ui.act_toggleheaders.toggled.connect(lambda checked: self.ui.trw_event.span_columns() if checked else None)
        self.ui.act_togglefooters.toggled.connect(lambda checked: self.proxy1_model.set_filter(Filter.FOOTER, checked))

        # Строка состояния
        self.le_sbar_backup = QLabel("")
        self.ui.statusBar.addWidget(self.le_sbar_backup)

        # Косметика
        self.ui.tv_payment.set_columns_visibility()
        self.ui.tlbr.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        # Постоянный вертикальный header
        self.ui.tv_payment.setVerticalHeader(PersistentHeader(Qt.Orientation.Vertical, self.ui.tv_payment))

        # # Очистка папки с резервными копиями
        # self.clean_backup_folder()
        # # Резервное копирование
        # self.make_backup()

        # Начальные действия
        self.settings_handler.apply_settings()

        # # Завершение работы
        # app.aboutToQuit.connect(self.on_quit_actions)

    def update_filters_and_select(self):
        self.base_model.set_filters(self.ui.lw_term.current_term(),
                                    self.ui.lw_category.current_category(),
                                    self.ui.le_receiverfilter.text(),
                                    self.ui.le_responsiblefilter.text(),
                                    self.ui.chb_paytoday.isChecked())

    # def allow_proxymodels_sortfliter(self, allow: bool) -> None:
    #     self.event_proxy_model.enable_sortfilter(allow)

    def get_current_event_index(self, source_model_index: bool = False) -> QModelIndex:
        if source_model_index:
            return map_to_source(-2, self.ui.trw_event.selectionModel().currentIndex())
            # return self.event_proxy_model.mapToSource(self.event_finalfilter_model.mapToSource(self.ui.trw_event.selectionModel().currentIndex()))
        else:
            return self.ui.trw_event.selectionModel().currentIndex()
        
    def current_data(self, column, role=LiabilitySqlTableModel.dbValueRole) -> Any:
        curr_index: QModelIndex = self.get_current_event_index()
        if not curr_index.isValid():
            return None
        return curr_index.siblingAtColumn(column).data(role)

    def check_event_selection_visibility(self) -> None:
        filtered_out = not bool(self.ui.trw_event.currentIndex().isValid())
        self.ui.act_copy.setDisabled(filtered_out)
        self.ui.act_edit.setDisabled(filtered_out)
        self.ui.act_delete.setDisabled(filtered_out)
        if filtered_out or self.current_data(Col.TYPE) != RowType.LIABILITY:
            self.ui.stw_eventinfo.setCurrentIndex(1)

    def check_payment_selection_visibility(self) -> None:
        filtered_out = not bool(self.ui.tv_payment.currentIndex().isValid())
        self.ui.pb_deletepayment.setDisabled(filtered_out)

    def on_currentevent_change(self) -> None:
        row_type: RowType = self.current_data(Col.TYPE)
        # Активировать/деактивировать кнопку удаления платежа
        self.check_payment_selection_visibility()
        # Отобразить только оплаты, относящиеся к текущему платежу
        self.payment_model.update_filter(self.current_data(Col.ID, LiabilitySqlTableModel.qtValueRole))
        self.check_event_selection_visibility()
        if row_type != RowType.LIABILITY:
            for act in (self.ui.act_copy, self.ui.act_edit, self.ui.act_delete):
                act.setEnabled(False)
        self.update_eventinfo()

    # def make_backup(self) -> bool:
    #     backup_path: str = self.settings_handler.settings.value("Backup/path")
    #     if not backup_path or not Path(backup_path).is_dir():
    #         log.w(f"Путь для резервного копирования не указан или неверен: {backup_path}")
    #         self.update_toolbar_info(backup_time=QTime(), backup_status=BackupAutosaveStatus.ERROR, initial=True)
    #         return False
    #     backup_filepath: Path = Path(backup_path).joinpath("backup_" + QDateTime().currentDateTime().toString("yyyyMMdd-hhmmss") + ".db")
    #     try:
    #         shutil.copy(os.path.abspath(self.db_handler.DEFAULT_DB_RELPATH), backup_filepath)
    #         self.update_toolbar_info(backup_time=QTime().currentTime(), backup_status=BackupAutosaveStatus.SUCCESS, initial=True)
    #         return True
    #     except FileNotFoundError:
    #         log.w(f"Файл для копирования {os.path.abspath(self.db_handler.DEFAULT_DB_RELPATH)} не найден")
    #     except Exception as e:
    #         log.x(f"При попытке создать резервную копию произошла ошибка: {e}")
    #     self.update_toolbar_info(backup_time=QTime(), backup_status=BackupAutosaveStatus.ERROR, initial=True)
    #     return False

    # def clean_backup_folder(self) -> bool:
    #     backup_foldername: str = self.settings_handler.settings.value("Backup/path")
    #     if not backup_foldername or not Path(backup_foldername).is_dir():
    #         return False
    #     try:
    #         cleanup_period: int = int(self.settings_handler.settings.value("Backup/cleanupperiod"))
    #     except ValueError, TypeError:
    #         return False
    #     minumum_date = QDate().currentDate().addDays(-cleanup_period)
    #     filenames: list[str] = [item.name for item in Path(backup_foldername).iterdir() if item.is_file()]
    #     for fname in filenames:
    #         try:
    #             date_substring: str = fname[7:15]
    #         except IndexError:
    #             continue
    #         filedate: QDate = QDate.fromString(date_substring, "yyyyMMdd")
    #         if not filedate.isValid():
    #             continue
    #         if filedate < minumum_date:
    #             Path(os.path.join(backup_foldername, fname)).unlink(missing_ok=True)
    #     return True

    # def update_plot(self) -> None:
    #     self.plot_available: bool = True
    #     if not self.get_current_event_index().isValid():
    #         self.plot_available = False
    #         self.update_plot_area()
    #         return
    #     payments_count: int = self.ui.tv_payment.model().rowCount()
    #     is_paid: bool = TermRoleFlags.PAID in self.get_current_event_index().siblingAtColumn(Col.TERMFLAGS).data(EventTableModel.internalValueRole)
    #     fully_paid_today: bool = (self.get_current_event_index().siblingAtColumn(Col.TOTALAMOUNT).data(EventTableModel.internalValueRole) ==
    #                               self.get_current_event_index().siblingAtColumn(Col.TODAYSHARE).data(EventTableModel.internalValueRole))
    #     if ((is_paid or fully_paid_today) and payments_count < 2) or (not is_paid and payments_count == 0):
    #         self.plot_available = False
    #         self.update_plot_area()
    #         return
    #     dates, amounts = [], []
    #     first_date: QDate = self.get_current_event_index().siblingAtColumn(Col.CREATEDATE).data(EventTableModel.internalValueRole).toPython()
    #     dates.append(first_date)
    #     amount: Decimal = self.get_current_event_index().siblingAtColumn(Col.TOTALAMOUNT).data(EventTableModel.internalValueRole)
    #     amounts.append(amount)
    #     for row in range(self.ui.tv_payment.model().rowCount()):
    #         date: QDate = self.ui.tv_payment.model().index(row, PaymentField.PAYMENT_DATE).data(PaymentHistoryTableModel.internalValueRole)
    #         dates.append(date.toPython())
    #         payment_sum: Decimal = self.ui.tv_payment.model().index(row, PaymentField.SUM).data(PaymentHistoryTableModel.internalValueRole)
    #         amount -= payment_sum
    #         amounts.append(amount)
    #     self.payment_plot.update_plot(dates, amounts)
    #     self.update_plot_area()

    # def update_plot_area(self) -> None:
    #     if not self.plot_available:
    #         self.ui.wdg_graph.setVisible(False)
    #     else:
    #         occupied_width: int = self.ui.tv_payment.width() + self.ui.wdg_eventinfo.width() + self.ui.de_paymentdate.width() + 60
    #         self.ui.wdg_graph.setVisible(self.ui.stw_eventinfo.width() - occupied_width > 400)

    # def resizeEvent(self, event, /):
    #     self.update_plot_area()
    #     QMainWindow.resizeEvent(self, event)

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
            self.ui.la_percentage.setText("<<<>>>>")
            self.ui.la_createdate.setText(str(current_index.siblingAtColumn(Col.CREATEDATE).data()))
            self.ui.la_paymenttype.setText(str(current_index.siblingAtColumn(Col.PAYMENTTYPE).data()).lower())
            self.ui.la_responsible.setText(str(current_index.siblingAtColumn(Col.RESPONSIBLE).data()))
            self.ui.te_descr.setPlainText(str(current_index.siblingAtColumn(Col.DESCR).data()))
            self.ui.te_notes.setPlainText(str(current_index.siblingAtColumn(Col.NOTES).data()))
            # Сумма платежа по умолчанию равна остатку
            self.ui.dsb_paymentsum.setValue(current_index.siblingAtColumn(Col.REMAINAMOUNT).data(LiabilitySqlTableModel.qtValueRole))
            # Обновить дату платежа по умолчанию
            self.ui.de_paymentdate.setDate(QDate.currentDate())
            # Обновить график
            # self.update_plot()
        return True

    # def reset_paymentproxymodel_filter(self, current_index: QModelIndex) -> None:
    #     current_event_id: int = 0
    #     if self.event_finalfilter_model.data(current_index.siblingAtColumn(Col.TYPE), EventTableModel.internalValueRole) == RowType.EVENT:
    #         current_event_id = self.event_finalfilter_model.data(current_index.siblingAtColumn(Col.ID), EventTableModel.internalValueRole)
    #     self.payment_proxy_model.reset_filter(current_event_id)


    # def set_data_to_current_event(self, column, value, emit_datachanaged: bool = True) -> bool:
    #     curr_index: QModelIndex = self.get_current_event_index()
    #     curr_proxy_index: QModelIndex = self.event_finalfilter_model.mapToSource(curr_index)
    #     curr_source_index: QModelIndex = self.event_proxy_model.mapToSource(curr_proxy_index)
    #     if not curr_source_index.isValid():
    #         return False
    #     return self.event_model.setData(curr_source_index.siblingAtColumn(column), value, EventTableModel.internalValueRole, emit_datachanaged)

    # def save_notes(self) -> None:
    #     self.set_data_to_current_event(Col.NOTES, self.ui.te_notes.toPlainText(), False)

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
        settings_dialog: SettingsDialog = SettingsDialog(self.settings_handler, reject_possible, self)
        settings_dialog.exec()
        self.on_currentevent_change()

    def open_event_dialog(self, edit: bool = False, copy: bool = False):
        curr_index: QModelIndex = self.get_current_event_index()
        if edit or copy:
            if not curr_index.isValid():
                return False
            selection_not_visible: bool = is_selection_filteredout(self.proxy2_model, self.ui.trw_event, two_proxies=True, current_instead=True)
            if selection_not_visible:
                return False
        event_dialog: EventDialog = EventDialog(final_proxy_model=self.proxy2_model, edit_mode=edit, copy_mode=copy, current_index=curr_index, parent=self)
        if event_dialog.exec():
            if not edit:
                self.ui.trw_event.selectionModel().clear()
                self.ui.trw_event.selectionModel().setCurrentIndex(self.proxy2_model.mapFromSource(self.proxy1_model.mapFromSource(
                    self.base_model.index(self.base_model.rowCount() - 1, 0, QModelIndex()))), QItemSelectionModel.SelectionFlag.SelectCurrent)
            self.proxy2_model.recalculate_totals()
            return True
        else:
            return False

    # def open_export_dialog(self) -> bool:
    #     if self.event_finalfilter_model.rowCount() == 0:
    #         return False
    #     if self.event_proxy_model.filters_active():
    #         msg_box = YesNoMessagebox("Предупреждение: на текущий момент применены один или несколько фильтров. Уверены, что хотите продолжить?")
    #         if msg_box.exec() == YesNoMessagebox.NO_RETURN_VALUE:
    #             return False
    #     dlg: ExportDialog = ExportDialog(self.xls_writer, self.ui.trw_event.get_columnvisibility_list(), self)
    #     return dlg.exec() == QDialog.DialogCode.Accepted

    # def open_finplan_dialog(self, ask_year: bool = False):
    #     current_year: int = QDate().currentDate().year()
    #     if ask_year:
    #         tdlg: YearInputDialog = YearInputDialog(current_year, self)
    #         tdlg.exec()
    #     dlg: FinPlanDialog = FinPlanDialog(self.db_handler, tdlg.ui.spinBox.value() if ask_year else current_year, self)
    #     dlg.exec()

    # def open_fulfillment_dialog(self):
    #     dlg: FulfillmentOptionDialog = FulfillmentOptionDialog(self.db_handler, self)
    #     dlg.exec()

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
            self.proxy2_model.recalculate_totals()
            self.update_filters_and_select()
            return True
        return False

    # def closeEvent(self, event, /):
    #     self.settings_handler.save_settings()
    #     if self.nosave_exit:
    #         event.accept()
    #         return
    #     if self.db_handler.save_eventspayments_to_db(self.event_model, self.payment_model):
    #         self.saved_before_exit = True
    #         event.accept()
    #         return
    #     else:
    #         msg_box = YesNoMessagebox("Перед выходом не удалось сохранить изменения в базу данных (подробности см. в логе). Уверены, что хотите выйти?")
    #         if msg_box.exec() == YesNoMessagebox.YES_RETURN_VALUE:
    #             event.accept()
    #             return
    #     event.ignore()

    # def on_quit_actions(self):
    #     if not self.saved_before_exit and not self.nosave_exit:
    #         self.db_handler.save_eventspayments_to_db(self.event_model, self.payment_model)
