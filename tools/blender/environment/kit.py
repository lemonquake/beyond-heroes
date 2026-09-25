"""Beyond Heroes environment modeling toolkit (Blender 5.2 bpy/bmesh).

Pattern: every primitive is built in its own temporary bmesh in *local* space (``tb()``), optionally
roughened (chips, jitter, noise), then ``Kit.put`` gives it box/explicit UVs, a vertex tint and a material,
transforms it and appends it to the asset's bmesh. ``Kit.finish`` turns the asset into one mesh object
(origin bottom-centre), optional ``<name>-colonly`` collision child, and the exporter writes a GLB.

Deterministic: each asset gets ``random.Random(crc32(name))`` and a fixed mathutils noise seed.
"""
import math
import random
import zlib

import bmesh
import bpy
from mathutils import Matrix, Vector, Euler, noise as mnoise

# ---------------------------------------------------------------------------------------------------------------
# Materials (contract names). Values are plausible Blender colours (linear) used for export; the render
# scripts swap in textured versions.
MATERIALS = {
    #  name            base colour (linear)          rough metal  emission (colour, strength)
    "BH_Stone":       ((0.30, 0.285, 0.26, 1), 0.85, 0.0, None),
    "BH_StoneDark":   ((0.13, 0.125, 0.12, 1), 0.9, 0.0, None),
    "BH_Brick":       ((0.25, 0.10, 0.07, 1), 0.88, 0.0, None),
    "BH_Cobble":      ((0.20, 0.19, 0.18, 1), 0.8, 0.0, None),
    "BH_Wood":        ((0.20, 0.12, 0.065, 1), 0.8, 0.0, None),
    "BH_WoodDark":    ((0.085, 0.055, 0.035, 1), 0.82, 0.0, None),
    "BH_Bark":        ((0.06, 0.045, 0.035, 1), 0.92, 0.0, None),
    "BH_Leaves":      ((0.06, 0.10, 0.03, 1), 0.7, 0.0, None),
    "BH_Grass":       ((0.07, 0.11, 0.03, 1), 0.8, 0.0, None),
    "BH_Moss":        ((0.05, 0.08, 0.018, 1), 0.95, 0.0, None),
    "BH_Metal":       ((0.35, 0.34, 0.33, 1), 0.45, 1.0, None),
    "BH_Iron":        ((0.06, 0.058, 0.058, 1), 0.6, 1.0, None),
    "BH_Gold":        ((0.62, 0.42, 0.14, 1), 0.35, 1.0, None),
    "BH_Cloth":       ((0.22, 0.18, 0.13, 1), 0.95, 0.0, None),
    "BH_ClothRed":    ((0.22, 0.03, 0.025, 1), 0.92, 0.0, None),
    "BH_Bone":        ((0.55, 0.50, 0.40, 1), 0.7, 0.0, None),
    "BH_Candle":      ((0.62, 0.55, 0.40, 1), 0.5, 0.0, None),
    "BH_Flame":       ((1.0, 0.45, 0.1, 1), 0.5, 0.0, ((1.0, 0.45, 0.12), 12.0)),
    "BH_Rune":        ((0.2, 0.75, 0.9, 1), 0.4, 0.0, ((0.25, 0.8, 1.0), 6.0)),
    "BH_Corruption":  ((0.35, 0.08, 0.5, 1), 0.4, 0.0, ((0.55, 0.12, 0.9), 6.0)),
    "BH_Water":       ((0.03, 0.18, 0.2, 1), 0.05, 0.0, None),
    "BH_Glass":       ((0.5, 0.6, 0.6, 1), 0.05, 0.0, None),
    "BH_Thatch":      ((0.25, 0.19, 0.08, 1), 0.92, 0.0, None),
    "BH_Dirt":        ((0.12, 0.08, 0.05, 1), 0.93, 0.0, None),
}
MATERIAL_NAMES = list(MATERIALS.keys())


def get_mat(name):
    assert name in MATERIALS, name
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    col, rough, metal, emis = MATERIALS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = col
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emis:
        bsdf.inputs["Emission Color"].default_value = (*emis[0], 1)
        bsdf.inputs["Emission Strength"].default_value = emis[1]
    if name in ("BH_Water", "BH_Glass"):
        bsdf.inputs["Alpha"].default_value = 0.6 if name == "BH_Water" else 0.35
    return m


