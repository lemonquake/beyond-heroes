"""Ghoul Brute (corrupted): huge hunched man bloated by grave-moss. Grey-green skin, barrel belly, a moss-grown hump on
the back and shoulders, the head thrust forward and low with tiny sickly-green eyes and an underbite, the right arm
swollen into a club of bone and flesh (rigid on weapon.R), torn trousers held by a rope belt with a cleaver, bare
feet. Kit: enemy_bandit_cutthroat."""
import math
import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K

SCALE = 1.2
PROPS = proportions(SCALE, shoulder_x=0.225 * SCALE, upper_len=0.3 * SCALE, fore_len=0.28 * SCALE,
                    hip_x=0.12 * SCALE, clav_drop=0.06 * SCALE)
PALETTE = "ghoul_brute"
PALETTE_COLORS = {
    "BH_Skin": ((0.25, 0.29, 0.21), 0.0, 0.5, None, 0.0, 1.0),               # grey-green skin
    "BH_Fur": ((0.05, 0.1, 0.028), 0.0, 0.95, None, 0.0, 1.0),               # grave-moss
    "BH_Flesh": ((0.3, 0.1, 0.09), 0.0, 0.45, None, 0.0, 1.0),               # raw swollen flesh
    "BH_Bone": ((0.5, 0.46, 0.35), 0.0, 0.6, None, 0.0, 1.0),                # bone spurs / teeth
    "BH_Cloth_Primary": ((0.13, 0.1, 0.07), 0.0, 0.92, None, 0.0, 1.0),      # torn trousers
    "BH_Leather": ((0.12, 0.1, 0.06), 0.0, 0.8, None, 0.0, 1.0),             # rope belt
    "BH_Rust": ((0.25, 0.13, 0.07), 0.45, 0.8, None, 0.0, 1.0),              # cleaver blade
    "BH_Wood": ((0.1, 0.07, 0.04), 0.0, 0.75, None, 0.0, 1.0),
    "BH_Shadow": ((0.03, 0.03, 0.02), 0.0, 0.8, None, 0.0, 1.0),             # mouth / sockets
    "BH_Emissive": ((0.5, 0.9, 0.3), 0.0, 0.4, (0.55, 1.0, 0.3), 5.0, 1.0),  # tiny green eyes
}
CLIPS = ["axe_2", "boss_slam", "boss_charge", "devour"]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


# (z, rx, ry_front, ry_back, keel, cy): belly low, hump high on the back, upper body shoved forward
TORSO = [
    (0.92, 0.18, 0.13, 0.13, 0.0, 0.0),
    (1.0, 0.195, 0.17, 0.13, 0.0, -0.02),
    (1.1, 0.205, 0.19, 0.135, 0.02, -0.035),
    (1.2, 0.21, 0.17, 0.16, 0.03, -0.04),
    (1.3, 0.235, 0.15, 0.22, 0.04, -0.04),
    (1.39, 0.25, 0.13, 0.25, 0.02, -0.04),
    (1.46, 0.235, 0.12, 0.265, 0.0, -0.03),
    (1.52, 0.2, 0.1, 0.255, 0.0, -0.01),
    (1.57, 0.15, 0.08, 0.2, 0.0, 0.02),
    (1.61, 0.09, 0.05, 0.14, 0.0, 0.05),
    (1.635, 0.03, 0.02, 0.06, 0.0, 0.07),
]
TORSO_W = K.zspec_w([(0.99, "hips"), (1.1, "spine"), (1.22, "spine"), (1.32, "chest")])
HEAD_DY, HEAD_DZ = -0.17, -0.15
HEAD = [
    (1.572, 0.03, 0.03, 0.03, 0.0, -0.075),
    (1.59, 0.07, 0.06, 0.05, 0.0, -0.06),     # heavy jaw
    (1.625, 0.085, 0.075, 0.07, 0.04, -0.035),
    (1.66, 0.088, 0.075, 0.085, 0.04, -0.02),
    (1.695, 0.085, 0.074, 0.092, 0.02, -0.012),
    (1.725, 0.086, 0.078, 0.092, 0.1, -0.008),
    (1.76, 0.078, 0.066, 0.088, 0.0, -0.0),
    (1.79, 0.058, 0.048, 0.07, 0.0, 0.004),
    (1.806, 0.03, 0.025, 0.04, 0.0, 0.006),
]


