"""bh-029 portraits: the people of Agdao on Zarael Island (game/assets/ui/portraits/<id>.svg, viewBox 0 0 256 256).

Same painted-bust style, helpers and ThorVG-safe subset (paths, gradients, groups, basic shapes) as bh018/bh019:
    terax         Terax, Warden of Agdao: jade-and-obsidian armour, tall feather crest, bronze gauntlet wound with
                  glowing gold wire, a scar, calm hard eyes
    wirekeeper    Wirekeeper Halvessa Orn: older engineer-priestess, turquoise mosaic collar, wire-wound headdress,
                  spectacles of polished crystal
    ilsa          Captain Ilsa Rhondar: weathered sea captain, braided hair, sea coat, copper earring
    agdao_porter  a porter with a tumpline strap across the brow and a woven load behind
    agdao_vendor  a market vendor in a woven headwrap with a basket of fruit
    agdao_elder   an elder with a carved cane and a feather stole

    python tools/ui_art/bh029_portraits.py            # writes the SVGs + .import and a PNG preview (if resvg-py is
                                                      # importable) to work/lemondev/bh-029/evidence/textures/
"""
from __future__ import annotations

import hashlib
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from bh_svg import Doc, OUTLINE, GOLD, BRONZE, f, poly, smooth, lt, dk, rrect_path, mix  # noqa: E402
from bh_shapes import T  # noqa: E402
from portraits import (S, SKIN, SKIN_TAN, SKIN_OLD, background, vignette, frame, neck, head, ears, eyes, brows,  # noqa: E402
                       nose, mouth, shoulders)
from bh003_portraits import wrinkles, lamp_glow, hair_strokes, hair_cap  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "ui", "portraits")
EVI = os.path.join(ROOT, "work", "lemondev", "bh-029", "evidence", "textures")

PORTRAITS = {}

JADE = dict(dark="#0e2a1e", base="#3a8a66", light="#a8e0c0")
OBSID = dict(dark="#050608", base="#1a1e24", light="#5a6470")
WIRE = "#ffc850"
WIRE_HI = "#fff2c0"
TURQ = ["#2aa89a", "#3ab8a8", "#1e8a86", "#48c4b0", "#2a9aa8", "#5ac8b8"]
SKIN_DEEP = dict(light="#c88a5a", base="#965a34", dark="#5a3218", shade="#2e160a")
SKIN_ELDER = dict(light="#dcae88", base="#ac7454", dark="#6c4028", shade="#3a1e10")


def portrait(fn):
    def build():
        d = Doc(S, S, name="pt29_" + fn.__name__)
        fn(d)
        return d
    PORTRAITS[fn.__name__] = build
    return fn


# ------------------------------------------------------------------------------------------ helpers

def feather(d, x, y, L, W, ang, base, tip=None, hi=None):
    """A long crest feather rooted at (x, y), pointing along `ang` degrees (0 = straight up)."""
    with d.g(T(x, y, ang)):
        body = smooth([(0, 0), (W * 0.55, -L * 0.25), (W * 0.5, -L * 0.7), (0, -L), (-W * 0.5, -L * 0.7),
                       (-W * 0.55, -L * 0.25)], tension=0.6)
        d.path(body, stroke=OUTLINE, sw=3)
        stops = [(0, dk(base, 0.35)), (0.55, base), (1, tip or lt(base, 0.3))]
        d.path(body, fill=d.lin(stops, 0, 0, 0, -L))
        if tip:
            d.path(smooth([(W * 0.42, -L * 0.72), (0, -L), (-W * 0.42, -L * 0.72), (0, -L * 0.8)], tension=0.6), fill=tip, op=0.9)
        d.path(f"M0,{f(-2)} L0,{f(-L * 0.94)}", stroke=hi or lt(base, 0.6), sw=1.1, op=0.8)
        for k in range(5):
            yy = -L * (0.25 + k * 0.12)
            d.path(f"M0,{f(yy)} l{f(W * 0.4)},{f(-L * 0.06)} M0,{f(yy)} l{f(-W * 0.4)},{f(-L * 0.06)}",
                   stroke=dk(base, 0.45), sw=0.8, op=0.6)


def wire_glow(d, path_d, w=2.0, col=WIRE):
    """An inlaid Heartwire channel: a dark groove, a soft halo and a bright core."""
    d.path(path_d, stroke="#140c04", sw=w + 2.6)
    d.path(path_d, stroke=col, sw=w * 3.2, op=0.22)
    d.path(path_d, stroke=col, sw=w)
    d.path(path_d, stroke=WIRE_HI, sw=w * 0.4, op=0.9)


def fret_band(d, x0, y0, x1, h, col, step=8):
    """A row of small stepped notches (a stepped-fret trim) between x0 and x1 at y0, height h."""
    pts = []
    x = x0
    up = True
    while x < x1 - 0.1:
        nx = min(x + step, x1)
        yy = y0 - (h if up else 0)
        pts += [(x, yy), (nx, yy)]
        up = not up
        x = nx
    d.path(poly(pts, closed=False), stroke=col, sw=1.6, op=0.9)


def tesserae_band(d, pts_outer, pts_inner, rng, n_u=16, n_v=3, palette=TURQ, accent_every=0, accent="#c83a2a"):
    """Fill the quad strip between two polylines with small irregular mosaic tiles."""
    for i in range(n_u):
        for j in range(n_v):
            def P(u, v):
                a = _poly_at(pts_outer, u)
                b = _poly_at(pts_inner, u)
                return (a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v)
            u0, u1 = i / n_u, (i + 1) / n_u
            v0, v1 = j / n_v, (j + 1) / n_v
            g = 0.08
            q = [P(u0 + g / n_u, v0 + g / n_v), P(u1 - g / n_u, v0 + g / n_v), P(u1 - g / n_u, v1 - g / n_v),
                 P(u0 + g / n_u, v1 - g / n_v)]
            q = [(x + rng.uniform(-0.7, 0.7), y + rng.uniform(-0.7, 0.7)) for x, y in q]
            if accent_every and j == n_v - 1 and i % accent_every == 0:
                col = accent
            elif rng.random() < 0.06:
                col = "#e8e0cc"
            else:
                col = rng.choice(palette)
            d.path(poly(q), fill=col, stroke="#0c1414", stroke_width=0.9)
            d.path(poly([q[0], q[1], (q[1][0] * 0.6 + q[2][0] * 0.4, q[1][1] * 0.6 + q[2][1] * 0.4)]), fill="#ffffff", op=0.18)


