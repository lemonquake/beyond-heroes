"""bh-002 character portraits (portraits/*.svg, viewBox 0 0 256 256): painted-emblem busts on a dark vignette with an
ornate frame edge. Same toolkit and ThorVG-safe subset as the icons (gradients + paths only)."""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, OUTLINE, GOLD, STEEL, CRIMSON, BRONZE, LEATHER, f, poly, smooth, mix, lt, dk, ribbon, taper, arc_pts,
                    bez, qbez, star_pts, ngon, polar, rrect_path, circle_path, lerp)

PORTRAITS = {}
AE_C = "#7ff3ff"
AE_HI = "#d8fdff"

SKIN = dict(light="#f4cfa8", base="#d9a077", dark="#8c5438", shade="#5a2a1a")
SKIN_TAN = dict(light="#e2aa80", base="#b0714a", dark="#6a3a22", shade="#3a1a0c")
SKIN_OLD = dict(light="#f2d6bc", base="#cfa088", dark="#8a5a48", shade="#4a2a20")
SKIN_PALE = dict(light="#f6dccb", base="#d8ab94", dark="#96604c", shade="#4a2a28")

S = 256


def portrait(fn):
    def build():
        d = Doc(S, S, name="pt_" + fn.__name__)
        fn(d)
        return d
    PORTRAITS[fn.__name__] = build
    return fn


# ------------------------------------------------------------------------------------------ background + frame

def background(d, inner, outer="#040208", haze=None, haze2=None, motes=None, seed=1):
    d.rect(0, 0, S, S, fill=d.rad([(0, inner), (0.55, mix(inner, outer, 0.6)), (1, outer)], 128, 100, 190))
    rng = random.Random(seed)
    for col, n in ((haze, 3), (haze2, 2)):
        if not col:
            continue
        for _ in range(n):
            x, y, r = rng.uniform(30, 226), rng.uniform(20, 170), rng.uniform(50, 90)
            d.circle(x, y, r, fill=d.rad([(0, col, 0.24), (1, col, 0)], x, y, r))
    if motes:
        for _ in range(14):
            x, y = rng.uniform(20, 236), rng.uniform(20, 200)
            r = rng.uniform(0.8, 2.2)
            d.circle(x, y, r * 3, fill=d.rad([(0, motes, 0.35), (1, motes, 0)], x, y, r * 3))
            d.circle(x, y, r * 0.7, fill=lt(motes, 0.5), opacity=0.9)


def vignette(d):
    d.rect(0, 0, S, S, fill=d.rad([(0, "#000000", 0), (0.6, "#000000", 0), (0.88, "#000000", 0.45), (1, "#000000", 0.8)], 128, 118, 185))


def frame(d, metal=GOLD, gem_col=AE_C):
    # dark outer band
    d.path(f"M0,0 L{S},0 L{S},{S} L0,{S} Z " + rrect_path(9, 9, S - 18, S - 18, 10), fill="#07040a", fill_rule="evenodd")
    bev = d.lin([(0, metal["light"]), (0.4, metal["base"]), (0.75, metal["dark"]), (1, dk(metal["dark"], 0.4))], 0, 0, S, S)
    d.path(rrect_path(7, 7, S - 14, S - 14, 12), stroke=OUTLINE, sw=9)
    d.path(rrect_path(7, 7, S - 14, S - 14, 12), stroke=bev, sw=5.5)
    d.path(rrect_path(12, 12, S - 24, S - 24, 8), stroke="#000000", sw=1.6, op=0.8)
    d.path(rrect_path(3, 3, S - 6, S - 6, 14), stroke=metal["dark"], sw=1.2, op=0.9)
    # corner ornaments: filigree L with gem
    for (x, y, sx, sy) in ((7, 7, 1, 1), (S - 7, 7, -1, 1), (7, S - 7, 1, -1), (S - 7, S - 7, -1, -1)):
        for a, b in (((0, 0), (1, 0)), ((0, 0), (0, 1))):
            pts = [(x + sx * (a[0] * 4 + b[0] * t), y + sy * (a[1] * 4 + b[1] * t)) for t in (6, 22, 34)]
            curl = [(x + sx * (b[0] * 38 + b[1] * 9), y + sy * (b[1] * 38 + b[0] * 9)), (x + sx * (b[0] * 32 + b[1] * 13), y + sy * (b[1] * 32 + b[0] * 13))]
            dd = smooth(pts + curl, closed=False)
            d.path(dd, stroke=OUTLINE, sw=5.5)
            d.path(dd, stroke=metal["base"], sw=2.8)
            d.path(dd, stroke=metal["light"], sw=0.9, op=0.8)
        dia = [(x + sx * 10, y - sy * 2), (x + sx * 22, y + sy * 10), (x + sx * 10, y + sy * 22), (x - sx * 2, y + sy * 10)]
        d.path(poly(dia), fill=d.lin([(0, metal["light"]), (1, metal["dark"])], x, y, x + sx * 22, y + sy * 22), stroke=OUTLINE, stroke_width=2)
        d.circle(x + sx * 10, y + sy * 10, 7, fill=gem_col, opacity=0.25)
        d.circle(x + sx * 10, y + sy * 10, 4.2, fill=d.rad([(0, "#ffffff"), (0.4, gem_col), (1, dk(gem_col, 0.6))], x + sx * 10 - 1.4, y + sy * 10 - 1.4, 5), stroke=OUTLINE, stroke_width=1.2)
    # top-centre crest notch
    d.path(poly([(118, 5), (138, 5), (132, 13), (128, 16), (124, 13)]), fill=d.lin([(0, metal["light"]), (1, metal["dark"])], 118, 5, 138, 16), stroke=OUTLINE, stroke_width=1.6)


# ------------------------------------------------------------------------------------------ anatomy helpers

def neck(d, cx, cy, w, h, skin):
    dd = poly([(cx - w / 2, cy), (cx + w / 2, cy), (cx + w / 2 + 4, cy + h), (cx - w / 2 - 4, cy + h)])
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, skin["base"]), (0.6, skin["dark"]), (1, skin["shade"])], cx - w / 2, cy, cx + w / 2, cy + h))
    d.path(poly([(cx - w / 2, cy), (cx + w / 2, cy), (cx + w / 2, cy + 14), (cx - w / 2, cy + 20)]), fill=skin["shade"], op=0.45)


