"""Rootweaver (bh-012, Builder B; Hollowroot Warren root-snare caster / healer): a gaunt ~2.0 m withered dryad of
twisted roots and bark. A body of braided roots, antler-like branches rising from the head (tips ~2.2 m), a pale bark
mask face with deep sockets glowing yellow-green, a skirt of trailing roots and hanging vines to the ground, a stack
of ochre shelf fungi on the left shoulder, long twig fingers, and a gnarled root staff crowned with a glowing seed
pod held in root claws. Modelled at true size on the shared humanoid skeleton; kits: greenskin_kit, kit_warren."""
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
import kit_a_common as A  # noqa: E402
from enemy_bandit_cutthroat import ring_frac  # noqa: E402

PROPS = proportions(
    1.0,
    pelvis_h=1.0, hip_h=0.96, knee_h=0.53, ankle_h=0.08, hip_x=0.085,
    hips_len=0.1, spine_len=0.2, chest_len=0.25, neck_len=0.12, head_len=0.2,
    clav_x0=0.03, clav_drop=0.05, shoulder_x=0.16, upper_len=0.32, fore_len=0.31, hand_len=0.12, grip_x=0.075,
)
L = K.levels(PROPS)
PREVIEW_HEIGHT = 2.35

PALETTE = "rootweaver"
PALETTE_COLORS = {
    "BH_Wood": ((0.085, 0.055, 0.03), 0.0, 0.85, None, 0.0, 1.0),            # dark bark / root body
    "BH_Leather": ((0.2, 0.13, 0.068), 0.0, 0.8, None, 0.0, 1.0),            # lighter braided root strands
    "BH_Horn": ((0.44, 0.4, 0.31), 0.0, 0.8, None, 0.0, 1.0),                # pale bark mask
    "BH_Fur": ((0.075, 0.14, 0.03), 0.0, 0.95, None, 0.0, 1.0),              # moss, vines
    "BH_Hair": ((0.035, 0.07, 0.022), 0.0, 0.9, None, 0.0, 1.0),             # dark hanging vines
    "BH_Cloth_Primary": ((0.46, 0.3, 0.1), 0.0, 0.8, None, 0.0, 1.0),        # ochre shelf fungi
    "BH_Bone": ((0.66, 0.6, 0.46), 0.0, 0.7, None, 0.0, 1.0),                # fungus rims
    "BH_Flesh": ((0.17, 0.06, 0.12), 0.0, 0.6, None, 0.0, 1.0),              # rot-purple caps
    "BH_Shadow": ((0.02, 0.015, 0.012), 0.0, 0.8, None, 0.0, 1.0),           # sockets
    "BH_Emissive": ((0.75, 1.0, 0.3), 0.0, 0.4, (0.75, 1.0, 0.3), 7.0, 1.0),  # eyes, seed pod, spores
}
CLIPS = ["staff_1", "cast_quick", "cast_area", "cast_heavy", "cast_weapon"]


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def torso_rows():
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    return [
        (zh - 0.06, 0.1, 0.075, 0.08, 0.0, 0.0),
        (zh + 0.04, 0.11, 0.08, 0.08, 0.0, 0.0),
        (zs + 0.06, 0.09, 0.07, 0.075, 0.04, 0.0),          # withered waist
        (zc + 0.06, 0.125, 0.09, 0.1, 0.06, 0.005),
        (zn - 0.07, 0.15, 0.085, 0.11, 0.03, 0.015),
        (zn - 0.02, 0.13, 0.07, 0.1, 0.0, 0.02),
        (zn + 0.02, 0.06, 0.05, 0.055, 0.0, 0.015),
    ]


ROWS = torso_rows()


