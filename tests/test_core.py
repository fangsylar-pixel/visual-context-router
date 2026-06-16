from pathlib import Path

from PIL import Image, ImageDraw

from visual_context_router import crop_roi, estimate_tokens, observe, route_observation
from visual_context_router.core import image_change_score


def _make_image(path: Path, changed: bool = False) -> None:
    image = Image.new("RGB", (320, 200), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 24, 180, 62), outline="black", width=2)
    draw.rectangle((220, 150, 300, 184), fill=(30, 90, 210))
    if changed:
        draw.rectangle((42, 92, 260, 122), fill=(240, 90, 90))
    image.save(path)


def test_image_change_score_detects_changes(tmp_path: Path) -> None:
    before = tmp_path / "before.png"
    after = tmp_path / "after.png"
    _make_image(before)
    _make_image(after, changed=True)

    score = image_change_score(Image.open(before), Image.open(after))

    assert score > 0


def test_observe_returns_wireframe_and_token_estimate(tmp_path: Path) -> None:
    before = tmp_path / "before.png"
    after = tmp_path / "after.png"
    _make_image(before)
    _make_image(after, changed=True)

    observation = observe(after, previous_path=before, change_threshold=0.0001)

    assert observation.changed is True
    assert "Screen 320x200" in observation.to_wireframe()
    assert estimate_tokens(observation).full_image_tokens >= 85
    assert observation.to_dict(include_route=True)["route"]["strategy"] in {
        "wireframe_plus_roi",
        "wireframe_only",
        "full_image",
    }


def test_route_skips_unchanged_screen(tmp_path: Path) -> None:
    before = tmp_path / "before.png"
    after = tmp_path / "after.png"
    _make_image(before)
    _make_image(after)

    observation = observe(after, previous_path=before)
    decision = route_observation(observation)

    assert decision.strategy == "skip"
    assert decision.include_full_image is False
    assert decision.include_wireframe is False


def test_crop_roi_writes_file(tmp_path: Path) -> None:
    image = tmp_path / "screen.png"
    out = tmp_path / "roi.png"
    _make_image(image)

    crop_roi(image, bbox=(0.0, 0.0, 0.5, 0.5), out_path=out)

    assert out.exists()
    assert Image.open(out).size == (160, 100)
