"""bh-029: Zarael Island tileable PBR texture sets (1024x1024, seamless, deterministic).

Same conventions as gen_textures.py (texlib helpers, OpenGL +Y normal maps derived from a height field,
linear roughness). Albedos are kept mid-value and fairly desaturated -- the game tints and lights them.

Usage (from repo root):
    python tools/textures/gen_zarael_textures.py                 # all ten sets
    python tools/textures/gen_zarael_textures.py jade_stone red_clay

Outputs  game/assets/textures/<set>_albedo.png (sRGB), <set>_normal.png (OpenGL +Y), <set>_rough.png (linear)
         + a .import beside each PNG (copied from the sunstone sibling, no uid line)
Evidence work/lemondev/bh-029/evidence/textures/sheet.png (each set 2x2, lit 2x2 plane, lit sphere, normal, rough)
         + textures.md (means, saturation, seam scores)
"""
import os
import sys
import time
import math
import hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texlib import *  # noqa

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "textures")
EVI = os.path.join(ROOT, "work", "lemondev", "bh-029", "evidence", "textures")


def warp_coords(seed, amp, beta=2.5, fmin=2.0, fmax=40.0):
    """Band-limited domain warp (texlib's version keeps per-pixel jitter, which frays every joint)."""
    wx = noise(seed, beta, fmin, fmax) * amp
    wy = noise(seed + 1, beta, fmin, fmax) * amp
    return (XX + wx) % N, (YY + wy) % N


def split_len(total, k, r, spread=0.35):
    w = 1.0 + (r.random(k) - 0.5) * 2 * spread
    w = w / w.sum() * total
    c = np.round(np.cumsum(w)).astype(int)
    c[-1] = total
    return np.concatenate([[0], c])


def cavity(h, s=6):
    return h - blur(h, s)


def desat(alb, keep):
    """Pull colour toward its own luma; keep=1 leaves it, keep=0 makes it grey."""
    l = (alb * np.array([0.299, 0.587, 0.114], np.float32)).sum(-1, keepdims=True)
    return l + (alb - l) * keep


def courses(seed, nrows, row_spread, blocks, spread, wamp=2.0):
    """Irregular running-bond courses. Returns edge distance, block id, course index, y0 and y1 per pixel."""
    r = rng(seed)
    wx, wy = warp_coords(seed + 1, wamp, 2.2, 6)
    rows = split_len(N, nrows, r, row_spread)
    edge = np.zeros((N, N), np.float32)
    bid = np.zeros((N, N), np.int32)
    cidx = np.zeros((N, N), np.int32)
    nb = 0
    for ri in range(nrows):
        y0, y1 = rows[ri], rows[ri + 1]
        k = blocks(ri, r)
        cum = split_len(N, k, r, spread(ri))
        off = int(r.integers(0, N))
        band = (wy >= y0) & (wy < y1)
        c = (wx - off) % N
        idx = np.clip(np.searchsorted(cum, c, side="right") - 1, 0, k - 1)
        e = np.minimum(np.minimum(c - cum[idx], cum[idx + 1] - c), np.minimum(wy - y0, y1 - wy))
        edge[band] = e[band]
        bid[band] = (idx + nb)[band]
        cidx[band] = ri
        nb += k
    return edge, bid, cidx, rows, nb


def crack_canvas(r, count, steps, step_len, widths, turn=0.45, branch=0.0):
    cv = Canvas()
    walkers = [(float(x), float(y), float(r.uniform(0, 2 * math.pi)), 0) for x, y in r.uniform(0, N, (count, 2))]
    while walkers:
        x, y, a, age = walkers.pop()
        p = [(x, y)]
        for _ in range(int(r.integers(steps[0], steps[1]))):
            a += r.normal(0, turn)
            x += math.cos(a) * step_len
            y += math.sin(a) * step_len
            p.append((x, y))
            if age < 2 and r.random() < branch:
                walkers.append((x, y, a + (1 if r.random() < 0.5 else -1) * r.uniform(0.6, 1.2), age + 1))
        cv.line(p, int(255 * (1 - 0.3 * age)), max(1, int(r.integers(widths[0], widths[1] + 1)) - age))
    return cv.array()


# ---- carved motifs (shared by glyph_stone and terrace_paving) ---------------------------------------------------
def _seg(cv, x0, y0, x1, y1, w, v=255):
    """Axis-aligned thick segment drawn as a rectangle (square joints for frets)."""
    xa, xb = min(x0, x1) - w / 2, max(x0, x1) + w / 2
    ya, yb = min(y0, y1) - w / 2, max(y0, y1) + w / 2
    cv.polygon([(xa, ya), (xb, ya), (xb, yb), (xa, yb)], v)


def _path(cv, pts, w, v=255):
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        _seg(cv, x0, y0, x1, y1, w, v)


def _square_spiral(cx, cy, step, turns, start_dir=0):
    """Points of a square spiral growing outward from (cx, cy). Directions: 0 right, 1 down, 2 left, 3 up."""
    dirs = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    pts = [(cx, cy)]
    x, y = cx, cy
    L = 1
    d = start_dir
    for i in range(int(turns * 4)):
        dx, dy = dirs[d % 4]
        x, y = x + dx * L * step, y + dy * L * step
        pts.append((x, y))
        d += 1
        if i % 2 == 1:
            L += 1
    return pts


def fret_unit(cv, x0, top, P, bh, w):
    """One period of a stepped fret: a stair rising to a plateau and falling again, a square hook under the
    plateau and a small hanging hook in the gap between plateaus."""
    lv = [top + bh * f for f in (0.86, 0.62, 0.38, 0.14)]
    xs = [x0 + P * f for f in (0.0, 0.12, 0.24, 0.36)]
    pts = [(xs[0], lv[0])]
    for k in range(1, 4):
        pts += [(xs[k], lv[k - 1]), (xs[k], lv[k])]
    xr = [x0 + P - (xx - x0) for xx in xs]
    pts += [(xr[3], lv[3])]
    for k in range(3, 0, -1):
        pts += [(xr[k], lv[k - 1])]
        pts += [(xr[k - 1], lv[k - 1])] if k > 1 else [(xr[k], lv[0]), (xr[0], lv[0])]
    _path(cv, pts, w)
    # hook under the plateau, joined to it
    cx, cy = x0 + P * 0.5, top + bh * 0.58
    sp = _square_spiral(cx, cy, w * 1.55, 1.5, 0)
    sp = sp[::-1] + []
    _path(cv, sp, w)
    _seg(cv, sp[0][0], sp[0][1], sp[0][0], lv[3], w)
    # hanging hook between plateaus (sits over x0, hanging from the top fillet)
    hx, hy = x0, top + bh * 0.36
    sp2 = _square_spiral(hx, hy, w * 1.3, 1.0, 2)
    _path(cv, sp2[::-1], w)
    _seg(cv, sp2[-1][0], sp2[-1][1], sp2[-1][0], top, w)


