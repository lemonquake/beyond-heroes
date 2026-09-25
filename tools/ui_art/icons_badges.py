"""Element medallions, status badges and attribute plaques."""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, EL, STEEL, CRIMSON, GOLD, BRONZE, INDIGO, ARCANE, LEATHER, WOOD, BONE, LINEN, OUTLINE, f, poly,
                    smooth, mix, lt, dk, ribbon, taper, arc_pts, bez, qbez, star_pts, ngon, jag_line, blob, teardrop, polar,
                    faceted, rrect_path, circle_path, lerp)
from bh_shapes import (T, sword, heater_shield, heater_pts, flame, ice_shard, snowflake, bolt, zig_bolt, rock, swirl, gust,
                       sun, void_orb, tendril, rune_ring, motes, fist, banner, heart, impact_star, droplet, skull, arrow,
                       smooth_pts, crystal)
from bh_frames import medallion_bg, medallion_rim, badge_bg, badge_rim, octagon_bg, octagon_rim, KNIGHT_METAL, MAGE_METAL

ELEMENTS, STATUS, ATTRIBUTES, ATTR_DRAW = {}, {}, {}, {}
BRIGHT_STEEL = dict(dark="#3a4250", base="#b4bfcc", light="#ffffff", glow="#e8f0ff")


# ------------------------------------------------------------------------------------------ shared glyphs

def feather(d: Doc, L=60, W=14, pal=None, ow=2.2):
    """Feather pointing -y, quill base at origin."""
    pal = pal or dict(dark="#2a5a4a", base="#8ad0b0", light="#f0fff8")
    vane = [(0, -6), (-W * 0.5, -L * 0.3), (-W * 0.55, -L * 0.62), (-W * 0.2, -L * 0.92), (0, -L), (W * 0.35, -L * 0.85),
            (W * 0.5, -L * 0.55), (W * 0.4, -L * 0.25), (0, -6)]
    dd = smooth(vane[:-1], tension=0.6)
    d.path(dd, stroke=OUTLINE, sw=ow * 2)
    d.path(dd, fill=d.lin([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], -W / 2, 0, W / 2, 0))
    # barb notches
    for t, s in ((0.35, -1), (0.6, 1), (0.5, -1)):
        x0, y0 = 0, -L * t
        d.path(f"M{f(x0)},{f(y0)} L{f(s * W * 0.55)},{f(y0 - L * 0.06)}", stroke=OUTLINE, sw=1.6)
    for k in range(1, 9):
        y = -L * (0.12 + k * 0.09)
        d.path(f"M0,{f(y)} L{f(-W * 0.42)},{f(y - 5)} M0,{f(y)} L{f(W * 0.36)},{f(y - 5)}", stroke=pal["dark"], sw=0.7, op=0.6)
    d.path(f"M0,8 L0,{f(-L * 0.95)}", stroke=OUTLINE, sw=3)
    d.path(f"M0,8 L0,{f(-L * 0.95)}", stroke=pal["light"], sw=1.3)


