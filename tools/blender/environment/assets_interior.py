"""Interior kit for Malasugue buildings (run bh-003): plaster / stone walls on the 4 m grid, floor, ceiling beams,
hearths, tavern bar pieces, home / guild / scholar furniture, banners, soft furnishings.

Conventions (see the contract work/lemondev/bh-003/contracts/architecture.md):
* Walls: 4 m along X, 0.3 m thick (centred on y=0), 3.6 m tall, origin at the bottom centre; the decorated / room side
  is -Y (front). Timber posts sit flush at the segment ends (x = +-1.93..2.0) so neighbours share one 0.14 m post.
* Wall-standing furniture (fireplace, shelves, wardrobe ...) is built with recenter=False and its back face on
  y = +depth/2 so it can be pushed against a wall that runs along the +Y side; free-standing furniture is re-centred
  (origin at the bottom centre of its bounding box) like assets_props.
* Ceiling pieces (int_ceiling_beams, hanging_lantern) keep the origin on the FLOOR (z=0) like the walls, so the game
  places them on the same grid point as the floor tile.
* Hanging banners (guild_banner_*) follow banner_torn: origin at the hanging rod, cloth hangs down to z=-2.4.
"""
import math

import bmesh
from mathutils import Vector

from kit import *  # noqa
from masonry import *  # noqa
from registry import asset
from assets_props import plank, rivet, flame_tip, helmet, sword
import assets_town2  # noqa  (registers the extra BH_* materials)
from assets_town2 import (swordfish, blade_shape, lantern_emblem, keg, hang_lantern, banner_cloth)

WL, WT, WH = 4.0, 0.3, 3.6
LOW_H = 0.9


# ---------------------------------------------------------------------------------------------------------------
# walls
def plaster_body(k, h, hole=None):
    """Plaster slab 4 x 0.3 x h with an optional rectangular hole (x0, x1, z0, z1)."""
    r = k.r
    pieces = []
    if hole is None:
        pieces.append((-WL / 2, WL / 2, 0, h))
    else:
        x0, x1, z0, z1 = hole
        pieces += [(-WL / 2, x0, 0, h), (x1, WL / 2, 0, h), (x0, x1, z1, h)]
        if z0 > 0:
            pieces.append((x0, x1, 0, z0))
    for (a, b, c, d) in pieces:
        if b - a < 1e-3 or d - c < 1e-3:
            continue
        t = box(b - a, WT - 0.02, d - c)
        subdiv(t, 1)
        k.put(t, "BH_Plaster", M=T((a + b) / 2, 0, (c + d) / 2), tint=r.uniform(0.92, 1.02), tile=2.0)


def wall_timbers(k, h, posts=(), rails=(), skirting=True, plate=True):
    """Dark timber on both faces: end posts (half posts at the grid ends), extra posts, rails, skirting, top plate."""
    r = k.r
    for sy in (-1, 1):
        y = sy * (WT / 2 + 0.01)
        for sx in (-1, 1):
            k.put(box(0.07, 0.06, h), "BH_WoodDark", M=T(sx * (WL / 2 - 0.035), y, h / 2), tint=r.uniform(0.55, 0.7))
        for x in posts:
            k.put(box(0.14, 0.06, h), "BH_WoodDark", M=T(x, y, h / 2), tint=r.uniform(0.55, 0.7))
        for (xa, xb, z) in rails:
            k.put(box(xb - xa, 0.06, 0.12), "BH_WoodDark", M=T((xa + xb) / 2, y, z), tint=r.uniform(0.55, 0.7))
        if skirting:
            k.put(box(WL, 0.05, 0.16), "BH_WoodDark", M=T(0, sy * (WT / 2 + 0.035), 0.08), tint=0.5)
        if plate:
            k.put(box(WL, 0.07, 0.16), "BH_WoodDark", M=T(0, y, h - 0.08), tint=0.55)


def brace(k, x0, z0, x1, z1):
    L = math.hypot(x1 - x0, z1 - z0)
    ang = math.degrees(math.atan2(z1 - z0, x1 - x0))
    for sy in (-1, 1):
        k.put(box(L, 0.05, 0.12), "BH_WoodDark", M=TRS((x0 + x1) / 2, sy * (WT / 2 + 0.01), (z0 + z1) / 2, 0, -ang, 0),
              tint=k.r.uniform(0.5, 0.65))


@asset("int_wall_plaster", "interior")
def int_wall_plaster(k):
    plaster_body(k, WH)
    wall_timbers(k, WH, posts=(0.0,), rails=((-WL / 2, WL / 2, 1.0),))
    brace(k, -1.9, 1.06, -0.1, 3.45)
    brace(k, 1.9, 1.06, 0.1, 3.45)
    k.col_box(WL, WT, WH, T(0, 0, WH / 2))
    return dict(recenter=False, damp=0.2, damp_h=0.6)


def window_insert(k, x0, x1, z0, z1):
    """Frame, lit glass (BH_Glass), mullions, sills both sides, open shutters on the room side (-Y)."""
    r = k.r
    w, h = x1 - x0, z1 - z0
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    for (sx, sz, bw, bh) in ((x0 - 0.04, cz, 0.08, h + 0.16), (x1 + 0.04, cz, 0.08, h + 0.16), (cx, z1 + 0.04, w, 0.08),
                             (cx, z0 - 0.04, w, 0.08)):
        k.put(box(bw, WT + 0.04, bh), "BH_WoodDark", M=T(sx, 0, sz), tint=0.55)
    k.put(box(w, 0.03, h), "BH_Glass", M=T(cx, 0.02, cz), uvoff=False)
    k.put(box(0.05, 0.08, h), "BH_WoodDark", M=T(cx, 0.02, cz), tint=0.5)
    for z in (z0 + h / 3, z0 + 2 * h / 3):
        k.put(box(w, 0.08, 0.04), "BH_WoodDark", M=T(cx, 0.02, z), tint=0.5)
    for sy in (-1, 1):
        k.put(box(w + 0.3, 0.14, 0.07, bev=0.015), "BH_Wood", M=T(cx, sy * (WT / 2 + 0.03), z0 - 0.1), tint=0.65)
    for sx in (-1, 1):  # shutters folded back against the room face
        for j in range(3):
            k.put(box(w / 6 - 0.008, 0.04, h - 0.04), "BH_Wood",
                  M=T(cx + sx * (w / 2 + 0.1 + (j + 0.5) * w / 6), -(WT / 2 + 0.06), cz), tint=r.uniform(0.5, 0.65))
        for z in (z0 + 0.2, z1 - 0.2):
            k.put(box(w / 2, 0.03, 0.06), "BH_Iron", M=T(cx + sx * (w / 2 + 0.1 + w / 4), -(WT / 2 + 0.09), z))
    # a candle on the sill
    k.put(cyl(0.03, 0.14, 8), "BH_Candle", M=T(cx + 0.3, -(WT / 2 + 0.03), z0 - 0.065))
    flame_tip(k, T(cx + 0.3, -(WT / 2 + 0.03), z0 + 0.1), 0.04)


@asset("int_wall_plaster_window", "interior")
def int_wall_plaster_window(k):
    x0, x1, z0, z1 = -0.65, 0.65, 1.0, 2.3
    plaster_body(k, WH, (x0 - 0.08, x1 + 0.08, z0 - 0.08, z1 + 0.08))
    wall_timbers(k, WH, posts=(-1.35, 1.35), rails=((-WL / 2, -1.35, 1.0), (1.35, WL / 2, 1.0)))
    window_insert(k, x0, x1, z0, z1)
    k.col_box(WL, WT, WH, T(0, 0, WH / 2))
    k.sockets.append(("light", (0.0, -0.4, 1.7)))
    return dict(recenter=False, damp=0.2, damp_h=0.6)


@asset("int_wall_plaster_door", "interior")
def int_wall_plaster_door(k):
    """Door opening 1.3 x 2.2 m at x=0; the leaf is hinged at x=-0.65 and stands ajar (60 deg) into the room (-Y).
    Socket `door` = floor point in front of the opening on the room side."""
    r = k.r
    w, h = 1.3, 2.2
    plaster_body(k, WH, (-w / 2 - 0.1, w / 2 + 0.1, 0, h + 0.1))
    wall_timbers(k, WH, posts=(-w / 2 - 0.17, w / 2 + 0.17), rails=((-WL / 2, -w / 2 - 0.17, 1.0), (w / 2 + 0.17, WL / 2, 1.0)))
    for sx in (-1, 1):  # jambs through the wall
        k.put(box(0.1, WT + 0.06, h + 0.1), "BH_WoodDark", M=T(sx * (w / 2 + 0.05), 0, (h + 0.1) / 2), tint=0.55)
    k.put(box(w + 0.5, WT + 0.08, 0.18), "BH_WoodDark", M=T(0, 0, h + 0.16), tint=0.5)
    k.put(box(w + 0.1, WT + 0.06, 0.03), "BH_WoodDark", M=T(0, 0, 0.015), tint=0.4)
    # leaf
    hinge = T(-w / 2 + 0.02, -WT / 2 + 0.02, 0) @ R(0, 0, -60)
    n = 5
    pw = (w - 0.04) / n
    for i in range(n):
        plank(k, pw - 0.006, 0.05, h - 0.03, hinge @ T(pw * (i + 0.5), -0.03, (h - 0.03) / 2 + 0.01), tint=(0.5, 0.7), chips=0)
    for z in (0.35, h - 0.4):
        k.put(box(w * 0.85, 0.02, 0.07), "BH_Iron", M=hinge @ T(w * 0.42, -0.065, z))
        k.put(box(w * 0.85, 0.02, 0.07), "BH_Iron", M=hinge @ T(w * 0.42, 0.005, z))
    k.put(box(w - 0.2, 0.04, 0.1), "BH_WoodDark", M=hinge @ T(w / 2, 0.0, 1.1), tint=0.4)
    k.put(torus(0.05, 0.01, 8, 4), "BH_Iron", M=hinge @ TRS(w - 0.2, -0.08, 1.05, 90, 0, 0))
    k.col_box(WL / 2 - w / 2 - 0.1, WT, WH, T(-(WL / 2 + w / 2 + 0.1) / 2, 0, WH / 2))
    k.col_box(WL / 2 - w / 2 - 0.1, WT, WH, T((WL / 2 + w / 2 + 0.1) / 2, 0, WH / 2))
    k.col_box(w + 0.2, WT, WH - h - 0.1, T(0, 0, (WH + h + 0.1) / 2))
    k.sockets.append(("door", (0.0, -0.9, 0.0)))
    return dict(recenter=False, damp=0.2, damp_h=0.6)


@asset("int_wall_plaster_low", "interior")
def int_wall_plaster_low(k):
    """Cutaway south wall: 0.9 m, plaster with a timber cap."""
    h = LOW_H
    plaster_body(k, h - 0.1)
    wall_timbers(k, h - 0.1, posts=(0.0,), plate=False)
    k.put(box(WL, WT + 0.12, 0.1, bev=0.015), "BH_WoodDark", M=T(0, 0, h - 0.05), tint=0.6)
    k.col_box(WL, WT, h, T(0, 0, h / 2))
    return dict(recenter=False, damp=0.2, damp_h=0.5)


@asset("int_wall_stone", "interior")
def int_wall_stone(k):
    masonry(k, -WL / 2, WL / 2, 0, WH - 0.18, WT, course=(0.4, 0.56), blen=(0.6, 1.2), chip_rng=(0, 1), tint=(0.75, 0.95))
    capstones(k, -WL / 2, WL / 2, WH - 0.18, WT, 0.18, over=0.03)
    for sy in (-1, 1):
        k.put(box(WL, 0.04, 0.14), "BH_StoneDark", M=T(0, sy * (WT / 2 + 0.015), 0.07), tint=0.5)
    k.col_box(WL, WT, WH, T(0, 0, WH / 2))
    return dict(recenter=False, damp=0.25, damp_h=0.7)


