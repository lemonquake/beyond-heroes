"""bh-002 status badges (same rounded-square badge frame as icons_badges.STATUS)."""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, EL, STEEL, CRIMSON, GOLD, BRONZE, ARCANE, LEATHER, OUTLINE, f, poly, smooth, mix, lt, dk, ribbon,
                    taper, arc_pts, bez, qbez, star_pts, ngon, jag_line, polar, rrect_path, circle_path, lerp, faceted)
from bh_shapes import (T, sword, heater_pts, tower_shield, cuirass, fist, heart, hourglass, skull, bolt, zig_bolt, gust,
                       swirl, droplet, motes, rune_ring, impact_star, crystal, smooth_pts, teardrop)
from bh_frames import badge_bg, badge_rim

STATUS2 = {}
DEBUFF = "#b8322e"
BUFF = "#d0a040"
AE_C = "#7ff3ff"


def status(rim, inner):
    def deco(fn):
        def build():
            d = Doc(name="st2_" + fn.__name__)
            badge_bg(d, inner, rim)
            with d.g("translate(64 64) scale(0.86) translate(-64 -64)"):
                fn(d)
            badge_rim(d, rim)
            return d
        STATUS2[fn.__name__] = build
        return fn
    return deco


def down_arrow(d, x, y, s, col="#ff5a4a"):
    pts = [(x - 7 * s, y - 6 * s), (x - 3 * s, y - 6 * s), (x - 3 * s, y - 14 * s), (x + 3 * s, y - 14 * s), (x + 3 * s, y - 6 * s),
           (x + 7 * s, y - 6 * s), (x, y + 2 * s)]
    d.shape(poly(pts), fill=d.lin([(0, lt(col, 0.4)), (1, dk(col, 0.35))], x, y - 14 * s, x, y + 2 * s), ow=1.8)


def up_chevron(d, x, y, s, col=GOLD):
    pts = [(x - 10 * s, y + 4 * s), (x, y - 6 * s), (x + 10 * s, y + 4 * s), (x + 10 * s, y + 9 * s), (x, y - 1 * s), (x - 10 * s, y + 9 * s)]
    d.shape(poly(pts), fill=d.lin([(0, col["light"]), (1, col["dark"])], x, y - 6 * s, x, y + 9 * s), ow=1.6)


@status("#6ac040", "#0e2a0a")
def poisoned(d):
    p = dict(dark="#0e4a0a", base="#5ad02a", light="#e0ffb0", glow="#7aff3a")
    d.glow(64, 72, 44, p["glow"], 0.35)
    droplet(d, 64, 72, 22, p)
    # skull mark inside the drop
    skull(d, 64, 76, 0.42, pal=dict(dark="#0a2a06", base="#1a4a10", light="#2a6a1a"))
    for (x, y, r) in ((30, 48, 5), (98, 40, 4), (96, 92, 6), (32, 96, 3.5), (84, 22, 3)):
        d.circle(x, y, r + 1.4, fill=OUTLINE, opacity=0.8)
        d.circle(x, y, r, fill=d.rad([(0, p["light"]), (1, p["base"])], x - r * 0.4, y - r * 0.4, r * 1.3))
        d.circle(x - r * 0.35, y - r * 0.35, r * 0.25, fill="#ffffff", opacity=0.8)


@status("#6a8ab8", "#0c1628")
def slowed(d):
    hourglass(d, 64, 62, 1.25, frame=dict(dark="#2a3448", base="#8a9ab8", light="#e8f0ff"), sand=dict(dark="#1a3a6a", base="#4a7ad0", light="#b0d0ff"))
    # heavy chain across
    for i in range(7):
        x = 20 + i * 14.5
        y = 96 + (3 if i % 2 else -2)
        if i % 2:
            d.path(f"M{f(x - 5)},{f(y)} L{f(x + 5)},{f(y)}", stroke=OUTLINE, sw=6)
            d.path(f"M{f(x - 5)},{f(y)} L{f(x + 5)},{f(y)}", stroke=STEEL["base"], sw=3)
        else:
            d.ellipse(x, y, 8, 4.5, stroke=OUTLINE, stroke_width=5)
            d.ellipse(x, y, 8, 4.5, stroke=STEEL["light"], stroke_width=2.4)