def _poly_at(pts, u):
    """Point at fraction u along a polyline."""
    segs = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    tot = sum(segs)
    t = u * tot
    for i, s in enumerate(segs):
        if t <= s or i == len(segs) - 1:
            k = 0 if s == 0 else min(t / s, 1.0)
            return (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * k, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k)
        t -= s
    return pts[-1]


def fingers(d, x, y, n, skin, dx=0, step=10, L=20):
    for i in range(n):
        fy = y + i * step
        fx = x + dx * i
        fing = smooth([(fx - L * 0.7, fy), (fx + L * 0.2, fy - 4), (fx + L, fy + 1), (fx + L * 0.9, fy + 9), (fx + L * 0.1, fy + 8),
                       (fx - L * 0.7, fy + 9)], tension=0.4)
        d.path(fing, stroke=OUTLINE, sw=2.6)
        d.path(fing, fill=d.lin([(0, skin["light"]), (1, skin["dark"])], 0, fy, 0, fy + 9))


# ------------------------------------------------------------------------------------------ Terax

@portrait
def terax(d):
    """Terax, Warden of Agdao."""
    rng = random.Random(2901)
    background(d, "#0c2622", haze="#3ab08a", haze2="#e0a030", motes="#ffd890", seed=291)
    vignette(d)
    cx, cy = 126, 128
    # ---- a tall upright plume of feathers rising from the helm's crest-socket (drawn behind the helm)
    for k, a in enumerate((-24, -14, -5, 4, 13, 23)):
        L = 60 - abs(a) * 0.3 + rng.uniform(-3, 3)
        base = "#2a9a7a" if k % 2 else "#33a496"
        tip = "#c8342a" if k in (1, 4) else "#1e5a4a"
        feather(d, cx + a * 0.35, cy - 60, L, 14, a * 0.9 + 6, base, tip)
    # ---- obsidian cuirass with jade plates and inlaid wire
    shoulders(d, OBSID, top=190, spread=1.1)
    chest = smooth([(cx - 40, 196), (cx + 40, 196), (cx + 46, 256), (cx - 46, 256)], tension=0.15)
    d.path(chest, stroke=OUTLINE, sw=4)
    d.path(chest, fill=d.lin([(0, JADE["light"]), (0.45, JADE["base"]), (1, JADE["dark"])], cx - 40, 196, cx + 40, 256))
    # a stepped glyph on the breastplate, wire-lit
    gx, gy = cx, 228
    wire_glow(d, poly([(gx - 14, gy + 10), (gx - 14, gy), (gx - 7, gy), (gx - 7, gy - 8), (gx + 7, gy - 8), (gx + 7, gy),
                       (gx + 14, gy), (gx + 14, gy + 10)], closed=False), w=2.2)
    d.circle(gx, gy + 2, 3.2, fill=WIRE_HI, stroke=OUTLINE, stroke_width=1.2)
    for sx in (-1, 1):   # jade pauldrons edged in obsidian, a fret trim in gold
        px = cx + sx * 74
        pl = smooth([(px - sx * 34, 194), (px - sx * 6, 178), (px + sx * 30, 186), (px + sx * 44, 214), (px + sx * 20, 232),
                     (px - sx * 26, 222)], tension=0.5)
        d.path(pl, stroke=OUTLINE, sw=5)
        d.path(pl, fill=d.lin([(0, JADE["light"]), (0.5, JADE["base"]), (1, JADE["dark"])], px - 30, 178, px + 30, 232))
        edge = smooth([(px - sx * 28, 222), (px + sx * 18, 230), (px + sx * 42, 212)], closed=False)
        d.path(edge, stroke=OUTLINE, sw=8)
        d.path(edge, stroke=OBSID["base"], sw=5)
        d.path(edge, stroke=OBSID["light"], sw=1.2, op=0.7)
        fret_band(d, px - 22 if sx > 0 else px - 6, 200, px + 6 if sx > 0 else px + 22, 4, GOLD["base"], step=5)
        wire_glow(d, smooth([(px - sx * 24, 210), (px + sx * 4, 204), (px + sx * 30, 208)], closed=False), w=1.4)
    neck(d, cx, cy + 40, 30, 26, SKIN_TAN)
    gor = smooth([(cx - 26, cy + 52), (cx + 26, cy + 52), (cx + 34, cy + 66), (cx - 34, cy + 66)], tension=0.2)
    d.path(gor, stroke=OUTLINE, sw=4)
    d.path(gor, fill=d.lin([(0, OBSID["light"]), (1, OBSID["dark"])], cx, cy + 52, cx, cy + 66))
    head(d, cx, cy, SKIN_TAN, w=1.02, jaw=1.06, chin=0.98, top=0.98)
    # cropped dark hair at the temples, under the helm
    for sx in (-1, 1):
        d.path(smooth([(cx + sx * 34, cy - 30), (cx + sx * 41, cy - 14), (cx + sx * 40, cy + 2), (cx + sx * 35, cy - 10)], tension=0.5),
               fill="#1a1210", stroke=OUTLINE, stroke_width=1.6)
    # jade helm cap with a gold stepped brow band and an obsidian crest-socket
    cap = smooth([(cx - 44, cy - 26), (cx - 40, cy - 46), (cx - 22, cy - 60), (cx, cy - 63), (cx + 22, cy - 60), (cx + 40, cy - 46),
                  (cx + 44, cy - 26), (cx + 24, cy - 34), (cx, cy - 36), (cx - 24, cy - 34)], tension=0.45)
    d.path(cap, stroke=OUTLINE, sw=5)
    d.path(cap, fill=d.lin([(0, JADE["light"]), (0.5, JADE["base"]), (1, JADE["dark"])], cx - 40, cy - 63, cx + 40, cy - 26))
    d.path(smooth([(cx - 34, cy - 50), (cx - 14, cy - 58), (cx + 4, cy - 59)], closed=False), stroke="#e0fff0", sw=2.2, op=0.5)
    band = smooth([(cx - 45, cy - 27), (cx, cy - 37), (cx + 45, cy - 27)], closed=False)
    d.path(band, stroke=OUTLINE, sw=8)
    d.path(band, stroke=GOLD["base"], sw=5)
    d.path(band, stroke=GOLD["light"], sw=1.4, op=0.8)
    for k in range(-4, 5):
        x = cx + k * 9
        y = cy - 37 + abs(k) * abs(k) * 0.12 + abs(k) * 0.6
        d.path(rrect_path(x - 2, y - 2, 4, 4, 0.6), fill=GOLD["dark"])
    sock = poly([(cx - 12, cy - 56), (cx - 12, cy - 62), (cx - 7, cy - 62), (cx - 7, cy - 68), (cx + 7, cy - 68), (cx + 7, cy - 62),
                 (cx + 12, cy - 62), (cx + 12, cy - 56)])
    d.path(sock, fill=d.lin([(0, OBSID["light"]), (1, OBSID["dark"])], cx - 12, cy - 68, cx + 12, cy - 56), stroke=OUTLINE, stroke_width=2.4)
    d.circle(cx, cy - 61, 2.6, fill=WIRE, stroke=OUTLINE, stroke_width=1)
    ears(d, cx, cy + 2, SKIN_TAN, w=1.02)
    # level brows, the left one broken by the scar; calm hard eyes
    brows(d, cx, cy - 16, "#1a1210", thick=4.6, angle=-0.5, w=13)
    eyes(d, cx, cy - 3, iris="#8a6a2a", spacing=17, w=10, h=3.8, squint=0.35, lid=1.2)
    nose(d, cx, cy - 2, SKIN_TAN, L=22, w=9)
    wrinkles(d, cx, cy, SKIN_TAN, fore=1, cheek=0.75, op=0.4)
    mouth(d, cx, cy + 28, SKIN_TAN, w=12, smile=-0.6, lip="#8a4a38")
    scar = [(cx - 30, cy - 30), (cx - 22, cy - 14), (cx - 17, cy + 6), (cx - 12, cy + 22)]
    d.path(smooth(scar, closed=False), stroke=SKIN_TAN["shade"], sw=3.6, op=0.55)
    d.path(smooth(scar, closed=False), stroke="#e8a890", sw=1.6, op=0.9)
    for (x, y) in ((cx - 26, cy - 22), (cx - 19, cy - 4), (cx - 14, cy + 14)):
        d.path(f"M{f(x - 3)},{f(y - 1)} l6,2", stroke=SKIN_TAN["shade"], sw=1, op=0.6)
    # ---- the bronze gauntlet, raised in a fist, its vambrace wound with glowing gold wire
    BRZ = dict(dark="#3a200c", base="#8a5a2a", light="#d8a060")
    arm = poly([(190, 176), (222, 180), (262, 248), (228, 266)])
    d.path(arm, stroke=OUTLINE, sw=5)
    d.path(arm, fill=d.lin([(0, BRZ["light"]), (0.45, BRZ["base"]), (1, BRZ["dark"])], 190, 176, 262, 248))
    for t in (0.06, 0.88):
        p0 = (190 + (228 - 190) * t, 176 + (266 - 176) * t)
        p1 = (222 + (262 - 222) * t, 180 + (248 - 180) * t)
        d.path(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}", stroke=OUTLINE, sw=8)
        d.path(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}", stroke=BRZ["dark"], sw=5)
    for k in range(6):   # wire windings round the vambrace
        t = 0.18 + k * 0.12
        p0 = (190 + (228 - 190) * t, 176 + (266 - 176) * t)
        p1 = (222 + (262 - 222) * t, 180 + (248 - 180) * t)
        wire_glow(d, f"M{f(p0[0] - 2)},{f(p0[1] + 2)} Q{f((p0[0] + p1[0]) / 2)},{f((p0[1] + p1[1]) / 2 - 9)} {f(p1[0] + 2)},{f(p1[1] - 1)}", w=1.8)
    d.circle(205, 152, 34, fill=d.rad([(0, WIRE, 0.3), (1, WIRE, 0)], 205, 152, 34))
    fist = smooth([(186, 172), (182, 150), (188, 136), (222, 136), (228, 150), (224, 172)], tension=0.45)
    d.path(fist, stroke=OUTLINE, sw=4.4)
    d.path(fist, fill=d.lin([(0, BRZ["light"]), (0.6, BRZ["base"]), (1, BRZ["dark"])], 184, 136, 226, 172))
    for k in range(4):   # knuckle plates and finger joints
        kx = 192 + k * 9.5
        d.circle(kx, 141, 5.2, fill=d.lin([(0, "#f0c080"), (1, BRZ["base"])], kx - 4, 136, kx + 4, 146), stroke=OUTLINE, stroke_width=1.6)
        if k:
            d.path(f"M{f(kx - 4.75)},{146} L{f(kx - 4.75)},{160}", stroke=BRZ["dark"], sw=1.6)
    thumb = smooth([(184, 160), (206, 154), (216, 160), (210, 168), (188, 170)], tension=0.5)
    d.path(thumb, stroke=OUTLINE, sw=3)
    d.path(thumb, fill=d.lin([(0, BRZ["light"]), (1, BRZ["dark"])], 184, 154, 216, 170))
    wire_glow(d, "M188,165 Q200,160 212,162", w=1.2)
    d.path(smooth([(cx + 36, cy - 14), (cx + 40, cy + 8), (cx + 32, cy + 30)], closed=False), stroke="#ffd890", sw=2.4, op=0.45)
    frame(d, dict(dark="#0e2a1e", base="#5aa07a", light="#d8f4e0"), gem_col=WIRE)


