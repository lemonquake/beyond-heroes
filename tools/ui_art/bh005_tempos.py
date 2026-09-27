"""bh-005 UI art: Tempo grades, the Mystic and Warden classes, the renowned spirits and Tobren (docs/LORE.md §9).

Writes (same painted style and helpers as bh004_tempos.py):
  game/assets/ui/icons/skills/tempo_<skill>.svg      20 new Tempo skill icons, 128x128, spectral bezel
  game/assets/ui/icons/classes/tempo_<class>.svg     mystic / warden crests, 128x128
  game/assets/ui/portraits/tempo_<who>.svg            Tobren + the five renowned spirits, 256x256

Usage:  python tools/ui_art/bh005_tempos.py
"""
from __future__ import annotations

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
UI = os.path.join(ROOT, "game", "assets", "ui")

from bh_svg import (Doc, OUTLINE, GOLD, STEEL, BONE, WOOD, EL, f, poly, smooth, mix, lt, dk, ribbon, taper, polar)  # noqa: E402
from bh_shapes import (T, sword, dagger, bow, arrow, heater_shield, tower_shield, staff, slash_arc, impact_star, swirl, heart,  # noqa: E402
                       void_orb, rune_ring, motes, skull, flame, snowflake, zig_bolt, bolt, rock, sun, ice_shard, eye)
from bh_frames import backdrop, vignette, skill_frame, medallion_bg, medallion_rim  # noqa: E402
import portraits as P  # noqa: E402

SPIRIT = dict(dark="#0e3a44", base="#62c8d8", light="#e4fcff", glow="#8ef4ff")
SPIRIT_METAL = dict(dark="#123a42", base="#5aaab8", light="#dcfaff")
GHOST_STEEL = dict(dark="#2a4a58", base="#a8dce8", light="#ffffff", glow="#c8f8ff")
HEAL = dict(dark="#0e4a2c", base="#46c888", light="#d8ffe8", glow="#9affc8")
SHADOW = dict(dark="#10081c", base="#4a2a70", light="#b89ae8", glow="#a070ff")
RENOWN = dict(dark="#5a3a10", base="#e0a040", light="#fff0c0", glow="#ffc860")
GHOST_WOOD = dict(dark="#1a3a48", base="#5aaab8", light="#dcfaff")

SKILLS = {}
CLASSES = {}
PORTRAITS = {}


def skill(inner, haze=None, haze2=None, renowned=False):
    def deco(fn):
        def build():
            d = Doc(name="tempo_" + fn.__name__)
            backdrop(d, inner, haze=haze, haze2=haze2)
            fn(d)
            d.circle(64, 120, 60, fill=d.rad([(0, SPIRIT["glow"], 0.18), (1, SPIRIT["glow"], 0)], 64, 120, 60))
            vignette(d, 0.7)
            # the renowned spirits' own skills wear a gold bezel
            skill_frame(d, dict(dark="#4a3010", base="#c89a48", light="#fff0c8") if renowned else SPIRIT_METAL)
            return d
        SKILLS[fn.__name__] = build
        return fn
    return deco


def m2(d, pts, color, glow_color=None, size=2.0):
    motes(d, [(x, y, 1.0) for x, y in pts], color, glow_color, size=size)


def trail(d, pts, w, col=SPIRIT["glow"], op=0.5):
    d.path(ribbon(pts, taper(len(pts), w, 0.0, 1.0, peak=0.8)), fill=col, op=op)


# ------------------------------------------------------------------------------------------ swordsman


@skill("#0c2a34", haze="#2a8aa0", haze2="#1a4a70")
def sw_whirl(d):
    for r, op in ((46, 0.35), (36, 0.55), (26, 0.8)):
        swirl(d, 64, 66, r - 8, r, 0.3, 0.8, 5, SPIRIT["glow"], op=op, outline=False)
    slash_arc(d, 64, 66, 44, math.radians(200), math.radians(520), 10, dict(dark="#0e3a44", base="#dffaff", light="#ffffff", glow=SPIRIT["glow"]))
    with d.g(T(64, 66, 60, 0.9)):
        sword(d, L=56, W=11, pal=GHOST_STEEL, hilt=SPIRIT_METAL)


@skill("#2a1a0c", haze="#e0a040", haze2="#8ef4ff")
def sw_rally(d):
    for r, op in ((50, 0.3), (40, 0.5)):
        d.circle(64, 70, r, stroke=RENOWN["glow"], stroke_width=3, opacity=op)
    for ang in (-28, 28):
        with d.g(T(64, 88, ang, 0.85)):
            sword(d, L=64, W=11, pal=GHOST_STEEL, hilt=dict(dark="#5a3a10", base="#e0a040", light="#fff0c0"))
    impact_star(d, 64, 34, 18, "#ffffff", RENOWN["glow"], n=8)


# ------------------------------------------------------------------------------------------ archer


