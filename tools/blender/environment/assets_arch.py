"""Modular architecture: walls, pillars, arches, stairs, floor, beam, gate (2 m grid, walls 4 m x 4 m x 0.8 m)."""
import math

from mathutils import Vector, noise as mnoise

from kit import *  # noqa
from masonry import *  # noqa
from registry import asset

WL, WH, WT = 4.0, 4.0, 0.8


# ---------------------------------------------------------------------------------------------------------------
def moss_drip(k, x, ztop, length, face_y, width=0.3, side=-1, M=None):
    """Moss clump hanging down a wall face: a short cap band with uneven dripping tendrils.
    side=-1 -> -Y face, +1 -> +Y face."""
    r = k.r
    n = r.randint(4, 7)
    top = []
    for i in range(n * 2 + 1):
        t = i / (n * 2)
        top.append((x - width / 2 + width * t, ztop + r.uniform(-0.01, 0.03)))
    bot = []
    for i in range(n * 2, -1, -1):
        t = i / (n * 2)
        edge = min(t, 1 - t) * 2
        if i % 2 == 1:
            drop = length * r.uniform(0.25, 1.0) * (0.4 + 0.6 * edge ** 0.5)
        else:
            drop = length * r.uniform(0.06, 0.16)
        bot.append((x - width / 2 + width * t + r.uniform(-0.01, 0.01), ztop - drop))
    outline = top + bot
    t = prism(outline[::-1] if side < 0 else outline, 0.022)
    jitter(t, r, 0.005)
    k.put(t, "BH_Moss", M=(M or T()) @ T(0, face_y + side * 0.012, 0), tint=r.uniform(0.6, 0.85))


def moss_top(k, x0, x1, z, thick, n=3, M=None):
    r = k.r
    for _ in range(n):
        w = r.uniform(0.25, 0.6)
        x = r.uniform(x0 + w / 2, x1 - w / 2)
        t = box(w, r.uniform(0.25, min(0.6, thick)), 0.05, bev=0.02)
        jitter(t, r, 0.02)
        k.put(t, "BH_Moss", M=(M or T()) @ TRS(x, r.uniform(-0.1, 0.1), z + 0.015, 0, 0, r.uniform(0, 180)))


def streaks(k, x0, x1, H, strength=0.28):
    """Damp streak darkening in vertex colours (world X noise, stronger toward the top)."""
    off = k.noff
    base = k.color_post

    def f(co, c):
        n = mnoise.noise(Vector((co.x * 2.3 + off.x, co.y * 0.3 + off.y, 0.3)))
        s = max(0.0, n) * strength * (0.4 + 0.6 * sstep(0.0, H, co.z))
        k_ = 1.0 - s
        c = (c[0] * k_, c[1] * k_, c[2] * k_)
        return base(co, c) if base else c
    k.color_post = f


def wall_common(k, cuts=(), quoin=None, top=WH, top_profile=None, skip=None, jamb_quoin_z=None, zbreaks=()):
    return masonry(k, -WL / 2, WL / 2, 0, top, WT, cuts=cuts, quoin=quoin, top_profile=top_profile, skip=skip,
                   jamb_quoin_z=jamb_quoin_z, zbreaks=zbreaks)


def drips(k, n, ztop, x0=-1.8, x1=1.8, both=True, M=None, face=WT / 2):
    r = k.r
    for i in range(n):
        side = -1 if (i % 2 == 0 or not both) else 1
        moss_drip(k, r.uniform(x0, x1), ztop - r.uniform(0.0, 0.15), r.uniform(0.35, 1.1), side * face,
                  r.uniform(0.2, 0.45), side, M=M)


@asset("wall_straight", "architecture")
def wall_straight(k):
    wall_common(k)
    drips(k, 4, WH - 0.05)
    moss_top(k, -1.8, 1.8, WH, WT, 2)
    streaks(k, -2, 2, WH)
    k.col_box(WL, WT, WH, T(0, 0, WH / 2))
    return dict(recenter=False, damp=0.3)


