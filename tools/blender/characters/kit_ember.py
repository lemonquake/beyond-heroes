"""Shared helpers for Builder C's Emberforge Depths enemies (bh-012): cinder_imp, forge_thrall, magma_golem,
forgemaster (and the slag_hound creature script). Model-space authoring on bh_body.Body, same conventions as
greenskin_kit (tubes / blobs / cones) plus lava seams, glowing crack networks, rivets and chain links.

Glow rule for the Ember family: everything that glows is BH_Emissive (orange, strong); the Magma Golem's furnace
core is BH_WeakPoint. Soot / basalt / blackened iron / leather carry no emission."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import interp_rows  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz  # noqa: E402
import greenskin_kit as GK  # noqa: E402

EMBER = ((1.0, 0.45, 0.1), 0.0, 0.35, (1.0, 0.45, 0.1), 10.0, 1.0)


def P(V, F, mat, name="part"):
    return M.Part(np.asarray(V, float), F, mat, name=name)


def rtube(pts, r, mat, n=6, up=None, cap=True, p=2.0):
    return GK.rtube(pts, r, mat, n=n, up=up, cap=cap, p=p)


def seam(pts, nrm, r=0.012, groove="BH_Shadow", glow="BH_Emissive", sink=0.35):
    """Lava seam on a surface: dark groove tube with a glowing core just proud of it.
    pts: surface points; nrm: outward normal (one or per point)."""
    pts = np.asarray(pts, float)
    nrm = np.asarray(nrm, float)
    if nrm.ndim == 1:
        nrm = np.repeat(nrm[None], len(pts), 0)
    out = []
    if groove:
        out.append(rtube(pts - nrm * r * sink, [r * 1.7] * len(pts), groove, n=4))
    out.append(rtube(pts + nrm * r * 0.15, [r] * len(pts), glow, n=5))
    return out


def crack_path(rng, start, steps, step_len, jag=0.6, drift=(0.0, -1.0)):
    """Random zig-zag 2D polyline in a (u, v) parameter plane."""
    p = np.array(start, float)
    d = normalize(np.array(drift, float) + rng.normal(size=2) * 0.4)
    pts = [p.copy()]
    for _ in range(steps):
        d = normalize(d + rng.normal(size=2) * jag)
        p = p + d * step_len * (0.7 + 0.6 * rng.random())
        pts.append(p.copy())
    return pts


def torso_point(rows, f, z, g=0.0, p=2.2):
    """Surface point + outward normal of a torso loft (rows (z, rx, ryf, ryb, keel[, cy])) at angle fraction f
    (0 = front, 0.25 = own left, 0.5 = back) and height z, grown by g."""
    r = interp_rows(rows, z)
    rx, ryf, ryb, keel = r[1] + g, r[2] + g, r[3] + g, r[4]
    cy = r[5] if len(r) > 5 else 0.0
    e = 2.0 / p
    a = 2 * math.pi * f - math.pi / 2
    c, s = math.cos(a), math.sin(a)
    x = rx * np.sign(c) * abs(c) ** e
    if s < 0:
        y = ryf * np.sign(s) * abs(s) ** e * (1 + keel * max(0.0, 1 - abs(c) ** (p / 2) * 1.6) ** 2)
    else:
        y = ryb * np.sign(s) * abs(s) ** e
    q = np.array([x, cy + y, z])
    n = normalize(np.array([x / max(rx, 1e-6) ** 2, y / max(ryf if s < 0 else ryb, 1e-6) ** 2, 0.0]))
    return q, n


def torso_cracks(rows, rng, count, f_range, z_range, r=0.006, steps=5, step=0.03, g=0.001, groove=None,
                 p=2.2, branch=0.5):
    """Glowing crack network on a torso loft. f_range may wrap (e.g. (-0.2, 0.2)). Returns parts (model space)."""
    parts = []
    circ = 2 * math.pi * max(interp_rows(rows, (z_range[0] + z_range[1]) / 2)[1], 0.03)
    for i in range(count):
        f0 = f_range[0] + (f_range[1] - f_range[0]) * rng.random()
        z0 = z_range[0] + (z_range[1] - z_range[0]) * rng.random()
        path = crack_path(rng, (f0 * circ, z0), steps, step, drift=(rng.normal() * 0.6, -1.0 if rng.random() < 0.6
                                                                    else 1.0))
        pts, ns = [], []
        for u, z in path:
            z = min(max(z, rows[0][0] + 0.01), rows[-1][0] - 0.01)
            q, n = torso_point(rows, (u / circ) % 1.0, z, g, p)
            pts.append(q)
            ns.append(n)
        parts += seam(pts, np.array(ns), r, groove=groove)
        if branch and rng.random() < branch and len(pts) > 3:
            k = int(rng.integers(1, len(path) - 2))
            sub = crack_path(rng, path[k], max(2, steps // 2), step * 0.8)
            pts2, ns2 = [], []
            for u, z in sub:
                z = min(max(z, rows[0][0] + 0.01), rows[-1][0] - 0.01)
                q, n = torso_point(rows, (u / circ) % 1.0, z, g, p)
                pts2.append(q)
                ns2.append(n)
            parts += seam(pts2, np.array(ns2), r * 0.75, groove=groove)
    return parts


def limb_cracks(a, b, radius, rng, count, r=0.005, u_range=(0.1, 0.9), steps=4, groove=None, face=None):
    """Glowing cracks on a limb tube around segment a->b of the given radius (float or fn(u)).
    face: optional preferred outward direction (cracks cluster on that side)."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    d = normalize(b - a)
    x = normalize(np.cross(d, (0, 0, 1.0))) if abs(d[2]) < 0.9 else normalize(np.cross(d, (0, 1.0, 0)))
    y = np.cross(d, x)
    L = np.linalg.norm(b - a)
    rad = radius if callable(radius) else (lambda u, R=radius: R)
    base_ang = None
    if face is not None:
        fv = np.asarray(face, float)
        base_ang = math.atan2(fv @ y, fv @ x)
    parts = []
    for i in range(count):
        u0 = u_range[0] + (u_range[1] - u_range[0]) * rng.random()
        ang0 = (base_ang + rng.normal() * 0.9) if base_ang is not None else rng.random() * 2 * math.pi
        cr = rad(u0) * 2 * math.pi
        path = crack_path(rng, (ang0 * rad(u0), u0 * L), steps, 0.1 * L / steps * 2.2, drift=(rng.normal() * 0.8,
                                                                                               1.0))
        pts, ns = [], []
        for s_, t in path:
            u = min(max(t / L, 0.02), 0.98)
            R = rad(u)
            ang = s_ / max(R, 1e-4)
            n = math.cos(ang) * x + math.sin(ang) * y
            pts.append(a + d * (u * L) + n * (R + 0.001))
            ns.append(n)
        parts += seam(pts, np.array(ns), r, groove=groove)
    return parts


