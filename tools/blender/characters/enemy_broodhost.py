"""Broodhost (bh-013, Builder B2 "brutes"; corrupted giant, also reused as a final boss at 1.9x): a bloated,
hulking, hunched grey-violet giant ~2.5 m to the top of its hump. Its back, hump, shoulders and belly are crusted with
clusters of swollen glowing sacs (BH_Emissive, sickly magenta-violet), each with a dark curled shape pressed against
the inside of the membrane, raw flesh rims and dark veins spreading out from them. The small head is sunk low between
the shoulders and ends in a round lamprey mouth (rings of hooked teeth round a black throat) under two tiny glowing
eyes. The right arm swells into a huge fleshy club-fist of knotted knuckles and bone spurs (rigid on weapon.R); the
left arm ends in a long-clawed hand. Rope bindings cut into the belly and upper body, rope wraps on the left arm and
shins, a torn rag loincloth on a rope belt, bare feet.

Kit: enemy_bandit_cutthroat (standard-space authoring, SB). SCALE = 1.47 (std-space top of hump ~1.76).
Clips: axe_1, axe_2 (club swings), axe_heavy (overhead smash), boss_slam, boss_roar, cast_area (brood burst)."""
import math
import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, M_align_z
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K

SCALE = 1.47
PROPS = proportions(SCALE, shoulder_x=0.28 * SCALE, upper_len=0.3 * SCALE, fore_len=0.28 * SCALE,
                    hip_x=0.13 * SCALE, clav_drop=0.08 * SCALE)
PALETTE = "broodhost"
PALETTE_COLORS = {
    "BH_Skin": ((0.27, 0.235, 0.29), 0.0, 0.5, None, 0.0, 1.0),              # bloated grey-violet hide
    "BH_Flesh": ((0.34, 0.09, 0.19), 0.0, 0.42, None, 0.0, 1.0),             # raw rims / club flesh / lips
    "BH_Fur": ((0.1, 0.035, 0.12), 0.0, 0.6, None, 0.0, 1.0),                # dark violet veins
    "BH_Bone": ((0.56, 0.5, 0.44), 0.0, 0.55, None, 0.0, 1.0),               # teeth, claws, bone spurs
    "BH_Cloth_Primary": ((0.15, 0.13, 0.11), 0.0, 0.95, None, 0.0, 1.0),     # filthy rags
    "BH_Leather": ((0.23, 0.17, 0.09), 0.0, 0.9, None, 0.0, 1.0),            # rope
    "BH_Shadow": ((0.035, 0.01, 0.04), 0.0, 0.8, None, 0.0, 1.0),            # throat, curled shapes in the sacs
    "BH_Emissive": ((0.95, 0.3, 0.9), 0.0, 0.35, (0.9, 0.22, 0.95), 6.0, 1.0),  # sacs + eyes
}
CLIPS = ["axe_1", "axe_2", "axe_heavy", "boss_slam", "boss_roar", "cast_area"]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


# (z, rx, ry_front, ry_back, keel, cy): huge low belly, a high hump the head sinks under
TORSO = [
    (0.9, 0.22, 0.16, 0.15, 0.0, 0.0),
    (0.98, 0.265, 0.25, 0.16, 0.0, -0.03),
    (1.07, 0.29, 0.3, 0.17, 0.02, -0.06),
    (1.17, 0.295, 0.28, 0.19, 0.03, -0.065),
    (1.27, 0.3, 0.2, 0.25, 0.03, -0.05),
    (1.37, 0.315, 0.15, 0.29, 0.02, -0.03),
    (1.45, 0.305, 0.125, 0.31, 0.0, -0.015),
    (1.52, 0.27, 0.1, 0.305, 0.0, 0.005),
    (1.58, 0.21, 0.08, 0.26, 0.0, 0.035),
    (1.63, 0.12, 0.05, 0.17, 0.0, 0.065),
    (1.655, 0.04, 0.02, 0.065, 0.0, 0.08),
]
TORSO_W = K.zspec_w([(0.97, "hips"), (1.08, "spine"), (1.2, "spine"), (1.3, "chest")])
HEAD_DY, HEAD_DZ = -0.2, -0.2
HEAD = [   # small skull, the lower face drawn out into a round sucker mouth (added separately)
    (1.585, 0.04, 0.04, 0.04, 0.0, -0.06),
    (1.6, 0.068, 0.07, 0.06, 0.0, -0.05),
    (1.63, 0.078, 0.08, 0.072, 0.02, -0.035),
    (1.665, 0.08, 0.078, 0.084, 0.02, -0.02),
    (1.7, 0.078, 0.072, 0.088, 0.0, -0.012),
    (1.735, 0.068, 0.06, 0.08, 0.0, -0.005),
    (1.76, 0.045, 0.04, 0.056, 0.0, 0.0),
    (1.773, 0.02, 0.018, 0.025, 0.0, 0.002),
]


