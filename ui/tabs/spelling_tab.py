from __future__ import annotations

import threading

from PySide6.QtWidgets import (
    QLabel, QPushButton, QVBoxLayout, QTextEdit, 
    QHBoxLayout, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, Signal, QObject

from .base import BaseTab


class RewriteWorker(QObject):
    """Worker to handle API calls in background thread with proper Qt signals."""
    finished = Signal(str)
    
    def __init__(self, client: OpenAIClient, text: str, system: str, prompt: str, temperature: float = 0.2):
        super().__init__()
        self._client = client
        self._text = text
        self._system = system
        self._prompt = prompt
        self._temperature = temperature
    
    def run(self) -> None:
        """Run the API call and emit result."""
        try:
            message = f"{self._prompt}\n\n{self._text}"
            output = self._client.chat(
                self._system if self._system else None,
                message,
                self._temperature
            )
            if output.strip():
                self.finished.emit(output)
        except Exception as e:
            print(f"❌ Rewrite error: {e}")


class SpellingTab(BaseTab):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        """Build simplified spelling/grammar check UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Spelling & Grammar Check")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        # Input section
        input_group = QGroupBox("Input Text")
        input_layout = QVBoxLayout()
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Paste or type text to check spelling and grammar...")
        input_layout.addWidget(self.input_text)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Output section
        output_group = QGroupBox("Checked Text")
        output_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Corrected text will appear here...")
        output_layout.addWidget(self.output_text)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Buttons
        buttons_layout = QHBoxLayout()
        check_btn = QPushButton("Check Spelling & Grammar")
        check_btn.clicked.connect(self._check_text)
        buttons_layout.addWidget(check_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_text)
        buttons_layout.addWidget(clear_btn)

        layout.addLayout(buttons_layout)

    def _check_text(self) -> None:
        """Basic spelling/grammar check (placeholder)."""
        input_text = self.input_text.toPlainText().strip()
        if not input_text:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Text", "Please enter some text to check.")
            return

        # For now, just copy input to output (would integrate with AI later)
        self.output_text.setPlainText(input_text)

    def _clear_text(self) -> None:
        """Clear all text."""
        self.input_text.clear()
        self.output_text.clear()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Create splitter for input/output
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Input and Quick Actions
        left_widget = QGroupBox("📝 Input Text")
        left_layout = QVBoxLayout()
        
        self._input_edit = QTextEdit()
        self._input_edit.setPlaceholderText("Paste or type your text here...")
        left_layout.addWidget(self._input_edit)
        
        # Quick action buttons
        actions_label = QLabel("⚡ Quick Actions:")
        actions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        left_layout.addWidget(actions_label)
        
        # Row 1: Spelling & Grammar
        row1 = QHBoxLayout()
        btn_spelling = QPushButton("✓ Fix Spelling")
        btn_spelling.setToolTip("Correct spelling and grammar")
        btn_spelling.clicked.connect(lambda: self._rewrite("spelling"))
        row1.addWidget(btn_spelling)
        
        btn_grammar = QPushButton("📖 Grammar Only")
        btn_grammar.setToolTip("Fix grammar, keep original wording")
        btn_grammar.clicked.connect(lambda: self._rewrite("grammar"))
        row1.addWidget(btn_grammar)
        left_layout.addLayout(row1)
        
        # Row 2: Length
        row2 = QHBoxLayout()
        btn_shorter = QPushButton("📉 Make Shorter")
        btn_shorter.setToolTip("Condense while keeping meaning")
        btn_shorter.clicked.connect(lambda: self._rewrite("shorter"))
        row2.addWidget(btn_shorter)
        
        btn_longer = QPushButton("📈 Make Longer")
        btn_longer.setToolTip("Expand with more detail")
        btn_longer.clicked.connect(lambda: self._rewrite("longer"))
        row2.addWidget(btn_longer)
        left_layout.addLayout(row2)
        
        # Row 3: Style
        row3 = QHBoxLayout()
        btn_simple = QPushButton("💡 Simplify")
        btn_simple.setToolTip("Make easier to understand")
        btn_simple.clicked.connect(lambda: self._rewrite("simple"))
        row3.addWidget(btn_simple)
        
        btn_professional = QPushButton("💼 Professional")
        btn_professional.setToolTip("Make more formal and polished")
        btn_professional.clicked.connect(lambda: self._rewrite("professional"))
        row3.addWidget(btn_professional)
        left_layout.addLayout(row3)
        
        # Row 4: Academic & Smart
        row4 = QHBoxLayout()
        btn_academic = QPushButton("🎓 Academic")
        btn_academic.setToolTip("Academic writing style")
        btn_academic.clicked.connect(lambda: self._rewrite("academic"))
        row4.addWidget(btn_academic)
        
        btn_smart = QPushButton("🧠 Smarter")
        btn_smart.setToolTip("Use more sophisticated language")
        btn_smart.clicked.connect(lambda: self._rewrite("smart"))
        row4.addWidget(btn_smart)
        left_layout.addLayout(row4)
        
        # Clear button
        btn_clear = QPushButton("🗑️ Clear All")
        btn_clear.clicked.connect(self._clear_all)
        left_layout.addWidget(btn_clear)
        
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        # Right side - Output
        right_widget = QGroupBox("✨ Output")
        right_layout = QVBoxLayout()
        
        self._output_edit = QTextEdit()
        self._output_edit.setPlaceholderText("Rewritten text will appear here...")
        self._output_edit.setReadOnly(True)
        right_layout.addWidget(self._output_edit)
        
        # Output buttons
        output_btns = QHBoxLayout()
        btn_copy = QPushButton("📋 Copy to Clipboard")
        btn_copy.clicked.connect(self._copy_output)
        output_btns.addWidget(btn_copy)
        
        btn_replace = QPushButton("⬅️ Replace Input")
        btn_replace.setToolTip("Move output back to input for further editing")
        btn_replace.clicked.connect(self._replace_input)
        output_btns.addWidget(btn_replace)
        right_layout.addLayout(output_btns)
        
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        # Set splitter sizes (50/50)
        splitter.setSizes([500, 500])
        
        layout.addWidget(splitter)

    def _rewrite(self, action: str) -> None:
        """Rewrite text based on action."""
        text = self._input_edit.toPlainText()
        
        if not text.strip():
            self._output_edit.setPlainText("⚠️ Please enter some text first!")
            return
        
        # Show processing message
        self._output_edit.setPlainText("⏳ Processing...")
        
        # Define prompts for each action
        prompts = {
            "spelling": (
                "You are an English spelling corrector and grammar improver. Reply ONLY with the corrected text—no explanations.",
                "Correct the spelling (American English) and grammar of the following:",
                0.0
            ),
            "grammar": (
                "You are a grammar expert. Fix ONLY grammar errors, keep the original wording and style. Reply with ONLY the corrected text.",
                "Fix only the grammar in the following text:",
                0.0
            ),
            "shorter": (
                "",
                "Make the following text shorter while preserving the key meaning:",
                0.2
            ),
            "longer": (
                "",
                "Expand the following text with more detail and explanation:",
                0.7
            ),
            "simple": (
                "",
                "Simplify the following text so it's easy for anyone to understand:",
                0.2
            ),
            "professional": (
                "",
                "Rewrite the following to sound professional and polished:",
                0.2
            ),
            "academic": (
                "You are an academic writing expert. Use formal, scholarly language.",
                "Rewrite the following in academic style:",
                0.2
            ),
            "smart": (
                "",
                "Rewrite the following using more sophisticated and intelligent language:",
                0.3
            ),
        }
        
        system, prompt, temp = prompts.get(action, prompts["spelling"])
        
        # Create worker and connect signal
        worker = RewriteWorker(self._client, text, system, prompt, temp)
        worker.finished.connect(self._on_rewrite_ready)
        
        # Run in background thread
        threading.Thread(target=worker.run, daemon=True).start()
    
    def _on_rewrite_ready(self, rewritten_text: str) -> None:
        """Handle the rewritten text from worker (runs in main thread)."""
        self._output_edit.setPlainText(rewritten_text)
    
    def _copy_output(self) -> None:
        """Copy output text to clipboard."""
        text = self._output_edit.toPlainText()
        if text and not text.startswith("⚠️") and not text.startswith("⏳"):
            from ...services.selection import copy_to_clipboard
            copy_to_clipboard(text)
            print("✅ Copied to clipboard!")
    
    def _replace_input(self) -> None:
        """Move output text back to input for further editing."""
        text = self._output_edit.toPlainText()
        if text and not text.startswith("⚠️") and not text.startswith("⏳"):
            self._input_edit.setPlainText(text)
            self._output_edit.clear()
    
    def _clear_all(self) -> None:
        """Clear both input and output."""
        self._input_edit.clear()
        self._output_edit.clear()
