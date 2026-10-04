"""Class Transcendence icons (128x128): the 36 active skills (icons/skills/<id>.svg) and the 36 talents
(icons/talents/<id>.svg) of the twelve advanced classes. Built from the same toolkit, backdrops and bezels as the
bh-010 icons; each class's own colours tint its backdrop and its bezel's accent, so a page of one class reads as one
set and two classes never look alike.

Registered in build_all.py as categories "transcend" (TRANSCEND) and "transcend_talents" (TRANSCEND_TALENTS).
"""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, EL, STEEL, CRIMSON, GOLD, BRONZE, LEATHER, WOOD, BONE, OUTLINE, f, poly, smooth, mix, lt, dk,
                    ribbon, taper, arc_pts, qbez, star_pts, ngon, jag_line, polar, circle_path)
from bh_shapes import (T, sword, greatsword, dagger, heater_shield, tower_shield, cuirass, flame, snowflake, zig_bolt,
                       swirl, droplet, sun, void_orb, tendril, gem, rune_ring, motes, slash_arc, fist, banner, heart,
                       impact_star, eye, crystal, staff, bow)
from bh_frames import backdrop, vignette, skill_frame_accent, talent_frame, KNIGHT_METAL, MAGE_METAL, RANGER_METAL, SHADOW_METAL
from bh010_motifs import (BRIGHT_STEEL, DARK_STEEL, BLOOD, FOREST, FLETCH_GREEN, FLETCH_WHITE, arrow2, dagger2, trap_jaws,
                          bullseye, crosshair, leaf, boot, footprint, chalice, vial, fang, pips, hood_silhouette, rune_glyph,
                          web)

TRANSCEND = {}
TRANSCEND_TALENTS = {}

# class themes (DataTranscendence.CLASSES)
THEME = {
    "royal_guard": ("#527ED6", "#D8B46A", "knight"), "dark_general": ("#343444", "#C9566C", "knight"),
    "grand_paladin": ("#E8E0C6", "#E5BD64", "knight"), "tracker": ("#688C53", "#D5B86A", "ranger"),
    "wildwarden": ("#39876A", "#A3CF9C", "ranger"), "starstrider": ("#495DB7", "#A5DCEC", "ranger"),
    "arcanist": ("#946BD3", "#C7D0E6", "mage"), "archmage": ("#497EC9", "#E0E7F3", "mage"),
    "void_sovereign": ("#5446A6", "#B292EA", "mage"), "nightstalker": ("#8655A8", "#ADB3C6", "shadowblade"),
    "phantom_reaper": ("#7A77C9", "#BEDDEB", "shadowblade"), "blood_sovereign": ("#AD4B64", "#DF9C9C", "shadowblade"),
}
METAL = {"knight": KNIGHT_METAL, "ranger": RANGER_METAL, "mage": MAGE_METAL, "shadowblade": SHADOW_METAL}


def pal(c: str) -> dict:
    return dict(dark=dk(c, 0.55), base=c, light=lt(c, 0.6), glow=lt(c, 0.3))


def _inner(cls: str) -> str:
    prim = THEME[cls][0]
    return dk(prim, 0.78) if cls != "grand_paladin" else dk("#8a7a40", 0.7)


def skill(cls: str):
    prim, acc, fam = THEME[cls]

    def deco(fn):
        def build():
            d = Doc(name="tc_" + fn.__name__)
            backdrop(d, _inner(cls), haze=prim if cls != "dark_general" else acc, haze2=acc)
            fn(d, pal(prim), pal(acc))
            vignette(d, 0.6)
            skill_frame_accent(d, METAL[fam], pal(acc))
            return d
        TRANSCEND[fn.__name__] = build
        return fn
    return deco


def talent(cls: str, kind="minor"):
    prim, acc, fam = THEME[cls]

    def deco(fn):
        def build():
            d = Doc(name="tct_" + fn.__name__)
            backdrop(d, _inner(cls), haze=prim if cls != "dark_general" else acc, haze2=acc, cy=64)
            s = 0.8 if kind == "normal" else 0.7
            with d.g(f"translate(64 64) scale({f(s)}) translate(-64 -64)"):
                fn(d, pal(prim), pal(acc))
            vignette(d, 0.5, cy=64)
            talent_frame(d, METAL[fam], kind)
            return d
        TRANSCEND_TALENTS[fn.__name__] = build
        return fn
    return deco


