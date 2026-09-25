"""Class crests (256 viewBox), main-menu logo emblem and filigree ornaments."""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, EL, STEEL, CRIMSON, GOLD, BRONZE, INDIGO, ARCANE, LEATHER, WOOD, BONE, OUTLINE, f, poly, smooth,
                    mix, lt, dk, ribbon, taper, arc_pts, bez, qbez, star_pts, ngon, jag_line, blob, teardrop, polar,
                    faceted, rrect_path, circle_path, lerp)
from bh_shapes import (T, sword, greatsword, heater_shield, heater_pts, great_helm, staff, crystal, gem, rune_ring, sun,
                       motes, smooth_pts, flame, snowflake, zig_bolt, rock)

CLASSES, EMBLEM = {}, {}
BRIGHT_STEEL = dict(dark="#3a4250", base="#b4bfcc", light="#ffffff", glow="#e8f0ff")


def reg(table, name, w, h):
    def deco(fn):
        def build():
            d = Doc(w, h, name=name)
            fn(d)
            return d
        table[name] = build
        return fn
    return deco


def mantling(d: Doc, side, pal=CRIMSON, lining=GOLD):
    """Flowing heraldic cloth flourish on one side (side=-1 left, 1 right), local around the crest centre."""
    s = side
    for k, (w, col) in enumerate(((22, pal), (12, lining))):
        pts = smooth_pts([(s * 30, -70), (s * 78, -56), (s * 96, -10), (s * 82, 40), (s * 100, 76), (s * 70, 92)], 36)
        ws = taper(36, w, 0.4, 0.1, peak=0.35)
        dd = ribbon(pts, ws)
        if k == 0:
            d.path(dd, stroke=OUTLINE, sw=5)
        d.path(dd, fill=d.lin([(0, col["light"]), (0.5, col["base"]), (1, col["dark"])], s * 30, -70, s * 90, 90))
    for (a, b) in (((s * 60, -58), (s * 88, -20)), ((s * 90, 30), (s * 94, 70))):
        d.path(poly([a, b], closed=False), stroke=pal["dark"], sw=2, op=0.6)


@reg(CLASSES, "knight", 256, 256)
def knight(d: Doc):
    cx, cy = 128, 140
    d.glow(cx, cy, 124, "#a0182a", 0.45)
    with d.g(T(cx, cy)):
        mantling(d, -1)
        mantling(d, 1)
    # crossed swords behind the shield
    for a in (-38, 38):
        with d.g(T(cx + (1 if a > 0 else -1) * -44, cy + 70, a, 1.55)):
            sword(d, L=110, W=13, pal=BRIGHT_STEEL)
    with d.g(T(cx, cy + 8, 0, 1.0)):
        heater_shield(d, w=124, h=146, field=CRIMSON, rim=STEEL, emblem=None, ow=3.2)
        # silver chevron + gold crown charge
        d.shape(poly([(-46, 30), (0, -6), (46, 30), (46, 50), (0, 14), (-46, 50)]),
                fill=d.lin([(0, "#ffffff"), (0.5, STEEL["base"]), (1, STEEL["dark"])], 0, -6, 0, 50), ow=2.4)
        crown = [(-26, -18), (-26, -46), (-14, -32), (0, -54), (14, -32), (26, -46), (26, -18)]
        d.shape(poly(crown), fill=d.lin([(0, GOLD["light"]), (0.5, GOLD["base"]), (1, GOLD["dark"])], 0, -54, 0, -18), ow=2.4)
        for (x, y) in ((-26, -46), (0, -54), (26, -46)):
            d.circle(x, y, 3.6, fill=GOLD["light"], stroke=OUTLINE, stroke_width=1.4)
        d.path("M-24,-24 L24,-24", stroke=GOLD["dark"], sw=2)
        for x in (-12, 0, 12):
            d.circle(x, -21, 2.4, fill=CRIMSON["light"] if x else "#6ab0ff", stroke=OUTLINE, stroke_width=0.8)
        d.path(poly([(0, 58), (-6, 68), (0, 78), (6, 68)]), fill=GOLD["base"], stroke=OUTLINE, stroke_width=1.4)
    # great helm crowning the shield
    with d.g(T(cx, 50, 0, 1.25)):
        great_helm(d, w=46, h=54, pal=STEEL, trim=GOLD)
    # plume
    for i, (dx, col) in enumerate(((-6, CRIMSON["dark"]), (0, CRIMSON["base"]), (6, CRIMSON["light"]))):
        pts = qbez((cx + dx * 0.3, 18), (cx + 20 + dx, -4 + 12), (cx + 46 + dx, 22), n=16)
        d.path(ribbon(pts, taper(16, 10, 0.6, 0.0, peak=0.2)), fill=col["base"] if isinstance(col, dict) else col, stroke=OUTLINE, stroke_width=1.2)


