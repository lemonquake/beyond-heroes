"""Shared helpers for Builder A's bh-010 enemies (necromancer, goblin_summoner, orc_shaman, frost_revenant,
plague_bloater). Pure geometry: every function returns bh_mesh.Part objects in whatever space its inputs are given
(standard space for the SB / Scaled authored modules, real model space for the greenskin ones)."""
import math
import numpy as np

import bh_mesh as M
from bh_body import M_align_z
from bh_math import normalize, Rx, Ry, Rz, R_axis


def P(V, F, mat, name="part"):
    return M.Part(V, F, mat, name=name)


def tube(pts, radii, mat, n=6, up=None, cap=True, p=2.0, name="tube"):
    """Tube along a polyline; radii: scalar, (rx, ry) tuple, or a per-point list of scalars / tuples."""
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


def ball(c, r, mat, n=8, rings=5, scale=(1, 1, 1), name="ball"):
    V, F = M.sphere(r, n, rings, center=c, scale=scale)
    return P(V, F, mat, name)


def arc(center, radius, a0, a1, n, z=0.0, scale=(1.0, 1.0)):
    """Points on a horizontal arc (angles in degrees, 0 = +X, 90 = +Y)."""
    c = np.asarray(center, float)
    return [c + np.array([radius * scale[0] * math.cos(math.radians(a)), radius * scale[1] * math.sin(math.radians(a)),
                          z]) for a in np.linspace(a0, a1, n)]


def shard(base, direction, length, radius, mat, sides=5, twist=0.0, up=(0, 0, 1), mid=0.35, name="shard"):
    """Angular crystal: a prism of `sides` flat faces from `base` along `direction`, widest at `mid`, pointed tip,
    blunt buried foot. Reads as ice / crystal at distance (flat facets)."""
    d = normalize(direction)
    R = M_align_z(d, up if abs(np.dot(normalize(up), d)) < 0.95 else (1, 0, 0))
    prof = [(radius * 0.55, -0.08 * length), (radius, mid * length), (radius * 0.75, 0.72 * length), (0.0, length)]
    V, F = M.lathe([(0.0, -0.1 * length)] + prof, sides, a0=twist, a1=twist + 360)
    V = np.asarray(V) @ R.T + np.asarray(base, float)
    return P(V, F, mat, name)


def cluster(base, normal, size, mat, count=4, seed=1, spread=28.0, up=(0, 0, 1), sides=5, name="cluster"):
    """A small cluster of shards growing out of a surface point along `normal`."""
    rng = np.random.default_rng(seed)
    n = normalize(normal)
    t1 = normalize(np.cross(n, (0.31, 0.53, 0.79)))
    t2 = np.cross(n, t1)
    out = []
    for i in range(count):
        a = 2 * math.pi * (i / count) + rng.random() * 0.8
        tilt = spread * (0.25 + 0.75 * rng.random()) if i else spread * 0.15
        d = R_axis(t1 * math.cos(a) + t2 * math.sin(a), tilt) @ n
        ln = size * (1.0 if i == 0 else 0.45 + 0.4 * rng.random())
        off = (t1 * math.cos(a) + t2 * math.sin(a)) * size * 0.12 * (i > 0)
        out.append(shard(np.asarray(base, float) + off - n * size * 0.05, d, ln, ln * 0.22, mat, sides=sides,
                         twist=rng.random() * 60, up=up, name=name))
    return out


