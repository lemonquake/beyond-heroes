"""Active skill icons (knight + mage). Square framed painted emblems, 128x128."""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, EL, STEEL, CRIMSON, GOLD, BRONZE, INDIGO, ARCANE, LEATHER, WOOD, BONE, OUTLINE, f, poly, smooth,
                    mix, lt, dk, ribbon, taper, arc_pts, bez, qbez, star_pts, ngon, jag_line, blob, teardrop, polar,
                    faceted, rrect_path, circle_path)
from bh_shapes import (T, sword, greatsword, blade, heater_shield, tower_shield, flame, ice_shard, snowflake, bolt,
                       zig_bolt, rock, swirl, gust, wave, sun, void_orb, tendril, rune_ring, motes, slash_arc,
                       humanoid_robed, horn, impact_star, eye, smooth_pts, crystal)
from bh_frames import backdrop, vignette, skill_frame, KNIGHT_METAL, MAGE_METAL

SKILLS = {}


def skill(cls, inner, haze=None, haze2=None):
    def deco(fn):
        def build():
            d = Doc(name=fn.__name__)
            backdrop(d, inner, haze=haze, haze2=haze2)
            fn(d)
            vignette(d, 0.7)
            skill_frame(d, KNIGHT_METAL if cls == "knight" else MAGE_METAL)
            return d
        SKILLS[fn.__name__] = build
        return fn
    return deco


BRIGHT_STEEL = dict(dark="#3a4250", base="#b4bfcc", light="#ffffff", glow="#e8f0ff")
SLASH_WHITE = dict(dark="#6a0a18", base="#f0e4e8", light="#ffffff", glow="#ff5a6a")

# ------------------------------------------------------------------------------------------------ knight


@skill("knight", "#3a0c14", haze="#8a1a24")
def cleave(d: Doc):
    cx, cy = 60, 80
    slash_arc(d, cx, cy, 46, math.radians(168), math.radians(338), 20, SLASH_WHITE)
    slash_arc(d, cx, cy, 34, math.radians(185), math.radians(320), 8, SLASH_WHITE, glow=False)
    # sword at the leading edge of the sweep
    with d.g(T(cx + 6, cy - 2, 58, 1.0)):
        sword(d, L=58, W=12, pal=BRIGHT_STEEL)
    # blood / spark spray off the tip
    rng = random.Random(4)
    for i in range(7):
        x, y = 104 + rng.uniform(-6, 10), 44 + rng.uniform(-14, 18)
        d.path(teardrop(x, y, 2.2 - i * 0.15, 6, lean=4), fill=CRIMSON["light"] if i % 2 else CRIMSON["base"], stroke=OUTLINE, stroke_width=0.8)


@skill("knight", "#1a2230", haze="#4a5a78")
def shield_bash(d: Doc):
    # speed streaks behind
    for i, (y, L) in enumerate(((40, 30), (56, 40), (72, 36), (88, 26))):
        d.path(ribbon([(10, y), (10 + L, y - 4)], [0.5, 5]), fill="#cfd8e8", op=0.5)
    # impact burst at the shield face
    impact_star(d, 94, 58, 30, "#ffffff", "#ffd070", n=9, inner=0.3)
    for a in range(-60, 61, 30):
        p0 = polar(94, 58, 22, math.radians(a))
        p1 = polar(94, 58, 36, math.radians(a))
        d.path(ribbon([p0, p1], [4, 0.5]), fill="#fff4c0")
    with d.g(T(58, 66, -14, 1.0)):
        heater_shield(d, w=60, h=72, field=CRIMSON, rim=STEEL, emblem="boss", boss=GOLD)


