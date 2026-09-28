"""Dungeon environment kit (run bh-012): five themed dungeons + shared stairs / railing.

Themes: deeps (Saltmouth Deeps, drowned cistern), warren (Hollowroot Warren, fungal), ember (Emberforge Depths),
rime (Rimeglass Barrow), orrery (The Shattered Orrery), dungeon (shared pieces).
Conventions as the rest of the kit: metres, Z-up (exported Y-up), front = -Y, origin bottom-centre unless noted,
`<name>-colonly` collision children, sockets as child empties (`light`, `flame`, `center`).
Wall-mounted pieces (fungus_shelf, icicles_hanging) have their back on the y=0 plane and extend toward -Y.
Hanging pieces (chain_hoist, icicles_hanging) have the origin at the TOP (all geometry below z=0).
armillary_sphere exports rings `ring_a`/`ring_b`/`ring_c` and `core` as separate child nodes whose origins sit at the
sphere centre; each ring lies in its node's local XY plane (Blender), i.e. it spins about its local Z (Godot local Y).
"""
import math

import bmesh
from mathutils import Vector

import kit
from kit import *  # noqa
from masonry import *  # noqa
from registry import asset
from assets_props import plank, rivet
from assets_arch import plinth, pillar_shaft, capital, pillar_moss, streaks, door_cuts
from assets_nature import rand_unit, align_z, rock_piece

# New BH_* names (MaterialLibrary ENV additions for bh-012). Export colours are linear previews only.
EXTRA_MATERIALS = {
    "BH_Lava": ((1.0, 0.3, 0.04, 1), 0.5, 0.0, ((1.0, 0.35, 0.05), 8.0)),
    "BH_Ice": ((0.45, 0.65, 0.8, 1), 0.12, 0.0, ((0.4, 0.7, 1.0), 0.6)),
    "BH_Spore": ((0.6, 0.85, 0.15, 1), 0.5, 0.0, ((0.65, 1.0, 0.2), 5.0)),
    "BH_Starglass": ((0.5, 0.3, 0.9, 1), 0.2, 0.0, ((0.6, 0.35, 1.0), 6.0)),
    "BH_Brass": ((0.55, 0.38, 0.12, 1), 0.35, 1.0, None),
    "BH_Coral": ((0.75, 0.25, 0.15, 1), 0.8, 0.0, None),
    "BH_Basalt": ((0.05, 0.048, 0.05, 1), 0.85, 0.0, None),
    "BH_Marble": ((0.7, 0.68, 0.64, 1), 0.35, 0.0, None),
    "BH_MushroomCap": ((0.22, 0.08, 0.14, 1), 0.7, 0.0, None),
    "BH_Fungus": ((0.62, 0.56, 0.45, 1), 0.75, 0.0, None),
    "BH_Snow": ((0.85, 0.88, 0.92, 1), 0.95, 0.0, None),
    "BH_Kelp": ((0.06, 0.09, 0.02, 1), 0.7, 0.0, None),
}
for _n, _v in EXTRA_MATERIALS.items():
    kit.MATERIALS.setdefault(_n, _v)
    if _n not in kit.MATERIAL_NAMES:
        kit.MATERIAL_NAMES.append(_n)


# ---------------------------------------------------------------------------------------------------------------
# helpers
def surf_pts(t, M, n, r, cond=None):
    """n random (point, normal) samples on temp bmesh t transformed by M (call BEFORE k.put, which frees t)."""
    M = M or T()
    N3 = M.to_3x3().inverted_safe().transposed()
    t.normal_update()
    data = []
    for f in t.faces:
        vs = [M @ v.co for v in f.verts]
        c = sum(vs, Vector()) / len(vs)
        nr = (N3 @ f.normal).normalized()
        if cond and not cond(c, nr):
            continue
        data.append((c, vs, nr, f.calc_area()))
    if not data:
        return []
    tot = sum(d[3] for d in data)
    out = []
    for _ in range(n):
        x = r.random() * tot
        for c, vs, nr, a in data:
            x -= a
            if x <= 0:
                break
        v = r.choice(vs)
        out.append((c.lerp(v, r.uniform(0, 0.7)), nr))
    return out


def bar(k, a, b, w, mat, tint=1.0, h=None, segs=None, smooth=None, r2=None):
    a, b = Vector(a), Vector(b)
    d = b - a
    t = cyl(w, d.length, segs, r2=r2) if segs else box(w, h or w, d.length, base=True)
    k.put(t, mat, M=T(*a) @ align_z(d), tint=tint, smooth=smooth)


def chain(k, a, b, R_=0.05, r_=0.013, mat="BH_Iron"):
    a, b = Vector(a), Vector(b)
    d = b - a
    pitch = R_ * 2.1
    n = max(1, int(d.length / pitch))
    A = align_z(d)
    for i in range(n):
        p = a + d.normalized() * (pitch * (i + 0.5))
        k.put(torus(R_, r_, 8, 4), mat, M=T(*p) @ A @ R(0, 0, 90 * (i % 2)) @ R(90, 0, 0) @ S(1, 1.6, 1),
              tint=k.r.uniform(0.7, 1.0))


def barnacle(k, p, nrm, s):
    prof = [(s, 0.0), (s * 0.92, s * 0.35), (s * 0.62, s * 0.75), (s * 0.42, s * 0.8), (s * 0.36, s * 0.55),
            (0.0, s * 0.5)]
    t = lathe(prof, 6, cap_bot=False, cap_top=False)
    jitter(t, k.r, s * 0.08)
    k.put(t, "BH_Bone", M=T(*p) @ align_z(nrm, k.r.uniform(0, 6.28)) @ T(0, 0, -s * 0.15), tint=k.r.uniform(0.55, 0.9))


def barnacles_on(k, pts, smin=0.03, smax=0.08):
    for p, nr in pts:
        barnacle(k, p, nr, k.r.uniform(smin, smax))


def ribbon(k, pts, width, mat="BH_Kelp", tint=None, thick=0.12):
    n = len(pts)
    rads = [width * (0.25 + 0.75 * math.sin(math.pi * (0.08 + 0.86 * i / (n - 1)))) for i in range(n)]
    k.put(tube(pts, rads, 4, flat=(1.0, thick)), mat, tint=tint or k.r.uniform(0.6, 1.0), smooth=50)


def kelp(k, base, H, w, phase, lean=(0.0, 0.0), n=12):
    base = Vector(base)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        pts.append(base + Vector((lean[0] * H * t * t + 0.12 * math.sin(t * 6 + phase) * t,
                                  lean[1] * H * t * t + 0.1 * math.cos(t * 5 + phase * 1.3) * t, H * t)))
    ribbon(k, pts, w)
    return pts


def hang_weed(k, top, L, phase):
    top = Vector(top)
    pts = [top + Vector((0.05 * math.sin(i * 1.3 + phase), 0.05 * math.cos(i + phase), -L * i / 7)) for i in range(8)]
    ribbon(k, pts, k.r.uniform(0.03, 0.06))


def small_mush(k, M, h, rc, glow_all=False, cap="BH_MushroomCap"):
    rs = max(0.012, rc * 0.22)
    k.put(lathe([(rs * 1.3, 0), (rs, h * 0.4), (rs * 0.85, h)], 7), "BH_Fungus", M=M, tint=k.r.uniform(0.8, 1.0),
          smooth=60)
    prof = [(0.0, h * 0.93), (rc * 0.9, h * 0.92), (rc, h * 1.0), (rc * 0.82, h + rc * 0.35), (rc * 0.4, h + rc * 0.55),
            (0.0, h + rc * 0.6)]
    under = (lambda f: "BH_Spore" if f.normal.z < -0.2 else None)
    k.put(lathe(prof, 10), "BH_Spore" if glow_all else cap, M=M, tint=k.r.uniform(0.75, 1.0), smooth=60,
          mat_fn=None if glow_all else under)


def crystal(k, base, d, L, r_, mat="BH_Ice", tip=0.3, segs=6, tint=None):
    prof = [(r_ * 0.85, -0.05 * L), (r_, L * 0.12), (r_ * 0.93, L * (1 - tip)), (0.0, L)]
    t = lathe(prof, segs, cap_bot=True)
    top = max(t.verts, key=lambda v: v.co.z)
    top.co.x += k.r.uniform(-0.25, 0.25) * r_
    top.co.y += k.r.uniform(-0.25, 0.25) * r_
    jitter(t, k.r, r_ * 0.04)
    k.put(t, mat, M=T(*Vector(base)) @ align_z(Vector(d), k.r.uniform(0, 1)), tint=tint or k.r.uniform(0.75, 1.0))


def flat_ring(k, rin, rout, z0, z1, mat, M=None, segs=64, tint=1.0):
    t = lathe([(rin, z0), (rout, z0), (rout, z1), (rin, z1), (rin, z0)], segs, cap_bot=False, cap_top=False)
    k.put(t, mat, M=M, tint=tint, smooth=30)


