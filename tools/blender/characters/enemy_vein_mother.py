"""Ysvharn, the Giant's Heart (bh-029, Builder M6, BOSS of the Veinworks): the thing that grew where the sleeping
Gigas' heart should be - a huge stooped figure of bone and grey-violet giant-stone, ~4.5 m to the tips of its crown.
Its torso is a gaunt hunched cage: a ridge of vertebra spurs up the back, ribs of pale bone curving round the front
and split open down the middle, and inside the opened cage the heart itself - a great pulsing white heart-cavity
(BH_WeakPoint: "strike the heart") in a pit of dark raw sinew. Veins like cables leave the heart: thick dark sinew
cables, each with a white burning line along it and white nodes, run over the shoulders, round the neck, down both
arms (wound round the forearms), across the belly to the hips and in two great loops down the back. Its arms are far
too long - knuckles at its knees - and end in claw-hands of five long jointed bone fingers. The head is thrust low and
forward: a long skull-like face of bone over stone with four white eyes and a long jaw of teeth, crowned by a ring
of long bone spurs splayed up and out (the silhouette key from the gameplay camera). A ragged skirt of dark membrane
hangs from a bone pelvis girdle; gaunt stone legs with bone knee plates, clawed feet. Every glow is pure white (bh-029).

Built at true size on the shared humanoid skeleton (custom long-armed, stooped proportions, real model space - the
gigas_spawn pattern, whose plate / horn / rock helpers it reuses). No weapon: the claws strike.
Clips: boss_roar boss_slam boss_summon boss_sweep cast_area cast_heavy cast_ultimate cast_weapon (+ boss_charge, gs_1)."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, interp_rows  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as GK  # noqa: E402
import enemy_rune_golem as RG  # noqa: E402
import enemy_glyphbound_warrior as Z  # noqa: E402
import enemy_gigas_spawn as GS  # noqa: E402
import kit_a_common as A  # noqa: E402

PROPS = proportions(
    2.4,
    pelvis_h=1.95, hip_h=1.87, knee_h=1.02, ankle_h=0.22, hip_x=0.34, ball_fwd=0.38, ball_h=0.07, toe_len=0.22,
    heel_back=0.18,
    hips_len=0.28, spine_len=0.5, chest_len=0.95, neck_len=0.14, head_len=0.55,
    clav_x0=0.16, clav_drop=0.24, shoulder_x=0.74, upper_len=1.0, fore_len=1.12, hand_len=0.4, grip_x=0.22,
    grip_drop=0.05,
)
L = GK.levels(PROPS)
PREVIEW_HEIGHT = 5.0

PALETTE = "vein_mother"
PALETTE_COLORS = {
    "BH_Stone": ((0.25, 0.235, 0.265), 0.0, 0.9, None, 0.0, 1.0),          # grey-violet giant-stone
    "BH_DarkSteel": ((0.11, 0.1, 0.115), 0.0, 0.92, None, 0.0, 1.0),       # darker stone in the joints
    "BH_Bone": ((0.62, 0.57, 0.47), 0.0, 0.55, None, 0.0, 1.0),            # pale bone: ribs, face, plates
    "BH_Horn": ((0.34, 0.29, 0.23), 0.0, 0.55, None, 0.0, 1.0),            # old dark bone: spurs, talons, crown
    "BH_Flesh": ((0.19, 0.055, 0.065), 0.0, 0.45, None, 0.0, 1.0),         # raw sinew, vein cables
    "BH_Cloth_Secondary": ((0.1, 0.045, 0.055), 0.0, 0.8, None, 0.0, 1.0),  # membrane skirt
    "BH_Shadow": ((0.014, 0.01, 0.012), 0.0, 0.85, None, 0.0, 1.0),
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),   # vein lines, eyes: white
    "BH_WeakPoint": ((1.0, 1.0, 1.0), 0.0, 0.3, (1.0, 1.0, 1.0), 6.0, 1.0),  # the heart
}
CLIPS = ["boss_roar", "boss_slam", "boss_summon", "boss_sweep", "cast_area", "cast_heavy", "cast_ultimate",
         "cast_weapon", "boss_charge", "gs_1"]

P = Z.P
horn, plate, rock = GS.horn, GS.plate, GS.rock
zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
HEAD_DY, HEAD_DZ = -0.6, -0.34

PELV = [(zh - 0.3, 0.32, 0.25, 0.27, 0.0, 0.02), (zh - 0.1, 0.42, 0.31, 0.32, 0.0, 0.02),
        (zh + 0.12, 0.44, 0.32, 0.32, 0.0, 0.0), (zh + 0.24, 0.4, 0.3, 0.3, 0.0, -0.01)]
TRUNK = [(zs - 0.02, 0.38, 0.29, 0.29, 0.0, -0.01), (zs + 0.22, 0.4, 0.29, 0.31, 0.0, -0.05),
         (zc, 0.5, 0.36, 0.4, 0.0, -0.09), (zc + 0.3, 0.62, 0.4, 0.55, 0.0, -0.15),
         (zc + 0.6, 0.68, 0.38, 0.64, 0.0, -0.21), (zn - 0.12, 0.62, 0.32, 0.62, 0.0, -0.26),
         (zn + 0.0, 0.46, 0.27, 0.52, 0.0, -0.27), (zn + 0.12, 0.24, 0.18, 0.32, 0.0, -0.24)]
CRANIUM = [(0.0, 0.22, 0.25, 0.25, 0.0, -0.03), (0.12, 0.28, 0.31, 0.31, 0.0, -0.04), (0.28, 0.3, 0.33, 0.35, 0.0, -0.03),
           (0.42, 0.26, 0.29, 0.32, 0.0, -0.01), (0.52, 0.16, 0.18, 0.22, 0.0, 0.02), (0.57, 0.06, 0.07, 0.1, 0.0, 0.04)]
JAW = [(-0.34, 0.08, 0.15, 0.07, 0.0, -0.16), (-0.18, 0.17, 0.24, 0.15, 0.0, -0.11), (0.0, 0.22, 0.27, 0.2, 0.0, -0.06)]


def hrows(rows):
    z0 = L["head"] + HEAD_DZ
    return [(z0 + r[0], r[1], r[2], r[3], r[4], r[5] + HEAD_DY) for r in rows]


def fy(rows, x, z):
    return GK.front_of(rows, x, z, p=2.4)


def by(rows, x, z):
    return GS.by(rows, x, z)


def addp(body, parts, bone=None, weights=None):
    for prt in parts:
        body.add(prt, bone, weights)


def cable(pts, r, nrm, glow=True, nodes=(), seed=0):
    """A vein cable: a thick dark sinew tube, a white burning line along its outer side (nrm: outward, one or per
    point), white nodes at the given point indices."""
    pts = np.asarray(pts, float)
    nrm = np.asarray(nrm, float)
    if nrm.ndim == 1:
        nrm = np.repeat(nrm[None], len(pts), 0)
    nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
    # subdivide into short segments (smooth skin weights need dense rings across the weight blends)
    node_pts = [(pts[i], nrm[i]) for i in nodes]
    P2, N2 = [pts[0]], [nrm[0]]
    for i in range(len(pts) - 1):
        k = max(1, int(math.ceil(np.linalg.norm(pts[i + 1] - pts[i]) / 0.09)))
        for j in range(1, k + 1):
            u = j / k
            P2.append(pts[i] * (1 - u) + pts[i + 1] * u)
            N2.append(normalize(nrm[i] * (1 - u) + nrm[i + 1] * u))
    pts, nrm = np.array(P2), np.array(N2)
    rng = np.random.default_rng(seed)
    rr = [r * (0.9 + 0.2 * math.sin(i * 1.7 + seed)) for i in range(len(pts))]
    out = [GK.rtube(pts, rr, "BH_Flesh", n=7)]
    if glow:
        out.append(GK.rtube(pts + nrm * np.array(rr)[:, None] * 0.8, r * 0.28, "BH_Emissive", n=4))
    for q, nn in node_pts:
        out.append(GK.blob(q + nn * r * 0.5, r * 1.25, "BH_Emissive", n=8, rings=5))
        out.append(GK.blob(q, r * 1.45, "BH_Flesh", n=8, rings=5))
    return out


# ================================================================================================= build
def build(body: Body):
    tw = GK.torso_w(PROPS)
    body.add(rock(TRUNK, mat="BH_Flesh", seed=3, amp=0.01), weights=tw)
    body.add(rock(PELV, seed=4), weights=GK.seat_w(body, zh + 0.05, zh - 0.28, max_leg=0.6))
    pelvis(body)
    cage(body, tw)
    back(body, tw)
    head(body)
    for s in ("L", "R"):
        arm(body, s)
        leg(body, s)
    belly_cables(body, tw)


def pelvis(body):
    for sx in (1, -1):
        body.add(plate((sx * 0.24, -0.18, zh + 0.06), (sx * 0.7, -1, 0.15), (0.42, 0.34, 0.08), up=(sx * 0.3, 0, 1),
                       seed=10 + sx), "hips")
        body.add(plate((sx * 0.3, 0.2, zh + 0.04), (sx * 0.6, 1, 0.2), (0.38, 0.3, 0.07), up=(sx * 0.3, 0, 1),
                       seed=12 + sx), "hips")
    # ragged membrane skirt hanging from the girdle
    w = body.skirt_weights(zh + 0.05, zh - 1.0, max_leg=0.8, center_w=0.12)
    wc = Z.centre_w(zh + 0.05, zh - 1.0, 0.6)          # front / back centre rags share both thighs
    for k, a in enumerate(np.linspace(0, 2 * math.pi, 13, endpoint=False)):
        c = np.array([0.46 * math.sin(a), -0.34 * math.cos(a), zh - 0.02])
        out = normalize(np.array([math.sin(a), -math.cos(a), 0.0]))
        ln = 0.7 + 0.25 * ((k * 5) % 3) / 2
        body.add(A.rag_strip(c, out * 0.25 + np.array([0, 0, -1.0]), ln, 0.3, "BH_Cloth_Secondary", n=5, thick=0.012,
                             ragged=0.6, seed=k, out=out), weights=wc if abs(c[0]) < 0.2 else w)


def cage(body, tw):
    """Ribs split open down the front, the heart inside them, cables leaving it."""
    zH = zc + 0.02
    yH = fy(TRUNK, 0, zH)
    # the pit of raw sinew + the heart (weak point) + a ring of torn tissue
    body.add(GK.blob((0, yH + 0.02, zH), 0.4, "BH_Shadow", scale=(1.0, 0.45, 1.15), n=14, rings=8), weights=tw)
    heart = GK.blob((0, yH - 0.08, zH), 0.29, "BH_WeakPoint", scale=(0.95, 0.75, 1.15), n=14, rings=9)
    GK.jitter(heart, 0.008, seed=2)
    body.add(heart, weights=tw)
    ring = [(0.34 * math.cos(a), yH - 0.04 + 0.02 * math.sin(3 * a), zH + 0.4 * math.sin(a))
            for a in np.linspace(0, 2 * math.pi, 19)]
    body.add(GK.rtube(ring, 0.05, "BH_Flesh", n=6), weights=tw)
    # ribs: pale bone arcs from the spine round the flanks to the split, five a side
    for i, z in enumerate((zc + 0.5, zc + 0.36, zc + 0.22, zc + 0.08, zc - 0.06)):
        for sx in (1, -1):
            pts = []
            for t in np.linspace(0.0, 1.0, 7):
                x = sx * (0.62 - 0.44 * t ** 0.8) * (1 - 0.06 * i)
                zz = z - 0.12 * t ** 1.4
                pts.append((x, fy(TRUNK, x, zz) - 0.035 - 0.05 * t, zz))
            pts[-1] = (pts[-1][0], pts[-1][1] - 0.04, pts[-1][2] + 0.02)
            body.add(A.tube(pts, [(0.06 - 0.005 * i, 0.04)] * 7, "BH_Bone", n=6, up=(0, -1, 0)), weights=tw)
            body.add(GK.blob(pts[-1], 0.05 - 0.004 * i, "BH_Bone", n=6, rings=4), weights=tw)
    # split sternum halves hanging open
    for sx in (1, -1):
        pts = [(sx * 0.22, fy(TRUNK, 0.22, zc + 0.56) - 0.04, zc + 0.56), (sx * 0.38, fy(TRUNK, 0.3, zc + 0.24) - 0.12,
                                                                          zc + 0.24),
               (sx * 0.32, fy(TRUNK, 0.3, zc - 0.14) - 0.1, zc - 0.14)]
        body.add(A.tube(pts, [(0.07, 0.04)] * 3, "BH_Bone", n=6, up=(0, -1, 0)), weights=tw)
    # cables leaving the heart: up over each shoulder, up into the neck
    for sx in (1, -1):
        sh = body.head("upper_arm." + ("L" if sx > 0 else "R"))
        pts = [(sx * 0.12, yH - 0.1, zH + 0.26), (sx * 0.3, fy(TRUNK, 0.3, zc + 0.7) - 0.06, zc + 0.7),
               (sx * 0.5, -0.12, zn + 0.08), sh + np.array([sx * 0.0, 0.05, 0.22])]
        nrm = [(0, -1, 0.3), (sx * 0.2, -1, 0.6), (sx * 0.3, -0.3, 1), (sx * 0.4, 0, 1)]
        addp(body, cable(pts, 0.07, nrm, nodes=(1,), seed=sx + 5), weights=tw)
        pts = [(sx * 0.08, yH - 0.12, zH + 0.3), (sx * 0.1, fy(TRUNK, 0.1, zc + 0.6) - 0.06, zc + 0.6),
               (sx * 0.12, fy(TRUNK, 0.12, zn - 0.1) - 0.08, zn - 0.1),
               (sx * 0.12, -0.38, zn + 0.1)]
        addp(body, cable(pts, 0.05, (0, -1, 0.3), nodes=(), seed=sx + 9), weights=tw)


def back(body, tw):
    """Vertebra spurs up the hump, bone plates, two great cable loops down the back."""
    for i, z in enumerate(np.linspace(zn + 0.02, zc - 0.1, 8)):
        yb = by(TRUNK, 0, z)
        body.add(GK.blob((0, yb - 0.02, z), 0.09, "BH_Bone", scale=(1.3, 0.8, 0.8), n=8, rings=5), weights=tw)
        ln = 0.4 - 0.03 * i if i > 0 else 0.3
        body.add(horn((0, yb + 0.02, z), (0, 0.7, 1.0), (0, 1.0, 0.1), ln, 0.06 - 0.004 * i, k=5),
                 "chest" if z > zc + 0.2 else None, None if z > zc + 0.2 else tw)
    for j, z in enumerate((zc + 0.6, zc + 0.3)):
        for sx in (1, -1):
            x = sx * 0.34
            n = normalize(np.array([x * 1.6, 1.0, 0.5]))
            body.add(plate((x, by(TRUNK, x, z) - 0.02, z), n, (0.42, 0.32, 0.09), up=(0, -0.3, 1), seed=30 + j * 2 + sx),
                     weights=tw)
    for sx in (1, -1):
        pts = [(sx * 0.2, by(TRUNK, 0.2, zn - 0.1) + 0.06, zn - 0.1), (sx * 0.52, by(TRUNK, 0.5, zc + 0.3) + 0.22,
                                                                       zc + 0.3),
               (sx * 0.46, by(TRUNK, 0.4, zc - 0.1) + 0.24, zc - 0.15), (sx * 0.2, by(PELV, 0.2, zh + 0.2) + 0.1, zh + 0.2)]
        nrm = [(sx * 0.3, 1, 0.3)] * 4
        addp(body, cable(pts, 0.065, nrm, nodes=(1, 2), seed=20 + sx), weights=GK.torso_w(PROPS, shoulder_blend=False))
    body.add(GK.blob((0, -0.12, zn + 0.04), 0.24, "BH_Flesh", scale=(1.2, 1.0, 0.6)), "chest")


def belly_cables(body, tw):
    for sx in (1, -1):
        pts = [(sx * 0.16, fy(TRUNK, 0.16, zc - 0.2) - 0.08, zc - 0.2), (sx * 0.3, fy(TRUNK, 0.3, zs + 0.2) - 0.04,
                                                                           zs + 0.2),
               (sx * 0.34, fy(PELV, 0.34, zh + 0.15) - 0.03, zh + 0.15), (sx * 0.38, -0.1, zh - 0.05)]
        addp(body, cable(pts, 0.05, (sx * 0.2, -1, 0.2), nodes=(1,), seed=40 + sx), weights=tw)
    for i, z in enumerate((zs + 0.16, zs + 0.0)):
        pts = [(x, fy(TRUNK, x, z) - 0.005, z + 0.03 * math.sin(x * 12)) for x in np.linspace(-0.24, 0.24, 5)]
        addp(body, GS.vcrack(pts, (0, -1, 0), 0.016, broken=(2,) if i else ()), weights=tw)


def head(body):
    C, J = hrows(CRANIUM), hrows(JAW)
    body.add(rock(C, mat="BH_Stone", seed=7, amp=0.008, n=22), "head")
    body.add(rock(J, mat="BH_Bone", seed=8, amp=0.006, n=18), "head")
    z0 = L["head"] + HEAD_DZ
    pts = [(0, -0.05, zn - 0.08), (0, -0.25, zn + 0.0), (0, HEAD_DY + 0.08, z0 + 0.06)]
    V, F = M.tube(pts, [(0.24, 0.24), (0.21, 0.2), (0.17, 0.17)], n=12, up=(0, -1, 0))
    body.add(P(V, F, "BH_Flesh", "neck"), weights=lambda V: [
        {"chest": 1.0} if v[1] > -0.12 else ({"neck": 1.0} if v[1] > -0.3 else {"neck": 0.4, "head": 0.6}) for v in V])
    # bone face plate over the stone skull: brow ridge, four eyes in two rows, nasal pit
    zb = z0 + 0.3
    yb = fy(C, 0, zb)
    V, F = M.sphere(1.0, 14, 8)
    V = np.asarray(V) * np.array([0.27, 0.12, 0.24])
    face = P(V, F, "BH_Bone", "faceplate")
    face.V[:, 1] = np.minimum(face.V[:, 1], 0.02)
    body.add(GK.jitter(face.move((0, fy(C, 0, z0 + 0.18) + 0.06, z0 + 0.2)), 0.006, seed=3), "head")
    for sx in (1, -1):
        body.add(GK.jitter(RG.slab((0.24, 0.12, 0.08), (sx * 0.12, yb - 0.04, zb + 0.02), R=Ry(sx * 14) @ Rx(-14),
                                   mat="BH_Bone", bev=0.03), 0.004, seed=71 + (sx > 0)), "head")
        for (dx, dz, r) in ((0.11, 0.2, 0.042), (0.17, 0.12, 0.03)):
            ye = fy(C, dx, z0 + dz) - 0.05
            body.add(GK.blob((sx * dx, ye + 0.02, z0 + dz), r * 1.6, "BH_Shadow", scale=(1.1, 0.6, 0.7)), "head")
            body.add(GK.blob((sx * dx, ye - 0.008, z0 + dz), r, "BH_Emissive", scale=(1.25, 0.4, 0.5)), "head")
    yn = fy(C, 0, z0 + 0.06) - 0.06
    for sx in (1, -1):
        body.add(GK.blob((sx * 0.03, yn + 0.01, z0 + 0.07), 0.028, "BH_Shadow", scale=(0.8, 0.5, 1.4)), "head")
    # long jaw: dark maw, a glowing throat, long uneven teeth top and bottom
    zm = z0 - 0.08
    ym = fy(J, 0, min(zm, J[-1][0]))
    body.add(GK.blob((0, ym + 0.04, zm), 0.15, "BH_Shadow", scale=(1.0, 0.4, 0.7), n=12, rings=6), "head")
    body.add(GK.blob((0, ym + 0.06, zm), 0.07, "BH_Emissive", scale=(1.0, 0.3, 0.6), n=10, rings=5), "head")
    rng = np.random.default_rng(9)
    for x in np.linspace(-0.12, 0.12, 7):
        h = 0.05 + 0.04 * rng.random()
        body.add(GK.cone((x, ym + 0.02, zm + 0.05), (x, ym + 0.02, zm + 0.05 - h), 0.018, "BH_Bone", n=5), "head")
        body.add(GK.cone((x + 0.015, ym + 0.025, zm - 0.06), (x + 0.015, ym + 0.025, zm - 0.06 + h * 0.8), 0.016,
                         "BH_Bone", n=5), "head")
    # the crown: a ring of long bone spurs splayed up and out round the back of the skull
    zc_ = z0 + 0.4
    cy = HEAD_DY + 0.0
    for k, a in enumerate(np.linspace(-150, 150, 11)):
        ra = math.radians(a)
        rad = np.array([math.sin(ra), math.cos(ra), 0.0])       # a = 0 -> straight back (+Y)
        base = np.array([0.0, cy, zc_]) + rad * np.array([0.27, 0.3, 0.0]) + np.array([0, 0, 0.06 * math.cos(ra)])
        ln = 0.5 + 0.32 * math.cos(ra * 0.6) ** 2 + 0.06 * (k % 2)
        d0 = rad * 0.55 + np.array([0, 0, 1.0])
        d1 = rad * 1.0 + np.array([0, 0, 0.45])
        body.add(horn(base, d0, d1, ln, 0.06, mat="BH_Horn" if k % 2 else "BH_Bone", n=6, k=6), "head")
    ring = [np.array([0.0, cy, zc_]) + np.array([0.29 * math.sin(math.radians(a)), 0.32 * math.cos(math.radians(a)),
                                                 0.04 * math.cos(math.radians(a))]) for a in np.linspace(-160, 160, 13)]
    body.add(GK.rtube(ring, 0.05, "BH_Bone", n=6), "head")
    # cracks with white light over the cranium
    for sx, pts in ((1, [(0.03, 0.46), (0.1, 0.4), (0.08, 0.34)]), (-1, [(0.05, 0.48), (0.14, 0.42), (0.2, 0.36)])):
        q = [(sx * x, fy(C, x, z0 + z) + 0.002, z0 + z) for x, z in pts]
        addp(body, GS.vcrack(q, (0, -1, 0.3), 0.01), "head")


def arm(body, s):
    sx = 1 if s == "L" else -1
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
    GK.arm(body, s, [(0.2, 0.21), (0.15, 0.16), (0.13, 0.14), (0.15, 0.15), (0.14, 0.14), (0.1, 0.1)], "BH_Stone",
           n=14, deltoid=0.23, deltoid_mat="BH_Stone")
    wsh = (lambda V, s=s: [{"shoulder." + s: 0.4, "upper_arm." + s: 0.6}] * len(V))
    for k, (dz, dy, sz) in enumerate(((0.22, 0.0, 0.42), (0.13, 0.15, 0.32), (0.13, -0.15, 0.3))):
        n = normalize(np.array([sx * 0.7, dy * 3, 1.0]))
        body.add(plate(sh + np.array([sx * 0.06, dy, dz - 0.04]), n, (sz, 0.3, 0.08), up=(0, 1, 0), seed=40 + k),
                 weights=wsh)
    body.add(horn(sh + np.array([sx * 0.14, 0.05, 0.26]), (sx * 0.6, 0.4, 1.0), (sx * 0.5, 1.0, 0.2), 0.42, 0.06),
             weights=wsh)
    # cable down the outside of the upper arm (rigid to it) and wound round the forearm
    Au, Af = body.axes(ua), body.axes(fa)
    ul, fl = body.p["upper_len"], body.p["fore_len"]
    pts = body.lpt(ua, [(0.04 * math.sin(u * 7), u * ul, 0.16) for u in (0.08, 0.35, 0.62, 0.9)])
    addp(body, cable(pts, 0.05, Au[:, 2], nodes=(2,), seed=50 + (sx > 0)), ua)
    k_ = 14
    pts, nrm = [], []
    for i in range(k_):
        t = i / (k_ - 1)
        ang = 2 * math.pi * 1.6 * t
        nl = np.array([math.cos(ang), 0.0, math.sin(ang)])
        pts.append(body.lpt(fa, [(0.155 * nl[0], (0.12 + 0.7 * t) * fl, 0.155 * nl[2])])[0])
        nrm.append(Af @ nl)
    addp(body, cable(pts, 0.04, nrm, nodes=(4, 10), seed=52 + (sx > 0)), fa)
    body.add(horn(el + np.array([0, 0.12, 0.0]), (0, 1, -0.3), (0, 0.4, -1.0), 0.3, 0.06),
             weights=lambda V, ua=ua, fa=fa: [{ua: 0.3, fa: 0.7}] * len(V))
    for k, u in enumerate((0.3, 0.62)):
        c = body.lpt(fa, [(0.0, u * fl, -0.15)])[0]
        body.add(plate(c, -Af[:, 2], (0.3, 0.2, 0.06), up=Af[:, 1], seed=56 + k + (sx > 0) * 5), fa)
    claw_hand(body, s)


def claw_hand(body, s):
    """Five long jointed bone fingers, curled, with dark talons; rigid to hand.<s> (bone-local: y along the hand,
    z = back of the hand)."""
    ha = "hand." + s
    Ax = body.axes(ha)
    o = body.head(ha)
    body.add(RG.local_box(body, ha, (0.3, 0.3, 0.16), (0, 0.13, 0.0), mat="BH_Stone", bev=0.04), ha)
    body.add(RG.local_box(body, ha, (0.26, 0.2, 0.06), (0, 0.14, 0.09), mat="BH_Bone", bev=0.02), ha)
    fwd = Ax.T @ np.array([0, -1.0, 0])
    tx = 1.0 if fwd[0] > 0 else -1.0
    for k, x in enumerate((-0.11, -0.04, 0.03, 0.1)):
        ln = (0.5, 0.6, 0.58, 0.48)[k]
        base = o + Ax @ np.array([x, 0.27, 0.0])
        d0 = np.array([x * 0.6, 1.0, -0.05])
        pts = [base]
        for i, curl in enumerate((0.1, 0.45, 0.85, 1.25)):
            d = Ax @ normalize(d0 + np.array([0, 0, -curl]))
            pts.append(pts[-1] + d * ln / 4)
        body.add(A.tube(pts[:4], [0.034, 0.03, 0.026, 0.022], "BH_Bone", n=6), ha)
        for q in pts[1:3]:
            body.add(GK.blob(q, 0.034, "BH_Bone", n=6, rings=4), ha)
        tip = pts[3]
        body.add(A.taper([tip, tip + (pts[4] - pts[3]) * 1.6], 0.024, 0.003, "BH_Horn", n=5), ha)
    base = o + Ax @ np.array([tx * 0.14, 0.12, -0.04])
    body.add(horn(base, Ax @ np.array([tx * 0.6, 0.6, -0.3]), Ax @ np.array([0.0, 0.6, -1.0]), 0.36, 0.035, n=6, k=5), ha)


def leg(body, s):
    sx = 1 if s == "L" else -1
    th, sh = "thigh." + s, "shin." + s
    GK.leg(body, s, [(0.25, 0.26), (0.2, 0.21), (0.16, 0.17), (0.17, 0.18), (0.16, 0.17), (0.11, 0.11)], "BH_Stone",
           n=14)
    hp, k, a = body.head(th), body.head(sh), body.tail(sh)
    body.add(plate(k + np.array([0, -0.15, 0.03]), (0, -1, 0.2), (0.3, 0.28, 0.08), up=(0, 0, 1), seed=60 + (sx > 0)),
             weights=lambda V, th=th, sh=sh: [{th: 0.4, sh: 0.6}] * len(V))
    body.add(horn(k + np.array([0, -0.2, 0.06]), (0, -1, 0.4), (0, -0.2, 1.0), 0.2, 0.045),
             weights=lambda V, th=th, sh=sh: [{th: 0.4, sh: 0.6}] * len(V))
    body.add(plate(hp + (k - hp) * 0.45 + np.array([sx * 0.2, -0.04, 0]), (sx, -0.3, 0), (0.36, 0.24, 0.08),
                   up=(0, 0, 1), seed=62 + (sx > 0)), th)
    q = [k + (a - k) * u + np.array([sx * (0.16 - 0.04 * u), -0.05, 0]) for u in (0.15, 0.45, 0.75)]
    addp(body, GS.vcrack(q, (sx, -0.3, 0), 0.013, broken=(0,)), sh)
    pts = [hp + (k - hp) * u + np.array([sx * 0.05, -0.2, 0]) for u in (0.1, 0.45, 0.85)]
    addp(body, cable(pts, 0.04, (0, -1, 0), nodes=(1,), seed=70 + (sx > 0)), th)
    GK.bare_foot(body, s, "BH_Stone", 0.66, 0.16, 0.15, claw_mat="BH_Horn", toes=3, toe_r=0.05)
