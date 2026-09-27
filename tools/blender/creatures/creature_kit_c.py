"""Shared kit for Builder C's bh-010 creatures (build_broodmother.py, build_mimic.py, build_war_totem.py).

Same conventions as build_wolf.py: Blender Z-up, the creature faces -Y (= +Z in Godot), origin on the ground under the
body, meters, 30 fps, clips in place. Differences from the wolf:
  * poses are evaluated as a world-space DELTA transform per bone (Xf with rotation, translation and uniform scale),
    so any bone may translate (mimic tongue) or scale (legs folding into the chest, abdomen pulses);
  * every clip bakes rotation + location + scale for every bone on every frame (no stale channels between clips);
  * rest frames are read back from Blender (bone.matrix_local), so bone rolls may be anything;
  * a generic planar leg solver (yaw about the body's up axis + 2-bone hinge IK + an end segment at a given pitch,
    with an FK "curl" blend) drives the spider's 8 legs and the mimic's 4 legs.
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHAR = os.path.join(HERE, "..", "characters")
for _p in (CHAR, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
ROOT_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CHAR_OUT = os.path.join(ROOT_DIR, "game", "assets", "characters")
META = os.path.join(CHAR_OUT, "creature_meta.json")
EVID = os.path.join(ROOT_DIR, "work", "lemondev", "bh-010", "evidence", "creatures")
COMPOSE = os.path.join(CHAR, "compose_sheets.py")

import numpy as np  # noqa: E402

FPS = 30
I3 = np.eye(3)
# names the game plays through its generic logic (length read from each model's own clip; never written to the meta)
GENERIC = {"idle", "idle_look", "walk", "run", "run_combat", "hit_light", "hit_heavy", "stagger_small", "knockback",
           "death", "death_back", "alert"}


# ------------------------------------------------------------------------------------------------ math
def Rx(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def Ry(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def Rz(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def R_axis(axis, a):
    axis = np.asarray(axis, float)
    n = np.linalg.norm(axis)
    if n < 1e-12 or abs(a) < 1e-12:
        return np.eye(3)
    x, y, z = axis / n
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


def unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def min_rot(a, b):
    """Smallest rotation taking direction a onto direction b."""
    a, b = unit(a), unit(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    s = np.linalg.norm(v)
    if s < 1e-9:
        if c > 0:
            return np.eye(3)
        p = np.cross(a, [1.0, 0, 0])
        if np.linalg.norm(p) < 1e-6:
            p = np.cross(a, [0, 1.0, 0])
        return R_axis(p, 180.0)
    return R_axis(v, math.degrees(math.atan2(s, c)))


def spine_rot(c, b):
    """yaw (+ = toward own left, about Z), pitch (+ = nose up, about -X), roll (about Y) channels of a body part."""
    return Rz(c.get(b + ".yaw", 0.0)) @ Rx(-c.get(b + ".pitch", 0.0)) @ Ry(c.get(b + ".roll", 0.0))


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def cyc(f, period, k=1.0, ph=0.0):
    return math.sin(2 * math.pi * (k * f / period + ph))


def pulse(f, f0, f1):
    """0 -> 1 -> 0 bump between frames f0 and f1."""
    if f <= f0 or f >= f1:
        return 0.0
    return math.sin(math.pi * (f - f0) / (f1 - f0))


# ------------------------------------------------------------------------------------------------ transforms
class Xf:
    """p -> s * R p + t (uniform scale)."""

    def __init__(self, R=None, t=None, s=1.0):
        self.R = np.eye(3) if R is None else np.asarray(R, float)
        self.t = np.zeros(3) if t is None else np.asarray(t, float)
        self.s = float(s)

    def __matmul__(self, o):
        return Xf(self.R @ o.R, self.s * (self.R @ o.t) + self.t, self.s * o.s)

    def apply(self, p):
        return self.s * (self.R @ np.asarray(p, float)) + self.t

    def inv(self):
        Ri = self.R.T
        return Xf(Ri, -(Ri @ self.t) / self.s, 1.0 / self.s)

    @staticmethod
    def about(R, c, s=1.0):
        c = np.asarray(c, float)
        return Xf(R, c - s * (R @ c), s)

    @staticmethod
    def move(t):
        return Xf(np.eye(3), t)


# ------------------------------------------------------------------------------------------------ rig
class Rig:
    """bones: {name: (head, tail, parent)}; parents precede children."""

    def __init__(self, bones, root="root"):
        self.ORDER = list(bones)
        self.H = {b: np.array(v[0], float) for b, v in bones.items()}
        self.T = {b: np.array(v[1], float) for b, v in bones.items()}
        self.PAR = {b: v[2] for b, v in bones.items()}
        self.root = root
        self.R0 = None

    def length(self, b):
        return float(np.linalg.norm(self.T[b] - self.H[b]))

    def rdir(self, b):
        return unit(self.T[b] - self.H[b])

    def parent_x(self, X, b):
        p = self.PAR[b]
        return X[p] if p else Xf()

    def fk(self, X, b, R=None, s=1.0, off=None, pivot=None):
        """X[b] = X[parent] @ move(off) @ about(R, pivot or head, s). R, off in armature (rest) axes."""
        L = Xf.about(I3 if R is None else R, self.H[b] if pivot is None else pivot, s)
        if off is not None:
            L = Xf.move(off) @ L
        X[b] = self.parent_x(X, b) @ L
        return X[b]

    def head(self, X, b):
        return X[b].apply(self.H[b])

    def tail(self, X, b):
        return X[b].apply(self.T[b])


def plane_leg(rig, X, Xp, bones, target, beta=70.0, curl=0.0, curl_ang=(-50.0, -160.0, 140.0), knee=1.0,
              coxa=None, scale=1.0, yaw_blend=None):
    """Planar leg: [coxa] -> A (upper) -> B (lower) -> C (end segment).
    The leg yaws about the parent's up axis (at the coxa head / A head) to face the foot target, the upper pair is a
    2-bone hinge IK and the end segment points `beta` degrees below the outward horizontal (tried +-, so the reach is
    always met). curl (0..1) blends the three hinge angles toward curl_ang (degrees in the leg plane, measured from
    the outward axis toward the body's up axis) and the yaw back to rest. scale shrinks the whole leg about its root.
    Rest bones must lie in the vertical plane through the first head. Returns the end-segment tail (world)."""
    first = coxa or bones[0]
    P = Xp.apply(rig.H[first])
    b = unit(Xp.R @ np.array([0.0, 0.0, 1.0]))
    tip_rest = rig.T[bones[2]] - rig.H[first]
    u0 = unit(np.array([tip_rest[0], tip_rest[1], 0.0]))
    ar = unit(Xp.R @ u0)
    v = np.asarray(target, float) - P
    vp = v - np.dot(v, b) * b
    if np.linalg.norm(vp) > 1e-4:
        a = unit(vp)
        yaw = math.degrees(math.atan2(np.dot(np.cross(ar, a), b), np.dot(ar, a)))
    else:
        yaw = 0.0
    yaw *= (1.0 - curl) if yaw_blend is None else yaw_blend
    Ryaw = R_axis(b, yaw)
    a = unit(Ryaw @ ar)
    Rp = Ryaw @ Xp.R
    if coxa:
        X[coxa] = Xf(Rp, P - Xp.s * (Rp @ rig.H[coxa]), Xp.s)
        F = X[coxa].apply(rig.T[coxa])
    else:
        F = P
    sc = Xp.s
    L1, L2, L3 = (rig.length(x) * sc for x in bones)
    t = np.asarray(target, float) - F
    tx, ty = float(np.dot(t, a)), float(np.dot(t, b))
    best = None
    for db in (0, -6, 6, -12, 12, -20, 20, -30, 30, -42, 42, -56):
        ph3 = -math.radians(beta + db)
        qx, qy = tx - L3 * math.cos(ph3), ty - L3 * math.sin(ph3)
        d = math.hypot(qx, qy)
        if abs(L1 - L2) + 1e-3 < d <= 0.995 * (L1 + L2):
            best = (ph3, qx, qy, d)
            break
    if best is None:
        ph3 = -math.radians(beta)
        qx, qy = tx - L3 * math.cos(ph3), ty - L3 * math.sin(ph3)
        d = min(max(math.hypot(qx, qy), abs(L1 - L2) + 2e-3), 0.995 * (L1 + L2))
    else:
        ph3, qx, qy, d = best
    base = math.atan2(qy, qx)
    al = math.acos(min(max((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1.0), 1.0))
    ph1 = base + knee * al
    kx, ky = L1 * math.cos(ph1), L1 * math.sin(ph1)
    qx, qy = d * math.cos(base), d * math.sin(base)
    ph2 = math.atan2(qy - ky, qx - kx)
    phis = [ph1, ph2, ph3]
    if curl > 0:
        phis = [p + curl * wrap(math.radians(ca) - p) for p, ca in zip(phis, curl_ang)]
    head = F
    for bn, ph in zip(bones, phis):
        d3 = math.cos(ph) * a + math.sin(ph) * b
        Rw = min_rot(Rp @ rig.rdir(bn), d3) @ Rp
        X[bn] = Xf(Rw, head - sc * (Rw @ rig.H[bn]), sc)
        head = head + rig.length(bn) * sc * d3
    if scale != 1.0:
        S = Xf.about(I3, P, scale)
        for bn in ([coxa] if coxa else []) + list(bones):
            X[bn] = S @ X[bn]
        head = S.apply(head)
    return head


# ------------------------------------------------------------------------------------------------ clips
class Clip:
    def __init__(self, name, frames, loop=False, **meta):
        self.name, self.frames, self.loop, self.meta = name, frames, loop, meta
        self.keys = []
        self.layers = []

    def key(self, f, **ch):
        self.keys.append((f, {k.replace("_", "."): v for k, v in ch.items()}))
        return self

    def layer(self, fn):
        self.layers.append(fn)
        return self

    def channels(self, f):
        keys = sorted(self.keys, key=lambda k: k[0])
        names = set()
        for _, d in keys:
            names.update(d)
        out = {}
        for n in names:
            pts = [(kf, d[n]) for kf, d in keys if n in d]
            if pts[0][0] > keys[0][0]:      # the first key implicitly holds every channel at 0
                pts.insert(0, (keys[0][0], 0.0))
            if f <= pts[0][0]:
                out[n] = pts[0][1]
                continue
            if f >= pts[-1][0]:
                out[n] = pts[-1][1]
                continue
            for (f0, v0), (f1, v1) in zip(pts, pts[1:]):
                if f0 <= f <= f1:
                    out[n] = v0 + (v1 - v0) * smooth((f - f0) / max(f1 - f0, 1e-6))
                    break
        for fn in self.layers:
            for kk, v in fn(f, self).items():
                out[kk] = out.get(kk, 0.0) + v
        return out


def gait_foot(u, duty, sweep, lift):
    """u: phase since touch-down (0..1). Returns (forward offset, lift, swing 0..1 or -1 in stance)."""
    u %= 1.0
    if u < duty:
        s = u / duty
        return sweep / 2 - sweep * s, 0.0, -1.0
    s = (u - duty) / (1 - duty)
    return -sweep / 2 + sweep * smooth(s), lift * math.sin(math.pi * s) ** 0.8, s


# ------------------------------------------------------------------------------------------------ skinning
def seg_dist(V, a, b):
    ab = b - a
    t = np.clip(((V - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(V - (a + t[:, None] * ab), axis=1)


def dist_weights(rig, V, bones, power=6.0, top=3, bias=None, floor=0.02):
    D = []
    for b in bones:
        d = seg_dist(V, rig.H[b], rig.T[b]) + 0.012
        if bias and b in bias:
            d = d * bias[b]
        D.append(d)
    D = np.stack(D, 1)
    W = 1.0 / D ** power
    out = []
    for row in W:
        idx = np.argsort(-row)[:top]
        s = row[idx].sum()
        out.append({bones[i]: float(row[i] / s) for i in idx if row[i] / s > floor})
    return out


def chain_weights(rig, V, bones, blend=0.35):
    """Weights along a chain by projection parameter: each vertex belongs to the bone segment it projects onto, with a
    linear cross-fade of `blend` (fraction of the shorter neighbour) around every joint. Used for tubes that must bend
    smoothly (legs, tongue, cords)."""
    P = [rig.H[bones[0]]] + [rig.T[b] for b in bones]
    lens = [np.linalg.norm(P[i + 1] - P[i]) for i in range(len(bones))]
    cum = np.concatenate([[0.0], np.cumsum(lens)])
    out = []
    for v in V:
        # nearest segment -> global arc parameter
        best, bs = 1e9, 0.0
        for i in range(len(bones)):
            a, b = P[i], P[i + 1]
            ab = b - a
            t = min(max(float(np.dot(v - a, ab) / max(np.dot(ab, ab), 1e-12)), 0.0), 1.0)
            dd = np.linalg.norm(v - (a + t * ab))
            if dd < best - 1e-9:
                best, bs = dd, cum[i] + t * lens[i]
        w = {}
        for j in range(len(bones)):
            lo, hi = cum[j], cum[j + 1]
            wl = blend * min(lens[j], lens[j - 1] if j > 0 else lens[j]) * 0.5
            wh = blend * min(lens[j], lens[j + 1] if j + 1 < len(bones) else lens[j]) * 0.5
            # trapezoid membership
            if j == 0:
                a_ = 1.0
            else:
                a_ = min(max((bs - (lo - wl)) / max(2 * wl, 1e-6), 0.0), 1.0)
            if j == len(bones) - 1:
                b_ = 1.0
            else:
                b_ = min(max(((hi + wh) - bs) / max(2 * wh, 1e-6), 0.0), 1.0)
            m = min(a_, b_)
            if m > 1e-3:
                w[bones[j]] = m
        s = sum(w.values())
        out.append({k: x / s for k, x in w.items()})
    return out


def bind(part, rig=None, bone=None, bones=None, chain=None, blend=0.35, **kw):
    if bone:
        part.W = [{bone: 1.0}] * len(part.V)
    elif chain:
        part.W = chain_weights(rig, part.V, chain, blend)
    else:
        part.W = dist_weights(rig, part.V, bones, **kw)
    return part


# ------------------------------------------------------------------------------------------------ Blender side
def build_armature(rig, name="Armature"):
    import bpy
    arm = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for b in rig.ORDER:
        e = arm.edit_bones.new(b)
        e.head, e.tail = tuple(rig.H[b]), tuple(rig.T[b])
        d = rig.rdir(b)
        e.align_roll((0.0, 0.0, 1.0) if abs(d[2]) < 0.9 else (0.0, -1.0, 0.0))
        e.use_deform = b != rig.root
        if rig.PAR[b]:
            e.parent = eb[rig.PAR[b]]
            e.use_connect = False
        eb[b] = e
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in ob.pose.bones:
        pb.rotation_mode = "QUATERNION"
    arm.display_type = "STICK"
    rig.R0 = {b.name: np.array(b.matrix_local)[:3, :3] for b in ob.data.bones}
    for b in ob.data.bones:
        assert np.abs(np.array(b.matrix_local)[:3, 3] - rig.H[b.name]).max() < 1e-5, b.name
    return ob


def mat_to_quat(R):
    from mathutils import Matrix
    q = Matrix(R.tolist()).to_quaternion()
    return np.array([q.w, q.x, q.y, q.z])


def pose_basis(rig, X):
    """{bone: (quat wxyz, loc, scale)} pose-bone basis values for world deltas X."""
    out = {}
    for b in rig.ORDER:
        L = rig.parent_x(X, b).inv() @ X[b]
        R0 = rig.R0[b]
        q = mat_to_quat(R0.T @ L.R @ R0)
        loc = R0.T @ (L.apply(rig.H[b]) - rig.H[b])
        out[b] = (q, loc, L.s)
    return out


def bake(ob, rig, clip, evaluate):
    import bpy
    n = clip.frames + 1
    names = rig.ORDER
    quats = {b: np.zeros((n, 4)) for b in names}
    locs = {b: np.zeros((n, 3)) for b in names}
    scls = {b: np.ones(n) for b in names}
    for f in range(n):
        ff = f % clip.frames if clip.loop else f
        X = evaluate(clip.channels(float(ff)))
        B = pose_basis(rig, X)
        for b in names:
            q, loc, s = B[b]
            if f > 0 and np.dot(q, quats[b][f - 1]) < 0:
                q = -q
            quats[b][f] = q
            locs[b][f] = loc
            scls[b][f] = s
    act = bpy.data.actions.new(clip.name)
    act.use_fake_user = True
    slot = act.slots.new(id_type="OBJECT", name=ob.name)
    layer = act.layers.new("Layer")
    strip = layer.strips.new(type="KEYFRAME")
    cb = strip.channelbag(slot, ensure=True)
    frames = np.arange(n, dtype=float)

    def put(path, idx, vals):
        fc = cb.fcurves.new(path, index=idx)
        fc.keyframe_points.add(n)
        co = np.empty(2 * n)
        co[0::2] = frames
        co[1::2] = vals
        fc.keyframe_points.foreach_set("co", co)
        fc.keyframe_points.foreach_set("interpolation", [1] * n)
        fc.update()
    for b in names:
        for i in range(4):
            put(f'pose.bones["{b}"].rotation_quaternion', i, quats[b][:, i])
        for i in range(3):
            put(f'pose.bones["{b}"].location', i, locs[b][:, i])
        for i in range(3):
            put(f'pose.bones["{b}"].scale', i, scls[b])
    act.use_frame_range = True
    act.frame_start = 0
    act.frame_end = clip.frames
    act.use_cyclic = clip.loop
    return act


def assign(ob, act):
    ad = ob.animation_data or ob.animation_data_create()
    ad.action = act
    try:
        if ad.action_slot is None and len(act.slots):
            ad.action_slot = act.slots[0]
    except Exception:
        pass


def verify_pose(ob, rig, clip, act, evaluate, frames=(0, None)):
    """Blender's evaluated bone heads/tails == the numpy model (catches roll / basis mistakes)."""
    import bpy
    assign(ob, act)
    worst = 0.0
    for f in frames:
        f = clip.frames // 2 if f is None else f
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        X = evaluate(clip.channels(float(f % clip.frames if clip.loop else f)))
        for pb in ob.pose.bones:
            for got, want in ((pb.head, rig.head(X, pb.name)), (pb.tail, rig.tail(X, pb.name))):
                worst = max(worst, float(np.abs(np.array(got[:]) - want).max()))
    return worst


def build_all(cid, rig, evaluate, clips, mesh_fn, palette, only=None, ao=(16, 0.25, 0.6), sharp=45):
    import bpy
    import bh_mesh as M
    import bh_materials as MT
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    mats = MT.make_materials(cid, vertex_color=False, extra=palette)
    arm = build_armature(rig)
    parts = mesh_fn()
    mesh = M.build_skinned(cid, parts, arm, mats, sharp_angle=sharp)
    MT.bake_vertex_ao(mesh, rays=ao[0], dist=ao[1], strength=ao[2])
    acts = {}
    worst = 0.0
    for c in clips:
        if only and c.name not in only:
            continue
        act = bake(arm, rig, c, evaluate)
        acts[c.name] = (c, act)
        worst = max(worst, verify_pose(arm, rig, c, act, evaluate))
    print(f"[{cid}] numpy-vs-Blender pose check: worst bone head/tail error {worst * 1000:.3f} mm")
    assert worst < 2e-3, worst
    return arm, mesh, acts


def export(cid, arm, mesh, acts, path):
    import glb_export as GX
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = None
    for name, (c, act) in acts.items():
        tr = ad.nla_tracks.new()
        tr.name = name
        st = tr.strips.new(name, 0, act)
        try:
            st.action_slot = act.slots[0]
        except Exception:
            pass
        st.extrapolation = "NOTHING"
    for pb in arm.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    GX.export_glb(path, [arm, mesh])
    print(f"[{cid}] -> {path} ({os.path.getsize(path) / 1e6:.2f} MB)")
    bad, got = GX.check_lengths(path, {n: c.frames / FPS for n, (c, a) in acts.items()})
    print(f"[{cid}] check_lengths: {len(got)} animations in the GLB; mismatches: {bad}")
    for n, (c, a) in acts.items():
        print(f"[{cid}]   {n:16s} want {c.frames / FPS:6.3f}s got {got.get(n)}")
    for tr in list(ad.nla_tracks):
        ad.nla_tracks.remove(tr)
    return bad, got


def clip_entry(c):
    d = {"length": round(c.frames / FPS, 3), "loop": bool(c.loop)}
    if "hits" in c.meta:
        d["hits"] = [[round(a, 3), round(b, 3)] for a, b in c.meta["hits"]]
    if "ground_speed" in c.meta:
        d["ground_speed"] = c.meta["ground_speed"]
    return d


def merge_meta(cid, clips, generator, extra=None):
    """MERGE into creature_meta.json: add/replace only this model's prefixed clip keys under "animations" and its
    entry under "models"; every other key is kept as loaded (json indent=1, same as build_wolf.py)."""
    with open(META) as fh:
        data = json.load(fh)
    anims = data.setdefault("animations", {})
    for c in clips:
        if c.name in GENERIC:
            continue
        anims[c.name] = clip_entry(c)
    models = data.setdefault("models", {})
    info = {"generator": generator, "glb": f"res://assets/characters/{cid}.glb",
            "clips": {c.name: clip_entry(c) for c in clips}}
    info.update(extra or {})
    models[cid] = info
    with open(META, "w") as fh:
        json.dump(data, fh, indent=1)
    print(f"[{cid}] meta merged -> {META}")


# ------------------------------------------------------------------------------------------------ evidence renders
def _render(path):
    import bpy
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def compose(job, job_path):
    os.makedirs(os.path.dirname(job_path), exist_ok=True)
    with open(job_path, "w") as fh:
        json.dump(job, fh, indent=1)
    try:
        r = subprocess.run(["python", COMPOSE, job_path], capture_output=True, text=True, timeout=300)
        print(r.stdout.strip() or r.stderr.strip()[-400:])
    except Exception as e:      # compose later with system Python
        print("compose failed:", e, "job:", job_path)


def rest_pose(arm):
    ad = arm.animation_data
    if ad:
        ad.action = None
    for pb in arm.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)