def arrow_at(d, x0, y0, deg, L, s=1.0, **kw):
    with d.g(T(x0, y0, deg + 90, s)):
        arrow2(d, L=L, **kw)


def ring(d, cx, cy, r, color, w=3.0, op=0.9):
    d.circle(cx, cy, r, stroke=color, stroke_width=w, opacity=op)


DARKP = dict(dark="#10041a", base="#5a2a7e", light="#b684ea", glow="#8a3ad0")
LIGHTP = EL["light"]


# ======================================================================================== ROYAL GUARD
@skill("royal_guard")
def rg_bastion_rush(d, P, A):
    for i, x in enumerate((26, 40, 54)):
        d.path(f"M{x},96 L{x + 26},70", stroke=A["light"], sw=3 - i * 0.6, op=0.35 + i * 0.2)
    with d.g(T(74, 60, 18, 0.95)):
        heater_shield(d, w=58, h=68, field=P, rim=GOLD, emblem="cross")
    impact_star(d, 100, 48, 16, "#ffffff", A["glow"], n=8)


@skill("royal_guard")
def rg_sovereigns_challenge(d, P, A):
    d.glow(64, 64, 46, A["glow"], 0.4)
    for r, op in ((48, 0.35), (38, 0.6)):
        ring(d, 64, 64, r, A["light"], 3, op)
    d.shape(poly([(40, 50), (48, 34), (56, 46), (64, 28), (72, 46), (80, 34), (88, 50), (86, 62), (42, 62)]),
            fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], 0, 28, 0, 62), ow=2.2)
    with d.g(T(64, 104, 0, 0.7)):
        heater_shield(d, w=50, h=56, field=P, rim=GOLD, emblem="cross")


@skill("royal_guard")
def rg_bulwark_standard(d, P, A):
    d.glow_ellipse(64, 108, 44, 10, A["glow"], 0.7)
    ring(d, 64, 108, 40, A["light"], 2.4, 0.7)
    with d.g(T(64, 62, 0, 1.0)):
        banner(d, field=P, trim=GOLD)


@talent("royal_guard")
def rg_crown_discipline(d, P, A):
    with d.g(T(64, 70, 0, 1.0)):
        heater_shield(d, w=62, h=72, field=P, rim=GOLD, emblem="cross")
    d.shape(poly([(46, 30), (52, 18), (58, 28), (64, 14), (70, 28), (76, 18), (82, 30), (80, 38), (48, 38)]),
            fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], 0, 14, 0, 38), ow=2.0)


@talent("royal_guard")
def rg_unbroken_line(d, P, A):
    for i, x in enumerate((30, 64, 98)):
        with d.g(T(x, 70, 0, 0.62)):
            heater_shield(d, w=56, h=66, field=P if i == 1 else pal(dk(P["base"], 0.2)), rim=GOLD, emblem="cross")
    d.path("M14,108 L114,108", stroke=A["light"], sw=4, op=0.8)


@talent("royal_guard", "normal")
def rg_guardians_resolve(d, P, A):
    d.glow(64, 64, 44, A["glow"], 0.5)
    with d.g(T(64, 70, 0, 0.9)):
        heater_shield(d, w=60, h=70, field=P, rim=GOLD, emblem="cross")
    pips(d, [(40, 22), (52, 16), (64, 14), (76, 16), (88, 22)], lit=4, color=A, r=4.5)


# ======================================================================================== DARK GENERAL
@skill("dark_general")
def dg_dread_cleave(d, P, A):
    slash_arc(d, 64, 76, 46, math.radians(200), math.radians(340), 14, dict(dark="#2a0610", base=A["base"], light="#ffd0d8", glow=A["base"]))
    with d.g(T(64, 100, -30, 0.9)):
        greatsword(d, L=70, W=13, pal=dict(dark="#101018", base="#4a4a5c", light="#b0b0c8"), hilt=dict(dark="#3a0a14", base=A["base"], light="#ffc0c8"))