def head_pts(cx, cy, w=1.0, jaw=1.0, chin=1.0, top=1.0):
    return [(cx, cy - 52 * top), (cx + 26 * w, cy - 47 * top), (cx + 38 * w, cy - 28 * top), (cx + 40 * w, cy - 4),
            (cx + 37 * w * jaw, cy + 18), (cx + 28 * w * jaw, cy + 36), (cx + 14 * chin, cy + 48), (cx, cy + 51),
            (cx - 14 * chin, cy + 48), (cx - 28 * w * jaw, cy + 36), (cx - 37 * w * jaw, cy + 18), (cx - 40 * w, cy - 4),
            (cx - 38 * w, cy - 28 * top), (cx - 26 * w, cy - 47 * top)]


def ears(d, cx, cy, skin, w=1.0, earring=False):
    for sx in (-1, 1):
        ex = cx + sx * 40 * w
        e = smooth([(ex, cy - 14), (ex + sx * 9, cy - 16), (ex + sx * 11, cy - 2), (ex + sx * 6, cy + 14), (ex - sx * 1, cy + 12)], tension=0.5)
        d.path(e, stroke=OUTLINE, sw=4.4)
        d.path(e, fill=d.lin([(0, skin["base"]), (1, skin["dark"])], ex, cy, ex + sx * 11, cy))
        d.path(smooth([(ex + sx * 3, cy - 8), (ex + sx * 7, cy - 6), (ex + sx * 5, cy + 6)], closed=False), stroke=skin["shade"], sw=1.6, op=0.7)
        if earring and sx == 1:
            d.circle(ex + sx * 6, cy + 20, 5, stroke=OUTLINE, stroke_width=4.4)
            d.circle(ex + sx * 6, cy + 20, 5, stroke=GOLD["base"], stroke_width=2.4)
            d.circle(ex + sx * 4, cy + 17, 1.2, fill="#ffffff", opacity=0.9)


def head(d, cx, cy, skin, **kw):
    pts = head_pts(cx, cy, **kw)
    dd = smooth(pts, tension=0.5)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.rad([(0, skin["light"]), (0.5, skin["base"]), (1, skin["dark"])], cx - 12, cy - 16, 70))
    # form shadow on the far (right) side + under-jaw
    sh = smooth([(cx + 8, cy - 50), (cx + 26, cy - 46), (cx + 38, cy - 28), (cx + 40, cy - 4), (cx + 37, cy + 18), (cx + 28, cy + 36),
                 (cx + 14, cy + 48), (cx + 4, cy + 50), (cx + 20, cy + 30), (cx + 26, cy + 4), (cx + 22, cy - 26)], tension=0.5)
    d.path(sh, fill=skin["shade"], op=0.28)
    # cheek warmth
    for sx in (-1, 1):
        d.circle(cx + sx * 22, cy + 14, 11, fill=d.rad([(0, "#e0604a", 0.22), (1, "#e0604a", 0)], cx + sx * 22, cy + 14, 11))
    return dd


def eyes(d, cx, cy, iris="#4a6a8a", glow=None, spacing=17, w=11, h=4.6, lid=0.0, age=0, squint=0.0):
    for sx in (-1, 1):
        ex = cx + sx * spacing
        # socket shadow
        d.ellipse(ex, cy - 1, w + 3, h + 4, fill=d.rad([(0, "#3a1a10", 0.35), (1, "#3a1a10", 0)], ex, cy - 1, w + 4))
        top = cy - h * (1 - squint)
        dd = f"M{f(ex - w)},{f(cy)} Q{f(ex)},{f(top - h)} {f(ex + w)},{f(cy)} Q{f(ex)},{f(cy + h * 1.2)} {f(ex - w)},{f(cy)} Z"
        d.path(dd, fill="#f4ece0" if not glow else "#1a2a30")
        ir = h * 1.05
        if glow:
            d.circle(ex, cy, ir * 3.4, fill=d.rad([(0, glow, 0.7), (1, glow, 0)], ex, cy, ir * 3.4))
            d.circle(ex, cy, ir, fill=d.rad([(0, "#ffffff"), (0.5, lt(glow, 0.4)), (1, glow)], ex, cy, ir))
        else:
            d.circle(ex + sx * 0.5, cy, ir, fill=d.rad([(0, lt(iris, 0.4)), (1, dk(iris, 0.4))], ex, cy - 1, ir))
            d.circle(ex + sx * 0.5, cy, ir * 0.45, fill="#0a0406")
            d.circle(ex - 1.2, cy - 1.4, ir * 0.25, fill="#ffffff", opacity=0.9)
        # upper lid line + lash weight
        d.path(f"M{f(ex - w - 1)},{f(cy + 0.5)} Q{f(ex)},{f(top - h - 0.5 + lid)} {f(ex + w + 1)},{f(cy - 0.5)}", stroke=OUTLINE, sw=2.6)
        d.path(f"M{f(ex - w * 0.7)},{f(cy + h * 1.0)} Q{f(ex)},{f(cy + h * 1.5)} {f(ex + w * 0.8)},{f(cy + h * 0.7)}", stroke="#5a2a1a", sw=0.9, op=0.6)
        if age:
            for k in range(age):
                d.path(f"M{f(ex + sx * (w + 2))},{f(cy - 1 + k * 3)} L{f(ex + sx * (w + 8))},{f(cy - 3 + k * 4)}", stroke="#5a2a1a", sw=0.9, op=0.6)


def brows(d, cx, cy, col, thick=4.0, angle=0.0, spacing=17, w=13):
    for sx in (-1, 1):
        bx = cx + sx * spacing
        pts = [(bx - sx * w * 0.9, cy + 2 + angle), (bx, cy - 2), (bx + sx * w, cy + 1 - angle * 0.3)]
        d.path(ribbon(qbez(*pts, n=10), taper(10, thick, 0.9, 0.3, peak=0.3)), fill=col, stroke=OUTLINE, stroke_width=0.8)


def nose(d, cx, cy, skin, L=20, w=7):
    d.path(smooth([(cx + 2, cy), (cx + 5, cy + L * 0.6), (cx + w, cy + L), (cx + 1, cy + L + 3)], closed=False), stroke=skin["shade"], sw=2.2, op=0.75)
    d.path(f"M{f(cx - w + 1)},{f(cy + L)} Q{f(cx - w - 1)},{f(cy + L + 3)} {f(cx - 2)},{f(cy + L + 3)}", stroke=skin["shade"], sw=1.8, op=0.7)
    d.path(f"M{f(cx - 2)},{f(cy + 4)} L{f(cx - 3)},{f(cy + L - 4)}", stroke=skin["light"], sw=2, op=0.6)


