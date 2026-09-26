"""Malasugue town buildings (run bh-003): the Salted Marlin tavern, Swordfin Hall, Lantern House and a copy of
house_intact with a `door` socket. Same style as assets_town.house_intact: stone ground floor, timber upper floor.

All exteriors: front (door) faces -Y, origin at the bottom centre of the footprint (recenter=False), `door` socket =
ground-level point just outside the door centre (outside the collision box), `door_light` above/in front of the door.
Also holds the shared emblem / lantern / barrel helpers used by assets_interior.py.
"""
import math
import random

import bmesh
from mathutils import Vector, noise as mnoise

import kit
from kit import *  # noqa
from masonry import *  # noqa
from registry import asset
from assets_props import plank, rivet, flame_tip
from assets_town import gable_roof, timber_frame, window, door
import assets_town

# Extra BH_* names from the ENV table in game/src/world/material_library.gd (bh-003). kit.get_mat asserts that the name
# is known, so register export colours (linear) here; the game swaps materials by name.
EXTRA_MATERIALS = {
    "BH_ClothBlue": ((0.025, 0.06, 0.22, 1), 0.92, 0.0, None),
    "BH_ClothViolet": ((0.075, 0.03, 0.15, 1), 0.92, 0.0, None),
    "BH_Silver": ((0.62, 0.64, 0.68, 1), 0.3, 1.0, None),
    "BH_Plaster": ((0.58, 0.5, 0.38, 1), 0.95, 0.0, None),
    "BH_Bottle": ((0.03, 0.16, 0.05, 1), 0.08, 0.0, None),
    "BH_Paper": ((0.7, 0.6, 0.42, 1), 0.9, 0.0, None),
    "BH_Rope": ((0.3, 0.2, 0.09, 1), 0.95, 0.0, None),
}
for _n, _v in EXTRA_MATERIALS.items():
    kit.MATERIALS.setdefault(_n, _v)
    if _n not in kit.MATERIAL_NAMES:
        kit.MATERIAL_NAMES.append(_n)


# ---------------------------------------------------------------------------------------------------------------
# shared helpers
def swordfish(k, M, L=1.0, depth=0.06, mat="BH_Silver", tint=0.95):
    """Leaping swordfish silhouette in the XZ plane (faces -Y), bill toward +X, centred on the origin, length L."""
    pts = [(0.5, 0.0), (0.22, 0.022), (0.16, 0.055), (0.08, 0.085), (0.05, 0.1), (0.02, 0.23), (-0.06, 0.25),
           (-0.12, 0.12), (-0.2, 0.07), (-0.34, 0.025), (-0.44, 0.14), (-0.49, 0.15), (-0.42, 0.0),
           (-0.49, -0.14), (-0.44, -0.13), (-0.34, -0.022), (-0.2, -0.06), (-0.05, -0.075), (-0.03, -0.15),
           (0.05, -0.16), (0.07, -0.085), (0.16, -0.05), (0.22, -0.012)]
    t = prism([(x * L, z * L) for x, z in pts], depth, bev=min(0.01, depth * 0.3))
    k.put(t, mat, M=M, tint=tint)
    # eye
    k.put(cyl(0.018 * L, depth + 0.01, 6), "BH_StoneDark", M=M @ TRS(0.14 * L, 0, 0.02 * L, 90, 0, 0) @ T(0, 0, -(depth + 0.01) / 2),
          tint=0.1)


def blade_shape(k, M, L=1.0, mat="BH_Silver", depth=0.03):
    """Straight sword in the XZ plane, point up (+Z), grip at z=0."""
    b = [(-0.035, 0.18), (0.035, 0.18), (0.035, 0.9), (0.0, 1.0), (-0.035, 0.9)]
    k.put(prism([(x * L, z * L) for x, z in b], depth), mat, M=M, tint=0.9)
    k.put(box(0.26 * L, depth * 1.4, 0.035 * L), mat, M=M @ T(0, 0, 0.17 * L), tint=0.8)
    k.put(box(0.03 * L, depth * 1.2, 0.16 * L), mat, M=M @ T(0, 0, 0.08 * L), tint=0.7)
    k.put(ico(0.03 * L, 1), mat, M=M @ T(0, 0, -0.01 * L), tint=0.8)


def lantern_emblem(k, M, s=1.0, mat="BH_Gold", depth=0.05):
    """Golden lantern with an eye-shaped flame, relief in the XZ plane (faces -Y), bottom at z=0, ~0.9*s tall."""
    body = [(-0.2, 0.08), (0.2, 0.08), (0.24, 0.6), (0.14, 0.7), (-0.14, 0.7), (-0.24, 0.6)]
    ring = [(x * s, z * s) for x, z in body]
    k.put(prism(ring, depth), mat, M=M, tint=0.9)
    k.put(prism([(-0.26 * s, 0.0), (0.26 * s, 0.0), (0.22 * s, 0.08 * s), (-0.22 * s, 0.08 * s)], depth * 1.3), mat, M=M, tint=0.75)
    k.put(prism([(-0.16 * s, 0.7 * s), (0.16 * s, 0.7 * s), (0.0, 0.84 * s)], depth * 1.3), mat, M=M, tint=0.75)
    k.put(torus(0.07 * s, 0.018 * s, 10, 4), mat, M=M @ TRS(0, 0, 0.9 * s, 90, 0, 0), tint=0.8)
    # eye-shaped flame (lens) inset, dark pupil
    eye = [(math.cos(a) * 0.14 * s, 0.39 * s + math.sin(a) * 0.14 * s * (0.55 if abs(math.cos(a)) > 0 else 1)
            * (1 if a < math.pi else 1)) for a in [math.tau * i / 16 for i in range(16)]]
    lens = [(math.cos(a) * 0.15 * s, 0.39 * s + math.sin(a) * 0.09 * s) for a in [math.tau * i / 16 for i in range(16)]]
    k.put(prism(lens, depth * 1.6), "BH_Flame", M=M, tint=1.0)
    k.put(cyl(0.04 * s, depth * 2.0, 10), "BH_StoneDark", M=M @ TRS(0, 0, 0.39 * s, 90, 0, 0) @ T(0, 0, -depth), tint=0.1)