@skill("knight", "#2a1a0c", haze="#7a4a1a", haze2="#8a1a24")
def leap_slam(d: Doc):
    # leap trajectory arc
    tr = qbez((14, 96), (20, 10), (62, 26), n=26)
    d.path(ribbon(tr, taper(26, 16, 0.0, 1.0, peak=1.0)), fill="#ffe0b0", op=0.25)
    d.path(ribbon(tr, taper(26, 7, 0.0, 1.0, peak=1.0)), fill="#fff4dc", op=0.8)
    # ground and shockwave
    d.path("M4,96 L124,96 L124,124 L4,124 Z", fill=d.lin([(0, "#4a3018"), (1, "#140a04")], 0, 96, 0, 124))
    d.glow_ellipse(64, 97, 58, 12, "#ffb050", 0.9)
    d.ellipse(64, 97, 46, 8, stroke="#ffe0a0", stroke_width=2.6, opacity=0.8)
    d.ellipse(64, 97, 30, 5, stroke="#fff4dc", stroke_width=2, opacity=0.9)
    rng = random.Random(7)
    for a in (-170, -150, -30, -12, 160, 20):
        pts = jag_line((64, 99), polar(64, 99, 44, math.radians(a)), 5, 3, rng)
        pts = [(x, 96 + (y - 96) * 0.35 + 3) for x, y in pts]
        d.path(poly(pts, closed=False), stroke="#140804", sw=2.4)
        d.path(poly(pts, closed=False), stroke="#ff9a30", sw=1.0, op=0.9)
    # debris
    for i, (x, y, r) in enumerate(((30, 80, 5), (98, 76, 6), (44, 66, 3.5), (86, 62, 4), (110, 88, 3.5), (20, 90, 3))):
        rock(d, x, y, r, EL["earth"], seed=i + 3, n=6, ow=1.4)
    # sword plunging point-first into the ground
    with d.g(T(66, 30, 180, 1.1)):
        greatsword(d, L=58, W=15, pal=BRIGHT_STEEL)
    impact_star(d, 66, 96, 16, "#ffffff", "#ffc060", n=8, inner=0.3)


@skill("knight", "#1c2028", haze="#5a6a80", haze2="#8a1a24")
def whirlwind(d: Doc):
    cx, cy = 64, 66
    d.glow(cx, cy, 56, "#b8c8ff", 0.45)
    # a vortex of slash trails at several radii
    for i, (r, a0, a1, w) in enumerate(((50, 200, 340, 14), (50, 20, 160, 14), (36, 250, 400, 10), (36, 70, 220, 10), (22, 300, 480, 7))):
        slash_arc(d, cx, cy, r, math.radians(a0), math.radians(a1), w, SLASH_WHITE if i < 2 else BRIGHT_STEEL, glow=i < 2)
    # two blades swinging round a common centre
    for a in (-30, 150):
        gx, gy = polar(cx, cy, 6, math.radians(a + 90))
        with d.g(T(gx, gy, a + 90 + 180 - 90, 0.92)):
            sword(d, L=50, W=11, pal=BRIGHT_STEEL, hilt=GOLD)
    d.circle(cx, cy, 6, fill=d.rad([(0, "#ffffff"), (1, "#8a9ab8")], cx - 1, cy - 1, 7), stroke=OUTLINE, stroke_width=1.8)


@skill("knight", "#3a0c10", haze="#a0182a", haze2="#8a5a1a")
def war_cry(d: Doc):
    # sound waves from the bell
    for i, r in enumerate((20, 32, 44)):
        pts = arc_pts(84, 44, r, math.radians(-100), math.radians(40), 24)
        w = 7 - i * 1.3
        d.path(ribbon(pts, taper(24, w * 2.2, 0.0, 0.0)), fill="#ff5030", op=0.25)
        d.path(ribbon(pts, taper(24, w, 0.0, 0.0)), fill=mix("#ffd070", "#ff5a3a", i * 0.35), op=0.95)
    with d.g(T(56, 74, -8, 1.02)):
        horn(d, pal=BONE, band=GOLD)
    # crimson tassel
    for i, x in enumerate((30, 35, 40)):
        pts = qbez((34, 90), (x - 2, 100), (x - 6, 114), n=10)
        d.path(ribbon(pts, taper(10, 4, 0.8, 0.2, peak=0.1)), fill=CRIMSON["base"] if i != 1 else CRIMSON["light"], stroke=OUTLINE, stroke_width=0.8)


