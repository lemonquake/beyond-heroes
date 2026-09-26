"""bh-003 NPC portraits: 13 new people of Malasugue (LORE §6), game/assets/ui/portraits/<id>.svg, viewBox 0 0 256 256.

Same painted-bust style and anatomy helpers as portraits.py (imported, not modified). Each person gets their own head
proportions, hair, age marks and costume/props so none reads as a recolour of another.
"""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, OUTLINE, GOLD, STEEL, CRIMSON, BRONZE, LEATHER, WOOD, f, poly, smooth, mix, lt, dk, ribbon, taper,
                    qbez, star_pts, polar, rrect_path, circle_path)
from bh_shapes import T, smooth_pts
from portraits import (S, AE_C, AE_HI, SKIN, SKIN_TAN, SKIN_OLD, SKIN_PALE, background, vignette, frame, neck, head, ears,
                       eyes, brows, nose, mouth, shoulders)

NEW_PORTRAITS = {}


def portrait(fn):
    def build():
        d = Doc(S, S, name="pt3_" + fn.__name__)
        fn(d)
        return d
    NEW_PORTRAITS[fn.__name__] = build
    return fn


# ------------------------------------------------------------------------------------------ helpers

def hair_cap(d, cx, cy, col, hi=None, w=1.0, top=1.0, line=1.0, lift=0.0, sides=1.0):
    """Short hair mass over the skull; `line` scales the hairline height (lower = more forehead)."""
    outer = [(cx - 42 * w, cy - 2 * sides), (cx - 45 * w, cy - 30), (cx - 30 * w, cy - 56 * top - lift), (cx, cy - 61 * top - lift),
             (cx + 30 * w, cy - 56 * top - lift), (cx + 45 * w, cy - 30), (cx + 42 * w, cy - 2 * sides)]
    inner = [(cx + 38 * w, cy - 12), (cx + 30 * w, cy - 34 * line), (cx, cy - 40 * line), (cx - 30 * w, cy - 34 * line), (cx - 38 * w, cy - 12)]
    dd = smooth(outer + inner, tension=0.45)
    d.path(dd, stroke=OUTLINE, sw=4)
    d.path(dd, fill=d.lin([(0, hi or lt(col, 0.25)), (0.5, col), (1, dk(col, 0.4))], cx - 40, cy - 60, cx + 40, cy))
    return dd


def hair_strokes(d, pts_list, col, sw=1.4, op=0.7):
    for pts in pts_list:
        d.path(smooth(pts, closed=False), stroke=col, sw=sw, op=op)


def wrinkles(d, cx, cy, skin, fore=0, cheek=0.0, eye_bags=False, op=0.5):
    for k in range(fore):
        y = cy - 38 + k * 6
        d.path(f"M{f(cx - 20 + k * 2)},{f(y)} Q{f(cx)},{f(y - 3)} {f(cx + 20 - k * 2)},{f(y)}", stroke=skin["shade"], sw=1.2, op=op)
    if cheek:
        for sx in (-1, 1):
            d.path(f"M{f(cx + sx * 9)},{f(cy + 14)} Q{f(cx + sx * 18)},{f(cy + 26)} {f(cx + sx * 16)},{f(cy + 36 * cheek)}", stroke=skin["shade"], sw=1.6, op=op)
    if eye_bags:
        for sx in (-1, 1):
            d.path(f"M{f(cx + sx * 9)},{f(cy + 5)} Q{f(cx + sx * 17)},{f(cy + 9)} {f(cx + sx * 25)},{f(cy + 4)}", stroke=skin["shade"], sw=1.1, op=op)


def stubble(d, cx, cy, col, op=0.35, w=1.0, seed=3):
    dd = smooth([(cx - 38 * w, cy + 6), (cx - 30 * w, cy + 34), (cx - 14, cy + 48), (cx, cy + 51), (cx + 14, cy + 48), (cx + 30 * w, cy + 34),
                 (cx + 38 * w, cy + 6), (cx + 24, cy + 24), (cx, cy + 20), (cx - 24, cy + 24)], tension=0.45)
    d.path(dd, fill=col, op=op)
    rng = random.Random(seed)
    for _ in range(40):
        x = cx + rng.uniform(-30, 30) * w
        y = cy + rng.uniform(26, 46) - abs(x - cx) * 0.2
        d.circle(x, y, 0.6, fill=dk(col, 0.3), opacity=0.6)


def book(d, x, y, w, h, cover, ang=0, clasp=GOLD, emblem=None, pages="#efe4c8"):
    with d.g(T(x, y, ang)):
        pg = poly([(-w / 2 + 3, -h / 2 + 4), (w / 2 + 4, -h / 2 + 4), (w / 2 + 4, h / 2 + 3), (-w / 2 + 3, h / 2 + 3)])
        d.path(pg, fill=pages, stroke=OUTLINE, stroke_width=2.4)
        for k in range(1, 4):
            d.path(f"M{f(w / 2 + 4 - k * 1.2)},{f(-h / 2 + 6)} L{f(w / 2 + 4 - k * 1.2)},{f(h / 2 + 1)}", stroke="#a89878", sw=0.7)
        cv = rrect_path(-w / 2, -h / 2, w, h, 3)
        d.path(cv, stroke=OUTLINE, sw=4.4)
        d.path(cv, fill=d.lin([(0, cover["light"]), (0.5, cover["base"]), (1, cover["dark"])], -w / 2, -h / 2, w / 2, h / 2))
        d.path(f"M{f(-w / 2 + 5)},{f(-h / 2)} L{f(-w / 2 + 5)},{f(h / 2)}", stroke=dk(cover["dark"], 0.3), sw=2)
        for yy in (-h / 2 + 6, h / 2 - 6):
            d.path(f"M{f(-w / 2 + 8)},{f(yy)} L{f(w / 2 - 3)},{f(yy)}", stroke=clasp["base"], sw=1.6)
        if emblem:
            emblem(d)


def lamp_glow(d, x, y, r, col="#ffb040", op=0.55):
    d.circle(x, y, r, fill=d.rad([(0, col, op), (0.4, col, op * 0.45), (1, col, 0)], x, y, r))


def pin_star(d, x, y, r, pal):
    d.circle(x, y, r * 1.9, fill=d.rad([(0, pal[2], 0.55), (1, pal[2], 0)], x, y, r * 1.9))
    st = star_pts(x, y, 8, r, r * 0.5)
    d.path(poly(st), stroke=OUTLINE, sw=3)
    d.path(poly(st), fill=d.lin([(0, "#ffffff"), (0.4, pal[1]), (1, pal[0])], x - r, y - r, x + r, y + r))
    d.path(poly(st), stroke="#e8eef4", sw=0.8)


def mini_marlin(d, x, y, s=1.0, col="#e8eef4"):
    """Tiny silver swordfish pin."""
    with d.g(T(x, y, -18, s)):
        body = "M-12,0 Q-4,-6 8,-2 L22,-2.4 L8,1 Q-4,5 -12,0 Z"
        tail = "M-11,0 L-17,-6 L-15,0 L-17,6 Z"
        fin = "M-4,-3 Q0,-10 4,-3 Z"
        for p in (tail, fin, body):
            d.path(p, stroke=OUTLINE, sw=2.6)
        for p in (tail, fin, body):
            d.path(p, fill=d.lin([(0, "#ffffff"), (1, "#8a9aac")], 0, -8, 0, 6))


def shell(d, x, y, s=1.0):
    dd = f"M{f(x)},{f(y - 6 * s)} Q{f(x + 6 * s)},{f(y - 4 * s)} {f(x + 5 * s)},{f(y + 3 * s)} Q{f(x)},{f(y + 8 * s)} {f(x - 5 * s)},{f(y + 3 * s)} Q{f(x - 6 * s)},{f(y - 4 * s)} {f(x)},{f(y - 6 * s)} Z"
    d.path(dd, stroke=OUTLINE, sw=2.8)
    d.path(dd, fill=d.lin([(0, "#fff8f0"), (1, "#e0b8a0")], x, y - 6 * s, x, y + 8 * s))
    for k in (-2.5, 0, 2.5):
        d.path(f"M{f(x)},{f(y - 5 * s)} L{f(x + k * s)},{f(y + 5 * s)}", stroke="#b08878", sw=0.7)


# ------------------------------------------------------------------------------------------ tavern