def keg(k, M, H=0.62, R_=0.24, mat="BH_Wood", tint=0.75, hoops=True, segs=10):
    """Small barrel standing on its end (origin at the bottom centre)."""
    prof = [(R_ * 0.86, 0.0), (R_ * 0.97, H * 0.22), (R_, H * 0.5), (R_ * 0.97, H * 0.78), (R_ * 0.86, H)]
    k.put(lathe(prof, segs, uv_tile=0.5), mat, M=M, tint=tint, smooth=50, uv="keep")
    k.put(cyl(R_ * 0.8, 0.02, segs), "BH_WoodDark", M=M @ T(0, 0, H - 0.015), tint=0.8)
    if hoops:
        for z, rr in ((H * 0.12, 0.92), (H * 0.88, 0.92), (H * 0.35, 0.99), (H * 0.65, 0.99)):
            k.put(torus(R_ * rr + 0.006, 0.01 + R_ * 0.02, segs, 3), "BH_Iron", M=M @ T(0, 0, z), smooth=50)


def hang_lantern(k, M, s=1.0, glass="BH_Glass"):
    """Wrought-iron lantern, origin at the hanging ring top; body hangs below. Returns local light point."""
    h = 0.55 * s
    r_ = 0.2 * s
    k.put(torus(0.05 * s, 0.012 * s, 10, 4), "BH_Iron", M=M @ TRS(0, 0, -0.05 * s, 90, 0, 0))
    k.put(cyl(r_ * 1.15, 0.16 * s, 6, r2=0.03 * s), "BH_Iron", M=M @ T(0, 0, -0.26 * s), smooth=None)
    k.put(cyl(r_ * 1.1, 0.04 * s, 6), "BH_Iron", M=M @ T(0, 0, -0.28 * s))
    k.put(cyl(r_, h, 6, r2=r_ * 0.85), glass, M=M @ T(0, 0, -0.28 * s - h), uvoff=False)
    for i in range(6):
        a = math.tau * i / 6
        k.put(box(0.022 * s, 0.022 * s, h), "BH_Iron", M=M @ TRS(math.cos(a) * r_ * 0.95, math.sin(a) * r_ * 0.95,
                                                                     -0.28 * s - h / 2, 0, 0, math.degrees(a)))
    k.put(cyl(r_ * 1.1, 0.05 * s, 6), "BH_Iron", M=M @ T(0, 0, -0.33 * s - h))
    k.put(cyl(0.05 * s, 0.1 * s, 6, r2=0.0), "BH_Iron", M=M @ TRS(0, 0, -0.33 * s - h, 180, 0, 0))
    k.put(cyl(0.035 * s, 0.14 * s, 8), "BH_Candle", M=M @ T(0, 0, -0.28 * s - h + 0.02 * s))
    flame_tip(k, M @ T(0, 0, -0.28 * s - h + 0.17 * s), 0.08 * s)
    return (0, 0, -0.28 * s - h * 0.55)


def wide_window(k, M, w=1.6, h=1.3, lit=True, shutters=True):
    """Window centred on the M origin (in the wall plane), faces -Y. Glass is BH_Glass (lit from within)."""
    r = k.r
    k.put(box(w + 0.2, 0.3, h + 0.2, bev=0.02), "BH_WoodDark", M=M, tint=0.55)
    k.put(box(w, 0.33, h), "BH_Glass" if lit else "BH_StoneDark", M=M, tint=1.0 if lit else 0.05, uvoff=False)
    n = max(1, int(round(w / 0.55)))
    for i in range(1, n):
        k.put(box(0.05, 0.36, h), "BH_WoodDark", M=M @ T(-w / 2 + w * i / n, 0, 0), tint=0.5)
    k.put(box(w, 0.36, 0.05), "BH_WoodDark", M=M @ T(0, 0, h * 0.18), tint=0.5)
    k.put(box(w + 0.35, 0.42, 0.1, bev=0.02), "BH_Stone", M=M @ T(0, -0.05, -h / 2 - 0.15), tint=0.9)
    if shutters:
        for sx in (-1, 1):
            for j in range(3):
                k.put(box(w / 2 / 3 - 0.01, 0.045, h + 0.05, bev=0.008), "BH_Wood",
                      M=M @ TRS(sx * (w / 2 + 0.12 + (j + 0.5) * (w / 6)), -0.2, 0, 0, 0, 0), tint=r.uniform(0.45, 0.6))
            k.put(box(w / 2, 0.05, 0.07), "BH_WoodDark", M=M @ T(sx * (w / 2 + 0.12 + w / 4), -0.23, h * 0.3), tint=0.4)
            k.put(box(w / 2, 0.05, 0.07), "BH_WoodDark", M=M @ T(sx * (w / 2 + 0.12 + w / 4), -0.23, -h * 0.3), tint=0.4)


def roof_frame(sy, half, ang, z, ph):
    """Matrix for one roof side: local +Y runs from the ridge down to the eave (outward), local Z = up from the slope."""
    return T(0, sy * half / 2, z + ph / 2) @ R(0, 0, 0 if sy > 0 else 180) @ R(-ang, 0, 0)


def slate_roof(k, L, W, z, ph, over=0.5, mat="BH_StoneDark", step=0.42, gable_over=0.45):
    """Slate gable roof along X over a L x W footprint. z = height of the eave line at the wall face."""
    r = k.r
    half = W / 2 + over
    z0 = z - ph * over / half  # roof plane passes through (W/2, z)
    ph2 = ph + ph * over / half
    slope = math.hypot(half, ph2)
    ang = math.degrees(math.atan2(ph2, half))
    Lr = L + 2 * gable_over
    rows = int(slope / step)
    for sy in (-1, 1):
        Mf = roof_frame(sy, half, ang, z0, ph2)
        k.put(box(Lr, slope, 0.16), "BH_WoodDark", M=Mf, tint=0.45)
        for i in range(rows):
            y = -slope / 2 + slope * (i + 0.5) / rows
            ws, _ = split_lengths(r, Lr, 1.2, 2.6)
            x = -Lr / 2
            for w in ws:
                k.put(box(w - 0.015, slope / rows * 1.3, 0.045), mat,
                      M=Mf @ TRS(x + w / 2, y, 0.1 + 0.02, 5, r.uniform(-0.4, 0.4), 0), tint=r.uniform(0.55, 0.85))
                x += w
        # barge boards
        for sx in (-1, 1):
            k.put(box(0.12, slope + 0.1, 0.3, bev=0.02), "BH_WoodDark", M=Mf @ T(sx * (Lr / 2 + 0.03), 0, 0.04), tint=0.55)
    k.put(box(Lr + 0.1, 0.34, 0.2, bev=0.03), "BH_WoodDark", M=T(0, 0, z0 + ph2 + 0.1), tint=0.5)
    for i in range(int(Lr / 0.6)):
        k.put(cyl(0.12, 0.58, 6), "BH_StoneDark", M=TRS(-Lr / 2 + 0.3 + i * 0.6 - 0.29, 0, z0 + ph2 + 0.2, 0, 90, 0), tint=0.5)
    return z0, ph2


