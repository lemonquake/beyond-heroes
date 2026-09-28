"""Sporeling (bh-012, Builder B; Hollowroot Warren swarm fodder that bursts): a squat walking mushroom ~1.1 m tall.
An oversized speckled cap (rot purple-brown with pale warts and a few glowing spore warts) is its head; ochre gill
frills under the brim hide two glowing yellow-green eyes; a pale, lumpy stalk-flesh body with glowing spore
blisters; stubby arms ending in knobbly root fingers; short thick legs with root toes. No weapon.
Modelled at true size on the shared humanoid skeleton (goblin-sized proportions), kits: greenskin_kit, kit_warren."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft, front_y, back_y  # noqa: E402
from bh_math import normalize  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as K  # noqa: E402
import kit_warren as W  # noqa: E402
from enemy_bandit_cutthroat import ring_frac  # noqa: E402

S = 0.6
PROPS = proportions(
    S,
    pelvis_h=0.35, hip_h=0.33, knee_h=0.18, ankle_h=0.045, ball_fwd=0.09, ball_h=0.018, toe_len=0.05,
    heel_back=0.035, hip_x=0.095,
    hips_len=0.07, spine_len=0.1, chest_len=0.13, neck_len=0.04, head_len=0.18,
    clav_x0=0.025, clav_drop=0.03, shoulder_x=0.125, upper_len=0.16, fore_len=0.15, hand_len=0.07, grip_x=0.05,
    grip_drop=0.012,
)
L = K.levels(PROPS)
PREVIEW_HEIGHT = 1.3

PALETTE = "sporeling"
PALETTE_COLORS = {
    "BH_Skin": ((0.56, 0.49, 0.37), 0.0, 0.6, None, 0.0, 1.0),               # pale stalk flesh
    "BH_Flesh": ((0.19, 0.07, 0.13), 0.0, 0.55, None, 0.0, 1.0),             # rot-purple cap
    "BH_Bone": ((0.72, 0.66, 0.5), 0.0, 0.7, None, 0.0, 1.0),                # pale warts
    "BH_Horn": ((0.46, 0.32, 0.14), 0.0, 0.75, None, 0.0, 1.0),              # ochre gills
    "BH_Wood": ((0.11, 0.07, 0.038), 0.0, 0.8, None, 0.0, 1.0),              # root fingers / toes
    "BH_Fur": ((0.07, 0.13, 0.03), 0.0, 0.95, None, 0.0, 1.0),               # moss tufts
    "BH_Shadow": ((0.03, 0.02, 0.022), 0.0, 0.8, None, 0.0, 1.0),            # face shade, mouth
    "BH_Emissive": ((0.75, 1.0, 0.3), 0.0, 0.4, (0.75, 1.0, 0.3), 6.0, 1.0),  # eyes, spore blisters
}
CLIPS = ["axe_1", "axe_2", "cast_quick"]

CAP_C = np.array([0.0, 0.005, L["head"] + 0.13])   # cap centre (rim plane)
CAP_R, CAP_H = 0.33, 0.25


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def torso_rows():
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    # pear-shaped: wide low belly, narrow shoulders, stalk neck
    return [
        (zh - 0.07, 0.11, 0.09, 0.09, 0.0, 0.0),
        (zh - 0.02, 0.15, 0.13, 0.12, 0.02, 0.0),
        (zs, 0.17, 0.15, 0.135, 0.05, -0.008),
        (zs + 0.06, 0.165, 0.145, 0.13, 0.04, -0.008),
        (zc + 0.04, 0.14, 0.115, 0.11, 0.02, 0.0),
        (zn - 0.04, 0.115, 0.09, 0.095, 0.0, 0.004),
        (zn - 0.005, 0.1, 0.08, 0.085, 0.0, 0.006),
        (zn + 0.03, 0.08, 0.072, 0.074, 0.0, 0.006),
    ]


ROWS = torso_rows()


def build(body: Body):
    add = body.add
    TW = K.torso_w(PROPS)
    V, F = torso_loft(ROWS, n=22, p=2.2, cap0=True, cap1=False)
    tor = M.Part(V, F, "BH_Skin", name="torso")
    K.jitter(tor, 0.004, seed=5)
    add(tor, weights=TW)
    rng = np.random.default_rng(3)
    # lumps on the belly / flanks
    for i in range(9):
        f = rng.random()
        z = L["hips"] + 0.02 + 0.22 * rng.random()
        q = ring_frac(ROWS, z, -0.006, [f], p=2.2)[0]
        a = 2 * math.pi * f - math.pi / 2
        n = normalize(np.array([math.cos(a), math.sin(a), 0.1]))
        add(K.blob(q, 0.03 + 0.02 * rng.random(), "BH_Skin", scale=(1.0, 1.0, 0.55), n=8, rings=4,
                   rot=W.M_align_z(n)), weights=TW)
    # glowing spore blisters: chest, belly, back, shoulders
    for f, z, r in ((0.08, L["chest"] + 0.02, 0.022), (0.93, L["spine"] + 0.02, 0.018), (0.45, L["chest"] + 0.06, 0.026),
                    (0.58, L["spine"] + 0.04, 0.02), (0.3, L["neck"] - 0.03, 0.017), (0.72, L["chest"], 0.016)):
        q = ring_frac(ROWS, z, -0.004, [f], p=2.2)[0]
        a = 2 * math.pi * f - math.pi / 2
        n = normalize(np.array([math.cos(a), math.sin(a), 0.2]))
        for p in W.blister(q, n, r * 1.25, "BH_Emissive", n=8):
            add(p, weights=TW)
    # moss tufts at the hips
    for f in (0.2, 0.34, 0.66, 0.8):
        q = ring_frac(ROWS, L["hips"] - 0.03, 0.0, [f], p=2.2)[0]
        add(K.jitter(K.blob(q, 0.035, "BH_Fur", scale=(1.2, 1.2, 0.5), n=8, rings=4), 0.004, seed=int(f * 99)),
            weights=K.seat_w(body, L["hips"] + 0.02, L["hips"] - 0.1, 0.4))

    head(body)

    for s in ("L", "R"):
        sx = 1 if s == "L" else -1
        K.leg(body, s, [(0.06, 0.062), (0.055, 0.058), (0.046, 0.048), (0.046, 0.048), (0.048, 0.05),
                        (0.036, 0.038)], "BH_Skin", bow=0.02, n=10, top_up=0.03)
        K.bare_foot(body, s, "BH_Skin", length=0.17, width=0.05, height=0.05, toes=3, toe_r=0.017)
        # root toes spreading from the foot
        p = body.p
        hx = p["hip_x"] * sx
        for k, (dx, ln) in enumerate(((-0.05, 0.07), (0.0, 0.09), (0.05, 0.07))):
            b = np.array([hx + dx * 0.8, -p["ball_fwd"] * 0.8, 0.02])
            pts = [b, b + (dx * 0.5, -ln * 0.55, -0.006), b + (dx * 1.1, -ln, -0.014)]
            add(W.root(pts, 0.013, 0.004, "BH_Wood", n=5, seed=k + 3 * (sx > 0)), "toe." + s)
        heel = np.array([hx, p["heel_back"] * 0.8, 0.02])
        add(W.root([heel, heel + (sx * 0.02, 0.04, -0.01), heel + (sx * 0.035, 0.07, -0.016)], 0.012, 0.004,
                   "BH_Wood", n=5, seed=9 + (sx > 0)), "foot." + s)
        # stubby arms, knobbly root fingers
        K.arm(body, s, [(0.05, 0.052), (0.043, 0.045), (0.038, 0.04), (0.037, 0.038), (0.036, 0.037),
                        (0.03, 0.03)], "BH_Skin", n=10, deltoid=0.05)
        wr = body.head("hand." + s)
        add(K.blob(body.head("weapon." + s) * 0.7 + wr * 0.3, 0.036, "BH_Skin", scale=(1.1, 0.9, 0.8), n=8, rings=5),
            "hand." + s)
        for prt in W.root_fingers(body, s, "BH_Wood", count=4, length=0.085, r=0.0095, curl=0.9, spread=1.1,
                                  open_hand=True, seed=11 + 5 * (sx > 0)):
            add(prt, "hand." + s)
        # small blister on each upper arm
        ua, fa = body.head("upper_arm." + s), body.head("forearm." + s)
        c = ua + (fa - ua) * 0.45 + np.array([sx * 0.03, 0.02, 0.0])
        for prt in W.blister(c, (sx * 1.0, 0.4, 0.3), 0.014, "BH_Emissive", ring_mat="BH_Skin", n=6):
            add(prt, "upper_arm." + s)


def head(body):
    add = body.add
    z0 = L["head"]
    HW = K.zspec_w([(L["neck"] - 0.02, "chest"), (L["neck"] + 0.02, "neck"), (z0, "neck"), (z0 + 0.03, "head")])
    # stalk head: continues the body up into the cap
    V, F = M.tube([(0, 0.004, L["neck"] - 0.02), (0, 0.004, z0 + 0.02), (0, 0.0, z0 + 0.08), (0, 0.004, z0 + 0.14)],
                  [(0.08, 0.075), (0.085, 0.08), (0.09, 0.088), (0.082, 0.08)], n=16, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="stalkhead"), weights=HW)
    # face: shaded brow hollow under the gills, eyes, a small gaping mouth
    zf = z0 + 0.04
    yf = -0.088
    add(K.blob((0, yf + 0.016, zf + 0.014), 0.07, "BH_Shadow", scale=(1.0, 0.28, 0.36), n=10, rings=4), "head")
    for sx in (1, -1):
        add(K.blob((sx * 0.034, yf - 0.008, zf + 0.008), 0.021, "BH_Emissive", scale=(1.0, 0.65, 1.15), n=8, rings=5),
            "head")
    add(K.blob((0, yf + 0.006, z0 - 0.012), 0.022, "BH_Shadow", scale=(1.3, 0.5, 0.7), n=8, rings=4), "head")
    # gill frill: a loose skirt of ochre frills hanging under the brim (the veil) round the face
    for k in range(16):
        a = math.radians(-90 + 30 + k * 20)            # leaves the face open (-90 +- 30 deg)
        r = 0.125
        top = np.array([r * math.cos(a), r * math.sin(a), CAP_C[2] - 0.01])
        out = np.array([math.cos(a), math.sin(a), 0.0])
        near_face = abs(((math.degrees(a) + 90 + 180) % 360) - 180) < 50
        ln = (0.07 if near_face else 0.1) + 0.03 * ((k * 7) % 3) / 2
        pts = [top, top + out * 0.012 + (0, 0, -ln * 0.6), top + out * 0.02 + (0, 0, -ln)]
        add(W.tube(pts, [(0.022, 0.004), (0.017, 0.004), (0.007, 0.003)], "BH_Horn", n=4,
                   up=[out, out, out], p=3.0), "head")
    # the cap
    for prt in W.cap(CAP_C, (0, 0.05, 1.0), CAP_R, CAP_H, "BH_Flesh", "BH_Horn", n=22, rim_phi=-20, gills=0.018,
                     gill_k=14, wobble=0.05, seed=4, rings=7, stem_r=0.085):
        add(prt, "head")
    for prt in W.warts(CAP_C, (0, 0.05, 1.0), CAP_R, CAP_H, 22, "BH_Bone", 0.03, seed=8, phi=(5, 72),
                       glow="BH_Emissive", glow_every=5, n=7):
        add(prt, "head")