@portrait
def innkeeper(d):
    """Pilar Abucay: middle-aged innkeeper, headscarf, apron, warm smile, lamplight."""
    background(d, "#4a2a10", haze="#ffa040", haze2="#c85a1a", motes="#ffd080", seed=31)
    lamp_glow(d, 212, 60, 90, "#ffc060", 0.6)
    vignette(d)
    cx, cy = 128, 118
    dress = dict(dark="#3a1a10", base="#7a3a22", light="#b8684a")
    shoulders(d, dress, top=186, spread=1.02)
    # apron bib + straps
    bib = smooth([(100, 196), (156, 196), (164, 256), (92, 256)], tension=0.15)
    d.path(bib, stroke=OUTLINE, sw=4)
    d.path(bib, fill=d.lin([(0, "#fbf2e0"), (0.6, "#e0d0b0"), (1, "#a89070")], 100, 196, 156, 256))
    for sx in (-1, 1):
        d.path(f"M{128 + sx * 26},198 L{128 + sx * 46},182", stroke=OUTLINE, sw=6)
        d.path(f"M{128 + sx * 26},198 L{128 + sx * 46},182", stroke="#e8dcc0", sw=3.6)
    d.path("M108,214 Q128,220 148,214", stroke="#b09878", sw=1.2)
    d.circle(118, 236, 5, fill="#a07a50", opacity=0.35)       # a honest stain
    # dishcloth over the shoulder
    cl = smooth([(52, 196), (76, 186), (84, 214), (70, 244), (54, 236)], tension=0.4)
    d.path(cl, stroke=OUTLINE, sw=4)
    d.path(cl, fill="#e8e0c8")
    for y in (200, 212, 224):
        d.path(f"M60,{y} L80,{y - 4}", stroke="#c03a2a", sw=2, op=0.8)
    neck(d, cx, cy + 42, 28, 28, SKIN_TAN)
    # headscarf back mass (behind the head)
    back = smooth([(cx - 50, cy - 10), (cx - 54, cy - 46), (cx - 30, cy - 70), (cx, cy - 76), (cx + 30, cy - 70), (cx + 54, cy - 46),
                   (cx + 52, cy - 8), (cx + 60, cy + 26), (cx + 40, cy + 34), (cx + 42, cy)], tension=0.45)
    scarf = dict(dark="#6a0e14", base="#c0302a", light="#f07050")
    d.path(back, stroke=OUTLINE, sw=5)
    d.path(back, fill=d.lin([(0, scarf["light"]), (0.5, scarf["base"]), (1, scarf["dark"])], cx - 50, cy - 70, cx + 60, cy + 30))
    head(d, cx, cy, SKIN_TAN, w=0.93, jaw=0.96, chin=0.9)
    # dark hair peeking at the temples
    for sx in (-1, 1):
        d.path(smooth([(cx + sx * 36, cy - 30), (cx + sx * 40, cy - 12), (cx + sx * 36, cy + 4), (cx + sx * 31, cy - 16)], tension=0.5), fill="#2a1810", stroke=OUTLINE, stroke_width=1.4)
    # scarf front band wrapping the forehead + knot at the right
    band = smooth([(cx - 46, cy - 26), (cx - 34, cy - 58), (cx, cy - 68), (cx + 34, cy - 58), (cx + 46, cy - 26), (cx + 34, cy - 36), (cx, cy - 44), (cx - 34, cy - 36)], tension=0.45)
    d.path(band, stroke=OUTLINE, sw=4.4)
    d.path(band, fill=d.lin([(0, scarf["light"]), (0.5, scarf["base"]), (1, scarf["dark"])], cx - 46, cy - 68, cx + 46, cy - 26))
    rng = random.Random(4)
    for i in range(11):   # yellow dot pattern
        a = math.pi * (1.1 + 0.8 * i / 10)
        x, y = cx + 40 * math.cos(a), cy - 30 + 30 * math.sin(a)
        d.circle(x, y + 4, 2, fill="#ffd060", stroke=OUTLINE, stroke_width=0.6)
    for (kx, ky, a) in ((cx + 50, cy - 42, 30), (cx + 60, cy - 30, 80)):
        with d.g(T(kx, ky, a)):
            d.path("M0,-6 Q10,-10 14,0 Q10,10 0,6 Z", fill=scarf["base"], stroke=OUTLINE, stroke_width=2.4)
    ears(d, cx, cy + 2, SKIN_TAN, w=0.93, earring=True)
    brows(d, cx, cy - 16, "#2a1810", thick=3.4, angle=1.5, w=12)
    eyes(d, cx, cy - 3, iris="#5a3418", spacing=16, w=10, h=4.0, squint=0.35, age=1)
    nose(d, cx, cy - 2, SKIN_TAN, L=20, w=8)
    wrinkles(d, cx, cy, SKIN_TAN, cheek=0.85, op=0.45)
    # broad warm smile with teeth
    sm = f"M{cx - 15},{cy + 26} Q{cx},{cy + 40} {cx + 15},{cy + 26} Q{cx},{cy + 32} {cx - 15},{cy + 26} Z"
    d.path(sm, fill="#fff6ee", stroke=OUTLINE, stroke_width=2.2)
    d.path(f"M{cx - 11},{cy + 33} Q{cx},{cy + 41} {cx + 11},{cy + 33}", stroke="#a0503c", sw=2.2, op=0.7)
    for sx in (-1, 1):
        d.circle(cx + sx * 24, cy + 14, 10, fill=d.rad([(0, "#f06a4a", 0.3), (1, "#f06a4a", 0)], cx + sx * 24, cy + 14, 10))
    # lamplight rim on the right cheek
    d.path(smooth([(cx + 34, cy - 20), (cx + 38, cy + 4), (cx + 30, cy + 30)], closed=False), stroke="#ffd090", sw=2.4, op=0.55)
    frame(d, BRONZE, gem_col="#ffb040")


@portrait
def bard(d):
    """Ciro Balintad: young bard, feathered cap, lute neck."""
    background(d, "#143a3a", haze="#30a090", haze2="#e0a040", motes="#ffe8a0", seed=37)
    vignette(d)
    cx, cy = 124, 120
    doublet = dict(dark="#062a2a", base="#137068", light="#4ab8a8")
    shoulders(d, doublet, top=188, spread=1.0)
    # slashed sleeves with orange showing through
    for sx in (-1, 1):
        for k in range(3):
            x = 128 + sx * (70 + k * 12)
            d.path(f"M{x},{206 + k * 6} L{x + sx * 4},{230 + k * 6}", stroke=OUTLINE, sw=5)
            d.path(f"M{x},{206 + k * 6} L{x + sx * 4},{230 + k * 6}", stroke="#f08a2a", sw=3)
    # laced collar opening
    d.path("M112,190 L128,230 L144,190 Z", fill="#f0e2c8", stroke=OUTLINE, stroke_width=3)
    for y in (200, 210, 220):
        d.path(f"M{122 + (y - 200) * 0.2},{y} L{134 - (y - 200) * 0.2},{y + 4}", stroke="#6a3a1a", sw=1.4)
    # lute neck + pegbox rising behind the right shoulder
    with d.g(T(196, 250, 18)):
        nk = poly([(-6, 0), (6, 0), (5, -150), (-5, -150)])
        d.path(nk, stroke=OUTLINE, sw=4.4)
        d.path(nk, fill=d.lin([(0, "#c08a50"), (0.5, "#7a4a22"), (1, "#3a1e0a")], -6, 0, 6, 0))
        for y in range(-20, -150, -16):
            d.path(f"M-5,{y} L5,{y}", stroke="#f0e0b0", sw=1.2)          # frets
        for x in (-2, 2):
            d.path(f"M{x},0 L{x * 0.8},-150", stroke="#f8f4ea", sw=0.6, op=0.8)
        pb = poly([(-6, -150), (6, -150), (14, -178), (4, -182)])
        d.path(pb, stroke=OUTLINE, sw=4)
        d.path(pb, fill="#5a3418")
        for k in range(3):
            y = -156 - k * 8
            d.circle(-4 + k * 3, y, 2.6, fill="#f0d8a0", stroke=OUTLINE, stroke_width=1)
            d.circle(12 + k * 2.4, y + 4, 2.6, fill="#f0d8a0", stroke=OUTLINE, stroke_width=1)
    neck(d, cx, cy + 42, 26, 28, SKIN)
    # curly brown hair spilling out under the cap
    for (x, y, r) in ((cx - 40, cy - 16, 11), (cx - 44, cy + 2, 10), (cx - 38, cy + 16, 8), (cx + 40, cy - 16, 11), (cx + 44, cy + 2, 10), (cx + 40, cy + 16, 8)):
        d.circle(x, y, r + 2, fill=OUTLINE)
        d.circle(x, y, r, fill=d.rad([(0, "#8a5a30"), (1, "#3a200e")], x - 3, y - 3, r * 1.3))
    head(d, cx, cy, SKIN, w=0.9, jaw=0.9, chin=0.95)
    ears(d, cx, cy + 2, SKIN, w=0.9)
    for (x, y, r) in ((cx - 30, cy - 36, 9), (cx - 14, cy - 40, 9), (cx + 4, cy - 42, 9), (cx + 22, cy - 38, 9), (cx + 34, cy - 30, 8)):
        d.circle(x, y, r + 1.8, fill=OUTLINE)
        d.circle(x, y, r, fill=d.rad([(0, "#9a6a3a"), (1, "#3a200e")], x - 3, y - 3, r * 1.3))
    # feathered cap: floppy beret tilted to the left with a long feather
    cap = smooth([(cx - 58, cy - 34), (cx - 50, cy - 62), (cx - 10, cy - 80), (cx + 36, cy - 72), (cx + 50, cy - 50), (cx + 40, cy - 40), (cx, cy - 46), (cx - 36, cy - 38)], tension=0.5)
    d.path(cap, stroke=OUTLINE, sw=5)
    d.path(cap, fill=d.lin([(0, "#e05a3a"), (0.5, "#a0201a"), (1, "#4a0a08")], cx - 58, cy - 80, cx + 50, cy - 36))
    d.path(smooth([(cx - 50, cy - 40), (cx, cy - 48), (cx + 44, cy - 44)], closed=False), stroke="#f0c050", sw=3)
    feather = smooth_pts([(cx + 30, cy - 58), (cx + 60, cy - 90), (cx + 96, cy - 104)], 20)
    d.path(ribbon(feather, taper(20, 16, 0.3, 0.1, peak=0.45)), stroke=OUTLINE, sw=4)
    d.path(ribbon(feather, taper(20, 16, 0.3, 0.1, peak=0.45)), fill=d.lin([(0, "#ffffff"), (1, "#9ad0e0")], cx + 30, cy - 58, cx + 96, cy - 104))
    d.path(poly(feather, closed=False), stroke="#3a6a80", sw=1.2)
    for i in range(3, 18, 2):
        x, y = feather[i]
        d.path(f"M{f(x)},{f(y)} L{f(x + 3)},{f(y + 6)}", stroke="#6aa0b8", sw=0.8)
    brows(d, cx, cy - 18, "#4a2a14", thick=3.2, angle=2.5, w=12)
    eyes(d, cx, cy - 4, iris="#3a8a5a", spacing=16, w=10.5, h=4.4)
    nose(d, cx, cy - 3, SKIN, L=18, w=7)
    # lopsided grin
    d.path(f"M{cx - 12},{cy + 26} Q{cx + 2},{cy + 36} {cx + 15},{cy + 22}", stroke=OUTLINE, sw=2.6)
    d.path(f"M{cx - 6},{cy + 30} Q{cx + 3},{cy + 35} {cx + 11},{cy + 28}", stroke="#b0503c", sw=2, op=0.6)
    d.path(f"M{cx + 15},{cy + 22} L{cx + 17},{cy + 19}", stroke=SKIN["shade"], sw=1.4, op=0.7)
    frame(d, GOLD, gem_col="#40d0b0")


