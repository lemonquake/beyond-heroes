"""Town pieces for the Hero Sanctuary and the fallen village: timber-framed houses (intact / destroyed), market stall,
well, fountain, fences."""
import math

import bmesh
from mathutils import Vector

from kit import *  # noqa
from masonry import *  # noqa
from registry import asset
from assets_props import plank, rivet, hay, flame_tip


def gable_roof(k, L, W, z, pitch_h, over=0.4, mat="BH_Thatch", missing=None, burnt=False):
    """Thatch gable roof along X. missing(x, side)->bool removes roof sections (collapsed roofs)."""
    r = k.r
    half = W / 2 + over
    slope = math.hypot(half, pitch_h)
    ang = math.degrees(math.atan2(pitch_h, half))
    nseg = max(2, int(L / 1.0))
    for sy in (-1, 1):
        for i in range(nseg):
            x = -L / 2 - over + (L + 2 * over) * (i + 0.5) / nseg
            if missing and missing(x, sy):
                continue
            t = box((L + 2 * over) / nseg + 0.02, slope, 0.35, bev=0.08)
            subdiv(t, 1)
            ndisp(t, 2.5, 0.04, k.noff + Vector((i, sy, 0)))
            jitter(t, r, 0.02)
            k.put(t, mat, M=T(x, sy * half / 2, z + pitch_h / 2) @ R(-sy * ang, 0, 0),
                  tint=r.uniform(0.35, 0.5) if burnt else r.uniform(0.8, 1.0), smooth=40)
    # ridge
    if not (missing and missing(0.0, 0)):
        k.put(cyl(0.2, L + 2 * over, 8), mat, M=TRS(-(L + 2 * over) / 2, 0, z + pitch_h + 0.05, 0, 90, 0), tint=0.7, smooth=40)


def timber_frame(k, L, W, z0, h, burnt=False, skip=None):
    """Plaster panels with dark timber posts/beams/braces on a box footprint L x W (walls centred on the footprint)."""
    r = k.r
    wood = "BH_WoodDark"
    tint_w = (0.25, 0.4) if burnt else (0.6, 0.85)
    for side, (ax, length, off) in enumerate(((0, L, W / 2), (0, L, -W / 2), (1, W, L / 2), (1, W, -L / 2))):
        M = T(0, off, 0) if ax == 0 else T(off, 0, 0) @ R(0, 0, 90)
        # plaster infill
        t = box(length - 0.1, 0.18, h, bev=0.02)
        k.put(t, "BH_Stone", M=M @ T(0, 0, z0 + h / 2), tint=0.25 if burnt else r.uniform(1.15, 1.3))
        n = max(2, int(length / 1.3))
        for i in range(n + 1):
            x = -length / 2 + length * i / n
            k.put(box(0.2, 0.26, h, bev=0.02), wood, M=M @ T(x, 0, z0 + h / 2), tint=r.uniform(*tint_w))
            if i < n and (i % 2 == 0):
                seg = length / n
                d = math.hypot(seg, h)
                k.put(box(d - 0.1, 0.22, 0.14, bev=0.01), wood,
                      M=M @ TRS(x + seg / 2, 0, z0 + h / 2, 0, -math.degrees(math.atan2(h, seg)) * (1 if i % 4 == 0 else -1), 0),
                      tint=r.uniform(*tint_w))
        for z in (z0 + 0.1, z0 + h - 0.1):
            k.put(box(length + 0.2, 0.28, 0.2, bev=0.02), wood, M=M @ T(0, 0, z), tint=r.uniform(*tint_w))


def window(k, M, lit=True):
    k.put(box(0.9, 0.3, 1.0, bev=0.02), "BH_WoodDark", M=M, tint=0.6)
    k.put(box(0.7, 0.32, 0.8), "BH_Candle" if lit else "BH_StoneDark", M=M, tint=1.0 if lit else 0.05)
    k.put(box(0.05, 0.34, 0.8), "BH_WoodDark", M=M, tint=0.5)
    k.put(box(0.7, 0.34, 0.05), "BH_WoodDark", M=M, tint=0.5)
    for sx in (-1, 1):  # open shutters
        k.put(box(0.4, 0.05, 0.9, bev=0.01), "BH_Wood", M=M @ TRS(sx * 0.68, -0.2, 0, 0, 0, sx * 20), tint=0.6)