# ---------------------------------------------------------------------------------------------------------------
# small math helpers
def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def R(rx=0.0, ry=0.0, rz=0.0):
    """Rotation from Euler XYZ in degrees."""
    return Euler((math.radians(rx), math.radians(ry), math.radians(rz)), "XYZ").to_matrix().to_4x4()


def S(x, y=None, z=None):
    if y is None:
        y = z = x
    m = Matrix.Identity(4)
    m[0][0], m[1][1], m[2][2] = x, y, z
    return m


def TRS(x=0, y=0, z=0, rx=0, ry=0, rz=0, s=1.0):
    ss = S(*s) if isinstance(s, (tuple, list)) else S(s)
    return T(x, y, z) @ R(rx, ry, rz) @ ss


def lerp(a, b, t):
    return a + (b - a) * t


def sstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def seed_of(name):
    return zlib.crc32(name.encode("utf8")) & 0x7FFFFFFF


# ---------------------------------------------------------------------------------------------------------------
# temp bmesh primitives (local space)
def tb():
    t = bmesh.new()
    t.loops.layers.uv.new("UVMap")
    t.loops.layers.float_color.new("Col")
    return t


def _bevel(t, bev, seg=1, verts_only=False):
    if bev and bev > 0:
        bmesh.ops.bevel(t, geom=list(t.verts) + list(t.edges), offset=bev, offset_type="OFFSET",
                        segments=seg, profile=0.5, affect="EDGES", clamp_overlap=True)
    return t


def box(sx, sy, sz, bev=0.0, seg=1, base=False):
    """Axis-aligned box centred at origin (or with its bottom at z=0 when base=True)."""
    t = tb()
    bmesh.ops.create_cube(t, size=1.0)
    for v in t.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz + (sz / 2 if base else 0)))
    b = min(bev, sx * 0.45, sy * 0.45, sz * 0.45) if bev else 0
    return _bevel(t, b, seg)


def hexa(c, bev=0.0, seg=1):
    """Block from 8 corners: c[0:4] bottom ring CCW (seen from +Z), c[4:8] top ring above them."""
    t = tb()
    vs = [t.verts.new(Vector(p)) for p in c]
    b0, b1, b2, b3, t0, t1, t2, t3 = vs
    for f in ((b3, b2, b1, b0), (t0, t1, t2, t3), (b0, b1, t1, t0), (b1, b2, t2, t1), (b2, b3, t3, t2),
              (b3, b0, t0, t3)):
        t.faces.new(f)
    bmesh.ops.recalc_face_normals(t, faces=t.faces)
    return _bevel(t, bev, seg)


def prism(outline_xz, depth, bev=0.0, seg=1):
    """Extrude a 2D outline given in the XZ plane (CCW seen from -Y) through Y in [-depth/2, depth/2]."""
    t = tb()
    n = len(outline_xz)
    front = [t.verts.new((x, -depth / 2, z)) for x, z in outline_xz]
    back = [t.verts.new((x, depth / 2, z)) for x, z in outline_xz]
    t.faces.new(front)
    t.faces.new(back[::-1])
    for i in range(n):
        j = (i + 1) % n
        t.faces.new((front[i], back[i], back[j], front[j]))
    bmesh.ops.recalc_face_normals(t, faces=t.faces)
    return _bevel(t, bev, seg)


def cyl(r, h, segs=12, r2=None, bev=0.0, seg=1, caps=True):
    t = tb()
    bmesh.ops.create_cone(t, cap_ends=caps, cap_tris=False, segments=segs, radius1=r,
                          radius2=r if r2 is None else r2, depth=h, matrix=T(0, 0, h / 2))
    return _bevel(t, bev, seg) if bev else t


def ico(r, subdiv=2):
    t = tb()
    bmesh.ops.create_icosphere(t, subdivisions=subdiv, radius=r)
    return t


