import getpass
import sys
from enum import IntEnum

import lovely_logger as log

from PySide6.QtCore import QSettings, QDir, QSize, QPoint, QRect, QCoreApplication
from PySide6.QtWidgets import QApplication, QWidget

from base.casting import str_bool, str_int
from base.paths import settings_path, backup_dir, to_stored_path, from_stored_path
from gui.eventsqlmodel import Col, RowFormatting


class FontSize(IntEnum):
    SMALL = 9
    MEDIUM = 11
    LARGE = 13


class SettingsHandler:

    def __init__(self, main_window):
        self.settings: QSettings = QSettings(settings_path(), QSettings.Format.IniFormat)

        self.mw = main_window
        self.app: QCoreApplication = QApplication.instance()

    def backup_path(self) -> str:
        stored_path: str = self.settings.value("Backup/path", "")
        return from_stored_path(stored_path) if stored_path else backup_dir()

    def set_backup_path(self, path: str) -> None:
        self.settings.setValue("Backup/path", to_stored_path(path))

    def sync_enabled(self) -> bool:
        return str_bool(self.settings.value("Sync/enabled"), False)

    def sync_channel_type(self) -> str:
        channel_type: str = self.settings.value("Sync/channel", "folder")
        return channel_type if channel_type in ("yandex", "folder") else "folder"

    def sync_token(self) -> str:
        return self.settings.value("Sync/token", "") or ""

    def sync_disk_folder(self) -> str:
        return self.settings.value("Sync/diskfolder", "") or "app:/"

    def sync_token_expires(self) -> str:
        return self.settings.value("Sync/tokenexpires", "") or ""

    def sync_folder(self) -> str:
        return from_stored_path(self.settings.value("Sync/folder", ""))

    def set_sync_folder(self, path: str) -> None:
        self.settings.setValue("Sync/folder", to_stored_path(path))

    def sync_author(self) -> str:
        return self.settings.value("Sync/author", "") or getpass.getuser()

    def sync_interval_minutes(self) -> int:
        return str_int(self.settings.value("Sync/interval"), 30)

    def sync_backup_keep_days(self) -> int:
        return str_int(self.settings.value("Sync/backupkeepdays"), 30)

    def paid_load_months(self) -> int:
        return str_int(self.settings.value("Common/paidloadperiod"), 999)

    def apply_settings(self, apply_geometry: bool = False) -> None:
        # Отключение фильтра на время применения настроек
        self.mw.ui.trw_event.model().sourceModel().enable_sortfilter(False)

        # Основные настройки
        ## Отображение оплаченных
        self.mw.base_model.set_paid_load_months(self.paid_load_months())
        ## Размер шрифта
        self.change_fontsize()
        ## Ширина столбцов
        columnwidth_data: str = self.settings.value("Appearance/columnwidth")
        try:
            columnwidth_listdata: list = list(map(int, columnwidth_data.split()))
        except (AttributeError, ValueError, TypeError):
            log.w(f"Не удалось прочитать сохранённую ширину столбцов из настроек: {columnwidth_data!r}")
            columnwidth_listdata = []
        for col, default_width in self.mw.ui.trw_event.DEFAULT_COLUMN_WIDTH.items():
            width = columnwidth_listdata[col] if col < len(columnwidth_listdata) else default_width
            self.mw.ui.trw_event.setColumnWidth(col, width)
        ## Геометрия окна
        if apply_geometry:
            self.mw.setGeometry(QRect(self.settings.value("Mainwindow/pos", QPoint(50, 50)),
                                      self.settings.value("Mainwindow/size", QSize(1300, 750))))
            window_state: int = str_int(self.settings.value("Mainwindow/fullscreen", 0))
            if window_state == 2:
                self.mw.showFullScreen()
            elif window_state == 1:
                self.mw.showMaximized()
        ## Положение разделителей
        for splitter, setting_key, default_sizes in (
                (self.mw.ui.spl_main, "Mainwindow/splittermain", (200, 1100)),
                (self.mw.ui.spl_workarea, "Mainwindow/splitterworkarea", (400, 320)),
        ):
            saved_state = self.settings.value(setting_key)
            if not (saved_state and splitter.restoreState(saved_state)):
                splitter.setSizes(default_sizes)

        # Интерфейс
        ## Состояние боковой панели
        self.mw.ui.spb_term.set_switch_state(str_bool(self.settings.value("Sidepanel/termfilter"), True))
        self.mw.ui.spb_category.set_switch_state(str_bool(self.settings.value("Sidepanel/categoryfilter"), True))
        self.mw.ui.spb_receiver.set_switch_state(str_bool(self.settings.value("Sidepanel/receiverfilter"), False))
        self.mw.ui.spb_responsible.set_switch_state(str_bool(self.settings.value("Sidepanel/responsiblefilter"), False))

        # Таблица
        ## Скрытие и отображение столбцов
        hidden_columns: list = []
        for column_state_settings in (
            ("Columns/totalamount", Col.TOTALAMOUNT),
            ("Columns/paymenttype", Col.PAYMENTTYPE),
            ("Columns/descr", Col.DESCR),
            ("Columns/responsible", Col.RESPONSIBLE),
            ("Columns/createdate", Col.INCURRENCEDATE),
        ):
            if not str_bool(self.settings.value(column_state_settings[0]), True):
                hidden_columns.append(column_state_settings[1])
        self.mw.ui.trw_event.hide_columns(hidden_columns)

        ## Форматирование строк
        if not self.mw.base_model.set_row_formatting(RowFormatting(
                str_bool(self.settings.value("Tableformat/boldforegrounddue")),
                str_bool(self.settings.value("Tableformat/boldforegroundtoday")),
                self.settings.value("Tableformat/foregrounddue"),
                self.settings.value("Tableformat/foregroundtoday"),
                self.settings.value("Tableformat/backgrounddue"),
                self.settings.value("Tableformat/backgroundtoday"),

                str_bool(self.settings.value("Tableformat/boldforegroundheader")),
                self.settings.value("Tableformat/foregroundsectionheader"),
                self.settings.value("Tableformat/backgroundsectionheader"),
                self.settings.value("Tableformat/foregroundsubsectionheader"),
                self.settings.value("Tableformat/backgroundsubsectionheader"),

                str_bool(self.settings.value("Tableformat/boldforegroundfooter")),
                self.settings.value("Tableformat/foregroundsectionfooter"),
                self.settings.value("Tableformat/backgroundsectionfooter"),
                self.settings.value("Tableformat/foregroundsubsectionfooter"),
                self.settings.value("Tableformat/backgroundsubsectionfooter"),

                str_bool(self.settings.value("Tableformat/verticalgrid")),
                )):
            self.mw.base_model.set_row_formatting(RowFormatting())

        ## Отображение заголовков/футеров
        self.mw.ui.act_toggleheaders.setChecked(str_bool(self.settings.value("Appearance/headersenabled"), False))
        self.mw.ui.act_togglefooters.setChecked(str_bool(self.settings.value("Appearance/footersenabled"), False))

        ## Перезагрузить список персонала
        self.mw.update_responsible_models(update_widgets=True)

        ## Включение фильтра после применения настроек
        self.mw.ui.trw_event.model().sourceModel().enable_sortfilter(True)
        ## Обновление статистики и сортировки
        self.mw.update_filters_and_select()
        ## Обновить отрисовку
        self.mw.ui.trw_event.viewport().update()

        ## При запуске переводим окно настроек на первую страницу
        self.settings.setValue("SettingsDialog/lastpage", 0)

    def change_fontsize(self) -> None:
        font_sizes: tuple = (FontSize.SMALL, FontSize.MEDIUM, FontSize.LARGE)
        setting_value: int = min(max(str_int(self.settings.value("Appearance/fontsize", 0)), 0), len(font_sizes) - 1)

        exclusions: tuple[QWidget] = ()
        saved_stylesheets: dict = {}

        # Сохранение значений исключений
        for widget in exclusions:
            saved_stylesheets[widget] = widget.styleSheet()

        font_size: int = font_sizes[setting_value]
        if sys.platform == "darwin":
            font_size = round(font_size * 96 / 72)
        self.app.setStyleSheet(f"QWidget {{ font-size: {font_size}pt;}}")

        # Установка ширины некоторых виджетов вручную
        forced_size = {
            self.mw.ui.wdg_eventinfo: (350, 410, 470),
            self.mw.ui.tv_payment: (190, 210, 230),
        }
        for option in forced_size.items():
            widget, width = option[0], option[1][setting_value]
            widget.setFixedWidth(width)
        # Боковая панель только ограничивается снизу - её ширину пользователь задаёт разделителем
        self.mw.ui.wdg_eventfilter.setMinimumWidth((200, 245, 270)[setting_value])

        # Виджеты с самостоятельной регулировкой
        for filterwdg in (self.mw.ui.lw_term, self.mw.ui.lw_category):
            filterwdg.update_height()
        self.mw.ui.tv_payment.update_column_width(setting_value)
        # Включить после возвращения графиков
        # self.mw.update_plot_area()

        # Вернуть исключениям свои стили
        for widget in exclusions:
            widget.setStyleSheet(saved_stylesheets[widget])

    def save_settings(self) -> None:
        # Отображение
        ## Ширина столбцов
        column_widths: list = []
        for col in range(self.mw.ui.trw_event.model().columnCount()):
            column_widths.append(str(self.mw.ui.trw_event.columnWidth(col)))
        sep: str = " "
        self.settings.setValue("Appearance/columnwidth", sep.join(column_widths))
        ## Отображение разделов/подразделов
        self.settings.setValue("Appearance/headersenabled", int(self.mw.ui.act_toggleheaders.isChecked()))
        self.settings.setValue("Appearance/footersenabled", int(self.mw.ui.act_togglefooters.isChecked()))

        # Интерфейс
        ## Состояние боковой панели
        self.settings.setValue("Sidepanel/termfilter", int(self.mw.ui.spb_term.switch_state()))
        self.settings.setValue("Sidepanel/categoryfilter", int(self.mw.ui.spb_category.switch_state()))
        self.settings.setValue("Sidepanel/receiverfilter", int(self.mw.ui.spb_receiver.switch_state()))
        self.settings.setValue("Sidepanel/responsiblefilter", int(self.mw.ui.spb_responsible.switch_state()))
        ## Положение разделителей
        self.settings.setValue("Mainwindow/splittermain", self.mw.ui.spl_main.saveState())
        self.settings.setValue("Mainwindow/splitterworkarea", self.mw.ui.spl_workarea.saveState())
        ## Геометрия
        normal_geometry: QRect = self.mw.normalGeometry()
        if not normal_geometry.isValid():
            normal_geometry = self.mw.geometry()
        self.settings.setValue("Mainwindow/size", normal_geometry.size())
        self.settings.setValue("Mainwindow/pos", normal_geometry.topLeft())
        window_state: int = 2 if self.mw.isFullScreen() else int(self.mw.isMaximized())
        self.settings.setValue("Mainwindow/fullscreen", window_state)
