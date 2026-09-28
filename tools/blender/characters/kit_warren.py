"""Shared modelling helpers for the Hollowroot Warren enemies (bh-012, Builder B): sporeling, rootweaver,
mycelid_hulk, rot_mother (and the rootback_boar creature script). Pure geometry in real MODEL space (the bh_body
modelling pose), returning bh_mesh.Part objects: mushroom caps with gill undersides and warts, shelf fungi, gnarled
roots / branching root antlers, glowing spore blisters, hanging root skirts and simple split robe skirts."""
import math

import numpy as np

import bh_mesh as M
from bh_body import M_align_z, smoothstep
from bh_math import normalize, R_axis


def P(V, F, mat, name="part"):
    return M.Part(V, F, mat, name=name)


def orient(part, up, center, spin=0.0, hint=(0, -1, 0)):
    """Part authored along +Z at the origin -> +Z along `up`, moved to `center` (spin: degrees about +Z first)."""
    if spin:
        part.rot(R_axis((0, 0, 1), spin))
    part.rot(M_align_z(up, hint if abs(np.dot(normalize(up), normalize(hint))) < 0.95 else (1, 0, 0)))
    return part.move(center)


# ------------------------------------------------------------------------------------------------ mushroom caps
def cap(center, up, radius, height, top_mat, under_mat, n=20, rim_phi=-18.0, under=0.22, gills=0.0, gill_k=10,
        wobble=0.0, seed=0, rings=7, stem_r=None, squash=1.0, spin=0.0):
    """Mushroom cap. Top: dome from the drooping rim (angle rim_phi below the equator) to the pole; underside from
    the stem (radius stem_r, depth `under` * height below the rim plane) out to the rim, with radial gill ridges
    (gills = ridge depth in m). wobble: organic radial wave. squash scales the cap along its local Y (oval caps).
    Returns [top, underside] parts."""
    R, H = float(radius), float(height)
    phis = np.linspace(math.radians(rim_phi), math.radians(90.0), rings)
    prof_top = [(R * math.cos(p) if i < rings - 1 else 0.0, H * math.sin(p) if p > 0 else R * 0.35 * math.sin(p))
                for i, p in enumerate(phis)]
    zr = prof_top[0][1]
    rr = prof_top[0][0]
    V, F = M.lathe(prof_top, n)
    top = P(V, F, top_mat, "cap")
    sr = stem_r if stem_r is not None else R * 0.18
    zu = zr + H * 0.12
    prof_u = [(0.0, zu + H * 0.1), (sr, zu), (sr + (rr - sr) * 0.35, zr + H * 0.02 - under * H * 0.3),
              (sr + (rr - sr) * 0.75, zr - under * H * 0.15), (rr * 0.985, zr)]
    V, F = M.lathe(prof_u, n)
    und = P(V, F, under_mat, "gills")
    if gills:
        a = np.arctan2(und.V[:, 1], und.V[:, 0])
        r = np.hypot(und.V[:, 0], und.V[:, 1])
        s = np.clip((r - sr) / max(rr - sr, 1e-6), 0, 1)
        und.V[:, 2] -= gills * (0.5 + 0.5 * np.cos(gill_k * a)) * np.sin(math.pi * s) ** 0.7
    rng = np.random.default_rng(seed)
    ph = rng.random(3) * 6.28
    for p in (top, und):
        if wobble:
            a = np.arctan2(p.V[:, 1], p.V[:, 0])
            f = 1 + wobble * (np.sin(3 * a + ph[0]) * 0.6 + np.sin(5 * a + ph[1]) * 0.4)
            p.V[:, 0] *= f
            p.V[:, 1] *= f
            p.V[:, 2] += wobble * H * 0.8 * np.sin(4 * a + ph[2]) * (np.hypot(p.V[:, 0], p.V[:, 1]) / R) ** 2
        p.V[:, 1] *= squash
        orient(p, up, center, spin)
    return [top, und]


def cap_point(center, up, radius, height, phi_deg, ang_deg, rim_phi=-18.0, spin=0.0, squash=1.0):
    """Point + outward normal on the top of a cap() (same parameters), phi = elevation angle, ang = azimuth."""
    p = math.radians(phi_deg)
    a = math.radians(ang_deg)
    z = height * math.sin(p) if p > 0 else radius * 0.35 * math.sin(p)
    q = np.array([radius * math.cos(p) * math.cos(a), radius * math.cos(p) * math.sin(a) * squash, z])
    nrm = normalize(np.array([math.cos(p) * math.cos(a) / radius, math.cos(p) * math.sin(a) / radius,
                              max(math.sin(p), 0.05) / max(height, 1e-3)]))
    Rm = M_align_z(up, (0, -1, 0) if abs(normalize(up)[1]) < 0.95 else (1, 0, 0))
    if spin:
        Rs = R_axis((0, 0, 1), spin)
        q, nrm = Rs @ q, Rs @ nrm
    return np.asarray(center, float) + Rm @ q, normalize(Rm @ nrm)


