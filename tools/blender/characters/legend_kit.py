"""bh-021 legends kit: shared modeling helpers for Aljay, Roydo, Paul David and Kethrax, plus the mesh finishing pass
(consistent normals + a rest-pose box-projected UV map so the game can lay real textures on them).

Coordinates: model space of the standard 1.8 m skeleton (faces -Y, left = +X, Z up). The game scales each legend
(CutsceneActor / NpcDef.model_scale) to its real height.

Materials (palette names; the game maps the base name to a texture set in MaterialLibrary.LEGEND):
  BH_DragonPlate  dragon-scale plate          BH_HolyPlate   engraved polished plate
  BH_ForsakenIron pitted rusty iron           BH_Mail        riveted mail
  BH_Leather      worn leather                BH_Wool        heavy twill wool
  BH_Horn / BH_Bone  tyrant bone              BH_Crimson / BH_Gold  engraved trim metals
"""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, interp_rows, front_y, back_y, dome, M_align_z, smoothstep
from bh_math import normalize, R_axis
from char_mage import ring_frac, zspec_w
from town_matron import P_, outward


def mat(rgb, metal=0.0, rough=0.6, emis=None, estr=0.0):
    return (tuple(rgb), metal, rough, tuple(emis) if emis else None, estr, 1.0)


# ------------------------------------------------------------------------------------------------ finishing
def finish_mesh(ob, tile=1.0):
    """Recalculate face normals outward per island and add a box-projected UV map (1 UV unit = `tile` m) from the
    rest-pose coordinates: every face takes the plane of its dominant normal axis, so a tileable texture wraps the
    armour with no stretching and deforms with the skin."""
    import bmesh
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    uv = bm.loops.layers.uv.verify()
    k = 1.0 / tile
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        s = 1.0 if n[ax] >= 0 else -1.0
        for lp in f.loops:
            x, y, z = lp.vert.co
            if ax == 0:
                u, v = -s * y, z
            elif ax == 1:
                u, v = s * x, z
            else:
                u, v = x, s * y
            lp[uv].uv = (u * k + 0.13 * ax, v * k + 0.29 * ax)
    bm.to_mesh(me)
    bm.free()
    me.update()


# ------------------------------------------------------------------------------------------------ primitives
def curve_pts(base, d0, length, bend_axis=None, bend_deg=0.0, n=9, twist_axis=None, twist_deg=0.0):
    """Points of a curved spine starting at `base` heading `d0`, bending by bend_deg (total) about bend_axis."""
    pts = [np.asarray(base, float)]
    d = normalize(d0)
    step = length / (n - 1)
    for i in range(1, n):
        if bend_axis is not None and bend_deg:
            d = R_axis(bend_axis, bend_deg / (n - 1)) @ d
        if twist_axis is not None and twist_deg:
            d = R_axis(twist_axis, twist_deg / (n - 1)) @ d
        pts.append(pts[-1] + d * step)
    return np.array(pts)


def horn(base, d0, length, r0, bend_axis=None, bend_deg=0.0, n=10, mat="BH_Horn", flat=1.0, rings_ridge=True,
         up=(0, 0, 1), name="horn"):
    """Tapered, curving horn (cone along a bent spine). flat < 1 flattens the section; ridges add growth rings."""
    pts = curve_pts(base, d0, length, bend_axis, bend_deg, n)
    prof = []
    for i in range(n):
        t = i / (n - 1)
        r = r0 * (1 - t) ** 0.85 + 0.0015
        if rings_ridge and 0.1 < t < 0.8 and i % 2 == 1:
            r *= 1.08
        prof.append((r, r * flat))
    V, F = M.tube(pts, prof, n=8, up=up, cap1=True)
    return outward(P_(V, F, mat, name))


def spike(base, d, length, r0, mat="BH_Horn", n=6, name="spike"):
    base = np.asarray(base, float)
    d = normalize(d)
    V, F = M.tube([base, base + d * length * 0.55, base + d * length], [(r0, r0), (r0 * 0.5, r0 * 0.5), (0.001, 0.001)],
                  n=n, up=(0, 0, 1) if abs(d[2]) < 0.9 else (0, -1, 0))
    return outward(P_(V, F, mat, name))