def mouth(d, cx, cy, skin, w=13, smile=0.0, lip="#a0503c"):
    d.path(f"M{f(cx - w)},{f(cy - smile)} Q{f(cx)},{f(cy + 3 + smile)} {f(cx + w)},{f(cy - smile)}", stroke=OUTLINE, sw=2.4)
    d.path(f"M{f(cx - w * 0.7)},{f(cy + 2)} Q{f(cx)},{f(cy + 7 + smile)} {f(cx + w * 0.7)},{f(cy + 2)}", stroke=lip, sw=2.6, op=0.7)
    d.path(f"M{f(cx - 4)},{f(cy + 11)} Q{f(cx)},{f(cy + 13)} {f(cx + 4)},{f(cy + 11)}", stroke=skin["shade"], sw=1.4, op=0.5)


def shoulders(d, pal, top=182, spread=1.0, neck_w=34):
    pts = [(128 - neck_w / 2 - 4, top - 6), (128 - 70 * spread, top + 6), (128 - 108 * spread, top + 30), (128 - 124 * spread, S + 4),
           (128 + 124 * spread, S + 4), (128 + 108 * spread, top + 30), (128 + 70 * spread, top + 6), (128 + neck_w / 2 + 4, top - 6)]
    dd = smooth(pts, tension=0.35)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, pal["light"]), (0.45, pal["base"]), (1, pal["dark"])], 20, top, 236, S))
    return dd


def strands(d, pts_list, col, w=3.0, op=0.9):
    for pts in pts_list:
        d.path(ribbon(smooth_list(pts), taper(16, w, 1.0, 0.1, peak=0.1)), fill=col, op=op)


def smooth_list(pts, n=16):
    from bh_shapes import smooth_pts
    return smooth_pts(pts, n)


# ------------------------------------------------------------------------------------------ heroes

@portrait
def knight(d):
    background(d, "#4a1418", haze="#b02020", haze2="#e08a30", seed=3)
    vignette(d)
    steel = dict(dark="#2a303a", base="#9aa4b2", light="#f2f6fa")
    cape = dict(dark="#3a060c", base="#8a1420", light="#d04a50")
    # cape collar behind
    d.path(smooth([(40, 256), (52, 196), (90, 176), (166, 176), (204, 196), (216, 256)], tension=0.4), fill=cape["dark"], stroke=OUTLINE, stroke_width=4)
    # chest plate + tabard
    chest = [(84, 186), (172, 186), (184, 256), (72, 256)]
    d.path(poly(chest), stroke=OUTLINE, sw=5)
    d.path(poly(chest), fill=d.lin([(0, steel["light"]), (0.45, steel["base"]), (1, steel["dark"])], 80, 186, 180, 256))
    d.path(poly([(108, 200), (148, 200), (140, 256), (116, 256)]), fill=d.lin([(0, cape["light"]), (1, cape["dark"])], 108, 200, 148, 256), stroke=OUTLINE, stroke_width=2.4)
    d.path("M112,204 L144,204", stroke=GOLD["base"], sw=3)
    # aether channels on the chest
    for sx in (-1, 1):
        ch = f"M{128 + sx * 24},{196} L{128 + sx * 34},{214} L{128 + sx * 30},{246}"
        d.path(ch, stroke="#021018", sw=4.4)
        d.path(ch, stroke=AE_C, sw=6, op=0.25)
        d.path(ch, stroke=AE_C, sw=2.2)
        d.path(ch, stroke="#ffffff", sw=0.8)
    # pauldrons (3 lames each)
    for sx in (-1, 1):
        for k in range(3):
            cx0 = 128 + sx * (62 + k * 8)
            cy0 = 196 + k * 18
            pts = [(cx0 - sx * 30, cy0 - 6), (cx0, cy0 - 20 + k * 4), (cx0 + sx * 34, cy0 - 2), (cx0 + sx * 38, cy0 + 22), (cx0 - sx * 22, cy0 + 16)]
            dd = smooth(pts, tension=0.5)
            d.path(dd, stroke=OUTLINE, sw=5)
            d.path(dd, fill=d.lin([(0, steel["light"]), (0.5, steel["base"]), (1, steel["dark"])], cx0 - 30, cy0 - 20, cx0 + 38, cy0 + 22))
            d.path(smooth([(cx0 - sx * 24, cy0 - 4), (cx0, cy0 - 16 + k * 4), (cx0 + sx * 30, cy0 - 1)], closed=False), stroke=GOLD["base"], sw=2.4)
        ch = f"M{128 + sx * 52},{190} Q{128 + sx * 72},{182} {128 + sx * 92},{196}"
        d.path(ch, stroke=AE_C, sw=5, op=0.25)
        d.path(ch, stroke=AE_C, sw=1.8)
    # gorget
    g = smooth([(92, 170), (164, 170), (172, 192), (84, 192)], tension=0.2)
    d.path(g, stroke=OUTLINE, sw=5)
    d.path(g, fill=d.lin([(0, steel["light"]), (1, steel["dark"])], 92, 170, 172, 192))
    d.path("M90,180 L166,180", stroke=steel["dark"], sw=1.6)
    # great helm
    cx, cy = 128, 104
    hp = [(cx, cy - 66), (cx + 34, cy - 58), (cx + 46, cy - 30), (cx + 46, cy + 44), (cx + 30, cy + 62), (cx - 30, cy + 62), (cx - 46, cy + 44), (cx - 46, cy - 30), (cx - 34, cy - 58)]
    hd = smooth(hp, tension=0.35)
    d.path(hd, stroke=OUTLINE, sw=6)
    d.path(hd, fill=d.lin([(0, steel["light"]), (0.3, steel["base"]), (0.62, dk(steel["base"], 0.25)), (1, steel["dark"])], cx - 46, 0, cx + 46, 0))
    d.path(smooth([(cx - 36, cy - 40), (cx - 20, cy - 56), (cx, cy - 60)], closed=False), stroke="#ffffff", sw=3, op=0.45)
    # crest ridge (gold)
    ridge = [(cx - 5, cy - 70), (cx + 5, cy - 70), (cx + 4, cy + 2), (cx - 4, cy + 2)]
    d.path(poly(ridge), fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], cx - 5, 0, cx + 5, 0), stroke=OUTLINE, stroke_width=2)
    fin = smooth([(cx - 3, cy - 68), (cx - 2, cy - 84), (cx + 12, cy - 92), (cx + 30, cy - 86), (cx + 16, cy - 78), (cx + 6, cy - 62)], tension=0.5)
    d.path(fin, fill=d.lin([(0, cape["light"]), (1, cape["dark"])], cx, cy - 92, cx + 30, cy - 62), stroke=OUTLINE, stroke_width=3)
    # visor slit glowing aether
    d.circle(cx, cy - 6, 44, fill=d.rad([(0, AE_C, 0.35), (1, AE_C, 0)], cx, cy - 6, 44))
    d.path(rrect_path(cx - 40, cy - 12, 80, 11, 5), fill="#03070a", stroke=OUTLINE, stroke_width=2)
    d.path(rrect_path(cx - 36, cy - 9, 72, 5, 2.5), fill=AE_C)
    d.path(rrect_path(cx - 30, cy - 7.6, 60, 2.2, 1.1), fill="#ffffff")
    d.path(f"M{cx - 42},{cy + 1} L{cx + 42},{cy + 1}", stroke=steel["light"], sw=1.4, op=0.6)
    # cross reinforcement + breaths
    d.path(poly([(cx - 4, cy + 4), (cx + 4, cy + 4), (cx + 4, cy + 60), (cx - 4, cy + 60)]), fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], cx - 4, 0, cx + 4, 0), stroke=OUTLINE, stroke_width=1.6)
    for yy in (cy + 16, cy + 28, cy + 40):
        for sx in (-1, 1):
            d.path(rrect_path(cx + sx * 22 - 6, yy - 2, 12, 4, 2), fill="#05040a")
    d.path(f"M{cx - 46},{cy - 22} L{cx + 46},{cy - 22}", stroke=GOLD["base"], sw=3)
    for sx in (-1, 1):
        d.circle(cx + sx * 40, cy + 20, 3, fill=GOLD["light"], stroke=OUTLINE, stroke_width=1)
    frame(d, GOLD)


