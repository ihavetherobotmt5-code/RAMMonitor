"""Generate a multi-resolution .ico file for RAM Monitor.

Creates a simple RAM-module glyph in the Windows 11 accent blue (#60CDFF)
at 4 sizes: 16x16, 32x32, 48x48, 256x256.

The glyph is a stylized RAM stick:
- Rounded rectangle outline (the PCB)
- 2 horizontal lines (the ICs)
- 1 vertical line at the bottom (the connector notch)

Run:
    python scripts/generate_icon.py
"""
from __future__ import annotations

import os
from pathlib import Path
from PIL import Image, ImageDraw

OUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "rammonitor.ico"

BG_TRANSPARENT = (0, 0, 0, 0)
ACCENT = (96, 205, 255, 255)
ACCENT_DIM = (96, 205, 255, 180)


def draw_glyph(size: int) -> Image.Image:
    """Draw the RAM-module glyph at the given size."""
    img = Image.new("RGBA", (size, size), BG_TRANSPARENT)
    draw = ImageDraw.Draw(img)
    m = max(2, size // 8)
    sw = max(1, size // 16)
    pcb_bbox = (m, m, size - m, size - m)
    radius = max(2, size // 8)
    draw.rounded_rectangle(pcb_bbox, radius=radius, outline=ACCENT, width=sw)
    line_top_y = size // 3
    line_bot_y = 2 * size // 3
    line_x_start = m + sw * 2
    line_x_end = size - m - sw * 2
    draw.line([(line_x_start, line_top_y), (line_x_end, line_top_y)], fill=ACCENT_DIM, width=sw)
    draw.line([(line_x_start, line_bot_y), (line_x_end, line_bot_y)], fill=ACCENT_DIM, width=sw)
    notch_w = max(2, size // 8)
    notch_h = max(2, size // 6)
    notch_x = (size - notch_w) // 2
    notch_y = size - m - notch_h
    draw.rectangle([notch_x, notch_y, notch_x + notch_w, size - m], fill=ACCENT)
    return img


def main() -> int:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    sizes = [16, 32, 48, 256]
    images = [draw_glyph(s) for s in sizes]
    base = images[-1]
    base.save(str(OUT_PATH), format="ICO", sizes=[(s, s) for s in sizes], append_images=images[:-1])
    size_bytes = OUT_PATH.stat().st_size
    print(f"Generated: {OUT_PATH}")
    print(f"  Sizes: {sizes}")
    print(f"  File size: {size_bytes} bytes")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
