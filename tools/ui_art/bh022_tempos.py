"""bh-022 UI art: portraits of the Mythic (level 25+) and Eternal (level 45+) renowned spirits.

Same painted style and helpers as bh005_tempos.py (ghost skin, spectral light, portrait frame); the frame's metal tells
the tier: Mythic = ember-gold, Eternal = moon-silver with a violet gem.

Writes game/assets/ui/portraits/tempo_<who>.svg (256x256).
Usage:  python tools/ui_art/bh022_tempos.py
"""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from bh_svg import Doc, OUTLINE, GOLD, EL, poly, smooth, mix  # noqa: E402
from bh_shapes import T, sword, dagger, bow, staff, tower_shield, flame, snowflake, zig_bolt, sun, ice_shard  # noqa: E402
import portraits as P  # noqa: E402
from bh005_tempos import ghost_skin, ghost_face, spectral, UI, ROOT, write  # noqa: E402

MYTHIC_METAL = dict(dark="#4a1a10", base="#d0703a", light="#ffe0b0")
ETERNAL_METAL = dict(dark="#2a2440", base="#a8a0d0", light="#f4f0ff")

PORTRAITS = {}


def portrait(fn):
    def build():
        d = Doc(P.S, P.S, name="pt22_" + fn.__name__)
        fn(d)
        return d
    PORTRAITS["tempo_" + fn.__name__] = build
    return fn


def fill_path(d, path, pal, x0, y0, x1, y1, sw=4):
    d.path(path, stroke=OUTLINE, sw=sw)
    d.path(path, fill=d.lin([(0, pal["light"]), (0.45, pal["base"]), (1, pal["dark"])], x0, y0, x1, y1))


def hair_back(d, cx, cy, col, length=40, width=48):
    back = smooth([(cx - width, cy + length), (cx - width - 6, cy - 30), (cx - 30, cy - 70), (cx + 10, cy - 78), (cx + width, cy - 58),
                   (cx + width + 6, cy - 10), (cx + width, cy + length)], tension=0.45)
    d.path(back, fill=col, stroke=OUTLINE, stroke_width=4)


def fringe(d, cx, cy, col, streak):
    fr = smooth([(cx - 42, cy - 16), (cx - 34, cy - 56), (cx + 4, cy - 70), (cx + 44, cy - 50), (cx + 42, cy - 22), (cx + 12, cy - 44), (cx - 18, cy - 36)], tension=0.45)
    d.path(fr, fill=col, stroke=OUTLINE, stroke_width=3)
    for k in range(4):
        d.path(smooth([(cx - 30 + k * 16, cy - 58), (cx - 18 + k * 16, cy - 44), (cx - 22 + k * 16, cy - 30)], closed=False), stroke=streak, sw=1.4)


def hood(d, cx, cy, pal, inner):
    h = smooth([(cx - 70, cy + 84), (cx - 70, cy - 10), (cx - 50, cy - 70), (cx, cy - 88), (cx + 50, cy - 70), (cx + 70, cy - 10), (cx + 70, cy + 84)], tension=0.45)
    fill_path(d, h, pal, cx - 70, cy - 88, cx + 70, cy + 84, sw=5)
    return smooth([(cx - 52, cy - 6), (cx - 40, cy - 60), (cx, cy - 72), (cx + 40, cy - 60), (cx + 52, cy - 6), (cx + 42, cy - 36), (cx, cy - 52), (cx - 42, cy - 36)], tension=0.45)


def beard(d, cx, cy, top="#f4f8f8", bottom="#7a8a90", length=100):
    b = smooth([(cx - 38, cy + 6), (cx - 42, cy + 44), (cx - 26, cy + length * 0.84), (cx, cy + length), (cx + 26, cy + length * 0.84), (cx + 42, cy + 44), (cx + 38, cy + 6),
                (cx + 20, cy + 30), (cx, cy + 34), (cx - 20, cy + 30)], tension=0.45)
    d.path(b, stroke=OUTLINE, sw=4)
    d.path(b, fill=d.lin([(0, top), (0.6, mix(top, bottom, 0.5)), (1, bottom)], cx, cy + 6, cx, cy + length))
    for k in range(7):
        x = cx - 24 + k * 8
        d.path(smooth([(x, cy + 40), (x + 2, cy + 66), (x - 1, cy + length * 0.88)], closed=False), stroke=bottom, sw=1.2, op=0.7)
    d.path(f"M{cx - 20},{cy + 26} Q{cx},{cy + 20} {cx + 20},{cy + 26}", stroke=top, sw=5)


