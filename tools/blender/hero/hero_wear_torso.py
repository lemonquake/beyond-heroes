"""bh-023: worn armour and inner garments (slots `armor`, `inner_garment`).

Each entry mirrors its item model's spec (tools/blender/items/item_gear.py GEAR, depth_specs.json) so the worn piece
is recognisably the thing in the icon: same kind, same palette keys, same trims.

Layers (offsets from the skin): inner garments 5-9 mm, armour cloth 10-16 mm, plates beyond. bh-024: the legs are the
Leggings slot's (hero_wear_legs.py): body garments stop at the hips, and their hems stand at least 6.5 mm out so the
leggings, tucked in at 3.5 mm, close under them. `skirt=` tells the game how low a skirt, tail or robe hangs. Inner
garments are only body-cut cloth and thin trims (nothing flares), so any armour covers them; they show at the neck and
the wrists.

How the pieces are made:
  cloth()      the body's own surface pushed out (hero_wear_kit.shell) and then relaxed like a membrane stretched
               over the body: it bridges the grooves between muscles instead of following them.
  TRUNK/ARM/LEG/NECK .ring()   convex cross-sections of the body — or of a cloth layer already made — so belts,
               hems, plates and skirts are lofted at a known distance outside what they sit on.
  loft()/skirt()/panel()/dome()  authored parts from those rings, skinned by hero_wear_kit.attach().
"""
import math

import numpy as np

import boss_regalia as R
import hero_wear_ends as E
import hero_wear_kit as WK
from hero_wear_kit import K, M, item, pal, shell, attach
from bh_math import Rx, Ry, Rz  # noqa: F401


# ====================================================================================================================
# cloth cut from the body
# ====================================================================================================================
def region(trunk=None, arms=None, legs=None, vest=None, sleeves=None, notch=None):
    """A region field: trunk=(z0, z1), arms=(x0, x1), legs=(z0, z1); vest=(z0, z1, xcut) is a sleeveless trunk cut
    on a vertical plane through the shoulder, sleeves=(xcut, x1) the arms beyond it; notch=(z_v, half width at the
    top) opens a V at the front of the neck."""
    def f(V):
        fs = []
        ax = np.abs(V[:, 0])
        if trunk:
            fs.append(WK.trunk(V, *trunk))
        if arms:
            fs.append(WK.arms(V, *arms))
        if legs:
            fs.append(WK.legs(V, *legs))
        if vest:
            fs.append(np.minimum.reduce([V[:, 2] - vest[0], vest[1] - V[:, 2], vest[2] - ax]))
        if sleeves:
            fs.append(np.minimum.reduce([ax - sleeves[0], sleeves[1] - ax, V[:, 2] - 1.25]))
        out = np.maximum.reduce(fs)
        if notch:
            zv, hw = notch
            slope = (1.545 - zv) / hw
            cut = np.minimum((V[:, 2] - (zv + slope * ax)) * 0.6, -V[:, 1] - 0.03)
            out = np.minimum(out, -cut)
        return out
    return f


def cloth(select, offset=0.012, mat="hw_wool", name="cloth", relax=8, rim=True, sink=0.004):
    """Cloth cut from the body inside the region `select` and stretched over it: each vertex may only rise along
    its normal, and rises to the average of its neighbours, so the cloth spans the hollows (abdominal muscles, the
    spine, between the shoulder blades) and lies on the ridges. The cut edges stay on the body, `offset` metres out
    (a number or a function of the cloth's vertices)."""
    p0 = shell(select, 0.0, mat, name, rim=False)
    p1 = shell(select, 1.0, mat, name, rim=False)
    base, N = p0.V, p1.V - p0.V
    T = np.array(p0.F, int)
    n = len(base)
    E = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    uniq, counts = np.unique(E, axis=0, return_counts=True)
    bnd = np.zeros(n, bool)
    bnd[uniq[counts == 1].ravel()] = True
    i, j = uniq[:, 0], uniq[:, 1]
    deg = np.maximum(np.bincount(np.r_[i, j], minlength=n), 1)[:, None]

    def avg(A):
        S = np.zeros_like(A)
        np.add.at(S, i, A[j])
        np.add.at(S, j, A[i])
        return S / deg
    h = np.zeros(n)
    for _ in range(relax):
        P = base + N * h[:, None]
        h = np.maximum(((0.5 * P + 0.5 * avg(P) - base) * N).sum(1), 0.0)
        h[bnd] = 0.0
    off = offset(base) if callable(offset) else np.full(n, float(offset))
    V = base + N * (h + off)[:, None]
    F = [tuple(f) for f in p0.F]
    W, D = p0.W, p0.D
    if rim:
        single = {(int(a), int(b)) for a, b in uniq[counts == 1]}
        inner = {}
        Vl, Wl = list(V), list(W)
        Dl = [list(D[k]) for k in range(D.shape[0])]
        for fc in list(F):
            for a_, c_ in ((fc[0], fc[1]), (fc[1], fc[2]), (fc[2], fc[0])):
                if (min(a_, c_), max(a_, c_)) not in single:
                    continue
                for v in (a_, c_):
                    if v not in inner:
                        inner[v] = len(Vl)
                        Vl.append(base[v] - N[v] * sink)
                        Wl.append(W[v])
                        for k in range(D.shape[0]):
                            Dl[k].append(D[k, v])
                F.append((c_, a_, inner[a_], inner[c_]))
        V, W, D = np.array(Vl), np.array(Wl), np.array(Dl)
    return WK.WPart(V, F, mat, W, D, name)


