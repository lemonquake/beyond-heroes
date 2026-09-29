"""Roydo, the Righteous Hammer (bh-021, contracts/story.md): Class SX, Lv 264. A mighty holy hero.

Broad-shouldered, white-gold engraved plate; a gold sunburst on the breastplate around a burning core; feathered
wing pauldrons; an ivory tabard and full cape edged in gold; a rounded great helm with gold wings and a sun crest,
a narrow Y-visor glowing faintly, a thick auburn beard spilling out beneath it in two gold-ringed braids; a halo of
light behind the head. His hammer (Dawnmaul) is a separate weapon GLB. The game scales him to ~2.1 m.
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

PROPS = proportions(1.0, shoulder_x=0.215, hip_x=0.108)
PALETTE = "roydo"
EXTRA_BONES = CAPE_BONES
CLIPS_ONLY = ["idle", "idle_2h", "walk", "run", "gs_1", "gs_2", "gs_heavy", "hit_heavy", "death",
              "cs_ro_land", "cs_ro_shoulder", "cs_ro_slam", "cs_ro_stand", "cs_ro_brace", "cs_ro_fall"]
PREVIEW_HEIGHT = 2.1

PALETTE_COLORS = {
    "BH_HolyPlate": LK.mat((0.82, 0.8, 0.74), 1.0, 0.3),
    "BH_Gold": LK.mat((0.95, 0.66, 0.24), 1.0, 0.28),
    "BH_Cloth_Primary": LK.mat((0.68, 0.64, 0.54), 0.0, 0.9),
    "BH_Cloth_Secondary": LK.mat((0.06, 0.09, 0.24), 0.0, 0.9),
    "BH_Mail": LK.mat((0.55, 0.55, 0.56), 1.0, 0.42),
    "BH_Leather": LK.mat((0.3, 0.18, 0.09), 0.0, 0.6),
    "BH_Hair": LK.mat((0.13, 0.05, 0.02), 0.0, 0.7),
    "BH_Emissive": LK.mat((1.0, 0.8, 0.4), 0.0, 0.3, (1.0, 0.7, 0.25), 4.0),
    "BH_Shadow": LK.mat((0.012, 0.01, 0.008), 0.0, 0.95),
}

TORSO = [
    (0.96, 0.178, 0.124, 0.128, 0.0),
    (1.02, 0.172, 0.126, 0.12, 0.02),
    (1.10, 0.172, 0.13, 0.118, 0.04),
    (1.20, 0.186, 0.142, 0.124, 0.08),
    (1.30, 0.205, 0.156, 0.13, 0.1),
    (1.38, 0.216, 0.158, 0.134, 0.08),
    (1.45, 0.21, 0.146, 0.132, 0.05),
    (1.50, 0.176, 0.118, 0.114, 0.02),
    (1.545, 0.108, 0.086, 0.084, 0.0),
]
HIP_ROWS = [(0.56, 0.21, 0.15, 0.16, 0.0), (0.8, 0.196, 0.14, 0.148, 0.0), (1.0, 0.182, 0.13, 0.132, 0.0),
            (1.07, 0.176, 0.126, 0.122, 0.0)]

secondary = _knight_secondary


def finish_mesh(ob):
    LK.finish_mesh(ob)


def build(body):
    k = Kit(body)
    torso(k, body)
    for s in "L":
        arm(k, body, s)
        leg(k, body, s)
    skirt(k, body)
    cape(k, body)
    helm(k, body)


# ------------------------------------------------------------------------------------------------------------ torso
def torso(k, body):
    add = body.add
    cw = chest_spine_w(1.24, 1.30)
    V, F = torso_loft([interp_rows(TORSO, z) for z in (1.2, 1.26, 1.3, 1.34, 1.38, 1.42, 1.45, 1.48, 1.5, 1.525, 1.545)],
                      n=32, cap1=True)
    add(M.bevel(P_(V, F, "BH_HolyPlate", "breastplate"), 0.004, 1, angle=50), weights=cw)
    V, F = thick_band(TORSO, 1.195, 1.215, 0.012, 0.0, n=32)
    add(P_(V, F, "BH_Gold", "rim"), weights=cw)
    for i, (z0, z1) in enumerate(((1.14, 1.2), (1.08, 1.145), (1.025, 1.085))):
        V, F = thick_band(TORSO, z0, z1, 0.01 + 0.004 * i, 0.0, n=30)
        add(M.bevel(P_(V, F, "BH_HolyPlate", "lame"), 0.003, 1), weights=k.torso_w())
        V, F = thick_band(TORSO, z0 - 0.003, z0 + 0.008, 0.016 + 0.004 * i, 0.006, n=30)
        add(P_(V, F, "BH_Gold", "lame_rim"), weights=k.torso_w())
    # the sunburst: a gold disc over the heart with long and short rays lying on the plate, a burning core
    zc = 1.36
    yc = front_y(TORSO, 0, zc) - 0.006
    V, F = M.lathe([(0.0, 0.0), (0.06, 0.0), (0.064, 0.008), (0.05, 0.016), (0.0, 0.02)], 24)
    disc = outward(P_(V, F, "BH_Gold", "sun")).rot(R_axis((1, 0, 0), 90)).move((0, yc, zc))
    add(disc, weights=cw)
    add(LK.gem((0, yc - 0.02, zc), 0.028, scale=(1, 0.5, 1), name="sun_core"), weights=cw)
    for i in range(16):
        a = i * math.pi / 8
        L = 0.13 if i % 2 == 0 else 0.075
        pts = []
        for t in np.linspace(0, 1, 5):
            r = 0.06 + L * t
            x, z = r * math.sin(a), zc + r * math.cos(a) * 0.95
            pts.append(LK.on_front(TORSO, x, z, 0.004))
        prof = [(0.012 * (1 - t) + 0.002, 0.004) for t in np.linspace(0, 1, 5)]
        V, F = M.tube(pts, prof, n=6, up=(0, -1, 0))
        add(outward(P_(V, F, "BH_Gold", "ray")), weights=cw)
    # gorget
    prof = [(0.18, 1.45), (0.16, 1.49), (0.12, 1.53), (0.1, 1.57), (0.106, 1.6), (0.094, 1.6), (0.084, 1.57),
            (0.1, 1.53), (0.15, 1.49), (0.172, 1.45), (0.18, 1.45)]
    V, F = M.lathe(prof, 28, cap=False)
    add(P_(V, F, "BH_HolyPlate", "gorget").scale((1.0, 0.86, 1.0)), "chest")
    V, F = M.lathe([(0.108, 1.594), (0.112, 1.603), (0.1, 1.608), (0.094, 1.6)], 28, cap=False)
    add(P_(V, F, "BH_Gold", "gorget_rim").scale((1.0, 0.86, 1.0)), "chest")
    # tabard panels with gold borders
    for front in (True, False):
        add(tabard(front), weights=tabard_w())
        for sx in (1, -1):
            pts = []
            for z in np.linspace(1.2, 0.52, 9):
                x = sx * (0.13 + 0.05 * max(0.0, (1.06 - z) / 0.5))
                zz = min(max(z, 1.06), 1.2)
                y0 = (front_y(TORSO, x, zz) - 0.022) if front else (back_y(TORSO, x, zz) + 0.022)
                d = max(0.0, 1.06 - z)
                y = y0 - 0.035 * d if front else y0 + 0.05 * d
                pts.append((x, y, z))
            add(LK.edge_tube(pts, 0.006, "BH_Gold", name="tabard_trim"), weights=tabard_w())
    # a gold sun embroidered low on the tabard front
    zc2 = 0.82
    y2 = front_y(TORSO, 0, 1.06) - 0.03 - 0.035 * (1.06 - zc2)
    V, F = M.lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.004), (0.0, 0.006)], 20)
    add(outward(P_(V, F, "BH_Gold", "emb")).rot(R_axis((1, 0, 0), 90)).move((0, y2, zc2)), weights=tabard_w())
    # belt
    V, F = thick_band(TORSO, 0.99, 1.035, 0.032, 0.012, n=30)
    add(M.bevel(P_(V, F, "BH_Leather", "belt"), 0.003, 1), "hips")
    by = front_y(TORSO, 0, 1.012) - 0.036
    V, F = M.box(0.085, 0.02, 0.06, center=(0, by, 1.012))
    add(M.bevel(P_(V, F, "BH_Gold", "buckle"), 0.008, 2), "hips")
    add(LK.gem((0, by - 0.012, 1.012), 0.012, scale=(1, 0.5, 1), name="buckle_gem"), "hips")


def tabard(front=True):
    nu, nv = 9, 16
    z_top = 1.2

    def fn(u, v):
        x_half = 0.13 + 0.05 * max(0.0, (1.06 - (z_top - v * (z_top - 0.52))) / 0.5)
        x = (u - 0.5) * 2 * x_half
        z = z_top + (0.52 + 0.04 * abs(u - 0.5) * 2 - z_top) * v
        if z >= 1.06:
            y = front_y(TORSO, x, z) - 0.02 if front else back_y(TORSO, x, z) + 0.02
        else:
            y0 = front_y(TORSO, x, 1.06) - 0.02 if front else back_y(TORSO, x, 1.06) + 0.02
            d = (1.06 - z)
            y = y0 - 0.035 * d if front else y0 + 0.05 * d
            y += 0.006 * math.sin(u * math.pi * 4) * d
        return (x, y, z)
    V, F = M.grid(fn, nu, nv)
    p = P_(V, F, "BH_Cloth_Primary", "tabard")
    if not front:
        p.flip()
    return M.solidify(p, 0.01, offset=1.0, bevel_w=0.002)


def tabard_w():
    from char_knight import tabard_w as tw
    return tw()


# ------------------------------------------------------------------------------------------------------------ arms
def arm(k, body, s):
    am = lambda part, bone=None, weights=None: body.add_mirror(part, bone, weights)
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    am(body.limb(ua, [(-0.05, 0.066, 0.066), (0.5, 0.062, 0.064), (1.0, 0.054, 0.056)], "BH_Mail", n=12), ua)
    rb = body.limb(ua, [(0.36, 0.07, 0.072), (0.4, 0.068, 0.07), (0.95, 0.06, 0.062)], "BH_HolyPlate", n=14, p=2.3)
    am(M.bevel(rb, 0.003, 1, angle=50), ua)
    el = body.head(fa)
    V, F = dome(el + (0.0, 0.034, 0.0), (0, 1, 0.1), 0.06, a_max=80, n=14, rings=5)
    am(M.solidify(P_(V, F, "BH_HolyPlate", "couter"), 0.006, offset=-1, bevel_w=0.002),
       weights=lambda V, ua=ua, fa=fa: [{ua: 0.5, fa: 0.5}] * len(V))
    V, F = fan_plate(el + (0.058, 0.014, 0.0), (1, 0, 0), (0, 0, 1), 0.058, 20, 200, n=8, thick=0.006)
    am(M.bevel(P_(V, F, "BH_Gold", "couterfan"), 0.002, 1), weights=lambda V, ua=ua, fa=fa: [{ua: 0.5, fa: 0.5}] * len(V))
    vb = body.limb(fa, [(0.08, 0.058, 0.06), (0.5, 0.054, 0.056), (0.9, 0.048, 0.05), (1.02, 0.06, 0.06)],
                   "BH_HolyPlate", n=14, p=2.3)
    am(M.bevel(vb, 0.003, 1, angle=50), fa)
    wr = body.head(ha)
    V, F = M.tube([el + (wr - el) * 0.9, el + (wr - el) * 1.0], [(0.066, 0.066), (0.068, 0.068)], n=14, up=(0, -1, 0))
    am(P_(V, F, "BH_Gold", "cuff_rim"), fa)
    for prt in fist(body, s, "BH_HolyPlate", "BH_Mail", scale=1.1):
        am(prt, ha)
    for prt in pauldron(body, s):
        am(prt, ua)


def pauldron(body, s):
    parts = []
    sh = body.head("upper_arm." + s)
    el = body.head("forearm." + s)
    armdir = normalize(el - sh)
    out = np.array([1.0, 0, 0])
    axis = normalize(out * 0.75 + np.array([0, 0.0, 1.0]) * 0.8)
    c = sh + np.array([0.012, 0.0, 0.014])
    R0 = 0.16
    V, F = dome(c, axis, R0, a_max=80, n=24, rings=7, scale=(1.0, 1.12, 1.0))
    parts.append(M.solidify(P_(V, F, "BH_HolyPlate", "pauldron"), 0.011, offset=-1, bevel_w=0.003))
    Rm = M_align_z(axis, (0, 0, 1))
    for frac, rr, mat_ in ((80, 0.011, "BH_Gold"), (52, 0.006, "BH_Gold")):
        rim = []
        for i in range(33):
            a = 2 * math.pi * i / 32
            r = R0 * math.sin(math.radians(frac))
            z = R0 * math.cos(math.radians(frac))
            rim.append(c + Rm @ np.array([r * math.cos(a), r * math.sin(a) * 1.12, z]))
        V, F = M.tube(rim, [(rr, rr)] * len(rim), n=6, up=axis, cap0=False, cap1=False)
        parts.append(P_(V, F, mat_, "rim"))
    # sunburst rays round the outer face of the dome
    for i in range(9):
        a = math.radians(-100 + 200 * i / 8)
        d = Rm @ np.array([math.cos(a), math.sin(a) * 1.12, 0.35])
        base = c + Rm @ np.array([R0 * 0.95 * math.cos(a), R0 * 0.95 * math.sin(a) * 1.12, R0 * 0.25])
        parts.append(LK.spike(base, d, 0.05 if i % 2 == 0 else 0.03, 0.012, "BH_Gold"))
    # feathered wings rising behind the pauldron
    top = c + axis * R0 * 0.8
    for i, (L, w, dy) in enumerate(((0.36, 0.055, 0.06), (0.3, 0.05, 0.085), (0.24, 0.045, 0.11), (0.18, 0.04, 0.13))):
        base = top + np.array([-0.02 - 0.008 * i, dy, -0.03 * i])
        parts.append(LK.fin(base, (0.32 + 0.08 * i, 0.3, 1.0), L, w, 0.007, (1, 0, 0), -55 - 8 * i, n=10,
                            mat="BH_HolyPlate", up=(1, 0, 0)))
        edge = LK.curve_pts(base + np.array([0.004, -w * 0.25, 0.0]), (0.32 + 0.08 * i, 0.3, 1.0), L * 0.9, (1, 0, 0),
                            -55 - 8 * i, 8)
        parts.append(LK.edge_tube(edge, 0.004, "BH_Gold", name="feather_edge"))
    ax_side = normalize(out - armdir * np.dot(out, armdir))
    ax_fwd = np.cross(armdir, ax_side)
    for i in range(3):
        t0 = 0.075 + 0.066 * i
        rr = 0.112 - 0.01 * i
        ctr = sh + armdir * (t0 + 0.04)
        loops = []
        for z_off in (0.0, 0.068):
            loop = []
            for kk in range(15):
                a = math.radians(-120 + 240 * kk / 14)
                pdir = ax_side * math.cos(a) + ax_fwd * math.sin(a) * 1.1
                loop.append(ctr + armdir * (z_off - 0.034) + pdir * (rr + 0.012 * (z_off > 0)))
            loops.append(np.array(loop))
        V, F = M.loft(loops, cap0=False, cap1=False, closed=False)
        parts.append(M.solidify(P_(V, F, "BH_HolyPlate", "lame"), 0.006, offset=1, bevel_w=0.002))
        V, F = M.tube(list(loops[1]), [(0.0042, 0.0042)] * 15, n=5, up=tuple(armdir))
        parts.append(P_(V, F, "BH_Gold", "lame_edge"))
    return parts


# ------------------------------------------------------------------------------------------------------------ legs
def leg(k, body, s):
    am = lambda part, bone=None, weights=None: body.add_mirror(part, bone, weights)
    th, sh = "thigh." + s, "shin." + s
    am(body.limb(th, [(-0.02, 0.088, 0.092), (0.4, 0.08, 0.084), (0.95, 0.06, 0.062)], "BH_Mail", n=12), th)
    cu = body.limb(th, [(0.15, 0.096, 0.1), (0.2, 0.094, 0.098), (0.55, 0.086, 0.09), (0.93, 0.07, 0.074)],
                   "BH_HolyPlate", n=16, p=2.4, offs=[(0, 0.004)] * 4)
    am(M.bevel(cu, 0.003, 1, angle=50), th)
    knee = body.head(sh)
    V, F = dome(knee + (0, -0.052, 0.0), (0, -1, 0.15), 0.07, a_max=78, n=14, rings=5)
    am(M.solidify(P_(V, F, "BH_HolyPlate", "poleyn"), 0.007, offset=-1, bevel_w=0.002),
       weights=lambda V, th=th, sh=sh: [{th: 0.5, sh: 0.5}] * len(V))
    V, F = fan_plate(knee + (0.064, -0.012, 0.0), (1, 0, 0), (0, 0, 1), 0.06, 100, 260, n=8, thick=0.006)
    am(M.bevel(P_(V, F, "BH_Gold", "kneefan"), 0.002, 1), weights=lambda V, th=th, sh=sh: [{th: 0.5, sh: 0.5}] * len(V))
    gr = body.limb(sh, [(0.03, 0.066, 0.068), (0.3, 0.072, 0.078), (0.55, 0.064, 0.068), (0.85, 0.054, 0.056),
                        (1.0, 0.058, 0.061)], "BH_HolyPlate", n=16, p=2.3,
                   offs=[(0, 0.0), (0, -0.012), (0, -0.006), (0, 0.0), (0, 0.0)])
    am(M.bevel(gr, 0.003, 1, angle=50), sh)
    kx, ky, kz = knee
    ridge = [(kx, -0.084, kz - 0.08), (kx, -0.088, kz - 0.17), (kx, -0.076, kz - 0.27), (kx, -0.066, kz - 0.34)]
    am(LK.edge_tube(ridge, 0.006, "BH_Gold", name="greave_ridge"), sh)
    for prt, bone in sabaton(s):
        am(prt, bone)


def sabaton(s):
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
    foot = rings([(0.07, 0.042, 0.078), (0.05, 0.05, 0.104), (0.0, 0.056, 0.124), (-0.06, 0.057, 0.094), (-0.125, 0.056, 0.064)])
    V, F = M.loft(foot[::-1])
    out.append((M.bevel(P_(V, F, "BH_HolyPlate", "sabaton"), 0.003, 1, angle=45), "foot." + s))
    toe = rings([(-0.115, 0.056, 0.064), (-0.17, 0.052, 0.05), (-0.22, 0.04, 0.036), (-0.245, 0.018, 0.022)])
    V, F = M.loft(toe[::-1])
    out.append((M.bevel(P_(V, F, "BH_HolyPlate", "sabaton_toe"), 0.003, 1, angle=45), "toe." + s))
    for y in (-0.03, -0.085):
        r = rings([(y + 0.012, 0.058, 0.11 if y > -0.05 else 0.084), (y - 0.008, 0.059, 0.108 if y > -0.05 else 0.08)])
        V, F = M.loft(r[::-1])
        out.append((P_(V, F, "BH_Gold", "lame"), "foot." + s))
    V, F = M.box(0.115, 0.21, 0.016, center=(hx, -0.03, 0.008))
    out.append((M.bevel(P_(V, F, "BH_Leather", "sole"), 0.004, 1), "foot." + s))
    V, F = M.box(0.09, 0.1, 0.012, center=(hx, -0.18, 0.006))
    out.append((M.bevel(P_(V, F, "BH_Leather", "sole_t"), 0.004, 1), "toe." + s))
    return out


def skirt(k, body):
    V, F = torso_loft([(0.97, 0.172, 0.12, 0.118, 0.0), (0.86, 0.186, 0.126, 0.126, 0.0), (0.74, 0.196, 0.13, 0.13, 0.0)], n=30)
    body.add(P_(V, F, "BH_Mail", "mailskirt"), weights=body.skirt_weights(0.98, 0.76, max_leg=0.8))
    w_side = body.skirt_weights(1.0, 0.7, max_leg=0.6, center_w=0.05)
    for f0, f1 in ((0.13, 0.25), (0.25, 0.37), (0.63, 0.75), (0.75, 0.87)):
        for i in range(3):
            zt = 1.02 - 0.05 * i
            body.add(LK.hanging_plate(HIP_ROWS, f0, f1, zt, zt - 0.1, 0.035 + 0.016 * i, "BH_HolyPlate", point=0.9, n=7,
                                      nv=4, flare=0.04), weights=w_side)
            pts = [ring_pt(HIP_ROWS, f, zt - 0.1, 0.035 + 0.016 * i + 0.043) for f in np.linspace(f0 + 0.005, f1 - 0.005, 6)]
            body.add(LK.edge_tube(pts, 0.004, "BH_Gold", name="fauld_edge"), weights=w_side)


def ring_pt(rows, frac, z, g):
    from char_mage import ring_frac
    return ring_frac(rows, max(min(z, rows[-1][0]), rows[0][0]), g, [frac])[0]


def cape(k, body):
    body.add(LK.cape_panel(TORSO, -0.24, 0.24, 1.47, 0.22, 21, back_off=0.045, flare=0.2, nu=15, nv=16,
                           depth_curve=0.1, tear=0.0, solid=0.012), weights=LK.cape_weights())
    lift = 0.0
    pts = []
    for u in np.linspace(0, 1, 15):
        x = (-0.24 + 0.48 * u) * 1.2
        y = back_y(TORSO, x * 0.95 / 1.2, 1.02) + 0.045 + 0.1 + 0.016 * math.sin(u * math.pi * 5 + 21)
        pts.append((x, y + 0.006, 0.225))
    body.add(LK.edge_tube(pts, 0.012, "BH_Gold", name="cape_hem"), weights=LK.cape_weights())
    for sx in (1, -1):
        c = np.array((sx * 0.15, back_y(TORSO, sx * 0.15, 1.47) + 0.04, 1.48))
        V, F = M.lathe([(0.0, 0.0), (0.034, 0.0), (0.036, 0.012), (0.02, 0.02), (0.0, 0.022)], 16)
        body.add(outward(P_(V, F, "BH_Gold", "clasp")).rot(R_axis((1, 0, 0), -90)).move(c), "chest")


# ------------------------------------------------------------------------------------------------------------ head
HELM = [
    (1.56, 0.096, 0.104, 0.104, 0.0, 0.0),
    (1.6, 0.102, 0.114, 0.11, 0.04, -0.004),
    (1.66, 0.108, 0.124, 0.118, 0.06, -0.008),
    (1.72, 0.11, 0.126, 0.122, 0.05, -0.008),
    (1.78, 0.106, 0.118, 0.12, 0.02, -0.004),
    (1.83, 0.092, 0.1, 0.104, 0.0, 0.0),
    (1.865, 0.064, 0.068, 0.074, 0.0, 0.004),
    (1.884, 0.028, 0.03, 0.034, 0.0, 0.006),
]


def helm(k, body):
    add = lambda p: body.add(p, "head")
    V, F = torso_loft(HELM, n=30, p=2.6, cap1=True)
    add(M.bevel(P_(V, F, "BH_HolyPlate", "helm"), 0.003, 1, angle=55))
    # Y visor: an eye slit and a vertical breath slit, glowing faintly
    for sx in (1, -1):
        pts = [LK.on_front(HELM, sx * x, z, 0.002) for x, z in ((0.01, 1.708), (0.045, 1.712), (0.08, 1.722))]
        add(LK.edge_tube(pts, 0.0075, "BH_Emissive", name="visor"))
    pts = [LK.on_front(HELM, 0, z, 0.002) for z in (1.7, 1.66, 1.62)]
    add(LK.edge_tube(pts, 0.006, "BH_Emissive", name="breath"))
    # gold brow band, centre ridge and bottom rim
    band = []
    for z in (1.735, 1.755):
        r = interp_rows(HELM, z)
        from bh_body import torso_ring
        band.append(torso_ring(z, r[1] + 0.006, r[2] + 0.006, r[3] + 0.006, r[4], 2.6, 40, cy=r[5]))
    V, F = M.loft(band, cap0=False, cap1=False)
    add(M.solidify(P_(V, F, "BH_Gold", "brow"), 0.004, offset=1))
    ridge = [np.array((0, front_y([(r[0], r[1], r[2], r[3], r[4]) for r in HELM], 0, z) - 0.006 + interp_rows(HELM, z)[5], z))
             for z in np.linspace(1.6, 1.83, 6)] + [np.array((0, 0.0, 1.9)), np.array((0, 0.09, 1.86))]
    add(LK.edge_tube(ridge, 0.01, "BH_Gold", name="ridge"))
    V, F = thick_band(HELM, 1.553, 1.568, 0.007, -0.002, n=30, p=2.6)
    add(P_(V, F, "BH_Gold", "helm_rim"))
    # gold wings on the temples
    for sx in (1, -1):
        base = np.array((sx * 0.1, -0.01, 1.76))
        for i, (L, w) in enumerate(((0.22, 0.05), (0.18, 0.042), (0.13, 0.034))):
            add(LK.fin(base + np.array([0, 0.015 * i, -0.02 * i]), (sx * 0.4, 0.55, 0.75 - 0.15 * i), L, w, 0.006,
                       (1, 0, 0), -40 - 10 * i, n=8, mat="BH_Gold", up=(1, 0, 0)))
    # sun crest on the crown
    c = np.array((0, 0.02, 1.93))
    V, F = M.lathe([(0.0, 0.0), (0.045, 0.0), (0.048, 0.008), (0.03, 0.014), (0.0, 0.016)], 20)
    add(outward(P_(V, F, "BH_Gold", "crest")).rot(R_axis((1, 0, 0), 90)).move(c))
    add(LK.gem(c + np.array([0, -0.012, 0]), 0.018, scale=(1, 0.5, 1), name="crest_core"))
    for i in range(8):
        a = i * math.pi / 4
        d = np.array([math.sin(a), 0, math.cos(a)])
        add(LK.spike(c + d * 0.045, d, 0.05 if i % 2 == 0 else 0.03, 0.01, "BH_Gold"))
    V, F = M.tube([(0, 0.02, 1.88), (0, 0.02, 1.93)], [(0.012, 0.01)] * 2, n=8, up=(0, -1, 0))
    add(P_(V, F, "BH_Gold", "crest_stem"))
    # halo behind the head
    hc = np.array((0, 0.17, 1.77))
    ring = [hc + np.array([0.23 * math.cos(a), 0.0, 0.23 * math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 49)]
    V, F = M.tube(ring, [(0.006, 0.003)] * 49, n=6, up=(0, 1, 0), cap0=False, cap1=False)
    add(P_(V, F, "BH_Emissive", "halo"))
    for i in range(24):
        a = i * math.pi / 12
        d = np.array([math.cos(a), 0.0, math.sin(a)])
        add(LK.spike(hc + d * 0.235, d, 0.035 if i % 2 == 0 else 0.018, 0.005, "BH_Emissive"))
    # beard spilling from under the helm down the gorget, two braids with gold rings
    bw = lambda V: [({"head": 1.0} if v[2] > 1.6 else {"head": 0.4, "neck": 0.3, "chest": 0.3} if v[2] > 1.52 else {"chest": 1.0})
                    for v in V]
    # the beard: thick locks falling from under the helm's rim over the gorget
    rng = np.random.default_rng(264)
    for i in range(13):
        u = (i / 12) * 2 - 1
        x0 = u * 0.078
        z0 = 1.595 - 0.02 * abs(u)
        y0 = front_y(HELM, x0, 1.58) - 0.004
        L = 0.15 - 0.05 * abs(u) + rng.uniform(-0.015, 0.015)
        pts = [np.array((x0, y0, z0))]
        for t in np.linspace(0.25, 1, 4):
            pts.append(np.array((x0 * (1 - 0.3 * t) + rng.uniform(-0.004, 0.004), y0 - 0.035 * math.sin(t * 2.2) - 0.012 * t,
                                 z0 - L * t)))
        prof = [(0.02 * (1 - 0.7 * t) + 0.003, 0.016 * (1 - 0.6 * t) + 0.003) for t in np.linspace(0, 1, 5)]
        V, F = M.tube(pts, prof, n=7, up=(0, -1, 0))
        body.add(outward(P_(V, F, "BH_Hair", "beard_lock")), weights=bw)
    for sx in (1, -1):
        pts = [np.array((sx * 0.04, -0.165, 1.49)), np.array((sx * 0.045, -0.176, 1.46)), np.array((sx * 0.047, -0.18, 1.43)),
               np.array((sx * 0.045, -0.178, 1.405))]
        V, F = M.tube(pts, [(0.018, 0.016), (0.016, 0.014), (0.013, 0.012), (0.006, 0.006)], n=8, up=(0, -1, 0))
        body.add(outward(P_(V, F, "BH_Hair", "braid")), "chest")
        for z in (1.465, 1.43):
            V, F = M.tube([(sx * 0.046, -0.178, z + 0.008), (sx * 0.046, -0.178, z - 0.008)], [(0.018, 0.018)] * 2, n=10, up=(0, -1, 0))
            body.add(outward(P_(V, F, "BH_Gold", "braid_ring")), "chest")