# ------------------------------------------------------------------------------------------ Wirekeeper

@portrait
def wirekeeper(d):
    """Wirekeeper Halvessa Orn."""
    rng = random.Random(2902)
    background(d, "#1a1430", haze="#e0a030", haze2="#3ab0a0", motes="#ffe0a0", seed=292)
    vignette(d)
    cx, cy = 128, 130
    robe = dict(dark="#2a0e0c", base="#6a2a22", light="#a8584a")
    shoulders(d, robe, top=192, spread=1.06)
    # broad turquoise mosaic collar
    outer = [(cx - 96, 236), (cx - 70, 206), (cx - 30, 192), (cx, 190), (cx + 30, 192), (cx + 70, 206), (cx + 96, 236)]
    inner = [(cx - 58, 250), (cx - 44, 222), (cx - 20, 212), (cx, 211), (cx + 20, 212), (cx + 44, 222), (cx + 58, 250)]
    coll = smooth(outer + inner[::-1], tension=0.3)
    d.path(coll, stroke=OUTLINE, sw=5)
    d.path(coll, fill="#0c1414")
    tesserae_band(d, outer, inner, rng, n_u=22, n_v=3, accent_every=3)
    d.path(smooth(outer, closed=False), stroke=GOLD["base"], sw=2.4)
    d.path(smooth(inner, closed=False), stroke=GOLD["base"], sw=2.4)
    neck(d, cx, cy + 40, 26, 24, SKIN_OLD)
    # silver hair falling from under the headdress
    for sx in (-1, 1):
        hp = smooth([(cx + sx * 30, cy - 40), (cx + sx * 46, cy - 18), (cx + sx * 48, cy + 26), (cx + sx * 44, cy + 56),
                     (cx + sx * 34, cy + 40), (cx + sx * 36, cy - 6)], tension=0.5)
        d.path(hp, fill=d.lin([(0, "#e8e4e0"), (1, "#8a8690")], cx, cy - 40, cx, cy + 56), stroke=OUTLINE, stroke_width=2)
        hair_strokes(d, [[(cx + sx * 40, cy - 20), (cx + sx * 44, cy + 20), (cx + sx * 42, cy + 48)]], "#ffffff", sw=1.2, op=0.6)
    head(d, cx, cy, SKIN_OLD, w=0.9, jaw=0.88, chin=0.86, top=1.0)
    # ---- the wire-wound headdress: a bronze drum wrapped in copper coils, a fan of wire stalks with gold beads
    for k, a in enumerate(range(-50, 51, 10)):
        ang = math.radians(a)
        x0, y0 = cx + a * 0.55, cy - 98
        L = 34 - abs(a) * 0.15
        x1, y1 = x0 + math.sin(ang) * L, y0 - math.cos(ang) * L
        d.path(f"M{f(x0)},{f(y0)} L{f(x1)},{f(y1)}", stroke=OUTLINE, sw=3.2)
        d.path(f"M{f(x0)},{f(y0)} L{f(x1)},{f(y1)}", stroke="#c8743a", sw=1.6)
        d.circle(x1, y1, 7, fill=d.rad([(0, WIRE, 0.6), (1, WIRE, 0)], x1, y1, 7))
        d.circle(x1, y1, 2.8, fill=WIRE_HI if k % 2 else WIRE, stroke=OUTLINE, stroke_width=1.1)
    drum = smooth([(cx - 44, cy - 36), (cx - 50, cy - 70), (cx - 46, cy - 100), (cx, cy - 106), (cx + 46, cy - 100), (cx + 50, cy - 70),
                   (cx + 44, cy - 36), (cx, cy - 44)], tension=0.35)
    d.path(drum, stroke=OUTLINE, sw=5)
    d.path(drum, fill=d.lin([(0, BRONZE["light"]), (0.45, BRONZE["base"]), (1, BRONZE["dark"])], cx - 50, cy - 100, cx + 50, cy - 40))
    for k in range(7):   # coil wraps
        y = cy - 46 - k * 8.4
        wd = f"M{f(cx - 47)},{f(y + 2)} Q{f(cx)},{f(y - 6)} {f(cx + 47)},{f(y + 2)}"
        if k in (1, 5):
            wire_glow(d, wd, w=1.8)
            continue
        d.path(wd, stroke=OUTLINE, sw=4.2)
        d.path(wd, stroke="#b8642c" if k % 2 else "#d88a48", sw=2.4)
        d.path(wd, stroke="#ffd0a0", sw=0.7, op=0.6)
    for sx in (-1, 1):   # wire drops at the sides of the drum
        wire_glow(d, smooth([(cx + sx * 46, cy - 60), (cx + sx * 52, cy - 40), (cx + sx * 50, cy - 16)], closed=False), w=1.3)
        d.circle(cx + sx * 50, cy - 14, 2.6, fill=WIRE_HI, stroke=OUTLINE, stroke_width=1)
    d.circle(cx, cy - 74, 13, fill=d.rad([(0, "#7affe8", 0.5), (1, "#7affe8", 0)], cx, cy - 74, 13))
    d.circle(cx, cy - 74, 8, fill=d.rad([(0, "#c8fff4"), (0.5, TURQ[1]), (1, TURQ[2])], cx - 2, cy - 76, 9), stroke=OUTLINE, stroke_width=2.2)
    d.circle(cx, cy - 74, 11, stroke=GOLD["base"], stroke_width=2)
    ears(d, cx, cy + 2, SKIN_OLD, w=0.9)
    wrinkles(d, cx, cy, SKIN_OLD, fore=3, cheek=0.85, eye_bags=True, op=0.5)
    brows(d, cx, cy - 16, "#d8d4d0", thick=3.4, angle=1.2, w=12)
    eyes(d, cx, cy - 3, iris="#5a7a6a", spacing=15, w=9, h=3.6, age=2, squint=0.15)
    nose(d, cx, cy - 2, SKIN_OLD, L=21, w=8)
    mouth(d, cx, cy + 26, SKIN_OLD, w=10, smile=0.6, lip="#a0605a")
    # spectacles of polished crystal: round lenses, faint teal tint, bright facet glints, thin bronze rims
    for sx in (-1, 1):
        lx, ly = cx + sx * 15, cy - 3
        d.circle(lx, ly, 12, fill="#bff8f0", opacity=0.16)
        d.circle(lx, ly, 12, stroke=OUTLINE, stroke_width=3.6)
        d.circle(lx, ly, 12, stroke="#c8943a", stroke_width=1.8)
        d.path(f"M{f(lx - 8)},{f(ly - 5)} Q{f(lx - 4)},{f(ly - 10)} {f(lx + 2)},{f(ly - 10)}", stroke="#ffffff", sw=1.8, op=0.75)
        d.path(poly([(lx + 4, ly + 4), (lx + 8, ly + 1), (lx + 7, ly + 7)]), fill="#ffffff", op=0.35)
        d.path(f"M{f(lx + sx * 12)},{f(ly - 2)} L{f(lx + sx * 24)},{f(ly - 8)}", stroke="#c8943a", sw=1.8)
    d.path(f"M{cx - 4},{cy - 4} Q{cx},{cy - 8} {cx + 4},{cy - 4}", stroke="#c8943a", sw=1.8)
    # a slim wire-wound rod held up (her tool), its tip glowing
    d.path("M206,256 L218,150", stroke=OUTLINE, sw=7)
    d.path("M206,256 L218,150", stroke="#5a3a20", sw=4)
    for k in range(8):
        y = 160 + k * 11
        x = 218 - (y - 150) * 0.11
        d.path(f"M{f(x - 4)},{f(y + 2)} L{f(x + 4)},{f(y - 2)}", stroke="#d88a48", sw=1.8)
    d.circle(218, 146, 16, fill=d.rad([(0, WIRE, 0.65), (1, WIRE, 0)], 218, 146, 16))
    d.circle(218, 146, 4.4, fill=WIRE_HI, stroke=OUTLINE, stroke_width=1.4)
    fingers(d, 206, 196, 3, SKIN_OLD, dx=-1, step=9, L=18)
    frame(d, GOLD, gem_col=TURQ[3])


