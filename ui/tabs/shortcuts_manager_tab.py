from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QTextEdit, QGroupBox,
    QCheckBox, QComboBox, QMessageBox, QSplitter, QHeaderView
)
from PySide6.QtCore import Qt

from .base import BaseTab
from .adapters import ShortcutsAdapter


class ShortcutsManagerTab(BaseTab):
    """Full shortcuts manager for Stratum with CommandRegistry integration."""

    def __init__(self, shortcuts_adapter: ShortcutsAdapter):
        super().__init__()
        self._adapter = shortcuts_adapter
        self._current_command_id = None
        self._build_ui()
        self._load_commands()

    def _build_ui(self) -> None:
        """Build the full shortcuts management UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Command Shortcuts Manager")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        # Create splitter for table and editor
        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Vertical)

        # Top section - Commands table
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)

        table_label = QLabel("Registered Commands:")
        table_layout.addWidget(table_label)

        self.commands_table = QTableWidget()
        self.commands_table.setColumnCount(5)
        self.commands_table.setHorizontalHeaderLabels(["Label", "Action", "Hotkey", "Hotstring", "Tags"])
        self.commands_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.commands_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.commands_table.itemSelectionChanged.connect(self._on_command_selected)
        table_layout.addWidget(self.commands_table)

        # Table buttons
        table_buttons = QHBoxLayout()
        add_btn = QPushButton("Add New")
        add_btn.clicked.connect(self._add_new_command)
        table_buttons.addWidget(add_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_command)
        table_buttons.addWidget(delete_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_commands)
        table_buttons.addWidget(refresh_btn)

        table_buttons.addStretch()
        table_layout.addLayout(table_buttons)

        # Bottom section - Editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)

        editor_label = QLabel("Command Editor:")
        editor_layout.addWidget(editor_label)

        # Editor form
        form_layout = QVBoxLayout()

        # Label
        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("Label:"))
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Command display name")
        label_layout.addWidget(self.label_edit)
        form_layout.addLayout(label_layout)

        # Action
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("Action:"))
        self.action_edit = QLineEdit()
        self.action_edit.setPlaceholderText("e.g., ui.toggle_main, tts.speak_selection")
        action_layout.addWidget(self.action_edit)
        form_layout.addLayout(action_layout)

        # Hotkey builder
        hotkey_group = QGroupBox("Hotkey (Keyboard Shortcut)")
        hotkey_layout = QVBoxLayout()

        # Modifiers
        modifiers_layout = QHBoxLayout()
        self.ctrl_check = QCheckBox("Ctrl")
        self.alt_check = QCheckBox("Alt")
        self.shift_check = QCheckBox("Shift")
        self.win_check = QCheckBox("Win")
        modifiers_layout.addWidget(self.ctrl_check)
        modifiers_layout.addWidget(self.alt_check)
        modifiers_layout.addWidget(self.shift_check)
        modifiers_layout.addWidget(self.win_check)
        modifiers_layout.addStretch()
        hotkey_layout.addLayout(modifiers_layout)

        # Key
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Key:"))
        self.key_combo = QComboBox()
        self.key_combo.addItems([
            "", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
            "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
            "space", "enter", "tab", "escape", "backspace", "delete", "insert",
            "up", "down", "left", "right", "home", "end", "pageup", "pagedown"
        ])
        key_layout.addWidget(self.key_combo)
        key_layout.addStretch()
        hotkey_layout.addLayout(key_layout)

        hotkey_group.setLayout(hotkey_layout)
        form_layout.addWidget(hotkey_group)

        # Hotstring
        hotstring_layout = QHBoxLayout()
        hotstring_layout.addWidget(QLabel("Hotstring:"))
        self.hotstring_edit = QLineEdit()
        self.hotstring_edit.setPlaceholderText("Text expansion trigger (e.g., /sig)")
        hotstring_layout.addWidget(self.hotstring_edit)
        form_layout.addLayout(hotstring_layout)

        # Tags
        tags_layout = QHBoxLayout()
        tags_layout.addWidget(QLabel("Tags:"))
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Comma-separated tags (e.g., navigation, ui)")
        tags_layout.addWidget(self.tags_edit)
        form_layout.addLayout(tags_layout)

        editor_layout.addLayout(form_layout)

        # Editor buttons
        editor_buttons = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self._save_command)
        editor_buttons.addWidget(save_btn)

        clear_btn = QPushButton("Clear Form")
        clear_btn.clicked.connect(self._clear_form)
        editor_buttons.addWidget(clear_btn)

        editor_buttons.addStretch()
        editor_layout.addLayout(editor_buttons)

        # Add widgets to splitter
        splitter.addWidget(table_widget)
        splitter.addWidget(editor_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

    def _load_commands(self) -> None:
        """Load commands from adapter into table."""
        try:
            commands = self._adapter.get_all_shortcuts()
            self.commands_table.setRowCount(len(commands))

            for row, cmd in enumerate(commands):
                self.commands_table.setItem(row, 0, QTableWidgetItem(cmd['label']))
                self.commands_table.setItem(row, 1, QTableWidgetItem(cmd['action']))
                self.commands_table.setItem(row, 2, QTableWidgetItem(cmd['hotkey'] or ""))
                self.commands_table.setItem(row, 3, QTableWidgetItem(cmd['hotstring'] or ""))
                self.commands_table.setItem(row, 4, QTableWidgetItem(", ".join(cmd['tags'])))

                # Store command data in row
                for col in range(5):
                    item = self.commands_table.item(row, col)
                    if item:
                        item.setData(1, cmd)

        except Exception as e:
            print(f"Error loading commands: {e}")
            QMessageBox.warning(self, "Load Error", f"Failed to load commands: {str(e)}")

    def _on_command_selected(self) -> None:
        """Handle command selection from table."""
        current_row = self.commands_table.currentRow()
        if current_row >= 0:
            # Get command data from any cell in the row
            item = self.commands_table.item(current_row, 0)
            if item and item.data(1):
                cmd = item.data(1)
                self._current_command_id = cmd['id']
                self._load_command_into_form(cmd)

    def _load_command_into_form(self, cmd: dict) -> None:
        """Load command data into the editor form."""
        self.label_edit.setText(cmd['label'])
        self.action_edit.setText(cmd['action'])
        self.hotstring_edit.setText(cmd['hotstring'] or "")
        self.tags_edit.setText(", ".join(cmd['tags']))

        # Parse hotkey
        self._clear_hotkey_checks()
        hotkey = cmd['hotkey'] or ""
        if hotkey:
            parts = hotkey.split('+')
            key = parts[-1]  # Last part is the key
            modifiers = parts[:-1]  # Everything before is modifiers

            if 'ctrl' in modifiers:
                self.ctrl_check.setChecked(True)
            if 'alt' in modifiers:
                self.alt_check.setChecked(True)
            if 'shift' in modifiers:
                self.shift_check.setChecked(True)
            if 'win' in modifiers or 'windows' in modifiers:
                self.win_check.setChecked(True)

            self.key_combo.setCurrentText(key)

    def _clear_hotkey_checks(self) -> None:
        """Clear all hotkey modifier checkboxes."""
        self.ctrl_check.setChecked(False)
        self.alt_check.setChecked(False)
        self.shift_check.setChecked(False)
        self.win_check.setChecked(False)
        self.key_combo.setCurrentText("")

    def _build_hotkey_string(self) -> str:
        """Build hotkey string from checkboxes and key combo."""
        modifiers = []
        if self.ctrl_check.isChecked():
            modifiers.append("ctrl")
        if self.alt_check.isChecked():
            modifiers.append("alt")
        if self.shift_check.isChecked():
            modifiers.append("shift")
        if self.win_check.isChecked():
            modifiers.append("win")

        key = self.key_combo.currentText()
        if key and modifiers:
            return "+".join(modifiers) + "+" + key
        elif key:
            return key
        else:
            return ""

    def _add_new_command(self) -> None:
        """Add a new command."""
        self._current_command_id = None
        self._clear_form()

    def _save_command(self) -> None:
        """Save the current command."""
        label = self.label_edit.text().strip()
        action = self.action_edit.text().strip()

        if not label or not action:
            QMessageBox.warning(self, "Validation Error", "Label and Action are required.")
            return

        hotkey = self._build_hotkey_string()
        hotstring = self.hotstring_edit.text().strip()
        tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]

        try:
            if self._current_command_id:
                # Update existing
                success = self._adapter.registry.update_command(
                    self._current_command_id,
                    label=label,
                    action=action,
                    hotkey=hotkey,
                    hotstring=hotstring,
                    tags=tags
                )
                if success:
                    QMessageBox.information(self, "Success", "Command updated successfully!")
                else:
                    QMessageBox.warning(self, "Error", "Failed to update command.")
            else:
                # Add new
                cmd_id = self._adapter.add_shortcut(label, hotkey, action, hotstring, tags)
                if cmd_id:
                    QMessageBox.information(self, "Success", "Command added successfully!")
                    self._current_command_id = cmd_id
                else:
                    QMessageBox.warning(self, "Error", "Failed to add command.")

            self._load_commands()

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save command: {str(e)}")

    def _delete_command(self) -> None:
        """Delete the selected command."""
        current_row = self.commands_table.currentRow()
        if current_row >= 0:
            item = self.commands_table.item(current_row, 0)
            if item and item.data(1):
                cmd = item.data(1)
                command_id = cmd['id']

                reply = QMessageBox.question(
                    self, "Confirm Delete",
                    f"Delete command '{cmd['label']}'?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    try:
                        success = self._adapter.remove_shortcut(command_id)
                        if success:
                            QMessageBox.information(self, "Success", "Command deleted successfully!")
                            self._load_commands()
                            self._clear_form()
                        else:
                            QMessageBox.warning(self, "Error", "Failed to delete command.")
                    except Exception as e:
                        QMessageBox.critical(self, "Delete Error", f"Failed to delete command: {str(e)}")

    def _clear_form(self) -> None:
        """Clear the editor form."""
        self.label_edit.clear()
        self.action_edit.clear()
        self.hotstring_edit.clear()
        self.tags_edit.clear()
        self._clear_hotkey_checks()
        self._current_command_id = None
