"""Passive talent icons: round bezel on a full-bleed painted background. Keystones get a spiked gold ring,
minor attribute nodes a thin ring and a smaller emblem."""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, EL, STEEL, CRIMSON, GOLD, BRONZE, INDIGO, ARCANE, LEATHER, WOOD, BONE, OUTLINE, f, poly, smooth,
                    mix, lt, dk, ribbon, taper, arc_pts, bez, qbez, star_pts, ngon, jag_line, blob, teardrop, polar,
                    faceted, rrect_path, circle_path, lerp)
from bh_shapes import (T, sword, blade, heater_shield, heater_pts, tower_shield, flame, ice_shard, snowflake, bolt,
                       zig_bolt, rock, swirl, gust, wave, sun, void_orb, tendril, rune_ring, motes, slash_arc, fist,
                       banner, heart, hourglass, impact_star, cuirass, great_helm, crystal, staff, droplet, gem, smooth_pts)
from bh_frames import backdrop, vignette, talent_frame, KNIGHT_METAL, MAGE_METAL

TALENTS = {}
MAGE_BG = "#140e30"


def talent(cls, inner, haze=None, haze2=None, kind="normal", scale=None):
    def deco(fn):
        def build():
            d = Doc(name=fn.__name__)
            backdrop(d, inner, haze=haze, haze2=haze2, cy=64)
            s = scale or {"normal": 0.8, "keystone": 0.74, "minor": 0.66}[kind]
            with d.g(f"translate(64 64) scale({f(s)}) translate(-64 -64)"):
                fn(d)
            vignette(d, 0.55, cy=64)
            talent_frame(d, KNIGHT_METAL if cls == "knight" else MAGE_METAL, kind)
            return d
        TALENTS[fn.__name__] = build
        return fn
    return deco


BRIGHT_STEEL = dict(dark="#3a4250", base="#b4bfcc", light="#ffffff", glow="#e8f0ff")


def laurel(d: Doc, cx, cy, r, pal=GOLD, leaves=7, a_from=100, a_to=230):
    for side in (-1, 1):
        stem = []
        for i in range(leaves + 1):
            a = math.radians(90 + side * (a_from - 90) + side * (i / leaves) * (a_to - a_from))
            stem.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.path(poly(stem, closed=False), stroke=OUTLINE, sw=4)
        d.path(poly(stem, closed=False), stroke=pal["dark"], sw=1.8)
        for i in range(1, leaves + 1):
            x, y = stem[i]
            px, py = stem[i - 1]
            ang = math.degrees(math.atan2(y - py, x - px))
            for off in (-40, 40):
                with d.g(T(x, y, ang + 90 + off, 1)):
                    lf = smooth([(0, 0), (4.6, -8), (0, -17), (-4.6, -8)], tension=0.9)
                    d.path(lf, stroke=OUTLINE, sw=2.6)
                    d.path(lf, fill=d.lin([(0, pal["light"]), (1, pal["dark"])], -3, -12, 3, 0))


def chain(d: Doc, p0, p1, link=7, pal=STEEL):
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    n = int(L / (link * 1.35))
    ang = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
    for i in range(n + 1):
        t = i / max(n, 1)
        x, y = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
        with d.g(T(x, y, ang, 1)):
            if i % 2 == 0:
                d.ellipse(0, 0, link, link * 0.55, stroke=OUTLINE, stroke_width=5)
                d.ellipse(0, 0, link, link * 0.55, stroke=pal["base"], stroke_width=2.6)
                d.path(f"M{f(-link * 0.6)},{f(-link * 0.42)} L{f(link * 0.4)},{f(-link * 0.5)}", stroke=pal["light"], sw=1.0)
            else:
                d.rect(-link * 0.95, -1.8, link * 1.9, 3.6, fill=OUTLINE, rx=1.8)
                d.rect(-link * 0.9, -1.0, link * 1.8, 2.0, fill=pal["base"], rx=1.0)


def cloud(d: Doc, circles, top="#b8b0d0", bottom="#3a3060"):
    ys = [c[1] - c[2] for c in circles] + [c[1] + c[2] for c in circles]
    g = d.lin([(0, top), (1, bottom)], 0, min(ys), 0, max(ys))
    for (x, y, r) in circles:
        d.circle(x, y, r + 2.4, fill=OUTLINE)
    for (x, y, r) in circles:
        d.circle(x, y, r, fill=g)
    for (x, y, r) in circles:
        d.path(smooth(arc_pts(x, y, r * 0.8, math.radians(200), math.radians(290), 5), closed=False), stroke="#ffffff", sw=1.4, op=0.35)


