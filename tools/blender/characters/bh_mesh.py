"""Small procedural modeling toolkit (numpy geometry + Blender modifier baking + skinned mesh assembly)."""
import math
import numpy as np

from bh_math import normalize, R_axis, Rx, Ry, Rz


class Part:
    """Geometry piece. bone = rigid binding; wfn(V) -> list[dict bone->w] for smooth skinning."""

    def __init__(self, V, F, mat, bone=None, wfn=None, name="part"):
        self.V = np.asarray(V, float).reshape(-1, 3)
        self.F = [tuple(int(i) for i in f) for f in F]
        self.mat = mat
        self.bone = bone
        self.wfn = wfn
        self.name = name
        self.W = None

    def copy(self):
        p = Part(self.V.copy(), list(self.F), self.mat, self.bone, self.wfn, self.name)
        p.W = None if self.W is None else list(self.W)
        return p

    # transforms (return self for chaining)
    def move(self, t):
        self.V = self.V + np.asarray(t, float)
        return self

    def rot(self, R, center=(0, 0, 0)):
        c = np.asarray(center, float)
        self.V = (self.V - c) @ np.asarray(R).T + c
        return self

    def scale(self, s, center=(0, 0, 0)):
        c = np.asarray(center, float)
        self.V = (self.V - c) * np.asarray(s, float) + c
        return self

    def warp(self, fn):
        self.V = np.array([fn(v) for v in self.V])
        return self

    def flip(self):
        self.F = [tuple(reversed(f)) for f in self.F]
        return self

    def mirrored(self, swap_sides=True):
        p = self.copy()
        p.V[:, 0] *= -1
        p.flip()
        if swap_sides and p.bone:
            p.bone = swap_lr(p.bone)
        if swap_sides and p.wfn:
            f = p.wfn

            def wfn(V, f=f):
                Vm = V.copy()
                Vm[:, 0] *= -1
                return [{swap_lr(k): v for k, v in d.items()} for d in f(Vm)]
            p.wfn = wfn
        return p

    def to(self, bone=None, mat=None, wfn=None):
        if bone is not None:
            self.bone = bone
            self.wfn = None
        if wfn is not None:
            self.wfn = wfn
            self.bone = None
        if mat is not None:
            self.mat = mat
        return self


def swap_lr(name):
    if name.endswith(".L"):
        return name[:-2] + ".R"
    if name.endswith(".R"):
        return name[:-2] + ".L"
    return name


def merge(parts, mat=None, bone=None):
    V, F, off = [], [], 0
    for p in parts:
        V.append(p.V)
        F.extend(tuple(i + off for i in f) for f in p.F)
        off += len(p.V)
    return Part(np.vstack(V), F, mat or parts[0].mat, bone if bone is not None else parts[0].bone, parts[0].wfn)


# ---------------------------------------------------------------------------------------------
# primitive generators
def superellipse(n, rx, ry, p=2.0, start=0.0):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False) + start
    c, s = np.cos(t), np.sin(t)
    e = 2.0 / p
    x = rx * np.sign(c) * np.abs(c) ** e
    y = ry * np.sign(s) * np.abs(s) ** e
    return np.stack([x, y], 1)


def ring_frame(T, up):
    T = normalize(T)
    A = np.asarray(up, float) - T * np.dot(up, T)
    if np.linalg.norm(A) < 1e-6:
        A = np.array([1.0, 0, 0]) - T * T[0]
    A = normalize(A)
    B = np.cross(A, T)
    return B, A


def loft(rings, cap0=True, cap1=True, closed=True):
    """rings: list of (n,3) arrays. Returns (V, F). Caps as center-fans."""
    n = len(rings[0])
    V = np.vstack(rings)
    F = []
    m = n if closed else n - 1
    for r in range(len(rings) - 1):
        a0, b0 = r * n, (r + 1) * n
        for i in range(m):
            j = (i + 1) % n
            F.append((a0 + i, a0 + j, b0 + j, b0 + i))
    Vl = [V]
    base = len(V)
    if cap0 and closed:
        c = rings[0].mean(0)
        Vl.append(c[None])
        for i in range(n):
            F.append((base, (i + 1) % n, i))
        base += 1
    if cap1 and closed:
        c = rings[-1].mean(0)
        Vl.append(c[None])
        o = (len(rings) - 1) * n
        for i in range(n):
            F.append((base, o + i, o + (i + 1) % n))
    return np.vstack(Vl), F


