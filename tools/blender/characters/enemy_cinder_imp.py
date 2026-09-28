"""Cinder Imp (Builder C, bh-012, Emberforge Depths): a small wiry imp (~1.1 m to the horn tips) with charcoal skin
split by glowing lava seams, small curled horns, long pointed ears, ember eyes and a wide glowing grin. Small leathery
bat wings are fixed on its back (rigid on the chest), a long tail (rigid on the hips) ends in a flame-shaped tip.
It carries a small iron fork-brand with a white-hot tip like a wand (right hand). Blinking fire caster."""
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

S = 0.62
PROPS = proportions(
    S,
    pelvis_h=0.50, hip_h=0.475, knee_h=0.265, ankle_h=0.05, ball_fwd=0.1, ball_h=0.02, toe_len=0.055,
    heel_back=0.04, hip_x=0.072,
    hips_len=0.07, spine_len=0.12, chest_len=0.15, neck_len=0.05, head_len=0.18,
    clav_x0=0.025, clav_drop=0.03, shoulder_x=0.112, upper_len=0.2, fore_len=0.19, hand_len=0.075, grip_x=0.055,
    grip_drop=0.012,
)
L = K.levels(PROPS)
PREVIEW_HEIGHT = 1.2

PALETTE = "cinder_imp"
PALETTE_COLORS = {
    "BH_Skin": ((0.052, 0.046, 0.046), 0.0, 0.62, None, 0.0, 1.0),        # charcoal skin
    "BH_Flesh": ((0.16, 0.035, 0.02), 0.0, 0.55, None, 0.0, 1.0),         # wing membrane (dark ember red)
    "BH_Horn": ((0.1, 0.07, 0.06), 0.0, 0.4, None, 0.0, 1.0),             # horns, claws, wing spars
    "BH_Shadow": ((0.018, 0.014, 0.014), 0.0, 0.8, None, 0.0, 1.0),       # soot grooves, mouth
    "BH_Leather": ((0.11, 0.06, 0.035), 0.0, 0.7, None, 0.0, 1.0),        # loin wrap, belt
    "BH_DarkSteel": ((0.1, 0.095, 0.095), 1.0, 0.5, None, 0.0, 1.0),      # fork-brand iron
    "BH_Bone": ((0.62, 0.52, 0.36), 0.0, 0.5, None, 0.0, 1.0),            # teeth
    "BH_Emissive": E.EMBER,
}

CLIPS = ["wand_1", "cast_quick", "cast_weapon", "dagger_1"]


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def torso_rows():
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    return [
        (zh - 0.05, 0.076, 0.054, 0.058, 0.0, 0.0),
        (zh + 0.02, 0.078, 0.058, 0.058, 0.03, 0.0),
        (zs + 0.03, 0.068, 0.054, 0.052, 0.05, 0.0),      # pinched waist
        (zs + 0.09, 0.078, 0.06, 0.058, 0.08, 0.0),
        (zc + 0.05, 0.094, 0.065, 0.066, 0.07, 0.006),
        (zn - 0.05, 0.106, 0.06, 0.07, 0.03, 0.012),
        (zn - 0.015, 0.094, 0.05, 0.062, 0.0, 0.014),
        (zn + 0.01, 0.044, 0.036, 0.042, 0.0, 0.01),
    ]


HEAD = [  # (dz, rx, ryf, ryb, keel, cy): pointed chin, wide grinning cheeks, round cranium
    (-0.036, 0.016, 0.018, 0.018, 0.0, -0.03),
    (-0.022, 0.038, 0.048, 0.034, 0.1, -0.026),
    (0.0, 0.062, 0.062, 0.046, 0.08, -0.02),
    (0.025, 0.069, 0.066, 0.058, 0.06, -0.015),
    (0.055, 0.071, 0.066, 0.072, 0.04, -0.008),
    (0.09, 0.074, 0.062, 0.08, 0.02, -0.002),
    (0.125, 0.07, 0.055, 0.078, 0.0, 0.004),
    (0.152, 0.055, 0.042, 0.062, 0.0, 0.008),
    (0.172, 0.028, 0.022, 0.032, 0.0, 0.01),
]