@status("#9a6ad0", "#180c2a")
def silenced(d):
    # arcane sigil sealed by a red slash
    d.glow(64, 64, 44, "#a060ff", 0.4)
    rune_ring(d, 64, 64, 34, "#c8a0ff", width=2.4, ticks=14, seed=2)
    d.path(poly(star_pts(64, 64, 5, 18, 7)), fill="#e0c8ff", stroke=OUTLINE, stroke_width=1.6)
    # stitched mouth seal / crossed slash
    d.path("M28,100 L100,28", stroke=OUTLINE, sw=12)
    d.path("M28,100 L100,28", stroke="#d02a2a", sw=7)
    d.path("M30,96 L96,30", stroke="#ff9a8a", sw=1.6, op=0.8)
    for t in (0.3, 0.5, 0.7):
        x, y = lerp(28, 100, t), lerp(100, 28, t)
        d.path(f"M{f(x - 6)},{f(y - 6)} L{f(x + 6)},{f(y + 6)}", stroke="#2a0606", sw=2.2)


@status(DEBUFF, "#2a1010")
def weakened(d):
    # snapped sword + downward arrow
    with d.g(T(54, 84, 30, 1.0)):
        sword(d, L=34, W=12, pal=dict(dark="#3a3a40", base="#8a8a94", light="#dcdce4"))
    frag = [(78, 30), (92, 22), (98, 30), (86, 38)]
    d.shape(poly(frag), fill=d.lin([(0, "#dcdce4"), (1, "#5a5a64")], 78, 22, 98, 38), ow=2)
    for (a, b) in (((76, 40), (86, 34)), ((70, 46), (72, 38))):
        d.path(poly([a, b], closed=False), stroke="#ffd0a0", sw=1.6, op=0.8)
    down_arrow(d, 94, 88, 1.6)


@status(DEBUFF, "#20161a")
def armor_broken(d):
    with d.g(T(64, 66, 0, 1.25)):
        cuirass(d, w=62, h=62, pal=dict(dark="#2a2e36", base="#7a8290", light="#d8dee8"), trim=BRONZE)
        rng = random.Random(3)
        crack = jag_line((-4, -30), (6, 32), 7, 5, rng)
        d.path(poly(crack, closed=False), stroke=OUTLINE, sw=3.4)
        d.path(poly(crack, closed=False), stroke="#ffb070", sw=1.2)
        br = jag_line(crack[3], (-20, 6), 3, 3, rng)
        d.path(poly(br, closed=False), stroke=OUTLINE, sw=2.4)
    for (x, y, a) in ((26, 36, 20), (100, 44, -30), (96, 96, 45)):
        faceted(d, [(x - 5, y - 3), (x + 4, y - 6), (x + 6, y + 3), (x - 2, y + 6)], (x, y), "#3a3e46", "#dcdce4", ow=1.6)


@status("#7ac8a0", "#0a2418")
def windswept(d):
    p = EL["wind"]
    for (pts, w) in (([(18, 44), (48, 36), (80, 40), (98, 30), (92, 20), (82, 26)], 9),
                     ([(14, 70), (52, 64), (90, 70), (108, 60), (104, 48), (94, 54)], 11),
                     ([(24, 96), (56, 92), (84, 98), (96, 90)], 7)):
        gust(d, smooth_pts(pts, 30), w, p["base"], hl=p["light"])
    # tumbling leaves
    for (x, y, a) in ((40, 54, 30), (74, 84, -40), (100, 100, 70)):
        with d.g(T(x, y, a, 1)):
            lf = smooth([(0, -8), (5, -2), (0, 8), (-5, -2)], tension=0.6)
            d.path(lf, fill="#6aa040", stroke=OUTLINE, stroke_width=1.4)
            d.path("M0,-7 L0,7", stroke="#2a4a1a", sw=0.8)


@status(BUFF, "#2a1c08")
def empowered(d):
    d.glow(64, 64, 48, "#ffc040", 0.55)
    for a in range(0, 360, 30):
        p0, p1 = polar(64, 64, 36, math.radians(a)), polar(64, 64, 52, math.radians(a))
        d.path(ribbon([p0, p1], [5, 0.4]), fill="#ffe090", op=0.7)
    with d.g(T(64, 66, 0, 1.2)):
        fist(d, pal=dict(dark="#6a4a10", base="#d8a840", light="#fff0b0"), trim=CRIMSON)
    up_chevron(d, 100, 30, 1.0)
    up_chevron(d, 100, 44, 0.8)