@skill("dark_general")
def dg_warbound_advance(d, P, A):
    for i in range(4):
        footprint(d, 24 + i * 16, 104 - i * 12, 0.9, a=-40, fill=A["dark"], op=0.35 + i * 0.15)
    with d.g(T(84, 56, 30, 0.85)):
        greatsword(d, L=66, W=13, pal=dict(dark="#101018", base="#4a4a5c", light="#b0b0c8"), hilt=dict(dark="#3a0a14", base=A["base"], light="#ffc0c8"))
    impact_star(d, 98, 30, 12, "#ffffff", A["glow"], n=6)


@skill("dark_general")
def dg_black_dominion(d, P, A):
    d.glow_ellipse(64, 92, 50, 18, A["base"], 0.5)
    void_orb(d, 64, 62, 26, dict(dark="#050208", base="#20162a", light=A["light"], glow=A["base"]))
    for a in range(0, 360, 45):
        p0 = polar(64, 62, 28, math.radians(a))
        p1 = polar(64, 62, 44, math.radians(a + 12))
        d.path(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}", stroke=A["base"], sw=3, op=0.8)


@talent("dark_general")
def dg_dreadsteel(d, P, A):
    with d.g(T(64, 104, 0, 0.95)):
        greatsword(d, L=78, W=15, pal=dict(dark="#101018", base="#4a4a5c", light="#b0b0c8"), hilt=dict(dark="#3a0a14", base=A["base"], light="#ffc0c8"))
    d.glow(64, 52, 20, A["glow"], 0.5)


@talent("dark_general")
def dg_relentless_march(d, P, A):
    for i in range(3):
        with d.g(T(34 + i * 30, 96 - i * 22, -20, 0.8)):
            footprint(d, 0, 0, 1.4, a=-20, fill=A["base"], op=0.5 + i * 0.25)
    d.path("M20,110 Q64,90 108,30", stroke=A["light"], sw=2.4, op=0.5)


@talent("dark_general", "normal")
def dg_iron_tyrant(d, P, A):
    with d.g(T(64, 66, 0, 0.9)):
        cuirass(d, w=64, h=66, pal=dict(dark="#101018", base="#40404e", light="#a0a0b8"), trim=dict(dark="#3a0a14", base=A["base"], light="#ffc0c8"))
    ring(d, 64, 66, 48, A["light"], 3, 0.6)


# ======================================================================================== GRAND PALADIN
@skill("grand_paladin")
def gp_dawn_verdict(d, P, A):
    sun(d, 64, 40, 16, pal=dict(dark="#9a6c20", base=A["base"], light="#fffff2", glow="#fff0b0"), rays=12)
    with d.g(T(64, 110, 0, 0.95)):
        sword(d, L=72, W=13, pal=BRIGHT_STEEL, hilt=GOLD, glow="#fff0b0")


@skill("grand_paladin")
def gp_sanctified_ground(d, P, A):
    d.glow_ellipse(64, 96, 50, 16, "#fff0b0", 0.8)
    rune_ring(d, 64, 96, 40, A["base"], width=2.4, ticks=20)
    for x in (40, 64, 88):
        d.path(f"M{x},96 L{x},40", stroke="#fffbe6", sw=4, op=0.55)
    d.shape(poly(star_pts(64, 52, 4, 18, 5)), fill="#fffbe6", ow=1.6)


@skill("grand_paladin")
def gp_oath_of_mercy(d, P, A):
    d.glow(64, 64, 46, "#fff0b0", 0.5)
    d.path(circle_path(64, 66, 40), fill="#fff4d0", op=0.18)
    ring(d, 64, 66, 40, A["base"], 3.2, 0.9)
    with d.g(T(64, 64, 0, 1.0)):
        heart(d, 0, 0, 1.0, dict(dark="#9a6c20", base=A["base"], light="#fffff2"))


@talent("grand_paladin")
def gp_radiant_steel(d, P, A):
    sun(d, 64, 60, 18, pal=dict(dark="#9a6c20", base=A["base"], light="#fffff2", glow="#fff0b0"), rays=10)
    with d.g(T(46, 104, 30, 0.8)):
        sword(d, L=60, W=11, pal=BRIGHT_STEEL, hilt=GOLD)


@talent("grand_paladin")
def gp_merciful_oath(d, P, A):
    with d.g(T(64, 70, 0, 0.9)):
        chalice(d, pal=GOLD, wine=dict(dark="#9a6c20", base="#fff0b0", light="#ffffff"))
    motes(d, [(40, 30, 1.0), (88, 28, 0.8), (64, 18, 1.2)], "#fffbe6", glow_color="#fff0b0")


