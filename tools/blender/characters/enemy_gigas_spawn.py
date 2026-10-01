"""Gigas Spawnling (bh-029, Builder M4, Zarael / Heart Citadel + Veinworks brute): a ~3 m creature grown from the
sleeping giant itself. A hunched body of grey stone with plates of old bone pushed out through it - a hump of
overlapping bone plates and spurs on the upper back, bone ribs across the chest, plates on the shoulders, forearms and
knees. Arms far too long (the knuckles hang by its shins), ending in huge three-talon claws of bone. The head is
thrust low and forward: a skull-like head of rock with a heavy brow, deep sockets burning white, a nasal cavity and a
jaw of stone teeth. White veins pulse in the cracks between every stone and bone plate (pure white BH_Emissive, the
bh-029 glow rule). Bare stone feet with bone claws.

Built at true size on the shared humanoid skeleton (custom long-armed proportions, real model space, the
mossback_idol / rune_golem pattern). No weapon: the claws strike. Clips: axe_1 axe_2 boss_slam cast_heavy
(+ boss_charge, gs_1)."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft, interp_rows, M_align_z  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as GK  # noqa: E402
import enemy_rune_golem as RG  # noqa: E402
import enemy_glyphbound_warrior as Z  # noqa: E402
import kit_a_common as A  # noqa: E402

PROPS = proportions(
    1.55,
    pelvis_h=1.34, hip_h=1.28, knee_h=0.7, ankle_h=0.15, hip_x=0.24, ball_fwd=0.26, ball_h=0.05, toe_len=0.14,
    heel_back=0.12,
    hips_len=0.18, spine_len=0.3, chest_len=0.62, neck_len=0.08, head_len=0.38,
    clav_x0=0.1, clav_drop=0.16, shoulder_x=0.5, upper_len=0.66, fore_len=0.8, hand_len=0.28, grip_x=0.15,
    grip_drop=0.03,
)
L = GK.levels(PROPS)
PREVIEW_HEIGHT = 3.2

PALETTE = "gigas_spawn"
PALETTE_COLORS = {
    "BH_Stone": ((0.27, 0.27, 0.28), 0.0, 0.9, None, 0.0, 1.0),            # grey giant-stone
    "BH_DarkSteel": ((0.12, 0.115, 0.12), 0.0, 0.92, None, 0.0, 1.0),     # darker stone (joints, under-plates)
    "BH_Bone": ((0.5, 0.46, 0.38), 0.0, 0.6, None, 0.0, 1.0),             # bone plates / ribs
    "BH_Horn": ((0.26, 0.22, 0.17), 0.0, 0.6, None, 0.0, 1.0),            # old dark bone: talons, spurs
    "BH_Flesh": ((0.14, 0.05, 0.05), 0.0, 0.5, None, 0.0, 1.0),           # raw sinew in the deep seams
    "BH_Shadow": ((0.015, 0.013, 0.014), 0.0, 0.85, None, 0.0, 1.0),       # sockets, mouth, grooves
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),  # white veins, eyes
}
CLIPS = ["axe_1", "axe_2", "boss_slam", "cast_heavy", "boss_charge", "gs_1"]

GLOW = "BH_Emissive"
P = Z.P
slab, local_box = RG.slab, RG.local_box
zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
HEAD_DY, HEAD_DZ = -0.3, -0.27

# (z, rx, ry_front, ry_back, keel, cy): the upper body leans forward, the hump swells behind
PELV = [(zh - 0.24, 0.27, 0.2, 0.22, 0.0, 0.02), (zh - 0.08, 0.35, 0.25, 0.26, 0.0, 0.02),
        (zh + 0.1, 0.36, 0.26, 0.26, 0.0, 0.0), (zh + 0.2, 0.34, 0.26, 0.26, 0.0, -0.01)]
TRUNK = [(zs - 0.02, 0.34, 0.27, 0.27, 0.0, -0.01), (zs + 0.16, 0.37, 0.3, 0.28, 0.0, -0.03),
         (zc, 0.43, 0.33, 0.32, 0.0, -0.06), (zc + 0.2, 0.5, 0.33, 0.42, 0.0, -0.1),
         (zc + 0.4, 0.54, 0.31, 0.5, 0.0, -0.13), (zn - 0.1, 0.5, 0.27, 0.5, 0.0, -0.14),
         (zn + 0.0, 0.38, 0.22, 0.42, 0.0, -0.13), (zn + 0.1, 0.2, 0.14, 0.26, 0.0, -0.1)]
CRANIUM = [(0.0, 0.19, 0.2, 0.19, 0.0, -0.02), (0.08, 0.235, 0.25, 0.24, 0.0, -0.03),
           (0.2, 0.25, 0.27, 0.27, 0.0, -0.03), (0.3, 0.23, 0.25, 0.26, 0.0, -0.02),
           (0.38, 0.17, 0.19, 0.2, 0.0, 0.0), (0.43, 0.07, 0.09, 0.11, 0.0, 0.02)]
JAW = [(-0.17, 0.09, 0.13, 0.07, 0.0, -0.08), (-0.09, 0.16, 0.2, 0.13, 0.0, -0.06), (0.01, 0.185, 0.21, 0.16, 0.0,
                                                                                     -0.04)]


def hrows(rows):
    z0 = L["head"] + HEAD_DZ
    return [(z0 + r[0], r[1], r[2], r[3], r[4], r[5] + HEAD_DY) for r in rows]


def fy(rows, x, z, p=2.4):
    return GK.front_of(rows, x, z, p=p)


def by(rows, x, z, p=2.4):
    r = interp_rows(rows, z)
    ax = min(abs(x) / r[1], 0.999)
    return (r[5] if len(r) > 5 else 0.0) + r[3] * (1 - ax ** p) ** (1 / p)


def rock(rows, mat="BH_Stone", n=26, p=2.4, seed=1, amp=0.012):
    V, F = torso_loft(rows, n=n, p=p, cap0=True, cap1=True)
    return GK.jitter(P(V, F, mat, "rock"), amp, seed=seed)


def horn(base, d0, d1, length, r0, mat="BH_Horn", n=6, k=6):
    d0, d1 = normalize(d0), normalize(d1)
    pts = [np.asarray(base, float)]
    for i in range(1, k):
        t = i / (k - 1)
        pts.append(pts[-1] + normalize(d0 * (1 - t) + d1 * t) * length / (k - 1))
    return A.tube(pts, [r0 * (1 - t) ** 0.85 + 0.003 for t in np.linspace(0, 1, k)], mat, n=n, name="horn")


def vcrack(pts, nrm, r=0.016, broken=()):
    """A crack in the stone with a white vein burning in it (dark groove + glow line)."""
    return Z.channel(pts, nrm, r=r, broken=broken)


def plate(c, nrm, size, up=(0, 0, 1), mat="BH_Bone", bev=0.02, seed=0):
    """A rounded bone scute lying on a surface (normal nrm): size (w along up, h across, t thick), a domed lens of
    bone with a lumpy rim, slightly curled at the ends."""
    n = normalize(nrm)
    u = np.asarray(up, float) - n * np.dot(up, n)
    R = M_align_z(n, normalize(u))           # x -> up direction, z -> normal
    V, F = M.sphere(1.0, 12, 6)
    V = np.asarray(V, float)
    V[:, 2] = np.where(V[:, 2] < 0, V[:, 2] * 0.25, V[:, 2])
    V = V * np.array([size[0] / 2, size[1] / 2, size[2]])
    p = P(V, F, mat, "plate")
    p.warp(lambda v: (v[0], v[1], v[2] + 0.5 * size[2] * (v[0] / (size[0] / 2)) ** 2))
    GK.jitter(p, size[2] * 0.08, seed=seed)
    p.V = p.V @ R.T + np.asarray(c, float)
    return p


def addp(body, parts, bone=None, weights=None):
    for prt in parts:
        body.add(prt, bone, weights)


# ================================================================================================= build
def build(body: Body):
    tw = GK.torso_w(PROPS)
    trunk = rock(TRUNK, seed=3)
    body.add(trunk, weights=tw)
    body.add(rock(PELV, seed=4), weights=GK.seat_w(body, zh + 0.05, zh - 0.26, max_leg=0.6))
    # bone pelvis girdle + a loin of stacked stone slabs
    for sx in (1, -1):
        body.add(plate((sx * 0.22, -0.2, zh + 0.04), (sx * 0.6, -1, 0.1), (0.34, 0.3, 0.07), up=(sx * 0.3, 0, 1),
                       seed=10 + sx), "hips")
    for k, (z, w) in enumerate(((zh - 0.08, 0.34), (zh - 0.22, 0.28), (zh - 0.34, 0.2))):
        body.add(slab((w, 0.1, 0.16), (0, -0.25 + 0.01 * k, z), R=Rx(6 + 4 * k), mat="BH_DarkSteel", bev=0.02),
                 weights=lambda V: [{"hips": 0.8, "thigh.L": 0.1, "thigh.R": 0.1}] * len(V))
    chest(body, tw)
    hump(body, tw)
    head(body)
    for s in ("L", "R"):
        arm(body, s)
        leg(body, s)


def chest(body, tw):
    # bone ribs curving round the front of the chest, white veins in the cracks between them
    for i, z in enumerate((zc + 0.38, zc + 0.26, zc + 0.14, zc + 0.02)):
        for sx in (1, -1):
            pts = []
            for t in np.linspace(0.05, 1.0, 6):
                x = sx * (0.04 + 0.42 * t * (1 - 0.1 * i))
                zz = z - 0.08 * t ** 1.6
                pts.append((x, fy(TRUNK, x, zz) - 0.01, zz))
            body.add(A.tube(pts, [(0.045 - 0.004 * i, 0.03)] * 6, "BH_Bone", n=6, up=(0, -1, 0)), weights=tw)
    keel = [(0.0, fy(TRUNK, 0, z) - 0.02, z) for z in np.linspace(zc - 0.06, zc + 0.46, 5)]
    body.add(A.tube(keel, [(0.05, 0.035)] * 5, "BH_Bone", n=6, up=(0, -1, 0)), weights=tw)
    for i, z in enumerate((zc + 0.32, zc + 0.2, zc + 0.08)):
        for sx in (1, -1):
            pts = [(sx * x, fy(TRUNK, sx * x, z - 0.04 * x) + 0.004, z - 0.04 * x) for x in (0.07, 0.18, 0.3, 0.38)]
            addp(body, vcrack(pts, (0, -1, 0), 0.012, broken=(1,) if (i + (sx > 0)) % 2 else ()), weights=tw)
    # belly: fissured stone with a glowing seam and a few bone knobs
    for sx in (1, -1):
        pts = [(sx * 0.05, fy(TRUNK, 0.05, zs + 0.25) - 0.0, zs + 0.25), (sx * 0.16, fy(TRUNK, 0.16, zs + 0.12), zs + 0.12),
               (sx * 0.12, fy(TRUNK, 0.12, zs - 0.0), zs), (sx * 0.22, fy(PELV, 0.22, zh + 0.12), zh + 0.12)]
        addp(body, vcrack(pts, (0, -1, 0), 0.014), weights=tw)
        body.add(GK.blob((sx * 0.25, fy(TRUNK, 0.25, zs + 0.2) + 0.02, zs + 0.2), 0.07, "BH_Bone", scale=(1, 0.6, 1.1)),
                 weights=tw)


def hump(body, tw):
    """Overlapping bone plates and spurs over the upper back (the silhouette key from the gameplay camera)."""
    rows = TRUNK
    k = 0
    for j, z in enumerate((zn - 0.04, zc + 0.36, zc + 0.18, zc + 0.0)):
        for x in ((-0.26, 0.0, 0.26) if j < 3 else (-0.16, 0.16)):
            yb = by(rows, x, z)
            n = normalize(np.array([x * 1.6, 1.0, 0.55 - 0.2 * j]))
            body.add(plate((x, yb - 0.02, z), n, (0.3, 0.26 - 0.02 * j, 0.08), up=(0, -0.3, 1), seed=20 + k), weights=tw)
            k += 1
    # spinal ridge spurs
    for i, z in enumerate(np.linspace(zn + 0.02, zc + 0.02, 6)):
        yb = by(rows, 0, z)
        ln = 0.3 - 0.035 * i if i > 0 else 0.2
        body.add(horn((0, yb + 0.02, z), (0, 0.6, 1.0), (0, 1.0, 0.2), ln, 0.06 - 0.005 * i, k=5), "chest" if z > zc + 0.1
                 else None, None if z > zc + 0.1 else tw)
    # side spurs on the hump
    for sx in (1, -1):
        for i, z in enumerate((zn - 0.08, zc + 0.24)):
            x = sx * 0.36
            body.add(horn((x, by(rows, x, z) - 0.05, z), (sx * 0.7, 0.6, 0.8), (sx * 0.3, 1.0, 0.0), 0.22 - 0.04 * i, 0.045,
                          k=5), weights=tw)
    # white veins in the cracks between the plates
    for z in (zc + 0.46, zc + 0.27, zc + 0.09):
        pts = [(x, by(rows, x, z) + 0.004, z + 0.02 * math.sin(x * 9)) for x in np.linspace(-0.38, 0.38, 7)]
        addp(body, vcrack(pts, (0, 1, 0.2), 0.013, broken=(2,)), weights=tw)
    for sx in (1, -1):
        pts = [(sx * 0.13, by(rows, 0.13, z) + 0.004, z) for z in np.linspace(zc + 0.5, zc - 0.05, 5)]
        addp(body, vcrack(pts, (0, 1, 0), 0.012, broken=(1,)), weights=tw)
    # sinew in the deep seam where the head meets the hump
    body.add(GK.blob((0, -0.05, zn + 0.02), 0.2, "BH_Flesh", scale=(1.2, 1.0, 0.6)), "chest")


def head(body):
    C, J = hrows(CRANIUM), hrows(JAW)
    body.add(rock(C, seed=7, amp=0.008, n=22), "head")
    body.add(rock(J, seed=8, amp=0.006, n=18), "head")
    z0 = L["head"] + HEAD_DZ
    # neck: a thick stone column from the chest forward into the skull
    pts = [(0, -0.02, zn - 0.05), (0, -0.12, zn + 0.05), (0, HEAD_DY + 0.06, z0 + 0.06)]
    V, F = M.tube(pts, [(0.2, 0.2), (0.18, 0.17), (0.15, 0.15)], n=12, up=(0, -1, 0))
    body.add(P(V, F, "BH_DarkSteel", "neck"), weights=lambda V: [
        {"chest": 1.0} if v[1] > -0.06 else ({"neck": 1.0} if v[1] > -0.16 else {"neck": 0.4, "head": 0.6}) for v in V])
    # heavy brow: two angled ridges meeting over a dark nasal pit; sockets sunk deep under them
    zb = z0 + 0.25
    for sx in (1, -1):
        yb = fy(C, 0.1, zb, 2.4)
        body.add(GK.jitter(slab((0.2, 0.12, 0.08), (sx * 0.1, yb + 0.015, zb + 0.005), R=Ry(sx * 14) @ Rx(-14),
                                bev=0.03), 0.004, seed=70 + (sx > 0)), "head")
        ze = z0 + 0.175
        ye = fy(C, 0.1, ze, 2.4)
        body.add(GK.blob((sx * 0.1, ye + 0.03, ze), 0.06, "BH_Shadow", scale=(1.15, 0.6, 0.62)), "head")
        body.add(GK.blob((sx * 0.105, ye - 0.004, ze + 0.004), 0.028, GLOW, scale=(1.3, 0.35, 0.32), rot=Ry(-sx * 12)), "head")
        # cheekbones: hard ridges under the sockets, sweeping back
        body.add(GK.rtube([(sx * 0.06, ye - 0.0, z0 + 0.1), (sx * 0.16, fy(C, 0.16, z0 + 0.1, 2.4) + 0.0, z0 + 0.11),
                           (sx * 0.23, HEAD_DY + 0.0, z0 + 0.13)], [0.035, 0.04, 0.025], "BH_Bone", n=6), "head")
        # small bone spurs behind the cranium
        body.add(horn((sx * 0.12, HEAD_DY + 0.2, z0 + 0.34), (sx * 0.5, 1.0, 0.5), (sx * 0.2, 1.0, -0.2), 0.18, 0.035,
                      k=4), "head")
    yn = fy(C, 0, z0 + 0.12, 2.4)
    V, F = M.prism(np.array([(-0.04, 0.0), (0.04, 0.0), (0.0, 0.08)]), 0.05, axis="y")
    body.add(P(V, F, "BH_Shadow", "nose").move((0, yn + 0.012, z0 + 0.07)), "head")
    # jutting lower jaw with a dark maw, uneven stone teeth and two tusks rising from the jaw
    zm = z0 - 0.02
    ym = fy(J, 0, min(zm, J[-1][0]), 2.4)
    body.add(slab((0.24, 0.06, 0.05), (0, ym + 0.025, zm), mat="BH_Shadow", bev=0.01), "head")
    body.add(slab((0.16, 0.02, 0.016), (0, ym + 0.04, zm), mat=GLOW, bev=0.004), "head")
    rng = np.random.default_rng(9)
    for k, x in enumerate((-0.085, -0.045, -0.01, 0.03, 0.07)):
        h = 0.03 + 0.025 * rng.random()
        body.add(GK.cone((x, ym + 0.02, zm + 0.045), (x + 0.004, ym + 0.02, zm + 0.045 - h), 0.017, "BH_Bone", n=5),
                 "head")
    for sx in (1, -1):
        body.add(horn((sx * 0.1, ym + 0.0, zm - 0.05), (sx * 0.2, -0.3, 1.0), (sx * 0.4, 0.2, 1.0), 0.13, 0.026,
                      mat="BH_Bone", n=6, k=4), "head")
    for x in (-0.05, 0.0, 0.05):
        body.add(GK.cone((x, ym + 0.02, zm - 0.04), (x, ym + 0.02, zm - 0.04 + 0.03), 0.014, "BH_Bone", n=5), "head")
    # cracks over the cranium (white)
    for sx, pts in ((1, [(0.02, 0.38), (0.08, 0.32), (0.06, 0.27), (0.13, 0.24)]),
                    (-1, [(0.04, 0.4), (0.12, 0.34), (0.18, 0.3)])):
        q = [(sx * x, fy(C, x, z0 + z, 2.4) + 0.002, z0 + z) for x, z in pts]
        addp(body, vcrack(q, (0, -1, 0.3), 0.009), "head")


def arm(body, s):
    sx = 1 if s == "L" else -1
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
    GK.arm(body, s, [(0.2, 0.21), (0.17, 0.18), (0.15, 0.16), (0.15, 0.16), (0.17, 0.17), (0.12, 0.12)], "BH_Stone",
           n=14, deltoid=0.22, deltoid_mat="BH_Stone")
    # shoulder: overlapping bone plates + a spur
    for k, (dz, dy, sz) in enumerate(((0.2, 0.0, 0.36), (0.12, 0.12, 0.28), (0.12, -0.12, 0.26))):
        n = normalize(np.array([sx * 0.7, dy * 3, 1.0]))
        body.add(plate(sh + np.array([sx * 0.06, dy, dz - 0.04]), n, (sz, 0.26, 0.07), up=(0, 1, 0), seed=40 + k),
                 weights=lambda V, s=s: [{"shoulder." + s: 0.4, "upper_arm." + s: 0.6}] * len(V))
    body.add(horn(sh + np.array([sx * 0.12, 0.05, 0.22]), (sx * 0.6, 0.4, 1.0), (sx * 0.4, 1.0, 0.2), 0.3, 0.05),
             weights=lambda V, s=s: [{"shoulder." + s: 0.4, "upper_arm." + s: 0.6}] * len(V))
    Aua = body.axes(ua)
    ul = body.p["upper_len"]
    addp(body, vcrack(body.lpt(ua, [(0.02 * math.sin(u * 9), u * ul, 0.165) for u in (0.2, 0.4, 0.6, 0.8)]), Aua[:, 2],
                      0.012, broken=(1,)), ua)
    # elbow spur, forearm bone plates (outer side), white veins between them
    body.add(horn(el + np.array([0, 0.1, 0.0]), (0, 1, -0.3), (0, 0.4, -1.0), 0.2, 0.05),
             weights=lambda V, ua=ua, fa=fa: [{ua: 0.3, fa: 0.7}] * len(V))
    fl = body.p["fore_len"]
    Afa = body.axes(fa)
    for k, u in enumerate((0.25, 0.5, 0.75)):
        c = body.lpt(fa, [(0.0, u * fl, 0.17)])[0]
        body.add(plate(c, Afa[:, 2], (0.24, 0.2, 0.06), up=Afa[:, 1], seed=50 + k + (sx > 0) * 5), fa)
    for u in (0.38, 0.63):
        q = body.lpt(fa, [(x, u * fl, 0.17) for x in (-0.12, -0.04, 0.04, 0.12)])
        addp(body, vcrack(q, Afa[:, 2], 0.01), fa)
    claw(body, s)


def claw(body, s):
    """Huge three-talon bone claw + thumb talon, rigid to hand.<s> (bone-local: y along the hand)."""
    ha = "hand." + s
    A_ = body.axes(ha)
    body.add(local_box(body, ha, (0.28, 0.3, 0.2), (0, 0.13, 0.0), mat="BH_Stone", bev=0.04), ha)
    body.add(local_box(body, ha, (0.26, 0.12, 0.08), (0, 0.12, 0.1), mat="BH_Bone", bev=0.02), ha)
    fwd = A_.T @ np.array([0, -1.0, 0])
    tx = 1.0 if fwd[0] > 0 else -1.0
    for k, x in enumerate((-0.09, 0.0, 0.09)):
        base = body.lpt(ha, [(x, 0.27, 0.0)])[0]
        d0 = A_ @ np.array([0.0, 1.0, -0.15])
        d1 = A_ @ np.array([0.0, 0.3, -1.0])
        ln = 0.34 if k == 1 else 0.3
        body.add(horn(base, d0, d1, ln * 0.55, 0.055, mat="BH_Stone", n=7, k=4), ha)
        tip0 = base + normalize(d0) * ln * 0.5
        body.add(horn(tip0 + normalize(d0 * 0.4 + d1 * 0.6) * 0.0, d0 * 0.3 + d1 * 0.7, d1 - d0 * 0.5, ln * 0.6, 0.04,
                      mat="BH_Horn", n=6, k=5), ha)
    base = body.lpt(ha, [(tx * 0.15, 0.1, -0.02)])[0]
    body.add(horn(base, A_ @ np.array([tx * 0.6, 0.6, -0.4]), A_ @ np.array([0.0, 0.5, -1.0]), 0.24, 0.045, n=6, k=5),
             ha)


def leg(body, s):
    sx = 1 if s == "L" else -1
    th, sh = "thigh." + s, "shin." + s
    GK.leg(body, s, [(0.23, 0.24), (0.21, 0.22), (0.18, 0.19), (0.17, 0.18), (0.17, 0.18), (0.12, 0.12)], "BH_Stone",
           n=14)
    hp, k, a = body.head(th), body.head(sh), body.tail(sh)
    body.add(plate(k + np.array([0, -0.15, 0.02]), (0, -1, 0.2), (0.24, 0.24, 0.07), up=(0, 0, 1), seed=60 + (sx > 0)),
             weights=lambda V, th=th, sh=sh: [{th: 0.4, sh: 0.6}] * len(V))
    body.add(horn(k + np.array([0, -0.2, 0.05]), (0, -1, 0.4), (0, -0.2, 1.0), 0.14, 0.035),
             weights=lambda V, th=th, sh=sh: [{th: 0.4, sh: 0.6}] * len(V))
    body.add(plate(hp + (k - hp) * 0.45 + np.array([sx * 0.2, -0.04, 0]), (sx, -0.3, 0), (0.3, 0.2, 0.07), up=(0, 0, 1),
                   seed=62 + (sx > 0)), th)
    q = [hp + (k - hp) * u + np.array([sx * 0.02, -0.215, 0]) for u in (0.2, 0.45, 0.7)]
    addp(body, vcrack(q, (0, -1, 0), 0.012), th)
    q = [k + (a - k) * u + np.array([sx * (0.17 - 0.04 * u), -0.04, 0]) for u in (0.2, 0.5, 0.8)]
    addp(body, vcrack(q, (sx, -0.3, 0), 0.011, broken=(0,)), "shin." + s)
    GK.bare_foot(body, s, "BH_Stone", 0.56, 0.14, 0.13, claw_mat="BH_Horn", toes=3, toe_r=0.045)