def crescent(d: Doc, cx, cy, R, thick, pal):
    top, bot = (cx, cy - R), (cx, cy + R)
    r2 = (R * R + (R - thick) ** 2) / (2 * (R - thick)) if thick < R else R * 10
    dd = f"M{f(top[0])},{f(top[1])} A{f(R)},{f(R)} 0 0 0 {f(bot[0])},{f(bot[1])} A{f(r2)},{f(r2)} 0 0 1 {f(top[0])},{f(top[1])} Z"
    d.glow(cx, cy, R * 2, pal["glow"], 0.5)
    d.path(dd, stroke=OUTLINE, sw=4.4)
    d.path(dd, fill=d.rad([(0, "#ffffff"), (0.6, pal["light"]), (1, pal["base"])], cx - R * 0.5, cy - R * 0.3, R * 1.3))


# ------------------------------------------------------------------------------------------ knight-leaning


@talent("knight", "#3a0a12", haze="#a0182a")
def crit(d: Doc):
    impact_star(d, 90, 38, 30, "#ffffff", "#ff4a4a", n=10, inner=0.26)
    rng = random.Random(1)
    for i in range(8):
        a = rng.uniform(-math.pi, math.pi)
        x, y = polar(90, 38, rng.uniform(22, 34), a)
        d.path(teardrop(x, y, 2.4, 6, lean=math.cos(a) * 3), fill=CRIMSON["light"], stroke=OUTLINE, stroke_width=0.8)
    with d.g(T(40, 90, 45, 1.05)):
        sword(d, L=64, W=12, pal=BRIGHT_STEEL)


@talent("knight", "#2a1208", haze="#ff6a14", haze2="#3a5a8a")
def fire_res(d: Doc):
    with d.g(T(64, 66, 0, 1.25)):
        heater_shield(d, w=64, h=76, field=dict(dark="#101a2a", base="#24406a", light="#5a8ac0"), rim=STEEL, emblem=None)
    flame(d, 64, 78, 0.5, EL["fire"])
    d.circle(64, 64, 52, stroke="#8ad0ff", stroke_width=2, opacity=0.35)


@talent("knight", "#2a1e0a", haze="#b88a3a")
def sword_mastery(d: Doc):
    d.glow(64, 50, 50, "#ffe8a0", 0.35)
    laurel(d, 64, 64, 44, GOLD, leaves=7, a_from=95, a_to=250)
    with d.g(T(64, 86, 0, 1.12)):
        sword(d, L=64, W=13, pal=BRIGHT_STEEL)


@talent("knight", "#0e1a30", haze="#3a6ad0", haze2="#a0182a")
def block_mana(d: Doc):
    with d.g(T(64, 64, 0, 1.3)):
        heater_shield(d, w=64, h=76, field=CRIMSON, rim=STEEL, emblem=None)
    d.glow(64, 64, 30, "#3a8aff", 0.8)
    droplet(d, 64, 72, 13, dict(dark="#0a1a6a", base="#2a6ae8", light="#a8d8ff"))


@talent("knight", "#2a0e14", haze="#a0182a", haze2="#b88a3a")
def crit_cooldown(d: Doc):
    impact_star(d, 90, 34, 24, "#ffffff", "#ff4a4a", n=8, inner=0.28)
    hourglass(d, 58, 70, 1.25, GOLD, dict(dark="#6a0a14", base="#d02a3a", light="#ff8a8a"))


@talent("mage", mix(MAGE_BG, "#4a1408", 0.5), haze="#ff5a14")
def burning_spread(d: Doc):
    pal = EL["fire"]
    # ember arcs jumping from the big flame to the smaller ones
    for (x0, y0, x1, y1) in ((58, 60, 24, 84), (70, 60, 104, 84)):
        pts = qbez((x0, y0), ((x0 + x1) / 2, 20), (x1, y1), n=18)
        d.path(poly(pts, closed=False), stroke=pal["glow"], sw=6, op=0.25)
        motes(d, [(p[0], p[1], 0.6 + 0.5 * i / 18) for i, p in enumerate(pts[1::3])], "#ffd060", glow_color="#ff6a14", size=2.0, diamonds=False)
    flame(d, 24, 104, 0.5, pal)
    flame(d, 104, 104, 0.5, pal)
    flame(d, 64, 96, 0.95, pal)


