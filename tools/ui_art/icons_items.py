"""Item icons: transparent background, painted object with a soft contact shadow."""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, EL, STEEL, CRIMSON, GOLD, BRONZE, INDIGO, ARCANE, LEATHER, WOOD, BONE, LINEN, CLOTH_RED, OUTLINE,
                    f, poly, smooth, mix, lt, dk, ribbon, taper, arc_pts, bez, qbez, star_pts, ngon, jag_line, blob, teardrop,
                    polar, faceted, rrect_path, circle_path, lerp)
from bh_shapes import (T, sword, greatsword, dagger, axe, spear, bow, staff, wand, heater_shield, great_helm, cuirass, crystal,
                       gem, rock, motes, arrow, smooth_pts)

ITEMS = {}
BRIGHT_STEEL = dict(dark="#3a4250", base="#b4bfcc", light="#ffffff", glow="#e8f0ff")
ROBE = dict(dark="#120e36", base="#34288a", light="#7a6ad8")
EMERALD = dict(dark="#063a1a", base="#1aa04a", light="#b0ffc8")
RUBY = dict(dark="#4a0410", base="#d0182e", light="#ffb0b8")
SAPPHIRE = dict(dark="#061a4a", base="#2a6ae8", light="#c8e4ff")


def item(shadow=(64, 116, 40, 7)):
    def deco(fn):
        def build():
            d = Doc(name="it_" + fn.__name__)
            if shadow:
                cx, cy, rx, ry = shadow
                with d.g(f"translate({f(cx)} {f(cy)}) scale(1 {f(ry / rx)})"):
                    d.circle(0, 0, rx, fill=d.rad([(0, "#000000", 0.55), (0.6, "#000000", 0.25), (1, "#000000", 0)], 0, 0, rx))
            fn(d)
            return d
        ITEMS[fn.__name__] = build
        return fn
    return deco


# ------------------------------------------------------------------------------------------ weapons

@item(shadow=(60, 116, 44, 6))
def sword(d):
    from bh_shapes import sword as _sword
    with d.g(T(42, 86, 45, 1.12)):
        _sword(d, L=70, W=13, pal=BRIGHT_STEEL)


@item(shadow=(60, 118, 48, 6))
def greatsword(d):
    from bh_shapes import greatsword as _gs
    with d.g(T(38, 90, 45, 0.98)):
        _gs(d, L=104, W=20, pal=BRIGHT_STEEL)


@item(shadow=(58, 118, 40, 6))
def axe(d):
    from bh_shapes import axe as _axe
    with d.g(T(74, 34, 35, 1.12)):
        _axe(d, H=84)


@item(shadow=(60, 118, 46, 6))
def spear(d):
    from bh_shapes import spear as _spear
    with d.g(T(86, 42, 45, 1.0)):
        _spear(d, H=116, W=7.5, head_w=17)


@item(shadow=(60, 112, 32, 6))
def dagger(d):
    from bh_shapes import dagger as _dagger
    with d.g(T(50, 80, 45, 1.75)):
        _dagger(d, L=40, W=10)


@item(shadow=(64, 118, 40, 6))
def bow(d):
    from bh_shapes import bow as _bow
    with d.g(T(60, 64, 40, 1.12)):
        _bow(d, H=104, limb=10)
    with d.g(T(26, 104, 45, 1.0)):
        arrow(d, L=100)


@item(shadow=(56, 120, 40, 6))
def staff(d):
    from bh_shapes import staff as _staff
    with d.g(T(86, 28, 32, 1.12)):
        _staff(d, H=94, thick=9, crystal_r=9.5)


@item(shadow=(56, 114, 34, 6))
def wand(d):
    from bh_shapes import wand as _wand
    with d.g(T(82, 34, 40, 1.5)):
        _wand(d, H=60, thick=1.5)
    d.sparkle(98, 20, 6, "#ffffff", 0.95, glow_color="#a060ff")


# ------------------------------------------------------------------------------------------ armour

@item(shadow=(64, 120, 36, 6))
def shield(d):
    with d.g(T(64, 62, 0, 1.4)):
        heater_shield(d, w=66, h=78, field=CRIMSON, rim=STEEL, emblem="cross", boss=GOLD)


@item(shadow=(64, 112, 36, 6))
def helm_plate(d):
    with d.g(T(64, 66, 0, 1.45)):
        great_helm(d, w=46, h=56, pal=STEEL, trim=GOLD)


