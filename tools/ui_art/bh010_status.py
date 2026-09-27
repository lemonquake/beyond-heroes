"""bh-010 status badges (icons/status/, 128x128) in the rounded-square badge frame of icons_badges / icons_status2.
Buffs use the gold rim, debuffs the red rim; the eight aura buffs reuse the aura emblems inside a small halo ring, with
the rim coloured by aura type (red-gold offence, blue-silver defence).
Registered in build_all.py as category "status10" (registry STATUS10)."""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, EL, STEEL, CRIMSON, GOLD, BRONZE, BONE, OUTLINE, f, poly, smooth, mix, lt, dk, ribbon, taper,
                    arc_pts, qbez, star_pts, ngon, jag_line, teardrop, polar, rrect_path, circle_path)
from bh_shapes import T, skull, eye, rune_ring, motes, bow, impact_star, heater_pts, smooth_pts, swirl
from bh_frames import badge_bg, badge_rim, aura_halo
from bh010_motifs import (BRIGHT_STEEL, VIOLET, BLOOD, FOREST, web, crosshair, pips, hood_silhouette, speed_lines,
                          rune_glyph, arrow2, FLETCH_GREEN)
import icons_skills_bh010 as SK

STATUS10 = {}
DEBUFF = "#b8322e"
BUFF = "#d0a040"
AURA_RIM = {"off": "#e0703a", "def": "#8aa4d8"}


def status(rim, inner):
    def deco(fn):
        def build():
            d = Doc(name="st10_" + fn.__name__)
            badge_bg(d, inner, rim)
            with d.g("translate(64 64) scale(0.86) translate(-64 -64)"):
                fn(d)
            badge_rim(d, rim)
            return d
        STATUS10[fn.__name__] = build
        return fn
    return deco


@status("#b8b0a0", "#1a1816")
def webbed(d):
    web(d, 64, 64, 54, color="#f0ece0", spokes=10, rings=5, op=0.95, sw=1.8)
    # caught fly-like victim silhouette: a trapped boot tangled in the middle
    d.circle(64, 64, 10, fill=d.rad([(0, "#f8f4e8"), (1, "#8a8478")], 60, 60, 12), stroke=OUTLINE, stroke_width=2)
    for a in (20, 70, 130, 200, 250, 320):
        p0, p1 = polar(64, 64, 8, math.radians(a)), polar(64, 64, 14, math.radians(a + 25))
        d.path(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}", stroke="#ffffff", sw=1.2, op=0.9)


@status(DEBUFF, "#1a0a20")
def feared(d):
    d.glow(64, 60, 46, "#8a3ae0", 0.4)
    skull(d, 58, 62, 1.1, pal=dict(dark="#5a5070", base="#d0c8e0", light="#fbf8ff"), eye_glow="#c060ff")
    # fleeing motion: the skull is being chased off to the left
    speed_lines(d, [(84, 44, 118, 40, 4), (88, 60, 120, 60, 5), (84, 78, 116, 82, 4)], "#e2c4ff", 0.7)
    for (x, y) in ((30, 30), (98, 100)):
        d.path(teardrop(x, y, 3, 7), fill="#a8d8ff", stroke=OUTLINE, stroke_width=1.2)


@status(DEBUFF, "#2a0a08")
def marked(d):
    d.glow(64, 64, 44, "#ff3a2a", 0.4)
    crosshair(d, 64, 64, 34, color="#ff4a3a", sw=3.2, gap=0.45)
    d.circle(64, 64, 14, stroke=OUTLINE, stroke_width=6)
    d.circle(64, 64, 14, stroke="#ffb0a0", stroke_width=2.6)
    d.circle(64, 64, 4, fill="#ff3a2a", stroke=OUTLINE, stroke_width=1.4)


@status("#8a6ad0", "#0e0a18")
def stealth(d):
    hood = [(64, 16), (94, 32), (108, 74), (104, 112), (24, 112), (20, 74), (34, 32)]
    dd = smooth(hood, tension=0.5)
    d.path(dd, stroke=OUTLINE, sw=5, op=0.8)
    d.path(dd, fill=d.lin([(0, "#6a5a8a", 0.85), (0.5, "#2a2240", 0.7), (1, "#0a0612", 0.4)], 20, 16, 108, 112))
    d.path(smooth([(64, 36), (88, 50), (92, 84), (64, 104), (36, 84), (40, 50)], tension=0.5), fill="#030206")
    for sx in (-1, 1):
        x = 64 + sx * 13
        d.glow(x, 70, 8, "#b070ff", 0.9)
        # eyelid closing: thin slit with a heavy upper lid
        d.path(f"M{x - 8},70 Q{x},67 {x + 8},70 Q{x},71.6 {x - 8},70 Z", fill="#e2c4ff")
        d.path(f"M{x - 9},69 Q{x},64 {x + 9},69", stroke="#6a5a8a", sw=2.2)
    for (x, y) in ((22, 24), (106, 30), (110, 104)):
        d.circle(x, y, 2, fill="#b89aff", opacity=0.6)


@status(BUFF, "#160a24")
def poised(d):
    pts = [polar(64, 76, 40, math.radians(a)) for a in (-160, -125, -90, -55, -20)]
    pips(d, pts, lit=5, color=VIOLET, r=8.5)
    d.glow(64, 80, 22, "#c070ff", 0.8)
    d.path(poly(star_pts(64, 82, 4, 16, 4)), fill="#ffffff", stroke=OUTLINE, stroke_width=1.2)