@skill("knight", "#2e220a", haze="#b08a2a", haze2="#fff0b0")
def judgment(d: Doc):
    # heavenly beam
    d.path("M44,0 L84,0 L74,128 L54,128 Z", fill=d.lin([(0, "#fff8d8", 0.7), (1, "#ffe08a", 0.05)], 0, 0, 0, 128))
    sun(d, 64, 34, 12, EL["light"], rays=16, ray_len=2.6)
    d.circle(64, 34, 22, stroke="#fff4c0", stroke_width=2.4, opacity=0.9)
    # ground strike glow
    d.glow_ellipse(64, 110, 40, 10, "#ffe08a", 0.9)
    with d.g(T(64, 38, 180, 1.0)):
        sword(d, L=70, W=13, pal=dict(dark="#8a6a2a", base="#f2e2b0", light="#ffffff"), hilt=GOLD, glow="#fff0b0")
    for (x, y, s) in ((34, 70, 5), (96, 80, 4), (40, 100, 3.5), (90, 56, 3)):
        d.sparkle(x, y, s, "#fffbe8", 0.95, glow_color="#ffe08a")


@skill("knight", "#24140a", haze="#8a4a14", haze2="#402010")
def ground_fissure(d: Doc):
    pal = EL["earth"]
    rng = random.Random(11)
    # ground plane in perspective (horizon at y=46)
    d.path("M0,46 L128,46 L128,128 L0,128 Z", fill=d.lin([(0, "#2a1a0c"), (0.4, "#4a3018"), (1, "#1a0e06")], 0, 46, 0, 128))
    # scattered ground plates
    for i in range(14):
        x, y = rng.uniform(4, 124), rng.uniform(52, 124)
        if abs(x - (64 + (y - 46) * 0.05)) < 14 + (y - 46) * 0.35:
            continue
        s = 0.5 + (y - 46) / 80
        pts = blob(x, y, 9 * s, 6, 0.25, rng, sy=0.45)
        faceted(d, pts, (x - 2, y - 2), "#24160a", "#8a6038", ow=1.0, light_dir=(-0.3, -1))
    # the chasm: widening towards the viewer
    L = [(64, 46), (60, 58), (63, 68), (52, 82), (56, 94), (42, 108), (46, 118), (34, 128)]
    R = [(64, 46), (67, 58), (65, 68), (76, 82), (72, 94), (86, 108), (82, 118), (96, 128)]
    chasm = L + R[::-1]
    d.glow_ellipse(64, 96, 50, 40, "#ff8a2a", 0.55)
    d.path(poly(chasm), stroke=OUTLINE, sw=5)
    d.path(poly(chasm), fill=d.lin([(0, "#ffe890"), (0.35, "#ff9a30"), (1, "#a8300a")], 0, 46, 0, 128))
    core = [(64, 50), (62, 62), (64, 70), (58, 84), (61, 96), (54, 110), (57, 128), (71, 128), (74, 110), (67, 96), (70, 84), (64, 70), (66, 62)]
    d.path(poly(core), fill="#fff4c0", op=0.8)
    # lifted slab lips along the chasm edges
    for side, sgn in ((L, -1), (R, 1)):
        lip = [(x + sgn * 5, y + 3) for x, y in side]
        d.path(poly(side + lip[::-1]), fill=pal["light"], op=0.85)
        d.path(poly(side, closed=False), stroke=OUTLINE, sw=1.6)
    # branching cracks
    for (x, y), dx in (((52, 82), -30), ((76, 82), 30), ((42, 108), -34), ((86, 108), 32), ((60, 58), -24), ((67, 58), 22)):
        br = jag_line((x, y), (x + dx, y + rng.uniform(-6, 10)), 4, 3, rng)
        d.path(poly(br, closed=False), stroke="#140804", sw=3.2)
        d.path(poly(br, closed=False), stroke="#ffa040", sw=1.3)
    # erupting rock chunks
    for i, (x, y, r) in enumerate(((44, 34, 8), (84, 28, 7), (64, 16, 5), (30, 58, 5), (100, 50, 5.5))):
        d.glow(x, y + r, r * 1.8, "#ff8a2a", 0.4)
        rock(d, x, y, r, pal, seed=20 + i, n=7, ow=1.8)
    for (x, y) in ((56, 40), (74, 44), (70, 30), (50, 22), (90, 40)):
        d.circle(x, y, 1.4, fill="#ffd070")


