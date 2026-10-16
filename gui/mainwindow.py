import sys
from datetime import date
from decimal import Decimal
from typing import Any, Callable
import lovely_logger as log

from PySide6.QtCore import QEvent, QModelIndex, Qt, QDate, QItemSelectionModel, QDateTime, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QPalette, QShortcut
from PySide6.QtSql import QSqlTableModel
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog, QLabel, QMenu, QStyle, QWidget, QListView, QToolButton, QSizePolicy

from base.backup import clean_backup_folder, save_backup
from base.casting import str_int
from base.contract import ContractInfo
from base.date import date_displstr, date_str
from base.dbhandler import DBHandler
from base.formatting import dec_strcommaspace
from base.payment import PaymentEntry, PaymentField
from base.sync import (MasterInfo, MasterInfoError, NetworkError, SyncAction, SyncCancelledError, SyncChannel, SyncError, SyncParams,
                       SyncReport, read_local_state, set_stage_listener, synchronize)
from base.workcalendar import clear_calendar_cache
from base.xlswriter import LiabilityXlsWriter
from gui.chartchoicedialog import ChartChoiceDialog
from gui.common import map_to_source
from gui.commonwidgets.common import is_selection_filteredout, StatusBarSeparator
from gui.commonwidgets.messagebox import YesNoMessagebox, ErrorInfoMessageBox
from gui.commonwidgets.persistentheader import PersistentHeader
from gui.contractdialog import ContractDocumentDialog
from gui.contractordialog import ContractorDialog
from gui.copydocdialog import CopyDocDialog
from gui.eventdialog import EventDialog
from gui.eventproxymodel import LiabilitySortFilterProxyModel, Filter, LiabilityTotalsProxyModel
from gui.eventsqlmodel import LiabilitySqlTableModel, Col
from base.liability import FilterFlags, RowType, PaymentType, TermCategory
from gui.feedialog import FeeDialog
from gui.finplandialog import FinPlanDialog
from gui.fulfillmentoptiondialog import FulfillmentOptionDialog
from gui.manualdialog import ManualDialog
from gui.matchingdialog import MatchingDialog
from gui.paymentamountdialog import PaymentAmountDialog
from gui.paymenthistorymodel import PaymentHistoryTableModel
from gui.paymenthistoryproxymodel import PaymentHistoryProxyModel
from gui.recoverydialog import RecoveryDialog
from gui.responsiblemodels import ResponsibleModel, ResponsibleCategorySortModel
from gui.settings import FontSize, SettingsHandler
from gui.settingsdialog import SettingsDialog
from gui.syncchangesdialog import SyncChangesDialog
from gui.syncconflictdialog import SyncConflictDialog
from gui.syncmanager import (SYNC_ACTION_MESSAGE, SYNC_PLANNED_STAGES, SYNC_RETRY_ATTEMPTS, SYNC_RETRY_DELAY_MS, SYNC_STALE_DAYS,
                             SYNC_STAGE_CHANGES_NOTICE, SYNC_STAGE_CONFLICT_RESOLUTION, SYNC_STATUS_TEXT, TOKEN_WARNING_DAYS, IdleSyncTimer, compare_with_master, conflict_tabs, connect_to_master,
                             create_master, create_sync_channel, create_sync_params, describe_master, discard_unsent_changes, failure_status_text,
                             master_age_days, merge_message, merge_tabs, merge_warning_lines, overwrite_master, pull_message,
                             pull_tabs, restore_master, take_master, token_days_left)
from gui.ui.syncicon import SyncToolButton, create_sync_icon
from gui.syncprogressdialog import SyncProgressDialog
from gui.syncsettingsdialog import SyncSettingsDialog
from gui.ui.mainwindow_ui import Ui_MainWindow
from gui.exportdialog import ExportDialog


