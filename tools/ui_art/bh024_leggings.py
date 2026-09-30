"""bh-024: the Leggings slot's 2D art — the three fallback item icons (icons/items/leggings_{plate,cloth,leather}.svg,
used when a leggings base's own 3D icon is missing) and the empty-slot glyph (slots/glyph_leggings.png).

  python tools/ui_art/bh024_leggings.py            writes both
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

from bh_svg import Doc, STEEL, GOLD, LEATHER, LINEN, INDIGO, OUTLINE, f, poly, smooth, lt, dk  # noqa: E402
from bh_shapes import T  # noqa: E402

ITEMS = {}


def item(shadow=(64, 118, 40, 6)):
    def deco(fn):
        def build():
            d = Doc(name="it_" + fn.__name__)
            cx, cy, rx, ry = shadow
            with d.g(f"translate({f(cx)} {f(cy)}) scale(1 {f(ry / rx)})"):
                d.circle(0, 0, rx, fill=d.rad([(0, "#000000", 0.55), (0.6, "#000000", 0.25), (1, "#000000", 0)], 0, 0, rx))
            fn(d)
            return d
        ITEMS[fn.__name__] = build
        return fn
    return deco


# local frame: waist at y = -50, ankles at y = +50, the legs at x = -/+ 13
def _trousers(d: Doc, pal, flare=0.0):
    L = [(-26, -46), (26, -46), (28, -30), (26, -6), (23, 22), (22 + flare, 50), (6 - flare, 50), (4, 22), (2, -8), (0, -14),
         (-2, -8), (-4, 22), (-6 + flare, 50), (-22 - flare, 50), (-23, 22), (-26, -6), (-28, -30)]
    dd = smooth(L, tension=0.18)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, pal["light"]), (0.45, pal["base"]), (1, pal["dark"])], -26, -46, 24, 50))
    # the inner seams and the fold of the crotch, a highlight down each shin
    d.path("M0,-14 Q0,-30 0,-38", stroke=pal["dark"], sw=1.2, op=0.8)
    for sx in (-1, 1):
        d.path(f"M{f(sx * 16)},-26 Q{f(sx * 15)},10 {f(sx * 14)},46", stroke=lt(pal["base"], 0.35), sw=2.2, op=0.45)


def _belt(d: Doc, strap, buckle):
    d.shape(poly([(-27, -52), (27, -52), (27, -42), (-27, -42)]), fill=d.lin([(0, strap["light"]), (1, strap["dark"])], 0, -52, 0, -42), ow=2)
    d.shape(poly([(-6, -54), (6, -54), (6, -40), (-6, -40)]), fill=d.lin([(0, buckle["light"]), (1, buckle["dark"])], 0, -54, 0, -40), ow=1.6)


@item()
def leggings_plate(d):
    with d.g(T(64, 60, 0, 0.98)):
        _trousers(d, dict(dark="#20160e", base="#4a3a2c", light="#7a6a58"))
        for sx in (-1, 1):
            # three thigh lames and a knee cop
            for k, (y0, y1) in enumerate(((-38, -22), (-24, -8), (-10, 6))):
                pts = [(sx * 3, y0), (sx * 27, y0 - 1), (sx * 26, y1), (sx * 5, y1 + 1)]
                d.shape(poly(pts), fill=d.lin([(0, STEEL["light"]), (0.5, STEEL["base"]), (1, STEEL["dark"])], sx * 3, y0, sx * 26, y1), ow=2)
                d.path(f"M{f(sx * 5)},{f(y1)} L{f(sx * 25)},{f(y1 - 1)}", stroke=GOLD["base"], sw=1.8)
            d.shape(smooth([(sx * 7, 10), (sx * 22, 10), (sx * 23, 20), (sx * 14, 26), (sx * 6, 20)], tension=0.3),
                    fill=d.rad([(0, STEEL["light"]), (0.6, STEEL["base"]), (1, STEEL["dark"])], sx * 12, 14, 12), ow=2)
            d.circle(sx * 14, 17, 1.8, fill=GOLD["light"], stroke=OUTLINE, stroke_width=0.6)
        _belt(d, LEATHER, GOLD)


@item()
def leggings_cloth(d):
    robe = dict(dark=dk(INDIGO["base"], 0.2), base=INDIGO["base"], light=INDIGO["light"])
    with d.g(T(64, 60, 0, 0.98)):
        _trousers(d, robe, flare=2.0)
        for sx in (-1, 1):
            d.shape(poly([(sx * 5, 44), (sx * 25, 44), (sx * 25, 50), (sx * 5, 50)]), fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], 0, 44, 0, 50), ow=1.6)
            for k in range(3):
                y = -24 + k * 16
                d.circle(sx * 17, y, 1.6, fill="#c8e4ff", stroke=OUTLINE, stroke_width=0.5)
        # a hanging panel in front
        d.shape(poly([(-9, -42), (9, -42), (11, 8), (0, 16), (-11, 8)]), fill=d.lin([(0, "#d05060"), (1, "#3a0a10")], 0, -42, 0, 16), ow=2)
        d.path("M-10,6 L0,14 L10,6", stroke=GOLD["base"], sw=1.6)
        _belt(d, dict(dark="#0e0c2e", base="#2c2a7a", light="#6a68c8"), GOLD)


@item()
def leggings_leather(d):
    with d.g(T(64, 60, 0, 0.98)):
        _trousers(d, LEATHER)
        for sx in (-1, 1):
            # lacing down the outer seam and a strapped thigh guard
            for k in range(8):
                y = -30 + k * 9
                d.path(f"M{f(sx * 24)},{f(y)} L{f(sx * 20)},{f(y + 5)}", stroke=LINEN["light"], sw=1.2)
            d.shape(poly([(sx * 6, -36), (sx * 25, -36), (sx * 24, -8), (sx * 7, -6)]),
                    fill=d.lin([(0, LINEN["light"]), (1, LINEN["dark"])], sx * 6, -36, sx * 24, -6), ow=2)
            for y in (-30, -14):
                d.path(f"M{f(sx * 5)},{f(y)} L{f(sx * 26)},{f(y)}", stroke="#1a100a", sw=3)
        _belt(d, dict(dark="#120a06", base="#3a2416", light="#6a4a30"), GOLD)


def write_icons():
    out = os.path.join(ROOT, "game", "assets", "ui", "icons", "items")
    for name, fn in ITEMS.items():
        d = fn()
        with open(os.path.join(out, name + ".svg"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(d.svg())
        print("[bh024] icons/items/%s.svg" % name)


def write_glyph():
    """The empty Leggings slot glyph (raster_slots.GLYPHS["leggings"]), through the raster pipeline."""
    import build_raster as BR
    BR._render("slots/glyph_leggings")
    print("[bh024] slots/glyph_leggings.png")


if __name__ == "__main__":
    write_icons()
    write_glyph()
