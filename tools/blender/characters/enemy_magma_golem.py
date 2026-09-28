"""Magma Golem (Builder C, bh-012, Emberforge Depths): a ~2.6 m brute of stacked basalt slabs with molten seams. A
glowing molten core column runs through the body, so every gap between the slabs glows; a furnace core burns in a
grated socket in the chest (BH_WeakPoint). Boulder fists, obsidian shards jutting from the back and shoulders, a
small head of fused rock with two ember eyes. Construct built like enemy_rune_golem (reuses its slab helpers)."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as K  # noqa: E402
import kit_ember as E  # noqa: E402
from enemy_rune_golem import P, block, band, slab, channel, crack, local_box, stone_limb, fy, by, add_parts  # noqa

S = 1.45
PROPS = proportions(
    S,
    pelvis_h=1.1, hip_h=1.04, knee_h=0.56, ankle_h=0.13, hip_x=0.24, ball_fwd=0.25, ball_h=0.045, toe_len=0.12,
    heel_back=0.1,
    hips_len=0.2, spine_len=0.3, chest_len=0.62, neck_len=0.07, head_len=0.26,
    clav_x0=0.11, clav_drop=0.16, shoulder_x=0.55, upper_len=0.5, fore_len=0.54, hand_len=0.2, grip_x=0.12,
    grip_drop=0.03,
)
L = K.levels(PROPS)
PREVIEW_HEIGHT = 3.0

PALETTE = "magma_golem"
PALETTE_COLORS = {
    "BH_Stone": ((0.085, 0.078, 0.076), 0.0, 0.9, None, 0.0, 1.0),        # basalt slabs
    "BH_DarkSteel": ((0.05, 0.045, 0.045), 0.0, 0.95, None, 0.0, 1.0),    # soot-black joint stones
    "BH_Horn": ((0.035, 0.03, 0.045), 0.3, 0.12, None, 0.0, 1.0),         # obsidian shards (glossy)
    "BH_Rust": ((0.16, 0.08, 0.04), 0.4, 0.8, None, 0.0, 1.0),            # iron grate over the core
    "BH_Shadow": ((0.02, 0.015, 0.012), 0.0, 0.85, None, 0.0, 1.0),       # seam grooves
    "BH_Emissive": E.EMBER,                                              # molten seams, eyes
    "BH_WeakPoint": ((1.0, 0.6, 0.2), 0.0, 0.3, (1.0, 0.55, 0.15), 14.0, 1.0),  # furnace core
}
CLIPS = ["gs_1", "gs_2", "boss_slam", "cast_heavy", "boss_charge"]

zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
FRONT, BACK = np.array([0, -1.0, 0]), np.array([0, 1.0, 0])
PELV = [(zh - 0.2, 0.3, 0.2, 0.2, 0.0), (zh - 0.12, 0.38, 0.25, 0.25, 0.0), (zh + 0.05, 0.4, 0.26, 0.26, 0.0),
        (zh + 0.1, 0.36, 0.23, 0.23, 0.0)]
ABDO = [(zs + 0.0, 0.3, 0.21, 0.21, 0.0), (zs + 0.06, 0.34, 0.24, 0.23, 0.0), (zs + 0.16, 0.37, 0.26, 0.25, 0.0),
        (zs + 0.21, 0.34, 0.24, 0.24, 0.0)]
CHEST = [(zc + 0.02, 0.4, 0.28, 0.28, 0.0, 0.0), (zc + 0.1, 0.5, 0.35, 0.34, 0.0, -0.01),
         (zc + 0.3, 0.6, 0.4, 0.4, 0.0, -0.02), (zc + 0.5, 0.64, 0.4, 0.43, 0.0, -0.01),
         (zn - 0.04, 0.58, 0.35, 0.4, 0.0, 0.01), (zn + 0.04, 0.42, 0.26, 0.3, 0.0, 0.02)]


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def rough(part, amp, seed):
    return E.jitter(part, amp, seed=seed)


def build(body: Body):
    add = body.add
    # molten core column: the glow that shows between every slab
    core_w = K.zspec_w([(zh + 0.02, "hips"), (zs + 0.05, "spine"), (zc - 0.02, "spine"), (zc + 0.12, "chest")])
    V, F = M.tube([(0, 0.0, zh - 0.12), (0, 0.0, zs), (0, 0.0, zc), (0, 0.0, zc + 0.4)],
                  [(0.3, 0.2), (0.3, 0.2), (0.33, 0.22), (0.4, 0.26)], n=14, up=(0, -1, 0))
    add(P(V, F, "BH_Emissive", "core"), weights=core_w)

    # ---- pelvis slab + tassets
    add(rough(block(PELV, p=3.2, bev=0.02), 0.012, 1), "hips")
    add_parts(body, channel(E_front(PELV, [(-0.28, zh - 0.02), (-0.1, zh - 0.1), (0.05, zh - 0.02), (0.25, zh - 0.08)]),
                            FRONT, 0.03), "hips")
    for sx in (1, -1):
        lb = "thigh.L" if sx > 0 else "thigh.R"
        c = np.array([sx * 0.3, -0.18, zh - 0.2])
        s = rough(slab((0.3, 0.1, 0.32), c, R=Rz(sx * 25) @ Rx(10), bev=0.02), 0.012, 2 + sx)
        add(s, weights=lambda V, lb=lb: [{"hips": 0.55, lb: 0.45}] * len(V))

    # ---- abdomen slab (smaller: a wide glowing gap above and below)
    add(rough(block(ABDO, p=3.2, bev=0.02), 0.012, 3), "spine")
    add_parts(body, channel(E_front(ABDO, [(-0.2, zs + 0.14), (-0.05, zs + 0.08), (0.12, zs + 0.16), (0.24, zs + 0.1)]),
                            FRONT, 0.03), "spine")
    add_parts(body, channel(E_back(ABDO, [(-0.1, zs), (0.05, zs + 0.12), (0.0, zs + 0.24)]), BACK, 0.03), "spine")

    chest(body)
    head(body)
    for s in ("L", "R"):
        arm(body, s)
        leg(body, s)


def E_front(rows, xz, out=0.0):
    return [(x, fy(rows, x, z) - out, z) for x, z in xz]


def E_back(rows, xz, out=0.0):
    return [(x, by(rows, x, z) + out, z) for x, z in xz]


def chest(body):
    add = body.add
    rng = np.random.default_rng(5)
    add(rough(block(CHEST, p=3.4, bev=0.02), 0.016, 4), "chest")
    # overlapping pectoral / flank slabs (leave glowing gaps between them)
    for sx in (1, -1):
        zp = zc + 0.46
        xp = sx * 0.34
        c = np.array([xp, fy(CHEST, xp, zp) + 0.03, zp])
        add(rough(slab((0.4, 0.12, 0.34), c, R=Ry(sx * 6), bev=0.02), 0.01, 6 + sx), "chest")
        c = np.array([sx * 0.5, fy(CHEST, sx * 0.5, zc + 0.16) + 0.05, zc + 0.16])
        add(rough(slab((0.22, 0.1, 0.3), c, R=Rz(-sx * 30) @ Ry(-sx * 8), bev=0.02), 0.01, 9 + sx), "chest")
    # furnace core: dark socket, iron rim, bars, the glowing core (weak point)
    zcore = zc + 0.22
    yc = fy(CHEST, 0, zcore)
    add(K.blob((0, yc + 0.02, zcore), 0.22, "BH_Shadow", scale=(1, 0.35, 1), n=16, rings=6), "chest")
    V, F = M.sphere(0.16, 16, 10, scale=(1, 0.7, 1))
    add(P(V, F, "BH_WeakPoint", "furnace_core").move((0, yc - 0.03, zcore)), "chest")
    ring = [(0.22 * math.cos(a), yc - 0.03, zcore + 0.22 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 21)]
    V, F = M.tube(ring, [(0.04, 0.05)] * len(ring), n=6, up=(0, -1, 0), cap0=False, cap1=False, p=3.0)
    add(rough(P(V, F, "BH_Stone", "socket"), 0.01, 11), "chest")
    for x in (-0.09, 0.0, 0.09):
        h = math.sqrt(max(0.2 ** 2 - x * x, 0.01))
        add(K.rtube([(x, yc - 0.12, zcore - h), (x, yc - 0.15, zcore), (x, yc - 0.12, zcore + h)], 0.018, "BH_Rust",
                    n=5), "chest")
    # seams radiating from the core
    lines = [[(0.0, zcore + 0.24), (0.06, zcore + 0.36), (-0.02, zn - 0.1)],
             [(0.22, zcore - 0.05), (0.36, zcore - 0.1), (0.42, zc + 0.02)],
             [(-0.22, zcore + 0.02), (-0.4, zcore - 0.04), (-0.52, zcore + 0.1)],
             [(0.0, zcore - 0.24), (-0.05, zc + 0.02)]]
    for ln in lines:
        add_parts(body, channel(E_front(CHEST, ln), FRONT, 0.032), "chest")
    for ln in ([(-0.3, zc + 0.1), (-0.15, zc + 0.3), (-0.2, zc + 0.5)], [(0.25, zc + 0.05), (0.3, zc + 0.35)],
               [(0.0, zc + 0.1), (0.05, zc + 0.45)]):
        add_parts(body, channel(E_back(CHEST, ln), BACK, 0.032), "chest")
    # obsidian shards jutting from the back (a spined ridge up the shoulders)
    for i, (x, z, ln, ax, az) in enumerate(((0.0, zc + 0.52, 0.55, 0, 55), (0.2, zc + 0.46, 0.45, 25, 45),
                                           (-0.22, zc + 0.44, 0.48, -25, 48), (0.12, zc + 0.24, 0.36, 18, 30),
                                           (-0.1, zc + 0.2, 0.34, -18, 28), (0.36, zc + 0.36, 0.32, 40, 35),
                                           (-0.38, zc + 0.32, 0.3, -40, 38))):
        b = np.array([x, by(CHEST, x, z) - 0.04, z])
        d = normalize(np.array([math.sin(math.radians(ax)), math.cos(math.radians(az)), math.sin(math.radians(az))]))
        add(E.shard(b, d, ln, 0.07 + 0.02 * (ln > 0.4), seed=i, twist=0.3 * i), "chest")
    # seam across the top of the shoulders (reads from the high gameplay camera)
    add_parts(body, channel([(-0.5, -0.05, zn - 0.02), (-0.3, 0.05, zn + 0.02), (-0.12, -0.1, zn + 0.03)],
                            np.array([0, 0, 1.0]), 0.032), "chest")
    add_parts(body, channel([(0.5, 0.05, zn - 0.02), (0.3, -0.08, zn + 0.02), (0.14, 0.08, zn + 0.03)],
                            np.array([0, 0, 1.0]), 0.032), "chest")
    # collar stones around the sunken head
    for sx in (1, -1):
        c = np.array([sx * 0.32, 0.05, zn + 0.02])
        add(rough(slab((0.22, 0.4, 0.16), c, R=Ry(sx * 20), bev=0.02), 0.01, 20 + sx), "chest")


def head(body):
    add = body.add
    z0 = L["head"]
    add(E.rock((0, -0.08, z0 + 0.1), (0.17, 0.18, 0.16), "BH_Stone", seed=3, amp=0.1), "head")
    add(E.rock((0, -0.2, z0 + 0.15), (0.2, 0.08, 0.06), "BH_Stone", seed=4, amp=0.08), "head")  # heavy brow
    add(E.rock((0, -0.14, z0 + 0.0), (0.14, 0.12, 0.08), "BH_DarkSteel", seed=5, amp=0.1), "head")  # jaw
    for sx in (1, -1):
        add(K.blob((sx * 0.07, -0.235, z0 + 0.1), 0.035, "BH_Shadow", scale=(1.3, 0.5, 0.8), n=8, rings=4), "head")
        add(K.blob((sx * 0.07, -0.25, z0 + 0.1), 0.022, "BH_Emissive", scale=(1.4, 0.5, 0.8), n=8, rings=4), "head")
    add_parts(body, channel([(0.12, -0.2, z0 + 0.02), (0.14, -0.14, z0 + 0.1), (0.12, -0.1, z0 + 0.2)],
                            np.array([1.0, -0.5, 0]), 0.012), "head")
    add(E.shard((0.05, -0.02, z0 + 0.22), (0.2, 0.3, 1.0), 0.16, 0.035, seed=7), "head")


def arm(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    sh_b, ua, fa, ha = "shoulder." + s, "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
    rng = np.random.default_rng(40 + sx)
    add(K.blob(sh, 0.2, "BH_DarkSteel", n=12, rings=7), ua)
    # glowing inner limb + two stacked stone sleeves per segment (gaps glow)
    add(body.limb(ua, [(0.05, 0.13, 0.13), (0.95, 0.12, 0.12)], "BH_Emissive", n=10), ua)
    for u0, u1 in ((0.08, 0.44), (0.58, 0.92)):
        add(rough(stone_limb(body, ua, [(u0, 0.19, 0.2), ((u0 + u1) / 2, 0.2, 0.21), (u1, 0.18, 0.19)]), 0.01,
                  int(u0 * 100) + sx), ua)
    # shoulder boulder + shard cluster (on the clavicle bone)
    c = sh + np.array([sx * 0.04, 0.02, 0.17])
    add(E.rock(c, (0.28, 0.3, 0.2), "BH_Stone", seed=10 + sx, amp=0.1), sh_b)
    add_parts(body, channel([c + (-sx * 0.14, -0.16, 0.15), c + (0.0, -0.04, 0.215), c + (sx * 0.06, 0.1, 0.2),
                             c + (sx * 0.16, 0.16, 0.13)], np.array([0, 0, 1.0]), 0.03), sh_b)
    for k, (dx, dy, ax, ln) in enumerate(((0.05, 0.08, 20, 0.36), (0.14, 0.0, 45, 0.28), (-0.04, 0.12, 5, 0.24))):
        d = normalize(np.array([sx * math.sin(math.radians(ax)), 0.35, math.cos(math.radians(ax))]))
        add(E.shard(c + (sx * dx, dy, 0.1), d, ln, 0.06, seed=30 + k + sx), sh_b)
    add(K.blob(el, 0.17, "BH_DarkSteel", n=12, rings=7), fa)
    add(body.limb(fa, [(0.05, 0.14, 0.14), (0.95, 0.14, 0.14)], "BH_Emissive", n=10), fa)
    for u0, u1, r in ((0.06, 0.36, 0.21), (0.5, 0.95, 0.25)):
        add(rough(stone_limb(body, fa, [(u0, r * 0.95, r), ((u0 + u1) / 2, r * 1.05, r * 1.05), (u1, r, r)], p=3.2),
                  0.012, int(u0 * 100) + 5 + sx), fa)
    fl = body.p["fore_len"]
    A = body.axes(fa)
    add_parts(body, channel(body.lpt(fa, [(0.08, 0.6 * fl, 0.26), (0.0, 0.75 * fl, 0.27), (-0.06, 0.88 * fl, 0.26)]),
                            A[:, 2], 0.028), fa)
    fist(body, s)


def fist(body, s):
    """Boulder fist rigid to hand.<s>: a big lumpy rock with knuckle stones and a glowing crack."""
    add = body.add
    ha = "hand." + s
    A = body.axes(ha)
    c = body.lpt(ha, [(0, 0.17, -0.01)])[0]
    add(E.rock(c, (0.25, 0.26, 0.24), "BH_Stone", seed=50 + (s == "L"), amp=0.1, n=12, rings=8), ha)
    for k in range(4):
        q = body.lpt(ha, [(-0.12 + 0.08 * k, 0.36, 0.07)])[0]
        add(E.rock(q, (0.06, 0.06, 0.07), "BH_DarkSteel", seed=60 + k, amp=0.12, n=7, rings=5), ha)
    pts = body.lpt(ha, [(-0.12, 0.08, 0.2), (-0.02, 0.2, 0.23), (0.08, 0.26, 0.2), (0.15, 0.3, 0.14)])
    add_parts(body, channel(pts, A[:, 2], 0.03), ha)


def leg(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    th, sh, ft, toe = "thigh." + s, "shin." + s, "foot." + s, "toe." + s
    hip, k, a = body.head(th), body.head(sh), body.tail(sh)
    add(K.blob(hip, 0.2, "BH_DarkSteel", n=12, rings=7), th)
    add(body.limb(th, [(0.05, 0.15, 0.15), (0.95, 0.14, 0.14)], "BH_Emissive", n=10), th)
    add(rough(stone_limb(body, th, [(0.1, 0.23, 0.24), (0.45, 0.25, 0.25), (0.82, 0.21, 0.22)]), 0.012, 70 + sx), th)
    add(K.blob(k + (0, -0.02, 0), 0.18, "BH_DarkSteel", n=12, rings=7), sh)
    add(body.limb(sh, [(0.05, 0.14, 0.14), (0.95, 0.13, 0.13)], "BH_Emissive", n=10), sh)
    for u0, u1 in ((0.1, 0.44), (0.6, 0.98)):
        add(rough(stone_limb(body, sh, [(u0, 0.22, 0.23), ((u0 + u1) / 2, 0.24, 0.25), (u1, 0.22, 0.23)]), 0.012,
                  int(u0 * 100) + 80 + sx), sh)
    add(rough(slab((0.28, 0.1, 0.24), k + (0, -0.2, 0.0), R=Rx(-8), bev=0.02), 0.01, 90 + sx), sh)
    add_parts(body, channel([hip + (sx * 0.24, -0.02, -0.12), k + (sx * 0.23, 0.0, 0.2)], np.array([sx, 0, 0.0]), 0.03),
              th)
    hx = body.p["hip_x"] * sx
    add(rough(slab((0.36, 0.44, 0.15), (hx, -0.03, 0.075), bev=0.03), 0.012, 95 + sx), ft)
    add(rough(slab((0.34, 0.16, 0.11), (hx, -0.3, 0.055), bev=0.025), 0.012, 97 + sx), toe)
