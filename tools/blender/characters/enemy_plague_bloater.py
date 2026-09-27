"""Plague Bloater (bh-010, Builder A; corrupted brute): a hulking man swollen by rot until he is mostly belly. A huge
round, taut, sickly yellow-green gut sagging over a rope belt, crossed by crude stitched seams, pocked with raw
pustules and bulging with glowing green plague sacs (the big ones on the belly, back and shoulders read as "about to
pop"), dark veins spreading round each sac. The small bald head is sunk between hunched shoulders, jaw hanging open
in a wide black maw; tiny green eyes. Heavy bare arms (bandaged left forearm), stubby thick legs in torn rag
trousers, bare wrapped feet, a rag loincloth under the gut and a rusty butcher's cleaver-axe in the right hand.
~2.0 m to the crown. Kit: enemy_bandit_cutthroat (standard-space SB authoring, like the Ghoul Brute)."""
import math
import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, M_align_z
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import kit_a_common as A

SCALE = 1.18
PROPS = proportions(SCALE, shoulder_x=0.33 * SCALE, upper_len=0.29 * SCALE, fore_len=0.27 * SCALE,
                    hip_x=0.125 * SCALE, clav_drop=0.06 * SCALE)
PALETTE = "plague_bloater"
PALETTE_COLORS = {
    "BH_Skin": ((0.36, 0.37, 0.2), 0.0, 0.42, None, 0.0, 1.0),               # taut sickly yellow-green skin
    "BH_Flesh": ((0.42, 0.14, 0.1), 0.0, 0.4, None, 0.0, 1.0),               # raw pustules / sac rims
    "BH_Fur": ((0.16, 0.2, 0.07), 0.0, 0.6, None, 0.0, 1.0),                 # dark veins / bruising
    "BH_Bone": ((0.55, 0.5, 0.33), 0.0, 0.6, None, 0.0, 1.0),                # teeth / nails
    "BH_Cloth_Primary": ((0.2, 0.16, 0.1), 0.0, 0.93, None, 0.0, 1.0),       # filthy rags
    "BH_Leather": ((0.2, 0.15, 0.08), 0.0, 0.85, None, 0.0, 1.0),            # rope / stitches / bandages
    "BH_Rust": ((0.28, 0.13, 0.06), 0.45, 0.78, None, 0.0, 1.0),             # cleaver
    "BH_Wood": ((0.12, 0.08, 0.045), 0.0, 0.75, None, 0.0, 1.0),
    "BH_Shadow": ((0.03, 0.025, 0.02), 0.0, 0.8, None, 0.0, 1.0),            # maw / sockets / seam cuts
    "BH_Emissive": ((0.55, 1.0, 0.22), 0.0, 0.35, (0.5, 1.0, 0.18), 6.0, 1.0),   # plague sacs / eyes
}
CLIPS = ["axe_1", "boss_slam", "cast_heavy", "boss_roar", "cast_area"]
PREVIEW_HEIGHT = 2.35


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