def great_helm(d, cx, cy, pal, trim, crest=None):
    helm = smooth([(cx - 46, cy - 16), (cx - 44, cy - 56), (cx - 22, cy - 78), (cx + 22, cy - 78), (cx + 44, cy - 56), (cx + 46, cy - 16)], closed=False, tension=0.5) + " Z"
    fill_path(d, helm, pal, cx - 46, 0, cx + 46, 0, sw=5)
    d.path(f"M{cx - 47},{cy - 22} L{cx + 47},{cy - 22}", stroke=trim, sw=6)
    d.path(f"M{cx},{cy - 78} L{cx},{cy - 22}", stroke=pal["light"], sw=3, op=0.7)
    for sx in (-1, 1):
        d.circle(cx + sx * 34, cy - 22, 2.6, fill=pal["light"], stroke=OUTLINE, stroke_width=0.8)
    if crest == "horns":
        for sx in (-1, 1):
            horn = smooth([(cx + sx * 36, cy - 50), (cx + sx * 66, cy - 66), (cx + sx * 80, cy - 100), (cx + sx * 70, cy - 104), (cx + sx * 58, cy - 76), (cx + sx * 40, cy - 64)], tension=0.4)
            fill_path(d, horn, dict(dark="#3a2a1a", base="#a08a6a", light="#f0e4c8"), cx, cy - 104, cx + sx * 80, cy - 50, sw=3)


def crown(d, cx, cy, metal, gem, points=5, h=26, y=-58):
    base_y = cy + y
    pts = [(cx - 44, base_y + 10)]
    for k in range(points * 2 + 1):
        x = cx - 44 + k * 88 / (points * 2)
        pts.append((x, base_y - (h if k % 2 == 1 else 4)))
    pts.append((cx + 44, base_y + 10))
    d.shape(poly(pts), fill=d.lin([(0, metal["light"]), (1, metal["dark"])], cx, base_y - h, cx, base_y + 10), ow=2.4)
    for k in range(points):
        x = cx - 44 + (2 * k + 1) * 88 / (points * 2)
        d.circle(x, base_y - h + 3, 3.2, fill=gem, stroke=OUTLINE, stroke_width=1)
    d.circle(cx, base_y + 2, 5, fill=gem, stroke=OUTLINE, stroke_width=1.4)


def collar(d, cx, pal, top=176):
    for sx in (-1, 1):
        col = smooth([(cx + sx * 18, top), (cx + sx * 44, top - 16), (cx + sx * 56, top + 20), (cx + sx * 30, top + 28)], tension=0.4)
        fill_path(d, col, pal, cx, top - 16, cx + sx * 56, top + 28, sw=4)


# ---------------------------------------------------------------------------------------------------- Mythic

@portrait
def branthor(d):
    """Branthor Veyle, the Last Rampart: a grey-bearded warden in a gilded great helm, his tower shield behind him."""
    P.background(d, "#1a1410", haze="#d0703a", haze2="#6a7a8a", motes="#ffb070", seed=221)
    P.vignette(d)
    cx, cy = 132, 114
    skin = ghost_skin("#c8a080", 0.3)
    plate = dict(dark="#262e38", base="#7a8898", light="#e6f0fa")
    with d.g(T(62, 176, -10, 1.7)):
        tower_shield(d, w=56, h=84, face=dict(dark="#3a1a10", base="#8a3a22", light="#d88a5a"), band=GOLD)
    P.shoulders(d, plate, top=188, spread=1.1)
    for sx in (-1, 1):
        d.path(smooth([(cx + sx * 40, 194), (cx + sx * 86, 188), (cx + sx * 106, 212)], closed=False), stroke=GOLD["base"], sw=3.4)
    P.neck(d, cx, cy + 40, 30, 30, skin)
    ghost_face(d, cx, cy, skin, "#ffb070", brow="#d6dcde", smile=-0.6, w=1.08, jaw=1.12, age=2)
    beard(d, cx, cy, top="#e6ecee", bottom="#6a7478", length=92)
    great_helm(d, cx, cy, plate, GOLD["base"])
    spectral(d, "#ffb070", seed=31)
    P.frame(d, MYTHIC_METAL, gem_col="#ff7a4a")


