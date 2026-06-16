from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "visual-context-router"


def main() -> int:
    checks = [
        check_python_package(),
        check_mcp_tools(),
        check_personal_marketplace(),
        check_local_plugin_copy(),
    ]

    print("Visual Context Router doctor")
    print()
    for ok, name, detail in checks:
        status = "ok" if ok else "fail"
        print(f"[{status}] {name}")
        if detail:
            print(f"     {detail}")

    print()
    print("Codex note:")
    print("  If tools are not visible in the current thread, start a new Codex thread after installation.")
    print("  This plugin exposes routing tools; it does not automatically intercept every built-in screenshot.")
    return 0 if all(ok for ok, _, _ in checks) else 1


def check_python_package() -> tuple[bool, str, str]:
    try:
        import visual_context_router  # noqa: F401
    except Exception as exc:
        return False, "Python package import", str(exc)
    return True, "Python package import", "visual_context_router imports successfully"


def check_mcp_tools() -> tuple[bool, str, str]:
    request = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n'
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vcr_mcp_server.py")],
            input=request,
            text=True,
            capture_output=True,
            cwd=ROOT,
            timeout=10,
            check=True,
        )
        payload = decode_content_length_message(result.stdout)
        tools = {tool["name"] for tool in payload["result"]["tools"]}
    except Exception as exc:
        return False, "MCP tools/list", str(exc)

    expected = {"vcr_capture_route", "vcr_route", "vcr_observe", "vcr_crop"}
    missing = expected - tools
    if missing:
        return False, "MCP tools/list", f"missing tools: {', '.join(sorted(missing))}"
    return True, "MCP tools/list", ", ".join(sorted(tools))


def check_personal_marketplace() -> tuple[bool, str, str]:
    marketplace = Path.home() / ".agents" / "plugins" / "marketplace.json"
    if not marketplace.exists():
        return False, "Personal marketplace", f"not found: {marketplace}"
    try:
        data = json.loads(marketplace.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, "Personal marketplace", str(exc)

    plugins = data.get("plugins", [])
    for plugin in plugins:
        if plugin.get("name") == PLUGIN_NAME:
            return True, "Personal marketplace", f"entry found at {marketplace}"
    return False, "Personal marketplace", f"{PLUGIN_NAME} entry not found"


def check_local_plugin_copy() -> tuple[bool, str, str]:
    plugin_dir = Path.home() / "plugins" / PLUGIN_NAME
    required = [
        plugin_dir / ".codex-plugin" / "plugin.json",
        plugin_dir / ".mcp.json",
        plugin_dir / "scripts" / "vcr_mcp_server.py",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        return False, "Local plugin copy", "missing: " + ", ".join(str(path) for path in missing)
    return True, "Local plugin copy", str(plugin_dir)


def decode_content_length_message(output: str) -> dict:
    _, _, body = output.partition("\r\n\r\n")
    if not body:
        _, _, body = output.partition("\n\n")
    return json.loads(body)


if __name__ == "__main__":
    raise SystemExit(main())

