"""bh-023: worn helms, gloves, boots and jewellery (slots `helm`, `gloves_*`, `boots_*`, `accessory_*`).

Helms reuse the item models' own builders (tools/blender/items/item_gear.py: helm, hood, circlet), scaled onto the
hero's head, so the worn helm is the helm in the icon. What an item model only paints (eye slits as black boxes, a
hood's face as a black ball, a rigid mantle ring) is made real here: slits lie on the helm's surface, the hood has an
open face and its mantle is cloth cut from the shoulders. Gloves, boots and jewellery follow the item specs (same
palette keys, cuffs, plates, straps, gems) but are cut from the hero's own hands and legs so they fit and bend; they
are authored for the LEFT side, the kit mirrors them.

Close-up previews: hero_wear_ends_preview.py; counts and checks: hero_wear_ends_check.py.
"""
import json
import math
import os

import numpy as np

import item_gear as G
import hero_wear_kit as WK
from hero_wear_kit import K, M, item, pal, shell, attach
from bh_math import Rx, Ry, Rz  # noqa: F401

HEAD_C = (0.0, -0.040)            # the skull's centre line (x, y)
EYE_Z = 1.687
R_HELM = 0.13                     # the head radius the item helms are built around

with open(os.path.join(WK.ITEMS, "depth_specs.json"), encoding="utf-8") as _f:
    DEPTH = {k: v[1] for k, v in json.load(_f).items()}


def spec_of(id):
    """The item model's spec: the worn piece is built from the same one."""
    return dict(DEPTH[id]) if id in DEPTH else dict(G.GEAR[id][1])


# ---- small tools ------------------------------------------------------------------------------------------------------
def tris_of(part):
    return sum(len(f) - 2 for f in part.F)


def simplify(part, tris):
    """A WPart reduced to about `tris` triangles (Blender's quadric Decimate), keeping its skin weights and its
    build-key deltas. The body is dense where it does not matter under a glove or a boot (fingers, toes)."""
    import bpy
    now = tris_of(part)
    if now <= tris:
        return part
    me = bpy.data.meshes.new("tmp_simplify")
    me.from_pydata(part.V.tolist(), [], part.F)
    ob = bpy.data.objects.new("tmp_simplify", me)
    bpy.context.scene.collection.objects.link(ob)
    used = [i for i in range(len(WK.BONES)) if part.W[:, i].max() > 1e-4]
    for i in used:
        g = ob.vertex_groups.new(name=WK.BONES[i])
        for v in np.nonzero(part.W[:, i] > 1e-4)[0]:
            g.add([int(v)], float(part.W[v, i]), "REPLACE")
    for k in range(part.D.shape[0]):
        a = me.attributes.new("bk%d" % k, "FLOAT_VECTOR", "POINT")
        a.data.foreach_set("vector", np.ascontiguousarray(part.D[k], dtype=np.float32).ravel())
    mod = ob.modifiers.new("dec", "DECIMATE")
    mod.ratio = tris / float(now)
    mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    n = len(me2.vertices)
    V = np.zeros(n * 3, np.float32)
    me2.vertices.foreach_get("co", V)
    F = [tuple(p.vertices) for p in me2.polygons]
    W = np.zeros((n, len(WK.BONES)))
    names = [g.name for g in ob.vertex_groups]
    for v in me2.vertices:
        for g in v.groups:
            W[v.index, WK.BONES.index(names[g.group])] = g.weight
    bad = W.sum(1) < 1e-6
    if bad.any():
        W[bad] = part.W.mean(0)
    W /= W.sum(1, keepdims=True)
    D = np.zeros((part.D.shape[0], n, 3))
    for k in range(part.D.shape[0]):
        buf = np.zeros(n * 3, np.float32)
        me2.attributes["bk%d" % k].data.foreach_get("vector", buf)
        D[k] = buf.reshape(-1, 3)
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    bpy.data.meshes.remove(me2)
    return WK.WPart(V.reshape(-1, 3).astype(float), F, part.mat, W, D, part.name)


def rigid(part, bone):
    """The whole WPart follows one bone (plates cut from the body: they keep the body's build keys)."""
    part.W = np.zeros_like(part.W)
    part.W[:, WK.BONES.index(bone)] = 1.0
    return part


def cut(part, field):
    """An authored part cut along the zero line of field(V): the side where it is positive stays (a hood's face
    opening). Faces are split exactly on the line, as the kit's shell() does with the body."""
    V = [tuple(v) for v in part.V]
    f = np.asarray(field(part.V), float)
    fl = list(f)
    index = {}

    def mid(i, j):
        key = (min(i, j), max(i, j))
        if key not in index:
            i0, j0 = key
            t = fl[i0] / (fl[i0] - fl[j0])
            index[key] = len(V)
            V.append(tuple(np.asarray(V[i0]) * (1 - t) + np.asarray(V[j0]) * t))
        return index[key]

    F = []
    for face in part.F:
        for k in range(1, len(face) - 1):
            tri = (face[0], face[k], face[k + 1])
            ins = [fl[i] > 0.0 for i in tri]
            n_in = sum(ins)
            if n_in == 3:
                F.append(tri)
            elif n_in:
                for r in range(3):
                    a_, b_, c_ = tri[r], tri[(r + 1) % 3], tri[(r + 2) % 3]
                    if n_in == 1 and fl[a_] > 0.0:
                        F.append((a_, mid(a_, b_), mid(a_, c_)))
                        break
                    if n_in == 2 and not fl[a_] > 0.0:
                        ab, ac = mid(a_, b_), mid(a_, c_)
                        F.append((ab, b_, c_))
                        F.append((ab, c_, ac))
                        break
    used = sorted({i for fc in F for i in fc})
    remap = {o: n for n, o in enumerate(used)}
    part.V = np.array([V[i] for i in used], float)
    part.F = [tuple(remap[i] for i in fc) for fc in F]
    return part