@portrait
def fisher(d):
    """Old Tasyo: very old fisherman, wide woven conical hat, deep wrinkles, sea-grey eyes."""
    background(d, "#18303e", haze="#4a8aa8", haze2="#c08a4a", seed=41)
    vignette(d)
    cx, cy = 128, 126
    shirt = dict(dark="#2a2a24", base="#6a6a58", light="#a8a890")
    shoulders(d, shirt, top=190, spread=0.9, neck_w=30)
    d.path("M112,192 L128,216 L144,192", stroke=OUTLINE, sw=3)
    for (x, y) in ((70, 222), (180, 230), (96, 244)):            # patches / wear
        d.path(rrect_path(x, y, 14, 12, 2), fill="#8a7a5a", stroke=OUTLINE, stroke_width=1.4)
    neck(d, cx, cy + 38, 24, 30, SKIN_OLD)
    for k in range(3):
        d.path(f"M{cx - 10},{cy + 50 + k * 6} Q{cx},{cy + 52 + k * 6} {cx + 10},{cy + 50 + k * 6}", stroke=SKIN_OLD["shade"], sw=1, op=0.6)
    head(d, cx, cy, SKIN_OLD, w=0.86, jaw=0.84, chin=0.8, top=0.96)
    ears(d, cx, cy + 4, SKIN_OLD, w=0.86)
    # hollow cheeks
    for sx in (-1, 1):
        d.ellipse(cx + sx * 24, cy + 20, 8, 12, fill=d.rad([(0, SKIN_OLD["shade"], 0.3), (1, SKIN_OLD["shade"], 0)], cx + sx * 24, cy + 20, 12))
    # white stubble + thin wispy hair at the temples
    stubble(d, cx, cy, "#e8e8e0", op=0.45, w=0.84, seed=5)
    for sx in (-1, 1):
        d.path(smooth([(cx + sx * 32, cy - 18), (cx + sx * 40, cy - 6), (cx + sx * 38, cy + 8)], closed=False), stroke="#f0f0ea", sw=4)
    wrinkles(d, cx, cy + 6, SKIN_OLD, fore=4, cheek=1.0, eye_bags=True, op=0.65)
    brows(d, cx, cy - 14, "#e0e0d8", thick=4.4, angle=3, w=12)
    eyes(d, cx, cy - 1, iris="#7a8a92", spacing=15, w=9, h=3.2, squint=0.45, age=3)
    nose(d, cx, cy - 2, SKIN_OLD, L=24, w=9)
    # toothless thin smile
    d.path(f"M{cx - 11},{cy + 30} Q{cx},{cy + 35} {cx + 11},{cy + 29}", stroke=OUTLINE, sw=2.2)
    d.path(f"M{cx - 13},{cy + 32} Q{cx - 16},{cy + 36} {cx - 14},{cy + 40}", stroke=SKIN_OLD["shade"], sw=1.2, op=0.6)
    # hat shadow over the brow
    d.path(smooth([(cx - 48, cy - 26), (cx, cy - 36), (cx + 48, cy - 26), (cx + 40, cy - 14), (cx, cy - 22), (cx - 40, cy - 14)], tension=0.4), fill="#1a0e06", op=0.4)
    # wide woven conical hat (salakot-like)
    hx, hy = cx, cy - 40
    hat = f"M{hx - 104},{hy + 18} Q{hx - 60},{hy - 20} {hx},{hy - 62} Q{hx + 60},{hy - 20} {hx + 104},{hy + 18} Q{hx},{hy + 34} {hx - 104},{hy + 18} Z"
    d.path(hat, stroke=OUTLINE, sw=5)
    d.path(hat, fill=d.lin([(0, "#f0d8a0"), (0.4, "#c8a060"), (1, "#6a4a20")], hx - 104, hy - 62, hx + 104, hy + 30))
    for k in range(1, 9):   # concentric weave rings
        t = k / 9
        y = hy - 62 + 80 * t
        half = 104 * t
        d.path(f"M{f(hx - half)},{f(y - 0 + 2 * t)} Q{f(hx)},{f(y + 14 * t)} {f(hx + half)},{f(y + 2 * t)}", stroke="#6a4a20", sw=1.1, op=0.7)
    for k in range(-6, 7):  # radial ribs
        d.path(f"M{hx},{hy - 60} L{f(hx + k * 16)},{f(hy + 18 + 10 * (1 - abs(k) / 6))}", stroke="#8a6630", sw=0.9, op=0.55)
    d.circle(hx, hy - 60, 4, fill="#6a4a20", stroke=OUTLINE, stroke_width=1.6)
    # chin cord
    for sx in (-1, 1):
        d.path(f"M{cx + sx * 40},{cy - 20} Q{cx + sx * 36},{cy + 30} {cx + sx * 8},{cy + 52}", stroke="#5a4020", sw=1.4, op=0.9)
    frame(d, dict(dark="#2a3440", base="#8a9aa8", light="#e8f0f8"), gem_col="#6ac0e0")


@portrait
def veteran(d):
    """Venna Kail: retired Class A heroine, brow scar, short grey hair, azure star pin."""
    background(d, "#1a2438", haze="#3a6ad0", haze2="#b08050", seed=43)
    vignette(d)
    cx, cy = 128, 116
    coat = dict(dark="#1e140c", base="#5a3e26", light="#9a7450")
    shoulders(d, coat, top=186, spread=1.0)
    # worn single pauldron (left) with azure enamel stripe
    pl = smooth([(26, 232), (40, 198), (80, 188), (96, 204), (80, 228), (44, 242)], tension=0.5)
    d.path(pl, stroke=OUTLINE, sw=5)
    d.path(pl, fill=d.lin([(0, "#c8d0d8"), (0.5, "#707a86"), (1, "#2a3038")], 26, 188, 96, 242))
    d.path(smooth([(40, 212), (62, 198), (86, 202)], closed=False), stroke="#2a6ad0", sw=3)
    for (x, y) in ((50, 222), (74, 212)):
        d.path(f"M{x},{y} l6,-3", stroke="#2a3038", sw=1.2)  # dents
    # high coat collar
    for sx in (-1, 1):
        col = poly([(128 + sx * 16, 178), (128 + sx * 44, 180), (128 + sx * 40, 204), (128 + sx * 10, 204)])
        d.path(col, stroke=OUTLINE, sw=4)
        d.path(col, fill=d.lin([(0, coat["light"]), (1, coat["dark"])], 128, 178, 128 + sx * 44, 204))
    pin_star(d, 164, 196, 9, ("#062a6a", "#2a7ae0", "#9ad0ff"))
    neck(d, cx, cy + 42, 28, 24, SKIN_PALE)
    head(d, cx, cy, SKIN_PALE, w=0.94, jaw=1.0, chin=0.92)
    ears(d, cx, cy + 2, SKIN_PALE, w=0.94)
    # cropped grey hair, swept back, undercut sides
    hair_cap(d, cx, cy, "#9a9ea4", hi="#e4e6ea", w=0.95, top=0.98, line=0.9, sides=4)
    hair_strokes(d, [[(cx - 30, cy - 38), (cx - 10, cy - 50), (cx + 20, cy - 52)], [(cx - 20, cy - 34), (cx + 6, cy - 44), (cx + 34, cy - 40)],
                     [(cx + 12, cy - 36), (cx + 32, cy - 44), (cx + 42, cy - 30)]], "#5a5e64")
    wrinkles(d, cx, cy, SKIN_PALE, fore=2, cheek=0.6, op=0.4)
    brows(d, cx, cy - 16, "#8a8e94", thick=4.2, angle=-1.5, w=13)
    eyes(d, cx, cy - 3, iris="#4a7aa0", spacing=17, w=10, h=3.8, squint=0.3, age=2)
    nose(d, cx, cy - 2, SKIN_PALE, L=21, w=8)
    # dry half-smile
    d.path(f"M{cx - 11},{cy + 29} Q{cx + 2},{cy + 31} {cx + 12},{cy + 26}", stroke=OUTLINE, sw=2.4)
    d.path(f"M{cx - 6},{cy + 32} Q{cx + 2},{cy + 35} {cx + 8},{cy + 31}", stroke="#b06a60", sw=2, op=0.5)
    # the scar: across the brow, through the left eyebrow onto the cheek
    sc = f"M{cx - 38},{cy - 30} L{cx - 6},{cy - 6}"
    d.path(sc, stroke="#6a2a24", sw=4.2, op=0.55)
    d.path(sc, stroke="#f0b0a0", sw=2)
    for t in (0.25, 0.5, 0.75):
        x, y = cx - 38 + 32 * t, cy - 30 + 24 * t
        d.path(f"M{f(x - 3)},{f(y + 3)} L{f(x + 3)},{f(y - 3)}", stroke="#8a3a30", sw=1, op=0.6)
    frame(d, dict(dark="#1a2a4a", base="#8aa8d8", light="#f0f6ff"), gem_col="#4a9aff")