@portrait
def mage(d):
    background(d, "#1a1650", haze="#3a3ab0", haze2="#2aa0c0", motes=AE_C, seed=5)
    vignette(d)
    indigo = dict(dark="#0a0a2a", base="#262a78", light="#5a62c8")
    cx, cy = 128, 118
    # mantle + coat
    shoulders(d, indigo, top=190, spread=0.95)
    d.path(smooth([(60, 200), (128, 226), (196, 200), (206, 256), (50, 256)], tension=0.4), fill=dk(indigo["base"], 0.25), stroke=OUTLINE, stroke_width=3)
    # runic trim on mantle
    d.path(smooth([(60, 202), (128, 228), (196, 202)], closed=False), stroke=STEEL["light"], sw=2.4)
    for i in range(9):
        x = 72 + i * 14
        y = 206 + 18 * math.sin(math.pi * (i + 0.5) / 9)
        d.path(f"M{x - 2},{f(y + 5)} L{x},{f(y + 11)} L{x + 2},{f(y + 5)}", stroke=AE_C, sw=1.4)
    # one pauldron (left) + harness strap
    pl = smooth([(28, 226), (44, 196), (80, 190), (92, 206), (76, 230), (40, 240)], tension=0.5)
    d.path(pl, stroke=OUTLINE, sw=5)
    d.path(pl, fill=d.lin([(0, "#e8eef8"), (0.5, "#8a94ac"), (1, "#2a3040")], 28, 190, 92, 240))
    d.path(smooth([(40, 212), (60, 198), (84, 200)], closed=False), stroke=AE_C, sw=2)
    d.path("M150,212 L196,256", stroke=OUTLINE, sw=9)
    d.path("M150,212 L196,256", stroke=LEATHER["base"], sw=6)
    d.circle(162, 224, 5, fill=d.rad([(0, GOLD["light"]), (1, GOLD["dark"])], 160, 222, 6), stroke=OUTLINE, stroke_width=1.4)
    # hood back
    hood_o = [(cx, 26), (cx + 52, 44), (cx + 70, 100), (cx + 74, 172), (cx + 50, 200), (cx - 50, 200), (cx - 74, 172), (cx - 70, 100), (cx - 52, 44)]
    hd = smooth(hood_o, tension=0.5)
    d.path(hd, stroke=OUTLINE, sw=6)
    d.path(hd, fill=d.lin([(0, indigo["light"]), (0.45, indigo["base"]), (1, indigo["dark"])], cx - 70, 40, cx + 70, 190))
    # hood opening shadow
    op_ = smooth([(cx, 48), (cx + 44, 70), (cx + 54, 130), (cx + 40, 184), (cx - 40, 184), (cx - 54, 130), (cx - 44, 70)], tension=0.5)
    d.path(op_, fill="#05040e")
    neck(d, cx, cy + 44, 26, 30, SKIN_PALE)
    head(d, cx, cy, SKIN_PALE, w=0.9, jaw=0.9, chin=0.85)
    # hair framing the face
    hair = dict(base="#1a1020", light="#4a3a5a")
    for sx in (-1, 1):
        hp = smooth([(cx, cy - 54), (cx + sx * 30, cy - 50), (cx + sx * 42, cy - 20), (cx + sx * 40, cy + 30), (cx + sx * 46, cy + 70),
                     (cx + sx * 30, cy + 40), (cx + sx * 30, cy - 10), (cx + sx * 14, cy - 36)], tension=0.5)
        d.path(hp, fill=hair["base"], stroke=OUTLINE, stroke_width=2.4)
        d.path(smooth([(cx + sx * 14, cy - 46), (cx + sx * 34, cy - 30), (cx + sx * 36, cy + 20)], closed=False), stroke=hair["light"], sw=1.6, op=0.7)
    # hood rim shadow over forehead
    d.path(smooth([(cx - 52, cy - 30), (cx - 30, cy - 60), (cx, cy - 66), (cx + 30, cy - 60), (cx + 52, cy - 30), (cx + 30, cy - 46), (cx, cy - 50), (cx - 30, cy - 46)], tension=0.5), fill="#05040e", op=0.7)
    brows(d, cx, cy - 16, "#1a1020", thick=3.2, angle=1.5)
    eyes(d, cx, cy - 3, glow=AE_C, spacing=16, w=10, h=4.2)
    nose(d, cx, cy - 2, SKIN_PALE, L=18, w=6)
    mouth(d, cx, cy + 27, SKIN_PALE, w=10, smile=0.5, lip="#b0505a")
    # circlet with aether gem
    d.path(smooth([(cx - 38, cy - 34), (cx, cy - 42), (cx + 38, cy - 34)], closed=False), stroke=OUTLINE, sw=5)
    d.path(smooth([(cx - 38, cy - 34), (cx, cy - 42), (cx + 38, cy - 34)], closed=False), stroke=STEEL["light"], sw=2.4)
    d.circle(cx, cy - 42, 12, fill=d.rad([(0, AE_C, 0.6), (1, AE_C, 0)], cx, cy - 42, 12))
    d.path(poly([(cx, cy - 50), (cx + 5, cy - 42), (cx, cy - 34), (cx - 5, cy - 42)]), fill=d.lin([(0, "#ffffff"), (1, "#2aa0c0")], cx - 5, cy - 50, cx + 5, cy - 34), stroke=OUTLINE, stroke_width=1.4)
    # hood runic trim
    d.path(smooth([(cx - 72, 170), (cx - 64, 96), (cx - 46, 48), (cx, 28), (cx + 46, 48), (cx + 64, 96), (cx + 72, 170)], closed=False), stroke=STEEL["base"], sw=2.2)
    # floating aether crystal
    fx, fy = 206, 176
    d.circle(fx, fy, 22, fill=d.rad([(0, AE_C, 0.5), (1, AE_C, 0)], fx, fy, 22))
    cr = [(fx, fy - 16), (fx + 7, fy - 3), (fx + 5, fy + 10), (fx, fy + 16), (fx - 5, fy + 10), (fx - 7, fy - 3)]
    d.path(poly(cr), stroke=OUTLINE, sw=3.4)
    d.path(poly(cr), fill=d.lin([(0, "#ffffff"), (0.5, AE_C), (1, "#1a6a8a")], fx - 7, fy - 16, fx + 7, fy + 16))
    d.path(f"M{fx},{fy - 16} L{fx - 1},{fy + 16}", stroke="#ffffff", sw=0.9, op=0.7)
    frame(d, dict(dark="#2a3048", base="#9aa8c8", light="#f0f4ff"))


