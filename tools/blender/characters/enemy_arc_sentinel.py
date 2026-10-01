"""Arc Sentinel (bh-029, Builder M2, Zarael / the Glasswire Barrens ranged + melee construct): a 2.1 m Wirewright
gate-guard of carved pale stone and old bronze. A squared stone chest under a bronze breastplate with a stepped-fret
border; in its centre a round bronze window holds a vertical arc coil where the old current still burns white.
Basalt core column at the waist, a stone pelvis block with hanging carved tassets. Stepped bronze pauldrons, stone
limb segments on dark basalt ball joints with bronze rings, bronze bracers and greaves, block feet. The head is a
stone block whose face IS a glyph: two stepped slot-eyes and a fret mouth-grille glowing white, a forehead glyph
line, bronze ear discs and a stepped bronze crown with a fan of flat bronze blade-feathers. Inlaid wire channels
(white) run over the stone, some cracked dark. Right hand: a long spear (rigid on weapon.R) - dark bronze-banded
shaft, an arc coil (copper helix over a stone core, glowing white) under a bronze leaf blade flanked by two
electrode prongs with a white arc between them; a coiled butt spike. Left hand free (cast_weapon).

GLOW: pure white (BH_Emissive (1, 1, 1), energy 5). Construct: every piece is rigid to one bone (basalt joint balls
cover the gaps). Clips: cast_weapon spear_1 spear_2 spear_heavy."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, interp_rows
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_rune_golem as RG
import kit_a_common as A
import enemy_glyphbound_warrior as Z

SCALE = 2.1 / 1.93
PROPS = proportions(SCALE, shoulder_x=0.215 * SCALE, hip_x=0.11 * SCALE, clav_x0=0.05 * SCALE)
PREVIEW_HEIGHT = 2.6
PALETTE = "arc_sentinel"
PALETTE_COLORS = {
    "BH_Stone": ((0.43, 0.39, 0.32), 0.0, 0.88, None, 0.0, 1.0),               # pale carved Wirewright stone
    "BH_Bronze": ((0.42, 0.27, 0.12), 0.9, 0.42, None, 0.0, 1.0),              # old bronze
    "BH_Horn": ((0.17, 0.3, 0.25), 0.3, 0.6, None, 0.0, 1.0),                  # verdigris accents
    "BH_DarkSteel": ((0.075, 0.072, 0.075), 0.0, 0.8, None, 0.0, 1.0),         # basalt core / joint balls
    "BH_Gold": ((0.62, 0.36, 0.18), 1.0, 0.38, None, 0.0, 1.0),                # copper coil wire
    "BH_Wood": ((0.07, 0.05, 0.04), 0.0, 0.6, None, 0.0, 1.0),                 # dark ironwood spear shaft
    "BH_Shadow": ((0.02, 0.018, 0.018), 0.0, 0.85, None, 0.0, 1.0),            # grooves, recesses, cracks
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),     # the old current (pure white)
}
CLIPS = ["cast_weapon", "spear_1", "spear_2", "spear_heavy"]

FRONT, BACK = np.array([0, -1.0, 0]), np.array([0, 1.0, 0])
P = Z.P
slab = RG.slab

PELV = [(0.86, 0.15, 0.1, 0.1, 0.0), (0.92, 0.175, 0.115, 0.115, 0.0), (1.0, 0.18, 0.12, 0.12, 0.0),
        (1.05, 0.165, 0.11, 0.11, 0.0)]
ABDO = [(1.06, 0.13, 0.095, 0.095, 0.0), (1.12, 0.145, 0.105, 0.1, 0.0), (1.2, 0.155, 0.11, 0.105, 0.0)]
CHEST = [(1.2, 0.165, 0.115, 0.11, 0.0), (1.28, 0.2, 0.135, 0.125, 0.0), (1.37, 0.225, 0.145, 0.135, 0.0),
         (1.45, 0.225, 0.14, 0.14, 0.0), (1.51, 0.19, 0.115, 0.125, 0.0), (1.55, 0.11, 0.08, 0.09, 0.0)]
CHEST = [(r[0], r[1] * 1.1, r[2] * 1.12, r[3] * 1.12, r[4]) for r in CHEST]
PELV = [(r[0], r[1] * 1.08, r[2] * 1.1, r[3] * 1.1, r[4]) for r in PELV]
ABDO = [(r[0], r[1] * 1.1, r[2] * 1.1, r[3] * 1.1, r[4]) for r in ABDO]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


def adds(sb, parts, bone=None, weights=None):
    for p in parts:
        sb.add(p, bone, weights)


def fy(rows, x, z):
    return front_y(rows, x, z, p=4.0)


def by(rows, x, z):
    return back_y(rows, x, z, p=4.0)


def chan(pts, nrm, r=0.008, broken=()):
    return Z.channel(pts, nrm, r=r, broken=broken)


LIMB = 1.3


def jball(c, r):
    return A.ball(c, r * LIMB, "BH_DarkSteel", n=10, rings=6)


def jring(c, axis, r, w=0.03, mat="BH_Bronze"):
    axis = normalize(axis)
    V, F = M.tube([c - axis * w / 2, c + axis * w / 2], [(r, r), (r, r)], n=14,
                  up=(0, 0, 1) if abs(axis[2]) < 0.9 else (0, -1, 0))
    return P(V, F, mat, "jring")


def seg(a, b, prof, mat="BH_Stone", n=10, p=3.2, bev=0.006):
    """Stone limb segment from a to b. prof: [(u, rx, ry)] (ry toward -Y-ish)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    pts = [a + (b - a) * u for u, _, _ in prof]
    up = (0, -1, 0) if abs(normalize(b - a)[1]) < 0.9 else (0, 0, 1)
    V, F = M.tube(pts, [(rx * LIMB, ry * LIMB) for _, rx, ry in prof], n=n, up=up, p=p)
    return M.bevel(P(V, F, mat, "seg"), bev, 1, angle=40)