def skull_charm(center, r, bone="BH_Bone", sockets="BH_Shadow", eyes=None, face=(0, -1, 0), up=(0, 0, 1),
                jaw=True, n=10):
    """Small skull (charm / staff head): cranium, cheek block, two sockets (optional glowing eyes), jaw.
    `face` = direction the face looks at, `up` = skull up."""
    f = normalize(face)
    u = normalize(np.asarray(up, float) - f * np.dot(up, f))
    x = np.cross(u, f)          # skull's left when looking along f... (only used symmetrically)
    Rm = np.stack([x, -f, u], 1)   # local: +X side, -Y face, +Z up
    c = np.asarray(center, float)

    def L(p):
        return c + Rm @ (np.asarray(p, float) * r)
    parts = []
    V, F = M.sphere(1.0, n, max(5, n // 2), scale=(0.86, 1.0, 0.92))
    parts.append(P(np.array([L(v) for v in V]), F, bone, "skull"))
    V, F = M.sphere(1.0, n, 4, scale=(0.62, 0.55, 0.42))
    parts.append(P(np.array([L(v + np.array([0, -0.52, -0.62])) for v in V]), F, bone, "maxilla"))
    for sx in (1, -1):
        V, F = M.sphere(1.0, 6, 4, scale=(0.26, 0.2, 0.24))
        parts.append(P(np.array([L(v + np.array([sx * 0.34, -0.86, -0.12])) for v in V]), F, sockets, "socket"))
        if eyes:
            V, F = M.sphere(1.0, 6, 4, scale=(0.13, 0.1, 0.12))
            parts.append(P(np.array([L(v + np.array([sx * 0.34, -0.99, -0.12])) for v in V]), F, eyes, "eye"))
    V, F = M.prism([(-0.08, 0.0), (0.08, 0.0), (0.0, 0.18)], 0.1, axis="y")
    parts.append(P(np.array([L(v + np.array([0, -0.98, -0.52])) for v in V]), F, sockets, "nasal"))
    if jaw:
        V, F = M.sphere(1.0, n, 4, scale=(0.52, 0.5, 0.26))
        parts.append(P(np.array([L(v + np.array([0, -0.45, -1.02])) for v in V]), F, bone, "jaw"))
        V, F = M.box(0.62, 0.08, 0.1)
        parts.append(P(np.array([L(v + np.array([0, -0.93, -0.8])) for v in V]), F, sockets, "teeth_gap"))
    return parts


def hand_frame(body, side):
    """Weapon-socket frame (model space): returns fn(x, y, z) -> point with +x = distal (knuckles) on both sides,
    +y = thumb side, +z = back of the hand."""
    A = body.axes("weapon." + side)
    o = body.head("weapon." + side)
    xs = 1.0 if side == "R" else -1.0

    def L(x, y, z):
        return o + A @ np.array([x * xs, y, z])
    return L, A


def bony_fingers(body, side, mat, length=0.1, r=0.0075, curl=0.5, spread=1.0, nails=None, open_hand=False, s=1.0):
    """Long bony fingers extending from the knuckles of a closed fist (open_hand=False: they wrap round the grip then
    the tips point down/back like claws) or splayed forward (open_hand=True). Returns parts bound to hand.<side>."""
    L, A = hand_frame(body, side)
    parts = []
    for k in range(4):
        y = (-0.03 + 0.02 * k) * spread * s
        lk = length * (0.85 + 0.15 * (k in (1, 2))) * s
        if open_hand:
            pts = [L(0.02 * s, y, 0.012 * s), L(0.02 * s + lk * 0.45, y * 1.25, 0.004 * s),
                   L(0.02 * s + lk * 0.8, y * 1.45, -lk * 0.25 * curl), L(0.02 * s + lk * 0.95, y * 1.55, -lk * 0.6 * curl)]
        else:
            pts = [L(0.035 * s, y, 0.0), L(0.05 * s, y, -0.03 * s), L(0.03 * s, y, -0.055 * s),
                   L(0.0, y, -0.06 * s - lk * 0.3 * curl)]
        parts.append(taper(pts, r * s, r * 0.55 * s, mat, n=5, up=A[:, 2], name="finger"))
        parts.append(ball(pts[1], r * 1.35 * s, mat, n=5, rings=3, name="knuckle"))
        if nails:
            tip = pts[-1]
            dirn = normalize(pts[-1] - pts[-2])
            parts.append(taper([tip - dirn * 0.004 * s, tip + dirn * 0.03 * s], r * 0.8 * s, 0.0008, nails, n=4,
                               name="nail"))
    return parts


def open_palm(body, side, mat, s=1.0):
    """Flat palm block for an open hand (fingers from bony_fingers(open_hand=True)) + a thumb."""
    L, A = hand_frame(body, side)
    rings = []
    for x, wy, hz in ((-0.07, 0.028, 0.018), (-0.04, 0.038, 0.02), (-0.005, 0.042, 0.018), (0.025, 0.04, 0.015)):
        ring = []
        for i in range(10):
            a = 2 * math.pi * i / 10
            ring.append(L(x * s, wy * s * np.sign(math.cos(a)) * abs(math.cos(a)) ** 0.7,
                          0.006 * s + hz * s * np.sign(math.sin(a)) * abs(math.sin(a)) ** 0.7))
        rings.append(np.array(ring))
    V, F = M.loft(rings)
    parts = [P(V, F, mat, "palm")]
    tp = [L(-0.045 * s, 0.035 * s, 0.0), L(-0.01 * s, 0.062 * s, -0.012 * s), L(0.02 * s, 0.075 * s, -0.02 * s)]
    parts.append(taper(tp, 0.011 * s, 0.006 * s, mat, n=6, up=A[:, 2], name="thumb"))
    return parts


def rag_strip(top, down, length, width, mat, n=5, thick=0.006, sway=(0.0, 0.0), ragged=0.3, seed=0.0, out=None):
    """Hanging cloth tatter: from `top` along `down` (unit-ish), narrowing, with a notched end. out = surface normal
    (thickness direction)."""
    top = np.asarray(top, float)
    d = normalize(down)
    o = normalize(out if out is not None else np.cross(d, (1, 0, 0)))
    pts = []
    for i in range(n):
        t = i / (n - 1)
        pts.append(top + d * length * t + np.array([sway[0], sway[1], 0.0]) * t * t)
    ws = [width * (1 - 0.45 * i / (n - 1)) for i in range(n)]
    ws[-1] *= 0.5 + ragged * math.sin(seed * 3.7) ** 2
    V, F = M.tube(pts, [(w / 2, thick / 2) for w in ws], n=4, up=o, p=3.0)
    return P(V, F, mat, "tatter")


def lathe_part(profile, mat, n=10, name="lathe"):
    V, F = M.lathe(profile, n)
    return P(V, F, mat, name)


def feather(base, direction, length, width, mat, side=(1, 0, 0), bend=0.15, name="feather"):
    """Flat feather: quill + vane (leaf outline) in the plane of direction x side."""
    d = normalize(direction)
    sd = normalize(np.asarray(side, float) - d * np.dot(side, d))
    nrm = np.cross(d, sd)
    outline = []
    k = 9
    for i in range(k):
        t = i / (k - 1)
        outline.append((t, 0.5 * width * math.sin(math.pi * min(t * 1.08, 1.0)) ** 0.8 * (1.0 if t < 0.95 else 0.4)))
    top = [(t * length, w) for t, w in outline]
    bot = [(t * length, -w * 0.8) for t, w in outline[::-1]][1:-1]
    o = np.array(top + bot)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    V, F = M.prism(o, 0.003, axis="z")
    b = np.asarray(base, float)
    Vn = [b + d * x + sd * y + nrm * (z + bend * (x / length) ** 2 * length) for x, y, z in V]
    return P(np.array(Vn), F, mat, name)