@item(shadow=(64, 118, 44, 6))
def helm_hood(d):
    c = dict(dark="#0e1a14", base="#2a4a36", light="#6a9a78")
    outer = [(0, -56), (14, -48), (28, -26), (34, 4), (46, 30), (52, 46), (30, 52), (0, 48), (-30, 52), (-52, 46), (-46, 30), (-34, 4),
             (-28, -26), (-14, -48)]
    with d.g(T(64, 64, 0, 1.0)):
        dd = smooth(outer, tension=0.5)
        d.path(dd, stroke=OUTLINE, sw=5)
        d.path(dd, fill=d.lin([(0, c["light"]), (0.45, c["base"]), (1, c["dark"])], -52, -40, 52, 40))
        # fold lines
        for pts in (((-8, -44), (-18, -20), (-22, 10)), ((10, -40), (18, -10), (24, 20)), ((-36, 30), (-26, 44)), ((34, 28), (28, 46))):
            d.path(smooth(pts, closed=False), stroke=c["dark"], sw=2.2, op=0.8)
            d.path(smooth([(x - 1.5, y) for x, y in pts], closed=False), stroke=c["light"], sw=0.8, op=0.4)
        # face opening
        face = [(0, -34), (16, -24), (20, 0), (12, 22), (0, 28), (-12, 22), (-20, 0), (-16, -24)]
        fd = smooth(face, tension=0.6)
        d.path(fd, stroke=GOLD["base"], sw=5)
        d.path(fd, stroke=GOLD["light"], sw=1.2, op=0.8)
        d.path(fd, fill=d.rad([(0, "#000000"), (0.7, "#05040a"), (1, "#1a2a20")], 0, 4, 26))
        # capelet clasp
        d.circle(0, 40, 5, fill=d.rad([(0, GOLD["light"]), (1, GOLD["dark"])], -1, 38, 6), stroke=OUTLINE, stroke_width=1.6)
        d.path(smooth([(-24, -20), (-10, -46), (0, -54)], closed=False), stroke="#ffffff", sw=1.4, op=0.3)


@item(shadow=(64, 120, 44, 6))
def inner_garment(d):
    c = LINEN
    body = [(-14, -44), (14, -44), (30, -38), (46, -24), (54, 14), (44, 18), (34, -8), (32, 42), (0, 46), (-32, 42), (-34, -8),
            (-44, 18), (-54, 14), (-46, -24), (-30, -38)]
    with d.g(T(64, 66, 0, 1.0)):
        dd = poly(body)
        d.path(dd, stroke=OUTLINE, sw=5)
        d.path(dd, fill=d.lin([(0, c["light"]), (0.5, c["base"]), (1, c["dark"])], -54, 0, 54, 0))
        # quilting: diamond stitching
        segs = []
        for k in range(-12, 13):
            x0 = k * 9
            for sgn in (1, -1):
                for i in range(40):
                    t0, t1 = i / 40, (i + 0.55) / 40
                    a = (x0 - sgn * 45 + sgn * 90 * t0, -45 + 90 * t0)
                    b = (x0 - sgn * 45 + sgn * 90 * t1, -45 + 90 * t1)
                    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                    if inside(m, body) and inside(a, body) and inside(b, body):
                        segs.append(f"M{f(a[0])},{f(a[1])} L{f(b[0])},{f(b[1])}")
        d.path(" ".join(segs), stroke=c["dark"], sw=1.0, op=0.5)
        # clean the stitching off the outside by redrawing the silhouette edge and background-colour sleeves gaps
        # standing collar
        col = rrect_path(-15, -52, 30, 11, 3)
        d.path(col, stroke=OUTLINE, sw=4)
        d.path(col, fill=d.lin([(0, lt(c["base"], 0.2)), (1, c["dark"])], 0, -52, 0, -41))
        # front opening with lacing
        d.path("M0,-41 L0,46", stroke=OUTLINE, sw=2.4)
        for y in range(-36, 40, 9):
            d.path(f"M-5,{y} L5,{y + 6} M5,{y} L-5,{y + 6}", stroke=CLOTH_RED["base"], sw=1.6)
            d.circle(-5, y, 1.2, fill="#2a1a0a")
            d.circle(5, y, 1.2, fill="#2a1a0a")
        # hem and cuffs
        d.path("M-32,40 L0,44 L32,40", stroke=c["dark"], sw=3)
        d.path("M-54,14 L-44,18 M54,14 L44,18", stroke=c["dark"], sw=3)
        d.path(dd, stroke=OUTLINE, sw=2.4)


