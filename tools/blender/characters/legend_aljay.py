"""Aljay, the Forsaken Hero (bh-021, work/lemondev/bh-021/contracts/story.md): Class SX, Lv 287.

Black dragon-scale plate fused with the Dusk Tyrant's hide, crimson trim, a Tyrant heart (a slit-pupil crimson gem)
in the chest with glowing blood-veins cracking out of it; wing-sheath pauldrons with horns, clawed gauntlets, finned
vambraces, spiked knees, clawed sabatons; a horned dragon helm whose snout visor hides the face and whose eye-slits
burn red; a dorsal ridge of spines and a torn crimson cape in two tails. His lance (Dusk-Piercer) is a separate
weapon GLB (legend_weapons.py). Authored on the standard skeleton; the game scales him to ~2.05 m.
"""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, interp_rows, front_y, back_y, dome, M_align_z, fan_plate, fist, smoothstep
from bh_math import normalize, R_axis, Rz
from bh_skeleton import proportions
from char_knight import thick_band, chest_spine_w, CAPE_BONES, secondary as _knight_secondary
from town_matron import P_, outward, Kit
import legend_kit as LK

PROPS = proportions(1.0, shoulder_x=0.2)
PALETTE = "aljay"
EXTRA_BONES = CAPE_BONES
CLIPS_ONLY = ["idle", "idle_spear", "walk", "run", "spear_1", "spear_heavy", "hit_heavy", "death",
              "cs_aj_kneel", "cs_aj_rise", "cs_aj_point", "cs_aj_clutch", "cs_aj_charge", "cs_aj_chained",
              "cs_aj_dragged", "cs_aj_stand"]
PREVIEW_HEIGHT = 2.1

PALETTE_COLORS = {
    "BH_DragonPlate": LK.mat((0.045, 0.038, 0.042), 0.8, 0.4),
    "BH_DarkSteel": LK.mat((0.05, 0.045, 0.05), 0.75, 0.46),
    "BH_Crimson": LK.mat((0.45, 0.03, 0.035), 0.85, 0.3),
    "BH_Horn": LK.mat((0.035, 0.026, 0.026), 0.0, 0.5),
    "BH_Fang": LK.mat((0.66, 0.6, 0.5), 0.0, 0.5),
    "BH_Mail": LK.mat((0.09, 0.085, 0.09), 1.0, 0.45),
    "BH_Leather": LK.mat((0.07, 0.03, 0.025), 0.0, 0.6),
    "BH_Cloth_Primary": LK.mat((0.2, 0.008, 0.012), 0.0, 0.9),
    "BH_Emissive": LK.mat((1.0, 0.12, 0.07), 0.0, 0.4, (1.0, 0.06, 0.025), 9.0),
    "BH_Shadow": LK.mat((0.012, 0.008, 0.01), 0.0, 0.95),
}

TORSO = [
    (0.96, 0.168, 0.12, 0.12, 0.0),
    (1.02, 0.162, 0.12, 0.114, 0.02),
    (1.10, 0.160, 0.126, 0.112, 0.06),
    (1.20, 0.172, 0.138, 0.118, 0.14),
    (1.30, 0.190, 0.152, 0.124, 0.20),
    (1.38, 0.200, 0.154, 0.128, 0.18),
    (1.45, 0.194, 0.142, 0.126, 0.10),
    (1.50, 0.162, 0.114, 0.11, 0.03),
    (1.545, 0.102, 0.082, 0.08, 0.0),
]
HIP_ROWS = [(0.56, 0.2, 0.15, 0.16, 0.0), (0.8, 0.186, 0.138, 0.146, 0.0), (1.0, 0.172, 0.128, 0.128, 0.0),
            (1.07, 0.166, 0.122, 0.118, 0.0)]

secondary = _knight_secondary


def finish_mesh(ob):
    LK.finish_mesh(ob)


def build(body):
    k = Kit(body)
    rng = np.random.default_rng(287)
    torso(k, body, rng)
    back(k, body)
    for s in "L":
        arm(k, body, s)
        leg(k, body, s)
    tassets(k, body)
    cape(k, body)
    helm(k, body)


