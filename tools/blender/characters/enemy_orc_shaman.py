"""Orc Shaman (bh-010, Builder A; orc support caster): an old, hunched, grey-green orc elder. A great antler headdress
on a leather cap hung with bone fetishes and feathers (the silhouette key), a grey wolf pelt worn as a mantle with the
wolf's head on the left shoulder and its tail down the back, long grey hair and a braided beard with bone beads, worn
tusks (one broken), blue-white war paint, strands of beads on the chest, a long hide kilt with a fur hem and a fetish
belt, wrapped shins, and a gnarled totem staff with a carved face whose root-claws grip a crackling blue-white
lightning crystal. ~1.9 m to the crown (the antlers rise to ~2.3 m). Kit: greenskin_kit."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft, dome, smoothstep, front_y, back_y, interp_rows  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz, R_axis  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as K  # noqa: E402
import enemy_bandit_cutthroat as BK  # noqa: E402
import kit_a_common as A  # noqa: E402

S = 1.08
PROPS = proportions(
    S,
    pelvis_h=1.03, hip_h=0.99, knee_h=0.55, ankle_h=0.09, hip_x=0.12,
    hips_len=0.11, spine_len=0.19, chest_len=0.27, neck_len=0.08, head_len=0.21,
    clav_x0=0.05, clav_drop=0.05, shoulder_x=0.245, upper_len=0.31, fore_len=0.29, hand_len=0.11, grip_x=0.08,
)
L = K.levels(PROPS)

PALETTE = "orc_shaman"
PALETTE_COLORS = {
    "BH_Skin": ((0.14, 0.165, 0.11), 0.0, 0.6, None, 0.0, 1.0),              # old grey-green
    "BH_Flesh": ((0.07, 0.08, 0.055), 0.0, 0.6, None, 0.0, 1.0),
    "BH_Fur": ((0.2, 0.2, 0.19), 0.0, 0.95, None, 0.0, 1.0),                 # grey wolf pelt
    "BH_Leather": ((0.085, 0.05, 0.028), 0.0, 0.68, None, 0.0, 1.0),         # kilt, cap, wraps
    "BH_Bone": ((0.6, 0.55, 0.43), 0.0, 0.6, None, 0.0, 1.0),                # fetishes, beads, tusks
    "BH_Horn": ((0.34, 0.27, 0.18), 0.0, 0.7, None, 0.0, 1.0),               # antlers
    "BH_Wood": ((0.1, 0.07, 0.045), 0.0, 0.8, None, 0.0, 1.0),               # gnarled staff, wooden beads
    "BH_Hair": ((0.42, 0.41, 0.38), 0.0, 0.8, None, 0.0, 1.0),               # grey hair / beard
    "BH_Cloth_Primary": ((0.3, 0.05, 0.03), 0.0, 0.88, None, 0.0, 1.0),      # dark red wraps / feathers
    "BH_Cloth_Secondary": ((0.55, 0.68, 0.8), 0.0, 0.7, None, 0.0, 1.0),     # blue-white war paint
    "BH_Shadow": ((0.03, 0.025, 0.02), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((0.72, 0.9, 1.0), 0.0, 0.3, (0.6, 0.85, 1.0), 10.0, 1.0),  # lightning crystal, eyes
}

CLIPS = ["staff_1", "staff_2", "cast_quick", "cast_area", "cast_heavy", "cast_weapon", "war_cry"]


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def torso_rows():
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    return [
        (zh - 0.10, 0.16, 0.11, 0.115, 0.0, 0.0),
        (zh + 0.02, 0.165, 0.13, 0.115, 0.05, 0.0),
        (zs + 0.06, 0.17, 0.145, 0.115, 0.1, -0.005),     # sagging belly
        (zc + 0.02, 0.185, 0.14, 0.13, 0.08, 0.0),
        (zc + 0.13, 0.21, 0.13, 0.16, 0.05, 0.012),       # hunched upper back
        (zn - 0.06, 0.225, 0.12, 0.17, 0.03, 0.03),
        (zn - 0.01, 0.18, 0.1, 0.14, 0.0, 0.04),
        (zn + 0.035, 0.085, 0.07, 0.08, 0.0, 0.03),
    ]


ROWS = torso_rows()
HEAD = [
    (-0.045, 0.040, 0.040, 0.030, 0.0, -0.035),
    (-0.030, 0.078, 0.082, 0.050, 0.10, -0.03),
    (0.000, 0.088, 0.096, 0.060, 0.12, -0.022),
    (0.035, 0.085, 0.098, 0.075, 0.10, -0.012),
    (0.075, 0.082, 0.096, 0.088, 0.06, -0.006),
    (0.110, 0.086, 0.088, 0.096, 0.02, 0.000),
    (0.150, 0.082, 0.076, 0.094, 0.0, 0.006),
    (0.185, 0.064, 0.058, 0.078, 0.0, 0.010),
    (0.210, 0.034, 0.032, 0.044, 0.0, 0.012),
]
HDY, HDZ = -0.05, -0.035     # head thrust forward and low (old, hunched)


def H_rows():
    return K.head_rows(HEAD, L["head"] + HDZ, dy=HDY)


def build(body: Body):
    add = body.add
    TW = K.torso_w(PROPS)
    V, F = torso_loft(ROWS, n=22, p=2.2, cap0=True, cap1=False)
    add(M.Part(V, F, "BH_Skin", name="torso"), weights=TW)
    zc = L["chest"]
    for sx in (1, -1):   # sagging pectorals
        add(K.blob((sx * 0.09, front_y(ROWS, 0.09, zc + 0.1) + 0.035, zc + 0.08), 0.085, "BH_Skin",
                   scale=(1.0, 0.45, 0.75), n=10, rings=6), weights=TW)
    war_paint(body)
    necklaces(body)
    kilt(body)
    for s in ("L", "R"):
        K.leg(body, s, [(0.095, 0.1), (0.084, 0.088), (0.066, 0.07), (0.064, 0.066), (0.066, 0.07), (0.05, 0.053)],
              "BH_Skin", n=12)
        shin_wraps(body, s)
        K.bare_foot(body, s, "BH_Skin", length=0.29, width=0.056, height=0.07, claw_mat="BH_Bone", toes=3,
                    toe_r=0.02)
    for s in ("L", "R"):
        K.arm(body, s, [(0.066, 0.07), (0.056, 0.06), (0.05, 0.052), (0.054, 0.054), (0.056, 0.052),
                        (0.042, 0.04)], "BH_Skin", n=12, deltoid=0.075)
        K.hand(body, s, "BH_Skin", scale=1.22, claws="BH_Bone")
        fa, ha = body.head("forearm." + s), body.head("hand." + s)
        d = normalize(ha - fa)
        V, F = M.tube([fa + (ha - fa) * 0.55, fa + (ha - fa) * 0.98], [(0.062, 0.06), (0.052, 0.05)], n=12,
                      up=(0, -1, 0))
        add(M.Part(V, F, "BH_Leather", name="wristwrap"), "forearm." + s)
        for j, u in enumerate((0.5, 0.56, 0.62)):
            q = fa + (ha - fa) * u
            for k in range(8):
                a = 2 * math.pi * (k + 0.5 * j) / 8
                side = normalize(np.cross(d, (0, 1, 0)))
                fw = np.cross(side, d)
                add(K.blob(q + (side * math.cos(a) + fw * math.sin(a)) * 0.061, 0.01,
                           "BH_Bone" if (k + j) % 2 else "BH_Wood", n=5, rings=3), "forearm." + s)
    wolf_pelt(body)
    head(body)
    antlers(body)
    K.weapon_to_socket(body, "R", totem_staff())


# ================================================================================================= body dressing
def war_paint(body):
    """Blue-white paint: a hand print over the heart and stripes across the belly."""
    add = body.add
    TW = K.torso_w(PROPS)
    zc, zs = L["chest"], L["spine"]
    c = np.array([0.1, 0, zc + 0.02])
    c[1] = front_y(ROWS, 0.1, c[2]) - 0.004
    add(K.blob(c, 0.045, "BH_Cloth_Secondary", scale=(1.0, 0.12, 1.1), n=8, rings=4), weights=TW)
    for k in range(4):
        a = math.radians(-35 + 22 * k)
        t = c + np.array([0.075 * math.sin(a), -0.012, 0.075 * math.cos(a)])
        t[1] = front_y(ROWS, t[0], t[2]) - 0.003
        add(K.rtube([c + (0, -0.004, 0.02), t], (0.012, 0.004), "BH_Cloth_Secondary", n=4, up=(0, -1, 0)), weights=TW)
    for k in range(3):
        z = zs + 0.02 + 0.04 * k
        pts = [(x, front_y(ROWS, x, z) - 0.003, z - 0.02 * abs(x) / 0.12) for x in np.linspace(-0.13, 0.02, 5)]
        add(K.rtube(pts, (0.009, 0.003), "BH_Cloth_Secondary", n=4, up=(0, -1, 0)), weights=TW)


def necklaces(body):
    add = body.add
    zn = L["neck"]
    for j, (rr, drop, n) in enumerate(((0.11, 0.07, 13), (0.13, 0.13, 15), (0.14, 0.2, 17))):
        pts = []
        for a in np.linspace(math.radians(-165), math.radians(-15), n):
            z = zn - 0.02 - drop * math.sin(-a) ** 2
            x = rr * math.cos(a)
            y = min(front_y(ROWS, x, z) - 0.018, 0.02 + rr * 0.9 * math.sin(a))
            pts.append(np.array([x, y, z]))
        add(K.rtube(pts, 0.003, "BH_Leather", n=4), weights=K.torso_w(PROPS))
        for i, p in enumerate(pts[1:-1]):
            if j == 2 and i == (n - 2) // 2:
                # a wolf fang pendant with a small blue crystal
                add(K.cone(p, p + (0, -0.01, -0.07), 0.013, "BH_Bone", n=5), weights=K.torso_w(PROPS))
                add(A.shard(p + (0, -0.012, -0.004), (0, -0.2, -1), 0.04, 0.009, "BH_Emissive", sides=5),
                    weights=K.torso_w(PROPS))
            else:
                mat = ("BH_Bone", "BH_Wood", "BH_Cloth_Primary")[(i + j) % 3]
                add(K.blob(p + (0, -0.004, 0), 0.011 + 0.003 * (i % 2), mat, n=6, rings=4), weights=K.torso_w(PROPS))


def seat(z_top, z_bot, leg=0.75, cw=0.03):
    def wfn(V):
        out = []
        for v in V:
            s = float(smoothstep(z_top, z_bot, v[2])) * leg
            side = float(smoothstep(-cw, cw, v[0]))
            d = {"hips": 1 - s}
            if s * side > 1e-3:
                d["thigh.L"] = s * side
            if s * (1 - side) > 1e-3:
                d["thigh.R"] = s * (1 - side)
            out.append(d)
        return out
    return wfn


def kilt(body):
    """Long hide kilt (8 overlapping panels to mid-shin) with a fur hem strip, wide belt and fetishes."""
    add = body.add
    zh = L["hips"]
    V, F = torso_loft([(zh - 0.045, 0.178, 0.15, 0.13, 0.0), (zh + 0.07, 0.182, 0.155, 0.13, 0.03)], n=22)
    add(M.bevel(M.Part(V, F, "BH_Leather", name="belt"), 0.004, 1), "hips")
    V, F = torso_loft([(zh - 0.16, 0.165, 0.115, 0.12, 0.0), (zh - 0.04, 0.175, 0.13, 0.125, 0.0)], n=22)
    add(M.Part(V, F, "BH_Leather", name="seat"), weights=seat(zh - 0.03, zh - 0.16, 0.6, cw=0.1))
    for k in range(8):
        ang = math.radians(-90 + k * 45)
        ca, sa = math.cos(ang), math.sin(ang)
        ln = 0.52 - 0.05 * (k % 2)

        def fn(u, v, ca=ca, sa=sa, ln=ln, k=k):
            w = 0.15 + 0.03 * v
            tx, ty = -sa, ca
            r0x, r0y = 0.185 + 0.06 * v, 0.15 + 0.06 * v
            end = ln - 0.05 * abs(math.sin(u * 5 + k))
            return (r0x * ca + (u - 0.5) * w * tx, r0y * sa + (u - 0.5) * w * ty, zh + 0.0 - end * v)
        V, F = M.grid(fn, 4, 6)
        fl = M.Part(V, F, "BH_Leather", name="kiltpanel")
        if (np.cross(fl.V[1] - fl.V[0], fl.V[4] - fl.V[0])[:2] @ np.array([ca, sa])) < 0:
            fl.flip()
        # front / back panels hang between the legs: soft L/R blend and less leg follow, so they do not tear apart
        # at the centre line when the legs split (side panels follow their own leg)
        w = seat(zh - 0.02, zh - 0.5, 0.85, cw=0.02) if abs(ca) > 0.5 else seat(zh - 0.02, zh - 0.5, 0.5, cw=0.16)
        add(M.solidify(fl, 0.01, offset=1.0), weights=w)
        # fur hem tuft on every other panel
        if k % 2 == 0:
            q = np.array(fn(0.5, 0.92))
            add(K.blob(q + np.array([ca, sa, 0]) * 0.01, 0.04, "BH_Fur", scale=(1.3, 0.5, 0.6), n=8, rings=4,
                       rot=Rz(math.degrees(ang) + 90)), weights=w)
    # fetishes on the belt: small skulls, bone bundles, feathers
    w = seat(zh, zh - 0.3, 0.45)
    for ang, kind in ((-120, "skull"), (-60, "bundle"), (-150, "feather"), (-30, "feather"), (200, "skull")):
        a = math.radians(ang)
        p = np.array([0.19 * math.cos(a), 0.16 * math.sin(a), zh - 0.03])
        out = normalize(np.array([math.cos(a), math.sin(a), 0.0]))
        add(K.rtube([p, p + out * 0.01 + (0, 0, -0.08)], 0.003, "BH_Leather", n=4), weights=w)
        b = p + out * 0.02 + np.array([0, 0, -0.1])
        if kind == "skull":
            for prt in A.skull_charm(b, 0.035, "BH_Bone", "BH_Shadow", face=out, n=8):
                add(prt, weights=w)
        elif kind == "bundle":
            for dx in (-0.012, 0.0, 0.012):
                add(K.rtube([b + (dx, 0, 0.03), b + (dx * 1.5, 0, -0.07)], 0.006, "BH_Bone", n=5), weights=w)
            add(K.rtube([b + (-0.02, 0, 0.0), b + (0.02, 0, 0.0)], 0.009, "BH_Cloth_Primary", n=5), weights=w)
        else:
            add(A.feather(b + (0, 0, 0.03), (0.1, 0, -1), 0.14, 0.04, "BH_Cloth_Primary", side=(-out[1], out[0], 0)),
                weights=w)


def shin_wraps(body, s):
    sh = "shin." + s
    k, a = body.head(sh), body.tail(sh)
    V, F = M.tube([a + (0, 0, 0.02), a + (k - a) * 0.5, a + (k - a) * 0.85], [(0.058, 0.062), (0.072, 0.076),
                                                                              (0.07, 0.074)], n=12, up=(0, -1, 0))
    body.add(M.Part(V, F, "BH_Cloth_Primary", name="wrap"), sh)
    for u in (0.2, 0.42, 0.64):
        q = a + (k - a) * u
        V, F = M.tube([q + (0, 0, -0.012), q + (0, -0.01, 0.014)], [(0.076, 0.08)] * 2, n=12, up=(0, -1, 0))
        body.add(M.Part(V, F, "BH_Leather", name="binding"), sh)


def wolf_pelt(body):
    """Grey wolf pelt: shaggy mantle round the shoulders (open at the chest), the wolf's head on the left shoulder,
    forelegs tied across the chest, the pelt hanging down the back with the tail."""
    add = body.add
    TW = K.torso_w(PROPS)
    zn, zc, zs = L["neck"], L["chest"], L["spine"]
    rng = np.random.default_rng(21)
    rings = []
    spec = ((zn + 0.02, 0.018), (zn - 0.02, 0.03), (zn - 0.07, 0.05), (zn - 0.13, 0.07), (zc + 0.06, 0.085))
    for k, (z, g) in enumerate(spec):
        fr = np.linspace(0.1, 0.9, 21)
        r = BK.ring_frac(ROWS, min(z, zn + 0.0), g, fr, p=2.2)
        r[:, 2] = z
        if k == len(spec) - 1:
            r[:, 2] -= np.array([0.05 * abs(math.sin(i * 1.7)) + 0.02 * (i % 2) for i in range(len(fr))])
        rings.append(r)
    V, F = M.loft(rings[::-1], cap0=False, cap1=False, closed=False)
    mant = M.Part(V, F, "BH_Fur", name="pelt")
    K.jitter(mant, 0.004, seed=3)
    add(M.solidify(mant, 0.016, offset=1.0), weights=TW)
    # shaggy tufts along the lower edge and over the shoulders
    for i, q in enumerate(rings[-1][::2]):
        out = normalize(np.array([q[0], q[1] - 0.02, 0.0]))
        add(K.cone(q + out * 0.005 + (0, 0, 0.02), q + out * 0.03 + (0, 0, -0.07 - 0.03 * rng.random()), 0.022,
                   "BH_Fur", n=5), weights=TW)
    # pelt down the back (to the hips) + tail
    def fn(u, v):
        zt, zb = zc + 0.1, zs - 0.08 + 0.05 * abs(math.sin(u * 9.0))
        z = zt + (zb - zt) * v
        hw = 0.2 - 0.07 * v
        x = (u - 0.5) * 2 * hw
        return (x, back_y(ROWS, x * 0.92, max(z, L["hips"])) + 0.03, z)
    V, F = M.grid(fn, 7, 6)
    back = M.Part(V, F, "BH_Fur", name="pelt_back").flip()
    K.jitter(back, 0.003, seed=5)
    add(M.solidify(back, 0.014, offset=1.0), weights=TW)
    tb = np.array(fn(0.5, 1.0)) + np.array([0, 0.01, 0.02])
    add(K.rtube([tb, tb + (0.01, 0.05, -0.12), tb + (0.03, 0.07, -0.28)], [0.04, 0.045, 0.012], "BH_Fur", n=8),
        weights=lambda V: [{"hips": 1.0}] * len(V))
    # forelegs tied across the chest
    for sx in (1, -1):
        st = rings[0][0 if sx < 0 else -1]
        pts = [st + (0, -0.01, -0.02), (sx * 0.08, front_y(ROWS, 0.08, zn - 0.1) - 0.03, zn - 0.1),
               (sx * 0.02, front_y(ROWS, 0.0, zn - 0.13) - 0.035, zn - 0.13)]
        add(K.rtube(pts, [0.03, 0.026, 0.02], "BH_Fur", n=7), weights=TW)
        add(K.cone(np.array(pts[-1]), np.array(pts[-1]) + (-sx * 0.03, -0.01, -0.03), 0.018, "BH_Fur", n=5),
            weights=TW)
    add(K.blob((0, front_y(ROWS, 0.0, zn - 0.13) - 0.04, zn - 0.13), 0.022, "BH_Leather", n=6, rings=4), "chest")
    wolf_head(body)


def wolf_head(body):
    """The pelt's wolf head riding on the left shoulder, snout forward, glass-blue bead eyes."""
    sh = body.head("upper_arm.L")
    c = sh + np.array([-0.03, 0.0, 0.1])
    parts = []
    parts.append(A.ball(c, 0.08, "BH_Fur", n=10, rings=6, scale=(0.95, 1.05, 0.8)))
    parts.append(A.taper([c + (0, -0.05, -0.01), c + (0, -0.11, -0.025), c + (0, -0.17, -0.04)], 0.05, 0.026, "BH_Fur",
                         n=8, up=(0, 0, 1)))
    parts.append(A.ball(c + (0, -0.175, -0.035), 0.018, "BH_Shadow", n=6, rings=4))
    for sx in (1, -1):
        parts.append(K.cone(c + (sx * 0.045, 0.01, 0.045), c + (sx * 0.06, 0.03, 0.12), 0.03, "BH_Fur", n=5))
        parts.append(A.ball(c + (sx * 0.035, -0.065, 0.02), 0.012, "BH_Shadow", n=6, rings=4))
        for j in range(2):   # upper fangs
            q = c + np.array([sx * 0.018, -0.13 - 0.02 * j, -0.055])
            parts.append(K.cone(q + (0, 0, 0.01), q + (0, 0, -0.03), 0.006, "BH_Bone", n=4))
    parts.append(A.taper([c + (0, -0.03, -0.055), c + (0, -0.1, -0.07), c + (0, -0.15, -0.07)], 0.035, 0.02, "BH_Fur",
                         n=7, up=(0, 0, 1)))    # lower jaw
    for p in parts:
        body.add(p, weights=lambda V: [{"shoulder.L": 0.45, "chest": 0.25, "upper_arm.L": 0.3}] * len(V))


