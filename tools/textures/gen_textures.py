"""Generate the Beyond Heroes tileable PBR texture sets (1024x1024, seamless, deterministic).

Usage (from repo root):
    python tools/textures/gen_textures.py            # all sets
    python tools/textures/gen_textures.py brick moss # only some

Outputs  game/assets/textures/<set>_albedo.png (sRGB), <set>_normal.png (OpenGL +Y, linear), <set>_rough.png (linear)
         game/assets/textures/leaves_atlas.png, grass_blades.png (RGBA, alpha-cut)
Evidence work/lemondev/bh-001/evidence/environment/tiling/<set>_2x2.png + textures_overview.png + seam_report.txt
"""
import os
import sys
import time
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texlib import *  # noqa

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "textures")
EVI = os.path.join(ROOT, "work", "lemondev", "bh-001", "evidence", "environment", "tiling")


def split_len(total, k, r, spread=0.35):
    w = 1.0 + (r.random(k) - 0.5) * 2 * spread
    w = w / w.sum() * total
    c = np.round(np.cumsum(w)).astype(int)
    c[-1] = total
    return np.concatenate([[0], c])


def cavity(h, s=6):
    return h - blur(h, s)


# ----------------------------------------------------------------------------------------------------------------
def stone_blocks(seed=101):
    r = rng(seed)
    wx, wy = warp_coords(seed + 1, 3.0, 2.2, 6)
    rows = split_len(N, 5, r, 0.18)
    h = np.zeros((N, N), np.float32)
    edge = np.zeros((N, N), np.float32)
    bid = np.zeros((N, N), np.int32)
    nb = 0
    for ri in range(5):
        y0, y1 = rows[ri], rows[ri + 1]
        k = int(r.integers(3, 5))
        cum = split_len(N, k, r, 0.4)
        off = r.integers(0, N)
        band = (wy >= y0) & (wy < y1)
        c = (wx - off) % N
        idx = np.clip(np.searchsorted(cum, c, side="right") - 1, 0, k - 1)
        dx = np.minimum(c - cum[idx], cum[idx + 1] - c)
        dy = np.minimum(wy - y0, y1 - wy)
        e = np.minimum(dx, dy)
        edge[band] = e[band]
        bid[band] = (idx + nb)[band]
        nb += k
    tone = r.uniform(0.86, 1.08, nb).astype(np.float32)
    warm = r.uniform(-0.018, 0.022, nb).astype(np.float32)
    tilt_x = r.uniform(-1, 1, nb).astype(np.float32) * 0.00012
    tilt_y = r.uniform(-1, 1, nb).astype(np.float32) * 0.00012
    rough_n = noise(seed + 5, 2.0, 4)
    fine = noise(seed + 6, 1.4, 30)
    chipn = noise(seed + 7, 1.8, 12)
    gap = 4.0
    blk = sstep(gap, gap + 16, edge + chipn * 3.0)
    chips = (chipn > 1.1) & (edge < 26)
    surf = 0.08 * rough_n + 0.025 * fine + (XX * tilt_x[bid] + YY * tilt_y[bid]) * 0.0
    h = 0.12 + blk * (0.75 + surf) - chips * 0.18 * sstep(26, 4, edge)
    h = np.clip(h, 0, 1)
    mortar = 1.0 - sstep(gap - 1, gap + 3, edge)
    # colour
    base = col([0.47, 0.45, 0.41])
    alb = fill(base)
    alb = mul(alb, tone[bid] * (1 + 0.06 * rough_n + 0.04 * fine))
    alb[..., 0] += warm[bid]
    alb[..., 2] -= warm[bid] * 0.8
    wear = sstep(14, 4, edge) * blk * 0.08
    alb += wear[..., None]
    alb = lerp(alb, col([0.25, 0.235, 0.21]) * (1 + 0.1 * fine[..., None]), mortar)
    streak = noise(seed + 8, 2.2, 3, ay=7.0)
    damp = sstep(0.3, 1.6, streak) * 0.35
    alb = mul(alb, 1.0 - damp)
    mossn = noise(seed + 9, 2.0, 5) + 0.6 * noise(seed + 10, 1.2, 40)
    moss = sstep(1.0, 1.6, mossn + mortar * 1.2 + damp * 2.0) * (0.35 + 0.65 * mortar)
    alb = lerp(alb, col([0.24, 0.29, 0.13]) * (1 + 0.2 * fine[..., None]), moss * 0.85)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 5), -0.3, 0.3) * 0.9)
    rough = 0.84 + 0.05 * rough_n - damp * 0.5 + mortar * 0.08 + moss * 0.05
    return alb, h, rough, 6.0


def stone_floor(seed=202):
    r = rng(seed)
    pts = jittered_points(4, 4, seed, 0.75)
    wx, wy = warp_coords(seed + 1, 9.0, 2.4, 3)
    f1, edge, i1, _ = voronoi(pts, wx, wy)
    n = len(pts)
    tone = r.uniform(0.84, 1.1, n).astype(np.float32)
    warm = r.uniform(-0.015, 0.025, n).astype(np.float32)
    off = r.uniform(-0.06, 0.06, n).astype(np.float32)
    rn = noise(seed + 2, 2.0, 3)
    fine = noise(seed + 3, 1.3, 40)
    chipn = noise(seed + 4, 1.8, 10)
    gap = 3.5
    blk = sstep(gap, gap + 22, edge + chipn * 4)
    # cracks
    cv = Canvas()
    for _ in range(9):
        x, y = r.uniform(0, N, 2)
        a = r.uniform(0, 2 * math.pi)
        p = [(x, y)]
        for _s in range(int(r.integers(6, 14))):
            a += r.normal(0, 0.5)
            x += math.cos(a) * 14
            y += math.sin(a) * 14
            p.append((x, y))
        cv.line(p, 255, int(r.integers(2, 4)))
    crack = blur(cv.array(), 0.8)
    h = 0.1 + blk * (0.8 + off[i1] + 0.06 * rn + 0.02 * fine) - crack * 0.35 * blk
    h = np.clip(h, 0, 1)
    grout = 1.0 - sstep(gap - 1, gap + 3, edge)
    alb = fill([0.46, 0.44, 0.41])
    alb = mul(alb, tone[i1] * (1 + 0.07 * rn + 0.05 * fine))
    alb[..., 0] += warm[i1]
    alb[..., 2] -= warm[i1]
    polish = sstep(0.2, 1.5, noise(seed + 5, 2.4, 2)) * blk
    alb = alb + polish[..., None] * 0.05
    dirt = col([0.24, 0.2, 0.16]) * (1 + 0.15 * fine[..., None])
    alb = lerp(alb, dirt, np.clip(grout + crack * 0.8, 0, 1))
    stain = sstep(0.8, 2.0, noise(seed + 6, 2.3, 2)) * 0.3
    alb = mul(alb, 1 - stain)
    mossn = sstep(1.2, 1.9, noise(seed + 7, 2.0, 5) + grout * 1.4)
    alb = lerp(alb, col([0.23, 0.27, 0.13]), mossn * 0.7)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 6), -0.3, 0.3))
    rough = 0.8 - polish * 0.2 + grout * 0.12 + 0.04 * rn
    return alb, h, rough, 5.0


