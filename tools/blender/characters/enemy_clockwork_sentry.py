"""Clockwork Sentry (bh-012, Builder E; The Shattered Orrery, ranged construct): a ~1.9 m riveted brass-and-iron
automaton. A polished brass barrel torso bound with riveted iron hoops, a round window in the chest showing a
violet-white glowing gear core, an iron waist gimbal and pelvis block with brass tassets, segmented tarnished-brass
limbs on iron ball joints, a round brass head with one large glowing lens eye, and three exhaust stacks on the back.
The LEFT forearm is a crossbow (rigid on weapon.L: lock housing, iron tiller, brass prod, glowing string, loaded bolt
with a glowing head) - there is no left hand. The right hand holds a short bayonet blade (weapon.R).

Clips: bow_1 (quick shot), bow_release (loose + follow-through), sword_1 (bayonet thrust/slash).
Construct: every piece is rigid to one bone (iron ball joints cover the gaps). Kit: kit_e_orrery.py."""
import math

import numpy as np

import bh_mesh as M
from bh_body import Body, torso_loft, fist
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import kit_e_orrery as O

KS = 1.9 / 1.82
PROPS = proportions(KS, shoulder_x=0.23 * KS, clav_x0=0.05 * KS, hip_x=0.11 * KS)
PREVIEW_HEIGHT = 2.2
PALETTE = "clockwork_sentry"
PALETTE_COLORS = {
    "BH_Bronze": O.BRASS,          # polished brass: barrel, head, pauldrons, prod
    "BH_Horn": O.BRASS_OLD,        # tarnished brass: limbs, tassets, rims
    "BH_DarkSteel": O.IRON,        # dark iron: hoops, joints, pelvis, tiller, pipes
    "BH_Gold": O.GOLD,             # small gold accents (hubs, finial, fletching)
    "BH_Steel": ((0.6, 0.62, 0.66), 1.0, 0.3, None, 0.0, 1.0),   # bayonet blade
    "BH_Shadow": O.VOID,           # recesses, pipe mouths
    "BH_Emissive": O.GLOW,         # lens eye, gear core, crossbow string + bolt head
}
CLIPS = ["bow_release", "bow_1", "sword_1"]

FRONT = np.array([0, -1.0, 0])
BARREL_SY = 0.86


def finish_mesh(mesh_ob):
    arm = mesh_ob.parent
    for bn in ("weapon.L", "weapon.R"):
        if bn in arm.data.bones and bn in mesh_ob.vertex_groups:
            arm.data.bones[bn].use_deform = True


def barrel_r(z):
    prof = [(1.19, 0.15), (1.23, 0.175), (1.3, 0.19), (1.38, 0.192), (1.45, 0.178), (1.5, 0.15), (1.53, 0.1)]
    zs = [p[0] for p in prof]
    return float(np.interp(z, zs, [p[1] for p in prof]))


def socket_parts(body, side, parts):
    A = body.axes("weapon." + side)
    o = body.head("weapon." + side)
    for p in parts:
        loc = np.stack([p.V[:, 0], p.V[:, 2], -p.V[:, 1]], 1)
        p.V = o + loc @ A.T
    return parts