def loop_tube(pts, r, mat, n=5, out=(0.0, -1.0, 0.0), centre=None, name="trim"):
    """A closed cord along a loop of points (a trim around an opening): `out` is the direction the loop faces."""
    pts = np.asarray(pts, float)
    out = np.asarray(out, float)
    c = pts.mean(0) if centre is None else np.asarray(centre, float)
    rings = []
    for p in pts:
        rad = p - c
        rad = rad - out * float(rad @ out)
        rad /= max(np.linalg.norm(rad), 1e-9)
        rings.append(np.array([p + r * (math.cos(a) * rad + math.sin(a) * out) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]))
    rings.append(rings[0].copy())
    V, F = M.loft(rings, cap0=False, cap1=False)
    return M.recalc_normals(M.Part(V, F, mat, name=name))


def face_toward(part, point, away=False):
    """Turn every face of an open sheet toward (or away from) a point."""
    p0 = np.asarray(point, float)
    F = []
    for f in part.F:
        P = part.V[list(f)]
        nrm = np.cross(P[1] - P[0], P[2] - P[0])
        d = float(nrm @ (p0 - P.mean(0)))
        F.append(tuple(reversed(f)) if (d < 0) != away else f)
    part.F = F
    return part


# ---- helms ------------------------------------------------------------------------------------------------------------
def _zmap(z, pairs):
    """Piecewise-linear heights: item z -> model z through the (item z, model z) pairs (continued past the ends)."""
    zi = np.array([a for a, _ in pairs], float)
    zw = np.array([b for _, b in pairs], float)
    out = np.interp(z, zi, zw)
    lo, hi = z < zi[0], z > zi[-1]
    out[lo] = zw[0] + (z[lo] - zi[0]) * (zw[1] - zw[0]) / (zi[1] - zi[0])
    out[hi] = zw[-1] + (z[hi] - zi[-1]) * (zw[-1] - zw[-2]) / (zi[-1] - zi[-2])
    return out


def on_head(parts, sx=0.76, sy=0.92, sz=0.62, z0=1.695, y=None, zmap=None):
    """Item-model helm parts (upright on the rim at the origin, face -Y, head radius 0.13) -> on the hero's head:
    scaled about the origin, rim lifted to z0 (or heights remapped through `zmap`, pairs of item z -> model z, when
    the helm must reach both the eyes and the crown), centred on the skull. Palette keys are switched to the worn
    palette."""
    yc = HEAD_C[1] if y is None else y
    for p in parts:
        src = p.V
        if p.name in ("sphere", "gem", "crystal"):       # rivets and stones keep their shape: only their place moves
            c = src.mean(0)
            src = np.vstack([c[None], src])
        V = src * np.array([sx, sy, 1.0])
        V[:, 2] = _zmap(src[:, 2], zmap) if zmap else z0 + src[:, 2] * sz
        V[:, 0] += HEAD_C[0]
        V[:, 1] += yc
        if len(src) != len(p.V):
            V = V[0] + (p.V - c) * min(sx, sy)
        p.V = V
        p.mat = pal(p.mat)
    return attach(parts, bone="head", keys=False)


def _open_rim(parts):
    """Drop the discs that close an item helm's lathes (the head goes through them)."""
    for p in parts:
        if p.name in ("dome", "lathe", "greathelm", "brim"):
            p.F = [f for f in p.F if len(f) <= 4]
    return parts


def _surface_r(parts):
    """Outer radius of a lathed helm as a function of height (item space), from its non-black lathes."""
    rows = {}
    for p in parts:
        if p.mat == "black" or p.name not in ("dome", "lathe", "greathelm"):
            continue
        r = np.hypot(p.V[:, 0], p.V[:, 1])
        for z, rr in zip(np.round(p.V[:, 2], 4), r):
            rows[z] = max(rows.get(z, 0.0), rr)
    zs = np.array(sorted(rows))
    rs = np.array([rows[z] for z in zs])
    return lambda z: float(np.interp(z, zs, rs))


