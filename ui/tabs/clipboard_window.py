"""
Clipboard Manager Window

Floating window showing clipboard history with pin, hotkey, and preview features.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit,
    QSplitter, QMessageBox, QInputDialog, QFrame
)

from ...services.clipboard_manager import ClipboardManager, ClipboardItem


class ClipboardItemWidget(QWidget):
    """Widget for a single clipboard item with actions."""
    
    copy_requested = Signal(str)  # item_id
    pin_requested = Signal(str)   # item_id
    delete_requested = Signal(str)  # item_id
    preview_requested = Signal(str)  # item_id
    hotkey_requested = Signal(str)  # item_id
    
    def __init__(self, item: ClipboardItem):
        super().__init__()
        self.item = item
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Left side: Content preview
        content_layout = QVBoxLayout()
        
        # Label (if set)
        if self.item.label:
            label_text = QLabel(f"🏷️ {self.item.label}")
            label_text.setStyleSheet("color: #4CAF50; font-weight: bold;")
            content_layout.addWidget(label_text)
        
        # Content preview
        preview = QLabel(self.item.preview(80))
        preview.setWordWrap(True)
        preview.setStyleSheet("color: #E0E0E0; padding: 5px;")
        content_layout.addWidget(preview)
        
        # Hotkey indicator
        if self.item.hotkey:
            hotkey_label = QLabel(f"⌨️ {self.item.hotkey}")
            hotkey_label.setStyleSheet("color: #FF9800; font-size: 10px;")
            content_layout.addWidget(hotkey_label)
        
        layout.addLayout(content_layout, stretch=3)
        
        # Right side: Action buttons
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(3)
        
        # Copy button
        btn_copy = QPushButton("📋")
        btn_copy.setToolTip("Copy to clipboard")
        btn_copy.setFixedSize(35, 35)
        btn_copy.clicked.connect(lambda: self.copy_requested.emit(self.item.id))
        actions_layout.addWidget(btn_copy)
        
        # Pin button
        pin_icon = "📌" if self.item.pinned else "📍"
        btn_pin = QPushButton(pin_icon)
        btn_pin.setToolTip("Pin/Unpin")
        btn_pin.setFixedSize(35, 35)
        btn_pin.clicked.connect(lambda: self.pin_requested.emit(self.item.id))
        if self.item.pinned:
            btn_pin.setStyleSheet("background-color: #4CAF50;")
        actions_layout.addWidget(btn_pin)
        
        # Hotkey button
        btn_hotkey = QPushButton("⌨️")
        btn_hotkey.setToolTip("Set hotkey")
        btn_hotkey.setFixedSize(35, 35)
        btn_hotkey.clicked.connect(lambda: self.hotkey_requested.emit(self.item.id))
        actions_layout.addWidget(btn_hotkey)
        
        # Preview button
        btn_preview = QPushButton("🔍")
        btn_preview.setToolTip("Double-click to preview")
        btn_preview.setFixedSize(35, 35)
        btn_preview.clicked.connect(lambda: self.preview_requested.emit(self.item.id))
        actions_layout.addWidget(btn_preview)
        
        # Delete button (only if not pinned)
        if not self.item.pinned:
            btn_delete = QPushButton("🗑️")
            btn_delete.setToolTip("Delete")
            btn_delete.setFixedSize(35, 35)
            btn_delete.clicked.connect(lambda: self.delete_requested.emit(self.item.id))
            btn_delete.setStyleSheet("background-color: #F44336;")
            actions_layout.addWidget(btn_delete)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout, stretch=1)


class ClipboardWindow(QWidget):
    """Main clipboard manager window."""
    
    def __init__(self, storage_path: Path):
        super().__init__()
        self.manager = ClipboardManager(storage_path, max_history=100)
        self.manager.on_new_item = self._on_new_item
        
        self._setup_ui()
        self._setup_monitoring()
        self._refresh_list()
        
        # Window settings
        self.setWindowTitle("📋 Clipboard Manager")
        self.resize(800, 600)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("📋 Clipboard History")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header.addWidget(title)
        
        # Clear button
        btn_clear = QPushButton("🗑️ Clear Unpinned")
        btn_clear.clicked.connect(self._clear_unpinned)
        header.addWidget(btn_clear)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search clipboard...")
        self.search_box.textChanged.connect(self._on_search)
        header.addWidget(self.search_box)
        
        layout.addLayout(header)
        
        # Splitter: List on left, Preview on right
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Clipboard list
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                border: 1px solid #3E3E3E;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #2E2E2E;
            }
            QListWidget::item:selected {
                background-color: #2D5F8D;
            }
            QListWidget::item:hover {
                background-color: #2E2E2E;
            }
        """)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        splitter.addWidget(self.list_widget)
        
        # Right: Preview panel
        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        
        preview_label = QLabel("📄 Preview")
        preview_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        preview_layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #3E3E3E;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        preview_layout.addWidget(self.preview_text)
        
        # Preview actions
        preview_actions = QHBoxLayout()
        
        btn_copy_preview = QPushButton("📋 Copy")
        btn_copy_preview.clicked.connect(self._copy_preview)
        preview_actions.addWidget(btn_copy_preview)
        
        btn_label = QPushButton("🏷️ Set Label")
        btn_label.clicked.connect(self._set_label)
        preview_actions.addWidget(btn_label)
        
        preview_actions.addStretch()
        preview_layout.addLayout(preview_actions)
        
        splitter.addWidget(preview_panel)
        splitter.setSizes([500, 300])
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(self.status_label)
    
    def _setup_monitoring(self):
        """Start clipboard monitoring."""
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self._check_clipboard)
        self.monitor_timer.start(1000)  # Check every second
    
    def _check_clipboard(self):
        """Check for new clipboard content."""
        item = self.manager.check_clipboard()
        if item:
            self._refresh_list()
    
    def _on_new_item(self, item: ClipboardItem):
        """Called when new item is added."""
        self.status_label.setText(f"✅ New clipboard item: {item.preview(30)}")
    
    def _refresh_list(self):
        """Refresh the clipboard list."""
        self.list_widget.clear()
        
        # Add pinned items first
        pinned = self.manager.get_pinned_items()
        if pinned:
            header = QListWidgetItem("📌 PINNED")
            header.setFlags(Qt.NoItemFlags)
            header.setBackground(QColor("#2E4053"))
            self.list_widget.addItem(header)
            
            for item in pinned:
                self._add_item_to_list(item)
        
        # Add recent items
        recent = self.manager.get_recent_items(50)
        if recent:
            header = QListWidgetItem("🕒 RECENT")
            header.setFlags(Qt.NoItemFlags)
            header.setBackground(QColor("#2E4053"))
            self.list_widget.addItem(header)
            
            for item in recent:
                self._add_item_to_list(item)
    
    def _add_item_to_list(self, item: ClipboardItem):
        """Add an item to the list."""
        list_item = QListWidgetItem(self.list_widget)
        widget = ClipboardItemWidget(item)
        
        # Connect signals
        widget.copy_requested.connect(self._on_copy)
        widget.pin_requested.connect(self._on_pin)
        widget.delete_requested.connect(self._on_delete)
        widget.preview_requested.connect(self._on_preview)
        widget.hotkey_requested.connect(self._on_set_hotkey)
        
        list_item.setSizeHint(widget.sizeHint())
        list_item.setData(Qt.UserRole, item.id)
        self.list_widget.setItemWidget(list_item, widget)
    
    def _on_copy(self, item_id: str):
        """Copy item to clipboard."""
        if self.manager.copy_to_clipboard(item_id):
            self.status_label.setText("✅ Copied to clipboard!")
    
    def _on_pin(self, item_id: str):
        """Toggle pin status."""
        pinned = self.manager.toggle_pin(item_id)
        self._refresh_list()
        status = "pinned" if pinned else "unpinned"
        self.status_label.setText(f"📌 Item {status}")
    
    def _on_delete(self, item_id: str):
        """Delete item."""
        if self.manager.delete_item(item_id):
            self._refresh_list()
            self.status_label.setText("🗑️ Item deleted")
    
    def _on_preview(self, item_id: str):
        """Show item preview."""
        item = self.manager.get_item_by_id(item_id)
        if item:
            self.preview_text.setPlainText(item.content)
            self.status_label.setText(f"👁️ Previewing: {item.preview(30)}")
    
    def _on_item_double_clicked(self, list_item: QListWidgetItem):
        """Handle double-click on item."""
        item_id = list_item.data(Qt.UserRole)
        if item_id:
            self._on_preview(item_id)
    
    def _on_set_hotkey(self, item_id: str):
        """Set hotkey for item."""
        item = self.manager.get_item_by_id(item_id)
        if not item:
            return
        
        current = item.hotkey or ""
        hotkey, ok = QInputDialog.getText(
            self,
            "Set Hotkey",
            f"Enter hotkey (e.g., 'ctrl+shift+1'):\n\nPreview: {item.preview(50)}",
            text=current
        )
        
        if ok:
            if hotkey.strip():
                self.manager.set_hotkey(item_id, hotkey.strip())
                self.status_label.setText(f"⌨️ Hotkey set: {hotkey}")
            else:
                self.manager.set_hotkey(item_id, None)
                self.status_label.setText("⌨️ Hotkey removed")
            self._refresh_list()
    
    def _set_label(self):
        """Set label for current preview item."""
        content = self.preview_text.toPlainText()
        if not content:
            return
        
        # Find item by content
        for item in self.manager.items:
            if item.content == content:
                label, ok = QInputDialog.getText(
                    self,
                    "Set Label",
                    "Enter a label for this item:",
                    text=item.label or ""
                )
                if ok:
                    if label.strip():
                        self.manager.set_label(item.id, label.strip())
                        self.status_label.setText(f"🏷️ Label set: {label}")
                    else:
                        self.manager.set_label(item.id, None)
                        self.status_label.setText("🏷️ Label removed")
                    self._refresh_list()
                break
    
    def _copy_preview(self):
        """Copy preview content to clipboard."""
        content = self.preview_text.toPlainText()
        if content:
            import pyperclip
            pyperclip.copy(content)
            self.status_label.setText("✅ Preview copied to clipboard!")
    
    def _clear_unpinned(self):
        """Clear all unpinned items."""
        reply = QMessageBox.question(
            self,
            "Clear Unpinned",
            "Delete all unpinned clipboard items?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            count = self.manager.clear_unpinned()
            self._refresh_list()
            self.status_label.setText(f"🗑️ Cleared {count} items")
    
    def _on_search(self, text: str):
        """Filter items by search text."""
        # Simple search - could be enhanced
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget and hasattr(widget, 'item'):
                visible = text.lower() in widget.item.content.lower()
                item.setHidden(not visible)
