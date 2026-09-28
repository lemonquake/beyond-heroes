"""Shared geometry for the Saltmouth Deeps monsters (bh-012, Builder A): drowned_deckhand, brinecaller, barnacle_hulk,
bell_warden (humanoids) and the reef_crawler creature. Pure geometry: every function returns bh_mesh.Part objects in
whatever space its inputs are given. Barnacles, kelp ribbons, branching coral, shell / pearl strings, sea-rot drips.

Palette family (each module sets its own PALETTE_COLORS): drowned greys and blue-greens, barnacle whites, kelp greens,
green-bronze, teal bioluminescent glow (BH_Emissive ~ (0.2, 0.95, 0.85))."""
import math
import numpy as np

import bh_mesh as M
from bh_body import M_align_z
from bh_math import normalize

TEAL = ((0.2, 0.95, 0.85), 0.0, 0.35, (0.2, 0.95, 0.85), 7.0, 1.0)


def P(V, F, mat, name="part"):
    return M.Part(V, F, mat, name=name)


def _frame(normal):
    n = normalize(normal)
    t1 = normalize(np.cross(n, (0.31, 0.53, 0.79)))
    t2 = np.cross(n, t1)
    return n, t1, t2


def barnacle(center, normal, r, shell="BH_Bone", hole="BH_Shadow", h=None, sides=6, tilt=None):
    """One acorn barnacle: a squat volcano cone (plated rim) with a dark aperture on top."""
    h = r * 0.9 if h is None else h
    prof = [(0.0, -0.25 * h), (r, -0.2 * h), (r * 0.98, 0.1 * h), (r * 0.72, 0.62 * h), (r * 0.5, h),
            (r * 0.3, h * 0.92), (0.0, h * 0.55)]
    V, F = M.lathe(prof, sides, a0=float(np.degrees(r * 97.0) % 60))
    V = np.asarray(V, float)
    n = normalize(normal if tilt is None else tilt)
    R = M_align_z(n, (0, 0, 1) if abs(n[2]) < 0.9 else (1, 0, 0))
    parts = [P(V @ R.T + np.asarray(center, float), F, shell, "barnacle")]
    if hole:
        V, F = M.sphere(r * 0.3, 5, 3, center=(0, 0, h * 0.8), scale=(1, 1, 0.5))
        parts.append(P(np.asarray(V) @ R.T + np.asarray(center, float), F, hole, "barnacle_hole"))
    return parts


def barnacle_cluster(center, normal, radius, count=9, seed=1, rmin=0.012, rmax=0.028, shell="BH_Bone",
                     hole="BH_Shadow", surface=None, crust=None, crust_mat="BH_Stone", sides=6):
    """Scatter barnacles on a disc (tangent plane of `normal`, radius `radius`). surface(p) -> (p_on_surface, normal)
    optionally snaps each point to the underlying body. crust: flat lumpy base patch under the cluster."""
    rng = np.random.default_rng(seed)
    n, t1, t2 = _frame(normal)
    c = np.asarray(center, float)
    out = []
    if crust:
        V, F = M.sphere(radius * 1.05, 9, 4, scale=(1.0, 1.0, 0.22))
        V = np.asarray(V, float)
        V[:, 2] += 0.0
        R = np.stack([t1, t2, n], 1)
        out.append(P(V @ R.T + c - n * radius * 0.08, F, crust_mat, "crust"))
    placed = []
    tries = 0
    while len(placed) < count and tries < count * 12:
        tries += 1
        a = rng.random() * 2 * math.pi
        d = radius * math.sqrt(rng.random()) * 0.9
        r = rmin + (rmax - rmin) * rng.random() ** 1.5 * (1.0 - 0.45 * d / radius)
        q = c + (t1 * math.cos(a) + t2 * math.sin(a)) * d
        if any(np.linalg.norm(q - p0) < (r + r0) * 0.85 for p0, r0 in placed):
            continue
        nn = n
        if surface is not None:
            q, nn = surface(q)
        placed.append((q, r))
        tl = normalize(nn + (rng.random(3) - 0.5) * 0.5)
        out += barnacle(q - nn * r * 0.15, nn, r, shell, hole, h=r * (0.7 + 0.5 * rng.random()), sides=sides, tilt=tl)
    return out