def lathe(profile, segs=16, cap_bot=True, cap_top=True, uv_tile=1.0, angle0=0.0, arc=None):
    """Revolve a (radius, z) profile (bottom to top) around Z. Cylindrical UVs (u = arc length / uv_tile)."""
    t = tb()
    uvl = t.loops.layers.uv.active
    full = arc is None
    arc = arc if arc is not None else 2 * math.pi
    ncol = segs if full else segs + 1
    rings = []
    for (r, z) in profile:
        ring = []
        for i in range(ncol):
            a = angle0 + arc * i / segs
            ring.append(t.verts.new((math.cos(a) * r, math.sin(a) * r, z)))
        rings.append(ring)
    # cumulative profile length for v
    vacc = [0.0]
    for k in range(1, len(profile)):
        dr = profile[k][0] - profile[k - 1][0]
        dz = profile[k][1] - profile[k - 1][1]
        vacc.append(vacc[-1] + math.hypot(dr, dz))
    rmax = max(p[0] for p in profile)
    circ = arc * rmax
    for k in range(len(profile) - 1):
        for i in range(segs):
            i2 = (i + 1) % ncol if full else i + 1
            f = t.faces.new((rings[k][i], rings[k][i2], rings[k + 1][i2], rings[k + 1][i]))
            us = (i / segs * circ / uv_tile, (i + 1) / segs * circ / uv_tile)
            vs = (vacc[k] / uv_tile, vacc[k + 1] / uv_tile)
            for l, (u, v) in zip(f.loops, ((us[0], vs[0]), (us[1], vs[0]), (us[1], vs[1]), (us[0], vs[1]))):
                l[uvl].uv = (u, v)
    if full:
        for k, flag in ((0, cap_bot), (len(profile) - 1, cap_top)):
            if flag and profile[k][0] > 1e-5:
                ring = rings[k] if k else rings[k][::-1]
                f = t.faces.new(ring)
                for l in f.loops:
                    l[uvl].uv = (l.vert.co.x / uv_tile * 0.5 + 0.5, l.vert.co.y / uv_tile * 0.5 + 0.5)
    bmesh.ops.remove_doubles(t, verts=t.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(t, faces=t.faces)
    return t


def _frames(pts):
    """Parallel-transport frames along a polyline."""
    tans = []
    for i in range(len(pts)):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        d = (b - a)
        tans.append(d.normalized() if d.length > 1e-9 else Vector((0, 0, 1)))
    up = Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0))
    n = tans[0].cross(up).normalized()
    frames = []
    for i, tg in enumerate(tans):
        if i:
            n = n - tg * n.dot(tg)
            if n.length < 1e-6:
                n = tg.orthogonal()
            n.normalize()
        b = tg.cross(n).normalized()
        frames.append((tg, n, b))
    return frames


def tube(points, radii, segs=8, cap_start=True, cap_end=True, closed=False, uv_tile=1.0, flat=None):
    """Generalised cylinder along a polyline. radii: float or list. flat: optional (sx, sy) ellipse scale."""
    t = tb()
    uvl = t.loops.layers.uv.active
    pts = [Vector(p) for p in points]
    if isinstance(radii, (int, float)):
        radii = [radii] * len(pts)
    fr = _frames(pts + ([pts[0], pts[1]] if closed else []))[:len(pts)]
    rings = []
    for p, r, (tg, n, b) in zip(pts, radii, fr):
        ring = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            sx, sy = flat if flat else (1, 1)
            ring.append(t.verts.new(p + (n * math.cos(a) * sx + b * math.sin(a) * sy) * r))
        rings.append(ring)
    L = [0.0]
    for i in range(1, len(pts)):
        L.append(L[-1] + (pts[i] - pts[i - 1]).length)
    nseg = len(pts) if closed else len(pts) - 1
    for k in range(nseg):
        k2 = (k + 1) % len(pts)
        rr = (radii[k] + radii[k2]) * 0.5
        for i in range(segs):
            i2 = (i + 1) % segs
            f = t.faces.new((rings[k][i], rings[k][i2], rings[k2][i2], rings[k2][i]))
            u0, u1 = i / segs * 2 * math.pi * rr / uv_tile, (i + 1) / segs * 2 * math.pi * rr / uv_tile
            v0 = L[k] / uv_tile
            v1 = (L[k2] if k2 else L[-1] + (pts[0] - pts[-1]).length) / uv_tile
            for l, uv in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
                l[uvl].uv = uv
    if not closed:
        if cap_start and radii[0] > 1e-5:
            t.faces.new(rings[0][::-1])
        if cap_end and radii[-1] > 1e-5:
            t.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(t, faces=t.faces)
    return t