@reg(CLASSES, "mage", 256, 256)
def mage(d: Doc):
    cx, cy = 128, 128
    d.glow(cx, cy, 128, "#6a3ad0", 0.55)
    d.circle(cx, cy, 112, fill=d.rad([(0, "#2a1a6a", 0.9), (0.7, "#140e30", 0.95), (1, "#07051a", 0.95)], cx, cy - 10, 112))
    d.circle(cx, cy, 116, stroke=OUTLINE, stroke_width=6)
    d.circle(cx, cy, 114, stroke=d.lin([(0, "#ece4ff"), (0.5, "#8c80c8"), (1, "#2a2050")], 30, 20, 226, 236), stroke_width=5)
    rune_ring(d, cx, cy, 102, "#c8a8ff", width=3, ticks=28, seed=11)
    tri1 = ngon(cx, cy, 82, 3)
    tri2 = ngon(cx, cy, 82, 3, rot0=math.pi / 2)
    d.path(poly(tri1) + " " + poly(tri2), stroke="#9a78f0", sw=2.2, op=0.7)
    # element orbs at the diagonals
    for i, name in enumerate(("fire", "ice", "lightning", "earth")):
        a = -3 * math.pi / 4 + i * math.pi / 2
        x, y = polar(cx, cy, 84, a)
        p = EL[name]
        d.glow(x, y, 22, p["glow"], 0.8)
        d.circle(x, y, 11, fill=d.rad([(0, "#ffffff"), (0.35, p["light"]), (0.8, p["base"]), (1, p["dark"])], x - 3, y - 3, 13), stroke=OUTLINE, stroke_width=2.4)
    # crescent moon cradling a star
    R, th = 52, 22
    top, bot = (cx - 8, cy - 18 - R), (cx - 8, cy - 18 + R)
    r2 = (R * R + (R - th) ** 2) / (2 * (R - th))
    dd = f"M{f(top[0])},{f(top[1])} A{f(R)},{f(R)} 0 0 0 {f(bot[0])},{f(bot[1])} A{f(r2)},{f(r2)} 0 0 1 {f(top[0])},{f(top[1])} Z"
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.rad([(0, "#ffffff"), (0.5, "#e0d0ff"), (1, "#8a70d0")], cx - 40, cy - 40, 70))
    # staff through the centre
    with d.g(T(cx + 10, cy - 50, 0, 1.55)):
        staff(d, H=100, pal=dict(dark="#2a0e5a", base="#b080ff", light="#ffffff", glow="#c090ff"), thick=8, crystal_r=9)
    d.path(poly(star_pts(cx - 30, cy - 12, 4, 16, 4)), fill="#ffffff", stroke=OUTLINE, stroke_width=1.4)
    for (x, y, s) in ((cx - 58, cy + 30, 6), (cx + 50, cy + 40, 5), (cx + 44, cy - 50, 4)):
        d.sparkle(x, y, s, "#f0e4ff", 0.9, glow_color="#a060ff")


# ------------------------------------------------------------------------------------------ logo emblem

