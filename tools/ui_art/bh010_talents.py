"""bh-010 talent icons for the Ranger and Shadowblade trees (icons/talents/, 128x128). Same round bezel as
icons_talents.py: minor attribute nodes thin ring, normal nodes studded ring, keystones spiked star-ring.
Registered in build_all.py as category "talents10" (registry TALENTS10)."""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, EL, STEEL, CRIMSON, GOLD, BRONZE, LEATHER, WOOD, BONE, OUTLINE, f, poly, smooth, mix, lt, dk,
                    ribbon, taper, arc_pts, qbez, star_pts, ngon, jag_line, teardrop, polar, rrect_path, circle_path)
from bh_shapes import (T, bow, heart, impact_star, eye, skull, rune_ring, motes, swirl, gust, flame, ice_shard, bolt,
                       zig_bolt, droplet, smooth_pts, slash_arc, crystal)
from bh_frames import backdrop, vignette, talent_frame, RANGER_METAL, SHADOW_METAL
from bh010_motifs import (BRIGHT_STEEL, DARK_STEEL, VENOM, VIOLET, BLOOD, FOREST, FLETCH_GREEN, FLETCH_WHITE, arrow2,
                          dagger2, claw, trap_jaws, bullseye, crosshair, leaf, boot, footprint, vial, fang, gear, smoke,
                          pips, hood_silhouette, cracked_skull, speed_lines, shuriken, knife)
from icons_badges import feather, wing
from icons_talents import laurel, crescent

TALENTS10 = {}
METAL = {"ranger": RANGER_METAL, "shadowblade": SHADOW_METAL}


def talent(cls, inner, haze=None, haze2=None, kind="normal", scale=None):
    def deco(fn):
        def build():
            d = Doc(name="bh10t_" + fn.__name__)
            backdrop(d, inner, haze=haze, haze2=haze2, cy=64)
            s = scale or {"normal": 0.8, "keystone": 0.74, "minor": 0.66}[kind]
            with d.g(f"translate(64 64) scale({f(s)}) translate(-64 -64)"):
                fn(d)
            vignette(d, 0.55, cy=64)
            talent_frame(d, METAL[cls], kind)
            return d
        TALENTS10[fn.__name__] = build
        return fn
    return deco


def arrow_at(d, x0, y0, deg, L, s=1.0, **kw):
    with d.g(T(x0, y0, deg + 90, s)):
        arrow2(d, L=L, **kw)
    return polar(x0, y0, L * s, math.radians(deg))


GOLD_HEAD = dict(dark="#6a4a14", base="#ffd070", light="#fffbe6")

# ------------------------------------------------------------------------------------------ ranger


@talent("ranger", "#1a2410", haze="#8ab040", kind="minor")
def r_dex(d: Doc):
    # dexterity: a drawn arrow balanced on a fingertip-steady green gem
    d.glow(64, 64, 40, "#9aff9a", 0.35)
    arrow_at(d, 22, 106, -45, 80, 1.05, head=BRIGHT_STEEL, fletch=FLETCH_GREEN, head_scale=1.4, shaft_w=2.6)
    arrow_at(d, 106, 106, -135, 80, 1.05, head=BRIGHT_STEEL, fletch=FLETCH_WHITE, head_scale=1.4, shaft_w=2.6)
    from bh_shapes import gem
    gem(d, 64, 72, 13, dict(dark="#0e3a14", base="#3ac050", light="#d0ffc0"), sides=6)


@talent("ranger", "#1e1a0a", haze="#b88a3a")
def r_bow(d: Doc):
    d.glow(64, 56, 48, "#ffe8a0", 0.3)
    laurel(d, 64, 64, 44, dict(dark="#1a3a14", base="#4a8a3a", light="#b8e0a0"), leaves=7, a_from=95, a_to=250)
    with d.g(T(58, 64, 0, 1.0)):
        bow(d, H=96, pal=WOOD, limb=7)


