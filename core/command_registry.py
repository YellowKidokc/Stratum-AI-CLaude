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

    # ---------- CRUD operations ----------

    def save(self) -> None:
        """Save all commands to JSON file."""
        data = []
        for cmd in self._commands.values():
            data.append({
                "id": cmd.id,
                "label": cmd.label,
                "action": cmd.action,
                "hotkey": cmd.hotkey,
                "hotstring": cmd.hotstring,
                "tags": cmd.tags or [],
            })
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_command(self, cmd: Command) -> bool:
        """Add a new command to the registry and save."""
        if cmd.id in self._commands:
            return False
        self._commands[cmd.id] = cmd
        self.save()
        return True

    def update_command(
        self,
        command_id: str,
        *,
        label: str | None = None,
        action: str | None = None,
        hotkey: str | None = None,
        hotstring: str | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """Update an existing command."""
        cmd = self._commands.get(command_id)
        if not cmd:
            return False

        if label is not None:
            cmd.label = label
        if action is not None:
            cmd.action = action
        if hotkey is not None:
            cmd.hotkey = hotkey
        if hotstring is not None:
            cmd.hotstring = hotstring
        if tags is not None:
            cmd.tags = tags

        self.save()
        return True

    def remove_command(self, command_id: str) -> bool:
        """Delete a command from the registry."""
        if command_id in self._commands:
            del self._commands[command_id]
            self.save()
            return True
        return False