@asset("wall_stone_capped", "architecture")
def wall_stone_capped(k):
    wall_common(k, top=WH - 0.22)
    capstones(k, -WL / 2, WL / 2, WH - 0.22, WT, 0.22, over=0.07)
    drips(k, 5, WH - 0.24)
    moss_top(k, -1.8, 1.8, WH, WT + 0.1, 2)
    streaks(k, -2, 2, WH)
    k.col_box(WL, WT + 0.14, WH, T(0, 0, WH / 2))
    return dict(recenter=False, damp=0.3)


@asset("wall_corner", "architecture")
def wall_corner(k):
    # L piece: corner post at origin, arms reach x=+2 and y=+2 (outer faces at x=-0.4 / y=-0.4)
    h = WH - 0.22
    masonry(k, -WT / 2, WL / 2, 0, h, WT, quoin="start")
    M = R(0, 0, 90)
    masonry(k, WT / 2, WL / 2, 0, h, WT, M=M, quoin=None)
    capstones(k, -WT / 2 - 0.07, WL / 2, h, WT, 0.22, over=0.07)
    capstones(k, WT / 2 + 0.07, WL / 2, h, WT, 0.22, over=0.07, M=M)
    drips(k, 3, h - 0.02, 0.2, 1.8)
    drips(k, 3, h - 0.02, 0.8, 1.8, M=M)
    streaks(k, -2, 2, WH)
    k.col_box(WL / 2 + WT / 2, WT, WH, T((WL / 2 - WT / 2) / 2, 0, WH / 2))
    k.col_box(WT, WL / 2 - WT / 2, WH, T(0, (WL / 2 + WT / 2) / 2, WH / 2))
    return dict(recenter=False, damp=0.3)


def door_cuts(w, spring, r_out, gap=0.03):
    return [RectCut(-w / 2, w / 2, -1, spring), CircleCut(0, spring, r_out + gap)]


@asset("wall_doorway", "architecture")
def wall_doorway(k):
    w, spring, r_in, r_out = 1.8, 2.1, 0.9, 1.3
    h = WH - 0.22
    masonry(k, -WL / 2, WL / 2, 0, h, WT, cuts=door_cuts(w, spring, r_out), jamb_quoin_z=spring, zbreaks=(spring,),
            core_cuts=door_cuts(w, spring, r_in + 0.08))
    arch_ring(k, 0, spring, r_in, r_out, WT, n=11, mat="BH_Stone")
    capstones(k, -WL / 2, WL / 2, h, WT, 0.22, over=0.07)
    # threshold + hinge pins
    t = box(w + 0.1, WT + 0.1, 0.08, bev=0.02)
    chip(t, k.r, 2, 0.04)
    k.put(t, "BH_Stone", M=T(0, 0, 0.04), tint=0.9)
    for z in (0.5, 1.7):
        for sx in (-1, 1):
            k.put(cyl(0.025, 0.14, 6), "BH_Iron", M=TRS(sx * (w / 2 + 0.02), -0.25, z, 0, 0, 0))
    drips(k, 4, h - 0.02)
    streaks(k, -2, 2, WH)
    k.col_box(WL / 2 - w / 2, WT, WH, T(-(WL / 2 + w / 2) / 2, 0, WH / 2))
    k.col_box(WL / 2 - w / 2, WT, WH, T((WL / 2 + w / 2) / 2, 0, WH / 2))
    k.col_box(w, WT, WH - spring - r_in * 0.7, T(0, 0, (WH + spring + r_in * 0.7) / 2))
    return dict(recenter=False, damp=0.3)


