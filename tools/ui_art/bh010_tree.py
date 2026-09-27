"""bh-010 tree backdrops for the new heroes (1600x900, opaque), same family as raster_tree.backdrop (knight/mage):
radial base, noise haze, engraved rune ring with ticks, class engraving, constellations, star dust, grain, vignette.

  * tree_bg_ranger       forest dusk: green-teal haze with an amber dusk glow, engraved longbow + crossed arrows,
                         drifting leaves, pine silhouettes along the lower edge.
  * tree_bg_shadowblade  moonless violet haze: smoke banks, engraved crossed daggers, a faint crescent sigil.

Registered in raster_all.py under folder "tree" (registry TREE10).
"""
from __future__ import annotations

import math

import numpy as np

from rast import Canvas, C, cov, sd_circle, sd_poly, sd_stroke, union, paint, catmull, arc, xf, leaf, fnoise, rgrad, F
from raster_orn import rune_strokes

TREE10 = {}

W, H = 1600, 900
CX, CY = W * 0.5, H * 0.52


def _line(cv, sd, color, op, w=0.8):
    paint(cv, np.abs(sd) - w, color, op)


def _rune_ring(cv, rng, line_c):
    for r in (300, 360, 420):
        _line(cv, sd_circle(cv, CX, CY, r), line_c, 0.11, 0.6)
    ticks = []
    for a in np.linspace(0, 2 * math.pi, 96, endpoint=False):
        r2 = 372 if int(a * 10) % 3 == 0 else 366
        ticks.append(sd_stroke(cv, [(CX + 360 * math.cos(a), CY + 360 * math.sin(a)), (CX + r2 * math.cos(a), CY + r2 * math.sin(a))], 1.0))
    paint(cv, union(*ticks), line_c, 0.12)
    runes = []
    for a in np.linspace(0, 2 * math.pi, 24, endpoint=False):
        for ln in rune_strokes(rng, CX + 395 * math.cos(a), CY + 395 * math.sin(a), 16):
            runes.append(sd_stroke(cv, ln, 1.4))
    paint(cv, union(*runes), line_c, 0.12)


def _constellations(cv, rng, line_c, star_c):
    for _ in range(7):
        x0, y0 = rng.uniform(120, W - 120), rng.uniform(90, H - 90)
        pts = [(x0, y0)]
        for _ in range(rng.integers(3, 6)):
            a = rng.uniform(0, 2 * math.pi)
            dd = rng.uniform(40, 110)
            pts.append((pts[-1][0] + dd * math.cos(a), pts[-1][1] + dd * math.sin(a)))
        paint(cv, sd_stroke(cv, pts, 1.0), line_c, 0.12)
        for (x, y) in pts:
            cv.glow(cov(cv, sd_circle(cv, x, y, 2.2)), star_c, 4, 0.5)
            paint(cv, sd_circle(cv, x, y, 1.8), "#ffffff", 0.8)


def _dust_grain_vignette(cv, rng, dust_c, seed):
    for _ in range(420):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.uniform(0.4, 1.3)
        a = rng.uniform(0.1, 0.5)
        sl = cv.region(x - 3, y - 3, x + 3, y + 3, 0)
        if sl is None:
            continue
        d = np.hypot(cv.X[sl] - x, cv.Y[sl] - y)
        m = np.clip(r + 0.5 - d, 0, 1) * a
        cv.rgb[sl] = cv.rgb[sl] * (1 - m[..., None]) + C(dust_c) * m[..., None]
    g = fnoise(H, W, seed, beta=0.5, lo=1)
    cv.rgb = np.clip(cv.rgb * (1 + g[..., None] * 0.035), 0, 1)
    d = np.hypot((cv.X - W / 2) / (W / 2), (cv.Y - H / 2) / (H / 2))
    cv.rgb *= (1 - np.clip((d - 0.6) / 0.8, 0, 1) ** 1.5 * 0.75)[..., None]
    cv.a[:] = 1.0


