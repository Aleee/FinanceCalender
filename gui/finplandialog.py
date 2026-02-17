from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import QDialog, QHeaderView, QApplication
import lovely_logger as log

from base.dbhandler import DBHandler
from gui.commonwidgets.messagebox import ErrorInfoMessageBox
from gui.finplanmodel import FinPlanTableModel
from gui.ui.finplandialog_ui import Ui_FinPlanDialog


class FinPlanDialog(QDialog):

    def __init__(self, db_handler: DBHandler, year: int, parent=None):
        super(FinPlanDialog, self).__init__(parent)
        self.ui = Ui_FinPlanDialog()
        self.ui.setupUi(self)

        self.db_handler = db_handler

        self.model = FinPlanTableModel()
        values = self.db_handler.load_finplan_from_db(year, self.model.FINPLAN_STRUCTURE)
        if not values:
            log.c(f"Не удалось загрузить данные финансового плана (выбранный год - {year})")
            msg_box = ErrorInfoMessageBox("Не удалось загрузить данные финансового плана из базы данных")
            msg_box.exec()
            self.reject()
        self.model.values = self.db_handler.load_finplan_from_db(year, self.model.FINPLAN_STRUCTURE)
        self.model.calculate_add_totals()
        self.ui.tv_finplan.setModel(self.model)

        for col in range(self.ui.tv_finplan.model().columnCount()):
            self.ui.tv_finplan.setColumnWidth(col, 70 if col != 0 else 250)
        self.ui.tv_finplan.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.ui.tv_finplan.verticalHeader().setDefaultSectionSize(20)

        self.shortcut_copy = QShortcut(QKeySequence.StandardKey.Copy, self.ui.tv_finplan)
        self.shortcut_copy.activated.connect(self.copy)
        # self.shortcut_copy = QShortcut(QKeySequence.StandardKey.Paste, self.ui.tv_finplan)
        # self.shortcut_copy.activated.connect(self.paste)

    def copy(self):
        values = ""
        selection_range = self.ui.tv_finplan.selectionModel().selection().first()
        for i in range(selection_range.top(), selection_range.bottom() + 1):
            row_content = []
            for j in range(selection_range.left(), selection_range.right() + 1):
                row_content.append(str(self.ui.tv_finplan.model().index(i, j).data()))
            values += "\t".join(row_content) + "\n"
        QApplication.clipboard().setText(values)

    def paste(self):
        start_index = self.ui.tv_finplan.selectionModel().selectedIndexes().first()
        cbtext = QApplication.clipboard().text()