def build(body: Body):
    add = body.add
    rng = np.random.default_rng(12)
    TW = K.torso_w(PROPS)
    rows = torso_rows()
    V, F = torso_loft(rows, n=20, p=2.2, cap0=True, cap1=False)
    add(M.Part(V, F, "BH_Skin", name="torso"), weights=TW)
    # rib ridges on the flanks + a sternum groove (wiry look)
    for sx in (1, -1):
        for k in range(3):
            z = L["chest"] - 0.01 + 0.035 * k
            pts = [E.torso_point(rows, f, z - 0.01 * abs(f - sx * 0.12) * 4, 0.0)[0] for f in
                   np.linspace(sx * 0.06, sx * 0.2, 5) % 1.0]
            add(K.rtube(pts, 0.0045, "BH_Skin", n=4), weights=TW)
    # lava seams over chest, belly and back
    for p in E.torso_cracks(rows, rng, 6, (-0.22, 0.22), (L["spine"], L["neck"] - 0.02), r=0.0068, steps=5,
                            step=0.022, groove="BH_Shadow"):
        add(p, weights=TW)
    for p in E.torso_cracks(rows, rng, 4, (0.32, 0.68), (L["spine"], L["neck"] - 0.02), r=0.0068, steps=5,
                            step=0.022, groove="BH_Shadow"):
        add(p, weights=TW)

    loin(body)

    # ---- wiry legs with knobby knees, clawed three-toed feet
    for s in ("L", "R"):
        sx = 1 if s == "L" else -1
        K.leg(body, s, [(0.036, 0.038), (0.029, 0.031), (0.023, 0.025), (0.025, 0.025), (0.026, 0.028),
                        (0.016, 0.018)], "BH_Skin", bow=0.02, n=10)
        K.bare_foot(body, s, "BH_Skin", length=0.17, width=0.036, height=0.04, claw_mat="BH_Horn", toes=3,
                    toe_r=0.011)
        k = body.head("shin." + s)
        add(K.blob(k + (sx * 0.004, -0.024, 0.0), 0.024, "BH_Skin", n=8, rings=5),
            weights=lambda V, s=s: [{"thigh." + s: 0.5, "shin." + s: 0.5}] * len(V))
        h, a = body.head("thigh." + s), body.tail("shin." + s)
        for p in E.limb_cracks(h, k, 0.03, rng, 2, r=0.006, face=(sx * 0.6, -1, 0)):
            add(p, "thigh." + s)
        for p in E.limb_cracks(k, a, 0.024, rng, 2, r=0.0055, face=(0, -1, 0)):
            add(p, "shin." + s)

    # ---- long thin arms, clawed hands, an iron cuff on the left wrist
    for s in ("L", "R"):
        K.arm(body, s, [(0.026, 0.026), (0.022, 0.023), (0.019, 0.02), (0.021, 0.021), (0.022, 0.021),
                        (0.016, 0.015)], "BH_Skin", n=10, deltoid=0.028)
        K.hand(body, s, "BH_Skin", scale=0.82, claws="BH_Horn")
        sh, el, wr = body.head("upper_arm." + s), body.head("forearm." + s), body.head("hand." + s)
        for p in E.limb_cracks(sh, el, 0.022, rng, 2, r=0.0052):
            add(p, "upper_arm." + s)
        for p in E.limb_cracks(el, wr, 0.02, rng, 2, r=0.005):
            add(p, "forearm." + s)
    fa, ha = body.head("forearm.L"), body.head("hand.L")
    d = normalize(ha - fa)
    q = fa + (ha - fa) * 0.78
    V, F = M.tube([q - d * 0.022, q + d * 0.022], [(0.026, 0.026)] * 2, n=10, up=(0, -1, 0))
    add(M.bevel(M.Part(V, F, "BH_DarkSteel", name="cuff"), 0.003, 1), "forearm.L")
    for lk in E.chain(q + (0, 0, -0.03), 2, 0.012, 0.0035, direction=(0.2, 0, -1)):
        add(lk, "forearm.L")

    head(body, rng)
    wings(body)
    tail(body)
    K.weapon_to_socket(body, "R", fork_brand())