def kelp(top, down, length, width, mat, out=None, waves=2.5, amp=0.02, n=7, thick=0.004, seed=0.0, bladders=None,
         taper=0.35):
    """Hanging kelp ribbon: flat, wavy (side-to-side sway along the ribbon), narrowing to a torn tip. out = the
    surface normal the ribbon lies against (thickness direction). bladders: material for small air-bladder beads."""
    top = np.asarray(top, float)
    d = normalize(down)
    o = normalize(out if out is not None else np.cross(d, (1, 0, 0)))
    side = normalize(np.cross(d, o))
    pts, ws, ups = [], [], []
    for i in range(n):
        t = i / (n - 1)
        wig = amp * math.sin(t * math.pi * waves + seed) * t
        pts.append(top + d * length * t + side * wig + o * amp * 0.5 * math.sin(t * 5 + seed) * t)
        ws.append(width * (1.0 - (1 - taper) * t ** 1.3) * (0.8 + 0.2 * math.sin(t * 9 + seed)))
        ups.append(o)
    ws[-1] *= 0.4
    V, F = M.tube(pts, [(w / 2, thick / 2) for w in ws], n=4, up=[np.asarray(u) for u in ups], p=3.0)
    parts = [P(V, F, mat, "kelp")]
    if bladders:
        for t in (0.35, 0.7):
            i = t * (n - 1)
            i0 = int(i)
            q = np.asarray(pts[i0]) * (1 - (i - i0)) + np.asarray(pts[min(i0 + 1, n - 1)]) * (i - i0)
            V, F = M.sphere(width * 0.28, 6, 4, center=q + o * thick)
            parts.append(P(V, F, bladders, "bladder"))
    return parts


def coral(base, direction, length, r, mat, seed=1, depth=2, spread=34.0, n=5, tip=None, branches=2):
    """Branching staghorn coral: a tapered tube that forks `branches` ways `depth` times. tip: optional material for
    little glowing polyp beads on the branch ends."""
    rng = np.random.default_rng(seed)
    out = []

    def grow(b, d, ln, rr, lvl):
        d = normalize(d)
        mid = b + d * ln * 0.5 + normalize(np.cross(d, (0.2, 0.7, 0.3))) * ln * 0.06 * (rng.random() - 0.5)
        e = b + d * ln
        V, F = M.tube([b - d * rr * 0.5, mid, e], [(rr, rr), (rr * 0.8, rr * 0.8), (rr * 0.55, rr * 0.55)], n=n,
                      up=(0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0))
        out.append(P(V, F, mat, "coral"))
        if lvl >= depth:
            if tip:
                V, F = M.sphere(rr * 0.9, 5, 3, center=e)
                out.append(P(V, F, tip, "polyp"))
            else:
                V, F = M.sphere(rr * 0.62, 5, 3, center=e)
                out.append(P(V, F, mat, "coral_tip"))
            return
        _, t1, t2 = _frame(d)
        for k in range(branches):
            a = 2 * math.pi * (k / branches) + rng.random() * 1.2
            ax = t1 * math.cos(a) + t2 * math.sin(a)
            ang = math.radians(spread * (0.7 + 0.6 * rng.random()))
            nd = d * math.cos(ang) + ax * math.sin(ang)
            grow(e - d * rr * 0.3, nd, ln * (0.62 + 0.15 * rng.random()), rr * 0.7, lvl + 1)
    grow(np.asarray(base, float), np.asarray(direction, float), length, r, 0)
    return out


def bead_string(pts, r, mats, cord="BH_Leather", every=1, cord_r=0.0028, n=5):
    """A cord along pts with beads (shells / pearls) threaded on it; mats cycles through bead materials.
    Returns parts."""
    pts = [np.asarray(p, float) for p in pts]
    V, F = M.tube(pts, [(cord_r, cord_r)] * len(pts), n=4, up=(0, 0, 1))
    out = [P(V, F, cord, "cord")]
    for i, q in enumerate(pts[1:-1:every]):
        m = mats[i % len(mats)]
        rr = r * (1.25 if m != mats[0] else 1.0)
        V, F = M.sphere(rr, n, 3, center=q)
        out.append(P(V, F, m, "bead"))
    return out


def cone_shell(center, axis, r, length, mat, turns=2.2, sides=6, n=10):
    """Small spiral cone shell (whelk) for charms / conch accents: a tapering helical tube."""
    ax = normalize(axis)
    _, t1, t2 = _frame(ax)
    c = np.asarray(center, float)
    pts, prof = [], []
    for i in range(n):
        t = i / (n - 1)
        rad = r * (1 - t) * 0.55
        a = 2 * math.pi * turns * t
        pts.append(c + ax * length * t + (t1 * math.cos(a) + t2 * math.sin(a)) * rad)
        rr = r * (1 - 0.85 * t) + 0.001
        prof.append((rr, rr))
    V, F = M.tube(pts, prof, n=sides, up=tuple(t1))
    return [P(V, F, mat, "shell")]


def drips(pts, mat, ln=0.05, r=0.006, seed=0):
    """Short hanging sea-rot / slime drips below points (z down)."""
    rng = np.random.default_rng(seed)
    out = []
    for q in pts:
        q = np.asarray(q, float)
        l = ln * (0.5 + 0.7 * rng.random())
        V, F = M.tube([q + (0, 0, 0.004), q + (0, 0, -l * 0.6), q + (0, 0, -l)], [(r, r), (r * 0.7, r * 0.7),
                      (0.0012, 0.0012)], n=4, up=(1, 0, 0))
        out.append(P(V, F, mat, "drip"))
        V, F = M.sphere(r * 1.1, 4, 3, center=q + (0, 0, -l))
        out.append(P(V, F, mat, "drop"))
    return out


def import_path_md5(res_path):
    import hashlib
    return hashlib.md5(res_path.encode()).hexdigest()