# ================================================================================================= build
def build(body):
    sb = K.SB(body, SCALE)
    torso(sb)
    head(sb)
    for s in ("L", "R"):
        arm(sb, s)
        leg(sb, s)
    K.add_weapon(sb, "R", arc_spear(SCALE))


def torso(sb):
    core_w = K.zspec_w([(1.0, "hips"), (1.1, "spine"), (1.2, "spine"), (1.3, "chest")])
    V, F = M.tube([(0, 0.0, 0.95), (0, 0.0, 1.1), (0, 0.0, 1.25), (0, 0.0, 1.35)], [(0.12, 0.085)] * 4, n=14,
                  up=(0, -1, 0))
    sb.add(P(V, F, "BH_DarkSteel", "core"), weights=core_w)
    # pelvis + bronze belt + carved tassets (split per leg)
    sb.add(RG.block(PELV, bev=0.008), "hips")
    sb.add(RG.band(PELV, 1.0, 0.035, 0.008, mat="BH_Bronze"), "hips")
    for sx in (1, -1):
        lb = "thigh.L" if sx > 0 else "thigh.R"
        w = (lambda V, lb=lb: [{"hips": 0.6, lb: 0.4}] * len(V))
        for (x, y, wd, rz) in ((0.085, -0.125, 0.13, 0), (0.18, -0.01, 0.12, 90), (0.085, 0.12, 0.13, 180)):
            c = np.array([sx * x, y, 0.82])
            sb.add(slab((wd, 0.03, 0.16), c, R=Rz(sx * rz) @ Rx(8 if rz == 0 else (-8 if rz == 180 else 0)),
                        bev=0.007), weights=w)
            if rz == 0:
                adds(sb, chan([c + (sx * -0.035, -0.018, 0.05), c + (sx * -0.035, -0.02, -0.04),
                               c + (sx * 0.035, -0.022, -0.04)], FRONT, r=0.006), weights=w)
    # abdomen block with fret channel
    sb.add(RG.block(ABDO, bev=0.008), "spine")
    sb.add(RG.band(ABDO, 1.17, 0.025, 0.006, mat="BH_Bronze"), "spine")
    fw = Z.fret_wave(2, steps=2)
    pts = [(-0.09 + 0.18 * u, fy(ABDO, -0.09 + 0.18 * u, 1.1) - 0.002, 1.08 + 0.05 * v) for u, v in fw]
    adds(sb, chan(pts, FRONT, r=0.005), "spine")
    chest(sb)