def torus(R_, r, segs=16, rsegs=6):
    pts = [(math.cos(2 * math.pi * i / segs) * R_, math.sin(2 * math.pi * i / segs) * R_, 0) for i in range(segs)]
    return tube(pts, r, rsegs, closed=True)


def card(w, h, uv=(0, 0, 1, 1), bend=0.0, rows=1):
    """Vertical quad strip in the XZ plane, bottom centre at origin, facing -Y. uv rect = (u0, v0, u1, v1).
    bend > 0 curls the top toward -Y (grass/fern droop)."""
    t = tb()
    uvl = t.loops.layers.uv.active
    vs = []
    for k in range(rows + 1):
        s = k / rows
        y = -bend * s * s
        vs.append((t.verts.new((-w / 2, y, h * s)), t.verts.new((w / 2, y, h * s))))
    for k in range(rows):
        f = t.faces.new((vs[k][0], vs[k][1], vs[k + 1][1], vs[k + 1][0]))
        v0 = uv[1] + (uv[3] - uv[1]) * k / rows
        v1 = uv[1] + (uv[3] - uv[1]) * (k + 1) / rows
        for l, c in zip(f.loops, ((uv[0], v0), (uv[2], v0), (uv[2], v1), (uv[0], v1))):
            l[uvl].uv = c
    return t


def flat_poly(pts_xy, z=0.0):
    t = tb()
    t.faces.new([t.verts.new((x, y, z)) for x, y in pts_xy])
    return t


# ---------------------------------------------------------------------------------------------------------------
# roughening
def chip(t, r, n=2, depth=0.05, spread=0.35):
    """Cut n random corners off with planes (clean chipped facets), keeping the mesh closed."""
    if not t.verts:
        return t
    for _ in range(n):
        vs = list(t.verts)
        mn = Vector((min(v.co.x for v in vs), min(v.co.y for v in vs), min(v.co.z for v in vs)))
        mx = Vector((max(v.co.x for v in vs), max(v.co.y for v in vs), max(v.co.z for v in vs)))
        ctr = (mn + mx) * 0.5
        corner = Vector((r.choice((mn.x, mx.x)), r.choice((mn.y, mx.y)), r.choice((mn.z, mx.z))))
        d = (corner - ctr)
        no = Vector((d.x * r.uniform(1 - spread, 1 + spread), d.y * r.uniform(1 - spread, 1 + spread),
                     d.z * r.uniform(1 - spread, 1 + spread))).normalized()
        far = max(v.co.dot(no) for v in t.verts)
        co = no * (far - depth * r.uniform(0.6, 1.3))
        res = bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), dist=1e-5,
                                     plane_co=co, plane_no=no, clear_outer=True)
        edges = [e for e in t.edges if e.is_boundary]
        if edges:
            bmesh.ops.holes_fill(t, edges=edges, sides=0)
    bmesh.ops.recalc_face_normals(t, faces=t.faces)
    return t


def slice_plane(t, co, no):
    """Remove everything on the +no side of a plane and cap it."""
    bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), dist=1e-5,
                           plane_co=Vector(co), plane_no=Vector(no).normalized(), clear_outer=True)
    edges = [e for e in t.edges if e.is_boundary]
    if edges:
        bmesh.ops.holes_fill(t, edges=edges, sides=0)
    bmesh.ops.recalc_face_normals(t, faces=t.faces)
    return t


def jitter(t, r, amt, axes=(1, 1, 1)):
    for v in t.verts:
        v.co += Vector((r.uniform(-amt, amt) * axes[0], r.uniform(-amt, amt) * axes[1],
                        r.uniform(-amt, amt) * axes[2]))
    return t


