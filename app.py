from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.settings_manager import SettingsManager
from core.command_registry import CommandRegistry
from core.hotkeys import register_hotkeys
from core.hotstrings import HotstringEngine
from core.vault_manager import VaultManager
from core.ai_clients import create_ai_manager_from_settings
from core.tts_engine import TTSEngine
from ui.main_window import create_main_window
from ui.api_key_dialog import ApiKeyDialog


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    config_dir = base_dir / "config"
    config_dir.mkdir(exist_ok=True)

    # Settings
    settings = SettingsManager(config_dir / "settings.ini")
    settings.load()

    app = QApplication([])

    # First-run API key dialog
    if settings.is_first_run():
        dlg = ApiKeyDialog()
        if dlg.exec() == dlg.Accepted:
            openai_key, claude_key, deepseek_key = dlg.get_values()
            if openai_key:
                settings.set_api_key("openai", openai_key)
            if claude_key:
                settings.set_api_key("claude", claude_key)
            if deepseek_key:
                settings.set_api_key("deepseek", deepseek_key)
            settings.save()

    # Core systems
    registry = CommandRegistry(config_dir / "commands.json")
    registry.load()

    vault = VaultManager(config_dir / "vault.json")
    ai_manager = create_ai_manager_from_settings(settings)
    tts_engine = TTSEngine()

    # Hotkeys + hotstrings
    register_hotkeys(registry)
    hotstring_engine = HotstringEngine(registry)
    hotstring_engine.register_all()

    # Main window
    window = create_main_window(
        settings=settings,
        command_registry=registry,
        vault_manager=vault,
        ai_manager=ai_manager,
        tts_engine=tts_engine
    )
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