def hshift(pts):
    return np.asarray(pts, float) + np.array([0, HEAD_DY, HEAD_DZ])


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft(K.rows_between(TORSO, 0.92, 1.635, n_extra=6), n=40, p=2.2, cap0=True, cap1=True)
    sb.add(M.Part(V, F, "BH_Skin", name="torso"), weights=TORSO_W)
    # sagging pectorals / belly folds
    V, F = M.sphere(0.2, 12, 7, center=(0, front_y(TORSO, 0, 1.08) + 0.075, 1.07), scale=(0.95, 0.5, 0.65))
    sb.add(M.Part(V, F, "BH_Skin", name="belly"), weights=TORSO_W)
    # neck thrust forward + head
    V, F = M.tube([(0, 0.02, 1.42), (0, -0.06, 1.48), (0, -0.14, 1.5), (0, -0.19, 1.52)],
                  [(0.1, 0.1), (0.095, 0.095), (0.08, 0.08), (0.06, 0.06)], n=12, up=(0, 0, 1))
    sb.add(M.Part(V, F, "BH_Skin", name="neck"), weights=lambda V: [
        {"chest": 1.0} if v[1] > -0.04 else ({"neck": 1.0} if v[1] > -0.12 else {"neck": 0.5, "head": 0.5})
        for v in V])
    head(sb)
    moss(sb)
    # arms
    K.bare_arm(sb, "L", r_up=0.06, r_fore=0.052, r_wrist=0.04, bulk=1.25)
    K.add_fist(sb, "L", "BH_Skin", "BH_Skin", scale=1.3)
    claws(sb, "L")
    club_arm(sb)
    # legs: torn trousers, bare feet
    K.pelvis_seat(sb, "BH_Cloth_Primary", g=0.035)
    torn_trousers(sb)
    feet(sb)
    belt_and_cleaver(sb)