@portrait
def ysmera(d):
    """Ysmera Coldbrand, the Frostblade: long frost-white hair, an ice circlet, a greatsword over her shoulder."""
    P.background(d, "#0a1622", haze="#8ae0ff", haze2="#ff7a4a", motes="#d8f6ff", seed=222)
    P.vignette(d)
    cx, cy = 126, 116
    skin = ghost_skin("#e6c0a4", 0.25)
    coat = dict(dark="#10243a", base="#3a6a90", light="#a8d8f0")
    with d.g(T(196, 150, 28, 1.5)):
        sword(d, L=110, W=16, pal=dict(dark="#2a4a68", base="#a8e0ff", light="#ffffff"), hilt=GOLD)
    hair_back(d, cx, cy, "#d8eef8", length=78, width=50)
    P.shoulders(d, coat, top=186, spread=0.98)
    collar(d, cx, coat)
    P.neck(d, cx, cy + 42, 24, 30, skin)
    ghost_face(d, cx, cy, skin, "#bff4ff", brow="#b8d0e0", smile=0.2, w=0.94, jaw=0.9, chin=0.86, lip="#8a7a98")
    fringe(d, cx, cy, "#e8f6fc", "#9ab8c8")
    for k in range(5):
        x = cx - 32 + k * 16
        with d.g(T(x, cy - 62, (k - 2) * 12, 0.5)):
            ice_shard(d, L=30 + (8 if k == 2 else 0), W=9, pal=EL["ice"])
    d.path(f"M{cx - 44},{cy - 50} Q{cx},{cy - 64} {cx + 44},{cy - 50}", stroke="#d8f6ff", sw=3)
    spectral(d, "#bff4ff", seed=32)
    P.frame(d, MYTHIC_METAL, gem_col="#8ae0ff")


@portrait
def aldevar(d):
    """Aldevar Quennt, the Starwarden: an old astronomer in a star-sewn hood, long white beard, a star-crowned staff."""
    P.background(d, "#0e0c22", haze="#8a7aff", haze2="#ffe08a", motes="#fff0c0", seed=223)
    P.vignette(d)
    cx, cy = 128, 114
    skin = ghost_skin("#e0bca0", 0.3)
    robe = dict(dark="#14123a", base="#3a3a8a", light="#9a9ae0")
    with d.g(T(210, 150, 8, 1.4)):
        staff(d, H=120, pal=EL["light"], thick=6.5, crystal_r=9)
    inner = hood(d, cx, cy, robe, robe)
    P.shoulders(d, robe, top=188, spread=1.0)
    P.neck(d, cx, cy + 40, 24, 30, skin)
    ghost_face(d, cx, cy, skin, "#fff0c0", brow="#e8e8f0", smile=0.4, w=0.92, jaw=0.94, age=2, ears=False)
    beard(d, cx, cy, top="#f8f8ff", bottom="#8a8ab0", length=104)
    d.path(inner, fill=robe["dark"], stroke=OUTLINE, stroke_width=3)
    for (x, y, r) in [(cx - 50, cy - 20, 4), (cx + 52, cy - 10, 3.4), (cx - 30, cy - 66, 3), (cx + 30, cy - 70, 3.6), (cx, cy - 82, 4.4), (cx - 62, cy + 30, 3), (cx + 60, cy + 40, 3.2)]:
        sun(d, x, y, r, pal=EL["light"], rays=4, ray_len=2.4)
    spectral(d, "#fff0c0", seed=33)
    P.frame(d, MYTHIC_METAL, gem_col="#fff0a0")


