"""bh-010 class art for the two new heroes:
  icons/classes/ranger.svg, shadowblade.svg   - heraldic crests, 256 viewBox, transparent (style of icons_crests.py)
  portraits/ranger.svg, shadowblade.svg       - hero busts, 256 viewBox (style of portraits.py knight()/mage())
Registered in build_all.py as categories "classes10" (CLASSES10) and "portraits10" (PORTRAITS10)."""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, OUTLINE, GOLD, STEEL, CRIMSON, BRONZE, LEATHER, WOOD, BONE, EL, f, poly, smooth, mix, lt, dk,
                    ribbon, taper, arc_pts, bez, qbez, star_pts, ngon, polar, rrect_path, circle_path, lerp, jag_line)
from bh_shapes import T, bow, heater_shield, heater_pts, rune_ring, motes, smooth_pts, gem
from bh010_motifs import (BRIGHT_STEEL, DARK_STEEL, VIOLET, FOREST, FLETCH_GREEN, FLETCH_WHITE, arrow2, dagger2, leaf,
                          smoke, quiver)
from icons_crests import mantling
from icons_badges import feather
import portraits as P

CLASSES10 = {}
PORTRAITS10 = {}

GREEN_CLOTH = dict(dark="#0e2a14", base="#2e6a34", light="#7ab86a")
BRONZE_LINING = dict(dark="#4a3010", base="#a0783a", light="#ecd49a")
VIOLET_CLOTH = dict(dark="#14061e", base="#4a1e7a", light="#a070e0")
BLACK_LINING = dict(dark="#050308", base="#2a2432", light="#6a6078")


def reg(table, name, w=256, h=256):
    def deco(fn):
        def build():
            d = Doc(w, h, name="bh10c_" + name)
            fn(d)
            return d
        table[name] = build
        return fn
    return deco


# ------------------------------------------------------------------------------------------ crests

@reg(CLASSES10, "ranger")
def ranger_crest(d: Doc):
    cx, cy = 128, 140
    d.glow(cx, cy, 124, "#4a9a3a", 0.45)
    with d.g(T(cx, cy)):
        mantling(d, -1, pal=GREEN_CLOTH, lining=BRONZE_LINING)
        mantling(d, 1, pal=GREEN_CLOTH, lining=BRONZE_LINING)
    # crossed arrows behind the shield
    for a in (-38, 38):
        sx = 1 if a > 0 else -1
        with d.g(T(cx - sx * 62, cy + 92, a, 1.9)):
            arrow2(d, L=112, head=BRIGHT_STEEL, fletch=FLETCH_GREEN, head_scale=1.3, shaft_w=2.6)
    # oak leaves at the base
    for i, (x, y, a) in enumerate(((cx - 40, cy + 84, -70), (cx - 22, cy + 96, -40), (cx + 22, cy + 96, 40), (cx + 40, cy + 84, 70))):
        with d.g(T(x, y, a, 1.6)):
            leaf(d, L=26, W=12, pal=FOREST)
    with d.g(T(cx, cy + 8, 0, 1.0)):
        heater_shield(d, w=124, h=146, field=GREEN_CLOTH, rim=BRONZE_LINING, emblem=None, ow=3.2)
        # charge: a strung longbow with a nocked arrow pointing to the sky, over a crescent of stars
        for k in range(5):
            x, y = polar(0, 12, 44, math.radians(200 + k * 35))
            d.path(poly(star_pts(x, y, 4, 5, 1.4)), fill="#fff4c8")
        with d.g(T(-8, 4, 0, 0.92)):
            bow(d, H=112, pal=dict(dark="#3a2410", base="#8a5a2a", light="#e0b070"), limb=8)
        with d.g(T(-6, 58, 0, 1.0)):
            arrow2(d, L=100, head=dict(dark="#6a4a14", base="#ffd070", light="#fffbe6"), fletch=FLETCH_WHITE, head_scale=1.5, shaft_w=2.6)
    # hawk-feather crest over the shield
    for i, (a, L) in enumerate(((-28, 64), (0, 76), (28, 64))):
        with d.g(T(cx + a * 0.3, 70, a, 1.0)):
            feather(d, L=L, W=18, pal=dict(dark="#3a2410", base="#9a6a36", light="#f0d8a8") if i != 1 else dict(dark="#4a4a50", base="#d8d8dc", light="#ffffff"))
    d.circle(cx, 72, 9, fill=d.rad([(0, "#d0ffc0"), (0.5, "#3ac050"), (1, "#0e3a14")], cx - 2, 70, 10), stroke=OUTLINE, stroke_width=2.4)
    d.circle(cx - 3, 69, 2.4, fill="#ffffff", opacity=0.9)