def glyph(cv, cx, cy, s, kind, w):
    """An abstract carved glyph in a square cartouche of side s (no letters, no real script)."""
    h = s / 2
    c = h * 0.28  # corner cut
    frame = [(cx - h + c, cy - h), (cx + h - c, cy - h), (cx + h, cy - h + c), (cx + h, cy + h - c),
             (cx + h - c, cy + h), (cx - h + c, cy + h), (cx - h, cy + h - c), (cx - h, cy - h + c),
             (cx - h + c, cy - h)]
    cv.line(frame, 255, int(w))
    i = h * 0.62
    if kind == 0:  # ringed eye over two bars
        cv.d.ellipse([cx - i * 0.55, cy - i * 0.85, cx + i * 0.55, cy + i * 0.25], outline=255, width=int(w))
        cv.ellipse(cx, cy - i * 0.3, w * 0.9, w * 0.9, 255)
        _seg(cv, cx - i * 0.75, cy + i * 0.55, cx + i * 0.75, cy + i * 0.55, w)
        _seg(cv, cx - i * 0.75, cy + i * 0.9, cx + i * 0.75, cy + i * 0.9, w)
    elif kind == 1:  # stepped cross
        q = i * 0.34
        pts = [(cx - q, cy - 3 * q), (cx + q, cy - 3 * q), (cx + q, cy - q), (cx + 3 * q, cy - q),
               (cx + 3 * q, cy + q), (cx + q, cy + q), (cx + q, cy + 3 * q), (cx - q, cy + 3 * q),
               (cx - q, cy + q), (cx - 3 * q, cy + q), (cx - 3 * q, cy - q), (cx - q, cy - q), (cx - q, cy - 3 * q)]
        _path(cv, pts, w)
        cv.ellipse(cx, cy, w * 0.9, w * 0.9, 255)
    elif kind == 2:  # square spiral
        _path(cv, _square_spiral(cx, cy, w * 1.6, 2.0, 0), w)
    else:  # three dots over a stepped mound
        for k in (-1, 0, 1):
            cv.ellipse(cx + k * i * 0.55, cy - i * 0.65, w * 0.95, w * 0.95, 255)
        q = i * 0.3
        pts = [(cx - 3 * q, cy + i * 0.85), (cx - 3 * q, cy + i * 0.5), (cx - 1.5 * q, cy + i * 0.5),
               (cx - 1.5 * q, cy + i * 0.1), (cx + 1.5 * q, cy + i * 0.1), (cx + 1.5 * q, cy + i * 0.5),
               (cx + 3 * q, cy + i * 0.5), (cx + 3 * q, cy + i * 0.85)]
        _path(cv, pts, w)


# ================================================================================================================
def glyph_stone(seed=2901):
    """Pale weathered limestone in irregular running bond; every third course a carved band of stepped frets and
    glyph cartouches in relief. Tiles at 2 m."""
    r = rng(seed + 50)
    ncourse = 6
    edge, bid, cidx, rows, nb = courses(seed, ncourse, 0.1,
                                        lambda ri, rr: 4 if ri % 3 == 0 else int(rr.integers(3, 6)),
                                        lambda ri: 0.18 if ri % 3 == 0 else 0.4, wamp=1.4)
    tone = r.uniform(0.9, 1.07, nb).astype(np.float32)
    warm = r.uniform(-0.015, 0.02, nb).astype(np.float32)
    rn = noise(seed + 5, 2.0, 4)
    fine = noise(seed + 6, 1.4, 40)
    pit = noise(seed + 11, 0.8, 120)
    chipn = noise(seed + 7, 1.8, 12)
    gap = 3.5
    blk = sstep(gap, gap + 12, edge + chipn * 3.0)
    chips = sstep(1.0, 1.4, chipn) * sstep(24, 5, edge)
    # carved bands
    cv = Canvas()
    recess = np.zeros((N, N), np.float32)
    for ri in (0, 3):
        y0, y1 = float(rows[ri]), float(rows[ri + 1])
        m = 15.0
        w = 6.0
        top, bot = y0 + m, y1 - m
        _seg(cv, 0, top, N, top, w)
        _seg(cv, 0, bot, N, bot, w)
        it, ib = top + w * 1.6, bot - w * 1.6
        bh = ib - it
        if ri == 0:
            P = 128
            for k in range(N // P):
                fret_unit(cv, k * P, it, P, bh, w)
        else:
            P = 256
            for k in range(N // P):
                x0 = k * P
                glyph(cv, x0 + 64, (it + ib) / 2, min(112, bh * 0.98), int(r.integers(0, 4)), w)
                fret_unit(cv, x0 + 128, it, 128, bh, w)
        yy = YY
        recess += (sstep(top - 4, top + 1, yy) * sstep(bot + 4, bot - 1, yy)).astype(np.float32)
    design = cv.array()
    erosion = sstep(0.4, 1.6, noise(seed + 8, 1.9, 10))
    relief = blur(design, 1.1) * (1 - 0.45 * erosion)
    carve_depth = recess * (1 - relief)
    h = 0.12 + blk * (0.78 + 0.06 * rn + 0.02 * fine - 0.2 * carve_depth - 0.04 * pit.clip(1.5, 9) / 9) - chips * 0.16
    h = np.clip(h, 0, 1)
    mortar = 1.0 - sstep(gap - 1, gap + 3, edge)
    # colour
    alb = mul(fill([0.56, 0.535, 0.475]), tone[bid] * (1 + 0.05 * rn + 0.035 * fine))
    alb[..., 0] += warm[bid]
    alb[..., 2] -= warm[bid] * 0.8
    alb = mul(alb, 1 - 0.26 * carve_depth * blk)                       # grime in the carving
    alb = lerp(alb, col([0.66, 0.64, 0.58]), relief * recess * 0.25 * (1 - erosion))  # worn raised tops
    alb = lerp(alb, col([0.62, 0.6, 0.55]), chips * 0.6)              # fresh chip faces
    alb = lerp(alb, col([0.3, 0.285, 0.255]) * (1 + 0.1 * fine[..., None]), mortar)
    streak = noise(seed + 9, 2.2, 3, ay=7.0)
    damp = sstep(0.4, 1.8, streak) * 0.22
    alb = mul(alb, 1.0 - damp)
    lich_n = noise(seed + 10, 1.6, 10) + 0.5 * noise(seed + 12, 1.2, 50)
    lich = sstep(1.6, 2.1, lich_n) * blk
    lich2 = sstep(1.9, 2.3, noise(seed + 13, 1.5, 14)) * blk
    alb = lerp(alb, col([0.5, 0.52, 0.44]), lich * 0.5)
    alb = lerp(alb, col([0.6, 0.48, 0.3]), lich2 * 0.35)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 4), -0.3, 0.3) * 0.9)
    rough = 0.86 + 0.04 * rn - damp * 0.3 + mortar * 0.06 + carve_depth * 0.04
    return alb, h, rough, 6.0