# ------------------------------------------------------------------------------------------ Ilsa

@portrait
def ilsa(d):
    """Captain Ilsa Rhondar of Agdao's ship."""
    background(d, "#10283a", haze="#4a8ab0", haze2="#e0a050", motes="#cfe8ff", seed=293)
    lamp_glow(d, 214, 70, 70, "#ffc070", 0.4)
    vignette(d)
    cx, cy = 122, 122
    coat = dict(dark="#0a1220", base="#22344e", light="#4a6688")
    shoulders(d, coat, top=190, spread=1.08)
    # the braid, over the right shoulder (drawn before the collar so the collar laps it)
    for k in range(9):
        y = cy + 18 + k * 12
        d.ellipse(cx + 44 + k * 1.6, y, 8.5, 7.5, fill="#3a2418" if k % 2 else "#4e3020", stroke=OUTLINE, stroke_width=1.8)
        d.path(f"M{f(cx + 38 + k * 1.6)},{f(y - 2)} q6,4 12,0", stroke="#6a4a30", sw=1, op=0.7)
    d.ellipse(cx + 59, cy + 128, 6, 4, fill="#c8743a", stroke=OUTLINE, stroke_width=1.6)
    # sea coat: high turned-up collar, brass buttons, a faded red neckcloth
    d.path("M98,190 L122,222 L146,190 Z", fill="#8a2a22", stroke=OUTLINE, stroke_width=3)
    for sx in (-1, 1):
        lap = smooth([(cx + sx * 16, 186), (cx + sx * 46, 168), (cx + sx * 62, 196), (cx + sx * 40, 240), (cx + sx * 18, 214)], tension=0.35)
        d.path(lap, stroke=OUTLINE, sw=4.4)
        d.path(lap, fill=d.lin([(0, lt(coat["light"], 0.1)), (0.5, coat["base"]), (1, coat["dark"])], cx + sx * 16, 168, cx + sx * 60, 240))
        d.path(smooth([(cx + sx * 20, 190), (cx + sx * 46, 174), (cx + sx * 56, 196)], closed=False), stroke="#8aa4c4", sw=1.4, op=0.6)
        for k in range(2):
            bx, by = cx + sx * 30, 216 + k * 22
            d.circle(bx, by, 4.6, fill=d.rad([(0, GOLD["light"]), (1, GOLD["dark"])], bx - 1, by - 1, 5), stroke=OUTLINE, stroke_width=1.6)
    neck(d, cx, cy + 42, 26, 24, SKIN_TAN)
    head(d, cx, cy, SKIN_TAN, w=0.93, jaw=0.94, chin=0.9, top=1.0)
    # hair pulled back hard, a streak of grey at the temple
    hair_cap(d, cx, cy, "#4a2e1e", hi="#7a5034", w=0.94, top=1.0, line=1.0, sides=0.6)
    hair_strokes(d, [[(cx - 34, cy - 30), (cx - 16, cy - 48), (cx + 8, cy - 52)], [(cx - 28, cy - 22), (cx - 10, cy - 42)],
                     [(cx + 12, cy - 46), (cx + 32, cy - 34)]], "#b8b0a8", sw=1.8, op=0.75)
    ears(d, cx, cy + 2, SKIN_TAN, w=0.93)
    # copper hoop earring on the near (left) ear
    ex, ey = cx - 40 * 0.93 - 6, cy + 20
    d.circle(ex, ey, 6, stroke=OUTLINE, stroke_width=4.6)
    d.circle(ex, ey, 6, stroke="#c8743a", stroke_width=2.6)
    d.circle(ex - 2, ey - 3, 1.3, fill="#ffd8b0", opacity=0.9)
    brows(d, cx, cy - 16, "#3a2418", thick=3.6, angle=-1.0, w=12)
    eyes(d, cx, cy - 3, iris="#3a7a9a", spacing=16, w=10, h=3.8, age=3, squint=0.4)
    nose(d, cx, cy - 2, SKIN_TAN, L=20, w=8)
    wrinkles(d, cx, cy, SKIN_TAN, fore=2, cheek=0.7, op=0.42)
    mouth(d, cx, cy + 27, SKIN_TAN, w=11, smile=0.9, lip="#9a4a3c")
    rng = random.Random(2903)
    for _ in range(14):   # sun freckles across the nose and cheeks
        x = cx + rng.uniform(-24, 24)
        y = cy + 6 + rng.uniform(-3, 6) + abs(x - cx) * 0.15
        d.circle(x, y, 0.9, fill=SKIN_TAN["dark"], opacity=0.6)
    d.path(smooth([(cx - 36, cy - 12), (cx - 38, cy + 10), (cx - 30, cy + 30)], closed=False), stroke="#ffd0a0", sw=2.2, op=0.35)
    frame(d, BRONZE, gem_col="#5ab0e0")