# (z, rx, ry_front, ry_back, keel, cy)  standard space. A huge round gut hanging low and forward, the back rising into
# a hunched mound round a sunken head.
TORSO = [
    (0.76, 0.1, 0.08, 0.06, 0.0, -0.22),      # bottom of the sagging gut, hanging in front of the thighs
    (0.8, 0.24, 0.21, 0.12, 0.0, -0.2),
    (0.86, 0.33, 0.31, 0.16, 0.0, -0.17),
    (0.94, 0.385, 0.38, 0.19, 0.0, -0.145),
    (1.03, 0.4, 0.43, 0.2, 0.0, -0.125),
    (1.12, 0.39, 0.43, 0.2, 0.0, -0.11),
    (1.21, 0.36, 0.38, 0.21, 0.0, -0.09),
    (1.3, 0.315, 0.3, 0.22, 0.0, -0.065),
    (1.38, 0.275, 0.23, 0.22, 0.0, -0.045),
    (1.42, 0.27, 0.2, 0.22, 0.0, -0.035),
    (1.49, 0.25, 0.13, 0.22, 0.0, -0.015),
    (1.56, 0.2, 0.1, 0.19, 0.0, -0.005),
    (1.61, 0.13, 0.075, 0.14, 0.0, 0.0),
    (1.64, 0.06, 0.04, 0.07, 0.0, 0.0),
]
P_TORSO = 2.05
TORSO_W = K.zspec_w([(0.99, "hips"), (1.1, "spine"), (1.22, "spine"), (1.34, "chest")])
HEAD_DY, HEAD_DZ = -0.1, -0.12
HEAD = [   # small bald head, heavy hanging jaw
    (1.55, 0.03, 0.03, 0.03, 0.0, -0.05),
    (1.57, 0.066, 0.064, 0.05, 0.0, -0.04),
    (1.6, 0.08, 0.074, 0.066, 0.02, -0.025),
    (1.64, 0.084, 0.078, 0.078, 0.03, -0.012),
    (1.68, 0.083, 0.078, 0.086, 0.04, -0.006),
    (1.72, 0.08, 0.076, 0.088, 0.06, -0.002),
    (1.76, 0.07, 0.066, 0.08, 0.0, 0.002),
    (1.79, 0.05, 0.048, 0.06, 0.0, 0.004),
    (1.806, 0.02, 0.02, 0.025, 0.0, 0.005),
]
HEAD_WF = lambda V: [{"neck": 0.35, "head": 0.65}] * len(V)   # noqa: E731  (head sunk low: soften the pivot)


def hshift(pts):
    return np.asarray(pts, float).reshape(-1, 3) + np.array([0, HEAD_DY, HEAD_DZ])


def surf(z, frac, g=0.0):
    """Torso surface point at height z / angle fraction (0 front, 0.25 own left, 0.5 back) + outward normal."""
    q = K.ring_frac(TORSO, z, g, [frac], p=P_TORSO)[0]
    a = 2 * math.pi * frac - math.pi / 2
    # vertical tilt from the local slope of the belly
    r0 = K.ring_frac(TORSO, z - 0.02, g, [frac], p=P_TORSO)[0]
    r1 = K.ring_frac(TORSO, z + 0.02, g, [frac], p=P_TORSO)[0]
    h = np.array([math.cos(a), math.sin(a), 0.0])
    slope = np.dot(r1 - r0, h) / 0.04
    n = normalize(h - np.array([0, 0, 1.0]) * slope)
    return q, n


def oriented(V, F, mat, name, n, at):
    p = M.Part(V, F, mat, name=name)
    p.V = np.asarray(p.V) @ M_align_z(n).T + np.asarray(at, float)
    return p


# ------------------------------------------------------------------------------------------------ build
def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft(K.rows_between(TORSO, 0.76, 1.64, n_extra=8), n=44, p=P_TORSO, cap0=True, cap1=True)
    torso = M.Part(V, F, "BH_Skin", name="torso")
    # sagging navel crease and a slight lopsided swell on the left of the gut
    torso.warp(lambda v: v + np.array([0.02, -0.025, 0.0]) * math.exp(-((v[0] - 0.13) ** 2 + (v[2] - 1.05) ** 2) / 0.014)
               * (v[1] < -0.2))
    sb.add(torso, weights=TORSO_W)
    # navel
    q, n = surf(0.99, 0.0)
    V, F = M.sphere(0.022, 8, 5, scale=(1.0, 1.0, 0.5))
    sb.add(oriented(V, F, "BH_Shadow", "navel", n, q - n * 0.004), weights=TORSO_W)
    head(sb)
    seams(sb)
    sacs(sb)
    pustules(sb)
    arms(sb)
    legs(sb)
    belt_and_rags(sb)
    K.add_weapon(sb, "R", cleaver_axe())