def tube(points, prof, n=12, up=(0, -1, 0), p=2.0, cap0=True, cap1=True, twist=None, offsets=None):
    """Tube along a polyline. prof: list of (rx, ry) or (rx, ry, p) per point (rx across, ry along `up`).
    offsets: optional list of 2D (dx, dy) ring-center offsets in the ring frame."""
    pts = np.asarray(points, float)
    rings = []
    ups = up if (isinstance(up, list) and len(up) == len(pts) and np.ndim(up[0]) == 1) else [up] * len(pts)
    for i, c in enumerate(pts):
        if i == 0:
            T = pts[1] - pts[0]
        elif i == len(pts) - 1:
            T = pts[-1] - pts[-2]
        else:
            T = normalize(pts[i + 1] - pts[i]) + normalize(pts[i] - pts[i - 1])
        B, A = ring_frame(T, np.asarray(ups[i], float))
        pr = prof[i]
        pp = pr[2] if len(pr) > 2 else p
        xy = superellipse(n, pr[0], pr[1], pp, start=(twist[i] if twist else 0.0))
        if offsets is not None:
            xy = xy + np.asarray(offsets[i], float)
        rings.append(c + xy[:, :1] * B + xy[:, 1:2] * A)
    return loft(rings, cap0, cap1)


def lathe(profile, n=16, a0=0.0, a1=360.0, cap=True):
    """profile: list of (r, z). Revolve around Z. r==0 endpoints become poles."""
    full = abs(a1 - a0) >= 359.999
    angs = np.radians(np.linspace(a0, a1, n, endpoint=not full))
    m = len(angs)
    V, F, idx = [], [], []
    for (r, z) in profile:
        if r < 1e-7:
            idx.append([len(V)] * m)
            V.append((0, 0, z))
        else:
            row = []
            for a in angs:
                row.append(len(V))
                V.append((r * math.cos(a), r * math.sin(a), z))
            idx.append(row)
    cols = m if full else m - 1
    for i in range(len(profile) - 1):
        for j in range(cols):
            jn = (j + 1) % m
            a, b, c, d = idx[i][j], idx[i][jn], idx[i + 1][jn], idx[i + 1][j]
            face = []
            for v in (a, b, c, d):
                if v not in face:
                    face.append(v)
            if len(face) >= 3:
                F.append(tuple(face))
    V = np.array(V, float)
    if cap and full:
        for row, top in ((idx[0], False), (idx[-1], True)):
            if len(set(row)) > 1:
                F.append(tuple(row) if top else tuple(reversed(row)))
    return V, F


