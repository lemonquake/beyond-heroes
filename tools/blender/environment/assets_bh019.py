"""bh-019: Lape the Ancient's stand, the practice dummy and the Vault (see work/lemondev/bh-019/contracts/art.md).

  stand_lape      3.8 x 3.0  "Lape the Ancient", appraiser of relics: two gnarled dead-wood poles under a sagging,
                             tattered charcoal shroud that falls to the ground behind; low black-oak appraisal table with
                             three brass offering dishes (the trade slots), a great brass balance, candles, an open tome;
                             a crooked relic cabinet crowned by an antlered skull, a hanging censer.
  practice_dummy  1.3 x 1.3  straw training dummy on a cross-footed spring post. Two mesh nodes in the GLB:
                             `dummy_base` (feet, braces, the bottom 0.35 m of the post; carries collision + sockets) and
                             its child `dummy_body` (everything that wobbles, origin at the pivot (0, 0, 0.35)).
  stand_vault     3.0 x 2.4  the Hero's Vault: squat ashlar strongroom with a round iron vault door, hipped slate roof,
                             two iron-bound chests (one ajar, coins spilling), wall lantern, barred slit window.

Conventions (contract): metres, Z-up, origin at the bottom centre of the footprint, front (customer side) = -Y,
recenter=False. Colour comes only from the BH_* material choice. Helpers are local copies of the kit idioms (the other
asset modules are not imported).
"""
import math

import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from kit import *  # noqa
from kit import _frames
from masonry import masonry, arch_ring, split_lengths, block_between  # noqa
import market_common  # noqa  (registers the extra BH_* materials)
from registry import asset


# =================================================================================================================
# generic helpers (local copies of the kit idioms)
_LAST = [0]


def tris_so_far(k, label):
    """Debug: print the triangles added since the previous call (budget bookkeeping)."""
    n = sum(len(f.verts) - 2 for f in k.bm.faces)
    print("   tris %-14s +%5d  (%d)" % (label, n - _LAST[0], n))
    _LAST[0] = n


