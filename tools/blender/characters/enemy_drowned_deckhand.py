"""Drowned Deckhand (bh-012, Builder A; Saltmouth Deeps melee grunt): a bloated, grey-blue drowned sailor. Torn,
waterlogged striped shirt (pale / navy bands, a rip over the belly, short torn sleeves), ragged sodden trousers cut off
at the shin, a rope belt with a rusted knife tucked at the left hip, barnacle clusters crusting the left shoulder, the
right forearm and the left shin, kelp strands hanging from both shoulders and the lank hair, a swollen face with a
slack, gaping jaw and faint teal glowing eyes, bare swollen feet. Weapon: a long rusted boat-hook (~2.3 m pole with an
iron spike and a back-curving hook at the tip, barnacles and a kelp tatter on the head) held like a spear (spear
clips; rigid on weapon.R). ~1.8 m. Kit: enemy_bandit_cutthroat (standard-space authoring) + kit_deeps."""
import math
import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C
import enemy_hollow_soldier as HS
import kit_a_common as A
import kit_deeps as D

SCALE = 1.8 / 1.83
PROPS = proportions(SCALE, shoulder_x=0.198 * SCALE, hip_x=0.105 * SCALE)
PALETTE = "drowned_deckhand"
PALETTE_COLORS = {
    "BH_Skin": ((0.28, 0.35, 0.38), 0.0, 0.42, None, 0.0, 1.0),             # drowned grey-blue, wet sheen
    "BH_Flesh": ((0.2, 0.2, 0.24), 0.0, 0.4, None, 0.0, 1.0),               # swollen lips / gums
    "BH_Cloth_Primary": ((0.46, 0.49, 0.47), 0.0, 0.85, None, 0.0, 1.0),    # faded waterlogged stripe
    "BH_Cloth_Secondary": ((0.05, 0.085, 0.13), 0.0, 0.85, None, 0.0, 1.0), # navy stripe
    "BH_Leather": ((0.11, 0.12, 0.11), 0.0, 0.88, None, 0.0, 1.0),          # sodden grey canvas trousers
    "BH_Horn": ((0.3, 0.27, 0.19), 0.0, 0.9, None, 0.0, 1.0),               # hemp rope
    "BH_Wood": ((0.15, 0.13, 0.1), 0.0, 0.75, None, 0.0, 1.0),              # sodden pole
    "BH_Rust": ((0.3, 0.155, 0.075), 0.4, 0.82, None, 0.0, 1.0),            # hook, knife, bands
    "BH_Hair": ((0.03, 0.04, 0.035), 0.0, 0.5, None, 0.0, 1.0),             # lank wet hair
    "BH_Fur": ((0.07, 0.17, 0.075), 0.0, 0.55, None, 0.0, 1.0),             # kelp
    "BH_Bone": ((0.7, 0.7, 0.64), 0.0, 0.85, None, 0.0, 1.0),               # barnacle shells
    "BH_Stone": ((0.3, 0.34, 0.32), 0.0, 0.9, None, 0.0, 1.0),              # crust under the barnacles
    "BH_Shadow": ((0.015, 0.025, 0.03), 0.0, 0.8, None, 0.0, 1.0),          # mouth / sockets / apertures
    "BH_Emissive": D.TEAL,                                                  # faint teal eyes
}
CLIPS = ["spear_1", "spear_2", "spear_heavy"]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


# bloated torso: wider, pot belly, rounded back
TORSO = [(r[0], r[1] * 1.1 + 0.006, r[2] * (1.12 + 0.2 * math.exp(-((r[0] - 1.12) / 0.1) ** 2)), r[3] * 1.07,
          r[4] * 0.3) for r in K.TORSO]
TW = K.TORSO_W
G = 0.012

# swollen head with a dropped, slack jaw (z, rx, ryf, ryb, keel, cy)
HEAD = [
    (1.563, 0.026, 0.024, 0.02, 0.0, -0.058),
    (1.583, 0.056, 0.05, 0.042, 0.0, -0.048),
    (1.612, 0.076, 0.066, 0.062, 0.03, -0.03),
    (1.648, 0.084, 0.072, 0.08, 0.04, -0.016),
    (1.69, 0.083, 0.072, 0.09, 0.02, -0.01),
    (1.722, 0.081, 0.072, 0.093, 0.06, -0.006),
    (1.76, 0.078, 0.067, 0.092, 0.0, -0.002),
    (1.795, 0.064, 0.053, 0.078, 0.0, 0.003),
    (1.82, 0.036, 0.03, 0.048, 0.0, 0.006),
]


