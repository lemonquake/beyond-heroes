"""bh-023: toolkit for the hero's worn equipment (hero_wear.py and its item modules).

A worn piece is a mesh skinned to the shared skeleton, so it bends with the body, carrying the body's build shape
keys (muscle, belly, build, rear), so it follows the body sliders. Two ways to make geometry:

  shell(select, offset, mat)      cloth cut from the body itself: the selected body faces pushed out along their
                                  normals. It fits by construction, bends exactly like the skin under it and follows
                                  every shape key. Use it for anything that lies on the body: shirts, hose, mail,
                                  gloves, under-layers.
  attach(parts, ...)              authored geometry (bh_mesh / item_kit / boss_regalia helpers, in the rest pose of
                                  the standard skeleton): skinned either rigidly to one bone (plates, helms) or by the
                                  weights of the nearest skin (skirts, sleeves, collars).

Space: metres, Z up, the hero faces -Y, his left is +X, exact T-pose (tools/blender/hero/README.md).
Materials: palette keys through pal() -> "<BH base>__it_hw_<key>"; the game lays the legend texture sets on the known
bases (mail, leather, wool, plate) through the box-projected UV map written here.
"""
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CHARS = os.path.join(ROOT, "tools", "blender", "characters")
ITEMS = os.path.join(ROOT, "tools", "blender", "items")
for _p in (HERE, CHARS, ITEMS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bh_mesh as M  # noqa: E402
import bh_skeleton as S  # noqa: E402
import item_kit as K  # noqa: E402
from bh_math import Rx, Ry, Rz  # noqa: E402,F401
import hero_conform as HC  # noqa: E402
import hero_shapes as SH  # noqa: E402

SCRATCH = os.path.join(ROOT, "work", "lemondev", "bh-023", "scratch")
OUT_DIR = os.path.join(ROOT, "game", "assets", "characters", "hero", "wear")
MANIFEST = os.path.join(OUT_DIR, "manifest.json")
J = S.joints(HC.PROPS)
BONES = [b for b in S.BONE_ORDER if b not in S.DEFORM_EXCLUDE]


# ---- the body -------------------------------------------------------------------------------------------------------
class _Body:
    def __init__(self):
        d = np.load(os.path.join(SCRATCH, "hero_mesh.npz"))
        self.V, self.T, self.N = d["V"], d["T"], d["N"]
        names = [str(b) for b in d["bones"]]
        W = d["W"]
        self.W = np.stack([W[:, names.index(b)] if b in names else np.zeros(len(self.V)) for b in BONES], 1)
        keys = [str(k) for k in d["keys"]]
        self.D = np.stack([d["deltas"][keys.index(k)] for k in SH.BODY_KEYS], 0)      # (4, n, 3)
        self._kd = None

    def kd(self):
        if self._kd is None:
            from mathutils.kdtree import KDTree
            kd = KDTree(len(self.V))
            for i, v in enumerate(self.V):
                kd.insert(v, i)
            kd.balance()
            self._kd = kd
        return self._kd


_BODY = None


def body():
    global _BODY
    if _BODY is None:
        _BODY = _Body()
    return _BODY


def step(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ---- regions of the body -----------------------------------------------------------------------------------------------
# A region is a field over the body's vertices (rest pose): positive inside, negative outside, in metres from its
# edge. shell() cuts the skin exactly where the field crosses zero, so hems, cuffs and necklines come out as clean
# lines instead of following the body's triangles. Combine regions with either() / both_of() / without().
def trunk(V, z0=0.84, z1=1.53):
    """The torso between two heights, out to the arms' roots."""
    xlim = np.where(V[:, 2] > 1.36, 0.255, 0.215)
    return np.minimum.reduce([V[:, 2] - z0, z1 - V[:, 2], xlim - np.abs(V[:, 0])])


def arms(V, x0=0.20, x1=0.74):
    """Both arms between two distances from the centre line."""
    ax = np.abs(V[:, 0])
    return np.minimum.reduce([ax - x0, x1 - ax, V[:, 2] - 1.25])


def legs(V, z0=0.10, z1=0.92):
    return np.minimum.reduce([V[:, 2] - z0, z1 - V[:, 2], 0.27 - np.abs(V[:, 0])])


def hand(V, side=1.0, x0=0.70):
    return np.minimum(V[:, 0] * side - x0, V[:, 2] - 1.25)


def foot(V, side=1.0, z1=0.16):
    return np.minimum.reduce([z1 - V[:, 2], V[:, 0] * side, 0.27 - np.abs(V[:, 0])])


def either(*fields):
    return np.maximum.reduce(fields)


def both_of(*fields):
    return np.minimum.reduce(fields)


def without(field, cut):
    return np.minimum(field, -cut)


# ---- measurements -----------------------------------------------------------------------------------------------------
def torso_row(z, grow=0.015, band=0.014):
    """(z, half width, front depth, back depth) of the trunk at height z, grown by `grow` — a row for regalia-style
    lofts (boss_regalia.shell / srow)."""
    b = body()
    m = (np.abs(b.V[:, 2] - z) < band) & (np.abs(b.V[:, 0]) < (0.27 if z > 1.36 else 0.215))
    if m.sum() < 4:
        return (z, 0.16 + grow, 0.13 + grow, 0.10 + grow)
    P = b.V[m]
    return (z, float(np.abs(P[:, 0]).max()) + grow, float(-P[:, 1].min()) + grow, float(P[:, 1].max()) + grow)


def neck_row(z, grow=0.010, band=0.012):
    """(z, half width, front depth, back depth, 0, centre y) of the neck at height z — a row for a collar."""
    b = body()
    m = (np.abs(b.V[:, 2] - z) < band) & (np.abs(b.V[:, 0]) < 0.11)
    P = b.V[m]
    cy = float(P[:, 1].min() + P[:, 1].max()) / 2
    return (z, float(np.abs(P[:, 0]).max()) + grow, float(cy - P[:, 1].min()) + grow, float(P[:, 1].max() - cy) + grow, 0.0, cy)


def arm_section(x, band=0.016):
    """(centre y, centre z, radius y, radius z) of the left arm at distance x from the centre line."""
    b = body()
    m = (np.abs(b.V[:, 0] - x) < band) & (b.V[:, 2] > 1.25)
    if m.sum() < 3:
        return (0.0, 1.44, 0.05, 0.05)
    P = b.V[m]
    return (float(P[:, 1].min() + P[:, 1].max()) / 2, float(P[:, 2].min() + P[:, 2].max()) / 2,
            float(P[:, 1].max() - P[:, 1].min()) / 2, float(P[:, 2].max() - P[:, 2].min()) / 2)


def leg_section(z, band=0.018):
    """(centre x, centre y, radius x, radius y) of the left leg at height z."""
    b = body()
    m = (np.abs(b.V[:, 2] - z) < band) & (b.V[:, 0] > 0.0) & (b.V[:, 0] < 0.27)
    if m.sum() < 3:
        return (0.10, 0.0, 0.06, 0.06)
    P = b.V[m]
    return (float(P[:, 0].min() + P[:, 0].max()) / 2, float(P[:, 1].min() + P[:, 1].max()) / 2,
            float(P[:, 0].max() - P[:, 0].min()) / 2, float(P[:, 1].max() - P[:, 1].min()) / 2)


# ---- palette ----------------------------------------------------------------------------------------------------------
def pal(key, base=None, rgb=None, metallic=None, rough=None, emission=None, estr=0.0):
    """A palette key for worn gear. With only `key`, copies item_kit.MAT[key] (the item models' palette), so a worn
    piece shares its item's colours; pass the other arguments to define a new one. Returns the key to give parts."""
    hk = "hw_" + key
    if hk in K.MAT and base is None:
        return hk
    if base is None:
        b0, rgb0, met0, rough0, erg0, estr0 = K.MAT[key]
        K.MAT[hk] = (b0, rgb0, met0, rough0, erg0, estr0)
    else:
        K.MAT[hk] = (base, tuple(rgb), 0.0 if metallic is None else metallic, 0.8 if rough is None else rough, emission, estr)
    return hk


def srgb(h):
    return tuple((int(h[i:i + 2], 16) / 255.0) ** 2.2 for i in (0, 2, 4))


def mail(key="mail", hexcol="c4c8d0"):
    """Riveted mail (the game lays its chainmail texture on BH_Mail). Kept bright and only part metallic: a fully
    metallic dark mail reads as black cloth under the game's night lighting."""
    return pal(key, "BH_Mail", srgb(hexcol), 0.65, 0.5)


# ---- parts ------------------------------------------------------------------------------------------------------------
class WPart:
    """Geometry ready to skin: V (n,3), F faces, mat palette key, W (n, len(BONES)), D (4, n, 3) build-key deltas."""

    def __init__(self, V, F, mat, W, D=None, name="part"):
        self.V = np.asarray(V, float)
        self.F = [tuple(int(i) for i in f) for f in F]
        self.mat = mat
        self.W = np.asarray(W, float)
        self.D = np.zeros((len(SH.BODY_KEYS), len(self.V), 3)) if D is None else np.asarray(D, float)
        self.name = name

    def mirrored(self):
        V = self.V * np.array([-1.0, 1.0, 1.0])
        F = [tuple(reversed(f)) for f in self.F]
        W = np.zeros_like(self.W)
        for i, b in enumerate(BONES):
            W[:, BONES.index(M.swap_lr(b))] = self.W[:, i]
        D = self.D * np.array([-1.0, 1.0, 1.0])
        return WPart(V, F, self.mat, W, D, self.name)


def shell(select, offset=0.006, mat="hw_wool", name="shell", rim=True, sink=0.004, relax=0):
    """Cloth cut from the body: the skin inside the region `select` (a field, see "regions"; a function of the body's
    vertices or an array) pushed out by `offset` (a number or a function of the body's vertices). The skin is cut
    exactly along the region's edge. `rim` closes the open edges back under the skin so no gap shows. `relax` smooths
    the cloth that many times before it is pushed out (thick cloth, shoes: hides toes and muscle detail)."""
    b = body()
    f = select(b.V) if callable(select) else np.asarray(select)
    f = np.where(f, 1.0, -1.0) if f.dtype == bool else f.astype(float)
    off = offset(b.V) if callable(offset) else np.full(len(b.V), float(offset))
    ins = f > 0.0
    P, Nn, Wn, On = [], [], [], []
    Dn = [[] for _ in range(b.D.shape[0])]
    index = {}

    def vert(i):
        if i not in index:
            index[i] = len(P)
            P.append(b.V[i])
            Nn.append(b.N[i])
            Wn.append(b.W[i])
            On.append(off[i])
            for k in range(b.D.shape[0]):
                Dn[k].append(b.D[k, i])
        return index[i]

    def cut(i, j):
        key = (min(i, j), max(i, j))
        if key not in index:
            i0, j0 = key
            t = f[i0] / (f[i0] - f[j0])
            index[key] = len(P)
            P.append(b.V[i0] * (1 - t) + b.V[j0] * t)
            n = b.N[i0] * (1 - t) + b.N[j0] * t
            Nn.append(n / max(np.linalg.norm(n), 1e-9))
            Wn.append(b.W[i0] * (1 - t) + b.W[j0] * t)
            On.append(off[i0] * (1 - t) + off[j0] * t)
            for k in range(b.D.shape[0]):
                Dn[k].append(b.D[k, i0] * (1 - t) + b.D[k, j0] * t)
        return index[key]

    F = []
    for tri in b.T:
        n_in = int(ins[tri].sum())
        if n_in == 0:
            continue
        if n_in == 3:
            F.append((vert(tri[0]), vert(tri[1]), vert(tri[2])))
            continue
        for r in range(3):                      # rotate so the odd vertex comes first
            a_, b_, c_ = tri[r], tri[(r + 1) % 3], tri[(r + 2) % 3]
            if n_in == 1 and ins[a_]:
                F.append((vert(a_), cut(a_, b_), cut(a_, c_)))
                break
            if n_in == 2 and not ins[a_]:
                ab, ac = cut(a_, b_), cut(a_, c_)
                F.append((ab, vert(b_), vert(c_)))
                F.append((ab, vert(c_), ac))
                break
    if not F:
        raise ValueError("shell %s selects no skin" % name)
    base, Nn, W, off_v = np.array(P), np.array(Nn), np.array(Wn), np.array(On)
    D = np.array(Dn)
    if relax:
        # smooth the surface, then put it back outside the skin wherever smoothing pulled it in
        sm = _smooth(base, F, relax)
        inward = np.einsum("ij,ij->i", sm - base, Nn)
        sm = sm + Nn * np.maximum(-inward, 0.0)[:, None]
    else:
        sm = base
    V = sm + Nn * off_v[:, None]
    if rim:
        count = {}
        for fc in F:
            for a_, c_ in ((fc[0], fc[1]), (fc[1], fc[2]), (fc[2], fc[0])):
                count[(min(a_, c_), max(a_, c_))] = count.get((min(a_, c_), max(a_, c_)), 0) + 1
        inner = {}
        Vl, Wl = list(V), list(W)
        Dl = [list(D[k]) for k in range(D.shape[0])]
        for fc in list(F):
            for a_, c_ in ((fc[0], fc[1]), (fc[1], fc[2]), (fc[2], fc[0])):
                if count[(min(a_, c_), max(a_, c_))] != 1:
                    continue
                for v in (a_, c_):
                    if v not in inner:
                        inner[v] = len(Vl)
                        Vl.append(base[v] - Nn[v] * sink)
                        Wl.append(W[v])
                        for k in range(D.shape[0]):
                            Dl[k].append(D[k, v])
                F.append((c_, a_, inner[a_], inner[c_]))
        V, W, D = np.array(Vl), np.array(Wl), np.array(Dl)
    return WPart(V, F, mat, W, D, name)


def _transfer(V, k=6, bones=None):
    """Skin weights and build-key deltas of the nearest skin, for authored geometry."""
    b = body()
    kd = b.kd()
    W = np.zeros((len(V), len(BONES)))
    D = np.zeros((b.D.shape[0], len(V), 3))
    for i, v in enumerate(V):
        hits = kd.find_n(tuple(v), k)
        w = np.array([1.0 / (h[2] + 0.004) for h in hits])
        w /= w.sum()
        idx = [h[1] for h in hits]
        W[i] = (b.W[idx] * w[:, None]).sum(0)
        D[:, i] = (b.D[:, idx] * w[None, :, None]).sum(1)
    if bones is not None:
        keep = np.array([bn in bones for bn in BONES])
        W = W * keep[None]
        bad = W.sum(1) < 1e-6
        if bad.any():
            W[bad, BONES.index(bones[0])] = 1.0
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    return W, D


def _smooth(A, F, iters):
    n = len(A)
    nb = [set() for _ in range(n)]
    for f in F:
        for i in range(len(f)):
            nb[f[i]].add(f[(i + 1) % len(f)])
            nb[f[(i + 1) % len(f)]].add(f[i])
    idx = [np.fromiter(s, int) if s else np.array([i]) for i, s in enumerate(nb)]
    for _ in range(iters):
        A = np.array([0.5 * A[i] + 0.5 * A[idx[i]].mean(0) for i in range(n)])
    return A


def attach(parts, bone=None, bones=None, keys=True, k=6, smooth=2, weights=None):
    """Skin authored parts (one bh_mesh.Part or a list). Returns a list of WParts.

    bone="chest"         rigid: everything follows that bone (plates, helms, buckles)
    bone=None            soft: weights of the nearest skin, smoothed over the part (`bones` limits which bones count)
    weights=fn(V)        explicit weights: (n, len(BONES)) array, see skirt_weights()
    keys=False           ignore the body sliders (things on the head)
    """
    if not isinstance(parts, (list, tuple)):
        parts = [parts]
    out = []
    for p in parts:
        V = np.asarray(p.V, float)
        F = [tuple(f) for f in p.F]
        Wn, D = _transfer(V, k, bones) if (bone is None or keys) else (None, None)
        if weights is not None:
            W = weights(V)
        elif bone is not None:
            W = np.zeros((len(V), len(BONES)))
            W[:, BONES.index(bone)] = 1.0
        else:
            W = _smooth(Wn, F, smooth) if smooth else Wn
            W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
        if not keys:
            D = None
        elif smooth:
            D = np.stack([_smooth(D[i], F, smooth) for i in range(D.shape[0])], 0)
        out.append(WPart(V, F, p.mat, W, D, getattr(p, "name", "part")))
    return out


def skirt_weights(z_top=1.0, z_knee=0.51, z_bot=0.12, centre=0.05, leg=0.85):
    """Weights for a skirt or robe hanging from the hips: the hips hold the top, each thigh carries its side (up to
    `leg` of the weight) further down, the shins take over below the knees. `centre` = half width of the blend
    between the two legs."""
    ih, tl, tr, sl, sr = (BONES.index(n) for n in ("hips", "thigh.L", "thigh.R", "shin.L", "shin.R"))

    def fn(V):
        W = np.zeros((len(V), len(BONES)))
        t = np.clip((z_top - V[:, 2]) / max(z_top - z_knee, 1e-6), 0.0, 1.0)         # 0 at the waist, 1 at the knees
        wl = leg * t ** 0.8
        sideL = step(-centre, centre, V[:, 0])
        low = np.clip((z_knee - V[:, 2]) / max(z_knee - z_bot, 1e-6), 0.0, 1.0) * 0.7   # share handed to the shins
        W[:, ih] = 1.0 - wl
        W[:, tl] = wl * sideL * (1 - low)
        W[:, tr] = wl * (1 - sideL) * (1 - low)
        W[:, sl] = wl * sideL * low
        W[:, sr] = wl * (1 - sideL) * low
        return W / W.sum(1, keepdims=True)
    return fn


def mirror(wparts):
    return [p.mirrored() for p in wparts]


def both(wparts):
    """The parts and their mirror image (pauldrons, sleeves authored on the left)."""
    return list(wparts) + mirror(wparts)


# ---- objects and export ---------------------------------------------------------------------------------------------
def box_uv(ob, tile=1.0):
    """Box-projected UVs in the rest pose (1 UV unit = `tile` metres): the game's tiling cloth / mail / plate
    textures need them."""
    import bmesh
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    k = 1.0 / tile
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        sgn = 1.0 if n[ax] >= 0 else -1.0
        for lp in f.loops:
            x, y, z = lp.vert.co
            if ax == 0:
                u, v = -sgn * y, z
            elif ax == 1:
                u, v = sgn * x, z
            else:
                u, v = x, sgn * y
            lp[uv].uv = (u * k + 0.13 * ax, v * k + 0.29 * ax)
    bm.to_mesh(me)
    bm.free()
    me.update()


def build_object(name, wparts, arm, sharp_angle=42.0):
    """One skinned mesh object from WParts: a surface per material, vertex groups, the four build shape keys."""
    import bpy
    order = sorted({p.mat for p in wparts})
    mats = K.make_materials([m for m in order if not m.startswith("raw:")])
    for m in order:
        if m.startswith("raw:"):          # a game material by its own name (BH_Cloth_Primary takes the wearer's tint)
            nm = m[4:]
            mats[m] = bpy.data.materials.get(nm) or bpy.data.materials.new(nm)
    Vs, Fs, mi, Ws, Ds, off = [], [], [], [], [], 0
    for p in wparts:
        Vs.append(p.V)
        Ws.append(p.W)
        Ds.append(p.D)
        for f in p.F:
            Fs.append(tuple(i + off for i in f))
            mi.append(order.index(p.mat))
        off += len(p.V)
    V = np.vstack(Vs)
    W = np.vstack(Ws)
    D = np.concatenate(Ds, 1)
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], Fs)
    me.validate(clean_customdata=False)
    for m in order:
        me.materials.append(mats[m])
    me.polygons.foreach_set("material_index", mi[:len(me.polygons)])
    me.shade_smooth()
    try:
        me.set_sharp_from_angle(angle=math.radians(sharp_angle))
    except Exception:
        pass
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    box_uv(ob)
    # at most four bones a vertex
    top = np.argsort(-W, 1)[:, :4]
    keep = np.zeros_like(W, bool)
    np.put_along_axis(keep, top, True, 1)
    W = np.where(keep & (W > 0.01), W, 0.0)
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    for bi, b in enumerate(BONES):
        idx = np.nonzero(W[:, bi] > 0)[0]
        if len(idx) == 0:
            continue
        g = ob.vertex_groups.new(name=b)
        for i in idx:
            g.add([int(i)], float(W[i, bi]), "REPLACE")
    ob.shape_key_add(name="Basis")
    for ki, kn in enumerate(SH.BODY_KEYS):
        kb = ob.shape_key_add(name=kn)
        kb.data.foreach_set("co", (V + D[ki]).ravel())
        kb.slider_min, kb.slider_max = -3.0, 6.0
        kb.value = 0.0                 # (a new key starts at 1.0)
    ob.parent = arm
    ob.modifiers.new("Armature", "ARMATURE").object = arm
    return ob