@skill("knight", "#141c26", haze="#4a6a90", haze2="#b88a3a")
def iron_bulwark(d: Doc):
    # hexagonal barrier dome
    cx, cy = 64, 66
    for k in range(-3, 4):
        for j in range(-3, 4):
            x = cx + k * 15 + (j % 2) * 7.5
            y = cy + j * 13
            dist = math.hypot(x - cx, y - cy)
            if 38 < dist < 56:
                op = 0.55 - abs(dist - 47) / 30
                d.path(poly(ngon(x, y, 7.6, 6, rot0=0)), stroke="#9ad0ff", sw=1.4, op=max(op, 0.12))
                d.path(poly(ngon(x, y, 7.0, 6, rot0=0)), fill="#6aa8e8", op=max(op * 0.25, 0.04))
    d.circle(cx, cy, 50, stroke="#bfe2ff", stroke_width=2.2, opacity=0.6)
    d.circle(cx, cy, 44, stroke="#6aa8e8", stroke_width=1, opacity=0.4)
    with d.g(T(cx, cy + 2, 0, 1.0)):
        tower_shield(d, w=50, h=78, face=STEEL, band=GOLD)
    d.path(smooth([(40, 34), (54, 26), (70, 26)], closed=False), stroke="#ffffff", sw=2, op=0.4)


# ------------------------------------------------------------------------------------------------ mage

MAGE_BG = "#140e30"


@skill("mage", mix(MAGE_BG, "#5a1a08", 0.5), haze="#ff5a14", haze2="#3a2a8a")
def firebolt(d: Doc):
    pal = EL["fire"]
    # trail towards the lower-left
    for (off, w, col, op) in ((0, 30, pal["dark"], 0.55), (0, 20, pal["base"], 0.8), (0, 10, pal["light"], 0.9), (0, 4, "#ffffff", 0.9)):
        pts = qbez((16, 110), (40, 90), (80, 50), n=20)
        d.path(ribbon(pts, taper(20, w, 0.0, 1.0, peak=1.0, power=1.4)), fill=col, op=op)
    rng = random.Random(3)
    for i in range(9):
        t = rng.uniform(0.1, 0.8)
        x, y = 16 + (80 - 16) * t + rng.uniform(-10, 10), 110 - 60 * t + rng.uniform(-10, 10)
        d.circle(x, y, rng.uniform(1, 2.4), fill=pal["light"], opacity=0.9)
    d.glow(84, 46, 34, pal["glow"], 0.8)
    with d.g(T(84, 46, 225, 0.72)):
        flame(d, 0, 0, 1.0, pal, glow=False)
    d.circle(84, 46, 12, fill=d.rad([(0, "#ffffff"), (0.45, "#fff0a0"), (1, pal["base"], 0.0)], 84, 46, 12))


