"""bh-023: worn armour and inner garments (slots `armor`, `inner_garment`).

Each entry mirrors its item model's spec (tools/blender/items/item_gear.py GEAR, depth_specs.json) so the worn piece
is recognisably the thing in the icon: same kind, same palette keys, same trims.

Layers (offsets from the skin): inner garments 4-9 mm, armour cloth 10-16 mm, plates beyond. Both layers bring their
own legwear, so a hero is never bare-legged under a hauberk whatever is in the other slot. Inner garments are only
body-cut cloth and thin trims (nothing flares), so any armour covers them; they show at the neck and the wrists.

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
# inner garments (4-9 mm)
# ====================================================================================================================
@item("padded_gambeson", hide={"z": [0.13, 1.49], "sleeve": [0.23, 0.69]})
def padded_gambeson():
    wool, linen = pal("wool"), pal("linen")
    jacket = cloth(region(trunk=(0.85, 1.535), arms=(0.19, 0.715)), 0.008, wool, "jacket", relax=5)
    hose = cloth(region(legs=(0.105, 0.93)), 0.004, linen, "hose", relax=2)
    S = surf(jacket)
    body = [hoop(z, 0.012, linen, S, 0.0015, 22) for z in (0.95, 1.04, 1.13, 1.22, 1.31)]      # quilting rows
    body += [hoop(0.868, 0.03, linen, S, 0.002, 24), collar(1.505, 1.56, linen, 0.009)]
    body.append(vband(0.0, 0.88, 1.50, 0.022, linen, S, 0.0025, 7, frame=TRUNK))
    arm = [hoop(x, 0.012, linen, S, 0.0015, 10, ARM) for x in (0.31, 0.40, 0.53, 0.62)]
    arm.append(hoop(0.70, 0.028, linen, S, 0.002, 10, ARM))
    return [jacket, hose] + attach(body, k=8) + WK.both(attach(arm, bones=["upper_arm.L", "forearm.L"], k=8))


@item("iron_hauberk", hide={"z": [0.13, 1.49], "sleeve": [0.23, 0.47]})
def iron_hauberk():
    mail, leather, gold, dark = WK.mail(), pal("leather"), pal("gold"), pal("darkleather")
    shirt = cloth(region(trunk=(0.90, 1.535), arms=(0.19, 0.50)), 0.014, mail, "shirt", relax=9)
    breeches = cloth(region(legs=(0.105, 0.95)), 0.0115, dark, "breeches", relax=5)
    S = surf(shirt)
    tail = skirt(1.02, 0.60, mail, S, (0.002, 0.022), n=28, steps=4, flare=0.02)
    ST = surf(tail)
    hem = hoop(0.617, 0.028, leather, ST, 0.002, 28, HIPS)
    parts = attach([tail, hem], weights=skw(z_knee=0.60, leg=0.95))
    waist = belt(0.995, 1.045, leather, S, 0.012, clasp=gold)
    neck = collar(1.50, 1.548, leather, 0.017)
    cuff = hoop(0.485, 0.028, leather, S, 0.002, 12, ARM)
    return [shirt, breeches] + parts + attach(waist, bones=["hips", "spine"], k=8) + attach(neck, k=8) \
        + WK.both(attach(cuff, bones=["upper_arm.L", "forearm.L"]))