@talent("ranger", "#2a0e0a", haze="#c0301a")
def r_crit(d: Doc):
    impact_star(d, 86, 42, 30, "#ffffff", "#ff4a3a", n=10, inner=0.26)
    arrow_at(d, 20, 108, -45, 76, 1.0, head=BRIGHT_STEEL, fletch=FLETCH_GREEN, head_scale=1.5, shaft_w=2.6)
    rng = random.Random(4)
    for i in range(6):
        a = rng.uniform(-math.pi, math.pi)
        x, y = polar(86, 42, rng.uniform(22, 32), a)
        d.path(teardrop(x, y, 2.2, 5.5, lean=math.cos(a) * 3), fill=CRIMSON["light"], stroke=OUTLINE, stroke_width=0.8)


@talent("ranger", "#101c20", haze="#6ab0a0")
def r_focus(d: Doc):
    cx, cy = 64, 64
    for r, op in ((44, 0.25), (34, 0.45), (24, 0.7)):
        d.circle(cx, cy, r, stroke="#e8f0c0", stroke_width=2.2, opacity=op)
    crosshair(d, cx, cy, 18, color="#9aff9a", sw=2.4, gap=0.4, ticks=False)
    d.glow(cx, cy, 12, "#ffffff", 0.9)
    for i in range(8):
        a = i * math.pi / 4
        p0, p1 = polar(cx, cy, 50, a), polar(cx, cy, 30, a)
        d.path(ribbon([p0, p1], [0.5, 4]), fill="#e8f0c0", op=0.6)


@talent("ranger", "#12200e", haze="#8ad07a")
def r_evasion(d: Doc):
    # cloak swirl with leaves: the hunter slipping aside
    for i, (r0, r1, a0) in enumerate(((10, 46, 0.3), (8, 40, 2.4), (6, 34, 4.5))):
        swirl(d, 64, 64, r0, r1, a0, 0.55, 12 - i * 2, FOREST["base"], n=30)
        swirl(d, 64, 64, r0, r1, a0, 0.55, 4, FOREST["light"], n=30, outline=False)
    for (x, y, a) in ((36, 36, -30), (96, 44, 50), (86, 96, 140), (30, 88, -130)):
        with d.g(T(x, y, a, 1.0)):
            leaf(d, L=20, W=9, pal=FOREST)


@talent("ranger", "#101a18", haze="#9ee0c0")
def r_speed(d: Doc):
    arrow_at(d, 16, 78, -20, 96, 1.0, head=BRIGHT_STEEL, fletch=FLETCH_WHITE, head_scale=1.4, shaft_w=2.6)
    with d.g(T(46, 64, -20, 0.62)):
        wing(d, dict(dark="#6a7078", base="#e0e4ea", light="#ffffff"))
    speed_lines(d, [(8, 96, 44, 84, 4), (10, 108, 50, 96, 3), (20, 116, 56, 106, 2)], "#e8ffe0", 0.6)


@talent("ranger", "#1a140a", haze="#8a6a3a")
def r_traps(d: Doc):
    with d.g(T(64, 66, 0, 1.2)):
        trap_jaws(d, w=72, pal=dict(dark="#2e343c", base="#9aa4b0", light="#f2f6fa"), open_=0.85, teeth=6)


@talent("ranger", "#16142a", haze="#ff6a14", haze2="#6ad8ff")
def r_elemental_arrows(d: Doc):
    heads = ((EL["fire"], -112), (EL["ice"], -90), (EL["lightning"], -68))
    for pal, a in heads:
        tip = arrow_at(d, *polar(64, 118, 4, math.radians(a)), a, 86, 1.0, head=pal, fletch=FLETCH_GREEN, head_scale=1.5, shaft_w=2.4)
        d.glow(tip[0], tip[1] + 6, 16, pal["glow"], 0.9)


