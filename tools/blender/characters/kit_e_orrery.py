"""Shared helpers for Builder E's bh-012 Shattered Orrery enemies (clockwork_sentry, astral_duelist, void_seer,
astrarch) and the Starmote creature (tools/blender/creatures/build_star_mote.py).

Pure geometry: every function returns bh_mesh.Part objects in whatever space its inputs are given. `ScaledP` lets a
module author in a "standard-ish" 1.8 m space with its own proportions (landmarks answer in that space, add() scales
to the real rig), like enemy_hollow_soldier.Scaled but for non-uniform proportion dicts.

Palette family (The Shattered Orrery): polished brass (BH_Bronze), tarnished brass (BH_Horn), dark iron
(BH_DarkSteel), midnight blue / violet cloth (BH_Cloth_Primary / BH_Cloth_Secondary), starglass (BH_Stone: dark
glass, flecked with tiny BH_Emissive specks), violet-white glow (BH_Emissive) and small gold accents (BH_Gold).
"""
import math

import numpy as np

import bh_mesh as M
from bh_body import Body, M_align_z
from bh_math import normalize, Rx, Ry, Rz, R_axis

# name: (base_rgb, metallic, roughness, emission_rgb, emission_strength, alpha)
BRASS = ((0.72, 0.5, 0.2), 0.85, 0.32, None, 0.0, 1.0)            # polished brass
BRASS_OLD = ((0.36, 0.3, 0.15), 0.7, 0.58, None, 0.0, 1.0)        # tarnished brass
IRON = ((0.085, 0.085, 0.1), 0.9, 0.5, None, 0.0, 1.0)            # dark iron
GOLD = ((0.85, 0.62, 0.24), 1.0, 0.3, None, 0.0, 1.0)             # gold accents
GLOW = ((0.75, 0.55, 1.0), 0.0, 0.4, (0.75, 0.55, 1.0), 8.0, 1.0)  # violet-white glow
STARGLASS = ((0.03, 0.03, 0.075), 0.2, 0.1, (0.035, 0.025, 0.1), 1.0, 1.0)
VOID = ((0.012, 0.01, 0.022), 0.0, 0.85, None, 0.0, 1.0)          # void black (hood interior, recesses)
MIDNIGHT = ((0.028, 0.035, 0.11), 0.0, 0.86, None, 0.0, 1.0)
VIOLET = ((0.13, 0.05, 0.22), 0.0, 0.82, None, 0.0, 1.0)
SILVER = ((0.72, 0.74, 0.8), 1.0, 0.28, None, 0.0, 1.0)


def P(V, F, mat, name="part"):
    return M.Part(np.asarray(V, float), F, mat, name=name)


# ------------------------------------------------------------------------------------------------ authoring space
class ScaledP:
    """Author in a scaled-down space: std Body built from props / k; add() scales parts by k onto the real Body."""

    def __init__(self, real, k, extra_bones=None):
        self.real, self.k = real, float(k)
        sp = {n: v / self.k for n, v in real.p.items()}
        ex = [(n, tuple(np.array(h) / k), tuple(np.array(t) / k), par, z) for (n, h, t, par, z) in (extra_bones or [])]
        self.std = Body(sp, extra_bones=ex)
        self.p, self.D, self.rig = self.std.p, self.std.D, self.std.rig

    def __getattr__(self, name):
        return getattr(self.std, name)

    def _w(self, weights):
        if weights is None:
            return None
        k = self.k
        return lambda V, f=weights: f(np.asarray(V) / k)

    def add(self, part, bone=None, weights=None):
        part.V = part.V * self.k
        return self.real.add(part, bone, self._w(weights))

    def add_all(self, parts, bone=None, weights=None):
        for p in parts:
            self.add(p, bone, weights)


def levels(p):
    zh = p["pelvis_h"]
    zs = zh + p["hips_len"]
    zc = zs + p["spine_len"]
    zn = zc + p["chest_len"]
    zhd = zn + p["neck_len"]
    return dict(hips=zh, spine=zs, chest=zc, neck=zn, head=zhd, top=zhd + p["head_len"], shoulder=zn - p["clav_drop"])


