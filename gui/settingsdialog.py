import os.path
import sys
from pathlib import Path
from typing import Optional

from PySide6 import QtGui, QtCore
from PySide6.QtGui import QPalette, QRegularExpressionValidator, QShortcut, QKeySequence
from PySide6.QtWidgets import QDialog, QListWidget, QListWidgetItem, QLineEdit, QFileDialog, QButtonGroup, QWidget, \
    QInputDialog, QPushButton, QApplication
from PySide6.QtCore import Qt, QSize, QRegularExpression, QModelIndex, QDate, QTimer

from base.backup import restore_backup
from base.casting import str_bool, str_int
from base.dbhandler import DBHandler
from base.updater import UpdateChecker, UpdateInfo
from base.workcalendar import load_calendar_exceptions, save_calendar_exceptions, ALLOWED_WEEKDAYS, WEEKDAY_ABBR
from gui.commonwidgets.datepickerdialog import DatePickerDialog
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.eventsqlmodel import RowFormatting
from gui.personaltablemodel import PersonalTableModel, PersonalSortFilterModel, PersonalCol
from gui.settings import SettingsHandler
from gui.ui.settingsdialog_ui import Ui_settingsdialog

DEF_ROW_PERIOD: int = 1
DEF_ROW_TRANSACTIONSTART: int = 9
DEF_TRANSACTION_CODE: int = 6
DEF_COLUMNSTOPARSE: str = "0,2,5,8,7,9,6"