def chest(sb):
    sb.add(RG.block(CHEST, bev=0.01), "chest")
    # bronze breastplate (front), stepped-fret border in relief
    zc = 1.38
    rows_b = [(r[0], r[1] + 0.012, r[2] + 0.012, r[3] + 0.012, r[4]) for r in CHEST]
    nu = 13
    rings = []
    for z in np.linspace(1.24, 1.5, 6):
        fr = np.linspace(-0.17, 0.17, nu)
        ring = K.ring_frac(rows_b, z, 0.0, fr, p=4.0)
        rings.append(ring)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    sb.add(M.solidify(P(V, F, "BH_Bronze", "breast"), 0.012, offset=1.0), "chest")
    fw = Z.fret_wave(4, steps=2)
    for zb in (1.255, 1.49):
        pts = [(-0.17 + 0.34 * u, fy(rows_b, -0.17 + 0.34 * u, zb) - 0.012, zb - 0.012 + 0.024 * v * (1 if zb < 1.3
                                                                                                       else -1))
               for u, v in fw]
        sb.add(A.tube(pts, (0.005, 0.004), "BH_Horn", n=4, up=(0, -1, 0)), "chest")
    # the arc window: a bronze ring, a dark recess, a vertical coil burning white
    yc = fy(rows_b, 0, zc) - 0.012
    sb.add(A.ball((0, yc + 0.02, zc), 0.075, "BH_Shadow", n=14, rings=6, scale=(1, 0.35, 1.05)), "chest")
    ring = [(0.078 * math.cos(a), yc - 0.006, zc + 0.082 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 25)]
    sb.add(A.tube(ring, (0.016, 0.012), "BH_Bronze", n=6, cap=False), "chest")
    for a in range(0, 360, 45):
        ra = math.radians(a)
        sb.add(slab((0.02, 0.02, 0.03), (0.095 * math.cos(ra), yc - 0.004, zc + 0.098 * math.sin(ra)), R=Ry(-a + 90),
                    mat="BH_Bronze", bev=0.004), "chest")
    sb.add(A.tube([(0, yc + 0.0, zc - 0.07), (0, yc + 0.0, zc + 0.07)], 0.014, "BH_Stone", n=6), "chest")
    sb.add(Z.coil((0, yc, zc - 0.06), (0, yc, zc + 0.06), 0.024, 5, 0.006, "BH_Emissive", n=4, pts_per_turn=8),
           "chest")
    sb.add(A.ball((0, yc - 0.01, zc), 0.022, "BH_Emissive", n=8, rings=4), "chest")
    # channels running from the window over the chest to the shoulders, and the back
    for sx in (1, -1):
        pts = [(sx * 0.09, zc), (sx * 0.14, zc + 0.04), (sx * 0.14, zc + 0.1), (sx * 0.19, zc + 0.12)]
        adds(sb, chan([(x, fy(rows_b, x, z) - 0.014, z) for x, z in pts], FRONT, r=0.006), "chest")
        pts = [(sx * 0.06, zc - 0.08), (sx * 0.12, zc - 0.1), (sx * 0.12, zc - 0.13)]
        adds(sb, chan([(x, fy(rows_b, x, z) - 0.014, z) for x, z in pts], FRONT, r=0.006), "chest")
    back = [(0.0, 1.22), (0.0, 1.38), (0.08, 1.44), (0.14, 1.44)]
    adds(sb, chan([(x, by(CHEST, x, z) + 0.002, z) for x, z in back], BACK, r=0.007, broken=(1,)), "chest")
    back2 = [(0.0, 1.38), (-0.08, 1.44), (-0.14, 1.44)]
    adds(sb, chan([(x, by(CHEST, x, z) + 0.002, z) for x, z in back2], BACK, r=0.007), "chest")
    for z in (1.27, 1.32):
        adds(sb, chan([(x, by(CHEST, x, z) + 0.002, z) for x in (-0.1, 0.0, 0.1)], BACK, r=0.006), "chest")
    # cracks in the stone
    sb.add(RG.crack([(0.16, by(CHEST, 0.16, 1.3) + 0.004, 1.3), (0.13, by(CHEST, 0.13, 1.25) + 0.004, 1.25),
                     (0.15, by(CHEST, 0.15, 1.21) + 0.004, 1.21)], BACK, r=0.005), "chest")
    # back plate: a bronze spine-plate between the shoulder blades
    sb.add(slab((0.11, 0.025, 0.2), (0, by(CHEST, 0, 1.4) + 0.008, 1.4), mat="BH_Bronze", bev=0.006), "chest")
    # gorget collar stones
    for sx in (1, -1):
        sb.add(slab((0.1, 0.17, 0.06), (sx * 0.11, 0.0, 1.535), R=Ry(sx * 16), bev=0.008), "chest")


