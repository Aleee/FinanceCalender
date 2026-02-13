from enum import IntEnum

from PySide6 import QtWidgets
from PySide6.QtCore import QSettings, QDir, QDate, QSize, QPoint, QCoreApplication
from PySide6.QtWidgets import QApplication

from base.casting import str_bool
from base.event import EventField
from gui.eventtablemodel import RowFormatting


class FontSize(IntEnum):
    SMALL = 9
    MEDIUM = 11
    LARGE = 13


class SettingsHandler:

    def __init__(self, main_window):
        settings_file: str = QDir.currentPath() + "/settings.ini"
        self.settings: QSettings = QSettings(settings_file, QSettings.Format.IniFormat)

        self.mw = main_window
        self.app: QCoreApplication = QApplication.instance()

    def apply_settings(self, autosave_needed: bool = False) -> None:
        # Отключение фильтра на время применения настроек
        self.mw.ui.trw_event.model().sourceModel().enable_sortfilter(False)

        # Основные настройки
        ## Отображение оплаченных
        try:
            self.mw.event_model.paid_minimum_date = QDate().currentDate().addDays(-30 * int(self.settings.value("Common/paidloadperiod")))
        except (ValueError, TypeError):
            self.mw.event_model.paid_minimum_date = QDate().currentDate().addDays(-30 * 999)
        ## Размер шрифта
        self.change_fontsize()
        ## Ширина столбцов
        columnwidth_data: str = self.settings.value("Appearance/columnwidth")
        try:
            columnwidth_listdata: list = list(map(int, columnwidth_data.split()))
            for index, width in enumerate(columnwidth_listdata):
                self.mw.ui.trw_event.setColumnWidth(index, width)
        except (AttributeError, ValueError, TypeError):
            for col, width in self.mw.ui.trw_event.DEFAULT_COLUMN_WIDTH.items():
                self.mw.ui.trw_event.setColumnWidth(col, width)
        ## Геометрия окна
        self.mw.resize(self.settings.value("Mainwindow/size", QSize(1300, 750)))
        self.mw.move(self.settings.value("Mainwindow/pos", QPoint(50, 50)))
        if str_bool(self.settings.value("Mainwindow/fullscreen", "0")):
            self.mw.showMaximized()

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
            ("Columns/totalamount", EventField.TOTALAMOUNT),
            ("Columns/paymenttype", EventField.PAYMENTTYPE),
            ("Columns/descr", EventField.DESCR),
            ("Columns/responsible", EventField.RESPONSIBLE),
        ):
            try:
                if not bool(int(self.settings.value(column_state_settings[0]))):
                    hidden_columns.append(column_state_settings[1])
            except (ValueError, TypeError):
                pass
        self.mw.ui.trw_event.set_columns_visibility(hidden_columns)
        # Скрытие полей в информационной панели
        setting_value = str_bool(self.settings.value("Infopanel/totalamount"), True)
        for widget in (self.mw.ui.la_totalsum, self.mw.ui.tla_totalsum):
            widget.setVisible(setting_value)
        self.mw.ui.ln_totalsum.setVisible(setting_value and str_bool(self.settings.value("Infopanel/percentage"), True))
        spacer_width: int = 15 if setting_value else 0
        self.mw.ui.hs_totalsum.changeSize(spacer_width, 10, QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
        for widget in (self.mw.ui.la_percentage, self.mw.ui.tla_percentage):
            widget.setVisible(str_bool(self.settings.value("Infopanel/percentage"), True))
        setting_value = str_bool(self.settings.value("Infopanel/paymenttype"), True)
        for widget in (self.mw.ui.la_paymenttype, self.mw.ui.tla_paymenttype):
            widget.setVisible(setting_value)
        self.mw.ui.ln_paymenttype.setVisible(setting_value and str_bool(self.settings.value("Infopanel/createdate"), True))
        spacer_width: int = 10 if setting_value else 0
        self.mw.ui.hs_paymenttype.changeSize(spacer_width, 10, QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
        for widget in (self.mw.ui.la_createdate, self.mw.ui.tla_createdate):
            widget.setVisible(str_bool(self.settings.value("Infopanel/createdate"), True))
        for widget in (self.mw.ui.la_responsible, self.mw.ui.tla_responsible):
            widget.setVisible(str_bool(self.settings.value("Infopanel/responsible"), True))
        for widget in (self.mw.ui.te_descr, self.mw.ui.tla_descr):
            widget.setVisible(str_bool(self.settings.value("Infopanel/descr"), True))

        ## Форматирование строк
        if not self.mw.event_model.set_row_formatting(RowFormatting(
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
                str_bool(self.settings.value("Tableformat/zebrastyle")),
                )):
            self.mw.event_model.set_row_formatting(RowFormatting())

        ## Отображение заголовков/футеров
        try:
            self.mw.ui.act_toggleheaders.setChecked(bool(int(self.settings.value("Appearance/headersenabled"))))
        except (ValueError, TypeError):
            self.mw.ui.act_toggleheaders.setChecked(False)
        try:
            self.mw.ui.act_togglefooters.setChecked(bool(int(self.settings.value("Appearance/footersenabled"))))
        except (ValueError, TypeError):
            self.mw.ui.act_togglefooters.setChecked(False)

        ## Обновление таймера автосохранения
        if autosave_needed:
            self.mw.autosave()
            self.mw.update_autosave_timer()

        ## Включение фильтра после применения настроек
        self.mw.ui.trw_event.model().sourceModel().enable_sortfilter(True)
        ## Обновление статистики и сортировки
        self.mw.event_model.recalculate_stats()
        ## Обновить отрисовку
        self.mw.ui.trw_event.viewport().update()

    def change_fontsize(self) -> None:
        font_sizes: tuple = (FontSize.SMALL, FontSize.MEDIUM, FontSize.LARGE)
        setting_value: int = int(self.settings.value("Appearance/fontsize", 0))
        self.app.setStyleSheet(f"QWidget {{ font-size: {font_sizes[setting_value]}pt;}}")

        # Установка ширины некоторых виджетов вручную
        forced_size = {
            self.mw.ui.wdg_eventfilter: (200, 245, 270),
            self.mw.ui.wdg_eventinfo: (300, 360, 410),
            self.mw.ui.tv_payment: (190, 210, 230),}
        for option in forced_size.items():
            widget, width = option[0], option[1][setting_value]
            widget.setFixedWidth(width)

        # Виджеты с самостоятельной регулировкой
        for filterwdg in (self.mw.ui.lw_term, self.mw.ui.lw_category):
            filterwdg.update_height()
        self.mw.ui.tv_payment.update_column_width(setting_value)
        self.mw.update_plot_area()

        # Исключения
        for widget in (self.mw.la_autosavestatus, self.mw.la_backupstatus, self.mw.la_autosavebackup):
           widget.setStyleSheet(f"QWidget {{ font-size: {font_sizes[0]}pt;}}")

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
        ## Геометрия
        self.settings.setValue("Mainwindow/size", self.mw.size())
        self.settings.setValue("Mainwindow/pos", self.mw.pos())
        self.settings.setValue("Mainwindow/fullscreen", int(self.mw.isMaximized()))
