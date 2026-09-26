"""Knight hero: full plate over mail, great helm with visor slit and crest, layered pauldrons, gauntlets,
crimson tabard with the Order emblem, belt with pouches, short cape (cape.1/cape.2 bones)."""
import math
import numpy as np

import bh_mesh as M
import bh_weapons as WP
from bh_body import (Body, torso_ring, torso_loft, interp_rows, front_y, back_y, dome, fist, fan_plate,
                     smoothstep, M_align_z)
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions

PROPS = proportions()

CAPE_BONES = [
    ("cape.1", (0, 0.15, 1.46), (0, 0.185, 1.08), "chest", (0, -1, 0)),
    ("cape.2", (0, 0.185, 1.08), (0, 0.215, 0.68), "cape.1", (0, -1, 0)),
]

EXTRA_BONES = CAPE_BONES
PALETTE = "knight"

TORSO = [
    (0.98, 0.152, 0.104, 0.102, 0.00),
    (1.06, 0.143, 0.106, 0.098, 0.04),
    (1.16, 0.150, 0.120, 0.102, 0.12),
    (1.27, 0.168, 0.134, 0.108, 0.16),
    (1.37, 0.181, 0.138, 0.113, 0.13),
    (1.44, 0.176, 0.126, 0.111, 0.08),
    (1.49, 0.148, 0.100, 0.097, 0.03),
    (1.53, 0.095, 0.074, 0.072, 0.0),
]


def rows_between(rows, z0, z1, scale=1.0, extra=0.0, n_extra=0):
    zs = sorted(set([z0, z1] + [r[0] for r in rows if z0 < r[0] < z1] +
                    list(np.linspace(z0, z1, n_extra + 2)[1:-1])))
    out = []
    for z in zs:
        r = interp_rows(rows, z)
        out.append((z, r[1] * scale + extra, r[2] * scale + extra, r[3] * scale + extra, r[4]))
    return out


def thick_band(rows, z0, z1, grow_out, grow_in=0.0, n=24, p=2.3, angs=None):
    """Closed thick band following torso rows between z0 and z1."""
    def ring(z, g):
        r = interp_rows(rows, z)
        return torso_ring(z, r[1] + g, r[2] + g, r[3] + g, r[4], p, n)
    loops = [ring(z0, grow_in), ring(z0, grow_out), ring(z1, grow_out), ring(z1, grow_in)]
    nn = len(loops[0])
    V = np.vstack(loops)
    F = []
    for k in range(4):
        a, b = k * nn, ((k + 1) % 4) * nn
        for i in range(nn):
            j = (i + 1) % nn
            F.append((a + i, a + j, b + j, b + i))
    return V, F


def arc_band(rows, z0, z1, g_out, a0, a1, n=24, p=2.3, thick=0.006):
    """Open band (angles in ring-index fraction 0..1, 0 = front, 0.25 = character's left...)."""
    def ring(z, g):
        r = interp_rows(rows, z)
        full = torso_ring(z, r[1] + g, r[2] + g, r[3] + g, r[4], p, 96)
        idx = [int(round((a0 + (a1 - a0) * i / (n - 1)) * 96)) % 96 for i in range(n)]
        return full[idx]
    V, F = M.loft([ring(z0, g_out), ring(z1, g_out)], cap0=False, cap1=False, closed=False)
    return V, F


