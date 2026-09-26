"""Crypt, temple and landmark pieces: statues, sarcophagus, altar, gravestones, teleporter dais (intact + destroyed),
corrupted obelisk, ritual circle, bridges, ruined watchtower, temple facade."""
import math

import bmesh
from mathutils import Vector

from kit import *  # noqa
from masonry import *  # noqa
from registry import asset
from assets_props import plank, sword, rivet, xform, flame_tip, skull


def carved_block(k, sx, sy, sz, M, mat="BH_Stone", tint=(0.8, 0.95), chips=2, trim=True):
    r = k.r
    t = box(sx, sy, sz, bev=0.03)
    chip(t, r, r.randint(0, chips), 0.05)
    jitter(t, r, 0.004)
    k.put(t, mat, M=M @ T(0, 0, sz / 2), tint=r.uniform(*tint))
    if trim:
        for z in (0.06, sz - 0.06):
            k.put(box(sx + 0.05, sy + 0.05, 0.08, bev=0.02), mat, M=M @ T(0, 0, z), tint=r.uniform(*tint) * 0.9)


def knight_figure(k, M, mat="BH_Stone", tint=0.95, parts=None):
    """3 m armoured figure (without plinth) holding a sword point-down in front. parts: optional set of part names
    to include (legs, torso, head, arms, cape, sword)."""
    r = k.r
    p = parts or {"legs", "torso", "head", "arms", "cape", "sword"}
    if "legs" in p:
        for sx in (-1, 1):
            k.put(tube([(sx * 0.2, 0, 0.0), (sx * 0.2, 0.02, 0.6), (sx * 0.18, 0, 1.25)], [0.16, 0.14, 0.17], 10), mat,
                  M=M, tint=tint * 0.9, smooth=35)
            k.put(box(0.3, 0.42, 0.14, bev=0.04), mat, M=M @ T(sx * 0.2, -0.06, 0.07), tint=tint * 0.85)
            k.put(ico(0.13, 1), mat, M=M @ TRS(sx * 0.2, -0.05, 0.65, s=(1, 1.1, 0.8)), tint=tint)
    if "torso" in p:
        k.put(lathe([(0.34, 1.2), (0.4, 1.45), (0.36, 1.7), (0.42, 2.0), (0.46, 2.2), (0.3, 2.35), (0.14, 2.42)], 12),
              mat, M=M @ S(1, 0.72, 1), tint=tint, smooth=35)
        k.put(torus(0.37, 0.05, 16, 5), mat, M=M @ T(0, 0, 1.45) @ S(1, 0.72, 1), tint=tint * 0.8)
        for sx in (-1, 1):  # pauldrons
            k.put(ico(0.24, 2), mat, M=M @ TRS(sx * 0.48, 0, 2.18, 0, sx * 20, 0, s=(1, 1, 0.7)), tint=tint, smooth=45)
    if "head" in p:
        k.put(lathe([(0.0, 2.42), (0.16, 2.44), (0.19, 2.6), (0.18, 2.78), (0.1, 2.9), (0.0, 2.93)], 12), mat, M=M, tint=tint,
              smooth=45)
        k.put(box(0.3, 0.05, 0.03), "BH_StoneDark", M=M @ T(0, -0.18, 2.66), tint=0.15)
        k.put(box(0.04, 0.3, 0.2, bev=0.01), mat, M=M @ T(0, 0, 2.95), tint=tint)
    if "arms" in p:
        for sx in (-1, 1):
            k.put(tube([(sx * 0.5, 0, 2.1), (sx * 0.46, -0.1, 1.7), (sx * 0.12, -0.36, 1.55)], [0.11, 0.1, 0.09], 8), mat,
                  M=M, tint=tint * 0.95, smooth=35)
        k.put(ico(0.12, 1), mat, M=M @ T(0, -0.38, 1.56), tint=tint)
    if "cape" in p:
        t = box(0.9, 0.06, 2.1, bev=0.0)
        subdiv(t, 4)
        for v in t.verts:
            v.co.y += 0.08 * math.sin(v.co.x * 9.0) * (1.05 - v.co.z / 2.1)
            v.co.x *= 1.0 + (1.05 - v.co.z) * 0.18
        k.put(t, mat, M=M @ TRS(0, 0.3, 1.2, -6, 0, 0), tint=tint * 0.75, smooth=40)
    if "sword" in p:
        k.put(box(0.12, 0.03, 1.4, bev=0.01), mat, M=M @ T(0, -0.4, 0.75), tint=tint)
        k.put(box(0.55, 0.08, 0.08, bev=0.02), mat, M=M @ T(0, -0.4, 1.47), tint=tint)
        k.put(cyl(0.035, 0.28, 8), mat, M=M @ T(0, -0.4, 1.5), tint=tint * 0.9)
        k.put(ico(0.07, 1), mat, M=M @ T(0, -0.4, 1.8), tint=tint)