def head(sb):
    hz = 1.6
    # neck: basalt column + bronze ring
    V, F = M.tube([(0, 0.0, 1.47), (0, -0.005, 1.6)], [(0.05, 0.05), (0.048, 0.048)], n=12, up=(0, -1, 0))
    sb.add(P(V, F, "BH_DarkSteel", "neck"), "neck")
    sb.add(jring(np.array([0, -0.003, 1.55]), (0, 0, 1), 0.06, w=0.025), "neck")
    H = [(hz + 0.0, 0.085, 0.085, 0.08, 0.0), (hz + 0.04, 0.112, 0.105, 0.095, 0.0),
         (hz + 0.15, 0.118, 0.11, 0.1, 0.0), (hz + 0.21, 0.106, 0.1, 0.092, 0.0), (hz + 0.235, 0.075, 0.074, 0.068, 0.0)]
    sb.add(RG.block(H, bev=0.008, n=24), "head")
    yf = fy(H, 0, hz + 0.1)
    # face plate (a glyph): stepped slot-eyes, forehead line, fret mouth grille
    sb.add(slab((0.18, 0.02, 0.19), (0, yf - 0.004, hz + 0.115), bev=0.006), "head")
    yp = yf - 0.015
    for sx in (1, -1):
        eye = [(sx * 0.015, hz + 0.135), (sx * 0.015, hz + 0.15), (sx * 0.04, hz + 0.15), (sx * 0.04, hz + 0.14),
               (sx * 0.06, hz + 0.14)]
        sb.add(A.tube([(x, yp + 0.004, z) for x, z in eye], (0.009, 0.004), "BH_Shadow", n=4, up=(0, -1, 0)), "head")
        sb.add(A.tube([(x, yp - 0.0, z) for x, z in eye], (0.0055, 0.003), "BH_Emissive", n=4, up=(0, -1, 0)),
               "head")
        sb.add(slab((0.05, 0.022, 0.016), (sx * 0.04, yp + 0.002, hz + 0.172), mat="BH_Stone", bev=0.004), "head")
    sb.add(A.tube([(0, yp, hz + 0.17), (0, yp, hz + 0.205)], (0.004, 0.003), "BH_Emissive", n=4, up=(0, -1, 0)),
           "head")
    fw = Z.fret_wave(2, steps=2)
    pts = [(-0.045 + 0.09 * u, yp + 0.001, hz + 0.055 + 0.03 * v) for u, v in fw]
    sb.add(A.tube(pts, (0.0045, 0.003), "BH_Emissive", n=4, up=(0, -1, 0)), "head")
    sb.add(slab((0.11, 0.012, 0.05), (0, yp + 0.008, hz + 0.07), mat="BH_Shadow", bev=0.003), "head")
    # bronze ear discs
    for sx in (1, -1):
        V, F = M.lathe([(0.0, -0.01), (0.034, -0.008), (0.038, 0.0), (0.034, 0.01), (0.0, 0.012)], 12)
        sb.add(P(V, F, "BH_Bronze", "ear").rot(Ry(90 * sx)).move((sx * 0.122, 0.0, hz + 0.11)), "head")
        sb.add(A.ball((sx * 0.134, 0.0, hz + 0.11), 0.011, "BH_Emissive", n=6, rings=3), "head")
    # stepped bronze crown + fan of flat bronze blade-feathers (tilted back so it reads from above)
    for k, (h, r) in enumerate(((0.025, 0.12), (0.022, 0.1), (0.02, 0.08))):
        z0 = hz + 0.225 + k * 0.022
        V, F = M.box(r * 2, r * 2.1, h)
        sb.add(M.bevel(P(V, F, "BH_Bronze", "crown").move((0, 0.0, z0)), 0.004, 1), "head")
    yb = -0.08
    V, F = M.box(0.16, 0.02, 0.06)
    sb.add(M.bevel(P(V, F, "BH_Bronze", "brow").move((0, yb, hz + 0.24)), 0.004, 1), "head")
    adds(sb, chan([(-0.06, yb - 0.011, hz + 0.24), (0.0, yb - 0.011, hz + 0.255), (0.06, yb - 0.011, hz + 0.24)],
                  FRONT, r=0.0045), "head")
    base = np.array([0.0, 0.03, hz + 0.29])
    tb = math.radians(28)
    n = 9
    for i in range(n):
        a = math.radians(-70 + 140 * i / (n - 1))
        d = np.array([math.sin(a), math.sin(tb) * math.cos(a), math.cos(tb) * math.cos(a)])
        ln = 0.17 + 0.08 * math.cos(a) ** 2
        tng = np.array([math.cos(a), 0.0, -math.sin(a)])
        nrm = normalize(np.cross(d, tng))
        o = np.array([(0.0, 0.0), (0.014, 0.25), (0.016, 0.7), (0.0, 1.0), (-0.016, 0.7), (-0.014, 0.25)])
        V2, F2 = M.prism(np.array([(u * 1.6, v * ln) for u, v in o]), 0.006, axis="z")
        R = np.stack([tng, d, nrm], 1)
        prt = P(np.asarray(V2) @ R.T + base, F2, "BH_Bronze" if i % 2 else "BH_Horn", "blade")
        sb.add(M.recalc_normals(prt), "head")
        if i % 2 == 0:
            sb.add(A.tube([base + d * ln * 0.3 - nrm * 0.004, base + d * ln * 0.8 - nrm * 0.004], 0.0035,
                          "BH_Emissive", n=4), "head")


