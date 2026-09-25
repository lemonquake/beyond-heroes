"""Rocks, cliffs, rubble, trees (bark tubes + alpha leaf cards), bushes, grass, fern, mushrooms, roots, logs."""
import math
import os

import bpy
from mathutils import Vector, Quaternion, Matrix, noise as mnoise

from kit import *  # noqa
from masonry import *  # noqa
from registry import asset

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ATLAS = os.path.join(ROOT, "game", "assets", "textures", "leaves_atlas.png")

# leaves_atlas quadrants as UV rects (u0, v0, u1, v1). Image top-left quadrant = high V.
QUAD = {0: (0.0, 0.5, 0.5, 1.0), 1: (0.5, 0.5, 1.0, 1.0), 2: (0.0, 0.0, 0.5, 0.5), 3: (0.5, 0.0, 1.0, 0.5)}
_opaque = {}


def atlas_opaque_uv(q):
    """UV of a texel deep inside an opaque leaf of quadrant q (for mesh leaves that must sample solid colour)."""
    if q in _opaque:
        return _opaque[q]
    import numpy as np
    im = bpy.data.images.load(ATLAS, check_existing=True)
    w, h = im.size
    px = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(px)
    a = px.reshape(h, w, 4)[..., 3] > 0.5  # row 0 = bottom (v=0)
    c = np.cumsum(np.cumsum(a.astype(np.int32), 0), 1)
    k = 6
    s = c[2 * k:, 2 * k:] - c[:-2 * k, 2 * k:] - c[2 * k:, :-2 * k] + c[:-2 * k, :-2 * k]
    full = s >= (2 * k) ** 2
    u0, v0, u1, v1 = QUAD[q]
    ys, xs = np.nonzero(full)
    xs = xs + k
    ys = ys + k
    cu, cv = (u0 + u1) / 2 * w, (v0 * 0.7 + v1 * 0.3) * h
    inq = (xs >= u0 * w) & (xs < u1 * w) & (ys >= v0 * h) & (ys < v1 * h)
    xs, ys = xs[inq], ys[inq]
    d = (xs - cu) ** 2 + (ys - cv) ** 2
    i = int(np.argmin(d))
    _opaque[q] = ((xs[i] + 0.5) / w, (ys[i] + 0.5) / h)
    return _opaque[q]


def set_uv_point(t, uv, spread=0.004):
    uvl = t.loops.layers.uv.active
    for f in t.faces:
        for i, l in enumerate(f.loops):
            l[uvl].uv = (uv[0] + spread * ((i % 2) - 0.5), uv[1] + spread * ((i // 2 % 2) - 0.5))


def rand_unit(r):
    while True:
        v = Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1)))
        if 0.01 < v.length <= 1:
            return v.normalized()


def align_z(d, roll=0.0):
    """Matrix rotating local +Z onto direction d with extra roll about it."""
    q = d.normalized().to_track_quat("Z", "Y")
    return q.to_matrix().to_4x4() @ Matrix.Rotation(roll, 4, "Z")


# ---------------------------------------------------------------------------------------------------------------
# rocks
def rock_piece(k, size, target, pos=(0, 0, 0), rz=0.0, mat="BH_Stone", tint=(0.75, 0.92), moss=True, cuts=9,
               flat_top=None, sink=0.0, tilt=(0, 0), amp=0.05):
    r = k.r
    t = rock(r, size, cuts=cuts, subd=3, noise_amp=amp, seed_off=r.uniform(0, 50), target=None)
    if flat_top is not None:
        top = max(v.co.z for v in t.verts)
        slice_plane(t, (0, 0, top * flat_top), (r.uniform(-0.08, 0.08), r.uniform(-0.08, 0.08), 1))
    n = len(t.faces)
    if n > target:
        t = decimate(t, target / n)
    M = TRS(pos[0], pos[1], pos[2] - sink, tilt[0], tilt[1], rz)
    k.put(t, mat, M=M, tint=r.uniform(*tint), smooth=38, mat_fn=moss_fn(k, 0.8, 0.9, 0.1) if moss else None)


@asset("rock_small", "nature", col=False)
def rock_small(k):
    rock_piece(k, (0.34, 0.28, 0.24), 150, moss=False)
    rock_piece(k, (0.12, 0.1, 0.08), 40, pos=(0.36, -0.1, 0), rz=40, moss=False)
    rock_piece(k, (0.09, 0.08, 0.06), 30, pos=(-0.3, 0.22, 0), rz=10, moss=False)


@asset("rock_medium", "nature")
def rock_medium(k):
    rock_piece(k, (0.85, 0.7, 0.6), 520)
    rock_piece(k, (0.4, 0.35, 0.3), 160, pos=(0.85, -0.35, 0), rz=30, tilt=(8, 0))
    rock_piece(k, (0.14, 0.12, 0.1), 40, pos=(-0.7, -0.5, 0), moss=False)
    k.col_box(1.6, 1.3, 1.0, T(0, 0, 0.5))