@skill("mage", mix(MAGE_BG, "#0a3a5a", 0.6), haze="#6ad8ff", haze2="#3a2a8a")
def frost_nova(d: Doc):
    pal = EL["ice"]
    cx, cy = 64, 64
    d.glow(cx, cy, 58, pal["glow"], 0.55)
    d.circle(cx, cy, 44, stroke=pal["light"], stroke_width=3, opacity=0.35)
    d.circle(cx, cy, 30, stroke=pal["light"], stroke_width=1.4, opacity=0.35)
    for i in range(10):
        a = i * 36 + 18
        L = 30 if i % 2 == 0 else 22
        bx, by = polar(cx, cy, 24 if i % 2 == 0 else 22, math.radians(a - 90))
        with d.g(T(bx, by, a, 1.0)):
            ice_shard(d, L=L, W=11 if i % 2 == 0 else 8, pal=pal)
    snowflake(d, cx, cy, 16, pal, width=3.2)
    d.circle(cx, cy, 6, fill="#ffffff", opacity=0.9)


@skill("mage", mix(MAGE_BG, "#2a1a5a", 0.5), haze="#8a5aff", haze2="#ffe23a")
def chain_lightning(d: Doc):
    pal = EL["lightning"]
    rng = random.Random(5)
    nodes = [(22, 100), (56, 34), (104, 70), (90, 112)]
    segs = [(0, 1), (1, 2), (2, 3)]
    for a, b in segs:
        pts = jag_line(nodes[a], nodes[b], 7, 7, rng)
        bolt(d, pts, width=9, pal=pal)
        # side forks
        k = rng.randint(2, 4)
        fk = jag_line(pts[k], (pts[k][0] + rng.uniform(-18, 18), pts[k][1] + rng.uniform(-18, 18)), 3, 3, rng)
        bolt(d, fk, width=4, pal=pal, glow=False)
    for (x, y) in nodes:
        d.glow(x, y, 22, pal["glow"], 0.95)
        d.circle(x, y, 8.5, fill=d.rad([(0, "#ffffff"), (0.5, pal["base"]), (1, pal["dark"])], x - 2, y - 2, 9), stroke=OUTLINE, stroke_width=1.8)
        d.circle(x - 2, y - 2, 2, fill="#ffffff")


@skill("mage", mix(MAGE_BG, "#3a1a6a", 0.5), haze="#8a4ae0", haze2="#2a6aff")
def blink(d: Doc):
    pal = ARCANE
    # ghostly destination echo
    with d.g(T(104, 104, 0, 0.62), op=0.3):
        humanoid_robed(d, fill="#b89aff", outline=False)
    d.glow(52, 70, 44, pal["glow"], 0.5)
    fill = d.lin([(0, "#4a3aa0"), (0.3, "#6a4ac8"), (0.45, "#9a7af0", 0.85), (0.68, "#c0a8ff", 0.0), (1, "#c0a8ff", 0.0)], -24, 0, 24, 0)
    with d.g(T(46, 114, 0, 1.08)):
        d.path(smooth([(0, -80), (7, -74), (10, -64), (9, -58), (16, -55), (22, -46), (24, -30), (21, -20), (17, -24), (18, -8), (22, 0),
                       (-22, 0), (-18, -8), (-17, -24), (-21, -20), (-24, -30), (-22, -46), (-16, -55), (-9, -58), (-10, -64), (-7, -74)], tension=0.45),
               stroke=d.lin([(0, OUTLINE), (0.4, OUTLINE), (0.6, OUTLINE, 0.0), (1, OUTLINE, 0)], -24, 0, 24, 0), sw=4.4)
        humanoid_robed(d, fill=fill, outline=False)
        d.path(smooth([(-7, -70), (0, -74), (7, -70), (8, -60), (0, -55), (-8, -60)], tension=0.5), fill="#07030e", op=0.95)
        for ex in (-3.4, 3.4):
            d.glow(ex, -64, 4.5, "#e0a0ff", 1.0)
            d.circle(ex, -64, 1.3, fill="#ffffff")
        d.path(smooth([(-9, -58), (-18, -52), (-23, -36), (-24, -24)], closed=False), stroke="#c8b0ff", sw=1.6, op=0.8)
        d.path(smooth([(0, -80), (-7, -74), (-10, -64)], closed=False), stroke="#c8b0ff", sw=1.4, op=0.8)
    # dissolving motes streaming right
    rng = random.Random(9)
    pts = []
    for i in range(34):
        x = 44 + (rng.random() ** 1.5) * 70
        y = rng.uniform(30, 112)
        s = max(0.35, 1.7 - (x - 44) / 45)
        pts.append((x, y, s))
    motes(d, pts, "#e8d8ff", glow_color="#a060ff", size=2.4)
    for (x, y, s) in ((70, 52, 6), (88, 80, 4.5), (104, 44, 3.5)):
        d.sparkle(x, y, s, "#ffffff", 0.95)