def rivet(c, r, mat="BH_DarkSteel", n=6):
    return GK.blob(c, r, mat, scale=(1, 1, 0.7), n=n, rings=3)


def rivet_on(c, nrm, r, mat="BH_DarkSteel", n=6):
    V, F = M.sphere(r, n, 3, scale=(1, 1, 0.55))
    from bh_body import M_align_z
    R = M_align_z(nrm)
    return P(np.asarray(V) @ R.T + np.asarray(c, float), F, mat, "rivet")


def link(c, r, t, rotz=0.0, mat="BH_DarkSteel", tilt=0.0):
    """One chain link: flattened torus in the XZ plane (long axis vertical), rotated about Z by rotz."""
    pts = [np.array([r * 0.6 * math.cos(a), 0.0, r * math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 9)]
    V, F = M.tube(pts, [(t, t)] * len(pts), n=4, up=(0, 1, 0), cap0=False, cap1=False)
    p = M.Part(V, F, mat, name="link")
    p.rot(Rz(rotz) @ Rx(tilt)).move(c)
    return p


def chain(top, n, r, t, direction=(0, 0, -1), mat="BH_DarkSteel", sway=0.0, broken=True):
    """Hanging chain from `top` downwards: n links alternating 0/90 deg; the last link is open (broken)."""
    d = normalize(direction)
    out = []
    for j in range(n):
        c = np.asarray(top, float) + d * (r * 1.5 * j + r) + np.array([sway * math.sin(j * 1.3), 0, 0])
        lk = link((0, 0, 0), r, t, rotz=90 * (j % 2), mat=mat)
        if broken and j == n - 1:
            keep = lk.V[:, 2] > -r * 0.2        # open the last link
            lk = _cut(lk, keep)
        R = _align(np.array([0, 0, -1.0]), d)
        lk.rot(R).move(c)
        out.append(lk)
    return out


def _align(a, b):
    a, b = normalize(a), normalize(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3) if c > 0 else np.diag([1, -1, -1.0])
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c))


