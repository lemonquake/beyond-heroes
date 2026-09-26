"""bh-002 item icons: tiered weapon/armour variants, set pieces, aether uniques, consumables, materials, quest items.

Same conventions as icons_items.py (128x128 viewBox, transparent background, soft contact shadow, dark outlines,
top-left light). Tier 2 = refined steel with gold engraving; tier 3 = runed ancient-tech steel with aether channels.
"""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, EL, STEEL, CRIMSON, GOLD, BRONZE, INDIGO, ARCANE, LEATHER, WOOD, BONE, LINEN, CLOTH_RED, OUTLINE,
                    f, poly, smooth, mix, lt, dk, ribbon, taper, arc_pts, bez, qbez, star_pts, ngon, jag_line, blob, teardrop,
                    polar, faceted, rrect_path, circle_path, lerp)
from bh_shapes import (T, sword, greatsword, dagger, axe, spear, bow, staff, wand, heater_shield, heater_pts, tower_shield,
                       great_helm, cuirass, crystal, gem, rock, motes, arrow, smooth_pts, snowflake, bolt, zig_bolt,
                       rune_ring, skull)
from icons_items import glove, boot, potion, coin, inside, SAPPHIRE, RUBY, EMERALD, ROBE, BRIGHT_STEEL

ITEMS2 = {}

REF = dict(dark="#2c3440", base="#c2cad6", light="#ffffff", glow="#e8f0ff")          # refined steel
RUNE = dict(dark="#0a0f16", base="#3a4a5c", light="#9ab8cc", glow="#7ff3ff")        # ancient-tech steel
DBRONZE = dict(dark="#24160a", base="#6a4a2a", light="#c89868")
WGOLD = dict(dark="#6a5630", base="#e6d6a8", light="#fffaf0")                        # white gold
SILVER = dict(dark="#3a4458", base="#a8b4c8", light="#f4f8ff")
AE = dict(dark="#0a4a5e", base="#62e0f4", light="#ffffff", glow="#7ff3ff")
AE_C = "#7ff3ff"
AE_HI = "#d8fdff"
MIDNIGHT = dict(dark="#060a24", base="#18206a", light="#4a5ac8")
EBONY = dict(dark="#120806", base="#3a2216", light="#8a5a3a")


def item(shadow=(64, 116, 40, 7)):
    def deco(fn):
        def build():
            d = Doc(name="it2_" + fn.__name__)
            if shadow:
                cx, cy, rx, ry = shadow
                with d.g(f"translate({f(cx)} {f(cy)}) scale(1 {f(ry / rx)})"):
                    d.circle(0, 0, rx, fill=d.rad([(0, "#000000", 0.55), (0.6, "#000000", 0.25), (1, "#000000", 0)], 0, 0, rx))
            fn(d)
            return d
        ITEMS2[fn.__name__] = build
        return fn
    return deco


# ------------------------------------------------------------------------------------------ overlay helpers

def inlay(d, pts, col=None, w=1.3, closed=False):
    col = col or GOLD
    p = smooth(pts, closed=closed) if len(pts) > 2 else poly(pts, closed=closed)
    d.path(p, stroke=dk(col["dark"], 0.3), sw=w + 1.0, op=0.8)
    d.path(p, stroke=col["light"], sw=w)


def aether_line(d, pts, w=2.0, core="#ffffff", col=AE_C, closed=False):
    p = smooth(pts, closed=closed) if len(pts) > 2 else poly(pts, closed=closed)
    d.path(p, stroke="#021018", sw=w + 1.6, op=0.9)
    d.glow_stroke(p, col, w * 1.3, op=0.55)
    d.path(p, stroke=col, sw=w)
    d.path(p, stroke=core, sw=max(0.5, w * 0.38))


def rune_ticks(d, p0, p1, n, s=2.4, col=AE_C, seed=1):
    rng = random.Random(seed)
    for i in range(n):
        t = (i + 0.5) / n
        x, y = lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t)
        k = rng.randint(0, 2)
        if k == 0:
            dd = f"M{f(x - s)},{f(y)} L{f(x + s)},{f(y)}"
        elif k == 1:
            dd = f"M{f(x - s)},{f(y - s * 0.6)} L{f(x)},{f(y + s * 0.6)} L{f(x + s)},{f(y - s * 0.6)}"
        else:
            dd = f"M{f(x - s)},{f(y + s * 0.5)} L{f(x + s)},{f(y - s * 0.5)} M{f(x)},{f(y - s * 0.7)} L{f(x)},{f(y + s * 0.7)}"
        d.path(dd, stroke=col, sw=0.9, op=0.95)


def aether_gem(d, x, y, r, glow=True):
    if glow:
        d.glow(x, y, r * 3.0, AE_C, 0.7)
    gem(d, x, y, r, dict(dark="#06506a", base="#40d0ea", light="#e8feff"), sides=6)


def scroll_curl(d, x, y, s=1.0, flip=1, col=GOLD):
    pts = [(x, y), (x + 3 * s * flip, y - 3 * s), (x + 6 * s * flip, y - 1 * s), (x + 5 * s * flip, y + 2 * s), (x + 3 * s * flip, y + 1 * s)]
    inlay(d, pts, col, w=0.9 * s)


def orbit(d, cx, cy, rx, ry, ang, col=AE_C, w=1.4, op=0.9):
    with d.g(f"translate({f(cx)} {f(cy)}) rotate({f(ang)})"):
        d.ellipse(0, 0, rx, ry, stroke=col, stroke_width=w * 2.4, opacity=op * 0.25)
        d.ellipse(0, 0, rx, ry, stroke=col, stroke_width=w, opacity=op)


# ------------------------------------------------------------------------------------------ swords

def _sword_refined(d, L, W, great=False):
    if great:
        greatsword(d, L=L, W=W, pal=REF, hilt=GOLD)
    else:
        sword(d, L=L, W=W, pal=REF, hilt=GOLD, guard_w=W * 3.5)
    sh = -L + W * (1.0 if great else 1.25)
    inlay(d, [(0, -W * (1.0 if great else 0.3)), (0, sh * 0.55)], GOLD, w=W * 0.12)
    for k in range(3):
        y = -W * 0.8 - k * W * 0.55
        scroll_curl(d, -W * 0.08, y, s=W * 0.09, flip=-1)
        scroll_curl(d, W * 0.08, y - W * 0.25, s=W * 0.09, flip=1)
    d.circle(0, 0, W * 0.2, fill=SAPPHIRE["base"], stroke=OUTLINE, stroke_width=0.9)
    d.circle(-W * 0.06, -W * 0.06, W * 0.07, fill="#ffffff", opacity=0.8)


def _sword_runed(d, L, W, great=False):
    if great:
        greatsword(d, L=L, W=W, pal=RUNE, hilt=DBRONZE)
    else:
        sword(d, L=L, W=W, pal=RUNE, hilt=DBRONZE, grip_pal=dict(dark="#06080c", base="#1a2230", light="#3a4a5c"), guard_w=W * 3.2)
    sh = -L + W * (1.0 if great else 1.25)
    aether_line(d, [(0, -W * (1.0 if great else 0.25)), (0, sh + W * 0.3)], w=W * 0.16)
    rune_ticks(d, (-W * 0.3, -W * 1.2), (-W * 0.3, sh * 0.8), 5, s=W * 0.12, seed=int(L))
    for sx in (-1, 1):
        d.path(poly([(sx * W * 0.5, -W * 0.5), (sx * W * 0.2, -W * 1.4)], closed=False), stroke=AE_C, sw=0.8, op=0.8)
    aether_gem(d, 0, 0, W * 0.24, glow=False)
    pom_y = W * (2.0 if great else 1.45) + W * (0.4 if great else 0.42) * 0.8
    d.glow(0, pom_y, W * 0.7, AE_C, 0.8)
    d.circle(0, pom_y, W * 0.18, fill=AE_HI)


@item(shadow=(60, 116, 44, 6))
def sword_2(d):
    with d.g(T(42, 86, 45, 1.12)):
        _sword_refined(d, 70, 13)


@item(shadow=(60, 116, 44, 6))
def sword_3(d):
    with d.g(T(42, 86, 45, 1.12)):
        _sword_runed(d, 72, 13)


@item(shadow=(60, 118, 48, 6))
def greatsword_2(d):
    with d.g(T(38, 90, 45, 0.98)):
        _sword_refined(d, 104, 20, great=True)


@item(shadow=(60, 118, 48, 6))
def greatsword_3(d):
    with d.g(T(38, 90, 45, 0.98)):
        _sword_runed(d, 106, 20, great=True)


@item(shadow=(58, 118, 40, 6))
def axe_2(d):
    with d.g(T(74, 34, 35, 1.12)):
        axe(d, H=84, pal=REF, wood=EBONY)
        inlay(d, [(-10, -8), (-18, -12), (-26, -8), (-26, 0), (-20, 4)], GOLD, w=1.3)
        inlay(d, [(-12, 2), (-16, 8), (-22, 10)], GOLD, w=1.0)
        d.circle(-19, -2, 2.2, fill=SAPPHIRE["base"], stroke=OUTLINE, stroke_width=0.8)


@item(shadow=(58, 118, 40, 6))
def axe_3(d):
    with d.g(T(74, 34, 35, 1.12)):
        axe(d, H=84, pal=RUNE, wood=dict(dark="#06080c", base="#1a2230", light="#3a4a5c"))
        aether_line(d, qbez((-12, -11), (-38, -9), (-34, 13), n=14), w=1.8)
        rune_ticks(d, (-10, -2), (-22, 4), 3, s=2.2, seed=5)
        d.glow(0, -2, 8, AE_C, 0.7)
        d.circle(0, -2, 2.2, fill=AE_HI)