def wing(d: Doc, pal=GOLD, flip=False):
    """Heraldic wing rising from a root at the origin, spreading up and to the left (~70 wide, ~70 tall)."""
    sx = -1 if flip else 1

    def feather_poly(ax, ay, ang, L, W, round_tip=False):
        ux, uy = math.cos(ang), math.sin(ang)
        nx, ny = -uy, ux
        P = lambda t, o: (sx * (ax + ux * L * t + nx * o), ay + uy * L * t + ny * o)
        if round_tip:
            pts = [P(0, -W * 0.4), P(0.5, -W * 0.5), P(0.9, -W * 0.35), P(1, 0), P(0.9, W * 0.35), P(0.5, W * 0.5), P(0, W * 0.4)]
        else:
            pts = [P(0, -W * 0.35), P(0.55, -W * 0.5), P(0.9, -W * 0.3), P(1.0, W * 0.05), P(0.8, W * 0.45), P(0.4, W * 0.5), P(0, W * 0.35)]
        return pts, P
    arm = qbez((2, 2), (-2, -34), (-30, -52), n=20)
    n = 8
    for i in range(n):
        t = i / (n - 1)
        ax, ay = arm[int(t * 16) + 1]
        ang = math.radians(128 + 52 * t)
        L = 26 + 40 * t ** 0.8
        pts, P = feather_poly(ax, ay, ang, L, 12)
        dd = smooth(pts, tension=0.55)
        d.path(dd, stroke=OUTLINE, sw=3.6)
        d.path(dd, fill=d.lin([(0, pal["base"]), (0.6, lt(pal["base"], 0.2)), (1, pal["dark"])], *P(0, 0), *P(1, 0)))
        d.path(poly([P(0.05, 0), P(0.85, 0)], closed=False), stroke=pal["dark"], sw=0.9, op=0.7)
    # coverts along the arm
    for i in range(6):
        t = i / 5
        ax, ay = arm[int(t * 17) + 1]
        pts, P = feather_poly(ax, ay, math.radians(120 + 50 * t), 16 + 6 * t, 11, round_tip=True)
        dd = smooth(pts, tension=0.6)
        d.path(dd, stroke=OUTLINE, sw=3.0)
        d.path(dd, fill=d.lin([(0, pal["light"]), (1, pal["base"])], *P(0, 0), *P(1, 0)))
    # leading-edge arm
    arm2 = [(sx * x, y) for x, y in arm]
    d.path(ribbon(arm2, taper(20, 7, 1.0, 0.3, peak=0.0)), fill=pal["light"], stroke=OUTLINE, stroke_width=1.6)


def book(d: Doc, cover=CRIMSON, page="#efe2c0"):
    """Open tome, local ~ x[-44,44] y[-24,30]."""
    cov = [(-46, -14), (0, -6), (46, -14), (46, 26), (0, 32), (-46, 26)]
    d.shape(poly(cov), fill=d.lin([(0, cover["light"]), (1, cover["dark"])], 0, -14, 0, 32), ow=2.6)
    for s in (-1, 1):
        pg = [(0, -2), (s * 18, -14), (s * 42, -18), (s * 42, 22), (s * 18, 20), (0, 28)]
        dd = smooth(pg, tension=0.25)
        d.path(dd, stroke=OUTLINE, sw=3)
        d.path(dd, fill=d.lin([(0, page), (1, dk(page, 0.35))], 0, 0, s * 42, 0))
        for k in range(5):
            y = -8 + k * 6
            x0, x1 = s * 8, s * 36
            d.path(smooth([(x0, y + 1), ((x0 + x1) / 2, y - 2), (x1, y - 3)], closed=False), stroke="#5a4020", sw=1.2, op=0.55)
    d.path("M0,-2 L0,28", stroke=OUTLINE, sw=2)


def owl(d: Doc):
    """Owl face, local ~ x[-40,40] y[-44,40]."""
    fe = dict(dark="#2a1c14", base="#7a5a40", light="#d8b890")
    head = [(-30, -30), (-36, -44), (-20, -34), (0, -38), (20, -34), (36, -44), (30, -30), (38, -6), (34, 20), (18, 38), (0, 42),
            (-18, 38), (-34, 20), (-38, -6)]
    dd = smooth(head, tension=0.45)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, fe["light"]), (0.5, fe["base"]), (1, fe["dark"])], 0, -44, 0, 42))
    # chest feather scallops
    for row, y in enumerate((20, 28)):
        for k in range(-2, 3):
            x = k * 9 + (row % 2) * 4.5
            d.path(f"M{f(x - 4)},{f(y)} Q{f(x)},{f(y + 5)} {f(x + 4)},{f(y)}", stroke=fe["dark"], sw=1.2, op=0.8)
    for s in (-1, 1):
        # facial disc
        d.circle(s * 15, -8, 15, fill=d.rad([(0, "#f4e6c8"), (1, "#a88a64")], s * 15, -10, 16), stroke=OUTLINE, stroke_width=2)
        d.circle(s * 15, -8, 9.5, fill=d.rad([(0, "#fff4a0"), (0.6, "#ffb020"), (1, "#a05a00")], s * 15 - 2, -10, 10), stroke=OUTLINE, stroke_width=1.6)
        d.circle(s * 15, -8, 4.6, fill="#0a0604")
        d.circle(s * 15 - 2, -10.5, 1.6, fill="#ffffff")
    d.shape(poly([(-5, 2), (5, 2), (0, 14)]), fill=d.lin([(0, "#f0d070"), (1, "#8a5a10")], 0, 2, 0, 14), ow=1.6)
    d.path("M-26,-24 L-6,-18 M26,-24 L6,-18", stroke=fe["dark"], sw=2.2)