@asset("wall_window", "architecture")
def wall_window(k):
    w, z0, z1 = 1.0, 1.5, 2.7
    h = WH - 0.22
    cuts = [RectCut(-w / 2, w / 2, z0, z1), RectCut(-0.85, 0.85, z1, z1 + 0.32), RectCut(-0.72, 0.72, z0 - 0.16, z0)]
    wall_common(k, cuts=cuts, top=h, jamb_quoin_z=z1, zbreaks=(z0 - 0.16, z0, z1, z1 + 0.32))
    t = box(1.66, WT + 0.06, 0.3, bev=0.03)
    chip(t, k.r, 2, 0.05)
    k.put(t, "BH_Stone", M=T(0, 0, z1 + 0.16), tint=0.98)
    t = box(1.42, WT + 0.16, 0.14, bev=0.025)
    chip(t, k.r, 2, 0.04)
    k.put(t, "BH_Stone", M=T(0, 0, z0 - 0.08), tint=0.95)
    for i in range(4):
        x = -w / 2 + w * (i + 1) / 5
        k.put(box(0.035, 0.035, z1 - z0 + 0.1), "BH_Iron", M=TRS(x, 0.1, (z0 + z1) / 2, 0, k.r.uniform(-2, 2), 0))
    k.put(box(w + 0.08, 0.03, 0.05), "BH_Iron", M=T(0, 0.1, (z0 + z1) / 2 + 0.2))
    capstones(k, -WL / 2, WL / 2, h, WT, 0.22, over=0.07)
    drips(k, 4, h - 0.02)
    drips(k, 1, z0 - 0.16, -0.5, 0.5, both=False)
    streaks(k, -2, 2, WH)
    k.col_box(WL, WT, z0, T(0, 0, z0 / 2))
    k.col_box(WL, WT, WH - z1, T(0, 0, (WH + z1) / 2))
    k.col_box(WL / 2 - w / 2, WT, z1 - z0, T(-(WL / 2 + w / 2) / 2, 0, (z0 + z1) / 2))
    k.col_box(WL / 2 - w / 2, WT, z1 - z0, T((WL / 2 + w / 2) / 2, 0, (z0 + z1) / 2))
    return dict(recenter=False, damp=0.3)


def fallen_blocks(k, n, area, mat="BH_StoneDark", size=(0.35, 0.8), tint=(0.7, 0.9)):
    """Loose blocks lying on the ground inside area=(x0, x1, y0, y1)."""
    r = k.r
    for _ in range(n):
        L = r.uniform(*size)
        t = box(L, r.uniform(0.3, 0.55), r.uniform(0.25, 0.45), bev=0.03)
        chip(t, r, r.randint(1, 3), 0.08)
        jitter(t, r, 0.01)
        x, y = r.uniform(area[0], area[1]), r.uniform(area[2], area[3])
        k.put(t, mat, M=TRS(x, y, 0.14, r.uniform(-18, 18), r.uniform(-18, 18), r.uniform(0, 180)), tint=r.uniform(*tint))


def rubble_bits(k, n, area, size=(0.08, 0.25), mat="BH_StoneDark"):
    r = k.r
    for i in range(n):
        s = r.uniform(*size)
        t = rock(r, (s, s * r.uniform(0.7, 1.1), s * r.uniform(0.5, 0.8)), cuts=5, subd=1, noise_amp=0.04,
                 seed_off=i * 0.37 + k.seed % 97)
        x, y = r.uniform(area[0], area[1]), r.uniform(area[2], area[3])
        k.put(t, mat, M=TRS(x, y, -0.02, 0, 0, r.uniform(0, 360)), tint=r.uniform(0.7, 0.95))


@asset("wall_broken", "architecture")
def wall_broken(k):
    r = k.r
    xs = [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]
    base = [3.7, 3.5, 3.3, 2.5, 1.7, 1.2, 1.5, 1.1, 1.3]
    zs = [b + r.uniform(-0.2, 0.2) for b in base]

    def prof(x):
        for i in range(len(xs) - 1):
            if xs[i] <= x <= xs[i + 1]:
                return lerp(zs[i], zs[i + 1], (x - xs[i]) / (xs[i + 1] - xs[i]))
        return zs[-1]

    holes = set()

    def skip(ci, xm):
        return ci > 1 and r.random() < 0.05

    masonry(k, -WL / 2, WL / 2, 0, WH, WT, top_profile=prof, skip=skip, chip_rng=(1, 3))
    fallen_blocks(k, 7, (-0.6, 2.2, -1.6, -0.6))
    fallen_blocks(k, 4, (0.0, 2.0, 0.6, 1.4))
    rubble_bits(k, 14, (-0.8, 2.0, -1.5, -0.5))
    drips(k, 3, 3.3, -1.9, -0.8)
    for x0, x1 in ((-2, -1), (-0.5, 0.5), (1, 2)):
        moss_top(k, x0, x1, prof((x0 + x1) / 2) - 0.2, WT, 1)
    streaks(k, -2, 2, WH)
    k.col_box(WL, WT, 1.2, T(0, 0, 0.6))
    k.col_box(2.0, WT, 2.2, T(-1.0, 0, 2.3))
    return dict(recenter=False, damp=0.3)