@talent("mage", mix(MAGE_BG, "#0a3a5a", 0.6), haze="#6ad8ff")
def frozen_impact(d: Doc):
    pal = EL["ice"]
    d.glow(64, 64, 50, pal["glow"], 0.5)
    # ice block splitting
    cube_l = [(34, 44), (60, 34), (58, 62), (56, 96), (30, 84)]
    cube_r = [(66, 34), (94, 44), (98, 84), (72, 96), (70, 62)]
    faceted(d, cube_l, (46, 56), pal["dark"], pal["light"], ow=2.4)
    faceted(d, cube_r, (80, 56), pal["dark"], pal["light"], ow=2.4)
    for pts in (cube_l, cube_r):
        d.path(poly(pts), fill="#ffffff", op=0.12)
    impact_star(d, 64, 60, 20, "#ffffff", "#9eeeff", n=8, inner=0.25)
    for a, L in ((-150, 16), (-30, 14), (160, 12), (20, 12), (-90, 14), (100, 10)):
        x, y = polar(64, 64, 44, math.radians(a))
        with d.g(T(x, y, a + 90, 1)):
            ice_shard(d, L=L, W=6, pal=pal, ow=1.6)


@talent("knight", "#1a2028", haze="#6a7a90", haze2="#b88a3a")
def armor(d: Doc):
    with d.g(T(64, 66, 0, 1.2)):
        cuirass(d, w=66, h=64, pal=STEEL, trim=GOLD)


@talent("knight", "#300810", haze="#d0203a")
def vitality(d: Doc):
    d.glow(64, 64, 52, "#ff3048", 0.55)
    heart(d, 64, 66, 1.35, dict(dark="#5a0410", base="#d0182e", light="#ff8a9a"))
    # pulse line
    pts = [(14, 66), (40, 66), (48, 50), (56, 82), (64, 58), (70, 70), (76, 66), (114, 66)]
    d.path(poly(pts, closed=False), stroke="#ffe0e4", sw=3, op=0.9)


@talent("knight", "#300a0e", haze="#a0182a", haze2="#b88a3a")
def valor(d: Doc):
    d.glow(64, 50, 48, "#ffc060", 0.35)
    with d.g(T(64, 66, 0, 1.15)):
        banner(d, CRIMSON, GOLD)


@talent("knight", "#1e1a18", haze="#6a5a48", haze2="#a0182a")
def heavy_hands(d: Doc):
    for a in range(-150, -20, 26):
        p0, p1 = polar(64, 60, 40, math.radians(a)), polar(64, 60, 56, math.radians(a))
        d.path(ribbon([p0, p1], [5, 0.6]), fill="#ffd8a0", op=0.8)
    with d.g(T(64, 68, 0, 1.35)):
        fist(d, STEEL, GOLD, plated=True)


@talent("knight", "#1a1c22", haze="#5a6070", haze2="#b88a3a")
def bulwark(d: Doc):
    stone = dict(dark="#2a2a30", base="#7a7680", light="#c8c4cc")
    # stone keep tower with battlements
    tw = [(34, 36), (42, 36), (42, 28), (52, 28), (52, 36), (60, 36), (60, 28), (68, 28), (68, 36), (76, 36), (76, 28), (86, 28), (86, 36),
          (94, 36), (94, 28), (94, 40), (90, 44), (90, 110), (38, 110), (38, 44), (34, 40)]
    tw = [(34, 28), (44, 28), (44, 36), (54, 36), (54, 28), (64, 28), (64, 36), (74, 36), (74, 28), (84, 28), (84, 36), (94, 36), (94, 28),
          (94, 44), (88, 50), (88, 112), (40, 112), (40, 50), (34, 44)]
    d.path(poly(tw), stroke=OUTLINE, sw=5)
    d.path(poly(tw), fill=d.lin([(0, stone["light"]), (0.5, stone["base"]), (1, stone["dark"])], 34, 0, 94, 0))
    # brick courses
    for i, y in enumerate(range(56, 112, 9)):
        d.path(f"M40,{y} L88,{y}", stroke=stone["dark"], sw=1.2, op=0.8)
        for x in range(44 + (i % 2) * 6, 88, 12):
            d.path(f"M{x},{y} L{x},{y + 9}", stroke=stone["dark"], sw=1.0, op=0.7)
    d.path("M34,44 L94,44", stroke=stone["dark"], sw=2)
    # gate
    gate = "M54,112 L54,90 Q64,78 74,90 L74,112 Z"
    d.path(gate, fill="#0a0608", stroke=OUTLINE, stroke_width=2)
    for x in (58, 64, 70):
        d.path(f"M{x},{86 if x == 64 else 89} L{x},112", stroke="#6a6a70", sw=1.4)
    d.path("M55,98 L73,98 M55,106 L73,106", stroke="#6a6a70", sw=1.2)
    # windows glow
    for x in (52, 76):
        d.path(rrect_path(x - 2.5, 58, 5, 10, 2.5), fill="#ffb040")
    # small banner on top
    d.path("M64,28 L64,8", stroke=OUTLINE, sw=3.4)
    d.path("M64,28 L64,8", stroke=WOOD["light"], sw=1.4)
    d.path("M64,9 L80,13 L64,18 Z", fill=CRIMSON["base"], stroke=OUTLINE, stroke_width=1.2)
    d.path("M36,30 L36,110", stroke="#ffffff", sw=1.2, op=0.25)


