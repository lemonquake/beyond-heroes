"""Kethrax, Chain-Marshal of the Forsaken (bh-021, contracts/story.md) — the commander who chained Aljay on the Weeping
Causeway three winters ago; boss of the Weeping Causeway.

Tall and gaunt in rusted, pitted forsaken iron: a rib-plated cuirass split by the wound Aljay's lance left in it (a
jagged crimson fissure that never closed, shards of the lance-head still standing in it), chains wound round his
chest and forearms, broken shackles hanging from his wrists, a spiked gorget, a great spiked pauldron on the left
shoulder hung with chains and a layered one on the right, a torn grey-black tabard and cape, and a tall caged helm
with forward-curling horns, a crown of iron spikes and violet soulfire eyes behind the bars. His weapon is the
kethrax_mace GLB. Authored on the standard skeleton; the game scales him up (boss).
"""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, interp_rows, front_y, back_y, dome, M_align_z, fist, smoothstep
from bh_math import normalize, R_axis, Rz
from bh_skeleton import proportions
from char_knight import thick_band, chest_spine_w, CAPE_BONES, secondary as _knight_secondary
from town_matron import P_, outward, Kit
import legend_kit as LK

PROPS = proportions(1.0, shoulder_x=0.205, hip_x=0.098)
PALETTE = "kethrax"
EXTRA_BONES = CAPE_BONES
CLIPS = ["boss_sweep", "boss_slam", "boss_charge", "boss_roar", "boss_summon", "cast_heavy", "axe_1", "axe_2",
         "cs_kx_emerge", "cs_kx_pull", "cs_kx_bind", "cs_kx_kneel"]
PREVIEW_HEIGHT = 2.1

PALETTE_COLORS = {
    "BH_ForsakenIron": LK.mat((0.85, 0.85, 0.85), 0.85, 0.55),
    "BH_DarkSteel": LK.mat((0.05, 0.045, 0.055), 0.8, 0.45),
    "BH_Cloth_Primary": LK.mat((0.06, 0.055, 0.06), 0.0, 0.92),
    "BH_Leather": LK.mat((0.06, 0.04, 0.035), 0.0, 0.65),
    "BH_Bone": LK.mat((0.55, 0.5, 0.42), 0.0, 0.6),
    "BH_Emissive": LK.mat((0.62, 0.35, 1.0), 0.0, 0.4, (0.6, 0.3, 1.0), 8.0),
    "BH_Wound": LK.mat((1.0, 0.1, 0.05), 0.0, 0.4, (1.0, 0.07, 0.03), 7.0),
    "BH_Shadow": LK.mat((0.01, 0.008, 0.012), 0.0, 0.95),
}

TORSO = [
    (0.96, 0.15, 0.108, 0.112, 0.0),
    (1.04, 0.14, 0.106, 0.104, 0.02),
    (1.12, 0.145, 0.112, 0.104, 0.05),
    (1.22, 0.168, 0.13, 0.112, 0.1),
    (1.32, 0.19, 0.142, 0.12, 0.12),
    (1.4, 0.2, 0.142, 0.126, 0.1),
    (1.46, 0.194, 0.132, 0.126, 0.06),
    (1.505, 0.16, 0.108, 0.108, 0.02),
    (1.545, 0.1, 0.08, 0.078, 0.0),
]

secondary = _knight_secondary


def finish_mesh(ob):
    LK.finish_mesh(ob)


def build(body):
    k = Kit(body)
    rng = np.random.default_rng(3)
    torso(k, body, rng)
    for s in "LR":
        arm(k, body, s)
    for s in "L":
        leg(k, body, s)
    skirt(k, body)
    helm(k, body)


