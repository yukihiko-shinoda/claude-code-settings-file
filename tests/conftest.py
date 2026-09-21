from pathlib import Path
from typing import Any
import json

import pytest
import yaml

REPOSITORY_ROOT = Path(__file__).parent.parent


@pytest.fixture
def yaml_settings() -> Any:
    return yaml.safe_load((REPOSITORY_ROOT / "managed-settings.yaml").read_text(encoding="utf-8"))


@pytest.fixture
def json_settings() -> Any:
    return json.loads((REPOSITORY_ROOT / "managed-settings.json").read_text(encoding="utf-8"))


@pytest.fixture
def permission_rules(yaml_settings: Any) -> list[str]:
    permissions = yaml_settings.get("permissions", {})
    return [rule for key in ("allow", "ask", "deny") for rule in permissions.get(key, [])]


@pytest.fixture
def valid_source(tmp_path: Path) -> Path:
    source = tmp_path / "valid.yaml"
    source.write_text("permissions:\n  deny:\n    - \"Read(~/.ssh/**)\"\n", encoding="utf-8")
    return source


@pytest.fixture
def duplicate_key_source(tmp_path: Path) -> Path:
    source = tmp_path / "duplicate.yaml"
    source.write_text("permissions:\n  deny:\n    - \"a\"\n  deny:\n    - \"b\"\n", encoding="utf-8")
    return source


@pytest.fixture
def list_source(tmp_path: Path) -> Path:
    source = tmp_path / "list.yaml"
    source.write_text("- \"a\"\n", encoding="utf-8")
    return source


@pytest.fixture
def destination(tmp_path: Path) -> Path:
    return tmp_path / "managed-settings.json"