def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def export_glb(path, objects):
    """Armature + skinned meshes with shape keys, no animation. Retries: an open Godot editor may hold the file."""
    import bpy
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    for attempt in range(8):
        try:
            bpy.ops.export_scene.gltf(
                filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
                export_animations=False, export_def_bones=False, export_cameras=False, export_lights=False,
                export_skins=True, export_influence_nb=4, export_morph=True, export_morph_normal=True,
                export_vertex_color="NONE", export_extras=False, export_tangents=False)
            return
        except Exception as e:  # noqa: BLE001
            print("[wear] retry %s (%s)" % (os.path.basename(path), str(e).splitlines()[-1][:80]))
            time.sleep(1.5 + attempt)
    raise RuntimeError("could not write " + path)


# ---- registry ---------------------------------------------------------------------------------------------------------
REGISTRY = {}


def item(id, hide=None, hair="hide", sides=False):
    """Register a worn piece.

    The function returns a list of WParts (for `sides=True` pieces — gloves, boots, rings — the LEFT side only: the
    right is mirrored from it and the GLB holds two meshes, wear_L and wear_R).
    hide: the body under the piece that the skin shader cuts away, in rest-pose metres:
          {"z": [z0, z1], "z2": [z0, z1]} heights of the trunk and legs, {"sleeve": [x0, x1]} distance along both arms,
          {"glove": [x0, x1]} / {"boot": [z0, z1]} for sided pieces. Leave a margin inside the garment's openings.
    hair: helms only, "hide" or "keep" (open crowns, circlets).
    """
    def deco(fn):
        REGISTRY[id] = dict(fn=fn, hide=hide or {}, hair=hair, sides=sides)
        return fn
    return deco