@talent("ranger", "#10160a", haze="#c8a040", haze2="#6a8a2a", kind="keystone")
def keystone_sniper(d: Doc):
    cx, cy = 64, 60
    d.glow(cx, cy, 50, "#ffd070", 0.35)
    crosshair(d, cx, cy, 42, color="#ff5a3a", sw=3, gap=0.6)
    d.circle(cx, cy, 24, fill=d.rad([(0, "#2a4a2a"), (1, "#08100a")], cx - 6, cy - 6, 28), stroke=OUTLINE, stroke_width=3)
    eye(d, cx, cy, 18, 8, dict(dark="#5a3a0a", base="#e0a020", light="#fff0a0"), white="#f4ecd8", ow=2)
    arrow_at(d, 14, 118, -45, 60, 1.0, head=GOLD_HEAD, fletch=FLETCH_GREEN, head_scale=1.5, shaft_w=2.6)


@talent("ranger", "#0e1e1a", haze="#9ee0c0", haze2="#ffffff", kind="keystone")
def keystone_windrunner(d: Doc):
    pal = EL["wind"]
    cx, cy = 64, 64
    d.glow(cx, cy, 50, pal["glow"], 0.45)
    for i in range(3):
        swirl(d, cx, cy, 6, 46, i * 2 * math.pi / 3, 0.6, 10, pal["base"], n=36)
        swirl(d, cx, cy, 6, 46, i * 2 * math.pi / 3, 0.6, 3.5, pal["light"], n=36, outline=False)
    with d.g(T(cx, cy + 22, 20, 0.62)):
        feather(d, L=70, W=18, pal=dict(dark="#6a7078", base="#e0e4ea", light="#ffffff"))
    with d.g(T(cx - 4, cy + 30, -8, 0.7)):
        boot(d, pal=dict(dark="#2a1a0c", base="#7a5030", light="#c89868"), trim=GOLD, cuff=FOREST)


@talent("ranger", "#1a1208", haze="#c8962e", haze2="#6a4a1a", kind="keystone")
def keystone_traplord(d: Doc):
    with d.g(T(64, 76, 0, 1.15)):
        trap_jaws(d, w=72, pal=dict(dark="#3a2a10", base="#c8a060", light="#fff0c0"), open_=0.8, teeth=6)
    crown = [(44, 44), (44, 22), (54, 32), (64, 16), (74, 32), (84, 22), (84, 44)]
    d.shape(poly(crown), fill=d.lin([(0, GOLD["light"]), (0.5, GOLD["base"]), (1, GOLD["dark"])], 0, 16, 0, 44), ow=2.4)
    for (x, y) in ((44, 22), (64, 16), (84, 22)):
        d.circle(x, y, 3, fill=GOLD["light"], stroke=OUTLINE, stroke_width=1.2)
    d.circle(64, 36, 3.6, fill="#3ac050", stroke=OUTLINE, stroke_width=1)


# ------------------------------------------------------------------------------------------ shadowblade

@talent("shadowblade", "#14102a", haze="#6a8ad0", kind="minor")
def s_agi(d: Doc):
    # agility: a thrown knife arcing through a looping motion trail
    pts = [(64 + 36 * math.cos(t) * (1 if t < math.pi else 1), 64 + 22 * math.sin(2 * t) * 0.9) for t in [i / 39 * 2 * math.pi for i in range(40)]]
    d.path(ribbon(pts, taper(40, 9, 0.1, 1.0, peak=1.0)), fill="#d8c8ff", op=0.8)
    with d.g(T(pts[-1][0], pts[-1][1], 60, 1.4)):
        knife(d, L=30, W=8)
    d.glow(64, 64, 12, "#b070ff", 0.8)


@talent("shadowblade", "#16101e", haze="#8a6ab0")
def s_dagger(d: Doc):
    d.glow(64, 50, 50, "#c8b0ff", 0.3)
    laurel(d, 64, 64, 44, dict(dark="#2a0a4a", base="#6a4ab0", light="#d8c8ff"), leaves=7, a_from=95, a_to=250)
    with d.g(T(64, 96, 0, 1.15)):
        dagger2(d, L=62, W=13)