@talent("grand_paladin")
def gp_hallowed_armor(d, P, A):
    with d.g(T(64, 66, 0, 0.9)):
        cuirass(d, w=64, h=66, pal=dict(dark="#7a6a40", base="#e8e0c6", light="#ffffff"), trim=GOLD)
    sun(d, 64, 56, 7, pal=dict(dark="#9a6c20", base=A["base"], light="#fffff2", glow="#fff0b0"), rays=8, ray_len=1.6)


# ======================================================================================== TRACKER
@skill("tracker")
def tr_quarry_mark(d, P, A):
    crosshair(d, 64, 64, 40, color=A["base"], sw=3.2)
    eye(d, 64, 64, 34, 18, iris=pal(P["base"]))


@skill("tracker")
def tr_snareline(d, P, A):
    for i in range(4):
        with d.g(T(24 + i * 27, 92 - i * 18, 0, 0.42)):
            trap_jaws(d, w=70, pal=BRONZE, open_=0.6)
    d.path("M14,104 L114,34", stroke=A["light"], sw=1.6, op=0.6)


@skill("tracker")
def tr_trail_volley(d, P, A):
    for a in (-30, -15, 0, 15, 30):
        arrow_at(d, 64, 112, -90 + a, 84, 0.9, fletch=FLETCH_GREEN)


@talent("tracker")
def tr_keen_trail(d, P, A):
    eye(d, 64, 56, 44, 22, iris=pal(A["base"]))
    for i in range(3):
        footprint(d, 40 + i * 22, 100 - (i % 2) * 6, 0.8, a=90, fill=P["base"], op=0.7)


@talent("tracker")
def tr_patient_aim(d, P, A):
    with d.g(T(46, 64, 0, 0.9)):
        bow(d, H=92)
    arrow_at(d, 46, 64, 0, 70, 0.95)
    d.glow(104, 64, 10, A["glow"], 0.6)


@talent("tracker")
def tr_fieldcraft(d, P, A):
    with d.g(T(64, 80, 0, 0.8)):
        trap_jaws(d, w=80, pal=BRONZE, open_=0.8)
    with d.g(T(64, 44, 0, 1.0)):
        leaf(d, L=26, W=11, pal=FOREST)


# ======================================================================================== WILDWARDEN
@skill("wildwarden")
def ww_briar_volley(d, P, A):
    d.glow_ellipse(64, 104, 44, 10, P["base"], 0.6)
    for a in (-20, 0, 20):
        arrow_at(d, 64, 110, -90 + a, 80, 0.85, fletch=FLETCH_GREEN)
    for x in (34, 64, 94):
        with d.g(T(x, 104, -30, 0.6)):
            leaf(d, L=22, W=9, pal=pal(P["base"]))


@skill("wildwarden")
def ww_living_thicket(d, P, A):
    rng = random.Random(4)
    for i in range(7):
        x = 22 + i * 14
        top = 40 + rng.random() * 24
        tendril(d, [(x, 112), (x + rng.uniform(-8, 8), (112 + top) / 2), (x + rng.uniform(-6, 6), top)], 5, pal=pal(P["base"]))
        with d.g(T(x, top, rng.uniform(-40, 40), 0.55)):
            leaf(d, L=20, W=9, pal=pal(A["base"]))


@skill("wildwarden")
def ww_wardens_refuge(d, P, A):
    d.path("M18,100 Q64,10 110,100 Z", fill=P["base"], op=0.35)
    d.path("M18,100 Q64,10 110,100", stroke=A["light"], sw=3, op=0.85)
    for x, y, a in ((30, 84, -50), (64, 46, 0), (98, 84, 50), (46, 62, -30), (82, 62, 30)):
        with d.g(T(x, y, a, 0.6)):
            leaf(d, L=20, W=9, pal=pal(A["base"]))


@talent("wildwarden")
def ww_thorncraft(d, P, A):
    tendril(d, [(20, 100), (54, 60), (108, 40)], 7, pal=pal(P["base"]))
    for t in (0.25, 0.5, 0.75):
        x, y = 20 + 88 * t, 100 - 60 * t
        d.shape(poly([(x - 4, y), (x + 2, y - 12), (x + 4, y)]), fill=A["base"], ow=1.4)