def target(d: Doc):
    for r, col in ((40, CRIMSON["base"]), (31, "#e8dcc0"), (22, CRIMSON["base"]), (13, "#e8dcc0"), (5, CRIMSON["light"])):
        d.circle(0, 0, r, fill=d.rad([(0, lt(col, 0.2)), (1, dk(col, 0.25))], -r * 0.3, -r * 0.3, r * 1.3), stroke=OUTLINE, stroke_width=2)
    d.circle(0, 0, 42, stroke=WOOD["base"], stroke_width=3)
    d.circle(0, 0, 44, stroke=OUTLINE, stroke_width=1.5)


def dragon_bubble(d: Doc, cx, cy, r, col="#8ad0ff"):
    d.circle(cx, cy, r, fill=d.rad([(0, col, 0.05), (0.75, col, 0.2), (1, lt(col, 0.5), 0.75)], cx, cy, r))
    d.circle(cx, cy, r, stroke=lt(col, 0.6), stroke_width=2.4)
    d.path(smooth(arc_pts(cx, cy, r * 0.78, math.radians(200), math.radians(260), 6), closed=False), stroke="#ffffff", sw=4, op=0.7)


# ------------------------------------------------------------------------------------------ elements

def element(name, metal):
    def deco(fn):
        def build():
            d = Doc(name="el_" + fn.__name__)
            p = EL[name]
            medallion_bg(d, mix(p["dark"], "#140e20", 0.35))
            d.circle(64, 64, 56, fill=d.rad([(0, p["glow"], 0.35), (1, p["glow"], 0)], 64, 60, 56))
            fn(d, p)
            medallion_rim(d, metal)
            return d
        ELEMENTS[name] = build
        return fn
    return deco


EL_RIM = dict(dark="#3a2c1a", base="#9a8468", light="#f0e2c4")


@element("physical", STEEL)
def e_physical(d, p):
    impact_star(d, 64, 64, 38, "#ffffff", "#c8d4e0", n=8, inner=0.3, rot0=math.pi / 8)
    with d.g(T(46, 84, 45, 0.95)):
        sword(d, L=60, W=12, pal=BRIGHT_STEEL)


@element("fire", dict(dark="#5a1206", base="#d0501a", light="#ffc070"))
def e_fire(d, p):
    flame(d, 64, 86, 1.0, p)


@element("ice", dict(dark="#1f4a6a", base="#6ab8d8", light="#e8fbff"))
def e_ice(d, p):
    snowflake(d, 64, 64, 38, p, width=6)


@element("lightning", dict(dark="#3a1a7a", base="#a080e8", light="#fff4b0"))
def e_lightning(d, p):
    zig_bolt(d, 64, 64, 90, pal=p, lean=0.1)


@element("earth", dict(dark="#3e2610", base="#a8733a", light="#e6bf7c"))
def e_earth(d, p):
    rock(d, 50, 84, 16, p, seed=3, n=7)
    rock(d, 86, 86, 13, p, seed=4, n=7)
    rock(d, 66, 60, 24, p, seed=2, n=8, jitter=0.18)
    for (x, y) in ((40, 40), (92, 44), (76, 30)):
        rock(d, x, y, 4, p, seed=int(x), n=5, ow=1.2)


