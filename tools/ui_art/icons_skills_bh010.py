"""bh-010 skill icons (128x128, full-bleed painted emblems) for the hero expansion.

Three visual families, all written into game/assets/ui/icons/skills/:
  * actives  - square bezel (skill_frame); knight gold, mage violet-silver, ranger weathered bronze with a stitched
               green-leather band, shadowblade blackened steel with violet studs.
  * auras    - hexagonal bezel with radiant corners + a glowing halo ring behind the emblem. Offensive auras: red-gold
               bezel; defensive auras: blue-silver bezel.
  * passives - round knurled medallion, emblem muted by a patina wash (reads as "always on", quieter than actives).

Registered in build_all.py as category "skills10" (registry SKILLS10). AURA_EMBLEMS is reused by the status badges.
"""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, EL, STEEL, CRIMSON, GOLD, BRONZE, INDIGO, ARCANE, LEATHER, WOOD, BONE, OUTLINE, f, poly, smooth,
                    mix, lt, dk, ribbon, taper, arc_pts, bez, qbez, star_pts, ngon, jag_line, blob, teardrop, polar,
                    faceted, rrect_path, circle_path, lerp)
from bh_shapes import (T, sword, greatsword, blade, dagger, axe, heater_shield, heater_pts, tower_shield, cuirass, flame,
                       ice_shard, snowflake, bolt, zig_bolt, rock, swirl, gust, wave, sun, rune_ring, motes, slash_arc,
                       humanoid_robed, fist, banner, heart, hourglass, impact_star, eye, skull, crystal, droplet, bow,
                       smooth_pts, gem)
from bh_frames import (backdrop, vignette, skill_frame, KNIGHT_METAL, MAGE_METAL, RANGER_METAL, RANGER_ACCENT, SHADOW_METAL,
                       SHADOW_ACCENT, AURA_OFF_METAL, AURA_DEF_METAL, skill_frame_accent, aura_frame, aura_halo,
                       passive_frame)
from bh010_motifs import (BRIGHT_STEEL, DARK_STEEL, HOLY, VENOM, VIOLET, BLOOD, FOREST, MANA, HEAL, FLETCH_GREEN,
                          FLETCH_WHITE, arrow2, javelin, knife, dagger2, claw, warhammer, shuriken, saw_blade, quiver,
                          trap_jaws, mine, web, bullseye, crosshair, leaf, boot, footprint, chalice, vial, fang, gear,
                          campfire, smoke, pips, hood_silhouette, cracked_skull, speed_lines, rune_glyph, cloud, wing_pair)
from icons_badges import feather, wing

SKILLS10 = {}
AURA_EMBLEMS = {}
AURA_COLORS = {}
KINDS = {}          # id -> (class, family)

METALS = {"knight": KNIGHT_METAL, "mage": MAGE_METAL, "ranger": RANGER_METAL, "shadowblade": SHADOW_METAL}
ACCENTS = {"ranger": RANGER_ACCENT, "shadowblade": SHADOW_ACCENT}
MAGE_BG = "#140e30"
RANGER_BG = "#12200e"
SHADOW_BG = "#120a1c"


def _active_frame(d, cls):
    if cls in ACCENTS:
        skill_frame_accent(d, METALS[cls], ACCENTS[cls])
    else:
        skill_frame(d, METALS[cls])


def active(cls, inner, haze=None, haze2=None):
    def deco(fn):
        def build():
            d = Doc(name="bh10_" + fn.__name__)
            backdrop(d, inner, haze=haze, haze2=haze2)
            fn(d)
            vignette(d, 0.7)
            _active_frame(d, cls)
            return d
        SKILLS10[fn.__name__] = build
        KINDS[fn.__name__] = (cls, "active")
        return fn
    return deco


def aura(kind, color, inner, haze=None, haze2=None):
    """kind: 'off' | 'def'. The emblem function draws at full 128 scale around (64, 64); it is shrunk inside the halo."""
    metal = AURA_OFF_METAL if kind == "off" else AURA_DEF_METAL

    def deco(fn):
        AURA_EMBLEMS[fn.__name__] = fn
        AURA_COLORS[fn.__name__] = (color, kind)

        def build():
            d = Doc(name="bh10_" + fn.__name__)
            backdrop(d, inner, haze=haze, haze2=haze2, cy=64)
            aura_halo(d, color, r=44)
            with d.g("translate(64 64) scale(0.74) translate(-64 -64)"):
                fn(d)
            vignette(d, 0.45, cy=64)
            aura_frame(d, metal, color)
            return d
        SKILLS10[fn.__name__] = build
        KINDS[fn.__name__] = ("knight", "aura_" + kind)
        return fn
    return deco


def passive(cls, inner, haze=None, patina=None, scale=0.76):
    def deco(fn):
        def build():
            d = Doc(name="bh10_" + fn.__name__)
            backdrop(d, inner, haze=haze, cy=64)
            with d.g(f"translate(64 64) scale({f(scale)}) translate(-64 -64)"):
                fn(d)
            passive_frame(d, METALS[cls], patina=patina or dk(inner, 0.5))
            return d
        SKILLS10[fn.__name__] = build
        KINDS[fn.__name__] = (cls, "passive")
        return fn
    return deco


SLASH_WHITE = dict(dark="#6a0a18", base="#f0e4e8", light="#ffffff", glow="#ff5a6a")
SLASH_VIOLET = dict(dark="#2a0a4a", base="#d8c0ff", light="#ffffff", glow="#b060ff")
GOLD_STEEL = dict(dark="#6a4a14", base="#e8c878", light="#fffbe6", glow="#ffe8a0")
ICE = EL["ice"]
FIRE = EL["fire"]
LIGHTNING = EL["lightning"]


# ================================================================================================ KNIGHT actives

@active("knight", "#3a1008", haze="#c0401a", haze2="#8a1a24")
def zeal(d: Doc):
    # four rapid parallel slash streaks, brightening with each hit
    for i in range(4):
        o = -30 + i * 20
        p0, p1 = (22 + o * 0.7, 18 - o * 0.7 + 8), (96 + o * 0.7, 92 - o * 0.7 + 8)
        mid = ((p0[0] + p1[0]) / 2 + 6, (p0[1] + p1[1]) / 2 - 6)
        pts = qbez(p0, mid, p1, n=20)
        w = 7 + i * 1.6
        op = 0.45 + i * 0.18
        d.path(ribbon(pts, taper(20, w * 2.4, 0.0, 0.1, peak=0.6)), fill="#ff5a3a", op=0.22 * op)
        d.path(ribbon(pts, taper(20, w, 0.0, 0.1, peak=0.6)), fill=d.lin([(0, "#ff5a3a", 0.0), (0.5, "#ffc0a0"), (1, "#ffffff")], *p0, *p1), op=min(op, 1.0))
        d.path(ribbon(pts, taper(20, w * 0.35, 0.0, 0.1, peak=0.6)), fill="#ffffff", op=min(op + 0.1, 1.0))
    with d.g(T(40, 104, 42, 1.0), op=0.3):
        sword(d, L=64, W=12, pal=dict(dark="#6a3a2a", base="#ffd0b0", light="#ffffff"), hilt=GOLD)
    with d.g(T(34, 100, 52, 1.04)):
        sword(d, L=66, W=12, pal=BRIGHT_STEEL, hilt=GOLD, glow="#ffd0a0")
    for (x, y, s) in ((104, 26, 5.5), (112, 48, 3.5), (86, 16, 3)):
        d.sparkle(x, y, s, "#fff4dc", 0.95, glow_color="#ff8a40")


@active("knight", "#2e2208", haze="#d8a030", haze2="#fff0b0")
def blessed_hammer(d: Doc):
    cx, cy = 64, 70
    # spiral path of light winding out from the centre
    pts = []
    for i in range(64):
        t = i / 63
        a = 2.4 + t * 2 * math.pi * 1.5
        r = 4 + t * 50
        pts.append((cx + r * math.cos(a), cy + r * 0.62 * math.sin(a)))
    d.path(ribbon(pts, taper(64, 14, 0.1, 1.0, peak=1.0)), fill="#ffe8a0", op=0.25)
    d.path(ribbon(pts, taper(64, 6, 0.1, 1.0, peak=1.0)), fill="#fff4c8", op=0.9)
    motes(d, [(p[0], p[1] - 5, 0.5 + i / 24) for i, p in enumerate(pts[10::5])], "#fffbe6", glow_color="#ffd070", size=1.7)
    # the hammer, big and tilted as it spins
    with d.g(T(58, 44, -28, 1.0)):
        warhammer(d, H=58, head=HOLY, glow="#ffe8a0")
    d.sparkle(96, 26, 5, "#ffffff", 1.0, glow_color="#ffd070")