def plinth_block(k, w, h, M=None, mat="BH_Stone"):
    M = M or T()
    carved_block(k, w + 0.3, w + 0.3, 0.25, M, mat, trim=False)
    carved_block(k, w, w, h - 0.25, M @ T(0, 0, 0.25), mat)


@asset("statue_knight", "crypt")
def statue_knight(k):
    plinth_block(k, 1.4, 1.0)
    knight_figure(k, T(0, 0, 1.0))
    k.put(box(0.6, 0.03, 0.2), "BH_StoneDark", M=T(0, -0.71, 0.6), tint=0.25)  # inscription panel
    k.col_box(1.7, 1.7, 4.0, T(0, 0, 2.0))
    return dict(recenter=True, damp=0.35, damp_h=1.2)


@asset("statue_collapsed", "crypt")
def statue_collapsed(k):
    r = k.r
    plinth_block(k, 1.4, 1.0)
    # broken leg stumps on the plinth
    for sx in (-1, 1):
        t = tube([(sx * 0.2, 0, 0), (sx * 0.2, 0.02, 0.5 + sx * 0.15)], [0.16, 0.15], 10)
        slice_plane(t, (0, 0, 0.35 + sx * 0.1), (0.3 * sx, 0.2, 1))
        k.put(t, "BH_Stone", M=T(0, 0, 1.0), tint=0.9, smooth=35)
    # fallen torso+head lying on the ground, rotated
    knight_figure(k, T(2.0, 0.5, 0.42) @ R(0, 88, 25) @ T(0, 0, -1.8), parts={"torso", "arms", "cape"}, tint=0.85)
    knight_figure(k, T(3.3, -0.9, 0.17) @ R(80, 0, 150) @ T(0, 0, -2.67), parts={"head"}, tint=0.8)
    for i in range(3):  # broken sword pieces
        k.put(box(0.12, 0.03, 0.45, bev=0.01), "BH_Stone", M=TRS(-1.2 + i * 0.5, -1.0 - i * 0.2, 0.03, 90, 0,
                                                                   r.uniform(0, 180)), tint=0.85)
    for i in range(14):
        a = r.uniform(0, math.tau)
        d = r.uniform(0.9, 2.4)
        t = rock(r, (r.uniform(0.1, 0.3),) * 3, cuts=5, subd=1, seed_off=i)
        k.put(t, "BH_Stone", M=TRS(math.cos(a) * d, math.sin(a) * d, 0, 0, 0, r.uniform(0, 360)), tint=r.uniform(0.6, 0.9))
    k.col_box(1.7, 1.7, 1.5, T(0, 0, 0.75))
    k.col_box(2.4, 1.2, 0.9, T(2.2, 0.4, 0.45) @ R(0, 0, 25))
    return dict(recenter=False, damp=0.3, damp_h=1.0)


@asset("altar", "crypt")
def altar(k):
    r = k.r
    carved_block(k, 2.4, 1.3, 0.2, T(), trim=False)
    carved_block(k, 2.0, 1.0, 0.85, T(0, 0, 0.2))
    t = box(2.3, 1.2, 0.14, bev=0.03)
    chip(t, r, 3, 0.05)
    k.put(t, "BH_Stone", M=T(0, 0, 1.12), tint=1.0)
    for sx in (-1, 0, 1):  # carved relief panels on the front
        k.put(box(0.45, 0.03, 0.5, bev=0.01), "BH_StoneDark", M=T(sx * 0.62, -0.51, 0.62), tint=0.35)
        k.put(cyl(0.12, 0.035, 12), "BH_Stone", M=TRS(sx * 0.62, -0.53, 0.62, 90, 0, 0), tint=0.9)
    cloth = box(0.5, 1.28, 0.012)
    subdiv(cloth, 3)
    for v in cloth.verts:
        if abs(v.co.y) > 0.58:
            v.co.z -= 0.35
            v.co.y = math.copysign(0.62, v.co.y)
    k.put(cloth, "BH_ClothRed", M=T(0, 0, 1.2), tint=0.8)
    k.put(box(0.54, 0.02, 0.05), "BH_Gold", M=T(0, -0.63, 0.86), tint=0.7)
    for x in (-0.85, -0.65, 0.7, 0.9):
        h = r.uniform(0.12, 0.3)
        k.put(cyl(0.035, h, 8), "BH_Candle", M=T(x, r.uniform(-0.3, 0.3), 1.19))
    k.put(cyl(0.18, 0.05, 12, r2=0.14), "BH_Gold", M=T(0, 0.1, 1.2), tint=0.8)  # offering bowl
    k.sockets.append(("light", (0, 0, 1.7)))
    k.col_box(2.4, 1.3, 1.2, T(0, 0, 0.6))
    return dict(recenter=True, damp=0.3)