def build(body: Body):
    add = body.add
    parts_added = []

    # ---------------- torso plates ----------------
    V, F = torso_loft(rows_between(TORSO, 1.215, 1.53, n_extra=3), n=28, cap1=True)
    brest = M.Part(V, F, "BH_Steel", name="breastplate")
    add(M.bevel(brest, 0.004, 1, angle=50), weights=chest_spine_w(1.24, 1.30))
    V, F = torso_loft(rows_between(TORSO, 0.99, 1.30, scale=0.985, n_extra=2), n=28, cap0=True)
    add(M.Part(V, F, "BH_Steel", name="plackart"), weights=spine_hips_w(1.0, 1.04))
    # rolled rims
    V, F = thick_band(TORSO, 1.212, 1.232, 0.012, 0.0, n=28)
    add(M.Part(V, F, "BH_Gold", name="rim"), weights=chest_spine_w(1.24, 1.30))
    V, F = thick_band(TORSO, 1.505, 1.525, 0.006, -0.01, n=28)
    add(M.Part(V, F, "BH_Gold", name="rim2"), "chest")

    # gorget + neck mail
    prof = [(0.158, 1.45), (0.135, 1.49), (0.098, 1.527), (0.084, 1.565), (0.074, 1.565), (0.088, 1.527),
            (0.125, 1.49), (0.148, 1.45), (0.158, 1.45)]
    V, F = M.lathe(prof, 24, cap=False)
    g = M.Part(V, F, "BH_Steel", name="gorget").scale((1.0, 0.85, 1.0))
    add(g, "chest")
    V, F = M.lathe([(0.0, 1.46), (0.074, 1.47), (0.07, 1.56), (0.064, 1.62), (0.0, 1.62)], 12)
    add(M.Part(V, F, "BH_DarkSteel", name="coif").scale((1, 0.9, 1), center=(0, 0, 1.5)), "neck")

    # ---------------- tabard ----------------
    add(tabard_panel(front=True), weights=tabard_w())
    add(tabard_panel(front=False), weights=tabard_w())
    for p in WP.emblem_parts(0.5, depth=0.006):
        zc = 1.34
        p.move((0, 0, zc))
        p.warp(lambda v: (v[0], front_y(TORSO, v[0], v[2]) - 0.02 + (v[1]), v[2]))
        add(p, weights=chest_spine_w(1.24, 1.30))

    # ---------------- belt, faulds, mail skirt ----------------
    V, F = thick_band(TORSO, 1.025, 1.072, 0.03, 0.012, n=28)
    add(M.bevel(M.Part(V, F, "BH_Leather", name="belt"), 0.003, 1), "hips")
    by = front_y(TORSO, 0, 1.05) - 0.032
    V, F = M.box(0.062, 0.016, 0.054, center=(0, by, 1.049))
    add(M.bevel(M.Part(V, F, "BH_Gold", name="buckle"), 0.005, 2), "hips")
    V, F = M.box(0.034, 0.02, 0.028, center=(0, by - 0.004, 1.049))
    add(M.Part(V, F, "BH_DarkSteel", name="buckle_in"), "hips")
    for (x, ang, sz) in ((-0.155, 0.62, (0.07, 0.045, 0.085)), (0.12, 0.37, (0.06, 0.04, 0.075)),
                         (0.165, 0.2, (0.045, 0.04, 0.09))):
        r = interp_rows(TORSO, 1.03)
        a = 2 * math.pi * ang - math.pi / 2
        px = (r[1] + 0.045) * math.cos(a)
        py = (r[2] + 0.04) * math.sin(a) if math.sin(a) < 0 else (r[3] + 0.04) * math.sin(a)
        V, F = M.box(*sz, center=(0, 0, 0))
        pouch = M.bevel(M.Part(V, F, "BH_Leather", name="pouch"), 0.008, 2)
        pouch.rot(Rz(math.degrees(a) + 90)).move((px, py, 0.99))
        add(pouch, "hips")
        V, F = M.box(sz[0] * 1.05, sz[1] * 1.1, 0.025)
        flap = M.bevel(M.Part(V, F, "BH_Leather", name="flap"), 0.006, 1)
        flap.rot(Rz(math.degrees(a) + 90)).move((px, py, 0.99 + sz[2] / 2 - 0.004))
        add(flap, "hips")
        V, F = M.sphere(0.008, 6, 4)
        add(M.Part(V, F, "BH_Gold").move((px + 0.0, py, 0.99 + sz[2] / 2 - 0.01)).move(
            normalize(np.array([px, py, 0])) * sz[1] * 0.55), "hips")
    # faulds: side lames
    for side_a in ((0.12, 0.38), (0.62, 0.88)):
        for i in range(3):
            z1 = 1.025 - 0.045 * i
            z0 = z1 - 0.06
            V, F = arc_band(TORSO, z0, z1, 0.035 + 0.018 * i, side_a[0], side_a[1], n=12)
            lame = M.Part(V, F, "BH_Steel", name="fauld")
            # flare the lower edge outward
            lame.warp(lambda v, z1=z1: (v[0] * (1 + 0.25 * (z1 - v[2])), v[1] * (1 + 0.25 * (z1 - v[2])), v[2]))
            lame = M.solidify(lame, 0.006, offset=1.0, bevel_w=0.002)
            add(lame, weights=body.skirt_weights(1.0, 0.8, max_leg=0.35, center_w=0.05))
    V, F = torso_loft([(0.97, 0.162, 0.112, 0.108, 0.0), (0.88, 0.176, 0.118, 0.115, 0.0),
                       (0.8, 0.185, 0.12, 0.118, 0.0)], n=28)
    add(M.Part(V, F, "BH_DarkSteel", name="mailskirt"), weights=body.skirt_weights(0.98, 0.78, max_leg=0.8))

    # ---------------- legs ----------------
    for s in ("L",):
        th, sh = "thigh." + s, "shin." + s
        add_leg = lambda part, bone=None, weights=None: body.add_mirror(part, bone, weights)
        add_leg(body.limb(th, [(-0.02, 0.078, 0.082), (0.4, 0.07, 0.075), (0.95, 0.052, 0.055)], "BH_DarkSteel", n=12), th)
        cu = body.limb(th, [(0.2, 0.086, 0.09), (0.24, 0.083, 0.087), (0.55, 0.077, 0.082), (0.93, 0.062, 0.066)],
                       "BH_Steel", n=14, p=2.4, offs=[(0, 0.004)] * 4)
        add_leg(M.bevel(cu, 0.003, 1, angle=50), th)
        V, F = M.tube([body.lpt(th, [(0, 0.2 * 0.43, 0)])[0] + (0, 0, 0.012),
                       body.lpt(th, [(0, 0.2 * 0.43, 0)])[0] + (0, 0, -0.004)],
                      [(0.09, 0.094), (0.09, 0.094)], n=14, up=(0, -1, 0))
        add_leg(M.Part(V, F, "BH_Gold", name="cuisse_rim"), th)
        knee = body.head(sh)
        V, F = dome(knee + (0, -0.045, 0.0), (0, -1, 0.15), 0.06, a_max=78, n=14, rings=5)
        cop = M.solidify(M.Part(V, F, "BH_Steel", name="poleyn"), 0.007, offset=-1, bevel_w=0.002)
        add_leg(cop, weights=lambda V, th=th, sh=sh: [{th: 0.5, sh: 0.5}] * len(V))
        V, F = fan_plate(knee + (0.055, -0.01, 0.0), (1, 0, 0), (0, 0, 1), 0.055, 100, 260, n=8, thick=0.006)
        add_leg(M.bevel(M.Part(V, F, "BH_Steel", name="kneefan"), 0.002, 1),
                weights=lambda V, th=th, sh=sh: [{th: 0.5, sh: 0.5}] * len(V))
        gr = body.limb(sh, [(0.03, 0.058, 0.06), (0.3, 0.064, 0.068), (0.55, 0.056, 0.058), (0.85, 0.046, 0.048),
                            (1.0, 0.05, 0.053)], "BH_Steel", n=14, p=2.3,
                       offs=[(0, 0.0), (0, -0.012), (0, -0.006), (0, 0.0), (0, 0.0)])
        add_leg(M.bevel(gr, 0.003, 1, angle=50), sh)
        V, F = M.tube([body.lpt(sh, [(0, 0.97 * 0.43, 0)])[0] + (0, 0, 0.01),
                       body.lpt(sh, [(0, 0.97 * 0.43, 0)])[0] + (0, 0, -0.006)],
                      [(0.056, 0.059), (0.056, 0.059)], n=14, up=(0, -1, 0))
        add_leg(M.Part(V, F, "BH_Gold", name="greave_rim"), sh)
        for part, bone in sabaton(body, s):
            add_leg(part, bone)

    # ---------------- arms ----------------
    for s in ("L",):
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        am = lambda part, bone=None, weights=None: body.add_mirror(part, bone, weights)
        am(body.limb(ua, [(-0.05, 0.058, 0.058), (0.5, 0.054, 0.056), (1.0, 0.046, 0.048)], "BH_DarkSteel", n=12), ua)
        rb = body.limb(ua, [(0.4, 0.06, 0.062), (0.44, 0.058, 0.06), (0.95, 0.051, 0.053)], "BH_Steel", n=12, p=2.3)
        am(M.bevel(rb, 0.003, 1, angle=50), ua)
        el = body.head(fa)
        V, F = dome(el + (0.0, 0.03, 0.0), (0, 1, 0.1), 0.05, a_max=80, n=12, rings=5)
        am(M.solidify(M.Part(V, F, "BH_Steel", name="couter"), 0.006, offset=-1, bevel_w=0.002),
           weights=lambda V, ua=ua, fa=fa: [{ua: 0.5, fa: 0.5}] * len(V))
        V, F = fan_plate(el + (0.05, 0.012, 0.0), (1, 0, 0), (0, 0, 1), 0.05, 20, 200, n=8, thick=0.005)
        am(M.bevel(M.Part(V, F, "BH_Steel", name="couterfan"), 0.002, 1),
           weights=lambda V, ua=ua, fa=fa: [{ua: 0.5, fa: 0.5}] * len(V))
        vb = body.limb(fa, [(0.1, 0.048, 0.05), (0.5, 0.045, 0.047), (0.93, 0.038, 0.04)], "BH_Steel", n=12, p=2.3)
        am(M.bevel(vb, 0.003, 1, angle=50), fa)
        cuff = body.limb(fa, [(0.84, 0.042, 0.044), (1.0, 0.054, 0.054), (1.08, 0.058, 0.056)], "BH_Steel", n=12,
                         cap0=False, cap1=False)
        am(M.solidify(cuff, 0.005, offset=1.0), ha)
        V, F = M.tube([body.lpt(fa, [(0, 1.075 * 0.26, 0)])[0], body.lpt(fa, [(0, 1.1 * 0.26, 0)])[0]],
                      [(0.06, 0.058), (0.06, 0.058)], n=12, up=(0, -1, 0))
        am(M.Part(V, F, "BH_Gold", name="cuffrim"), ha)
        for prt in fist(body, s, "BH_Steel", "BH_DarkSteel"):
            am(prt, ha)
        for prt in pauldron(body, s):
            am(prt, ua)

    # ---------------- helm ----------------
    for prt in helm(body):
        add(prt, "head")

    # ---------------- cape ----------------
    add(cape(), weights=cape_w())