@item(shadow=(64, 116, 40, 6))
def armor_plate(d):
    with d.g(T(64, 64, 0, 1.45)):
        cuirass(d, w=66, h=66, pal=STEEL, trim=GOLD)


@item(shadow=(64, 120, 44, 6))
def armor_robe(d):
    c = ROBE
    with d.g(T(64, 64, 0, 1.0)):
        for s in (-1, 1):
            sl = [(s * 22, -44), (s * 40, -26), (s * 54, 20), (s * 36, 26), (s * 28, -6)]
            sd = smooth(sl, tension=0.4)
            d.path(sd, stroke=OUTLINE, sw=5)
            d.path(sd, fill=d.lin([(0, c["light"]), (1, c["dark"])], s * 22, -40, s * 54, 20))
            d.path(poly([(s * 54, 20), (s * 36, 26)], closed=False), stroke=GOLD["base"], sw=3)
        body = [(-12, -50), (12, -50), (24, -44), (28, -6), (36, 52), (0, 56), (-36, 52), (-28, -6), (-24, -44)]
        bd = smooth(body, tension=0.3)
        d.path(bd, stroke=OUTLINE, sw=5)
        d.path(bd, fill=d.lin([(0, c["light"]), (0.45, c["base"]), (1, c["dark"])], -36, 0, 36, 0))
        # folds
        for x in (-18, -8, 10, 20):
            d.path(smooth([(x * 0.6, 4), (x * 0.9, 30), (x * 1.1, 52)], closed=False), stroke=c["dark"], sw=2, op=0.7)
        # V collar + centre trim
        d.path("M-12,-50 L0,-28 L12,-50 Z", fill="#07051a", stroke=OUTLINE, stroke_width=1.4)
        d.path("M-13,-49 L0,-26 L13,-49", stroke=GOLD["base"], sw=3)
        d.path("M0,-26 L0,55", stroke=GOLD["base"], sw=3.4)
        d.path("M0,-26 L0,55", stroke=GOLD["light"], sw=1)
        # sash belt
        d.path(rrect_path(-28, -6, 56, 8, 2), fill=d.lin([(0, CLOTH_RED["light"]), (1, CLOTH_RED["dark"])], 0, -6, 0, 2), stroke=OUTLINE, stroke_width=1.6)
        d.path("M6,2 L10,26 L4,24 L2,2 Z", fill=CLOTH_RED["base"], stroke=OUTLINE, stroke_width=1.2)
        d.circle(0, -2, 4, fill=d.rad([(0, "#e0c4ff"), (1, "#5a2ab0")], -1, -3, 5), stroke=OUTLINE, stroke_width=1.2)
        d.path("M-36,52 Q0,58 36,52", stroke=GOLD["base"], sw=3)
        # arcane rune on the hem
        d.path(poly(star_pts(-18, 40, 4, 5, 1.5)), fill="#c8a8ff", op=0.8)
        d.path(poly(star_pts(18, 40, 4, 5, 1.5)), fill="#c8a8ff", op=0.8)