# ====================================================================================================================
# cross-sections
# ====================================================================================================================
class Surf:
    """A surface to measure: the body, or cloth parts already made."""

    def __init__(self, V, F):
        self.V = np.asarray(V, float)
        e = set()
        for f in F:
            k = len(f)
            for q in range(k):
                a, b = int(f[q]), int(f[(q + 1) % k])
                e.add((a, b) if a < b else (b, a))
        self.E = np.array(sorted(e), int)
        self._cache = {}

    def section(self, axis, value):
        key = (axis, round(float(value), 5))
        if key not in self._cache:
            d = self.V[:, axis] - value
            a, b = self.E[:, 0], self.E[:, 1]
            m = d[a] * d[b] < 0
            t = d[a][m] / (d[a][m] - d[b][m])
            self._cache[key] = self.V[a[m]] + (self.V[b[m]] - self.V[a[m]]) * t[:, None]
        return self._cache[key]


_BODY_SURF = None


def body_surf():
    global _BODY_SURF
    if _BODY_SURF is None:
        b = WK.body()
        _BODY_SURF = Surf(b.V, b.T)
    return _BODY_SURF


def surf(parts):
    """The surface of some parts (WParts or bh_mesh Parts), to fit other parts around."""
    if not isinstance(parts, (list, tuple)):
        parts = [parts]
    Vs, Fs, off = [], [], 0
    for p in parts:
        Vs.append(np.asarray(p.V, float))
        Fs += [tuple(q + off for q in f) for f in p.F]
        off += len(p.V)
    return Surf(np.vstack(Vs), Fs)


def _hull2(P):
    P = np.unique(np.round(P, 6), axis=0)
    P = P[np.lexsort((P[:, 1], P[:, 0]))]

    def half(pts):
        h = []
        for p in pts:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h
    lo, up = half(P), half(P[::-1])
    return np.array(lo[:-1] + up[:-1])


def _ray(H, c, ang):
    """Distance from c to the convex polygon H along each angle (0 where the ray misses)."""
    d = np.stack([np.cos(ang), np.sin(ang)], 1)
    p = H - np.asarray(c, float)
    e = np.roll(p, -1, 0) - p
    den = d[:, None, 0] * e[None, :, 1] - d[:, None, 1] * e[None, :, 0]
    pe = p[:, 0] * e[:, 1] - p[:, 1] * e[:, 0]
    pd = p[None, :, 0] * d[:, None, 1] - p[None, :, 1] * d[:, None, 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        t = pe[None] / den
        s = pd / den
    ok = (np.abs(den) > 1e-12) & (s >= -1e-9) & (s <= 1 + 1e-9) & (t > 0)
    r = np.where(ok, t, -np.inf).max(1)
    return np.where(np.isfinite(r), r, 0.0)


def _angles(n, a0=0.0, a1=360.0):
    full = abs(a1 - a0) >= 359.9
    return np.radians(np.linspace(a0, a1, n, endpoint=not full))


class Frame:
    """Sections across one axis. Angles: for vertical frames 0 = the hero's left (+X), 90 = back, 270 = front (as
    boss_regalia.srow); for the arm 0 = front, 90 = top, 180 = back (as boss_regalia.arm_tube)."""

    def __init__(self, axis, keep, centre=None, axis_xy=None):
        self.axis, self.keep, self.centre = axis, keep, centre
        self.axis_xy = axis_xy if axis_xy is not None else centre

    def hull(self, t, src=None, lim=None):
        P = (src or body_surf()).section(self.axis, t)
        P = P[self.keep(P, t, lim)]
        if len(P) < 3:
            P = body_surf().section(self.axis, t)
            P = P[self.keep(P, t, lim)]
        P2 = np.stack([-P[:, 1], P[:, 2]], 1) if self.axis == 0 else P[:, :2]
        H = _hull2(P2)
        c = self.centre if self.centre is not None else (H.min(0) + H.max(0)) / 2
        return H, np.asarray(c, float)

    def prof(self, t, n=32, grow=0.0, src=None, a0=0.0, a1=360.0, lim=None):
        """-> (radii of the convex section at `t`, its centre)."""
        H, c = self.hull(t, src, lim)
        r = _ray(H, c, _angles(n, a0, a1))
        return np.where(r > 0, r + grow, 0.0), c

    def pts(self, t, r, c, a0=0.0, a1=360.0):
        a = _angles(len(r), a0, a1)
        if self.axis == 0:
            return np.stack([np.full(len(r), float(t)), -(c[0] + r * np.cos(a)), c[1] + r * np.sin(a)], 1)
        return np.stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a), np.full(len(r), float(t))], 1)

    def ring(self, t, n=32, grow=0.0, src=None, a0=0.0, a1=360.0, lim=None):
        r, c = self.prof(t, n, grow, src, a0, a1, lim)
        return self.pts(t, r, c, a0, a1)

    def ref(self, c):
        """The point of the axis nearest to c (to tell inside from outside)."""
        if self.axis == 0:
            return np.array([c[0], 0.0, 1.44])
        return np.array([self.axis_xy[0], self.axis_xy[1], c[2]])