@skill("#0a2030", haze="#6ac8f0", haze2="#1a4a70")
def ar_frost(d):
    trail(d, [(10, 104), (70, 52)], 10, col=EL["ice"]["glow"], op=0.45)
    with d.g(T(24, 98, 45, 1.05)):
        arrow(d, L=80, pal=dict(dark="#1f5a7a", base="#bff0ff", light="#ffffff"), fletch=EL["ice"])
    snowflake(d, 94, 38, 18, EL["ice"], width=3.4)


@skill("#0e2418", haze="#3a9a5a", haze2="#8ef4ff")
def ar_trap(d):
    d.ellipse(64, 92, 46, 14, fill=HEAL["glow"], opacity=0.14)
    d.ellipse(64, 92, 46, 14, stroke=HEAL["glow"], stroke_width=2.4, opacity=0.8)
    rng = random.Random(11)
    for i in range(9):
        x = 22 + i * 10.5
        h = rng.uniform(22, 44)
        pts = [(x - 4, 94), (x + rng.uniform(-6, 6), 94 - h * 0.5), (x + rng.uniform(-3, 3), 94 - h)]
        d.path(ribbon(pts, taper(3, 6, 1.0, 0.0, peak=0.0)), fill=dk(HEAL["base"], 0.2), stroke=OUTLINE, stroke_width=1.4)
    m2(d, [(30, 40), (98, 34), (64, 26)], HEAL["light"], HEAL["glow"], size=2.2)


# ------------------------------------------------------------------------------------------ thief


@skill("#140c22", haze="#6a3ab0", haze2="#8ef4ff")
def th_fan(d):
    for i in range(8):
        a = i * 45 + 22
        p = polar(64, 64, 36, math.radians(a))
        trail(d, [polar(64, 64, 12, math.radians(a)), p], 5, col=SHADOW["glow"], op=0.35)
        with d.g(T(p[0], p[1], a + 90, 0.62)):
            dagger(d, L=36, W=9, pal=GHOST_STEEL, hilt=SPIRIT_METAL)
    d.circle(64, 64, 9, fill=SHADOW["glow"], opacity=0.6)


@skill("#1a0810", haze="#a02040", haze2="#6a3ab0")
def th_finish(d):
    slash_arc(d, 60, 70, 40, math.radians(210), math.radians(330), 14, dict(dark="#3a0810", base="#ffd0d8", light="#ffffff", glow="#ff4060"))
    with d.g(T(70, 72, 35, 1.3)):
        dagger(d, L=44, W=11, pal=GHOST_STEEL, hilt=SPIRIT_METAL)
    skull(d, 42, 44, 0.42, pal=dict(dark="#2a5a68", base="#c8f0f8", light="#ffffff", glow="#8ef4ff"), eye_glow="#ff4060")


# ------------------------------------------------------------------------------------------ mystic


@skill("#14143a", haze="#8a8aff", haze2="#ffe8a0")
def my_bolt(d):
    trail(d, [(14, 100), (74, 50)], 16, col=EL["light"]["glow"], op=0.4)
    sun(d, 82, 44, 13, EL["light"], rays=10)
    m2(d, [(30, 86), (48, 70), (22, 60)], EL["light"]["light"], EL["light"]["glow"], size=2.0)


@skill("#0e2230", haze="#62c8d8", haze2="#b8a0ff")
def my_ward(d):
    d.circle(64, 66, 44, fill=d.rad([(0, SPIRIT["glow"], 0.05), (0.8, SPIRIT["glow"], 0.25), (1, SPIRIT["glow"], 0.6)], 64, 66, 44))
    rune_ring(d, 64, 66, 44, SPIRIT["light"], width=2.4, ticks=18, op=0.9)
    with d.g(T(64, 70, 0, 0.62)):
        heater_shield(d, w=60, h=70, field=dict(dark="#0e3a44", base="#2a7a8a", light="#8ef4ff"), rim=GHOST_STEEL, emblem="cross", boss=SPIRIT_METAL)