def arm(sb, s):
    sx = 1 if s == "L" else -1
    sh_b, ua, fa, ha = "shoulder." + s, "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    sb.add(jball(sh, 0.07), ua)
    sb.add(seg(sh + (el - sh) * 0.15, el - (el - sh) * 0.08, [(0.0, 0.052, 0.056), (0.5, 0.058, 0.06), (1.0, 0.05, 0.052)]),
           ua)
    sb.add(jring(sh + (el - sh) * 0.6, el - sh, 0.062 * LIMB, w=0.022), ua)
    d = normalize(el - sh)
    out = normalize(np.cross(d, (0, 1, 0))) * sx
    adds(sb, chan([sh + (el - sh) * u + out * 0.059 * LIMB for u in (0.22, 0.5)], out, r=0.006), ua)
    # stepped bronze pauldron (three lames) on the clavicle bone
    c = sh + np.array([sx * 0.02, 0.0, 0.05])
    for k, (w, dz, dx) in enumerate(((0.17, 0.0, 0.0), (0.15, -0.045, 0.03), (0.13, -0.085, 0.055))):
        R = Ry(-sx * (12 + 14 * k))
        sb.add(slab((w, 0.19 - 0.02 * k, 0.05), c + np.array([sx * dx, 0, dz]), R=R, mat="BH_Bronze" if k != 1 else
                    "BH_Stone", bev=0.008), sh_b)
    top = c + np.array([0, 0, 0.028])
    adds(sb, chan([top + (sx * -0.05, -0.07, 0), top + (0, -0.07, 0.004), top + (sx * 0.05, -0.07, 0)],
                  (0, -0.3, 1.0), r=0.005), sh_b)
    # elbow, forearm, bronze bracer
    sb.add(jball(el, 0.055), fa)
    sb.add(seg(el + (wr - el) * 0.1, wr - (wr - el) * 0.06, [(0.0, 0.05, 0.052), (0.6, 0.056, 0.058),
                                                             (1.0, 0.046, 0.048)]), fa)
    V, F = M.tube([el + (wr - el) * 0.45, wr - (wr - el) * 0.04], [(0.06 * LIMB, 0.062 * LIMB),
                                                                   (0.052 * LIMB, 0.055 * LIMB)], n=12, up=(0, -1, 0))
    sb.add(M.bevel(P(V, F, "BH_Bronze", "bracer"), 0.004, 1), fa)
    dd = normalize(wr - el)
    o2 = normalize(np.cross(dd, (0, 1, 0))) * sx
    adds(sb, chan([el + (wr - el) * u + o2 * 0.06 * LIMB for u in (0.5, 0.85)], o2, r=0.005), fa)
    sb.add(jball(wr, 0.038), ha)
    K.add_fist(sb, s, "BH_Bronze", "BH_Stone", gauntlet=True, scale=1.1)