def shingle_roof(k, L, W, z, ph, over=0.45, gable_over=0.4):
    """Wooden shingle gable roof (Lantern House)."""
    return slate_roof(k, L, W, z, ph, over, mat="BH_Wood", step=0.3, gable_over=gable_over)


def stone_shell(k, L, W, h, cuts_front=(), cuts_back=(), cuts_side=(), thick=0.7, course=(0.42, 0.58),
                blen=(0.7, 1.3), mat="BH_StoneDark", cuts_left=None, cuts_right=None, chip_rng=(0, 1), **kw):
    """Four masonry walls centred on the footprint (outer faces at +-(L/2+thick/2), +-(W/2+thick/2))."""
    for (sx, sy, rot, length) in ((0, -1, 0, L), (0, 1, 0, L), (-1, 0, 90, W), (1, 0, 90, W)):
        M = T(sx * L / 2, sy * W / 2, 0) @ R(0, 0, rot)
        if sy == -1:
            cuts = cuts_front
        elif sy == 1:
            cuts = cuts_back
        elif sx == -1:
            cuts = cuts_left if cuts_left is not None else cuts_side
        else:
            cuts = cuts_right if cuts_right is not None else cuts_side
        masonry(k, -length / 2 - thick / 2, length / 2 + thick / 2, 0, h, thick, M=M, cuts=cuts, quoin="both",
                course=course, blen=blen, chip_rng=chip_rng, mat=mat, **kw)


def chimney(k, x, y, top, w=1.0, d=0.9, mat="BH_Brick", z0=0.0):
    """Masonry stack from z0 (start it inside the roof: the part below is hidden) to top."""
    masonry(k, -w / 2, w / 2, z0, top, d, mat=mat, M=T(x, y, 0), tint=(0.6, 0.85), course=(0.34, 0.46), blen=(0.5, 0.9),
            core_mat=mat, chip_rng=(0, 0))
    k.put(box(w + 0.2, d + 0.2, 0.2, bev=0.03), "BH_Stone", M=T(x, y, top + 0.1), tint=0.8)
    k.put(box(w * 0.55, d * 0.5, 0.05), "BH_StoneDark", M=T(x, y, top + 0.21), tint=0.03)


# ---------------------------------------------------------------------------------------------------------------
@asset("house_intact_door", "town2")
def house_intact_door(k):
    """Identical to house_intact (same RNG / noise seeds, same builder) plus a `door` socket."""
    k.seed = seed_of("house_intact")
    k.r = random.Random(k.seed)
    k.noff = Vector(((k.seed % 997) * 0.137, (k.seed % 991) * 0.071, (k.seed % 983) * 0.053))
    mnoise.seed_set(k.seed % 100000)
    opts = assets_town.house_intact(k)
    # door leaf front at y=-2.85, porch step y=-3.8..-2.8 (0.15 high), porch posts at y=-3.6, collision to y=-2.85:
    # the socket is on the ground just in front of the step.
    k.sockets.append(("door", (0.0, -4.0, 0.0)))
    return opts


# ---------------------------------------------------------------------------------------------------------------
def double_door(k, M, w=2.0, h=2.5):
    """Tavern double door in the wall plane at M (origin = threshold centre), faces -Y, closed with iron bands."""
    r = k.r
    k.put(box(w + 0.35, 0.34, h + 0.25, bev=0.03), "BH_WoodDark", M=M @ T(0, 0, (h + 0.25) / 2), tint=0.5)
    k.put(box(w, 0.36, h), "BH_StoneDark", M=M @ T(0, 0, h / 2), tint=0.02)
    for sx in (-1, 1):
        n = 4
        pw = (w / 2 - 0.03) / n
        for i in range(n):
            plank(k, pw - 0.01, 0.07, h - 0.04, M @ TRS(sx * (0.015 + pw * (i + 0.5)), -0.16, h / 2), tint=(0.55, 0.75))
        for z in (0.45, h - 0.5):
            k.put(box(w / 2 - 0.08, 0.04, 0.09), "BH_Iron", M=M @ T(sx * w / 4, -0.21, z))
        k.put(torus(0.07, 0.013, 10, 4), "BH_Iron", M=M @ TRS(sx * 0.16, -0.23, 1.15, 90, 0, 0))
    # stone lintel with keystone
    k.put(box(w + 0.8, 0.5, 0.32, bev=0.03), "BH_Stone", M=M @ T(0, -0.05, h + 0.4), tint=0.95)
    k.put(prism([(-0.18, 0), (0.18, 0), (0.24, 0.42), (-0.24, 0.42)], 0.56, bev=0.02), "BH_Stone", M=M @ T(0, -0.05, h + 0.25), tint=1.0)


