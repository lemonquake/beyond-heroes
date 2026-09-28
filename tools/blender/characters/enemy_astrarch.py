"""The Astrarch (bh-012, Builder E; BOSS of The Shattered Orrery): a colossal armillary construct, authored ~2.3 m
(the game scales it ~2x). The torso is an open cage of brass rings (equator band, tilted meridians, latitude hoops)
around a blazing star core (BH_WeakPoint, white-gold) with an iron spine column behind it; a heavy iron shoulder yoke,
segmented brass arms on iron ball joints with orrery-ring pauldrons, massive gauntlets, a ringed hip girdle with
tarnished skirt plates, and armoured legs. The head is a crowned lens: a short brass barrel housing a glowing violet
lens under a crown of gold spikes. Two large orrery rings stand behind its back like a halo (rigid on the chest),
carrying planet beads and a glowing moon, their inner edges lit violet. It holds a tall sceptre-staff topped with a
small sun (BH_Aether palette entry = white-gold glow) inside a gold ray crown (weapon.R).

Clips: staff_1, staff_heavy, cast_heavy, cast_area, cast_ultimate, cast_channel (base, loop), boss_slam, boss_sweep,
boss_summon, boss_roar. Construct: every piece rigid to one bone except the skirt plates. Kit: kit_e_orrery.py."""
import math

import numpy as np

import bh_mesh as M
from bh_body import Body, torso_loft, fist
from bh_math import normalize, R_axis, Rx, Ry, Rz
from bh_skeleton import proportions
import kit_e_orrery as O

KA = 2.3 / 1.8
PROPS = proportions(KA, shoulder_x=0.27 * KA, clav_x0=0.06 * KA, hip_x=0.125 * KA, upper_len=0.3 * KA,
                    fore_len=0.29 * KA, hand_len=0.11 * KA)
PREVIEW_HEIGHT = 3.1
PALETTE = "astrarch"
PALETTE_COLORS = {
    "BH_Bronze": O.BRASS,
    "BH_Horn": O.BRASS_OLD,
    "BH_DarkSteel": O.IRON,
    "BH_Gold": O.GOLD,
    "BH_Stone": O.STARGLASS,                                                   # planet beads
    "BH_Shadow": O.VOID,
    "BH_Emissive": O.GLOW,                                                     # lens, ring edges, moon
    "BH_WeakPoint": ((1.0, 0.86, 0.55), 0.0, 0.3, (1.0, 0.82, 0.5), 12.0, 1.0),  # the star core
    "BH_Aether": ((1.0, 0.9, 0.6), 0.0, 0.3, (1.0, 0.85, 0.5), 8.0, 1.0),        # sceptre sun
}
CLIPS = ["staff_1", "staff_heavy", "cast_heavy", "cast_area", "cast_ultimate", "cast_channel", "boss_slam",
         "boss_sweep", "boss_summon", "boss_roar"]

FRONT = np.array([0, -1.0, 0])
CORE = np.array([0.0, 0.0, 1.33])


def finish_mesh(mesh_ob):
    arm = mesh_ob.parent
    for bn in ("weapon.L", "weapon.R"):
        if bn in arm.data.bones and bn in mesh_ob.vertex_groups:
            arm.data.bones[bn].use_deform = True


def socket_parts(body, side, parts):
    A = body.axes("weapon." + side)
    o = body.head("weapon." + side)
    for p in parts:
        loc = np.stack([p.V[:, 0], p.V[:, 2], -p.V[:, 1]], 1)
        p.V = o + loc @ A.T
    return parts