@asset("rock_large", "nature")
def rock_large(k):
    rock_piece(k, (1.7, 1.35, 1.35), 1100, flat_top=0.9)
    rock_piece(k, (1.0, 0.85, 0.8), 450, pos=(1.55, -0.8, 0), rz=35, tilt=(6, -5))
    rock_piece(k, (0.6, 0.5, 0.45), 200, pos=(-1.5, -0.9, 0), rz=70)
    rock_piece(k, (0.2, 0.16, 0.14), 50, pos=(0.4, -1.5, 0), moss=False)
    rock_piece(k, (0.15, 0.13, 0.1), 40, pos=(-0.8, -1.4, 0), moss=False)
    k.col_box(3.2, 2.5, 2.2, T(0, 0, 1.1))
    k.col_box(1.8, 1.6, 1.3, TRS(1.55, -0.8, 0.65, 0, 0, 35))


@asset("cliff_a", "nature")
def cliff_a(k):
    r = k.r
    tiers = [  # (z, y, count, size ranges, flat)
        (0.0, 0.0, 4, (1.3, 1.7), (1.3, 1.6), (1.7, 2.1)),
        (2.5, 0.8, 4, (1.2, 1.5), (1.2, 1.5), (1.4, 1.8)),
        (4.4, 1.6, 3, (1.2, 1.6), (1.1, 1.4), (1.3, 1.6)),
    ]
    W = 8.0
    for ti, (z, y, n, sx, sy, sz) in enumerate(tiers):
        xs = [-W / 2 + W * (i + 0.5) / n + r.uniform(-0.3, 0.3) for i in range(n)]
        for x in xs:
            size = (r.uniform(*sx), r.uniform(*sy), r.uniform(*sz))
            rock_piece(k, size, 520, pos=(x, y + r.uniform(-0.25, 0.25), z - 0.15 * (ti > 0)), rz=r.uniform(-25, 25),
                       flat_top=0.82, cuts=10, tint=(0.7, 0.88), sink=0.05)
    # scree at the foot
    for i in range(9):
        s = r.uniform(0.15, 0.4)
        rock_piece(k, (s, s * 0.8, s * 0.6), 40, pos=(r.uniform(-4, 4), r.uniform(-1.9, -1.3), 0), rz=r.uniform(0, 360),
                   moss=False, tint=(0.7, 0.85))
    k.col_box(8.4, 3.0, 3.0, T(0, 0.0, 1.5))
    k.col_box(8.0, 2.6, 2.2, T(0, 0.8, 3.6))
    k.col_box(7.0, 2.4, 2.2, T(0, 1.6, 5.4))
    return dict(damp=0.25, damp_h=1.5)


@asset("cliff_b", "nature")
def cliff_b(k):
    """Columnar basalt-like face ~9.5 m tall."""
    r = k.r
    cols = []
    x = -2.8
    while x < 2.9:
        rad = r.uniform(0.45, 0.7)
        cols.append((x + rad, rad))
        x += rad * 1.75
    for i, (cx, rad) in enumerate(cols):
        h = 9.5 - abs(cx) * 0.9 + r.uniform(-1.4, 0.6)
        t = cyl(rad, h, r.choice((5, 6, 6, 7)), r2=rad * 0.9)
        slice_plane(t, (0, 0, h - rad * 0.4), (r.uniform(-0.6, 0.6), r.uniform(-0.6, 0.6), 1))
        chip(t, r, 3, 0.18)
        # horizontal joints: break the column into drums with slight offsets
        cy = r.uniform(-0.2, 0.3)
        k.put(t, "BH_Stone", M=TRS(cx, cy, 0, r.uniform(-3, 3), r.uniform(-3, 3), r.uniform(0, 60)),
              tint=r.uniform(0.66, 0.84), smooth=None, mat_fn=moss_fn(k, 0.85, 1.4, 0.2))
        # joint bands
        for jz in (r.uniform(2, 3.5), r.uniform(5, 6.5)):
            if jz < h - 0.8:
                k.put(cyl(rad * 1.02, 0.06, 7), "BH_StoneDark", M=TRS(cx, cy, jz, 0, 0, r.uniform(0, 60)), tint=0.4)
    # back mass so the face is not see-through
    rock_piece(k, (3.4, 1.4, 4.2), 700, pos=(0, 1.5, 0), flat_top=0.9, tint=(0.6, 0.75))
    # fallen columns / talus
    for i in range(3):
        rad = r.uniform(0.35, 0.5)
        L = r.uniform(1.2, 2.2)
        t = cyl(rad, L, 6)
        chip(t, r, 3, 0.15)
        k.put(t, "BH_Stone", M=TRS(r.uniform(-2.5, 2.5), r.uniform(-2.2, -1.2), rad * 0.8, 90, 0, r.uniform(-60, 60)),
              tint=r.uniform(0.66, 0.82))
    for i in range(10):
        s = r.uniform(0.12, 0.35)
        rock_piece(k, (s, s * 0.8, s * 0.6), 40, pos=(r.uniform(-3, 3), r.uniform(-2.4, -0.9), 0), rz=r.uniform(0, 360),
                   moss=False, tint=(0.7, 0.85))
    k.col_box(6.4, 2.6, 8.0, T(0, 0.4, 4.0))
    return dict(damp=0.25, damp_h=1.5)


