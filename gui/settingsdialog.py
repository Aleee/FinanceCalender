import os.path
import sys
from pathlib import Path

from PySide6 import QtGui, QtCore
from PySide6.QtGui import QPalette, QRegularExpressionValidator
from PySide6.QtWidgets import QDialog, QListWidgetItem, QLineEdit, QFileDialog, QButtonGroup
from PySide6.QtCore import Qt, QSize, QRegularExpression

from base.backup import restore_backup
from base.casting import str_bool
from base.dbhandler import DBHandler
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.eventsqlmodel import RowFormatting
from gui.recoverydialog import RecoveryDialog
from gui.settings import SettingsHandler
from gui.ui.settingsdialog_ui import Ui_settingsdialog


DEF_ROW_PERIOD: int = 1
DEF_ROW_TRANSACTIONSTART: int = 9
DEF_TRANSACTION_CODE: int = 6
DEF_COLUMNSTOPARSE: str = "0,2,5,6,7,9"


class SettingsDialog(QDialog):

    MENU_PAGES = {
        0: 1,
        1: 2,
        2: 3,
        3: 0,
    }

    CLEANBACKUP_SET = {
        0: 30,
        1: 180,
        2: 9999,
    }

    LOADPAID_SET = {
        0: 3,
        1: 6,
        2: 12,
        3: 999,
    }

    def __init__(self, settings_handler: SettingsHandler, db_handler: DBHandler, reject_possible: bool = True, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.ui = Ui_settingsdialog()
        self.ui.setupUi(self)

        self.settings_handler: SettingsHandler = settings_handler
        self.settings_handler.save_settings()
        self.db_handler = db_handler

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
        for loadpaid_option in self.LOADPAID_SET.items():
            self.ui.cmb_loadpaid.setItemData(loadpaid_option[0], loadpaid_option[1], Qt.ItemDataRole.UserRole)
        for cleanbackup_option in self.CLEANBACKUP_SET.items():
            self.ui.cmb_backupautodelete.setItemData(cleanbackup_option[0], cleanbackup_option[1], Qt.ItemDataRole.UserRole)

        # Валидаторы
        reg_unp = QRegularExpression(r"^(\d{9}(,\s?\d{9})*)?$")
        validator_unp = QRegularExpressionValidator(reg_unp)
        self.ui.le_csv_unp.setValidator(validator_unp)

        # Сигналы
        self.ui.pb_ok.clicked.connect(self.accept)
        self.ui.pb_cancel.clicked.connect(self.reject)
        self.ui.lw_menu.currentItemChanged.connect(self.change_stw_page)
        self.ui.pb_backuppath.clicked.connect(lambda: self.change_path(self.ui.le_backuppath))
        self.ui.pb_restorefrombackup.clicked.connect(self.request_restore_backup)

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
            ErrorInfoMessageBox("Папка для резервного копирования не указана или указана неверно").exec()
            return
        if not self.ui.le_csv_unp.hasAcceptableInput():
            ErrorInfoMessageBox("Поле с перечнем известных УНП заполнено неверно (разрешены только девятизначные УНП через запятую)").exec()
            return

        self.save_settings_values()
        self.settings_handler.apply_settings()
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
        self.ui.chb_dataintable_createdate.setChecked(bool(int(self.settings_handler.settings.value("Columns/createdate", 1))))
        ## Информационная панель
        self.ui.chb_datainfo_totalamount.setChecked(bool(int(self.settings_handler.settings.value("Infopanel/totalamount", 1))))
        self.ui.chb_datainfo_percentage.setChecked(bool(int(self.settings_handler.settings.value("Infopanel/percentage", 1))))
        self.ui.chb_datainfo_createdate.setChecked(bool(int(self.settings_handler.settings.value("Infopanel/createdate", 1))))
        self.ui.chb_datainfo_paymenttype.setChecked(bool(int(self.settings_handler.settings.value("Infopanel/paymenttype", 1))))
        self.ui.chb_datainfo_descr.setChecked(bool(int(self.settings_handler.settings.value("Infopanel/descr", 1))))
        self.ui.chb_datainfo_responsible.setChecked(bool(int(self.settings_handler.settings.value("Infopanel/responsible", 1))))
        ## Настройки экспорта
        self.ui.chb_frozenheader.setChecked(bool(int(self.settings_handler.settings.value("Export/frozenheader", 1))))
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
        self.ui.cmb_backupautodelete.setCurrentIndex(0)
        try:
            for cleanbackup_option in self.CLEANBACKUP_SET.items():
                if int(self.settings_handler.settings.value("Backup/cleanupperiod")) == cleanbackup_option[1]:
                    self.ui.cmb_backupautodelete.setCurrentIndex(cleanbackup_option[0])
        except ValueError, TypeError:
            pass
        self.ui.le_backuppath.setText(self.settings_handler.settings.value("Backup/path", ""))
        # CSV-парсер
        try:
            self.ui.spb_csv_rowperiod.setValue(int(self.settings_handler.settings.value("CSVparser/rowperiod", DEF_ROW_PERIOD)))
        except ValueError, TypeError:
            self.ui.spb_csv_rowperiod.setValue(DEF_ROW_PERIOD)
        try:
            self.ui.spb_csv_rowfirsttransaction.setValue(int(self.settings_handler.settings.value("CSVparser/rowtransactionstart", DEF_ROW_TRANSACTIONSTART)))
        except ValueError, TypeError:
            self.ui.spb_csv_rowfirsttransaction.setValue(DEF_ROW_TRANSACTIONSTART)
        try:
            self.ui.spb_csv_codetransaction.setValue(int(self.settings_handler.settings.value("CSVparser/transactioncode", DEF_TRANSACTION_CODE)))
        except ValueError, TypeError:
            self.ui.spb_csv_codetransaction.setValue(DEF_TRANSACTION_CODE)
        self.ui.le_csv_columns.setText(self.settings_handler.settings.value("CSVparser/columnstoparse", DEF_COLUMNSTOPARSE))
        self.ui.le_csv_unp.setText(self.settings_handler.settings.value("CSVparser/knownunp", ""))

    def save_settings_values(self) -> None:
        # Отображение
        ## Отображение оплаченных
        self.settings_handler.settings.setValue("Common/paidloadperiod", int(self.ui.cmb_loadpaid.currentData()))
        ## Размер шрифта
        self.settings_handler.settings.setValue("Appearance/fontsize", self.rbg_fontsize.checkedId())
        # Таблица
        ## Отображаемые столбцы
        self.settings_handler.settings.setValue("Columns/totalamount", int(self.ui.chb_dataintable_totalamount.isChecked()))
        self.settings_handler.settings.setValue("Columns/paymenttype", int(self.ui.chb_dataintable_paymenttype.isChecked()))
        self.settings_handler.settings.setValue("Columns/descr", int(self.ui.chb_dataintable_descr.isChecked()))
        self.settings_handler.settings.setValue("Columns/responsible", int(self.ui.chb_dataintable_responsible.isChecked()))
        self.settings_handler.settings.setValue("Columns/createdate", int(self.ui.chb_dataintable_createdate.isChecked()))
        ## Данные в информационной панели
        self.settings_handler.settings.setValue("Infopanel/totalamount", int(self.ui.chb_datainfo_totalamount.isChecked()))
        self.settings_handler.settings.setValue("Infopanel/percentage", int(self.ui.chb_datainfo_percentage.isChecked()))
        self.settings_handler.settings.setValue("Infopanel/createdate", int(self.ui.chb_datainfo_createdate.isChecked()))
        self.settings_handler.settings.setValue("Infopanel/paymenttype", int(self.ui.chb_datainfo_paymenttype.isChecked()))
        self.settings_handler.settings.setValue("Infopanel/descr", int(self.ui.chb_datainfo_descr.isChecked()))
        self.settings_handler.settings.setValue("Infopanel/responsible", int(self.ui.chb_datainfo_responsible.isChecked()))
        ## Настройки экспорта
        self.settings_handler.settings.setValue("Export/frozenheader", int(self.ui.chb_frozenheader.isChecked()))
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
        self.settings_handler.settings.setValue("Backup/cleanupperiod", self.ui.cmb_backupautodelete.currentData(Qt.ItemDataRole.UserRole))
        self.settings_handler.settings.setValue("Backup/path", self.ui.le_backuppath.text())
        # CSV-парсер
        self.settings_handler.settings.setValue("CSVparser/rowperiod", self.ui.spb_csv_rowperiod.value())
        self.settings_handler.settings.setValue("CSVparser/rowtransactionstart", self.ui.spb_csv_rowfirsttransaction.value())
        self.settings_handler.settings.setValue("CSVparser/transactioncode", self.ui.spb_csv_codetransaction.value())
        self.settings_handler.settings.setValue("CSVparser/columnstoparse", self.ui.le_csv_columns.text())
        self.settings_handler.settings.setValue("CSVparser/knownunp", self.ui.le_csv_unp.text())

        self.settings_handler.settings.sync()

    def change_stw_page(self, current_item: QListWidgetItem, previous_item: QListWidgetItem) -> None:
        self.ui.stw.setCurrentIndex(self.MENU_PAGES[self.ui.lw_menu.row(current_item)])

    def request_restore_backup(self) -> bool:
        msg_box = YesNoMessagebox("Обратите внимание, что данные текущей сессии будут заменены выбранными и в результате полностью утрачены. "
                                  "Последней сохраненной контрольной точкой будет точка последнего запуска приложения (при условии, что резервное "
                                  "копирование было выполнено успешно). Уверены, что хотите продолжить?", self)
        if not msg_box.exec():
            return False
        backup_folder = self.settings_handler.settings.value("Backup/path")
        file_path: str = QFileDialog.getOpenFileName(parent=self, caption="Выберите файл БД",
                                                     dir="" if not backup_folder or not os.path.isdir(backup_folder) else backup_folder,
                                                     filter="База данных SQLite 3 (*.db)")[0]
        if not file_path:
            return False
        if restore_backup(self.db_handler, file_path):
            ErrorInfoMessageBox("Восстановление прошло успешно!", True, self).exec()
            return True
        else:
            ErrorInfoMessageBox("При попытке восстановления произошла ошибка", True, self).exec()
            return False
