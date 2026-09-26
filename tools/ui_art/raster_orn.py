"""Shared ornament builders for the raster UI art (frames, bands, filigree, runes)."""
from __future__ import annotations

import math

import numpy as np

from rast import (Canvas, MAT, C, cov, sd_circle, sd_box, sd_rect, sd_poly, sd_stroke, union, sub, inter, ring_of, shell,
                  profile, metal, shade, groove_h, paint, gem, blur, spiral, arc, bez3, bez2, catmull, xf, star, ngon, leaf,
                  canvas_noise, fnoise, light_terms, ramp, cmix, F)

AETHER = "#7ff3ff"
AETHER_HI = "#d8fdff"
GOLD_C = "#f5cc75"
BRONZE_C = "#b88c52"
EMBER = "#f2731f"
BLOOD = "#b81a1a"
MANA = "#3373f2"
ARCANE_C = "#9e73ff"
PARCH = "#ebdcbd"


def diag_mirror(pts):
    return [(y, x) for x, y in pts]


def place(pts, ox, oy, sx, sy, s=1.0):
    """Map local corner coords (x,y >= 0 pointing inward) to canvas coords at corner (ox,oy) with signs sx,sy."""
    return [(ox + sx * x * s, oy + sy * y * s) for x, y in pts]


def filigree_corner_sd(cv, ox, oy, sx, sy, S=110.0, plate=True, arms=True, scroll=True, thick=1.0):
    """Gold corner filigree (symmetric about the corner diagonal). Returns (sd_union, gem_center)."""
    k = S / 110.0
    parts = []
    half = []  # (points, w0, w1) strokes in local coords for one half; mirrored across the diagonal
    if arms:
        # arm hugging the edge, tapering, ending in an inward curl
        arm = [(18, 9), (40, 8.5), (64, 8), (84, 9.5)]
        curl = spiral(90, 18, 9, 1.5, -math.pi / 2 - 0.2, math.pi * 1.35, 30)
        half.append((catmull(arm, 6) + curl[1:], 7.0 * thick, 2.2 * thick))
        # thin secondary tendril with a leaf
        ten = catmull([(30, 18), (46, 20), (58, 28), (62, 38)], 8)
        half.append((ten, 3.0 * thick, 1.0 * thick))
        parts.append(("leaf", leaf((44, 19), (60, 13), 6.5, bend=-1.0)))
    if scroll:
        # diagonal S-scroll from the plate into the panel
        sc = catmull([(34, 30), (44, 36), (50, 48), (48, 58)], 8) + spiral(56, 58, 8, 1.2, math.pi, math.pi * 2.6, 26)[1:]
        half.append((sc, 3.6 * thick, 1.4 * thick))
    sds = []
    for pts, w0, w1 in half:
        for P in (pts, diag_mirror(pts)):
            sds.append(sd_stroke(cv, place([(x * k, y * k) for x, y in P], ox, oy, sx, sy), w0 * k, w1 * k))
    for kind, P in parts:
        for Q in (P, diag_mirror(P)):
            sds.append(sd_poly(cv, place([(x * k, y * k) for x, y in Q], ox, oy, sx, sy), margin=3))
    gc = None
    if plate:
        # diamond plate on the corner with a quatrefoil back
        c = 24 * k
        dia = [(c, c - 22 * k), (c + 22 * k, c), (c, c + 22 * k), (c - 22 * k, c)]
        sds.append(sd_poly(cv, place(dia, ox, oy, sx, sy), margin=4))
        for ang in (0, 90, 180, 270):
            a = math.radians(ang + 45)
            px, py = c + math.cos(a) * 17 * k, c + math.sin(a) * 17 * k
            sds.append(sd_circle(cv, *place([(px, py)], ox, oy, sx, sy)[0], 8.5 * k))
        gc = place([(c, c)], ox, oy, sx, sy)[0]
    return union(*sds), gc


def rune_strokes(rng, cx, cy, s):
    """A random angular rune glyph (list of polylines) centred on (cx,cy), size s."""
    g = [(-0.5, -0.5), (0, -0.5), (0.5, -0.5), (-0.5, 0), (0, 0), (0.5, 0), (-0.5, 0.5), (0, 0.5), (0.5, 0.5)]
    lines = [[(cx, cy - s / 2), (cx, cy + s / 2)]]  # stave
    for _ in range(rng.integers(1, 4)):
        a = g[rng.integers(0, 9)]
        b = g[rng.integers(0, 9)]
        if a == b:
            continue
        lines.append([(cx + a[0] * s * 0.6, cy + a[1] * s), (cx + b[0] * s * 0.6, cy + b[1] * s)])
    return lines