@asset("rubble_pile", "nature")
def rubble_pile(k):
    r = k.r
    R_ = 1.3
    for i in range(34):
        a = r.uniform(0, 2 * math.pi)
        d = R_ * math.sqrt(r.random())
        x, y = math.cos(a) * d, math.sin(a) * d
        z = 0.85 * (1 - (d / R_) ** 2) * r.uniform(0.6, 1.0)
        if r.random() < 0.55:
            t = box(r.uniform(0.3, 0.6), r.uniform(0.25, 0.4), r.uniform(0.2, 0.32), bev=0.03)
            chip(t, r, r.randint(1, 3), 0.08)
            jitter(t, r, 0.01)
            k.put(t, r.choice(("BH_StoneDark", "BH_StoneDark", "BH_Stone")),
                  M=TRS(x, y, z * 0.85 + 0.1, r.uniform(-35, 35), r.uniform(-35, 35), r.uniform(0, 180)),
                  tint=r.uniform(0.7, 0.92))
        else:
            s = r.uniform(0.12, 0.3)
            rock_piece(k, (s, s * 0.8, s * 0.7), 50, pos=(x, y, z * 0.8), rz=r.uniform(0, 360), moss=False,
                       mat="BH_StoneDark")
    # dusty mound core
    t = ico(1.0, 2)
    for v in t.verts:
        v.co = Vector((v.co.x * R_ * 1.05, v.co.y * R_ * 0.95, max(v.co.z, -0.02) * 0.6))
    ndisp(t, 2.0, 0.08, k.noff)
    k.put(t, "BH_Dirt", tint=0.8, smooth=60)
    # broken beam
    t = box(1.8, 0.2, 0.22, bev=0.02)
    chip(t, r, 3, 0.08)
    k.put(t, "BH_WoodDark", M=TRS(0.2, 0.3, 0.55, 0, -18, 30), tint=0.85)
    k.col_mesh(cyl(R_, 0.7, 8, r2=R_ * 0.35))


@asset("rubble_spill", "nature")
def rubble_spill(k):
    """Debris fan spilling from a broken wall line (wall at y=0, fan toward -Y)."""
    r = k.r
    for i in range(46):
        d = r.random() ** 1.3 * 3.2
        a = math.radians(r.uniform(-70, 70))
        x = math.sin(a) * d * 1.1 + r.uniform(-0.6, 0.6)
        y = -math.cos(a) * d
        s = lerp(1.0, 0.35, d / 3.2)
        z = max(0.0, 0.9 * (1 - d / 2.2)) * r.uniform(0.4, 1.0)
        if r.random() < 0.7:
            t = box(r.uniform(0.35, 0.75) * s, r.uniform(0.3, 0.45) * s, r.uniform(0.22, 0.35) * s, bev=0.03)
            chip(t, r, r.randint(1, 3), 0.07)
            jitter(t, r, 0.01)
            k.put(t, "BH_StoneDark", M=TRS(x, y, z + 0.12 * s, r.uniform(-30, 30), r.uniform(-30, 30), r.uniform(0, 180)),
                  tint=r.uniform(0.7, 0.92))
        else:
            q = r.uniform(0.08, 0.2)
            rock_piece(k, (q, q * 0.8, q * 0.6), 36, pos=(x, y, z * 0.9), rz=r.uniform(0, 360), moss=False,
                       mat="BH_StoneDark")
    t = ico(1.0, 2)
    for v in t.verts:
        yy = v.co.y * 1.9 - 1.0
        v.co = Vector((v.co.x * 2.0 * (0.6 + 0.4 * (1 - abs(yy) / 3)), yy, max(v.co.z, -0.02) * 0.55 * (1 - (-yy) / 3.2)))
    ndisp(t, 2.0, 0.06, k.noff)
    k.put(t, "BH_Dirt", tint=0.75, smooth=60)
    k.col_mesh(hexa([(-2, -2.6, 0), (2, -2.6, 0), (2.2, 0.2, 0), (-2.2, 0.2, 0),
                     (-1, -2.0, 0.15), (1, -2.0, 0.15), (1.6, 0.2, 0.9), (-1.6, 0.2, 0.9)]))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# trees