def _patch(x0, x1, z0, z1, rfn, mat, proud=0.002, raised=False, name="slit"):
    """A patch lying on the front of a lathed helm (item space): what the item model paints with a flat box."""
    nx = max(1, int(math.ceil((x1 - x0) / 0.02)))
    nz = max(1, int(math.ceil((z1 - z0) / 0.012)))
    xs, zs = np.linspace(x0, x1, nx + 1), np.linspace(z0, z1, nz + 1)

    def layer(d):
        out = []
        for z in zs:
            r = rfn(z) + d
            out += [(x, -math.sqrt(max(r * r - x * x, 1e-8)), z) for x in xs]
        return out
    V, F, w = layer(proud), [], nx + 1
    for j in range(nz):
        for i in range(nx):
            a = j * w + i
            F.append((a, a + 1, a + w + 1, a + w))
    if raised:
        n = len(V)
        V += layer(-0.004)
        loop = [i for i in range(nx)] + [j * w + nx for j in range(nz)] + [nz * w + nx - i for i in range(nx)] + [(nz - j) * w for j in range(nz)]
        for k, a in enumerate(loop):
            b = loop[(k + 1) % len(loop)]
            F.append((b, a, a + n, b + n))
    return M.Part(np.array(V, float), F, mat, name=name)


def _wrap_boxes(parts):
    """Replace a lathed helm's flat boxes (eye slits, breaths, nasal, crest bar) by patches on its surface."""
    rfn = _surface_r(parts)
    out = []
    for p in parts:
        if p.name != "box":
            out.append(p)
            continue
        x0, x1, z0, z1 = p.V[:, 0].min(), p.V[:, 0].max(), p.V[:, 2].min(), p.V[:, 2].max()
        if p.mat == "black":
            out.append(_patch(x0, x1, z0, z1, rfn, p.mat))
        else:
            out.append(_patch(x0, x1, z0, z1, rfn, p.mat, proud=0.006, raised=True, name="bar"))
    return out


def _open_face(parts, z_split=0.085, keep=0.12, a0=42.0, a1=74.0):
    """Lift the front of a helm's lower shell (item space, below z_split) so the face shows: the shell keeps its
    depth at the sides and the back (cheek and neck guards) and only `keep` of it over the brow."""
    for p in parts:
        V = p.V
        low = V[:, 2] < z_split
        ang = np.degrees(np.abs(np.arctan2(V[:, 0], -V[:, 1])))
        r = np.hypot(V[:, 0], V[:, 1])
        k = keep + (1 - keep) * WK.step(a0, a1, ang)
        k = np.where(r < 1e-6, keep, k)
        V[:, 2] = np.where(low, z_split - (z_split - V[:, 2]) * k, V[:, 2])
    return parts


@item("iron_helm", hair="hide")
def iron_helm():
    """Kettle hat: the bowl on the crown, the brim at the brow, the face open."""
    parts = _wrap_boxes(_open_rim(G.helm(spec_of("iron_helm"))))
    return on_head(parts, sx=0.76, sy=0.90, sz=0.54, z0=1.706)


@item("barbute_helm", hair="hide")
def barbute_helm():
    """Barbute: closed to the jaw, a T-shaped opening with its bar on the eye line."""
    parts = _open_rim(G.helm(spec_of("barbute_helm")))
    for p in parts:
        if p.name == "lathe" and np.abs(p.V[:, 0]).max() < 0.02:       # the crest: only its comb above the bowl
            p.V[:, 2] = 0.205 + (p.V[:, 2] - 0.08) * 0.42
            p.V[:, 1] *= 1.5
        elif p.name == "box" and np.ptp(p.V[:, 0]) > 0.1:              # the eye bar, lower on the bowl
            p.V[:, 2] -= 0.031
        elif p.name == "box":                                          # the nose-to-chin slot up to the eye bar
            p.V[:, 2] = 0.005 + (p.V[:, 2] - 0.005) * (0.10 / 0.13)
    parts = _wrap_boxes(parts)
    return on_head(parts, sx=0.83, sy=1.06, y=-0.040, zmap=[(0.0, 1.560), (0.08, 1.655), (0.109, EYE_Z), (0.25, 1.840)])


def _greathelm(id):
    parts = _wrap_boxes(_open_rim(G.helm(spec_of(id))))
    # the two eye slits sit at item z 0.175 / 0.195 (the builder grounds the helm 5 mm up): the eye line between them
    return on_head(parts, sx=0.80, sy=0.98, y=-0.046, zmap=[(0.005, 1.540), (0.185, EYE_Z), (0.315, 1.842)])


@item("visored_greathelm", hair="hide")
def visored_greathelm():
    return _greathelm("visored_greathelm")


@item("depth_deepwarden_crown", hair="hide")
def depth_deepwarden_crown():
    return _greathelm("depth_deepwarden_crown")


@item("guardian_helm", hair="hide")
def guardian_helm():
    """Winged helm: open face, cheek and neck guards, the wings at the temples, the aether crystal over the brow."""
    parts = _open_rim(G.helm(spec_of("guardian_helm")))
    rfn = _surface_r(parts)
    for p in parts:
        if p.name == "crystal":                      # the item's crystal floats before the bowl: stand it on the brow
            c = p.V.mean(0)
            p.rot(K.Rx(-90), c).rot(K.Rx(-24), c).move((0 - c[0], -(rfn(0.15) + 0.006) - c[1], 0.15 - c[2]))
    parts = _open_face(parts)
    return on_head(parts, sx=0.85, sy=0.98, y=-0.044, zmap=[(0.0, 1.585), (0.085, 1.722), (0.25, 1.840)])


