"""
Simplified Audio Tab for Stratum - Text-to-Speech only
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from .base import BaseTab
from .adapters import TTSAdapter

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.tts_engine import TTSEngine


class AudioTab(BaseTab):
    """Simplified Audio/Voice interaction tab for TTS."""

    # Signals for thread-safe UI updates
    status_changed = Signal(str)

    def __init__(self, tts_engine: TTSEngine):
        super().__init__()
        self.tts = TTSAdapter(tts_engine)
        self._current_voice = "en-US-AriaNeural"

        # Connect signals
        self.status_changed.connect(self._update_status)

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the simplified TTS UI."""
        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("🎙️ Voice Assistant")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header_label)

        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
        layout.addWidget(self.lbl_status)

        # TTS Section
        tts_group = QGroupBox("🗣️ Text to Speech")
        tts_layout = QVBoxLayout()

        # Voice selection
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        self._load_voices()
        self.voice_combo.currentTextChanged.connect(self._on_voice_changed)
        voice_layout.addWidget(self.voice_combo)
        voice_layout.addStretch()
        tts_layout.addLayout(voice_layout)

        # Text input
        self.txt_input = QTextEdit()
        self.txt_input.setPlaceholderText("Type text here and I will speak it...")
        self.txt_input.setMaximumHeight(120)
        tts_layout.addWidget(self.txt_input)

        # Quick test buttons
        quick_layout = QHBoxLayout()
        self.btn_test1 = QPushButton("Test: 'Hello'")
        self.btn_test1.clicked.connect(lambda: self.txt_input.setText("Hello, Stratum is online."))
        self.btn_test2 = QPushButton("Stop Speaking")
        self.btn_test2.clicked.connect(self._stop_speaking)
        quick_layout.addWidget(self.btn_test1)
        quick_layout.addWidget(self.btn_test2)
        quick_layout.addStretch()
        tts_layout.addLayout(quick_layout)

        # Speak and Download buttons
        buttons_layout = QHBoxLayout()

        self.btn_speak = QPushButton("🔊 Speak Text")
        self.btn_speak.setStyleSheet("padding: 10px; font-weight: bold;")
        self.btn_speak.clicked.connect(self._run_tts)
        buttons_layout.addWidget(self.btn_speak)

        self.btn_download = QPushButton("💾 Download as MP3")
        self.btn_download.setStyleSheet("padding: 10px;")
        self.btn_download.setToolTip("Save this text-to-speech as an MP3 file")
        self.btn_download.clicked.connect(self._download_as_mp3)
        buttons_layout.addWidget(self.btn_download)

        tts_layout.addLayout(buttons_layout)

        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group)

        layout.addStretch()

    def _load_voices(self) -> None:
        """Load available voices into combo box."""
        try:
            voices = self.tts.get_voices()
            if voices:
                voice_names = [f"{v['name']} ({v['language']})" for v in voices[:5]]  # Limit to 5
                self.voice_combo.addItems(voice_names)
            else:
                # Fallback voices
                self.voice_combo.addItems([
                    "en-US-AriaNeural (Female)",
                    "en-US-Zira (Female)",
                    "en-US-David (Male)",
                ])
        except Exception:
            self.voice_combo.addItems(["Default Voice"])

    def _on_voice_changed(self, voice_text: str) -> None:
        """Handle voice selection change."""
        if voice_text:
            # Extract voice name from display text
            voice_name = voice_text.split(" (")[0]
            self.tts.set_voice(voice_name)
            self._current_voice = voice_name

    def _run_tts(self) -> None:
        """Run text-to-speech."""
        text = self.txt_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Text", "Please enter some text to speak.")
            return

        try:
            self.status_changed.emit("Speaking...")
            self.btn_speak.setEnabled(False)
            self.tts.speak(text)
            self.status_changed.emit("Ready")
            self.btn_speak.setEnabled(True)
        except Exception as e:
            self.status_changed.emit(f"Error: {str(e)}")
            self.btn_speak.setEnabled(True)
            QMessageBox.critical(self, "TTS Error", f"Failed to speak text: {str(e)}")

    def _stop_speaking(self) -> None:
        """Stop current speech."""
        try:
            self.tts.stop()
            self.status_changed.emit("Stopped")
        except Exception as e:
            self.status_changed.emit(f"Error stopping: {str(e)}")

    def _update_status(self, status: str) -> None:
        """Update status label."""
        self.lbl_status.setText(status)

    def _download_as_mp3(self) -> None:
        """Download the current text as an MP3 file."""
        text = self.txt_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Text", "Please enter some text to convert to audio.")
            return

        # Ask where to save the MP3
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Audio As",
            "stratum_tts.mp3",
            "MP3 Files (*.mp3);;All Files (*.*)",
        )

        if not file_path:
            return  # User canceled

        try:
            self.status_changed.emit("Saving audio file...")
            self.btn_download.setEnabled(False)

            ok = self.tts.save_to_file(text, file_path)

            if ok:
                self.status_changed.emit("Audio saved!")
                QMessageBox.information(
                    self,
                    "Saved",
                    f"Audio saved successfully:\n{file_path}",
                )
            else:
                self.status_changed.emit("Save failed")
                QMessageBox.critical(
                    self,
                    "Error",
                    "The TTS engine reported a failure while saving the file.",
                )
        except Exception as e:
            self.status_changed.emit(f"Error: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save MP3:\n{e}",
            )
        finally:
            self.btn_download.setEnabled(True)
            self.status_changed.emit("Ready")
