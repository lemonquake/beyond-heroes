"""Goblin Skulker (Builder C): small big-eared, big-nosed goblin with mottled olive skin, a dented scavenged kettle
helmet far too big for it, a loot sack on its back, a notched knife in the right hand and clay fire-pots with burning
rags on its rope belt. Long arms, bowed legs, big feet. ~1.15 m standing (top of the helmet)."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft, smoothstep, dome  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz, R_axis  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as K  # noqa: E402

S = 0.64
PROPS = proportions(
    S,
    pelvis_h=0.50, hip_h=0.475, knee_h=0.265, ankle_h=0.052, ball_fwd=0.105, ball_h=0.02, toe_len=0.055,
    heel_back=0.04, hip_x=0.085,
    hips_len=0.07, spine_len=0.12, chest_len=0.15, neck_len=0.05, head_len=0.19,
    clav_x0=0.025, clav_drop=0.03, shoulder_x=0.12, upper_len=0.215, fore_len=0.205, hand_len=0.08, grip_x=0.06,
    grip_drop=0.013,
)
L = K.levels(PROPS)

PALETTE = "goblin_skulker"
PALETTE_COLORS = {
    "BH_Skin": ((0.13, 0.17, 0.045), 0.0, 0.6, None, 0.0, 1.0),            # olive
    "BH_Flesh": ((0.065, 0.085, 0.03), 0.0, 0.6, None, 0.0, 1.0),          # darker mottling
    "BH_Rust": ((0.20, 0.11, 0.055), 0.55, 0.75, None, 0.0, 1.0),          # the helmet
    "BH_DarkSteel": ((0.12, 0.115, 0.11), 1.0, 0.55, None, 0.0, 1.0),
    "BH_Steel": ((0.38, 0.38, 0.37), 1.0, 0.45, None, 0.0, 1.0),
    "BH_Cloth_Primary": ((0.16, 0.06, 0.03), 0.0, 0.92, None, 0.0, 1.0),   # filthy loincloth
    "BH_Cloth_Secondary": ((0.24, 0.17, 0.085), 0.0, 0.95, None, 0.0, 1.0),  # burlap loot sack
    "BH_Leather": ((0.09, 0.055, 0.03), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Stone": ((0.34, 0.12, 0.05), 0.0, 0.85, None, 0.0, 1.0),           # fired clay (fire-pots)
    "BH_Emissive": ((1.0, 0.45, 0.08), 0.0, 0.4, (1.0, 0.42, 0.06), 8.0, 1.0),  # rag flames + eyes
    "BH_Bone": ((0.55, 0.50, 0.38), 0.0, 0.6, None, 0.0, 1.0),
    "BH_Wood": ((0.10, 0.06, 0.03), 0.0, 0.75, None, 0.0, 1.0),
    "BH_Shadow": ((0.03, 0.025, 0.02), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Gold": ((0.6, 0.42, 0.16), 1.0, 0.35, None, 0.0, 1.0),
}

CLIPS = ["dagger_1", "dagger_2", "cast_quick"]


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


# torso cross-sections (z, rx, ry_front, ry_back, keel, cy): skinny chest, a little pot belly, hunched back
def torso_rows():
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    return [
        (zh - 0.05, 0.088, 0.062, 0.066, 0.0, 0.0),
        (zh + 0.02, 0.092, 0.07, 0.066, 0.05, 0.0),
        (zs + 0.03, 0.090, 0.082, 0.062, 0.12, -0.004),
        (zs + 0.09, 0.094, 0.078, 0.068, 0.10, 0.0),
        (zc + 0.05, 0.105, 0.07, 0.08, 0.04, 0.01),
        (zn - 0.05, 0.12, 0.066, 0.085, 0.02, 0.02),
        (zn - 0.015, 0.105, 0.058, 0.075, 0.0, 0.022),
        (zn + 0.01, 0.055, 0.042, 0.05, 0.0, 0.012),
    ]


HEAD = [  # (dz, rx, ryf, ryb, keel, cy) relative to the head joint; big cranium, protruding muzzle, forward jut
    (-0.030, 0.030, 0.030, 0.030, 0.0, -0.030),
    (-0.012, 0.058, 0.070, 0.040, 0.10, -0.030),
    (0.010, 0.070, 0.082, 0.052, 0.12, -0.025),
    (0.035, 0.078, 0.086, 0.066, 0.10, -0.018),
    (0.062, 0.084, 0.080, 0.080, 0.06, -0.010),
    (0.095, 0.088, 0.074, 0.088, 0.02, -0.004),
    (0.130, 0.084, 0.066, 0.086, 0.0, 0.000),
    (0.160, 0.066, 0.052, 0.070, 0.0, 0.004),
    (0.180, 0.034, 0.028, 0.038, 0.0, 0.006),
]


def build(body: Body):
    add = body.add
    TW = K.torso_w(PROPS)
    rows = torso_rows()
    V, F = torso_loft(rows, n=20, p=2.2, cap0=True, cap1=False)
    add(M.Part(V, F, "BH_Skin", name="torso"), weights=TW)
    # mottled patches on the back / shoulders (large enough to read as blotches)
    rng = np.random.default_rng(3)
    for i in range(6):
        z = L["spine"] + 0.02 + 0.2 * rng.random()
        x = (rng.random() - 0.5) * 0.15
        c = (x, 0.07 + 0.012 * (z > L["chest"]), z)
        add(K.blob(c, 0.028 + 0.012 * rng.random(), "BH_Flesh", scale=(1.2, 0.35, 0.9), n=8, rings=4), weights=TW)

    # ------------ loincloth + rope belt (the pelvis is covered by the cloth)
    zh = L["hips"]
    V, F = torso_loft([(zh - 0.085, 0.096, 0.072, 0.074, 0.0), (zh - 0.03, 0.098, 0.074, 0.074, 0.0),
                       (zh + 0.035, 0.096, 0.074, 0.072, 0.0)], n=20)
    add(M.Part(V, F, "BH_Cloth_Primary", name="seat"), weights=K.seat_w(body, zh + 0.02, zh - 0.09, 0.7))
    for sgn in (-1, 1):   # front and back flaps
        def fn(u, v, sgn=sgn):
            x = (u - 0.5) * (0.12 - 0.03 * v)
            z = zh + 0.01 - 0.2 * v
            y = sgn * (0.08 + 0.02 * v) + 0.004 * math.sin(u * 9 + v * 3)
            return (x, y, z)
        V, F = M.grid(fn, 5, 5)
        fl = M.Part(V, F, "BH_Cloth_Primary", name="flap")
        if sgn > 0:
            fl.flip()
        fl.V[-5:, 2] += np.array([0.0, 0.015, -0.01, 0.02, 0.0])  # ragged hem
        add(M.solidify(fl, 0.008, offset=1.0), weights=K.seat_w(body, zh, zh - 0.2, 0.7, center_w=0.02))
    belt = K.rtube([(0.1 * math.cos(a), 0.078 * math.sin(a), zh + 0.03) for a in np.linspace(0, 2 * math.pi, 17)],
                   0.009, "BH_Leather", n=6, up=(0, 0, 1), cap=False)
    add(belt, "hips")

    # ------------ fire-pots on the belt (left hip, right hip, back-left)
    for (ang, tilt) in ((150, 8), (205, -6), (35, 10)):
        a = math.radians(ang)
        c = np.array([0.125 * math.cos(a), 0.095 * math.sin(a), zh - 0.035])
        for prt in fire_pot(0.048):
            prt.rot(Ry(tilt)).move(c)
            add(prt, "hips")

    # ------------ legs (bowed) + big bare feet
    for s in ("L", "R"):
        K.leg(body, s, [(0.05, 0.052), (0.044, 0.046), (0.034, 0.036), (0.036, 0.036), (0.034, 0.036),
                        (0.022, 0.024)], "BH_Skin", bow=0.045, n=10)
        K.bare_foot(body, s, "BH_Skin", length=0.2, width=0.042, height=0.045, claw_mat="BH_Bone", toes=3,
                    toe_r=0.013)
        # knee knob
        k = body.head("shin." + s)
        sx = 1 if s == "L" else -1
        add(K.blob(k + (sx * 0.045, -0.02, 0), 0.033, "BH_Skin", n=8, rings=5),
            weights=lambda V, s=s: [{"thigh." + s: 0.5, "shin." + s: 0.5}] * len(V))

    # ------------ long skinny arms, big hands with claws, leather wrap on the right forearm
    for s in ("L", "R"):
        K.arm(body, s, [(0.036, 0.036), (0.03, 0.031), (0.026, 0.027), (0.028, 0.028), (0.03, 0.028),
                        (0.022, 0.021)], "BH_Skin", n=10, deltoid=0.038)
        K.hand(body, s, "BH_Skin", scale=0.95, claws="BH_Bone")
    fa, ha = body.head("forearm.R"), body.head("hand.R")
    V, F = M.tube([fa + (ha - fa) * 0.45, fa + (ha - fa) * 0.95], [(0.034, 0.033), (0.027, 0.026)], n=10,
                  up=(0, -1, 0))
    add(M.Part(V, F, "BH_Leather", name="wrap"), "forearm.R")

    # ------------ head, face, ears, helmet
    head(body)

    # ------------ loot sack on the back + rope strap across the chest
    sack(body)

    # ------------ notched knife (right hand)
    K.weapon_to_socket(body, "R", knife())


def fire_pot(r):
    parts = []
    V, F = M.lathe([(0.0, -r * 1.0), (r * 0.55, -r * 0.98), (r * 0.95, -r * 0.55), (r * 1.0, 0.0), (r * 0.8, r * 0.55),
                    (r * 0.42, r * 0.8), (r * 0.48, r * 0.98), (r * 0.3, r * 1.0), (0, r * 1.0)], 10)
    parts.append(M.Part(V, F, "BH_Stone", name="pot"))
    V, F = M.sphere(r * 0.5, 8, 4, center=(0, 0, r * 1.05), scale=(1.0, 1.0, 0.6))
    parts.append(M.Part(V, F, "BH_Cloth_Secondary", name="rag"))
    # burning rag tip (small flame tongue)
    V, F = M.lathe([(0.0, r * 1.05), (r * 0.42, r * 1.2), (r * 0.3, r * 1.55), (0.0, r * 2.1)], 7)
    parts.append(M.Part(V, F, "BH_Emissive", name="flame"))
    V, F = M.lathe([(0.0, r * 0.2), (r * 1.03, r * 0.22), (r * 1.03, r * 0.34), (0.0, r * 0.36)], 10)
    parts.append(M.Part(V, F, "BH_Leather", name="potcord"))
    return parts


def head(body):
    add = body.add
    z0 = L["head"]
    H = K.head_rows(HEAD, z0, sx=1.1, sy=1.08, sz=1.08, dy=-0.012)
    # neck
    V, F = M.tube([(0, 0.012, L["neck"] - 0.02), (0, 0.0, L["neck"] + 0.03), (0, -0.018, z0 + 0.02)],
                  [(0.036, 0.034), (0.033, 0.03), (0.035, 0.033)], n=10, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="neck"),
        weights=K.zspec_w([(L["neck"] - 0.01, "chest"), (L["neck"] + 0.02, "neck"), (z0 + 0.0, "neck"),
                           (z0 + 0.02, "head")]))
    V, F = torso_loft(H, n=20, p=2.1, cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Skin", name="head"), "head")
    # heavy brow
    zb = z0 + 0.078
    yb = K.front_of(H, 0, zb) + 0.004
    add(K.rtube([(-0.06, yb + 0.02, zb - 0.004), (-0.025, yb - 0.004, zb + 0.004), (0.0, yb - 0.002, zb),
                 (0.025, yb - 0.004, zb + 0.004), (0.06, yb + 0.02, zb - 0.004)], 0.014, "BH_Skin", n=6,
                up=(0, -1, 0)), "head")
    # eyes: dark sockets + glowing pupils
    for sx in (1, -1):
        ye = K.front_of(H, 0.03, z0 + 0.06)
        add(K.blob((sx * 0.031, ye + 0.006, z0 + 0.06), 0.018, "BH_Shadow", scale=(1.2, 0.5, 0.7), n=8, rings=4),
            "head")
        add(K.blob((sx * 0.032, ye - 0.001, z0 + 0.061), 0.008, "BH_Emissive", scale=(1.3, 0.6, 0.8), n=6, rings=4),
            "head")
    # big hooked nose
    yn = K.front_of(H, 0, z0 + 0.055)
    add(K.rtube([(0, yn + 0.005, z0 + 0.07), (0, yn - 0.04, z0 + 0.058), (0, yn - 0.075, z0 + 0.038),
                 (0, yn - 0.085, z0 + 0.016), (0, yn - 0.07, z0 + 0.004)],
                [(0.015, 0.013), (0.019, 0.017), (0.02, 0.018), (0.015, 0.013), (0.008, 0.006)], "BH_Skin", n=8,
                up=(0, 0, 1)), "head")
    # wide mouth slit + two jutting teeth
    ym = K.front_of(H, 0, z0 + 0.0) - 0.002
    mouth = [(x, K.front_of(H, x, z0 + 0.0 + 60 * x * x * 0.1) + 0.002, z0 + 0.0 + 6 * x * x)
             for x in np.linspace(-0.05, 0.05, 7)]
    add(K.rtube(mouth, (0.006, 0.004), "BH_Shadow", n=5), "head")
    for sx in (1, -1):
        add(K.cone((sx * 0.022, ym + 0.006, z0 - 0.004), (sx * 0.024, ym - 0.004, z0 + 0.022), 0.006, "BH_Bone",
                   n=5), "head")
    # huge ears, sticking out sideways and slightly back under the helmet brim
    for sx in (1, -1):
        rx, cy = K.side_of(H, z0 + 0.05)
        root = (sx * (rx - 0.012), cy + 0.012, z0 + 0.05)
        e = K.ear(root, 0.25, 0.11, "BH_Skin", out=(sx * 1.0, 0.25, 0.12), up=(0, 0.25, 1), droop=-0.02,
                  thick=0.014, back=0.02)
        add(e, "head")
        e2 = K.ear(np.array(root) + (sx * 0.03, -0.009, 0.004), 0.17, 0.06, "BH_Flesh", out=(sx * 1.0, 0.25, 0.12),
                   up=(0, 0.25, 1), droop=-0.014, thick=0.004)
        add(e2, "head")
        # notch / ring in one ear
        if sx > 0:
            add(K.rtube([np.array(root) + (0.17, 0.045, 0.02) + 0.012 * np.array([0, math.cos(a), math.sin(a)])
                         for a in np.linspace(0, 2 * math.pi, 9)], 0.003, "BH_Gold", n=4, cap=False), "head")
    # the oversized dented kettle helmet: sits low, tilted forward and to one side
    parts = []
    cz = z0 + 0.118
    V, F = dome((0, 0, 0), (0, 0, 1), 0.118, a_max=88, n=20, rings=7, scale=(1.0, 1.05, 0.95))
    shell = M.solidify(M.Part(V, F, "BH_Rust", name="helm"), 0.008, offset=-1.0)
    parts.append(shell)
    brim = []
    for rr in (0.108, 0.175):
        brim.append(np.array([(rr * math.cos(a), rr * 1.05 * math.sin(a), -0.005 - 0.03 * (rr - 0.108) / 0.07)
                              for a in np.linspace(0, 2 * math.pi, 20, endpoint=False)]))
    V, F = M.loft(brim, cap0=False, cap1=False)
    parts.append(M.solidify(M.Part(V, F, "BH_Rust", name="brim"), 0.007, offset=1.0))
    V, F = M.tube([(0.176 * math.cos(a), 0.176 * 1.05 * math.sin(a), -0.035)
                   for a in np.linspace(0, 2 * math.pi, 21)], [(0.006, 0.006)] * 21, n=5, up=(0, 0, 1),
                  cap0=False, cap1=False)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="brimrim"))
    # crest ridge + a spike knob (scavenged soldier's cap)
    V, F = M.tube([(0, -0.11, 0.035), (0, -0.06, 0.1), (0, 0.0, 0.118), (0, 0.06, 0.1), (0, 0.11, 0.035)],
                  [(0.008, 0.006)] * 5, n=5, up=(0, 0, 1))
    parts.append(M.Part(V, F, "BH_DarkSteel", name="ridge"))
    for pt in parts:
        dent(pt, (0.07, -0.06, 0.07), 0.07, 0.022)
        dent(pt, (-0.05, 0.08, 0.09), 0.06, 0.016)
        pt.rot(Rx(-20) @ Ry(12)).move((0.0, 0.012, cz))
        add(pt, "head")


def dent(part, c, r, d):
    return K.dent(part, c, r, d)


def sack(body):
    add = body.add
    zc = L["chest"]
    c = np.array([0.02, 0.17, zc + 0.03])
    V, F = M.sphere(0.13, 14, 9)
    sk = M.Part(V, F, "BH_Cloth_Secondary", name="sack")
    sk.scale((0.95, 0.72, 1.12))
    K.jitter(sk, 0.006, seed=4)
    # lumpy loot inside
    for (dx, dy, dz, r) in ((0.06, 0.02, 0.05, 0.06), (-0.05, 0.01, -0.06, 0.05), (0.02, 0.05, -0.02, 0.055)):
        dent(sk, (dx * 1.8, -dy, dz * 1.8), r * 1.2, -0.02)
    sk.rot(Ry(-14)).move(c)
    add(sk, "chest")
    # tied neck + a loot handle sticking out (a candlestick)
    top = c + np.array([-0.035, 0.0, 0.14])
    add(K.rtube([top - (0, 0, 0.03), top, top + (-0.02, 0.0, 0.035)], [0.035, 0.022, 0.045], "BH_Cloth_Secondary",
                n=9), "chest")
    add(K.rtube([top + (0, 0, -0.012) + 0.03 * np.array([math.cos(a), math.sin(a), 0])
                 for a in np.linspace(0, 2 * math.pi, 11)], 0.006, "BH_Leather", n=4, cap=False), "chest")
    add(K.rtube([top + (0.03, 0.0, 0.02), top + (0.07, -0.01, 0.12)], [0.008, 0.006], "BH_Gold", n=6), "chest")
    add(K.blob(top + (0.072, -0.01, 0.125), 0.018, "BH_Gold", scale=(1, 1, 0.5), n=8, rings=4), "chest")
    # strap: from the sack neck over the right shoulder, across the chest to the left hip
    zn = L["neck"]
    rows = torso_rows()
    pts = [top + (-0.05, -0.02, -0.02), (-0.09, 0.06, zn - 0.01), (-0.095, -0.02, zn - 0.03),
           (-0.04, -0.075, zn - 0.09), (0.04, -0.082, L["chest"] - 0.01), (0.1, -0.03, L["spine"] + 0.01),
           (0.1, 0.07, L["spine"] + 0.0), c + (0.06, -0.02, -0.1)]
    add(K.rtube(pts, (0.012, 0.005), "BH_Leather", n=6, up=(0, 0, 1), p=3.0), weights=K.torso_w(PROPS))


def knife():
    """Notched scavenged knife: single-edged blade along +Z, edge on +X (knuckle side), grip at origin."""
    parts = []
    out = [(-0.012, 0.04), (0.018, 0.04), (0.022, 0.1), (0.014, 0.11), (0.024, 0.12), (0.026, 0.18),
           (0.016, 0.19), (0.022, 0.2), (0.016, 0.25), (0.0, 0.29), (-0.012, 0.25), (-0.013, 0.12)]
    o = np.array(out)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    V, F = M.prism(o, 0.008, axis="y")
    bl = M.Part(V, F, "BH_Steel", name="knife")
    bl.warp(lambda v: (v[0], v[1] * (1 - 0.7 * max(0.0, v[0] / 0.026)), v[2]))
    parts.append(bl)
    V, F = M.box(0.05, 0.022, 0.014, center=(0.004, 0, 0.035))
    parts.append(M.Part(V, F, "BH_DarkSteel", name="guard"))
    V, F = M.lathe([(0, -0.07), (0.014, -0.07), (0.016, -0.05), (0.013, 0.0), (0.015, 0.03), (0.0, 0.03)], 8)
    parts.append(M.Part(V, F, "BH_Wood", name="grip"))
    V, F = M.lathe([(0.0, -0.085), (0.012, -0.08), (0.016, -0.07), (0.0, -0.064)], 8)
    parts.append(M.Part(V, F, "BH_Leather", name="knot"))
    return parts