def torso(k, body, rng):
    add = body.add
    cw = chest_spine_w(1.24, 1.30)
    V, F = torso_loft([interp_rows(TORSO, z) for z in np.linspace(1.12, 1.545, 12)], n=32, cap1=True)
    add(M.bevel(P_(V, F, "BH_ForsakenIron", "cuirass"), 0.004, 1, angle=50), weights=lambda V: [
        ({"chest": 1.0} if v[2] > 1.3 else {"spine": 1.0} if v[2] < 1.2 else {"chest": 0.5, "spine": 0.5}) for v in V])
    # rib plates: curved bars across the front like a cage of ribs
    for i, z in enumerate(np.linspace(1.18, 1.44, 6)):
        for sx in (1, -1):
            pts = [LK.on_front(TORSO, sx * x, z - 0.03 * (x / 0.18) ** 2, 0.004) for x in np.linspace(0.02, 0.17, 6)]
            V, F = M.tube(pts, [(0.009, 0.006)] * 6, n=6, up=(0, -1, 0))
            add(outward(P_(V, F, "BH_DarkSteel", "rib")), weights=cw)
    V, F = M.tube([LK.on_front(TORSO, 0, z, 0.005) for z in np.linspace(1.15, 1.5, 6)], [(0.014, 0.01)] * 6, n=6, up=(0, -1, 0))
    add(outward(P_(V, F, "BH_DarkSteel", "sternum")), weights=cw)
    # the wound: a jagged crimson fissure across the left breast, lance-head shards standing in it
    pts = []
    for t in np.linspace(0, 1, 9):
        x = 0.03 + 0.12 * t
        z = 1.44 - 0.16 * t + 0.012 * math.sin(t * 17)
        pts.append(LK.on_front(TORSO, x, z, 0.001))
    V, F = M.tube(pts, [(0.012 * math.sin(math.pi * t) + 0.003, 0.004) for t in np.linspace(0, 1, 9)], n=6, up=(0, -1, 0))
    add(P_(V, F, "BH_Wound", "wound"), weights=cw)
    for t in (0.3, 0.5, 0.7):
        base = pts[int(t * 8)]
        add(LK.spike(base, (0.3 * rng.normal(), -1.0, 0.3 * rng.normal()), 0.05 + 0.02 * t, 0.009, "BH_DarkSteel", n=4), weights=cw)
    for p in LK.veins(TORSO, [((0.09, 1.36), a) for a in (0.5, 2.2, 3.8, 5.3)], rng, steps=5, step=0.018, off=0.0035,
                      r=0.0025, mat="BH_Wound", zlim=(1.2, 1.5), xlim=0.19):
        add(p, weights=cw)
    # waist: dark iron lames
    for i, (z0, z1) in enumerate(((1.06, 1.12), (1.0, 1.065))):
        V, F = thick_band(TORSO, z0, z1, 0.014 + 0.004 * i, 0.0, n=30)
        add(M.bevel(P_(V, F, "BH_DarkSteel", "lame"), 0.003, 1), weights=k.torso_w())
    # chains wound round the chest
    def cfn(z):
        r = interp_rows(TORSO, z)
        return (0.0, 0.0, r[1] + 0.02, r[2] + 0.024)
    for ph in (0.0, 2.6):
        for prt in LK.chain(LK.helix_pts(cfn, 1.1, 1.46, 1.1, 50, ph), 0.03, 0.005):
            add(prt, weights=k.torso_w())
    # spiked gorget
    prof = [(0.18, 1.46), (0.15, 1.5), (0.11, 1.54), (0.1, 1.6), (0.086, 1.6), (0.08, 1.55), (0.14, 1.5), (0.17, 1.46), (0.18, 1.46)]
    V, F = M.lathe(prof, 26, cap=False)
    add(P_(V, F, "BH_ForsakenIron", "gorget").scale((1, 0.86, 1)), "chest")
    for a in np.linspace(0.6, 2 * math.pi - 0.6, 8):
        add(LK.spike((0.1 * math.sin(a), -0.086 * math.cos(a), 1.595), (math.sin(a) * 0.5, -math.cos(a) * 0.5, 1.0), 0.06,
                     0.009, "BH_DarkSteel"), "chest")
    # chain belt with a skull
    V, F = thick_band(TORSO, 0.965, 1.0, 0.026, 0.008, n=30)
    add(P_(V, F, "BH_Leather", "belt"), "hips")
    ring = LK.helix_pts(lambda z: (0, 0, 0.176, 0.136), 0.975, 0.99, 1.0, 40)
    for prt in LK.chain(ring, 0.028, 0.0045):
        add(prt, "hips")
    by = front_y(TORSO, 0, 0.98) - 0.03
    V, F = M.sphere(0.035, 10, 8, center=(0, by - 0.01, 0.985), scale=(0.9, 0.9, 1.05))
    add(outward(P_(V, F, "BH_Bone", "skull")), "hips")
    for sx in (1, -1):
        add(LK.gem((sx * 0.012, by - 0.04, 0.992), 0.008, "BH_Shadow", scale=(1, 0.5, 1.1)), "hips")
    # cape: three torn grey tails
    w = LK.cape_weights()
    for x0, x1, seed in ((-0.24, -0.08, 5), (-0.08, 0.08, 6), (0.08, 0.24, 7)):
        add(LK.cape_panel(TORSO, x0, x1, 1.47, 0.18, seed, back_off=0.05, flare=0.25, nu=7, nv=16, depth_curve=0.12,
                          tear=0.12, solid=0.01), weights=w)


