"""bh-029 Builder K1 - the Agdao town kit (Zarael island), category ``zarael_town``.

Ancient stepped stone of the Wirewrights: talus-and-panel terraces, stepped-fret relief bands, serpent-head
balustrades, ochre and red lime plaster, jade and turquoise accents, and the Heartwire (``BH_Wire``) inlaid in
carved channels. Kit conventions: metres, Blender -Y = Godot +Z = the front, ``<name>-colonly`` collision children
(walkable tops, smooth ramp colliders under every stair, thin blocking rails), child empties as sockets.

    blender -b --factory-startup --python tools/blender/environment/build_assets.py -- zarael_town
"""
import math

import bmesh
from mathutils import Vector, Matrix

import kit
from kit import (box, hexa, prism, cyl, ico, lathe, tube, torus, chip, jitter, T, R, S, TRS, lerp, sstep, tb)
from masonry import split_lengths, course_heights
from registry import asset
import market_common  # noqa  (BH_Brass, BH_Copper, BH_Verdigris, BH_Rope, BH_Cloth* export colours)

CAT = "zarael_town"

# bh-029 contract materials (linear preview colours; Godot swaps them by name via MaterialLibrary.ENV).
EXTRA_MATERIALS = {
    "BH_GlyphStone":     ((0.42, 0.38, 0.31, 1), 0.88, 0.0, None),
    "BH_GlyphStoneDark": ((0.15, 0.15, 0.12, 1), 0.92, 0.0, None),
    "BH_Jade":           ((0.04, 0.24, 0.12, 1), 0.3, 0.0, None),
    "BH_Obsidian":       ((0.012, 0.01, 0.016, 1), 0.08, 0.0, None),
    "BH_LimePlaster":    ((0.46, 0.31, 0.13, 1), 0.95, 0.0, None),
    "BH_LimePlasterRed": ((0.34, 0.06, 0.04, 1), 0.95, 0.0, None),
    "BH_TerracePave":    ((0.3, 0.27, 0.22, 1), 0.9, 0.0, None),
    "BH_Turquoise":      ((0.04, 0.3, 0.28, 1), 0.45, 0.0, None),
    "BH_Wire":           ((0.8, 0.2, 0.42, 1), 0.35, 0.6, ((0.9, 0.16, 0.42), 6.0)),
    "BH_Glyph":          ((0.1, 0.7, 0.6, 1), 0.4, 0.0, ((0.15, 0.85, 0.72), 4.0)),
    "BH_Blackwire":      ((0.5, 0.04, 0.28, 1), 0.35, 0.0, ((0.75, 0.08, 0.38), 6.0)),
    "BH_Feather":        ((0.03, 0.24, 0.17, 1), 0.85, 0.0, None),
    "BH_FeatherRed":     ((0.4, 0.03, 0.02, 1), 0.85, 0.0, None),
    "BH_JungleLeaf":     ((0.035, 0.11, 0.025, 1), 0.7, 0.0, None),
    "BH_Coral":          ((0.75, 0.25, 0.15, 1), 0.8, 0.0, None),   # (already in ENV) fruit
}
for _n, _v in EXTRA_MATERIALS.items():
    kit.MATERIALS.setdefault(_n, _v)
    if _n not in kit.MATERIAL_NAMES:
        kit.MATERIAL_NAMES.append(_n)

GS, GSD, PAVE = "BH_GlyphStone", "BH_GlyphStoneDark", "BH_TerracePave"
PL, PLR = "BH_LimePlaster", "BH_LimePlasterRed"
WIRE, GLY, JADE, OBS, TURQ = "BH_Wire", "BH_Glyph", "BH_Jade", "BH_Obsidian", "BH_Turquoise"
BRZ, VERD, COP = "BH_Brass", "BH_Verdigris", "BH_Copper"
FEA, FEAR, LEAF = "BH_Feather", "BH_FeatherRed", "BH_JungleLeaf"
WOOD, WOODD, ROPE = "BH_Wood", "BH_WoodDark", "BH_Rope"
CLAY = "BH_Brick"   # terracotta pots


# ===============================================================================================================
# small helpers
def mm(M, N):
    return N if M is None else M @ N


def rt(k, a=0.8, b=1.0):
    return k.r.uniform(a, b)