# ------------------------------------------------------------------------------------------------------------ torso
def torso(k, body, rng):
    add = body.add
    # breastplate: dragon-scale plate with a strong keel
    V, F = torso_loft([interp_rows(TORSO, z) for z in (1.21, 1.26, 1.3, 1.34, 1.38, 1.42, 1.45, 1.48, 1.5, 1.525, 1.545)],
                      n=32, cap1=True)
    add(M.bevel(P_(V, F, "BH_DragonPlate", "breastplate"), 0.004, 1, angle=50), weights=chest_spine_w(1.24, 1.30))
    # pectoral rims (crimson) under the chest line
    for sx in (1, -1):
        pts = [LK.on_front(TORSO, sx * x, z, 0.004) for x, z in
               ((0.01, 1.255), (0.06, 1.262), (0.11, 1.285), (0.15, 1.32), (0.175, 1.36))]
        add(LK.edge_tube(pts, 0.007, "BH_Crimson", name="pec_rim"), weights=chest_spine_w(1.24, 1.30))
    # ventral lames down the stomach, each overlapping the one below, crimson lower edges
    for i, (z0, z1) in enumerate(((1.16, 1.225), (1.105, 1.17), (1.05, 1.115), (0.995, 1.06))):
        V, F = thick_band(TORSO, z0, z1, 0.012 + 0.004 * i, 0.0, n=30)
        add(M.bevel(P_(V, F, "BH_DarkSteel", "lame"), 0.003, 1), weights=k.torso_w())
        V, F = thick_band(TORSO, z0 - 0.004, z0 + 0.008, 0.018 + 0.004 * i, 0.006, n=30)
        add(P_(V, F, "BH_Crimson", "lame_rim"), weights=k.torso_w())
    # the Tyrant heart: a slit-pupil crimson gem in a crimson setting, veins cracking out of it
    zc = 1.37
    yc = front_y(TORSO, 0, zc) - 0.016
    add(LK.gem((0, yc, zc), 0.03, scale=(1.0, 0.45, 1.3), name="heart"), weights=chest_spine_w(1.24, 1.30))
    V, F = M.box(0.006, 0.01, 0.05, center=(0, yc - 0.013, zc))
    add(P_(V, F, "BH_Shadow", "pupil"), weights=chest_spine_w(1.24, 1.30))
    ring = [np.array((0.042 * math.sin(a), yc + 0.004 - 0.006 * math.cos(a) ** 2, zc + 0.052 * math.cos(a)))
            for a in np.linspace(0, 2 * math.pi, 25)]
    V, F = M.tube(ring, [(0.008, 0.008)] * 25, n=6, up=(0, -1, 0), cap0=False, cap1=False)
    add(P_(V, F, "BH_Crimson", "heart_ring"), weights=chest_spine_w(1.24, 1.30))
    for a in range(6):   # claw prongs gripping the gem
        ang = a * math.pi / 3 + math.pi / 6
        base = np.array((0.05 * math.sin(ang), yc + 0.004, zc + 0.062 * math.cos(ang)))
        add(LK.spike(base, (math.sin(ang), -0.5, math.cos(ang)), 0.03, 0.006, "BH_Horn"), weights=chest_spine_w(1.24, 1.30))
    seeds = [((0.0, zc), a) for a in (0.3, 1.1, 2.0, 2.9, 3.6, 4.4, 5.2, 5.9)]
    for p in LK.veins(TORSO, seeds, rng, steps=9, step=0.024, off=0.0025, zlim=(1.02, 1.5), xlim=0.18):
        add(p, weights=chest_spine_w(1.24, 1.30))
    # gorget: tall flared collar with spines round the back
    prof = [(0.17, 1.45), (0.15, 1.49), (0.11, 1.53), (0.095, 1.575), (0.105, 1.61), (0.09, 1.61), (0.078, 1.57),
            (0.095, 1.53), (0.14, 1.49), (0.162, 1.45), (0.17, 1.45)]
    V, F = M.lathe(prof, 28, cap=False)
    g = P_(V, F, "BH_DarkSteel", "gorget").scale((1.0, 0.86, 1.0))
    add(g, "chest")
    V, F = M.lathe([(0.108, 1.603), (0.112, 1.612), (0.1, 1.618), (0.094, 1.61)], 28, cap=False)
    add(P_(V, F, "BH_Crimson", "gorget_rim").scale((1.0, 0.86, 1.0)), "chest")
    for i, a in enumerate(np.linspace(math.radians(40), math.radians(320), 7)):
        # a = angle from the front (0) round by the left; skip the throat
        x, y = 0.1 * math.sin(a), -0.088 * math.cos(a)
        d = (math.sin(a) * 0.35, -math.cos(a) * 0.35 + 0.25, 1.0)
        L = 0.07 + 0.03 * (abs(math.cos(a)) > 0.8)
        add(LK.fin((x, y, 1.6), d, L, 0.022, 0.006, (math.cos(a), math.sin(a), 0), -25, n=6, mat="BH_Horn",
                   up=(math.cos(a), math.sin(a), 0.0), tip=1.2), "chest")
    # belt with a dragon-skull buckle
    V, F = thick_band(TORSO, 0.985, 1.03, 0.03, 0.012, n=30)
    add(M.bevel(P_(V, F, "BH_Leather", "belt"), 0.003, 1), "hips")
    by = front_y(TORSO, 0, 1.005) - 0.034
    skull = [(0.0, by - 0.045, 1.0), (0.0, by - 0.02, 1.012), (0.0, by, 1.018)]
    V, F = M.tube(skull[::-1], [(0.042, 0.03), (0.034, 0.026), (0.018, 0.016)], n=10, up=(0, 0, 1), p=2.6)
    add(outward(P_(V, F, "BH_DarkSteel", "buckle")), "hips")
    for sx in (1, -1):
        add(LK.horn((sx * 0.03, by - 0.01, 1.03), (sx * 0.6, 0.3, 0.75), 0.06, 0.009, (0, 1, 0), sx * 30, n=6), "hips")
        add(LK.gem((sx * 0.016, by - 0.036, 1.02), 0.006, scale=(1.4, 0.5, 0.6)), "hips")
    for i in range(4):
        x = -0.021 + 0.014 * i
        add(LK.spike((x, by - 0.05, 0.985), (0, -0.2, -1.0), 0.02, 0.004, "BH_Fang"), "hips")


