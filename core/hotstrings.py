from __future__ import annotations

import threading
from typing import Callable, Dict, Optional

import keyboard

from .command_registry import CommandRegistry


class HotstringEngine:
    """
    Working hotstring engine driven by CommandRegistry.
    Monitors keyboard input and triggers commands when hotstring patterns are typed.
    """

    def __init__(self, registry: CommandRegistry) -> None:
        self._registry = registry
        self._buffer: str = ""
        self._max_buffer_size: int = 50
        self._hotstrings: Dict[str, str] = {}  # trigger -> command_id
        self._enabled: bool = True
        self._hook_installed: bool = False

    def register_all(self) -> None:
        """Register all hotstrings from the command registry."""
        self._hotstrings.clear()

        for cmd in self._registry.all():
            if cmd.hotstring:
                # Store the trigger and command ID
                trigger = cmd.hotstring.upper()  # Case-insensitive matching
                self._hotstrings[trigger] = cmd.id

        # Install keyboard hook if we have hotstrings
        if self._hotstrings and not self._hook_installed:
            self._install_hook()

    def _install_hook(self) -> None:
        """Install the keyboard hook for hotstring detection."""
        try:
            keyboard.on_press(self._on_key_press)
            self._hook_installed = True
        except Exception as e:
            print(f"Failed to install hotstring hook: {e}")

    def _on_key_press(self, event: keyboard.KeyboardEvent) -> None:
        """Handle key press events for hotstring detection."""
        if not self._enabled:
            return

        key_name = event.name

        # Handle special keys that should clear the buffer
        if key_name in ('space', 'enter', 'tab', 'escape', 'backspace'):
            if key_name == 'backspace' and self._buffer:
                self._buffer = self._buffer[:-1]
            else:
                # Check for trigger before clearing
                self._check_and_trigger()
                if key_name != 'backspace':
                    self._buffer = ""
            return

        # Handle regular character keys
        if len(key_name) == 1:
            self._buffer += key_name.upper()

            # Keep buffer size manageable
            if len(self._buffer) > self._max_buffer_size:
                self._buffer = self._buffer[-self._max_buffer_size:]

            # Check if the buffer ends with any hotstring trigger
            self._check_and_trigger()

    def _check_and_trigger(self) -> None:
        """Check if buffer matches any hotstring and trigger if so."""
        for trigger, cmd_id in self._hotstrings.items():
            if self._buffer.endswith(trigger):
                # Execute in a separate thread to avoid blocking keyboard events
                threading.Thread(
                    target=self._execute_hotstring,
                    args=(cmd_id, trigger),
                    daemon=True
                ).start()
                self._buffer = ""
                return

    def _execute_hotstring(self, cmd_id: str, trigger: str) -> None:
        """Execute a hotstring command."""
        try:
            # First, delete the typed trigger
            for _ in range(len(trigger)):
                keyboard.send('backspace')

            # Execute the command
            self._registry.execute(cmd_id)

        except Exception as e:
            print(f"Hotstring execution error: {e}")

    def enable(self) -> None:
        """Enable hotstring detection."""
        self._enabled = True

    def disable(self) -> None:
        """Disable hotstring detection."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if hotstring detection is enabled."""
        return self._enabled

    def clear_buffer(self) -> None:
        """Clear the keyboard buffer."""
        self._buffer = ""

    def unregister_all(self) -> None:
        """Unregister all hotstrings and remove hook."""
        self._hotstrings.clear()
        self._buffer = ""
        # Note: keyboard library doesn't easily support unhooking specific handlers
        # The hook will remain but hotstrings dict is empty so nothing will trigger