def door(k, M, open_=False):
    k.put(box(1.3, 0.3, 2.3, bev=0.03), "BH_WoodDark", M=M @ T(0, 0, 1.15), tint=0.5)
    k.put(box(1.0, 0.32, 2.05), "BH_StoneDark", M=M @ T(0, 0, 1.03), tint=0.02)
    rot = TRS(-0.5, -0.2, 0, 0, 0, -70) @ T(0.5, 0, 0) if open_ else T(0, -0.05, 0)
    for i in range(4):
        plank(k, 0.25, 0.06, 2.0, M @ rot @ T(-0.375 + i * 0.25, 0, 1.01), tint=(0.55, 0.75))
    for z in (0.4, 1.6):
        k.put(box(0.95, 0.07, 0.08), "BH_Iron", M=M @ rot @ T(0, -0.04, z))
    k.put(torus(0.06, 0.012, 10, 4), "BH_Iron", M=M @ rot @ TRS(0.3, -0.08, 1.0, 90, 0, 0))


@asset("house_intact", "town")
def house_intact(k):
    """Two storeys: stone ground floor, timber-framed upper floor, thatch roof, brick chimney. Door faces -Y."""
    r = k.r
    L, W = 7.0, 5.0
    h0, h1 = 3.0, 2.6
    for (sx, sy, rot, length) in ((0, -1, 0, L), (0, 1, 0, L), (-1, 0, 90, W), (1, 0, 90, W)):
        M = T(sx * L / 2, sy * W / 2, 0) @ R(0, 0, rot)
        cuts = ()
        if sy == -1:
            cuts = (RectCut(-0.65, 0.65, 0.0, 2.3), RectCut(1.6, 2.5, 1.0, 2.0), RectCut(-2.5, -1.6, 1.0, 2.0))
        elif sx == 1:
            cuts = (RectCut(-0.45, 0.45, 1.0, 2.0),)
        masonry(k, -length / 2 - 0.35, length / 2 + 0.35, 0, h0, 0.7, M=M, cuts=cuts, quoin="both", course=(0.35, 0.5))
    door(k, T(0, -W / 2 - 0.2, 0))
    for x in (-2.05, 2.05):
        window(k, T(x, -W / 2 - 0.1, 1.5))
    window(k, T(L / 2 + 0.1, 0, 1.5) @ R(0, 0, 90))
    k.put(box(L + 0.8, W + 0.8, 0.25, bev=0.03), "BH_WoodDark", M=T(0, 0, h0 + 0.12), tint=0.6)
    timber_frame(k, L + 0.4, W + 0.4, h0 + 0.25, h1)
    for x in (-2.0, 2.0):
        window(k, T(x, -(W + 0.4) / 2 - 0.12, h0 + 1.4))
    # gable ends (plaster triangles)
    ph = 2.6
    for sx in (-1, 1):
        t = prism([(-(W + 0.4) / 2, 0), ((W + 0.4) / 2, 0), (0, ph)], 0.2)
        k.put(t, "BH_Stone", M=T(sx * (L + 0.4) / 2, 0, h0 + 0.25 + h1) @ R(0, 0, 90), tint=1.2)
        k.put(box(0.2, 0.26, ph * 0.8), "BH_WoodDark", M=T(sx * (L + 0.5) / 2, 0, h0 + 0.25 + h1 + ph * 0.4), tint=0.6)
    gable_roof(k, L + 0.4, W + 0.4, h0 + 0.25 + h1 - 0.1, ph, over=0.5)
    # chimney
    masonry(k, -0.5, 0.5, 0, h0 + h1 + ph + 1.2, 0.9, mat="BH_Brick", M=T(-L / 2 + 1.2, W / 4, 0) @ R(0, 0, 0),
            tint=(0.6, 0.85), course=(0.25, 0.3), blen=(0.3, 0.45), core_mat="BH_Brick")
    k.put(box(1.2, 1.1, 0.2, bev=0.03), "BH_Stone", M=T(-L / 2 + 1.2, W / 4, h0 + h1 + ph + 1.3), tint=0.8)
    # porch details
    k.put(box(1.8, 1.0, 0.15, bev=0.03), "BH_Stone", M=T(0, -W / 2 - 0.8, 0.075), tint=0.8)
    for x in (-0.95, 0.95):
        k.put(box(0.14, 0.14, 2.5), "BH_WoodDark", M=T(x, -W / 2 - 1.1, 1.25), tint=0.6)
    k.put(box(2.4, 1.4, 0.12), "BH_Thatch", M=TRS(0, -W / 2 - 0.9, 2.6, -18, 0, 0), tint=0.8)
    k.sockets.append(("door_light", (0, -W / 2 - 0.9, 2.2)))
    k.col_box(L + 0.7, W + 0.7, h0 + h1, T(0, 0, (h0 + h1) / 2))
    return dict(recenter=False, damp=0.35, damp_h=1.2)


