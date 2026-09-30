"""bh-023: the modelling kit behind hero_hair.py (the fitted skull, strands, locks, sheets, the mesh accumulator).

Everything is numpy; Blender is only needed for the BVH tree of the hero's surface (work/.../hero_mesh.npz) and, in
hero_hair.py, to make the mesh object and export it.

Directions around the head are given as (az, pol) in degrees about the skull centre C: az 0 = the face (-Y),
+90 = the hero's left (+X), 180 = the back of the head; pol 0 = straight up.  `Head.H(az, f)` is the direction at the
fraction f of the way from the crown (f = 0) to the hairline (f = 1) on that azimuth, so styles are written in terms of
the hairline and never in raw angles.
"""
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCRATCH = os.path.join(ROOT, "work", "lemondev", "bh-023", "scratch")

C = np.array([0.0, -0.04, 1.70])       # centre of the skull
AXIS_Y = -0.03                         # the vertical axis the face / beard is measured around
UP = np.array([0.0, 0.0, 1.0])
DOWN = np.array([0.0, 0.0, -1.0])


# ---- small maths -----------------------------------------------------------------------------------------------------

def unit(v):
    v = np.asarray(v, float)
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def sstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def pw(vals, t):
    """Piecewise-linear profile through evenly spaced knots, sampled at t in 0..1 (a scalar stays a constant)."""
    t = np.asarray(t, float)
    if np.isscalar(vals):
        return np.full(t.shape, float(vals))
    vals = np.asarray(vals, float)
    return np.interp(t, np.linspace(0, 1, len(vals)), vals)


def dirv(az, pol):
    az, pol = np.radians(az), np.radians(pol)
    return np.stack([np.sin(pol) * np.sin(az), -np.sin(pol) * np.cos(az), np.cos(pol)], -1)


def az_pol(d):
    d = unit(d)
    pol = np.degrees(np.arccos(np.clip(d[..., 2], -1, 1)))
    az = np.degrees(np.arctan2(d[..., 0], -d[..., 1]))
    return az, pol


def slerp(a, b, t):
    a, b = unit(a), unit(b)
    w = math.acos(float(np.clip(a @ b, -1, 1)))
    t = np.asarray(t, float)[..., None]
    if w < 1e-6:
        return unit(a + (b - a) * t)
    return (np.sin((1 - t) * w) * a + np.sin(t * w) * b) / math.sin(w)


def arc_t(P):
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    L = np.concatenate([[0.0], np.cumsum(seg)])
    return L / max(L[-1], 1e-9)


def resample(P, k):
    P = np.asarray(P, float)
    t = arc_t(P)
    ts = np.linspace(0, 1, k)
    return np.stack([np.interp(ts, t, P[:, i]) for i in range(3)], 1)


def spline(pts, k, sub=12):
    """Catmull-Rom through the control points, resampled to k points evenly by length."""
    p = np.asarray(pts, float)
    if len(p) == 2:
        return resample(p, k)
    q = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(len(p) - 1):
        p0, p1, p2, p3 = q[i], q[i + 1], q[i + 2], q[i + 3]
        for s in np.linspace(0, 1, sub, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3))
    out.append(p[-1])
    return resample(np.array(out), k)


def tangents(P):
    T = np.empty_like(P)
    T[1:-1] = P[2:] - P[:-2]
    T[0] = P[1] - P[0]
    T[-1] = P[-1] - P[-2]
    return unit(T)


def perp(T, ref):
    """ref made perpendicular to T (row-wise)."""
    ref = np.broadcast_to(np.asarray(ref, float), T.shape)
    n = ref - T * (T * ref).sum(-1, keepdims=True)
    bad = np.linalg.norm(n, axis=-1) < 1e-5
    if bad.any():
        alt = np.cross(T, np.array([1.0, 0.0, 0.0]))
        n = np.where(bad[:, None], alt, n)
    return unit(n)


# ---- the head --------------------------------------------------------------------------------------------------------

def hairline(y):
    ys = np.array([-0.17, -0.150, -0.12, -0.09, -0.06, -0.035, -0.01, 0.02, 0.10])
    zs = np.array([1.756, 1.754, 1.748, 1.734, 1.712, 1.700, 1.668, 1.632, 1.612])
    return np.interp(y, ys, zs)