def cobblestone(seed=303):
    r = rng(seed)
    pts = jittered_points(11, 11, seed, 0.95)
    wx, wy = warp_coords(seed + 1, 4.0, 2.2, 6)
    f1, edge, i1, _ = voronoi(pts, wx, wy)
    n = len(pts)
    pal = np.array([[0.44, 0.43, 0.41], [0.40, 0.37, 0.33], [0.36, 0.37, 0.38], [0.47, 0.44, 0.39],
                    [0.33, 0.31, 0.29]], np.float32)
    pc = pal[r.integers(0, len(pal), n)] * r.uniform(0.88, 1.1, (n, 1)).astype(np.float32)
    fine = noise(seed + 2, 1.4, 40)
    rn = noise(seed + 3, 2.0, 6)
    dome = np.sqrt(sstep(2.0, 30.0, edge))
    h = 0.08 + dome * (0.82 + 0.05 * rn + 0.02 * fine) * r.uniform(0.85, 1.0, n).astype(np.float32)[i1]
    gap = 1.0 - sstep(1.0, 6.0, edge)
    alb = pc[i1] * (1 + 0.06 * fine + 0.05 * rn)[..., None]
    alb = alb * (0.8 + 0.2 * dome)[..., None]
    dirt = col([0.22, 0.19, 0.15]) * (1 + 0.2 * fine[..., None])
    alb = lerp(alb, dirt, gap)
    mossn = sstep(1.0, 1.8, noise(seed + 4, 2.0, 4) + gap * 1.2) * gap
    alb = lerp(alb, col([0.22, 0.27, 0.12]), mossn * 0.8)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 4), -0.3, 0.3) * 0.8)
    rough = 0.78 - dome * 0.08 + gap * 0.15 + 0.04 * rn
    return alb, h, rough, 7.0


def brick(seed=404):
    r = rng(seed)
    wx, wy = warp_coords(seed + 1, 1.6, 2.2, 10)
    nrows = 16
    rh = N // nrows
    edge = np.zeros((N, N), np.float32)
    bid = np.zeros((N, N), np.int32)
    nb = 0
    for ri in range(nrows):
        y0, y1 = ri * rh, (ri + 1) * rh
        cum = split_len(N, 8, r, 0.12)
        off = (ri % 2) * 64 + int(r.integers(-10, 10))
        band = (wy >= y0) & (wy < y1)
        c = (wx - off) % N
        idx = np.clip(np.searchsorted(cum, c, side="right") - 1, 0, 7)
        dx = np.minimum(c - cum[idx], cum[idx + 1] - c)
        dy = np.minimum(wy - y0, y1 - wy)
        edge[band] = np.minimum(dx, dy)[band]
        bid[band] = (idx + nb)[band]
        nb += 8
    pal = np.array([[0.43, 0.25, 0.19], [0.38, 0.22, 0.17], [0.47, 0.30, 0.22], [0.33, 0.21, 0.17],
                    [0.40, 0.31, 0.26]], np.float32)
    pc = pal[r.integers(0, len(pal), nb)] * r.uniform(0.85, 1.1, (nb, 1)).astype(np.float32)
    fine = noise(seed + 2, 1.3, 50)
    rn = noise(seed + 3, 2.0, 8)
    chipn = noise(seed + 4, 1.7, 16)
    gap = 3.0
    blk = sstep(gap, gap + 7, edge + chipn * 2.2)
    h = 0.15 + blk * (0.75 + 0.05 * rn + 0.03 * fine)
    mortar = 1 - sstep(gap - 1, gap + 2, edge + chipn * 2.2)
    alb = pc[bid] * (1 + 0.08 * fine + 0.06 * rn)[..., None]
    alb = lerp(alb, col([0.36, 0.34, 0.30]) * (1 + 0.1 * fine[..., None]), mortar)
    soot = sstep(0.2, 1.8, noise(seed + 5, 2.3, 2)) * 0.4
    alb = mul(alb, 1 - soot)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 4), -0.3, 0.3) * 0.8)
    rough = 0.86 + 0.04 * rn + mortar * 0.06
    return alb, h, rough, 5.0


