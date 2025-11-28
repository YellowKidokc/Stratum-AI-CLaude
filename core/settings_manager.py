from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path


class SettingsManager:
    def __init__(self, ini_path: Path) -> None:
        self._path = Path(ini_path)
        self._config = ConfigParser()

    # ---------- load / init ----------

    def load(self) -> None:
        if not self._path.exists():
            self._create_default()
        self._config.read(self._path, encoding="utf-8")

    def _create_default(self) -> None:
        self._config["openai"] = {"api_key": "", "model": "gpt-4.1"}
        self._config["claude"] = {"api_key": "", "model": "claude-3.5"}
        self._config["deepseek"] = {"api_key": "", "model": "deepseek-chat"}
        self._config["stratum"] = {"theme": "dark", "window_on_top": "false"}
        with self._path.open("w", encoding="utf-8") as f:
            self._config.write(f)

    # ---------- persist ----------

    def save(self) -> None:
        with self._path.open("w", encoding="utf-8") as f:
            self._config.write(f)

    # ---------- convenience helpers ----------

    @property
    def config(self) -> ConfigParser:
        return self._config

    def get_api_key(self, section: str) -> str:
        return self._config.get(section, "api_key", fallback="")

    def set_api_key(self, section: str, value: str) -> None:
        if section not in self._config:
            self._config[section] = {}
        self._config[section]["api_key"] = value

    def is_first_run(self) -> bool:
        # "first run" = no OpenAI key at all
        return not self.get_api_key("openai").strip()
