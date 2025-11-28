from __future__ import annotations

from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QMessageBox
)

from .base import BaseTab
from .adapters import PromptManagerAdapter


class PromptsTab(BaseTab):
    def __init__(self, prompt_adapter: PromptManagerAdapter):
        super().__init__()
        self._adapter = prompt_adapter
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("AI Prompts")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        # Prompts list
        list_group = QLabel("Available Prompts:")
        layout.addWidget(list_group)

        self.prompt_list = QListWidget(self)
        self._load_prompts()
        self.prompt_list.itemSelectionChanged.connect(self._on_prompt_selected)
        layout.addWidget(self.prompt_list)

        # Prompt content display
        content_group = QLabel("Prompt Content:")
        layout.addWidget(content_group)

        self.prompt_content = QTextEdit()
        self.prompt_content.setReadOnly(True)
        self.prompt_content.setMaximumHeight(150)
        layout.addWidget(self.prompt_content)

        # Buttons
        buttons_layout = QHBoxLayout()
        run_btn = QPushButton("Use Prompt")
        run_btn.clicked.connect(self._on_use_prompt)
        buttons_layout.addWidget(run_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_prompts)
        buttons_layout.addWidget(refresh_btn)

        layout.addLayout(buttons_layout)

    def _load_prompts(self) -> None:
        """Load prompts from adapter."""
        self.prompt_list.clear()
        prompts = self._adapter.get_all_prompts()

        for prompt in prompts:
            item_text = f"{prompt['title']}"
            if prompt['tags']:
                item_text += f" ({', '.join(prompt['tags'])})"
            item = QListWidgetItem(item_text)
            item.setData(1, prompt)  # Store full prompt data
            self.prompt_list.addItem(item)

    def _on_prompt_selected(self) -> None:
        """Handle prompt selection."""
        current_item = self.prompt_list.currentItem()
        if current_item:
            prompt_data = current_item.data(1)
            if prompt_data:
                self.prompt_content.setPlainText(prompt_data['content'])

    def _on_use_prompt(self) -> None:
        """Handle using the selected prompt."""
        current_item = self.prompt_list.currentItem()
        if current_item:
            prompt_data = current_item.data(1)
            if prompt_data:
                # Copy prompt content to clipboard
                from PySide6.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                clipboard.setText(prompt_data['content'])
                QMessageBox.information(self, "Copied", "Prompt copied to clipboard!")
            else:
                QMessageBox.warning(self, "No Selection", "Please select a prompt first.")
        else:
            QMessageBox.warning(self, "No Selection", "Please select a prompt first.")
            return
        prompt = self._prompts[index]
        selection = get_selection().text
        if not selection.strip():
            return

        def run() -> None:
            output = self._client.chat(prompt.system or None, prompt.build_message(selection), prompt.temperature)
            if not output.strip():
                return
            if prompt.replace:
                replace_selection(output)
            else:
                ResultPopup.show_text(prompt.name, output)

        threading.Thread(target=run, daemon=True).start()