def balcony(k, x0, x1, y_wall, z, depth=1.2):
    r = k.r
    L = x1 - x0
    cx = (x0 + x1) / 2
    n = int(L / 0.32)
    for i in range(n):  # floor boards run outward
        plank(k, depth, L / n - 0.01, 0.06, TRS(x0 + L / n * (i + 0.5), y_wall - depth / 2, z - 0.03, 0, 0, 90), tint=(0.6, 0.85))
    k.put(box(L, 0.14, 0.16), "BH_WoodDark", M=T(cx, y_wall - depth + 0.07, z - 0.1), tint=0.55)
    for x in (x0 + 0.1, cx, x1 - 0.1):  # joists + knee braces
        k.put(box(0.14, depth, 0.18), "BH_WoodDark", M=T(x, y_wall - depth / 2, z - 0.15), tint=0.55)
        d = math.hypot(0.9, 0.9)
        k.put(box(0.12, d, 0.12), "BH_WoodDark", M=TRS(x, y_wall - 0.45, z - 0.2 - 0.45, 45, 0, 0), tint=0.55)
    # railing
    posts = int(L / 0.9) + 1
    for i in range(posts):
        x = x0 + 0.06 + (L - 0.12) * i / (posts - 1)
        k.put(box(0.1, 0.1, 1.05, bev=0.01), "BH_WoodDark", M=T(x, y_wall - depth + 0.08, z + 0.52), tint=0.55)
    for sx, xx in ((-1, x0 + 0.06), (1, x1 - 0.06)):
        k.put(box(0.1, depth - 0.1, 0.08), "BH_WoodDark", M=T(xx, y_wall - depth / 2, z + 1.0), tint=0.55)
    k.put(box(L, 0.12, 0.08, bev=0.01), "BH_WoodDark", M=T(cx, y_wall - depth + 0.08, z + 1.02), tint=0.6)
    k.put(box(L, 0.08, 0.06), "BH_WoodDark", M=T(cx, y_wall - depth + 0.08, z + 0.12), tint=0.6)
    nb = int(L / 0.2)
    for i in range(nb):
        x = x0 + 0.12 + (L - 0.24) * (i + 0.5) / nb
        k.put(box(0.045, 0.045, 0.84), "BH_Wood", M=T(x, y_wall - depth + 0.08, z + 0.57), tint=r.uniform(0.5, 0.7))
    # a flower box / hanging washing line flavour: a rolled net over the rail
    k.put(tube([(x0 + 0.4, y_wall - depth + 0.02, z + 1.02), ((x0 + x1) / 2, y_wall - depth - 0.02, z + 0.7),
                (x1 - 0.5, y_wall - depth + 0.02, z + 1.02)], 0.05, 6), "BH_Rope", tint=0.8, smooth=40)


@asset("tavern_exterior", "town2")
def tavern_exterior(k):
    """The Salted Marlin: 11 x 7 m two-storey inn. Double door at x=0 on the -Y face, swordfish sign over it."""
    r = k.r
    L, W = 11.0, 7.0
    h0, h1 = 3.2, 2.8
    yF = -W / 2 - 0.35  # stone front face
    wins = (-3.6, 3.6)
    cf = [RectCut(-1.18, 1.18, 0.0, 2.75)] + [RectCut(x - 0.9, x + 0.9, 0.95, 2.35) for x in wins]
    cb = [RectCut(x - 0.5, x + 0.5, 1.0, 2.1) for x in (-3.0, 2.5)]
    cs = [RectCut(-0.6, 0.6, 1.0, 2.1)]
    stone_shell(k, L, W, h0, cf, cb, cs, course=(0.46, 0.64), blen=(0.9, 1.6), chip_rng=(0, 0))
    double_door(k, T(0, -W / 2 - 0.02, 0))
    for x in wins:
        wide_window(k, T(x, -W / 2 - 0.1, 1.65), 1.6, 1.3)
    for x in (-3.0, 2.5):
        window(k, T(x, W / 2 + 0.1, 1.55) @ R(0, 0, 180))
    for sx in (-1, 1):
        window(k, T(sx * (L / 2 + 0.1), 0, 1.55) @ R(0, 0, -90 * sx))
    # doorstep
    t = box(2.8, 0.7, 0.12, bev=0.03)
    chip(t, r, 2, 0.04)
    k.put(t, "BH_Stone", M=T(0, yF - 0.3, 0.06), tint=0.85)
    # floor band + timber upper floor
    k.put(box(L + 0.8, W + 0.8, 0.25, bev=0.03), "BH_WoodDark", M=T(0, 0, h0 + 0.12), tint=0.6)
    timber_frame(k, L + 0.4, W + 0.4, h0 + 0.25, h1)
    yU = -(W + 0.4) / 2
    for x in (-4.2, -1.6):
        window(k, T(x, yU - 0.12, h0 + 1.5))
    for x in (-1.6, 2.2):
        window(k, T(x, -yU + 0.12, h0 + 1.5) @ R(0, 0, 180))
    for sx in (-1, 1):
        window(k, T(sx * ((L + 0.4) / 2 + 0.12), -1.2, h0 + 1.5) @ R(0, 0, -90 * sx))
        window(k, T(sx * ((L + 0.4) / 2 + 0.12), 1.2, h0 + 1.5) @ R(0, 0, -90 * sx))
    # balcony door + balcony on the right half of the front
    door(k, T(3.4, yU - 0.05, h0 + 0.25))
    balcony(k, 1.5, 5.3, yU - 0.14, h0 + 0.25)
    # gable ends + thatch roof + two chimneys
    ph = 3.0
    for sx in (-1, 1):
        t = prism([(-(W + 0.4) / 2, 0), ((W + 0.4) / 2, 0), (0, ph)], 0.2)
        k.put(t, "BH_Stone", M=T(sx * (L + 0.4) / 2, 0, h0 + 0.25 + h1) @ R(0, 0, 90), tint=1.2)
        k.put(box(0.2, 0.26, ph * 0.8), "BH_WoodDark", M=T(sx * (L + 0.5) / 2, 0, h0 + 0.25 + h1 + ph * 0.4), tint=0.6)
        window(k, T(sx * ((L + 0.4) / 2 + 0.1), 0, h0 + 0.25 + h1 + 0.9) @ R(0, 0, -90 * sx) @ S(0.7))
    gable_roof(k, L + 0.4, W + 0.4, h0 + 0.25 + h1 - 0.1, ph, over=0.5)
    top = h0 + h1 + ph + 1.3
    for sx in (-1, 1):
        chimney(k, sx * (L / 2 - 1.0), W / 4 + 0.2, top, mat="BH_Stone" if sx < 0 else "BH_Brick", z0=h0 + h1)
    # sign: iron bracket from the floor band, board hanging parallel to the facade, carved swordfish
    yb = -W / 2 - 0.4
    k.put(box(0.3, 0.06, 0.5, bev=0.01), "BH_Iron", M=T(0, yb - 0.03, h0 + 0.02))
    k.put(tube([(0, yb, h0 + 0.18), (0, yb - 1.35, h0 + 0.18)], 0.03, 6), "BH_Iron")
    k.put(tube([(0, yb, h0 - 0.25), (0, yb - 0.5, h0 + 0.02), (0, yb - 0.95, h0 + 0.16)], 0.022, 6), "BH_Iron", smooth=40)
    k.put(torus(0.1, 0.012, 10, 4), "BH_Iron", M=TRS(0, yb - 0.45, h0 + 0.02, 0, 90, 0))  # scroll curl
    k.put(box(1.5, 0.05, 0.05), "BH_Iron", M=T(0, yb - 1.2, h0 + 0.17))
    ys = yb - 1.2
    zt = h0 + 0.15
    bw, bh = 1.4, 0.75
    zc = zt - 0.18 - bh / 2
    for sx in (-1, 1):
        for j in range(3):
            k.put(torus(0.03, 0.007, 6, 3), "BH_Iron", M=TRS(sx * 0.55, ys, zt - 0.03 - j * 0.05, 90 if j % 2 else 0, 0, 90))
    for i in range(3):
        plank(k, bw, 0.06, bh / 3 - 0.01, T(0, ys, zc - bh / 3 + i * bh / 3), mat="BH_WoodDark", tint=(0.55, 0.7))
    k.put(box(bw + 0.08, 0.08, 0.07), "BH_Wood", M=T(0, ys, zc + bh / 2), tint=0.6)
    k.put(box(bw + 0.08, 0.08, 0.07), "BH_Wood", M=T(0, ys, zc - bh / 2), tint=0.6)
    for sx in (-1, 1):
        k.put(box(0.07, 0.08, bh + 0.07), "BH_Wood", M=T(sx * (bw / 2 + 0.005), ys, zc), tint=0.6)
    for sy in (-1, 1):
        swordfish(k, T(0, ys + sy * 0.045, zc + 0.03) @ R(0, 0, 0 if sy < 0 else 180), 1.15, 0.04, "BH_Silver", 0.85)
    # wall lanterns flanking the door
    for sx in (-1, 1):
        x = sx * 1.55
        k.put(box(0.12, 0.05, 0.25), "BH_Iron", M=T(x, yF - 0.02, 2.55))
        k.put(tube([(x, yF, 2.6), (x, yF - 0.35, 2.62)], 0.018, 5), "BH_Iron")
        hang_lantern(k, T(x, yF - 0.35, 2.6), 0.6)
    # barrels and a crate by the entrance
    for (x, y, rot) in ((-2.1, yF - 0.45, 0), (-2.75, yF - 0.4, 30), (2.2, yF - 0.45, 10)):
        keg(k, TRS(x, y, 0, 0, 0, rot), 1.0, 0.36, tint=r.uniform(0.6, 0.8))
    k.put(box(0.7, 0.6, 0.6, bev=0.03), "BH_Wood", M=TRS(2.9, yF - 0.4, 0.3, 0, 0, 8), tint=0.7)
    k.sockets.append(("door", (0.0, yF - 0.95, 0.0)))
    k.sockets.append(("door_light", (0.0, yF - 0.5, 2.6)))
    k.sockets.append(("sign_light", (0.0, ys - 0.6, zc + 0.6)))
    k.col_box(L + 0.7, W + 0.7, h0 + h1 + 0.25, T(0, 0, (h0 + h1 + 0.25) / 2))
    k.col_box(1.5, 0.9, 1.05, T(-2.45, yF - 0.45, 0.52))
    k.col_box(0.75, 0.75, 1.0, T(2.2, yF - 0.45, 0.5))
    k.col_box(0.7, 0.6, 0.6, T(2.9, yF - 0.4, 0.3))
    return dict(recenter=False, damp=0.3, damp_h=1.2)