def dirt(seed=505):
    r = rng(seed)
    rn = noise(seed, 2.1, 2)
    mid = noise(seed + 1, 1.8, 8)
    fine = noise(seed + 2, 1.2, 60)
    pts = r.uniform(0, N, (700, 2))
    f1, edge, i1, _ = voronoi(pts)
    rad = r.uniform(2.0, 9.0, 700).astype(np.float32)
    keep = r.random(700) < 0.55
    peb = np.sqrt(np.clip(1 - (f1 / rad[i1]) ** 2, 0, 1)) * keep[i1]
    h = 0.35 + 0.12 * rn + 0.06 * mid + 0.03 * fine + peb * 0.35
    alb = fill([0.34, 0.27, 0.20])
    alb = mul(alb, 1 + 0.12 * rn + 0.07 * mid + 0.06 * fine)
    pc = np.array([[0.42, 0.40, 0.37], [0.36, 0.32, 0.27], [0.30, 0.28, 0.26]], np.float32)[r.integers(0, 3, 700)]
    alb = lerp(alb, pc[i1] * (0.85 + 0.25 * peb)[..., None], sstep(0.05, 0.3, peb))
    dark = sstep(0.5, 1.8, noise(seed + 3, 2.4, 3)) * 0.25
    alb = mul(alb, 1 - dark)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 3), -0.3, 0.3) * 1.2)
    rough = 0.92 - peb * 0.1 - dark * 0.1
    return alb, h, rough, 5.0


def mud(seed=606):
    rn = noise(seed, 2.2, 2)
    mid = noise(seed + 1, 1.7, 10)
    fine = noise(seed + 2, 1.2, 60)
    ruts = noise(seed + 3, 2.4, 2, ax=5.0)
    churn = np.abs(noise(seed + 4, 1.9, 12))
    h = 0.45 + 0.12 * rn + 0.06 * churn - 0.1 * sstep(0.3, 1.4, ruts) + 0.02 * fine
    puddle = sstep(0.55, 0.75, sstep(0.9, 1.8, -rn * 0.8 + 0.5 * mid + sstep(0.3, 1.4, ruts)))
    h = lerp(h, np.float32(0.3), puddle)
    alb = fill([0.25, 0.20, 0.15])
    alb = mul(alb, 1 + 0.12 * rn + 0.08 * mid + 0.05 * fine + 0.06 * churn)
    alb = lerp(alb, col([0.15, 0.13, 0.11]), puddle * 0.85)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 3), -0.3, 0.3) * 1.2)
    rough = 0.82 - 0.66 * puddle + 0.04 * churn
    return alb, h, rough, 4.0


def grass(seed=707):
    r = rng(seed)
    soil = fill([0.20, 0.17, 0.12])
    patch = noise(seed, 2.2, 2)
    rgbc = Canvas("RGB", (0, 0, 0))
    hc = Canvas("L", 0)
    greens = np.array([[0.24, 0.31, 0.13], [0.30, 0.35, 0.16], [0.20, 0.27, 0.11], [0.36, 0.37, 0.19],
                       [0.40, 0.37, 0.22], [0.27, 0.30, 0.15]], np.float32)
    n = 26000
    xs = r.uniform(0, N, n)
    ys = r.uniform(0, N, n)
    pv = patch[ys.astype(int) % N, xs.astype(int) % N]
    for i in range(n):
        x, y = xs[i], ys[i]
        a = r.uniform(-math.pi, math.pi)
        L = r.uniform(7, 24)
        cidx = int(r.integers(0, 4)) if pv[i] < 0.6 else int(r.integers(2, 6))
        c = greens[cidx] * r.uniform(0.8, 1.15)
        mx, my = x + math.cos(a) * L * 0.5 + r.normal(0, 2), y + math.sin(a) * L * 0.5 + r.normal(0, 2)
        ex, ey = x + math.cos(a) * L, y + math.sin(a) * L
        cc = tuple(int(np.clip(v, 0, 1) * 255) for v in c)
        rgbc.line([(x, y), (mx, my), (ex, ey)], cc, 2)
        hc.line([(x, y), (mx, my), (ex, ey)], int(90 + 165 * (i / n)), 2)
    blades = np.asarray(rgbc.img, np.float32) / 255.0
    hb = hc.array()
    cover = blur((hb > 0).astype(np.float32), 0.6)
    alb = lerp(soil * (1 + 0.1 * patch[..., None]), blades, cover)
    alb = mul(alb, 1 + 0.08 * patch)
    h = 0.2 + 0.6 * hb + 0.05 * patch
    alb = mul(alb, 1.0 + np.clip(cavity(h, 2), -0.3, 0.3) * 0.6)
    rough = 0.88 - 0.05 * hb
    return alb, h, rough, 3.0


def forest_floor(seed=808):
    r = rng(seed)
    rn = noise(seed, 2.1, 2)
    fine = noise(seed + 1, 1.2, 60)
    rgbc = Canvas("RGB", (0, 0, 0))
    hc = Canvas("L", 0)
    # needles & tiny twigs
    for i in range(5000):
        x, y = r.uniform(0, N, 2)
        a = r.uniform(0, math.pi * 2)
        L = r.uniform(6, 16)
        c = np.array([0.33, 0.24, 0.15]) * r.uniform(0.6, 1.2)
        cc = tuple(int(v * 255) for v in np.clip(c, 0, 1))
        rgbc.line([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], cc, 1)
        hc.line([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], 70, 1)
    leafpal = np.array([[0.42, 0.28, 0.14], [0.36, 0.23, 0.13], [0.46, 0.35, 0.17], [0.30, 0.20, 0.13],
                        [0.40, 0.21, 0.13], [0.28, 0.27, 0.14], [0.22, 0.17, 0.12]], np.float32)
    nl = 2600
    for i in range(nl):
        x, y = r.uniform(0, N, 2)
        a = r.uniform(0, math.pi * 2)
        L = r.uniform(12, 30)
        W = L * r.uniform(0.3, 0.5)
        pts = []
        for t in np.linspace(0, 1, 9):
            pts.append((t * L - L / 2, math.sin(t * math.pi) ** 0.8 * W / 2))
        for t in np.linspace(1, 0, 9)[1:-1]:
            pts.append((t * L - L / 2, -math.sin(t * math.pi) ** 0.8 * W / 2))
        ca, sa = math.cos(a), math.sin(a)
        P = [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts]
        c = leafpal[int(r.integers(0, len(leafpal)))] * r.uniform(0.75, 1.15)
        rgbc.polygon(P, tuple(int(v * 255) for v in np.clip(c, 0, 1)))
        hc.polygon(P, int(110 + 140 * i / nl))
        # midrib
        rgbc.line([P[0], P[8]], tuple(int(v * 255 * 0.7) for v in np.clip(c, 0, 1)), 1)
    for i in range(140):
        x, y = r.uniform(0, N, 2)
        a = r.uniform(0, math.pi * 2)
        p = [(x, y)]
        for s in range(int(r.integers(3, 7))):
            a += r.normal(0, 0.35)
            x += math.cos(a) * 14
            y += math.sin(a) * 14
            p.append((x, y))
        w = int(r.integers(2, 5))
        rgbc.line(p, (int(0.26 * 255), int(0.19 * 255), int(0.13 * 255)), w)
        hc.line(p, 255, w)
    lay = np.asarray(rgbc.img, np.float32) / 255.0
    hl = hc.array()
    cover = blur((hl > 0).astype(np.float32), 0.5)
    soil = fill([0.19, 0.15, 0.11])
    alb = lerp(soil * (1 + 0.12 * rn + 0.05 * fine)[..., None], lay, cover)
    alb = mul(alb, 1 + 0.08 * rn)
    h = 0.15 + 0.7 * hl + 0.05 * rn
    alb = mul(alb, 1.0 + np.clip(cavity(h, 3), -0.35, 0.3) * 0.9)
    rough = 0.9 - 0.05 * hl
    return alb, h, rough, 4.0


