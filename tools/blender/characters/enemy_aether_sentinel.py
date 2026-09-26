"""Aether Sentinel (ancient construct, builder A): a massive temple guardian of weathered stone and verdigris bronze.
Blocky torso segments float slightly apart (pelvis / abdomen / chest) held by a column of Aether light, bronze bands
around every block, a glowing cyan Aether core set in the chest, boulder pauldrons, pillar limbs with bronze joint
rings and stone fists. Faceless head: a stone block with a single glowing visor slit. Stone slab shield on the left
arm (bronze frame, Aether rune) and a bronze-headed maul in the right hand."""
import math
import numpy as np

import bh_mesh as M
from bh_body import Body, torso_loft, front_y, back_y, fist
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_hollow_soldier as HS
from enemy_hollow_soldier import P, rtube, ball, Scaled, add_weapon, dent

K = 2.0 / 1.8
PROPS = proportions(K)
PALETTE = "aether_sentinel"
PALETTE_COLORS = {
    "BH_Stone": ((0.27, 0.26, 0.23), 0.0, 0.88, None, 0.0, 1.0),
    "BH_Bronze": ((0.30, 0.26, 0.13), 0.9, 0.45, None, 0.0, 1.0),       # verdigris-dulled bronze
    "BH_DarkSteel": ((0.12, 0.17, 0.15), 0.8, 0.5, None, 0.0, 1.0),
    "BH_Wood": ((0.09, 0.06, 0.035), 0.0, 0.75, None, 0.0, 1.0),
    "BH_Shadow": ((0.03, 0.035, 0.045), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Aether": ((0.5, 0.95, 1.0), 0.0, 0.25, (0.4, 0.92, 1.0), 9.0, 1.0),
}
CLIPS = ["gs_1", "boss_slam", "cast_heavy"]


def finish_mesh(mesh_ob):
    HS.enable_weapon_deform(mesh_ob)


def block(rows, mat="BH_Stone", p=4.0, n=28, bev=0.01):
    V, F = torso_loft(rows, n=n, p=p, cap0=True, cap1=True)
    return M.bevel(P(V, F, mat, "block"), bev, 2, angle=40)


def band(rows, z, h, g, mat="BH_Bronze", p=4.0, n=20):
    from bh_body import torso_ring, interp_rows
    r = interp_rows(rows, z)
    loops = [torso_ring(z - h / 2, r[1] + g, r[2] + g, r[3] + g, 0.0, p, n),
             torso_ring(z + h / 2, r[1] + g, r[2] + g, r[3] + g, 0.0, p, n)]
    V, F = M.loft(loops, cap0=True, cap1=True)
    return P(V, F, mat, "band")


def aether_line(pts, r=0.006):
    return rtube(pts, r, "BH_Aether", n=4)


def stone_limb(body, b, prof, mat="BH_Stone"):
    return M.bevel(body.limb(b, prof, mat, n=14, p=3.2), 0.006, 2, angle=40)


def joint_ring(c, axis, r, w=0.03, mat="BH_Bronze"):
    axis = normalize(axis)
    V, F = M.tube([c - axis * w / 2, c + axis * w / 2], [(r, r), (r, r)], n=12, up=(0, 0, 1) if abs(axis[2]) < 0.9
                  else (0, -1, 0))
    return P(V, F, mat, "jring")


# --------------------------------------------------------------------------------------------------- weapons
def slab_shield():
    """Weapon-GLB space: handle at origin, face -Y, long axis Z."""
    parts = []
    yf = -0.08
    V, F = M.box(0.58, 0.075, 0.92, center=(0, yf + 0.0375, -0.06))
    slab = M.bevel(P(V, F, "BH_Stone", "slab"), 0.02, 2, angle=40)
    dent(slab, (0.22, yf, 0.33), (0, 1, -0.3), 0.03, 0.06)        # chipped corner
    parts.append(slab)
    for (sx, sz, cx, cz) in ((0.62, 0.05, 0, 0.4), (0.62, 0.05, 0, -0.52), (0.05, 0.96, 0.3, -0.06),
                             (0.05, 0.96, -0.3, -0.06)):
        V, F = M.box(sx, 0.09, sz, center=(cx, yf + 0.035, cz))
        parts.append(M.bevel(P(V, F, "BH_Bronze", "frame"), 0.008, 1))
    # rune: diamond ring + bars
    dia = [(0.0, 0.14), (-0.1, 0.0), (0.0, -0.14), (0.1, 0.0)]
    ring = [np.array((x, yf - 0.004, z - 0.04)) for x, z in dia + dia[:1]]
    parts.append(rtube(ring, 0.011, "BH_Aether", n=4, up=(0, -1, 0)))
    for z0, z1 in ((0.12, 0.34), (-0.2, -0.44)):
        parts.append(rtube([(0, yf - 0.004, z0 - 0.04 + 0.02 * np.sign(z0)), (0, yf - 0.004, z1)], 0.009, "BH_Aether",
                           n=4, up=(0, -1, 0)))
    V, F = M.tube([(-0.1, -0.03, 0.0), (-0.06, 0.025, 0.0), (0.06, 0.025, 0.0), (0.1, -0.03, 0.0)],
                  [(0.014, 0.04)] * 4, n=6, up=(0, 0, 1))
    parts.append(P(V, F, "BH_Bronze", "handle"))
    return parts


def maul():
    parts = []
    V, F = M.lathe([(0, -0.34), (0.03, -0.34), (0.032, -0.3), (0.024, -0.27), (0.024, 0.7), (0, 0.72)], 8)
    parts.append(P(V, F, "BH_Wood", "haft"))
    for z in (-0.2, 0.2, 0.55):
        V, F = M.lathe([(0, z - 0.02), (0.03, z - 0.02), (0.03, z + 0.02), (0, z + 0.02)], 8)
        parts.append(P(V, F, "BH_Bronze", "hband"))
    V, F = M.lathe([(0, -0.4), (0.04, -0.39), (0.045, -0.35), (0.03, -0.33), (0, -0.33)], 8)
    parts.append(P(V, F, "BH_Bronze", "pommel"))
    # head: long block across the haft (faces +-X), flared ends
    rings = []
    for x, s in ((-0.2, 0.1), (-0.17, 0.11), (-0.1, 0.085), (0.1, 0.085), (0.17, 0.11), (0.2, 0.1)):
        rings.append(np.array([(x, s * c, 0.78 + s * sn) for c, sn in ((1, 1), (-1, 1), (-1, -1), (1, -1))]))
    V, F = M.loft(rings)
    parts.append(M.bevel(P(V, F, "BH_Bronze", "maulhead"), 0.012, 1, angle=30))
    for sy in (1, -1):
        parts.append(rtube([(-0.1, sy * 0.087, 0.78), (0.1, sy * 0.087, 0.78)], 0.012, "BH_Aether", n=4))
    V, F = M.box(0.07, 0.07, 0.07, center=(0, 0, 0.9))
    parts.append(M.bevel(P(V, F, "BH_Bronze", "cap"), 0.01, 1))
    return parts


# --------------------------------------------------------------------------------------------------- body
CHEST = [(1.27, 0.19, 0.13, 0.12, 0.0), (1.34, 0.225, 0.15, 0.13, 0.0), (1.44, 0.24, 0.155, 0.135, 0.0),
         (1.51, 0.21, 0.13, 0.12, 0.0), (1.545, 0.13, 0.095, 0.1, 0.0)]
ABDO = [(1.1, 0.13, 0.1, 0.095, 0.0), (1.16, 0.145, 0.11, 0.1, 0.0), (1.23, 0.14, 0.105, 0.1, 0.0)]
PELV = [(0.88, 0.15, 0.1, 0.1, 0.0), (0.95, 0.185, 0.12, 0.12, 0.0), (1.02, 0.18, 0.115, 0.115, 0.0),
        (1.065, 0.15, 0.1, 0.1, 0.0)]
HEADB = [(1.625, 0.075, 0.085, 0.085, 0.0, -0.005), (1.68, 0.09, 0.1, 0.095, 0.0, -0.005),
         (1.78, 0.092, 0.1, 0.095, 0.0, 0.0), (1.83, 0.07, 0.08, 0.08, 0.0, 0.005)]


def build(real: Body):
    body = Scaled(real, K)
    add = body.add
    SPW = HS.SPINE_W
    # ---- aether spine: visible in the gaps between the floating blocks
    add(rtube([(0, 0.0, 0.95), (0, 0.0, 1.12), (0, 0.0, 1.3), (0, 0.0, 1.5)], 0.045, "BH_Aether", n=8), weights=SPW)
    add(rtube([(0, 0.0, 1.5), (0, 0.0, 1.66)], 0.035, "BH_Aether", n=8), weights=HS.NECK_W)

    # ---- torso blocks
    add(block(CHEST, bev=0.012), "chest")
    add(band(CHEST, 1.3, 0.035, 0.008), "chest")
    add(band(CHEST, 1.5, 0.03, 0.008), "chest")
    add(block(ABDO), "spine")
    add(band(ABDO, 1.165, 0.04, 0.008), "spine")
    add(block(PELV), "hips")
    add(band(PELV, 1.03, 0.04, 0.008), "hips")
    # loin plates (bronze) front/back, split per leg
    for sx in (1, -1):
        for fy, sgn in ((-1, 1), (1, -1)):
            V, F = M.box(0.13, 0.03, 0.2, center=(sx * 0.075, fy * 0.125, 0.8))
            lp = M.bevel(P(V, F, "BH_Bronze", "loin"), 0.008, 1)
            lp.rot(Rx(fy * 8), center=(0, fy * 0.12, 0.9))
            add(lp, weights=lambda V, sx=sx: [{"hips": 0.6, ("thigh.L" if sx > 0 else "thigh.R"): 0.4}] * len(V))
    # chest core: aether sphere in a bronze ring + radiating seams
    cz = 1.39
    cy = front_y(CHEST, 0, cz, p=4.0)
    add(ball((0, cy + 0.01, cz), 0.07, "BH_Aether", 12, 8, (1, 0.7, 1)), "chest")
    ring = [(0.085 * math.cos(a), cy - 0.012, cz + 0.085 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 17)]
    V, F = M.tube(ring, [(0.018, 0.018)] * len(ring), n=6, up=(0, -1, 0), cap0=False, cap1=False)
    add(P(V, F, "BH_Bronze", "corering"), "chest")
    for a in (30, 150, 210, 330):
        ra = math.radians(a)
        pts = []
        for t in np.linspace(0, 1, 4):
            rr = 0.1 + 0.1 * t
            x, z = rr * math.cos(ra), cz + rr * 0.8 * math.sin(ra)
            pts.append((x, front_y(CHEST, x, z, p=4.0) + 0.002, z))
        add(aether_line(pts, 0.007), "chest")

    # ---- head: faceless block with a visor slit
    add(block(HEADB, bev=0.01), "head")
    yv = front_y([h[:5] for h in HEADB], 0, 1.72, p=4.0)
    V, F = M.box(0.16, 0.03, 0.026, center=(0, yv + 0.01, 1.72))
    add(P(V, F, "BH_Shadow", "slit"), "head")
    V, F = M.box(0.14, 0.02, 0.014, center=(0, yv + 0.003, 1.72))
    add(P(V, F, "BH_Aether", "visor"), "head")
    add(band([h[:5] for h in HEADB], 1.765, 0.025, 0.006), "head")
    crest = [(0, -0.09, 1.8), (0, -0.03, 1.87), (0, 0.05, 1.885), (0, 0.12, 1.85), (0, 0.16, 1.76)]
    V, F = M.tube(crest, [(0.012, 0.03), (0.014, 0.045), (0.014, 0.045), (0.012, 0.035), (0.006, 0.02)], n=6,
                  up=(0, 0, 1), p=3.0)
    add(P(V, F, "BH_Bronze", "crest"), "head")
    V, F = M.lathe([(0.1, 1.53), (0.105, 1.56), (0.08, 1.62), (0.07, 1.62)], 12, cap=False)
    add(P(V, F, "BH_Bronze", "collar"), "neck")

    # ---- arms
    for sx, s in ((1, "L"), (-1, "R")):
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
        add(ball(sh, 0.075, "BH_Bronze", 10, 6), ua)
        add(stone_limb(body, ua, [(0.12, 0.065, 0.068), (0.5, 0.072, 0.075), (0.88, 0.064, 0.066)]), ua)
        add(ball(el, 0.06, "BH_Bronze", 10, 6), fa)
        add(stone_limb(body, fa, [(0.12, 0.066, 0.068), (0.55, 0.08, 0.082), (0.93, 0.084, 0.086)]), fa)
        add(joint_ring(el + (wr - el) * 0.62, wr - el, 0.088), fa)
        add(joint_ring(sh + (el - sh) * 0.55, el - sh, 0.078), ua)
        L = body.p["fore_len"]
        for dx in (-0.03, 0.03):   # aether seams on the back of the forearm
            add(aether_line(body.lpt(fa, [(dx, u * L, 0.083 + 0.004 * u) for u in np.linspace(0.15, 0.55, 4)]), 0.006), fa)
        for prt in fist(body, s, "BH_Bronze", "BH_Stone", gauntlet=True, scale=1.18):
            add(prt, ha)
        # boulder pauldron floating over the shoulder
        c = sh + np.array([sx * 0.03, 0.0, 0.07])
        V, F = M.sphere(0.13, 14, 8, center=(0, 0, 0), scale=(1.0, 1.05, 0.7))
        bp = P(V, F, "BH_Stone", "boulder")
        bp.warp(lambda v: (v[0] * (1 + 0.1 * math.sin(v[1] * 40)), v[1], v[2] * (1 + 0.15 * (v[0] * sx > 0))))
        bp.rot(Ry(-sx * 25)).move(c)
        add(M.bevel(bp, 0.008, 1, angle=35), ua)
        rim = [c + Ry(-sx * 25) @ np.array([0.13 * math.cos(a), 0.137 * math.sin(a), -0.02]) for a in
               np.linspace(0, 2 * math.pi, 17)]
        V, F = M.tube(rim, [(0.014, 0.014)] * len(rim), n=5, up=(0, 0, 1), cap0=False, cap1=False)
        add(P(V, F, "BH_Bronze", "brim"), ua)
        add(aether_line([c + Ry(-sx * 25) @ np.array([0.0, y, 0.095 * math.cos(y * 9)]) for y in
                         np.linspace(-0.09, 0.09, 5)], 0.008), ua)

    # ---- legs
    for sx, s in ((1, "L"), (-1, "R")):
        th, sh = "thigh." + s, "shin." + s
        add(stone_limb(body, th, [(0.08, 0.085, 0.09), (0.5, 0.09, 0.095), (0.88, 0.075, 0.08)]), th)
        k = body.head(sh)
        add(ball(k + (0, -0.01, 0), 0.07, "BH_Bronze", 10, 6), sh)
        add(stone_limb(body, sh, [(0.12, 0.085, 0.09), (0.45, 0.09, 0.098), (0.85, 0.075, 0.08)]), sh)
        a = body.tail(sh)
        add(joint_ring(k + (a - k) * 0.3, a - k, 0.1, w=0.04), sh)
        add(joint_ring(body.head(th) + (k - body.head(th)) * 0.3, k - body.head(th), 0.098, w=0.035), th)
        tl = body.p["hip_h"] - body.p["knee_h"]
        add(aether_line(body.lpt(th, [(sx * 0.02, u * tl, 0.097) for u in np.linspace(0.4, 0.8, 4)]), 0.007), th)
        add(aether_line(body.lpt(sh, [(0.0, u * 0.43, 0.1) for u in np.linspace(0.4, 0.75, 4)]), 0.007), sh)
        hx = body.p["hip_x"] * sx
        V, F = M.box(0.15, 0.24, 0.1, center=(hx, -0.04, 0.05))
        add(M.bevel(P(V, F, "BH_Stone", "foot"), 0.02, 1), "foot." + s)
        V, F = M.box(0.14, 0.09, 0.07, center=(hx, -0.2, 0.035))
        add(M.bevel(P(V, F, "BH_Bronze", "toecap"), 0.015, 1), "toe." + s)

    add_weapon(body, "L", slab_shield())
    add_weapon(body, "R", maul())