def jade_stone(seed=2902):
    """Polished jade slabs with cloudy veins and fine gold-wire inlay running between the slabs."""
    r = rng(seed + 50)
    edge, bid, cidx, rows, nb = courses(seed, 4, 0.1, lambda ri, rr: 3, lambda ri: 0.2, wamp=0.0)
    hue = r.uniform(-1, 1, nb).astype(np.float32)
    tone = r.uniform(0.86, 1.1, nb).astype(np.float32)
    cloud = noise(seed + 1, 3.0, 2)
    cloud2 = noise(seed + 2, 2.6, 4, fmax=60)
    fine = noise(seed + 3, 1.2, 60)
    w1 = noise(seed + 4, 3.0, 2, fmax=8) * 1.8 + noise(seed + 5, 2.5, 6, fmax=40) * 0.35
    ph = r.uniform(0, 2 * math.pi, nb).astype(np.float32)
    v1 = np.abs(np.sin((XX * 1 + YY * 2) / N * 2 * math.pi * 1.5 + w1 + ph[bid]))
    vein = (1 - sstep(0.0, 0.07, v1)) * sstep(-0.6, 0.6, noise(seed + 6, 2.0, 3))
    halo = (1 - sstep(0.0, 0.4, v1)) * 0.5
    spots = sstep(2.7, 3.0, noise(seed + 7, 1.0, 80))
    dark = col([0.17, 0.25, 0.21])
    midc = col([0.32, 0.41, 0.35])
    lite = col([0.45, 0.51, 0.45])
    t = sstep(-2.0, 2.0, cloud + 0.35 * cloud2)
    alb = lerp(np.broadcast_to(dark, (N, N, 3)), midc, t)
    alb = lerp(alb, lite, sstep(1.0, 2.6, cloud2 + 0.3 * cloud) * 0.45)
    alb = mul(alb, tone[bid] * (1 + 0.02 * fine))
    alb[..., 2] += 0.025 * hue[bid]
    alb[..., 0] -= 0.012 * hue[bid]
    alb = lerp(alb, col([0.54, 0.6, 0.52]), halo * 0.35)
    alb = lerp(alb, col([0.62, 0.66, 0.58]), vein * 0.7)
    alb = lerp(alb, col([0.08, 0.12, 0.1]), spots * 0.7)
    # joints: dark grout either side of a fine gold wire
    gold = 1 - sstep(0.9, 2.1, edge)
    grout = (1 - sstep(2.8, 4.6, edge)) * (1 - gold)
    bevel = (1 - sstep(4.0, 14.0, edge)) * (1 - grout) * (1 - gold)
    alb = lerp(alb, col([0.09, 0.1, 0.08]), grout)
    alb = lerp(alb, col([0.6, 0.48, 0.26]) * (1 + 0.06 * fine[..., None]), gold)
    alb = lerp(alb, col([0.5, 0.58, 0.5]), bevel * 0.12)
    h = 0.72 - sstep(14.0, 4.0, edge) * 0.08 - grout * 0.5 - gold * 0.32 + 0.006 * fine
    h = np.clip(h, 0, 1)
    rough = 0.16 + 0.04 * sstep(-1, 1, cloud2) + vein * 0.05 + grout * 0.6 + gold * 0.16
    return alb, h, rough, 3.0


def obsidian(seed=2903):
    """Black volcanic glass flags with conchoidal fracture ripples and thin molten-copper seams in the joints."""
    r = rng(seed + 50)
    pts = jittered_points(5, 5, seed, 0.85)
    wx, wy = warp_coords(seed + 1, 9.0, 2.4, 3)
    f1, edge, i1, _ = voronoi(pts, wx, wy)
    n = len(pts)
    tone = r.uniform(0.8, 1.2, n).astype(np.float32)
    cloud = noise(seed + 2, 2.4, 2)
    fine = noise(seed + 3, 1.3, 60)
    # conchoidal shells: rippled bowls around a point near each flag's border
    ang = r.uniform(0, 2 * math.pi, n)
    sh = (pts + np.stack([np.cos(ang), np.sin(ang)], 1) * r.uniform(40, 80, (n, 1))) % N
    dp = np.stack([wx, wy], -1) - sh[i1]
    dp = (dp + N / 2) % N - N / 2
    d = np.sqrt((dp ** 2).sum(-1))
    per = r.uniform(11, 19, n).astype(np.float32)[i1]
    reach = r.uniform(90, 150, n).astype(np.float32)[i1]
    a_ = np.arctan2(dp[..., 1], dp[..., 0])
    fan = sstep(-0.2, 0.5, np.cos(a_ - ang[i1] - math.pi)) * (1 - sstep(reach * 0.6, reach, d))
    rip = np.sin(d / per * 2 * math.pi + 0.15 * noise(seed + 4, 2.0, 6))
    shell = fan * (0.5 + 0.5 * rip) * np.clip(1 - d / (reach + 1), 0, 1) ** 0.7
    bowl = fan * (d / reach) ** 2
    # secondary fractures
    fpts = r.uniform(0, N, (50, 2)).astype(np.float32)
    _, fe, _, _ = voronoi(fpts, *warp_coords(seed + 5, 16.0, 2.2, 3))
    frac = (1 - sstep(0.3, 1.4, fe)) * sstep(0.3, 1.3, noise(seed + 6, 2.0, 4))
    gap = 4.0
    copper = 1 - sstep(0.8, 2.0, edge)
    joint = (1 - sstep(gap - 0.5, gap + 3.5, edge)) * (1 - copper)
    h = np.clip(0.3 + sstep(gap, gap + 18, edge) * (0.62 + 0.04 * cloud) - 0.05 * bowl + 0.025 * shell
                - frac * 0.06 - copper * 0.22, 0, 1)
    alb = mul(fill([0.058, 0.055, 0.064]), tone[i1] * (1 + 0.15 * cloud + 0.05 * fine))
    alb = lerp(alb, col([0.19, 0.18, 0.21]), np.clip(shell * 0.7 + frac * 0.5, 0, 1))
    sheen = sstep(1.0, 2.2, noise(seed + 7, 2.0, 5)) * 0.2
    alb = lerp(alb, col([0.15, 0.13, 0.16]), sheen)
    alb = lerp(alb, col([0.035, 0.03, 0.03]), joint)
    alb = lerp(alb, col([0.42, 0.22, 0.11]) * (1 + 0.12 * fine[..., None]), copper * 0.9)
    rough = 0.07 + 0.03 * sstep(-1, 1, cloud) + frac * 0.1 + joint * 0.6 + copper * 0.3
    return alb, h, rough, 4.0