# ---------------------------------------------------------------------------------------------------------------
def banner_cloth(k, M, w, h, mat, trim="BH_Silver", tail=0.45, nx=4, nz=10, wave=0.03):
    """Hanging banner, top edge at M origin, hangs down -Z in the XZ plane, faces -Y, swallow-tail hem."""
    r = k.r
    t = tb()
    vs = []
    for j in range(nz + 1):
        row = []
        for i in range(nx + 1):
            u = i / nx
            x = -w / 2 + w * u
            z = -h * j / nz
            if j == nz:
                z += tail * (1 - abs(u - 0.5) * 2)  # swallow-tail notch
            y = wave * math.sin(u * 3.1 + j * 0.9) * (j / nz)
            row.append(t.verts.new((x, y, z)))
        vs.append(row)
    for j in range(nz):
        for i in range(nx):
            t.faces.new((vs[j][i], vs[j + 1][i], vs[j + 1][i + 1], vs[j][i + 1]))
    bmesh.ops.solidify(t, geom=list(t.faces), thickness=0.02)
    k.put(t, mat, M=M, tint=0.85, smooth=40, uvoff=False)
    # trim strips down both sides and along the hem
    for sx in (-1, 1):
        k.put(box(0.06, 0.035, h - 0.02), trim, M=M @ T(sx * (w / 2 - 0.03), -0.012, -h / 2 + 0.01), tint=0.9)
        hem = [(sx * (w / 2 - 0.02), 0, -h), (0, 0, -h + tail)]
        k.put(tube(hem, 0.022, 4), trim, M=M @ T(0, -0.015, 0), tint=0.9)
    k.put(box(w, 0.04, 0.07), trim, M=M @ T(0, -0.012, -0.08), tint=0.9)


def banner_pole(k, x, y, H, w, h, mat, trim, finial="BH_Silver"):
    """Free-standing pole with a crossbar and a hanging banner; returns the hang point (crossbar centre)."""
    r = k.r
    k.put(box(0.55, 0.55, 0.4, bev=0.04), "BH_Stone", M=T(x, y, 0.2), tint=0.85)
    k.put(cyl(0.07, H, 10), "BH_WoodDark", M=T(x, y, 0.4), tint=0.6, smooth=40)
    k.put(cyl(0.09, 0.08, 10), "BH_Iron", M=T(x, y, 0.4))
    zc = 0.4 + H - 0.35
    k.put(cyl(0.045, w + 0.3, 8), "BH_WoodDark", M=TRS(x - (w + 0.3) / 2, y - 0.1, zc, 0, 90, 0), tint=0.6)
    for sx in (-1, 1):
        k.put(ico(0.06, 1), finial, M=T(x + sx * (w / 2 + 0.17), y - 0.1, zc))
    k.put(cyl(0.06, 0.25, 8, r2=0.0), finial, M=T(x, y, 0.4 + H))
    k.put(ico(0.08, 1), finial, M=T(x, y, 0.4 + H))
    banner_cloth(k, T(x, y - 0.1, zc - 0.05), w, h, mat, trim)
    return (x, y - 0.1, zc)


