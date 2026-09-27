"""Rune Golem (construct / tank; Builder B, bh-010): a ~2.9 m blocky golem of carved dark slate slabs held together by
a few bronze bands. Huge squared shoulders with slab pauldrons, a small head-stone sunk between them, massive forearms
and block fists, short thick pillar legs on broad slab feet. Deeply carved rune channels run over every block and a
large rune core sits in a bronze-clamped socket in the chest.

Runtime contract: ALL glowing rune / core / eye geometry uses BH_Emissive and nothing else does. The game recolours
BH_Emissive per spawn to show the element the golem is immune to, so its base / emission colour is neutral white.
Distinct from the Aether Sentinel (no floating segments, no weapons or shield, no visor, far heavier and squarer).
Modelled at true size on the shared humanoid skeleton (proportions())."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft, torso_ring, interp_rows, front_y, back_y  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as K  # noqa: E402

S = 1.6
PROPS = proportions(
    S,
    pelvis_h=1.25, hip_h=1.18, knee_h=0.62, ankle_h=0.15, hip_x=0.27, ball_fwd=0.28, ball_h=0.05, toe_len=0.14,
    heel_back=0.12,
    hips_len=0.22, spine_len=0.36, chest_len=0.72, neck_len=0.08, head_len=0.3,
    clav_x0=0.12, clav_drop=0.18, shoulder_x=0.62, upper_len=0.58, fore_len=0.62, hand_len=0.22, grip_x=0.14,
    grip_drop=0.03,
)
L = K.levels(PROPS)
PREVIEW_HEIGHT = 3.3

PALETTE = "rune_golem"
PALETTE_COLORS = {
    "BH_Stone": ((0.2, 0.205, 0.215), 0.0, 0.9, None, 0.0, 1.0),           # dark slate slabs
    "BH_Bronze": ((0.46, 0.3, 0.13), 1.0, 0.42, None, 0.0, 1.0),           # bronze bands / clamps
    "BH_DarkSteel": ((0.075, 0.075, 0.085), 0.0, 0.9, None, 0.0, 1.0),     # basalt core column / joint stones
    "BH_Shadow": ((0.02, 0.02, 0.025), 0.0, 0.85, None, 0.0, 1.0),         # carved grooves (no emission)
    # neutral white: the game tints this per spawn (element immunity). Only runes / core / eyes use it.
    "BH_Emissive": ((0.92, 0.92, 0.9), 0.0, 0.35, (0.95, 0.95, 0.92), 6.0, 1.0),
}

CLIPS = ["gs_1", "boss_slam", "cast_heavy", "boss_sweep", "boss_charge"]

HEAD_DZ = 0.0


# ------------------------------------------------------------------------------------------------- helpers
def P(V, F, mat, name="part"):
    return M.Part(np.asarray(V, float), F, mat, name=name)


def block(rows, mat="BH_Stone", p=4.0, n=28, bev=0.012):
    V, F = torso_loft(rows, n=n, p=p, cap0=True, cap1=True)
    return M.bevel(P(V, F, mat, "block"), bev, 2, angle=40)


def band(rows, z, h, g, mat="BH_Bronze", p=4.0, n=28):
    r = interp_rows(rows, z)
    cy = r[5] if len(r) > 5 else 0.0
    loops = [torso_ring(z - h / 2, r[1] + g, r[2] + g, r[3] + g, 0.0, p, n, cy=cy),
             torso_ring(z + h / 2, r[1] + g, r[2] + g, r[3] + g, 0.0, p, n, cy=cy)]
    V, F = M.loft(loops, cap0=True, cap1=True)
    return P(V, F, mat, "band")


def slab(size, center, R=None, mat="BH_Stone", bev=0.015):
    V, F = M.box(*size)
    prt = P(V, F, mat, "slab")
    if R is not None:
        prt.rot(R)
    prt.move(center)
    return M.bevel(prt, bev, 1, angle=35)


def channel(pts, nrm, r=0.022):
    """A carved rune channel: a dark groove strip with the glowing BH_Emissive inlay just proud of it.
    pts: surface points; nrm: outward normal (one vector or one per point)."""
    pts = np.asarray(pts, float)
    nrm = np.asarray(nrm, float)
    if nrm.ndim == 1:
        nrm = np.repeat(nrm[None], len(pts), 0)
    return [K.rtube(pts - nrm * 0.012, r * 1.7, "BH_Shadow", n=4),
            K.rtube(pts - nrm * 0.003, r, "BH_Emissive", n=6)]


def crack(pts, nrm, r=0.006):
    pts = np.asarray(pts, float) - np.asarray(nrm, float) * 0.004
    return K.rtube(pts, r, "BH_Shadow", n=4)


def local_box(body, b, size, center, mat="BH_Stone", bev=0.015):
    """Box in bone-local coordinates (x, y along the bone, z) -> model space, rigid to b."""
    V, F = M.box(*size, center=center)
    V = body.lpt(b, V)
    return M.bevel(P(V, F, mat, "lbox"), bev, 1, angle=35)


def stone_limb(body, b, prof, mat="BH_Stone", p=3.4):
    return M.bevel(body.limb(b, prof, mat, n=16, p=p), 0.008, 2, angle=40)


def joint_ring(c, axis, r, w=0.05, mat="BH_Bronze"):
    axis = normalize(axis)
    V, F = M.tube([c - axis * w / 2, c + axis * w / 2], [(r, r), (r, r)], n=16,
                  up=(0, 0, 1) if abs(axis[2]) < 0.9 else (0, -1, 0))
    return P(V, F, mat, "jring")


# ------------------------------------------------------------------------------------------------- torso blocks
zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
PELV = [(zh - 0.23, 0.33, 0.22, 0.22, 0.0), (zh - 0.14, 0.42, 0.28, 0.27, 0.0), (zh + 0.06, 0.44, 0.29, 0.28, 0.0),
        (zh + 0.17, 0.4, 0.26, 0.25, 0.0)]
ABDO = [(zs + 0.11 - 0.2, 0.34, 0.24, 0.24, 0.0), (zs + 0.0, 0.38, 0.27, 0.26, 0.0), (zs + 0.22, 0.41, 0.29, 0.28, 0.0),
        (zs + 0.3, 0.38, 0.27, 0.27, 0.0)]
CHEST = [(zc - 0.12, 0.42, 0.3, 0.3, 0.0, 0.0), (zc + 0.02, 0.53, 0.37, 0.36, 0.0, -0.01),
         (zc + 0.28, 0.63, 0.42, 0.42, 0.0, -0.02), (zc + 0.54, 0.68, 0.42, 0.45, 0.0, -0.01),
         (zn - 0.04, 0.62, 0.37, 0.42, 0.0, 0.01), (zn + 0.05, 0.46, 0.28, 0.33, 0.0, 0.02)]
HEADB = [(-0.12, 0.15, 0.17, 0.15, 0.0, -0.08), (-0.04, 0.18, 0.2, 0.17, 0.0, -0.1), (0.12, 0.19, 0.21, 0.18, 0.0, -0.1),
         (0.2, 0.17, 0.19, 0.17, 0.0, -0.09), (0.24, 0.13, 0.15, 0.13, 0.0, -0.08)]


def hrows():
    z0 = L["head"] + HEAD_DZ
    return [(z0 + r[0], r[1], r[2], r[3], r[4], r[5]) for r in HEADB]


def fy(rows, x, z):
    return front_y([r[:5] for r in rows], x, z, p=4.0) + (interp_rows(rows, z)[5] if len(rows[0]) > 5 else 0.0)


def by(rows, x, z):
    return back_y([r[:5] for r in rows], x, z, p=4.0) + (interp_rows(rows, z)[5] if len(rows[0]) > 5 else 0.0)


def surf_front(rows, xz, out=0.0):
    return [(x, fy(rows, x, z) - out, z) for x, z in xz]


def surf_back(rows, xz, out=0.0):
    return [(x, by(rows, x, z) + out, z) for x, z in xz]


# ================================================================================================= build
def build(body: Body):
    add = body.add
    FRONT, BACK = np.array([0, -1.0, 0]), np.array([0, 1.0, 0])
    # basalt core column: bridges the gaps between the slab blocks when the torso bends
    core_w = K.zspec_w([(zh + 0.05, "hips"), (zs + 0.05, "spine"), (zc - 0.05, "spine"), (zc + 0.1, "chest")])
    V, F = M.tube([(0, 0.0, zh - 0.05), (0, 0.0, zs), (0, 0.0, zc), (0, 0.0, zc + 0.3)],
                  [(0.3, 0.2), (0.3, 0.2), (0.3, 0.2), (0.3, 0.2)], n=14, up=(0, -1, 0))
    add(P(V, F, "BH_DarkSteel", "core"), weights=core_w)

    # ---- pelvis
    add(block(PELV), "hips")
    add(band(PELV, zh + 0.1, 0.07, 0.012), "hips")
    for x0, x1 in ((-0.3, -0.12), (0.12, 0.3)):
        add_parts(body, channel(surf_front(PELV, [(x0, zh - 0.02), (x0 * 0.5 + x1 * 0.5, zh - 0.09), (x1, zh - 0.02)],
                                           0.0), FRONT), "hips")
    # tasset slabs hanging over each thigh (front and sides), split per leg
    for sx in (1, -1):
        lb = "thigh.L" if sx > 0 else "thigh.R"
        for (x, y, w, rz) in ((0.17, -0.3, 0.26, 0), (0.47, -0.04, 0.24, 90)):
            c = np.array([sx * x, y, zh - 0.2])
            s = slab((w, 0.07, 0.3), c, R=Rz(sx * rz) @ Rx(10 if rz == 0 else 0), bev=0.014)
            add(s, weights=lambda V, lb=lb: [{"hips": 0.55, lb: 0.45}] * len(V))
            if rz == 0:
                pts = [c + (sx * 0.0, -0.045, 0.1), c + (0, -0.05, -0.02), c + (sx * 0.06, -0.055, -0.1)]
                for prt in channel(pts, FRONT, 0.02):
                    add(prt, weights=lambda V, lb=lb: [{"hips": 0.55, lb: 0.45}] * len(V))

    # ---- abdomen
    add(block(ABDO), "spine")
    add(band(ABDO, zs + 0.2, 0.06, 0.012), "spine")
    add_parts(body, channel(surf_front(ABDO, [(-0.22, zs + 0.06), (-0.08, zs + 0.06), (0.0, zs + 0.0),
                                              (0.08, zs + 0.06), (0.22, zs + 0.06)]), FRONT), "spine")
    add_parts(body, channel(surf_back(ABDO, [(0.0, zs - 0.06), (0.0, zs + 0.26)]), BACK), "spine")

    # ---- chest
    chest(body)
    head(body)
    for s in ("L", "R"):
        arm(body, s)
        leg(body, s)


def add_parts(body, parts, bone):
    for prt in parts:
        body.add(prt, bone)


def chest(body):
    add = body.add
    FRONT, BACK = np.array([0, -1.0, 0]), np.array([0, 1.0, 0])
    add(block(CHEST, bev=0.016), "chest")
    add(band(CHEST, zc - 0.02, 0.07, 0.012), "chest")
    # pectoral slabs, each with a carved glyph
    for sx in (1, -1):
        zp = zc + 0.47
        xp = sx * 0.34
        yf = fy(CHEST, xp, zp)
        c = np.array([xp, yf + 0.02, zp])
        add(slab((0.38, 0.1, 0.32), c, bev=0.018), "chest")
        f = c[1] - 0.05
        glyph = [(xp - sx * 0.1, f, zp + 0.08), (xp - sx * 0.0, f, zp - 0.06), (xp + sx * 0.1, f, zp + 0.08)]
        add_parts(body, channel(glyph, FRONT, 0.02), "chest")
        add_parts(body, channel([(xp - sx * 0.1, f, zp - 0.1), (xp + sx * 0.1, f, zp - 0.1)], FRONT, 0.02), "chest")
    # rune core in a recessed socket with bronze clamps
    zcore = zc + 0.25
    yc = fy(CHEST, 0, zcore)
    add(K.blob((0, yc + 0.0, zcore), 0.2, "BH_Shadow", scale=(1, 0.35, 1), n=16, rings=6), "chest")
    V, F = M.sphere(0.15, 16, 10, scale=(1, 0.75, 1))
    core = P(V, F, "BH_Emissive", "core")
    add(core.move((0, yc - 0.03, zcore)), "chest")
    ring = [(0.2 * math.cos(a), yc - 0.02, zcore + 0.2 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 25)]
    V, F = M.tube(ring, [(0.035, 0.035)] * len(ring), n=6, up=(0, -1, 0), cap0=False, cap1=False, p=3.0)
    add(P(V, F, "BH_Stone", "socket"), "chest")
    ring = [(0.245 * math.cos(a), yc - 0.005, zcore + 0.245 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 25)]
    V, F = M.tube(ring, [(0.02, 0.02)] * len(ring), n=6, up=(0, -1, 0), cap0=False, cap1=False)
    add(P(V, F, "BH_Bronze", "corering"), "chest")
    for a in (45, 135, 225, 315):
        ra = math.radians(a)
        d = np.array([math.cos(ra), 0, math.sin(ra)])
        c = np.array([0, yc - 0.04, zcore]) + d * 0.2
        add(slab((0.07, 0.05, 0.12), c, R=Ry(-a + 90), mat="BH_Bronze", bev=0.01), "chest")
    # channels radiating from the core: angular rune lines
    lines = [
        [(0.0, zcore + 0.26), (0.0, zcore + 0.4), (0.1, zcore + 0.5)],
        [(0.0, zcore + 0.4), (-0.1, zcore + 0.5)],
        [(0.0, zcore - 0.26), (0.0, zc + 0.02), ],
        [(-0.1, zc + 0.08), (0.1, zc + 0.08)],
    ]
    for sx in (1, -1):
        lines.append([(sx * 0.25, zcore - 0.08), (sx * 0.38, zcore - 0.16), (sx * 0.38, zc + 0.04)])
        lines.append([(sx * 0.25, zcore + 0.06), (sx * 0.5, zcore + 0.06), (sx * 0.56, zcore + 0.14)])
    for ln in lines:
        add_parts(body, channel(surf_front(CHEST, ln), FRONT), "chest")
    # back: spine channel with cross bars and a rune ring between the shoulder blades
    add_parts(body, channel(surf_back(CHEST, [(0, zc - 0.06), (0, zc + 0.3)]), BACK), "chest")
    for z, w in ((zc + 0.08, 0.2), (zc + 0.2, 0.3)):
        add_parts(body, channel(surf_back(CHEST, [(-w, z), (w, z)]), BACK), "chest")
    zr = zc + 0.46
    ring = [(0.13 * math.cos(a), zr + 0.13 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 17)]
    add_parts(body, channel(surf_back(CHEST, ring), BACK), "chest")
    add_parts(body, channel(surf_back(CHEST, [(0, zr - 0.13), (0, zr + 0.13)]), BACK), "chest")
    # back slabs + cracks for texture
    for sx in (1, -1):
        c = np.array([sx * 0.36, by(CHEST, sx * 0.36, zc + 0.3) - 0.02, zc + 0.3])
        add(slab((0.3, 0.1, 0.42), c, R=Rz(sx * 5), bev=0.018), "chest")
    add(crack(surf_front(CHEST, [(0.3, zc + 0.3), (0.34, zc + 0.24), (0.31, zc + 0.16), (0.36, zc + 0.1)]), FRONT),
        "chest")
    add(crack(surf_front(CHEST, [(-0.52, zc + 0.46), (-0.46, zc + 0.4), (-0.48, zc + 0.33)]), FRONT), "chest")
    add(crack(surf_back(CHEST, [(-0.5, zc + 0.1), (-0.44, zc + 0.16), (-0.46, zc + 0.24)]), BACK), "chest")
    # collar stones round the sunken head
    for sx in (1, -1):
        c = np.array([sx * 0.34, 0.04, zn + 0.03])
        add(slab((0.2, 0.44, 0.16), c, R=Ry(sx * 18), bev=0.015), "chest")


def head(body):
    add = body.add
    FRONT = np.array([0, -1.0, 0])
    H = hrows()
    z0 = L["head"] + HEAD_DZ
    add(block(H, bev=0.014), "head")
    # heavy brow slab overhanging deep eye sockets
    yb = fy(H, 0, z0 + 0.1)
    add(slab((0.4, 0.12, 0.08), (0, yb - 0.02, z0 + 0.13), R=Rx(-8), bev=0.012), "head")
    for sx in (1, -1):
        ye = fy(H, 0.08, z0 + 0.06)
        add(slab((0.1, 0.03, 0.05), (sx * 0.08, ye + 0.006, z0 + 0.06), mat="BH_Shadow", bev=0.006), "head")
        add(slab((0.07, 0.02, 0.022), (sx * 0.08, ye - 0.006, z0 + 0.06), mat="BH_Emissive", bev=0.005), "head")
    # jaw stone and a forehead rune
    yj = fy(H, 0, z0 - 0.06)
    add(slab((0.3, 0.1, 0.1), (0, yj + 0.02, z0 - 0.07), bev=0.014), "head")
    add_parts(body, channel([(0, yb - 0.085, z0 + 0.1), (0, yb - 0.085, z0 + 0.16)], FRONT, 0.012), "head")
    zt = z0 + 0.19
    yt = fy(H, 0, zt)
    add_parts(body, channel([(-0.07, yt - 0.004, zt), (0.0, yt - 0.004, zt + 0.035), (0.07, yt - 0.004, zt)], FRONT,
                            0.012), "head")
    add(band(H, z0 + 0.0, 0.035, 0.012), "head")
    # a flat cap stone on top
    add(slab((0.28, 0.3, 0.07), (0, -0.1, z0 + 0.255), R=Rx(4), bev=0.015), "head")


def arm(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    sh_b, ua, fa, ha = "shoulder." + s, "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
    # shoulder ball + upper arm pillar
    add(K.blob(sh, 0.22, "BH_DarkSteel", n=14, rings=8), ua)
    add(stone_limb(body, ua, [(0.12, 0.17, 0.18), (0.5, 0.18, 0.19), (0.9, 0.16, 0.17)]), ua)
    add(joint_ring(sh + (el - sh) * 0.55, el - sh, 0.225, w=0.07), ua)
    A = body.axes(ua)
    ul = body.p["upper_len"]
    add_parts(body, channel(body.lpt(ua, [(0.0, u * ul, 0.19) for u in (0.2, 0.42)]), A[:, 2], 0.02), ua)
    add_parts(body, channel(body.lpt(ua, [(0.0, u * ul, 0.19) for u in (0.68, 0.85)]), A[:, 2], 0.02), ua)
    # pauldron: a heavy tilted slab over the shoulder (on the clavicle bone so it stays put when the arm swings)
    c = sh + np.array([sx * 0.04, 0.0, 0.16])
    R = Ry(-sx * 10)
    add(slab((0.5, 0.58, 0.3), c, R=R, bev=0.03), sh_b)
    add(slab((0.42, 0.5, 0.12), c + R @ np.array([sx * 0.04, 0, 0.17]), R=R, bev=0.02), sh_b)
    add(slab((0.52, 0.06, 0.3), c + R @ np.array([0, -0.27, -0.02]), R=R, mat="BH_Bronze", bev=0.01), sh_b)
    top = c + R @ np.array([sx * 0.04, 0, 0.231])
    nz = R @ np.array([0, 0, 1.0])
    add_parts(body, channel([top + R @ np.array([-0.14, -0.16, 0]), top + R @ np.array([0, 0.0, 0]),
                             top + R @ np.array([0.14, -0.16, 0])], nz, 0.022), sh_b)
    add_parts(body, channel([top + R @ np.array([0, 0.0, 0]), top + R @ np.array([0, 0.2, 0])], nz, 0.022), sh_b)
    # elbow stone + massive forearm
    add(K.blob(el, 0.19, "BH_DarkSteel", n=14, rings=8), fa)
    add(stone_limb(body, fa, [(0.05, 0.2, 0.2), (0.45, 0.25, 0.25), (0.8, 0.26, 0.26), (0.97, 0.23, 0.23)], p=3.8), fa)
    fl = body.p["fore_len"]
    add(joint_ring(el + (wr - el) * 0.9, wr - el, 0.29, w=0.08), fa)
    add(joint_ring(el + (wr - el) * 0.3, wr - el, 0.27, w=0.05), fa)
    A = body.axes(fa)
    for dx in (-0.07, 0.07):
        add_parts(body, channel(body.lpt(fa, [(dx, u * fl, 0.25 + 0.03 * u) for u in (0.4, 0.6, 0.78)]), A[:, 2],
                                0.022), fa)
    add_parts(body, channel(body.lpt(fa, [(-0.07, 0.6 * fl, 0.265), (0.07, 0.6 * fl, 0.265)]), A[:, 2], 0.022), fa)
    add(crack(body.lpt(fa, [(0.2, 0.5 * fl, -0.14), (0.22, 0.6 * fl, -0.12), (0.2, 0.7 * fl, -0.15)]), -A[:, 2]), fa)
    fist(body, s)


def fist(body, s):
    """Massive block fist rigid to hand.<s>, bone-local (x, y along the hand, z = back of the hand)."""
    add = body.add
    ha = "hand." + s
    A = body.axes(ha)
    fwd = A.T @ np.array([0, -1.0, 0])      # world forward (thumb side in the T-pose) in bone-local axes
    tx = 1.0 if fwd[0] > 0 else -1.0
    add(local_box(body, ha, (0.36, 0.34, 0.34), (0, 0.17, -0.02), bev=0.03), ha)
    # knuckle row (four stones across the distal face)
    for k in range(4):
        x = -0.135 + 0.09 * k
        add(local_box(body, ha, (0.085, 0.08, 0.12), (x, 0.35, 0.06), bev=0.015), ha)
    # thumb block on the forward side
    add(local_box(body, ha, (0.1, 0.2, 0.14), (tx * 0.2, 0.2, -0.08), bev=0.02), ha)
    # bronze strap over the back of the fist and a rune on it
    add(local_box(body, ha, (0.38, 0.07, 0.36), (0, 0.1, -0.02), mat="BH_Bronze", bev=0.01), ha)
    pts = body.lpt(ha, [(-0.1, 0.2, 0.15), (0.0, 0.28, 0.15), (0.1, 0.2, 0.15)])
    add_parts(body, channel(pts, A[:, 2], 0.022), ha)


def leg(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    th, sh, ft, toe = "thigh." + s, "shin." + s, "foot." + s, "toe." + s
    hip, k, a = body.head(th), body.head(sh), body.tail(sh)
    add(K.blob(hip, 0.21, "BH_DarkSteel", n=14, rings=8), th)
    add(stone_limb(body, th, [(0.05, 0.22, 0.23), (0.5, 0.25, 0.25), (0.92, 0.21, 0.22)]), th)
    add(joint_ring(hip + (k - hip) * 0.55, k - hip, 0.295, w=0.07), th)
    add(K.blob(k + (0, -0.02, 0), 0.2, "BH_DarkSteel", n=14, rings=8), sh)
    add(stone_limb(body, sh, [(0.08, 0.22, 0.22), (0.4, 0.25, 0.26), (0.85, 0.24, 0.25), (1.0, 0.22, 0.23)]), sh)
    add(joint_ring(k + (a - k) * 0.75, a - k, 0.295, w=0.08), sh)
    # knee slab
    add(slab((0.3, 0.1, 0.24), k + (0, -0.2, 0.0), R=Rx(-8), bev=0.02), sh)
    add_parts(body, channel([k + (-0.07, -0.255, 0.06), k + (0.0, -0.26, -0.04), k + (0.07, -0.255, 0.06)],
                            np.array([0, -1.0, 0]), 0.02), sh)
    # shin runes (front) and thigh runes (outer side)
    add_parts(body, channel([k + (0, -0.25, -0.18) + (a - k) * 0.0, a + (0, -0.26, 0.2)], np.array([0, -1.0, 0]),
                            0.022), sh)
    add_parts(body, channel([a + (-0.07, -0.25, 0.28), a + (0.07, -0.25, 0.28)], np.array([0, -1.0, 0]), 0.022), sh)
    add_parts(body, channel([hip + (sx * 0.25, 0, -0.15), k + (sx * 0.24, 0, 0.18)], np.array([sx, 0, 0.0]), 0.022),
              th)
    # broad slab foot + toe slab
    hx = body.p["hip_x"] * sx
    add(slab((0.4, 0.46, 0.17), (hx, -0.02, 0.085), bev=0.03), ft)
    add(slab((0.36, 0.08, 0.1), (hx, -0.21, 0.19), R=Rx(-30), mat="BH_Bronze", bev=0.01), ft)
    add(slab((0.38, 0.16, 0.12), (hx, -0.31, 0.06), bev=0.025), toe)
