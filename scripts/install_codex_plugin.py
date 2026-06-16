from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


PLUGIN_NAME = "visual-context-router"
MARKETPLACE_NAME = "personal"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install Visual Context Router as a local Codex plugin."
    )
    parser.add_argument(
        "--skip-pip",
        action="store_true",
        help="Do not run pip install -e after copying the plugin.",
    )
    parser.add_argument(
        "--skip-codex-add",
        action="store_true",
        help="Do not run `codex plugin add visual-context-router@personal`.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned paths without writing files.",
    )
    args = parser.parse_args()

    source_root = Path(__file__).resolve().parents[1]
    home = Path.home()
    target_root = home / "plugins" / PLUGIN_NAME
    marketplace_path = home / ".agents" / "plugins" / "marketplace.json"

    print(f"Source:      {source_root}")
    print(f"Plugin dir:  {target_root}")
    print(f"Marketplace: {marketplace_path}")

    if args.dry_run:
        return 0

    copy_plugin(source_root, target_root)
    update_marketplace(marketplace_path)

    if not args.skip_pip:
        run_checked([sys.executable, "-m", "pip", "install", "-e", str(target_root)])

    if not args.skip_codex_add:
        try_codex_add()

    print()
    print("Visual Context Router is installed locally for Codex.")
    print("Start a new Codex thread, then ask:")
    print("  Use Visual Context Router to inspect my screen with vcr_capture_route.")
    return 0


def copy_plugin(source_root: Path, target_root: Path) -> None:
    if source_root.resolve() == target_root.resolve():
        print("Plugin is already in the target directory; skipping copy.")
        return

    target_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source_root,
        target_root,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
            ".vcr",
            "*.egg-info",
            "dist",
            "build",
        ),
    )
    print("Plugin files copied.")


def update_marketplace(marketplace_path: Path) -> None:
    marketplace_path.parent.mkdir(parents=True, exist_ok=True)
    if marketplace_path.exists():
        data = json.loads(marketplace_path.read_text(encoding="utf-8"))
    else:
        data = {
            "name": MARKETPLACE_NAME,
            "interface": {"displayName": "Personal"},
            "plugins": [],
        }

    data.setdefault("name", MARKETPLACE_NAME)
    data.setdefault("interface", {}).setdefault("displayName", "Personal")
    plugins = data.setdefault("plugins", [])

    entry = marketplace_entry()
    plugins[:] = [plugin for plugin in plugins if plugin.get("name") != PLUGIN_NAME]
    plugins.append(entry)

    marketplace_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("Marketplace entry written.")


def marketplace_entry() -> dict[str, Any]:
    return {
        "name": PLUGIN_NAME,
        "source": {
            "source": "local",
            "path": f"./plugins/{PLUGIN_NAME}",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }


def try_codex_add() -> None:
    command = ["codex", "plugin", "add", f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"]
    try:
        run_checked(command)
    except FileNotFoundError:
        print("Codex CLI was not found; install from the Codex app or run manually:")
        print(f"  {' '.join(command)}")
    except subprocess.CalledProcessError:
        print("Codex CLI install command failed. Run manually after opening Codex:")
        print(f"  {' '.join(command)}")


def run_checked(command: list[str]) -> None:
    print("+ " + " ".join(command))
    subprocess.run(command, check=True)


if __name__ == "__main__":
    raise SystemExit(main())

