"""bh-018 portraits: the three Socket Specialists (game/assets/ui/portraits/<id>.svg, viewBox 0 0 256 256).

Same painted-bust style and helpers as bh003_portraits.py. Each one is lit by the crystals they work with.
    python tools/ui_art/bh018_portraits.py            # writes the SVGs and a PNG preview sheet
"""
from __future__ import annotations

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from bh_svg import Doc, OUTLINE, GOLD, BRONZE, STEEL, f, poly, smooth, lt, dk, rrect_path  # noqa: E402
from bh_shapes import T  # noqa: E402
from portraits import (S, SKIN, SKIN_TAN, SKIN_OLD, SKIN_PALE, background, vignette, frame, neck, head, ears, eyes, brows,  # noqa: E402
                       nose, mouth, shoulders)
from bh003_portraits import wrinkles, stubble, lamp_glow, hair_strokes  # noqa: E402

PORTRAITS = {}


def portrait(fn):
    def build():
        d = Doc(S, S, name="pt18_" + fn.__name__)
        fn(d)
        return d
    PORTRAITS[fn.__name__] = build
    return fn


def crystal(d, x, y, s, core, edge, ang=0.0, glow=True):
    """A small faceted crystal (hexagonal point) with an inner glow, drawn at (x, y)."""
    if glow:
        d.circle(x, y, 26 * s, fill=d.rad([(0, core, 0.55), (1, core, 0)], x, y, 26 * s))
    with d.g(T(x, y, ang)):
        body = poly([(0, -22 * s), (8 * s, -10 * s), (8 * s, 12 * s), (0, 20 * s), (-8 * s, 12 * s), (-8 * s, -10 * s)])
        d.path(body, stroke=OUTLINE, sw=3)
        d.path(body, fill=d.lin([(0, lt(core, 0.6)), (0.5, core), (1, dk(edge, 0.3))], -8 * s, -22 * s, 8 * s, 20 * s))
        d.path(poly([(0, -22 * s), (8 * s, -10 * s), (0, -4 * s), (-8 * s, -10 * s)]), fill=lt(core, 0.75), op=0.8)
        d.path(f"M0,{f(-4 * s)} L0,{f(20 * s)}", stroke=lt(core, 0.8), sw=1.2, op=0.7)
        d.path(poly([(-8 * s, -10 * s), (0, -4 * s), (0, 20 * s), (-8 * s, 12 * s)]), fill="#ffffff", op=0.12)


# ------------------------------------------------------------------------------------------ Malasugue