def beard_top(ax):
    xs = np.array([0.0, 0.02, 0.03, 0.045, 0.06, 0.075, 0.088, 0.12])
    zs = np.array([1.640, 1.640, 1.633, 1.624, 1.632, 1.656, 1.678, 1.678])
    return np.interp(ax, xs, zs)


try:                                    # the authoritative copies (hero_skin needs PIL, which Blender lacks)
    import hero_skin as _HSK
    hairline, beard_top = _HSK.hairline, _HSK.beard_top
except Exception:
    pass


class Head:
    """The hero's surface: a smooth radial map of the skull (ears removed) plus the body's BVH tree."""

    AZ = np.arange(-180.0, 180.1, 5.0)
    POL = np.arange(0.0, 160.1, 4.0)

    def __init__(self):
        from mathutils.bvhtree import BVHTree
        d = np.load(os.path.join(SCRATCH, "hero_mesh.npz"))
        self.V, self.T = d["V"], d["T"]
        self.bvh = BVHTree.FromPolygons([tuple(v) for v in self.V.tolist()], [tuple(t) for t in self.T.tolist()])
        self._skull()
        self._hairline()

    # -- skull radial map
    def _skull(self):
        A, Pl = np.meshgrid(self.AZ, self.POL)
        D = dirv(A, Pl)
        r = np.full(A.shape, np.nan)
        for i in range(A.shape[0]):
            for j in range(A.shape[1]):
                hit = self.bvh.ray_cast(tuple(C), tuple(D[i, j]), 0.4)
                if hit[0] is not None:
                    p = np.array(hit[0])
                    rr = hit[3]
                    # the ears are not the skull: keep the radius on the side of the head there
                    if abs(p[0]) > 0.0805 and 1.625 < p[2] < 1.705 and -0.08 < p[1] < 0.005:
                        rr *= 0.0805 / abs(p[0])
                    r[i, j] = rr
        r[0, :] = np.nanmean(r[0, :])
        r = np.where(np.isnan(r), np.nanmean(r), r)
        r = 0.5 * (r + r[:, ::-1])                      # the head is symmetric; keep the hair so too
        for _ in range(2):                              # soften the facets
            rp = np.concatenate([r[:, -2:-1], r, r[:, 1:2]], 1)
            rr = (rp[:, :-2] + 2 * rp[:, 1:-1] + rp[:, 2:]) / 4
            rq = np.concatenate([rr[:1], rr, rr[-1:]], 0)
            r = (rq[:-2] + 2 * rq[1:-1] + rq[2:]) / 4
            r[0, :] = r[0, :].mean()
        self.r = r
        P = C + D * r[..., None]
        dA = np.roll(P, -1, 1) - np.roll(P, 1, 1)
        dA[:, 0] = P[:, 1] - P[:, -2]
        dA[:, -1] = P[:, 1] - P[:, -2]
        dP = np.empty_like(P)
        dP[1:-1] = P[2:] - P[:-2]
        dP[0] = P[1] - P[0]
        dP[-1] = P[-1] - P[-2]
        n = np.cross(dP, dA)
        n = unit(n)
        flip = (n * D).sum(-1) < 0
        n[flip] *= -1
        n[0, :] = UP
        self.n = n

    def _interp(self, grid, d):
        az, pol = az_pol(d)
        fa = (np.asarray(az) - self.AZ[0]) / 5.0
        fp = np.clip(np.asarray(pol) / 4.0, 0, len(self.POL) - 1.001)
        ia = np.clip(np.floor(fa).astype(int), 0, len(self.AZ) - 2)
        ip = np.floor(fp).astype(int)
        ua, up = fa - ia, fp - ip
        if grid.ndim == 3:
            ua, up = ua[..., None], up[..., None]
        return ((grid[ip, ia] * (1 - ua) + grid[ip, ia + 1] * ua) * (1 - up)
                + (grid[ip + 1, ia] * (1 - ua) + grid[ip + 1, ia + 1] * ua) * up)

    def surf(self, d, lift=0.0):
        """Points on the skull along the directions d (…, 3), lifted along the skull's normal; -> (P, N)."""
        d = unit(d)
        r = self._interp(self.r, d)
        n = unit(self._interp(self.n, d))
        lift = np.asarray(lift, float)
        return C + d * r[..., None] + n * lift[..., None], n

    def _hairline(self):
        azs = np.arange(-180.0, 180.1, 2.5)
        pols = np.arange(20.0, 156.0, 0.5)
        out = []
        for a in azs:
            P, _ = self.surf(dirv(np.full(len(pols), a), pols))
            below = P[:, 2] <= hairline(P[:, 1])
            out.append(pols[np.argmax(below)] if below.any() else pols[-1])
        out = np.array(out)
        out = 0.5 * (out + out[::-1])
        self._hl_az, self._hl = azs, out

    def hl(self, az):
        az = (np.asarray(az, float) + 180.0) % 360.0 - 180.0
        return np.interp(az, self._hl_az, self._hl)

    def H(self, az, f):
        """Direction at the fraction f from the crown (0) to the hairline (1) on the azimuth az."""
        az = np.asarray(az, float)
        return dirv(az, np.asarray(f, float) * self.hl(az))

    def on(self, az, f, lift=0.0):
        return self.surf(self.H(az, f), lift)

    def f_of(self, P):
        """The crown-to-hairline fraction of the points P (the inverse of H)."""
        az, pol = az_pol(np.asarray(P, float) - C)
        return pol / self.hl(az)

    # -- the whole body
    def nearest(self, P):
        """-> (closest surface points, unit directions away from the body, signed distances (negative inside))."""
        P = np.atleast_2d(np.asarray(P, float))
        L = np.empty_like(P)
        Nn = np.empty_like(P)
        S = np.empty(len(P))
        for i, p in enumerate(P):
            loc, nrm, _idx, dist = self.bvh.find_nearest(tuple(p))
            loc, nrm = np.array(loc), np.array(nrm)
            v = p - loc
            inside = float(v @ nrm) < 0.0
            L[i] = loc
            S[i] = -dist if inside else dist
            Nn[i] = nrm if (inside or dist < 1e-5) else v / dist
        return L, Nn, S

    def push(self, P, margin):
        """Move the points that are inside the body, or nearer than `margin`, out to `margin`."""
        P = np.array(P, float)
        margin = np.broadcast_to(np.asarray(margin, float), (len(P),))
        L, Nn, S = self.nearest(P)
        m = S < margin
        P[m] = L[m] + Nn[m] * margin[m, None]
        return P

    def away(self, P):
        """Unit normals pointing away from the body at the points P."""
        return self.nearest(P)[1]

    def face(self, phi, z):
        """Outermost surface point at the angle phi (0 = front, 90 = the hero's left) and height z, seen from the
        vertical axis through (0, AXIS_Y); -> (point, outward normal) or (None, None)."""
        d = np.array([math.sin(math.radians(phi)), -math.cos(math.radians(phi)), 0.0])
        o = np.array([0.0, AXIS_Y, z]) + d * 0.4
        hit = self.bvh.ray_cast(tuple(o), tuple(-d), 0.4)
        if hit[0] is None:
            return None, None
        n = np.array(hit[1])
        if n @ d < 0:
            n = -n
        return np.array(hit[0]), n

    def front(self, x, z, y0=-0.5):
        """First surface point met coming from the front (+Y ray) at (x, z); -> (point, normal) or (None, None)."""
        hit = self.bvh.ray_cast((x, y0, z), (0.0, 1.0, 0.0), 1.0)
        if hit[0] is None:
            return None, None
        n = np.array(hit[1])
        if n[1] > 0:
            n = -n
        return np.array(hit[0]), n