@talent("knight", "#221418", haze="#a0182a", haze2="#6a7a90")
def counter(d: Doc):
    # circular return arrow
    pts = arc_pts(64, 64, 46, math.radians(200), math.radians(500), 40)
    d.path(ribbon(pts, taper(40, 9, 0.2, 1.0, peak=1.0)), stroke=OUTLINE, stroke_width=2.4)
    d.path(ribbon(pts, taper(40, 9, 0.2, 1.0, peak=1.0)), fill=GOLD["base"])
    end = pts[-1]
    tang = math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0])
    head = [polar(end[0], end[1], 12, tang), polar(end[0], end[1], 9, tang + 2.2), polar(end[0], end[1], 9, tang - 2.2)]
    d.shape(poly(head), fill=GOLD["light"], ow=2)
    with d.g(T(50, 88, 40, 0.95)):
        sword(d, L=58, W=11, pal=BRIGHT_STEEL)
    with d.g(T(78, 88, -40, 0.95)):
        sword(d, L=58, W=11, pal=BRIGHT_STEEL)
    impact_star(d, 64, 56, 12, "#ffffff", "#ffd070", n=8, inner=0.3)


@talent("knight", "#2a0e0c", haze="#a0182a", haze2="#ff8a2a")
def momentum(d: Doc):
    for i, y in enumerate((36, 50, 78, 92)):
        d.path(ribbon([(10, y), (40, y)], [0.5, 4]), fill="#ffd8b0", op=0.55)
    for i, x in enumerate((30, 56, 82)):
        pts = [(x, 30), (x + 22, 64), (x, 98), (x + 12, 98), (x + 34, 64), (x + 12, 30)]
        col = mix(CRIMSON["base"], GOLD["light"], i / 2)
        d.shape(poly(pts), fill=d.lin([(0, lt(col, 0.3)), (1, dk(col, 0.35))], x, 30, x, 98), ow=2.6)
        d.path(poly([(x + 3, 33), (x + 24, 64)], closed=False), stroke="#ffffff", sw=1.4, op=0.5)


# ------------------------------------------------------------------------------------------ mage-leaning


@talent("mage", mix(MAGE_BG, "#2a0e5a", 0.5), haze="#8a4ae0")
def arcane_mind(d: Doc):
    head = [(36, 62), (40, 40), (54, 26), (72, 24), (88, 34), (94, 48), (95, 56), (103, 68), (96, 71), (97, 76), (94, 79), (95, 86),
            (88, 92), (78, 92), (78, 104), (84, 122), (40, 122), (46, 102), (38, 86)]
    hd = smooth(head, tension=0.5)
    d.path(hd, stroke=OUTLINE, sw=5)
    d.path(hd, fill=d.lin([(0, "#0e0a24"), (0.7, "#2a2060"), (1, "#6a5ac8")], 36, 0, 104, 0))
    # rim light on the face side
    d.path(smooth([(88, 34), (94, 48), (95, 56), (103, 68), (96, 71), (97, 76), (94, 79), (95, 86), (88, 92)], closed=False, tension=0.5), stroke="#c8a8ff", sw=1.8, op=0.8)
    d.glow(64, 52, 30, "#b070ff", 0.9)
    rune_ring(d, 64, 52, 17, "#e0c8ff", width=1.4, ticks=12, inner=False)
    d.path(poly(star_pts(64, 52, 4, 11, 3)), fill="#ffffff")
    for (x, y, s) in ((44, 34, 3), (82, 36, 2.5), (50, 70, 2.2)):
        d.sparkle(x, y, s, "#f0e4ff", 0.9)