def _cut(part, keep):
    idx = np.nonzero(keep)[0]
    remap = {int(o): i for i, o in enumerate(idx)}
    F = [tuple(remap[v] for v in f) for f in part.F if all(v in remap for v in f)]
    return M.Part(part.V[idx], F, part.mat, name=part.name)


def shard(base, direction, length, width, mat="BH_Horn", sides=4, twist=0.0, seed=0):
    """Jagged crystal shard (obsidian): a pyramid-tipped prism from base along direction."""
    d = normalize(direction)
    rng = np.random.default_rng(seed)
    up = (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)
    pts = [np.asarray(base, float) - d * width * 0.6, np.asarray(base, float) + d * length * 0.55,
           np.asarray(base, float) + d * length]
    w2 = width * (0.75 + 0.2 * rng.random())
    V, F = M.tube(pts, [(width, width * 0.8, 1.2), (w2, w2 * 0.8, 1.2), (0.001, 0.001, 1.2)], n=sides, up=up,
                  twist=[twist, twist + 0.3, twist])
    return M.Part(V, F, mat, name="shard")


def flame(base, height, r, mat="BH_Emissive", tongues=3, seed=1, n=7, axis=(0, 0, 1)):
    """Flame tip: a pointed teardrop plus flickering side tongues, rising along `axis` from base."""
    rng = np.random.default_rng(seed)
    parts = []
    prof = [(0.0, -r * 0.6), (r * 0.8, -r * 0.2), (r, r * 0.4), (r * 0.7, height * 0.45), (r * 0.25, height * 0.8),
            (0.0, height)]
    V, F = M.lathe(prof, n)
    parts.append(P(V, F, mat, "flame"))
    for k in range(tongues):
        a = 2 * math.pi * (k / tongues + 0.13 * rng.random())
        o = np.array([math.cos(a), math.sin(a), 0.0]) * r * 0.55
        h = height * (0.5 + 0.25 * rng.random())
        pts = [o + (0, 0, r * 0.2), o * 1.5 + (0, 0, h * 0.5), o * 1.1 + (0, 0, h)]
        V, F = M.tube(pts, [(r * 0.45, r * 0.45), (r * 0.3, r * 0.3), (0.001, 0.001)], n=5, up=(1, 0, 0))
        parts.append(P(V, F, mat, "tongue"))
    R = _align(np.array([0, 0, 1.0]), np.asarray(axis, float))
    for p in parts:
        p.rot(R).move(base)
    return parts


def jitter(part, amp, seed=1, axis_scale=(1, 1, 1)):
    return GK.jitter(part, amp, seed=seed, axis_scale=axis_scale)


def rock(center, size, mat="BH_Stone", seed=0, n=10, rings=6, amp=0.12):
    """Lumpy boulder: sphere scaled to size (3 radii) with low-frequency noise."""
    V, F = M.sphere(1.0, n, rings)
    rng = np.random.default_rng(seed)
    k = rng.normal(size=(4, 3))
    ph = rng.random(4) * 6.28
    Vn = V.copy()
    for i, v in enumerate(V):
        nv = normalize(v) if np.linalg.norm(v) > 1e-6 else v
        s = 1.0 + amp * sum(math.sin(3.0 * (nv @ k[j]) + ph[j]) for j in range(4)) / 2.0
        Vn[i] = v * s
    Vn = Vn * np.asarray(size, float) + np.asarray(center, float)
    return P(Vn, F, mat, "rock")