def fin(base, d0, length, width, thick, bend_axis=None, bend_deg=0.0, n=9, mat="BH_DragonPlate", up=(0, 0, 1),
        name="fin", tip=0.0):
    """Blade-like curved plate (a flat tube tapering to a point): wing sheaths, vambrace fins, crest spines."""
    pts = curve_pts(base, d0, length, bend_axis, bend_deg, n)
    prof = []
    for i in range(n):
        t = i / (n - 1)
        w = width * (math.sin(math.pi * min(0.18 + t * 0.95, 1.0)) ** 0.6 if t < 0.8 else (1 - t) / 0.2 * 0.55) + 0.001
        if tip:
            w = width * (1 - t) ** tip + 0.001
        prof.append((w, thick * (1 - 0.6 * t) + 0.0008, 3.0))
    V, F = M.tube(pts, prof, n=8, up=up)
    return outward(P_(V, F, mat, name))


def edge_tube(pts, r, mat, n=5, name="trim"):
    pts = np.asarray(pts, float)
    d = pts[-1] - pts[0]
    up = (0, 0, 1) if abs(normalize(d)[2]) < 0.8 else (0, -1, 0)
    V, F = M.tube(pts, [(r, r)] * len(pts), n=n, up=up)
    return P_(V, F, mat, name)


def on_front(rows, x, z, off=0.0):
    return np.array([x, front_y(rows, x, z) - off, z])


def on_back(rows, x, z, off=0.0):
    return np.array([x, back_y(rows, x, z) + off, z])


def veins(rows, seeds, rng, steps=10, step=0.022, off=0.003, r=0.0038, mat="BH_Emissive", branch=0.35,
          zlim=(1.0, 1.52), xlim=0.17):
    """Branching glowing cracks crawling over the front of a torso-row surface from seed points (x, z)."""
    parts = []
    stack = [(np.array(s, float), a, steps, r) for s, a in seeds]
    while stack:
        p, ang, left, rad = stack.pop()
        pts = [on_front(rows, p[0], p[1], off)]
        for i in range(left):
            ang += rng.normal(0, 0.45)
            p = p + np.array([math.cos(ang), math.sin(ang)]) * step
            p[0] = float(np.clip(p[0], -xlim, xlim))
            p[1] = float(np.clip(p[1], *zlim))
            pts.append(on_front(rows, p[0], p[1], off))
            if rng.random() < branch * 0.25 and left - i > 3 and rad > 0.0022:
                stack.append((p.copy(), ang + rng.choice([-1, 1]) * rng.uniform(0.6, 1.1), left - i - 1, rad * 0.7))
        if len(pts) >= 2:
            prof = [(rad * (1 - 0.6 * i / (len(pts) - 1)) + 0.0008,) * 2 for i in range(len(pts))]
            V, F = M.tube(pts, prof, n=5, up=(0, -1, 0))
            parts.append(P_(V, F, mat, "vein"))
    return parts


def tattered_edge(n, seed, depth=0.06, teeth=9):
    """Per-sample lift (m) of a torn hem: long tongues and ragged notches."""
    r = np.random.default_rng(seed)
    u = np.linspace(0, 1, n)
    lift = np.abs(np.sin(u * math.pi * teeth + r.uniform(0, 3))) ** 0.5 * depth * 0.6
    lift += r.uniform(0, depth * 0.5, n)
    # a few deep rips
    for _ in range(3):
        c = r.uniform(0.1, 0.9)
        lift += depth * 1.6 * np.exp(-((u - c) / 0.025) ** 2)
    return lift


def cape_panel(rows, x0, x1, z_top, z_bot, seed, back_off=0.03, flare=0.1, nu=9, nv=14, depth_curve=0.08,
               mat="BH_Cloth_Primary", tear=0.07, solid=0.01, name="cape"):
    """Cape panel hanging behind the torso from x0..x1 at z_top down to a torn hem at z_bot."""
    lift = tattered_edge(nu, seed, tear)

    def fn(u, v):
        x = x0 + (x1 - x0) * u
        x *= 1 + flare * v
        zb = z_bot + lift[int(round(u * (nu - 1)))]
        z = z_top + (zb - z_top) * v
        zc = min(max(z, 1.02), z_top)
        y = back_y(rows, x * 0.95, zc) + back_off + depth_curve * v ** 1.3
        y += 0.016 * math.sin(u * math.pi * 5 + seed) * v
        return (x, y, z)
    V, F = M.grid(fn, nu, nv)
    p = P_(V, F, mat, name)
    return M.solidify(p, solid, offset=1.0)