def back(k, body):
    """Dorsal ridge: flat spines down the spine between the two cape tails."""
    for i, z in enumerate(np.linspace(1.5, 1.06, 8)):
        yb = back_y(TORSO, 0, z) + 0.004
        L = 0.105 - 0.007 * i
        w = chest_spine_w(1.24, 1.30) if z > 1.2 else k.torso_w()
        body.add(LK.fin((0, yb, z), (0, 0.75, 0.66), L, 0.03, 0.007, (1, 0, 0), -30, n=7, mat="BH_Horn",
                        up=(1, 0, 0), tip=1.1), weights=w)
        V, F = M.sphere(0.018, 8, 5, center=(0, yb - 0.004, z), scale=(1.0, 0.5, 1.2))
        body.add(P_(V, F, "BH_DarkSteel", "spine_plate"), weights=w)


# ------------------------------------------------------------------------------------------------------------ arms
def arm(k, body, s):
    am = lambda part, bone=None, weights=None: body.add_mirror(part, bone, weights)
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    am(body.limb(ua, [(-0.05, 0.062, 0.062), (0.5, 0.058, 0.06), (1.0, 0.05, 0.052)], "BH_Mail", n=12), ua)
    rb = body.limb(ua, [(0.36, 0.066, 0.068), (0.4, 0.064, 0.066), (0.95, 0.056, 0.058)], "BH_DragonPlate", n=14, p=2.3)
    am(M.bevel(rb, 0.003, 1, angle=50), ua)
    el = body.head(fa)
    V, F = dome(el + (0.0, 0.032, 0.0), (0, 1, 0.1), 0.056, a_max=80, n=14, rings=5)
    am(M.solidify(P_(V, F, "BH_DarkSteel", "couter"), 0.006, offset=-1, bevel_w=0.002),
       weights=lambda V, ua=ua, fa=fa: [{ua: 0.5, fa: 0.5}] * len(V))
    am(LK.horn(el + (0.0, 0.07, 0.0), (0.1, 1.0, -0.25), 0.11, 0.016, (1, 0, 0), -25, n=7), fa)
    vb = body.limb(fa, [(0.08, 0.054, 0.056), (0.5, 0.05, 0.052), (0.9, 0.045, 0.046), (1.02, 0.056, 0.056)],
                   "BH_DragonPlate", n=14, p=2.3)
    am(M.bevel(vb, 0.003, 1, angle=50), fa)
    # three fins along the outer forearm, raking back toward the elbow
    wr = body.head(ha)
    for i, t in enumerate((0.25, 0.5, 0.75)):
        c = el + (wr - el) * t
        base = c + np.array([0.05, 0.012, 0.0])
        am(LK.fin(base, (0.55, 0.45, 0.7 - 0.1 * i), 0.09 - 0.012 * i, 0.028, 0.006, (0, 0, 1), 20, n=6,
                  mat="BH_Horn", up=(0, 1, 0), tip=1.0), fa)
    V, F = M.tube([el + (wr - el) * 0.93, el + (wr - el) * 1.0], [(0.062, 0.062), (0.064, 0.064)], n=14, up=(0, -1, 0))
    am(P_(V, F, "BH_Crimson", "cuff_rim"), fa)
    for prt in fist(body, s, "BH_DragonPlate", "BH_Mail"):
        am(prt, ha)
    for prt in LK.claws(body, s, "BH_Horn", 0.045, 0.009):
        am(prt, ha)
    for prt in pauldron(body, s):
        am(prt, ua)