# ---- the mesh accumulator --------------------------------------------------------------------------------------------

class HairMesh:
    """Vertices, faces and the per-vertex data the game reads: R sway, G clump shade, D the `length` displacement."""

    def __init__(self):
        self.V, self.F, self.R, self.G, self.D = [], [], [], [], []
        self.n = 0

    def add(self, V, F, R=0.0, G=1.0, D=None):
        V = np.asarray(V, float).reshape(-1, 3)
        k = len(V)
        self.V.append(V)
        self.R.append(np.broadcast_to(np.asarray(R, float), (k,)).copy())
        self.G.append(np.broadcast_to(np.asarray(G, float), (k,)).copy())
        self.D.append(np.zeros((k, 3)) if D is None else np.broadcast_to(np.asarray(D, float), (k, 3)).copy())
        self.F.extend(tuple(int(i) + self.n for i in f) for f in F)
        self.n += k
        return self

    def arrays(self):
        return (np.vstack(self.V), self.F, np.clip(np.concatenate(self.R), 0, 1),
                np.clip(np.concatenate(self.G), 0.35, 1.0), np.vstack(self.D))

    def tris(self):
        return sum(len(f) - 2 for f in self.F)

    def mirror(self, start):
        """Append the mirror image (x -> -x) of everything added since vertex index `start` (face list position is
        found from the vertex ids)."""
        V = np.vstack(self.V)
        R, G, D = np.concatenate(self.R), np.concatenate(self.G), np.vstack(self.D)
        F = [f for f in self.F if min(f) >= start]
        Vm, Dm = V[start:].copy(), D[start:].copy()
        Vm[:, 0] *= -1
        Dm[:, 0] *= -1
        Fm = [tuple(i - start for i in reversed(f)) for f in F]
        return self.add(Vm, Fm, R[start:], G[start:], Dm)