@item(shadow=(60, 118, 46, 6))
def spear_2(d):
    with d.g(T(86, 42, 45, 1.0)):
        spear(d, H=116, W=7.5, head_w=17, pal=REF)
        L = 116 * 0.3
        inlay(d, [(0, -3), (0, -L * 0.62)], GOLD, w=1.4)
        for sx in (-1, 1):
            scroll_curl(d, sx * 2, -L * 0.3, s=1.2, flip=sx)
        d.path(poly([(0, -L * 0.75), (2.4, -L * 0.68), (0, -L * 0.61), (-2.4, -L * 0.68)]), fill=GOLD["light"], stroke=OUTLINE, stroke_width=0.6)


@item(shadow=(60, 118, 46, 6))
def spear_3(d):
    with d.g(T(86, 42, 45, 1.0)):
        spear(d, H=116, W=7.5, head_w=17, pal=RUNE)
        L = 116 * 0.3
        aether_line(d, [(0, -2), (0, -L * 0.82)], w=2.0)
        for sx in (-1, 1):
            d.path(poly([(sx * 3.5, -L * 0.2), (sx * 6.5, -L * 0.42)], closed=False), stroke=AE_C, sw=0.9)
        d.glow(0, 3, 8, AE_C, 0.7)


@item(shadow=(60, 112, 32, 6))
def dagger_2(d):
    with d.g(T(50, 80, 45, 1.75)):
        dagger(d, L=40, W=10, pal=REF, hilt=GOLD)
        inlay(d, [(0.5, -3), (-0.5, -14), (-1.5, -26)], GOLD, w=0.9)
        scroll_curl(d, 1, -8, s=0.7, flip=1)
        d.circle(0, 0, 1.8, fill=SAPPHIRE["base"], stroke=OUTLINE, stroke_width=0.5)


@item(shadow=(60, 112, 32, 6))
def dagger_3(d):
    with d.g(T(50, 80, 45, 1.75)):
        dagger(d, L=40, W=10, pal=RUNE, hilt=DBRONZE)
        aether_line(d, [(0.4, -3), (-0.6, -16), (-1.6, -32)], w=1.3)
        rune_ticks(d, (3, -6), (2, -20), 3, s=1.4, seed=9)
        d.glow(0, 0, 5, AE_C, 0.8)


@item(shadow=(64, 118, 40, 6))
def bow_2(d):
    with d.g(T(60, 64, 40, 1.12)):
        bow(d, H=104, limb=10, pal=EBONY)
        for s in (-1, 1):
            pts = bez((-2, s * 10), (-14, s * 20), (-12, s * 40), (0, s * 50), n=10)
            inlay(d, pts[1:-2], GOLD, w=1.1)
            d.circle(2, s * 52, 3, fill=GOLD["base"], stroke=OUTLINE, stroke_width=1)
    with d.g(T(26, 104, 45, 1.0)):
        arrow(d, L=100, pal=REF, fletch=dict(dark="#1a2a5a", base="#3a5ab0", light="#8ab0ff"))


@item(shadow=(64, 118, 40, 6))
def bow_3(d):
    with d.g(T(60, 64, 40, 1.12)):
        bow(d, H=104, limb=10, pal=RUNE)
        d.glow_stroke("M2,-52 L2,52", AE_C, 2.2, op=0.6)
        d.path("M2,-52 L2,52", stroke=AE_HI, sw=1.0)
        for s in (-1, 1):
            pts = bez((-3, s * 10), (-14, s * 20), (-12, s * 40), (0, s * 50), n=10)
            aether_line(d, pts[1:-2], w=1.2)
        d.glow(-2, 0, 9, AE_C, 0.7)
    with d.g(T(26, 104, 45, 1.0)):
        arrow(d, L=100, pal=dict(dark="#0a4a5e", base="#62e0f4", light="#ffffff"), fletch=dict(dark="#0a1a2a", base="#2a4a6a", light="#6ab0d0"))


@item(shadow=(56, 120, 40, 6))
def staff_2(d):
    with d.g(T(86, 28, 32, 1.12)):
        staff(d, H=94, thick=9, crystal_r=9.5, pal=dict(dark="#0a1e5a", base="#3a7ae8", light="#e0f0ff", glow="#4a8aff"), wood=EBONY)
        for yy in (22, 40, 70):
            d.path(f"M-5,{yy} L5,{yy + 1.5}", stroke=OUTLINE, sw=4)
            d.path(f"M-5,{yy} L5,{yy + 1.5}", stroke=GOLD["base"], sw=2.4)
        inlay(d, [(-1, 44), (1, 52), (-1, 60), (1, 68)], GOLD, w=0.9)


@item(shadow=(56, 120, 40, 6))
def staff_3(d):
    with d.g(T(86, 28, 32, 1.12)):
        staff(d, H=94, thick=9, crystal_r=9.5, pal=AE, wood=RUNE)
        aether_line(d, [(0, 16), (2, 40), (-1, 64), (0, 88)], w=1.6)
        orbit(d, 0, 0, 16, 5.5, -20)
        orbit(d, 0, 0, 14, 4.5, 50, w=1.0, op=0.7)


@item(shadow=(56, 114, 34, 6))
def wand_2(d):
    with d.g(T(82, 34, 40, 1.5)):
        wand(d, H=60, thick=1.5, pal=dict(dark="#4a0410", base="#e0283e", light="#ffc0c8", glow="#ff4050"))
        inlay(d, [(0, 10), (1.4, 22), (-1.4, 34), (0, 46)], GOLD, w=0.8)
    d.sparkle(98, 20, 5, "#ffffff", 0.9, glow_color="#ff6070")


@item(shadow=(56, 114, 34, 6))
def wand_3(d):
    with d.g(T(82, 34, 40, 1.5)):
        wand(d, H=60, thick=1.5, pal=AE)
        aether_line(d, [(0, 10), (0, 52)], w=1.1)
        orbit(d, 0, -3, 8, 2.6, -25, w=0.8)
    d.sparkle(98, 20, 6, "#ffffff", 0.95, glow_color=AE_C)


# ------------------------------------------------------------------------------------------ shields

@item(shadow=(64, 120, 34, 6))
def shield_2(d):
    with d.g(T(64, 62, 0, 1.3)):
        tower_shield(d, w=56, h=82, face=REF, band=GOLD)
        # sun boss emblem between the bands
        d.path(poly(star_pts(0, -2, 12, 13, 8)), fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], -12, -14, 12, 10), stroke=OUTLINE, stroke_width=1.2)
        d.circle(0, -2, 6.5, fill=d.rad([(0, SAPPHIRE["light"]), (1, SAPPHIRE["dark"])], -2, -4, 8), stroke=OUTLINE, stroke_width=1.2)
        d.circle(-2, -4, 1.6, fill="#ffffff", opacity=0.8)


@item(shadow=(64, 116, 36, 6))
def shield_3(d):
    cx, cy, r = 64, 62, 46
    d.circle(cx, cy, r + 2.6, fill=OUTLINE)
    d.circle(cx, cy, r, fill=d.lin([(0, DBRONZE["light"]), (0.5, DBRONZE["base"]), (1, DBRONZE["dark"])], cx - r, cy - r, cx + r, cy + r))
    d.circle(cx, cy, r - 6, fill=d.rad([(0, "#3a4a5c"), (0.7, "#141c26"), (1, "#070a10")], cx - 10, cy - 12, r))
    d.circle(cx, cy, r - 6, stroke=OUTLINE, stroke_width=1.4)
    for i in range(12):
        x, y = polar(cx, cy, r - 3, i * math.pi / 6)
        d.circle(x, y, 1.6, fill=DBRONZE["light"], stroke=OUTLINE, stroke_width=0.6)
    d.glow(cx, cy, r - 6, AE_C, 0.35)
    rune_ring(d, cx, cy, 30, AE_C, width=1.6, ticks=18, seed=4)
    pts = star_pts(cx, cy, 6, 22, 8)
    d.path(poly(pts), stroke=AE_C, sw=3.4, op=0.3)
    d.path(poly(pts), stroke=AE_HI, sw=1.4)
    aether_gem(d, cx, cy, 8)
    d.path(smooth(arc_pts(cx, cy, r - 2, math.radians(200), math.radians(250), 6), closed=False), stroke="#ffffff", sw=2, op=0.5)


# ------------------------------------------------------------------------------------------ helms

def plume(d, x, y, col=CRIMSON, L=34, lean=1.0):
    pts = bez((x, y), (x + 4 * lean, y - L * 0.6), (x + 22 * lean, y - L * 0.9), (x + 34 * lean, y - L * 0.55), n=14)
    dd = ribbon(pts, taper(14, 12, 0.6, 0.15, peak=0.35))
    d.path(dd, stroke=OUTLINE, sw=3.6)
    d.path(dd, fill=d.lin([(0, col["light"]), (0.5, col["base"]), (1, col["dark"])], x, y - L, x + 30 * lean, y))
    for k in range(3, 12, 2):
        px, py = pts[k]
        d.path(f"M{f(px)},{f(py)} L{f(px + 3 * lean)},{f(py + 5)}", stroke=col["dark"], sw=0.9, op=0.8)


@item(shadow=(64, 112, 36, 6))
def helm_plate_2(d):
    with d.g(T(60, 74, 0, 1.25)):
        plume(d, 0, -28, CRIMSON, L=26, lean=0.9)
        great_helm(d, w=46, h=56, pal=REF, trim=GOLD)
        for sx in (-1, 1):
            inlay(d, [(sx * 7, -20), (sx * 14, -24), (sx * 19, -18), (sx * 16, -12)], GOLD, w=1.0)
            d.circle(sx * 20, 10, 1.6, fill=GOLD["light"], stroke=OUTLINE, stroke_width=0.5)