# ------------------------------------------------------------------------------------------ Agdao townsfolk

@portrait
def agdao_porter(d):
    """An Agdao porter: a tumpline across the brow carries the woven load on the back."""
    background(d, "#2a2414", haze="#e0a040", haze2="#7ab05a", motes="#ffe0a0", seed=294)
    vignette(d)
    cx, cy = 128, 126
    # the load: a tall woven pack behind the shoulders
    pack = smooth([(48, 214), (52, 74), (90, 54), (166, 54), (204, 74), (208, 214)], tension=0.25)
    d.path(pack, stroke=OUTLINE, sw=5)
    d.path(pack, fill=d.lin([(0, "#b08a50"), (0.5, "#7a5a30"), (1, "#3a2810")], 50, 54, 208, 214))
    for k in range(9):   # weave rows
        y = 70 + k * 16
        d.path(f"M{56 + (3 if k % 2 else 0)},{y} Q128,{y + 6} {200},{y}", stroke="#3a2810", sw=2, op=0.7)
        for j in range(10):
            x = 64 + j * 14 + (7 if k % 2 else 0)
            d.path(f"M{x},{y + 2} l0,10", stroke="#c8a46a", sw=1.4, op=0.55)
    d.path(smooth([(56, 70), (128, 58), (200, 70)], closed=False), stroke="#c83a2a", sw=4, op=0.85)
    # tumpline straps from the pack's top corners down to the brow
    for sx in (-1, 1):
        st = smooth([(cx + sx * 66, 66), (cx + sx * 54, cy - 46), (cx + sx * 42, cy - 30)], closed=False)
        d.path(st, stroke=OUTLINE, sw=9)
        d.path(st, stroke="#7a4a24", sw=6)
    tunic = dict(dark="#6a5a40", base="#c8b894", light="#efe4c8")
    shoulders(d, tunic, top=190, spread=1.04)
    for k, colr in enumerate(("#a83a24", "#2a8a7a", "#a83a24")):   # woven stripe band on the tunic
        y = 222 + k * 7
        d.path(f"M30,{y} Q128,{y - 18} 226,{y}", stroke=colr, sw=4, op=0.85)
    fret_band(d, 60, 244, 196, 5, "#3a2810", step=7)
    neck(d, cx, cy + 40, 30, 26, SKIN_DEEP)
    head(d, cx, cy, SKIN_DEEP, w=0.98, jaw=1.0, chin=0.95, top=0.98)
    hair_cap(d, cx, cy, "#141010", hi="#3a3030", w=0.98, top=0.98, line=0.95, sides=0.8)
    # the tumpline band across the forehead
    band = smooth([(cx - 44, cy - 28), (cx, cy - 36), (cx + 44, cy - 28)], closed=False)
    d.path(band, stroke=OUTLINE, sw=12)
    d.path(band, stroke="#8a5a2e", sw=8.5)
    d.path(band, stroke="#c08850", sw=2, op=0.6)
    for k in range(-3, 4):
        d.path(f"M{cx + k * 11 - 3},{f(cy - 34 + abs(k) * 1.2)} l6,0", stroke="#4a2e14", sw=1.4)
    ears(d, cx, cy + 2, SKIN_DEEP, w=0.98)
    brows(d, cx, cy - 15, "#141010", thick=4.2, angle=-2.4, w=12)
    eyes(d, cx, cy - 3, iris="#3a2a1a", spacing=17, w=10, h=4.0, squint=0.2)
    nose(d, cx, cy - 2, SKIN_DEEP, L=21, w=10)
    mouth(d, cx, cy + 28, SKIN_DEEP, w=12, smile=0.1, lip="#6a3020")
    wrinkles(d, cx, cy, SKIN_DEEP, fore=0, cheek=0.6, op=0.4)
    for (x, y) in ((cx + 30, cy - 18), (cx - 33, cy - 8)):   # sweat beads
        d.ellipse(x, y, 1.8, 2.8, fill="#ffffff", opacity=0.75)
    frame(d, BRONZE, gem_col="#e0a040")