# ---- geometry --------------------------------------------------------------------------------------------------------

def _ngon(n, start=180.0):
    a = np.radians(start - np.arange(n) * 360.0 / n)
    return np.stack([np.cos(a), np.sin(a)], 1)


SECT = {
    # (profile as (across, up) in units of (w, h), closed)
    "roof": (np.array([(-1, 0), (0, 1), (1, 0)], float), False),
    "tri": (np.array([(-1, 0), (0, 1), (1, 0)], float), True),
    "diamond": (np.array([(-1, 0), (0, 1), (1, 0), (0, -0.45)], float), True),
    "blade": (np.array([(-1, 0), (0, 1), (1, 0), (0, -1)], float), True),
    "fat": (np.array([(-1, 0), (-0.72, 0.72), (0, 1), (0.72, 0.72), (1, 0), (0, -0.35)], float), True),
    "band": (np.array([(-1, 0), (-0.5, 0.85), (0.5, 0.85), (1, 0)], float), True),
    "band_open": (np.array([(-1, 0), (-0.5, 0.85), (0.5, 0.85), (1, 0)], float), False),
    "lens": (np.array([(-1, 0), (-0.45, 0.9), (0.45, 0.9), (1, 0), (0, -0.4)], float), True),
    "round5": (_ngon(5), True),
    "round6": (_ngon(6), True),
    "round8": (_ngon(8), True),
}