# ---- hoods ------------------------------------------------------------------------------------------------------------
def border_loops(part):
    """The open edges of a part as loops of vertex indices."""
    count = {}
    for f in part.F:
        for a, b in zip(f, tuple(f[1:]) + tuple(f[:1])):
            count[(min(a, b), max(a, b))] = count.get((min(a, b), max(a, b)), 0) + 1
    nb = {}
    for (a, b), c in count.items():
        if c == 1:
            nb.setdefault(a, []).append(b)
            nb.setdefault(b, []).append(a)
    loops, seen = [], set()
    for start in nb:
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            nxt = [v for v in nb[cur] if v != prev and v not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            loop.append(cur)
            seen.add(cur)
        loops.append(loop)
    return loops


def cord_on(part, loop, r, mat, n=28, sides=4, lift=0.0, name="cord"):
    """A cord along a loop of a WPart's vertices (the hem of a cut cloth): it takes the cloth's own weights and
    build keys, so it stays on the hem however the body bends."""
    P, W, D = part.V[loop], part.W[loop], part.D[:, loop]
    seg = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)
    L = np.concatenate([[0.0], np.cumsum(seg)])
    m = len(loop)
    Pn, Wn, Dn = [], [], []
    for t in np.linspace(0.0, L[-1], n, endpoint=False):
        i = min(int(np.searchsorted(L, t, side="right")) - 1, m - 1)
        u = (t - L[i]) / max(seg[i], 1e-9)
        j = (i + 1) % m
        Pn.append(P[i] * (1 - u) + P[j] * u)
        Wn.append(W[i] * (1 - u) + W[j] * u)
        Dn.append(D[:, i] * (1 - u) + D[:, j] * u)
    Pn, Wn, Dn = np.array(Pn), np.array(Wn), np.array(Dn)          # (n,3) (n,bones) (n,keys,3)
    c = Pn.mean(0)
    V, Wv, Dv, F = [], [], [], []
    for k in range(n):
        T = Pn[(k + 1) % n] - Pn[k - 1]
        T /= max(np.linalg.norm(T), 1e-9)
        A = Pn[k] - c
        A = A - T * float(A @ T)
        A /= max(np.linalg.norm(A), 1e-9)
        B = np.cross(T, A)
        for a in np.linspace(0, 2 * math.pi, sides, endpoint=False):
            V.append(Pn[k] + lift * A + r * (math.cos(a) * A + math.sin(a) * B))
            Wv.append(Wn[k])
            Dv.append(Dn[k])
        k2 = (k + 1) % n
        for i in range(sides):
            j = (i + 1) % sides
            F.append((k * sides + i, k * sides + j, k2 * sides + j, k2 * sides + i))
    V = np.array(V)
    q = V[list(F[0])]
    if float(np.cross(q[1] - q[0], q[2] - q[0]) @ (q.mean(0) - Pn[0])) < 0:
        F = [tuple(reversed(f)) for f in F]
    return WK.WPart(V, F, mat, np.array(Wv), np.transpose(np.array(Dv), (1, 0, 2)), name)


def _mantle_field(V, R, c=(0.0, -0.02, 1.56), top=1.572):
    """The shoulders, collar and upper chest within R of the base of the neck: where a hood's mantle lies."""
    d = np.sqrt(V[:, 0] ** 2 + (V[:, 1] - c[1]) ** 2 + (V[:, 2] - c[2]) ** 2)
    return np.minimum.reduce([R - d, top - V[:, 2]])


# item heights of the cowl -> on the head: its wide lower half spans the whole head (neck to crown), its rounded top
# closes just above the skull, so the hood is a round cowl and not a cone
HOOD_Z = [(0.03, 1.512), (0.16, 1.760), (0.29, 1.852)]


