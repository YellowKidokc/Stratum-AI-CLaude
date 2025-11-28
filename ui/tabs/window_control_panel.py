"""
Window Control Panel

A side panel for managing window settings (always-on-top, size, position).
Can be docked to the floating player or used independently.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...services.window_manager import get_window_settings


class WindowControlPanel(QWidget):
    """Control panel for window management."""

    # Signals
    always_on_top_changed = Signal(bool)
    save_position_requested = Signal()
    save_size_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.window_settings = get_window_settings()
        self._setup_ui()
        self._load_current_settings()

    def _setup_ui(self) -> None:
        """Setup the UI."""
        # Window flags for floating behavior
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        
        self.setWindowTitle("🎮 Window Manager")
        
        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                color: white;
            }
            QGroupBox {
                border: 2px solid #007acc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #505050;
                border: 1px solid #007acc;
            }
            QPushButton:pressed {
                background-color: #007acc;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QLabel {
                color: #aaa;
                font-size: 11px;
            }
        """)
        
        # Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title = QLabel("🎮 Window Manager")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        main_layout.addWidget(title)
        
        # Always On Top Section
        on_top_group = QGroupBox("Always On Top")
        on_top_layout = QVBoxLayout()
        
        self.global_on_top_cb = QCheckBox("All Windows On Top")
        self.global_on_top_cb.setToolTip("Make all AI Hub windows stay on top")
        self.global_on_top_cb.stateChanged.connect(self._on_global_on_top_changed)
        on_top_layout.addWidget(self.global_on_top_cb)
        
        self.main_window_on_top_cb = QCheckBox("Main Window On Top")
        self.main_window_on_top_cb.setToolTip("Keep main AI Hub window on top")
        self.main_window_on_top_cb.stateChanged.connect(self._on_main_window_on_top_changed)
        on_top_layout.addWidget(self.main_window_on_top_cb)
        
        self.player_on_top_cb = QCheckBox("Floating Player On Top")
        self.player_on_top_cb.setToolTip("Keep floating player on top")
        self.player_on_top_cb.stateChanged.connect(self._on_player_on_top_changed)
        on_top_layout.addWidget(self.player_on_top_cb)
        
        on_top_group.setLayout(on_top_layout)
        main_layout.addWidget(on_top_group)
        
        # Position & Size Section
        geometry_group = QGroupBox("Position & Size")
        geometry_layout = QVBoxLayout()
        
        save_pos_btn = QPushButton("💾 Save Current Position")
        save_pos_btn.setToolTip("Remember current window positions")
        save_pos_btn.clicked.connect(self._on_save_position)
        geometry_layout.addWidget(save_pos_btn)
        
        save_size_btn = QPushButton("📏 Save Current Size")
        save_size_btn.setToolTip("Remember current window sizes")
        save_size_btn.clicked.connect(self._on_save_size)
        geometry_layout.addWidget(save_size_btn)
        
        save_all_btn = QPushButton("💾 Save Position & Size")
        save_all_btn.setToolTip("Remember everything about current windows")
        save_all_btn.clicked.connect(self._on_save_all)
        geometry_layout.addWidget(save_all_btn)
        
        geometry_group.setLayout(geometry_layout)
        main_layout.addWidget(geometry_group)
        
        # Info
        info_label = QLabel(
            "💡 Tip: Resize and move windows,\n"
            "then click 'Save' to remember.\n"
            "Settings persist across restarts."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; font-style: italic; font-size: 10px;")
        main_layout.addWidget(info_label)
        
        main_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("✖ Close")
        close_btn.clicked.connect(self.hide)
        main_layout.addWidget(close_btn)
        
        # Set size
        self.setFixedWidth(250)
        self.setMinimumHeight(400)

    def _load_current_settings(self) -> None:
        """Load current settings from window manager."""
        # Block signals while loading
        self.global_on_top_cb.blockSignals(True)
        self.main_window_on_top_cb.blockSignals(True)
        self.player_on_top_cb.blockSignals(True)
        
        # Load settings
        self.global_on_top_cb.setChecked(self.window_settings.get_global_always_on_top())
        self.main_window_on_top_cb.setChecked(self.window_settings.is_always_on_top("main_window"))
        self.player_on_top_cb.setChecked(self.window_settings.is_always_on_top("floating_player"))
        
        # Unblock signals
        self.global_on_top_cb.blockSignals(False)
        self.main_window_on_top_cb.blockSignals(False)
        self.player_on_top_cb.blockSignals(False)

    def _on_global_on_top_changed(self, state: int) -> None:
        """Handle global always-on-top toggle."""
        enabled = state == Qt.Checked
        self.window_settings.set_global_always_on_top(enabled)
        self.always_on_top_changed.emit(enabled)
        print(f"🎮 Global always-on-top: {enabled}")

    def _on_main_window_on_top_changed(self, state: int) -> None:
        """Handle main window always-on-top toggle."""
        enabled = state == Qt.Checked
        self.window_settings.set_always_on_top("main_window", enabled)
        self.always_on_top_changed.emit(enabled)
        print(f"🎮 Main window always-on-top: {enabled}")

    def _on_player_on_top_changed(self, state: int) -> None:
        """Handle floating player always-on-top toggle."""
        enabled = state == Qt.Checked
        self.window_settings.set_always_on_top("floating_player", enabled)
        self.always_on_top_changed.emit(enabled)
        print(f"🎮 Floating player always-on-top: {enabled}")

    def _on_save_position(self) -> None:
        """Save current window positions."""
        self.save_position_requested.emit()
        print("💾 Saving window positions...")

    def _on_save_size(self) -> None:
        """Save current window sizes."""
        self.save_size_requested.emit()
        print("💾 Saving window sizes...")

    def _on_save_all(self) -> None:
        """Save both position and size."""
        self.save_position_requested.emit()
        self.save_size_requested.emit()
        print("💾 Saving window geometry...")

    def refresh_settings(self) -> None:
        """Refresh displayed settings."""
        self._load_current_settings()
