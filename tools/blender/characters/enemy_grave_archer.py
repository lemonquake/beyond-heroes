"""Grave Archer (undead ranged, builder A): a lean hooded skeleton in a tattered moss-green hood, capelet and long
ragged cloak (cape bones), bare skull with the jaw hanging and teal grave-light eyes under the hood. A bone-and-sinew
longbow in the left hand, a quiver of black-fletched arrows on the back (baldric across the bare ribcage), leather
bracer on the bow arm, rag belt and leg wraps."""
import math
import numpy as np

import bh_mesh as M
from bh_body import Body, front_y, back_y, dome, fist, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
from char_knight import CAPE_BONES, secondary as _cape_secondary, thick_band
from char_mage import HOOD, HOOD_W, zspec_w
import enemy_hollow_soldier as HS
from enemy_hollow_soldier import P, rtube, ball, add_weapon, cloth_panel, cloth_w, ragged, ENV

PROPS = proportions()
EXTRA_BONES = CAPE_BONES
PALETTE = "grave_archer"
PALETTE_COLORS = {
    "BH_Bone": ((0.50, 0.47, 0.37), 0.0, 0.62, None, 0.0, 1.0),
    "BH_Cloth_Primary": ((0.075, 0.105, 0.05), 0.0, 0.92, None, 0.0, 1.0),     # moss-green hood / cloak
    "BH_Cloth_Secondary": ((0.30, 0.28, 0.22), 0.0, 0.8, None, 0.0, 1.0),      # sinew / bowstring
    "BH_Leather": ((0.065, 0.045, 0.03), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Wood": ((0.09, 0.07, 0.05), 0.0, 0.75, None, 0.0, 1.0),
    "BH_Hair": ((0.025, 0.025, 0.03), 0.0, 0.8, None, 0.0, 1.0),                # black fletching
    "BH_DarkSteel": ((0.12, 0.16, 0.14), 0.85, 0.55, None, 0.0, 1.0),
    "BH_Shadow": ((0.025, 0.03, 0.03), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((0.3, 0.9, 0.8), 0.0, 0.4, (0.3, 1.0, 0.85), 7.0, 1.0),
}
CLIPS = ["bow_release", "bow_draw_hold"]


def finish_mesh(mesh_ob):
    HS.enable_weapon_deform(mesh_ob)


def secondary(anim, frames):
    return _cape_secondary(anim, frames)


# --------------------------------------------------------------------------------------------------- bow
def bone_longbow():
    """Weapon-GLB space: grip at origin, limbs along +-Z, string on -X (as bh_weapons.bow)."""
    parts = []
    pts, prof = [], []
    n = 12
    for i in range(n + 1):
        u = i / n
        z = 0.07 + 0.74 * u
        x = -0.1 * u ** 1.6 + 0.05 * max(u - 0.8, 0) ** 1.3 / 0.2 ** 1.3
        pts.append((x, 0, z))
        prof.append((0.018 * (1 - 0.55 * u) + 0.005, 0.015 * (1 - 0.5 * u) + 0.004))
    V, F = M.tube(pts, prof, n=6, up=(1, 0, 0), p=2.2)
    up = P(V, F, "BH_Bone", "limb")
    # knuckle-like swellings (the limbs are made of joined bones)
    up.warp(lambda v: (v[0], v[1] * (1 + 0.35 * max(0, math.cos(v[2] * 60)) ** 8),
                       v[2]))
    lo = up.copy().scale((1, 1, -1)).flip()
    parts += [up, lo]
    # sinew wraps
    for zc in (0.2, 0.42, 0.62):
        i = min(int((zc - 0.07) / 0.74 * n), n - 1)
        c = np.array(pts[i])
        for sz in (1, -1):
            V, F = M.lathe([(0, -0.012), (0.022, -0.012), (0.022, 0.012), (0, 0.012)], 6)
            parts.append(P(V, F, "BH_Cloth_Secondary", "wrap").move((c[0], 0, sz * zc)))
    V, F = M.tube([(0.004, 0, -0.1), (0.012, 0, 0.0), (0.004, 0, 0.1)], [(0.02, 0.022), (0.024, 0.027), (0.02, 0.022)],
                  n=8, up=(1, 0, 0))
    parts.append(P(V, F, "BH_Leather", "riser"))
    # hooked skull-tip ornaments (small vertebrae)
    tip = np.array(pts[-1])
    for sz in (1, -1):
        parts.append(ball((tip[0] + 0.01, 0, sz * (tip[2] + 0.015)), 0.016, "BH_Bone", 6, 4))
    V, F = M.tube([(tip[0], 0, tip[2] - 0.01), (tip[0], 0, -tip[2] + 0.01)], [(0.0022, 0.0022)] * 2, n=4, up=(1, 0, 0))
    parts.append(P(V, F, "BH_Cloth_Secondary", "string"))
    return parts


# --------------------------------------------------------------------------------------------------- cloth
def hood(body):
    """Tattered hood (moss cloth) around the skull; ragged front edge; dark lining."""
    parts = []
    nu = 20
    rings = []
    for k, (z, rx, ryf, ryb, cy, th) in enumerate(HOOD):
        ring = []
        for u in np.linspace(0, 1, nu):
            a = math.radians(th + (360 - 2 * th) * u)
            sa, ca = math.sin(a), math.cos(a)
            s = 1.08
            ring.append((rx * s * sa, cy - (ryf * s if ca > 0 else ryb * s) * ca - 0.012, z + 0.012))
        rings.append(np.array(ring))
    # drape the lower rim onto the shoulders
    low = rings[0].copy()
    low[:, 0] *= 1.35
    low[:, 1] = low[:, 1] * 1.15
    low[:, 2] -= 0.05
    rings = [low] + rings
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    h = P(V, F, "BH_Cloth_Primary", "hood")
    # ragged front edge: pull the opening edge verts back a bit irregularly
    h.warp(lambda v: (v[0], v[1] + (0.012 * math.sin(v[2] * 90) if v[1] < -0.06 else 0.0), v[2]))
    parts.append(M.solidify(h, 0.012, offset=-1.0))
    inner = []
    for (z, rx, ryf, ryb, cy, th) in HOOD[1:6]:
        ring = []
        for u in np.linspace(0, 1, nu):
            a = math.radians(th + (360 - 2 * th) * u)
            ring.append((rx * 0.97 * math.sin(a), cy - (ryf if math.cos(a) > 0 else ryb) * 0.97 * math.cos(a) - 0.01,
                         z + 0.012))
        inner.append(np.array(ring))
    V, F = M.loft(inner, cap0=False, cap1=False, closed=False)
    parts.append(P(V, F, "BH_Shadow", "lining").flip())
    # point of the hood trailing back
    parts.append(rtube([(0, 0.1, 1.86), (0, 0.16, 1.8), (0, 0.19, 1.72)], 0.03, "BH_Cloth_Primary", n=6, r1=0.006))
    return parts


def capelet():
    """Short ragged shoulder cape over the collarbones (chest/shoulder weighted)."""
    nu, nv = 34, 5
    gap = math.radians(34)
    rings = []
    for j in range(nv):
        v = j / (nv - 1)
        ring = []
        for i in range(nu):
            th = gap + (2 * math.pi - 2 * gap) * i / (nu - 1)
            st, ct = math.sin(th), math.cos(th)
            rx = 0.1 + 0.2 * v
            ry = (0.085 + 0.08 * v) if ct > 0 else (0.085 + 0.1 * v)
            drop = 0.11 + 0.1 * ct * ct
            z = 1.56 - drop * v ** 2 - (ragged(i / (nu - 1), 7.0, 0.07, 9) * v ** 3)
            ring.append((rx * st, 0.012 - ry * ct, z))
        rings.append(np.array(ring))
    rings = rings[::-1]
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    return M.solidify(P(V, F, "BH_Cloth_Primary", "capelet"), 0.009, offset=1.0)


def capelet_w():
    def wfn(V):
        out = []
        for v in V:
            s = float(smoothstep(0.14, 0.28, abs(v[0])))
            side = "L" if v[0] > 0 else "R"
            d = {"chest": 1 - 0.55 * s}
            if s > 1e-4:
                d["shoulder." + side] = 0.33 * s
                d["upper_arm." + side] = 0.22 * s
            out.append(d)
        return out
    return wfn


def cloak():
    nu, nv = 13, 12

    def fn(u, v):
        half = 0.19 + 0.12 * v
        x = (u - 0.5) * 2 * half
        zb = 0.42 + ragged(u, 3.3, 0.16, 5)
        z = 1.47 + (zb - 1.47) * v
        yb = back_y(ENV, x * 0.9, min(max(z, 1.3), 1.47)) + 0.04 if v < 0.2 else back_y(ENV, x * 0.9, 1.3) + 0.04
        y = yb + 0.06 * v ** 1.2 + 0.02 * math.sin(u * math.pi * 5.0) * v
        y -= 0.06 * (abs(u - 0.5) * 2) ** 3 * (1 - v) ** 2
        return (x, y, z)
    V, F = M.grid(fn, nu, nv)
    return M.solidify(P(V, F, "BH_Cloth_Primary", "cloak"), 0.01, offset=1.0)


def cloak_w():
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


def quiver():
    """On the back, top over the right shoulder. Model space, chest bone."""
    parts = []
    top = np.array([-0.1, 0.17, 1.47])
    bot = np.array([0.08, 0.15, 1.02])
    d = normalize(top - bot)
    V, F = M.tube([bot, bot + d * 0.02, top - d * 0.02, top], [(0.035, 0.045), (0.048, 0.058), (0.05, 0.06),
                                                               (0.05, 0.06)], n=8, up=(0, 1, 0), cap1=False)
    parts.append(M.solidify(P(V, F, "BH_Leather", "quiver"), 0.005, offset=-1))
    for k, t in enumerate(np.linspace(0.12, 0.9, 3)):
        c = bot + (top - bot) * t
        V, F = M.tube([c - d * 0.01, c + d * 0.01], [(0.056, 0.066)] * 2, n=8, up=(0, 1, 0))
        parts.append(P(V, F, "BH_DarkSteel", "qband"))
    side = normalize(np.cross(d, np.array([0, 1.0, 0])))
    for i, (ox, oy) in enumerate(((0.0, 0.0), (0.022, 0.015), (-0.02, 0.012), (0.012, -0.02), (-0.014, -0.018))):
        b = top - d * 0.1 + side * ox + np.array([0, oy, 0])
        e = b + d * (0.2 + 0.02 * (i % 2))
        parts.append(rtube([b, e], 0.0045, "BH_Wood", n=4))
        # black fletching: two crossed vanes
        for rot in (0, 90):
            ax = side if rot == 0 else np.array([0, 1.0, 0])
            V = np.array([e - d * 0.1, e - d * 0.02, e + ax * 0.02 - d * 0.03, e + ax * 0.024 - d * 0.1,
                          e - ax * 0.02 - d * 0.03, e - ax * 0.024 - d * 0.1])
            F = [(0, 3, 2, 1), (0, 1, 4, 5), (0, 1, 2, 3), (0, 5, 4, 1)]
            parts.append(P(V, F, "BH_Hair", "fletch"))
    return parts


# --------------------------------------------------------------------------------------------------- build
def build(body: Body):
    add = body.add
    for prt in HS.skull(body, jaw_open=14.0, s=0.97):
        add(prt, "head")
    for prt in hood(body):
        add(prt, weights=HOOD_W)
    for z in np.arange(1.495, 1.61, 0.032):
        V, F = M.lathe([(0, -0.008), (0.021, -0.007), (0.023, 0.0), (0.021, 0.007), (0, 0.008)], 8)
        add(P(V, F, "BH_Bone", "cvert").move((0, 0.012, z)), weights=HS.NECK_W if z < 1.51 else None,
            bone=None if z < 1.51 else "neck")
    add(rtube([(0, 0.02, 1.47), (0, 0.01, 1.62)], 0.012, "BH_Bone", n=6), weights=HS.NECK_W)
    for prt, w in HS.spine_column(body):
        add(prt, weights=w)
    for prt in HS.ribcage(body, s=0.96):
        add(prt, "chest")
    for prt in HS.pelvis(body, s=0.95):
        add(prt, "hips")
    for sx, s in ((1, "L"), (-1, "R")):
        sh = body.head("upper_arm." + s)
        add(rtube([(sx * 0.02, -0.075, 1.445), (sx * 0.1, -0.05, 1.462), (sh[0] - sx * 0.01, -0.01, sh[2] + 0.02)],
                  0.011, "BH_Bone", n=5), "shoulder." + s)
        add(ball(sh, 0.028, "BH_Bone", 8, 5), "upper_arm." + s)
        for prt, b in HS.bone_arm(body, s, r=0.95, hand_scale=0.85):
            add(prt, b)
        for prt, b in HS.bone_leg(body, s, r=0.95):
            add(prt, b)
        for prt, b in HS.boot(body, s, top=0.24, wrap_mat="BH_Cloth_Primary"):
            add(prt, b)
    # bow-arm bracer (left)
    fa = "forearm.L"
    L = body.p["fore_len"]
    V, F = M.tube(body.lpt(fa, [(0, u * L, 0) for u in (0.4, 0.7, 0.98)]), [(0.036, 0.038), (0.035, 0.037),
                                                                            (0.032, 0.034)], n=8, up=(0, 0, 1))
    add(P(V, F, "BH_Leather", "bracer"), fa)
    # cloth: capelet, cloak, rag skirt, belt, baldric
    add(capelet(), weights=capelet_w())
    add(cloak(), weights=cloak_w())
    add(cloth_panel(ENV, 1.06, 0.66, lambda z: 0.09 + 0.05 * (1.06 - z), front=True, nu=7, nv=6, seed=2.4, rag=0.12,
                    teeth=3), weights=cloth_w())
    V, F = thick_band(ENV, 1.035, 1.07, 0.022, 0.01, n=20)
    add(P(V, F, "BH_Leather", "belt"), "hips")
    pts = []
    for t in np.linspace(0, 1, 9):          # baldric: right hip -> over the left shoulder (quiver strap)
        x = -0.14 + 0.28 * t
        z = 1.06 + 0.42 * t
        pts.append((x, front_y(ENV, x * 0.9, min(z, 1.46)) - 0.018, z))
    add(rtube(pts, 0.012, "BH_Leather", n=4), weights=zspec_w([(1.08, "hips"), (1.14, "spine"), (1.24, "spine"),
                                                              (1.3, "chest")]))
    for prt in quiver():
        add(prt, "chest")
    add_weapon(body, "L", bone_longbow())