def build_item(id, arm):
    """-> list of Blender objects for the piece (skinned to `arm`)."""
    spec = REGISTRY[id]
    parts = spec["fn"]()
    if spec["sides"]:
        return [build_object("wear_L", parts, arm), build_object("wear_R", mirror(parts), arm)]
    return [build_object("wear", parts, arm)]


def write_manifest(ids, fallback=None):
    data = {"items": {}, "fallback": {}}
    if os.path.exists(MANIFEST):
        try:
            with open(MANIFEST) as f:
                data = json.load(f)
        except Exception:
            pass
    for i in ids:
        spec = REGISTRY[i]
        data.setdefault("items", {})[i] = {"hide": spec["hide"], "hair": spec["hair"], "sides": spec["sides"]}
    if fallback:
        data["fallback"] = fallback
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(MANIFEST, "w") as f:
        json.dump(data, f, indent=1, sort_keys=True)


def export_items(ids, log=print):
    import bpy
    os.makedirs(OUT_DIR, exist_ok=True)
    report = {}
    for i in ids:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        arm, _ = S.build_armature(HC.PROPS, "Armature")
        obs = build_item(i, arm)
        tris = sum(tri_count(o) for o in obs)
        export_glb(os.path.join(OUT_DIR, i + ".glb"), [arm] + obs)
        report[i] = tris
        log("[wear] %-28s %5d tris" % (i, tris))
    write_manifest(ids)
    return report
