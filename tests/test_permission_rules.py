import re

# Read/Edit rules anchor a single leading "/" at the settings source, not at the filesystem root. Absolute paths need "//".
SINGLE_SLASH_PATH_RULE = re.compile(r"^(Read|Edit)\(/(?!/)")


class TestPermissionRules:
    def test_path_rules_do_not_start_with_single_slash(self, permission_rules: list[str]) -> None:
        """Ensure Read/Edit rules use `//` for absolute paths, since a single leading `/` is settings-relative.

        - Read and Edit | Configure permissions - Claude Code Docs
          https://code.claude.com/docs/en/permissions#read-and-edit

        > A pattern like `/Users/alice/file` isn't an absolute path. The single leading slash anchors at the settings
        > source, not the filesystem root. Use `//Users/alice/file` for absolute paths.
        """
        offenders = [rule for rule in permission_rules if SINGLE_SLASH_PATH_RULE.match(rule)]
        assert offenders == []
