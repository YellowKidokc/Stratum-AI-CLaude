from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QScrollArea, QWidget, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QIcon

from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from .settings_manager import SettingsManager


class APIKeyDialog(QDialog):
    """First-run dialog for API key setup."""

    def __init__(self, settings_manager: SettingsManager, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings_manager
        self.api_keys: Dict[str, str] = {}

        self.setWindowTitle("Welcome to Stratum - API Setup")
        self.setModal(True)
        self.setFixedWidth(500)
        self.resize(500, 600)

        # Set window icon if available
        try:
            self.setWindowIcon(QIcon("assets/stratum.ico"))
        except:
            pass

        self._setup_ui()
        self._load_existing_keys()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_label = QLabel("Welcome to Stratum!")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)

        # Description
        desc_label = QLabel(
            "To get started, please enter your API keys for the AI providers you want to use.\n\n"
            "You can get API keys from:\n"
            "• OpenAI: https://platform.openai.com/api-keys\n"
            "• Anthropic (Claude): https://console.anthropic.com/\n\n"
            "Leave fields blank for providers you don't want to use."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666;")
        layout.addWidget(desc_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # API Key inputs
        self._add_api_key_input(layout, "OpenAI", "openai", "GPT-4, GPT-3.5")
        self._add_api_key_input(layout, "Claude (Anthropic)", "claude", "Claude 3, Claude 2")

        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator2)

        # Buttons
        button_layout = QHBoxLayout()

        save_button = QPushButton("Save & Continue")
        save_button.setDefault(True)
        save_button.clicked.connect(self._save_and_continue)
        button_layout.addWidget(save_button)

        skip_button = QPushButton("Skip for Now")
        skip_button.clicked.connect(self._skip_for_now)
        button_layout.addWidget(skip_button)

        layout.addLayout(button_layout)

        # Footer note
        footer_label = QLabel(
            "You can change these settings later in the Settings tab.\n"
            "Stratum will work with any combination of API keys."
        )
        footer_label.setWordWrap(True)
        footer_label.setStyleSheet("color: #888; font-size: 10px;")
        footer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer_label)

    def _add_api_key_input(self, parent_layout: QVBoxLayout, provider_name: str,
                          config_key: str, models: str) -> None:
        """Add an API key input section."""
        # Provider header
        provider_label = QLabel(f"{provider_name} API Key")
        provider_font = QFont()
        provider_font.setBold(True)
        provider_label.setFont(provider_font)
        parent_layout.addWidget(provider_label)

        # Model info
        model_label = QLabel(f"Models: {models}")
        model_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 5px;")
        parent_layout.addWidget(model_label)

        # Input field
        key_input = QLineEdit()
        key_input.setPlaceholderText(f"Enter your {provider_name} API key...")
        key_input.setEchoMode(QLineEdit.Password)  # Hide the key
        key_input.textChanged.connect(lambda text, key=config_key: self._on_key_changed(key, text))
        parent_layout.addWidget(key_input)

        # Store reference
        setattr(self, f"{config_key}_input", key_input)

        # Spacer
        parent_layout.addSpacing(10)

    def _on_key_changed(self, provider: str, key: str) -> None:
        """Handle API key input changes."""
        self.api_keys[provider] = key

    def _load_existing_keys(self) -> None:
        """Load any existing API keys."""
        try:
            openai_key = self.settings.config.get("openai", "api_key", fallback="")
            claude_key = self.settings.config.get("claude", "api_key", fallback="")

            if openai_key:
                self.api_keys["openai"] = openai_key
                self.openai_input.setText(openai_key)

            if claude_key:
                self.api_keys["claude"] = claude_key
                self.claude_input.setText(claude_key)
        except Exception as e:
            print(f"Error loading existing keys: {e}")

    def _save_and_continue(self) -> None:
        """Save the API keys and close the dialog."""
        try:
            # Update settings
            for provider, key in self.api_keys.items():
                if key.strip():  # Only save non-empty keys
                    if not self.settings.config.has_section(provider):
                        self.settings.config.add_section(provider)
                    self.settings.config.set(provider, "api_key", key.strip())

            # Save to file
            with open(self.settings._path, 'w', encoding='utf-8') as f:
                self.settings.config.write(f)

            self.accept()

        except Exception as e:
            QMessageBox.warning(
                self,
                "Save Error",
                f"Failed to save API keys: {str(e)}"
            )

    def _skip_for_now(self) -> None:
        """Skip API key setup for now."""
        reply = QMessageBox.question(
            self,
            "Skip API Setup",
            "Are you sure you want to skip API key setup?\n\n"
            "You can set them up later in the Settings tab, but some features won't work until you do.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.reject()

    @staticmethod
    def show_if_needed(settings_manager: SettingsManager, parent=None) -> bool:
        """Show the dialog if API keys are missing. Returns True if user completed setup."""
        # Check if we have any API keys
        has_openai = bool(settings_manager.config.get("openai", "api_key", fallback="").strip())
        has_claude = bool(settings_manager.config.get("claude", "api_key", fallback="").strip())

        if not has_openai and not has_claude:
            dialog = APIKeyDialog(settings_manager, parent)
            result = dialog.exec()
            return result == QDialog.Accepted

        return True  # Keys already exist