def zspec_w(spec):
    """Blend bones along height: spec = [(z, bone), ...] ascending."""
    from bh_body import smoothstep

    def wfn(V):
        out = []
        for v in V:
            z = v[2]
            if z <= spec[0][0]:
                out.append({spec[0][1]: 1.0})
                continue
            if z >= spec[-1][0]:
                out.append({spec[-1][1]: 1.0})
                continue
            d = {spec[-1][1]: 1.0}
            for (z0, b0), (z1, b1) in zip(spec, spec[1:]):
                if z0 <= z <= z1:
                    if b0 == b1:
                        d = {b0: 1.0}
                    else:
                        t = float(smoothstep(z0, z1, z))
                        d = {b0: 1 - t, b1: t}
                    break
            out.append({k: x for k, x in d.items() if x > 1e-4})
        return out
    return wfn


def const_w(d):
    return lambda V, d=d: [dict(d)] * len(V)


# ------------------------------------------------------------------------------------------------ primitives
def tube(pts, radii, mat, n=8, up=None, cap=True, p=2.0, name="tube"):
    pts = np.asarray(pts, float)
    if np.ndim(radii) == 0 or isinstance(radii, tuple):
        radii = [radii] * len(pts)
    prof = [(r, r) if np.ndim(r) == 0 else tuple(r) for r in radii]
    if up is None:
        d = normalize(pts[-1] - pts[0])
        up = (0, 0, 1) if abs(d[2]) < 0.85 else (0, -1, 0)
    V, F = M.tube(pts, prof, n=n, up=up, cap0=cap, cap1=cap, p=p)
    return P(V, F, mat, name)


def taper(pts, r0, r1, mat, n=6, up=None, power=1.0, name="taper"):
    k = len(pts)
    rr = [r0 + (r1 - r0) * (i / (k - 1)) ** power for i in range(k)]
    return tube(pts, rr, mat, n=n, up=up, name=name)


def ball(c, r, mat, n=10, rings=6, scale=(1, 1, 1), name="ball"):
    V, F = M.sphere(r, n, rings, center=c, scale=scale)
    return P(V, F, mat, name)


def orient(part, center, normal, up=(0, 0, 1)):
    """Part authored around the origin with +Z as its axis -> axis along `normal` at `center`."""
    n = normalize(normal)
    u = np.asarray(up, float)
    if abs(np.dot(normalize(u), n)) > 0.95:
        u = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    R = M_align_z(n, u)
    part.V = part.V @ R.T + np.asarray(center, float)
    return part


def lathe(profile, mat, n=12, name="lathe", cap=True):
    V, F = M.lathe(profile, n, cap=cap)
    return P(V, F, mat, name)


def ring(center, normal, radius, r_tube, mat, n=28, m=6, up=(0, 0, 1), arc=(0.0, 360.0), flat=1.0, name="ring"):
    """Torus / arc ring of radius `radius` around `normal`. flat < 1 flattens the tube along the ring axis."""
    a0, a1 = arc
    full = abs(a1 - a0) >= 359.9
    na = n if full else n + 1
    angs = np.radians(np.linspace(a0, a1, na, endpoint=not full))
    V, F = [], []
    for a in angs:
        ca, sa = math.cos(a), math.sin(a)
        for j in range(m):
            b = 2 * math.pi * j / m
            rr = radius + r_tube * math.cos(b)
            V.append((rr * ca, rr * sa, r_tube * flat * math.sin(b)))
    rows = na if full else na - 1
    for i in range(rows):
        i2 = (i + 1) % na
        for j in range(m):
            j2 = (j + 1) % m
            F.append((i * m + j, i2 * m + j, i2 * m + j2, i * m + j2))
    if not full:
        F.append(tuple(reversed(range(m))))
        F.append(tuple((na - 1) * m + j for j in range(m)))
    return orient(P(V, F, mat, name), center, normal, up)


