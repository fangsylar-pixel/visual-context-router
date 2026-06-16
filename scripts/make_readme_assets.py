from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
WIDTH = 1280
HEIGHT = 720

BG = "#0f172a"
PANEL = "#111827"
PANEL_ALT = "#172033"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"
BLUE = "#38bdf8"
GREEN = "#22c55e"
AMBER = "#f59e0b"
RED = "#ef4444"
BORDER = "#334155"


def main() -> int:
    ASSETS.mkdir(exist_ok=True)
    frames = [draw_frame(step) for step in range(6)]
    gif_path = ASSETS / "visual-context-router-flow.gif"
    png_path = ASSETS / "visual-context-router-flow.png"
    frames[0].save(png_path)
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=[900, 900, 900, 900, 900, 1200],
        loop=0,
        optimize=False,
    )
    print(gif_path)
    print(png_path)
    return 0


def draw_frame(step: int) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    fonts = load_fonts()

    draw.text((56, 42), "Visual Context Router", fill=TEXT, font=fonts["title"])
    draw.text(
        (56, 88),
        "Stop sending full screenshots to agents.",
        fill=MUTED,
        font=fonts["subtitle"],
    )

    draw_before_panel(draw, fonts, active=step == 0)
    draw_pipeline(draw, fonts, step)
    draw_after_panel(draw, fonts, active=step >= 4)
    draw_savings(draw, fonts, active=step == 5)

    return image


def draw_before_panel(draw: ImageDraw.ImageDraw, fonts: dict[str, ImageFont.ImageFont], active: bool) -> None:
    x, y, w, h = 56, 150, 320, 360
    rounded(draw, (x, y, x + w, y + h), PANEL, BLUE if active else BORDER)
    draw.text((x + 24, y + 24), "Without routing", fill=TEXT, font=fonts["heading"])
    draw.text((x + 24, y + 62), "Full screenshot", fill=MUTED, font=fonts["body"])
    screen = (x + 24, y + 108, x + w - 24, y + 255)
    rounded(draw, screen, "#1e293b", BORDER)
    draw.rectangle((screen[0] + 18, screen[1] + 18, screen[2] - 18, screen[1] + 48), fill="#334155")
    draw.rectangle((screen[0] + 18, screen[1] + 68, screen[2] - 70, screen[1] + 94), fill="#475569")
    draw.rectangle((screen[0] + 18, screen[1] + 112, screen[2] - 18, screen[1] + 130), fill="#334155")
    draw.text((x + 24, y + 290), "768 image tokens", fill=RED, font=fonts["metric"])
    draw.text((x + 24, y + 326), "Every pixel goes to the model", fill=MUTED, font=fonts["small"])


def draw_pipeline(draw: ImageDraw.ImageDraw, fonts: dict[str, ImageFont.ImageFont], step: int) -> None:
    nodes = [
        ("Diff", "changed?"),
        ("Wireframe", "UI regions"),
        ("ROI", "local crops"),
        ("Route", "send less"),
    ]
    start_x = 410
    y = 260
    gap = 124
    node_w = 104
    for index, (title, caption) in enumerate(nodes):
        x = start_x + index * gap
        active = step >= index + 1
        color = GREEN if active else BORDER
        rounded(draw, (x, y, x + node_w, y + 86), PANEL_ALT, color)
        draw.text((x + 18, y + 18), title, fill=TEXT if active else MUTED, font=fonts["node"])
        draw.text((x + 18, y + 52), caption, fill=MUTED, font=fonts["small"])
        if index < len(nodes) - 1:
            arrow_color = GREEN if step >= index + 2 else BORDER
            draw.line((x + node_w + 4, y + 43, x + gap - 10, y + 43), fill=arrow_color, width=4)
            draw.polygon(
                [(x + gap - 10, y + 43), (x + gap - 22, y + 35), (x + gap - 22, y + 51)],
                fill=arrow_color,
            )

    draw.text((430, 384), "Local pre-model routing", fill=MUTED, font=fonts["body"])


def draw_after_panel(draw: ImageDraw.ImageDraw, fonts: dict[str, ImageFont.ImageFont], active: bool) -> None:
    x, y, w, h = 904, 150, 320, 360
    rounded(draw, (x, y, x + w, y + h), PANEL, GREEN if active else BORDER)
    draw.text((x + 24, y + 24), "With VCR", fill=TEXT, font=fonts["heading"])
    draw.text((x + 24, y + 62), "wireframe_plus_roi", fill=GREEN if active else MUTED, font=fonts["body"])

    lines = [
        "Screen 960x600",
        "Changed: yes",
        "Panel[1] bbox=(0.645...)",
        "Panel[2] bbox=(0.043...)",
        "ROI crops: 2",
    ]
    yy = y + 108
    for line in lines:
        rounded(draw, (x + 24, yy, x + w - 24, yy + 28), "#1f2937", "#1f2937")
        draw.text((x + 36, yy + 6), line, fill=TEXT if active else MUTED, font=fonts["mono"])
        yy += 38

    draw.text((x + 24, y + 312), "65 routed text tokens", fill=GREEN, font=fonts["metric"])


def draw_savings(draw: ImageDraw.ImageDraw, fonts: dict[str, ImageFont.ImageFont], active: bool) -> None:
    x, y = 430, 500
    rounded(draw, (x, y, x + 390, y + 100), "#052e16" if active else PANEL, GREEN if active else BORDER)
    draw.text((x + 24, y + 20), "Saved 703 tokens", fill=GREEN if active else MUTED, font=fonts["heading"])
    draw.text((x + 24, y + 58), "91.5% less visual context on the sample screen", fill=TEXT, font=fonts["body"])


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str) -> None:
    draw.rounded_rectangle(box, radius=16, fill=fill, outline=outline, width=2)


def load_fonts() -> dict[str, ImageFont.ImageFont]:
    candidates = [
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    font_path = next((path for path in candidates if path.exists()), None)
    mono_path = Path("C:/Windows/Fonts/consola.ttf")
    if font_path:
        return {
            "title": ImageFont.truetype(str(font_path), 38),
            "subtitle": ImageFont.truetype(str(font_path), 22),
            "heading": ImageFont.truetype(str(font_path), 25),
            "body": ImageFont.truetype(str(font_path), 18),
            "small": ImageFont.truetype(str(font_path), 14),
            "node": ImageFont.truetype(str(font_path), 20),
            "metric": ImageFont.truetype(str(font_path), 24),
            "mono": ImageFont.truetype(str(mono_path if mono_path.exists() else font_path), 14),
        }
    default = ImageFont.load_default()
    return {
        "title": default,
        "subtitle": default,
        "heading": default,
        "body": default,
        "small": default,
        "node": default,
        "metric": default,
        "mono": default,
    }


if __name__ == "__main__":
    raise SystemExit(main())