AX = (0.0, -0.02)
TRUNK = Frame(2, lambda P, z, lim: np.abs(P[:, 0]) < (lim or (0.215 if z <= 1.36 else 0.19)), AX)
HIPS = Frame(2, lambda P, z, lim: np.abs(P[:, 0]) < (lim or 0.27), AX)             # trunk and both legs: skirts
NECK = Frame(2, lambda P, z, lim: np.abs(P[:, 0]) < (lim or 0.11), axis_xy=(0.0, -0.03))
LEG = Frame(2, lambda P, z, lim: (P[:, 0] > 0.004) & (P[:, 0] < 0.27), axis_xy=(0.105, 0.02))    # the left leg
ARM = Frame(0, lambda P, x, lim: P[:, 2] > (1.25 if x > 0.235 else 1.37))          # the left arm


def front_y(z, x, src=None, back=False, frame=HIPS, lim=None):
    """y of the front (or back) of the convex section at height z, at lateral position x."""
    H, _ = frame.hull(z, src, lim)
    q = np.roll(H, -1, 0)
    ys = []
    for a, b in zip(H, q):
        if (a[0] - x) * (b[0] - x) <= 0 and abs(b[0] - a[0]) > 1e-9:
            ys.append(a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
    if not ys:
        k = np.argmin(np.abs(H[:, 0] - x))
        return float(H[k, 1])
    return float(max(ys) if back else min(ys))


# ====================================================================================================================
# authored parts
# ====================================================================================================================
def _outward(part, frame):
    s = 0.0
    V = part.V
    for f in part.F:
        p = V[list(f)]
        c = p.mean(0)
        s += float(np.cross(p[1] - p[0], p[2] - p[0]) @ (c - frame.ref(c)))
    if s < 0:
        part.flip()
    return part


def _inset(ring, d):
    c = ring.mean(0)
    v = c - ring
    return ring + v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9) * d


def loft(rings, mat, frame=TRUNK, closed=True, lip0=0.0, lip1=0.0, thick=0.0, name="loft"):
    """A surface through the rings, facing away from the frame's axis. lip0 / lip1 fold the first / last edge inward
    by that much (the thickness one sees at a hem); `thick` instead makes a real two-sided sheet."""
    rings = [np.asarray(r, float) for r in rings]
    if lip0:
        rings = [_inset(rings[0], lip0)] + rings
    if lip1:
        rings = rings + [_inset(rings[-1], lip1)]
    V, F = M.loft(rings, cap0=False, cap1=False, closed=closed)
    p = _outward(M.Part(V, F, mat, name=name), frame)
    if thick > 0:
        p = M.solidify(p, thick, offset=1.0)
    return p


def hoop(z, width, mat, src=None, grow=0.002, n=24, frame=TRUNK, lip=0.0, a0=0.0, a1=360.0, lim=None):
    """A band around the frame's axis, `width` wide, centred at z (or x, for the arm), `grow` outside `src`."""
    closed = abs(a1 - a0) >= 359.9
    rings = [frame.ring(z + s * width / 2, n, grow, src, a0, a1, lim) for s in (-1, 1)]
    return loft(rings, mat, frame, closed, lip, lip, name="hoop")


def cord(points, r, mat, sides=4, closed=False, up=(0, 0, 1)):
    pts = [tuple(p) for p in points]
    if closed:
        pts = pts + [pts[0]]
    return K.tube(pts, [r] * len(pts), mat, n=sides, up=up, cap=not closed, name="cord")


def studs(points, centre_of, r, mat, h=0.7):
    """Low four-sided rivet heads at the points, facing away from centre_of(p)."""
    V, F = [], []
    for p in points:
        p = np.asarray(p, float)
        nrm = p - np.asarray(centre_of(p), float)
        nrm /= max(np.linalg.norm(nrm), 1e-9)
        a = np.cross(nrm, (0.0, 0.0, 1.0))
        if np.linalg.norm(a) < 1e-6:
            a = np.cross(nrm, (1.0, 0.0, 0.0))
        a /= np.linalg.norm(a)
        b = np.cross(nrm, a)
        o = len(V)
        q = p - nrm * r * 0.25
        V += [q + nrm * r * (h + 0.25), q + a * r, q + b * r, q - a * r, q - b * r]
        F += [(o, o + 1, o + 2), (o, o + 2, o + 3), (o, o + 3, o + 4), (o, o + 4, o + 1)]
    return M.Part(np.array(V), F, mat, name="studs")


def ring_studs(z, count, r, mat, src=None, grow=0.001, frame=TRUNK, a0=0.0, a1=360.0, lim=None):
    """A row of rivets around the frame's axis."""
    pts = frame.ring(z, count, grow, src, a0, a1, lim)
    return studs(pts, frame.ref, r, mat)