# ------------------------------------------------------------------------------------------ NPCs

@portrait
def blacksmith(d):
    background(d, "#4a2008", haze="#ff6a14", haze2="#b83a0a", motes="#ffb040", seed=7)
    vignette(d)
    cx, cy = 128, 112
    # broad torso: rough tunic + leather apron
    shoulders(d, dict(dark="#2a1a10", base="#6a4a34", light="#a88460"), top=178, spread=1.1, neck_w=44)
    apron = [(92, 196), (164, 196), (178, 256), (78, 256)]
    d.path(poly(apron), stroke=OUTLINE, sw=4)
    d.path(poly(apron), fill=d.lin([(0, "#8a5a34"), (0.5, "#5a361c"), (1, "#2a160a")], 92, 196, 164, 256))
    for sx in (-1, 1):
        d.path(f"M{128 + sx * 34},198 L{128 + sx * 58},178", stroke=OUTLINE, sw=7)
        d.path(f"M{128 + sx * 34},198 L{128 + sx * 58},178", stroke="#5a361c", sw=4.4)
        d.circle(128 + sx * 34, 199, 4, fill=d.rad([(0, "#d8d8d8"), (1, "#4a4a4a")], 128 + sx * 34 - 1, 197, 5), stroke=OUTLINE, stroke_width=1.2)
    d.path("M104,226 L124,224", stroke="#2a160a", sw=1.4)
    for (x, y, r) in ((110, 238, 6), (150, 218, 5), (96, 210, 4)):   # soot / scorch
        d.circle(x, y, r, fill="#1a0e08", opacity=0.45)
    neck(d, cx, cy + 40, 44, 30, SKIN_TAN)
    head(d, cx, cy, SKIN_TAN, w=1.08, jaw=1.12, chin=1.2, top=0.95)
    ears(d, cx, cy, SKIN_TAN, w=1.08)
    # bald crown with short side hair + sweat sheen
    for sx in (-1, 1):
        d.path(smooth([(cx + sx * 38, cy - 26), (cx + sx * 44, cy - 6), (cx + sx * 42, cy + 8), (cx + sx * 36, cy - 8)], tension=0.5), fill="#1a100a", stroke=OUTLINE, stroke_width=1.6)
    d.path(smooth([(cx - 20, cy - 44), (cx - 6, cy - 50), (cx + 6, cy - 48)], closed=False), stroke="#ffffff", sw=3, op=0.35)
    brows(d, cx, cy - 16, "#1a100a", thick=6, angle=-1.5, w=14)
    eyes(d, cx, cy - 3, iris="#5a3a1a", spacing=18, w=10, h=4.0, squint=0.25)
    nose(d, cx, cy - 4, SKIN_TAN, L=22, w=9)
    # thick dark beard + mustache
    beard = smooth([(cx - 40, cy + 2), (cx - 32, cy + 34), (cx - 18, cy + 62), (cx, cy + 70), (cx + 18, cy + 62), (cx + 32, cy + 34), (cx + 40, cy + 2),
                    (cx + 30, cy + 22), (cx + 14, cy + 24), (cx, cy + 20), (cx - 14, cy + 24), (cx - 30, cy + 22)], tension=0.45)
    d.path(beard, stroke=OUTLINE, sw=4.4)
    d.path(beard, fill=d.lin([(0, "#4a3020"), (0.5, "#2a180e"), (1, "#140a06")], cx - 40, cy, cx + 40, cy + 70))
    for i in range(9):
        x = cx - 28 + i * 7
        d.path(f"M{x},{cy + 30} Q{x + 2},{cy + 46} {x - 1},{cy + 60 - abs(i - 4) * 3}", stroke="#6a4a30", sw=1.2, op=0.6)
    must = smooth([(cx - 24, cy + 30), (cx - 12, cy + 18), (cx, cy + 22), (cx + 12, cy + 18), (cx + 24, cy + 30), (cx + 10, cy + 27), (cx, cy + 28), (cx - 10, cy + 27)], tension=0.5)
    d.path(must, fill="#2a180e", stroke=OUTLINE, stroke_width=2)
    d.path(f"M{cx - 8},{cy + 34} Q{cx},{cy + 37} {cx + 8},{cy + 34}", stroke="#8a4030", sw=2.4)
    # soot smudges on face
    for (x, y, rx, ry, a) in ((cx - 24, cy - 34, 12, 3.5, -15), (cx + 26, cy + 10, 8, 3, 25)):
        with d.g(f"translate({x} {y}) rotate({a}) scale(1 {ry / rx:.3f})"):
            d.circle(0, 0, rx, fill=d.rad([(0, "#1a0e08", 0.35), (1, "#1a0e08", 0)], 0, 0, rx))
    frame(d, BRONZE, gem_col="#ff8a30")


