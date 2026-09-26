"""bh-003 hero tier emblems (game/assets/ui/tiers/tier_<x>.svg, viewBox 0 0 128 128).

Progression (LORE §5/§8): iron -> bronze -> silver -> gold -> azure -> crimson -> twin-moon violet-silver -> prismatic Aether.
Plain and dark at E, increasingly ornate and luminous towards SSS. Letters are glyph outlines (no <text>), drawn big with a
heavy dark outline so they survive the 28 px HUD size.
"""
from __future__ import annotations

import math
import random

from bh_svg import Doc, OUTLINE, f, poly, smooth, mix, lt, dk, star_pts, polar, circle_path, ribbon, taper, qbez
from bh003_text import text_path, cap_height, SERIF_BOLD

TIERS = {}
C = 64.0


def tier(key):
    def deco(fn):
        def build():
            d = Doc(128, 128, name="tier_" + key)
            fn(d)
            return d
        TIERS["tier_" + key] = build
        return fn
    return deco


# ------------------------------------------------------------------------------------------ helpers

def letters(d, text, cy, size, top, bot, sx=1.0, tracking=0.0, ow=5.5, oc=OUTLINE, shadow=True, rim=None, cx=C):
    """Big outlined glyphs, vertically centred on cy (cap height)."""
    base = cy + cap_height(size) / 2
    dd, _ = text_path(text, size, cx, base, sx=sx, tracking=tracking)
    if shadow:
        with d.g(f"translate(1.5 2.5)"):
            d.path(dd, fill=oc, stroke=oc, sw=ow * 2, op=0.55)
    d.path(dd, fill=oc, stroke=oc, sw=ow * 2)
    if rim:
        d.path(dd, fill="none", stroke=rim, sw=2.4)
    d.path(dd, fill=d.lin([(0, top), (0.55, mix(top, bot, 0.45)), (1, bot)], 0, cy - cap_height(size) / 2, 0, base))
    return dd


def heater(cx, top, w, h):
    l, r = cx - w / 2, cx + w / 2
    t = top
    return (f"M{f(l)},{f(t)} Q{f(cx)},{f(t + h * 0.06)} {f(r)},{f(t)} L{f(r)},{f(t + h * 0.42)} "
            f"C{f(r)},{f(t + h * 0.76)} {f(cx + w * 0.22)},{f(t + h * 0.9)} {f(cx)},{f(t + h)} "
            f"C{f(cx - w * 0.22)},{f(t + h * 0.9)} {f(l)},{f(t + h * 0.76)} {f(l)},{f(t + h * 0.42)} Z")


def kite(cx, top, w, h):
    l, r = cx - w / 2, cx + w / 2
    t = top
    return (f"M{f(l)},{f(t + h * 0.16)} C{f(l + w * 0.06)},{f(t - h * 0.03)} {f(r - w * 0.06)},{f(t - h * 0.03)} {f(r)},{f(t + h * 0.16)} "
            f"C{f(r)},{f(t + h * 0.42)} {f(cx + w * 0.18)},{f(t + h * 0.8)} {f(cx)},{f(t + h)} "
            f"C{f(cx - w * 0.18)},{f(t + h * 0.8)} {f(l)},{f(t + h * 0.42)} {f(l)},{f(t + h * 0.16)} Z")


def rivet(d, x, y, r, pal):
    d.circle(x, y, r + 1.2, fill=OUTLINE)
    d.circle(x, y, r, fill=d.rad([(0, pal[2]), (0.6, pal[1]), (1, pal[0])], x - r * 0.4, y - r * 0.4, r * 1.3))