# ------------------------------------------------------------------------------------------ Swordfin Company

@portrait
def swordfin_master(d):
    """Commander Rhea Talvanne: stern woman, blue coat, silver swordfish pin, spear shaft."""
    background(d, "#0e2240", haze="#2a6ab0", haze2="#6ab0e0", seed=47)
    vignette(d)
    cx, cy = 124, 116
    # spear shaft behind the right shoulder, head at top right
    with d.g(T(206, 256, 8)):
        sh = poly([(-4, 0), (4, 0), (4, -196), (-4, -196)])
        d.path(sh, stroke=OUTLINE, sw=4)
        d.path(sh, fill=d.lin([(0, "#b88452"), (0.5, "#6e4424"), (1, "#2a1608")], -4, 0, 4, 0))
        for y in (-150, -170):
            d.path(f"M-5,{y} L5,{y}", stroke="#dfe8f0", sw=3)
        hd = poly([(-8, -196), (8, -196), (4, -212), (0, -236), (-4, -212)])
        d.path(hd, stroke=OUTLINE, sw=4)
        d.path(hd, fill=d.lin([(0, "#ffffff"), (0.5, "#aab4be"), (1, "#3c444e")], -8, 0, 8, 0))
    coat = dict(dark="#061634", base="#16408a", light="#4a80d0")
    shoulders(d, coat, top=184, spread=1.02)
    # silver epaulettes + frogging
    for sx in (-1, 1):
        ep = smooth([(128 + sx * 52, 190), (128 + sx * 84, 184), (128 + sx * 100, 200), (128 + sx * 80, 210), (128 + sx * 52, 204)], tension=0.4)
        d.path(ep, stroke=OUTLINE, sw=4)
        d.path(ep, fill=d.lin([(0, "#ffffff"), (1, "#7a8898")], 128, 184, 128 + sx * 100, 210))
        for k in range(5):
            x = 128 + sx * (58 + k * 8)
            d.path(f"M{x},{206} L{x + sx * 1},{216}", stroke="#c8d4e0", sw=1.6)
    for y in (214, 228, 242):
        d.path(f"M112,{y} L144,{y}", stroke=OUTLINE, sw=5)
        d.path(f"M112,{y} L144,{y}", stroke="#dfe6ee", sw=2.4)
    # high standing collar
    col = poly([(96, 172), (160, 172), (164, 196), (92, 196)])
    d.path(col, stroke=OUTLINE, sw=4)
    d.path(col, fill=d.lin([(0, coat["light"]), (1, coat["dark"])], 96, 172, 96, 196))
    d.path("M94,178 L162,178", stroke="#dfe6ee", sw=2)
    d.circle(158, 212, 16, fill=d.rad([(0, "#dfe8f0", 0.4), (1, "#dfe8f0", 0)], 158, 212, 16))
    mini_marlin(d, 156, 214, 1.6)
    neck(d, cx, cy + 40, 26, 20, SKIN)
    # dark hair pulled into a tight high bun
    d.circle(cx + 4, cy - 62, 16, fill=OUTLINE)
    d.circle(cx + 4, cy - 62, 13.5, fill=d.rad([(0, "#4a3020"), (1, "#140a06")], cx, cy - 66, 16))
    d.path(f"M{cx - 6},{cy - 64} Q{cx + 4},{cy - 70} {cx + 14},{cy - 62}", stroke="#6a4a30", sw=1.2)
    head(d, cx, cy, SKIN, w=0.9, jaw=0.98, chin=0.95, top=1.0)
    ears(d, cx, cy + 2, SKIN, w=0.9)
    hair_cap(d, cx, cy, "#2a1810", hi="#5a3a24", w=0.92, top=0.98, line=1.05, sides=6)
    hair_strokes(d, [[(cx - 34, cy - 20), (cx - 22, cy - 46), (cx + 2, cy - 56)], [(cx + 34, cy - 20), (cx + 22, cy - 46), (cx + 4, cy - 56)]], "#5a3a24", sw=1.2)
    brows(d, cx, cy - 16, "#2a1810", thick=4.4, angle=-3, w=13)
    eyes(d, cx, cy - 3, iris="#2a5a9a", spacing=16, w=10, h=3.6, squint=0.35)
    nose(d, cx, cy - 2, SKIN, L=21, w=7)
    wrinkles(d, cx, cy, SKIN, fore=0, cheek=0.7, op=0.35)
    # set, unsmiling mouth
    d.path(f"M{cx - 11},{cy + 29} Q{cx},{cy + 28} {cx + 11},{cy + 29}", stroke=OUTLINE, sw=2.6)
    d.path(f"M{cx - 7},{cy + 32} Q{cx},{cy + 34} {cx + 7},{cy + 32}", stroke="#a04a48", sw=2, op=0.6)
    frame(d, dict(dark="#3a4250", base="#b4bfcc", light="#ffffff"), gem_col="#4a9aff")


@portrait
def swordfin_quartermaster(d):
    """Dax Mercado: burly bearded man, ledger, blue sash."""
    background(d, "#1a2a3a", haze="#3a6aa0", haze2="#c0904a", seed=53)
    vignette(d)
    cx, cy = 128, 114
    tunic = dict(dark="#2a1c10", base="#6a5038", light="#a8886a")
    shoulders(d, tunic, top=180, spread=1.14, neck_w=46)
    # blue sash across the chest
    sash = poly([(40, 196), (70, 184), (212, 256), (170, 256)])
    d.path(sash, stroke=OUTLINE, sw=4.4)
    d.path(sash, fill=d.lin([(0, "#4a80d0"), (0.5, "#16408a"), (1, "#061634")], 40, 190, 200, 256))
    d.path("M56,190 L196,256", stroke="#c8d4e0", sw=1.4, op=0.7)
    mini_marlin(d, 96, 208, 1.0)
    neck(d, cx, cy + 40, 44, 26, SKIN_TAN)
    head(d, cx, cy, SKIN_TAN, w=1.1, jaw=1.14, chin=1.15, top=0.94)
    ears(d, cx, cy + 2, SKIN_TAN, w=1.1)
    # close-cropped black hair with a widow's peak
    hair_cap(d, cx, cy, "#141010", hi="#3a3434", w=1.1, top=0.95, line=1.08, sides=6)
    brows(d, cx, cy - 16, "#141010", thick=5.4, angle=0.5, w=14)
    eyes(d, cx, cy - 3, iris="#4a2a14", spacing=18, w=9.5, h=3.8, squint=0.2)
    nose(d, cx, cy - 4, SKIN_TAN, L=20, w=10)
    # full rounded beard, grey streak at the chin
    beard = smooth([(cx - 44, cy - 2), (cx - 42, cy + 30), (cx - 26, cy + 58), (cx, cy + 66), (cx + 26, cy + 58), (cx + 42, cy + 30), (cx + 44, cy - 2),
                    (cx + 34, cy + 18), (cx + 16, cy + 22), (cx, cy + 19), (cx - 16, cy + 22), (cx - 34, cy + 18)], tension=0.45)
    d.path(beard, stroke=OUTLINE, sw=4.4)
    d.path(beard, fill=d.lin([(0, "#3a3030"), (0.6, "#1a1414"), (1, "#0a0808")], cx - 44, cy, cx + 44, cy + 66))
    d.path(smooth([(cx - 6, cy + 42), (cx, cy + 62), (cx + 6, cy + 42)], closed=False), stroke="#b0aaa8", sw=3, op=0.8)
    for i in range(10):
        x = cx - 34 + i * 7.5
        d.path(f"M{x},{cy + 26} Q{x + 2},{cy + 40} {x},{cy + 54 - abs(i - 4.5) * 3}", stroke="#5a5050", sw=1, op=0.6)
    # mouth inside the beard: a friendly open laugh
    d.path(f"M{cx - 10},{cy + 30} Q{cx},{cy + 40} {cx + 10},{cy + 30} Z", fill="#6a2018", stroke=OUTLINE, stroke_width=2)
    d.path(f"M{cx - 8},{cy + 31} L{cx + 8},{cy + 31}", stroke="#fff6ee", sw=2.2)
    # ledger held up at the bottom left, open, with quill
    with d.g(T(74, 232, -10)):
        lg = poly([(-40, -22), (0, -18), (40, -22), (40, 22), (0, 26), (-40, 22)])
        d.path(lg, stroke=OUTLINE, sw=5)
        d.path(poly([(-44, -18), (0, -14), (44, -18), (44, 26), (0, 30), (-44, 26)]), fill="#2a3a6a", stroke=OUTLINE, stroke_width=3)
        d.path(poly([(-40, -22), (0, -18), (0, 26), (-40, 22)]), fill=d.lin([(0, "#fbf4e0"), (1, "#d8c8a0")], -40, 0, 0, 0))
        d.path(poly([(0, -18), (40, -22), (40, 22), (0, 26)]), fill=d.lin([(0, "#e0d0a8"), (1, "#fbf4e0")], 0, 0, 40, 0))
        d.path("M0,-18 L0,26", stroke="#8a7a58", sw=1.4)
        for k in range(6):
            y = -12 + k * 6
            d.path(f"M-34,{y} L-6,{y + 0.6}", stroke="#4a4a5a", sw=1, op=0.7)
            d.path(f"M6,{y + 0.6} L{22 + (k % 3) * 4},{y}", stroke="#4a4a5a", sw=1, op=0.7)
            d.path(f"M28,{y} L34,{y}", stroke="#a02a2a", sw=1, op=0.7)
    frame(d, dict(dark="#3a4250", base="#b4bfcc", light="#ffffff"), gem_col="#4a9aff")