def evidence_rest(cid, arm, tz, dist, title, res=420, iso_scales=(1.0,), pose=None, acts=None, base=None):
    """4 orthogonal-ish views + gameplay-camera iso (26 m, 55 deg pitch) per iso scale. pose: optional (clip, frame)."""
    import bpy
    import preview_enemy as PE
    PE.material_colors()
    cam = bpy.data.objects.get("Cam") or PE.setup(res)
    bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = res
    out = os.path.join(base or EVID, cid)
    tiles = os.path.join(out, "tiles")
    os.makedirs(tiles, exist_ok=True)
    tag = "rest"
    if pose:
        assign(arm, acts[pose[0]][1])
        bpy.context.scene.frame_set(pose[1])
        tag = f"{pose[0]}{pose[1]}"
    else:
        rest_pose(arm)
    paths, labels = [], []
    for v, nm in ((0, "front"), (90, "left side"), (180, "back"), (270, "right side"), (35, "3/4 front")):
        PE.place(cam, (0, 0, tz), dist, v, 10)
        paths.append(_render(os.path.join(tiles, f"{tag}_{v}.png")))
        labels.append(f"{nm} (yaw {v})")
    for s in iso_scales:
        arm.scale = (s, s, s)
        bpy.context.view_layer.update()
        PE.place(cam, (0, 0, 0.4 * s), 26.0, 20, 55)
        paths.append(_render(os.path.join(tiles, f"{tag}_iso_{int(s * 100)}.png")))
        labels.append(f"gameplay iso 26 m / 55 deg, scale {s}")
    arm.scale = (1, 1, 1)
    compose({"paths": paths, "labels": labels, "out": os.path.join(out, f"{cid}_{tag}.png"),
             "cols": 4 if len(paths) > 6 else len(paths), "title": title, "cell": res},
            os.path.join(tiles, f"job_{tag}.json"))