@portrait
def sabeline(d):
    """Sabeline Harrowgale, the Windpiercer: wind-tossed braids, a feathered mantle, a longbow drawn across her back."""
    P.background(d, "#0c1c14", haze="#9affb0", haze2="#d0703a", motes="#c8ffd8", seed=224)
    P.vignette(d)
    cx, cy = 124, 116
    skin = ghost_skin("#d8a47e", 0.3)
    mantle = dict(dark="#12281c", base="#3a6a4a", light="#9ad8a8")
    with d.g(T(184, 150, 24, 1.7)):
        bow(d, H=116, pal=dict(dark="#1a3a24", base="#6a9a6a", light="#d8f0c8"))
    hair_back(d, cx, cy, "#6a3a1a", length=30, width=46)
    P.shoulders(d, mantle, top=188, spread=1.0)
    for k in range(9):
        x = 50 + k * 19
        d.path(smooth([(x, 190), (x + 6, 214), (x + 2, 242)], closed=False), stroke=mantle["light"], sw=5, op=0.8)
        d.path(smooth([(x, 190), (x + 6, 214), (x + 2, 242)], closed=False), stroke=OUTLINE, sw=1.2, op=0.6)
    P.neck(d, cx, cy + 42, 24, 30, skin)
    ghost_face(d, cx, cy, skin, "#c8ffd8", brow="#4a2a14", smile=0.3, w=0.94, jaw=0.9, chin=0.86, lip="#8a4a3a")
    fringe(d, cx, cy, "#7a4424", "#a86a44")
    for sx, y0 in ((-1, 0), (1, 10)):
        for k in range(6):
            x, y = cx + sx * (46 + k * 3), cy + y0 + k * 14
            d.ellipse(x, y, 8, 7, fill="#7a4424", stroke=OUTLINE, stroke_width=2)
    for k in range(3):
        y = 60 + k * 36
        d.path(smooth([(20, y), (70, y - 14), (120, y + 4), (150, y - 8)], closed=False), stroke="#c8ffd8", sw=2.2, op=0.45)
    spectral(d, "#c8ffd8", seed=34)
    P.frame(d, MYTHIC_METAL, gem_col="#9affb0")


@portrait
def mireth(d):
    """Mireth Dusk, the Velvet Death: a wine-dark hood, a gauze veil over the mouth, two curved daggers crossed below."""
    P.background(d, "#16060e", haze="#c83a5a", haze2="#5a1a3a", motes="#ff9ab4", seed=225)
    P.vignette(d)
    cx, cy = 128, 114
    skin = ghost_skin("#d8a8b0", 0.3)
    cloak = dict(dark="#1a060e", base="#5a1a2e", light="#b85a74")
    inner = hood(d, cx, cy, cloak, cloak)
    P.shoulders(d, cloak, top=188, spread=1.02)
    P.neck(d, cx, cy + 40, 24, 30, skin)
    ghost_face(d, cx, cy, skin, "#ff9ab4", brow="#2a0a14", smile=0.0, w=0.92, jaw=0.9, chin=0.86, lip="#8a3a4a", ears=False)
    veil = smooth([(cx - 38, cy + 8), (cx + 38, cy + 8), (cx + 30, cy + 44), (cx, cy + 58), (cx - 30, cy + 44)], tension=0.35)
    d.path(veil, fill="#3a0a1a", op=0.82, stroke=OUTLINE, stroke_width=3)
    for k in range(4):
        d.path(f"M{cx - 30 + k * 4},{cy + 18 + k * 9} Q{cx},{cy + 24 + k * 9} {cx + 30 - k * 4},{cy + 18 + k * 9}", stroke="#8a3a54", sw=1.2)
    d.path(inner, fill=cloak["dark"], stroke=OUTLINE, stroke_width=3)
    for sx in (-1, 1):
        with d.g(T(cx + sx * 30, 232, sx * 50, 1.2)):
            dagger(d, L=44, W=10, pal=dict(dark="#2a0a14", base="#e0a0b4", light="#ffffff"), hilt=GOLD)
    spectral(d, "#ff9ab4", seed=35)
    P.frame(d, MYTHIC_METAL, gem_col="#ff5a7a")


# ---------------------------------------------------------------------------------------------------- Eternal

@portrait
def gorran(d):
    """Gorran Stoneveil, the Mountain That Walks: a giant with a stone-grey beard and a horned helm, a mountain behind."""
    P.background(d, "#14121a", haze="#a8a0d0", haze2="#a08a6a", motes="#e0d8ff", seed=231)
    d.path(poly([(0, 200), (60, 110), (96, 150), (140, 70), (196, 150), (226, 120), (256, 170), (256, 256), (0, 256)]), fill="#1a1824", op=0.8)
    d.path(poly([(118, 98), (140, 70), (160, 98), (148, 92), (140, 100), (130, 92)]), fill="#d8d4e8", op=0.5)
    P.vignette(d)
    cx, cy = 128, 116
    skin = ghost_skin("#b8a090", 0.35)
    plate = dict(dark="#2a2632", base="#76707e", light="#dcd8e6")
    P.shoulders(d, plate, top=184, spread=1.16)
    for sx in (-1, 1):
        d.path(smooth([(cx + sx * 44, 192), (cx + sx * 92, 184), (cx + sx * 112, 210)], closed=False), stroke="#c8c0e0", sw=3.4)
    P.neck(d, cx, cy + 40, 32, 30, skin)
    ghost_face(d, cx, cy, skin, "#e0d8ff", brow="#9a9aa4", smile=-0.4, w=1.12, jaw=1.16, age=2)
    beard(d, cx, cy, top="#c8c8d0", bottom="#4a4a56", length=112)
    great_helm(d, cx, cy, plate, "#c8c0e0", crest="horns")
    spectral(d, "#e0d8ff", seed=41)
    P.frame(d, ETERNAL_METAL, gem_col="#c8a8ff")