def hshift(pts):
    return np.asarray(pts, float) + np.array([0, HEAD_DY, HEAD_DZ])


def surf(z, frac, g=0.0):
    """Point on the torso surface + its outward normal (0 = front, 0.25 = own left, 0.5 = back)."""
    q = K.ring_frac(TORSO, z, g, [frac], p=2.2)[0]
    a = 2 * math.pi * frac - math.pi / 2
    dz = 0.0
    if z > 1.45:                         # the hump rounds over the top: tilt normals up
        dz = (z - 1.45) / 0.2 * 1.2
    elif z < 1.12 and math.sin(a) < 0:  # the belly sags: tilt down
        dz = -0.25
    return q, normalize(np.array([math.cos(a), math.sin(a), dz]))


def oriented(V, F, mat, name, n, at):
    return M.Part(V, F, mat, name=name).rot(M_align_z(normalize(n))).move(at)


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft(K.rows_between(TORSO, 0.9, 1.655, n_extra=6), n=40, p=2.2, cap0=True, cap1=True)
    sb.add(M.Part(V, F, "BH_Skin", name="torso"), weights=TORSO_W)
    # thick neck folds dropping forward to the sunk head
    V, F = M.tube([(0, 0.02, 1.42), (0, -0.07, 1.45), (0, -0.15, 1.44), (0, -0.2, 1.43)],
                  [(0.12, 0.11), (0.11, 0.1), (0.09, 0.085), (0.07, 0.07)], n=14, up=(0, 0, 1))
    sb.add(M.Part(V, F, "BH_Skin", name="neck"), weights=lambda V: [
        {"chest": 1.0} if v[1] > -0.05 else ({"chest": 0.4, "neck": 0.6} if v[1] > -0.13 else
                                              {"neck": 0.5, "head": 0.5}) for v in V])
    head(sb)
    sacs(sb)
    ropes(sb)
    # arms
    K.bare_arm(sb, "L", r_up=0.075, r_fore=0.062, r_wrist=0.048, bulk=1.4)
    K.add_fist(sb, "L", "BH_Skin", "BH_Skin", scale=1.45)
    claws(sb, "L")
    club_arm(sb)
    # legs
    seat(sb)
    legs(sb)
    loincloth(sb)