def leg(sb, s):
    sx = 1 if s == "L" else -1
    th, shn, ft, toe = "thigh." + s, "shin." + s, "foot." + s, "toe." + s
    hip, k, a = sb.head(th), sb.head(shn), sb.tail(shn)
    sb.add(jball(hip, 0.072), th)
    sb.add(seg(hip + (k - hip) * 0.12, k - (k - hip) * 0.06, [(0.0, 0.07, 0.072), (0.5, 0.068, 0.07),
                                                              (1.0, 0.058, 0.06)]), th)
    sb.add(jring(hip + (k - hip) * 0.6, k - hip, 0.072 * LIMB, w=0.025), th)
    adds(sb, chan([hip + (k - hip) * u + np.array([sx * 0.07 * LIMB, 0, 0]) for u in (0.2, 0.5)], (sx, 0, 0),
                  r=0.006), th)
    sb.add(jball(k, 0.06), shn)
    sb.add(slab((0.12, 0.035, 0.11), k + (0, -0.08, 0.0), R=Rx(-8), mat="BH_Bronze", bev=0.008), shn)
    sb.add(seg(k + (a - k) * 0.08, a + (k - a) * 0.12, [(0.0, 0.058, 0.06), (0.4, 0.062, 0.066),
                                                         (1.0, 0.05, 0.052)]), shn)
    # bronze greave plate down the front of the shin + channel
    V, F = M.box(0.11, 0.022, 0.28)
    gy = -0.06 * LIMB - 0.004
    sb.add(M.bevel(P(V, F, "BH_Bronze", "greave").move(k + (a - k) * 0.45 + np.array([0, gy, 0])), 0.005, 1), shn)
    adds(sb, chan([k + (a - k) * 0.3 + np.array([0, gy - 0.013, 0]), k + (a - k) * 0.6 + np.array([0, gy - 0.013, 0])],
                  FRONT, r=0.005), shn)
    hx = sb.head(th)[0]
    sb.add(jball(a + np.array([0, 0, 0.02]), 0.045), ft)
    sb.add(slab((0.14, 0.22, 0.09), (hx, -0.04, 0.045), bev=0.012), ft)
    sb.add(slab((0.13, 0.025, 0.05), (hx, -0.14, 0.085), R=Rx(-30), mat="BH_Bronze", bev=0.005), ft)
    sb.add(slab((0.13, 0.08, 0.05), (hx, -0.185, 0.026), bev=0.01), toe)