@skill("#140e30", haze="#b88aff", haze2="#ffe23a")
def my_chain(d):
    pts = [(18, 40), (44, 58), (62, 40), (86, 70), (108, 52)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        mx, my = (x0 + x1) / 2 + 4, (y0 + y1) / 2 - 8
        bolt(d, [(x0, y0), (mx, my), (x1, y1)], width=5, pal=EL["lightning"])
    for x, y in pts[1:]:
        impact_star(d, x, y, 9, "#ffffff", EL["lightning"]["glow"], n=6)


@skill("#0a1c30", haze="#9eeeff", haze2="#62c8d8")
def my_nova(d):
    d.circle(64, 66, 48, fill=d.rad([(0, EL["ice"]["glow"], 0.1), (0.85, EL["ice"]["glow"], 0.3), (1, EL["ice"]["glow"], 0)], 64, 66, 48))
    for i in range(8):
        a = i * 45
        with d.g(T(*polar(64, 66, 22, math.radians(a - 90)), a, 0.9)):
            ice_shard(d, L=26, W=10, pal=EL["ice"])
    snowflake(d, 64, 66, 16, EL["ice"], width=3.0)


# ------------------------------------------------------------------------------------------ warden


@skill("#261a0c", haze="#d89a48", haze2="#8ef4ff")
def wd_bash(d):
    impact_star(d, 92, 58, 28, "#ffffff", RENOWN["glow"], n=9, inner=0.3)
    for y in (46, 62, 78):
        trail(d, [(10, y + 4), (54, y)], 7, op=0.4)
    with d.g(T(62, 64, -12, 0.95)):
        tower_shield(d, w=50, h=74, face=GHOST_STEEL, band=SPIRIT_METAL)


@skill("#1a1a2a", haze="#e0c080", haze2="#8ef4ff")
def wd_oath(d):
    for r, op in ((50, 0.3), (40, 0.5), (30, 0.75)):
        d.circle(64, 66, r, stroke=RENOWN["glow"], stroke_width=3, opacity=op)
    with d.g(T(64, 70, 0, 0.9)):
        tower_shield(d, w=48, h=72, face=GHOST_STEEL, band=dict(dark="#5a3a10", base="#e0a040", light="#fff0c0"))


@skill("#0c2430", haze="#8ef4ff", haze2="#e0c080")
def wd_aegis(d):
    d.path("M64,14 A52,52 0 0 1 116,66", stroke=SPIRIT["glow"], sw=6, op=0.5)
    d.path("M12,66 A52,52 0 0 1 64,14", stroke=SPIRIT["glow"], sw=6, op=0.5)
    d.circle(64, 66, 50, fill=d.rad([(0, SPIRIT["glow"], 0.0), (0.8, SPIRIT["glow"], 0.18), (1, SPIRIT["glow"], 0.45)], 64, 66, 50))
    with d.g(T(64, 68, 0, 0.85)):
        heater_shield(d, w=60, h=70, field=dict(dark="#3a2a10", base="#8a6a2a", light="#e0c080"), rim=GHOST_STEEL, emblem="cross", boss=SPIRIT_METAL)
    heart(d, 64, 64, 0.35, HEAL)


@skill("#2a1a0a", haze="#d89a48", haze2="#6a4a20")
def wd_quake(d):
    for i, (x, y, r) in enumerate(((28, 96, 11), (50, 104, 9), (78, 102, 10), (100, 94, 12), (64, 90, 8))):
        rock(d, x, y, r, EL["earth"], seed=i + 3)
    for sx in (-1, 1):
        d.path(poly([(64, 84), (64 + sx * 18, 70), (64 + sx * 34, 76), (64 + sx * 52, 64)], closed=False), stroke=OUTLINE, sw=5)
        d.path(poly([(64, 84), (64 + sx * 18, 70), (64 + sx * 34, 76), (64 + sx * 52, 64)], closed=False), stroke=EL["earth"]["glow"], sw=2.4)
    with d.g(T(64, 44, 180, 0.72)):
        sword(d, L=56, W=12, pal=GHOST_STEEL, hilt=SPIRIT_METAL)


# ------------------------------------------------------------------------------------------ the renowned


@skill("#1e160a", haze="#e0a040", haze2="#8ef4ff", renowned=True)
def lg_bastion(d):
    d.circle(64, 66, 50, fill=d.rad([(0, RENOWN["glow"], 0.0), (0.75, RENOWN["glow"], 0.2), (1, RENOWN["glow"], 0.5)], 64, 66, 50))
    for x, s in ((36, 0.55), (92, 0.55)):
        with d.g(T(x, 74, 0, s)):
            heater_shield(d, w=60, h=70, field=dict(dark="#0e3a44", base="#2a7a8a", light="#8ef4ff"), rim=GHOST_STEEL, emblem="cross", boss=SPIRIT_METAL)
    with d.g(T(64, 70, 0, 0.9)):
        tower_shield(d, w=50, h=76, face=GHOST_STEEL, band=dict(dark="#5a3a10", base="#e0a040", light="#fff0c0"))


@skill("#140e30", haze="#b88aff", haze2="#ffe23a", renowned=True)
def lg_stormbreak(d):
    zig_bolt(d, 88, 44, 62, EL["lightning"], lean=0.1)
    with d.g(T(50, 78, 40, 1.0)):
        sword(d, L=62, W=12, pal=dict(dark="#4a2a9a", base="#fff6c0", light="#ffffff", glow="#b88aff"), hilt=SPIRIT_METAL)
    for x, y in ((24, 40), (104, 96), (30, 104)):
        impact_star(d, x, y, 8, "#ffffff", EL["lightning"]["glow"], n=6)


@skill("#2a2410", haze="#ffe08a", haze2="#9affc8", renowned=True)
def lg_sanctuary(d):
    d.circle(64, 64, 52, fill=d.rad([(0, "#fff0b0", 0.55), (1, "#fff0b0", 0)], 64, 64, 52))
    # a lantern: cap, glass, flame, handle
    d.path("M50,34 Q64,14 78,34", stroke=OUTLINE, sw=5)
    d.path("M50,34 Q64,14 78,34", stroke=GOLD["base"], sw=2.4)
    d.shape(poly([(46, 38), (82, 38), (78, 46), (50, 46)]), fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], 46, 38, 82, 46), ow=2)
    d.shape(poly([(50, 46), (78, 46), (82, 90), (46, 90)]), fill="#fff6d0", ow=2.4)
    flame(d, 64, 84, 0.52, EL["light"], glow=True)
    d.shape(poly([(44, 90), (84, 90), (80, 98), (48, 98)]), fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], 44, 90, 84, 98), ow=2)
    heart(d, 100, 30, 0.38, HEAL)
    m2(d, [(24, 50), (104, 70), (30, 96)], HEAL["light"], HEAL["glow"], size=2.2)


