from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    examples = Path(__file__).resolve().parents[1] / "examples"
    examples.mkdir(exist_ok=True)

    before = Image.new("RGB", (960, 600), "#f7f8fb")
    draw = ImageDraw.Draw(before)
    draw.rectangle((40, 40, 920, 100), fill="#ffffff", outline="#c8ccd6")
    draw.rectangle((64, 58, 300, 82), fill="#eef1f7", outline="#c8ccd6")
    draw.rectangle((760, 54, 880, 86), fill="#2563eb")
    draw.rectangle((80, 150, 460, 210), fill="#ffffff", outline="#d4d8e2")
    draw.rectangle((80, 240, 880, 500), fill="#ffffff", outline="#d4d8e2")
    before.save(examples / "sample-screen.png")

    after = before.copy()
    draw = ImageDraw.Draw(after)
    draw.rectangle((620, 130, 900, 320), fill="#ffffff", outline="#1f2937", width=3)
    draw.rectangle((650, 265, 760, 300), fill="#2563eb")
    draw.rectangle((780, 265, 870, 300), fill="#eef1f7", outline="#c8ccd6")
    after.save(examples / "sample-screen-after.png")


if __name__ == "__main__":
    main()