# ------------------------------------------------------------------------------------------------------ head
def head(sb):
    rows = [(r[0] + HEAD_DZ,) + r[1:5] + (r[5] + HEAD_DY,) for r in HEAD]
    V, F = torso_loft(rows, n=18, p=2.1, cap0=True, cap1=True)
    sb.add(M.Part(V, F, "BH_Skin", name="head"), "head")
    # lamprey mouth: a short fleshy funnel pushed forward-down, black throat, rings of hooked teeth
    c = hshift([(0.0, -0.085, 1.615)])[0]
    n = normalize(np.array([0.0, -1.0, -0.35]))
    R = M_align_z(n)
    V, F = M.lathe([(0.0, -0.05), (0.07, -0.05), (0.085, 0.0), (0.082, 0.03), (0.07, 0.045), (0.05, 0.04),
                    (0.042, 0.02), (0.0, 0.0)], 18)
    sb.add(M.Part(V, F, "BH_Flesh", name="sucker").rot(R).move(c), "head")
    V, F = M.sphere(0.045, 12, 6, scale=(1.0, 1.0, 0.35))
    sb.add(M.Part(V, F, "BH_Shadow", name="throat").rot(R).move(c + n * 0.03), "head")
    for ring_r, cnt, ln, zoff in ((0.066, 12, 0.03, 0.036), (0.045, 9, 0.024, 0.026)):
        for k in range(cnt):
            a = 2 * math.pi * (k + 0.5 * (ring_r < 0.05)) / cnt
            base = np.array([ring_r * math.cos(a), ring_r * math.sin(a), zoff])
            tip = base * np.array([0.55, 0.55, 1.0]) + np.array([0, 0, 0.01])
            V, F = M.tube([base, base + (tip - base) * 0.5 + np.array([0, 0, 0.006]), tip],
                          [(0.008, 0.008), (0.005, 0.005), (0.0008, 0.0008)], n=4, up=(0, 0, 1))
            sb.add(M.Part(V, F, "BH_Bone", name="tooth").rot(R).move(c), "head")
    # tiny sunken glowing eyes above the sucker, heavy brow folds
    for sx in (1, -1):
        e = hshift([(sx * 0.035, -0.07, 1.69)])[0]
        V, F = M.sphere(0.017, 8, 5, center=e + (0, 0.004, 0), scale=(1.2, 0.6, 0.8))
        sb.add(M.Part(V, F, "BH_Shadow", name="socket"), "head")
        V, F = M.sphere(0.0085, 6, 4, center=e + (0, -0.004, 0))
        sb.add(M.Part(V, F, "BH_Emissive", name="eye"), "head")
    V, F = M.tube(hshift([(-0.075, -0.035, 1.695), (-0.045, -0.066, 1.708), (0.0, -0.078, 1.714),
                          (0.045, -0.066, 1.708), (0.075, -0.035, 1.695)]), [(0.018, 0.018)] * 5, n=8, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Skin", name="brow"), "head")
    # gill-like slits down the sides of the head
    for sx in (1, -1):
        for k in range(3):
            p0 = hshift([(sx * 0.078, -0.02 + 0.022 * k, 1.66)])[0]
            V, F = M.tube([p0 + (0, 0, 0.025), p0 - (0, 0, 0.025)], [(0.005, 0.005)] * 2, n=4, up=(1, 0, 0))
            sb.add(M.Part(V, F, "BH_Shadow", name="gill"), "head")


# ------------------------------------------------------------------------------------------------------ sacs
def sac(sb, q, n, r, weights, seed=0, veins=True):
    """Glowing sac bulging out of a raw rim; a dark curled shape pressed against the membrane from inside."""
    rng = np.random.default_rng(seed)
    c = q + n * r * 0.5
    V, F = M.sphere(r, 12, 7, scale=(1.0, 0.92, 0.88))
    sb.add(oriented(V, F, "BH_Emissive", "sac", n, c), weights=weights)
    V, F = M.sphere(r * 1.1, 12, 4, scale=(1.0, 1.0, 0.4))
    sb.add(oriented(V, F, "BH_Flesh", "sac_rim", n, q - n * r * 0.08), weights=weights)
    # the curled shape: a C-shaped tube just under the outer surface (its back pokes through -> dark curl)
    t1 = normalize(np.cross(n, (0.3, 0.5, 0.8)))
    t2 = np.cross(n, t1)
    rot = rng.random() * 2 * math.pi
    pts = []
    for i in range(7):
        a = rot + math.radians(-130 + 260 * i / 6)
        pts.append(c + n * r * 0.74 + (t1 * math.cos(a) + t2 * math.sin(a)) * r * 0.4)
    rad = [r * f for f in (0.12, 0.2, 0.24, 0.24, 0.21, 0.16, 0.24)]
    V, F = M.tube(pts, [(x, x) for x in rad], n=6, up=tuple(n))
    sb.add(M.Part(V, F, "BH_Shadow", name="brood"), weights=weights)
    if not veins:
        return
    for k in range(3):
        a = 2 * math.pi * (k + rng.random() * 0.6) / 3
        d = t1 * math.cos(a) + t2 * math.sin(a)
        pts = [q + d * r * (1.05 + 0.32 * i) - n * 0.006 * i for i in range(4)]
        V, F = M.tube(pts, [(0.007, 0.007), (0.006, 0.006), (0.004, 0.004), (0.002, 0.002)], n=4, up=tuple(n))
        sb.add(M.Part(V, F, "BH_Fur", name="vein"), weights=weights)


def sacs(sb):
    # back / hump cluster (the silhouette key from behind and above)
    spots = [(1.22, 0.5, 0.09), (1.3, 0.4, 0.075), (1.32, 0.6, 0.085), (1.42, 0.47, 0.11), (1.44, 0.34, 0.07),
             (1.47, 0.63, 0.08), (1.55, 0.53, 0.085), (1.56, 0.4, 0.07), (1.62, 0.47, 0.06), (1.37, 0.53, 0.06),
             (1.2, 0.33, 0.055), (1.18, 0.66, 0.06)]
    # belly cluster
    spots += [(1.02, 0.02, 0.075), (1.1, 0.94, 0.06), (0.97, 0.9, 0.05), (1.15, 0.08, 0.05), (1.06, 0.13, 0.045)]
    for k, (z, f, r) in enumerate(spots):
        q, n = surf(z, f)
        sac(sb, q, n, r, TORSO_W, seed=k, veins=r > 0.058 and z < 1.4)
    # shoulder clusters (bulging over the shoulder tops)
    for s, sx in (("L", 1), ("R", -1)):
        sh = sb.head("upper_arm." + s)
        w = sb.seg(["chest", "shoulder." + s], power=6)
        for k, (dx, dy, dz, r) in enumerate(((-0.05, 0.04, 0.09, 0.08), (0.03, 0.0, 0.08, 0.062),
                                             (-0.1, 0.1, 0.07, 0.06), (0.0, 0.08, 0.03, 0.05))):
            q = sh + np.array([sx * dx, dy, dz])
            n = normalize(np.array([sx * 0.4, 0.3, 1.0]))
            sac(sb, q, n, r, w, seed=40 + k + (10 if s == "R" else 0), veins=False)


# ----------------------------------------------------------------------------------------------------- ropes
def ropes(sb):
    """Rope bindings cutting into the belly, and a rope wound diagonally round the upper body."""
    for z, g in ((0.99, 0.004), (1.13, 0.0)):
        ring = K.ring_frac(TORSO, z, g, np.linspace(0, 1, 33)[:-1], p=2.2)
        ring = np.vstack([ring, ring[:1]])
        V, F = M.tube(ring, [(0.016, 0.016)] * len(ring), n=6, up=(0, 0, 1), cap0=False, cap1=False)
        sb.add(M.Part(V, F, "BH_Leather", name="rope"), weights=TORSO_W)
    # diagonal wrap: from the left hip round the back, over the right shoulder, down the front
    pts = []
    for i in range(22):
        t = i / 21
        f = 0.25 + 0.75 * t
        z = 1.05 + 0.4 * t
        pts.append(K.ring_frac(TORSO, z, 0.012, [f % 1.0], p=2.2)[0])
    V, F = M.tube(pts, [(0.015, 0.015)] * len(pts), n=6, up=(0, 0, 1))
    sb.add(M.Part(V, F, "BH_Leather", name="rope_wrap"), weights=TORSO_W)
    p, _ = K.on_ring(TORSO, 1.13, 0.02, 0.1)
    V, F = M.sphere(0.03, 8, 5, center=p)
    sb.add(M.Part(V, F, "BH_Leather", name="knot"), weights=TORSO_W)
    V, F = M.tube([p, p + (0.01, -0.02, -0.08), p + (0.0, -0.025, -0.16)], [(0.013, 0.013)] * 3, n=5, up=(1, 0, 0))
    sb.add(M.Part(V, F, "BH_Leather", name="rope_end"), weights=TORSO_W)
    # rope wraps on the left upper arm
    K.wrap_band(sb, "upper_arm.L", "forearm.L", 0.45, 0.7, 0.1, "BH_Leather", turns=3, width=0.018, thick=0.012)


# ------------------------------------------------------------------------------------------------------ arms
def claws(sb, s):
    A = sb.axes("weapon." + s)
    o = sb.head("weapon." + s)
    xs = 1.0 if s == "R" else -1.0
    for y in (-0.045, -0.015, 0.015, 0.045):
        base = o + A @ np.array([xs * 0.065, y, 0.0])
        mid = base + A @ np.array([xs * 0.03, 0.0, -0.04])
        tip = base + A @ np.array([xs * 0.015, 0.0, -0.095])
        V, F = M.tube([base, mid, tip], [(0.011, 0.011), (0.007, 0.007), (0.001, 0.001)], n=5, up=A[:, 1])
        sb.add(M.Part(V, F, "BH_Bone", name="claw"), "hand." + s)


def club_arm(sb):
    """Right arm: bloated upper arm, the forearm swelling into a huge club-fist of knotted flesh and knuckle bone."""
    ua, fa, ha = "upper_arm.R", "forearm.R", "hand.R"
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    pts = [sh + (0.05, 0, 0.02), sh, sh + (el - sh) * 0.3, sh + (el - sh) * 0.7, el, el + (wr - el) * 0.35,
           el + (wr - el) * 0.75, wr]
    prof = [(0.07, 0.075), (0.095, 0.1), (0.098, 0.1), (0.09, 0.095), (0.088, 0.092), (0.1, 0.105), (0.115, 0.12),
            (0.12, 0.125)]
    V, F = M.tube(pts, prof, n=14, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Skin", name="arm"), weights=sb.seg(["chest", "shoulder.R", ua, fa, ha], power=9))
    # a few sacs on the swollen forearm
    d = normalize(wr - el)
    side = normalize(np.cross(d, (0, 1, 0)))
    fw = np.cross(side, d)
    for k, (u, ang, r) in enumerate(((0.35, 60, 0.045), (0.6, 200, 0.04), (0.5, 320, 0.035))):
        a = math.radians(ang)
        nrm = side * math.cos(a) + fw * math.sin(a)
        q = el + (wr - el) * u + nrm * 0.1
        sac(sb, q, nrm, r, lambda V: [{fa: 1.0}] * len(V), seed=70 + k, veins=False)
    # the club-fist (weapon space: +X distal / knuckles, +Z thumb-forward, flats +-Y)
    parts = []
    prof = [(0.0, -0.1), (0.13, -0.08), (0.155, 0.0), (0.185, 0.13), (0.215, 0.27), (0.21, 0.37), (0.16, 0.46),
            (0.075, 0.5), (0.0, 0.51)]
    V, F = M.lathe(prof, 18)
    club = M.Part(V, F, "BH_Flesh", name="club")
    club.warp(lambda v: v * (1 + 0.09 * math.sin(v[2] * 27 + math.atan2(v[1], v[0]) * 3)))
    club.rot(Ry(90)).rot(Ry(-15))
    parts.append(club)
    V, F = M.lathe([(0.0, -0.11), (0.13, -0.1), (0.148, 0.02), (0.158, 0.12), (0.0, 0.13)], 14)
    parts.append(M.Part(V, F, "BH_Skin", name="club_skin").rot(Ry(90)).rot(Ry(-15)))
    # knotted knuckle lumps (bone) ringed round the striking end + spurs
    rng = np.random.default_rng(8)
    for k in range(4):
        y = -0.1 + 0.066 * k
        V, F = M.sphere(0.06, 8, 6, center=(0.47, y * 1.2, 0.05 - 0.02 * abs(y) / 0.1), scale=(0.8, 0.85, 1.0))
        parts.append(M.Part(V, F, "BH_Bone", name="knuckle").rot(Ry(-15)))
    for k in range(7):
        u = 0.1 + 0.25 * rng.random()
        a = 2 * math.pi * rng.random()
        base = np.array([u + 0.05, 0.18 * math.cos(a), 0.18 * math.sin(a)])
        out = normalize(np.array([0.4 + 0.4 * rng.random(), math.cos(a), math.sin(a)]))
        ln = 0.07 + 0.06 * rng.random()
        V, F = M.tube([base - out * 0.02, base + out * ln * 0.6, base + out * ln], [(0.024, 0.024), (0.013, 0.013),
                      (0.002, 0.002)], n=6, up=(0, 0, 1) if abs(out[2]) < 0.9 else (1, 0, 0))
        parts.append(M.Part(V, F, "BH_Bone", name="spur").rot(Ry(-15)))
    # two small glowing sacs bulging from the back of the club
    for k, (u, a, r) in enumerate(((0.2, 2.2, 0.045), (0.3, 3.6, 0.04))):
        n = np.array([0.2, math.cos(a), math.sin(a)])
        n = normalize(n)
        c = np.array([u + 0.05, 0.0, 0.0]) + n * 0.19
        V, F = M.sphere(r, 10, 6, scale=(1.0, 1.0, 0.85))
        parts.append(oriented(V, F, "BH_Emissive", "club_sac", n, c).rot(Ry(-15)))
    K.add_weapon(sb, "R", parts)


# ------------------------------------------------------------------------------------------------------ legs
def seat(sb):
    V, F = torso_loft([(0.8, 0.2, 0.13, 0.14, 0.0), (0.88, 0.22, 0.15, 0.155, 0.0), (0.96, 0.225, 0.16, 0.155, 0.0)],
                      n=24)
    sb.add(M.Part(V, F, "BH_Skin", name="seat"), weights=sb.skirt(0.95, 0.8, max_leg=0.7, center_w=0.06))


def legs(sb):
    for s in ("L", "R"):
        th, sh = "thigh." + s, "shin." + s
        h, k, a = sb.head(th), sb.head(sh), sb.tail(sh)
        pts = [h + (0, 0, 0.06), h + (k - h) * 0.45, k + (0, 0, 0.02), k + (a - k) * 0.5, a + (0, 0, 0.03)]
        prof = [(0.145, 0.15), (0.13, 0.135), (0.1, 0.105), (0.095, 0.1), (0.068, 0.074)]
        V, F = M.tube(pts, prof, n=16, up=(0, -1, 0))
        sb.add(M.Part(V, F, "BH_Skin", name="leg"), weights=sb.seg([th, sh], power=10))
        # rope-wrapped shins
        for u in (0.45, 0.62, 0.78):
            c = k + (a - k) * u
            rr = 0.104 - 0.033 * u
            ring = [c + (rr * math.cos(t), rr * math.sin(t), 0.012 * math.sin(t)) for t in np.linspace(0, 2 * math.pi,
                                                                                                      13)]
            V, F = M.tube(ring, [(0.011, 0.011)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
            sb.add(M.Part(V, F, "BH_Leather", name="shin_rope"), sh)
        # a sac on the outer thigh
        sx = 1 if s == "L" else -1
        q = h + (k - h) * 0.5 + np.array([sx * 0.125, 0.02, 0.0])
        sac(sb, q, normalize(np.array([sx, 0.3, 0.1])), 0.045, lambda V, th=th: [{th: 1.0}] * len(V), seed=90 + sx,
            veins=False)
        # bare feet with bone toenails
        hx = h[0]
        V, F = M.tube([(hx, 0.06, 0.09), (hx, 0.0, 0.055), (hx, -0.11, 0.04)], [(0.07, 0.06), (0.078, 0.052),
                      (0.074, 0.038)], n=12, up=(0, 0, 1))
        sb.add(M.Part(V, F, "BH_Skin", name="foot"), "foot." + s)
        V, F = M.tube([(hx, -0.11, 0.04), (hx, -0.19, 0.028), (hx, -0.22, 0.022)], [(0.074, 0.038), (0.066, 0.028),
                      (0.04, 0.017)], n=12, up=(0, 0, 1))
        sb.add(M.Part(V, F, "BH_Skin", name="toes"), "toe." + s)
        for x in (-0.04, 0.0, 0.04):
            V, F = M.sphere(0.012, 5, 3, center=(hx + x, -0.225, 0.03))
            sb.add(M.Part(V, F, "BH_Bone", name="toenail"), "toe." + s)


def loincloth(sb):
    z = 0.95
    ring = K.ring_frac(TORSO, z, 0.03, np.linspace(0, 1, 29)[:-1], p=2.2)
    ring = np.vstack([ring, ring[:1]])
    V, F = M.tube(ring, [(0.017, 0.017)] * len(ring), n=6, up=(0, 0, 1), cap0=False, cap1=False)
    sb.add(M.Part(V, F, "BH_Leather", name="rope_belt"), "hips")
    for fr, w, ln in ((0.0, 0.26, 0.36), (0.5, 0.3, 0.34), (0.2, 0.14, 0.26), (0.8, 0.14, 0.24)):
        c, ang = K.on_ring(TORSO, z, 0.035, fr)

        def fn(u, v, w=w, ln=ln):
            x = (u - 0.5) * (w + 0.04 * v)
            zz = -ln * v - (0.05 * v * math.sin(u * 17.0 + 1.3) ** 2 if v > 0.75 else 0.0)
            return (x, -0.02 * v * v, zz)
        p = K.cloth_panel(fn, 7, 6, "BH_Cloth_Primary", thick=0.01, flip=True)
        p.rot(Rz(ang)).move(c)
        sb.add(p, weights=sb.skirt(z, z - ln, max_leg=0.45, center_w=0.1))
