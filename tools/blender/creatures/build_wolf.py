"""Dire Wolf (Builder C): quadruped with its own armature, a skinned mesh and baked procedural clips.

  python3 build_wolf.py                      # export game/assets/characters/dire_wolf.glb + creature_meta.json
  python3 build_wolf.py --preview DIR [--clips walk,run --frames 0,0.25,0.5,0.75] [--views 90,35] [--no-export]

Conventions: Blender Z-up, the wolf faces -Y (= +Z in Godot), origin on the ground under the body, meters, 30 fps.
Clips are in place (the root only bobs / leans; wolf_bite and wolf_pounce lunge forward and come back).
Every clip is baked on every frame for every bone (quaternions) plus the root location.
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHAR = os.path.join(HERE, "..", "characters")
sys.path.insert(0, CHAR)
ROOT_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT_GLB = os.path.join(ROOT_DIR, "game", "assets", "characters", "dire_wolf.glb")
OUT_META = os.path.join(ROOT_DIR, "game", "assets", "characters", "creature_meta.json")

import numpy as np  # noqa: E402

FPS = 30
PALETTE = {
    "BH_Fur": ((0.15, 0.15, 0.155), 0.0, 0.92, None, 0.0, 1.0),          # grey-black coat
    "BH_Hair": ((0.04, 0.038, 0.042), 0.0, 0.9, None, 0.0, 1.0),          # near-black ragged mane / back stripe
    "BH_Bone": ((0.62, 0.58, 0.48), 0.0, 0.5, None, 0.0, 1.0),            # teeth, claws
    "BH_Flesh": ((0.30, 0.10, 0.09), 0.0, 0.5, None, 0.0, 1.0),           # mouth, scars
    "BH_Shadow": ((0.025, 0.022, 0.024), 0.0, 0.5, None, 0.0, 1.0),       # nose, lips, pads
    "BH_Emissive": ((0.6, 0.95, 1.0), 0.0, 0.3, (0.5, 0.92, 1.0), 4.0, 1.0),  # pale eyes, faint Aether glint
    "BH_Stone": ((0.34, 0.33, 0.31), 0.0, 0.9, None, 0.0, 1.0),           # pale grey fur: muzzle, chest, belly
}

# ------------------------------------------------------------------------------------------------ skeleton
# name: (head, tail, parent)
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.25), None),
    "hips": ((0, 0.42, 0.84), (0, 0.18, 0.865), "root"),
    "spine": ((0, 0.18, 0.865), (0, -0.08, 0.875), "hips"),
    "chest": ((0, -0.08, 0.875), (0, -0.34, 0.87), "spine"),
    "neck": ((0, -0.34, 0.88), (0, -0.52, 1.04), "chest"),
    "head": ((0, -0.52, 1.04), (0, -0.83, 1.0), "neck"),
    "jaw": ((0, -0.575, 0.99), (0, -0.8, 0.955), "head"),
    "tail.1": ((0, 0.46, 0.855), (0, 0.6, 0.83), "hips"),
    "tail.2": ((0, 0.6, 0.83), (0, 0.73, 0.76), "tail.1"),
    "tail.3": ((0, 0.73, 0.76), (0, 0.84, 0.66), "tail.2"),
    "tail.4": ((0, 0.84, 0.66), (0, 0.92, 0.54), "tail.3"),
}
for _s, _x in (("L", 1.0), ("R", -1.0)):
    BONES.update({
        f"ear.{_s}": ((0.055 * _x, -0.555, 1.1), (0.07 * _x, -0.535, 1.2), "head"),
        f"scap.{_s}": ((0.095 * _x, -0.23, 0.88), (0.12 * _x, -0.3, 0.66), "chest"),
        f"upperarm.{_s}": ((0.12 * _x, -0.3, 0.66), (0.12 * _x, -0.19, 0.45), f"scap.{_s}"),
        f"forearm.{_s}": ((0.12 * _x, -0.19, 0.45), (0.12 * _x, -0.25, 0.13), f"upperarm.{_s}"),
        f"fpaw.{_s}": ((0.12 * _x, -0.25, 0.13), (0.12 * _x, -0.285, 0.035), f"forearm.{_s}"),
        f"ftoe.{_s}": ((0.12 * _x, -0.285, 0.035), (0.12 * _x, -0.35, 0.018), f"fpaw.{_s}"),
        f"thigh.{_s}": ((0.11 * _x, 0.40, 0.80), (0.12 * _x, 0.29, 0.52), "hips"),
        f"shin.{_s}": ((0.12 * _x, 0.29, 0.52), (0.12 * _x, 0.46, 0.26), f"thigh.{_s}"),
        f"hpaw.{_s}": ((0.12 * _x, 0.46, 0.26), (0.12 * _x, 0.43, 0.035), f"shin.{_s}"),
        f"htoe.{_s}": ((0.12 * _x, 0.43, 0.035), (0.12 * _x, 0.365, 0.018), f"hpaw.{_s}"),
    })
ORDER = list(BONES)          # parents precede children
H = {b: np.array(v[0], float) for b, v in BONES.items()}
T = {b: np.array(v[1], float) for b, v in BONES.items()}
PAR = {b: v[2] for b, v in BONES.items()}
LEGS = {  # leg id: (parent-of-upper, upper, lower, meta, toe)
    "LF": ("scap.L", "upperarm.L", "forearm.L", "fpaw.L", "ftoe.L"),
    "RF": ("scap.R", "upperarm.R", "forearm.R", "fpaw.R", "ftoe.R"),
    "LH": ("hips", "thigh.L", "shin.L", "hpaw.L", "htoe.L"),
    "RH": ("hips", "thigh.R", "shin.R", "hpaw.R", "htoe.R"),
}
PIVOT = np.array([0.0, 0.05, 0.84])     # body rotation pivot (centre of mass)


def rest_frames():
    """Rest rotation (columns X, Y=along bone, Z) matching Blender's align_roll(+X hint)."""
    R = {}
    for b in ORDER:
        y = T[b] - H[b]
        y = y / np.linalg.norm(y)
        z = np.array([1.0, 0, 0]) - y * y[0]
        if np.linalg.norm(z) < 1e-6:
            z = np.array([0, -1.0, 0])
        z /= np.linalg.norm(z)
        x = np.cross(y, z)
        R[b] = np.stack([x, y, z], 1)
    return R


R0 = rest_frames()