# ---------------------------------------------------------------------------------------------------------------
def plinth(k, w, z=0.0, tiers=((1.34, 0.18), (1.18, 0.16)), mat="BH_Stone", tint=(0.9, 1.0)):
    r = k.r
    for (s, h) in tiers:
        t = box(s, s, h, bev=0.035)
        chip(t, r, r.randint(1, 3), 0.05)
        jitter(t, r, 0.006)
        k.put(t, mat, M=TRS(0, 0, z + h / 2, 0, 0, r.uniform(-1.2, 1.2)), tint=r.uniform(*tint))
        z += h
    return z


def pillar_shaft(k, z0, z1, W=1.0, quoin=False, top_profile=None, lean=0.0):
    r = k.r
    hs = course_heights(r, z1 - z0, 0.4, 0.5)
    z = z0
    gap = 0.02
    for ci, h in enumerate(hs):
        zb, zt = z + gap / 2, z + h - gap / 2
        z += h
        if top_profile is not None and zb > top_profile:
            break
        if quoin:
            # dark core + four light corner blocks alternating long/short on each face
            k.put(box(W - 0.08, W - 0.08, zt - zb), "BH_StoneDark", M=T(0, 0, (zb + zt) / 2), tint=0.8)
            la, lb = (0.46, 0.3) if ci % 2 == 0 else (0.3, 0.46)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    cx = sx * (W / 2 - la / 2)
                    cy = sy * (W / 2 - lb / 2)
                    t = box(la - gap, lb - gap, zt - zb, bev=0.035)
                    chip(t, r, r.randint(0, 2), 0.05)
                    jitter(t, r, 0.005)
                    k.put(t, "BH_Stone", M=T(cx + sx * 0.012, cy + sy * 0.012, (zb + zt) / 2), tint=r.uniform(0.92, 1.0))
            # middle filler blocks on each face (dark)
            for ax in range(2):
                for s_ in (-1, 1):
                    wlen = W - 2 * (la if ax == 0 else lb) - gap
                    if wlen < 0.08:
                        continue
                    t = box(wlen if ax == 0 else 0.2, 0.2 if ax == 0 else wlen, zt - zb, bev=0.03)
                    chip(t, r, r.randint(0, 1), 0.04)
                    pos = (0, s_ * (W / 2 - 0.1), (zb + zt) / 2) if ax == 0 else (s_ * (W / 2 - 0.1), 0, (zb + zt) / 2)
                    k.put(t, "BH_StoneDark", M=T(*pos), tint=r.uniform(0.72, 0.9))
        else:
            split_x = ci % 2 == 0
            s = r.uniform(0.4, 0.6)
            for part in range(2):
                a = s if part == 0 else 1 - s
                off = (-W / 2 + a * W / 2) if part == 0 else (W / 2 - a * W / 2)
                sx, sy = (a * W - gap, W) if split_x else (W, a * W - gap)
                t = box(sx, sy, zt - zb, bev=0.035)
                chip(t, r, r.randint(0, 2), 0.06)
                jitter(t, r, 0.006)
                pos = (off, 0) if split_x else (0, off)
                k.put(t, "BH_StoneDark", M=TRS(pos[0] + r.uniform(-0.01, 0.01), pos[1] + r.uniform(-0.01, 0.01),
                                                 (zb + zt) / 2, 0, 0, r.uniform(-0.8, 0.8)), tint=r.uniform(0.72, 0.92))
    return z


def capital(k, z, W=1.0):
    r = k.r
    for (s, h) in ((W + 0.12, 0.14), (W + 0.3, 0.2)):
        t = box(s, s, h, bev=0.035)
        chip(t, r, r.randint(1, 2), 0.05)
        k.put(t, "BH_Stone", M=TRS(0, 0, z + h / 2, 0, 0, r.uniform(-1, 1)), tint=r.uniform(0.9, 1.0))
        z += h
    return z