def lime_plaster(seed=2904):
    """Neutral warm off-white lime plaster over stone: trowel strokes, hairline cracks, flaked patches."""
    r = rng(seed + 50)
    rn = noise(seed + 1, 2.2, 2)
    fine = noise(seed + 2, 1.2, 60)
    # trowel strokes: overlapping arc swaths, each a slightly different value
    cv = Canvas()
    rc = Canvas()
    for i in range(900):
        cx, cy = r.uniform(0, N, 2)
        R = r.uniform(90, 240)
        a0 = r.uniform(0, 2 * math.pi)
        span = r.uniform(0.35, 0.8)
        th = r.uniform(34, 70)
        outer = [(cx + math.cos(a0 + span * t) * R, cy + math.sin(a0 + span * t) * R) for t in np.linspace(0, 1, 12)]
        inner = [(cx + math.cos(a0 + span * t) * (R - th), cy + math.sin(a0 + span * t) * (R - th))
                 for t in np.linspace(1, 0, 12)]
        cv.polygon(outer + inner, int(r.integers(50, 206)))
        rc.polygon(outer + inner, 0)
        rc.line(outer, 255, 2)  # the trowel's edge leaves a low ridge
    strokes = blur(cv.array(), 1.2)
    stroke_tone = strokes - blur(strokes, 20)
    ridge = blur(rc.array(), 1.0)
    # flaked patches showing stone underneath
    fl = noise(seed + 3, 2.8, 2, fmax=40) + 0.25 * noise(seed + 4, 1.6, 20, fmax=140)
    flake = sstep(1.95, 2.02, fl)
    rim = sstep(1.7, 1.95, fl) * (1 - flake)
    st_edge, st_id, _, _, nst = courses(seed + 5, 8, 0.2, lambda ri, rr: int(rr.integers(4, 7)), lambda ri: 0.4, 3.0)
    st_tone = r.uniform(0.8, 1.15, nst).astype(np.float32)
    st_blk = sstep(2.0, 10.0, st_edge)
    stone = mul(fill([0.4, 0.37, 0.32]), st_tone[st_id] * (1 + 0.08 * fine)) * (0.55 + 0.45 * st_blk)[..., None]
    cracks = blur(crack_canvas(r, 22, (10, 26), 9, (1, 1), 0.5, 0.05), 0.5)
    h = 0.62 + 0.06 * rn + 0.1 * stroke_tone + 0.04 * ridge + 0.006 * fine - cracks * 0.08 + rim * 0.03
    h = lerp(h, 0.25 + 0.15 * st_blk, flake)
    alb = mul(fill([0.63, 0.605, 0.56]), 1 + 0.05 * rn + 0.14 * stroke_tone + 0.03 * ridge + 0.015 * fine)
    grime = sstep(0.2, 1.8, noise(seed + 6, 2.3, 2, ay=4.0)) * 0.16
    alb = mul(alb, 1 - grime)
    alb = mul(alb, 1 - rim * 0.12)
    alb = lerp(alb, col([0.34, 0.31, 0.27]), cracks * 0.7)
    alb = lerp(alb, stone, flake)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 4), -0.3, 0.3) * 0.6)
    rough = 0.88 + 0.03 * rn - 0.04 * stroke_tone + flake * 0.02
    return alb, h, rough, 3.5


def terrace_paving(seed=2905):
    """Fitted irregular paving with an occasional square glyph tile and a thin inlaid wire line every tile."""
    r = rng(seed + 50)
    pts = jittered_points(6, 6, seed, 0.8)
    wx, wy = warp_coords(seed + 1, 7.0, 2.4, 3)
    f1, edge, i1, _ = voronoi(pts, wx, wy)
    n = len(pts)
    ids = i1.copy()
    # inlaid wire lines: one horizontal and one vertical per tile (a grid every few metres in the world)
    WY, WX = 300.0, 690.0
    dwy = np.abs(((YY - WY) + N / 2) % N - N / 2)
    dwx = np.abs(((XX - WX) + N / 2) % N - N / 2)
    dwire = np.minimum(dwy, dwx)
    side = (((YY - WY) % N) < N / 2).astype(np.int32) * 2 + (((XX - WX) % N) < N / 2).astype(np.int32)
    ids = ids * 4 + side
    edge = np.minimum(edge, dwire - 3.0)
    # square glyph tiles replace the paving where they sit
    gcv = Canvas()
    for k, (gx, gy, gs) in enumerate([(150.0, 560.0, 150.0), (880.0, 880.0, 140.0)]):
        dx = np.abs(((XX - gx) + N / 2) % N - N / 2)
        dy = np.abs(((YY - gy) + N / 2) % N - N / 2)
        dsq = gs / 2 - np.maximum(dx, dy)
        inside = dsq > 0
        edge = np.where(inside, dsq, np.minimum(edge, -dsq))
        ids = np.where(inside, n * 4 + k, ids)
        glyph(gcv, gx, gy, gs * 0.78, (k * 2 + 1) % 4, 6)
    nid = n * 4 + 2
    tone = r.uniform(0.84, 1.1, nid).astype(np.float32)
    warm = r.uniform(-0.02, 0.025, nid).astype(np.float32)
    tone[n * 4:] = 1.08
    carve = blur(gcv.array(), 1.0)
    is_tile = (ids >= n * 4).astype(np.float32)
    rn = noise(seed + 2, 2.0, 3)
    fine = noise(seed + 3, 1.3, 40)
    chipn = noise(seed + 4, 1.8, 10)
    gap = 3.5
    blk = sstep(gap, gap + 18, edge + chipn * 3 * (1 - is_tile))
    joint = 1 - sstep(gap - 1, gap + 4, edge)
    wire = 1 - sstep(1.0, 2.2, dwire)
    wgroove = (1 - sstep(2.5, 4.5, dwire)) * (1 - wire)
    grit = np.clip(noise(seed + 5, 0.6, 150), -2, 2)
    tilt = r.uniform(-0.05, 0.05, nid).astype(np.float32)
    h = 0.12 + blk * (0.74 + 0.05 * rn + 0.02 * fine + tilt[ids]) + joint * 0.04 * sstep(0.5, 1.5, grit)
    h = h - is_tile * blk * 0.14 * carve
    h = np.where(wire > 0, np.maximum(h, 0.2 * wire), h)
    h = np.clip(h, 0, 1)
    alb = mul(fill([0.48, 0.45, 0.4]), tone[ids] * (1 + 0.06 * rn + 0.04 * fine))
    alb[..., 0] += warm[ids]
    alb[..., 2] -= warm[ids] * 0.8
    alb = lerp(alb, col([0.55, 0.51, 0.43]), is_tile * 0.4)
    alb = lerp(alb, col([0.27, 0.245, 0.21]), is_tile * carve * 0.75)
    gritc = lerp(np.broadcast_to(col([0.24, 0.215, 0.18]), (N, N, 3)), col([0.44, 0.4, 0.34]),
                 sstep(0.3, 1.5, grit))
    alb = lerp(alb, gritc, joint)
    alb = lerp(alb, col([0.16, 0.14, 0.12]), wgroove)
    alb = lerp(alb, col([0.52, 0.4, 0.22]) * (1 + 0.1 * fine[..., None]), wire)
    wear = sstep(0.6, 1.8, noise(seed + 6, 2.2, 3)) * 0.12
    alb = mul(alb, 1 - wear)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 5), -0.3, 0.3) * 0.8)
    rough = 0.8 + 0.05 * rn + joint * 0.12 - wire * 0.45 - wear * 0.4
    return alb, h, rough, 6.0