def crescent_pts(cx, cy, r, off, r2, facing, n=28):
    """Crescent = circle(c, r) minus circle(c + off*dir(facing), r2). Points of the remaining lune."""
    ux, uy = math.cos(facing), math.sin(facing)
    ox, oy = cx + off * ux, cy + off * uy
    # intersection angle on the outer circle, measured from the facing direction
    cos_t = (r * r + off * off - r2 * r2) / (2 * r * off)
    t = math.acos(max(-1.0, min(1.0, cos_t)))
    pts = []
    for i in range(n):  # outer arc: from +t going the long way round to -t (2pi - 2t)
        a = facing + t + (2 * math.pi - 2 * t) * i / (n - 1)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    p_end, p_start = pts[-1], pts[0]
    a1 = math.atan2(p_end[1] - oy, p_end[0] - ox)
    a0 = math.atan2(p_start[1] - oy, p_start[0] - ox)
    # inner arc: back from p_end to p_start through the side facing the outer circle's centre
    da = (a0 - a1) % (2 * math.pi)
    if da > math.pi:
        da -= 2 * math.pi
    # choose the arc passing nearest the outer centre (the "inside" of the bite)
    mid_a = a1 + da / 2
    mid = (ox + r2 * math.cos(mid_a), oy + r2 * math.sin(mid_a))
    if math.hypot(mid[0] - cx, mid[1] - cy) > r:
        da = da - 2 * math.pi if da > 0 else da + 2 * math.pi
    for i in range(1, n - 1):
        a = a1 + da * i / (n - 1)
        pts.append((ox + r2 * math.cos(a), oy + r2 * math.sin(a)))
    return pts


def rays(d, cx, cy, n, r0, r1, w, cols, op=1.0, rot0=-math.pi / 2, outline=True):
    for i in range(n):
        a = rot0 + i * 2 * math.pi / n
        col = cols[i % len(cols)]
        rr = r1[i % len(r1)] if isinstance(r1, (list, tuple)) else r1
        ww = w[i % len(w)] if isinstance(w, (list, tuple)) else w
        p0 = polar(cx, cy, r0, a - ww / r0)
        p1 = polar(cx, cy, rr, a)
        p2 = polar(cx, cy, r0, a + ww / r0)
        if outline:
            d.path(poly([p0, p1, p2]), stroke=OUTLINE, sw=3.2, op=op)
        d.path(poly([p0, p1, p2]), fill=col, op=op)


# ------------------------------------------------------------------------------------------ unranked

@tier("unranked")
def unranked(d):
    d.circle(C, C, 44, stroke=OUTLINE, stroke_width=16)
    d.circle(C, C, 44, stroke=d.lin([(0, "#a4a6aa"), (1, "#5c5e62")], 0, 20, 0, 108), stroke_width=9)
    d.circle(C, C, 48, stroke="#c8cacc", stroke_width=1.2, opacity=0.35)
    d.path("M44,64 L84,64", stroke=OUTLINE, sw=15)
    d.path("M44,64 L84,64", stroke=d.lin([(0, "#b4b6ba"), (1, "#7a7c80")], 0, 58, 0, 70), sw=8)


# ------------------------------------------------------------------------------------------ E  iron ring-shield

IRON = ("#1a1d21", "#50565d", "#8e949a")


@tier("e")
def tier_e(d):
    d.circle(C, C, 58, fill=OUTLINE)
    d.circle(C, C, 55, fill=d.lin([(0, IRON[2]), (0.45, IRON[1]), (1, IRON[0])], 20, 10, 108, 118))
    d.circle(C, C, 55, stroke="#000000", stroke_width=1, opacity=0.5)
    # recessed dished face
    d.circle(C, C, 42, fill=OUTLINE)
    d.circle(C, C, 40, fill=d.rad([(0, "#4a4f55"), (0.7, "#33373c"), (1, "#202327")], 56, 52, 50))
    # dull scratches + pitting
    rng = random.Random(4)
    for _ in range(7):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(8, 34)
        x, y = polar(C, C, rr, a)
        L = rng.uniform(5, 11)
        b = rng.uniform(0, math.pi)
        d.path(f"M{f(x)},{f(y)} L{f(x + L * math.cos(b))},{f(y + L * math.sin(b))}", stroke="#6a7076", sw=0.9, op=0.5)
    for i in range(10):
        a = -math.pi / 2 + i * 2 * math.pi / 10
        x, y = polar(C, C, 48.5, a)
        rivet(d, x, y, 3.2, ("#202428", "#5e646a", "#a8aeb4"))
    letters(d, "E", 66, 70, "#e4e6e8", "#8e949a", ow=5)


# ------------------------------------------------------------------------------------------ D  bronze kite shield

BRZ = ("#3a200c", "#9a6030", "#e8b47c")