@talent("shadowblade", "#2a0a14", haze="#c0141e")
def s_crit(d: Doc):
    impact_star(d, 88, 40, 30, "#ffffff", "#ff3a5a", n=10, inner=0.26)
    with d.g(T(38, 96, 45, 1.05)):
        dagger2(d, L=60, W=12, glow="#c090ff")
    rng = random.Random(2)
    for i in range(7):
        a = rng.uniform(-math.pi, math.pi)
        x, y = polar(88, 40, rng.uniform(22, 32), a)
        d.path(teardrop(x, y, 2.2, 5.5, lean=math.cos(a) * 3), fill=BLOOD["light"], stroke=OUTLINE, stroke_width=0.8)


@talent("shadowblade", "#140a22", haze="#8a3ae0")
def s_combo(d: Doc):
    pts = [polar(64, 70, 36, math.radians(a)) for a in (-162, -126, -90, -54, -18)]
    pips(d, pts, lit=5, color=VIOLET, r=7)
    for (a0, a1) in ((200, 250), (260, 310)):
        slash_arc(d, 64, 96, 44, math.radians(a0), math.radians(a1), 7, dict(dark="#2a0a4a", base="#d8c0ff", light="#ffffff", glow="#b060ff"))
    d.glow(64, 80, 16, "#c070ff", 0.8)
    d.path(poly(star_pts(64, 80, 4, 12, 3)), fill="#ffffff")


@talent("shadowblade", "#120c1e", haze="#6a4ab0")
def s_evasion(d: Doc):
    for (x, op) in ((44, 0.3), (58, 0.55)):
        with d.g(T(x, 112, 0, 0.9), op=op):
            hood_silhouette(d, "#b89aff", outline=False, lean=-0.8)
    with d.g(T(80, 112, 0, 0.95)):
        hood_silhouette(d, d.lin([(0, "#7a68a0"), (0.5, "#3a2e52"), (1, "#0a0612")], -26, 0, 28, 0), lean=-0.8)
    speed_lines(d, [(10, 60, 40, 60, 3), (14, 76, 40, 76, 3), (10, 92, 36, 92, 2)], "#e2d4ff", 0.6)


@talent("shadowblade", "#0c0814", haze="#4a2a6a")
def s_stealth(d: Doc):
    hood = [(64, 20), (92, 34), (104, 74), (100, 108), (28, 108), (24, 74), (36, 34)]
    dd = smooth(hood, tension=0.5)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, "#5a4a7a"), (0.5, "#2a2240"), (1, "#0a0612")], 24, 20, 104, 108))
    op_ = smooth([(64, 38), (86, 50), (90, 82), (64, 100), (38, 82), (42, 50)], tension=0.5)
    d.path(op_, fill="#030206")
    # closing eyes (half-lidded slits)
    for sx in (-1, 1):
        x = 64 + sx * 12
        d.glow(x, 70, 7, "#b070ff", 0.8)
        d.path(f"M{x - 7},70 Q{x},66 {x + 7},70 Q{x},72 {x - 7},70 Z", fill="#e2c4ff")
    motes(d, [(30, 30, 0.8), (100, 26, 0.7), (104, 100, 0.6)], "#b89aff", glow_color="#8a3ae0", size=2)


@talent("shadowblade", "#0e1a0a", haze="#5ad02a")
def s_poison(d: Doc):
    d.glow(64, 70, 44, VENOM["glow"], 0.35)
    droplet(d, 64, 72, 22, VENOM)
    skull(d, 64, 76, 0.42, pal=dict(dark="#0a2a06", base="#1a4a10", light="#2a6a1a"))
    with d.g(T(64, 30, 180, 0.8)):
        pass
    for (x, y, r) in ((30, 44, 5), (98, 40, 4), (96, 96, 5.5), (32, 96, 3.5)):
        d.circle(x, y, r + 1.4, fill=OUTLINE, opacity=0.8)
        d.circle(x, y, r, fill=d.rad([(0, VENOM["light"]), (1, VENOM["base"])], x - r * 0.4, y - r * 0.4, r * 1.3))