@asset("house_destroyed", "town")
def house_destroyed(k):
    """Burnt-out house: broken stone walls, collapsed charred roof beams, rubble. Door gap faces -Y."""
    r = k.r
    L, W, h0 = 7.0, 5.0, 3.0
    profs = {
        (0, -1): lambda x: 2.2 + 0.9 * math.sin(x * 0.9) - (1.4 if x > 1.5 else 0.0),
        (0, 1): lambda x: 3.0 + 0.4 * math.sin(x * 1.7),
        (-1, 0): lambda x: 3.0 + 0.8 * math.cos(x * 1.1),
        (1, 0): lambda x: 1.1 + 0.6 * math.sin(x * 2.3),
    }
    for (sx, sy, rot, length) in ((0, -1, 0, L), (0, 1, 0, L), (-1, 0, 90, W), (1, 0, 90, W)):
        M = T(sx * L / 2, sy * W / 2, 0) @ R(0, 0, rot)
        cuts = (RectCut(-0.65, 0.65, 0.0, 2.3), RectCut(-2.5, -1.6, 1.0, 2.0)) if sy == -1 else ()
        masonry(k, -length / 2 - 0.35, length / 2 + 0.35, 0, h0, 0.7, M=M, cuts=cuts, quoin="both",
                top_profile=profs[(sx, sy)], course=(0.35, 0.5))
    # soot on the upper stones is handled by tint via colour post
    k.color_post = lambda co, c: tuple(ch * (1.0 - 0.55 * sstep(1.2, 3.0, co.z)) for ch in c)
    for i in range(7):  # fallen charred beams
        a = r.uniform(-40, 40)
        k.put(box(r.uniform(3.0, 5.5), 0.22, 0.22, bev=0.03), "BH_WoodDark",
              M=TRS(r.uniform(-2, 2), r.uniform(-1.6, 1.6), r.uniform(0.3, 1.8), 0, r.uniform(-25, 25), a), tint=0.18)
    for i in range(3):  # rafters still leaning from the back wall
        k.put(box(0.18, 3.6, 0.18, bev=0.02), "BH_WoodDark", M=TRS(-2.2 + i * 1.6, 0.6, 2.2, 35, 0, r.uniform(-5, 5)), tint=0.2)
    t = box(3.0, 2.2, 0.3, bev=0.1)
    subdiv(t, 2)
    ndisp(t, 2.0, 0.12, k.noff)
    k.put(t, "BH_Thatch", M=TRS(0.8, 0.5, 0.25, 4, 3, 10), tint=0.3, smooth=40)
    for i in range(20):
        a = r.uniform(0, math.tau)
        d = r.uniform(0.5, 3.0)
        s = r.uniform(0.2, 0.5)
        t = rock(r, (s, s * 0.8, s * 0.6), cuts=5, subd=1, seed_off=i)
        k.put(t, "BH_StoneDark", M=TRS(math.cos(a) * d * 1.3, math.sin(a) * d, 0, 0, 0, r.uniform(0, 360)), tint=r.uniform(0.5, 0.8))
    k.put(box(L, W, 0.06), "BH_Dirt", M=T(0, 0, 0.03), tint=0.25)
    # collision: wall stubs
    for (sx, sy, rot, length) in ((0, -1, 0, L), (0, 1, 0, L), (-1, 0, 90, W), (1, 0, 90, W)):
        M = T(sx * L / 2, sy * W / 2, 0) @ R(0, 0, rot)
        if sy == -1:
            k.col_box(length / 2 - 0.3, 0.7, 2.0, M @ T(-length / 4 - 0.5, 0, 1.0))
            k.col_box(length / 2 - 0.3, 0.7, 2.0, M @ T(length / 4 + 0.5, 0, 1.0))
        else:
            k.col_box(length + 0.7, 0.7, 2.0, M @ T(0, 0, 1.0))
    return dict(recenter=False, damp=0.3)