# ---------------------------------------------------------------------------------------------------
def chest_spine_w(z0, z1):
    def wfn(V):
        s = smoothstep(z0, z1, V[:, 2])
        return [({"chest": 1.0} if x >= 1 else {"spine": 1.0} if x <= 0 else {"chest": float(x), "spine": float(1 - x)})
                for x in s]
    return wfn


def spine_hips_w(z0, z1):
    def wfn(V):
        s = smoothstep(z0, z1, V[:, 2])
        return [({"spine": 1.0} if x >= 1 else {"hips": 1.0} if x <= 0 else {"spine": float(x), "hips": float(1 - x)})
                for x in s]
    return wfn


def tabard_w():
    def wfn(V):
        out = []
        for v in V:
            z = v[2]
            if z >= 1.30:
                out.append({"chest": 1.0})
            elif z >= 1.18:
                t = float(smoothstep(1.18, 1.30, z))
                out.append({"chest": t, "spine": 1 - t})
            elif z >= 1.03:
                t = float(smoothstep(1.03, 1.12, z))
                out.append({"spine": t, "hips": 1 - t} if t > 0 else {"hips": 1.0})
            else:
                s = float(smoothstep(1.0, 0.55, z)) * 0.75
                side = float(smoothstep(-0.07, 0.07, v[0]))
                d = {"hips": 1 - s}
                if s * side > 1e-3:
                    d["thigh.L"] = s * side
                if s * (1 - side) > 1e-3:
                    d["thigh.R"] = s * (1 - side)
                out.append(d)
        return out
    return wfn


