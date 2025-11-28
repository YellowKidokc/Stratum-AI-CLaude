from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)


class ApiKeyDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Stratum – API keys")

        self.openai_edit = QLineEdit(self)
        self.claude_edit = QLineEdit(self)
        self.deepseek_edit = QLineEdit(self)

        # Don't show keys as plain text if you prefer; for now, plain is OK.
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("OpenAI key", self.openai_edit)
        form.addRow("Claude key", self.claude_edit)
        form.addRow("DeepSeek key", self.deepseek_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self) -> tuple[str, str, str]:
        return (
            self.openai_edit.text().strip(),
            self.claude_edit.text().strip(),
            self.deepseek_edit.text().strip(),
        )