@asset("sarcophagus", "crypt")
def sarcophagus(k):
    r = k.r
    L, W, H = 2.4, 1.1, 0.9
    carved_block(k, L, W, H, T())
    for sx in range(-2, 3):  # side niches
        for sy in (-1, 1):
            k.put(box(0.3, 0.03, 0.45, bev=0.01), "BH_StoneDark", M=T(sx * 0.42, sy * (W / 2 + 0.005), 0.45), tint=0.3)
    lid = box(L + 0.1, W + 0.1, 0.16, bev=0.04)
    chip(lid, r, 2, 0.06)
    k.put(lid, "BH_Stone", M=TRS(0.12, 0.05, H + 0.08, 0, 0, 3), tint=0.95)
    # effigy on the lid: lying figure
    ef = T(0.12, 0.05, H + 0.16) @ R(0, 0, 3)
    k.put(lathe([(0.0, 0.0), (0.2, 0.05), (0.26, 0.4), (0.22, 1.2), (0.28, 1.5), (0.15, 1.65), (0.0, 1.7)], 10),
          "BH_Stone", M=ef @ TRS(-0.9, 0, 0.1, 0, 90, 0) @ S(1, 1.2, 1) @ S(0.55, 1, 1), tint=1.0, smooth=35)
    k.put(ico(0.14, 2), "BH_Stone", M=ef @ T(0.95, 0, 0.14), tint=1.0, smooth=45)
    k.put(box(1.1, 0.06, 0.04, bev=0.01), "BH_Stone", M=ef @ T(0.0, 0, 0.26), tint=0.9)  # sword on chest
    k.put(box(0.05, 0.25, 0.04, bev=0.01), "BH_Stone", M=ef @ T(0.45, 0, 0.28), tint=0.9)
    k.col_box(L + 0.2, W + 0.2, H + 0.4, T(0, 0, (H + 0.4) / 2))
    return dict(recenter=True, damp=0.35)


@asset("gravestone_a", "crypt")
def gravestone_a(k):
    r = k.r
    pts = [(-0.35, 0.0), (0.35, 0.0), (0.35, 0.8)] + [(math.cos(a) * 0.35, 0.8 + math.sin(a) * 0.3)
                                                    for a in [math.pi * i / 8 for i in range(1, 8)]] + [(-0.35, 0.8)]
    t = prism(pts, 0.14, bev=0.02)
    chip(t, r, 3, 0.06)
    jitter(t, r, 0.006)
    k.put(t, "BH_Stone", M=R(r.uniform(-6, 6), r.uniform(-8, 8), 0), tint=0.8)
    k.put(box(0.4, 0.02, 0.3), "BH_StoneDark", M=T(0, -0.075, 0.6), tint=0.3)
    k.put(box(0.8, 0.4, 0.1, bev=0.02), "BH_Dirt", M=T(0, -0.1, 0.0), tint=0.5)
    k.col_box(0.7, 0.2, 1.1, T(0, 0, 0.55))
    return dict(recenter=True, damp=0.4)


@asset("gravestone_b", "crypt")
def gravestone_b(k):
    r = k.r
    lean = R(r.uniform(4, 10), r.uniform(-6, 6), 0)
    t = box(0.18, 0.14, 1.3, bev=0.02)
    chip(t, r, 2, 0.04)
    k.put(t, "BH_Stone", M=lean @ T(0, 0, 0.65), tint=0.8)
    t = box(0.65, 0.14, 0.18, bev=0.02)
    chip(t, r, 2, 0.04)
    k.put(t, "BH_Stone", M=lean @ T(0, 0, 0.95), tint=0.8)
    k.put(torus(0.18, 0.03, 14, 4), "BH_Stone", M=lean @ TRS(0, 0, 0.95, 90, 0, 0), tint=0.75)
    k.put(box(0.5, 0.35, 0.15, bev=0.03), "BH_Stone", M=T(0, 0, 0.05), tint=0.6)
    k.col_box(0.6, 0.3, 1.3, T(0, 0, 0.65))
    return dict(recenter=True, damp=0.4)


def _rune_ring(k, R_, z, n_glyph, mat="BH_Rune", tint=1.0, gaps=0):
    r = k.r
    k.put(torus(R_, 0.025, 48, 4), mat, M=T(0, 0, z) @ S(1, 1, 0.3), tint=tint, uvoff=False)
    for i in range(n_glyph):
        if gaps and r.random() < gaps:
            continue
        a = math.tau * i / n_glyph
        g = r.randint(0, 2)
        M = TRS(math.cos(a) * (R_ + 0.18), math.sin(a) * (R_ + 0.18), z, 0, 0, math.degrees(a))
        k.put(box(0.03, 0.2, 0.012), mat, M=M, tint=tint, uvoff=False)
        if g == 0:
            k.put(box(0.12, 0.03, 0.012), mat, M=M @ T(0.03, 0.05, 0), tint=tint, uvoff=False)
        elif g == 1:
            k.put(box(0.1, 0.03, 0.012), mat, M=M @ TRS(0.03, -0.04, 0, 0, 0, 40), tint=tint, uvoff=False)
        else:
            k.put(torus(0.05, 0.012, 8, 3), mat, M=M @ T(0.05, 0.0, 0), tint=tint, uvoff=False)