def pillar_moss(k, z_top, W=1.0, n=3):
    r = k.r
    for i in range(n):
        side = r.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])
        M = R(0, 0, {(0, -1): 0, (0, 1): 180, (-1, 0): -90, (1, 0): 90}[side])
        moss_drip(k, r.uniform(-0.3, 0.3), z_top - r.uniform(0, 0.1), r.uniform(0.3, 0.8), -W / 2, 0.3, -1, M=M)


@asset("pillar", "architecture")
def pillar(k):
    z = plinth(k, 1.0)
    z = pillar_shaft(k, z, WH - 0.34)
    capital(k, WH - 0.34)
    pillar_moss(k, WH - 0.36)
    streaks(k, -1, 1, WH)
    k.col_box(1.3, 1.3, WH, T(0, 0, WH / 2))
    return dict(recenter=False, damp=0.3)


@asset("pillar_quoin", "architecture")
def pillar_quoin(k):
    z = plinth(k, 1.0)
    pillar_shaft(k, z, WH - 0.34, quoin=True)
    capital(k, WH - 0.34)
    pillar_moss(k, WH - 0.36)
    streaks(k, -1, 1, WH)
    k.col_box(1.3, 1.3, WH, T(0, 0, WH / 2))
    return dict(recenter=False, damp=0.3)


@asset("pillar_broken", "architecture")
def pillar_broken(k):
    r = k.r
    z = plinth(k, 1.0)
    z = pillar_shaft(k, z, 2.35)
    # half block + heavily chipped cap stump
    t = box(0.55, 1.0, 0.42, bev=0.03)
    chip(t, r, 4, 0.14)
    k.put(t, "BH_StoneDark", M=TRS(-0.22, 0, z + 0.21, 0, 3, 2), tint=0.8)
    # fallen shaft courses & capital
    for i, (x, y, rz) in enumerate(((1.3, -0.6, 20), (2.1, -0.3, 35), (2.9, 0.1, 50))):
        t = box(0.98, 0.98, 0.44, bev=0.035)
        chip(t, r, 3, 0.1)
        jitter(t, r, 0.01)
        k.put(t, "BH_StoneDark", M=TRS(x, y, 0.49, 90, r.uniform(-8, 8), rz), tint=r.uniform(0.72, 0.88))
    t = box(1.3, 1.3, 0.34, bev=0.035)
    chip(t, r, 3, 0.1)
    k.put(t, "BH_Stone", M=TRS(-1.4, 1.1, 0.3, 14, 6, 25), tint=0.95)
    rubble_bits(k, 12, (-1.2, 2.8, -1.3, 1.2), (0.08, 0.22))
    pillar_moss(k, z, n=2)
    k.col_box(1.3, 1.3, 2.8, T(0, 0, 1.4))
    k.col_box(2.4, 1.2, 1.0, TRS(2.1, -0.25, 0.5, 0, 0, 35))
    return dict(recenter=False, damp=0.3)


# ---------------------------------------------------------------------------------------------------------------
def archway(k, alt):
    w, spring, r_in, r_out = 2.4, 2.0, 1.2, 1.6
    h = WH - 0.22
    cuts = [RectCut(-w / 2, w / 2, -1, spring), CircleCut(0, spring, r_out + 0.03)]
    masonry(k, -WL / 2, WL / 2, 0, h, WT, cuts=cuts, quoin="both" if alt else None,
            jamb_quoin_z=spring if alt else None, zbreaks=(spring,), core_cuts=door_cuts(w, spring, r_in + 0.08))
    arch_ring(k, 0, spring, r_in, r_out, WT, n=13, mat="BH_Stone" if alt else "BH_StoneDark",
              alt_mat="BH_StoneDark" if alt else None, tint=(0.9, 1.0) if alt else (0.75, 0.9), proud=0.04)
    # keystone accent + impost blocks
    for sx in (-1, 1):
        t = box(0.5, WT + 0.14, 0.18, bev=0.03)
        chip(t, k.r, 1, 0.04)
        k.put(t, "BH_Stone", M=T(sx * (w / 2 + 0.2), 0, spring - 0.09), tint=0.95)
    capstones(k, -WL / 2, WL / 2, h, WT, 0.22, over=0.07)
    drips(k, 5, h - 0.02)
    streaks(k, -2, 2, WH)
    k.col_box(WL / 2 - w / 2, WT, WH, T(-(WL / 2 + w / 2) / 2, 0, WH / 2))
    k.col_box(WL / 2 - w / 2, WT, WH, T((WL / 2 + w / 2) / 2, 0, WH / 2))
    k.col_box(w, WT, WH - spring - r_in * 0.75, T(0, 0, (WH + spring + r_in * 0.75) / 2))