@item(shadow=(64, 112, 36, 6))
def helm_plate_3(d):
    with d.g(T(64, 74, 0, 1.12)):
        great_helm(d, w=46, h=56, pal=RUNE, trim=DBRONZE, horns=True)
        d.glow(0, -1, 22, AE_C, 0.55)
        d.path(rrect_path(-20, -3.6, 40, 5.2, 2.4), fill=AE_C, op=0.9)
        d.path(rrect_path(-18, -2.4, 36, 2.4, 1.2), fill="#ffffff", op=0.9)
        aether_line(d, [(-9, -24), (-4, -18), (4, -18), (9, -24)], w=1.0)


def hood(d, c, trim, inner_glow=None, stars=False):
    outer = [(0, -56), (14, -48), (28, -26), (34, 4), (46, 30), (52, 46), (30, 52), (0, 48), (-30, 52), (-52, 46), (-46, 30), (-34, 4),
             (-28, -26), (-14, -48)]
    dd = smooth(outer, tension=0.5)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, c["light"]), (0.45, c["base"]), (1, c["dark"])], -52, -40, 52, 40))
    for pts in (((-8, -44), (-18, -20), (-22, 10)), ((10, -40), (18, -10), (24, 20)), ((-36, 30), (-26, 44)), ((34, 28), (28, 46))):
        d.path(smooth(pts, closed=False), stroke=c["dark"], sw=2.2, op=0.8)
        d.path(smooth([(x - 1.5, y) for x, y in pts], closed=False), stroke=c["light"], sw=0.8, op=0.4)
    # hem trim
    d.path(smooth([(-52, 46), (-30, 52), (0, 48), (30, 52), (52, 46)], closed=False), stroke=trim["base"], sw=3)
    face = [(0, -34), (16, -24), (20, 0), (12, 22), (0, 28), (-12, 22), (-20, 0), (-16, -24)]
    fd = smooth(face, tension=0.6)
    d.path(fd, stroke=trim["base"], sw=5)
    d.path(fd, stroke=trim["light"], sw=1.2, op=0.8)
    d.path(fd, fill=d.rad([(0, "#000000"), (0.7, "#05040a"), (1, dk(c["dark"], 0.3))], 0, 4, 26))
    if inner_glow:
        for sx in (-1, 1):
            d.glow(sx * 6, -2, 7, inner_glow, 0.9)
            d.path(poly([(sx * 3, -2), (sx * 6, -4), (sx * 9, -2), (sx * 6, -0.5)]), fill=AE_HI)
    if stars:
        rng = random.Random(7)
        for _ in range(9):
            x, y = rng.uniform(-40, 40), rng.uniform(-40, 44)
            if abs(x) < 20 and -34 < y < 28:
                continue
            d.sparkle(x, y, rng.uniform(1.6, 3.2), "#e8f0ff", 0.9)
    d.circle(0, 40, 5, fill=d.rad([(0, trim["light"]), (1, trim["dark"])], -1, 38, 6), stroke=OUTLINE, stroke_width=1.6)
    d.path(smooth([(-24, -20), (-10, -46), (0, -54)], closed=False), stroke="#ffffff", sw=1.4, op=0.3)


@item(shadow=(64, 118, 44, 6))
def helm_hood_2(d):
    with d.g(T(64, 64, 0, 1.0)):
        hood(d, dict(dark="#2a0608", base="#7a1620", light="#c84a50"), GOLD)
        for sx in (-1, 1):
            inlay(d, [(sx * 24, 30), (sx * 30, 40), (sx * 40, 44)], GOLD, w=1.0)


@item(shadow=(64, 118, 44, 6))
def helm_hood_3(d):
    with d.g(T(64, 64, 0, 1.0)):
        hood(d, dict(dark="#040a10", base="#16283a", light="#3a5a70"), dict(dark="#0a4a5e", base="#3ab8d0", light="#d8fdff"), inner_glow=AE_C)
        rune_ticks(d, (-40, 47), (40, 47), 8, s=2.2, seed=12)


# ------------------------------------------------------------------------------------------ body armour

@item(shadow=(64, 116, 44, 6))
def armor_plate_2(d):
    with d.g(T(64, 64, 0, 1.45)):
        cuirass(d, w=66, h=66, pal=REF, trim=GOLD)
        d.path(poly(star_pts(0, -10, 8, 8, 4)), fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], -8, -18, 8, -2), stroke=OUTLINE, stroke_width=0.9)
        d.circle(0, -10, 2.4, fill=CRIMSON["base"], stroke=OUTLINE, stroke_width=0.6)
        for sx in (-1, 1):
            inlay(d, [(sx * 4, -2), (sx * 10, 4), (sx * 16, 0), (sx * 15, -6)], GOLD, w=0.8)


@item(shadow=(64, 116, 44, 6))
def armor_plate_3(d):
    with d.g(T(64, 64, 0, 1.45)):
        cuirass(d, w=66, h=66, pal=RUNE, trim=DBRONZE)
        aether_line(d, [(-16, -18), (-8, -10), (0, -10), (8, -10), (16, -18)], w=1.0)
        aether_line(d, [(0, -4), (0, 26)], w=1.0)
        d.glow(0, -8, 12, AE_C, 0.8)
        d.path(poly(ngon(0, -8, 5, 6)), fill=AE_HI, stroke=OUTLINE, stroke_width=0.8)


def robe(d, c, trim, sash, rune_col="#c8a8ff", stars=False):
    for s in (-1, 1):
        sl = [(s * 22, -44), (s * 40, -26), (s * 54, 20), (s * 36, 26), (s * 28, -6)]
        sd = smooth(sl, tension=0.4)
        d.path(sd, stroke=OUTLINE, sw=5)
        d.path(sd, fill=d.lin([(0, c["light"]), (1, c["dark"])], s * 22, -40, s * 54, 20))
        d.path(poly([(s * 54, 20), (s * 36, 26)], closed=False), stroke=trim["base"], sw=3)
    body = [(-12, -50), (12, -50), (24, -44), (28, -6), (36, 52), (0, 56), (-36, 52), (-28, -6), (-24, -44)]
    bd = smooth(body, tension=0.3)
    d.path(bd, stroke=OUTLINE, sw=5)
    d.path(bd, fill=d.lin([(0, c["light"]), (0.45, c["base"]), (1, c["dark"])], -36, 0, 36, 0))
    for x in (-18, -8, 10, 20):
        d.path(smooth([(x * 0.6, 4), (x * 0.9, 30), (x * 1.1, 52)], closed=False), stroke=c["dark"], sw=2, op=0.7)
    d.path("M-12,-50 L0,-28 L12,-50 Z", fill="#07051a", stroke=OUTLINE, stroke_width=1.4)
    d.path("M-13,-49 L0,-26 L13,-49", stroke=trim["base"], sw=3)
    d.path("M0,-26 L0,55", stroke=trim["base"], sw=3.4)
    d.path("M0,-26 L0,55", stroke=trim["light"], sw=1)
    d.path(rrect_path(-28, -6, 56, 8, 2), fill=d.lin([(0, sash["light"]), (1, sash["dark"])], 0, -6, 0, 2), stroke=OUTLINE, stroke_width=1.6)
    d.path("M6,2 L10,26 L4,24 L2,2 Z", fill=sash["base"], stroke=OUTLINE, stroke_width=1.2)
    d.path("M-36,52 Q0,58 36,52", stroke=trim["base"], sw=3)
    if stars:
        rng = random.Random(3)
        for _ in range(10):
            x, y = rng.uniform(-30, 30), rng.uniform(6, 48)
            if abs(x) < 4:
                continue
            d.sparkle(x, y, rng.uniform(1.4, 2.8), "#e8f0ff", 0.9)
        d.path(poly([(-22, 14), (-14, 22), (-20, 34), (-10, 42)], closed=False), stroke="#c8d8ff", sw=0.7, op=0.6)
    else:
        d.path(poly(star_pts(-18, 40, 4, 5, 1.5)), fill=rune_col, op=0.85)
        d.path(poly(star_pts(18, 40, 4, 5, 1.5)), fill=rune_col, op=0.85)


@item(shadow=(64, 120, 44, 6))
def armor_robe_2(d):
    with d.g(T(64, 64, 0, 1.0)):
        robe(d, dict(dark="#2a0610", base="#6a1428", light="#b84a5a"), GOLD, dict(dark="#2a1a06", base="#a07a2a", light="#f0d080"), "#ffd890")
        d.circle(0, -2, 4, fill=d.rad([(0, "#fff0b0"), (1, "#a07a2a")], -1, -3, 5), stroke=OUTLINE, stroke_width=1.2)
        for sx in (-1, 1):
            inlay(d, [(sx * 6, 12), (sx * 12, 20), (sx * 8, 28), (sx * 14, 36)], GOLD, w=0.9)


@item(shadow=(64, 120, 44, 6))
def armor_robe_3(d):
    with d.g(T(64, 64, 0, 1.0)):
        robe(d, dict(dark="#03080c", base="#10222c", light="#2e5060"), dict(dark="#0a4a5e", base="#3ab8d0", light="#d8fdff"),
             dict(dark="#06101a", base="#1e3444", light="#4a7088"), AE_C)
        aether_line(d, [(0, -24), (0, 54)], w=1.2)
        aether_line(d, [(-34, 50), (0, 55), (34, 50)], w=1.0)
        d.glow(0, -2, 9, AE_C, 0.8)
        d.circle(0, -2, 3.2, fill=AE_HI, stroke=OUTLINE, stroke_width=0.8)


SHIRT = [(-14, -44), (14, -44), (30, -38), (46, -24), (54, 14), (44, 18), (34, -8), (32, 42), (0, 46), (-32, 42), (-34, -8),
         (-44, 18), (-54, 14), (-46, -24), (-30, -38)]