@reg(CLASSES10, "shadowblade")
def shadowblade_crest(d: Doc):
    cx, cy = 128, 128
    d.glow(cx, cy, 128, "#7a2ad0", 0.5)
    with d.g(T(cx, cy + 6)):
        mantling(d, -1, pal=VIOLET_CLOTH, lining=BLACK_LINING)
        mantling(d, 1, pal=VIOLET_CLOTH, lining=BLACK_LINING)
    # crossed daggers behind the roundel
    for a in (-40, 40):
        sx = 1 if a > 0 else -1
        with d.g(T(cx - sx * 70, cy + 84, a, 1.9)):
            dagger2(d, L=92, W=15, glow="#b070ff")
    # dark roundel with a violet bezel and a rune ring
    d.circle(cx, cy, 86, fill=d.rad([(0, "#2a1440", 0.95), (0.7, "#120a1e", 0.97), (1, "#07040c", 0.97)], cx, cy - 10, 86))
    d.circle(cx, cy, 90, stroke=OUTLINE, stroke_width=6)
    d.circle(cx, cy, 88, stroke=d.lin([(0, "#e2c4ff"), (0.5, "#6a5a80"), (1, "#14101c")], 40, 40, 216, 216), stroke_width=5)
    rune_ring(d, cx, cy, 78, "#b890ff", width=2.4, ticks=24, seed=19, op=0.8)
    # crescent moon behind the mask
    R, th = 52, 20
    top, bot = (cx + 18, cy - 12 - R), (cx + 18, cy - 12 + R)
    r2 = (R * R + (R - th) ** 2) / (2 * (R - th))
    dd = f"M{f(top[0])},{f(top[1])} A{f(R)},{f(R)} 0 0 1 {f(bot[0])},{f(bot[1])} A{f(r2)},{f(r2)} 0 0 0 {f(top[0])},{f(top[1])} Z"
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.rad([(0, "#ffffff"), (0.5, "#e0d0ff"), (1, "#8a70d0")], cx + 50, cy - 40, 70))
    # hooded, masked face
    hood = [(cx - 4, cy - 62), (cx + 30, cy - 46), (cx + 40, cy - 6), (cx + 36, cy + 40), (cx + 16, cy + 58), (cx - 24, cy + 58), (cx - 44, cy + 40),
            (cx - 48, cy - 6), (cx - 38, cy - 46)]
    hd = smooth(hood, tension=0.5)
    d.path(hd, stroke=OUTLINE, sw=6)
    d.path(hd, fill=d.lin([(0, "#5a4a7a"), (0.45, "#2a2040"), (1, "#0a0612")], cx - 48, cy - 62, cx + 40, cy + 58))
    op_ = smooth([(cx - 4, cy - 42), (cx + 24, cy - 28), (cx + 28, cy + 8), (cx + 14, cy + 40), (cx - 24, cy + 40), (cx - 36, cy + 8), (cx - 30, cy - 28)], tension=0.5)
    d.path(op_, fill="#030206")
    for sx in (-1, 1):
        x = cx - 4 + sx * 14
        d.glow(x, cy - 6, 12, "#c070ff", 1.0)
        d.path(f"M{x - 9},{cy - 6} Q{x},{cy - 11} {x + 9},{cy - 6} Q{x},{cy - 3} {x - 9},{cy - 6} Z", fill="#f0dcff")
    mask = smooth([(cx - 36, cy + 4), (cx - 4, cy + 10), (cx + 28, cy + 4), (cx + 24, cy + 32), (cx + 10, cy + 44), (cx - 18, cy + 44), (cx - 32, cy + 32)], tension=0.4)
    d.path(mask, stroke=OUTLINE, sw=4)
    d.path(mask, fill=d.lin([(0, "#6a2aa8"), (1, "#240a40")], cx, cy + 4, cx, cy + 44))
    for k in range(3):
        y = cy + 16 + k * 8
        d.path(f"M{cx - 30 + k * 3},{y} Q{cx - 4},{y + 4} {cx + 24 - k * 3},{y}", stroke="#14061e", sw=1.6, op=0.8)
    # smoke curling at the base
    smoke(d, [(cx - 60, cy + 92, 16), (cx - 34, cy + 102, 14), (cx + 34, cy + 102, 14), (cx + 60, cy + 92, 16), (cx, cy + 108, 14)],
          top="#8a80a8", bottom="#2a2438", op=0.9)
    gem(d, cx, cy + 96, 10, dict(dark="#2a0a4a", base="#8a3ae0", light="#e2c4ff"), sides=6)
    for (x, y, s) in ((cx - 70, cy - 54, 5), (cx + 74, cy - 60, 4), (cx - 82, cy + 20, 3.5)):
        d.sparkle(x, y, s, "#f0e4ff", 0.9, glow_color="#a060ff")