@element("wind", dict(dark="#2c6a4c", base="#8ac8a0", light="#ecffec"))
def e_wind(d, p):
    for k, (y, L, r) in enumerate(((44, 56, 11), (64, 66, 12), (84, 48, 9))):
        x0 = 16 + k * 6
        pts = [(x0, y)] + [(x0 + L * t, y - math.sin(t * math.pi) * 3) for t in (0.3, 0.6)] + [(x0 + L, y)]
        pts += arc_pts(x0 + L, y - r, r, math.pi / 2, -math.pi * 0.9, 12)[1:]
        gust(d, smooth_pts(pts, 30), 9, p["base"], hl=p["light"], peak=0.3, start=0.1, end=0.1)


@element("water", dict(dark="#062a44", base="#138a9c", light="#76e2ea"))
def e_water(d, p):
    droplet(d, 64, 70, 24, p, ow=2.6)
    for k in range(2):
        y = 98 + k * 8
        pts = [(24 + i * 10, y + (3 if i % 2 else -3)) for i in range(9)]
        d.path(smooth(pts, closed=False), stroke=OUTLINE, sw=5)
        d.path(smooth(pts, closed=False), stroke=p["light"], sw=2.4)


@element("light", dict(dark="#9a6c20", base="#e8c060", light="#fff8d0"))
def e_light(d, p):
    sun(d, 64, 64, 18, p, rays=12, ray_len=2.4)


@element("dark", dict(dark="#10041a", base="#6a3a90", light="#c8a0f0"))
def e_dark(d, p):
    # black sun with a violet corona
    pts = star_pts(64, 64, 14, 50, 26)
    d.path(poly(pts), fill=d.rad([(0, p["light"]), (0.55, p["base"], 0.9), (1, p["base"], 0.0)], 64, 64, 50))
    void_orb(d, 64, 64, 24, p)
    d.path(smooth(arc_pts(64, 64, 28, math.radians(-30), math.radians(80), 8), closed=False), stroke=p["light"], sw=2.4, op=0.8)
    motes(d, [(34, 34, 1), (96, 40, 0.8), (90, 96, 0.9), (32, 92, 0.7)], p["light"], glow_color=p["glow"], size=2.2)


# ------------------------------------------------------------------------------------------ status

DEBUFF = "#b8322e"
BUFF = "#d0a040"


def status(rim, inner):
    def deco(fn):
        def build():
            d = Doc(name="st_" + fn.__name__)
            badge_bg(d, inner, rim)
            with d.g("translate(64 64) scale(0.86) translate(-64 -64)"):
                fn(d)
            badge_rim(d, rim)
            return d
        STATUS[fn.__name__] = build
        return fn
    return deco


@status(DEBUFF, "#4a1206")
def burning(d):
    flame(d, 64, 90, 1.05, EL["fire"])


@status("#6ab8d8", "#0e2a40")
def chilled(d):
    p = EL["ice"]
    snowflake(d, 64, 56, 30, p, width=5)
    for y in (96, 106):
        pts = [(24 + i * 16, y + (4 if i % 2 else -2)) for i in range(6)]
        d.path(smooth(pts, closed=False), stroke="#bfefff", sw=3.2, op=0.7)


@status("#8ad8f0", "#0a3048")
def frozen(d):
    p = EL["ice"]
    d.glow(64, 64, 50, p["glow"], 0.5)
    front = [(30, 50), (66, 60), (66, 104), (30, 92)]
    side = [(66, 60), (98, 48), (98, 90), (66, 104)]
    top = [(30, 50), (62, 38), (98, 48), (66, 60)]
    for pts, col in ((front, p["base"]), (side, p["dark"]), (top, p["light"])):
        d.shape(poly(pts), fill=d.lin([(0, lt(col, 0.25)), (1, col)], pts[0][0], pts[0][1], pts[2][0], pts[2][1]), ow=2.2)
    d.path("M36,58 L44,86 M50,64 L56,76 M74,70 L84,82", stroke="#ffffff", sw=1.6, op=0.6)
    for x, L, a in ((44, 20, -10), (60, 28, 0), (78, 22, 12)):
        with d.g(T(x, 48 + abs(a) * 0.2, a, 1)):
            from bh_shapes import ice_shard as _s
            _s(d, L=L, W=9, pal=p)


