import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_make_readme_assets_generates_gif_and_png() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/make_readme_assets.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "visual-context-router-flow.gif" in result.stdout
    assert (ROOT / "assets" / "visual-context-router-flow.gif").exists()
    assert (ROOT / "assets" / "visual-context-router-flow.png").exists()
