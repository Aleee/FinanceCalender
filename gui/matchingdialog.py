from pathlib import Path

import lovely_logger as log

from PySide6.QtWidgets import QDialog, QFileDialog

from base.dbhandler import DBHandler
from base.feeparser import CSVParseError
from base.paymentmacther import reconcile_statement_with_calendar, ReconciliationResult
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.settings import SettingsHandler
from gui.ui.matchingdialog_ui import Ui_matchingdialog


class MatchingDialog(QDialog):
    def __init__(self, settings_handler, db_handler, parent=None):
        super(MatchingDialog, self).__init__(parent)
        self.ui = Ui_matchingdialog()
        self.ui.setupUi(self)

        self.sh: SettingsHandler = settings_handler
        self.dbh: DBHandler = db_handler

        self.match_result: ReconciliationResult | None = None

        self.ui.pb_close.clicked.connect(self.close)
        self.ui.pb_opencsv.clicked.connect(self.open_csv)
        self.ui.chb_fullreport.clicked.connect(self.print_report)

    def open_csv(self):
        last_path = self.sh.settings.value("CSVparser/lastloadpath")
        file_path: str = QFileDialog.getOpenFileName(
            parent=self,
            caption="Выберите выписку",
            dir=last_path if last_path and Path(last_path).is_dir() else "",
            filter="Файл выписки в формате CSV (*.csv)", )[0]
        if not file_path:
            return

        self.sh.settings.setValue("CSVparser/lastloadpath", str(Path(file_path).parent))
        self.ui.te_info.clear()

        try:
            self.match_result = reconcile_statement_with_calendar(file_path, self.dbh, self.sh)
        except CSVParseError as exc:
            log.w(f"Не удалось прочитать CSV-файл выписки: {exc}")
            ErrorInfoMessageBox(f"Не удалось прочитать CSV-файл: {exc}").exec()
            self.match_result = None
            return
        except Exception as exc:
            log.x(f"Не удалось обработать CSV-файл: {exc}")
            ErrorInfoMessageBox(f"Не удалось обработать CSV-файл: {exc}").exec()
            self.match_result = None
            return
        if self.match_result is None:
            ErrorInfoMessageBox("В процессе обработки CSV-файла произошла ошибка (см. лог)").exec()
            self.match_result = None
            return

        self.print_report()

    def print_report(self):
        if self.match_result is None:
            return
        full_requested = self.ui.chb_fullreport.isChecked()
        self.ui.te_info.setHtml(self.match_result.format_report(full=full_requested))