def arm(k, body, s):
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    sx = 1.0 if s == "L" else -1.0
    add = body.add
    add(body.limb(ua, [(-0.05, 0.06, 0.06), (0.5, 0.056, 0.058), (1.0, 0.05, 0.052)], "BH_DarkSteel", n=12), ua)
    rb = body.limb(ua, [(0.3, 0.066, 0.068), (0.95, 0.058, 0.06)], "BH_ForsakenIron", n=14, p=2.3)
    add(M.bevel(rb, 0.003, 1, angle=50), ua)
    el = body.head(fa)
    wr = body.head(ha)
    V, F = dome(el + (0.0, 0.03, 0.0), (0, 1, 0.1), 0.055, a_max=80, n=12, rings=5)
    add(M.solidify(P_(V, F, "BH_ForsakenIron", "couter"), 0.006, offset=-1), weights=lambda V, ua=ua, fa=fa: [{ua: 0.5, fa: 0.5}] * len(V))
    add(LK.spike(el + (0, 0.075, 0), (0, 1, -0.3), 0.08, 0.014, "BH_DarkSteel"), fa)
    vb = body.limb(fa, [(0.05, 0.056, 0.058), (0.5, 0.052, 0.054), (1.0, 0.058, 0.058)], "BH_ForsakenIron", n=14, p=2.3)
    add(M.bevel(vb, 0.003, 1, angle=50), fa)
    d = normalize(wr - el)
    side = normalize(np.cross(d, (0, 1, 0)))
    up = np.cross(side, d)
    pts = []
    for i in range(40):
        t = i / 39
        a = t * 3.2 * 2 * math.pi
        pts.append(el + d * (0.04 + 0.2 * t) + (side * math.cos(a) + up * math.sin(a)) * 0.064)
    for prt in LK.chain(pts, 0.026, 0.0042):
        add(prt, fa)
    # shackle at the wrist, a broken chain hanging from it
    V, F = M.tube([wr - d * 0.03, wr + d * 0.01], [(0.066, 0.066)] * 2, n=14, up=tuple(up))
    add(outward(P_(V, F, "BH_DarkSteel", "shackle")), fa)
    hang = [wr + np.array([0, -0.02, -0.02]), wr + np.array([sx * 0.01, -0.03, -0.1]), wr + np.array([sx * 0.02, -0.02, -0.2])]
    for prt in LK.chain(hang, 0.03, 0.0048):
        add(prt, fa)
    for prt in fist(body, s, "BH_ForsakenIron", "BH_DarkSteel", scale=1.1):
        add(prt, ha)
    for prt in LK.claws(body, s, "BH_DarkSteel", 0.03, 0.008):
        add(prt, ha)
    add_p = lambda p: add(p, ua)
    sh = body.head(ua)
    axis = normalize(np.array([sx * 0.75, 0.0, 0.85]))
    c = sh + np.array([sx * 0.01, 0, 0.012])
    big = s == "L"
    R0 = 0.165 if big else 0.13
    V, F = dome(c, axis, R0, a_max=76, n=20, rings=6, scale=(1.0, 1.12, 1.0))
    add_p(M.solidify(P_(V, F, "BH_ForsakenIron", "pauldron"), 0.01, offset=-1, bevel_w=0.003))
    Rm = M_align_z(axis, (0, 0, 1))
    if big:
        for i, (a, L) in enumerate(((-0.6, 0.16), (0.1, 0.2), (0.8, 0.15))):
            base = c + Rm @ np.array([R0 * 0.6 * math.cos(a), R0 * 0.6 * math.sin(a), R0 * 0.75])
            add_p(LK.spike(base, Rm @ np.array([0.35 * math.cos(a), 0.35 * math.sin(a), 1.0]), L, 0.022, "BH_DarkSteel", n=6))
        for a in (-1.2, -0.3, 0.6):
            top = c + Rm @ np.array([R0 * 0.95 * math.cos(a), R0 * 0.95 * math.sin(a) * 1.1, R0 * 0.25])
            for prt in LK.chain([top, top + np.array([0, -0.01, -0.12]), top + np.array([0.01, 0.0, -0.24])], 0.03, 0.0045):
                add_p(prt)
    else:
        for i in range(2):
            V, F = dome(c + axis * 0.02 * (i + 1), axis, R0 * (0.85 - 0.18 * i), a_max=60, n=16, rings=4, scale=(1.0, 1.1, 1.0))
            add_p(M.solidify(P_(V, F, "BH_ForsakenIron", "pauldron_layer"), 0.008, offset=-1))