def rune_band_sd(cv, x0, x1, y, s, seed=1, gap=1.6):
    """Row of rune glyph strokes (distance to centre lines) from x0..x1 at height y."""
    rng = np.random.default_rng(seed)
    sds = []
    x = x0 + s * 0.4
    while x < x1 - s * 0.4:
        for ln in rune_strokes(rng, x, y, s):
            sds.append(sd_stroke(cv, ln, 0.0))
        x += s * gap
    return union(*sds) if sds else cv.empty()


def hammered(cv, seed, amp=0.6, scale=1.0):
    return canvas_noise(cv, seed, beta=2.6, scale=scale) * amp


def draw_part(cv, sd, mat, bevel=3.0, kind="round", shadow=(1.2, 2.0, 2.2, 0.75), extra_h=None, noise=None,
              noise_amt=0.0, flat=None, height=1.0, bright=1.0):
    if shadow:
        dx, dy, bl, op = shadow
        cv.shadow(cov(cv, sd), dx, dy, bl, op)
    cv.put(metal(cv, sd, mat, bevel=bevel, kind=kind, extra_h=extra_h, noise=noise, noise_amt=noise_amt, flat=flat,
                 height=height, bright=bright))


def inner_shadow(cv, inner_sd, width, op=0.8, color="#000000"):
    """Darkening that falls off from the inner boundary of a well (inner_sd < 0 inside the well)."""
    t = np.clip(1 + inner_sd / width, 0, 1) * cov(cv, inner_sd)  # 1 at edge -> 0 at depth `width`
    cv.over(color, t ** 1.6, op)


def center_fill(cv, x0, y0, x1, y1, base="#16110e", seed=3, amt=0.035, cw=None, ch=None, runes=0.0, rune_seed=5,
                cells=None):
    """Recessed panel body. The noise is periodic over (cw, ch) design px so the 9-slice centre tiles seamlessly."""
    H, W = cv.H, cv.W
    s = cv.ss
    cw = cw or cv.w
    ch = ch or cv.h
    n1 = fnoise(int(ch * s), int(cw * s), seed, beta=2.2, lo=1.0)
    n2 = fnoise(int(ch * s), int(cw * s), seed + 1, beta=1.0, lo=3.0)
    tile = n1 * amt + n2 * amt * 0.35
    # tile over the full canvas, phase-aligned to the centre patch origin
    oy = int(round(y0 * s)) % tile.shape[0]
    ox = int(round(x0 * s)) % tile.shape[1]
    reps_y = H // tile.shape[0] + 2
    reps_x = W // tile.shape[1] + 2
    big = np.tile(tile, (reps_y, reps_x))
    big = np.roll(np.roll(big, oy, axis=0), ox, axis=1)[:H, :W]
    rgb = np.clip(C(base)[None, None, :] * (1 + big[..., None] * 6.0), 0, 1).astype(F)
    if runes and cells:
        # faint periodic rune lattice: `cells` glyphs per centre patch in each direction
        nx, ny = cells
        gw, gh = cw / nx, ch / ny
        rng = np.random.default_rng(rune_seed)
        glyphs = []
        for j in range(ny):
            for i in range(nx):
                glyphs.append((i, j, rune_strokes(rng, 0, 0, min(gw, gh) * 0.42)))
        sds = []
        for ry in range(-1, int(cv.h / ch) + 2):
            for rx in range(-1, int(cv.w / cw) + 2):
                for i, j, lines in glyphs:
                    cx = x0 + rx * cw + (i + 0.5) * gw + ((j % 2) * gw * 0.5)
                    cy = y0 + ry * ch + (j + 0.5) * gh
                    if -gw < cx < cv.w + gw and -gh < cy < cv.h + gh:
                        for ln in lines:
                            sds.append(sd_stroke(cv, [(cx + a, cy + b) for a, b in ln], 0.0, margin=2))
        if sds:
            d = union(*sds)
            m = np.clip(1 - np.abs(d) / 1.1, 0, 1)
            rgb = rgb * (1 - m[..., None] * runes) + C("#6a5a48") * (m * runes * 0.5)[..., None]
    return rgb