def _hood(id, sx=0.93, sy=0.93, yc=-0.040, zpairs=HOOD_Z, face=(0.072, 0.105, 1.664), R=0.215, mantle_tris=280, gather=0.22):
    """A worn hood from the item's own cowl: the cowl rigid on the head with a real face opening (trimmed with the
    item's trim, shadowed inside), the item's drooping point, gem and stars, and a mantle cut from the shoulders."""
    s = spec_of(id)
    m, peak = pal(s.get("mat", "wool")), s.get("peak", 1.0)
    tm = pal(s["trim"]) if s.get("trim") else m
    src = G.hood(dict(s))
    cowl = next(p for p in src if p.name == "hood")
    shift = cowl.V[:, 2].min() - 0.03                       # the builder grounds the model: the cowl starts at 0.03
    cloth = [p for p in src if p.name in ("hood", "tube")]
    zi, zw = np.array([p[0] for p in zpairs]), np.array([p[1] for p in zpairs])

    def tuck(zit):                                          # the cowl is gathered at the neck, below the face
        return 1.0 - gather * (1.0 - WK.step(0.03, 0.085, zit))

    for p in cloth:
        zit = p.V[:, 2] - shift
        k = tuck(zit)
        p.V = np.stack([p.V[:, 0] * sx * k, yc + p.V[:, 1] * sy * k, _zmap(zit, zpairs)], 1)
        p.mat = m
    a, b, zc = face

    def ring(z):                                            # the cowl at height z: half width, half depth, centre y
        zit = float(np.interp(z, zw, zi))
        t = min(max((zit - 0.03) / 0.26, 0.0), 1.0)
        rt = math.cos(t * math.pi / 2) ** 0.55
        k = float(tuck(zit))
        return (0.13 * rt + 0.004) * sx * k, (0.145 * rt + 0.004) * sy * k, yc + 0.03 * peak * t ** 3 * sy * k

    def front(x, z):
        rx, ry, cy = ring(z)
        return cy - ry * math.sqrt(max(1.0 - (x / rx) ** 2, 0.0))

    cut(cowl, lambda V: np.where(V[:, 1] < yc + 0.03, np.sqrt((V[:, 0] / a) ** 2 + ((V[:, 2] - zc) / b) ** 2) - 1.0, 1.0))
    th = np.linspace(0, 2 * math.pi, 18, endpoint=False)
    edge = np.array([(a * math.cos(t), front(a * math.cos(t), zc + b * math.sin(t)) - 0.001, zc + b * math.sin(t)) for t in th])
    parts = cloth + [loop_tube(edge, 0.0075, tm, n=4, centre=(0.0, edge[:, 1].mean(), zc))]
    deep = np.array([(0.88 * x, max(y + 0.07, -0.075), zc + 0.90 * (z - zc)) for x, y, z in edge])
    V, F = M.loft([edge, deep], cap0=False, cap1=False)
    parts.append(face_toward(M.Part(V, F, pal("black"), name="shade"), (0.0, float(edge[:, 1].mean()) + 0.03, zc)))
    if s.get("gem"):
        zt = zc + b + 0.017
        parts.append(K.gem((0.0, front(0.0, zt) - 0.004, zt), 0.013, pal(s["gem"]), rot=(90, 0, 0)))
    if s.get("stars"):
        for i in range(9):
            ang = i * 0.7
            z = float(_zmap(np.array([0.06 + 0.024 * i]), zpairs)[0])
            rx, ry, cy = ring(z)
            x, y = rx * math.cos(ang), cy + ry * math.sin(ang)
            if y < yc and (x / a) ** 2 + ((z - zc) / b) ** 2 < 1.5:       # not in the face: up onto the brow
                z = zc + b + 0.04
                rx, ry, cy = ring(z)
                x, y = rx * math.cos(ang), cy + ry * math.sin(ang)
            parts.append(K.gem((x * 1.02, cy + (y - cy) * 1.02, z), 0.0075, pal(s["stars"]), facets=4))
    out = attach(parts, bone="head", keys=False)

    def fld(V):
        return _mantle_field(V, R)

    def off(V):
        return 0.016 + 0.034 * WK.step(1.50, 1.57, V[:, 2])
    out.append(simplify(shell(fld, off, m, "mantle", relax=3), mantle_tris))
    if s.get("trim"):
        raw = shell(fld, off, m, "mantle", rim=False, relax=3)
        hem = min(border_loops(raw), key=lambda lp: raw.V[lp][:, 2].mean())
        out.append(cord_on(raw, hem, 0.006, tm, n=26))
    return out


@item("linen_hood", hair="hide")
def linen_hood():
    return _hood("linen_hood")


@item("arcanist_cowl", hair="hide")
def arcanist_cowl():
    return _hood("arcanist_cowl")


@item("sage_hood", hair="hide")
def sage_hood():
    return _hood("sage_hood")


@item("depth_prismkeeper_crown", hair="hide")
def depth_prismkeeper_crown():
    return _hood("depth_prismkeeper_crown")


@item("depth_vaultpath_crown", hair="hide")
def depth_vaultpath_crown():
    return _hood("depth_vaultpath_crown")


@item("depth_gloomthread_crown", hair="hide")
def depth_gloomthread_crown():
    return _hood("depth_gloomthread_crown")


@item("seers_circlet", hair="keep")
def seers_circlet():
    """The circlet on the brow (the hair stays), its veil falling behind the head."""
    parts = G.circlet(spec_of("seers_circlet"))
    band_z = float(parts[0].V[:, 2].mean())
    for p in parts:
        if p.name == "veil":                                  # hang the veil closer to the neck than the item's bell
            t = np.clip((band_z - p.V[:, 2]) / 0.16, 0.0, 1.0)
            p.V[:, 0] *= 1.0 + 0.07 * np.minimum(t * 4.0, 1.0)          # clear of the ears
            p.V[:, 1] *= 1.0 - 0.22 * t
    return on_head(parts, sx=0.92, sy=0.985, sz=0.9, z0=1.742 - band_z * 0.9, y=-0.030)


# ---- gloves -----------------------------------------------------------------------------------------------------------
# The hero's hands are fists: palm down in the rest pose, the back of the hand up (+Z), the knuckles at x ~ 0.83, the
# fingers curled under, the thumb forward (-Y). A glove is the skin of the fist pushed out (the skin itself is hidden
# from x = 0.725 on), a cuff cut from the forearm and flaring toward the elbow, and the item's plates, spikes and stone.
X_WRIST = 0.74