class MainWindow(QMainWindow):

    CONTRACT_NOTBOUND_TEXT = '<span style="color: #808080;">не привязан</span>'
    SYNC_PROBLEM_STATUSES = (SYNC_STATUS_TEXT[SyncAction.CONFLICT], SYNC_STATUS_TEXT[SyncAction.FOREIGN_DB],
                             SYNC_STATUS_TEXT[SyncAction.CLIENT_OUTDATED], "токен недействителен", "ошибка")
    SYNC_SUCCESS_ACTIONS = (SyncAction.NOTHING, SyncAction.PULL, SyncAction.PUSH, SyncAction.MERGE)
    SYNC_PROBLEM_COLOR = QColor("#C62828")
    SYNC_WARNING_COLOR = QColor("#B26A00")
    SYNC_OK_COLOR = QColor("#2E7D32")

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.settings_handler: SettingsHandler = SettingsHandler(self)
        self.db_handler: DBHandler = DBHandler(self.settings_handler)

        self.saved_before_exit: bool = False
        self.nosave_exit: bool = False
        self.bound_document_id: int = 0
        self.sync_status_text: str = "не выполнялась"
        self.sync_progress: SyncProgressDialog | None = None
        self.sync_error: str = ""
        self.sync_network_failed: bool = False
        self.sync_cancelled: bool = False
        self.sync_info_unreadable: bool = False
        self.sync_retry_text: str = ""
        self.sync_failure_text: str = "ошибка"
        self.sync_master_info: MasterInfo | None = None
        self.sync_checked_at: str = ""
        self.sync_succeeded_at: QDateTime = QDateTime()
        self.manual_dialog: ManualDialog | None = None

        # Загрузка данных из БД: проверка файла, восстановление при необходимости, подключение
        self._load_database()

        # Создание моделей таблиц (обязательства/платежи) и экспортера
        self._init_models()

        # Подписи кнопок и выпадающие группы в тулбаре
        self._init_toolbar_groups()

        # Строка состояния
        self._init_statusbar()

        # Кнопка синхронизации в правой части тулбара
        self._init_toolbar_sync()

        # Подключение всех сигналов (фильтры, модели, тулбар)
        self._connect_signals()

        # Косметика
        self._init_widget_cosmetics()

        # Резервное копирование
        self.make_backup()

        # Начальные действия
        self.settings_handler.apply_settings(apply_geometry=True)
        self.ui.stw_eventinfo.setCurrentIndex(1)

        # Первая синхронизация после запуска
        QTimer.singleShot(100, lambda: self.auto_sync(is_first=True))


    def _load_database(self) -> None:
        # Если файла БД нет или он не прошёл проверку - предлагаем восстановление,
        # в конце в любом случае пытаемся открыть подключение
        ## Проверка на наличие файла
        if not self.db_handler.check_db_files_exists():
            recover_dlg = RecoveryDialog(self.settings_handler, self.db_handler,
                                         text="К сожалению, найти файл базы данных в стандартном расположении не удалось. "
                                              "Выберите файл для восстановления или загрузите базу с сервера синхронизации",
                                         cancel_available=False, offer_sync=True, parent=self)
            if recover_dlg.exec() != QDialog.DialogCode.Accepted:
                sys.exit()
        ## База данных новее программы - ничего не трогаем
        if self.db_handler.is_db_newer_than_client():
            ErrorInfoMessageBox("База данных создана более новой версией программы. Обновите программу").exec()
            sys.exit()
        ## Обновление структуры до актуальной версии: при сбое файл остаётся прежним, восстановление не предлагаем
        if not self.db_handler.migrate_db() and self.db_handler.migration_failed:
            ErrorInfoMessageBox("Не удалось обновить структуру базы данных до версии этой программы. "
                                "Файл базы данных не изменён, программа будет закрыта. "
                                "Передайте разработчику файлы из папки логов (подробности см. в логе)").exec()
            sys.exit()
        ## Проверка файла
        if not self.db_handler.check_db_file_integrity():
            recover_dlg = RecoveryDialog(self.settings_handler, self.db_handler,
                                         text="К сожалению, при проверке файла базы данных обнаружены ошибки (подробности см. в логе). "
                                              "Выберите файл для восстановления",
                                         cancel_available=False, parent=self)
            if recover_dlg.exec() != QDialog.DialogCode.Accepted:
                sys.exit()

        if not self.db_handler.open_db_connection():
            ErrorInfoMessageBox("Не удалось открыть базу данных (подробности см. в логе)").exec()
            sys.exit()

    def _init_models(self) -> None:
        # Основная модель таблицы обязательств (поверх таблицы event) + две прокси-модели над ней
        self.base_model: LiabilitySqlTableModel = LiabilitySqlTableModel(self.db_handler, self)
        self.base_model.setTable("event")
        self.base_model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        self.base_model.set_paid_load_months(self.settings_handler.paid_load_months())
        self.base_model.select()

        self.proxy1_model = LiabilitySortFilterProxyModel()
        self.proxy1_model.setSourceModel(self.base_model)

        self.proxy2_model = LiabilityTotalsProxyModel()
        self.proxy2_model.setSourceModel(self.proxy1_model)

        self.ui.trw_event.setModel(self.proxy2_model)
        self.ui.trw_event.hide_columns()
        self.ui.trw_event.span_columns()

        # Модель таблицы платежей + прокси-модель над ней
        self.payment_model: PaymentHistoryTableModel = PaymentHistoryTableModel(self)
        self.payment_model.setTable("payment")
        self.payment_model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.payment_model.select()

        self.payment_proxy_model = PaymentHistoryProxyModel()
        self.payment_proxy_model.setSourceModel(self.payment_model)

        # Модели ответственных - заполняются позже, в update_responsible_models()
        self.responsible_partial_model: ResponsibleModel | None = None
        self.responsible_full_model: ResponsibleModel | None = None
        self.responsible_partial_sorted_model: ResponsibleCategorySortModel | None = None

        self.ui.tv_payment.setModel(self.payment_proxy_model)

        # Инициализация экспортера
        self.xls_writer: LiabilityXlsWriter = LiabilityXlsWriter(self.proxy2_model, self.ui.tv_payment, self.settings_handler)

    def _init_toolbar_groups(self) -> None:
        short_labels: dict[QAction, str] = {
            self.ui.act_new: "Новый",
            self.ui.act_copy: "Копия",
            self.ui.act_edit: "Изменить",
            self.ui.act_delete: "Удалить",
            self.ui.act_export: "Экспорт",
            self.ui.act_contracts: "Договоры",
            self.ui.act_settings: "Настройки",
        }
        for action, text in short_labels.items():
            action.setIconText(text)
        for action, key in ((self.ui.act_fulfillment, "Ctrl+P"), (self.ui.act_finplan, "Ctrl+Shift+P"),
                            (self.ui.act_chart, "Ctrl+G"), (self.ui.act_contracts, "Ctrl+K"),
                            (self.ui.act_settings, "Ctrl+,")):
            action.setShortcut(QKeySequence(key))
            action.setToolTip(f"{action.toolTip() or action.text()} ({key})")
            self.addAction(action)
        self.ui.tlbr.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        view_actions: list[QAction] = [self.ui.act_featured, self.ui.act_toggleheaders, self.ui.act_togglefooters]
        bank_actions: list[QAction] = [self.ui.act_matching, self.ui.act_fees]
        tb_view = self._make_toolbar_dropdown("Вид", ":/icon-toolbar/designer/icons/view.svg", view_actions,
                                              "На контроле, заголовки и итоги разделов")
        tb_bank = self._make_toolbar_dropdown("Выписка", ":/icon-toolbar/designer/icons/statement.svg", bank_actions,
                                              "Сверка банковской выписки и учет комиссий")
        copy_actions: list[QAction] = [self.ui.act_copy, self.ui.act_copydoc]
        tb_copy = self._make_toolbar_split_button(self.ui.act_copy, copy_actions)
        planfact_actions: list[QAction] = [self.ui.act_finplan, self.ui.act_fulfillment, self.ui.act_chart]
        self.tb_planfact = self._make_toolbar_split_button(
            self.ui.act_fulfillment, planfact_actions, "План-факт", ":/icon-toolbar/designer/icons/fulfillment.svg",
            "Исполнение финансового плана, финансовый план и графики")
        self.ui.tlbr.insertWidget(self.ui.act_copy, tb_copy)
        self.ui.tlbr.insertWidget(self.ui.act_finplan, self.tb_planfact)
        self.ui.tlbr.insertWidget(self.ui.act_featured, tb_view)
        self.ui.tlbr.insertWidget(self.ui.act_fees, tb_bank)
        for action in copy_actions + planfact_actions + view_actions + bank_actions:
            self.ui.tlbr.removeAction(action)

        button_groups: list[list[QToolButton]] = [[]]
        for action in self.ui.tlbr.actions():
            if action.isSeparator():
                button_groups.append([])
                continue
            button: QToolButton = self.ui.tlbr.widgetForAction(action)
            button.setStyleSheet(f"font-size: {FontSize.LARGE - 1}pt;")
            button.ensurePolished()
            button_groups[-1].append(button)
        for group in button_groups:
            group_width: int = max(self._toolbar_button_width(button) for button in group)
            for button in group:
                button.setFixedWidth(group_width)

    @staticmethod
    def _toolbar_button_width(button: QToolButton) -> int:
        text_width: int = button.fontMetrics().horizontalAdvance(button.text())
        arrow_width: int = button.style().pixelMetric(QStyle.PixelMetric.PM_MenuButtonIndicator, None, button)
        if button.popupMode() == QToolButton.ToolButtonPopupMode.MenuButtonPopup:
            return text_width + arrow_width + 8
        return text_width + 14

    def _make_toolbar_dropdown(self, text: str, icon_path: str, actions: list[QAction], tooltip: str) -> QToolButton:
        menu = QMenu(self)
        for action in actions:
            action.setIconVisibleInMenu(True)
            menu.addAction(action)
        button = QToolButton()
        button.setObjectName("tb_dropdown")
        button.setText(text)
        button.setIcon(QIcon(icon_path))
        button.setIconSize(self.ui.tlbr.iconSize())
        button.setToolTip(tooltip)
        button.setAutoRaise(True)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        button.setMenu(menu)
        return button

    def _make_toolbar_split_button(self, default_action: QAction, actions: list[QAction], text: str = "",
                                   icon_path: str = "", tooltip: str = "") -> QToolButton:
        menu = QMenu(self)
        for action in actions:
            action.setIconVisibleInMenu(True)
            menu.addAction(action)
        button = QToolButton()
        button.setObjectName("tb_dropdown")
        button.setDefaultAction(default_action)
        if text:
            button.setText(text)
            button.setIcon(QIcon(icon_path))
            button.setToolTip(tooltip)
        button.setIconSize(self.ui.tlbr.iconSize())
        button.setAutoRaise(True)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        button.setMenu(menu)
        return button

    def _connect_signals(self) -> None:
        # Пересчет итоговых строк
        self.proxy1_model.layoutChanged.connect(self.proxy2_model.recalculate_totals)
        # Секции боковой панели: кнопка-переключатель, сам фильтр, подпись и проверка активности фильтра
        self.filter_sections: tuple = (
            (self.ui.spb_term, self.ui.lw_term, "СРОК ОПЛАТЫ",
             lambda: self.ui.lw_term.currentRow() != 0),
            (self.ui.spb_category, self.ui.lw_category, "КАТЕГОРИЯ",
             lambda: self.ui.lw_category.currentRow() != 0),
            (self.ui.spb_responsible, self.ui.cmb_responsiblefilter, "ОТВЕТСТВЕННЫЙ",
             lambda: self.ui.cmb_responsiblefilter.currentData(Qt.ItemDataRole.UserRole) != 0),
        )
        # Подписи заголовков, отображение/скрытие фильтров и цвет заголовка при скрытии активного фильтра
        for switch_button, filter_widget, label, is_active in self.filter_sections:
            switch_button.set_button_label(label, label)
            switch_button.switch_status_changed.connect(filter_widget.setVisible)
            switch_button.switch_status_changed.connect(
                lambda sw_status, button=switch_button, active=is_active:
                button.change_style_on_hiding_activefilter(sw_status, active()))

        # Новые сигналы фильтров
        self.ui.lw_term.currentRowChanged.connect(lambda row: self.proxy1_model.set_filter(Filter.TERM, list(TermCategory)[row], invalidate=False))
        self.ui.lw_category.currentRowChanged.connect(lambda row: self.proxy1_model.set_filter(Filter.CATEGORY, row, invalidate=False))
        self.ui.chb_paytoday.checkStateChanged.connect(lambda state: self.proxy1_model.set_filter(Filter.PAYTODAY, state, invalidate=False))

        self.ui.lw_term.currentRowChanged.connect(self.update_filters_and_select)
        self.ui.lw_category.currentRowChanged.connect(self.update_filters_and_select)
        self.ui.cmb_responsiblefilter.currentIndexChanged.connect(self.update_filters_and_select)
        self.ui.chb_paytoday.checkStateChanged.connect(self.update_filters_and_select)

        # Быстрый поиск (с задержкой, чтобы не перефильтровывать таблицу на каждое нажатие) и сброс фильтров
        self.search_timer: QTimer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(250)
        self.search_timer.timeout.connect(self.update_filters_and_select)
        self.ui.le_search.textChanged.connect(lambda: self.search_timer.start())
        self.ui.pb_resetfilters.clicked.connect(self.reset_filters)
        self.ui.scrollArea.verticalScrollBar().rangeChanged.connect(self.update_search_margin)

        # Действия при переключении избранного
        self.ui.act_featured.triggered.connect(self.update_filters_and_select)
        self.ui.act_featured.triggered.connect(lambda: self.actions_on_selection_visibility_changed(True) if not self.current_data(Col.FEATURED) and self.ui.act_featured.isChecked() else None)
        self.ui.trw_event.filter_conditions_changed.connect(self.update_filters_and_select)
        self.ui.trw_event.filter_conditions_changed.connect(lambda: self.actions_on_selection_visibility_changed(True) if self.ui.act_featured.isChecked() else None)

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
        # Экспортировать нечего, если в таблице не осталось платежей
        self.proxy2_model.layoutChanged.connect(self.check_export_availability)
        # События при смене выбранного ивента
        self.ui.trw_event.selectionModel().currentChanged.connect(self.on_currentevent_change)
        self.ui.trw_event.doubleClicked.connect(lambda: self.ui.act_edit.trigger())
        # Сигналы таблицы платежей
        self.ui.tv_payment.selectionModel().selectionChanged.connect(self.check_payment_selection_visibility)
        # Cигналы информационной панели
        self.ui.pb_addpayment.clicked.connect(self.make_new_payment)
        self.ui.pb_deletepayment.clicked.connect(self.delete_payment)
        # Сигналы тулбара
        self.ui.act_new.triggered.connect(lambda: self.open_event_dialog())
        self.ui.act_copy.triggered.connect(lambda: self.open_event_dialog(copy=True))
        self.ui.act_copydoc.triggered.connect(self.open_copydoc_dialog)
        self.ui.act_edit.triggered.connect(lambda: self.open_event_dialog(edit=True))
        self.ui.act_delete.triggered.connect(self.delete_event)
        self.ui.act_finplan.triggered.connect(self.open_finplan_dialog)
        self.ui.act_fulfillment.triggered.connect(self.open_fulfillment_dialog)
        self.ui.act_chart.triggered.connect(self.open_chart_dialog)
        self.ui.act_fees.triggered.connect(lambda: self.open_fees_dialog())
        self.ui.act_matching.triggered.connect(self.open_matching_dialog)
        self.ui.act_export.triggered.connect(self.open_export_dialog)
        self.ui.act_contracts.triggered.connect(self.open_contractor_dialog)
        self.ui.la_contractbound.linkActivated.connect(self.open_bound_document)
        self.ui.act_gotocontract.triggered.connect(self.open_bound_document)
        self.ui.act_settings.triggered.connect(lambda: self.open_settings_dialog())
        self.ui.act_help.triggered.connect(lambda: self.open_manual_dialog())
        self.ui.act_toggleheaders.toggled.connect(lambda checked: self.proxy1_model.set_filter(Filter.HEADER, checked))
        self.ui.act_toggleheaders.toggled.connect(lambda checked: self.ui.trw_event.span_columns() if checked else None)
        self.ui.act_togglefooters.toggled.connect(lambda checked: self.proxy1_model.set_filter(Filter.FOOTER, checked))

        # Сигналы обновления кэша стилей
        # self.proxy1_model.modelInvalidated.connect(self.proxy2_model.refresh_style_cache)
        self.base_model.cacheUpdateNeeded.connect(self.proxy1_model.invalidate_style_cache)
        # Сигналы обновления кэша сортировки
        self.base_model.cacheUpdateNeeded.connect(self.base_model.invalidate_sort_cache)

    def _init_statusbar(self) -> None:
        self.la_sbar_sync = QLabel("")
        self.la_sbar_backup = QLabel("")
        self.la_sbar_update = QLabel("")
        self.separator1 = StatusBarSeparator(self)
        self.separator_sync = StatusBarSeparator(self)
        self.separator2 = StatusBarSeparator(self)
        self.separator3 = StatusBarSeparator(self)
        self.spacer = QWidget()
        self.spacer.setFixedWidth(10)

        self.ui.statusBar.addPermanentWidget(self.separator1)
        self.ui.statusBar.addPermanentWidget(self.la_sbar_sync)
        self.ui.statusBar.addPermanentWidget(self.separator_sync)
        self.ui.statusBar.addPermanentWidget(self.la_sbar_backup)
        self.ui.statusBar.addPermanentWidget(self.separator2)
        self.ui.statusBar.addPermanentWidget(self.la_sbar_update)
        self.ui.statusBar.addPermanentWidget(self.separator3)
        self.ui.statusBar.addPermanentWidget(self.spacer)
        self.update_sync_statusbar()
        self.set_backup_status("")

    def update_sync_statusbar(self) -> None:
        is_visible: bool = self.settings_handler.sync_enabled() and self.sync_succeeded_at.isValid()
        if is_visible:
            is_today: bool = self.sync_succeeded_at.date() == QDate.currentDate()
            self.la_sbar_sync.setText(f"Последняя синхронизация: {self.sync_succeeded_at.toString('HH:mm' if is_today else 'HH:mm dd.MM.yyyy')}")
        self.la_sbar_sync.setToolTip("Дата и время последней успешной синхронизации")
        self.la_sbar_sync.setVisible(is_visible)
        self.separator_sync.setVisible(is_visible)

    def set_backup_status(self, error_text: str) -> None:
        self.la_sbar_backup.setText(error_text)
        self.la_sbar_backup.setStyleSheet(f"color: {self.SYNC_PROBLEM_COLOR.name()};")
        self.la_sbar_backup.setVisible(bool(error_text))
        self.separator2.setVisible(bool(error_text))

    def _init_toolbar_sync(self) -> None:
        self.act_sync_now = QAction("Синхронизировать сейчас", self)
        self.act_sync_settings = QAction("Настройки синхронизации...", self)
        self.act_sync_discard = QAction("Отказаться от моих изменений...", self)
        self.act_sync_now.setShortcut(QKeySequence("F5"))
        self.addAction(self.act_sync_now)
        sync_menu = QMenu(self)
        sync_menu.addAction(self.act_sync_now)
        sync_menu.addAction(self.act_sync_discard)
        sync_menu.addSeparator()
        sync_menu.addAction(self.act_sync_settings)
        self.tb_sync = SyncToolButton()
        self.tb_sync.setAutoRaise(True)
        self.tb_sync.setObjectName("tb_sync")
        self.tb_sync.setFixedHeight(self.ui.tlbr.widgetForAction(self.ui.act_new).sizeHint().height())
        self.tb_sync.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.tb_sync.setMenu(sync_menu)
        self.tb_sync.clicked.connect(self.on_sync_button_clicked)
        self.act_sync_now.triggered.connect(lambda: self.run_sync())
        self.act_sync_settings.triggered.connect(self.open_sync_settings_dialog)
        self.act_sync_discard.triggered.connect(self.discard_local_changes)
        self.sync_channel: SyncChannel | None = None
        self.sync_channel_settings: tuple | None = None
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.auto_sync)
        self.idle_sync_timer = IdleSyncTimer(self)
        self.idle_sync_timer.timeout.connect(self.idle_sync)
        self.apply_sync_timer()
        self.update_sync_status()
        self.sync_status_timer = QTimer(self)
        self.sync_status_timer.timeout.connect(self.refresh_sync_status)
        self.sync_status_timer.start(3000)

        self.tb_sync.setParent(self.ui.tlbr)
        self.ui.tlbr.installEventFilter(self)
        self.ui.te_notes.installEventFilter(self)
        self.place_sync_button()

    def place_sync_button(self) -> None:
        button_width: int = self.tb_sync.sizeHint().width()
        right_margin: int = 6
        self.ui.tlbr.setContentsMargins(0, 0, button_width + right_margin, 0)
        self.tb_sync.setGeometry(self.ui.tlbr.width() - button_width - right_margin, 0,
                                 button_width, self.ui.tlbr.height())
        self.tb_sync.show()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.ui.tlbr and event.type() == QEvent.Type.Resize:
            self.place_sync_button()
        elif watched is self.ui.te_notes and event.type() == QEvent.Type.FocusOut:
            self.save_note()
        return super().eventFilter(watched, event)

    def on_sync_button_clicked(self) -> None:
        if self.settings_handler.sync_enabled():
            self.run_sync()
        else:
            self.open_sync_settings_dialog()

    def set_sync_button_state(self, text: str, color: QColor | None = None, icon_color: QColor | None = None) -> None:
        self.tb_sync.setText(text)
        palette: QPalette = QApplication.palette(self.tb_sync)
        if color is not None:
            palette.setColor(QPalette.ColorRole.ButtonText, color)
            palette.setColor(QPalette.ColorRole.WindowText, color)
        self.tb_sync.setPalette(palette)
        self.tb_sync.setIcon(create_sync_icon(palette.buttonText().color() if icon_color is None else icon_color))
        self.place_sync_button()

    def update_sync_status(self) -> None:
        self.update_sync_statusbar()
        if not self.settings_handler.sync_enabled():
            self.set_sync_button_state("Синхронизация:\nвыключена",self.palette().color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText))
            self.tb_sync.setToolTip("Синхронизация выключена. Нажмите, чтобы открыть настройки синхронизации")
            self.act_sync_now.setEnabled(False)
            self.act_sync_discard.setEnabled(False)
            return
        self.act_sync_now.setEnabled(True)
        master_age: int | None = master_age_days(self.sync_master_info) if self.sync_master_info else None
        is_master_stale: bool = master_age is not None and master_age >= SYNC_STALE_DAYS
        days_left: int | None = token_days_left(self.settings_handler)
        token_warning: str = ""
        if days_left is not None and days_left < 0:
            token_warning = "Токен Яндекса истёк, получите новый и укажите его в настройках синхронизации"
        elif days_left is not None and days_left <= TOKEN_WARNING_DAYS:
            token_warning = f"Токен Яндекса истекает через {days_left} дн., получите новый заранее"
        is_problem: bool = self.sync_status_text in self.SYNC_PROBLEM_STATUSES or (days_left is not None and days_left < 0)
        is_actual: bool = self.sync_status_text == SYNC_STATUS_TEXT[SyncAction.NOTHING]
        is_conflict: bool = self.sync_status_text == SYNC_STATUS_TEXT[SyncAction.CONFLICT]
        has_local_changes: bool = False
        if is_actual or is_conflict:
            try:
                has_local_changes = read_local_state(self.db_handler).has_changes
            except SyncError as e:
                log.e(f"Не удалось проверить наличие неотправленных изменений: {e}")
        self.act_sync_discard.setEnabled(has_local_changes)
        has_unsent_changes: bool = has_local_changes and is_actual
        is_warning: bool = is_master_stale or bool(token_warning) or has_unsent_changes
        status_text: str = f"Синхронизация:\n{'есть неотправленные' if has_unsent_changes else self.sync_status_text}"
        if not is_problem and is_warning and not has_unsent_changes:
            status_text += " ⚠"
        color: QColor | None = None
        icon_color: QColor | None = None
        if is_problem:
            color = self.SYNC_PROBLEM_COLOR
        elif is_warning or not is_actual:
            color = self.SYNC_WARNING_COLOR
        else:
            icon_color = self.SYNC_OK_COLOR
        self.set_sync_button_state(status_text, color, icon_color)
        if self.settings_handler.sync_channel_type() == "yandex":
            tooltip_lines: list[str] = [f"Яндекс.Диск, папка {self.settings_handler.sync_disk_folder()}"]
        else:
            tooltip_lines = [f"Папка обмена: {self.settings_handler.sync_folder()}"]
        if token_warning:
            tooltip_lines.append(token_warning)
        if self.sync_checked_at:
            tooltip_lines.append(f"Последняя проверка: {self.sync_checked_at}")
        if self.sync_master_info:
            tooltip_lines.append(f"Общая база обновлена: {describe_master(self.sync_master_info)}")
        if is_master_stale:
            tooltip_lines.append(f"Внимание: общая база не обновлялась {master_age} дн., возможно, второй пользователь не отправляет изменения")
        if self.sync_error:
            tooltip_lines.append(f"Последняя ошибка: {self.sync_error}")
        if self.sync_retry_text:
            tooltip_lines.append(self.sync_retry_text)
        tooltip_lines.append("Нажмите, чтобы синхронизировать; стрелка справа — меню")
        self.tb_sync.setToolTip("\n".join(tooltip_lines))

    def refresh_sync_status(self) -> None:
        if self.settings_handler.sync_enabled() and self.tb_sync.isEnabled():
            self.update_sync_status()

    def apply_sync_timer(self) -> None:
        self.sync_timer.stop()
        if self.settings_handler.sync_enabled():
            self.sync_timer.start(self.settings_handler.sync_interval_minutes() * 60 * 1000)
        self.idle_sync_timer.set_idle_seconds(self.settings_handler.sync_idle_seconds() if self.settings_handler.sync_enabled() else 0)

    def idle_sync(self) -> None:
        try:
            if not read_local_state(self.db_handler).has_changes:
                return
        except SyncError as e:
            log.e(f"Не удалось проверить наличие неотправленных изменений: {e}")
            return
        self.auto_sync()

    def get_sync_channel(self) -> SyncChannel:
        current_settings = (self.settings_handler.sync_channel_type(), self.settings_handler.sync_token(),
                            self.settings_handler.sync_disk_folder(), self.settings_handler.sync_folder())
        if self.sync_channel is None or self.sync_channel_settings != current_settings:
            self.sync_channel = create_sync_channel(self.settings_handler)
            self.sync_channel_settings = current_settings
        return self.sync_channel

    def auto_sync(self, retries_left: int = SYNC_RETRY_ATTEMPTS, is_first: bool = False) -> None:
        if (not self.settings_handler.sync_enabled() or not self.tb_sync.isEnabled()
                or self.sync_progress is not None or QApplication.activeModalWidget() is not None):
            return
        self.run_sync(interactive=False, pause_when_done=is_first)
        if self.sync_network_failed and retries_left > 0:
            delay_seconds: int = SYNC_RETRY_DELAY_MS // 1000
            log.i(f"Повтор синхронизации через {delay_seconds} с, осталось попыток: {retries_left}")
            self.sync_retry_text = f"Автоматический повтор через {delay_seconds} с (осталось попыток: {retries_left})"
            self.update_sync_status()
            self.ui.statusBar.showMessage(f"Не удалось связаться с сервером синхронизации. "
                                          f"Повторим попытку через {delay_seconds} с (осталось попыток: {retries_left})",
                                          SYNC_RETRY_DELAY_MS)
            QTimer.singleShot(SYNC_RETRY_DELAY_MS, lambda: self.auto_sync(retries_left - 1))

    def run_sync(self, interactive: bool = True, pause_when_done: bool = True) -> None:
        if not self.settings_handler.sync_enabled():
            return
        self.save_note()
        channel = self.get_sync_channel()
        params = create_sync_params(self.settings_handler)
        previous_status_text: str = self.sync_status_text
        report = SyncReport()
        action: SyncAction | None = None
        self.sync_progress = SyncProgressDialog(self, planned_stages=SYNC_PLANNED_STAGES)
        self.sync_progress.start()
        try:
            action = self._run_sync_step(channel, lambda: synchronize(self.db_handler, channel, params, report, merge=True))
            if action is None and interactive and self.sync_info_unreadable:
                action = self._restore_master_info_and_sync(channel, params, report)
            is_changed_by_other: bool = action in (SyncAction.PULL, SyncAction.MERGE)
            is_merged: bool = action == SyncAction.MERGE
            if interactive or action == SyncAction.CONFLICT:
                action = self._resolve_sync_action(action, channel, params, report)
            self.sync_checked_at = QDateTime.currentDateTime().toString("dd.MM.yyyy HH:mm")
            if action in self.SYNC_SUCCESS_ACTIONS:
                self.sync_succeeded_at = QDateTime.currentDateTime()
            self.sync_status_text = self.sync_failure_text if action is None else SYNC_STATUS_TEXT[action]
            if action in (SyncAction.PULL, SyncAction.MERGE):
                self.reload_after_sync_pull()
            self.update_sync_status()
            if is_changed_by_other:
                if is_merged:
                    changes_dlg = SyncChangesDialog(merge_message(report), merge_tabs(report), self, warnings=merge_warning_lines(report))
                else:
                    changes_dlg = SyncChangesDialog(pull_message(report.master_info or self.sync_master_info), pull_tabs(report), self)
                self.sync_progress.show_stage_now(SYNC_STAGE_CHANGES_NOTICE)
                changes_dlg.exec()
        finally:
            self._close_sync_progress(pause=pause_when_done and action is not None)
        if interactive:
            if action is None and not self.sync_cancelled:
                ErrorInfoMessageBox(f"Не удалось выполнить синхронизацию: {self.sync_error}", parent=self).exec()
            elif action in SYNC_ACTION_MESSAGE:
                ErrorInfoMessageBox(SYNC_ACTION_MESSAGE[action], is_info=True, parent=self).exec()
        elif self.sync_status_text != previous_status_text and action in (SyncAction.CONFLICT, SyncAction.CLIENT_OUTDATED):
            self.ui.statusBar.showMessage(f"Синхронизация: {self.sync_status_text}. Нажмите на кнопку синхронизации на панели инструментов", 15000)

    def _restore_master_info_and_sync(self, channel: SyncChannel, params: SyncParams, report: SyncReport) -> SyncAction | None:
        self.sync_progress.hide_for_question()
        if YesNoMessagebox(f"Не удалось прочитать служебный файл master.json в общем хранилище ({self.sync_error}).\n\n"
                           "Восстановить его по общей базе? Сама общая база не изменится, будет заново создан только master.json, "
                           "после чего пройдёт обычная синхронизация.",
                           self).exec() != YesNoMessagebox.YES_RETURN_VALUE:
            return None
        self.sync_progress.start()
        if self._run_sync_step(channel, lambda: restore_master(self.db_handler, channel, params)) is None:
            return None
        return self._run_sync_step(channel, lambda: synchronize(self.db_handler, channel, params, report, merge=True))

    def _resolve_sync_action(self, action: SyncAction | None, channel: SyncChannel, params: SyncParams,
                             report: SyncReport) -> SyncAction | None:
        if action in (SyncAction.NO_MASTER, SyncAction.FOREIGN_DB):
            self.sync_progress.hide_for_question()
        if action == SyncAction.NO_MASTER and YesNoMessagebox(
                "В папке обмена нет общей базы. Создать её из вашей локальной копии?",
                self).exec() == YesNoMessagebox.YES_RETURN_VALUE:
            self.sync_progress.start()
            return self._run_sync_step(channel, lambda: create_master(self.db_handler, channel, params))
        if action == SyncAction.FOREIGN_DB and YesNoMessagebox(
                "В папке обмена лежит общая база с другими данными. Заменить ею вашу локальную копию? "
                "Текущая локальная копия будет сохранена в папке резервных копий.",
                self).exec() == YesNoMessagebox.YES_RETURN_VALUE:
            self.sync_progress.start()
            return self._run_sync_step(channel, lambda: connect_to_master(self.db_handler, channel))
        if action == SyncAction.CONFLICT and self.sync_master_info:
            if report.my_changes is None:
                self._run_sync_step(channel, lambda: compare_with_master(self.db_handler, channel, report))
            conflict_dlg = SyncConflictDialog(describe_master(self.sync_master_info), self, conflict_tabs(report), report.conflicts)
            self.sync_progress.show_stage_now(SYNC_STAGE_CONFLICT_RESOLUTION)
            conflict_dlg.exec()
            if conflict_dlg.take_master_chosen():
                return self._run_sync_step(channel, lambda: take_master(self.db_handler, channel))
            if conflict_dlg.overwrite_chosen():
                return self._run_sync_step(channel, lambda: overwrite_master(self.db_handler, channel, params))
        return action

    def discard_local_changes(self) -> None:
        if YesNoMessagebox("Все ваши изменения, не отправленные в общую базу, будут отменены, а вместо них загрузится общая база.\n\n"
                           "Текущая локальная копия сохранится в папке резервных копий. Продолжить?",
                           self).exec() != YesNoMessagebox.YES_RETURN_VALUE:
            return
        self.save_note()
        channel = self.get_sync_channel()
        action: SyncAction | None = self._run_sync_step(channel, lambda: discard_unsent_changes(self.db_handler, channel))
        self.sync_checked_at = QDateTime.currentDateTime().toString("dd.MM.yyyy HH:mm")
        if action is None:
            self.sync_status_text = self.sync_failure_text
            self.update_sync_status()
            if not self.sync_cancelled:
                ErrorInfoMessageBox(f"Не удалось загрузить общую базу: {self.sync_error}", parent=self).exec()
            return
        self.sync_succeeded_at = QDateTime.currentDateTime()
        self.sync_status_text = SYNC_STATUS_TEXT[action]
        self.reload_after_sync_pull()
        self.update_sync_status()

    def confirm_exit_with_sync(self) -> bool:
        if not self.settings_handler.sync_enabled():
            return True
        try:
            if not read_local_state(self.db_handler).has_changes:
                return True
        except SyncError as e:
            log.e(f"Не удалось проверить наличие неотправленных изменений: {e}")
            return True
        channel = self.get_sync_channel()
        params = create_sync_params(self.settings_handler)
        action: SyncAction | None = self._run_sync_step(channel, lambda: synchronize(self.db_handler, channel, params),
                                                        SYNC_PLANNED_STAGES)
        if action == SyncAction.PUSH:
            return True
        reason: str = self.sync_error if action is None else SYNC_STATUS_TEXT[action]
        return YesNoMessagebox(f"Изменения не отправлены в общую базу ({reason}). Закрыть программу без отправки?",
                               self).exec() == YesNoMessagebox.YES_RETURN_VALUE

    def _close_sync_progress(self, pause: bool) -> None:
        progress: SyncProgressDialog = self.sync_progress
        self.sync_progress = None
        progress.complete(pause)
        progress.finish()

    def _run_sync_step(self, channel: SyncChannel, step: Callable[[], SyncAction],
                       planned_stages: tuple[str, ...] = ()) -> SyncAction | None:
        self.tb_sync.setEnabled(False)
        self.sync_retry_text = ""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        owns_progress: bool = self.sync_progress is None
        progress: SyncProgressDialog = SyncProgressDialog(self, planned_stages=planned_stages) if owns_progress else self.sync_progress
        set_stage_listener(progress.set_stage)
        http = getattr(channel, "http", None)
        if http is not None:
            http.cancel_requested = False
            http.on_retry = progress.set_attempt
            http.on_long_wait = progress.show_waiting
            http.on_long_wait_end = progress.end_waiting
            http.on_progress = progress.set_progress
            progress.set_cancel_handler(http.request_cancel)
        if owns_progress:
            progress.start()
        try:
            action: SyncAction = step()
            progress.complete(owns_progress)
            self.sync_error = ""
            self.sync_cancelled = False
            self.sync_network_failed = False
            self.sync_info_unreadable = False
            self.sync_master_info = channel.last_master_info()
            return action
        except SyncError as e:
            log.e(f"Синхронизация не выполнена: {e}")
            self.sync_error = str(e)
            self.sync_cancelled = isinstance(e, SyncCancelledError)
            self.sync_network_failed = isinstance(e, NetworkError)
            self.sync_info_unreadable = isinstance(e, MasterInfoError)
            self.sync_failure_text = failure_status_text(e)
            progress.fail()
            return None
        finally:
            set_stage_listener(None)
            if http is not None:
                http.on_retry = None
                http.on_long_wait = None
                http.on_long_wait_end = None
                http.on_progress = None
                progress.set_cancel_handler(None)
            if owns_progress:
                progress.finish()
            QApplication.restoreOverrideCursor()
            self.tb_sync.setEnabled(True)

    def reload_after_sync_pull(self) -> None:
        clear_calendar_cache()
        self.base_model.select()
        self.payment_model.select()
        self.update_responsible_models(update_widgets=True)
        self.update_filters_and_select()
        self.base_model.cacheUpdateNeeded.emit()
        self.on_currentevent_change()

    def open_sync_settings_dialog(self) -> None:
        if SyncSettingsDialog(self.settings_handler, self).exec() == QDialog.DialogCode.Accepted:
            self.apply_sync_timer()
            self.update_sync_status()
            QTimer.singleShot(1000, self.auto_sync)

    def set_update_status(self, text: str) -> None:
        self.la_sbar_update.setText(text)

    def _init_widget_cosmetics(self) -> None:
        self.ui.tv_payment.set_columns_visibility()
        # При изменении размера окна свободное место достаётся таблице, а не боковой панели и не инфопанели
        self.ui.spl_main.setStretchFactor(0, 0)
        self.ui.spl_main.setStretchFactor(1, 1)
        self.ui.spl_workarea.setStretchFactor(0, 1)
        self.ui.spl_workarea.setStretchFactor(1, 0)
        # Контекстное меню таблицы (ActionsContextMenu собирает его из действий виджета)
        menu_separator = QAction(self)
        menu_separator.setSeparator(True)
        self.ui.trw_event.addActions([self.ui.act_new, self.ui.act_copy, self.ui.act_copydoc, self.ui.act_edit, self.ui.act_delete,
                                      menu_separator, self.ui.act_gotocontract])
        for action in self.ui.trw_event.actions():
            action.setIconVisibleInMenu(True)
        self.ui.act_copydoc.setShortcut(QKeySequence("Ctrl+Shift+D"))
        self.ui.act_copydoc.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.ui.act_copydoc.setToolTip(f"{self.ui.act_copydoc.toolTip()} (Ctrl+Shift+D)")
        # Горячие клавиши, которым не соответствует кнопка тулбара
        for key, slot in (("Ctrl+F", self.ui.le_search.setFocus),
                          ("Ctrl+R", self.reset_filters),
                          ("Ctrl+S", self.save_note)):
            QShortcut(QKeySequence(key), self).activated.connect(slot)
        # Поиск: Esc очищает поле, Enter и стрелка вниз переводят в таблицу
        search_shortcuts = ((Qt.Key.Key_Escape, self.ui.le_search.clear),
                            (Qt.Key.Key_Down, self.ui.trw_event.setFocus))
        for key, slot in search_shortcuts:
            search_shortcut = QShortcut(QKeySequence(key), self.ui.le_search)
            search_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            search_shortcut.activated.connect(slot)
        self.ui.le_search.returnPressed.connect(self.ui.trw_event.setFocus)
        # Оплата с клавиатуры: Enter в полях даты и суммы, Del в истории оплат
        self.ui.dsb_paymentsum.lineEdit().returnPressed.connect(self.ui.pb_addpayment.click)
        self.ui.de_paymentdate.lineEdit().returnPressed.connect(self.ui.pb_addpayment.click)
        delete_payment_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.ui.tv_payment)
        delete_payment_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        delete_payment_shortcut.activated.connect(self.ui.pb_deletepayment.click)
        # Начальное состояние: в таблице ничего не выбрано
        for element in (self.ui.act_copy, self.ui.act_edit, self.ui.act_delete,
                        self.ui.pb_addpayment, self.ui.pb_deletepayment):
            element.setEnabled(False)
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

    def make_backup(self) -> None:
        # Очистка папки с резервными копиями
        cleanup_ok: bool = clean_backup_folder(self.settings_handler)
        if not cleanup_ok:
            error_msg = ErrorInfoMessageBox("Не удалось очистить папку с резервными копиями (см. подробности в логе)", parent=self)
            error_msg.exec()
        backup_datetime: QDateTime = save_backup(self.settings_handler, self.db_handler)
        self.set_backup_status("" if backup_datetime.isValid() else "Резервная копия: ОШИБКА СОЗДАНИЯ")


    def get_current_event_index(self, source_model_index: bool = False) -> QModelIndex:
        if source_model_index:
            return map_to_source(-2, self.ui.trw_event.selectionModel().currentIndex())
        else:
            return self.ui.trw_event.selectionModel().currentIndex()

    def current_data(self, column: Col, role: int = LiabilitySqlTableModel.dbValueRole) -> Any:
        curr_index: QModelIndex = self.get_current_event_index()
        if not curr_index.isValid():
            return None
        return curr_index.siblingAtColumn(column).data(role)

    def set_data_to_event(self, index: QModelIndex, column: Col, value: Any) -> bool:
        index_source: QModelIndex = map_to_source(-2, index)
        if not index_source.isValid():
            return False
        return self.base_model.setData(index_source.siblingAtColumn(column), value)

    def set_data_to_current_event(self, column: Col, value: Any) -> bool:
        return self.set_data_to_event(self.get_current_event_index(), column, value)

    def check_event_selection_visibility(self) -> None:
        filtered_out = not bool(self.ui.trw_event.currentIndex().isValid())
        self.actions_on_selection_visibility_changed(filtered_out)

    def actions_on_selection_visibility_changed(self, filtered_out: bool) -> None:
        self.ui.act_copy.setDisabled(filtered_out)
        self.ui.act_edit.setDisabled(filtered_out)
        self.ui.act_delete.setDisabled(filtered_out)
        if filtered_out:
            self.ui.act_copydoc.setEnabled(False)
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

    def on_currentevent_change(self, current: QModelIndex = QModelIndex(), previous: QModelIndex = QModelIndex()) -> None:
        # Несохранённая заметка предыдущей строки не должна потеряться при переходе
        self.save_note(previous)
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
            # Без выделения row_type is None - кнопку добавления платежа включаем только если выбрано обязательство
            self.ui.pb_addpayment.setEnabled(row_type == RowType.LIABILITY)
        self.update_eventinfo()

    def update_eventinfo(self) -> bool:
        current_index: QModelIndex = self.get_current_event_index()
        self.set_bound_document(0)
        if not current_index.isValid():
            self.ui.stw_eventinfo.setCurrentIndex(1)
            return False
        row_type: int = current_index.siblingAtColumn(Col.TYPE).data(LiabilitySqlTableModel.dbValueRole)
        is_event_selected: bool = (row_type == RowType.LIABILITY)
        # Информационная часть отображается только для платежей
        self.ui.stw_eventinfo.setCurrentIndex(int(not is_event_selected))
        # Значения для информационной части
        if row_type == RowType.LIABILITY:
            remain_amount: Decimal = current_index.siblingAtColumn(Col.REMAINAMOUNT).data(LiabilitySqlTableModel.qtValueRole)
            self.ui.la_remainsum.setText(dec_strcommaspace(remain_amount, add_rub=True))
            self.update_contractbound_field(current_index)
            self.ui.la_createdate.setText(str(current_index.siblingAtColumn(Col.INCURRENCEDATE).data()))
            self.ui.la_paymenttype.setText(str(current_index.siblingAtColumn(Col.PAYMENTTYPE).data()).lower())
            self.ui.te_descr.setPlainText(str(current_index.siblingAtColumn(Col.DESCR).data()))
            self.ui.te_notes.setPlainText(str(current_index.siblingAtColumn(Col.NOTES).data()))
            # Сумма платежа по умолчанию равна остатку
            self.ui.dsb_paymentsum.setValue(current_index.siblingAtColumn(Col.REMAINAMOUNT).data(LiabilitySqlTableModel.qtValueRole))
            # Обновить дату платежа по умолчанию
            self.ui.de_paymentdate.setDate(QDate.currentDate())
        return True

    def set_bound_document(self, document_id: int) -> None:
        self.bound_document_id = document_id
        self.ui.act_gotocontract.setEnabled(bool(document_id))
        self.ui.act_copydoc.setEnabled(bool(document_id) and self.current_data(Col.PAYMENTTYPE) != PaymentType.REFUND)

    def update_contractbound_field(self, index: QModelIndex) -> None:
        document_id: int = index.siblingAtColumn(Col.CONTRACTDOCUMENTID).data(LiabilitySqlTableModel.qtValueRole)
        title = self.base_model.document_title(document_id) if document_id else None
        self.set_bound_document(document_id if title else 0)
        if title is None:
            self.ui.la_contractbound.setText(self.CONTRACT_NOTBOUND_TEXT)
            self.ui.la_contractbound.setToolTip("")
            return
        link_text: str = f"№ {title.contract_number} от {date_displstr(title.contract_date)}"
        if title.document_name:
            link_text += f" · {title.document_name}"
        self.ui.la_contractbound.setText(f'<a href="#document">{link_text}</a>')
        self.ui.la_contractbound.setToolTip("Открыть документ договора")

    def open_bound_document(self, _=None) -> None:
        title = self.base_model.document_title(self.bound_document_id) if self.bound_document_id else None
        if title is None:
            return
        contract = ContractInfo(contractor_id=title.contractor_id,
                                contractor_name=title.contractor_name,
                                contract_id=title.contract_id,
                                contract_number=title.contract_number,
                                contract_date=title.contract_date)
        dlg = ContractDocumentDialog(self.db_handler, self.settings_handler.settings, self.bound_document_id, contract, self)
        if dlg.exec():
            self.base_model.document_titles.clear()
            self.update_eventinfo()

    # Общий набор аргументов для set_filters, чтобы не дублировать список из 7 параметров
    def _current_filter_args(self) -> tuple:
        return (self.ui.lw_term.current_term(),
                self.ui.lw_category.current_category(),
                self.ui.le_search.text(),
                self.ui.cmb_responsiblefilter.currentData(),
                self.ui.chb_paytoday.isChecked(),
                str_int(self.settings_handler.settings.value("Common/paidloadperiod", 3), 3),
                self.ui.act_featured.isChecked())

    def update_filters_and_select(self) -> None:
        filter_args = self._current_filter_args()
        self.proxy1_model.set_filters(*filter_args)
        self.base_model.send_filterwidget_labeldata(*filter_args)
        self.ui.trw_event.span_columns()
        self.ui.pb_resetfilters.setEnabled(self.any_filter_active())

    def any_filter_active(self) -> bool:
        return (any(is_active() for *_, is_active in self.filter_sections)
                or self.ui.chb_paytoday.isChecked()
                or self.ui.act_featured.isChecked()
                or bool(self.ui.le_search.text()))

    def update_search_margin(self, _minimum: int, maximum: int) -> None:
        scrollbar_width: int = self.ui.scrollArea.verticalScrollBar().sizeHint().width() if maximum > 0 else 0
        right_margin: int = 9 + scrollbar_width
        self.ui.pb_resetfilters.setStyleSheet(
            "QPushButton {border: 1px solid #cbcbcb; padding: 3px; background-color: #f4f4f4; "
            f"margin: 9px {right_margin}px 0px 9px;}}\n"
            "QPushButton:hover {background-color: #e8eef4;}\n"
            "QPushButton:disabled {color: #6e6e6e;}")
        self.ui.horizontalLayout_search.setContentsMargins(9, 3, right_margin, 3)

    def reset_filters(self) -> None:
        blocked_widgets: tuple = (self.ui.lw_term, self.ui.lw_category,
                                  self.ui.cmb_responsiblefilter, self.ui.chb_paytoday,
                                  self.ui.le_search, self.ui.act_featured)
        for widget in blocked_widgets:
            widget.blockSignals(True)
        self.ui.lw_term.setCurrentRow(0)
        self.ui.lw_category.setCurrentRow(0)
        self.ui.cmb_responsiblefilter.setCurrentIndex(0)
        self.ui.chb_paytoday.setChecked(False)
        self.ui.le_search.clear()
        self.ui.act_featured.setChecked(False)
        for widget in blocked_widgets:
            widget.blockSignals(False)

        self.proxy1_model.set_filter(Filter.TERM, list(TermCategory)[0], invalidate=False)
        self.proxy1_model.set_filter(Filter.CATEGORY, 0, invalidate=False)
        self.proxy1_model.set_filter(Filter.PAYTODAY, False, invalidate=False)
        # Заголовки свёрнутых секций могли остаться подкрашенными как активные
        for switch_button, filter_widget, label, is_active in self.filter_sections:
            switch_button.change_style_on_hiding_activefilter(switch_button.switch_state(), is_active())
        self.update_filters_and_select()

    def check_export_availability(self) -> None:
        self.ui.act_export.setEnabled(self.proxy2_model.stored_count > 0)

    def save_note(self, index: QModelIndex | None = None) -> bool:
        note_index: QModelIndex = self.get_current_event_index() if index is None else index
        if not note_index.isValid():
            return False
        if note_index.siblingAtColumn(Col.TYPE).data(LiabilitySqlTableModel.dbValueRole) != RowType.LIABILITY:
            return False
        note_text: str = self.ui.te_notes.toPlainText()
        if note_index.siblingAtColumn(Col.NOTES).data(LiabilitySqlTableModel.dbValueRole) == note_text:
            return False
        return self.set_data_to_event(note_index, Col.NOTES, note_text)

    def make_new_payment(self) -> bool:
        date: QDate = self.ui.de_paymentdate.date()
        amount: Decimal = Decimal(str(self.ui.dsb_paymentsum.value()))

        if amount == 0:
            return False
        if (amount - self.current_data(Col.REMAINAMOUNT, LiabilitySqlTableModel.qtValueRole)) > 0.01:
            msg_box = YesNoMessagebox(f"Сумма оплаты ({dec_strcommaspace(amount)}) превышает остаток задолженности ({dec_strcommaspace(
                self.current_data(Col.REMAINAMOUNT, LiabilitySqlTableModel.qtValueRole))}). Уверены, что хотите продолжить?", self)
            if msg_box.exec() == YesNoMessagebox.NO_RETURN_VALUE:
                return False
        if date > QDate.currentDate():
            msg_box = YesNoMessagebox(f"Выбранная дата ({date_displstr(date)}) больше текущей даты. Уверены, что хотите продолжить?", self)
            if msg_box.exec() == YesNoMessagebox.NO_RETURN_VALUE:
                return False
        if self.payment_model.append_row([self.current_data(Col.ID),
                                         date_str(date),
                                         str(amount),
                                         date_str(QDate.currentDate())]):
            self.base_model.load_payment_totals()
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
        msg_box = YesNoMessagebox(f"Вы уверены, что хотите удалить запись об оплате?", self, cancel_by_default=True)
        if msg_box.exec() == YesNoMessagebox.NO_RETURN_VALUE:
            return False

        if self.payment_model.removeRow(origin_index_row):
            self.payment_model.submitAll()
            self.base_model.load_payment_totals()
            self.update_filters_and_select()
            self.update_eventinfo()
            return True
        else:
            return False

    def open_event_dialog(self, edit: bool = False, copy: bool = False, initial_amount: Decimal | None = None,
                          parent: QWidget | None = None, from_statement: bool = False,
                          payment_date: date | None = None) -> bool:
        curr_index: QModelIndex = self.get_current_event_index()

        if edit or copy:
            if not curr_index.isValid():
                self.warn_selection_lost()
                return False
            selection_not_visible: bool = is_selection_filteredout(
                self.proxy2_model, self.ui.trw_event, two_proxies=True, current_instead=True)
            if selection_not_visible:
                self.warn_selection_lost()
                return False

            is_current_paid = True if FilterFlags.PAID in curr_index.siblingAtColumn(Col.FILTERFLAGS).data(LiabilitySqlTableModel.qtValueRole) else False

        responsible_model: ResponsibleCategorySortModel = self.responsible_partial_sorted_model
        if edit or copy:
            # Модели ответственных могли не загрузиться при старте (например, сбой чтения персонала)
            if not self.responsible_partial_model:
                self.warn_personal_unavailable()
                return False
            responsible_id = curr_index.siblingAtColumn(Col.RESPONSIBLE).data(LiabilitySqlTableModel.qtValueRole)
            matches = self.responsible_partial_model.match(self.responsible_partial_model.index(0, 0), Qt.ItemDataRole.UserRole,
                                                           responsible_id, hits=1, flags=Qt.MatchFlag.MatchExactly)
            if not matches:
                responsible_model = self.responsible_full_sorted_model
        if not responsible_model:
            self.warn_personal_unavailable()
            return False

        event_dialog: EventDialog = EventDialog(final_proxy_model=self.proxy2_model, responsible_model=responsible_model, payment_model= self.payment_model,
                                                settings_handler=self.settings_handler, db_handler=self.db_handler, edit_mode=edit, copy_mode=copy, current_index=curr_index, initial_amount=initial_amount,
                                                from_statement=from_statement, payment_date=payment_date, parent=parent or self)
        if event_dialog.exec():
            if not edit:
                set_due_filter = False
                if copy:
                    if is_current_paid:
                        set_due_filter = True
                self.select_new_event(set_due_filter)
            else:
                self.base_model.load_payment_totals()
                self.update_filters_and_select()
                self.update_eventinfo()
            self.proxy1_model.invalidate()
            return True
        else:
            return False

    def select_new_event(self, set_due_filter: bool) -> None:
        self.base_model.submitAll()
        self.base_model.load_payment_totals()
        self.ui.trw_event.selectionModel().clear()
        if set_due_filter:
            self.ui.lw_term.setCurrentRow(0)
        self.update_filters_and_select()
        # ищем и выделяем новую строку
        last_id: int = self.base_model.last_inserted_id

        base_index_to_select = None
        for row in range(self.base_model.rowCount() - 1, -1, -1):
            if self.base_model.index(row, Col.ID).data(LiabilitySqlTableModel.qtValueRole) == last_id:
                base_index_to_select = self.base_model.index(row, 0)
                break
        if base_index_to_select:
            index_to_select: QModelIndex = self.proxy2_model.mapFromSource(self.proxy1_model.mapFromSource(base_index_to_select))
            if index_to_select.isValid():
                self.ui.trw_event.skip_restore_selection = True
                self.ui.trw_event.selectionModel().setCurrentIndex(index_to_select, QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows)

    def open_copydoc_dialog(self) -> bool:
        curr_index: QModelIndex = self.get_current_event_index()
        if not curr_index.isValid() or is_selection_filteredout(self.proxy2_model, self.ui.trw_event, two_proxies=True, current_instead=True):
            self.warn_selection_lost()
            return False
        title = self.base_model.document_title(self.bound_document_id) if self.bound_document_id else None
        if title is None:
            return False

        is_current_paid = FilterFlags.PAID in curr_index.siblingAtColumn(Col.FILTERFLAGS).data(LiabilitySqlTableModel.qtValueRole)
        copydoc_dialog = CopyDocDialog(final_proxy_model=self.proxy2_model, db_handler=self.db_handler, settings_handler=self.settings_handler,
                                       current_index=curr_index, title=title, parent=self)
        if not copydoc_dialog.exec():
            return False
        self.select_new_event(is_current_paid)
        self.proxy1_model.invalidate()
        return True

    def warn_selection_lost(self) -> None:
        msg = ErrorInfoMessageBox("Выбранный платеж больше не отображается в таблице - вероятно, изменились условия "
                                  "фильтрации. Выберите платеж заново.", is_info=True, parent=self)
        msg.exec()

    def warn_personal_unavailable(self) -> None:
        msg = ErrorInfoMessageBox("Не удалось получить список ответственных (подробности см. в логе). "
                                  "Проверьте настройки и файл персонала.", parent=self)
        msg.exec()

    def delete_event(self) -> bool:
        curr_index: QModelIndex = self.get_current_event_index()
        if not curr_index.isValid():
            self.warn_selection_lost()
            return False
        selection_not_visible: bool = is_selection_filteredout(self.proxy2_model, self.ui.trw_event, two_proxies=True, current_instead=True)
        if selection_not_visible:
            self.warn_selection_lost()
            return False
        msg_box = YesNoMessagebox("Удаление платежа - необратимое действие. Уверены, что хотите продолжить?",
                                  self, cancel_by_default=True)
        if msg_box.exec() == YesNoMessagebox.YES_RETURN_VALUE:
            event_id: int = self.current_data(Col.ID, LiabilitySqlTableModel.qtValueRole)
            row: int = self.proxy1_model.mapToSource(self.proxy2_model.mapToSource(curr_index)).row()
            deleted: bool = self.db_handler.run_in_transaction(
                lambda: self.db_handler.delete_payments_by_event(event_id) and self.base_model.delete_row(row) != 0)
            if not deleted:
                self.base_model.select()
                self.update_filters_and_select()
                ErrorInfoMessageBox("Не удалось удалить платеж (подробности см. в логе)", parent=self).exec()
                return False
            # Удаление строки не вызывает currentChanged
            self.on_currentevent_change()
            self.update_filters_and_select()
            return True
        return False

    def open_settings_dialog(self) -> None:
        settings_dialog: SettingsDialog = SettingsDialog(self.settings_handler, self.db_handler, self)
        settings_dialog.exec()
        self.on_currentevent_change()
        self.base_model.select()
        self.update_filters_and_select()
        self.base_model.cacheUpdateNeeded.emit()
        self.update_sync_status()

    def open_manual_dialog(self, page: str = "", owner: QWidget | None = None) -> None:
        if not ManualDialog.is_available():
            ErrorInfoMessageBox("Руководство не найдено. Переустановите программу или обратитесь к ответственному за программу",
                                parent=self).exec()
            return
        if self.manual_dialog is None:
            self.manual_dialog = ManualDialog(self.settings_handler, owner or self)
        else:
            self.manual_dialog.set_owner(owner or self)
        self.manual_dialog.show_manual(page)

    def open_fees_dialog(self, csv_path: str = "", statement_fee_totals: dict | None = None,
                         parent: QWidget | None = None) -> None:
        fees_dialog: FeeDialog = FeeDialog(self.settings_handler, self.db_handler, self.base_model, self.payment_model,
                                           parent or self, csv_path, statement_fee_totals)
        fees_dialog.exec()
        self.base_model.select()
        self.update_filters_and_select()

    def open_matching_dialog(self) -> None:
        matching_dialog: MatchingDialog = MatchingDialog(
            self.settings_handler, self.db_handler,
            lambda amount, fee_date, dialog: self.open_event_dialog(initial_amount=amount, parent=dialog, from_statement=True,
                                                                    payment_date=fee_date),
            lambda entry, new_amount, dialog: self.open_payment_amount_dialog(entry, new_amount, dialog),
            self.open_fees_dialog, self)
        matching_dialog.exec()
        self.base_model.select()
        self.payment_model.update_filter()
        self.update_filters_and_select()

    def open_payment_amount_dialog(self, entry: PaymentEntry, new_amount: Decimal | None, parent: QWidget) -> bool:
        info = self.db_handler.read_payment_info(entry.payment_id)
        if info is None:
            ErrorInfoMessageBox("Не удалось прочитать платеж для этой оплаты (подробности см. в логе)", parent=parent).exec()
            return False
        return PaymentAmountDialog(self.db_handler, info, new_amount, parent).exec() == QDialog.DialogCode.Accepted

    def open_export_dialog(self) -> bool:
        if self.proxy2_model.rowCount() == 0:
            msg = ErrorInfoMessageBox("Экспортировать нечего: в таблице нет ни одного платежа. "
                                      "Измените условия фильтрации или поиска.", is_info=True, parent=self)
            msg.exec()
            return False
        dlg: ExportDialog = ExportDialog(self.xls_writer, self.ui.trw_event.get_columnvisibility_list(), self)
        return dlg.exec() == QDialog.DialogCode.Accepted

    def open_finplan_dialog(self) -> None:
        year: int = QDate().currentDate().year()
        dlg: FinPlanDialog = FinPlanDialog(self.db_handler, self.settings_handler, year, self)
        dlg.exec()

    def open_fulfillment_dialog(self) -> None:
        dlg: FulfillmentOptionDialog = FulfillmentOptionDialog(self.db_handler, self.settings_handler, self)
        dlg.exec()

    def open_chart_dialog(self) -> None:
        self.chart_choice_dialog = ChartChoiceDialog(self)
        self.chart_choice_dialog.exec()

    def open_contractor_dialog(self) -> None:
        self.contractor_dialog = ContractorDialog(self.db_handler, self.settings_handler.settings, self)
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
        self.save_note()
        if not self.confirm_exit_with_sync():
            event.ignore()
            return
        self.settings_handler.save_settings()
        event.accept()