def build(body: Body):
    add = body.add
    TW = K.torso_w(PROPS)
    V, F = torso_loft(ROWS, n=18, p=2.2, cap0=True, cap1=False)
    add(K.jitter(M.Part(V, F, "BH_Wood", name="torso"), 0.004, seed=2), weights=TW)
    braid(body, TW)
    head(body)
    shoulder_fungi(body)
    root_skirt(body)
    for s in ("L", "R"):
        sx = 1 if s == "L" else -1
        K.leg(body, s, [(0.06, 0.062), (0.05, 0.052), (0.04, 0.042), (0.042, 0.044), (0.04, 0.042),
                        (0.03, 0.032)], "BH_Wood", n=8)
        K.bare_foot(body, s, "BH_Wood", length=0.24, width=0.045, height=0.05, toes=3, toe_r=0.014,
                    claw_mat="BH_Leather")
        K.arm(body, s, [(0.045, 0.047), (0.036, 0.038), (0.032, 0.034), (0.034, 0.034), (0.032, 0.032),
                        (0.026, 0.026)], "BH_Wood", n=8)
        # a strand of lighter root spiralling down each arm
        sh, el, wr = body.head("upper_arm." + s), body.head("forearm." + s), body.head("hand." + s)
        pts = []
        for i in range(19):
            t = i / 18
            c = sh + (el - sh) * (t * 2) if t <= 0.5 else el + (wr - el) * ((t - 0.5) * 2)
            d = normalize(el - sh if t <= 0.5 else wr - el)
            side = normalize(np.cross(d, (0, 1, 0)))
            fw = np.cross(side, d)
            a = 2 * math.pi * 2.5 * t
            r = 0.04 - 0.012 * t
            pts.append(c + (side * math.cos(a) + fw * math.sin(a)) * r)
        add(W.tube(pts, 0.011, "BH_Leather", n=5), weights=body.seg_weights(["upper_arm." + s, "forearm." + s],
                                                                          power=10))
        # hanging vines from the forearms
        for k, u in enumerate((0.3, 0.6)):
            q = el + (wr - el) * u + np.array([0, 0.02, -0.02])
            add(W.root([q, q + (0.01 * sx, 0.02, -0.1), q + (0.0, 0.03, -0.2 - 0.05 * k)], 0.006, 0.002, "BH_Fur",
                       n=4, seed=k), "forearm." + s)
    # hands: right holds the staff (fist + twig claws), left open with long twig fingers
    K.hand(body, "R", "BH_Wood", scale=0.95)
    for prt in W.root_fingers(body, "R", "BH_Wood", count=4, length=0.07, r=0.007, curl=0.6, seed=4):
        add(prt, "hand.R")
    for prt in A.open_palm(body, "L", "BH_Wood", s=0.95):
        add(prt, "hand.L")
    for prt in W.root_fingers(body, "L", "BH_Wood", count=4, length=0.19, r=0.0075, curl=0.9, spread=1.3,
                              open_hand=True, seed=9, tip_mat="BH_Leather"):
        add(prt, "hand.L")
    K.weapon_to_socket(body, "R", seed_staff())


def braid(body, TW):
    """Three light root strands braided round the torso + a few ribs of root across the chest."""
    add = body.add
    z0, z1 = L["hips"] - 0.04, L["neck"] - 0.03
    for k in range(3):
        pts = []
        for i in range(25):
            t = i / 24
            z = z0 + (z1 - z0) * t
            f = (k / 3 + 1.25 * t) % 1.0
            pts.append(ring_frac(ROWS, z, 0.004, [f], p=2.2)[0])
        add(W.tube(pts, 0.016, "BH_Leather", n=5), weights=TW)
    for j, z in enumerate((L["chest"] + 0.02, L["chest"] + 0.09, L["chest"] + 0.16)):
        for sx in (1, -1):
            fr = np.linspace(0.02, 0.2, 5) if sx > 0 else 1 - np.linspace(0.02, 0.2, 5)
            pts = ring_frac(ROWS, z, 0.006, list(fr), p=2.2)
            pts[:, 2] -= np.linspace(0, 0.05, 5)
            add(W.root(pts, 0.014, 0.008, "BH_Wood", n=5, seed=j * 2 + (sx > 0)), weights=TW)
    # moss patches on the chest / back and a couple of glowing spores
    rng = np.random.default_rng(5)
    for i in range(7):
        f = rng.random()
        z = L["spine"] + 0.3 * rng.random()
        q = ring_frac(ROWS, z, 0.0, [f], p=2.2)[0]
        add(K.jitter(K.blob(q, 0.035, "BH_Fur", scale=(1.2, 1.2, 0.45), n=7, rings=4), 0.004, seed=i), weights=TW)
    for f, z in ((0.1, L["chest"] + 0.1), (0.55, L["chest"] + 0.05), (0.9, L["spine"] + 0.1)):
        q = ring_frac(ROWS, z, 0.0, [f], p=2.2)[0]
        a = 2 * math.pi * f - math.pi / 2
        for prt in W.blister(q, (math.cos(a), math.sin(a), 0.2), 0.016, "BH_Emissive", n=6):
            add(prt, weights=TW)