@active("knight", "#101830", haze="#5a7ad0", haze2="#ffe08a")
def heavens_fist(d: Doc):
    # storm clouds
    cloud(d, [(22, 20, 16), (46, 14, 18), (74, 12, 20), (102, 18, 17), (60, 26, 14), (90, 28, 12)], top="#d8d4f0", bottom="#3a3a70")
    # lightning column
    d.path("M48,24 L80,24 L74,112 L54,112 Z", fill=d.lin([(0, "#fffbe6", 0.85), (1, "#ffe08a", 0.15)], 0, 24, 0, 112))
    rng = random.Random(21)
    col = jag_line((64, 26), (64, 106), 8, 5, rng)
    bolt(d, col, width=7, pal=dict(dark="#6a4ab0", base="#fff0a0", light="#ffffff", glow="#fff0b0"))
    # fist of light inside the column
    with d.g(T(64, 66, 0, 0.62)):
        d.glow(0, 0, 44, "#ffe8a0", 0.8)
        fist(d, pal=dict(dark="#9a7020", base="#ffe08a", light="#ffffff"), trim=dict(dark="#6a4a10", base="#fff4c0", light="#ffffff"))
    # ground impact with radiating holy bolts
    d.glow_ellipse(64, 108, 48, 10, "#ffe08a", 0.9)
    for a in (-170, -140, -110, -70, -40, -10):
        end = polar(64, 106, 46, math.radians(a))
        end = (end[0], 106 + (end[1] - 106) * 0.55)
        bolt(d, jag_line((64, 106), end, 4, 3, rng), width=3.2, pal=dict(dark="#6a4ab0", base="#ffe890", light="#ffffff", glow="#ffe8a0"), glow=False)
    impact_star(d, 64, 106, 14, "#ffffff", "#ffd070", n=8, inner=0.3)


# ================================================================================================ KNIGHT auras

@aura("off", "#ff4a2a", "#3a0c08", haze="#c02010", haze2="#ffb040")
def aura_might(d: Doc):
    d.glow(64, 64, 50, "#ff5030", 0.55)
    with d.g(T(64, 104, 0, 1.0)):
        sword(d, L=86, W=12, pal=BRIGHT_STEEL, hilt=GOLD)
    with d.g(T(64, 68, 0, 1.12)):
        fist(d, pal=dict(dark="#5a1a10", base="#c8502a", light="#ffc8a0"), trim=GOLD)
    for (x, y) in ((30, 44), (98, 44)):
        up = [(x - 7, y + 6), (x, y - 4), (x + 7, y + 6), (x + 7, y + 11), (x, y + 2), (x - 7, y + 11)]
        d.shape(poly(up), fill=d.lin([(0, "#ffe0a0"), (1, "#c83a1a")], x, y - 4, x, y + 11), ow=1.6)


@aura("off", "#ff8a20", "#3a1406", haze="#ff6a14", haze2="#ffd070")
def aura_cinders(d: Doc):
    cx, cy = 64, 64
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        x, y = polar(cx, cy, 34, a)
        with d.g(T(x, y, math.degrees(a) + 90, 0.26)):
            flame(d, 0, 0, 1.0, FIRE, glow=False, tongues=False)
    d.circle(cx, cy, 34, stroke="#ffb040", stroke_width=3, opacity=0.8)
    holy_fire = dict(dark="#b84a0a", base="#ffb040", light="#fff4c0", glow="#ffd070")
    flame(d, cx, cy + 20, 0.62, holy_fire)
    d.shape(poly([(cx - 3, cy - 2), (cx + 3, cy - 2), (cx + 3, cy + 6), (cx + 10, cy + 6), (cx + 10, cy + 11), (cx + 3, cy + 11), (cx + 3, cy + 22),
                  (cx - 3, cy + 22), (cx - 3, cy + 11), (cx - 10, cy + 11), (cx - 10, cy + 6), (cx - 3, cy + 6)]), fill="#fffbe6", ow=1.4)


@aura("off", "#7ae0ff", "#08203a", haze="#4ab0e0", haze2="#c0f0ff")
def aura_winter(d: Doc):
    cx, cy = 64, 64
    d.glow(cx, cy, 50, ICE["glow"], 0.5)
    for i in range(8):
        a = i * 45
        bx, by = polar(cx, cy, 20, math.radians(a - 90))
        with d.g(T(bx, by, a, 1.0)):
            ice_shard(d, L=26 if i % 2 == 0 else 18, W=10 if i % 2 == 0 else 7, pal=ICE)
    crystal(d, cx, cy, 11, dict(dark="#1f5a7a", base="#9ee8ff", light="#ffffff", glow="#9eeeff"), stretch=1.5, glow=False)


@aura("off", "#ffcc40", "#2e1c06", haze="#ffb030", haze2="#ff6a20")
def aura_fervor(d: Doc):
    cx, cy = 64, 62
    # speed rings
    for r, op in ((38, 0.5), (30, 0.7)):
        pts = arc_pts(cx, cy, r, math.radians(200), math.radians(340), 20)
        d.path(ribbon(pts, taper(20, 4, 0.1, 0.9, peak=0.8)), fill="#fff0b0", op=op)
        pts = arc_pts(cx, cy, r, math.radians(20), math.radians(160), 20)
        d.path(ribbon(pts, taper(20, 4, 0.1, 0.9, peak=0.8)), fill="#fff0b0", op=op)
    for flip in (False, True):
        with d.g(T(cx + (-6 if not flip else 6), cy + 6, 0, 0.62)):
            wing(d, dict(dark="#8a5a14", base="#ffd070", light="#fffbe6"), flip=flip)
    with d.g(T(cx, cy + 34, 0, 0.98)):
        sword(d, L=66, W=11, pal=GOLD_STEEL, hilt=CRIMSON, glow="#ffe8a0")


@aura("def", "#6affb0", "#082a1c", haze="#30c080", haze2="#d8ffe8")
def aura_mending(d: Doc):
    cx, cy = 64, 66
    d.glow(cx, cy, 46, HEAL["glow"], 0.45)
    with d.g(T(cx, cy + 10, 0, 0.92)):
        chalice(d, pal=dict(dark="#6a7488", base="#d8e0ec", light="#ffffff"), wine=HEAL)
    heart(d, cx, cy - 30, 0.42, dict(dark="#0e5a30", base="#46d888", light="#e0ffe8"), ow=2)
    for (x, y, s) in ((34, 40, 4), (96, 46, 3.4), (40, 92, 3), (92, 90, 3.6)):
        d.path(poly([(x - s * 0.35, y - s), (x + s * 0.35, y - s), (x + s * 0.35, y - s * 0.35), (x + s, y - s * 0.35), (x + s, y + s * 0.35),
                     (x + s * 0.35, y + s * 0.35), (x + s * 0.35, y + s), (x - s * 0.35, y + s), (x - s * 0.35, y + s * 0.35), (x - s, y + s * 0.35),
                     (x - s, y - s * 0.35), (x - s * 0.35, y - s * 0.35)]), fill="#d8ffe8", stroke=OUTLINE, stroke_width=0.8)


@aura("def", "#c8dcff", "#101828", haze="#6a8ac0", haze2="#e8f0ff")
def aura_defiance(d: Doc):
    d.glow(64, 64, 50, "#c8dcff", 0.45)
    with d.g(T(64, 66, 0, 1.0)):
        tower_shield(d, w=56, h=84, face=dict(dark="#3a4458", base="#b4c0d4", light="#ffffff"), band=dict(dark="#3a4a6a", base="#8aa4d0", light="#e8f0ff"))
        d.shape(poly(star_pts(0, -3, 4, 13, 3.4)), fill="#ffffff", ow=1.4)


@aura("def", "#8ad860", "#0e1a0a", haze="#4a8a2a", haze2="#a0182a")
def aura_thorns(d: Doc):
    with d.g(T(64, 64, 0, 1.18)):
        heater_shield(d, w=60, h=72, field=dict(dark="#1a2a14", base="#3a5a2a", light="#7a9a5a"), rim=dict(dark="#3a4250", base="#aab4c4", light="#ffffff"), emblem=None)
    rng = random.Random(8)
    vine_col = dict(dark="#1a3a0e", base="#4a7a2a", light="#9ad06a")
    for pts in (((30, 100), (44, 76), (40, 52), (56, 34), (80, 30)), ((98, 100), (82, 82), (90, 60), (74, 44), (60, 58), (66, 80))):
        sp = smooth_pts(list(pts), 30)
        d.path(ribbon(sp, [5] * 30), stroke=OUTLINE, stroke_width=1.8)
        d.path(ribbon(sp, [5] * 30), fill=d.lin([(0, vine_col["light"]), (1, vine_col["dark"])], 0, 30, 0, 100))
        for i in range(3, 28, 4):
            x, y = sp[i]
            px, py = sp[i - 1]
            a = math.atan2(y - py, x - px) + (math.pi / 2 if i % 8 == 3 else -math.pi / 2)
            tip = polar(x, y, 8, a)
            th = [polar(x, y, 2.4, a + math.pi / 2), tip, polar(x, y, 2.4, a - math.pi / 2)]
            d.shape(poly(th), fill="#e8d8b0", ow=1.0)
    for (x, y) in ((54, 70), (72, 52)):
        d.circle(x, y, 3.4, fill=CRIMSON["base"], stroke=OUTLINE, stroke_width=1.2)