def sceptre():
    parts = []
    parts.append(O.tube([(0, 0, -1.0), (0, 0, 0.95)], 0.024, "BH_Horn", n=10))
    for z in (-0.95, -0.6, -0.25, 0.12, 0.5, 0.85):
        parts.append(O.ring((0, 0, z), (0, 0, 1), 0.027, 0.009, "BH_Bronze", n=12, m=5))
    V, F = M.lathe([(0.0, -1.1), (0.02, -1.08), (0.04, -1.02), (0.03, -0.98), (0.0, -0.98)], 10)
    parts.append(O.P(V, F, "BH_DarkSteel", "foot"))
    V, F = M.lathe([(0.0, -0.12), (0.03, -0.12), (0.031, 0.12), (0.0, 0.12)], 10)
    parts.append(O.P(V, F, "BH_DarkSteel", "grip"))
    # head: gold cradle, ray crown, sun, orbit ring with a bead
    V, F = M.lathe([(0.0, 0.93), (0.05, 0.96), (0.075, 1.02), (0.06, 1.04), (0.0, 1.04)], 12)
    parts.append(O.P(V, F, "BH_Gold", "cradle"))
    c = np.array([0, 0, 1.15])
    parts.append(O.ball(c, 0.075, "BH_Aether", n=16, rings=10))
    for k in range(12):
        a = 2 * math.pi * k / 12
        d = np.array([math.cos(a), 0.0, math.sin(a)])
        ln = 0.19 if k % 2 == 0 else 0.13
        parts.append(O.taper([c + d * 0.08, c + d * ln], 0.016, 0.002, "BH_Gold", n=5))
    parts.append(O.ring(c, (0, 1, 0), 0.105, 0.007, "BH_Gold", n=24, m=5))
    parts.append(O.ring(c, (0.25, 0.3, 1.0), 0.15, 0.006, "BH_Bronze", n=26, m=4))
    parts.append(O.ball(c + R_axis((0.25, 0.3, 1.0), 0) @ np.array([0.0, 0.0, 0.0]) + np.array([0.145, -0.03, -0.02]),
                        0.018, "BH_Stone", n=8, rings=5))
    return parts


def halo(add):
    """Two large orrery rings behind the back, rigid on the chest."""
    hc = np.array([0.0, 0.32, 1.58])
    for (r, nrm, w, seed) in ((0.62, (0.0, 1.0, 0.12), 0.07, 1), (0.48, (0.45, 1.0, -0.35), 0.05, 2)):
        nrm = normalize(np.array(nrm))
        add(O.band_ring(hc, nrm, r, w, 0.024, "BH_Bronze", n=48), "chest")
        add(O.ring(hc, nrm, r - 0.016, 0.009, "BH_Emissive", n=48, m=4), "chest")      # lit inner edge
        for sgn in (1, -1):
            add(O.ring(hc + nrm * sgn * w * 0.5, nrm, r + 0.004, 0.007, "BH_Horn", n=48, m=4), "chest")
        # graduation ticks + planet beads
        for p in O.ring_points(hc, nrm, r + 0.018, 16):
            add(O.ball(p, 0.012, "BH_Gold", n=6, rings=3), "chest")
        beads = O.ring_points(hc, nrm, r, 3, phase=0.7 * seed)
        for k, p in enumerate(beads):
            if seed == 1 and k == 0:
                add(O.ball(p, 0.07, "BH_Emissive", n=14, rings=8), "chest")               # glowing moon
                add(O.ring(p, nrm, 0.095, 0.006, "BH_Gold", n=18, m=4), "chest")
            else:
                add(O.ball(p, 0.055 if k == 1 else 0.042, "BH_Stone" if k == 1 else "BH_Horn", n=12, rings=7), "chest")
                add(O.ring(p, (0.2, 0.1, 1.0), 0.075 if k == 1 else 0.06, 0.005, "BH_Gold", n=16, m=4), "chest")
    # hub + struts from the back of the cage
    add(O.disc(hc, (0, 1, 0), 0.07, 0.04, "BH_DarkSteel", n=16), "chest")
    add(O.ball(hc + (0, 0.02, 0), 0.04, "BH_Gold", n=10, rings=6), "chest")
    for sx in (1, -1):
        add(O.tube([(sx * 0.12, 0.2, 1.42), hc + (sx * 0.03, -0.02, -0.02)], 0.022, "BH_DarkSteel", n=8), "chest")
    add(O.tube([(0, 0.18, 1.2), hc + (0, -0.02, -0.04)], 0.026, "BH_DarkSteel", n=8), "chest")