def loin(body):
    add = body.add
    zh = L["hips"]
    V, F = torso_loft([(zh - 0.06, 0.08, 0.058, 0.062, 0.0), (zh - 0.02, 0.082, 0.06, 0.062, 0.0),
                       (zh + 0.03, 0.08, 0.06, 0.06, 0.0)], n=18)
    add(M.Part(V, F, "BH_Leather", name="seat"), weights=K.seat_w(body, zh + 0.02, zh - 0.07, 0.7))
    for sgn in (-1, 1):
        def fn(u, v, sgn=sgn):
            x = (u - 0.5) * (0.09 - 0.03 * v)
            z = zh + 0.0 - 0.12 * v
            y = sgn * (0.064 + 0.012 * v)
            return (x, y, z)
        V, F = M.grid(fn, 4, 4)
        fl = M.Part(V, F, "BH_Leather", name="flap")
        if sgn > 0:
            fl.flip()
        fl.V[-4:, 2] += np.array([0.0, 0.012, -0.008, 0.01])
        add(M.solidify(fl, 0.006, offset=1.0), weights=K.seat_w(body, zh, zh - 0.12, 0.7, center_w=0.02))
    belt = K.rtube([(0.084 * math.cos(a), 0.064 * math.sin(a), zh + 0.028) for a in np.linspace(0, 2 * math.pi, 15)],
                   0.007, "BH_Leather", n=5, up=(0, 0, 1), cap=False)
    add(belt, "hips")
    # iron ring + a smouldering coal pouch on the belt
    add(K.rtube([(0.05, -0.07, zh + 0.02) + 0.014 * np.array([math.cos(a), 0, math.sin(a)])
                 for a in np.linspace(0, 2 * math.pi, 9)], 0.0035, "BH_DarkSteel", n=4, cap=False), "hips")
    V, F = M.sphere(0.028, 8, 5, center=(-0.075, -0.03, zh - 0.0), scale=(1, 0.8, 1.1))
    add(M.Part(V, F, "BH_Leather", name="pouch"), "hips")
    add(K.blob((-0.075, -0.03, zh + 0.03), 0.013, "BH_Emissive", n=6, rings=4), "hips")