# ------------------------------------------------------------------------------------------ portraits

@reg(PORTRAITS10, "ranger")
def ranger_portrait(d: Doc):
    P.background(d, "#16301a", haze="#3a7a3a", haze2="#c8a040", motes="#d8f0a0", seed=31)
    P.vignette(d)
    cloak = dict(dark="#0a1e0e", base="#23502a", light="#5a9a4a")
    leather = dict(dark="#2a160a", base="#6a4024", light="#b07c4c")
    cx, cy = 128, 120
    # quiver behind the right shoulder (fletchings above)
    with d.g(T(188, 150, 22, 1.5)):
        quiver(d, H=70, pal=leather, trim=BRONZE, fletch=FLETCH_GREEN)
    # cloak + shoulders
    P.shoulders(d, cloak, top=186, spread=1.0)
    d.path(smooth([(70, 200), (128, 222), (186, 200), (200, 256), (56, 256)], tension=0.4), fill=dk(cloak["base"], 0.3), stroke=OUTLINE, stroke_width=3)
    # leather jerkin under the cloak
    d.path(poly([(100, 206), (156, 206), (164, 256), (92, 256)]), fill=d.lin([(0, leather["light"]), (1, leather["dark"])], 100, 206, 156, 256), stroke=OUTLINE, stroke_width=3)
    for y in (216, 230, 244):
        d.path(f"M112,{y} L144,{y}", stroke=leather["dark"], sw=1.4)
        for x in (118, 138):
            d.circle(x, y, 1.6, fill=BRONZE["light"])
    # fur collar: a ruff of tufts around the neck
    rng = random.Random(4)
    tufts = []
    for i in range(15):
        t = i / 14
        x = lerp(62, 194, t)
        y = 190 + 16 * math.sin(math.pi * t) + rng.uniform(-3, 3)
        tufts.append((x, y))
    fur = dict(dark="#3a2a1a", base="#8a6a4a", light="#d8c0a0")
    for i, (x, y) in enumerate(tufts):
        tf = smooth([(x - 12, y - 6), (x, y - 16 - (i % 3) * 3), (x + 12, y - 6), (x + 6, y + 10), (x - 6, y + 10)], tension=0.5)
        d.path(tf, stroke=OUTLINE, sw=3)
        d.path(tf, fill=d.lin([(0, fur["light"]), (0.6, fur["base"]), (1, fur["dark"])], x, y - 18, x, y + 10))
    for (x, y) in tufts[::2]:
        d.path(f"M{x - 3},{y - 8} L{x},{y + 2} M{x + 4},{y - 6} L{x + 2},{y + 4}", stroke=fur["dark"], sw=1, op=0.7)
    # quiver strap across the chest with a bronze buckle
    d.path("M78,200 L176,256", stroke=OUTLINE, sw=12)
    d.path("M78,200 L176,256", stroke=leather["base"], sw=8)
    d.path("M80,198 L178,254", stroke=leather["light"], sw=1.4, op=0.7)
    d.path(rrect_path(118, 214, 16, 14, 2), fill=d.lin([(0, BRONZE["light"]), (1, BRONZE["dark"])], 118, 214, 134, 228), stroke=OUTLINE, stroke_width=2)
    d.path(rrect_path(122, 218, 8, 6, 1), fill=leather["dark"])
    # hood back
    hood_o = [(cx, 22), (cx + 56, 40), (cx + 74, 100), (cx + 76, 170), (cx + 52, 196), (cx - 52, 196), (cx - 76, 170), (cx - 74, 100), (cx - 56, 40)]
    hd = smooth(hood_o, tension=0.5)
    d.path(hd, stroke=OUTLINE, sw=6)
    d.path(hd, fill=d.lin([(0, cloak["light"]), (0.45, cloak["base"]), (1, cloak["dark"])], cx - 74, 30, cx + 74, 190))
    d.path(smooth([(cx - 60, 60), (cx - 70, 120), (cx - 66, 170)], closed=False), stroke=cloak["dark"], sw=3, op=0.7)
    op_ = smooth([(cx, 44), (cx + 46, 66), (cx + 56, 126), (cx + 42, 184), (cx - 42, 184), (cx - 56, 126), (cx - 46, 66)], tension=0.5)
    d.path(op_, fill="#061008")
    P.neck(d, cx, cy + 44, 30, 28, P.SKIN_TAN)
    P.ears(d, cx, cy, P.SKIN_TAN, w=0.95)
    P.head(d, cx, cy, P.SKIN_TAN, w=0.95, jaw=1.05, chin=1.0)
    # weathered detail: stubble beard + scar
    beard = smooth([(cx - 36, cy + 12), (cx - 30, cy + 34), (cx - 14, cy + 48), (cx, cy + 52), (cx + 14, cy + 48), (cx + 30, cy + 34), (cx + 36, cy + 12),
                    (cx + 24, cy + 26), (cx + 10, cy + 22), (cx, cy + 24), (cx - 10, cy + 22), (cx - 24, cy + 26)], tension=0.5)
    d.path(beard, fill="#3a2414", op=0.55)
    for i in range(26):
        x = cx + rng.uniform(-30, 30)
        y = cy + rng.uniform(26, 48)
        if abs(x - cx) < 34 - (y - cy - 26) * 0.6:
            d.circle(x, y, 0.8, fill="#1a0e06", opacity=0.6)
    d.path(f"M{cx + 20},{cy - 20} L{cx + 28},{cy + 2}", stroke="#8a3a2a", sw=2.2, op=0.8)
    d.path(f"M{cx + 21},{cy - 20} L{cx + 29},{cy + 2}", stroke="#f0b090", sw=0.8, op=0.7)
    # hair strands under the hood
    hair = "#3a2414"
    for sx in (-1, 1):
        hp = smooth([(cx, cy - 54), (cx + sx * 30, cy - 50), (cx + sx * 42, cy - 22), (cx + sx * 40, cy + 10), (cx + sx * 34, cy - 14), (cx + sx * 20, cy - 40)], tension=0.5)
        d.path(hp, fill=hair, stroke=OUTLINE, stroke_width=2)
    d.path(smooth([(cx - 50, cy - 28), (cx - 30, cy - 58), (cx, cy - 66), (cx + 30, cy - 58), (cx + 50, cy - 28), (cx + 30, cy - 44), (cx, cy - 50), (cx - 30, cy - 44)], tension=0.5), fill="#061008", op=0.6)
    P.brows(d, cx, cy - 16, "#2a1608", thick=4.4, angle=2.0)
    P.eyes(d, cx, cy - 3, iris="#4a8a3a", spacing=17, w=10.5, h=4.2, squint=0.25, age=2)
    P.nose(d, cx, cy - 2, P.SKIN_TAN, L=20, w=7)
    P.mouth(d, cx, cy + 28, P.SKIN_TAN, w=12, smile=-0.5, lip="#8a4a34")
    # hood rim stitching
    d.path(smooth([(cx - 72, 170), (cx - 64, 96), (cx - 46, 46), (cx, 26), (cx + 46, 46), (cx + 64, 96), (cx + 72, 170)], closed=False), stroke=BRONZE["base"], sw=2)
    # a feather tucked in the hood
    with d.g(T(cx + 58, 64, 30, 0.9)):
        feather(d, L=56, W=14, pal=dict(dark="#3a2410", base="#9a6a36", light="#f0d8a8"))
    P.frame(d, dict(dark="#2a2410", base="#8a7c44", light="#e6dca2"), gem_col="#8ad870")