def tabard_panel(front=True):
    nu, nv = 9, 16
    z_top = 1.465 if front else 1.46

    def fn(u, v):
        x_half = 0.118 + 0.03 * max(0.0, (1.06 - (z_top - v * 1.0)) / 0.5)
        x = (u - 0.5) * 2 * x_half
        bottom = 0.49 + 0.05 * abs(u - 0.5) * 2
        z = z_top + (bottom - z_top) * v
        if z >= 1.06:
            y = front_y(TORSO, x, z) - 0.014 if front else back_y(TORSO, x, z) + 0.014
        else:
            y0 = front_y(TORSO, x, 1.06) - 0.014 if front else back_y(TORSO, x, 1.06) + 0.014
            d = (1.06 - z)
            y = y0 - 0.035 * d if front else y0 + 0.05 * d
            y += (0.006 * math.sin(u * math.pi * 4)) * d  # soft folds
        return (x, y, z)
    V, F = M.grid(fn, nu, nv)
    p = M.Part(V, F, "BH_Cloth_Primary", name="tabard")
    if not front:
        p.flip()
    p = M.solidify(p, 0.01, offset=1.0 if front else 1.0, bevel_w=0.002)
    return p


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
    foot = rings([(0.07, 0.036, 0.07), (0.05, 0.044, 0.095), (0.0, 0.049, 0.115), (-0.06, 0.05, 0.085),
                  (-0.125, 0.05, 0.055)])
    V, F = M.loft(foot[::-1])
    out.append((M.bevel(M.Part(V, F, "BH_Steel", name="sabaton"), 0.003, 1, angle=45), "foot." + s))
    toe = rings([(-0.115, 0.05, 0.055), (-0.17, 0.047, 0.045), (-0.215, 0.036, 0.034), (-0.24, 0.016, 0.02)])
    V, F = M.loft(toe[::-1])
    out.append((M.bevel(M.Part(V, F, "BH_Steel", name="sabaton_toe"), 0.003, 1, angle=45), "toe." + s))
    for y in (-0.03, -0.085):
        r = rings([(y + 0.012, 0.051, 0.1 if y > -0.05 else 0.078), (y - 0.008, 0.052, 0.098 if y > -0.05 else 0.074)])
        V, F = M.loft(r[::-1])
        out.append((M.Part(V, F, "BH_Steel", name="lame"), "foot." + s))
    V, F = M.box(0.1, 0.2, 0.014, center=(hx, -0.03, 0.007))
    out.append((M.bevel(M.Part(V, F, "BH_Leather", name="sole"), 0.004, 1), "foot." + s))
    V, F = M.box(0.08, 0.1, 0.012, center=(hx, -0.18, 0.006))
    out.append((M.bevel(M.Part(V, F, "BH_Leather", name="sole_t"), 0.004, 1), "toe." + s))
    return out


