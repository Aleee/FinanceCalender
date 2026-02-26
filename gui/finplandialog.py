import lovely_logger as log
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import QDialog, QHeaderView, QApplication

from base.dbhandler import DBHandler
from gui.commonwidgets.eventfilter import TooltipFilter
from gui.commonwidgets.messagebox import ErrorInfoMessageBox, YesNoMessagebox
from gui.finplanmodel import FinPlanTableModel
from gui.ui.finplandialog_ui import Ui_FinPlanDialog


class FinPlanDialog(QDialog):

    def __init__(self, db_handler: DBHandler, year: int, parent=None):
        super(FinPlanDialog, self).__init__(parent)
        self.ui = Ui_FinPlanDialog()
        self.ui.setupUi(self)

        self.db_handler: DBHandler = db_handler
        self.year: int = year

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

        self.shortcut_copy: QShortcut = QShortcut(QKeySequence.StandardKey.Copy, self.ui.tv_finplan)
        self.shortcut_copy.activated.connect(self.copy)
        self.shortcut_copy: QShortcut = QShortcut(QKeySequence.StandardKey.Paste, self.ui.tv_finplan)
        self.shortcut_copy.activated.connect(self.paste)

        self.tooltip_eventfilter: TooltipFilter = TooltipFilter(self.ui.tv_finplan)
        self.ui.tv_finplan.installEventFilter(self.tooltip_eventfilter)

        self.ui.pb_cancel.clicked.connect(self.reject)
        self.ui.pb_save.clicked.connect(self.accept)

    def copy(self):
        values: str = ""
        selection_range = self.ui.tv_finplan.selectionModel().selection()[0]
        for i in range(selection_range.top(), selection_range.bottom() + 1):
            row_content: list = []
            for j in range(selection_range.left(), selection_range.right() + 1):
                row_content.append(str(self.ui.tv_finplan.model().index(i, j).data()))
            values += "\t".join(row_content) + "\n"
        QApplication.clipboard().setText(values)

    def paste(self):
        start_index: QModelIndex = self.ui.tv_finplan.selectionModel().selectedIndexes()[0]
        cbtext: str = QApplication.clipboard().text()
        i, j = 0, 0
        for row_text in cbtext.split("\n"):
            j = 0
            for cell_text in row_text.split("\t"):
                index = self.ui.tv_finplan.model().index(start_index.row() + i, start_index.column() + j)
                QApplication.clipboard().setText(cell_text)
                if index.isValid() and index.data(self.model.EditableRole):
                    self.ui.tv_finplan.model().setData(index, cell_text, Qt.ItemDataRole.EditRole)
                j += 1
            i += 1

    def accept(self, /):
        if not self.db_handler.save_finplan_to_db(self.year, self.model.FINPLAN_STRUCTURE, self.model):
            msg_box = ErrorInfoMessageBox("К сожалению, данные не удалось сохранить (см. подробности в логе)")
            msg_box.exec()
            return
        QDialog.accept(self)

    def reject(self, /):
        msg_box = YesNoMessagebox("Вы уверены, что хотите выйти без сохранения изменений?")
        if msg_box.exec() == YesNoMessagebox.YES_RETURN_VALUE:
            QDialog.reject(self)
