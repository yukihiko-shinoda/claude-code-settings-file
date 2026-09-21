from pathlib import Path
from typing import Any
import json

from converter.unique_key_loader import UniqueKeySafeLoader


class SettingsConverter:
    """Convert a YAML settings file into the JSON file that Claude Code reads."""

    def __init__(self, source: Path, destination: Path) -> None:
        self.source = source
        self.destination = destination

    def convert(self) -> None:
        settings = self._load()
        self.destination.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def _load(self) -> dict[str, Any]:
        loader = UniqueKeySafeLoader(self.source.read_text(encoding="utf-8"))
        try:
            loaded = loader.get_single_data()
        finally:
            loader.dispose()
        if not isinstance(loaded, dict):
            msg = f"{self.source} must contain a mapping at the top level, but got {type(loaded).__name__}"
            raise TypeError(msg)
        return loaded