def corner_bastion(cv, ox, oy, sx, sy, S=112.0, plate_mat="gold_dim", fil_mat="gold", gem_mat="aether", gem_glow=AETHER,
                   fil=True, arm_len=1.0, glow_str=0.6):
    """Heavy corner piece: chamfered plate with a recessed gem socket, gold arms along both edges ending in curls,
    and a diagonal fleur scroll pointing into the panel. Local coords: corner at (0,0), +x/+y inward."""
    k = S / 112.0

    def P(pts):
        return place([(x * k, y * k) for x, y in pts], ox, oy, sx, sy)

    both = lambda pts: (pts, diag_mirror(pts))
    # --- filigree (under the plate)
    if fil:
        sds = []
        for pts in both(catmull([(50, 9), (70, 8.5), (86, 9.5)], 6) + spiral(92, 19, 10, 1.6, -math.pi / 2 - 0.15,
                                                                               math.pi * 1.25, 30)[1:]):
            sds.append(sd_stroke(cv, P([(x, y) for x, y in pts]), 8.0 * k, 2.4 * k))
        for pts in both(catmull([(52, 30), (64, 30), (74, 36), (78, 46)], 8) + spiral(72, 50, 6, 1.2, 0.0, math.pi * 1.9, 20)[1:]):
            sds.append(sd_stroke(cv, P(pts), 4.2 * k, 1.4 * k))
        for pts in both(leaf((58, 20), (80, 22), 7.5, bend=1.2)):
            sds.append(sd_poly(cv, P(pts), margin=3))
        # diagonal fleur
        sds.append(sd_poly(cv, P(leaf((44, 44), (84, 84), 13)), margin=3))
        for pts in both(catmull([(52, 58), (60, 72), (58, 84)], 8) + spiral(50, 84, 8, 1.4, 0.0, math.pi * 1.7, 22)[1:]):
            sds.append(sd_stroke(cv, P(pts), 4.6 * k, 1.4 * k))
        fsd = union(*sds)
        draw_part(cv, fsd, MAT[fil_mat], bevel=3.0 * k, shadow=(1.4, 2.4, 2.4, 0.85))
    # --- plate
    plate = [(0, 0), (60, 0), (60, 38), (38, 60), (0, 60)]
    psd = sd_poly(cv, P(plate), margin=6)
    rim = MAT[plate_mat]
    draw_part(cv, psd, rim, bevel=5.0 * k, shadow=(2, 3, 4, 0.9), noise=canvas_noise(cv, 91, 2.0), noise_amt=0.05)
    inner = [(8, 8), (52, 8), (52, 35), (35, 52), (8, 52)]
    isd = sd_poly(cv, P(inner), margin=4)
    # recessed dark socket field with engraved bevel (inverted height)
    h = -profile(isd, 3.0 * k, "round") * 3.0 * k
    from rast import shade as _shade
    rgb = _shade(cv, h, MAT["iron"], flat_level=0.45)
    cv.put((rgb, cov(cv, isd)))
    # gold ring + gem
    gx, gy = P([(29, 29)])[0]
    ring = ring_of(sd_circle(cv, gx, gy, 16.5 * k), 4.0 * k)
    draw_part(cv, ring, MAT["gold"], bevel=2.0 * k, shadow=(0.8, 1.4, 1.6, 0.8))
    # four tiny studs on the ring
    for a in range(4):
        ang = math.pi / 4 + a * math.pi / 2
        s_ = sd_circle(cv, gx + math.cos(ang) * 16.5 * k, gy + math.sin(ang) * 16.5 * k, 2.6 * k)
        draw_part(cv, s_, MAT["gold"], bevel=2.6 * k, shadow=None)
    if gem_mat:
        gem(cv, gx, gy, 11.0 * k, MAT[gem_mat], glow=gem_glow, glow_sigma=9 * k, glow_str=glow_str, setting=None)
    return (gx, gy)


def aether_channel(cv, sd_line, core=1.0, glow_sigma=3.0, strength=0.9, color=AETHER, core_color=AETHER_HI):
    """Luminous line along the zero set of an unsigned/line distance field (sd_line >= 0 near the channel)."""
    m = np.clip(1 - np.abs(sd_line) / (core + 1.0 / cv.ss), 0, 1)
    cv.over("#020608", np.clip(1 - np.abs(sd_line) / (core * 2.6), 0, 1), 0.85)   # dark groove
    cv.glow(m, color, glow_sigma, strength, gain=3.0)
    cv.glow(m, color, glow_sigma * 0.4, strength * 0.8, gain=2.0)
    cv.over(color, m, strength)
    cv.over(core_color, np.clip(1 - np.abs(sd_line) / (core * 0.55 + 0.3 / cv.ss), 0, 1), strength)
    return m