@asset("market_stall", "town")
def market_stall(k):
    r = k.r
    L, W = 3.0, 1.8
    for sx in (-1, 1):
        for sy in (-1, 1):
            h = 2.6 if sy > 0 else 2.2
            k.put(box(0.12, 0.12, h, bev=0.015), "BH_WoodDark", M=T(sx * (L / 2 - 0.06), sy * (W / 2 - 0.06), h / 2), tint=0.7)
    for i in range(4):
        plank(k, L - 0.1, 0.22, 0.05, T(0, -W / 2 + 0.2 + i * 0.23, 0.95))
    plank(k, L - 0.1, 0.04, 0.9, T(0, -W / 2 + 0.08, 0.5), mat="BH_Wood")
    slope = math.hypot(W + 0.6, 0.45)
    ang = math.degrees(math.atan2(0.45, W + 0.6))
    n = 8
    for i in range(n):
        x = -L / 2 - 0.2 + (L + 0.4) * (i + 0.5) / n
        t = box((L + 0.4) / n, slope, 0.02)
        subdiv(t, 2)
        for v in t.verts:
            v.co.z -= 0.05 * math.sin((v.co.y / slope + 0.5) * math.pi)
        k.put(t, "BH_ClothRed" if i % 2 else "BH_Cloth", M=TRS(x, 0, 2.45, ang, 0, 0), tint=0.8, smooth=40)
    for i in range(n):  # scalloped valance
        x = -L / 2 - 0.2 + (L + 0.4) * (i + 0.5) / n
        k.put(cyl(0.19, 0.02, 8, bev=0.0), "BH_ClothRed" if i % 2 else "BH_Cloth", M=TRS(x, -W / 2 - 0.3, 2.2, 90, 0, 0), tint=0.8)
    # goods: baskets of produce, cloth rolls, a crate
    for i, x in enumerate((-1.0, -0.3, 0.4)):
        b = lathe([(0.15, 0.0), (0.22, 0.14), (0.2, 0.14), (0.13, 0.02), (0.0, 0.02)], 10, cap_top=False)
        k.put(b, "BH_Thatch", M=T(x, -0.3, 0.98), tint=0.7)
        for j in range(7):
            k.put(ico(0.05, 1), ("BH_ClothRed", "BH_Gold", "BH_Moss")[i],
                  M=T(x + r.uniform(-0.1, 0.1), -0.3 + r.uniform(-0.1, 0.1), 1.1), tint=r.uniform(0.6, 0.9))
    for i in range(3):
        k.put(cyl(0.08, 0.7, 8), ("BH_Cloth", "BH_ClothRed", "BH_Cloth")[i], M=TRS(1.0, -0.5 + i * 0.17, 1.06, 0, 90, 0) @ T(0, 0, -0.35),
              tint=r.uniform(0.6, 0.9))
    k.put(box(0.6, 0.6, 0.6, bev=0.03), "BH_Wood", M=TRS(L / 2 + 0.3, 0.3, 0.3, 0, 0, 12), tint=0.7)
    k.sockets.append(("light", (0, -W / 2 - 0.4, 2.1)))
    k.col_box(L, W, 1.0, T(0, 0, 0.5))
    return dict(recenter=False)