def band_ring(center, normal, radius, width, thick, mat, n=28, up=(0, 0, 1), name="band"):
    """Flat band (short wide cylinder shell) - orrery ring with a rectangular section."""
    prof = [(radius - thick / 2, -width / 2), (radius + thick / 2, -width / 2), (radius + thick / 2, width / 2),
            (radius - thick / 2, width / 2), (radius - thick / 2, -width / 2)]
    V, F = M.lathe(prof, n, cap=False)
    return orient(P(V, F, mat, name), center, normal, up)


def disc(center, normal, r, thick, mat, n=16, up=(0, 0, 1), name="disc"):
    V, F = M.lathe([(0.0, -thick / 2), (r, -thick / 2), (r, thick / 2), (0.0, thick / 2)], n)
    return orient(P(V, F, mat, name), center, normal, up)


def dome(center, normal, r, mat, n=14, rings=5, depth=0.5, up=(0, 0, 1), name="dome"):
    """Spherical cap bulging along `normal` (closed with a flat back)."""
    prof = [(0.0, 0.0)]
    for i in range(rings + 1):
        a = math.pi / 2 * i / rings
        prof.append((r * math.cos(a), r * depth * math.sin(a)))
    prof[-1] = (0.0, r * depth)
    V, F = M.lathe(prof, n)
    return orient(P(V, F, mat, name), center, normal, up)


def gear(center, normal, r_out, teeth, thick, mat, r_root=None, hub=0.0, n_per=4, up=(0, 0, 1), name="gear"):
    """Toothed gear disc (prism). hub > 0 cuts nothing (solid) but a hub ring can be added separately."""
    r_root = r_root or r_out * 0.82
    pts = []
    for i in range(teeth):
        a0 = 2 * math.pi * i / teeth
        da = 2 * math.pi / teeth
        for u, r in ((0.0, r_root), (0.18, r_out), (0.5, r_out), (0.68, r_root)):
            a = a0 + da * u
            pts.append((r * math.cos(a), r * math.sin(a)))
    V, F = M.prism(pts, thick, axis="z")
    return orient(P(V, F, mat, name), center, normal, up)


def spokes_gear(center, normal, r_out, teeth, thick, mat, spokes=4, up=(0, 0, 1), name="gear"):
    """Gear with an open rim + spokes + hub (reads as clockwork)."""
    parts = []
    r_root = r_out * 0.84
    # rim: toothed outline outer, circle inner
    outer = []
    for i in range(teeth):
        a0 = 2 * math.pi * i / teeth
        da = 2 * math.pi / teeth
        for u, r in ((0.0, r_root), (0.2, r_out), (0.5, r_out), (0.7, r_root)):
            a = a0 + da * u
            outer.append((r * math.cos(a), r * math.sin(a)))
    ri = r_out * 0.66
    nO = len(outer)
    inner = [(ri * math.cos(2 * math.pi * i / nO), ri * math.sin(2 * math.pi * i / nO)) for i in range(nO)]
    V, F = [], []
    for z in (-thick / 2, thick / 2):
        V += [(x, y, z) for x, y in outer] + [(x, y, z) for x, y in inner]
    o0, i0, o1, i1 = 0, nO, 2 * nO, 3 * nO
    for i in range(nO):
        j = (i + 1) % nO
        F.append((o1 + i, o1 + j, i1 + j, i1 + i))       # top
        F.append((o0 + j, o0 + i, i0 + i, i0 + j))       # bottom
        F.append((o0 + i, o0 + j, o1 + j, o1 + i))       # outer wall
        F.append((i0 + j, i0 + i, i1 + i, i1 + j))       # inner wall
    parts.append(orient(P(V, F, mat, name), center, normal, up))
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        V, F = M.box(ri * 1.02, r_out * 0.12, thick * 0.8, center=(ri * 0.5, 0, 0))
        sp = P(V, F, mat, "spoke").rot(Rz(math.degrees(a)))
        parts.append(orient(sp, center, normal, up))
    parts.append(disc(center, normal, r_out * 0.22, thick * 1.3, mat, n=10, up=up, name="hub"))
    return parts