def pauldron(body, s):
    parts = []
    sh = body.head("upper_arm." + s)
    el = body.head("forearm." + s)
    armdir = normalize(el - sh)
    out = np.array([1.0, 0, 0])
    axis = normalize(out * 0.72 + np.array([0, 0.05, 1.0]) * 0.8)
    c = sh + np.array([0.01, 0.0, 0.012])
    R0 = 0.15
    V, F = dome(c, axis, R0, a_max=78, n=22, rings=7, scale=(1.0, 1.15, 1.0), up_hint=(0, 0, 1))
    parts.append(M.solidify(P_(V, F, "BH_DragonPlate", "pauldron"), 0.01, offset=-1, bevel_w=0.003))
    Rm = M_align_z(axis, (0, 0, 1))
    rim = []
    for i in range(33):
        a = 2 * math.pi * i / 32
        r = R0 * math.sin(math.radians(78))
        z = R0 * math.cos(math.radians(78))
        rim.append(c + Rm @ np.array([r * math.cos(a), r * math.sin(a) * 1.15, z]))
    V, F = M.tube(rim, [(0.009, 0.009)] * len(rim), n=6, up=axis, cap0=False, cap1=False)
    parts.append(P_(V, F, "BH_Crimson", "pauldron_rim"))
    # second, smaller over-plate lapping the top of the dome
    V, F = dome(c + axis * 0.03 + np.array([-0.01, 0, 0.01]), axis, 0.12, a_max=60, n=18, rings=5, scale=(1.0, 1.1, 1.0))
    parts.append(M.solidify(P_(V, F, "BH_DragonPlate", "pauldron_top"), 0.008, offset=-1, bevel_w=0.002))
    # wing sheaths: three blades sweeping up and back like folded wings
    top = c + axis * R0 * 0.9
    for i, (L, w, dy, dz) in enumerate(((0.3, 0.07, -0.02, 0.0), (0.24, 0.058, 0.035, -0.02), (0.18, 0.046, 0.08, -0.035))):
        base = top + np.array([0.035 - 0.012 * i, dy, dz])
        parts.append(LK.fin(base, (0.28, 0.18, 1.0), L, w, 0.008, (1, 0, 0), -70, n=10, mat="BH_DragonPlate",
                            up=(1, 0, 0)))
        edge = LK.curve_pts(base + np.array([0.004, -w * 0.3, 0.0]), (0.28, 0.18, 1.0), L * 0.92, (1, 0, 0), -70, 8)
        parts.append(LK.edge_tube(edge, 0.0045, "BH_Crimson", name="sheath_edge"))
    # two horns rising from the dome
    parts.append(LK.horn(c + axis * R0 * 0.75 + np.array([0.06, -0.05, 0.0]), (0.55, -0.15, 0.8), 0.17, 0.02,
                         (1, 0, 0), -45, n=9))
    parts.append(LK.horn(c + axis * R0 * 0.6 + np.array([0.1, 0.03, -0.02]), (0.8, 0.25, 0.45), 0.12, 0.016,
                         (1, 0, 0), -35, n=8))
    # lames down the arm
    ax_side = normalize(out - armdir * np.dot(out, armdir))
    ax_fwd = np.cross(armdir, ax_side)
    for i in range(3):
        t0 = 0.07 + 0.065 * i
        rr = 0.108 - 0.01 * i
        ctr = sh + armdir * (t0 + 0.04)
        loops = []
        for z_off in (0.0, 0.066):
            loop = []
            for kk in range(15):
                a = math.radians(-120 + 240 * kk / 14)
                pdir = ax_side * math.cos(a) + ax_fwd * math.sin(a) * 1.1
                loop.append(ctr + armdir * (z_off - 0.033) + pdir * (rr + 0.012 * (z_off > 0)))
            loops.append(np.array(loop))
        V, F = M.loft(loops, cap0=False, cap1=False, closed=False)
        parts.append(M.solidify(P_(V, F, "BH_DragonPlate", "lame"), 0.006, offset=1, bevel_w=0.002))
        V, F = M.tube(list(loops[1]), [(0.004, 0.004)] * 15, n=5, up=tuple(armdir), cap0=True, cap1=True)
        parts.append(P_(V, F, "BH_Crimson", "lame_edge"))
    return parts