@status("#b890ff", "#1e1244")
def shocked(d):
    p = EL["lightning"]
    zig_bolt(d, 64, 64, 84, pal=p, lean=0.1)
    rng = random.Random(8)
    for (x0, y0, x1, y1) in ((24, 40, 40, 30), (92, 84, 108, 96), (28, 90, 18, 104), (100, 34, 112, 22)):
        bolt(d, jag_line((x0, y0), (x1, y1), 3, 3, rng), width=3.5, pal=p, glow=False)


@status(DEBUFF, "#2a1a14")
def staggered(d):
    # shield cracking in two
    rng = random.Random(4)
    pts = heater_pts(64, 78)
    crack = jag_line((2, -36), (-2, 44), 7, 5, rng)
    halves = ((crack + [pts[9], pts[10], pts[11], pts[0], pts[1]], -5, -9), (crack + [pts[7], pts[6], pts[5], pts[4], pts[3]], 5, 9))
    for hp, off, ang in halves:
        with d.g(T(64 + off, 66, ang, 1)):
            d.shape(poly(hp), fill=d.lin([(0, "#e8506a"), (1, "#5a0a18")], -32, -40, 32, 40), ow=2.4)
            d.path(poly(hp), stroke=STEEL["light"], sw=1.6, op=0.6)
    d.path(poly([(64 + x, 66 + y) for x, y in crack], closed=False), stroke="#ffe0a0", sw=3, op=0.5)
    for a in (-160, -120, -60, -20, 30, 150):
        p0, p1 = polar(64, 64, 46, math.radians(a)), polar(64, 64, 56, math.radians(a))
        d.path(ribbon([p0, p1], [4, 0.5]), fill="#ffd8a0", op=0.9)


@status("#30b0c8", "#06283a")
def wet(d):
    p = EL["water"]
    droplet(d, 64, 56, 18, p)
    droplet(d, 34, 92, 11, p)
    droplet(d, 94, 94, 12, p)


@status("#9a4ad0", "#1e0a2a")
def cursed(d):
    d.glow(64, 60, 52, "#8a3ad0", 0.6)
    tendril(d, [(18, 110), (30, 92), (26, 74)], 8, EL["dark"])
    tendril(d, [(110, 110), (98, 92), (104, 74)], 8, EL["dark"])
    skull(d, 64, 64, 1.35, dict(dark="#4a3a5a", base="#b8a8c4", light="#f4ecff"), eye_glow="#d060ff")


@status(BUFF, "#3a3014")
def purged(d):
    rng = random.Random(6)
    pts = []
    for i in range(14):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(34, 52)
        pts.append((64 + r * math.cos(a), 64 + r * math.sin(a), rng.uniform(0.6, 1.2)))
    motes(d, pts, "#2a0a3a", glow_color="#8a3ad0", size=3.0)
    sun(d, 64, 64, 14, EL["light"], rays=8, ray_len=2.6)
    d.circle(64, 64, 34, stroke="#fff4c0", stroke_width=2.4, opacity=0.8)