@aura("def", "#7ab8ff", "#0a1430", haze="#3a6ae8", haze2="#a8d8ff")
def aura_clarity(d: Doc):
    cx, cy = 64, 66
    d.glow(cx, cy, 44, MANA["glow"], 0.5)
    eye(d, cx, cy + 6, 34, 13, dict(dark="#0a2a6a", base="#3a8aff", light="#d8f0ff"), white="#eaf4ff", ow=2.4)
    # third-eye brow rays
    for i in range(7):
        a = math.radians(-160 + i * 23.3)
        p0, p1 = polar(cx, cy + 6, 26, a), polar(cx, cy + 6, 36, a)
        d.path(ribbon([p0, p1], [4, 0.6]), fill="#d8f0ff", op=0.8)
    droplet(d, cx, cy - 30, 8, MANA)


# ================================================================================================ KNIGHT passives

@passive("knight", "#2a1a0c", haze="#8a5a20")
def arms_mastery(d: Doc):
    with d.g(T(84, 42, 38, 1.05)):
        axe(d, H=84, pal=BRIGHT_STEEL)
    with d.g(T(90, 100, -40, 1.05)):
        sword(d, L=74, W=13, pal=BRIGHT_STEEL, hilt=GOLD)


@passive("knight", "#1a1a24", haze="#5a6070")
def shield_mastery(d: Doc):
    with d.g(T(64, 64, 0, 1.3)):
        heater_shield(d, w=64, h=76, field=dict(dark="#101a2a", base="#2a4a7a", light="#6a9ad0"), rim=STEEL, emblem=None)
    d.glow(64, 62, 22, "#ffe08a", 0.5)
    d.shape(poly(star_pts(64, 62, 5, 20, 8.5)), fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], 64, 42, 64, 82), ow=2)


@passive("knight", "#1c1e24", haze="#6a7080")
def iron_skin(d: Doc):
    with d.g(T(64, 66, 0, 1.25)):
        cuirass(d, w=64, h=66, pal=dict(dark="#2a2e36", base="#7a828e", light="#dce2ea"), trim=BRONZE)
        for (x, y) in ((-14, -14), (14, -14), (-12, 4), (12, 4), (-10, 20), (10, 20), (0, -24)):
            d.circle(x, y, 2.2, fill=d.rad([(0, "#ffffff"), (1, "#5a606a")], x - 0.6, y - 0.6, 2.6), stroke=OUTLINE, stroke_width=0.8)


@passive("knight", "#1a1420", haze="#6a5a80")
def oathbound(d: Doc):
    pts = [(64 + x * 1.25, 66 + y * 1.25) for x, y in heater_pts(64, 76)]
    sd = smooth(pts, tension=0.55)
    d.path(sd, stroke=OUTLINE, sw=6)
    d.path(sd, fill=STEEL["base"])
    quads = ((FIRE, [(64, 66), (20, 66), (20, 20), (64, 20)]), (ICE, [(64, 66), (64, 20), (108, 20), (108, 66)]),
             (LIGHTNING, [(64, 66), (108, 66), (108, 124), (64, 124)]), (VENOM, [(64, 66), (64, 124), (20, 124), (20, 66)]))
    inner = [(64 + x * 1.08, 65 + y * 1.08) for x, y in heater_pts(64, 76)]
    # quarters: draw each colour, then mask outside the shield by re-stroking the rim thick
    for pal, q in quads:
        cx_ = sum(p[0] for p in q) / 4
        cy_ = sum(p[1] for p in q) / 4
        d.path(poly(q), fill=d.rad([(0, pal["light"]), (0.6, pal["base"]), (1, pal["dark"])], cx_, cy_, 40), op=0.95)
    # knock out the quarters beyond the shield outline with the backdrop colour ring
    d.path("M0,0 L128,0 L128,128 L0,128 Z " + smooth(pts, tension=0.55), fill="#0d0a12", fill_rule="evenodd")
    d.path(sd, stroke=OUTLINE, sw=6)
    d.path(sd, stroke=d.lin([(0, "#ffffff"), (0.5, STEEL["base"]), (1, STEEL["dark"])], 20, 20, 108, 120), sw=4)
    d.path(smooth(inner, tension=0.55), stroke=OUTLINE, sw=1.2, op=0.6)
    d.path("M64,24 L64,122 M24,66 L104,66", stroke=OUTLINE, sw=3.4)
    d.path("M64,24 L64,122 M24,66 L104,66", stroke=GOLD["base"], sw=1.6)
    d.circle(64, 66, 7, fill=d.rad([(0, GOLD["light"]), (1, GOLD["dark"])], 62, 64, 8), stroke=OUTLINE, stroke_width=1.6)


@passive("knight", "#2a0a0e", haze="#a0182a")
def toughness(d: Doc):
    heart(d, 64, 62, 1.25, dict(dark="#3a0408", base="#c0141e", light="#ff8a8a"))
    band = [(24, 58), (104, 58), (106, 72), (22, 72)]
    d.shape(poly(band), fill=d.lin([(0, "#e8eef4"), (0.5, "#8a94a0"), (1, "#2a3038")], 0, 58, 0, 72), ow=2.2)
    for x in (32, 48, 64, 80, 96):
        d.circle(x, 65, 2.2, fill=d.rad([(0, "#ffffff"), (1, "#4a525c")], x - 0.6, 64.4, 2.6), stroke=OUTLINE, stroke_width=0.8)


@passive("knight", "#0e2224", haze="#4ab0a0")
def second_wind(d: Doc):
    heart(d, 64, 66, 0.9, dict(dark="#3a0408", base="#d02a34", light="#ff9a9a"))
    pal = EL["wind"]
    for i in range(3):
        swirl(d, 64, 66, 20, 50, i * 2 * math.pi / 3 + 0.4, 0.5, 8, pal["base"], n=34)
        swirl(d, 64, 66, 20, 50, i * 2 * math.pi / 3 + 0.4, 0.5, 3, pal["light"], n=34, outline=False)


@passive("knight", "#241418", haze="#a0182a")
def retaliation(d: Doc):
    with d.g(T(54, 70, -8, 1.12)):
        heater_shield(d, w=62, h=74, field=CRIMSON, rim=STEEL, emblem="boss", boss=GOLD)
    # incoming strike deflected back as a counter arrow
    impact_star(d, 86, 44, 16, "#ffffff", "#ffc040", n=8, inner=0.3)
    arc = qbez((86, 44), (112, 60), (100, 96), n=18)
    d.path(ribbon(arc, taper(18, 7, 0.4, 1.0, peak=1.0)), stroke=OUTLINE, stroke_width=1.6)
    d.path(ribbon(arc, taper(18, 7, 0.4, 1.0, peak=1.0)), fill="#ffd070")
    tip = arc[-1]
    d.shape(poly([(tip[0] - 9, tip[1] - 6), (tip[0] + 8, tip[1] - 6), (tip[0] - 2, tip[1] + 10)]), fill="#ffd070", ow=1.6)


@passive("knight", "#2a1a08", haze="#c8962e")
def crusader_resolve(d: Doc):
    with d.g(T(64, 66, 0, 1.12)):
        banner(d, field=dict(dark="#e0d8c8", base="#f4eee0", light="#ffffff"), trim=GOLD, emblem=False)
    sun(d, 64, 56, 9, EL["light"], rays=12, ray_len=1.8, glow=False)


# ================================================================================================ MAGE actives

@active("mage", mix(MAGE_BG, "#0a3a5a", 0.6), haze="#6ad8ff", haze2="#3a2a8a")
def blizzard(d: Doc):
    cloud(d, [(24, 30, 17), (50, 22, 20), (80, 20, 21), (106, 28, 17), (40, 40, 14), (66, 38, 16), (92, 40, 13)], top="#e8f4ff", bottom="#3a5a8a")
    rng = random.Random(4)
    for i in range(9):
        x = 18 + i * 11.5 + rng.uniform(-3, 3)
        y = 70 + rng.uniform(-10, 34)
        L = rng.uniform(14, 24)
        d.path(ribbon([(x + 10, y - 26), (x, y)], [0.5, 3]), fill="#dff6ff", op=0.35)
        with d.g(T(x, y, 200, 1.0)):
            ice_shard(d, L=L, W=L * 0.4, pal=ICE, ow=1.6)
    for (x, y, s) in ((30, 58, 3), (96, 64, 3.4), (64, 110, 2.6), (82, 98, 2.4)):
        d.sparkle(x, y, s, "#ffffff", 0.9)