# ------------------------------------------------------------------------------------------------------------ legs
def leg(k, body, s):
    am = lambda part, bone=None, weights=None: body.add_mirror(part, bone, weights)
    th, sh = "thigh." + s, "shin." + s
    am(body.limb(th, [(-0.02, 0.082, 0.086), (0.4, 0.074, 0.078), (0.95, 0.056, 0.058)], "BH_Mail", n=12), th)
    cu = body.limb(th, [(0.15, 0.09, 0.094), (0.2, 0.088, 0.092), (0.55, 0.081, 0.086), (0.93, 0.066, 0.07)],
                   "BH_DragonPlate", n=16, p=2.4, offs=[(0, 0.004)] * 4)
    am(M.bevel(cu, 0.003, 1, angle=50), th)
    knee = body.head(sh)
    V, F = dome(knee + (0, -0.05, 0.0), (0, -1, 0.15), 0.066, a_max=78, n=14, rings=5)
    am(M.solidify(P_(V, F, "BH_DarkSteel", "poleyn"), 0.007, offset=-1, bevel_w=0.002),
       weights=lambda V, th=th, sh=sh: [{th: 0.5, sh: 0.5}] * len(V))
    am(LK.horn(knee + (0, -0.105, 0.01), (0, -0.85, 0.5), 0.1, 0.018, (1, 0, 0), 30, n=7),
       weights=lambda V, th=th, sh=sh: [{th: 0.3, sh: 0.7}] * len(V))
    gr = body.limb(sh, [(0.03, 0.062, 0.064), (0.3, 0.068, 0.074), (0.55, 0.06, 0.064), (0.85, 0.05, 0.052),
                        (1.0, 0.054, 0.057)], "BH_DragonPlate", n=16, p=2.3,
                   offs=[(0, 0.0), (0, -0.014), (0, -0.007), (0, 0.0), (0, 0.0)])
    am(M.bevel(gr, 0.003, 1, angle=50), sh)
    kx, ky, kz = knee
    for i, dz in enumerate((0.12, 0.2, 0.28)):
        base = (kx, -0.082 + 0.008 * i, kz - dz)
        am(LK.fin(base, (0, -0.55, 0.85), 0.05 - 0.008 * i, 0.018, 0.006, (1, 0, 0), 25, n=5, mat="BH_Horn",
                  up=(1, 0, 0), tip=1.0), sh)
    vein = [(kx + 0.02, -0.075, kz - 0.08), (kx + 0.03, -0.074, kz - 0.18), (kx + 0.02, -0.066, kz - 0.3)]
    am(LK.edge_tube(vein, 0.0032, "BH_Emissive", name="leg_vein"), sh)
    for prt, bone in sabaton(body, s):
        am(prt, bone)