def dome(centre, radii, mat, n=10, rings=4, span=100.0, tilt=0.0, lip=0.006, name="dome"):
    """The cap of an ellipsoid (pole up, down to `span` degrees from it), leaned `tilt` degrees toward +X."""
    V, F = [(0.0, 0.0, 1.0)], []
    for q in range(1, rings + 1):
        ph = math.radians(span * q / rings)
        for a in np.linspace(0, 2 * math.pi, n, endpoint=False):
            V.append((math.sin(ph) * math.cos(a), math.sin(ph) * math.sin(a), math.cos(ph)))
    if lip:
        ph = math.radians(span)
        k = 1.0 - lip / max(radii[0], 1e-6)
        for a in np.linspace(0, 2 * math.pi, n, endpoint=False):
            V.append((math.sin(ph) * math.cos(a) * k, math.sin(ph) * math.sin(a) * k, math.cos(ph)))
    for q in range(n):
        F.append((0, 1 + q, 1 + (q + 1) % n))
    rows = rings + (1 if lip else 0)
    for q in range(rows - 1):
        a0, b0 = 1 + q * n, 1 + (q + 1) * n
        for s in range(n):
            t = (s + 1) % n
            F.append((a0 + s, b0 + s, b0 + t, a0 + t))
    p = M.Part(np.array(V) * np.asarray(radii, float), F, mat, name=name)
    p.rot(Ry(tilt))
    p.move(centre)
    return p


def panel(x0, x1, z0, z1, mat, src=None, grow=0.004, nu=5, nv=5, flare=0.0, hem="flat", back=False, thick=0.005,
          grow1=None, frame=HIPS, name="panel"):
    """A hanging panel lying on the front (or back) of `src` (default: the body) from z0 down to z1: tassets,
    tabards, coat fronts. `flare` widens it toward the hem, grow1 lifts the hem further off the surface."""
    g1 = grow if grow1 is None else grow1
    sgn = 1.0 if back else -1.0

    def fn(u, v):
        xm = (x0 + x1) / 2
        x = xm + (x0 + (x1 - x0) * u - xm) * (1 + flare * v)
        z = z0 + (z1 - z0) * v
        y = front_y(z, x, src, back, frame) + sgn * (grow + (g1 - grow) * v)
        if hem == "point":
            z -= (z0 - z1) * 0.16 * (1 - abs(2 * u - 1)) * v ** 4
        elif hem == "round":
            z -= (z0 - z1) * 0.1 * (1 - (2 * u - 1) ** 2) * v ** 4
        return (x, y, z)
    V, F = M.grid(fn, nu, nv)
    p = M.Part(V, F, mat, name=name)
    V3 = p.V[list(p.F[0])]
    if float(np.cross(V3[1] - V3[0], V3[2] - V3[0])[1]) * sgn < 0:
        p.flip()
    if thick > 0:
        p = M.solidify(p, thick, offset=1.0)
    return p


def skirt(z_top, z_bot, mat, top_src=None, grow=(0.004, 0.03), n=28, steps=5, flare=0.0, pleats=0, pleat=0.0,
          thick=0.006, a0=0.0, a1=360.0, hem_lip=0.0, name="skirt"):
    """One tube hanging from the hips (mail skirts, coat tails, robes). The top ring lies grow[0] outside `top_src`
    (the cloth it hangs over); further down it stays grow[1] clear of the body and never narrows; `flare` widens it
    toward the hem and `pleats` folds of depth `pleat` open toward the hem."""
    rings, prev = [], None
    a = _angles(n, a0, a1)
    for q in range(steps + 1):
        t = q / steps
        z = z_top + (z_bot - z_top) * t
        if q == 0:
            r, _ = HIPS.prof(z, n, grow[0], top_src, a0, a1)
        else:
            rb, _ = HIPS.prof(z, n, grow[0] + (grow[1] - grow[0]) * min(1.0, t * 2.5), None, a0, a1)
            r = np.maximum(rb, prev + flare / steps)
        prev = r
        rr = r * (1.0 + pleat * t * np.cos(pleats * a)) if pleats else r
        rings.append(HIPS.pts(z, rr, np.asarray(AX), a0, a1))
    closed = abs(a1 - a0) >= 359.9
    return loft(rings, mat, HIPS, closed, 0.0, hem_lip, thick, name)


def sleeve(xs, grows, mat, src=None, n=14, lip1=0.0, thick=0.0, drop=None, name="sleeve"):
    """A sleeve around the left arm through the stations xs, `grows` outside `src` at each; drop=[dz...] lets the
    sleeve hang below the arm (the T-pose's down)."""
    rings = []
    for q, (x, g) in enumerate(zip(xs, grows)):
        r, c = ARM.prof(x, n, g, src)
        if drop:
            c = c + np.array([0.0, -drop[q]])
        rings.append(ARM.pts(x, r, c))
    return loft(rings, mat, ARM, True, 0.0, lip1, thick, name)


def collar(z0, z1, mat, grow=0.012, n=18, flare=0.004, lip=0.008):
    """A standing collar around the neck."""
    return loft([NECK.ring(z0, n, grow + flare), NECK.ring(z1, n, grow)], mat, NECK, True, 0.0, lip, name="collar")


def buckle(z, mat, src=None, grow=0.006, w=0.046, h=0.05, x=0.0):
    y = front_y(z, x, src) - grow
    return [K.box(w, 0.012, h, (x, y, z), mat), K.box(w * 0.5, 0.016, h * 0.5, (x, y - 0.002, z), mat)]


def belt(z0, z1, mat, src=None, grow=0.005, n=28, clasp=None, frame=TRUNK):
    """A strap round the waist over `src`, with a buckle of palette key `clasp`."""
    rings = [frame.ring(z, n, grow, src) for z in (z0, z1)]
    parts = [loft(rings, mat, frame, True, 0.008, 0.008, name="belt")]
    if clasp:
        parts += buckle((z0 + z1) / 2, clasp, src, grow + 0.004, h=(z1 - z0) * 1.15)
    return parts