def cape_weights(z_chest=1.42, z1=1.3, z2=1.14, z3=1.02):
    def wfn(V):
        out = []
        for v in V:
            z = v[2]
            if z > z_chest:
                out.append({"chest": 1.0})
            elif z > z1:
                t = float(smoothstep(z1, z_chest, z))
                out.append({"chest": t, "cape.1": 1 - t})
            elif z > z2:
                out.append({"cape.1": 1.0})
            elif z > z3:
                t = float(smoothstep(z3, z2, z))
                out.append({"cape.1": t, "cape.2": 1 - t})
            else:
                out.append({"cape.2": 1.0})
        return out
    return wfn


def hanging_plate(rows, frac0, frac1, z_top, z_bot, g, mat, point=0.35, n=9, nv=6, flare=0.18, name="tasset"):
    """Pointed plate hanging over the hips (tasset): follows the grown torso rows around frac0..frac1 at the top,
    flares outward and closes to a point at the bottom (point = how far up the point starts, 0..1)."""
    def fn(u, v):
        z = z_top + (z_bot - z_top) * v
        half = 1.0 - v * (1 - point) if v < 1 else point
        # narrow toward the point in the lower part
        uu = 0.5 + (u - 0.5) * (1.0 if v < 0.55 else max(0.02, 1 - (v - 0.55) / 0.45))
        fr = frac0 + (frac1 - frac0) * uu
        q = ring_frac(rows, max(min(z, rows[-1][0]), rows[0][0]), g + flare * v ** 1.2, [fr])[0]
        return (q[0], q[1], z - 0.02 * math.sin(math.pi * uu) * v)
    V, F = M.grid(fn, n, nv)
    p = P_(V, F, mat, name)
    return M.solidify(p, 0.007, offset=1.0, bevel_w=0.002)


def socket(body, side="R"):
    """Weapon socket frame of a hand in the MODEL pose: origin (grip centre) and axes (X knuckles for R, Y blade,
    Z back of hand)."""
    return np.asarray(body.head("weapon." + side), float), body.axes("weapon." + side)


def claws(body, side, mat="BH_Horn", length=0.04, r=0.008):
    """Talon tips over the curled fingers of a gauntleted fist (bone hand.<side>)."""
    o, A = socket(body, side)
    xs = 1.0 if side == "R" else -1.0
    out = []
    for k in range(4):
        y = -0.03 + 0.02 * k
        base = o + A @ np.array([0.05 * xs, y, -0.005])
        d = A @ np.array([0.2 * xs, 0.0, -1.0])
        out.append(spike(base, d, length, r, mat, name="claw"))
        kb = o + A @ np.array([0.035 * xs, y, 0.03])
        out.append(spike(kb, A @ np.array([0.4 * xs, 0, 1.0]), 0.022, 0.006, mat, name="knuckle_spike"))
    return out


def gem(center, r, mat="BH_Emissive", scale=(1, 0.5, 1.3), name="gem"):
    V, F = M.sphere(r, 10, 6, center=center, scale=scale)
    return P_(V, F, mat, name)


def lathe_part(profile, n, mat, name="lathe"):
    V, F = M.lathe(profile, n)
    return outward(P_(V, F, mat, name))


def chain(pts, link=0.028, r=0.0045, mat="BH_ForsakenIron", n_ring=10):
    """Chain of alternating links laid along a polyline (link = link length, r = wire radius)."""
    pts = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    parts = []
    count = max(1, int(L[-1] / (link * 0.72)))
    for i in range(count):
        t = (i + 0.5) * L[-1] / count
        j = min(np.searchsorted(L, t, side="right") - 1, len(seg) - 1)
        u = (t - L[j]) / max(seg[j], 1e-9)
        c = pts[j] * (1 - u) + pts[j + 1] * u
        d = normalize(pts[j + 1] - pts[j])
        a = normalize(np.cross(d, (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)))
        if i % 2:
            a = normalize(np.cross(d, a))
        b = np.cross(d, a)
        ring = [c + d * (link * 0.5 * math.cos(q)) + b * (link * 0.3 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, n_ring + 1)]
        V, F = M.tube(ring, [(r, r)] * len(ring), n=5, up=tuple(a), cap0=False, cap1=False)
        parts.append(P_(V, F, mat, "link"))
    return parts


def helix_pts(center_fn, z0, z1, turns, n=60, phase=0.0):
    """Points spiralling round a vertical body: center_fn(z) -> (cx, cy, rx, ry)."""
    out = []
    for i in range(n):
        t = i / (n - 1)
        z = z0 + (z1 - z0) * t
        a = phase + t * turns * 2 * math.pi
        cx, cy, rx, ry = center_fn(z)
        out.append((cx + rx * math.cos(a), cy + ry * math.sin(a), z))
    return out