def ndisp(t, scale, amp, off=(0, 0, 0), octaves=3, along_normal=True, zmin=None):
    """Displace verts with fractal noise (deterministic: mathutils noise is seedless for noise())."""
    t.normal_update()
    o = Vector(off)
    for v in t.verts:
        p = v.co * scale + o
        d = mnoise.fractal(p, 0.5, 2.0, octaves, noise_basis="PERLIN_ORIGINAL")
        if zmin is not None and v.co.z <= zmin + 1e-4:
            continue
        v.co += (v.normal if along_normal else Vector((0, 0, 1))) * d * amp
    return t


def subdiv(t, cuts=1, smooth=0.0):
    bmesh.ops.subdivide_edges(t, edges=list(t.edges), cuts=cuts, use_grid_fill=True, smooth=smooth)
    return t


def taper_z(t, z0, z1, s0, s1):
    for v in t.verts:
        k = lerp(s0, s1, sstep(z0, z1, v.co.z) if z1 != z0 else 0)
        v.co.x *= k
        v.co.y *= k
    return t


def decimate(t, ratio):
    """Collapse-decimate a temp bmesh via a throwaway object + modifier (keeps UV/colour layers)."""
    me = bpy.data.meshes.new("_dec")
    t.to_mesh(me)
    ob = bpy.data.objects.new("_dec", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("d", "DECIMATE")
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m2 = ev.to_mesh()
    out = tb()
    out.from_mesh(m2)
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    t.free()
    return out


def rock(r, size=(1, 1, 1), cuts=9, subd=2, noise_amp=0.06, seed_off=0.0, flat_bottom=True, target=None):
    """Faceted boulder: icosphere -> random plane cuts (big planar facets) -> subdivide -> noise -> decimate."""
    t = ico(1.0, subd)
    for v in t.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    for _ in range(cuts):
        a = r.uniform(0, 2 * math.pi)
        el = r.uniform(-0.3, 1.0)
        no = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
        far = max(v.co.dot(no) for v in t.verts)
        co = no * far * r.uniform(0.72, 0.9)
        slice_plane(t, co, no)
    if flat_bottom:
        slice_plane(t, (0, 0, -size[2] * 0.45), (0, 0, -1))
    # remesh-ish: subdivide long faces then displace
    bmesh.ops.triangulate(t, faces=t.faces)
    bmesh.ops.subdivide_edges(t, edges=[e for e in t.edges if e.calc_length() > max(size) * 0.25], cuts=1,
                              use_grid_fill=False)
    bmesh.ops.triangulate(t, faces=t.faces)
    t.normal_update()
    o = Vector((seed_off * 3.1, seed_off * 1.7, seed_off * 2.3))
    zb = min(v.co.z for v in t.verts)
    for v in t.verts:
        d = mnoise.fractal(v.co * 1.3 / max(size) * 2 + o, 0.55, 2.0, 4, noise_basis="PERLIN_ORIGINAL")
        w = 0.0 if (flat_bottom and v.co.z <= zb + 1e-4) else 1.0
        v.co += v.normal * d * noise_amp * max(size) * w
    if target:
        n = len(t.faces)
        if n > target:
            t = decimate(t, target / n)
    for v in t.verts:
        v.co.z -= zb
    return t


# ---------------------------------------------------------------------------------------------------------------
def moss_fn(k, thresh=0.72, scale=1.2, bias=0.0, mat="BH_Moss"):
    """Per-face material function: upward faces with positive noise become moss."""
    o = k.noff

    def f(face):
        n = face.normal
        if n.z < thresh:
            return None
        c = face.calc_center_median()
        v = mnoise.noise(c * scale + o) + bias + (n.z - thresh) * 0.8
        return mat if v > 0.0 else None
    return f


def bm_copy(t):
    return t.copy()


def voronoi_clip(t, seeds, i):
    """Clip a closed temp bmesh to the Voronoi cell of seeds[i] (returns a new closed bmesh or None)."""
    c = t.copy()
    si = Vector(seeds[i])
    for j, sj in enumerate(seeds):
        if j == i:
            continue
        sj = Vector(sj)
        no = (sj - si).normalized()
        co = (si + sj) * 0.5
        if not c.verts:
            break
        if min(v.co.dot(no) for v in c.verts) > co.dot(no):
            c.free()
            return None
        slice_plane(c, co, no)
    if len(c.faces) < 4:
        c.free()
        return None
    return c


def box_uv(t, tile=2.0, off=(0.0, 0.0), rot=False):
    uvl = t.loops.layers.uv.active
    t.normal_update()
    for f in t.faces:
        n = f.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for l in f.loops:
            p = l.vert.co
            if az >= ax and az >= ay:
                u, v = p.x, p.y * (1 if n.z >= 0 else -1)
            elif ax >= ay:
                u, v = p.y * (1 if n.x >= 0 else -1), p.z
            else:
                u, v = -p.x * (1 if n.y >= 0 else -1), p.z
            if rot:
                u, v = v, u
            l[uvl].uv = (u / tile + off[0], v / tile + off[1])


def planar_uv(t, axis="z", tile=1.0, center=(0, 0), size=None):
    """Planar projection; with size=(w,h) maps the rect centred at `center` to 0..1."""
    uvl = t.loops.layers.uv.active
    for f in t.faces:
        for l in f.loops:
            p = l.vert.co
            a, b = (p.x, p.y) if axis == "z" else ((p.x, p.z) if axis == "y" else (p.y, p.z))
            if size:
                l[uvl].uv = ((a - center[0]) / size[0] + 0.5, (b - center[1]) / size[1] + 0.5)
            else:
                l[uvl].uv = (a / tile, b / tile)


def set_smooth(t, angle_deg):
    """angle None -> flat. Otherwise smooth with edges sharper than angle marked sharp."""
    if angle_deg is None:
        for f in t.faces:
            f.smooth = False
        return
    lim = math.radians(angle_deg)
    t.normal_update()
    for f in t.faces:
        f.smooth = True
    for e in t.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(0.0) <= lim
        else:
            e.smooth = False


# ---------------------------------------------------------------------------------------------------------------
class Kit:
    """Accumulates one asset."""

    def __init__(self, name):
        self.name = name
        self.seed = seed_of(name)
        self.r = random.Random(self.seed)
        self.noff = Vector(((self.seed % 997) * 0.137, (self.seed % 991) * 0.071, (self.seed % 983) * 0.053))
        self.bm = tb()
        self.mats = []
        self.cols = []  # collision pieces: temp bmeshes already transformed
        self._tmp = bpy.data.meshes.new("_kit_tmp")
        self.origin_mode = "bottom_center"
        self.groups = {}  # fragment groups: name -> bmesh
        self.color_post = None
        self.sockets = []  # (name, (x,y,z)) -> exported as child empties  # optional fn(world_co, (r,g,b)) -> (r,g,b) applied in finish()

    def mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def put(self, t, mat, M=None, uv="box", tile=2.0, tint=1.0, smooth=None, uvoff=True, rotuv=False,
            group=None, M2=None, mat_fn=None, main=True):
        """Finalize temp bmesh t (local space) and append it. uv: 'box' | 'keep' | 'planar_z'.
        tint: float or (r,g,b) vertex colour multiplier. smooth: None (flat) or crease angle in degrees."""
        if uv == "box":
            off = (self.r.random(), self.r.random()) if uvoff else (0, 0)
            box_uv(t, tile, off, rotuv)
        elif uv == "planar_z":
            planar_uv(t, "z", tile)
        cl = t.loops.layers.float_color.active
        tc = (tint, tint, tint) if isinstance(tint, (int, float)) else tint
        for f in t.faces:
            for l in f.loops:
                l[cl] = (tc[0], tc[1], tc[2], 1.0)
        set_smooth(t, smooth)
        idx = self.mi(mat)
        for f in t.faces:
            f.material_index = idx
        if M is not None:
            bmesh.ops.transform(t, matrix=M, verts=t.verts)
        if M2 is not None:
            bmesh.ops.transform(t, matrix=M2, verts=t.verts)
        if M is not None and M.determinant() < 0:
            bmesh.ops.reverse_faces(t, faces=t.faces)
        if mat_fn is not None:
            t.normal_update()
            for f in t.faces:
                m2 = mat_fn(f)
                if m2:
                    f.material_index = self.mi(m2)
        t.to_mesh(self._tmp)
        if main:
            self.bm.from_mesh(self._tmp)
        if group is not None:
            g = self.groups.get(group)
            if g is None:
                g = self.groups[group] = tb()
            # material index in group bmesh must follow self.mats order as well
            g.from_mesh(self._tmp)
        t.free()

    def col_box(self, sx, sy, sz, M=None, base=False):
        """Collision helper box."""
        t = box(sx, sy, sz, base=base)
        if M is not None:
            bmesh.ops.transform(t, matrix=M, verts=t.verts)
        self.cols.append(t)

    def col_mesh(self, t, M=None):
        if M is not None:
            bmesh.ops.transform(t, matrix=M, verts=t.verts)
        self.cols.append(t)

    # ---------------------------------------------------------------------------------------------------
    def _bm_to_obj(self, bm, name):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        for m in self.mats:
            me.materials.append(get_mat(m))
        if "Col" in me.color_attributes:
            me.color_attributes.active_color = me.color_attributes["Col"]
            me.color_attributes.render_color_index = me.color_attributes.find("Col")
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob

    def finish(self, recenter=True, damp=0.0, damp_h=0.8):
        """Create the object(s). recenter: shift so the bbox bottom-centre is at the origin.
        damp: darken vertex colour near the ground (0..1) over damp_h metres (rising damp)."""
        bm = self.bm
        shift = Vector((0, 0, 0))
        if recenter and bm.verts:
            xs = [v.co.x for v in bm.verts]
            ys = [v.co.y for v in bm.verts]
            zs = [v.co.z for v in bm.verts]
            shift = Vector((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs)))
        mats = [shift]
        for b in [bm] + self.cols + list(self.groups.values()):
            bmesh.ops.transform(b, matrix=T(*shift), verts=b.verts)
        if damp > 0:
            cl = bm.loops.layers.float_color.active
            for f in bm.faces:
                for l in f.loops:
                    k = 1.0 - damp * (1.0 - sstep(0.0, damp_h, l.vert.co.z))
                    c = l[cl]
                    l[cl] = (c[0] * k, c[1] * k, c[2] * k, 1.0)
        if self.color_post is not None:
            cl = bm.loops.layers.float_color.active
            for f in bm.faces:
                if self.mats[f.material_index] not in ("BH_Stone", "BH_StoneDark", "BH_Brick", "BH_Cobble"):
                    continue
                for l in f.loops:
                    c = l[cl]
                    c2 = self.color_post(l.vert.co - shift, (c[0], c[1], c[2]))
                    l[cl] = (c2[0], c2[1], c2[2], 1.0)
        ob = self._bm_to_obj(bm, self.name)
        if self.cols:
            cb = bmesh.new()
            for c in self.cols:
                c.to_mesh(self._tmp)
                cb.from_mesh(self._tmp)
            me = bpy.data.meshes.new(self.name + "-colonly")
            cb.to_mesh(me)
            co = bpy.data.objects.new(self.name + "-colonly", me)
            bpy.context.scene.collection.objects.link(co)
            co.parent = ob
        for (sn, loc) in self.sockets:
            e = bpy.data.objects.new(sn, None)
            e.empty_display_type = "SPHERE"
            e.empty_display_size = 0.1
            e.location = Vector(loc) + shift
            bpy.context.scene.collection.objects.link(e)
            e.parent = ob
        self.obj = ob
        return ob

    def finish_fragments(self, name):
        """Separate object per fragment group (frag_00...), recentred with the same shift as finish()."""
        objs = []
        root = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(root)
        for i, key in enumerate(sorted(self.groups.keys())):
            g = self.groups[key]
            ob = self._bm_to_obj(g, "frag_%02d" % i)
            ob.parent = root
            objs.append(ob)
        return root, objs


# ---------------------------------------------------------------------------------------------------------------
def clear_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)


def export_glb(root_obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    stack = [root_obj]
    while stack:
        o = stack.pop()
        o.select_set(True)
        stack.extend(o.children)
    bpy.context.view_layer.objects.active = root_obj
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
        export_materials="EXPORT", export_image_format="NONE", export_vertex_color="ACTIVE",
        export_normals=True, export_texcoords=True, export_extras=False, export_cameras=False,
        export_lights=False, export_animations=False, export_skins=False, export_morph=False)