def vband(x, z0, z1, width, mat, src=None, grow=0.002, steps=6, back=False, frame=HIPS):
    """A vertical band lying on the front (or back) of `src` (plackets, the trim down a robe's front)."""
    return panel(x - width / 2, x + width / 2, z1, z0, mat, src, grow, nu=2, nv=steps + 1, back=back, thick=0.0,
                 frame=frame, name="vband")


SKW = dict(z_top=1.0, z_knee=0.51, z_bot=0.12, centre=0.09, leg=0.9)


def skw(**kw):
    d = dict(SKW)
    d.update(kw)
    return WK.skirt_weights(**d)


def rigid_mix(parts, bones, keys=True):
    """Skin parts to a fixed blend of bones (elbow and knee cops: half of each side of the joint)."""
    out = attach(parts, bone=bones[0][0], keys=keys)
    for p in out:
        p.W[:] = 0.0
        for b, w in bones:
            p.W[:, WK.BONES.index(b)] = w
    return out


# ====================================================================================================================
# helpers
# ====================================================================================================================
def hem_off(base, z_hem, extra=0.003, band=0.08):
    """`base` all over, standing `extra` further out over the last `band` metres above the hem (z_hem)."""
    def f(V):
        return base + extra * (1.0 - WK.step(z_hem, z_hem + band, V[:, 2]))
    return f


def edge_cords(raw, mat, r=0.004, n=40, pick=None):
    """Trim cords along the open edges of an un-rimmed cloth (hems, armholes, necklines): `pick(P)` keeps a loop."""
    out = []
    for lp in E.border_loops(raw):
        P = raw.V[lp]
        if len(lp) < 6 or (pick is not None and not pick(P)):
            continue
        out.append(E.cord_on(raw, lp, r, mat, n=n, name="edge"))
    return out


def bell(x0, x1, grow0, grow1, mat, src=None, drop1=0.03, n=16, trim=None, name="bell"):
    """A sleeve opening out into a bell from x0 to the cuff at x1 (the T-pose's down is the sleeve's hang)."""
    xs = np.linspace(x0, x1, 5)
    t = np.linspace(0.0, 1.0, 5)
    grows = list(grow0 + (grow1 - grow0) * t ** 1.6)
    drops = list(drop1 * t ** 1.8)
    parts = [sleeve(list(xs), grows, mat, src, n=n, lip1=0.006, drop=drops, name=name)]
    if trim:
        r, c = ARM.prof(x1, n, grows[-1] + 0.001, src)
        c = c + np.array([0.0, -drops[-1]])
        P = ARM.pts(x1, r, c)
        parts.append(cord(P, 0.0045, trim, sides=4, closed=True))
    return attach(parts, bones=["upper_arm.L", "forearm.L"], k=8)


def pauldron(mat, trim, big=True):
    """The left pauldron: a dome over the shoulder and two lames down the upper arm."""
    r = (0.095, 0.088, 0.07) if big else (0.082, 0.078, 0.06)
    parts = [dome((0.215, -0.004, 1.448), r, mat, n=14, rings=4, span=96.0, tilt=38.0, lip=0.006, name="pauldron")]
    parts.append(dome((0.215, -0.004, 1.448), (r[0] + 0.004, r[1] + 0.004, r[2] * 0.25), trim, n=14, rings=1, span=96.0, tilt=38.0,
                      lip=0.0, name="pauldron_rim"))
    for i, x in enumerate((0.30, 0.345)):
        rr, c = ARM.prof(x, 14, 0.024 - 0.004 * i)
        parts.append(loft([ARM.pts(x - 0.024, rr * 1.02, c), ARM.pts(x + 0.024, rr * 0.98, c)], mat, ARM, True, 0.004, 0.004, name="lame"))
    return rigid_mix(parts, [("upper_arm.L", 0.8), ("shoulder.L", 0.2)])


# ====================================================================================================================
# inner garments (5-9 mm)
# ====================================================================================================================
@item("padded_gambeson", hide={"z": [0.875, 1.49], "sleeve": [0.23, 0.69]})
def padded_gambeson():
    wool, linen = pal("wool"), pal("linen")
    jacket = cloth(region(trunk=(0.85, 1.535), arms=(0.19, 0.715)), hem_off(0.008, 0.85), wool, "jacket", relax=5)
    S = surf(jacket)
    body = [hoop(z, 0.012, linen, S, 0.0015, 22) for z in (0.95, 1.04, 1.13, 1.22, 1.31)]      # quilting rows
    body += [hoop(0.868, 0.03, linen, S, 0.002, 24), collar(1.505, 1.56, linen, 0.009)]
    body.append(vband(0.0, 0.88, 1.50, 0.022, linen, S, 0.0025, 7, frame=TRUNK))
    arm = [hoop(x, 0.012, linen, S, 0.0015, 10, ARM) for x in (0.31, 0.40, 0.53, 0.62)]
    arm.append(hoop(0.70, 0.028, linen, S, 0.002, 10, ARM))
    return [jacket] + attach(body, k=8) + WK.both(attach(arm, bones=["upper_arm.L", "forearm.L"], k=8))