@asset("int_wall_stone_low", "interior")
def int_wall_stone_low(k):
    h = LOW_H
    masonry(k, -WL / 2, WL / 2, 0, h - 0.16, WT, course=(0.34, 0.4), blen=(0.6, 1.2), chip_rng=(0, 1), tint=(0.75, 0.95))
    capstones(k, -WL / 2, WL / 2, h - 0.16, WT, 0.16, over=0.04)
    k.col_box(WL, WT, h, T(0, 0, h / 2))
    return dict(recenter=False, damp=0.25, damp_h=0.5)


# ---------------------------------------------------------------------------------------------------------------
@asset("int_floor_planks", "interior")
def int_floor_planks(k):
    """4 x 4 m tile, 0.1 m thick (top at z=0.1). Boards run along X, 0.25 m wide, staggered butt joints."""
    r = k.r
    k.put(box(3.98, 3.98, 0.05), "BH_WoodDark", M=T(0, 0, 0.025), tint=0.25, uvoff=False)
    rows = 16
    rw = WL / rows
    prev = []
    for j in range(rows):
        ws, joints = split_lengths(r, WL, 1.1, 2.4, avoid=[p + 2 for p in prev], min_gap=0.3)
        x = -WL / 2
        for w in ws:
            plank(k, w - 0.008, rw - 0.008, 0.05, T(x + w / 2, -WL / 2 + rw * (j + 0.5), 0.075), tint=(0.55, 0.85), chips=0)
            x += w
        prev = [jj - 2 for jj in joints]
    k.col_box(WL, WL, 0.1, T(0, 0, 0.05))
    return dict(recenter=False)


@asset("int_ceiling_beams", "interior", col=False)
def int_ceiling_beams(k):
    """Origin on the floor. Two main beams along Y (x=+-1, bottoms at 3.4 m) carrying joists along X every 0.5 m."""
    r = k.r
    for x in (-1.0, 1.0):
        t = box(0.24, WL, 0.3, bev=0.02)
        jitter(t, r, 0.005)
        k.put(t, "BH_WoodDark", M=T(x, 0, 3.4 + 0.15), tint=r.uniform(0.5, 0.65))
        for y in (-1.2, 1.2):
            k.put(box(0.27, 0.05, 0.32), "BH_Iron", M=T(x, y, 3.55))
    for i in range(8):
        y = -WL / 2 + 0.25 + i * 0.5
        k.put(box(WL, 0.12, 0.12, bev=0.01), "BH_WoodDark", M=T(0, y, 3.76), tint=r.uniform(0.45, 0.6))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
def stone_block(k, sx, sy, sz, M, mat="BH_Stone", tint=None, chips=1):
    t = box(sx, sy, sz, bev=0.025)
    if chips:
        chip(t, k.r, k.r.randint(0, chips), 0.03)
    k.put(t, mat, M=M, tint=tint if tint is not None else k.r.uniform(0.75, 0.95))


def logs_fire(k, M, n=3, L=0.55):
    r = k.r
    for i in range(n):
        a = 360.0 * i / n + r.uniform(-15, 15)
        t = tube([(-L / 2, 0, 0), (L / 2, 0, 0)], [0.06, 0.05], 7)
        k.put(t, "BH_Bark", M=M @ TRS(0, 0, 0.07 + 0.03 * (i % 2), 0, r.uniform(-8, 8), a), tint=0.35, smooth=40)
    for i in range(5):
        h = r.uniform(0.18, 0.32)
        k.put(cyl(0.05, h, 5, r2=0.0), "BH_Flame", M=M @ TRS(r.uniform(-0.12, 0.12), r.uniform(-0.08, 0.08), 0.08,
                                                               r.uniform(-10, 10), r.uniform(-10, 10), 0), uvoff=False)
    for i in range(6):
        t = ico(0.04, 1)
        jitter(t, r, 0.01)
        k.put(t, "BH_Flame", M=M @ TRS(r.uniform(-0.2, 0.2), r.uniform(-0.12, 0.12), 0.01, s=(1, 1, 0.6)), tint=0.3)


@asset("fireplace", "interior")
def fireplace(k):
    """Stone hearth 2.2 m wide, back face at y=+0.45 (against a wall), chimney breast to 3.6 m.
    Sockets: flame (in the firebox), light (in front of it)."""
    r = k.r
    W, D = 2.2, 0.9
    ow, oh = 1.1, 0.95  # firebox opening
    yb = D / 2
    # hearth slab
    stone_block(k, W + 0.4, 0.55, 0.12, T(0, -D / 2 - 0.2, 0.06), tint=0.8)
    # jambs of stacked blocks
    z = 0.0
    hs = [0.34, 0.3, 0.31]
    for i, hh in enumerate(hs):
        for sx in (-1, 1):
            wj = (W - ow) / 2
            stone_block(k, wj - 0.02 + (0.06 if i % 2 else 0), D - 0.02, hh - 0.02,
                        T(sx * (ow / 2 + wj / 2) + sx * (0.03 if i % 2 else 0), 0, z + hh / 2))
        z += hh
    # lintel (three voussoir-ish blocks) + mantel beam
    for i, x in enumerate((-0.75, 0.0, 0.75)):
        stone_block(k, 0.74 if i != 1 else 0.72, D - 0.02, 0.34, T(x, 0, oh + 0.17), tint=0.95 if i == 1 else None)
    k.put(box(W + 0.3, D * 0.55 + 0.1, 0.16, bev=0.02), "BH_WoodDark", M=T(0, yb - (D * 0.55 + 0.1) / 2 - 0.2, 1.4), tint=0.6)
    for sx in (-1, 1):
        k.put(box(0.12, 0.2, 0.2, bev=0.02), "BH_WoodDark", M=T(sx * (W / 2 + 0.02), -D / 2 + 0.1 - 0.02, 1.25), tint=0.5)
    # chimney breast
    bw, bd = 1.6, 0.6
    zc = 1.48
    ci = 0
    while zc < WH - 0.01:
        hh = min(0.36, WH - zc)
        ws, _ = split_lengths(r, bw, 0.4, 0.8)
        x = -bw / 2 + (0.1 if ci % 2 else 0.0)
        x = -bw / 2
        for w in ws:
            stone_block(k, w - 0.02, bd, hh - 0.02, T(x + w / 2, yb - bd / 2, zc + hh / 2), chips=0)
            x += w
        zc += hh
        ci += 1
    # firebox: dark sooty back + sides + iron grate + logs
    k.put(box(ow, 0.05, oh), "BH_StoneDark", M=T(0, yb - 0.08, oh / 2), tint=0.08)
    for sx in (-1, 1):
        k.put(box(0.04, D - 0.1, oh), "BH_StoneDark", M=T(sx * (ow / 2 - 0.02), 0, oh / 2), tint=0.1)
    k.put(box(ow - 0.04, D - 0.1, 0.04), "BH_StoneDark", M=T(0, 0, oh - 0.02), tint=0.05)
    k.put(box(ow - 0.05, D - 0.05, 0.12), "BH_StoneDark", M=T(0, 0, 0.06), tint=0.15)
    gy = -0.05
    for i in range(6):
        k.put(box(0.03, 0.4, 0.03), "BH_Iron", M=T(-0.3 + i * 0.12, gy, 0.22))
    for sx in (-1, 1):
        k.put(box(0.03, 0.03, 0.22), "BH_Iron", M=T(sx * 0.33, gy - 0.18, 0.1))
        k.put(box(0.03, 0.03, 0.22), "BH_Iron", M=T(sx * 0.33, gy + 0.18, 0.1))
    k.put(box(0.7, 0.03, 0.03), "BH_Iron", M=T(0, gy - 0.2, 0.3))
    logs_fire(k, T(0, gy, 0.22), 3, 0.6)
    # tools + a pot on the hearth
    k.put(cyl(0.012, 0.8, 5), "BH_Iron", M=TRS(W / 2 + 0.1, -D / 2 - 0.15, 0.12, 8, 0, 0))
    k.put(lathe([(0.1, 0.0), (0.16, 0.08), (0.17, 0.18), (0.14, 0.22)], 10, cap_top=False), "BH_Iron", M=T(-W / 2 + 0.05, -D / 2 - 0.2, 0.12), smooth=40)
    for i in range(3):
        k.put(box(0.06, 0.06, 0.4), "BH_WoodDark", M=TRS(-W / 2 - 0.12 + i * 0.07, -D / 2 - 0.05, 0.12 + 0.2, 0, 0, 0), tint=0.5)
    k.sockets.append(("flame", (0.0, gy, 0.45)))
    k.sockets.append(("light", (0.0, -D / 2 - 0.6, 0.9)))
    k.col_box(W, D, 1.48, T(0, 0, 0.74))
    k.col_box(bw, bd, WH - 1.48, T(0, yb - bd / 2, (WH + 1.48) / 2))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
def mug(k, M, h=0.13, r_=0.05, mat="BH_Wood"):
    k.put(cyl(r_, h, 8), mat, M=M, tint=k.r.uniform(0.55, 0.8))
    k.put(cyl(r_ + 0.004, 0.015, 8, caps=False), "BH_Iron", M=M @ T(0, 0, h * 0.2))
    k.put(tube([(r_, 0, h * 0.75), (r_ + 0.04, 0, h * 0.6), (r_, 0, h * 0.25)], 0.01, 3), mat, M=M, tint=0.6)


def bottle(k, M, h=0.3, r_=0.05, mat="BH_Bottle"):
    prof = [(r_, 0.0), (r_, h * 0.55), (r_ * 0.4, h * 0.74), (r_ * 0.3, h * 0.95), (r_ * 0.3, h)]
    k.put(lathe(prof, 6), mat, M=M, smooth=50, tint=k.r.uniform(0.7, 1.0))


def book(k, M, w, d, h, mat=None, tint=None):
    mat = mat or k.r.choice(("BH_ClothRed", "BH_Cloth", "BH_ClothBlue", "BH_WoodDark", "BH_Cloth", "BH_ClothViolet"))
    k.put(box(w, d, h), mat, M=M, tint=tint if tint is not None else k.r.uniform(0.5, 1.0))


def candle(k, M, h=0.15, r_=0.025):
    k.put(cyl(r_, h, 8), "BH_Candle", M=M)
    flame_tip(k, M @ T(0, 0, h + 0.015), 0.04)