def _arrow(cv, p0, p1, line_c, op, head=34, shaft=5):
    """Engraved arrow outline from nock p0 to tip p1 with fletching."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    shaft_pts = [(0, -shaft), (L - head, -shaft), (L - head, shaft), (0, shaft)]
    tip = [(L - head - 6, -16), (L, 0), (L - head - 6, 16), (L - head + 4, 0)]
    fl = [[(4, -shaft), (70, -shaft), (40, -26), (-6, -30)], [(4, shaft), (70, shaft), (40, 26), (-6, 30)]]
    for poly in [shaft_pts, tip] + fl:
        _line(cv, sd_poly(cv, xf(poly, a=ang, tx=x0, ty=y0), margin=4), line_c, op)


def _dagger(cv, p0, p1, line_c, op):
    """Engraved dagger outline: pommel at p0, tip at p1."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    grip = L * 0.26
    blade = [(grip + 14, -26), (L * 0.72, -22), (L, 0), (L * 0.72, 22), (grip + 14, 26)]
    guard = [(grip, -70), (grip + 14, -76), (grip + 14, 76), (grip, 70)]
    handle = [(18, -12), (grip, -14), (grip, 14), (18, 12)]
    for poly in (blade, guard, handle):
        _line(cv, sd_poly(cv, xf(poly, a=ang, tx=x0, ty=y0), margin=4), line_c, op)
    _line(cv, sd_circle(cv, *xf([(8, 0)], a=ang, tx=x0, ty=y0)[0], 18), line_c, op)
    fuller = xf([(grip + 26, 0), (L * 0.8, 0)], a=ang, tx=x0, ty=y0)
    paint(cv, sd_stroke(cv, fuller, 1.0), line_c, op * 0.9)


def ranger_backdrop():
    cv = Canvas(W, H, ss=1)
    rng = np.random.default_rng(31)
    base = rgrad(cv, CX, H * 0.45, W * 0.75, [(0, "#10200f"), (0.55, "#070e08"), (1, "#020403")], sy=1.6)
    cv.over(base, np.ones((cv.H, cv.W), F))
    # dusk: amber glow low on the horizon, teal up top
    dusk = np.clip((cv.Y - H * 0.35) / (H * 0.65), 0, 1)
    cv.over("#9a6420", dusk ** 2, 0.34)
    n1 = fnoise(H, W, 41, beta=3.0, lo=1)
    n2 = fnoise(H, W, 43, beta=2.2, lo=2)
    cv.over("#2a6a3a", np.clip(n1 * 0.5 + 0.2, 0, 1) ** 2, 0.18)
    cv.over("#1a6a6a", np.clip(n2 * 0.4, 0, 1) ** 3, 0.12)
    line_c = "#c8c88a"
    _rune_ring(cv, rng, line_c)
    # engraved longbow (vertical) with string, and two crossed arrows through the centre
    limb = catmull([(CX - 40, 120), (CX + 30, 200), (CX + 90, 380), (CX + 96, 470), (CX + 90, 560), (CX + 30, 740), (CX - 40, 820)], 10)
    _line(cv, sd_stroke(cv, limb, 14, 14), line_c, 0.10)
    _line(cv, sd_stroke(cv, [(CX + 76, 430), (CX + 112, 430), (CX + 112, 510), (CX + 76, 510)], 1.0), line_c, 0.09)
    paint(cv, sd_stroke(cv, [(CX - 40, 120), (CX - 40, 820)], 1.1), line_c, 0.10)
    _arrow(cv, (CX - 330, CY + 250), (CX + 330, CY - 250), line_c, 0.10)
    _arrow(cv, (CX + 330, CY + 250), (CX - 330, CY - 250), line_c, 0.10)
    # drifting leaves (engraved, a few faintly lit)
    leaves = []
    for _ in range(26):
        x, y = rng.uniform(60, W - 60), rng.uniform(60, H - 160)
        a = rng.uniform(0, 2 * math.pi)
        s = rng.uniform(16, 34)
        p1 = (x + s * math.cos(a), y + s * math.sin(a))
        leaves.append((leaf((x, y), p1, s * 0.5, bend=s * 0.1), (x, y), p1))
    for pts, p0, p1 in leaves:
        _line(cv, sd_poly(cv, pts, margin=3), line_c, 0.13, 0.6)
        paint(cv, sd_stroke(cv, [p0, p1], 0.5), line_c, 0.10)
        paint(cv, sd_poly(cv, pts, margin=3), "#6a9a4a", 0.06)
    # pine silhouettes along the lower edge
    trees = []
    x = -20.0
    while x < W + 40:
        h = rng.uniform(120, 260)
        w = h * rng.uniform(0.28, 0.36)
        right = []
        tiers = 5
        for k in range(tiers):
            t0 = k / tiers
            yb = H + 5 - h * t0 * 0.9            # tier base
            ww = w * (1 - t0 * 0.8) * 0.5
            right += [(x + ww, yb), (x + ww * 0.35, yb - h * 0.16)]
        left = [(2 * x - px, py) for (px, py) in reversed(right)]
        trees.append(sd_poly(cv, [(x + 6, H + 5)] + right + [(x, H - h)] + left + [(x - 6, H + 5)], margin=3))
        x += rng.uniform(55, 110)
    tr = union(*trees)
    paint(cv, tr, "#020503", 0.8)
    _line(cv, tr, "#3a5a2a", 0.10, 0.6)
    _constellations(cv, rng, line_c, "#ffe8b0")
    _dust_grain_vignette(cv, rng, "#fff4d0", 45)
    return cv