@skill("mage", mix(MAGE_BG, "#4a1408", 0.55), haze="#ff5a14", haze2="#ffb040")
def meteor(d: Doc):
    pal = EL["fire"]
    # fiery tail to upper-right
    for (w, col, op) in ((48, pal["dark"], 0.5), (34, pal["base"], 0.75), (20, pal["light"], 0.85), (8, "#ffffff", 0.8)):
        pts = qbez((124, 4), (96, 30), (56, 72), n=20)
        d.path(ribbon(pts, taper(20, w, 0.0, 1.0, peak=1.0, power=1.2)), fill=col, op=op)
    # impact glow on the ground
    d.glow_ellipse(40, 112, 48, 12, "#ff7a1a", 0.8)
    d.glow(52, 76, 36, pal["glow"], 0.8)
    rng = random.Random(2)
    pts = blob(50, 78, 21, 9, 0.18, rng, rot0=0.3)
    faceted(d, pts, (46, 74), "#1a0804", "#6a3a22", ow=2.6, light_dir=(0.7, -0.7))
    # molten cracks
    for a, b in (((40, 70), (54, 80)), ((54, 80), (62, 72)), ((54, 80), (50, 94)), ((44, 86), (36, 82))):
        pp = jag_line(a, b, 3, 2, rng)
        d.path(poly(pp, closed=False), stroke="#ff8a2a", sw=2.6)
        d.path(poly(pp, closed=False), stroke="#ffe080", sw=1.0)
    # leading-edge flames licking back
    for (x, y, s) in ((66, 64, 0.34), (60, 60, 0.3), (70, 72, 0.3)):
        with d.g(T(x, y, 45, s)):
            flame(d, 0, 0, 1.0, pal, glow=False, tongues=False)


@skill("mage", mix(MAGE_BG, "#06304a", 0.6), haze="#30c4d4", haze2="#2a2a8a")
def tidal_wave(d: Doc):
    with d.g(T(64, 70, 0, 1.0)):
        wave(d, EL["water"], s=1.0)
    for (x, y, r) in ((18, 36, 3), (26, 26, 2), (112, 96, 2.4)):
        d.circle(x, y, r, fill="#b8f4ff", opacity=0.8)


@skill("mage", mix(MAGE_BG, "#1a4a30", 0.5), haze="#9ee0a6", haze2="#3a8a6a")
def gale_burst(d: Doc):
    pal = EL["wind"]
    cx, cy = 64, 64
    d.glow(cx, cy, 50, pal["glow"], 0.45)
    for i in range(3):
        swirl(d, cx, cy, 4, 46, i * 2 * math.pi / 3, 0.62, 11, pal["base"], n=36)
        swirl(d, cx, cy, 4, 46, i * 2 * math.pi / 3, 0.62, 4, pal["light"], n=36, outline=False)
    # outward gust streaks
    for i in range(6):
        a = i * math.pi / 3 + 0.4
        p0, p1 = polar(cx, cy, 44, a), polar(cx, cy, 58, a + 0.12)
        gust(d, [p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), p1], 4, pal["light"], outline=False, op=0.8)
    # leaves
    for i, (x, y, a) in enumerate(((96, 36, 30), (30, 92, -40), (100, 92, 80))):
        with d.g(T(x, y, a, 1)):
            lf = smooth([(0, -7), (3.5, 0), (0, 7), (-3.5, 0)], tension=0.9)
            d.path(lf, fill=d.lin([(0, "#bff0a0"), (1, "#3a8a4a")], -3, -7, 3, 7), stroke=OUTLINE, stroke_width=1.2)
            d.path("M0,-6 L0,6", stroke="#2a6a3a", sw=0.7)
    d.circle(cx, cy, 6, fill="#ffffff", opacity=0.85)