def _above(x, y, r=0.009):
    """Height of the top of the left hand's skin near (x, y)."""
    b = WK.body()
    m = (np.abs(b.V[:, 0] - x) < r) & (np.abs(b.V[:, 1] - y) < r) & (b.V[:, 2] > 1.25)
    return float(b.V[m][:, 2].max()) if m.any() else 1.46


def _cuff(x_end, base, flare, mat, trim, rings=1, relax=2):
    """A cuff cut from the forearm between x_end and the wrist: `base` thick at the wrist, `flare` more at its end,
    with `rings` trim cords (the first on its end)."""
    def off(V):
        return base + flare * np.clip((X_WRIST - V[:, 0]) / (X_WRIST - x_end), 0.0, 1.0) ** 1.5

    def fld(x0):
        return lambda V: np.minimum.reduce([V[:, 0] - x0, X_WRIST - V[:, 0], V[:, 2] - 1.25])
    out = [shell(fld(x_end), off, mat, "cuff", relax=relax)]
    for i in range(rings):
        x0 = x_end + (X_WRIST - 0.012 - x_end) * i / max(rings, 1)
        raw = shell(fld(x0), off, mat, "cuff", rim=False, relax=relax)
        end = min(border_loops(raw), key=lambda lp: raw.V[lp][:, 0].mean())
        out.append(cord_on(raw, end, 0.0048 if i == 0 else 0.0038, trim, n=14, name="cuff_trim"))
    return out


def _glove(id, fist_tris=640):
    s = spec_of(id)
    m, plate = pal(s.get("mat", "leather")), s.get("plate")
    trim = pal(s.get("trim") or "gold")
    cuff_m = pal(s.get("cuff") or plate or s.get("mat", "leather"))
    parts = [simplify(shell(lambda V: WK.hand(V, 1.0, 0.715), 0.005, m, "glove", relax=1), fist_tris)]
    if plate:
        pm = WK.plate(plate)
        parts += _cuff(0.60, 0.013, 0.020, cuff_m, trim, rings=3)

        def back(V):          # the back of the hand, wrist to knuckles
            top = 1.466 - 0.24 * (V[:, 0] - 0.74)
            return np.minimum.reduce([V[:, 2] - top, V[:, 0] - 0.742, 0.826 - V[:, 0], 0.045 - np.abs(V[:, 1] - 0.002)])

        def knuckles(V):      # the knuckles and the first joints of the fingers
            return np.minimum.reduce([V[:, 0] - 0.812, V[:, 2] - 1.418, 0.05 - np.abs(V[:, 1] - 0.002)])
        parts.append(rigid(simplify(shell(back, 0.011, pm, "back_plate", relax=3), 110), "hand.L"))
        parts.append(rigid(simplify(shell(knuckles, 0.0085, pm, "knuckle_plate", relax=2), 170), "hand.L"))
    else:
        parts += _cuff(0.665, 0.012, 0.006, cuff_m, trim, rings=1)
    extra = []
    if s.get("spikes"):
        for y in (-0.030, -0.010, 0.010, 0.030):
            z = _above(0.826, y) + (0.008 if plate else 0.004)
            extra.append(K.cone_spike((0.826, y, z - 0.004), (0.842, y, z + 0.026), 0.0065, pal(s["spikes"])))
    if s.get("runes"):
        z = _above(0.785, 0.002) + (0.012 if plate else 0.006)
        extra.append(K.gem((0.785, 0.002, z), 0.011, pal(s["runes"]), facets=6))
        extra.append(K.ring_tube((0.785, 0.002, z), 0.013, 0.0022, trim, axis="z", n=10))
    return parts + attach(extra, bone="hand.L", keys=False)


def _glove_item(id):
    @item(id, hide={"glove": [0.725, 1.0]}, sides=True)
    def fn():
        return _glove(id)
    return fn


# ---- boots ------------------------------------------------------------------------------------------------------------
# A boot is the skin of the foot and the lower leg pushed out (10 mm on the foot, 12 mm up the shaft, flaring at its top)
# up to a height from the item's own shaft (spec "h"); the skin is hidden inside it. Plated boots add a greave down the
# shin and lames over the instep. The leggings stay within 6.5 mm below the calf, so every shaft closes over them.
def _leg_axis(z):
    """Centre (x, y) of the left lower leg at height z (smoothed body sections)."""
    zs = np.linspace(0.08, 0.46, 20)
    cs = np.array([WK.leg_section(zz)[:2] for zz in zs])
    k = np.ones(3) / 3.0
    cx = np.convolve(np.pad(cs[:, 0], 1, mode="edge"), k, "valid")
    cy = np.convolve(np.pad(cs[:, 1], 1, mode="edge"), k, "valid")
    return np.interp(z, zs, cx), np.interp(z, zs, cy)


def _shin_front(z0, z1, a0=205.0, a1=335.0):
    """The front of the left shin between z0 and z1, from angle a0 to a1 around the leg (front = 270)."""
    def f(V):
        cx, cy = _leg_axis(V[:, 2])
        ang = np.degrees(np.arctan2(V[:, 1] - cy, V[:, 0] - cx)) % 360.0
        mid, half = (a0 + a1) / 2.0, (a1 - a0) / 2.0
        d = np.abs((ang - mid + 180.0) % 360.0 - 180.0)
        return np.minimum.reduce([V[:, 2] - z0, z1 - V[:, 2], (half - d) * 0.001, V[:, 0]])
    return f