# ------------------------------------------------------------------------------------------ Lantern Covenant

@portrait
def lantern_master(d):
    """Archivist Oren Vale: elderly scholar, violet robes, spectacles, small lantern light."""
    background(d, "#24143e", haze="#7a4ac0", haze2="#e0a040", motes="#ffd070", seed=59)
    vignette(d)
    cx, cy = 124, 112
    robe = dict(dark="#140828", base="#3e2070", light="#7a58b8")
    shoulders(d, robe, top=182, spread=0.98)
    # gold-embroidered stole
    for sx in (-1, 1):
        st = poly([(128 + sx * 14, 184), (128 + sx * 32, 184), (128 + sx * 40, 256), (128 + sx * 18, 256)])
        d.path(st, stroke=OUTLINE, sw=3.4)
        d.path(st, fill=d.lin([(0, "#fff0b0"), (0.5, "#d8a838"), (1, "#6a4210")], 128 + sx * 14, 0, 128 + sx * 40, 0))
        for y in (200, 220, 240):
            d.circle(128 + sx * (24 + (y - 184) * 0.07), y, 3, fill="#6a3ab0", stroke=OUTLINE, stroke_width=1)
    neck(d, cx, cy + 42, 26, 28, SKIN_OLD)
    head(d, cx, cy, SKIN_OLD, w=0.92, jaw=0.88, chin=0.86, top=1.04)
    ears(d, cx, cy + 2, SKIN_OLD, w=0.92)
    # bald dome, white tufts over the ears, bushy brows
    d.path(smooth([(cx - 20, cy - 44), (cx - 4, cy - 52), (cx + 10, cy - 50)], closed=False), stroke="#ffffff", sw=3, op=0.4)
    for sx in (-1, 1):
        tuft = smooth([(cx + sx * 34, cy - 30), (cx + sx * 50, cy - 26), (cx + sx * 54, cy - 8), (cx + sx * 46, cy + 8), (cx + sx * 38, cy - 6)], tension=0.5)
        d.path(tuft, fill="#eeeeea", stroke=OUTLINE, stroke_width=2)
        d.path(smooth([(cx + sx * 40, cy - 24), (cx + sx * 50, cy - 12), (cx + sx * 46, cy + 2)], closed=False), stroke="#a8a8b0", sw=1)
    wrinkles(d, cx, cy, SKIN_OLD, fore=3, cheek=0.9, eye_bags=True, op=0.55)
    brows(d, cx, cy - 17, "#f4f4f0", thick=5.6, angle=3.5, w=14)
    eyes(d, cx, cy - 3, iris="#6a4a9a", spacing=16, w=9, h=3.4, age=2)
    # round gold spectacles
    for sx in (-1, 1):
        ex = cx + sx * 16
        d.circle(ex, cy - 2, 11, fill="#ffffff", opacity=0.12)
        d.circle(ex, cy - 2, 11, stroke=OUTLINE, stroke_width=4)
        d.circle(ex, cy - 2, 11, stroke="#e0b040", stroke_width=2)
        d.path(f"M{f(ex - 6)},{cy - 8} L{f(ex - 2)},{cy - 11}", stroke="#ffffff", sw=1.4, op=0.8)
        d.path(f"M{cx + sx * 27},{cy - 4} L{cx + sx * 38},{cy - 6}", stroke="#e0b040", sw=1.6)
    d.path(f"M{cx - 5},{cy - 3} Q{cx},{cy - 7} {cx + 5},{cy - 3}", stroke="#e0b040", sw=1.8)
    nose(d, cx, cy + 2, SKIN_OLD, L=21, w=8)
    # short neat white beard + mustache
    beard = smooth([(cx - 30, cy + 20), (cx - 22, cy + 46), (cx, cy + 62), (cx + 22, cy + 46), (cx + 30, cy + 20), (cx + 14, cy + 30), (cx, cy + 28), (cx - 14, cy + 30)], tension=0.45)
    d.path(beard, stroke=OUTLINE, sw=3.6)
    d.path(beard, fill=d.lin([(0, "#ffffff"), (1, "#a8a8b8")], cx, cy + 20, cx, cy + 62))
    must = smooth([(cx - 20, cy + 32), (cx - 10, cy + 24), (cx, cy + 27), (cx + 10, cy + 24), (cx + 20, cy + 32), (cx + 8, cy + 30), (cx, cy + 31), (cx - 8, cy + 30)], tension=0.5)
    d.path(must, fill="#f4f4f8", stroke=OUTLINE, stroke_width=1.6)
    d.path(f"M{cx - 6},{cy + 37} Q{cx},{cy + 39} {cx + 6},{cy + 37}", stroke="#8a4a4a", sw=1.8)
    # small hand lantern lower right, warm light on the robe
    lx, ly = 204, 214
    lamp_glow(d, lx, ly, 60, "#ffc050", 0.55)
    d.path(f"M{lx},{ly - 34} L{lx},{ly - 22}", stroke=OUTLINE, sw=3)
    d.circle(lx, ly - 36, 5, stroke=OUTLINE, stroke_width=4)
    d.circle(lx, ly - 36, 5, stroke="#e0b040", stroke_width=2)
    d.path(poly([(lx - 13, ly - 22), (lx + 13, ly - 22), (lx + 7, ly - 30), (lx - 7, ly - 30)]), fill="#d8a838", stroke=OUTLINE, stroke_width=2.4)
    body = poly([(lx - 12, ly - 22), (lx + 12, ly - 22), (lx + 10, ly + 12), (lx - 10, ly + 12)])
    d.path(body, stroke=OUTLINE, sw=4)
    d.path(body, fill=d.rad([(0, "#ffffff"), (0.4, "#ffd070"), (1, "#c0601a")], lx, ly - 6, 20))
    d.path(f"M{lx},{ly - 16} Q{lx + 5},{ly - 6} {lx},{ly + 2} Q{lx - 5},{ly - 6} {lx},{ly - 16} Z", fill="#ffffff")
    d.path(poly([(lx - 13, ly + 12), (lx + 13, ly + 12), (lx + 13, ly + 18), (lx - 13, ly + 18)]), fill="#d8a838", stroke=OUTLINE, stroke_width=2.4)
    for sx in (-1, 1):
        d.path(f"M{lx + sx * 11},{ly - 22} L{lx + sx * 9.5},{ly + 12}", stroke="#b08020", sw=2.4)
    frame(d, GOLD, gem_col="#b890ff")