def leg(k, body, s):
    am = lambda part, bone=None, weights=None: body.add_mirror(part, bone, weights)
    th, sh = "thigh." + s, "shin." + s
    am(body.limb(th, [(-0.02, 0.078, 0.082), (0.5, 0.07, 0.074), (0.95, 0.054, 0.056)], "BH_DarkSteel", n=12), th)
    cu = body.limb(th, [(0.2, 0.084, 0.088), (0.6, 0.078, 0.082), (0.93, 0.064, 0.068)], "BH_ForsakenIron", n=14, p=2.4)
    am(M.bevel(cu, 0.003, 1, angle=50), th)
    knee = body.head(sh)
    V, F = dome(knee + (0, -0.048, 0.0), (0, -1, 0.15), 0.062, a_max=78, n=12, rings=5)
    am(M.solidify(P_(V, F, "BH_ForsakenIron", "poleyn"), 0.007, offset=-1), weights=lambda V, th=th, sh=sh: [{th: 0.5, sh: 0.5}] * len(V))
    am(LK.spike(knee + (0, -0.1, 0.0), (0, -1, 0.3), 0.07, 0.014, "BH_DarkSteel"), weights=lambda V, th=th, sh=sh: [{th: 0.3, sh: 0.7}] * len(V))
    gr = body.limb(sh, [(0.03, 0.06, 0.062), (0.35, 0.066, 0.07), (0.8, 0.052, 0.054), (1.0, 0.056, 0.058)], "BH_ForsakenIron",
                   n=14, p=2.3, offs=[(0, 0), (0, -0.01), (0, 0), (0, 0)])
    am(M.bevel(gr, 0.003, 1, angle=50), sh)
    hx = PROPS["hip_x"]
    foot = []
    for y, w, top in ((0.07, 0.04, 0.075), (0.0, 0.052, 0.12), (-0.08, 0.052, 0.08), (-0.2, 0.03, 0.04), (-0.27, 0.006, 0.02)):
        foot.append(np.array([(hx + w * np.sign(math.cos(a)) * abs(math.cos(a)) ** 0.7, y,
                               max(top / 2 + top / 2 * np.sign(math.sin(a)) * abs(math.sin(a)) ** 0.6, 0.012))
                              for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]))
    V, F = M.loft(foot[::-1])
    part = outward(P_(V, F, "BH_ForsakenIron", "sabaton"))
    am(part, weights=lambda V: [({"foot.L": 1.0} if v[1] > -0.12 else {"toe.L": 1.0}) for v in V])