@talent("mage", mix(MAGE_BG, "#0a2a5a", 0.5), haze="#3a8aff")
def mana_flow(d: Doc):
    pal = dict(dark="#0a1a6a", base="#2a6ae8", light="#a8d8ff", glow="#4a9aff")
    d.glow(64, 64, 52, pal["glow"], 0.45)
    for k, (w, col, op) in enumerate(((22, pal["dark"], 0.9), (14, pal["base"], 1.0), (5, pal["light"], 0.9))):
        pts = bez((18, 104), (40, 20), (88, 108), (110, 24), n=40)
        d.path(ribbon(pts, taper(40, w, 0.1, 0.1)), fill=col, op=op, stroke=OUTLINE if k == 0 else None, stroke_width=2 if k == 0 else None)
    for (x, y, r) in ((30, 44, 5), (96, 88, 5.5), (60, 30, 3.5)):
        droplet(d, x, y, r, pal, ow=1.4)
    for (x, y, s) in ((76, 48, 3.5), (46, 90, 3)):
        d.sparkle(x, y, s, "#ffffff", 0.9, glow_color=pal["glow"])


@talent("mage", mix(MAGE_BG, "#2a1a4a", 0.4), haze="#8a4ae0", haze2="#ffe08a")
def elemental_focus(d: Doc):
    cx, cy = 64, 64
    d.circle(cx, cy, 40, stroke="#d8c8ff", stroke_width=1.6, opacity=0.5)
    for i, name in enumerate(("fire", "ice", "lightning", "earth")):
        a = -math.pi / 2 + i * math.pi / 2
        x, y = polar(cx, cy, 40, a)
        p = EL[name]
        d.path(poly([(cx, cy), (x, y)], closed=False), stroke=p["glow"], sw=5, op=0.35)
        d.glow(x, y, 20, p["glow"], 0.8)
        d.circle(x, y, 11, fill=d.rad([(0, "#ffffff"), (0.35, p["light"]), (0.75, p["base"]), (1, p["dark"])], x - 3, y - 3, 13), stroke=OUTLINE, stroke_width=2.2)
    crystal(d, cx, cy, 11, dict(dark="#4a3a8a", base="#c8b8ff", light="#ffffff", glow="#e0d0ff"), stretch=1.5)


@talent("mage", mix(MAGE_BG, "#2a1a5a", 0.5), haze="#b88aff", haze2="#ffe23a")
def conduit(d: Doc):
    pal = EL["lightning"]
    rng = random.Random(4)
    # crystal spire
    cr = dict(dark="#2a1a6a", base="#8a70e0", light="#f0e8ff", glow="#b88aff")
    spire = [(64, 14), (78, 40), (76, 96), (64, 110), (52, 96), (50, 40)]
    d.glow(64, 60, 50, cr["glow"], 0.6)
    faceted(d, spire, (60, 50), cr["dark"], cr["light"], ow=2.6)
    d.path("M64,14 L62,60 L64,110", stroke="#ffffff", sw=1, op=0.5)
    # lightning enters the tip and is channelled out through the base
    for (p0, p1, w) in (((22, 26), (64, 16), 7), ((106, 28), (64, 16), 6)):
        bolt(d, jag_line(p0, p1, 5, 5, rng), width=w, pal=pal)
    for (p0, p1, w) in (((64, 108), (26, 104), 6), ((64, 108), (102, 102), 6)):
        bolt(d, jag_line(p0, p1, 5, 5, rng), width=w, pal=pal)
    for y in (40, 62, 84):
        d.path(f"M54,{y} L74,{y - 4}", stroke="#fff4b0", sw=1.6, op=0.8)
    d.sparkle(64, 16, 9, "#ffffff", 1.0, glow_color=pal["glow"])
    d.glow(64, 108, 12, pal["glow"], 0.9)