@talent("wildwarden", "normal")
def ww_rootbound_guard(d, P, A):
    with d.g(T(64, 60, 0, 0.8)):
        heater_shield(d, w=56, h=66, field=pal(P["base"]), rim=WOOD, emblem="cross")
    for x in (40, 64, 88):
        tendril(d, [(x, 90), (x + 6, 104), (x - 4, 118)], 4, pal=WOOD)


@talent("wildwarden")
def ww_verdant_reserve(d, P, A):
    with d.g(T(64, 68, 0, 1.0)):
        vial(d, liquid=dict(dark="#0a3a1a", base=A["base"], light="#ecffe8"))
    with d.g(T(84, 40, 30, 0.7)):
        leaf(d, L=22, W=9, pal=pal(P["base"]))


# ======================================================================================== STARSTRIDER
@skill("starstrider")
def ss_astral_pierce(d, P, A):
    d.path("M10,64 L118,64", stroke=A["light"], sw=8, op=0.25)
    arrow_at(d, 10, 64, 0, 108, 1.0, fletch=FLETCH_WHITE, glow=A["glow"])
    for x in (44, 80):
        d.shape(poly(star_pts(x, 64, 4, 10, 3)), fill="#ffffff", ow=1.2)


@skill("starstrider")
def ss_comet_step(d, P, A):
    d.path("M18,104 Q50,30 98,30", stroke=A["light"], sw=10, op=0.25)
    d.path("M18,104 Q50,30 98,30", stroke="#ffffff", sw=3, op=0.8)
    d.glow(98, 30, 14, A["glow"], 0.8)
    with d.g(T(40, 96, 0, 0.9)):
        boot(d, pal=pal(P["base"]), trim=dict(dark="#3a4a6a", base=A["base"], light="#ffffff"))


@skill("starstrider")
def ss_constellation_rain(d, P, A):
    pts = [(28, 30), (52, 22), (74, 34), (98, 24), (86, 48)]
    for a, b in zip(pts, pts[1:]):
        d.path(f"M{a[0]},{a[1]} L{b[0]},{b[1]}", stroke=A["light"], sw=1.4, op=0.7)
    for x, y in pts:
        d.shape(poly(star_pts(x, y, 4, 6, 2)), fill="#ffffff", ow=1)
    for x in (36, 60, 84):
        arrow_at(d, x, 50, 100, 54, 0.8, fletch=FLETCH_WHITE, glow=A["glow"])


@talent("starstrider")
def ss_celestial_sight(d, P, A):
    eye(d, 64, 64, 50, 24, iris=pal(A["base"]))
    for x, y in ((24, 26), (104, 30), (100, 100), (28, 102)):
        d.shape(poly(star_pts(x, y, 4, 7, 2)), fill="#ffffff", ow=1)


@talent("starstrider", "normal")
def ss_comet_rhythm(d, P, A):
    swirl(d, 64, 64, 8, 42, 0, 1.4, 6, A["light"], op=0.85)
    d.glow(90, 34, 10, "#ffffff", 0.8)


@talent("starstrider")
def ss_steady_constellation(d, P, A):
    for i, (x, y) in enumerate(((30, 90), (48, 62), (64, 40), (82, 62), (98, 90))):
        d.shape(poly(star_pts(x, y, 5, 9, 3.5)), fill="#ffffff" if i == 2 else A["light"], ow=1.2)
    d.path("M30,90 L48,62 L64,40 L82,62 L98,90", stroke=A["base"], sw=1.6, op=0.7)


# ======================================================================================== ARCANIST
@skill("arcanist")
def ar_aether_lance(d, P, A):
    pts = [(14, 104), (114, 24)]
    d.path(ribbon(pts, [4, 18]), fill=P["base"], op=0.35)
    d.path(ribbon(pts, [2, 8]), fill=A["light"], op=0.9)
    crystal(d, 104, 32, 9, pal(P["base"]))


@skill("arcanist")
def ar_runic_circle(d, P, A):
    rune_ring(d, 64, 64, 44, A["light"], width=2.6, ticks=24)
    rune_ring(d, 64, 64, 28, P["light"], width=2.0, ticks=12, seed=7)
    for k in range(3):
        a = math.radians(-90 + k * 120)
        x, y = polar(64, 64, 36, a)
        rune_glyph(d, x, y, 7, A["light"], kind=k)