@talent("shadowblade", "#2a0608", haze="#c0141e")
def s_bleed(d: Doc):
    for (p0, p1) in (((24, 30), (88, 94)), ((40, 22), (104, 86))):
        pts = qbez(p0, ((p0[0] + p1[0]) / 2 + 6, (p0[1] + p1[1]) / 2 - 6), p1, n=18)
        d.path(ribbon(pts, taper(18, 12, 0.0, 0.0, peak=0.5)), stroke=OUTLINE, stroke_width=1.6)
        d.path(ribbon(pts, taper(18, 12, 0.0, 0.0, peak=0.5)), fill=d.lin([(0, "#6a0a18"), (0.5, "#ff6a6a"), (1, "#6a0a18")], *p0, *p1))
    for (x, y, r) in ((48, 84, 5), (60, 98, 4), (40, 104, 3.5), (74, 108, 3)):
        d.path(teardrop(x, y, r, r * 2.3), fill=d.rad([(0, BLOOD["light"]), (1, BLOOD["dark"])], x - 1, y - 1, r * 2), stroke=OUTLINE, stroke_width=1.3)


@talent("shadowblade", "#12081e", haze="#9a3ae0", haze2="#c0141e", kind="keystone")
def keystone_deathmark(d: Doc):
    cx, cy = 64, 64
    d.glow(cx, cy, 54, "#9a3ae0", 0.6)
    crosshair(d, cx, cy, 40, color="#c060ff", sw=2.6, gap=0.62)
    skull(d, cx, cy + 4, 0.95, pal=dict(dark="#3a3050", base="#b8b0cc", light="#f4f0ff"), eye_glow="#ff3a5a")
    for sx in (-1, 1):
        with d.g(T(cx + sx * 36, cy + 34, sx * 45, 0.7)):
            dagger2(d, L=46, W=10)


@talent("shadowblade", "#100c20", haze="#8a8aff", haze2="#b060ff", kind="keystone")
def keystone_phantom(d: Doc):
    cx, cy = 64, 64
    d.glow(cx, cy, 52, "#a080ff", 0.5)
    smoke(d, [(36, 90, 14), (92, 90, 14), (64, 98, 16)], top="#8a80a8", bottom="#2a2438", op=0.85)
    # ghostly mask
    mask = [(64, 24), (88, 34), (94, 60), (84, 88), (64, 98), (44, 88), (34, 60), (40, 34)]
    dd = smooth(mask, tension=0.5)
    d.path(dd, stroke=OUTLINE, sw=4.4, op=0.9)
    d.path(dd, fill=d.lin([(0, "#f4f0ff", 0.95), (0.6, "#b8a8e0", 0.8), (1, "#6a5aa0", 0.5)], 40, 24, 88, 98))
    for sx in (-1, 1):
        ey = smooth([(64 + sx * 6, 56), (64 + sx * 20, 50), (64 + sx * 22, 60), (64 + sx * 10, 64)], tension=0.6)
        d.path(ey, fill="#0a0414")
        d.glow(64 + sx * 15, 58, 6, "#c070ff", 1.0)
    d.path("M56,80 Q64,84 72,80", stroke="#0a0414", sw=2.4)


@talent("shadowblade", "#0e1a0a", haze="#5ad02a", haze2="#6a2ab0", kind="keystone")
def keystone_plague(d: Doc):
    smoke(d, [(30, 60, 18), (54, 44, 22), (82, 46, 22), (100, 64, 16), (44, 76, 16), (80, 76, 18)], top="#8ac06a", bottom="#1a3a14", op=0.9)
    skull(d, 64, 62, 0.8, pal=dict(dark="#2a4a1a", base="#b8d8a0", light="#f0ffe0"), eye_glow="#7aff3a")
    with d.g(T(64, 100, 0, 0.62)):
        vial(d, liquid=VENOM)
    for (x, y) in ((30, 100), (98, 100)):
        d.path(teardrop(x, y, 3.4, 8), fill=VENOM["base"], stroke=OUTLINE, stroke_width=1.2)