def skirt(k, body):
    """Torn tabard hanging front and back to the shins, over iron tassets."""
    from legend_aljay import HIP_ROWS
    w = body.skirt_weights(1.0, 0.5, max_leg=0.75, center_w=0.08)
    for f0, f1, seed in ((0.93, 1.07, 1), (0.43, 0.57, 2)):
        body.add(LK.hanging_plate(HIP_ROWS, f0, f1, 1.0, 0.38, 0.03, "BH_Cloth_Primary", point=0.9, n=9, nv=10, flare=0.1),
                 weights=w)
    for f0, f1 in ((0.1, 0.24), (0.24, 0.38), (0.62, 0.76), (0.76, 0.9)):
        body.add(LK.hanging_plate(HIP_ROWS, f0, f1, 1.0, 0.74, 0.05, "BH_ForsakenIron", point=0.4, n=7, nv=5, flare=0.08),
                 weights=body.skirt_weights(1.0, 0.7, max_leg=0.8, center_w=0.05))


HELM = [
    (1.555, 0.094, 0.106, 0.106, 0.0, 0.0),
    (1.62, 0.1, 0.116, 0.112, 0.05, -0.004),
    (1.7, 0.104, 0.12, 0.118, 0.06, -0.006),
    (1.78, 0.102, 0.116, 0.118, 0.03, -0.004),
    (1.86, 0.094, 0.104, 0.108, 0.0, 0.0),
    (1.92, 0.07, 0.078, 0.084, 0.0, 0.004),
    (1.95, 0.03, 0.034, 0.038, 0.0, 0.006),
]


def helm(k, body):
    add = lambda p: body.add(p, "head")
    V, F = torso_loft(HELM, n=30, p=2.4, cap1=True)
    add(M.bevel(P_(V, F, "BH_ForsakenIron", "helm"), 0.003, 1, angle=55))
    # the cage: a dark face opening behind vertical bars, two violet eyes
    open_ = []
    for z in (1.61, 1.8):
        open_.append(np.array([LK.on_front(HELM, x, z, 0.003) for x in np.linspace(-0.078, 0.078, 11)]))
    V, F = M.loft(open_, cap0=False, cap1=False, closed=False)
    add(M.solidify(P_(V, F, "BH_Shadow", "face"), 0.003, offset=1.0))
    for sx in (1, -1):
        add(LK.gem(LK.on_front(HELM, sx * 0.03, 1.715, 0.007), 0.012, "BH_Emissive", scale=(1.5, 0.5, 0.7), name="eye"))
    for x in np.linspace(-0.07, 0.07, 7):
        pts = [LK.on_front(HELM, x, z, 0.013) for z in (1.6, 1.66, 1.72, 1.81)]
        V, F = M.tube(pts, [(0.006, 0.006)] * 4, n=6, up=(0, -1, 0))
        add(P_(V, F, "BH_DarkSteel", "bar"))
    for z in (1.6, 1.81):
        pts = [LK.on_front(HELM, x, z, 0.012) for x in np.linspace(-0.085, 0.085, 9)]
        V, F = M.tube(pts, [(0.008, 0.008)] * 9, n=6, up=(0, 0, 1))
        add(P_(V, F, "BH_ForsakenIron", "cage_rim"))
    # ram horns curling forward from the sides, and a crown of iron spikes
    for sx in (1, -1):
        add(LK.horn((sx * 0.1, 0.02, 1.8), (sx * 0.8, 0.5, 0.35), 0.34, 0.032, (0, 0, 1), sx * -150, n=14, mat="BH_Bone"))
    for i in range(10):
        a = 2 * math.pi * i / 10
        base = np.array((0.08 * math.sin(a), -0.09 * math.cos(a), 1.9))
        add(LK.spike(base, (math.sin(a) * 0.25, -math.cos(a) * 0.25, 1.0), 0.07 + 0.03 * (i % 2 == 0), 0.012, "BH_DarkSteel", n=5))