@asset("bar_counter", "interior")
def bar_counter(k):
    """4 m tavern counter along X, 1.1 m tall, 0.7 m deep. Customer side (panels + foot rail) faces -Y."""
    r = k.r
    L, D, H = 4.0, 0.7, 1.1
    # carcass: front panelling
    k.put(box(L - 0.1, 0.06, H - 0.14), "BH_WoodDark", M=T(0, -D / 2 + 0.08, (H - 0.14) / 2 + 0.06), tint=0.45)
    n = 6
    for i in range(n + 1):
        x = -L / 2 + 0.05 + (L - 0.1) * i / n
        k.put(box(0.1, 0.05, H - 0.14), "BH_Wood", M=T(x, -D / 2 + 0.03, (H - 0.14) / 2 + 0.06), tint=r.uniform(0.5, 0.65))
    for i in range(n):
        x = -L / 2 + 0.05 + (L - 0.1) * (i + 0.5) / n
        k.put(box((L - 0.1) / n - 0.24, 0.03, H - 0.46), "BH_Wood", M=T(x, -D / 2 + 0.04, H / 2 + 0.02), tint=r.uniform(0.6, 0.75))
    for z in (0.12, H - 0.13):
        k.put(box(L - 0.1, 0.06, 0.1), "BH_Wood", M=T(0, -D / 2 + 0.03, z), tint=0.6)
    k.put(box(L - 0.1, 0.06, 0.1), "BH_WoodDark", M=T(0, -D / 2 + 0.03, 0.05), tint=0.35)  # kick board
    # ends + back shelf (bartender side, +Y)
    for sx in (-1, 1):
        k.put(box(0.06, D - 0.1, H - 0.08), "BH_WoodDark", M=T(sx * (L / 2 - 0.08), 0, (H - 0.08) / 2), tint=0.5)
    plank(k, L - 0.2, D - 0.2, 0.04, T(0, 0.05, 0.5), mat="BH_WoodDark", tint=0.5, chips=0)
    # top
    for i in range(3):
        plank(k, L + 0.04, (D + 0.12) / 3 - 0.006, 0.07, T(0, -D / 2 - 0.06 + (D + 0.12) / 3 * (i + 0.5), H - 0.035),
              tint=(0.7, 0.9), chips=0)
    # foot rail
    for x in (-1.6, -0.55, 0.55, 1.6):
        k.put(tube([(x, -D / 2, 0.22), (x, -D / 2 - 0.16, 0.2), (x, -D / 2 - 0.16, 0.18)], 0.018, 5), "BH_Iron")
    k.put(cyl(0.028, L - 0.2, 8), "BH_Iron", M=TRS(-(L - 0.2) / 2, -D / 2 - 0.16, 0.18, 0, 90, 0), smooth=40)
    # clutter: mugs, a rag, coins, bottles at one end
    for x in (-1.3, -1.15, 0.6):
        mug(k, T(x, -0.1 + r.uniform(-0.05, 0.05), H))
    k.put(box(0.3, 0.2, 0.015), "BH_Cloth", M=TRS(0.1, 0.05, H + 0.008, 0, 0, 20), tint=0.7)
    for i in range(4):
        k.put(cyl(0.015, 0.005, 6), "BH_Gold", M=T(-0.4 + i * 0.03, -0.18, H + 0.003 + 0.005 * (i % 2)))
    for i in range(2):
        bottle(k, T(1.6 + i * 0.12, 0.1, H), 0.28)
    k.col_box(L + 0.04, D + 0.12, H, T(0, 0, H / 2))
    return dict(recenter=False)


@asset("bar_back_shelf", "interior")
def bar_back_shelf(k):
    """Wall shelf unit 3 m wide, 0.45 m deep, 2.4 m tall; back face at y=+0.225. Bottles, mugs and a small keg."""
    r = k.r
    W, D, H = 3.0, 0.45, 2.4
    yb = D / 2
    for sx in (-1, 0, 1):
        plank(k, H, D, 0.05, TRS(sx * (W / 2 - 0.025), 0, H / 2, 0, 90, 0), mat="BH_WoodDark", chips=0)
    k.put(box(W, 0.03, H), "BH_WoodDark", M=T(0, yb - 0.015, H / 2), tint=0.35)
    plank(k, W + 0.1, D + 0.05, 0.06, T(0, 0, H - 0.03), mat="BH_WoodDark", chips=0)
    # lower closed cabinet 0..0.9
    k.put(box(W - 0.1, D - 0.05, 0.9), "BH_WoodDark", M=T(0, 0.02, 0.45), tint=0.4)
    for i in range(4):
        x = -W / 2 + W * (i + 0.5) / 4
        k.put(box(W / 4 - 0.1, 0.03, 0.7), "BH_Wood", M=T(x, -D / 2 + 0.02, 0.47), tint=r.uniform(0.55, 0.7))
        k.put(ico(0.02, 1), "BH_Iron", M=T(x + (0.25 if i % 2 else -0.25), -D / 2 - 0.01, 0.55))
    plank(k, W + 0.06, D + 0.08, 0.05, T(0, -0.02, 0.92), chips=0)
    shelves = (1.4, 1.9)
    for z in shelves:
        plank(k, W - 0.1, D - 0.04, 0.04, T(0, 0.01, z), chips=0)
    # counter-top items: small keg on a cradle, mugs
    keg(k, T(-1.05, 0.0, 0.945) @ R(90, 0, 0) @ T(0, 0.14, -0.2), 0.4, 0.14, segs=8)
    k.put(box(0.3, 0.3, 0.06), "BH_WoodDark", M=T(-1.05, 0.0, 0.975), tint=0.5)
    k.put(cyl(0.012, 0.08, 5), "BH_Iron", M=TRS(-1.05, -0.2, 1.1, 90, 0, 0))
    for i in range(3):
        mug(k, T(0.3 + i * 0.18, -0.05, 0.945), mat="BH_Wood" if i % 2 else "BH_Iron")
    # bottles on the shelves
    for z in shelves:
        x = -W / 2 + 0.15
        while x < W / 2 - 0.15:
            if abs(x) < 0.08:
                x += 0.12
                continue
            if r.random() < 0.18:
                x += 0.18
                continue
            h = r.uniform(0.22, 0.34)
            mat = "BH_Bottle" if r.random() < 0.75 else "BH_Candle"
            bottle(k, T(x, r.uniform(-0.05, 0.08), z + 0.02), h, r.uniform(0.04, 0.055), mat)
            x += r.uniform(0.17, 0.26)
    # mugs hanging from hooks under the top
    for i in range(3):
        x = -0.9 + i * 0.9
        k.put(cyl(0.006, 0.08, 4), "BH_Iron", M=T(x, -0.12, H - 0.14))
        mug(k, T(x, -0.12, H - 0.3) @ R(180, 0, 0) @ T(0, 0, -0.13), 0.12, 0.045)
    k.col_box(W, D, H, T(0, 0, H / 2))
    return dict(recenter=False)


@asset("keg_rack", "interior")
def keg_rack(k):
    """Rack 2.1 m wide holding three lying kegs with brass taps toward -Y (back at y=+0.35)."""
    r = k.r
    W, D = 2.1, 0.7
    for sx in (-1, 0, 1):
        x = sx * (W / 2 - 0.05) if sx else 0.0
        for sy in (-1, 1):
            k.put(box(0.08, 0.08, 0.45), "BH_WoodDark", M=T(x, sy * (D / 2 - 0.05), 0.225), tint=0.55)
    for sy in (-1, 1):
        plank(k, W, 0.1, 0.08, T(0, sy * (D / 2 - 0.05), 0.42), mat="BH_WoodDark", chips=0)
        plank(k, W, 0.06, 0.06, T(0, sy * (D / 2 - 0.05), 0.1), mat="BH_WoodDark", chips=0)
    for i, x in enumerate((-0.68, 0.0, 0.68)):
        R_ = 0.3
        keg(k, T(x, 0, 0.46 + R_ * 0.9) @ R(90, 0, 0) @ T(0, 0, -0.32), 0.64, R_, tint=r.uniform(0.6, 0.8), segs=12)
        # chocks
        for sy in (-1, 1):
            for sx in (-1, 1):
                k.put(box(0.06, 0.08, 0.08), "BH_WoodDark", M=T(x + sx * 0.2, sy * (D / 2 - 0.05), 0.49), tint=0.4)
        # tap on the front head
        ty = -0.34
        k.put(cyl(0.025, 0.1, 8), "BH_Gold", M=TRS(x, ty + 0.02, 0.46 + R_ * 0.9 - 0.12, 90, 0, 0), tint=0.8)
        k.put(cyl(0.015, 0.08, 6), "BH_Gold", M=T(x, ty - 0.07, 0.46 + R_ * 0.9 - 0.2), tint=0.8)
        k.put(box(0.02, 0.02, 0.07), "BH_Gold", M=T(x, ty - 0.07, 0.46 + R_ * 0.9 - 0.08), tint=0.8)
    k.put(lathe([(0.15, 0.0), (0.17, 0.08), (0.17, 0.1), (0.0, 0.1)], 10, cap_top=False), "BH_Wood", M=T(0.68, -0.55, 0), tint=0.6)
    k.col_box(W, D, 1.1, T(0, 0, 0.55))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
@asset("stool", "interior")
def stool(k):
    r = k.r
    H = 0.7
    k.put(cyl(0.2, 0.05, 12, bev=0.01), "BH_Wood", M=T(0, 0, H - 0.05), tint=0.75)
    for i in range(3):
        a = math.tau * i / 3
        k.put(tube([(math.cos(a) * 0.1, math.sin(a) * 0.1, H - 0.05), (math.cos(a) * 0.2, math.sin(a) * 0.2, 0.0)], 0.024, 6),
              "BH_WoodDark", tint=r.uniform(0.6, 0.75))
    ring = [(math.cos(math.tau * i / 3) * 0.17, math.sin(math.tau * i / 3) * 0.17, 0.25) for i in range(3)]
    for i in range(3):
        k.put(tube([ring[i], ring[(i + 1) % 3]], 0.014, 4), "BH_WoodDark", tint=0.6)
    k.col_box(0.4, 0.4, H, T(0, 0, H / 2))
    return dict(recenter=True)


@asset("bench", "interior")
def bench(k):
    L, W, H = 1.8, 0.36, 0.46
    for i in range(2):
        plank(k, L, W / 2 - 0.008, 0.05, T(0, -W / 4 + i * W / 2, H - 0.025), warp=0.004)
    for sx in (-1, 1):
        k.put(box(0.06, W - 0.04, H - 0.05), "BH_WoodDark", M=T(sx * (L / 2 - 0.2), 0, (H - 0.05) / 2), tint=0.6)
        k.put(box(0.1, W + 0.04, 0.06), "BH_WoodDark", M=T(sx * (L / 2 - 0.2), 0, 0.03), tint=0.5)
    plank(k, L - 0.5, 0.06, 0.05, T(0, 0, 0.18), mat="BH_WoodDark")
    k.col_box(L, W, H, T(0, 0, H / 2))
    return dict(recenter=True)


@asset("table_round", "interior")
def table_round(k):
    r = k.r
    Rt, H = 0.62, 0.78
    k.put(cyl(Rt, 0.05, 20), "BH_Wood", M=T(0, 0, H - 0.05), tint=0.75)  # round top
    n = 5
    for i in range(1, n):  # board seams, clipped to the circle
        y = -Rt + 2 * Rt * i / n
        w = 2 * math.sqrt(max(0.0, Rt * Rt - y * y)) - 0.03
        k.put(box(w, 0.012, 0.004), "BH_WoodDark", M=T(0, y, H + 0.001), tint=0.3)
    k.put(torus(Rt - 0.02, 0.025, 20, 4), "BH_WoodDark", M=T(0, 0, H - 0.04), tint=0.6)
    k.put(cyl(0.07, H - 0.05, 8), "BH_WoodDark", tint=0.6)
    for a in (0, 90):
        k.put(box(0.9, 0.08, 0.08, bev=0.01), "BH_WoodDark", M=TRS(0, 0, 0.04, 0, 0, a), tint=0.55)
        k.put(box(0.6, 0.06, 0.06), "BH_WoodDark", M=TRS(0, 0, H - 0.1, 0, 0, a), tint=0.55)
    mug(k, T(0.2, 0.15, H))
    mug(k, T(-0.25, -0.1, H), mat="BH_Iron")
    candle(k, T(0.0, 0.0, H), 0.12)
    k.col_mesh(cyl(Rt, H, 10))
    return dict(recenter=True)


@asset("table_long", "interior")
def table_long(k):
    r = k.r
    L, W, H = 3.0, 0.9, 0.78
    for i in range(4):
        plank(k, L, W / 4 - 0.01, 0.06, T(0, -W / 2 + W / 4 * (i + 0.5), H - 0.03), warp=0.004, chips=0)
    for sx in (-1, 1):  # trestles
        x = sx * (L / 2 - 0.35)
        k.put(box(0.1, W - 0.2, 0.08), "BH_WoodDark", M=T(x, 0, H - 0.1), tint=0.55)
        for sy in (-1, 1):
            k.put(box(0.09, 0.09, H - 0.14), "BH_WoodDark", M=TRS(x, sy * 0.18, (H - 0.14) / 2, sy * 10, 0, 0), tint=0.6)
        k.put(box(0.12, W - 0.1, 0.08), "BH_WoodDark", M=T(x, 0, 0.04), tint=0.5)
    plank(k, L - 0.7, 0.08, 0.06, T(0, 0, 0.3), mat="BH_WoodDark", chips=0)
    for x, y in ((-1.1, 0.2), (-0.4, -0.25), (0.7, 0.22), (1.15, -0.2)):
        mug(k, T(x, y, H), mat="BH_Wood" if x < 0 else "BH_Iron")
    for x in (-0.8, 0.3):
        k.put(cyl(0.14, 0.02, 12), "BH_Wood", M=T(x, 0.0, H), tint=0.5)
        k.put(ico(0.06, 1), "BH_Bone", M=TRS(x, 0.0, H + 0.04, s=(1.4, 0.8, 0.6)), tint=0.6)
    candle(k, T(-0.2, 0.05, H), 0.14)
    candle(k, T(1.0, 0.05, H), 0.1)
    bottle(k, T(0.1, 0.25, H), 0.3)
    k.col_box(L, W, H, T(0, 0, H / 2))
    return dict(recenter=True)