@item(shadow=(64, 120, 44, 6))
def inner_chain(d):
    c = dict(dark="#2a3038", base="#8a94a2", light="#e4eaf2")
    with d.g(T(64, 66, 0, 1.0)):
        dd = poly(SHIRT)
        d.path(dd, stroke=OUTLINE, sw=5)
        d.path(dd, fill=d.lin([(0, c["light"]), (0.5, c["base"]), (1, c["dark"])], -54, -40, 54, 40))
        rings = []
        for j in range(-11, 12):
            y = j * 4.2
            for i in range(-14, 15):
                x = i * 4.2 + (2.1 if j % 2 else 0)
                if inside((x, y), SHIRT) and inside((x + 2, y + 2), SHIRT) and inside((x - 2, y - 2), SHIRT):
                    rings.append(circle_path(x, y, 1.7))
        d.path(" ".join(rings), stroke=c["dark"], sw=0.8, op=0.75)
        d.path(" ".join(rings[::3]), stroke="#ffffff", sw=0.5, op=0.35)
        # leather collar + hem binding
        d.path("M-14,-44 Q0,-36 14,-44", stroke=LEATHER["base"], sw=5)
        d.path("M-14,-44 Q0,-36 14,-44", stroke=LEATHER["light"], sw=1.2, op=0.6)
        d.path("M-32,42 L0,46 L32,42", stroke=LEATHER["base"], sw=4)
        d.path(dd, stroke=OUTLINE, sw=2.4)
        d.path("M-40,-20 L-30,-34", stroke="#ffffff", sw=2, op=0.4)


@item(shadow=(64, 120, 44, 6))
def inner_silk(d):
    c = dict(dark="#6a5a4a", base="#e4d8c4", light="#fffaf0")
    with d.g(T(64, 66, 0, 1.0)):
        pts = [(-14, -44), (14, -44), (30, -38), (48, -22), (58, 12), (46, 16), (34, -6), (34, 44), (0, 48), (-34, 44), (-34, -6),
               (-46, 16), (-58, 12), (-48, -22), (-30, -38)]
        dd = smooth(pts, tension=0.25)
        d.path(dd, stroke=OUTLINE, sw=5)
        d.path(dd, fill=d.lin([(0, c["light"]), (0.4, c["base"]), (0.7, lt(c["base"], 0.3)), (1, c["dark"])], -58, -30, 58, 40))
        # silk sheen folds
        for x in (-20, -6, 12, 24):
            d.path(smooth([(x, -30), (x + 3, 0), (x - 2, 40)], closed=False), stroke="#ffffff", sw=3, op=0.35)
            d.path(smooth([(x + 3, -30), (x + 6, 0), (x + 1, 40)], closed=False), stroke=c["dark"], sw=1.2, op=0.35)
        # embroidered collar
        d.path("M-14,-44 L0,-26 L14,-44", stroke=OUTLINE, sw=4.4)
        d.path("M-14,-44 L0,-26 L14,-44", stroke=GOLD["base"], sw=2.6)
        for sx in (-1, 1):
            inlay(d, [(sx * 6, -38), (sx * 10, -30), (sx * 16, -32)], dict(dark="#0a3a6a", base="#3a7ae8", light="#8ab8ff"), w=1.0)
        d.path("M-34,44 Q0,50 34,44", stroke=GOLD["base"], sw=2.6)
        d.path("M-58,12 L-46,16 M58,12 L46,16", stroke=GOLD["base"], sw=2.6)


@item(shadow=(64, 118, 34, 6))
def gloves_plate_2(d):
    with d.g(T(66, 64, -8, 1.12)):
        glove(d, REF, GOLD, plated=True)
        inlay(d, [(-16, -6), (-6, -9), (6, -9), (16, -6)], GOLD, w=1.4)
        d.circle(0, 14, 3.2, fill=SAPPHIRE["base"], stroke=OUTLINE, stroke_width=1)
        for sx in (-1, 1):
            scroll_curl(d, sx * 6, 34, s=1.4, flip=sx)


@item(shadow=(64, 118, 34, 6))
def gloves_cloth_2(d):
    with d.g(T(66, 64, -8, 1.12)):
        glove(d, dict(dark="#1a0a24", base="#4a2a6a", light="#8a6ab0"), GOLD, plated=False)
        d.path(poly(star_pts(0, 6, 4, 6, 2)), fill=GOLD["light"], stroke=OUTLINE, stroke_width=0.8)
        inlay(d, [(-20, 30), (0, 32), (20, 30)], GOLD, w=1.2)


@item(shadow=(66, 112, 38, 6))
def boots_plate_2(d):
    with d.g(T(58, 72, 0, 1.3)):
        boot(d, REF, GOLD, plated=True)
        inlay(d, [(-14, -40), (-6, -36), (2, -40), (8, -34)], GOLD, w=1.0)
        d.circle(-2, -44, 2.4, fill=SAPPHIRE["base"], stroke=OUTLINE, stroke_width=0.8)
        inlay(d, [(20, 4), (28, 10), (36, 16)], GOLD, w=1.0)


@item(shadow=(66, 112, 38, 6))
def boots_cloth_2(d):
    with d.g(T(58, 72, 0, 1.3)):
        boot(d, dict(dark="#101a2a", base="#2a4468", light="#6a8ab8"), GOLD, plated=False)
        inlay(d, [(-18, -44), (-2, -46), (14, -44)], GOLD, w=1.2)


# ------------------------------------------------------------------------------------------ jewellery

def ring_base(d, metal, stone, glow, cx=64, cy=76, stone_sides=8, runes=None):
    g = metal
    d.path(circle_path(cx, cy + 6, 36, 20) + " " + circle_path(cx, cy + 6, 27, 13), fill=g["dark"], fill_rule="evenodd", stroke=OUTLINE, stroke_width=2.4)
    band = circle_path(cx, cy, 36, 20) + " " + circle_path(cx, cy, 27, 13)
    d.path(band, fill=d.lin([(0, g["light"]), (0.35, g["base"]), (0.7, g["dark"]), (1, g["base"])], cx - 36, cy - 20, cx + 36, cy + 20), fill_rule="evenodd", stroke=OUTLINE, stroke_width=2.4)
    d.path(smooth(arc_pts(cx, cy, 32, math.radians(150), math.radians(230), 8, ry=17), closed=False), stroke="#ffffff", sw=2, op=0.6)
    if runes:
        pts = arc_pts(cx, cy, 31.5, math.radians(20), math.radians(160), 30, ry=16.5)
        aether_line(d, pts, w=1.3, col=runes)
    d.glow(cx, cy - 26, 26, glow, 0.5)
    d.path(poly([(cx - 16, cy - 16), (cx + 16, cy - 16), (cx + 10, cy - 8), (cx - 10, cy - 8)]), fill=d.lin([(0, g["light"]), (1, g["dark"])], 0, cy - 16, 0, cy - 8), stroke=OUTLINE, stroke_width=1.8)
    gem(d, cx, cy - 28, 15, stone, sides=stone_sides)
    for s in (-1, 1):
        for dx in (6, 13):
            d.path(poly([(cx + s * dx, cy - 14), (cx + s * (dx + 1), cy - 22), (cx + s * (dx - 1.5), cy - 20)]), fill=g["light"], stroke=OUTLINE, stroke_width=1)


@item(shadow=(64, 112, 44, 6))
def ring_2(d):
    with d.g("translate(64 64) scale(1.22) translate(-64 -64)"):
        ring_base(d, WGOLD, SAPPHIRE, "#3a7aff", stone_sides=10)
        for x in (44, 84):
            d.circle(x, 76, 2, fill=SAPPHIRE["light"], stroke=OUTLINE, stroke_width=0.8)


@item(shadow=(64, 112, 44, 6))
def ring_3(d):
    with d.g("translate(64 64) scale(1.22) translate(-64 -64)"):
        ring_base(d, RUNE, dict(dark="#06506a", base="#40d0ea", light="#e8feff"), AE_C, stone_sides=6, runes=AE_C)


def pendant_chain(d, g, bail_y=56):
    for side in (-1, 1):
        pts = qbez((64 + side * 44, 8), (64 + side * 40, 56), (64 + side * 8, 60), n=16)
        for i, (x, y) in enumerate(pts):
            d.ellipse(x, y, 3.2, 2.2, stroke=OUTLINE, stroke_width=3.2)
            d.ellipse(x, y, 3.2, 2.2, stroke=g["base"] if i % 2 else g["light"], stroke_width=1.5)
    d.shape(rrect_path(59, bail_y, 10, 12, 3), fill=d.lin([(0, g["light"]), (1, g["dark"])], 59, 0, 69, 0), ow=1.8)


@item(shadow=None)
def amulet_2(d):
    g = WGOLD
    pendant_chain(d, g)
    cx, cy = 64, 90
    shape = [(cx, cy - 26), (cx + 22, cy - 8), (cx + 14, cy + 22), (cx, cy + 30), (cx - 14, cy + 22), (cx - 22, cy - 8)]
    dd = smooth(shape, tension=0.4)
    d.path(dd, stroke=OUTLINE, sw=4.4)
    d.path(dd, fill=d.lin([(0, g["light"]), (0.5, g["base"]), (1, g["dark"])], cx - 22, cy - 26, cx + 22, cy + 30))
    for sx in (-1, 1):
        inlay(d, [(cx + sx * 4, cy - 20), (cx + sx * 14, cy - 8), (cx + sx * 10, cy + 14)], GOLD, w=0.9)
    d.glow(cx, cy, 24, "#30d060", 0.5)
    gem(d, cx, cy + 2, 12, EMERALD, sides=8)


