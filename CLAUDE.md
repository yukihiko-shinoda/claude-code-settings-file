# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Claude Code's `managed-settings.json` cannot hold comments, and its specification changes often and contains bugs. This repository keeps the settings in `managed-settings.yaml`, where comments record why each setting exists, and generates `managed-settings.json` from it with a small Python converter.

- `managed-settings.yaml` is the source of truth. Edit it, never `managed-settings.json`.
- `managed-settings.json` is generated output and is committed. The conversion drops YAML comments.
- `managed-settings.json` is meant to be installed as Claude Code's managed settings file (`/etc/claude-code/managed-settings.json` on Linux), not as user or project settings. See the README's Quickstart.

A hand-edited or stale `managed-settings.json` drifts away from `managed-settings.yaml`, and the sync test fails.

## Workflow

Run the following all steps after every `managed-settings.yaml` change:

1. `uv run convert` regenerates `managed-settings.json` (optional positional arguments: source path, destination path).
2. `uv run pytest` verifies that `managed-settings.json` matches `managed-settings.yaml`.

Other commands:

- `uv sync` installs dependencies.
- `uv run pytest tests/test_settings_sync.py::TestSettingsSync::test_json_matches_yaml` runs a single test; the same `path::Class::method` form works for the tests under `tests/converter/`.
- CI (`.github/workflows/test.yaml`) runs only `uv sync` and `uv run pytest`. There is no linter or type-checker configured in this repository.

## Architecture

- `converter/converter.py` (flat layout, the `converter` package at the repository root): `SettingsConverter(source, destination).convert()` loads the YAML with `UniqueKeySafeLoader` and writes JSON (2-space indent, `ensure_ascii=False`, trailing newline). A top-level value that is not a mapping raises `TypeError`, so an empty file or a bare list fails.
- `converter/unique_key_loader.py`: `UniqueKeySafeLoader` is a `yaml.SafeLoader` that raises `ConstructorError` for a mapping that repeats a key. Plain `SafeLoader` keeps the last value silently, so a second `deny:` list would drop the first one without any warning. YAML merge keys (`<<`) are exempt.
- `converter/__init__.py`: `main()` is the argparse wrapper behind the `convert` script. The defaults are `managed-settings.yaml` and `managed-settings.json` in the current directory.
- `tests/converter/`: unit tests for the converter modules, mirroring the module path. Their input files are built by fixtures in `tests/conftest.py` under `tmp_path`.
- `tests/test_settings_sync.py`: compares the parsed `managed-settings.yaml` with the parsed `managed-settings.json` (comments are not compared). Its fixtures live in `tests/conftest.py` and read the files at the repository root. It intentionally does not mirror a module path.

## Conventions in managed-settings.yaml

- Never repeat a key in the same mapping (for example two `deny:` lists under `permissions`). The converter rejects it, because a plain YAML loader would silently drop the earlier one.
- Quote every list value with double quotes. An unquoted leading `*` (for example `**/*.pem`) is a YAML alias and fails to load.
- Comment each non-obvious setting in this order: a one-line reason, the Claude Code docs page title with its URL, then verbatim quote lines prefixed with `# >`. Keep the amount of comments close to neighbouring entries.
- Path syntax differs between sections:
  - `permissions` Read/Edit rules anchor a single leading `/` at the settings source. Absolute paths need `//` (for example `Read(//run/secrets/*)`).
  - `sandbox.filesystem` uses standard paths, where `/run/secrets/` is already absolute.
- Secret paths appear in both `permissions.deny` and `sandbox.filesystem.denyRead`/`denyWrite` on purpose. Permission rules cover Claude's built-in Read and Edit tools, which run outside the sandbox, while the sandbox settings cover Bash subprocesses. Keep both lists in step when adding a path. The one exception is `~/.config/gh/`, which is not in `denyRead` (see "GitHub credentials and network").

## GitHub credentials and network

These settings interact, so change them together:

- `sandbox.credentials.files` masks `~/.config/gh/hosts.yml` (`mode: mask`, an `extract` regex for the token only, `onExtractNoMatch: deny`). Masking needs `sandbox.network.tlsTerminate`, and every `injectHosts` host must also be in `sandbox.network.allowedDomains`. It replaced the earlier `GH_TOKEN` entry in `credentials.envVars`, so a `GH_TOKEN` variable passed to Claude Code is no longer masked.
- `~/.config/gh/` is intentionally absent from `sandbox.filesystem.denyRead`. With it present and `allowRead` re-opening `hosts.yml`, `extract` stops working: the whole file becomes one sentinel and `gh` fails with `invalid format` (verified by testing; see the comment in `managed-settings.yaml`). The token stays protected by the mask, `permissions.deny`, and `denyWrite`.
- `github.com` is in `allowedDomains` so that `git fetch` connects, but not in `injectHosts`. `git` over HTTPS cannot authenticate with the masked token (anthropics/claude-code#95752), so private clone and push happen outside the sandbox.
- In auto mode, Claude can name extra hosts on a single Bash command (`allowed_domains`). Nothing is written to settings, and `allowManagedDomainsOnly` or `strictAllowlist` would make Claude Code refuse it. Neither is set today.

## Working inside the sandbox

- `uv` fails with a read-only cache error. Prefix `uv` commands with `UV_CACHE_DIR="$TMPDIR/uv-cache"`.
- Network access to `pypi.org` and `files.pythonhosted.org` is blocked by default. It matters only when dependencies change.
- The sandbox mounts `/dev/null` over its protected paths, so the following files appear in the repository root as untracked character devices. They are not project files; never `git add -A` or `git add .`:
  - `.bashrc`, `.bash_profile`, `.profile`, `.zprofile`, `.zshrc`
  - `.gitconfig`, `.gitmodules`, `.ripgreprc`, `.mcp.json`
  - `.pem`, `config.yml`, `.idea`, `.vscode`
- The root `managed-settings.json` is not `.claude/settings.json`. The latter configures Claude Code sessions in this repository and is write-protected by the sandbox.
- The sandbox that a session runs under comes from the installed `/etc/claude-code/managed-settings.json`, which is also write-protected. Regenerating the root `managed-settings.json` does not change the running session; the user reinstalls it (README Quickstart, step 1). Whether a running session picks up the new copy without a restart is unverified.
