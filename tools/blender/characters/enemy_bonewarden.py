"""Bonewarden (undead elite, builder A): a heavier, broad skeleton in rusted half-plate (breastplate, big layered
pauldrons, faulds, iron boots, gauntlets) with the lumbar spine bare between breastplate and belt. Its tower shield is
the lid of its own coffin (wood planks, iron bands, a bronze nameplate) on the left arm; a heavy bearded axe in the
right. Bascinet whose visor is broken off on the right side (the skull's grave-light shows through), chains hanging
from the belt, a tattered drab tabard."""
import math
import numpy as np

import bh_mesh as M
from bh_body import Body, torso_loft, front_y, back_y, dome, fist, M_align_z
from bh_math import Rx, Ry, Rz
from bh_skeleton import proportions
from char_knight import thick_band, arc_band
import enemy_hollow_soldier as HS
from enemy_hollow_soldier import P, rtube, ball, Scaled, add_weapon, dent, cloth_panel, cloth_w, ragged

K = 1.9 / 1.8
PROPS = proportions(K)
PALETTE = "bonewarden"
PALETTE_COLORS = {
    "BH_Bone": ((0.47, 0.43, 0.33), 0.0, 0.62, None, 0.0, 1.0),
    "BH_Rust": ((0.22, 0.11, 0.055), 0.45, 0.78, None, 0.0, 1.0),
    "BH_DarkSteel": ((0.12, 0.16, 0.14), 0.85, 0.55, None, 0.0, 1.0),       # verdigris iron
    "BH_Wood": ((0.10, 0.065, 0.04), 0.0, 0.8, None, 0.0, 1.0),             # grey-brown coffin wood
    "BH_Bronze": ((0.22, 0.30, 0.22), 0.8, 0.5, None, 0.0, 1.0),            # verdigris bronze nameplate
    "BH_Cloth_Primary": ((0.11, 0.095, 0.065), 0.0, 0.92, None, 0.0, 1.0),
    "BH_Leather": ((0.06, 0.04, 0.025), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Shadow": ((0.03, 0.035, 0.04), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((0.3, 0.9, 0.8), 0.0, 0.4, (0.3, 1.0, 0.85), 7.0, 1.0),
}
CLIPS = ["shield_bash", "axe_1"]


def finish_mesh(mesh_ob):
    HS.enable_weapon_deform(mesh_ob)


ENV = [  # standard-space envelope of the half-plate
    (0.86, 0.175, 0.12, 0.12, 0.0),
    (0.96, 0.17, 0.115, 0.115, 0.0),
    (1.05, 0.155, 0.105, 0.105, 0.0),
    (1.16, 0.15, 0.115, 0.10, 0.03),
    (1.24, 0.168, 0.135, 0.108, 0.10),
    (1.34, 0.185, 0.145, 0.115, 0.10),
    (1.43, 0.18, 0.13, 0.112, 0.05),
    (1.49, 0.145, 0.10, 0.098, 0.0),
    (1.53, 0.09, 0.07, 0.07, 0.0),
]


def rows_between(rows, z0, z1, n_extra=2, g=0.0):
    from bh_body import interp_rows
    zs = sorted(set([z0, z1] + [r[0] for r in rows if z0 < r[0] < z1] + list(np.linspace(z0, z1, n_extra + 2)[1:-1])))
    out = []
    for z in zs:
        r = interp_rows(rows, z)
        out.append((z, r[1] + g, r[2] + g, r[3] + g, r[4]))
    return out


# --------------------------------------------------------------------------------------------------- weapons
def coffin_lid():
    """Tower shield = coffin lid. Weapon-GLB space: handle at origin, face -Y, long axis Z."""
    parts = []
    o = np.array([(0.0, 0.58), (-0.2, 0.56), (-0.29, 0.32), (-0.17, -0.64), (0.17, -0.64), (0.29, 0.32), (0.2, 0.56)])
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    y_face = -0.075
    V, F = M.prism(o, 0.045, axis="y", center=y_face + 0.0225)
    parts.append(M.bevel(P(V, F, "BH_Wood", "lid"), 0.006, 1, angle=40))

    def half_w(z):
        if z >= 0.32:
            return 0.29 - (z - 0.32) / 0.24 * 0.09
        return 0.17 + (z + 0.64) / 0.96 * 0.12
    # plank grooves
    for x in (-0.095, 0.095):
        V, F = M.box(0.008, 0.006, 1.1, center=(x, y_face - 0.001, -0.04))
        parts.append(P(V, F, "BH_Shadow", "groove"))
    # iron bands (wrap slightly around the edges)
    for z in (0.44, 0.05, -0.45):
        hw = half_w(z) + 0.008
        V, F = M.box(2 * hw, 0.058, 0.055, center=(0, y_face + 0.02, z))
        parts.append(M.bevel(P(V, F, "BH_DarkSteel", "band"), 0.004, 1))
        for x in (-hw + 0.03, hw - 0.03):
            parts.append(ball((x, y_face - 0.01, z), 0.012, "BH_DarkSteel", 6, 3, (1, 0.6, 1)))
    # nameplate
    V, F = M.box(0.17, 0.012, 0.075, center=(0, y_face - 0.006, 0.25))
    parts.append(M.bevel(P(V, F, "BH_Bronze", "nameplate"), 0.004, 1))
    for i, w in enumerate((0.12, 0.09)):
        V, F = M.box(w, 0.006, 0.008, center=(0, y_face - 0.013, 0.262 - 0.022 * i))
        parts.append(P(V, F, "BH_Shadow", "letters"))
    # iron oath-cross on the lower half
    V, F = M.box(0.03, 0.014, 0.34, center=(0, y_face - 0.006, -0.22))
    parts.append(M.bevel(P(V, F, "BH_DarkSteel", "cross"), 0.003, 1))
    V, F = M.box(0.2, 0.014, 0.03, center=(0, y_face - 0.006, -0.13))
    parts.append(M.bevel(P(V, F, "BH_DarkSteel", "cross2"), 0.003, 1))
    # handle straps behind
    V, F = M.tube([(-0.09, -0.03, 0.0), (-0.05, 0.02, 0.0), (0.05, 0.02, 0.0), (0.09, -0.03, 0.0)],
                  [(0.012, 0.035)] * 4, n=6, up=(0, 0, 1))
    parts.append(P(V, F, "BH_Leather", "handle"))
    V, F = M.box(0.3, 0.012, 0.05, center=(0, -0.045, 0.22))
    parts.append(P(V, F, "BH_Leather", "strap"))
    return parts


def heavy_axe():
    parts = []
    prof = [(0, -0.2), (0.024, -0.2), (0.026, -0.18), (0.02, -0.15), (0.019, 0.4), (0.02, 0.76), (0.016, 0.8), (0, 0.81)]
    V, F = M.lathe(prof, 8)
    parts.append(P(V, F, "BH_Wood", "haft"))
    V, F = M.lathe([(0, -0.12), (0.022, -0.12), (0.022, 0.1), (0, 0.1)], 8)
    parts.append(P(V, F, "BH_Leather", "grip"))
    out = [(0.02, 0.56), (0.1, 0.575), (0.2, 0.64), (0.3, 0.76), (0.32, 0.66), (0.325, 0.54), (0.31, 0.42),
           (0.27, 0.33), (0.23, 0.37), (0.16, 0.46), (0.08, 0.51), (0.02, 0.5)]
    o = np.array(out)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    V, F = M.prism(M.resample_closed(o, 36), 0.036, axis="y")
    head = P(V, F, "BH_Rust", "axehead")
    head.warp(lambda v: (v[0] - 0.012 * math.exp(-((v[2] - 0.6) / 0.02) ** 2) * (v[0] > 0.28),
                         v[1] * (1.0 - 0.8 * min(max((v[0] - 0.04) / 0.28, 0), 1)), v[2]))
    parts.append(M.bevel(head, 0.002, 1, angle=50))
    V, F = M.tube([(-0.01, 0, 0.57), (-0.1, 0, 0.56), (-0.15, 0, 0.53)], [(0.02, 0.026), (0.012, 0.014), (0.002, 0.002)],
                  n=6, up=(0, 0, 1))
    parts.append(P(V, F, "BH_DarkSteel", "spike"))
    V, F = M.lathe([(0, 0.48), (0.03, 0.48), (0.032, 0.51), (0.032, 0.64), (0.027, 0.66), (0.0, 0.67)], 8)
    parts.append(P(V, F, "BH_DarkSteel", "socket"))
    return parts


# --------------------------------------------------------------------------------------------------- helm
def broken_bascinet(body):
    parts = []
    hz = body.head("head")[2]
    prof = [(0.0, 0.255), (0.05, 0.248), (0.088, 0.222), (0.11, 0.175), (0.116, 0.115), (0.114, 0.05), (0.104, -0.005)]
    V, F = M.lathe(prof, 18, a0=-50, a1=230, cap=False)
    shell = P(V, F, "BH_DarkSteel", "helm").scale((1.0, 1.08, 1.0)).move((0, 0.012, hz))
    shell = M.solidify(shell, 0.007, offset=1)
    dent(shell, (-0.08, 0.05, hz + 0.2), (1, 0, -0.5), 0.014, 0.035)
    parts.append(shell)
    # rim along the face opening + bottom
    # visor: left half only (broken off at the right), with the eye slit
    ez = hz + 0.035 + 0.068
    for (za, zb) in ((ez + 0.012, hz + 0.19), (hz + 0.0, ez - 0.01)):
        def fn(u, v, za=za, zb=zb):
            z = za + (zb - za) * v
            a_end = -86 - 14 * ragged(v + (0.3 if za > ez else 0), 2.0, 1.0, 2)
            a = math.radians(-30 + (a_end + 30) * u)
            r = 0.108 + 0.014 * max(0.0, 1 - abs(math.degrees(a) + 90) / 50) - 0.01 * (1 - v) * (za < ez)
            return (r * math.cos(a), 0.012 + 1.08 * r * math.sin(a), z)
        V, F = M.grid(fn, 5, 4)
        vis = P(V, F, "BH_Rust", "visor")
        vis.flip()
        parts.append(M.solidify(vis, 0.007, offset=1))
    # a pivot rivet on the left
    parts.append(ball((0.12, -0.005, ez + 0.01), 0.013, "BH_DarkSteel", 6, 3))
    # ridge comb along the crown
    pts = [(0, 0.012 + 1.08 * 0.116 * math.sin(a), hz + 0.12 + 0.135 * math.cos(a)) for a in np.linspace(-1.1, 1.4, 8)]
    parts.append(rtube(pts, 0.009, "BH_Rust", n=5, up=(1, 0, 0)))
    return parts


def chain(p0, p1, sag, n=10, r=(0.012, 0.019), wire=0.0045):
    """Hanging chain of alternating links between two anchors (catenary-ish)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    out = []
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(p0 + (p1 - p0) * t - np.array([0, 0, sag * 4 * t * (1 - t)]))
    for i in range(n):
        a, b = pts[i], pts[i + 1]
        c = (a + b) / 2
        d = b - a
        ring = [(r[0] * math.cos(t), 0.0, r[1] * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 9)[:-1]]
        ring = np.array(ring + [ring[0]])
        V, F = M.tube(ring, [(wire, wire)] * len(ring), n=4, up=(0, 1, 0), cap0=False, cap1=False)
        link = P(V, F, "BH_DarkSteel", "link")
        ang = math.degrees(math.atan2(d[0], d[2]))
        link.rot(Rz(90 * (i % 2)))
        link.rot(Ry(ang))
        pitch = math.degrees(math.atan2(-d[1], math.hypot(d[0], d[2])))
        link.rot(Rx(pitch)).move(c)
        out.append(link)
    return out


# --------------------------------------------------------------------------------------------------- build
def build(real: Body):
    body = Scaled(real, K)
    add = body.add
    for prt in HS.skull(body):
        add(prt, "head")
    for prt in broken_bascinet(body):
        add(prt, "head")
    add(rtube([(0, 0.02, 1.47), (0, 0.01, 1.62)], 0.016, "BH_Bone", n=6), weights=HS.NECK_W)
    for z in np.arange(1.51, 1.6, 0.032):
        V, F = M.lathe([(0, -0.008), (0.025, -0.007), (0.027, 0.0), (0.025, 0.007), (0, 0.008)], 8)
        add(P(V, F, "BH_Bone", "cvert").move((0, 0.012, z)), "neck")
    # bare lumbar spine between the plates (the rest of the column is inside the armour)
    for prt, w in HS.spine_column(body, y=0.02, z0=1.0, z1=1.26, r=0.02):
        add(prt, weights=w)
    for prt in HS.ribcage(body, n_ribs=7):
        add(prt, "chest")
    for prt in HS.pelvis(body, s=1.1):
        add(prt, "hips")

    # ---- half plate: breastplate + backplate (rust), gorget
    V, F = torso_loft(rows_between(ENV, 1.2, 1.53, 3), n=24, cap1=True)
    brest = P(V, F, "BH_Rust", "breastplate")
    dent(brest, (0.08, -0.14, 1.33), (-0.2, 1, 0), 0.02, 0.04)
    dent(brest, (-0.1, -0.13, 1.25), (0.2, 1, 0.2), 0.012, 0.03)
    add(M.bevel(brest, 0.004, 1, angle=50), weights=lambda V: [{"chest": 1.0}] * len(V))
    V, F = thick_band(ENV, 1.195, 1.215, 0.01, -0.004, n=24)
    add(P(V, F, "BH_DarkSteel", "rim"), "chest")
    # central ridge
    pts = [(0, front_y(ENV, 0, z) - 0.006, z) for z in np.linspace(1.22, 1.46, 5)]
    add(rtube(pts, 0.012, "BH_DarkSteel", n=5, up=(0, -1, 0)), "chest")
    prof = [(0.17, 1.45), (0.14, 1.5), (0.1, 1.54), (0.09, 1.575), (0.078, 1.575), (0.092, 1.535), (0.13, 1.49),
            (0.16, 1.45), (0.17, 1.45)]
    V, F = M.lathe(prof, 18, cap=False)
    add(P(V, F, "BH_DarkSteel", "gorget").scale((1.0, 0.85, 1.0)), "chest")

    # ---- belt, faulds, tabard, chains
    V, F = thick_band(ENV, 1.0, 1.06, 0.03, 0.012, n=24)
    add(M.bevel(P(V, F, "BH_Leather", "belt"), 0.003, 1), "hips")
    by = front_y(ENV, 0, 1.03) - 0.032
    V, F = M.box(0.075, 0.016, 0.065, center=(0, by, 1.03))
    add(M.bevel(P(V, F, "BH_DarkSteel", "buckle"), 0.004, 1), "hips")
    for side_a in ((0.1, 0.4), (0.6, 0.9)):
        for i in range(2):
            z1 = 1.0 - 0.05 * i
            V, F = arc_band(ENV, z1 - 0.065, z1, 0.035 + 0.02 * i, side_a[0], side_a[1], n=10)
            lame = P(V, F, "BH_Rust", "fauld")
            lame.warp(lambda v, z1=z1: (v[0] * (1 + 0.3 * (z1 - v[2])), v[1] * (1 + 0.3 * (z1 - v[2])), v[2]))
            add(M.solidify(lame, 0.006, offset=1.0), weights=body.skirt_weights(1.0, 0.8, max_leg=0.35, center_w=0.05))
    add(cloth_panel(ENV, 1.0, 0.5, lambda z: 0.11 + 0.03 * (1.0 - z), front=True, nu=7, nv=8, seed=1.3, rag=0.1,
                    gap=0.03, belt_z=1.0), weights=cloth_w(belt_z=1.0))
    add(cloth_panel(ENV, 1.0, 0.48, lambda z: 0.13 + 0.03 * (1.0 - z), front=False, nu=7, nv=8, seed=4.1, rag=0.1,
                    gap=0.03, belt_z=1.0), weights=cloth_w(belt_z=1.0))
    cw = cloth_w(belt_z=1.0, leg=0.6)
    for p0, p1, sag, n in (((0.17, -0.07, 1.0), (0.18, 0.07, 1.0), 0.16, 10),
                           ((-0.17, -0.06, 1.0), (-0.16, 0.09, 1.0), 0.22, 12),
                           ((0.08, 0.13, 1.0), (-0.07, 0.13, 1.0), 0.12, 8)):
        for link in chain(p0, p1, sag, n):
            add(link, weights=cw)
    # a padlock on the right chain
    V, F = M.box(0.05, 0.03, 0.06, center=(-0.19, 0.0, 0.8))
    add(M.bevel(P(V, F, "BH_DarkSteel", "lock"), 0.006, 1), weights=cw)

    # ---- arms: bones, big pauldrons, vambraces, gauntlets
    for sx, s in ((1, "L"), (-1, "R")):
        sh = body.head("upper_arm." + s)
        add(ball(sh, 0.034, "BH_Bone", 8, 5), "upper_arm." + s)
        for prt, b in HS.bone_arm(body, s, r=1.25, hand=False):
            add(prt, b)
        for prt in fist(body, s, "BH_DarkSteel", "BH_Rust", gauntlet=True, scale=1.05):
            add(prt, "hand." + s)
        fa = "forearm." + s
        L = body.p["fore_len"]
        V, F = M.tube(body.lpt(fa, [(0, u * L, 0) for u in (0.4, 0.7, 1.0)]),
                      [(0.043, 0.045), (0.042, 0.044), (0.047, 0.049)], n=10, up=(0, 0, 1))
        add(M.bevel(P(V, F, "BH_DarkSteel", "vambrace"), 0.003, 1, angle=50), fa)
        for prt in HS.rust_pauldron(body, s, r=0.135, lames=2, flat=0.75):
            add(prt, "upper_arm." + s)
        # couter
        el = body.head(fa)
        V, F = dome(el + (0, 0.03, 0), (0, 1, 0.1), 0.045, a_max=75, n=10, rings=4)
        add(M.solidify(P(V, F, "BH_Rust", "couter"), 0.006, offset=-1),
            weights=lambda V, s=s: [{"upper_arm." + s: 0.5, "forearm." + s: 0.5}] * len(V))

    # ---- legs: bones, poleyns + greaves, iron boots
    for sx, s in ((1, "L"), (-1, "R")):
        for prt, b in HS.bone_leg(body, s, r=1.2):
            add(prt, b)
        sh = "shin." + s
        k = body.head(sh)
        V, F = dome(k + (0, -0.02, 0.0), (0, -1, 0.15), 0.06, a_max=65, n=12, rings=4, scale=(1.1, 1.2, 0.7))
        add(M.solidify(P(V, F, "BH_Rust", "poleyn"), 0.007, offset=-1),
            weights=lambda V, s=s: [{"thigh." + s: 0.5, "shin." + s: 0.5}] * len(V))
        a = body.tail(sh)
        V, F = M.tube([a + (k - a) * u + np.array([0, -0.01, 0]) for u in (0.35, 0.65, 0.9)],
                      [(0.05, 0.056), (0.054, 0.06), (0.048, 0.052)], n=10, up=(0, -1, 0), cap0=False)
        add(M.solidify(P(V, F, "BH_Rust", "greave"), 0.006, offset=-1), sh)
        for prt, b in HS.boot(body, s, mat="BH_DarkSteel", top=0.2, r=1.1):
            add(prt, b)

    # ---- weapons
    add_weapon(body, "L", coffin_lid())
    add_weapon(body, "R", heavy_axe())
