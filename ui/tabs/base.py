from __future__ import annotations

from typing import Protocol

from PySide6.QtWidgets import QWidget


class Tab(Protocol):
    widget: QWidget

    def on_activate(self) -> None:  # pragma: no cover - UI hook
        """Called when the tab becomes active."""

    def on_deactivate(self) -> None:  # pragma: no cover - UI hook
        """Called when the tab is hidden."""


class BaseTab(QWidget):
    """Convenience base class providing no-op activate/deactivate hooks."""

    def on_activate(self) -> None:  # pragma: no cover - UI hook
        pass

    def on_deactivate(self) -> None:  # pragma: no cover - UI hook
        pass