@portrait
def merchant(d):
    background(d, "#1a3a34", haze="#d0a040", haze2="#2a8a7a", seed=11)
    vignette(d)
    cx, cy = 128, 118
    cloak = dict(dark="#1a1408", base="#5a4a24", light="#9a8450")
    shoulders(d, cloak, top=186, spread=1.0)
    # scarf wrap
    sc = smooth([(88, 182), (128, 200), (168, 182), (176, 206), (128, 222), (80, 206)], tension=0.4)
    d.path(sc, stroke=OUTLINE, sw=4)
    d.path(sc, fill=d.lin([(0, "#e05a3a"), (1, "#6a1a10")], 80, 182, 176, 222))
    for i in range(5):
        d.path(f"M{96 + i * 16},{196 + (4 if i in (1, 3) else 0)} L{104 + i * 16},{206}", stroke="#ffd070", sw=1.4, op=0.7)
    # coin pouch strap
    d.path("M168,206 L196,256", stroke=OUTLINE, sw=8)
    d.path("M168,206 L196,256", stroke="#6a3e22", sw=5)
    hood_o = [(cx, 34), (cx + 50, 50), (cx + 66, 104), (cx + 70, 170), (cx + 46, 196), (cx - 46, 196), (cx - 70, 170), (cx - 66, 104), (cx - 50, 50)]
    hd = smooth(hood_o, tension=0.5)
    d.path(hd, stroke=OUTLINE, sw=6)
    d.path(hd, fill=d.lin([(0, cloak["light"]), (0.45, cloak["base"]), (1, cloak["dark"])], cx - 66, 40, cx + 66, 190))
    op_ = smooth([(cx, 54), (cx + 42, 74), (cx + 50, 130), (cx + 40, 182), (cx - 40, 182), (cx - 50, 130), (cx - 42, 74)], tension=0.5)
    d.path(op_, fill="#0a0806")
    neck(d, cx, cy + 42, 28, 26, SKIN)
    head(d, cx, cy, SKIN, w=0.92, jaw=0.95, chin=0.9)
    ears(d, cx, cy + 2, SKIN, w=0.92, earring=True)
    # hood shadow band over the brow
    d.path(smooth([(cx - 50, cy - 26), (cx - 30, cy - 56), (cx, cy - 62), (cx + 30, cy - 56), (cx + 50, cy - 26), (cx + 30, cy - 40), (cx, cy - 44), (cx - 30, cy - 40)], tension=0.5), fill="#0a0806", op=0.75)
    brows(d, cx, cy - 16, "#3a2410", thick=3.6, angle=-2.5)
    eyes(d, cx, cy - 3, iris="#3a7a4a", spacing=16, w=10, h=4.0, squint=0.35)
    nose(d, cx, cy - 2, SKIN, L=21, w=8)
    # sly smile + trimmed goatee and thin mustache
    mouth(d, cx + 1, cy + 26, SKIN, w=12, smile=2.5)
    d.path(smooth([(cx - 16, cy + 22), (cx - 6, cy + 18), (cx, cy + 20), (cx + 6, cy + 18), (cx + 16, cy + 22)], closed=False), stroke="#3a2410", sw=2.6)
    goatee = smooth([(cx - 8, cy + 38), (cx + 8, cy + 38), (cx + 4, cy + 54), (cx, cy + 58), (cx - 4, cy + 54)], tension=0.5)
    d.path(goatee, fill="#3a2410", stroke=OUTLINE, stroke_width=1.6)
    frame(d, GOLD, gem_col="#40d0a0")


@portrait
def elder(d):
    background(d, "#18323e", haze="#5ad0e0", haze2="#2a5a8a", motes=AE_C, seed=13)
    vignette(d)
    cx, cy = 128, 108
    robe = dict(dark="#2a3440", base="#8a98a8", light="#e0e8f0")
    shoulders(d, robe, top=182, spread=0.95)
    d.path(smooth([(96, 186), (128, 226), (160, 186)], closed=False), stroke=GOLD["base"], sw=3)
    neck(d, cx, cy + 40, 28, 30, SKIN_OLD)
    head(d, cx, cy, SKIN_OLD, w=0.95, jaw=0.9, chin=0.9, top=1.02)
    ears(d, cx, cy, SKIN_OLD, w=0.95)
    # wispy white hair at the sides + receding crown
    for sx in (-1, 1):
        wh = smooth([(cx + sx * 30, cy - 38), (cx + sx * 46, cy - 20), (cx + sx * 50, cy + 10), (cx + sx * 44, cy + 36), (cx + sx * 38, cy + 6), (cx + sx * 36, cy - 20)], tension=0.5)
        d.path(wh, fill="#e8eef4", stroke=OUTLINE, stroke_width=2)
        d.path(smooth([(cx + sx * 34, cy - 30), (cx + sx * 44, cy - 6), (cx + sx * 42, cy + 24)], closed=False), stroke="#9aa8b8", sw=1.2)
    # forehead wrinkles
    for k in range(3):
        y = cy - 38 + k * 6
        d.path(f"M{cx - 20 + k * 2},{y} Q{cx},{y - 3} {cx + 20 - k * 2},{y}", stroke=SKIN_OLD["shade"], sw=1.2, op=0.5)
    brows(d, cx, cy - 16, "#f0f4f8", thick=5, angle=2.5, w=15)
    eyes(d, cx, cy - 3, glow=AE_C, spacing=17, w=10, h=3.8, age=2)
    nose(d, cx, cy - 4, SKIN_OLD, L=24, w=9)
    # long white beard + mustache
    beard = smooth([(cx - 40, cy + 4), (cx - 36, cy + 40), (cx - 26, cy + 80), (cx - 10, cy + 118), (cx, cy + 128), (cx + 10, cy + 118), (cx + 26, cy + 80),
                    (cx + 36, cy + 40), (cx + 40, cy + 4), (cx + 28, cy + 24), (cx + 10, cy + 26), (cx, cy + 22), (cx - 10, cy + 26), (cx - 28, cy + 24)], tension=0.45)
    d.path(beard, stroke=OUTLINE, sw=4.4)
    d.path(beard, fill=d.lin([(0, "#ffffff"), (0.5, "#dce4ec"), (1, "#8a98a8")], cx - 40, cy, cx + 40, cy + 128))
    for i in range(11):
        x = cx - 30 + i * 6
        d.path(f"M{x},{cy + 32} Q{x + 3},{cy + 70} {x + (i - 5) * 0.8},{cy + 110 - abs(i - 5) * 6}", stroke="#9aa8b8", sw=1.1, op=0.7)
    must = smooth([(cx - 30, cy + 34), (cx - 14, cy + 18), (cx, cy + 22), (cx + 14, cy + 18), (cx + 30, cy + 34), (cx + 12, cy + 28), (cx, cy + 30), (cx - 12, cy + 28)], tension=0.5)
    d.path(must, fill="#f4f8fc", stroke=OUTLINE, stroke_width=2)
    # aether light from below catching the beard
    d.circle(cx, 250, 70, fill=d.rad([(0, AE_C, 0.25), (1, AE_C, 0)], cx, 250, 70))
    frame(d, dict(dark="#2a3848", base="#a8b8c8", light="#f4f8ff"))