@portrait
def lantern_scribe(d):
    """Lio Sanvar: young scribe, ink-stained, quill behind the ear, violet."""
    background(d, "#1e1a40", haze="#6a5ac8", haze2="#40a0c0", motes=AE_C, seed=61)
    vignette(d)
    cx, cy = 130, 120
    tunic = dict(dark="#1a0e30", base="#50328a", light="#8a6ac8")
    shoulders(d, tunic, top=188, spread=0.94)
    # plain white collar + gold edge
    col = smooth([(100, 184), (128, 206), (156, 184), (160, 196), (128, 216), (96, 196)], tension=0.4)
    d.path(col, stroke=OUTLINE, sw=3.6)
    d.path(col, fill="#f0ecf8")
    d.path(smooth([(96, 196), (128, 216), (160, 196)], closed=False), stroke="#d8a838", sw=2)
    # ink bottle strap / satchel
    d.path("M156,200 L206,256", stroke=OUTLINE, sw=8)
    d.path("M156,200 L206,256", stroke="#6a3e22", sw=5)
    for (x, y, r) in ((82, 224, 5), (90, 236, 3), (172, 238, 4)):
        d.circle(x, y, r, fill="#0a0a1a", opacity=0.55)
    neck(d, cx, cy + 42, 24, 28, SKIN_PALE)
    # quill tucked behind the right ear
    ql = smooth_pts([(cx + 36, cy + 12), (cx + 52, cy - 20), (cx + 76, cy - 66)], 20)
    d.path(ribbon(ql, taper(20, 11, 0.1, 0.2, peak=0.55)), stroke=OUTLINE, sw=3.6)
    d.path(ribbon(ql, taper(20, 11, 0.1, 0.2, peak=0.55)), fill=d.lin([(0, "#ffffff"), (1, "#c8b8e8")], cx + 36, cy + 12, cx + 76, cy - 66))
    d.path(poly(ql, closed=False), stroke="#6a5a8a", sw=1)
    d.path(f"M{cx + 36},{cy + 12} L{cx + 34},{cy + 18}", stroke="#0a0a1a", sw=2.4)
    head(d, cx, cy, SKIN_PALE, w=0.86, jaw=0.84, chin=0.86, top=1.0)
    ears(d, cx, cy + 2, SKIN_PALE, w=0.86)
    # messy light-brown hair, fringe falling over the brow
    hair_cap(d, cx, cy, "#8a6034", hi="#c8985a", w=0.9, top=1.02, line=0.9, sides=5)
    fr = smooth([(cx - 34, cy - 34), (cx - 20, cy - 16), (cx - 12, cy - 30), (cx - 2, cy - 18), (cx + 6, cy - 32), (cx + 18, cy - 22), (cx + 30, cy - 36), (cx, cy - 46)], tension=0.4)
    d.path(fr, fill="#8a6034", stroke=OUTLINE, stroke_width=2)
    hair_strokes(d, [[(cx - 30, cy - 44), (cx - 12, cy - 56), (cx + 10, cy - 58)], [(cx + 4, cy - 50), (cx + 24, cy - 52), (cx + 38, cy - 40)]], "#c8985a", sw=1.6)
    brows(d, cx, cy - 16, "#5a3a1a", thick=3, angle=2, w=11)
    eyes(d, cx, cy - 3, iris="#6a8a3a", spacing=15, w=9.5, h=4.4)
    nose(d, cx, cy - 2, SKIN_PALE, L=17, w=6)
    # shy slight smile, freckles, ink smudge on the cheek
    mouth(d, cx, cy + 25, SKIN_PALE, w=9, smile=1.2, lip="#c07070")
    rng = random.Random(7)
    for _ in range(12):
        sx = rng.choice((-1, 1))
        d.circle(cx + sx * rng.uniform(12, 26), cy + rng.uniform(4, 14), 0.9, fill="#a8603a", opacity=0.6)
    with d.g(T(cx - 22, cy + 20, -20)):
        d.ellipse(0, 0, 8, 3, fill="#0e0a24", opacity=0.6)
    frame(d, dict(dark="#2a1a48", base="#9a80d0", light="#f0e8ff"), gem_col="#ffd070")


# ------------------------------------------------------------------------------------------ townsfolk

@portrait
def netmender(d):
    """Nena Lagdameo: weathered woman, shell earrings, net over the shoulder."""
    background(d, "#0e3438", haze="#2a9a9a", haze2="#d0b070", seed=67)
    vignette(d)
    cx, cy = 126, 118
    blouse = dict(dark="#3a2a14", base="#a07a40", light="#dcc088")
    shoulders(d, blouse, top=188, spread=0.98)
    # long dark braid over the left shoulder (drawn later, after the head)
    neck(d, cx, cy + 42, 26, 28, SKIN_TAN)
    # hair mass behind the head
    hb = smooth([(cx - 46, cy + 20), (cx - 50, cy - 30), (cx - 30, cy - 62), (cx, cy - 66), (cx + 30, cy - 62), (cx + 50, cy - 30), (cx + 44, cy + 20)], tension=0.45)
    d.path(hb, stroke=OUTLINE, sw=4)
    d.path(hb, fill=d.lin([(0, "#3a2a20"), (1, "#100806")], cx, cy - 66, cx, cy + 20))
    head(d, cx, cy, SKIN_TAN, w=0.9, jaw=0.92, chin=0.86, top=1.0)
    ears(d, cx, cy + 2, SKIN_TAN, w=0.9)
    # centre-parted hair, pulled back, grey strands
    for sx in (-1, 1):
        hp = smooth([(cx, cy - 58), (cx + sx * 26, cy - 54), (cx + sx * 42, cy - 30), (cx + sx * 40, cy - 6), (cx + sx * 34, cy - 20), (cx + sx * 22, cy - 40), (cx + sx * 4, cy - 46)], tension=0.5)
        d.path(hp, fill="#2a1c14", stroke=OUTLINE, stroke_width=2)
        d.path(smooth([(cx + sx * 8, cy - 52), (cx + sx * 28, cy - 46), (cx + sx * 38, cy - 24)], closed=False), stroke="#a8a098", sw=1.4, op=0.8)
    # braid
    br = smooth_pts([(cx - 36, cy + 10), (cx - 44, cy + 50), (cx - 40, cy + 90), (cx - 30, cy + 130)], 12)
    for i in range(0, 11):
        x, y = br[i]
        d.ellipse(x, y, 9, 7, fill=OUTLINE)
    for i in range(0, 11):
        x, y = br[i]
        with d.g(T(x, y, 30 if i % 2 else -30)):
            d.ellipse(0, 0, 7.5, 5.2, fill=d.lin([(0, "#4a3428"), (1, "#140a06")], 0, -5, 0, 5))
    # fishing net over the right shoulder
    net_pts = [(150, 184), (206, 180), (240, 206), (246, 256), (170, 256), (158, 220)]
    d.path(smooth(net_pts, tension=0.3), fill="#1a1208", op=0.25)
    for i in range(9):
        t = i / 8
        a = (lerp(150, 206, t), lerp(184, 180, t))
        b = (lerp(158, 246, t), 256)
        d.path(f"M{f(a[0])},{f(a[1])} Q{f(a[0] + 20)},{f((a[1] + b[1]) / 2)} {f(b[0])},{f(b[1])}", stroke="#e8dcb0", sw=1.3, op=0.85)
        d.path(f"M{f(150 + 8 * t)},{f(184 + 72 * t)} Q{f(200)},{f(190 + 60 * t)} {f(206 + 40 * t)},{f(180 + 76 * t)}", stroke="#e8dcb0", sw=1.3, op=0.85)
    for (x, y) in ((214, 226), (188, 244)):   # cork floats
        d.ellipse(x, y, 7, 4.5, fill="#c86a2a", stroke=OUTLINE, stroke_width=1.6)
    # face: weathered, level gaze, a knowing half smile
    wrinkles(d, cx, cy, SKIN_TAN, fore=2, cheek=0.75, eye_bags=True, op=0.5)
    brows(d, cx, cy - 16, "#2a1c14", thick=3.4, angle=0.5, w=12)
    eyes(d, cx, cy - 3, iris="#3a2a1a", spacing=16, w=10, h=3.8, squint=0.25, age=2)
    nose(d, cx, cy - 2, SKIN_TAN, L=20, w=9)
    mouth(d, cx, cy + 27, SKIN_TAN, w=11, smile=1.0, lip="#8a4032")
    for sx in (-1, 1):
        ex = cx + sx * 36
        d.path(f"M{f(ex + sx * 4)},{cy + 14} L{f(ex + sx * 4)},{cy + 20}", stroke="#d8c8a0", sw=1.2)
        shell(d, ex + sx * 4, cy + 26, 1.2)
    frame(d, dict(dark="#1a3a3a", base="#7ab8b0", light="#e8fff8"), gem_col="#40d0c0")


def lerp(a, b, t):
    return a + (b - a) * t