@portrait
def lapidary(d):
    """Ysolde Marr: lapidary of Malasugue — hair pinned up with a stylus, jeweller's loupe over the right eye, leather
    apron, a glowing ember crystal held up in fine tongs."""
    background(d, "#1a2a3a", haze="#5ac0ff", haze2="#ff8a3a", motes="#bfe8ff", seed=181)
    vignette(d)
    cx, cy = 118, 118
    work = dict(dark="#20160e", base="#4e3620", light="#8a6440")
    shoulders(d, work, top=186, spread=1.0)
    # leather apron bib with a pocket of tools
    bib = smooth([(96, 196), (150, 196), (158, 256), (88, 256)], tension=0.15)
    d.path(bib, stroke=OUTLINE, sw=4)
    d.path(bib, fill=d.lin([(0, "#8a5a32"), (0.6, "#5a3a1e"), (1, "#2a1a0c")], 96, 196, 150, 256))
    d.path(rrect_path(104, 222, 30, 22, 4), fill="#4a2e16", stroke=OUTLINE, stroke_width=2)
    for k, col in enumerate(("#c8c8d0", "#c89a40", "#c8c8d0")):
        d.path(f"M{110 + k * 8},224 L{112 + k * 8},206", stroke=OUTLINE, sw=4)
        d.path(f"M{110 + k * 8},224 L{112 + k * 8},206", stroke=col, sw=2)
    neck(d, cx, cy + 42, 26, 26, SKIN_PALE)
    # hair: auburn, swept up into a knot pierced by a brass stylus
    knot = smooth([(cx - 22, cy - 50), (cx - 12, cy - 74), (cx + 10, cy - 80), (cx + 30, cy - 70), (cx + 30, cy - 50), (cx + 4, cy - 44)], tension=0.5)
    d.path(knot, stroke=OUTLINE, sw=4)
    d.path(knot, fill=d.rad([(0, "#b0542a"), (1, "#6a2a12")], cx + 2, cy - 70, 32))
    for k in range(4):
        d.path(smooth([(cx - 14 + k * 8, cy - 50), (cx - 8 + k * 9, cy - 70), (cx + 4 + k * 6, cy - 76)], closed=False), stroke="#d06a34", sw=1.4, op=0.6)
    d.path(f"M{cx - 20},{cy - 82} L{cx + 36},{cy - 56}", stroke=OUTLINE, sw=5)
    d.path(f"M{cx - 20},{cy - 82} L{cx + 36},{cy - 56}", stroke="#d0a040", sw=2.6)
    d.circle(cx - 20, cy - 82, 3.2, fill="#ff9a40", stroke=OUTLINE, stroke_width=1.4)
    head(d, cx, cy, SKIN_PALE, w=0.88, jaw=0.86, chin=0.88, top=1.0)
    for sx in (-1, 1):
        hp = smooth([(cx, cy - 58), (cx + sx * 30, cy - 52), (cx + sx * 42, cy - 26), (cx + sx * 38, cy - 4), (cx + sx * 30, cy - 26), (cx + sx * 14, cy - 42)], tension=0.5)
        d.path(hp, fill="#8a3c1c", stroke=OUTLINE, stroke_width=2)
    hair_strokes(d, [[(cx - 30, cy - 44), (cx - 10, cy - 54)], [(cx + 8, cy - 54), (cx + 28, cy - 46)]], "#c05a2a", sw=1.6, op=0.7)
    d.path(smooth([(cx - 38, cy - 20), (cx - 44, cy + 6), (cx - 40, cy + 24)], closed=False), stroke="#8a3c1c", sw=3)   # loose strand
    ears(d, cx, cy + 2, SKIN_PALE, w=0.88)
    brows(d, cx, cy - 16, "#6a2a14", thick=3.0, angle=-1.5, w=12)
    eyes(d, cx, cy - 3, iris="#3a8a7a", spacing=16, w=10, h=4.2)
    nose(d, cx, cy - 2, SKIN_PALE, L=19, w=7)
    wrinkles(d, cx, cy, SKIN_PALE, fore=1, cheek=0.3, op=0.3)
    mouth(d, cx, cy + 27, SKIN_PALE, w=11, smile=0.35, lip="#b0584a")
    # jeweller's loupe: a black barrel over the right eye on a strap
    lx, ly = cx + 16, cy - 3
    d.path(f"M{lx + 10},{ly - 6} Q{cx + 38},{cy - 30} {cx + 40},{cy - 40}", stroke=OUTLINE, sw=4)
    d.path(f"M{lx + 10},{ly - 6} Q{cx + 38},{cy - 30} {cx + 40},{cy - 40}", stroke="#3a2a1a", sw=2)
    d.ellipse(lx, ly, 12, 11, fill="#1a1a1e", stroke=OUTLINE, stroke_width=3)
    d.ellipse(lx + 3, ly + 1, 9, 8, fill="#26262c")
    d.ellipse(lx + 5, ly + 1, 6.5, 6, fill=d.rad([(0, "#ffd9a0"), (0.5, "#c86a2a"), (1, "#2a1a10")], lx + 4, ly, 7))
    d.circle(lx + 3, ly - 2, 1.6, fill="#ffffff")
    # fine tongs holding a glowing ember crystal up by the face
    tx, ty = 196, 118
    for k in (-1, 1):
        d.path(f"M{tx - 34},{ty + 96} L{tx + k * 4},{ty + 18}", stroke=OUTLINE, sw=5)
        d.path(f"M{tx - 34},{ty + 96} L{tx + k * 4},{ty + 18}", stroke="#b8bcc4", sw=2.4)
    crystal(d, tx, ty, 1.15, "#ff8a2a", "#a0200a", ang=12)
    # crystal light on the cheek and the loupe rim
    d.path(smooth([(cx + 34, cy - 18), (cx + 38, cy + 6), (cx + 30, cy + 30)], closed=False), stroke="#ffb070", sw=2.6, op=0.55)
    for k in range(3):
        a = random.Random(k + 5).uniform(0, math.tau)
        d.circle(tx + math.cos(a) * 30, ty + math.sin(a) * 30, 1.8, fill="#ffe0a0", opacity=0.8)
    frame(d, BRONZE, gem_col="#ff8a3a")