def glove(d: Doc, pal, trim, plated=True):
    """Upright glove, palm facing viewer; local ~ x[-34,24] y[-48,46]."""
    fingers = [(-13.5, -40), (-4.5, -46), (4.5, -44), (13.5, -36)]
    for i, (x, top) in enumerate(fingers):
        fd = rrect_path(x - 4.4, top, 8.8, 44 + top * -0.1 + 10, 4.2)
        d.path(fd, stroke=OUTLINE, sw=4)
        d.path(fd, fill=d.lin([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], x - 4.4, 0, x + 4.4, 0))
        if plated:
            for k in range(1, 4):
                y = top + k * 9
                d.path(f"M{f(x - 4.2)},{f(y)} Q{f(x)},{f(y + 2.5)} {f(x + 4.2)},{f(y)}", stroke=OUTLINE, sw=1.2)
            d.path(f"M{f(x - 2)},{f(top + 2)} L{f(x - 2)},{f(top + 24)}", stroke="#ffffff", sw=0.9, op=0.5)
        else:
            d.path(f"M{f(x + 2.6)},{f(top + 4)} L{f(x + 2.6)},{f(top + 28)}", stroke=pal["dark"], sw=0.8, op=0.8, stroke_dasharray="2 1.6")
    # thumb
    th = [(-18, 8), (-26, -6), (-32, -18), (-26, -22), (-18, -10), (-10, -2)]
    tdd = smooth(th, tension=0.5)
    d.path(tdd, stroke=OUTLINE, sw=4)
    d.path(tdd, fill=d.lin([(0, pal["light"]), (1, pal["dark"])], -32, -20, -10, 8))
    if plated:
        d.path("M-29,-14 L-22,-18 M-24,-4 L-17,-9", stroke=OUTLINE, sw=1.2)
    # palm / back plate
    palm = [(-18, -12), (18, -12), (19, 22), (-19, 22)]
    pd = smooth(palm, tension=0.2)
    d.path(pd, stroke=OUTLINE, sw=4.4)
    d.path(pd, fill=d.lin([(0, pal["light"]), (0.45, pal["base"]), (1, pal["dark"])], -18, -12, 18, 22))
    if plated:
        d.path("M-17,-2 Q0,2 17,-2 M-18,8 Q0,12 18,8", stroke=OUTLINE, sw=1.4)
        for x in (-12, -4, 4, 12):
            d.circle(x, -8, 1.6, fill=trim["light"], stroke=OUTLINE, stroke_width=0.6)
    else:
        d.path("M-18,4 L18,10 M-18,12 L18,4", stroke=LINEN["light"], sw=3, op=0.85)
    # flared cuff
    cuff = [(-19, 20), (19, 20), (26, 46), (-26, 46)]
    cd = poly(cuff)
    d.path(cd, stroke=OUTLINE, sw=4.4)
    d.path(cd, fill=d.lin([(0, pal["light"]), (0.4, pal["base"]), (1, pal["dark"])], -26, 0, 26, 0))
    d.path("M-20,24 L20,24", stroke=trim["base"], sw=3)
    d.path("M-24,40 L24,40", stroke=trim["base"], sw=2.4 if plated else 1.4)
    if not plated:
        d.path("M-22,30 L22,30", stroke=pal["dark"], sw=0.9, stroke_dasharray="2 1.6")


@item(shadow=(64, 118, 34, 6))
def gloves_plate(d):
    with d.g(T(66, 64, -8, 1.12)):
        glove(d, STEEL, GOLD, plated=True)


@item(shadow=(64, 118, 34, 6))
def gloves_cloth(d):
    with d.g(T(66, 64, -8, 1.12)):
        glove(d, LEATHER, dict(dark="#2a1a0a", base="#8a6a3a", light="#d8b880"), plated=False)


def boot(d: Doc, pal, trim, plated=True):
    """Side-profile boot facing right; local ~ x[-24,40] y[-48,32]."""
    pts = [(-16, -46), (12, -46), (12, -6), (24, 4), (36, 12), (40, 22), (40, 28), (-20, 28), (-22, 12), (-18, -6)]
    dd = smooth(pts, tension=0.25)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, pal["light"]), (0.45, pal["base"]), (1, pal["dark"])], -20, -46, 30, 28))
    # sole
    d.path(poly([(-21, 24), (41, 24), (40, 31), (-20, 31)]), fill="#1a100a", stroke=OUTLINE, stroke_width=1.6)
    d.path("M-20,31 L-8,31 L-8,24", fill="none", stroke=OUTLINE, sw=1)
    if plated:
        # sabaton lames
        for k in range(4):
            x = 14 + k * 6
            d.path(f"M{f(x - 3)},{f(-2 + k * 3)} Q{f(x + 2)},{f(10 + k * 2)} {f(x + 1)},{f(22)}", stroke=OUTLINE, sw=1.4)
        # greave ridge + knee flare
        d.path("M-2,-46 L-2,-4", stroke="#ffffff", sw=1.4, op=0.45)
        d.path("M2,-46 L2,-4", stroke=pal["dark"], sw=1.2, op=0.7)
        flare = [(-20, -50), (16, -50), (18, -40), (-22, -40)]
        d.shape(poly(flare), fill=d.lin([(0, trim["light"]), (1, trim["dark"])], 0, -50, 0, -40), ow=2)
        d.path("M-18,-8 L12,-8", stroke=trim["base"], sw=2.4)
        for y in (-30, -18):
            d.circle(-12, y, 1.6, fill=trim["light"], stroke=OUTLINE, stroke_width=0.6)
    else:
        # fold-over cuff and cloth wraps
        cuff = [(-20, -50), (16, -50), (15, -34), (-19, -34)]
        d.shape(smooth(cuff, tension=0.2), fill=d.lin([(0, lt(pal["base"], 0.25)), (1, pal["dark"])], 0, -50, 0, -34), ow=2)
        for y in (-26, -18, -10):
            d.path(f"M-18,{y + 4} L12,{y - 2}", stroke=LINEN["base"], sw=4)
            d.path(f"M-18,{y + 4} L12,{y - 2}", stroke=LINEN["light"], sw=1.2, op=0.7)
        d.path("M14,-2 Q24,8 38,16", stroke=pal["dark"], sw=1, stroke_dasharray="2 1.6")
        d.path("M-19,16 L38,20", stroke=pal["dark"], sw=1, stroke_dasharray="2 1.6")