def hfront(z, x=0.0):
    return front_y(HEAD, x, z, p=2.1)


def build(body):
    sb = K.SB(body, SCALE)
    # ---- body under the shirt (skin shows through the rip)
    V, F = torso_loft(K.rows_between(TORSO, 0.96, 1.53, n_extra=3), n=26, cap1=True)
    sb.add(M.Part(V, F, "BH_Skin", name="torso"), weights=TW)
    shirt(sb)
    # ---- head
    head(sb)
    # ---- arms: bloated bare arms, striped short sleeves
    for s in ("L", "R"):
        K.bare_arm(sb, s, r_up=0.056, r_fore=0.05, r_wrist=0.037, bulk=1.06)
        K.add_fist(sb, s, "BH_Skin", "BH_Skin", scale=1.06)
        sleeve(sb, s)
    # ---- legs
    K.pelvis_seat(sb, "BH_Leather", g=0.02)
    trousers(sb)
    feet(sb)
    belt_and_knife(sb)
    # ---- sea growth
    barnacles(sb)
    kelp(sb)
    # ---- weapon
    K.add_weapon(sb, "R", boat_hook())


# ================================================================================================= clothes
def shirt(sb):
    """Striped shirt as alternating horizontal bands (own material each); ripped open over the belly (front-left),
    ragged hem, open collar."""
    zs = [0.985, 1.04, 1.09, 1.14, 1.19, 1.24, 1.29, 1.34, 1.39, 1.44, 1.49, 1.515]
    nu = 30
    for i, (z0, z1) in enumerate(zip(zs, zs[1:])):
        mat = "BH_Cloth_Primary" if i % 2 == 0 else "BH_Cloth_Secondary"
        t0 = (z0 - 0.985) / 0.53
        t1 = (z1 - 0.985) / 0.53
        # rip over the belly: the front-left bands 1..3 leave a gap
        if 1 <= i <= 3:
            a, b = 0.045 + 0.02 * (i == 2), 0.97 - 0.035 * (i == 2)
        elif i >= 9:
            a, b = 0.035, 0.965              # open collar
        else:
            a, b = 0.0, 1.0
        fr = a + (b - a) * np.linspace(0, 1, nu)
        closed = (a == 0.0)
        if closed:
            fr = np.linspace(0, 1, nu, endpoint=False)
        r0 = K.ring_frac(TORSO, max(z0, 0.96), G + 0.006 * (1 - t0), fr)
        r1 = K.ring_frac(TORSO, z1, G + 0.006 * (1 - t1), fr)
        if i == 0:     # ragged hem
            for j in range(len(r0)):
                r0[j, 2] -= HS.ragged(fr[j] % 1.0, 2.2, 0.06, 5)
        V, F = M.loft([r0, r1], cap0=False, cap1=False, closed=closed)
        sb.add(M.solidify(M.Part(V, F, mat, name="shirt"), 0.006, offset=1.0), weights=TW)
    # torn flaps hanging off the rip edges
    for frac, z, ln in ((0.05, 1.12, 0.07), (0.965, 1.1, 0.09)):
        p, ang = K.on_ring(TORSO, z, G + 0.008, frac)
        out = normalize(np.array([p[0], p[1] + 0.02, 0.0]))
        for prt in [A.rag_strip(p, (0.1 * np.sign(p[0] + 1e-6), -0.25, -1.0), ln, 0.04, "BH_Cloth_Primary", out=out,
                                seed=frac * 7)]:
            sb.add(prt, weights=TW)
    # collar band
    ring = K.ring_frac(TORSO, 1.515, G + 0.003, np.linspace(0.035, 0.965, 20))
    sb.add(K.rtube(ring, 0.009, "BH_Cloth_Secondary", n=5), "chest")