def head(sb):
    rows = [(r[0] + HEAD_DZ,) + r[1:5] + (r[5] + HEAD_DY,) for r in HEAD]
    V, F = torso_loft(rows, n=22, p=2.1, cap0=True, cap1=True)
    hd = M.Part(V, F, "BH_Skin", name="head")
    sb.add(hd, weights=HEAD_WF)
    # the head is sunk: a thick fold of neck fat rolls round it from the shoulders
    V, F = M.tube(hshift([(-0.1, 0.02, 1.575), (-0.06, -0.05, 1.555), (0.0, -0.075, 1.548), (0.06, -0.05, 1.555),
                          (0.1, 0.02, 1.575)]), [(0.03, 0.026)] * 5, n=8, up=(0, 0, 1))
    sb.add(M.Part(V, F, "BH_Skin", name="neckfold"), weights=lambda V: [{"chest": 0.6, "neck": 0.4}] * len(V))
    # heavy brow, deep sockets, tiny glowing eyes
    V, F = M.tube(hshift([(-0.065, -0.068, 1.715), (0.0, -0.082, 1.72), (0.065, -0.068, 1.715)]), [(0.018, 0.012)] * 3,
                  n=6, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Skin", name="brow"), weights=HEAD_WF)
    for sx in (1, -1):
        c = hshift([(sx * 0.03, -0.076, 1.695)])[0]
        V, F = M.sphere(0.015, 8, 5, center=c, scale=(1.2, 0.6, 0.85))
        sb.add(M.Part(V, F, "BH_Shadow", name="socket"), weights=HEAD_WF)
        V, F = M.sphere(0.0065, 6, 4, center=c + (0, -0.006, 0))
        sb.add(M.Part(V, F, "BH_Emissive", name="eye"), weights=HEAD_WF)
        V, F = M.sphere(0.02, 6, 4, center=hshift([(sx * 0.083, 0.0, 1.68)])[0], scale=(0.35, 0.8, 1.1))
        sb.add(M.Part(V, F, "BH_Skin", name="ear"), weights=HEAD_WF)
    V, F = M.sphere(0.02, 8, 5, center=hshift([(0, -0.09, 1.672)])[0], scale=(1.1, 0.8, 0.75))
    sb.add(M.Part(V, F, "BH_Skin", name="nose"), weights=HEAD_WF)
    # gaping maw: a big black hole ringed by swollen lips, crooked teeth top and bottom
    c = hshift([(0, -0.086, 1.604)])[0]
    V, F = M.sphere(0.05, 12, 6, center=c, scale=(0.95, 0.45, 1.0))
    sb.add(M.Part(V, F, "BH_Shadow", name="maw"), weights=HEAD_WF)
    ring = [hshift([(0.048 * math.cos(t), -0.092 + 0.012 * abs(math.cos(t)), 1.604 + 0.047 * math.sin(t))])[0]
            for t in np.linspace(0, 2 * math.pi, 17)]
    V, F = M.tube(ring, [(0.011, 0.01)] * len(ring), n=6, up=(0, -1, 0), cap0=False, cap1=False)
    sb.add(M.Part(V, F, "BH_Flesh", name="lips"), weights=HEAD_WF)
    for k, x in enumerate((-0.03, -0.01, 0.014, 0.033)):
        V, F = M.lathe([(0, 0), (0.0055, 0.002), (0.0, 0.018 + 0.007 * (k % 2))], 5)
        sb.add(M.Part(V, F, "BH_Bone", name="tooth").rot(Rx(180)).move(hshift([(x, -0.093, 1.646)])[0]),
               weights=HEAD_WF)
    for x in (-0.027, 0.0, 0.024):
        V, F = M.lathe([(0, 0), (0.0055, 0.002), (0.0, 0.016)], 5)
        sb.add(M.Part(V, F, "BH_Bone", name="tooth").move(hshift([(x, -0.093, 1.562)])[0]), weights=HEAD_WF)
    # a sac swelling on the scalp and a few pustules
    c = hshift([(0.04, 0.0, 1.785)])[0]
    V, F = M.sphere(0.03, 8, 5, center=c + (0, 0, 0.006), scale=(1.0, 1.0, 0.8))
    sb.add(M.Part(V, F, "BH_Emissive", name="scalp_sac"), weights=HEAD_WF)
    V, F = M.sphere(0.036, 10, 5, center=c - (0, 0, 0.004), scale=(1.0, 1.0, 0.45))
    sb.add(M.Part(V, F, "BH_Flesh", name="scalp_rim"), weights=HEAD_WF)
    for (x, y, z) in ((-0.05, -0.04, 1.75), (-0.07, 0.03, 1.72), (0.06, -0.05, 1.66)):
        V, F = M.sphere(0.011, 6, 4, center=hshift([(x, y, z)])[0])
        sb.add(M.Part(V, F, "BH_Flesh", name="pustule"), weights=HEAD_WF)


def seams(sb):
    """Crude stitched seams across the gut: a dark cut line with thick cross stitches."""
    rng = np.random.default_rng(3)
    for (z0, f0, z1, f1, k) in ((1.3, 0.93, 1.02, 0.1, 9), (1.22, 0.14, 1.08, 0.3, 5), (1.36, 0.6, 1.14, 0.52, 6)):
        pts, nrm = [], []
        for t in np.linspace(0, 1, 12):
            z = z0 + (z1 - z0) * t
            f = f0 + ((f1 - f0 + 0.5) % 1.0 - 0.5) * t
            q, n = surf(z, f % 1.0)
            pts.append(q + n * 0.002)
            nrm.append(n)
        sb.add(K.strip(pts, 0.013, 0.005, "BH_Shadow", ups=nrm), weights=TORSO_W)
        for i in np.linspace(0.5, 10.5, k):
            i0 = int(i)
            q = pts[i0] + (pts[i0 + 1] - pts[i0]) * (i - i0)
            n = nrm[i0]
            d = normalize(pts[i0 + 1] - pts[i0])
            c = normalize(np.cross(n, d))
            c = normalize(c + d * (rng.random() - 0.5) * 0.4)
            sb.add(K.rtube([q - c * 0.034 + n * 0.003, q + n * 0.009, q + c * 0.034 + n * 0.003], 0.0065,
                           "BH_Leather", n=4), weights=TORSO_W)


SACS = [   # (z, frac, radius) on the torso: big glowing plague sacs
    (1.12, 0.06, 0.085), (1.02, 0.9, 0.06), (1.26, 0.17, 0.055), (1.2, 0.84, 0.05), (0.97, 0.12, 0.04),
    (1.38, 0.38, 0.07), (1.24, 0.47, 0.08), (1.44, 0.58, 0.06), (1.1, 0.6, 0.05), (1.34, 0.72, 0.045),
    (1.5, 0.3, 0.05), (1.52, 0.7, 0.055),
]


def sac(sb, q, n, r, weights, seed=0, veins=True):
    """Glowing sac bulging out of a raw swollen patch, dark veins spreading out from it."""
    V, F = M.sphere(r, 12, 7, scale=(1.0, 1.0, 0.85))
    sb.add(oriented(V, F, "BH_Emissive", "sac", n, q + n * r * 0.45), weights=weights)
    V, F = M.sphere(r * 1.28, 14, 5, scale=(1.0, 1.0, 0.32))
    sb.add(oriented(V, F, "BH_Flesh", "sac_rim", n, q + n * r * 0.02), weights=weights)
    if not veins:
        return
    rng = np.random.default_rng(seed)
    t1 = normalize(np.cross(n, (0.3, 0.5, 0.8)))
    t2 = np.cross(n, t1)
    for k in range(4):
        a = 2 * math.pi * (k + rng.random() * 0.6) / 4
        d = t1 * math.cos(a) + t2 * math.sin(a)
        pts = []
        for i in range(4):
            u = r * (1.1 + 0.55 * i)
            w = (t1 * -math.sin(a) + t2 * math.cos(a)) * r * 0.25 * math.sin(i * 1.7 + seed)
            pts.append(q + d * u + w + n * (0.004 - 0.012 * (i / 3) ** 2 * r / 0.05))
        sb.add(K.rtube(pts, [0.0055, 0.0045, 0.0035, 0.002], "BH_Fur", n=4), weights=weights)


def sacs(sb):
    for i, (z, f, r) in enumerate(SACS):
        q, n = surf(z, f)
        sac(sb, q, n, r, TORSO_W, seed=i, veins=(r > 0.045))
    # a cluster of three sacs on the right shoulder top (reads from the high camera)
    for k, (dx, dy, dz, r) in enumerate(((0.0, 0.0, 0.05, 0.055), (0.05, 0.05, 0.03, 0.04), (-0.05, 0.04, 0.035,
                                                                                          0.035))):
        base = sb.head("upper_arm.R") + np.array([0.06 + dx, dy, dz])
        sac(sb, base, normalize(np.array([-0.4, 0.1, 1.0])), r, sb.seg(["chest", "shoulder.R"], power=6), seed=20 + k,
            veins=False)


def pustules(sb):
    rng = np.random.default_rng(17)
    for i in range(46):
        z = 0.82 + 0.72 * rng.random()
        f = rng.random()
        q, n = surf(z, f)
        r = 0.009 + 0.014 * rng.random()
        V, F = M.sphere(r, 6, 4, scale=(1.0, 1.0, 0.7))
        mat = "BH_Flesh" if i % 5 else "BH_Emissive"
        sb.add(oriented(V, F, mat, "pustule", n, q + n * r * 0.3), weights=TORSO_W)


def arms(sb):
    for s, sx in (("L", 1), ("R", -1)):
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        K.bare_arm(sb, s, r_up=0.07, r_fore=0.064, r_wrist=0.047, bulk=1.3)
        K.add_fist(sb, s, "BH_Skin", "BH_Skin", scale=1.35)
        sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
        # swollen shoulder mound
        V, F = M.sphere(0.1, 12, 6, center=sh + (sx * -0.01, 0.0, 0.045), scale=(1.0, 1.05, 0.7))
        sb.add(M.Part(V, F, "BH_Skin", name="deltoid"), weights=sb.seg(["chest", "shoulder." + s, ua], power=7))
        # nails
        A_ = sb.axes("weapon." + s)
        o = sb.head("weapon." + s)
        xs = 1.0 if s == "R" else -1.0
        for y in (-0.03, -0.01, 0.01, 0.03):
            b = o + A_ @ np.array([xs * 0.05, y, 0.0]) * 1.35
            V, F = M.sphere(0.008, 5, 3, center=b + A_ @ np.array([xs * 0.004, 0.0, -0.028]))
            sb.add(M.Part(V, F, "BH_Bone", name="nail"), ha)
        # pustules along the upper arm
        d = normalize(el - sh)
        side = normalize(np.cross(d, (0, 1, 0)))
        fw = np.cross(side, d)
        rng = np.random.default_rng(40 + sx)
        for k in range(6):
            u = 0.2 + 0.7 * rng.random()
            a = 2 * math.pi * rng.random()
            nrm = side * math.cos(a) + fw * math.sin(a)
            c = sh + (el - sh) * u + nrm * 0.075
            V, F = M.sphere(0.012 + 0.008 * rng.random(), 6, 4)
            sb.add(M.Part(V, F, "BH_Flesh" if k % 3 else "BH_Emissive", name="pustule").move(c), ua)
    # a filthy bandage round the left forearm, a sac bursting through the right forearm
    K.wrap_band(sb, "forearm.L", "hand.L", 0.15, 0.8, 0.068, "BH_Leather", turns=4, width=0.03, thick=0.008)
    el, wr = sb.head("forearm.R"), sb.head("hand.R")
    d = normalize(wr - el)
    nrm = normalize(np.cross(d, (0, 1, 0)))
    sac(sb, el + (wr - el) * 0.45 - nrm * 0.055, -nrm, 0.04, lambda V: [{"forearm.R": 1.0}] * len(V), veins=False)


def legs(sb):
    for s, sx in (("L", 1), ("R", -1)):
        th, sh = "thigh." + s, "shin." + s
        h, k, a = sb.head(th), sb.head(sh), sb.tail(sh)
        # thick bare legs (mostly hidden by rags and the gut)
        pts = [h + (0, 0, 0.06), h + (k - h) * 0.4, k + (0, 0, 0.02), k + (a - k) * 0.5, a + (0, 0, 0.04)]
        prof = [(0.14, 0.14), (0.125, 0.13), (0.1, 0.105), (0.09, 0.095), (0.07, 0.075)]
        V, F = M.tube(pts, prof, n=14, up=(0, -1, 0))
        sb.add(M.Part(V, F, "BH_Skin", name="leg"), weights=sb.seg(["hips", th, sh], power=10))
        # torn rag trousers to below the knee, ragged hem
        pts = [h + (0, 0, 0.07), h + (k - h) * 0.45, k + (0, 0, 0.02), k + (a - k) * 0.25]
        prof = [(0.17, 0.17), (0.155, 0.16), (0.12, 0.125), (0.114, 0.12)]
        V, F = M.tube(pts, prof, n=18, up=(0, -1, 0), cap0=False, cap1=False)
        tr = M.Part(V, F, "BH_Cloth_Primary", name="trouser")
        lo = k + (a - k) * 0.25
        tr.warp(lambda v, lo=lo: v - np.array([0, 0, 0.06]) * max(0, 1 - abs(v[2] - lo[2]) / 0.02) *
                (0.5 + 0.5 * math.sin(math.atan2(v[1], v[0] - lo[0]) * 5 + sx)))
        sb.add(M.solidify(tr, 0.007, offset=-1.0), weights=sb.seg(["hips", th, sh], power=10))
        # rag patch + a knee pustule showing through a tear
        c = k + np.array([0.0, -0.11, 0.06])
        V, F = M.sphere(0.035, 8, 5, center=c, scale=(1.0, 0.35, 1.2))
        sb.add(M.Part(V, F, "BH_Skin", name="tear"), th)
        V, F = M.sphere(0.017, 6, 4, center=c + (0, -0.012, 0))
        sb.add(M.Part(V, F, "BH_Emissive" if s == "L" else "BH_Flesh", name="pustule"), th)
        # shin wraps
        K.wrap_band(sb, sh, "foot." + s, 0.45, 0.92, 0.078, "BH_Leather", turns=3, width=0.028, thick=0.008, bone=sh)
        # wide bare feet
        hx = h[0]
        V, F = M.tube([(hx, 0.05, 0.085), (hx, 0.0, 0.055), (hx, -0.1, 0.038)],
                      [(0.06, 0.06), (0.07, 0.052), (0.066, 0.036)], n=10, up=(0, 0, 1))
        sb.add(M.Part(V, F, "BH_Skin", name="foot"), "foot." + s)
        V, F = M.tube([(hx, -0.1, 0.038), (hx, -0.17, 0.027), (hx, -0.205, 0.02)],
                      [(0.066, 0.036), (0.06, 0.027), (0.036, 0.016)], n=10, up=(0, 0, 1))
        sb.add(M.Part(V, F, "BH_Skin", name="toes"), "toe." + s)
        for x in (-0.035, -0.012, 0.012, 0.035):
            V, F = M.sphere(0.009, 5, 3, center=(hx + x, -0.21, 0.03))
            sb.add(M.Part(V, F, "BH_Bone", name="toenail"), "toe." + s)


def belt_and_rags(sb):
    """Rope belt under the overhang of the gut, rag loincloth front and back, a rag hanging off the rope."""
    rows = [(0.9, 0.2, 0.17, 0.13, 0.0, -0.03), (0.96, 0.215, 0.2, 0.14, 0.0, -0.04)]
    z = 0.935
    ring = K.ring_frac(rows, z, 0.012, np.linspace(0, 1, 33)[:-1], p=2.1)
    ring = np.vstack([ring, ring[:1]])
    V, F = M.tube(ring, [(0.016, 0.016)] * len(ring), n=6, up=(0, 0, 1), cap0=False, cap1=False)
    sb.add(M.Part(V, F, "BH_Leather", name="rope"), "hips")
    p, _ = K.on_ring(rows, z, 0.03, 0.88)
    V, F = M.sphere(0.03, 8, 5, center=p)
    sb.add(M.Part(V, F, "BH_Leather", name="knot"), "hips")
    for k in range(2):
        q = p + np.array([0.01 * k, -0.005, -0.02])
        sb.add(K.rtube([q, q + (0.005, -0.01, -0.08 - 0.03 * k), q + (0.012 * k, -0.012, -0.15 - 0.04 * k)], 0.01,
                       "BH_Leather", n=5), weights=sb.skirt(0.94, 0.7, max_leg=0.4, center_w=0.05))
    # loincloth panels hanging from the rope (front: under the gut; back: over the seat)
    for front in (True, False):
        sgn = -1 if front else 1
        nu, nv = 7, 7

        def fn(u, v, front=front, sgn=sgn):
            x = (u - 0.5) * (0.24 if front else 0.3) * (1 + 0.15 * v)
            zt = 0.93
            zb = 0.6 + 0.05 * math.sin(u * 11.0 + (0 if front else 2)) + (0.04 if abs(u - 0.5) > 0.35 else 0.0)
            zz = zt + (zb - zt) * v
            y0 = K.ring_frac(rows, zt, 0.02, [0.0 if front else 0.5], p=2.1)[0][1]
            y = y0 + sgn * 0.03 * v + 0.01 * math.sin(u * 9.0) * v
            return (x, y, zz)
        V, F = M.grid(fn, nu, nv)
        sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="loincloth"), 0.008, offset=1.0 if front else -1.0),
               weights=sb.skirt(0.94, 0.62, max_leg=0.45, center_w=0.16))
    # a rag tied round the right upper arm
    K.wrap_band(sb, "upper_arm.R", "forearm.R", 0.5, 0.75, 0.074, "BH_Cloth_Primary", turns=2, width=0.04,
                thick=0.008)


