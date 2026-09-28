"""Mycelid Hulk (bh-012, Builder B; Hollowroot Warren brute with a spore breath): a massive hunched mushroom giant
~2.5 m to the top of its cap. A broad flat cap (rot brown-purple, pale warts, a few glowing spore warts) spreads over
the hunched shoulders like a mantle; a small face peers out under the brim with glowing eyes; the body is pale stalk
flesh ridged with ochre shelf fungi; huge fists, the right one wrapped in a knot of root like a club (rigid on
weapon.R); glowing spore sacs on the lower back; thick legs with root toes. True size on the shared humanoid skeleton;
kits: greenskin_kit, kit_warren."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft  # noqa: E402
from bh_math import normalize  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as K  # noqa: E402
import kit_warren as W  # noqa: E402
from enemy_bandit_cutthroat import ring_frac  # noqa: E402

S = 1.4
PROPS = proportions(
    S,
    pelvis_h=1.05, hip_h=0.98, knee_h=0.55, ankle_h=0.11, hip_x=0.2, ball_fwd=0.22, ball_h=0.04, toe_len=0.1,
    heel_back=0.09,
    hips_len=0.16, spine_len=0.3, chest_len=0.48, neck_len=0.1, head_len=0.22,
    clav_x0=0.08, clav_drop=0.12, shoulder_x=0.42, upper_len=0.6, fore_len=0.56, hand_len=0.2, grip_x=0.13,
    grip_drop=0.03,
)
L = K.levels(PROPS)
PREVIEW_HEIGHT = 2.9

PALETTE = "mycelid_hulk"
PALETTE_COLORS = {
    "BH_Skin": ((0.5, 0.44, 0.32), 0.0, 0.6, None, 0.0, 1.0),                # pale stalk flesh
    "BH_Flesh": ((0.28, 0.15, 0.055), 0.0, 0.55, None, 0.0, 1.0),           # rot-ochre cap
    "BH_Bone": ((0.7, 0.64, 0.49), 0.0, 0.7, None, 0.0, 1.0),                # pale warts, shelf rims
    "BH_Horn": ((0.42, 0.29, 0.13), 0.0, 0.75, None, 0.0, 1.0),              # ochre gills
    "BH_Cloth_Primary": ((0.2, 0.08, 0.14), 0.0, 0.7, None, 0.0, 1.0),       # rot-purple shelf fungi
    "BH_Wood": ((0.1, 0.065, 0.035), 0.0, 0.85, None, 0.0, 1.0),             # root knot club, root toes
    "BH_Fur": ((0.07, 0.13, 0.03), 0.0, 0.95, None, 0.0, 1.0),               # moss
    "BH_Shadow": ((0.025, 0.018, 0.018), 0.0, 0.8, None, 0.0, 1.0),          # face, mouth
    "BH_Emissive": ((0.75, 1.0, 0.3), 0.0, 0.4, (0.75, 1.0, 0.3), 6.0, 1.0),  # eyes, spore sacs, spore warts
}
CLIPS = ["axe_1", "axe_2", "boss_slam", "cast_heavy", "boss_charge"]

HEAD_DY, HEAD_DZ = -0.44, -0.42
CAP_C = np.array([0.0, 0.06, L["neck"] + 0.14])
CAP_UP = normalize(np.array([0.0, -0.12, 1.0]))
CAP_R, CAP_H = 0.82, 0.3


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def torso_weights():
    base = K.torso_w(PROPS)

    def wfn(V):
        out = []
        for w in base(V):
            if "neck" in w:
                w = dict(w)
                w["chest"] = w.get("chest", 0.0) + w.pop("neck")
            out.append(w)
        return out
    return wfn


def torso_rows():
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    return [
        (zh - 0.16, 0.26, 0.2, 0.2, 0.0, 0.0),
        (zh + 0.02, 0.33, 0.3, 0.26, 0.03, -0.02),
        (zs + 0.1, 0.36, 0.34, 0.27, 0.05, -0.04),         # barrel belly
        (zc + 0.08, 0.4, 0.3, 0.32, 0.05, -0.04),
        (zc + 0.3, 0.46, 0.26, 0.38, 0.03, -0.03),         # hunched shoulders
        (zn - 0.08, 0.44, 0.2, 0.4, 0.0, 0.0),
        (zn + 0.02, 0.32, 0.14, 0.34, 0.0, 0.04),
        (zn + 0.1, 0.16, 0.08, 0.2, 0.0, 0.06),
    ]


ROWS = torso_rows()


def surf(frac, z, g=0.0):
    q = ring_frac(ROWS, z, g, [frac % 1.0], p=2.2)[0]
    a = 2 * math.pi * frac - math.pi / 2
    return q, normalize(np.array([math.cos(a), math.sin(a), 0.1]))


def build(body: Body):
    add = body.add
    TW = torso_weights()
    V, F = torso_loft(ROWS, n=26, p=2.2, cap0=True, cap1=True)
    add(K.jitter(M.Part(V, F, "BH_Skin", name="torso"), 0.006, seed=12), weights=TW)
    # vertical stalk ridges down the belly and flanks
    for f in (0.04, 0.12, 0.2, 0.8, 0.88, 0.96, 0.4, 0.6):
        pts = [surf(f, z, -0.005)[0] for z in np.linspace(L["hips"] - 0.05, L["chest"] + 0.35, 6)]
        add(W.root(pts, 0.022, 0.016, "BH_Skin", n=5, seed=int(f * 100), knot=0.3), weights=TW)
    # shelf fungi ridging the flanks
    rng = np.random.default_rng(4)
    for i, (f, z) in enumerate(((0.21, L["spine"] + 0.05), (0.23, L["spine"] + 0.2), (0.26, L["chest"] + 0.05),
                                (0.77, L["spine"] + 0.1), (0.75, L["chest"] + 0.0), (0.36, L["spine"] + 0.15),
                                (0.64, L["spine"] + 0.25), (0.5, L["hips"] + 0.1))):
        q, n = surf(f, z)
        for prt in W.shelf(q, n, 0.15 + 0.05 * rng.random(), "BH_Cloth_Primary", thick=0.3, rim_mat="BH_Bone", n=12):
            add(prt, weights=TW)
    # glowing spore sacs on the lower back (below the cap rim)
    for i, (f, z, r) in enumerate(((0.43, L["chest"] + 0.1, 0.1), (0.57, L["chest"] + 0.06, 0.09),
                                   (0.5, L["chest"] + 0.3, 0.11), (0.39, L["spine"] + 0.12, 0.075),
                                   (0.61, L["spine"] + 0.2, 0.08), (0.5, L["spine"] + 0.02, 0.07))):
        q, n = surf(f, z, -0.01)
        for prt in W.blister(q, n, r, "BH_Emissive", ring_mat="BH_Skin", n=10):
            add(prt, weights=TW)
    # moss round the hips
    for f in np.linspace(0, 1, 9, endpoint=False):
        q, n = surf(f + 0.05, L["hips"] - 0.1)
        add(K.jitter(K.blob(q, 0.07, "BH_Fur", scale=(1.2, 1.2, 0.5), n=8, rings=4), 0.006, seed=int(f * 50)),
            weights=K.seat_w(body, L["hips"], L["hips"] - 0.25, 0.45))
    head(body)
    mantle_cap(body, TW)
    for s in ("L", "R"):
        sx = 1 if s == "L" else -1
        K.leg(body, s, [(0.21, 0.22), (0.19, 0.2), (0.16, 0.17), (0.16, 0.17), (0.16, 0.17), (0.12, 0.125)],
              "BH_Skin", bow=0.03, n=12, top_up=0.08)
        K.bare_foot(body, s, "BH_Skin", length=0.46, width=0.15, height=0.12, toes=4, toe_r=0.04)
        p = body.p
        hx = p["hip_x"] * sx
        for k, dx in enumerate((-0.12, -0.04, 0.04, 0.12)):
            b = np.array([hx + dx, -p["ball_fwd"] * 0.9, 0.05])
            add(W.root([b, b + (dx * 0.4, -0.12, -0.02), b + (dx * 0.8, -0.2, -0.04)], 0.03, 0.008, "BH_Wood",
                       n=5, seed=k + 4 * (sx > 0)), "toe." + s)
        K.arm(body, s, [(0.17, 0.18), (0.14, 0.15), (0.12, 0.13), (0.13, 0.13), (0.15, 0.15), (0.11, 0.11)],
              "BH_Skin", n=12, deltoid=0.19)
        # shelf fungi on the upper arm and forearm
        ua, fa, ha = body.head("upper_arm." + s), body.head("forearm." + s), body.head("hand." + s)
        for u, bone, a in ((0.45, "upper_arm." + s, 0.0), (0.4, "forearm." + s, 0.6)):
            c = (ua + (fa - ua) * u) if bone.startswith("upper") else (fa + (ha - fa) * u)
            out = normalize(np.array([sx * 1.0, a, 0.1]))
            for prt in W.shelf(c + out * 0.1, out, 0.13, "BH_Cloth_Primary", thick=0.3, rim_mat="BH_Bone", n=10):
                add(prt, bone)
        for prt in W.blister(fa + (ha - fa) * 0.7 + np.array([sx * 0.02, 0.1, 0.05]), (sx * 0.4, 1.0, 0.3), 0.035,
                             "BH_Emissive", n=8):
            add(prt, "forearm." + s)
        K.hand(body, s, "BH_Skin", scale=2.5, claws="BH_Wood")
    K.weapon_to_socket(body, "R", root_knot())


def head(body):
    add = body.add
    z0 = L["head"] + HEAD_DZ
    V, F = M.tube([(0, 0.05, L["neck"] - 0.1), (0, -0.1, L["neck"] - 0.02), (0, -0.22 + 0.0, z0 + 0.02),
                   (0, HEAD_DY + 0.02, z0 + 0.08)],
                  [(0.2, 0.18), (0.18, 0.16), (0.15, 0.14), (0.13, 0.12)], n=12, up=(0, 0, 1))
    add(M.Part(V, F, "BH_Skin", name="neck"), weights=lambda V: [
        {"chest": 1.0} if v[1] > -0.08 else ({"neck": 1.0} if v[1] > -0.2 else {"neck": 0.4, "head": 0.6})
        for v in V])
    H = [(-0.02, 0.07, 0.07, 0.06, 0.0, 0.0), (0.03, 0.13, 0.13, 0.11, 0.05, -0.01),
         (0.1, 0.14, 0.14, 0.13, 0.05, 0.0), (0.17, 0.12, 0.12, 0.13, 0.0, 0.01), (0.22, 0.06, 0.06, 0.07, 0.0, 0.01)]
    rows = K.head_rows(H, z0, dy=HEAD_DY)
    V, F = torso_loft(rows, n=16, p=2.1, cap0=True, cap1=True)
    add(K.jitter(M.Part(V, F, "BH_Skin", name="head"), 0.004, seed=6), "head")
    yf = K.front_of(rows, 0, z0 + 0.1)
    add(K.blob((0, yf + 0.02, z0 + 0.13), 0.12, "BH_Shadow", scale=(1.0, 0.25, 0.35), n=10, rings=4), "head")
    for sx in (1, -1):
        add(K.blob((sx * 0.05, K.front_of(rows, 0.05, z0 + 0.1) - 0.022, z0 + 0.1), 0.028, "BH_Emissive",
                   scale=(1.1, 0.6, 0.9), n=8, rings=5), "head")
    # gaping spore mouth
    add(K.blob((0, K.front_of(rows, 0, z0 + 0.04) + 0.01, z0 + 0.04), 0.06, "BH_Shadow", scale=(1.2, 0.4, 0.6),
               n=10, rings=5), "head")
    add(K.blob((0, K.front_of(rows, 0, z0 + 0.04) + 0.02, z0 + 0.04), 0.03, "BH_Emissive", scale=(1.3, 0.4, 0.5),
               n=8, rings=4), "head")
    # heavy brow ridge of stalk flesh with small gill frills hanging over the eyes
    yb = K.front_of(rows, 0, z0 + 0.16)
    add(W.root([(-0.12, yb + 0.03, z0 + 0.15), (0, yb - 0.02, z0 + 0.17), (0.12, yb + 0.03, z0 + 0.15)], 0.04, 0.04,
               "BH_Skin", n=6, knot=0.1), "head")


def mantle_cap(body, TW):
    add = body.add
    w = W.const_w({"chest": 1.0})
    for prt in W.cap(CAP_C, CAP_UP, CAP_R, CAP_H, "BH_Flesh", "BH_Horn", n=28, rim_phi=-24, gills=0.035, gill_k=18,
                     wobble=0.06, seed=9, rings=7, stem_r=0.35, squash=0.9):
        add(prt, weights=w)
    for prt in W.warts(CAP_C, CAP_UP, CAP_R, CAP_H, 30, "BH_Bone", 0.06, seed=17, phi=(4, 70), glow="BH_Emissive",
                       glow_every=4, n=7, squash=0.9):
        add(prt, weights=w)
    # moss and small mushrooms growing on the mantle
    for k, (ph, an) in enumerate(((30, 60), (45, 200), (25, 320), (55, 130))):
        q, n = W.cap_point(CAP_C, CAP_UP, CAP_R, CAP_H, ph, an, squash=0.9)
        add(K.jitter(K.blob(q, 0.1, "BH_Fur", scale=(1.3, 1.3, 0.35), n=8, rings=4, rot=W.M_align_z(n)), 0.01,
                     seed=k), weights=w)
        if k % 2 == 0:
            for prt in W.mushroom(q, n, 0.1, 0.02, 0.07, 0.05, "BH_Bone", "BH_Flesh", "BH_Horn", n=8, seed=k,
                                  warts_mat="BH_Emissive", wart_count=3):
                add(prt, weights=w)


def root_knot():
    """Knot of root wrapped round the right fist (weapon space: grip at origin, +Z = forward out of the fist)."""
    parts = []
    rng = np.random.default_rng(7)
    parts.append(K.jitter(K.blob((0, 0, 0.06), 0.2, "BH_Wood", scale=(1.0, 0.95, 1.1), n=12, rings=8), 0.012, seed=2))
    for k in range(7):
        ax = normalize(rng.normal(size=3))
        u = normalize(np.cross(ax, (0.3, 0.5, 0.8)))
        v = np.cross(ax, u)
        r = 0.2 + 0.03 * rng.random()
        loop = [np.array([0, 0, 0.06]) + (u * math.cos(a) + v * math.sin(a)) * r for a in np.linspace(0, 2 * math.pi, 13)]
        parts.append(W.root(loop, 0.035, 0.03, "BH_Wood", n=6, seed=30 + k, knot=0.3))
    for k in range(9):
        d = normalize(rng.normal(size=3) + np.array([0, 0, 0.6]))
        b = np.array([0, 0, 0.06]) + d * 0.2
        parts.append(W.root([b, b + d * 0.08, b + d * 0.14 + rng.normal(size=3) * 0.02], 0.03, 0.006, "BH_Wood",
                            n=5, seed=50 + k))
    for k in range(4):
        d = normalize(rng.normal(size=3))
        parts += W.blister(np.array([0, 0, 0.06]) + d * 0.215, d, 0.025, "BH_Emissive", n=6)
    return parts
