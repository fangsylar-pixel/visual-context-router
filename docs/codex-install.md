# Install As A Codex Plugin

Visual Context Router includes a Codex plugin manifest and an MCP server. After installation, Codex can call:

- `vcr_capture_route`
- `vcr_route`
- `vcr_observe`
- `vcr_crop`

## One Command

Clone the repository, then run:

```bash
python scripts/install_codex_plugin.py
```

The installer:

- copies the plugin to `~/plugins/visual-context-router`
- creates or updates `~/.agents/plugins/marketplace.json`
- runs `pip install -e ~/plugins/visual-context-router`
- tries to run `codex plugin add visual-context-router@personal`

After it finishes, start a new Codex thread and ask:

```text
Use Visual Context Router to inspect my screen with vcr_capture_route.
```

## Manual Install

If the one-command installer cannot run the Codex CLI command, run this manually:

```bash
codex plugin add visual-context-router@personal
```

Then start a new Codex thread so the plugin tools are loaded.

## Important Limitation

This plugin gives Codex callable routing tools. It does not globally intercept every built-in screenshot path. To use the low-token path, ask Codex to call `vcr_capture_route` before requesting or analyzing a full screenshot.