@skill("#fff0b0", haze="#ffe08a", haze2="#ffffff", renowned=True)
def lg_dawn(d):
    d.rect(0, 0, 128, 128, fill=d.rad([(0, "#fffbe0", 0.0), (1, "#3a2a10", 0.55)], 64, 64, 90))
    sun(d, 64, 64, 18, EL["light"], rays=14, ray_len=2.4)
    rune_ring(d, 64, 64, 50, "#fff6d0", width=2.2, ticks=20, op=0.8)


@skill("#2a0e06", haze="#ff6a14", haze2="#ffd34a", renowned=True)
def lg_cinderfall(d):
    rng = random.Random(5)
    for i, x in enumerate((24, 42, 60, 78, 96, 110)):
        y = 30 + rng.uniform(-6, 18)
        trail(d, [(x - 8, y - 28), (x, y)], 6, col=EL["fire"]["glow"], op=0.5)
        with d.g(T(x, y + 40, 168 + rng.uniform(-5, 5), 0.56)):
            arrow(d, L=70, pal=dict(dark="#7a1206", base="#ffb070", light="#fff0c0"), fletch=EL["fire"])
    for x in (36, 64, 92):
        flame(d, x, 112, 0.4, EL["fire"])


@skill("#0c0616", haze="#8a3ad0", haze2="#ff4060", renowned=True)
def lg_nightfall(d):
    void_orb(d, 64, 58, 30, EL["dark"])
    for ang in (-40, 40):
        with d.g(T(64, 92, ang, 1.2)):
            dagger(d, L=44, W=10, pal=dict(dark="#10041a", base="#c8a8f0", light="#ffffff"), hilt=SPIRIT_METAL)
    eye(d, 64, 56, 14, 6, dict(dark="#5a0a1a", base="#ff4060", light="#ffc0c8"))


# ------------------------------------------------------------------------------------------ class crests


def crest(fn):
    def build():
        d = Doc(name="tempo_" + fn.__name__)
        medallion_bg(d, "#0e2c36")
        d.circle(64, 64, 50, fill=d.rad([(0, SPIRIT["glow"], 0.22), (1, SPIRIT["glow"], 0)], 64, 70, 50))
        fn(d)
        medallion_rim(d, SPIRIT_METAL)
        return d
    CLASSES["tempo_" + fn.__name__] = build
    return fn


@crest
def mystic(d):
    rune_ring(d, 64, 64, 40, SPIRIT["light"], width=2.0, ticks=16, op=0.7)
    with d.g(T(64, 36, 0, 1.0)):
        staff(d, H=74, pal=dict(dark="#2a2a7a", base="#9a9aff", light="#ffffff", glow="#b8b8ff"), wood=GHOST_WOOD, thick=8.0, crystal_r=11.0)
    motes(d, [(38, 44, 1.0), (92, 50, 1.0), (40, 84, 0.8), (90, 88, 0.8)], "#ffffff", "#b8b8ff", size=2.4)


@crest
def warden(d):
    with d.g(T(64, 66, 45, 1.0)):
        sword(d, L=72, W=11, pal=GHOST_STEEL, hilt=SPIRIT_METAL)
    with d.g(T(58, 70, 0, 0.72)):
        tower_shield(d, w=54, h=78, face=dict(dark="#0e3a44", base="#2a7a8a", light="#8ef4ff"), band=GHOST_STEEL)


# ------------------------------------------------------------------------------------------ portraits (256)

GHOST = dict(light="#eafcff", base="#a6d8e2", dark="#4e8c9c", shade="#173c4a")


def ghost_skin(tint, k=0.3):
    """The pale, cold skin of a spirit, warmed or cooled toward `tint`."""
    return {key: mix(v, tint, k if key != "shade" else k * 0.5) for key, v in GHOST.items()}


def spectral(d, glow, seed=1, wisps=True):
    """Cold light from below, drifting motes and a wisp or two: every Tempo portrait shares it."""
    d.circle(128, 262, 96, fill=d.rad([(0, glow, 0.35), (1, glow, 0)], 128, 262, 96))
    rng = random.Random(seed)
    if wisps:
        for sx in (-1, 1):
            x0 = 128 + sx * rng.uniform(78, 96)
            pts = [(x0, 236), (x0 + sx * 8, 196), (x0 - sx * 6, 150), (x0 + sx * 6, 110)]
            sp = P.smooth_list(pts, 14)
            d.path(ribbon(sp, taper(len(sp), 10, 0.2, 1.0, peak=0.4)), fill=glow, op=0.3)
    for _ in range(10):
        x, y = rng.uniform(26, 230), rng.uniform(30, 220)
        d.circle(x, y, 5, fill=d.rad([(0, glow, 0.5), (1, glow, 0)], x, y, 5))
        d.circle(x, y, 1.2, fill="#ffffff", opacity=0.8)


