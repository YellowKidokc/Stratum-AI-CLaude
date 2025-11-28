from __future__ import annotations

from typing import Optional

import keyboard

from .command_registry import CommandRegistry


def register_hotkeys(registry: CommandRegistry) -> None:
    """
    Register all hotkeys defined in commands.json with the keyboard library.
    """
    for cmd in registry.all():
        if not cmd.hotkey:
            continue

        # Capture cmd.id by value in default arg
        keyboard.add_hotkey(cmd.hotkey, lambda cid=cmd.id: registry.execute(cid))


def unregister_all_hotkeys() -> None:
    try:
        keyboard.unhook_all_hotkeys()
    except Exception:
        # Be tolerant if nothing is registered yet.
        pass