@active("mage", mix(MAGE_BG, "#4a1408", 0.55), haze="#ff5a14", haze2="#ffb040")
def flame_sentinel(d: Doc):
    stone = dict(dark="#1a1418", base="#5a4a50", light="#a89aa0")
    d.glow_ellipse(64, 114, 40, 8, "#ff7a1a", 0.8)
    # carved stone pylon with an eye socket
    body = [(46, 116), (82, 116), (78, 60), (86, 52), (42, 52), (50, 60)]
    faceted(d, body, (58, 80), stone["dark"], stone["light"], ow=2.6, light_dir=(-0.6, -0.5))
    d.path("M52,76 L76,76 M50,96 L78,96", stroke=OUTLINE, sw=1.6, op=0.7)
    eye(d, 64, 86, 12, 5, dict(dark="#7a1206", base="#ff8a2a", light="#ffe08a"), white="#2a0a04", ow=1.8)
    d.glow(64, 86, 10, "#ff9a30", 0.7)
    # brazier bowl + flame
    d.shape(poly([(38, 52), (90, 52), (84, 44), (44, 44)]), fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], 0, 44, 0, 52), ow=2)
    flame(d, 64, 42, 0.6, FIRE)
    rng = random.Random(6)
    for i in range(6):
        x, y = rng.uniform(30, 98), rng.uniform(14, 40)
        d.circle(x, y, rng.uniform(1, 2.2), fill="#ffd070", opacity=0.9)


@active("mage", mix(MAGE_BG, "#0a2a5a", 0.6), haze="#6ad8ff", haze2="#8a5aff")
def frost_orb(d: Doc):
    cx, cy = 60, 62
    d.glow(cx, cy, 52, ICE["glow"], 0.6)
    # spikes
    for i in range(12):
        a = i * 30 + 15
        L = 18 if i % 2 == 0 else 12
        bx, by = polar(cx, cy, 17, math.radians(a - 90))
        with d.g(T(bx, by, a, 1.0)):
            ice_shard(d, L=L, W=8 if i % 2 == 0 else 6, pal=ICE, ow=1.6)
    d.circle(cx, cy, 19, fill=OUTLINE)
    d.circle(cx, cy, 17, fill=d.rad([(0, "#ffffff"), (0.4, "#bff0ff"), (0.85, "#3a9ac8"), (1, "#1f5a7a")], cx - 5, cy - 5, 20))
    snowflake(d, cx, cy, 9, ICE, width=2, glow=False)
    # shed shards flying outward
    for (x, y, a, L) in ((104, 30, 45, 14), (110, 76, 100, 12), (88, 108, 150, 13), (24, 104, 220, 11), (16, 40, 300, 12)):
        d.path(ribbon([polar(x, y, 14, math.radians(a + 90)), (x, y)], [0.4, 3]), fill="#dff6ff", op=0.5)
        with d.g(T(x, y, a, 1.0)):
            ice_shard(d, L=L, W=5, pal=ICE, ow=1.4)


# ================================================================================================ MAGE passives

def _rune_circle(d, color):
    d.glow(64, 64, 52, color, 0.35)
    rune_ring(d, 64, 64, 48, lt(color, 0.3), width=2.4, ticks=18, seed=6)


@passive("mage", mix(MAGE_BG, "#4a1408", 0.4), haze="#ff5a14")
def pyre_mastery(d: Doc):
    _rune_circle(d, "#ff8a3a")
    flame(d, 64, 86, 0.78, FIRE)


@passive("mage", mix(MAGE_BG, "#0a3a5a", 0.5), haze="#6ad8ff")
def frost_mastery(d: Doc):
    _rune_circle(d, "#8ae0ff")
    snowflake(d, 64, 64, 32, ICE, width=4.4)


@passive("mage", mix(MAGE_BG, "#2a1a5a", 0.4), haze="#b88aff")
def storm_mastery(d: Doc):
    _rune_circle(d, "#c8a0ff")
    zig_bolt(d, 64, 64, 66, LIGHTNING)


@passive("mage", mix(MAGE_BG, "#06304a", 0.5), haze="#30c4d4")
def tide_stone_mastery(d: Doc):
    with d.g(T(58, 60, 0, 0.72)):
        wave(d, EL["water"], s=1.0)
    rock(d, 84, 90, 20, EL["earth"], seed=7, n=8)
    rock(d, 50, 98, 11, EL["earth"], seed=3, n=7)


@passive("mage", mix(MAGE_BG, "#3a1008", 0.45), haze="#ff6a14")
def inner_fire(d: Doc):
    coal = dict(dark="#1a0604", base="#4a1408", light="#a0401a")
    d.glow(64, 66, 50, FIRE["glow"], 0.55)
    hp = heart(d, 64, 64, 1.2, coal)
    rng = random.Random(12)
    for (a, b) in (((64, 48), (56, 64)), ((56, 64), (62, 82)), ((62, 82), (64, 96)), ((56, 64), (40, 58)), ((64, 48), (80, 56)), ((80, 56), (74, 74)), ((74, 74), (88, 72))):
        cr = jag_line(a, b, 3, 2, rng)
        d.path(poly(cr, closed=False), stroke="#ff6a14", sw=3.4)
        d.path(poly(cr, closed=False), stroke="#ffe080", sw=1.3)
    d.glow(64, 70, 18, "#ffb040", 0.9)
    flame(d, 64, 80, 0.36, FIRE, glow=False)


@passive("mage", mix(MAGE_BG, "#0a1a5a", 0.5), haze="#3a8aff")
def mana_shield(d: Doc):
    cx, cy = 64, 64
    with d.g(T(cx, cy + 34, 0, 0.74)):
        humanoid_robed(d, fill=d.lin([(0, "#b0a0f0"), (0.5, "#6a5ab0"), (1, "#2a2060")], 0, -80, 0, 0))
    d.circle(cx, cy, 46, fill=d.rad([(0, "#3a8aff", 0.05), (0.75, "#3a8aff", 0.25), (0.95, "#a8d8ff", 0.6), (1, "#a8d8ff", 0)], cx, cy, 46))
    d.circle(cx, cy, 44, stroke="#c8e8ff", stroke_width=2.4, opacity=0.9)
    for k in range(-2, 3):
        for j in range(-2, 3):
            x = cx + k * 16 + (j % 2) * 8
            y = cy + j * 14
            if math.hypot(x - cx, y - cy) < 34:
                d.path(poly(ngon(x, y, 8, 6, rot0=0)), stroke="#a8d8ff", sw=1.0, op=0.35)
    d.path(smooth(arc_pts(cx, cy, 36, math.radians(200), math.radians(250), 6), closed=False), stroke="#ffffff", sw=3, op=0.7)


@passive("mage", mix(MAGE_BG, "#2a0e5a", 0.45), haze="#a060ff")
def spell_echo(d: Doc):
    for (cx, cy, op, s) in ((74, 54, 0.45, 0.8), (56, 72, 1.0, 1.0)):
        with d.g(T(cx, cy, 0, s), op=op):
            rune_ring(d, 0, 0, 36, "#d8c0ff", width=2.2, ticks=14, seed=4)
            tri1 = ngon(0, 0, 28, 3)
            tri2 = ngon(0, 0, 28, 3, rot0=math.pi / 2)
            d.path(poly(tri1) + " " + poly(tri2), stroke="#b890ff", sw=1.8)
            d.path(poly(star_pts(0, 0, 4, 12, 3)), fill="#ffffff", stroke=OUTLINE, stroke_width=1.2)
    for (x, y, s) in ((96, 88, 3), (30, 34, 3)):
        d.sparkle(x, y, s, "#ffffff", 0.9, glow_color="#a060ff")


@passive("mage", mix(MAGE_BG, "#1a1a4a", 0.4), haze="#8a8aff")
def arcane_precision(d: Doc):
    cx, cy = 64, 64
    d.glow(cx, cy, 44, "#a060ff", 0.45)
    d.circle(cx, cy, 34, stroke=OUTLINE, stroke_width=5)
    d.circle(cx, cy, 34, stroke="#c8a8ff", stroke_width=2.4)
    for i, a in enumerate((0, 90, 180, 270)):
        x, y = polar(cx, cy, 34, math.radians(a - 90))
        rune_glyph(d, x, y, 0.8, "#e8d8ff", sw=2.2, kind=i)
    for i, a in enumerate((0, 90, 180, 270)):
        p0, p1 = polar(cx, cy, 8, math.radians(a)), polar(cx, cy, 24, math.radians(a))
        d.path(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}", stroke=OUTLINE, sw=5)
        d.path(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}", stroke="#e8d8ff", sw=2.4)
    d.glow(cx, cy, 10, "#ffffff", 0.9)
    d.circle(cx, cy, 3, fill="#ffffff")