@status(BUFF, "#141c0e")
def steady(d):
    d.glow(64, 64, 44, "#9aff9a", 0.3)
    crosshair(d, 64, 60, 30, color="#b8f0a0", sw=2.6, gap=0.45)
    with d.g(T(34, 64, 0, 0.9)):
        bow(d, H=96, pal=dict(dark="#2a1608", base="#6e4424", light="#b88452"), limb=7)
    with d.g(T(40, 60, 90, 1.0)):
        arrow2(d, L=64, head=BRIGHT_STEEL, fletch=FLETCH_GREEN, head_scale=1.3, shaft_w=2.4)


def _aura_status(name):
    color, kind = SK.AURA_COLORS[name]

    def fn(d):
        aura_halo(d, color, r=40, rays=False)
        with d.g("translate(64 64) scale(0.7) translate(-64 -64)"):
            SK.AURA_EMBLEMS[name](d)
    fn.__name__ = name
    return status(AURA_RIM[kind], dk(color, 0.82))(fn)


for _n in ("aura_might", "aura_cinders", "aura_winter", "aura_fervor", "aura_mending", "aura_defiance", "aura_thorns", "aura_clarity"):
    _aura_status(_n)


@status(BUFF, "#1a1814")
def bone_ward(d):
    bone = dict(dark="#6a5a40", base="#d8ccae", light="#fbf6e6")
    d.glow(64, 64, 46, "#a8ffc8", 0.3)
    pts = [(64 + x * 1.1, 62 + y * 1.1) for x, y in heater_pts(64, 76)]
    sd = smooth(pts, tension=0.55)
    d.path(sd, stroke=OUTLINE, sw=6)
    d.path(sd, fill=d.lin([(0, "#3a3428"), (1, "#14100a")], 0, 20, 0, 110))
    # overlapping rib-bones across the shield face
    for i, y in enumerate((36, 50, 64, 78, 92)):
        w = 34 - abs(i - 1.5) * 5
        dd = f"M{64 - w},{y + 4} Q64,{y - 6} {64 + w},{y + 4}"
        d.path(dd, stroke=OUTLINE, sw=8)
        d.path(dd, stroke=bone["base"], sw=5)
        d.path(dd, stroke=bone["light"], sw=1.6, op=0.8)
    d.path("M64,26 L64,104", stroke=OUTLINE, sw=8)
    d.path("M64,26 L64,104", stroke=bone["light"], sw=4.4)
    for y in (32, 46, 60, 74, 88, 100):
        d.circle(64, y, 3.4, fill=bone["base"], stroke=OUTLINE, stroke_width=1.2)
    skull(d, 64, 26, 0.36, pal=bone, eye_glow="#7affb0")


@status(BUFF, "#2a0806")
def frenzy(d):
    # war drum with crossed beaters and burning red eyes above
    drum = dict(dark="#3a1a08", base="#8a4a1a", light="#d0905a")
    d.ellipse(64, 96, 34, 10, fill=d.lin([(0, drum["base"]), (1, drum["dark"])], 0, 86, 0, 106), stroke=OUTLINE, stroke_width=2.4)
    d.path("M30,76 L30,96 A34,10 0 0 0 98,96 L98,76 Z", fill=d.lin([(0, drum["light"]), (0.5, drum["base"]), (1, drum["dark"])], 30, 0, 98, 0), stroke=OUTLINE, stroke_width=2.4)
    for x in (38, 52, 64, 76, 90):
        d.path(f"M{x},{80} L{x + 6},{98}", stroke="#e8d8b0", sw=1.4, op=0.8)
    d.ellipse(64, 76, 34, 10, fill=d.rad([(0, "#f0dcb0"), (1, "#a08050")], 60, 74, 34), stroke=OUTLINE, stroke_width=2.4)
    for sx in (-1, 1):
        with d.g(T(64 + sx * 20, 70, sx * 35, 1.0)):
            d.path("M0,0 L0,-34", stroke=OUTLINE, sw=6)
            d.path("M0,0 L0,-34", stroke="#8a6a3a", sw=3)
            d.circle(0, -36, 5, fill=d.rad([(0, "#f0dcb0"), (1, "#8a6a3a")], -1, -37, 6), stroke=OUTLINE, stroke_width=1.6)
    for sx in (-1, 1):
        x = 64 + sx * 16
        d.glow(x, 30, 13, "#ff2a1a", 1.0)
        d.path(f"M{x - 9},{30 + sx * 0} L{x + 9},{28 - sx * 3} L{x + 5},{34} L{x - 6},{34} Z" if sx < 0 else f"M{x - 9},{28 + 3} L{x + 9},{30} L{x + 6},{34} L{x - 5},{34} Z",
               fill="#ffdc60", stroke=OUTLINE, stroke_width=1.6)
    for (x, y) in ((20, 60), (108, 60)):
        d.path(poly(star_pts(x, y, 4, 8, 2)), fill="#ff8a4a", op=0.9)


@status("#7ff3ff", "#081c24")
def rune_immune(d):
    d.glow(64, 64, 50, "#7ff3ff", 0.55)
    rune_ring(d, 64, 64, 42, "#b8f8ff", width=2.4, ticks=16, seed=17)
    d.path(poly(ngon(64, 64, 26, 6)), stroke=OUTLINE, sw=5)
    d.path(poly(ngon(64, 64, 26, 6)), fill=d.rad([(0, "#ffffff"), (0.4, "#7ff3ff"), (1, "#0a5a6e")], 60, 58, 30))
    rune_glyph(d, 64, 64, 1.3, "#ffffff", sw=3, kind=3)