def blk(k, x0, x1, y0, y1, z0, z1, mat, tint=1.0, chips=0, chipd=0.06, M=None, jit=0.0, bev=0.0):
    """Axis box between bounds (optionally chipped), in the frame M."""
    t = box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), bev=bev)
    if chips:
        chip(t, k.r, chips, chipd)
    if jit:
        jitter(t, k.r, jit)
    k.put(t, mat, M=mm(M, T((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)), tint=tint)


def cbox(k, x0, x1, y0, y1, z0, z1, M=None):
    k.col_box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), mm(M, T((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))


def sock(k, name, p, M=None):
    v = Vector(p)
    if M is not None:
        v = M @ v
    k.sockets.append((name, (v.x, v.y, v.z)))


def frame(c, xdir, zdir):
    """Matrix whose local X runs along xdir and local Z along (zdir made orthogonal), placed at c."""
    x = Vector(xdir).normalized()
    z = Vector(zdir)
    z = (z - x * z.dot(x)).normalized()
    y = z.cross(x)
    return Matrix(((x.x, y.x, z.x, c[0]), (x.y, y.y, z.y, c[1]), (x.z, y.z, z.z, c[2]), (0, 0, 0, 1)))


def yz_prism(pts, x0, x1):
    """Closed prism from a (y, z) outline extruded along X between x0 and x1."""
    t = tb()
    a = [t.verts.new((x0, y, z)) for y, z in pts]
    b = [t.verts.new((x1, y, z)) for y, z in pts]
    t.faces.new(a)
    t.faces.new(b[::-1])
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        t.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(t, faces=t.faces)
    return t


def xz_prism(pts, y0, y1):
    """Closed prism from an (x, z) outline extruded along Y between y0 and y1."""
    t = tb()
    a = [t.verts.new((x, y0, z)) for x, z in pts]
    b = [t.verts.new((x, y1, z)) for x, z in pts]
    t.faces.new(a)
    t.faces.new(b[::-1])
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        t.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(t, faces=t.faces)
    return t


def frustum(hx0, hy0, hx1, hy1, z0, z1):
    return hexa([(-hx0, -hy0, z0), (hx0, -hy0, z0), (hx0, hy0, z0), (-hx0, hy0, z0),
                 (-hx1, -hy1, z1), (hx1, -hy1, z1), (hx1, hy1, z1), (-hx1, hy1, z1)])


def subtract(a, b, ex):
    segs = [(a, b)]
    for (e0, e1) in ex or ():
        out = []
        for (s0, s1) in segs:
            if e1 <= s0 or e0 >= s1:
                out.append((s0, s1))
                continue
            if e0 > s0:
                out.append((s0, e0))
            if e1 < s1:
                out.append((e1, s1))
        segs = out
    return [(s0, s1) for s0, s1 in segs if s1 - s0 > 0.05]


def helix(rad, z0, z1, turns, per_turn=10, phase=0.0):
    n = max(4, int(turns * per_turn))
    return [(rad * math.cos(phase + 2 * math.pi * turns * i / n), rad * math.sin(phase + 2 * math.pi * turns * i / n),
             z0 + (z1 - z0) * i / n) for i in range(n + 1)]


def strip(k, a, b, n, w, th, mat, tint=1.0, lift=0.0, M=None):
    """Thin box lying on a surface from a to b (surface normal n), width w, thickness th."""
    a, b, n = Vector(a), Vector(b), Vector(n).normalized()
    L = (b - a).length
    if L < 1e-4:
        return
    c = (a + b) / 2 + n * (th / 2 + lift)
    k.put(box(L, w, th), mat, M=mm(M, frame(c, b - a, n)), tint=tint)


def wire_inlay(k, a, b, n, w=0.14, M=None):
    """A carved channel (dark stone lips) with the glowing Heartwire bedded in it."""
    strip(k, a, b, n, w + 0.1, 0.03, GSD, 0.28, lift=-0.012, M=M)
    strip(k, a, b, n, w * 0.5, 0.045, WIRE, 1.0, lift=-0.012, M=M)


def wire_tube(k, pts, r=0.06, segs=4, M=None):
    k.put(tube(pts, r, segs), WIRE, M=M, uvoff=False)


def moss_patch(k, x, y, z, s, M=None):
    """Low irregular cushion of moss (flattened, jittered icosphere)."""
    t = ico(0.5, 1)
    for v in t.verts:
        v.co = Vector((v.co.x * s, v.co.y * s * k.r.uniform(0.55, 0.9), max(-0.02, v.co.z * 0.12)))
    jitter(t, k.r, s * 0.1, (1, 1, 0.2))
    k.put(t, "BH_Moss", M=mm(M, TRS(x, y, z, 0, 0, k.r.uniform(0, 180))), tint=rt(k, 0.6, 0.9))


# ---------------------------------------------------------------------------------------------------------------
# relief ornament: stepped fret and glyph medallions (face-local: x along the face, z up, outward = -y)
FRET_PTS = [(0.0, 0.0), (0.2, 0.0), (0.2, 0.25), (0.4, 0.25), (0.4, 0.5), (0.6, 0.5), (0.6, 0.78), (0.78, 0.78),
            (0.78, 0.42), (0.62, 0.42), (0.62, 0.22), (0.98, 0.22), (0.98, 1.0), (0.4, 1.0), (0.4, 0.75),
            (0.2, 0.75), (0.2, 0.5), (0.0, 0.5)]


def fret_mesh(W, H, dep, mirror=False):
    pts = [(((1.0 - u) if mirror else u) * W, v * H) for u, v in FRET_PTS]
    if mirror:
        pts = pts[::-1]
    t = prism(pts, dep)
    for v in t.verts:
        v.co.y -= dep / 2
    return t


def medallion(k, M, uc, zc, s, yp, dep, boss=TURQ, mat=GS, tint=0.9):
    blk(k, uc - s / 2, uc + s / 2, yp - dep * 0.5, yp, zc - s / 2, zc + s / 2, mat, tint, M=M)
    k.put(cyl(s * 0.3, dep, 8), boss, M=mm(M, T(uc, yp, zc) @ R(90, 0, 22.5)), tint=0.95)
    for sx in (-1, 1):
        for sz in (-1, 1):
            blk(k, uc + sx * s * 0.36 - 0.03, uc + sx * s * 0.36 + 0.03, yp - dep * 0.85, yp - dep * 0.4,
                zc + sz * s * 0.36 - 0.03, zc + sz * s * 0.36 + 0.03, mat, tint, M=M)


def ornament_row(k, M, ul, ur, z0, z1, yp, dep, unit_h, pattern="mix", mat=GS, tint=(0.82, 0.98)):
    """Fill [ul, ur] x [z0, z1] on the plane y=yp with fret units / medallions projecting by dep."""
    h = min(unit_h, (z1 - z0) - 0.1)
    if h < 0.15:
        return
    zc0 = (z0 + z1) / 2 - h / 2
    W = 2.0 * h if pattern != "medallion" else 1.5 * h
    span = ur - ul - 0.1
    n = int(span // W)
    if n < 1:
        if span > h:
            medallion(k, M, (ul + ur) / 2, zc0 + h / 2, h * 0.85, yp, dep, mat=mat)
        return
    W2 = span / n
    for i in range(n):
        u0 = ul + 0.05 + i * W2
        kind = "fret"
        if pattern == "medallion" or (pattern == "mix" and i % 3 == 2):
            kind = "med"
        if kind == "fret":
            k.put(fret_mesh(W2 - 0.08, h, dep, mirror=(i % 2 == 1)), mat, M=mm(M, T(u0 + 0.04, yp, zc0)),
                  tint=k.r.uniform(*tint))
        else:
            medallion(k, M, u0 + W2 / 2, zc0 + h / 2, min(h, W2) * 0.82, yp, dep, mat=mat)


# ---------------------------------------------------------------------------------------------------------------
# coursed masonry pieces
def _mitred_block(k, Ms, L, D, pa, pb, zb, zt, dob, dot, depth, mat, tint, chips, chipd):
    pts = []
    for z, d in ((zb, dob), (zt, dot)):
        yo = -(D - d)
        yi = yo + depth
        lo = L - d
        li = max(0.0, L - d - depth)
        o0, o1 = max(pa, -lo), min(pb, lo)
        i0, i1 = max(pa, -li), min(pb, li)
        if i1 < i0:
            i0 = i1 = max(-li, min(li, (pa + pb) / 2))
        pts += [(o0, yo, z), (o1, yo, z), (i1, yi, z), (i0, yi, z)]
    if pts[1][0] - pts[0][0] < 0.04:
        return
    t = hexa(pts)
    n = k.r.randint(*chips)
    if n and pb - pa > 0.4:
        chip(t, k.r, n, chipd)
    k.put(t, mat, M=Ms, tint=tint)


def mitred_run(k, Ms, L, D, zb, zt, dob, dot, depth, lens, mat, tint, gap=0.03, chips=(0, 1), chipd=0.07, excl=(),
               alt=None, alt_p=0.0):
    """One course of blocks along a face (face-local x in [-L, L], face plane at y=-(D-d), outward -y). The outer
    inset d runs from dob (at zb) to dot (at zt) so a talus can lean back. Block ends at +-L are mitred at 45 degrees
    so four runs rotated by 0/90/180/270 close a ring."""
    r = k.r
    ws, _ = split_lengths(r, 2 * L, *lens)
    u = -L
    for i, w in enumerate(ws):
        ua = u + (gap / 2 if i else 0.0)
        ub = u + w - (gap / 2 if i < len(ws) - 1 else 0.0)
        u += w
        for pa, pb in subtract(ua, ub, excl):
            m = alt if (alt and r.random() < alt_p) else mat
            _mitred_block(k, Ms, L, D, pa, pb, zb, zt, dob, dot, depth, m, r.uniform(*tint), chips, chipd)


def sloped_wall(k, M, u0, u1, prof, thick, z0=0.0, course=(0.5, 0.7), blen=(0.8, 1.4), mat=GS, tint=(0.72, 0.92),
                gap=0.03, core=True, alt=None, alt_p=0.0, chips=(0, 1)):
    """Coursed wall along local x (u0..u1), thickness along y centred on 0, from z0 up to prof(x) (linear within a
    block). Blocks crossing the profile have their tops clamped to it; a dark core under the profile fills joints."""
    r = k.r
    zmax = max(prof(u0), prof(u1), prof((u0 + u1) / 2))
    hs = course_heights(r, zmax - z0, *course)
    zs = [z0]
    for h in hs:
        zs.append(zs[-1] + h)
    y0, y1 = -thick / 2, thick / 2
    for ci in range(len(hs)):
        zb, zt = zs[ci] + gap / 2, zs[ci + 1] - gap / 2
        ws, _ = split_lengths(r, u1 - u0, *blen)
        x = u0
        for i, w in enumerate(ws):
            xa, xb = x + (gap / 2 if i else 0), x + w - (gap / 2 if i < len(ws) - 1 else 0)
            x += w
            pa, pb = prof(xa), prof(xb)
            lim = zb + 0.06
            if max(pa, pb) < lim:
                continue
            if pa < lim:
                xa = xa + (lim - pa) / (pb - pa) * (xb - xa)
                pa = lim
            elif pb < lim:
                xb = xb - (lim - pb) / (pa - pb) * (xb - xa)
                pb = lim
            ta_, tb_ = min(zt, pa), min(zt, pb)
            c = [(xa, y0, zb), (xb, y0, zb), (xb, y1, zb), (xa, y1, zb), (xa, y0, ta_), (xb, y0, tb_), (xb, y1, tb_),
                 (xa, y1, ta_)]
            t = hexa(c)
            n = r.randint(*chips)
            if n and xb - xa > 0.35 and min(ta_, tb_) - zb > 0.25:
                chip(t, r, n, 0.06)
            m = alt if (alt and r.random() < alt_p) else mat
            k.put(t, m, M=M, tint=r.uniform(*tint))
    if core:
        N = 10
        pts = [(u0 + 0.02, z0), (u1 - 0.02, z0)]
        for i in range(N, -1, -1):
            x = lerp(u0 + 0.02, u1 - 0.02, i / N)
            pts.append((x, prof(x) - 0.05))
        k.put(xz_prism(pts, y0 + 0.04, y1 - 0.04), GSD, M=M, tint=0.28)


def coping(k, M, u0, u1, prof, width, th=0.16, mat=GS, tint=0.95, n=1):
    """Sloped capstone strip on top of a sloped wall (local frame of sloped_wall)."""
    xs = [lerp(u0, u1, i / n) for i in range(n + 1)]
    for a, b in zip(xs[:-1], xs[1:]):
        pts = [(a, prof(a) - 0.04), (b, prof(b) - 0.04), (b, prof(b) + th), (a, prof(a) + th)]
        t = xz_prism(pts, -width / 2, width / 2)
        if b - a > 0.6:
            chip(t, k.r, 1, 0.04)
        k.put(t, mat, M=M, tint=tint * k.r.uniform(0.9, 1.0))


def tier_ring(k, hx, hy, z0, H, th, ta, fo, courses=2, blen=(1.4, 2.4), unit_h=0.8, bay=4.0, orn_sides=(0, 1, 2, 3),
              wire_sides=(0,), excl=None, cornice_depth=0.7, ct=0.26, rb=0.16, plaster=PLR, plaster_p=0.75,
              mat=GS, alt=GSD, alt_p=0.18, M=None, pattern="mix", two_rows=True):
    """A talus-and-panel block ring: a leaning talus of coursed blocks (inset 0 -> ta over th), then a vertical
    panel framed by a bottom rail and a cornice (at inset fo, proud of the talus top) with painted plaster and
    relief ornament in each bay, and an optional Heartwire channel along the cornice top. excl = {side: [(u0,u1)]}."""
    r = k.r
    zp0, zp1 = z0 + th, z0 + H
    # cores (seen through joints and as the panel background)
    k.put(frustum(hx - 0.05, hy - 0.05, hx - ta - 0.03, hy - ta - 0.03, z0, zp0), GSD, M=M, tint=0.3)
    k.put(frustum(hx - ta, hy - ta, hx - ta, hy - ta, zp0, zp1 - 0.02), GS, M=M, tint=0.5)
    excl = excl or {}
    for s in range(4):
        L, D = (hx, hy) if s % 2 == 0 else (hy, hx)
        Ms = mm(M, R(0, 0, 90 * s))
        ex = excl.get(s, [])
        for ci in range(courses):
            zb = z0 + ci * th / courses + 0.015
            zt = z0 + (ci + 1) * th / courses - 0.015
            mitred_run(k, Ms, L, D, zb, zt, ta * (zb - z0) / th, ta * (zt - z0) / th, 0.45, blen, mat,
                       (0.7, 0.92) if ci == 0 else (0.78, 0.96), excl=ex, alt=alt, alt_p=alt_p * (1.6 if ci == 0 else 0.6))
        lens2 = (blen[0] * 1.2, blen[1] * 1.5)
        mitred_run(k, Ms, L, D, zp0, zp0 + rb, fo, fo, 0.5, lens2, mat, (0.85, 1.0), excl=ex)
        mitred_run(k, Ms, L, D, zp1 - ct, zp1, fo - 0.05, fo - 0.05, cornice_depth, lens2, mat, (0.86, 1.0), excl=ex)
        # stiles and bays
        Lp = L - fo
        nb = max(1, int(round(2 * Lp / bay)))
        bw = 2 * Lp / nb
        sw = 0.32
        zi0, zi1 = zp0 + rb, zp1 - ct
        yfr, ypn = -(D - fo), -(D - ta)
        for j in range(nb + 1):
            uc = -Lp + j * bw
            ua, ub = (uc, uc + sw) if j == 0 else ((uc - sw, uc) if j == nb else (uc - sw / 2, uc + sw / 2))
            for pa, pb in subtract(ua, ub, ex):
                blk(k, pa, pb, yfr, ypn + 0.05, zi0, zi1, mat, rt(k, 0.8, 0.95), M=Ms)
        for j in range(nb):
            ul = -Lp + j * bw + (sw if j == 0 else sw / 2)
            ur = -Lp + (j + 1) * bw - (sw if j == nb - 1 else sw / 2)
            for pa, pb in subtract(ul, ur, ex):
                if r.random() < plaster_p:
                    blk(k, pa + r.uniform(0, 0.25), pb - r.uniform(0, 0.25), ypn - 0.025, ypn + 0.01,
                        zi0 + r.uniform(0.0, 0.08), zi1 - r.uniform(0.0, 0.06), plaster, rt(k, 0.65, 1.0), M=Ms)
                if s in orn_sides:
                    dep = max(0.06, (ta - fo) * 0.8)
                    if two_rows and zi1 - zi0 > 1.3:
                        zm = zi0 + (zi1 - zi0) * 0.42
                        ornament_row(k, Ms, pa, pb, zm, zi1, ypn - 0.02, dep, unit_h, "fret")
                        ornament_row(k, Ms, pa, pb, zi0, zm, ypn - 0.02, dep, unit_h * 0.7, "medallion")
                    else:
                        ornament_row(k, Ms, pa, pb, zi0, zi1, ypn - 0.02, dep, unit_h, pattern)
        if s in wire_sides:
            dw = fo + 0.2
            Lw = L - dw
            for pa, pb in subtract(-Lw, Lw, ex):
                wire_inlay(k, (pa, -(D - dw), zp1), (pb, -(D - dw), zp1), (0, 0, 1), 0.14, M=Ms)


def pave(k, x0, x1, y0, y1, z, nx, ny, th=0.14, mat=PAVE, tint=(0.75, 1.0), bed=True, M=None, chips=(0, 2)):
    """Fitted paving slabs with their tops at z (a dark bed under the joints)."""
    r = k.r
    for i in range(nx):
        for j in range(ny):
            xa, xb = lerp(x0, x1, i / nx), lerp(x0, x1, (i + 1) / nx)
            ya, yb = lerp(y0, y1, j / ny), lerp(y0, y1, (j + 1) / ny)
            t = box(xb - xa - 0.035, yb - ya - 0.035, th)
            n = r.randint(*chips)
            if n:
                chip(t, r, n, 0.05)
            k.put(t, mat, M=mm(M, TRS((xa + xb) / 2, (ya + yb) / 2, z - th / 2 - r.uniform(0, 0.01),
                                      r.uniform(-0.3, 0.3), r.uniform(-0.3, 0.3), 0)), tint=r.uniform(*tint))
    if bed:
        blk(k, x0 + 0.01, x1 - 0.01, y0 + 0.01, y1 - 0.01, z - th - 0.04, z - 0.03, GSD, 0.22, M=M)


def stair_flight(k, M, w, n, rise, run, split=(0.9, 1.6), mat=GS, tint=(0.78, 0.95), core=True, chip_p=0.5):
    """Treads climbing toward local +y from y=0 (front of the first step) to y=n*run; local x in [-w/2, w/2]."""
    r = k.r
    L = n * run
    if core:
        k.put(yz_prism([(0.02, 0.0), (L, 0.0), (L, n * rise - 0.08)], -w / 2 + 0.02, w / 2 - 0.02), GSD, M=M,
              tint=0.3)
    for i in range(n):
        y0, y1 = i * run, min(L, (i + 1) * run + 0.04)
        z1 = (i + 1) * rise
        z0 = max(0.0, i * rise - 0.08)
        ws, _ = split_lengths(r, w, *split)
        x = -w / 2
        for j, ww in enumerate(ws):
            xa = x + (0.015 if j else 0.0)
            xb = x + ww - (0.015 if j < len(ws) - 1 else 0.0)
            x += ww
            t = box(xb - xa, y1 - y0, z1 - z0)
            if r.random() < chip_p:
                chip(t, r, 1, 0.05)
            k.put(t, mat, M=mm(M, TRS((xa + xb) / 2, (y0 + y1) / 2, (z0 + z1) / 2 - r.uniform(0, 0.008), 0, 0,
                                      r.uniform(-0.25, 0.25))), tint=r.uniform(*tint))


def ramp_wedge(n, rise, run, x0, x1, extra=0.0):
    """Smooth ramp collider for a flight built by stair_flight: its top runs through the middle of every tread
    (z = 0 half a tread in front of the first step, full height half a tread before the top) then stays flat."""
    L, H = n * run, n * rise
    return yz_prism([(-run / 2, 0.0), (L + extra, 0.0), (L + extra, H), (L - run / 2, H)], x0, x1)


# ---------------------------------------------------------------------------------------------------------------
# feathered serpent head (local: faces -y, base at z=0, ~1.05 tall, snout at y=-0.8, neck to y=+0.85)
def serpent_head(k, M, s=1.0, mat=GS, tint=0.9, plume=(GS, TURQ), eye=JADE, mouth=PLR, fang="BH_Bone", n_plume=9,
                 fan=(-105, 105), plume_len=0.75, plume_tint=0.95):
    r = k.r
    Ms = M @ S(s)
    c = [(-0.34, -0.62, 0.0), (0.34, -0.62, 0.0), (0.42, 0.45, 0.0), (-0.42, 0.45, 0.0),
         (-0.32, -0.66, 0.22), (0.32, -0.66, 0.22), (0.44, 0.45, 0.34), (-0.44, 0.45, 0.34)]
    t = hexa(c)
    chip(t, r, 1, 0.04)
    k.put(t, mat, M=Ms, tint=tint * 0.92)
    blk(k, -0.3, 0.3, -0.52, 0.42, 0.18, 0.5, mouth, 0.4, M=Ms)
    c = [(-0.40, -0.74, 0.44), (0.40, -0.74, 0.44), (0.47, 0.55, 0.40), (-0.47, 0.55, 0.40),
         (-0.30, -0.80, 0.80), (0.30, -0.80, 0.80), (0.40, 0.55, 1.06), (-0.40, 0.55, 1.06)]
    t = hexa(c)
    chip(t, r, 2, 0.05)
    k.put(t, mat, M=Ms, tint=tint)
    for sx in (-1, 1):
        k.put(box(0.28, 0.4, 0.17), mat, M=Ms @ TRS(sx * 0.33, -0.14, 0.95, 0, sx * -14, 0), tint=tint * 1.02)
        k.put(ico(0.1, 1), eye, M=Ms @ T(sx * 0.41, -0.2, 0.79), tint=1.0)
        k.put(cyl(0.065, 0.27, 6, r2=0.0), fang, M=Ms @ T(sx * 0.25, -0.66, 0.47) @ R(180, 0, 0), tint=0.95)
        k.put(box(0.05, 0.42, 0.03), mouth, M=Ms @ TRS(sx * 0.05, -0.86, 0.27, -18, 0, sx * 10), tint=0.7)
        # lip scroll / nostril
        k.put(cyl(0.07, 0.12, 6), mat, M=Ms @ T(sx * 0.17, -0.74, 0.78) @ R(90, 0, 0), tint=tint)
    k.put(cyl(0.085, 0.58, 8), mat, M=Ms @ T(-0.29, -0.6, 0.86) @ R(0, 90, 0), tint=tint * 0.97)
    for i in range(4):
        k.put(cyl(0.035, 0.11, 4, r2=0.0), fang, M=Ms @ T(-0.15 + 0.1 * i, -0.69, 0.46) @ R(180, 0, 0), tint=0.95)
    blk(k, -0.43, 0.43, 0.42, 0.86, 0.0, 0.98, mat, tint * 0.88, M=Ms)
    if n_plume:
        for i in range(n_plume):
            a = lerp(fan[0], fan[1], i / max(1, n_plume - 1))
            outline = [(-0.08, 0.0), (0.08, 0.0), (0.12, plume_len * 0.6), (0.0, plume_len), (-0.12, plume_len * 0.6)]
            k.put(prism(outline, 0.07), plume[i % len(plume)],
                  M=Ms @ T(0, 0.66, 0.56) @ R(0, a, 0) @ T(0, 0, 0.3) @ R(-14, 0, 0), tint=plume_tint * rt(k, 0.88, 1.0))


# ---------------------------------------------------------------------------------------------------------------
# Heartwire fittings
def cage_lamp(k, M, rc=0.13, h=0.5, ribs=6):
    """Copper wire cage round a glowing core; local origin at the core."""
    k.put(ico(rc, 1), WIRE, M=M, tint=1.0)
    R_ = rc + 0.09
    for i in range(ribs):
        a = 2 * math.pi * i / ribs
        pts = [(math.cos(a) * R_ * f, math.sin(a) * R_ * f, z) for f, z in
               ((0.45, -h / 2), (0.95, -h / 4), (1.05, 0.0), (0.95, h / 4), (0.45, h / 2))]
        k.put(tube(pts, 0.014, 4), COP, M=M, uvoff=False)
    k.put(torus(R_ * 1.02, 0.014, 12, 3), COP, M=M)
    k.put(cyl(R_ * 0.62, 0.07, 8, r2=R_ * 0.25), BRZ, M=mm(M, T(0, 0, h / 2 - 0.02)), tint=0.85)
    k.put(cyl(R_ * 0.25, 0.07, 8, r2=R_ * 0.62), BRZ, M=mm(M, T(0, 0, -h / 2 - 0.05)), tint=0.85)


def coil(k, M, rad, h, turns, wr=0.045, spool=BRZ, flange=True):
    """A copper coil (glowing Heartwire windings) on a bronze spool, base at local z=0."""
    k.put(cyl(rad - wr, h, 10), spool, M=M, tint=0.75)
    k.put(tube(helix(rad, 0.07, h - 0.07, turns, 10), wr, 4, cap_start=False, cap_end=False), WIRE, M=M, uvoff=False)
    if flange:
        for z in (0.0, h - 0.06):
            k.put(cyl(rad + 0.07, 0.06, 10), spool, M=mm(M, T(0, 0, z)), tint=0.9)


def chain(k, a, b, link=0.18, w=0.06, mat="BH_Iron"):
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    n = max(2, int(L / (link * 0.8)))
    up = Vector((0, 0, 1)) if abs(d.normalized().z) < 0.9 else Vector((1, 0, 0))
    side = d.cross(up).normalized()
    for i in range(n):
        c = a + d * ((i + 0.5) / n)
        zdir = up if i % 2 == 0 else side
        k.put(box(link, w, w * 0.45), mat, M=frame(c, d, zdir), tint=0.8)


def glyph(k, M, kind, s, dep=0.03, mat=GLY):
    """Abstract carved glyph (no letters) inside an s x s cell; face-local, outward -y, centred at the origin."""
    q = s / 10.0

    def bx(x0, x1, z0, z1):
        blk(k, x0 * q, x1 * q, -dep, 0.0, z0 * q, z1 * q, mat, 1.0, M=M)
    if kind == 0:      # eye in a ring
        for i in range(8):
            a = 2 * math.pi * i / 8
            cx, cz = math.cos(a) * 3.4, math.sin(a) * 3.4
            bx(cx - 0.8, cx + 0.8, cz - 0.8, cz + 0.8)
        bx(-1.2, 1.2, -1.2, 1.2)
    elif kind == 1:    # stepped cross
        bx(-1, 1, -4, 4)
        bx(-4, 4, -1, 1)
        for sx in (-1, 1):
            for sz in (-1, 1):
                bx(sx * 2 - 0.6, sx * 2 + 0.6, sz * 2 - 0.6, sz * 2 + 0.6)
    elif kind == 2:    # square spiral
        bx(-4, 4, 3, 4)
        bx(3, 4, -4, 4)
        bx(-4, 4, -4, -3)
        bx(-4, -3, -4, 1.5)
        bx(-4, 1.5, 0.5, 1.5)
        bx(0.5, 1.5, -1.5, 1.5)
    else:              # three bars over two dots
        for x in (-3, 0, 3):
            bx(x - 0.7, x + 0.7, -0.5, 4)
        for x in (-1.6, 1.6):
            bx(x - 0.9, x + 0.9, -3.8, -2.0)


def pot(k, M, h=0.5, rad=0.22, mat=CLAY, tint=0.9, plant=False):
    prof = [(0.0, 0.0), (rad * 0.55, 0.0), (rad * 0.9, h * 0.18), (rad, h * 0.45), (rad * 0.85, h * 0.78),
            (rad * 0.5, h * 0.9), (rad * 0.58, h), (rad * 0.45, h)]
    k.put(lathe(prof, 10), mat, M=M, tint=tint, smooth=50)
    if plant:
        for i in range(5):
            a = i * 72 + k.r.uniform(-15, 15)
            k.put(cyl(0.035, h * 0.9, 4, r2=0.0), LEAF, M=mm(M, T(0, 0, h * 0.9) @ R(0, 0, a) @ R(28, 0, 0)), tint=0.9)


def curtain(k, M, w, h, mats, rows=4, cols=8, wave=0.04):
    """Woven door curtain hanging from local z=h down to z=0, centred on x, in the plane y~0 (both faces)."""
    r = k.r
    for j in range(rows):
        za, zb = h * j / rows, h * (j + 1) / rows
        t = tb()
        vs = []
        for jj, z in enumerate((za, zb)):
            row = []
            for i in range(cols + 1):
                x = -w / 2 + w * i / cols
                y = wave * math.sin(i * 1.9 + 0.6) * (0.4 + 0.6 * (1 - z / h))
                row.append(t.verts.new((x, y, z)))
            vs.append(row)
        for i in range(cols):
            t.faces.new((vs[0][i], vs[0][i + 1], vs[1][i + 1], vs[1][i]))
        k.put(two_sided(t), mats[j % len(mats)], M=M, tint=rt(k, 0.8, 1.0))


def two_sided(t, off=0.006):
    """Give a single-sided sheet a back face (separate verts, offset a hair behind, reversed winding)."""
    t.normal_update()
    faces = list(t.faces)
    vmap = {v: t.verts.new(v.co - v.normal * off) for v in list(t.verts)}
    for f in faces:
        t.faces.new([vmap[v] for v in reversed(f.verts)])
    return t


# ===============================================================================================================
# The Crown of Steps
PYR_TIERS, PYR_TH = 5, 3.2
PYR_B = [16.0 - 2.6 * i for i in range(PYR_TIERS)]
PYR_TA, PYR_FO, PYR_THL = 0.6, 0.45, 1.8


@asset("zr_step_pyramid", CAT)
def zr_step_pyramid(k):
    r = k.r
    bs, TH, TA, FO = PYR_B, PYR_TH, PYR_TA, PYR_FO
    top = PYR_TIERS * TH                     # 16 m
    n, rise, run = 50, 0.32, 0.425           # 37 degree monumental stair
    y_top = -(bs[-1] - FO)                   # front edge of the top platform (-5.15)
    yf = y_top - n * run                     # foot of the stair (-26.4)
    SW, BW = 3.0, 1.0                        # half tread width, balustrade width
    ex_front = {0: [(-(SW + BW) - 0.02, SW + BW + 0.02)]}
    for i, b in enumerate(bs):
        z0 = i * TH
        tier_ring(k, b, b, z0, TH, PYR_THL, TA, FO, courses=2, blen=(2.4, 4.0), unit_h=0.8, bay=5.2,
                  orn_sides=(0, 1, 3), wire_sides=(0, 1, 2, 3), excl=ex_front, cornice_depth=0.9, ct=0.3, rb=0.18)
        if i < PYR_TIERS - 1:
            h = b - FO - 0.85
            blk(k, -h, h, -h, h, z0 + TH - 0.25, z0 + TH - 0.004, PAVE, rt(k, 0.68, 0.8))
        k.col_mesh(frustum(b, b, b - FO, b - FO, z0, z0 + TH))
        # moss gathered at the foot of each tier (on the ledge below)
        for _ in range(7):
            s = r.randrange(4)
            u = r.uniform(-b + 1, b - 1)
            if s == 0 and abs(u) < SW + BW + 0.5:
                continue
            Ms = R(0, 0, 90 * s)
            moss_patch(k, u, -(b + r.uniform(0.1, 0.5)), z0, r.uniform(0.4, 0.9), M=Ms)
    # top platform paving
    ph = bs[-1] - FO - 0.85
    pave(k, -ph, ph, -ph, ph, top, 4, 4, th=0.2)
    # Heartwire running down every corner of every tier and out into the ground
    for sx in (-1, 1):
        for sy in (-1, 1):
            o = 0.07
            pts = [(bs[0] + 2.8, 0.03)]
            for i, b in enumerate(bs):
                z0 = i * TH
                pts += [(b + o, z0 + 0.03), (b - TA + o, z0 + PYR_THL), (b - FO + o, z0 + PYR_THL + 0.04),
                        (b - FO + o, z0 + TH + 0.03)]
                if i < PYR_TIERS - 1:
                    pts.append((bs[i + 1] + o, z0 + TH + 0.03))
            wire_tube(k, [(sx * d, sy * d, z) for d, z in pts], r=0.07)
    # --- the front stair with serpent balustrades
    Mst = T(0, yf, 0)
    stair_flight(k, Mst, 2 * SW, n, rise, run, split=(1.6, 3.0), tint=(0.76, 0.94))
    k.col_mesh(ramp_wedge(n, rise, run, -SW, SW, extra=0.05), Mst)
    Lst = n * run
    slope = rise / run
    over = 0.95
    prof = (lambda u: over + max(0.0, u) * slope)
    for sx in (-1, 1):
        xc = sx * (SW + BW / 2)
        Mb = T(xc, yf, 0) @ R(0, 0, 90)
        sloped_wall(k, Mb, -0.6, Lst, prof, BW, course=(0.75, 1.05), blen=(1.5, 2.6), tint=(0.7, 0.9), alt=GSD,
                    alt_p=0.12)
        coping(k, Mb, -0.6, Lst, prof, BW + 0.12, th=0.2, n=6)
        a = Vector((-0.2, 0, prof(-0.2) + 0.2))
        b = Vector((Lst - 0.4, 0, prof(Lst - 0.4) + 0.2))
        wire_inlay(k, a, b, (-slope, 0, 1), 0.16, M=Mb)
        # newel block at the top and the serpent head at the foot
        blk(k, xc - 0.62, xc + 0.62, y_top - 1.3, y_top, top - 0.2, top + 1.35, GS, 0.9, chips=2, chipd=0.08)
        wire_inlay(k, (xc, y_top - 1.3, top + 1.35), (xc, y_top, top + 1.35), (0, 0, 1), 0.12)
        serpent_head(k, T(xc, yf - 0.95, 0), s=1.3, plume=(GS, TURQ, GS), fan=(-80, 80), n_plume=7)
        k.col_mesh(xz_prism([(-1.0, 0), (Lst, 0), (Lst, prof(Lst) + 0.3), (-1.0, over + 0.3)], -BW / 2, BW / 2), Mb)
        cbox(k, xc - 0.6, xc + 0.6, yf - 2.1, yf - 0.5, 0, 1.4)
    sock(k, "stair_foot", (0, yf, 0))
    # --- the priests' switchback stair up the east face: one flight per tier, landings onto each ledge
    s_y, d = -5.5, 1
    for i in range(PYR_TIERS):
        b = bs[i]
        z0 = i * TH
        xin, xout = b - TA, b + 2.0
        w = xout - xin
        cx = (xin + xout) / 2
        nn, rs, rn = 10, TH / 10, 0.4
        Lf = nn * rn
        M = T(cx, s_y, z0) @ (R(0, 0, 0) if d > 0 else R(0, 0, 180))
        stair_flight(k, M, w, nn, rs, rn, split=(1.0, 1.6), tint=(0.74, 0.92))
        side = 1 if d > 0 else -1          # local x of the outer (east) edge
        pr = (lambda u, rs=rs, rn=rn: 0.8 + max(0.0, u) * rs / rn)
        Mb = M @ T(side * (w / 2 - 0.15), 0, 0) @ R(0, 0, 90)
        sloped_wall(k, Mb, -0.2, Lf, pr, 0.3, course=(0.45, 0.65), blen=(0.8, 1.3), tint=(0.68, 0.88))
        coping(k, Mb, -0.2, Lf, pr, 0.38, th=0.12, n=2)
        # landing block (local y Lf .. Lf+1.6), coursed outer faces, paved top, parapet on the outer edge and end
        LL = 1.6
        Ml = M @ T(side * (w / 2 - 0.15), Lf + LL / 2, 0) @ R(0, 0, 90)
        sloped_wall(k, Ml, -LL / 2, LL / 2, (lambda u: TH), 0.3, course=(0.5, 0.7), blen=(0.7, 1.0), core=False)
        Me = M @ T(0, Lf + LL - 0.15, 0)
        sloped_wall(k, Me, -w / 2, w / 2, (lambda u: TH), 0.3, course=(0.5, 0.7), blen=(0.8, 1.3), core=False)
        blk(k, -w / 2 + 0.05, w / 2 - 0.05, Lf, Lf + LL - 0.05, 0, TH - 0.14, GSD, 0.3, M=M)
        pave(k, -w / 2, w / 2, Lf, Lf + LL, TH, 2, 1, th=0.14, M=M, bed=False)
        for (x0_, x1_, y0_, y1_) in ((side * (w / 2 - 0.3), side * w / 2, Lf, Lf + LL),
                                     (-w / 2 + 0.6, w / 2, Lf + LL - 0.3, Lf + LL)):
            blk(k, x0_, x1_, y0_, y1_, TH, TH + 0.8, GS, rt(k, 0.82, 0.95), chips=1, M=M)
            blk(k, x0_ - 0.04 * side, x1_ + 0.04 * side, y0_ - 0.04, y1_ + 0.04, TH + 0.8, TH + 0.92, GS, 0.95, M=M)
            cbox(k, x0_, x1_, y0_, y1_, TH, TH + 0.9, M=M)
        # collision: ramp, landing, outer rail
        xr0, xr1 = (-w / 2, w / 2 - 0.3) if side > 0 else (-w / 2 + 0.3, w / 2)
        k.col_mesh(ramp_wedge(nn, rs, rn, xr0, xr1), M)
        cbox(k, -w / 2, w / 2, Lf, Lf + LL, 0, TH, M=M)
        k.col_mesh(xz_prism([(-0.3, 0), (Lf, 0), (Lf, pr(Lf) + 0.1), (-0.3, 0.9)], -0.15, 0.15), Mb)
        # next flight starts on the ledge above, climbing back the other way
        t_end = s_y + Lf * d
        s_y = t_end - 0.2 * d
        d = -d
    # --- the shrine and the Dawn conduit
    zt = top
    sx0, sx1, sy0, sy1, wt, hz = -3.0, 3.0, 0.4, 4.6, 0.6, 3.6
    from masonry import masonry
    masonry(k, sx0, sx1, 0, hz, wt, mat=GS, core_mat=GSD, bev=0.0, course=(0.5, 0.7), blen=(0.7, 1.3),
            M=T(0, sy1 - wt / 2, zt), chip_rng=(0, 1), tint=(0.75, 0.92))
    for sxx in (-1, 1):
        masonry(k, -(sy1 - sy0 - wt) / 2, (sy1 - sy0 - wt) / 2, 0, hz, wt, mat=GS, core_mat=GSD, bev=0.0,
                course=(0.5, 0.7), blen=(0.7, 1.3), M=T(sxx * (sx1 - wt / 2), (sy0 + sy1 - wt) / 2, zt) @ R(0, 0, 90),
                chip_rng=(0, 1), tint=(0.75, 0.92))
        blk(k, sxx * (sx1 - wt) - 0.02 * sxx, sxx * (sx1 - wt) + 0.0, sy0 + 0.2, sy1 - wt, zt + 0.3, zt + hz - 0.2, PLR,
            0.8)
        cbox(k, sxx * sx1, sxx * (sx1 - wt), sy0, sy1, zt, zt + hz)
    blk(k, sx0 + wt, sx1 - wt, sy1 - wt - 0.02, sy1 - wt, zt + 0.3, zt + hz - 0.2, PLR, 0.8)
    cbox(k, sx0, sx1, sy1 - wt, sy1, zt, zt + hz)
    # lintel with glowing glyphs, roof, frieze and roof comb
    blk(k, sx0 - 0.1, sx1 + 0.1, sy0 - 0.15, sy0 + 0.75, zt + hz - 0.75, zt + hz, GS, 0.95, chips=2)
    for i, kind in enumerate((2, 0, 1, 0, 2)):
        glyph(k, T(-2.2 + i * 1.1, sy0 - 0.15, zt + hz - 0.38), kind, 0.55)
    blk(k, sx0 - 0.35, sx1 + 0.35, sy0 - 0.45, sy1 + 0.3, zt + hz, zt + hz + 0.35, GS, 0.9, chips=2)
    blk(k, sx0 - 0.2, sx1 + 0.2, sy0 - 0.3, sy1 + 0.15, zt + hz + 0.35, zt + hz + 1.0, PLR, 0.85)
    ornament_row(k, T(0, sy0 - 0.3, 0), sx0 - 0.15, sx1 + 0.15, zt + hz + 0.4, zt + hz + 0.95, 0.0, 0.08, 0.5, "fret")
    blk(k, sx0 - 0.35, sx1 + 0.35, sy0 - 0.45, sy1 + 0.3, zt + hz + 1.0, zt + hz + 1.2, GS, 0.95)
    for i in range(5):
        x = -2.4 + i * 1.2
        blk(k, x - 0.42, x + 0.42, sy0 - 0.2, sy0 + 0.3, zt + hz + 1.2, zt + hz + 1.6, GS, rt(k, 0.85, 0.95), chips=1)
        blk(k, x - 0.24, x + 0.24, sy0 - 0.15, sy0 + 0.25, zt + hz + 1.6, zt + hz + 1.9, GS, rt(k, 0.85, 0.95))
    wire_inlay(k, (sx0 - 0.1, sy0 - 0.15, zt + hz - 0.6), (sx1 + 0.1, sy0 - 0.15, zt + hz - 0.6), (0, -1, 0), 0.1)
    cbox(k, sx0 - 0.35, sx1 + 0.35, sy0 - 0.45, sy1 + 0.3, zt + hz - 0.75, zt + hz + 1.2)
    # Dawn conduit: stepped plinth, wire-wound pillar through the roof, crowned by a caged orb
    cy = 2.8
    blk(k, -0.75, 0.75, cy - 0.75, cy + 0.75, zt, zt + 0.3, GS, 0.9, chips=1)
    blk(k, -0.55, 0.55, cy - 0.55, cy + 0.55, zt + 0.3, zt + 0.6, JADE, 0.85)
    z_c1 = zt + hz + 2.6
    k.put(cyl(0.3, z_c1 - zt - 0.6, 10), OBS, M=T(0, cy, zt + 0.6), tint=0.9)
    k.put(tube(helix(0.34, zt + 0.75, zt + hz - 0.15, 8, 12), 0.05, 4), WIRE, M=T(0, cy, 0), uvoff=False)
    for z in (zt + 0.7, zt + 1.8, zt + 2.9):
        k.put(torus(0.37, 0.05, 14, 4), COP, M=T(0, cy, z))
    k.put(tube(helix(0.34, zt + hz + 1.25, z_c1 - 0.2, 3, 12), 0.05, 4), WIRE, M=T(0, cy, 0), uvoff=False)
    k.put(cyl(0.5, 0.18, 10, r2=0.36), BRZ, M=T(0, cy, z_c1 - 0.05), tint=0.9)
    cage_lamp(k, T(0, cy, z_c1 + 0.42), rc=0.24, h=0.75, ribs=8)
    k.put(cyl(0.05, 0.6, 6, r2=0.0), BRZ, M=T(0, cy, z_c1 + 0.8))
    sock(k, "light", (0, cy, zt + 2.0))
    sock(k, "top", (0, -1.2, zt))
    cbox(k, -0.75, 0.75, cy - 0.75, cy + 0.75, zt, zt + hz)
    return dict(recenter=False, damp=0.22, damp_h=1.2)


# ===============================================================================================================
# terraces and stairs
def terrace(k, H):
    if H <= 2.0:
        th, ta, fo, crs, uh, rb, ct = 0.8, 0.26, 0.11, 1, 0.6, 0.14, 0.24
    else:
        th, ta, fo, crs, uh, rb, ct = 2.0, 0.42, 0.2, 2, 0.72, 0.18, 0.3
    tier_ring(k, 4.0, 4.0, 0.0, H, th, ta, fo, courses=crs, blen=(1.2, 2.2), unit_h=uh, bay=3.8,
              orn_sides=(0, 1, 2, 3), wire_sides=(0,), cornice_depth=0.55, ct=ct, rb=rb)
    ph = 4.0 - fo - 0.5 + 0.01
    pave(k, -ph, ph, -ph, ph, H, 3, 3)
    r = k.r
    for s in range(4):
        Ms = R(0, 0, 90 * s)
        for _ in range(3):
            moss_patch(k, r.uniform(-3.4, 3.4), -(4.0 + r.uniform(0.0, 0.25)), 0.0, r.uniform(0.3, 0.7), M=Ms)
    for _ in range(3):
        moss_patch(k, r.uniform(-ph + 0.3, ph - 0.3), r.uniform(-ph + 0.3, ph - 0.3), H, r.uniform(0.25, 0.5))
    k.col_box(8.0, 8.0, H, T(0, 0, H / 2))
    return dict(recenter=False, damp=0.22, damp_h=0.9)


@asset("zr_terrace_2m", CAT)
def zr_terrace_2m(k):
    return terrace(k, 2.0)


@asset("zr_terrace_4m", CAT)
def zr_terrace_4m(k):
    return terrace(k, 4.0)


def town_stair(k, H, L):
    n = int(round(H / 0.25))
    rise, run = H / n, L / n
    TW = 3.0
    stair_flight(k, None, TW, n, rise, run, split=(0.8, 1.5))
    slope = H / L
    over = 0.75
    prof = (lambda u: over + max(0.0, u) * slope)
    for sx in (-1, 1):
        xc = sx * (TW / 2 + 0.25)
        Mb = T(xc, 0, 0) @ R(0, 0, 90)
        sloped_wall(k, Mb, -0.15, L, prof, 0.5, course=(0.4, 0.6), blen=(0.7, 1.2))
        coping(k, Mb, -0.15, L, prof, 0.6, th=0.14, n=2)
        wire_inlay(k, (0.0, 0, prof(0.0) + 0.14), (L - 0.15, 0, prof(L - 0.15) + 0.14), (-slope, 0, 1), 0.12, M=Mb)
        serpent_head(k, T(xc, -0.65, 0), s=0.78, fan=(-62, 62), n_plume=5, plume_len=0.62)
        k.col_mesh(xz_prism([(-0.3, 0), (L, 0), (L, prof(L) + 0.15), (-0.3, over + 0.15)], -0.25, 0.25), Mb)
        cbox(k, xc - 0.35, xc + 0.35, -1.25, -0.3, 0, 0.85)
    k.col_mesh(ramp_wedge(n, rise, run, -TW / 2, TW / 2))
    return dict(recenter=False, damp=0.2, damp_h=0.6)


@asset("zr_stair_2m", CAT)
def zr_stair_2m(k):
    return town_stair(k, 2.0, 4.0)


@asset("zr_stair_4m", CAT)
def zr_stair_4m(k):
    return town_stair(k, 4.0, 7.0)


# ===============================================================================================================
# houses
def stone_plinth(k, hx, hy, h, lens=(0.6, 1.1)):
    for s in range(4):
        L, D = (hx, hy) if s % 2 == 0 else (hy, hx)
        mitred_run(k, R(0, 0, 90 * s), L, D, 0.0, h, 0.0, 0.0, 0.45, lens, GS, (0.62, 0.82), chips=(0, 1), alt=GSD,
                   alt_p=0.3)


def plaster_coat(k, M, u0, u1, z0, z1, y_face, mat, tint=0.9, jag=0.28, holes=1):
    """Plaster skin on a wall face (face-local frame: x along, outward -y) with a ragged, flaked lower edge and a
    few patches where the stones underneath show through."""
    r = k.r
    N = max(2, int((u1 - u0) / 0.35))
    bottom = [(lerp(u0, u1, i / N), z0 + (r.uniform(0.0, jag) if 0 < i < N else 0.0)) for i in range(N + 1)]
    pts = bottom + [(u1, z1), (u0, z1)]
    t = prism(pts, 0.04)
    k.put(t, mat, M=mm(M, T(0, y_face - 0.02, 0)), tint=tint)
    for _ in range(holes):
        cx, cz = r.uniform(u0 + 0.6, u1 - 0.6), r.uniform(z0 + 0.6, z1 - 0.5)
        for j in range(3):
            w = r.uniform(0.25, 0.45)
            blk(k, cx - w / 2 + j * 0.12, cx + w / 2 + j * 0.12, y_face - 0.075, y_face - 0.03,
                cz - 0.1 + j * 0.17, cz + 0.06 + j * 0.17, GS, rt(k, 0.6, 0.8), chips=1, chipd=0.03, M=M)


def house_body(k, hx, hy, z0, z1, wall, frieze, door_u=0.0, door_w=1.4, door_h=2.3, curtain_mats=("BH_ClothTeal",),
               windows=True, frieze_sides=(0, 1, 3), frieze_h=(0.4, 0.3)):
    """Thick plastered stone box (x in [-hx,hx], y in [-hy,hy]) with a doorway on -y. Returns nothing."""
    r = k.r
    dz1 = z0 + door_h
    dx0, dx1 = door_u - door_w / 2, door_u + door_w / 2
    # solid core behind the door recess, front wall pieces around the door
    blk(k, -hx + 0.02, hx - 0.02, -hy + 0.6, hy - 0.02, z0, z1, GSD, 0.45)
    blk(k, -hx + 0.02, dx0, -hy + 0.02, -hy + 0.62, z0, z1, GSD, 0.45)
    blk(k, dx1, hx - 0.02, -hy + 0.02, -hy + 0.62, z0, z1, GSD, 0.45)
    blk(k, dx0 - 0.01, dx1 + 0.01, -hy + 0.02, -hy + 0.62, dz1, z1, GSD, 0.45)
    blk(k, dx0, dx1, -hy + 0.58, -hy + 0.62, z0, dz1, GSD, 0.07)    # dark interior
    # plaster on all faces (front split round the door)
    fz0, fz1 = z1 - frieze_h[0] - frieze_h[1], z1 - frieze_h[1]
    for s in range(4):
        L, D = (hx, hy) if s % 2 == 0 else (hy, hx)
        Ms = R(0, 0, 90 * s)
        if s == 0:
            plaster_coat(k, Ms, -L, dx0 - 0.22, z0 + 0.05, fz0, -D, wall, rt(k, 0.82, 0.95), holes=1)
            plaster_coat(k, Ms, dx1 + 0.22, L, z0 + 0.05, fz0, -D, wall, rt(k, 0.82, 0.95), holes=0)
            plaster_coat(k, Ms, dx0 - 0.22, dx1 + 0.22, dz1 + 0.3, fz0, -D, wall, rt(k, 0.82, 0.95), jag=0.0,
                         holes=0)
        else:
            plaster_coat(k, Ms, -L, L, z0 + 0.05, fz0, -D, wall, rt(k, 0.8, 0.95), holes=1 if r.random() < 0.6 else 0)
        # frieze band
        blk(k, -L - 0.03, L + 0.03, -D - 0.06, -D + 0.1, fz0, fz1, frieze if s in frieze_sides else wall,
            rt(k, 0.8, 0.95), M=Ms)
        if s in frieze_sides:
            ornament_row(k, Ms, -L + 0.1, L - 0.1, fz0 + 0.03, fz1 - 0.03, -D - 0.06, 0.06, frieze_h[0] * 0.8, "fret")
        blk(k, -L - 0.04, L + 0.04, -D - 0.08, -D + 0.1, fz1, z1, wall, rt(k, 0.85, 0.95), M=Ms)
        if windows and s in (1, 3):
            for u in (-L * 0.45, L * 0.45):
                blk(k, u - 0.3, u + 0.3, -D - 0.035, -D + 0.02, z0 + 1.35, z0 + 1.95, GSD, 0.08, M=Ms)
                blk(k, u - 0.42, u + 0.42, -D - 0.1, -D + 0.05, z0 + 1.95, z0 + 2.1, WOODD, 0.8, M=Ms)
                blk(k, u - 0.38, u + 0.38, -D - 0.12, -D + 0.05, z0 + 1.25, z0 + 1.35, GS, 0.85, M=Ms)
    # door frame: jambs, glyph lintel, threshold, curtain
    for sx in (dx0 - 0.11, dx1 + 0.11):
        blk(k, sx - 0.13, sx + 0.13, -hy - 0.08, -hy + 0.2, z0, dz1, GS, rt(k, 0.85, 0.95), chips=1, chipd=0.04)
    blk(k, dx0 - 0.35, dx1 + 0.35, -hy - 0.1, -hy + 0.2, dz1, dz1 + 0.34, GS, 0.92, chips=2, chipd=0.04)
    ornament_row(k, None, dx0 - 0.2, dx1 + 0.2, dz1 + 0.04, dz1 + 0.3, -hy - 0.1, 0.04, 0.22, "fret")
    blk(k, dx0 - 0.1, dx1 + 0.1, -hy - 0.25, -hy + 0.3, z0 - 0.02, z0 + 0.06, GS, 0.8)
    curtain(k, T(door_u, -hy + 0.25, z0 + 0.35), door_w - 0.06, door_h - 0.38, curtain_mats, rows=5, cols=8)
    k.put(cyl(0.035, door_w + 0.1, 6), WOODD, M=T(dx0 - 0.05, -hy + 0.25, dz1 - 0.04) @ R(0, 90, 0))


def vigas(k, hx, hy, z, step=0.9, out=0.38):
    n = int((2 * hx - 0.6) / step)
    for i in range(n + 1):
        x = -hx + 0.3 + i * (2 * hx - 0.6) / max(1, n)
        for sy in (-1, 1):
            k.put(cyl(0.085, out + 0.1, 6), WOODD, M=T(x, sy * (hy - 0.1), z) @ R(-90 * sy, 0, 0) @ R(0, 0, 22.5),
                  tint=rt(k, 0.7, 0.95))


def roof_parapet(k, hx, hy, z, h, wall, th=0.28, gaps=(), merlons=False):
    r = k.r
    blk(k, -hx - 0.06, hx + 0.06, -hy - 0.06, hy + 0.06, z - 0.15, z, wall, 0.8)
    for s in range(4):
        L, D = (hx, hy) if s % 2 == 0 else (hy, hx)
        Ms = R(0, 0, 90 * s)
        for pa, pb in subtract(-L, L, gaps[s] if gaps else ()):
            pa2 = pa if pa > -L + 0.01 else -L
            blk(k, pa2, pb, -D, -D + th, z, z + h, wall, rt(k, 0.82, 0.95), M=Ms)
            ws, _ = split_lengths(r, pb - pa2, 0.5, 0.9)
            x = pa2
            for w in ws:
                blk(k, x + 0.01, x + w - 0.01, -D - 0.04, -D + th + 0.04, z + h, z + h + 0.1, GS, rt(k, 0.85, 1.0),
                    chips=1, chipd=0.03, M=Ms)
                x += w
            if merlons and s == 0:
                nm = int((pb - pa2) / 1.1)
                for i in range(nm):
                    x = pa2 + (i + 0.5) * (pb - pa2) / nm
                    blk(k, x - 0.3, x + 0.3, -D, -D + th, z + h + 0.1, z + h + 0.32, GS, 0.9, M=Ms)
                    blk(k, x - 0.16, x + 0.16, -D + 0.03, -D + th - 0.03, z + h + 0.32, z + h + 0.5, GS, 0.9, M=Ms)
    # rain spouts
    for sx in (-1, 1):
        blk(k, sx * (hx - 0.6) - 0.1, sx * (hx - 0.6) + 0.1, -hy - 0.5, -hy + 0.1, z - 0.05, z + 0.08, GS, 0.8)


def door_lamp(k, x, y, z, name="door_light"):
    blk(k, x - 0.07, x + 0.07, y - 0.02, y + 0.1, z + 0.05, z + 0.35, GS, 0.85)
    k.put(cyl(0.025, 0.35, 6), BRZ, M=T(x, y + 0.05, z + 0.32) @ R(90, 0, 0))
    k.put(cyl(0.02, 0.12, 6), BRZ, M=T(x, y - 0.29, z + 0.32) @ R(180, 0, 0))
    cage_lamp(k, T(x, y - 0.29, z), rc=0.09, h=0.34, ribs=5)
    sock(k, name, (x, y - 0.29, z))


@asset("zr_house_a", CAT)
def zr_house_a(k):
    r = k.r
    hx = hy = 3.5
    stone_plinth(k, hx + 0.05, hy + 0.05, 0.45)
    house_body(k, hx, hy, 0.45, 3.5, PL, PLR, door_u=0.0, curtain_mats=("BH_ClothTeal", "BH_ClothRed", "BH_ClothTeal",
                                                                         "BH_ClothOchre"))
    vigas(k, hx, hy, 3.3)
    roof_parapet(k, hx, hy, 3.62, 0.5, PL)
    door_lamp(k, 1.3, -hy - 0.08, 2.35)
    # bench and water jar by the door, pots on the parapet
    blk(k, -2.9, -1.3, -hy - 0.6, -hy - 0.05, 0, 0.45, GS, 0.8, chips=2)
    pot(k, T(-2.6, -hy - 0.5, 0.0), h=0.75, rad=0.3, tint=0.85)
    for (x, y, pl) in ((-3.2, -3.2, True), (3.2, -3.2, False), (3.15, 3.2, True), (-0.4, -3.25, False)):
        pot(k, T(x, y, 4.22), h=r.uniform(0.35, 0.5), rad=r.uniform(0.16, 0.22), tint=rt(k, 0.75, 0.95), plant=pl)
    sock(k, "door", (0.0, -hy - 0.7, 0.0))
    cbox(k, -hx - 0.05, hx + 0.05, -hy - 0.05, hy + 0.05, 0, 4.2)
    cbox(k, -2.9, -1.3, -hy - 0.6, -hy, 0, 0.45)
    return dict(recenter=False, damp=0.25, damp_h=0.7)


@asset("zr_house_b", CAT)
def zr_house_b(k):
    r = k.r
    hx, hy = 4.0, 3.0
    stone_plinth(k, hx + 0.05, hy + 0.05, 0.4)
    house_body(k, hx, hy, 0.4, 3.5, PLR, PL, door_u=1.3, curtain_mats=("BH_ClothOchre", "BH_ClothBlack",
                                                                        "BH_ClothOchre", "BH_ClothCream"))
    vigas(k, hx, hy, 3.3)
    roof_parapet(k, hx, hy, 3.62, 0.42, PLR, merlons=True)
    # raised back room on the roof (stepped massing)
    ux0, ux1, uy0, uy1 = -3.5, -0.6, -0.4, 2.6
    blk(k, ux0, ux1, uy0, uy1, 3.6, 5.5, GSD, 0.45)
    for s in range(4):
        L = (ux1 - ux0) / 2 if s % 2 == 0 else (uy1 - uy0) / 2
        D = (uy1 - uy0) / 2 if s % 2 == 0 else (ux1 - ux0) / 2
        Ms = T((ux0 + ux1) / 2, (uy0 + uy1) / 2, 0) @ R(0, 0, 90 * s)
        plaster_coat(k, Ms, -L, L, 3.62, 5.15, -D, PLR, rt(k, 0.8, 0.92), jag=0.12, holes=0)
        blk(k, -L - 0.03, L + 0.03, -D - 0.06, -D + 0.1, 5.15, 5.5, PL, 0.88, M=Ms)
    blk(k, -2.45, -1.65, uy0 - 0.04, uy0 + 0.05, 3.62, 5.0, GSD, 0.08)
    blk(k, ux0 - 0.1, ux1 + 0.1, uy0 - 0.1, uy1 + 0.1, 5.5, 5.68, GS, 0.9, chips=2)
    # cane awning over the door
    for x in (0.1, 2.5):
        k.put(cyl(0.06, 2.45, 6), WOODD, M=T(x, -hy - 1.25, 0.0), tint=0.85)
    k.put(box(2.8, 1.5, 0.08), "BH_Thatch", M=TRS(1.3, -hy - 0.62, 2.48, -9, 0, 0), tint=0.9)
    for i in range(6):
        k.put(cyl(0.03, 2.9, 5), WOODD, M=T(-0.15, -hy - 1.3 + i * 0.27, 2.54 + i * 0.04) @ R(0, 90, 0), tint=0.8)
    door_lamp(k, -0.1, -hy - 0.08, 2.3)
    pot(k, T(-3.4, -hy - 0.4, 0.0), h=0.7, rad=0.28, tint=0.85)
    pot(k, T(-2.85, -hy - 0.35, 0.0), h=0.5, rad=0.2, tint=0.8, plant=True)
    for (x, y, pl) in ((3.6, -2.6, True), (3.6, 2.6, False), (0.4, 2.6, True)):
        pot(k, T(x, y, 4.15), h=r.uniform(0.35, 0.5), rad=r.uniform(0.16, 0.22), tint=rt(k, 0.75, 0.95), plant=pl)
    sock(k, "door", (1.3, -hy - 0.8, 0.0))
    cbox(k, -hx - 0.05, hx + 0.05, -hy - 0.05, hy + 0.05, 0, 4.15)
    cbox(k, ux0, ux1, uy0, uy1, 3.6, 5.7)
    for x in (0.1, 2.5):
        cbox(k, x - 0.07, x + 0.07, -hy - 1.32, -hy - 1.18, 0, 2.45)
    return dict(recenter=False, damp=0.25, damp_h=0.7)


@asset("zr_house_c", CAT)
def zr_house_c(k):
    r = k.r
    bx0, bx1, by0, by1 = -4.8, 3.4, -4.0, 4.0
    hx, hy = (bx1 - bx0) / 2, (by1 - by0) / 2
    cx = (bx0 + bx1) / 2
    ZR = 5.0                                     # roof terrace level
    Mc = T(cx, 0, 0)
    # plinth + two storeys (house_body is centred, so build it in a shifted frame)
    for s in range(4):
        L, D = (hx + 0.05, hy + 0.05) if s % 2 == 0 else (hy + 0.05, hx + 0.05)
        mitred_run(k, Mc @ R(0, 0, 90 * s), L, D, 0.0, 0.4, 0.0, 0.0, 0.45, (0.6, 1.1), GS, (0.62, 0.82), alt=GSD,
                   alt_p=0.3)
    # house_body works in the origin frame: temporarily emulate by building pieces with Mc
    dz0 = 0.4
    door_u, door_w, door_h = -1.6, 1.4, 2.3
    dx0, dx1 = door_u - door_w / 2, door_u + door_w / 2
    z1 = ZR
    blk(k, bx0 + 0.02, bx1 - 0.02, by0 + 0.6, by1 - 0.02, dz0, z1, GSD, 0.45)
    blk(k, bx0 + 0.02, dx0, by0 + 0.02, by0 + 0.62, dz0, z1, GSD, 0.45)
    blk(k, dx1, bx1 - 0.02, by0 + 0.02, by0 + 0.62, dz0, z1, GSD, 0.45)
    blk(k, dx0 - 0.01, dx1 + 0.01, by0 + 0.02, by0 + 0.62, dz0 + door_h, z1, GSD, 0.45)
    blk(k, dx0, dx1, by0 + 0.58, by0 + 0.62, dz0, dz0 + door_h, GSD, 0.07)
    for s in range(4):
        L, D = (hx, hy) if s % 2 == 0 else (hy, hx)
        Ms = Mc @ R(0, 0, 90 * s)
        if s == 0:
            plaster_coat(k, Mc, bx0 - cx, dx0 - cx - 0.22, dz0 + 0.05, ZR - 0.05, by0, PL, 0.9, holes=1)
            plaster_coat(k, Mc, dx1 - cx + 0.22, bx1 - cx, dz0 + 0.05, ZR - 0.05, by0, PL, 0.9, holes=1)
            plaster_coat(k, Mc, dx0 - cx - 0.22, dx1 - cx + 0.22, dz0 + door_h + 0.3, ZR - 0.05, by0, PL, 0.9, jag=0.0,
                         holes=0)
        elif s != 1:
            plaster_coat(k, Ms, -L, L, dz0 + 0.05, ZR - 0.05, -D, PL, rt(k, 0.82, 0.95), holes=1)
        else:
            plaster_coat(k, Ms, -L, L, dz0 + 0.05, ZR - 0.05, -D, PL, rt(k, 0.82, 0.95), holes=0)
        # storey band (painted red with frets) between the floors
        blk(k, -L - 0.03, L + 0.03, -D - 0.07, -D + 0.1, 2.75, 3.15, PLR, rt(k, 0.8, 0.92), M=Ms)
        if s in (0, 3):
            ornament_row(k, Ms, -L + 0.1, L - 0.1, 2.78, 3.12, -D - 0.07, 0.06, 0.3, "fret")
        if s in (0, 2, 3):
            for u in ((-L * 0.55, L * 0.15) if s == 0 else (-L * 0.5, L * 0.5)):
                if s == 0 and abs(u - (door_u - cx)) < 1.2:
                    continue
                blk(k, u - 0.32, u + 0.32, -D - 0.035, -D + 0.02, 3.45, 4.2, GSD, 0.08, M=Ms)
                blk(k, u - 0.45, u + 0.45, -D - 0.1, -D + 0.05, 4.2, 4.36, WOODD, 0.8, M=Ms)
                blk(k, u - 0.4, u + 0.4, -D - 0.12, -D + 0.05, 3.35, 3.45, GS, 0.85, M=Ms)
    for sx in (dx0 - 0.11, dx1 + 0.11):
        blk(k, sx - 0.13, sx + 0.13, by0 - 0.08, by0 + 0.2, dz0, dz0 + door_h, GS, 0.9, chips=1, chipd=0.04)
    blk(k, dx0 - 0.35, dx1 + 0.35, by0 - 0.1, by0 + 0.2, dz0 + door_h, dz0 + door_h + 0.34, GS, 0.92, chips=2)
    ornament_row(k, None, dx0 - 0.2, dx1 + 0.2, dz0 + door_h + 0.04, dz0 + door_h + 0.3, by0 - 0.1, 0.04, 0.22, "fret")
    blk(k, dx0 - 0.1, dx1 + 0.1, by0 - 0.25, by0 + 0.3, dz0 - 0.02, dz0 + 0.06, GS, 0.8)
    curtain(k, T(door_u, by0 + 0.25, dz0 + 0.35), door_w - 0.06, door_h - 0.38,
            ("BH_ClothRed", "BH_ClothOchre", "BH_ClothRed", "BH_ClothCream"), rows=5)
    door_lamp(k, door_u + 1.2, by0 - 0.08, 2.35)
    # vigas under the roof edge
    for i in range(10):
        x = bx0 + 0.4 + i * (bx1 - bx0 - 0.8) / 9
        for sy in (-1, 1):
            k.put(cyl(0.085, 0.48, 6), WOODD, M=T(x, sy * (hy - 0.1), ZR - 0.25) @ R(-90 * sy, 0, 0), tint=rt(k, 0.7, 0.9))
    # roof terrace: paving, parapets (open to the stair landing at the back-right), cane awning on poles
    pave(k, bx0 + 0.3, bx1 - 0.3, by0 + 0.3, by1 - 0.3, ZR, 4, 4, th=0.12, mat=PAVE, bed=False)
    PT, PH = 0.3, 0.8
    rails = [(bx0, bx1, by0, by0 + PT), (bx0, bx0 + PT, by0, by1), (bx0, 2.8, by1 - PT, by1), (bx1 - PT, bx1, by0, 1.4)]
    for (x0, x1, y0, y1) in rails:
        blk(k, x0, x1, y0, y1, ZR, ZR + PH, PL, rt(k, 0.82, 0.92))
        blk(k, x0 - 0.04, x1 + 0.04, y0 - 0.04, y1 + 0.04, ZR + PH, ZR + PH + 0.1, GS, 0.95, chips=1)
        cbox(k, x0, x1, y0, y1, ZR, ZR + PH + 0.1)
    for (x, y) in ((-4.3, -3.4), (-0.5, -3.4), (-4.3, 0.8), (-0.5, 0.8)):
        k.put(cyl(0.07, 2.5, 6), WOODD, M=T(x, y, ZR), tint=0.85)
        cbox(k, x - 0.08, x + 0.08, y - 0.08, y + 0.08, ZR, ZR + 2.5)
    for (y0, y1) in ((-3.5, 0.9),):
        k.put(box(4.3, 4.6, 0.07), "BH_Thatch", M=TRS(-2.4, -1.3, ZR + 2.55, -5, 0, 0), tint=0.92)
        for i in range(7):
            k.put(cyl(0.035, 4.4, 5), WOODD, M=T(-4.55, -3.4 + i * 0.7, ZR + 2.4 + i * 0.06) @ R(0, 90, 0), tint=0.8)
    pot(k, T(2.6, -3.3, ZR), h=0.55, rad=0.24, plant=True)
    pot(k, T(-4.2, 3.2, ZR), h=0.45, rad=0.2, plant=True)
    blk(k, -4.3, -2.8, -0.3, 0.2, ZR, ZR + 0.42, GS, 0.8, chips=1)
    sock(k, "roof", (-1.0, -0.4, ZR))
    # outside stair along +x (bottom at the front), landing at the back-right corner level with the roof
    sx0_, sx1_ = bx1, bx1 + 1.8
    nst, run = 17, 6.4 / 17
    rise = ZR / nst
    Ms_ = T((sx0_ + sx1_ - 0.3) / 2, by0, 0)
    stair_flight(k, Ms_, 1.5, nst, rise, run, split=(0.7, 1.6))
    slope = rise / run
    prof = (lambda u: 0.8 + max(0.0, u) * slope)
    Mb = T(sx1_ - 0.15, by0, 0) @ R(0, 0, 90)
    sloped_wall(k, Mb, -0.15, nst * run, prof, 0.3, course=(0.45, 0.65), blen=(0.8, 1.3))
    coping(k, Mb, -0.15, nst * run, prof, 0.38, th=0.12, n=3)
    ly0 = by0 + nst * run
    Ml = T(sx1_ - 0.15, (ly0 + by1) / 2, 0) @ R(0, 0, 90)
    sloped_wall(k, Ml, -(by1 - ly0) / 2, (by1 - ly0) / 2, (lambda u: ZR), 0.3, course=(0.5, 0.7), blen=(0.6, 1.0))
    Me = T((sx0_ + sx1_) / 2, by1 - 0.15, 0)
    sloped_wall(k, Me, -0.9, 0.9, (lambda u: ZR), 0.3, course=(0.5, 0.7), blen=(0.6, 1.0))
    blk(k, sx0_, sx1_ - 0.3, ly0, by1 - 0.3, 0, ZR - 0.12, GSD, 0.3)
    pave(k, sx0_, sx1_, ly0, by1, ZR, 1, 1, th=0.12, bed=False)
    for (x0, x1, y0, y1) in ((sx1_ - 0.3, sx1_, ly0, by1), (2.8, sx1_, by1 - 0.3, by1)):
        blk(k, x0, x1, y0, y1, ZR, ZR + PH, PL, 0.88)
        blk(k, x0 - 0.04, x1 + 0.04, y0 - 0.04, y1 + 0.04, ZR + PH, ZR + PH + 0.1, GS, 0.95)
        cbox(k, x0, x1, y0, y1, ZR, ZR + PH + 0.1)
    # collision
    cbox(k, bx0, bx1, by0, by1, 0, ZR)
    k.col_mesh(ramp_wedge(nst, rise, run, sx0_ - (sx0_ + sx1_ - 0.3) / 2, (sx1_ - 0.3) - (sx0_ + sx1_ - 0.3) / 2,
                          extra=0.02), Ms_)
    k.col_mesh(xz_prism([(-0.3, 0), (nst * run, 0), (nst * run, prof(nst * run) + 0.1), (-0.3, 0.9)], -0.15, 0.15), Mb)
    cbox(k, sx0_, sx1_, ly0, by1, 0, ZR)
    sock(k, "door", (door_u, by0 - 0.8, 0.0))
    return dict(recenter=False, damp=0.25, damp_h=0.7)


# ===============================================================================================================
# the council hall
@asset("zr_hall_council", CAT)
def zr_hall_council(k):
    r = k.r
    X, Y0, Y1, ZS = 9.0, -4.4, 6.0, 1.0
    cy = (Y0 + Y1) / 2
    Mc = T(0, cy, 0)
    hx, hy = X, (Y1 - Y0) / 2
    # stylobate: two courses + cornice lip, paved top
    k.put(frustum(hx - 0.05, hy - 0.05, hx - 0.05, hy - 0.05, 0, ZS - 0.05), GSD, M=Mc, tint=0.3)
    for s in range(4):
        L, D = (hx, hy) if s % 2 == 0 else (hy, hx)
        Ms = Mc @ R(0, 0, 90 * s)
        ex = [(-6.05, 6.05)] if s == 0 else []
        mitred_run(k, Ms, L, D, 0.0, 0.42, 0.0, 0.0, 0.45, (1.0, 1.8), GS, (0.62, 0.82), excl=ex, alt=GSD, alt_p=0.3)
        mitred_run(k, Ms, L, D, 0.45, 0.82, 0.03, 0.03, 0.45, (1.0, 1.8), GS, (0.72, 0.9), excl=ex)
        mitred_run(k, Ms, L, D, 0.84, ZS, -0.08, -0.08, 0.6, (1.4, 2.4), GS, (0.85, 1.0), excl=ex)
    pave(k, -X + 0.55, X - 0.55, Y0 + 0.55, Y1 - 0.55, ZS, 6, 4, th=0.12, bed=False)
    # front steps with serpent-headed cheeks
    nst, rise, run = 4, 0.25, 0.4
    Mf = T(0, Y0 - nst * run, 0)
    stair_flight(k, Mf, 12.0, nst, rise, run, split=(1.4, 2.6))
    k.col_mesh(ramp_wedge(nst, rise, run, -6.0, 6.0, extra=0.05), Mf)
    for sx in (-1, 1):
        xc = sx * 6.3
        Mb = T(xc, Y0 - nst * run, 0) @ R(0, 0, 90)
        prof = (lambda u: 0.55 + max(0.0, u) * rise / run)
        sloped_wall(k, Mb, -0.1, nst * run, prof, 0.6, course=(0.35, 0.5), blen=(0.6, 1.0))
        coping(k, Mb, -0.1, nst * run, prof, 0.68, th=0.12)
        serpent_head(k, T(xc, Y0 - nst * run - 0.55, 0), s=0.62, fan=(-60, 60), n_plume=5, plume_len=0.6)
        k.col_mesh(xz_prism([(-0.3, 0), (nst * run, 0), (nst * run, ZS + 0.5), (-0.3, 0.7)], -0.3, 0.3), Mb)
    # hall body behind the porch
    WY0 = -1.6
    ZP1, ZF1, ZC1, ZTOP = 5.9, 7.0, 7.25, 8.0
    blk(k, -X + 0.3, X - 0.3, WY0 + 0.6, Y1 - 0.3, ZS, ZP1, GSD, 0.42)
    door_w, door_h = 2.6, 3.6
    blk(k, -X + 0.3, -door_w / 2, WY0, WY0 + 0.62, ZS, ZP1, GSD, 0.42)
    blk(k, door_w / 2, X - 0.3, WY0, WY0 + 0.62, ZS, ZP1, GSD, 0.42)
    blk(k, -door_w / 2, door_w / 2, WY0, WY0 + 0.62, ZS + door_h, ZP1, GSD, 0.42)
    blk(k, -door_w / 2, door_w / 2, WY0 + 0.56, WY0 + 0.6, ZS, ZS + door_h, GSD, 0.06)
    from masonry import masonry
    # front wall: stone base courses then ochre plaster
    masonry(k, -X + 0.3, -door_w / 2 - 0.25, ZS, ZS + 1.1, 0.12, mat=GS, core=False, bev=0.0, course=(0.5, 0.6),
            blen=(0.6, 1.1), M=T(0, WY0 - 0.05, 0), chip_rng=(0, 1), tint=(0.7, 0.88))
    masonry(k, door_w / 2 + 0.25, X - 0.3, ZS, ZS + 1.1, 0.12, mat=GS, core=False, bev=0.0, course=(0.5, 0.6),
            blen=(0.6, 1.1), M=T(0, WY0 - 0.05, 0), chip_rng=(0, 1), tint=(0.7, 0.88))
    plaster_coat(k, None, -X + 0.3, -door_w / 2 - 0.25, ZS + 1.1, ZP1, WY0 - 0.07, PL, 0.9, jag=0.2, holes=1)
    plaster_coat(k, None, door_w / 2 + 0.25, X - 0.3, ZS + 1.1, ZP1, WY0 - 0.07, PL, 0.9, jag=0.2, holes=1)
    for s in (1, 2, 3):
        L, D = ((X - 0.3), (Y1 - 0.3 - WY0) / 2) if s % 2 == 0 else ((Y1 - 0.3 - WY0) / 2, X - 0.3)
        Ms = T(0, (WY0 + Y1 - 0.3) / 2, 0) @ R(0, 0, 90 * s)
        plaster_coat(k, Ms, -L, L, ZS + 0.05, ZP1, -D, PL, rt(k, 0.82, 0.92), holes=1)
    # doorway frame with glowing glyph lintel and a drawn-back curtain
    for sx in (-1, 1):
        blk(k, sx * (door_w / 2 + 0.02), sx * (door_w / 2 + 0.38), WY0 - 0.14, WY0 + 0.2, ZS, ZS + door_h, GS, 0.92,
            chips=1)
        curtain(k, T(sx * (door_w / 2 - 0.3), WY0 + 0.4, ZS + 0.2), 0.55, door_h - 0.3,
                ("BH_ClothRed", "BH_ClothOchre", "BH_ClothRed"), rows=3, cols=3, wave=0.08)
    blk(k, -door_w / 2 - 0.6, door_w / 2 + 0.6, WY0 - 0.16, WY0 + 0.2, ZS + door_h, ZS + door_h + 0.6, GS, 0.95, chips=2)
    for i, kind in enumerate((1, 0, 2, 0, 1)):
        glyph(k, T(-1.4 + i * 0.7, WY0 - 0.16, ZS + door_h + 0.3), kind, 0.42)
    # porch pillars with painted glyph bands
    for i in range(6):
        x = -7.5 + i * 3.0
        py = -3.6
        blk(k, x - 0.6, x + 0.6, py - 0.6, py + 0.6, ZS, ZS + 0.3, GS, 0.85, chips=2)
        z = ZS + 0.3
        zs_ = [z]
        hs = course_heights(r, ZP1 - 0.35 - z, 0.6, 0.85)
        for h in hs:
            zs_.append(zs_[-1] + h)
        for j, (za, zb) in enumerate(zip(zs_[:-1], zs_[1:])):
            band = j in (1, len(hs) - 2)
            blk(k, x - 0.44, x + 0.44, py - 0.44, py + 0.44, za + 0.012, zb - 0.012, PLR if band else GS,
                rt(k, 0.8, 0.95), chips=0 if band else 1, chipd=0.04)
            if band:
                for s in range(4):
                    Ms = T(x, py, 0) @ R(0, 0, 90 * s)
                    ornament_row(k, Ms, -0.42, 0.42, za + 0.05, zb - 0.05, -0.44, 0.05, (zb - za) * 0.6, "medallion")
        blk(k, x - 0.62, x + 0.62, py - 0.62, py + 0.62, ZP1 - 0.35, ZP1, GS, 0.92, chips=2)
        cbox(k, x - 0.6, x + 0.6, py - 0.6, py + 0.6, ZS, ZP1)
    # entablature: painted frieze, cornice, stepped roof ornaments
    blk(k, -X - 0.05, X + 0.05, Y0 + 0.2, Y1 - 0.25, ZP1, ZF1, GSD, 0.4)
    for s in range(4):
        L, D = ((X + 0.05), (Y1 - 0.25 - Y0 - 0.2) / 2) if s % 2 == 0 else ((Y1 - 0.25 - Y0 - 0.2) / 2, X + 0.05)
        Ms = T(0, (Y0 + 0.2 + Y1 - 0.25) / 2, 0) @ R(0, 0, 90 * s)
        blk(k, -L - 0.02, L + 0.02, -D - 0.05, -D + 0.05, ZP1 + 0.08, ZF1 - 0.08, PLR, rt(k, 0.82, 0.95), M=Ms)
        blk(k, -L - 0.06, L + 0.06, -D - 0.1, -D + 0.1, ZP1, ZP1 + 0.1, GS, 0.9, M=Ms)
        if s != 2:
            ornament_row(k, Ms, -L + 0.2, L - 0.2, ZP1 + 0.14, ZF1 - 0.1, -D - 0.05, 0.08, 0.78, "mix")
        mitred_run(k, Ms, L, D, ZF1, ZC1, -0.22, -0.22, 0.8, (1.4, 2.4), GS, (0.85, 1.0))
        if s == 0:
            wire_inlay(k, (-L + 0.3, -D - 0.1, ZP1 + 0.05), (L - 0.3, -D - 0.1, ZP1 + 0.05), (0, -1, 0), 0.08, M=Ms)
    blk(k, -X, X, Y0 + 0.4, Y1 - 0.45, ZC1 - 0.1, ZC1 + 0.05, PL, 0.8)
    for i in range(12):
        x = -X + 0.75 + i * (2 * X - 1.5) / 11
        for (yy, ss) in ((Y0 + 0.05, 1.0), (Y1 - 0.4, 0.85)):
            blk(k, x - 0.36, x + 0.36, yy, yy + 0.3, ZC1, ZC1 + 0.32, GS, rt(k, 0.8, 0.95) * ss, chips=1, chipd=0.04)
            blk(k, x - 0.2, x + 0.2, yy + 0.04, yy + 0.26, ZC1 + 0.32, ZTOP, GS, rt(k, 0.8, 0.95) * ss)
    # flanking wire braziers
    for sx, nm in ((-1, "light_a"), (1, "light_b")):
        bx = sx * 7.4
        by = Y0 - 1.0
        blk(k, bx - 0.5, bx + 0.5, by - 0.5, by + 0.5, 0, 0.25, GS, 0.85, chips=2)
        blk(k, bx - 0.36, bx + 0.36, by - 0.36, by + 0.36, 0.25, 1.05, GS, 0.9, chips=1)
        ornament_row(k, T(bx, by, 0), -0.34, 0.34, 0.45, 0.85, -0.36, 0.04, 0.3, "medallion")
        k.put(lathe([(0.0, 0.0), (0.3, 0.0), (0.5, 0.18), (0.56, 0.3), (0.5, 0.3), (0.0, 0.2)], 12), COP,
              M=T(bx, by, 1.05), tint=0.85)
        cage_lamp(k, T(bx, by, 1.6), rc=0.2, h=0.62, ribs=7)
        sock(k, nm, (bx, by, 1.6))
        cbox(k, bx - 0.5, bx + 0.5, by - 0.5, by + 0.5, 0, 1.6)
    # collision
    cbox(k, -X, X, Y0, Y1, 0, ZS)
    cbox(k, -X + 0.3, X - 0.3, WY0, Y1 - 0.3, ZS, ZC1)
    cbox(k, -X, X, Y0, Y1, ZP1, ZTOP)
    sock(k, "door", (0, WY0 - 0.6, ZS))
    sock(k, "npc", (-2.4, WY0 - 0.9, ZS))
    return dict(recenter=False, damp=0.22, damp_h=1.0)


# ===============================================================================================================
# market stalls
def stall(k, cloth, goods):
    r = k.r
    # stone counter
    blk(k, -1.35, 1.35, -1.2, -0.6, 0, 0.88, GS, 0.82, chips=2)
    blk(k, -1.45, 1.45, -1.3, -0.5, 0.88, 1.0, GS, 0.95, chips=2, chipd=0.04)
    blk(k, -1.3, 1.3, -1.225, -1.2, 0.18, 0.72, PLR if cloth == "BH_ClothOchre" else PL, 0.85)
    ornament_row(k, None, -1.25, 1.25, 0.24, 0.66, -1.225, 0.04, 0.34, "fret")
    # back shelf
    blk(k, -1.3, 1.3, 0.75, 1.15, 0, 0.55, GS, 0.75, chips=1)
    # poles and woven awning (higher at the back)
    for (x, y, h) in ((-1.4, -1.2, 2.3), (1.4, -1.2, 2.3), (-1.4, 1.15, 2.65), (1.4, 1.15, 2.65)):
        k.put(cyl(0.06, h, 6), WOODD, M=T(x, y, 0), tint=0.85)
    ang = math.degrees(math.atan2(0.35, 2.35))
    k.put(box(3.25, 2.75, 0.05), cloth, M=TRS(0, -0.02, 2.5, -ang, 0, 0), tint=0.95)
    for i in range(5):
        k.put(box(0.66, 2.77, 0.055), cloth, M=TRS(-1.3 + i * 0.65, -0.02, 2.505, -ang, 0, 0),
              tint=0.6 if i % 2 else 1.0)
    for i in range(8):
        x = -1.4 + i * 0.4
        k.put(prism([(-0.19, 0.0), (0.19, 0.0), (0.0, -0.32)], 0.03), cloth, M=T(x + 0.2, -1.38, 2.32),
              tint=0.75 if i % 2 else 1.0)
    for x in (-1.4, 1.4):
        k.put(cyl(0.03, 2.6, 5), WOODD, M=T(x, -1.35, 2.31) @ R(-90, 0, 0) @ R(0, 0, 0), tint=0.8)
    goods(k)
    sock(k, "npc", (0, 0.2, 0))
    sock(k, "customer", (0, -1.95, 0))
    cbox(k, -1.45, 1.45, -1.3, -0.5, 0, 1.0)
    cbox(k, -1.3, 1.3, 0.75, 1.15, 0, 0.55)
    for (x, y) in ((-1.4, -1.2), (1.4, -1.2), (-1.4, 1.15), (1.4, 1.15)):
        cbox(k, x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0, 2.3)
    return dict(recenter=False, damp=0.2, damp_h=0.5)


def basket(k, M, rad=0.24, h=0.18, fruit="BH_Coral", n=7):
    r = k.r
    k.put(lathe([(0.0, 0.0), (rad * 0.7, 0.0), (rad, h), (rad * 0.92, h)], 10), "BH_Thatch", M=M, tint=0.85)
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = rad * (0.45 if i else 0.0)
        k.put(ico(0.075, 1), fruit, M=mm(M, T(math.cos(a) * rr, math.sin(a) * rr, h - 0.02 + (0.05 if i == 0 else 0))),
              tint=rt(k, 0.75, 1.0))


@asset("zr_market_stall_a", CAT)
def zr_market_stall_a(k):
    def goods(k):
        r = k.r
        for i, x in enumerate((-1.05, -0.6, -0.15)):
            pot(k, T(x, -0.9, 1.0), h=r.uniform(0.32, 0.45), rad=r.uniform(0.13, 0.18), tint=rt(k, 0.7, 0.95))
        basket(k, T(0.45, -0.9, 1.0), fruit="BH_Coral")
        basket(k, T(1.0, -0.88, 1.0), rad=0.2, fruit="BH_Candle")
        for i in range(4):
            pot(k, T(-1.0 + i * 0.6, 0.95, 0.55), h=r.uniform(0.4, 0.6), rad=r.uniform(0.17, 0.24),
                tint=rt(k, 0.7, 0.95))
        basket(k, T(-0.5, 1.6, 0.0), rad=0.3, h=0.3, fruit="BH_Leaves", n=8)
        pot(k, T(1.2, 1.55, 0.0), h=0.7, rad=0.3, tint=0.8)
    return stall(k, "BH_ClothOchre", goods)


@asset("zr_market_stall_b", CAT)
def zr_market_stall_b(k):
    def goods(k):
        r = k.r
        for i, (m, x) in enumerate((("BH_ClothRed", -1.0), ("BH_ClothBlue", -0.72), ("BH_ClothTeal", -0.44),
                                    ("BH_ClothOchre", -0.16))):
            k.put(cyl(0.12, 0.5, 8), m, M=T(x, -0.9, 1.12) @ R(90, 0, 0), tint=rt(k, 0.85, 1.0))
        for i in range(3):
            k.put(torus(0.15, 0.035, 12, 4), COP, M=TRS(0.35 + i * 0.32, -0.9, 1.05 + 0.02, 0, 0, i * 20))
            k.put(torus(0.13, 0.035, 12, 4), COP, M=TRS(0.35 + i * 0.32, -0.9, 1.11, 0, 0, i * 20 + 10))
        coil(k, T(0.4, 0.95, 0.55), 0.14, 0.32, 5, wr=0.03)
        coil(k, T(0.9, 0.95, 0.55), 0.11, 0.26, 4, wr=0.025)
        for i in range(3):
            k.put(cyl(0.14, 0.9, 8), ("BH_ClothCream", "BH_ClothRed", "BH_ClothTeal")[i],
                  M=T(-1.05 + i * 0.32, 0.95, 0.69) @ R(0, 90, 0) @ T(0, 0, -0.45), tint=rt(k, 0.85, 1.0))
        for i in range(4):
            k.put(torus(0.22, 0.04, 14, 4), COP, M=T(1.25, 1.6, 0.04 + i * 0.075))
        k.put(cyl(0.3, 0.45, 10), WOODD, M=T(-1.0, 1.6, 0.0), tint=0.8)
    return stall(k, "BH_ClothTeal", goods)


# ===============================================================================================================
# Heartwire street furniture
@asset("zr_wire_pylon", CAT)
def zr_wire_pylon(k):
    blk(k, -0.95, 0.95, -0.95, 0.95, 0, 0.4, GS, 0.8, chips=3)
    blk(k, -0.72, 0.72, -0.72, 0.72, 0.4, 0.8, GS, 0.85, chips=2)
    blk(k, -0.48, 0.48, -0.48, 0.48, 0.8, 2.6, GS, 0.88, chips=2)
    blk(k, -0.52, 0.52, -0.52, 0.52, 2.0, 2.6, PLR, 0.85)
    for s in range(4):
        Ms = R(0, 0, 90 * s)
        glyph(k, Ms @ T(0, -0.52, 2.3), s % 4, 0.42)
        wire_inlay(k, (0, -0.48, 0.85), (0, -0.48, 1.95), (0, -1, 0), 0.1, M=Ms)
    blk(k, -0.58, 0.58, -0.58, 0.58, 2.6, 2.78, GS, 0.95, chips=2)
    k.put(cyl(0.17, 4.0, 10, r2=0.13), BRZ, M=T(0, 0, 2.78), tint=0.8)
    for z in (3.15, 4.25, 5.35):
        coil(k, T(0, 0, z), 0.34, 0.8, 5, wr=0.05)
        k.put(cyl(0.42, 0.08, 10), JADE, M=T(0, 0, z - 0.12), tint=0.9)
    for s in range(4):
        a = math.radians(90 * s + 45)
        k.put(tube([(math.cos(a) * 0.55, math.sin(a) * 0.55, 2.78), (math.cos(a) * 0.18, math.sin(a) * 0.18, 3.1)],
                   0.035, 5), VERD)
    k.put(torus(0.28, 0.05, 14, 4), COP, M=T(0, 0, 6.45))
    k.put(ico(0.2, 2), WIRE, M=T(0, 0, 6.75))
    for i in range(4):
        a = math.radians(i * 90)
        k.put(tube([(math.cos(a) * 0.28, math.sin(a) * 0.28, 6.45), (math.cos(a) * 0.3, math.sin(a) * 0.3, 6.75),
                    (0, 0, 7.05)], 0.02, 4), COP)
    sock(k, "light", (0, 0, 5.75))
    cbox(k, -0.95, 0.95, -0.95, 0.95, 0, 0.8)
    cbox(k, -0.58, 0.58, -0.58, 0.58, 0.8, 2.78)
    cbox(k, -0.45, 0.45, -0.45, 0.45, 2.78, 6.6)
    return dict(recenter=False, damp=0.25, damp_h=0.6)


@asset("zr_wire_conduit_4m", CAT, col=False)
def zr_wire_conduit_4m(k):
    r = k.r
    blk(k, -2.0, 2.0, -0.3, 0.3, -0.2, -0.02, GSD, 0.3)
    for sy in (-1, 1):
        ws, _ = split_lengths(r, 4.0, 0.9, 1.5)
        x = -2.0
        for w in ws:
            blk(k, x + 0.01, x + w - 0.01, sy * 0.1, sy * 0.3, -0.12, 0.05, GS, rt(k, 0.75, 0.92), chips=1, chipd=0.03)
            x += w
        for i in range(8):
            x = -1.75 + i * 0.5
            blk(k, x - 0.1, x + 0.1, sy * 0.2, sy * 0.3, 0.05, 0.065, GS, 0.8)
    k.put(box(4.0, 0.08, 0.05), WIRE, M=T(0, 0, 0.0))
    for x in (-1.5, -0.5, 0.5, 1.5):
        k.put(box(0.06, 0.26, 0.03), BRZ, M=T(x, 0, 0.035), tint=0.8)
    return dict(recenter=False)


@asset("zr_wire_lamp", CAT)
def zr_wire_lamp(k):
    blk(k, -0.38, 0.38, -0.38, 0.38, 0, 0.28, GS, 0.82, chips=2)
    blk(k, -0.2, 0.2, -0.2, 0.2, 0.28, 2.25, GS, 0.88, chips=2, chipd=0.04)
    blk(k, -0.22, 0.22, -0.22, 0.22, 1.5, 1.8, TURQ, 0.85)
    for s in range(4):
        glyph(k, R(0, 0, 90 * s) @ T(0, -0.22, 1.65), (0, 1, 2, 3)[s], 0.24, dep=0.02)
    blk(k, -0.3, 0.3, -0.3, 0.3, 2.25, 2.4, GS, 0.95, chips=1)
    cage_lamp(k, T(0, 0, 2.7), rc=0.15, h=0.56, ribs=6)
    k.put(cyl(0.05, 0.25, 6, r2=0.0), BRZ, M=T(0, 0, 3.0))
    sock(k, "light", (0, 0, 2.7))
    cbox(k, -0.3, 0.3, -0.3, 0.3, 0, 2.4)
    return dict(recenter=False, damp=0.2, damp_h=0.5)


@asset("zr_glyph_stele", CAT)
def zr_glyph_stele(k):
    r = k.r
    blk(k, -1.0, 1.0, -0.6, 0.6, 0, 0.25, GS, 0.8, chips=3)
    blk(k, -0.82, 0.82, -0.45, 0.45, 0.25, 0.45, GS, 0.85, chips=2)
    W, Dp, H = 1.3, 0.55, 3.05
    k.put(box(W, Dp, H - 0.45), GS, M=T(0, 0, 0.45 + (H - 0.45) / 2), tint=0.88)
    for i, (w, h) in enumerate(((1.1, 0.16), (0.8, 0.16), (0.5, 0.18))):
        blk(k, -w / 2, w / 2, -Dp / 2 + 0.04, Dp / 2 - 0.04, H + i * 0.16, H + i * 0.16 + h, GS, 0.9, chips=1,
            chipd=0.03)
    # front: border and three cartouches with glowing glyphs
    yf = -Dp / 2
    for (x0, x1, z0, z1) in ((-0.65, -0.55, 0.5, H - 0.05), (0.55, 0.65, 0.5, H - 0.05), (-0.65, 0.65, H - 0.15, H),
                             (-0.65, 0.65, 0.5, 0.6)):
        blk(k, x0, x1, yf - 0.05, yf + 0.01, z0, z1, GS, 0.95)
    for j, kind in enumerate((0, 2, 1)):
        zc = 0.95 + j * 0.72
        blk(k, -0.42, 0.42, yf - 0.012, yf + 0.01, zc - 0.3, zc + 0.3, GSD, 0.35)
        glyph(k, T(0, yf - 0.012, zc), kind, 0.52)
    for s in (1, 3):
        Ms = R(0, 0, 90 * s)
        ornament_row(k, Ms, -0.24, 0.24, 0.6, H - 0.1, -W / 2, 0.04, 0.22, "fret")
    k.put(box(1.1, 0.04, 0.5), "BH_Moss", M=TRS(0.1, Dp / 2 + 0.01, 0.75, 0, 0, 0), tint=0.7)
    moss_patch(k, 0.6, 0.5, 0.25, 0.4)
    cbox(k, -1.0, 1.0, -0.6, 0.6, 0, 0.45)
    cbox(k, -W / 2, W / 2, -Dp / 2, Dp / 2, 0.45, H + 0.5)
    return dict(recenter=False, damp=0.25, damp_h=0.6)


@asset("zr_serpent_statue", CAT)
def zr_serpent_statue(k):
    blk(k, -0.85, 0.85, -1.05, 1.05, 0, 0.3, GS, 0.8, chips=3)
    blk(k, -0.7, 0.7, -0.9, 0.9, 0.3, 0.6, GS, 0.85, chips=2)
    ornament_row(k, None, -0.66, 0.66, 0.33, 0.57, -0.9, 0.04, 0.22, "fret")
    # coiled body under the head
    pts = [(0.45 * math.cos(a), 0.45 * math.sin(a) + 0.2, 0.62 + 0.12 * a / (2 * math.pi)) for a in
           [i * 0.5 for i in range(14)]]
    k.put(tube(pts, 0.2, 8), GS, tint=0.85, smooth=50)
    serpent_head(k, T(0, -0.1, 0.72), s=1.5, plume=(FEA, FEA, FEAR), fan=(-110, 110), n_plume=11, plume_len=0.8,
                 tint=0.92)
    cbox(k, -0.85, 0.85, -1.3, 1.05, 0, 2.3)
    return dict(recenter=False, damp=0.2, damp_h=0.5)


@asset("zr_brazier_stone", CAT)
def zr_brazier_stone(k):
    for i in range(3):
        a = math.radians(90 + i * 120)
        p0 = Vector((math.cos(a) * 0.42, math.sin(a) * 0.42, 0.0))
        p1 = Vector((math.cos(a) * 0.24, math.sin(a) * 0.24, 0.95))
        d = p1 - p0
        k.put(box(d.length + 0.04, 0.17, 0.2), GS, M=frame((p0 + p1) / 2, d, (math.cos(a), math.sin(a), 0.2)),
              tint=rt(k, 0.82, 0.92))
        k.put(box(0.26, 0.26, 0.1), GS, M=TRS(p0.x, p0.y, 0.05, 0, 0, i * 120), tint=0.8)
    k.put(cyl(0.3, 0.14, 8), GS, M=T(0, 0, 0.42), tint=0.85)
    k.put(lathe([(0.0, 0.88), (0.22, 0.88), (0.42, 0.98), (0.56, 1.18), (0.58, 1.32), (0.5, 1.32), (0.46, 1.2),
                 (0.0, 1.16)], 12), GS, tint=0.9)
    for i in range(10):
        a = 2 * math.pi * i / 10
        k.put(box(0.12, 0.05, 0.14), TURQ if i % 2 else GS, M=frame((math.cos(a) * 0.53, math.sin(a) * 0.53, 1.2),
                                                                     (-math.sin(a), math.cos(a), 0), (0, 0, 1)),
              tint=0.9)
    k.put(cyl(0.46, 0.1, 10, r2=0.3), "BH_Coals", M=T(0, 0, 1.18))
    sock(k, "flame", (0, 0, 1.45))
    cbox(k, -0.55, 0.55, -0.55, 0.55, 0, 1.32)
    return dict(recenter=False, damp=0.15, damp_h=0.4)


def agave(k, M, s=1.0, n=14):
    r = k.r
    for i in range(n):
        a = i * 137.5 + r.uniform(-8, 8)
        tilt = r.uniform(20, 65)
        L = r.uniform(0.6, 0.95) * s
        outline = [(-0.07 * s, 0.0), (0.07 * s, 0.0), (0.05 * s, L * 0.7), (0.0, L)]
        t = prism(outline, 0.035 * s)
        k.put(t, LEAF, M=mm(M, R(0, 0, a) @ R(tilt, 0, 0)), tint=(0.55, 0.75, 0.68))


def palm(k, M, h=1.9, fronds=7):
    r = k.r
    pts = [(0.06 * math.sin(i * 0.9), 0.05 * i / 6, h * i / 6) for i in range(7)]
    k.put(tube(pts, [0.07 - 0.02 * i / 6 for i in range(7)], 6), "BH_Bark", M=M, tint=0.8, smooth=50)
    top = Vector(pts[-1])
    for i in range(fronds):
        a = 2 * math.pi * i / fronds + r.uniform(-0.2, 0.2)
        d = Vector((math.cos(a), math.sin(a), 0))
        fp = [top + d * (0.75 * t_) + Vector((0, 0, 0.3 * t_ - 0.75 * t_ * t_)) for t_ in (0.0, 0.3, 0.6, 1.0)]
        side = Vector((-d.y, d.x, 0))
        t = tb()
        rows = []
        for j, p in enumerate(fp):
            wdt = 0.16 * math.sin(math.pi * min(0.95, (j + 0.4) / 4))
            rows.append((t.verts.new(p - side * wdt + Vector((0, 0, -0.03))), t.verts.new(p),
                         t.verts.new(p + side * wdt + Vector((0, 0, -0.03)))))
        for j in range(len(rows) - 1):
            for (a0, a1) in ((0, 1), (1, 2)):
                t.faces.new((rows[j][a0], rows[j][a1], rows[j + 1][a1], rows[j + 1][a0]))
        k.put(two_sided(t, 0.008), LEAF, M=M, tint=rt(k, 0.75, 1.0))


@asset("zr_planter", CAT)
def zr_planter(k):
    for s in range(4):
        Ms = R(0, 0, 90 * s)
        mitred_run(k, Ms, 1.0, 1.0, 0.0, 0.62, 0.0, 0.0, 0.25, (0.8, 1.3), GS, (0.75, 0.9))
        mitred_run(k, Ms, 1.0, 1.0, 0.62, 0.74, -0.05, -0.05, 0.32, (0.9, 1.4), GS, (0.88, 1.0))
        blk(k, -0.9, 0.9, -1.0 - 0.01, -0.96, 0.16, 0.5, PLR, 0.85, M=Ms)
        ornament_row(k, Ms, -0.85, 0.85, 0.18, 0.48, -1.0, 0.035, 0.26, "fret")
    blk(k, -0.76, 0.76, -0.76, 0.76, 0.1, 0.64, "BH_Dirt", 0.7)
    agave(k, T(-0.3, -0.25, 0.64), s=0.9)
    palm(k, T(0.4, 0.35, 0.64) @ R(0, 0, 30), h=1.9)
    palm(k, T(-0.45, 0.45, 0.64) @ R(0, 0, 200), h=1.4, fronds=6)
    moss_patch(k, 0.7, -1.05, 0.0, 0.35)
    cbox(k, -1.0, 1.0, -1.0, 1.0, 0, 0.74)
    return dict(recenter=False, damp=0.2, damp_h=0.4)


@asset("zr_lift_platform", CAT)
def zr_lift_platform(k):
    r = k.r
    # platform: four slabs on a dark bed, Heartwire ring inlaid round the top edge
    blk(k, -2.0, 2.0, -2.0, 2.0, 0.0, 0.18, GSD, 0.3)
    for (x0, x1) in ((-2.0, 0.0), (0.0, 2.0)):
        for (y0, y1) in ((-2.0, 0.0), (0.0, 2.0)):
            blk(k, x0 + 0.02, x1 - 0.02, y0 + 0.02, y1 - 0.02, 0.06, 0.3, GS, rt(k, 0.82, 0.95), chips=1)
    for s in range(4):
        Ms = R(0, 0, 90 * s)
        wire_inlay(k, (-1.75, -1.75, 0.3), (1.75, -1.75, 0.3), (0, 0, 1), 0.1, M=Ms)
        blk(k, -2.02, 2.02, -2.04, -1.98, 0.02, 0.28, BRZ, 0.75, M=Ms)
    for (x, y) in ((-1.2, -1.2), (1.2, 1.2), (-1.2, 1.2), (1.2, -1.2)):
        glyph(k, T(x, y, 0.3) @ R(-90, 0, 0), 1, 0.3, dep=0.015)
    # bronze frame on stone footings
    P = 2.35
    for (x, y) in ((-P, -P), (P, -P), (-P, P), (P, P)):
        blk(k, x - 0.32, x + 0.32, y - 0.32, y + 0.32, 0, 0.45, GS, 0.8, chips=2)
        blk(k, x - 0.15, x + 0.15, y - 0.15, y + 0.15, 0.45, 9.0, BRZ, 0.78)
        blk(k, x - 0.2, x + 0.2, y - 0.2, y + 0.2, 1.0, 1.35, GS, 0.9)
        glyph(k, T(x, y - 0.2, 1.17), 0, 0.28, dep=0.015)
        for z in (3.0, 6.0):
            blk(k, x - 0.19, x + 0.19, y - 0.19, y + 0.19, z, z + 0.12, VERD, 0.8)
        cbox(k, x - 0.32, x + 0.32, y - 0.32, y + 0.32, 0, 9.0)
    for sy in (-1, 1):
        blk(k, -P - 0.18, P + 0.18, sy * P - 0.18, sy * P + 0.18, 8.6, 9.0, BRZ, 0.75)
    for sx in (-1, 1):
        blk(k, sx * P - 0.18, sx * P + 0.18, -P - 0.18, P + 0.18, 8.65, 8.95, BRZ, 0.72)
        blk(k, sx * P - 0.12, sx * P + 0.12, -P, P, 4.4, 4.62, BRZ, 0.72)
    # winding drum on the top beam (the light), pulleys, chains to the platform corners
    k.put(cyl(0.38, 2.4, 12), BRZ, M=T(-1.2, P, 9.35) @ R(0, 90, 0), tint=0.7)
    k.put(tube([(x, P + 0.43 * math.cos(a), 9.35 + 0.43 * math.sin(a)) for x, a in
                [(-1.1 + 2.2 * i / 90, i * 2 * math.pi * 9 / 90) for i in range(91)]], 0.045, 4), WIRE, uvoff=False)
    for x in (-1.25, 1.25):
        k.put(cyl(0.48, 0.08, 12), BRZ, M=T(x, P, 9.35) @ R(0, 90, 0), tint=0.85)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(cyl(0.2, 0.08, 10), BRZ, M=T(sx * 1.7, sy * P, 8.62) @ R(0, 90, 0) @ T(0, 0, -0.04), tint=0.85)
            chain(k, (sx * 1.7, sy * (P - 0.05), 8.45), (sx * 1.7, sy * 1.7, 0.32))
            blk(k, sx * 1.7 - 0.12, sx * 1.7 + 0.12, sy * 1.7 - 0.12, sy * 1.7 + 0.12, 0.3, 0.38, BRZ, 0.8)
    # counterweights hanging outside the side posts
    for sx in (-1, 1):
        x = sx * (P + 0.55)
        k.put(cyl(0.22, 0.1, 10), BRZ, M=T(sx * (P + 0.2), 0.0, 8.8) @ R(0, 90, 0) @ T(0, 0, -0.05 + sx * 0.0), tint=0.85)
        blk(k, sx * P, x + sx * 0.1, -0.1, 0.1, 8.7, 8.9, BRZ, 0.7)
        chain(k, (x, 0, 8.6), (x, 0, 5.6))
        blk(k, x - 0.3, x + 0.3, -0.45, 0.45, 4.3, 5.6, GS, 0.8, chips=3)
        blk(k, x - 0.32, x + 0.32, -0.47, 0.47, 4.8, 5.0, BRZ, 0.75)
    # coils on the back posts
    for sx in (-1, 1):
        coil(k, T(sx * P, P, 2.0), 0.3, 0.9, 6, wr=0.045)
    sock(k, "light", (0.0, P, 9.35))
    cbox(k, -2.0, 2.0, -2.0, 2.0, 0, 0.3)
    return dict(recenter=False, damp=0.15, damp_h=0.5)


@asset("zr_aqueduct_4m", CAT)
def zr_aqueduct_4m(k):
    r = k.r
    Y = 1.0
    # pier halves at both ends (segments tile along X: neighbouring halves form one pier)
    for sx in (-1, 1):
        x0, x1 = sx * 2.0, sx * 1.3
        z = 0.0
        for h in course_heights(r, 2.6, 0.45, 0.6):
            blk(k, x0, x1, -Y, Y, z + 0.012, z + h - 0.012, GS, rt(k, 0.72, 0.9), chips=1)
            z += h
        # corbel courses stepping in
        for i, (za, zb) in enumerate(((2.6, 2.95), (2.95, 3.3), (3.3, 3.65))):
            xi = sx * (1.0 - i * 0.3)
            ws, _ = split_lengths(r, abs(x0 - xi), 0.5, 0.9)
            xx = min(x0, xi)
            for w in ws:
                blk(k, xx + 0.01, xx + w - 0.01, -Y, Y, za + 0.012, zb - 0.012, GS, rt(k, 0.75, 0.92), chips=1)
                xx += w
        k.put(box(0.9, 2 * Y - 0.1, 3.6), GSD, M=T(sx * 1.6, 0, 1.8), tint=0.3)
    blk(k, -2.0, 2.0, -Y, Y, 3.65, 4.0, GS, 0.88, chips=2)
    k.put(box(1.4, 2 * Y - 0.1, 0.3), GSD, M=T(0, 0, 3.6), tint=0.25)
    # glyph frieze both faces
    blk(k, -2.0, 2.0, -Y + 0.03, Y - 0.03, 4.0, 4.4, PLR, 0.85)
    for s in (0, 2):
        ornament_row(k, R(0, 0, 90 * s), -1.98, 1.98, 4.03, 4.37, -Y + 0.03, 0.05, 0.3, "fret")
    blk(k, -2.0, 2.0, -Y - 0.05, Y + 0.05, 4.4, 4.58, GS, 0.95, chips=1)
    # channel walls and water
    for sy in (-1, 1):
        ws, _ = split_lengths(r, 4.0, 0.9, 1.4)
        x = -2.0
        for w in ws:
            blk(k, x + 0.01, x + w - 0.01, sy * 0.62, sy * Y, 4.58, 5.0, GS, rt(k, 0.8, 0.95), chips=1)
            x += w
        wire_inlay(k, (-2.0, sy * 0.81, 5.0), (2.0, sy * 0.81, 5.0), (0, 0, 1), 0.1)
    k.put(box(4.0, 1.24, 0.05), "BH_Water", M=T(0, 0, 4.85))
    for _ in range(3):
        moss_patch(k, r.uniform(-1.8, 1.8), r.uniform(-0.6, 0.6), 4.86, 0.3)
    cbox(k, -2.0, -1.3, -Y, Y, 0, 2.6)
    cbox(k, 1.3, 2.0, -Y, Y, 0, 2.6)
    cbox(k, -2.0, 2.0, -Y, Y, 2.6, 5.0)
    return dict(recenter=False, damp=0.25, damp_h=0.8)


@asset("zr_fountain_wire", CAT)
def zr_fountain_wire(k):
    r = k.r
    # octagonal stepped basin (flat side to the front)
    k.put(cyl(2.55, 0.25, 8), GS, M=R(0, 0, 22.5), tint=0.82)
    k.put(cyl(2.25, 0.5, 8), GS, M=T(0, 0, 0.25) @ R(0, 0, 22.5), tint=0.86)
    k.put(cyl(2.32, 0.12, 8), GS, M=T(0, 0, 0.75) @ R(0, 0, 22.5), tint=0.95)
    for i in range(8):
        a = math.radians(i * 45 + 90)
        Ms = T(math.cos(a) * 2.08, math.sin(a) * 2.08, 0) @ R(0, 0, i * 45)
        blk(k, -0.78, 0.78, -0.02, 0.0, 0.3, 0.7, PLR, 0.85, M=Ms)
        ornament_row(k, Ms, -0.75, 0.75, 0.32, 0.68, -0.02, 0.035, 0.3, "fret")
    k.put(cyl(1.98, 0.06, 8), "BH_Water", M=T(0, 0, 0.62) @ R(0, 0, 22.5))
    # central pedestal with four small spouting serpent heads
    k.put(cyl(0.85, 0.5, 8), GS, M=T(0, 0, 0.4) @ R(0, 0, 22.5), tint=0.85)
    k.put(cyl(0.6, 0.45, 8), GS, M=T(0, 0, 0.9) @ R(0, 0, 22.5), tint=0.88)
    for i in range(4):
        a = i * 90
        Mh = R(0, 0, a) @ T(0, -0.62, 0.95)
        serpent_head(k, Mh, s=0.26, n_plume=0)
        p0 = Mh @ Vector((0, -0.25, 0.1))
        p1 = Mh @ Vector((0, -0.7, -0.05))
        p2 = Mh @ Vector((0, -0.95, -0.33))
        k.put(tube([p0, p1, p2], [0.035, 0.05, 0.07], 5), "BH_Water")
    # wire-wound column, copper bands, caged core
    k.put(cyl(0.24, 2.0, 10), OBS, M=T(0, 0, 1.35), tint=0.9)
    k.put(tube(helix(0.28, 1.45, 3.2, 6, 12), 0.045, 4), WIRE, uvoff=False)
    for z in (1.4, 2.3, 3.25):
        k.put(torus(0.31, 0.045, 14, 4), COP, M=T(0, 0, z))
    k.put(cyl(0.42, 0.12, 10, r2=0.3), BRZ, M=T(0, 0, 3.35), tint=0.85)
    cage_lamp(k, T(0, 0, 3.78), rc=0.2, h=0.6, ribs=7)
    k.put(cyl(0.05, 0.35, 6, r2=0.0), BRZ, M=T(0, 0, 4.1))
    sock(k, "light", (0, 0, 3.78))
    k.col_mesh(cyl(2.55, 0.25, 8), R(0, 0, 22.5))
    k.col_mesh(cyl(2.25, 0.87, 8), R(0, 0, 22.5))
    cbox(k, -0.6, 0.6, -0.6, 0.6, 0.87, 3.4)
    return dict(recenter=False, damp=0.2, damp_h=0.5)


# ===============================================================================================================
# harbour
def pier_body(k, y0, y1, ends=()):
    """Pier between y0..y1 (deck top z=0), 5 m wide, blocks down to z=-4; coursed faces on +-x (and listed ends)."""
    r = k.r
    blk(k, -2.35, 2.35, y0 + 0.02, y1 - 0.02, -4.0, -0.3, GSD, 0.3)
    L = y1 - y0
    for sx in (-1, 1):
        Mb = T(sx * 2.35, (y0 + y1) / 2, 0) @ R(0, 0, 90)
        sloped_wall(k, Mb, -L / 2, L / 2, (lambda u: -0.35), 0.3, z0=-4.0, course=(0.5, 0.7), blen=(0.9, 1.5),
                    tint=(0.6, 0.85), alt=GSD, alt_p=0.35, core=False)
        for _ in range(3):
            k.put(box(r.uniform(0.6, 1.4), 0.05, r.uniform(0.25, 0.45)), "BH_Moss",
                  M=T(sx * 2.52, r.uniform(y0 + 0.5, y1 - 0.5), r.uniform(-1.1, -0.8)), tint=0.6)
    for e in ends:
        ye = y0 if e < 0 else y1
        Me = T(0, ye + (0.15 if e < 0 else -0.15), 0)
        sloped_wall(k, Me, -2.5, 2.5, (lambda u: -0.35), 0.3, z0=-4.0, course=(0.5, 0.7), blen=(0.9, 1.5),
                    tint=(0.6, 0.85), alt=GSD, alt_p=0.35, core=False)


def pier_deck(k, y0, y1, x0=-2.3, x1=2.3, wire=True):
    r = k.r
    ny = max(1, int(round((y1 - y0) / 2.0)))
    pave(k, x0, x1, y0, y1, 0.0, 3, ny, th=0.35, bed=False, tint=(0.7, 0.95))
    if wire:
        wire_inlay(k, (0, y0, 0.0), (0, y1, 0.0), (0, 0, 1), 0.12)


def kerbs(k, y0, y1, sides=(-1, 1)):
    r = k.r
    for sx in sides:
        ws, _ = split_lengths(r, y1 - y0, 0.8, 1.3)
        y = y0
        for w in ws:
            blk(k, sx * 2.3, sx * 2.52, y + 0.01, y + w - 0.01, -0.35, 0.2, GS, rt(k, 0.78, 0.95), chips=1, chipd=0.04)
            y += w


def bollard(k, x, y):
    k.put(cyl(0.2, 0.62, 8, r2=0.17), GS, M=T(x, y, 0.0), tint=0.85)
    k.put(cyl(0.26, 0.12, 8), GS, M=T(x, y, 0.62), tint=0.9)
    k.put(torus(0.19, 0.03, 10, 4), COP, M=T(x, y, 0.42))
    k.put(torus(0.22, 0.035, 10, 4), ROPE, M=T(x, y, 0.2))


@asset("zr_pier_4m", CAT)
def zr_pier_4m(k):
    pier_body(k, -2.0, 2.0)
    pier_deck(k, -2.0, 2.0)
    kerbs(k, -2.0, 2.0)
    bollard(k, 1.85, 0.0)
    bollard(k, -1.85, 0.6)
    k.col_box(5.0, 4.0, 4.0, T(0, 0, -2.0))
    for sx in (-1, 1):
        cbox(k, sx * 2.3, sx * 2.52, -2.0, 2.0, 0, 0.2)
    return dict(recenter=False)


@asset("zr_pier_end", CAT)
def zr_pier_end(k):
    r = k.r
    # water steps cut into the seaward (-y) corner on +x, down to z=-1.25
    sx0, sx1 = 0.3, 2.3
    nst, rise, run = 5, 0.25, 0.32
    ys = -2.0
    yt = ys + nst * run
    pier_body(k, -2.0, 2.0, ends=(-1,))
    pier_deck(k, yt, 2.0, wire=False)
    pave(k, -2.3, sx0, -2.0, yt, 0.0, 1, 1, th=0.35, bed=False)
    wire_inlay(k, (0, -1.6, 0.0), (0, 2.0, 0.0), (0, 0, 1), 0.12)
    kerbs(k, -2.0, 2.0, sides=(-1,))
    kerbs(k, yt, 2.0, sides=(1,))
    for i in range(5):
        x = -2.3 + i * 0.52
        blk(k, x + 0.01, x + 0.5, -2.2, -1.98, -0.35, 0.2, GS, rt(k, 0.78, 0.95), chips=1, chipd=0.04)
    Mf = T((sx0 + 2.35) / 2, ys, -nst * rise)
    blk(k, sx0, 2.35, ys, yt, -4.0, -nst * rise, GSD, 0.3)
    stair_flight(k, Mf, 2.35 - sx0, nst, rise, run, split=(0.8, 1.2))
    blk(k, sx0 - 0.02, sx0 + 0.02, ys, yt, -nst * rise, 0.0, GS, 0.7)
    k.put(box(2.0, 0.05, 0.3), "BH_Moss", M=T(1.3, ys - 0.02, -1.15), tint=0.6)
    # lamp post on the end, bollards at the corners
    blk(k, -1.75, -0.85, -1.75, -0.85, 0.0, 0.3, GS, 0.85, chips=2)
    blk(k, -1.48, -1.12, -1.48, -1.12, 0.3, 2.3, GS, 0.88, chips=1)
    blk(k, -1.5, -1.1, -1.5, -1.1, 1.5, 1.75, TURQ, 0.85)
    blk(k, -1.58, -1.02, -1.58, -1.02, 2.3, 2.45, GS, 0.95)
    cage_lamp(k, T(-1.3, -1.3, 2.75), rc=0.15, h=0.56, ribs=6)
    sock(k, "light", (-1.3, -1.3, 2.75))
    bollard(k, -1.9, 0.9)
    bollard(k, 1.9, 1.3)
    # collision
    cbox(k, -2.5, sx0, -2.0, 2.0, -4.0, 0.0)
    cbox(k, sx0, 2.5, yt, 2.0, -4.0, 0.0)
    cbox(k, sx0, 2.5, ys, yt, -4.0, -nst * rise)
    k.col_mesh(ramp_wedge(nst, rise, run, -(2.35 - sx0) / 2, (2.35 - sx0) / 2), Mf)
    cbox(k, -2.52, -2.3, -2.0, 2.0, 0, 0.2)
    cbox(k, 2.3, 2.52, yt, 2.0, 0, 0.2)
    cbox(k, -2.3, sx0, -2.2, -1.98, 0, 0.2)
    cbox(k, -1.75, -0.85, -1.75, -0.85, 0, 2.45)
    return dict(recenter=False)


# ===============================================================================================================
# Agdao's ship
def ship_hb(t):
    if t >= 0.5:
        q = (t - 0.5) / 0.5
        return max(0.14, 3.0 * max(0.0, 1 - q ** 2.1) ** 0.55)
    q = (0.5 - t) / 0.5
    return max(0.14, 3.0 * max(0.0, 1 - q ** 2.8) ** 0.45)


def ship_zk(t):
    return -1.6 + 1.0 * sstep(0.8, 1.0, t) + 0.7 * sstep(0.18, 0.0, t)


def ship_zs(t):
    return 2.95 + 1.2 * sstep(0.62, 1.0, t) ** 1.2 + 0.85 * sstep(0.36, 0.0, t)


def ship_pt(t, u):
    zk, zs, hb = ship_zk(t), ship_zs(t), ship_hb(t)
    z = zk + (zs - zk) * u
    f = max(0.0, 1 - (1 - u) ** 2.3) ** 0.65
    w = 0.1 + (hb - 0.1) * f * (1 - 0.05 * sstep(0.8, 1.0, u))
    return w, z


def ship_y(t):
    return -11.0 + 22.0 * t


def ship_u_at(t, z):
    zk, zs = ship_zk(t), ship_zs(t)
    return max(0.0, min(1.0, (z - zk) / (zs - zk)))


def hull_line(t_list, u, off=0.0, side=1):
    out = []
    for t in t_list:
        w, z = ship_pt(t, u)
        out.append((side * (w + off), ship_y(t), z))
    return out


@asset("zr_ship", CAT)
def zr_ship(k):
    r = k.r
    NS, NU = 34, 11
    ts = [i / NS for i in range(NS + 1)]
    us = [j / NU for j in range(NU + 1)]
    DECK = 2.2
    # --- hull planking: one strip per strake, both sides (carvel: flush strakes, alternating plank tone)
    for side in (1, -1):
        for j in range(NU):
            t = tb()
            vs = []
            for i, tt in enumerate(ts):
                row = []
                for u in (us[j], us[j + 1]):
                    w, z = ship_pt(tt, u)
                    row.append(t.verts.new((side * w, ship_y(tt), z)))
                vs.append(row)
            for i in range(NS):
                q = (vs[i][0], vs[i + 1][0], vs[i + 1][1], vs[i][1])
                t.faces.new(q if side > 0 else q[::-1])
            zc = ship_pt(0.5, (us[j] + us[j + 1]) / 2)[1]
            if zc < 0.25:
                k.put(t, WOODD, tint=0.5 + 0.06 * (j % 2), uvoff=False, smooth=40)
            else:
                k.put(t, WOOD, tint=(0.82 if j % 2 else 0.95) * rt(k, 0.92, 1.0), uvoff=False, smooth=40)
    # keel and inner bulwarks
    k.put(tube([(0, ship_y(tt), ship_zk(tt) - 0.08) for tt in ts[1:-1]], 0.16, 4), WOODD, tint=0.6, uvoff=False)
    for side in (1, -1):
        t = tb()
        vs = []
        for tt in ts:
            row = []
            for z in (DECK, None):
                u = ship_u_at(tt, DECK) if z is not None else 1.0
                w, zz = ship_pt(tt, u)
                row.append(t.verts.new((side * max(0.04, w - 0.12), ship_y(tt), zz)))
            vs.append(row)
        for i in range(NS):
            q = (vs[i][0], vs[i][1], vs[i + 1][1], vs[i + 1][0])
            t.faces.new(q if side > 0 else q[::-1])
        k.put(t, WOOD, tint=0.62, uvoff=False)
        # gunwale cap, wales, carved painted band, the Heartwire line
        k.put(tube(hull_line(ts[1:-1], 1.0, -0.04, side), 0.1, 5), WOODD, tint=0.75, uvoff=False)
        for u, rad in ((0.56, 0.08), (0.74, 0.085)):
            k.put(tube(hull_line(ts[2:-2], u, 0.04, side), rad, 5), WOODD, tint=0.6, uvoff=False)
        k.put(tube(hull_line(ts[2:-2], 0.655, 0.03, side), 0.035, 4), WIRE, uvoff=False)
        tb_ = tb()
        vs = []
        for tt in ts[2:-2]:
            row = []
            for u in (0.83, 0.94):
                w, z = ship_pt(tt, u)
                row.append(tb_.verts.new((side * (w + 0.025), ship_y(tt), z)))
            vs.append(row)
        for i in range(len(vs) - 1):
            q = (vs[i][0], vs[i + 1][0], vs[i + 1][1], vs[i][1])
            tb_.faces.new(q if side > 0 else q[::-1])
        k.put(tb_, TURQ, tint=0.85, uvoff=False)
        # carved bosses on the band (gold-leafed steps and dark discs alternating)
        for i in range(2, NS - 2, 1):
            tt = (ts[i] + ts[i + 1]) / 2
            w, z = ship_pt(tt, 0.885)
            w2, z2 = ship_pt(tt + 0.01, 0.885)
            d = Vector((side * (w2 - w), ship_y(tt + 0.01) - ship_y(tt), z2 - z))
            n = Vector((side, 0, 0.15)).normalized()
            c = Vector((side * (w + 0.05), ship_y(tt), z))
            if i % 2:
                k.put(box(0.32, 0.16, 0.06), "BH_Gold", M=frame(c, d, n), tint=0.8)
            else:
                k.put(cyl(0.11, 0.06, 6), WOODD, M=frame(c, d, n), tint=0.6)
    # oar ports between the wales
    for side in (1, -1):
        for yp in (-3.8, -2.6, 0.9, 2.1, 3.3, 4.5, 5.7):
            tt = (yp + 11) / 22
            w, z = ship_pt(tt, 0.70)
            n = Vector((side, 0, 0.08))
            c = Vector((side * (w + 0.02), yp, z))
            M = frame(c, (0, 1, 0), n)
            k.put(box(0.42, 0.34, 0.05), WOODD, M=M, tint=0.55)
            k.put(box(0.28, 0.22, 0.06), WOODD, M=M @ T(0, 0, 0.01), tint=0.08)
    # --- deck
    t = tb()
    vs = []
    for tt in ts:
        w, _ = ship_pt(tt, ship_u_at(tt, DECK))
        w = max(0.05, w - 0.1)
        vs.append((t.verts.new((-w, ship_y(tt), DECK)), t.verts.new((w, ship_y(tt), DECK))))
    for i in range(NS):
        t.faces.new((vs[i][0], vs[i][1], vs[i + 1][1], vs[i + 1][0]))
    k.put(t, WOOD, tint=0.85, uvoff=False)
    for x in (-1.6, -0.8, 0.0, 0.8, 1.6):
        k.put(box(0.03, 15.0, 0.012), WOODD, M=T(x, 1.0, DECK + 0.005), tint=0.3)
    # hatch, capstan, barrels, crates, rope coils, stowed oars, boarding step
    blk(k, -0.9, 0.9, 3.0, 4.6, DECK, DECK + 0.3, WOODD, 0.7)
    for i in range(5):
        blk(k, -0.8 + i * 0.4, -0.66 + i * 0.4, 3.1, 4.5, DECK + 0.3, DECK + 0.33, WOODD, 0.25)
    k.put(lathe([(0.0, 0.0), (0.4, 0.0), (0.4, 0.12), (0.26, 0.2), (0.24, 0.75), (0.34, 0.85), (0.34, 0.95), (0.0, 0.95)],
                10), WOODD, M=T(1.1, -4.0, DECK), tint=0.75)
    for i in range(4):
        a = math.radians(i * 90 + 20)
        k.put(cyl(0.04, 0.9, 5), WOOD, M=T(1.1, -4.0, DECK + 0.8) @ R(0, 90, math.degrees(a)), tint=0.8)
    for (x, y, rz) in ((1.9, 1.8, 0), (1.5, 2.4, 20), (-1.8, 5.6, 0)):
        k.put(lathe([(0.0, 0.0), (0.28, 0.0), (0.34, 0.35), (0.28, 0.7), (0.0, 0.7)], 10), WOOD, M=T(x, y, DECK),
              tint=0.75)
        for z in (0.12, 0.58):
            k.put(torus(0.31, 0.02, 10, 3), "BH_Iron", M=T(x, y, DECK + z))
    for (x, y, rz) in ((-1.7, 2.0, 10), (-1.65, 2.75, -5)):
        k.put(box(0.6, 0.6, 0.55), WOOD, M=TRS(x, y, DECK + 0.275, 0, 0, rz), tint=0.7)
    for (x, y) in ((0.9, -1.6), (-0.6, 7.0), (0.6, -6.2)):
        for i in range(3):
            k.put(torus(0.3 - i * 0.05, 0.045, 12, 4), ROPE, M=T(x, y, DECK + 0.045 + i * 0.08))
    for i in range(4):   # stowed oars along the starboard bulwark
        k.put(cyl(0.05, 5.0, 5), WOOD, M=T(1.95 - 0.12 * i, 5.4, DECK + 0.08 + 0.1 * (i % 2)) @ R(-90, 0, 0), tint=0.78)
    blk(k, -2.55, -2.05, -2.0, -1.0, DECK, DECK + 0.35, WOODD, 0.7)   # boarding step at the gangway
    for yy in (-2.1, -0.9):
        k.put(cyl(0.07, 1.25, 6), WOODD, M=T(-ship_hb((yy + 11) / 22) + 0.05, yy, DECK), tint=0.6)
        k.put(ico(0.1, 1), "BH_Gold", M=T(-ship_hb((yy + 11) / 22) + 0.05, yy, DECK + 1.28), tint=0.8)
    k.put(tube([(-ship_hb(0.43) + 0.05, -2.1, DECK + 1.15), (-ship_hb(0.43) - 0.05, -1.5, DECK + 0.95),
                (-ship_hb(0.43) + 0.05, -0.9, DECK + 1.15)], 0.025, 4), ROPE, uvoff=False)
    # --- stern castle (overhangs the narrowing stern), carved and painted, with a ladder up from the deck
    CY0, CY1, CZ = -10.5, -5.0, 4.4

    def cw(y):
        return lerp(1.35, 2.85, (y - CY0) / (CY1 - CY0))
    for side in (1, -1):
        p0 = Vector((side * cw(CY0), CY0, 0))
        p1 = Vector((side * cw(CY1), CY1, 0))
        d = p1 - p0
        L = d.length
        xdir = d if side > 0 else -d
        c = (p0 + p1) / 2
        Mw = frame((c.x, c.y, 0), xdir, (0, 0, 1))
        # Mw local: x along the wall, z up, -y outward (frame(): y = z x x)
        blk(k, -L / 2 - 0.05, L / 2 + 0.05, -0.08, 0.08, 2.45, CZ + 0.85, WOOD, 0.8, M=Mw)
        for i in range(6):
            u = -L / 2 + (i + 0.5) * L / 6
            blk(k, u - 0.06, u + 0.06, -0.16, -0.06, 2.5, CZ + 0.95, WOODD, 0.6, M=Mw)
            k.put(ico(0.08, 1), "BH_Gold", M=Mw @ T(u, -0.12, CZ + 1.02), tint=0.85)
        blk(k, -L / 2, L / 2, -0.11, -0.08, CZ + 0.1, CZ + 0.62, TURQ, 0.85, M=Mw)
        ornament_row(k, Mw, -L / 2 + 0.2, L / 2 - 0.2, CZ + 0.13, CZ + 0.6, -0.11, 0.04, 0.4, "fret", mat=WOODD,
                     tint=(0.55, 0.7))
        blk(k, -L / 2 - 0.08, L / 2 + 0.08, -0.14, 0.12, CZ + 0.85, CZ + 0.95, WOODD, 0.65, M=Mw)
        blk(k, -L / 2, L / 2, -0.12, -0.08, 3.1, 3.3, "BH_Gold", 0.7, M=Mw)
        # brackets under the overhang
        for i in range(4):
            yb = lerp(CY0 + 0.3, CY0 + 3.0, i / 3)
            hw = ship_pt((yb + 11) / 22, ship_u_at((yb + 11) / 22, 2.6))[0]
            x0 = side * max(0.1, hw - 0.05)
            x1 = side * cw(yb)
            k.put(tube([(x0, yb, 1.9), (x1 * 0.9 + x0 * 0.1, yb, 2.3), (x1, yb, 2.5)], 0.08, 4), WOODD, tint=0.6)
    blk(k, -cw(CY0), cw(CY0), CY0 - 0.08, CY0 + 0.08, 2.45, CZ + 0.85, WOOD, 0.8)
    blk(k, -1.1, 1.1, CY0 - 0.14, CY0 - 0.08, CZ - 1.6, CZ + 0.5, TURQ, 0.85)
    medallion(k, T(0, CY0 - 0.14, 0), 0.0, CZ - 0.55, 0.9, 0.0, 0.08, boss="BH_Gold", mat=WOODD, tint=0.6)
    for x in (-0.75, 0.75):
        k.put(prism([(0.0, 0.0), (0.12, 0.0), (0.12, 0.6), (0.0, 0.6)], 0.06), "BH_Gold",
              M=T(x - 0.06, CY0 - 0.16, CZ - 0.85), tint=0.8)
    # castle floor (deck) and underside
    pts_top = [(cw(CY0), CY0), (cw(CY1), CY1), (-cw(CY1), CY1), (-cw(CY0), CY0)]
    t = tb()
    for zz, flip in ((CZ, False), (2.45, True)):
        vv = [t.verts.new((x, y, zz)) for x, y in pts_top]
        t.faces.new(vv[::-1] if flip else vv)
    k.put(t, WOOD, tint=0.85, uvoff=False)
    k.put(box(5.8, 0.3, CZ - DECK), WOOD, M=T(0, CY1, (CZ + DECK) / 2), tint=0.72)
    blk(k, -0.55, 0.55, CY1 - 0.17, CY1 - 0.14, DECK, DECK + 1.85, WOODD, 0.08)
    blk(k, -0.7, 0.7, CY1 - 0.22, CY1 - 0.12, DECK + 1.85, DECK + 2.0, WOODD, 0.6)
    for x in (-1.9, 1.9):
        blk(k, x - 0.25, x + 0.25, CY1 - 0.17, CY1 - 0.14, DECK + 1.1, DECK + 1.55, WOODD, 0.08)
    ornament_row(k, T(0, CY1 - 0.15, 0), -2.7, 2.7, CZ - 0.42, CZ - 0.05, 0.0, 0.04, 0.32, "fret", mat="BH_Gold",
                 tint=(0.6, 0.75))
    for i in range(9):
        x = -2.8 + i * 0.7
        k.put(cyl(0.05, 0.85, 6), WOODD, M=T(x, CY1 + 0.05, CZ), tint=0.6)
    k.put(box(5.7, 0.12, 0.1), WOODD, M=T(0, CY1 + 0.05, CZ + 0.88), tint=0.65)
    # ladder from the main deck
    p0, p1 = Vector((1.6, CY1 + 2.0, DECK)), Vector((1.6, CY1 + 0.1, CZ))
    for dx in (-0.35, 0.35):
        k.put(tube([p0 + Vector((dx, 0, 0)), p1 + Vector((dx, 0, 0.4))], 0.05, 5), WOODD, tint=0.6)
    for i in range(7):
        q = p0.lerp(p1, (i + 0.6) / 7.5)
        k.put(box(0.7, 0.22, 0.05), WOOD, M=T(q.x, q.y, q.z), tint=0.75)
    # rudder, tiller, the serpent stern-post
    k.put(hexa([(-0.09, -11.95, -1.3), (0.09, -11.95, -1.3), (0.09, -11.2, -1.3), (-0.09, -11.2, -1.3),
                (-0.09, -11.75, 3.6), (0.09, -11.75, 3.6), (0.09, -11.3, 3.6), (-0.09, -11.3, 3.6)]), WOODD, tint=0.6)
    for z in (-0.6, 0.8, 2.2):
        k.put(box(0.24, 0.5, 0.1), "BH_Iron", M=T(0, -11.4, z), tint=0.7)
    k.put(tube([(0, -11.3, 4.3), (0, -10.4, 4.75), (0, -8.8, 4.95)], 0.07, 6), WOODD, tint=0.7)
    sp = [(0, -10.7, -1.4), (0, -11.1, 0.5), (0, -11.3, 2.6), (0, -11.4, 4.6), (0, -11.7, 6.0), (0, -12.15, 6.6)]
    k.put(tube(sp, [0.32, 0.3, 0.28, 0.26, 0.24, 0.22], 8), WOODD, tint=0.65, smooth=50)
    for i, (a, b) in enumerate(zip(sp[1:-1], sp[2:])):
        q = (Vector(a) + Vector(b)) / 2
        d = Vector(b) - Vector(a)
        k.put(torus(0.29 - 0.015 * i, 0.04, 12, 4), "BH_Gold", M=frame(q, (1, 0, 0), d), tint=0.75)
    serpent_head(k, T(0, -12.25, 6.45) @ R(-18, 0, 0), s=0.72, mat=WOODD, tint=0.62, plume=(TURQ, FEAR, "BH_Gold"),
                 eye=JADE, n_plume=9, plume_tint=0.85)
    # --- bow: stem post, serpent figurehead, bowsprit
    stem = [(0, 10.7, -0.9), (0, 11.35, 0.8), (0, 11.75, 2.6), (0, 12.0, 3.85), (0, 12.15, 4.35)]
    k.put(tube(stem, [0.26, 0.25, 0.24, 0.22, 0.2], 8), WOODD, tint=0.65, smooth=50)
    k.put(tube([(0, 11.0, 1.2), (0, 11.5, 2.6), (0, 11.85, 3.7)], 0.12, 5), "BH_Gold", tint=0.7)
    serpent_head(k, T(0, 12.05, 4.2) @ R(0, 0, 180) @ R(-14, 0, 0), s=0.66, mat=WOODD, tint=0.62,
                 plume=(TURQ, FEAR, "BH_Gold"), n_plume=9, plume_tint=0.85)
    k.put(tube([(0, 9.6, 3.6), (0, 12.0, 4.6), (0, 14.6, 5.65)], [0.15, 0.12, 0.08], 6), WOODD, tint=0.7)
    # --- mast, crow's nest, yard and the half-furled sail
    MY = 0.6
    k.put(tube([(0, MY, 0.8), (0, MY, 9.0), (0, MY, 18.2)], [0.27, 0.22, 0.15], 10), WOOD, tint=0.78, smooth=50)
    blk(k, -0.45, 0.45, MY - 0.45, MY + 0.45, DECK, DECK + 0.25, WOODD, 0.65)
    for z in (5.0, 9.5, 13.0):
        k.put(torus(0.25 - z * 0.004, 0.04, 12, 4), "BH_Iron", M=T(0, MY, z))
    k.put(lathe([(0.0, 0.0), (0.45, 0.0), (0.78, 0.25), (0.82, 0.95), (0.74, 0.95), (0.7, 0.3), (0.0, 0.3)], 12),
          WOODD, M=T(0, MY, 15.3), tint=0.65)
    k.put(torus(0.8, 0.05, 14, 4), "BH_Gold", M=T(0, MY, 16.22), tint=0.7)
    k.put(cyl(0.18, 0.25, 8), "BH_Gold", M=T(0, MY, 18.15), tint=0.75)
    YZ, YY = 14.2, MY + 0.34
    k.put(tube([(-6.3, YY, YZ), (-3.0, YY, YZ + 0.05), (0, YY, YZ + 0.08), (3.0, YY, YZ + 0.05), (6.3, YY, YZ)],
               [0.08, 0.13, 0.17, 0.13, 0.08], 8), WOODD, tint=0.7)
    SB = 9.55
    nx, nz = 12, 6
    for i in range(nx):
        t = tb()
        rows = []
        for j in range(nz + 1):
            row = []
            zz = lerp(YZ - 0.12, SB + 0.35, j / nz)
            for xx in (lerp(-5.7, 5.7, i / nx), lerp(-5.7, 5.7, (i + 1) / nx)):
                belly = 0.35 * math.sin(math.pi * j / nz) * math.cos(xx / 5.7 * math.pi / 2)
                row.append(t.verts.new((xx, YY + 0.12 + belly, zz)))
            rows.append(row)
        for j in range(nz):
            q = (rows[j][0], rows[j][1], rows[j + 1][1], rows[j + 1][0])
            t.faces.new(q)
        red = i in (2, 3, 8, 9)
        k.put(two_sided(t, 0.02), "BH_ClothCream", tint=(1.0, 0.32, 0.24) if red else (0.95, 0.92, 0.85), uvoff=False)
    roll = []
    for i in range(13):
        xx = lerp(-5.8, 5.8, i / 12)
        roll.append((xx, YY + 0.25, SB + 0.02 * math.sin(i * 1.7)))
    k.put(tube(roll, [0.24 + 0.1 * abs(math.sin(i * 1.3)) for i in range(13)], 8), "BH_ClothCream", tint=0.88,
          smooth=60)
    for xx in (-4.5, -2.25, 0.0, 2.25, 4.5):
        k.put(torus(0.33, 0.035, 10, 4), ROPE, M=T(xx, YY + 0.25, SB) @ R(0, 90, 0))
        k.put(tube([(xx, YY - 0.05, YZ), (xx, YY + 0.0, SB + 0.3)], 0.022, 3), ROPE)
    # --- rigging
    head = Vector((0, MY, 15.0))
    for side in (1, -1):
        for yy in (-0.6, -1.7, -2.8):
            tt = (yy + 11) / 22
            p = Vector((side * (ship_hb(tt) + 0.05), yy, ship_zs(tt) - 0.05))
            k.put(tube([head, p], 0.03, 4), ROPE, uvoff=False)
            k.put(box(0.1, 0.35, 0.5), "BH_Iron", M=T(p.x, p.y, p.z - 0.3), tint=0.7)
        sh = [Vector((side * (ship_hb((yy + 11) / 22) + 0.05), yy, ship_zs((yy + 11) / 22) - 0.05)) for yy in
              (-0.6, -2.8)]
        for f in [0.12 + 0.07 * i for i in range(10)]:
            a = sh[0].lerp(head, f)
            b = sh[1].lerp(head, f)
            k.put(tube([a, b], 0.018, 3, cap_start=False, cap_end=False), ROPE, uvoff=False)
    top_ = Vector((0, MY, 17.6))
    for p in ((0, 14.5, 5.62), (1.0, -10.0, CZ + 0.95), (-1.0, -10.0, CZ + 0.95)):
        k.put(tube([top_, Vector(p)], 0.035, 4), ROPE, uvoff=False)
    for side in (1, -1):
        arm = Vector((side * 6.2, YY, YZ))
        k.put(tube([arm, Vector((side * 1.6, -8.6, CZ + 0.95))], 0.025, 3), ROPE, uvoff=False)
        k.put(tube([top_, arm], 0.025, 3), ROPE, uvoff=False)
    k.put(tube([top_ + Vector((0.2, 0, 0)), Vector((0.25, MY + 0.5, DECK + 0.4))], 0.03, 4), ROPE, uvoff=False)
    # --- copper wire lanterns at bow and stern
    k.put(cyl(0.06, 1.0, 6), WOODD, M=T(0, 10.3, ship_zs((10.3 + 11) / 22) - 0.2), tint=0.6)
    yb_, zb_ = 10.3, ship_zs((10.3 + 11) / 22) + 1.05
    cage_lamp(k, T(0, yb_, zb_), rc=0.15, h=0.52, ribs=6)
    k.put(cyl(0.05, 1.3, 6), WOODD, M=T(0, CY0 + 0.2, CZ + 0.8), tint=0.6)
    zs_ = CZ + 2.35
    cage_lamp(k, T(0, CY0 + 0.2, zs_), rc=0.16, h=0.55, ribs=6)
    sock(k, "light_bow", (0, yb_, zb_))
    sock(k, "light_stern", (0, CY0 + 0.2, zs_))
    sock(k, "helm", (0, -8.4, CZ))
    tg = (-1.5 + 11) / 22
    sock(k, "gangway", (-(ship_hb(tg) + 0.1), -1.5, ship_zs(tg)))
    sock(k, "npc", (-1.6, -1.5, DECK))
    k.col_box(5.9, 22.4, 4.65, T(0, 0, -1.6 + 4.65 / 2))
    return dict(recenter=False)


# ===============================================================================================================
# gate and walls
def coursed_block(k, M, hx, hy, z0, z1, course=(0.55, 0.75), lens=(0.9, 1.6), depth=0.45, tint=(0.72, 0.92),
                  inset=0.0, alt_p=0.15):
    r = k.r
    hs = course_heights(r, z1 - z0, *course)
    z = z0
    k.put(frustum(hx - 0.06 - inset, hy - 0.06 - inset, hx - 0.06 - inset, hy - 0.06 - inset, z0, z1), GSD, M=M,
          tint=0.3)
    for h in hs:
        for s in range(4):
            L, D = (hx, hy) if s % 2 == 0 else (hy, hx)
            mitred_run(k, mm(M, R(0, 0, 90 * s)), L, D, z + 0.012, z + h - 0.012, inset, inset, depth, lens, GS, tint,
                       alt=GSD, alt_p=alt_p)
        z += h


def stepped_merlon(k, M, x, y, z, w=0.9, d=0.6, h=0.55, rot=0):
    Mm = mm(M, T(x, y, z) @ R(0, 0, rot))
    blk(k, -w / 2, w / 2, -d / 2, d / 2, 0, h * 0.55, GS, rt(k, 0.82, 0.95), chips=1, chipd=0.04, M=Mm)
    blk(k, -w * 0.3, w * 0.3, -d * 0.4, d * 0.4, h * 0.55, h, GS, rt(k, 0.82, 0.95), M=Mm)


@asset("zr_gate_arch", CAT)
def zr_gate_arch(k):
    r = k.r
    for sx, nm in ((-1, "light_a"), (1, "light_b")):
        cx = sx * 5.6
        Mt = T(cx, 0, 0)
        tier_ring(k, 1.6, 1.6, 0.0, 4.2, 1.2, 0.2, 0.08, courses=2, blen=(0.8, 1.4), unit_h=0.5, bay=3.0,
                  orn_sides=(0, 2) + ((1,) if sx > 0 else (3,)), wire_sides=(), cornice_depth=0.5, ct=0.24, rb=0.14,
                  M=Mt, two_rows=True)
        coursed_block(k, Mt, 1.38, 1.38, 4.2, 5.8, course=(0.5, 0.6), lens=(0.8, 1.3))
        mitred_run(k, Mt, 1.45, 1.45, 5.8, 6.0, -0.02, -0.02, 0.6, (1.0, 1.6), GS, (0.88, 1.0))
        coursed_block(k, Mt, 1.15, 1.15, 6.0, 6.55, course=(0.5, 0.6), lens=(0.8, 1.2))
        blk(k, cx - 1.22, cx + 1.22, -1.22, 1.22, 6.55, 6.68, GS, 0.95, chips=2)
        for (mx, my) in ((-0.6, -0.6), (0.6, -0.6), (-0.6, 0.6), (0.6, 0.6)):
            stepped_merlon(k, Mt, mx, my, 6.68, w=0.6, d=0.5, h=0.34)
        # Heartwire up the inner face (into the passage) and a caged lamp on the front face
        xi = cx - sx * 1.6
        for yy in (-0.8, 0.8):
            wire_inlay(k, (xi, yy, 0.1), (xi, yy, 4.1), (-sx, 0, 0), 0.1)
        bx = cx + sx * 0.4
        blk(k, bx - 0.12, bx + 0.12, -1.75, -1.6, 2.95, 3.35, GS, 0.85)
        k.put(cyl(0.025, 0.35, 6), BRZ, M=T(bx, -1.6, 3.3) @ R(90, 0, 0))
        cage_lamp(k, T(bx, -1.95, 3.05), rc=0.12, h=0.42, ribs=6)
        sock(k, nm, (bx, -1.95, 3.05))
        cbox(k, cx - 1.6, cx + 1.6, -1.6, 1.6, 0, 7.0)
    # carved lintel and crest
    LZ0, LZ1 = 4.6, 5.6
    blk(k, -4.6, 4.6, -1.1, 1.1, LZ0, LZ1, GSD, 0.35)
    for s in (0, 2):
        Ms = R(0, 0, 90 * s)
        blk(k, -4.0, 4.0, -1.15, -1.1, LZ0 + 0.1, LZ1 - 0.12, PLR, 0.85, M=Ms)
        ornament_row(k, Ms, -3.9, 3.9, LZ0 + 0.14, LZ1 - 0.16, -1.15, 0.07, 0.62, "mix")
        blk(k, -4.6, 4.6, -1.2, -1.0, LZ1 - 0.12, LZ1 + 0.05, GS, 0.95, M=Ms)
        blk(k, -4.6, 4.6, -1.18, -1.0, LZ0, LZ0 + 0.1, GS, 0.9, M=Ms)
    wire_inlay(k, (-4.0, 0, LZ0), (4.0, 0, LZ0), (0, 0, -1), 0.12)
    for i, x in enumerate((-2.4, 0.0, 2.4)):
        stepped_merlon(k, None, x, 0, LZ1 + 0.05, w=1.4 if i == 1 else 1.0, d=0.9, h=0.8 if i == 1 else 0.6)
    glyph(k, T(0, -0.46, LZ1 + 0.38), 0, 0.42)
    # paved passage
    pave(k, -4.0, 4.0, -1.6, 1.6, 0.06, 4, 2, th=0.16, bed=False)
    cbox(k, -4.6, 4.6, -1.1, 1.1, LZ0, LZ1 + 0.85)
    cbox(k, -4.0, 4.0, -1.6, 1.6, -0.1, 0.06)
    return dict(recenter=False, damp=0.25, damp_h=1.0)


@asset("zr_wall_4m", CAT)
def zr_wall_4m(k):
    r = k.r
    from masonry import masonry
    # leaning talus on the outer (-y) face, then a straight coursed wall
    blk(k, -2.0, 2.0, -0.45, 0.55, 0, 4.0, GSD, 0.3)
    k.put(yz_prism([(-0.75, 0.0), (-0.45, 0.0), (-0.45, 1.2), (-0.6, 1.2)], -2.0, 2.0), GSD, tint=0.3)
    for ci, (za, zb) in enumerate(((0.0, 0.6), (0.6, 1.2))):
        ws, _ = split_lengths(r, 4.0, 0.9, 1.6)
        x = -2.0
        for w in ws:
            ya, yb = -0.75 + 0.25 * za / 1.2, -0.75 + 0.25 * zb / 1.2
            c = [(x + 0.015, ya, za + 0.015), (x + w - 0.015, ya, za + 0.015), (x + w - 0.015, -0.35, za + 0.015),
                 (x + 0.015, -0.35, za + 0.015), (x + 0.015, yb, zb - 0.015), (x + w - 0.015, yb, zb - 0.015),
                 (x + w - 0.015, -0.35, zb - 0.015), (x + 0.015, -0.35, zb - 0.015)]
            t = hexa(c)
            if r.random() < 0.5:
                chip(t, r, 1, 0.06)
            k.put(t, GS if r.random() > 0.3 else GSD, tint=rt(k, 0.62, 0.85))
            x += w
    masonry(k, -2.0, 2.0, 1.2, 3.3, 1.0, mat=GS, core=False, bev=0.0, course=(0.5, 0.7), blen=(0.8, 1.4),
            M=T(0, 0.05, 0), chip_rng=(0, 1), tint=(0.7, 0.9))
    masonry(k, -2.0, 2.0, 0.0, 1.2, 0.5, mat=GS, core=False, bev=0.0, course=(0.5, 0.7), blen=(0.8, 1.4),
            M=T(0, 0.3, 0), chip_rng=(0, 1), tint=(0.65, 0.85))
    # glyph band both faces, coping with the Heartwire channel, stepped merlons
    for s, mat_ in ((0, PLR), (2, TURQ)):
        Ms = R(0, 0, 90 * s)
        D = 0.45 if s == 0 else 0.55
        blk(k, -2.0, 2.0, -D - 0.05, -D + 0.1, 3.3, 3.95, mat_, 0.85, M=Ms)
        if s == 0:
            ornament_row(k, Ms, -1.98, 1.98, 3.34, 3.91, -D - 0.05, 0.06, 0.5, "mix")
    blk(k, -2.0, 2.0, -0.5, 0.6, 3.3, 4.0, GSD, 0.3)
    ws, _ = split_lengths(r, 4.0, 0.8, 1.3)
    x = -2.0
    for w in ws:
        blk(k, x + 0.01, x + w - 0.01, -0.58, 0.68, 4.0, 4.24, GS, rt(k, 0.85, 1.0), chips=1, chipd=0.04)
        x += w
    wire_inlay(k, (-2.0, -0.4, 4.24), (2.0, -0.4, 4.24), (0, 0, 1), 0.1)
    for x in (-1.0, 1.0):
        stepped_merlon(k, None, x, 0.1, 4.24, w=1.2, d=0.8, h=0.76)
    for _ in range(4):
        moss_patch(k, r.uniform(-1.8, 1.8), -0.8 - r.uniform(0, 0.2), 0.0, r.uniform(0.3, 0.6))
    cbox(k, -2.0, 2.0, -0.75, 0.6, 0, 1.2)
    cbox(k, -2.0, 2.0, -0.6, 0.68, 1.2, 5.0)
    return dict(recenter=False, damp=0.3, damp_h=1.0)


@asset("zr_wall_tower", CAT)
def zr_wall_tower(k):
    r = k.r
    # talus-and-panel base, coursed shaft, painted fret frieze, cornice, stepped merlons
    tier_ring(k, 2.5, 2.5, 0.0, 2.7, 1.6, 0.3, 0.12, courses=2, blen=(1.0, 1.7), unit_h=0.5, bay=4.6,
              orn_sides=(0, 1, 3), wire_sides=(), cornice_depth=0.6, ct=0.24, rb=0.14)
    coursed_block(k, None, 2.25, 2.25, 2.7, 5.4, course=(0.5, 0.7), lens=(0.9, 1.5))
    for s in range(4):
        Ms = R(0, 0, 90 * s)
        blk(k, -2.27, 2.27, -2.3, -2.2, 5.4, 6.15, PLR, 0.85, M=Ms)
        if s != 2:
            ornament_row(k, Ms, -2.2, 2.2, 5.44, 6.11, -2.3, 0.07, 0.6, "mix")
        mitred_run(k, Ms, 2.4, 2.4, 6.15, 6.45, 0.0, 0.0, 0.7, (1.0, 1.6), GS, (0.88, 1.0))
        for u in (-0.8, 0.8):
            blk(k, u - 0.07, u + 0.07, -2.27, -2.2, 3.4, 4.5, GSD, 0.06, M=Ms)
        for i, u in enumerate((-1.75, 0.0, 1.75)):
            stepped_merlon(k, Ms, u, -2.1, 6.45, w=1.0 if i != 1 else 1.3, d=0.55, h=1.2 if i != 1 else 1.55)
    blk(k, -2.2, 2.2, -2.2, 2.2, 6.3, 6.5, PAVE, 0.75)
    # Heartwire down the front face into the ground
    wire_inlay(k, (0, -2.3, 5.35), (0, -2.3, 2.75), (0, -1, 0), 0.12)
    pts = [(0, -2.43, 2.72), (0, -2.43, 1.6), (0, -2.27, 1.57), (0, -2.56, 0.05), (0, -4.2, 0.04)]
    wire_tube(k, pts, 0.06)
    for _ in range(5):
        s = r.randrange(4)
        moss_patch(k, r.uniform(-2.0, 2.0), -2.6 - r.uniform(0, 0.2), 0.0, r.uniform(0.3, 0.7), M=R(0, 0, 90 * s))
    cbox(k, -2.5, 2.5, -2.5, 2.5, 0, 8.0)
    return dict(recenter=False, damp=0.3, damp_h=1.2)


@asset("zr_footbridge_8m", CAT)
def zr_footbridge_8m(k):
    r = k.r
    W = 1.5
    # corbelled body: each course reaches further in toward the middle
    courses = [(-0.75, -0.35, 0.0), (-1.15, -0.75, 1.6), (-1.6, -1.15, 2.4), (-2.2, -1.6, 3.2)]
    for (za, zb, xin) in courses:
        for sx in (-1, 1):
            x0, x1 = (sx * 4.0, sx * xin) if xin > 0 else (-4.0, 4.0)
            if xin == 0.0 and sx > 0:
                continue
            a, b = min(x0, x1), max(x0, x1)
            ws, _ = split_lengths(r, b - a, 0.7, 1.3)
            x = a
            for w in ws:
                blk(k, x + 0.012, x + w - 0.012, -W, W, za + 0.012, zb - 0.012, GS, rt(k, 0.7, 0.9), chips=1)
                x += w
            k.put(box(b - a - 0.04, 2 * W - 0.08, zb - za - 0.02), GSD, M=T((a + b) / 2, 0, (za + zb) / 2), tint=0.3)
            cbox(k, a, b, -W, W, za, zb)
    # frieze on the spandrel faces
    for s in (0, 2):
        Ms = R(0, 0, 90 * s)
        blk(k, -4.0, 4.0, -W - 0.03, -W + 0.05, -0.72, -0.38, PLR, 0.85, M=Ms)
        ornament_row(k, Ms, -3.95, 3.95, -0.7, -0.4, -W - 0.03, 0.05, 0.28, "fret")
    # deck slabs, kerbs, glyph posts, rails with a Heartwire line along each
    pave(k, -4.0, 4.0, -W + 0.3, W - 0.3, 0.0, 4, 1, th=0.35, bed=False)
    for sy in (-1, 1):
        y0, y1 = sy * (W - 0.3), sy * W
        blk(k, -4.0, 4.0, min(y0, y1), max(y0, y1), -0.35, 0.12, GS, 0.85, chips=0)
        for x in (-3.85, -1.92, 0.0, 1.92, 3.85):
            blk(k, x - 0.15, x + 0.15, min(y0, y1), max(y0, y1), 0.12, 1.1, GS, rt(k, 0.85, 0.95), chips=1, chipd=0.03)
            blk(k, x - 0.19, x + 0.19, min(y0, y1) - 0.04, max(y0, y1) + 0.04, 1.1, 1.2, GS, 0.95)
            glyph(k, T(x, sy * (W + 0.0), 0.7) @ R(0, 0, 0 if sy < 0 else 180), (0, 1, 2, 1, 0)[int((x + 3.85) / 1.92 + 0.5)],
                  0.22, dep=0.02)
        for (a, b) in ((-3.7, -2.07), (-1.77, -0.15), (0.15, 1.77), (2.07, 3.7)):
            blk(k, a, b, sy * (W - 0.27), sy * (W - 0.03), 0.8, 0.98, GS, rt(k, 0.82, 0.95), chips=1, chipd=0.03)
            blk(k, a, b, sy * (W - 0.25), sy * (W - 0.05), 0.12, 0.3, GS, rt(k, 0.75, 0.9))
        wire_tube(k, [(-3.95, sy * (W - 0.32), 0.92), (3.95, sy * (W - 0.32), 0.92)], r=0.035)
        cbox(k, -4.0, 4.0, min(y0, y1), max(y0, y1), 0.0, 1.15)
    cbox(k, -4.0, 4.0, -W, W, -0.35, 0.0)
    return dict(recenter=False)