@item(shadow=(66, 112, 38, 6))
def boots_plate(d):
    with d.g(T(58, 72, 0, 1.3)):
        boot(d, STEEL, GOLD, plated=True)


@item(shadow=(66, 112, 38, 6))
def boots_cloth(d):
    with d.g(T(58, 72, 0, 1.3)):
        boot(d, LEATHER, GOLD, plated=False)


# ------------------------------------------------------------------------------------------ jewellery

@item(shadow=(64, 112, 44, 6))
def ring(d):
    with d.g("translate(64 64) scale(1.22) translate(-64 -64)"):
        _ring(d)


def _ring(d):
    cx, cy = 64, 76
    g = GOLD
    # band thickness (back layer)
    d.path(circle_path(cx, cy + 6, 36, 20) + " " + circle_path(cx, cy + 6, 27, 13), fill=g["dark"], fill_rule="evenodd", stroke=OUTLINE, stroke_width=2.4)
    band = circle_path(cx, cy, 36, 20) + " " + circle_path(cx, cy, 27, 13)
    d.path(band, fill=d.lin([(0, g["light"]), (0.35, g["base"]), (0.7, g["dark"]), (1, g["base"])], cx - 36, cy - 20, cx + 36, cy + 20), fill_rule="evenodd", stroke=OUTLINE, stroke_width=2.4)
    d.path(smooth(arc_pts(cx, cy, 32, math.radians(150), math.radians(230), 8, ry=17), closed=False), stroke="#ffffff", sw=2, op=0.6)
    # setting + prongs
    d.glow(cx, cy - 26, 26, "#ff4050", 0.5)
    d.path(poly([(cx - 16, cy - 16), (cx + 16, cy - 16), (cx + 10, cy - 8), (cx - 10, cy - 8)]), fill=d.lin([(0, g["light"]), (1, g["dark"])], 0, cy - 16, 0, cy - 8), stroke=OUTLINE, stroke_width=1.8)
    gem(d, cx, cy - 28, 15, RUBY, sides=8)
    for s in (-1, 1):
        for dx in (6, 13):
            d.path(poly([(cx + s * dx, cy - 14), (cx + s * (dx + 1), cy - 22), (cx + s * (dx - 1.5), cy - 20)]), fill=g["light"], stroke=OUTLINE, stroke_width=1)


@item(shadow=None)
def amulet(d):
    g = GOLD
    # chain
    for side in (-1, 1):
        pts = qbez((64 + side * 44, 8), (64 + side * 40, 56), (64 + side * 8, 60), n=16)
        for i, (x, y) in enumerate(pts):
            d.ellipse(x, y, 3.2, 2.2, stroke=OUTLINE, stroke_width=3.2)
            d.ellipse(x, y, 3.2, 2.2, stroke=g["base"] if i % 2 else g["light"], stroke_width=1.5)
    # bail
    d.shape(rrect_path(59, 56, 10, 12, 3), fill=d.lin([(0, g["light"]), (1, g["dark"])], 59, 0, 69, 0), ow=1.8)
    # ornate setting
    cx, cy = 64, 88
    petals = star_pts(cx, cy, 8, 28, 22, rot0=-math.pi / 2 + math.pi / 8)
    d.path(smooth(petals, tension=0.6), stroke=OUTLINE, sw=4.4)
    d.path(smooth(petals, tension=0.6), fill=d.lin([(0, g["light"]), (0.5, g["base"]), (1, g["dark"])], cx - 28, cy - 28, cx + 28, cy + 28))
    d.circle(cx, cy, 19, stroke=g["dark"], stroke_width=1.6)
    for i in range(8):
        x, y = polar(cx, cy, 24, -math.pi / 2 + i * math.pi / 4 + math.pi / 8)
        d.circle(x, y, 1.6, fill=g["light"])
    d.glow(cx, cy, 26, "#4a8aff", 0.5)
    gem(d, cx, cy, 15, SAPPHIRE, sides=10)
    # drop
    d.path(teardrop(cx, cy + 36, 5, -14), fill=d.rad([(0, SAPPHIRE["light"]), (1, SAPPHIRE["dark"])], cx - 1, cy + 34, 7), stroke=OUTLINE, stroke_width=1.8)


