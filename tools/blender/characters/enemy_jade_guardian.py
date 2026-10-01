"""Jade Guardian (bh-029, Builder M5, Zarael / the Jade Sepulchre shield tank): a ~2.2 m statue warrior carved from
one block of jade, set at the king's door and woken by the wire laid down its spine. A stern carved face (heavy brow,
broad nose, set lips) with slits of white light for eyes under a crest helm: a gold brow band, jade ear spools and a
fan of carved stone feathers. A carved quilted cuirass (ridged courses edged in gold) with a turquoise mosaic
pectoral round a white-lit glyph disc; round shoulder discs with turquoise rims; a skirt of jade slabs with a carved
fret; smooth statue limbs with gold arm rings, carved bracers and greaves; sandalled slab feet. Down its back the
white wire spine runs in a carved channel from the nape to the hips. The Blackwire's damage is in the stone: dark
cracks across the breast and thigh and a broken-off corner of the shield.

Left hand (weapon.L, face -Y): a square shield of jade in a gold frame, a turquoise mosaic border, a carved stepped
spiral with a white channel and a glyph eye. Right hand (weapon.R): a long stone spear, a dark jade shaft in gold
bands with a broad carved jade leaf blade and a white channel up its spine.

Built at true size on the shared skeleton (proportions x1.2, broad shoulders). Clips: shield_bash spear_1
spear_heavy (+ spear_2, the enemy base set)."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, fist  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as GK  # noqa: E402
import enemy_rune_golem as RG  # noqa: E402
import enemy_bandit_cutthroat as KB  # noqa: E402
import enemy_glyphbound_warrior as Z  # noqa: E402
import enemy_span_warden as SW  # noqa: E402
import enemy_jade_sleeper as J  # noqa: E402
import kit_a_common as A  # noqa: E402

S = 1.2
PROPS = proportions(S, shoulder_x=0.25, hip_x=0.12, upper_len=0.33, fore_len=0.31, hand_len=0.115, grip_x=0.085,
                    clav_x0=0.05, clav_drop=0.06)
L = GK.levels(PROPS)
PREVIEW_HEIGHT = 2.6
PALETTE = "jade_guardian"
PALETTE_COLORS = {
    "BH_Stone": ((0.12, 0.4, 0.29), 0.0, 0.3, None, 0.0, 1.0),             # polished jade (the statue)
    "BH_Horn": ((0.045, 0.18, 0.13), 0.0, 0.4, None, 0.0, 1.0),           # dark jade (core, shaft, recesses)
    "BH_Bronze": ((0.1, 0.48, 0.46), 0.0, 0.3, None, 0.0, 1.0),           # turquoise mosaic
    "BH_Gold": ((0.74, 0.52, 0.2), 1.0, 0.32, None, 0.0, 1.0),            # gold bands / frames
    "BH_Shadow": ((0.012, 0.02, 0.016), 0.0, 0.85, None, 0.0, 1.0),       # carved grooves / cracks
    "BH_Emissive": J.WHITE_GLOW,                                           # the wire spine, eyes, channels
}
CLIPS = ["shield_bash", "spear_1", "spear_heavy", "spear_2"]

P = Z.P
FRONT, BACK = np.array([0, -1.0, 0]), np.array([0, 1.0, 0])
block, slab, band, stone_limb, joint_ring = RG.block, RG.slab, RG.band, RG.stone_limb, RG.joint_ring
fy, by = RG.fy, RG.by
chan, crack, jag, addp = SW.chan, SW.crack, SW.jag, SW.addp


def finish_mesh(mesh_ob):
    KB.enable_weapon_deform(mesh_ob)


zh, zs, zc, zn, zhd = L["hips"], L["spine"], L["chest"], L["neck"], L["head"]
PELV = [(zh - 0.12, 0.16, 0.12, 0.12, 0.0), (zh - 0.03, 0.19, 0.135, 0.14, 0.0), (zh + 0.08, 0.19, 0.135, 0.14, 0.0),
        (zh + 0.14, 0.175, 0.125, 0.13, 0.0)]
ABDO = [(zs - 0.03, 0.165, 0.12, 0.12, 0.0), (zs + 0.1, 0.17, 0.125, 0.12, 0.0), (zs + 0.2, 0.19, 0.13, 0.125, 0.0)]
CHEST = [(zc - 0.06, 0.2, 0.14, 0.135, 0.0, 0.0), (zc + 0.06, 0.24, 0.165, 0.15, 0.0, -0.005),
         (zc + 0.18, 0.275, 0.18, 0.165, 0.0, -0.01), (zn - 0.05, 0.28, 0.17, 0.17, 0.0, 0.0),
         (zn + 0.02, 0.22, 0.13, 0.15, 0.0, 0.01), (zn + 0.07, 0.12, 0.09, 0.1, 0.0, 0.01)]
HEADB = [(-0.06, 0.07, 0.075, 0.075, 0.0, -0.01), (0.0, 0.085, 0.095, 0.09, 0.0, -0.015),
         (0.1, 0.095, 0.105, 0.1, 0.0, -0.015), (0.18, 0.09, 0.1, 0.095, 0.0, -0.01), (0.23, 0.07, 0.08, 0.08, 0.0, 0.0)]


def build(body: Body):
    add = body.add
    core_w = GK.zspec_w([(zh + 0.04, "hips"), (zs + 0.04, "spine"), (zc - 0.04, "spine"), (zc + 0.08, "chest")])
    V, F = M.tube([(0, 0.0, zh - 0.05), (0, 0.0, zs), (0, 0.0, zc), (0, 0.0, zc + 0.15)], [(0.14, 0.1)] * 4, n=14,
                  up=(0, -1, 0))
    add(P(V, F, "BH_Horn", "core"), weights=core_w)
    pelvis(body)
    abdomen(body)
    chest(body)
    spine_wire(body)
    head(body)
    for s in ("L", "R"):
        arm(body, s)
        leg(body, s)
    for p in square_shield():
        add(KB.to_socket(body, "L", p), "weapon.L")
    for p in stone_spear():
        add(KB.to_socket(body, "R", p), "weapon.R")


def pelvis(body):
    add = body.add
    add(block(PELV, p=3.0, bev=0.01), "hips")
    add(band(PELV, zh + 0.11, 0.045, 0.01, mat="BH_Gold", p=3.0), "hips")
    # skirt of jade slabs: front / back aprons + side slabs per thigh, a carved fret on the front apron
    for front in (True, False):
        y = -0.15 if front else 0.155
        c = np.array([0, y, zh - 0.15])
        w = Z.centre_w(zh, zh - 0.32, 0.45)
        add(slab((0.2, 0.045, 0.32), c, R=Rx(8 if front else -8), bev=0.012), weights=w)
        add(slab((0.21, 0.05, 0.03), c + (0, 0, -0.16), R=Rx(8 if front else -8), mat="BH_Gold", bev=0.006),
            weights=w)
        if front:
            pts = SW.fret_pts(c + (-0.08, -0.03, -0.1), (1, 0, 0), (0, 0, 1), 0.16, 0.05, 2, steps=2)
            add(GK.rtube(pts, 0.0045, "BH_Shadow", n=4), weights=w)
            addp(body, chan([c + (0, -0.027, 0.13), c + (0, -0.03, -0.02)], FRONT, 0.008), weights=w)
    for sx in (1, -1):
        lb = "thigh.L" if sx > 0 else "thigh.R"
        tw = (lambda V, lb=lb: [{"hips": 0.6, lb: 0.4}] * len(V))
        for (x, y, rz) in ((0.14, -0.1, 30), (0.2, 0.04, 80)):
            cc = np.array([sx * x, y, zh - 0.13])
            R = Rz(sx * rz) @ Rx(7)
            add(slab((0.14, 0.04, 0.26), cc, R=R, bev=0.01), weights=tw)
            add(slab((0.15, 0.045, 0.025), cc + R @ np.array([0, 0, -0.13]), R=R, mat="BH_Bronze", bev=0.005),
                weights=tw)


def abdomen(body):
    add = body.add
    for k, z in enumerate((zs + 0.0, zs + 0.09, zs + 0.18)):
        rows = [(z - 0.042, 0.16 + 0.012 * k, 0.115 + 0.006 * k, 0.115 + 0.006 * k, 0.0),
                (z + 0.042, 0.165 + 0.012 * k, 0.12 + 0.006 * k, 0.118 + 0.006 * k, 0.0)]
        add(block(rows, p=2.6, bev=0.012), "spine")


def chest(body):
    add = body.add
    add(block(CHEST, p=2.8, bev=0.014), "chest")
    # carved quilting: proud ridges across the cuirass, the lowest edged in gold
    for k, z in enumerate((zc + 0.0, zc + 0.08, zc + 0.16)):
        add(band(CHEST, z, 0.022, 0.008, mat="BH_Gold" if k == 0 else "BH_Stone", p=2.8), "chest")
    add(band(CHEST, zn + 0.03, 0.035, 0.008, mat="BH_Gold", p=2.8), "chest")
    # turquoise mosaic pectoral (an arc of tiles) round a jade glyph disc with a white core
    zp = zc + 0.27
    for k in range(13):
        a = math.radians(200 + 140 * k / 12)
        for r, mat in ((0.12, "BH_Bronze"), (0.155, "BH_Gold" if k % 2 else "BH_Bronze")):
            x, z = r * math.cos(a), zp + 0.05 + r * math.sin(a) * 0.9
            yy = fy(CHEST, x, z) - 0.006
            add(slab((0.034, 0.012, 0.03), (x, yy, z), R=Ry(-math.degrees(a) - 90), mat=mat, bev=0.003), "chest")
    ye = fy(CHEST, 0, zp)
    V, F = M.lathe([(0.0, -0.012), (0.06, -0.012), (0.066, 0.0), (0.06, 0.016), (0.0, 0.018)], 18)
    add(P(V, F, "BH_Stone", "disc").rot(Rx(90)).move((0, ye - 0.01, zp)), "chest")
    eye = [(0.042 * math.cos(a), ye - 0.03, zp + 0.026 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 15)]
    addp(body, chan(eye, FRONT, 0.006), "chest")
    add(A.ball((0, ye - 0.03, zp), 0.016, "BH_Emissive", n=8, rings=4, scale=(1, 0.5, 1)), "chest")
    # corruption cracks across the right breast
    add(crack(RG.surf_front(CHEST, [(-0.1, zn - 0.03), (-0.14, zc + 0.24), (-0.11, zc + 0.18), (-0.19, zc + 0.1)]),
              FRONT, 0.007), "chest")
    add(crack(RG.surf_front(CHEST, [(0.2, zc + 0.12), (0.23, zc + 0.05), (0.2, zc - 0.02)]), FRONT, 0.005), "chest")
    # collar stones
    for sx in (1, -1):
        add(slab((0.11, 0.2, 0.06), (sx * 0.15, 0.0, zn + 0.035), R=Ry(sx * 14), bev=0.012), "chest")


def spine_wire(body):
    """The wire laid down its spine: a carved channel on the back from the nape to the pelvis, white."""
    w = GK.zspec_w([(zh + 0.04, "hips"), (zs + 0.04, "spine"), (zc - 0.04, "spine"), (zc + 0.08, "chest")])
    pts = RG.surf_back(CHEST, [(0, zn + 0.02), (0, zc + 0.2), (0, zc)], -0.002)
    addp(body, chan(pts, BACK, 0.012), "chest")
    rows_abd = ABDO
    pts = [(0, by([r + (0.0,) for r in rows_abd], 0, z) + 0.02, z) for z in (zc - 0.02, zs + 0.12, zs - 0.02)]
    addp(body, chan(pts, BACK, 0.012), weights=w)
    pts = [(0, by(PELV, 0, z) + 0.004, z) for z in (zh + 0.12, zh - 0.06)]
    addp(body, chan(pts, BACK, 0.012), "hips")
    # vertebra studs along the channel
    for z in np.linspace(zc + 0.03, zn - 0.02, 5):
        add_y = by(CHEST, 0, z) + 0.004
        body.add(A.ball((0, add_y, z), 0.022, "BH_Gold", n=8, rings=4, scale=(1.4, 0.5, 0.6)), "chest")


def head(body):
    add = body.add
    z0 = zhd
    H = [(z0 + r[0], r[1], r[2], r[3], r[4], r[5]) for r in HEADB]
    add(block(H, p=2.4, bev=0.008), "head")
    yf = fy(H, 0, z0 + 0.08)
    # carved face: brow, nose, lips, cheekbones; white eye slits
    add(GK.rtube([(-0.07, yf + 0.004, z0 + 0.125), (0.0, yf - 0.012, z0 + 0.13), (0.07, yf + 0.004, z0 + 0.125)],
                 0.016, "BH_Stone", n=6), "head")
    add(GK.rtube([(0, yf - 0.01, z0 + 0.12), (0, yf - 0.03, z0 + 0.07), (0, yf - 0.026, z0 + 0.055)],
                 [0.011, 0.018, 0.016], "BH_Stone", n=6), "head")
    add(GK.rtube([(-0.03, yf - 0.006, z0 + 0.03), (0.0, yf - 0.012, z0 + 0.026), (0.03, yf - 0.006, z0 + 0.03)],
                 [0.008, 0.011, 0.008], "BH_Stone", n=5), "head")
    add(GK.rtube([(-0.028, yf - 0.012, z0 + 0.021), (0.028, yf - 0.012, z0 + 0.021)], 0.0035, "BH_Shadow", n=4), "head")
    for sx in (1, -1):
        add(A.ball((sx * 0.035, yf - 0.002, z0 + 0.1), 0.02, "BH_Shadow", n=8, rings=4, scale=(1.3, 0.5, 0.55)), "head")
        add(A.ball((sx * 0.035, yf - 0.009, z0 + 0.1), 0.012, "BH_Emissive", n=8, rings=4, scale=(1.5, 0.4, 0.45)),
            "head")
        add(A.ball((sx * 0.06, yf + 0.006, z0 + 0.07), 0.022, "BH_Stone", n=6, rings=4, scale=(0.8, 0.5, 1.0)), "head")
        # ear spools
        V, F = M.lathe([(0.0, -0.012), (0.04, -0.012), (0.045, 0.0), (0.04, 0.014), (0.0, 0.014)], 12)
        add(P(V, F, "BH_Gold", "spool").rot(Ry(90 * sx)).move((sx * 0.1, 0.0, z0 + 0.09)), "head")
        add(A.ball((sx * 0.115, 0.0, z0 + 0.09), 0.02, "BH_Bronze", n=8, rings=4, scale=(0.4, 1, 1)), "head")
    # crest helm: cap over the skull, gold brow band, carved stone feathers fanning up and back
    V, F = M.lathe([(0.0, 0.262), (0.05, 0.255), (0.088, 0.225), (0.104, 0.18), (0.108, 0.14), (0.108, 0.13)], 18,
                   cap=False)
    add(M.solidify(P(V, F, "BH_Stone", "helm").scale((1.0, 1.08, 1.0)).move((0, -0.006, z0)), 0.012, offset=1),
        "head")
    V, F = M.lathe([(0.112, 0.125), (0.12, 0.13), (0.12, 0.162), (0.112, 0.166)], 18, cap=False)
    add(P(V, F, "BH_Gold", "browband").scale((1.0, 1.08, 1.0)).move((0, -0.006, z0)), "head")
    for k in range(9):
        a = 2 * math.pi * k / 9 - math.pi / 2
        add(A.ball((0.123 * math.cos(a), -0.006 + 0.13 * math.sin(a), z0 + 0.146), 0.012, "BH_Bronze", n=6, rings=3,
                   scale=(1, 1, 1.2)), "head")
    base = np.array([0.0, 0.03, z0 + 0.26])
    tb = math.radians(25)
    n = 9
    for i in range(n):
        a = math.radians(-75 + 150 * i / (n - 1))
        d = np.array([math.sin(a), math.sin(tb) * math.cos(a), math.cos(tb) * math.cos(a)])
        tng = np.array([math.cos(a), -math.sin(tb) * math.sin(a), -math.cos(tb) * math.sin(a)])
        ln = 0.24 + 0.08 * math.cos(a) ** 2
        fe = Z.feather(base + d * 0.02, d, ln, 0.07, "BH_Stone", side=tng, bend=0.02, k=7, thick=0.014)
        add(fe, "head")
        # a carved quill groove down each stone feather
        nrm = np.cross(d, tng)
        add(GK.rtube([base + d * 0.05 + nrm * 0.008, base + d * (ln * 0.9) + nrm * 0.01], 0.0035, "BH_Shadow", n=4),
            "head")
    V, F = M.lathe([(0.0, -0.03), (0.036, -0.03), (0.042, 0.0), (0.03, 0.03), (0.0, 0.034)], 10)
    add(P(V, F, "BH_Gold", "holder").scale((1.5, 1.0, 1.0)).move(base), "head")


def arm(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    sh_b, ua, fa, ha = "shoulder." + s, "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
    add(GK.blob(sh, 0.09, "BH_Stone", n=12, rings=7), ua)
    add(stone_limb(body, ua, [(0.04, 0.072, 0.074), (0.45, 0.078, 0.08), (0.95, 0.066, 0.066)], p=2.2), ua)
    add(joint_ring(sh + (el - sh) * 0.55, el - sh, 0.083, w=0.03, mat="BH_Gold"), ua)
    # round shoulder disc: a domed jade plate with a turquoise rim and a white glyph dot
    c = sh + np.array([sx * 0.03, 0.0, 0.07])
    V, F = M.lathe([(0.0, 0.05), (0.06, 0.045), (0.11, 0.025), (0.13, 0.0), (0.13, -0.02), (0.0, -0.02)], 20)
    add(M.bevel(P(V, F, "BH_Stone", "pauldron").rot(Ry(-sx * 22)).move(c), 0.006, 1), sh_b)
    ring = [c + Ry(-sx * 22) @ np.array([0.128 * math.cos(a), 0.128 * math.sin(a), 0.0]) for a in
            np.linspace(0, 2 * math.pi, 25)]
    add(GK.rtube(ring, 0.014, "BH_Bronze", n=5), sh_b)
    add(A.ball(c + Ry(-sx * 22) @ np.array([0, 0, 0.05]), 0.016, "BH_Emissive", n=8, rings=4, scale=(1, 1, 0.5)), sh_b)
    # forearm with a carved bracer and a white channel
    add(GK.blob(el, 0.07, "BH_Stone", n=12, rings=6), fa)
    add(stone_limb(body, fa, [(0.04, 0.064, 0.066), (0.5, 0.068, 0.07), (0.95, 0.052, 0.054)], p=2.2), fa)
    add(stone_limb(body, fa, [(0.32, 0.08, 0.083), (0.55, 0.085, 0.088), (0.88, 0.072, 0.075)], p=3.4), fa)
    add(joint_ring(el + (wr - el) * 0.9, wr - el, 0.077, w=0.022, mat="BH_Gold"), fa)
    Ax = body.axes(fa)
    fl = body.p["fore_len"]
    addp(body, chan(body.lpt(fa, [(0.0, 0.36 * fl, 0.087), (0.0, 0.84 * fl, 0.077)]), Ax[:, 2], 0.007), fa)
    for prt in fist(body, s, "BH_Stone", "BH_Stone", gauntlet=False, scale=1.35):
        add(prt, ha)


def leg(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    th, sh, ft, toe = "thigh." + s, "shin." + s, "foot." + s, "toe." + s
    hip, k, a = body.head(th), body.head(sh), body.tail(sh)
    add(GK.blob(hip, 0.1, "BH_Stone", n=12, rings=7), th)
    add(stone_limb(body, th, [(0.04, 0.1, 0.105), (0.45, 0.1, 0.106), (0.95, 0.075, 0.08)], p=2.2), th)
    add(GK.blob(k + (0, -0.01, 0), 0.08, "BH_Stone", n=12, rings=7), sh)
    add(stone_limb(body, sh, [(0.06, 0.07, 0.074), (0.4, 0.075, 0.08), (0.95, 0.055, 0.058)], p=2.2), sh)
    # greave (front + sides) with a white channel and a gold rim; knee disc
    add(stone_limb(body, sh, [(0.18, 0.088, 0.094), (0.45, 0.092, 0.1), (0.82, 0.078, 0.082)], p=3.2), sh)
    add(joint_ring(k + (a - k) * 0.84, a - k, 0.08, w=0.018, mat="BH_Gold"), sh)
    V, F = M.lathe([(0.0, 0.02), (0.05, 0.016), (0.065, 0.0), (0.0, -0.01)], 14)
    add(P(V, F, "BH_Stone", "knee").rot(Rx(90)).move(k + (0, -0.075, 0.0)), sh)
    addp(body, chan([k + (0, -0.1, -0.1), a + (0, -0.09, 0.14)], FRONT, 0.007, broken=(0,) if sx < 0 else ()), sh)
    if sx > 0:
        add(crack([hip + (0.05, -0.1, -0.08), hip + (0.07, -0.098, -0.16), hip + (0.05, -0.099, -0.22)], FRONT, 0.005),
            th)
    # sandalled slab foot: a jade sole, carved toes, gold strap
    hx = body.p["hip_x"] * sx
    add(slab((0.14, 0.24, 0.07), (hx, -0.045, 0.035), bev=0.018), ft)
    add(slab((0.15, 0.03, 0.05), (hx, -0.1, 0.085), R=Rx(-35), mat="BH_Gold", bev=0.006), ft)
    add(slab((0.13, 0.1, 0.055), (hx, -0.19, 0.03), bev=0.016), toe)
    for k2 in range(4):
        add(GK.rtube([(hx - 0.045 + 0.03 * k2, -0.22, 0.05), (hx - 0.045 + 0.03 * k2, -0.24, 0.015)], 0.004,
                     "BH_Shadow", n=4), toe)


# ================================================================================================= weapons
def square_shield():
    """Square shield (weapon space: handle at origin, face -Y, +Z up): ~0.78 m. A jade slab in a gold frame, a
    turquoise mosaic border, a carved stepped spiral (square fret) with a white channel ending in a glyph eye, the
    lower right corner broken off."""
    parts = []
    hw = 0.39
    yf = -0.09
    th = 0.06
    o = np.array([(hw, -hw), (hw, hw), (-hw, hw), (-hw, -hw + 0.1), (-hw + 0.1, -hw)])  # chipped corner (-x, -z)
    V, F = M.prism(o[::-1] if 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1]) < 0 else o,
                   th, axis="y", center=yf + th / 2)
    parts.append(M.bevel(P(V, F, "BH_Stone", "slab"), 0.01, 1, angle=35))
    # gold frame along the edges (except the broken corner)
    for a, b in (((hw, -hw), (hw, hw)), ((hw, hw), (-hw, hw)), ((-hw, hw), (-hw, -hw + 0.12)),
                 ((-hw + 0.12, -hw), (hw, -hw))):
        parts.append(A.tube([(a[0], yf - 0.004, a[1]), (b[0], yf - 0.004, b[1])], (0.02, 0.018), "BH_Gold", n=5,
                            up=(0, -1, 0)))
    parts.append(GK.rtube([(-hw, yf - 0.002, -hw + 0.1), (-hw + 0.03, yf - 0.002, -hw + 0.06),
                           (-hw + 0.06, yf - 0.002, -hw + 0.04), (-hw + 0.1, yf - 0.002, -hw)], 0.008, "BH_Shadow", n=4))
    # turquoise mosaic border (tiles in a square ring)
    for i in range(14):
        t = (i + 0.5) / 14
        x = -0.3 + 0.6 * t
        for (px, pz) in ((x, 0.31), (0.31, -x), (-x, -0.31), (-0.31, x)):
            if px < -0.22 and pz < -0.22:
                continue
            V, F = M.box(0.036, 0.008, 0.036)
            parts.append(P(V, F, "BH_Bronze" if i % 3 else "BH_Gold", "tile").move((px, yf - 0.004, pz)))
    # carved stepped square spiral (a square fret) with the white current in its groove
    sp = [(-0.2, -0.2), (0.2, -0.2), (0.2, 0.2), (-0.14, 0.2), (-0.14, -0.13), (0.13, -0.13), (0.13, 0.13),
          (-0.07, 0.13), (-0.07, -0.06), (0.06, -0.06), (0.06, 0.06), (0.0, 0.06)]
    pts = [(x, yf - 0.003, z) for x, z in sp]
    parts += chan(pts, np.array([0, -1.0, 0]), 0.009, broken=(2,))
    parts.append(A.ball((0.0, yf - 0.012, 0.0), 0.028, "BH_Emissive", n=8, rings=4, scale=(1, 0.45, 1)))
    parts.append(A.ball((0.0, yf + 0.002, 0.0), 0.05, "BH_Shadow", n=8, rings=4, scale=(1.2, 0.25, 0.9)))
    # a crack across the upper left
    parts.append(crack(jag((-0.36, yf - 0.001, 0.1), (-0.12, yf - 0.001, 0.36), 6, 0.02, (0, -1.0, 0), 5),
                       np.array([0, -1.0, 0]), 0.006))
    # back: gold cross bars, grip
    for z in (-0.22, 0.22):
        parts.append(slab((0.6, 0.025, 0.04), (0, yf + th + 0.01, z), mat="BH_Gold", bev=0.005))
    V, F = M.tube([(-0.08, -0.03, 0.0), (-0.05, 0.02, 0.0), (0.05, 0.02, 0.0), (0.08, -0.03, 0.0)],
                  [(0.016, 0.035)] * 4, n=6, up=(0, 0, 1))
    parts.append(P(V, F, "BH_Gold", "handle"))
    return parts


def stone_spear():
    """Long stone spear (weapon space: grip at origin, +Z to the point). Shaft -0.95..1.3 of dark jade with gold bands
    and a turquoise grip collar; a broad carved jade leaf blade 1.3..1.78 with a white channel up its spine; a gold
    socket with a feather tassel."""
    parts = []
    parts.append(A.tube([(0, 0, -0.95), (0, 0, 1.32)], [0.022, 0.02], "BH_Horn", n=8))
    for z in (-0.92, -0.5, 0.25, 0.75, 1.22):
        V, F = M.lathe([(0.0, z - 0.018), (0.026, z - 0.018), (0.028, z), (0.026, z + 0.018), (0.0, z + 0.018)], 8)
        parts.append(P(V, F, "BH_Gold", "band"))
    parts.append(Z.coil((0, 0, -0.12), (0, 0, 0.14), 0.024, 6, 0.004, "BH_Bronze", n=4, pts_per_turn=8))
    V, F = M.lathe([(0.0, -1.08), (0.01, -1.08), (0.026, -1.0), (0.024, -0.95), (0.0, -0.95)], 8)
    parts.append(P(V, F, "BH_Stone", "butt"))
    # socket
    V, F = M.lathe([(0.0, 1.26), (0.03, 1.26), (0.036, 1.3), (0.03, 1.34), (0.0, 1.34)], 10)
    parts.append(P(V, F, "BH_Gold", "socket"))
    # leaf blade (flat in the XZ plane, flats +-Y)
    zs = np.linspace(1.33, 1.78, 12)

    def hw(z):
        t = (z - 1.33) / 0.45
        return 0.025 + 0.06 * math.sin(math.pi * min(t * 1.35, 1.0)) * (1 - t) ** 0.4

    o = [(hw(z), z) for z in zs] + [(0.0, 1.83)] + [(-hw(z), z) for z in zs[::-1]]
    o = np.array(o)
    if 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1]) < 0:
        o = o[::-1]
    V, F = M.prism(o, 0.026, axis="y")
    bl = P(V, F, "BH_Stone", "blade")
    bl.warp(lambda v: (v[0], v[1] * (1.0 - 0.8 * min(abs(v[0]) / 0.085, 1.0) ** 1.4), v[2]))
    parts.append(M.bevel(bl, 0.003, 1, angle=40))
    for sy in (1, -1):
        parts += chan([(0, sy * 0.013, 1.36), (0, sy * 0.013, 1.72)], (0, sy, 0), 0.006)
    # feather tassel under the socket
    for k in range(3):
        a = math.radians(120 * k)
        d = normalize(np.array([0.25 * math.cos(a), 0.25 * math.sin(a), -1.0]))
        parts += Z.zfeather((0.03 * math.cos(a), 0.03 * math.sin(a), 1.25), d, 0.16, 0.045,
                            (-math.sin(a), math.cos(a), 0), mats=("BH_Bronze", "BH_Gold"), tip=0.25, bend=0.02,
                            quill=False, k=5)
    return parts