@portrait
def agdao_vendor(d):
    """An Agdao market vendor in a woven headwrap, with a basket of fruit."""
    rng = random.Random(2905)
    background(d, "#2a1a16", haze="#e07a40", haze2="#e0c050", motes="#ffd8a0", seed=295)
    vignette(d)
    cx, cy = 124, 128
    dress = dict(dark="#3a120a", base="#9a3a1e", light="#d8744a")
    shoulders(d, dress, top=192, spread=1.04)
    shawl = smooth([(32, 256), (52, 206), (104, 192), (150, 240), (124, 256)], tension=0.35)
    d.path(shawl, stroke=OUTLINE, sw=4)
    d.path(shawl, fill=d.lin([(0, "#e0b860"), (1, "#8a6420")], 40, 196, 140, 256))
    for k in range(5):
        d.path(smooth([(44 + k * 6, 252), (62 + k * 9, 210), (106 + k * 6, 200)], closed=False), stroke="#2a8a7a" if k % 2 else "#a83a24", sw=2.4, op=0.8)
    neck(d, cx, cy + 40, 26, 26, SKIN)
    head(d, cx, cy, SKIN, w=0.94, jaw=0.92, chin=0.9, top=1.0)
    # the woven headwrap: stacked bands of patterned cloth, a twisted knot at the front
    bands = [("#a83a24", "#e0a040"), ("#2a8a7a", "#e8dcc0"), ("#d08a30", "#7a2a18"), ("#a83a24", "#2a8a7a"), ("#e0c890", "#a83a24")]
    for k, (c0, c1) in enumerate(bands):
        y0 = cy - 30 - k * 13
        w0 = 48 - k * 3
        bd = smooth([(cx - w0, y0 + 6), (cx - w0 + 2, y0 - 8), (cx, y0 - 18), (cx + w0 - 2, y0 - 8), (cx + w0, y0 + 6), (cx, y0 - 2)], tension=0.5)
        d.path(bd, stroke=OUTLINE, sw=4)
        d.path(bd, fill=d.lin([(0, lt(c0, 0.2)), (1, dk(c0, 0.35))], cx - w0, y0 - 18, cx + w0, y0 + 6))
        zz = []
        for j in range(13):
            t = j / 12
            x = cx - w0 + 6 + (2 * w0 - 12) * t
            y = y0 - 4 - 9 * math.sin(math.pi * t) + (3 if j % 2 else -1)
            zz.append((x, y))
        d.path(poly(zz, closed=False), stroke=c1, sw=1.8, op=0.9)
    knot = smooth([(cx - 12, cy - 40), (cx - 4, cy - 58), (cx + 10, cy - 54), (cx + 14, cy - 38), (cx, cy - 32)], tension=0.5)
    d.path(knot, stroke=OUTLINE, sw=3.4)
    d.path(knot, fill=d.lin([(0, "#e0a040"), (1, "#8a3a18")], cx - 12, cy - 58, cx + 14, cy - 32))
    d.path(smooth([(cx - 6, cy - 52), (cx + 2, cy - 40), (cx + 8, cy - 48)], closed=False), stroke="#5a2a10", sw=1.4)
    for sx in (-1, 1):   # dark hair visible below the wrap
        d.path(smooth([(cx + sx * 36, cy - 30), (cx + sx * 42, cy - 10), (cx + sx * 38, cy + 6), (cx + sx * 33, cy - 14)], tension=0.5),
               fill="#1e1410", stroke=OUTLINE, stroke_width=1.6)
    ears(d, cx, cy + 2, SKIN, w=0.94)
    for sx in (-1, 1):   # jade drop earrings
        ex = cx + sx * (40 * 0.94 + 6)
        d.path(f"M{f(ex)},{cy + 14} L{f(ex)},{cy + 22}", stroke=GOLD["base"], sw=1.6)
        d.path(smooth([(ex, cy + 20), (ex + 4, cy + 28), (ex, cy + 34), (ex - 4, cy + 28)], tension=0.6),
               fill=d.rad([(0, "#a8f0c8"), (1, "#1e6a46")], ex - 1, cy + 25, 7), stroke=OUTLINE, stroke_width=1.4)
    brows(d, cx, cy - 15, "#1e1410", thick=3.4, angle=1.5, w=12)
    eyes(d, cx, cy - 3, iris="#5a3a1a", spacing=16, w=10, h=3.8, squint=0.3, age=1)
    nose(d, cx, cy - 2, SKIN, L=19, w=8)
    mouth(d, cx, cy + 27, SKIN, w=13, smile=1.8, lip="#a8483a")
    wrinkles(d, cx, cy, SKIN, fore=0, cheek=0.75, op=0.35)
    # a basket of fruit held up at the right
    bx, by = 196, 210
    for _ in range(9):
        fx, fy = bx + rng.uniform(-26, 26), by - 14 + rng.uniform(-10, 4)
        col = rng.choice(("#e07a2a", "#c8342a", "#9ab03a", "#e0b030"))
        r = rng.uniform(7, 10)
        d.circle(fx, fy, r, fill=d.rad([(0, lt(col, 0.45)), (1, dk(col, 0.3))], fx - r * 0.3, fy - r * 0.3, r * 1.2), stroke=OUTLINE, stroke_width=2)
        d.path(f"M{f(fx)},{f(fy - r)} l2,-4", stroke="#3a5a1a", sw=1.6)
    bk = smooth([(bx - 40, by - 10), (bx + 40, by - 10), (bx + 32, by + 34), (bx - 32, by + 34)], tension=0.2)
    d.path(bk, stroke=OUTLINE, sw=4)
    d.path(bk, fill=d.lin([(0, "#c8a060"), (1, "#5a3a18")], bx, by - 10, bx, by + 34))
    for k in range(4):
        y = by - 2 + k * 9
        d.path(f"M{bx - 38 + k * 2},{y} L{bx + 38 - k * 2},{y}", stroke="#3a2410", sw=1.6, op=0.7)
    for j in range(8):
        x = bx - 32 + j * 9
        d.path(f"M{x},{by - 8} l{(j - 3.5) * -0.4:.1f},40", stroke="#e0c890", sw=1.2, op=0.5)
    frame(d, BRONZE, gem_col="#ff9a40")


