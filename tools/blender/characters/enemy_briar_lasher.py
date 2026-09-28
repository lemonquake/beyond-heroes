"""Briar Lasher (bh-013, Builder B1 "warriors"; walking thorn plant, thorn hide + vine-lash pull): a hunched ~2.0 m
figure of twisted dark bark wrapped in thorny green vines. Its head is a hollow bark knot (a dark hole ringed by a
thick bark lip) with two ember-red eyes glowing inside, under a CROWN of long crimson thorns; big tufts of crimson
thorns burst from both shoulders, a crimson-thorned vine ridge runs down the spine, crimson thorns bristle on the
vines round the limbs. Right hand: a long rigid curling thorned vine whip (weapon.R). Left forearm: no hand - it
swells into a heavy knotted bark club studded with crimson thorns (rigid on hand.L).

Modelled at true size on the shared humanoid skeleton (greenskin kit + kit_warren roots).
Clips: sword_1, sword_2 (whip lashes), spear_heavy (lash-pull thrust), cast_quick, cast_area, boss_roar."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft, interp_rows, M_align_z  # noqa: E402
from bh_math import normalize, R_axis  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as K  # noqa: E402
import kit_warren as W  # noqa: E402
import kit_a_common as A  # noqa: E402
from enemy_bandit_cutthroat import ring_frac  # noqa: E402

S = 1.08
PROPS = proportions(
    S,
    pelvis_h=1.0, hip_h=0.96, knee_h=0.54, ankle_h=0.085, hip_x=0.11,
    hips_len=0.1, spine_len=0.21, chest_len=0.27, neck_len=0.08, head_len=0.21,
    clav_x0=0.045, clav_drop=0.05, shoulder_x=0.225, upper_len=0.31, fore_len=0.3, hand_len=0.11, grip_x=0.08,
)
L = K.levels(PROPS)
PREVIEW_HEIGHT = 2.45

PALETTE = "briar_lasher"
PALETTE_COLORS = {
    "BH_Wood": ((0.085, 0.055, 0.035), 0.0, 0.85, None, 0.0, 1.0),           # dark twisted bark
    "BH_Leather": ((0.2, 0.13, 0.07), 0.0, 0.8, None, 0.0, 1.0),             # lighter bark ridges / knot lip
    "BH_Fur": ((0.07, 0.13, 0.035), 0.0, 0.9, None, 0.0, 1.0),               # thorny green vines
    "BH_Cloth_Primary": ((0.62, 0.04, 0.07), 0.0, 0.6, None, 0.0, 1.0),      # crimson thorns
    "BH_Flesh": ((0.3, 0.03, 0.05), 0.0, 0.7, None, 0.0, 1.0),               # dark red dried leaves
    "BH_Shadow": ((0.012, 0.008, 0.006), 0.0, 0.8, None, 0.0, 1.0),          # the hollow
    "BH_Emissive": ((1.0, 0.32, 0.08), 0.0, 0.4, (1.0, 0.28, 0.05), 6.0, 1.0),  # ember eyes
}
CLIPS = ["sword_1", "sword_2", "spear_heavy", "cast_quick", "cast_area", "boss_roar"]
THORN = "BH_Cloth_Primary"


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def torso_rows():
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    return [
        (zh - 0.08, 0.14, 0.1, 0.1, 0.0, 0.0),
        (zh + 0.04, 0.15, 0.105, 0.105, 0.0, 0.0),
        (zs + 0.06, 0.13, 0.1, 0.1, 0.04, 0.0),
        (zc + 0.05, 0.17, 0.12, 0.13, 0.06, 0.01),
        (zc + 0.17, 0.21, 0.13, 0.15, 0.05, 0.02),
        (zn - 0.05, 0.215, 0.12, 0.15, 0.02, 0.03),
        (zn - 0.005, 0.15, 0.09, 0.12, 0.0, 0.035),
        (zn + 0.04, 0.07, 0.06, 0.07, 0.0, 0.03),
    ]


ROWS = torso_rows()


def thorn(base, direction, length, r, mat=THORN, n=4):
    d = normalize(direction)
    return K.cone(np.asarray(base, float) - d * r * 0.8, np.asarray(base, float) + d * length, r, mat, n=n)


def thorny_vine(pts, r0, r1, seed, thorn_every=2, thorn_len=0.05, thorn_r=0.011, mat="BH_Fur", n=5, amp=0.006):
    """A green vine along pts with crimson thorns sticking out along it."""
    q = W.gnarl(pts, amp, seed, sub=2)
    parts = [W.root(q, r0, r1, mat, n=n, seed=seed, knot=0.2)]
    rng = np.random.default_rng(seed + 7)
    for i in range(1, len(q) - 1):
        if i % thorn_every:
            continue
        d = normalize(np.asarray(q[i + 1]) - np.asarray(q[i - 1]))
        side = normalize(np.cross(d, rng.normal(size=3)))
        dirn = normalize(side + d * 0.35)
        rr = r0 + (r1 - r0) * i / (len(q) - 1)
        parts.append(thorn(np.asarray(q[i]) + side * rr * 0.6, dirn, thorn_len * (0.7 + 0.6 * rng.random()), thorn_r))
    return parts


# ================================================================================================= build
def build(body: Body):
    add = body.add
    TW = K.torso_w(PROPS)
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    V, F = torso_loft(ROWS, n=18, p=2.2, cap0=True, cap1=False)
    tor = M.Part(V, F, "BH_Wood", name="torso")
    # twist the bark: rotate each ring a little with height + knobbly noise
    c0 = tor.V.copy()
    ang = (c0[:, 2] - zh) * 1.6
    tor.V[:, 0] = c0[:, 0] * np.cos(ang) - (c0[:, 1]) * np.sin(ang) * 0.35
    add(K.jitter(tor, 0.006, seed=2), weights=TW)
    # twisted bark ridges spiralling up the torso (lighter), thorny vines wrapping across them
    for k in range(4):
        pts = []
        for i in range(17):
            t = i / 16
            z = zh - 0.05 + (zn - 0.02 - (zh - 0.05)) * t
            f = (k / 4 + 0.55 * t) % 1.0
            pts.append(ring_frac(ROWS, z, 0.004, [f], p=2.2)[0])
        add(W.root(pts, 0.022, 0.016, "BH_Leather", n=5, seed=k, knot=0.25), weights=TW)
    for k in range(3):
        pts = []
        for i in range(17):
            t = i / 16
            z = zh - 0.04 + (zn - 0.06 - (zh - 0.04)) * t
            f = (k / 3 - 0.9 * t) % 1.0
            pts.append(ring_frac(ROWS, z, 0.016, [f], p=2.2)[0])
        for prt in thorny_vine(pts, 0.017, 0.012, seed=10 + k, thorn_len=0.06, thorn_r=0.012):
            add(prt, weights=TW)
    # crimson-thorned ridge down the spine
    for i, z in enumerate(np.linspace(zn - 0.02, zs + 0.02, 7)):
        q = ring_frac(ROWS, z, 0.0, [0.5], p=2.2)[0]
        ln = 0.16 - 0.012 * i
        add(thorn(q, (0.0, 1.0, 0.55), ln, 0.028, n=5), weights=TW)
        for sx in (1, -1):
            q2 = ring_frac(ROWS, z - 0.03, 0.0, [0.5 - 0.06 * sx], p=2.2)[0]
            add(thorn(q2, (sx * 0.6, 1.0, 0.4), ln * 0.6, 0.018), weights=TW)
    # thorn hide: long crimson thorns growing straight out of the bark all over the chest, belly and back
    rng = np.random.default_rng(31)
    for i in range(22):
        f = (i / 22 + 0.03 * rng.random()) % 1.0
        z = zs - 0.02 + (zn - 0.08 - zs) * ((i * 0.618) % 1.0)
        q = ring_frac(ROWS, z, -0.004, [f], p=2.2)[0]
        a = 2 * math.pi * f - math.pi / 2
        out = np.array([math.cos(a), math.sin(a), 0.35 + 0.3 * rng.random()])
        add(thorn(q, out, 0.07 + 0.05 * rng.random(), 0.016), weights=TW)
    # a few dried red leaves stuck on the vines
    rng = np.random.default_rng(4)
    for i in range(6):
        f = rng.random()
        z = zs + 0.35 * rng.random()
        q = ring_frac(ROWS, z, 0.02, [f], p=2.2)[0]
        a = 2 * math.pi * f - math.pi / 2
        add(A.feather(q, (math.cos(a), math.sin(a), -0.5), 0.09, 0.05, "BH_Flesh", side=(0, 0, 1)), weights=TW)

    root_hips(body)
    head(body)
    for s in ("L", "R"):
        shoulder_thorns(body, s)

    # ---- legs: bark, vine wraps, root feet
    for s in ("L", "R"):
        sx = 1 if s == "L" else -1
        K.leg(body, s, [(0.1, 0.104), (0.086, 0.09), (0.068, 0.07), (0.07, 0.072), (0.074, 0.076),
                        (0.052, 0.054)], "BH_Wood", n=10)
        th, sh = "thigh." + s, "shin." + s
        hp, kn, an = body.head(th), body.head(sh), body.tail(sh)
        pts = []
        for i in range(15):
            t = i / 14
            c = hp + (kn - hp) * (t * 2) if t <= 0.5 else kn + (an - kn) * ((t - 0.5) * 2)
            d = normalize(kn - hp if t <= 0.5 else an - kn)
            side = normalize(np.cross(d, (0, 1, 0)))
            fw = np.cross(side, d)
            a = 2 * math.pi * 2.0 * t * sx
            r = 0.088 - 0.024 * t
            pts.append(c + (side * math.cos(a) + fw * math.sin(a)) * r)
        for prt in thorny_vine(pts, 0.013, 0.009, seed=30 + (sx > 0), thorn_len=0.05, thorn_r=0.01, amp=0.0):
            add(prt, weights=body.seg_weights([th, sh], power=10))
        K.bare_foot(body, s, "BH_Wood", length=0.3, width=0.06, height=0.07, toes=3, toe_r=0.02, claw_mat="BH_Leather")
        # root spurs off the heel / ankle
        add(W.root([an + (sx * 0.03, 0.04, -0.03), an + (sx * 0.07, 0.1, -0.07), an + (sx * 0.08, 0.15, -0.08)],
                   0.02, 0.004, "BH_Wood", n=5, seed=40 + (sx > 0)), "foot." + s)

    # ---- arms: bark, vine wraps; right hand grips the whip; left forearm swells into the thorn club
    for s in ("L", "R"):
        sx = 1 if s == "L" else -1
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        K.arm(body, s, [(0.078, 0.08), (0.066, 0.068), (0.056, 0.058), (0.06, 0.06), (0.062, 0.062) if s == "R"
                        else (0.075, 0.075), (0.046, 0.046) if s == "R" else (0.078, 0.078)], "BH_Wood", n=10,
              deltoid=0.08)
        sh_, el, wr = body.head(ua), body.head(fa), body.head(ha)
        pts = []
        for i in range(15):
            t = i / 14
            c = sh_ + (el - sh_) * (t * 2) if t <= 0.5 else el + (wr - el) * ((t - 0.5) * 2)
            d = normalize(el - sh_ if t <= 0.5 else wr - el)
            side = normalize(np.cross(d, (0, 1, 0)))
            fw = np.cross(side, d)
            a = 2 * math.pi * 2.2 * t
            r = 0.07 - 0.014 * t
            pts.append(c + (side * math.cos(a) + fw * math.sin(a)) * r)
        for prt in thorny_vine(pts, 0.012, 0.009, seed=50 + (sx > 0), thorn_len=0.05, thorn_r=0.01, amp=0.0):
            add(prt, weights=body.seg_weights([ua, fa], power=10))
    K.hand(body, "R", "BH_Wood", scale=1.1)
    for prt in W.root_fingers(body, "R", "BH_Wood", count=4, length=0.06, r=0.008, curl=0.6, seed=4):
        add(prt, "hand.R")
    thorn_club(body)
    K.weapon_to_socket(body, "R", vine_whip())


def root_hips(body):
    """Knotted root mass round the hips (split front/back so the legs move) + short hanging roots."""
    zh = L["hips"]
    W.split_skirt(body, "BH_Wood", zh + 0.04, zh - 0.26, (0.15, 0.11, 0.11), 0.05, ragged=0.07, folds=0.014, nz=5,
                  nu=6, thick=0.012, max_leg=0.8, center_w=0.05)
    w = body.skirt_weights(zh + 0.04, zh - 0.4, max_leg=0.8, center_w=0.05)
    rng = np.random.default_rng(12)
    for i in range(12):
        f = (i + 0.3 * rng.random()) / 12
        top = W.ellipse_ring(zh - 0.02, 0.16, 0.12, 0.12, [f])[0]
        out = normalize(np.array([top[0], top[1], 0.0]))
        ln = 0.28 + 0.12 * rng.random()
        pts = [top, top + out * 0.04 + (0, 0, -ln * 0.5), top + out * 0.07 + (0, 0, -ln)]
        if i % 2:
            for prt in thorny_vine(pts, 0.012, 0.004, seed=60 + i, thorn_every=2, thorn_len=0.04, thorn_r=0.008,
                                   amp=0.008):
                body.add(prt, weights=w)
        else:
            body.add(W.root(pts, 0.02, 0.005, "BH_Wood", n=5, seed=60 + i, knot=0.25, amp=0.01), weights=w)


def head(body):
    """Bark head with a hollow knot face (dark hole in a thick bark lip, ember eyes inside) under a crown of long
    crimson thorns."""
    add = body.add
    z0 = L["head"]
    zn = L["neck"]
    HW = K.zspec_w([(zn - 0.01, "chest"), (zn + 0.03, "neck"), (z0, "neck"), (z0 + 0.03, "head")])
    V, F = M.tube([(0, 0.035, zn - 0.03), (0, 0.02, z0), (0, 0.01, z0 + 0.05)],
                  [(0.07, 0.065), (0.06, 0.058), (0.07, 0.066)], n=10, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Wood", name="neck"), weights=HW)
    H = [(-0.03, 0.05, 0.05, 0.05, 0.0, 0.0), (0.02, 0.1, 0.1, 0.09, 0.02, -0.005),
         (0.08, 0.108, 0.11, 0.1, 0.02, 0.0), (0.14, 0.1, 0.1, 0.105, 0.0, 0.005),
         (0.2, 0.08, 0.075, 0.09, 0.0, 0.01), (0.245, 0.035, 0.03, 0.04, 0.0, 0.012)]
    rows = K.head_rows(H, z0)
    V, F = torso_loft(rows, n=16, p=2.1, cap0=True, cap1=True)
    add(K.jitter(M.Part(V, F, "BH_Wood", name="skull"), 0.004, seed=3), "head")
    # the hollow: a dark recessed oval, framed by a thick lighter bark lip (torus), eyes inside
    zc = z0 + 0.085
    yf = K.front_of(rows, 0.0, zc)
    ax, az = 0.062, 0.078
    V, F = M.sphere(1.0, 14, 7, scale=(ax, 0.035, az))
    add(M.Part(V + np.array([0, yf + 0.012, zc]), F, "BH_Shadow", name="hollow"), "head")
    lip = []
    for a in np.linspace(0, 2 * math.pi, 17):
        x, z = (ax + 0.012) * math.cos(a), zc + (az + 0.012) * math.sin(a)
        lip.append((x, K.front_of(rows, abs(x) * 0.95, z) - 0.006 + 0.004 * math.sin(3 * a), z))
    V, F = M.tube(lip, [(0.022, 0.018)] * len(lip), n=6, up=(0, -1, 0), cap0=False, cap1=False)
    add(K.jitter(M.Part(V, F, "BH_Leather", name="knotlip"), 0.003, seed=5), "head")
    for sx in (1, -1):
        add(K.blob((sx * 0.026, yf - 0.014, zc + 0.018), 0.014, "BH_Emissive", scale=(1.25, 0.6, 0.8), n=8, rings=4),
            "head")
    # bark "brow" splits running up from the lip
    for sx in (1, -1):
        add(W.root([(sx * 0.04, yf + 0.0, zc + az), (sx * 0.05, yf + 0.02, zc + az + 0.05),
                    (sx * 0.045, yf + 0.05, zc + az + 0.1)], 0.012, 0.004, "BH_Leather", n=4, seed=sx + 8), "head")
    # crown of long crimson thorns (tallest at the front / back, sweeping out and up)
    zt = z0 + 0.17
    for k in range(11):
        a = 2 * math.pi * k / 11 - math.pi / 2
        r = interp_rows(rows, zt)
        base = np.array([(r[1] - 0.01) * math.cos(a), r[5] + (r[2] - 0.01) * math.sin(a), zt + 0.01 * (k % 2)])
        out = np.array([math.cos(a), math.sin(a), 0.0])
        ln = 0.2 + 0.07 * (k % 2 == 0) + 0.05 * abs(math.sin(a))
        dirn = normalize(out * 0.55 + np.array([0, 0, 1.0]))
        add(thorn(base, dirn, ln, 0.03 if k % 2 == 0 else 0.022, n=5), "head")
    # vine band round the crown base
    band = [np.array([(interp_rows(rows, zt)[1] + 0.004) * math.cos(a), interp_rows(rows, zt)[5] +
                      (interp_rows(rows, zt)[2] + 0.004) * math.sin(a), zt - 0.01]) for a in np.linspace(0, 2 * math.pi, 15)]
    add(W.tube(band, 0.014, "BH_Fur", n=5, cap=False), "head")


def shoulder_thorns(body, s):
    """A burst of long crimson thorns from each shoulder (rigid to shoulder / upper arm)."""
    sx = 1 if s == "L" else -1
    sh = body.head("upper_arm." + s)
    w = W.const_w({"shoulder." + s: 0.45, "upper_arm." + s: 0.55})
    body.add(K.jitter(K.blob(sh + np.array([0.0, 0.0, 0.05]), 0.085, "BH_Fur", scale=(1.1, 1.1, 0.8), n=8, rings=5),
                      0.008, seed=7 + (sx > 0)), weights=w)
    rng = np.random.default_rng(20 + (sx > 0))
    for k in range(7):
        a = 2 * math.pi * k / 7
        tilt = 0.45 + 0.25 * rng.random()
        d = normalize(np.array([sx * 0.6 + tilt * math.cos(a), tilt * math.sin(a), 1.0]))
        base = sh + np.array([0, 0, 0.06]) + d * 0.04
        body.add(thorn(base, d, 0.13 + 0.09 * rng.random(), 0.024, n=5), weights=w)


def thorn_club(body):
    """Left forearm swelling into a heavy knotted bark club studded with crimson thorns (club head rigid on hand.L)."""
    fa, ha = "forearm.L", "hand.L"
    el, wr = body.head(fa), body.head(ha)
    d = normalize(wr - el)
    tip = wr + d * 0.36
    pts = [wr - d * 0.04, wr + d * 0.08, wr + d * 0.2, wr + d * 0.3, tip]
    radii = [0.075, 0.095, 0.12, 0.118, 0.07]
    V, F = M.tube(pts, [(r, r) for r in radii], n=12, up=(0, 0, 1))
    club = K.jitter(M.Part(V, F, "BH_Wood", name="club"), 0.008, seed=71)
    body.add(club, ha)
    # knots + bark ridges
    rng = np.random.default_rng(72)
    side = normalize(np.cross(d, (0, 0, 1)))
    up = np.cross(side, d)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        c = wr + d * (0.12 + 0.05 * k) + (side * math.cos(a) + up * math.sin(a)) * 0.1
        body.add(K.blob(c, 0.035, "BH_Leather", scale=(1.0, 1.0, 0.7), n=7, rings=4), ha)
    # thorn studs all round the club head
    for i, u in enumerate((0.1, 0.17, 0.24, 0.31)):
        r = np.interp(u, [-0.04, 0.08, 0.2, 0.3, 0.36], radii)
        for k in range(7):
            a = 2 * math.pi * (k + 0.5 * (i % 2)) / 7
            nrm = side * math.cos(a) + up * math.sin(a)
            base = wr + d * u + nrm * r * 0.85
            body.add(thorn(base, normalize(nrm + d * 0.25), 0.07 + 0.03 * rng.random(), 0.018), ha)
    body.add(thorn(tip + d * 0.0, d, 0.12, 0.03, n=5), ha)


# ================================================================================================= weapon
def vine_whip():
    """Rigid curling vine whip (weapon space: grip at origin, +Z forward): a bark grip, then a long tapering green vine
    that curves out, sweeps round in a loose S and ends in a tight curl, crimson thorns all along it."""
    parts = []
    V, F = M.lathe([(0, -0.14), (0.028, -0.13), (0.024, -0.1), (0.022, 0.06), (0.026, 0.09), (0.0, 0.1)], 8)
    parts.append(K.jitter(M.Part(V, F, "BH_Wood", name="whipgrip"), 0.002, seed=3))
    for z in (-0.08, -0.02, 0.04):
        V, F = M.lathe([(0, z - 0.01), (0.027, z - 0.01), (0.027, z + 0.01), (0, z + 0.01)], 8)
        parts.append(M.Part(V, F, "BH_Fur", name="whipwrap"))
    # centreline: out along +Z, bending toward +X, back toward -X, ending in a curl (mostly in the X-Z plane)
    pts = []
    n = 40
    for i in range(n + 1):
        t = i / n
        z = 0.08 + 0.92 * math.sin(t * math.pi * 0.5) ** 0.9
        x = 0.22 * math.sin(t * math.pi * 1.4) - 0.05 * t
        y = 0.03 * math.sin(t * math.pi * 2.0)
        pts.append(np.array([x, y, z]))
    # final curl
    c = pts[-1]
    d = normalize(pts[-1] - pts[-2])
    side = normalize(np.cross(d, (0, 1, 0)))
    for k in range(1, 10):
        a = k / 9 * math.pi * 1.5
        r = 0.09 * (1 - 0.5 * k / 9)
        pts.append(c + d * r * math.sin(a) + side * r * (1 - math.cos(a)))
    q = np.array(pts)
    m = len(q)
    radii = [0.022 * (1 - 0.72 * (i / (m - 1)) ** 0.8) + 0.003 for i in range(m)]
    V, F = M.tube(q, [(r, r) for r in radii], n=6, up=(0, 1, 0))
    parts.append(M.Part(V, F, "BH_Fur", name="whip"))
    rng = np.random.default_rng(9)
    for i in range(2, m - 1, 2):
        dd = normalize(q[i + 1] - q[i - 1])
        sd = normalize(np.cross(dd, rng.normal(size=3)))
        parts.append(thorn(q[i] + sd * radii[i] * 0.5, normalize(sd + dd * 0.4), 0.035 + 0.02 * radii[i] / 0.022 +
                           0.01 * rng.random(), max(radii[i] * 0.45, 0.006)))
    # a couple of dried leaves near the grip
    for k in range(2):
        parts.append(A.feather(q[3 + 3 * k], (0.6 * (1 if k else -1), 0.3, 0.3), 0.08, 0.045, "BH_Flesh",
                               side=(0, 1, 0)))
    return parts