# ================================================================================================= head
def head(body):
    add = body.add
    z0 = L["head"] + HDZ
    H = H_rows()
    zn = L["neck"]
    V, F = M.tube([(0, 0.03, zn - 0.03), (0, 0.0, zn + 0.04), (0, -0.03 + HDY * 0.6, z0 + 0.03)],
                  [(0.08, 0.076), (0.074, 0.07), (0.068, 0.066)], n=12, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="neck"),
        weights=K.zspec_w([(zn - 0.0, "chest"), (zn + 0.03, "neck"), (z0 - 0.01, "neck"), (z0 + 0.03, "head")]))
    V, F = torso_loft(H, n=22, p=2.2, cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Skin", name="head"), "head")
    zb = z0 + 0.1
    yb = K.front_of(H, 0, zb)
    add(K.rtube([(-0.08, yb + 0.03, zb - 0.012), (-0.035, yb - 0.004, zb + 0.002), (0, yb + 0.002, zb - 0.008),
                 (0.035, yb - 0.004, zb + 0.002), (0.08, yb + 0.03, zb - 0.012)], 0.02, "BH_Skin", n=6,
                up=(0, -1, 0)), "head")
    # bushy grey eyebrows
    for sx in (1, -1):
        add(K.rtube([(sx * 0.015, yb - 0.012, zb + 0.012), (sx * 0.05, yb - 0.004, zb + 0.016),
                     (sx * 0.085, yb + 0.03, zb + 0.004)], [0.009, 0.011, 0.004], "BH_Hair", n=5), "head")
    for sx in (1, -1):
        ye = K.front_of(H, 0.035, z0 + 0.075, p=2.2)
        add(K.blob((sx * 0.036, ye - 0.004, z0 + 0.075), 0.017, "BH_Shadow", scale=(1.2, 0.5, 0.6), n=8, rings=4),
            "head")
        add(K.blob((sx * 0.037, ye - 0.01, z0 + 0.076), 0.0075, "BH_Emissive", scale=(1.3, 0.6, 0.7), n=6, rings=4),
            "head")
        # paint: three blue-white stripes down each cheek from under the eye
        for j in range(3):
            x = sx * (0.03 + 0.017 * j)
            pts = [(x, K.front_of(H, x, z, p=2.2) - 0.002, z) for z in (z0 + 0.06, z0 + 0.035, z0 + 0.01)]
            add(K.rtube(pts, (0.005, 0.002), "BH_Cloth_Secondary", n=4, up=(0, -1, 0)), "head")
    yn = K.front_of(H, 0, z0 + 0.05, p=2.2)
    add(K.rtube([(0, yn + 0.004, z0 + 0.085), (0, yn - 0.024, z0 + 0.05), (0, yn - 0.02, z0 + 0.028)],
                [(0.016, 0.012), (0.032, 0.02), (0.028, 0.014)], "BH_Skin", n=8, up=(0, 0, 1)), "head")
    zm = z0 + 0.005
    ym = K.front_of(H, 0, zm, p=2.2)
    add(K.rtube([(x, K.front_of(H, x, zm, p=2.2) - 0.004, zm - 0.004 + 3 * x * x) for x in np.linspace(-0.06, 0.06, 7)],
                (0.007, 0.004), "BH_Shadow", n=5), "head")
    for sx, ln in ((1, 0.06), (-1, 0.03)):     # worn tusks, the right one broken
        b = np.array([sx * 0.04, K.front_of(H, 0.04, zm - 0.01, p=2.2) + 0.008, zm - 0.012])
        add(K.rtube([b, b + (sx * 0.005, -0.012, ln * 0.5), b + (sx * 0.012, -0.006, ln)],
                    [0.013, 0.011, 0.004 if ln > 0.05 else 0.009], "BH_Bone", n=7), "head")
    # long ears drooping back, with bone rings
    for sx in (1, -1):
        rx, cy = K.side_of(H, z0 + 0.07)
        root = (sx * (rx - 0.01), cy + 0.02, z0 + 0.07)
        add(K.ear(root, 0.13, 0.065, "BH_Skin", out=(sx * 0.8, 0.8, -0.1), up=(0, 0, 1), droop=0.03, thick=0.014),
            "head")
        for j in range(2):
            add(K.rtube([np.array(root) + (sx * (0.03 + 0.025 * j), 0.03 + 0.02 * j, -0.015) +
                         0.012 * np.array([0, math.cos(a), math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 9)],
                        0.0035, "BH_Bone", n=4, cap=False), "head")
    # braided beard: two braids from the chin to the chest, bone beads
    chin = np.array([0, K.front_of(H, 0, z0 - 0.03, p=2.2) + 0.01, z0 - 0.035])
    add(K.blob(chin + (0, 0.0, 0.0), 0.05, "BH_Hair", scale=(1.2, 0.7, 0.8), n=8, rings=5), "head")
    for sx in (1, -1):
        pts = [chin + (sx * 0.025, -0.01, -0.01), chin + (sx * 0.03, -0.03, -0.08), chin + (sx * 0.025, -0.045, -0.16),
               chin + (sx * 0.02, -0.05, -0.24)]
        add(K.rtube(pts, [0.02, 0.017, 0.014, 0.008], "BH_Hair", n=6), weights=beard_w())
        for u in (0.45, 0.8):
            q = np.array(pts[int(u * 3)]) * (1 - (u * 3 % 1)) + np.array(pts[min(int(u * 3) + 1, 3)]) * (u * 3 % 1)
            add(K.rtube([q + (0, 0, 0.012), q - (0, 0, 0.012)], 0.02, "BH_Bone", n=7), weights=beard_w())
    # long grey hair from under the cap down the back
    for k, x in enumerate(np.linspace(-0.07, 0.07, 5)):
        t = np.array([x, 0.06 + HDY, z0 + 0.15])
        pts = [t, t + (x * 0.2, 0.05, -0.08), t + (x * 0.4, 0.08, -0.2), t + (x * 0.5, 0.1, -0.32 - 0.02 * (k % 2))]
        add(K.rtube(pts, [0.026, 0.024, 0.018, 0.006], "BH_Hair", n=6), weights=hair_w())


def beard_w():
    z0 = L["head"] + HDZ
    return K.zspec_w([(z0 - 0.2, "chest"), (z0 - 0.12, "neck"), (z0 - 0.06, "head")])


def hair_w():
    z0 = L["head"] + HDZ
    return K.zspec_w([(L["neck"] - 0.02, "chest"), (L["neck"] + 0.04, "neck"), (z0 + 0.06, "head")])


def antlers(body):
    """Leather cap with a fur band, two big branching antlers sweeping up and out, bone fetishes and feathers."""
    add = body.add
    z0 = L["head"] + HDZ
    H = H_rows()
    zc = z0 + 0.16
    r = interp_rows(H, zc)
    V, F = dome((0, r[5] + 0.004, zc - 0.025), (0, 0.1, 1), 0.098, a_max=78, n=16, rings=5,
                scale=(0.98, 1.08, 0.75))
    add(M.solidify(M.Part(V, F, "BH_Leather", name="cap"), 0.008, offset=1.0), "head")
    ring = [(0.1 * math.cos(a), r[5] + 0.004 + 0.108 * math.sin(a), zc - 0.022) for a in np.linspace(0, 2 * math.pi, 17)]
    add(K.rtube(ring, 0.018, "BH_Fur", n=6, up=(0, 0, 1), cap=False), "head")
    for sx in (1, -1):
        base = np.array([sx * 0.07, r[5] + 0.01, zc + 0.02])
        beam = [base]
        for t in np.linspace(0.15, 1.0, 6):
            beam.append(base + np.array([sx * (0.26 * t + 0.12 * t * t), 0.1 * t * t, 0.33 * t - 0.08 * t ** 3]))
        add(A.taper(beam, 0.024, 0.008, "BH_Horn", n=7), "head")
        add(K.blob(base + (0, 0, -0.005), 0.03, "BH_Horn", n=7, rings=4, scale=(1, 1, 0.6)), "head")
        # tines
        for i, (bi, d, ln) in enumerate(((2, (0.2 * sx, -0.7, 0.7), 0.1), (3, (0.1 * sx, -0.3, 1.0), 0.13),
                                         (5, (0.6 * sx, 0.0, 0.8), 0.1), (4, (0.3 * sx, 0.6, 0.8), 0.09))):
            b = beam[bi]
            dd = normalize(np.array(d))
            add(A.taper([b, b + dd * ln * 0.55 + (0, 0, 0.01), b + dd * ln], 0.012, 0.004, "BH_Horn", n=5), "head")
        # fetish hanging from the lower beam: a bone + feather on a cord
        hb = beam[2]
        add(K.rtube([hb, hb + (0, -0.005, -0.09)], 0.003, "BH_Leather", n=4), "head")
        add(K.rtube([hb + (-0.01, -0.005, -0.09), hb + (0.01, -0.005, -0.15)], 0.007, "BH_Bone", n=5), "head")
        add(A.feather(hb + (0.0, 0.01, -0.03), (sx * 0.2, 0.2, -1), 0.12, 0.034,
                      "BH_Cloth_Primary" if sx > 0 else "BH_Hair", side=(0, 1, 0)), "head")
    # a small bird skull on the brow of the cap
    for prt in A.skull_charm((0, K.front_of(H, 0, zc - 0.02) - 0.018, zc - 0.005), 0.03, "BH_Bone", "BH_Shadow",
                             face=(0, -1, 0.3), n=8, jaw=False):
        add(prt, "head")


# ================================================================================================= staff
def totem_staff():
    """Gnarled totem staff (weapon space, grip at origin, +Z up): twisted shaft, carved face knob, root claws
    gripping a blue-white lightning crystal with jagged arcs, feathers and bone charms."""
    parts = []
    pts, prof = [], []
    for i in range(16):
        u = i / 15
        z = -1.12 + 1.72 * u
        pts.append((0.014 * math.sin(u * 11.0) + 0.01 * math.sin(u * 4.3), 0.012 * math.cos(u * 8.0), z))
        r = 0.022 + 0.004 * math.sin(u * 29) + 0.01 * max(0.0, u - 0.8) / 0.2
        prof.append((r, r * 0.9))
    V, F = M.tube(pts, prof, n=8, up=(0, -1, 0), twist=[u * 1.6 for u in np.linspace(0, 1, 16)])
    parts.append(M.Part(V, F, "BH_Wood", name="shaft"))
    for u in (0.2, 0.45, 0.7):     # knots
        i = int(u * 15)
        parts.append(A.ball(pts[i], 0.028, "BH_Wood", n=6, rings=4, scale=(1.0, 0.8, 1.4)))
    top = np.array(pts[-1])
    # carved face knob just under the head (faces the staff's -Y flat)
    fc = top + np.array([0, 0, -0.1])
    parts.append(A.ball(fc, 0.045, "BH_Wood", n=8, rings=5, scale=(1.0, 0.9, 1.4)))
    for sx in (1, -1):
        parts.append(A.ball(fc + (sx * 0.018, -0.038, 0.02), 0.011, "BH_Shadow", n=5, rings=3))
    parts.append(A.ball(fc + (0, -0.038, -0.025), 0.013, "BH_Shadow", n=5, rings=3, scale=(1.4, 0.6, 0.7)))
    parts.append(A.tube([fc + (0, -0.04, 0.03), fc + (0, -0.05, -0.005)], [0.008, 0.012], "BH_Wood", n=5))
    # root claws (4) curling up round the crystal
    cz = top + np.array([0, 0, 0.14])
    for k in range(4):
        a = math.radians(90 * k + 20)
        d = np.array([math.cos(a), math.sin(a), 0.0])
        claw = [top + d * 0.01, top + d * 0.05 + (0, 0, 0.05), top + d * 0.07 + (0, 0, 0.13),
                top + d * 0.045 + (0, 0, 0.21), top + d * 0.015 + (0, 0, 0.24)]
        parts.append(A.taper(claw, 0.017, 0.004, "BH_Wood", n=6))
    # the lightning crystal: a tall central shard + small shards
    parts.append(A.shard(cz + (0, 0, -0.1), (0, 0, 1), 0.3, 0.05, "BH_Emissive", sides=6, twist=15))
    for k in range(3):
        a = math.radians(120 * k + 50)
        d = normalize(np.array([math.cos(a) * 0.5, math.sin(a) * 0.5, 1.0]))
        parts.append(A.shard(cz + (0, 0, -0.06), d, 0.14, 0.024, "BH_Emissive", sides=5, twist=30 * k))
    # jagged arcs crackling from the crystal to the claw tips
    rng = np.random.default_rng(12)
    for k in range(4):
        a = math.radians(90 * k + 65)
        start = cz + np.array([0.02 * math.cos(a), 0.02 * math.sin(a), 0.02 + 0.03 * k])
        end = top + np.array([0.075 * math.cos(a), 0.075 * math.sin(a), 0.1 + 0.04 * (k % 2)])
        zz = [start]
        for t in (0.33, 0.66):
            q = start + (end - start) * t
            zz.append(q + (rng.random() - 0.5) * 0.04 + np.array([0, 0, 0.02 * (1 if k % 2 else -1)]))
        zz.append(end)
        parts.append(A.tube(zz, 0.0045, "BH_Emissive", n=4))
    top_arc = [cz + (0, 0, 0.17), cz + (0.03, 0.01, 0.21), cz + (-0.01, -0.01, 0.24), cz + (0.02, 0.0, 0.29)]
    parts.append(A.taper(top_arc, 0.006, 0.002, "BH_Emissive", n=4))
    # feathers + bone charms tied under the claws
    for k, (a, mat) in enumerate(((200, "BH_Cloth_Primary"), (320, "BH_Hair"), (80, "BH_Cloth_Primary"))):
        r = math.radians(a)
        b = top + np.array([0.035 * math.cos(r), 0.035 * math.sin(r), -0.02])
        parts.append(A.tube([b, b + (0, 0, -0.07)], 0.003, "BH_Leather", n=4))
        parts.append(A.feather(b + (0, 0, -0.06), (0.25 * math.cos(r), 0.25 * math.sin(r), -1), 0.16, 0.04, mat,
                               side=(-math.sin(r), math.cos(r), 0)))
    parts.append(A.tube([top + (0.03, 0.0, -0.03), top + (0.035, 0.0, -0.13)], 0.003, "BH_Leather", n=4))
    parts.append(A.tube([top + (0.025, 0.0, -0.13), top + (0.045, 0.0, -0.19)], 0.008, "BH_Bone", n=5))
    # leather wraps at the grip and a bound butt
    V, F = M.lathe([(0, -0.12), (0.027, -0.12), (0.028, 0.12), (0, 0.12)], 8)
    parts.append(M.Part(V, F, "BH_Leather", name="grip"))
    V, F = M.lathe([(0, -1.16), (0.022, -1.14), (0.028, -1.08), (0.0, -1.05)], 8)
    parts.append(M.Part(V, F, "BH_Bone", name="butt"))
    return parts
