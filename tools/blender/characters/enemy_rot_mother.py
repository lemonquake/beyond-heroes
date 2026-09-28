"""Verdigast, the Rot Mother (bh-012, Builder B; Hollowroot Warren BOSS): a towering fungal matriarch ~2.2 m to the
crown, the fungal halo rising to ~2.8 m (the game scales her ~2x). Long layered robes of moss over rot-purple, hung
with pale mycelium threads; a vast fan of rot-purple mushroom caps (glowing spore warts) and ochre shelf fungi
rising behind her head like a crown / halo (the silhouette key, rigid on the chest); a pale fungal mask face with
seven small glowing eyes under a mossy cowl; long root arms with long root fingers; a cluster of glowing spore sacs
on her chest; a living root staff crowned with a large glowing pod. True size on the shared humanoid skeleton;
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
import kit_a_common as A  # noqa: E402
from enemy_bandit_cutthroat import ring_frac  # noqa: E402

PROPS = proportions(
    1.1,
    pelvis_h=1.15, hip_h=1.1, knee_h=0.6, ankle_h=0.09, hip_x=0.1,
    hips_len=0.12, spine_len=0.23, chest_len=0.3, neck_len=0.13, head_len=0.24,
    clav_x0=0.035, clav_drop=0.06, shoulder_x=0.19, upper_len=0.37, fore_len=0.36, hand_len=0.14, grip_x=0.085,
)
L = K.levels(PROPS)
PREVIEW_HEIGHT = 3.0

PALETTE = "rot_mother"
PALETTE_COLORS = {
    "BH_Fur": ((0.075, 0.13, 0.035), 0.0, 0.95, None, 0.0, 1.0),             # moss robe
    "BH_Cloth_Secondary": ((0.1, 0.04, 0.07), 0.0, 0.9, None, 0.0, 1.0),     # rot-purple under-robe
    "BH_Horn": ((0.62, 0.58, 0.45), 0.0, 0.7, None, 0.0, 1.0),               # pale fungal mask
    "BH_Bone": ((0.74, 0.7, 0.56), 0.0, 0.8, None, 0.0, 1.0),                # mycelium threads, warts
    "BH_Flesh": ((0.24, 0.07, 0.17), 0.0, 0.55, None, 0.0, 1.0),             # rot-purple caps
    "BH_Cloth_Primary": ((0.48, 0.3, 0.09), 0.0, 0.8, None, 0.0, 1.0),       # ochre shelf fungi
    "BH_Leather": ((0.36, 0.24, 0.1), 0.0, 0.8, None, 0.0, 1.0),             # gills
    "BH_Wood": ((0.1, 0.065, 0.035), 0.0, 0.85, None, 0.0, 1.0),             # root arms / fingers / staff
    "BH_Shadow": ((0.02, 0.015, 0.02), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((0.75, 1.0, 0.3), 0.0, 0.4, (0.75, 1.0, 0.3), 8.0, 1.0),  # eyes, spore sacs, pod, spores
}
CLIPS = ["staff_1", "staff_heavy", "cast_area", "cast_heavy", "cast_ultimate", "boss_roar", "boss_summon",
         "boss_slam"]


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def torso_rows(g=0.0):
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    return [
        (zh - 0.06, 0.14 + g, 0.1 + g, 0.11 + g, 0.0, 0.0),
        (zh + 0.06, 0.13 + g, 0.095 + g, 0.1 + g, 0.0, 0.0),
        (zs + 0.08, 0.12 + g, 0.09 + g, 0.095 + g, 0.03, 0.0),
        (zc + 0.08, 0.15 + g, 0.11 + g, 0.11 + g, 0.06, 0.005),
        (zn - 0.08, 0.17 + g, 0.1 + g, 0.12 + g, 0.03, 0.015),
        (zn - 0.02, 0.15 + g, 0.08 + g, 0.11 + g, 0.0, 0.02),
        (zn + 0.03, 0.07 + g, 0.06 + g, 0.065 + g, 0.0, 0.015),
    ]


ROWS = torso_rows()
ROBE = torso_rows(0.02)


def build(body: Body):
    add = body.add
    TW = K.torso_w(PROPS)
    V, F = torso_loft(ROBE, n=22, p=2.2, cap0=True, cap1=False)
    add(M.Part(V, F, "BH_Fur", name="robe_top"), weights=TW)
    # layered skirts: long rot-purple under-robe, ragged moss over-robe
    W.split_skirt(body, "BH_Cloth_Secondary", L["hips"] + 0.03, 0.03, (0.15, 0.11, 0.12), 0.3, ragged=0.05,
                  folds=0.02, nz=8, nu=9, thick=0.01, max_leg=0.8, center_w=0.08, shin_from=0.75, seed=1.0)
    w = W.split_skirt(body, "BH_Fur", L["hips"] + 0.08, 0.32, (0.17, 0.13, 0.14), 0.3, ragged=0.16, folds=0.025,
                      nz=7, nu=9, thick=0.01, max_leg=0.75, center_w=0.08, shin_from=0.75, seed=2.3)
    # mycelium threads hanging from the over-robe hem and the waist
    rng = np.random.default_rng(3)
    tops, lens = [], []
    for i in range(30):
        f = i / 30 + 0.01 * rng.random()
        r = W.ellipse_ring(0.36 + 0.1 * rng.random(), 0.44, 0.4, 0.43, [f])[0]
        tops.append(r)
        lens.append(0.12 + 0.2 * rng.random())
    for prt in W.hanging_strands(tops, lens, 0.007, "BH_Bone", seed=5, sway=0.02, n=4):
        add(prt, weights=w)
    # moss sash + spore sacs on the chest
    V, F = M.tube([np.array(p) for p in W.ellipse_ring(L["hips"] + 0.1, 0.19, 0.15, 0.16, np.linspace(0, 1, 17))],
                  [(0.03, 0.03)] * 17, n=6, up=(0, 0, 1))
    add(M.Part(V, F, "BH_Cloth_Secondary", name="sash"), "hips")
    for f, z, r in ((0.02, L["chest"] + 0.14, 0.05), (0.92, L["chest"] + 0.08, 0.04), (0.1, L["chest"] + 0.06, 0.042),
                    (0.96, L["chest"] + 0.2, 0.034), (0.06, L["chest"] + 0.24, 0.03), (0.0, L["chest"] - 0.02, 0.036)):
        q = ring_frac(ROBE, z, 0.0, [f], p=2.2)[0]
        a = 2 * math.pi * f - math.pi / 2
        for prt in W.blister(q, (math.cos(a), math.sin(a), 0.15), r, "BH_Emissive", ring_mat="BH_Flesh", n=10):
            add(prt, weights=TW)
    head(body)
    halo(body)
    for s in ("L", "R"):
        sx = 1 if s == "L" else -1
        K.leg(body, s, [(0.07, 0.072), (0.06, 0.062), (0.05, 0.052), (0.05, 0.052), (0.048, 0.05),
                        (0.036, 0.038)], "BH_Wood", n=8)
        K.bare_foot(body, s, "BH_Wood", length=0.27, width=0.055, height=0.06, toes=4, toe_r=0.016)
        # thin root arms inside wide mossy sleeves
        K.arm(body, s, [(0.05, 0.052), (0.04, 0.042), (0.036, 0.038), (0.038, 0.038), (0.036, 0.036),
                        (0.03, 0.03)], "BH_Wood", n=8)
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
        pts = [sh + (sh - el) * 0.05, sh + (el - sh) * 0.5, el, el + (wr - el) * 0.45, el + (wr - el) * 0.78]
        V, F = M.tube(pts, [(0.075, 0.08), (0.07, 0.075), (0.08, 0.085), (0.11, 0.12), (0.14, 0.15)], n=12,
                      up=(0, -1, 0), cap1=False)
        add(M.solidify(M.Part(V, F, "BH_Fur", name="sleeve"), 0.008, offset=1.0),
            weights=body.seg_weights(["shoulder." + s, ua, fa], power=10))
        d = normalize(wr - el)
        c = pts[-1]
        side = normalize(np.cross(d, (0, 1, 0)))
        fw = np.cross(side, d)
        tops = [c + (side * math.cos(a) + fw * math.sin(a)) * 0.14 for a in np.linspace(0, 2 * math.pi, 9)[:-1]]
        for prt in W.hanging_strands(tops, [0.2, 0.28, 0.16, 0.3, 0.22, 0.34, 0.18, 0.26], 0.006, "BH_Bone",
                                     seed=60 + 3 * (sx > 0), sway=0.015, n=4):
            add(prt, fa)
        # shelf fungi on the shoulders
        for k, (dz, dy, r) in enumerate(((0.07, 0.02, 0.09), (0.02, 0.07, 0.07))):
            base = sh + np.array([-sx * 0.02, dy, dz])
            for prt in W.shelf(base, (sx * 1.0, 0.2 * k, 0.1), r, "BH_Cloth_Primary", thick=0.28, rim_mat="BH_Bone"):
                add(prt, weights=W.const_w({"chest": 0.5, "shoulder." + s: 0.5}))
    # hands: long root fingers (left open, right gripping the staff)
    K.hand(body, "R", "BH_Wood", scale=1.0)
    for prt in W.root_fingers(body, "R", "BH_Wood", count=4, length=0.08, r=0.008, curl=0.6, seed=4):
        add(prt, "hand.R")
    for prt in A.open_palm(body, "L", "BH_Wood", s=1.05):
        add(prt, "hand.L")
    for prt in W.root_fingers(body, "L", "BH_Wood", count=5, length=0.22, r=0.009, curl=0.9, spread=1.4,
                              open_hand=True, seed=9, tip_mat="BH_Bone"):
        add(prt, "hand.L")
    K.weapon_to_socket(body, "R", pod_staff())


def head(body):
    add = body.add
    z0 = L["head"]
    HW = K.zspec_w([(L["neck"] - 0.01, "chest"), (L["neck"] + 0.04, "neck"), (z0, "neck"), (z0 + 0.03, "head")])
    V, F = M.tube([(0, 0.02, L["neck"] - 0.03), (0, 0.0, z0), (0, -0.005, z0 + 0.05)],
                  [(0.05, 0.05), (0.045, 0.045), (0.05, 0.05)], n=10, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Horn", name="neck"), weights=HW)
    H = [(-0.03, 0.05, 0.05, 0.05, 0.0, 0.0), (0.02, 0.085, 0.1, 0.08, 0.05, -0.005),
         (0.1, 0.095, 0.105, 0.095, 0.04, 0.0), (0.17, 0.09, 0.095, 0.1, 0.0, 0.005),
         (0.22, 0.07, 0.07, 0.085, 0.0, 0.01), (0.25, 0.03, 0.03, 0.04, 0.0, 0.01)]
    rows = K.head_rows(H, z0)
    V, F = torso_loft(rows, n=16, p=2.1, cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Horn", name="mask"), "head")
    # seven small glowing eyes in two arcs + a centre eye; a slit mouth; gill ridges on the cheeks
    eyes = [(0.0, 0.15, 0.019), (0.037, 0.126, 0.017), (-0.037, 0.126, 0.017), (0.064, 0.1, 0.014),
            (-0.064, 0.1, 0.014), (0.03, 0.082, 0.012), (-0.03, 0.082, 0.012)]
    for x, dz, r in eyes:
        y = K.front_of(rows, x, z0 + dz)
        add(K.blob((x, y + 0.004, z0 + dz), r * 1.5, "BH_Shadow", scale=(1.0, 0.45, 1.0), n=7, rings=4), "head")
        add(K.blob((x, y - 0.002, z0 + dz), r, "BH_Emissive", scale=(1.0, 0.6, 1.0), n=7, rings=4), "head")
    ym = K.front_of(rows, 0, z0 + 0.03)
    add(K.blob((0, ym + 0.004, z0 + 0.03), 0.035, "BH_Shadow", scale=(1.0, 0.3, 0.25), n=8, rings=4), "head")
    for sx in (1, -1):
        for k in range(3):
            x = sx * (0.055 + 0.012 * k)
            pts = [(x, K.front_of(rows, x, z) + 0.002, z) for z in (z0 + 0.07, z0 + 0.035, z0 + 0.0)]
            add(W.tube(pts, (0.005, 0.003), "BH_Leather", n=4, up=(0, -1, 0)), "head")
    # mossy cowl round the back / sides of the head, threads hanging from it
    rows_c = K.head_rows([(r[0], r[1] + 0.025, r[2] + 0.025, r[3] + 0.03, r[4], r[5]) for r in H[1:]], z0)
    rings = []
    for z in np.linspace(z0 + 0.0, z0 + 0.235, 6):
        fr = np.linspace(0.16, 0.84, 13)
        r = ring_frac(rows_c, z, 0.0, list(fr), p=2.1)
        rings.append(r)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    add(M.solidify(M.Part(V, F, "BH_Fur", name="cowl"), 0.012, offset=1.0), "head")
    tops = [np.array(p) for p in rings[0][::2]]
    for prt in W.hanging_strands(tops, [0.25, 0.35, 0.3, 0.4, 0.3, 0.35, 0.25], 0.006, "BH_Bone", seed=33, n=4):
        add(prt, weights=HW)


def halo(body):
    """Fan of mushroom caps and shelf fungi rising behind the head (rigid on the chest)."""
    add = body.add
    w = W.const_w({"chest": 1.0})
    c = np.array([0.0, 0.2, L["neck"] + 0.02])
    rng = np.random.default_rng(11)
    # woody root back-plate the fan grows from
    for k in range(7):
        a = math.radians(-75 + 25 * k)
        d = normalize(np.array([math.sin(a), 0.25, math.cos(a)]))
        add(W.root([c + (0, -0.05, -0.1), c + d * 0.22, c + d * 0.4], 0.035, 0.015, "BH_Wood", n=6, seed=k, amp=0.01),
            weights=w)
    spokes = [(-78, 0.5, 0.17, "cap"), (-58, 0.62, 0.2, "cap"), (-38, 0.72, 0.22, "cap"), (-16, 0.8, 0.24, "cap"),
              (0, 0.9, 0.27, "cap"), (16, 0.8, 0.24, "cap"), (38, 0.72, 0.22, "cap"), (58, 0.62, 0.2, "cap"),
              (78, 0.5, 0.17, "cap"),
              (-68, 0.36, 0.12, "shelf"), (-48, 0.46, 0.13, "shelf"), (-27, 0.52, 0.13, "shelf"),
              (-6, 0.58, 0.13, "shelf"), (6, 0.58, 0.13, "shelf"), (27, 0.52, 0.13, "shelf"),
              (48, 0.46, 0.13, "shelf"), (68, 0.36, 0.12, "shelf")]
    for i, (ang, ln, r, kind) in enumerate(spokes):
        a = math.radians(ang)
        d = normalize(np.array([math.sin(a), 0.3, math.cos(a)]))
        tip = c + d * ln
        if kind == "cap":
            add(W.root([c + d * 0.05, c + d * ln * 0.5 + (0, 0.02, 0), tip], 0.03, 0.022, "BH_Bone", n=6, seed=20 + i),
                weights=w)
            up = normalize(d * 0.6 + np.array([0, -0.8, 0.25]))       # cap tops face forward / up
            for prt in W.cap(tip, up, r, r * 0.6, "BH_Flesh", "BH_Leather", n=16, rings=5, gills=0.012,
                             gill_k=12, wobble=0.05, seed=i, stem_r=0.03):
                add(prt, weights=w)
            for prt in W.warts(tip, up, r, r * 0.6, 7, "BH_Bone", r * 0.12, seed=40 + i, glow="BH_Emissive",
                               glow_every=2, n=5):
                add(prt, weights=w)
            # mycelium threads from the cap rims
            if i % 2 == 0:
                q = tip + np.array([0, 0.02, -r * 0.5])
                for prt in W.hanging_strands([q, q + (0.04, 0.0, 0.0)], [0.2, 0.3], 0.005, "BH_Bone", seed=70 + i,
                                             n=4):
                    add(prt, weights=w)
        else:
            out = normalize(d + np.array([0, -0.6, 0.0]))
            for prt in W.shelf(tip, out, r, "BH_Cloth_Primary", thick=0.25, up=d, rim_mat="BH_Bone", n=12):
                add(prt, weights=w)


def pod_staff():
    """Living root staff (weapon space: grip at origin, +Z up) crowned with a large glowing pod in a cage of roots,
    small purple caps growing on the shaft, trailing root tendrils."""
    parts = []
    pts = [(0.025 * math.sin(u * 7.0) + 0.015 * math.sin(u * 2.1), 0.02 * math.cos(u * 4.5), -1.0 + 2.0 * u)
           for u in np.linspace(0, 1, 13)]
    parts.append(W.root(pts, 0.026, 0.032, "BH_Wood", n=8, seed=2, knot=0.2))
    for k in range(2):
        parts.append(W.root([np.array(p) + np.array([0.02 * math.cos(i * 1.1 + k * 3), 0.02 * math.sin(i * 1.1 + k * 3), 0])
                             for i, p in enumerate(pts[2:])], 0.01, 0.008, "BH_Wood", n=4, seed=5 + k))
    top = np.array(pts[-1])
    pod = top + np.array([0, 0, 0.17])
    parts.append(A.ball(pod, 0.11, "BH_Emissive", n=14, rings=9, scale=(1.0, 1.0, 1.3)))
    for k in range(6):
        a = 2 * math.pi * k / 6
        o = np.array([math.cos(a), math.sin(a), 0.0])
        cl = [top + o * 0.02, top + o * 0.1 + (0, 0, 0.06), pod + o * 0.12 + (0, 0, 0.03),
              pod + o * 0.08 + (0, 0, 0.14), pod + o * 0.02 + (0, 0, 0.2)]
        parts.append(W.root(cl, 0.016, 0.004, "BH_Wood", n=5, seed=10 + k, knot=0.2))
    for k, (u, a) in enumerate(((0.7, 40), (0.74, 210), (0.55, 120), (0.3, 300))):
        q = np.array(pts[int(u * 12)])
        o = np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), 0.3])
        parts += W.mushroom(q, o, 0.045, 0.009, 0.04, 0.028, "BH_Bone", "BH_Flesh", "BH_Leather", n=8, seed=k)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        o = np.array([math.cos(a), math.sin(a), 0.0])
        q = top + o * 0.08
        parts.append(W.root([q, q + o * 0.04 + (0, 0, -0.1), q + o * 0.03 + (0, 0, -0.25)], 0.006, 0.002, "BH_Bone",
                            n=4, seed=30 + k))
    return parts