def Rx(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def Ry(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def Rz(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def ang2(v):
    return math.atan2(v[2], v[1])


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------------------------------------ pose evaluation
class Xf:
    def __init__(self, R=None, t=None):
        self.R = np.eye(3) if R is None else R
        self.t = np.zeros(3) if t is None else np.asarray(t, float)

    def __matmul__(self, o):
        return Xf(self.R @ o.R, self.R @ o.t + self.t)

    def apply(self, p):
        return self.R @ p + self.t

    def inv(self):
        return Xf(self.R.T, -self.R.T @ self.t)

    @staticmethod
    def about(R, c):
        return Xf(R, c - R @ c)


def spine_rot(c, b):
    return Rz(c.get(b + ".yaw", 0.0)) @ Rx(-c.get(b + ".pitch", 0.0)) @ Ry(c.get(b + ".roll", 0.0))


NEUTRAL_BALL = {k: H[v[4]].copy() for k, v in LEGS.items()}
REST_META_DIR = {k: (H[v[4]] - H[v[3]]) / np.linalg.norm(H[v[4]] - H[v[3]]) for k, v in LEGS.items()}
REST_TOE_DIR = {k: (T[v[4]] - H[v[4]]) / np.linalg.norm(T[v[4]] - H[v[4]]) for k, v in LEGS.items()}


def evaluate(c):
    """c: channel dict. Returns (Rd dict bone -> armature-axis rotation relative to parent, X dict bone -> Xf)."""
    Rd, X = {}, {}
    Rb = spine_rot(c, "body")
    t = np.array([c.get("body.side", 0.0), -c.get("body.fwd", 0.0), c.get("body.up", 0.0)])
    X["root"] = Xf(np.eye(3), t) @ Xf.about(Rb, PIVOT)
    Rd["root"] = Rb
    for b in ("hips", "spine", "chest", "neck", "head"):
        Rd[b] = spine_rot(c, b)
    Rd["jaw"] = Rx(c.get("jaw", 0.0))
    for s, sx in (("L", 1), ("R", -1)):
        Rd["ear." + s] = Rx(-c.get("ears", 0.0) - c.get("ear." + s, 0.0)) @ Ry(sx * c.get("ears.out", 0.0))
    # tail: lift (+ up), yaw (+ toward own left), curl adds lift down the chain
    for i in range(1, 5):
        Rd[f"tail.{i}"] = Rz(c.get("tail.yaw", 0.0) * (0.6 + 0.2 * i) + c.get("tail.wag", 0.0) * 0.25 * i) @ \
            Rx(c.get("tail.lift", 0.0) * (1.0 if i == 1 else 0.35) + c.get("tail.curl", 0.0) * 0.25 * (i - 1))
    for b in ORDER:
        if b == "root":
            continue
        if b not in Rd:
            Rd[b] = np.eye(3)
        if b in X:
            continue
    # FK for everything except legs below the scapula / hips (legs solved after their parents are known)
    for s in ("L", "R"):
        Rd["scap." + s] = Rx(c.get(f"scap.{s}", 0.0))
    leg_bones = set()
    for k, (p, u, l, m, tt) in LEGS.items():
        leg_bones.update((u, l, m, tt))
    for b in ORDER:
        if b == "root" or b in leg_bones:
            continue
        X[b] = X[PAR[b]] @ Xf.about(Rd[b], H[b])
    for k, (p, u, l, m, tt) in LEGS.items():
        au, al, am, at = solve_leg(k, c, X[p])
        Rd[u], Rd[l], Rd[m], Rd[tt] = Rx(au), Rx(al), Rx(am), Rx(at)
        for b in (u, l, m, tt):
            X[b] = X[PAR[b]] @ Xf.about(Rd[b], H[b])
    return Rd, X


def solve_leg(k, c, Xp):
    """Planar IK in the rest space of the leg's parent. Channels (world, meters/deg):
    <k>.f forward offset of the paw ball from neutral, <k>.up lift, <k>.phi metacarpus/metatarsus rotation
    (+ = paw folds back), <k>.toe (+ = toes curl down), <k>.loc 0..1 blend toward a target given in the parent's
    rest space (<k>.lf / <k>.lup offsets, used when the body lies on its side)."""
    p, u, l, m, tt = LEGS[k]
    A, B, C, D, E = H[u], H[l], H[m], H[tt], T[tt]
    Lu, Ll, Lm = np.linalg.norm(B - A), np.linalg.norm(C - B), np.linalg.norm(D - C)
    tw = NEUTRAL_BALL[k] + np.array([0.0, -c.get(k + ".f", 0.0), c.get(k + ".up", 0.0)])
    tw[2] = max(tw[2], 0.03)
    qw = Xp.inv().apply(tw)
    ql = NEUTRAL_BALL[k] + np.array([0.0, -c.get(k + ".lf", 0.0), c.get(k + ".lup", 0.0)])
    w = min(max(c.get(k + ".loc", 0.0), 0.0), 1.0)
    q = qw * (1 - w) + ql * w
    # meta direction: world rest direction rotated by phi (world), expressed in parent rest space (blend w/ local)
    phi = c.get(k + ".phi", 0.0)
    dm_w = Xp.R.T @ (Rx(phi) @ REST_META_DIR[k])
    dm_l = Rx(phi) @ REST_META_DIR[k]
    dm = dm_w * (1 - w) + dm_l * w
    dm /= np.linalg.norm(dm)
    reach = 0.985 * (Lu + Ll)
    # rotate the meta toward reach if the 2-bone part cannot get there (prefer the requested angle)
    best = None
    for dphi in [0, 5, -5, 10, -10, 16, -16, 24, -24, 34, -34, 46, -46]:
        d2 = Rx(dphi) @ dm
        Ct = q - Lm * d2
        dist = math.hypot(Ct[1] - A[1], Ct[2] - A[2])
        if dist <= reach:
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
    tdir_w = Xp.R.T @ (Rx(toe) @ REST_TOE_DIR[k])
    tdir = tdir_w * (1 - w) + (Rx(toe) @ REST_TOE_DIR[k]) * w
    at = wrap(ang2(tdir) - ang2(E - D) - au - al - am)
    return math.degrees(au), math.degrees(al), math.degrees(am), math.degrees(at)


# ------------------------------------------------------------------------------------------------ clip authoring
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


def gait_layer(period, duty, speed, phases, lift_f, lift_h, fold_f, fold_h, heel):
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
            if front:   # scapula swings with the leg (adds reach)
                out["scap." + k[0]] = -80.0 * ff
        return out
    return fn


def cyc(f, period, k=1.0, ph=0.0):
    return math.sin(2 * math.pi * (k * f / period + ph))


def clips():
    C = []
    # ---- idle: breathing, slow tail sway, ear flicks
    c = Clip("idle", 90, loop=True)
    c.key(0, neck_pitch=0.0)
    c.layer(lambda f, cl: {"chest.pitch": 1.2 * cyc(f, 90, 2), "body.up": 0.004 * cyc(f, 90, 2),
                           "neck.pitch": 2.0 * cyc(f, 90, 1, 0.1), "head.yaw": 4 * cyc(f, 90, 1, 0.3),
                           "tail.yaw": 8 * cyc(f, 90, 1), "tail.lift": -8.0,
                           "ear.L": 12 * max(0.0, cyc(f, 90, 3)) ** 8, "jaw": 2 + 2 * cyc(f, 90, 2, 0.25)})
    C.append(c)
    # ---- idle_look: look left, then right, sniff
    c = Clip("idle_look", 75)
    c.key(0).key(12, neck_yaw=22, head_yaw=18, neck_pitch=6, ears=-6).key(30, neck_yaw=24, head_yaw=20, neck_pitch=6)
    c.key(42, neck_yaw=-22, head_yaw=-18, neck_pitch=4, head_roll=-6).key(58, neck_yaw=-20, head_yaw=-16)
    c.key(75, neck_yaw=0, head_yaw=0, neck_pitch=0, ears=0, head_roll=0)
    c.layer(lambda f, cl: {"tail.lift": -8.0, "tail.yaw": 6 * cyc(f, 75, 1)})
    C.append(c)
    # ---- walk: lateral-sequence 4-beat walk
    WALK_P, WALK_V = 30, 1.25
    c = Clip("walk", WALK_P, loop=True, ground_speed=WALK_V)
    c.key(0)
    c.layer(gait_layer(WALK_P, 0.62, WALK_V, {"LH": 0.0, "LF": 0.25, "RH": 0.5, "RF": 0.75}, 0.09, 0.08, 55, 25, 20))
    c.layer(lambda f, cl: {"body.up": -0.02 + 0.01 * cyc(f, WALK_P, 2), "body.roll": 2.0 * cyc(f, WALK_P, 1),
                           "neck.pitch": -6 + 3 * cyc(f, WALK_P, 2, 0.2), "head.pitch": -4,
                           "spine.yaw": 3 * cyc(f, WALK_P, 1), "tail.lift": -12, "tail.yaw": 8 * cyc(f, WALK_P, 1, .3)})
    C.append(c)
    # ---- run: rotary gallop with spine flexion and a suspension phase
    RUN_P, RUN_V = 15, 5.5
    for nm in ("run", "run_combat"):
        c = Clip(nm, RUN_P, loop=True, ground_speed=RUN_V)
        c.key(0)
        c.layer(gait_layer(RUN_P, 0.3, RUN_V, {"LH": 0.0, "RH": 0.1, "RF": 0.45, "LF": 0.56}, 0.16, 0.14, 80, 40, 25))
        crouch = -0.06 if nm == "run" else -0.09
        c.layer(lambda f, cl, cr=crouch: {
            "body.up": cr + 0.035 * cyc(f, RUN_P, 1, 0.1), "body.pitch": 5 * cyc(f, RUN_P, 1, 0.35),
            "spine.pitch": 7 * cyc(f, RUN_P, 1, 0.55), "hips.pitch": -6 * cyc(f, RUN_P, 1, 0.55),
            "neck.pitch": -14 + 6 * cyc(f, RUN_P, 1, 0.8), "head.pitch": -4 + (-6 if cr < -0.07 else 0),
            "ears": 25 if cr < -0.07 else 15, "tail.lift": 4 + 8 * cyc(f, RUN_P, 1, 0.2), "jaw": 12})
        C.append(c)
    # ---- reactions
    c = Clip("hit_light", 12)
    c.key(0).key(3, body_fwd=-0.05, body_pitch=5, neck_pitch=14, head_pitch=6, neck_yaw=8, ears=30, jaw=14)
    c.key(12, body_fwd=0, body_pitch=0, neck_pitch=0, head_pitch=0, neck_yaw=0, ears=0, jaw=0)
    C.append(c)
    c = Clip("hit_heavy", 18)
    c.key(0).key(4, body_fwd=-0.12, body_up=-0.05, body_pitch=9, body_roll=5, neck_pitch=24, head_pitch=10,
                 neck_yaw=14, ears=45, jaw=24, tail_lift=-25, LF_f=0.06, RF_f=0.04)
    c.key(9, body_fwd=-0.1, body_up=-0.04, body_pitch=6, body_roll=3, neck_pitch=14, head_pitch=4, neck_yaw=8,
          ears=35, jaw=10, tail_lift=-20, LF_f=0.1, RF_f=0.06)
    c.key(18, body_fwd=0, body_up=0, body_pitch=0, body_roll=0, neck_pitch=0, head_pitch=0, neck_yaw=0, ears=0,
          jaw=0, tail_lift=0, LF_f=0, RF_f=0)
    C.append(c)
    c = Clip("stagger_small", 24)
    c.key(0).key(5, body_fwd=-0.09, body_side=-0.05, body_roll=-8, body_pitch=6, neck_pitch=16, neck_yaw=-18,
                 ears=35, tail_lift=-20)
    c.key(9, LF_up=0.08, LF_f=-0.03, body_fwd=-0.12, body_side=-0.06, body_roll=-9, neck_pitch=12, neck_yaw=-14)
    c.key(14, LF_up=0.0, LF_f=-0.12, RH_f=-0.08, body_fwd=-0.1, body_roll=-4, body_side=-0.03, neck_pitch=8)
    c.key(24, LF_f=0, RH_f=0, body_fwd=0, body_side=0, body_roll=0, body_pitch=0, neck_pitch=0, neck_yaw=0, ears=0,
          tail_lift=0)
    C.append(c)
    c = Clip("knockback", 27)
    c.key(0).key(4, body_fwd=-0.2, body_up=0.04, body_pitch=16, neck_pitch=20, ears=45, jaw=26, tail_lift=-30,
                 LF_up=0.16, RF_up=0.12, LF_f=0.08, RF_f=0.1, LH_f=0.18, RH_f=0.16, hips_pitch=-8)
    c.key(11, body_fwd=-0.3, body_up=-0.08, body_pitch=6, neck_pitch=10, ears=40, jaw=10, tail_lift=-30,
          LF_up=0.0, RF_up=0.0, LF_f=0.12, RF_f=0.08, LH_f=0.2, RH_f=0.18, hips_pitch=-4)
    c.key(18, body_fwd=-0.18, body_up=-0.05, body_pitch=2, neck_pitch=4, ears=20, jaw=4, tail_lift=-18,
          LF_f=0.06, RF_f=0.02, LH_f=0.1, RH_f=0.12, hips_pitch=0)
    c.key(27, body_fwd=0, body_up=0, body_pitch=0, neck_pitch=0, ears=0, jaw=0, tail_lift=0, LF_f=0, RF_f=0,
          LH_f=0, RH_f=0)
    C.append(c)
    # ---- deaths
    C.append(death_clip("death", side=1, first="front"))
    C.append(death_clip("death_back", side=-1, first="hind"))
    # ---- alert: head up, ears forward, tail up, stiff front legs, lips curl (jaw slightly open)
    c = Clip("alert", 30)
    c.key(0).key(8, neck_pitch=18, head_pitch=-8, ears=-12, ears_out=-8, tail_lift=22, body_up=0.02, body_pitch=3,
                 jaw=8, LF_f=0.05)
    c.key(18, neck_pitch=12, head_pitch=-12, ears=-12, ears_out=-8, tail_lift=24, body_up=0.01, body_pitch=-2,
          jaw=14, body_fwd=0.03, LF_f=0.05)
    c.key(30, neck_pitch=4, head_pitch=-6, ears=-8, ears_out=-4, tail_lift=12, body_up=0.0, body_pitch=0, jaw=6,
          body_fwd=0.0, LF_f=0.0)
    C.append(c)
    # ---- attacks
    c = Clip("wolf_bite", 24, hits=[[10 / FPS, 13 / FPS]])
    c.key(0).key(6, body_fwd=-0.08, body_up=-0.07, body_pitch=-4, neck_pitch=-10, head_pitch=-8, jaw=6, ears=35,
                 tail_lift=-4, LH_f=0.04, RH_f=0.04)
    c.key(9, body_fwd=0.2, body_up=-0.02, body_pitch=-6, neck_pitch=-26, head_pitch=-6, jaw=44, ears=40,
          LF_f=0.18, LF_up=0.0, RF_f=0.12, LH_f=-0.02, RH_f=-0.02)
    c.key(11, body_fwd=0.3, body_up=-0.03, body_pitch=-7, neck_pitch=-30, head_pitch=-2, jaw=2, ears=40,
          LF_f=0.3, RF_f=0.24, LH_f=-0.04, RH_f=-0.05)
    c.key(13, body_fwd=0.28, neck_pitch=-24, head_pitch=4, head_yaw=10, jaw=0, LF_f=0.3, RF_f=0.24)
    c.key(17, body_fwd=0.22, neck_pitch=-18, head_pitch=6, head_yaw=-14, head_roll=-10, jaw=4, LF_f=0.28,
          RF_f=0.22)
    c.key(24, body_fwd=0, body_up=0, body_pitch=0, neck_pitch=0, head_pitch=0, head_yaw=0, head_roll=0, jaw=0,
          ears=0, tail_lift=0, LF_f=0, RF_f=0, LH_f=0, RH_f=0)
    C.append(c)
    c = Clip("wolf_pounce", 42, hits=[[23 / FPS, 27 / FPS]])
    c.key(0)
    c.key(10, body_up=-0.16, body_fwd=-0.08, body_pitch=-6, neck_pitch=-18, head_pitch=-2, ears=40, jaw=10,
          tail_lift=-6, hips_pitch=6, LH_f=0.1, RH_f=0.1, LF_f=0.02, RF_f=0.02)
    c.key(15, body_up=0.28, body_fwd=0.15, body_pitch=18, neck_pitch=-6, head_pitch=-12, ears=45, jaw=40,
          tail_lift=10, hips_pitch=-10, LF_f=0.5, RF_f=0.46, LF_up=0.6, RF_up=0.58, LF_phi=40, RF_phi=40,
          LH_f=-0.3, RH_f=-0.3, LH_up=0.2, RH_up=0.2, LH_phi=60, RH_phi=60)
    c.key(20, body_up=0.3, body_fwd=0.38, body_pitch=-4, neck_pitch=-20, head_pitch=-4, jaw=48, tail_lift=14,
          LF_f=0.78, RF_f=0.74, LF_up=0.3, RF_up=0.32, LF_phi=-20, RF_phi=-20, LH_f=-0.2, RH_f=-0.18,
          LH_up=0.4, RH_up=0.4, LH_phi=50, RH_phi=50)
    c.key(24, body_up=-0.1, body_fwd=0.55, body_pitch=-12, neck_pitch=-30, head_pitch=6, jaw=0,
          LF_f=0.72, RF_f=0.7, LF_up=0.0, RF_up=0.0, LF_phi=0, RF_phi=0, LH_f=0.32, RH_f=0.3, LH_up=0.1,
          RH_up=0.1, LH_phi=10, RH_phi=10, hips_pitch=4)
    c.key(28, body_up=-0.12, body_fwd=0.55, body_pitch=-8, neck_pitch=-22, head_pitch=10, head_yaw=12, jaw=6,
          LF_f=0.72, RF_f=0.7, LH_f=0.4, RH_f=0.38, LH_up=0.0, RH_up=0.0, LH_phi=0, RH_phi=0)
    c.key(42, body_up=0, body_fwd=0, body_pitch=0, neck_pitch=0, head_pitch=0, head_yaw=0, jaw=0, ears=0,
          tail_lift=0, hips_pitch=0, LF_f=0, RF_f=0, LH_f=0, RH_f=0)
    C.append(c)
    c = Clip("wolf_howl", 75)
    c.key(0).key(12, body_up=-0.03, body_pitch=10, neck_pitch=40, head_pitch=34, jaw=10, ears=12, tail_lift=-16,
                 hips_pitch=-4, LH_f=0.06, RH_f=0.06)
    c.key(20, body_up=-0.04, body_pitch=12, neck_pitch=46, head_pitch=40, jaw=26, ears=18, tail_lift=-18)
    c.key(56, body_up=-0.04, body_pitch=12, neck_pitch=48, head_pitch=44, jaw=22, ears=18, tail_lift=-18)
    c.key(75, body_up=0, body_pitch=0, neck_pitch=0, head_pitch=0, jaw=0, ears=0, tail_lift=0, hips_pitch=0,
          LH_f=0, RH_f=0)
    c.layer(lambda f, cl: {"jaw": 4 * math.sin(2 * math.pi * f / 18) * (1 if 20 < f < 56 else 0),
                           "head.yaw": 3 * math.sin(2 * math.pi * f / 40)})
    C.append(c)
    c = Clip("devour", 60, loop=True)
    base = dict(body_up=-0.1, body_pitch=-10, neck_pitch=-50, head_pitch=-18, ears=20, tail_lift=-14,
                LF_f=0.12, RF_f=0.02, hips_pitch=4)
    c.key(0, **base, jaw=10)
    c.key(12, **dict(base, neck_pitch=-38, head_pitch=-8, head_yaw=18, head_roll=16, jaw=4, body_fwd=-0.04))
    c.key(20, **dict(base, neck_pitch=-52, head_pitch=-20, jaw=24))
    c.key(30, **dict(base, neck_pitch=-50, head_pitch=-20, jaw=2))
    c.key(42, **dict(base, neck_pitch=-36, head_pitch=-4, head_yaw=-20, head_roll=-14, jaw=6, body_fwd=-0.05))
    c.key(52, **dict(base, neck_pitch=-50, head_pitch=-18, jaw=20))
    c.key(60, **base, jaw=10)
    C.append(c)
    return C


def death_clip(name, side, first):
    """Legs buckle, the body drops and rolls onto its side (side=+1: onto its right side)."""
    c = Clip(name, 45)
    r = 84 * side
    fr = ("LF", "RF") if first == "front" else ("LH", "RH")
    bk = ("LH", "RH") if first == "front" else ("LF", "RF")
    c.key(0)
    k1 = dict(body_up=-0.12, body_pitch=-12 if first == "front" else 14, neck_pitch=16 if first == "hind" else -10,
              head_pitch=-10, ears=40, jaw=20, tail_lift=-20)
    for k in fr:
        k1[k + "_f"] = 0.08 if first == "front" else 0.12
        k1[k + "_phi"] = 30
    c.key(8, **k1)
    k2 = dict(body_up=-0.4, body_pitch=-8 if first == "front" else 8, body_roll=r * 0.35, body_side=-0.04 * side,
              neck_pitch=-4 if first == "front" else 24, neck_yaw=-10 * side, head_pitch=-6, ears=40, jaw=26,
              tail_lift=-30)
    for k in fr + bk:
        k2[k + "_loc"] = 0.6
        k2[k + "_lf"] = 0.1 if k.endswith("F") else 0.14
        k2[k + "_lup"] = 0.22
    c.key(18, **k2)
    k3 = dict(body_up=-0.66, body_pitch=0, body_roll=r, body_side=-0.1 * side, neck_pitch=-14, neck_yaw=-6 * side,
              head_pitch=-10, head_roll=10 * side, ears=50, jaw=18, tail_lift=-6, tail_yaw=12 * side)
    legs = {"LF": (0.18, 0.12), "RF": (0.08, 0.2), "LH": (-0.12, 0.2), "RH": (0.02, 0.24)}
    for k, (lf, lup) in legs.items():
        k3[k + "_loc"] = 1.0
        k3[k + "_lf"] = lf
        k3[k + "_lup"] = lup
    c.key(30, **k3)
    k4 = dict(k3, body_up=-0.68, neck_pitch=-20, head_pitch=-14, jaw=12, ears=60)
    c.key(45, **k4)
    return c


# ------------------------------------------------------------------------------------------------ mesh
def seg_dist(V, a, b):
    ab = b - a
    t = np.clip(((V - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(V - (a + t[:, None] * ab), axis=1)


def dist_weights(V, bones, power=6.0, top=3, bias=None):
    D = []
    for b in bones:
        d = seg_dist(V, H[b], T[b]) + 0.015
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


def build_mesh(mats):
    import bh_mesh as M
    parts = []
    rng = np.random.default_rng(21)

    def add(p, bone=None, bones=None, power=6.0, bias=None):
        if bone:
            p.W = [{bone: 1.0}] * len(p.V)
        else:
            p.W = dist_weights(p.V, bones, power=power, bias=bias)
        parts.append(p)
        return p

    def ring(y, zc, rx, rt, rb, n=18, x0=0.0):
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            s, co = math.sin(a), math.cos(a)
            pts.append((x0 + rx * co, y, zc + (rt if s > 0 else rb) * s))
        return np.array(pts)

    # ---- body: rump -> deep chest; loft along -Y (rings ordered front to back so faces point outward)
    BODY = [(0.60, 0.80, 0.05, 0.05, 0.05), (0.52, 0.81, 0.10, 0.075, 0.10), (0.42, 0.815, 0.125, 0.085, 0.13),
            (0.30, 0.83, 0.125, 0.085, 0.13), (0.16, 0.85, 0.105, 0.08, 0.1), (0.02, 0.855, 0.115, 0.09, 0.16),
            (-0.12, 0.85, 0.135, 0.105, 0.24), (-0.26, 0.85, 0.14, 0.115, 0.25), (-0.36, 0.87, 0.13, 0.115, 0.2),
            (-0.43, 0.9, 0.11, 0.11, 0.13)]
    rings = [ring(y, z, rx * 1.18, rt, rb, n=20) for (y, z, rx, rt, rb) in BODY]
    V, F = M.loft(rings[::-1], cap0=True, cap1=True)
    body = M.Part(V, F, "BH_Fur", name="body")
    add(body, bones=["hips", "spine", "chest", "neck", "scap.L", "scap.R", "thigh.L", "thigh.R", "tail.1"],
        bias={"scap.L": 1.5, "scap.R": 1.5, "thigh.L": 1.35, "thigh.R": 1.35, "tail.1": 1.6, "neck": 1.2})
    # pale chest / belly patch
    V, F = M.loft([ring(y, z - 0.01, rx * 0.72, 0.02, rb * 1.02, n=14) for (y, z, rx, rt, rb) in BODY[4:9]][::-1],
                  cap0=False, cap1=False)
    belly = M.Part(V, F, "BH_Stone", name="belly")
    keep = belly.V[:, 2] < np.array([r[1] for r in BODY[4:9]]).min() - 0.05
    # push the belly patch just outside the body only on its underside
    belly.V[:, 2] -= 0.004
    add(belly, bones=["spine", "chest", "neck", "scap.L", "scap.R"], bias={"scap.L": 1.5, "scap.R": 1.5})

    # ---- neck + head
    NECK = [(-0.34, 0.9, 0.11, 0.12, 0.16), (-0.44, 0.96, 0.1, 0.1, 0.13), (-0.52, 1.02, 0.085, 0.08, 0.1),
            (-0.56, 1.05, 0.075, 0.07, 0.08)]
    V, F = M.loft([ring(*r, n=16) for r in NECK][::-1], cap0=False, cap1=False)
    add(M.Part(V, F, "BH_Fur", name="neck"), bones=["chest", "neck", "head"], bias={"head": 1.3})
    SKULL = [(-0.48, 1.06, 0.06, 0.06, 0.05), (-0.54, 1.075, 0.08, 0.075, 0.07), (-0.6, 1.07, 0.082, 0.07, 0.07),
             (-0.65, 1.055, 0.062, 0.055, 0.055), (-0.7, 1.03, 0.044, 0.04, 0.035),
             (-0.76, 1.015, 0.037, 0.034, 0.026), (-0.81, 1.008, 0.029, 0.027, 0.018),
             (-0.84, 1.0, 0.014, 0.012, 0.01)]
    V, F = M.loft([ring(*r, n=16) for r in SKULL][::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Fur", name="skull"), bone="head")
    # pale muzzle underside + cheeks
    V, F = M.loft([ring(y, z - 0.012, rx * 0.95, rt * 0.4, rb * 1.05, n=12) for (y, z, rx, rt, rb) in SKULL[3:7]][::-1],
                  cap0=False, cap1=False)
    add(M.Part(V, F, "BH_Stone", name="muzzle"), bone="head")
    JAW = [(-0.58, 0.985, 0.05, 0.02, 0.03), (-0.66, 0.975, 0.04, 0.016, 0.026), (-0.74, 0.968, 0.03, 0.013, 0.02),
           (-0.8, 0.964, 0.02, 0.01, 0.014)]
    V, F = M.loft([ring(*r, n=12) for r in JAW][::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Stone", name="jaw"), bone="jaw")
    # mouth interior (flesh) on the jaw top, lips (shadow)
    V, F = M.loft([ring(y, z + 0.012, rx * 0.8, 0.006, 0.006, n=10) for (y, z, rx, rt, rb) in JAW[:3]][::-1])
    add(M.Part(V, F, "BH_Flesh", name="tongue"), bone="jaw")
    V, F = M.loft([ring(y, z - 0.028, rx * 0.95, 0.008, 0.01, n=12) for (y, z, rx, rt, rb) in SKULL[3:7]][::-1],
                  cap0=False, cap1=False)
    add(M.Part(V, F, "BH_Shadow", name="lips"), bone="head")
    # nose, eyes, teeth
    V, F = M.sphere(0.022, 10, 6, center=(0, -0.835, 1.012), scale=(1.1, 0.8, 0.8))
    add(M.Part(V, F, "BH_Shadow", name="nose"), bone="head")
    for sx in (1, -1):
        V, F = M.sphere(0.013, 8, 5, center=(sx * 0.047, -0.648, 1.082), scale=(0.9, 1.2, 0.7))
        add(M.Part(V, F, "BH_Emissive", name="eye"), bone="head")
        V, F = M.sphere(0.02, 8, 5, center=(sx * 0.045, -0.642, 1.093), scale=(1.1, 1.3, 0.5))
        add(M.Part(V, F, "BH_Hair", name="brow"), bone="head")
        for y, L in ((-0.79, 0.034), (-0.72, 0.02)):   # upper fangs + carnassial
            V, F = M.lathe([(0.0, -L), (0.006, -L * 0.3), (0.007, 0.0), (0.0, 0.004)], 5)
            add(M.Part(V, F, "BH_Bone").move((sx * 0.024, y, 0.985)), bone="head")
        V, F = M.lathe([(0.0, 0.0), (0.006, 0.003), (0.005, 0.02), (0.0, 0.026)], 5)
        add(M.Part(V, F, "BH_Bone").move((sx * 0.02, -0.775, 0.97)), bone="jaw")
    # scars: across the muzzle and one on the right shoulder
    for pts in ([(0.035, -0.69, 1.07), (0.0, -0.72, 1.06), (-0.04, -0.74, 1.04)],
                [(0.045, -0.6, 1.1), (0.065, -0.66, 1.07)]):
        V, F = M.tube(pts, [(0.005, 0.003)] * len(pts), n=5, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Flesh", name="scar"), bone="head")
    V, F = M.tube([(-0.14, -0.3, 0.96), (-0.16, -0.22, 0.9), (-0.17, -0.14, 0.82)], [(0.006, 0.004)] * 3, n=5,
                  up=(1, 0, 0))
    add(M.Part(V, F, "BH_Flesh", name="scar"), bones=["chest", "scap.R"], bias={"scap.R": 1.3})
    # ears: tall pointed, slightly cupped
    for s, sx in (("L", 1), ("R", -1)):
        h, t = H["ear." + s], T["ear." + s]
        out = [(-0.03, 0.0), (0.03, 0.0), (0.004, 0.11), (-0.004, 0.11)]
        V, F = M.prism(np.array([(-0.034, -0.01), (0.034, -0.01), (0.012, 0.09), (0.0, 0.115), (-0.012, 0.09)]),
                       0.018, axis="y")
        e = M.Part(V, F, "BH_Fur", name="ear")
        e.V[:, 1] += 0.02 * (np.abs(e.V[:, 0]) / 0.034) ** 2 - 0.004       # cup
        e.rot(Rz(-18 * sx)).move(h + (0, 0.0, -0.01))
        add(e, bone="ear." + s)
        V, F = M.prism(np.array([(-0.022, 0.0), (0.022, 0.0), (0.0, 0.08)]), 0.004, axis="y")
        ei = M.Part(V, F, "BH_Flesh", name="ear_in").rot(Rz(-18 * sx)).move(h + (0, -0.012, 0.0))
        add(ei, bone="ear." + s)

    # ---- legs
    def leg_tube(chain, radii, mat="BH_Fur"):
        pts = [H[chain[0]]] + [T[b] for b in chain]
        V, F = M.tube(pts, radii, n=12, up=(0, -1, 0))
        return M.Part(V, F, mat, name="leg")
    for s, sx in (("L", 1), ("R", -1)):
        p = leg_tube(["scap." + s, "upperarm." + s, "forearm." + s, "fpaw." + s],
                     [(0.085, 0.11), (0.078, 0.092), (0.056, 0.062), (0.036, 0.04), (0.03, 0.032)])
        add(p, bones=["scap." + s, "upperarm." + s, "forearm." + s, "fpaw." + s, "chest"], power=8,
            bias={"chest": 1.6})
        p = leg_tube(["thigh." + s, "shin." + s, "hpaw." + s],
                     [(0.115, 0.14), (0.082, 0.095), (0.045, 0.05), (0.03, 0.032)])
        p.V[:, 0] += 0.01 * sx
        add(p, bones=["hips", "thigh." + s, "shin." + s, "hpaw." + s], power=8, bias={"hips": 1.8})
        # haunch mass
        V, F = M.sphere(0.12, 14, 8, center=(0.075 * sx, 0.38, 0.72), scale=(0.75, 1.1, 1.25))
        add(M.Part(V, F, "BH_Fur", name="haunch"), bones=["hips", "thigh." + s], power=6, bias={"hips": 0.9})
        # paws: pad block on the toe bone + claws
        for toe, meta in (("ftoe." + s, "fpaw." + s), ("htoe." + s, "hpaw." + s)):
            c = H[toe]
            V, F = M.sphere(0.045, 12, 7, center=c + (0, -0.03, -0.005), scale=(0.95, 1.3, 0.55))
            add(M.Part(V, F, "BH_Fur", name="paw"), bone=toe)
            V, F = M.sphere(0.038, 10, 5, center=c + (0, 0.015, 0.0), scale=(0.9, 1.0, 0.6))
            add(M.Part(V, F, "BH_Fur", name="heel"), bone=meta)
            for k in range(4):
                x = (k - 1.5) * 0.02
                V, F = M.tube([c + (x, -0.08, 0.004), c + (x, -0.098, -0.012)], [(0.006, 0.006), (0.001, 0.001)],
                              n=5, up=(0, 0, 1))
                add(M.Part(V, F, "BH_Bone", name="claw"), bone=toe)

    # ---- tail: bushy, tapered, ragged
    pts = [H["tail.1"] + (0, -0.03, 0.01)] + [T["tail.%d" % i] for i in range(1, 5)]
    pts = [pts[0]] + [pts[0] + (pts[1] - pts[0]) * 0.5] + pts[1:] + [T["tail.4"] + (T["tail.4"] - H["tail.4"]) * 0.3]
    V, F = M.tube(pts, [(0.035, 0.04), (0.055, 0.06), (0.075, 0.08), (0.08, 0.085), (0.07, 0.075), (0.045, 0.05),
                        (0.012, 0.012)], n=12, up=(1, 0, 0))
    tail = M.Part(V, F, "BH_Fur", name="tail")
    tail.V += rng.normal(size=tail.V.shape) * 0.006
    add(tail, bones=["hips", "tail.1", "tail.2", "tail.3", "tail.4"], power=8, bias={"hips": 2.0})
    V, F = M.tube(pts[3:], [(0.06, 0.066), (0.052, 0.058), (0.034, 0.038), (0.01, 0.01)], n=10, up=(1, 0, 0))
    tip = M.Part(V, F, "BH_Hair", name="tailtip")
    tip.V *= 1.0
    c0 = np.array(pts[3])
    tip.V = c0 + (tip.V - c0) * 1.08
    add(tip, bones=["tail.2", "tail.3", "tail.4"], power=8)

    # ---- ragged mane: dark fur shards over the neck, withers and cheeks; back stripe tufts
    def tuft(base, direction, length, width, mat="BH_Hair"):
        d = direction / np.linalg.norm(direction)
        V, F = M.tube([base, base + d * length * 0.55, base + d * length], [(width, width * 0.6),
                      (width * 0.7, width * 0.4), (0.002, 0.002)], n=5, up=(1, 0, 0) if abs(d[0]) < 0.8 else (0, 0, 1))
        return M.Part(V, F, mat, name="tuft")
    for i in range(46):
        y = -0.58 + 0.34 * rng.random()          # neck to withers
        a = math.radians(-100 + 200 * rng.random())   # around the top of the neck
        # neck surface estimate
        t = (y + 0.58) / 0.34
        zc = 1.05 - 0.17 * t
        r = 0.085 + 0.05 * t
        base = np.array([r * math.sin(a), y, zc + r * math.cos(a) * 1.05])
        out = np.array([math.sin(a), 0.0, math.cos(a)])
        direction = out * 0.7 + np.array([0, 1.0, 0.25]) + rng.normal(size=3) * 0.2
        add(tuft(base, direction, 0.11 + 0.08 * rng.random(), 0.028), bones=["neck", "chest", "head"], power=6,
            bias={"head": 1.3})
    for i in range(12):                          # cheek ruff
        sx = 1 if i % 2 else -1
        y = -0.53 - 0.06 * rng.random()
        base = np.array([sx * 0.07, y, 1.0 + 0.06 * rng.random()])
        direction = np.array([sx * 0.8, 0.6, -0.3]) + rng.normal(size=3) * 0.2
        add(tuft(base, direction, 0.08, 0.02, "BH_Fur"), bones=["head", "neck"], power=6)
    for i in range(14):                          # back stripe
        y = -0.18 + 0.6 * i / 13
        r = [b for b in BODY if b[0] <= y + 0.08]
        zc = 0.93 if y < 0.35 else 0.9
        base = np.array([0.02 * (rng.random() - 0.5), y, zc])
        direction = np.array([0.0, 1.0, 0.45]) + rng.normal(size=3) * 0.15
        add(tuft(base, direction, 0.07 + 0.04 * rng.random(), 0.024), bones=["hips", "spine", "chest"], power=6)
    for i in range(10):                          # chest ruff (pale) + belly fringe
        x = (rng.random() - 0.5) * 0.16
        base = np.array([x, -0.4 + 0.1 * rng.random(), 0.72 + 0.06 * rng.random()])
        add(tuft(base, np.array([x * 2, 0.3, -1.0]), 0.08, 0.025, "BH_Stone"), bones=["chest", "neck"], power=6)
    return parts


# ------------------------------------------------------------------------------------------------ Blender side
def build_armature():
    import bpy
    arm = bpy.data.armatures.new("Armature")
    ob = bpy.data.objects.new("Armature", arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for b in ORDER:
        e = arm.edit_bones.new(b)
        e.head, e.tail = tuple(H[b]), tuple(T[b])
        e.align_roll((1.0, 0.0, 0.0))
        e.use_deform = b != "root"
        if PAR[b]:
            e.parent = eb[PAR[b]]
            e.use_connect = False
        eb[b] = e
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in ob.pose.bones:
        pb.rotation_mode = "QUATERNION"
    arm.display_type = "STICK"
    for b in ob.data.bones:     # sanity: numpy rest frames == Blender rest frames
        err = np.abs(np.array(b.matrix_local)[:3, :3] - R0[b.name]).max()
        assert err < 1e-4, (b.name, err)
    return ob


def mat_to_quat(R):
    from mathutils import Matrix
    q = Matrix(R.tolist()).to_quaternion()
    return np.array([q.w, q.x, q.y, q.z])


def bake(ob, clip):
    import bpy
    n = clip.frames + 1
    names = [b.name for b in ob.data.bones]
    quats = {b: np.zeros((n, 4)) for b in names}
    locs = np.zeros((n, 3))
    for f in range(n):
        ff = f % clip.frames if clip.loop else f
        c = clip.channels(float(ff))
        Rd, X = evaluate(c)
        for b in names:
            q = mat_to_quat(R0[b].T @ Rd[b] @ R0[b])
            if f > 0 and np.dot(q, quats[b][f - 1]) < 0:
                q = -q
            quats[b][f] = q
        # root: basis translation = R0^T (X(h) - h) with h = 0
        locs[f] = R0["root"].T @ X["root"].apply(H["root"])
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
        put('pose.bones["root"].location', i, locs[:, i])
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


def build_all(only=None):
    import bpy
    import bh_mesh as M
    import bh_materials as MT
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    mats = MT.make_materials("dire_wolf", vertex_color=False, extra=PALETTE)
    arm = build_armature()
    parts = build_mesh(mats)
    mesh = M.build_skinned("dire_wolf", parts, arm, mats, sharp_angle=50)
    MT.bake_vertex_ao(mesh, rays=16, dist=0.25, strength=0.6)
    acts = {}
    for c in clips():
        if only and c.name not in only:
            continue
        acts[c.name] = (c, bake(arm, c))
    return arm, mesh, acts


def write_meta(acts, path):
    anims = {}
    for name, (c, act) in acts.items():
        d = {"length": round(c.frames / FPS, 3), "loop": bool(c.loop)}
        if "hits" in c.meta:
            d["hits"] = [[round(a, 3), round(b, 3)] for a, b in c.meta["hits"]]
        if "ground_speed" in c.meta:
            d["ground_speed"] = c.meta["ground_speed"]
        anims[name] = d
    data = {"fps": FPS, "generator": "tools/blender/creatures/build_wolf.py",
            "notes": "dire_wolf clips (in place; hits = seconds where the jaws close / the body lands)",
            "animations": anims}
    with open(path, "w") as fh:
        json.dump(data, fh, indent=1)
    print("[dire_wolf] meta ->", path)


def export(arm, mesh, acts):
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
    GX.export_glb(OUT_GLB, [arm, mesh])
    print(f"[dire_wolf] -> {OUT_GLB} ({os.path.getsize(OUT_GLB) / 1e6:.1f} MB)")
    bad, got = GX.check_lengths(OUT_GLB, {n: c.frames / FPS for n, (c, a) in acts.items()})
    print(f"[dire_wolf] {len(got)} animations in the GLB; length mismatches: {bad}")


def preview(arm, acts, out_dir, clip_names, frames, views, res=300, tag="", dist=3.8, tz=0.5):
    import bpy
    import preview_enemy as PE
    PE.material_colors()
    cam = PE.setup(res)
    rows = []
    tmp = os.path.join(out_dir, "_wolf")
    os.makedirs(tmp, exist_ok=True)
    for cn in clip_names:
        if cn == "rest":
            assign_none = arm.animation_data
            if assign_none:
                assign_none.action = None
            for pb in arm.pose.bones:
                pb.rotation_quaternion = (1, 0, 0, 0)
                pb.location = (0, 0, 0)
            row = []
            for v in views:
                PE.place(cam, (0, 0, tz), dist, v, 12)
                p = os.path.join(tmp, f"rest_{int(v)}.png")
                bpy.context.scene.render.filepath = p
                bpy.ops.render.render(write_still=True)
                row.append(p)
            PE.place(cam, (0, 0, 0.4), 26.0, 20, 55)
            p = os.path.join(tmp, "rest_iso.png")
            bpy.context.scene.render.filepath = p
            bpy.ops.render.render(write_still=True)
            row.append(p)
            rows.append(row)
            continue
        c, act = acts[cn]
        assign(arm, act)
        for v in views:
            row = []
            for fr in frames:
                f = int(round(fr * c.frames))
                bpy.context.scene.frame_set(f)
                PE.place(cam, (0, -0.1, tz), dist, v, 10)
                p = os.path.join(tmp, f"{cn}_{int(v)}_{f}.png")
                bpy.context.scene.render.filepath = p
                bpy.ops.render.render(write_still=True)
                row.append(p)
            rows.append(row)
    from PIL import Image
    w = max(len(r) for r in rows) * res
    sheet = Image.new("RGB", (w, len(rows) * res), (20, 20, 24))
    for i, r in enumerate(rows):
        for j, p in enumerate(r):
            sheet.paste(Image.open(p).convert("RGB").resize((res, res)), (j * res, i * res))
    out = os.path.join(out_dir, f"dire_wolf_{tag or '_'.join(clip_names)[:60]}.png")
    sheet.save(out)
    print("PREVIEW", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", default="")
    ap.add_argument("--clips", default="rest")
    ap.add_argument("--frames", default="0,0.25,0.5,0.75")
    ap.add_argument("--views", default="90")
    ap.add_argument("--res", type=int, default=300)
    ap.add_argument("--tag", default="")
    ap.add_argument("--dist", type=float, default=3.8)
    ap.add_argument("--tz", type=float, default=0.5)
    ap.add_argument("--no-export", action="store_true")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    import bh_mesh as M
    names = [x for x in a.clips.split(",") if x]
    only = None if not a.no_export else set(n for n in names if n != "rest")
    arm, mesh, acts = build_all(only=only)
    print(f"[dire_wolf] mesh {M.tri_count(mesh)} tris, {len(acts)} clips")
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        preview(arm, acts, a.preview, names, [float(x) for x in a.frames.split(",")],
                [float(x) for x in a.views.split(",")], a.res, a.tag, a.dist, a.tz)
    if not a.no_export:
        write_meta(acts, OUT_META)
        export(arm, mesh, acts)


if __name__ == "__main__":
    main()
