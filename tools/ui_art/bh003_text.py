"""Text as SVG path outlines (ThorVG-safe: no <text> element), via fontTools glyph outlines of a system TTF.

Requires `pip install fonttools`. Fonts are only read at build time; the emitted SVGs contain plain path data.
"""
from __future__ import annotations

import os
from functools import lru_cache

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONT_DIRS = ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation", "/usr/share/fonts/truetype/freefont")
SERIF_BOLD = "DejaVuSerif-Bold.ttf"       # chunky slab-ish serif: survives 28 px
BOOK_SERIF_BOLD = "LiberationSerif-Bold.ttf"  # classic roman caps for mottos


def _find(name):
    for d in FONT_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


@lru_cache(maxsize=8)
def _font(name):
    return TTFont(_find(name))


def text_path(text, size, x, y, font=SERIF_BOLD, anchor="middle", tracking=0.0, sx=1.0):
    """Outline `text` with cap-baseline at y. `size` = em size in px; anchor start/middle/end on x.
    tracking: extra px between glyphs; sx: horizontal squash (1 = normal). Returns (path_d, width_px)."""
    ft = _font(font)
    gs = ft.getGlyphSet()
    cmap = ft.getBestCmap()
    upm = ft["head"].unitsPerEm
    hmtx = ft["hmtx"]
    s = size / upm
    names = [cmap.get(ord(ch), ".notdef") for ch in text]
    adv = [hmtx[n][0] * s * sx for n in names]
    width = sum(adv) + tracking * max(0, len(text) - 1)
    x0 = x - (width / 2 if anchor == "middle" else width if anchor == "end" else 0)
    pen = SVGPathPen(gs, ntos=lambda v: ("%.2f" % v).rstrip("0").rstrip("."))
    cur = x0
    for n, a in zip(names, adv):
        tp = TransformPen(pen, (s * sx, 0, 0, -s, cur, y))
        gs[n].draw(tp)
        cur += a + tracking
    return pen.getCommands(), width


def cap_height(size, font=SERIF_BOLD):
    ft = _font(font)
    os2 = ft["OS/2"]
    ch = getattr(os2, "sCapHeight", 0) or int(ft["head"].unitsPerEm * 0.72)
    return ch * size / ft["head"].unitsPerEm


def text_bbox(text, size, font=SERIF_BOLD, sx=1.0, tracking=0.0):
    _, w = text_path(text, size, 0, 0, font=font, sx=sx, tracking=tracking)
    return w, cap_height(size, font)