def lock(m, P, N, w, h, sect="tri", tip="point", root="open", sway=(0.0, 1.0), G=1.0, grow=None, gw=0.0, t=None,
         roll=None, D=None, R=None, ride=None):
    """Sweep a section along the strand P (k, 3) with up vectors N (k, 3).

    w, h     half width / height: a constant, knots for pw(), or (k,) arrays
    tip      "point" (the last ring is one vertex), "cap" (flat fan) or "open"
    sway     (t_free, max[, base]): R = base below t_free, rising smoothly to max at the tip
    grow     (vector, t0[, power]): the `length` displacement, 0 up to t0 then growing to the vector at the tip
    gw       extra scale of the section at length 1 (0 = the lock keeps its girth), times the same ramp (with an
             explicit D: on every ring)
    roll     (k,) rotation of the section about the tangent, radians
    ride     (k, 3) displacement added to every ring (a lock riding on a shell that thickens with `length`)
    """
    P = np.asarray(P, float)
    k = len(P)
    t = arc_t(P) if t is None else np.asarray(t, float)
    prof, closed = SECT[sect]
    n = len(prof)
    T = tangents(P)
    Nn = perp(T, N)
    S = unit(np.cross(T, Nn))
    if roll is not None:
        c, s = np.cos(roll)[:, None], np.sin(roll)[:, None]
        S, Nn = S * c + Nn * s, Nn * c - S * s
    w = pw(w, t) if not (isinstance(w, np.ndarray) and w.shape == (k,)) else w
    h = pw(h, t) if not (isinstance(h, np.ndarray) and h.shape == (k,)) else h
    if R is None:
        base = sway[2] if len(sway) > 2 else 0.0
        R = base + (sway[1] - base) * sstep(sway[0], 1.0, t)
    ramp = np.zeros(k)
    if D is None:
        D = np.zeros((k, 3))
        if grow is not None:
            t0 = grow[1]
            p = grow[2] if len(grow) > 2 else 1.0
            ramp = np.clip((t - t0) / max(1 - t0, 1e-6), 0, 1) ** p
            D = ramp[:, None] * np.asarray(grow[0], float)
    else:
        D = np.asarray(D, float)
        ramp = np.ones(k)
    if ride is not None:
        D = D + np.asarray(ride, float)
    rings = k - 1 if tip == "point" else k
    off = (S[:rings, None, :] * (prof[None, :, 0:1] * w[:rings, None, None])
           + Nn[:rings, None, :] * (prof[None, :, 1:2] * h[:rings, None, None]))
    V = (P[:rings, None, :] + off).reshape(-1, 3)
    Dv = (D[:rings, None, :] + off * (gw * ramp[:rings])[:, None, None]).reshape(-1, 3)
    Rv = np.repeat(R[:rings], n)
    F = []
    m_ = n if closed else n - 1
    for i in range(rings - 1):
        a0, b0 = i * n, (i + 1) * n
        for j in range(m_):
            j2 = (j + 1) % n
            F.append((a0 + j, a0 + j2, b0 + j2, b0 + j))
    Vl, Dl, Rl = [V], [Dv], [Rv]
    nv = len(V)
    if tip == "point":
        Vl.append(P[-1:])
        Dl.append(D[-1:])
        Rl.append(R[-1:])
        a0 = (rings - 1) * n
        for j in range(m_):
            F.append((a0 + j, a0 + (j + 1) % n, nv))
        nv += 1
    elif tip == "cap" and closed:
        a0 = (rings - 1) * n
        Vl.append(V[a0:a0 + n].mean(0)[None])
        Dl.append(Dv[a0:a0 + n].mean(0)[None])
        Rl.append(R[-1:])
        for j in range(n):
            F.append((a0 + j, a0 + (j + 1) % n, nv))
        nv += 1
    if root == "cap" and closed:
        Vl.append(V[:n].mean(0)[None])
        Dl.append(Dv[:n].mean(0)[None])
        Rl.append(R[:1])
        for j in range(n):
            F.append((nv, (j + 1) % n, j))
        nv += 1
    m.add(np.vstack(Vl), F, np.concatenate(Rl), G, np.vstack(Dl))


def grid(m, V, Nref, closed_u=False, R=0.0, G=1.0, D=None):
    """A sheet from a (U, K, 3) vertex grid; the winding is chosen so the faces look along Nref (U, K, 3).
    R, G: scalars or (U, K); D: (U, K, 3)."""
    V = np.asarray(V, float)
    U, K = V.shape[:2]
    F = []
    cu = U if closed_u else U - 1
    for u in range(cu):
        u2 = (u + 1) % U
        for v in range(K - 1):
            F.append((u * K + v, u * K + v + 1, u2 * K + v + 1, u2 * K + v))
    flat = V.reshape(-1, 3)
    s = 0.0
    nr = np.broadcast_to(np.asarray(Nref, float), V.shape).reshape(-1, 3)
    for f in F:
        a, b, c, d = (flat[i] for i in f)
        s += float(np.cross(c - a, d - b) @ nr[f[0]])
    if s < 0:
        F = [tuple(reversed(f)) for f in F]
    # drop the quads that collapsed (poles, tucked corners)
    out = []
    for f in F:
        ids = []
        for i in f:
            if not any(np.allclose(flat[i], flat[j], atol=1e-7) for j in ids):
                ids.append(i)
        if len(ids) >= 3:
            out.append(tuple(ids))
    Rg = np.broadcast_to(np.asarray(R, float), (U, K)).reshape(-1)
    Gg = np.broadcast_to(np.asarray(G, float), (U, K)).reshape(-1)
    Dg = None if D is None else np.asarray(D, float).reshape(-1, 3)
    m.add(flat, out, Rg, Gg, Dg)