@skill("arcanist")
def ar_mana_ward(d, P, A):
    d.path(circle_path(64, 66, 42), fill="#6a8aff", op=0.22)
    ring(d, 64, 66, 42, "#a0c0ff", 3.4, 0.9)
    droplet(d, 64, 66, 18, dict(dark="#10206a", base="#4a7aff", light="#e0ecff"))


@talent("arcanist")
def ar_runic_efficiency(d, P, A):
    droplet(d, 64, 70, 22, dict(dark="#10206a", base="#4a7aff", light="#e0ecff"))
    rune_glyph(d, 64, 30, 10, A["light"], kind=1)


@talent("arcanist")
def ar_charge_discipline(d, P, A):
    pips(d, [(30, 64), (47, 64), (64, 64), (81, 64), (98, 64)], lit=5, color=pal(P["base"]), r=7)
    d.path("M24,84 L104,84", stroke=A["light"], sw=2.4, op=0.7)


@talent("arcanist")
def ar_aether_precision(d, P, A):
    crosshair(d, 64, 64, 38, color=A["light"], sw=2.6)
    crystal(d, 64, 64, 10, pal(P["base"]))


# ======================================================================================== ARCHMAGE
@skill("archmage")
def am_prismatic_tempest(d, P, A):
    swirl(d, 64, 64, 6, 46, 0.0, 1.6, 9, "#ff8a40", op=0.8)
    swirl(d, 64, 64, 6, 46, 2.1, 1.6, 9, "#40a0ff", op=0.8)
    swirl(d, 64, 64, 6, 46, 4.2, 1.6, 9, "#ffe23a", op=0.8)
    d.glow(64, 64, 10, "#ffffff", 0.9)


@skill("archmage")
def am_grand_convergence(d, P, A):
    for (x, y, c) in ((22, 26, "#ff8a40"), (106, 26, "#7fd6ec"), (64, 112, "#ffe23a")):
        d.path(f"M{x},{y} L64,64", stroke=c, sw=6, op=0.75)
    impact_star(d, 64, 64, 26, "#ffffff", A["glow"], n=10)
    with d.g(T(22, 26, 0, 0.5)):
        flame(d, 0, 0, 1.0, EL["fire"], glow=False)
    snowflake(d, 106, 26, 10, EL["ice"])
    zig_bolt(d, 64, 108, 22, EL["lightning"])


@skill("archmage")
def am_spellweave(d, P, A):
    for k in range(3):
        swirl(d, 64, 64, 14 + k * 9, 20 + k * 9, k * 1.4, 0.9, 3.4, A["light"] if k != 1 else P["light"], op=0.85)
    crystal(d, 64, 64, 9, pal(P["base"]))


@talent("archmage")
def am_elemental_concord(d, P, A):
    with d.g(T(40, 80, 0, 0.6)):
        flame(d, 0, 0, 1.0, EL["fire"], glow=False)
    droplet(d, 88, 80, 13, EL["water"])
    zig_bolt(d, 64, 44, 26, EL["lightning"])
    ring(d, 64, 66, 46, A["light"], 2.4, 0.6)


@talent("archmage")
def am_master_channeling(d, P, A):
    with d.g(T(64, 34, 20, 0.9)):
        staff(d, H=92, pal=pal(P["base"]))
    swirl(d, 64, 40, 8, 26, 0.5, 1.0, 3, A["light"], op=0.8)


@talent("archmage", "normal")
def am_prismatic_shelter(d, P, A):
    d.path("M24,96 Q64,16 104,96 Z", fill=P["base"], op=0.25)
    for i, c in enumerate(("#ff8a40", "#40a0ff", "#ffe23a")):
        d.path(f"M{24 + i * 4},96 Q64,{16 + i * 10} {104 - i * 4},96", stroke=c, sw=3, op=0.85)


# ======================================================================================== VOID SOVEREIGN
@skill("void_sovereign")
def vs_event_horizon(d, P, A):
    swirl(d, 64, 64, 6, 50, 0.0, 2.2, 7, A["base"], op=0.7, cw=False)
    swirl(d, 64, 64, 6, 50, 3.1, 2.2, 7, P["light"], op=0.6, cw=False)
    void_orb(d, 64, 64, 14, DARKP)


