"""Barnacle Hulk (bh-012, Builder A; Saltmouth Deeps brute): a hunched giant sea-thing ~2.5 m tall. Huge shoulders and
a high back crusted with barnacle colonies, branching coral and hanging weed; a small head sunk low between the
shoulders with a jutting underbite jaw, stubby tusks and teal eyes; grey-green drowned hide; rotten sailcloth wrapped
round the waist and tied off; a heavy rusted ship-chain draped from the left shoulder across the chest and back to the
right hip; huge bare hands and feet. Weapon (rigid on weapon.R, two-handed): a rusted ship's anchor held by the shank
near the ring, crown and flukes forward (the striking end). Kit: enemy_bandit_cutthroat / enemy_ghoul_brute / kit_deeps."""
import math
import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep, M_align_z
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_ghoul_brute as GB
import enemy_hollow_soldier as HS
import kit_a_common as A
import kit_deeps as D

SCALE = 1.45
PROPS = proportions(SCALE, shoulder_x=0.255 * SCALE, upper_len=0.31 * SCALE, fore_len=0.3 * SCALE,
                    hip_x=0.125 * SCALE, clav_drop=0.07 * SCALE)
PREVIEW_HEIGHT = 2.9
PALETTE = "barnacle_hulk"
PALETTE_COLORS = {
    "BH_Skin": ((0.22, 0.29, 0.28), 0.0, 0.45, None, 0.0, 1.0),            # drowned grey-green hide
    "BH_Flesh": ((0.13, 0.17, 0.17), 0.0, 0.5, None, 0.0, 1.0),            # darker mottling / lips
    "BH_Bone": ((0.72, 0.72, 0.66), 0.0, 0.85, None, 0.0, 1.0),            # barnacles, tusks
    "BH_Stone": ((0.28, 0.31, 0.3), 0.0, 0.92, None, 0.0, 1.0),            # crust patches
    "BH_Horn": ((0.62, 0.46, 0.42), 0.0, 0.8, None, 0.0, 1.0),             # bleached coral
    "BH_Fur": ((0.06, 0.15, 0.07), 0.0, 0.55, None, 0.0, 1.0),             # hanging weed / kelp
    "BH_Cloth_Primary": ((0.3, 0.29, 0.24), 0.0, 0.92, None, 0.0, 1.0),    # rotten sailcloth
    "BH_Leather": ((0.26, 0.23, 0.16), 0.0, 0.9, None, 0.0, 1.0),          # rope ties
    "BH_Rust": ((0.28, 0.14, 0.07), 0.45, 0.8, None, 0.0, 1.0),            # anchor, chain
    "BH_DarkSteel": ((0.1, 0.1, 0.1), 0.8, 0.6, None, 0.0, 1.0),
    "BH_Shadow": ((0.015, 0.025, 0.03), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": D.TEAL,                                                 # eyes
}
CLIPS = ["gs_1", "gs_2", "boss_slam", "boss_charge", "cast_heavy"]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


# (z, rx, ry_front, ry_back, keel, cy): barrel chest, massive shoulders, a high barnacled hump
TORSO = [
    (0.92, 0.175, 0.13, 0.13, 0.0, 0.0),
    (1.0, 0.185, 0.15, 0.13, 0.0, -0.01),
    (1.1, 0.2, 0.16, 0.14, 0.02, -0.025),
    (1.2, 0.225, 0.16, 0.17, 0.03, -0.035),
    (1.3, 0.26, 0.155, 0.23, 0.04, -0.04),
    (1.39, 0.285, 0.14, 0.27, 0.02, -0.04),
    (1.46, 0.27, 0.12, 0.29, 0.0, -0.03),
    (1.52, 0.225, 0.1, 0.28, 0.0, -0.01),
    (1.575, 0.16, 0.08, 0.23, 0.0, 0.02),
    (1.615, 0.09, 0.05, 0.16, 0.0, 0.05),
    (1.64, 0.03, 0.02, 0.07, 0.0, 0.07),
]
TW = K.zspec_w([(0.99, "hips"), (1.1, "spine"), (1.22, "spine"), (1.32, "chest")])
HEAD_DY, HEAD_DZ = -0.2, -0.15
HEAD = [
    (1.572, 0.035, 0.03, 0.03, 0.0, -0.082),
    (1.59, 0.075, 0.075, 0.05, 0.0, -0.07),     # jutting jaw
    (1.625, 0.086, 0.085, 0.07, 0.04, -0.045),
    (1.66, 0.084, 0.075, 0.085, 0.04, -0.022),
    (1.695, 0.08, 0.07, 0.09, 0.02, -0.012),
    (1.725, 0.08, 0.074, 0.088, 0.1, -0.008),
    (1.755, 0.07, 0.06, 0.08, 0.0, -0.0),
    (1.78, 0.048, 0.04, 0.058, 0.0, 0.004),
    (1.795, 0.022, 0.02, 0.03, 0.0, 0.006),
]


def hs(pts):
    return np.asarray(pts, float) + np.array([0, HEAD_DY, HEAD_DZ])


def surf(f, z, g=0.0):
    """Point + outward normal on the torso at ring fraction f, height z."""
    q = K.ring_frac(TORSO, z, g, [f], p=2.2)[0]
    a = 2 * math.pi * f - math.pi / 2
    return q, normalize(np.array([math.cos(a), math.sin(a), 0.25]))


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft(K.rows_between(TORSO, 0.92, 1.64, n_extra=6), n=36, p=2.2, cap0=True, cap1=True)
    sb.add(M.Part(V, F, "BH_Skin", name="torso"), weights=TW)
    V, F = M.sphere(0.19, 12, 7, center=(0, front_y(TORSO, 0, 1.1) + 0.07, 1.08), scale=(0.95, 0.5, 0.6))
    sb.add(M.Part(V, F, "BH_Skin", name="belly"), weights=TW)
    for sx in (1, -1):           # pectoral slabs
        V, F = M.sphere(0.11, 10, 6, center=(sx * 0.11, front_y(TORSO, sx * 0.11, 1.36) + 0.05, 1.36),
                        scale=(1.0, 0.45, 0.7))
        sb.add(M.Part(V, F, "BH_Skin", name="pec"), weights=TW)
    V, F = M.tube([(0, 0.03, 1.4), (0, -0.05, 1.45), (0, -0.12, 1.47), (0, -0.16, 1.48)],
                  [(0.11, 0.1), (0.1, 0.095), (0.085, 0.08), (0.065, 0.06)], n=12, up=(0, 0, 1))
    sb.add(M.Part(V, F, "BH_Skin", name="neck"), weights=lambda V: [
        {"chest": 1.0} if v[1] > -0.05 else ({"neck": 1.0} if v[1] > -0.12 else {"neck": 0.5, "head": 0.5})
        for v in V])
    head(sb)
    # arms: massive, bare; big fists
    for s in ("L", "R"):
        K.bare_arm(sb, s, r_up=0.068, r_fore=0.062, r_wrist=0.048, bulk=1.3)
        K.add_fist(sb, s, "BH_Skin", "BH_Skin", scale=1.45)
        GB.claws(sb, s)
    K.pelvis_seat(sb, "BH_Cloth_Primary", g=0.04)
    legs(sb)
    GB.feet(sb)
    sailcloth(sb)
    growth(sb)
    chain(sb)
    K.add_weapon(sb, "R", anchor(1.3))


# ================================================================================================= head
def head(sb):
    rows = [(r[0] + HEAD_DZ,) + tuple(r[1:5]) + (r[5] + HEAD_DY,) for r in HEAD]
    V, F = torso_loft(rows, n=20, p=2.1, cap0=True, cap1=True)
    sb.add(M.Part(V, F, "BH_Skin", name="head"), "head")
    V, F = M.tube(hs([(-0.07, -0.072, 1.722), (0.0, -0.09, 1.728), (0.07, -0.072, 1.722)]), [(0.022, 0.016)] * 3,
                  n=6, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Flesh", name="brow"), "head")
    for sx in (1, -1):
        c = hs([(sx * 0.032, -0.078, 1.7)])[0]
        V, F = M.sphere(0.015, 8, 5, center=c, scale=(1.2, 0.6, 0.8))
        sb.add(M.Part(V, F, "BH_Shadow", name="socket"), "head")
        V, F = M.sphere(0.0085, 6, 4, center=c + (0, -0.007, 0), scale=(1.2, 0.7, 0.9))
        sb.add(M.Part(V, F, "BH_Emissive", name="eye"), "head")
        # gill slits on the neck sides
        for k in range(3):
            q = hs([(sx * 0.08, -0.01 + 0.02 * k, 1.63 - 0.012 * k)])[0]
            V, F = M.box(0.006, 0.012, 0.04, center=q)
            sb.add(M.Part(V, F, "BH_Shadow", name="gill").rot(Rx(20), center=q), "head")
    V, F = M.sphere(0.02, 8, 5, center=hs([(0, -0.09, 1.672)])[0], scale=(1.2, 0.7, 0.7))
    sb.add(M.Part(V, F, "BH_Flesh", name="nose"), "head")
    c = hs([(0, -0.1, 1.61)])[0]
    V, F = M.sphere(0.045, 10, 5, center=c, scale=(1.15, 0.35, 0.3))
    sb.add(M.Part(V, F, "BH_Shadow", name="mouth"), "head")
    for k, x in enumerate((-0.045, -0.02, 0.02, 0.045)):
        h = 0.035 if k in (0, 3) else 0.016
        V, F = M.lathe([(0, 0), (0.008, 0.003), (0.0, h)], 5)
        sb.add(M.Part(V, F, "BH_Bone", name="tusk").move(hs([(x, -0.112, 1.598)])[0]), "head")
    # a crown of barnacles on the skull
    for prt in D.barnacle_cluster(hs([(0.0, 0.01, 1.785)])[0], (0.0, 0.2, 1.0), 0.06, count=6, seed=77, rmin=0.012,
                                  rmax=0.02, sides=5):
        sb.add(prt, "head")


# ================================================================================================= legs / cloth
def legs(sb):
    for s in ("L", "R"):
        th, sh = "thigh." + s, "shin." + s
        h, k, a = sb.head(th), sb.head(sh), sb.tail(sh)
        V, F = M.tube([h + (0, 0, 0.05), h + (k - h) * 0.45, k, k + (a - k) * 0.4, a + (0, 0, 0.03)],
                      [(0.11, 0.115), (0.1, 0.105), (0.078, 0.085), (0.075, 0.08), (0.055, 0.06)], n=14, up=(0, -1, 0))
        sb.add(M.Part(V, F, "BH_Skin", name="leg"), weights=sb.seg([th, sh], power=10))
        for prt in D.barnacle_cluster(k + (a - k) * 0.45 + np.array([0.02 if s == "L" else -0.03, -0.07, 0.0]),
                                      (0.3 if s == "L" else -0.3, -1, 0), 0.05, count=5, seed=90 + len(s) + (s == "L"),
                                      rmin=0.01, rmax=0.02, sides=5):
            sb.add(prt, sh)


def sailcloth(sb):
    """Rotten sailcloth wrapped round the waist: a tube skirt in 4 panels to the knees, ragged, tied with rope."""
    for side, sgn in (("L", 1), ("R", -1)):
        for back in (False, True):
            rings = []
            for z in np.linspace(0.62, 1.04, 6):
                t = (1.04 - z) / 0.42
                fr = np.linspace(0.005, 0.25, 8) if not back else np.linspace(0.25, 0.495, 8)
                rows = [(z, 0.19 + 0.05 * t + 0.02, 0.15 + 0.05 * t + 0.02, 0.14 + 0.06 * t + 0.02, 0.0)]
                pts = K.ring_frac(rows * 2, z, 0.0, fr, p=2.2)
                if t > 0.99:
                    for j in range(len(pts)):
                        pts[j, 2] += HS.ragged(j / 7, 1.7 + back + sgn, 0.1, 3)
                if sgn < 0:
                    pts[:, 0] *= -1
                rings.append(pts)
            if sgn < 0:
                rings = [r[::-1] for r in rings]
            V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
            import enemy_ashen_cultist as C
            sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="sail"), 0.01, offset=1.0),
                   weights=C.robe_panel_w(sb, side, back, leg_max=0.7))
    # rope ties
    for z in (1.02, 0.95):
        ring = K.ring_frac(TORSO, z, 0.045 + (1.02 - z) * 0.4, np.linspace(0, 1, 25)[:-1], p=2.2)
        ring = np.vstack([ring, ring[:1]])
        V, F = M.tube(ring, [(0.014, 0.014)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
        sb.add(M.Part(V, F, "BH_Leather", name="rope"), "hips")
    p, _ = K.on_ring(TORSO, 1.0, 0.07, 0.1)
    V, F = M.sphere(0.03, 8, 5, center=p)
    sb.add(M.Part(V, F, "BH_Leather", name="knot"), "hips")
    for dx in (0.015, -0.02):     # hanging corner of the sail
        sb.add(A.rag_strip(p + (dx, -0.01, -0.01), (dx * 3, -0.2, -1), 0.3, 0.08, "BH_Cloth_Primary", out=(0, -1, 0),
                           seed=dx * 50), weights=sb.skirt(1.0, 0.6, max_leg=0.5, center_w=0.05))


# ================================================================================================= growth
def growth(sb):
    rng = np.random.default_rng(3)
    # big barnacle colonies on the hump, shoulder tops and upper back
    spots = [(0.5, 1.45, 0.12, 14), (0.4, 1.35, 0.09, 9), (0.6, 1.33, 0.09, 9), (0.47, 1.25, 0.08, 7),
             (0.33, 1.47, 0.08, 7), (0.67, 1.47, 0.08, 7), (0.55, 1.56, 0.07, 6)]
    for i, (f, z, r, n) in enumerate(spots):
        q, nn = surf(f, z)
        for prt in D.barnacle_cluster(q, nn, r, count=n + 3, seed=10 + i, rmin=0.02, rmax=0.042, sides=5):
            sb.add(prt, weights=TW)
    for s, sx in (("L", 1), ("R", -1)):
        sh = sb.head("upper_arm." + s)
        w = sb.seg(["chest", "shoulder." + s, "upper_arm." + s], power=7)
        for prt in D.barnacle_cluster(sh + (sx * 0.02, 0.03, 0.09), (sx * 0.4, 0.2, 1.0), 0.1, count=12, seed=30 + sx,
                                      rmin=0.018, rmax=0.04, sides=5):
            sb.add(prt, weights=w)
        # weed hanging off the shoulder and down the arm
        for k in range(4):
            top = sh + np.array([sx * (0.03 + 0.03 * k), -0.06 + 0.05 * k, 0.07])
            for prt in D.kelp(top, (sx * 0.25, 0.1 * (k - 1.5), -1.0), 0.28 + 0.08 * (k % 2), 0.04, "BH_Fur",
                              out=(sx, 0.0, 0.3), amp=0.02, seed=k + sx):
                sb.add(prt, "upper_arm." + s)
        # barnacles on the forearm
        el, wr = sb.head("forearm." + s), sb.head("hand." + s)
        d = normalize(wr - el)
        o = normalize(np.array([sx * 1.0, 0.3, 0.0]) - d * np.dot(np.array([sx * 1.0, 0.3, 0.0]), d))
        for prt in D.barnacle_cluster(el + (wr - el) * 0.4 + o * 0.075, o, 0.06, count=6, seed=40 + sx, rmin=0.012,
                                      rmax=0.022, sides=5):
            sb.add(prt, "forearm." + s)
    # coral branches rising from the hump
    for k, (f, z, ln) in enumerate(((0.45, 1.5, 0.12), (0.56, 1.44, 0.1), (0.38, 1.4, 0.09), (0.62, 1.52, 0.1),
                                    (0.5, 1.36, 0.08), (0.3, 1.52, 0.08))):
        q, nn = surf(f, z)
        for prt in D.coral(q - nn * 0.015, nn * 0.9 + np.array([0, 0, 0.5]), ln, 0.03, "BH_Horn", seed=50 + k,
                           depth=2, spread=42, n=5, branches=3 if k < 2 else 2):
            sb.add(prt, "chest")
    # weed curtains down the back
    for k in range(6):
        f = 0.36 + 0.28 * k / 5
        q, nn = surf(f, 1.42 - 0.04 * (k % 2), 0.01)
        for prt in D.kelp(q, (0, 0.35, -1.0), 0.3 + 0.12 * rng.random(), 0.045, "BH_Fur", out=nn, amp=0.02,
                          seed=k * 1.9, bladders="BH_Fur" if k % 2 else None):
            sb.add(prt, weights=TW)


def chain(sb):
    """Heavy ship-chain from the left shoulder, across the chest to the right hip and back up behind."""
    front = [(0.2, None, 1.5), (0.12, None, 1.38), (0.0, None, 1.26), (-0.12, None, 1.14), (-0.2, None, 1.04)]
    back = [(-0.2, None, 1.04), (-0.12, None, 1.18), (0.0, None, 1.32), (0.12, None, 1.44), (0.2, None, 1.5)]
    g = 0.03
    pts = [np.array([x, front_y(TORSO, x, z) - g - (0.03 if z < 1.2 else 0.0), z]) for x, _, z in front]
    pts += [np.array([-0.24, 0.0, 1.02])]
    pts += [np.array([x, back_y(TORSO, x, z) + g + (0.02 if z > 1.3 else 0.0), z]) for x, _, z in back]
    pts += [np.array([0.22, 0.0, 1.56]), pts[0]]
    # resample into link centres
    P = np.array(pts)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    L = 0.07
    n = int(cum[-1] / L)
    for i in range(n):
        s = i * L
        j = min(np.searchsorted(cum, s) - 1, len(seg) - 1)
        j = max(j, 0)
        t = (s - cum[j]) / seg[j]
        c = P[j] * (1 - t) + P[j + 1] * t
        d = normalize(P[j + 1] - P[j])
        nrm = normalize(np.array([c[0], c[1] + 0.02, 0.0]))
        side = normalize(np.cross(d, nrm))
        plane = nrm if i % 2 else side          # alternate link orientation
        loop = []
        for a in np.linspace(0, 2 * math.pi, 9)[:-1]:
            loop.append(c + d * 0.042 * math.cos(a) + plane * 0.024 * math.sin(a))
        loop.append(loop[0])
        V, F = M.tube(loop, [(0.009, 0.009)] * len(loop), n=4, up=tuple(np.cross(d, plane)), cap0=False, cap1=False)
        sb.add(M.Part(V, F, "BH_Rust", name="link"), weights=TW)


# ================================================================================================= anchor
def anchor(s=1.0):
    """Weapon space (grip at origin, +Z toward the crown, flukes on +-X). Ring + stock at the grip end (-Z)."""
    parts = []
    V, F = M.lathe([(0, -0.52), (0.03, -0.52), (0.034, -0.4), (0.03, 0.2), (0.038, 0.9), (0.05, 1.0), (0.0, 1.05)], 8)
    parts.append(M.Part(V, F, "BH_Rust", name="shank"))
    # rope wrap where the hands hold it
    V, F = M.lathe([(0, -0.34), (0.038, -0.34), (0.04, -0.1), (0.038, 0.14), (0, 0.14)], 8)
    parts.append(M.Part(V, F, "BH_Leather", name="grip"))
    # ring at the end + stock (crossbar along Y)
    ring = [np.array([0.0, 0.08 * math.cos(a) * 0.0, -0.58 + 0.07 * math.sin(a)]) + np.array([0.07 * math.cos(a), 0, 0])
            for a in np.linspace(0, 2 * math.pi, 13)]
    parts.append(A.tube(ring, 0.014, "BH_Rust", n=5, up=(0, 1, 0), cap=False))
    V, F = M.tube([(0, -0.24, -0.44), (0, 0, -0.45), (0, 0.24, -0.44)], [(0.022, 0.022), (0.028, 0.028), (0.022, 0.022)],
                  n=6, up=(0, 0, 1))
    parts.append(M.Part(V, F, "BH_DarkSteel", name="stock"))
    for sy in (1, -1):
        V, F = M.sphere(0.032, 6, 4, center=(0, sy * 0.25, -0.44))
        parts.append(M.Part(V, F, "BH_DarkSteel", name="stockend"))
    # crown + two arms curving back toward the grip, triangular flukes
    V, F = M.sphere(0.07, 8, 5, center=(0, 0, 1.02), scale=(1.4, 0.8, 0.9))
    parts.append(M.Part(V, F, "BH_Rust", name="crown"))
    for sx in (1, -1):
        arm = [(sx * 0.34 * math.sin(math.radians(100 * t)), 0.0, 1.03 - 0.3 * (1 - math.cos(math.radians(100 * t))))
               for t in np.linspace(0, 1, 7)]
        V, F = M.tube(arm, [(0.04, 0.03), (0.038, 0.028), (0.034, 0.026), (0.03, 0.024), (0.027, 0.022),
                            (0.024, 0.02), (0.02, 0.018)], n=6, up=(0, 1, 0))
        parts.append(M.Part(V, F, "BH_Rust", name="arm"))
        tip = np.array(arm[-1])
        outline = [(0.0, 0.0), (sx * 0.1, 0.1), (sx * 0.05, -0.2), (-sx * 0.02, -0.18)]
        o = np.array(outline)
        area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
        if area < 0:
            o = o[::-1]
        V, F = M.prism(o, 0.02, axis="y")
        parts.append(M.bevel(M.Part(V, F, "BH_Rust", name="fluke").move(tip + np.array([0, 0, 0.02])), 0.004, 1))
        # point of the fluke (bill)
        parts.append(A.taper([tip + (sx * 0.02, 0, -0.16), tip + (sx * 0.045, 0, -0.26)], 0.018, 0.002, "BH_Rust", n=4))
    # barnacles + weed on the crown
    parts += D.barnacle_cluster((0.0, -0.05, 0.95), (0, -1, 0.1), 0.07, count=5, seed=61, rmin=0.012, rmax=0.022,
                                sides=5)
    parts += D.barnacle_cluster((0.05, 0.04, 0.7), (0.4, 1, 0), 0.05, count=3, seed=62, rmin=0.01, rmax=0.018, sides=5)
    parts += D.kelp((0.05, 0.0, 0.98), (0.3, 0.1, -1.0), 0.3, 0.04, "BH_Fur", out=(0, -1, 0), amp=0.02)
    for p in parts:
        p.V = p.V * s
    return parts