def head(body, rng):
    add = body.add
    z0 = L["head"]
    H = K.head_rows(HEAD, z0)
    V, F = M.tube([(0, 0.012, L["neck"] - 0.02), (0, 0.0, L["neck"] + 0.03), (0, -0.016, z0 + 0.02)],
                  [(0.028, 0.026), (0.025, 0.024), (0.027, 0.026)], n=10, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="neck"),
        weights=K.zspec_w([(L["neck"] - 0.01, "chest"), (L["neck"] + 0.02, "neck"), (z0 + 0.0, "neck"),
                           (z0 + 0.02, "head")]))
    V, F = torso_loft(H, n=20, p=2.1, cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Skin", name="head"), "head")
    # angry brow ridges (V shape)
    zb = z0 + 0.075
    for sx in (1, -1):
        yb = K.front_of(H, 0.03, zb)
        add(K.rtube([(sx * 0.008, yb - 0.004, zb - 0.012), (sx * 0.03, yb - 0.006, zb + 0.0),
                     (sx * 0.058, yb + 0.012, zb + 0.014)], [0.008, 0.01, 0.006], "BH_Skin", n=5), "head")
    # ember eyes in soot sockets
    for sx in (1, -1):
        ye = K.front_of(H, 0.03, z0 + 0.058)
        add(K.blob((sx * 0.029, ye + 0.005, z0 + 0.058), 0.016, "BH_Shadow", scale=(1.25, 0.5, 0.7), n=8, rings=4),
            "head")
        add(K.blob((sx * 0.03, ye - 0.002, z0 + 0.058), 0.0095, "BH_Emissive", scale=(1.4, 0.6, 0.75), n=6, rings=4),
            "head")
    # small pointed nose
    yn = K.front_of(H, 0, z0 + 0.04)
    add(K.rtube([(0, yn + 0.004, z0 + 0.052), (0, yn - 0.014, z0 + 0.036), (0, yn - 0.02, z0 + 0.024)],
                [0.009, 0.008, 0.002], "BH_Skin", n=6, up=(0, 0, 1)), "head")
    # the wide grin: dark lips, a glowing mouth line and a row of small teeth, corners pulled up to the cheeks
    zm = z0 + 0.006
    xs = np.linspace(-0.058, 0.058, 11)
    lip = [(x, K.front_of(H, x, zm + 7 * x * x) - 0.0015, zm + 7 * x * x) for x in xs]
    add(K.rtube(lip, (0.0065, 0.0055), "BH_Shadow", n=5), "head")
    glow = [(x, K.front_of(H, x, zm + 7 * x * x) - 0.004, zm + 7 * x * x) for x in xs[1:-1]]
    add(K.rtube(glow, (0.0034, 0.0026), "BH_Emissive", n=5), "head")
    for x in np.linspace(-0.042, 0.042, 8):
        z = zm + 7 * x * x
        yb = K.front_of(H, x, z) - 0.004
        add(K.cone((x, yb, z + 0.004), (x, yb - 0.002, z - 0.004), 0.0035, "BH_Bone", n=4), "head")
    # seams on the face / cranium
    for pts in ([(0.05, 0.068), (0.045, 0.1), (0.03, 0.13)], [(-0.035, 0.11), (-0.05, 0.135), (-0.04, 0.155)]):
        q = [(x, K.front_of(H, x, z0 + z) + 0.001, z0 + z) for x, z in pts]
        for p in E.seam(q, np.array([0, -1.0, 0]), 0.0035, groove=None):
            add(p, "head")
    # long pointed ears swept back-up
    for sx in (1, -1):
        rx, cy = K.side_of(H, z0 + 0.06)
        root = (sx * (rx - 0.01), cy + 0.012, z0 + 0.06)
        add(K.ear(root, 0.13, 0.05, "BH_Skin", out=(sx * 1.0, 0.35, 0.45), up=(0, 0.3, 1), droop=-0.015,
                  thick=0.009, back=0.012), "head")
        add(K.ear(np.array(root) + (sx * 0.014, -0.006, 0.004), 0.09, 0.026, "BH_Flesh", out=(sx * 1.0, 0.35, 0.45),
                  up=(0, 0.3, 1), droop=-0.01, thick=0.003), "head")
    # small horns curling back from the brow corners
    for sx in (1, -1):
        b = np.array([sx * 0.04, K.front_of(H, 0.04, z0 + 0.12) + 0.02, z0 + 0.12])
        pts = [b, b + (sx * 0.02, 0.0, 0.04), b + (sx * 0.035, 0.035, 0.07), b + (sx * 0.04, 0.075, 0.07),
               b + (sx * 0.038, 0.095, 0.045), b + (sx * 0.034, 0.088, 0.028)]
        add(K.rtube(pts, [0.017, 0.014, 0.011, 0.008, 0.005, 0.0015], "BH_Horn", n=7), "head")
        for t in (0.2, 0.45):
            c = np.array(pts[1]) * (1 - t) + np.array(pts[2]) * t
            add(K.rtube([c - (0, 0, 0.003), c + (0, 0, 0.003)], 0.0165 - 0.004 * t, "BH_Shadow", n=7), "head")


def wings(body):
    """Two small bat wings, fixed half-spread behind the shoulders (rigid on the chest)."""
    add = body.add
    zc, zn = L["chest"], L["neck"]
    for sx in (1, -1):
        root = np.array([sx * 0.04, 0.07, zn - 0.035])
        wrist = np.array([sx * 0.2, 0.2, zn + 0.1])
        tips = [np.array([sx * 0.42, 0.25, zn + 0.1]), np.array([sx * 0.44, 0.27, zn - 0.05]),
                np.array([sx * 0.33, 0.25, zn - 0.19]), np.array([sx * 0.16, 0.18, zc - 0.03])]
        # spars
        add(K.rtube([root, root + (wrist - root) * 0.5 + (0, 0, 0.03), wrist], [0.013, 0.011, 0.009], "BH_Horn", n=6),
            "chest")
        for t in tips[:3]:
            add(K.rtube([wrist, wrist + (t - wrist) * 0.55 + (0, 0.01, 0.01), t], [0.0065, 0.005, 0.0015], "BH_Horn",
                        n=5), "chest")
        add(K.cone(wrist, wrist + (sx * 0.01, -0.01, 0.045), 0.008, "BH_Horn", n=5), "chest")  # thumb claw
        # membrane: fan from the root to the scalloped trailing edge
        edge = [wrist]
        for a, b in zip(tips, tips[1:]):
            mid = (a + b) / 2
            edge.append(a)
            edge.append(mid + (wrist - mid) * 0.18)
        edge.append(tips[-1])
        edge = np.array(edge)
        nv = 4
        V, F = [], []
        ne = len(edge)
        # dense resample of the edge for a smoother scallop
        fine = []
        for i in range(ne - 1):
            for t in (0.0, 0.5):
                fine.append(edge[i] * (1 - t) + edge[i + 1] * t)
        fine.append(edge[-1])
        fine = np.array(fine)
        nf = len(fine)
        nrm = normalize(np.cross(wrist - root, tips[1] - root)) * sx
        for j in range(nv + 1):
            v = j / nv
            for i in range(nf):
                q = root + (fine[i] - root) * v
                q = q + nrm * 0.02 * math.sin(math.pi * v) * (1 - abs(i / (nf - 1) - 0.5))
                V.append(q)
        for j in range(nv):
            for i in range(nf - 1):
                a, b = j * nf + i, (j + 1) * nf + i
                F.append((a, a + 1, b + 1, b))
        mem = M.Part(np.array(V), F, "BH_Flesh", name="membrane")
        if sx < 0:
            mem.flip()
        add(M.solidify(mem, 0.005, offset=0.0), "chest")
        # glowing veins in the membrane
        for t in tips[:3]:
            m = wrist + (t - wrist) * 0.5
            add(K.rtube([wrist + (m - wrist) * 0.3 + nrm * 0.004, m + (root - m) * 0.25 + nrm * 0.004],
                        0.0028, "BH_Emissive", n=4), "chest")


def tail(body):
    """Long tail from the base of the spine, sweeping back and down, curling up to a flame tip (rigid on hips)."""
    add = body.add
    zh = L["hips"]
    pts = np.array([(0, 0.035, zh - 0.02), (0, 0.1, zh - 0.06), (0.01, 0.2, zh - 0.14), (0.03, 0.31, zh - 0.2),
                    (0.06, 0.42, zh - 0.2), (0.08, 0.5, zh - 0.14), (0.085, 0.54, zh - 0.06), (0.08, 0.545, zh + 0.0)])
    rad = [0.024, 0.02, 0.016, 0.013, 0.011, 0.009, 0.0075, 0.006]
    add(K.rtube(pts, rad, "BH_Skin", n=8, up=(1, 0, 0)), "hips")
    # seam along the top of the tail
    top = [p + (0, 0, r * 0.9) for p, r in zip(pts[1:6], rad[1:6])]
    for p in E.seam(top, np.array([0, 0, 1.0]), 0.0035, groove=None):
        add(p, "hips")
    # flame tip: spade-like tongue of fire rising from the end
    for p in E.flame(pts[-1] + (0, 0, -0.004), 0.1, 0.022, tongues=3, seed=4, axis=(0.05, 0.1, 1)):
        add(p, "hips")


def fork_brand():
    """Small iron fork-brand: iron rod, leather-wrapped grip, a two-prong fork head glowing white-hot at the tips.
    Weapon space: grip at origin, +Z along the rod."""
    parts = []
    V, F = M.lathe([(0, -0.1), (0.011, -0.1), (0.012, -0.085), (0.0085, -0.07), (0.0085, 0.3), (0, 0.305)], 8)
    parts.append(E.P(V, F, "BH_DarkSteel", "rod"))
    V, F = M.lathe([(0, -0.055), (0.0115, -0.055), (0.0115, 0.055), (0, 0.055)], 8)
    parts.append(E.P(V, F, "BH_Leather", "wrap"))
    V, F = M.lathe([(0, -0.118), (0.014, -0.11), (0.016, -0.1), (0, -0.092)], 8)
    parts.append(E.P(V, F, "BH_DarkSteel", "knob"))
    # fork head: crossbar + two prongs, the upper third of each prong glowing
    parts.append(K.rtube([(-0.045, 0, 0.29), (-0.02, 0, 0.3), (0.02, 0, 0.3), (0.045, 0, 0.29)], 0.0085, "BH_DarkSteel",
                         n=6))
    for sx in (1, -1):
        parts.append(K.rtube([(sx * 0.045, 0, 0.288), (sx * 0.045, 0, 0.34)], 0.0078, "BH_DarkSteel", n=6))
        parts.append(K.rtube([(sx * 0.045, 0, 0.338), (sx * 0.043, 0, 0.38), (sx * 0.036, 0, 0.405)],
                             [0.0078, 0.0065, 0.0012], "BH_Emissive", n=6))
    # ember held between the prongs
    parts.append(K.blob((0, 0, 0.345), 0.022, "BH_Emissive", n=8, rings=5, scale=(1, 1, 1.25)))
    parts += E.flame((0, 0, 0.36), 0.07, 0.014, tongues=2, seed=9)
    return parts
