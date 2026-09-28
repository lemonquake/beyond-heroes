"""Treasure Gremlin (bh-013, Builder B2 "brutes"; loot runner - it never fights, it flees): a greedy little stooped
creature (~1.0 m to the tip of its crown) with warm grey-brown skin, huge bat-like ears, big glowing gold eyes, a long
nose and a wide needle-toothed grin. It wears a patched purple waistcoat with gold buttons over ragged breeches,
three gold chains with a medallion round its neck and a small gold crown set askew on its head. On its back it
hauls a HUGE overstuffed sack almost as big as itself, gold heaped out of the open mouth (a mound of coins, a
jewelled goblet, a string of pearls) and more coins spilling from a split seam. No weapon.

Greenskin kit on a small custom skeleton (scaled goblin proportions). The sack is rigid on the chest.
Clips: dagger_1 (panicked claw swipe), cast_quick (toss a coin / flash), blink (vanish) + the enemy base set."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft, dome  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as K  # noqa: E402
import enemy_goblin_skulker as GS  # noqa: E402

G = 0.88   # goblin proportions scaled down
PROPS = proportions(
    0.64 * G,
    pelvis_h=0.46 * G, hip_h=0.44 * G, knee_h=0.25 * G, ankle_h=0.05 * G, ball_fwd=0.11 * G, ball_h=0.02 * G,
    toe_len=0.06 * G, heel_back=0.04 * G, hip_x=0.08 * G,
    hips_len=0.07 * G, spine_len=0.12 * G, chest_len=0.15 * G, neck_len=0.05 * G, head_len=0.2 * G,
    clav_x0=0.025 * G, clav_drop=0.03 * G, shoulder_x=0.12 * G, upper_len=0.22 * G, fore_len=0.21 * G,
    hand_len=0.085 * G, grip_x=0.06 * G, grip_drop=0.013 * G,
)
L = K.levels(PROPS)

PALETTE = "treasure_gremlin"
PALETTE_COLORS = {
    "BH_Skin": ((0.3, 0.23, 0.18), 0.0, 0.6, None, 0.0, 1.0),               # warm grey-brown
    "BH_Flesh": ((0.36, 0.14, 0.13), 0.0, 0.55, None, 0.0, 1.0),            # inner ears, gums
    "BH_Cloth_Primary": ((0.24, 0.05, 0.3), 0.0, 0.75, None, 0.0, 1.0),     # purple waistcoat
    "BH_Cloth_Secondary": ((0.3, 0.2, 0.09), 0.0, 0.95, None, 0.0, 1.0),    # burlap sack
    "BH_Fur": ((0.09, 0.2, 0.12), 0.0, 0.85, None, 0.0, 1.0),               # green patches on the waistcoat
    "BH_Leather": ((0.1, 0.06, 0.035), 0.0, 0.8, None, 0.0, 1.0),           # breeches, rope, belt
    "BH_Gold": ((1.0, 0.72, 0.22), 1.0, 0.18, None, 0.0, 1.0),              # coins, crown, chains, goblet
    "BH_Aether": ((0.8, 0.03, 0.08), 0.3, 0.08, (0.6, 0.02, 0.06), 1.0, 1.0),  # ruby gems
    "BH_Bone": ((0.85, 0.82, 0.74), 0.0, 0.3, None, 0.0, 1.0),              # teeth, claws, pearls
    "BH_Shadow": ((0.03, 0.02, 0.02), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((1.0, 0.8, 0.25), 0.0, 0.4, (1.0, 0.75, 0.2), 7.0, 1.0),  # greedy gold eyes
}

CLIPS = ["dagger_1", "cast_quick", "blink"]


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


STOOP = 0.045          # forward shift of the upper body at the neck (mesh only; the bones stay upright)


def torso_rows():
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    rows = [
        (zh - 0.045, 0.078, 0.06, 0.062, 0.0, 0.0),
        (zh + 0.02, 0.082, 0.07, 0.06, 0.05, 0.0),
        (zs + 0.03, 0.08, 0.078, 0.06, 0.1, 0.0),          # little pot belly
        (zs + 0.08, 0.082, 0.07, 0.072, 0.06, 0.004),
        (zc + 0.05, 0.092, 0.06, 0.09, 0.02, 0.012),       # hunched back
        (zn - 0.045, 0.1, 0.056, 0.092, 0.0, 0.02),
        (zn - 0.012, 0.09, 0.05, 0.075, 0.0, 0.018),
        (zn + 0.01, 0.048, 0.038, 0.045, 0.0, 0.006),
    ]
    out = []
    for r in rows:
        t = max(0.0, (r[0] - zs) / (zn - zs))
        out.append(r[:5] + (r[5] - STOOP * t * t,))
    return out


HEAD = [  # (dz, rx, ryf, ryb, keel, cy): round cranium, pointed chin
    (-0.03, 0.022, 0.03, 0.025, 0.0, -0.03),
    (-0.012, 0.05, 0.06, 0.04, 0.12, -0.03),
    (0.01, 0.066, 0.075, 0.055, 0.12, -0.025),
    (0.035, 0.075, 0.08, 0.068, 0.08, -0.018),
    (0.065, 0.082, 0.078, 0.08, 0.04, -0.01),
    (0.098, 0.085, 0.074, 0.088, 0.0, -0.004),
    (0.13, 0.08, 0.066, 0.084, 0.0, 0.0),
    (0.158, 0.062, 0.05, 0.066, 0.0, 0.004),
    (0.176, 0.03, 0.025, 0.032, 0.0, 0.006),
]


def build(body: Body):
    add = body.add
    TW = K.torso_w(PROPS)
    rows = torso_rows()
    V, F = torso_loft(rows, n=20, p=2.2, cap0=True, cap1=False)
    add(M.Part(V, F, "BH_Skin", name="torso"), weights=TW)

    zh = L["hips"]
    # ragged breeches
    V, F = torso_loft([(zh - 0.08, 0.088, 0.066, 0.068, 0.0), (zh - 0.03, 0.09, 0.068, 0.068, 0.0),
                       (zh + 0.03, 0.088, 0.07, 0.066, 0.0)], n=20)
    add(M.Part(V, F, "BH_Leather", name="seat"), weights=K.seat_w(body, zh + 0.02, zh - 0.09, 0.7))
    for s in ("L", "R"):
        pts = K.leg(body, s, [(0.044, 0.046), (0.036, 0.038), (0.028, 0.03), (0.03, 0.03), (0.03, 0.032),
                              (0.02, 0.022)], "BH_Skin", bow=0.05, n=10)
        V, F = M.tube([pts[0] + (0, 0, 0.01), pts[1], pts[2] + (pts[3] - pts[2]) * 0.6],
                      [(0.052, 0.054), (0.046, 0.048), (0.04, 0.042)], n=12, up=(0, -1, 0), cap1=False)
        br = M.Part(V, F, "BH_Leather", name="breeches")
        lo = pts[2][2]
        br.warp(lambda v, lo=lo: v - np.array([0, 0, 0.022]) * max(0.0, 1 - abs(v[2] - lo) / 0.03) *
                (0.5 + 0.5 * math.sin(math.atan2(v[1], v[0]) * 5)))
        add(M.solidify(br, 0.005, offset=-1.0), weights=body.seg_weights(["thigh." + s, "shin." + s], power=10))
        K.bare_foot(body, s, "BH_Skin", length=0.2, width=0.045, height=0.04, claw_mat="BH_Bone", toes=3,
                    toe_r=0.013)
        k = body.head("shin." + s)
        sx = 1 if s == "L" else -1
        add(K.blob(k + (sx * 0.035, -0.02, 0), 0.028, "BH_Skin", n=8, rings=5),
            weights=lambda V, s=s: [{"thigh." + s: 0.5, "shin." + s: 0.5}] * len(V))

    # long skinny arms, oversized clawed hands
    for s in ("L", "R"):
        K.arm(body, s, [(0.03, 0.03), (0.025, 0.026), (0.021, 0.022), (0.024, 0.024), (0.025, 0.024),
                        (0.019, 0.018)], "BH_Skin", n=10, deltoid=0.03)
        K.hand(body, s, "BH_Skin", scale=1.05, claws="BH_Bone")
    # gold ring on the left hand, bangle on the right wrist
    wr = body.head("hand.R")
    add(K.rtube([wr + (0.0, 0.026 * math.cos(a), 0.026 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 11)],
                0.006, "BH_Gold", n=4, cap=False), "forearm.R")

    waistcoat(body, rows, TW)
    head(body)
    chains(body, rows, TW)
    sack(body)


# ------------------------------------------------------------------------------------------------- waistcoat
def waistcoat(body, rows, TW):
    add = body.add
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    g = 0.01
    vr = [(r[0], r[1] + g, r[2] + g, r[3] + g, r[4] * 0.5, r[5]) for r in rows if zh - 0.01 <= r[0] <= zn]
    vr = [(zh - 0.02,) + vr[0][1:]] + vr
    V, F = torso_loft(vr, n=24, p=2.2, cap0=False, cap1=False)
    add(M.Part(V, F, "BH_Cloth_Primary", name="waistcoat"), weights=TW)
    # pointed front hem tails
    for sx in (1, -1):
        x = sx * 0.035
        y = K.front_of(rows, x, zh + 0.02) - g - 0.004
        add(K.rtube([(x - sx * 0.03, y, zh - 0.0), (x, y - 0.004, zh - 0.035), (x + sx * 0.025, y, zh - 0.005)],
                    (0.02, 0.006), "BH_Cloth_Primary", n=5, up=(0, -1, 0)), "hips")
    # lapels (V down to the belly) + gold buttons
    for sx in (1, -1):
        pts = []
        for t in np.linspace(0, 1, 5):
            z = zn - 0.02 - (zn - zs - 0.02) * t
            x = sx * (0.045 * (1 - t) + 0.008)
            pts.append((x, K.front_of(rows, x, z) - g - 0.004, z))
        add(K.rtube(pts, (0.012, 0.004), "BH_Fur", n=5, up=(0, -1, 0)), weights=TW)
    for z in np.linspace(zs - 0.01, zc + 0.03, 4):
        add(K.blob((0.0, K.front_of(rows, 0, z) - g - 0.006, z), 0.009, "BH_Gold", scale=(1, 0.5, 1), n=6, rings=3),
            weights=TW)
    # sewn-on patches (green and burlap) with stitches
    for (x, z, mat) in ((0.06, zs + 0.03, "BH_Fur"), (-0.07, zc + 0.02, "BH_Cloth_Secondary")):
        y = K.front_of(rows, x, z) - g - 0.002
        add(M.Part(*M.box(0.04, 0.006, 0.035, center=(x, y, z)), mat, name="patch").rot(Rz(0)), weights=TW)
    # rope belt
    add(K.rtube([(0.096 * math.cos(a), 0.075 * math.sin(a), zh + 0.02) for a in np.linspace(0, 2 * math.pi, 17)],
                0.008, "BH_Leather", n=5, cap=False), "hips")
    # a couple of coins tucked in the belt
    for ang in (230, 300):
        a = math.radians(ang)
        c = np.array([0.1 * math.cos(a), 0.08 * math.sin(a) - 0.006, zh + 0.02])
        add(coin(c, (math.cos(a), math.sin(a), 0.3), 0.016), "hips")


# ------------------------------------------------------------------------------------------------------ head
def head(body):
    add = body.add
    z0 = L["head"]
    dy = -STOOP - 0.01
    H = K.head_rows(HEAD, z0, sx=1.12, sy=1.08, sz=1.0, dy=dy)
    V, F = M.tube([(0, 0.012 - STOOP * 0.8, L["neck"] - 0.02), (0, -STOOP, L["neck"] + 0.03),
                   (0, dy - 0.012, z0 + 0.02)],
                  [(0.032, 0.03), (0.028, 0.026), (0.032, 0.03)], n=10, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="neck"),
        weights=K.zspec_w([(L["neck"] - 0.01, "chest"), (L["neck"] + 0.02, "neck"), (z0 + 0.0, "neck"),
                           (z0 + 0.02, "head")]))
    V, F = torso_loft(H, n=20, p=2.1, cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Skin", name="head"), "head")
    # big round greedy eyes under a pinched brow
    for sx in (1, -1):
        ye = K.front_of(H, sx * 0.035, z0 + 0.075)
        add(K.blob((sx * 0.035, ye + 0.008, z0 + 0.075), 0.026, "BH_Shadow", scale=(1.0, 0.5, 0.85), n=10, rings=5),
            "head")
        add(K.blob((sx * 0.035, ye - 0.002, z0 + 0.075), 0.017, "BH_Emissive", scale=(1.0, 0.55, 0.9), n=8, rings=4),
            "head")
        add(K.rtube([(sx * 0.012, ye - 0.004, z0 + 0.1), (sx * 0.04, ye - 0.002, z0 + 0.104),
                     (sx * 0.065, ye + 0.012, z0 + 0.112)], 0.009, "BH_Skin", n=5), "head")
    # long drooping nose
    yn = K.front_of(H, 0, z0 + 0.06)
    add(K.rtube([(0, yn + 0.004, z0 + 0.07), (0, yn - 0.035, z0 + 0.055), (0, yn - 0.06, z0 + 0.03),
                 (0, yn - 0.058, z0 + 0.012)], [(0.013, 0.012), (0.016, 0.015), (0.015, 0.014), (0.009, 0.008)],
                "BH_Skin", n=8, up=(0, 0, 1)), "head")
    # wide grin with needle teeth
    zm = z0 + 0.008
    mouth = [(x, K.front_of(H, x, zm + 6 * x * x) + 0.002, zm + 6 * x * x) for x in np.linspace(-0.058, 0.058, 9)]
    add(K.rtube(mouth, (0.009, 0.005), "BH_Shadow", n=5), "head")
    for x in np.linspace(-0.045, 0.045, 7):
        zz = zm + 6 * x * x
        y = K.front_of(H, x, zz) - 0.002
        add(K.cone((x, y + 0.002, zz + 0.006), (x, y - 0.002, zz - 0.009), 0.004, "BH_Bone", n=4), "head")
    # HUGE bat ears: out to the sides and up
    for sx in (1, -1):
        rx, cy = K.side_of(H, z0 + 0.07)
        root = (sx * (rx - 0.012), cy + 0.01, z0 + 0.07)
        add(K.ear(root, 0.3, 0.17, "BH_Skin", out=(sx * 1.0, 0.25, 0.45), up=(0, 0.1, 1), droop=0.02, thick=0.012,
                  back=0.03), "head")
        add(K.ear(np.array(root) + (sx * 0.03, -0.01, 0.01), 0.22, 0.1, "BH_Flesh", out=(sx * 1.0, 0.25, 0.45),
                  up=(0, 0.1, 1), droop=0.015, thick=0.004, back=0.022), "head")
    # gold hoop in the left ear
    c = np.array(root) * np.array([-1, 1, 1]) + (0.12, -0.01, 0.04)
    add(K.rtube([c + 0.014 * np.array([0, math.cos(a), math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 9)], 0.0035,
                "BH_Gold", n=4, cap=False), "head")
    crown(body, H, z0)


def crown(body, H, z0):
    parts = []
    r = 0.058
    V, F = M.lathe([(r, 0.0), (r * 1.04, 0.035), (r * 1.0, 0.036), (r * 0.96, 0.001)], 12, cap=False)
    parts.append(M.solidify(M.Part(V, F, "BH_Gold", name="crown"), 0.004, offset=1.0))
    for k in range(6):
        a = 2 * math.pi * k / 6
        base = np.array([r * math.cos(a), r * math.sin(a), 0.034])
        parts.append(K.cone(base, base + (0, 0, 0.034), 0.013, "BH_Gold", n=4))
        parts.append(K.blob(base + (0, 0, 0.037), 0.006, "BH_Gold", n=5, rings=3))
        if k % 2 == 0:
            parts.append(K.blob(np.array([r * 1.05 * math.cos(a), r * 1.05 * math.sin(a), 0.017]), 0.009,
                                "BH_Aether", scale=(1, 1, 1.2), n=6, rings=3))
    for p in parts:
        p.rot(Ry(-22) @ Rx(8)).move((0.05, -STOOP - 0.02, z0 + 0.158))
        body.add(p, "head")


# ---------------------------------------------------------------------------------------------------- chains
def chains(body, rows, TW):
    zn, zc = L["neck"], L["chest"]
    for k, (drop, rr) in enumerate(((0.05, 0.005), (0.085, 0.0055), (0.12, 0.006))):
        pts = []
        for t in np.linspace(-1, 1, 13):
            a = t * math.pi * 0.62
            x = 0.07 * math.sin(a) * (1.0 + 0.15 * k)
            z = zn - 0.015 - drop * (1 - t * t) ** 0.7
            y = K.front_of(rows, x, z) - 0.017 if abs(t) < 0.95 else 0.02
            pts.append((x, y, z))
        body.add(K.rtube(pts, rr, "BH_Gold", n=4, cap=False), weights=TW)
    z = zn - 0.015 - 0.12 - 0.015
    y = K.front_of(rows, 0, z) - 0.03
    body.add(coin((0.0, y, z), (0, -1, 0.2), 0.026), weights=TW)
    body.add(K.blob((0.0, y - 0.006, z), 0.01, "BH_Aether", scale=(1, 0.6, 1), n=6, rings=3), weights=TW)


# ------------------------------------------------------------------------------------------------ gold / sack
def coin(c, n, r=0.02, th=0.005):
    V, F = M.lathe([(0.0, -th / 2), (r, -th / 2), (r, th / 2), (0.0, th / 2)], 10)
    from bh_body import M_align_z
    return M.Part(V, F, "BH_Gold", name="coin").rot(M_align_z(normalize(np.asarray(n, float)))).move(c)


def goblet():
    parts = []
    V, F = M.lathe([(0.0, 0.0), (0.04, 0.0), (0.042, 0.008), (0.012, 0.018), (0.009, 0.07), (0.016, 0.08),
                    (0.045, 0.1), (0.05, 0.15), (0.044, 0.15), (0.0, 0.11)], 12)
    parts.append(M.Part(V, F, "BH_Gold", name="goblet"))
    for k in range(4):
        a = 2 * math.pi * k / 4
        parts.append(K.blob((0.048 * math.cos(a), 0.048 * math.sin(a), 0.128), 0.01, "BH_Aether", n=6, rings=3))
    parts.append(K.blob((0.0, 0.0, 0.075), 0.013, "BH_Aether", n=6, rings=3))
    return parts


def sack(body):
    add = body.add
    zc = L["chest"]
    c = np.array([0.0, 0.31, zc - 0.02])       # sits on the hunched back, hangs down to the seat
    R = np.array([0.28, 0.24, 0.3])
    V, F = M.sphere(1.0, 20, 13)
    sk = M.Part(V, F, "BH_Cloth_Secondary", name="sack")
    # pear shape: wider at the bottom, gathered to a neck at the top, lumpy with the loot inside
    def shape(v):
        z = v[2]
        w = 1.0 + 0.12 * (1 - z) - 0.35 * max(0.0, z - 0.55) / 0.45
        lump = 1.0 + 0.05 * math.sin(v[0] * 7 + v[2] * 5) * math.cos(v[1] * 6)
        return np.array([v[0] * w * lump, v[1] * w * lump, z]) * R
    sk.V = np.array([shape(v) for v in sk.V])
    K.jitter(sk, 0.006, seed=9)
    sk.rot(Rx(-12)).move(c)
    add(sk, "chest")
    top = c + Rx(-12) @ np.array([0.0, 0.0, R[2] * 0.95])
    # open mouth: a rolled lip, and a mound of gold coins heaped out of it
    lip = [top + Rx(-12) @ np.array([0.18 * math.cos(a), 0.155 * math.sin(a), 0.0]) for a in np.linspace(0, 2 * math.pi, 15)]
    add(K.rtube(lip, 0.022, "BH_Cloth_Secondary", n=6, cap=False), "chest")
    V, F = M.sphere(1.0, 16, 8)
    mound = M.Part(V, F, "BH_Gold", name="gold_mound")
    mound.V = mound.V * np.array([0.185, 0.16, 0.12])
    K.jitter(mound, 0.008, seed=3)
    mound.rot(Rx(-12)).move(top + (0, 0, 0.01))
    add(mound, "chest")
    rng = np.random.default_rng(21)
    for k in range(30):
        a = 2 * math.pi * rng.random()
        rr = 0.18 * math.sqrt(rng.random())
        p = top + Rx(-12) @ np.array([rr * math.cos(a), rr * 0.88 * math.sin(a), 0.115 * max(0.0, 1 - (rr / 0.19) ** 2) + 0.014])
        n = normalize(np.array([rng.random() - 0.5, rng.random() - 0.5, 1.2]))
        add(coin(p, n, 0.022 + 0.008 * rng.random()), "chest")
    for (dx, dy, ang) in ((-0.08, 0.04, 30), (0.02, 0.08, -35)):
        ing = M.Part(*M.box(0.035, 0.07, 0.03), "BH_Gold", name="ingot")
        ing.rot(Rx(ang) @ Rz(20 + ang)).move(top + Rx(-12) @ np.array([dx, dy, 0.1]))
        add(ing, "chest")
    # jewelled goblet tipped out of the heap, a pearl string trailing over the lip
    for prt in goblet():
        prt.rot(Rx(-40) @ Ry(25)).move(top + (0.07, -0.06, 0.07))
        add(prt, "chest")
    pearls = [top + Rx(-12) @ np.array([-0.13 + 0.02 * i, -0.1 - 0.012 * math.sin(i), 0.02 - 0.012 * i])
              for i in range(8)]
    for p in pearls:
        add(K.blob(p, 0.011, "BH_Bone", n=6, rings=4), "chest")
    # rope tie + strap: from the sack neck over both shoulders, round under the arms
    zn = L["neck"]
    for sx in (1, -1):
        pts = [top + (sx * 0.1, -0.08, -0.06), (sx * 0.06, 0.07, zn + 0.01), (sx * 0.075, -0.02 - STOOP, zn - 0.015),
               (sx * 0.085, -0.075, zc + 0.02), (sx * 0.1, -0.04, zc - 0.06), (sx * 0.1, 0.05, zc - 0.08),
               c + (sx * 0.15, -0.2, -0.15)]
        add(K.rtube(pts, (0.011, 0.005), "BH_Leather", n=5, up=(0, 0, 1), p=3.0), weights=K.torso_w(PROPS))
    # split seam low on the right side with coins spilling out (frozen in the fall)
    s = c + np.array([-0.24, 0.02, -0.12])
    add(K.blob(s, 0.045, "BH_Gold", scale=(0.5, 1.0, 0.8), n=8, rings=5), "chest")
    add(K.rtube([s + (0.01, -0.04, 0.03), s + (-0.012, 0.0, 0.045), s + (0.01, 0.04, 0.03)], 0.01, "BH_Cloth_Secondary",
                n=5), "chest")
    for i in range(3):
        p = s + np.array([-0.035 - 0.01 * i, -0.01 + 0.025 * math.sin(i * 2.1), -0.035 - 0.03 * i])
        add(coin(p, (0.7 * math.cos(i), 0.5, 0.6 * math.sin(i * 1.7)), 0.018), "chest")
    # patches on the sack
    for (dx, dz) in ((0.12, -0.08), (-0.08, 0.1)):
        q = c + Rx(-12) @ np.array([dx, R[1] * 0.98, dz])
        add(M.Part(*M.box(0.08, 0.008, 0.07, center=q), "BH_Leather", name="sack_patch"), "chest")