@portrait
def agdao_elder(d):
    """An Agdao elder with a carved cane and a feather stole."""
    rng = random.Random(2906)
    background(d, "#16261e", haze="#5ab08a", haze2="#e0a040", motes="#e8ffd8", seed=296)
    vignette(d)
    cx, cy = 132, 120
    linen = dict(dark="#4a3e2a", base="#a89878", light="#e8dcc0")
    # the cane behind the near shoulder: carved shaft, a stepped head with a jade stud
    d.path("M44,256 L54,128", stroke=OUTLINE, sw=12)
    d.path("M44,256 L54,128", stroke=d.lin([(0, "#7a5230"), (1, "#3a2410")], 40, 0, 58, 0), sw=8)
    for k in range(6):
        y = 150 + k * 18
        x = 54 - (y - 128) * 0.078
        d.path(f"M{f(x - 4)},{y} l8,-3", stroke="#2a1808", sw=1.6, op=0.8)
    chead = poly([(40, 132), (40, 120), (46, 120), (46, 112), (62, 112), (62, 120), (68, 120), (68, 132)])
    d.path(chead, fill=d.lin([(0, "#a07a4a"), (1, "#4a2e14")], 40, 112, 68, 132), stroke=OUTLINE, stroke_width=3)
    d.circle(54, 116, 4, fill=d.rad([(0, "#c8ffe0"), (1, "#2a8a5a")], 53, 115, 5), stroke=OUTLINE, stroke_width=1.4)
    shoulders(d, linen, top=192, spread=1.04)
    # the feather stole: rows of overlapping feathers, a scarlet edge row
    rows = [(238, 15, "#c8342a"), (226, 13, "#2a8a6a"), (214, 12, "#3aa08a"), (203, 11, "#2a8a6a")]
    for y, n, col in rows:
        span = 96 + (238 - y) * -0.8
        for k in range(n):
            t = k / (n - 1)
            x = cx - 4 - span + 2 * span * t
            yy = y - 12 * math.sin(math.pi * t) + rng.uniform(-1, 1)
            if y < 210 and abs(x - cx) < 20:
                continue
            fp = smooth([(x - 7, yy - 10), (x + 7, yy - 10), (x + 6, yy + 6), (x, yy + 14), (x - 6, yy + 6)], tension=0.6)
            d.path(fp, stroke=OUTLINE, sw=2.4)
            d.path(fp, fill=d.lin([(0, lt(col, 0.25)), (1, dk(col, 0.35))], x, yy - 10, x, yy + 14))
            d.path(f"M{f(x)},{f(yy - 8)} L{f(x)},{f(yy + 11)}", stroke=lt(col, 0.5), sw=0.9, op=0.7)
    neck(d, cx, cy + 40, 26, 26, SKIN_ELDER)
    head(d, cx, cy, SKIN_ELDER, w=0.96, jaw=0.9, chin=0.88, top=1.02)
    # white hair drawn back to a topknot pinned with jade
    hair_cap(d, cx, cy, "#d8d4cc", hi="#ffffff", w=0.96, top=1.02, line=1.25, sides=0.5)
    tk = smooth([(cx - 14, cy - 56), (cx - 14, cy - 72), (cx, cy - 80), (cx + 14, cy - 72), (cx + 14, cy - 56)], tension=0.5)
    d.path(tk, stroke=OUTLINE, sw=3.6)
    d.path(tk, fill=d.rad([(0, "#ffffff"), (1, "#a8a49c")], cx - 4, cy - 74, 18))
    d.path(f"M{cx - 22},{cy - 70} L{cx + 22},{cy - 64}", stroke=OUTLINE, sw=4.6)
    d.path(f"M{cx - 22},{cy - 70} L{cx + 22},{cy - 64}", stroke="#3aa080", sw=2.4)
    d.circle(cx + 22, cy - 64, 3, fill="#a8f0c8", stroke=OUTLINE, stroke_width=1.2)
    ears(d, cx, cy + 2, SKIN_ELDER, w=0.96)
    wrinkles(d, cx, cy, SKIN_ELDER, fore=4, cheek=0.95, eye_bags=True, op=0.55)
    brows(d, cx, cy - 16, "#f0ece4", thick=4.4, angle=2.4, w=13)
    eyes(d, cx, cy - 3, iris="#4a3a2a", spacing=16, w=9, h=3.2, age=3, squint=0.35)
    nose(d, cx, cy - 2, SKIN_ELDER, L=24, w=10)
    mouth(d, cx, cy + 28, SKIN_ELDER, w=12, smile=1.2, lip="#8a4a3a")
    # a carved bone-and-jade pendant on a cord
    d.path(f"M{cx - 18},{cy + 64} Q{cx},{cy + 92} {cx + 18},{cy + 64}", stroke="#5a3a20", sw=1.6)
    pend = poly([(cx - 7, cy + 88), (cx + 7, cy + 88), (cx + 7, cy + 96), (cx, cy + 102), (cx - 7, cy + 96)])
    d.path(pend, fill=d.lin([(0, "#a8f0c8"), (1, "#1e6a46")], cx, cy + 88, cx, cy + 102), stroke=OUTLINE, stroke_width=1.8)
    # gnarled fingers round the cane
    fingers(d, 52, 148, 4, SKIN_ELDER, dx=0, step=10, L=18)
    frame(d, dict(dark="#2a2010", base="#a08a4a", light="#f0e4b0"), gem_col="#5ad0a0")