@item(shadow=None)
def amulet_3(d):
    g = DBRONZE
    pendant_chain(d, g)
    cx, cy = 64, 90
    d.circle(cx, cy, 27, fill=OUTLINE)
    d.circle(cx, cy, 24.5, fill=d.lin([(0, g["light"]), (0.5, g["base"]), (1, g["dark"])], cx - 24, cy - 24, cx + 24, cy + 24))
    d.circle(cx, cy, 19, fill=d.rad([(0, "#2a3a4a"), (1, "#070a10")], cx - 5, cy - 6, 22))
    d.glow(cx, cy, 24, AE_C, 0.5)
    rune_ring(d, cx, cy, 16, AE_C, width=1.2, ticks=12, seed=6)
    orbit(d, cx, cy, 30, 10, -24, w=1.2)
    aether_gem(d, cx, cy, 7, glow=False)


@item(shadow=None)
def charm_2(d):
    # jade talisman on a red cord with gold wire and tassel
    jade = dict(dark="#0a3a2a", base="#3aa07a", light="#b8f0d8")
    d.path("M64,6 C44,6 46,30 58,40 M64,6 C84,6 82,30 70,40", stroke=OUTLINE, sw=4.6)
    d.path("M64,6 C44,6 46,30 58,40 M64,6 C84,6 82,30 70,40", stroke=CLOTH_RED["base"], sw=2.2)
    d.circle(64, 42, 5, fill=d.rad([(0, GOLD["light"]), (1, GOLD["dark"])], 62, 40, 6), stroke=OUTLINE, stroke_width=1.4)
    cx, cy = 64, 72
    disc = circle_path(cx, cy, 24) + " " + circle_path(cx, cy, 7)
    d.path(circle_path(cx, cy, 24), stroke=OUTLINE, sw=4.6)
    d.path(disc, fill=d.lin([(0, jade["light"]), (0.5, jade["base"]), (1, jade["dark"])], cx - 24, cy - 24, cx + 24, cy + 24), fill_rule="evenodd")
    d.circle(cx, cy, 7, stroke=OUTLINE, stroke_width=1.6)
    for i in range(8):
        a = i * math.pi / 4
        p0, p1 = polar(cx, cy, 10, a), polar(cx, cy, 20, a + 0.3)
        d.path(f"M{f(p0[0])},{f(p0[1])} Q{f(polar(cx, cy, 16, a - 0.2)[0])},{f(polar(cx, cy, 16, a - 0.2)[1])} {f(p1[0])},{f(p1[1])}", stroke=jade["dark"], sw=1.2, op=0.8)
    d.circle(cx, cy, 21.5, stroke=GOLD["base"], stroke_width=1.6)
    d.path(smooth(arc_pts(cx, cy, 20, math.radians(200), math.radians(250), 6), closed=False), stroke="#ffffff", sw=2.2, op=0.6)
    # tassel
    for i in range(7):
        x = cx - 6 + i * 2
        d.path(f"M{f(x)},{cy + 26} L{f(x + (i - 3) * 0.8)},{cy + 48}", stroke=OUTLINE, sw=2.6)
        d.path(f"M{f(x)},{cy + 26} L{f(x + (i - 3) * 0.8)},{cy + 48}", stroke=CLOTH_RED["light"] if i % 2 else CLOTH_RED["base"], sw=1.4)
    d.shape(rrect_path(cx - 7, cy + 22, 14, 7, 2), fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], 0, cy + 22, 0, cy + 29), ow=1.4)


# ------------------------------------------------------------------------------------------ consumables

def big_flask(d, liquid, cage=GOLD):
    with d.g("translate(64 70) scale(1.12) translate(-64 -70)"):
        potion(d, liquid)
    # filigree cage over the bulb
    cx, cy, r = 64, 80 + (80 - 70) * 0.12, 30 * 1.12
    for a in (-60, -20, 20, 60):
        pts = [polar(cx, cy, r + 0.5, math.radians(-90 + a * 0.25 - 60)), polar(cx, cy, r + 1, math.radians(90 + a))]
        d.path(f"M{f(cx + a * 0.25)},{f(cy - r + 2)} Q{f(cx + a * 0.75)},{f(cy)} {f(cx + a * 0.3)},{f(cy + r - 1)}", stroke=OUTLINE, sw=3.4)
        d.path(f"M{f(cx + a * 0.25)},{f(cy - r + 2)} Q{f(cx + a * 0.75)},{f(cy)} {f(cx + a * 0.3)},{f(cy + r - 1)}", stroke=cage["base"], sw=1.6)
    d.path(f"M{f(cx - r)},{f(cy)} Q{f(cx)},{f(cy + 8)} {f(cx + r)},{f(cy)}", stroke=OUTLINE, sw=3.6)
    d.path(f"M{f(cx - r)},{f(cy)} Q{f(cx)},{f(cy + 8)} {f(cx + r)},{f(cy)}", stroke=cage["light"], sw=1.8)
    d.circle(cx, cy + 4, 3.2, fill=d.rad([(0, cage["light"]), (1, cage["dark"])], cx - 1, cy + 3, 4), stroke=OUTLINE, stroke_width=1)


@item(shadow=(64, 118, 36, 5))
def potion_health_large(d):
    big_flask(d, dict(dark="#4a0008", base="#d0162a", light="#ff9aa4", glow="#ff3048"))


@item(shadow=(64, 118, 36, 5))
def potion_mana_large(d):
    big_flask(d, dict(dark="#061a5a", base="#2a5ae8", light="#a8d0ff", glow="#3a7aff"), cage=SILVER)


@item(shadow=(64, 116, 26, 5))
def elixir_rejuvenation(d):
    cx = 64
    liquid = dict(dark="#0a4a1a", base="#3ad05a", light="#e0ffb0", glow="#80ff60")
    d.glow(cx, 78, 40, liquid["glow"], 0.45)
    body = [(cx - 8, 34), (cx + 8, 34), (cx + 10, 44), (cx + 20, 60), (cx + 20, 100), (cx + 14, 108), (cx - 14, 108), (cx - 20, 100), (cx - 20, 60), (cx - 10, 44)]
    dd = smooth(body, tension=0.3)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, "#2a3440"), (1, "#0c1016")], cx - 20, 0, cx + 20, 0))
    liq = [(cx - 19, 64), (cx - 6, 60), (cx + 6, 66), (cx + 19, 62), (cx + 19, 100), (cx + 13, 106), (cx - 13, 106), (cx - 19, 100)]
    d.path(smooth(liq, tension=0.3), fill=d.lin([(0, liquid["light"]), (0.4, liquid["base"]), (1, liquid["dark"])], cx, 60, cx, 106))
    # swirl of life
    d.path(smooth([(cx - 10, 98), (cx + 8, 90), (cx - 6, 80), (cx + 6, 70)], closed=False), stroke="#f0ffd0", sw=1.6, op=0.8)
    for (x, y, r) in ((cx - 8, 88, 2), (cx + 9, 96, 1.6), (cx + 2, 76, 1.4)):
        d.circle(x, y, r, stroke=liquid["light"], stroke_width=0.9)
    d.path(f"M{cx - 13},50 L{cx - 13},96", stroke="#ffffff", sw=2.4, op=0.5)
    # gold collar + leaf stopper
    d.path(rrect_path(cx - 11, 30, 22, 7, 2.5), fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], 0, 30, 0, 37), stroke=OUTLINE, stroke_width=1.8)
    for sx in (-1, 1):
        lf = [(cx, 30), (cx + sx * 10, 20), (cx + sx * 16, 8), (cx + sx * 6, 14)]
        ld = smooth(lf, tension=0.5)
        d.path(ld, stroke=OUTLINE, sw=3.4)
        d.path(ld, fill=d.lin([(0, "#b8f090"), (1, "#2a7a2a")], cx, 8, cx + sx * 16, 30))
        d.path(f"M{cx},28 L{f(cx + sx * 11)},14", stroke="#1a5a1a", sw=0.9)
    d.path(rrect_path(cx - 4, 18, 8, 13, 2), fill=d.lin([(0, "#d8a868"), (1, "#6a4020")], cx - 4, 0, cx + 4, 0), stroke=OUTLINE, stroke_width=1.4)
    d.sparkle(cx + 16, 50, 5, "#ffffff", 0.9, glow_color="#a0ff80")


@item(shadow=(64, 110, 46, 6))
def scroll_return(d):
    paper = dict(dark="#8a7050", base="#e4d2a8", light="#fff6dc")
    # unrolled sheet between two rollers
    sheet = [(30, 36), (98, 30), (100, 94), (32, 100)]
    d.shape(poly(sheet), fill=d.lin([(0, paper["light"]), (0.6, paper["base"]), (1, paper["dark"])], 30, 30, 100, 100), ow=2.4)
    # teleport sigil
    cx, cy = 65, 64
    d.glow(cx, cy, 24, AE_C, 0.6)
    rune_ring(d, cx, cy, 17, "#1a6a8a", width=1.3, ticks=12, seed=2)
    d.path(poly(star_pts(cx, cy, 4, 10, 3)), fill=AE_C, stroke="#0a4a5e", stroke_width=0.8)
    d.circle(cx, cy, 2.4, fill="#ffffff")
    for (x0, y0, x1, y1) in ((38, 44, 56, 42), (72, 88, 92, 84)):
        d.path(f"M{x0},{y0} L{x1},{y1}", stroke="#6a5030", sw=1.2, op=0.7)
    for (a, b) in (((22, 38), (106, 28)), ((24, 102), (108, 92))):
        # rollers
        d.path(poly([a, b], closed=False), stroke=OUTLINE, sw=12)
        d.path(poly([a, b], closed=False), stroke=WOOD["base"], sw=8.4)
        d.path(poly([(a[0], a[1] - 2), (b[0], b[1] - 2)], closed=False), stroke=WOOD["light"], sw=2, op=0.7)
        for p in (a, b):
            d.circle(p[0], p[1], 5.6, fill=d.rad([(0, GOLD["light"]), (1, GOLD["dark"])], p[0] - 1.5, p[1] - 1.5, 6), stroke=OUTLINE, stroke_width=1.6)
    # blue wax seal hanging
    d.path("M84,98 L88,114 M90,98 L96,112", stroke=CLOTH_RED["base"], sw=2.4)
    d.circle(88, 100, 7, fill=d.rad([(0, "#8ab0ff"), (1, "#1a3a8a")], 86, 98, 8), stroke=OUTLINE, stroke_width=1.6)
    d.path(poly(star_pts(88, 100, 4, 3.6, 1.2)), fill="#d8e8ff")