def portrait(fn):
    def build():
        d = Doc(P.S, P.S, name="pt5_" + fn.__name__)
        fn(d)
        return d
    PORTRAITS["tempo_" + fn.__name__] = build
    return fn


def ghost_face(d, cx, cy, skin, glow, brow="#dfe8ea", smile=0.0, w=1.0, jaw=1.0, chin=1.0, age=0, lip="#6a8a94", ears=True):
    if ears:
        P.ears(d, cx, cy, skin, w=w)
    P.head(d, cx, cy, skin, w=w, jaw=jaw, chin=chin)
    P.brows(d, cx, cy - 16, brow, thick=3.8, angle=1.2)
    P.eyes(d, cx, cy - 3, glow=glow, spacing=16, w=10, h=4.0, age=age)
    P.nose(d, cx, cy - 2, skin, L=21, w=7)
    P.mouth(d, cx, cy + 27, skin, w=11, smile=smile, lip=lip)


@portrait
def tobren(d):
    """Tobren: a town guard of Malasugue in a brimmed kettle helm and a sea-blue tabard, gone to spirit."""
    P.background(d, "#0e2630", haze="#3a8aa0", haze2="#1a4a6a", motes="#8ef4ff", seed=21)
    P.vignette(d)
    cx, cy = 128, 118
    skin = ghost_skin("#c89a7a", 0.25)
    tabard = dict(dark="#0e2a44", base="#2a5a8a", light="#6a9ac8")
    mail = dict(dark="#2a3a44", base="#7a9aa8", light="#d8f0f8")
    P.shoulders(d, mail, top=188, spread=1.02)
    # mail rings
    for row in range(4):
        for k in range(14):
            x = 36 + k * 13 + (row % 2) * 6
            y = 204 + row * 12
            d.circle(x, y, 4, stroke=mail["dark"], stroke_width=1.2, opacity=0.6)
    d.path(poly([(96, 196), (160, 196), (170, 256), (86, 256)]), fill=d.lin([(0, tabard["light"]), (1, tabard["dark"])], 96, 196, 160, 256), stroke=OUTLINE, stroke_width=3)
    # the town's mark on the tabard: a marlin over waves
    d.path("M112,226 Q128,212 146,222 Q134,224 128,232 Q120,228 112,226 Z", fill="#dcecf4", stroke=OUTLINE, stroke_width=1.4)
    d.path("M108,240 Q118,234 128,240 T148,240", stroke="#dcecf4", sw=2.2)
    P.neck(d, cx, cy + 42, 28, 30, skin)
    ghost_face(d, cx, cy, skin, "#8ef4ff", smile=0.8, jaw=1.04)
    # stubble shadow
    d.path(smooth([(cx - 30, cy + 22), (cx - 16, cy + 44), (cx, cy + 50), (cx + 16, cy + 44), (cx + 30, cy + 22), (cx + 18, cy + 36), (cx, cy + 40), (cx - 18, cy + 36)], tension=0.4),
           fill=skin["shade"], op=0.3)
    # kettle helm with a wide brim
    helm = dict(dark="#2a4450", base="#8ab4c2", light="#eefcff")
    dome = smooth([(cx - 44, cy - 26), (cx - 40, cy - 56), (cx - 18, cy - 74), (cx + 18, cy - 74), (cx + 40, cy - 56), (cx + 44, cy - 26)], closed=False, tension=0.5) + " Z"
    d.path(dome, stroke=OUTLINE, sw=5)
    d.path(dome, fill=d.lin([(0, helm["light"]), (0.4, helm["base"]), (1, helm["dark"])], cx - 44, 0, cx + 44, 0))
    brim = smooth([(cx - 70, cy - 22), (cx - 40, cy - 34), (cx, cy - 36), (cx + 40, cy - 34), (cx + 70, cy - 22), (cx + 40, cy - 22), (cx, cy - 24), (cx - 40, cy - 22)], tension=0.4)
    d.path(brim, stroke=OUTLINE, sw=5)
    d.path(brim, fill=d.lin([(0, helm["light"]), (1, helm["dark"])], cx, cy - 36, cx, cy - 20))
    d.path(f"M{cx},{cy - 74} L{cx},{cy - 36}", stroke=helm["light"], sw=2, op=0.6)
    for sx in (-1, 1):
        d.circle(cx + sx * 30, cy - 34, 2.2, fill=helm["light"], stroke=OUTLINE, stroke_width=0.8)
    spectral(d, "#8ef4ff", seed=4)
    P.frame(d, dict(dark="#123a42", base="#5aaab8", light="#dcfaff"), gem_col="#8ef4ff")