@skill("mage", mix(MAGE_BG, "#3a1270", 0.55), haze="#a060ff", haze2="#ff60e0")
def arcane_surge(d: Doc):
    pal = ARCANE
    cx, cy = 64, 64
    d.glow(cx, cy, 60, pal["glow"], 0.55)
    rune_ring(d, cx, cy, 46, "#c8a8ff", width=2.2, ticks=20)
    tri1 = ngon(cx, cy, 36, 3)
    tri2 = ngon(cx, cy, 36, 3, rot0=math.pi / 2)
    d.path(poly(tri1) + " " + poly(tri2), stroke="#b890ff", sw=1.6, op=0.8)
    # surge rays
    for i in range(8):
        a = i * math.pi / 4
        p0, p1 = polar(cx, cy, 10, a), polar(cx, cy, 40 if i % 2 == 0 else 28, a)
        d.path(ribbon([p0, p1], [7, 0.5]), fill="#e8d8ff", op=0.8)
    d.path(poly(star_pts(cx, cy, 4, 30, 6)), fill="#d8c0ff", stroke=OUTLINE, stroke_width=1.8)
    d.path(poly(star_pts(cx, cy, 4, 22, 4)), fill="#ffffff")
    d.glow(cx, cy, 14, "#ffffff", 0.9)
    for (x, y, s) in ((28, 30, 3.5), (100, 34, 3), (98, 100, 4), (30, 98, 3)):
        d.sparkle(x, y, s, "#ffffff", 0.9, glow_color="#a060ff")


@skill("mage", mix(MAGE_BG, "#1a0626", 0.6), haze="#6a1a8a", haze2="#2a0a3a")
def shadow_curse(d: Doc):
    pal = EL["dark"]
    cx, cy = 64, 62
    d.glow(cx, cy, 60, "#b050ff", 0.75)
    # swirling tendrils
    tendril(d, [(10, 116), (30, 96), (24, 70), (40, 50), (52, 38)], 12, pal)
    tendril(d, [(118, 112), (98, 100), (106, 76), (90, 52), (78, 40)], 12, pal)
    tendril(d, [(64, 124), (70, 104), (56, 92), (64, 82)], 9, pal)
    tendril(d, [(116, 16), (96, 22), (92, 38)], 7, pal)
    tendril(d, [(12, 20), (30, 22), (36, 38)], 7, pal)
    # the cursed eye
    eye(d, cx, cy, 36, 15, dict(dark="#3a0a4a", base="#b03ae0", light="#ffb0ff"), white="#1a0a24", ow=2.6)
    d.glow(cx, cy, 16, "#e060ff", 0.6)
    d.ellipse(cx, cy, 3.2, 10, fill="#07030a")
    # dripping motes
    motes(d, [(46, 86, 1), (82, 90, 0.8), (70, 100, 0.7), (56, 104, 0.6)], "#c070ff", glow_color="#8a3ad0", size=2.2, diamonds=False)