def sabaton(body, s):
    hx = PROPS["hip_x"]
    out = []

    def rings(spec):
        R = []
        for y, w, top in spec:
            pts = []
            for i in range(12):
                a = 2 * math.pi * i / 12
                c, sn = math.cos(a), math.sin(a)
                x = w * np.sign(c) * abs(c) ** 0.7
                z = top / 2 + top / 2 * np.sign(sn) * abs(sn) ** 0.6
                pts.append((hx + x, y, max(z, 0.012)))
            R.append(np.array(pts))
        return R
    foot = rings([(0.07, 0.04, 0.075), (0.05, 0.048, 0.1), (0.0, 0.053, 0.12), (-0.06, 0.054, 0.09), (-0.125, 0.054, 0.06)])
    V, F = M.loft(foot[::-1])
    out.append((M.bevel(P_(V, F, "BH_DragonPlate", "sabaton"), 0.003, 1, angle=45), "foot." + s))
    toe = rings([(-0.115, 0.054, 0.06), (-0.17, 0.05, 0.048), (-0.215, 0.038, 0.036), (-0.24, 0.018, 0.022)])
    V, F = M.loft(toe[::-1])
    out.append((M.bevel(P_(V, F, "BH_DarkSteel", "sabaton_toe"), 0.003, 1, angle=45), "toe." + s))
    for dx in (-0.028, 0.0, 0.028):
        out.append((LK.horn((hx + dx, -0.2 - 0.02 * (dx == 0), 0.022), (dx * 3, -1.0, -0.25), 0.06, 0.009, (1, 0, 0),
                            -30, n=6, name="toe_claw"), "toe." + s))
    out.append((LK.spike((hx, 0.07, 0.07), (0, 1, 0.2), 0.05, 0.012, "BH_Horn"), "foot." + s))
    V, F = M.box(0.11, 0.21, 0.016, center=(hx, -0.03, 0.008))
    out.append((M.bevel(P_(V, F, "BH_Leather", "sole"), 0.004, 1), "foot." + s))
    V, F = M.box(0.085, 0.1, 0.012, center=(hx, -0.18, 0.006))
    out.append((M.bevel(P_(V, F, "BH_Leather", "sole_t"), 0.004, 1), "toe." + s))
    return out


def tassets(k, body):
    w_front = body.skirt_weights(1.0, 0.62, max_leg=0.55, center_w=0.09)
    w_side = body.skirt_weights(1.0, 0.62, max_leg=0.85, center_w=0.05)
    specs = [
        (0.94, 1.06, 1.0, 0.6, 0.035, w_front),
        (0.06, 0.18, 1.01, 0.66, 0.04, w_side),
        (0.18, 0.31, 1.01, 0.64, 0.045, w_side),
        (0.31, 0.43, 1.01, 0.66, 0.045, w_side),
        (0.44, 0.56, 1.0, 0.55, 0.04, w_front),
        (0.57, 0.69, 1.01, 0.66, 0.045, w_side),
        (0.69, 0.82, 1.01, 0.64, 0.045, w_side),
        (0.82, 0.94, 1.01, 0.66, 0.04, w_side),
    ]
    for f0, f1, zt, zb, g, w in specs:
        body.add(LK.hanging_plate(HIP_ROWS, f0, f1, zt, zb, g, "BH_DragonPlate", point=0.3, n=9, nv=7, flare=0.12), weights=w)
        # crimson spine down the middle of each plate
        pts = [ring_pt(HIP_ROWS, (f0 + f1) / 2, z, g + 0.012 + 0.12 * ((zt - z) / (zt - zb)) ** 1.2) for z in
               np.linspace(zt - 0.01, zb + 0.06, 6)]
        body.add(LK.edge_tube(pts, 0.005, "BH_Crimson", name="tasset_spine"), weights=w)
    # a second, shorter layer over the hips (front and sides)
    for f0, f1 in ((0.0, 0.1), (0.9, 1.0), (0.12, 0.25), (0.75, 0.88)):
        body.add(LK.hanging_plate(HIP_ROWS, f0, f1, 1.03, 0.82, 0.062, "BH_DarkSteel", point=0.35, n=7, nv=5, flare=0.08),
                 weights=w_side)