def _instep(y0, y1, z0=0.035):
    """The top of the left foot between y0 (toward the toes, -Y) and y1."""
    return lambda V: np.minimum.reduce([V[:, 2] - z0, V[:, 1] - y0, y1 - V[:, 1], V[:, 0], 0.16 - V[:, 2]])


def _leg_ring(z, grow, mat, tube=0.004, n=14):
    """A strap round the left lower leg (four-sided cord: straps are flat)."""
    cx, cy, rx, ry = WK.leg_section(z)
    ax, ay = _leg_axis(z)
    P = [(ax + (rx + grow) * math.cos(a), ay + (ry + grow) * math.sin(a), z) for a in np.linspace(0, 2 * math.pi, n + 1)]
    return K.tube(P, [(tube * 0.6, tube * 1.3)] * len(P), mat, n=4, up=(0, 0, 1), cap=False, name="strap")


def boot_top(id):
    return 0.12 + float(spec_of(id).get("h", 0.3)) * 0.85


def _boot(id):
    s = spec_of(id)
    m = pal(s.get("mat", "leather"))
    plate = s.get("plate")
    trim = pal(s.get("cuff") or s.get("trim") or "gold")
    top = boot_top(id)
    flare = float(s.get("flare", 0.0))

    def off(V):
        z = V[:, 2]
        return 0.0105 + 0.0025 * WK.step(0.10, 0.20, z) + (0.003 + flare * 0.5) * WK.step(top - 0.09, top, z)
    sel = lambda V: WK.foot(V, 1.0, top)                           # noqa: E731
    parts = [simplify(shell(sel, off, m, "boot", relax=6), 660 if plate else 820)]
    raw = shell(sel, off, m, "boot", rim=False, relax=6)
    loops = border_loops(raw)
    if loops:
        lp = max(loops, key=lambda l: raw.V[l][:, 2].mean())
        parts.append(cord_on(raw, lp, 0.0065 if s.get("cuff") else 0.0035, trim, n=20, sides=4, name="cuff"))
    sole = lambda V: np.minimum.reduce([0.024 - V[:, 2], V[:, 0], 0.27 - np.abs(V[:, 0])])   # noqa: E731
    parts.append(simplify(shell(sole, 0.0138, pal(s.get("sole", "darkleather")), "sole", relax=6), 160))
    extra = []
    if plate:
        pm = WK.plate(plate)
        g = shell(_shin_front(0.15, top - 0.012), 0.0195, pm, "greave", relax=8)
        parts.append(simplify(g, 200))
        graw = shell(_shin_front(0.15, top - 0.012), 0.0195, pm, "greave", rim=False, relax=8)
        gl = border_loops(graw)
        if gl:
            parts.append(cord_on(graw, max(gl, key=len), 0.0032, trim, n=16, name="greave_trim"))
        for i, (y0, y1) in enumerate(((-0.17, -0.12), (-0.125, -0.075), (-0.08, -0.03))):
            lame = shell(_instep(y0, y1, 0.03 + 0.012 * i), 0.0185 + 0.001 * i, pm, "lame", relax=5)
            parts.append(rigid(simplify(lame, 70), "foot.L"))
    for z in ((0.16, 0.26) if s.get("straps") else ()):
        if z < top - 0.03:
            extra.append(_leg_ring(z, 0.016, pal(s["straps"]), 0.0045))
            cx, cy = _leg_axis(z)
            _, _, rx, _ = WK.leg_section(z)
            extra.append(K.box(0.008, 0.016, 0.018, (cx + rx + 0.017, cy - 0.01, z), trim, 0.002))
    if s.get("wings"):
        o = [(0.0, 0.0), (0.05, 0.055), (0.018, 0.045), (0.045, 0.085), (-0.008, 0.03)]
        cx, cy = _leg_axis(top - 0.06)
        _, _, rx, _ = WK.leg_section(top - 0.06)
        extra.append(K.slab(o, 0.005, pal(s["wings"]), axis="x").move((cx + rx + 0.02, cy + 0.01, top - 0.09)))
    if s.get("glow"):
        z = min(top - 0.05, 0.3)
        cx, cy = _leg_axis(z)
        H = WK.leg_section(z)
        y = cy - H[3] - (0.024 if plate else 0.016)
        extra.append(K.gem((cx, y, z), 0.011, pal(s["glow"]), rot=(90, 0, 0)))
    out = parts + (attach(extra, bones=["shin.L"], k=6) if extra else [])
    # within the boot budget (1,600 a foot): what is over comes off the upper, the densest part
    over = sum(tris_of(p) for p in out) - 1480
    if over > 0:
        out[0] = simplify(out[0], max(360, tris_of(out[0]) - over))
    return out


def _boot_item(id):
    @item(id, hide={"boot": [-1.0, round(boot_top(id) - 0.015, 3)]}, sides=True)
    def fn():
        return _boot(id)
    return fn


