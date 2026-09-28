"""Warband Chieftain (bh-013, Builder B1 "warriors"; big humanoid, rally leader): an old orc war-leader, much bigger
and more decorated than the orc_reaver. Green-grey skin, a massive jaw with huge upward tusks, red war paint (three
claw stripes over the eyes), an iron spiked crown and a long black braid. Heavy fur-and-iron armour: a riveted iron
cuirass painted with red claw marks, a thick dark fur mantle over the shoulders, two big iron pauldrons with bone
spikes (a trophy skull bolted to the left one), gold arm rings, spiked iron bracers, a fur war-skirt over iron
tassets, a wide belt with a skull buckle and three trophy skulls hanging on cords. A tall war-banner pole strapped to
his back (harness crossing the chest) rises above his head with a RIGID red-and-black clan banner (swallowtail, black
border, black tusked-skull emblem on both faces) and a skull + iron spearhead finial. Weapon: a huge notched
two-handed cleaver (weapon.R).

~2.45 m to the crown spikes (custom proportions, modelled at true size, greenskin kit); the banner top is ~3.2 m.
Clips: axe_1, axe_2, axe_heavy, war_cry, boss_roar, boss_slam (+ the enemy base set)."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft, dome, smoothstep, interp_rows, torso_ring  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz, R_axis  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as K  # noqa: E402
import kit_a_common as A  # noqa: E402

S = 1.3
PROPS = proportions(
    S,
    pelvis_h=1.3, hip_h=1.25, knee_h=0.69, ankle_h=0.11, hip_x=0.165,
    hips_len=0.14, spine_len=0.24, chest_len=0.36, neck_len=0.1, head_len=0.26,
    clav_x0=0.07, clav_drop=0.07, shoulder_x=0.36, upper_len=0.41, fore_len=0.38, hand_len=0.145, grip_x=0.105,
    grip_drop=0.025, ball_fwd=0.17, ball_h=0.03, toe_len=0.09, heel_back=0.07,
)
L = K.levels(PROPS)
PREVIEW_HEIGHT = 3.4

PALETTE = "warband_chieftain"
PALETTE_COLORS = {
    "BH_Skin": ((0.2, 0.25, 0.15), 0.0, 0.55, None, 0.0, 1.0),            # green-grey
    "BH_Flesh": ((0.09, 0.1, 0.06), 0.0, 0.55, None, 0.0, 1.0),            # lips / mouth
    "BH_Fur": ((0.25, 0.19, 0.13), 0.0, 0.95, None, 0.0, 1.0),             # brown-grey fur mantle / skirt
    "BH_DarkSteel": ((0.2, 0.19, 0.18), 0.9, 0.5, None, 0.0, 1.0),         # iron
    "BH_Rust": ((0.27, 0.13, 0.065), 0.5, 0.8, None, 0.0, 1.0),
    "BH_Steel": ((0.52, 0.52, 0.5), 1.0, 0.35, None, 0.0, 1.0),            # cleaver edge
    "BH_Leather": ((0.09, 0.05, 0.028), 0.0, 0.68, None, 0.0, 1.0),
    "BH_Horn": ((0.1, 0.08, 0.06), 0.0, 0.9, None, 0.0, 1.0),              # trousers
    "BH_Bone": ((0.66, 0.6, 0.47), 0.0, 0.6, None, 0.0, 1.0),              # tusks, skulls, spikes
    "BH_Cloth_Primary": ((0.56, 0.04, 0.03), 0.0, 0.85, None, 0.0, 1.0),   # clan red (banner, paint)
    "BH_Cloth_Secondary": ((0.025, 0.022, 0.02), 0.0, 0.9, None, 0.0, 1.0),  # clan black
    "BH_Wood": ((0.13, 0.08, 0.045), 0.0, 0.75, None, 0.0, 1.0),
    "BH_Hair": ((0.03, 0.025, 0.02), 0.0, 0.65, None, 0.0, 1.0),
    "BH_Gold": ((0.75, 0.52, 0.2), 1.0, 0.35, None, 0.0, 1.0),             # arm rings, crown studs
    "BH_Shadow": ((0.03, 0.025, 0.02), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((1.0, 0.4, 0.1), 0.0, 0.4, (1.0, 0.36, 0.08), 5.0, 1.0),  # eye glints
}
CLIPS = ["axe_1", "axe_2", "axe_heavy", "war_cry", "boss_roar", "boss_slam"]


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def torso_rows():
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    return [
        (zh - 0.13, 0.225, 0.155, 0.16, 0.0, 0.0),
        (zh + 0.03, 0.235, 0.175, 0.16, 0.02, 0.0),
        (zs + 0.08, 0.245, 0.19, 0.16, 0.06, 0.0),
        (zc + 0.03, 0.28, 0.2, 0.17, 0.1, 0.0),
        (zc + 0.18, 0.33, 0.21, 0.19, 0.12, 0.005),
        (zn - 0.08, 0.345, 0.2, 0.2, 0.08, 0.012),
        (zn - 0.015, 0.27, 0.16, 0.17, 0.03, 0.02),
        (zn + 0.045, 0.12, 0.11, 0.115, 0.0, 0.015),
    ]


ROWS = torso_rows()


def grown(rows, g):
    return [(r[0], r[1] + g, r[2] + g, r[3] + g, r[4], r[5]) for r in rows]


def band(rows, z0, z1, g_out, g_in, mat, n=26, name="band"):
    def ring(z, g):
        r = interp_rows(rows, z)
        return torso_ring(z, r[1] + g, r[2] + g, r[3] + g, r[4], 2.3, n, cy=r[5])
    loops = [ring(z0, g_in), ring(z0, g_out), ring(z1, g_out), ring(z1, g_in)]
    nn = len(loops[0])
    V = np.vstack(loops)
    F = []
    for k in range(4):
        a, b = k * nn, ((k + 1) % 4) * nn
        for i in range(nn):
            j = (i + 1) % nn
            F.append((a + i, a + j, b + j, b + i))
    return M.Part(V, F, mat, name=name)


def surf(rows, x, z, g, back=False):
    """Point on the (grown) torso surface at (x, z), front or back."""
    y = K.front_of(grown(rows, g), x, z, p=2.3)
    if back:
        r = interp_rows(grown(rows, g), z)
        ax = min(abs(x) / r[1], 0.999)
        y = r[5] + r[3] * (1 - ax ** 2.3) ** (1 / 2.3)
    return np.array([x, y, z])


# ================================================================================================= build
def build(body: Body):
    add = body.add
    TW = K.torso_w(PROPS)
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    V, F = torso_loft(ROWS, n=24, p=2.2, cap0=True, cap1=False)
    add(M.Part(V, F, "BH_Skin", name="torso"), weights=TW)

    cuirass(body)
    fur_mantle(body)
    for s in ("L", "R"):
        pauldron(body, s)
    belt_and_skirt(body)

    # ---- legs: heavy trousers, fur-wrapped shins, iron knee guards, iron-capped boots
    for s in ("L", "R"):
        K.leg(body, s, [(0.13, 0.135), (0.115, 0.12), (0.095, 0.1), (0.092, 0.096), (0.095, 0.1), (0.07, 0.074)],
              "BH_Horn", n=12)
        sh = "shin." + s
        k, a = body.head(sh), body.tail(sh)
        V, F = M.tube([a + (0, 0, 0.03), a + (k - a) * 0.45, a + (k - a) * 0.85],
                      [(0.09, 0.095), (0.112, 0.118), (0.105, 0.11)], n=12, up=(0, -1, 0))
        fw = M.Part(V, F, "BH_Fur", name="shinfur")
        fw.V = fw.V + (fw.V - np.array([k[0], k[1], fw.V[:, 2].mean()])) * np.array([1, 1, 0]) * \
            (0.08 * np.sin(fw.V[:, 2] * 60 + fw.V[:, 0] * 30))[:, None]
        add(fw, sh)
        for u in (0.3, 0.62):
            q = a + (k - a) * u
            V, F = M.tube([q + (0, 0, 0.015), q - (0, 0, 0.015)], [(0.116, 0.122)] * 2, n=12, up=(0, -1, 0))
            add(M.Part(V, F, "BH_Leather", name="binding"), sh)
        V, F = dome(k + (0, -0.075, 0.03), (0, -1, 0.2), 0.09, a_max=65, n=12, rings=4)
        add(M.solidify(M.Part(V, F, "BH_DarkSteel", name="knee"), 0.014, offset=-1.0),
            weights=lambda V, s=s: [{"thigh." + s: 0.35, "shin." + s: 0.65}] * len(V))
        add(K.cone(k + (0, -0.15, 0.05), k + (0, -0.24, 0.08), 0.025, "BH_Bone", n=6),
            weights=lambda V, s=s: [{"thigh." + s: 0.35, "shin." + s: 0.65}] * len(V))
        K.bare_foot(body, s, "BH_Leather", length=0.38, width=0.075, height=0.1, toes=0)
        hx = PROPS["hip_x"] * (1 if s == "L" else -1)
        V, F = M.box(0.17, 0.38, 0.03, center=(hx, -0.09, 0.015))
        add(M.bevel(M.Part(V, F, "BH_DarkSteel", name="sole"), 0.008, 1), "foot." + s)
        V, F = dome((hx, -0.2, 0.03), (0, -1, 0.6), 0.085, a_max=80, n=10, rings=4, scale=(1.0, 1.0, 0.8))
        add(M.solidify(M.Part(V, F, "BH_DarkSteel", name="toecap"), 0.01, offset=-1.0), "toe." + s)

    # ---- arms: heavy bare skin arms, gold rings, spiked iron bracers
    for s in ("L", "R"):
        K.arm(body, s, [(0.105, 0.11), (0.095, 0.1), (0.08, 0.084), (0.082, 0.082), (0.086, 0.08), (0.062, 0.06)],
              "BH_Skin", n=12, deltoid=0.125)
        K.hand(body, s, "BH_Skin", scale=1.7)
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        sh_, el, wr = body.head(ua), body.head(fa), body.head(ha)
        for u in (0.55, 0.66):
            q = sh_ + (el - sh_) * u
            d = normalize(el - sh_)
            V, F = M.tube([q - d * 0.022, q + d * 0.022], [(0.108, 0.112)] * 2, n=12, up=(0, -1, 0))
            add(M.Part(V, F, "BH_Gold", name="armring"), ua)
        V, F = M.tube([el + (wr - el) * 0.3, el + (wr - el) * 0.68, el + (wr - el) * 1.02],
                      [(0.098, 0.094), (0.095, 0.09), (0.08, 0.076)], n=12, up=(0, -1, 0))
        add(M.bevel(M.Part(V, F, "BH_DarkSteel", name="bracer"), 0.005, 1, angle=50), fa)
        for u in (0.42, 0.62, 0.82):
            q = el + (wr - el) * u
            add(K.cone(q + (0, 0, 0.08), q + (0, 0, 0.14), 0.02, "BH_Bone", n=6), fa)

    head(body)
    banner(body)
    K.weapon_to_socket(body, "R", cleaver())


# ------------------------------------------------------------------------------------------------- armour
def cuirass(body):
    add = body.add
    TW = K.torso_w(PROPS, shoulder_blend=False)
    zs, zc, zn = L["spine"], L["chest"], L["neck"]
    z0, z1 = zs + 0.02, zn - 0.03
    rows = [r for r in grown(ROWS, 0.028) if z0 <= r[0] <= z1]
    rows = [(z0,) + tuple(interp_rows(grown(ROWS, 0.028), z0)[1:])] + rows + \
           [(z1,) + tuple(interp_rows(grown(ROWS, 0.028), z1)[1:])]
    V, F = torso_loft(rows, n=26, p=2.2, cap0=False, cap1=False)
    add(M.bevel(M.Part(V, F, "BH_DarkSteel", name="cuirass"), 0.005, 1, angle=50), weights=TW)
    add(band(ROWS, z0 - 0.01, z0 + 0.035, 0.046, 0.02, "BH_Rust", name="cuirass_rim"), weights=TW)
    add(band(ROWS, z1 - 0.035, z1 + 0.005, 0.042, 0.018, "BH_Rust", name="cuirass_top"), weights=TW)
    # rivets along the rims + a centre ridge
    for z in (z0 + 0.012, z1 - 0.015):
        for x in np.linspace(-0.26, 0.26, 7):
            add(K.blob(surf(ROWS, x, z, 0.05), 0.014, "BH_DarkSteel", n=6, rings=4), weights=TW)
    ridge = [surf(ROWS, 0.0, z, 0.031) for z in np.linspace(z0 + 0.04, z1 - 0.04, 6)]
    add(K.rtube(ridge, 0.016, "BH_DarkSteel", n=6, up=(0, -1, 0)), weights=TW)
    # three red claw marks painted diagonally across the chest (thin shells on the plate)
    for k in range(3):
        x0 = -0.2 + 0.1 * k
        pts = [surf(ROWS, x0 + 0.12 * t, zc + 0.28 - 0.3 * t, 0.034) for t in np.linspace(0, 1, 6)]
        add(K.rtube(pts, [(0.012, 0.004), (0.022, 0.004), (0.026, 0.004), (0.024, 0.004), (0.016, 0.004),
                          (0.006, 0.003)], "BH_Cloth_Primary", n=4, up=(0, -1, 0), p=3.0), weights=TW)
    # banner harness: two leather straps crossing on the chest to the shoulders, a bracket at the back
    for sx in (1, -1):
        pts = [surf(ROWS, sx * 0.24, zn - 0.02, 0.05), surf(ROWS, sx * 0.1, zc + 0.2, 0.045),
               surf(ROWS, -sx * 0.08, zc + 0.02, 0.045), surf(ROWS, -sx * 0.22, zs + 0.06, 0.05)]
        add(K.rtube(pts, (0.035, 0.009), "BH_Leather", n=6, up=(0, -1, 0), p=3.0), weights=TW)
        back = [surf(ROWS, sx * 0.24, zn - 0.02, 0.05, back=True), surf(ROWS, 0.14, zc + 0.12, 0.05, back=True)]
        add(K.rtube(back, (0.035, 0.009), "BH_Leather", n=6, up=(0, 1, 0), p=3.0), weights=TW)
        add(K.blob(pts[1], 0.03, "BH_DarkSteel", scale=(1, 0.5, 1), n=8, rings=4), weights=TW)


def fur_mantle(body):
    """Thick dark fur mantle over the shoulders and upper back (rigid to the chest), shaggy lumps along its edge."""
    add = body.add
    zn = L["neck"]
    rng = np.random.default_rng(11)
    loop = []
    for a in np.linspace(0, 2 * math.pi, 29):
        rx, ry = 0.3, 0.215
        z = zn - 0.045 + 0.02 * math.cos(a) - 0.06 * max(0.0, -math.sin(a)) ** 2
        loop.append((rx * math.cos(a), 0.015 + ry * math.sin(a), z))
    V, F = M.tube(loop, [(0.1, 0.068)] * len(loop), n=10, up=(0, 0, 1), cap0=False, cap1=False)
    V = V * (1 + 0.05 * np.sin(V[:, 0] * 61 + V[:, 1] * 47) * np.cos(V[:, 2] * 83))[:, None]
    add(M.Part(V, F, "BH_Fur", name="mantle_collar"), "chest")
    for k in range(14):
        a = 2 * math.pi * k / 14 + rng.random() * 0.3
        c = (0.33 * math.cos(a), 0.015 + 0.24 * math.sin(a), zn - 0.09 + 0.02 * math.cos(a) - 0.04 * max(0.0, -math.sin(a)))
        add(K.jitter(K.blob(c, 0.06 + 0.02 * rng.random(), "BH_Fur", scale=(1.0, 1.0, 1.3), n=7, rings=4), 0.008,
                     seed=k), "chest")
    # back cape of fur down to the waist (behind the banner pole foot)
    def fn(u, v):
        half = 0.27 + 0.05 * v
        x = (u - 0.5) * 2 * half
        z = zn - 0.02 + (L["spine"] + 0.02 - (zn - 0.02)) * v - 0.05 * abs(math.sin(u * math.pi * 5)) * v
        r = interp_rows(ROWS, max(min(z, zn - 0.02), L["spine"]))
        ax = min(abs(x) / (r[1] + 0.05), 0.999)
        y = r[5] + (r[3] + 0.06) * (1 - ax ** 2.3) ** (1 / 2.3) + 0.03 * v
        return (x, y, z)
    V, F = M.grid(fn, 9, 6)
    add(M.solidify(M.Part(V, F, "BH_Fur", name="mantle_back"), 0.045, offset=1.0),
        weights=K.zspec_w([(L["spine"] + 0.05, "spine"), (L["chest"] + 0.15, "chest")]))


def pauldron(body, s):
    ua = "upper_arm." + s
    sh = body.head(ua)
    sx = 1 if s == "L" else -1
    axis = normalize(np.array([0.7 * sx, 0.0, 1.0]))
    c = sh + np.array([0.02 * sx, 0.0, 0.03])
    parts = []
    for i, (r, off) in enumerate(((0.2, 0.0), (0.175, 0.08), (0.15, 0.15))):
        cc = c + np.array([0.03 * i * sx, 0, -off])
        V, F = dome(cc, axis, r, a_max=70, n=16, rings=5, scale=(1.0, 1.15, 1.0))
        parts.append(M.solidify(M.Part(V, F, "BH_DarkSteel" if i == 0 else "BH_Rust", name="pauldron"), 0.016,
                                offset=-1.0))
    # rim rivets and three bone spikes
    for k, (a, l) in enumerate(((-38, 0.2), (0, 0.27), (38, 0.2))):
        base = c + R_axis((1, 0, 0), a) @ (axis * 0.19)
        dirn = normalize(base - c + axis * 0.1)
        parts.append(K.cone(base - dirn * 0.03, base + dirn * l, 0.042, "BH_Bone", n=7))
    for p in parts:
        body.add(p, weights=lambda V, s=s: [{"shoulder." + s: 0.3, "upper_arm." + s: 0.7}] * len(V))
    if s == "L":   # trophy skull bolted to the front of the left pauldron
        q = c + np.array([0.1, -0.16, -0.05])
        for prt in A.skull_charm(q, 0.075, face=(0.3, -1, 0.1)):
            body.add(prt, weights=lambda V: [{"shoulder.L": 0.3, "upper_arm.L": 0.7}] * len(V))


def belt_and_skirt(body):
    add = body.add
    zh = L["hips"]
    # iron tassets (sides) under a fur war-skirt (front + back)
    for k in range(6):
        ang = math.radians([-30, 0, 30, 150, 180, 210][k])
        ca, sa = math.cos(ang), math.sin(ang)

        def fn(u, v, ca=ca, sa=sa):
            w = 0.16 + 0.03 * v
            tx, ty = -sa, ca
            px = (0.27 + 0.06 * v) * ca + (u - 0.5) * w * tx
            py = (0.2 + 0.06 * v) * sa + (u - 0.5) * w * ty
            return (px, py, zh - 0.0 - 0.38 * v)
        V, F = M.grid(fn, 3, 4)
        fl = M.Part(V, F, "BH_DarkSteel", name="tasset")
        if (np.cross(fl.V[1] - fl.V[0], fl.V[3] - fl.V[0])[:2] @ np.array([ca, sa])) < 0:
            fl.flip()
        add(M.solidify(fl, 0.014, offset=1.0), weights=K.seat_w(body, zh - 0.02, zh - 0.42, 0.8, center_w=0.03))
    # seat
    V, F = torso_loft([(zh - 0.2, 0.23, 0.165, 0.17, 0.0), (zh - 0.05, 0.24, 0.175, 0.175, 0.0)], n=22)
    add(M.Part(V, F, "BH_Horn", name="seat"), weights=K.seat_w(body, zh - 0.04, zh - 0.2, 0.7))
    # fur war-skirt: two overlapping flaps per side (front + back), each following its own leg
    for sgn in (-1, 1):
        for hx in (-1, 1):
            def fn(u, v, sgn=sgn, hx=hx):
                x = hx * (0.012 + u * (0.19 - 0.03 * v))
                z = zh + 0.02 - 0.55 * v
                y = sgn * (0.2 + 0.06 * v + 0.012 * (hx > 0)) + 0.015 * math.sin(u * 9 + v * 5 + hx)
                return (x, y, z)
            V, F = M.grid(fn, 4, 6)
            fl = M.Part(V, F, "BH_Fur", name="furskirt")
            if (sgn > 0) != (hx < 0):
                fl.flip()
            fl.V[-4:, 2] += np.array([0.03, -0.03, 0.04, -0.02]) * (1 if hx > 0 else -1)
            add(M.solidify(fl, 0.03, offset=1.0), weights=side_leg_w("thigh.L" if hx > 0 else "thigh.R", zh - 0.02,
                                                                  zh - 0.5, 0.8))
    # wide belt, skull buckle, trophy skulls on cords
    V, F = torso_loft([(zh - 0.03, 0.262, 0.2, 0.19, 0.0), (zh + 0.1, 0.262, 0.205, 0.19, 0.02)], n=24)
    add(M.bevel(M.Part(V, F, "BH_Leather", name="belt"), 0.005, 1), "hips")
    V, F = M.box(0.2, 0.03, 0.16, center=(0, -0.215, zh + 0.035))
    add(M.bevel(M.Part(V, F, "BH_DarkSteel", name="buckleplate"), 0.012, 1), "hips")
    for prt in A.skull_charm((0, -0.25, zh + 0.045), 0.07, face=(0, -1, 0)):
        add(prt, "hips")
    for (ang, drop) in ((-58, 0.2), (-120, 0.16), (35, 0.18)):
        a = math.radians(ang)
        top = np.array([0.27 * math.cos(a), 0.21 * math.sin(a), zh - 0.01])
        out = normalize(np.array([math.cos(a), math.sin(a), 0.0]))
        q = top + out * 0.05 + np.array([0, 0, -drop])
        add(K.rtube([top, top + out * 0.03 + np.array([0, 0, -drop * 0.5]), q + np.array([0, 0, 0.06])], 0.008,
                    "BH_Leather", n=5), weights=K.seat_w(body, zh, zh - 0.3, 0.5, center_w=0.05))
        for prt in A.skull_charm(q, 0.06, face=out + np.array([0, 0, -0.2])):
            add(prt, weights=K.seat_w(body, zh, zh - 0.3, 0.5, center_w=0.05))


def side_leg_w(thigh, z_top, z_bot, max_leg):
    """Flap that follows one leg only: hips above z_top, blending into `thigh` (up to max_leg) toward z_bot."""
    def wfn(V):
        out = []
        for v in V:
            t = float(smoothstep(z_top, z_bot, v[2])) * max_leg
            out.append({"hips": 1 - t, thigh: t} if t > 1e-3 else {"hips": 1.0})
        return out
    return wfn


# ------------------------------------------------------------------------------------------------- head
HEAD = [  # (dz, rx, ryf, ryb, keel, cy): wide heavy jaw, big brow, low sloped skull
    (-0.05, 0.055, 0.05, 0.04, 0.0, -0.04),
    (-0.035, 0.105, 0.11, 0.065, 0.1, -0.035),
    (0.0, 0.118, 0.13, 0.078, 0.12, -0.026),
    (0.045, 0.112, 0.128, 0.095, 0.1, -0.014),
    (0.095, 0.106, 0.124, 0.113, 0.06, -0.007),
    (0.14, 0.11, 0.113, 0.123, 0.02, 0.0),
    (0.19, 0.104, 0.098, 0.12, 0.0, 0.008),
    (0.232, 0.08, 0.074, 0.098, 0.0, 0.012),
    (0.26, 0.042, 0.04, 0.054, 0.0, 0.014),
]


def head(body):
    add = body.add
    z0 = L["head"]
    H = K.head_rows(HEAD, z0, sx=1.1, sy=1.1, sz=1.05)
    zn = L["neck"]
    V, F = M.tube([(0, 0.03, zn - 0.05), (0, 0.01, zn + 0.06), (0, -0.015, z0 + 0.04)],
                  [(0.13, 0.12), (0.118, 0.108), (0.1, 0.095)], n=12, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="neck"),
        weights=K.zspec_w([(zn - 0.0, "chest"), (zn + 0.04, "neck"), (z0 - 0.01, "neck"), (z0 + 0.04, "head")]))
    V, F = torso_loft(H, n=22, p=2.2, cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Skin", name="head"), "head")
    zb = z0 + 0.13
    yb = K.front_of(H, 0, zb)
    add(K.rtube([(-0.105, yb + 0.04, zb - 0.012), (-0.045, yb - 0.006, zb + 0.006), (0, yb + 0.002, zb - 0.008),
                 (0.045, yb - 0.006, zb + 0.006), (0.105, yb + 0.04, zb - 0.012)], 0.026, "BH_Skin", n=6,
                up=(0, -1, 0)), "head")
    # eyes
    for sx in (1, -1):
        ye = K.front_of(H, 0.045, z0 + 0.1, p=2.2)
        add(K.blob((sx * 0.046, ye - 0.004, z0 + 0.1), 0.022, "BH_Shadow", scale=(1.2, 0.5, 0.6), n=8, rings=4), "head")
        add(K.blob((sx * 0.047, ye - 0.011, z0 + 0.101), 0.009, "BH_Emissive", scale=(1.3, 0.6, 0.7), n=6, rings=4),
            "head")
    # war paint: three red claw stripes running down over each eye onto the cheek + a red chin bar
    for sx in (1, -1):
        for k, dx in enumerate((-0.022, 0.0, 0.022)):
            pts = []
            for t in np.linspace(0, 1, 5):
                x = sx * (0.046 + dx + 0.01 * t)
                z = z0 + 0.155 - 0.12 * t
                pts.append((x, K.front_of(H, abs(x), z, p=2.2) + 0.001, z))
            add(K.rtube(pts, [(0.006, 0.003)] * 5, "BH_Cloth_Primary", n=4, up=(0, -1, 0), p=3.0), "head")
    # broad nose
    yn = K.front_of(H, 0, z0 + 0.065, p=2.2)
    add(K.rtube([(0, yn + 0.005, z0 + 0.11), (0, yn - 0.028, z0 + 0.065), (0, yn - 0.024, z0 + 0.04)],
                [(0.02, 0.015), (0.038, 0.022), (0.035, 0.018)], "BH_Skin", n=8, up=(0, 0, 1)), "head")
    # mouth + huge tusks
    zm = z0 + 0.005
    add(K.rtube([(x, K.front_of(H, x, zm, p=2.2) - 0.004, zm - 0.004 + 3 * x * x) for x in np.linspace(-0.08, 0.08, 7)],
                (0.009, 0.005), "BH_Flesh", n=5), "head")
    for sx in (1, -1):
        b = np.array([sx * 0.055, K.front_of(H, 0.055, zm - 0.012, p=2.2) + 0.01, zm - 0.016])
        add(K.rtube([b, b + (sx * 0.012, -0.02, 0.05), b + (sx * 0.03, -0.012, 0.1), b + (sx * 0.04, 0.01, 0.13)],
                    [0.022, 0.017, 0.009, 0.002], "BH_Bone", n=7), "head")
    # ears with iron rings
    for sx in (1, -1):
        rx, cy = K.side_of(H, z0 + 0.09)
        root = (sx * (rx - 0.012), cy + 0.02, z0 + 0.09)
        add(K.ear(root, 0.13, 0.08, "BH_Skin", out=(sx * 0.85, 0.7, 0.25), up=(0, 0, 1), thick=0.018), "head")
        for j in range(2):
            add(K.rtube([np.array(root) + (sx * (0.035 + 0.03 * j), 0.03 + 0.025 * j, -0.025) +
                         0.016 * np.array([0, math.cos(a), math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 9)],
                        0.005, "BH_Gold", n=4, cap=False), "head")
    # iron spiked crown
    zc = z0 + 0.19
    r = interp_rows(H, zc)
    V, F = M.lathe([(1.0, -0.03), (1.08, -0.026), (1.08, 0.026), (1.0, 0.03)], 22, cap=False)
    crown = M.Part(V, F, "BH_DarkSteel", name="crown")
    crown.V = crown.V * np.array([r[1] + 0.012, (r[2] + r[3]) / 2 + 0.012, 1.0]) + np.array([0, r[5] + 0.012, zc])
    add(M.solidify(crown, 0.01, offset=-1), "head")
    for k in range(7):
        a = math.radians(-90 + (k - 3) * 30)
        rr = np.array([(r[1] + 0.02) * math.cos(a), (r[2] + 0.02) * math.sin(a) + r[5] + 0.012, zc + 0.02])
        ln = 0.16 - 0.03 * abs(k - 3)
        out = normalize(np.array([math.cos(a) * 0.35, math.sin(a) * 0.35, 1.0]))
        add(K.cone(rr - out * 0.02, rr + out * ln, 0.024, "BH_DarkSteel", n=5), "head")
        add(K.blob(rr + np.array([math.cos(a), math.sin(a), 0]) * 0.008 - (0, 0, 0.012), 0.012, "BH_Gold", n=6,
                   rings=4), "head")
    # long black braid down the back of the head
    top = np.array([0.0, r[5] + r[3] + 0.0, z0 + 0.19])
    pts = [top, top + (0, 0.05, -0.08), top + (0, 0.08, -0.2), top + (0.02, 0.1, -0.33), top + (0.03, 0.12, -0.44)]
    for i in range(len(pts) - 1):
        add(K.blob((np.array(pts[i]) + pts[i + 1]) / 2, 0.034 - 0.004 * i, "BH_Hair", scale=(1.0, 1.0, 1.7), n=7,
                   rings=4), weights=K.zspec_w([(zn - 0.1, "chest"), (z0 + 0.05, "head")]))
    add(K.rtube([pts[-1] + (0, 0, 0.02), pts[-1] - (0, 0, 0.03)], 0.03, "BH_Gold", n=6),
        weights=K.zspec_w([(zn - 0.1, "chest"), (z0 + 0.05, "head")]))


# ------------------------------------------------------------------------------------------------- banner
def banner(body):
    """War-banner pole strapped to the back, rigid to the chest: wood pole with iron bands from the lower back to
    ~3.2 m, a crossbar, a rigid red swallowtail banner with a black border and a black tusked-skull emblem on both
    faces, a skull + spearhead finial."""
    add = body.add
    zs, zc = L["spine"], L["chest"]
    px = 0.13
    yb = interp_rows(ROWS, zc + 0.12)[3] + 0.13
    bot = np.array([px, yb - 0.02, zs - 0.08])
    top = np.array([px, yb - 0.02, 3.08])
    d = normalize(top - bot)
    parts = []
    parts.append(K.rtube([bot, bot + d * 0.4, top], [0.034, 0.032, 0.028], "BH_Wood", n=8))
    for t in (0.0, 0.25, 0.5, 0.78):
        q = bot + (top - bot) * t
        parts.append(K.rtube([q - d * 0.02, q + d * 0.02], 0.038, "BH_DarkSteel", n=8))
    # back bracket (iron ring + plate on the harness)
    q = bot + d * ((zc + 0.12 - bot[2]) / d[2])
    parts.append(K.rtube([q - d * 0.04, q + d * 0.04], 0.045, "BH_DarkSteel", n=8))
    V, F = M.box(0.12, 0.05, 0.14, center=(q[0] - 0.02, q[1] - 0.06, q[2]))
    parts.append(M.Part(V, F, "BH_Leather", name="bracket"))
    # finial: skull + spearhead
    parts += A.skull_charm(top + d * 0.07, 0.07, face=(0, -1, 0))
    parts.append(K.rtube([top + d * 0.15, top + d * 0.2], 0.03, "BH_DarkSteel", n=8))
    V, F = M.lathe([(0.0, 0.0), (0.045, 0.04), (0.04, 0.09), (0.0, 0.19)], 4)
    sp = M.Part(V, F, "BH_DarkSteel", name="spearhead")
    sp.V = sp.V @ M_align(d).T + top + d * 0.19
    parts.append(sp)
    # crossbar
    zt = 2.98
    cb = bot + d * ((zt - bot[2]) / d[2])
    cbf = cb + (0, -0.036, 0)
    parts.append(K.rtube([cbf + (-0.37, 0, 0), cbf + (0.37, 0, 0)], 0.018, "BH_Wood", n=6))
    for sx in (1, -1):
        parts.append(K.blob(cbf + (sx * 0.38, 0, 0), 0.03, "BH_DarkSteel", n=6, rings=4))
    # the banner: rigid swallowtail slab hanging from the crossbar, just in front of the pole
    W2, Hh, notch = 0.34, 0.64, 0.14
    outline = [(-W2, 0.0), (-W2, -Hh), (0.0, -Hh + notch), (W2, -Hh), (W2, 0.0)]
    o = np.array(outline)
    if 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1]) < 0:
        o = o[::-1]
    fy = cb[1] - 0.052            # banner plane (in front of the pole)
    org = np.array([cb[0], fy, zt - 0.015])
    V, F = M.prism(M.resample_closed(o, 40), 0.014, axis="y")
    parts.append(M.Part(V + org, F, "BH_Cloth_Primary", name="banner"))
    # black border (both faces): top, sides, tails
    def strip2d(p0, p1, w, mat, z_off=0.0):
        p0, p1 = np.array(p0), np.array(p1)
        t = normalize(p1 - p0)
        nrm = np.array([-t[1], t[0]])
        quad = [p0 + nrm * w / 2, p0 - nrm * w / 2, p1 - nrm * w / 2, p1 + nrm * w / 2]
        q = np.array(quad)
        if 0.5 * np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1]) < 0:
            q = q[::-1]
        V, F = M.prism(q, 0.02, axis="y")
        return M.Part(V + org, F, mat, name="border")
    edge = [(-W2, 0.0), (-W2, -Hh), (0.0, -Hh + notch), (W2, -Hh), (W2, 0.0), (-W2, 0.0)]
    inset = 0.028
    for (a, b) in zip(edge, edge[1:]):
        a2 = np.array(a) * np.array([(W2 - inset) / W2, 1.0]) + (0, -inset if a[1] == 0.0 else inset * 0.5)
        b2 = np.array(b) * np.array([(W2 - inset) / W2, 1.0]) + (0, -inset if b[1] == 0.0 else inset * 0.5)
        parts.append(strip2d(a2, b2, 0.04, "BH_Cloth_Secondary"))
    # emblem: black tusked skull with horns (both faces), red eye holes
    ez = -0.3
    skull_o = [(-0.1, ez + 0.1), (-0.12, ez + 0.02), (-0.08, ez - 0.07), (-0.04, ez - 0.1), (0.04, ez - 0.1),
               (0.08, ez - 0.07), (0.12, ez + 0.02), (0.1, ez + 0.1), (0.0, ez + 0.14)]
    so = np.array(skull_o)
    if 0.5 * np.sum(so[:, 0] * np.roll(so[:, 1], -1) - np.roll(so[:, 0], -1) * so[:, 1]) < 0:
        so = so[::-1]
    V, F = M.prism(so, 0.022, axis="y")
    parts.append(M.Part(V + org, F, "BH_Cloth_Secondary", name="emblem"))
    for sx in (1, -1):
        horn = [(sx * 0.09, ez + 0.07), (sx * 0.17, ez + 0.1), (sx * 0.21, ez + 0.18), (sx * 0.19, ez + 0.23),
                (sx * 0.17, ez + 0.17), (sx * 0.12, ez + 0.12)]
        ho = np.array(horn)
        if 0.5 * np.sum(ho[:, 0] * np.roll(ho[:, 1], -1) - np.roll(ho[:, 0], -1) * ho[:, 1]) < 0:
            ho = ho[::-1]
        V, F = M.prism(ho, 0.022, axis="y")
        parts.append(M.Part(V + org, F, "BH_Cloth_Secondary", name="emblem_horn"))
        tusk = [(sx * 0.05, ez - 0.08), (sx * 0.08, ez - 0.08), (sx * 0.1, ez + 0.0), (sx * 0.07, ez - 0.03)]
        to = np.array(tusk)
        if 0.5 * np.sum(to[:, 0] * np.roll(to[:, 1], -1) - np.roll(to[:, 0], -1) * to[:, 1]) < 0:
            to = to[::-1]
        V, F = M.prism(to, 0.026, axis="y")
        parts.append(M.Part(V + org, F, "BH_Bone", name="emblem_tusk"))
        V, F = M.box(0.05, 0.03, 0.04, center=(sx * 0.045, 0.0, ez + 0.03))
        parts.append(M.Part(V + org, F, "BH_Cloth_Primary", name="emblem_eye"))
    # two black tassels hanging from the crossbar ends
    for sx in (1, -1):
        t0 = cbf + (sx * 0.38, 0, -0.03)
        parts.append(K.rtube([t0, t0 + (0, 0, -0.12), t0 + (sx * 0.01, 0.01, -0.22)], [0.012, 0.018, 0.006],
                             "BH_Cloth_Secondary", n=5))
    for p in parts:
        add(p, "chest")


def M_align(d):
    from bh_body import M_align_z
    return M_align_z(normalize(d), (0, -1, 0))


# ------------------------------------------------------------------------------------------------- weapon
def cleaver():
    """Huge two-handed cleaver (weapon space: grip at origin, +Z blade, flats +-Y, edge +X): long leather-wrapped
    grip with a spiked pommel, an iron collar, a broad slab blade with a straight thick spine (-X), a squared tip and
    a notched edge (bright steel edge band), rust patches and a hanging hole near the tip."""
    parts = []
    V, F = M.lathe([(0, -0.46), (0.03, -0.46), (0.034, -0.43), (0.026, -0.4), (0.025, 0.05), (0.03, 0.08),
                    (0.0, 0.09)], 10)
    parts.append(M.Part(V, F, "BH_Wood", name="haft"))
    for z0, z1 in ((-0.12, 0.04), (-0.38, -0.2)):
        V, F = M.lathe([(0, z0), (0.029, z0), (0.029, z1), (0, z1)], 10)
        parts.append(M.Part(V, F, "BH_Leather", name="grip"))
    V, F = M.lathe([(0, -0.52), (0.045, -0.48), (0.05, -0.46), (0.0, -0.44)], 8)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="pommel"))
    parts.append(K.cone((0, 0, -0.5), (0, 0, -0.6), 0.025, "BH_DarkSteel", n=6))
    V, F = M.lathe([(0, 0.04), (0.05, 0.04), (0.06, 0.07), (0.06, 0.1), (0.045, 0.12), (0.0, 0.12)], 10)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="collar"))
    # blade outline (x, z): spine -X, edge +X with notches
    out = [(-0.06, 0.1), (-0.06, 1.12), (-0.02, 1.17), (0.29, 1.12), (0.31, 1.0), (0.3, 0.9), (0.26, 0.86),
           (0.3, 0.82), (0.29, 0.7), (0.24, 0.66), (0.28, 0.61), (0.27, 0.47), (0.23, 0.44), (0.26, 0.4),
           (0.24, 0.26), (0.18, 0.16), (0.06, 0.1)]
    o = np.array(out)
    if 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1]) < 0:
        o = o[::-1]
    V, F = M.prism(M.resample_closed(o, 60), 0.036, axis="y")
    bl = M.Part(V, F, "BH_DarkSteel", name="blade")
    bl.warp(lambda v: (v[0], v[1] * (1.0 - 0.78 * min(max((v[0] + 0.02) / 0.3, 0), 1)), v[2]))
    parts.append(M.bevel(bl, 0.003, 1, angle=50))
    # bright edge band following the notched edge
    edge = [(0.285, 1.11), (0.303, 1.0), (0.293, 0.9), (0.253, 0.86), (0.293, 0.82), (0.283, 0.7), (0.233, 0.66),
            (0.273, 0.61), (0.263, 0.47), (0.223, 0.44), (0.253, 0.4), (0.233, 0.26), (0.175, 0.17)]
    parts.append(K.rtube([(x - 0.012, 0.0, z) for x, z in edge], (0.014, 0.006), "BH_Steel", n=4, up=(1, 0, 0)))
    # spine bar
    parts.append(K.rtube([(-0.055, 0.0, 0.12), (-0.055, 0.0, 1.11)], (0.014, 0.022), "BH_DarkSteel", n=6,
                         up=(0, 1, 0)))
    # hole near the tip: dark disc + rust ring on both faces
    for sy in (1, -1):
        c = np.array([0.03, sy * 0.013, 1.03])
        parts.append(K.blob(c, 0.035, "BH_Shadow", scale=(1, 0.2, 1), n=10, rings=4))
        parts.append(K.rtube([c + 0.04 * np.array([math.cos(a), 0, math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 11)],
                             0.008, "BH_Rust", n=4, cap=False))
    # rust patches on the flats
    rng = np.random.default_rng(3)
    for (x, z) in ((0.1, 0.35), (0.02, 0.62), (0.14, 0.8), (0.0, 0.9)):
        for sy in (1, -1):
            parts.append(K.blob((x, sy * 0.012, z), 0.045 + 0.02 * rng.random(), "BH_Rust",
                                scale=(1.0, 0.15, 0.8 + 0.4 * rng.random()), n=8, rings=4))
    return parts