# ================================================================================================ RANGER actives

GLOW_GOLD = "#ffd070"


def _placed_arrow(d, x0, y0, deg, L, s=1.0, **kw):
    """Arrow with its nock at (x0, y0) flying along compass angle deg (0 = +x, -90 = up)."""
    with d.g(T(x0, y0, deg + 90, s)):
        arrow2(d, L=L, **kw)
    return polar(x0, y0, L * s, math.radians(deg))


@active("ranger", "#1e2a10", haze="#8ab040", haze2="#ffd070")
def power_shot(d: Doc):
    # heavy glowing arrow driving diagonally up-right, shock rings around the shaft
    for (w, col, op) in ((34, "#ffb040", 0.18), (20, "#ffd070", 0.3), (9, "#fff4c8", 0.7)):
        d.path(ribbon([(8, 120), (84, 44)], [w * 0.3, w]), fill=col, op=op)
    for t, r in ((0.3, 15), (0.52, 12)):
        x, y = lerp(18, 96, t), lerp(110, 32, t)
        with d.g(T(x, y, 45, 1.0)):
            d.ellipse(0, 0, r * 0.4, r, stroke=OUTLINE, stroke_width=3.6, opacity=0.5)
            d.ellipse(0, 0, r * 0.4, r, stroke="#fff4c8", stroke_width=2.0)
    _placed_arrow(d, 22, 106, -45, 64, 1.45, head=dict(dark="#6a4a14", base="#ffd070", light="#fffbe6"), fletch=FLETCH_GREEN,
                  head_scale=1.5, glow="#ffd070", shaft_w=2.6)
    impact_star(d, 100, 28, 14, "#ffffff", GLOW_GOLD, n=8, inner=0.3, rot0=0.4)


@active("ranger", "#16240e", haze="#6aa040", haze2="#c8b060")
def multishot(d: Doc):
    ox, oy = 20, 110
    d.glow(ox + 8, oy - 8, 24, "#fff0b0", 0.7)
    for i, a in enumerate((-82, -64, -45, -26, -8)):
        L = 82 if i == 2 else 70
        d.path(ribbon([polar(ox, oy, 10, math.radians(a)), polar(ox, oy, L * 0.85, math.radians(a))], [0.5, 5]), fill="#e8f0c0", op=0.22)
        L = L - 12
        _placed_arrow(d, *polar(ox, oy, 20, math.radians(a)), a, L, 1.0, head=BRIGHT_STEEL,
                      fletch=FLETCH_GREEN if i % 2 == 0 else FLETCH_WHITE, head_scale=1.2)


@active("ranger", "#0c2030", haze="#6ad8ff", haze2="#3a7a4a")
def frost_arrow(d: Doc):
    tr = qbez((10, 118), (40, 92), (80, 50), n=20)
    d.path(ribbon(tr, taper(20, 26, 0.1, 1.0, peak=1.0)), fill=ICE["glow"], op=0.22)
    d.path(ribbon(tr, taper(20, 10, 0.1, 1.0, peak=1.0)), fill="#eafcff", op=0.6)
    for (x, y, s) in ((30, 92, 3.5), (48, 84, 2.6), (40, 104, 2.4), (62, 70, 3)):
        d.sparkle(x, y, s, "#ffffff", 0.9)
    hx, hy = _placed_arrow(d, 22, 106, -45, 80, 1.15, head=ICE, fletch=FLETCH_GREEN, head_scale=1.3)
    d.glow(hx, hy, 24, ICE["glow"], 0.8)
    for a, L in ((-5, 20), (-85, 20), (-45, 28), (25, 13), (-115, 13)):
        with d.g(T(hx - 8, hy + 8, a + 90, 1.0)):
            ice_shard(d, L=L, W=8, pal=ICE, ow=1.5)
    d.sparkle(hx + 4, hy - 4, 6, "#ffffff", 1.0)


@active("ranger", "#2a1206", haze="#ff6a14", haze2="#6a8a2a")
def blast_arrow(d: Doc):
    _placed_arrow(d, 16, 112, -45, 70, 1.05, head=dict(dark="#4a2a10", base="#c8703a", light="#ffd8a0"), fletch=FLETCH_GREEN, head_scale=1.2)
    bx, by = 84, 44
    d.glow(bx, by, 46, FIRE["glow"], 0.85)
    impact_star(d, bx, by, 32, "#fff4c0", "#ff7a1a", n=12, inner=0.42)
    rng = random.Random(3)
    for i in range(10):
        a = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(22, 36)
        x, y = polar(bx, by, r0, a)
        d.path(ribbon([polar(bx, by, r0 - 9, a), (x, y)], [0.5, 3.2]), fill="#ffd070", op=0.9)
        rock(d, x, y, rng.uniform(1.8, 3.2), EL["earth"], seed=i, n=5, ow=1)
    d.circle(bx, by, 10, fill=d.rad([(0, "#ffffff"), (1, "#ffd070", 0)], bx, by, 10))


@active("ranger", "#101c28", haze="#6a8ab0", haze2="#8ab040")
def arrow_rain(d: Doc):
    d.path("M0,106 L128,102 L128,128 L0,128 Z", fill=d.lin([(0, "#2a3a1a"), (1, "#0a1206")], 0, 102, 0, 128))
    rng = random.Random(9)
    spots = [(22, 74), (38, 100), (56, 62), (70, 104), (88, 80), (104, 104), (112, 58)]
    for (x, y) in spots:
        tail = polar(x, y, 60, math.radians(-105))
        d.path(ribbon([tail, polar(x, y, 14, math.radians(-105))], [0.4, 3.2]), fill="#dfe8ff", op=0.3)
        nock = polar(x, y, 42, math.radians(-105))
        _placed_arrow(d, nock[0], nock[1], 75, 42, 1.0, head=BRIGHT_STEEL, fletch=FLETCH_GREEN, head_scale=1.25, ow=1.6)
    for (x, y) in ((70, 104), (38, 100), (104, 104)):
        d.ellipse(x, y + 2, 7, 2, fill="#000000", opacity=0.45)
    cloud(d, [(18, 12, 14), (44, 8, 16), (76, 6, 17), (106, 12, 14), (60, 16, 12), (30, 20, 10), (92, 20, 10)], top="#a8b0c8", bottom="#2a3048")


@active("ranger", "#1a1206", haze="#c8962e", haze2="#6a8a2a")
def deadeye(d: Doc):
    cx, cy = 64, 60
    d.glow(cx, cy, 50, "#ffd070", 0.35)
    crosshair(d, cx, cy, 40, color="#ff5a3a", sw=2.6, gap=0.62)
    eye(d, cx, cy, 25, 10.5, dict(dark="#5a3a0a", base="#e0a020", light="#fff0a0"), white="#f4ecd8", ow=2.4)
    d.circle(cx, cy, 2.4, fill="#ff3a2a")
    _placed_arrow(d, 14, 118, -40, 44, 1.0, head=BRIGHT_STEEL, fletch=FLETCH_GREEN, head_scale=1.2)


@active("ranger", "#141030", haze="#8a5aff", haze2="#ffe23a")
def storm_javelin(d: Doc):
    rng = random.Random(14)
    with d.g(T(20, 112, 45, 1.18)):
        d.glow_stroke("M0,0 L0,-100", LIGHTNING["glow"], 10, op=0.6)
        javelin(d, L=102, head=dict(dark="#6a5aa0", base="#fff0a0", light="#ffffff"))
    for (a, b) in (((36, 92), (14, 74)), ((54, 76), (74, 94)), ((72, 54), (52, 36)), ((92, 36), (114, 46)), ((90, 38), (98, 12))):
        bolt(d, jag_line(a, b, 4, 4, rng), width=3.4, pal=LIGHTNING, glow=False)
    hx, hy = polar(20, 112, 102 * 1.18, math.radians(-45))
    d.glow(hx, hy, 18, LIGHTNING["glow"], 0.9)
    d.sparkle(hx, hy, 8, "#ffffff", 1.0)


@active("ranger", "#1a1410", haze="#8a6a3a", haze2="#4a7a3a")
def snare_trap(d: Doc):
    d.path("M0,92 L128,88 L128,128 L0,128 Z", fill=d.lin([(0, "#3a2a14"), (1, "#0e0a04")], 0, 88, 0, 128))
    web(d, 64, 52, 46, color="#e8e4d8", spokes=10, rings=4, op=0.55, sw=1.2)
    with d.g(T(64, 82, 0, 1.0)):
        trap_jaws(d, w=76, pal=dict(dark="#2e343c", base="#9aa4b0", light="#f2f6fa"), open_=0.9, teeth=7)
    for i in range(4):
        x, y = 100 + i * 5, 98 + i * 4
        d.ellipse(x, y, 3.4, 2, stroke=OUTLINE, stroke_width=3)
        d.ellipse(x, y, 3.4, 2, stroke=STEEL["light"], stroke_width=1.2)
    d.shape(poly([(117, 110), (124, 110), (120.5, 124)]), fill=WOOD["base"], ow=1.4)