def warts(center, up, radius, height, count, mat, size, seed=0, phi=(12, 75), glow=None, glow_every=0, spin=0.0,
          squash=1.0, n=7):
    """Flattened warts / speckles scattered over the top of a cap(); every glow_every-th wart uses `glow`."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(count):
        ph = phi[0] + (phi[1] - phi[0]) * rng.random() ** 0.8
        an = 360.0 * (i / count) + 25 * rng.random()
        q, nrm = cap_point(center, up, radius, height, ph, an, spin=spin, squash=squash)
        r = size * (0.6 + 0.8 * rng.random())
        mat_i = glow if (glow and glow_every and i % glow_every == 0) else mat
        V, F = M.sphere(r, n, 4, scale=(1.0, 1.0, 0.45))
        out.append(orient(P(V, F, mat_i, "wart"), nrm, q + nrm * r * 0.1))
    return out


# ------------------------------------------------------------------------------------------------ fungi / blisters
def shelf(base, out, radius, mat, thick=0.3, up=(0, 0, 1), tilt=8.0, n=12, rim_mat=None):
    """Bracket (shelf) fungus growing out of a surface at `base` toward `out`: a flat half-buried ellipsoid,
    optionally with a pale rim band."""
    o = normalize(np.asarray(out, float) - np.asarray(up, float) * np.dot(out, up) * 0.7)
    V, F = M.sphere(radius, n, 5, scale=(1.0, 0.72, thick))
    p = P(V, F, mat, "shelf")
    # local: +Y = outward, +Z = up
    zz = normalize(np.asarray(up, float) - o * np.dot(up, o))
    xx = np.cross(o, zz)
    Rm = np.stack([xx, o, zz], 1) @ R_axis((1, 0, 0), tilt)
    p.V = p.V @ Rm.T + np.asarray(base, float) + o * radius * 0.35
    parts = [p]
    if rim_mat:
        V, F = M.sphere(radius * 1.02, n, 3, scale=(1.0, 0.74, thick * 0.35))
        r = P(V, F, rim_mat, "shelf_rim")
        r.V = r.V @ Rm.T + np.asarray(base, float) + o * radius * 0.35 - zz * radius * thick * 0.25
        parts.append(r)
    return parts


def blister(center, normal, r, glow_mat, ring_mat=None, n=8):
    """Glowing spore blister half sunk into a surface, optionally with a swollen collar."""
    nrm = normalize(normal)
    V, F = M.sphere(r, n, 5, scale=(1.0, 1.0, 0.8))
    parts = [orient(P(V, F, glow_mat, "blister"), nrm, np.asarray(center, float) + nrm * r * 0.25)]
    if ring_mat:
        V, F = M.sphere(r * 1.45, n, 4, scale=(1.0, 1.0, 0.35))
        parts.append(orient(P(V, F, ring_mat, "blister_ring"), nrm, np.asarray(center, float)))
    return parts


def mushroom(base, up, stalk_h, stalk_r, cap_r, cap_h, stalk_mat, cap_mat, under_mat, n=10, bend=0.0, seed=0,
             warts_mat=None, wart_count=0, glow=None, bend_dir=(1, 0, 0)):
    """Small whole mushroom (stalk + cap) growing from `base` along `up` (bent sideways by `bend`)."""
    u = normalize(up)
    bd = normalize(np.asarray(bend_dir, float) - u * np.dot(bend_dir, u)) if bend else np.zeros(3)
    b = np.asarray(base, float)
    pts = [b - u * stalk_r * 0.5, b + u * stalk_h * 0.5 + bd * bend * 0.3, b + u * stalk_h + bd * bend]
    parts = [tube(pts, [stalk_r * 1.25, stalk_r, stalk_r * 0.85], stalk_mat, n=max(5, n // 2 + 1))]
    top_dir = normalize(pts[-1] - pts[-2])
    parts += cap(pts[-1], top_dir, cap_r, cap_h, cap_mat, under_mat, n=n, rings=5, seed=seed, stem_r=stalk_r)
    if warts_mat and wart_count:
        parts += warts(pts[-1], top_dir, cap_r, cap_h, wart_count, warts_mat, cap_r * 0.12, seed=seed, glow=glow,
                       glow_every=2 if glow else 0, n=5)
    return parts


# ------------------------------------------------------------------------------------------------ roots
def tube(pts, radii, mat, n=6, up=None, cap=True, p=2.0, name="tube"):
    pts = np.asarray(pts, float)
    if np.ndim(radii) == 0 or isinstance(radii, tuple):
        radii = [radii] * len(pts)
    prof = [(r, r) if np.ndim(r) == 0 else tuple(r) for r in radii]
    if up is None:
        d = normalize(pts[-1] - pts[0])
        up = (0, 0, 1) if abs(d[2]) < 0.85 else (0, -1, 0)
    V, F = M.tube(pts, prof, n=n, up=up, cap0=cap, cap1=cap, p=p)
    return P(V, F, mat, name)


def gnarl(pts, amp, seed=0, sub=2):
    """Subdivide a polyline and push the inner points sideways by smooth noise (gnarled roots / branches)."""
    pts = [np.asarray(p, float) for p in pts]
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        for k in range(1, sub + 1):
            out.append(a + (b - a) * k / sub)
    rng = np.random.default_rng(seed)
    res = [out[0]]
    for i, q in enumerate(out[1:-1], 1):
        res.append(q + rng.normal(size=3) * amp)
    res.append(out[-1])
    return res


def root(pts, r0, r1, mat, n=6, seed=0, knot=0.18, amp=0.0, sub=1, name="root"):
    """Gnarled tapering root along a polyline (radius noise `knot`, lateral noise `amp`)."""
    q = gnarl(pts, amp, seed, sub) if amp else [np.asarray(p, float) for p in pts]
    k = len(q)
    rng = np.random.default_rng(seed + 101)
    rr = [max((r0 + (r1 - r0) * i / (k - 1)) * (1 + knot * (rng.random() - 0.5) * 2), 0.0015) for i in range(k)]
    return tube(q, rr, mat, n=n, name=name)


def branch(base, direction, length, r0, mat, depth=2, seed=0, spread=32.0, up=(0, 0, 1), forks=2, curl=0.0,
           n=6, taper=0.55, min_r=0.004):
    """Recursive branching root / antler from `base` along `direction`."""
    rng = np.random.default_rng(seed)
    d = normalize(direction)
    side = normalize(np.cross(d, up)) if abs(np.dot(d, normalize(up))) < 0.97 else np.array([1.0, 0, 0])
    mid = np.asarray(base, float) + d * length * 0.5 + side * length * 0.08 * (rng.random() - 0.5)
    d2 = normalize(d + np.asarray(up, float) * curl)
    tip = mid + d2 * length * 0.5
    r1 = max(r0 * taper, min_r)
    parts = [root([base, mid, tip], r0, r1, mat, n=n, seed=seed, knot=0.12)]
    if depth > 0:
        for k in range(forks):
            ang = spread * (1 if k % 2 == 0 else -1) * (0.7 + 0.6 * rng.random())
            rot_axis = normalize(np.cross(d2, side) * 0.3 + side * (0.2 if k else -0.2) + np.cross(d2, up))
            nd = R_axis(rot_axis if np.linalg.norm(rot_axis) > 1e-3 else side, ang) @ d2
            t = 0.55 + 0.4 * rng.random() if k else 1.0
            start = mid + (tip - mid) * t if k else tip
            parts += branch(start, nd, length * (0.55 + 0.2 * rng.random()), r1 * (0.9 if k == 0 else 0.75), mat,
                            depth - 1, seed * 7 + k + 1, spread, up, forks, curl, n=max(4, n - 1), taper=taper,
                            min_r=min_r)
    return parts


def hanging_strands(tops, lengths, r0, mat, seed=0, sway=0.03, n=5, r1=None, out_push=0.0, centre=(0, 0)):
    """Hanging roots / vines / mycelium threads from each top point straight down (with a little curl)."""
    rng = np.random.default_rng(seed)
    parts = []
    for i, (t, ln) in enumerate(zip(tops, lengths)):
        t = np.asarray(t, float)
        out = normalize(np.array([t[0] - centre[0], t[1] - centre[1], 0.0]) + 1e-6)
        pts = [t]
        for k in (0.33, 0.66, 1.0):
            pts.append(t + np.array([0, 0, -ln * k]) + out * out_push * k +
                       np.array([rng.normal() * sway, rng.normal() * sway, 0.0]) * k)
        parts.append(root(pts, r0, r1 if r1 is not None else r0 * 0.3, mat, n=n, seed=seed + i, knot=0.2))
    return parts


# ------------------------------------------------------------------------------------------------ hands
def hand_frame(body, side):
    A = body.axes("weapon." + side)
    o = body.head("weapon." + side)
    xs = 1.0 if side == "R" else -1.0

    def L(x, y, z):
        return o + A @ np.array([x * xs, y, z])
    return L, A


def root_fingers(body, side, mat, count=4, length=0.12, r=0.01, curl=0.7, spread=1.0, s=1.0, seed=0,
                 open_hand=False, tip_mat=None):
    """Knobbly root fingers from the knuckles of the hand (closed: wrap the grip and hang as claws; open: splayed)."""
    L, A = hand_frame(body, side)
    rng = np.random.default_rng(seed)
    parts = []
    for k in range(count):
        y = (-0.03 + 0.06 * k / max(count - 1, 1)) * spread * s
        lk = length * (0.85 + 0.3 * rng.random()) * s
        if open_hand:
            pts = [L(0.02 * s, y, 0.01 * s), L(0.02 * s + lk * 0.4, y * 1.3, 0.0),
                   L(0.02 * s + lk * 0.75, y * 1.5, -lk * 0.25 * curl), L(0.02 * s + lk, y * 1.6, -lk * 0.55 * curl)]
        else:
            pts = [L(0.03 * s, y, 0.004 * s), L(0.05 * s, y, -0.028 * s), L(0.035 * s, y * 1.1, -0.055 * s),
                   L(0.01 * s, y * 1.2, -0.06 * s - lk * 0.45 * curl)]
        parts.append(root(pts, r * s, r * 0.35 * s, mat, n=5, seed=seed + k, knot=0.25))
        parts.append(P(*M.sphere(r * 1.35 * s, 5, 3, center=pts[1]), mat, "knuckle"))
        if tip_mat:
            d = normalize(pts[-1] - pts[-2])
            parts.append(tube([pts[-1] - d * 0.004 * s, pts[-1] + d * 0.022 * s], [r * 0.5 * s, 0.001], tip_mat, n=4))
    return parts


# ------------------------------------------------------------------------------------------------ robes
def ellipse_ring(z, rx, ryf, ryb, fr, cy=0.0, p=2.2):
    """Points on a horizontal super-ellipse ring at fractions fr (0 = front (-Y), 0.25 = own left (+X), 0.5 = back)."""
    e = 2.0 / p
    pts = []
    for f in fr:
        a = 2 * math.pi * f - math.pi / 2
        c, s = math.cos(a), math.sin(a)
        x = rx * np.sign(c) * abs(c) ** e
        y = (ryf if s < 0 else ryb) * np.sign(s) * abs(s) ** e
        pts.append((x, cy + y, z))
    return np.array(pts)


def split_skirt(body, mat, z_top, z_bot, top_r, flare, ragged=0.0, folds=0.0, nz=8, nu=9, seed=0.0, thick=0.01,
                max_leg=0.8, center_w=0.08, cy=0.0, shin_from=None, upper="hips", gap=0.006):
    """Long skirt as 4 panels (front/back x L/R) so the legs can move. top_r = (rx, ryf, ryb) at z_top, flare = extra
    radius at the hem. Weighted hips -> thighs (-> shins from shin_from)."""
    zs = list(np.linspace(z_bot, z_top, nz))
    span = z_top - z_bot
    w = body.skirt_weights(z_top, z_bot, max_leg=max_leg, shin_from=shin_from, center_w=center_w, upper=upper)
    for sgn in (1, -1):
        for back in (False, True):
            rings = []
            for z in zs:
                t = (z_top - z) / span
                a, b = (gap, 0.25) if not back else (0.25, 0.5 - gap)
                fr = np.linspace(a, b, nu)
                pts = ellipse_ring(z, top_r[0] + flare * t, top_r[1] + flare * t, top_r[2] + flare * 1.1 * t, fr,
                                   cy=cy)
                ang = np.linspace(0, 1, nu)
                if folds:
                    fold = folds * t ** 1.2 * np.sin(ang * math.pi * 3 + (0.6 if back else 0.0) + seed)
                    rad = pts[:, :2] - np.array([0, cy])
                    rad /= np.maximum(np.linalg.norm(rad, axis=1, keepdims=True), 1e-9)
                    pts[:, :2] += rad * fold[:, None]
                if ragged and t > 0.99:
                    pts[:, 2] += ragged * (0.5 + 0.5 * np.sin(ang * 17 + (3 if back else 0) + sgn + seed)) * \
                        (0.6 + 0.4 * np.cos(ang * 7 + seed))
                if sgn < 0:
                    pts[:, 0] *= -1
                rings.append(pts)
            if sgn < 0:
                rings = [r[::-1] for r in rings]
            V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
            body.add(M.solidify(P(V, F, mat, "skirt_panel"), thick, offset=1.0), weights=w)
    return w


def const_w(d):
    return lambda V: [dict(d)] * len(V)