def head(body):
    add = body.add
    z0 = L["head"]
    HW = K.zspec_w([(L["neck"] - 0.01, "chest"), (L["neck"] + 0.03, "neck"), (z0, "neck"), (z0 + 0.03, "head")])
    V, F = M.tube([(0, 0.02, L["neck"] - 0.02), (0, 0.0, z0), (0, -0.005, z0 + 0.04)],
                  [(0.04, 0.04), (0.035, 0.035), (0.04, 0.04)], n=8, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Wood", name="neck"), weights=HW)
    # long narrow skull of bark
    H = [(-0.02, 0.04, 0.05, 0.05, 0.0, 0.0), (0.02, 0.07, 0.085, 0.07, 0.05, -0.005),
         (0.08, 0.075, 0.09, 0.085, 0.04, 0.0), (0.14, 0.072, 0.08, 0.09, 0.0, 0.005),
         (0.19, 0.055, 0.06, 0.075, 0.0, 0.01), (0.22, 0.02, 0.02, 0.03, 0.0, 0.01)]
    rows = K.head_rows(H, z0)
    V, F = torso_loft(rows, n=14, p=2.1, cap0=True, cap1=True)
    add(K.jitter(M.Part(V, F, "BH_Wood", name="skull"), 0.003, seed=3), "head")
    # pale bark mask over the face: a curved plate, long chin point, deep sockets with glowing eyes
    def fn(u, v):
        x = (u - 0.5) * 0.14 * (1.0 - 0.55 * (1 - v) ** 2)
        z = z0 - 0.06 + 0.24 * v
        yb = K.front_of(rows, x, min(max(z, z0 - 0.015), z0 + 0.2)) - 0.012
        return (x, yb - 0.01 * math.sin(math.pi * v), z)
    V, F = M.grid(fn, 7, 9)
    add(M.solidify(M.Part(V, F, "BH_Horn", name="mask"), 0.012, offset=1.0), "head")
    ye = K.front_of(rows, 0.03, z0 + 0.1) - 0.042
    for sx in (1, -1):
        add(K.blob((sx * 0.032, ye + 0.006, z0 + 0.1), 0.024, "BH_Shadow", scale=(1.0, 0.4, 1.25), n=8, rings=5),
            "head")
        add(K.blob((sx * 0.032, ye - 0.002, z0 + 0.1), 0.012, "BH_Emissive", scale=(1.0, 0.7, 1.2), n=6, rings=4),
            "head")
        # bark ridges on the mask cheeks
        add(W.root([(sx * 0.05, ye - 0.002, z0 + 0.07), (sx * 0.045, ye + 0.004, z0 + 0.02),
                    (sx * 0.025, ye + 0.01, z0 - 0.03)], 0.007, 0.003, "BH_Wood", n=4, seed=sx + 2), "head")
    add(K.blob((0, ye + 0.006, z0 + 0.03), 0.018, "BH_Shadow", scale=(1.2, 0.4, 0.5), n=6, rings=4), "head")
    # antler branches rising from the crown
    for sx in (1, -1):
        base = np.array([sx * 0.035, 0.01, z0 + 0.17])
        for prt in W.branch(base, (sx * 0.55, 0.15, 1.0), 0.26, 0.018, "BH_Wood", depth=2, seed=21 + (sx > 0),
                            spread=30, forks=2, curl=0.25, n=5, min_r=0.004):
            add(prt, "head")
        # small side tine curling back
        b2 = np.array([sx * 0.06, 0.03, z0 + 0.13])
        for prt in W.branch(b2, (sx * 1.0, 0.6, 0.35), 0.13, 0.01, "BH_Wood", depth=1, seed=31 + (sx > 0), n=4):
            add(prt, "head")
    # vines draped from the antler bases down the back of the head
    for k in range(5):
        a = math.radians(30 + 30 * k)
        t = np.array([0.06 * math.cos(a), 0.05 * math.sin(a) + 0.03, z0 + 0.15])
        add(W.root([t, t + (0, 0.03, -0.12), t + (0.01, 0.05, -0.26 - 0.04 * (k % 2))], 0.006, 0.002,
                   "BH_Hair" if k % 2 else "BH_Fur", n=4, seed=40 + k), weights=HW)


def shoulder_fungi(body):
    sh = body.head("upper_arm.L")
    w = W.const_w({"chest": 0.5, "shoulder.L": 0.5})
    for k, (dz, dy, r) in enumerate(((0.05, 0.0, 0.075), (0.0, 0.035, 0.062), (0.09, -0.03, 0.05), (-0.04, 0.06, 0.045))):
        base = sh + np.array([-0.03, dy, dz])
        out = normalize(np.array([1.0, 0.25 * (k % 2) - 0.1, 0.0]))
        for prt in W.shelf(base, out, r, "BH_Cloth_Primary", thick=0.28, rim_mat="BH_Bone", n=12):
            body.add(prt, weights=w)
    body.add(K.jitter(K.blob(sh + np.array([-0.04, 0.03, 0.05]), 0.06, "BH_Fur", scale=(1.2, 1.2, 0.6), n=8,
                             rings=4), 0.005, seed=4), weights=w)


def root_skirt(body):
    """Bark under-skirt (split panels) + trailing roots and vines to the ground."""
    zt = L["hips"] + 0.02
    W.split_skirt(body, "BH_Wood", zt, 0.18, (0.105, 0.085, 0.085), 0.12, ragged=0.1, folds=0.012, nz=7, nu=7,
                  thick=0.008, max_leg=0.85, center_w=0.06, shin_from=0.7)
    w = body.skirt_weights(zt, 0.1, max_leg=0.85, shin_from=0.7, center_w=0.06)
    rng = np.random.default_rng(12)
    n = 26
    for i in range(n):
        f = i / n + 0.01 * rng.random()
        top = W.ellipse_ring(zt - 0.01, 0.12, 0.1, 0.1, [f])[0]
        out = normalize(np.array([top[0], top[1], 0.0]))
        ln = zt - 0.02 - 0.08 * rng.random()
        pts = [top, top + out * 0.05 + (0, 0, -ln * 0.3), top + out * 0.12 + (0, 0, -ln * 0.65),
               top + out * (0.16 + 0.04 * rng.random()) + (0, 0, -ln)]
        pts[-1][2] = max(pts[-1][2], 0.02)
        mat = "BH_Wood" if i % 3 else "BH_Leather"
        body.add(W.root(pts, 0.02 if i % 3 else 0.015, 0.004, mat, n=5, seed=50 + i, knot=0.25, amp=0.01), weights=w)
    for i in range(10):
        f = (i + 0.5) / 10
        top = W.ellipse_ring(zt - 0.03, 0.13, 0.11, 0.11, [f])[0]
        out = normalize(np.array([top[0], top[1], 0.0]))
        ln = 0.5 + 0.35 * rng.random()
        body.add(W.root([top, top + out * 0.08 + (0, 0, -ln * 0.5), top + out * 0.13 + (0, 0, -ln)], 0.007, 0.003,
                        "BH_Fur" if i % 2 else "BH_Hair", n=4, seed=80 + i), weights=w)


def seed_staff():
    """Gnarled root staff (weapon space: grip at origin, +Z up): twisting shaft, root claws gripping a glowing seed
    pod at the top, a few small purple caps on the shaft, root tendrils at the foot."""
    parts = []
    pts = []
    for i in range(12):
        u = i / 11
        z = -0.95 + 1.8 * u
        pts.append((0.02 * math.sin(u * 8.0) + 0.012 * math.sin(u * 2.3), 0.014 * math.cos(u * 5.5), z))
    parts.append(W.root(pts, 0.02, 0.026, "BH_Wood", n=7, seed=3, knot=0.2))
    parts.append(W.root([p + np.array([0.012 * math.cos(i * 1.3), 0.012 * math.sin(i * 1.3), 0]) for i, p in
                         enumerate(np.array(pts[3:]))], 0.009, 0.008, "BH_Leather", n=4, seed=4))
    top = np.array(pts[-1])
    pod = top + np.array([0, 0, 0.13])
    parts.append(A.ball(pod, 0.075, "BH_Emissive", n=12, rings=8, scale=(1.0, 1.0, 1.35)))
    for k in range(5):
        a = 2 * math.pi * k / 5
        o = np.array([math.cos(a), math.sin(a), 0.0])
        cl = [top + o * 0.015, top + o * 0.07 + (0, 0, 0.05), pod + o * 0.085 + (0, 0, 0.02),
              pod + o * 0.055 + (0, 0, 0.1), pod + o * 0.012 + (0, 0, 0.14)]
        parts.append(W.root(cl, 0.013, 0.003, "BH_Wood", n=5, seed=10 + k, knot=0.2))
    for k, (u, a) in enumerate(((0.62, 30), (0.66, 200), (0.45, 110))):
        q = np.array(pts[int(u * 11)])
        o = np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), 0.25])
        parts += W.mushroom(q, o, 0.035, 0.007, 0.03, 0.022, "BH_Horn", "BH_Flesh", "BH_Cloth_Primary", n=8, seed=k)
    foot = np.array(pts[0])
    for k in range(3):
        a = 2 * math.pi * k / 3
        o = np.array([math.cos(a), math.sin(a), 0.0])
        parts.append(W.root([foot + (0, 0, 0.08), foot + o * 0.03 + (0, 0, 0.02), foot + o * 0.05 + (0, 0, -0.04)],
                            0.012, 0.003, "BH_Wood", n=4, seed=20 + k))
    return parts
