from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional
import json


@dataclass
class Command:
    id: str
    label: str
    action: str
    hotkey: str = ""
    hotstring: str = ""
    tags: List[str] | None = None


class CommandRegistry:
    def __init__(self, commands_path: Path) -> None:
        self._path = Path(commands_path)
        self._commands: Dict[str, Command] = {}
        self._handlers: Dict[str, Callable[..., None]] = {}

    # ---------- loading ----------

    def load(self) -> None:
        if not self._path.exists():
            self._path.write_text("[]", encoding="utf-8")
        raw = self._path.read_text(encoding="utf-8").strip() or "[]"
        data = json.loads(raw)
        self._commands.clear()
        for item in data:
            cmd = Command(
                id=item["id"],
                label=item.get("label", item["id"]),
                action=item.get("action", ""),
                hotkey=item.get("hotkey", ""),
                hotstring=item.get("hotstring", ""),
                tags=item.get("tags", []),
            )
            self._commands[cmd.id] = cmd

    # ---------- query ----------

    def all(self) -> List[Command]:
        return list(self._commands.values())

    def get(self, command_id: str) -> Optional[Command]:
        return self._commands.get(command_id)

    # ---------- handlers / execution ----------

    def register_handler(self, action_id: str, func: Callable[..., None]) -> None:
        """
        Register a handler for an action id like 'tts.speak_selection'
        or 'vault.insert'. If the command's action has a suffix
        (e.g. 'vault.insert:openai_main'), the suffix is passed as an argument.
        """
        self._handlers[action_id] = func

    def execute(self, command_id: str) -> None:
        cmd = self._commands.get(command_id)
        if not cmd:
            return

        action = cmd.action or ""
        if not action:
            return

        base, arg = action, None
        if ":" in action:
            base, arg = action.split(":", 1)

        handler = self._handlers.get(base)
        if not handler:
            return

        if arg is None:
            handler()
        else:
            handler(arg)