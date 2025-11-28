"""
Snippet handler for Stratum.
Handles inserting snippets from the vault into the active window.
"""

from __future__ import annotations

import keyboard
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .vault_manager import VaultManager


class SnippetHandler:
    """Handles snippet insertion into active windows."""

    def __init__(self, vault_manager: VaultManager) -> None:
        self._vault = vault_manager

    def insert_snippet(self, item_id: str) -> bool:
        """Insert a snippet by its ID.

        Args:
            item_id: The ID of the vault item to insert

        Returns:
            True if successful, False otherwise
        """
        item = self._vault.find_item(item_id)
        if not item:
            print(f"Snippet not found: {item_id}")
            return False

        return self.type_text(item.value)

    def type_text(self, text: str) -> bool:
        """Type text into the currently active window.

        Args:
            text: The text to type

        Returns:
            True if successful, False otherwise
        """
        if not text:
            return False

        try:
            # Use keyboard.write for reliable text insertion
            # This handles special characters and unicode properly
            keyboard.write(text, delay=0.01)
            return True
        except Exception as e:
            print(f"Failed to type text: {e}")
            # Fallback: try using clipboard
            return self._clipboard_paste(text)

    def _clipboard_paste(self, text: str) -> bool:
        """Fallback method: copy to clipboard and paste.

        Args:
            text: The text to paste

        Returns:
            True if successful, False otherwise
        """
        try:
            import pyperclip
            # Save current clipboard
            try:
                original = pyperclip.paste()
            except Exception:
                original = ""

            # Set new clipboard content and paste
            pyperclip.copy(text)
            time.sleep(0.05)
            keyboard.send('ctrl+v')
            time.sleep(0.05)

            # Restore original clipboard (optional)
            # pyperclip.copy(original)

            return True
        except ImportError:
            print("pyperclip not available for clipboard fallback")
            return False
        except Exception as e:
            print(f"Clipboard paste failed: {e}")
            return False


def create_snippet_handler(vault_manager: VaultManager) -> SnippetHandler:
    """Factory function to create a snippet handler."""
    return SnippetHandler(vault_manager)