# ------------------------------------------------------------------------------------------ Olivar

@portrait
def gemcutter(d):
    """Anselm Cray: old gem-cutter of Olivar — bald crown, long white beard, spectacles with a flip-down second lens,
    a velvet cap, lit from below by a violet crystal on the wheel."""
    background(d, "#24163a", haze="#a070ff", haze2="#4ac0c0", motes="#e0c8ff", seed=187)
    vignette(d)
    cx, cy = 128, 112
    robe = dict(dark="#14102a", base="#3a2a5a", light="#6a5a9a")
    shoulders(d, robe, top=188, spread=1.04)
    # fur-trimmed collar
    rng = random.Random(9)
    for sx in (-1, 1):
        col = smooth([(128 + sx * 20, 190), (128 + sx * 58, 184), (128 + sx * 80, 210), (128 + sx * 40, 214)], tension=0.4)
        d.path(col, stroke=OUTLINE, sw=3)
        d.path(col, fill=d.lin([(0, "#e8dcc4"), (0.5, "#a89070"), (1, "#5a4a34")], 128 + sx * 20, 186, 128 + sx * 70, 214))
        for i in range(14):   # fur tufts
            x = 128 + sx * rng.uniform(26, 74)
            y = rng.uniform(190, 208)
            d.path(f"M{f(x)},{f(y)} l{f(sx * rng.uniform(2, 5))},{f(rng.uniform(3, 7))}", stroke="#f4ecd8" if i % 3 else "#4a3a28", sw=1.3, op=0.8)
    neck(d, cx, cy + 42, 28, 24, SKIN_OLD)
    head(d, cx, cy, SKIN_OLD, w=0.98, jaw=0.9, chin=0.92, top=1.04)
    # velvet skullcap
    cap = smooth([(cx - 38, cy - 40), (cx - 26, cy - 66), (cx, cy - 72), (cx + 26, cy - 66), (cx + 38, cy - 40), (cx, cy - 50)], tension=0.45)
    d.path(cap, stroke=OUTLINE, sw=4)
    d.path(cap, fill=d.lin([(0, "#8a4ac0"), (1, "#2a1050")], cx - 38, cy - 72, cx + 38, cy - 40))
    # white hair at the sides
    for sx in (-1, 1):
        d.path(smooth([(cx + sx * 36, cy - 36), (cx + sx * 46, cy - 16), (cx + sx * 44, cy + 6), (cx + sx * 36, cy - 8)], tension=0.5), fill="#e8e4dc", stroke=OUTLINE, stroke_width=1.8)
    ears(d, cx, cy + 2, SKIN_OLD, w=0.98)
    wrinkles(d, cx, cy, SKIN_OLD, fore=4, cheek=0.8, eye_bags=True, op=0.5)
    brows(d, cx, cy - 16, "#f0ece4", thick=4.6, angle=2.0, w=13)
    eyes(d, cx, cy - 3, iris="#5a6a8a", spacing=16, w=9, h=3.4, age=2, squint=0.2)
    nose(d, cx, cy - 2, SKIN_OLD, L=26, w=10)
    # long white beard and moustache
    beard = smooth([(cx - 34, cy + 10), (cx - 30, cy + 44), (cx - 14, cy + 78), (cx, cy + 92), (cx + 14, cy + 78), (cx + 30, cy + 44), (cx + 34, cy + 10),
                    (cx + 20, cy + 24), (cx, cy + 22), (cx - 20, cy + 24)], tension=0.45)
    d.path(beard, stroke=OUTLINE, sw=3.4)
    d.path(beard, fill=d.lin([(0, "#fbf8f0"), (0.6, "#d8d2c6"), (1, "#8a8478")], cx, cy + 10, cx, cy + 92))
    for k in range(9):
        x = cx - 24 + k * 6
        d.path(f"M{x},{cy + 30} Q{x + 2},{cy + 56} {cx + (x - cx) * 0.4},{cy + 84}", stroke="#b0aaa0", sw=1, op=0.6)
    d.path(smooth([(cx - 26, cy + 22), (cx - 10, cy + 16), (cx, cy + 20), (cx + 10, cy + 16), (cx + 26, cy + 22), (cx + 10, cy + 25), (cx, cy + 23), (cx - 10, cy + 25)], tension=0.5),
           fill="#f4f0e8", stroke=OUTLINE, stroke_width=1.6)
    # round spectacles, the left lens with a second magnifier flipped down in front of it
    for sx in (-1, 1):
        d.circle(cx + sx * 16, cy - 3, 11, stroke=OUTLINE, stroke_width=4)
        d.circle(cx + sx * 16, cy - 3, 11, stroke="#c8a040", stroke_width=2)
        d.circle(cx + sx * 16, cy - 3, 10, fill="#e8f0ff", opacity=0.12)
    d.path(f"M{cx - 5},{cy - 4} Q{cx},{cy - 8} {cx + 5},{cy - 4}", stroke="#c8a040", sw=2)
    d.path(f"M{cx - 27},{cy - 12} L{cx - 36},{cy - 22}", stroke="#c8a040", sw=2)
    d.circle(cx - 20, cy + 4, 8, stroke=OUTLINE, stroke_width=3.6)
    d.circle(cx - 20, cy + 4, 8, stroke="#c8a040", stroke_width=1.8)
    d.circle(cx - 20, cy + 4, 7, fill=d.rad([(0, "#c0a0ff", 0.4), (1, "#c0a0ff", 0.05)], cx - 22, cy + 2, 7))
    # violet crystal glowing below the frame edge, lighting the beard from beneath
    d.circle(70, 250, 80, fill=d.rad([(0, "#b070ff", 0.45), (1, "#b070ff", 0)], 70, 250, 80))
    crystal(d, 62, 214, 1.0, "#c080ff", "#401080", ang=-18)
    d.path(smooth([(cx - 34, cy + 40), (cx - 26, cy + 70), (cx - 10, cy + 88)], closed=False), stroke="#d0a8ff", sw=2.4, op=0.55)
    frame(d, dict(dark="#2a1a3a", base="#8a7aa0", light="#e8dcff"), gem_col="#b070ff")