def renowned_frame(d, gem):
    P.frame(d, dict(dark="#4a3010", base="#c89a48", light="#fff0c8"), gem_col=gem)


@portrait
def hollan(d):
    """Hollan Greywall: an old warden with a great grey beard, a nasal helm and the rim of a tower shield."""
    P.background(d, "#1e1a10", haze="#b08a40", haze2="#3a6a78", motes="#ffd890", seed=31)
    P.vignette(d)
    cx, cy = 132, 112
    skin = ghost_skin("#caa07a", 0.3)
    plate = dict(dark="#2a3a40", base="#8aa0a8", light="#e8f6fa")
    # tower shield rim behind his left shoulder
    with d.g(T(58, 180, -8, 1.55)):
        tower_shield(d, w=54, h=80, face=dict(dark="#3a2a14", base="#7a6038", light="#c8a870"), band=plate)
    P.shoulders(d, plate, top=190, spread=1.08)
    for sx in (-1, 1):
        d.path(smooth([(cx + sx * 40, 196), (cx + sx * 84, 190), (cx + sx * 104, 214)], closed=False), stroke=GOLD["base"], sw=3)
    P.neck(d, cx, cy + 40, 30, 30, skin)
    ghost_face(d, cx, cy, skin, "#ffd890", brow="#e6ecee", smile=-0.5, w=1.06, jaw=1.1, age=2)
    # great beard
    beard = smooth([(cx - 38, cy + 6), (cx - 42, cy + 44), (cx - 26, cy + 84), (cx, cy + 100), (cx + 26, cy + 84), (cx + 42, cy + 44), (cx + 38, cy + 6),
                    (cx + 20, cy + 30), (cx, cy + 34), (cx - 20, cy + 30)], tension=0.45)
    d.path(beard, stroke=OUTLINE, sw=4)
    d.path(beard, fill=d.lin([(0, "#f4f8f8"), (0.6, "#b8c4c8"), (1, "#7a8a90")], cx, cy + 6, cx, cy + 100))
    for k in range(7):
        x = cx - 24 + k * 8
        d.path(smooth([(x, cy + 40), (x + 2, cy + 66), (x - 1, cy + 88)], closed=False), stroke="#8a9aa0", sw=1.2, op=0.7)
    d.path(f"M{cx - 20},{cy + 26} Q{cx},{cy + 20} {cx + 20},{cy + 26}", stroke="#dfe8ea", sw=5)
    # nasal helm
    helm = smooth([(cx - 44, cy - 20), (cx - 42, cy - 54), (cx - 20, cy - 74), (cx + 20, cy - 74), (cx + 42, cy - 54), (cx + 44, cy - 20)], closed=False, tension=0.5) + " Z"
    d.path(helm, stroke=OUTLINE, sw=5)
    d.path(helm, fill=d.lin([(0, plate["light"]), (0.45, plate["base"]), (1, plate["dark"])], cx - 44, 0, cx + 44, 0))
    d.path(f"M{cx - 45},{cy - 24} L{cx + 45},{cy - 24}", stroke=GOLD["base"], sw=5)
    d.shape(poly([(cx - 5, cy - 26), (cx + 5, cy - 26), (cx + 4, cy + 10), (cx - 4, cy + 10)]), fill=d.lin([(0, plate["light"]), (1, plate["dark"])], cx - 5, 0, cx + 5, 0), ow=2)
    spectral(d, "#ffd890", seed=6)
    renowned_frame(d, "#ffd890")


@portrait
def kavira(d):
    """Kavira Vane: a Corvessa duelist, short storm-swept hair, a high-collared coat, lightning in her eyes."""
    P.background(d, "#12102e", haze="#6a4ac0", haze2="#ffe23a", motes="#b88aff", seed=41)
    P.vignette(d)
    cx, cy = 126, 116
    skin = ghost_skin("#e0b494", 0.25)
    coat = dict(dark="#10122a", base="#2c3470", light="#6a7ac8")
    P.shoulders(d, coat, top=186, spread=0.96)
    for sx in (-1, 1):
        col = smooth([(cx + sx * 18, 176), (cx + sx * 44, 160), (cx + sx * 56, 196), (cx + sx * 30, 204)], tension=0.4)
        d.path(col, stroke=OUTLINE, sw=4)
        d.path(col, fill=d.lin([(0, coat["light"]), (1, coat["dark"])], cx, 160, cx + sx * 56, 204))
    for y in (212, 230, 248):
        d.circle(cx, y, 3.4, fill=GOLD["light"], stroke=OUTLINE, stroke_width=1)
    P.neck(d, cx, cy + 42, 24, 30, skin)
    # hair behind
    back = smooth([(cx - 44, cy + 20), (cx - 50, cy - 30), (cx - 30, cy - 66), (cx + 10, cy - 76), (cx + 46, cy - 56), (cx + 52, cy - 10), (cx + 44, cy + 24)], tension=0.45)
    d.path(back, fill="#1a1a2a", stroke=OUTLINE, stroke_width=4)
    ghost_face(d, cx, cy, skin, "#fff6a0", brow="#2a2a3a", smile=0.6, w=0.94, jaw=0.9, chin=0.86, lip="#8a6a88")
    # swept fringe
    fringe = smooth([(cx - 42, cy - 18), (cx - 34, cy - 56), (cx + 4, cy - 70), (cx + 44, cy - 50), (cx + 40, cy - 30), (cx + 10, cy - 44), (cx - 16, cy - 36)], tension=0.45)
    d.path(fringe, fill="#24243a", stroke=OUTLINE, stroke_width=3)
    for k in range(4):
        d.path(smooth([(cx - 30 + k * 16, cy - 58), (cx - 18 + k * 16, cy - 44), (cx - 22 + k * 16, cy - 30)], closed=False), stroke="#4a4a6a", sw=1.4)
    # a lightning scar down her cheek
    bolt(d, [(cx + 22, cy - 10), (cx + 28, cy + 4), (cx + 20, cy + 12), (cx + 26, cy + 26)], width=3, pal=EL["lightning"])
    zig_bolt(d, 206, 70, 56, EL["lightning"], lean=0.1)
    spectral(d, "#b88aff", seed=8)
    renowned_frame(d, "#fff6a0")