def shadowblade_backdrop():
    cv = Canvas(W, H, ss=1)
    rng = np.random.default_rng(51)
    base = rgrad(cv, CX, H * 0.45, W * 0.75, [(0, "#170c24"), (0.55, "#0a0612"), (1, "#030205")], sy=1.6)
    cv.over(base, np.ones((cv.H, cv.W), F))
    n1 = fnoise(H, W, 61, beta=3.0, lo=1)
    n2 = fnoise(H, W, 63, beta=2.2, lo=2)
    cv.over("#4a1a7a", np.clip(n1 * 0.5 + 0.2, 0, 1) ** 2, 0.22)
    cv.over("#8a2a6a", np.clip(n2 * 0.4, 0, 1) ** 3, 0.08)
    # smoke banks: stretched noise bands drifting across the lower half and the top corners
    sm = fnoise(H, W * 3, 65, beta=2.6, lo=1)[:, ::3]
    band = np.clip(1 - np.abs(cv.Y - H * 0.78) / 220, 0, 1) + np.clip(1 - cv.Y / 260, 0, 1) * 0.6
    cv.over("#8a80a8", np.clip(sm * 0.8 + 0.1, 0, 1) ** 2 * band, 0.14)
    line_c = "#b898ff"
    _rune_ring(cv, rng, line_c)
    # faint crescent sigil behind the daggers
    moon = union(sd_circle(cv, CX, CY, 230))
    inner = sd_circle(cv, CX + 70, CY - 40, 205)
    cres = np.maximum(moon, -inner)
    paint(cv, cres, "#6a4ab0", 0.05)
    _line(cv, cres, line_c, 0.09, 0.7)
    # engraved crossed daggers, tips up
    _dagger(cv, (CX - 300, CY + 290), (CX + 230, CY - 330), line_c, 0.11)
    _dagger(cv, (CX + 300, CY + 290), (CX - 230, CY - 330), line_c, 0.11)
    # five combo pips beneath
    for k in range(5):
        x = CX + (k - 2) * 44
        _line(cv, sd_poly(cv, [(x, CY + 318), (x + 11, CY + 330), (x, CY + 342), (x - 11, CY + 330)], margin=3), line_c, 0.14, 0.7)
        cv.glow(cov(cv, sd_circle(cv, x, CY + 330, 4)), "#a060ff", 6, 0.3)
    _constellations(cv, rng, line_c, "#c8a0ff")
    _dust_grain_vignette(cv, rng, "#e8dcff", 67)
    return cv


TREE10["tree_bg_ranger"] = (ranger_backdrop, dict(margins=None, use="Ranger talent/skill tree backdrop (1600x900, opaque): forest dusk haze, engraved longbow + crossed arrows, leaves, pine silhouettes, rune ring, constellations. Stretch/cover.", scale=1.0))
TREE10["tree_bg_shadowblade"] = (shadowblade_backdrop, dict(margins=None, use="Shadowblade talent/skill tree backdrop (1600x900, opaque): moonless violet haze, smoke banks, engraved crossed daggers, crescent sigil, rune ring, constellations. Stretch/cover.", scale=1.0))