class TreeP:
    def __init__(self, **kw):
        self.depth = 3
        self.children = [5, 3, 2, 0]
        self.lscale = [0.55, 0.6, 0.6]
        self.rscale = [0.55, 0.6, 0.65]
        self.angle = [(35, 60), (30, 55), (25, 50)]
        self.up = [0.05, 0.08, 0.1, 0.1]
        self.wobble = [0.15, 0.3, 0.35, 0.4]
        self.segs = [7, 5, 4, 3]
        self.rings = [10, 7, 5, 4]
        self.taper = [0.45, 0.35, 0.3, 0.25]
        self.twist = 0.0
        self.tmin = 0.35
        self.leaves = None  # (quads, size range, per tip, extra mid)
        self.gravity = [0, 0, 0, 0]
        self.__dict__.update(kw)


def grow(k, p0, d, L, r0, depth, P, tips, mids):
    r = k.r
    n = P.segs[depth]
    pts = [p0.copy()]
    rads = [r0]
    dirs = [d.copy()]
    dc = d.copy()
    for i in range(1, n + 1):
        dc = (dc + rand_unit(r) * P.wobble[depth] + Vector((0, 0, P.up[depth] - P.gravity[depth]))).normalized()
        pts.append(pts[-1] + dc * (L / n))
        rads.append(max(0.008, r0 * (1 - (1 - P.taper[depth]) * i / n)))
        dirs.append(dc.copy())
    t = tube(pts, rads, P.rings[depth], cap_start=False, cap_end=True, uv_tile=1.0)
    k.put(t, "BH_Bark", uv="keep", smooth=75, tint=r.uniform(0.85, 1.0))
    if depth < P.depth:
        nc = P.children[depth]
        for c in range(nc):
            tt = r.uniform(P.tmin, 0.95) if nc > 1 else 0.9
            fi = tt * n
            i0 = min(int(fi), n - 1)
            f = fi - i0
            bp = pts[i0].lerp(pts[i0 + 1], f)
            br = lerp(rads[i0], rads[i0 + 1], f)
            bd = dirs[i0 + 1]
            ang = math.radians(r.uniform(*P.angle[depth]))
            axis = bd.orthogonal().normalized()
            axis.rotate(Quaternion(bd, r.uniform(0, 2 * math.pi) + c * 2.4))
            nd = bd.copy()
            nd.rotate(Quaternion(axis, ang))
            grow(k, bp - nd * br * 0.5, nd, L * P.lscale[depth] * r.uniform(0.8, 1.15), br * P.rscale[depth] + 0.004,
                 depth + 1, P, tips, mids)
    else:
        tips.append((pts[-1], dirs[-1], L))
    if depth >= P.depth - 1:
        mids.append((pts[len(pts) // 2], dirs[len(pts) // 2], L))


def leaf_cluster(k, pos, d, size, quad, crossed=True, up_bias=0.45, tint=(0.8, 1.0)):
    r = k.r
    dd = (d.normalized() + Vector((0, 0, up_bias)) + rand_unit(r) * 0.35).normalized()
    roll = r.uniform(0, math.pi)
    for c in range(2 if crossed else 1):
        t = card(size, size, uv=QUAD[quad], bend=size * 0.18, rows=2)
        M = T(*(pos - dd * size * 0.2)) @ align_z(dd, roll + c * math.pi / 2)
        k.put(t, "BH_Leaves", M=M, uv="keep", smooth=80, tint=r.uniform(*tint))


def roots_flare(k, base_r, n, reach=(0.9, 1.6), z0=0.35, rad=(0.12, 0.2), under=0.15):
    r = k.r
    for i in range(n):
        a = 2 * math.pi * i / n + r.uniform(-0.3, 0.3)
        L = r.uniform(*reach)
        pts, rads = [], []
        for j in range(6):
            t = j / 5
            dist = base_r * 0.6 + L * t
            z = z0 * (1 - t) ** 1.6 - under * t ** 2
            pts.append(Vector((math.cos(a) * dist, math.sin(a) * dist, z)))
            rads.append(lerp(r.uniform(*rad), 0.03, t ** 0.8))
        k.put(tube(pts, rads, 7, cap_start=False, cap_end=True, uv_tile=1.0), "BH_Bark", uv="keep", smooth=75,
              tint=r.uniform(0.8, 0.95))


@asset("tree_dead_a", "nature")
def tree_dead_a(k):
    P = TreeP(depth=3, children=[6, 3, 2], lscale=[0.55, 0.55, 0.55], rscale=[0.5, 0.55, 0.6],
              angle=[(40, 65), (30, 55), (25, 50)], wobble=[0.12, 0.35, 0.4, 0.45], up=[0.05, 0.05, 0.1, 0.12],
              segs=[8, 5, 4, 3], rings=[10, 6, 5, 4], tmin=0.4)
    tips, mids = [], []
    grow(k, Vector((0, 0, -0.1)), Vector((0.05, 0.02, 1)).normalized(), 5.2, 0.3, 0, P, tips, mids)
    roots_flare(k, 0.3, 5)
    # broken snag top splinters
    r = k.r
    k.col_box(0.7, 0.7, 5.0, T(0, 0, 2.5))
    return dict()


@asset("tree_dead_b", "nature")
def tree_dead_b(k):
    r = k.r
    P = TreeP(depth=3, children=[3, 3, 2], lscale=[0.6, 0.55, 0.5], rscale=[0.55, 0.55, 0.6],
              angle=[(25, 45), (35, 60), (30, 55)], wobble=[0.2, 0.4, 0.45, 0.5], up=[0.0, 0.02, 0.05, 0.08],
              segs=[7, 5, 4, 3], rings=[10, 6, 5, 4], tmin=0.55, gravity=[0, 0.08, 0.1, 0.1])
    tips, mids = [], []
    lean = Vector((0.45, 0.1, 1)).normalized()
    grow(k, Vector((0, 0, -0.1)), lean, 4.2, 0.34, 0, P, tips, mids)
    roots_flare(k, 0.34, 6, reach=(1.0, 1.8))
    # split / broken top: splinter cones
    top = Vector((0, 0, -0.1)) + lean * 4.2
    k.col_box(0.8, 0.8, 4.0, TRS(0.8, 0.2, 2.0, 0, 20, 0))
    return dict()


@asset("tree_oak_twisted", "nature")
def tree_oak_twisted(k):
    r = k.r
    P = TreeP(depth=3, children=[4, 3, 3], lscale=[0.7, 0.6, 0.55], rscale=[0.6, 0.55, 0.6],
              angle=[(35, 55), (30, 55), (25, 50)], wobble=[0.22, 0.3, 0.35, 0.4], up=[0.1, 0.05, 0.08, 0.1],
              segs=[6, 5, 4, 3], rings=[12, 8, 5, 4], tmin=0.55, taper=[0.5, 0.4, 0.3, 0.25])
    tips, mids = [], []
    grow(k, Vector((0, 0, -0.1)), Vector((-0.1, 0.12, 1)).normalized(), 3.4, 0.5, 0, P, tips, mids)
    roots_flare(k, 0.5, 7, reach=(1.0, 1.9), z0=0.5, rad=(0.16, 0.26))
    for (p, d, L) in tips:
        leaf_cluster(k, p, d, r.uniform(1.5, 2.1), r.choice((0, 0, 1)), up_bias=0.6)
    for (p, d, L) in mids[::2]:
        leaf_cluster(k, p, d, r.uniform(1.2, 1.7), r.choice((0, 1)), up_bias=0.6, tint=(0.7, 0.9))
    k.col_box(1.1, 1.1, 3.0, T(0, 0, 1.5))
    return dict()


@asset("tree_pine", "nature")
def tree_pine(k):
    r = k.r
    H = 9.5
    pts = []
    for i in range(9):
        z = H * i / 8 - 0.1
        pts.append(Vector((r.uniform(-0.04, 0.04) * i * 0.3, r.uniform(-0.04, 0.04) * i * 0.3, z)))
    rads = [lerp(0.3, 0.03, (i / 8) ** 0.9) for i in range(9)]
    k.put(tube(pts, rads, 10, cap_start=False, uv_tile=1.0), "BH_Bark", uv="keep", smooth=75, tint=0.9)
    roots_flare(k, 0.3, 5, reach=(0.6, 1.0), z0=0.3, rad=(0.1, 0.14))
    z = 1.9
    wi = 0
    while z < H - 0.6:
        f = (z - 1.9) / (H - 2.5)
        L = lerp(2.4, 0.5, f) * r.uniform(0.85, 1.1)
        nb = 5 if f < 0.7 else 4
        a0 = r.uniform(0, 2 * math.pi)
        for b in range(nb):
            a = a0 + 2 * math.pi * b / nb + r.uniform(-0.25, 0.25)
            d = Vector((math.cos(a), math.sin(a), r.uniform(-0.15, 0.1)))
            p0 = Vector((0, 0, z))
            p1 = p0 + d * L * 0.5 + Vector((0, 0, -0.1 * L))
            p2 = p0 + d * L + Vector((0, 0, -0.35 * L + 0.2))
            k.put(tube([p0, p1, p2], [0.05 * (1 - f * 0.5), 0.03, 0.012], 4, cap_start=False, uv_tile=1.0), "BH_Bark",
                  uv="keep", smooth=75, tint=0.8)
            for s in (0.35, 0.75):
                p = p0.lerp(p2, s)
                size = L * r.uniform(0.75, 0.95) + 0.3
                dd = (d + Vector((0, 0, -0.25))).normalized()
                # near-horizontal needle cards: card up-axis along the branch, face mostly up
                t = card(size * 0.9, size, uv=QUAD[2], bend=-size * 0.15, rows=2)
                M = T(*(p - dd * size * 0.25)) @ align_z(dd, math.pi / 2 + r.uniform(-0.3, 0.3))
                k.put(t, "BH_Leaves", M=M, uv="keep", smooth=80, tint=r.uniform(0.75, 1.0))
        z += r.uniform(0.55, 0.75)
        wi += 1
    for i in range(3):
        leaf_cluster(k, Vector((0, 0, H - 0.9 + i * 0.3)), Vector((0, 0, 1)), 1.0 - i * 0.2, 2, up_bias=2.0)
    k.col_box(0.7, 0.7, 5.0, T(0, 0, 2.5))
    return dict()


@asset("bush_a", "nature", col=False)
def bush_a(k):
    r = k.r
    P = TreeP(depth=1, children=[3, 0], lscale=[0.6], rscale=[0.6], angle=[(25, 50)], segs=[4, 3], rings=[5, 4],
              up=[0.1, 0.1], wobble=[0.3, 0.3])
    for i in range(4):
        a = i * 1.6
        tips, mids = [], []
        grow(k, Vector((0, 0, -0.05)), Vector((math.cos(a) * 0.5, math.sin(a) * 0.5, 1)).normalized(), 0.8, 0.035, 0,
             P, tips, mids)
    for i in range(22):
        a = r.uniform(0, 2 * math.pi)
        el = r.uniform(0.1, 1.2)
        d = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
        p = Vector((0, 0, 0.45)) + Vector((d.x * 0.6, d.y * 0.6, d.z * 0.4))
        leaf_cluster(k, p, d, r.uniform(0.7, 1.0), r.choice((0, 1, 1)), crossed=False, up_bias=0.5)


@asset("bush_b", "nature", col=False)
def bush_b(k):
    """Dry thorny bush with autumn clusters."""
    r = k.r
    P = TreeP(depth=2, children=[4, 2, 0], lscale=[0.55, 0.5], rscale=[0.6, 0.6], angle=[(30, 60), (30, 60)],
              segs=[4, 3, 3], rings=[5, 4, 3], up=[0.05, 0.05, 0.1], wobble=[0.35, 0.45, 0.5])
    for i in range(5):
        a = i * 1.3 + r.uniform(-0.2, 0.2)
        tips, mids = [], []
        grow(k, Vector((0, 0, -0.05)), Vector((math.cos(a) * 0.7, math.sin(a) * 0.7, 1)).normalized(),
             r.uniform(0.9, 1.3), 0.03, 0, P, tips, mids)
        for (p, d, L) in tips[::2]:
            leaf_cluster(k, p, d, r.uniform(0.5, 0.75), 3, crossed=False, up_bias=0.3)
    # thorns
    for i in range(30):
        a = r.uniform(0, 2 * math.pi)
        p = Vector((math.cos(a) * r.uniform(0.2, 0.6), math.sin(a) * r.uniform(0.2, 0.6), r.uniform(0.2, 0.9)))
        k.put(cyl(0.008, 0.07, 3, r2=0.0), "BH_Bark", M=T(*p) @ align_z(rand_unit(r)), tint=0.7)


@asset("grass_clump", "nature", col=False)
def grass_clump(k):
    r = k.r
    n = 9
    for i in range(n):
        a = i * 180.0 / n + r.uniform(-8, 8)
        h = r.uniform(0.45, 0.8)
        w = r.uniform(0.35, 0.55)
        dry = r.random() < 0.25
        u0 = r.uniform(0.52, 0.72) if dry else r.uniform(0.02, 0.22)
        uw = r.uniform(0.18, 0.26)
        t = card(w, h, uv=(u0, 0.0, u0 + uw, 0.98), bend=h * r.uniform(0.05, 0.2), rows=2)
        k.put(t, "BH_Grass", M=TRS(r.uniform(-0.08, 0.08), r.uniform(-0.08, 0.08), -0.02, r.uniform(-8, 8), 0, a),
              uv="keep", smooth=80, tint=r.uniform(0.8, 1.0))


@asset("fern", "nature", col=False)
def fern(k):
    r = k.r
    uvp = atlas_opaque_uv(0)
    nf = 10
    for f in range(nf):
        a = 2 * math.pi * f / nf + r.uniform(-0.2, 0.2)
        L = r.uniform(0.7, 1.05)
        rise = r.uniform(0.3, 0.5)
        dirh = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-math.sin(a), math.cos(a), 0))
        pts = []
        for j in range(8):
            t = j / 7
            pts.append(dirh * (L * t) + Vector((0, 0, rise * math.sin(t * math.pi * 0.75) - 0.25 * t * t + 0.02)))
        k.put(tube(pts, [0.012 * (1 - j / 8) + 0.003 for j in range(8)], 3, uv_tile=1.0), "BH_Leaves", uv="keep",
              tint=0.6)
        # leaflets
        nl = 11
        for j in range(1, nl):
            t = j / nl
            fi = t * 7
            i0 = min(int(fi), 6)
            p = pts[i0].lerp(pts[i0 + 1], fi - i0)
            tang = (pts[i0 + 1] - pts[i0]).normalized()
            ll = 0.2 * math.sin(math.pi * min(1.0, t * 1.15)) + 0.03
            for sgn in (-1, 1):
                sd = side * sgn
                tip = p + sd * ll + tang * ll * 0.35 + Vector((0, 0, -ll * 0.25))
                b0 = p - tang * 0.018
                b1 = p + tang * 0.018
                mid = p + sd * ll * 0.5 + tang * ll * 0.12 + Vector((0, 0, -ll * 0.05))
                tt = tb()
                vs = [tt.verts.new(b0), tt.verts.new(mid + tang * 0.02 - sd * 0.0), tt.verts.new(tip),
                      tt.verts.new(mid - tang * 0.025)]
                tt.faces.new(vs if sgn > 0 else vs[::-1])
                set_uv_point(tt, uvp)
                k.put(tt, "BH_Leaves", uv="keep", smooth=80, tint=r.uniform(0.75, 1.0) * lerp(0.8, 1.0, t))


@asset("mushrooms", "nature", col=False)
def mushrooms(k):
    r = k.r
    spots = []
    for i in range(8):
        a = r.uniform(0, 2 * math.pi)
        d = r.uniform(0.0, 0.35)
        spots.append((math.cos(a) * d, math.sin(a) * d, r.uniform(0.06, 0.28)))
    spots.sort(key=lambda s: -s[2])
    for i, (x, y, h) in enumerate(spots):
        rs = h * 0.16
        rc = h * r.uniform(0.45, 0.65)
        lean = (r.uniform(-12, 12), r.uniform(-12, 12))
        stem = lathe([(rs * 1.3, 0), (rs, h * 0.3), (rs * 0.85, h * 0.9), (rs * 0.8, h)], 8, uv_tile=0.5)
        k.put(stem, "BH_Bone", M=TRS(x, y, -0.01, lean[0], lean[1], 0), uv="keep", smooth=70, tint=0.95)
        red = i % 3 == 0
        prof = [(rs * 0.8, h * 0.93), (rc * 0.95, h * 0.95), (rc, h * 1.0), (rc * 0.85, h * 1.18), (rc * 0.45, h * 1.32),
                (0.0, h * 1.36)]
        cap = lathe(prof, 12, cap_bot=True, uv_tile=0.5)
        k.put(cap, "BH_ClothRed" if red else "BH_Wood", M=TRS(x, y, -0.01, lean[0], lean[1], 0), uv="keep", smooth=70,
              tint=r.uniform(0.75, 1.0))
        if red:
            for j in range(5):
                a = r.uniform(0, 2 * math.pi)
                el = r.uniform(0.3, 1.0)
                p = Vector((math.cos(a) * rc * 0.7 * math.cos(el), math.sin(a) * rc * 0.7 * math.cos(el), h * 1.12 + h * 0.2 * math.sin(el)))
                dot = ico(rc * 0.09, 1)
                k.put(dot, "BH_Bone", M=TRS(x, y, -0.01, lean[0], lean[1], 0) @ T(*p), tint=1.0)
    # small leaf litter mound
    t = ico(1.0, 2)
    for v in t.verts:
        v.co = Vector((v.co.x * 0.5, v.co.y * 0.45, max(v.co.z, 0) * 0.06))
    k.put(t, "BH_Dirt", tint=0.8, smooth=60)


@asset("roots", "nature", col=False)
def roots(k):
    r = k.r
    for i in range(7):
        a = 2 * math.pi * i / 7 + r.uniform(-0.3, 0.3)
        L = r.uniform(1.2, 2.2)
        big = i == 0
        pts, rads = [], []
        n = 9
        h = r.uniform(0.18, 0.35) * (1.4 if big else 1.0)
        for j in range(n):
            t = j / (n - 1)
            d = 0.2 + L * t
            z = h * math.sin(t * math.pi) - 0.12 + 0.05 * math.sin(t * 9 + i)
            wob = 0.15 * math.sin(t * 5 + i * 2)
            pts.append(Vector((math.cos(a + wob) * d, math.sin(a + wob) * d, z)))
            rads.append(lerp(0.16 if big else r.uniform(0.07, 0.11), 0.025, t))
        k.put(tube(pts, rads, 6, uv_tile=1.0), "BH_Bark", uv="keep", smooth=75, tint=r.uniform(0.8, 0.95))
        # side rootlets
        for j in range(2):
            s = r.uniform(0.3, 0.8)
            p = pts[int(s * (n - 1))]
            b = Vector((math.cos(a + 1.2 * (1 if j else -1)), math.sin(a + 1.2 * (1 if j else -1)), 0))
            k.put(tube([p, p + b * 0.4 + Vector((0, 0, 0.08)), p + b * 0.75 + Vector((0, 0, -0.1))], [0.04, 0.025, 0.01], 4,
                       uv_tile=1.0), "BH_Bark", uv="keep", smooth=75, tint=0.85)
    t = ico(1.0, 2)
    for v in t.verts:
        v.co = Vector((v.co.x * 0.6, v.co.y * 0.6, max(v.co.z, -0.01) * 0.12))
    ndisp(t, 3, 0.03, k.noff)
    k.put(t, "BH_Dirt", tint=0.8, smooth=60)


def bracket_fungus(k, p, d, s):
    t = lathe([(s, 0), (s * 0.95, s * 0.12), (s * 0.6, s * 0.22), (0.0, s * 0.25)], 8, arc=math.pi, cap_bot=False,
              cap_top=False)
    # close the half disc with a back wall
    bmesh.ops.holes_fill(t, edges=[e for e in t.edges if e.is_boundary], sides=0)
    ang = math.atan2(d.y, d.x)
    k.put(t, "BH_Wood", M=T(*p) @ R(0, 0, math.degrees(ang) - 90), tint=1.0)


@asset("log_fallen", "nature")
def log_fallen(k):
    r = k.r
    L = 5.0
    n = 12
    pts, rads = [], []
    for i in range(n):
        t = i / (n - 1)
        pts.append(Vector((-L / 2 + L * t, 0.15 * math.sin(t * 3), 0.33 + 0.03 * math.sin(t * 7))))
        rads.append(lerp(0.4, 0.3, t))
    t = tube(pts, rads, 12, cap_start=False, cap_end=False, uv_tile=1.0)
    ndisp(t, 2.5, 0.05, k.noff)
    k.put(t, "BH_Bark", uv="keep", smooth=70, tint=0.9, mat_fn=moss_fn(k, 0.55, 1.2, 0.15))
    # cut end (rings) at start
    k.put(cyl(0.4, 0.04, 12), "BH_Wood", M=TRS(pts[0].x, pts[0].y, pts[0].z, 0, -90, 0), uv="planar_z", tile=0.8,
          tint=1.0)
    # jagged broken end: splinter cones around the rim
    e = pts[-1]
    for j in range(9):
        a = 2 * math.pi * j / 9
        h = r.uniform(0.1, 0.45)
        rr = rads[-1] * 0.8
        k.put(cyl(0.07, h, 4, r2=0.0), "BH_Wood",
              M=T(e.x - 0.02, e.y + math.cos(a) * rr, e.z + math.sin(a) * rr) @ R(0, 90, 0), tint=r.uniform(0.7, 0.9))
    k.put(cyl(rads[-1] * 0.9, 0.05, 10), "BH_WoodDark", M=TRS(e.x - 0.03, e.y, e.z, 0, 90, 0), tint=0.6)
    # branch stubs
    for s, a in ((0.3, 60), (0.55, -110), (0.75, 20)):
        i = int(s * (n - 1))
        p = pts[i]
        d = Vector((0.3, math.cos(math.radians(a)), math.sin(math.radians(a)))).normalized()
        k.put(tube([p, p + d * 0.55, p + d * 0.8], [0.12, 0.08, 0.05], 6, uv_tile=1.0), "BH_Bark", uv="keep", smooth=70,
              tint=0.85)
    for s in (0.2, 0.45, 0.62):
        i = int(s * (n - 1))
        p = pts[i] + Vector((0, -rads[i] * 0.95, -0.05))
        bracket_fungus(k, p, Vector((0, -1, 0)), r.uniform(0.1, 0.16))
    k.col_mesh(box(L, 0.8, 0.7, base=True))
    return dict()


@asset("stump", "nature")
def stump(k):
    r = k.r
    h = 0.75
    pts = [Vector((0, 0, -0.05)), Vector((0, 0, 0.2)), Vector((0.02, 0, 0.5)), Vector((0.02, 0.01, h))]
    t = tube(pts, [0.62, 0.5, 0.46, 0.45], 12, cap_start=False, cap_end=False, uv_tile=1.0)
    ndisp(t, 3.0, 0.03, k.noff)
    k.put(t, "BH_Bark", uv="keep", smooth=70, tint=0.9, mat_fn=moss_fn(k, 0.45, 2.0, -0.1))
    k.put(cyl(0.44, 0.03, 12), "BH_Wood", M=T(0.02, 0.01, h - 0.02), uv="planar_z", tile=1.0)
    for j in range(7):
        a = r.uniform(-1.2, 1.2) + math.pi * 0.3
        rr = 0.36
        hh = r.uniform(0.12, 0.4)
        k.put(cyl(0.08, hh, 4, r2=0.0), "BH_Wood", M=TRS(math.cos(a) * rr, math.sin(a) * rr, h - 0.02, r.uniform(-10, 10),
                                                           r.uniform(-10, 10), r.uniform(0, 90)), tint=r.uniform(0.7, 0.9))
    roots_flare(k, 0.5, 6, reach=(0.6, 1.1), z0=0.3, rad=(0.13, 0.2))
    bracket_fungus(k, Vector((0.0, -0.5, 0.35)), Vector((0, -1, 0)), 0.13)
    k.col_mesh(cyl(0.55, h, 8))
    return dict()
