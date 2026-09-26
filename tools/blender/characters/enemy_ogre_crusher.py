"""Ogre Crusher (Builder C): enormous pot-bellied ogre (~3 m) with a tiny head sunk between hulking shoulders, an
underbite with jutting teeth, patchy hair, a broken iron slave collar with a hanging chain (the orcs drive it),
iron shackle cuffs, a loincloth on a rope belt, huge bare feet, arms long enough to reach the knees, and a
tree-trunk club bound with iron bands in the right hand. Modelled at true size."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft, smoothstep  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz, R_axis  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as K  # noqa: E402

S = 1.62
PROPS = proportions(
    S,
    pelvis_h=1.50, hip_h=1.42, knee_h=0.78, ankle_h=0.14, hip_x=0.25, ball_fwd=0.25, ball_h=0.04, toe_len=0.12,
    heel_back=0.1,
    hips_len=0.2, spine_len=0.40, chest_len=0.54, neck_len=0.07, head_len=0.3,
    clav_x0=0.1, clav_drop=0.1, shoulder_x=0.47, upper_len=0.66, fore_len=0.6, hand_len=0.2, grip_x=0.14,
    grip_drop=0.03,
)
L = K.levels(PROPS)
PREVIEW_HEIGHT = 3.4

PALETTE = "ogre_crusher"
PALETTE_COLORS = {
    "BH_Skin": ((0.34, 0.30, 0.20), 0.0, 0.6, None, 0.0, 1.0),            # pale grey-brown hide
    "BH_Flesh": ((0.22, 0.12, 0.09), 0.0, 0.55, None, 0.0, 1.0),           # scars / gums
    "BH_Hair": ((0.05, 0.04, 0.03), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Rust": ((0.22, 0.11, 0.055), 0.6, 0.78, None, 0.0, 1.0),           # collar, shackles, chain
    "BH_DarkSteel": ((0.1, 0.095, 0.09), 1.0, 0.55, None, 0.0, 1.0),       # club bands
    "BH_Wood": ((0.13, 0.085, 0.05), 0.0, 0.8, None, 0.0, 1.0),            # tree trunk
    "BH_Bark": None,
    "BH_Cloth_Primary": ((0.10, 0.06, 0.035), 0.0, 0.95, None, 0.0, 1.0),   # loincloth hide/sackcloth
    "BH_Leather": ((0.08, 0.05, 0.03), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Bone": ((0.55, 0.49, 0.36), 0.0, 0.6, None, 0.0, 1.0),
    "BH_Shadow": ((0.03, 0.02, 0.02), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((1.0, 0.6, 0.2), 0.0, 0.4, (1.0, 0.55, 0.15), 3.0, 1.0),  # dull eye glints
}
del PALETTE_COLORS["BH_Bark"]

CLIPS = ["gs_1", "boss_slam", "cast_heavy", "boss_roar"]


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def torso_rows():
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    return [
        (zh - 0.16, 0.33, 0.26, 0.25, 0.0, 0.0),
        (zh - 0.02, 0.38, 0.36, 0.27, 0.05, 0.0),
        (zs + 0.08, 0.43, 0.46, 0.29, 0.12, -0.02),       # the pot belly
        (zc - 0.02, 0.44, 0.44, 0.30, 0.1, -0.02),
        (zc + 0.18, 0.46, 0.34, 0.34, 0.06, 0.02),
        (zn - 0.14, 0.50, 0.28, 0.38, 0.03, 0.06),        # hunched upper back
        (zn - 0.04, 0.42, 0.22, 0.34, 0.0, 0.08),
        (zn + 0.04, 0.2, 0.17, 0.2, 0.0, 0.05),
    ]


HEAD = [  # tiny head: (dz, rx, ryf, ryb, keel, cy) — sits forward and low; underbite jaw wider than the skull
    (-0.06, 0.08, 0.08, 0.06, 0.0, -0.07),
    (-0.03, 0.15, 0.17, 0.10, 0.10, -0.07),
    (0.02, 0.16, 0.18, 0.12, 0.10, -0.06),
    (0.07, 0.14, 0.15, 0.13, 0.06, -0.05),
    (0.12, 0.13, 0.14, 0.14, 0.04, -0.04),
    (0.17, 0.13, 0.13, 0.14, 0.0, -0.035),
    (0.22, 0.115, 0.11, 0.13, 0.0, -0.03),
    (0.26, 0.08, 0.08, 0.09, 0.0, -0.028),
    (0.285, 0.035, 0.035, 0.04, 0.0, -0.028),
]


def build(body: Body):
    add = body.add
    TW = K.torso_w(PROPS)
    V, F = torso_loft(torso_rows(), n=24, p=2.2, cap0=True, cap1=False)
    tor = M.Part(V, F, "BH_Skin", name="torso")
    K.jitter(tor, 0.006, seed=2)
    add(tor, weights=TW)
    zc, zs, zn = L["chest"], L["spine"], L["chest"] + PROPS["chest_len"]
    # navel + scars + hair patches on the back/shoulders
    add(K.blob((0, -0.49, zs + 0.06), 0.03, "BH_Shadow", scale=(1, 0.4, 1.2), n=6, rings=4), weights=TW)
    for (x, z, a) in ((0.18, zc + 0.12, 30), (-0.22, zc - 0.05, -20)):
        add(K.rtube([(x - 0.1 * math.cos(math.radians(a)), -0.43, z - 0.1 * math.sin(math.radians(a))),
                     (x, -0.46, z), (x + 0.1 * math.cos(math.radians(a)), -0.43, z + 0.1 * math.sin(math.radians(a)))],
                    0.013, "BH_Flesh", n=5), weights=TW)
    rng = np.random.default_rng(5)
    for i in range(7):
        x = (rng.random() - 0.5) * 0.6
        z = zn - 0.3 + 0.25 * rng.random()
        add(K.jitter(K.blob((x, 0.36 + 0.03 * rng.random(), z), 0.08 + 0.04 * rng.random(), "BH_Hair",
                            scale=(1.2, 0.3, 0.9), n=7, rings=4), 0.01, seed=i), weights=TW)

    loincloth(body)

    for s in ("L", "R"):
        K.leg(body, s, [(0.24, 0.25), (0.22, 0.23), (0.17, 0.18), (0.16, 0.16), (0.17, 0.18), (0.12, 0.13)],
              "BH_Skin", bow=0.03, n=14, top_up=0.08)
        K.bare_foot(body, s, "BH_Skin", length=0.52, width=0.13, height=0.12, claw_mat="BH_Bone", toes=3,
                    toe_r=0.042)
        K.arm(body, s, [(0.19, 0.2), (0.17, 0.18), (0.14, 0.15), (0.14, 0.14), (0.15, 0.14), (0.1, 0.095)],
              "BH_Skin", n=14, deltoid=0.2)
        K.hand(body, s, "BH_Skin", scale=2.6, claws="BH_Bone")
        # iron shackle cuff with a broken chain stub
        fa, ha = body.head("forearm." + s), body.head("hand." + s)
        d = normalize(ha - fa)
        q = fa + (ha - fa) * 0.8
        V, F = M.tube([q - d * 0.06, q + d * 0.06], [(0.14, 0.14)] * 2, n=12, up=(0, -1, 0))
        add(M.bevel(M.Part(V, F, "BH_Rust", name="shackle"), 0.01, 1), "forearm." + s)
        for j in range(2):
            c = q + np.array([0, 0.0, -0.17 - 0.1 * j])
            add(link(c, 0.06, 0.02, rotz=90 * j), "forearm." + s)

    head(body)
    collar(body)
    K.weapon_to_socket(body, "R", club())


def link(c, r, t, rotz=0.0, axis_up=True):
    """One chain link: flattened torus around Z (long axis vertical)."""
    pts = [np.array([r * 0.6 * math.cos(a), 0.0, r * math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 11)]
    V, F = M.tube(pts, [(t, t)] * len(pts), n=5, up=(0, 1, 0), cap0=False, cap1=False)
    p = M.Part(V, F, "BH_Rust", name="link")
    p.rot(Rz(rotz)).move(c)
    return p


def loincloth(body):
    add = body.add
    zh = L["hips"]
    V, F = torso_loft([(zh - 0.3, 0.34, 0.28, 0.26, 0.0), (zh - 0.15, 0.37, 0.33, 0.27, 0.0),
                       (zh + 0.0, 0.39, 0.37, 0.28, 0.03)], n=22)
    add(M.Part(V, F, "BH_Cloth_Primary", name="seat"), weights=K.seat_w(body, zh - 0.02, zh - 0.3, 0.75))
    belt = K.rtube([(0.4 * math.cos(a), (0.38 if math.sin(a) < 0 else 0.29) * math.sin(a), zh + 0.0)
                    for a in np.linspace(0, 2 * math.pi, 21)], 0.03, "BH_Leather", n=6, up=(0, 0, 1), cap=False)
    add(belt, "hips")
    for sgn in (-1, 1):
        def fn(u, v, sgn=sgn):
            x = (u - 0.5) * (0.42 - 0.08 * v)
            z = zh - 0.02 - 0.62 * v
            y = sgn * ((0.38 if sgn < 0 else 0.3) + 0.04 * v) + 0.012 * math.sin(u * 11 + v * 4)
            return (x, y, z)
        V, F = M.grid(fn, 6, 6)
        fl = M.Part(V, F, "BH_Cloth_Primary", name="flap")
        if sgn > 0:
            fl.flip()
        fl.V[-6:, 2] += np.array([0.0, 0.05, -0.02, 0.04, -0.03, 0.02])
        add(M.solidify(fl, 0.02, offset=1.0), weights=K.seat_w(body, zh - 0.05, zh - 0.62, 0.75, center_w=0.05))


def head(body):
    add = body.add
    z0 = L["head"]
    H = K.head_rows(HEAD, z0)
    zn = L["neck"]
    # thick neck, almost hidden by the trapezius
    V, F = M.tube([(0, 0.06, zn - 0.08), (0, 0.0, zn + 0.05), (0, -0.05, z0 + 0.06)],
                  [(0.2, 0.19), (0.18, 0.17), (0.14, 0.14)], n=14, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="neck"),
        weights=K.zspec_w([(zn - 0.02, "chest"), (zn + 0.04, "neck"), (z0 - 0.01, "neck"), (z0 + 0.05, "head")]))
    V, F = torso_loft(H, n=20, p=2.2, cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Skin", name="head"), "head")
    # brow, small deep eyes, squashed nose
    zb = z0 + 0.13
    yb = K.front_of(H, 0, zb)
    add(K.rtube([(-0.11, yb + 0.05, zb - 0.01), (0, yb - 0.01, zb + 0.005), (0.11, yb + 0.05, zb - 0.01)], 0.032,
                "BH_Skin", n=7, up=(0, -1, 0)), "head")
    for sx in (1, -1):
        ye = K.front_of(H, 0.05, z0 + 0.105)
        add(K.blob((sx * 0.052, ye + 0.005, z0 + 0.105), 0.025, "BH_Shadow", scale=(1.2, 0.5, 0.7), n=8, rings=4),
            "head")
        add(K.blob((sx * 0.052, ye - 0.004, z0 + 0.105), 0.01, "BH_Emissive", n=6, rings=4), "head")
    yn = K.front_of(H, 0, z0 + 0.07)
    add(K.blob((0, yn - 0.01, z0 + 0.07), 0.04, "BH_Skin", scale=(1.3, 0.8, 0.9), n=8, rings=5), "head")
    # underbite: lower lip ridge in front of the upper jaw + upward teeth
    zm = z0 + 0.0
    ym = K.front_of(H, 0, zm)
    add(K.rtube([(x, K.front_of(H, x, zm) - 0.012, zm + 4 * x * x) for x in np.linspace(-0.12, 0.12, 9)], 0.022,
                "BH_Flesh", n=6), "head")
    for x, hgt in ((-0.085, 0.07), (-0.035, 0.04), (0.03, 0.045), (0.09, 0.075)):
        b = np.array([x, K.front_of(H, x, zm) - 0.018, zm + 0.01])
        add(K.cone(b, b + (0, -0.004, hgt), 0.017, "BH_Bone", n=5), "head")
    # small ears
    for sx in (1, -1):
        rx, cy = K.side_of(H, z0 + 0.09)
        add(K.ear((sx * (rx - 0.01), cy + 0.01, z0 + 0.09), 0.09, 0.08, "BH_Skin", out=(sx, 0.3, 0.1),
                  up=(0, 0, 1), thick=0.02), "head")
    # patchy hair tufts on the crown
    for (x, y, z, r) in ((0.05, 0.02, 0.25, 0.05), (-0.06, 0.06, 0.22, 0.045), (0.0, 0.09, 0.2, 0.04)):
        add(K.jitter(K.blob((x, y - 0.03, z0 + z), r, "BH_Hair", scale=(1.2, 1.2, 0.5), n=7, rings=4), 0.006, seed=3),
            "head")


def collar(body):
    """Broken iron slave collar around the neck (gap on the right) + a chain hanging down the chest."""
    zn = L["neck"]
    c = np.array([0, 0.0, zn + 0.02])
    pts = []
    for a in np.linspace(math.radians(-60), math.radians(235), 16):   # open between 235..300 deg (right front)
        pts.append(c + np.array([0.27 * math.cos(a), 0.25 * math.sin(a) + 0.02, 0.0]))
    V, F = M.tube(pts, [(0.045, 0.06)] * len(pts), n=8, up=(0, 0, 1), p=3.0)
    col = M.bevel(M.Part(V, F, "BH_Rust", name="collar"), 0.008, 1)
    W = K.zspec_w([(zn - 0.2, "chest"), (zn + 0.1, "chest")])
    body.add(col, weights=lambda V: [{"chest": 0.6, "neck": 0.4}] * len(V))
    # rivets / studs
    for a in np.linspace(math.radians(-40), math.radians(215), 7):
        q = c + np.array([0.3 * math.cos(a), 0.28 * math.sin(a) + 0.02, 0.0])
        body.add(K.blob(q, 0.022, "BH_DarkSteel", n=6, rings=4), weights=lambda V: [{"chest": 0.6, "neck": 0.4}] * len(V))
    # hanging chain: from the front ring down over the belly (links rigid to chest)
    top = c + np.array([0.06, -0.3, -0.03])
    body.add(K.rtube([top + 0.05 * np.array([math.cos(a), 0, math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 11)],
                     0.016, "BH_Rust", n=5, cap=False), weights=lambda V: [{"chest": 0.6, "neck": 0.4}] * len(V))
    q = top + np.array([0, 0, -0.08])
    rows = torso_rows()
    for j in range(8):
        z = q[2] - 0.1 * j
        y = K.front_of(rows, abs(q[0]), max(z, rows[0][0] + 0.01), p=2.2) - 0.035
        body.add(link((q[0] + 0.012 * math.sin(j), y, z), 0.065, 0.017, rotz=90 * (j % 2)), weights=K.torso_w(PROPS))


def club():
    """Tree-trunk club: grip at origin, handle down to -0.55 (two-hand grip), trunk thickening to a knotted head at
    +1.45, three iron bands and iron spikes."""
    parts = []
    prof = [(0, -0.62), (0.07, -0.62), (0.075, -0.55), (0.06, -0.4), (0.062, 0.0), (0.075, 0.3), (0.1, 0.6),
            (0.14, 0.9), (0.17, 1.15), (0.18, 1.35), (0.15, 1.5), (0.08, 1.57), (0.0, 1.58)]
    V, F = M.lathe(prof, 12)
    tr = M.Part(V, F, "BH_Wood", name="trunk")
    K.jitter(tr, 0.01, seed=8, axis_scale=(1, 1, 0.3))
    tr.warp(lambda v: (v[0] + 0.03 * math.sin(v[2] * 3.0), v[1] + 0.02 * math.sin(v[2] * 2.1 + 1), v[2]))
    parts.append(tr)
    # knots / stubs of broken branches
    for (z, a, l) in ((0.7, 40, 0.12), (1.05, 200, 0.14), (1.3, 110, 0.1)):
        r = 0.1 + 0.08 * (z - 0.6)
        d = np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), 0.4])
        b = np.array([0.03 * math.sin(z * 3), 0.02 * math.sin(z * 2.1 + 1), z]) + d * r * 0.6
        parts.append(K.rtube([b, b + normalize(d) * l], [0.05, 0.035], "BH_Wood", n=7))
    for z, r in ((0.2, 0.078), (0.95, 0.165), (1.3, 0.19)):
        V, F = M.lathe([(0, z - 0.04), (r, z - 0.04), (r + 0.012, z), (r, z + 0.04), (0, z + 0.04)], 12)
        band = M.Part(V, F, "BH_DarkSteel", name="band")
        band.move((0.03 * math.sin(z * 3), 0.02 * math.sin(z * 2.1 + 1), 0))
        parts.append(band)
    for k in range(7):
        a = 2 * math.pi * k / 7
        z = 1.12 + 0.12 * (k % 2)
        d = np.array([math.cos(a), math.sin(a), 0.15])
        b = np.array([0.03 * math.sin(z * 3), 0.02 * math.sin(z * 2.1 + 1), z]) + d * 0.16
        parts.append(K.cone(b, b + normalize(d) * 0.1, 0.025, "BH_DarkSteel", n=5))
    for z0, z1 in ((-0.5, -0.3), (-0.12, 0.12)):
        V, F = M.lathe([(0, z0), (0.07, z0), (0.07, z1), (0, z1)], 10)
        parts.append(M.Part(V, F, "BH_Leather", name="wrap"))
    return parts