# ---- jewellery --------------------------------------------------------------------------------------------------------
# Rings on the fist's middle finger (left slots on the left hand, right on the right), pendants on the breastbone over
# whatever is worn, charms hanging from the left hip. Built from the item models' own parts.
RING_AT = (0.829, -0.018, 1.426)
PENDANT_AT = (0.0, -0.172, 1.37)


def _ring_worn(id):
    s = spec_of(id)
    src = [p for p in G.ring(dict(s))]
    for p in src:
        p.mat = pal(p.mat)
    # item: band round the Y axis, stone on top (+Z) at z = 0.024, the band's centre at z = 0.011
    for p in src:
        p.move((0.0, 0.0, -0.011))
        p.rot(Rx(90.0))                  # band now round the Z axis, the stone toward -Y
        p.rot(Rz(-90.0))                 # the stone toward +X: the front of the fist
        p.scale((0.95, 0.95, 0.95))
        p.move(RING_AT)
    out = attach(src, bone="hand.L", keys=False)
    total = sum(tris_of(p) for p in out)
    return [simplify(p, max(12, int(tris_of(p) * 260 / total))) for p in out] if total > 270 else out


def _neck_chain(mat, r=0.0022):
    P = [(0.0, 0.062, 1.548), (0.058, 0.03, 1.548), (0.083, -0.03, 1.525), (0.078, -0.098, 1.47), (0.048, -0.15, 1.415),
         (0.0, -0.168, 1.395), (-0.048, -0.15, 1.415), (-0.078, -0.098, 1.47), (-0.083, -0.03, 1.525), (-0.058, 0.03, 1.548),
         (0.0, 0.062, 1.548)]
    return K.tube(P, [r] * len(P), mat, n=5, up=(0, 0, 1), cap=False, name="chain")


def _pendant_worn(id):
    s = spec_of(id)
    src = [p for p in G.amulet(dict(s)) if p.name != "tube" or len(p.V) < 40]
    src = [p for p in src if not (p.name == "tube" and p.V[:, 1].max() > 0.06)]
    for p in src:
        p.mat = pal(p.mat)
    c = np.vstack([p.V for p in src]).mean(0)
    for p in src:
        p.move(-c)
        p.rot(Rx(90.0))                  # the face (+Z) toward -Y
        p.scale((1.25, 1.25, 1.25))
        p.move(PENDANT_AT)
    chain = _neck_chain(pal(s.get("chain", s.get("mat", "gold"))))
    out = attach(src, bone="chest", keys=False)
    total = sum(tris_of(p) for p in out)
    if total > 180:
        out = [simplify(p, max(8, int(tris_of(p) * 180 / total))) for p in out]
    return out + attach([chain], bone="chest", keys=False)


def _charm_worn(id):
    s = spec_of(id)
    src = [p for p in G.charm(dict(s))]
    for p in src:
        p.mat = pal(p.mat)
    c = np.vstack([p.V for p in src]).mean(0)
    at = (0.172, -0.118, 0.95)
    for p in src:
        p.move(-c)
        p.rot(Rx(90.0))
        p.rot(Rz(-28.0))
        p.scale((1.2, 1.2, 1.2))
        p.move(at)
    cordp = K.tube([(0.165, -0.112, 1.05), (0.17, -0.118, 1.0), (0.172, -0.12, 0.985)], [0.0018] * 3, pal(s.get("cord", "leather")), n=5)
    return attach(src + [cordp], bones=["hips", "thigh.L"], keys=False)


def _jewel_item(id):
    kind = G.GEAR[id][0].__name__
    if kind == "ring":
        @item(id, sides=True)
        def fn():
            return _ring_worn(id)
    elif kind == "amulet":
        @item(id)
        def fn():
            return _pendant_worn(id)
    else:
        @item(id)
        def fn():
            return _charm_worn(id)
    return fn


HELMS = ["iron_helm", "barbute_helm", "visored_greathelm", "guardian_helm", "linen_hood", "arcanist_cowl", "seers_circlet", "sage_hood",
         "depth_deepwarden_crown", "depth_prismkeeper_crown", "depth_vaultpath_crown", "depth_gloomthread_crown"]
GLOVES = ["iron_gauntlet", "spiked_gauntlet", "silk_glove", "runed_glove", "guardian_gauntlets", "sage_gloves", "depth_deepwarden_grips",
          "depth_prismkeeper_grips", "depth_vaultpath_grips", "depth_gloomthread_grips"]
BOOTS = ["iron_sabaton", "warden_greave", "soft_boot", "wayfarer_boot", "guardian_greaves", "sage_boots", "depth_deepwarden_treads",
         "depth_prismkeeper_treads", "depth_vaultpath_treads", "depth_gloomthread_treads"]
JEWELS = ["copper_ring", "silver_ring", "sigil_ring", "u_band_of_stillness", "bone_amulet", "gold_amulet", "star_pendant",
          "u_heart_of_aether", "rune_charm", "war_talisman"]
ALL = HELMS + GLOVES + BOOTS + JEWELS

for _id in GLOVES:
    _glove_item(_id)
for _id in BOOTS:
    _boot_item(_id)
for _id in JEWELS:
    _jewel_item(_id)