@tier("d")
def tier_d(d):
    outer = kite(C, 6, 92, 118)
    d.path(outer, stroke=OUTLINE, sw=8)
    d.path(outer, fill=d.lin([(0, BRZ[2]), (0.45, BRZ[1]), (1, BRZ[0])], 20, 6, 108, 124))
    inner = kite(C, 15, 74, 96)
    d.path(inner, stroke=OUTLINE, sw=3)
    d.path(inner, fill=d.lin([(0, "#6a3e1c"), (0.6, "#4a2a12"), (1, "#2c180a")], 30, 15, 98, 111))
    d.path(smooth([(34, 22), (50, 14), (70, 13)], closed=False), stroke="#ffe0b0", sw=2, op=0.5)
    for (x, y) in ((24, 24), (104, 24), (C, 116)):
        rivet(d, x, y, 3.2, (BRZ[0], BRZ[1], "#ffe0b0"))
    letters(d, "D", 58, 72, "#fff0d8", "#d09a60", ow=5)


# ------------------------------------------------------------------------------------------ C  silver crest + star

SILV = ("#3a4048", "#a8b2bc", "#ffffff")


@tier("c")
def tier_c(d):
    d.glow(C, 20, 22, "#dfe8f0", 0.35)
    # little side flourishes
    for sx in (-1, 1):
        fl = smooth([(C + sx * 40, 34), (C + sx * 56, 34), (C + sx * 58, 48), (C + sx * 50, 58)], closed=False)
        d.path(fl, stroke=OUTLINE, sw=6)
        d.path(fl, stroke=SILV[1], sw=3)
    outer = heater(C, 28, 90, 96)
    d.path(outer, stroke=OUTLINE, sw=8)
    d.path(outer, fill=d.lin([(0, SILV[2]), (0.4, SILV[1]), (1, SILV[0])], 20, 28, 108, 124))
    inner = heater(C, 36, 74, 80)
    d.path(inner, stroke=OUTLINE, sw=2.4)
    d.path(inner, fill=d.lin([(0, "#3e4a58"), (1, "#161c24")], 0, 36, 0, 116))
    d.path(f"M26,33 Q{C},37 102,33", stroke="#ffffff", sw=1.6, op=0.7)
    # the one star
    st = star_pts(C, 17, 5, 15, 6.4)
    d.path(poly(st), stroke=OUTLINE, sw=6)
    d.path(poly(st), fill=d.lin([(0, "#ffffff"), (0.6, "#c8d2dc"), (1, "#7a8490")], C, 2, C, 32))
    letters(d, "C", 72, 66, "#ffffff", "#9aa6b2", ow=5)


# ------------------------------------------------------------------------------------------ B  gold laurel shield

GLD = ("#5a3a0c", "#d0a032", "#fff0b0")


def laurel(d, sx):
    stem = qbez((C + sx * 6, 122), (C + sx * 70, 104), (C + sx * 46, 14), n=20)
    d.path(poly(stem, closed=False), stroke=OUTLINE, sw=6)
    d.path(poly(stem, closed=False), stroke=GLD[1], sw=3)
    for i in range(2, 20, 2):
        x, y = stem[i]
        nx, ny = stem[min(i + 1, 19)]
        a = math.atan2(ny - y, nx - x)
        for side in (-1, 1):
            la = a + side * 0.75
            L = 13 - i * 0.25
            tip = (x + L * math.cos(la), y + L * math.sin(la))
            mid = ((x + tip[0]) / 2, (y + tip[1]) / 2)
            pa = la + math.pi / 2
            w = 4.2
            leaf = f"M{f(x)},{f(y)} Q{f(mid[0] + w * math.cos(pa))},{f(mid[1] + w * math.sin(pa))} {f(tip[0])},{f(tip[1])} Q{f(mid[0] - w * math.cos(pa))},{f(mid[1] - w * math.sin(pa))} {f(x)},{f(y)} Z"
            d.path(leaf, stroke=OUTLINE, sw=3.2)
            d.path(leaf, fill=d.lin([(0, GLD[2]), (1, GLD[1] if side < 0 else "#a07420")], x, y, tip[0], tip[1]))