@portrait
def mystic(d):
    background(d, "#2a1446", haze="#9e73ff", haze2="#2ac0d0", motes=AE_C, seed=17)
    vignette(d)
    cx, cy = 128, 116
    cloth = dict(dark="#10081e", base="#3e2468", light="#8a64c8")
    teal = dict(dark="#06282c", base="#1a7a80", light="#6ad8d8")
    shoulders(d, cloth, top=186, spread=0.95)
    for i in range(7):
        x = 64 + i * 21
        d.path(poly(star_pts(x, 214 + 8 * math.sin(i), 4, 4, 1.2)), fill=AE_HI, op=0.8)
    # headdress / hood
    hood_o = [(cx, 22), (cx + 54, 40), (cx + 70, 100), (cx + 72, 176), (cx + 48, 196), (cx - 48, 196), (cx - 72, 176), (cx - 70, 100), (cx - 54, 40)]
    hd = smooth(hood_o, tension=0.5)
    d.path(hd, stroke=OUTLINE, sw=6)
    d.path(hd, fill=d.lin([(0, cloth["light"]), (0.45, cloth["base"]), (1, cloth["dark"])], cx - 70, 30, cx + 70, 190))
    d.path(smooth([(cx - 70, 170), (cx - 62, 96), (cx - 44, 46), (cx, 26), (cx + 44, 46), (cx + 62, 96), (cx + 70, 170)], closed=False), stroke=teal["light"], sw=3)
    op_ = smooth([(cx, 44), (cx + 44, 66), (cx + 52, 128), (cx + 40, 184), (cx - 40, 184), (cx - 52, 128), (cx - 44, 66)], tension=0.5)
    d.path(op_, fill="#07040e")
    neck(d, cx, cy + 42, 26, 28, SKIN_PALE)
    head(d, cx, cy, SKIN_PALE, w=0.88, jaw=0.88, chin=0.82)
    # dark hair parted
    for sx in (-1, 1):
        hp = smooth([(cx, cy - 54), (cx + sx * 30, cy - 50), (cx + sx * 40, cy - 22), (cx + sx * 38, cy + 20), (cx + sx * 30, cy - 10), (cx + sx * 12, cy - 38)], tension=0.5)
        d.path(hp, fill="#140a1e", stroke=OUTLINE, stroke_width=2)
    # brow sigil
    d.circle(cx, cy - 32, 16, fill=d.rad([(0, AE_C, 0.7), (1, AE_C, 0)], cx, cy - 32, 16))
    sig = f"M{cx},{cy - 42} L{cx},{cy - 22} M{cx - 7},{cy - 36} L{cx},{cy - 30} L{cx + 7},{cy - 36} M{cx - 5},{cy - 26} L{cx + 5},{cy - 26}"
    d.path(sig, stroke="#021018", sw=3.6)
    d.path(sig, stroke=AE_HI, sw=1.8)
    brows(d, cx, cy - 16, "#140a1e", thick=3, angle=1, w=12)
    eyes(d, cx, cy - 4, glow="#b890ff", spacing=15, w=10, h=4.0)
    # translucent veil over the lower face with beaded edge
    veil = smooth([(cx - 44, cy + 2), (cx - 20, cy + 6), (cx, cy + 4), (cx + 20, cy + 6), (cx + 44, cy + 2), (cx + 40, cy + 40), (cx + 20, cy + 70), (cx, cy + 76), (cx - 20, cy + 70), (cx - 40, cy + 40)], tension=0.45)
    d.path(veil, fill=d.lin([(0, teal["light"], 0.85), (1, teal["dark"], 0.95)], cx, cy, cx, cy + 76), stroke=OUTLINE, stroke_width=2.4)
    for x in (-20, -6, 8, 22):
        d.path(f"M{cx + x},{cy + 10} Q{cx + x * 1.1},{cy + 40} {cx + x * 0.8},{cy + 70}", stroke=teal["dark"], sw=1.4, op=0.6)
    d.path(smooth([(cx - 44, cy + 2), (cx - 20, cy + 6), (cx, cy + 4), (cx + 20, cy + 6), (cx + 44, cy + 2)], closed=False), stroke=GOLD["base"], sw=2.4)
    for i in range(9):
        x = cx - 40 + i * 10
        d.circle(x, cy + 5 + (1 if i % 2 else 0), 2, fill=GOLD["light"], stroke=OUTLINE, stroke_width=0.8)
    frame(d, dict(dark="#2a1a48", base="#9a80d0", light="#f0e8ff"), gem_col="#b890ff")