# ---------------------------------------------------------------------------------------------------------------
@asset("bed_double", "interior")
def bed_double(k):
    """2.1 m x 1.6 m bed, headboard at +X (like `bed`)."""
    L, W = 2.1, 1.6
    for sy in (-1, 1):
        plank(k, L, 0.08, 0.22, T(0, sy * (W / 2 - 0.04), 0.3), mat="BH_WoodDark")
    for sx, h in ((1, 1.2), (-1, 0.65)):
        plank(k, W, 0.08, h, TRS(sx * (L / 2 - 0.04), 0, h / 2, 0, 0, 90), mat="BH_WoodDark")
        for sy in (-1, 1):
            k.put(cyl(0.05, h + 0.08, 8), "BH_WoodDark", M=T(sx * (L / 2 - 0.04), sy * (W / 2 - 0.04), 0), tint=0.6)
            k.put(ico(0.06, 1), "BH_WoodDark", M=T(sx * (L / 2 - 0.04), sy * (W / 2 - 0.04), h + 0.1), tint=0.6)
    k.put(box(0.06, W - 0.3, 0.35, bev=0.02), "BH_Wood", M=T(L / 2 - 0.06, 0, 0.85), tint=0.7)
    m = box(L - 0.16, W - 0.12, 0.2, bev=0.06, seg=2)
    ndisp(m, 4.0, 0.015, k.noff)
    k.put(m, "BH_Cloth", M=T(0, 0, 0.47), tint=0.85, smooth=40)
    for sy in (-1, 1):
        p = box(0.36, W * 0.4, 0.13, bev=0.05, seg=2)
        k.put(p, "BH_Cloth", M=TRS(L / 2 - 0.32, sy * W * 0.22, 0.61, 0, -10, 0), tint=1.05, smooth=40)
    b = box(L * 0.6, W - 0.02, 0.05, bev=0.02)
    subdiv(b, 3)
    for v in b.verts:
        if abs(v.co.y) > W / 2 - 0.12:
            v.co.z -= 0.12
    ndisp(b, 5.0, 0.02, k.noff)
    k.put(b, "BH_ClothBlue", M=T(-L * 0.18, 0, 0.59), tint=0.9, smooth=40)
    k.col_box(L, W, 0.62, T(0, 0, 0.31))
    return dict(recenter=True)