@active("ranger", "#1e1008", haze="#ff6a14", haze2="#4a5a2a")
def blast_trap(d: Doc):
    d.path("M0,96 L128,92 L128,128 L0,128 Z", fill=d.lin([(0, "#3a2a14"), (1, "#0e0a04")], 0, 92, 0, 128))
    d.glow_ellipse(64, 96, 50, 12, "#ff8a2a", 0.4)
    mine(d, 58, 74, 25)
    for (x, y) in ((22, 102), (102, 106), (40, 114)):
        rock(d, x, y, 4, EL["earth"], seed=int(x), n=6, ow=1.2)


@active("ranger", "#12220e", haze="#9ee0a6", haze2="#c8b060")
def vault(d: Doc):
    cx, cy = 62, 58
    # backward somersault arc: a big loop arrow sweeping up and back over the boots
    loop = arc_pts(cx, cy, 42, math.radians(30), math.radians(-250), 44)
    d.path(ribbon(loop, taper(44, 18, 0.05, 1.0, peak=0.9)), fill="#e8ffe0", op=0.2)
    d.path(ribbon(loop, taper(44, 8, 0.05, 1.0, peak=0.9)), stroke=OUTLINE, stroke_width=1.6)
    d.path(ribbon(loop, taper(44, 8, 0.05, 1.0, peak=0.9)), fill=d.lin([(0, "#6aa050"), (1, "#f0ffe0")], *loop[0], *loop[-1]))
    end, prev = loop[-1], loop[-3]
    ang = math.atan2(end[1] - prev[1], end[0] - prev[0])
    tip = polar(end[0], end[1], 11, ang)
    d.shape(poly([tip, polar(end[0], end[1], 8, ang + 1.9), polar(end[0], end[1], 8, ang - 1.9)]), fill="#f0ffe0", ow=1.6)
    # ground and dust kicked up by the take-off
    d.path("M0,112 L128,108 L128,128 L0,128 Z", fill=d.lin([(0, "#2a3a1a"), (1, "#0a1206")], 0, 108, 0, 128))
    smoke(d, [(80, 106, 8), (92, 108, 6), (70, 110, 5), (100, 104, 4)], top="#d8d0b0", bottom="#6a6048", op=0.85)
    # the pair of hunting boots in mid-air, tilted back
    for (x, y, a, op) in ((50, 84, -24, 0.35), (60, 80, -34, 1.0)):
        with d.g(T(x, y, a, 0.95), op=op):
            boot(d, pal=LEATHER, trim=BRONZE, cuff=FOREST)
    speed_lines(d, [(86, 70, 108, 78, 3), (84, 82, 110, 92, 3), (88, 58, 106, 62, 2)], "#e8ffe0", 0.5)


@active("ranger", "#260c08", haze="#c02a1a", haze2="#6a8a2a")
def hunters_mark(d: Doc):
    cx, cy = 64, 64
    bullseye(d, cx, cy, 38, a=dict(dark="#3a2a14", base="#7a5a34", light="#c8a070"), b=dict(dark="#6a5a40", base="#d8ccae", light="#fbf6e6"), rings=4)
    sig = dict(dark="#3a0408", base="#e02a2a", light="#ff9a8a")
    strokes = ["M64,94 L64,40", "M64,58 L48,44 L44,30", "M64,58 L80,44 L84,30", "M48,44 L38,46", "M80,44 L90,46", "M54,80 L64,72 L74,80"]
    dd = " ".join(strokes)
    d.glow(cx, cy, 30, "#ff3a2a", 0.6)
    d.path(dd, stroke=OUTLINE, sw=8)
    d.path(dd, stroke=sig["base"], sw=5)
    d.path(dd, stroke=sig["light"], sw=1.6, op=0.8)
    for a in (45, 135, 225, 315):
        p = polar(cx, cy, 47, math.radians(a))
        d.shape(poly([polar(p[0], p[1], 7, math.radians(a + 180)), polar(p[0], p[1], 5, math.radians(a + 90)), polar(p[0], p[1], 5, math.radians(a - 90))]), fill=sig["base"], ow=1.2)


# ================================================================================================ RANGER passives

@passive("ranger", "#1e1a0c", haze="#a08a3a")
def keen_eye(d: Doc):
    for (a, x, y) in ((-60, 30, 50), (-100, 64, 26), (-140, 98, 50)):
        with d.g(T(x, y, a + 90, 0.5)):
            feather(d, L=44, W=14, pal=dict(dark="#3a2410", base="#8a6030", light="#e8c890"))
    # hawk eye: sharp brow, golden iris, dark eye-stripe
    d.path("M26,62 Q64,30 104,60 L96,64 Q64,42 32,66 Z", fill="#2a1a0a", stroke=OUTLINE, stroke_width=1.6)
    eye(d, 66, 72, 30, 13, dict(dark="#6a3a04", base="#f0a818", light="#fff0a0"), white="#f4ecd8", ow=2.6)
    d.path("M44,82 Q52,100 46,112", stroke=OUTLINE, sw=6)
    d.path("M44,82 Q52,100 46,112", stroke="#2a1a0a", sw=3.4)


@passive("ranger", "#20120a", haze="#a0402a")
def deadly_aim(d: Doc):
    bullseye(d, 70, 60, 36)
    _placed_arrow(d, 18, 112, -45, 62, 1.0, head=BRIGHT_STEEL, fletch=FLETCH_GREEN, head_scale=1.3, shaft_w=2.4)
    impact_star(d, 70, 60, 12, "#ffffff", "#ffd070", n=8, inner=0.3)


@passive("ranger", "#142014", haze="#6aa060")
def light_feet(d: Doc):
    with d.g(T(58, 104, 0, 1.25)):
        boot(d, pal=dict(dark="#2a1a0c", base="#7a5030", light="#c89868"), trim=BRONZE, cuff=FOREST)
    with d.g(T(84, 84, 30, 1.0)):
        feather(d, L=62, W=18, pal=dict(dark="#6a7078", base="#e0e4ea", light="#ffffff"))


@passive("ranger", "#141a20", haze="#6a8ab0")
def piercing_arrows(d: Doc):
    for i, x in enumerate((36, 64, 92)):
        d.circle(x, 64, 15, stroke=OUTLINE, stroke_width=7)
        d.circle(x, 64, 15, stroke=d.lin([(0, "#e8d8b0"), (1, "#7a5a34")], x - 15, 49, x + 15, 79), stroke_width=4)
        d.circle(x, 64, 11, fill="#000000", opacity=0.35)
    _placed_arrow(d, 8, 64, 0, 110, 1.0, head=BRIGHT_STEEL, fletch=FLETCH_GREEN, head_scale=1.3, shaft_w=2.4)
    for x in (36, 64, 92):
        d.path(f"M{x},49 A15,15 0 0 1 {x + 15},64", stroke=OUTLINE, sw=7)
        d.path(f"M{x},49 A15,15 0 0 1 {x + 15},64", stroke="#e8d8b0", sw=4)


@passive("ranger", "#10200e", haze="#8ad07a")
def fleet_foot(d: Doc):
    with d.g(T(34, 64, 0, 0.8)):
        wing(d, dict(dark="#6a7078", base="#e0e4ea", light="#ffffff"))
    with d.g(T(56, 104, 0, 1.3)):
        boot(d, pal=dict(dark="#2a1a0c", base="#7a5030", light="#c89868"), trim=GOLD, cuff=FOREST)
    speed_lines(d, [(88, 70, 108, 70, 3), (92, 84, 112, 84, 3), (86, 96, 104, 96, 2)], "#e8ffe0", 0.6)


@passive("ranger", "#1c1408", haze="#c86a2a")
def survivalist(d: Doc):
    campfire(d, 64, 88, 1.0)
    for (x, y, a) in ((32, 44, -40), (96, 40, 40), (64, 26, 0)):
        with d.g(T(x, y + 16, a, 1.0)):
            leaf(d, L=26, W=12, pal=FOREST)


@passive("ranger", "#16160e", haze="#8a8a4a")
def patient_hunter(d: Doc):
    with d.g(T(80, 64, 0, 0.95)):
        bow(d, H=98, pal=WOOD, limb=6.5)
    hourglass(d, 54, 64, 1.1, frame=BRONZE, sand=dict(dark="#3a5a1a", base="#8ab04a", light="#d8f0a0"))