@reg(EMBLEM, "logo_emblem", 512, 512)
def logo_emblem(d: Doc):
    cx, cy = 256, 256
    # radiant backdrop (transparent outside)
    d.glow(cx, cy, 250, "#ffcf70", 0.45, core="#fff4d0")
    rays = []
    rng = random.Random(7)
    for i in range(36):
        a = i * math.tau / 36 + rng.uniform(-0.03, 0.03)
        L = 236 if i % 2 == 0 else 176
        w = 0.05 if i % 2 == 0 else 0.035
        rays.append(poly([polar(cx, cy, 60, a - w), polar(cx, cy, L, a), polar(cx, cy, 60, a + w)]))
    d.path(" ".join(rays), fill=d.rad([(0, "#fff8e0", 0.9), (0.5, "#ffd070", 0.45), (1, "#ffb040", 0.0)], cx, cy, 236))
    # halo rings
    d.circle(cx, cy, 196, stroke="#000000", stroke_width=10, opacity=0.35)
    d.circle(cx, cy, 196, stroke=d.lin([(0, "#ffe9a0"), (0.5, "#b88a3a"), (1, "#4a3010")], 60, 60, 452, 452), stroke_width=5)
    rune_ring(d, cx, cy, 184, "#ffe9a0", width=3, ticks=36, seed=21, op=0.8)
    # crossed sword and staff behind the crest
    with d.g(T(cx - 112, cy + 112, 45, 2.3)):
        sword(d, L=170, W=14, pal=BRIGHT_STEEL)
    with d.g(T(cx - 146, cy - 146, -45, 2.0)):
        staff(d, H=205, pal=dict(dark="#2a0e5a", base="#b080ff", light="#ffffff", glow="#c090ff"), thick=8, crystal_r=9)
    # cracked crest, split in two halves with light pouring from the crack
    pts = heater_pts(236, 272)
    pts = [(x, y + 6) for x, y in pts]
    rng = random.Random(3)
    crack = jag_line((6, pts[2][1] + 2), (-2, pts[8][1]), 9, 16, rng)
    left = crack + [pts[9], pts[10], pts[11], pts[0], pts[1]]
    right = crack + [pts[7], pts[6], pts[5], pts[4], pts[3]]
    stone = dict(dark="#14101c", base="#3a3448", light="#8a84a0")
    with d.g(T(cx, cy)):
        d.path(poly([(x, y) for x, y in crack], closed=False), stroke="#ffe6a0", sw=60, op=0.25)
        for hp, dx in ((left, -9), (right, 9)):
            with d.g(T(dx, 0)):
                d.path(poly(hp), stroke=OUTLINE, sw=9)
                d.path(poly(hp), fill=d.lin([(0, stone["light"]), (0.45, stone["base"]), (1, stone["dark"])], -118, -140, 118, 140))
                # gold rim inset
                inner = [(x * 0.9, y * 0.9 - 3) for x, y in hp]
                d.path(poly(inner), stroke=GOLD["base"], sw=4, op=0.9)
                d.path(poly(inner), stroke=GOLD["light"], sw=1.2, op=0.8)
                # etched chevron detail
                for k in range(3):
                    y = -70 + k * 24
                    d.path(f"M{f(-80 if dx < 0 else 80)},{f(y + 40)} L{f(-8 if dx < 0 else 8)},{f(y)}", stroke=stone["dark"], sw=4, op=0.7)
                    d.path(f"M{f(-80 if dx < 0 else 80)},{f(y + 38)} L{f(-8 if dx < 0 else 8)},{f(y - 2)}", stroke=stone["light"], sw=1.4, op=0.5)
        # hairline branch cracks
        for i in (2, 4, 6):
            x, y = crack[i]
            for s in (-1, 1):
                br = jag_line((x + s * 9, y), (x + s * 9 + s * rng.uniform(30, 60), y + rng.uniform(-30, 30)), 3, 5, rng)
                d.path(poly(br, closed=False), stroke="#0a0610", sw=4)
                d.path(poly(br, closed=False), stroke="#ffd070", sw=1.6, op=0.9)
        # the light in the crack
        cp = poly(crack, closed=False)
        d.path(cp, stroke="#ffb040", sw=22, op=0.55)
        d.path(cp, stroke="#fff0b0", sw=11)
        d.path(cp, stroke="#ffffff", sw=4)
    # radiant core
    d.glow(cx, cy - 6, 110, "#fff0b0", 0.9, core="#ffffff")
    d.path(poly(star_pts(cx, cy - 6, 4, 70, 9)), fill="#ffffff", op=0.95)
    d.path(poly(star_pts(cx, cy - 6, 4, 38, 7, rot0=-math.pi / 4)), fill="#fff4c0", op=0.9)
    d.circle(cx, cy - 6, 20, fill=d.rad([(0, "#ffffff"), (0.6, "#fff4c0"), (1, "#ffd070")], cx - 4, cy - 10, 22), stroke="#b88a3a", stroke_width=2)


# ------------------------------------------------------------------------------------------ ornaments

def scroll_curl(d: Doc, x, y, r, a0, turns, width, cw, g=GOLD, n=34):
    pts = []
    for i in range(n):
        t = i / (n - 1)
        a = a0 + (1 if cw else -1) * turns * math.tau * t
        rr = r * (1 - 0.72 * t)
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    ws = taper(n, width, 0.9, 0.35, peak=0.15)
    dd = ribbon(pts, ws)
    d.path(dd, stroke=OUTLINE, sw=1.8)
    d.path(dd, fill=d.lin([(0, g["light"]), (0.5, g["base"]), (1, g["dark"])], x - r, y - r, x + r, y + r))
    d.circle(pts[-1][0], pts[-1][1], width * 0.45, fill=g["light"], stroke=OUTLINE, stroke_width=0.8)


