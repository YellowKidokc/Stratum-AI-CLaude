"""
Settings Tab

Centralized settings panel for all toggleable options.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .base import BaseTab


class SettingsTab(BaseTab):
    """Settings and preferences tab."""

    # Signals
    auto_copy_changed = Signal(bool)
    show_notifications_changed = Signal(bool)
    auto_start_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_settings()

    def _build_ui(self) -> None:
        """Build the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("⚙️ Settings & Preferences")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # --- BEHAVIOR SETTINGS ---
        behavior_group = QGroupBox("🎯 Behavior")
        behavior_layout = QVBoxLayout()

        self.auto_copy_cb = QCheckBox("Auto-copy selected text when using TTS (CapsLock+A)")
        self.auto_copy_cb.setToolTip("Automatically copy text to clipboard when speaking it")
        self.auto_copy_cb.setChecked(True)  # Enabled by default
        self.auto_copy_cb.stateChanged.connect(self._on_auto_copy_changed)
        behavior_layout.addWidget(self.auto_copy_cb)

        self.show_notifications_cb = QCheckBox("Show notifications for TTS actions")
        self.show_notifications_cb.setToolTip("Display toast notifications when text is copied/spoken")
        self.show_notifications_cb.setChecked(True)
        self.show_notifications_cb.stateChanged.connect(self._on_notifications_changed)
        behavior_layout.addWidget(self.show_notifications_cb)

        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)

        # --- STARTUP SETTINGS ---
        startup_group = QGroupBox("🚀 Startup")
        startup_layout = QVBoxLayout()

        self.auto_start_cb = QCheckBox("Start AI Hub automatically when Windows starts")
        self.auto_start_cb.setToolTip("Add AI Hub to Windows startup")
        self.auto_start_cb.stateChanged.connect(self._on_auto_start_changed)
        startup_layout.addWidget(self.auto_start_cb)

        startup_info = QLabel(
            "💡 Tip: AI Hub will start minimized to system tray.\n"
            "Use Ctrl+Alt+G to show the window anytime."
        )
        startup_info.setStyleSheet("color: #888; font-style: italic; font-size: 11px;")
        startup_info.setWordWrap(True)
        startup_layout.addWidget(startup_info)

        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)

        # --- HOTKEYS INFO ---
        hotkeys_group = QGroupBox("⌨️ Hotkeys Reference")
        hotkeys_layout = QVBoxLayout()

        hotkeys_text = QLabel(
            "<b>CapsLock+A</b> - Speak selected text (with auto-copy)<br>"
            "<b>Ctrl+Alt+G</b> - Show/Hide main window<br>"
            "<b>Ctrl+Space</b> - Fix grammar with AI<br>"
            "<b>Ctrl+Shift+K</b> - Open prompt navigator<br>"
            "<b>Ctrl+Alt+H</b> - Toggle hotstrings<br>"
            "<br>"
            "<i>Custom shortcuts can be created in the Shortcuts tab</i>"
        )
        hotkeys_text.setWordWrap(True)
        hotkeys_layout.addWidget(hotkeys_text)

        hotkeys_group.setLayout(hotkeys_layout)
        layout.addWidget(hotkeys_group)

        # --- ACTIONS ---
        actions_group = QGroupBox("🔧 Actions")
        actions_layout = QVBoxLayout()

        open_window_manager_btn = QPushButton("🎮 Open Window Manager")
        open_window_manager_btn.setToolTip("Manage window positions and always-on-top settings")
        open_window_manager_btn.clicked.connect(self._open_window_manager)
        actions_layout.addWidget(open_window_manager_btn)

        open_config_folder_btn = QPushButton("📁 Open Config Folder")
        open_config_folder_btn.setToolTip("Open the config folder in File Explorer")
        open_config_folder_btn.clicked.connect(self._open_config_folder)
        actions_layout.addWidget(open_config_folder_btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        # --- INFO ---
        info_label = QLabel(
            "AI Hub v0.2.0 - Voice-Enabled Personal Assistant<br>"
            "Settings are saved automatically"
        )
        info_label.setStyleSheet("color: #666; font-size: 10px; margin-top: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        layout.addStretch()

    def _load_settings(self) -> None:
        """Load settings from config."""
        # TODO: Load from config file
        # For now, using defaults
        pass

    def _on_auto_copy_changed(self, state: int) -> None:
        """Handle auto-copy toggle."""
        from PySide6.QtCore import Qt
        enabled = state == Qt.Checked
        self.auto_copy_changed.emit(enabled)
        print(f"⚙️ Auto-copy: {enabled}")

    def _on_notifications_changed(self, state: int) -> None:
        """Handle notifications toggle."""
        from PySide6.QtCore import Qt
        enabled = state == Qt.Checked
        self.show_notifications_changed.emit(enabled)
        print(f"⚙️ Notifications: {enabled}")

    def _on_auto_start_changed(self, state: int) -> None:
        """Handle auto-start toggle."""
        from PySide6.QtCore import Qt
        enabled = state == Qt.Checked
        self.auto_start_changed.emit(enabled)
        
        if enabled:
            self._enable_auto_start()
        else:
            self._disable_auto_start()

    def _enable_auto_start(self) -> None:
        """Enable Windows auto-start."""
        import os
        import winreg
        from pathlib import Path

        try:
            # Get path to Start_AI_Hub.bat
            bat_path = Path(__file__).parent.parent.parent.parent / "Start_AI_Hub.bat"
            
            if not bat_path.exists():
                print(f"⚠️ Startup script not found: {bat_path}")
                return

            # Add to Windows startup registry
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.SetValueEx(key, "AI Hub", 0, winreg.REG_SZ, str(bat_path))
            winreg.CloseKey(key)
            
            print(f"✅ Auto-start enabled: {bat_path}")
            
        except Exception as e:
            print(f"❌ Could not enable auto-start: {e}")

    def _disable_auto_start(self) -> None:
        """Disable Windows auto-start."""
        import winreg

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            try:
                winreg.DeleteValue(key, "AI Hub")
                print("✅ Auto-start disabled")
            except FileNotFoundError:
                print("⚠️ Auto-start was not enabled")
            
            winreg.CloseKey(key)
            
        except Exception as e:
            print(f"❌ Could not disable auto-start: {e}")

    def _open_window_manager(self) -> None:
        """Open the window manager panel."""
        # Get main window and show window manager
        main_window = self.window()
        if hasattr(main_window, 'window_control_panel'):
            main_window.window_control_panel.show()
            main_window.window_control_panel.raise_()
            main_window.window_control_panel.activateWindow()

    def _open_config_folder(self) -> None:
        """Open config folder in File Explorer."""
        import os
        import subprocess
        from pathlib import Path

        config_folder = Path(__file__).parent.parent.parent.parent / "config"
        config_folder.mkdir(exist_ok=True)
        
        try:
            subprocess.Popen(f'explorer "{config_folder}"')
            print(f"📁 Opened config folder: {config_folder}")
        except Exception as e:
            print(f"❌ Could not open config folder: {e}")