@item(shadow=None)
def charm(d):
    # cord loop
    d.path("M64,6 C40,6 44,40 58,52 M64,6 C88,6 84,40 70,52", stroke=OUTLINE, sw=4.6)
    d.path("M64,6 C40,6 44,40 58,52 M64,6 C88,6 84,40 70,52", stroke=LEATHER["light"], sw=2)
    # beads
    for i, (x, y) in enumerate(((50, 34), (78, 34), (56, 48), (72, 48))):
        col = [CRIMSON, EMERALD, EMERALD, CRIMSON][i]
        d.circle(x, y, 4.2, fill=d.rad([(0, col["light"]), (1, col["dark"])], x - 1, y - 1.5, 5), stroke=OUTLINE, stroke_width=1.6)
    # hanging feather
    from icons_badges import feather
    with d.g(T(88, 70, -150, 0.7)):
        feather(d, L=60, W=16, pal=dict(dark="#3a2410", base="#b07a40", light="#f8e0b8"))
    # carved bone disc with rune
    cx, cy = 62, 80
    d.circle(cx, cy, 26, fill=OUTLINE)
    d.circle(cx, cy, 23.6, fill=d.rad([(0, BONE["light"]), (0.6, BONE["base"]), (1, BONE["dark"])], cx - 8, cy - 8, 32))
    d.circle(cx, cy, 18, stroke=BONE["dark"], stroke_width=1.4)
    rune = "M%s,%s L%s,%s M%s,%s L%s,%s L%s,%s M%s,%s L%s,%s" % (
        f(cx), f(cy - 13), f(cx), f(cy + 13), f(cx - 9), f(cy - 6), f(cx), f(cy + 2), f(cx + 9), f(cy - 6), f(cx - 8), f(cy + 8), f(cx + 8), f(cy + 8))
    d.path(rune, stroke="#3a1a0a", sw=3.4)
    d.path(rune, stroke="#ff7a3a", sw=1.3, op=0.9)
    d.circle(cx, cy - 24, 3.6, fill="#1a0e06")


# ------------------------------------------------------------------------------------------ consumables

