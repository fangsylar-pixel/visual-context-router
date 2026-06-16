import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install_codex_plugin.py"


def _load_installer():
    spec = importlib.util.spec_from_file_location("install_codex_plugin", INSTALLER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_marketplace_entry_shape() -> None:
    installer = _load_installer()

    entry = installer.marketplace_entry()

    assert entry["name"] == "visual-context-router"
    assert entry["source"]["path"] == "./plugins/visual-context-router"
    assert entry["policy"]["installation"] == "AVAILABLE"
    assert entry["policy"]["authentication"] == "ON_INSTALL"


def test_update_marketplace_replaces_existing_entry(tmp_path: Path) -> None:
    installer = _load_installer()
    marketplace = tmp_path / ".agents" / "plugins" / "marketplace.json"
    marketplace.parent.mkdir(parents=True)
    marketplace.write_text(
        json.dumps(
            {
                "name": "personal",
                "interface": {"displayName": "Personal"},
                "plugins": [
                    {"name": "visual-context-router", "source": {"path": "old"}},
                    {"name": "other", "source": {"path": "./plugins/other"}},
                ],
            }
        ),
        encoding="utf-8",
    )

    installer.update_marketplace(marketplace)

    data = json.loads(marketplace.read_text(encoding="utf-8"))
    names = [plugin["name"] for plugin in data["plugins"]]

    assert names == ["other", "visual-context-router"]
    assert data["plugins"][-1]["source"]["path"] == "./plugins/visual-context-router"
