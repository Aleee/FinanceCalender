from PySide6.QtWidgets import QMessageBox, QPushButton, QWidget


class SyncConflictDialog(QMessageBox):
    def __init__(self, master_description: str, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowTitle("Конфликт синхронизации")
        self.setIcon(QMessageBox.Icon.Warning)
        self.setText("Изменения есть и в вашей базе данных, и в мастере. Автоматически объединить их нельзя.")
        self.setInformativeText(f"Мастер обновлён: {master_description}.\n\n"
                                "Перед любым выбором ваша версия будет сохранена в папке резервных копий.")

        self.take_master_button: QPushButton = QPushButton("Взять мастер", self)
        self.overwrite_button: QPushButton = QPushButton("Перезаписать мастер моей версией", self)
        self.cancel_button: QPushButton = QPushButton("Отмена", self)
        self.addButton(self.take_master_button, QMessageBox.ButtonRole.AcceptRole)
        self.addButton(self.overwrite_button, QMessageBox.ButtonRole.DestructiveRole)
        self.addButton(self.cancel_button, QMessageBox.ButtonRole.RejectRole)
        self.setEscapeButton(self.cancel_button)

    def take_master_chosen(self) -> bool:
        return self.clickedButton() is self.take_master_button

    def overwrite_chosen(self) -> bool:
        return self.clickedButton() is self.overwrite_button