def _dais(k, broken=False):
    r = k.r
    tiers = ((2.1, 0.0, 0.25), (1.75, 0.25, 0.2))
    for (R_, z0, h) in tiers:
        n = 16
        for i in range(n):
            if broken and i in (3, 4, 11):
                continue
            a0, a1 = math.tau * i / n + 0.006, math.tau * (i + 1) / n - 0.006
            c = [(math.cos(a0) * (R_ - 0.45), math.sin(a0) * (R_ - 0.45), z0), (math.cos(a0) * R_, math.sin(a0) * R_, z0),
                 (math.cos(a1) * R_, math.sin(a1) * R_, z0), (math.cos(a1) * (R_ - 0.45), math.sin(a1) * (R_ - 0.45), z0)]
            c = c[::-1] + [(x, y, z0 + h - (r.uniform(0, 0.06) if broken else 0)) for (x, y, _) in c[::-1]]
            t = hexa(c, 0.02)
            chip(t, r, r.randint(0, 2 if broken else 1), 0.05)
            k.put(t, "BH_Stone", tint=r.uniform(0.75, 0.95))
    core = cyl(1.32, 0.45, 24)
    k.put(core, "BH_StoneDark", tint=0.5)
    slab_floor(k, 2.0, 2.0, 0.46, th=0.06, crack_p=0.3 if broken else 0.1, mat="BH_Stone", missing=0.15 if broken else 0.0)


@asset("teleporter_platform", "crypt")
def teleporter_platform(k):
    r = k.r
    _dais(k)
    _rune_ring(k, 1.35, 0.46, 18)
    _rune_ring(k, 0.75, 0.47, 10)
    k.put(cyl(0.22, 0.02, 16), "BH_Rune", M=T(0, 0, 0.465), uvoff=False)
    for i in range(3):
        a = math.tau * i / 3 + math.pi / 2
        x, y = math.cos(a) * 1.75, math.sin(a) * 1.75
        M = TRS(x, y, 0.45, 0, 0, math.degrees(a) + 90)
        t = box(0.55, 0.4, 2.4, bev=0.04)
        bmesh.ops.subdivide_edges(t, edges=[e for e in t.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1.0], cuts=3)
        taper_z(t, -1.2, 1.2, 1.0, 0.75)
        chip(t, r, 3, 0.07)
        ndisp(t, 2.0, 0.03, k.noff + Vector((i, 0, 0)))
        k.put(t, "BH_Stone", M=M @ T(0, 0, 1.2), tint=0.85, smooth=None)
        for z in (0.6, 1.1, 1.6, 2.0):  # rune column facing the centre
            k.put(box(0.16, 0.02, 0.1), "BH_Rune", M=M @ T(0, -0.205, z), uvoff=False)
        k.put(box(0.02, 0.02, 1.6), "BH_Rune", M=M @ T(0, -0.2, 1.3), uvoff=False)
        # small cap stone
        k.put(box(0.5, 0.45, 0.14, bev=0.03), "BH_Stone", M=M @ T(0, 0, 2.47), tint=0.95)
    k.sockets.append(("center", (0, 0, 0.5)))
    # sloped rim so a character body can walk up onto the dais (a vertical 0.47 m edge cannot be stepped)
    k.col_mesh(cyl(2.45, 0.47, 16, r2=1.4))
    for i in range(3):
        a = math.tau * i / 3 + math.pi / 2
        k.col_box(0.55, 0.4, 2.4, TRS(math.cos(a) * 1.75, math.sin(a) * 1.75, 1.65, 0, 0, math.degrees(a) + 90))
    return dict(recenter=False, damp=0.25)


@asset("teleporter_destroyed", "crypt")
def teleporter_destroyed(k):
    r = k.r
    _dais(k, broken=True)
    _rune_ring(k, 1.35, 0.46, 18, mat="BH_StoneDark", tint=0.15, gaps=0.4)
    k.put(cyl(0.22, 0.02, 16), "BH_Corruption", M=T(0, 0, 0.465), tint=0.6, uvoff=False)
    for i, (standing, h) in enumerate(((True, 1.1), (False, 2.4), (False, 1.6))):
        a = math.tau * i / 3 + math.pi / 2
        x, y = math.cos(a) * 1.75, math.sin(a) * 1.75
        t = box(0.55, 0.4, h, bev=0.04)
        chip(t, r, 4, 0.08)
        if standing:
            slice_plane(t, (0, 0, h / 2 - 0.25), (0.4, 0.3, 1))
            k.put(t, "BH_Stone", M=TRS(x, y, 0.45 + h / 2, 0, 0, math.degrees(a) + 90), tint=0.7)
        else:
            d = 2.9 + i * 0.3
            k.put(t, "BH_Stone", M=TRS(math.cos(a) * d, math.sin(a) * d, 0.2, 90, 0, math.degrees(a) + 60 * i), tint=0.7)
    for i in range(18):
        a = r.uniform(0, math.tau)
        d = r.uniform(1.2, 3.3)
        t = rock(r, (r.uniform(0.1, 0.35),) * 3, cuts=5, subd=1, seed_off=i)
        k.put(t, "BH_Stone", M=TRS(math.cos(a) * d, math.sin(a) * d, 0.0 if d > 2.1 else 0.45, 0, 0, r.uniform(0, 360)),
              tint=r.uniform(0.5, 0.8))
    for i in range(5):  # corruption crystals growing from the cracks
        a = r.uniform(0, math.tau)
        d = r.uniform(0.3, 1.2)
        t = cyl(0.07, r.uniform(0.3, 0.7), 5, r2=0.0)
        k.put(t, "BH_Corruption", M=TRS(math.cos(a) * d, math.sin(a) * d, 0.42, r.uniform(-25, 25), r.uniform(-25, 25), 0),
              tint=0.7)
    k.sockets.append(("center", (0, 0, 0.5)))
    k.col_mesh(cyl(2.45, 0.47, 16, r2=1.4))
    return dict(recenter=False, damp=0.3)