@skill("void_sovereign")
def vs_null_lance(d, P, A):
    pts = [(14, 108), (114, 20)]
    d.path(ribbon(pts, [5, 20]), fill=dk(P["base"], 0.4), op=0.5)
    d.path(ribbon(pts, [2, 8]), fill=A["light"], op=0.9)
    d.glow(110, 24, 10, A["glow"], 0.7)
    ring(d, 64, 64, 12, A["light"], 2.0, 0.8)


@skill("void_sovereign")
def vs_rift_collapse(d, P, A):
    d.path(circle_path(64, 70, 44), fill=A["base"], op=0.12)
    ring(d, 64, 70, 44, A["light"], 2.4, 0.8)
    rng = random.Random(9)
    crack = jag_line((40, 40), (88, 100), 6, 8, rng)
    d.path(poly(crack, closed=False), stroke="#ffffff", sw=4, op=0.9)
    d.path(poly(crack, closed=False), stroke=A["base"], sw=9, op=0.3)
    void_orb(d, 64, 70, 10, DARKP)


@talent("void_sovereign")
def vs_void_geometry(d, P, A):
    d.shape(poly(ngon(64, 64, 42, 6)), fill=P["base"], ow=2, op=0.35)
    d.shape(poly(ngon(64, 64, 26, 6, rot0=0)), fill=dk(P["base"], 0.3), ow=2, op=0.6)
    void_orb(d, 64, 64, 10, DARKP)


@talent("void_sovereign")
def vs_entropy(d, P, A):
    void_orb(d, 64, 60, 22, DARKP)
    for a in (200, 250, 290, 340):
        p0 = polar(64, 60, 24, math.radians(a))
        p1 = polar(64, 60, 44, math.radians(a + 20))
        d.path(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}", stroke=A["light"], sw=2.4, op=0.7)


@talent("void_sovereign")
def vs_sovereigns_reserve(d, P, A):
    droplet(d, 64, 70, 24, dict(dark="#10063a", base=P["base"], light=A["light"]))
    d.shape(poly([(46, 32), (52, 20), (58, 30), (64, 16), (70, 30), (76, 20), (82, 32)]), fill=A["base"], ow=1.8)


# ======================================================================================== NIGHTSTALKER
@skill("nightstalker")
def ns_umbral_lunge(d, P, A):
    for i in range(4):
        d.path(f"M{14 + i * 8},{100 - i * 2} L{64 + i * 6},{62 - i * 4}", stroke=P["light"], sw=2, op=0.2 + i * 0.15)
    with d.g(T(88, 46, 45, 1.0)):
        dagger2(d, L=50, W=10, gem=pal(A["base"]))


@skill("nightstalker")
def ns_gloom_veil(d, P, A):
    with d.g(T(64, 112, 0, 1.0)):
        hood_silhouette(d, fill=dk(P["base"], 0.5), op=0.85)
    for x, y, r in ((30, 70, 18), (98, 66, 20), (64, 92, 22)):
        d.path(circle_path(x, y, r), fill=A["dark"], op=0.45)


@skill("nightstalker")
def ns_marked_execution(d, P, A):
    crosshair(d, 64, 60, 36, color=P["light"], sw=2.4)
    with d.g(T(64, 108, 0, 1.0)):
        dagger2(d, L=60, W=11, gem=pal(A["base"]))


@talent("nightstalker")
def ns_ambush_training(d, P, A):
    with d.g(T(64, 110, 0, 0.9)):
        hood_silhouette(d, fill=dk(P["base"], 0.5))
    eye(d, 64, 54, 26, 10, iris=pal(A["base"]))


@talent("nightstalker")
def ns_silent_footwork(d, P, A):
    for i in range(4):
        footprint(d, 30 + i * 22, 92 - i * 16, 1.0, a=-35, fill=P["light"], op=0.25 + i * 0.2)


@talent("nightstalker")
def ns_patient_blade(d, P, A):
    with d.g(T(46, 104, 30, 0.8)):
        dagger2(d, L=50, W=10, gem=pal(A["base"]))
    pips(d, [(74, 34), (86, 46), (98, 58), (104, 74), (104, 90)], lit=5, color=pal(P["base"]), r=5)