# ================================================================================================= weapons
def forearm_crossbow():
    """Weapon-builder space for the LEFT socket: grip at origin, builder -X = distal (along the forearm toward the
    target), +Z = thumb side (up when aiming), +-Y = across. Built as the hand: no fist on this side."""
    parts = []
    V, F = M.box(0.2, 0.085, 0.095, center=(0.02, 0, 0.0))
    parts.append(M.bevel(O.P(V, F, "BH_Bronze", "lock"), 0.012, 1))
    V, F = M.box(0.36, 0.05, 0.055, center=(-0.25, 0, 0.0))
    parts.append(M.bevel(O.P(V, F, "BH_DarkSteel", "tiller"), 0.008, 1))
    V, F = M.box(0.34, 0.018, 0.01, center=(-0.25, 0, 0.031))
    parts.append(O.P(V, F, "BH_Gold", "rail"))
    for sy in (1, -1):
        parts += O.spokes_gear((0.02, sy * 0.047, 0.0), (0, sy, 0), 0.036, 10, 0.008, "BH_Gold", spokes=3)
    # prod (bow arms) across the front, tips swept back toward the shooter
    xp = -0.39
    for sy in (1, -1):
        pts = [(xp - 0.005, 0.0, 0.004)]
        for t in np.linspace(0.12, 1.0, 6):
            pts.append((xp + 0.11 * t ** 2, sy * 0.3 * t, 0.004 + 0.01 * t))
        parts.append(O.taper(pts, 0.019, 0.009, "BH_Bronze", n=6, up=(0, 0, 1)))
        tip = np.array(pts[-1])
        parts.append(O.ball(tip, 0.014, "BH_Gold", n=6, rings=4))
    V, F = M.box(0.07, 0.08, 0.07, center=(xp, 0, 0.0))
    parts.append(M.bevel(O.P(V, F, "BH_DarkSteel", "prod_mount"), 0.01, 1))
    # glowing string drawn back to the nut, loaded bolt with a glowing head
    nut = np.array([-0.075, 0.0, 0.036])
    for sy in (1, -1):
        parts.append(O.tube([(xp + 0.11, sy * 0.3, 0.014), nut], 0.0045, "BH_Emissive", n=4))
    parts.append(O.tube([(-0.08, 0, 0.042), (-0.47, 0, 0.042)], 0.0075, "BH_DarkSteel", n=5))
    V, F = M.lathe([(0.0, 0.0), (0.016, 0.012), (0.012, 0.03), (0.0, 0.075)], 4)
    parts.append(O.orient(O.P(V, F, "BH_Emissive", "bolt_head"), (-0.47, 0, 0.042), (-1, 0, 0)))
    for a in (0, 120, 240):
        V, F = M.box(0.05, 0.003, 0.018, center=(-0.105, 0, 0.009))
        parts.append(O.P(V, F, "BH_Gold", "fletch").rot(Rx(a), center=(0, 0, 0)).move((0, 0, 0.042 - 0.0)))
    return parts


def bayonet():
    """Weapon-builder space (right socket): grip at origin, +Z blade, flats +-Y."""
    parts = []
    V, F = M.lathe([(0.0, -0.1), (0.022, -0.1), (0.024, -0.085), (0.017, -0.075), (0.017, 0.04), (0.0, 0.04)], 8)
    parts.append(O.P(V, F, "BH_DarkSteel", "grip"))
    for z in (-0.04, 0.0):
        parts.append(O.ring((0, 0, z), (0, 0, 1), 0.018, 0.005, "BH_Horn", n=10, m=4))
    parts.append(O.ring((0, 0, 0.055), (0, 1, 0), 0.03, 0.007, "BH_Gold", n=12, m=5))
    V, F = M.box(0.11, 0.022, 0.02, center=(0, 0, 0.05))
    parts.append(M.bevel(O.P(V, F, "BH_Horn", "guard"), 0.005, 1))
    V, F = M.lathe([(0.0, 0.05), (0.026, 0.07), (0.024, 0.3), (0.012, 0.44), (0.0, 0.5)], 4)
    blade = O.P(V, F, "BH_Steel", "blade").rot(Rz(45)).scale((1.0, 0.22, 1.0))
    parts.append(blade)
    V, F = M.box(0.004, 0.008, 0.3, center=(0, 0, 0.21))
    parts.append(O.P(V, F, "BH_Emissive", "edge_glow").move((0.0, 0.0, 0.0)).scale((1, 1, 1)))
    return parts