def rock_cliff(seed=909):
    r = rng(seed)
    n1 = noise(seed, 2.2, 2)
    ridg = 1 - np.abs(noise(seed + 1, 2.0, 4))
    fine = noise(seed + 2, 1.4, 40)
    strn = noise(seed + 3, 2.4, 2, ax=4.0)
    strata = np.sin(YY / N * 2 * math.pi * 9 + strn * 2.2 + n1 * 0.6)
    ledge = sstep(0.3, 0.9, strata)
    pts = jittered_points(6, 9, seed + 9, 0.9)
    pts[:, 0] = (pts[:, 0] * 1.0) % N
    wx, wy = warp_coords(seed + 4, 14, 2.2, 3)
    f1, edge, i1, _ = voronoi(pts, wx, wy * 1.0)
    crack = 1 - sstep(0.8, 4.0, edge)
    facet = rng(seed + 11).uniform(-0.08, 0.08, len(pts)).astype(np.float32)[i1]
    h = 0.4 + 0.16 * n1 + 0.1 * ridg + 0.14 * ledge + 0.03 * fine + facet + 0.08 * sstep(0, 30, edge) - crack * 0.3
    alb = fill([0.41, 0.39, 0.36])
    band = noise(seed + 5, 2.0, 1, ax=12.0)
    alb[..., 0] += 0.012 * band
    alb[..., 2] -= 0.01 * band
    alb = mul(alb, 1 + 0.1 * n1 + 0.06 * fine + 0.16 * ledge - 0.12 * (1 - ridg))
    alb = lerp(alb, col([0.16, 0.15, 0.14]), crack * 0.85)
    lich = sstep(1.3, 1.8, noise(seed + 6, 1.9, 8)) * ledge
    alb = lerp(alb, col([0.47, 0.49, 0.38]), lich * 0.6)
    streak = sstep(0.4, 1.8, noise(seed + 7, 2.2, 3, ay=8.0)) * 0.3
    alb = mul(alb, 1 - streak)
    alb = mul(alb, 1.0 + np.clip(cavity(h, 6), -0.3, 0.3) * 1.0)
    rough = 0.88 + 0.04 * fine - streak * 0.2
    return alb, h, rough, 7.0