def box(sx, sy, sz, center=(0, 0, 0)):
    x, y, z = sx / 2, sy / 2, sz / 2
    V = np.array([(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
                  (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]) + np.asarray(center, float)
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return V, F


def prism(outline, depth, axis="y", center=0.0):
    """Extrude 2D outline (list of (u, v), CCW) into a slab. axis: slab normal.
    'y': u->x, v->z (slab facing -Y/+Y); 'x': u->y, v->z; 'z': u->x, v->y."""
    o = np.asarray(outline, float)
    n = len(o)
    d0, d1 = center - depth / 2, center + depth / 2

    def P(u, v, w):
        if axis == "y":
            return (u, w, v)
        if axis == "x":
            return (w, u, v)
        return (u, v, w)
    V = [P(u, v, d0) for u, v in o] + [P(u, v, d1) for u, v in o]
    F = []
    for i in range(n):
        j = (i + 1) % n
        F.append((i, j, n + j, n + i))
    F.append(tuple(range(n)))
    F.append(tuple(reversed(range(n, 2 * n))))
    return np.array(V, float), F


def grid(fn, nu, nv, closed_u=False):
    """Surface sheet: fn(u, v) -> xyz with u,v in [0,1]."""
    us = np.linspace(0, 1, nu, endpoint=not closed_u)
    vs = np.linspace(0, 1, nv)
    V = [fn(u, v) for v in vs for u in us]
    F = []
    cu = nu if closed_u else nu - 1
    for j in range(nv - 1):
        for i in range(cu):
            i2 = (i + 1) % nu
            F.append((j * nu + i, j * nu + i2, (j + 1) * nu + i2, (j + 1) * nu + i))
    return np.array(V, float), F


def sphere(r, n=12, rings=8, center=(0, 0, 0), scale=(1, 1, 1)):
    prof = [(r * math.sin(math.pi * i / rings), -r * math.cos(math.pi * i / rings)) for i in range(rings + 1)]
    V, F = lathe(prof, n)
    V = V * np.asarray(scale, float) + np.asarray(center, float)
    return V, F


def mk(VF, mat, bone=None, wfn=None, name="part"):
    return Part(VF[0], VF[1], mat, bone, wfn, name)


# ---------------------------------------------------------------------------------------------
# skin weight helpers
def seg_dist(V, a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    ab = b - a
    t = np.clip(((V - a) @ ab) / max(np.dot(ab, ab), 1e-12), 0, 1)
    P = a + t[:, None] * ab
    return np.linalg.norm(V - P, axis=1), t


def chain_weights(J, bones, power=8.0, top=3):
    """Distance-based smooth skinning over a set of bone segments (rest pose joints J)."""
    def wfn(V):
        D = []
        for b in bones:
            h, t, _ = J[b]
            d, _ = seg_dist(V, h, t)
            D.append(d)
        D = np.stack(D, 1) + 0.01
        W = 1.0 / D ** power
        out = []
        for row in W:
            idx = np.argsort(-row)[:top]
            s = row[idx].sum()
            out.append({bones[i]: row[i] / s for i in idx if row[i] / s > 0.01})
        return out
    return wfn


def blend_weights(fn):
    """Wrap a per-vertex python function v -> dict."""
    def wfn(V):
        return [fn(v) for v in V]
    return wfn


def smoothstep(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------------------------------------
# Blender side
def bake_mods(part, mods):
    """Apply Blender modifiers to a part. mods: list of (type, {props})."""
    import bpy
    me = bpy.data.meshes.new("tmp_" + part.name)
    me.from_pydata(part.V.tolist(), [], part.F)
    me.validate(clean_customdata=False)
    ob = bpy.data.objects.new("tmp_" + part.name, me)
    bpy.context.scene.collection.objects.link(ob)
    for i, (typ, props) in enumerate(mods):
        m = ob.modifiers.new(f"m{i}", typ)
        for k, v in props.items():
            setattr(m, k, v)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me2 = bpy.data.meshes.new_from_object(ev)
    V = np.array([v.co[:] for v in me2.vertices])
    F = [tuple(p.vertices) for p in me2.polygons]
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    bpy.data.meshes.remove(me2)
    part.V, part.F = V, F
    return part


def bevel(part, width=0.004, segments=2, angle=35.0, harden=False):
    return bake_mods(part, [("BEVEL", dict(width=width, segments=segments, limit_method="ANGLE",
                                           angle_limit=math.radians(angle), harden_normals=harden))])


def solidify(part, thickness=0.01, offset=-1.0, bevel_w=0.0, segs=1):
    mods = [("SOLIDIFY", dict(thickness=thickness, offset=offset, use_even_offset=True))]
    if bevel_w > 0:
        mods.append(("BEVEL", dict(width=bevel_w, segments=segs, limit_method="ANGLE",
                                   angle_limit=math.radians(40))))
    return bake_mods(part, mods)


def subsurf(part, levels=1):
    return bake_mods(part, [("SUBSURF", dict(levels=levels, render_levels=levels))])


def recalc_normals(part):
    import bmesh
    import bpy
    me = bpy.data.meshes.new("tmpn")
    me.from_pydata(part.V.tolist(), [], part.F)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    part.V = np.array([v.co[:] for v in me.vertices])
    part.F = [tuple(p.vertices) for p in me.polygons]
    bpy.data.meshes.remove(me)
    return part


def build_skinned(name, parts, arm_ob, materials, J=None, sharp_angle=38.0, ao=None):
    """Join parts into one skinned mesh object parented to arm_ob. materials: dict name->bpy material."""
    import bpy
    V_all, F_all, mat_idx, wlist = [], [], [], []
    mats = []
    off = 0
    for p in parts:
        if p.mat not in mats:
            mats.append(p.mat)
        mi = mats.index(p.mat)
        V_all.append(p.V)
        for f in p.F:
            F_all.append(tuple(i + off for i in f))
            mat_idx.append(mi)
        if getattr(p, "W", None) is not None:
            wlist.extend(p.W)
        elif p.bone:
            wlist.extend([{p.bone: 1.0}] * len(p.V))
        elif p.wfn:
            wlist.extend(p.wfn(p.V))
        else:
            raise ValueError(f"part {p.name} has no skin binding")
        off += len(p.V)
    V = np.vstack(V_all)
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], F_all)
    me.validate(clean_customdata=False)
    for m in mats:
        me.materials.append(materials[m])
    me.polygons.foreach_set("material_index", mat_idx[:len(me.polygons)])
    me.shade_smooth()
    try:
        me.set_sharp_from_angle(angle=math.radians(sharp_angle))
    except Exception:
        pass
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    groups = {}
    for i, d in enumerate(wlist):
        for b, w in d.items():
            if b not in groups:
                groups[b] = ob.vertex_groups.new(name=b)
            groups[b].add([i], float(w), "REPLACE")
    ob.parent = arm_ob
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = arm_ob
    return ob


def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def outline_fill(outline, rings=4, center=None, power=1.0):
    """Quad-fill a star-shaped 2D outline with concentric scaled loops. Returns (V2 (n,2), F, outer_idx).
    The outer loop is the last `len(outline)` vertices."""
    o = np.asarray(outline, float)
    n = len(o)
    c = o.mean(0) if center is None else np.asarray(center, float)
    V = [c]
    F = []
    for r in range(1, rings + 1):
        s = (r / rings) ** power
        V.extend(c + (o - c) * s)
    V = np.array(V)
    for i in range(n):  # center fan
        F.append((0, 1 + i, 1 + (i + 1) % n))
    for r in range(1, rings):
        a = 1 + (r - 1) * n
        b = 1 + r * n
        for i in range(n):
            j = (i + 1) % n
            F.append((a + i, b + i, b + j, a + j))
    return V, F, list(range(1 + (rings - 1) * n, 1 + rings * n))


def resample_closed(pts, n):
    """Resample closed 2D polyline to n points evenly by arc length."""
    p = np.asarray(pts, float)
    q = np.vstack([p, p[:1]])
    seg = np.linalg.norm(np.diff(q, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    ts = np.linspace(0, L[-1], n, endpoint=False)
    out = []
    for t in ts:
        i = min(np.searchsorted(L, t, side="right") - 1, len(seg) - 1)
        u = (t - L[i]) / max(seg[i], 1e-9)
        out.append(q[i] * (1 - u) + q[i + 1] * u)
    return np.array(out)


def plate_from_outline(outline, thickness, rings=4, bulge=0.0, axis="y", bevel_w=0.0, front=-1.0):
    """Curved plate: fill outline in (u, v) plane, bulge toward `front` along the normal axis, solidify."""
    V2, F, _ = outline_fill(outline, rings)
    c = V2.mean(0)
    ext = np.abs(V2 - c).max(0)
    r2 = ((V2[:, 0] - c[0]) / max(ext[0], 1e-6)) ** 2 + ((V2[:, 1] - c[1]) / max(ext[1], 1e-6)) ** 2
    w = front * bulge * (1 - np.clip(r2, 0, 1.5) / 1.5)
    if axis == "y":
        V = np.stack([V2[:, 0], w, V2[:, 1]], 1)
    elif axis == "x":
        V = np.stack([w, V2[:, 0], V2[:, 1]], 1)
    else:
        V = np.stack([V2[:, 0], V2[:, 1], w], 1)
    return V, F


def build_static(name, parts, materials, sharp_angle=38.0):
    import bpy
    V_all, F_all, mat_idx, mats, off = [], [], [], [], 0
    for p in parts:
        if p.mat not in mats:
            mats.append(p.mat)
        mi = mats.index(p.mat)
        V_all.append(p.V)
        for f in p.F:
            F_all.append(tuple(i + off for i in f))
            mat_idx.append(mi)
        off += len(p.V)
    me = bpy.data.meshes.new(name)
    me.from_pydata(np.vstack(V_all).tolist(), [], F_all)
    me.validate(clean_customdata=False)
    for m in mats:
        me.materials.append(materials[m])
    me.polygons.foreach_set("material_index", mat_idx[:len(me.polygons)])
    me.shade_smooth()
    try:
        me.set_sharp_from_angle(angle=math.radians(sharp_angle))
    except Exception:
        pass
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob
