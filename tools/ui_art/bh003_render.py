"""bh-003 evidence rasteriser: renders SVGs with resvg (pip `resvg-py`, Rust resvg) instead of Godot/ThorVG, because
Godot may not be run in this pipeline. resvg is a strict SVG renderer; the SVGs stay in the ThorVG-safe subset of
bh_svg.py (paths, gradients, groups, basic shapes - no text/filters/masks/clips) so the two renderers agree closely.

Also composes contact sheets with PIL.
"""
from __future__ import annotations

import io
import os
import re

from PIL import Image, ImageDraw, ImageFont

try:
    import resvg_py
except ImportError:  # pragma: no cover
    resvg_py = None

BG = (22, 18, 28)
CELL_BG = (34, 28, 42)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except Exception:
        return ImageFont.load_default()


def svg_size(svg: str):
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg[:600])
    return float(m.group(1)), float(m.group(2))


def render_svg(svg: str, width: int) -> Image.Image:
    """Render SVG markup to an RGBA image `width` px wide (height follows the viewBox aspect)."""
    if resvg_py is None:
        raise RuntimeError("resvg-py not installed: pip install resvg-py")
    w, h = svg_size(svg)
    png = resvg_py.svg_to_bytes(svg_string=svg, width=int(width), height=int(round(width * h / w)))
    return Image.open(io.BytesIO(bytes(png))).convert("RGBA")


def render_file(path: str, width: int) -> Image.Image:
    with open(path, encoding="utf-8") as fh:
        return render_svg(fh.read(), width)


def sheet(entries, title, out_path, cols=None, bg=BG, cell_bg=CELL_BG, label=True, pad=None):
    """entries: list of (name, PIL image). All cells sized to the largest image."""
    cw = max(im.width for _, im in entries)
    ch = max(im.height for _, im in entries)
    pad = pad if pad is not None else (10 if cw <= 64 else 14)
    lab_h = 16 if label else 0
    cellw = max(cw, 110 if cw <= 64 else cw) + pad
    n = len(entries)
    cols = cols or max(1, min(n, 1800 // cellw))
    rows = (n + cols - 1) // cols
    head = 34
    W = cols * cellw + pad
    H = head + rows * (ch + lab_h + pad) + pad
    img = Image.new("RGB", (W, H), bg)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 8), title, fill=(230, 214, 180), font=font(15))
    fs = font(11)
    for i, (name, im) in enumerate(entries):
        c, r = i % cols, i // cols
        x0 = pad + c * cellw
        y0 = head + r * (ch + lab_h + pad)
        dr.rectangle([x0 - 2, y0 - 2, x0 + cellw - pad + 1, y0 + ch + lab_h + 1], fill=cell_bg)
        img.paste(im, (x0 + (cellw - pad - im.width) // 2, y0 + (ch - im.height) // 2), im)
        if label:
            tw = dr.textlength(name, font=fs)
            dr.text((x0 + (cellw - pad - tw) / 2, y0 + ch + 2), name, fill=(200, 196, 210), font=fs)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    return out_path