@portrait
def maudra(d):
    """Maudra Vell, the Lantern Saint: a hooded healer with a kind, tired face, lit from below by her lantern."""
    P.background(d, "#241c0e", haze="#ffe08a", haze2="#9affc8", motes="#fff0b0", seed=51)
    P.vignette(d)
    cx, cy = 128, 114
    skin = ghost_skin("#e8c4a0", 0.3)
    robe = dict(dark="#3a2e1a", base="#8a7650", light="#e0d0a0")
    hood = smooth([(cx - 66, cy + 80), (cx - 68, cy - 14), (cx - 46, cy - 70), (cx, cy - 84), (cx + 46, cy - 70), (cx + 68, cy - 14), (cx + 66, cy + 80)], tension=0.45)
    d.path(hood, stroke=OUTLINE, sw=5)
    d.path(hood, fill=d.lin([(0, robe["light"]), (0.5, robe["base"]), (1, robe["dark"])], cx - 68, cy - 80, cx + 68, cy + 80))
    P.shoulders(d, robe, top=188, spread=1.0)
    P.neck(d, cx, cy + 40, 24, 30, skin)
    ghost_face(d, cx, cy, skin, "#fff0b0", brow="#c8b8a0", smile=0.9, w=0.9, jaw=0.88, chin=0.86, age=1, lip="#9a7a6a", ears=False)
    inner = smooth([(cx - 50, cy - 10), (cx - 36, cy - 56), (cx, cy - 66), (cx + 36, cy - 56), (cx + 50, cy - 10), (cx + 40, cy - 38), (cx, cy - 50), (cx - 40, cy - 38)], tension=0.45)
    d.path(inner, fill=robe["base"], stroke=OUTLINE, stroke_width=3)
    # lantern held low: its light warms the face from below
    d.circle(cx, 240, 70, fill=d.rad([(0, "#fff6c8", 0.7), (1, "#fff6c8", 0)], cx, 240, 70))
    d.shape(poly([(cx - 16, 216), (cx + 16, 216), (cx + 18, 250), (cx - 18, 250)]), fill="#fff6d0", ow=2.4)
    flame(d, cx, 246, 0.42, EL["light"])
    d.path(f"M{cx - 16},216 Q{cx},200 {cx + 16},216", stroke=GOLD["base"], sw=3)
    spectral(d, "#fff0b0", seed=10)
    renowned_frame(d, "#9affc8")