@asset("well", "town")
def well(k):
    r = k.r
    Rr = 1.0
    n = 12
    for c in range(4):
        z0 = c * 0.24
        for i in range(n):
            a0 = math.tau * (i + (0.5 if c % 2 else 0)) / n + 0.01
            a1 = math.tau * (i + 1 + (0.5 if c % 2 else 0)) / n - 0.01
            c8 = [(math.cos(a0) * (Rr - 0.3), math.sin(a0) * (Rr - 0.3), z0), (math.cos(a0) * Rr, math.sin(a0) * Rr, z0),
                  (math.cos(a1) * Rr, math.sin(a1) * Rr, z0), (math.cos(a1) * (Rr - 0.3), math.sin(a1) * (Rr - 0.3), z0)]
            c8 = c8 + [(x, y, z0 + 0.22) for (x, y, _) in c8]
            t = hexa(c8, 0.025)
            chip(t, r, r.randint(0, 1), 0.04)
            k.put(t, "BH_Stone", tint=r.uniform(0.7, 0.95))
    k.put(cyl(Rr - 0.3, 0.02, 16), "BH_Water", M=T(0, 0, 0.3), uvoff=False)
    k.put(cyl(Rr - 0.3, 0.3, 16), "BH_StoneDark", tint=0.05)
    for sx in (-1, 1):
        k.put(box(0.14, 0.14, 2.4), "BH_WoodDark", M=T(sx * (Rr + 0.05), 0, 1.2), tint=0.7)
    k.put(cyl(0.1, 2.3, 10), "BH_Wood", M=TRS(-1.15, 0, 1.6, 0, 90, 0), tint=0.7)
    for i in range(6):
        k.put(torus(0.11, 0.012, 10, 4), "BH_Cloth", M=TRS(-0.15 + i * 0.03, 0, 1.6, 0, 90, 0), tint=0.5)
    k.put(cyl(0.01, 1.0, 4), "BH_Cloth", M=T(0, 0, 0.6), tint=0.5)
    k.put(box(0.05, 0.3, 0.05), "BH_Iron", M=T(Rr + 0.15, 0, 1.6))
    for sy in (-1, 1):
        t = box(2.8, 0.9, 0.1, bev=0.03)
        k.put(t, "BH_Thatch", M=TRS(0, sy * 0.4, 2.55, -sy * 32, 0, 0), tint=0.8)
    k.put(box(0.12, 0.12, 2.8), "BH_WoodDark", M=TRS(-1.4, 0, 2.7, 0, 90, 0), tint=0.6)
    b = lathe([(0.14, 0.0), (0.17, 0.3), (0.15, 0.3), (0.12, 0.03), (0.0, 0.03)], 10, cap_bot=True, cap_top=False)
    k.put(b, "BH_Wood", M=T(Rr + 0.3, -0.4, 0), tint=0.6)
    k.col_mesh(cyl(Rr, 1.0, 10))
    return dict(recenter=False)


