"""
Simplified TTS Preprocessor Tab for Stratum

Basic text preprocessing for TTS without complex dependencies.
"""

from __future__ import annotations

import re
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QGroupBox, QMessageBox
)


class TTSPreprocessorTab(QWidget):
    """Simplified TTS preprocessor tab."""

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the simplified UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("TTS Preprocessor")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        # Input section
        input_group = QGroupBox("Input Text")
        input_layout = QVBoxLayout()
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Paste your text here for TTS preprocessing...")
        input_layout.addWidget(self.input_text)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Output section
        output_group = QGroupBox("Processed Text")
        output_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Processed text will appear here...")
        output_layout.addWidget(self.output_text)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Buttons
        buttons_layout = QHBoxLayout()
        preprocess_btn = QPushButton("Preprocess Text")
        preprocess_btn.clicked.connect(self._preprocess_text)
        buttons_layout.addWidget(preprocess_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_text)
        buttons_layout.addWidget(clear_btn)

        layout.addLayout(buttons_layout)

    def _preprocess_text(self) -> None:
        """Basic text preprocessing."""
        input_text = self.input_text.toPlainText().strip()
        if not input_text:
            QMessageBox.warning(self, "No Text", "Please enter some text to preprocess.")
            return

        # Simple preprocessing: remove extra whitespace, basic formatting
        processed = self._basic_preprocess(input_text)
        self.output_text.setPlainText(processed)

    def _basic_preprocess(self, text: str) -> str:
        """Basic text preprocessing for TTS."""
        # Remove markdown links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Remove markdown headers formatting
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)

        # Remove markdown bold/italic
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)

        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

        return text.strip()

    def _clear_text(self) -> None:
        """Clear all text."""
        self.input_text.clear()
        self.output_text.clear()