@portrait
def cartographer(d):
    """Ibarra Quell: middle-aged man, magnifying lens, rolled maps."""
    background(d, "#3a2c18", haze="#d0a860", haze2="#6a8a60", seed=71)
    vignette(d)
    cx, cy = 122, 116
    # rolled maps poking up behind the left shoulder
    for (x, a, col) in ((52, -14, "#efe0b8"), (66, -6, "#e4d0a0"), (40, -24, "#f4e8c8")):
        with d.g(T(x, 250, a)):
            r = poly([(-8, 0), (8, 0), (8, -120), (-8, -120)])
            d.path(r, stroke=OUTLINE, sw=4)
            d.path(r, fill=d.lin([(0, lt(col, 0.3)), (0.5, col), (1, dk(col, 0.35))], -8, 0, 8, 0))
            d.ellipse(0, -120, 8, 3.4, fill=dk(col, 0.2), stroke=OUTLINE, stroke_width=2)
            d.ellipse(0, -120, 3.4, 1.4, fill=dk(col, 0.5))
            d.path("M-8,-40 L8,-40", stroke="#8a2a1a", sw=2.4)
    coat = dict(dark="#1e1a10", base="#5a5030", light="#9a8a58")
    shoulders(d, coat, top=186, spread=1.0)
    d.path("M108,188 L128,222 L148,188", fill="#e8e0cc", stroke=OUTLINE, stroke_width=3)
    d.path("M122,196 L128,222 L134,196 L128,192 Z", fill="#7a2a1a", stroke=OUTLINE, stroke_width=1.6)   # cravat
    for y in (206, 224, 242):
        d.circle(154, y, 3, fill="#c8a040", stroke=OUTLINE, stroke_width=1.2)
    neck(d, cx, cy + 42, 28, 26, SKIN)
    head(d, cx, cy, SKIN, w=0.96, jaw=0.92, chin=1.0, top=1.02)
    ears(d, cx, cy + 2, SKIN, w=0.96)
    # receding brown hair with grey temples
    for sx in (-1, 1):
        hp = smooth([(cx + sx * 20, cy - 52), (cx + sx * 40, cy - 38), (cx + sx * 46, cy - 12), (cx + sx * 42, cy + 6), (cx + sx * 36, cy - 14), (cx + sx * 30, cy - 36)], tension=0.5)
        d.path(hp, fill="#5a3a22", stroke=OUTLINE, stroke_width=2)
        d.path(smooth([(cx + sx * 40, cy - 22), (cx + sx * 42, cy - 8), (cx + sx * 40, cy + 2)], closed=False), stroke="#c8c8c0", sw=3)
    d.path(smooth([(cx - 22, cy - 50), (cx - 6, cy - 58), (cx + 6, cy - 58), (cx + 22, cy - 50)], closed=False), stroke="#5a3a22", sw=3)
    wrinkles(d, cx, cy, SKIN, fore=3, cheek=0.6, op=0.4)
    brows(d, cx, cy - 16, "#4a3020", thick=3.8, angle=1, w=12)
    eyes(d, cx, cy - 3, iris="#6a5a30", spacing=16, w=9.5, h=3.6, age=1)
    nose(d, cx, cy - 2, SKIN, L=24, w=8)
    # neat pointed mustache
    must = smooth([(cx - 22, cy + 22), (cx - 10, cy + 20), (cx, cy + 23), (cx + 10, cy + 20), (cx + 22, cy + 22), (cx + 10, cy + 26), (cx, cy + 27), (cx - 10, cy + 26)], tension=0.5)
    d.path(must, fill="#5a3a22", stroke=OUTLINE, stroke_width=1.6)
    d.path(f"M{cx - 8},{cy + 33} Q{cx},{cy + 35} {cx + 8},{cy + 32}", stroke=OUTLINE, sw=2.2)
    # magnifying lens held up before the right eye: eye enlarged behind glass
    lx, ly, R = cx + 30, cy - 2, 22
    # handle
    d.path(f"M{lx + 14},{ly + 16} L{lx + 44},{ly + 70}", stroke=OUTLINE, sw=9)
    d.path(f"M{lx + 14},{ly + 16} L{lx + 44},{ly + 70}", stroke="#6e4424", sw=5.4)
    d.circle(lx, ly, R, fill=d.rad([(0, "#f8f0d8", 0.25), (1, "#c8d8e0", 0.35)], lx - 6, ly - 6, R))
    # magnified iris
    d.ellipse(lx - 12, ly - 1, 13, 7, fill="#f4ece0", opacity=0.9)
    d.circle(lx - 12, ly - 1, 6.6, fill=d.rad([(0, "#a89a60"), (1, "#3a3018")], lx - 13, ly - 2, 7))
    d.circle(lx - 12, ly - 1, 3, fill="#0a0406")
    d.circle(lx - 14, ly - 3, 1.4, fill="#ffffff")
    d.circle(lx, ly, R, stroke=OUTLINE, stroke_width=7)
    d.circle(lx, ly, R, stroke=d.lin([(0, "#fff0b0"), (0.5, "#c8962e"), (1, "#5a3a0c")], lx - R, ly - R, lx + R, ly + R), stroke_width=4)
    d.path(f"M{lx - 12},{ly - 14} Q{lx - 4},{ly - 18} {lx + 4},{ly - 16}", stroke="#ffffff", sw=2.4, op=0.7)
    # fingers on the handle
    for k in range(3):
        d.path(rrect_path(lx + 22 + k * 3, ly + 34 + k * 7, 16, 8, 4), fill=SKIN["base"], stroke=OUTLINE, stroke_width=2)
    frame(d, BRONZE, gem_col="#6ac080")


@portrait
def widow(d):
    """Mirasol Hald: mourning grey, dark hair, a soldier's token on a cord."""
    background(d, "#22262e", haze="#5a6070", haze2="#3a4a5a", seed=73)
    vignette(d)
    cx, cy = 128, 118
    grey = dict(dark="#1e2024", base="#50545c", light="#8a8e96")
    # shawl/veil behind the head
    veil = smooth([(cx - 58, cy + 70), (cx - 60, cy - 20), (cx - 40, cy - 66), (cx, cy - 76), (cx + 40, cy - 66), (cx + 60, cy - 20), (cx + 58, cy + 70)], tension=0.45)
    d.path(veil, stroke=OUTLINE, sw=5)
    d.path(veil, fill=d.lin([(0, grey["light"]), (0.5, grey["base"]), (1, grey["dark"])], cx - 60, cy - 70, cx + 60, cy + 70))
    shoulders(d, grey, top=188, spread=0.95)
    d.path(smooth([(96, 188), (128, 210), (160, 188)], closed=False), stroke="#2a2c30", sw=2.4)
    # the token on a cord
    d.path(f"M112,190 Q128,226 144,190", stroke="#3a2a1a", sw=2)
    tx, ty = 128, 226
    tag = rrect_path(tx - 9, ty - 4, 18, 22, 5)
    d.path(tag, stroke=OUTLINE, sw=4)
    d.path(tag, fill=d.lin([(0, "#e8eef4"), (0.5, "#9aa4b0"), (1, "#4a525c")], tx - 9, ty - 4, tx + 9, ty + 18))
    d.path(f"M{tx - 4},{ty + 3} L{tx + 4},{ty + 3} M{tx - 4},{ty + 7} L{tx + 4},{ty + 7} M{tx - 3},{ty + 11} L{tx + 3},{ty + 11}", stroke="#3a424c", sw=1.2)
    d.circle(tx, ty - 1, 1.6, fill="#2a2c30")
    neck(d, cx, cy + 42, 24, 28, SKIN_PALE)
    head(d, cx, cy, SKIN_PALE, w=0.86, jaw=0.84, chin=0.8, top=1.0)
    # dark hair parted and drawn under the veil
    for sx in (-1, 1):
        hp = smooth([(cx, cy - 56), (cx + sx * 28, cy - 52), (cx + sx * 42, cy - 26), (cx + sx * 42, cy + 20), (cx + sx * 36, cy + 30), (cx + sx * 34, cy - 10), (cx + sx * 22, cy - 38), (cx + sx * 4, cy - 46)], tension=0.5)
        d.path(hp, fill="#18100e", stroke=OUTLINE, stroke_width=2)
        d.path(smooth([(cx + sx * 10, cy - 50), (cx + sx * 30, cy - 42), (cx + sx * 38, cy - 10)], closed=False), stroke="#4a3a34", sw=1.2)
    # veil front edge over the crown
    d.path(smooth([(cx - 50, cy - 20), (cx - 36, cy - 58), (cx, cy - 70), (cx + 36, cy - 58), (cx + 50, cy - 20), (cx + 40, cy - 44), (cx, cy - 56), (cx - 40, cy - 44)], tension=0.45), fill=grey["base"], stroke=OUTLINE, stroke_width=3)
    # sorrowful brows (inner ends raised), downcast eyes, closed mouth
    for sx in (-1, 1):
        bx = cx + sx * 16
        pts = [(bx - sx * 11, cy - 20), (bx, cy - 18), (bx + sx * 12, cy - 13)]
        d.path(ribbon(qbez(*pts, n=10), taper(10, 3, 0.9, 0.3, peak=0.3)), fill="#18100e", stroke=OUTLINE, stroke_width=0.8)
    eyes(d, cx, cy - 2, iris="#4a4a3a", spacing=16, w=10, h=3.6, lid=2.6, squint=0.35)
    for sx in (-1, 1):
        d.path(f"M{cx + sx * 8},{cy + 5} Q{cx + sx * 16},{cy + 9} {cx + sx * 24},{cy + 5}", stroke="#8a5a60", sw=1.4, op=0.5)
    nose(d, cx, cy - 1, SKIN_PALE, L=19, w=7)
    d.path(f"M{cx - 9},{cy + 29} Q{cx},{cy + 27} {cx + 9},{cy + 29}", stroke=OUTLINE, sw=2.2)
    d.path(f"M{cx - 6},{cy + 32} Q{cx},{cy + 33} {cx + 6},{cy + 32}", stroke="#a06a6a", sw=1.8, op=0.5)
    d.path(f"M{cx - 14},{cy + 6} Q{cx - 15},{cy + 14} {cx - 13},{cy + 20}", stroke="#c8e0f0", sw=1.6, op=0.6)   # tear track
    frame(d, dict(dark="#2a2c30", base="#8a8e96", light="#e8eaee"), gem_col="#9aa0b0")