def ring_pt(rows, frac, z, g):
    from char_mage import ring_frac
    return ring_frac(rows, max(min(z, rows[-1][0]), rows[0][0]), g, [frac])[0]


def cape(k, body):
    """Two torn crimson tails hanging from under the pauldrons, parted over the dorsal ridge."""
    w = LK.cape_weights()
    for x0, x1, seed in ((0.03, 0.23, 11), (-0.23, -0.03, 12)):
        body.add(LK.cape_panel(TORSO, x0, x1, 1.46, 0.3, seed, back_off=0.04, flare=0.22, nu=9, nv=16,
                               depth_curve=0.1, tear=0.09, solid=0.011), weights=w)
    # clasps at the shoulders: crimson discs with a claw
    for sx in (1, -1):
        c = np.array((sx * 0.14, back_y(TORSO, sx * 0.14, 1.46) + 0.035, 1.47))
        V, F = M.tube([c + (0, -0.006, 0), c + (0, 0.012, 0)], [(0.028, 0.028), (0.03, 0.03)], n=12, up=(0, 0, 1))
        body.add(outward(P_(V, F, "BH_Crimson", "clasp")), "chest")


# ------------------------------------------------------------------------------------------------------------ helm
HELM = [
    (1.555, 0.092, 0.104, 0.104, 0.0, 0.0),
    (1.60, 0.1, 0.114, 0.11, 0.04, -0.004),
    (1.66, 0.106, 0.124, 0.118, 0.08, -0.008),
    (1.72, 0.108, 0.128, 0.122, 0.08, -0.008),
    (1.78, 0.104, 0.12, 0.12, 0.04, -0.004),
    (1.83, 0.09, 0.1, 0.106, 0.0, 0.0),
    (1.865, 0.062, 0.068, 0.076, 0.0, 0.004),
    (1.884, 0.026, 0.03, 0.034, 0.0, 0.006),
]