@asset("wardrobe", "interior")
def wardrobe(k):
    """1.3 x 0.6 x 2.1 m, doors toward -Y, back face at y=+0.3."""
    r = k.r
    W, D, H = 1.3, 0.6, 2.1
    k.put(box(W, D - 0.04, H - 0.2, bev=0.015), "BH_WoodDark", M=T(0, 0.02, 0.1 + (H - 0.2) / 2), tint=0.45)
    k.put(box(W + 0.1, D + 0.04, 0.12, bev=0.02), "BH_WoodDark", M=T(0, 0, H - 0.06), tint=0.55)
    k.put(box(W + 0.16, D + 0.08, 0.05, bev=0.01), "BH_WoodDark", M=T(0, 0, H - 0.005), tint=0.5)
    k.put(box(W + 0.04, D, 0.1), "BH_WoodDark", M=T(0, 0, 0.05), tint=0.4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(box(0.06, 0.06, 0.08), "BH_WoodDark", M=T(sx * (W / 2 - 0.04), sy * (D / 2 - 0.04), 0.04), tint=0.4)
        # doors: frame + raised panels
        cx = sx * W / 4
        k.put(box(W / 2 - 0.03, 0.03, H - 0.4), "BH_Wood", M=T(cx, -D / 2 - 0.0, 0.1 + (H - 0.2) / 2), tint=r.uniform(0.5, 0.6))
        for zc, hh in ((0.62, 0.62), (1.45, 0.82)):
            k.put(box(W / 2 - 0.2, 0.03, hh, bev=0.01), "BH_Wood", M=T(cx, -D / 2 - 0.02, zc), tint=r.uniform(0.65, 0.75))
        k.put(ico(0.022, 1), "BH_Iron", M=T(sx * 0.07, -D / 2 - 0.04, 1.05))
        for z in (0.35, H - 0.45):
            k.put(box(0.04, 0.03, 0.12), "BH_Iron", M=T(sx * (W / 2 - 0.02), -D / 2 - 0.01, z))
    k.put(box(0.2, 0.3, 0.2, bev=0.02), "BH_Wood", M=TRS(0.3, 0, H + 0.12, 0, 0, 10), tint=0.6)
    k.col_box(W + 0.1, D, H, T(0, 0, H / 2))
    return dict(recenter=False)


@asset("cabinet", "interior")
def cabinet(k):
    """1.0 x 0.5 x 0.95 m sideboard: drawers over doors, jug and bowl on top; back at y=+0.25."""
    r = k.r
    W, D, H = 1.0, 0.5, 0.95
    k.put(box(W - 0.04, D - 0.04, H - 0.14), "BH_WoodDark", M=T(0, 0.01, 0.1 + (H - 0.14) / 2), tint=0.45)
    plank(k, W + 0.06, D + 0.04, 0.05, T(0, 0, H - 0.025), chips=0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(box(0.06, 0.06, 0.1), "BH_WoodDark", M=T(sx * (W / 2 - 0.04), sy * (D / 2 - 0.04), 0.05), tint=0.4)
        k.put(box(W / 2 - 0.05, 0.03, 0.18), "BH_Wood", M=T(sx * W / 4, -D / 2 + 0.005, H - 0.17), tint=r.uniform(0.6, 0.7))
        k.put(ico(0.02, 1), "BH_Iron", M=T(sx * W / 4, -D / 2 - 0.02, H - 0.17))
        k.put(box(W / 2 - 0.05, 0.03, 0.5), "BH_Wood", M=T(sx * W / 4, -D / 2 + 0.005, 0.4), tint=r.uniform(0.55, 0.65))
        k.put(ico(0.02, 1), "BH_Iron", M=T(sx * 0.06, -D / 2 - 0.02, 0.5))
    k.put(lathe([(0.06, 0), (0.1, 0.08), (0.09, 0.16), (0.05, 0.22), (0.06, 0.26)], 10, cap_top=False), "BH_Brick",
          M=T(-0.25, 0.05, H), tint=0.8, smooth=40)
    k.put(lathe([(0.06, 0), (0.15, 0.06), (0.16, 0.07)], 12, cap_top=False), "BH_Wood", M=T(0.2, 0.0, H), tint=0.6, smooth=40)
    for i in range(3):
        k.put(ico(0.035, 1), "BH_ClothRed", M=T(0.2 + (i - 1) * 0.05, 0.01 * i, H + 0.05), tint=0.9)
    k.col_box(W, D, H, T(0, 0, H / 2))
    return dict(recenter=False)


@asset("crib", "interior")
def crib(k):
    r = k.r
    L, W, H = 1.0, 0.56, 0.8
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(cyl(0.025, H, 6), "BH_Wood", M=T(sx * (L / 2 - 0.03), sy * (W / 2 - 0.03), 0.08), tint=0.75)
            k.put(ico(0.035, 1), "BH_Wood", M=T(sx * (L / 2 - 0.03), sy * (W / 2 - 0.03), H + 0.1), tint=0.75)
    for sx in (-1, 1):  # rockers
        pts = [(sx * (L / 2 - 0.03), -W / 2 - 0.08 + (W + 0.16) * i / 6, 0.03 + 0.06 * ((i - 3) / 3) ** 2) for i in range(7)]
        k.put(tube(pts, 0.022, 5, flat=(1.0, 0.5)), "BH_WoodDark", tint=0.6)
        k.put(box(0.04, W, 0.05), "BH_WoodDark", M=T(sx * (L / 2 - 0.03), 0, 0.1), tint=0.6)
    for sy in (-1, 1):
        for z in (0.3, H + 0.05):
            k.put(box(L, 0.035, 0.035), "BH_Wood", M=T(0, sy * (W / 2 - 0.03), z), tint=0.7)
        for i in range(9):
            k.put(cyl(0.011, H - 0.25, 4), "BH_Wood", M=T(-L / 2 + 0.1 + i * (L - 0.2) / 8, sy * (W / 2 - 0.03), 0.3), tint=0.75)
    for sx in (-1, 1):
        for z in (0.3, H + 0.05):
            k.put(box(0.035, W, 0.035), "BH_Wood", M=T(sx * (L / 2 - 0.03), 0, z), tint=0.7)
        k.put(box(0.03, W - 0.06, H - 0.3), "BH_Wood", M=T(sx * (L / 2 - 0.03), 0, 0.3 + (H - 0.3) / 2 + 0.02), tint=0.6)
    plank(k, L - 0.06, W - 0.06, 0.03, T(0, 0, 0.3), chips=0)
    m = box(L - 0.1, W - 0.1, 0.08, bev=0.03, seg=2)
    k.put(m, "BH_Cloth", M=T(0, 0, 0.36), tint=0.95, smooth=40)
    b = box(0.5, W - 0.08, 0.04, bev=0.015)
    subdiv(b, 2)
    ndisp(b, 6.0, 0.015, k.noff)
    k.put(b, "BH_ClothBlue", M=T(-0.15, 0, 0.42), tint=1.0, smooth=40)
    k.put(ico(0.08, 2), "BH_Cloth", M=TRS(0.3, 0.05, 0.45, s=(1.0, 0.8, 0.6)), tint=0.6, smooth=50)  # rag doll/pillow
    k.col_box(L, W + 0.16, H, T(0, 0, H / 2))
    return dict(recenter=True)


@asset("washstand", "interior")
def washstand(k):
    """0.7 x 0.45 x 0.8 m stand with basin, pitcher and towel; back at y=+0.225."""
    r = k.r
    W, D, H = 0.7, 0.45, 0.8
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(box(0.05, 0.05, H), "BH_WoodDark", M=T(sx * (W / 2 - 0.03), sy * (D / 2 - 0.03), H / 2), tint=0.55)
    plank(k, W, D, 0.04, T(0, 0, H - 0.02), chips=0)
    plank(k, W - 0.06, D - 0.06, 0.03, T(0, 0, 0.18), chips=0)
    k.put(box(W, 0.03, 0.2), "BH_WoodDark", M=T(0, D / 2 - 0.015, H + 0.1), tint=0.5)
    k.put(lathe([(0.08, 0), (0.18, 0.07), (0.2, 0.1), (0.19, 0.105)], 14, cap_top=False), "BH_Brick", M=T(0, -0.02, H),
          tint=0.95, smooth=40)
    k.put(cyl(0.16, 0.01, 14), "BH_Water", M=T(0, -0.02, H + 0.06), uvoff=False)
    k.put(lathe([(0.07, 0), (0.09, 0.08), (0.08, 0.18), (0.05, 0.24), (0.065, 0.28)], 10, cap_top=False), "BH_Brick",
          M=T(0.0, 0.0, 0.195), tint=0.85, smooth=40)
    k.put(tube([(0.07, 0, 0.42), (0.13, 0, 0.38), (0.08, 0, 0.3)], 0.012, 4), "BH_Brick", tint=0.85)
    t = box(0.03, 0.3, 0.45)
    subdiv(t, 2)
    ndisp(t, 8.0, 0.01, k.noff)
    k.put(t, "BH_Cloth", M=T(W / 2 + 0.03, 0, H - 0.2), tint=1.05, smooth=40)
    k.put(cyl(0.012, D, 5), "BH_WoodDark", M=TRS(W / 2 + 0.03, -D / 2, H + 0.03, -90, 0, 0), tint=0.5)
    k.put(box(0.08, 0.05, 0.03, bev=0.01), "BH_Candle", M=T(-0.25, 0.1, H + 0.015), tint=0.9)  # soap
    k.col_box(W, D, H, T(0, 0, H / 2))
    return dict(recenter=False)


@asset("trunk", "interior")
def trunk(k):
    r = k.r
    L, W, H = 0.9, 0.5, 0.42
    for i in range(3):
        for sy in (-1, 1):
            plank(k, L, 0.03, H / 3 - 0.01, T(0, sy * (W / 2 - 0.015), H / 6 + H / 3 * i), mat="BH_WoodDark", chips=0)
    for sx in (-1, 1):
        plank(k, W - 0.06, 0.03, H, TRS(sx * (L / 2 - 0.015), 0, H / 2, 0, 0, 90), mat="BH_WoodDark", chips=0)
    k.put(box(L - 0.06, W - 0.06, 0.03), "BH_WoodDark", M=T(0, 0, 0.03), tint=0.4)
    lid = [(math.cos(a) * W / 2, math.sin(a) * 0.14) for a in [math.pi * i / 8 for i in range(9)]]
    k.put(prism(lid, L), "BH_WoodDark", M=T(0, 0, H) @ R(0, 0, 90), tint=0.6, smooth=30)
    for x in (-L / 2 + 0.16, L / 2 - 0.16):  # leather straps
        k.put(box(0.06, W + 0.02, H - 0.02), "BH_Cloth", M=T(x, 0, H / 2), tint=0.35)
        k.put(prism([(math.cos(a) * (W / 2 + 0.012), math.sin(a) * 0.152) for a in [math.pi * i / 8 for i in range(9)]], 0.06),
              "BH_Cloth", M=T(x, 0, H) @ R(0, 0, 90), tint=0.35)
        k.put(box(0.07, 0.02, 0.05), "BH_Iron", M=T(x, -W / 2 - 0.015, H - 0.1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(box(0.06, 0.06, 0.06), "BH_Iron", M=T(sx * (L / 2 - 0.02), sy * (W / 2 - 0.02), 0.04))
        k.put(torus(0.04, 0.008, 8, 3), "BH_Iron", M=TRS(sx * (L / 2 + 0.01), 0, H * 0.65, 0, 90, 0))
    k.put(box(0.09, 0.03, 0.1, bev=0.01), "BH_Iron", M=T(0, -W / 2 - 0.015, H - 0.03))
    k.col_box(L, W, H + 0.14, T(0, 0, (H + 0.14) / 2))
    return dict(recenter=True)


@asset("cooking_hearth", "interior")
def cooking_hearth(k):
    """Kitchen hearth: stone ring with coals, iron tripod with a hanging pot. Socket `flame` at the coals."""
    r = k.r
    n = 10
    for i in range(n):
        a = math.tau * i / n
        stone_block(k, 0.3, 0.2, 0.18, TRS(math.cos(a) * 0.5, math.sin(a) * 0.5, 0.09, 0, 0, math.degrees(a) + 90), chips=0)
    k.put(cyl(0.44, 0.06, 12), "BH_StoneDark", M=T(0, 0, 0.0), tint=0.12)
    for i in range(10):
        t = ico(0.06, 1)
        jitter(t, r, 0.012)
        k.put(t, "BH_Flame" if i % 2 else "BH_Dirt", M=TRS(r.uniform(-0.25, 0.25), r.uniform(-0.25, 0.25), 0.05, s=(1.2, 1, 0.6)),
              tint=0.3 if i % 2 else 0.15)
    logs_fire(k, T(0, 0, 0.02), 3, 0.5)
    top = (0, 0, 1.35)
    for i in range(3):
        a = math.tau * i / 3 + 0.4
        k.put(tube([(math.cos(a) * 0.72, math.sin(a) * 0.72, 0.0), top], 0.02, 5), "BH_Iron")
    k.put(torus(0.04, 0.01, 8, 3), "BH_Iron", M=T(0, 0, 1.33))
    for i in range(8):
        k.put(torus(0.03, 0.007, 6, 3), "BH_Iron", M=T(0, 0, 1.3 - i * 0.05) @ R(90, 0, 90 * (i % 2)) @ S(1, 1.5, 1))
    pz = 0.5
    k.put(lathe([(0.12, 0.0), (0.22, 0.07), (0.25, 0.2), (0.22, 0.32), (0.23, 0.34)], 12, cap_top=False), "BH_Iron",
          M=T(0, 0, pz), smooth=40)
    k.put(cyl(0.21, 0.01, 12), "BH_Dirt", M=T(0, 0, pz + 0.28), tint=0.5)
    k.put(tube([(-0.23, 0, pz + 0.33), (0, 0, pz + 0.55), (0.23, 0, pz + 0.33)], 0.01, 4), "BH_Iron", smooth=40)
    k.put(tube([(0.3, 0.1, pz + 0.7), (0.05, 0.05, pz + 0.25)], 0.012, 4), "BH_Wood", tint=0.6)  # ladle
    k.sockets.append(("flame", (0.0, 0.0, 0.25)))
    k.sockets.append(("light", (0.0, 0.0, 0.7)))
    k.col_mesh(cyl(0.65, 0.4, 10))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
def papers(k, x0, x1, y0, y1, z, n):
    r = k.r
    for i in range(n):
        k.put(box(r.uniform(0.2, 0.3), r.uniform(0.28, 0.36), 0.004), "BH_Paper",
              M=TRS(r.uniform(x0, x1), r.uniform(y0, y1), z + 0.003 + i * 0.004, 0, 0, r.uniform(-25, 25)), tint=r.uniform(0.8, 1.0))


def inkwell(k, M):
    k.put(lathe([(0.03, 0), (0.035, 0.04), (0.015, 0.06), (0.018, 0.07)], 8, cap_top=False), "BH_Bottle", M=M, tint=0.3)
    k.put(tube([(0.0, 0, 0.05), (0.03, 0.02, 0.2), (0.05, 0.03, 0.28)], [0.004, 0.01, 0.002], 4), "BH_Paper", M=M, tint=1.0)


@asset("desk_writing", "interior")
def desk_writing(k):
    """1.4 x 0.7 x 0.78 m scholar's desk (writer sits at -Y), papers, ink, books, candle; back at y=+0.35."""
    r = k.r
    L, W, H = 1.4, 0.7, 0.78
    for i in range(3):
        plank(k, L, W / 3 - 0.008, 0.05, T(0, -W / 2 + W / 3 * (i + 0.5), H - 0.025), chips=0)
    # drawer pedestal on the right, legs on the left
    k.put(box(0.42, W - 0.08, H - 0.05), "BH_WoodDark", M=T(L / 2 - 0.25, 0, (H - 0.05) / 2), tint=0.45)
    for j in range(3):
        k.put(box(0.36, 0.02, 0.18), "BH_Wood", M=T(L / 2 - 0.25, -W / 2 + 0.03, 0.14 + j * 0.21), tint=r.uniform(0.55, 0.7))
        k.put(ico(0.018, 1), "BH_Gold", M=T(L / 2 - 0.25, -W / 2 + 0.01, 0.14 + j * 0.21))
    for sy in (-1, 1):
        k.put(box(0.06, 0.06, H - 0.05), "BH_WoodDark", M=T(-L / 2 + 0.05, sy * (W / 2 - 0.05), (H - 0.05) / 2), tint=0.55)
    k.put(box(L - 0.4, 0.03, 0.4), "BH_WoodDark", M=T(-0.2, W / 2 - 0.05, H - 0.25), tint=0.4)
    # hutch at the back with pigeon holes
    k.put(box(L, 0.25, 0.03), "BH_WoodDark", M=T(0, W / 2 - 0.125, H + 0.45), tint=0.5)
    for x in (-L / 2 + 0.015, -0.2, 0.25, L / 2 - 0.015):
        k.put(box(0.03, 0.25, 0.45), "BH_WoodDark", M=T(x, W / 2 - 0.125, H + 0.225), tint=0.5)
    k.put(box(L, 0.02, 0.48), "BH_WoodDark", M=T(0, W / 2 - 0.01, H + 0.24), tint=0.35)
    for i in range(6):  # scrolls
        k.put(cyl(0.03, 0.22, 6), "BH_Paper", M=TRS(-0.55 + (i % 3) * 0.1, W / 2 - 0.13, H + 0.05 + (i // 3) * 0.07, 90, 0, 0)
              @ T(0, 0, -0.11), tint=r.uniform(0.7, 0.95))
    x = -0.15
    while x < 0.2:
        bw = r.uniform(0.04, 0.07)
        book(k, T(x + bw / 2, W / 2 - 0.13, H + 0.02 + 0.13), bw, 0.19, r.uniform(0.2, 0.28))
        x += bw + 0.005
    for i in range(3):
        book(k, TRS(0.45, W / 2 - 0.13, H + 0.04 + i * 0.05, 0, 0, r.uniform(-8, 8)), 0.24, 0.18, 0.045)
    papers(k, -0.4, 0.15, -0.2, 0.1, H, 6)
    k.put(box(0.34, 0.24, 0.05), "BH_ClothRed", M=TRS(0.35, -0.08, H + 0.025, 0, 0, -12), tint=0.6)  # open book
    k.put(box(0.32, 0.22, 0.012), "BH_Paper", M=TRS(0.35, -0.08, H + 0.056, 0, 0, -12))
    inkwell(k, T(-0.05, 0.12, H))
    candle(k, T(-0.55, 0.1, H), 0.16)
    k.put(cyl(0.05, 0.01, 8), "BH_Iron", M=T(-0.55, 0.1, H))
    k.col_box(L, W, H, T(0, 0, H / 2))
    return dict(recenter=False)


def island(k, M, R_, seed, z=0.0, mat="BH_Moss"):
    r = k.r
    ph = [r.uniform(0, math.tau) for _ in range(3)]
    amp = [r.uniform(0.1, 0.22), r.uniform(0.06, 0.14), r.uniform(0.03, 0.08)]
    pts = []
    for i in range(18):
        a = math.tau * i / 18
        rr = R_ * (1 + amp[0] * math.sin(2 * a + ph[0]) + amp[1] * math.sin(3 * a + ph[1]) + amp[2] * math.sin(5 * a + ph[2]))
        pts.append((math.cos(a) * rr, math.sin(a) * rr))
    t = prism(pts, 0.006)
    k.put(t, mat, M=M @ R(90, 0, 0), tint=0.9, uvoff=False)
    t2 = prism([(x * 1.12, y * 1.12) for x, y in pts], 0.003)
    k.put(t2, "BH_Paper", M=M @ T(0, 0, -0.0015) @ R(90, 0, 0), tint=0.55, uvoff=False)  # shallows / coast ink


@asset("map_table", "interior")
def map_table(k):
    """1.8 x 1.2 m table with a spread map of the four islands of Jre, compass, dividers, weights."""
    r = k.r
    L, W, H = 1.8, 1.2, 0.85
    for i in range(4):
        plank(k, L, W / 4 - 0.01, 0.05, T(0, -W / 2 + W / 4 * (i + 0.5), H - 0.025), chips=0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(lathe([(0.05, 0), (0.045, 0.2), (0.06, 0.35), (0.04, 0.5), (0.045, H - 0.08)], 8), "BH_WoodDark",
                  M=T(sx * (L / 2 - 0.1), sy * (W / 2 - 0.1), 0), tint=0.55, smooth=40)
        k.put(box(0.05, W - 0.2, 0.1), "BH_WoodDark", M=T(sx * (L / 2 - 0.1), 0, H - 0.1), tint=0.5)
    for sy in (-1, 1):
        k.put(box(L - 0.2, 0.05, 0.1), "BH_WoodDark", M=T(0, sy * (W / 2 - 0.1), H - 0.1), tint=0.5)
    # map sheet with curled ends
    mw, md = 1.4, 0.95
    t = box(mw, md, 0.004)
    bmesh.ops.subdivide_edges(t, edges=[e for e in t.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > 0.5], cuts=8)
    for v in t.verts:
        u = abs(v.co.x) / (mw / 2)
        if u > 0.82:
            v.co.z += (u - 0.82) * 0.25
    k.put(t, "BH_Paper", M=T(0, 0, H + 0.003), tint=0.95, uvoff=False)
    for (x, y, R_) in ((-0.36, 0.14, 0.17), (0.08, -0.16, 0.13), (0.34, 0.2, 0.11), (-0.1, 0.26, 0.07)):
        island(k, T(x, y, H + 0.008), R_, 0)
    # compass rose
    for a in (0, 45, 90, 135):
        s = 0.07 if a % 90 == 0 else 0.045
        k.put(prism([(-0.008, 0), (0.0, s), (0.008, 0), (0.0, -s)], 0.002), "BH_Gold", M=TRS(0.5, -0.3, H + 0.01, 90, 0, 0)
              @ R(0, a, 0), tint=0.8)
    # weights on the corners, dividers, candle
    for (x, y) in ((-0.68, -0.44), (0.68, 0.44)):
        k.put(rock(r, (0.05, 0.05, 0.035), cuts=4, subd=1), "BH_Stone", M=T(x, y, H), tint=0.7)
    inkwell(k, T(0.66, -0.44, H))
    book(k, TRS(-0.7, 0.42, H + 0.03, 0, 0, 15), 0.26, 0.2, 0.06)
    for sx in (-1, 1):
        k.put(box(0.008, 0.16, 0.006), "BH_Iron", M=TRS(0.1 + sx * 0.02, -0.33, H + 0.012, 0, 0, sx * 10))
    candle(k, T(-0.8, -0.5, H), 0.14)
    k.col_box(L, W, H, T(0, 0, H / 2))
    return dict(recenter=True)


@asset("bookshelf_full", "interior")
def bookshelf_full(k):
    """Tall (2.8 m) packed bookshelf 1.8 m wide, back at y=+0.225: books, stacks, scroll cubbies, a skull-free top."""
    r = k.r
    W, D, H = 1.8, 0.45, 2.8
    for sx in (-1, 1):
        plank(k, H, D, 0.06, TRS(sx * (W / 2 - 0.03), 0, H / 2, 0, 90, 0), mat="BH_WoodDark", chips=0)
    k.put(box(W - 0.1, 0.03, H - 0.1), "BH_WoodDark", M=T(0, D / 2 - 0.015, H / 2), tint=0.3)
    k.put(box(W + 0.12, D + 0.06, 0.1, bev=0.02), "BH_WoodDark", M=T(0, 0, H - 0.05), tint=0.55)
    k.put(box(W + 0.04, D + 0.02, 0.12), "BH_WoodDark", M=T(0, 0, 0.06), tint=0.45)
    shelves = [0.12, 0.58, 1.02, 1.46, 1.9, 2.34]
    for z in shelves[1:]:
        plank(k, W - 0.12, D - 0.03, 0.035, T(0, 0.0, z - 0.018), chips=0)
    for zi, z in enumerate(shelves):
        top = (shelves[zi + 1] - 0.04) if zi + 1 < len(shelves) else H - 0.1
        space = top - z
        x = -W / 2 + 0.07
        while x < W / 2 - 0.12:
            roll = r.random()
            if zi == 2 and -0.3 < x < 0.25:  # scroll cubby
                for j in range(9):
                    k.put(cyl(0.035, D - 0.08, 6), "BH_Paper", M=TRS(x + 0.04 + (j % 3) * 0.08, 0, z + 0.04 + (j // 3) * 0.075,
                                                                         90, 0, 0) @ T(0, 0, -(D - 0.08) / 2), tint=r.uniform(0.7, 1.0))
                x += 0.26
                continue
            if roll < 0.08:  # a lying stack
                for j in range(r.randint(2, 5)):
                    book(k, TRS(x + 0.14, -0.02, z + 0.025 + j * 0.05, 0, 0, r.uniform(-6, 6)), 0.26, 0.22, 0.045)
                x += 0.3
                continue
            if roll < 0.12:
                x += r.uniform(0.06, 0.14)
                continue
            bw = r.uniform(0.045, 0.085)
            bh = min(space - 0.02, r.uniform(0.24, 0.38))
            lean = r.uniform(-12, 12) if r.random() < 0.08 else 0.0
            book(k, TRS(x + bw / 2, -0.02 + r.uniform(-0.02, 0.02), z + bh / 2, 0, lean, 0), bw, r.uniform(0.2, 0.3), bh)
            x += bw + 0.004
    # top clutter
    k.put(lathe([(0.1, 0), (0.14, 0.12), (0.1, 0.22), (0.07, 0.26)], 10, cap_top=False), "BH_Brick", M=T(-0.5, 0, H), tint=0.8,
          smooth=40)
    for j in range(3):
        book(k, TRS(0.4, 0, H + 0.03 + j * 0.05, 0, 0, r.uniform(-10, 10)), 0.28, 0.22, 0.05)
    k.col_box(W + 0.12, D + 0.06, H, T(0, 0, H / 2))
    return dict(recenter=False)


@asset("notice_board", "interior")
def notice_board(k):
    """Guild contract board 1.8 x 1.2 m on two posts, pinned papers, a small shingle hood; faces -Y."""
    r = k.r
    W, Hb = 1.8, 1.2
    z0 = 0.8
    for sx in (-1, 1):
        k.put(box(0.1, 0.1, z0 + Hb + 0.45, bev=0.01), "BH_WoodDark", M=T(sx * (W / 2 + 0.05), 0, (z0 + Hb + 0.45) / 2), tint=0.6)
        k.put(box(0.12, 0.5, 0.08), "BH_WoodDark", M=T(sx * (W / 2 + 0.05), 0, 0.04), tint=0.5)
        k.put(box(0.05, 0.3, 0.05), "BH_WoodDark", M=TRS(sx * (W / 2 + 0.05), 0, 0.2, 45, 0, 0), tint=0.5)
    n = 6
    for i in range(n):
        plank(k, W / n - 0.01, 0.04, Hb, T(-W / 2 + W / n * (i + 0.5), 0.0, z0 + Hb / 2), tint=(0.45, 0.6), chips=0)
    for z in (z0 - 0.04, z0 + Hb + 0.04):
        k.put(box(W + 0.1, 0.07, 0.08), "BH_WoodDark", M=T(0, 0, z), tint=0.55)
    # hood
    for sy in (-1, 1):
        k.put(box(W + 0.5, 0.35, 0.04), "BH_Wood", M=TRS(0, sy * 0.15, z0 + Hb + 0.52, sy * -25, 0, 0), tint=0.45)
    k.put(box(W + 0.5, 0.06, 0.06), "BH_WoodDark", M=T(0, 0, z0 + Hb + 0.6), tint=0.5)
    # papers
    cols = 5
    for i in range(cols):
        for j in range(3):
            if r.random() < 0.18:
                continue
            x = -W / 2 + 0.18 + (W - 0.36) * i / (cols - 1) + r.uniform(-0.05, 0.05)
            z = z0 + 0.22 + j * 0.38 + r.uniform(-0.04, 0.04)
            pw, phh = r.uniform(0.2, 0.28), r.uniform(0.26, 0.34)
            M = TRS(x, -0.03, z, 0, r.uniform(-8, 8), 0)
            k.put(box(pw, 0.004, phh), "BH_Paper", M=M, tint=r.uniform(0.75, 1.0))
            k.put(ico(0.012, 1), "BH_Iron" if r.random() < 0.6 else "BH_ClothRed", M=M @ T(0, -0.008, phh / 2 - 0.03))
            if r.random() < 0.3:
                k.put(cyl(0.025, 0.006, 8), "BH_ClothRed", M=M @ TRS(pw * 0.25, -0.005, -phh / 2 + 0.05, 90, 0, 0), tint=0.9)
            for li in range(3):  # ink lines
                k.put(box(pw * 0.7, 0.002, 0.008), "BH_StoneDark", M=M @ T(0, -0.003, phh / 2 - 0.08 - li * 0.04), tint=0.1)
    k.col_box(W + 0.2, 0.3, z0 + Hb + 0.5, T(0, 0, (z0 + Hb + 0.5) / 2))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
def spear(k, M, L=2.4):
    k.put(cyl(0.02, L, 6), "BH_WoodDark", M=M, tint=0.65)
    k.put(prism([(-0.04, 0), (0.04, 0), (0.0, 0.3)], 0.012), "BH_Metal", M=M @ T(0, 0, L), tint=0.85)
    k.put(cyl(0.026, 0.08, 6), "BH_Iron", M=M @ T(0, 0, L - 0.06))
    k.put(cyl(0.022, 0.06, 6, r2=0.0), "BH_Iron", M=M @ TRS(0, 0, 0.0, 180, 0, 0))


@asset("weapon_display", "interior")
def weapon_display(k):
    """Swordfin wall display: blue-backed board with crossed spears, a round shield with the swordfish, swords on
    pegs. Back plate at y=+0.08 (hang on a wall, origin on the floor below it)."""
    r = k.r
    W, H, z0 = 2.0, 1.6, 0.9
    for i in range(5):
        plank(k, W / 5 - 0.01, 0.04, H, T(-W / 2 + W / 5 * (i + 0.5), 0.06, z0 + H / 2), mat="BH_WoodDark", chips=0)
    k.put(box(W - 0.3, 0.02, H - 0.3), "BH_ClothBlue", M=T(0, 0.03, z0 + H / 2), tint=0.9)
    for z in (z0 + 0.04, z0 + H - 0.04):
        k.put(box(W + 0.08, 0.06, 0.08), "BH_WoodDark", M=T(0, 0.05, z), tint=0.55)
    for sx in (-1, 1):
        spear(k, T(sx * 0.75, -0.05 - (0.03 if sx > 0 else 0.0), z0 - 0.35) @ R(0, -sx * 32, 0), 2.3)  # crossed
        for z in (z0 + 0.45, z0 + 1.1):
            k.put(cyl(0.02, 0.1, 6), "BH_WoodDark", M=TRS(sx * 0.9, 0.03, z, 90, 0, 0), tint=0.4)
    # shield
    Ms = TRS(0, -0.12, z0 + H / 2, 90, 0, 0)
    k.put(cyl(0.38, 0.05, 20, bev=0.01), "BH_ClothBlue", M=Ms, tint=0.9)
    k.put(torus(0.38, 0.022, 24, 4), "BH_Silver", M=Ms @ T(0, 0, 0.025))
    swordfish(k, T(0, -0.155, z0 + H / 2), 0.62, 0.02, "BH_Silver", 1.0)
    # swords on pegs
    for sx in (-1, 1):
        sword(k, T(sx * 0.62, -0.02, z0 + 0.25) @ R(0, sx * -6, 0), 1.0)
    k.col_box(W + 0.1, 0.3, z0 + H, T(0, -0.02, (z0 + H) / 2))
    return dict(recenter=False)


@asset("armor_stand", "interior")
def armor_stand(k):
    """Wooden stand with a Swordfin plate harness: breastplate, pauldrons, faulds, helmet, blue tabard. Faces -Y."""
    r = k.r
    for a in (0, 90):
        k.put(box(0.7, 0.1, 0.07, bev=0.01), "BH_WoodDark", M=TRS(0, 0, 0.035, 0, 0, a), tint=0.55)
    k.put(cyl(0.035, 1.72, 8), "BH_WoodDark", M=T(0, 0, 0.05), tint=0.6)
    k.put(box(0.62, 0.06, 0.06), "BH_WoodDark", M=T(0, 0, 1.45), tint=0.55)
    # tabard
    t = box(0.36, 0.03, 0.62)
    subdiv(t, 2)
    ndisp(t, 6.0, 0.01, k.noff)
    k.put(t, "BH_ClothBlue", M=T(0, -0.17, 0.72), tint=0.9, smooth=40)
    k.put(box(0.36, 0.035, 0.03), "BH_Silver", M=T(0, -0.175, 0.42), tint=0.8)
    # breastplate
    bp = lathe([(0.17, 0.0), (0.19, 0.12), (0.22, 0.3), (0.23, 0.42), (0.2, 0.5), (0.1, 0.56)], 14, cap_top=False, cap_bot=False)
    for v in bp.verts:
        v.co.y *= 0.72
        if v.co.y < 0:
            v.co.y *= 1.1
    bmesh.ops.solidify(bp, geom=list(bp.faces), thickness=0.012)
    k.put(bp, "BH_Metal", M=T(0, 0, 0.95), tint=0.85, smooth=45)
    k.put(box(0.02, 0.03, 0.4), "BH_Metal", M=TRS(0, -0.17, 1.2, -10, 0, 0), tint=0.9)  # ridge
    for i in range(3):  # faulds
        f = lathe([(0.2 + i * 0.015, 0.0), (0.19 + i * 0.015, 0.08)], 14, cap_top=False, cap_bot=False)
        for v in f.verts:
            v.co.y *= 0.75
        bmesh.ops.solidify(f, geom=list(f.faces), thickness=0.01)
        k.put(f, "BH_Metal", M=T(0, 0, 0.93 - i * 0.07), tint=0.8, smooth=45)
    for sx in (-1, 1):  # pauldrons
        p = ico(0.13, 2)
        for v in p.verts:
            v.co.z = max(v.co.z, -0.02)
        k.put(p, "BH_Metal", M=TRS(sx * 0.27, 0, 1.43, 0, sx * 25, 0) @ S(1.0, 1.0, 0.7), tint=0.85, smooth=45)
        k.put(torus(0.12, 0.012, 12, 4), "BH_Silver", M=TRS(sx * 0.28, 0, 1.42, 0, sx * 25, 0))
    k.put(cyl(0.07, 0.06, 10), "BH_Metal", M=T(0, 0, 1.5), tint=0.7)
    helmet(k, T(0, 0, 1.56))
    k.put(box(0.03, 0.2, 0.22), "BH_ClothBlue", M=TRS(0, 0.02, 1.9, 0, 0, 0), tint=0.9)  # crest
    swordfish(k, T(0, -0.185, 1.18), 0.22, 0.012, "BH_Silver", 1.0)
    k.col_box(0.7, 0.5, 1.9, T(0, 0, 0.95))
    return dict(recenter=True)


@asset("lectern", "interior")
def lectern(k):
    """Lantern House lectern with an open tome and a violet ribbon; reader stands at -Y."""
    r = k.r
    H = 1.1
    k.put(box(0.55, 0.45, 0.08, bev=0.02), "BH_WoodDark", M=T(0, 0, 0.04), tint=0.55)
    k.put(lathe([(0.1, 0), (0.07, 0.1), (0.06, 0.5), (0.08, 0.7), (0.06, H - 0.2)], 8), "BH_WoodDark", M=T(0, 0, 0.08),
          tint=0.6, smooth=40)
    top = TRS(0, 0, H, 25, 0, 0)
    k.put(box(0.6, 0.45, 0.04, bev=0.01), "BH_WoodDark", M=top, tint=0.55)
    k.put(box(0.6, 0.03, 0.06), "BH_WoodDark", M=top @ T(0, -0.23, 0.04), tint=0.5)
    # open tome
    for sx in (-1, 1):
        pg = box(0.24, 0.34, 0.04)
        bmesh.ops.subdivide_edges(pg, edges=[e for e in pg.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > 0.1], cuts=4)
        for v in pg.verts:
            u = (v.co.x * sx + 0.12) / 0.24
            v.co.z += 0.03 * math.sin(u * math.pi) * (1 if v.co.z > 0 else 0.5)
        k.put(pg, "BH_Paper", M=top @ T(sx * 0.125, 0, 0.05), tint=0.95, smooth=40)
        k.put(box(0.27, 0.37, 0.015), "BH_ClothViolet", M=top @ T(sx * 0.13, 0, 0.025), tint=0.8)
        for li in range(6):
            k.put(box(0.17, 0.006, 0.002), "BH_StoneDark", M=top @ T(sx * 0.125, -0.12 + li * 0.045, 0.078), tint=0.1)
    k.put(box(0.02, 0.005, 0.3), "BH_ClothViolet", M=top @ TRS(0.01, -0.17, -0.1, 0, 0, 0), tint=0.9)
    lantern_emblem(k, top @ T(0, -0.245, -0.14), 0.16, "BH_Gold", 0.01)  # plaque on the front lip
    k.col_box(0.6, 0.5, H, T(0, 0, H / 2))
    return dict(recenter=True)


@asset("lantern_stand", "interior")
def lantern_stand(k):
    """2.3 m wrought-iron stand, crook arm, lit lantern. Socket `light` in the lantern."""
    r = k.r
    for i in range(3):
        a = math.tau * i / 3
        k.put(tube([(0, 0, 0.35), (math.cos(a) * 0.25, math.sin(a) * 0.25, 0.08), (math.cos(a) * 0.32, math.sin(a) * 0.32, 0.0)],
                   0.02, 5), "BH_Iron", smooth=40)
        k.put(ico(0.03, 1), "BH_Iron", M=T(math.cos(a) * 0.32, math.sin(a) * 0.32, 0.02))
    k.put(cyl(0.025, 2.0, 8), "BH_Iron", M=T(0, 0, 0.3), smooth=40)
    k.put(ico(0.045, 1), "BH_Iron", M=T(0, 0, 1.2))
    pts = [(0, 0, 2.2), (0.08, 0, 2.38), (0.3, 0, 2.42), (0.45, 0, 2.3)]
    k.put(tube(pts, 0.018, 5), "BH_Iron", smooth=40)
    k.put(torus(0.06, 0.01, 10, 4), "BH_Iron", M=TRS(0.03, 0, 2.1, 90, 0, 0))
    k.put(cyl(0.008, 0.15, 4), "BH_Iron", M=T(0.45, 0, 2.15))
    lp = hang_lantern(k, T(0.45, 0, 2.15), 0.75)
    k.put(cyl(0.012, 0.3, 6, r2=0.0), "BH_Gold", M=T(0, 0, 2.3), tint=0.8)
    k.sockets.append(("light", (0.45, 0.0, 2.15 + lp[2])))
    k.col_box(0.3, 0.3, 2.3, T(0, 0, 1.15))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
def interior_banner(k, cloth, trim, emblem):
    W, H = 1.2, 2.4
    k.put(cyl(0.03, W + 0.3, 8), "BH_WoodDark", M=TRS(-(W + 0.3) / 2, 0, 0, 0, 90, 0), tint=0.7)
    for sx in (-1, 1):
        k.put(ico(0.05, 1), trim, M=T(sx * (W / 2 + 0.16), 0, 0))
        k.put(tube([(sx * 0.4, 0, 0.0), (0, 0, 0.35), (-sx * 0.0, 0, 0.35)], 0.008, 4), "BH_Rope", tint=0.7)
    banner_cloth(k, T(0, 0, -0.04), W, H, cloth, trim, tail=0.4, nx=6, nz=12, wave=0.025)
    emblem()


@asset("guild_banner_swordfin", "interior", col=False)
def guild_banner_swordfin(k):
    """Silver swordfish leaping over two crossed blades on sea-blue; origin at the rod, hangs down to z=-2.4."""
    def emb():
        for sx in (-1, 1):
            blade_shape(k, T(sx * 0.28, -0.045 - (0.012 if sx > 0 else 0), -2.0) @ R(0, -sx * 30, 0), 0.9, "BH_Silver", 0.025)  # X
        swordfish(k, T(0, -0.07, -0.85) @ R(0, -15, 0), 0.95, 0.03, "BH_Silver", 1.0)
    interior_banner(k, "BH_ClothBlue", "BH_Silver", emb)
    return dict(recenter=False)


@asset("guild_banner_lantern", "interior", col=False)
def guild_banner_lantern(k):
    """Golden lantern with an eye-shaped flame on dusk violet; origin at the rod, hangs down to z=-2.4."""
    def emb():
        lantern_emblem(k, T(0, -0.05, -1.75), 0.95, "BH_Gold", 0.03)
        for sx in (-1, 1):  # rays
            for i in range(3):
                a = -30 + i * 30
                k.put(box(0.03, 0.02, 0.18), "BH_Gold", M=T(0, -0.045, -1.33) @ R(0, sx * (40 + i * 25), 0) @ T(0, 0, 0.55), tint=0.8)
    interior_banner(k, "BH_ClothViolet", "BH_Gold", emb)
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
def fish(k, M, L=0.4, mat="BH_Silver", tint=0.6):
    pts = [(0.5, 0.0), (0.38, 0.1), (0.1, 0.15), (-0.25, 0.08), (-0.38, 0.03), (-0.5, 0.13), (-0.46, 0.0), (-0.5, -0.13),
           (-0.38, -0.03), (-0.25, -0.07), (0.1, -0.12), (0.38, -0.08)]
    k.put(prism([(x * L, z * L) for x, z in pts], 0.05 * L / 0.4), mat, M=M, tint=tint)


@asset("fishing_nets", "interior")
def fishing_nets(k):
    """Net draped over a 2.4 m pole frame with cork floats and glass floats; faces -Y."""
    r = k.r
    W, H = 2.4, 2.0
    for sx in (-1, 1):
        k.put(cyl(0.05, H + 0.1, 8), "BH_Bark", M=TRS(sx * W / 2, 0, 0, 0, sx * 3, 0), tint=0.7, smooth=40)
    k.put(cyl(0.045, W + 0.3, 8), "BH_Bark", M=TRS(-(W + 0.3) / 2, 0, H, 0, 90, 0), tint=0.7, smooth=40)
    # net: hanging threads with sag + horizontal threads
    nx, nz = 12, 9

    def P(i, j):
        u = i / nx
        x = -W / 2 + 0.1 + (W - 0.2) * u
        z = H - 0.03 - (H - 0.3) * j / nz - 0.12 * math.sin(u * math.pi) * (j / nz)  # bottom row stays >= 0.15 m
        y = -0.06 - 0.12 * math.sin(u * math.pi) * (j / nz) ** 1.5 + 0.03 * math.sin(i * 1.7 + j)
        return (x, y, z)
    for i in range(nx + 1):
        k.put(tube([P(i, j) for j in range(nz + 1)], 0.006, 3, cap_start=False, cap_end=False), "BH_Rope", tint=0.8, uvoff=False)
    for j in range(1, nz + 1):
        k.put(tube([P(i, j) for i in range(nx + 1)], 0.006, 3, cap_start=False, cap_end=False), "BH_Rope", tint=0.8, uvoff=False)
    for i in range(0, nx + 1, 2):
        x, y, z = P(i, nz)
        k.put(cyl(0.035, 0.08, 6), "BH_Wood", M=TRS(x, y, z - 0.04, 0, 90, 0) @ T(0, 0, -0.04), tint=0.9)
    for (i, j) in ((3, 4), (9, 6), (12, 3)):
        x, y, z = P(i, j)
        k.put(ico(0.08, 1), "BH_Bottle", M=T(x, y - 0.08, z - 0.08), smooth=50)
        k.put(torus(0.08, 0.006, 8, 3), "BH_Rope", M=TRS(x, y - 0.08, z - 0.08, 90, 0, 0))
    # coiled rope + a basket at the foot
    for i in range(4):
        k.put(torus(0.22 - i * 0.03, 0.02, 10, 3), "BH_Rope", M=T(-0.7, -0.35, 0.02 + i * 0.035), tint=0.8)
    k.put(lathe([(0.18, 0.0), (0.24, 0.3), (0.22, 0.3), (0.16, 0.02), (0.0, 0.02)], 10, cap_top=False), "BH_Thatch",
          M=T(0.7, -0.3, 0), tint=0.7)
    fish(k, TRS(0.7, -0.3, 0.3, 0, 60, 20), 0.35)
    k.col_box(W + 0.2, 0.5, H, T(0, -0.1, H / 2))
    return dict(recenter=False)


@asset("fish_rack", "interior")
def fish_rack(k):
    """A-frame drying rack 2.2 m wide with rows of split fish hanging from strings."""
    r = k.r
    W, H = 2.2, 1.8
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(tube([(sx * W / 2, sy * 0.55, 0.0), (sx * W / 2, 0, H)], 0.035, 6), "BH_Bark", tint=0.7)
    k.put(cyl(0.04, W + 0.2, 8), "BH_Bark", M=TRS(-(W + 0.2) / 2, 0, H - 0.02, 0, 90, 0), tint=0.7)
    for sy in (-1, 1):
        z = H * 0.55
        k.put(cyl(0.03, W, 6), "BH_Wood", M=TRS(-W / 2, sy * 0.55 * (1 - z / H), z, 0, 90, 0), tint=0.65)
    rows = ((0.0, H - 0.02), (-0.55 * 0.45, H * 0.55), (0.55 * 0.45, H * 0.55))
    for (y, z) in rows:
        for i in range(6):
            x = -W / 2 + 0.25 + i * (W - 0.5) / 5 + r.uniform(-0.05, 0.05)
            L = r.uniform(0.32, 0.45)
            k.put(cyl(0.004, 0.12, 3), "BH_Rope", M=T(x, y, z - 0.12))
            fish(k, T(x, y, z - 0.12 - L / 2) @ R(0, 90, r.uniform(-20, 20)), L, "BH_Silver", r.uniform(0.45, 0.7))
    k.col_box(W + 0.1, 1.1, H, T(0, 0, H / 2))
    return dict(recenter=True)


def figure_serpent(k, M):
    pts = []
    for i in range(20):
        t = i / 19
        a = t * math.tau * 1.6
        rr = 0.09 * (1 - t * 0.55)
        pts.append((math.cos(a) * rr, math.sin(a) * rr, 0.02 + t * 0.2))
    k.put(tube(pts, [0.028 * (1 - i / 25) for i in range(20)], 6), "BH_Stone", M=M, tint=0.9, smooth=40)
    k.put(ico(0.035, 1), "BH_Stone", M=M @ T(pts[-1][0] * 1.2, pts[-1][1] * 1.2, 0.24), tint=0.9)


def figure_giant(k, M):
    k.put(box(0.12, 0.08, 0.16, bev=0.02), "BH_Stone", M=M @ T(0, 0, 0.16), tint=0.85)  # torso
    k.put(box(0.1, 0.07, 0.08, bev=0.015), "BH_Stone", M=M @ T(0, 0, 0.05), tint=0.8)  # hips/legs block
    for sx in (-1, 1):
        k.put(box(0.04, 0.04, 0.1), "BH_Stone", M=M @ T(sx * 0.03, 0, 0.0 + 0.05), tint=0.8)
        k.put(box(0.04, 0.04, 0.16, bev=0.01), "BH_Stone", M=M @ TRS(sx * 0.085, 0, 0.14, 0, sx * 12, 0), tint=0.85)
    k.put(ico(0.045, 1), "BH_Stone", M=M @ T(0, 0, 0.28), tint=0.9)
    k.put(box(0.2, 0.1, 0.02), "BH_Stone", M=M, tint=0.7)


def figure_beast(k, M):
    body = ico(0.08, 2)
    for v in body.verts:
        v.co.x *= 1.6
    k.put(body, "BH_Stone", M=M @ T(0, 0, 0.12), tint=0.85, smooth=45)
    k.put(ico(0.05, 1), "BH_Stone", M=M @ T(0.14, 0, 0.17), tint=0.9)
    for sx in (-1, 1):
        k.put(cyl(0.012, 0.06, 4, r2=0.0), "BH_Bone", M=M @ TRS(0.15, sx * 0.03, 0.2, sx * 30, 0, 0), tint=0.8)
        for fx in (-0.08, 0.08):
            k.put(cyl(0.02, 0.08, 5), "BH_Stone", M=M @ T(fx, sx * 0.04, 0.0), tint=0.8)
    k.put(tube([(-0.12, 0, 0.13), (-0.2, 0, 0.1), (-0.24, 0, 0.16)], 0.012, 4), "BH_Stone", M=M, tint=0.8)
    k.put(box(0.3, 0.12, 0.02), "BH_Stone", M=M, tint=0.7)


@asset("shrine_small", "interior")
def shrine_small(k):
    """Keeper's household shrine: stone altar (back at y=+0.25), candles, offering bowl and three carved creature
    figures (serpent / giant / beast - the Oros, a Gigas and a Tyrant beast)."""
    r = k.r
    W, D, H = 1.1, 0.5, 0.85
    stone_block(k, W + 0.1, D + 0.1, 0.12, T(0, 0, 0.06), tint=0.8)
    stone_block(k, W - 0.1, D - 0.1, H - 0.24, T(0, 0, 0.12 + (H - 0.24) / 2), tint=0.85)
    stone_block(k, W + 0.08, D + 0.06, 0.12, T(0, 0, H - 0.06), tint=0.95)
    k.put(box(0.5, 0.02, 0.3), "BH_StoneDark", M=T(0, -D / 2 + 0.04, 0.45), tint=0.4)
    # back tablet
    k.put(prism([(-0.45, 0), (0.45, 0), (0.45, 0.45), (0.0, 0.62), (-0.45, 0.45)], 0.08, bev=0.015), "BH_Stone",
          M=T(0, D / 2 - 0.08, H), tint=0.9)
    for i in range(3):
        a = math.pi * (i + 1) / 4
        k.put(box(0.03, 0.02, 0.2), "BH_Gold", M=T(0, D / 2 - 0.13, H + 0.25) @ R(0, 90 - math.degrees(a), 0) @ T(0, 0, 0.12), tint=0.7)
    k.put(cyl(0.06, 0.02, 12), "BH_Gold", M=TRS(0, D / 2 - 0.13, H + 0.25, 90, 0, 0), tint=0.8)
    figure_serpent(k, T(-0.36, 0.02, H))
    figure_giant(k, T(0.0, 0.04, H))
    figure_beast(k, TRS(0.36, 0.02, H, 0, 0, 200))
    k.put(lathe([(0.04, 0), (0.1, 0.04), (0.11, 0.06)], 10, cap_top=False), "BH_Brick", M=T(-0.15, -0.14, H), tint=0.8)
    for i in range(3):
        k.put(ico(0.02, 1), "BH_ClothRed", M=T(-0.15 + (i - 1) * 0.03, -0.14, H + 0.04), tint=0.8)
    for (x, y, h) in ((0.2, -0.17, 0.14), (0.28, -0.12, 0.09), (-0.45, -0.16, 0.12), (0.47, -0.18, 0.07)):
        candle(k, T(x, y, H), h, 0.022)
    k.sockets.append(("light", (0.0, -0.3, H + 0.35)))
    k.col_box(W + 0.1, D + 0.1, H, T(0, 0, H / 2))
    return dict(recenter=False)


@asset("hanging_lantern", "interior", col=False)
def hanging_lantern(k):
    """Ceiling lantern on a chain; origin on the floor, ceiling plate at 3.4 m, lantern body ~2.2-2.7 m."""
    k.put(cyl(0.1, 0.04, 8), "BH_Iron", M=T(0, 0, 3.36))
    k.put(torus(0.03, 0.008, 6, 3), "BH_Iron", M=TRS(0, 0, 3.33, 90, 0, 0))
    n = 9
    for i in range(n):
        k.put(torus(0.028, 0.007, 6, 3), "BH_Iron", M=T(0, 0, 3.28 - i * 0.055) @ R(90, 0, 90 * (i % 2)) @ S(1, 1.5, 1))
    top = 3.28 - n * 0.055 + 0.02
    lp = hang_lantern(k, T(0, 0, top), 0.9)
    k.sockets.append(("light", (0.0, 0.0, top + lp[2])))
    return dict(recenter=False)


@asset("rug_round", "interior", col=False)
def rug_round(k):
    r = k.r
    R_ = 1.0
    k.put(cyl(R_, 0.015, 32), "BH_ClothRed", tint=0.8, uvoff=False)
    for rr, mat, tint in ((0.92, "BH_Cloth", 0.9), (0.84, "BH_ClothRed", 0.7), (0.62, "BH_Cloth", 0.85), (0.56, "BH_ClothBlue", 0.8),
                          (0.3, "BH_Cloth", 0.9)):
        k.put(torus(rr, 0.025, 32, 3), mat, M=TRS(0, 0, 0.016, s=(1, 1, 0.12)), tint=tint)
    for i in range(8):
        a = 360.0 * i / 8
        k.put(prism([(-0.05, 0), (0.05, 0), (0, 0.18)], 0.003), "BH_Gold", M=TRS(0, 0, 0.018, 0, 0, a) @ T(0, -0.33, 0) @ R(90, 0, 0),
              tint=0.7)
    for i in range(48):
        a = math.tau * i / 48
        k.put(box(0.1, 0.012, 0.005), "BH_Cloth", M=TRS(math.cos(a) * (R_ + 0.045), math.sin(a) * (R_ + 0.045), 0.003, 0, 0,
                                                        math.degrees(a) + r.uniform(-15, 15)), tint=0.8)
    return dict(recenter=False)


@asset("curtain", "interior", col=False)
def curtain(k):
    """Curtain for a 1.3 m window: iron rod at 2.5 m on wall brackets (back at y=0, hangs toward -Y), two gathered
    panels tied back. Origin on the floor below the rod centre."""
    r = k.r
    W, z = 1.9, 2.5
    k.put(cyl(0.015, W + 0.1, 6), "BH_Iron", M=TRS(-(W + 0.1) / 2, -0.12, z, 0, 90, 0))
    for sx in (-1, 1):
        k.put(ico(0.03, 1), "BH_Iron", M=T(sx * (W / 2 + 0.07), -0.12, z))
        k.put(box(0.03, 0.12, 0.03), "BH_Iron", M=T(sx * (W / 2 - 0.05), -0.06, z))
    for sx in (-1, 1):
        t = tb()
        nx, nz = 10, 10
        vs = []
        for j in range(nz + 1):
            row = []
            v = j / nz
            zz = z - 0.03 - (z - 0.05) * v
            gather = 1.0 - 0.6 * math.exp(-((v - 0.55) / 0.18) ** 2)  # tied back at 55%
            for i in range(nx + 1):
                u = i / nx
                x = sx * (W / 2 - (W / 2 - 0.05) * u * gather)  # u=0 outer edge, inner edge pulled out at the tie
                y = -0.12 + 0.05 * math.sin(u * math.pi * 5)
                row.append(t.verts.new((x, y, zz)))
            vs.append(row)
        for j in range(nz):
            for i in range(nx):
                t.faces.new((vs[j][i], vs[j + 1][i], vs[j + 1][i + 1], vs[j][i + 1]))
        bmesh.ops.recalc_face_normals(t, faces=t.faces)
        bmesh.ops.solidify(t, geom=list(t.faces), thickness=0.012)
        k.put(t, "BH_ClothRed", tint=0.8, smooth=40)
        k.put(torus(0.07, 0.012, 8, 3), "BH_Gold", M=TRS(sx * (W / 2 - 0.2), -0.12, z - 0.55 * (z - 0.05), 0, 90, 0), tint=0.8)
    return dict(recenter=False)