def rivets(points, r, mat, n=6, name="rivet"):
    out = []
    for c in points:
        V, F = M.sphere(r, n, 3, center=c, scale=(1, 1, 1))
        out.append(P(V, F, mat, name))
    return out


def ring_points(center, normal, radius, count, up=(0, 0, 1), phase=0.0):
    R = M_align_z(normalize(normal), up if abs(np.dot(normalize(up), normalize(normal))) < 0.95 else (1, 0, 0))
    c = np.asarray(center, float)
    return [c + R @ np.array([radius * math.cos(2 * math.pi * i / count + phase),
                              radius * math.sin(2 * math.pi * i / count + phase), 0.0]) for i in range(count)]


def speck(c, r, mat="BH_Emissive", seed=0):
    """Tiny octahedron (8 tris): star fleck."""
    rng = np.random.default_rng(seed)
    V = np.array([(r, 0, 0), (-r, 0, 0), (0, r, 0), (0, -r, 0), (0, 0, r), (0, 0, -r)], float)
    R = R_axis(rng.normal(size=3), rng.random() * 90)
    V = V @ R.T + np.asarray(c, float)
    F = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
    return P(V, F, mat, "speck")


def star4(c, r, normal, mat="BH_Emissive", up=(0, 0, 1), thick=0.004):
    """Flat four-pointed star sparkle (prism)."""
    pts = []
    for i in range(8):
        a = math.pi / 4 * i
        rr = r if i % 2 == 0 else r * 0.3
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    V, F = M.prism(pts, thick, axis="z")
    return orient(P(V, F, mat, "star"), c, normal, up)


def surface_specks(part, count, r, seed=1, mat="BH_Emissive", lift=0.002, zmin=-9.0, zmax=9.0):
    """Scatter tiny glowing specks on a part's vertices (with the face-average normal pushed out a little)."""
    rng = np.random.default_rng(seed)
    V = part.V
    cen = V.mean(0)
    idx = [i for i in range(len(V)) if zmin <= V[i, 2] <= zmax]
    if not idx:
        return []
    pick = rng.choice(idx, size=min(count, len(idx)), replace=False)
    N = np.zeros_like(V)
    for f in part.F:
        a, b_, c = V[f[0]], V[f[1]], V[f[2]]
        n = np.cross(b_ - a, c - a)
        for i in f:
            N[i] += n
    out = []
    for k, i in enumerate(pick):
        d = N[i] if np.linalg.norm(N[i]) > 1e-12 else V[i] - cen
        out.append(speck(V[i] + normalize(d) * lift, r * (0.7 + 0.6 * rng.random()), mat, seed=seed * 100 + k))
    return out


def armillary(center, radius, r_tube, mat, n=20, core=None, core_r=0.0, tilt=(0.0, 60.0, -60.0), up=(0, 0, 1)):
    """Small armillary sphere: three crossing rings (+ optional glowing core)."""
    parts = []
    c = np.asarray(center, float)
    normals = [(0, 0, 1), R_axis((1, 0, 0), 70) @ np.array([0, 0, 1.0]), R_axis((0, 1, 0), 70) @ np.array([0, 0, 1.0])]
    for k, nrm in enumerate(normals):
        rr = radius * (1.0 - 0.06 * k)
        parts.append(ring(c, nrm, rr, r_tube, mat, n=n, m=5, name="arm_ring"))
    if core:
        parts.append(ball(c, core_r or radius * 0.35, core, n=10, rings=6))
    return parts


def fins(center, axis, r0, r1, count, width, thick, mat, up=(0, 0, 1), phase=0.0):
    """Radial fins/blades around an axis (flat plates)."""
    out = []
    ax = normalize(axis)
    R = M_align_z(ax, up if abs(np.dot(normalize(up), ax)) < 0.95 else (1, 0, 0))
    for i in range(count):
        a = 2 * math.pi * i / count + phase
        V, F = M.box(r1 - r0, thick, width, center=((r0 + r1) / 2, 0, 0))
        prt = P(V, F, mat, "fin").rot(Rz(math.degrees(a)))
        prt.V = prt.V @ R.T + np.asarray(center, float)
        out.append(prt)
    return out