def pauldron(body, s):
    parts = []
    sh = body.head("upper_arm." + s)            # shoulder joint (model space)
    el = body.head("forearm." + s)
    armdir = normalize(el - sh)
    out = np.array([1.0, 0, 0])
    axis = normalize(out * 0.75 + np.array([0, 0, 1.0]) * 0.75)
    c = sh + np.array([0.005, 0.0, 0.0])
    V, F = dome(c, axis, 0.128, a_max=74, n=18, rings=6, scale=(1.0, 1.12, 1.0), up_hint=(0, 0, 1))
    d = M.solidify(M.Part(V, F, "BH_Steel", name="pauldron"), 0.008, offset=-1, bevel_w=0.003)
    parts.append(d)
    # ridge on the dome
    rp = [c + R_axis((0, 1, 0), -a) @ (np.array([0, 0, 1.0]) * 0.13) for a in np.linspace(-20, 55, 7)]
    V, F = M.tube(rp, [(0.012, 0.01)] * len(rp), n=6, up=(0, 1, 0))
    parts.append(M.Part(V, F, "BH_Gold", name="ridge"))
    # rim trim along dome edge
    rim = []
    Rm = M_align_z(axis, (0, 0, 1))
    for i in range(25):
        a = 2 * math.pi * i / 24
        r = 0.128 * math.sin(math.radians(74))
        z = 0.128 * math.cos(math.radians(74))
        rim.append(c + Rm @ (np.array([r * math.cos(a), r * math.sin(a) * 1.12, z]) * 1.0))
    V, F = M.tube(rim, [(0.008, 0.008)] * len(rim), n=6, up=axis, cap0=False, cap1=False)
    parts.append(M.Part(V, F, "BH_Gold", name="pauldron_rim"))
    # lames down the arm (outer side)
    for i in range(3):
        t0 = 0.06 + 0.06 * i
        rr = 0.098 - 0.009 * i
        ctr = sh + armdir * (t0 + 0.04)
        ring_pts = []
        ax_side = normalize(out - armdir * np.dot(out, armdir))
        ax_fwd = np.cross(armdir, ax_side)
        for z_off in (0.0, 0.062):
            loop = []
            for k in range(13):
                a = math.radians(-115 + 230 * k / 12)
                pdir = ax_side * math.cos(a) + ax_fwd * math.sin(a) * 1.1
                loop.append(ctr + armdir * (z_off - 0.031) + pdir * (rr + 0.012 * (z_off > 0)))
            ring_pts.append(np.array(loop))
        V, F = M.loft(ring_pts, cap0=False, cap1=False, closed=False)
        lame = M.solidify(M.Part(V, F, "BH_Steel", name="lame"), 0.006, offset=1, bevel_w=0.002)
        parts.append(lame)
    return parts