# ------------------------------------------------------------------------------------------ Wyman Outpost

@portrait
def prospector(d):
    """Dagna Flint: crystal prospector of Wyman Outpost — weathered, a thick braid, a leather cap with a small lamp,
    soot on the cheek, a pick over the shoulder and a chunk of glowing green ore."""
    background(d, "#1a2a14", haze="#7ae05a", haze2="#e0a040", motes="#d0ffb0", seed=193)
    lamp_glow(d, 150, 40, 70, "#ffd080", 0.5)
    vignette(d)
    cx, cy = 126, 120
    coat = dict(dark="#1e1a10", base="#5a4a2a", light="#8a7a4a")
    # pick-axe haft over the left shoulder
    d.path("M28,256 L96,150", stroke=OUTLINE, sw=12)
    d.path("M28,256 L96,150", stroke="#7a5230", sw=7)
    with d.g(T(96, 150, -30)):
        head_p = poly([(-34, -6), (0, -12), (34, -4), (30, 4), (0, 0), (-30, 6)])
        d.path(head_p, stroke=OUTLINE, sw=4)
        d.path(head_p, fill=d.lin([(0, "#c8ccd4"), (1, "#4a4e56")], 0, -12, 0, 6))
    shoulders(d, coat, top=188, spread=1.08)
    d.path("M100,196 L128,214 L156,196", fill="#8a2a1a", stroke=OUTLINE, stroke_width=3)   # neckerchief
    neck(d, cx, cy + 42, 30, 26, SKIN_TAN)
    head(d, cx, cy, SKIN_TAN, w=1.0, jaw=1.02, chin=0.94, top=0.98)
    # thick braid over the right shoulder
    for k in range(6):
        y = cy + 20 + k * 14
        d.ellipse(cx + 46 + k * 2, y, 9, 8, fill="#4a2e18" if k % 2 else "#5a3a20", stroke=OUTLINE, stroke_width=1.8)
    d.path(f"M{cx + 50},{cy + 100} l-4,10 l10,0 Z", fill="#c03a2a", stroke=OUTLINE, stroke_width=1.4)
    # leather cap with a brass lamp
    capb = smooth([(cx - 46, cy - 28), (cx - 38, cy - 58), (cx, cy - 70), (cx + 38, cy - 58), (cx + 46, cy - 28), (cx + 20, cy - 40), (cx - 20, cy - 40)], tension=0.45)
    d.path(capb, stroke=OUTLINE, sw=4)
    d.path(capb, fill=d.lin([(0, "#8a5a32"), (1, "#3a2410")], cx, cy - 70, cx, cy - 28))
    d.path(f"M{cx - 50},{cy - 28} Q{cx},{cy - 38} {cx + 50},{cy - 28}", stroke="#2a1a0c", sw=5)
    d.path(rrect_path(cx - 10, cy - 66, 20, 16, 4), fill="#c8962e", stroke=OUTLINE, stroke_width=2.4)
    d.circle(cx, cy - 58, 5.5, fill="#fff4c0", stroke=OUTLINE, stroke_width=1.6)
    ears(d, cx, cy + 2, SKIN_TAN, w=1.0)
    brows(d, cx, cy - 16, "#3a2410", thick=4.2, angle=-2.0, w=13)
    eyes(d, cx, cy - 3, iris="#4a6a2a", spacing=17, w=10, h=3.8, squint=0.4, age=1)
    nose(d, cx, cy - 2, SKIN_TAN, L=21, w=9)
    wrinkles(d, cx, cy, SKIN_TAN, fore=2, cheek=0.7, op=0.45)
    mouth(d, cx, cy + 28, SKIN_TAN, w=13, smile=0.55, lip="#9a4a38")
    # soot smudges
    for (sx, sy, r) in ((cx - 24, cy + 12, 9), (cx + 20, cy - 26, 7)):
        d.circle(sx, sy, r, fill=d.rad([(0, "#1a1410", 0.45), (1, "#1a1410", 0)], sx, sy, r))
    # a chunk of green ore held up in a gloved hand
    ox, oy = 194, 196
    d.path(rrect_path(ox - 22, oy + 8, 44, 40, 12), fill="#5a3a1e", stroke=OUTLINE, stroke_width=3)
    rock = poly([(ox - 26, oy + 12), (ox - 20, oy - 8), (ox + 2, oy - 14), (ox + 24, oy - 4), (ox + 26, oy + 14), (ox, oy + 20)])
    d.path(rock, fill="#3a3a3e", stroke=OUTLINE, stroke_width=3)
    crystal(d, ox - 8, oy - 12, 0.7, "#7aff5a", "#1a6a10", ang=-20)
    crystal(d, ox + 10, oy - 8, 0.55, "#7aff5a", "#1a6a10", ang=24, glow=False)
    d.path(smooth([(cx + 36, cy - 10), (cx + 40, cy + 10), (cx + 32, cy + 34)], closed=False), stroke="#b0ff90", sw=2.4, op=0.45)
    frame(d, dict(dark="#2a2010", base="#8a7a4a", light="#e8dca0"), gem_col="#7aff5a")


def main():
    out_dir = os.path.abspath(os.path.join(HERE, "..", "..", "game", "assets", "ui", "portraits"))
    paths = []
    for name, fn in PORTRAITS.items():
        p = os.path.join(out_dir, name + ".svg")
        if os.path.exists(p) and "--force" not in sys.argv:
            existing = open(p, encoding="utf-8").read()
            if "pt18_" not in existing:
                raise SystemExit(f"refusing to overwrite existing portrait {name}")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(fn().svg())
        paths.append(p)
        print("WROTE", p)
    return paths


if __name__ == "__main__":
    main()