@item(shadow=(64, 114, 30, 5))
def antidote(d):
    cx = 64
    liquid = dict(dark="#3a4a06", base="#b0d020", light="#f0ffa0", glow="#c0ff40")
    d.glow(cx, 84, 34, liquid["glow"], 0.35)
    body = [(cx - 9, 44), (cx + 9, 44), (cx + 26, 62), (cx + 28, 98), (cx + 22, 106), (cx - 22, 106), (cx - 28, 98), (cx - 26, 62)]
    dd = smooth(body, tension=0.25)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, "#2a3440"), (1, "#0c1016")], cx - 26, 0, cx + 26, 0))
    liq = [(cx - 25, 72), (cx + 25, 72), (cx + 27, 98), (cx + 21, 104), (cx - 21, 104), (cx - 27, 98)]
    d.path(smooth(liq, tension=0.25), fill=d.lin([(0, liquid["light"]), (0.4, liquid["base"]), (1, liquid["dark"])], cx, 72, cx, 104))
    d.ellipse(cx, 72, 25, 3, fill=lt(liquid["base"], 0.3))
    d.path(f"M{cx - 18},66 L{cx - 20},96", stroke="#ffffff", sw=2.6, op=0.5)
    # label with herb leaf
    d.path(rrect_path(cx - 14, 76, 28, 18, 2), fill=LINEN["light"], stroke=OUTLINE, stroke_width=1.4)
    lf = smooth([(cx - 8, 90), (cx - 2, 80), (cx + 8, 78), (cx + 2, 88)], tension=0.5)
    d.path(lf, fill="#3a8a2a", stroke="#143a0a", stroke_width=0.9)
    d.path(f"M{cx - 7},89 L{cx + 6},79", stroke="#b0e080", sw=0.8)
    d.path(rrect_path(cx - 11, 38, 22, 8, 3), fill=d.lin([(0, "#c0c8d8"), (1, "#4a5060")], 0, 38, 0, 46), stroke=OUTLINE, stroke_width=1.6)
    d.path(rrect_path(cx - 7, 24, 14, 16, 3), fill=d.lin([(0, "#d8a868"), (1, "#6a4020")], cx - 7, 0, cx + 7, 0), stroke=OUTLINE, stroke_width=1.8)


# ------------------------------------------------------------------------------------------ materials

@item(shadow=(64, 108, 42, 7))
def aether_shard(d):
    d.glow(64, 70, 54, AE_C, 0.75)
    pal = dict(dark="#063a4a", base="#40c8e0", light="#f0ffff", glow=AE_C)
    for (cx, cy, r, st, rot_) in ((48, 84, 8, 2.2, -24), (82, 86, 7, 2.0, 22), (64, 70, 11, 2.8, 0)):
        with d.g(f"rotate({rot_} {cx} {cy})"):
            crystal(d, cx, cy, r, pal, stretch=st, glow=False)
    motes(d, [(34, 46, 1), (96, 50, 0.8), (88, 26, 0.7), (40, 24, 0.6)], AE_HI, glow_color=AE_C, size=2.2)
    d.sparkle(64, 40, 8, "#ffffff", 1.0, glow_color=AE_C)


@item(shadow=(64, 108, 42, 7))
def frost_crystal(d):
    p = EL["ice"]
    d.glow(64, 72, 50, p["glow"], 0.55)
    rng = random.Random(4)
    for (cx, cy, r, st, rot_) in ((44, 88, 7, 2.2, -32), (86, 90, 6, 2.1, 28), (58, 80, 8, 2.6, -10), (72, 78, 9, 2.9, 10)):
        with d.g(f"rotate({rot_} {cx} {cy})"):
            crystal(d, cx, cy, r, dict(dark="#1f5a7a", base="#8ad8f0", light="#ffffff", glow=p["glow"]), stretch=st, glow=False)
    rock(d, 64, 104, 22, pal=dict(dark="#1a2a3a", base="#4a6a88", light="#a8c8e0"), seed=3, sy=0.35)
    snowflake(d, 94, 34, 11, p, width=2.2, glow=True)
    d.sparkle(40, 40, 5, "#ffffff", 0.9)


@item(shadow=(64, 112, 34, 6))
def storm_essence(d):
    cx, cy, r = 64, 64, 34
    p = EL["lightning"]
    d.glow(cx, cy, 54, p["glow"], 0.6)
    d.circle(cx, cy, r + 2.6, fill=OUTLINE)
    d.circle(cx, cy, r, fill=d.rad([(0, "#4a3a9a"), (0.7, "#1a1044"), (1, "#0a0620")], cx - 8, cy - 8, r * 1.2))
    rng = random.Random(6)
    for (a, b) in (((cx, cy), (cx - 22, cy - 18)), ((cx, cy), (cx + 24, cy - 12)), ((cx, cy), (cx + 8, cy + 26)), ((cx, cy), (cx - 20, cy + 16))):
        bolt(d, jag_line(a, b, 4, 4, rng), width=3.2, pal=p, glow=False)
    d.glow(cx, cy, 14, "#fff8c0", 1.0, core="#ffffff")
    # metal cradle
    d.path(smooth(arc_pts(cx, cy, r + 1, math.radians(30), math.radians(150), 12), closed=False), stroke=OUTLINE, sw=7)
    d.path(smooth(arc_pts(cx, cy, r + 1, math.radians(30), math.radians(150), 12), closed=False), stroke=SILVER["base"], sw=4)
    for a in (40, 90, 140):
        x, y = polar(cx, cy, r + 1, math.radians(a))
        d.circle(x, y, 3, fill=SILVER["light"], stroke=OUTLINE, stroke_width=1)
    d.path(smooth(arc_pts(cx, cy, r - 6, math.radians(200), math.radians(250), 6), closed=False), stroke="#ffffff", sw=3, op=0.6)


@item(shadow=(64, 108, 46, 7))
def shadow_silk(d):
    c = dict(dark="#0a0414", base="#3a1a5a", light="#9a6ad8")
    # folded bolt of cloth: three stacked folds
    for k, (y, w) in enumerate(((88, 70), (70, 64), (52, 58))):
        x0 = 64 - w / 2
        fold = [(x0, y), (x0 + w, y - 6), (x0 + w + 6, y + 8), (x0 + 6, y + 14)]
        dd = smooth(fold, tension=0.25)
        d.path(dd, stroke=OUTLINE, sw=4.4)
        d.path(dd, fill=d.lin([(0, c["light"]), (0.3, c["base"]), (0.6, lt(c["base"], 0.15)), (1, c["dark"])], x0, y - 6, x0 + w, y + 14))
        d.path(smooth([(x0 + 8, y + 4), (x0 + w * 0.5, y + 1), (x0 + w - 4, y)], closed=False), stroke="#ffffff", sw=1.6, op=0.35)
    # trailing loose end
    tail = [(96, 60), (110, 72), (104, 92), (112, 108)]
    d.path(ribbon(smooth_pts(tail, 20), taper(20, 10, 1.0, 0.3)), fill=c["base"], stroke=OUTLINE, stroke_width=2)
    motes(d, [(30, 40, 0.8), (98, 36, 0.7), (40, 104, 0.6)], "#c8a0ff", glow_color="#6a2aa0", size=2.2)


@item(shadow=(64, 110, 48, 7))
def beast_hide(d):
    c = dict(dark="#3a200c", base="#9a6a3a", light="#e0b884")
    hide = [(30, 30), (46, 36), (64, 26), (82, 36), (100, 28), (104, 50), (96, 66), (108, 86), (96, 104), (74, 98), (64, 110),
            (52, 98), (30, 104), (20, 86), (32, 66), (22, 50)]
    dd = smooth(hide, tension=0.45)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.rad([(0, c["light"]), (0.6, c["base"]), (1, c["dark"])], 56, 56, 60))
    # fur edge tufts
    rng = random.Random(2)
    for i in range(0, len(hide)):
        x, y = hide[i]
        dx, dy = x - 64, y - 68
        L = math.hypot(dx, dy) or 1
        d.path(f"M{f(x)},{f(y)} L{f(x + dx / L * 6)},{f(y + dy / L * 6)}", stroke=c["dark"], sw=2.2)
    # stitch lacing + markings
    for (x, y) in ((44, 60), (84, 58), (58, 84), (72, 50)):
        d.ellipse(x, y, 7, 3.6, fill=c["dark"], opacity=0.5)
    d.path(smooth([(40, 44), (64, 50), (88, 44)], closed=False), stroke=c["light"], sw=1.6, op=0.5)
    for i in range(6):
        x = 42 + i * 9
        d.path(f"M{x},92 L{x + 4},96", stroke="#2a1606", sw=1.4)


# ------------------------------------------------------------------------------------------ quest items

