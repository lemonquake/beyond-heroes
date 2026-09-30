"""bh-026: the Ember Dragon set worn by the hero — the Ember Dragonhide cuirass.

The source is the sculpted model in models/special_weapons/dragonforge_ember_dragonhide.obj (Y up, 1 unit tall, made
for a figure with its arms hanging at its sides). It is fitted to the hero here, not rebuilt. Because the sculpt's
pauldrons and the blades hanging from them sit where a lowered arm is, the cuirass is fitted to the hero standing in
the game's own idle pose (BIND_CLIP) and then carried back to the rig's T-pose:

  1. the body is posed with the idle clip (linear blend skinning of hero_mesh.npz by the clip's bone matrices);
  2. the sculpt is reduced to the armour budget, scaled and placed on the posed trunk, and its centre line is moved
     onto the body's band by band (the sculpt leans back a little; the hero stands straight);
  3. it is pushed out of the posed skin: every vertex at least GAP outside it, a push carrying the plate round it
     along so plates are lifted whole instead of being flattened onto the body;
  4. every vertex takes the skin weights (and build shape keys) of the nearest posed skin, smoothed over the mesh;
  5. inverse skinning with those weights and the idle bone matrices gives the rest (T-pose) position — so in the
     game's idle the cuirass is exactly the fitted sculpt, and the pauldrons ride the upper arms everywhere else.

Two materials: the plates take the dragon-scale texture set (BH_DragonPlate, dark ember red); what stands proud of the
plates — ridges, spikes, horns, the dragon heads on the pauldrons — is bronze (BH_Gold).
"""
import os

import numpy as np

import hero_wear_kit as WK
from hero_wear_kit import item, pal, BONES

SRC_DIR = os.path.join(WK.ROOT, "models", "special_weapons")
HIDE_SRC = os.path.join(SRC_DIR, "dragonforge_ember_dragonhide.obj")

BIND_CLIP = "idle"               # the pose the sculpt is fitted in (tools/blender/characters/bh_library.py)
BIND_FRAME = 0
# placement (metres, hero space: Z up, the hero faces -Y, his left is +X)
SCALE = (0.84, 0.88, 0.76)       # x across, y front to back, z up (the source is 1 unit tall)
LIFT = 0.79                      # height of the source's bottom edge (relative to the rest pose's hips)
GAP = 0.010                      # the least distance kept between a plate and the skin
PUSH_RADIUS = 0.035              # a push out of the skin carries the plate round it (metres)
MAX_TRIS = 6800                  # the armour budget is 7,200 (tests/unit/test_bh023.gd)
RELIEF = 0.004                   # faces standing proud of the smoothed cuirass are bronze trim: at least this far,
TRIM_SHARE = 0.22                # and at most this share of the faces (the most proud)
ARM_FROM = 1.16                  # (posed) height above which the cuirass may follow the upper arms

SCALE_PAL = None
TRIM_PAL = None


def palettes():
    global SCALE_PAL, TRIM_PAL
    if SCALE_PAL is None:
        SCALE_PAL = pal("ember_scale", "BH_DragonPlate", WK.srgb("6a2016"), 0.45, 0.42)
        TRIM_PAL = pal("ember_bronze", "BH_Gold", WK.srgb("c47a30"), 0.6, 0.36)
    return SCALE_PAL, TRIM_PAL


# ---- source -----------------------------------------------------------------------------------------------------------
def read_obj(path):
    """Vertices (Blender axes: Z up, -Y front), faces and per-vertex colours (or None) of a Wavefront OBJ."""
    V, C, F = [], [], []
    with open(path) as f:
        for line in f:
            if line.startswith("v "):
                p = line.split()
                x, y, z = float(p[1]), float(p[2]), float(p[3])
                V.append((x, -z, y))
                if len(p) >= 7:
                    C.append((float(p[4]), float(p[5]), float(p[6])))
            elif line.startswith("f "):
                F.append(tuple(int(t.split("/")[0]) - 1 for t in line.split()[1:]))
    return np.array(V, float), F, (np.array(C, float) if len(C) == len(V) else None)