@asset("obelisk_corrupted", "crypt")
def obelisk_corrupted(k):
    r = k.r
    carved_block(k, 1.8, 1.8, 0.5, T(), trim=True)
    t = box(0.9, 0.9, 5.0)
    bmesh.ops.subdivide_edges(t, edges=[e for e in t.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1.0], cuts=6)
    taper_z(t, -2.5, 2.5, 1.0, 0.55)
    chip(t, r, 4, 0.1)
    ndisp(t, 1.5, 0.04, k.noff)
    k.put(t, "BH_StoneDark", M=TRS(0, 0, 3.0, 2, -1.5, 8), tint=0.55)
    k.put(cyl(0.36, 0.5, 4, r2=0.0), "BH_StoneDark", M=TRS(0, 0, 5.45, 2, -1.5, 53), tint=0.5)
    # glowing veins climbing the faces
    for face in range(4):
        Mf = TRS(0, 0, 0.5, 2, -1.5, 8 + 90 * face)
        pts = [(r.uniform(-0.1, 0.1), -0.43, 0.2)]
        for i in range(8):
            z = pts[-1][2] + r.uniform(0.3, 0.6)
            w = 0.43 - 0.2 * z / 5.0
            pts.append((max(-w + 0.05, min(w - 0.05, pts[-1][0] + r.uniform(-0.2, 0.2))), -w - 0.005, z))
        k.put(tube(pts, 0.025, 4), "BH_Corruption", M=Mf, uvoff=False)
    for i in range(9):
        a = r.uniform(0, math.tau)
        d = r.uniform(0.9, 1.6)
        h = r.uniform(0.4, 1.3)
        k.put(cyl(0.12, h, 5, r2=0.0), "BH_Corruption", M=TRS(math.cos(a) * d, math.sin(a) * d, 0.0, r.uniform(-30, 30),
                                                             r.uniform(-30, 30), 0), tint=0.8)
    k.sockets.append(("light", (0, 0, 2.5)))
    k.col_box(1.8, 1.8, 5.5, T(0, 0, 2.75))
    return dict(recenter=False, damp=0.3)


@asset("ritual_circle", "crypt", col=False)
def ritual_circle(k):
    r = k.r
    k.put(cyl(3.0, 0.03, 48), "BH_StoneDark", tint=0.4)
    _rune_ring(k, 2.6, 0.035, 28)
    _rune_ring(k, 1.4, 0.035, 12)
    for i in range(5):  # pentagram-like star of rune lines
        a0 = math.tau * i / 5 + math.pi / 2
        a1 = math.tau * ((i + 2) % 5) / 5 + math.pi / 2
        p0 = Vector((math.cos(a0) * 2.6, math.sin(a0) * 2.6, 0.04))
        p1 = Vector((math.cos(a1) * 2.6, math.sin(a1) * 2.6, 0.04))
        k.put(tube([p0, p1], 0.02, 4), "BH_Rune", uvoff=False)
        k.put(cyl(0.05, r.uniform(0.1, 0.25), 8), "BH_Candle", M=T(p0.x * 1.12, p0.y * 1.12, 0.03))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# bridges and landmarks
