# Install As A Codex Plugin

Visual Context Router includes a Codex plugin manifest and an MCP server. After installation, Codex can call:

- `vcr_capture_route`
- `vcr_watch`
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

For repeated screen work:

```text
Use Visual Context Router with vcr_watch before each screen observation.
```

## Manual Install

If the one-command installer cannot run the Codex CLI command, run this manually:

```bash
codex plugin add visual-context-router@personal
```

On some Windows Codex Desktop installs, the `codex` executable may be present under `WindowsApps` but blocked from direct shell execution. In that case the installer still writes the local marketplace entry. Open Codex, refresh/reopen the plugin UI, and install `visual-context-router` from the Personal marketplace.

Then start a new Codex thread so the plugin tools are loaded.

## Verify Install

Run:

```bash
python scripts/doctor.py
```

Expected checks:

- Python package import: ok
- MCP tools/list: ok
- Personal marketplace: ok
- Local plugin copy: ok

If these pass but Codex still cannot call `vcr_capture_route`, start a new thread. Tool availability is determined when a thread starts.

## Important Limitation

This plugin gives Codex callable routing tools. It does not globally intercept every built-in screenshot path. To use the low-token path, ask Codex to call `vcr_capture_route` before requesting or analyzing a full screenshot.