def cleaver_axe():
    """Rusty butcher's cleaver-axe (weapon space: grip at origin, +Z haft, blade on +X, flats +-Y)."""
    parts = []
    prof = [(0, -0.18), (0.024, -0.18), (0.026, -0.16), (0.02, -0.14), (0.019, 0.3), (0.021, 0.6), (0.017, 0.64),
            (0, 0.65)]
    V, F = M.lathe(prof, 10)
    parts.append(M.Part(V, F, "BH_Wood", name="haft"))
    import bh_weapons as WP
    parts.append(WP._grip(-0.13, 0.08, 0.021, 5, mat="BH_Leather"))
    # broad rectangular cleaver blade, slightly bellied edge, a chipped notch
    out = [(0.02, 0.62), (0.2, 0.64), (0.3, 0.6), (0.33, 0.5), (0.3, 0.38), (0.24, 0.34), (0.2, 0.36), (0.16, 0.345),
           (0.1, 0.38), (0.02, 0.4)]
    V, F = M.prism(M.resample_closed(out, 44)[::-1], 0.03, axis="y")
    bl = M.Part(V, F, "BH_Rust", name="cleaver")
    bl.warp(lambda v: (v[0], v[1] * (1.0 - 0.75 * min(max((v[0] - 0.08) / 0.25, 0), 1)), v[2]))
    parts.append(M.bevel(bl, 0.002, 1, angle=50))
    # rivets and a hanging hook on the back
    for (x, z) in ((0.06, 0.45), (0.06, 0.56)):
        for sy in (1, -1):
            V, F = M.sphere(0.011, 6, 4, center=(x, sy * 0.016, z))
            parts.append(M.Part(V, F, "BH_Wood", name="rivet"))
    V, F = M.lathe([(0, 0.36), (0.03, 0.36), (0.032, 0.4), (0.032, 0.63), (0.026, 0.66), (0.0, 0.67)], 10)
    parts.append(M.Part(V, F, "BH_Rust", name="socket"))
    V, F = M.tube([(-0.02, 0, 0.58), (-0.09, 0, 0.6), (-0.13, 0, 0.55), (-0.12, 0, 0.5)],
                  [(0.012, 0.012), (0.01, 0.01), (0.008, 0.008), (0.002, 0.002)], n=6, up=(0, 1, 0))
    parts.append(M.Part(V, F, "BH_Rust", name="hook"))
    # plague slime dripping from the edge
    for (x, z, ln) in ((0.3, 0.42, 0.07), (0.25, 0.36, 0.05)):
        parts.append(A.taper([(x, 0, z), (x + 0.005, 0, z - ln * 0.6), (x, 0, z - ln)], 0.009, 0.004, "BH_Emissive",
                             n=5))
    # rag wrapped under the head
    V, F = M.lathe([(0.0, 0.3), (0.028, 0.3), (0.03, 0.33), (0.028, 0.36), (0.0, 0.36)], 10)
    parts.append(M.Part(V, F, "BH_Cloth_Primary", name="rag"))
    return parts