def evidence_clips(cid, arm, acts, spec, tz, dist, title, res=300, yaw=55, pitch=12, name="clips", cols=6,
                   base=None):
    """spec: [(clip, [normalized times])]. One labelled contact sheet."""
    import bpy
    import preview_enemy as PE
    PE.material_colors()
    cam = bpy.data.objects.get("Cam") or PE.setup(res)
    bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = res
    out = os.path.join(base or EVID, cid)
    tiles = os.path.join(out, "tiles")
    os.makedirs(tiles, exist_ok=True)
    paths, labels = [], []
    for cn, times in spec:
        c, act = acts[cn]
        assign(arm, act)
        for tt in times:
            f = int(round(tt * c.frames))
            bpy.context.scene.frame_set(f)
            PE.place(cam, (0, -0.1, tz), dist, yaw, pitch)
            paths.append(_render(os.path.join(tiles, f"{name}_{cn}_{f}.png")))
            hit = ""
            for h0, h1 in c.meta.get("hits", []):
                if h0 - 1e-3 <= f / FPS <= h1 + 1e-3:
                    hit = "  HIT"
            labels.append(f"{cn} f{f} {f / FPS:.2f}s{hit}")
    compose({"paths": paths, "labels": labels, "out": os.path.join(out, f"{cid}_{name}.png"), "cols": cols,
             "title": title, "cell": res}, os.path.join(tiles, f"job_{name}.json"))