@asset("bridge_stone", "landmarks")
def bridge_stone(k):
    """12 m span along X, deck top at z=0 (origin), 3.6 m wide, arch + piers reach down to z=-6."""
    r = k.r
    L, W = 12.0, 3.6
    slab_floor(k, L, W - 0.6, 0.0, th=0.12, mat="BH_Stone", crack_p=0.2)
    k.put(box(L, W - 0.6, 0.5), "BH_StoneDark", M=T(0, 0, -0.37), tint=0.4)
    for sy in (-1, 1):
        M = T(0, sy * (W / 2 - 0.15), 0)
        masonry(k, -L / 2, L / 2, -0.25, 0.75, 0.3, M=M, quoin="both", course=(0.3, 0.4))
        capstones(k, -L / 2, L / 2, 0.75, 0.3, 0.14, M=M)
        # spandrel under the deck + arch ring
        M2 = T(0, sy * (W / 2 - 0.4), 0)
        arch_ring(k, 0, -5.5, 4.2, 5.0, 0.8, n=15, mat="BH_Stone", alt_mat="BH_StoneDark", M=M2)

        def prof(x):
            return -0.25
        masonry(k, -L / 2, L / 2, -6.0, -0.25, 0.8, M=M2, cuts=(CircleCut(0, -5.5, 5.0),), course=(0.45, 0.6))
    for sx in (-1, 1):
        masonry(k, -W / 2, W / 2, -6.0, -0.25, 1.4, M=T(sx * (L / 2 - 0.7), 0, 0) @ R(0, 0, 90), quoin="both")
    k.col_box(L, W, 0.5, T(0, 0, -0.25))
    for sy in (-1, 1):
        k.col_box(L, 0.3, 1.0, T(0, sy * (W / 2 - 0.15), 0.25))
    return dict(recenter=False, damp=0.0)


@asset("bridge_wood", "landmarks")
def bridge_wood(k):
    """8 m rope-and-plank bridge along X, deck top at z=0, trestles down to z=-3."""
    r = k.r
    L, W = 8.0, 2.4
    n = 30
    for i in range(n):
        if i in (9, 21):
            continue
        x = -L / 2 + L * (i + 0.5) / n
        plank(k, W, L / n - 0.03, 0.06, TRS(x, 0, -0.03 - 0.12 * math.sin(math.pi * (i + 0.5) / n), 0, 0, 90 + r.uniform(-2, 2)),
              warp=0.0)
    for sy in (-1, 1):
        pts = [(-L / 2 + L * i / 12, sy * (W / 2 - 0.1), -0.12 - 0.12 * math.sin(math.pi * i / 12)) for i in range(13)]
        k.put(tube(pts, 0.07, 6), "BH_WoodDark", tint=0.6, smooth=40)
        rail = [(p[0], p[1], p[2] + 1.0) for p in pts]
        k.put(tube(rail, 0.025, 5), "BH_Cloth", tint=0.5, smooth=40)
        for i in range(0, 13, 2):
            p = pts[i]
            k.put(box(0.09, 0.09, 1.1), "BH_WoodDark", M=T(p[0], p[1], p[2] + 0.5), tint=0.7)
    for x in (-L / 2 + 0.3, L / 2 - 0.3, 0.0):
        for sy in (-1, 1):
            t = tube([(x, sy * (W / 2 - 0.1), -3.0), (x, sy * (W / 2 - 0.1), -0.1)], 0.12, 8)
            k.put(t, "BH_WoodDark", tint=0.55, smooth=40)
        plank(k, W, 0.14, 0.14, TRS(x, 0, -0.35, 0, 0, 90), mat="BH_WoodDark")
        plank(k, math.hypot(W, 2.4), 0.1, 0.08, TRS(x, 0, -1.6, 45, 0, 90) @ R(0, 0, 0), mat="BH_WoodDark")
    k.col_box(L, W, 0.3, T(0, 0, -0.15))
    for sy in (-1, 1):
        k.col_box(L, 0.1, 1.0, T(0, sy * (W / 2 - 0.1), 0.4))
    return dict(recenter=False)