def helm(k, body):
    add = lambda p: body.add(p, "head")
    V, F = torso_loft(HELM, n=30, p=2.5, cap1=True)
    add(M.bevel(P_(V, F, "BH_DragonPlate", "helm"), 0.003, 1, angle=55))
    # the maw: a dark opening in front of the face, framed by the snout above and the jaw below
    maw = []
    for z in (1.62, 1.7):
        r = interp_rows(HELM, z)
        maw.append(np.array([(0.075 * math.sin(a), -0.128 - 0.01 * math.cos(a * 2), z) for a in np.linspace(-1.2, 1.2, 9)]))
    V, F = M.loft(maw, cap0=False, cap1=False, closed=False)
    add(M.solidify(P_(V, F, "BH_Shadow", "maw"), 0.004, offset=1.0))
    # upper snout visor: a keeled wedge from the brow down to a hooked tip
    path = LK.curve_pts((0, -0.105, 1.745), (0, -0.86, -0.5), 0.15, (1, 0, 0), 18, 7)
    prof = []
    for i in range(7):
        t = i / 6
        prof.append((0.058 * (1 - 0.55 * t) + 0.006, 0.036 * (1 - 0.45 * t) + 0.004, 1.7))
    V, F = M.tube(path, prof, n=12, up=(0, 0, 1), offsets=[(0, 0.012 * (1 - i / 6)) for i in range(7)])
    add(outward(M.bevel(P_(V, F, "BH_DragonPlate", "snout"), 0.003, 1, angle=45)))
    ridge = [p + np.array([0, 0.0, 0.034 * (1 - i / 6) + 0.006]) for i, p in enumerate(path)]
    add(LK.edge_tube(ridge, 0.008, "BH_Crimson", name="snout_ridge"))
    # upper fangs along the snout's lower edge
    for i in range(1, 6):
        p = path[i]
        wdt = 0.07 * (1 - 0.62 * i / 6)
        for sx in (1, -1):
            add(LK.spike(p + np.array([sx * wdt * 0.8, 0, -0.02]), (sx * 0.1, -0.2, -1.0), 0.028 - 0.002 * i, 0.005, "BH_Fang"))
    # nostrils
    for sx in (1, -1):
        add(LK.gem(path[-1] + np.array([sx * 0.016, -0.008, 0.012]), 0.006, "BH_Shadow", scale=(1.3, 0.6, 0.8)))
    # lower jaw guard with fangs pointing up
    jaw = LK.curve_pts((0, -0.1, 1.6), (0, -1.0, 0.2), 0.1, (1, 0, 0), -10, 5)
    V, F = M.tube(jaw, [(0.072 - 0.008 * i, 0.022, 1.8) for i in range(5)], n=12, up=(0, 0, 1))
    add(outward(M.bevel(P_(V, F, "BH_DragonPlate", "jaw"), 0.003, 1, angle=45)))
    for i in range(1, 5):
        for sx in (1, -1):
            add(LK.spike(jaw[i] + np.array([sx * (0.06 - 0.008 * i), 0, 0.018]), (0, -0.2, 1.0), 0.024, 0.005, "BH_Fang"))
    # cheek guards sweeping back into spines
    for sx in (1, -1):
        base = np.array((sx * 0.108, -0.07, 1.64))
        add(LK.fin(base, (sx * 0.25, 1.0, 0.1), 0.2, 0.05, 0.008, (0, 0, 1), sx * 12, n=8, mat="BH_DragonPlate",
                   up=(1, 0, 0), tip=1.2))
        add(LK.fin(base + (0, 0, 0.045), (sx * 0.3, 1.0, 0.3), 0.14, 0.03, 0.006, (0, 0, 1), sx * 12, n=6, mat="BH_Horn",
                   up=(1, 0, 0), tip=1.2))
    # eyes: burning slits, angled like a frown, under heavy brow ridges
    for sx in (1, -1):
        c = np.array((sx * 0.074, -0.118, 1.742))
        V, F = M.box(0.05, 0.014, 0.011)
        e = P_(V, F, "BH_Emissive", "eye").rot(R_axis((0, 1, 0), sx * 18)).rot(Rz(sx * -38)).move(c)
        add(e)
        brow = [np.array((sx * 0.03, -0.134, 1.762)), np.array((sx * 0.07, -0.126, 1.77)),
                np.array((sx * 0.095, -0.1, 1.79)), np.array((sx * 0.12, -0.05, 1.81))]
        V, F = M.tube(brow, [(0.012, 0.01), (0.016, 0.012), (0.014, 0.011), (0.006, 0.006)], n=8, up=(0, -0.3, 1))
        add(outward(P_(V, F, "BH_DragonPlate", "brow")))
    # great horns: back from the temples, curling upward; lesser horns below them
    for sx in (1, -1):
        add(LK.horn((sx * 0.085, -0.03, 1.8), (sx * 0.3, 0.9, 0.3), 0.42, 0.034, (1, 0, 0), 62, n=12))
        add(LK.horn((sx * 0.1, -0.0, 1.735), (sx * 0.55, 0.85, -0.05), 0.24, 0.022, (1, 0, 0), 30, n=9))
        add(LK.horn((sx * 0.105, 0.03, 1.68), (sx * 0.45, 0.9, -0.3), 0.14, 0.014, (1, 0, 0), 15, n=7))
    # crest of spines over the crown and down the nape
    for i, (y, z, L) in enumerate(((-0.07, 1.86, 0.07), (-0.02, 1.885, 0.1), (0.035, 1.878, 0.11), (0.08, 1.85, 0.1),
                                   (0.112, 1.8, 0.08), (0.125, 1.74, 0.06))):
        add(LK.fin((0, y, z), (0, 0.65, 0.76), L, 0.028, 0.006, (1, 0, 0), -35, n=6, mat="BH_Horn", up=(1, 0, 0), tip=1.1))
    # nape guard lames
    for i, z in enumerate((1.6, 1.565)):
        loop = []
        for a in np.linspace(math.radians(110), math.radians(250), 11):
            loop.append((0.1 * math.sin(a) * 1.05, 0.11 * -math.cos(a) + 0.012 * i, z))
        loop2 = [(x * 1.06, y * 1.06 + 0.01, z - 0.045) for x, y, z in loop]
        V, F = M.loft([np.array(loop2), np.array(loop)], cap0=False, cap1=False, closed=False)
        body.add(M.solidify(P_(V, F, "BH_DragonPlate", "nape"), 0.006, offset=1.0),
                 weights=lambda V: [{"head": 0.6, "neck": 0.4}] * len(V))