def ornament_gem(d: Doc, x, y, rx, ry, pal=CRIMSON):
    pts = [(x, y - ry), (x + rx, y), (x, y + ry), (x - rx, y)]
    d.path(poly(pts), stroke=OUTLINE, sw=3)
    d.path(poly([(x, y - ry), (x + rx, y), (x, y)]), fill=pal["light"])
    d.path(poly([(x + rx, y), (x, y + ry), (x, y)]), fill=pal["dark"])
    d.path(poly([(x, y + ry), (x - rx, y), (x, y)]), fill=pal["base"])
    d.path(poly([(x - rx, y), (x, y - ry), (x, y)]), fill=lt(pal["light"], 0.3))


@reg(EMBLEM, "ornament_divider", 512, 32)
def ornament_divider(d: Doc):
    cy = 16
    g = GOLD
    for s in (-1, 1):
        # tapered main line
        pts = [(256 + s * 30, cy), (256 + s * 250, cy)]
        line = ribbon(smooth_pts([(256 + s * 30, cy), (256 + s * 140, cy), (256 + s * 250, cy)], 12), taper(12, 4.4, 1.0, 0.0, peak=0.0))
        d.path(line, stroke=OUTLINE, sw=1.6)
        d.path(line, fill=d.lin([(0, g["light"]), (1, g["dark"])], 0, cy - 2, 0, cy + 2))
        # twin scroll curls near the centre
        scroll_curl(d, 256 + s * 44, cy - 5, 9, math.pi / 2 if s > 0 else math.pi / 2, 0.8, 3.2, cw=s < 0)
        scroll_curl(d, 256 + s * 64, cy + 5, 8, -math.pi / 2, 0.8, 3.0, cw=s > 0)
        # small diamonds along the line
        for k, xo in enumerate((96, 150, 200)):
            r = 3.6 - k * 0.8
            d.path(poly([(256 + s * xo, cy - r * 1.4), (256 + s * xo + r, cy), (256 + s * xo, cy + r * 1.4), (256 + s * xo - r, cy)]),
                   fill=g["light"], stroke=OUTLINE, stroke_width=1)
        # leaf flourishes
        for xo, up in ((118, -1), (176, 1)):
            x0 = 256 + s * xo
            lf = qbez((x0, cy), (x0 + s * 6, cy + up * 9), (x0 + s * 18, cy + up * 8), n=10)
            d.path(ribbon(lf, taper(10, 3.2, 0.3, 0.0, peak=0.3)), fill=g["base"], stroke=OUTLINE, stroke_width=0.8)
    ornament_gem(d, 256, cy, 11, 13, CRIMSON)
    d.circle(256, cy, 17, stroke=OUTLINE, stroke_width=3.6)
    d.circle(256, cy, 17, stroke=d.lin([(0, g["light"]), (1, g["dark"])], 239, 0, 273, 32), stroke_width=1.8)


@reg(EMBLEM, "ornament_corner", 64, 64)
def ornament_corner(d: Doc):
    g = GOLD
    # two tapered arms along the top and left edges
    for pts in (smooth_pts([(8, 7), (30, 7), (62, 6)], 12), smooth_pts([(7, 8), (7, 30), (6, 62)], 12)):
        dd = ribbon(pts, taper(12, 4.6, 1.0, 0.0, peak=0.0))
        d.path(dd, stroke=OUTLINE, sw=1.6)
        d.path(dd, fill=d.lin([(0, g["light"]), (1, g["dark"])], 0, 0, 64, 64))
    # inner arms
    for pts in (smooth_pts([(14, 14), (30, 14), (44, 13)], 10), smooth_pts([(14, 14), (14, 30), (13, 44)], 10)):
        dd = ribbon(pts, taper(10, 2.6, 1.0, 0.0, peak=0.0))
        d.path(dd, stroke=OUTLINE, sw=1.2)
        d.path(dd, fill=g["base"])
    # scroll curls
    scroll_curl(d, 30, 22, 7, math.pi, 0.85, 2.8, cw=True)
    scroll_curl(d, 22, 30, 7, -math.pi / 2, 0.85, 2.8, cw=False)
    ornament_gem(d, 10, 10, 5.5, 5.5, CRIMSON)
    d.circle(10, 10, 7.6, stroke=OUTLINE, stroke_width=2.6)
    d.circle(10, 10, 7.6, stroke=g["base"], stroke_width=1.2)