@status(DEBUFF, "#3a060c")
def bleeding(d):
    # diagonal gash + dripping blood
    gash = qbez((24, 26), (60, 44), (100, 70), n=20)
    d.path(ribbon(gash, taper(20, 16, 0.0, 0.0)), fill="#1a0206", stroke=OUTLINE, stroke_width=2)
    d.path(ribbon(gash, taper(20, 8, 0.0, 0.0)), fill="#ff4a5a")
    d.path(ribbon([(p[0] - 1, p[1] - 2) for p in gash], taper(20, 2.4, 0.0, 0.0)), fill="#ffd0d4", op=0.8)
    pal = dict(dark="#4a0008", base="#c0101e", light="#ff8a90")
    droplet(d, 40, 70, 8, pal)
    droplet(d, 66, 90, 12, pal)
    droplet(d, 92, 96, 7, pal)
    d.path("M40,44 L40,58 M66,56 L66,74 M92,74 L92,86", stroke="#c0101e", sw=3)


@status("#e0b040", "#2a2208")
def stunned(d):
    cx, cy = 64, 64
    d.ellipse(cx, cy, 44, 16, stroke=OUTLINE, stroke_width=6)
    d.ellipse(cx, cy, 44, 16, stroke="#ffe080", stroke_width=2.6)
    for i, a in enumerate((200, 300, 60)):
        x, y = cx + 44 * math.cos(math.radians(a)), cy + 16 * math.sin(math.radians(a))
        r = (13, 11, 9)[i]
        d.glow(x, y, r * 1.6, "#ffd040", 0.8)
        d.shape(poly(star_pts(x, y, 5, r, r * 0.45)), fill=d.rad([(0, "#ffffff"), (0.5, "#ffe060"), (1, "#c88a10")], x, y, r), ow=2)
    for (x, y) in ((40, 30), (88, 98)):
        d.sparkle(x, y, 5, "#fff4c0", 0.9)


@status(BUFF, "#3a0c10")
def valor(d):
    with d.g(T(64, 66, 0, 1.12)):
        banner(d)


@status("#b080ff", "#1a0e3a")
def arcane_charge(d):
    cx, cy = 64, 64
    d.glow(cx, cy, 44, "#a060ff", 0.8)
    d.circle(cx, cy, 20 + 2.4, fill=OUTLINE)
    d.circle(cx, cy, 20, fill=d.rad([(0, "#ffffff"), (0.35, "#d0b0ff"), (0.8, "#7a3ae0"), (1, "#2a0e5a")], cx - 5, cy - 6, 24))
    d.circle(cx, cy, 38, stroke="#c8a8ff", stroke_width=1.6, opacity=0.6)
    for i in range(3):
        a = -math.pi / 2 + i * 2 * math.pi / 3
        x, y = polar(cx, cy, 38, a)
        d.glow(x, y, 12, "#c090ff", 0.9)
        d.path(poly([(x, y - 8), (x + 6, y), (x, y + 8), (x - 6, y)]), fill="#f4ecff", stroke=OUTLINE, stroke_width=1.6)


@status(BUFF, "#1a2030")
def guard(d):
    with d.g(T(64, 64, 0, 1.25)):
        heater_shield(d, w=64, h=76, field=CRIMSON, rim=STEEL, emblem="cross", boss=GOLD)


@status(BUFF, "#2a2410")
def haste(d):
    for i, (y, L) in enumerate(((44, 34), (62, 44), (80, 30))):
        d.path(ribbon([(10, y), (10 + L, y)], [0.5, 5]), fill="#fff0c0", op=0.7)
    with d.g(T(98, 78, 0, 1.18)):
        wing(d, GOLD)


@status("#40c060", "#0c2a14")
def regen(d):
    pal = dict(dark="#0a4a1a", base="#2ab04a", light="#b0ffb8")
    d.glow(64, 64, 50, "#40e060", 0.5)
    heart(d, 58, 68, 1.05, pal)
    cx, cy = 92, 36
    cr = poly([(cx - 4, cy - 14), (cx + 4, cy - 14), (cx + 4, cy - 4), (cx + 14, cy - 4), (cx + 14, cy + 4), (cx + 4, cy + 4), (cx + 4, cy + 14),
               (cx - 4, cy + 14), (cx - 4, cy + 4), (cx - 14, cy + 4), (cx - 14, cy - 4), (cx - 4, cy - 4)])
    d.shape(cr, fill=d.lin([(0, "#ffffff"), (1, "#6ae07a")], cx, cy - 14, cx, cy + 14), ow=2.2)
    for (x, y, s) in ((28, 30, 3), (100, 96, 3.5)):
        d.sparkle(x, y, s, "#d0ffd8", 0.9)