@talent("mage", mix(MAGE_BG, "#0a3a5a", 0.6), haze="#9eeeff")
def permafrost(d: Doc):
    pal = EL["ice"]
    # frozen ground with spikes
    d.path("M4,98 L124,98 L124,128 L4,128 Z", fill=d.lin([(0, "#bfefff"), (1, "#1f5a7a")], 0, 98, 0, 128))
    for x, L, w in ((20, 22, 9), (34, 30, 10), (94, 30, 10), (108, 22, 9), (50, 16, 7), (78, 16, 7)):
        with d.g(T(x, 102, 0, 1)):
            ice_shard(d, L=L, W=w, pal=pal)
    snowflake(d, 64, 50, 34, pal, width=5)


@talent("mage", mix(MAGE_BG, "#4a1408", 0.55), haze="#ff5a14")
def pyromancy(d: Doc):
    rune_ring(d, 64, 64, 50, "#ffb060", width=2.2, ticks=18, seed=5)
    d.path(poly(ngon(64, 64, 42, 5)) , stroke="#ff8a3a", sw=1.2, op=0.5)
    d.path(poly(star_pts(64, 64, 5, 42, 16)), stroke="#ffb060", sw=1.4, op=0.6)
    flame(d, 64, 88, 0.95, EL["fire"])


@talent("mage", mix(MAGE_BG, "#2a1a5a", 0.5), haze="#8a5aff")
def storm(d: Doc):
    zig_bolt(d, 62, 92, 50, lean=0.15)
    cloud(d, [(36, 52, 16), (56, 40, 22), (80, 42, 20), (98, 56, 14), (66, 60, 16), (46, 62, 12), (86, 62, 12)])
    for x in (30, 44, 96, 108):
        d.path(f"M{x},78 L{x - 6},96", stroke="#9ab8ff", sw=1.6, op=0.7)


@talent("mage", mix(MAGE_BG, "#06304a", 0.6), haze="#30c4d4")
def tides(d: Doc):
    crescent(d, 58, 42, 26, 14, dict(dark="#6a7a9a", base="#b8d8f0", light="#f4fbff", glow="#b8e8ff"))
    pal = EL["water"]
    for k, y in enumerate((80, 96)):
        pts = [(4, y + 8)]
        for i in range(9):
            x = 4 + i * 15
            pts += [(x + 4, y - 2 + (k * 3)), (x + 10, y + 6)]
        pts += [(124, y + 30), (4, y + 30)]
        dd = smooth(pts, tension=0.6)
        d.path(dd, stroke=OUTLINE, sw=4)
        d.path(dd, fill=d.lin([(0, pal["light"] if k == 0 else pal["base"]), (1, pal["dark"])], 0, y - 4, 0, y + 30))
        d.path(smooth(pts[1:-2], closed=False, tension=0.6), stroke="#eafcff", sw=1.6, op=0.8)
    d.path("M58,70 L54,80 M60,74 L62,86", stroke="#e0f4ff", sw=2, op=0.5)


@talent("mage", mix(MAGE_BG, "#1a0626", 0.6), haze="#6a1a8a")
def shadow(d: Doc):
    pal = EL["dark"]
    for i in range(6):
        a = i * math.pi / 3 + 0.3
        p = [polar(64, 64, 20, a), polar(64, 64, 34, a + 0.4), polar(64, 64, 44, a + 0.1), polar(64, 64, 54, a + 0.6)]
        tendril(d, p[::-1], 9, pal)
    void_orb(d, 64, 64, 24, pal)
    d.path(smooth(arc_pts(64, 64, 18, math.radians(200), math.radians(260), 5), closed=False), stroke="#e0b0ff", sw=2, op=0.6)


@talent("mage", mix(MAGE_BG, "#4a3a10", 0.55), haze="#ffe08a")
def radiance(d: Doc):
    sun(d, 64, 64, 20, EL["light"], rays=12, ray_len=2.3)


# ------------------------------------------------------------------------------------------ keystones


@talent("knight", "#20100c", haze="#a0182a", haze2="#6a5a48", kind="keystone")
def keystone_juggernaut(d: Doc):
    d.glow(64, 70, 50, "#ff5030", 0.45)
    with d.g(T(64, 74, 0, 1.25)):
        great_helm(d, w=46, h=54, pal=STEEL, trim=GOLD, horns=True)
    for x in (52, 76):
        d.glow(x, 73, 5, "#ff4020", 1.0)