@tier("b")
def tier_b(d):
    d.glow(C, 62, 64, "#ffd070", 0.25)
    laurel(d, -1)
    laurel(d, 1)
    outer = heater(C, 16, 78, 96)
    d.path(outer, stroke=OUTLINE, sw=8)
    d.path(outer, fill=d.lin([(0, GLD[2]), (0.4, GLD[1]), (1, GLD[0])], 26, 16, 102, 112))
    inner = heater(C, 24, 62, 78)
    d.path(inner, stroke=OUTLINE, sw=2.4)
    d.path(inner, fill=d.lin([(0, "#6a3a0a"), (1, "#2a1404")], 0, 24, 0, 102))
    d.path(f"M30,21 Q{C},25 98,21", stroke="#ffffff", sw=1.6, op=0.7)
    # tie ribbon crossing the stems
    rb = f"M{C - 16},116 Q{C},110 {C + 16},116 L{C + 12},124 Q{C},119 {C - 12},124 Z"
    d.path(rb, stroke=OUTLINE, sw=3)
    d.path(rb, fill="#b01a2a")
    letters(d, "B", 58, 64, "#fffbe8", "#e8b440", ow=5)


# ------------------------------------------------------------------------------------------ A  azure star

AZ = ("#06205a", "#1e64d8", "#8cc8ff")


@tier("a")
def tier_a(d):
    d.glow(C, C, 64, "#4a9aff", 0.5)
    st = star_pts(C, C, 8, 62, 38, rot0=-math.pi / 2)
    d.path(poly(st), stroke=OUTLINE, sw=8)
    d.path(poly(st), stroke=d.lin([(0, "#ffffff"), (0.5, "#b8c4d0"), (1, "#6a7480")], 0, 0, 128, 128), sw=5)
    # faceted azure body
    n = len(st)
    for i in range(n):
        a, b = st[i], st[(i + 1) % n]
        mx, my = (a[0] + b[0]) / 2 - C, (a[1] + b[1]) / 2 - C
        t = ((-(mx * 0.6 + my * 0.8) / (math.hypot(mx, my) or 1)) + 1) / 2
        col = mix(AZ[0], AZ[2], 0.15 + 0.8 * t)
        d.path(poly([(C, C), a, b]), fill=col, stroke=col, sw=0.5)
    d.circle(C, C, 35, fill=OUTLINE)
    d.circle(C, C, 32.5, fill=d.rad([(0, "#1a4aa8"), (1, "#061a48")], 58, 56, 38))
    d.circle(C, C, 32.5, stroke="#dfe8f0", stroke_width=1.8)
    d.sparkle(C, 8, 6, "#ffffff", op=0.9)
    letters(d, "A", 65, 60, "#ffffff", "#9cd0ff", ow=5)


# ------------------------------------------------------------------------------------------ S  crimson sunburst

@tier("s")
def tier_s(d):
    d.glow(C, C, 64, "#ff5a2a", 0.6, core="#ffd070")
    rays(d, C, C, 16, 34, [63, 50], [10, 7.5], ["#c8182c", "#ffc038"])
    rays(d, C, C, 16, 34, [57, 45], [3.8, 3], ["#ff6a5a", "#fff0a0"], outline=False, op=0.8)
    d.circle(C, C, 41, fill=OUTLINE)
    d.circle(C, C, 38, fill=d.lin([(0, "#ffe9a0"), (0.5, "#d0a032"), (1, "#6a3a0c")], 0, 26, 0, 102))
    d.circle(C, C, 33, fill=OUTLINE)
    d.circle(C, C, 31, fill=d.rad([(0, "#c8203a"), (0.7, "#7a0a1a"), (1, "#3a0610")], 58, 54, 38))
    letters(d, "S", 65, 60, "#fffbe0", "#ffc040", ow=5)


# ------------------------------------------------------------------------------------------ SS  twin moon