@item("silk_undershirt", hide={"z": [0.885, 1.49], "sleeve": [0.23, 0.71]})
def silk_undershirt():
    silk, white = pal("silk"), pal("white")
    shirt = cloth(region(trunk=(0.86, 1.535), arms=(0.19, 0.735), notch=(1.46, 0.05)), hem_off(0.0058, 0.86, 0.0022), silk, "shirt", relax=5)
    raw = cloth(region(trunk=(0.86, 1.535), arms=(0.19, 0.735), notch=(1.46, 0.05)), hem_off(0.0058, 0.86, 0.0022), silk, "shirt",
                relax=5, rim=False)
    S = surf(shirt)
    trims = edge_cords(raw, white, 0.0028, 44, pick=lambda P: P[:, 2].mean() > 1.3 and np.abs(P[:, 0]).max() < 0.2)
    trims += attach([hoop(0.872, 0.014, white, S, 0.0015, 26)], k=8)
    cuff = hoop(0.722, 0.022, white, S, 0.0015, 12, ARM)
    return [shirt] + trims + WK.both(attach(cuff, bones=["forearm.L"], k=6))


@item("chain_shirt", hide={"z": [0.885, 1.49], "sleeve": [0.23, 0.47]})
def chain_shirt():
    mail, dark = WK.mail("mail_shirt", "b8bcc4"), pal("darksteel")
    shirt = cloth(region(trunk=(0.86, 1.535), arms=(0.19, 0.50)), hem_off(0.009, 0.86), mail, "shirt", relax=7)
    S = surf(shirt)
    trims = attach([hoop(0.872, 0.018, dark, S, 0.0018, 26), collar(1.50, 1.545, dark, 0.012)], k=8)
    cuff = hoop(0.485, 0.02, dark, S, 0.0018, 12, ARM)
    return [shirt] + trims + WK.both(attach(cuff, bones=["upper_arm.L", "forearm.L"], k=6))


@item("runeweave_vest", hide={"z": [0.885, 1.46]})
def runeweave_vest():
    teal, silver, tide = pal("teal"), pal("silver"), pal("tide")
    sel = region(vest=(0.86, 1.53, 0.205), notch=(1.40, 0.06))
    vest = cloth(sel, hem_off(0.0072, 0.86, 0.0025), teal, "vest", relax=6)
    raw = cloth(sel, hem_off(0.0072, 0.86, 0.0025), teal, "vest", relax=6, rim=False)
    S = surf(vest)
    parts = [vest] + edge_cords(raw, silver, 0.0032, 48)
    pts = [(x, front_y(z, x, S, frame=TRUNK) - 0.002, z) for z in (0.95, 1.05, 1.15, 1.25, 1.35) for x in (-0.028, 0.028)]
    parts += attach([studs(pts, lambda p: (0.0, -0.02, p[2]), 0.0055, tide)], k=6)
    runes = [K.box(0.012, 0.004, 0.028, (-0.08 + i * 0.04, front_y(1.2 + 0.02 * (i % 2), -0.08 + i * 0.04, S, frame=TRUNK) - 0.003,
                                           1.2 + 0.02 * (i % 2)), tide) for i in range(5)]
    return parts + attach(runes, k=6)


# ====================================================================================================================
# armour (10-16 mm cloth, plates beyond)
# ====================================================================================================================
@item("iron_hauberk", hide={"z": [0.925, 1.49], "sleeve": [0.23, 0.47]}, skirt=0.60)
def iron_hauberk():
    mail, leather, gold = WK.mail(), pal("leather"), pal("gold")
    shirt = cloth(region(trunk=(0.90, 1.535), arms=(0.19, 0.50)), 0.014, mail, "shirt", relax=9)
    S = surf(shirt)
    tail = skirt(1.02, 0.60, mail, S, (0.002, 0.022), n=28, steps=4, flare=0.02)
    ST = surf(tail)
    hem = hoop(0.617, 0.028, leather, ST, 0.002, 28, HIPS)
    parts = attach([tail, hem], weights=skw(z_knee=0.60, leg=0.95))
    waist = belt(0.995, 1.045, leather, S, 0.012, clasp=gold)
    neck = collar(1.50, 1.548, leather, 0.017)
    cuff = hoop(0.485, 0.028, leather, S, 0.002, 12, ARM)
    return [shirt] + parts + attach(waist, bones=["hips", "spine"], k=8) + attach(neck, k=8) \
        + WK.both(attach(cuff, bones=["upper_arm.L", "forearm.L"]))


def _brigandine(face, rivet, trim, belt_m, clasp="gold", glow=None, skirt_to=None):
    sel = region(vest=(0.84, 1.53, 0.215), notch=(1.47, 0.045))
    coat = cloth(sel, hem_off(0.0135, 0.84, 0.003), face, "coat", relax=9)
    raw = cloth(sel, hem_off(0.0135, 0.84, 0.003), face, "coat", relax=9, rim=False)
    S = surf(coat)
    parts = [coat] + edge_cords(raw, trim, 0.0045, 52)
    pts = []
    for z in np.linspace(0.93, 1.40, 8):
        for x in np.linspace(-0.15, 0.15, 7):
            if abs(x) < 0.02:
                continue
            pts.append((x, front_y(z, x, S, frame=TRUNK) - 0.001, z))
            pts.append((x, front_y(z, x, S, back=True, frame=TRUNK) + 0.001, z))
    parts += attach([studs(pts, lambda p: (0.0, -0.02, p[2]), 0.0048, rivet)], k=6)
    parts += attach(belt(0.975, 1.03, belt_m, S, 0.004, clasp=clasp), bones=["hips", "spine"], k=8)
    if glow:
        parts += attach([K.gem((0.0, front_y(1.3, 0.0, S, frame=TRUNK) - 0.01, 1.3), 0.013, glow, rot=(90, 0, 0))], bone="chest")
    if skirt_to:
        tail = skirt(0.99, skirt_to, face, S, (0.003, 0.02), n=28, steps=3, flare=0.02, a0=0.0, a1=360.0)
        parts += attach([tail, hoop(skirt_to + 0.012, 0.022, trim, surf(tail), 0.002, 28, HIPS)], weights=skw(z_knee=0.6, leg=0.9))
    return parts