# ================================================================================================= build
def build(real: Body):
    b = O.ScaledP(real, KS)
    add = b.add
    L = O.levels(b.p)
    # ---------------------------------------------------------------- pelvis + waist gimbal
    PEL = [(0.85, 0.115, 0.085, 0.085, 0.0), (0.9, 0.145, 0.105, 0.105, 0.0), (0.99, 0.15, 0.108, 0.108, 0.0),
           (1.05, 0.12, 0.09, 0.09, 0.0)]
    V, F = torso_loft(PEL, n=20, p=3.0, cap0=True, cap1=True)
    add(M.bevel(O.P(V, F, "BH_DarkSteel", "pelvis"), 0.01, 1, angle=40), "hips")
    V, F = torso_loft([(0.965, 0.158, 0.116, 0.116, 0.0), (1.005, 0.158, 0.116, 0.116, 0.0)], n=20, p=3.0,
                      cap0=True, cap1=True)
    add(O.P(V, F, "BH_Horn", "belt"), "hips")
    for x in (-0.11, -0.055, 0.0, 0.055, 0.11):
        add(O.ball((x, -0.118 * (1 - (abs(x) / 0.16) ** 3) ** 0.33, 0.985), 0.008, "BH_Gold", n=6, rings=3), "hips")
    # tassets: split per leg (front + back + outer sides)
    for sx, s in ((1, "L"), (-1, "R")):
        w = O.const_w({"hips": 0.6, "thigh." + s: 0.4})
        for (x, y, rz, wdt) in ((0.075, -0.125, 0, 0.12), (0.075, 0.125, 0, 0.12), (0.165, 0.0, 90, 0.14)):
            V, F = M.box(wdt, 0.022, 0.17)
            tp = O.P(V, F, "BH_Horn", "tasset").rot(Rx(8 if y < 0 else -8) if rz == 0 else Ry(-sx * 8))
            tp.rot(Rz(rz)).move((sx * x, y, 0.88))
            add(M.bevel(tp, 0.006, 1), weights=w)
            add(O.P(*M.box(wdt * 0.8, 0.026, 0.02, center=(0, 0, 0)), "BH_DarkSteel", "trim")
                .rot(Rz(rz)).move((sx * x, y * 1.04, 0.8)), weights=w)
    # waist gimbal: iron core column + stacked rings (spine)
    add(O.tube([(0, 0, 1.03), (0, 0, 1.2)], 0.095, "BH_DarkSteel", n=16), "spine")
    for z, r, m in ((1.07, 0.112, "BH_Horn"), (1.12, 0.118, "BH_DarkSteel"), (1.17, 0.112, "BH_Horn")):
        add(O.ring((0, 0, z), (0, 0, 1), r, 0.016, m, n=20, m=6), "spine")
    # ---------------------------------------------------------------- barrel torso (chest)
    prof = [(0.0, 1.185)] + [(barrel_r(z), z) for z in np.linspace(1.19, 1.53, 11)] + [(0.0, 1.535)]
    V, F = M.lathe(prof, 26)
    barrel = O.P(V, F, "BH_Bronze", "barrel").scale((1, BARREL_SY, 1))
    add(barrel, "chest")

    def hoop(z, rt=0.013, mat="BH_DarkSteel", nr=14):
        r = barrel_r(z) + 0.004
        V, F = M.lathe([(r - 0.004, z - 0.02), (r + rt, z - 0.018), (r + rt, z + 0.018), (r - 0.004, z + 0.02)], 26,
                       cap=False)
        add(O.P(V, F, mat, "hoop").scale((1, BARREL_SY * (r + rt * 0.5) / (r + rt * 0.5), 1)), "chest")
        pts = []
        for i in range(nr):
            a = 2 * math.pi * (i + 0.5) / nr
            if abs(math.cos(a - (-math.pi / 2))) > 0.93 and 1.25 < z < 1.45:
                continue
            pts.append((math.cos(a) * (r + rt + 0.002), math.sin(a) * (r + rt + 0.002) * BARREL_SY, z))
        for p in O.rivets(pts, 0.0075, "BH_Gold"):
            add(p, "chest")
    hoop(1.215)
    hoop(1.475)
    # vertical riveted seams at the sides and back
    for a in (0.0, math.pi, math.pi / 2 + 0.6, math.pi / 2 - 0.6):
        pts = []
        for z in np.linspace(1.25, 1.44, 5):
            r = barrel_r(z) + 0.003
            pts.append((math.cos(a) * r, math.sin(a) * r * BARREL_SY, z))
        for p in O.rivets(pts, 0.0065, "BH_DarkSteel"):
            add(p, "chest")
    # chest window: brass rim, dark recess, glowing gear core, grille
    zw = 1.345
    yf = -barrel_r(zw) * BARREL_SY
    add(O.disc((0, yf + 0.012, zw), FRONT, 0.088, 0.02, "BH_Shadow", n=20), "chest")
    for p in O.spokes_gear((0.0, yf - 0.004, zw), FRONT, 0.074, 12, 0.012, "BH_Emissive", spokes=5):
        add(p, "chest")
    for p in O.spokes_gear((0.052, yf - 0.009, zw - 0.045), FRONT, 0.036, 9, 0.008, "BH_Emissive", spokes=3):
        add(p, "chest")
    add(O.disc((0, yf - 0.012, zw), FRONT, 0.018, 0.012, "BH_Gold", n=10), "chest")
    add(O.ring((0, yf - 0.006, zw), FRONT, 0.094, 0.016, "BH_Horn", n=24, m=6), "chest")
    for p in O.rivets(O.ring_points((0, yf - 0.02, zw), FRONT, 0.094, 8, phase=math.pi / 8), 0.0075, "BH_Gold"):
        add(p, "chest")
    add(O.tube([(0, yf - 0.018, zw - 0.085), (0, yf - 0.018, zw + 0.085)], 0.0045, "BH_DarkSteel", n=4), "chest")
    add(O.tube([(-0.085, yf - 0.018, zw), (0.085, yf - 0.018, zw)], 0.0045, "BH_DarkSteel", n=4), "chest")
    # collar + exhaust stacks on the back
    add(O.ring((0, 0, 1.53), (0, 0, 1), 0.1, 0.018, "BH_DarkSteel", n=18, m=6), "chest")
    for sx, h, r in ((1, 1.67, 0.028), (-1, 1.67, 0.028), (0, 1.58, 0.022)):
        base = np.array([sx * 0.085, barrel_r(1.32) * BARREL_SY - 0.02, 1.3])
        pts = [base, base + (sx * 0.01, 0.06, 0.06), base + (sx * 0.02, 0.085, 0.16), (sx * 0.1, base[1] + 0.09, h)]
        add(O.tube(pts, r, "BH_DarkSteel", n=8), "chest")
        top = np.array(pts[-1])
        V, F = M.lathe([(r * 0.9, -0.01), (r * 1.25, 0.0), (r * 1.55, 0.05), (r * 1.2, 0.052), (r * 0.9, 0.01)], 10,
                       cap=False)
        add(O.P(V, F, "BH_Horn", "flare").move(top), "chest")
        add(O.disc(top + (0, 0, 0.035), (0, 0, 1), r * 1.15, 0.01, "BH_Shadow", n=10), "chest")
        add(O.ring(top + (0, 0, -0.05), (0, 0, 1), r + 0.004, 0.006, "BH_Gold", n=10, m=4), "chest")
    # ---------------------------------------------------------------- neck + head
    add(O.tube([(0, 0, 1.5), (0, 0, 1.6)], 0.045, "BH_DarkSteel", n=10), "neck")
    for sx in (1, -1):
        add(O.tube([(sx * 0.055, 0.01, 1.51), (sx * 0.05, 0.0, 1.6)], 0.009, "BH_Bronze", n=5), "neck")
    hc = np.array([0, 0.0, 1.69])
    V, F = M.sphere(0.125, 20, 12, center=hc, scale=(1.0, 1.0, 0.94))
    add(O.P(V, F, "BH_Bronze", "head"), "head")
    add(O.ring(hc, (1, 0, 0), 0.127, 0.011, "BH_DarkSteel", n=22, m=5, arc=(20, 200)), "head")   # crest (over top)
    add(O.ring(hc + (0, 0, -0.04), (0, 0, 1), 0.119, 0.009, "BH_DarkSteel", n=22, m=5), "head")  # jaw line band
    le = hc + np.array([0, -0.11, 0.012])
    add(O.disc(le + (0, 0.01, 0), FRONT, 0.07, 0.03, "BH_DarkSteel", n=20), "head")
    add(O.dome(le + (0, -0.004, 0), FRONT, 0.058, "BH_Emissive", n=18, rings=4, depth=0.45), "head")
    add(O.ring(le + (0, -0.006, 0), FRONT, 0.066, 0.013, "BH_Horn", n=22, m=6), "head")
    add(O.ring(le + (0, -0.02, 0), FRONT, 0.03, 0.004, "BH_DarkSteel", n=14, m=4), "head")   # iris ring
    for p in O.rivets(O.ring_points(le + (0, -0.016, 0), FRONT, 0.066, 6, phase=math.pi / 6), 0.006, "BH_Gold"):
        add(p, "head")
    for sx in (1, -1):
        add(O.disc(hc + (sx * 0.122, 0, 0), (sx, 0, 0), 0.04, 0.02, "BH_DarkSteel", n=12), "head")
        add(O.disc(hc + (sx * 0.134, 0, 0), (sx, 0, 0), 0.016, 0.012, "BH_Gold", n=8), "head")
    add(O.tube([hc + (0, 0.02, 0.1), hc + (0, 0.03, 0.17)], 0.006, "BH_DarkSteel", n=5), "head")
    add(O.ball(hc + (0, 0.03, 0.175), 0.016, "BH_Gold", n=8, rings=5), "head")
    # ---------------------------------------------------------------- arms
    for sx, s in ((1, "L"), (-1, "R")):
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        sh, el, wr = b.head(ua), b.head(fa), b.head(ha)
        add(O.ball(sh, 0.066, "BH_DarkSteel", n=12, rings=7), ua)
        add(O.tube([sh + (el - sh) * 0.14, sh + (el - sh) * 0.86], [0.052, 0.046], "BH_Horn", n=12), ua)
        add(O.ring(sh + (el - sh) * 0.5, el - sh, 0.052, 0.009, "BH_DarkSteel", n=14, m=5), ua)
        # pauldron: polished brass dome over the shoulder ball (on the clavicle bone)
        pc = sh + np.array([sx * 0.0, 0.0, 0.03])
        nrm = normalize(np.array([sx * 0.55, 0.0, 1.0]))
        add(O.dome(pc, nrm, 0.1, "BH_Bronze", n=16, rings=5, depth=0.62), "shoulder." + s)
        add(O.ring(pc, nrm, 0.1, 0.012, "BH_DarkSteel", n=18, m=5), "shoulder." + s)
        for p in O.rivets(O.ring_points(pc + nrm * 0.006, nrm, 0.1, 6), 0.0065, "BH_Gold"):
            add(p, "shoulder." + s)
        add(O.ball(el, 0.052, "BH_DarkSteel", n=12, rings=7), fa)
        if s == "R":
            add(O.tube([el + (wr - el) * 0.14, el + (wr - el) * 0.95], [0.047, 0.04], "BH_Horn", n=12), fa)
            add(O.ring(el + (wr - el) * 0.85, wr - el, 0.043, 0.009, "BH_DarkSteel", n=14, m=5), fa)
            add(O.ball(wr, 0.034, "BH_DarkSteel", n=10, rings=6), ha)
            for prt in fist(b.std, "R", "BH_Bronze", "BH_DarkSteel", gauntlet=True, scale=1.15):
                add(prt, ha)
        else:
            # crossbow forearm: heavier polished housing with a gear and piston
            add(O.tube([el + (wr - el) * 0.1, el + (wr - el) * 0.6, el + (wr - el) * 1.02],
                       [0.056, 0.064, 0.058], "BH_Bronze", n=14), fa)
            for u in (0.3, 0.92):
                add(O.ring(el + (wr - el) * u, wr - el, 0.062, 0.009, "BH_DarkSteel", n=14, m=5), fa)
            A = b.axes(fa)
            gc = el + (wr - el) * 0.6 + A[:, 2] * 0.066
            for p in O.spokes_gear(gc, A[:, 2], 0.034, 10, 0.008, "BH_Gold", spokes=3):
                add(p, fa)
            add(O.tube([el + (wr - el) * 0.2 - A[:, 2] * 0.06, wr - A[:, 2] * 0.05], 0.009, "BH_DarkSteel", n=5), fa)
    for p in socket_parts(b.std, "L", forearm_crossbow()):
        add(p, "weapon.L")
    for p in socket_parts(b.std, "R", bayonet()):
        add(p, "weapon.R")
    # ---------------------------------------------------------------- legs
    for sx, s in ((1, "L"), (-1, "R")):
        th, sh_ = "thigh." + s, "shin." + s
        hp, k, a = b.head(th), b.head(sh_), b.tail(sh_)
        add(O.ball(hp, 0.068, "BH_DarkSteel", n=12, rings=7), th)
        for p in O.spokes_gear(hp + (sx * 0.07, 0, 0), (sx, 0, 0), 0.055, 12, 0.012, "BH_Horn", spokes=4):
            add(p, th)
        add(O.tube([hp + (k - hp) * 0.12, hp + (k - hp) * 0.88], [0.068, 0.056], "BH_Horn", n=12), th)
        add(O.ring(hp + (k - hp) * 0.55, k - hp, 0.064, 0.01, "BH_DarkSteel", n=14, m=5), th)
        add(O.ball(k, 0.058, "BH_DarkSteel", n=12, rings=7), sh_)
        add(O.dome(k + (0, -0.04, 0.0), FRONT, 0.055, "BH_Bronze", n=12, rings=4, depth=0.55), sh_)
        add(O.tube([k + (a - k) * 0.1, k + (a - k) * 0.9], [0.058, 0.046], "BH_Horn", n=12), sh_)
        add(O.ring(k + (a - k) * 0.72, a - k, 0.054, 0.01, "BH_DarkSteel", n=14, m=5), sh_)
        # calf piston
        add(O.tube([k + (0, 0.06, -0.04), a + (0, 0.055, 0.1)], 0.016, "BH_DarkSteel", n=6), sh_)
        add(O.tube([k + (0, 0.062, -0.08), k + (a - k) * 0.5 + (0, 0.06, 0)], 0.022, "BH_Bronze", n=8), sh_)
        add(O.ball(a, 0.045, "BH_DarkSteel", n=10, rings=6), "foot." + s)
        hx = b.p["hip_x"] * sx
        V, F = M.box(0.13, 0.22, 0.085, center=(hx, -0.035, 0.0425))
        add(M.bevel(O.P(V, F, "BH_DarkSteel", "foot"), 0.018, 1), "foot." + s)
        V, F = M.box(0.12, 0.1, 0.065, center=(hx, -0.175, 0.0325))
        add(M.bevel(O.P(V, F, "BH_Horn", "toe"), 0.016, 1), "toe." + s)
        V, F = M.box(0.14, 0.05, 0.03, center=(hx, 0.07, 0.015))
        add(M.bevel(O.P(V, F, "BH_Horn", "heel"), 0.01, 1), "foot." + s)