@asset("arch", "architecture")
def arch(k):
    archway(k, False)
    return dict(recenter=False, damp=0.3)


@asset("arch_quoin", "architecture")
def arch_quoin(k):
    archway(k, True)
    return dict(recenter=False, damp=0.3)


# ---------------------------------------------------------------------------------------------------------------
@asset("floor_tile_4m", "architecture")
def floor_tile_4m(k):
    k.put(box(3.96, 3.96, 0.21, bev=0.02), "BH_StoneDark", M=T(0, 0, 0.105), tint=0.4)
    slab_floor(k, 4.0, 4.0, 0.3, th=0.1, crack_p=0.15)
    k.col_box(4, 4, 0.3, T(0, 0, 0.15))
    return dict(recenter=False)


@asset("stairs", "architecture")
def stairs(k):
    r = k.r
    n, rise, run, W = 10, 0.2, 0.4, 3.2
    # stepped core under the treads (run along +Y)
    outline = [(-2 + run, 0.0), (2.0, 0.0), (2.0, (n - 1) * rise)]
    for i in range(n - 1, 0, -1):
        outline.append((-2 + run * i, i * rise))
        outline.append((-2 + run * i, (i - 1) * rise)) if i > 1 else None
    outline = [p for p in outline if p is not None]
    t = prism(outline[::-1], W - 0.04)
    k.put(t, "BH_StoneDark", M=R(0, 0, 90) @ T(0, 0, 0), tint=0.35)
    for i in range(n):
        y0 = -2 + run * i
        ws, _ = split_lengths(r, W, 0.7, 1.3)
        x = -W / 2
        for w in ws:
            t = box(w - 0.02, run + 0.06, rise - 0.015, bev=0.03)
            chip(t, r, r.randint(1, 2), 0.05)
            jitter(t, r, 0.005)
            # worn front edge: sink the middle a hair
            k.put(t, "BH_Stone", M=TRS(x + w / 2, y0 + run / 2 + 0.02, rise * i + rise / 2, r.uniform(-0.6, 0.6),
                                        r.uniform(-0.5, 0.5), r.uniform(-0.5, 0.5)), tint=r.uniform(0.85, 1.0))
            x += w
    # stepped cheek walls
    for sx in (-1, 1):
        M = T(sx * (W / 2 + 0.2), 0, 0) @ R(0, 0, 90)

        def prof(x):
            return 2.0 * (x + 2.0) / 4.0 + 0.55

        masonry(k, -2.0, 2.0, 0, 2.6, 0.4, M=M, top_profile=prof, course=(0.3, 0.42), blen=(0.4, 0.8))
    k.col_mesh(box(W, math.hypot(4, 2), 0.2), TRS(0, 0, 1.0 - 0.1, math.degrees(math.atan2(2, 4)), 0, 0))
    k.col_box(0.4, 4, 2.6, T(-(W / 2 + 0.2), 0, 1.3))
    k.col_box(0.4, 4, 2.6, T(W / 2 + 0.2, 0, 1.3))
    return dict(recenter=False, damp=0.25)