def sleeve(sb, s):
    ua, fa = "upper_arm." + s, "forearm." + s
    sh, el = sb.head(ua), sb.head(fa)
    sx = 1 if s == "L" else -1
    w = sb.seg(["chest", "shoulder." + s, ua, fa], power=9)
    bands = [(sh + (-0.045 * sx, 0, 0.03), sh, (0.066, 0.07), (0.07, 0.074), "BH_Cloth_Primary"),
             (sh, sh + (el - sh) * 0.28, (0.07, 0.074), (0.068, 0.072), "BH_Cloth_Secondary"),
             (sh + (el - sh) * 0.28, sh + (el - sh) * 0.5, (0.068, 0.072), (0.07, 0.074), "BH_Cloth_Primary")]
    for k, (a, b, p0, p1, mat) in enumerate(bands):
        V, F = M.tube([a, b], [p0, p1], n=14, up=(0, -1, 0), cap0=False, cap1=False)
        prt = M.Part(V, F, mat, name="sleeve")
        if k == 2:     # ragged end
            e = b
            d = normalize(el - sh)
            prt.warp(lambda v, e=e, d=d: v + d * (0.03 * max(0.0, 1 - abs(np.dot(v - e, d)) / 0.01) *
                                                  (0.5 + 0.5 * math.sin(7 * math.atan2(v[1] - e[1], v[0] - e[0])))))
        sb.add(M.solidify(prt, 0.006, offset=-1.0), weights=w)


def trousers(sb):
    for s in ("L", "R"):
        th, sh = "thigh." + s, "shin." + s
        h, k, a = sb.head(th), sb.head(sh), sb.tail(sh)
        lo = k + (a - k) * 0.42
        pts = [h + (0, 0, 0.05), h + (k - h) * 0.45, k + (0, 0, 0.02), lo]
        prof = [(0.092, 0.096), (0.08, 0.084), (0.066, 0.07), (0.066, 0.07)]
        V, F = M.tube(pts, prof, n=16, up=(0, -1, 0), cap1=False)
        tr = M.Part(V, F, "BH_Leather", name="trouser")
        seed = 1.3 if s == "L" else 4.1
        tr.warp(lambda v, lo=lo, seed=seed: v - np.array([0, 0, 1.0]) * 0.06 * max(0.0, 1 - abs(v[2] - lo[2]) / 0.03)
                * HS.ragged((math.atan2(v[1] - lo[1], v[0] - lo[0]) / (2 * math.pi)) % 1.0, seed, 1.0, 4))
        sb.add(M.solidify(tr, 0.006, offset=-1.0), weights=sb.seg([th, sh], power=10))
        # bare swollen shins below
        V, F = M.tube([k + (a - k) * 0.25, k + (a - k) * 0.65, a + (0, 0, 0.03)], [(0.056, 0.06), (0.05, 0.054),
                      (0.042, 0.046)], n=12, up=(0, -1, 0))
        sb.add(M.Part(V, F, "BH_Skin", name="shin"), sh)
        # a torn flap hanging from the hem
        q = lo + np.array([0.03 if s == "L" else -0.03, -0.055, -0.01])
        sb.add(A.rag_strip(q, (0, -0.15, -1), 0.08, 0.04, "BH_Leather", out=(0, -1, 0), seed=seed), sh)


def feet(sb):
    for s in ("L", "R"):
        hx = sb.head("thigh." + s)[0]
        V, F = M.tube([(hx, 0.05, 0.075), (hx, 0.0, 0.045), (hx, -0.09, 0.032)], [(0.046, 0.046), (0.052, 0.04),
                      (0.05, 0.03)], n=10, up=(0, 0, 1))
        sb.add(M.Part(V, F, "BH_Skin", name="foot"), "foot." + s)
        V, F = M.tube([(hx, -0.09, 0.032), (hx, -0.16, 0.024), (hx, -0.19, 0.018)], [(0.05, 0.03), (0.046, 0.022),
                      (0.028, 0.013)], n=10, up=(0, 0, 1))
        sb.add(M.Part(V, F, "BH_Skin", name="toes"), "toe." + s)
        for x in (-0.026, 0.0, 0.026):
            V, F = M.sphere(0.008, 5, 3, center=(hx + x, -0.193, 0.024))
            sb.add(M.Part(V, F, "BH_Flesh", name="toenail"), "toe." + s)