@portrait
def captain(d):
    background(d, "#142438", haze="#3a6ab0", haze2="#c8a040", seed=19)
    vignette(d)
    cx, cy = 128, 122
    steel = dict(dark="#2a303a", base="#9aa4b2", light="#f2f6fa")
    blue = dict(dark="#0a1636", base="#1e3c8a", light="#5a80d0")
    shoulders(d, blue, top=188, spread=1.02)
    for sx in (-1, 1):
        pp = smooth([(128 + sx * 40, 196), (128 + sx * 80, 188), (128 + sx * 112, 210), (128 + sx * 110, 240), (128 + sx * 70, 232)], tension=0.5)
        d.path(pp, stroke=OUTLINE, sw=5)
        d.path(pp, fill=d.lin([(0, steel["light"]), (1, steel["dark"])], 128 + sx * 40, 188, 128 + sx * 112, 240))
        d.path(smooth([(128 + sx * 50, 198), (128 + sx * 80, 192), (128 + sx * 106, 210)], closed=False), stroke=GOLD["base"], sw=2.4)
    d.path("M128,206 L120,216 L128,226 L136,216 Z", fill=GOLD["base"], stroke=OUTLINE, stroke_width=2)
    g = smooth([(96, 176), (160, 176), (168, 200), (88, 200)], tension=0.2)
    d.path(g, stroke=OUTLINE, sw=5)
    d.path(g, fill=d.lin([(0, steel["light"]), (1, steel["dark"])], 96, 176, 168, 200))
    neck(d, cx, cy + 40, 28, 20, SKIN)
    head(d, cx, cy, SKIN, w=0.95, jaw=1.02, chin=1.0)
    ears(d, cx, cy + 4, SKIN, w=0.95)
    brows(d, cx, cy - 14, "#3a2a1a", thick=5, angle=-2.5)
    eyes(d, cx, cy - 1, iris="#3a5a8a", spacing=17, w=10, h=4.0, squint=0.2)
    nose(d, cx, cy, SKIN, L=20, w=8)
    # stern mouth + heavy mustache
    d.path(f"M{cx - 10},{cy + 32} L{cx + 10},{cy + 32}", stroke=OUTLINE, sw=2.4)
    must = smooth([(cx - 28, cy + 36), (cx - 14, cy + 22), (cx, cy + 25), (cx + 14, cy + 22), (cx + 28, cy + 36), (cx + 12, cy + 30), (cx, cy + 30), (cx - 12, cy + 30)], tension=0.5)
    d.path(must, fill="#4a3220", stroke=OUTLINE, stroke_width=2)
    d.path(f"M{cx + 20},{cy - 6} L{cx + 30},{cy + 10}", stroke="#b0604a", sw=2, op=0.7)     # scar
    # open-faced plumed helm
    helm = smooth([(cx - 46, cy - 6), (cx - 46, cy - 40), (cx - 30, cy - 64), (cx, cy - 72), (cx + 30, cy - 64), (cx + 46, cy - 40), (cx + 46, cy - 6),
                   (cx + 40, cy + 10), (cx + 36, cy - 18), (cx, cy - 26), (cx - 36, cy - 18), (cx - 40, cy + 10)], tension=0.4)
    d.path(helm, stroke=OUTLINE, sw=6)
    d.path(helm, fill=d.lin([(0, steel["light"]), (0.35, steel["base"]), (1, steel["dark"])], cx - 46, 0, cx + 46, 0))
    d.path(smooth([(cx - 40, cy - 22), (cx, cy - 30), (cx + 40, cy - 22)], closed=False), stroke=GOLD["base"], sw=3)
    d.path(poly([(cx - 4, cy - 72), (cx + 4, cy - 72), (cx + 3, cy - 26), (cx - 3, cy - 26)]), fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], cx - 4, 0, cx + 4, 0), stroke=OUTLINE, stroke_width=1.4)
    d.path(smooth([(cx - 34, cy - 50), (cx - 18, cy - 64), (cx, cy - 68)], closed=False), stroke="#ffffff", sw=2.6, op=0.45)
    # plume
    pl = smooth([(cx - 2, cy - 70), (cx - 6, cy - 92), (cx + 14, cy - 110), (cx + 50, cy - 108), (cx + 70, cy - 92), (cx + 46, cy - 90), (cx + 20, cy - 84), (cx + 8, cy - 68)], tension=0.5)
    d.path(pl, stroke=OUTLINE, sw=4)
    d.path(pl, fill=d.lin([(0, "#ff7a7a"), (0.5, "#c01a2a"), (1, "#5a0610")], cx, cy - 110, cx + 70, cy - 70))
    for k in range(5):
        x = cx + 8 + k * 11
        d.path(f"M{x},{cy - 100 + k} Q{x + 6},{cy - 94} {x + 4},{cy - 86}", stroke="#5a0610", sw=1.2, op=0.8)
    frame(d, GOLD, gem_col="#5a90ff")


@portrait
def stranger(d):
    background(d, "#141418", haze="#3a3a44", haze2="#2a2a34", seed=23)
    vignette(d)
    cx, cy = 128, 118
    cloak = dict(dark="#060608", base="#1e1e24", light="#44444e")
    shoulders(d, cloak, top=184, spread=1.0)
    hood_o = [(cx, 26), (cx + 56, 44), (cx + 72, 104), (cx + 76, 176), (cx + 50, 200), (cx - 50, 200), (cx - 76, 176), (cx - 72, 104), (cx - 56, 44)]
    hd = smooth(hood_o, tension=0.5)
    d.path(hd, stroke=OUTLINE, sw=6)
    d.path(hd, fill=d.lin([(0, cloak["light"]), (0.45, cloak["base"]), (1, cloak["dark"])], cx - 72, 30, cx + 72, 190))
    for pts in (((cx - 30, 48), (cx - 50, 110), (cx - 58, 170)), ((cx + 34, 52), (cx + 54, 110), (cx + 60, 168))):
        d.path(smooth(pts, closed=False), stroke=cloak["dark"], sw=3, op=0.8)
    op_ = smooth([(cx, 50), (cx + 44, 72), (cx + 52, 130), (cx + 38, 186), (cx - 38, 186), (cx - 52, 130), (cx - 44, 72)], tension=0.5)
    d.path(op_, fill=d.rad([(0, "#0c0c10"), (1, "#000000")], cx, cy + 10, 70))
    # faint jaw silhouette + two dim eye glints
    for sx in (-1, 1):
        d.circle(cx + sx * 16, cy - 2, 7, fill=d.rad([(0, "#c8d0e0", 0.35), (1, "#c8d0e0", 0)], cx + sx * 16, cy - 2, 7))
        d.ellipse(cx + sx * 16, cy - 2, 3.4, 1.4, fill="#dce4f0", opacity=0.85)
    d.path(smooth([(cx - 40, 64), (cx - 20, 44), (cx, 38)], closed=False), stroke="#6a6a78", sw=2, op=0.5)
    frame(d, dict(dark="#1e1e24", base="#6a6a74", light="#c0c0cc"), gem_col="#9aa0b0")
