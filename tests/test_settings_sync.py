from typing import Any


class TestSettingsSync:
    def test_json_matches_yaml(self, yaml_settings: Any, json_settings: Any) -> None:
        """Ensure managed-settings.json is regenerated after managed-settings.yaml changes (run `uv run convert`)."""
        assert json_settings == yaml_settings
