"""
Prompts Manager Tab - Complete CRUD interface for managing AI prompts
No hardcoding needed - everything managed through GUI
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QCheckBox,
    QDoubleSpinBox,
)

from .base import BaseTab
from .adapters import PromptManagerAdapter


class PromptEditDialog(QDialog):
    """Dialog for creating/editing a prompt."""
    
    def __init__(self, prompt_data=None, parent=None):
        super().__init__(parent)
        self.prompt_data = prompt_data or {}
        self.setWindowTitle("Edit Prompt" if prompt_data else "New Prompt")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self._setup_ui()
        self._load_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout
        form = QFormLayout()
        
        # Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g., Fix Grammar")
        form.addRow("📝 Title:", self.title_input)
        
        # Description
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Brief description of what this prompt does")
        form.addRow("📄 Description:", self.description_input)
        
        layout.addLayout(form)
        
        # System message
        system_group = QGroupBox("🤖 System Message (Optional)")
        system_layout = QVBoxLayout()
        system_layout.addWidget(QLabel("Sets the AI's behavior and role:"))
        self.system_input = QTextEdit()
        self.system_input.setPlaceholderText(
            "e.g., You are a professional editor. Be concise and clear."
        )
        self.system_input.setMaximumHeight(80)
        system_layout.addWidget(self.system_input)
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)
        
        # User prompt
        prompt_group = QGroupBox("💬 User Prompt")
        prompt_layout = QVBoxLayout()
        prompt_layout.addWidget(QLabel("The instruction sent to AI (selected text will be appended):"))
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText(
            "e.g., Fix the spelling and grammar in the following text:\n\n"
        )
        self.prompt_input.setMinimumHeight(100)
        prompt_layout.addWidget(self.prompt_input)
        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group)
        
        # Options
        options_group = QGroupBox("⚙️ Options")
        options_layout = QFormLayout()
        
        # Replace checkbox
        self.replace_checkbox = QCheckBox("Replace selected text with result")
        self.replace_checkbox.setChecked(True)
        options_layout.addRow("Replace:", self.replace_checkbox)
        
        # Temperature
        temp_layout = QHBoxLayout()
        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(0.0, 2.0)
        self.temperature_input.setSingleStep(0.1)
        self.temperature_input.setValue(0.2)
        self.temperature_input.setDecimals(1)
        temp_layout.addWidget(self.temperature_input)
        temp_layout.addWidget(QLabel("(0.0 = focused, 2.0 = creative)"))
        options_layout.addRow("🌡️ Temperature:", temp_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Help text
        help_text = QLabel(
            "💡 Tip: Use clear, specific instructions. The selected text will be "
            "automatically added after your prompt."
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #888; font-size: 10px; padding: 10px;")
        layout.addWidget(help_text)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def _load_data(self):
        """Load existing prompt data."""
        if not self.prompt_data:
            return
            
        self.title_input.setText(self.prompt_data.get("title", ""))
        self.description_input.setText(self.prompt_data.get("description", ""))
        self.system_input.setPlainText(self.prompt_data.get("system", ""))
        self.prompt_input.setPlainText(self.prompt_data.get("prompt", ""))
        self.replace_checkbox.setChecked(self.prompt_data.get("replace", True))
        self.temperature_input.setValue(self.prompt_data.get("temperature", 0.2))
        
    def _save(self):
        """Validate and save."""
        title = self.title_input.text().strip()
        prompt = self.prompt_input.toPlainText().strip()
        
        if not title:
            QMessageBox.warning(self, "Error", "Please enter a title!")
            return
            
        if not prompt:
            QMessageBox.warning(self, "Error", "Please enter a prompt!")
            return
            
        self.result = {
            "title": title,
            "description": self.description_input.text().strip(),
            "system": self.system_input.toPlainText().strip(),
            "prompt": prompt,
            "replace": self.replace_checkbox.isChecked(),
            "temperature": self.temperature_input.value(),
        }
        
        self.accept()


class PromptsManagerTab(BaseTab):
    """Simplified prompts manager interface."""

    def __init__(self, prompt_adapter: PromptManagerAdapter):
        super().__init__()
        self._adapter = prompt_adapter
        self._build_ui()

    def _build_ui(self):
        """Build simplified prompts manager UI."""
        from PySide6.QtWidgets import QVBoxLayout, QLabel, QPushButton, QListWidget

        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Prompts Manager")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        # Prompts list
        self.prompts_list = QListWidget()
        self._load_prompts()
        layout.addWidget(self.prompts_list)

        # Buttons
        buttons_layout = QHBoxLayout()
        add_btn = QPushButton("Add Prompt")
        add_btn.clicked.connect(self._add_prompt)
        buttons_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit Prompt")
        edit_btn.clicked.connect(self._edit_prompt)
        buttons_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete Prompt")
        delete_btn.clicked.connect(self._delete_prompt)
        buttons_layout.addWidget(delete_btn)

        layout.addLayout(buttons_layout)

    def _load_prompts(self):
        """Load prompts from adapter."""
        self.prompts_list.clear()
        prompts = self._adapter.get_all_prompts()

        for prompt in prompts:
            from PySide6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(f"{prompt['title']}")
            item.setData(1, prompt)
            self.prompts_list.addItem(item)

    def _add_prompt(self):
        """Add a new prompt."""
        from PySide6.QtWidgets import QInputDialog, QTextEdit, QDialog, QVBoxLayout, QDialogButtonBox
        title, ok = QInputDialog.getText(self, "Add Prompt", "Prompt title:")
        if ok and title:
            # For now, just add a simple prompt
            prompt_id = self._adapter.save_prompt(title, f"Content for {title}", ["user"])
            self._load_prompts()

    def _edit_prompt(self):
        """Edit selected prompt."""
        QMessageBox.information(self, "Edit", "Edit functionality coming soon!")

    def _delete_prompt(self):
        """Delete selected prompt."""
        current_item = self.prompts_list.currentItem()
        if current_item:
            prompt_data = current_item.data(1)
            if prompt_data:
                # This would need to be implemented in the adapter
                QMessageBox.information(self, "Delete", "Delete functionality coming soon!")
        else:
            QMessageBox.warning(self, "No Selection", "Please select a prompt to delete.")
        
    def _get_prompts_file(self) -> Path:
        """Get prompts storage file."""
        config_dir = Path(__file__).parent.parent.parent.parent / "config"
        config_dir.mkdir(exist_ok=True)
        return config_dir / "prompts_manager.json"
        
    def _build_ui(self):
        layout = QHBoxLayout(self)
        
        # Left side - Prompt list
        left_layout = QVBoxLayout()
        
        # Header
        header = QLabel("📝 AI Prompts Manager")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        left_layout.addWidget(header)
        
        info = QLabel(
            "Create and manage AI prompts. Select text anywhere, then run a prompt "
            "to transform it with AI."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; padding: 5px 10px; font-size: 11px;")
        left_layout.addWidget(info)
        
        # Prompt list
        self.prompt_list = QListWidget()
        self.prompt_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.prompt_list.itemDoubleClicked.connect(self._on_edit_clicked)
        left_layout.addWidget(self.prompt_list)
        
        # List buttons
        list_buttons = QHBoxLayout()
        
        self.move_up_btn = QPushButton("⬆️ Move Up")
        self.move_up_btn.clicked.connect(self._move_up)
        list_buttons.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("⬇️ Move Down")
        self.move_down_btn.clicked.connect(self._move_down)
        list_buttons.addWidget(self.move_down_btn)
        
        left_layout.addLayout(list_buttons)
        
        # Action buttons
        action_buttons = QHBoxLayout()
        
        new_btn = QPushButton("➕ New Prompt")
        new_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        new_btn.clicked.connect(self._on_new_clicked)
        action_buttons.addWidget(new_btn)
        
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self._on_edit_clicked)
        action_buttons.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        action_buttons.addWidget(self.delete_btn)
        
        left_layout.addLayout(action_buttons)
        
        layout.addLayout(left_layout, 2)
        
        # Right side - Preview and run
        right_layout = QVBoxLayout()
        
        # Preview group
        preview_group = QGroupBox("👁️ Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_title = QLabel("Select a prompt to preview")
        self.preview_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        preview_layout.addWidget(self.preview_title)
        
        self.preview_description = QLabel("")
        self.preview_description.setWordWrap(True)
        self.preview_description.setStyleSheet("color: #888; font-size: 11px;")
        preview_layout.addWidget(self.preview_description)
        
        preview_layout.addWidget(QLabel("\n🤖 System:"))
        self.preview_system = QTextEdit()
        self.preview_system.setReadOnly(True)
        self.preview_system.setMaximumHeight(60)
        preview_layout.addWidget(self.preview_system)
        
        preview_layout.addWidget(QLabel("\n💬 Prompt:"))
        self.preview_prompt = QTextEdit()
        self.preview_prompt.setReadOnly(True)
        self.preview_prompt.setMaximumHeight(100)
        preview_layout.addWidget(self.preview_prompt)
        
        preview_layout.addWidget(QLabel("\n⚙️ Settings:"))
        self.preview_settings = QLabel("")
        self.preview_settings.setStyleSheet("font-size: 10px; color: #888;")
        preview_layout.addWidget(self.preview_settings)
        
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)
        
        # Run button
        self.run_btn = QPushButton("▶️ Run on Selected Text")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.run_btn.clicked.connect(self._on_run_clicked)
        right_layout.addWidget(self.run_btn)
        
        # Status
        self.status_label = QLabel("💡 Select text in any app, then click Run")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 10px; color: #888;")
        right_layout.addWidget(self.status_label)
        
        layout.addLayout(right_layout, 1)
        
        self._update_buttons()
        
    def _populate_list(self):
        """Populate the prompt list."""
        self.prompt_list.clear()
        for i, prompt in enumerate(self._prompts):
            title = prompt.get("title", f"Prompt {i+1}")
            item = QListWidgetItem(f"{i+1}. {title}")
            item.setData(Qt.UserRole, i)
            self.prompt_list.addItem(item)
            
    def _on_selection_changed(self):
        """Update preview when selection changes."""
        self._update_buttons()
        self._update_preview()
        
    def _update_preview(self):
        """Update the preview panel."""
        current = self.prompt_list.currentItem()
        if not current:
            self.preview_title.setText("Select a prompt to preview")
            self.preview_description.setText("")
            self.preview_system.clear()
            self.preview_prompt.clear()
            self.preview_settings.setText("")
            return
            
        idx = current.data(Qt.UserRole)
        if idx < 0 or idx >= len(self._prompts):
            return
            
        prompt = self._prompts[idx]
        
        self.preview_title.setText(prompt.get("title", "Untitled"))
        self.preview_description.setText(prompt.get("description", "No description"))
        self.preview_system.setPlainText(prompt.get("system", "(none)"))
        self.preview_prompt.setPlainText(prompt.get("prompt", ""))
        
        replace = "✅ Replace text" if prompt.get("replace", True) else "📋 Show in popup"
        temp = prompt.get("temperature", 0.2)
        self.preview_settings.setText(f"{replace} • Temperature: {temp}")
        
    def _update_buttons(self):
        """Update button states."""
        has_selection = self.prompt_list.currentItem() is not None
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.run_btn.setEnabled(has_selection)
        
        idx = self.prompt_list.currentRow()
        self.move_up_btn.setEnabled(idx > 0)
        self.move_down_btn.setEnabled(idx >= 0 and idx < len(self._prompts) - 1)
        
    def _on_new_clicked(self):
        """Create new prompt."""
        dialog = PromptEditDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._prompts.append(dialog.result)
            self._save_prompts()
            self._populate_list()
            self.prompt_list.setCurrentRow(len(self._prompts) - 1)
            self.status_label.setText("✅ Prompt created successfully!")
            
    def _on_edit_clicked(self):
        """Edit selected prompt."""
        current = self.prompt_list.currentItem()
        if not current:
            return
            
        idx = current.data(Qt.UserRole)
        if idx < 0 or idx >= len(self._prompts):
            return
            
        dialog = PromptEditDialog(self._prompts[idx], parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._prompts[idx] = dialog.result
            self._save_prompts()
            self._populate_list()
            self.prompt_list.setCurrentRow(idx)
            self.status_label.setText("✅ Prompt updated successfully!")
            
    def _on_delete_clicked(self):
        """Delete selected prompt."""
        current = self.prompt_list.currentItem()
        if not current:
            return
            
        idx = current.data(Qt.UserRole)
        if idx < 0 or idx >= len(self._prompts):
            return
            
        prompt = self._prompts[idx]
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete prompt '{prompt.get('title', 'Untitled')}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._prompts.pop(idx)
            self._save_prompts()
            self._populate_list()
            self.status_label.setText("✅ Prompt deleted!")
            
    def _move_up(self):
        """Move prompt up in list."""
        idx = self.prompt_list.currentRow()
        if idx <= 0:
            return
            
        self._prompts[idx], self._prompts[idx-1] = self._prompts[idx-1], self._prompts[idx]
        self._save_prompts()
        self._populate_list()
        self.prompt_list.setCurrentRow(idx - 1)
        
    def _move_down(self):
        """Move prompt down in list."""
        idx = self.prompt_list.currentRow()
        if idx < 0 or idx >= len(self._prompts) - 1:
            return
            
        self._prompts[idx], self._prompts[idx+1] = self._prompts[idx+1], self._prompts[idx]
        self._save_prompts()
        self._populate_list()
        self.prompt_list.setCurrentRow(idx + 1)
        
    def _on_run_clicked(self):
        """Run selected prompt on selected text."""
        current = self.prompt_list.currentItem()
        if not current:
            return
            
        idx = current.data(Qt.UserRole)
        if idx < 0 or idx >= len(self._prompts):
            return
            
        prompt = self._prompts[idx]
        selection = get_selection().text
        
        if not selection.strip():
            QMessageBox.warning(
                self,
                "No Text Selected",
                "Please select some text in any application first!"
            )
            return
            
        self.status_label.setText("⏳ Processing with AI...")
        self.run_btn.setEnabled(False)
        
        def run():
            try:
                # Build message
                system = prompt.get("system", "").strip() or None
                user_message = prompt.get("prompt", "") + "\n\n" + selection
                temperature = prompt.get("temperature", 0.2)
                
                # Call AI
                output = self._client.chat(system, user_message, temperature)
                
                if not output.strip():
                    self.status_label.setText("❌ No response from AI")
                    return
                    
                # Handle result
                if prompt.get("replace", True):
                    replace_selection(output)
                    self.status_label.setText("✅ Text replaced!")
                else:
                    ResultPopup.show_text(prompt.get("title", "Result"), output)
                    self.status_label.setText("✅ Result shown in popup!")
                    
            except Exception as e:
                self.status_label.setText(f"❌ Error: {str(e)}")
            finally:
                self.run_btn.setEnabled(True)
                
        threading.Thread(target=run, daemon=True).start()
        
    def _save_prompts(self):
        """Save prompts to file."""
        try:
            with open(self._prompts_file, "w") as f:
                json.dump(self._prompts, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save prompts: {e}")
            
    def _load_prompts(self):
        """Load prompts from file."""
        if self._prompts_file.exists():
            try:
                with open(self._prompts_file, "r") as f:
                    self._prompts = json.load(f)
                return
            except Exception as e:
                print(f"Error loading prompts: {e}")
                
        # Create default prompts
        self._prompts = [
            {
                "title": "Fix Spelling & Grammar",
                "description": "Correct spelling and grammar errors",
                "system": "You are a professional editor. Reply ONLY with the corrected text—no explanations.",
                "prompt": "Fix the spelling and grammar in the following text:",
                "replace": True,
                "temperature": 0.0,
            },
            {
                "title": "Make Professional",
                "description": "Rewrite in a professional tone",
                "system": "",
                "prompt": "Rewrite the following text in a professional, business-appropriate tone:",
                "replace": True,
                "temperature": 0.2,
            },
            {
                "title": "Simplify",
                "description": "Make text simpler and clearer",
                "system": "",
                "prompt": "Simplify the following text. Use simple words and short sentences:",
                "replace": True,
                "temperature": 0.2,
            },
            {
                "title": "Summarize",
                "description": "Create a brief summary",
                "system": "",
                "prompt": "Summarize the following text in 2-3 sentences:",
                "replace": False,
                "temperature": 0.2,
            },
        ]
        self._save_prompts()