@talent("knight", "#141820", haze="#5a6a80", haze2="#b88a3a", kind="keystone")
def keystone_unbreakable(d: Doc):
    with d.g(T(64, 64, 0, 1.35)):
        heater_shield(d, w=64, h=76, field=dict(dark="#20242c", base="#4a5260", light="#8a94a4"), rim=GOLD, emblem=None)
    chain(d, (22, 34), (106, 98), link=7)
    chain(d, (106, 34), (22, 98), link=7)
    d.glow(64, 66, 22, "#ffd070", 0.9)
    gem(d, 64, 66, 11, dict(dark="#6a3a0a", base="#ffb030", light="#fff4c0"), sides=6)


@talent("mage", mix(MAGE_BG, "#2a0e5a", 0.5), haze="#a060ff", haze2="#ffe08a", kind="keystone")
def keystone_archmage(d: Doc):
    cx, cy = 64, 40
    d.glow(cx, cy, 50, "#a060ff", 0.6)
    with d.g(T(cx, cy, 0, 1.6)):
        staff(d, H=56, pal=dict(dark="#2a0e5a", base="#b080ff", light="#ffffff", glow="#c090ff"))
    for k, (rx, ry, a) in enumerate(((36, 10, -25), (36, 10, 25), (34, 12, 90))):
        with d.g(T(cx, cy, a, 1)):
            d.ellipse(0, 0, rx, ry, stroke=OUTLINE, stroke_width=3.4, opacity=0.7)
            d.ellipse(0, 0, rx, ry, stroke="#e0c8ff", stroke_width=1.6)
            d.circle(rx, 0, 3.2, fill="#ffffff", stroke=OUTLINE, stroke_width=1)
            d.glow(rx, 0, 7, "#c090ff", 0.9)


@talent("mage", mix(MAGE_BG, "#2a1a3a", 0.4), haze="#ff5a14", haze2="#6ad8ff", kind="keystone")
def keystone_elemental_overload(d: Doc):
    cx, cy, r = 64, 64, 32
    names = ("fire", "lightning", "ice", "earth")
    for i, name in enumerate(names):
        a0 = -math.pi / 2 + i * math.pi / 2
        p = EL[name]
        mid = a0 + math.pi / 4
        x, y = polar(cx, cy, 44, mid)
        d.glow(x, y, 34, p["glow"], 0.7)
        # burst rays
        for k in (-0.25, 0, 0.25):
            p0, p1 = polar(cx, cy, r + 2, mid + k), polar(cx, cy, r + 22 - abs(k) * 20, mid + k)
            d.path(ribbon([p0, p1], [6, 0.5]), fill=p["light"], op=0.9)
    d.circle(cx, cy, r + 2.6, fill=OUTLINE)
    for i, name in enumerate(names):
        a0 = -math.pi / 2 + i * math.pi / 2
        p = EL[name]
        pts = [(cx, cy)] + arc_pts(cx, cy, r, a0, a0 + math.pi / 2, 10)
        x, y = polar(cx, cy, r * 0.5, a0 + math.pi / 4)
        d.path(poly(pts), fill=d.rad([(0, p["light"]), (0.6, p["base"]), (1, p["dark"])], x, y, r * 0.9))
    rng = random.Random(3)
    for i in range(4):
        a = -math.pi / 2 + i * math.pi / 2
        cr = jag_line((cx, cy), polar(cx, cy, r + 1, a), 4, 3, rng)
        d.path(poly(cr, closed=False), stroke="#1a0a10", sw=3)
        d.path(poly(cr, closed=False), stroke="#ffffff", sw=1.4)
    d.glow(cx, cy, 16, "#ffffff", 1.0)
    d.path(smooth(arc_pts(cx, cy, r * 0.8, math.radians(200), math.radians(250), 5), closed=False), stroke="#ffffff", sw=2, op=0.6)


# ------------------------------------------------------------------------------------------ minor attribute nodes

def _minor(attr, cls, inner, haze):
    def fn(d: Doc):
        import icons_badges
        icons_badges.ATTR_DRAW[attr](d)
    fn.__name__ = f"minor_{attr[:3]}"
    return talent(cls, inner, haze=haze, kind="minor")(fn)


for _attr, _cls, _inner, _haze in (("strength", "knight", "#2a0e0c", "#a0182a"), ("agility", "knight", "#10241a", "#6ab88a"),
                                   ("intelligence", "mage", "#140e34", "#6a5ae0"), ("wisdom", "mage", "#0e1a30", "#4a8ad0"),
                                   ("spirit", "mage", "#0a2428", "#6ae0d8"), ("dexterity", "knight", "#241a0a", "#c8962e")):
    _minor(_attr, _cls, _inner, _haze)