def write_md(cid, title, lines):
    os.makedirs(os.path.join(EVID, cid), exist_ok=True)
    p = os.path.join(EVID, f"{cid}.md")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("\n".join([f"# {title}", ""] + lines) + "\n")
    print(f"[{cid}] notes -> {p}")


def clip_table(clips):
    rows = ["| clip | frames | length (s) | loop | hits (s) | ground_speed (m/s) |", "|---|---|---|---|---|---|"]
    for c in clips:
        hits = ", ".join(f"[{a:.3f}, {b:.3f}]" for a, b in c.meta.get("hits", [])) or "-"
        rows.append(f"| `{c.name}` | {c.frames} | {c.frames / FPS:.3f} | {'yes' if c.loop else 'no'} | {hits} | "
                    f"{c.meta.get('ground_speed', '-')} |")
    return rows


def std_args(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-export", action="store_true", help="skip GLB + meta")
    ap.add_argument("--evidence", action="store_true", help="render rest + clip contact sheets into the evidence dir")
    ap.add_argument("--clips", default="", help="only bake these clips (implies --no-export)")
    ap.add_argument("--sheet", default="", help="quick preview sheet of these clips (8 steps each) into --prev")
    ap.add_argument("--prev", default="", help="quick preview dir (rest views + --sheet clips, small renders)")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else (argv or [])
    return ap.parse_args(argv)


def quick_preview(cid, arm, acts, a, tz, dist, yaw=55, pitch=12, steps=8, res=200):
    """--prev DIR: small rest sheet + an 8-step sheet of each --sheet clip (for iteration, not evidence)."""
    if not a.prev:
        return
    evidence_rest(cid, arm, tz, dist, f"{cid} rest", res=res, base=a.prev)
    for cn in [x for x in a.sheet.split(",") if x and x in acts]:
        evidence_clips(cid, arm, acts, [(cn, [i / (steps - 1) for i in range(steps)])], tz, dist, cn, res=res,
                       yaw=yaw, pitch=pitch, name=f"q_{cn}", cols=steps, base=a.prev)


def foot_slide(clip, ev, feet_fn, ids, speed, floor):
    """Stance-foot slip vs the ideal in-place slide (+speed along +Y). Returns (max m/frame, mean, contact frac)."""
    P = []
    for f in range(clip.frames + 1):
        X = ev(clip.channels(float(f % clip.frames)))
        P.append({k: feet_fn(X, k) for k in ids})
    res = []
    cont = 0
    for f in range(clip.frames):
        for k in ids:
            a, b = P[f][k], P[f + 1][k]
            if a[2] < floor and b[2] < floor:
                cont += 1
                res.append(np.linalg.norm((b - a) - np.array([0.0, speed / FPS, 0.0])))
    return (max(res) if res else 0.0), (float(np.mean(res)) if res else 0.0), cont / (clip.frames * len(ids))


def orient(part, center, inward=False):
    """Flip faces of an open sheet so they face away from (or toward, inward=True) center."""
    F = []
    c0 = np.asarray(center, float)
    for f in part.F:
        a, b, c3 = part.V[f[0]], part.V[f[1]], part.V[f[2]]
        n = np.cross(b - a, c3 - a)
        out = np.dot(n, part.V[list(f)].mean(0) - c0) >= 0
        F.append(f if out != inward else tuple(reversed(f)))
    part.F = F
    return part


def hat_weights(V, joints, bones, tip_bone=None):
    """Linear 'hat' weights along a joint polyline: a vertex between joint j and j+1 gets (1-t) on bones[j] and t on
    bones[j+1]; past the last joint it belongs to tip_bone (or the last bone). With translating bones this gives an
    exact uniform stretch of the segment in between (used for the mimic's extending tongue)."""
    J = [np.asarray(j, float) for j in joints]
    out = []
    for v in V:
        best, seg, tt = 1e9, 0, 0.0
        for i in range(len(J) - 1):
            a, b = J[i], J[i + 1]
            ab = b - a
            t = min(max(float(np.dot(v - a, ab) / max(np.dot(ab, ab), 1e-12)), 0.0), 1.0)
            d = np.linalg.norm(v - (a + t * ab))
            if d < best - 1e-9:
                best, seg, tt = d, i, t
        if seg >= len(bones) - 1:
            out.append({tip_bone or bones[-1]: 1.0})
        else:
            w = {bones[seg]: 1.0 - tt, bones[seg + 1]: tt}
            out.append({k: x for k, x in w.items() if x > 1e-3})
    return out
