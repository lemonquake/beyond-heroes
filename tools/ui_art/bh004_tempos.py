"""bh-004 UI art: Tempos (spirit companions, docs/LORE.md §9).

Writes (same painted style and helpers as the existing icon and portrait families):
  game/assets/ui/icons/skills/tempo_<skill>.svg      12 Tempo skill icons, 128x128, spectral-teal bezel
  game/assets/ui/icons/classes/tempo_<class>.svg     swordsman / archer / thief crests, 128x128
  game/assets/ui/portraits/tempo_caller.svg           Veyra Ashgrave, the Tempo-Caller, 256x256

Usage:  python tools/ui_art/bh004_tempos.py
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

from bh_svg import (Doc, OUTLINE, GOLD, STEEL, CRIMSON, BONE, WOOD, LEATHER, f, poly, smooth, mix, lt, dk, ribbon, taper,  # noqa: E402
                    qbez, polar, rrect_path, circle_path, teardrop)
from bh_shapes import (T, sword, dagger, bow, arrow, heater_shield, slash_arc, impact_star, swirl, gust, heart, droplet,  # noqa: E402
                       void_orb, rune_ring, motes, skull, horn)
from bh_frames import backdrop, vignette, skill_frame, medallion_bg, medallion_rim  # noqa: E402
import portraits as P  # noqa: E402

SPIRIT = dict(dark="#0e3a44", base="#62c8d8", light="#e4fcff", glow="#8ef4ff")
SPIRIT_METAL = dict(dark="#123a42", base="#5aaab8", light="#dcfaff")
GHOST_STEEL = dict(dark="#2a4a58", base="#a8dce8", light="#ffffff", glow="#c8f8ff")
HEAL = dict(dark="#0e4a2c", base="#46c888", light="#d8ffe8", glow="#9affc8")
POISON = dict(dark="#1e3a08", base="#6ab82a", light="#d8ff9a", glow="#b0ff5a")
SHADOW = dict(dark="#10081c", base="#4a2a70", light="#b89ae8", glow="#a070ff")

SKILLS = {}
CLASSES = {}


def skill(inner, haze=None, haze2=None):
    def deco(fn):
        def build():
            d = Doc(name="tempo_" + fn.__name__)
            backdrop(d, inner, haze=haze, haze2=haze2)
            fn(d)
            # every Tempo icon carries a faint ghost-light wash from below
            d.circle(64, 120, 60, fill=d.rad([(0, SPIRIT["glow"], 0.18), (1, SPIRIT["glow"], 0)], 64, 120, 60))
            vignette(d, 0.7)
            skill_frame(d, SPIRIT_METAL)
            return d
        SKILLS[fn.__name__] = build
        return fn
    return deco


def motes2(d, pts, color, glow_color=None, size=2.0):
    motes(d, [(x, y, 1.0) for x, y in pts], color, glow_color, size=size)


def ghost_trail(d, pts, w, col=SPIRIT["glow"], op=0.5):
    d.path(ribbon(pts, taper(len(pts), w, 0.0, 1.0, peak=0.8)), fill=col, op=op)


# ------------------------------------------------------------------------------------------ swordsman


@skill("#0c2a34", haze="#2a8aa0", haze2="#1a4a70")
def sw_cleave(d):
    cx, cy = 60, 80
    slash_arc(d, cx, cy, 46, math.radians(165), math.radians(340), 20, dict(dark="#0e3a44", base="#dffaff", light="#ffffff", glow=SPIRIT["glow"]))
    slash_arc(d, cx, cy, 33, math.radians(185), math.radians(320), 8, dict(dark="#0e3a44", base="#dffaff", light="#ffffff", glow=SPIRIT["glow"]), glow=False)
    with d.g(T(cx + 6, cy - 2, 58, 1.0)):
        sword(d, L=58, W=12, pal=GHOST_STEEL, hilt=SPIRIT_METAL)
    motes2(d, [(100, 40), (108, 58), (94, 30), (112, 72)], SPIRIT["light"], SPIRIT["glow"], size=2.2)


@skill("#102030", haze="#3a7aa0", haze2="#8ef4ff")
def sw_challenge(d):
    # a spectral skull roaring, rings of challenge rolling outward
    for r, op in ((48, 0.35), (38, 0.5), (28, 0.7)):
        d.circle(64, 66, r, stroke=SPIRIT["glow"], stroke_width=3.0, opacity=op)
    skull(d, 64, 62, 0.95, pal=dict(dark="#2a5a68", base="#c8f0f8", light="#ffffff", glow="#8ef4ff"), eye_glow=SPIRIT["glow"])
    for a in range(0, 360, 45):
        p0 = polar(64, 66, 52, math.radians(a))
        p1 = polar(64, 66, 60, math.radians(a))
        d.path(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}", stroke="#ffffff", sw=2.4, op=0.7)


@skill("#0e2230", haze="#4a7a98", haze2="#2a5a78")
def sw_charge(d):
    for i, (y, L) in enumerate(((36, 36), (54, 48), (72, 42), (90, 30))):
        ghost_trail(d, [(8, y + 6), (8 + L, y)], 7, op=0.45)
    impact_star(d, 100, 58, 26, "#ffffff", SPIRIT["glow"], n=9, inner=0.3)
    with d.g(T(58, 64, 90, 1.0)):
        sword(d, L=62, W=12, pal=GHOST_STEEL, hilt=SPIRIT_METAL)


@skill("#0a2a24", haze="#2ac88a", haze2="#8ef4ff")
def sw_mend(d):
    rune_ring(d, 64, 66, 44, HEAL["glow"], width=2.4, ticks=20, op=0.8)
    heart(d, 64, 64, 0.9, HEAL)
    with d.g(T(64, 64, -35, 0.8)):
        sword(d, L=56, W=10, pal=GHOST_STEEL, hilt=SPIRIT_METAL)
    motes2(d, [(34, 36), (96, 40), (30, 92), (98, 96)], HEAL["light"], HEAL["glow"], size=2.4)


# ------------------------------------------------------------------------------------------ archer


@skill("#0c2430", haze="#2a8aa0", haze2="#1a3a58")
def ar_pierce(d):
    # three ghostly rings pierced by one arrow
    for x, r in ((46, 16), (66, 14), (86, 12)):
        d.ellipse(x, 64, r * 0.45, r, stroke=SPIRIT["glow"], stroke_width=3, opacity=0.75)
    ghost_trail(d, [(10, 66), (60, 64)], 9, op=0.5)
    with d.g(T(18, 64, 90, 1.25)):
        arrow(d, L=82, pal=GHOST_STEEL, fletch=dict(dark="#0e3a44", base="#62c8d8", light="#e4fcff"))
    impact_star(d, 114, 64, 12, "#ffffff", SPIRIT["glow"], n=7)


@skill("#0e1e2c", haze="#3a6a88", haze2="#8ef4ff")
def ar_volley(d):
    d.ellipse(64, 100, 44, 12, stroke=SPIRIT["glow"], stroke_width=2.6, opacity=0.7)
    d.ellipse(64, 100, 44, 12, fill=SPIRIT["glow"], opacity=0.12)
    rng = random.Random(7)
    for i, x in enumerate((30, 48, 64, 80, 98)):
        y = 24 + rng.uniform(-6, 16) + (i % 2) * 8
        ghost_trail(d, [(x - 6, y - 26), (x, y)], 5, op=0.35)
        with d.g(T(x, y + 44, 170 + rng.uniform(-6, 6), 0.62)):
            arrow(d, L=70, pal=GHOST_STEEL, fletch=dict(dark="#0e3a44", base="#62c8d8", light="#e4fcff"))


@skill("#0a2a22", haze="#2ac88a", haze2="#1a4a58")
def ar_mend(d):
    ghost_trail(d, [(12, 100), (70, 50)], 10, col=HEAL["glow"], op=0.45)
    with d.g(T(26, 92, 45, 1.0)):
        arrow(d, L=78, pal=dict(dark="#1e5a3a", base="#a8f0c8", light="#ffffff"), fletch=HEAL)
    heart(d, 92, 40, 0.55, HEAL)
    motes2(d, [(106, 64), (80, 22), (112, 30)], HEAL["light"], HEAL["glow"], size=2.0)


@skill("#101c2a", haze="#3a7a98", haze2="#1a3a58")
def ar_disengage(d):
    gust(d, [(100, 96), (76, 84), (52, 60), (40, 34)], 12, SPIRIT["glow"], op=0.55)
    with d.g(T(46, 58, -20, 0.8)):
        bow(d, H=86, pal=dict(dark="#1a3a48", base="#5aaab8", light="#dcfaff"))
    # the snare left behind
    for r in (14, 9):
        d.ellipse(94, 104, r * 1.6, r * 0.5, stroke=SPIRIT["glow"], stroke_width=2.2, opacity=0.8)


# ------------------------------------------------------------------------------------------ thief


@skill("#120a22", haze="#6a3aa8", haze2="#1a0a2a")
def th_shadowstep(d):
    void_orb(d, 44, 60, 22, pal=SHADOW)
    ghost_trail(d, [(44, 60), (86, 58)], 12, col=SHADOW["glow"], op=0.4)
    with d.g(T(88, 70, 30, 1.25)):
        dagger(d, L=44, W=11, pal=GHOST_STEEL, hilt=SPIRIT_METAL)
    impact_star(d, 104, 36, 12, "#ffffff", SHADOW["glow"], n=7)


@skill("#0e1a08", haze="#4a8a1a", haze2="#1a2a08")
def th_venom(d):
    for ang, x in ((-28, 50), (28, 78)):
        with d.g(T(x, 92, ang, 1.2)):
            dagger(d, L=46, W=11, pal=dict(dark="#2a4a1a", base="#c0e8a0", light="#ffffff"), hilt=SPIRIT_METAL)
    for x, y in ((46, 34), (80, 30), (64, 20)):
        d.path(teardrop(x, y + 20, 4.2, 10), fill=POISON["base"], stroke=OUTLINE, stroke_width=1.2)
        d.circle(x - 1.2, y + 17, 1.2, fill="#ffffff", opacity=0.7)


@skill("#101014", haze="#4a4a5a", haze2="#2a2a3a")
def th_smoke(d):
    rng = random.Random(3)
    for i in range(9):
        x, y = 64 + rng.uniform(-34, 34), 70 + rng.uniform(-26, 22)
        r = rng.uniform(14, 24)
        d.circle(x, y, r, fill=d.rad([(0, "#6a6a78", 0.85), (0.7, "#2a2a34", 0.6), (1, "#101014", 0)], x - 4, y - 4, r))
    swirl(d, 64, 66, 6, 30, 0.0, 1.4, 5, "#b8b8c8", op=0.6)
    d.circle(64, 40, 5, fill=SHADOW["glow"], opacity=0.8)


@skill("#0a2226", haze="#2ac8a0", haze2="#6a3aa8")
def th_remedy(d):
    # a stolen draught: a small flask trailing healing light
    flask = smooth([(56, 40), (56, 56), (40, 76), (44, 100), (84, 100), (88, 76), (72, 56), (72, 40)], tension=0.6)
    d.path(flask, stroke=OUTLINE, sw=5)
    d.path(flask, fill=d.lin([(0, "#e4fcff"), (0.5, "#8ad8c8"), (1, "#2a6a64")], 40, 40, 88, 100), op=0.85)
    liquid = smooth([(43, 80), (46, 98), (82, 98), (85, 80), (64, 84)], tension=0.6)
    d.path(liquid, fill=HEAL["base"], op=0.9)
    d.shape(rrect_path(54, 30, 20, 12, 3), fill=WOOD["base"], ow=2)
    d.path("M50,60 Q46,74 50,90", stroke="#ffffff", sw=3, op=0.6)
    motes2(d, [(96, 36), (104, 56), (30, 44), (24, 70)], HEAL["light"], HEAL["glow"], size=2.4)


# ------------------------------------------------------------------------------------------ class crests (128)


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
def swordsman(d):
    with d.g(T(64, 70, 0, 0.7)):
        heater_shield(d, w=60, h=70, field=dict(dark="#0e3a44", base="#2a7a8a", light="#8ef4ff"), rim=GHOST_STEEL, emblem="cross", boss=SPIRIT_METAL)
    with d.g(T(64, 60, 45, 1.0)):
        sword(d, L=66, W=11, pal=GHOST_STEEL, hilt=SPIRIT_METAL)


@crest
def archer(d):
    with d.g(T(58, 64, 0, 1.0)):
        bow(d, H=86, pal=dict(dark="#1a3a48", base="#5aaab8", light="#dcfaff"))
    with d.g(T(34, 64, 90, 1.05)):
        arrow(d, L=72, pal=GHOST_STEEL, fletch=dict(dark="#0e3a44", base="#62c8d8", light="#e4fcff"))


@crest
def thief(d):
    for ang in (-35, 35):
        with d.g(T(64, 84, ang, 1.35)):
            dagger(d, L=42, W=10, pal=GHOST_STEEL, hilt=SPIRIT_METAL)
    # a watching eye of shadow over the crossed blades
    d.ellipse(64, 40, 16, 7, fill=SHADOW["dark"], stroke=OUTLINE, stroke_width=2)
    d.circle(64, 40, 5, fill=SHADOW["glow"])
    d.circle(63, 39, 1.6, fill="#ffffff")


# ------------------------------------------------------------------------------------------ portrait (256)


def tempo_caller():
    """Veyra Ashgrave: an old shrine-woman in a sea-grey shawl, shell charms, lit from below by cold spirit light."""
    d = Doc(P.S, P.S, name="pt4_tempo_caller")
    P.background(d, "#10262e", haze="#5ad0e0", haze2="#2a4a6a", motes="#8ef4ff", seed=91)
    P.vignette(d)
    cx, cy = 128, 114
    shawl = dict(dark="#1a2a30", base="#4a6a70", light="#9ac0c4")
    # shawl behind the head
    veil = smooth([(cx - 62, cy + 76), (cx - 64, cy - 18), (cx - 44, cy - 66), (cx, cy - 78), (cx + 44, cy - 66), (cx + 64, cy - 18), (cx + 62, cy + 76)], tension=0.45)
    d.path(veil, stroke=OUTLINE, sw=5)
    d.path(veil, fill=d.lin([(0, shawl["light"]), (0.5, shawl["base"]), (1, shawl["dark"])], cx - 64, cy - 70, cx + 64, cy + 70))
    P.shoulders(d, shawl, top=186, spread=1.0)
    # necklace of shells and small bones
    d.path(f"M100,192 Q128,224 156,192", stroke="#2a1a10", sw=2)
    for i, t in enumerate((0.1, 0.3, 0.5, 0.7, 0.9)):
        x = 100 + 56 * t
        y = 192 + 32 * math.sin(math.pi * t)
        if i % 2 == 0:
            d.ellipse(x, y + 3, 4.2, 5.4, fill=BONE["light"], stroke=OUTLINE, stroke_width=1.2)
            d.path(f"M{f(x - 2)},{f(y + 1)} L{f(x + 2)},{f(y + 5)}", stroke=BONE["dark"], sw=0.8)
        else:
            d.path(f"M{f(x)},{f(y - 1)} L{f(x)},{f(y + 9)}", stroke=BONE["light"], sw=3)
            d.path(f"M{f(x)},{f(y - 1)} L{f(x)},{f(y + 9)}", stroke=OUTLINE, sw=0.6, op=0.6)
    P.neck(d, cx, cy + 42, 26, 28, P.SKIN_OLD)
    P.head(d, cx, cy, P.SKIN_OLD, w=0.9, jaw=0.86, chin=0.84, top=1.0)
    # grey hair pulled back under the shawl, a loose strand
    for sx in (-1, 1):
        hp = smooth([(cx, cy - 54), (cx + sx * 26, cy - 50), (cx + sx * 40, cy - 26), (cx + sx * 40, cy + 8), (cx + sx * 34, cy + 16), (cx + sx * 32, cy - 12), (cx + sx * 20, cy - 36), (cx + sx * 4, cy - 44)], tension=0.5)
        d.path(hp, fill="#c8ccd0", stroke=OUTLINE, stroke_width=2)
        d.path(smooth([(cx + sx * 10, cy - 48), (cx + sx * 28, cy - 40), (cx + sx * 36, cy - 10)], closed=False), stroke="#8a9098", sw=1.2)
    d.path(smooth([(cx + 30, cy - 20), (cx + 36, cy + 10), (cx + 30, cy + 34)], closed=False), stroke="#dfe3e6", sw=1.6)
    d.path(smooth([(cx - 52, cy - 18), (cx - 38, cy - 58), (cx, cy - 70), (cx + 38, cy - 58), (cx + 52, cy - 18), (cx + 40, cy - 44), (cx, cy - 56), (cx - 40, cy - 44)], tension=0.45),
           fill=shawl["base"], stroke=OUTLINE, stroke_width=3)
    # age lines
    for k in range(3):
        y = cy - 34 + k * 5
        d.path(f"M{cx - 18 + k * 2},{y} Q{cx},{y - 3} {cx + 18 - k * 2},{y}", stroke=P.SKIN_OLD["shade"], sw=1.1, op=0.5)
    P.brows(d, cx, cy - 16, "#c8ccd0", thick=3.4, angle=1.0, w=13)
    # pale, far-seeing eyes that catch the spirit light
    P.eyes(d, cx, cy - 3, iris="#8ad8e0", glow="#8ef4ff", spacing=16, w=10, h=3.6, age=2)
    P.nose(d, cx, cy - 2, P.SKIN_OLD, L=21, w=8)
    P.mouth(d, cx, cy + 27, P.SKIN_OLD, w=11, smile=0.35, lip="#8a4a44")
    for sx in (-1, 1):
        d.path(f"M{cx + sx * 16},{cy + 16} Q{cx + sx * 20},{cy + 26} {cx + sx * 16},{cy + 34}", stroke=P.SKIN_OLD["shade"], sw=1.2, op=0.5)
    # a wisp of a fallen warrior's spirit curling over her shoulder
    wisp = [(196, 210), (206, 170), (196, 136), (206, 104), (198, 76)]
    d.path(ribbon(smooth_list(wisp), taper(len(smooth_list(wisp)), 12, 0.2, 1.0, peak=0.4)), fill="#8ef4ff", op=0.35)
    d.circle(198, 74, 8, fill=d.rad([(0, "#ffffff", 0.9), (1, "#8ef4ff", 0)], 198, 74, 12))
    # cold light from below
    d.circle(cx, 262, 80, fill=d.rad([(0, "#8ef4ff", 0.3), (1, "#8ef4ff", 0)], cx, 262, 80))
    P.frame(d, dict(dark="#123a42", base="#5aaab8", light="#dcfaff"), gem_col="#8ef4ff")
    return d


def smooth_list(pts, n=14):
    return P.smooth_list(pts, n)


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
    p = os.path.join(UI, "portraits", "tempo_caller.svg")
    write(p, tempo_caller().svg())
    out.append(p)
    return out


if __name__ == "__main__":
    for p in build():
        print("wrote", os.path.relpath(p, ROOT))