@portrait
def aurelis(d):
    """Aurelis Dawnmantle, the Sunsworn: golden hair, a crown of sunrays, a greatsword blazing behind her."""
    P.background(d, "#241808", haze="#ffd060", haze2="#c8a8ff", motes="#fff0b0", seed=232)
    sun(d, 128, 70, 46, pal=EL["light"], rays=16, ray_len=2.0)
    P.vignette(d)
    cx, cy = 128, 118
    skin = ghost_skin("#ecc8a0", 0.25)
    plate = dict(dark="#5a3a10", base="#d0a050", light="#fff4d0")
    with d.g(T(58, 150, -26, 1.6)):
        sword(d, L=110, W=16, pal=dict(dark="#8a6a20", base="#fff0b0", light="#ffffff"), hilt=GOLD)
    hair_back(d, cx, cy, "#e8b850", length=76, width=50)
    P.shoulders(d, plate, top=186, spread=1.02)
    collar(d, cx, plate)
    P.neck(d, cx, cy + 42, 24, 30, skin)
    ghost_face(d, cx, cy, skin, "#fff0b0", brow="#b08030", smile=0.5, w=0.94, jaw=0.9, chin=0.86, lip="#a06a50")
    fringe(d, cx, cy, "#f0c860", "#b08030")
    crown(d, cx, cy, dict(dark="#8a6a20", base="#e0b050", light="#fff4d0"), "#ffe890", points=7, h=30)
    spectral(d, "#fff0b0", seed=42)
    P.frame(d, ETERNAL_METAL, gem_col="#fff0a0")


@portrait
def ilyra(d):
    """Ilyra Moonwhisper, the Tidecaller: long sea-dark hair, a crescent circlet, rings of tide around her."""
    P.background(d, "#081624", haze="#5aa8ff", haze2="#c8a8ff", motes="#c8e8ff", seed=233)
    P.vignette(d)
    cx, cy = 128, 116
    skin = ghost_skin("#d8c0c8", 0.35)
    robe = dict(dark="#0a1a34", base="#2a5a8a", light="#9ac8f0")
    for k in range(3):
        r = 96 + k * 16
        d.path(f"M{cx - r},{cy + 20} Q{cx},{cy + 20 - r * 0.6} {cx + r},{cy + 20}", stroke="#8ac8ff", sw=2.4, op=0.5 - k * 0.12)
    hair_back(d, cx, cy, "#16304a", length=88, width=52)
    P.shoulders(d, robe, top=188, spread=1.0)
    P.neck(d, cx, cy + 42, 24, 30, skin)
    ghost_face(d, cx, cy, skin, "#c8e8ff", brow="#1a2a3a", smile=0.5, w=0.9, jaw=0.88, chin=0.84, lip="#7a6a8a")
    fringe(d, cx, cy, "#1e3a5a", "#4a7aa0")
    d.path(f"M{cx - 44},{cy - 46} Q{cx},{cy - 60} {cx + 44},{cy - 46}", stroke="#e8f0ff", sw=3.2)
    # a crescent moon on the circlet: an outer arc and a thinner inner arc
    outer = [(cx + 16 * math.cos(a), cy - 66 + 16 * math.sin(a)) for a in [math.radians(t) for t in range(60, 301, 12)]]
    inner = [(cx + 7 + 12 * math.cos(a), cy - 66 + 12 * math.sin(a)) for a in [math.radians(t) for t in range(290, 69, -12)]]
    d.shape(poly(outer + inner), fill=d.lin([(0, "#ffffff"), (1, "#b8c8f0")], cx - 16, cy - 82, cx + 8, cy - 50), ow=2)
    spectral(d, "#c8e8ff", seed=43)
    P.frame(d, ETERNAL_METAL, gem_col="#8ac8ff")