@item("brigandine", hide={"z": [0.865, 1.46]})
def brigandine():
    return _brigandine(pal("crimson"), pal("gold"), pal("leather"), pal("leather"))


@item("depth_vaultpath_coat", hide={"z": [0.865, 1.46]}, skirt=0.66)
def depth_vaultpath_coat():
    return _brigandine(pal("forest"), pal("copper"), pal("copper"), pal("darkleather"), "copper", pal("ember"), skirt_to=0.66)


def _plate(plate, trim, belt_m, glow=None, under="darkleather"):
    """A cuirass over an arming coat: breast and back plates, a gorget, three fauld lames, two pauldrons."""
    # the arming coat shows only below the cuirass and down the upper arms
    coat = cloth(region(trunk=(0.84, 0.975), arms=(0.19, 0.45)), hem_off(0.010, 0.84), pal(under), "arming", relax=6)
    S0 = surf(coat)
    sel = region(trunk=(0.93, 1.515))
    cuir = cloth(sel, 0.021, plate, "cuirass", relax=14)
    raw = cloth(sel, 0.021, plate, "cuirass", relax=14, rim=False)
    S = surf(cuir)
    parts = [coat, cuir] + edge_cords(raw, trim, 0.0045, 36)
    ridge = vband(0.0, 0.96, 1.46, 0.012, trim, S, 0.0025, 8, frame=TRUNK)
    fauld = []
    top = S
    for i in range(3):
        z0 = 0.95 - i * 0.045
        lame = skirt(z0, z0 - 0.06, plate, top, (0.003 + 0.001 * i, 0.012 + 0.002 * i), n=24, steps=1, flare=0.004, thick=0.0,
                     name="fauld")
        top = surf(lame)
        fauld += [lame, hoop(z0 - 0.056, 0.008, trim, top, 0.0015, 24, HIPS)]
    parts += attach([ridge], bone="chest") + attach(fauld, weights=skw(z_top=0.96, z_knee=0.62, leg=0.6))
    parts += attach(belt(0.955, 0.99, belt_m, S0, 0.018, clasp=trim), bones=["hips", "spine"], k=8)
    parts += attach([collar(1.49, 1.555, plate, 0.018, lip=0.006)], k=8)
    parts += WK.both(pauldron(plate, trim))
    if glow:
        parts += attach([K.gem((0.0, front_y(1.3, 0.0, S, frame=TRUNK) - 0.012, 1.3), 0.016, glow, rot=(90, 0, 0)),
                         K.ring_tube((0.0, front_y(1.3, 0.0, S, frame=TRUNK) - 0.006, 1.3), 0.026, 0.0035, trim, axis="y", n=20)],
                        bone="chest")
    return parts


@item("warden_plate", hide={"z": [0.865, 1.49], "sleeve": [0.23, 0.43]}, skirt=0.80)
def warden_plate():
    return _plate(WK.plate("steel"), pal("gold"), pal("darkleather"))


@item("guardian_plate", hide={"z": [0.865, 1.49], "sleeve": [0.23, 0.43]}, skirt=0.80)
def guardian_plate():
    return _plate(WK.plate("bright"), pal("gold"), pal("white"), glow=pal("aether"), under="white")


@item("depth_deepwarden_coat", hide={"z": [0.865, 1.49], "sleeve": [0.23, 0.43]}, skirt=0.80)
def depth_deepwarden_coat():
    return _plate(WK.plate("blued"), pal("bronze"), pal("darkleather"), glow=pal("emerald"))


def metal(key):
    """A metal trim as the worn plates are finished (hero_wear_kit.plate): a mirror-bright gold band reads as black at night."""
    return WK.plate(key) if K.MAT[key][2] >= 0.9 else pal(key)


