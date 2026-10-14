from PySide6.QtWidgets import QDialogButtonBox, QPushButton, QWidget

from base.syncdiff import Conflict, DbDiff
from gui.syncchangesdialog import SyncChangesDialog


class SyncConflictDialog(SyncChangesDialog):
    clicked_button: QPushButton | None = None

    def __init__(self, master_description: str, parent: QWidget | None = None, tabs: list[tuple[str, DbDiff | None]] | None = None,
                 conflicts: list[Conflict] | None = None):
        super().__init__("Изменения есть и в вашей локальной копии, и в общей базе. Автоматически объединить их нельзя.",
                         tabs or [], parent,
                         f"Общая база обновлена: {master_description}.\nПеред любым выбором ваша версия будет сохранена в папке резервных копий.",
                         conflicts)
        self.setWindowTitle("Конфликт синхронизации")

    def create_buttons(self) -> None:
        self.take_master_button: QPushButton = QPushButton("Взять общую базу", self)
        self.overwrite_button: QPushButton = QPushButton("Перезаписать общую базу моей версией", self)
        self.cancel_button: QPushButton = QPushButton("Отмена", self)
        self.button_box.addButton(self.take_master_button, QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.addButton(self.overwrite_button, QDialogButtonBox.ButtonRole.DestructiveRole)
        self.button_box.addButton(self.cancel_button, QDialogButtonBox.ButtonRole.RejectRole)
        self.cancel_button.setDefault(True)
        self.button_box.clicked.connect(self.on_button_clicked)

    def on_button_clicked(self, button: QPushButton) -> None:
        self.clicked_button = button
        if button is self.cancel_button:
            self.reject()
        else:
            self.accept()

    def take_master_chosen(self) -> bool:
        return self.clicked_button is self.take_master_button

    def overwrite_chosen(self) -> bool:
        return self.clicked_button is self.overwrite_button