@status("#6ab8ff", "#0a1a34")
def shielded(d):
    cx, cy = 64, 66
    d.glow(cx, cy, 50, "#6ab8ff", 0.5)
    # hex lattice inside the bubble
    for k in range(-3, 4):
        for j in range(-3, 4):
            x = cx + k * 13 + (j % 2) * 6.5
            y = cy + j * 11.3
            if math.hypot(x - cx, y - cy) < 36:
                d.path(poly(ngon(x, y, 6.6, 6, rot0=0)), stroke="#9ad8ff", sw=1.1, op=0.45)
    dragon_bubble(d, cx, cy, 42, "#6ab8ff")
    d.circle(cx, cy, 44.5, stroke=OUTLINE, stroke_width=2)


# ------------------------------------------------------------------------------------------ attributes

def attribute(name, metal, inner):
    def deco(fn):
        ATTR_DRAW[name] = fn

        def build():
            d = Doc(name="at_" + name)
            octagon_bg(d, inner)
            with d.g("translate(64 64) scale(0.9) translate(-64 -64)"):
                fn(d)
            octagon_rim(d, metal)
            return d
        ATTRIBUTES[name] = build
        return fn
    return deco


@attribute("strength", GOLD, "#3a0e0c")
def a_strength(d):
    d.glow(64, 60, 50, "#ff5030", 0.4)
    with d.g(T(64, 64, 0, 1.3)):
        fist(d, dict(dark="#3a2410", base="#a8743a", light="#f4cc90"), CRIMSON, plated=False)


@attribute("agility", GOLD, "#0e2a1c")
def a_agility(d):
    d.glow(64, 60, 50, "#80ffb0", 0.3)
    for i, (y, L) in enumerate(((88, 40), (100, 54), (112, 36))):
        d.path(ribbon([(12, y), (12 + L, y - 8)], [0.5, 4]), fill="#d8ffe8", op=0.6)
    with d.g(T(62, 104, 35, 1.2)):
        feather(d, L=76, W=20)


@attribute("intelligence", GOLD, "#16103a")
def a_intelligence(d):
    d.glow(64, 44, 44, "#8a6aff", 0.7)
    with d.g(T(64, 84, 0, 1.15)):
        book(d, dict(dark="#10083a", base="#3a2a8a", light="#7a6ad0"))
    rune_ring(d, 64, 40, 18, "#d8c8ff", width=1.4, ticks=10, inner=False)
    d.path(poly(star_pts(64, 40, 4, 12, 3)), fill="#ffffff")
    for (x, y, s) in ((40, 30, 3), (90, 28, 2.6), (84, 54, 2.2)):
        d.sparkle(x, y, s, "#e8e0ff", 0.9)


@attribute("wisdom", GOLD, "#0e1c30")
def a_wisdom(d):
    d.glow(64, 60, 50, "#6a9ae0", 0.35)
    with d.g(T(64, 68, 0, 1.15)):
        owl(d)


@attribute("spirit", GOLD, "#08282a")
def a_spirit(d):
    p = dict(dark="#0a4a5a", base="#3ac8c8", light="#e0fff8", glow="#60f0e0")
    flame(d, 64, 92, 1.05, p)
    motes(d, [(34, 50, 0.9), (96, 44, 0.8), (88, 84, 0.7), (36, 86, 0.6)], "#e0fff8", glow_color="#60f0e0", size=2.2, diamonds=False)


@attribute("dexterity", GOLD, "#2a1e0a")
def a_dexterity(d):
    with d.g(T(58, 70, 0, 1.0)):
        target(d)
    with d.g(T(106, 22, -135, 1.0)):
        arrow(d, L=70)