def belt_and_knife(sb):
    C.rope_belt(sb, z=1.0, g=G + 0.022, mat="BH_Horn", knot_frac=0.88, tails=0.2, rows=TORSO)
    # rusted knife tucked through the rope on the left hip, blade down
    q, ang = K.on_ring(TORSO, 1.0, G + 0.04, 0.17)
    w = sb.skirt(1.02, 0.72, max_leg=0.35, center_w=0.05)
    for prt in K.curved_knife(length=0.24, width=0.036, curve=0.03, mat="BH_Rust", grip_mat="BH_Wood"):
        prt.rot(Rx(180)).rot(Rz(ang + 90)).move(q + (0, 0, 0.1))
        sb.add(prt, weights=w)


# ================================================================================================= head
def head(sb):
    V, F = M.tube([(0, 0.0, 1.45), (0, -0.006, 1.53), (0, -0.012, 1.6)], [(0.066, 0.062), (0.06, 0.058),
                  (0.058, 0.056)], n=12, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Skin", name="neck"), weights=K.HEAD_W)
    V, F = torso_loft(HEAD, n=24, p=2.1, cap0=True, cap1=True)
    hd = M.Part(V, F, "BH_Skin", name="head")
    # puffy, lopsided swelling (left cheek)
    HS.dent(hd, (0.06, -0.06, 1.64), (0.6, -0.4, 0), -0.012, 0.035)
    sb.add(hd, "head")
    # heavy brow, bloated nose
    V, F = M.tube([(-0.055, hfront(1.726, -0.055) + 0.004, 1.724), (0.0, hfront(1.728) - 0.004, 1.73),
                   (0.055, hfront(1.726, 0.055) + 0.004, 1.724)], [(0.014, 0.01)] * 3, n=6, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Skin", name="brow"), "head")
    V, F = M.sphere(0.02, 8, 5, center=(0, hfront(1.68) - 0.012, 1.672), scale=(1.1, 0.9, 1.1))
    sb.add(M.Part(V, F, "BH_Skin", name="nose"), "head")
    # sunken sockets with faint teal eyes (a little oversized so they read at distance)
    for sx in (1, -1):
        c = np.array([sx * 0.032, hfront(1.703, sx * 0.032) + 0.006, 1.703])
        V, F = M.sphere(0.017, 8, 5, center=c, scale=(1.15, 0.6, 0.78))
        sb.add(M.Part(V, F, "BH_Shadow", name="socket"), "head")
        V, F = M.sphere(0.0085, 6, 4, center=c + (0, -0.006, 0), scale=(1.2, 0.7, 0.9))
        sb.add(M.Part(V, F, "BH_Emissive", name="eye"), "head")
        # puffy lower lids
        V, F = M.tube([c + (-0.014, -0.003, -0.012), c + (0, -0.006, -0.016), c + (0.014, -0.003, -0.012)],
                      [(0.006, 0.005)] * 3, n=5, up=(0, -1, 0))
        sb.add(M.Part(V, F, "BH_Flesh", name="lid"), "head")
        V, F = M.sphere(0.022, 6, 4, center=(sx * 0.082, 0.0, 1.69), scale=(0.35, 0.8, 1.2))
        sb.add(M.Part(V, F, "BH_Skin", name="ear"), "head")
    # slack, gaping mouth: dark hole, swollen lips, dropped lower lip
    zc = 1.612
    V, F = M.sphere(0.036, 10, 6, center=(0, hfront(zc) + 0.008, zc), scale=(0.95, 0.45, 0.85))
    sb.add(M.Part(V, F, "BH_Shadow", name="mouth"), "head")
    up = [(x, hfront(zc + 0.028, x) - 0.002, zc + 0.028 - 0.01 * (abs(x) / 0.034) ** 2) for x in np.linspace(-0.034, 0.034, 5)]
    sb.add(K.rtube(up, 0.008, "BH_Flesh", n=5), "head")
    lo = [(x, hfront(zc - 0.03, x) - 0.004, zc - 0.03 + 0.012 * (abs(x) / 0.03) ** 2) for x in np.linspace(-0.03, 0.03, 5)]
    sb.add(K.rtube(lo, 0.009, "BH_Flesh", n=5), "head")
    for x in (-0.018, 0.0, 0.017):        # a few crooked teeth
        V, F = M.box(0.008, 0.006, 0.012, center=(x, hfront(zc + 0.02) + 0.004, zc + 0.014))
        sb.add(M.Part(V, F, "BH_Bone", name="tooth").rot(Ry(12 * x / 0.02), center=(x, 0, zc)), "head")
    # lank thinning hair + wet strands down the back
    K.hair_cap(sb, mat="BH_Hair", g=0.013, z_front=1.765, z_back=1.64, messy=0.008)
    rng = np.random.default_rng(3)
    for k in range(9):
        a = math.radians(-70 + 140 * k / 8)
        top = np.array([0.075 * math.sin(a), 0.03 + 0.07 * math.cos(a), 1.77 - 0.03 * abs(math.sin(a))])
        d = normalize(np.array([math.sin(a) * 0.35, 0.3 + 0.2 * math.cos(a), -1.0]))
        ln = 0.14 + 0.06 * rng.random()
        pts = [top, top + d * ln * 0.4 + (0, 0.02, 0), top + d * ln]
        sb.add(A.taper(pts, 0.011, 0.003, "BH_Hair", n=4), weights=K.HEAD_W)


# ================================================================================================= sea growth
def barnacles(sb):
    # left shoulder / deltoid
    sh = sb.head("upper_arm.L")
    w = sb.seg(["chest", "shoulder.L", "upper_arm.L", "forearm.L"], power=9)
    for prt in D.barnacle_cluster(sh + (0.03, 0.0, 0.058), (0.55, -0.05, 0.85), 0.07, count=12, seed=4, rmin=0.011,
                                  rmax=0.024, crust=True):
        sb.add(prt, weights=w)
    for prt in D.barnacle_cluster(sh + (0.07, -0.01, -0.03), (1.0, -0.1, 0.1), 0.045, count=6, seed=5, rmin=0.01,
                                  rmax=0.02, crust=True):
        sb.add(prt, weights=w)
    # right forearm (outer side)
    el, wr = sb.head("forearm.R"), sb.head("hand.R")
    d = normalize(wr - el)
    out = normalize(np.array([-1.0, 0.25, 0.0]) - d * np.dot(np.array([-1.0, 0.25, 0.0]), d))
    for u, r, sd in ((0.35, 0.05, 11), (0.7, 0.035, 12)):
        for prt in D.barnacle_cluster(el + (wr - el) * u + out * 0.05, out, r, count=7 if r > 0.04 else 4, seed=sd,
                                      rmin=0.009, rmax=0.019, crust=True):
            sb.add(prt, "forearm.R")
    # left shin (front)
    k, a = sb.head("shin.L"), sb.tail("shin.L")
    for prt in D.barnacle_cluster(k + (a - k) * 0.62 + np.array([0.012, -0.05, 0.0]), (0.2, -1, 0.0), 0.045, count=7,
                                  seed=21, rmin=0.009, rmax=0.018, crust=True):
        sb.add(prt, "shin.L")


def kelp(sb):
    """Kelp strands draped over the shoulders (front + back) and tangled in the hair."""
    rng = np.random.default_rng(8)
    for s, sx in (("L", 1), ("R", -1)):
        base = np.array([sx * 0.13, 0.0, 1.49])
        for k, (dy, ln, fw) in enumerate(((-0.07, 0.3, True), (-0.03, 0.22, True), (0.06, 0.34, False),
                                          (0.09, 0.26, False))):
            top = base + np.array([sx * 0.02 * k, dy, 0.012])
            down = np.array([sx * 0.05, -0.2 if fw else 0.25, -1.0])
            outn = (0, -1, 0.2) if fw else (0, 1, 0.2)
            for prt in D.kelp(top, down, ln, 0.03, "BH_Fur", out=outn, amp=0.018, seed=rng.random() * 6,
                              bladders="BH_Fur" if k == 2 else None):
                sb.add(prt, "chest")
        # strap of weed across the top of the shoulder
        pts = [base + (0, -0.08, 0.0), base + (sx * 0.015, 0.0, 0.03), base + (0, 0.08, 0.0)]
        sb.add(K.rtube(pts, 0.012, "BH_Fur", n=5), "chest")
    for k in range(5):
        a = math.radians(-100 + 50 * k)
        top = np.array([0.08 * math.sin(a), 0.02 + 0.08 * math.cos(a), 1.74])
        d = np.array([math.sin(a) * 0.3, 0.25 * math.cos(a), -1.0])
        for prt in D.kelp(top, d, 0.16 + 0.05 * (k % 2), 0.022, "BH_Fur", out=(math.sin(a), math.cos(a), 0.0),
                          amp=0.012, seed=k * 1.7):
            sb.add(prt, weights=K.HEAD_W)


# ================================================================================================= weapon
def boat_hook():
    """Weapon space (grip at origin, +Z = shaft toward the head, hook edge on +X). ~2.35 m."""
    parts = []
    pts, prof = [], []
    for i in range(12):
        u = i / 11
        z = -0.86 + 2.14 * u
        pts.append((0.008 * math.sin(u * 5.0), 0.005 * math.cos(u * 4.0), z))
        r = 0.0185 - 0.003 * u + 0.0015 * math.sin(u * 23)
        prof.append((r, r))
    V, F = M.tube(pts, prof, n=8, up=(0, -1, 0))
    parts.append(M.Part(V, F, "BH_Wood", name="pole"))
    # rope grips (right hand at 0, left hand at +0.34)
    for z0, z1 in ((-0.1, 0.1), (0.24, 0.46)):
        V, F = M.lathe([(0, z0), (0.022, z0), (0.023, (z0 + z1) / 2), (0.022, z1), (0, z1)], 8)
        parts.append(M.Part(V, F, "BH_Horn", name="grip"))
    # iron ferrule + bands
    V, F = M.lathe([(0, -0.9), (0.012, -0.9), (0.021, -0.86), (0.021, -0.8), (0.0, -0.79)], 8)
    parts.append(M.Part(V, F, "BH_Rust", name="ferrule"))
    for z in (0.66, 0.9):
        V, F = M.lathe([(0, z - 0.012), (0.021, z - 0.012), (0.022, z), (0.021, z + 0.012), (0, z + 0.012)], 8)
        parts.append(M.Part(V, F, "BH_Rust", name="band"))
    # head: socket, straight spike, back-curving hook
    V, F = M.lathe([(0, 1.12), (0.02, 1.12), (0.026, 1.16), (0.024, 1.3), (0.018, 1.33), (0, 1.335)], 8)
    parts.append(M.Part(V, F, "BH_Rust", name="socket"))
    V, F = M.tube([(0, 0, 1.32), (0, 0, 1.44), (0, 0, 1.56)], [(0.016, 0.012), (0.01, 0.008), (0.0015, 0.0015)], n=4,
                  up=(0, -1, 0))
    parts.append(M.Part(V, F, "BH_Rust", name="spike"))
    hook = [(0.015, 0, 1.27), (0.07, 0, 1.3), (0.115, 0, 1.27), (0.13, 0, 1.2), (0.115, 0, 1.13), (0.09, 0, 1.105)]
    rr = [(0.014, 0.011), (0.013, 0.01), (0.012, 0.009), (0.01, 0.008), (0.007, 0.006), (0.0015, 0.0015)]
    V, F = M.tube(hook, rr, n=6, up=(0, -1, 0))
    parts.append(M.Part(V, F, "BH_Rust", name="hook"))
    # barnacles crusting the socket, a kelp tatter hanging off the hook
    for prt in D.barnacle_cluster((0.0, -0.022, 1.2), (0.1, -1, 0.1), 0.04, count=4, seed=31, rmin=0.008, rmax=0.014):
        parts.append(prt)
    for prt in D.barnacle_cluster((-0.022, 0.0, 1.05), (-1, 0.2, 0.1), 0.035, count=3, seed=32, rmin=0.007, rmax=0.012):
        parts.append(prt)
    parts += D.kelp((0.12, 0.0, 1.22), (0.25, 0.1, -1.0), 0.22, 0.026, "BH_Fur", out=(0, -1, 0), amp=0.015, seed=1.0)
    return parts