def _robe(mat, trim, belt_m, hem, sleeve_to=0.70, bell_to=0.08, glow=None, stars=None, open_front=False, belt_clasp=None):
    """A robe or coat: body and sleeves cut from the body, a skirt from the waist to `hem` (open in front for a coat),
    bell cuffs, a trim down the front and round the hem, a belt."""
    body = cloth(region(trunk=(0.86, 1.535), arms=(0.19, sleeve_to), notch=(1.44, 0.055)), hem_off(0.0125, 0.86), mat, "robe", relax=8)
    raw = cloth(region(trunk=(0.86, 1.535), arms=(0.19, sleeve_to), notch=(1.44, 0.055)), hem_off(0.0125, 0.86), mat, "robe", relax=8,
                rim=False)
    S = surf(body)
    parts = [body] + edge_cords(raw, trim, 0.004, 44, pick=lambda P: P[:, 2].mean() > 1.3 and np.abs(P[:, 0]).max() < 0.2)
    a0, a1 = (283.0, 257.0 + 360.0) if open_front else (0.0, 360.0)
    tail = skirt(1.0, hem, mat, S, (0.004, 0.032), n=32, steps=6, flare=0.12 if not open_front else 0.07, a0=a0, a1=a1, thick=0.004,
                 name="skirt")
    ST = surf(tail)
    hemt = hoop(hem + 0.014, 0.026, trim, ST, 0.0022, 32, HIPS, a0=a0, a1=a1)
    skirt_parts = [tail, hemt]
    if not open_front:
        skirt_parts.append(vband(0.0, hem + 0.02, 0.99, 0.034, trim, ST, 0.0045, 20))
    else:
        for x in (-0.03, 0.03):
            skirt_parts.append(vband(x, hem + 0.02, 0.99, 0.022, trim, ST, 0.0045, 20))
    parts += attach(skirt_parts, weights=skw(z_top=1.0, z_knee=0.51, z_bot=hem, centre=0.09, leg=0.85))
    parts += attach([vband(0.0, 1.0, 1.44, 0.026, trim, S, 0.002, 6, frame=TRUNK)], bone="chest")
    parts += attach(belt(0.985, 1.035, belt_m, S, 0.006, clasp=belt_clasp), bones=["hips", "spine"], k=8)
    if bell_to:
        parts += WK.both(bell(sleeve_to - 0.16, sleeve_to - 0.005, 0.004, bell_to * 0.45, mat, S, bell_to * 0.4, trim=trim))
    if glow:
        parts += attach([K.gem((0.0, front_y(1.34, 0.0, S, frame=TRUNK) - 0.01, 1.34), 0.014, glow, rot=(90, 0, 0))], bone="chest")
    if stars:
        pts = []
        for i in range(12):
            z = hem + 0.05 + ((i * 0.37) % 1.0) * (0.95 - hem)
            a = 200.0 + (i * 53.0) % 140.0
            pts.append(HIPS.ring(z, 3, 0.036, ST, a, a + 0.001)[0])
        parts += attach([K.gem(tuple(p), 0.007, stars) for p in pts], weights=skw(z_top=1.0, z_knee=0.51, z_bot=hem, centre=0.09, leg=0.85))
    return parts


@item("apprentice_robe", hide={"z": [0.885, 1.49], "sleeve": [0.23, 0.70]}, skirt=0.30)
def apprentice_robe():
    return _robe(pal("ochre"), pal("linen"), pal("rope"), 0.30)


@item("traveler_coat", hide={"z": [0.885, 1.49], "sleeve": [0.23, 0.70]}, skirt=0.42)
def traveler_coat():
    return _robe(pal("forest"), pal("tan"), pal("leather"), 0.42, bell_to=0.0, open_front=True, belt_clasp=pal("brass"))


@item("magister_robe", hide={"z": [0.885, 1.49], "sleeve": [0.23, 0.70]}, skirt=0.24)
def magister_robe():
    return _robe(pal("navy"), metal("gold"), pal("crimson"), 0.24, glow=pal("sapphire"), belt_clasp=metal("gold"))


@item("sage_robe", hide={"z": [0.885, 1.49], "sleeve": [0.23, 0.70]}, skirt=0.24)
def sage_robe():
    return _robe(pal("violet"), metal("paleg"), pal("paleg"), 0.24, stars=pal("holy"), belt_clasp=metal("paleg"))


@item("depth_prismkeeper_coat", hide={"z": [0.885, 1.49], "sleeve": [0.23, 0.70]}, skirt=0.30)
def depth_prismkeeper_coat():
    return _robe(pal("violet"), metal("silver"), pal("darkleather"), 0.30, glow=pal("tide"), belt_clasp=metal("silver"))


@item("depth_gloomthread_coat", hide={"z": [0.865, 1.46]})
def depth_gloomthread_coat():
    black, moon, ice = pal("black"), pal("moonsteel"), pal("ice")
    sel = region(vest=(0.84, 1.53, 0.21), notch=(1.42, 0.05))
    vest = cloth(sel, hem_off(0.012, 0.84, 0.003), black, "vest", relax=8)
    raw = cloth(sel, hem_off(0.012, 0.84, 0.003), black, "vest", relax=8, rim=False)
    S = surf(vest)
    parts = [vest] + edge_cords(raw, moon, 0.0035, 48)
    for sx in (1.0, -1.0):
        strap = [(sx * 0.19, front_y(1.47, sx * 0.19, S, frame=TRUNK) - 0.004, 1.47),
                 (sx * 0.05, front_y(1.30, sx * 0.05, S, frame=TRUNK) - 0.006, 1.30),
                 (-sx * 0.10, front_y(1.14, -sx * 0.10, S, frame=TRUNK) - 0.006, 1.14),
                 (-sx * 0.19, front_y(1.04, -sx * 0.19, S, frame=TRUNK) - 0.004, 1.04)]
        parts += attach([cord(strap, 0.006, pal("darkleather"), sides=4)], k=6)
    parts += attach(belt(0.97, 1.02, pal("darkleather"), S, 0.004, clasp=moon), bones=["hips", "spine"], k=8)
    parts += attach([K.gem((0.0, front_y(1.30, 0.0, S, frame=TRUNK) - 0.012, 1.30), 0.012, ice, rot=(90, 0, 0))], bone="chest")
    return parts