def head(sb):
    rows = [(r[0] + HEAD_DZ,) + r[1:5] + (r[5] + HEAD_DY,) for r in HEAD]
    V, F = torso_loft(rows, n=20, p=2.1, cap0=True, cap1=True)
    sb.add(M.Part(V, F, "BH_Skin", name="head"), "head")
    # heavy brow ridge
    V, F = M.tube(hshift([(-0.07, -0.07, 1.72), (0.0, -0.088, 1.726), (0.07, -0.07, 1.72)]), [(0.02, 0.014)] * 3, n=6,
                  up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Skin", name="brow"), "head")
    for sx in (1, -1):
        c = hshift([(sx * 0.032, -0.08, 1.7)])[0]
        V, F = M.sphere(0.014, 8, 5, center=c, scale=(1.2, 0.6, 0.8))
        sb.add(M.Part(V, F, "BH_Shadow", name="socket"), "head")
        V, F = M.sphere(0.0055, 6, 4, center=c + (0, -0.007, 0))
        sb.add(M.Part(V, F, "BH_Emissive", name="eye"), "head")
        # ear stubs
        V, F = M.sphere(0.022, 6, 4, center=hshift([(sx * 0.088, 0.0, 1.68)])[0], scale=(0.35, 0.8, 1.1))
        sb.add(M.Part(V, F, "BH_Skin", name="ear"), "head")
    # squashed nose
    V, F = M.sphere(0.022, 8, 5, center=hshift([(0, -0.094, 1.672)])[0], scale=(1.1, 0.8, 0.8))
    sb.add(M.Part(V, F, "BH_Skin", name="nose"), "head")
    # gaping mouth with an underbite (lower teeth jut up)
    c = hshift([(0, -0.086, 1.625)])[0]
    V, F = M.sphere(0.04, 10, 5, center=c, scale=(1.1, 0.35, 0.45))
    sb.add(M.Part(V, F, "BH_Shadow", name="mouth"), "head")
    for k, x in enumerate((-0.03, -0.012, 0.012, 0.03)):
        h = 0.022 if k in (0, 3) else 0.013
        V, F = M.lathe([(0, 0), (0.006, 0.002), (0.0, h)], 5)
        sb.add(M.Part(V, F, "BH_Bone", name="tusk").move(hshift([(x, -0.098, 1.607)])[0]), "head")
    # patchy hair tufts
    for (x, y, z) in ((0.04, 0.03, 1.79), (-0.05, 0.05, 1.77), (0.0, 0.07, 1.76)):
        V, F = M.sphere(0.025, 6, 4, center=hshift([(x, y, z)])[0], scale=(1.0, 1.0, 0.45))
        sb.add(M.Part(V, F, "BH_Fur", name="tuft"), "head")


def moss(sb):
    """Grave-moss clumps over the hump, shoulders and the back of the neck (lumpy flattened blobs)."""
    rng = np.random.default_rng(11)
    spots = []
    for i in range(34):
        f = 0.3 + 0.4 * rng.random()          # back half
        z = 1.2 + 0.4 * rng.random()
        spots.append((f, z, 0.05 + 0.035 * rng.random()))
    for sx in (1, -1):                         # shoulder tops
        for k in range(3):
            spots.append((0.25 + sx * 0.0 + (0.2 if sx < 0 else 0.0) + (0.5 if sx < 0 else 0) * 0 + 0.0, 0, 0))
    out = []
    for f, z, r in spots:
        if r == 0:
            continue
        q = K.ring_frac(TORSO, z, 0.0, [f], p=2.2)[0]
        a = 2 * math.pi * f - math.pi / 2
        nrm = np.array([math.cos(a), math.sin(a), 0.3])
        V, F = M.sphere(r, 12, 7, center=(0, 0, 0), scale=(1.0, 1.0, 0.45))
        blob = M.Part(V, F, "BH_Fur", name="moss")
        from bh_body import M_align_z
        blob.rot(M_align_z(normalize(nrm))).move(q + normalize(nrm) * r * 0.15)
        out.append(blob)
    for p in out:
        sb.add(p, weights=TORSO_W)
    for s, sx in (("L", 1), ("R", -1)):
        sh = sb.head("upper_arm." + s)
        for k, (dx, dy, dz, r) in enumerate(((-0.02, 0.03, 0.06, 0.07), (0.04, 0.0, 0.04, 0.055),
                                            (-0.07, 0.06, 0.07, 0.06))):
            V, F = M.sphere(r, 8, 5, center=sh + (sx * dx, dy, dz), scale=(1.0, 1.1, 0.5))
            sb.add(M.Part(V, F, "BH_Fur", name="moss_sh"), weights=sb.seg(["chest", "shoulder." + s], power=6))
    # moss drape down the back of the neck
    V, F = M.sphere(0.1, 10, 6, center=(0, 0.08, 1.63), scale=(1.2, 0.9, 0.45))
    sb.add(M.Part(V, F, "BH_Fur", name="moss_neck"), "chest")
    # a few pale fungus caps on the hump
    for (x, z) in ((0.08, 1.42), (-0.1, 1.36), (0.02, 1.3)):
        yb = back_y(TORSO, x, z)
        V, F = M.lathe([(0, 0), (0.018, 0.004), (0.02, 0.012), (0.0, 0.02)], 8)
        cap = M.Part(V, F, "BH_Bone", name="fungus").rot(Rx(-70)).move((x, yb + 0.03, z))
        sb.add(cap, "chest")


def claws(sb, s):
    A = sb.axes("weapon." + s)
    o = sb.head("weapon." + s)
    xs = 1.0 if s == "R" else -1.0
    for y in (-0.03, -0.01, 0.01, 0.03):
        base = o + A @ np.array([xs * 0.045, y, 0.0]) * 1.3
        tip = base + A @ np.array([xs * 0.01, 0.0, -0.035])
        V, F = M.tube([base, tip], [(0.006, 0.006), (0.001, 0.001)], n=5, up=A[:, 1])
        sb.add(M.Part(V, F, "BH_Bone", name="claw"), "hand." + s)


def club_arm(sb):
    """Right arm: thick upper arm, the forearm swelling into a lumpy club of flesh and bone that swallows the hand."""
    s = "R"
    ua, fa, ha = "upper_arm.R", "forearm.R", "hand.R"
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    pts = [sh + (0.05, 0, 0.02), sh, sh + (el - sh) * 0.3, sh + (el - sh) * 0.7, el, el + (wr - el) * 0.35,
           el + (wr - el) * 0.75, wr]
    prof = [(0.06, 0.065), (0.085, 0.09), (0.085, 0.09), (0.08, 0.085), (0.08, 0.085), (0.09, 0.095), (0.1, 0.105),
            (0.1, 0.105)]
    V, F = M.tube(pts, prof, n=14, up=(0, -1, 0))
    arm = M.Part(V, F, "BH_Skin", name="arm")
    sb.add(arm, weights=sb.seg(["chest", "shoulder.R", ua, fa, ha], power=9))
    # veins / raw flesh splits on the forearm
    d = normalize(wr - el)
    side = normalize(np.cross(d, (0, 1, 0)))
    fw = np.cross(side, d)
    for k, ang in enumerate((20, 140, 250)):
        a = math.radians(ang)
        nrm = side * math.cos(a) + fw * math.sin(a)
        pl = [el + (wr - el) * u + nrm * (0.088 + 0.012 * u) for u in (0.3, 0.6, 0.95)]
        sb.add(K.rtube(pl, [0.012, 0.018, 0.012], "BH_Flesh", n=5), fa)
    # the club itself (weapon space: +X distal / knuckles, +Z = thumb-forward, flats +-Y)
    parts = []
    prof = [(0.0, -0.09), (0.1, -0.07), (0.115, 0.0), (0.13, 0.12), (0.145, 0.24), (0.125, 0.33), (0.07, 0.39),
            (0.0, 0.41)]
    V, F = M.lathe(prof, 18)
    club = M.Part(V, F, "BH_Flesh", name="club")
    rng = np.random.default_rng(5)
    club.warp(lambda v: v * (1 + 0.1 * math.sin(v[2] * 31 + math.atan2(v[1], v[0]) * 3)))
    club.rot(Ry(90)).rot(Rz(0)).move((0.0, 0, 0.0))
    # tilt slightly toward the thumb side so it reads as a bludgeon
    club.rot(Ry(-18))
    parts.append(club)
    # skin sleeve over the root of the club
    V, F = M.lathe([(0.0, -0.1), (0.108, -0.09), (0.12, 0.02), (0.128, 0.1), (0.0, 0.11)], 12)
    parts.append(M.Part(V, F, "BH_Skin", name="club_skin").rot(Ry(90)).rot(Ry(-18)))
    # bone spurs bursting out of the flesh
    for k in range(9):
        u = 0.08 + 0.3 * rng.random()
        a = 2 * math.pi * rng.random()
        base = np.array([u, 0.12 * math.cos(a), 0.12 * math.sin(a)])
        out = normalize(np.array([0.5 + 0.4 * rng.random(), math.cos(a), math.sin(a)]))
        ln = 0.07 + 0.07 * rng.random()
        V, F = M.tube([base - out * 0.02, base + out * ln * 0.6, base + out * ln], [(0.022, 0.022), (0.012, 0.012),
                      (0.002, 0.002)], n=6, up=(0, 0, 1) if abs(out[2]) < 0.9 else (1, 0, 0))
        sp = M.Part(V, F, "BH_Bone", name="spur")
        sp.rot(Ry(-18))
        parts.append(sp)
    # knuckle-bone ridge at the end
    for y in (-0.05, 0.0, 0.05):
        V, F = M.sphere(0.035, 8, 5, center=(0.39, y, 0.02), scale=(0.8, 0.9, 1.0))
        parts.append(M.Part(V, F, "BH_Bone", name="knuckle").rot(Ry(-18)))
    K.add_weapon(sb, "R", parts)


def torn_trousers(sb):
    for s in ("L", "R"):
        th, sh = "thigh." + s, "shin." + s
        h, k, a = sb.head(th), sb.head(sh), sb.tail(sh)
        pts = [h + (0, 0, 0.05), h + (k - h) * 0.45, k + (0, 0, 0.02), k + (a - k) * 0.3]
        prof = [(0.12, 0.125), (0.1, 0.105), (0.08, 0.085), (0.078, 0.082)]
        V, F = M.tube(pts, prof, n=18, up=(0, -1, 0), cap1=False)
        tr = M.Part(V, F, "BH_Cloth_Primary", name="trouser")
        # ragged hem: pull alternate hem vertices down
        lo = k + (a - k) * 0.3
        tr.warp(lambda v, lo=lo: v - np.array([0, 0, 0.05]) * max(0, 1 - abs(v[2] - lo[2]) / 0.02) *
                (0.5 + 0.5 * math.sin(math.atan2(v[1], v[0] - lo[0]) * 5)))
        sb.add(M.solidify(tr, 0.006, offset=-1.0), weights=sb.seg([th, sh], power=10))
        # bare skin shin below
        V, F = M.tube([k + (a - k) * 0.2, k + (a - k) * 0.6, a + (0, 0, 0.03)], [(0.07, 0.075), (0.06, 0.065),
                      (0.05, 0.055)], n=12, up=(0, -1, 0))
        sb.add(M.Part(V, F, "BH_Skin", name="shin"), sh)
        # tear showing flesh on the left thigh
        if s == "L":
            c = h + (k - h) * 0.55 + np.array([0.02, -0.1, 0])
            V, F = M.sphere(0.04, 8, 5, center=c, scale=(0.8, 0.3, 1.2))
            sb.add(M.Part(V, F, "BH_Skin", name="tear"), th)


def feet(sb):
    for s in ("L", "R"):
        hx = sb.head("thigh." + s)[0]
        V, F = M.tube([(hx, 0.05, 0.08), (hx, 0.0, 0.05), (hx, -0.1, 0.035)], [(0.05, 0.05), (0.058, 0.045),
                      (0.056, 0.032)], n=10, up=(0, 0, 1))
        sb.add(M.Part(V, F, "BH_Skin", name="foot"), "foot." + s)
        V, F = M.tube([(hx, -0.1, 0.035), (hx, -0.17, 0.025), (hx, -0.2, 0.02)], [(0.056, 0.032), (0.05, 0.025),
                      (0.03, 0.015)], n=10, up=(0, 0, 1))
        sb.add(M.Part(V, F, "BH_Skin", name="toes"), "toe." + s)
        for x in (-0.03, 0.0, 0.03):
            V, F = M.sphere(0.009, 5, 3, center=(hx + x, -0.205, 0.028))
            sb.add(M.Part(V, F, "BH_Bone", name="toenail"), "toe." + s)


def belt_and_cleaver(sb):
    z = 0.99
    g = 0.045
    ring = K.ring_frac(TORSO, z, g, np.linspace(0, 1, 29)[:-1], p=2.2)
    ring = np.vstack([ring, ring[:1]])
    V, F = M.tube(ring, [(0.014, 0.014)] * len(ring), n=6, up=(0, 0, 1), cap0=False, cap1=False)
    sb.add(M.Part(V, F, "BH_Leather", name="rope"), "hips")
    p, _ = K.on_ring(TORSO, z, g + 0.01, 0.9)
    V, F = M.sphere(0.028, 8, 5, center=p)
    sb.add(M.Part(V, F, "BH_Leather", name="knot"), "hips")
    # cleaver tucked in the rope on the left hip, blade hanging down
    q, ang = K.on_ring(TORSO, z, g + 0.03, 0.2)
    parts = []
    V, F = M.box(0.012, 0.2, 0.024)       # handle (along Y before orientation -> vertical after)
    parts.append(M.Part(V, F, "BH_Wood", name="handle").rot(Rx(90)).move((0, 0, 0.1)))
    outline = [(-0.06, 0.0), (0.075, 0.0), (0.08, -0.2), (-0.05, -0.23)]
    V, F = M.prism(outline, 0.008, axis="x")
    parts.append(M.Part(V, F, "BH_Rust", name="cleaver"))
    for prt in parts:
        prt.rot(Rz(ang)).rot(Ry(0)).move(q + (0, 0, -0.02))
        sb.add(prt, weights=sb.skirt(1.0, 0.7, max_leg=0.3, center_w=0.05))
