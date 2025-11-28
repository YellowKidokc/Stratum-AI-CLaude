from __future__ import annotations

import asyncio
import io
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
import threading
import time


class TTSEngine:
    """Unified text-to-speech engine with Edge TTS primary and SAPI fallback."""

    def __init__(self):
        self._edge_available = self._check_edge_tts()
        self._current_process: Optional[subprocess.Popen] = None
        self._voice = "en-US-AriaNeural"  # Default Edge TTS voice
        self._rate = "+0%"  # Speech rate
        self._volume = "+0%"  # Speech volume

    def _check_edge_tts(self) -> bool:
        """Check if Edge TTS is available."""
        try:
            result = subprocess.run(
                ["edge-tts", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False

    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available voices."""
        if self._edge_available:
            return self._get_edge_voices()
        else:
            return self._get_sapi_voices()

    def _get_edge_voices(self) -> List[Dict[str, str]]:
        """Get Edge TTS voices."""
        try:
            result = subprocess.run(
                ["edge-tts", "--list-voices"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                voices = []
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            voices.append({
                                "name": parts[0],
                                "language": parts[1],
                                "gender": parts[2],
                                "description": " ".join(parts[3:])
                            })
                return voices
        except Exception:
            pass
        return []

    def _get_sapi_voices(self) -> List[Dict[str, str]]:
        """Get Windows SAPI voices (fallback)."""
        # This is a simplified fallback - in a real implementation,
        # you'd use pyttsx3 or similar to enumerate SAPI voices
        return [
            {"name": "Microsoft Zira Desktop", "language": "en-US", "gender": "Female", "description": "SAPI Default"},
            {"name": "Microsoft David Desktop", "language": "en-US", "gender": "Male", "description": "SAPI Male"},
        ]

    def set_voice(self, voice_name: str) -> None:
        """Set the TTS voice."""
        self._voice = voice_name

    def set_rate(self, rate: str) -> None:
        """Set speech rate (e.g., '+50%', '-20%')."""
        self._rate = rate

    def set_volume(self, volume: str) -> None:
        """Set speech volume (e.g., '+20%', '-10%')."""
        self._volume = volume

    def speak_text(self, text: str, block: bool = False) -> None:
        """Speak text using available TTS engine."""
        if not text.strip():
            return

        if self._edge_available:
            self._speak_edge(text, block)
        else:
            self._speak_sapi(text, block)

    def _speak_edge(self, text: str, block: bool) -> None:
        """Speak text using Edge TTS."""
        def run_tts():
            try:
                # Create temporary file for audio output
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                    temp_path = temp_file.name

                # Build Edge TTS command
                cmd = [
                    "edge-tts",
                    "--text", text,
                    "--voice", self._voice,
                    "--rate", self._rate,
                    "--volume", self._volume,
                    "--write-media", temp_path
                ]

                # Run Edge TTS
                self._current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                # Wait for completion if blocking
                if block:
                    self._current_process.wait()

                    # Play the generated audio file
                    self._play_audio_file(temp_path)

                    # Clean up temp file
                    try:
                        Path(temp_path).unlink(missing_ok=True)
                    except Exception:
                        pass

            except Exception as e:
                print(f"Edge TTS error: {e}")
            finally:
                self._current_process = None

        if block:
            run_tts()
        else:
            thread = threading.Thread(target=run_tts, daemon=True)
            thread.start()

    def _speak_sapi(self, text: str, block: bool) -> None:
        """Speak text using Windows SAPI (fallback)."""
        def run_sapi():
            try:
                # Use PowerShell to speak via SAPI
                ps_command = f'''
                Add-Type -AssemblyName System.Speech;
                $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer;
                $speak.Rate = 0;  # Default rate
                $speak.Volume = 100;  # Default volume
                $speak.Speak("{text.replace('"', '""')}");
                '''

                self._current_process = subprocess.Popen(
                    ["powershell", "-Command", ps_command],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                if block:
                    self._current_process.wait()

            except Exception as e:
                print(f"SAPI TTS error: {e}")
            finally:
                self._current_process = None

        if block:
            run_sapi()
        else:
            thread = threading.Thread(target=run_sapi, daemon=True)
            thread.start()

    def _play_audio_file(self, file_path: str) -> None:
        """Play an audio file."""
        try:
            if platform.system() == "Windows":
                # Use Windows Media Player or default player
                subprocess.run(["cmd", "/c", "start", "", file_path],
                             shell=True, check=True)
            else:
                # For other platforms, you might use different commands
                print(f"Audio file generated: {file_path}")
        except Exception as e:
            print(f"Error playing audio file: {e}")

    def speak_selection(self) -> None:
        """Speak currently selected text (clipboard-based approach)."""
        try:
            # Get clipboard content (this would need pyperclip or similar)
            # For now, this is a placeholder
            print("Speak selection not yet implemented - would get selected text from clipboard")
        except Exception as e:
            print(f"Error speaking selection: {e}")

    def stop_speaking(self) -> None:
        """Stop current speech."""
        if self._current_process:
            try:
                self._current_process.terminate()
                self._current_process.wait(timeout=1)
            except Exception:
                try:
                    self._current_process.kill()
                except Exception:
                    pass
            finally:
                self._current_process = None

    def is_speaking(self) -> bool:
        """Check if TTS is currently speaking."""
        return self._current_process is not None and self._current_process.poll() is None

    def save_to_file(self, text: str, file_path: str) -> bool:
        """Save TTS output as an MP3 file.

        Args:
            text: The text to convert to speech
            file_path: Path where to save the MP3 file

        Returns:
            True if successful, False otherwise
        """
        if not text.strip():
            return False

        try:
            if self._edge_available:
                return self._save_edge_tts(text, file_path)
            else:
                return self._save_sapi_tts(text, file_path)
        except Exception as e:
            print(f"Error saving TTS to file: {e}")
            return False

    def _save_edge_tts(self, text: str, file_path: str) -> bool:
        """Save TTS using Edge TTS to file."""
        try:
            # Ensure .mp3 extension
            if not file_path.lower().endswith('.mp3'):
                file_path += '.mp3'

            # Build Edge TTS command
            cmd = [
                "edge-tts",
                "--text", text,
                "--voice", self._voice,
                "--rate", self._rate,
                "--volume", self._volume,
                "--write-media", file_path
            ]

            # Run Edge TTS and wait for completion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout for longer texts
            )

            return result.returncode == 0 and Path(file_path).exists()

        except subprocess.TimeoutExpired:
            print("Edge TTS timed out while saving file")
            return False
        except Exception as e:
            print(f"Edge TTS save error: {e}")
            return False

    def _save_sapi_tts(self, text: str, file_path: str) -> bool:
        """Save TTS using Windows SAPI to file (WAV format, then convert if possible)."""
        try:
            # Ensure .wav extension for SAPI
            wav_path = file_path
            if file_path.lower().endswith('.mp3'):
                wav_path = file_path[:-4] + '.wav'

            # Use PowerShell to save via SAPI
            escaped_text = text.replace('"', '""').replace("'", "''")
            ps_command = f'''
            Add-Type -AssemblyName System.Speech;
            $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer;
            $speak.SetOutputToWaveFile("{wav_path}");
            $speak.Speak("{escaped_text}");
            $speak.Dispose();
            '''

            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0 and Path(wav_path).exists():
                # If original request was for MP3, note that we saved as WAV
                if file_path.lower().endswith('.mp3'):
                    print(f"Note: SAPI saved as WAV format: {wav_path}")
                return True
            return False

        except Exception as e:
            print(f"SAPI save error: {e}")
            return False