# ======================================================================================== PHANTOM REAPER
@skill("phantom_reaper")
def pr_phantom_crossing(d, P, A):
    with d.g(T(34, 108, 0, 0.8)):
        hood_silhouette(d, fill=A["base"], op=0.35, outline=False)
    with d.g(T(94, 108, 0, 0.8)):
        hood_silhouette(d, fill=dk(P["base"], 0.4))
    d.path("M40,64 Q64,40 88,64", stroke=A["light"], sw=3, op=0.8)


@skill("phantom_reaper")
def pr_reapers_arc(d, P, A):
    slash_arc(d, 64, 72, 46, math.radians(190), math.radians(350), 13, dict(dark="#202040", base=P["base"], light=A["light"], glow=A["base"]))
    with d.g(T(64, 104, 0, 0.9)):
        dagger2(d, L=50, W=10, gem=pal(A["base"]))


@skill("phantom_reaper")
def pr_afterimage_flurry(d, P, A):
    for i, op in enumerate((0.25, 0.45, 0.7, 1.0)):
        with d.g(T(30 + i * 22, 100, 35, 0.7), op=op):
            dagger2(d, L=48, W=10, gem=pal(A["base"]))


@talent("phantom_reaper")
def pr_ghoststep(d, P, A):
    for i in range(3):
        footprint(d, 40 + i * 24, 90 - i * 18, 1.1, a=-35, fill=A["light"], op=0.25 + i * 0.25)


@talent("phantom_reaper")
def pr_reaping_edge(d, P, A):
    slash_arc(d, 64, 76, 40, math.radians(200), math.radians(340), 11, dict(dark="#202040", base=P["base"], light=A["light"], glow=A["base"]))
    pips(d, [(40, 96), (52, 100), (64, 102), (76, 100), (88, 96)], lit=5, color=pal(A["base"]), r=4)


@talent("phantom_reaper", "normal")
def pr_untouchable_rhythm(d, P, A):
    with d.g(T(64, 110, 0, 0.9)):
        hood_silhouette(d, fill=dk(P["base"], 0.4))
    for r in (44, 34):
        ring(d, 64, 64, r, A["light"], 2.2, 0.6)


# ======================================================================================== BLOOD SOVEREIGN
@skill("blood_sovereign")
def bs_crimson_rend(d, P, A):
    for i in range(3):
        d.path(f"M{30 + i * 14},28 L{74 + i * 14},100", stroke=P["base"], sw=7, op=0.85)
        d.path(f"M{30 + i * 14},28 L{74 + i * 14},100", stroke=A["light"], sw=2, op=0.9)
    for x, y in ((44, 108), (70, 112), (96, 104)):
        droplet(d, x, y, 6, BLOOD)


@skill("blood_sovereign")
def bs_sanguine_pact(d, P, A):
    with d.g(T(64, 74, 0, 0.9)):
        chalice(d, pal=dict(dark="#3a0a14", base=P["base"], light=A["light"]), wine=BLOOD)
    heart(d, 64, 30, 0.6, BLOOD)


@skill("blood_sovereign")
def bs_blood_eclipse(d, P, A):
    d.glow(64, 64, 48, P["base"], 0.6)
    d.path(circle_path(64, 64, 34), fill="#2a0610")
    d.path(circle_path(74, 58, 30), fill=dk(P["base"], 0.75))
    ring(d, 64, 64, 34, A["light"], 2.6, 0.9)
    for a in range(0, 360, 60):
        x, y = polar(64, 64, 46, math.radians(a))
        droplet(d, x, y, 5, BLOOD)


@talent("blood_sovereign")
def bs_hemomancy(d, P, A):
    droplet(d, 64, 68, 26, BLOOD)
    swirl(d, 64, 68, 6, 18, 0.0, 1.0, 2.4, A["light"], op=0.8)


@talent("blood_sovereign")
def bs_sovereigns_hunger(d, P, A):
    with d.g(T(64, 60, 0, 1.0)):
        fang(d, L=30, W=12)
    droplet(d, 64, 100, 9, BLOOD)


@talent("blood_sovereign")
def bs_crimson_endurance(d, P, A):
    heart(d, 64, 66, 1.1, dict(dark="#3a0a14", base=P["base"], light=A["light"]))
    d.path("M30,66 L50,66 L56,52 L64,82 L72,60 L78,66 L98,66", stroke="#ffffff", sw=2.6, op=0.85)
