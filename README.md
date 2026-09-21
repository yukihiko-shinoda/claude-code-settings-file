# claude-code-settings-file

A best-practice Claude Code `managed-settings.json` for running Claude Code in a Docker dev container. The reason for every setting is recorded as a comment in [managed-settings.yaml](managed-settings.yaml), and `managed-settings.json` is generated from it.

## Advantage

Claude Code's settings specification changes often and contains bugs, and a safe configuration needs several settings that interact: permission rules for Claude's built-in tools, the sandbox for shell commands, and credential handling. The documentation's caveats are easy to miss.

A configuration that looks protective can silently protect nothing. Two examples:

- A permission rule such as `Read(/run/secrets/*)` is not an absolute path, because a single leading `/` anchors at the settings source. Absolute paths need `//`.
- `sandbox.filesystem.denyWrite` silently ignores rules with a wildcard in the middle of the path on Linux ([anthropics/claude-code#92684](https://github.com/anthropics/claude-code/issues/92684)).

This `managed-settings.json` is a ready-made baseline that applies the following:

- The sandbox is required. Claude Code fails instead of running without it, and the unsandboxed retry escape hatch is off.
- Secret paths are denied twice: in `permissions` for Claude's built-in Read, Edit, and Write tools, and in `sandbox.filesystem` for shell commands.
- The GitHub token in `~/.config/gh/hosts.yml` is masked, so the GitHub CLI works without exposing the token to sandboxed commands.
- Risky but necessary operations, such as `git push` and `rm`, ask for confirmation instead of being denied.
  - Currently, `git push` is not supported by Claude Code inside the sandbox (see below)

Every non-obvious entry in [managed-settings.yaml](managed-settings.yaml) carries its reason, the documentation page, and a verbatim quote, so each setting can be checked against its source. A test verifies that `managed-settings.json` matches `managed-settings.yaml`.

## Quickstart

The settings assume that Claude Code runs inside a Docker container and that the sandbox is available. On Linux and WSL2, the sandbox needs the packages listed in the [sandboxing documentation](https://code.claude.com/docs/en/sandboxing).

Run the following all steps:

1. Install `managed-settings.json` as the managed settings file. On Linux and WSL2, the file is `/etc/claude-code/managed-settings.json`, and writing it needs root. Managed settings take precedence over user and project settings, so they apply to every project in the container and a user cannot override them. The `hosts.yml` masking is honored only from user settings, managed settings, and the `--settings` flag, so a project `.claude/settings.json` does not work for it.

   ```bash
   install -D -m 644 managed-settings.json /etc/claude-code/managed-settings.json
   ```

2. Save the GitHub token to `~/.config/gh/hosts.yml`, only if Claude Code needs the GitHub CLI. Run this in your own shell, not through Claude, because `/run/secrets/` is denied inside the sandbox. `--insecure-storage` writes the token into `hosts.yml` as plain text, which is the file the masking covers:

   ```bash
   gh auth login --hostname github.com --with-token --insecure-storage < /run/secrets/<secret-name>
   ```

   Do not pass the token to Claude Code in the `GH_TOKEN` environment variable. This baseline masks `hosts.yml` only, so a `GH_TOKEN` variable would reach sandboxed commands unmasked.

3. Check the result inside the session:
   - `/sandbox` lists the applied sandbox configuration.
   - Asking Claude to run `cat ~/.config/gh/hosts.yml` in a sandboxed command prints a placeholder in place of the real token on Linux and WSL2. On macOS the read fails instead.
   - Asking Claude to run `gh api user` succeeds, which shows that the proxy substitutes the real token on requests to `api.github.com`.

<!-- markdownlint-disable-next-line MD026 -->
## How do I...

### How do I use this outside a Docker container?

Remove `enableWeakerNestedSandbox` from your copy. It exists for unprivileged containers where bubblewrap cannot mount a fresh `/proc`, and it weakens the isolation the sandbox provides.

### How do I protect another secret path?

Add the path to both places in `managed-settings.yaml`, because each covers a different tool:

- `permissions.deny` as a `Read(...)` rule for Claude's built-in tools. It also blocks the Edit and Write tools on the same path, so no `Edit(...)` rule is needed.
- `sandbox.filesystem.denyRead` and `denyWrite` for shell commands.

Write an absolute path with `//` in `permissions` and with a single `/` in `sandbox.filesystem`. Quote every value, because YAML reads an unquoted leading `*` as an alias.

Do not add `~/.config/gh/` to `sandbox.filesystem.denyRead`. It breaks the masking of `hosts.yml`; see [How do I fix `gh` failing with `invalid format` inside the sandbox?](#how-do-i-fix-gh-failing-with-invalid-format-inside-the-sandbox).

Then convert `managed-settings.yaml` to `managed-settings.json` and run the test that checks the two files match:

```bash
uv run convert
uv run pytest
```

The conversion drops the comments. The test fails while the two files differ.

Install the regenerated `managed-settings.json` again as in step 1 of the [Quickstart](#quickstart), because Claude Code reads the installed copy.

### How do I let the GitHub CLI reach another host?

Add the host to `sandbox.network.allowedDomains`. Add it to the `injectHosts` of the `~/.config/gh/hosts.yml` entry under `sandbox.credentials.files` as well if the token must be sent to it. The masked token is substituted only on requests to the hosts in `injectHosts`.

`github.com` is in `allowedDomains` so that `git fetch` can connect, but it is not in `injectHosts`. Requests to it therefore carry no token from `hosts.yml`. Adding it to `injectHosts` does not make `git` authenticate either; see [How do I clone or push a private repository?](#how-do-i-clone-or-push-a-private-repository).

### How do I clone or push a private repository?

Run `git clone` and `git push` in your own shell outside the sandbox, not through Claude. Inside the sandbox, `git` over HTTPS cannot authenticate with the masked token, and neither a credential helper such as `gh auth setup-git` nor `github.com` in `injectHosts` changes that. It is a limitation of Claude Code, tracked in [anthropics/claude-code#95752](https://github.com/anthropics/claude-code/issues/95752).

The following all keep working inside the sandbox:

- Claude can read and edit a repository that you cloned outside the sandbox.
- Commands that call the API, such as `gh pr create`.
- `git fetch` from a public repository, because it needs no token.

`sandbox.excludedCommands` can run `git` outside the sandbox, but this baseline does not use it. An excluded command runs with no filesystem or network isolation, so it can read the real credentials, and so can anything `git` invokes, such as hooks. If you add it, keep the `git push*` ask rules.

### How do I fix `gh` failing with `invalid format` inside the sandbox?

Remove `~/.config/gh/` from `sandbox.filesystem.denyRead`, together with any `sandbox.filesystem.allowRead` entry that re-opens `hosts.yml`. This baseline leaves the directory out of `denyRead` for that reason.

The symptom is that `cat ~/.config/gh/hosts.yml` in a sandboxed command prints one line that starts with `fake_value_`, instead of a file in which only the token is a placeholder. `gh` cannot parse that line, so it exits with `invalid format`.

Removing the entry does not expose the token. The evidence comes from testing this baseline:

- With the entry present, the output of `cat ~/.config/gh/hosts.yml` contained no `github_pat_` string, so the real token was already hidden. Only the file format was broken.
- With the entry removed, `gh api user` succeeds. The mask on `hosts.yml` is what keeps the real token out of sandboxed commands.
- The `Read` and `Edit` deny rules for `~/.config/gh/**` in `permissions`, and the `denyWrite` entry, stay in place.

Two limits apply:

- The cause is not identified. The [sandboxing documentation](https://code.claude.com/docs/en/sandboxing#mask-credential-files) describes the whole-file replacement only for a `mask` entry without `extract`, and this baseline sets `extract`. A similar combination of `denyRead` and `allowRead` is reported in [anthropics/claude-code#95135](https://github.com/anthropics/claude-code/issues/95135), where `hosts.yml` disappears entirely instead.
- Sandboxed commands can read the other files in `~/.config/gh/`. In the tested container, the directory held only `config.yml` and `hosts.yml`.

The fix is a settings edit only, so reverting it restores the previous behavior.
