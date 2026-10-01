"""Varrogh, the Deathspan Colossus (bh-029, Builder M3, BOSS of the Bridge of Death): the Wirewrights' last guardian
of the span, a ~4.5 m construct of cast bronze and pale carved stone. A massive chest block bound in bronze bands with
a stepped-fret breast and a great glyph eye, stepped pylon pauldrons, a bronze-segmented waist over a dark core
column, pillar legs on slab feet. The head is a pylon capital: a tall block with a single white visor slit, crowned
by widening stepped courses. On its back stand three arc coils (bronze helices round white-hot cores, BH_WeakPoint:
"its back coils are its heart") with arcs of current jumping between their crowns. The right forearm ends in a
hammer-fist (a huge banded stone block with a glyph face), the left in a coil-lance (a long bronze lance wound with
coils, a white emitter fork at its tip). White light burns in its seams and in the corruption cracks that split
it; two Kharvenn rune-chain spikes are driven into its right shoulder and back, their snapped chains hanging.

Built at true size (~4.5 m to the capital, coils ~4.6 m) on the shared skeleton with custom construct proportions;
no weapon sockets are used (hammer and lance are part of the hands). Clips: boss_charge boss_slam boss_summon
boss_sweep cast_area cast_heavy cast_ultimate (+ boss_roar, gs_1, the enemy base set)."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as GK  # noqa: E402
import enemy_rune_golem as RG  # noqa: E402
import enemy_span_warden as SW  # noqa: E402
import enemy_glyphbound_warrior as Z  # noqa: E402
import kit_a_common as A  # noqa: E402

PROPS = proportions(
    2.4,
    pelvis_h=1.85, hip_h=1.77, knee_h=0.95, ankle_h=0.22, hip_x=0.4, ball_fwd=0.42, ball_h=0.07, toe_len=0.2,
    heel_back=0.18,
    hips_len=0.32, spine_len=0.52, chest_len=1.05, neck_len=0.2, head_len=0.42,
    clav_x0=0.18, clav_drop=0.27, shoulder_x=0.92, upper_len=0.84, fore_len=0.9, hand_len=0.3, grip_x=0.2,
    grip_drop=0.04,
)
L = GK.levels(PROPS)
PREVIEW_HEIGHT = 5.0

PALETTE = "deathspan_colossus"
PALETTE_COLORS = {
    "BH_Stone": ((0.45, 0.42, 0.355), 0.0, 0.9, None, 0.0, 1.0),          # pale weathered glyph stone
    "BH_Bronze": ((0.4, 0.25, 0.11), 1.0, 0.48, None, 0.0, 1.0),          # cast bronze frame
    "BH_Gold": ((0.6, 0.4, 0.16), 1.0, 0.36, None, 0.0, 1.0),             # bright bronze bands / rims
    "BH_DarkSteel": ((0.07, 0.065, 0.06), 0.3, 0.8, None, 0.0, 1.0),      # dark joint stones / core column
    "BH_Horn": ((0.1, 0.37, 0.36), 0.0, 0.35, None, 0.0, 1.0),            # turquoise mosaic
    "BH_Steel": ((0.22, 0.22, 0.24), 0.9, 0.5, None, 0.0, 1.0),           # Kharvenn chain iron
    "BH_Shadow": ((0.016, 0.014, 0.013), 0.0, 0.85, None, 0.0, 1.0),      # grooves / cracks
    "BH_Emissive": SW.WHITE_GLOW,                                          # seams, eye, visor, arcs
    "BH_WeakPoint": ((1.0, 1.0, 1.0), 0.0, 0.3, (1.0, 1.0, 1.0), 6.0, 1.0),  # the three coil cores (its heart)
}
CLIPS = ["boss_charge", "boss_slam", "boss_summon", "boss_sweep", "cast_area", "cast_heavy", "cast_ultimate",
         "boss_roar", "gs_1"]

P = Z.P
FRONT, BACK = np.array([0, -1.0, 0]), np.array([0, 1.0, 0])
block, slab, band, stone_limb, joint_ring, local_box = RG.block, RG.slab, RG.band, RG.stone_limb, RG.joint_ring, \
    RG.local_box
fy, by = RG.fy, RG.by
chan, addp = SW.chan, SW.addp

zh, zs, zc, zn, zhd = L["hips"], L["spine"], L["chest"], L["neck"], L["head"]
PELV = [(zh - 0.33, 0.5, 0.33, 0.33, 0.0), (zh - 0.18, 0.63, 0.42, 0.4, 0.0), (zh + 0.12, 0.66, 0.43, 0.42, 0.0),
        (zh + 0.26, 0.6, 0.39, 0.38, 0.0)]
ABDO = [(zs - 0.1, 0.5, 0.36, 0.36, 0.0), (zs + 0.05, 0.56, 0.4, 0.39, 0.0), (zs + 0.36, 0.6, 0.43, 0.42, 0.0),
        (zs + 0.47, 0.57, 0.4, 0.4, 0.0)]
CHEST = [(zc - 0.18, 0.62, 0.45, 0.45, 0.0, 0.0), (zc + 0.03, 0.8, 0.55, 0.54, 0.0, -0.015),
         (zc + 0.42, 0.95, 0.62, 0.63, 0.0, -0.03), (zc + 0.8, 1.0, 0.62, 0.66, 0.0, -0.015),
         (zn - 0.06, 0.92, 0.55, 0.62, 0.0, 0.015), (zn + 0.08, 0.66, 0.42, 0.5, 0.0, 0.03)]
HEADB = [(-0.2, 0.26, 0.28, 0.27, 0.0, -0.06), (0.0, 0.31, 0.33, 0.31, 0.0, -0.07), (0.24, 0.33, 0.35, 0.32, 0.0, -0.07),
         (0.36, 0.31, 0.33, 0.3, 0.0, -0.07)]


def seam(pts, nrm, r=0.022, broken=()):
    return chan(pts, nrm, r, broken=broken)


def glow_crack(pts, nrm, r=0.012):
    """A corruption crack with white light deep inside it."""
    pts = np.asarray(pts, float)
    nrm = np.asarray(nrm, float)
    return [GK.rtube(pts - nrm * 0.004, r * 1.8, "BH_Shadow", n=4), GK.rtube(pts - nrm * 0.0, r * 0.55, "BH_Emissive", n=4)]


def front_line(rows, xz, off=0.006):
    return [(x, fy(rows, x, z) - off, z) for x, z in xz]


def back_line(rows, xz, off=0.006):
    return [(x, by(rows, x, z) + off, z) for x, z in xz]


# ================================================================================================= build
def build(body: Body):
    add = body.add
    core_w = GK.zspec_w([(zh + 0.06, "hips"), (zs + 0.06, "spine"), (zc - 0.06, "spine"), (zc + 0.14, "chest")])
    V, F = M.tube([(0, 0.0, zh - 0.08), (0, 0.0, zs), (0, 0.0, zc), (0, 0.0, zc + 0.4)], [(0.44, 0.3)] * 4, n=16,
                  up=(0, -1, 0))
    add(P(V, F, "BH_DarkSteel", "core"), weights=core_w)
    pelvis(body)
    abdomen(body)
    chest(body)
    back_coils(body)
    head(body)
    for s in ("L", "R"):
        arm(body, s)
        leg(body, s)
    hammer_fist(body)
    coil_lance(body)
    chain_spikes(body)


def pelvis(body):
    add = body.add
    add(block(PELV, bev=0.02), "hips")
    add(band(PELV, zh + 0.14, 0.1, 0.018, mat="BH_Gold"), "hips")
    add(band(PELV, zh - 0.12, 0.05, 0.014, mat="BH_Bronze"), "hips")
    # front loin slab with a stepped glyph, tassets per thigh
    c = np.array([0, -0.45, zh - 0.32])
    w = Z.centre_w(zh, zh - 0.9, 0.45)
    add(slab((0.44, 0.12, 0.62), c, R=Rx(6), bev=0.02), weights=w)
    addp(body, seam([c + (-0.12, -0.065, 0.2), c + (-0.12, -0.068, 0.04), c + (0.0, -0.07, 0.04), c + (0, -0.072, -0.2)],
                    FRONT, 0.02), weights=w)
    addp(body, seam([c + (0.12, -0.065, 0.2), c + (0.12, -0.068, 0.04), c + (0.0, -0.07, 0.04)], FRONT, 0.02), weights=w)
    add(slab((0.46, 0.14, 0.05), c + (0, 0, 0.32), R=Rx(6), mat="BH_Gold", bev=0.01), weights=w)
    for sx in (1, -1):
        lb = "thigh.L" if sx > 0 else "thigh.R"
        tw = (lambda V, lb=lb: [{"hips": 0.55, lb: 0.45}] * len(V))
        for (x, y, wd, rz) in ((0.4, -0.36, 0.36, 18), (0.68, -0.02, 0.36, 82)):
            cc = np.array([sx * x, y, zh - 0.3])
            R = Rz(sx * rz) @ Rx(9)
            add(slab((wd, 0.1, 0.46), cc, R=R, bev=0.02), weights=tw)
            add(slab((wd + 0.02, 0.12, 0.05), cc + R @ np.array([0, 0, 0.22]), R=R, mat="BH_Bronze", bev=0.01),
                weights=tw)
            n = R @ np.array([0, -1.0, 0])
            addp(body, seam([cc + R @ np.array([-0.1, -0.055, 0.1]), cc + R @ np.array([0.1, -0.055, 0.1]),
                             cc + R @ np.array([0.1, -0.055, -0.12])], n, 0.018), weights=tw)


def abdomen(body):
    add = body.add
    for k, z in enumerate((zs - 0.02, zs + 0.15, zs + 0.32)):
        rows = [(z - 0.07, 0.5 + 0.03 * k, 0.35 + 0.02 * k, 0.36 + 0.02 * k, 0.0),
                (z + 0.07, 0.52 + 0.03 * k, 0.37 + 0.02 * k, 0.37 + 0.02 * k, 0.0)]
        add(block(rows, mat="BH_Bronze", bev=0.014), "spine")
        add(band(rows, z, 0.03, 0.01, mat="BH_Gold"), "spine")
    addp(body, seam(front_line(ABDO, [(0, zs - 0.08), (0, zs + 0.4)], 0.02), FRONT, 0.02, broken=(0,)), "spine")


def chest(body):
    add = body.add
    add(block(CHEST, bev=0.025), "chest")
    add(band(CHEST, zc - 0.08, 0.1, 0.02, mat="BH_Gold"), "chest")
    add(band(CHEST, zn + 0.04, 0.07, 0.016, mat="BH_Bronze"), "chest")
    # stepped-fret breast band with turquoise rails
    zb = zc + 0.62
    for x0, x1 in ((-0.84, -0.26), (0.26, 0.84)):
        pts = [(x0 + (x1 - x0) * a, fy(CHEST, x0 + (x1 - x0) * a, zb + 0.16 * b) - 0.008, zb + 0.16 * b)
               for a, b in Z.fret_wave(3, steps=2)]
        add(GK.rtube(pts, 0.018, "BH_Shadow", n=4), "chest")
        for zz in (zb - 0.05, zb + 0.21):
            q = [(x, fy(CHEST, x, zz) - 0.004, zz) for x in np.linspace(x0, x1, 9)]
            add(GK.rtube(q, 0.016, "BH_Horn", n=4), "chest")
    # the great glyph eye on the breastbone in a bronze-clamped socket
    ze = zc + 0.36
    ye = fy(CHEST, 0, ze)
    add(GK.blob((0, ye + 0.02, ze), 0.27, "BH_Shadow", scale=(1.3, 0.3, 0.85), n=16, rings=6), "chest")
    eye = [(0.24 * math.cos(a), ye - 0.03, ze + 0.13 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 25)]
    addp(body, seam(eye, FRONT, 0.024), "chest")
    add(GK.blob((0, ye - 0.035, ze), 0.085, "BH_Emissive", scale=(1, 0.45, 1), n=12, rings=6), "chest")
    ring = [(0.34 * math.cos(a), ye - 0.006, ze + 0.22 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 29)]
    V, F = M.tube(ring, [(0.03, 0.03)] * len(ring), n=6, up=(0, -1, 0), cap0=False, cap1=False)
    add(P(V, F, "BH_Gold", "eyering"), "chest")
    for a in (0, 90, 180, 270):
        ra = math.radians(a)
        cc = np.array([0.34 * math.cos(ra), ye - 0.03, ze + 0.22 * math.sin(ra)])
        add(slab((0.1, 0.07, 0.14), cc, R=Ry(-a + 90), mat="BH_Bronze", bev=0.012), "chest")
    # seams radiating from the eye (stepped), one broken by a glowing crack
    for sx in (1, -1):
        addp(body, seam(front_line(CHEST, [(sx * 0.34, ze), (sx * 0.56, ze), (sx * 0.56, zc + 0.12), (sx * 0.74, zc + 0.12)]),
                        FRONT, 0.02, broken=(1,) if sx > 0 else ()), "chest")
        addp(body, seam(front_line(CHEST, [(sx * 0.14, ze - 0.22), (sx * 0.14, zc - 0.02)]), FRONT, 0.02), "chest")
    addp(body, seam(front_line(CHEST, [(0, ze + 0.22), (0, zb - 0.08)]), FRONT, 0.02), "chest")
    # corruption: glowing cracks splitting the stone
    rng_pts = SW.jag((-0.2, 0, zn - 0.05), (-0.52, 0, zc + 0.1), 8, 0.05, FRONT, 11)
    addp(body, glow_crack(front_line(CHEST, [(p[0], p[2]) for p in rng_pts], 0.004), FRONT, 0.014), "chest")
    rng_pts = SW.jag((0.72, 0, zc + 0.9), (0.42, 0, zc + 0.52), 6, 0.04, FRONT, 12)
    addp(body, glow_crack(front_line(CHEST, [(p[0], p[2]) for p in rng_pts], 0.004), FRONT, 0.012), "chest")
    # collar stones round the head
    for sx in (1, -1):
        add(slab((0.34, 0.66, 0.24), (sx * 0.5, 0.04, zn + 0.06), R=Ry(sx * 16), bev=0.02), "chest")
    # back plate (mount for the coils)
    zp = zc + 0.55
    add(slab((1.0, 0.16, 0.9), (0, by(CHEST, 0, zp) - 0.02, zp), bev=0.025), "chest")
    add(slab((1.06, 0.18, 0.08), (0, by(CHEST, 0, zp) - 0.01, zp - 0.43), mat="BH_Gold", bev=0.012), "chest")
    add(slab((1.06, 0.18, 0.08), (0, by(CHEST, 0, zp) - 0.01, zp + 0.43), mat="BH_Gold", bev=0.012), "chest")
    yb = by(CHEST, 0, zp) + 0.065
    addp(body, seam([(-0.38, yb, zp - 0.3), (0.38, yb, zp - 0.3)], BACK, 0.02), "chest")
    addp(body, glow_crack(back_line(CHEST, [(0.62, zc + 0.15), (0.7, zc + 0.3), (0.64, zc + 0.42), (0.74, zc + 0.6)],
                                    0.004), BACK, 0.012), "chest")


def back_coils(body):
    """Three arc coils standing on the back plate, white-hot cores, arcs of current between their crowns."""
    add = body.add
    zp = zc + 0.55
    yb = by(CHEST, 0, zp) + 0.07
    tops = []
    for sx, ln, lean in ((0, 1.9, 0.0), (1, 1.5, 1.0), (-1, 1.5, 1.0)):
        base = np.array([sx * 0.36, yb + 0.06, zp - 0.2 + (0.12 if sx == 0 else 0.0)])
        d = normalize(np.array([sx * 0.3 * lean, 0.3, 1.0]))
        top = base + d * ln
        # bronze foot socket on the plate
        V, F = M.tube([base - d * 0.12, base + d * 0.08], [(0.2, 0.2), (0.17, 0.17)], n=12,
                      up=(1, 0, 0))
        add(P(V, F, "BH_Bronze", "coilfoot"), "chest")
        # the coil: helix round a white weak-point core
        add(Z.coil(base + d * 0.08, top - d * 0.1, 0.15, 14 if sx == 0 else 11, 0.022, "BH_Gold", n=5, pts_per_turn=10),
            "chest")
        V, F = M.tube([base + d * 0.05, top - d * 0.05], [(0.095, 0.095)] * 2, n=12, up=(1, 0, 0))
        add(P(V, F, "BH_WeakPoint", "coilheart"), "chest")
        for u in (0.25, 0.5, 0.75):
            cc = base + (top - base) * u
            V, F = M.tube([cc - d * 0.025, cc + d * 0.025], [(0.19, 0.19)] * 2, n=12, up=(1, 0, 0))
            add(P(V, F, "BH_Bronze", "coilring"), "chest")
        # crown: a bronze disc with prongs, a glowing ball on top
        V, F = M.tube([top - d * 0.06, top + d * 0.04], [(0.22, 0.22), (0.17, 0.17)], n=14, up=(1, 0, 0))
        add(P(V, F, "BH_Bronze", "crown"), "chest")
        side = normalize(np.cross(d, (1, 0, 0)))
        side2 = np.cross(d, side)
        for k in range(4):
            a = 2 * math.pi * k / 4 + 0.4
            o = side * math.cos(a) + side2 * math.sin(a)
            add(A.taper([top + o * 0.15, top + o * 0.2 + d * 0.16], 0.03, 0.008, "BH_Gold", n=5), "chest")
        add(A.ball(top + d * 0.12, 0.085, "BH_WeakPoint", n=10, rings=6), "chest")
        tops.append(top + d * 0.12)
    # arcs of current between the crowns (jagged white bolts)
    for i, j, seed in ((0, 1, 1), (0, 2, 2)):
        a, b = tops[i], tops[j]
        pts = SW.jag(a, b, 7, 0.07, normalize(np.cross(b - a, (0, 1.0, 0))), seed)
        pts = [np.asarray(p) + np.array([0, 0, 0.12 * math.sin(math.pi * t)]) for p, t in zip(pts, np.linspace(0, 1, 7))]
        add(A.tube(pts, 0.014, "BH_Emissive", n=4), "chest")


def head(body):
    add = body.add
    z0 = zhd
    H = [(z0 + r[0], r[1], r[2], r[3], r[4], r[5]) for r in HEADB]
    add(block(H, bev=0.02), "head")
    add(band(H, z0 + 0.02, 0.06, 0.012, mat="BH_Bronze"), "head")
    yf = fy(H, 0, z0 + 0.2)
    # heavy brow and one long visor slit of white light, a channel down to the chin
    add(slab((0.58, 0.12, 0.08), (0, yf - 0.03, z0 + 0.28), R=Rx(-6), bev=0.014), "head")
    add(slab((0.46, 0.04, 0.07), (0, yf + 0.0, z0 + 0.2), mat="BH_Shadow", bev=0.006), "head")
    add(slab((0.4, 0.03, 0.03), (0, yf - 0.012, z0 + 0.2), mat="BH_Emissive", bev=0.006), "head")
    addp(body, seam([(0, yf - 0.006, z0 + 0.15), (0, yf - 0.006, z0 - 0.06)], FRONT, 0.016), "head")
    for sx in (1, -1):
        pts = SW.fret_pts((sx * 0.07, yf - 0.006, z0 - 0.04), (sx * 1.0, 0, 0), (0, 0, 1), 0.17, 0.12, 1, steps=2)
        add(GK.rtube(pts, 0.012, "BH_Shadow", n=4), "head")
        V, F = M.lathe([(0.0, -0.03), (0.11, -0.03), (0.125, 0.0), (0.11, 0.035), (0.0, 0.035)], 14)
        add(P(V, F, "BH_Gold", "earplate").rot(Ry(90 * sx)).move((sx * 0.3, -0.05, z0 + 0.16)), "head")
        add(A.ball((sx * 0.335, -0.05, z0 + 0.16), 0.05, "BH_Horn", n=8, rings=5, scale=(0.45, 1, 1)), "head")
    # the pylon capital: widening stepped courses, a bronze slab, a fret front, a white seam, a cap stone
    top = z0 + 0.36
    for p in SW.stepped_capital((0, -0.06, top), 0.56, 0.56, 0.075, steps=3, grow=0.1, bev=0.014):
        add(p, "head")
    add(slab((0.88, 0.88, 0.05), (0, -0.06, top + 0.25), mat="BH_Gold", bev=0.01), "head")
    add(slab((0.64, 0.64, 0.1), (0, -0.06, top + 0.325), bev=0.016), "head")
    add(slab((0.34, 0.34, 0.07), (0, -0.06, top + 0.41), bev=0.012), "head")
    yc = -0.06 - 0.38
    pts = SW.fret_pts((-0.36, yc - 0.005, top + 0.165), (1, 0, 0), (0, 0, 1), 0.72, 0.06, 5, steps=2)
    add(GK.rtube(pts, 0.011, "BH_Shadow", n=4), "head")
    add(A.tube([(-0.42, -0.06 - 0.443, top + 0.25), (0.42, -0.06 - 0.443, top + 0.25)], 0.014, "BH_Emissive", n=5),
        "head")


def arm(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    sh_b, ua, fa, ha = "shoulder." + s, "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
    add(GK.blob(sh, 0.32, "BH_DarkSteel", n=14, rings=8), ua)
    add(stone_limb(body, ua, [(0.1, 0.25, 0.26), (0.5, 0.27, 0.28), (0.9, 0.24, 0.25)], mat="BH_Bronze"), ua)
    add(stone_limb(body, ua, [(0.25, 0.3, 0.31), (0.5, 0.31, 0.32), (0.72, 0.29, 0.3)]), ua)
    add(joint_ring(sh + (el - sh) * 0.8, el - sh, 0.29, w=0.07, mat="BH_Gold"), ua)
    Ax = body.axes(ua)
    ul = body.p["upper_len"]
    addp(body, seam(body.lpt(ua, [(0.0, u * ul, 0.315) for u in (0.28, 0.5, 0.7)]), Ax[:, 2], 0.02), ua)
    # stepped pylon pauldron (three courses) with a bronze lip
    c = sh + np.array([sx * 0.06, 0.0, 0.26])
    R = Ry(-sx * 13)
    for i, (w, d, h) in enumerate(((0.78, 0.86, 0.22), (0.64, 0.72, 0.14), (0.48, 0.56, 0.12))):
        add(slab((w, d, h), c + R @ np.array([sx * 0.02 * i, 0, 0.16 * i]), R=R, bev=0.022), sh_b)
    add(slab((0.82, 0.9, 0.05), c + R @ np.array([0, 0, -0.13]), R=R, mat="BH_Gold", bev=0.01), sh_b)
    fr = c + R @ np.array([0, -0.435, 0.0])
    pts = SW.fret_pts(fr + R @ np.array([-0.32, 0, -0.07]), R @ np.array([1.0, 0, 0]), R @ np.array([0, 0, 1.0]),
                      0.64, 0.12, 3, steps=2)
    add(GK.rtube(pts, 0.012, "BH_Shadow", n=4), sh_b)
    addp(body, seam([fr + R @ np.array([-0.36, -0.004, 0.09]), fr + R @ np.array([0.36, -0.004, 0.09])],
                    R @ np.array([0, -1.0, 0]), 0.018, broken=(0,) if sx < 0 else ()), sh_b)
    # elbow + forearm (massive, stone bracer)
    add(GK.blob(el, 0.27, "BH_DarkSteel", n=14, rings=8), fa)
    add(stone_limb(body, fa, [(0.05, 0.27, 0.27), (0.5, 0.29, 0.3), (0.95, 0.25, 0.26)], mat="BH_Bronze"), fa)
    add(stone_limb(body, fa, [(0.2, 0.33, 0.34), (0.55, 0.38, 0.38), (0.88, 0.36, 0.36)], p=3.8), fa)
    add(joint_ring(el + (wr - el) * 0.93, wr - el, 0.36, w=0.08, mat="BH_Gold"), fa)
    add(joint_ring(el + (wr - el) * 0.2, wr - el, 0.34, w=0.06, mat="BH_Bronze"), fa)
    Ax = body.axes(fa)
    fl = body.p["fore_len"]
    for dx in (-0.1, 0.1):
        addp(body, seam(body.lpt(fa, [(dx, u * fl, 0.375) for u in (0.32, 0.55, 0.8)]), Ax[:, 2], 0.02,
                        broken=(1,) if dx > 0 and sx > 0 else ()), fa)
    addp(body, glow_crack(body.lpt(fa, [(0.32, 0.4 * fl, -0.14), (0.35, 0.5 * fl, -0.1), (0.33, 0.62 * fl, -0.16),
                                        (0.36, 0.72 * fl, -0.12)]), -Ax[:, 2], 0.012), fa)


def hammer_fist(body):
    """The right forearm ends in a hammer-fist: a huge banded stone block with a glyph face, rigid to hand.R
    (bone-local: x across, y along the hand, z = back of the hand)."""
    add = body.add
    ha = "hand.R"
    Ax = body.axes(ha)
    add(local_box(body, ha, (0.5, 0.18, 0.5), (0, 0.04, 0), mat="BH_Bronze", bev=0.02), ha)
    add(local_box(body, ha, (0.72, 0.62, 0.66), (0, 0.42, 0), bev=0.035), ha)
    for y in (0.2, 0.62):
        add(local_box(body, ha, (0.76, 0.07, 0.7), (0, y, 0), mat="BH_Gold", bev=0.012), ha)
    # striking face (distal, +y): stepped boss with a glyph and white seams
    add(local_box(body, ha, (0.56, 0.08, 0.5), (0, 0.76, 0), bev=0.02), ha)
    add(local_box(body, ha, (0.36, 0.06, 0.32), (0, 0.82, 0), bev=0.016), ha)
    yface = 0.855
    nrm = Ax[:, 1]
    sq = [(-0.11, yface, -0.1), (-0.11, yface, 0.1), (0.11, yface, 0.1), (0.11, yface, -0.1), (-0.05, yface, -0.1),
          (-0.05, yface, 0.04), (0.05, yface, 0.04)]
    addp(body, seam(body.lpt(ha, sq), nrm, 0.016), ha)
    # studs on the sides, a seam round the block
    for sxx in (1, -1):
        for y in (0.32, 0.52):
            for z in (-0.2, 0.0, 0.2):
                q = body.lpt(ha, [(sxx * 0.365, y, z)])[0]
                add(A.ball(q, 0.035, "BH_Gold", n=6, rings=4), ha)
    for zz in (0.335, -0.335):
        pts = body.lpt(ha, [(-0.3, 0.42, zz), (0.0, 0.42, zz), (0.3, 0.42, zz)])
        addp(body, seam(pts, Ax[:, 2] * np.sign(zz), 0.018), ha)
    addp(body, glow_crack(body.lpt(ha, [(-0.25, 0.3, 0.335), (-0.15, 0.4, 0.335), (-0.2, 0.5, 0.335), (-0.08, 0.6, 0.335)]),
                          Ax[:, 2], 0.012), ha)


def coil_lance(body):
    """The left forearm ends in a coil-lance: a socket block, a long bronze shaft wound with two coils, a white
    emitter fork at the tip (rigid to hand.L)."""
    add = body.add
    ha = "hand.L"
    Ax = body.axes(ha)
    d = Ax[:, 1]
    add(local_box(body, ha, (0.5, 0.32, 0.5), (0, 0.1, 0), bev=0.03), ha)
    add(local_box(body, ha, (0.54, 0.06, 0.54), (0, 0.25, 0), mat="BH_Gold", bev=0.01), ha)
    o = body.head(ha)
    pts = [o + d * 0.25, o + d * 0.55, o + d * 1.1, o + d * 1.35]
    V, F = M.tube(pts, [(0.13, 0.13), (0.12, 0.12), (0.09, 0.09), (0.07, 0.07)], n=12, up=tuple(Ax[:, 2]))
    add(P(V, F, "BH_Bronze", "shaft"), ha)
    for a, b in ((0.38, 0.72), (0.82, 1.08)):
        for prt in SW.coil_stud(o + d * a, o + d * b, 0.19 if a < 0.5 else 0.15, 0.022, turns=6, core=False):
            add(prt, ha)
        V, F = M.tube([o + d * (a + 0.02), o + d * (b - 0.02)], [(0.135 if a < 0.5 else 0.105,) * 2] * 2, n=12,
                      up=tuple(Ax[:, 2]))
        add(P(V, F, "BH_Emissive", "lanceglow"), ha)
    # emitter fork: three bronze prongs round a white spike
    tip = o + d * 1.35
    for k in range(3):
        a = 2 * math.pi * k / 3
        off = Ax[:, 0] * math.cos(a) + Ax[:, 2] * math.sin(a)
        add(A.taper([tip - d * 0.05 + off * 0.07, tip + d * 0.14 + off * 0.15, tip + d * 0.3 + off * 0.09], 0.035, 0.01,
                    "BH_Gold", n=5), ha)
    add(A.shard(tip - d * 0.02, d, 0.4, 0.055, "BH_Emissive", sides=6), ha)
    add(A.ball(tip + d * 0.02, 0.1, "BH_Bronze", n=10, rings=6), ha)


def leg(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    th, sh, ft, toe = "thigh." + s, "shin." + s, "foot." + s, "toe." + s
    hip, k, a = body.head(th), body.head(sh), body.tail(sh)
    add(GK.blob(hip, 0.32, "BH_DarkSteel", n=14, rings=8), th)
    add(stone_limb(body, th, [(0.05, 0.31, 0.32), (0.5, 0.34, 0.35), (0.92, 0.3, 0.31)], mat="BH_Bronze"), th)
    add(stone_limb(body, th, [(0.18, 0.36, 0.37), (0.45, 0.38, 0.39), (0.72, 0.35, 0.36)]), th)
    add(joint_ring(hip + (k - hip) * 0.82, k - hip, 0.34, w=0.08, mat="BH_Gold"), th)
    add(GK.blob(k + (0, -0.03, 0), 0.29, "BH_DarkSteel", n=14, rings=8), sh)
    add(stone_limb(body, sh, [(0.06, 0.3, 0.31), (0.4, 0.34, 0.35), (0.85, 0.36, 0.37), (1.0, 0.33, 0.34)]), sh)
    add(joint_ring(k + (a - k) * 0.7, a - k, 0.38, w=0.09, mat="BH_Gold"), sh)
    add(slab((0.44, 0.14, 0.34), k + (0, -0.3, 0.0), R=Rx(-8), bev=0.025), sh)
    addp(body, seam([k + (-0.1, -0.38, 0.08), k + (0.0, -0.385, -0.06), k + (0.1, -0.38, 0.08)], FRONT, 0.02), sh)
    addp(body, seam([k + (0, -0.36, -0.28), a + (0, -0.37, 0.3)], FRONT, 0.02, broken=(0,) if sx > 0 else ()), sh)
    addp(body, glow_crack([k + (sx * 0.3, -0.18, -0.2), k + (sx * 0.33, -0.15, -0.3), k + (sx * 0.31, -0.17, -0.42)],
                          np.array([sx * 0.6, -0.8, 0.0]), 0.012), sh)
    hx = body.p["hip_x"] * sx
    add(slab((0.62, 0.74, 0.24), (hx, -0.05, 0.12), bev=0.04), ft)
    add(slab((0.58, 0.12, 0.16), (hx, -0.34, 0.26), R=Rx(-30), mat="BH_Gold", bev=0.014), ft)
    add(slab((0.58, 0.28, 0.17), (hx, -0.5, 0.085), bev=0.03), toe)


def chain_spikes(body):
    """Two Kharvenn rune-chain spikes driven into it (right pauldron, back), snapped chains hanging."""
    add = body.add
    sh = body.head("upper_arm.R")
    base = sh + np.array([-0.12, -0.2, 0.5])
    d = normalize(np.array([0.3, -0.5, 0.8]))
    add(A.taper([base - d * 0.15, base + d * 0.35], 0.06, 0.02, "BH_Steel", n=6), "shoulder.R")
    add(A.ball(base + d * 0.35, 0.05, "BH_Steel", n=6, rings=4), "shoulder.R")
    for p in SW.chain_links([base + d * 0.25, base + d * 0.3 + (0.0, -0.15, -0.25), base + (0.05, -0.32, -0.75)],
                            link=0.11, r=0.016):
        add(p, "shoulder.R")
    zb = zc + 0.18
    base = np.array([-0.5, by(CHEST, -0.5, zb), zb])
    d = normalize(np.array([-0.3, 0.8, 0.4]))
    add(A.taper([base - d * 0.15, base + d * 0.32], 0.06, 0.02, "BH_Steel", n=6), "chest")
    for p in SW.chain_links([base + d * 0.25, base + d * 0.35 + (0, 0.05, -0.3), base + (-0.08, 0.3, -0.9)],
                            link=0.11, r=0.016):
        add(p, weights=GK.zspec_w([(zs, "spine"), (zc + 0.1, "chest")]))