@item(shadow=(64, 112, 44, 6))
def quest_seal_key(d):
    with d.g(T(64, 64, -40, 1.0)):
        g = GOLD
        # shaft + bit
        d.shape(rrect_path(-4.5, -8, 9, 64, 3), fill=d.lin([(0, g["light"]), (0.5, g["base"]), (1, g["dark"])], -4.5, 0, 4.5, 0), ow=2.2)
        bit = [(4, 38), (18, 38), (18, 46), (12, 46), (12, 50), (18, 50), (18, 56), (4, 56)]
        d.shape(poly(bit), fill=d.lin([(0, g["light"]), (1, g["dark"])], 4, 38, 18, 56), ow=2)
        for yy in (8, 20):
            d.shape(rrect_path(-6.5, yy, 13, 4, 1.5), fill=g["light"], ow=1.4)
        # seal bow: round crest with crimson gem
        d.path(poly(star_pts(0, -28, 8, 24, 18, rot0=-math.pi / 2 + math.pi / 8)), stroke=OUTLINE, sw=4.4)
        d.path(poly(star_pts(0, -28, 8, 24, 18, rot0=-math.pi / 2 + math.pi / 8)), fill=d.lin([(0, g["light"]), (0.5, g["base"]), (1, g["dark"])], -24, -52, 24, -4))
        d.circle(0, -28, 14, fill=d.rad([(0, "#3a0a10"), (1, "#12040a")], 0, -28, 14), stroke=OUTLINE, stroke_width=1.6)
        d.glow(0, -28, 16, "#ff3040", 0.5)
        gem(d, 0, -28, 9, RUBY, sides=8)


@item(shadow=(64, 114, 42, 7))
def quest_tablet(d):
    st = dict(dark="#2a2622", base="#6e665a", light="#b8ae9a")
    slab = [(34, 20), (86, 16), (98, 30), (96, 104), (40, 110), (28, 96), (30, 34)]
    d.shape(poly(slab), fill=d.lin([(0, st["light"]), (0.5, st["base"]), (1, st["dark"])], 28, 16, 98, 110), ow=2.6)
    # broken corner
    d.path(poly([(86, 16), (98, 30), (90, 34), (88, 26)]), fill=st["dark"], op=0.8)
    d.path("M34,20 L86,16 L98,30", stroke="#ffffff", sw=1.4, op=0.3)
    # carved glowing runes (rows)
    rng = random.Random(8)
    for row in range(5):
        y = 34 + row * 14
        x = 40
        while x < 86:
            s = 4.2
            k = rng.randint(0, 3)
            if k == 0:
                g_ = f"M{x},{y - s} L{x},{y + s} M{x},{y - s} L{x + s},{y}"
            elif k == 1:
                g_ = f"M{x - s * 0.6},{y + s} L{x},{y - s} L{x + s * 0.6},{y + s}"
            elif k == 2:
                g_ = f"M{x},{y - s} L{x},{y + s} M{x - s * 0.6},{y - s * 0.3} L{x + s * 0.6},{y + s * 0.3}"
            else:
                g_ = f"M{x - s * 0.5},{y - s} L{x + s * 0.5},{y} L{x - s * 0.5},{y + s}"
            d.path(g_, stroke="#141210", sw=2.6)
            d.path(g_, stroke=AE_C, sw=1.1, op=0.95)
            x += 10
    d.glow(64, 62, 36, AE_C, 0.25)
    for (a, b) in (((40, 108), (52, 90)), ((52, 90), (50, 80))):
        d.path(poly([a, b], closed=False), stroke="#141210", sw=1.2)


@item(shadow=(64, 108, 46, 7))
def quest_crown_fragment(d):
    g = GOLD
    # half crown band with a jagged break on the right
    band = [(18, 86), (26, 60), (36, 40), (44, 60), (56, 32), (66, 58), (74, 44), (78, 60), (72, 70), (82, 74), (76, 84), (84, 94), (22, 100)]
    d.shape(poly(band), fill=d.lin([(0, g["light"]), (0.5, g["base"]), (1, g["dark"])], 18, 32, 84, 100), ow=2.6)
    d.path("M22,90 L80,88", stroke=g["dark"], sw=1.6)
    d.path("M22,92 L80,90", stroke=g["light"], sw=0.9, op=0.7)
    for (x, y, pal, r) in ((36, 44, SAPPHIRE, 4.2), (56, 36, RUBY, 5), (32, 76, EMERALD, 4.4), (56, 76, RUBY, 4.4)):
        gem(d, x, y, r, pal, sides=6, sparkle=False)
    d.path(poly([(74, 44), (78, 60), (72, 70), (82, 74), (76, 84), (84, 94)], closed=False), stroke="#fff0c0", sw=1.2, op=0.8)
    # separated shard
    shard = [(96, 70), (106, 64), (110, 80), (100, 90)]
    d.shape(poly(shard), fill=d.lin([(0, g["light"]), (1, g["dark"])], 96, 64, 110, 90), ow=2)
    d.sparkle(40, 24, 6, "#ffffff", 0.95, glow_color="#ffd070")
    d.sparkle(98, 56, 4, "#ffffff", 0.8)


@item(shadow=(64, 108, 46, 6))
def quest_letter(d):
    paper = dict(dark="#8a7050", base="#e8d6ae", light="#fff8e2")
    env = [(20, 40), (108, 32), (112, 94), (24, 102)]
    d.shape(poly(env), fill=d.lin([(0, paper["light"]), (0.6, paper["base"]), (1, paper["dark"])], 20, 32, 112, 102), ow=2.6)
    d.path(poly([(20, 40), (66, 74), (108, 32)], closed=False), stroke=paper["dark"], sw=2)
    d.path(poly([(24, 102), (62, 72)], closed=False), stroke=paper["dark"], sw=1.4, op=0.7)
    d.path(poly([(112, 94), (72, 70)], closed=False), stroke=paper["dark"], sw=1.4, op=0.7)
    # ribbon
    d.path("M20,64 L112,58", stroke=OUTLINE, sw=7)
    d.path("M20,64 L112,58", stroke=CLOTH_RED["base"], sw=4.4)
    # wax seal with crest
    cx, cy = 66, 72
    seal = [polar(cx, cy, 13 + (1.5 if i % 2 else 0), i * math.pi / 8) for i in range(16)]
    d.path(smooth(seal, tension=0.6), fill=d.rad([(0, "#e0404a"), (1, "#5a0a10")], cx - 4, cy - 4, 16), stroke=OUTLINE, stroke_width=1.8)
    d.circle(cx, cy, 8, stroke="#3a0408", stroke_width=1.2)
    d.path(poly(star_pts(cx, cy, 5, 5.5, 2.4)), fill="#ff8a8a", op=0.9)
    d.path("M58,108 L60,116 M70,108 L74,116", stroke=CLOTH_RED["base"], sw=3)


# ------------------------------------------------------------------------------------------ Aether Guardian set (knight)

GUARD = dict(dark="#5a6278", base="#dce4f0", light="#ffffff", glow="#e8f0ff")


def guardian_wings(d, x, y, s=1.0):
    for sx in (-1, 1):
        for k in range(3):
            pts = [(x, y + k * 5 * s), (x + sx * (14 + k * 4) * s, y - (10 - k * 4) * s), (x + sx * (22 + k * 2) * s, y - (4 - k * 5) * s)]
            dd = ribbon(pts, [4 * s, 5 * s, 0.6])
            d.path(dd, fill=d.lin([(0, WGOLD["light"]), (1, WGOLD["dark"])], x, y - 10 * s, x + sx * 22 * s, y + 10 * s), stroke=OUTLINE, stroke_width=1.2)


@item(shadow=(64, 112, 36, 6))
def set_guardian_helm(d):
    with d.g(T(64, 70, 0, 1.4)):
        great_helm(d, w=46, h=56, pal=GUARD, trim=WGOLD)
        guardian_wings(d, 0, -18, 0.8)
        d.glow(0, -1, 20, AE_C, 0.6)
        d.path(rrect_path(-20, -3.6, 40, 5.2, 2.4), fill=AE_C, op=0.95)
        d.path(rrect_path(-18, -2.4, 36, 2.4, 1.2), fill="#ffffff")
        aether_gem(d, 0, -22, 3.6, glow=True)


@item(shadow=(64, 116, 44, 6))
def set_guardian_armor(d):
    with d.g(T(64, 64, 0, 1.45)):
        cuirass(d, w=66, h=66, pal=GUARD, trim=WGOLD)
        guardian_wings(d, 0, -8, 0.8)
        aether_line(d, [(0, -2), (0, 26)], w=1.1)
        aether_line(d, [(-18, 18), (0, 22), (18, 18)], w=0.9)
        aether_gem(d, 0, -8, 5)


@item(shadow=(64, 118, 34, 6))
def set_guardian_gloves(d):
    with d.g(T(66, 64, -8, 1.12)):
        glove(d, GUARD, WGOLD, plated=True)
        aether_line(d, [(-14, -9), (0, -12), (14, -9)], w=1.2)
        aether_gem(d, 0, 12, 4)
        aether_line(d, [(-20, 32), (20, 32)], w=1.0)


@item(shadow=(66, 112, 38, 6))
def set_guardian_boots(d):
    with d.g(T(58, 72, 0, 1.3)):
        boot(d, GUARD, WGOLD, plated=True)
        aether_line(d, [(-6, -40), (-6, -12)], w=1.1)
        guardian_wings(d, -2, -46, 0.45)
        aether_gem(d, -2, -8, 3)


@item(shadow=(64, 120, 36, 6))
def set_guardian_shield(d):
    with d.g(T(64, 62, 0, 1.4)):
        heater_shield(d, w=66, h=78, field=dict(dark="#0a2a3a", base="#1a5a70", light="#6ac8d8"), rim=GUARD, emblem=None, boss=WGOLD)
        guardian_wings(d, 0, -4, 0.9)
        aether_gem(d, 0, -2, 6)
        aether_line(d, [(0, 6), (0, 26)], w=1.2)


# ------------------------------------------------------------------------------------------ Starbound Sage set (mage)

STAR_TRIM = SILVER