@passive("ranger", "#18140c", haze="#8a6a3a")
def trapmaster(d: Doc):
    gear(d, 84, 40, 24, pal=BRONZE, teeth=10)
    with d.g(T(58, 80, 0, 0.9)):
        trap_jaws(d, w=70, pal=dict(dark="#2e343c", base="#9aa4b0", light="#f2f6fa"), open_=0.85, teeth=6)


# ================================================================================================ SHADOWBLADE actives

@active("shadowblade", "#1e0a2a", haze="#8a3ae0", haze2="#3a0a4a")
def twin_fang(d: Doc):
    for (a0, a1, cx, cy) in ((200, 290, 92, 90), (250, 340, 36, 90)):
        slash_arc(d, cx, cy, 58, math.radians(a0), math.radians(a1), 10, SLASH_VIOLET)
    with d.g(T(40, 98, 40, 1.05)):
        dagger2(d, L=58, W=11, glow="#c090ff")
    with d.g(T(88, 98, -40, 1.05)):
        dagger2(d, L=58, W=11, glow="#c090ff")
    impact_star(d, 64, 58, 14, "#ffffff", "#c070ff", n=8, inner=0.3)


@active("shadowblade", "#0e1a0a", haze="#5ad02a", haze2="#2a0a3a")
def venom_strike(d: Doc):
    with d.g(T(46, 34, 150, 1.12)):
        dagger2(d, L=58, W=12, pal=dict(dark="#1a3a14", base="#8ab89a", light="#e8fff0"), glow=VENOM["glow"])
    # venom coating dripping off the blade edge
    for (x, y, r, h) in ((72, 62, 3.4, 9), (80, 76, 4, 11), (64, 74, 2.6, 7)):
        d.path(teardrop(x, y, r, h), fill=d.rad([(0, VENOM["light"]), (1, VENOM["base"])], x - 1, y - 1, r * 2), stroke=OUTLINE, stroke_width=1.2)
    for (x, y, r) in ((80, 96, 4.4), (72, 108, 3.2), (88, 112, 2.6)):
        d.path(teardrop(x, y, r, r * 2.4), fill=d.rad([(0, VENOM["light"]), (0.6, VENOM["base"]), (1, VENOM["dark"])], x - 1, y - 1, r * 2), stroke=OUTLINE, stroke_width=1.4)
    d.glow_ellipse(82, 118, 26, 5, VENOM["glow"], 0.7)
    d.ellipse(82, 118, 18, 3.4, fill=VENOM["base"], stroke=OUTLINE, stroke_width=1.2)
    motes(d, [(40, 90, 1), (100, 60, 0.8), (30, 70, 0.7)], VENOM["light"], glow_color=VENOM["glow"], size=2, diamonds=False)


@active("shadowblade", "#140a24", haze="#6a2ab0", haze2="#1a0a2a")
def shadow_step(d: Doc):
    # the shadow pool and the figure stepping out of it
    d.glow_ellipse(46, 104, 40, 12, "#8a3ae0", 0.8)
    d.ellipse(46, 104, 34, 9, fill=d.rad([(0, "#000000"), (0.7, "#14061e"), (1, "#3a1460")], 46, 104, 34), stroke="#b070ff", stroke_width=1.6)
    for i, (x, op) in enumerate(((40, 0.25), (54, 0.45))):
        with d.g(T(x, 104, 0, 0.92), op=op):
            hood_silhouette(d, "#6a3ab0", outline=False, lean=0.6)
    with d.g(T(76, 108, 0, 1.0)):
        hood_silhouette(d, d.lin([(0, "#3a2a50"), (0.5, "#1a1026"), (1, "#07040c")], -26, 0, 28, 0), lean=0.8)
        for ex in (-1.5, 5.5):
            d.glow(ex + 6, -64, 4.5, "#c070ff", 1.0)
            d.circle(ex + 6, -64, 1.2, fill="#ffffff")
    tendril_col = dict(dark="#1a0626", base="#5a2a8a", light="#c090ff")
    from bh_shapes import tendril
    tendril(d, [(30, 104), (26, 88), (34, 74)], 6, tendril_col)
    tendril(d, [(58, 106), (66, 92), (62, 80)], 5, tendril_col)


@active("shadowblade", "#160c24", haze="#8a4ae0", haze2="#b0b8d0")
def fan_of_knives(d: Doc):
    cx, cy = 64, 64
    d.glow(cx, cy, 30, "#b070ff", 0.7)
    for i in range(10):
        a = -90 + i * 36
        d.path(ribbon([polar(cx, cy, 10, math.radians(a)), polar(cx, cy, 34, math.radians(a))], [0.5, 4]), fill="#e2d4ff", op=0.4)
        x, y = polar(cx, cy, 30, math.radians(a))
        with d.g(T(x, y, a + 90, 1.0)):
            knife(d, L=26, W=7)
    d.circle(cx, cy, 7, fill=d.rad([(0, "#ffffff"), (1, "#8a3ae0")], cx - 1, cy - 1, 8), stroke=OUTLINE, stroke_width=1.6)


@active("shadowblade", "#240a10", haze="#b0141e", haze2="#6a2ab0")
def crippling_star(d: Doc):
    # spin arcs + blood trail
    for r in (40, 32):
        pts = arc_pts(58, 62, r, math.radians(120), math.radians(250), 20)
        d.path(ribbon(pts, taper(20, 4, 0.1, 0.9, peak=0.8)), fill="#e2d4ff", op=0.5)
    shuriken(d, 64, 60, 34, pal=BRIGHT_STEEL, n=4, rot0=0.3)
    for (x, y, r) in ((92, 84, 4), (100, 96, 3), (86, 104, 3.6), (106, 76, 2.4)):
        d.path(teardrop(x, y, r, r * 2.2), fill=d.rad([(0, BLOOD["light"]), (1, BLOOD["dark"])], x - 1, y - 1, r * 2), stroke=OUTLINE, stroke_width=1.2)
    for (x, y) in ((74, 46), (50, 74)):
        d.path(teardrop(x, y, 2.4, 5, lean=2), fill=BLOOD["base"], stroke=OUTLINE, stroke_width=0.8)


@active("shadowblade", "#2a0610", haze="#c0141e", haze2="#6a2ab0")
def eviscerate(d: Doc):
    for (p0, p1) in (((18, 16), (106, 88)), ((108, 18), (22, 90))):
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        pts = qbez(p0, (mid[0] + 4, mid[1] - 6), p1, n=22)
        d.path(ribbon(pts, taper(22, 30, 0.0, 0.0, peak=0.5)), fill="#ff2030", op=0.25)
        d.path(ribbon(pts, taper(22, 14, 0.0, 0.0, peak=0.5)), stroke=OUTLINE, stroke_width=1.6)
        d.path(ribbon(pts, taper(22, 14, 0.0, 0.0, peak=0.5)), fill=d.lin([(0, "#6a0a18"), (0.5, "#ff6a6a"), (1, "#6a0a18")], *p0, *p1))
        d.path(ribbon(pts, taper(22, 5, 0.0, 0.0, peak=0.5)), fill="#ffffff")
    rng = random.Random(5)
    for i in range(7):
        x, y = 64 + rng.uniform(-24, 24), 52 + rng.uniform(-20, 20)
        d.path(teardrop(x, y, 2.2, 5, lean=rng.uniform(-3, 3)), fill=BLOOD["light"], stroke=OUTLINE, stroke_width=0.8)
    pips(d, [(32 + i * 16, 108) for i in range(5)], lit=5, color=VIOLET, r=5.2)


@active("shadowblade", "#1a0826", haze="#b060ff", haze2="#c0141e")
def death_blossom(d: Doc):
    cx, cy = 64, 64
    d.glow(cx, cy, 54, "#a050ff", 0.5)
    for i in range(3):
        swirl(d, cx, cy, 8, 50, i * 2 * math.pi / 3, 0.45, 5, "#d8c0ff", n=30, outline=False, op=0.5)
    # curved petal blades
    for i in range(6):
        a = i * 60
        with d.g(T(cx, cy, a, 1.0)):
            pts = [(0, -8), (10, -20), (12, -36), (4, -48), (-2, -40), (-4, -24)]
            dd = smooth(pts, tension=0.6)
            d.path(dd, stroke=OUTLINE, sw=4)
            d.path(dd, fill=d.lin([(0, "#ffffff"), (0.5, "#c8c0dc"), (1, "#4a4260")], -4, -8, 12, -48))
            d.path(smooth([(8, -20), (10, -36), (4, -46)], closed=False), stroke="#ffffff", sw=1.0, op=0.8)
    d.circle(cx, cy, 11, fill=OUTLINE)
    d.circle(cx, cy, 9, fill=d.rad([(0, "#ffb0c0"), (0.6, BLOOD["base"]), (1, BLOOD["dark"])], cx - 2, cy - 2, 10))
    d.circle(cx - 2.4, cy - 2.4, 2, fill="#ffffff", opacity=0.8)