# ------------------------------------------------------------------------------------------ output

IMPORT_TEMPLATE = "lape.svg.import"
MARK = "<!-- bh029_portraits.py -->"


def write_import(name):
    src = os.path.join(OUT, IMPORT_TEMPLATE)
    with open(src, encoding="utf-8") as fh:
        txt = fh.read()
    res = f"res://assets/ui/portraits/{name}.svg"
    md5 = hashlib.md5(res.encode()).hexdigest()
    lines = []
    for line in txt.splitlines():
        if line.startswith("uid="):
            continue
        line = line.replace("res://assets/ui/portraits/lape.svg", res)
        line = line.replace("lape.svg-d3337495e1120d567f51f0df11126df6", f"{name}.svg-{md5}")
        lines.append(line)
    with open(os.path.join(OUT, name + ".svg.import"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    paths = []
    for name, fn in PORTRAITS.items():
        p = os.path.join(OUT, name + ".svg")
        if os.path.exists(p) and "--force" not in sys.argv:
            existing = open(p, encoding="utf-8").read()
            if MARK not in existing:
                raise SystemExit(f"refusing to overwrite existing portrait {name} (not written by this script)")
        svg = fn().svg()
        head_end = svg.index(">") + 1
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(svg[:head_end] + "\n" + MARK + svg[head_end:])
        write_import(name)
        paths.append(p)
        print("WROTE", p)
    try:
        from bh003_render import render_file
        from PIL import Image, ImageDraw
    except Exception:
        return paths
    try:
        ims = [(os.path.basename(p)[:-4], render_file(p, 256)) for p in paths]
    except RuntimeError as e:
        print("preview skipped:", e)
        return paths
    os.makedirs(EVI, exist_ok=True)
    sheet = Image.new("RGB", (len(ims) * 266 + 10, 300), (22, 18, 28))
    dr = ImageDraw.Draw(sheet)
    for i, (nm, im) in enumerate(ims):
        sheet.paste(im, (10 + i * 266, 10), im)
        dr.text((14 + i * 266, 274), nm, fill=(230, 214, 180))
    sheet.save(os.path.join(EVI, "portraits.png"))
    big = Image.new("RGB", (3 * 520, 2 * 520), (22, 18, 28))
    for i, p in enumerate(paths):
        big.paste(render_file(p, 512), ((i % 3) * 520 + 4, (i // 3) * 520 + 4))
    big.save(os.path.join(EVI, "portraits_512.png"))
    print("WROTE", os.path.join(EVI, "portraits.png"))
    return paths


if __name__ == "__main__":
    main()
