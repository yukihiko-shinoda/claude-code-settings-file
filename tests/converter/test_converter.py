from pathlib import Path
import json

import pytest
from yaml.constructor import ConstructorError

from converter.converter import SettingsConverter


class TestSettingsConverter:
    def test_convert_writes_json(self, valid_source: Path, destination: Path) -> None:
        SettingsConverter(valid_source, destination).convert()
        assert json.loads(destination.read_text(encoding="utf-8")) == {"permissions": {"deny": ["Read(~/.ssh/**)"]}}

    def test_convert_rejects_duplicate_keys(self, duplicate_key_source: Path, destination: Path) -> None:
        with pytest.raises(ConstructorError, match="found duplicate key 'deny'"):
            SettingsConverter(duplicate_key_source, destination).convert()
        assert not destination.exists()

    def test_convert_rejects_non_mapping(self, list_source: Path, destination: Path) -> None:
        with pytest.raises(TypeError, match="must contain a mapping at the top level"):
            SettingsConverter(list_source, destination).convert()
