"""Mire Troll (beast / brute; Builder B, bh-010): a ~2.8 m hunched swamp giant. Lean, long-limbed body with a high
mossy hump, arms so long the knuckles hang at the knees, huge half-open clawed hands, a small head thrust forward and
low with a long drooping nose, an underbite with two jutting lower tusks, drooping ears and tiny yellow-green eyes.
Mottled grey-green hide with dark blotches, moss clumps on the hump / shoulders / head, wet mud caked up the shins and
splashed on the forearms, swamp weed and roots hanging from the shoulders and arms, a rotten-hide loin wrap on a vine
belt with bone trophies (a small skull, long bones) and a tooth necklace. Thick legs and big flat four-toed feet.
No chains, no armour: wetter, leaner, longer-limbed and mossier than the Ogre Crusher. Modelled at true size on the
shared humanoid skeleton (proportions()), kit: ../creatures/greenskin_kit.py."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft, smoothstep, M_align_z  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as K  # noqa: E402
from enemy_bandit_cutthroat import ring_frac  # noqa: E402

S = 1.5
PROPS = proportions(
    S,
    pelvis_h=1.40, hip_h=1.32, knee_h=0.74, ankle_h=0.13, hip_x=0.21, ball_fwd=0.25, ball_h=0.04, toe_len=0.13,
    heel_back=0.1,
    hips_len=0.18, spine_len=0.36, chest_len=0.60, neck_len=0.12, head_len=0.28,
    clav_x0=0.08, clav_drop=0.1, shoulder_x=0.37, upper_len=0.78, fore_len=0.72, hand_len=0.25, grip_x=0.15,
    grip_drop=0.03,
)
L = K.levels(PROPS)
PREVIEW_HEIGHT = 3.2

PALETTE = "mire_troll"
PALETTE_COLORS = {
    "BH_Skin": ((0.19, 0.22, 0.155), 0.0, 0.5, None, 0.0, 1.0),            # grey-green hide
    "BH_Flesh": ((0.085, 0.095, 0.06), 0.0, 0.5, None, 0.0, 1.0),          # dark mottling blotches
    "BH_Fur": ((0.075, 0.14, 0.03), 0.0, 0.95, None, 0.0, 1.0),            # moss
    "BH_Hair": ((0.045, 0.06, 0.025), 0.0, 0.6, None, 0.0, 1.0),           # hanging swamp weed / hair strands
    "BH_Ichor": ((0.065, 0.045, 0.028), 0.0, 0.28, None, 0.0, 1.0),        # wet mud
    "BH_Wood": ((0.1, 0.07, 0.045), 0.0, 0.8, None, 0.0, 1.0),             # roots, vine belt
    "BH_Leather": ((0.11, 0.085, 0.055), 0.0, 0.85, None, 0.0, 1.0),       # rotten hide loin wrap
    "BH_Bone": ((0.56, 0.52, 0.38), 0.0, 0.6, None, 0.0, 1.0),             # tusks, bone trophies
    "BH_Horn": ((0.13, 0.11, 0.08), 0.0, 0.45, None, 0.0, 1.0),            # claws, toenails
    "BH_Shadow": ((0.025, 0.02, 0.018), 0.0, 0.8, None, 0.0, 1.0),         # mouth, sockets
    "BH_Emissive": ((0.85, 0.9, 0.3), 0.0, 0.4, (0.8, 0.95, 0.25), 3.0, 1.0),  # small eyes
}

CLIPS = ["axe_1", "axe_2", "boss_slam", "cast_heavy", "boss_roar", "boss_charge"]

HEAD_DY, HEAD_DZ = -0.36, -0.2        # head thrust forward and down from the head joint, below the hump


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def const_w(wfn, c):
    w = wfn(np.asarray([c], float))[0]
    return lambda V: [dict(w)] * len(V)


def torso_weights():
    """greenskin torso weights, but the hump above the neck joint stays on the chest (the neck tube carries the head)."""
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
        (zh - 0.2, 0.3, 0.23, 0.24, 0.0, 0.0),
        (zh - 0.02, 0.33, 0.27, 0.26, 0.02, -0.01),
        (zs + 0.06, 0.3, 0.26, 0.24, 0.03, -0.03),        # lean waist
        (zc - 0.08, 0.35, 0.26, 0.28, 0.05, -0.03),
        (zc + 0.14, 0.43, 0.27, 0.36, 0.07, -0.04),       # ribcage, hump rising
        (zn - 0.18, 0.48, 0.27, 0.44, 0.05, -0.04),       # shoulders
        (zn - 0.05, 0.45, 0.22, 0.47, 0.0, 0.0),
        (zn + 0.07, 0.36, 0.14, 0.42, 0.0, 0.05),         # hump rising above and behind the head
        (zn + 0.16, 0.22, 0.08, 0.3, 0.0, 0.08),
        (zn + 0.22, 0.08, 0.04, 0.13, 0.0, 0.1),
    ]


HEAD = [  # (dz, rx, ryf, ryb, keel, cy) small skull, heavy protruding lower jaw
    (-0.06, 0.06, 0.07, 0.05, 0.0, -0.05),
    (-0.035, 0.13, 0.16, 0.08, 0.06, -0.06),
    (0.0, 0.145, 0.175, 0.1, 0.06, -0.055),
    (0.04, 0.13, 0.15, 0.12, 0.05, -0.04),
    (0.09, 0.12, 0.13, 0.13, 0.06, -0.03),
    (0.14, 0.12, 0.12, 0.14, 0.02, -0.025),
    (0.19, 0.105, 0.1, 0.13, 0.0, -0.02),
    (0.225, 0.075, 0.07, 0.1, 0.0, -0.02),
    (0.245, 0.035, 0.035, 0.05, 0.0, -0.02),
]


def hrows():
    return K.head_rows(HEAD, L["head"] + HEAD_DZ, dy=HEAD_DY)


# ================================================================================================= build
def build(body: Body):
    add = body.add
    TW = torso_weights()
    rows = torso_rows()
    V, F = torso_loft(rows, n=26, p=2.2, cap0=True, cap1=False)
    tor = M.Part(V, F, "BH_Skin", name="torso")
    K.jitter(tor, 0.005, seed=12)
    add(tor, weights=TW)
    zc, zs, zn, zh = L["chest"], L["spine"], L["neck"], L["hips"]
    # ribs on the flanks, collar bones, a sagging belly
    for sx in (1, -1):
        for k, z in enumerate((zc + 0.02, zc + 0.12, zc + 0.22)):
            pts = []
            for f in np.linspace(0.1, 0.22, 5):
                q = ring_frac(rows, z - 0.25 * (f - 0.1), 0.0, [f if sx > 0 else 1 - f], p=2.2)[0]
                pts.append(q)
            add(K.rtube(pts, [0.012, 0.02, 0.022, 0.02, 0.012], "BH_Skin", n=6), weights=TW)
    add(K.blob((0, -0.24, zs + 0.02), 0.22, "BH_Skin", scale=(1.05, 0.45, 0.75), n=12, rings=7), weights=TW)
    add(K.blob((0, -0.35, zs + 0.0), 0.022, "BH_Shadow", scale=(1, 0.4, 1.2), n=6, rings=4), weights=TW)
    mottle_torso(body, rows, TW)
    moss_and_weed(body, rows, TW)
    loin(body)
    necklace(body, rows, TW)

    for s in ("L", "R"):
        sx = 1 if s == "L" else -1
        pts = K.leg(body, s, [(0.23, 0.24), (0.2, 0.21), (0.16, 0.17), (0.16, 0.17), (0.17, 0.18), (0.12, 0.12)],
                    "BH_Skin", bow=0.04, n=14, top_up=0.1)
        # knobbly knee
        add(K.blob(body.head("shin." + s) + np.array([sx * 0.04, -0.13, 0.02]), 0.09, "BH_Skin",
                   scale=(1, 0.7, 1.1), n=8, rings=5), "shin." + s)
        K.bare_foot(body, s, "BH_Skin", length=0.58, width=0.17, height=0.13, claw_mat="BH_Horn", toes=4,
                    toe_r=0.046)
        mud_leg(body, s)
        K.arm(body, s, [(0.16, 0.17), (0.12, 0.13), (0.1, 0.11), (0.11, 0.11), (0.13, 0.125), (0.09, 0.085)],
              "BH_Skin", n=14, deltoid=0.17)
        el = body.head("forearm." + s)
        add(K.blob(el + np.array([0.0, 0.1, 0.0]), 0.07, "BH_Skin", scale=(1, 0.8, 1), n=8, rings=5), "forearm." + s)
        claw_hand(body, s)
        arm_dressing(body, s)
    head(body)


# ------------------------------------------------------------------------------------------------- hide & swamp
def surf(rows, frac, z, g=0.0):
    q = ring_frac(rows, z, g, [frac % 1.0], p=2.2)[0]
    a = 2 * math.pi * frac - math.pi / 2
    n = normalize(np.array([math.cos(a), math.sin(a), 0.15]))
    return q, n


def patch(c, n, r, mat, flat=0.25, seed=0, n_seg=10):
    p = K.blob((0, 0, 0), r, mat, scale=(1.0, 1.0, flat), n=n_seg, rings=5)
    K.jitter(p, r * 0.06, seed=seed)
    p.rot(M_align_z(n))
    return p.move(np.asarray(c) + np.asarray(n) * r * flat * 0.3)


def mottle_torso(body, rows, TW):
    rng = np.random.default_rng(31)
    zlo, zhi = L["hips"] - 0.1, L["neck"] - 0.02
    for i in range(26):
        f = rng.random()
        z = zlo + (zhi - zlo) * rng.random()
        q, n = surf(rows, f, z)
        body.add(patch(q, n, 0.05 + 0.06 * rng.random(), "BH_Flesh", flat=0.12, seed=i), weights=TW)


def moss_and_weed(body, rows, TW):
    add = body.add
    rng = np.random.default_rng(7)
    zn = L["neck"]
    # moss blanket over the hump and shoulder tops
    for i in range(30):
        f = 0.28 + 0.44 * rng.random()
        z = zn - 0.5 + 0.66 * rng.random() ** 0.6
        q, n = surf(rows, f, z)
        n = normalize(n + np.array([0, 0, 0.6]))
        add(patch(q, n, 0.07 + 0.06 * rng.random(), "BH_Fur", flat=0.4, seed=100 + i, n_seg=10), weights=TW)
    for s, sx in (("L", 1), ("R", -1)):
        sh = body.head("upper_arm." + s)
        for k, (dx, dy, dz, r) in enumerate(((-0.1, 0.05, 0.16, 0.12), (0.02, 0.08, 0.14, 0.1),
                                            (-0.2, 0.12, 0.13, 0.11), (0.06, -0.04, 0.12, 0.08))):
            add(K.jitter(K.blob(sh + (sx * dx, dy, dz), r, "BH_Fur", scale=(1.1, 1.0, 0.45), n=10, rings=5), 0.008,
                         seed=k + 3 * (sx > 0)),
                weights=lambda V, s=s: [{"chest": 0.5, "shoulder." + s: 0.5}] * len(V))
    # swamp weed strands hanging down the back from the hump (bend with the spine)
    for i in range(9):
        f = 0.36 + 0.28 * (i / 8) + 0.02 * rng.normal()
        z0 = zn - 0.12 - 0.12 * rng.random()
        q, n = surf(rows, f, z0, 0.03)
        ln = 0.45 + 0.35 * rng.random()
        pts = []
        for t in np.linspace(0, 1, 6):
            z = z0 - ln * t
            qq, nn = surf(rows, f, max(z, L["hips"] - 0.15), 0.035 + 0.05 * t)
            qq[2] = z
            qq[0] += 0.03 * math.sin(t * 5 + i)
            pts.append(qq)
        prof = [(0.03 * (1 - 0.6 * t), 0.006) for t in np.linspace(0, 1, 6)]
        ups = [np.array([0, 1.0, 0])] * 6
        V, F = M.tube(pts, prof, n=4, up=ups, p=3.0)
        add(M.Part(V, F, "BH_Hair", name="weed"), weights=TW)
    # a root draped over the right shoulder, front to back
    pts = [(-0.3, -0.26, zn - 0.35), (-0.36, -0.22, zn - 0.12), (-0.38, -0.05, zn + 0.0), (-0.36, 0.2, zn - 0.05),
           (-0.3, 0.36, zn - 0.3), (-0.25, 0.38, zn - 0.55)]
    add(K.rtube(pts, [0.012, 0.022, 0.026, 0.024, 0.018, 0.008], "BH_Wood", n=6), weights=TW)
    for (a, b) in ((1, (-0.32, -0.34, zn - 0.2)), (3, (-0.2, 0.44, zn - 0.2))):
        add(K.rtube([pts[a], b], [0.014, 0.004], "BH_Wood", n=5), weights=TW)


def loin(body):
    add = body.add
    zh = L["hips"]
    V, F = torso_loft([(zh - 0.32, 0.31, 0.25, 0.26, 0.0), (zh - 0.16, 0.34, 0.29, 0.28, 0.0),
                       (zh + 0.02, 0.35, 0.3, 0.28, 0.02, -0.01)], n=24)
    add(M.Part(V, F, "BH_Leather", name="seat"), weights=K.seat_w(body, zh - 0.02, zh - 0.32, 0.75))
    # ragged hide flaps front and back, each split up the middle so each half follows its own thigh
    def flap_w(V):
        out = []
        for v in V:
            if v[1] < 0:      # front flap: follows its thigh from just under the belt
                t = float(smoothstep(zh - 0.04, zh - 0.34, v[2]))
            else:             # back flap: hangs from the hips (the thigh pivots far in front of it)
                t = 0.55 * float(smoothstep(zh - 0.15, zh - 0.6, v[2]))
            side = "thigh.L" if v[0] > 0 else "thigh.R"
            out.append({k: x for k, x in (("hips", 1 - t), (side, t)) if x > 1e-4})
        return out
    for sgn in (-1, 1):
        for sx in (1, -1):
            def fn(u, v, sgn=sgn, sx=sx):
                uu = 0.5 + 0.5 * sx * (0.03 + 0.97 * u)
                x = (uu - 0.5) * (0.46 - 0.1 * v)
                z = zh + 0.0 - 0.6 * v
                y = sgn * ((0.31 if sgn < 0 else 0.3) + 0.05 * v) + 0.015 * math.sin(uu * 11 + v * 4)
                return (x, y, z)
            V, F = M.grid(fn, 4, 6)
            fl = M.Part(V, F, "BH_Leather", name="flap")
            if (sgn > 0) != (sx < 0):
                fl.flip()
            hem = np.array([0.03, -0.06, 0.02, -0.08, 0.0, -0.05, 0.04])
            fl.V[-4:, 2] += hem[3:] if sx > 0 else hem[3::-1]
            add(M.solidify(fl, 0.02, offset=1.0), weights=flap_w)
    # vine belt
    ring = [(0.36 * math.cos(a), (0.33 if math.sin(a) < 0 else 0.3) * math.sin(a) - 0.01, zh + 0.01 + 0.02 * math.sin(3 * a))
            for a in np.linspace(0, 2 * math.pi, 25)]
    add(K.rtube(ring, 0.024, "BH_Wood", n=6, up=(0, 0, 1), cap=False), "hips")
    ring2 = [(0.365 * math.cos(a), (0.335 if math.sin(a) < 0 else 0.305) * math.sin(a) - 0.01,
              zh + 0.01 + 0.02 * math.sin(3 * a + 1.3)) for a in np.linspace(0, 2 * math.pi, 25)]
    add(K.rtube(ring2, 0.014, "BH_Wood", n=5, up=(0, 0, 1), cap=False), "hips")
    # bone trophies hanging from the belt: small skull (left front), long bones (right front / right side)
    hang = K.seat_w(body, zh, zh - 0.5, 0.35, center_w=0.1)
    c = np.array([0.22, -0.34, zh - 0.14])
    parts = [K.blob(c, 0.075, "BH_Bone", scale=(0.9, 0.95, 1.0), n=10, rings=7),
             K.blob(c + (0, -0.03, -0.065), 0.05, "BH_Bone", scale=(0.9, 0.9, 0.6), n=8, rings=5)]
    for ex in (-0.028, 0.028):
        parts.append(K.blob(c + (ex, -0.062, 0.005), 0.02, "BH_Shadow", scale=(1, 0.5, 1.1), n=6, rings=4))
    parts.append(K.blob(c + (0, -0.08, -0.03), 0.01, "BH_Shadow", scale=(1, 0.5, 1.5), n=5, rings=3))
    parts.append(K.rtube([(0.22, -0.33, zh + 0.0), c + (0, 0, 0.07)], 0.008, "BH_Wood", n=5))
    for prt in parts:
        add(prt, weights=const_w(hang, c))
    for (x, y, ln, tilt) in ((-0.2, -0.33, 0.3, 12), (-0.29, -0.2, 0.26, -10), (0.1, -0.35, 0.22, 6)):
        top = np.array([x, y, zh - 0.02])
        d = normalize(np.array([math.sin(math.radians(tilt)), -0.1, -1.0]))
        bot = top + d * ln
        bparts = [K.rtube([top, bot], [0.018, 0.016], "BH_Bone", n=7),
                  K.blob(top, 0.028, "BH_Bone", scale=(1.3, 1, 0.8), n=7, rings=4),
                  K.blob(bot, 0.03, "BH_Bone", scale=(1.3, 1, 0.8), n=7, rings=4)]
        for prt in bparts:
            add(prt, weights=const_w(hang, (top + bot) / 2))


def necklace(body, rows, TW):
    """Vine cord round the base of the neck with big teeth / finger bones hanging on the chest."""
    zn = L["neck"]
    pts = []
    for f in np.linspace(-0.3, 0.3, 13):
        z = zn - 0.02 - 0.2 * math.cos(f * math.pi / 0.6) ** 2
        q = ring_frac(rows, z, 0.02, [f % 1.0], p=2.2)[0]
        pts.append(q)
    body.add(K.rtube(pts, 0.012, "BH_Wood", n=5), weights=TW)
    for k in (2, 4, 5, 6, 7, 8, 10):
        q = np.asarray(pts[k])
        body.add(K.cone(q + (0, -0.01, 0.0), q + (0.01 * (k - 6), -0.03, -0.1 - 0.02 * (k % 2)), 0.02, "BH_Bone", n=6),
                 weights=TW)


def mud_leg(body, s):
    """Wet mud caked up the shin (jagged top edge) and over the top of the foot."""
    sh = "shin." + s
    k, a = body.head(sh), body.tail(sh)
    pts = [a + (0, 0, -0.03), a + (k - a) * 0.3, a + (k - a) * 0.55]
    V, F = M.tube(pts, [(0.14, 0.145), (0.18, 0.19), (0.18, 0.19)], n=16, up=(0, -1, 0), cap0=False, cap1=False)
    mud = M.Part(V, F, "BH_Ichor", name="mud")
    top = pts[-1][2]
    rng = np.random.default_rng(3 if s == "L" else 4)
    noise = rng.random(64)

    def w(v):
        if v[2] > top - 0.01:
            ang = math.atan2(v[1] - a[1], v[0] - a[0])
            i = int((ang + math.pi) / (2 * math.pi) * 16) % 16
            return (v[0], v[1], v[2] - 0.12 * noise[i] - 0.04 * (i % 2))
        return tuple(v)
    mud.warp(w)
    K.jitter(mud, 0.006, seed=5)
    body.add(M.solidify(mud, 0.01, offset=-1.0), sh)
    # clods on the foot and ankle
    hx = PROPS["hip_x"] * (1 if s == "L" else -1)
    for (dx, y, z, r) in ((0.04, -0.12, 0.13, 0.07), (-0.05, -0.2, 0.1, 0.06), (0.0, 0.02, 0.16, 0.08)):
        body.add(K.jitter(K.blob((hx + dx, y, z), r, "BH_Ichor", scale=(1.2, 1.1, 0.55), n=8, rings=5), 0.006,
                          seed=int(10 * r)), "foot." + s)


def arm_dressing(body, s):
    """Moss on the forearm, mud splashes, weed strands hanging from the upper arm and wrist."""
    add = body.add
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
    sx = 1 if s == "L" else -1
    d = normalize(wr - el)
    out = normalize(np.array([sx, 0.0, 0.0]) - d * d[0] * sx)
    back = np.array([0, 1.0, 0])
    for k, (u, dirv, r) in enumerate(((0.3, out, 0.08), (0.55, back, 0.07), (0.75, out * 0.6 + back * 0.6, 0.06))):
        c = el + (wr - el) * u + normalize(dirv) * 0.11
        add(patch(c, normalize(dirv), r, "BH_Fur", flat=0.45, seed=50 + k + (sx > 0) * 10), fa)
    for k, (u, dirv, r) in enumerate(((0.2, -back, 0.07), (0.45, -out, 0.06), (0.85, -back * 0.7 - out * 0.3, 0.05))):
        c = el + (wr - el) * u + normalize(dirv) * 0.115
        add(patch(c, normalize(dirv), r, "BH_Ichor", flat=0.2, seed=70 + k + (sx > 0) * 10), fa)
    for k, (u, dirv, r) in enumerate(((0.35, back, 0.08), (0.6, out, 0.07))):
        c = sh + (el - sh) * u + normalize(dirv) * 0.12
        add(patch(c, normalize(dirv), r, "BH_Flesh", flat=0.12, seed=90 + k), ua)
    # weed strands hanging from the back of the upper arm (rigid to upper arm; they hang in the modelling pose)
    for k in range(3):
        top = sh + (el - sh) * (0.35 + 0.18 * k) + back * 0.12 + out * 0.03 * k
        pts = [top, top + np.array([sx * 0.02, 0.03, -0.12]), top + np.array([sx * 0.0, 0.05, -0.25 - 0.06 * k])]
        V, F = M.tube(pts, [(0.024, 0.005), (0.02, 0.005), (0.01, 0.004)], n=4, up=[np.array([sx, 0, 0])] * 3, p=3.0)
        add(M.Part(V, F, "BH_Hair", name="weed"), ua)
    for k in range(2):
        top = el + (wr - el) * (0.6 + 0.2 * k) - back * 0.1
        pts = [top, top + np.array([0.0, -0.04, -0.12]), top + np.array([sx * 0.02, -0.05, -0.22])]
        V, F = M.tube(pts, [(0.02, 0.005), (0.016, 0.004), (0.008, 0.003)], n=4, up=[np.array([sx, 0, 0])] * 3, p=3.0)
        add(M.Part(V, F, "BH_Hair", name="weed"), fa)


def claw_hand(body, s, scale=2.5):
    """Huge half-open clawed hand, rigid to hand.<s>, built in the weapon-socket frame (x distal, y thumb side,
    z back of the hand) like bh_body.fist."""
    A = body.axes("weapon." + s)
    o = body.head("weapon." + s)
    xs = 1.0 if s == "R" else -1.0

    def P(x, y, z):
        return o + A @ (np.array([x * xs, y, z]) * scale)
    add = lambda prt: body.add(prt, "hand." + s)  # noqa: E731
    # palm block
    rings = []
    for x, wy, hz, zc in ((-0.075, 0.032, 0.024, 0.018), (-0.05, 0.045, 0.03, 0.012), (-0.01, 0.05, 0.032, 0.006),
                          (0.02, 0.05, 0.028, 0.004), (0.03, 0.046, 0.022, 0.004)):
        ring = []
        for i in range(12):
            a = 2 * math.pi * i / 12
            ring.append(P(x, wy * np.sign(math.cos(a)) * abs(math.cos(a)) ** 0.7,
                          zc + hz * np.sign(math.sin(a)) * abs(math.sin(a)) ** 0.7))
        rings.append(np.array(ring))
    V, F = M.loft(rings)
    add(M.Part(V, F, "BH_Skin", name="palm"))
    # four long fingers: out along x, curling toward the palm (-z), claws at the tips
    for k in range(4):
        y = -0.033 + 0.022 * k
        ln = 0.055 + 0.01 * (k in (1, 2))
        pts = [P(0.025, y, 0.008), P(0.025 + ln * 0.6, y * 1.1, 0.002), P(0.025 + ln * 1.0, y * 1.15, -0.02),
               P(0.025 + ln * 1.05, y * 1.15, -0.045)]
        rr = [0.0125 * scale, 0.011 * scale, 0.0095 * scale, 0.008 * scale]
        add(K.rtube(pts, rr, "BH_Skin", n=7))
        add(K.blob(pts[1], 0.012 * scale, "BH_Skin", n=6, rings=4))
        tip = pts[-1]
        dirv = normalize(pts[-1] - pts[-2])
        add(K.cone(tip - dirv * 0.004 * scale, tip + dirv * 0.03 * scale + (P(0, 0, -0.01) - o) * 0.4,
                   0.008 * scale, "BH_Horn", n=6))
    # thumb
    pts = [P(-0.045, 0.045, -0.005), P(-0.01, 0.07, -0.02), P(0.02, 0.07, -0.04)]
    add(K.rtube(pts, [0.013 * scale, 0.012 * scale, 0.01 * scale], "BH_Skin", n=7))
    tip = pts[-1]
    dirv = normalize(pts[-1] - pts[-2])
    add(K.cone(tip, tip + dirv * 0.028 * scale, 0.008 * scale, "BH_Horn", n=6))
    # mud on the back of the hand
    add(patch(P(-0.02, 0.0, 0.035), A[:, 2], 0.03 * scale, "BH_Ichor", flat=0.25, seed=int(xs + 5)))


# ------------------------------------------------------------------------------------------------- head
def head(body):
    add = body.add
    z0 = L["head"] + HEAD_DZ
    H = hrows()
    zn = L["neck"]
    # neck: from the top of the chest forward and up into the head (chest -> neck -> head by y)
    pts = [(0, 0.0, zn - 0.1), (0, -0.12, zn - 0.08), (0, HEAD_DY + 0.12, z0 + 0.02), (0, HEAD_DY + 0.05, z0 + 0.06)]
    V, F = M.tube(pts, [(0.2, 0.19), (0.19, 0.18), (0.15, 0.14), (0.12, 0.12)], n=14, up=(0, 0, 1))

    def neck_w(V):
        out = []
        for v in V:
            t = float(smoothstep(-0.06, -0.16, v[1]))
            u = float(smoothstep(HEAD_DY + 0.16, HEAD_DY + 0.04, v[1]))
            d = {"chest": 1 - t, "neck": t * (1 - u), "head": t * u}
            out.append({k: x for k, x in d.items() if x > 1e-4})
        return out
    add(M.Part(V, F, "BH_Skin", name="neck"), weights=neck_w)
    V, F = torso_loft(H, n=20, p=2.2, cap0=True, cap1=True)
    hd = M.Part(V, F, "BH_Skin", name="head")
    K.jitter(hd, 0.003, seed=8)
    add(hd, "head")
    cy = HEAD_DY
    # heavy brow ridge
    zb = z0 + 0.135
    yb = K.front_of(H, 0, zb)
    add(K.rtube([(-0.1, yb + 0.05, zb - 0.015), (0, yb - 0.005, zb + 0.005), (0.1, yb + 0.05, zb - 0.015)], 0.03,
                "BH_Skin", n=7, up=(0, -1, 0)), "head")
    # small deep eyes
    for sx in (1, -1):
        ye = K.front_of(H, 0.05, z0 + 0.11)
        add(K.blob((sx * 0.05, ye + 0.006, z0 + 0.11), 0.024, "BH_Shadow", scale=(1.2, 0.5, 0.7), n=8, rings=4),
            "head")
        add(K.blob((sx * 0.05, ye - 0.002, z0 + 0.11), 0.011, "BH_Emissive", n=6, rings=4), "head")
    # long drooping nose: root between the eyes, hangs down past the upper lip to a bulbous tip
    yn = K.front_of(H, 0, z0 + 0.1)
    npts = [(0, yn + 0.01, z0 + 0.115), (0, yn - 0.04, z0 + 0.075), (0, yn - 0.075, z0 + 0.02),
            (0, yn - 0.085, z0 - 0.04), (0, yn - 0.07, z0 - 0.075)]
    add(K.rtube(npts, [0.026, 0.03, 0.034, 0.042, 0.03], "BH_Skin", n=10, up=(1, 0, 0)), "head")
    add(K.blob((0, yn - 0.08, z0 - 0.05), 0.048, "BH_Skin", scale=(1.0, 0.95, 1.1), n=10, rings=6), "head")
    for sx in (1, -1):
        add(K.blob((sx * 0.025, yn - 0.075, z0 - 0.088), 0.01, "BH_Shadow", scale=(1, 1, 0.6), n=5, rings=3), "head")
    # wide mouth line under the nose + underbite lower lip, two big tusks jutting up outside the nose
    zm = z0 - 0.018
    add(K.rtube([(x, K.front_of(H, x, zm) + 0.004, zm + 3 * x * x) for x in np.linspace(-0.12, 0.12, 9)], 0.012,
                "BH_Shadow", n=5), "head")
    zl = z0 - 0.04
    add(K.rtube([(x, K.front_of(H, x, zl) - 0.018, zl + 3 * x * x) for x in np.linspace(-0.13, 0.13, 9)], 0.024,
                "BH_Flesh", n=6), "head")
    for sx in (1, -1):
        b = np.array([sx * 0.08, K.front_of(H, 0.08, zl) - 0.02, zl + 0.01])
        add(K.rtube([b, b + (sx * 0.012, -0.018, 0.06), b + (sx * 0.028, -0.02, 0.115)], [0.024, 0.018, 0.004],
                    "BH_Bone", n=7), "head")
        b2 = np.array([sx * 0.035, K.front_of(H, 0.035, zl) - 0.024, zl + 0.012])
        add(K.cone(b2, b2 + (0, -0.004, 0.032), 0.01, "BH_Bone", n=5), "head")
    # long drooping ears
    for sx in (1, -1):
        rx, cyy = K.side_of(H, z0 + 0.1)
        add(K.ear((sx * (rx - 0.015), cyy + 0.02, z0 + 0.1), 0.2, 0.11, "BH_Skin", out=(sx, 0.35, -0.25),
                  up=(0, 0, 1), droop=0.35, thick=0.02), "head")
    # stringy weed-hair and a moss cap on the crown
    rng = np.random.default_rng(17)
    add(K.jitter(K.blob((0.0, cy + 0.04, z0 + 0.21), 0.11, "BH_Fur", scale=(1.1, 1.3, 0.45), n=10, rings=5), 0.01,
                 seed=2), "head")
    for i in range(8):
        a = math.pi * (0.15 + 0.7 * i / 7)
        top = np.array([0.1 * math.cos(a), cy + 0.03 + 0.1 * math.sin(a), z0 + 0.2])
        pts = [top, top + (0.04 * math.cos(a), 0.05 + 0.02 * math.sin(a), -0.1),
               top + (0.06 * math.cos(a), 0.09, -0.22 - 0.06 * rng.random())]
        V, F = M.tube(pts, [(0.02, 0.005), (0.016, 0.004), (0.008, 0.003)], n=4,
                      up=[np.array([math.cos(a), math.sin(a), 0.0])] * 3, p=3.0)
        add(M.Part(V, F, "BH_Hair", name="hair"), "head")