def turquoise_mosaic(seed=2906):
    """Small irregular turquoise / teal tesserae set in dark grout, with a few shell-white and red pieces."""
    r = rng(seed + 50)
    pts = jittered_points(34, 34, seed, 0.85)
    wx, wy = warp_coords(seed + 1, 2.0, 2.2, 8)
    f1, edge, i1, _ = voronoi(pts, wx, wy)
    n = len(pts)
    pal = np.array([[0.3, 0.5, 0.47], [0.24, 0.44, 0.44], [0.35, 0.53, 0.47], [0.21, 0.38, 0.4],
                    [0.38, 0.55, 0.51], [0.27, 0.46, 0.42], [0.33, 0.47, 0.5]], np.float32)
    pc = pal[r.integers(0, len(pal), n)] * r.uniform(0.82, 1.1, (n, 1)).astype(np.float32)
    roll = r.random(n)
    pc[roll < 0.03] = np.array([0.66, 0.63, 0.57], np.float32) * r.uniform(0.9, 1.05, ((roll < 0.03).sum(), 1))
    red = (roll >= 0.03) & (roll < 0.05)
    pc[red] = np.array([0.5, 0.23, 0.17], np.float32) * r.uniform(0.85, 1.1, (red.sum(), 1))
    is_tq = (roll >= 0.05).astype(np.float32)
    # matrix web inside some turquoise pieces
    mpts = r.uniform(0, N, (900, 2)).astype(np.float32)
    _, me, _, _ = voronoi(mpts, *warp_coords(seed + 2, 4.0, 2.2, 6, 120))
    web = (1 - sstep(0.3, 1.2, me)) * (r.random(n) < 0.35)[i1] * is_tq[i1]
    fine = noise(seed + 3, 1.2, 80)
    cloud = noise(seed + 4, 2.2, 6)
    tx = r.uniform(-1, 1, n).astype(np.float32)
    ty = r.uniform(-1, 1, n).astype(np.float32)
    dp = np.stack([wx, wy], -1) - pts[i1]
    dp = (dp + N / 2) % N - N / 2
    gap = 2.4
    blk = sstep(gap, gap + 5, edge)
    grout = 1 - sstep(gap - 0.8, gap + 1.2, edge)
    h = 0.15 + blk * (0.7 + (dp[..., 0] * tx[i1] + dp[..., 1] * ty[i1]) * 0.0035 + 0.01 * fine) - web * 0.03
    h = np.clip(h, 0, 1)
    alb = pc[i1] * (1 + 0.06 * cloud + 0.035 * fine)[..., None]
    alb = lerp(alb, col([0.62, 0.68, 0.62]), sstep(1.2, 2.4, cloud + fine * 0.3)[..., None] * is_tq[i1][..., None] * 0.25)
    alb = lerp(alb, col([0.17, 0.16, 0.13]), web * 0.75)
    alb = lerp(alb, col([0.12, 0.11, 0.1]) * (1 + 0.15 * fine[..., None]), grout)
    dust = sstep(0.8, 2.0, noise(seed + 5, 2.3, 3)) * 0.14
    alb = mul(alb, 1 - dust)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 3), -0.3, 0.3) * 0.6)
    rough = 0.3 + 0.05 * cloud + grout * 0.6 + web * 0.2 + dust * 0.4
    return alb, h, rough, 4.0


def _leaf(L, W, a, x, y, seg=11):
    pts = []
    for t in np.linspace(0, 1, seg):
        pts.append((t * L - L / 2, math.sin(t * math.pi) ** 0.7 * W / 2))
    for t in np.linspace(1, 0, seg)[1:-1]:
        pts.append((t * L - L / 2, -math.sin(t * math.pi) ** 0.7 * W / 2))
    ca, sa = math.cos(a), math.sin(a)
    return [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts]