@asset("ceiling_beam", "architecture")
def ceiling_beam(k):
    r = k.r
    L = 4.0
    t = box(L, 0.3, 0.4, bev=0.03)
    bmesh.ops.subdivide_edges(t, edges=[e for e in t.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > 1.0], cuts=7)
    for v in t.verts:
        v.co.z -= 0.04 * math.cos(v.co.x / L * math.pi)  # slight sag
    jitter(t, r, 0.008)
    k.put(t, "BH_WoodDark", M=T(0, 0, 0.2), tint=0.9, uvoff=False)
    # adze scars / cracks
    for i in range(5):
        c = box(r.uniform(0.3, 0.9), 0.02, 0.02)
        k.put(c, "BH_WoodDark", M=TRS(r.uniform(-1.6, 1.6), -0.152, r.uniform(0.1, 0.3), r.uniform(-5, 5), 0, 0), tint=0.4)
    for x in (-1.5, 0.0, 1.5):
        k.put(box(0.07, 0.34, 0.44, bev=0.01), "BH_Iron", M=T(x, 0, 0.2))
        for sy in (-1, 1):
            for z in (0.08, 0.32):
                k.put(cyl(0.018, 0.02, 6), "BH_Iron", M=TRS(x, sy * 0.175, z, 90, 0, 0))
    for sx in (-1, 1):
        k.put(box(0.3, 0.4, 0.06, bev=0.01), "BH_Iron", M=T(sx * (L / 2 - 0.15), 0, 0.43))
    k.col_box(L, 0.3, 0.4, T(0, 0, 0.2))
    return dict(recenter=False)


@asset("gate_iron", "architecture")
def gate_iron(k):
    W, H = 1.8, 2.7
    k.put(box(0.08, 0.08, H), "BH_Iron", M=T(-W / 2 + 0.04, 0, H / 2))
    k.put(box(0.08, 0.08, H), "BH_Iron", M=T(W / 2 - 0.04, 0, H / 2))
    for z in (0.12, 1.2, H - 0.3):
        k.put(box(W, 0.07, 0.07, bev=0.005), "BH_Iron", M=T(0, 0, z))
    nb = 7
    for i in range(nb):
        x = -W / 2 + W * (i + 1) / (nb + 1)
        k.put(box(0.035, 0.035, H - 0.1), "BH_Iron", M=TRS(x, 0, (H - 0.1) / 2 + 0.05, 0, 0, 45))
        k.put(cyl(0.05, 0.16, 4, r2=0.0), "BH_Iron", M=TRS(x, 0, H - 0.06, 0, 0, 45))
        for z in (0.12, 1.2, H - 0.3):
            k.put(box(0.05, 0.09, 0.05), "BH_Iron", M=T(x, 0, z))
    # diagonal brace
    d = math.hypot(W - 0.16, 1.08)
    k.put(box(d, 0.05, 0.05), "BH_Iron", M=TRS(0, 0.02, 0.66, 0, -math.degrees(math.atan2(1.08, W - 0.16)), 0))
    for z in (0.3, H - 0.5):
        k.put(cyl(0.06, 0.2, 8), "BH_Iron", M=T(-W / 2 - 0.02, 0, z - 0.1))
    k.put(torus(0.08, 0.012, 12, 5), "BH_Iron", M=TRS(W / 2 - 0.2, -0.07, 1.05, 90, 0, 0))
    k.col_box(W, 0.1, H, T(0, 0, H / 2))
    return dict(recenter=False)


@asset("wall_low", "architecture")
def wall_low(k):
    """Cutaway wall for camera-facing sides of interiors: 4 m long, 1.3 m tall, capped, same thickness/grid as walls."""
    h = 1.3
    wall_common(k, top=h - 0.2)
    capstones(k, -WL / 2, WL / 2, h - 0.2, WT, 0.2, over=0.07)
    moss_top(k, -1.8, 1.8, h, WT + 0.1, 2)
    streaks(k, -2, 2, h)
    k.col_box(WL, WT + 0.14, h, T(0, 0, h / 2))
    return dict(recenter=False, damp=0.3, damp_h=0.6)


@asset("wall_low_broken", "architecture")
def wall_low_broken(k):
    """Cutaway wall variant with a crumbled top and fallen blocks in front (toward -Y)."""
    r = k.r

    def prof(x):
        return 1.15 + 0.35 * math.sin(x * 1.7 + 0.6) - (0.45 if -0.6 < x < 0.9 else 0.0)
    wall_common(k, top=1.6, top_profile=prof)
    fallen_blocks(k, 5, (-1.6, 1.6, -1.4, -0.5))
    rubble_bits(k, 14, (-1.8, 1.8, -1.2, -0.45))
    streaks(k, -2, 2, 1.5)
    k.col_box(WL, WT, 1.2, T(0, 0, 0.6))
    return dict(recenter=False, damp=0.3, damp_h=0.6)