@asset("ruin_tower", "landmarks")
def ruin_tower(k):
    """Collapsed round watchtower, ~12 m at its tallest, 7 m diameter, doorway toward -Y."""
    r = k.r
    Rr, th, n = 3.4, 0.9, 18
    chord = 2 * Rr * math.sin(math.pi / n)
    for i in range(n):
        a = math.tau * (i + 0.5) / n
        # broken silhouette: tall on the back (+Y), collapsed toward the front-right
        h = 5.0 + 7.0 * (0.5 + 0.5 * math.cos(a - math.pi * 0.55)) ** 1.5 + r.uniform(-0.6, 0.6)
        h0 = h
        M = TRS(math.cos(a) * Rr, math.sin(a) * Rr, 0, 0, 0, math.degrees(a) + 90)
        cuts = ()
        if abs(math.degrees(a) - 270) < 12:  # doorway
            cuts = (RectCut(-0.9, 0.9, 0.0, 2.4),)
        elif i % 5 == 2:  # arrow slits
            cuts = (RectCut(-0.15, 0.15, h * 0.55, h * 0.55 + 1.0),)

        def prof(x, h0=h0, i=i):
            return h0 + 0.8 * math.sin(x * 2.1 + i)
        masonry(k, -chord / 2 - 0.02, chord / 2 + 0.02, 0, h + 1.0, th, M=M, top_profile=prof, cuts=cuts,
                course=(0.4, 0.55), blen=(0.5, 0.9))
        if h > 10.5:
            for z in (h - 0.6,):
                k.put(box(chord, th + 0.2, 0.25, bev=0.03), "BH_Stone", M=M @ T(0, 0, z), tint=0.9)
    for i in range(4):  # interior floor beams, some fallen
        z = 4.2
        if i < 2:
            k.put(box(0.3, 2 * Rr - 0.4, 0.35, bev=0.03), "BH_WoodDark", M=TRS(-1.5 + i * 1.3, 0.8, z, 0, 0, 0), tint=0.5)
        else:
            k.put(box(0.3, 3.5, 0.35, bev=0.03), "BH_WoodDark", M=TRS(-0.5 + i * 0.6, -1.2, 1.2, 50, 10, 20), tint=0.4)
    for i in range(22):  # collapsed stones outside the broken side
        a = r.uniform(-1.3, 0.2)
        d = r.uniform(Rr + 0.8, Rr + 4.5)
        s = r.uniform(0.3, 0.7)
        t = rock(r, (s, s * 0.8, s * 0.6), cuts=6, subd=1, seed_off=i)
        k.put(t, "BH_StoneDark", M=TRS(math.cos(a) * d, math.sin(a) * d, 0, 0, 0, r.uniform(0, 360)), tint=r.uniform(0.5, 0.8))
    k.put(cyl(Rr - 0.4, 0.1, 18), "BH_Dirt", tint=0.5)
    for i in range(n):
        a = math.tau * (i + 0.5) / n
        if abs(math.degrees(a) - 270) < 12:
            continue
        k.col_box(chord, th, 6.0, TRS(math.cos(a) * Rr, math.sin(a) * Rr, 3.0, 0, 0, math.degrees(a) + 90))
    return dict(recenter=False, damp=0.35, damp_h=2.0)


@asset("temple_facade", "landmarks")
def temple_facade(k):
    """Ruined temple front ~14 m wide facing -Y: stepped base, 6 columns, entablature, pediment, dark doorway."""
    r = k.r
    W = 14.0
    for i in range(4):  # four 0.25 m steps, 0.5 m treads, rising to the portico at y=-3.25
        y0 = -5.25 + 0.5 * i
        depth = -3.25 - y0
        slab_floor(k, W - i * 0.4, depth, 0.25 * (i + 1), th=0.25, M=T(0, (y0 - 3.25) / 2, 0), lens=(0.8, 1.4),
                   rows=(0.5, 0.5))
    k.put(box(W, 4.5, 1.0), "BH_StoneDark", M=T(0, -1.0, 0.5), tint=0.4)
    slab_floor(k, W - 1.2, 4.2, 1.0, th=0.1, lens=(0.8, 1.4))
    # back wall with doorway
    masonry(k, -W / 2 + 0.6, W / 2 - 0.6, 1.0, 8.2, 1.0, M=T(0, 0.8, 0), cuts=(RectCut(-1.4, 1.4, 1.0, 4.6),
                                                                              CircleCut(0, 4.6, 1.4)), quoin="both")
    arch_ring(k, 0, 4.6, 1.4, 2.0, 1.0, n=11, M=T(0, 0.8, 0), alt_mat="BH_StoneDark")
    cols = [-5.5, -3.3, -1.1, 1.1, 3.3, 5.5]
    for ci, x in enumerate(cols):
        broken = ci == 5
        h = 3.8 if broken else 6.4
        t = lathe([(0.55, 0.0), (0.55, 0.3), (0.48, 0.35), (0.45, 0.4), (0.42, h), ], 14)
        # fluting-ish ridges via noise
        k.put(t, "BH_Stone", M=T(x, -2.4, 1.0), tint=r.uniform(0.85, 1.0), smooth=30)
        if broken:
            for i in range(3):
                k.put(cyl(0.42, 0.9, 12), "BH_Stone", M=TRS(x + 1.4 + i * 0.95, -5.6 + i * 0.3, 0.42, 90, 0, 80 + i * 8),
                      tint=0.85)
        else:
            k.put(box(1.3, 1.3, 0.35, bev=0.04), "BH_Stone", M=T(x, -2.4, 1.0 + h + 0.17), tint=0.95)
    # entablature (missing over the broken column)
    k.put(box(W - 3.2, 1.6, 0.9, bev=0.04), "BH_Stone", M=T(-1.5, -2.2, 1.0 + 6.4 + 0.35 + 0.45), tint=0.9)
    capstones(k, -W / 2 + 0.3, W / 2 - 3.6, 8.6, 1.9, 0.25, M=T(0, -2.2, 0))
    ped = [(-W / 2 + 0.3, 0.0), (W / 2 - 3.6, 0.0), (W / 2 - 3.6, 1.2), (-0.5, 2.6), (-W / 2 + 0.3, 0.0)]
    t = prism([(-5.4, 0.0), (2.4, 0.0), (1.0, 1.2), (-1.5, 2.5)], 1.2, bev=0.04)
    chip(t, r, 3, 0.1)
    k.put(t, "BH_Stone", M=T(0, -2.1, 8.85), tint=0.85)
    k.put(cyl(0.6, 0.12, 16), "BH_Gold", M=TRS(-1.5, -2.72, 9.7, 90, 0, 0), tint=0.5)  # sun disc emblem
    k.put(torus(0.6, 0.06, 16, 4), "BH_Stone", M=TRS(-1.5, -2.75, 9.7, 90, 0, 0), tint=0.9)
    for i in range(16):
        a = r.uniform(0, math.pi)
        t = rock(r, (r.uniform(0.25, 0.6),) * 3, cuts=6, subd=1, seed_off=i)
        k.put(t, "BH_Stone", M=TRS(W / 2 - 1.0 + math.cos(a) * r.uniform(0.5, 3.0), -4.8 + math.sin(a) * r.uniform(0.3, 2.0),
                                   0.0, 0, 0, r.uniform(0, 360)), tint=r.uniform(0.6, 0.85))
    # walkable collision: a ramp over the four steps, the portico platform, and the back wall with a door gap
    ramp_len = math.hypot(2.0, 1.0)
    k.col_mesh(box(W - 1.6, ramp_len, 0.2), TRS(0, -4.25, 0.4, -math.degrees(math.atan2(1.0, 2.0)), 0, 0))
    k.col_box(W - 0.4, 4.5, 1.0, T(0, -1.0, 0.5))
    half = (W - 1.2) / 2 - 1.4
    for sx in (-1, 1):
        k.col_box(half, 1.0, 7.2, T(sx * (1.4 + half / 2), 0.8, 4.6))
    k.col_box(2.8, 1.0, 3.6, T(0, 0.8, 6.4))
    for x in cols[:5]:
        k.col_box(1.0, 1.0, 6.4, T(x, -2.4, 4.2))
    k.col_box(1.0, 1.0, 3.8, T(cols[5], -2.4, 2.9))
    return dict(recenter=False, damp=0.3, damp_h=2.0)