def jungle_floor(seed=2907):
    """Jungle ground: dark loam, broad fallen leaves, roots, seeds and moss patches."""
    r = rng(seed + 50)
    rn = noise(seed + 1, 2.1, 2)
    fine = noise(seed + 2, 1.2, 70)
    crumb = noise(seed + 3, 0.7, 140)
    rgbc = Canvas("RGB", (0, 0, 0))
    hc = Canvas("L", 0)
    # roots, low on the ground
    for i in range(26):
        x, y = r.uniform(0, N, 2)
        a = r.uniform(0, 2 * math.pi)
        w = int(r.integers(7, 15))
        stack = [(x, y, a, w)]
        while stack:
            x, y, a, w = stack.pop()
            p = [(x, y)]
            for s in range(int(r.integers(6, 16))):
                a += r.normal(0, 0.22)
                x += math.cos(a) * 16
                y += math.sin(a) * 16
                p.append((x, y))
                if w > 4 and r.random() < 0.09:
                    stack.append((x, y, a + r.choice([-1, 1]) * r.uniform(0.5, 1.1), max(3, w // 2)))
            c = np.array([0.29, 0.23, 0.17]) * r.uniform(0.8, 1.15)
            rgbc.line(p, tuple(int(v * 255) for v in np.clip(c, 0, 1)), w)
            hc.line(p, 150, w)
            rgbc.line(p, tuple(int(v * 255 * 1.18) for v in np.clip(c, 0, 1)), max(1, w // 3))
            hc.line(p, 175, max(1, w // 3))
    # broad fallen leaves
    leafpal = np.array([[0.38, 0.27, 0.15], [0.32, 0.22, 0.13], [0.44, 0.34, 0.18], [0.26, 0.19, 0.12],
                        [0.36, 0.33, 0.17], [0.29, 0.3, 0.16], [0.42, 0.24, 0.14], [0.2, 0.16, 0.11]], np.float32)
    nl = 620
    for i in range(nl):
        x, y = r.uniform(0, N, 2)
        a = r.uniform(0, math.pi * 2)
        L = r.uniform(34, 92)
        W = L * r.uniform(0.38, 0.6)
        P = _leaf(L, W, a, x, y)
        c = leafpal[int(r.integers(0, len(leafpal)))] * r.uniform(0.78, 1.12)
        cc = tuple(int(v * 255) for v in np.clip(c, 0, 1))
        dc = tuple(int(v * 255 * 0.72) for v in np.clip(c, 0, 1))
        rgbc.polygon(P, cc)
        hv = int(120 + 120 * i / nl)
        hc.polygon(P, hv)
        k = len(P) // 2
        rgbc.line([P[0], P[k]], dc, 2)
        hc.line([P[0], P[k]], hv + 6, 2)
        ca, sa = math.cos(a), math.sin(a)
        for t in np.linspace(-0.3, 0.32, 5):
            bx, by = x + ca * t * L, y + sa * t * L
            for sgn in (-1, 1):
                ex = bx + (ca * 0.16 * L - sa * sgn * 0.36 * W)
                ey = by + (sa * 0.16 * L + ca * sgn * 0.36 * W)
                rgbc.line([(bx, by), (ex, ey)], dc, 1)
        # decayed holes in some leaves
        if r.random() < 0.25:
            hx, hy = x + r.normal(0, L * 0.12), y + r.normal(0, L * 0.12)
            rr = r.uniform(3, 8)
            rgbc.ellipse(hx, hy, rr, rr * 0.8, (0, 0, 0))
            hc.ellipse(hx, hy, rr, rr * 0.8, 0)
    # seeds and pods
    for i in range(260):
        x, y = r.uniform(0, N, 2)
        rx = r.uniform(2.5, 6)
        c = np.array([0.33, 0.2, 0.12]) * r.uniform(0.7, 1.2)
        rgbc.ellipse(x, y, rx, rx * r.uniform(0.6, 0.9), tuple(int(v * 255) for v in np.clip(c, 0, 1)))
        hc.ellipse(x, y, rx, rx * 0.8, 250)
    lay = np.asarray(rgbc.img, np.float32) / 255.0
    hl = hc.array()
    cover = blur((hl > 0).astype(np.float32), 0.5)
    soil = mul(fill([0.16, 0.12, 0.085]), 1 + 0.14 * rn + 0.08 * crumb + 0.04 * fine)
    alb = lerp(soil, lay, cover)
    h = 0.12 + 0.72 * hl + 0.04 * rn + 0.025 * crumb * (1 - cover)
    mossn = noise(seed + 4, 2.0, 4) + 0.4 * noise(seed + 5, 1.3, 40)
    moss = sstep(0.9, 1.4, mossn) * (1 - 0.7 * sstep(0.45, 0.6, hl))
    alb = lerp(alb, col([0.2, 0.25, 0.11]) * (1 + 0.25 * fine[..., None]), moss * 0.85)
    h = h + moss * 0.05 * (1 + 0.5 * fine)
    alb = mul(alb, 1 + 0.07 * rn)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 3), -0.35, 0.3) * 0.9)
    alb = desat(alb, 0.8)
    rough = 0.88 - 0.06 * hl * (1 - moss) - 0.08 * sstep(0.8, 2.0, -rn)
    return alb, h, rough, 4.0


def red_clay(seed=2908):
    """Packed red-ochre clay ground with cracks, pebbles and dry grass tufts."""
    r = rng(seed + 50)
    rn = noise(seed + 1, 2.1, 2)
    mid = noise(seed + 2, 1.8, 8)
    fine = noise(seed + 3, 1.2, 70)
    cp = jittered_points(9, 9, seed + 4, 0.9)
    cwx, cwy = warp_coords(seed + 5, 10.0, 2.7, 3, 24)
    jag = noise(seed + 9, 1.8, 20, fmax=70)
    _, ce, ci, _ = voronoi(cp, (cwx + jag * 1.2) % N, (cwy - jag * 1.2) % N)
    crackm = sstep(-0.6, 0.4, noise(seed + 6, 2.2, 2))
    cw = 1.2 + 2.2 * sstep(-1, 1.5, noise(seed + 10, 2.0, 3))
    crack = (1 - sstep(cw * 0.5, cw * 0.5 + 1.6, ce)) * crackm
    curl = sstep(16, 2, ce) * crackm
    small = crack_canvas(r, 40, (4, 12), 7, (1, 2), 0.6)
    small = blur(small, 0.5) * sstep(-0.5, 0.5, noise(seed + 7, 2.0, 4))
    pp = r.uniform(0, N, (600, 2))
    pf1, _, pi1, _ = voronoi(pp)
    rad = r.uniform(2.0, 7.0, 600).astype(np.float32)
    keep = r.random(600) < 0.5
    peb = np.sqrt(np.clip(1 - (pf1 / rad[pi1]) ** 2, 0, 1)) * keep[pi1]
    h = 0.42 + 0.1 * rn + 0.05 * mid + 0.02 * fine + curl * 0.06 - crack * 0.35 - small * 0.1 + peb * 0.3
    alb = mul(fill([0.44, 0.31, 0.23]), 1 + 0.1 * rn + 0.06 * mid + 0.05 * fine + 0.06 * curl)
    pale = sstep(0.6, 1.8, noise(seed + 8, 2.3, 3))
    alb = lerp(alb, col([0.52, 0.42, 0.33]), pale * 0.35)
    pc = np.array([[0.46, 0.42, 0.37], [0.4, 0.33, 0.27], [0.34, 0.3, 0.27], [0.5, 0.4, 0.3]], np.float32)[
        r.integers(0, 4, 600)]
    alb = lerp(alb, pc[pi1] * (0.8 + 0.3 * peb)[..., None], sstep(0.05, 0.3, peb))
    alb = lerp(alb, col([0.22, 0.14, 0.1]), np.clip(crack * 0.9 + small * 0.5, 0, 1))
    # dry grass tufts
    rgbc = Canvas("RGB", (0, 0, 0))
    hc = Canvas("L", 0)
    gpal = np.array([[0.5, 0.44, 0.31], [0.45, 0.4, 0.28], [0.4, 0.39, 0.28], [0.54, 0.47, 0.33],
                     [0.34, 0.32, 0.23]], np.float32)
    for t in range(40):
        tx, ty = r.uniform(0, N, 2)
        lean = r.uniform(0, 2 * math.pi)
        for b in range(int(r.integers(24, 50))):
            a = lean + r.normal(0, 0.55)
            L = r.uniform(14, 40)
            x0, y0 = tx + r.normal(0, 5), ty + r.normal(0, 5)
            bend = r.normal(0, 0.3)
            mx, my = x0 + math.cos(a) * L * 0.5, y0 + math.sin(a) * L * 0.5
            ex, ey = x0 + math.cos(a + bend) * L, y0 + math.sin(a + bend) * L
            c = gpal[int(r.integers(0, len(gpal)))] * r.uniform(0.8, 1.1)
            rgbc.line([(x0, y0), (mx, my), (ex, ey)], tuple(int(v * 255) for v in np.clip(c, 0, 1)), 2)
            hc.line([(x0, y0), (mx, my), (ex, ey)], int(130 + r.uniform(0, 120)), 2)
    lay = np.asarray(rgbc.img, np.float32) / 255.0
    hg = hc.array()
    gcov = blur((hg > 0).astype(np.float32), 0.5)
    alb = lerp(alb, lay, gcov)
    h = lerp(h, 0.55 + 0.4 * hg, gcov)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 3), -0.3, 0.3) * 1.0)
    alb = desat(alb, 0.85)
    rough = 0.9 - peb * 0.08 - pale * 0.03
    return alb, h, rough, 6.0


def blackwire_soil(seed=2909):
    """Corrupted ground: cracked dark red-brown earth, thin dim violet-red veins in the cracks, glassy grit."""
    r = rng(seed + 50)
    rn = noise(seed + 1, 2.1, 2)
    mid = noise(seed + 2, 1.8, 8)
    fine = noise(seed + 3, 1.2, 70)
    jag = noise(seed + 13, 1.8, 20, fmax=70)
    cp = jittered_points(6, 6, seed + 4, 0.9)
    cwx, cwy = warp_coords(seed + 5, 13.0, 2.7, 3, 22)
    _, ce, _, _ = voronoi(cp, (cwx + jag * 0.6) % N, (cwy + jag * 0.6) % N)
    cp2 = jittered_points(15, 15, seed + 6, 0.95)
    c2x, c2y = warp_coords(seed + 7, 5.0, 2.6, 5, 40)
    _, ce2, _, _ = voronoi(cp2, (c2x - jag * 0.5) % N, (c2y + jag * 0.5) % N)
    bw = 2.5 + 2.5 * sstep(-1, 1.5, noise(seed + 14, 2.0, 3))
    big = 1 - sstep(bw, bw + 2.0, ce)
    sm = (1 - sstep(0.8, 2.2, ce2)) * sstep(-0.4, 0.6, noise(seed + 8, 2.0, 4))
    vein = (1 - sstep(0.2, 1.0, ce)) * sstep(-0.5, 0.5, noise(seed + 9, 2.0, 3))
    plate = sstep(bw, bw + 18.0, ce)
    grit = noise(seed + 10, 0.4, 220)
    glass = sstep(2.0, 2.4, grit)
    glint = sstep(2.6, 2.9, grit) * sstep(0.0, 1.0, noise(seed + 11, 2.0, 5))
    h = 0.4 + 0.1 * rn + 0.04 * mid + 0.02 * fine + plate * 0.08 - big * 0.32 - sm * 0.09 + glass * 0.06
    alb = mul(fill([0.215, 0.145, 0.125]), 1 + 0.12 * rn + 0.07 * mid + 0.05 * fine)
    ash = sstep(0.7, 2.0, noise(seed + 12, 2.2, 3))
    alb = lerp(alb, col([0.3, 0.25, 0.24]), ash * 0.3)
    alb = lerp(alb, col([0.09, 0.06, 0.06]), np.clip(big * 0.9 + sm * 0.6, 0, 1))
    alb = lerp(alb, col([0.4, 0.12, 0.22]), vein * 0.8)
    alb = lerp(alb, col([0.07, 0.06, 0.08]), glass * 0.8)
    alb = lerp(alb, col([0.3, 0.16, 0.28]), glint * 0.6)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 3), -0.3, 0.3) * 1.0)
    rough = 0.88 - glass * 0.6 - glint * 0.2 - vein * 0.25 + 0.03 * rn
    return alb, h, rough, 5.0