def along(a, b):
    """Frame with origin at a and local +Z pointing to b. Returns (matrix, length)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    z = d / L
    up = Vector((0, 0, 1)) if abs(z.z) < 0.95 else Vector((1, 0, 0))
    x = up.cross(z).normalized()
    y = z.cross(x)
    M = Matrix(((x.x, y.x, z.x, a.x), (x.y, y.y, z.y, a.y), (x.z, y.z, z.z, a.z), (0, 0, 0, 1)))
    return M, L


def beam(k, a, b, w, h=None, mat="BH_WoodDark", tint=0.6, bev=0.012, over=0.0):
    M, L = along(a, b)
    k.put(box(w, h or w, L + 2 * over, bev=bev), mat, M=M @ T(0, 0, L / 2), tint=tint)


def rod(k, a, b, r_, mat="BH_Iron", segs=6):
    k.put(tube([Vector(a), Vector(b)], r_, segs), mat, smooth=40)


def rope(k, a, b, sag=0.05, r=0.012, n=6, mat="BH_Rope", segs=4):
    a, b = Vector(a), Vector(b)
    pts = []
    for i in range(n + 1):
        t = i / n
        p = a.lerp(b, t)
        p.z -= sag * 4 * t * (1 - t)
        pts.append(p)
    k.put(tube(pts, r, segs), mat, smooth=40)


def lashing(k, M, r=0.07, n=3, rr=0.011):
    for i in range(n):
        k.put(torus(r, rr, 8, 3), "BH_Rope", M=M @ T(0, 0, (i - (n - 1) / 2) * 0.026))


def peg(k, x, y, lean=(0, 0)):
    """Wooden tent peg driven into the ground (top 0.12 above it)."""
    k.put(box(0.045, 0.045, 0.2, bev=0.008), "BH_WoodDark", M=TRS(x, y, 0.02, lean[0], lean[1], k.r.uniform(0, 90)),
          tint=0.5)


def plank(k, L, w, th, M, mat="BH_Wood", tint=(0.7, 1.0), chips=1, warp=0.0):
    r = k.r
    t = box(L, w, th, bev=min(0.012, th * 0.3))
    if warp:
        bmesh.ops.subdivide_edges(t, edges=[e for e in t.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > L * 0.5],
                                  cuts=3)
        for v in t.verts:
            v.co.z += warp * math.sin((v.co.x / L + 0.5) * math.pi)
    if chips:
        chip(t, r, r.randint(0, chips), min(0.03, th * 0.5))
    jitter(t, r, 0.003)
    k.put(t, mat, M=M, tint=r.uniform(*tint) if isinstance(tint, tuple) else tint)


def rivet(k, M, r_=0.018, mat="BH_Iron"):
    k.put(cyl(r_, 0.012, 6), mat, M=M)


def flame_tip(k, M, h=0.05):
    k.put(cyl(h * 0.28, h, 6, r2=0.0), "BH_Flame", M=M, uvoff=False)


def candle(k, M, h=0.15, r_=0.025, drips=2):
    c = cyl(r_, h, 8)
    for v in c.verts:
        if v.co.z > h - 0.01:
            v.co.z -= k.r.uniform(0, 0.015)
    k.put(c, "BH_Candle", M=M, smooth=40)
    for j in range(drips):
        a = k.r.uniform(0, math.tau)
        k.put(cyl(0.007, h * k.r.uniform(0.3, 0.75), 4), "BH_Candle", M=M @ T(math.cos(a) * r_, math.sin(a) * r_, 0))
    k.put(cyl(0.003, 0.02, 3), "BH_StoneDark", M=M @ T(0, 0, h - 0.012), tint=0.1)  # wick
    flame_tip(k, M @ T(0, 0, h + 0.006), 0.045)


def hang_lantern(k, M, s=1.0, glass="BH_Glass"):
    """Wrought-iron lantern, origin at the hanging ring top; body hangs below. Returns local light point."""
    h = 0.55 * s
    r_ = 0.2 * s
    k.put(torus(0.05 * s, 0.012 * s, 10, 4), "BH_Iron", M=M @ TRS(0, 0, -0.05 * s, 90, 0, 0))
    k.put(cyl(r_ * 1.15, 0.16 * s, 6, r2=0.03 * s), "BH_Iron", M=M @ T(0, 0, -0.26 * s))
    k.put(cyl(r_ * 1.1, 0.04 * s, 6), "BH_Iron", M=M @ T(0, 0, -0.28 * s))
    k.put(cyl(r_, h, 6, r2=r_ * 0.85), glass, M=M @ T(0, 0, -0.28 * s - h), uvoff=False)
    for i in range(6):
        a = math.tau * i / 6
        k.put(box(0.022 * s, 0.022 * s, h), "BH_Iron", M=M @ TRS(math.cos(a) * r_ * 0.95, math.sin(a) * r_ * 0.95,
                                                                     -0.28 * s - h / 2, 0, 0, math.degrees(a)))
    k.put(cyl(r_ * 1.1, 0.05 * s, 6), "BH_Iron", M=M @ T(0, 0, -0.33 * s - h))
    k.put(cyl(0.05 * s, 0.1 * s, 6, r2=0.0), "BH_Iron", M=M @ TRS(0, 0, -0.33 * s - h, 180, 0, 0))
    return (0, 0, -0.28 * s - h * 0.55)


def sheet(k, P, nu, nv, mat, keep=None, th=0.02, smooth=45, tint=0.85, tile=1.5, flip=False):
    """Cloth from P(u, v) -> (x, y, z) over a nu x nv grid; keep(i, j) -> bool drops faces (tatters, holes).
    th=0 keeps a single-sided sheet whose normal is d/du x d/dv (flip=True reverses it)."""
    t = tb()
    vs = [[t.verts.new(Vector(P(i / nu, j / nv))) for i in range(nu + 1)] for j in range(nv + 1)]
    for j in range(nv):
        for i in range(nu):
            if keep is None or keep(i, j):
                t.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    loose = [v for v in t.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(t, geom=loose, context="VERTS")
    if th:
        bmesh.ops.solidify(t, geom=list(t.faces), thickness=th)
        bmesh.ops.recalc_face_normals(t, faces=list(t.faces))
    elif flip:
        bmesh.ops.reverse_faces(t, faces=list(t.faces))
    k.put(t, mat, tint=tint, smooth=smooth, tile=tile)


def coin(k, x, y, z, tilt=8.0, mat="BH_Gold"):
    k.put(cyl(0.019, 0.005, 6), mat, M=TRS(x, y, z, k.r.uniform(-tilt, tilt), k.r.uniform(-tilt, tilt), 0))


def book_closed(k, M, w, d, h, cover="BH_Leather"):
    k.put(box(w, d, h, bev=0.006), cover, M=M @ T(0, 0, h / 2), tint=0.7)
    k.put(box(w - 0.012, d - 0.02, h - 0.014), "BH_Paper", M=M @ T(0.008, 0, h / 2), tint=0.8)


def jar(k, M, h=0.2, r_=0.07, mat="BH_Bone", lid="BH_Cloth"):
    prof = [(0.0, 0.0), (r_ * 0.75, 0.0), (r_, h * 0.35), (r_ * 0.92, h * 0.72), (r_ * 0.55, h * 0.86),
            (r_ * 0.6, h), (0.0, h)]
    k.put(lathe(prof, 7), mat, M=M, smooth=50, tint=k.r.uniform(0.6, 0.9))
    if lid:
        k.put(cyl(r_ * 0.7, 0.025, 7), lid, M=M @ T(0, 0, h - 0.01), tint=0.6)


def scroll(k, M, L=0.32, r=0.024, ribbon="BH_ClothRed", seal=False):
    """Rolled parchment along local X, resting on its side (origin at the bottom centre)."""
    k.put(cyl(r, L, 8), "BH_Paper", M=M @ TRS(-L / 2, 0, r, 0, 90, 0), tint=k.r.uniform(0.8, 1.0), smooth=40)
    k.put(torus(r + 0.003, 0.006, 8, 3), ribbon, M=M @ TRS(0, 0, r, 0, 90, 0))
    if seal:
        k.put(cyl(0.02, 0.008, 8), "BH_ClothRed", M=M @ TRS(0, -r, r, 90, 0, 0), tint=0.6)


def dented(t, center, radius, depth):
    """Push vertices near `center` inward (toward the local Z axis) - a dent in a helm or a pot."""
    c = Vector(center)
    for v in t.verts:
        d = (v.co - c).length
        if d < radius:
            f = (1.0 - d / radius) ** 2 * depth
            n = Vector((v.co.x, v.co.y, 0.0))
            if n.length > 1e-6:
                v.co -= n.normalized() * f
    return t


def gnarled_pole(k, foot, top, r0=0.11, r1=0.055, n=20, segs=9, bend=0.14, seed=0.0, lobes=3, twist=1.6,
                 mat="BH_Bark", roots=4, cap_z=None, bound=None):
    """Twisted dead-wood pole: a meandering spine, lobed cross-section whose ridges spiral up the trunk, a flared
    root foot with a few roots gripping the ground, and a jagged broken top. Returns the spine points."""
    foot, top = Vector(foot), Vector(top)
    pts = []
    for i in range(n + 1):
        t = i / n
        p = foot.lerp(top, t)
        w = math.sin(math.pi * min(t * 1.15, 1.0)) ** 0.7
        p += Vector((mnoise.noise(Vector((t * 2.3, seed, 0.37))), mnoise.noise(Vector((seed + 3.1, t * 2.3, 1.73))),
                     0.0)) * bend * w
        pts.append(p)
    fr = _frames(pts)
    t_ = tb()
    rings = []
    for i, (p, (tg, nn, bb)) in enumerate(zip(pts, fr)):
        t = i / n
        rr = lerp(r0, r1, t) + r0 * 0.9 * max(0.0, 1.0 - t / 0.1) ** 2
        ring = []
        for s in range(segs):
            a = math.tau * s / segs
            ph = t * twist * math.tau + seed
            m = 1.0 + 0.2 * math.cos(lobes * a - ph) + 0.07 * mnoise.noise(Vector((a * 1.3, t * 9.0, seed)))
            ring.append(t_.verts.new(p + (nn * math.cos(a) + bb * math.sin(a)) * rr * m))
        rings.append(ring)
    for i in range(n):
        for s in range(segs):
            s2 = (s + 1) % segs
            t_.faces.new((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]))
    t_.faces.new(rings[0][::-1])
    # jagged broken top: a fan up to an off-centre splinter tip
    tip = t_.verts.new(pts[-1] + fr[-1][0] * r1 * 2.2 + fr[-1][1] * r1 * 0.4)
    for s in range(segs):
        v = rings[-1][s]
        v.co += fr[-1][0] * (r1 * 0.9 * k.r.random())
        t_.faces.new((rings[-1][s], rings[-1][(s + 1) % segs], tip))
    bmesh.ops.recalc_face_normals(t_, faces=t_.faces)
    k.put(t_, mat, tint=0.7, smooth=55, tile=1.0)
    # roots gripping the ground (roots: a count, or a list of directions in degrees)
    angs = roots if isinstance(roots, (list, tuple)) else [math.degrees(math.tau * j / roots + seed * 1.7) for j in range(roots)]
    for ang in angs:
        a = math.radians(ang) + k.r.uniform(-0.25, 0.25)
        d = Vector((math.cos(a), math.sin(a), 0.0))
        L = k.r.uniform(0.3, 0.46)
        if bound:  # keep the root tip inside the footprint
            for ax, lim in ((0, bound[0]), (1, bound[1])):
                if abs(d[ax]) > 1e-3:
                    room = (math.copysign(lim, d[ax]) - foot[ax]) / d[ax] - r0 - 0.04
                    L = max(0.12, min(L, room))
        base = foot + Vector((0, 0, 0.16))
        rp = [base + d * r0 * 0.6, base + d * (r0 + L * 0.35) + Vector((0, 0, -0.06)),
              foot + d * (r0 + L * 0.75) + Vector((0, 0, 0.02)), foot + d * (r0 + L) + Vector((0, 0, -0.03))]
        k.put(tube(rp, [r0 * 0.55, r0 * 0.4, r0 * 0.22, r0 * 0.08], 6), mat, tint=0.65, smooth=50)
    return pts


def branch_stub(k, p, d, L, r_, mat="BH_Bark", up=0.25):
    """Short broken-off branch from p along d (tapering, curling a little upward)."""
    p, d = Vector(p), Vector(d).normalized()
    q1 = p + d * L * 0.5 + Vector((0, 0, L * up * 0.4))
    q2 = p + d * L + Vector((0, 0, L * up))
    k.put(tube([p - d * r_ * 0.8, q1, q2], [r_, r_ * 0.7, r_ * 0.45], 6), mat, tint=0.65, smooth=50)
    return q2


# =================================================================================================================
# 1. stand_lape - Lape the Ancient, appraiser of relics (Malasugue)
def antler(k, M, side, L=0.42):
    """One branching antler rising from local origin, spreading toward local +X * side."""
    s = side
    main = [Vector((0, 0, 0)), Vector((s * 0.07, 0.02, 0.1)), Vector((s * 0.16, 0.03, 0.2)),
            Vector((s * 0.2, -0.01, 0.31)), Vector((s * 0.19, -0.05, L))]
    main = [M @ p for p in main]
    k.put(tube(main, [0.022, 0.019, 0.016, 0.012, 0.004], 5), "BH_Bone", tint=0.85, smooth=50)
    for (i, dv, ln) in ((1, (s * 0.02, -0.12, 0.1), 0.13), (2, (s * 0.1, -0.04, 0.12), 0.12),
                        (3, (s * -0.05, -0.08, 0.1), 0.1)):
        p0 = main[i]
        d = (M.to_3x3() @ Vector(dv)).normalized()
        k.put(tube([p0, p0 + d * ln * 0.6 + Vector((0, 0, 0.02)), p0 + d * ln + Vector((0, 0, 0.05))],
                   [0.012, 0.008, 0.003], 4), "BH_Bone", tint=0.85, smooth=50)


def beast_skull(k, M):
    """Long-snouted antlered beast skull resting on its jaw, looking toward -Y; origin at its underside."""
    t = ico(0.1, 2)
    for v in t.verts:
        v.co.y *= 1.1
        v.co.x *= 0.9
        if v.co.y < 0:
            v.co.y *= 1.0 + (-v.co.y / 0.11) * 0.9  # stretch the snout forward
            v.co.z *= 1.0 - (-v.co.y / 0.25) * 0.45
            v.co.x *= 1.0 - (-v.co.y / 0.25) * 0.4
    k.put(t, "BH_Bone", M=M @ T(0, 0, 0.085), tint=0.9, smooth=40)
    for sx in (-1, 1):
        k.put(cyl(0.026, 0.05, 7), "BH_StoneDark", M=M @ TRS(sx * 0.062, -0.07, 0.115, 0, 90 * sx, 0) @ T(0, 0, -0.02),
              tint=0.05)  # eye sockets
        k.put(cyl(0.012, 0.03, 5), "BH_StoneDark", M=M @ TRS(sx * 0.018, -0.235, 0.075, 90, 0, 0), tint=0.05)  # nostrils
        antler(k, M @ TRS(sx * 0.055, 0.03, 0.16, 0, sx * 12, 0), sx)


def gnarl_knot(k, p, r_):
    t = ico(r_, 1)
    jitter(t, k.r, r_ * 0.2)
    k.put(t, "BH_Bark", M=T(*Vector(p)) @ S(1.0, 1.0, 1.3), tint=0.6, smooth=40)


def balance_scale(k, M):
    """Great brass balance, beam along local X, tipped: the left pan lower. Origin at the foot."""
    k.put(lathe([(0.0, 0.0), (0.11, 0.0), (0.11, 0.025), (0.08, 0.04), (0.05, 0.06), (0.03, 0.08), (0.0, 0.08)], 10),
          "BH_Brass", M=M, smooth=45)
    k.put(lathe([(0.018, 0.0), (0.016, 0.3), (0.026, 0.33), (0.016, 0.36), (0.014, 0.52), (0.0, 0.53)], 8), "BH_Brass",
          M=M @ T(0, 0, 0.07), smooth=45)
    piv = M @ Vector((0, 0, 0.58))
    k.put(ico(0.028, 1), "BH_Brass", M=T(*piv), smooth=40)
    k.put(cyl(0.012, 0.09, 6, r2=0.0), "BH_Brass", M=M @ T(0, 0, 0.6))  # finial spike
    tilt = 9.0
    Mb = T(*piv) @ M.to_3x3().to_4x4() @ R(0, tilt, 0)
    k.put(box(0.62, 0.018, 0.022, bev=0.005), "BH_Brass", M=Mb)
    k.put(cyl(0.008, 0.12, 5, r2=0.0), "BH_Brass", M=Mb @ TRS(0, -0.012, 0, 180, 0, 0))  # pointer
    for sx, drop in ((-1, 0.36), (1, 0.28)):
        hook = Mb @ Vector((sx * 0.3, 0, 0))
        k.put(torus(0.012, 0.004, 6, 3), "BH_Brass", M=T(*hook) @ R(90, 0, 0))
        pan_c = hook - Vector((0, 0, drop))
        for a in (90, 210, 330):
            q = pan_c + Vector((math.cos(math.radians(a)) * 0.085, math.sin(math.radians(a)) * 0.085, 0.012))
            k.put(tube([hook, q], 0.0025, 3), "BH_Brass")
        k.put(lathe([(0.0, 0.0), (0.05, 0.0), (0.09, 0.02), (0.1, 0.03), (0.092, 0.03), (0.08, 0.02), (0.0, 0.012)],
                    10), "BH_Brass", M=T(*pan_c), smooth=45)
    # an old coin in the heavy pan
    lp = Mb @ Vector((-0.3, 0, 0)) - Vector((0, 0, 0.36))
    k.put(cyl(0.022, 0.006, 8), "BH_Gold", M=T(lp.x, lp.y, lp.z + 0.013))


def candle_cluster(k, M):
    """Candles of mixed height on an iron dish, wax pooled and dripping over its rim. Returns light point."""
    r = k.r
    k.put(lathe([(0.0, 0.0), (0.14, 0.0), (0.16, 0.025), (0.15, 0.03), (0.0, 0.012)], 12), "BH_Iron", M=M, smooth=40)
    wax = cyl(0.13, 0.02, 12, r2=0.1)
    jitter(wax, r, 0.008)
    k.put(wax, "BH_Candle", M=M @ T(0, 0, 0.01), smooth=40)
    spots = [(0.0, 0.0, 0.3), (0.07, 0.03, 0.2), (-0.06, 0.05, 0.24), (0.03, -0.075, 0.13), (-0.07, -0.05, 0.1),
             (0.08, -0.03, 0.07)]
    for (x, y, h) in spots:
        candle(k, M @ TRS(x, y, 0.02, r.uniform(-4, 4), r.uniform(-4, 4), 0), h, r.uniform(0.018, 0.028), 2)
    for i in range(3):  # wax runs over the rim, down to the cloth
        a = r.uniform(0, math.tau)
        k.put(cyl(0.009, 0.03, 4), "BH_Candle", M=M @ T(math.cos(a) * 0.158, math.sin(a) * 0.158, 0.0))
    return M @ Vector((0, 0, 0.42))


def open_tome(k, M, w=0.44, d=0.32):
    """Ancient open book, spine along local Y; pages fanning up from the gutter."""
    k.put(box(w + 0.03, d + 0.03, 0.02, bev=0.006), "BH_Leather", M=M @ T(0, 0, 0.01), tint=0.6)
    for sx in (-1, 1):
        prof = []
        for i in range(6):
            u = i / 5
            prof.append((sx * u * w / 2, 0.02 + 0.045 * math.sin(math.pi * (0.15 + 0.7 * u)) + 0.012 * (1 - u)))
        pts = [(x, z) for x, z in prof] + [(x, 0.02) for x, z in prof[::-1]]
        if sx > 0:
            pts = pts[::-1]
        t = prism(pts, d)
        k.put(t, "BH_Paper", M=M, tint=0.8, smooth=30)
        # a few loose leaves of a darker old paper curling up
    k.put(box(0.015, 0.012, 0.18), "BH_ClothRed", M=M @ TRS(0.02, -d / 2 - 0.004, -0.04, 0, 8, 0), tint=0.6)  # ribbon


def loupe(k, M):
    k.put(torus(0.045, 0.008, 12, 4), "BH_Brass", M=M @ T(0, 0, 0.012))
    k.put(cyl(0.04, 0.004, 12), "BH_Silver", M=M @ T(0, 0, 0.01))
    k.put(cyl(0.011, 0.13, 6, r2=0.014), "BH_WoodDark", M=M @ TRS(0.05, 0, 0.012, 0, 90, 0), tint=0.5)


def iron_casket(k, M, w=0.36, d=0.24, h=0.2):
    """Sealed iron casket: riveted box, domed lid, crossed chains and a padlock at the front."""
    k.put(box(w, d, h, bev=0.01), "BH_Iron", M=M @ T(0, 0, h / 2), tint=0.8)
    lid = prism([(math.cos(a) * d / 2, math.sin(a) * 0.06) for a in [math.pi * i / 6 for i in range(7)]], w + 0.01)
    k.put(lid, "BH_Iron", M=M @ T(0, 0, h) @ R(0, 0, 90), smooth=40)
    for sx in (-1, 1):
        for sz in (0.03, h - 0.03):
            rivet(k, M @ TRS(sx * (w / 2 - 0.03), -d / 2 - 0.002, sz, 90, 0, 0), 0.012)
    # chains over the lid and down both faces (a heavy cord of iron)
    for x in (-w * 0.22, w * 0.22):
        pts = [(x, -d / 2 - 0.008, 0.03), (x, -d / 2 - 0.008, h)]
        pts += [(x, math.cos(a) * (d / 2 + 0.008), h + math.sin(a) * 0.068) for a in [math.pi * i / 4 for i in range(1, 4)]]
        pts += [(x, d / 2 + 0.008, h), (x, d / 2 + 0.008, 0.03)]
        k.put(tube([M @ Vector(p_) for p_ in pts], 0.011, 4), "BH_Iron", smooth=30)
    k.put(box(0.07, 0.03, 0.08, bev=0.01), "BH_Iron", M=M @ T(0, -d / 2 - 0.02, h * 0.45))  # padlock
    k.put(torus(0.024, 0.006, 8, 3), "BH_Iron", M=M @ TRS(0, -d / 2 - 0.02, h * 0.45 + 0.05, 90, 0, 0))
    k.put(cyl(0.02, 0.02, 8), "BH_ClothRed", M=M @ TRS(0, -d / 2 - 0.004, h * 0.75, 90, 0, 0), tint=0.5)  # wax seal


def crown(k, M, R_=0.085):
    k.put(cyl(R_, 0.05, 12, caps=False), "BH_Gold", M=M, smooth=40, tint=0.55)
    for i in range(6):
        a = math.tau * i / 6
        tip = cyl(0.022, 0.06, 3, r2=0.0)
        k.put(tip, "BH_Gold", M=M @ TRS(math.cos(a) * R_, math.sin(a) * R_, 0.045, 0, 0, math.degrees(a) + 90) @ S(1, 0.3, 1),
              tint=0.55)
        k.put(ico(0.009, 0), "BH_GemRed" if i % 3 == 0 else "BH_Gold", M=M @ T(math.cos(a) * R_, math.sin(a) * R_, 0.025))
    # bent: one point knocked askew
    k.put(torus(R_, 0.006, 12, 3), "BH_Gold", M=M @ T(0, 0, 0.003), tint=0.5)


def dented_helm(k, M):
    """Old dented kettle-helm with a nasal and a torn mail aventail stub."""
    t = lathe([(0.0, 0.25), (0.07, 0.24), (0.12, 0.2), (0.145, 0.12), (0.15, 0.03), (0.17, 0.0)], 12, cap_top=False)
    dented(t, (0.09, -0.08, 0.19), 0.09, 0.04)
    dented(t, (-0.1, 0.05, 0.12), 0.06, 0.025)
    k.put(t, "BH_Iron", M=M, smooth=50, tint=0.7)
    k.put(box(0.035, 0.016, 0.14, bev=0.004), "BH_Iron", M=M @ TRS(0, -0.152, 0.04, -6, 0, 0))
    k.put(torus(0.158, 0.011, 14, 3), "BH_Iron", M=M @ T(0, 0, 0.012))


def relic_stand(k, M):
    """The one magical accent: a violet stone held in a bronze claw on a little plinth."""
    k.put(box(0.12, 0.12, 0.04, bev=0.008), "BH_WoodDark", M=M @ T(0, 0, 0.02), tint=0.5)
    k.put(cyl(0.02, 0.07, 6), "BH_Brass", M=M @ T(0, 0, 0.04))
    for a in (0, 120, 240):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        k.put(tube([(0, 0, 0.1), (ca * 0.045, sa * 0.045, 0.13), (ca * 0.03, sa * 0.03, 0.19)], [0.008, 0.006, 0.003], 4),
              "BH_Brass", M=M)
    t = ico(0.045, 1)
    for v in t.verts:
        v.co.z *= 1.35
    k.put(t, "BH_GemViolet", M=M @ T(0, 0, 0.155))


def censer(k, top, drop=0.6):
    """Small brass censer on a chain from `top`; embers glow through its pierced bowl. Returns the body centre."""
    top = Vector(top)
    c = top - Vector((0, 0, drop))
    n = 7
    for i in range(n):  # chain links
        z = top.z - (drop - 0.12) * (i + 0.5) / n
        k.put(torus(0.014, 0.004, 6, 3), "BH_Brass", M=TRS(top.x, top.y, z, 90, 0, 90 * (i % 2)))
    k.put(cyl(0.012, 0.03, 6, r2=0.03), "BH_Brass", M=T(c.x, c.y, c.z + 0.1))
    for a in (0, 120, 240):  # three short chains to the rim
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        k.put(tube([(c.x, c.y, c.z + 0.12), (c.x + ca * 0.07, c.y + sa * 0.07, c.z + 0.01)], 0.0025, 3), "BH_Brass")
    k.put(lathe([(0.0, -0.075), (0.04, -0.07), (0.07, -0.03), (0.075, 0.0), (0.07, 0.01), (0.0, 0.01)], 10), "BH_Brass",
          M=T(c.x, c.y, c.z), smooth=45)
    k.put(lathe([(0.07, 0.015), (0.06, 0.05), (0.03, 0.075), (0.0, 0.085)], 10, cap_bot=False), "BH_Brass",
          M=T(c.x, c.y, c.z), smooth=45)
    k.put(ico(0.05, 1), "BH_Coals", M=T(c.x, c.y, c.z - 0.005))  # embers seen through the gap under the lid
    k.put(cyl(0.03, 0.03, 6, r2=0.0), "BH_Brass", M=T(c.x, c.y, c.z - 0.1))
    return c


@asset("stand_lape", "market")
def stand_lape(k):
    """Lape the Ancient. 3.8 x 3.0, <= 4.2 m. Two twisted dead-wood poles lean into a sagging, holed charcoal shroud
    whose ragged tail falls to the ground behind; a low black-oak table with three brass offering dishes set into its
    front edge (the trade slots), a great balance, candles and an open tome; a crooked relic cabinet behind Lape."""
    r = k.r
    _LAST[0] = 0
    npc = Vector((0.0, 0.44, 0.0))

    # --- ground: threadbare round rug with a ragged, holed edge ------------------------------------------------
    rc = Vector((0.0, 0.18))
    Rr = 1.38

    def rug_p(u, v):
        a = u * math.tau
        rad = Rr * max(v, 0.05) * (1.0 + (0.035 * mnoise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, 5.1))) if v > 0.9 else 0))
        return (rc.x + math.cos(a) * rad, rc.y + math.sin(a) * rad * 0.92, 0.012 + 0.004 * v)
    rug_holes = {(3, 2), (15, 2), (22, 3), (10, 3)}
    rug_edge = {i: r.random() < 0.3 for i in range(28)}
    sheet(k, rug_p, 28, 4, "BH_ClothRed",
          keep=lambda i, j: (i, j) not in rug_holes and not (j == 3 and rug_edge[i]), th=0.0, smooth=None, tint=0.6,
          flip=True)
    # the faded woven ring on it
    sheet(k, lambda u, v: (rc.x + math.cos(u * math.tau) * lerp(0.98, 1.1, v),
                           rc.y + math.sin(u * math.tau) * lerp(0.98, 1.1, v) * 0.92, 0.021),
          28, 1, "BH_Cloth", keep=lambda i, j: i not in (4, 5, 17), th=0.0, smooth=None, tint=0.5, flip=True)

    tris_so_far(k, "rug")
    # --- the two gnarled dead-wood poles (feet at the back, leaning forward over Lape) -------------------------------
    A = Vector((-1.40, 0.36, 3.98))   # left pole top (taller); the shroud is tied here
    B = Vector((1.42, 0.5, 3.52))     # right pole top
    fa = Vector((-1.63, 1.02, 0.0))
    fb = Vector((1.66, 1.12, 0.0))
    pa = gnarled_pole(k, fa, A + Vector((0.01, -0.02, 0.08)), 0.12, 0.06, seed=1.3, bend=0.2,
                      roots=(-100, -20, 60, 170, 250), bound=(1.9, 1.5))
    pb = gnarled_pole(k, fb, B + Vector((-0.01, -0.02, 0.08)), 0.11, 0.055, seed=4.7, bend=0.18, lobes=4,
                      roots=(-80, 10, 100, 200), bound=(1.9, 1.5))
    # broken branch stubs and knots
    branch_stub(k, pa[9], (-0.9, -0.5, 0.2), 0.36, 0.035)
    branch_stub(k, pa[15], (-0.4, 0.9, 0.1), 0.26, 0.03)
    hook = branch_stub(k, pb[12], (-1.0, -0.35, 0.05), 0.42, 0.035, up=0.1)
    branch_stub(k, pb[6], (0.8, -0.6, 0.3), 0.22, 0.03)
    for p, s_ in ((pa[5], 0.05), (pa[13], 0.04), (pb[4], 0.05), (pb[10], 0.045), (pb[16], 0.035)):
        gnarl_knot(k, p + Vector((0.05, -0.04, 0)), s_)
    for P_ in (A, B):  # rope lashings where the shroud is tied to the pole tops
        lashing(k, T(P_.x, P_.y, P_.z + 0.02), 0.07, 3)

    tris_so_far(k, "poles")
    # --- the shroud: one tattered charcoal cloth tied to the two pole tops -------------------------------------------
    # Cross-section (front -> back): a ragged front hang, the canopy from the pole-top line back to the back corners,
    # and the back fall that breaks over them and hangs to the ground; beyond the poles it slumps down the sides.
    # Radial folds run out from each pole top, the hems end in pointed tongues, a few moth holes.
    C = Vector((-1.7, 1.3, 3.0))      # back corners
    D = Vector((1.72, 1.3, 2.84))
    vf, vb = 0.17, 0.6
    nu, nv = 30, 22

    def front_line(a):
        p = A.lerp(B, a)
        p.z -= 0.55 * 4 * a * (1 - a)
        return p

    def back_line(a):
        p = C.lerp(D, a)
        p.z -= 0.14 * 4 * a * (1 - a)
        return p

    tongue = [0.35, 0.55, 0.95, 1.0, 0.6, 0.3, 0.2, 0.45, 0.8, 0.5, 0.3, 0.65, 1.0, 0.9, 0.5, 0.25, 0.4, 0.75, 0.55, 0.2,
              0.3, 0.7, 0.95, 0.6, 0.35, 0.5, 0.85, 0.4, 0.25, 0.6, 1.0, 0.7, 0.3]
    rs = [r.random() for _ in range(nu + 1)]
    front_len = [lerp(0.55, 1.0, rs[i]) * tongue[i % len(tongue)] for i in range(nu + 1)]
    back_end = [lerp(0.2, 0.9, r.random() ** 1.5) for _ in range(nu + 1)]
    side_drop = [lerp(0.75, 1.0, r.random()) for _ in range(nv + 1)]

    def folds(p, peak, amp, n=7):
        d = Vector((p.x - peak.x, p.y - peak.y))
        L = d.length
        if L < 1e-4:
            return 0.0
        ang = math.atan2(d.y, d.x)
        return amp * math.sin(ang * n + peak.x) * sstep(0.1, 0.9, L) * max(0.0, 1.0 - L / 2.2)

    def shroud(u, v):
        i = int(round(u * nu))
        j = int(round(v * nv))
        a = lerp(-0.12, 1.1, u)
        ac = min(max(a, 0.0), 1.0)
        over = max(-a / 0.12, (a - 1.0) / 0.1, 0.0)
        F, Bk = front_line(ac), back_line(ac)
        mid = 1.0 - abs(ac - 0.5) * 2.0     # 1 in the middle, 0 at the poles
        if v < vf:        # front hang: longer near the poles, short over Lape's head; pointed tongues
            t = (vf - v) / vf
            L = lerp(0.62, 0.2, mid ** 0.7) * front_len[i]
            p = F + Vector((0.0, -0.1 * t, -L * t ** 1.05))
            p.y += 0.03 * math.sin(a * math.tau * 6.0) * t
        elif v < vb:      # canopy
            s = (v - vf) / (vb - vf)
            p = F.lerp(Bk, s)
            p.z -= 0.14 * math.sin(math.pi * ac) * math.sin(math.pi * s)
        else:             # back fall: to a ragged hem 0.2 - 0.9 m above the ground
            t = (v - vb) / (1.0 - vb)
            zend = back_end[i]
            p = Bk + Vector((0.0, 0.12 * t ** 0.5, -(Bk.z - zend) * t))
            p.y += 0.05 * math.sin(a * math.tau * 4.5 + 0.7) * t ** 0.5
        if over > 0:      # beyond the poles: slumps down the sides, deeper on the left
            sg = -1.0 if a < 0 else 1.0
            deep = 1.9 if a < 0 else 1.2
            p.x += sg * 0.16 * over ** 0.8
            p.z -= deep * over ** 1.4 * (side_drop[j] if i in (0, nu) else 1.0)
            p.y += 0.06 * math.sin(v * math.tau * 3.5) * over
        z_f = folds(p, A, 0.07) + folds(p, B, 0.06, 6)
        p.z += z_f
        p.z += 0.035 * mnoise.noise(Vector((p.x * 1.8, p.y * 1.8, 0.4)) + k.noff)
        p.z = max(p.z, 0.2)
        return (p.x, p.y, p.z)

    holes = {(8, 8), (8, 9), (9, 9), (21, 10), (22, 10), (14, 12), (13, 12), (26, 16), (5, 18), (5, 17)}
    sheet(k, shroud, nu, nv, "BH_ClothBlack", keep=lambda i, j: (i, j) not in holes, th=0.022, smooth=50, tint=0.7)
    # two long torn strips hanging from the front line, clear of Lape's head and staff
    for a_, L in ((0.12, 1.05), (0.86, 0.95)):
        F = front_line(a_)
        pts = [F + Vector((0, -0.03, -0.05)), F + Vector((0.03, -0.12, -L * 0.45)), F + Vector((-0.03, -0.15, -L))]
        k.put(tube(pts, [0.04, 0.03, 0.01], 4, flat=(1.0, 0.25)), "BH_ClothBlack", tint=0.6, smooth=40)
    # the ragged back hem pegged down with ropes; the slumped left side pegged out
    for a_ in (0.05, 0.5, 0.95):
        i = int(round((a_ + 0.12) / 1.22 * nu))
        hem = Vector(shroud(i / nu, 1.0))
        pg = Vector((hem.x * 0.97, 1.44, 0.0))
        rope(k, hem + Vector((0, 0, 0.02)), pg + Vector((0, 0, 0.12)), 0.0, 0.01, 2)
        peg(k, pg.x, pg.y, (-14, 0))
    # bone charms and a feathered talisman hung on cords from the front line, near the poles
    for a_, L in ((0.2, 0.55), (0.27, 0.8), (0.72, 0.62), (0.79, 0.45)):
        F = front_line(a_) + Vector((0.0, -0.02, -0.02))
        bot = F - Vector((0, 0, L))
        k.put(tube([F, bot], 0.004, 3), "BH_Rope")
        Mb = TRS(bot.x, bot.y, bot.z, 0, r.uniform(-10, 10), r.uniform(-35, 35))  # bone chime on a crooked twig
        k.put(tube([Mb @ Vector((-0.1, 0, 0.01)), Mb @ Vector((0.0, 0, -0.005)), Mb @ Vector((0.1, 0, 0.012))], 0.007, 4),
              "BH_Bark", tint=0.7)
        for sx, dl in ((-0.075, 0.13), (0.0, 0.2), (0.075, 0.1)):
            k.put(tube([Mb @ Vector((sx, 0, 0)), Mb @ Vector((sx, 0, -dl))], 0.0025, 3), "BH_Rope")
            k.put(tube([Mb @ Vector((sx, 0, -dl + 0.01)), Mb @ Vector((sx, 0, -dl - 0.06))], [0.008, 0.005], 4),
                  "BH_Bone", tint=0.9)
            k.put(ico(0.011, 0), "BH_Bone", M=Mb @ T(sx, 0, -dl - 0.065), tint=0.85)
        k.put(prism([(0, 0), (0.016, -0.02), (0.01, -0.12), (-0.004, -0.1)], 0.003), "BH_ClothBlack",
              M=Mb @ TRS(0.04, 0, -0.03, 0, 0, r.uniform(-20, 20)), tint=0.6)  # black feather

    tris_so_far(k, "shroud")
    # --- the appraisal table: low, heavy black oak --------------------------------------------------------------
    zt = 0.74
    x0, x1 = -0.96, 0.96
    y0, y1 = -0.76, -0.08
    ym = (y0 + y1) / 2
    for i in range(3):  # thick top of three boards
        plank(k, x1 - x0 + 0.06, (y1 - y0) / 3 - 0.006, 0.08,
              T(0, y0 + (y1 - y0) * (i + 0.5) / 3, zt - 0.04), mat="BH_WoodDark", tint=(0.4, 0.55), chips=2)
    leg = [(0.07, 0.0), (0.085, 0.04), (0.06, 0.1), (0.075, 0.2), (0.095, 0.3), (0.075, 0.42), (0.05, 0.5),
           (0.065, 0.56), (0.065, zt - 0.08)]
    for sx in (-1, 1):
        for y in (y0 + 0.1, y1 - 0.1):
            k.put(lathe(leg, 8), "BH_WoodDark", M=T(sx * (x1 - 0.12), y, 0), tint=0.5, smooth=45)
        beam(k, (sx * (x1 - 0.12), y0 + 0.1, 0.14), (sx * (x1 - 0.12), y1 - 0.1, 0.14), 0.06, tint=0.45)
    beam(k, (x0 + 0.12, ym, 0.14), (x1 - 0.12, ym, 0.14), 0.06, tint=0.45)  # stretcher
    # deep front apron with a carved lower edge (lobed)
    lob = [(x0 + 0.06, zt - 0.08)]
    n_l = 30
    for i in range(n_l + 1):
        x = lerp(x0 + 0.06, x1 - 0.06, i / n_l)
        lob.append((x, zt - 0.2 - 0.05 * abs(math.sin(math.pi * i / 5)) ** 0.6))
    lob.append((x1 - 0.06, zt - 0.08))
    k.put(prism(lob[::-1], 0.045), "BH_WoodDark", M=T(0, y0 + 0.06, 0), tint=0.45)
    for sx in (-1, 1):
        k.put(box(0.045, y1 - y0 - 0.2, 0.12), "BH_WoodDark", M=T(sx * (x1 - 0.1), ym, zt - 0.14), tint=0.45)
    tris_so_far(k, "table")
    # worn velvet cloth over the back half, falling over both ends with frayed hems
    half = x1 + 0.02
    vy0, vy1 = -0.46, -0.06

    def velvet(u, v):
        s = lerp(-half - 0.34, half + 0.34, u)
        y = lerp(vy0, vy1 + 0.04, v)
        if abs(s) <= half:
            x, z = s, zt + 0.006
        else:
            x = math.copysign(half + 0.012, s)
            z = zt + 0.006 - (abs(s) - half)
        if v > 0.93:  # falls a little over the back edge
            z -= 0.08 * (v - 0.93) / 0.07
        z += 0.004 * mnoise.noise(Vector((s * 6, y * 6, 2.0)))
        return (x, y, z)
    fray = [r.random() < 0.5 for _ in range(4)]
    sheet(k, velvet, 26, 4, "BH_Velvet", keep=lambda i, j: not (i in (0, 25) and fray[j]),
          th=0.008, smooth=40, tint=0.7)
    tris_so_far(k, "velvet")
    # three brass-rimmed offering dishes set into the front edge (the trade slots)
    dish_y = y0 + 0.17
    for x in (-0.42, 0.0, 0.42):
        k.put(lathe([(0.0, zt - 0.004), (0.13, zt - 0.004), (0.15, zt + 0.012), (0.158, zt + 0.02), (0.166, zt + 0.004),
                     (0.172, zt - 0.002)], 16), "BH_Brass", M=T(x, dish_y, 0), smooth=40)
        k.put(torus(0.152, 0.012, 16, 4), "BH_Brass", M=T(x, dish_y, zt + 0.02))
        k.put(cyl(0.132, 0.012, 16), "BH_Velvet", M=T(x, dish_y, zt + 0.002), tint=0.5)
    tris_so_far(k, "dishes")
    # the great balance at the right end, candles at the left, the open tome and a loupe in between
    balance_scale(k, TRS(0.62, -0.27, zt + 0.01, 0, 0, -8))
    light_a = candle_cluster(k, T(-0.72, -0.28, zt + 0.01))
    open_tome(k, TRS(-0.16, -0.27, zt + 0.012, 0, 0, 6))
    loupe(k, TRS(0.24, -0.34, zt + 0.012, 0, 0, 30))
    for (x, y) in ((0.21, -0.7), (-0.21, -0.69), (-0.66, -0.64), (0.67, -0.63), (0.1, -0.08)):
        coin(k, x, y, zt + 0.006)
    scroll(k, TRS(0.26, -0.14, zt + 0.01, 0, 0, -8), 0.3, 0.022, "BH_Rope", seal=True)

    tris_so_far(k, "tabletop")
    # --- the crooked relic cabinet behind Lape -------------------------------------------------------------------
    Mc = T(0.0, 1.13, 0.0) @ R(0, 1.8, -3.5)  # leans a little and is turned askew
    cw, cd, ch = 1.04, 0.2, 1.8    # half width, half depth, height
    shelves = (0.1, 0.52, 0.95, 1.37)
    for sx in (-1, 1):  # side boards with a ragged top
        t = box(0.05, cd * 2, ch, bev=0.008)
        chip(t, r, 2, 0.04)
        k.put(t, "BH_WoodDark", M=Mc @ T(sx * cw, 0, ch / 2), tint=0.45)
        k.put(box(0.08, cd * 2 + 0.04, 0.08, bev=0.01), "BH_WoodDark", M=Mc @ T(sx * cw, 0, 0.04), tint=0.4)
    for i, z in enumerate(shelves):
        plank(k, cw * 2 - 0.04, cd * 2 - 0.02, 0.04, Mc @ TRS(0, 0, z, 0, (-1.5, 1.2, -0.8, 1.6)[i], 0),
              mat="BH_WoodDark", tint=(0.4, 0.55), warp=-0.02)
    plank(k, cw * 2 + 0.16, cd * 2 + 0.08, 0.06, Mc @ TRS(0, 0, ch + 0.02, 0, -1.0, 0), mat="BH_WoodDark",
          tint=(0.4, 0.5))
    nb = 8
    for i in range(nb):  # back boards, one missing, one split short
        if i == 5:
            continue
        x = -cw + (2 * cw) * (i + 0.5) / nb
        hh = ch - (0.55 if i == 2 else 0.0)
        plank(k, 2 * cw / nb - 0.012, 0.025, hh, Mc @ T(x, cd - 0.012, hh / 2), mat="BH_Wood", tint=(0.35, 0.5))
    # carved crest on the top: two horn-like scrolls
    for sx in (-1, 1):
        k.put(tube([Mc @ Vector((sx * 0.95, 0, ch + 0.05)), Mc @ Vector((sx * 1.02, 0, ch + 0.2)),
                    Mc @ Vector((sx * 0.9, 0, ch + 0.3)), Mc @ Vector((sx * 0.82, 0, ch + 0.22))],
                   [0.035, 0.03, 0.022, 0.012], 6), "BH_WoodDark", tint=0.45, smooth=45)
    tris_so_far(k, "cabinet")
    # relics
    zs = [z + 0.02 for z in shelves]
    jar(k, Mc @ T(-0.78, -0.02, zs[0]), 0.3, 0.1, "BH_StoneDark", lid=None)
    jar(k, Mc @ T(-0.52, 0.02, zs[0]), 0.22, 0.08, "BH_Bone")
    iron_casket(k, Mc @ TRS(0.62, -0.02, zs[0], 0, 0, -6), 0.38, 0.26, 0.2)
    iron_casket(k, Mc @ TRS(-0.62, -0.02, zs[1], 0, 0, 5), 0.36, 0.24, 0.19)
    for i in range(5):  # bundle of scrolls tied with cord
        a = math.tau * i / 5
        k.put(cyl(0.028, 0.42, 8), "BH_Paper", M=Mc @ TRS(0.6 + math.cos(a) * 0.035, -0.02, zs[1] + 0.05 + math.sin(a) * 0.035,
                                                           0, 90, 3) @ T(0, 0, -0.21), tint=r.uniform(0.7, 0.95), smooth=40)
    k.put(torus(0.075, 0.009, 10, 3), "BH_Rope", M=Mc @ TRS(0.6, -0.02, zs[1] + 0.05, 0, 90, 0))
    dented_helm(k, Mc @ TRS(-0.66, -0.02, zs[2], 0, 0, 25))
    jar(k, Mc @ T(-0.3, 0.03, zs[2]), 0.16, 0.06, "BH_Bottle", lid="BH_Leather")
    k.put(box(0.2, 0.14, 0.05, bev=0.02), "BH_Velvet", M=Mc @ T(0.62, -0.02, zs[2] + 0.025), tint=0.5)  # cushion
    crown(k, Mc @ TRS(0.62, -0.02, zs[2] + 0.05, 6, 0, 0))
    for i in range(3):
        book_closed(k, Mc @ TRS(-0.72, 0.0, zs[3] + i * 0.055, 0, 0, r.uniform(-12, 12)), 0.26, 0.2, 0.05,
                    ("BH_Leather", "BH_ClothRed", "BH_WoodDark")[i])
    relic_stand(k, Mc @ T(0.5, -0.04, zs[3]))
    k.put(cyl(0.05, 0.02, 8), "BH_Brass", M=Mc @ T(-0.36, -0.02, zs[3]))
    candle(k, Mc @ T(-0.36, -0.02, zs[3] + 0.02), 0.12, 0.022, 3)
    light_b = Mc @ Vector((-0.36, -0.12, zs[3] + 0.3))
    jar(k, Mc @ T(0.82, 0.0, zs[3]), 0.18, 0.06, "BH_Bone")
    beast_skull(k, Mc @ TRS(0.0, 0.06, ch + 0.05, 0, 0, 4))

    tris_so_far(k, "relics")
    # --- stool with a pile of old books; a coffer of gold by the table; an urn and tomes at the left ------------------
    sp = Vector((1.12, 0.62, 0.0))
    k.put(cyl(0.2, 0.05, 10, bev=0.01), "BH_WoodDark", M=T(sp.x, sp.y, 0.44), tint=0.5)
    for a in (30, 150, 270):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        beam(k, (sp.x + ca * 0.2, sp.y + sa * 0.2, 0.0), (sp.x + ca * 0.1, sp.y + sa * 0.1, 0.45), 0.04, tint=0.45)
    for i in range(3):
        book_closed(k, TRS(sp.x, sp.y, 0.49 + i * 0.06, 0, 0, r.uniform(-25, 25)), 0.24, 0.18, 0.055,
                    ("BH_WoodDark", "BH_Leather", "BH_ClothRed")[i])
    # coffer of coins (payment in gold) on the ground at the table's right end
    cp = TRS(1.3, -0.52, 0.0, 0, 0, -14)
    k.put(box(0.4, 0.28, 0.2, bev=0.01), "BH_WoodDark", M=cp @ T(0, 0, 0.1), tint=0.45)
    for x in (-0.14, 0.14):
        k.put(box(0.03, 0.29, 0.21), "BH_Iron", M=cp @ T(x, 0, 0.105))
    mound = lathe([(0.0, 0.0), (0.16, 0.0), (0.13, 0.03), (0.06, 0.06), (0.0, 0.07)], 8)
    for v in mound.verts:
        v.co.y *= 0.7
    k.put(mound, "BH_Gold", M=cp @ T(0, 0, 0.17), smooth=30)
    lid_M = cp @ T(0, 0.14, 0.2) @ R(-70, 0, 0)
    k.put(box(0.42, 0.29, 0.04, bev=0.01), "BH_WoodDark", M=lid_M @ T(0, -0.145, 0.02), tint=0.45)
    for (x, y) in ((1.1, -0.72), (1.18, -0.78), (1.02, -0.68), (0.9, -0.95), (1.5, -0.8)):
        coin(k, x, y, 0.014, 25)
    # ancient urn and fallen tomes at the left front
    k.put(lathe([(0.0, 0.0), (0.1, 0.0), (0.16, 0.12), (0.17, 0.26), (0.1, 0.4), (0.075, 0.44), (0.1, 0.48),
                 (0.0, 0.48)], 10), "BH_StoneDark", M=TRS(-1.3, -0.42, 0, 0, 0, 20), smooth=50, tint=0.6)
    for i, (x, y, rz) in enumerate(((-1.18, -0.78, 20), (-1.2, -0.76, -10))):
        book_closed(k, TRS(x, y, i * 0.06, 0, 0, rz), 0.3, 0.22, 0.06, ("BH_Leather", "BH_WoodDark")[i])
    scroll(k, TRS(-1.45, -0.72, 0, 0, 0, 60), 0.34, 0.026, "BH_ClothRed")

    tris_so_far(k, "ground")
    # --- censer from the right pole's branch --------------------------------------------------------------------
    censer(k, hook + Vector((-0.02, 0, -0.02)), 0.62)

    tris_so_far(k, "censer")
    # --- sockets and collision -------------------------------------------------------------------------------------
    k.sockets.append(("npc", tuple(npc)))
    k.sockets.append(("customer", (0.0, -1.62, 0.0)))
    k.sockets.append(("light_a", tuple(light_a)))
    k.sockets.append(("light_b", tuple(light_b)))
    k.col_box(x1 - x0 + 0.06, y1 - y0, zt + 0.25, T(0, ym, (zt + 0.25) / 2))
    k.col_box(cw * 2 + 0.1, cd * 2 + 0.04, 2.1, T(0, 1.14, 1.05) @ R(0, 0, -3.5))
    for f in (fa, fb):
        k.col_box(0.34, 0.34, 2.2, T(f.x, f.y, 1.1))
    k.col_box(0.5, 0.36, 0.3, cp @ T(0, 0, 0.15))
    k.col_box(0.42, 0.42, 0.6, T(sp.x, sp.y, 0.3))
    k.col_box(0.4, 0.4, 0.5, T(-1.3, -0.42, 0.25))
    return dict(recenter=False)


# =================================================================================================================
# 2. practice_dummy - straw training dummy on a spring post (two mesh nodes)
PIVOT_Z = 0.35


def arrow_stuck(k, tip, d, L=0.5, fletch="BH_Cloth"):
    """Arrow whose head is buried at `tip`; the shaft sticks out along d (pointing away from the target)."""
    tip, d = Vector(tip), Vector(d).normalized()
    M, _ = along(tip - d * 0.04, tip + d * L)
    k.put(cyl(0.007, L + 0.04, 5), "BH_Wood", M=M, tint=0.8)
    for a in (0, 120, 240):
        k.put(prism([(0.0, 0.0), (0.035, 0.03), (0.035, 0.13), (0.0, 0.12)], 0.003), fletch,
              M=M @ T(0, 0, L - 0.12) @ R(0, 0, a), tint=0.8)
    k.put(cyl(0.009, 0.02, 5), "BH_Rope", M=M @ T(0, 0, L - 0.16))


def straw_tuft(k, M, n=7, L=0.16, spread=40.0):
    r = k.r
    for i in range(n):
        a = r.uniform(0, 360)
        k.put(cyl(0.009, L * r.uniform(0.6, 1.2), 3, r2=0.002), "BH_Thatch",
              M=M @ R(0, 0, a) @ R(r.uniform(spread * 0.3, spread), 0, 0), tint=0.9)


def _dummy_base(k):
    r = k.r
    # cross-shaped timber foot: two beams halved into each other
    for rz in (0, 90):
        t = box(1.22, 0.14, 0.12, bev=0.012)
        chip(t, r, 2, 0.03)
        k.put(t, "BH_WoodDark", M=TRS(0, 0, 0.06 + (0.004 if rz else 0), 0, 0, rz), tint=0.55)
    # four braces from the feet up to the post
    for a in (0, 90, 180, 270):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        beam(k, (ca * 0.46, sa * 0.46, 0.1), (ca * 0.1, sa * 0.1, 0.33), 0.07, tint=0.5)
        rivet(k, TRS(ca * 0.45, sa * 0.45, 0.121), 0.014)
        # iron cleat pinning the brace to the post
        k.put(box(0.05, 0.05, 0.08, bev=0.006), "BH_Iron", M=TRS(ca * 0.095, sa * 0.095, 0.3, 0, 0, a))
    # the bottom of the post: a square socket block capped with iron, a coil spring over the joint
    k.put(box(0.2, 0.2, PIVOT_Z - 0.12, bev=0.012), "BH_WoodDark", M=T(0, 0, 0.12 + (PIVOT_Z - 0.12) / 2), tint=0.5)
    k.put(box(0.23, 0.23, 0.03, bev=0.006), "BH_Iron", M=T(0, 0, PIVOT_Z - 0.015))
    for sx in (-1, 1):
        for sy in (-1, 1):
            rivet(k, TRS(sx * 0.1, sy * 0.1, PIVOT_Z + 0.001), 0.012)
    # sandbags weighing down two feet, straw strewn about, a spent arrow
    for (x, y, rz) in ((0.5, 0.02, 90), (-0.02, -0.5, 0)):
        t = lathe([(0.0, 0.0), (0.1, 0.0), (0.13, 0.05), (0.12, 0.1), (0.0, 0.13)], 8)
        for v in t.verts:
            v.co.x *= 1.35
        ndisp(t, 8.0, 0.012, k.noff)
        k.put(t, "BH_Cloth", M=TRS(x, y, 0.1, 0, 0, rz), tint=0.7, smooth=50)
        k.put(torus(0.03, 0.008, 6, 3), "BH_Rope", M=TRS(x, y, 0.23, 0, 0, rz) @ T(0.12, 0, 0) @ R(0, 90, 0))
    for i in range(16):
        a = r.uniform(0, math.tau)
        d = r.uniform(0.2, 0.6)
        k.put(box(r.uniform(0.1, 0.22), 0.008, 0.004), "BH_Thatch",
              M=TRS(math.cos(a) * d, math.sin(a) * d, 0.004, 0, 0, r.uniform(0, 180)), tint=0.9)
    M, _ = along((-0.28, -0.46, 0.012), (0.18, -0.58, 0.012))
    k.put(cyl(0.007, 0.48, 5), "BH_Wood", M=M, tint=0.8)
    k.put(cyl(0.012, 0.05, 4, r2=0.0), "BH_Iron", M=M @ T(0, 0, 0.48))


def _dummy_body(k):
    """Everything that wobbles, built in asset space (z >= 0.33); shifted to the pivot by the caller."""
    r = k.r
    # the post, square, rising through the sack into the head
    k.put(box(0.13, 0.13, 1.4, bev=0.012), "BH_WoodDark", M=T(0, 0, 0.33 + 0.7), tint=0.5)  # top hidden in the head
    k.put(box(0.15, 0.15, 0.05, bev=0.006), "BH_Iron", M=T(0, 0, 0.4))  # iron collar just above the joint
    # straw-stuffed sack torso
    z0, z1 = 0.78, 1.52
    prof = [(0.15, z0), (0.21, z0 + 0.05), (0.23, z0 + 0.14), (0.195, z0 + 0.25), (0.24, z0 + 0.36), (0.285, z0 + 0.5),
            (0.29, z0 + 0.6), (0.25, z1 - 0.05), (0.15, z1 - 0.015), (0.06, z1)]
    t = lathe(prof, 14, cap_bot=False, cap_top=False)
    for v in t.verts:
        v.co.y *= 0.76
    ndisp(t, 6.0, 0.018, k.noff)
    probe = t.copy()
    k.put(t, "BH_Cloth", tint=0.8, smooth=50)
    bvh = BVHTree.FromBMesh(probe)
    # straw fringe out of the open bottom of the sack, and out of the neck
    for i in range(12):
        a = math.tau * i / 12 + r.uniform(-0.2, 0.2)
        x, y = math.cos(a) * 0.16, math.sin(a) * 0.16 * 0.76
        k.put(cyl(0.012, r.uniform(0.08, 0.15), 3, r2=0.002), "BH_Thatch",
              M=TRS(x, y, z0 + 0.03, 180 + math.sin(a) * -25, math.cos(a) * 25, 0), tint=0.9)
    straw_tuft(k, T(0, 0, z1 - 0.01), 8, 0.14, 55)
    # rope bindings: waist and neck, and a crossed binding over the back
    k.put(torus(0.2, 0.016, 14, 4), "BH_Rope", M=T(0, 0, z0 + 0.25) @ S(1, 0.78, 1))
    k.put(torus(0.1, 0.013, 10, 4), "BH_Rope", M=T(0, 0, z1 - 0.02))
    # a burst seam on the right flank with straw bursting out
    straw_tuft(k, T(-0.24, 0.02, z0 + 0.42) @ R(0, -90, 0), 9, 0.15, 50)
    # head: a smaller stuffed sack tied at the neck
    hd = ico(0.14, 2)
    for v in hd.verts:
        v.co.z *= 1.1
        v.co.y *= 0.9
    ndisp(hd, 9.0, 0.012, k.noff + Vector((3, 1, 2)))
    k.put(hd, "BH_Cloth", M=T(0, 0, 1.66), tint=0.75, smooth=50)
    k.put(torus(0.07, 0.014, 8, 3), "BH_Rope", M=T(0, 0, 1.53))
    # dented iron practice helm (a plain cap with a nasal), knocked askew down over one eye
    Mh = TRS(0.02, 0.0, 1.64, -4, 12, 0)
    h = lathe([(0.0, 0.215), (0.06, 0.205), (0.115, 0.165), (0.148, 0.1), (0.158, 0.03), (0.16, 0.0)], 14,
              cap_top=False, cap_bot=False)
    dented(h, (0.07, -0.1, 0.15), 0.08, 0.035)
    dented(h, (-0.12, 0.03, 0.09), 0.06, 0.022)
    k.put(h, "BH_Iron", M=Mh, smooth=50, tint=0.7)
    k.put(torus(0.16, 0.013, 16, 4), "BH_Iron", M=Mh @ T(0, 0, 0.012))           # rim band
    k.put(tube([Mh @ Vector((0, y_ * 1.04, z_ + 0.008)) for (y_, z_) in ((-0.152, 0.08), (-0.118, 0.165), (-0.06, 0.205),
                                                                          (0.0, 0.216), (0.06, 0.205), (0.118, 0.165),
                                                                          (0.152, 0.08))], 0.011, 4), "BH_Iron", smooth=40)  # crest
    k.put(box(0.032, 0.016, 0.13, bev=0.004), "BH_Iron", M=Mh @ TRS(0, -0.162, -0.04, -4, 0, 0))  # nasal
    for i in range(8):  # rivets round the band
        a = math.tau * (i + 0.5) / 8
        rivet(k, Mh @ TRS(math.cos(a) * 0.172, math.sin(a) * 0.172, 0.012, 0, 90, math.degrees(a)), 0.009)
    # arm beam through the shoulders, its ends wrapped in sacking
    za = 1.33
    k.put(box(1.0, 0.09, 0.09, bev=0.01), "BH_WoodDark", M=T(0, 0, za), tint=0.5)
    for sx in (-1, 1):
        k.put(cyl(0.065, 0.2, 8), "BH_Cloth", M=TRS(sx * 0.4, 0, za, 0, 90, 0) @ T(0, 0, -0.1), tint=0.7, smooth=40)
        for dx in (-0.07, 0.07):
            k.put(torus(0.066, 0.009, 8, 3), "BH_Rope", M=TRS(sx * 0.4 + dx, 0, za, 0, 90, 0))
        straw_tuft(k, TRS(sx * 0.5, 0, za, 0, sx * 90, 0), 7, 0.1, 35)
    # battered round shield strapped to the left arm (+X; the dummy faces -Y): four planks cut to a disc
    Ms = TRS(0.4, -0.072, za - 0.06, 90, 0, 0) @ R(0, 0, 8) @ R(6, -12, 0)  # local +Z faces -Y
    Rs = 0.22
    for i in range(4):
        xl, xr = -Rs + 2 * Rs * i / 4 + 0.004, -Rs + 2 * Rs * (i + 1) / 4 - 0.004
        t = cyl(Rs, 0.028, 18)
        slice_plane(t, (xr, 0, 0), (1, 0, 0))
        slice_plane(t, (xl, 0, 0), (-1, 0, 0))
        if i == 3:  # a bite hacked out of the edge
            slice_plane(t, (0.16, 0.12, 0), (0.7, 0.7, 0))
        jitter(t, r, 0.003)
        k.put(t, "BH_Wood", M=Ms, tint=r.uniform(0.55, 0.8))
    rim = torus(Rs, 0.012, 18, 4)
    slice_plane(rim, (0.16, 0.12, 0), (0.7, 0.7, 0))
    k.put(rim, "BH_Iron", M=Ms @ T(0, 0, 0.022))
    k.put(ico(0.055, 1), "BH_Iron", M=Ms @ TRS(0, 0, 0.03, s=(1, 1, 0.55)), smooth=40)
    for i in range(6):
        a = math.tau * (i + 0.3) / 6
        rivet(k, Ms @ T(math.cos(a) * (Rs - 0.04), math.sin(a) * (Rs - 0.04), 0.028), 0.011)
    for dz in (-0.06, 0.06):  # leather straps binding it to the arm
        k.put(torus(0.068, 0.012, 8, 3), "BH_Leather", M=TRS(0.4 + dz, 0, za, 0, 90, 0) @ S(1.0, 1.35, 1.0))
    # target patch on the chest: a darker cloth disc with a pale ring, projected onto the sack
    tc = Vector((0.0, 0.0, 1.14))

    def on_sack(px, pz, off):
        o = Vector((px, -1.0, pz))
        hit = bvh.ray_cast(o, Vector((0, 1, 0)), 2.0)
        if hit[0] is None:
            return Vector((px, -0.2, pz))
        return hit[0] + hit[1] * off

    def disc(r0, r1, off, mat, n=20):
        tt = tb()
        rings = []
        for rad in (r0, r1):
            ring = []
            for i in range(n):
                a = math.tau * i / n
                rj = rad * (1.0 + (0.06 * mnoise.noise(Vector((math.cos(a) * 3, math.sin(a) * 3, rad * 20))) if rad > 0 else 0))
                ring.append(tt.verts.new(on_sack(tc.x + math.cos(a) * rj, tc.z + math.sin(a) * rj, off)))
            rings.append(ring)
        for i in range(n):
            j = (i + 1) % n
            if r0 > 0:
                tt.faces.new((rings[1][i], rings[1][j], rings[0][j], rings[0][i]))
        if r0 <= 0:
            c = tt.verts.new(on_sack(tc.x, tc.z, off))
            for i in range(n):
                tt.faces.new((rings[1][i], rings[1][(i + 1) % n], c))
        bmesh.ops.recalc_face_normals(tt, faces=tt.faces)
        for f in tt.faces:  # face the viewer (toward -Y)
            f.normal_update()
            if f.normal.y > 0:
                f.normal_flip()
        k.put(tt, mat, tint=0.7, smooth=40)
    disc(0.0, 0.15, 0.008, "BH_ClothRed")
    disc(0.065, 0.098, 0.013, "BH_ClothCream")
    # a stitched border of rope round the patch
    pts = [on_sack(tc.x + math.cos(a) * 0.155, tc.z + math.sin(a) * 0.155, 0.01) for a in
           [math.tau * i / 18 for i in range(18)]]
    k.put(tube(pts, 0.006, 3, closed=True), "BH_Rope")
    # arrows stuck in the torso (one near the bull's-eye) and one in the shield
    for (px, pz, d) in ((0.03, 1.16, (0.25, -1.0, 0.18)), (-0.15, 1.3, (-0.4, -1.0, 0.35)),
                        (0.12, 0.95, (0.3, -1.0, -0.12))):
        tip = on_sack(px, pz, -0.03)
        arrow_stuck(k, tip, d, r.uniform(0.42, 0.52))
    sh = Ms @ Vector((-0.07, 0.08, 0.03))
    arrow_stuck(k, sh, (0.15, -1.0, 0.25), 0.46)
    probe.free()
    return (0.0, 0.0, 1.2)


@asset("practice_dummy", "market")
def practice_dummy(k):
    """Straw training dummy, 1.3 x 1.3, ~2.0 m. `dummy_base` (this asset's own mesh, renamed) carries the cross foot,
    braces and the bottom 0.35 m of the post plus collision and sockets; `dummy_body` is a separate child mesh node with
    its origin at the pivot (0, 0, 0.35) so the game can tilt it like a spring post when hit.
    The kit merges an asset into one mesh, so the body is built with its own Kit and attached in a finish() wrapper
    (see _attach_body) - the only extension, local to this file."""
    _dummy_base(k)
    kb = Kit("practice_dummy_body")
    hit = _dummy_body(kb)
    k.sockets.append(("use", (0.0, -1.6, 0.0)))
    k.sockets.append(("hit", hit))
    k.col_box(0.5, 0.5, 2.0, T(0, 0, 1.0))
    base_finish = k.finish

    def finish_with_body(recenter=False, damp=0.0, damp_h=0.8):
        ob = base_finish(recenter=False, damp=damp, damp_h=damp_h)
        ob.name = "dummy_base"
        ob.data.name = "dummy_base"
        bmesh.ops.transform(kb.bm, matrix=T(0, 0, -PIVOT_Z), verts=kb.bm.verts)
        body = kb._bm_to_obj(kb.bm, "dummy_body")
        body.data.name = "dummy_body"
        body.location = (0.0, 0.0, PIVOT_Z)
        body.parent = ob
        body.data.calc_loop_triangles()
        print("BUILT   dummy_body tris=%d (child of dummy_base, origin at z=%.2f)" % (len(body.data.loop_triangles),
                                                                                       PIVOT_Z), flush=True)
        return ob
    k.finish = finish_with_body
    return dict(recenter=False)


# =================================================================================================================
# 3. stand_vault - the Hero's Vault
class RoundCut:
    """Full circular opening for masonry(): blocks stop at a straight line outside the circle in every course."""

    def __init__(self, cx, cz, R_):
        self.cx, self.cz, self.R = cx, cz, R_

    def hw(self, z):
        d = z - self.cz
        return math.sqrt(max(0.0, self.R * self.R - d * d))

    def occ(self, zb, zt):
        if zt <= self.cz - self.R + 1e-3 or zb >= self.cz + self.R - 1e-3:
            return None
        hb, ht = self.hw(zb), self.hw(zt)
        deficit = 0.0
        for i in range(1, 8):
            z = lerp(zb, zt, i / 8)
            deficit = max(deficit, self.hw(z) - lerp(hb, ht, i / 8))
        hb += deficit
        ht += deficit
        return (self.cx - hb, self.cx - ht, self.cx + hb, self.cx + ht)


class RectCut2:
    def __init__(self, x0, x1, z0, z1):
        self.x0, self.x1, self.z0, self.z1 = x0, x1, z0, z1

    def occ(self, zb, zt):
        if zt <= self.z0 + 1e-4 or zb >= self.z1 - 1e-4:
            return None
        return (self.x0, self.x0, self.x1, self.x1)


def battered_course(k, x0, x1, yf_bot, yf_top, y_back, z0, z1, M, lens=(0.5, 0.9)):
    """Plinth course along local X whose front face (-Y) slopes back as it rises (a battered base)."""
    r = k.r
    ws, _ = split_lengths(r, x1 - x0, *lens)
    acc = x0
    for w in ws:
        xa, xb = acc + 0.012, acc + w - 0.012
        acc += w
        c = [(xa, yf_bot, z0), (xb, yf_bot, z0), (xb, y_back, z0), (xa, y_back, z0),
             (xa, yf_top, z1), (xb, yf_top, z1), (xb, y_back, z1), (xa, y_back, z1)]
        t = hexa(c, 0.03)
        chip(t, r, r.randint(0, 2), 0.05)
        jitter(t, r, 0.006)
        k.put(t, "BH_Stone", M=M, tint=r.uniform(0.7, 0.9), mat_fn=moss_fn(k, 0.6, 2.2, -0.25))


def vault_door(k, M, Rd=0.72):
    """Round iron vault door; local +Z is its outward normal, origin at the centre of its back face."""
    prof = [(0.0, 0.0), (Rd, 0.0), (Rd, 0.12), (Rd - 0.03, 0.17), (Rd - 0.11, 0.17), (Rd - 0.13, 0.13),
            (0.3, 0.13), (0.28, 0.15), (0.2, 0.15), (0.19, 0.13), (0.0, 0.13)]
    k.put(lathe(prof, 24), "BH_Iron", M=M, smooth=35, uv="keep")
    # bolt heads round the thick rim
    for i in range(12):
        a = math.tau * (i + 0.5) / 12
        k.put(cyl(0.024, 0.02, 6, r2=0.015), "BH_Iron", M=M @ T(math.cos(a) * (Rd - 0.07), math.sin(a) * (Rd - 0.07), 0.168))
    # radial locking bars from the hub to the rim, each riveted
    for i in range(8):
        a = math.tau * i / 8 + math.pi / 8
        Mr = M @ R(0, 0, math.degrees(a))
        k.put(box(Rd - 0.42, 0.07, 0.03), "BH_Iron", M=Mr @ T(0.23 + (Rd - 0.42) / 2 + 0.05, 0, 0.145))
        rivet(k, Mr @ T(0.5, 0, 0.16), 0.016)
    # spoked wheel handle standing off the hub
    k.put(cyl(0.07, 0.16, 10), "BH_Iron", M=M @ T(0, 0, 0.13), smooth=40)
    k.put(torus(0.21, 0.022, 18, 5), "BH_Iron", M=M @ T(0, 0, 0.28), smooth=45)
    for i in range(6):
        a = 60 * i + 15
        Mr = M @ R(0, 0, a)
        k.put(cyl(0.016, 0.21, 6), "BH_Iron", M=Mr @ TRS(0.0, 0, 0.28, 0, 90, 0), smooth=40)
        k.put(cyl(0.03, 0.05, 6), "BH_Brass", M=Mr @ T(0.21, 0, 0.26), smooth=40)  # worn brass grips
    k.put(ico(0.05, 1), "BH_Brass", M=M @ TRS(0, 0, 0.29, s=(1, 1, 0.6)), smooth=40)
    # keyhole plate on the latch side (-X)
    k.put(cyl(0.065, 0.02, 8), "BH_Brass", M=M @ T(-(Rd - 0.24), 0, 0.13) @ S(0.75, 1.25, 1.0))  # oval escutcheon
    k.put(box(0.02, 0.05, 0.02), "BH_StoneDark", M=M @ T(-(Rd - 0.24), -0.015, 0.152), tint=0.02)
    k.put(cyl(0.017, 0.02, 8), "BH_StoneDark", M=M @ T(-(Rd - 0.24), 0.02, 0.143), tint=0.02)


def iron_chest(k, M, L=0.74, W=0.46, H=0.4, open_deg=0.0, spill=False):
    """Iron-bound treasure chest (origin bottom centre, front -Y); open_deg lifts the lid about its back hinge."""
    r = k.r
    for i in range(3):
        for sy in (-1, 1):
            plank(k, L, 0.03, H / 3 - 0.008, M @ T(0, sy * (W / 2 - 0.015), H / 6 + H / 3 * i), mat="BH_WoodDark",
                  tint=(0.4, 0.6))
    for sx in (-1, 1):
        plank(k, W - 0.06, 0.03, H, M @ TRS(sx * (L / 2 - 0.015), 0, H / 2, 0, 0, 90), mat="BH_WoodDark", tint=(0.4, 0.6))
    k.put(box(L - 0.06, W - 0.06, 0.03), "BH_WoodDark", M=M @ T(0, 0, 0.03), tint=0.4)
    for x in (-L / 2 + 0.1, L / 2 - 0.1):
        k.put(box(0.06, W + 0.016, H - 0.01), "BH_Iron", M=M @ T(x, 0, H / 2))
    for sx in (-1, 1):  # corner caps
        for sy in (-1, 1):
            k.put(box(0.07, 0.07, 0.08), "BH_Iron", M=M @ T(sx * (L / 2 - 0.03), sy * (W / 2 - 0.03), 0.04))
    k.put(box(0.1, 0.03, 0.12, bev=0.008), "BH_Iron", M=M @ T(0, -W / 2 - 0.01, H - 0.07))
    k.put(cyl(0.02, 0.012, 8), "BH_StoneDark", M=M @ TRS(0, -W / 2 - 0.026, H - 0.08, 90, 0, 0), tint=0.03)
    for sx in (-1, 1):  # drop handles on the ends
        k.put(torus(0.05, 0.01, 8, 3), "BH_Iron", M=M @ TRS(sx * (L / 2 + 0.012), 0, H * 0.6, 0, 90, 0))
    # domed lid about the back hinge
    Mh = M @ T(0, W / 2, H) @ R(-open_deg, 0, 0) @ T(0, -W / 2, 0)
    lid = [(math.cos(a) * W / 2, math.sin(a) * 0.14) for a in [math.pi * i / 8 for i in range(9)]]
    k.put(prism(lid, L), "BH_Wood", M=Mh @ R(0, 0, 90), tint=0.6, smooth=30)
    k.put(box(L, W, 0.02), "BH_WoodDark", M=Mh @ T(0, 0, 0.01), tint=0.4)
    for x in (-L / 2 + 0.1, L / 2 - 0.1):
        band = prism([(math.cos(a) * (W / 2 + 0.012), math.sin(a) * 0.152) for a in [math.pi * i / 8 for i in range(9)]],
                     0.065)
        k.put(band, "BH_Iron", M=Mh @ T(x, 0, 0) @ R(0, 0, 90), smooth=30)
    if open_deg > 0:
        mound = ico(1.0, 2)
        slice_plane(mound, (0, 0, 0.0), (0, 0, -1))  # keep the upper half: a heap of coin
        for v in mound.verts:
            v.co = Vector((v.co.x * 0.31, v.co.y * 0.19, v.co.z * 0.085))
        jitter(mound, r, 0.012)
        k.put(mound, "BH_Gold", M=M @ T(0, 0, H - 0.07), smooth=None)
        for i in range(10):
            x_, y_ = r.uniform(-0.26, 0.26), r.uniform(-0.15, 0.13)
            hz = 0.075 * max(0.0, 1.0 - (abs(x_) / 0.31) ** 2 - (abs(y_) / 0.19) ** 2) ** 0.5
            coin(k, *(M @ Vector((x_, y_, H - 0.07 + hz + 0.004))), 35)
        k.put(ico(0.022, 0), "BH_GemRed", M=M @ T(0.08, -0.05, H + 0.01))
        k.put(lathe([(0.0, 0.0), (0.035, 0.0), (0.01, 0.03), (0.01, 0.07), (0.04, 0.1), (0.045, 0.14), (0.0, 0.1)], 8),
              "BH_Gold", M=M @ TRS(-0.14, 0.04, H - 0.04, 0, 20, 30), smooth=40)  # a tipped goblet
    if spill:
        for i in range(10):
            p = M @ Vector((r.uniform(-0.36, 0.1), -W / 2 - r.uniform(0.02, 0.12), 0.004))
            coin(k, p.x, p.y, 0.004 + (0.004 if i % 4 == 0 else 0), 12)
    else:
        k.put(box(0.07, 0.04, 0.09, bev=0.012), "BH_Iron", M=M @ T(0, -W / 2 - 0.035, H - 0.14))  # padlock
        k.put(torus(0.024, 0.007, 8, 3), "BH_Iron", M=M @ TRS(0, -W / 2 - 0.035, H - 0.08, 90, 0, 0))


def wall_lantern(k, x, y_wall, z):
    """Wrought bracket sprung from a wall plate, lantern hanging from its tip. Returns the light point."""
    k.put(box(0.055, 0.025, 0.3, bev=0.006), "BH_Iron", M=T(x, y_wall - 0.012, z - 0.05))  # wall strap
    k.put(tube([(x, y_wall - 0.02, z - 0.2), (x, y_wall - 0.04, z - 0.25), (x, y_wall - 0.02, z - 0.28)], 0.012, 4),
          "BH_Iron")  # curled foot
    for dz in (-0.14, 0.05):
        rivet(k, TRS(x, y_wall - 0.026, z + dz, 90, 0, 0), 0.02)
    arm = [(x, y_wall - 0.03, z + 0.06), (x, y_wall - 0.2, z + 0.1), (x, y_wall - 0.36, z + 0.06),
           (x, y_wall - 0.4, z - 0.02)]
    k.put(tube(arm, 0.015, 6), "BH_Iron", smooth=40)
    k.put(tube([(x, y_wall - 0.03, z - 0.18), (x, y_wall - 0.18, z - 0.06), (x, y_wall - 0.3, z + 0.07)], 0.012, 5),
          "BH_Iron", smooth=40)  # brace
    tip = Vector((x, y_wall - 0.4, z - 0.02))
    lp = hang_lantern(k, T(*tip), 0.5)
    return (tip.x + lp[0], tip.y + lp[1], tip.z + lp[2])


def moss_clump(k, x, y, s=0.2):
    t = ico(1.0, 1)
    for v in t.verts:
        v.co = Vector((v.co.x * s, v.co.y * s * 0.7, max(v.co.z, -0.1) * s * 0.3))
    jitter(t, k.r, s * 0.12)
    k.put(t, "BH_Moss", M=TRS(x, y, 0.0, 0, 0, k.r.uniform(0, 180)), tint=0.8, smooth=40)


@asset("stand_vault", "market")
def stand_vault(k):
    """The Hero's Vault. 3.0 x 2.4, <= 3.4 m. A squat ashlar strongroom on a battered plinth; a round iron vault door
    recessed in a voussoir surround, a hipped slate roof, two iron-bound chests before the door (one ajar, gold
    spilling), a wall lantern and a barred slit window."""
    r = k.r
    _LAST[0] = 0
    X0, X1 = -1.32, 1.32          # outer wall faces
    YF, YB = -0.5, 1.06           # front / back faces
    th = 0.36
    zp = 0.3                      # plinth top
    zw = 2.52                     # wall top
    dc, Rd = 1.16, 0.7            # door centre height, door radius
    r_in, r_out = 0.74, 1.0

    # --- battered plinth all round ------------------------------------------------------------------------------
    battered_course(k, X0 - 0.13, X1 + 0.13, YF - 0.14, YF - 0.05, YF + 0.3, 0.0, zp, T())
    battered_course(k, X0 - 0.13, X1 + 0.13, YF - 0.12, YF - 0.04, YF + 0.3, 0.0, zp,
                    T(0, (YF + YB), 0) @ R(0, 0, 180))
    for sx in (-1, 1):
        M = T(sx * (X1 + 0.0), (YF + YB) / 2, 0) @ R(0, 0, 90 * sx)
        half = (YB - YF) / 2
        battered_course(k, -half + 0.29, half - 0.29, -0.14, -0.05, 0.3, 0.0, zp, M, lens=(0.45, 0.7))

    tris_so_far(k, "plinth")
    # --- ashlar walls -------------------------------------------------------------------------------------------
    cut = [RoundCut(0.0, dc, r_out - 0.02), RectCut2(0.84, 1.12, 1.92, 2.34)]
    masonry(k, X0, X1, zp, zw, th, mat="BH_Stone", tint=(0.72, 0.95), course=(0.34, 0.46), blen=(0.5, 0.95),
            M=T(0, YF + th / 2, 0), cuts=cut, quoin="both", quoin_mat="BH_Stone", chip_rng=(0, 1),
            core_cuts=[RoundCut(0.0, dc, r_in + 0.01), RectCut2(0.86, 1.1, 1.94, 2.32)])
    masonry(k, X0, X1, zp, zw, th, mat="BH_StoneDark", tint=(0.7, 0.9), course=(0.4, 0.56), blen=(0.6, 1.1),
            M=T(0, YB - th / 2, 0), quoin="both", quoin_mat="BH_Stone", chip_rng=(0, 1))
    for sx in (-1, 1):
        masonry(k, YF + th, YB - th, zp, zw, th, mat="BH_StoneDark", tint=(0.7, 0.9), course=(0.4, 0.56),
                blen=(0.5, 0.9), M=T(sx * (X1 - th / 2), 0, 0) @ R(0, 0, 90), chip_rng=(0, 1),
                cuts=[RectCut2(0.18, 0.42, 1.9, 2.3)] if sx < 0 else ())
    tris_so_far(k, "walls")
    # --- the round door in its recess ----------------------------------------------------------------------------
    arch_ring(k, 0.0, dc, r_in, r_out, th, n=15, mat="BH_Stone", tint=(0.9, 1.0), key_extra=0.13,
              M=T(0, YF + th / 2, 0), proud=0.045, a0=-math.pi / 2, a1=1.5 * math.pi)
    lining = tube([(0, YF - 0.01, dc), (0, YF + 0.2, dc)], r_in + 0.004, 24, cap_start=False, cap_end=False)
    bmesh.ops.reverse_faces(lining, faces=lining.faces)
    k.put(lining, "BH_StoneDark", tint=0.5)
    ydoor = YF + 0.14
    vault_door(k, T(0, ydoor + 0.17, dc) @ R(90, 0, 0), Rd)
    # massive hinges on the right (+X) side: straps across the door into barrel knuckles set in the reveal
    for dz in (-0.34, 0.34):
        z = dc + dz
        xk = math.sqrt(max(r_in * r_in - dz * dz, 0.0)) - 0.06
        k.put(box(0.55, 0.03, 0.1, bev=0.01), "BH_Iron", M=T(xk - 0.3, ydoor - 0.005, z))
        for i in range(3):
            rivet(k, TRS(xk - 0.5 + i * 0.16, ydoor - 0.022, z, 90, 0, 0), 0.016)
        k.put(cyl(0.05, 0.2, 8), "BH_Iron", M=T(xk, ydoor + 0.02, z - 0.1), smooth=40)
        k.put(cyl(0.02, 0.26, 6), "BH_Iron", M=T(xk, ydoor + 0.02, z - 0.13))
    # threshold step before the door
    t = box(1.2, 0.34, 0.18, bev=0.03)
    chip(t, r, 2, 0.04)
    k.put(t, "BH_Stone", M=T(0, YF - 0.29, 0.09), tint=0.85)
    k.put(box(1.0, 0.2, 0.14, bev=0.02), "BH_StoneDark", M=T(0, YF - 0.06, zp + 0.1 - 0.02), tint=0.7)  # sill

    tris_so_far(k, "door")
    # --- cornice and the hipped slate roof ------------------------------------------------------------------------
    ov = 0.1
    ex0, ex1, ey0, ey1 = X0 - ov, X1 + ov, YF - ov, YB + ov
    zc = zw + 0.18
    for (a, b, M) in ((ex0, ex1, T(0, YF + 0.1 - ov / 2, 0)), (ex0, ex1, T(0, YB - 0.1 + ov / 2, 0))):
        ws, _ = split_lengths(r, b - a, 0.5, 0.85)
        acc = a
        for w in ws:
            tt = box(w - 0.02, 0.3, 0.18, bev=0.025)
            chip(tt, r, r.randint(0, 2), 0.04)
            k.put(tt, "BH_Stone", M=M @ TRS(acc + w / 2, 0, zw + 0.09, 0, r.uniform(-0.6, 0.6), 0), tint=0.9,
                  mat_fn=moss_fn(k, 0.7, 2.0, -0.1))
            acc += w
    for sx in (-1, 1):
        ws, _ = split_lengths(r, ey1 - ey0 - 0.6, 0.45, 0.8)
        acc = ey0 + 0.3
        for w in ws:
            tt = box(0.3, w - 0.02, 0.18, bev=0.025)
            chip(tt, r, r.randint(0, 2), 0.04)
            k.put(tt, "BH_Stone", M=T(sx * (X1 + ov / 2 - 0.1), acc + w / 2, zw + 0.09), tint=0.9)
            acc += w
    # roof: four planes of overlapping slate courses up to a short ridge
    ycen = (YF + YB) / 2
    hx, hy = (ex1 - ex0) / 2 + 0.03, (ey1 - ey0) / 2 + 0.02
    rise = 0.58
    ridge_hx = hx - hy          # hip geometry: equal pitch on all sides
    ncourse = 5
    for side in range(4):
        for c in range(ncourse):
            f0, f1 = c / ncourse, (c + 1) / ncourse + 0.06
            z0_, z1_ = zc + rise * f0, zc + rise * min(f1, 1.0)
            kick = 0.035 if c else 0.0
            if side in (0, 2):  # front / back planes (trapezoids along X)
                sy = -1 if side == 0 else 1
                w0 = hx - (hx - ridge_hx) * f0
                w1 = hx - (hx - ridge_hx) * min(f1, 1.0)
                y0_, y1_ = sy * hy * (1 - f0), sy * hy * (1 - min(f1, 1.0))
                c8 = [(-w0, y0_, z0_ - 0.03 + kick), (w0, y0_, z0_ - 0.03 + kick), (w1, y1_, z1_ - 0.03),
                      (-w1, y1_, z1_ - 0.03), (-w0, y0_, z0_ + 0.03 + kick), (w0, y0_, z0_ + 0.03 + kick),
                      (w1, y1_, z1_ + 0.03), (-w1, y1_, z1_ + 0.03)]
            else:               # hip ends (triangles narrowing to the ridge ends)
                sx = -1 if side == 3 else 1
                d0 = hy * (1 - f0)
                d1 = hy * (1 - min(f1, 1.0))
                x0_, x1_ = sx * hx * 1.0 - sx * (hx - ridge_hx) * f0, sx * hx - sx * (hx - ridge_hx) * min(f1, 1.0)
                c8 = [(x0_, -d0, z0_ - 0.03 + kick), (x0_, d0, z0_ - 0.03 + kick), (x1_, d1 + 0.001, z1_ - 0.03),
                      (x1_, -d1 - 0.001, z1_ - 0.03), (x0_, -d0, z0_ + 0.03 + kick), (x0_, d0, z0_ + 0.03 + kick),
                      (x1_, d1 + 0.001, z1_ + 0.03), (x1_, -d1 - 0.001, z1_ + 0.03)]
            tt = hexa(c8, 0.0)
            bmesh.ops.recalc_face_normals(tt, faces=tt.faces)
            jitter(tt, r, 0.008)
            k.put(tt, "BH_Slate", M=T(0, ycen, 0), tint=r.uniform(0.7, 0.9))
    # lead rolls on the hips and ridge
    top_z = zc + rise + 0.03
    for sx in (-1, 1):
        for sy in (-1, 1):
            rod(k, (sx * hx, ycen + sy * hy, zc + 0.04), (sx * ridge_hx, ycen, top_z), 0.035, "BH_Slate", 6)
    rod(k, (-ridge_hx - 0.03, ycen, top_z), (ridge_hx + 0.03, ycen, top_z), 0.045, "BH_Slate", 8)
    for sx in (-1, 1):
        k.put(ico(0.06, 1), "BH_Iron", M=T(sx * ridge_hx, ycen, top_z), smooth=40)

    tris_so_far(k, "roof")
    # --- barred slit window above the door's shoulder (front), and one on the left side ------------------------------
    for (M, w, h) in ((T(0.98, YF, 2.13), 0.24, 0.38), (T(X0, 0.3, 2.1) @ R(0, 0, -90), 0.2, 0.36)):
        k.put(box(w + 0.02, 0.2, h + 0.02), "BH_StoneDark", M=M @ T(0, 0.1, 0), tint=0.02)
        k.put(box(w + 0.18, 0.12, 0.08, bev=0.015), "BH_Stone", M=M @ T(0, -0.02, -h / 2 - 0.04), tint=0.9)
        k.put(box(w + 0.14, 0.1, 0.1, bev=0.015), "BH_Stone", M=M @ T(0, -0.015, h / 2 + 0.05), tint=0.9)
        for dx in (-w / 3, 0.0, w / 3):
            k.put(cyl(0.013, h + 0.04, 6), "BH_Iron", M=M @ T(dx, 0.02, -h / 2 - 0.02))
        k.put(box(w, 0.03, 0.025), "BH_Iron", M=M @ T(0, 0.02, 0.02))

    # --- iron wall anchors on the sides and back (tie-rod plates) ---------------------------------------------------
    for (x, y, rz) in ((X0 - 0.01, 0.9, 90), (X1 + 0.01, 0.2, 90), (X1 + 0.01, 0.9, 90), (-0.7, YB + 0.01, 0),
                       (0.7, YB + 0.01, 0)):
        Ma = TRS(x, y, 1.75, 0, 0, rz)
        k.put(box(0.05, 0.03, 0.42), "BH_Iron", M=Ma @ R(0, 35, 0))
        k.put(box(0.05, 0.03, 0.42), "BH_Iron", M=Ma @ R(0, -35, 0))
        k.put(cyl(0.035, 0.03, 6), "BH_Iron", M=Ma @ TRS(0, -0.005, 0, 90, 0, 0))

    tris_so_far(k, "windows")
    # --- lantern bracket left of the door --------------------------------------------------------------------------
    light_a = wall_lantern(k, -1.0, YF, 2.12)

    tris_so_far(k, "lantern")
    # --- two chests before the door; the right one ajar and spilling gold --------------------------------------------
    iron_chest(k, TRS(-1.02, -0.86, 0, 0, 0, 9), 0.7, 0.44, 0.4)
    iron_chest(k, TRS(1.02, -0.86, 0, 0, 0, -11), 0.7, 0.44, 0.4, open_deg=62, spill=True)

    tris_so_far(k, "chests")
    # --- moss at the foot of the walls and between the chests --------------------------------------------------------
    for (x, y, s) in ((-1.34, -0.7, 0.14), (-0.62, -0.72, 0.15), (0.64, -0.73, 0.12), (1.35, -0.68, 0.12),
                      (-0.45, -0.66, 0.08)):
        moss_clump(k, x, y, s)

    # --- sockets and collision -------------------------------------------------------------------------------------
    k.sockets.append(("use", (0.0, YF - 1.5, 0.0)))
    k.sockets.append(("light_a", light_a))
    k.col_box(X1 - X0 + 0.26, YB - YF + 0.28, 2.2, T(0, (YF + YB) / 2, 1.1))
    for (x, rz) in ((-1.02, 9), (1.02, -11)):
        k.col_box(0.74, 0.48, 0.6, TRS(x, -0.88, 0.3, 0, 0, rz))
    return dict(recenter=False)