@asset("fountain", "town")
def fountain(k):
    r = k.r
    basin = lathe([(3.0, 0.0), (3.1, 0.1), (3.1, 0.6), (2.95, 0.7), (2.75, 0.7), (2.7, 0.2), (0.0, 0.2)], 32,
                  cap_top=False, uv_tile=2.0)
    k.put(basin, "BH_Stone", tint=0.85, smooth=30, uv="keep")
    k.put(cyl(2.72, 0.02, 32), "BH_Water", M=T(0, 0, 0.5), uvoff=False)
    k.put(lathe([(0.5, 0.0), (0.45, 0.3), (0.3, 0.5), (0.28, 1.4), (0.35, 1.6)], 16), "BH_Stone", M=T(0, 0, 0.2), tint=0.9,
          smooth=30)
    bowl = lathe([(0.3, 0.0), (1.3, 0.35), (1.35, 0.5), (1.2, 0.5), (0.2, 0.2), (0.0, 0.2)], 24, cap_top=False)
    k.put(bowl, "BH_Stone", M=T(0, 0, 1.75), tint=0.95, smooth=30)
    k.put(cyl(1.18, 0.02, 24), "BH_Water", M=T(0, 0, 2.18), uvoff=False)
    # a small robed figure holding a sun disc on top (the sanctuary's patron)
    k.put(lathe([(0.3, 0.0), (0.25, 0.6), (0.2, 1.1), (0.24, 1.3), (0.1, 1.45), (0.0, 1.5)], 12), "BH_Stone", M=T(0, 0, 2.2),
          tint=1.0, smooth=35)
    k.put(ico(0.13, 2), "BH_Stone", M=T(0, 0, 3.8), tint=1.0, smooth=45)
    for sx in (-1, 1):
        k.put(tube([(sx * 0.2, 0, 3.45), (sx * 0.35, -0.1, 3.8), (sx * 0.12, -0.15, 4.15)], 0.06, 6), "BH_Stone", tint=0.95,
              smooth=35)
    k.put(cyl(0.35, 0.05, 20), "BH_Gold", M=TRS(0, -0.17, 4.35, 90, 0, 0), tint=0.9)
    k.put(torus(0.35, 0.03, 20, 4), "BH_Gold", M=TRS(0, -0.17, 4.35, 90, 0, 0), tint=0.7)
    for i in range(4):  # water spouts (thin falling streams)
        a = math.tau * i / 4 + math.pi / 4
        p0 = (math.cos(a) * 1.3, math.sin(a) * 1.3, 2.2)
        p1 = (math.cos(a) * 1.7, math.sin(a) * 1.7, 0.55)
        k.put(tube([p0, ((p0[0] + p1[0]) / 2 * 1.05, (p0[1] + p1[1]) / 2 * 1.05, 1.6), p1], 0.04, 5), "BH_Water", uvoff=False)
    k.sockets.append(("light", (0, 0, 4.6)))
    k.col_mesh(cyl(3.1, 0.7, 16))
    k.col_mesh(cyl(1.35, 2.3, 10))
    return dict(recenter=False)


@asset("palisade_fence", "town")
def palisade_fence(k):
    """4 m section of sharpened logs along X, ~3 m tall."""
    r = k.r
    n = 13
    for i in range(n):
        x = -2 + 4 * (i + 0.5) / n
        h = r.uniform(2.7, 3.2)
        rr = r.uniform(0.13, 0.16)
        t = tube([(0, 0, -0.2), (0, 0, h)], [rr, rr * 0.95], 7)
        k.put(t, "BH_Bark", M=TRS(x, r.uniform(-0.03, 0.03), 0, r.uniform(-2, 2), r.uniform(-2, 2), r.uniform(0, 60)), tint=0.75,
              smooth=40)
        k.put(cyl(rr * 0.95, 0.4, 7, r2=0.0), "BH_Wood", M=T(x, 0, h), tint=0.8)
    for z in (0.7, 2.1):
        k.put(box(4.0, 0.12, 0.14, bev=0.02), "BH_WoodDark", M=T(0, 0.17, z), tint=0.6)
        for i in range(4):
            k.put(torus(0.16, 0.015, 8, 3), "BH_Cloth", M=TRS(-1.5 + i, 0.08, z, 0, 90, 0), tint=0.4)
    k.col_box(4.0, 0.4, 3.0, T(0, 0, 1.5))
    return dict(recenter=False)


@asset("wood_fence", "town")
def wood_fence(k):
    """4 m split-rail fence along X, 1.1 m tall."""
    r = k.r
    for x in (-2.0, 0.0, 2.0):
        k.put(box(0.12, 0.12, 1.2, bev=0.015), "BH_WoodDark", M=TRS(x, 0, 0.55, r.uniform(-3, 3), r.uniform(-3, 3), 0), tint=0.7)
    for z in (0.45, 0.9):
        plank(k, 4.1, 0.08, 0.1, T(0, 0.08, z), mat="BH_Wood", warp=0.02)
    k.col_box(4.0, 0.25, 1.1, T(0, 0, 0.55))
    return dict(recenter=False)