def pillar_round(k, x, y, H, r_=0.32, mat="BH_Stone"):
    rr = k.r
    k.put(box(r_ * 2.5, r_ * 2.5, 0.3, bev=0.03), mat, M=T(x, y, 0.15), tint=0.85)
    k.put(lathe([(r_ * 1.15, 0), (r_ * 1.05, 0.14), (r_, 0.22)], 12), mat, M=T(x, y, 0.3), tint=0.9, smooth=40)
    n = max(2, int(H / 0.9))
    hh = (H - 0.9) / n
    for i in range(n):  # drums
        t = cyl(r_, hh - 0.02, 12)
        jitter(t, rr, 0.004)
        k.put(t, mat, M=T(x, y, 0.52 + i * hh), tint=rr.uniform(0.85, 1.0), smooth=40)
    k.put(lathe([(r_, 0), (r_ * 1.2, 0.18), (r_ * 1.3, 0.22)], 12), mat, M=T(x, y, 0.52 + n * hh), tint=0.95, smooth=40)
    k.put(box(r_ * 2.8, r_ * 2.8, 0.2, bev=0.03), mat, M=T(x, y, 0.52 + n * hh + 0.3), tint=0.9)


@asset("guild_hall_swordfin", "town2")
def guild_hall_swordfin(k):
    """Swordfin Hall: 10 x 8 m stone hall, tall arched door at x=0 on the -Y face, slate roof, blue banners."""
    from assets_arch import door_cuts
    r = k.r
    L, W, H = 10.0, 8.0, 5.6
    yF = -W / 2 - 0.35
    w, spring, r_in, r_out = 2.2, 2.9, 1.1, 1.55
    ph = 3.2

    def gable_top(x):
        return H + ph * (1 - abs(x) / (W / 2 + 0.35))
    cf = door_cuts(w, spring, r_out)
    side_wins = [(-2.0), (2.0)]
    cs = []
    for y in side_wins:
        cs += [RectCut(y - 0.45, y + 0.45, 1.6, 3.2), CircleCut(y, 3.2, 0.5)]
    # front + back walls: plain rectangles; gable (side) walls rise to the ridge
    for (sx, sy, rot, length) in ((0, -1, 0, L), (0, 1, 0, L)):
        M = T(0, sy * W / 2, 0) @ R(0, 0, rot)
        cuts = cf if sy < 0 else [RectCut(-2.5, -1.7, 1.8, 3.4), RectCut(1.7, 2.5, 1.8, 3.4)]
        masonry(k, -length / 2 - 0.35, length / 2 + 0.35, 0, H, 0.7, M=M, cuts=cuts, quoin="both", course=(0.5, 0.7),
                blen=(0.9, 1.7), chip_rng=(0, 0), jamb_quoin_z=spring if sy < 0 else None,
                zbreaks=(spring,) if sy < 0 else (), core_cuts=door_cuts(w, spring, r_in + 0.08) if sy < 0 else None)
    for sx in (-1, 1):
        M = T(sx * L / 2, 0, 0) @ R(0, 0, 90)
        masonry(k, -W / 2 + 0.35, W / 2 - 0.35, 0, H + ph, 0.7, M=M, cuts=cs, quoin=None, course=(0.5, 0.7),
                blen=(0.9, 1.7), chip_rng=(0, 0), top_profile=gable_top)
    arch_ring(k, 0, spring, r_in, r_out, 0.7, n=13, mat="BH_Stone")
    for y in side_wins:
        for sx in (-1, 1):
            M = T(sx * L / 2, y, 0) @ R(0, 0, 90)
            arch_ring(k, 0, 3.2, 0.45, 0.72, 0.7, n=7, mat="BH_Stone", M=M)
            k.put(box(0.9, 0.36, 1.6), "BH_Glass", M=M @ T(0, 0, 2.4), uvoff=False)
            k.put(cyl(0.45, 0.36, 12), "BH_Glass", M=M @ TRS(0, 0.18, 3.2, 90, 0, 0), uvoff=False)
            for dx in (-0.15, 0.15):
                k.put(box(0.04, 0.4, 2.0), "BH_Iron", M=M @ T(dx, 0, 2.6))
            k.put(box(1.1, 0.5, 0.12, bev=0.02), "BH_Stone", M=M @ T(0, 0, 1.55), tint=0.95)
    for x in (-2.1, 2.1):
        wide_window(k, T(x, W / 2 + 0.1, 2.6) @ R(0, 0, 180), 0.8, 1.6, shutters=False)
    # cornice along the long walls
    for sy in (-1, 1):
        k.put(box(L + 1.0, 0.95, 0.22, bev=0.04), "BH_Stone", M=T(0, sy * W / 2, H - 0.05), tint=0.95)
    slate_roof(k, L + 0.7, W, H + 0.1, ph, over=0.6, gable_over=0.2)
    # arched door leaves + tympanum
    for sx in (-1, 1):
        n = 3
        pw = (w / 2 - 0.02) / n
        for i in range(n):
            plank(k, pw - 0.01, 0.08, spring, M=T(sx * (0.01 + pw * (i + 0.5)), -W / 2 + 0.05, spring / 2), tint=(0.5, 0.7))
        for z in (0.5, 1.6, 2.6):
            k.put(box(w / 2 - 0.1, 0.04, 0.08), "BH_Iron", M=T(sx * w / 4, -W / 2, z))
        k.put(torus(0.08, 0.014, 10, 4), "BH_Iron", M=TRS(sx * 0.2, -W / 2 - 0.04, 1.3, 90, 0, 0))
    semi = [(math.cos(a) * r_in, math.sin(a) * r_in) for a in [math.pi * i / 12 for i in range(13)]]
    k.put(prism(semi, 0.1), "BH_WoodDark", M=T(0, -W / 2 + 0.05, spring), tint=0.5)
    for i in range(5):
        a = math.pi * (i + 1) / 6
        k.put(box(0.04, 0.12, r_in - 0.1), "BH_Iron", M=T(0, -W / 2 + 0.0, spring) @ R(0, 90 - math.degrees(a), 0) @ T(0, 0, (r_in - 0.1) / 2))
    t = box(w + 0.9, 1.0, 0.1, bev=0.02)
    k.put(t, "BH_Stone", M=T(0, yF - 0.35, 0.05), tint=0.9)
    # pillars flanking the door
    for sx in (-1, 1):
        pillar_round(k, sx * 1.95, yF - 0.3, H - 0.3)
    # silver swordfish over the arch, leaping over two crossed blades
    zf = spring + r_out + 0.75
    for sx in (-1, 1):
        blade_shape(k, T(sx * 0.5, yF - 0.07 - (0.03 if sx > 0 else 0), zf - 0.95) @ R(0, -sx * 32, 0), 1.5, "BH_Silver", 0.05)
    swordfish(k, T(0, yF - 0.16, zf + 0.05) @ R(0, -12, 0), 3.2, 0.1, "BH_Silver", 1.0)
    # banner poles
    bl = banner_pole(k, -3.3, yF - 0.8, 6.2, 1.0, 3.6, "BH_ClothBlue", "BH_Silver")
    br = banner_pole(k, 3.3, yF - 0.8, 6.2, 1.0, 3.6, "BH_ClothBlue", "BH_Silver")
    for (x, y, z) in (bl, br):
        swordfish(k, T(x, y - 0.035, z - 1.1), 0.75, 0.025, "BH_Silver", 0.9)
    # door lantern hung from the arch keystone
    k.put(tube([(0, yF, spring + r_out + 0.05), (0, yF - 0.45, spring + r_out + 0.05)], 0.02, 5), "BH_Iron")
    hang_lantern(k, T(0, yF - 0.45, spring + r_out), 0.55)
    k.sockets.append(("door", (0.0, yF - 1.0, 0.0)))
    k.sockets.append(("door_light", (0.0, yF - 0.45, spring + r_out - 0.45)))
    k.sockets.append(("banner_l", bl))
    k.sockets.append(("banner_r", br))
    k.col_box(L + 0.7, W + 0.7, H, T(0, 0, H / 2))
    for sx in (-1, 1):
        k.col_box(0.8, 0.8, H - 0.3, T(sx * 1.95, yF - 0.3, (H - 0.3) / 2))
        k.col_box(0.55, 0.55, 6.6, T(sx * 3.3, yF - 0.8, 3.3))
    return dict(recenter=False, damp=0.3, damp_h=1.2)


