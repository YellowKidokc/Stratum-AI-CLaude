"""
Audio Tab - Voice interaction interface

Features:
- Text-to-Speech with high-quality neural voices
- Speech-to-Text from files or microphone
- Voice selection
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
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
    """Audio/Voice interaction tab."""

    # Signals for thread-safe UI updates
    status_changed = Signal(str)

    def __init__(self, tts_engine: TTSEngine):
        super().__init__()
        self.tts = TTSAdapter(tts_engine)
        self._current_voice = "en-US-AriaNeural"

        # Connect signals
        self.status_changed.connect(self._update_status)
        
        self._build_ui()
        
        # Load engine in background
        threading.Thread(target=self._load_engine, daemon=True).start()

    def _load_engine(self) -> None:
        """Load audio engine in background thread."""
        self.status_changed.emit("⏳ Loading AI Models (Whisper + EdgeTTS)...")
        
        try:
            self.engine = AudioEngine()
            
            # Initialize pygame for TTS
            self.engine.initialize_pygame()
            
            # Initialize Whisper for STT (this takes a moment)
            whisper_ok = self.engine.initialize_whisper()
            
            # Create floating player with window control panel
            self.floating_player = FloatingPlayer(self.engine, self.window_control_panel)
            
            if whisper_ok:
                self.status_changed.emit("✅ Audio Engine Ready (Whisper + EdgeTTS)")
                self._engine_ready = True
                self._enable_controls()
            else:
                self.status_changed.emit("⚠️ Audio Engine Partially Ready (TTS only)")
                self._engine_ready = True
                self._enable_tts_only()
                
        except Exception as e:
            self.status_changed.emit(f"❌ Error loading audio engine: {e}")
            print(f"Audio engine error: {e}")

    def _build_ui(self) -> None:
        """Build the UI."""
        layout = QVBoxLayout(self)

        # --- HEADER ---
        header_label = QLabel("<h2>🎙️ Voice Assistant</h2>")
        layout.addWidget(header_label)

        self.lbl_status = QLabel("⏳ Initializing...")
        self.lbl_status.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
        layout.addWidget(self.lbl_status)

        # --- SECTION 1: TEXT TO SPEECH ---
        tts_group = QGroupBox("🗣️ Text to Speech (Neural Voices)")
        tts_layout = QVBoxLayout()

        # Voice selection
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        self.voice_combo.addItems([
            "en-US-BrianMultilingualNeural (Brian - Multilingual) ⭐",
            "en-US-GuyNeural (Male, Professional)",
            "en-US-AriaNeural (Female, Friendly)",
            "en-US-JennyNeural (Female, Warm)",
            "en-GB-SoniaNeural (British Female)",
            "en-AU-NatashaNeural (Australian Female)",
        ])
        self.voice_combo.currentTextChanged.connect(self._on_voice_changed)
        voice_layout.addWidget(self.voice_combo)
        voice_layout.addStretch()
        tts_layout.addLayout(voice_layout)

        self.txt_input = QTextEdit()
        self.txt_input.setPlaceholderText("Type text here and I will speak it with a human-like voice...")
        self.txt_input.setMaximumHeight(120)
        tts_layout.addWidget(self.txt_input)

        # Quick test buttons
        quick_layout = QHBoxLayout()
        self.btn_test1 = QPushButton("Test: 'Hello'")
        self.btn_test1.clicked.connect(lambda: self.txt_input.setText("Hello, AI Hub is online."))
        self.btn_test2 = QPushButton("Test: 'Jarvis'")
        self.btn_test2.clicked.connect(lambda: self.txt_input.setText("Good morning, sir. All systems operational."))
        quick_layout.addWidget(self.btn_test1)
        quick_layout.addWidget(self.btn_test2)
        quick_layout.addStretch()
        tts_layout.addLayout(quick_layout)

        self.btn_speak = QPushButton("🔊 Speak Text")
        self.btn_speak.setEnabled(False)
        self.btn_speak.setStyleSheet("padding: 10px; font-weight: bold;")
        self.btn_speak.clicked.connect(self._run_tts)
        tts_layout.addWidget(self.btn_speak)

        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group)

        # --- SECTION 1.5: ACADEMIC TEXT TO SPEECH ---
        academic_group = QGroupBox("🎓 Academic Text to Speech (Convert & Download)")
        academic_layout = QVBoxLayout()
        
        info_academic = QLabel(
            "Convert academic/complex text to natural speech and download as MP3.\n"
            "Perfect for listening to research papers, articles, or study materials!"
        )
        info_academic.setStyleSheet("color: #888; font-size: 11px;")
        academic_layout.addWidget(info_academic)
        
        self.txt_academic = QTextEdit()
        self.txt_academic.setPlaceholderText("Paste your academic text here (research papers, articles, etc.)...")
        self.txt_academic.setMaximumHeight(150)
        academic_layout.addWidget(self.txt_academic)
        
        # Buttons for academic TTS
        academic_btn_layout = QHBoxLayout()
        
        self.btn_academic_speak = QPushButton("🔊 Speak Now")
        self.btn_academic_speak.setEnabled(False)
        self.btn_academic_speak.setToolTip("Play the audio immediately")
        self.btn_academic_speak.clicked.connect(self._speak_academic)
        academic_btn_layout.addWidget(self.btn_academic_speak)
        
        self.btn_academic_download = QPushButton("💾 Download as MP3")
        self.btn_academic_download.setEnabled(False)
        self.btn_academic_download.setToolTip("Save as MP3 file to listen later")
        self.btn_academic_download.clicked.connect(self._download_academic)
        academic_btn_layout.addWidget(self.btn_academic_download)
        
        academic_layout.addLayout(academic_btn_layout)
        
        self.lbl_academic_status = QLabel("")
        self.lbl_academic_status.setStyleSheet("color: #888; font-style: italic;")
        academic_layout.addWidget(self.lbl_academic_status)
        
        academic_group.setLayout(academic_layout)
        layout.addWidget(academic_group)

        # --- SECTION 2: SPEECH TO TEXT ---
        stt_group = QGroupBox("👂 Speech to Text (Transcription)")
        stt_layout = QVBoxLayout()

        info_label = QLabel(
            "Transcribe audio/video files or record from microphone.\n"
            "Supports: MP3, WAV, MP4, M4A, and more."
        )
        info_label.setStyleSheet("color: #888; font-size: 11px;")
        stt_layout.addWidget(info_label)

        btn_layout = QHBoxLayout()
        
        self.btn_transcribe = QPushButton("📂 Select File (Audio/Video)")
        self.btn_transcribe.setEnabled(False)
        self.btn_transcribe.clicked.connect(self._select_file)
        
        self.btn_record = QPushButton("🎤 Record (5 seconds)")
        self.btn_record.setEnabled(False)
        self.btn_record.clicked.connect(self._record_mic)
        
        btn_layout.addWidget(self.btn_transcribe)
        btn_layout.addWidget(self.btn_record)
        stt_layout.addLayout(btn_layout)

        self.txt_transcription = QTextEdit()
        self.txt_transcription.setPlaceholderText("Transcription output will appear here...")
        self.txt_transcription.setMinimumHeight(200)
        stt_layout.addWidget(self.txt_transcription)

        # Copy button
        self.btn_copy = QPushButton("📋 Copy to Clipboard")
        self.btn_copy.clicked.connect(self._copy_transcription)
        stt_layout.addWidget(self.btn_copy)

        stt_group.setLayout(stt_layout)
        layout.addWidget(stt_group)

        layout.addStretch()

    def _enable_controls(self) -> None:
        """Enable all controls when engine is ready."""
        self.btn_speak.setEnabled(True)
        self.btn_academic_speak.setEnabled(True)
        self.btn_academic_download.setEnabled(True)
        self.btn_transcribe.setEnabled(True)
        self.btn_record.setEnabled(True)

    def _enable_tts_only(self) -> None:
        """Enable only TTS controls."""
        self.btn_speak.setEnabled(True)
        self.btn_academic_speak.setEnabled(True)
        self.btn_academic_download.setEnabled(True)
        self.btn_transcribe.setEnabled(False)
        self.btn_record.setEnabled(False)

    def _update_status(self, status: str) -> None:
        """Update status label (thread-safe)."""
        self.lbl_status.setText(status)

    def _update_transcription(self, text: str) -> None:
        """Update transcription text (thread-safe)."""
        self.txt_transcription.setText(text)

    def _on_voice_changed(self, voice_text: str) -> None:
        """Handle voice selection change."""
        if not self.engine:
            return
        
        # Extract voice ID from the combo text
        voice_id = voice_text.split(" ")[0]
        self.engine.set_voice(voice_id)

    def _run_tts(self) -> None:
        """Run text-to-speech."""
        text = self.txt_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Text", "Please enter some text to speak.")
            return

        if not self.engine:
            QMessageBox.warning(self, "Not Ready", "Audio engine is not ready yet.")
            return

        self.status_changed.emit("🔊 Speaking...")
        self.btn_speak.setEnabled(False)
        
        # Show floating player
        if self.floating_player:
            self.floating_player.set_speaking(text[:50] + "..." if len(text) > 50 else text)

        def speak_thread():
            try:
                success = self.engine.speak(text)
                if success:
                    self.status_changed.emit("✅ Done speaking")
                else:
                    self.status_changed.emit("❌ TTS failed")
            except Exception as e:
                self.status_changed.emit(f"❌ Error: {e}")
            finally:
                # Re-enable button after a short delay
                QTimer.singleShot(500, lambda: self.btn_speak.setEnabled(True))

        threading.Thread(target=speak_thread, daemon=True).start()

    def _select_file(self) -> None:
        """Open file dialog to select audio/video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio or Video File",
            "",
            "Media Files (*.mp3 *.wav *.mp4 *.m4a *.ogg *.flac);;All Files (*.*)"
        )
        
        if file_path:
            self._transcribe_file(file_path)

    def _record_mic(self) -> None:
        """Record from microphone."""
        if not self.engine:
            return

        self.status_changed.emit("🎤 Recording for 5 seconds...")
        self.btn_record.setEnabled(False)

        def record_thread():
            try:
                file_path = self.engine.record_audio(duration=5)
                if file_path:
                    self._transcribe_file(file_path)
                else:
                    self.status_changed.emit("❌ Recording failed")
            except Exception as e:
                self.status_changed.emit(f"❌ Error: {e}")
            finally:
                QTimer.singleShot(500, lambda: self.btn_record.setEnabled(True))

        threading.Thread(target=record_thread, daemon=True).start()

    def _transcribe_file(self, file_path: str) -> None:
        """Transcribe an audio/video file."""
        if not self.engine:
            return

        self.status_changed.emit(f"⏳ Transcribing: {Path(file_path).name}...")
        self.txt_transcription.setText("Processing...")

        def transcribe_thread():
            try:
                text = self.engine.transcribe_file(file_path)
                self.transcription_ready.emit(text)
                self.status_changed.emit("✅ Transcription complete")
            except Exception as e:
                error_msg = f"❌ Error: {e}"
                self.transcription_ready.emit(error_msg)
                self.status_changed.emit(error_msg)

        threading.Thread(target=transcribe_thread, daemon=True).start()

    def _copy_transcription(self) -> None:
        """Copy transcription to clipboard."""
        text = self.txt_transcription.toPlainText()
        if text:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            self.status_changed.emit("✅ Copied to clipboard")
        else:
            QMessageBox.information(self, "Empty", "No transcription to copy.")
    
    def _speak_academic(self) -> None:
        """Speak academic text immediately."""
        text = self.txt_academic.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Text", "Please paste some academic text first.")
            return
        
        if not self.engine:
            QMessageBox.warning(self, "Not Ready", "Audio engine is not ready yet.")
            return
        
        self.lbl_academic_status.setText("🔊 Speaking academic text...")
        self.btn_academic_speak.setEnabled(False)
        self.btn_academic_download.setEnabled(False)
        
        def speak_thread():
            try:
                success = self.engine.speak(text)
                if success:
                    self.lbl_academic_status.setText("✅ Done speaking")
                else:
                    self.lbl_academic_status.setText("❌ TTS failed")
            except Exception as e:
                self.lbl_academic_status.setText(f"❌ Error: {e}")
            finally:
                QTimer.singleShot(500, lambda: self.btn_academic_speak.setEnabled(True))
                QTimer.singleShot(500, lambda: self.btn_academic_download.setEnabled(True))
        
        threading.Thread(target=speak_thread, daemon=True).start()
    
    def _download_academic(self) -> None:
        """Download academic text as MP3 file."""
        text = self.txt_academic.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Text", "Please paste some academic text first.")
            return
        
        if not self.engine:
            QMessageBox.warning(self, "Not Ready", "Audio engine is not ready yet.")
            return
        
        # Ask where to save
        default_name = "academic_audio.mp3"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Academic Audio",
            default_name,
            "MP3 Files (*.mp3);;All Files (*.*)"
        )
        
        if not file_path:
            return  # User cancelled
        
        self.lbl_academic_status.setText("💾 Generating MP3...")
        self.btn_academic_speak.setEnabled(False)
        self.btn_academic_download.setEnabled(False)
        
        def download_thread():
            try:
                success = self.engine.save_to_file(text, file_path)
                if success:
                    self.lbl_academic_status.setText(f"✅ Saved to: {Path(file_path).name}")
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Academic audio saved successfully!\n\nLocation: {file_path}\n\nYou can now listen to it anytime!"
                    )
                else:
                    self.lbl_academic_status.setText("❌ Failed to save MP3")
            except Exception as e:
                self.lbl_academic_status.setText(f"❌ Error: {e}")
                QMessageBox.critical(self, "Error", f"Failed to save MP3:\n{e}")
            finally:
                QTimer.singleShot(500, lambda: self.btn_academic_speak.setEnabled(True))
                QTimer.singleShot(500, lambda: self.btn_academic_download.setEnabled(True))
        
        threading.Thread(target=download_thread, daemon=True).start()