def wood_planks(seed=1001):
    r = rng(seed)
    nP = 8
    ph = N // nP
    wx, wy = warp_coords(seed + 1, 1.2, 2.2, 10)
    pid = (wy // ph).astype(np.int32) % nP
    ly = wy - pid * ph
    edge_y = np.minimum(ly, ph - ly)
    joints = [r.uniform(0, N, int(r.integers(1, 3))) for _ in range(nP)]
    edge_x = np.full((N, N), 999.0, np.float32)
    seg = np.zeros((N, N), np.int32)
    for p in range(nP):
        m = pid == p
        for j, jx in enumerate(joints[p]):
            d = np.abs(((wx - jx + N / 2) % N) - N / 2)
            edge_x[m] = np.minimum(edge_x[m], d[m])
            seg[m] += (((wx - jx) % N) < N / 2)[m].astype(np.int32) * (j + 1)
    board = pid * 7 + seg
    nb = nP * 7 + 8
    tone = r.uniform(0.8, 1.15, nb).astype(np.float32)
    grey = r.uniform(0.0, 0.5, nb).astype(np.float32)
    shift = r.uniform(0, 400, nb).astype(np.float32)
    grain = noise(seed + 2, 1.6, 3, ax=14.0)
    gfine = noise(seed + 3, 1.2, 20, ax=10.0)
    rings = np.sin((YY + shift[board] + grain * 18) * 0.35)
    e = np.minimum(edge_y, edge_x)
    blk = sstep(1.5, 6.0, e)
    h = 0.15 + blk * (0.7 + 0.05 * rings + 0.06 * grain + 0.03 * gfine)
    # nails near joints and plank ends
    nc = Canvas("L", 0)
    for p in range(nP):
        for jx in joints[p]:
            for sx in (-9, 9):
                for yy in (0.3, 0.7):
                    nc.ellipse(jx + sx, p * ph + yy * ph, 3.5, 3.5, 255)
    nails = nc.array()
    base = col([0.40, 0.31, 0.22])
    alb = fill(base)
    alb = mul(alb, tone[board] * (1 + 0.06 * rings + 0.08 * grain + 0.04 * gfine))
    alb = lerp(alb, col([0.36, 0.34, 0.31]) * (1 + 0.08 * gfine[..., None]), grey[board] * sstep(-0.5, 1.2, noise(seed + 4, 2.0, 3)))
    rot = sstep(0.8, 1.8, noise(seed + 5, 2.0, 3) + (1 - sstep(0, 25, e)) * 0.9) * 0.45
    alb = mul(alb, 1 - rot)
    alb = lerp(alb, col([0.08, 0.07, 0.06]), 1 - blk)
    alb = lerp(alb, col([0.16, 0.14, 0.13]), nails)
    h = h + nails * 0.08
    alb = mul(alb, 1.0 + np.clip(cavity(h, 3), -0.3, 0.3) * 0.7)
    rough = 0.78 + 0.05 * grain + rot * 0.15 - nails * 0.35
    return alb, h, rough, 5.0


def wood_grain(seed=1051):
    """Extra set (not in the contract list): clean grain for individual modelled boards/beams (no plank gaps)."""
    r = rng(seed)
    grain = noise(seed + 2, 1.6, 3, ax=16.0)
    gfine = noise(seed + 3, 1.2, 20, ax=12.0)
    rings = np.sin((YY + grain * 22 + 6 * noise(seed + 6, 2.2, 2)) * 2 * math.pi / 32.0)
    kn = Canvas("L", 0)
    for i in range(6):
        x, y = r.uniform(0, N, 2)
        kn.ellipse(x, y, r.uniform(8, 16), r.uniform(5, 9), 255)
    knots = blur(kn.array(), 3)
    streak = sstep(0.4, 1.8, noise(seed + 4, 1.8, 3, ax=12.0))
    h = 0.5 + 0.06 * rings + 0.08 * grain + 0.04 * gfine - 0.1 * knots - 0.05 * streak
    alb = fill([0.41, 0.31, 0.21])
    alb = mul(alb, 1 + 0.07 * rings + 0.09 * grain + 0.05 * gfine - 0.35 * knots - 0.2 * streak)
    grey = sstep(0.2, 1.6, noise(seed + 5, 2.0, 2)) * 0.45
    alb = lerp(alb, col([0.36, 0.34, 0.31]) * (1 + 0.08 * gfine[..., None]), grey)
    rough = 0.78 + 0.05 * grain + 0.1 * streak
    return alb, h, rough, 4.0


def bark(seed=1101):
    n1 = noise(seed, 1.9, 3, ay=6.0)
    n2 = noise(seed + 1, 1.8, 8, ay=5.0)
    fine = noise(seed + 2, 1.3, 50)
    ridge = np.clip(1 - np.abs(n1), 0, 1)
    ridge2 = np.clip(1 - np.abs(n2), 0, 1)
    hcrack = sstep(1.7, 2.3, noise(seed + 3, 2.0, 6, ax=4.0))
    h = 0.15 + 0.55 * ridge ** 1.5 + 0.2 * ridge2 + 0.03 * fine - 0.3 * hcrack * ridge
    h = np.clip(h, 0, 1)
    dark = col([0.13, 0.10, 0.08])
    light = col([0.36, 0.31, 0.26])
    alb = lerp(dark, light, sstep(0.15, 0.85, h))
    alb = mul(alb, 1 + 0.08 * fine + 0.06 * noise(seed + 4, 2.0, 2))
    lich = sstep(1.2, 1.8, noise(seed + 5, 2.0, 5)) * sstep(0.4, 0.7, h)
    alb = lerp(alb, col([0.36, 0.40, 0.29]), lich * 0.5)
    moss = sstep(1.3, 1.9, noise(seed + 6, 2.2, 3)) * (1 - sstep(0.3, 0.6, h))
    alb = lerp(alb, col([0.2, 0.25, 0.11]), moss * 0.7)
    rough = 0.9 - 0.04 * h
    return alb, h, rough, 9.0


def moss(seed=1201):
    r = rng(seed)
    pts = r.uniform(0, N, (900, 2))
    f1, edge, i1, _ = voronoi(pts)
    clump = np.sqrt(sstep(0.0, 22.0, edge + noise(seed + 7, 1.6, 20) * 6))
    clump = 0.5 * clump + 0.5 * sstep(-1.5, 1.5, noise(seed + 8, 1.7, 12))
    n1 = noise(seed, 2.0, 3)
    fine = noise(seed + 1, 1.0, 90)
    fuzz = noise(seed + 2, 0.8, 200)
    h = 0.2 + 0.5 * clump + 0.12 * n1 + 0.04 * fine + 0.03 * fuzz
    base = col([0.21, 0.28, 0.11])
    tip = col([0.38, 0.41, 0.18])
    dry = col([0.36, 0.33, 0.18])
    alb = lerp(base * 0.55, base, sstep(0.1, 0.5, h))
    alb = lerp(alb, tip, sstep(0.55, 0.95, h + 0.08 * fuzz) * 0.8)
    alb = lerp(alb, dry, sstep(0.8, 1.8, noise(seed + 3, 2.2, 2)) * 0.6)
    alb = mul(alb, 1 + 0.08 * fine + 0.08 * fuzz)
    rough = 0.93 - 0.05 * clump
    return alb, h, rough, 4.0


def metal_iron(seed=1301):
    r = rng(seed)
    pts = r.uniform(0, N, (500, 2))
    f1, edge, i1, _ = voronoi(pts)
    rad = 30.0
    dimple = (f1 / rad) ** 2
    n1 = noise(seed, 2.0, 3)
    fine = noise(seed + 1, 1.2, 60)
    h = 0.5 + 0.12 * np.clip(dimple, 0, 1) + 0.05 * n1 + 0.01 * fine
    scr = Canvas("L", 0)
    for i in range(160):
        x, y = r.uniform(0, N, 2)
        a = r.normal(0.3, 0.6)
        L = r.uniform(20, 120)
        scr.line([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], int(r.integers(80, 255)), 1)
    scratches = scr.array()
    rustm = sstep(0.6, 1.5, noise(seed + 2, 2.2, 3) + 0.5 * noise(seed + 3, 1.3, 30))
    pit = (noise(seed + 4, 0.5, 200) > 2.2).astype(np.float32) * rustm
    h = h - scratches * 0.03 + rustm * 0.06 * (1 + fine * 0.5) - pit * 0.08
    alb = fill([0.25, 0.25, 0.26])
    alb = mul(alb, 1 + 0.08 * n1 + 0.05 * fine)
    alb = alb + scratches[..., None] * 0.12
    rust = lerp(col([0.33, 0.19, 0.11]), col([0.44, 0.28, 0.15]), sstep(-1, 1.5, fine))
    alb = lerp(alb, rust, rustm * 0.9)
    alb = mul(alb, 1 - pit * 0.5)
    rough = 0.48 + 0.08 * n1 - scratches * 0.15 + rustm * 0.42
    return alb, h, rough, 5.0


def cloth(seed=1401):
    per = 8.0
    u = XX / per * 2 * math.pi
    v = YY / per * 2 * math.pi
    slub = noise(seed, 1.5, 6, ax=10.0) * 0.15
    slub2 = noise(seed + 1, 1.5, 6, ay=10.0) * 0.15
    warp_t = 0.5 + 0.5 * np.sin(v + slub * 4)
    weft_t = 0.5 + 0.5 * np.sin(u + slub2 * 4)
    check = ((np.floor(XX / per) + np.floor(YY / per)) % 2).astype(np.float32)
    h = lerp(warp_t * (0.8 + slub), weft_t * (0.8 + slub2), check)
    n1 = noise(seed + 2, 2.2, 2)
    h = 0.4 + 0.35 * h + 0.08 * n1
    alb = fill([0.52, 0.48, 0.41])
    alb = mul(alb, 0.82 + 0.25 * h + 0.06 * n1)
    stain = sstep(0.6, 1.8, noise(seed + 3, 2.3, 2)) * 0.35
    alb = lerp(alb, col([0.30, 0.25, 0.19]), stain)
    alb = mul(alb, 1 - 0.15 * sstep(1.0, 2.0, noise(seed + 4, 1.5, 12)))
    rough = 0.94 - 0.03 * h
    return alb, h, rough, 3.0


def thatch(seed=1501):
    r = rng(seed)
    rgbc = Canvas("RGB", (0, 0, 0))
    hc = Canvas("L", 0)
    courses = 6
    ch = N / courses
    pal = np.array([[0.49, 0.42, 0.26], [0.42, 0.36, 0.23], [0.36, 0.32, 0.23], [0.30, 0.27, 0.20],
                    [0.45, 0.41, 0.30]], np.float32)
    order = []
    for c in range(courses):
        for i in range(2600):
            order.append((c, i))
    for c, i in order:
        x = r.uniform(0, N)
        y0 = c * ch + ch * 0.5 + r.uniform(-10, 10)
        L = r.uniform(ch * 0.9, ch * 1.45)
        a = math.pi / 2 + r.normal(0, 0.07)
        ex, ey = x + math.cos(a) * L, y0 + math.sin(a) * L
        cc = pal[int(r.integers(0, len(pal)))] * r.uniform(0.75, 1.15)
        t = i / 2600.0
        rgbc.line([(x, y0), (ex, ey)], tuple(int(v * 255) for v in np.clip(cc, 0, 1)), int(r.integers(2, 4)))
        hc.line([(x, y0), (ex, ey)], int(60 + 190 * t), 2)
    lay = np.asarray(rgbc.img, np.float32) / 255.0
    hl = hc.array()
    lc = ((YY - ch * 0.5) % ch) / ch
    shade = 0.65 + 0.35 * sstep(0.0, 0.5, lc)
    h = 0.2 + 0.5 * hl + 0.25 * lc
    alb = mul(lay, shade * (1 + 0.1 * noise(seed + 1, 2.2, 2)))
    aged = sstep(0.3, 1.6, noise(seed + 2, 2.2, 2)) * 0.5
    alb = lerp(alb, col([0.27, 0.26, 0.21]), aged)
    mossm = sstep(1.3, 2.0, noise(seed + 3, 2.1, 3))
    alb = lerp(alb, col([0.24, 0.28, 0.13]), mossm * 0.6)
    alb = lerp(col([0.1, 0.09, 0.07]), alb, blur((hl > 0).astype(np.float32), 0.6))
    rough = np.full((N, N), 0.9, np.float32)
    return alb, h, rough, 5.0


def sand_path(seed=1601):
    r = rng(seed)
    n1 = noise(seed, 2.2, 2)
    grain = noise(seed + 1, 0.4, 300)
    mid = noise(seed + 2, 1.7, 12)
    pts = r.uniform(0, N, (500, 2))
    f1, edge, i1, _ = voronoi(pts)
    rad = r.uniform(1.5, 6.0, 500).astype(np.float32)
    keep = r.random(500) < 0.5
    peb = np.sqrt(np.clip(1 - (f1 / rad[i1]) ** 2, 0, 1)) * keep[i1]
    tracks = sstep(0.4, 1.5, noise(seed + 3, 2.4, 2, ax=6.0))
    h = 0.4 + 0.08 * n1 + 0.03 * mid + 0.02 * grain + 0.3 * peb - 0.06 * tracks
    alb = fill([0.51, 0.45, 0.35])
    alb = mul(alb, 1 + 0.07 * n1 + 0.05 * mid + 0.06 * grain)
    alb = mul(alb, 1 - 0.12 * tracks)
    pc = np.array([[0.46, 0.44, 0.40], [0.38, 0.34, 0.29], [0.55, 0.50, 0.42]], np.float32)[r.integers(0, 3, 500)]
    alb = lerp(alb, pc[i1] * (0.85 + 0.2 * peb)[..., None], sstep(0.05, 0.3, peb))
    alb = mul(alb, 1.0 + np.clip(cavity(h, 3), -0.3, 0.3) * 1.2)
    rough = 0.92 - peb * 0.1
    return alb, h, rough, 4.0


SETS = {
    "stone_blocks": stone_blocks, "stone_floor": stone_floor, "cobblestone": cobblestone, "brick": brick,
    "dirt": dirt, "mud": mud, "grass": grass, "forest_floor": forest_floor, "rock_cliff": rock_cliff,
    "wood_planks": wood_planks, "wood_grain": wood_grain, "bark": bark, "moss": moss, "metal_iron": metal_iron, "cloth": cloth,
    "thatch": thatch, "sand_path": sand_path,
}


# ----------------------------------------------------------------------------------------------------------------
def leaf_polygon(L, W, tip=1.0):
    pts = []
    ts = np.linspace(0, 1, 10)
    for t in ts:
        pts.append((t * L, (math.sin(t * math.pi) ** 0.9) * (1 - 0.35 * t) * W / 2))
    for t in ts[::-1][1:-1]:
        pts.append((t * L, -(math.sin(t * math.pi) ** 0.9) * (1 - 0.35 * t) * W / 2))
    return pts


def dilate_rgb(rgb, a):
    """Push colour into transparent texels so mip-mapped alpha edges do not fringe dark."""
    w = blur(a, 6) + 1e-4
    fillc = np.stack([blur(rgb[..., c] * a, 6) for c in range(3)], -1) / w[..., None]
    w2 = blur(a, 24) + 1e-4
    fill2 = np.stack([blur(rgb[..., c] * a, 24) for c in range(3)], -1) / w2[..., None]
    fillc = np.where((blur(a, 6) > 0.02)[..., None], fillc, fill2)
    return lerp(fillc, rgb, a)


def leaves_atlas(seed=1701):
    """2x2 atlas of 512 px alpha-cut clusters: [0] broadleaf green, [1] dark olive, [2] pine spray, [3] autumn."""
    r = rng(seed)
    S = 1024
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pals = [
        [[0.26, 0.34, 0.14], [0.31, 0.38, 0.16], [0.22, 0.29, 0.12], [0.35, 0.40, 0.19]],
        [[0.20, 0.25, 0.12], [0.25, 0.28, 0.13], [0.17, 0.21, 0.10], [0.28, 0.30, 0.16]],
        [[0.16, 0.24, 0.13], [0.20, 0.28, 0.15], [0.13, 0.20, 0.11], [0.24, 0.30, 0.17]],
        [[0.48, 0.30, 0.13], [0.42, 0.24, 0.11], [0.50, 0.38, 0.16], [0.34, 0.27, 0.12]],
    ]

    def c255(c, a=255):
        return tuple(int(np.clip(v, 0, 1) * 255) for v in c) + (a,)

    for q in range(4):
        ox, oy = (q % 2) * 512, (q // 2) * 512
        cx, cy = ox + 256, oy + 256
        pal = pals[q]
        if q == 2:
            # pine: central twig with needle sprays
            for b in range(7):
                a0 = -math.pi / 2 + (b - 3) * 0.42 + r.normal(0, 0.05)
                L = 200 - abs(b - 3) * 22
                x0, y0 = cx, cy + 190
                x1, y1 = x0 + math.cos(a0) * L * 1.8, y0 + math.sin(a0) * L * 1.8
                x1 = np.clip(x1, ox + 40, ox + 472)
                y1 = np.clip(y1, oy + 40, oy + 472)
                d.line([(x0, y0), (x1, y1)], fill=c255([0.2, 0.15, 0.1]), width=5)
                for t in np.linspace(0.1, 1.0, 38):
                    px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                    for side in (-1, 1):
                        na = a0 + side * r.uniform(0.6, 1.1)
                        nl = r.uniform(26, 44) * (1.1 - 0.4 * t)
                        ex, ey = px + math.cos(na) * nl, py + math.sin(na) * nl
                        ex = np.clip(ex, ox + 8, ox + 504)
                        ey = np.clip(ey, oy + 8, oy + 504)
                        c = np.array(pal[int(r.integers(0, 4))]) * r.uniform(0.8, 1.2)
                        d.line([(px, py), (ex, ey)], fill=c255(c), width=3)
            continue
        # broadleaf clusters: several twigs from lower centre, leaves along them
        twigs = []
        for b in range(5):
            a0 = -math.pi / 2 + (b - 2) * 0.55 + r.normal(0, 0.1)
            L = r.uniform(170, 220)
            twigs.append((cx + r.normal(0, 8), cy + 200, a0, L))
        leaves = []
        for (x0, y0, a0, L) in twigs:
            x1, y1 = x0 + math.cos(a0) * L, y0 + math.sin(a0) * L
            d.line([(x0, y0), (x1, y1)], fill=c255([0.22, 0.17, 0.11]), width=4)
            for t in np.linspace(0.25, 1.0, 7):
                px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                for side in (-1, 1):
                    la = a0 + side * r.uniform(0.5, 1.1)
                    ll = r.uniform(58, 86)
                    leaves.append((px, py, la, ll))
            leaves.append((x1, y1, a0, r.uniform(64, 86)))
        order = r.permutation(len(leaves))
        for k in order:
            px, py, la, ll = leaves[k]
            poly = leaf_polygon(ll, ll * r.uniform(0.45, 0.6))
            ca, sa = math.cos(la), math.sin(la)
            P = [(px + x * ca - y * sa, py + x * sa + y * ca) for x, y in poly]
            P = [(float(np.clip(x, ox + 6, ox + 506)), float(np.clip(y, oy + 6, oy + 506))) for x, y in P]
            c = np.array(pal[int(r.integers(0, 4))]) * r.uniform(0.8, 1.2)
            d.polygon(P, fill=c255(c))
            # lit half / shaded half
            half = [P[0]] + P[1:10]
            d.polygon(half, fill=c255(c * 1.12))
            d.line([P[0], P[9]], fill=c255(c * 0.7), width=2)
    a = np.asarray(img, np.float32) / 255.0
    rgb, al = a[..., :3], a[..., 3]
    al = (al > 0.5).astype(np.float32)
    rgb = dilate_rgb(rgb, al)
    return np.concatenate([rgb, al[..., None]], -1)


def grass_blades(seed=1801):
    """RGBA blade strip: left half green, right half dry. Roots at the bottom edge."""
    r = rng(seed)
    S = 1024
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for half in (0, 1):
        for i in range(150):
            x0 = half * 512 + r.uniform(20, 492)
            H = r.uniform(420, 980)
            bend = r.normal(0, 0.35) * H * 0.35
            w0 = r.uniform(9, 16)
            seg = 14
            left, right = [], []
            if half == 0:
                base = np.array([0.12, 0.16, 0.07]) * r.uniform(0.8, 1.2)
                tipc = np.array([0.34, 0.40, 0.17]) * r.uniform(0.8, 1.15)
                if r.random() < 0.15:
                    tipc = np.array([0.45, 0.43, 0.24])
            else:
                base = np.array([0.20, 0.18, 0.09]) * r.uniform(0.8, 1.2)
                tipc = np.array([0.50, 0.44, 0.26]) * r.uniform(0.85, 1.12)
            for s in range(seg + 1):
                t = s / seg
                x = x0 + bend * t * t
                y = S - 2 - t * H
                w = w0 * (1 - t) ** 0.8 + 0.5
                left.append((x - w / 2, y))
                right.append((x + w / 2, y))
            for s in range(seg):
                t = (s + 0.5) / seg
                c = base + (tipc - base) * t ** 0.7
                poly = [left[s], right[s], right[s + 1], left[s + 1]]
                poly = [(float(np.clip(px, half * 512 + 3, half * 512 + 508)), py) for px, py in poly]
                d.polygon(poly, fill=tuple(int(np.clip(v, 0, 1) * 255) for v in c) + (255,))
    a = np.asarray(img, np.float32) / 255.0
    rgb, al = a[..., :3], (a[..., 3] > 0.5).astype(np.float32)
    rgb = dilate_rgb(rgb, al)
    return np.concatenate([rgb, al[..., None]], -1)


# ----------------------------------------------------------------------------------------------------------------
def tile_check(name, alb, nrm):
    a = Image.fromarray((np.clip(alb, 0, 1) * 255).astype(np.uint8))
    n = Image.fromarray((np.clip(nrm, 0, 1) * 255).astype(np.uint8))
    out = Image.new("RGB", (2048, 1024), (0, 0, 0))
    a2 = Image.new("RGB", (2048, 2048))
    n2 = Image.new("RGB", (2048, 2048))
    for i in range(2):
        for j in range(2):
            a2.paste(a, (i * 1024, j * 1024))
            n2.paste(n, (i * 1024, j * 1024))
    out.paste(a2.resize((1024, 1024), Image.LANCZOS), (0, 0))
    out.paste(n2.resize((1024, 1024), Image.LANCZOS), (1024, 0))
    out.save(os.path.join(EVI, f"{name}_2x2.png"))


def main(names):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(EVI, exist_ok=True)
    report = []
    thumbs = []
    for name in names:
        t = time.time()
        if name == "leaves_atlas":
            rgba = leaves_atlas()
            save_rgba(os.path.join(OUT, "leaves_atlas.png"), rgba)
            thumbs.append((name, rgba))
            report.append(f"{name:14s} RGBA atlas (not tiled)  {time.time() - t:.1f}s")
            continue
        if name == "grass_blades":
            rgba = grass_blades()
            save_rgba(os.path.join(OUT, "grass_blades.png"), rgba)
            thumbs.append((name, rgba))
            report.append(f"{name:14s} RGBA strip (not tiled)  {time.time() - t:.1f}s")
            continue
        alb, h, rough, ns = SETS[name]()
        alb = np.clip(alb, 0, 1)
        h = np.clip(h, 0, 1)
        nrm = normal_from_height(h * 255.0 / 64.0, ns * 0.35)
        save_rgb(os.path.join(OUT, f"{name}_albedo.png"), alb)
        save_rgb(os.path.join(OUT, f"{name}_normal.png"), nrm)
        save_gray(os.path.join(OUT, f"{name}_rough.png"), np.clip(rough, 0.05, 1))
        tile_check(name, alb, nrm)
        sa = seam_score(alb.mean(-1))
        sn = seam_score(nrm[..., 0])
        report.append(f"{name:14s} seam(albedo x,y)={sa[0]:.2f},{sa[1]:.2f}  seam(normal x,y)={sn[0]:.2f},{sn[1]:.2f}  "
                      f"mean albedo={alb.reshape(-1, 3).mean(0).round(3).tolist()}  {time.time() - t:.1f}s")
        thumbs.append((name, alb))
        print(report[-1], flush=True)
    # overview sheet
    if len(thumbs) > 1:
        cols = 6
        rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 260, rows * 284), (24, 22, 28))
        dr = ImageDraw.Draw(sheet)
        for k, (nm, im) in enumerate(thumbs):
            if im.shape[-1] == 4:
                bg = np.full(im.shape[:2] + (3,), 0.5, np.float32)
                chk = ((np.indices(im.shape[:2]).sum(0) // 64) % 2)[..., None] * 0.15 + 0.35
                rgb = im[..., :3] * im[..., 3:] + chk * (1 - im[..., 3:])
            else:
                rgb = im
            th = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).resize((256, 256), Image.LANCZOS)
            x, y = (k % cols) * 260 + 2, (k // cols) * 284 + 2
            sheet.paste(th, (x, y))
            dr.text((x + 4, y + 262), nm, fill=(230, 220, 200))
        sheet.save(os.path.join(EVI, "textures_overview.png"))
    with open(os.path.join(EVI, "seam_report.txt"), "a" if len(names) < len(SETS) + 2 else "w") as f:
        f.write("# seam score = mean |first-last column/row| / mean interior neighbour diff (~1 == seamless)\n")
        f.write("\n".join(report) + "\n")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    names = args if args else list(SETS.keys()) + ["leaves_atlas", "grass_blades"]
    main(names)