@asset("throne", "crypt")
def throne(k):
    """The Hollow Throne: a massive stone seat on a stepped base, tall cracked back with a corruption-veined sigil."""
    r = k.r
    carved_block(k, 3.6, 3.0, 0.4, T(), trim=False)
    carved_block(k, 3.0, 2.4, 0.35, T(0, 0.2, 0.4), trim=False)
    seat = box(2.0, 1.5, 0.7, bev=0.05)
    chip(seat, r, 3, 0.06)
    k.put(seat, "BH_StoneDark", M=T(0, 0.3, 0.75 + 0.35), tint=0.55)
    for sx in (-1, 1):  # armrests with skull finials
        t = box(0.45, 1.6, 0.6, bev=0.05)
        chip(t, r, 2, 0.05)
        k.put(t, "BH_StoneDark", M=T(sx * 1.2, 0.3, 1.45 + 0.3), tint=0.5)
        k.put(ico(0.2, 2), "BH_Bone", M=TRS(sx * 1.2, -0.35, 2.15, s=(1, 1.15, 1)), tint=0.8, smooth=45)
    back = prism([(-1.3, 0.0), (1.3, 0.0), (1.1, 3.2), (0.55, 3.6), (0.0, 4.4), (-0.55, 3.6), (-1.1, 3.2)], 0.5, bev=0.04)
    chip(back, r, 4, 0.1)
    k.put(back, "BH_StoneDark", M=T(0, 1.0, 1.1), tint=0.5)
    for sx in (-1, 1):  # spikes crowning the back
        k.put(cyl(0.12, 1.4, 5, r2=0.0), "BH_Iron", M=TRS(sx * 0.9, 1.0, 4.2, 0, sx * -14, 0), tint=0.7)
    k.put(cyl(0.14, 1.8, 5, r2=0.0), "BH_Iron", M=T(0, 1.0, 5.4), tint=0.7)
    k.put(torus(0.55, 0.06, 20, 5), "BH_Corruption", M=TRS(0, 0.73, 3.0, 90, 0, 0), tint=0.9)
    k.put(cyl(0.18, 0.05, 12), "BH_Corruption", M=TRS(0, 0.72, 3.0, 90, 0, 0), tint=1.0)
    for i in range(6):  # veins spreading from the sigil
        a = math.tau * i / 6 + 0.3
        pts = [(math.cos(a) * 0.6, 0.72, 3.0 + math.sin(a) * 0.6)]
        for j in range(3):
            p = pts[-1]
            pts.append((p[0] + math.cos(a) * 0.3 + r.uniform(-0.1, 0.1), 0.72, p[2] + math.sin(a) * 0.3 + r.uniform(-0.1, 0.1)))
        k.put(tube(pts, 0.025, 4), "BH_Corruption", uvoff=False)
    k.sockets.append(("light", (0, -0.3, 3.0)))
    k.col_box(3.6, 3.0, 1.1, T(0, 0, 0.55))
    k.col_box(2.8, 0.6, 4.2, T(0, 1.0, 2.9))
    return dict(recenter=False, damp=0.3)
