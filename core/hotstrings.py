from __future__ import annotations

from typing import Callable

from .command_registry import CommandRegistry


class HotstringEngine:
    """
    Placeholder / skeleton for your future hotstring system.
    This will eventually mirror your old hotstrings backend,
    but driven by CommandRegistry.
    """

    def __init__(self, registry: CommandRegistry) -> None:
        self._registry = registry

    def register_all(self) -> None:
        # TODO: integrate your real hotstring engine here.
        # For now, this is a no-op so Stratum still runs.
        for cmd in self._registry.all():
            if cmd.hotstring:
                # later: register with your hotstring library and
                # call self._registry.execute(cmd.id) when triggered.
                pass