def helm(body):
    parts = []
    H = [(1.552, 0.106, 0.117, 0.117, 0.10), (1.585, 0.112, 0.124, 0.122, 0.12), (1.64, 0.116, 0.129, 0.125, 0.12),
         (1.697, 0.117, 0.13, 0.126, 0.08), (1.715, 0.117, 0.13, 0.126, 0.06), (1.77, 0.115, 0.126, 0.124, 0.03),
         (1.815, 0.108, 0.117, 0.117, 0.0), (1.838, 0.088, 0.094, 0.094, 0.0), (1.848, 0.05, 0.052, 0.052, 0.0)]
    cy = 0.008
    Hc = [h + (cy,) for h in H]
    lower = [h for h in Hc if h[0] <= 1.698]
    upper = [h for h in Hc if h[0] >= 1.714]
    V, F = torso_loft(lower, n=28, p=2.6, cap0=False)
    parts.append(M.bevel(M.Part(V, F, "BH_Steel", name="helm_low"), 0.003, 1, angle=55))
    V, F = torso_loft(upper, n=28, p=2.6, cap1=True)
    parts.append(M.bevel(M.Part(V, F, "BH_Steel", name="helm_up"), 0.003, 1, angle=55))
    # visor slit liner (dark) and back filler
    V, F = torso_loft([(1.688, 0.108, 0.12, 0.118, 0.06, cy), (1.724, 0.108, 0.12, 0.118, 0.06, cy)], n=28, p=2.6)
    parts.append(M.Part(V, F, "BH_Shadow", name="slit"))
    r0 = interp_rows(Hc, 1.697)
    back = []
    for z in (1.695, 1.717):
        full = torso_ring(z, r0[1], r0[2], r0[3], r0[4], 2.6, 56, cy=cy)
        back.append(full[18:39])
    V, F = M.loft(back, cap0=False, cap1=False, closed=False)
    parts.append(M.solidify(M.Part(V, F, "BH_Steel", name="helm_back"), 0.006, offset=1))
    # brow band and cross (gold)
    band = []
    for z in (1.714, 1.736):
        r = interp_rows(Hc, z)
        full = torso_ring(z, r[1] + 0.005, r[2] + 0.005, r[3] + 0.005, r[4], 2.6, 56, cy=cy)
        band.append(np.vstack([full[42:], full[:15]]))
    V, F = M.loft(band, cap0=False, cap1=False, closed=False)
    parts.append(M.solidify(M.Part(V, F, "BH_Gold", name="brow"), 0.004, offset=1))
    strip = []
    for z in np.linspace(1.56, 1.697, 5):
        fy = front_y([h for h in Hc], 0.0, z, p=2.6) - 0.004
        strip.append((0.0, fy, z))
    V, F = M.tube(strip, [(0.013, 0.006)] * len(strip), n=6, up=(0, -1, 0))
    parts.append(M.Part(V, F, "BH_Gold", name="cross"))
    # bottom rim
    V, F = thick_band(Hc, 1.548, 1.562, 0.006, -0.002, n=28, p=2.6)
    parts.append(M.Part(V, F, "BH_Gold", name="helm_rim"))
    # breaths (right cheek: -X)
    for row, z in enumerate((1.615, 1.64)):
        for k in range(3):
            ang = -0.55 - 0.13 * k
            x = 0.118 * math.sin(ang)
            y = -0.125 * math.cos(ang) + cy
            V, F = M.sphere(0.0065, 6, 4, center=(x * 1.01, y * 1.01, z - 0.012 * (k % 2)))
            parts.append(M.Part(V, F, "BH_Shadow", name="breath"))
    # crest: crimson fin on a gold base
    out = [(-0.075, 1.84), (-0.055, 1.895), (-0.015, 1.93), (0.045, 1.94), (0.105, 1.915), (0.15, 1.865),
           (0.168, 1.79), (0.13, 1.815), (0.085, 1.84), (0.02, 1.85)]
    o = np.array(out)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    V, F = M.prism(M.resample_closed(o, 30), 0.034, axis="x")
    fin = M.Part(V, F, "BH_Cloth_Primary", name="crest")
    fin.warp(lambda v: (v[0] * (1 - 0.6 * max(0, (v[2] - 1.85) / 0.09)), v[1], v[2]))
    parts.append(M.bevel(fin, 0.006, 2, angle=30))
    base = [(0, -0.07, 1.842), (0, 0.0, 1.853), (0, 0.08, 1.843), (0, 0.13, 1.815)]
    V, F = M.tube(base, [(0.02, 0.012)] * 4, n=6, up=(0, 0, 1))
    parts.append(M.Part(V, F, "BH_Gold", name="crest_base"))
    return parts