def inside(p, poly_pts):
    x, y = p
    n = len(poly_pts)
    c = False
    for i in range(n):
        x1, y1 = poly_pts[i]
        x2, y2 = poly_pts[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            c = not c
    return c


def potion(d: Doc, liquid):
    cx, cy, r = 64, 80, 30
    d.glow(cx, cy, 44, liquid["glow"], 0.45)
    # glass back
    d.circle(cx, cy, r + 2.6, fill=OUTLINE)
    d.path(rrect_path(cx - 10.6, 28, 21.2, 30, 3), fill=OUTLINE)
    d.circle(cx, cy, r, fill=d.rad([(0, "#2a3040"), (1, "#0e1016")], cx, cy, r))
    d.path(rrect_path(cx - 8, 30, 16, 28, 2), fill="#1a1e28")
    # liquid (circle segment below the surface)
    yl = cy - 10
    dx = math.sqrt(r * r - (yl - cy) ** 2) - 1.2
    liq = f"M{f(cx - dx)},{f(yl)} A{f(r - 1.2)},{f(r - 1.2)} 0 1 0 {f(cx + dx)},{f(yl)} Z"
    d.path(liq, fill=d.rad([(0, liquid["light"]), (0.5, liquid["base"]), (1, liquid["dark"])], cx - 6, cy + 2, r * 1.1))
    d.ellipse(cx, yl, dx, 3.6, fill=lt(liquid["base"], 0.3), stroke=liquid["light"], stroke_width=1)
    for (x, y, rr) in ((56, 94, 2.6), (70, 88, 1.8), (62, 102, 1.6), (74, 100, 2.2)):
        d.circle(x, y, rr, stroke=liquid["light"], stroke_width=1, opacity=0.8)
    # glass highlights
    d.path(smooth(arc_pts(cx, cy, r - 5, math.radians(200), math.radians(250), 6), closed=False), stroke="#ffffff", sw=4, op=0.7)
    d.path(smooth(arc_pts(cx, cy, r - 5, math.radians(20), math.radians(50), 5), closed=False), stroke="#ffffff", sw=2, op=0.4)
    d.path(f"M{f(cx - 4)},34 L{f(cx - 4)},54", stroke="#ffffff", sw=2, op=0.5)
    # lip + cork + string
    d.path(rrect_path(cx - 12, 26, 24, 6, 3), fill=d.lin([(0, "#c0c8d8"), (1, "#4a5060")], 0, 26, 0, 32), stroke=OUTLINE, stroke_width=1.8)
    d.path(rrect_path(cx - 8, 12, 16, 16, 3), fill=d.lin([(0, "#d8a868"), (1, "#6a4020")], cx - 8, 0, cx + 8, 0), stroke=OUTLINE, stroke_width=2)
    d.path(f"M{f(cx - 11)},30 C{f(cx - 22)},34 {f(cx - 20)},46 {f(cx - 26)},52", stroke=OUTLINE, sw=3)
    d.path(f"M{f(cx - 11)},30 C{f(cx - 22)},34 {f(cx - 20)},46 {f(cx - 26)},52", stroke=LINEN["light"], sw=1.4)
    d.path(rrect_path(cx - 32, 50, 10, 13, 1.5), fill=LINEN["light"], stroke=OUTLINE, stroke_width=1.4)


@item(shadow=(64, 114, 32, 5))
def potion_health(d):
    potion(d, dict(dark="#4a0008", base="#d0162a", light="#ff9aa4", glow="#ff3048"))


@item(shadow=(64, 114, 32, 5))
def potion_mana(d):
    potion(d, dict(dark="#061a5a", base="#2a5ae8", light="#a8d0ff", glow="#3a7aff"))


# ------------------------------------------------------------------------------------------ materials

@item(shadow=(64, 108, 44, 7))
def mat_iron_shard(d):
    pal = dict(dark="#1e2228", base="#6a727e", light="#dfe6ee")
    shards = [((46, 74), [(30, 100), (38, 44), (52, 36), (60, 70), (56, 102)]),
              ((84, 76), [(70, 104), (74, 58), (92, 30), (100, 64), (96, 100)]),
              ((64, 94), [(48, 106), (58, 80), (74, 84), (84, 106)])]
    for c, pts in shards:
        faceted(d, pts, c, pal["dark"], pal["light"], ow=2.4, light_dir=(-0.7, -0.7))
    rng = random.Random(3)
    for i in range(10):
        x, y = rng.uniform(38, 96), rng.uniform(50, 100)
        d.circle(x, y, rng.uniform(1, 2.4), fill="#8a3a14", opacity=0.6)
    d.sparkle(52, 40, 6, "#ffffff", 0.95)
    d.sparkle(92, 34, 4, "#ffffff", 0.8)


@item(shadow=(64, 108, 44, 7))
def mat_arcane_dust(d):
    d.glow(64, 80, 50, "#a060ff", 0.7)
    mound = [(20, 104), (30, 88), (46, 74), (64, 66), (82, 74), (98, 88), (108, 104)]
    md = smooth(mound, closed=False, tension=0.6) + " Z"
    d.path(md, stroke=OUTLINE, sw=4)
    d.path(md, fill=d.lin([(0, "#e8d4ff"), (0.4, "#9a5ae8"), (1, "#3a1470")], 0, 66, 0, 104))
    rng = random.Random(5)
    for i in range(40):
        x = rng.uniform(26, 102)
        top = 104 - (38 * (1 - abs(x - 64) / 44))
        y = rng.uniform(top + 3, 102)
        d.circle(x, y, rng.uniform(0.7, 1.6), fill=rng.choice(["#ffffff", "#e0c8ff", "#5a2aa0"]), opacity=0.9)
    pts = [(rng.uniform(30, 98), rng.uniform(20, 64), rng.uniform(0.6, 1.2)) for _ in range(9)]
    motes(d, pts, "#f0e4ff", glow_color="#a060ff", size=2.2)
    d.sparkle(64, 42, 9, "#ffffff", 1.0, glow_color="#c090ff")
    d.sparkle(40, 58, 5, "#ffffff", 0.9)
    d.sparkle(90, 52, 5, "#ffffff", 0.9)


@item(shadow=(64, 108, 38, 7))
def mat_ember_core(d):
    cx, cy = 64, 68
    d.glow(cx, cy, 58, "#ff6a14", 0.8)
    rng = random.Random(9)
    pts = blob(cx, cy, 34, 10, 0.1, rng)
    faceted(d, pts, (cx - 6, cy - 8), "#140604", "#6a3020", ow=2.8)
    # molten fissures with glowing core
    cracks = [((cx, cy), (cx - 26, cy - 14)), ((cx, cy), (cx + 22, cy - 22)), ((cx, cy), (cx + 26, cy + 14)), ((cx, cy), (cx - 12, cy + 30)),
              ((cx - 12, cy - 6), (cx - 14, cy - 30))]
    for a, b in cracks:
        pp = jag_line(a, b, 4, 3, rng)
        d.path(poly(pp, closed=False), stroke="#ff5a10", sw=6, op=0.6)
        d.path(poly(pp, closed=False), stroke="#ffb040", sw=3)
        d.path(poly(pp, closed=False), stroke="#fff4c0", sw=1.2)
    d.glow(cx, cy, 16, "#fff0a0", 1.0, core="#ffffff")
    for (x, y) in ((40, 30), (92, 26), (100, 50), (30, 48)):
        d.circle(x, y, 1.8, fill="#ffc060")


@item(shadow=(64, 104, 44, 7))
def mat_bone_fragment(d):
    pal = BONE
    with d.g(T(68, 62, -35, 1.35)):
        # shaft ending in a jagged break on the right
        shaft = [(-30, -7), (10, -6), (18, -10), (22, -4), (28, -9), (32, 0), (26, 3), (30, 8), (14, 7), (-30, 7)]
        d.path(poly(shaft), stroke=OUTLINE, sw=5)
        # knuckle end (two condyles)
        for (x, y, r) in ((-38, -9, 11), (-38, 9, 11)):
            d.circle(x, y, r + 2.5, fill=OUTLINE)
        for (x, y, r) in ((-38, -9, 11), (-38, 9, 11)):
            d.circle(x, y, r, fill=d.rad([(0, pal["light"]), (0.6, pal["base"]), (1, pal["dark"])], x - 3, y - 4, r * 1.4))
        d.path(poly(shaft), fill=d.lin([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], 0, -8, 0, 8))
        d.path("M-26,-3 L12,-3", stroke="#ffffff", sw=1.6, op=0.6)
        d.path(poly([(18, -10), (22, -4), (28, -9), (32, 0), (26, 3), (30, 8), (24, 2), (20, 0)]), fill="#6a5a40", op=0.8)
        d.path("M-6,4 L2,5 M-16,-5 L-10,-4", stroke=pal["dark"], sw=1, op=0.7)
    # small splinter
    rng = random.Random(2)
    faceted(d, [(92, 100), (102, 92), (110, 98), (98, 106)], (100, 98), pal["dark"], pal["light"], ow=1.8)


def coin(d: Doc, x, y, r=13, tilt=0.42, g=GOLD):
    ry = r * tilt
    d.ellipse(x, y + 3, r, ry, fill=g["dark"], stroke=OUTLINE, stroke_width=2)
    d.path(f"M{f(x - r)},{f(y)} L{f(x - r)},{f(y + 3)} M{f(x + r)},{f(y)} L{f(x + r)},{f(y + 3)}", stroke=OUTLINE, sw=2)
    d.ellipse(x, y, r, ry, fill=d.lin([(0, g["light"]), (0.5, g["base"]), (1, g["dark"])], x - r, y - ry, x + r, y + ry), stroke=OUTLINE, stroke_width=2)
    d.ellipse(x, y, r * 0.7, ry * 0.7, stroke=g["dark"], stroke_width=1.2)
    d.path(f"M{f(x - r * 0.25)},{f(y)} L{f(x)},{f(y - ry * 0.4)} L{f(x + r * 0.25)},{f(y)} L{f(x)},{f(y + ry * 0.4)} Z", fill=g["light"])


@item(shadow=(64, 110, 50, 7))
def gold(d):
    d.glow(64, 80, 54, "#ffd070", 0.4)
    # heap
    heap = [(16, 106), (28, 88), (48, 76), (68, 72), (90, 80), (106, 92), (112, 106)]
    hd = smooth(heap, closed=False, tension=0.6) + " Z"
    d.path(hd, stroke=OUTLINE, sw=4)
    d.path(hd, fill=d.lin([(0, GOLD["light"]), (0.5, GOLD["base"]), (1, GOLD["dark"])], 0, 72, 0, 106))
    rng = random.Random(4)
    for i in range(14):
        x = rng.uniform(26, 104)
        top = 106 - 30 * (1 - abs(x - 66) / 46)
        y = rng.uniform(top + 4, 104)
        coin(d, x, y, r=rng.uniform(7, 9.5), tilt=0.4)
    # stacks
    for k in range(5):
        coin(d, 40, 86 - k * 6, r=13)
    for k in range(7):
        coin(d, 80, 82 - k * 6, r=13)
    coin(d, 62, 96, r=14, tilt=0.45)
    d.sparkle(84, 36, 7, "#ffffff", 0.95)
    d.sparkle(40, 58, 5, "#ffffff", 0.9)
