import os.path
import sys
from pathlib import Path

from PySide6 import QtGui, QtCore
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QDialog, QListWidgetItem, QLineEdit, QFileDialog, QButtonGroup
from PySide6.QtCore import Qt, QSize

from base.casting import str_bool
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.eventtablemodel import RowFormatting
from gui.recoverydialog import RecoveryDialog
from gui.settings import SettingsHandler
from gui.ui.settingsdialog_ui import Ui_settingsdialog


class SettingsDialog(QDialog):

    AUTOSAVE_SET = {
        0: 5,
        1: 15,
        2: 30,
        3: 60,
        4: 180,
    }

    CLEANBACKUP_SET = {
        0: 7,
        1: 30,
        2: 180,
        3: 9999,
    }

    LOADPAID_SET = {
        0: 1,
        1: 3,
        2: 6,
        3: 12,
        4: 999,
    }

    def __init__(self, settings_handler: SettingsHandler, reject_possible: bool = True, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.ui = Ui_settingsdialog()
        self.ui.setupUi(self)

        self.settings_handler: SettingsHandler = settings_handler
        self.settings_handler.save_settings()
        self.autosave_needed: bool = False

        self.ui.lw_menu.setIconSize(QSize(30, 30))
        self.ui.pb_cancel.setEnabled(reject_possible)
        if not reject_possible:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowType.CustomizeWindowHint)
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowType.WindowCloseButtonHint)

        # Центрирование элементов списка меню
        for row in range(self.ui.lw_menu.count()):
            self.ui.lw_menu.item(row).setSizeHint(QSize(128, 40))
            self.ui.lw_menu.item(row).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Группы кнопок
        self.rbg_fontsize: QButtonGroup = QButtonGroup()
        self.rbg_fontsize.addButton(self.ui.rb_fontsize_1, 0)
        self.rbg_fontsize.addButton(self.ui.rb_fontsize_2, 1)
        self.rbg_fontsize.addButton(self.ui.rb_fontsize_3, 2)

        # Заполнение комбобоксов
        for autosave_option in self.AUTOSAVE_SET.items():
            self.ui.cmb_autosave.setItemData(autosave_option[0], autosave_option[1], Qt.ItemDataRole.UserRole)
        for loadpaid_option in self.LOADPAID_SET.items():
            self.ui.cmb_loadpaid.setItemData(loadpaid_option[0], loadpaid_option[1], Qt.ItemDataRole.UserRole)
        for cleanbackup_option in self.CLEANBACKUP_SET.items():
            self.ui.cmb_backupautodelete.setItemData(cleanbackup_option[0], cleanbackup_option[1], Qt.ItemDataRole.UserRole)

        # Сигналы
        self.ui.pb_ok.clicked.connect(self.accept)
        self.ui.pb_cancel.clicked.connect(self.reject)
        self.ui.lw_menu.currentItemChanged.connect(self.change_stw_page)
        self.ui.pb_exportpath.clicked.connect(lambda: self.change_path(self.ui.le_exportpath))
        self.ui.pb_backuppath.clicked.connect(lambda: self.change_path(self.ui.le_backuppath))
        self.ui.pb_restorefrombackup.clicked.connect(self.restore_backup)

        # Выбор первого пункта меню и косметика выбора
        palette: QPalette = self.ui.lw_menu.palette()
        palette.setColor(QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Highlight,
                         palette.color(QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Highlight))
        palette.setColor(QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.HighlightedText,
                         palette.color(QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.HighlightedText))
        self.ui.lw_menu.setPalette(palette)
        self.ui.lw_menu.setCurrentRow(0)

        self.load_settings_values()

    def accept(self):
        if not self.ui.le_backuppath.text() or not Path(self.ui.le_backuppath.text()).is_dir():
            msg_box: ErrorInfoMessageBox = ErrorInfoMessageBox("Папка для резервного копирования не указана или указана неверно")
            msg_box.exec()
            return
        self.save_settings_values()
        self.settings_handler.apply_settings(self.autosave_needed)
        QDialog.accept(self)

    def change_path(self, le_widget: QLineEdit) -> None:
        path: str = QFileDialog.getExistingDirectory(self, "Выберите папку", le_widget.text())
        if path:
            le_widget.setText(path)

    def load_settings_values(self) -> None:
        # Основные
        ## Отображение оплаченных
        self.ui.cmb_loadpaid.setCurrentIndex(1)
        try:
            for loadpaid_option in self.LOADPAID_SET.items():
                if int(self.settings_handler.settings.value("Common/paidloadperiod")) == loadpaid_option[1]:
                    self.ui.cmb_loadpaid.setCurrentIndex(loadpaid_option[0])
        except ValueError, TypeError:
            pass
        ## Размер шрифта
        try:
            self.rbg_fontsize.button(int(self.settings_handler.settings.value("Appearance/fontsize", 0))).setChecked(True)
        except TypeError:
            self.rbg_fontsize.button(0).setChecked(True)
        # Таблица
        ## Отображаемые столбцы
        self.ui.chb_dataintable_totalamount.setChecked(bool(int(self.settings_handler.settings.value("Columns/totalamount", 1))))
        self.ui.chb_dataintable_paymenttype.setChecked(bool(int(self.settings_handler.settings.value("Columns/paymenttype", 1))))
        self.ui.chb_dataintable_descr.setChecked(bool(int(self.settings_handler.settings.value("Columns/descr", 1))))
        self.ui.chb_dataintable_responsible.setChecked(bool(int(self.settings_handler.settings.value("Columns/responsible", 1))))
        ## Информационная панель
        self.ui.chb_datainfo_totalamount.setChecked(bool(int(self.settings_handler.settings.value("Infopanel/totalamount", 1))))
        self.ui.chb_datainfo_percentage.setChecked(bool(int(self.settings_handler.settings.value("Infopanel/percentage", 1))))
        self.ui.chb_datainfo_createdate.setChecked(bool(int(self.settings_handler.settings.value("Infopanel/createdate", 1))))
        self.ui.chb_datainfo_paymenttype.setChecked(bool(int(self.settings_handler.settings.value("Infopanel/paymenttype", 1))))
        self.ui.chb_datainfo_descr.setChecked(bool(int(self.settings_handler.settings.value("Infopanel/descr", 1))))
        self.ui.chb_datainfo_responsible.setChecked(bool(int(self.settings_handler.settings.value("Infopanel/responsible", 1))))
        ## Настройки экспорта
        self.ui.chb_frozenheader.setChecked(bool(int(self.settings_handler.settings.value("Export/frozenheader", 1))))
        self.ui.le_exportpath.setText(self.settings_handler.settings.value("Export/path", os.getcwd()))
        ## Форматирование строк
        self.ui.chb_verticalgrid.setChecked(str_bool(self.settings_handler.settings.value("Tableformat/verticalgrid"), RowFormatting().vertical_grid))
        self.ui.chb_zebrastyle.setChecked(str_bool(self.settings_handler.settings.value("Tableformat/zebrastyle"), RowFormatting().zebra_style))
        self.ui.pb_backgrounddue.set_color(self.settings_handler.settings.value("Tableformat/backgrounddue", RowFormatting().due_backcolor))
        self.ui.pb_backgroundtoday.set_color(self.settings_handler.settings.value("Tableformat/backgroundtoday", RowFormatting().today_backcolor))
        self.ui.pb_foregrounddue.set_color(self.settings_handler.settings.value("Tableformat/foregrounddue", RowFormatting().due_forecolor))
        self.ui.pb_foregroundtoday.set_color(self.settings_handler.settings.value("Tableformat/foregroundtoday", RowFormatting().today_forecolor))
        self.ui.chb_formatbolddue.setChecked(str_bool(self.settings_handler.settings.value("Tableformat/boldforegrounddue", RowFormatting().due_textbold)))
        self.ui.chb_formatboldtoday.setChecked(str_bool(self.settings_handler.settings.value("Tableformat/boldforegroundtoday", RowFormatting().today_textbold)))
        self.ui.chb_formatboldheader.setChecked(str_bool(self.settings_handler.settings.value("Tableformat/boldforegroundheader", RowFormatting().header_textbold)))
        self.ui.pb_foregroundsectionheader.set_color(self.settings_handler.settings.value("Tableformat/foregroundsectionheader", RowFormatting().header_section_forecolor))
        self.ui.pb_backgroundsectionheader.set_color(self.settings_handler.settings.value("Tableformat/backgroundsectionheader", RowFormatting().header_section_backcolor))
        self.ui.pb_foregroundsubsectionheader.set_color(self.settings_handler.settings.value("Tableformat/foregroundsubsectionheader", RowFormatting().header_subsection_forecolor))
        self.ui.pb_backgroundsubsectionheader.set_color(self.settings_handler.settings.value("Tableformat/backgroundsubsectionheader", RowFormatting().header_subsection_backcolor))
        self.ui.chb_formatboldfooter.setChecked(bool(int(self.settings_handler.settings.value("Tableformat/boldforegroundfooter", RowFormatting().footer_textbold))))
        self.ui.pb_foregroundsectionfooter.set_color(self.settings_handler.settings.value("Tableformat/foregroundsectionfooter", RowFormatting().footer_section_forecolor))
        self.ui.pb_backgroundsectionfooter.set_color(self.settings_handler.settings.value("Tableformat/backgroundsectionfooter", RowFormatting().footer_section_backcolor))
        self.ui.pb_foregroundsubsectionfooter.set_color(self.settings_handler.settings.value("Tableformat/foregroundsubsectionfooter", RowFormatting().footer_subsection_forecolor))
        self.ui.pb_backgroundsubsectionfooter.set_color(self.settings_handler.settings.value("Tableformat/backgroundsubsectionfooter", RowFormatting().footer_subsection_backcolor))
        # Хранение
        self.ui.cmb_autosave.setCurrentIndex(1)
        try:
            probable_setting: int = int(self.settings_handler.settings.value("Autosave/interval"))
            for autosave_option in self.AUTOSAVE_SET.items():
                if probable_setting == autosave_option[1]:
                    self.ui.cmb_autosave.itemData(self.ui.cmb_autosave.setCurrentIndex(autosave_option[0]))
        except TypeError, ValueError:
            pass
        self.ui.cmb_autosave.currentIndexChanged.connect(lambda: setattr(self, "autosave_needed", True))  # Установка сигнала на изменение после выбора
        self.ui.cmb_backupautodelete.setCurrentIndex(0)
        try:
            for cleanbackup_option in self.CLEANBACKUP_SET.items():
                if int(self.settings_handler.settings.value("Backup/cleanupperiod")) == cleanbackup_option[1]:
                    self.ui.cmb_backupautodelete.setCurrentIndex(cleanbackup_option[0])
        except ValueError, TypeError:
            pass
        self.ui.le_backuppath.setText(self.settings_handler.settings.value("Backup/path", ""))

    def save_settings_values(self) -> None:
        # Отображение
        ## Отображение оплаченных
        self.settings_handler.settings.setValue("Common/paidloadperiod", self.ui.cmb_loadpaid.currentData())
        ## Размер шрифта
        self.settings_handler.settings.setValue("Appearance/fontsize", self.rbg_fontsize.checkedId())
        # Таблица
        ## Отображаемые столбцы
        self.settings_handler.settings.setValue("Columns/totalamount", int(self.ui.chb_dataintable_totalamount.isChecked()))
        self.settings_handler.settings.setValue("Columns/paymenttype", int(self.ui.chb_dataintable_paymenttype.isChecked()))
        self.settings_handler.settings.setValue("Columns/descr", int(self.ui.chb_dataintable_descr.isChecked()))
        self.settings_handler.settings.setValue("Columns/responsible", int(self.ui.chb_dataintable_responsible.isChecked()))
        ## Данные в информационной панели
        self.settings_handler.settings.setValue("Infopanel/totalamount", int(self.ui.chb_datainfo_totalamount.isChecked()))
        self.settings_handler.settings.setValue("Infopanel/percentage", int(self.ui.chb_datainfo_percentage.isChecked()))
        self.settings_handler.settings.setValue("Infopanel/createdate", int(self.ui.chb_datainfo_createdate.isChecked()))
        self.settings_handler.settings.setValue("Infopanel/paymenttype", int(self.ui.chb_datainfo_paymenttype.isChecked()))
        self.settings_handler.settings.setValue("Infopanel/descr", int(self.ui.chb_datainfo_descr.isChecked()))
        self.settings_handler.settings.setValue("Infopanel/responsible", int(self.ui.chb_datainfo_responsible.isChecked()))
        ## Настройки экспорта
        self.settings_handler.settings.setValue("Export/frozenheader", int(self.ui.chb_frozenheader.isChecked()))
        self.settings_handler.settings.setValue("Export/path", self.ui.le_exportpath.text())
        ## Форматирование строк
        self.settings_handler.settings.setValue("Tableformat/verticalgrid", int(self.ui.chb_verticalgrid.isChecked()))
        self.settings_handler.settings.setValue("Tableformat/zebrastyle", int(self.ui.chb_zebrastyle.isChecked()))
        self.settings_handler.settings.setValue("Tableformat/backgrounddue", self.ui.pb_backgrounddue.get_color())
        self.settings_handler.settings.setValue("Tableformat/backgroundtoday", self.ui.pb_backgroundtoday.get_color())
        self.settings_handler.settings.setValue("Tableformat/foregrounddue", self.ui.pb_foregrounddue.get_color())
        self.settings_handler.settings.setValue("Tableformat/foregroundtoday", self.ui.pb_foregroundtoday.get_color())
        self.settings_handler.settings.setValue("Tableformat/boldforegrounddue", int(self.ui.chb_formatbolddue.isChecked()))
        self.settings_handler.settings.setValue("Tableformat/boldforegroundtoday", int(self.ui.chb_formatboldtoday.isChecked()))
        self.settings_handler.settings.setValue("Tableformat/boldforegroundheader", int(self.ui.chb_formatboldheader.isChecked()))
        self.settings_handler.settings.setValue("Tableformat/foregroundsectionheader", self.ui.pb_foregroundsectionheader.get_color())
        self.settings_handler.settings.setValue("Tableformat/backgroundsectionheader", self.ui.pb_backgroundsectionheader.get_color())
        self.settings_handler.settings.setValue("Tableformat/foregroundsubsectionheader", self.ui.pb_foregroundsubsectionheader.get_color())
        self.settings_handler.settings.setValue("Tableformat/backgroundsubsectionheader", self.ui.pb_backgroundsubsectionheader.get_color())
        self.settings_handler.settings.setValue("Tableformat/boldforegroundfooter", int(self.ui.chb_formatboldfooter.isChecked()))
        self.settings_handler.settings.setValue("Tableformat/foregroundsectionfooter", self.ui.pb_foregroundsectionfooter.get_color())
        self.settings_handler.settings.setValue("Tableformat/backgroundsectionfooter", self.ui.pb_backgroundsectionfooter.get_color())
        self.settings_handler.settings.setValue("Tableformat/foregroundsubsectionfooter", self.ui.pb_foregroundsubsectionfooter.get_color())
        self.settings_handler.settings.setValue("Tableformat/backgroundsubsectionfooter", self.ui.pb_backgroundsubsectionfooter.get_color())
        # Хранение
        self.settings_handler.settings.setValue("Autosave/interval", self.ui.cmb_autosave.currentData(Qt.ItemDataRole.UserRole))
        self.settings_handler.settings.setValue("Backup/cleanupperiod", self.ui.cmb_backupautodelete.currentData(Qt.ItemDataRole.UserRole))
        self.settings_handler.settings.setValue("Backup/path", self.ui.le_backuppath.text())
        self.settings_handler.settings.sync()

    def change_stw_page(self, current_item: QListWidgetItem, previous_item: QListWidgetItem) -> None:
        self.ui.stw.setCurrentIndex(self.ui.lw_menu.row(current_item))

    def restore_backup(self) -> None:
        dlg = RecoveryDialog(self.settings_handler, self.parent().db_handler,
                             "Обратите внимание, что данные текущей сессии будут заменены выбранными и в результате полностью\n"
                             "утрачены (в случае успешного резервного копирования при запуске приложения будет доступно их\n"
                             "восстановление в контрольной точке, соответствующей запуску приложения)", True, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.parent().nosave_exit = True
            msg_box: ErrorInfoMessageBox = ErrorInfoMessageBox("Приложение будет перезапущено", is_info=True, parent=self)
            msg_box.exec()
            QtCore.QCoreApplication.quit()
            QtCore.QProcess.startDetached(sys.executable, sys.argv)