@skill("mage", mix(MAGE_BG, "#4a3a10", 0.55), haze="#ffe08a", haze2="#fff0c0")
def radiant_ward(d: Doc):
    pal = EL["light"]
    cx, cy = 64, 64
    d.glow(cx, cy, 60, pal["glow"], 0.6)
    rune_ring(d, cx, cy, 48, "#ffe9a0", width=2.4, ticks=24, seed=8)
    # radiant spokes
    for i in range(12):
        a = i * math.pi / 6 + math.pi / 12
        p0, p1 = polar(cx, cy, 26, a), polar(cx, cy, 42, a)
        d.path(ribbon([p0, p1], [5, 0.5]), fill="#fff4c0", op=0.8)
    # luminous shield of light
    from bh_shapes import heater_pts
    pts = [(cx + x * 0.75, cy + 2 + y * 0.75) for x, y in heater_pts(60, 70)]
    sd = smooth(pts, tension=0.55)
    d.path(sd, stroke="#fff4c0", sw=10, op=0.25)
    d.path(sd, stroke=OUTLINE, sw=5)
    d.path(sd, fill=d.rad([(0, "#ffffff"), (0.4, "#fff2b8"), (1, "#d8a840")], cx - 6, cy - 8, 44))
    d.path(smooth([(cx + x * 0.6, cy + 1 + y * 0.6) for x, y in heater_pts(60, 70)], tension=0.55), stroke="#c8962e", sw=1.6)
    sun(d, cx, cy - 2, 7, pal, rays=8, ray_len=2.0, glow=False)


@skill("mage", mix(MAGE_BG, "#2a1a0a", 0.55), haze="#a8733a", haze2="#6a4a8a")
def stone_spear(d: Doc):
    pal = dict(dark="#2a2018", base="#8a7a64", light="#e0d2b4")
    d.path("M0,100 L128,96 L128,128 L0,128 Z", fill=d.lin([(0, "#3a2812"), (1, "#0e0804")], 0, 96, 0, 128))
    d.glow_ellipse(42, 104, 44, 14, "#d89a48", 0.7)

    def spike(base_c, tip, w, seed):
        r2 = random.Random(seed)
        dx, dy = tip[0] - base_c[0], tip[1] - base_c[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L

        def P(t, o):
            return (base_c[0] + dx * t + nx * o, base_c[1] + dy * t + ny * o)
        ts = (0, 0.18, 0.36, 0.55, 0.74, 0.9)
        left = [P(t, -w * (1 - t) * r2.uniform(0.75, 1.1) - 1) for t in ts]
        rr = [P(t, w * (1 - t) * r2.uniform(0.75, 1.1) + 1) for t in ts]
        outline = left + [P(1, 0)] + rr[::-1]
        d.path(poly(outline), stroke=OUTLINE, sw=5)
        mid = [P(t, w * 0.15 * (1 - t)) for t in ts]
        for i in range(len(ts) - 1):
            d.path(poly([left[i], left[i + 1], mid[i + 1], mid[i]]), fill=mix(pal["base"], pal["light"], 0.3 + 0.15 * (i % 2)))
            d.path(poly([mid[i], mid[i + 1], rr[i + 1], rr[i]]), fill=mix(pal["dark"], pal["base"], 0.35 + 0.18 * (i % 2)))
        d.path(poly([left[-1], P(1, 0), mid[-1]]), fill=pal["light"])
        d.path(poly([mid[-1], P(1, 0), rr[-1]]), fill=pal["base"])
        d.path(poly(mid + [P(1, 0)], closed=False), stroke=pal["light"], sw=0.9, op=0.7)
        for i in range(1, len(mid) - 1):
            d.path(poly([left[i], mid[i], rr[i]], closed=False), stroke=pal["dark"], sw=1.1, op=0.8)

    d.glow_stroke("M40,104 L108,18", "#e8b060", 16, op=0.3)
    spike((20, 106), (46, 56), 9, 2)
    spike((70, 106), (92, 64), 8, 3)
    spike((38, 110), (110, 16), 17, 1)
    for i, (x, y, r) in enumerate(((14, 104, 7), (60, 102, 6), (26, 86, 4), (58, 82, 4), (8, 90, 3), (46, 118, 5), (84, 110, 5))):
        rock(d, x, y, r, pal, seed=40 + i, n=6, ow=1.5)
    d.sparkle(106, 22, 6, "#fff4d0", 0.95, glow_color="#e8b060")