def cliff_ochre(seed=2910):
    """Layered ochre / red sandstone cliff: horizontal strata, cross-bedding, erosion streaks, joints."""
    r = rng(seed + 50)
    K = 15
    bounds = split_len(N, K, r, 0.65)
    warp = noise(seed + 1, 2.6, 1, ax=4.0) * 34 + noise(seed + 2, 2.2, 3, ax=2.0, fmax=60) * 7
    yw = (YY + warp) % N
    li = np.clip(np.searchsorted(bounds, yw, side="right") - 1, 0, K - 1)
    ly = (yw - bounds[li]) / np.maximum(bounds[li + 1] - bounds[li], 1)
    pal = np.array([[0.55, 0.41, 0.28], [0.5, 0.32, 0.23], [0.54, 0.46, 0.36], [0.45, 0.34, 0.26],
                    [0.53, 0.37, 0.25], [0.48, 0.39, 0.31]], np.float32)
    lc = pal[r.integers(0, len(pal), K)] * r.uniform(0.9, 1.08, (K, 1)).astype(np.float32)
    hard = np.where(r.random(K) < 0.5, r.uniform(0.75, 1.0, K), r.uniform(0.0, 0.25, K)).astype(np.float32)
    slope = r.uniform(-0.35, 0.35, K).astype(np.float32)
    lam = np.sin((yw + XX * slope[li]) / r.uniform(8, 13) * 2 * math.pi + noise(seed + 3, 2.4, 4, fmax=60) * 2)
    n1 = noise(seed + 4, 2.2, 2)
    fine = noise(seed + 5, 1.3, 50)
    # vertical joints: each bed breaks into blocks at its own spacing; hard beds stand out as ledges
    jx = (XX + noise(seed + 7, 2.4, 3, fmax=50) * 6) % N
    jd = np.full((N, N), 1e4, np.float32)
    bk = np.zeros((N, N), np.int32)
    for k in range(K):
        nj = int(r.integers(2, 7))
        cum = split_len(N, nj, r, 0.5)
        off = float(r.uniform(0, N))
        m = li == k
        c = (jx[m] - off) % N
        idx = np.clip(np.searchsorted(cum, c, side="right") - 1, 0, nj - 1)
        jd[m] = np.minimum(c - cum[idx], cum[idx + 1] - c)
        bk[m] = k * 8 + idx
    joint = (1 - sstep(0.8, 3.0, jd)) * sstep(0.25, 0.6, hard[li])
    facet = rng(seed + 9).uniform(-0.07, 0.07, K * 8).astype(np.float32)[bk] * hard[li]
    lip = sstep(0.0, 0.1, ly) * sstep(1.0, 0.8, ly)
    prof = hard[li] * 0.4 * lip * sstep(0.0, 14.0, jd) + (1 - hard[li]) * 0.12 * np.sin(ly * math.pi)
    h = 0.25 + prof + 0.05 * n1 + 0.012 * lam + 0.012 * fine + facet - joint * 0.2
    alb = lc[li] * (1 + 0.06 * lam * (1 - hard[li]) + 0.07 * n1 + 0.03 * fine)[..., None]
    alb = mul(alb, 0.86 + 0.18 * hard[li])
    alb = mul(alb, 1 + 0.1 * hard[li] * sstep(0.2, 0.0, ly) - 0.32 * hard[li] * sstep(0.78, 1.0, ly))  # lit lip, shaded underside
    alb = mul(alb, 1 - 0.22 * hard[(li - 1) % K] * sstep(0.25, 0.0, ly))  # soft bed in the shadow of the ledge above
    alb = lerp(alb, col([0.32, 0.22, 0.17]), (1 - sstep(0.0, 0.08, ly)) * 0.45)  # dark parting at each bed
    streak = sstep(0.3, 1.8, noise(seed + 10, 2.2, 3, ay=9.0))
    alb = mul(alb, 1 - streak * 0.22)
    alb = lerp(alb, col([0.56, 0.52, 0.46]), sstep(1.4, 2.2, noise(seed + 11, 2.2, 4, ay=6.0)) * 0.25)
    alb = lerp(alb, col([0.18, 0.13, 0.1]), joint * 0.85)
    alb = desat(alb, 0.82)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 6), -0.3, 0.3) * 1.0)
    rough = 0.9 + 0.03 * fine - streak * 0.08
    return alb, h, rough, 7.0


