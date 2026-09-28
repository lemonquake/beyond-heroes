"""Shared machinery for the bh-013 Builder C creatures (gloam_ooze, tunnel_maw, stonegaze_basilisk,
shellback_grinder): generic rig (any bone hierarchy, rotation + local scale + head translation per bone), the
channel/keyframe Clip DSL, a numpy FK that mirrors Blender's pose evaluation (checked against Blender after baking),
a quadruped evaluator with the planar leg IK / gait machinery ported from build_rootback_boar.py / build_wolf.py
(those files are not modified), GLB export, creature_meta.json merge and Workbench evidence renders.

Conventions: Blender Z-up, the creature faces -Y (= +Z in Godot), origin on the ground, meters, 30 fps, in place.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CHAR = os.path.join(HERE, "..", "characters")
if CHAR not in sys.path:
    sys.path.insert(0, CHAR)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT_DIR = os.path.join(ROOT_DIR, "game", "assets", "characters")
OUT_META = os.path.join(OUT_DIR, "creature_meta.json")
EVID = os.path.join(ROOT_DIR, "work", "lemondev", "bh-013", "evidence", "models_creatures")
SCRATCH = os.path.join(ROOT_DIR, "work", "lemondev", "bh-013", "scratch", "creatures")
FPS = 30
GENERIC = ["idle", "idle_look", "walk", "run", "run_combat", "hit_light", "hit_heavy", "stagger_small", "knockback",
           "death", "death_back", "alert"]


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
    ax = np.asarray(axis, float)
    ax = ax / np.linalg.norm(ax)
    x, y, z = ax
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


def ang2(v):
    return math.atan2(v[2], v[1])


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def cyc(f, period, k=1.0, ph=0.0):
    return math.sin(2 * math.pi * (k * f / period + ph))


def damp(f, f0, freq, decay, amp=1.0):
    """Damped oscillation starting at frame f0 (0 before)."""
    if f < f0:
        return 0.0
    t = (f - f0) / FPS
    return amp * math.exp(-decay * t) * math.sin(2 * math.pi * freq * t)


def normalize(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def align_z(d, hint=(0, -1, 0)):
    """Rotation matrix taking +Z to direction d."""
    z = normalize(d)
    h = np.asarray(hint, float)
    if abs(np.dot(z, normalize(h))) > 0.95:
        h = np.array([1.0, 0, 0]) if abs(z[0]) < 0.9 else np.array([0, 1.0, 0])
    x = normalize(np.cross(h, z))
    y = np.cross(z, x)
    return np.stack([x, y, z], 1)


class Xf:
    def __init__(self, R=None, t=None):
        self.R = np.eye(3) if R is None else R
        self.t = np.zeros(3) if t is None else np.asarray(t, float)

    def __matmul__(self, o):
        return Xf(self.R @ o.R, self.R @ o.t + self.t)

    def apply(self, p):
        return self.R @ p + self.t

    def inv(self):
        Ri = np.linalg.inv(self.R)
        return Xf(Ri, -Ri @ self.t)

    @staticmethod
    def about(R, c):
        return Xf(R, c - R @ c)


# ------------------------------------------------------------------------------------------------ rig
class Rig:
    """bones: {name: (head, tail, parent)} with parents listed before children."""

    def __init__(self, bones):
        self.ORDER = list(bones)
        self.H = {b: np.array(v[0], float) for b, v in bones.items()}
        self.T = {b: np.array(v[1], float) for b, v in bones.items()}
        self.PAR = {b: v[2] for b, v in bones.items()}
        self.R0 = {}
        for b in self.ORDER:
            y = normalize(self.T[b] - self.H[b])
            z = np.array([1.0, 0, 0]) - y * y[0]
            if np.linalg.norm(z) < 1e-6:
                z = np.array([0, -1.0, 0])
            z /= np.linalg.norm(z)
            x = np.cross(y, z)
            self.R0[b] = np.stack([x, y, z], 1)

    def local_mat(self, b, R=None, S=None):
        """Armature-axis local delta: rotation R (armature axes) after a local scale S (bone axes)."""
        M = np.eye(3) if R is None else R
        if S is not None:
            M = M @ (self.R0[b] @ np.diag(S) @ self.R0[b].T)
        return M

    def fk_one(self, X, b, R=None, S=None, L=None):
        par = X[self.PAR[b]] if self.PAR[b] else Xf()
        t = Xf(np.eye(3), np.zeros(3) if L is None else L)
        X[b] = par @ t @ Xf.about(self.local_mat(b, R, S), self.H[b])
        return X[b]

    def fk(self, Rd, S=None, L=None, X=None):
        S = S or {}
        L = L or {}
        X = {} if X is None else X
        for b in self.ORDER:
            if b in X:
                continue
            self.fk_one(X, b, Rd.get(b), S.get(b), L.get(b))
        return X


def dist_weights(rig, V, bones, power=6.0, top=3, bias=None, floor=0.015):
    D = []
    for b in bones:
        a, c = rig.H[b], rig.T[b]
        ab = c - a
        t = np.clip(((V - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
        d = np.linalg.norm(V - (a + t[:, None] * ab), axis=1) + floor
        if bias and b in bias:
            d = d * bias[b]
        D.append(d)
    D = np.stack(D, 1)
    W = 1.0 / D ** power
    out = []
    for row in W:
        idx = np.argsort(-row)[:top]
        s = row[idx].sum()
        out.append({bones[i]: float(row[i] / s) for i in idx if row[i] / s > 0.02})
    return out


# ------------------------------------------------------------------------------------------------ clips
class Clip:
    def __init__(self, name, frames, loop=False, **meta):
        self.name, self.frames, self.loop, self.meta = name, frames, loop, meta
        self.keys = []
        self.layers = []

    def key(self, f, **ch):
        self.keys.append((f, {k.replace("__", "#").replace("_", ".").replace("#", "_"): v for k, v in ch.items()}))
        return self

    def keyd(self, f, d):
        self.keys.append((f, dict(d)))
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


# ------------------------------------------------------------------------------------------------ quadruped
def gait_leg(u, duty, sweep, lift, fold, heel):
    """u: phase since touch-down (0..1). Returns f, up, phi, toe."""
    u %= 1.0
    if u < duty:
        s = u / duty
        f = sweep / 2 - sweep * s
        return f, 0.0, heel * smooth((s - 0.7) / 0.3), 0.0
    s = (u - duty) / (1 - duty)
    f = -sweep / 2 + sweep * smooth(s)
    up = lift * math.sin(math.pi * s) ** 0.8
    return f, up, heel * (1 - smooth(s / 0.3)) + fold * math.sin(math.pi * min(s * 1.2, 1.0)), 30 * math.sin(math.pi * s)


def gait_layer(period, duty, speed, phases, lift_f, lift_h, fold_f, fold_h, heel, scap_gain=-80.0, scap=None):
    sweep = speed * duty * period / FPS

    def fn(f, clip):
        out = {}
        t = f / period
        for k, ph in phases.items():
            front = k.endswith("F")
            ff, up, phi, toe = gait_leg(t - ph, duty, sweep, lift_f if front else lift_h, fold_f if front else fold_h,
                                        heel)
            out[k + ".f"] = ff
            out[k + ".up"] = up
            out[k + ".phi"] = phi
            out[k + ".toe"] = toe
            if scap is not None and k in scap:     # shoulder / hip bone swings with the leg (adds reach)
                out[scap[k]] = scap_gain * ff
        return out
    return fn


def spine_rot(c, b):
    return Rz(c.get(b + ".yaw", 0.0)) @ Rx(-c.get(b + ".pitch", 0.0)) @ Ry(c.get(b + ".roll", 0.0))


class Quadruped:
    """Four legs with planar IK (in each leg's parent rest space), body root channels, spine channels.
    legs: {id: (parent, upper, lower, meta, toe)}; spine: bones driven by <b>.yaw/pitch/roll channels;
    extra(c, Rd, S, L): hook for jaw / tail / frill ... (armature-axis rotations)."""

    def __init__(self, rig, legs, pivot, spine, extra=None, scap_bones=()):
        self.rig, self.LEGS, self.PIVOT, self.spine, self.extra = rig, legs, np.asarray(pivot, float), spine, extra
        self.scap_bones = scap_bones
        H, T = rig.H, rig.T
        self.NEUTRAL = {k: H[v[4]].copy() for k, v in legs.items()}
        self.META_DIR = {k: normalize(H[v[4]] - H[v[3]]) for k, v in legs.items()}
        self.TOE_DIR = {k: normalize(T[v[4]] - H[v[4]]) for k, v in legs.items()}

    def evaluate(self, c):
        rig = self.rig
        Rd, S, L, X = {}, {}, {}, {}
        Rb = spine_rot(c, "body")
        piv = self.PIVOT + np.array([0.0, c.get("piv.y", 0.0), c.get("piv.z", 0.0)])
        t = np.array([c.get("body.side", 0.0), -c.get("body.fwd", 0.0), c.get("body.up", 0.0)])
        Xr = Xf(np.eye(3), t) @ Xf.about(Rb, piv)
        root = rig.ORDER[0]
        Rd[root] = Rb
        L[root] = Xr.apply(rig.H[root]) - rig.H[root]
        for b in self.spine:
            Rd[b] = spine_rot(c, b)
        for b in self.scap_bones:
            Rd[b] = Rx(c.get(b, 0.0))
        if self.extra:
            self.extra(c, Rd, S, L)
        leg_bones = set()
        for k, (p, u, l, m, tt) in self.LEGS.items():
            leg_bones.update((u, l, m, tt))
        for b in rig.ORDER:
            if b in leg_bones:
                continue
            rig.fk_one(X, b, Rd.get(b), S.get(b), L.get(b))
        for k, (p, u, l, m, tt) in self.LEGS.items():
            au, al, am, at = self.solve_leg(k, c, X[p])
            Rd[u], Rd[l], Rd[m], Rd[tt] = Rx(au), Rx(al), Rx(am), Rx(at)
            for b in (u, l, m, tt):
                rig.fk_one(X, b, Rd[b])
        return Rd, S, L, X

    def solve_leg(self, k, c, Xp):
        """Planar IK (see build_rootback_boar.solve_leg). Channels <k>.f/.up/.phi/.toe, <k>.loc/.lf/.lup."""
        H, T = self.rig.H, self.rig.T
        p, u, l, m, tt = self.LEGS[k]
        A, B, C, D, E = H[u], H[l], H[m], H[tt], T[tt]
        Lu, Ll, Lm = np.linalg.norm(B - A), np.linalg.norm(C - B), np.linalg.norm(D - C)
        tw = self.NEUTRAL[k] + np.array([0.0, -c.get(k + ".f", 0.0), c.get(k + ".up", 0.0)])
        tw[2] = max(tw[2], 0.03)
        qw = Xp.inv().apply(tw)
        ql = self.NEUTRAL[k] + np.array([0.0, -c.get(k + ".lf", 0.0), c.get(k + ".lup", 0.0)])
        w = min(max(c.get(k + ".loc", 0.0), 0.0), 1.0)
        q = qw * (1 - w) + ql * w
        phi = c.get(k + ".phi", 0.0)
        dm_w = Xp.R.T @ (Rx(phi) @ self.META_DIR[k])
        dm_l = Rx(phi) @ self.META_DIR[k]
        dm = normalize(dm_w * (1 - w) + dm_l * w)
        reach = 0.985 * (Lu + Ll)
        best = None
        for dphi in [0, 5, -5, 10, -10, 16, -16, 24, -24, 34, -34, 46, -46]:
            d2 = Rx(dphi) @ dm
            Ct = q - Lm * d2
            if math.hypot(Ct[1] - A[1], Ct[2] - A[2]) <= reach:
                best = (d2, Ct)
                break
        if best is None:
            d2 = dm
            Ct = q - Lm * d2
        else:
            d2, Ct = best
        v = np.array([0.0, Ct[1] - A[1], Ct[2] - A[2]])
        d = min(max(np.linalg.norm(v), abs(Lu - Ll) + 1e-3), reach)
        base = ang2(v)
        alpha = math.acos(min(max((Lu * Lu + d * d - Ll * Ll) / (2 * Lu * d), -1.0), 1.0))
        s0 = np.sign((B - A)[1] * (C - A)[2] - (B - A)[2] * (C - A)[1])
        cands = []
        for sg in (1, -1):
            a = base + sg * alpha
            Bn = np.array([0.0, A[1] + Lu * math.cos(a), A[2] + Lu * math.sin(a)])
            Cn = np.array([0.0, A[1] + d * math.cos(base), A[2] + d * math.sin(base)])
            cr = (Bn - A)[1] * (Cn - A)[2] - (Bn - A)[2] * (Cn - A)[1]
            cands.append((np.sign(cr) == s0, a, Bn, Cn))
        cands.sort(key=lambda x: not x[0])
        _, a_u, Bn, Cn = cands[0]
        au = wrap(a_u - ang2(B - A))
        al = wrap(ang2(Cn - Bn) - ang2(C - B) - au)
        am = wrap(ang2(d2) - ang2(D - C) - au - al)
        toe = c.get(k + ".toe", 0.0)
        tdir_w = Xp.R.T @ (Rx(toe) @ self.TOE_DIR[k])
        tdir = tdir_w * (1 - w) + (Rx(toe) @ self.TOE_DIR[k]) * w
        at = wrap(ang2(tdir) - ang2(E - D) - au - al - am)
        return math.degrees(au), math.degrees(al), math.degrees(am), math.degrees(at)


# ------------------------------------------------------------------------------------------------ Blender side
def build_armature(rig):
    import bpy
    arm = bpy.data.armatures.new("Armature")
    ob = bpy.data.objects.new("Armature", arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for b in rig.ORDER:
        e = arm.edit_bones.new(b)
        e.head, e.tail = tuple(rig.H[b]), tuple(rig.T[b])
        e.align_roll((1.0, 0.0, 0.0))
        e.use_deform = rig.PAR[b] is not None
        if rig.PAR[b]:
            e.parent = eb[rig.PAR[b]]
            e.use_connect = False
        eb[b] = e
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in ob.pose.bones:
        pb.rotation_mode = "QUATERNION"
    arm.display_type = "STICK"
    for b in ob.data.bones:     # sanity: numpy rest frames == Blender rest frames
        err = np.abs(np.array(b.matrix_local)[:3, :3] - rig.R0[b.name]).max()
        assert err < 1e-4, (b.name, err)
    return ob


def mat_to_quat(R):
    from mathutils import Matrix
    q = Matrix(np.asarray(R).tolist()).to_quaternion()
    return np.array([q.w, q.x, q.y, q.z])


def _split_rot_scale(M):
    """M = R @ Sym (armature axes). Polar decomposition -> rotation part."""
    U, s, Vt = np.linalg.svd(M)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        U[:, -1] *= -1
        R = U @ Vt
    return R


def bake(ob, rig, clip, evaluate):
    """evaluate(channels) -> (Rd, S, L[, X]) : armature-axis rotation deltas, local scales, head translations."""
    import bpy
    n = clip.frames + 1
    names = [b.name for b in ob.data.bones]
    quats = {b: np.zeros((n, 4)) for b in names}
    scales = {b: np.ones((n, 3)) for b in names}
    locs = {b: np.zeros((n, 3)) for b in names}
    used_s, used_l = set(), set()
    for f in range(n):
        ff = f % clip.frames if clip.loop else f
        res = evaluate(clip.channels(float(ff)))
        Rd, S, L = res[0], res[1], res[2]
        for b in names:
            q = mat_to_quat(rig.R0[b].T @ Rd.get(b, np.eye(3)) @ rig.R0[b])
            if f > 0 and np.dot(q, quats[b][f - 1]) < 0:
                q = -q
            quats[b][f] = q
            if b in S:
                scales[b][f] = S[b]
                used_s.add(b)
            if b in L:
                locs[b][f] = rig.R0[b].T @ np.asarray(L[b], float)
                used_l.add(b)
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
        if b in used_s:
            for i in range(3):
                put(f'pose.bones["{b}"].scale', i, scales[b][:, i])
    act.use_frame_range = True
    act.frame_start = 0
    act.frame_end = clip.frames
    act.use_cyclic = clip.loop
    return act


def assign(ob, act):
    ad = ob.animation_data or ob.animation_data_create()
    ad.action = act
    try:
        if len(act.slots):
            ad.action_slot = act.slots[0]
    except Exception:
        pass


def verify_fk(arm, rig, acts, evaluate, samples=3):
    """Compare Blender's evaluated bone heads / tails with the numpy FK at a few frames of every clip."""
    import bpy
    worst = 0.0
    where = None
    for name, (c, act) in acts.items():
        assign(arm, act)
        for k in range(samples):
            f = int(round(k * c.frames / max(samples - 1, 1)))
            bpy.context.scene.frame_set(f)
            bpy.context.view_layer.update()
            ff = f % c.frames if c.loop else f
            res = evaluate(c.channels(float(ff)))
            X = res[3] if len(res) > 3 else rig.fk(res[0], res[1], res[2])
            for pb in arm.pose.bones:
                b = pb.name
                for mine, got in ((X[b].apply(rig.H[b]), pb.head), (X[b].apply(rig.T[b]), pb.tail)):
                    e = float(np.linalg.norm(mine - np.array(got)))
                    if e > worst:
                        worst, where = e, (name, f, b)
    ad = arm.animation_data
    if ad:
        ad.action = None
    return worst, where


def export(arm, mesh, acts, out_glb, name):
    import glb_export as GX
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = None
    for cn, (c, act) in acts.items():
        tr = ad.nla_tracks.new()
        tr.name = cn
        st = tr.strips.new(cn, 0, act)
        try:
            st.action_slot = act.slots[0]
        except Exception:
            pass
        st.extrapolation = "NOTHING"
    for pb in arm.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    GX.export_glb(out_glb, [arm, mesh])
    print(f"[{name}] -> {out_glb} ({os.path.getsize(out_glb) / 1e6:.1f} MB)")
    bad, got = GX.check_lengths(out_glb, {n: c.frames / FPS for n, (c, a) in acts.items()})
    print(f"[{name}] {len(got)} animations in the GLB; length mismatches: {bad}")
    for tr in list(ad.nla_tracks):
        ad.nla_tracks.remove(tr)


def clip_meta(c):
    d = {"length": round(c.frames / FPS, 3), "loop": bool(c.loop)}
    if "hits" in c.meta:
        d["hits"] = [[round(a, 3), round(b, 3)] for a, b in c.meta["hits"]]
    if "ground_speed" in c.meta:
        d["ground_speed"] = c.meta["ground_speed"]
    return d


def write_meta(acts, name, prefix, generator, tris=0, bones=0, path=OUT_META):
    """Merge ONLY this model's keys: animations.<prefix>* and models.<name>. Re-read right before writing (other
    builders merge into the same file), keep every other key, write, re-read and verify."""
    mine, clips_all = {}, {}
    for cn, (c, act) in acts.items():
        d = clip_meta(c)
        clips_all[cn] = d
        if cn.startswith(prefix):
            mine[cn] = d
    model = {"generator": generator, "glb": f"res://assets/characters/{name}.glb", "clips": clips_all, "tris": tris,
             "bones": bones}
    with open(path) as fh:
        data = json.load(fh)
    before_a = json.dumps({k: v for k, v in data.get("animations", {}).items() if not k.startswith(prefix)},
                          sort_keys=True)
    before_m = json.dumps({k: v for k, v in data.get("models", {}).items() if k != name}, sort_keys=True)
    before_top = json.dumps({k: v for k, v in data.items() if k not in ("animations", "models")}, sort_keys=True)
    data.setdefault("animations", {}).update(mine)
    data.setdefault("models", {})[name] = model
    with open(path, "w") as fh:
        json.dump(data, fh, indent=1)
    with open(path) as fh:
        chk = json.load(fh)
    after_a = json.dumps({k: v for k, v in chk["animations"].items() if not k.startswith(prefix)}, sort_keys=True)
    after_m = json.dumps({k: v for k, v in chk["models"].items() if k != name}, sort_keys=True)
    after_top = json.dumps({k: v for k, v in chk.items() if k not in ("animations", "models")}, sort_keys=True)
    ok = (before_a == after_a and before_m == after_m and before_top == after_top and
          all(chk["animations"].get(k) == v for k, v in mine.items()) and chk["models"].get(name) == model)
    print(f"[{name}] meta merged {sorted(mine)} + models.{name} -> {path} (verified: {ok})")
    return ok


def make_import(name, template="rootback_boar"):
    """<name>.glb.import from an existing creature's import (same settings), uid line removed, paths fixed."""
    src = os.path.join(OUT_DIR, template + ".glb.import")
    dst = os.path.join(OUT_DIR, name + ".glb.import")
    if os.path.exists(dst):
        return dst
    txt = open(src).read()
    lines = [l for l in txt.splitlines() if not l.startswith("uid=")]
    txt = "\n".join(lines) + "\n"
    txt = txt.replace(f"{template}.glb", f"{name}.glb")
    import hashlib
    txt = txt.replace(txt.split(f"{name}.glb-")[1].split(".scn")[0],
                      hashlib.md5(f"res://assets/characters/{name}.glb".encode()).hexdigest())
    open(dst, "w", newline="\n").write(txt)
    print(f"[{name}] wrote {dst}")
    return dst


# ------------------------------------------------------------------------------------------------ evidence
def evidence(name, arm, mesh, acts, mode, rest_cfg, clip_cfg, out=EVID, res=400):
    """rest: rest views + close-ups + gameplay camera crops; clips: rows of clips at normalized times.
    rest_cfg = dict(views=[(label, target, dist, yaw, pitch)], game=[(dist, facing, scale)], target_z=..)
    clip_cfg = dict(clips=[...], target=(x,y,z), dist=.., yaw=.., pitch=.., frames=[...])"""
    import bpy
    import kit_b_evidence as KB
    tiles = os.path.join(SCRATCH, "tiles", name, mode)
    os.makedirs(tiles, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    KB.material_colors()
    for m in bpy.data.materials:
        if m.use_backface_culling:
            pass
    cam = KB.setup(res)
    bpy.context.scene.display.shading.show_backface_culling = True
    g = bpy.data.objects.get("Ground")
    if g:
        g.scale = (3, 3, 1)
    paths, labels = [], []
    if mode == "rest":
        ad = arm.animation_data
        if ad:
            ad.action = None
            for tr in list(ad.nla_tracks):
                ad.nla_tracks.remove(tr)
        for pb in arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.location = (0, 0, 0)
            pb.scale = (1, 1, 1)
        bpy.context.scene.frame_set(0)
        bpy.context.view_layer.update()
        lo, hi = KB.mesh_bounds(mesh)
        print(f"[evidence] {name} rest bounds {lo.round(3)} {hi.round(3)}")
        for lab, tgt, dist, yaw, pitch in rest_cfg["views"]:
            KB.place(cam, tgt, dist, yaw, pitch)
            paths.append(KB.render(os.path.join(tiles, f"v_{len(paths)}.png"), res=res))
            labels.append(lab)
        for dist, facing, sc in rest_cfg["game"]:
            KB.place(cam, (0, 0, rest_cfg.get("target_z", 0.6) * sc), dist, 0, 54, fov=40)
            arm.rotation_euler.z = math.radians(facing)
            arm.scale = (sc, sc, sc)
            p = KB.render(os.path.join(tiles, f"game_{dist}_{facing}_{sc}.png"), res=1080)
            KB.crop_center(p, res)
            paths.append(p)
            labels.append(f"game cam {dist} m, facing {facing}" + (f", scale {sc}" if sc != 1 else "") +
                          " (1:1 px @1080p)")
        arm.rotation_euler.z = 0
        arm.scale = (1, 1, 1)
        KB.compose(paths, labels, os.path.join(out, f"{name}_rest_iso.png"), 4,
                   f"{name}: rest / gameplay camera (bounds {lo.round(2).tolist()} .. {hi.round(2).tolist()} m)",
                   cell=res)
    else:
        frames = clip_cfg.get("frames", [0, 0.25, 0.5, 0.75, 1.0])
        for cn in clip_cfg["clips"]:
            c, act = acts[cn]
            for fr in frames:
                f = int(round(fr * c.frames))
                KB.set_action(arm, act, f)
                KB.place(cam, clip_cfg["target"], clip_cfg["dist"], clip_cfg.get("yaw", 60), clip_cfg.get("pitch", 12))
                paths.append(KB.render(os.path.join(tiles, f"{cn}_{f}.png"), res=res))
                labels.append(f"{cn}  f{f}/{c.frames}")
        KB.compose(paths, labels, os.path.join(out, f"{name}_{clip_cfg.get('tag', 'clips')}.png"), len(frames),
                   f"{name}: clips ({clip_cfg.get('title', '3/4 view')})", cell=res)


def run_main(build_all, name, prefix, generator, rest_cfg, clip_cfg_fn, rig, evaluate):
    """CLI: -- [--no-export] [--evidence rest|clips|both] [--clips a,b --tag t --frames .. --dist .. --yaw ..]"""
    import argparse
    import bh_mesh as M
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--evidence", default="")
    ap.add_argument("--clips", default="")
    ap.add_argument("--tag", default="clips")
    ap.add_argument("--frames", default="0,0.25,0.5,0.75,1")
    ap.add_argument("--out", default=EVID)
    ap.add_argument("--dist", type=float, default=0.0)
    ap.add_argument("--yaw", type=float, default=-999)
    ap.add_argument("--pitch", type=float, default=-999)
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    only = set(x for x in a.clips.split(",") if x) or None
    arm, mesh, acts = build_all(only=only if a.no_export else None)
    tris = M.tri_count(mesh)
    print(f"[{name}] mesh {tris} tris, {len(acts)} clips, {len(arm.data.bones)} bones")
    worst, where = verify_fk(arm, rig, acts if only is None else {k: v for k, v in acts.items() if k in only},
                             evaluate)
    print(f"[{name}] numpy FK vs Blender pose: worst {worst * 1000:.2f} mm at {where}")
    if not a.no_export:
        write_meta(acts, name, prefix, generator, tris, len(arm.data.bones))
        export(arm, mesh, acts, os.path.join(OUT_DIR, name + ".glb"), name)
        make_import(name)
    if a.evidence in ("rest", "both"):
        evidence(name, arm, mesh, acts, "rest", rest_cfg, None, out=a.out)
    if a.evidence in ("clips", "both"):
        cfg = clip_cfg_fn()
        if only:
            cfg["clips"] = [x for x in a.clips.split(",") if x]
        cfg["tag"] = a.tag
        cfg["frames"] = [float(x) for x in a.frames.split(",")]
        if a.dist:
            cfg["dist"] = a.dist
        if a.yaw != -999:
            cfg["yaw"] = a.yaw
        if a.pitch != -999:
            cfg["pitch"] = a.pitch
        evidence(name, arm, mesh, acts, "clips", rest_cfg, cfg, out=a.out)