class SettingsDialog(QDialog):

    MENU_PAGES = {
        0: 1,
        1: 3,
        2: 2,
        3: 0,
        4: 4,
        5: 5,
        6: 6,
        7: 7,
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

    HOTKEYS = (
        ("Ctrl+N", "Новый платеж"),
        ("Ctrl+D", "Копировать платеж"),
        ("Ctrl+Shift+D", "Быстрая копия привязанного платежа"),
        ("F2", "Редактировать платеж (или двойной клик)"),
        ("Del", "Удалить платеж"),
        ("Ctrl+E", "Экспорт"),
        ("Ctrl+F", "Поиск по платежам"),
        ("Ctrl+R", "Сбросить все фильтры"),
    )

    MENU_ROW_CSV: int = 3
    MENU_ROW_PERSONAL: int = 4
    MENU_ROW_STORAGE: int = 5
    MENU_ROW_MISC: int = 7

    def __init__(self, settings_handler: SettingsHandler, db_handler: DBHandler, reject_possible: bool = True, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.ui = Ui_settingsdialog()
        self.ui.setupUi(self)

        self.settings_handler: SettingsHandler = settings_handler
        self.settings_handler.save_settings()
        self.db_handler = db_handler

        self.personal_model: Optional[PersonalTableModel] = None
        self.personal_proxy_model: Optional[PersonalSortFilterModel] = None

        self.reject_possible: bool = reject_possible
        self.ui.lw_menu.setIconSize(QSize(30, 30))
        self.ui.pb_cancel.setEnabled(reject_possible)
        if not reject_possible:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowType.CustomizeWindowHint)
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowType.WindowCloseButtonHint)

        # Центрирование элементов списка меню
        menu_item_height: int = max(40, self.ui.lw_menu.fontMetrics().height() + 20)
        for row in range(self.ui.lw_menu.count()):
            self.ui.lw_menu.item(row).setSizeHint(QSize(128, menu_item_height))
            self.ui.lw_menu.item(row).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.ui.lw_menu.item(self.MENU_ROW_MISC).setHidden(True)

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
        current_year: int = QDate.currentDate().year()
        for year in range(current_year - 1, current_year + 2):
            self.ui.cmb_calender_year.addItem(str(year), year)
        self.ui.cmb_calender_year.setCurrentIndex(self.ui.cmb_calender_year.findData(current_year))

        # Валидаторы
        reg_unp = QRegularExpression(r"^(\d{9}(,\s?\d{9})*)?$")
        validator_unp = QRegularExpressionValidator(reg_unp)
        self.ui.le_csv_unp.setValidator(validator_unp)
        self.ui.le_csv_unp.textChanged.connect(lambda: self.highlight_invalid_input(self.ui.le_csv_unp))
        self.ui.le_csv_columns.textChanged.connect(lambda: self.highlight_invalid_input(self.ui.le_csv_columns))

        # Сигналы
        self.ui.pb_ok.clicked.connect(self.accept)
        self.ui.pb_cancel.clicked.connect(self.reject)
        self.ui.lw_menu.currentItemChanged.connect(self.change_stw_page)
        self.ui.pb_backuppath.clicked.connect(lambda: self.change_path(self.ui.le_backuppath))
        self.ui.pb_restorefrombackup.clicked.connect(self.request_restore_backup)
        self.ui.pb_format_reset.clicked.connect(self.reset_formatting)

        # Образец форматирования
        for wdg in self.format_color_buttons():
            wdg.color_changed.connect(self.update_format_preview)
        for wdg in (self.ui.chb_formatbolddue, self.ui.chb_formatboldtoday,
                    self.ui.chb_formatboldheader, self.ui.chb_formatboldfooter):
            wdg.toggled.connect(self.update_format_preview)

        # Меню персонала
        self.prepare_personalpage()
        # Календарь
        self.prepare_calendarpage()
        # Также добавить персонал в CSV-подменю
        self.ui.cmb_csv_responsible.setModel(self.personal_proxy_model)
        self.ui.cmb_csv_responsible.setModelColumn(PersonalCol.NAME)
        # Информация
        self.fill_hotkeys_info()
        self.prepare_updatesection()
        app = QApplication.instance()
        self.ui.la_buildnumber.setText(f"Сборка {app.app_version}")
        db_version = self.db_handler.get_db_version()
        self.ui.la_dbnumber.setText("База данных v" + ("?" if db_version is None else str(db_version)))

        # Выбор первого пункта меню и косметика выбора
        palette: QPalette = self.ui.lw_menu.palette()
        palette.setColor(QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Highlight,
                         palette.color(QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Highlight))
        palette.setColor(QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.HighlightedText,
                         palette.color(QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.HighlightedText))
        self.ui.lw_menu.setPalette(palette)
        last_page: int = str_int(self.settings_handler.settings.value("SettingsDialog/lastpage", 0), 0)
        if not 0 <= last_page < self.ui.lw_menu.count() or self.ui.lw_menu.item(last_page).isHidden():
            last_page = 0
        self.ui.lw_menu.setCurrentRow(last_page)

        self.load_settings_values()

    def prepare_personalpage(self):
        self.personal_model = PersonalTableModel(self.db_handler, self)
        self.personal_model.setup_model()
        self.personal_proxy_model = PersonalSortFilterModel()
        self.personal_proxy_model.setSourceModel(self.personal_model)
        self.personal_proxy_model.sort(PersonalCol.NAME)

        self.ui.lv_personal.setModel(self.personal_proxy_model)
        self.ui.lv_personal.setModelColumn(PersonalCol.NAME)

        self.departments: list[tuple[int, str]] = self.db_handler.load_departments() or []
        for dept_id, dept_name in self.departments:
            self.ui.cmb_pers_dept.addItem(dept_name, dept_id)

        self.positions: dict[int, tuple[int, str]] = self.db_handler.load_positions(as_dict=True) or {}

        self.prepare_positionmanagement_section()

        for wdg in (self.ui.pb_pers_current, self.ui.pb_pers_hist):
            wdg.clicked.connect(lambda: self.personal_proxy_model.show_actuals(self.ui.pb_pers_current.isChecked()))
            wdg.clicked.connect(lambda: self.ui.pb_pers_add.setEnabled(self.ui.pb_pers_current.isChecked()))
            wdg.clicked.connect(lambda: self.ui.pb_pers_changetype.setText(
                "В архив" if self.ui.pb_pers_current.isChecked() else "Вернуть"))

        self.ui.cmb_pers_dept.activated.connect(self.on_persdept_changed)
        self.ui.cmb_pers_position.activated.connect(self.on_persposition_changed)

        self.ui.pb_pers_add.clicked.connect(self.add_personal)
        self.ui.pb_pers_rename.clicked.connect(self.rename_personal)
        self.ui.pb_pers_changetype.clicked.connect(self.change_personaltype)
        self.ui.lv_personal.doubleClicked.connect(lambda index: self.rename_personal())

        self.ui.lv_personal.selectionModel().currentChanged.connect(self.on_personallist_current_change)
        self.personal_proxy_model.layoutChanged.connect(
            lambda: self.on_personallist_current_change(QModelIndex(), QModelIndex()))
        if self.ui.lv_personal.model().rowCount() > 0:
            self.ui.lv_personal.setCurrentIndex(self.ui.lv_personal.model().index(0, PersonalCol.NAME, QModelIndex()))

    def fill_hotkeys_info(self) -> None:
        rows: list[str] = []
        for keys, description in self.HOTKEYS:
            rows.append(f"<tr><td style='background-color: #ffffff; color: #2c5c8a;'>&nbsp;<b>{keys}</b>&nbsp;</td>"
                        f"<td style='padding-left: 8px;'>{description}</td></tr>")
        self.ui.la_hotkeys.setText(f"<table cellspacing='3' cellpadding='2'>{''.join(rows)}</table>")

    def prepare_updatesection(self) -> None:
        self.update_checker: Optional[UpdateChecker] = getattr(QApplication.instance(), "update_checker", None)
        if self.update_checker is None:
            self.ui.gb_updates.setHidden(True)
            return
        self.manual_check: bool = False
        self.update_checker.check_finished.connect(self.show_update_status)
        self.update_checker.update_available.connect(self.on_update_found)
        self.ui.pb_checkupdates.clicked.connect(self.request_update_check)
        self.show_update_status()

    def request_update_check(self) -> None:
        self.manual_check = True
        self.update_checker.check()
        self.show_update_status()

    def on_update_found(self, info: UpdateInfo) -> None:
        if not self.manual_check:
            return
        self.manual_check = False
        msg_box = YesNoMessagebox(f"Доступно обновление {info.version}. Для его установки настройки будут сохранены, "
                                  "а окно настроек закрыто. Продолжить?", self)
        if msg_box.exec() != YesNoMessagebox.YES_RETURN_VALUE:
            return
        self.accept()
        update_controller = getattr(QApplication.instance(), "update_controller", None)
        if self.result() == QDialog.DialogCode.Accepted and update_controller is not None:
            QTimer.singleShot(0, lambda: update_controller.offer_update(info))

    def show_update_status(self) -> None:
        self.ui.pb_checkupdates.setEnabled(not self.update_checker.checking)
        if self.update_checker.checking:
            self.ui.la_updatestatus.setText("Проверка…")
        elif self.update_checker.last_check_time is None:
            self.ui.la_updatestatus.setText("Проверка ещё не выполнялась")
        else:
            checked_at: str = self.update_checker.last_check_time.toString("dd.MM.yyyy HH:mm")
            self.ui.la_updatestatus.setText(f"Последняя проверка: {checked_at}\n{self.update_checker.last_check_result}")

    def on_personallist_current_change(self, current: QModelIndex, prevoius: QModelIndex):
        current_index: QModelIndex = self.ui.lv_personal.currentIndex()
        selection_active: bool = current_index.isValid()
        self.ui.pb_pers_rename.setEnabled(selection_active)
        self.ui.pb_pers_changetype.setEnabled(selection_active)
        self.ui.cmb_pers_dept.setEnabled(selection_active)
        self.ui.cmb_pers_position.setEnabled(selection_active)
        if selection_active:
            dept: int = current_index.siblingAtColumn(PersonalCol.DEPT).data(PersonalTableModel.internalValueRole)
            position: int = current_index.siblingAtColumn(PersonalCol.POSITION).data(
                PersonalTableModel.internalValueRole)
            self.ui.cmb_pers_dept.setCurrentIndex(self.ui.cmb_pers_dept.findData(dept))
            self.refill_position_combo(dept, position)
        else:
            self.ui.cmb_pers_position.clear()

    def on_persdept_changed(self) -> None:
        current_index = self.ui.lv_personal.currentIndex()
        if not current_index.isValid():
            return
        new_dept = self.ui.cmb_pers_dept.currentData()
        self.personal_proxy_model.setData(current_index.siblingAtColumn(PersonalCol.DEPT), new_dept)
        # Должность привязана к конкретному подразделению — при смене подразделения сбрасывается
        self.personal_proxy_model.setData(current_index.siblingAtColumn(PersonalCol.POSITION), 0)
        self.refill_position_combo(new_dept, 0)

    def on_persposition_changed(self) -> None:
        current_index = self.ui.lv_personal.currentIndex()
        if not current_index.isValid():
            return
        new_position = self.ui.cmb_pers_position.currentData()
        if new_position:
            holder_row = self.find_active_position_holder(new_position)
            if holder_row is not None:
                holder_name = self.personal_model.tdata[holder_row][PersonalCol.NAME]
                ErrorInfoMessageBox(
                    f"Эту должность сейчас занимает {holder_name}. Сначала снимите этого работника с должности.").exec()
                current_position = current_index.siblingAtColumn(PersonalCol.POSITION).data(
                    PersonalTableModel.internalValueRole)
                self.ui.cmb_pers_position.setCurrentIndex(self.ui.cmb_pers_position.findData(current_position))
                return
        self.personal_proxy_model.setData(current_index.siblingAtColumn(PersonalCol.POSITION), new_position)

    def find_active_position_holder(self, position_id: int) -> Optional[int]:
        current_source_row = self.personal_proxy_model.mapToSource(self.ui.lv_personal.currentIndex()).row()
        for row, entry in enumerate(self.personal_model.tdata):
            if row == current_source_row:
                continue
            if entry[PersonalCol.POSITION] == position_id and not entry[PersonalCol.ARCHIVED]:
                return row
        return None

    def refill_position_combo(self, department_id: int, select_position_id: int = 0) -> None:
        self.ui.cmb_pers_position.blockSignals(True)
        self.ui.cmb_pers_position.clear()
        self.ui.cmb_pers_position.addItem("— нет —", 0)
        for pos_id, (pos_dept, pos_name) in self.positions.items():
            if pos_dept == department_id:
                self.ui.cmb_pers_position.addItem(pos_name, pos_id)
        idx = self.ui.cmb_pers_position.findData(select_position_id)
        self.ui.cmb_pers_position.setCurrentIndex(idx if idx >= 0 else 0)
        self.ui.cmb_pers_position.blockSignals(False)

    def add_personal(self):
        text, ok = QInputDialog.getText(self, "Введите имя работника", "Имя работника:")
        text = text.strip()
        if not ok or not self.personal_model.data_loaded or not text:
            return
        if not self.confirm_personal_name(text):
            return
        row: int = len(self.personal_model.tdata)
        self.personal_model.beginInsertRows(QModelIndex(), row, row)
        new_id = self.personal_model.last_id + 1
        default_dept = self.departments[0][0] if self.departments else 0
        new_row: list = [new_id, text, default_dept, 0, 0]
        self.personal_model.tdata.append(new_row)
        self.personal_model.endInsertRows()
        self.personal_model.last_id = new_id
        source_index: QModelIndex = self.personal_model.index(row, PersonalCol.NAME)
        proxy_index: QModelIndex = self.personal_proxy_model.mapFromSource(source_index)
        self.ui.lv_personal.setCurrentIndex(proxy_index)

    def rename_personal(self):
        current_index: QModelIndex = self.ui.lv_personal.currentIndex()
        if not current_index.isValid():
            return
        text, ok = QInputDialog.getText(self, "Сменить имя работника", "Новое имя работника:", text=f"{current_index.data()}")
        text = text.strip()
        if not ok or not text or text == current_index.data():
            return
        if not self.confirm_personal_name(text):
            return
        self.personal_proxy_model.setData(current_index, text)

    def confirm_personal_name(self, name: str) -> bool:
        if not any(entry[PersonalCol.NAME] == name for entry in self.personal_model.tdata):
            return True
        msg_box = YesNoMessagebox(f"Работник с именем \"{name}\" уже есть в списке (возможно, в архиве). Всё равно продолжить?", self)
        return msg_box.exec() == YesNoMessagebox.YES_RETURN_VALUE

    def change_personaltype(self):
        current_index: QModelIndex = self.ui.lv_personal.currentIndex()
        if not current_index.isValid():
            return
        self.personal_proxy_model.setData(current_index.siblingAtColumn(PersonalCol.ARCHIVED),
                                          0 if current_index.siblingAtColumn(PersonalCol.ARCHIVED).data(PersonalTableModel.internalValueRole) else 1)

    def prepare_positionmanagement_section(self) -> None:
        for dept_id, dept_name in self.departments:
            self.ui.cmb_positions_department.addItem(dept_name, dept_id)

        self.ui.cmb_positions_department.currentIndexChanged.connect(self.refresh_position_list)
        self.ui.pb_position_add.clicked.connect(self.add_position)
        self.ui.pb_position_rename.clicked.connect(self.rename_position)
        self.ui.pb_position_remove.clicked.connect(self.remove_position)
        self.ui.lw_positions.itemSelectionChanged.connect(self.on_positionlist_selection_change)
        self.ui.lw_positions.itemDoubleClicked.connect(lambda item: self.rename_position())
        self.add_delete_shortcut(self.ui.lw_positions, self.remove_position)
        self.ui.pb_position_rename.setEnabled(False)
        self.ui.pb_position_remove.setEnabled(False)

        self.refresh_position_list()

    def on_positionlist_selection_change(self) -> None:
        has_selection = bool(self.ui.lw_positions.selectedItems())
        self.ui.pb_position_rename.setEnabled(has_selection)
        self.ui.pb_position_remove.setEnabled(has_selection)

    def refresh_position_list(self) -> None:
        self.ui.lw_positions.clear()
        dept_id = self.ui.cmb_positions_department.currentData()
        for pos_id, (pos_dept, pos_name) in self.positions.items():
            if pos_dept == dept_id:
                item = QListWidgetItem(pos_name)
                item.setData(Qt.ItemDataRole.UserRole, pos_id)
                self.ui.lw_positions.addItem(item)
        self.ui.pb_position_rename.setEnabled(False)
        self.ui.pb_position_remove.setEnabled(False)

    def _refresh_pers_position_combo_if_needed(self, department_id: int) -> None:
        if self.ui.lv_personal.currentIndex().isValid() and self.ui.cmb_pers_dept.currentData() == department_id:
            self.refill_position_combo(department_id, self.ui.cmb_pers_position.currentData())

    def add_position(self) -> None:
        dept_id = self.ui.cmb_positions_department.currentData()
        if dept_id is None:
            return
        text, ok = QInputDialog.getText(self, "Новая должность", "Название должности:")
        text = text.strip()
        if not ok or not text or self.position_name_taken(dept_id, text):
            return
        new_id = self.db_handler.add_position(dept_id, text)
        if new_id is None:
            ErrorInfoMessageBox("Не удалось создать должность").exec()
            return
        self.positions[new_id] = (dept_id, text)
        self.refresh_position_list()
        self._refresh_pers_position_combo_if_needed(dept_id)

    def rename_position(self) -> None:
        item = self.ui.lw_positions.currentItem()
        if item is None:
            return
        pos_id = item.data(Qt.ItemDataRole.UserRole)
        text, ok = QInputDialog.getText(self, "Переименовать должность", "Название должности:", text=item.text())
        text = text.strip()
        dept_id = self.positions[pos_id][0]
        if not ok or not text or text == item.text() or self.position_name_taken(dept_id, text):
            return
        if not self.db_handler.rename_position(pos_id, text):
            ErrorInfoMessageBox("Не удалось переименовать должность").exec()
            return
        self.positions[pos_id] = (dept_id, text)
        self.refresh_position_list()
        self._refresh_pers_position_combo_if_needed(dept_id)

    def position_name_taken(self, department_id: int, name: str) -> bool:
        for pos_dept, pos_name in self.positions.values():
            if pos_dept == department_id and pos_name == name:
                ErrorInfoMessageBox(f"Должность \"{name}\" уже есть в этом подразделении").exec()
                return True
        return False

    def remove_position(self) -> None:
        item = self.ui.lw_positions.currentItem()
        if item is None:
            return
        pos_id = item.data(Qt.ItemDataRole.UserRole)
        msg_box = YesNoMessagebox(
            f"Удалить должность \"{item.text()}\"? Работники, занимающие её, лишатся привязки к должности "
            "(и останутся просто в своём подразделении).", self)
        if msg_box.exec() != YesNoMessagebox.YES_RETURN_VALUE:
            return
        if not self.db_handler.delete_position(pos_id):
            ErrorInfoMessageBox("Не удалось удалить должность").exec()
            return
        dept_id = self.positions[pos_id][0]
        for entry in self.personal_model.tdata:
            if entry[PersonalCol.POSITION] == pos_id:
                entry[PersonalCol.POSITION] = 0
        del self.positions[pos_id]
        self.refresh_position_list()
        self._refresh_pers_position_combo_if_needed(dept_id)

    def prepare_calendarpage(self) -> None:
        self.calendar_data: dict = {}
        self.last_picked_date: Optional[QDate] = None

        self.calendar_lists: dict[str, QListWidget] = {
            "holidays": self.ui.lw_calender_weekdays,
            "workbank": self.ui.lw_calender_workbankdays,
            "worknonbank": self.ui.lw_calender_worknonbankdays,
        }
        self.calendar_add_buttons: dict[str, QPushButton] = {
            "holidays": self.ui.pb_calender_add_week,
            "workbank": self.ui.pb_calender_add_workbank,
            "worknonbank": self.ui.pb_calender_add_worknobank,
        }
        self.calendar_remove_buttons: dict[str, QPushButton] = {
            "holidays": self.ui.pb_calender_remove_week,
            "workbank": self.ui.pb_calender_remove_workbank,
            "worknonbank": self.ui.pb_calender_remove_worknobank,
        }
        self.calendar_titles: dict[str, str] = {
            "holidays": self.ui.label_26.text(),
            "workbank": self.ui.label_25.text(),
            "worknonbank": self.ui.label_27.text(),
        }

        for category, button in self.calendar_add_buttons.items():
            button.clicked.connect(lambda checked=False, cat=category: self.add_calendar_exception(cat))
        for category, button in self.calendar_remove_buttons.items():
            button.setEnabled(False)
            button.clicked.connect(lambda checked=False, cat=category: self.remove_calendar_exception(cat))
        for category, list_widget in self.calendar_lists.items():
            list_widget.itemSelectionChanged.connect(
                lambda cat=category: self.calendar_remove_buttons[cat].setEnabled(
                    bool(self.calendar_lists[cat].selectedItems())))
            self.add_delete_shortcut(list_widget, lambda cat=category: self.remove_calendar_exception(cat))

        self.ui.cmb_calender_year.currentIndexChanged.connect(lambda: self.refresh_calendar_lists())

    def refresh_calendar_lists(self) -> None:
        year = self.ui.cmb_calender_year.currentData(Qt.ItemDataRole.UserRole)
        if year is None:
            return
        year_data = self.calendar_data.get(year, {"holidays": [], "workbank": [], "worknonbank": []})
        for category, list_widget in self.calendar_lists.items():
            list_widget.clear()
            for date in year_data.get(category, []):
                item = QListWidgetItem(f"{date.toString('dd.MM')} ({WEEKDAY_ABBR[date.dayOfWeek()]})")
                item.setData(Qt.ItemDataRole.UserRole, date)
                list_widget.addItem(item)
            self.calendar_remove_buttons[category].setEnabled(False)

    def add_calendar_exception(self, category: str) -> None:
        year = self.ui.cmb_calender_year.currentData(Qt.ItemDataRole.UserRole)
        if year is None:
            return
        min_date, max_date = QDate(year, 1, 1), QDate(year, 12, 31)

        if self.last_picked_date is not None and min_date <= self.last_picked_date <= max_date:
            initial_date = self.last_picked_date
        elif min_date <= QDate.currentDate() <= max_date:
            initial_date = QDate.currentDate()
        else:
            initial_date = min_date

        dialog = DatePickerDialog(initial_date, min_date, max_date, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        picked_date: QDate = dialog.selected_date()

        if picked_date.dayOfWeek() not in ALLOWED_WEEKDAYS[category]:
            allowed_days = ", ".join(WEEKDAY_ABBR[day] for day in sorted(ALLOWED_WEEKDAYS[category]))
            ErrorInfoMessageBox(f"В список \"{self.calendar_titles[category]}\" можно добавлять только дни: {allowed_days}").exec()
            return

        year_data = self.calendar_data.setdefault(year, {"holidays": [], "workbank": [], "worknonbank": []})
        for other_category, dates in year_data.items():
            if picked_date in dates:
                ErrorInfoMessageBox(f"Эта дата уже есть в списке \"{self.calendar_titles[other_category]}\"").exec()
                return

        year_data[category].append(picked_date)
        year_data[category].sort()
        self.last_picked_date = picked_date
        self.refresh_calendar_lists()

        list_widget = self.calendar_lists[category]
        list_widget.setCurrentRow(year_data[category].index(picked_date))

    def remove_calendar_exception(self, category: str) -> None:
        year = self.ui.cmb_calender_year.currentData(Qt.ItemDataRole.UserRole)
        list_widget = self.calendar_lists[category]
        current_item = list_widget.currentItem()
        if year is None or current_item is None:
            return
        date: QDate = current_item.data(Qt.ItemDataRole.UserRole)
        dates = self.calendar_data.get(year, {}).get(category, [])
        if date in dates:
            dates.remove(date)
        self.refresh_calendar_lists()

    def accept(self):
        if not self.ui.le_backuppath.text() or not Path(self.ui.le_backuppath.text()).is_dir():
            self.show_error("Папка для резервного копирования не указана или указана неверно",
                            self.MENU_ROW_STORAGE, self.ui.pb_backuppath)
            return
        if not self.ui.le_csv_columns.hasAcceptableInput():
            self.show_error("Укажите номера всех семи столбцов выписки (цифры через запятую)",
                            self.MENU_ROW_CSV, self.ui.le_csv_columns)
            return
        if not self.ui.le_csv_unp.hasAcceptableInput():
            self.show_error("Поле с перечнем известных УНП заполнено неверно (разрешены только девятизначные УНП через запятую)",
                            self.MENU_ROW_CSV, self.ui.le_csv_unp)
            return

        seen_positions: set = set()
        for entry in self.personal_model.tdata:
            pos = entry[PersonalCol.POSITION]
            if pos and not entry[PersonalCol.ARCHIVED]:
                if pos in seen_positions:
                    self.show_error("Обнаружена должность, занятая сразу несколькими активными работниками. Исправьте это перед сохранением.",
                                    self.MENU_ROW_PERSONAL, self.ui.lv_personal)
                    return
                seen_positions.add(pos)

        self.save_settings_values()
        self.settings_handler.apply_settings()
        if not self.db_handler.save_personal_data(self.personal_model.tdata):
            ErrorInfoMessageBox("Не удалось сохранить данные персонала (подробности см. в логе)", parent=self).exec()
            return
        QDialog.accept(self)

    def reject(self):
        if self.reject_possible:
            QDialog.reject(self)

    def done(self, result: int):
        self.settings_handler.settings.setValue("SettingsDialog/lastpage", self.ui.lw_menu.currentRow())
        super().done(result)

    def show_error(self, message: str, menu_row: int, widget: QWidget) -> None:
        self.ui.lw_menu.setCurrentRow(menu_row)
        ErrorInfoMessageBox(message, parent=self).exec()
        widget.setFocus()

    def highlight_invalid_input(self, le_widget: QLineEdit) -> None:
        le_widget.setStyleSheet("" if le_widget.hasAcceptableInput() else "border: 1px solid #cc0000;")

    def add_delete_shortcut(self, widget: QWidget, handler) -> None:
        shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Delete), widget)
        shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        shortcut.activated.connect(handler)

    def format_color_buttons(self) -> tuple:
        return (self.ui.pb_backgrounddue, self.ui.pb_foregrounddue,
                self.ui.pb_backgroundtoday, self.ui.pb_foregroundtoday,
                self.ui.pb_foregroundsectionheader, self.ui.pb_backgroundsectionheader,
                self.ui.pb_foregroundsubsectionheader, self.ui.pb_backgroundsubsectionheader,
                self.ui.pb_foregroundsectionfooter, self.ui.pb_backgroundsectionfooter,
                self.ui.pb_foregroundsubsectionfooter, self.ui.pb_backgroundsubsectionfooter)

    def reset_formatting(self) -> None:
        defaults = RowFormatting()
        self.ui.chb_verticalgrid.setChecked(defaults.vertical_grid)
        self.ui.chb_formatbolddue.setChecked(defaults.due_textbold)
        self.ui.chb_formatboldtoday.setChecked(defaults.today_textbold)
        self.ui.chb_formatboldheader.setChecked(defaults.header_textbold)
        self.ui.chb_formatboldfooter.setChecked(defaults.footer_textbold)
        default_colors = (defaults.due_backcolor, defaults.due_forecolor,
                          defaults.today_backcolor, defaults.today_forecolor,
                          defaults.header_section_forecolor, defaults.header_section_backcolor,
                          defaults.header_subsection_forecolor, defaults.header_subsection_backcolor,
                          defaults.footer_section_forecolor, defaults.footer_section_backcolor,
                          defaults.footer_subsection_forecolor, defaults.footer_subsection_backcolor)
        for button, color in zip(self.format_color_buttons(), default_colors):
            button.set_color(color)

    def update_format_preview(self) -> None:
        previews = (
            (self.ui.la_preview_due, self.ui.pb_backgrounddue, self.ui.pb_foregrounddue, self.ui.chb_formatbolddue),
            (self.ui.la_preview_today, self.ui.pb_backgroundtoday, self.ui.pb_foregroundtoday, self.ui.chb_formatboldtoday),
            (self.ui.la_preview_header, self.ui.pb_backgroundsectionheader, self.ui.pb_foregroundsectionheader, self.ui.chb_formatboldheader),
            (self.ui.la_preview_footer, self.ui.pb_backgroundsectionfooter, self.ui.pb_foregroundsectionfooter, self.ui.chb_formatboldfooter),
        )
        for label, pb_background, pb_foreground, chb_bold in previews:
            label.setStyleSheet(f"background-color: {pb_background.get_color() or 'white'}; "
                                f"color: {pb_foreground.get_color() or 'black'}; "
                                f"font-weight: {'bold' if chb_bold.isChecked() else 'normal'}; "
                                "border: 1px solid #c0c0c0; padding: 2px 8px;")
        # Qt не пересчитывает раскладку скрытой страницы до её первого показа
        self.ui.groupBox_8.layout().activate()

    def change_path(self, le_widget: QLineEdit) -> None:
        path: str = QFileDialog.getExistingDirectory(self, "Выберите папку", le_widget.text())
        if path:
            le_widget.setText(path)

    def load_settings_values(self) -> None:
        # Основные
        ## Отображение оплаченных
        self.ui.cmb_loadpaid.setCurrentIndex(1)
        paidloadperiod: int = str_int(self.settings_handler.settings.value("Common/paidloadperiod"), -1)
        for loadpaid_option in self.LOADPAID_SET.items():
            if paidloadperiod == loadpaid_option[1]:
                self.ui.cmb_loadpaid.setCurrentIndex(loadpaid_option[0])
        ## Размер шрифта
        fontsize_value: int = min(max(str_int(self.settings_handler.settings.value("Appearance/fontsize", 0), 0), 0), 2)
        self.rbg_fontsize.button(fontsize_value).setChecked(True)
        # Таблица
        ## Отображаемые столбцы
        self.ui.chb_dataintable_totalamount.setChecked(str_bool(self.settings_handler.settings.value("Columns/totalamount", 1)))
        self.ui.chb_dataintable_paymenttype.setChecked(str_bool(self.settings_handler.settings.value("Columns/paymenttype", 1)))
        self.ui.chb_dataintable_descr.setChecked(str_bool(self.settings_handler.settings.value("Columns/descr", 1)))
        self.ui.chb_dataintable_responsible.setChecked(str_bool(self.settings_handler.settings.value("Columns/responsible", 1)))
        self.ui.chb_dataintable_createdate.setChecked(str_bool(self.settings_handler.settings.value("Columns/createdate", 1)))
        ## Настройки экспорта
        self.ui.chb_frozenheader.setChecked(str_bool(self.settings_handler.settings.value("Export/frozenheader", 1)))
        ## Форматирование строк
        self.ui.chb_verticalgrid.setChecked(str_bool(self.settings_handler.settings.value("Tableformat/verticalgrid"), RowFormatting().vertical_grid))
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
        self.ui.chb_formatboldfooter.setChecked(str_bool(self.settings_handler.settings.value("Tableformat/boldforegroundfooter", RowFormatting().footer_textbold)))
        self.ui.pb_foregroundsectionfooter.set_color(self.settings_handler.settings.value("Tableformat/foregroundsectionfooter", RowFormatting().footer_section_forecolor))
        self.ui.pb_backgroundsectionfooter.set_color(self.settings_handler.settings.value("Tableformat/backgroundsectionfooter", RowFormatting().footer_section_backcolor))
        self.ui.pb_foregroundsubsectionfooter.set_color(self.settings_handler.settings.value("Tableformat/foregroundsubsectionfooter", RowFormatting().footer_subsection_forecolor))
        self.ui.pb_backgroundsubsectionfooter.set_color(self.settings_handler.settings.value("Tableformat/backgroundsubsectionfooter", RowFormatting().footer_subsection_backcolor))
        # Хранение
        self.ui.cmb_backupautodelete.setCurrentIndex(0)
        cleanupperiod: int = str_int(self.settings_handler.settings.value("Backup/cleanupperiod"), -1)
        for cleanbackup_option in self.CLEANBACKUP_SET.items():
            if cleanupperiod == cleanbackup_option[1]:
                self.ui.cmb_backupautodelete.setCurrentIndex(cleanbackup_option[0])
        self.ui.le_backuppath.setText(self.settings_handler.backup_path())
        # CSV-парсер
        self.ui.spb_csv_rowperiod.setValue(
            str_int(self.db_handler.get_setting("CSVparser/rowperiod", DEF_ROW_PERIOD), DEF_ROW_PERIOD))
        self.ui.spb_csv_rowfirsttransaction.setValue(
            str_int(self.db_handler.get_setting("CSVparser/rowtransactionstart", DEF_ROW_TRANSACTIONSTART), DEF_ROW_TRANSACTIONSTART))
        self.ui.le_csv_columns.setText(self.db_handler.get_setting("CSVparser/columnstoparse", DEF_COLUMNSTOPARSE))
        self.ui.le_csv_unp.setText(self.db_handler.get_setting("CSVparser/knownunp"))
        self.ui.te_csv_patterns.setPlainText(self.db_handler.get_setting("CSVparser/patterns"))
        for row in range(self.ui.cmb_csv_responsible.model().rowCount()):
            if self.db_handler.get_setting("CSVparser/responsible", "0") == self.ui.cmb_csv_responsible.model().index(row, 0).data():
                self.ui.cmb_csv_responsible.setCurrentIndex(row)
                break
        self.ui.te_csv_nomatchpatterns.setPlainText(self.db_handler.get_setting("CSVparser/nomatchpatterns"))
        # Календарь
        self.calendar_data = {}
        for row in range(self.ui.cmb_calender_year.count()):
            year: int = self.ui.cmb_calender_year.itemData(row)
            self.calendar_data[year] = load_calendar_exceptions(self.db_handler, year)
        self.refresh_calendar_lists()

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
        ## Настройки экспорта
        self.settings_handler.settings.setValue("Export/frozenheader", int(self.ui.chb_frozenheader.isChecked()))
        ## Форматирование строк
        self.settings_handler.settings.setValue("Tableformat/verticalgrid", int(self.ui.chb_verticalgrid.isChecked()))
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
        self.settings_handler.set_backup_path(self.ui.le_backuppath.text())
        # CSV-парсер
        self.db_handler.set_setting("CSVparser/rowperiod", self.ui.spb_csv_rowperiod.value())
        self.db_handler.set_setting("CSVparser/rowtransactionstart", self.ui.spb_csv_rowfirsttransaction.value())
        self.db_handler.set_setting("CSVparser/columnstoparse", self.ui.le_csv_columns.text())
        self.db_handler.set_setting("CSVparser/knownunp", self.ui.le_csv_unp.text())
        self.db_handler.set_setting("CSVparser/patterns", self.ui.te_csv_patterns.toPlainText())
        self.db_handler.set_setting("CSVparser/responsible", self.ui.cmb_csv_responsible.model().index(self.ui.cmb_csv_responsible.currentIndex(), 0).data())
        self.db_handler.set_setting("CSVparser/nomatchpatterns", self.ui.te_csv_nomatchpatterns.toPlainText())
        # Календарь
        for year, year_data in self.calendar_data.items():
            save_calendar_exceptions(self.db_handler, year, year_data)

        self.settings_handler.settings.sync()

    def change_stw_page(self, current_item: QListWidgetItem, previous_item: QListWidgetItem) -> None:
        self.ui.stw.setCurrentIndex(self.MENU_PAGES[self.ui.lw_menu.row(current_item)])

    def request_restore_backup(self) -> bool:
        msg_box = YesNoMessagebox("Обратите внимание, что данные текущей сессии будут заменены выбранными и в результате полностью утрачены. "
                                  "Последней сохраненной контрольной точкой будет точка последнего запуска приложения (при условии, что резервное "
                                  "копирование было выполнено успешно). Уверены, что хотите продолжить?", self)
        if msg_box.exec() != YesNoMessagebox.YES_RETURN_VALUE:
            return False
        backup_folder = self.settings_handler.backup_path()
        file_path: str = QFileDialog.getOpenFileName(parent=self, caption="Выберите файл БД",
                                                     dir=backup_folder if os.path.isdir(backup_folder) else "",
                                                     filter="База данных SQLite 3 (*.db)")[0]
        if not file_path:
            return False
        if restore_backup(self.db_handler, file_path):
            ErrorInfoMessageBox("Восстановление прошло успешно! Окно настроек будет закрыто, "
                                "несохранённые изменения в нём отменены.", True, self).exec()
            QDialog.reject(self)
            return True
        else:
            ErrorInfoMessageBox("При попытке восстановления произошла ошибка (подробности см. в логе)", False, self).exec()
            return False