@tier("ss")
def tier_ss(d):
    d.glow(C, C, 64, "#a070ff", 0.55)
    R = 47
    d.circle(C, C, R + 3, fill=OUTLINE)
    d.circle(C, C, R, fill=d.rad([(0, "#2e1858"), (0.7, "#140a2e"), (1, "#06030e")], C, 56, R + 6))
    rng = random.Random(9)
    for _ in range(22):
        a = rng.uniform(0, 2 * math.pi)
        rr = math.sqrt(rng.uniform(0.05, 1)) * (R - 5)
        x, y = polar(C, C, rr, a)
        d.circle(x, y, rng.uniform(0.6, 1.4), fill="#e8e0ff", opacity=rng.uniform(0.5, 0.95))
    for (x, y, r) in ((C, 24, 3.4), (C - 4, 104, 2.6), (C + 22, 30, 2.0)):
        d.sparkle(x, y, r * 1.8, "#ffffff", op=0.95)
    d.circle(C, C, R, stroke=d.lin([(0, "#f4f0ff"), (0.5, "#b8a0e8"), (1, "#5a3a9a")], 0, 14, 0, 114), stroke_width=3.4)
    # two crescent moons, backs outward, horns reaching round the letters
    for sx in (-1, 1):
        mc = (C + sx * 33, C)
        d.glow(mc[0] + sx * 6, C, 30, "#c8b4ff", 0.35)
        pts = crescent_pts(mc[0], mc[1], 30, 14, 27, 0 if sx < 0 else math.pi, n=34)
        dd = poly(pts)
        d.path(dd, stroke=OUTLINE, sw=6)
        d.path(dd, fill=d.lin([(0, "#ffffff"), (0.4, "#dcd2ff"), (1, "#6a4ab8")], C + sx * 62, 32, C + sx * 40, 100))
    letters(d, "SS", 64, 54, "#ffffff", "#d8ccff", sx=0.78, tracking=-1, ow=4.5)


# ------------------------------------------------------------------------------------------ SSS  Aether crown

PRISM = ["#b8fbff", "#ffffff", "#ffc8f4", "#fff2b0", "#c8d4ff"]


@tier("sss")
def tier_sss(d):
    d.glow(C, 60, 64, "#7ff3ff", 0.75, core="#ffffff")
    # prismatic light rays
    rays(d, C, 60, 20, 18, [64, 52], [4.2, 3], PRISM, outline=False, op=0.8)
    d.circle(C, 60, 46, stroke="#ffffff", stroke_width=1.4, opacity=0.6)
    d.circle(C, 60, 40, stroke="#b8fbff", stroke_width=3, opacity=0.35)
    # crown: 5 points with orbs, broad band
    top, band_t, band_b = 20, 56, 114
    xs = [14, 32, 64, 96, 114]
    peaks = [30, 18, 6, 18, 30]
    pts = [(12, band_b), (12, band_t - 8)]
    for i, (x, py) in enumerate(zip(xs, peaks)):
        if i > 0:
            vx = (xs[i - 1] + x) / 2
            pts.append((vx, band_t - 4))
        pts.append((x, py + 6))
    pts += [(116, band_t - 8), (116, band_b)]
    crown = poly(pts)
    d.path(crown, stroke=OUTLINE, sw=8)
    d.path(crown, fill=d.lin([(0, "#ffffff"), (0.35, "#d8fdff"), (0.7, "#7ff3ff"), (1, "#2aa8c8")], 0, 6, 0, band_b))
    # prism sheen stripes on the points
    for i, x in enumerate(xs):
        d.path(poly([(x, peaks[i] + 8), (x + 3, band_t - 6), (x - 3, band_t - 6)]), fill=PRISM[(i + 2) % 5], op=0.7)
    for i, (x, py) in enumerate(zip(xs, peaks)):
        r = 6 if i == 2 else 4.6
        d.glow(x, py, r * 3, "#ffffff", 0.6)
        d.circle(x, py, r + 1.6, fill=OUTLINE)
        d.circle(x, py, r, fill=d.rad([(0, "#ffffff"), (0.5, PRISM[(i * 2) % 5]), (1, "#4ac8e0")], x - 1.5, py - 1.5, r * 1.3))
    # band panel for the letters
    band = f"M12,{band_t} Q{C},{band_t - 6} 116,{band_t} L116,{band_b} Q{C},{band_b - 6} 12,{band_b} Z"
    d.path(band, stroke=OUTLINE, sw=5)
    d.path(band, fill=d.lin([(0, "#1a4a8a"), (1, "#081838")], 0, band_t, 0, band_b))
    d.path(f"M12,{band_t} Q{C},{band_t - 6} 116,{band_t}", stroke="#ffffff", sw=2.2)
    d.path(f"M12,{band_b} Q{C},{band_b - 6} 116,{band_b}", stroke="#b8fbff", sw=2.2)
    d.sparkle(20, 12, 7, "#ffffff", op=0.95)
    d.sparkle(110, 116, 6, "#ffffff", op=0.9)
    letters(d, "SSS", 84, 58, "#ffffff", "#9cf4ff", sx=0.72, tracking=-2, ow=4.5)