@item(shadow=(64, 118, 44, 6))
def set_sage_hood(d):
    with d.g(T(64, 64, 0, 1.0)):
        hood(d, MIDNIGHT, STAR_TRIM, inner_glow=None, stars=True)
        d.path(smooth([(-12, -34), (0, -46), (12, -34)], closed=False), stroke="#c8d8ff", sw=1, op=0.6)
        crescent = circle_path(0, -44, 6) + " " + circle_path(3, -46, 5.2)
        d.path(crescent, fill="#e8f0ff", fill_rule="evenodd", stroke=OUTLINE, stroke_width=0.8)


@item(shadow=(64, 120, 44, 6))
def set_sage_robe(d):
    with d.g(T(64, 64, 0, 1.0)):
        robe(d, MIDNIGHT, STAR_TRIM, dict(dark="#1a1a3a", base="#4a4a8a", light="#a8a8e8"), stars=True)
        d.glow(0, -2, 8, "#a8c8ff", 0.8)
        d.path(poly(star_pts(0, -2, 4, 5, 1.6)), fill="#ffffff")


@item(shadow=(64, 118, 34, 6))
def set_sage_gloves(d):
    with d.g(T(66, 64, -8, 1.12)):
        glove(d, MIDNIGHT, STAR_TRIM, plated=False)
        d.sparkle(0, 6, 5, "#e8f0ff", 0.95, glow_color="#8ab0ff")
        d.sparkle(-10, -4, 2.5, "#e8f0ff", 0.8)
        d.sparkle(10, 14, 2.2, "#e8f0ff", 0.8)


@item(shadow=(66, 112, 38, 6))
def set_sage_boots(d):
    with d.g(T(58, 72, 0, 1.3)):
        boot(d, MIDNIGHT, STAR_TRIM, plated=False)
        d.sparkle(-4, -28, 3.4, "#e8f0ff", 0.95, glow_color="#8ab0ff")
        d.sparkle(20, 10, 2.4, "#e8f0ff", 0.8)


@item(shadow=(56, 120, 40, 6))
def set_sage_staff(d):
    with d.g(T(86, 28, 32, 1.12)):
        staff(d, H=94, thick=8, crystal_r=8, pal=dict(dark="#1a2a8a", base="#8ab0ff", light="#ffffff", glow="#8ab0ff"),
              wood=dict(dark="#0a0c20", base="#262c5a", light="#6a74b8"))
        crescent = circle_path(0, 0, 17) + " " + circle_path(5, -4, 15)
        d.path(crescent, fill="none", stroke=OUTLINE, stroke_width=2.4)
        d.path(crescent, fill=d.lin([(0, SILVER["light"]), (1, SILVER["dark"])], -17, -17, 17, 17), fill_rule="evenodd")
        for yy in (30, 60):
            d.path(f"M-4.5,{yy} L4.5,{yy + 1}", stroke=OUTLINE, sw=4)
            d.path(f"M-4.5,{yy} L4.5,{yy + 1}", stroke=SILVER["base"], sw=2.4)
    d.sparkle(62, 22, 4, "#ffffff", 0.9, glow_color="#8ab0ff")
    d.sparkle(104, 10, 3, "#ffffff", 0.8)


# ------------------------------------------------------------------------------------------ Aether uniques

def crystal_blade(d, L, W, tip=1.3):
    sh = -L + W * tip
    pts = [(-W / 2, 0), (-W * 0.55, sh * 0.5), (-W / 2, sh), (0, -L), (W / 2, sh), (W * 0.55, sh * 0.5), (W / 2, 0)]
    n = 6
    for i in range(n):
        d.glow(0, -L * (i + 0.5) / n, W * 1.25, AE_C, 0.32)
    d.path(poly(pts), stroke=OUTLINE, sw=4.4)
    d.path(poly([(-W / 2, 0), (-W * 0.55, sh * 0.5), (-W / 2, sh), (0, -L), (0, 0)]), fill=d.lin([(0, "#ffffff"), (1, "#8af0ff")], -W / 2, 0, 0, 0))
    d.path(poly([(0, 0), (0, -L), (W / 2, sh), (W * 0.55, sh * 0.5), (W / 2, 0)]), fill=d.lin([(0, "#3ac0dc"), (1, "#0a5a70")], 0, 0, W / 2, 0))
    # facet lines
    for t in (0.25, 0.5, 0.75):
        y = sh * t
        d.path(f"M{f(-W * 0.52)},{f(y + W * 0.3)} L0,{f(y)} L{f(W * 0.52)},{f(y + W * 0.3)}", stroke="#ffffff", sw=0.7, op=0.6)
    d.path(f"M0,-2 L0,{f(-L + 2)}", stroke="#ffffff", sw=1.0)


def white_hilt(d, W, grip_len):
    g = WGOLD
    d.shape(rrect_path(-W * 0.22, 0, W * 0.44, grip_len, 1.5), fill=d.lin([(0, "#e8f0ff"), (1, "#6a7a90")], -W * 0.22, 0, W * 0.22, 0), ow=2)
    for i in range(1, int(grip_len // 4)):
        d.path(f"M{f(-W * 0.22)},{f(i * 4)} L{f(W * 0.22)},{f(i * 4 + 1)}", stroke=AE_C, sw=0.8, op=0.8)
    guard = [(-W * 1.6, -W * 0.5), (-W * 0.5, -W * 0.1), (0, -W * 0.4), (W * 0.5, -W * 0.1), (W * 1.6, -W * 0.5), (W * 0.6, W * 0.35), (0, W * 0.2), (-W * 0.6, W * 0.35)]
    d.shape(smooth(guard, tension=0.4), fill=d.lin([(0, g["light"]), (0.5, g["base"]), (1, g["dark"])], 0, -W * 0.5, 0, W * 0.35), ow=2)
    aether_gem(d, 0, 0, W * 0.24, glow=False)
    d.glow(0, grip_len + W * 0.3, W * 0.8, AE_C, 0.8)
    d.path(poly([(0, grip_len - 1), (W * 0.3, grip_len + W * 0.3), (0, grip_len + W * 0.7), (-W * 0.3, grip_len + W * 0.3)]), fill=AE_HI, stroke=OUTLINE, stroke_width=1.2)


@item(shadow=(60, 116, 44, 6))
def aether_sword(d):
    with d.g(T(42, 86, 45, 1.12)):
        white_hilt(d, 13, 18)
        crystal_blade(d, 72, 13)
    motes(d, [(96, 22, 0.8), (104, 44, 0.6), (82, 14, 0.6)], AE_HI, glow_color=AE_C, size=2)


@item(shadow=(60, 118, 48, 6))
def aether_greatsword(d):
    with d.g(T(38, 90, 45, 0.98)):
        white_hilt(d, 20, 36)
        crystal_blade(d, 106, 20, tip=1.0)
    motes(d, [(100, 20, 0.9), (110, 40, 0.7), (86, 12, 0.6)], AE_HI, glow_color=AE_C, size=2)


@item(shadow=(56, 120, 40, 6))
def aether_staff(d):
    with d.g(T(86, 28, 32, 1.12)):
        staff(d, H=94, thick=8, crystal_r=1, pal=AE, wood=dict(dark="#5a6278", base="#dce4f0", light="#ffffff"))
        aether_line(d, [(0, 18), (1.5, 50), (-1, 88)], w=1.3)
        # floating crystal cluster above the prongs
        d.glow(0, -4, 24, AE_C, 0.8)
        for (x, y, r, st) in ((-6, 0, 4, 1.8), (6, 0, 4, 1.8), (0, -6, 6.5, 2.4)):
            crystal(d, x, y, r, AE, stretch=st, glow=False)
        orbit(d, 0, -4, 18, 6, -15)
        orbit(d, 0, -4, 15, 4.5, 60, w=1.0, op=0.8)


@item(shadow=(56, 114, 34, 6))
def aether_wand(d):
    with d.g(T(82, 34, 40, 1.5)):
        wand(d, H=60, thick=1.5, pal=AE)
        aether_line(d, [(0, 10), (0, 56)], w=1.2)
        d.glow(0, -4, 12, AE_C, 0.6)
        orbit(d, 0, -3, 9, 3, -30, w=0.8)
    d.sparkle(98, 20, 7, "#ffffff", 1.0, glow_color=AE_C)
    motes(d, [(106, 36, 0.7), (88, 12, 0.6)], AE_HI, glow_color=AE_C, size=2)


@item(shadow=(64, 112, 44, 6))
def aether_ring(d):
    with d.g("translate(64 64) scale(1.22) translate(-64 -64)"):
        ring_base(d, dict(dark="#6a7a90", base="#e8f0ff", light="#ffffff"), dict(dark="#06506a", base="#62e0f4", light="#ffffff"), AE_C,
                  stone_sides=6, runes=AE_C)
        d.glow(64, 48, 22, AE_C, 0.6)
        d.sparkle(64, 42, 6, "#ffffff", 0.95)


@item(shadow=None)
def aether_amulet(d):
    pendant_chain(d, dict(dark="#6a7a90", base="#e8f0ff", light="#ffffff"))
    cx, cy = 64, 92
    d.glow(cx, cy, 38, AE_C, 0.75)
    orbit(d, cx, cy, 30, 9, -20)
    orbit(d, cx, cy, 26, 7, 40, w=1.0, op=0.8)
    with d.g(f"rotate(0 {cx} {cy})"):
        crystal(d, cx, cy, 11, AE, stretch=2.0, glow=False)
    for a in (0, 120, 240):
        x, y = polar(cx, cy, 20, math.radians(a - 90))
        d.path(poly([(x, y - 4), (x + 2.6, y), (x, y + 4), (x - 2.6, y)]), fill=AE_HI, stroke=OUTLINE, stroke_width=0.8)