# ================================================================================================= spear
def arc_spear(s=1.0):
    """Weapon space (grip at origin, +Z to the head). Shaft -1.05..1.25: dark ironwood with bronze bands; the arc
    coil (copper helix over a stone core, glowing white between the turns) at 1.22..1.48; a bronze leaf blade
    1.5..1.85 flanked by two electrode prongs with a white arc jumping between their tips; coiled butt spike."""
    parts = []
    V, F = M.lathe([(0, -1.05), (0.016, -1.05), (0.02, -1.0), (0.02, 0.0), (0.019, 1.2), (0, 1.22)], 8)
    parts.append(P(V, F, "BH_Wood", "shaft"))
    parts.append(K.WP._grip(-0.12, 0.12, 0.0215, 5, mat="BH_Bronze"))
    for z in (-0.9, -0.5, 0.2, 0.5, 0.85, 1.12):
        V, F = M.lathe([(0.0, z - 0.012), (0.025, z - 0.012), (0.027, z), (0.025, z + 0.012), (0, z + 0.012)], 8)
        parts.append(P(V, F, "BH_Bronze", "band"))
    # glyph wire inlaid along the upper shaft
    parts.append(A.tube([(0.0, -0.0205, 0.25), (0.0, -0.0205, 1.1)], 0.004, "BH_Emissive", n=4))
    # butt: bronze spike with a little copper coil
    V, F = M.lathe([(0, -1.25), (0.012, -1.2), (0.026, -1.08), (0.026, -1.03), (0, -1.02)], 8)
    parts.append(P(V, F, "BH_Bronze", "butt"))
    parts.append(Z.coil((0, 0, -1.02), (0, 0, -0.94), 0.024, 4, 0.0045, "BH_Gold", n=4, pts_per_turn=8))
    # head socket + arc coil
    V, F = M.lathe([(0, 1.18), (0.03, 1.18), (0.036, 1.22), (0.03, 1.24), (0, 1.25)], 10)
    parts.append(P(V, F, "BH_Bronze", "socket"))
    V, F = M.lathe([(0, 1.23), (0.026, 1.24), (0.028, 1.47), (0, 1.48)], 8)
    parts.append(P(V, F, "BH_Stone", "coilcore"))
    parts.append(A.tube([(0, 0, 1.25), (0, 0, 1.46)], 0.03, "BH_Emissive", n=8))
    parts.append(Z.coil((0, 0, 1.25), (0, 0, 1.46), 0.036, 8, 0.0065, "BH_Gold", n=4, pts_per_turn=9))
    for z in (1.245, 1.475):
        V, F = M.lathe([(0.0, z - 0.012), (0.046, z - 0.01), (0.048, z), (0.046, z + 0.01), (0, z + 0.012)], 10)
        parts.append(P(V, F, "BH_Bronze", "coilcap"))
    # leaf blade (bronze, edges ±X, flats ±Y)
    rings = []
    for z, w in ((1.48, 0.03), (1.53, 0.07), (1.6, 0.095), (1.68, 0.085), (1.76, 0.05), (1.82, 0.015), (1.85, 0.002)):
        hw = w / 2
        t = 0.013 * (w / 0.095) + 0.002
        rings.append(np.array([(hw, 0, z), (0, t, z), (-hw, 0, z), (0, -t, z)]))
    V, F = M.loft(rings)
    parts.append(P(V, F, "BH_Bronze", "blade"))
    parts.append(A.tube([(0, -0.014, 1.52), (0, -0.012, 1.74)], (0.0035, 0.002), "BH_Emissive", n=4))
    parts.append(A.tube([(0, 0.014, 1.52), (0, 0.012, 1.74)], (0.0035, 0.002), "BH_Emissive", n=4))
    # electrode prongs + the arc
    tips = []
    for sx in (1, -1):
        pts = [(sx * 0.04, 0, 1.47), (sx * 0.085, 0, 1.52), (sx * 0.09, 0, 1.6), (sx * 0.075, 0, 1.66)]
        parts.append(A.taper(pts, 0.011, 0.005, "BH_Bronze", n=6))
        parts.append(A.ball(pts[-1], 0.012, "BH_Emissive", n=6, rings=4))
        tips.append(np.array(pts[-1]))
    bolt = [tips[0], (0.045, 0.012, 1.69), (0.015, -0.01, 1.655), (-0.02, 0.01, 1.7), (-0.05, -0.006, 1.67), tips[1]]
    parts.append(A.tube(bolt, 0.0045, "BH_Emissive", n=4))
    for p in parts:
        p.V = p.V * s
    return parts