@portrait
def keeper(d):
    """Keeper Tomas Dalisay: shrine-keeper, shaved head, prayer beads, bestiary tome."""
    background(d, "#2e2010", haze="#c89040", haze2="#6a8a50", motes="#ffd080", seed=79)
    lamp_glow(d, 50, 70, 70, "#ffc060", 0.45)
    vignette(d)
    cx, cy = 132, 114
    robe = dict(dark="#3a2008", base="#a06a20", light="#e0a850")
    shoulders(d, robe, top=184, spread=1.0)
    # wrap robe crossing + dark sash
    d.path("M96,186 L150,256", stroke=OUTLINE, sw=5)
    d.path("M96,186 L150,256", stroke="#e8c070", sw=2.6)
    d.path("M72,236 L200,226 L204,244 L70,256 Z", fill="#3a2410", stroke=OUTLINE, stroke_width=2.4)
    neck(d, cx, cy + 42, 28, 26, SKIN_TAN)
    head(d, cx, cy, SKIN_TAN, w=0.98, jaw=0.94, chin=0.94, top=1.06)
    ears(d, cx, cy + 2, SKIN_TAN, w=0.98)
    # shaved head: scalp stubble shading + highlight, no hair mass
    d.path(smooth([(cx - 38, cy - 20), (cx - 30, cy - 46), (cx, cy - 56), (cx + 30, cy - 46), (cx + 38, cy - 20), (cx + 28, cy - 34), (cx, cy - 40), (cx - 28, cy - 34)], tension=0.45), fill="#2a1a10", op=0.25)
    d.path(smooth([(cx - 22, cy - 46), (cx - 6, cy - 54), (cx + 10, cy - 52)], closed=False), stroke="#ffffff", sw=4, op=0.4)
    # shrine mark on the brow
    d.circle(cx, cy - 30, 3.4, fill="#c83a1a", stroke=OUTLINE, stroke_width=1)
    wrinkles(d, cx, cy, SKIN_TAN, fore=2, cheek=0.5, op=0.35)
    brows(d, cx, cy - 16, "#1a100a", thick=3, angle=1.5, w=12)
    eyes(d, cx, cy - 3, iris="#3a2a14", spacing=17, w=9.5, h=3.6, lid=1.4, squint=0.2)
    nose(d, cx, cy - 2, SKIN_TAN, L=22, w=9)
    mouth(d, cx, cy + 27, SKIN_TAN, w=10, smile=0.6, lip="#7a3a2a")
    stubble(d, cx, cy, "#1a100a", op=0.18, w=0.94, seed=11)
    # prayer beads: large wooden loop with a tassel
    for i in range(17):
        t = i / 16
        a = math.pi * (0.08 + 0.84 * t)
        x = cx + 44 * math.cos(a)
        y = 180 + 48 * math.sin(a)
        d.circle(x, y, 5.2, fill=OUTLINE)
        d.circle(x, y, 4, fill=d.rad([(0, "#c88a4a"), (1, "#4a2408")], x - 1.4, y - 1.4, 5))
    d.circle(cx, 234, 6, fill=OUTLINE)
    d.circle(cx, 234, 4.8, fill="#2a8a6a")
    d.path(poly([(cx - 4, 238), (cx + 4, 238), (cx + 6, 254), (cx - 6, 254)]), fill="#c83a1a", stroke=OUTLINE, stroke_width=1.6)

    def tome_mark(dd):
        # beast-eye sigil with claw marks on the cover
        dd.path("M-10,0 Q0,-9 10,0 Q0,9 -10,0 Z", fill="#e0c060", stroke=OUTLINE, stroke_width=1.4)
        dd.path("M0,-5 Q2,0 0,5 Q-2,0 0,-5 Z", fill="#1a0a04")
        for k in (-5, 0, 5):
            dd.path(f"M{k - 4},-20 L{k + 2},-10", stroke="#e0c060", sw=1.6)
    book(d, 196, 214, 52, 62, dict(dark="#1e0e06", base="#4a2412", light="#7a4a2a"), ang=-12, emblem=tome_mark)
    frame(d, BRONZE, gem_col="#40c080")


@portrait
def refugee(d):
    """Yusra Ven: young woman from Tambakol, hooded travel cloak with ash on it."""
    background(d, "#261a18", haze="#6a5a52", haze2="#e06a2a", motes="#ff9a40", seed=83)
    vignette(d)
    cx, cy = 128, 120
    cloak = dict(dark="#1a140e", base="#5a4a3a", light="#948272")
    shoulders(d, cloak, top=186, spread=1.0)
    hood_o = [(cx, 30), (cx + 52, 46), (cx + 68, 104), (cx + 72, 172), (cx + 48, 198), (cx - 48, 198), (cx - 72, 172), (cx - 68, 104), (cx - 52, 46)]
    hd = smooth(hood_o, tension=0.5)
    d.path(hd, stroke=OUTLINE, sw=6)
    d.path(hd, fill=d.lin([(0, cloak["light"]), (0.45, cloak["base"]), (1, cloak["dark"])], cx - 68, 40, cx + 68, 190))
    # ash dusting on hood + shoulders, a scorched hem
    rng = random.Random(5)
    for _ in range(46):
        x, y = rng.uniform(40, 216), rng.uniform(40, 250)
        if abs(x - cx) < 40 and 60 < y < 180:
            continue
        r = rng.uniform(1.5, 5)
        d.circle(x, y, r, fill=rng.choice(("#c8c4be", "#8a8680", "#e0dcd6")), opacity=rng.uniform(0.35, 0.7))
    d.path(smooth([(cx - 72, 170), (cx - 60, 184), (cx - 40, 178)], closed=False), stroke="#140c08", sw=5, op=0.7)
    op_ = smooth([(cx, 52), (cx + 42, 72), (cx + 50, 130), (cx + 38, 184), (cx - 38, 184), (cx - 50, 130), (cx - 42, 72)], tension=0.5)
    d.path(op_, fill="#0c0806")
    neck(d, cx, cy + 42, 24, 26, SKIN)
    head(d, cx, cy, SKIN, w=0.86, jaw=0.86, chin=0.84, top=0.98)
    # dark hair framing the face, loose strand
    for sx in (-1, 1):
        hp = smooth([(cx, cy - 54), (cx + sx * 30, cy - 50), (cx + sx * 42, cy - 22), (cx + sx * 42, cy + 40), (cx + sx * 34, cy + 20), (cx + sx * 30, cy - 12), (cx + sx * 12, cy - 38)], tension=0.5)
        d.path(hp, fill="#1a0e0a", stroke=OUTLINE, stroke_width=2)
    d.path(smooth([(cx + 6, cy - 44), (cx + 16, cy - 20), (cx + 10, cy + 6)], closed=False), stroke="#1a0e0a", sw=2.4)
    # hood rim shadow
    d.path(smooth([(cx - 50, cy - 26), (cx - 30, cy - 58), (cx, cy - 64), (cx + 30, cy - 58), (cx + 50, cy - 26), (cx + 30, cy - 42), (cx, cy - 46), (cx - 30, cy - 42)], tension=0.5), fill="#0c0806", op=0.6)
    brows(d, cx, cy - 16, "#1a0e0a", thick=3.2, angle=2.8, w=12)
    eyes(d, cx, cy - 3, iris="#7a4a1a", spacing=16, w=10.5, h=4.4, lid=1.0)
    wrinkles(d, cx, cy, SKIN, eye_bags=True, op=0.45)
    nose(d, cx, cy - 2, SKIN, L=19, w=7)
    d.path(f"M{cx - 9},{cy + 28} Q{cx},{cy + 29} {cx + 9},{cy + 28}", stroke=OUTLINE, sw=2.2)
    d.path(f"M{cx - 6},{cy + 31} Q{cx},{cy + 33} {cx + 6},{cy + 31}", stroke="#b0605a", sw=1.8, op=0.6)
    # soot smudge on the cheek + ember light from below-left
    with d.g(T(cx + 20, cy + 14, 20, 1, 0.4)):
        d.circle(0, 0, 9, fill=d.rad([(0, "#2a1a14", 0.45), (1, "#2a1a14", 0)], 0, 0, 9))
    d.circle(40, 230, 70, fill=d.rad([(0, "#ff7a2a", 0.3), (1, "#ff7a2a", 0)], 40, 230, 70))
    # cloak clasp: a plain iron ring
    d.circle(cx, 200, 7, stroke=OUTLINE, stroke_width=5)
    d.circle(cx, 200, 7, stroke="#8a8e94", stroke_width=2.6)
    frame(d, dict(dark="#2a2420", base="#8a7a6a", light="#e8dcd0"), gem_col="#ff8a40")