@portrait
def cindrel(d):
    """Cindrel Ashreed: a hunter with a long soot-streaked braid and ember eyes, a bow over her shoulder."""
    P.background(d, "#2a0e06", haze="#ff6a14", haze2="#ffd34a", motes="#ffb060", seed=61)
    P.vignette(d)
    cx, cy = 124, 116
    skin = ghost_skin("#c8906a", 0.3)
    leather = dict(dark="#2a160c", base="#6a3e22", light="#b87a4a")
    with d.g(T(190, 150, 20, 1.6)):
        bow(d, H=110, pal=dict(dark="#3a1a0c", base="#8a5a32", light="#e0b080"))
    P.shoulders(d, leather, top=188, spread=0.98)
    d.path(poly([(60, 256), (150, 188), (162, 196), (78, 256)]), fill="#3a200e", stroke=OUTLINE, stroke_width=2.4)
    P.neck(d, cx, cy + 42, 24, 30, skin)
    hair = smooth([(cx - 44, cy + 10), (cx - 46, cy - 36), (cx - 22, cy - 66), (cx + 18, cy - 70), (cx + 46, cy - 44), (cx + 46, cy + 4)], tension=0.45)
    d.path(hair, fill="#3a1a10", stroke=OUTLINE, stroke_width=4)
    ghost_face(d, cx, cy, skin, "#ffb060", brow="#4a2210", smile=0.2, w=0.94, jaw=0.9, chin=0.86, lip="#8a4a3a")
    d.path(smooth([(cx - 42, cy - 16), (cx - 30, cy - 58), (cx + 10, cy - 66), (cx + 44, cy - 40), (cx + 30, cy - 44), (cx - 6, cy - 50), (cx - 30, cy - 34)], tension=0.45),
           fill="#4a2414", stroke=OUTLINE, stroke_width=3)
    # the braid over her shoulder
    for k in range(7):
        x, y = cx - 44 + k * 1.5, cy + 10 + k * 14
        d.ellipse(x, y, 9, 8, fill="#4a2414", stroke=OUTLINE, stroke_width=2)
    # soot streaks under the eyes
    for sx in (-1, 1):
        d.path(f"M{cx + sx * 10},{cy + 6} L{cx + sx * 24},{cy + 10}", stroke="#2a1a14", sw=3, op=0.6)
    for x in (58, 200):
        flame(d, x, 250, 0.5, EL["fire"])
    spectral(d, "#ffb060", seed=12)
    renowned_frame(d, "#ff6a14")


@portrait
def vessik(d):
    """Vessik Thorn: a hooded man with a cloth mask over his mouth, burn scars about his eyes, violet dark behind him."""
    P.background(d, "#0c0616", haze="#8a3ad0", haze2="#3a1a5a", motes="#b684ea", seed=71)
    P.vignette(d)
    cx, cy = 128, 114
    skin = ghost_skin("#b0a0c0", 0.3)
    cloak = dict(dark="#0a0612", base="#2a1a3a", light="#5a4a78")
    hood = smooth([(cx - 70, cy + 84), (cx - 70, cy - 10), (cx - 50, cy - 70), (cx, cy - 88), (cx + 50, cy - 70), (cx + 70, cy - 10), (cx + 70, cy + 84)], tension=0.45)
    d.path(hood, stroke=OUTLINE, sw=5)
    d.path(hood, fill=d.lin([(0, cloak["light"]), (0.5, cloak["base"]), (1, cloak["dark"])], cx - 70, cy - 88, cx + 70, cy + 84))
    P.shoulders(d, cloak, top=188, spread=1.02)
    P.neck(d, cx, cy + 40, 26, 30, skin)
    ghost_face(d, cx, cy, skin, "#c88aff", brow="#1a1024", smile=-1.0, w=0.94, jaw=0.96, age=1, ears=False)
    # burn scars
    for sx in (-1, 1):
        d.path(smooth([(cx + sx * 8, cy - 14), (cx + sx * 28, cy - 12), (cx + sx * 34, cy + 4)], closed=False), stroke="#7a3a4a", sw=3, op=0.6)
    # mask over mouth and nose
    mask = smooth([(cx - 40, cy + 4), (cx + 40, cy + 4), (cx + 36, cy + 34), (cx + 16, cy + 52), (cx - 16, cy + 52), (cx - 36, cy + 34)], tension=0.35)
    d.path(mask, stroke=OUTLINE, sw=4)
    d.path(mask, fill=d.lin([(0, "#3a2a4a"), (1, "#140a1e")], cx, cy + 4, cx, cy + 52))
    for k in range(3):
        d.path(f"M{cx - 34 + k * 4},{cy + 14 + k * 12} Q{cx},{cy + 20 + k * 12} {cx + 34 - k * 4},{cy + 14 + k * 12}", stroke="#5a4a6a", sw=1.2)
    inner = smooth([(cx - 52, cy - 6), (cx - 40, cy - 60), (cx, cy - 72), (cx + 40, cy - 60), (cx + 52, cy - 6), (cx + 42, cy - 36), (cx, cy - 52), (cx - 42, cy - 36)], tension=0.45)
    d.path(inner, fill=cloak["dark"], stroke=OUTLINE, stroke_width=3)
    for sx in (-1, 1):
        with d.g(T(cx + sx * 84, 226, sx * 20, 1.1)):
            dagger(d, L=40, W=10, pal=dict(dark="#10041a", base="#c8a8f0", light="#ffffff"), hilt=SPIRIT_METAL)
    spectral(d, "#b684ea", seed=14)
    renowned_frame(d, "#c88aff")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def build():
    out = []
    for name, fn in SKILLS.items():
        p = os.path.join(UI, "icons", "skills", "tempo_%s.svg" % name)
        write(p, fn().svg())
        out.append(p)
    for name, fn in CLASSES.items():
        p = os.path.join(UI, "icons", "classes", "%s.svg" % name)
        write(p, fn().svg())
        out.append(p)
    for name, fn in PORTRAITS.items():
        p = os.path.join(UI, "portraits", "%s.svg" % name)
        write(p, fn().svg())
        out.append(p)
    return out


if __name__ == "__main__":
    for p in build():
        print("wrote", os.path.relpath(p, ROOT))