@active("shadowblade", "#12101a", haze="#6a6a8a", haze2="#6a2ab0")
def smoke_veil(d: Doc):
    smoke(d, [(30, 84, 20), (56, 70, 26), (86, 76, 24), (104, 92, 16), (44, 100, 18), (74, 100, 20), (60, 44, 16), (86, 50, 14), (36, 56, 12)],
          top="#a8a2bc", bottom="#2a2438")
    # the hidden eye peering from the smoke
    d.glow(64, 74, 22, "#b060ff", 0.9)
    d.path("M40,74 Q64,58 88,74 Q64,86 40,74 Z", fill="#07030c", stroke=OUTLINE, stroke_width=2)
    d.circle(64, 74, 6.5, fill=d.rad([(0, "#ffffff"), (0.4, "#d8a0ff"), (1, "#6a1aa0")], 64, 74, 7))
    d.ellipse(64, 74, 1.6, 5, fill="#07030c")
    smoke(d, [(24, 108, 12), (104, 110, 12), (64, 114, 12)], top="#6a6480", bottom="#1a1624", op=0.9)


@active("shadowblade", "#16101e", haze="#8a4ae0", haze2="#8a8aa0")
def blade_sentinel(d: Doc):
    cx, cy = 64, 56
    # tripod post
    for (x, y) in ((44, 112), (84, 112), (64, 116)):
        d.path(f"M{cx},{cy + 10} L{x},{y}", stroke=OUTLINE, sw=6)
        d.path(f"M{cx},{cy + 10} L{x},{y}", stroke=DARK_STEEL["base"], sw=3)
    d.glow(cx, cy, 44, "#b070ff", 0.55)
    for r, a0 in ((44, 200), (44, 20), (36, 290), (36, 110)):
        pts = arc_pts(cx, cy, r, math.radians(a0), math.radians(a0 + 70), 16)
        d.path(ribbon(pts, taper(16, 4, 0.1, 1.0, peak=0.9)), fill="#e2d4ff", op=0.7)
    saw_blade(d, cx, cy, 30, pal=BRIGHT_STEEL, teeth=12, rot0=0.2)
    d.circle(cx, cy, 4.6, fill=d.rad([(0, "#ffffff"), (1, "#8a3ae0")], cx - 1, cy - 1, 5), stroke=OUTLINE, stroke_width=1.2)


@active("shadowblade", "#12081e", haze="#6a1a8a", haze2="#2a0a3a")
def dread_mark(d: Doc):
    cx, cy = 64, 64
    d.glow(cx, cy, 58, "#9a3ae0", 0.6)
    rune_ring(d, cx, cy, 46, "#c890ff", width=2.4, ticks=16, seed=13)
    tri1 = ngon(cx, cy, 44, 3, rot0=math.pi / 2)
    d.path(poly(tri1), stroke="#b070ff", sw=1.8, op=0.8)
    skull(d, cx, cy + 4, 1.05, pal=dict(dark="#3a3050", base="#b8b0cc", light="#f4f0ff"), eye_glow="#c060ff")


@active("shadowblade", "#140c1e", haze="#6a4ab0", haze2="#b0b8d0")
def quickstep(d: Doc):
    d.path("M0,108 L128,106 L128,128 L0,128 Z", fill=d.lin([(0, "#1a1426"), (1, "#05030a")], 0, 106, 0, 128))
    speed_lines(d, [(6, 58, 58, 60, 3), (10, 72, 50, 72, 4), (4, 86, 38, 86, 3), (18, 46, 60, 48, 2)], "#e2d4ff", 0.5)
    ghost = dict(dark="#2a0a4a", base="#8a3ae0", light="#e2c4ff")
    for (x, y, op) in ((30, 98, 0.22), (46, 98, 0.4)):
        with d.g(T(x, y, 6, 0.95), op=op):
            boot(d, pal=ghost, trim=ghost, cuff=ghost)
    with d.g(T(64, 100, 6, 1.0)):
        boot(d, pal=dict(dark="#120c1c", base="#4a3a66", light="#9a88c0"), trim=DARK_STEEL, cuff=VIOLET)
    d.glow(98, 104, 14, "#b070ff", 0.6)
    smoke(d, [(100, 104, 6), (110, 106, 4.5)], top="#8a80a8", bottom="#2a2438", op=0.8)


# ================================================================================================ SHADOWBLADE passives

@passive("shadowblade", "#16101e", haze="#6a4ab0")
def blade_mastery(d: Doc):
    with d.g(T(84, 94, 30, 1.0)):
        claw(d, L=50)
    with d.g(T(44, 100, -26, 1.12)):
        dagger2(d, L=58, W=11)


@passive("shadowblade", "#240810", haze="#c0141e")
def lethality(d: Doc):
    heart(d, 58, 72, 0.95, dict(dark="#3a0408", base="#b0141e", light="#ff8a8a"))
    with d.g(T(34, 108, 45, 1.0)):
        dagger2(d, L=70, W=10)
    impact_star(d, 92, 34, 16, "#ffffff", "#ff4a5a", n=10, inner=0.28)


@passive("shadowblade", "#120c1e", haze="#6a4ab0")
def evasion(d: Doc):
    for (x, op) in ((34, 0.3), (50, 0.5)):
        with d.g(T(x, 112, 0, 0.95), op=op):
            hood_silhouette(d, "#b89aff", outline=False, lean=-0.8)
    with d.g(T(76, 112, 0, 1.0)):
        hood_silhouette(d, d.lin([(0, "#7a68a0"), (0.5, "#3a2e52"), (1, "#0a0612")], -26, 0, 28, 0), lean=-0.8)
    # a blade passing harmlessly through the afterimage
    d.path(ribbon([(6, 48), (74, 60)], [0.5, 7]), fill="#ffffff", op=0.9)
    d.path(ribbon([(6, 48), (74, 60)], [0.5, 16]), fill="#e2d4ff", op=0.25)


@passive("shadowblade", "#0e1a0a", haze="#5ad02a")
def venomcraft(d: Doc):
    with d.g(T(64, 70, 0, 1.2)):
        vial(d, liquid=VENOM)
    for sx in (-1, 1):
        with d.g(T(64 + sx * 34, 36, -sx * 20, 1.1)):
            fang(d, L=34, W=11)
    d.path(teardrop(64, 110, 3, 7), fill=VENOM["base"], stroke=OUTLINE, stroke_width=1.2)


@passive("shadowblade", "#1a0c14", haze="#8a1a2a")
def ruthless(d: Doc):
    cracked_skull(d, 64, 74, 1.2, pal=dict(dark="#5a5040", base="#d8ccae", light="#fbf6e6"))
    with d.g(T(64, 60, 180, 1.05)):
        dagger2(d, L=60, W=11)


@passive("shadowblade", "#100a1e", haze="#6a2ab0")
def shadow_discipline(d: Doc):
    from icons_talents import crescent
    crescent(d, 58, 60, 40, 16, dict(dark="#2a0a4a", base="#6a4ab0", light="#c8b0ff", glow="#8a4ae0"))
    pts = [polar(58, 60, 50, math.radians(a)) for a in (-60, -30, 0, 30, 60)]
    pips(d, pts, lit=5, color=VIOLET, r=5.6)


@passive("shadowblade", "#160c1a", haze="#8a3ae0")
def opportunist(d: Doc):
    hood = dict(dark="#07040c", base="#2a2238", light="#6a5a8a")
    with d.g(T(54, 118, 0, 1.1)):
        hood_silhouette(d, d.lin([(0, "#8a78b0"), (0.5, "#3a2e52"), (1, "#0a0612")], -26, -80, 28, 0), lean=0.2)
    d.glow(58, 38, 22, "#b060ff", 0.8)
    eye(d, 58, 38, 22, 8.5, dict(dark="#2a0a4a", base="#b060ff", light="#ffe0ff"), white="#1a0a24", ow=2.0)
    with d.g(T(104, 104, -40, 1.0)):
        dagger2(d, L=56, W=11, glow="#c090ff")


@passive("shadowblade", "#100a1a", haze="#5a2a8a")
def fleet_step(d: Doc):
    prints = [(34, 104, -8, 0.3), (58, 90, 12, 0.45), (48, 66, -8, 0.65), (74, 52, 12, 0.85), (64, 28, -6, 1.0)]
    for (x, y, a, op) in prints:
        d.glow(x, y, 14, "#9a4ae0", 0.5 * op)
        footprint(d, x, y, 1.0, a, fill="#d8b8ff", op=op, rim=OUTLINE)
    smoke(d, [(26, 112, 8), (40, 114, 6)], top="#6a6480", bottom="#1a1624", op=0.7)