def build(real: Body):
    b = O.ScaledP(real, KA)
    add = b.add
    # ---------------------------------------------------------------- hips: girdle ring + skirt plates
    PEL = [(0.86, 0.15, 0.11, 0.11, 0.0), (0.92, 0.18, 0.13, 0.13, 0.0), (1.0, 0.18, 0.13, 0.13, 0.0),
           (1.07, 0.13, 0.1, 0.1, 0.0)]
    V, F = torso_loft(PEL, n=22, p=3.0, cap0=True, cap1=True)
    add(M.bevel(O.P(V, F, "BH_DarkSteel", "pelvis"), 0.012, 1, angle=40), "hips")
    add(O.band_ring((0, 0, 0.99), (0, 0, 1), 0.2, 0.06, 0.02, "BH_Bronze", n=32), "hips")
    add(O.ring((0, 0, 1.025), (0, 0, 1), 0.205, 0.008, "BH_Gold", n=32, m=4), "hips")
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        d = np.array([math.cos(a), math.sin(a), 0.0])
        x = d[0]
        side = "L" if x > 0 else "R"
        wl = 0.45 * min(1.0, abs(x) * 3.0)
        w = O.const_w({"hips": 1 - wl, "thigh." + side: wl}) if wl > 0.01 else O.const_w({"hips": 1.0})
        V, F = M.box(0.12, 0.022, 0.22, center=(0, 0, -0.11))
        pl = O.P(V, F, "BH_Horn", "skirt").rot(Rx(-14)).rot(Rz(math.degrees(a) + 90)).move(d * 0.205 + (0, 0, 0.97))
        add(M.bevel(pl, 0.006, 1), weights=w)
    # ---------------------------------------------------------------- spine + cage torso around the star core
    add(O.tube([(0, 0.06, 1.04), (0, 0.08, 1.22)], 0.07, "BH_DarkSteel", n=12), "spine")
    for z in (1.08, 1.15):
        add(O.disc((0, 0.06, z), (0, 0, 1), 0.1, 0.03, "BH_Horn", n=14), "spine")
    add(O.tube([(0, 0.13, 1.18), (0, 0.15, 1.5)], 0.05, "BH_DarkSteel", n=10), "chest")    # back column
    c = CORE
    R = 0.25
    add(O.band_ring(c, (0, 0, 1), R, 0.05, 0.02, "BH_Bronze", n=36), "chest")                # equator
    for zoff, rr in ((0.14, 0.2), (-0.14, 0.2)):
        add(O.ring(c + (0, 0, zoff), (0, 0, 1), rr, 0.012, "BH_Horn", n=28, m=5), "chest")
    for nrm in ((1, 0, 0), (0.7, 0.7, 0), (-0.7, 0.7, 0), (0.0, 1, 0)):
        add(O.ring(c, nrm, R, 0.014, "BH_Bronze", n=34, m=5), "chest")                     # meridians
    add(O.ring(c, (0.3, -0.2, 1.0), R * 0.8, 0.008, "BH_Gold", n=30, m=4), "chest")       # inner tilted ring
    for zz in (R, -R):
        add(O.ball(c + (0, 0, zz), 0.035, "BH_Gold", n=10, rings=6), "chest")
    # the star core: blazing sphere + rays
    add(O.ball(c, 0.14, "BH_WeakPoint", n=18, rings=12), "chest")
    rng = np.random.default_rng(4)
    for k in range(14):
        d = normalize(rng.normal(size=3))
        ln = 0.2 + 0.06 * rng.random()
        add(O.taper([c + d * 0.12, c + d * ln], 0.036, 0.002, "BH_WeakPoint", n=4), "chest")
    # shoulder yoke + collar
    add(M.bevel(O.P(*M.box(0.62, 0.2, 0.09, center=(0, 0.03, 1.47)), "BH_DarkSteel", "yoke"), 0.02, 1), "chest")
    add(O.band_ring((0, 0.02, 1.53), (0, 0, 1), 0.12, 0.05, 0.02, "BH_Bronze", n=24), "chest")
    for sx in (1, -1):
        add(O.tube([(sx * 0.2, 0.02, 1.43), c + (sx * R * 0.72, 0, R * 0.62)], 0.022, "BH_Horn", n=8), "chest")
        add(O.tube([(sx * 0.12, 0.05, 0.99 + 0.08), c + (sx * R * 0.7, 0.02, -R * 0.66)], 0.02, "BH_Horn", n=8),
            "spine")
    for p in O.rivets([(x, -0.075, 1.47) for x in np.linspace(-0.26, 0.26, 7)], 0.012, "BH_Gold"):
        add(p, "chest")
    halo(add)
    # ---------------------------------------------------------------- neck + crowned lens head
    add(O.tube([(0, 0.0, 1.52), (0, 0.0, 1.64)], 0.055, "BH_DarkSteel", n=10), "neck")
    hc = np.array([0.0, -0.01, 1.71])
    V, F = M.lathe([(0.0, -0.1), (0.1, -0.1), (0.135, -0.07), (0.14, 0.05), (0.12, 0.09), (0.0, 0.09)], 22)
    add(O.orient(O.P(V, F, "BH_Bronze", "housing"), hc, FRONT, up=(0, 0, 1)), "head")
    add(O.ring(hc + FRONT * 0.085, FRONT, 0.125, 0.017, "BH_Horn", n=26, m=6), "head")
    add(O.dome(hc + FRONT * 0.08, FRONT, 0.112, "BH_Emissive", n=22, rings=5, depth=0.35), "head")
    add(O.ring(hc + FRONT * 0.118, FRONT, 0.06, 0.006, "BH_DarkSteel", n=18, m=4), "head")
    add(O.ring(hc + FRONT * 0.122, FRONT, 0.025, 0.005, "BH_Gold", n=12, m=4), "head")
    add(O.ring(hc + FRONT * 0.02, FRONT, 0.143, 0.01, "BH_DarkSteel", n=26, m=4), "head")
    for sx in (1, -1):
        add(O.disc(hc + (sx * 0.14, 0.0, 0.0), (sx, 0, 0), 0.05, 0.03, "BH_DarkSteel", n=12), "head")
    # crown of gold spikes on a band over the housing
    add(O.ring(hc + (0, 0.0, 0.1), (0, 0, 1), 0.11, 0.014, "BH_Gold", n=24, m=5), "head")
    for k in range(9):
        a = math.radians(-90 + (k - 4) * 22)
        base = hc + np.array([0.11 * math.cos(a), 0.11 * math.sin(a), 0.1])
        h = 0.2 if k == 4 else (0.15 if k in (3, 5) else 0.11)
        outd = normalize(np.array([math.cos(a), math.sin(a), 0.0]))
        add(O.taper([base, base + outd * 0.03 + (0, 0, h)], 0.02, 0.003, "BH_Gold", n=5), "head")
        if k == 4:
            add(O.ball(base + outd * 0.01 + (0, 0, 0.05), 0.022, "BH_Emissive", n=8, rings=5), "head")
    # ---------------------------------------------------------------- arms
    for sx, s in ((1, "L"), (-1, "R")):
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        sh, el, wr = b.head(ua), b.head(fa), b.head(ha)
        add(O.ball(sh, 0.09, "BH_DarkSteel", n=14, rings=8), ua)
        # pauldron: two concentric orrery rings round the shoulder ball + a brass cap
        add(O.dome(sh + (sx * 0.01, 0, 0.04), (sx * 0.5, 0, 1.0), 0.12, "BH_Bronze", n=18, rings=5, depth=0.55),
            "shoulder." + s)
        add(O.band_ring(sh, (0, 1, 0), 0.15, 0.04, 0.016, "BH_Horn", n=30), "shoulder." + s)
        add(O.ring(sh, (sx * 0.6, 0, 0.8), 0.17, 0.009, "BH_Gold", n=30, m=4), "shoulder." + s)
        for u0, u1, r0, r1 in ((0.14, 0.5, 0.068, 0.064), (0.54, 0.88, 0.064, 0.06)):
            add(O.tube([sh + (el - sh) * u0, sh + (el - sh) * u1], [r0, r1], "BH_Bronze", n=14), ua)
        add(O.ring(sh + (el - sh) * 0.52, el - sh, 0.058, 0.012, "BH_DarkSteel", n=16, m=5), ua)
        add(O.ball(el, 0.07, "BH_DarkSteel", n=12, rings=7), fa)
        add(O.tube([el + (wr - el) * 0.12, el + (wr - el) * 0.55, el + (wr - el) * 0.95], [0.066, 0.078, 0.07],
                   "BH_Horn", n=14), fa)
        for u in (0.35, 0.9):
            add(O.ring(el + (wr - el) * u, wr - el, 0.078, 0.011, "BH_Bronze", n=16, m=5), fa)
        A = b.axes(fa)
        for p in O.fins(el + (wr - el) * 0.55, wr - el, 0.07, 0.11, 3, 0.16, 0.012, "BH_Bronze", phase=0.3):
            add(p, fa)
        add(O.ball(wr, 0.045, "BH_DarkSteel", n=10, rings=6), ha)
        for prt in fist(b.std, s, "BH_Bronze", "BH_DarkSteel", gauntlet=True, scale=1.5):
            add(prt, ha)
    for p in socket_parts(b.std, "R", sceptre()):
        add(p, "weapon.R")
    # ---------------------------------------------------------------- legs
    for sx, s in ((1, "L"), (-1, "R")):
        th, sh_ = "thigh." + s, "shin." + s
        hp, k, a = b.head(th), b.head(sh_), b.tail(sh_)
        add(O.ball(hp, 0.085, "BH_DarkSteel", n=12, rings=7), th)
        add(O.tube([hp + (k - hp) * 0.1, hp + (k - hp) * 0.88], [0.085, 0.068], "BH_Bronze", n=14), th)
        add(O.ring(hp + (k - hp) * 0.5, k - hp, 0.08, 0.012, "BH_DarkSteel", n=16, m=5), th)
        add(O.ball(k, 0.07, "BH_DarkSteel", n=12, rings=7), sh_)
        for p in O.spokes_gear(k + (0, -0.06, 0), FRONT, 0.065, 12, 0.016, "BH_Gold", spokes=4):
            add(p, sh_)
        add(O.tube([k + (a - k) * 0.1, k + (a - k) * 0.5, k + (a - k) * 0.92], [0.07, 0.078, 0.06], "BH_Horn", n=14),
            sh_)
        for u in (0.3, 0.8):
            add(O.ring(k + (a - k) * u, a - k, 0.075, 0.011, "BH_Bronze", n=16, m=5), sh_)
        add(O.ball(a, 0.055, "BH_DarkSteel", n=10, rings=6), "foot." + s)
        hx = b.p["hip_x"] * sx
        V, F = M.box(0.17, 0.26, 0.1, center=(hx, -0.04, 0.05))
        add(M.bevel(O.P(V, F, "BH_DarkSteel", "foot"), 0.022, 1), "foot." + s)
        V, F = M.box(0.16, 0.12, 0.08, center=(hx, -0.2, 0.04))
        add(M.bevel(O.P(V, F, "BH_Bronze", "toe"), 0.02, 1), "toe." + s)
        add(O.ring((hx, -0.03, 0.105), (0, 0, 1), 0.07, 0.012, "BH_Gold", n=16, m=4), "foot." + s)