def cape():
    nu, nv = 13, 12

    def fn(u, v):
        top_half = 0.2
        bot_half = 0.27
        half = top_half + (bot_half - top_half) * v
        x = (u - 0.5) * 2 * half
        z = 1.47 + (0.64 - 1.47) * v
        if v < 0.2:
            yb = back_y(TORSO, x * 0.95, min(max(z, 1.3), 1.47)) + 0.035
        else:
            yb = back_y(TORSO, x * 0.95, 1.3) + 0.035
        y = yb + 0.07 * v ** 1.2 + 0.018 * math.sin(u * math.pi * 6.0) * v
        # shoulders: wrap forward a bit at the top corners
        y -= 0.05 * (abs(u - 0.5) * 2) ** 3 * (1 - v) ** 2
        z += 0.02 * math.cos(u * math.pi * 6.0) * v * 0.3
        return (x, y, z)
    V, F = M.grid(fn, nu, nv)
    p = M.Part(V, F, "BH_Cloth_Primary", name="cape")
    p = M.solidify(p, 0.012, offset=1.0, bevel_w=0.002)
    return p


def cape_w():
    def wfn(V):
        out = []
        for v in V:
            z = v[2]
            if z > 1.42:
                out.append({"chest": 1.0})
            elif z > 1.3:
                t = float(smoothstep(1.3, 1.42, z))
                out.append({"chest": t, "cape.1": 1 - t})
            elif z > 1.14:
                out.append({"cape.1": 1.0})
            elif z > 1.02:
                t = float(smoothstep(1.02, 1.14, z))
                out.append({"cape.1": t, "cape.2": 1 - t})
            else:
                out.append({"cape.2": 1.0})
        return out
    return wfn