@reg(PORTRAITS10, "shadowblade")
def shadowblade_portrait(d: Doc):
    P.background(d, "#1e0e30", haze="#5a2a9a", haze2="#2a1a4a", motes="#c8a0ff", seed=37)
    P.vignette(d)
    leather = dict(dark="#07050a", base="#221a2c", light="#5a4a6a")
    cx, cy = 128, 120
    # dagger hilt over the left shoulder
    with d.g(T(64, 176, -24, 1.4)):
        dagger2(d, L=10, W=12)
    P.shoulders(d, leather, top=186, spread=0.98)
    # layered leather pauldrons with straps
    for sx in (-1, 1):
        pl = smooth([(128 + sx * 44, 194), (128 + sx * 86, 190), (128 + sx * 110, 214), (128 + sx * 108, 240), (128 + sx * 66, 228)], tension=0.5)
        d.path(pl, stroke=OUTLINE, sw=5)
        d.path(pl, fill=d.lin([(0, leather["light"]), (1, leather["dark"])], 128 + sx * 44, 190, 128 + sx * 110, 240))
        d.path(smooth([(128 + sx * 54, 200), (128 + sx * 88, 198), (128 + sx * 104, 216)], closed=False), stroke="#8a3ae0", sw=1.6, op=0.8)
    # violet sash across the chest
    sash = [(70, 206), (92, 196), (196, 250), (188, 256), (170, 256)]
    d.path(poly(sash), stroke=OUTLINE, sw=4)
    d.path(poly(sash), fill=d.lin([(0, "#b070ff"), (0.5, "#6a2aa8"), (1, "#2a0a4a")], 70, 196, 196, 256))
    for t in (0.3, 0.55, 0.8):
        x, y = lerp(82, 190, t), lerp(200, 252, t)
        d.path(f"M{x - 6},{y - 8} L{x + 4},{y + 8}", stroke="#2a0a4a", sw=1.4, op=0.7)
    # throwing knives on a bandolier strap
    d.path("M184,200 L148,256", stroke=OUTLINE, sw=9)
    d.path("M184,200 L148,256", stroke=leather["light"], sw=5)
    for k in range(3):
        x, y = 180 - k * 11, 208 + k * 16
        with d.g(T(x, y, 30, 0.7)):
            d.path("M0,0 L0,-16", stroke=OUTLINE, sw=5)
            d.path("M0,0 L0,-16", stroke=STEEL["light"], sw=2.6)
    # hood
    hood_o = [(cx, 20), (cx + 58, 40), (cx + 76, 102), (cx + 78, 172), (cx + 52, 198), (cx - 52, 198), (cx - 78, 172), (cx - 76, 102), (cx - 58, 40)]
    hd = smooth(hood_o, tension=0.5)
    d.path(hd, stroke=OUTLINE, sw=6)
    d.path(hd, fill=d.lin([(0, "#4a3a66"), (0.45, "#221a30"), (1, "#07050c")], cx - 76, 30, cx + 76, 190))
    for pts in (((cx - 30, 44), (cx - 52, 110), (cx - 60, 170)), ((cx + 34, 48), (cx + 56, 110), (cx + 62, 168))):
        d.path(smooth(pts, closed=False), stroke="#07050c", sw=3, op=0.8)
    op_ = smooth([(cx, 46), (cx + 46, 68), (cx + 54, 128), (cx + 40, 186), (cx - 40, 186), (cx - 54, 128), (cx - 46, 68)], tension=0.5)
    d.path(op_, fill="#040208")
    P.neck(d, cx, cy + 44, 26, 28, P.SKIN_PALE)
    P.head(d, cx, cy, P.SKIN_PALE, w=0.9, jaw=0.9, chin=0.9)
    # dark hair fringe
    for sx in (-1, 1):
        hp = smooth([(cx, cy - 54), (cx + sx * 30, cy - 50), (cx + sx * 40, cy - 22), (cx + sx * 38, cy + 6), (cx + sx * 30, cy - 18), (cx + sx * 14, cy - 36)], tension=0.5)
        d.path(hp, fill="#0e0a14", stroke=OUTLINE, stroke_width=2)
    d.path(smooth([(cx - 50, cy - 28), (cx - 30, cy - 60), (cx, cy - 66), (cx + 30, cy - 60), (cx + 50, cy - 28), (cx + 30, cy - 44), (cx, cy - 48), (cx - 30, cy - 44)], tension=0.5), fill="#040208", op=0.75)
    # shadow band across the eyes, then glowing violet eyes
    d.path(smooth([(cx - 42, cy - 14), (cx, cy - 18), (cx + 42, cy - 14), (cx + 40, cy + 6), (cx, cy + 4), (cx - 40, cy + 6)], tension=0.5), fill="#1a0a24", op=0.45)
    P.brows(d, cx, cy - 15, "#0e0a14", thick=4.0, angle=3.0)
    P.eyes(d, cx, cy - 3, glow="#b060ff", spacing=16, w=10, h=4.0, squint=0.3)
    # cloth mask over the lower face
    mask = smooth([(cx - 44, cy + 6), (cx - 20, cy + 10), (cx, cy + 6), (cx + 20, cy + 10), (cx + 44, cy + 6), (cx + 42, cy + 34), (cx + 26, cy + 54),
                   (cx, cy + 60), (cx - 26, cy + 54), (cx - 42, cy + 34)], tension=0.45)
    d.path(mask, stroke=OUTLINE, sw=5)
    d.path(mask, fill=d.lin([(0, "#3a2a50"), (0.5, "#1e1430"), (1, "#0a0612")], cx - 44, cy, cx + 44, cy + 60))
    for k in range(4):
        y = cy + 18 + k * 9
        d.path(f"M{cx - 38 + k * 3},{y} Q{cx},{y + 5} {cx + 38 - k * 3},{y}", stroke="#07040c", sw=1.6, op=0.8)
        d.path(f"M{cx - 36 + k * 3},{y - 2} Q{cx},{y + 3} {cx + 36 - k * 3},{y - 2}", stroke="#6a5a8a", sw=0.8, op=0.5)
    d.path(f"M{cx - 2},{cy + 8} L{cx + 2},{cy + 24}", stroke="#5a4a70", sw=1.2, op=0.6)
    # hood trim in violet
    d.path(smooth([(cx - 74, 170), (cx - 66, 96), (cx - 48, 46), (cx, 26), (cx + 48, 46), (cx + 66, 96), (cx + 74, 170)], closed=False), stroke="#8a3ae0", sw=2)
    for (x, y, s) in ((34, 60, 4), (224, 84, 3.4), (212, 40, 3)):
        d.sparkle(x, y, s, "#f0e4ff", 0.85, glow_color="#a060ff")
    P.frame(d, dict(dark="#07060b", base="#3e3a4c", light="#aaa4bc"), gem_col="#b070ff")