def extrude_xy(pts, h, z0=0.0):
    t = tb()
    bot = [t.verts.new((x, y, z0)) for x, y in pts]
    top = [t.verts.new((x, y, z0 + h)) for x, y in pts]
    t.faces.new(bot[::-1])
    t.faces.new(top)
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        t.faces.new((bot[i], bot[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(t, faces=t.faces)
    return t


def attach_children(k, children):
    """children: list of (node name, sub Kit, location, rotation degrees). Created as child mesh objects after finish."""
    orig = k.finish

    def fin(**kw):
        ob = orig(**kw)
        for name, sub, loc, rot in children:
            co = sub._bm_to_obj(sub.bm, name)
            co.parent = ob
            co.location = loc
            co.rotation_euler = tuple(math.radians(a) for a in rot)
        return ob
    k.finish = fin


def seabed(k, n, rad, z=0.0):
    r = k.r
    for i in range(n):
        a = r.uniform(0, math.tau)
        d = r.uniform(0.2, 1.0) * rad
        s = r.uniform(0.1, 0.28)
        k.put(rock(r, (s, s * 0.8, s * 0.5), cuts=5, subd=1, noise_amp=0.04, seed_off=i * 0.7 + 3), "BH_StoneDark",
              M=TRS(math.cos(a) * d, math.sin(a) * d, z - 0.03, 0, 0, r.uniform(0, 360)), tint=r.uniform(0.6, 0.9))


# ===============================================================================================================
# Saltmouth Deeps
def coral_branch(k, p, d, L, r0, depth, tint):
    r = k.r
    pts = [p]
    cur, dd = Vector(p), Vector(d)
    n = 5
    for i in range(n):
        dd = (dd + rand_unit(r) * 0.25 + Vector((0, 0, 0.18))).normalized()
        cur = cur + dd * (L / n)
        pts.append(cur.copy())
    rads = [lerp(r0, r0 * 0.6, i / n) for i in range(n + 1)]
    k.put(tube(pts, rads, 6, cap_start=False, cap_end=False), "BH_Coral", tint=tint, smooth=60)
    k.put(ico(r0 * 0.66, 1), "BH_Coral", M=T(*cur), tint=min(1.0, tint * 1.15), smooth=60)
    if depth > 0:
        for j in range(r.randint(2, 3)):
            nd = (dd + rand_unit(r) * 0.9)
            nd.z = abs(nd.z) + 0.25
            coral_branch(k, pts[r.randint(2, n)], nd.normalized(), L * 0.65, r0 * 0.66, depth - 1, tint)


@asset("coral_cluster", "deeps", col=False)
def coral_cluster(k):
    r = k.r
    rock_piece(k, (0.55, 0.45, 0.28), 300, moss=False, mat="BH_Stone", tint=(0.55, 0.7))
    for (x, y, L, tint) in ((0.0, 0.05, 0.42, 0.95), (-0.28, -0.12, 0.3, 0.7), (0.3, 0.1, 0.34, 0.82)):
        coral_branch(k, Vector((x, y, 0.2)), Vector((r.uniform(-0.2, 0.2), r.uniform(-0.2, 0.2), 1)).normalized(), L,
                     0.055, 2, tint)
    # tube sponges
    for i, (x, y, h) in enumerate(((0.36, -0.22, 0.55), (0.45, -0.1, 0.4), (0.28, -0.32, 0.32), (-0.4, 0.22, 0.45))):
        ro = r.uniform(0.07, 0.1)
        ri = ro * 0.7
        prof = [(0.0, h * 0.75), (ri * 0.95, h * 0.76), (ri, h), (ro, h), (ro * 1.05, h * 0.5), (ro * 1.25, 0.0)]
        k.put(lathe(prof, 10), "BH_Coral", M=TRS(x, y, 0.12, r.uniform(-12, 12), r.uniform(-12, 12), 0),
              tint=r.uniform(0.45, 0.65), smooth=60)
    # brain coral
    t = ico(1.0, 3)
    for v in t.verts:
        v.co = Vector((v.co.x * 0.22, v.co.y * 0.22, max(v.co.z, -0.1) * 0.16))
    ndisp(t, 30.0, 0.03, k.noff, octaves=2)
    k.put(t, "BH_Coral", M=T(-0.22, -0.3, 0.1), tint=0.55, smooth=40)
    # sea fan
    fan = ico(1.0, 2)
    for v in fan.verts:
        v.co = Vector((v.co.x * 0.28, v.co.y * 0.02, (v.co.z + 1) * 0.25))
    ndisp(fan, 6.0, 0.02, k.noff)
    k.put(fan, "BH_Coral", M=TRS(-0.1, 0.3, 0.15, 0, 0, 20), tint=0.4, smooth=50)
    return dict()


@asset("kelp_strands", "deeps", col=False)
def kelp_strands(k):
    r = k.r
    rock_piece(k, (0.35, 0.3, 0.18), 160, moss=False, mat="BH_StoneDark", tint=(0.6, 0.8))
    for i in range(9):
        a = r.uniform(0, math.tau)
        d = r.uniform(0.02, 0.22)
        H = r.uniform(1.7, 3.05)
        pts = kelp(k, (math.cos(a) * d, math.sin(a) * d, 0.1), H, r.uniform(0.06, 0.1), r.uniform(0, 6),
                   (math.cos(a) * 0.12, math.sin(a) * 0.12))
        for j in range(3, len(pts) - 2, 3):
            k.put(ico(0.025, 1), "BH_Kelp", M=T(*(pts[j] + Vector((0.04, 0, 0)))), tint=1.0, smooth=60)
        # holdfast
        k.put(tube([pts[0] + Vector((0, 0, -0.1)), pts[0] + Vector((math.cos(a) * 0.15, math.sin(a) * 0.15, -0.05))],
                   0.025, 5), "BH_Kelp", tint=0.5)
    return dict()


@asset("anchor_giant", "deeps")
def anchor_giant(k):
    r = k.r
    M = T(0.2, 0, -0.08) @ R(0, 26, 20)
    sh = tube([(0, 0, 0.2), (0, 0, 1.8), (0, 0, 3.3)], [0.16, 0.13, 0.11], 8)
    bp = surf_pts(sh, M, 40, r)
    k.put(sh, "BH_Iron", M=M, tint=0.9, smooth=40)
    k.put(torus(0.3, 0.055, 14, 6), "BH_Iron", M=M @ TRS(0, 0, 3.6, 0, 90, 0), smooth=40)
    k.put(box(0.2, 0.2, 0.16, bev=0.02), "BH_Iron", M=M @ T(0, 0, 3.32))
    st = tube([(0, -0.95, 2.85), (0, 0.95, 2.85)], 0.07, 8)
    bp += surf_pts(st, M, 12, r)
    k.put(st, "BH_Iron", M=M, smooth=40, tint=0.85)
    for sy in (-1, 1):
        k.put(ico(0.11, 1), "BH_Iron", M=M @ T(0, sy * 0.97, 2.85), smooth=40)
    k.put(ico(0.2, 2), "BH_Iron", M=M @ T(0, 0, 0.22), smooth=40)
    for sx in (-1, 1):
        arm = tube([(0, 0, 0.25), (sx * 0.5, 0, 0.15), (sx * 0.95, 0, 0.4), (sx * 1.15, 0, 0.85)], [0.13, 0.12, 0.1, 0.07], 8)
        bp += surf_pts(arm, M, 20, r)
        k.put(arm, "BH_Iron", M=M, smooth=40, tint=0.8)
        fl = prism([(-0.22, 0.0), (0.22, 0.0), (0.0, 0.55)], 0.07, bev=0.01)
        k.put(fl, "BH_Iron", M=M @ TRS(sx * 1.05, 0, 0.6, 0, sx * 25, 0), tint=0.75)
    barnacles_on(k, bp, 0.035, 0.08)
    for i in range(5):
        p = M @ Vector((0, r.uniform(-0.8, 0.8), 2.8))
        hang_weed(k, p, r.uniform(0.5, 1.3), i)
    # silt mound burying the crown
    t = ico(1.0, 2)
    for v in t.verts:
        v.co = Vector((v.co.x * 0.9, v.co.y * 0.75, max(v.co.z, -0.05) * 0.28))
    ndisp(t, 2.0, 0.05, k.noff)
    k.put(t, "BH_Stone", M=T(0.2, 0, 0), tint=0.6, smooth=50)
    seabed(k, 8, 1.4)
    k.col_mesh(box(0.45, 0.45, 3.6, base=True), M.copy())
    k.col_mesh(box(2.6, 0.7, 1.0, base=True), M.copy())
    k.col_box(1.8, 1.5, 0.3, T(0.2, 0, 0.15))
    return dict(recenter=False)


@asset("sunken_bell", "deeps")
def sunken_bell(k):
    r = k.r
    prof = [(0.0, 1.46), (0.28, 1.42), (0.4, 1.2), (0.42, 0.9), (0.5, 0.5), (0.62, 0.2), (0.74, 0.04), (0.82, 0.0),
            (0.85, 0.08), (0.73, 0.24), (0.59, 0.52), (0.5, 0.92), (0.48, 1.22), (0.42, 1.44), (0.3, 1.56), (0.0, 1.6)]
    M = T(0, 0, 0.85) @ R(0, 104, 0) @ T(0, 0, -0.8)
    bell = lathe(prof, 24, cap_bot=False, cap_top=False)
    bp = surf_pts(bell, M, 45, r, cond=lambda c, n: n.z > 0.25)
    k.put(bell, "BH_Brass", M=M, tint=0.8, smooth=40)
    for z, rr in ((0.06, 0.84), (0.35, 0.67), (1.15, 0.49)):
        k.put(torus(rr + 0.01, 0.025, 28, 4), "BH_Brass", M=M @ T(0, 0, z), tint=0.9, smooth=40)
    for a in (0, 90):
        k.put(torus(0.16, 0.045, 12, 5), "BH_Brass", M=M @ TRS(0, 0, 1.68, 90, 0, a), smooth=40)
    k.put(tube([(0, 0, 1.4), (0.2, 0, 0.9), (0.38, 0, 0.45)], 0.035, 6), "BH_Iron", M=M, smooth=40)
    k.put(ico(0.12, 1), "BH_Iron", M=M @ T(0.38, 0, 0.4), smooth=40)
    barnacles_on(k, bp, 0.03, 0.07)
    for i in range(6):
        p, _ = bp[i * 5]
        hang_weed(k, p, r.uniform(0.3, 0.7), i)
    for i in range(4):
        a = r.uniform(0, math.tau)
        kelp(k, (math.cos(a) * 1.1, math.sin(a) * 0.9, 0.0), r.uniform(0.6, 1.2), 0.05, i)
    t = ico(1.0, 2)
    for v in t.verts:
        v.co = Vector((v.co.x * 1.2, v.co.y * 0.9, max(v.co.z, -0.05) * 0.22))
    ndisp(t, 2.5, 0.04, k.noff)
    k.put(t, "BH_Stone", M=T(0, 0, 0.0), tint=0.55, smooth=50)
    seabed(k, 7, 1.3)
    k.put(prism([(-0.2, 0), (0.25, 0.02), (0.05, 0.3)], 0.06), "BH_Brass", M=TRS(-1.0, -0.7, 0.03, 90, 0, 30), tint=0.7)
    k.col_mesh(cyl(0.72, 1.65, 10), M @ T(0, 0, -0.02))
    return dict()


@asset("barnacle_pillar", "deeps")
def barnacle_pillar(k):
    r = k.r
    WH = 4.0
    z = plinth(k, 1.0)
    pillar_shaft(k, z, WH - 0.34, quoin=True)
    capital(k, WH - 0.34)
    pillar_moss(k, WH - 0.36, n=2)
    pts = []
    for c in range(34):
        side = r.randrange(4)
        nrm = [Vector((0, -1, 0)), Vector((0, 1, 0)), Vector((-1, 0, 0)), Vector((1, 0, 0))][side]
        tang = Vector((nrm.y, -nrm.x, 0))
        zc = 0.34 + 2.9 * r.random() ** 1.8
        u = r.uniform(-0.42, 0.42)
        for j in range(r.randint(2, 6)):
            p = nrm * 0.515 + tang * (u + r.uniform(-0.1, 0.1)) + Vector((0, 0, zc + r.uniform(-0.1, 0.1)))
            pts.append((p, nrm))
    for i in range(18):  # plinth tops
        a = r.uniform(0, math.tau)
        p = Vector((math.cos(a) * 0.63, math.sin(a) * 0.63, 0.18))
        p.x, p.y = max(-0.64, min(0.64, p.x)), max(-0.64, min(0.64, p.y))
        pts.append((p, Vector((0, 0, 1))))
    barnacles_on(k, pts, 0.03, 0.075)
    for i in range(9):
        a = r.uniform(0, math.tau)
        p = Vector((math.cos(a) * 0.72, math.sin(a) * 0.72, WH - 0.1))
        hang_weed(k, p, r.uniform(0.5, 1.6), i)
    for i in range(6):
        a = r.uniform(0, math.tau)
        kelp(k, (math.cos(a) * 0.8, math.sin(a) * 0.8, 0.0), r.uniform(0.6, 1.5), 0.05, i)
    streaks(k, -1, 1, WH)
    k.col_box(1.3, 1.3, WH, T(0, 0, WH / 2))
    return dict(recenter=False, damp=0.4, damp_h=1.4)


# ===============================================================================================================
# Hollowroot Warren
@asset("mushroom_giant", "warren")
def mushroom_giant(k):
    r = k.r
    pts = [Vector((0, 0, -0.1)), Vector((0.02, 0, 0.6)), Vector((0.08, 0.02, 1.6)), Vector((0.18, 0.05, 2.7)),
           Vector((0.26, 0.08, 3.7)), Vector((0.3, 0.1, 4.65))]
    t = tube(pts, [1.0, 0.8, 0.68, 0.62, 0.62, 0.7], 14)
    ndisp(t, 1.5, 0.05, k.noff)
    k.put(t, "BH_Fungus", tint=0.9, smooth=60)
    # skirt
    k.put(lathe([(0.6, 3.75), (0.95, 3.6), (1.2, 3.3), (1.17, 3.26), (0.92, 3.52), (0.6, 3.66)], 18, cap_bot=False,
                cap_top=False), "BH_Fungus", M=T(0.27, 0.08, 0), tint=0.8, smooth=50)
    for i in range(6):  # root flares
        a = math.tau * i / 6 + r.uniform(-0.3, 0.3)
        k.put(tube([(math.cos(a) * 0.4, math.sin(a) * 0.4, 0.5), (math.cos(a) * 0.9, math.sin(a) * 0.9, 0.12),
                    (math.cos(a) * 1.4, math.sin(a) * 1.4, 0.0)], [0.22, 0.14, 0.05], 6), "BH_Fungus", tint=0.75, smooth=50)
    cx, cy, cz = 0.3, 0.1, 4.5
    CM = T(cx, cy, cz) @ R(6, -4, 0)
    cap = lathe([(0.0, 0.05), (0.5, 0.0), (2.2, 0.28), (2.95, 0.5), (3.05, 0.62), (2.85, 0.95), (2.3, 1.25),
                 (1.4, 1.5), (0.0, 1.6)], 28)
    ndisp(cap, 0.9, 0.07, k.noff)
    k.put(cap, "BH_MushroomCap", M=CM, tint=0.9, smooth=45,
          mat_fn=lambda f: "BH_Spore" if f.normal.z < -0.15 else None)
    for i in range(44):  # dark gills over the glowing underside
        a = math.tau * i / 44
        g = prism([(0.6, 0.0), (2.2, 0.28), (2.85, 0.47), (2.8, 0.36), (2.1, 0.12), (0.6, -0.14)], 0.035)
        k.put(g, "BH_MushroomCap", M=CM @ R(0, 0, math.degrees(a)), tint=0.5)
    for i in range(16):  # pale warts on top
        a = r.uniform(0, math.tau)
        d = r.uniform(0.3, 2.4)
        zz = lerp(1.6, 0.95, (d / 2.85) ** 2)
        k.put(ico(r.uniform(0.07, 0.16), 1), "BH_Fungus", M=CM @ TRS(math.cos(a) * d, math.sin(a) * d, zz, s=(1, 1, 0.5)),
              tint=1.0, smooth=50)
    for i in range(10):  # hanging spore threads
        a = r.uniform(0, math.tau)
        d = r.uniform(1.0, 2.6)
        p = CM @ Vector((math.cos(a) * d, math.sin(a) * d, 0.2 + d * 0.08))
        L = r.uniform(0.3, 0.9)
        k.put(tube([p, p + Vector((0.02, 0, -L))], [0.012, 0.006], 4), "BH_Spore", tint=1.0)
        k.put(ico(0.035, 1), "BH_Spore", M=T(*(p + Vector((0.02, 0, -L)))), tint=1.0)
    for i in range(4):
        a = r.uniform(0, math.tau)
        small_mush(k, TRS(math.cos(a) * 1.1, math.sin(a) * 1.1, 0, r.uniform(-10, 10), r.uniform(-10, 10), 0),
                   r.uniform(0.2, 0.45), r.uniform(0.1, 0.2))
    k.sockets.append(("light", (cx, cy, cz - 0.5)))
    k.col_mesh(cyl(0.8, 4.6, 8))
    return dict(recenter=False)


@asset("mushroom_glow_cluster", "warren", col=False)
def mushroom_glow_cluster(k):
    r = k.r
    t = ico(1.0, 2)
    for v in t.verts:
        v.co = Vector((v.co.x * 0.42, v.co.y * 0.38, max(v.co.z, -0.02) * 0.08))
    k.put(t, "BH_Moss", tint=0.8, smooth=60)
    spots = [(0.0, 0.0, 0.62, 0.2)] + [(r.uniform(-0.3, 0.3), r.uniform(-0.28, 0.28), r.uniform(0.1, 0.42), 0) for _ in range(9)]
    for i, (x, y, h, rc) in enumerate(spots):
        rc = rc or h * r.uniform(0.35, 0.55)
        small_mush(k, TRS(x, y, 0, r.uniform(-14, 14), r.uniform(-14, 14), 0), h, rc, glow_all=(i % 3 == 1))
    return dict()


@asset("fungus_shelf", "warren", col=False)
def fungus_shelf(k):
    """Wall piece: back on y=0 (wall), shelves stick out toward -Y. Origin = bottom-centre of the back edge."""
    r = k.r
    for (x, z, s) in ((-0.3, 0.1, 0.34), (0.25, 0.32, 0.42), (-0.12, 0.68, 0.3), (0.36, 0.9, 0.22), (-0.42, 0.98, 0.18)):
        t = lathe([(0.0, 0.0), (s, 0.0), (s * 0.97, s * 0.1), (s * 0.8, s * 0.2), (s * 0.4, s * 0.27), (0.0, s * 0.29)],
                  10, arc=math.pi, cap_bot=False, cap_top=False)
        bmesh.ops.holes_fill(t, edges=[e for e in t.edges if e.is_boundary], sides=0)
        ndisp(t, 5.0, s * 0.04, k.noff)
        k.put(t, "BH_MushroomCap", M=TRS(x, 0.0, z, r.uniform(-6, 6), 0, 180), tint=r.uniform(0.7, 1.0), smooth=50,
              mat_fn=lambda f: "BH_Spore" if f.normal.z < -0.5 else None)
        for j in range(3):  # growth rings
            rr = s * (0.55 + 0.15 * j)
            k.put(lathe([(rr, s * (0.24 - 0.05 * j)), (rr + 0.012, s * (0.22 - 0.05 * j))], 10, arc=math.pi,
                        cap_bot=False, cap_top=False), "BH_Fungus", M=TRS(x, 0.0, z, 0, 0, 180), tint=0.8)
    t = ico(1.0, 2)  # mycelium mat on the wall
    for v in t.verts:
        v.co = Vector((v.co.x * 0.3, -abs(v.co.y) * 0.02 - 0.002, (v.co.z + 1) * 0.35 + 0.1))
    ndisp(t, 6.0, 0.06, k.noff)
    for v in t.verts:
        v.co.y = min(v.co.y, -0.002)
    k.put(t, "BH_Fungus", tint=0.6, smooth=50)
    return dict(recenter=False)


@asset("root_arch", "warren")
def root_arch(k):
    r = k.r
    X, SP, RZ = 1.85, 2.2, 2.05
    cl = [Vector((-X - 0.08 + 0.08 * z / SP, 0, z)) for z in (-0.1, 0.55, 1.2, 1.85)]
    for i in range(13):
        th = math.pi - math.pi * i / 12
        cl.append(Vector((X * math.cos(th), 0, SP + RZ * math.sin(th))))
    cl += [Vector((X + 0.08 - 0.08 * z / SP, 0, z)) for z in (1.85, 1.2, 0.55, -0.1)]
    ncl = len(cl)
    tops = []
    for j in range(4):
        ph = j * math.pi / 2 + r.uniform(-0.3, 0.3)
        pts, rads = [], []
        for i, c in enumerate(cl):
            s = i / (ncl - 1)
            a = cl[min(i + 1, ncl - 1)] - cl[max(i - 1, 0)]
            nin = Vector((-a.z, 0, a.x)).normalized()
            off = Vector((0, 1, 0)) * math.cos(ph + s * 7) * 0.3 + nin * math.sin(ph + s * 7) * 0.22
            off += Vector((mnoise.noise(c * 0.8 + k.noff + Vector((j, 0, 0))) * 0.08, 0, 0))
            pts.append(c + off)
            rads.append(lerp(0.36, 0.2, math.sin(math.pi * s)) * r.uniform(0.85, 1.1))
        t = tube(pts, rads, 8)
        ndisp(t, 3.0, 0.03, k.noff + Vector((j, 0, 0)))
        k.put(t, "BH_Bark", tint=r.uniform(0.75, 0.95), smooth=60, mat_fn=moss_fn(k, 0.55, 1.4, 0.1))
        tops += pts[5:13]
    for i in range(10):  # hanging rootlets (kept above 3.2 m)
        p = r.choice(tops)
        L = max(0.15, min(p.z - 3.3, r.uniform(0.3, 1.0)))
        k.put(tube([p, p + Vector((0.05, 0.03, -L * 0.5)), p + Vector((0.02, 0.06, -L))], [0.04, 0.025, 0.008], 5),
              "BH_Bark", tint=0.8, smooth=60)
    for sx in (-1, 1):  # foot flares
        for j in range(4):
            a = math.radians(r.uniform(-70, 70)) + (0 if sx > 0 else math.pi)
            b = Vector((sx * X, 0, 0.3))
            k.put(tube([b, b + Vector((math.cos(a) * 0.6, math.sin(a) * 0.6, -0.2)),
                        b + Vector((math.cos(a) * 1.1, math.sin(a) * 1.1, -0.32))], [0.2, 0.1, 0.03], 6), "BH_Bark",
                  tint=0.8, smooth=60)
    for i in range(12):  # glowing caps on the roots
        c = r.choice(cl[1:6] + cl[-6:-1])
        p = c + Vector((r.uniform(-0.2, 0.2), r.choice((-1, 1)) * 0.3, 0.1))
        small_mush(k, TRS(p.x, p.y, p.z, r.uniform(-30, 30), r.uniform(-30, 30), 0), r.uniform(0.12, 0.3),
                   r.uniform(0.08, 0.16), glow_all=i % 4 == 0)
    for i in range(14):
        p = r.choice(tops) + Vector((0, r.choice((-1, 1)) * 0.22, 0))
        k.put(ico(r.uniform(0.02, 0.045), 1), "BH_Spore", M=T(*p), tint=1.0)
    for sx in (-1, 1):
        k.col_box(0.9, 1.1, 3.2, T(sx * X, 0, 1.6))
    return dict(recenter=False)


@asset("spore_pod", "warren")
def spore_pod(k):
    r = k.r

    def pod(M, sc):
        prof = [(0.22, 0.0), (0.45, 0.15), (0.55, 0.45), (0.5, 0.8), (0.32, 1.02), (0.12, 1.14), (0.06, 1.2)]
        prof = [(a * sc, b * sc) for a, b in prof]
        t = lathe(prof, 16, cap_top=False)
        ndisp(t, 2.5, 0.03 * sc, k.noff)
        k.put(t, "BH_Fungus", M=M, tint=r.uniform(0.75, 0.95), smooth=55)
        for j in range(7):
            a0 = math.tau * j / 7 + r.uniform(-0.2, 0.2)
            pts = []
            for i in range(10):
                z = 0.05 + 1.08 * i / 9
                # sample profile radius at height z*sc
                zz = z * sc
                rr = prof[-1][0]
                for p0, p1 in zip(prof, prof[1:]):
                    if p0[1] <= zz <= p1[1]:
                        rr = lerp(p0[0], p1[0], (zz - p0[1]) / max(1e-6, p1[1] - p0[1]))
                        break
                a = a0 + 0.3 * math.sin(z * 5 + j)
                pts.append(M @ Vector((math.cos(a) * (rr + 0.02 * sc), math.sin(a) * (rr + 0.02 * sc), zz)))
            k.put(tube(pts, [0.025 * sc * (1 - 0.5 * i / 9) for i in range(10)], 5), "BH_Spore", tint=1.0, smooth=50)
        k.put(ico(0.09 * sc, 1), "BH_Spore", M=M @ T(0, 0, 1.18 * sc), tint=1.0)
        k.put(torus(0.08 * sc, 0.03 * sc, 10, 5), "BH_Fungus", M=M @ T(0, 0, 1.19 * sc), tint=0.7)

    pod(T(0, 0, 0), 1.0)
    pod(TRS(0.62, -0.25, 0, 0, 12, 20), 0.45)
    pod(TRS(-0.55, 0.3, 0, -10, -8, 0), 0.32)
    t = ico(1.0, 2)  # mycelium mat
    for v in t.verts:
        v.co = Vector((v.co.x * 0.95, v.co.y * 0.85, max(v.co.z, -0.02) * 0.06))
    ndisp(t, 4.0, 0.03, k.noff)
    k.put(t, "BH_Fungus", tint=0.55, smooth=50)
    k.col_mesh(cyl(0.55, 1.2, 8))
    return dict(recenter=False)


# ===============================================================================================================
# Emberforge Depths
@asset("forge_furnace", "ember")
def forge_furnace(k):
    r = k.r
    W, D, H, th = 3.5, 2.4, 2.6, 0.5
    w, sill, spring, ri = 1.3, 0.45, 0.85, 0.65
    cuts = [RectCut(-w / 2, w / 2, sill, spring), CircleCut(0, spring, ri + 0.33)]
    ccuts = [RectCut(-w / 2, w / 2, sill, spring), CircleCut(0, spring, ri + 0.05)]
    kw = dict(mat="BH_Basalt", core_mat="BH_Basalt", tint=(0.8, 1.0), quoin_mat="BH_StoneDark")
    masonry(k, -W / 2, W / 2, 0, H, th, M=T(0, -D / 2 + th / 2, 0), cuts=cuts, core_cuts=ccuts, zbreaks=(sill, spring),
            quoin="both", **kw)
    masonry(k, -W / 2, W / 2, 0, H, th, M=T(0, D / 2 - th / 2, 0), quoin="both", **kw)
    for sx in (-1, 1):
        masonry(k, -D / 2 + th, D / 2 - th, 0, H, th, M=T(sx * (W / 2 - th / 2), 0, 0) @ R(0, 0, 90), **kw)
    arch_ring(k, 0, spring, ri, ri + 0.32, th, n=9, mat="BH_StoneDark", M=T(0, -D / 2 + th / 2, 0), proud=0.05)
    # glowing interior + coal bed
    k.put(box(W - 2 * th + 0.02, D - 2 * th + 0.02, H - 0.1), "BH_Lava", M=T(0, 0, H / 2), tint=0.8)
    for i in range(10):
        s = r.uniform(0.1, 0.2)
        k.put(rock(r, (s, s, s * 0.6), cuts=4, subd=1, seed_off=i), "BH_Basalt" if i % 2 else "BH_Lava",
              M=T(r.uniform(-0.5, 0.5), r.uniform(-0.85, -0.5), sill), tint=0.4)
    k.put(box(w + 0.5, 0.6, 0.12, bev=0.02), "BH_StoneDark", M=T(0, -D / 2 - 0.1, sill - 0.06), tint=0.9)
    # roof, hood, chimney
    capstones(k, -W / 2 - 0.1, W / 2 + 0.1, H, D, 0.28, over=0.1, mat="BH_Basalt", tint=(0.7, 0.9))
    hb, ht = (W - 0.5, D - 0.5), (1.2, 1.2)
    k.put(hexa([(-hb[0] / 2, -hb[1] / 2, 0), (hb[0] / 2, -hb[1] / 2, 0), (hb[0] / 2, hb[1] / 2, 0), (-hb[0] / 2, hb[1] / 2, 0),
                (-ht[0] / 2, -ht[1] / 2 + 0.3, 0.55), (ht[0] / 2, -ht[1] / 2 + 0.3, 0.55), (ht[0] / 2, ht[1] / 2 + 0.3, 0.55),
                (-ht[0] / 2, ht[1] / 2 + 0.3, 0.55)], 0.04), "BH_Basalt", M=T(0, 0, H + 0.28), tint=0.8)
    z = H + 0.8
    ci = 0
    while z < 3.95:
        h = min(0.34, 4.0 - z)
        t = box(1.0, 1.0, h - 0.02, bev=0.03)
        chip(t, r, 2, 0.05)
        k.put(t, "BH_Basalt", M=TRS(0, 0.3, z + h / 2, 0, 0, r.uniform(-3, 3)), tint=r.uniform(0.75, 0.95))
        z += h
        ci += 1
    k.put(box(0.62, 0.62, 0.05), "BH_Lava", M=T(0, 0.3, 3.99), tint=0.6)
    k.put(box(1.06, 1.06, 0.07), "BH_Iron", M=T(0, 0.3, H + 1.3))
    # lava spill into a trough in front
    k.put(tube([(0, -D / 2 - 0.3, sill + 0.02), (0.05, -D / 2 - 0.42, 0.25), (0.08, -D / 2 - 0.55, 0.12)], [0.12, 0.09, 0.12],
               6, flat=(1.0, 0.45)), "BH_Lava", smooth=50)
    for sx in (-1, 1):
        k.put(box(0.16, 0.9, 0.22, bev=0.02), "BH_StoneDark", M=T(sx * 0.62, -D / 2 - 0.6, 0.11), tint=0.8)
    k.put(box(1.4, 0.16, 0.22, bev=0.02), "BH_StoneDark", M=T(0, -D / 2 - 1.0, 0.11), tint=0.8)
    k.put(box(1.1, 0.66, 0.06), "BH_Lava", M=T(0, -D / 2 - 0.6, 0.12))
    # open iron doors
    for sx in (-1, 1):
        DM = T(sx * (w / 2 + 0.2), -D / 2 - 0.05, sill) @ R(0, 0, sx * 70) @ T(-sx * 0.35, -0.03, 0.55)
        k.put(box(0.7, 0.05, 1.05, bev=0.01), "BH_Iron", M=DM, tint=0.8)
        for zz in (-0.35, 0.35):
            k.put(box(0.72, 0.07, 0.06), "BH_Iron", M=DM @ T(0, -0.02, zz), tint=0.6)
    # tongs + coal heap
    for i in range(2):
        bar(k, (-1.5 + i * 0.12, -D / 2 - 0.25, 0.0), (-1.4 + i * 0.18, -D / 2 + 0.01, 1.4), 0.025, "BH_Iron", segs=6)
    for i in range(9):
        s = r.uniform(0.08, 0.16)
        k.put(rock(r, (s, s, s * 0.7), cuts=4, subd=1, seed_off=i + 20), "BH_Basalt",
              M=T(1.3 + r.uniform(-0.25, 0.25), -D / 2 - 0.35 + r.uniform(-0.2, 0.2), 0), tint=0.3)
    k.sockets.append(("flame", (0, -D / 2 + 0.55, sill + 0.35)))
    k.sockets.append(("light", (0, -D / 2 - 0.9, 1.3)))
    k.col_box(W, D, H + 0.3, T(0, 0, (H + 0.3) / 2))
    k.col_box(1.0, 1.0, 4.0 - H - 0.3, T(0, 0.3, (4.0 + H + 0.3) / 2))
    k.col_box(1.4, 0.9, 0.25, T(0, -D / 2 - 0.6, 0.12))
    return dict(recenter=False)


@asset("lava_crucible", "ember")
def lava_crucible(k):
    r = k.r
    t = cyl(0.75, 0.25, 12, bev=0.03)
    chip(t, r, 3, 0.05)
    k.put(t, "BH_StoneDark", tint=0.8)
    for i in range(10):
        a = r.uniform(0, math.tau)
        d = r.uniform(0, 0.5)
        k.put(rock(r, (0.1, 0.09, 0.07), cuts=4, subd=1, seed_off=i), "BH_Lava" if i % 2 else "BH_Basalt",
              M=T(math.cos(a) * d, math.sin(a) * d, 0.24), tint=0.5)
    for i in range(4):
        a = math.tau * i / 4 + math.pi / 4
        bar(k, (math.cos(a) * 0.68, math.sin(a) * 0.68, 0.0), (math.cos(a) * 0.52, math.sin(a) * 0.52, 0.95), 0.04,
            "BH_Iron", segs=6)
    k.put(torus(0.53, 0.04, 20, 5), "BH_Iron", M=T(0, 0, 0.95), smooth=40)
    bowl = [(0.0, 0.12), (0.38, 0.14), (0.46, 0.52), (0.5, 0.6), (0.57, 0.6), (0.55, 0.45), (0.45, 0.08), (0.28, 0.0),
            (0.0, 0.0)]
    k.put(lathe(bowl, 20), "BH_Iron", M=T(0, 0, 0.85), tint=0.85, smooth=40)
    k.put(cyl(0.475, 0.03, 20), "BH_Lava", M=T(0, 0, 1.36))
    for i in range(5):
        a = r.uniform(0, math.tau)
        d = r.uniform(0, 0.32)
        k.put(ico(r.uniform(0.05, 0.1), 1), "BH_Lava", M=TRS(math.cos(a) * d, math.sin(a) * d, 1.39, s=(1, 1, 0.5)))
    k.put(prism([(-0.1, 0.0), (0.1, 0.0), (0.0, -0.18)], 0.1), "BH_Iron", M=TRS(0.57, 0, 1.44, 90, 0, 90))
    k.put(tube([(0.62, 0, 1.43), (0.68, 0, 1.2), (0.66, 0, 0.7), (0.5, 0, 0.3)], [0.035, 0.03, 0.025, 0.04], 6), "BH_Lava",
          smooth=50)
    for sy in (-1, 1):
        k.put(torus(0.1, 0.022, 10, 4), "BH_Iron", M=TRS(0, sy * 0.58, 1.35, 90, 0, 0))
    k.sockets.append(("light", (0, 0, 1.7)))
    k.col_mesh(cyl(0.75, 1.5, 8))
    return dict(recenter=False)


def tub_wall(k, q, thick, n, mat="BH_WoodDark"):
    """q = (bl, br, tl, tr) inner corners; outward = right-hand normal; n planks stacked bottom->top."""
    bl, br, tl, tr = [Vector(p) for p in q]
    nrm = (br - bl).cross(tl - bl).normalized() * thick
    for i in range(n):
        a0, a1 = i / n + 0.004, (i + 1) / n - 0.004
        l0, r0, l1, r1 = bl.lerp(tl, a0), br.lerp(tr, a0), bl.lerp(tl, a1), br.lerp(tr, a1)
        t = hexa([l0, r0, r0 + nrm, l0 + nrm, l1, r1, r1 + nrm, l1 + nrm], 0.008)
        jitter(t, k.r, 0.003)
        k.put(t, mat, tint=k.r.uniform(0.6, 1.0))


@asset("ore_cart", "ember")
def ore_cart(k):
    r = k.r
    for x in (-0.9, -0.3, 0.3, 0.9):
        plank(k, 1.3, 0.2, 0.1, TRS(x, 0, 0.05, 0, 0, 90 + r.uniform(-3, 3)), mat="BH_WoodDark", tint=(0.5, 0.7))
    for sy in (-1, 1):
        k.put(box(2.3, 0.06, 0.06, bev=0.01), "BH_Iron", M=T(0, sy * 0.45, 0.13), tint=0.8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            W_ = T(sx * 0.5, sy * 0.45, 0.34) @ R(90, 0, 0)
            k.put(cyl(0.18, 0.06, 12), "BH_Iron", M=W_ @ T(0, 0, -0.03), smooth=40)
            k.put(cyl(0.21, 0.02, 12), "BH_Iron", M=W_ @ T(0, 0, sy * 0.03 - 0.01), smooth=40, tint=0.8)
        k.put(cyl(0.03, 1.05, 6), "BH_Iron", M=TRS(sx * 0.5, -0.52, 0.34, -90, 0, 0))
    k.put(box(1.4, 0.7, 0.08), "BH_WoodDark", M=T(0, 0, 0.47), tint=0.6)
    z0, z1 = 0.5, 1.15
    b = [(-0.65, -0.4), (0.65, -0.4), (0.65, 0.4), (-0.65, 0.4)]
    tp = [(-0.8, -0.52), (0.8, -0.52), (0.8, 0.52), (-0.8, 0.52)]
    for i in range(4):
        j = (i + 1) % 4
        tub_wall(k, ((*b[j], z0), (*b[i], z0), (*tp[j], z1), (*tp[i], z1)), 0.05, 4)
    for i in range(4):  # corner straps + rim
        j = (i + 1) % 4
        bar(k, (*b[i], z0), (*tp[i], z1 + 0.02), 0.07, "BH_Iron", h=0.07)
        bar(k, (*tp[i], z1), (*tp[j], z1), 0.05, "BH_Iron", h=0.06)
        mid_b = Vector((*b[i], z0)).lerp(Vector((*b[j], z0)), 0.5)
        mid_t = Vector((*tp[i], z1)).lerp(Vector((*tp[j], z1)), 0.5)
        bar(k, mid_b, mid_t, 0.06, "BH_Iron", h=0.05)
    k.put(tube([(0.8, -0.35, 1.0), (1.0, -0.35, 1.02), (1.0, 0.35, 1.02), (0.8, 0.35, 1.0)], 0.022, 6), "BH_Iron", smooth=40)
    for i in range(16):
        s = r.uniform(0.1, 0.2)
        mat = "BH_Lava" if i % 5 == 0 else ("BH_Gold" if i % 7 == 3 else ("BH_Basalt" if i % 2 else "BH_Stone"))
        k.put(rock(r, (s, s * 0.9, s * 0.8), cuts=5, subd=1, seed_off=i), mat,
              M=TRS(r.uniform(-0.6, 0.6), r.uniform(-0.38, 0.38), 1.0 + r.uniform(0, 0.25) * (1 - abs(r.random() - 0.5)),
                    0, 0, r.uniform(0, 360)), tint=r.uniform(0.5, 0.9))
    k.col_box(1.7, 1.1, 1.35, T(0, 0, 0.67))
    return dict(recenter=False)


@asset("basalt_column", "ember")
def basalt_column(k):
    r = k.r
    Rc = 0.36
    sp = 2 * Rc * math.cos(math.pi / 6) + 0.03
    pos = [(0, 0)]
    for i in range(6):
        a = math.pi / 6 + math.tau * i / 6
        pos.append((math.cos(a) * sp, math.sin(a) * sp))
    for i in (0, 2, 4):
        a = math.pi / 6 + math.tau * i / 6 + math.pi / 6
        pos.append((math.cos(a) * sp * 1.73, math.sin(a) * sp * 1.73))
    heights = [4.0, 3.3, 2.6, 3.6, 1.8, 2.9, 2.2, 1.2, 1.6, 0.9]
    for (x, y), H in zip(pos, heights):
        z = 0.0
        while z < H - 0.05:
            h = min(H - z, r.uniform(0.6, 1.2))
            t = cyl(Rc, h - 0.05, 6)
            if z + h >= H - 0.05 and H < 3.9:
                slice_plane(t, (0, 0, h - 0.05 - r.uniform(0.05, 0.25)), (r.uniform(-0.4, 0.4), r.uniform(-0.4, 0.4), 1))
            chip(t, r, r.randint(1, 3), 0.05)
            jitter(t, r, 0.008)
            k.put(t, "BH_Basalt", M=TRS(x, y, z, 0, 0, 30 + r.uniform(-4, 4)), tint=r.uniform(0.7, 1.0))
            if z + h < H - 0.05:
                k.put(cyl(Rc * 0.9, 0.07, 6), "BH_Lava", M=TRS(x, y, z + h - 0.06, 0, 0, 30))
            z += h
        if r.random() < 0.5:
            a = r.uniform(0, math.tau)
            k.put(box(0.03, 0.02, H * 0.5), "BH_Lava", M=TRS(x + math.cos(a) * Rc * 0.86, y + math.sin(a) * Rc * 0.86,
                                                               H * 0.3, 0, 0, math.degrees(a) + 90))
    k.put(cyl(sp * 1.6, 0.03, 12), "BH_Lava", M=T(0, 0, 0.0))
    for i in range(3):  # fallen drums
        a = r.uniform(0, math.tau)
        t = cyl(Rc * 0.9, r.uniform(0.4, 0.7), 6)
        chip(t, r, 3, 0.06)
        k.put(t, "BH_Basalt", M=TRS(math.cos(a) * 1.7, math.sin(a) * 1.7, Rc * 0.78, 90, 0, math.degrees(a)), tint=0.8)
    k.col_mesh(cyl(sp * 1.75, 4.0, 6))
    return dict(recenter=False)


@asset("chain_hoist", "ember", col=False)
def chain_hoist(k):
    """Hangs from a ceiling: origin at the TOP of the beam, everything below z=0."""
    r = k.r
    t = box(4.0, 0.35, 0.4, bev=0.03)
    jitter(t, r, 0.006)
    k.put(t, "BH_WoodDark", M=T(0, 0, -0.2), tint=0.8)
    for x in (-1.6, 0.4, 1.6):
        k.put(box(0.08, 0.39, 0.44, bev=0.01), "BH_Iron", M=T(x, 0, -0.2))
    # pulley block
    k.put(box(0.1, 0.06, 0.3), "BH_Iron", M=T(0.4, 0, -0.55))
    for sy in (-1, 1):
        k.put(box(0.34, 0.03, 0.42, bev=0.01), "BH_Iron", M=T(0.4, sy * 0.07, -0.85), tint=0.8)
    k.put(cyl(0.15, 0.08, 14), "BH_WoodDark", M=TRS(0.4, -0.04, -0.85, -90, 0, 0), smooth=40)
    chain(k, (0.28, 0, -0.9), (0.28, 0, -2.2), 0.05, 0.013)
    chain(k, (0.54, 0, -0.9), (0.54, 0, -1.6), 0.05, 0.013)
    k.put(tube([(0.28, 0, -2.2), (0.28, 0, -2.4), (0.36, 0, -2.52), (0.44, 0, -2.42), (0.43, 0, -2.3)], 0.035, 6),
          "BH_Iron", smooth=40)
    # slung slab
    for sx in (-1, 1):
        chain(k, (0.36, 0, -2.48), (0.36 + sx * 0.5, 0, -3.1), 0.04, 0.011)
    k.put(box(1.3, 0.5, 0.26, bev=0.02), "BH_Iron", M=T(0.36, 0, -3.25), tint=0.7)
    for sx in (-1, 1):
        k.put(torus(0.06, 0.015, 10, 4), "BH_Iron", M=TRS(0.36 + sx * 0.5, 0, -3.1, 90, 0, 0))
    chain(k, (-1.3, 0, -0.4), (-1.3, 0, -3.7), 0.05, 0.013)
    k.put(tube([(-1.3, 0, -3.7), (-1.3, 0, -3.9), (-1.2, 0, -4.0), (-1.1, 0, -3.88)], 0.03, 6), "BH_Iron", smooth=40)
    return dict(recenter=False)


# ===============================================================================================================
# Rimeglass Barrow
@asset("ice_crystal_large", "rime")
def ice_crystal_large(k):
    r = k.r
    rock_piece(k, (0.9, 0.8, 0.35), 260, moss=False, mat="BH_Stone", tint=(0.5, 0.7))
    specs = [(0, 0, 3.0, 0.34, 0, 0)] + [(r.uniform(-0.6, 0.6), r.uniform(-0.6, 0.6), r.uniform(1.2, 2.4),
                                          r.uniform(0.2, 0.32), r.uniform(18, 45), 36 * i + r.uniform(-12, 12)) for i in range(10)]
    for (x, y, L, rr, tilt, az) in specs:
        d = Vector((math.sin(math.radians(tilt)) * math.cos(math.radians(az)),
                    math.sin(math.radians(tilt)) * math.sin(math.radians(az)), math.cos(math.radians(tilt))))
        crystal(k, (x, y, 0.1), d, L, rr)
    t = ico(1.0, 2)
    for v in t.verts:
        v.co = Vector((v.co.x * 0.95, v.co.y * 0.85, max(v.co.z, -0.02) * 0.3))
    ndisp(t, 3.0, 0.08, k.noff)
    k.put(t, "BH_Snow", tint=0.95, smooth=50)
    k.col_mesh(cyl(0.8, 2.6, 8))
    return dict(recenter=False)


@asset("ice_crystal_small", "rime", col=False)
def ice_crystal_small(k):
    r = k.r
    for i in range(6):
        tilt = 0 if i == 0 else r.uniform(15, 55)
        az = r.uniform(0, 360)
        d = Vector((math.sin(math.radians(tilt)) * math.cos(math.radians(az)),
                    math.sin(math.radians(tilt)) * math.sin(math.radians(az)), math.cos(math.radians(tilt))))
        crystal(k, (r.uniform(-0.1, 0.1), r.uniform(-0.1, 0.1), 0.0), d, 0.8 if i == 0 else r.uniform(0.25, 0.55),
                0.09 if i == 0 else r.uniform(0.04, 0.07))
    t = ico(1.0, 2)
    for v in t.verts:
        v.co = Vector((v.co.x * 0.3, v.co.y * 0.26, max(v.co.z, -0.02) * 0.06))
    k.put(t, "BH_Snow", smooth=50)
    return dict()


@asset("icicles_hanging", "rime", col=False)
def icicles_hanging(k):
    """Origin at the TOP back edge (wall face at y=0); crust + icicles hang below z=0 toward -Y."""
    r = k.r
    x = -2.0
    while x < 2.0:
        w = min(r.uniform(0.4, 0.8), 2.0 - x)
        t = box(w + 0.05, r.uniform(0.25, 0.32), r.uniform(0.1, 0.16), bev=0.03)
        subdiv(t, 2)
        ndisp(t, 5.0, 0.05, k.noff + Vector((x, 0, 0)))
        k.put(t, "BH_Snow", M=T(x + w / 2, -0.14, -0.06), tint=r.uniform(0.9, 1.0), smooth=40)
        t = box(w + 0.02, 0.22, 0.1, bev=0.02)
        k.put(t, "BH_Ice", M=T(x + w / 2, -0.14, -0.15), tint=0.9, smooth=40)
        x += w
    for i in range(72):
        x = r.uniform(-1.95, 1.95)
        L = r.uniform(0.15, 0.5) if r.random() < 0.7 else r.uniform(0.6, 1.3)
        r0 = r.uniform(0.03, 0.06) * (1.4 if L > 0.6 else 1.0)
        prof = [(0.0, -L), (r0 * 0.3, -L * 0.8), (r0 * 0.6, -L * 0.4), (r0 * 0.85, -L * 0.12), (r0, 0.0)]
        t = lathe(prof, 6, cap_top=True)
        jitter(t, r, r0 * 0.1)
        k.put(t, "BH_Ice", M=TRS(x, r.uniform(-0.22, -0.07), -0.17, r.uniform(-4, 4), r.uniform(-4, 4), 0),
              tint=r.uniform(0.8, 1.0), smooth=40)
    return dict(recenter=False)


@asset("frozen_coffin", "rime")
def frozen_coffin(k):
    r = k.r
    outer = [(-1.0, -0.3), (0.45, -0.42), (1.0, -0.3), (1.0, 0.3), (0.45, 0.42), (-1.0, 0.3)]
    k.put(extrude_xy([(x * 1.06, y * 1.12) for x, y in outer], 0.1), "BH_StoneDark", tint=0.8)
    k.put(extrude_xy(outer, 0.14, 0.1), "BH_Stone", tint=0.85)
    inner = [(x * 0.9, y * 0.72) for x, y in outer]
    n = len(outer)
    for i in range(n):
        j = (i + 1) % n
        c = [(*outer[i], 0.24), (*outer[j], 0.24), (*inner[j], 0.24), (*inner[i], 0.24),
             (*outer[i], 0.62), (*outer[j], 0.62), (*inner[j], 0.62), (*inner[i], 0.62)]
        t = hexa(c, 0.02)
        chip(t, r, 1, 0.04)
        k.put(t, "BH_Stone", tint=r.uniform(0.8, 0.95))
    for sy in (-1, 1):
        for x in (-0.55, 0.1):
            k.put(box(0.4, 0.02, 0.18), "BH_StoneDark", M=T(x, sy * (0.33 if x < 0 else 0.4), 0.43), tint=0.5)
    # dark armoured figure lying head toward +X
    z0 = 0.24
    k.put(ico(0.13, 2), "BH_Iron", M=TRS(0.72, 0, z0 + 0.13, s=(1, 0.95, 0.9)), tint=0.6, smooth=50)
    k.put(box(0.1, 0.2, 0.05), "BH_StoneDark", M=T(0.8, 0, z0 + 0.22), tint=0.1)
    k.put(box(0.5, 0.36, 0.2, bev=0.05), "BH_Iron", M=T(0.33, 0, z0 + 0.12), tint=0.55)
    for sy in (-1, 1):
        k.put(tube([(0.5, sy * 0.2, z0 + 0.14), (0.25, sy * 0.16, z0 + 0.22), (0.12, sy * 0.03, z0 + 0.25)], 0.05, 6),
              "BH_Iron", tint=0.5, smooth=40)
        k.put(tube([(0.05, sy * 0.1, z0 + 0.1), (-0.4, sy * 0.1, z0 + 0.1), (-0.8, sy * 0.09, z0 + 0.09)], [0.08, 0.065, 0.05],
                   6), "BH_Cloth", tint=0.25, smooth=40)
    k.put(box(0.95, 0.05, 0.02), "BH_Metal", M=T(-0.35, 0, z0 + 0.26), tint=0.5)
    k.put(box(0.05, 0.2, 0.03), "BH_Iron", M=T(0.12, 0, z0 + 0.27))
    # ice mass (legs + head end), leaving the chest and face exposed; crystals on the rim
    for (x, y, sx, sy_, sz) in ((-0.62, 0, 0.36, 0.26, 0.4), (-0.2, 0.17, 0.18, 0.1, 0.34), (0.3, -0.24, 0.16, 0.08, 0.36),
                                (0.93, 0, 0.08, 0.22, 0.4)):
        t = rock(r, (sx, sy_, sz), cuts=7, subd=2, noise_amp=0.03, seed_off=x * 7)
        k.put(t, "BH_Ice", M=T(x, y, 0.2), tint=r.uniform(0.8, 1.0), smooth=30)
    for i in range(9):
        p = r.choice(outer)
        crystal(k, (p[0] * 0.9, p[1] * 0.85, 0.5), Vector((p[0] * 0.3, p[1], 1.2)).normalized(), r.uniform(0.2, 0.45),
                r.uniform(0.04, 0.07))
    t = ico(1.0, 2)
    for v in t.verts:
        v.co = Vector((v.co.x * 1.15, v.co.y * 0.55, max(v.co.z, -0.02) * 0.05))
    k.put(t, "BH_Snow", tint=0.9, smooth=50)
    k.col_box(2.15, 1.0, 0.8, T(0, 0, 0.4))
    return dict(recenter=False)


@asset("snow_drift", "rime", col=False)
def snow_drift(k):
    r = k.r
    t = ico(1.0, 3)
    for v in t.verts:
        x, y, z = v.co
        zz = max(z, 0.0) * (0.5 if x < 0 else lerp(0.5, 0.25, x))
        v.co = Vector((x * 1.5, y * 1.05, zz - 0.02))
    ndisp(t, 1.1, 0.14, k.noff, zmin=-0.02)
    ndisp(t, 4.0, 0.03, k.noff * 2, zmin=-0.02)
    k.put(t, "BH_Snow", tint=0.95, smooth=50)
    for i in range(3):
        a = r.uniform(0, math.tau)
        rock_piece(k, (r.uniform(0.2, 0.35),) * 2 + (0.3,), 80, pos=(math.cos(a) * 1.25, math.sin(a) * 0.8, 0.0),
                   moss=False, tint=(0.5, 0.7))
    return dict(recenter=False)


# ===============================================================================================================
# The Shattered Orrery
def band_ring(k, R_, w, th, gems=8, ticks=36):
    flat_ring(k, R_ - w, R_, -th / 2, th / 2, "BH_Brass", segs=48, tint=0.9)
    flat_ring(k, R_ - 0.012, R_ + 0.012, -th / 2 - 0.01, th / 2 + 0.01, "BH_Brass", segs=48, tint=0.7)
    for i in range(ticks):
        a = math.tau * i / ticks
        k.put(box(0.012, w * 0.5, th + 0.012), "BH_Brass", M=TRS(math.cos(a) * (R_ - w * 0.5), math.sin(a) * (R_ - w * 0.5),
                                                                   0, 0, 0, math.degrees(a) + 90), tint=0.5)
    for i in range(gems):
        a = math.tau * (i + 0.5) / gems
        k.put(ico(w * 0.3, 1), "BH_Starglass", M=TRS(math.cos(a) * (R_ - w * 0.5), math.sin(a) * (R_ - w * 0.5), 0,
                                                     s=(1, 1, 0.9)), tint=1.0)


@asset("armillary_sphere", "orrery")
def armillary_sphere(k):
    r = k.r
    C = 3.2
    for i, (rad, h) in enumerate(((1.25, 0.2), (1.05, 0.18), (0.85, 0.15))):
        t = cyl(rad, h, 8, bev=0.02)
        chip(t, r, 2, 0.04)
        k.put(t, "BH_Marble", M=T(0, 0, sum(x[1] for x in ((1.25, 0.2), (1.05, 0.18), (0.85, 0.15))[:i])), tint=0.95)
    z = 0.53
    k.put(lathe([(0.5, 0), (0.42, 0.15), (0.28, 0.35), (0.22, 1.0), (0.26, 1.2), (0.2, 1.3)], 12), "BH_Brass", M=T(0, 0, z),
          smooth=40)
    k.put(torus(0.3, 0.04, 16, 5), "BH_Brass", M=T(0, 0, z + 1.2))
    # static horizon ring on four struts + meridian cradle
    flat_ring(k, 1.82, 1.95, C - 0.04, C + 0.04, "BH_Brass", segs=56)
    for i in range(4):
        a = math.tau * i / 4 + math.pi / 4
        k.put(tube([(math.cos(a) * 0.22, math.sin(a) * 0.22, z + 1.25), (math.cos(a) * 1.1, math.sin(a) * 1.1, z + 1.7),
                    (math.cos(a) * 1.88, math.sin(a) * 1.88, C - 0.02)], 0.04, 6), "BH_Brass", smooth=40, tint=0.8)
        k.put(ico(0.07, 1), "BH_Brass", M=T(math.cos(a) * 1.88, math.sin(a) * 1.88, C + 0.05))
    k.put(cyl(0.05, C - 1.85 - z - 1.3 + 0.4, 6), "BH_Brass", M=T(0, 0, z + 1.2))
    subs = []
    for name, R_, w, rot in (("ring_a", 1.7, 0.12, (90, 0, 0)), ("ring_b", 1.42, 0.1, (90, 0, 60)),
                              ("ring_c", 1.15, 0.09, (23, 0, 0))):
        sub = kit.Kit(k.name + "_" + name)
        band_ring(sub, R_, w, 0.05)
        for sy in (-1, 1):  # pivot pins on the ring's local X axis
            sub.put(cyl(0.03, 0.12, 6), "BH_Brass", M=TRS(sy * (R_ + 0.05), 0, 0, 0, 90, 0) @ T(0, 0, -0.06))
        subs.append((name, sub, (0, 0, C), rot))
    core = kit.Kit(k.name + "_core")
    core.put(ico(0.3, 2), "BH_Starglass", tint=1.0, smooth=None)
    for i in range(8):
        d = rand_unit(core.r)
        core.put(cyl(0.07, 0.25, 4, r2=0.0), "BH_Starglass", M=align_z(d) @ T(0, 0, 0.22))
    subs.append(("core", core, (0, 0, C), (0, 0, 0)))
    attach_children(k, subs)
    k.sockets.append(("light", (0, 0, C)))
    k.col_mesh(cyl(1.25, 1.8, 8))
    return dict(recenter=False)


@asset("crystal_pylon", "orrery")
def crystal_pylon(k):
    r = k.r
    k.put(cyl(0.75, 0.18, 8, bev=0.02), "BH_Marble", tint=0.95)
    k.put(cyl(0.55, 0.35, 8, bev=0.02), "BH_Brass", M=T(0, 0, 0.18), tint=0.85)
    for z in (0.2, 0.5):
        k.put(torus(0.57, 0.025, 8, 4), "BH_Brass", M=TRS(0, 0, z, 0, 0, 22.5))
    for i in range(8):
        a = math.tau * (i + 0.5) / 8
        k.put(box(0.12, 0.02, 0.12), "BH_Starglass", M=TRS(math.cos(a) * 0.5, math.sin(a) * 0.5, 0.35, 0, 0,
                                                           math.degrees(a) + 90))
    t = lathe([(0.0, 0.35), (0.3, 0.75), (0.32, 2.2), (0.0, 3.0)], 6)
    top = max(t.verts, key=lambda v: v.co.z)
    top.co.x += 0.05
    k.put(t, "BH_Starglass", tint=1.0)
    for i in range(4):
        a = math.tau * i / 4
        k.put(tube([(math.cos(a) * 0.5, math.sin(a) * 0.5, 0.5), (math.cos(a) * 0.52, math.sin(a) * 0.52, 0.9),
                    (math.cos(a) * 0.36, math.sin(a) * 0.36, 1.25), (math.cos(a) * 0.3, math.sin(a) * 0.3, 1.35)],
                   [0.05, 0.045, 0.035, 0.02], 6), "BH_Brass", smooth=40)
    k.put(torus(0.34, 0.03, 12, 4), "BH_Brass", M=T(0, 0, 1.25))
    for i in range(4):
        a = r.uniform(0, math.tau)
        crystal(k, (math.cos(a) * 0.62, math.sin(a) * 0.62, 0.15), Vector((math.cos(a) * 0.5, math.sin(a) * 0.5, 1)),
                r.uniform(0.25, 0.5), 0.05, mat="BH_Starglass")
    k.sockets.append(("light", (0, 0, 1.8)))
    k.col_mesh(cyl(0.6, 3.0, 8))
    return dict(recenter=False)


@asset("star_lens_disc", "orrery", col=False)
def star_lens_disc(k):
    r = k.r
    k.put(cyl(3.0, 0.02, 64), "BH_StoneDark", tint=0.3)
    for rin, rout in ((2.72, 3.0), (1.45, 1.55), (0.45, 0.55)):
        flat_ring(k, rin, rout, 0.0, 0.035, "BH_Brass", segs=64)
    for i in range(72):
        a = math.tau * i / 72
        L = 0.12 if i % 6 else 0.22
        k.put(box(L, 0.018, 0.01), "BH_Brass", M=TRS(math.cos(a) * (2.72 - L / 2 - 0.02), math.sin(a) * (2.72 - L / 2 - 0.02),
                                                        0.025, 0, 0, math.degrees(a)), tint=0.8)
    for i in range(12):
        a = math.tau * i / 12
        k.put(box(0.9, 0.03, 0.012), "BH_Brass", M=TRS(math.cos(a) * 1.0, math.sin(a) * 1.0, 0.026, 0, 0, math.degrees(a)))
        k.put(cyl(0.05, 0.012, 6), "BH_Starglass", M=T(math.cos(a + 0.26) * 1.0, math.sin(a + 0.26) * 1.0, 0.02))
    star = []
    for i in range(16):
        rr = 0.42 if i % 2 == 0 else 0.13
        a = math.tau * i / 16
        star.append((math.cos(a) * rr, math.sin(a) * rr))
    k.put(extrude_xy(star, 0.02, 0.02), "BH_Starglass")
    for c in range(6):
        a0 = math.tau * c / 6 + r.uniform(-0.2, 0.2)
        pts = []
        for s in range(r.randint(4, 6)):
            a = a0 + r.uniform(-0.38, 0.38)
            d = r.uniform(1.75, 2.5)
            pts.append(Vector((math.cos(a) * d, math.sin(a) * d, 0.025)))
        pts.sort(key=lambda p: math.atan2(p.y, p.x))
        for p in pts:
            k.put(cyl(r.uniform(0.04, 0.07), 0.015, 6), "BH_Starglass", M=T(p.x, p.y, 0.02))
        for p, q in zip(pts, pts[1:]):
            d = q - p
            k.put(box(d.length, 0.018, 0.008), "BH_Starglass", M=TRS((p.x + q.x) / 2, (p.y + q.y) / 2, 0.028, 0, 0,
                                                                      math.degrees(math.atan2(d.y, d.x))))
    return dict(recenter=False)


@asset("brass_telescope", "orrery")
def brass_telescope(k):
    r = k.r
    head = Vector((0, 0, 1.5))
    for i in range(3):
        a = math.tau * i / 3 + math.pi / 2
        foot = Vector((math.cos(a) * 0.85, math.sin(a) * 0.85, 0.0))
        bar(k, foot, head, 0.04, "BH_WoodDark", segs=6, r2=0.03)
        k.put(cyl(0.05, 0.08, 6), "BH_Brass", M=T(*foot))
        mid = foot.lerp(head, 0.35)
        b = Vector((math.cos(a + math.tau / 3) * 0.85, math.sin(a + math.tau / 3) * 0.85, 0)).lerp(head, 0.35)
        bar(k, mid, b, 0.012, "BH_Brass", segs=4)
    k.put(cyl(0.14, 0.15, 10), "BH_Brass", M=T(0, 0, 1.45), smooth=40)
    for sy in (-1, 1):
        k.put(box(0.12, 0.03, 0.34, bev=0.01), "BH_Brass", M=T(0, sy * 0.17, 1.72))
    P = T(0, 0, 1.78) @ R(0, 0, -30) @ R(0, 50, 0)
    k.put(cyl(0.025, 0.4, 8), "BH_Brass", M=T(0, 0, 1.78) @ R(0, 0, -30) @ R(90, 0, 0) @ T(0, 0, -0.2))
    for (s0, s1, rad) in ((-0.55, 0.9, 0.13), (0.9, 1.55, 0.11), (1.55, 1.95, 0.16)):
        k.put(cyl(rad, s1 - s0, 16), "BH_Brass", M=P @ T(0, 0, s0), smooth=40, tint=r.uniform(0.75, 0.95))
        k.put(torus(rad + 0.005, 0.018, 16, 4), "BH_Brass", M=P @ T(0, 0, s0), tint=0.6)
    k.put(cyl(0.14, 0.02, 16), "BH_Starglass", M=P @ T(0, 0, 1.9))
    k.put(cyl(0.045, 0.2, 8), "BH_Brass", M=P @ T(0, 0, -0.75), smooth=40)
    k.put(cyl(0.05, 0.6, 8), "BH_Brass", M=P @ T(0.2, 0, 0.1), smooth=40)
    for s in (0.2, 0.6):
        k.put(box(0.1, 0.03, 0.03), "BH_Brass", M=P @ T(0.13, 0, s))
    k.put(cyl(0.02, 0.45, 6), "BH_Brass", M=T(0, 0, 1.78) @ R(0, 0, -30) @ R(0, 180, 0))
    k.put(ico(0.11, 2), "BH_Brass", M=T(0, 0, 1.3), smooth=40)
    k.col_mesh(cyl(0.8, 1.8, 6))
    return dict(recenter=False)


@asset("floating_rock", "orrery", col=False)
def floating_rock(k):
    """Hovering island chunk; origin bottom-centre (crystal tips), socket `center` at the rock's middle."""
    r = k.r
    t = rock(r, (1.0, 0.85, 1.3), cuts=10, subd=3, noise_amp=0.06, seed_off=4.0)
    taper_z(t, 0.0, 1.0, 1.0, 0.3)
    t = decimate(t, min(1.0, 700 / len(t.faces)))
    M = T(0, 0, 2.0) @ S(1, 1, -1)
    under = surf_pts(t, M, 14, r, cond=lambda c, n: n.z < -0.2 and c.z < 1.7)
    k.put(t, "BH_Stone", M=M, tint=0.75, smooth=38, mat_fn=moss_fn(k, 0.8, 1.2, 0.3))
    for i, (p, n) in enumerate(under):
        crystal(k, p - n * 0.05, (n + Vector((0, 0, -1.2))).normalized(), r.uniform(0.3, 0.75), r.uniform(0.06, 0.12),
                mat="BH_Starglass")
    slab_floor(k, 1.0, 0.8, 2.02, th=0.06, mat="BH_Marble", missing=0.3, crack_p=0.3)
    k.sockets.append(("center", (0, 0, 1.4)))
    return dict()


# ===============================================================================================================
# shared dungeon pieces
@asset("stairs_wood", "dungeon")
def stairs_wood(k):
    """Same footprint/collision convention as `stairs`: 4 m run along +Y (y -2..2), rise 0 -> 2 m, 10 treads of 0.2 m."""
    r = k.r
    n, rise, run, W = 10, 0.2, 0.4, 2.4
    sw = 0.08
    for i in range(n):
        y0 = -2 + run * i
        for j in range(2):
            plank(k, W - 2 * sw + 0.02, run / 2 - 0.01, 0.05,
                  TRS(0, y0 + run / 4 + j * run / 2, rise * (i + 1) - 0.025, 0, 0, r.uniform(-0.4, 0.4)), tint=(0.65, 1.0))
        for sx in (-1, 1):
            rivet(k, TRS(sx * (W / 2 + 0.002), y0 + run / 2, rise * (i + 1) - 0.06, 0, sx * 90, 0), 0.02)
    outline = [(-2.0, 0.0), (-1.4, 0.0), (2.0, 1.7), (2.0, 2.3), (-2.0, 0.3)]
    for sx in (-1, 1):
        t = prism(outline, sw, bev=0.01)
        jitter(t, r, 0.004)
        k.put(t, "BH_WoodDark", M=T(sx * (W / 2 - sw / 2), 0, 0) @ R(0, 0, 90), tint=0.8)
    t = prism([(-1.7, 0.0), (-1.2, 0.0), (2.0, 1.6), (2.0, 1.85), (-1.7, 0.2)], 0.1)
    k.put(t, "BH_WoodDark", M=R(0, 0, 90), tint=0.6)
    # rails: posts on both stringers + handrail and mid rail along the slope
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.04)
        ys = (-1.85, -0.6, 0.65, 1.9)
        tops = []
        for y in ys:
            zb = 0.3 + 0.5 * (y + 2) - 0.25
            zt = 0.2 + 0.5 * (y + 2) + 0.95
            k.put(box(0.08, 0.08, zt - zb, bev=0.01), "BH_WoodDark", M=T(x, y, (zb + zt) / 2), tint=r.uniform(0.6, 0.8))
            tops.append(Vector((x, y, zt)))
        bar(k, tops[0] + Vector((0, 0, -0.02)), tops[-1] + Vector((0, 0, -0.02)), 0.07, "BH_Wood", h=0.06)
        bar(k, tops[0] + Vector((0, 0, -0.5)), tops[-1] + Vector((0, 0, -0.5)), 0.05, "BH_Wood", h=0.04)
        for tp in tops:
            k.put(box(0.1, 0.1, 0.04), "BH_Iron", M=T(tp.x, tp.y, tp.z - 0.2))
    k.col_mesh(box(W, math.hypot(4, 2), 0.2), TRS(0, 0, 1.0 - 0.1, math.degrees(math.atan2(2, 4)), 0, 0))
    k.col_box(0.2, 4, 3.0, T(-(W / 2 + 0.04), 0, 1.5))
    k.col_box(0.2, 4, 3.0, T(W / 2 + 0.04, 0, 1.5))
    return dict(recenter=False)


@asset("gallery_railing", "dungeon")
def gallery_railing(k):
    r = k.r
    L, D = 4.0, 0.34
    for z0, h, dd in ((0.0, 0.14, D), (0.84, 0.14, D + 0.04)):
        ws, _ = split_lengths(r, L, 0.9, 1.6)
        x = -L / 2
        for w in ws:
            t = box(w - 0.02, dd, h, bev=0.025)
            chip(t, r, r.randint(0, 2), 0.04)
            jitter(t, r, 0.004)
            k.put(t, "BH_Stone", M=T(x + w / 2, 0, z0 + h / 2), tint=r.uniform(0.85, 1.0))
            x += w
    for sx in (-1, 1):
        t = box(0.34, 0.38, 0.84, bev=0.03)
        chip(t, r, 2, 0.04)
        k.put(t, "BH_Stone", M=T(sx * 1.82, 0, 0.42), tint=0.95)
        k.put(box(0.42, 0.44, 0.08, bev=0.02), "BH_Stone", M=T(sx * 1.82, 0, 1.02), tint=0.9)
    prof = [(0.07, 0.0), (0.07, 0.04), (0.05, 0.08), (0.06, 0.2), (0.09, 0.35), (0.075, 0.48), (0.045, 0.58),
            (0.05, 0.64), (0.07, 0.66), (0.07, 0.7)]
    for i in range(10):
        x = -1.575 + i * 0.35
        t = lathe(prof, 10)
        if r.random() < 0.3:
            chip(t, r, 1, 0.03)
        k.put(t, "BH_Stone", M=T(x, 0, 0.14), tint=r.uniform(0.8, 0.95), smooth=50)
    streaks(k, -2, 2, 1.0)
    k.col_box(L, 0.4, 1.06, T(0, 0, 0.53))
    return dict(recenter=False, damp=0.25, damp_h=0.5)
