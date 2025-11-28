# D:\Stratum\ui\main_window.py
from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMessageBox, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.command_registry import CommandRegistry
    from core.settings_manager import SettingsManager
    from core.vault_manager import VaultManager
    from core.ai_clients import AIClientManager
    from core.tts_engine import TTSEngine

# Import all working tab classes and adapters
from .tabs.chat_tab import ChatTab
from .tabs.audio_tab_simple import AudioTab
from .tabs.tts_preprocessor_tab import TTSPreprocessorTab
from .tabs.shortcuts_manager_tab import ShortcutsManagerTab
from .tabs.prompts_tab import PromptsTab
from .tabs.prompts_manager_tab import PromptsManagerTab
from .tabs.spelling_tab import SpellingTab
from .tabs.search_scraper_tab import SearchScraperTab
from .tabs.settings_tab import SettingsTab
# Temporarily using placeholders for complex tabs
# from .tabs.clipboard_window import ClipboardWindow
# from .tabs.window_control_panel import WindowControlPanel
from .tabs.adapters import OpenAIClientAdapter, TTSAdapter, PromptManagerAdapter, ShortcutsAdapter


class MainWindow(QMainWindow):
    def __init__(self,
                 settings: SettingsManager,
                 command_registry: CommandRegistry,
                 vault_manager: VaultManager,
                 ai_manager: AIClientManager,
                 tts_engine: TTSEngine) -> None:
        super().__init__()
        self.settings = settings
        self.command_registry = command_registry
        self.vault_manager = vault_manager
        self.ai_manager = ai_manager
        self.tts_engine = tts_engine

        self.setWindowTitle("Stratum")
        self.setGeometry(100, 100, 1400, 900)

        # Check for "always on top" setting
        always_on_top = settings.config.getboolean("stratum", "window_on_top", fallback=False)
        if always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self._setup_ui()
        self._register_command_handlers()

    def _setup_ui(self) -> None:
        """Setup the main user interface with all tabs."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        layout.addWidget(self.tab_widget)

        # Add all tabs in the specified order
        self._add_all_tabs()

    def _add_all_tabs(self) -> None:
        """Add all functional tabs in the correct order with Stratum backend wiring."""
        try:
            # 1. Chat Tab - uses AI manager
            chat_tab = ChatTab(self.ai_manager)
            self.tab_widget.addTab(chat_tab, "Chat")

            # 2. Voice Tab - uses TTS engine
            voice_tab = AudioTab(self.tts_engine)
            self.tab_widget.addTab(voice_tab, "Voice")

            # 3. TTS Preprocessor Tab - basic text preprocessing
            tts_prep_tab = TTSPreprocessorTab()
            self.tab_widget.addTab(tts_prep_tab, "TTS Prep")

            # 4. Shortcuts Tab - uses shortcuts adapter with command registry
            shortcuts_adapter = ShortcutsAdapter(self.command_registry)
            shortcuts_tab = ShortcutsManagerTab(shortcuts_adapter)
            self.tab_widget.addTab(shortcuts_tab, "Shortcuts")

            # 5. Prompts Tab - uses vault manager via adapter
            prompts_adapter = PromptManagerAdapter(self.vault_manager)
            prompts_tab = PromptsTab(prompts_adapter)
            self.tab_widget.addTab(prompts_tab, "Prompts")

            # 6. Prompts Manager Tab - uses vault manager via adapter
            prompts_manager_tab = PromptsManagerTab(prompts_adapter)
            self.tab_widget.addTab(prompts_manager_tab, "Prompts Mgr")

            # 7. Spelling Tab - basic text checking
            spelling_tab = SpellingTab()
            self.tab_widget.addTab(spelling_tab, "Spelling")

            # 8. Search Tab - placeholder for now
            search_tab = self._create_simple_placeholder("Search Tab", "Search and scraping functionality")
            self.tab_widget.addTab(search_tab, "Search")

            # 9. Clipboard Tab - placeholder for now
            clipboard_tab = self._create_simple_placeholder("Clipboard Tab", "Clipboard management functionality")
            self.tab_widget.addTab(clipboard_tab, "Clipboard")

            # 10. Window Manager Tab - placeholder for now
            window_tab = self._create_simple_placeholder("Window Manager", "Window control and automation")
            self.tab_widget.addTab(window_tab, "Windows")

            # 11. Vault Tab - uses vault manager directly
            vault_tab = self._create_vault_tab()
            self.tab_widget.addTab(vault_tab, "Vault")

            # 12. Settings Tab - uses settings manager
            settings_tab = self._create_settings_tab()
            self.tab_widget.addTab(settings_tab, "Settings")

        except Exception as e:
            print(f"Error creating tabs: {e}")
            import traceback
            traceback.print_exc()
            # Add a basic fallback tab
            fallback_tab = QWidget()
            layout = QVBoxLayout(fallback_tab)
            layout.addWidget(QMessageBox(self, text=f"Error loading tabs: {str(e)}"))
            self.tab_widget.addTab(fallback_tab, "Error")

    def _create_simple_placeholder(self, title: str, description: str) -> QWidget:
        """Create a simple placeholder tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label, alignment=Qt.AlignCenter)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin: 20px;")
        layout.addWidget(desc_label, alignment=Qt.AlignCenter)

        layout.addStretch()
        return widget

    def _create_vault_tab(self) -> QWidget:
        """Create the vault tab UI."""
        try:
            widget = QWidget()
            layout = QVBoxLayout(widget)

            title = QLabel("Vault - 6-Lane Deep Storage")
            title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
            layout.addWidget(title)

            # Lane selector
            from PySide6.QtWidgets import QListWidget, QHBoxLayout, QTextEdit, QPushButton
            lanes_layout = QHBoxLayout()
            self.vault_lane_list = QListWidget()

            # Get zone names from vault manager
            self.vault_manager.load()  # Ensure loaded
            for zone in self.vault_manager.zones.values():
                self.vault_lane_list.addItem(zone.name)

            self.vault_lane_list.itemSelectionChanged.connect(self._on_vault_lane_changed)
            lanes_layout.addWidget(self.vault_lane_list)

            # Item list and content
            content_layout = QVBoxLayout()
            self.vault_item_list = QListWidget()
            self.vault_item_list.itemDoubleClicked.connect(self._on_vault_item_selected)
            content_layout.addWidget(self.vault_item_list)

            self.vault_content = QTextEdit()
            self.vault_content.setReadOnly(True)
            content_layout.addWidget(self.vault_content)

            lanes_layout.addLayout(content_layout)
            layout.addLayout(lanes_layout)

            # Buttons
            buttons_layout = QHBoxLayout()
            copy_btn = QPushButton("Copy")
            copy_btn.clicked.connect(self._vault_copy_item)
            buttons_layout.addWidget(copy_btn)

            insert_btn = QPushButton("Insert")
            insert_btn.clicked.connect(self._vault_insert_item)
            buttons_layout.addWidget(insert_btn)

            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(self._vault_edit_item)
            buttons_layout.addWidget(edit_btn)

            layout.addLayout(buttons_layout)

            # Load initial lane if available
            if self.vault_lane_list.count() > 0:
                self.vault_lane_list.setCurrentRow(0)

            return widget
        except Exception as e:
            return self._create_error_tab("Vault", str(e))

    def _create_settings_tab(self) -> QWidget:
        """Create the settings tab."""
        try:
            # For now, create a simple settings placeholder
            widget = QWidget()
            layout = QVBoxLayout(widget)

            title = QLabel("Settings")
            title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
            layout.addWidget(title)

            # Basic settings info
            info_label = QLabel("Settings panel - API keys and preferences")
            info_label.setStyleSheet("color: #666;")
            layout.addWidget(info_label)

            # API key status
            status_layout = QVBoxLayout()
            openai_key = self.settings.get_api_key("openai")
            claude_key = self.settings.get_api_key("claude")

            openai_status = QLabel(f"OpenAI Key: {'✓ Set' if openai_key else '✗ Not set'}")
            claude_status = QLabel(f"Claude Key: {'✓ Set' if claude_key else '✗ Not set'}")

            status_layout.addWidget(openai_status)
            status_layout.addWidget(claude_status)
            layout.addLayout(status_layout)

            layout.addStretch()
            return widget
        except Exception as e:
            return self._create_error_tab("Settings", str(e))

    def _create_error_tab(self, tab_name: str, error_msg: str) -> QWidget:
        """Create an error tab for when tab creation fails."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        error_label = QLabel(f"Error loading {tab_name} tab")
        error_label.setStyleSheet("font-size: 14px; font-weight: bold; color: red; margin-bottom: 10px;")
        layout.addWidget(error_label, alignment=Qt.AlignCenter)

        error_details = QLabel(f"Details: {error_msg}")
        error_details.setWordWrap(True)
        error_details.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(error_details, alignment=Qt.AlignCenter)

        layout.addStretch()
        return widget


    def _register_command_handlers(self) -> None:
        """Register command handlers for system-wide actions."""
        # UI toggle (show/hide main window)
        self.command_registry.register_handler("ui.toggle_main", self._toggle_main_window)

    def _toggle_main_window(self) -> None:
        """Toggle main window visibility."""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    # Vault tab methods
    def _on_vault_lane_changed(self) -> None:
        """Handle vault lane selection change."""
        current_item = self.vault_lane_list.currentItem()
        if current_item:
            lane_name = current_item.text()
            self._load_vault_lane(lane_name)

    def _load_vault_lane(self, lane_name: str) -> None:
        """Load items for a specific vault lane."""
        self.vault_item_list.clear()

        # Find the zone by name
        zone = None
        for z in self.vault_manager.zones.values():
            if z.name == lane_name:
                zone = z
                break

        if zone:
            for item in zone.items:
                display_text = f"{item.label} ({'📌 ' if item.pinned else ''})"
                self.vault_item_list.addItem(display_text)

    def _on_vault_item_selected(self, item) -> None:
        """Handle vault item selection."""
        if not item:
            return

        # Find the selected zone
        current_lane_item = self.vault_lane_list.currentItem()
        if not current_lane_item:
            return

        lane_name = current_lane_item.text()
        zone = None
        for z in self.vault_manager.zones.values():
            if z.name == lane_name:
                zone = z
                break

        if zone:
            item_index = self.vault_item_list.row(item)
            if 0 <= item_index < len(zone.items):
                vault_item = zone.items[item_index]
                self.vault_content.setPlainText(vault_item.value)

    def _vault_copy_item(self) -> None:
        """Copy selected vault item content to clipboard."""
        content = self.vault_content.toPlainText()
        if content:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(content)

    def _vault_insert_item(self) -> None:
        """Insert vault item content at cursor (placeholder)."""
        QMessageBox.information(self, "Insert", "Insert functionality coming soon!")

    def _vault_edit_item(self) -> None:
        """Edit selected vault item (placeholder)."""
        QMessageBox.information(self, "Edit", "Edit functionality coming soon!")

    def closeEvent(self, event) -> None:
        """Handle application close."""
        # Save any pending settings
        try:
            self.settings._config.write(open(self.settings._path, 'w', encoding='utf-8'))
        except Exception:
            pass

        event.accept()


def create_main_window(settings: SettingsManager,
                      command_registry: CommandRegistry,
                      vault_manager: VaultManager,
                      ai_manager: AIClientManager,
                      tts_engine: TTSEngine) -> MainWindow:
    return MainWindow(
        settings=settings,
        command_registry=command_registry,
        vault_manager=vault_manager,
        ai_manager=ai_manager,
        tts_engine=tts_engine
    )