@status(BUFF, "#1c1c22")
def fortified(d):
    # stone wall behind a tower shield
    st = dict(dark="#2a2622", base="#6a6258", light="#b0a896")
    for row in range(4):
        y = 30 + row * 18
        off = 0 if row % 2 else 12
        for k in range(-1, 5):
            x = 14 + k * 24 + off
            if x < 8 or x > 104:
                continue
            d.path(rrect_path(x, y, 22, 16, 2), fill=d.lin([(0, st["light"]), (1, st["dark"])], x, y, x + 22, y + 16), stroke=OUTLINE, stroke_width=1.4)
    with d.g(T(64, 66, 0, 1.0)):
        tower_shield(d, w=50, h=76, face=dict(dark="#3a4250", base="#aab4c4", light="#ffffff"), band=GOLD)
        d.path(poly(star_pts(0, -2, 4, 10, 3)), fill=GOLD["light"], stroke=OUTLINE, stroke_width=1)


@status("#b080ff", "#140a30")
def overcharged(d):
    p = EL["lightning"]
    d.glow(64, 64, 50, "#b070ff", 0.6)
    crystal(d, 64, 62, 16, dict(dark="#3a1a8a", base="#a070ff", light="#ffffff", glow="#b070ff"), stretch=1.8, glow=False)
    rng = random.Random(4)
    for (a, b) in (((64, 40), (30, 22)), ((64, 40), (100, 26)), ((64, 84), (28, 104)), ((64, 84), (102, 100)), ((48, 62), (18, 64)), ((80, 62), (110, 60))):
        bolt(d, jag_line(a, b, 4, 4, rng), width=3.2, pal=p, glow=False)
    motes(d, [(32, 40, 0.8), (96, 44, 0.8), (40, 90, 0.7), (92, 86, 0.7)], "#fff4c0", glow_color="#b070ff", size=2.2)


@status(BUFF, "#1a1a2a")
def resolute(d):
    # sword planted before a laurel wreath
    lau = dict(dark="#1a4a1a", base="#4aa04a", light="#b8f0a0")
    for sx in (-1, 1):
        pts = arc_pts(64, 66, 38, math.radians(90 + sx * 20), math.radians(90 + sx * 160), 9)
        for i, (x, y) in enumerate(pts):
            a = math.atan2(y - 66, x - 64) + sx * 1.2
            lf = [(x, y), (x + math.cos(a) * 9 - math.sin(a) * 4, y + math.sin(a) * 9 + math.cos(a) * 4), (x + math.cos(a) * 14, y + math.sin(a) * 14),
                  (x + math.cos(a) * 9 + math.sin(a) * 4, y + math.sin(a) * 9 - math.cos(a) * 4)]
            d.path(smooth(lf, tension=0.5), fill=d.lin([(0, lau["light"]), (1, lau["dark"])], x, y, lf[2][0], lf[2][1]), stroke=OUTLINE, stroke_width=1.2)
    with d.g(T(64, 100, 0, 1.0)):
        sword(d, L=70, W=13, pal=dict(dark="#3a4250", base="#b4bfcc", light="#ffffff"), hilt=GOLD)
    d.path("M40,104 Q64,98 88,104", stroke=OUTLINE, sw=5)
    d.path("M40,104 Q64,98 88,104", stroke="#6a4a2a", sw=3)


@status(DEBUFF, "#2a0608")
def badly_hurt(d):
    d.glow(64, 62, 46, "#ff2020", 0.45)
    heart(d, 64, 62, 1.15, dict(dark="#3a0408", base="#c0141e", light="#ff8a8a"))
    rng = random.Random(9)
    crack = jag_line((64, 46), (60, 92), 6, 6, rng)
    d.path(poly(crack, closed=False), stroke=OUTLINE, sw=4)
    d.path(poly(crack, closed=False), stroke="#1a0204", sw=2)
    for (x, y, r) in ((44, 96, 4.5), (56, 104, 3.4), (80, 100, 4)):
        d.path(teardrop(x, y, r, r * 2.2), fill=d.rad([(0, "#ff6a6a"), (1, "#6a0408")], x - 1, y - 1, r * 1.8), stroke=OUTLINE, stroke_width=1.4)