SETS = {
    "glyph_stone": glyph_stone, "jade_stone": jade_stone, "obsidian": obsidian, "lime_plaster": lime_plaster,
    "terrace_paving": terrace_paving, "turquoise_mosaic": turquoise_mosaic, "jungle_floor": jungle_floor,
    "red_clay": red_clay, "blackwire_soil": blackwire_soil, "cliff_ochre": cliff_ochre,
}


# ---- .import beside each PNG -------------------------------------------------------------------------------------
def write_import(fname):
    src = os.path.join(OUT, "sunstone_albedo.png.import")
    with open(src, "r", encoding="utf-8") as f:
        txt = f.read()
    res = "res://assets/textures/" + fname
    md5 = hashlib.md5(res.encode()).hexdigest()
    out = []
    for line in txt.splitlines():
        if line.startswith("uid="):
            continue
        line = line.replace("res://assets/textures/sunstone_albedo.png", res)
        line = line.replace("sunstone_albedo.png-4c9e4174a4a7dfd15776e6583db23192", f"{fname}-{md5}")
        out.append(line)
    with open(os.path.join(OUT, fname + ".import"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")


# ---- evidence: lit previews --------------------------------------------------------------------------------------
LIGHT = np.array([-0.55, 0.5, 0.67], np.float32)
LIGHT /= np.linalg.norm(LIGHT)


def shade(alb, n, rough, view=np.array([0, 0, 1], np.float32)):
    ndl = np.clip((n * LIGHT).sum(-1), 0, 1)
    hv = LIGHT + view
    hv = hv / np.linalg.norm(hv, axis=-1, keepdims=True)
    ndh = np.clip((n * hv).sum(-1), 0, 1)
    shin = 2.0 / np.clip(rough, 0.05, 1) ** 4
    spec = ndh ** np.minimum(shin, 4000) * (1 - rough) ** 2 * 0.6 * ndl
    return np.clip(alb * (0.3 + 0.95 * ndl[..., None]) + spec[..., None] * 0.9, 0, 1)


def lit_plane(alb, nrm, rough, size):
    a2 = np.tile(alb, (2, 2, 1))
    n2 = np.tile(nrm, (2, 2, 1)) * 2 - 1
    r2 = np.tile(rough, (2, 2))
    img = shade(a2, n2, r2)
    return Image.fromarray((img * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)


def lit_sphere(alb, nrm, rough, size):
    s = size * 2
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    x = (xx + 0.5) / s * 2 - 1
    y = 1 - (yy + 0.5) / s * 2
    rr = x * x + y * y
    inside = rr < 1
    z = np.sqrt(np.clip(1 - rr, 0, 1))
    P = np.stack([x, y, z], -1)
    u = (np.arctan2(x, z) / (2 * math.pi) + 0.5) * 2.0
    v = np.arccos(np.clip(y, -1, 1)) / math.pi * 1.0
    px = (u * N) % N
    py = (v * N) % N
    a = sample_wrap(alb, px, py)
    t = sample_wrap(nrm, px, py) * 2 - 1
    ro = sample_wrap(rough, px, py)
    T = np.stack([z, np.zeros_like(z), -x], -1)
    T /= np.maximum(np.linalg.norm(T, axis=-1, keepdims=True), 1e-6)
    B = np.cross(P, T)
    nw = T * t[..., :1] + B * t[..., 1:2] + P * t[..., 2:3]
    nw /= np.maximum(np.linalg.norm(nw, axis=-1, keepdims=True), 1e-6)
    img = shade(a, nw, ro)
    bg = np.array([0.11, 0.1, 0.12], np.float32)
    img = np.where(inside[..., None], img, bg)
    return Image.fromarray((img * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)


def tile2(img, size):
    a = np.tile(img, (2, 2, 1)) if img.ndim == 3 else np.tile(img, (2, 2))
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)


def sat_mean(alb):
    mx, mn = alb.max(-1), alb.min(-1)
    return float(((mx - mn) / np.maximum(mx, 1e-4)).mean())


def main(names):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(EVI, exist_ok=True)
    rows = []
    report = []
    for name in names:
        t = time.time()
        alb, h, rough, ns = SETS[name]()
        alb = np.clip(alb, 0, 1).astype(np.float32)
        h = np.clip(h, 0, 1)
        rough = np.clip(rough, 0.05, 1).astype(np.float32)
        nrm = normal_from_height(h * 255.0 / 64.0, ns * 0.35).astype(np.float32)
        for suf, arr, fn in (("albedo", alb, save_rgb), ("normal", nrm, save_rgb), ("rough", rough, save_gray)):
            fname = f"{name}_{suf}.png"
            fn(os.path.join(OUT, fname), arr)
            write_import(fname)
        sa = seam_score(alb.mean(-1))
        sn = seam_score(nrm[..., 0])
        m = alb.reshape(-1, 3).mean(0)
        luma = float((alb * np.array([0.299, 0.587, 0.114], np.float32)).sum(-1).mean())
        report.append((name, sa, sn, m, luma, sat_mean(alb), float(rough.mean()), time.time() - t))
        print(f"{name:17s} seam a={sa[0]:.2f},{sa[1]:.2f} n={sn[0]:.2f},{sn[1]:.2f} mean={m.round(3).tolist()} "
              f"luma={luma:.3f} sat={report[-1][5]:.2f} rough={report[-1][6]:.2f} {time.time() - t:.1f}s", flush=True)
        rows.append((name, alb, nrm, rough))
    if len(names) < len(SETS):
        return
    # contact sheet
    S = 300
    W = 30 + S * 3 + S // 2 + 40
    sheet = Image.new("RGB", (W, 40 + len(rows) * (S + 34)), (26, 24, 28))
    dr = ImageDraw.Draw(sheet)
    dr.text((10, 12), "bh-029 Zarael textures: albedo 2x2 | lit 2x2 plane | lit sphere | normal / rough", fill=(230, 220, 200))
    for k, (name, alb, nrm, rough) in enumerate(rows):
        y = 40 + k * (S + 34)
        dr.text((10, y), name, fill=(235, 225, 205))
        y += 16
        sheet.paste(tile2(alb, S), (10, y))
        sheet.paste(lit_plane(alb, nrm, rough, S), (20 + S, y))
        sheet.paste(lit_sphere(alb, nrm, rough, S), (30 + 2 * S, y))
        sheet.paste(tile2(nrm, S // 2), (40 + 3 * S, y))
        sheet.paste(tile2(rough, S // 2).convert("RGB"), (40 + 3 * S, y + S // 2))
    sheet.save(os.path.join(EVI, "sheet.png"))
    with open(os.path.join(EVI, "seam_report.txt"), "w") as f:
        f.write("# set  seam(albedo x,y)  seam(normal x,y)  mean albedo  luma  mean saturation  mean rough\n")
        for name, sa, sn, m, luma, sat, ro, dt in report:
            f.write(f"{name:17s} {sa[0]:.2f},{sa[1]:.2f}  {sn[0]:.2f},{sn[1]:.2f}  {m.round(3).tolist()}  "
                    f"{luma:.3f}  {sat:.2f}  {ro:.2f}\n")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    main(args if args else list(SETS.keys()))