def load_mesh(path, max_tris=0):
    """read_obj, reduced (Blender's collapse decimation) to at most max_tris triangles when given."""
    V, F, C = read_obj(path)
    tris = sum(len(f) - 2 for f in F)
    if not max_tris or tris <= max_tris:
        return V, F, C
    import bpy
    me = bpy.data.meshes.new("src")
    me.from_pydata(V.tolist(), [], F)
    me.validate()
    ob = bpy.data.objects.new("src", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("reduce", "DECIMATE")
    mod.ratio = max_tris / tris * 0.99
    mod.use_collapse_triangulate = True
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    red = bpy.data.meshes.new_from_object(ev)
    V2 = np.array([v.co[:] for v in red.vertices], float)
    F2 = [tuple(p.vertices) for p in red.polygons]
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    bpy.data.meshes.remove(red)
    return V2, F2, None


def _neighbours(n, F):
    nb = [set() for _ in range(n)]
    for f in F:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            nb[a].add(b)
            nb[b].add(a)
    return [np.fromiter(s, int) if s else np.array([i]) for i, s in enumerate(nb)]


def _vertex_normals(V, F):
    N = np.zeros_like(V)
    for f in F:
        for i in range(1, len(f) - 1):
            a, b, c = V[f[0]], V[f[i]], V[f[i + 1]]
            n = np.cross(b - a, c - a)
            N[[f[0], f[i], f[i + 1]]] += n
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


# ---- the posed body ---------------------------------------------------------------------------------------------------
class _Pose:
    """Skinning matrices (4x4, armature space) of the hero's bones in the bind pose, and the body posed with them."""

    def __init__(self):
        import bpy
        import bh_anim as A
        import bh_library as L
        import bh_skeleton as S
        import hero_conform as HC
        arm, _ = S.build_armature(HC.PROPS, "BindArmature")
        lib = {a.name: a for a in L.library()}
        # bake_action replaces an action of the same name: keep one already baked (hero_wear.py preview)
        kept = bpy.data.actions.get(BIND_CLIP)
        if kept:
            kept.name = "__kept_" + BIND_CLIP
        act = A.bake_action(arm, A.Rig(HC.PROPS), lib[BIND_CLIP])
        act.name = "__bind_" + BIND_CLIP
        if kept:
            kept.name = BIND_CLIP
        A.assign_action(arm, act)
        bpy.context.scene.frame_set(BIND_FRAME)
        bpy.context.view_layer.update()
        self.M = np.zeros((len(BONES), 4, 4))
        for bi, bn in enumerate(BONES):
            pb = arm.pose.bones[bn]
            self.M[bi] = np.array(arm.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted())
        arm.animation_data.action = None
        bpy.data.objects.remove(arm)
        bpy.data.actions.remove(act)
        b = WK.body()
        self.V = self.skin(b.V, b.W)
        R = np.einsum("vb,bij->vij", b.W, self.M[:, :3, :3])
        N = np.einsum("vij,vj->vi", R, b.N)
        self.N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        # the skin a cuirass may sit on and follow: never the forearms, hands, head or lower legs (in the idle pose
        # the hands hang beside the hips, right where the tassets are); the upper arms only above ARM_FROM
        mass = lambda names: b.W[:, [BONES.index(n) for n in names if n in BONES]].sum(1)
        away = mass(["forearm.L", "hand.L", "weapon.L", "forearm.R", "hand.R", "weapon.R", "head",
                     "shin.L", "foot.L", "toe.L", "shin.R", "foot.R", "toe.R"])
        arms = mass(["upper_arm.L", "upper_arm.R"])
        self.upper = np.nonzero(away < 0.3)[0]
        self.lower = np.nonzero((away < 0.3) & (arms < 0.3))[0]
        self.kd_upper = self._tree(self.upper)
        self.kd_lower = self._tree(self.lower)

    def _tree(self, idx):
        from mathutils.kdtree import KDTree
        kd = KDTree(len(idx))
        for n, i in enumerate(idx):
            kd.insert(self.V[i], n)
        kd.balance()
        return kd

    def near(self, v, k=1):
        """Nearest allowed skin: [(body vertex index, distance)] (k of them)."""
        up = v[2] > ARM_FROM
        kd, idx = (self.kd_upper, self.upper) if up else (self.kd_lower, self.lower)
        return [(int(idx[h[1]]), h[2]) for h in kd.find_n(tuple(v), k)]

    def skin(self, V, W):
        Mv = np.einsum("vb,bij->vij", W, self.M)
        return np.einsum("vij,vj->vi", Mv[:, :3, :3], V) + Mv[:, :3, 3]

    def unskin(self, V, W):
        Mv = np.einsum("vb,bij->vij", W, self.M)
        return np.array([np.linalg.solve(Mv[i, :3, :3], V[i] - Mv[i, :3, 3]) for i in range(len(V))])


# ---- fitting ----------------------------------------------------------------------------------------------------------
def _core_centre(P, z, half=0.06, band=0.02):
    """Middle of the front-to-back extent of the points near the centre line at height z (None if too few)."""
    s = (np.abs(P[:, 2] - z) < band) & (np.abs(P[:, 0]) < half)
    if s.sum() < 4:
        return None
    return 0.5 * (float(P[s, 1].min()) + float(P[s, 1].max()))


def _align(V, body_V):
    """Band by band, move the cuirass's centre line onto the body's (a smooth shift in y by height)."""
    zs = np.arange(V[:, 2].min(), V[:, 2].max() + 0.001, 0.02)
    trunk = body_V[np.abs(body_V[:, 0]) < 0.3]
    shift = []
    for z in zs:
        ca, cb = _core_centre(V, z), _core_centre(trunk, z)
        shift.append(np.nan if ca is None or cb is None else cb - ca)
    shift = np.array(shift)
    ok = ~np.isnan(shift)
    shift = np.interp(zs, zs[ok], shift[ok])
    k = 7
    shift = np.convolve(np.pad(shift, k // 2, mode="edge"), np.ones(k) / k, mode="valid")
    out = V.copy()
    out[:, 1] += np.interp(V[:, 2], zs, shift)
    return out


def _push_out(V, pose):
    """Keep every vertex at least GAP outside the posed skin; a push carries everything within PUSH_RADIUS along."""
    from mathutils.kdtree import KDTree
    for _ in range(8):
        need = np.zeros(len(V))
        dirs = np.zeros_like(V)
        for i, v in enumerate(V):
            j, dist = pose.near(v)[0]
            d = float(np.dot(v - pose.V[j], pose.N[j]))
            if d < GAP and dist < 0.12:
                need[i] = GAP - d
                dirs[i] = pose.N[j]
        if need.max() < 2e-4:
            break
        tree = KDTree(len(V))
        for i, v in enumerate(V):
            tree.insert(v, i)
        tree.balance()
        best = np.zeros(len(V))
        acc = np.zeros_like(V)
        for j in np.nonzero(need > 0)[0]:
            for co, i, r in tree.find_range(tuple(V[j]), PUSH_RADIUS):
                c = need[j] * (1.0 - r / PUSH_RADIUS)
                acc[i] += dirs[j] * c
                best[i] = max(best[i], c)
        ln = np.linalg.norm(acc, axis=1, keepdims=True)
        V = V + np.where(ln > 1e-9, acc / np.maximum(ln, 1e-9), 0.0) * best[:, None] * 1.05
    return V


def _weights(V, F, pose, k=8, smooth=3):
    """Skin weights and build-key deltas of the nearest posed skin, smoothed over the mesh."""
    b = WK.body()
    W = np.zeros((len(V), len(BONES)))
    D = np.zeros((b.D.shape[0], len(V), 3))
    for i, v in enumerate(V):
        hits = pose.near(v, k)
        w = np.array([1.0 / (h[1] + 0.004) for h in hits])
        w /= w.sum()
        idx = [h[0] for h in hits]
        W[i] = (b.W[idx] * w[:, None]).sum(0)
        D[:, i] = (b.D[:, idx] * w[None, :, None]).sum(1)
    nb = _neighbours(len(V), F)
    for _ in range(smooth):
        W = np.array([0.5 * W[i] + 0.5 * W[nb[i]].mean(0) for i in range(len(V))])
        D = np.stack([np.array([0.5 * Dk[i] + 0.5 * Dk[nb[i]].mean(0) for i in range(len(V))]) for Dk in D], 0)
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    return W, D


def _relief(V, F, iters=30):
    """How far each vertex stands proud of a smoothed copy of the mesh (along its normal). Taubin smoothing (a shrink
    step and an inflate step) so the plates themselves do not count as standing proud of their own shrunken copy."""
    nb = _neighbours(len(V), F)
    S = V.copy()
    for _ in range(iters):
        for lam in (0.5, -0.53):
            S = S + lam * (np.array([S[nb[i]].mean(0) for i in range(len(S))]) - S)
    N = _vertex_normals(V, F)
    # the sculpt's faces may wind inwards: turn the normals to point away from the body's axis
    out = V - np.stack([np.zeros(len(V)), np.full(len(V), V[:, 1].mean()), V[:, 2]], 1)
    if float(np.einsum("ij,ij->i", N, out).mean()) < 0.0:
        N = -N
    return np.einsum("ij,ij->i", V - S, N)


_CACHE = {}


def dragonhide():
    """-> dict(rest, posed, F, W, D, trim): the fitted cuirass (rest = T-pose positions, posed = in BIND_CLIP)."""
    if "hide" in _CACHE:
        return _CACHE["hide"]
    pose = _Pose()
    V, F, _ = load_mesh(HIDE_SRC, MAX_TRIS)
    lo, hi = V.min(0), V.max(0)
    centre = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
    hi_ = BONES.index("hips")
    hips = np.array(WK.J["hips"][0], float)
    hips_posed = pose.M[hi_, :3, :3] @ hips + pose.M[hi_, :3, 3]
    V = (V - centre) * np.array(SCALE) + np.array([hips_posed[0], hips_posed[1], LIFT + hips_posed[2] - hips[2]])
    V = _align(V, pose.V)
    V = _push_out(V, pose)
    W, D = _weights(V, F, pose)
    rest = pose.unskin(V, W)
    relief = _relief(V, F)
    face = np.array([relief[list(f)].mean() for f in F])
    trim = face > max(RELIEF, float(np.quantile(face, 1.0 - TRIM_SHARE)))
    _CACHE["hide"] = dict(rest=rest, posed=V, F=F, W=W, D=D, trim=trim)
    return _CACHE["hide"]


@item("ember_dragonhide", hide={"z": [0.96, 1.40]}, skirt=0.80)
def ember_dragonhide():
    scale_m, trim_m = palettes()
    h = dragonhide()
    parts = []
    for flag, mat, nm in ((False, scale_m, "scales"), (True, trim_m, "trim")):
        fs = [f for f, t in zip(h["F"], h["trim"]) if t == flag]
        used = sorted({i for f in fs for i in f})
        remap = {o: n for n, o in enumerate(used)}
        parts.append(WK.WPart(h["rest"][used], [tuple(remap[i] for i in f) for f in fs], mat, h["W"][used],
                              h["D"][:, used], nm))
    return parts