@portrait
def kaedric(d):
    """Kaedric Emberline, the Skyburner: ember-red hair, a scorched leather collar, a crossbow and burning sky behind."""
    P.background(d, "#200a04", haze="#ff6a14", haze2="#ffd34a", motes="#ffb060", seed=234)
    P.vignette(d)
    cx, cy = 124, 116
    skin = ghost_skin("#c8906a", 0.3)
    leather = dict(dark="#2a120a", base="#7a3a1e", light="#d0804a")
    with d.g(T(196, 146, 12, 1.5)):
        bow(d, H=84, pal=dict(dark="#3a1a0c", base="#8a5a32", light="#e0b080"))
    d.path(f"M188,108 L204,196", stroke="#4a2a14", sw=8)
    P.shoulders(d, leather, top=188, spread=1.0)
    collar(d, cx, leather)
    P.neck(d, cx, cy + 42, 26, 30, skin)
    hair_back(d, cx, cy, "#8a2a0a", length=14, width=46)
    ghost_face(d, cx, cy, skin, "#ffb060", brow="#5a1a08", smile=0.1, w=0.98, jaw=1.0, lip="#8a4a3a")
    fringe(d, cx, cy, "#a8380e", "#ff7a2a")
    for x in (48, 90, 170, 212):
        flame(d, x, 250, 0.5, EL["fire"])
    spectral(d, "#ffb060", seed=44)
    P.frame(d, ETERNAL_METAL, gem_col="#ff7a2a")


@portrait
def veyl(d):
    """Veyl Ashenmourn, the Unseen Crown: a deep hood, violet eyes, and a crown that is only an outline of light."""
    P.background(d, "#08040e", haze="#6a3ab0", haze2="#2a1a4a", motes="#b684ea", seed=235)
    P.vignette(d)
    cx, cy = 128, 114
    skin = ghost_skin("#a898b8", 0.35)
    cloak = dict(dark="#06040a", base="#1e1430", light="#4a3a68")
    inner = hood(d, cx, cy, cloak, cloak)
    P.shoulders(d, cloak, top=188, spread=1.02)
    P.neck(d, cx, cy + 40, 26, 30, skin)
    ghost_face(d, cx, cy, skin, "#d0a0ff", brow="#10081a", smile=-0.8, w=0.94, jaw=0.96, age=1, ears=False)
    mask = smooth([(cx - 40, cy + 4), (cx + 40, cy + 4), (cx + 36, cy + 34), (cx + 16, cy + 52), (cx - 16, cy + 52), (cx - 36, cy + 34)], tension=0.35)
    d.path(mask, stroke=OUTLINE, sw=4)
    d.path(mask, fill=d.lin([(0, "#2a1e3e"), (1, "#0c0614")], cx, cy + 4, cx, cy + 52))
    d.path(inner, fill=cloak["dark"], stroke=OUTLINE, stroke_width=3)
    # the unseen crown: only its outline burns
    pts = [(cx - 40, cy - 72)]
    for k in range(11):
        pts.append((cx - 40 + k * 8, cy - 72 - (20 if k % 2 == 1 else 4)))
    pts.append((cx + 40, cy - 72))
    d.path(poly(pts), stroke="#d0a0ff", sw=3.2, op=0.9)
    d.path(poly(pts), stroke="#ffffff", sw=1.0, op=0.8)
    for sx in (-1, 1):
        with d.g(T(cx + sx * 86, 226, sx * 22, 1.1)):
            dagger(d, L=42, W=10, pal=dict(dark="#10041a", base="#c8a8f0", light="#ffffff"), hilt=dict(dark="#2a2440", base="#a8a0d0", light="#f4f0ff"))
    spectral(d, "#b684ea", seed=45)
    P.frame(d, ETERNAL_METAL, gem_col="#c8a8ff")


def build():
    out = []
    for name, fn in PORTRAITS.items():
        p = os.path.join(UI, "portraits", "%s.svg" % name)
        write(p, fn().svg())
        out.append(p)
    return out


if __name__ == "__main__":
    for p in build():
        print("wrote", os.path.relpath(p, ROOT))