# ---------------------------------------------------------------------------------------------------------------
def wall_banner(k, x, y_wall, z, w, h, mat, trim="BH_Gold"):
    """Banner hung from an iron rod bracketed to a wall face (wall at y_wall, banner in front, -Y)."""
    for sx in (-1, 1):
        k.put(tube([(x + sx * (w / 2 + 0.05), y_wall, z + 0.1), (x + sx * (w / 2 + 0.05), y_wall - 0.3, z)], 0.02, 5), "BH_Iron")
    k.put(cyl(0.03, w + 0.3, 8), "BH_Iron", M=TRS(x - (w + 0.3) / 2, y_wall - 0.3, z, 0, 90, 0))
    for sx in (-1, 1):
        k.put(ico(0.05, 1), trim, M=T(x + sx * (w / 2 + 0.17), y_wall - 0.3, z))
    banner_cloth(k, T(x, y_wall - 0.3, z - 0.04), w, h, mat, trim, tail=0.35)
    return (x, y_wall - 0.3, z)


@asset("guild_hall_lantern", "town2")
def guild_hall_lantern(k):
    """Lantern House: 8 x 8 m, stone ground floor + tall timber upper floor, a small tower at the back-left corner,
    violet banners, a big wrought-iron lantern over the arched door (x=0, -Y face)."""
    from assets_arch import door_cuts
    r = k.r
    L, W = 7.0, 7.0  # wall centre lines; outer faces ~7.7 m
    h0, h1 = 3.8, 3.4
    yF = -W / 2 - 0.35
    w, spring, r_in, r_out = 1.8, 2.4, 0.9, 1.3
    cf = door_cuts(w, spring, r_out)
    cs = [RectCut(-0.45, 0.45, 1.2, 2.4)]
    stone_shell(k, L, W, h0, cf, [RectCut(-0.45, 0.45, 1.2, 2.4)], cs, jamb_quoin_z=None, course=(0.46, 0.64),
                blen=(0.9, 1.6), chip_rng=(0, 0))
    arch_ring(k, 0, spring, r_in, r_out, 0.7, n=11, mat="BH_Stone")
    for sx in (-1, 1):
        n = 3
        pw = (w / 2 - 0.02) / n
        for i in range(n):
            plank(k, pw - 0.01, 0.08, spring, T(sx * (0.01 + pw * (i + 0.5)), -W / 2 + 0.05, spring / 2), mat="BH_WoodDark",
                  tint=(0.5, 0.7))
        k.put(torus(0.07, 0.013, 10, 4), "BH_Iron", M=TRS(sx * 0.18, -W / 2 - 0.03, 1.2, 90, 0, 0))
        for z in (0.5, 1.9):
            k.put(box(w / 2 - 0.1, 0.04, 0.08), "BH_Iron", M=T(sx * w / 4, -W / 2 - 0.01, z))
    semi = [(math.cos(a) * r_in, math.sin(a) * r_in) for a in [math.pi * i / 12 for i in range(13)]]
    k.put(prism(semi, 0.1), "BH_WoodDark", M=T(0, -W / 2 + 0.05, spring), tint=0.45)
    k.put(cyl(0.3, 0.12, 12), "BH_Glass", M=TRS(0, -W / 2 - 0.02, spring + 0.45, 90, 0, 0), uvoff=False)
    k.put(torus(0.3, 0.03, 16, 4), "BH_Iron", M=TRS(0, -W / 2 - 0.06, spring + 0.45, 90, 0, 0))
    for sx in (-1, 1):
        window(k, T(sx * (L / 2 + 0.1), 0, 1.8) @ R(0, 0, -90 * sx))
    window(k, T(0, W / 2 + 0.1, 1.8) @ R(0, 0, 180))
    k.put(box(w + 1.0, 1.0, 0.1, bev=0.02), "BH_Stone", M=T(0, yF - 0.35, 0.05), tint=0.9)
    k.put(box(L + 0.8, W + 0.8, 0.25, bev=0.03), "BH_WoodDark", M=T(0, 0, h0 + 0.12), tint=0.6)
    timber_frame(k, L + 0.4, W + 0.4, h0 + 0.25, h1)
    yU = -(W + 0.4) / 2
    for x in (-2.0, 2.0):
        wide_window(k, T(x, yU - 0.1, h0 + 1.9), 0.8, 1.5, shutters=False)
    for sx in (-1, 1):
        window(k, T(sx * ((L + 0.4) / 2 + 0.12), -1.2, h0 + 1.8) @ R(0, 0, -90 * sx))
    # steep gable roof with wooden shingles; gable faces front/back so the tall front reads from the game camera
    ph = 3.6
    zr = h0 + 0.25 + h1
    for sy in (-1, 1):
        t = prism([(-(L + 0.4) / 2, 0), ((L + 0.4) / 2, 0), (0, ph)], 0.2)
        k.put(t, "BH_Stone", M=T(0, sy * (W + 0.4) / 2, zr), tint=1.2)
        k.put(box(0.2, 0.26, ph * 0.85), "BH_WoodDark", M=T(0, sy * (W + 0.5) / 2, zr + ph * 0.42), tint=0.6)
        for sx in (-1, 1):
            d = math.hypot((L + 0.4) / 2, ph)
            k.put(box(d, 0.26, 0.2), "BH_WoodDark", M=TRS(sx * (L + 0.4) / 4, sy * (W + 0.5) / 2, zr + ph / 2, 0,
                                                            sx * math.degrees(math.atan2(ph, (L + 0.4) / 2)), 0), tint=0.6)
    wide_window(k, T(0, yU - 0.1, zr + 1.0), 0.7, 1.0, shutters=False)
    # roof: ridge along Y -> build along X and rotate 90
    Mroof = R(0, 0, 90)
    half = (L + 0.4) / 2 + 0.5
    ph2 = ph + ph * 0.5 / ((L + 0.4) / 2)
    z0 = zr - ph * 0.5 / ((L + 0.4) / 2)
    slope = math.hypot(half, ph2)
    ang = math.degrees(math.atan2(ph2, half))
    Lr = W + 0.4 + 1.0
    rows = int(slope / 0.3)
    for sy in (-1, 1):
        Mf = Mroof @ roof_frame(sy, half, ang, z0, ph2)
        k.put(box(Lr, slope, 0.14), "BH_WoodDark", M=Mf, tint=0.45)
        for i in range(rows):
            y = -slope / 2 + slope * (i + 0.5) / rows
            ws, _ = split_lengths(r, Lr, 1.0, 2.2)
            x = -Lr / 2
            for ww in ws:
                k.put(box(ww - 0.015, slope / rows * 1.3, 0.04), "BH_Wood", M=Mf @ TRS(x + ww / 2, y, 0.1, 5, 0, 0),
                      tint=r.uniform(0.35, 0.55))
                x += ww
    k.put(box(0.3, Lr + 0.1, 0.22, bev=0.03), "BH_WoodDark", M=T(0, 0, z0 + ph2 + 0.1), tint=0.5)
    # tower at the back-left corner
    tx, ty, tw = -L / 2 - 0.2, W / 2 + 0.2, 2.6
    th = zr + ph + 2.2
    masonry(k, -tw / 2, tw / 2, 0, th, tw, M=T(tx, ty, 0), course=(0.5, 0.7), blen=(0.8, 1.3), quoin="both",
            chip_rng=(0, 0), cuts=[RectCut(-0.3, 0.3, th - 2.0, th - 0.9)])
    masonry(k, -tw / 2, tw / 2, 0, th, tw, M=T(tx, ty, 0) @ R(0, 0, 90), course=(0.5, 0.7), blen=(0.8, 1.3), quoin=None,
            chip_rng=(0, 0), core=False, cuts=[RectCut(-0.3, 0.3, th - 2.0, th - 0.9)])
    for (dx, dy, rz) in ((0, -tw / 2 - 0.02, 0), (-tw / 2 - 0.02, 0, 90), (0, tw / 2 + 0.02, 180), (tw / 2 + 0.02, 0, 270)):
        k.put(box(0.6, 0.2, 1.1), "BH_Glass", M=T(tx + dx * 0.9, ty + dy * 0.9, th - 1.45) @ R(0, 0, rz), uvoff=False)
    k.put(box(tw + 0.3, tw + 0.3, 0.25, bev=0.04), "BH_Stone", M=T(tx, ty, th + 0.12), tint=0.95)
    k.put(cyl((tw + 0.5) / 2 * 1.41, 2.6, 4, r2=0.02), "BH_WoodDark", M=TRS(tx, ty, th + 0.25, 0, 0, 45), tint=0.4)
    k.put(cyl(0.03, 0.8, 6), "BH_Iron", M=T(tx, ty, th + 2.8))
    k.put(ico(0.1, 1), "BH_Gold", M=T(tx, ty, th + 3.0))
    # violet banners on the wall either side of the door
    for sx in (-1, 1):
        wall_banner(k, sx * 2.35, yF, h0 - 0.2, 0.9, 2.6, "BH_ClothViolet", "BH_Gold")
        lantern_emblem(k, T(sx * 2.35, yF - 0.33, h0 - 1.6), 0.8, "BH_Gold", 0.03)
    # big wrought-iron lantern over the door on a scrolled bracket from the floor band
    yb = yF - 0.05
    zb = h0 + 0.05
    k.put(box(0.35, 0.08, 0.6, bev=0.01), "BH_Iron", M=T(0, yb - 0.04, zb - 0.05))
    k.put(tube([(0, yb, zb + 0.1), (0, yb - 1.3, zb + 0.1)], 0.04, 6), "BH_Iron")
    k.put(tube([(0, yb, zb - 0.4), (0, yb - 0.6, zb - 0.1), (0, yb - 1.0, zb + 0.08)], 0.03, 6), "BH_Iron", smooth=40)
    k.put(torus(0.14, 0.018, 12, 4), "BH_Iron", M=TRS(0, yb - 0.55, zb - 0.1, 0, 90, 0))
    k.put(ico(0.06, 1), "BH_Gold", M=T(0, yb - 1.33, zb + 0.1))
    lp = hang_lantern(k, T(0, yb - 1.1, zb + 0.05), 1.35)
    k.put(tube([(0, yb - 1.1, zb + 0.05), (0, yb - 1.1, zb + 0.1)], 0.02, 5), "BH_Iron")
    lantern_light = (0, yb - 1.1, zb + 0.05 + lp[2])
    k.sockets.append(("door", (0.0, yF - 1.0, 0.0)))
    k.sockets.append(("door_light", (0.0, yF - 0.6, 2.2)))
    k.sockets.append(("lantern_light", lantern_light))
    k.col_box(L + 0.7, W + 0.7, h0 + h1, T(0, 0, (h0 + h1) / 2))
    k.col_box(tw, tw, th, T(tx, ty, th / 2))
    return dict(recenter=False, damp=0.3, damp_h=1.2)