def cap(m, head, thick=0.006, n_az=24, fs=(0.16, 0.36, 0.58, 0.78, 0.93), f_edge=1.0, tuck=-0.003, G=0.45,
        g_jit=0.05, grow=0.0, ridge=0.0, rng=None, rim=0.45):
    """The scalp shell: skull + thick(az, f) from the crown to the hairline, thinning to `rim` of its thickness at
    the edge, the rim itself tucked into the skin.  thick, f_edge, grow may be constants or callables of arrays
    (az, f) / (az); `grow` is how much thicker it gets at length 1 (locks laid on it ride along: lock(ride=...))."""
    rng = rng or np.random.default_rng(1)
    azs = np.linspace(-180, 180, n_az, endpoint=False)
    th = thick if callable(thick) else (lambda a, f: np.full(np.shape(a), float(thick)))
    fe = f_edge if callable(f_edge) else (lambda a: np.full(np.shape(a), float(f_edge)))
    gr = grow if callable(grow) else (lambda a, f: np.full(np.shape(a), float(grow)))
    alt = 1.0 + ridge * np.where(np.arange(n_az) % 2 == 0, 1.0, -1.0)
    rows_f = [0.0] + list(fs) + [1.0]
    K = len(rows_f)
    V = np.zeros((n_az, K, 3))
    Nr = np.zeros((n_az, K, 3))
    D = np.zeros((n_az, K, 3))
    e = fe(azs)
    for r, f in enumerate(rows_f):
        last = r == K - 1
        ff = np.full(n_az, f) * e
        taper = 1.0 - (1.0 - rim) * float(sstep(0.62, 1.0, f))
        lift = np.full(n_az, tuck) if last else th(azs, np.full(n_az, f)) * (alt if 0 < r else 1.0) * taper
        P, N = head.on(azs, ff, lift)
        V[:, r], Nr[:, r] = P, N
        if not last:
            D[:, r] = N * (np.asarray(gr(azs, np.full(n_az, f))) * taper)[:, None]
    V[:, 0] = V[:, 0].mean(0)
    D[:, 0] = D[:, 0].mean(0)
    Gc = np.repeat(np.clip(G + g_jit * rng.uniform(-1, 1, n_az), 0.35, 1.0)[:, None], K, 1)
    grid(m, V, Nr, closed_u=True, R=0.0, G=Gc, D=D)


def blob(m, c, r, axis, n=6, G=1.0, R=0.0, D=None, squash=0.8, grow_r=0.0, dome=True):
    """A low dome (or a whole blob) of radius r centred at c with its pole along `axis`: a curl / a bun lobe.
    D: the displacement of the centre at length 1; grow_r: the growth of the radius at length 1."""
    axis = unit(axis)
    a = unit(np.cross(axis, (0.31, 0.57, 0.76)))
    b = np.cross(axis, a)
    ang = np.arange(n) * 2 * math.pi / n
    ring = np.cos(ang)[:, None] * a + np.sin(ang)[:, None] * b
    levels = [(0.97, 0.05), (0.66, 0.70)] if dome else [(0.70, -0.66), (1.0, 0.0), (0.70, 0.66)]
    V, F = [], []
    for li, (rr, hh) in enumerate(levels):
        V.append(ring * rr + axis * hh * squash)
    V.append((axis * squash)[None])
    V = np.vstack(V)
    L = len(levels)
    for li in range(L - 1):
        for j in range(n):
            j2 = (j + 1) % n
            F.append((li * n + j, li * n + j2, (li + 1) * n + j2, (li + 1) * n + j))
    top = L * n
    for j in range(n):
        F.append(((L - 1) * n + j, (L - 1) * n + (j + 1) % n, top))
    if not dome:
        V = np.vstack([V, (-axis * squash)[None]])
        for j in range(n):
            F.append((top + 1, (j + 1) % n, j))
    D0 = np.zeros(3) if D is None else np.asarray(D, float)
    m.add(np.asarray(c, float) + V * r, F, R, G, D0 + V * grow_r)
