"""Rootback Boar (bh-012, Builder B; Hollowroot Warren charger): heavy quadruped ~1.1 m at the shoulder, ~1.9 m
snout to rump. Bristly dark hide, a back armoured with bark plates and thorny root spines grown over with moss and
small glowing fungi, two big curving pale-wood tusks, small amber glowing eyes, short sturdy legs with hooves.
Own armature, skinned mesh and baked procedural clips (rig / planar leg IK / gait machinery copied from
build_wolf.py, which is not modified).

  "<blender>" -b --factory-startup --python build_rootback_boar.py -- [--preview DIR --clips rest,walk --frames ..]
                                                                      [--no-export]
Export: game/assets/characters/rootback_boar.glb; merges ONLY the boar_* clip keys (+ models.rootback_boar) into
creature_meta.json. Conventions: Blender Z-up, faces -Y (= +Z in Godot), origin on the ground under the body,
meters, 30 fps, clips in place (boar_charge is a 1.0 s one-shot whose first and last frames match so the game can
replay it back to back while it runs).
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHAR = os.path.join(HERE, "..", "characters")
sys.path.insert(0, CHAR)
sys.path.insert(0, HERE)
ROOT_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT_GLB = os.path.join(ROOT_DIR, "game", "assets", "characters", "rootback_boar.glb")
OUT_META = os.path.join(ROOT_DIR, "game", "assets", "characters", "creature_meta.json")
NAME = "rootback_boar"

import numpy as np  # noqa: E402

FPS = 30
PALETTE = {
    "BH_Fur": ((0.075, 0.055, 0.045), 0.0, 0.92, None, 0.0, 1.0),          # bristly dark hide
    "BH_Hair": ((0.03, 0.024, 0.022), 0.0, 0.9, None, 0.0, 1.0),           # black bristle crest / tail tuft
    "BH_Wood": ((0.24, 0.16, 0.085), 0.0, 0.85, None, 0.0, 1.0),          # bark plates
    "BH_Horn": ((0.12, 0.075, 0.04), 0.0, 0.75, None, 0.0, 1.0),           # thorny root spines, bark grain
    "BH_Bone": ((0.62, 0.55, 0.4), 0.0, 0.6, None, 0.0, 1.0),              # pale-wood tusks
    "BH_Cloth_Secondary": ((0.075, 0.14, 0.03), 0.0, 0.95, None, 0.0, 1.0),  # moss
    "BH_Flesh": ((0.3, 0.17, 0.15), 0.0, 0.5, None, 0.0, 1.0),             # snout disc, inner ears
    "BH_Shadow": ((0.02, 0.018, 0.016), 0.0, 0.5, None, 0.0, 1.0),          # nostrils, hooves, mouth
    "BH_Skin": ((0.55, 0.49, 0.37), 0.0, 0.6, None, 0.0, 1.0),             # pale fungus stalks
    "BH_Aether": ((1.0, 0.55, 0.12), 0.0, 0.3, (1.0, 0.55, 0.1), 5.0, 1.0),  # small amber eyes
    "BH_Emissive": ((0.75, 1.0, 0.3), 0.0, 0.4, (0.75, 1.0, 0.3), 6.0, 1.0),  # glowing fungi on the back
}

# ------------------------------------------------------------------------------------------------ skeleton
# name: (head, tail, parent)
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.25), None),
    "hips": ((0, 0.6, 0.95), (0, 0.28, 1.0), "root"),
    "spine": ((0, 0.28, 1.0), (0, -0.08, 1.02), "hips"),
    "chest": ((0, -0.08, 1.02), (0, -0.46, 0.98), "spine"),
    "neck": ((0, -0.46, 0.94), (0, -0.7, 0.86), "chest"),
    "head": ((0, -0.7, 0.86), (0, -1.16, 0.56), "neck"),
    "jaw": ((0, -0.78, 0.7), (0, -1.04, 0.54), "head"),
    "tail.1": ((0, 0.66, 0.93), (0, 0.73, 0.86), "hips"),
    "tail.2": ((0, 0.73, 0.86), (0, 0.77, 0.76), "tail.1"),
    "tail.3": ((0, 0.77, 0.76), (0, 0.79, 0.66), "tail.2"),
    "tail.4": ((0, 0.79, 0.66), (0, 0.8, 0.58), "tail.3"),
}
for _s, _x in (("L", 1.0), ("R", -1.0)):
    BONES.update({
        f"ear.{_s}": ((0.1 * _x, -0.74, 0.97), (0.16 * _x, -0.71, 1.06), "head"),
        f"scap.{_s}": ((0.17 * _x, -0.3, 0.95), (0.19 * _x, -0.36, 0.72), "chest"),
        f"upperarm.{_s}": ((0.19 * _x, -0.36, 0.72), (0.19 * _x, -0.28, 0.47), f"scap.{_s}"),
        f"forearm.{_s}": ((0.19 * _x, -0.28, 0.47), (0.19 * _x, -0.32, 0.17), f"upperarm.{_s}"),
        f"fpaw.{_s}": ((0.19 * _x, -0.32, 0.17), (0.19 * _x, -0.35, 0.05), f"forearm.{_s}"),
        f"ftoe.{_s}": ((0.19 * _x, -0.35, 0.05), (0.19 * _x, -0.43, 0.02), f"fpaw.{_s}"),
        f"thigh.{_s}": ((0.17 * _x, 0.56, 0.91), (0.18 * _x, 0.42, 0.6), "hips"),
        f"shin.{_s}": ((0.18 * _x, 0.42, 0.6), (0.18 * _x, 0.58, 0.32), f"thigh.{_s}"),
        f"hpaw.{_s}": ((0.18 * _x, 0.58, 0.32), (0.18 * _x, 0.55, 0.05), f"shin.{_s}"),
        f"htoe.{_s}": ((0.18 * _x, 0.55, 0.05), (0.18 * _x, 0.47, 0.02), f"hpaw.{_s}"),
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
PIVOT = np.array([0.0, 0.12, 0.92])     # body rotation pivot (centre of mass)


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
    # ---- idle: heavy breathing, snout sniffing the ground, tail flick, ear twitch
    c = Clip("idle", 90, loop=True)
    c.key(0, neck_pitch=0.0)
    c.layer(lambda f, cl: {"chest.pitch": 1.5 * cyc(f, 90, 2), "body.up": 0.006 * cyc(f, 90, 2),
                           "neck.pitch": -4 + 3.0 * cyc(f, 90, 1, 0.1), "head.pitch": 2 * cyc(f, 90, 3, 0.2),
                           "head.yaw": 3 * cyc(f, 90, 1, 0.3), "tail.wag": 14 * cyc(f, 90, 3), "tail.lift": -10.0,
                           "ear.R": 14 * max(0.0, cyc(f, 90, 2)) ** 8, "jaw": 1 + 1.5 * cyc(f, 90, 2, 0.25)})
    C.append(c)
    # ---- idle_look: head swings left / right, snort
    c = Clip("idle_look", 75)
    c.key(0).key(14, neck_yaw=18, head_yaw=14, neck_pitch=6, ears=-8).key(30, neck_yaw=20, head_yaw=16, neck_pitch=6)
    c.key(44, neck_yaw=-18, head_yaw=-14, neck_pitch=4, head_roll=-5).key(58, neck_yaw=-16, head_yaw=-12, jaw=8)
    c.key(75, neck_yaw=0, head_yaw=0, neck_pitch=0, ears=0, head_roll=0, jaw=0)
    c.layer(lambda f, cl: {"tail.lift": -10.0, "tail.wag": 10 * cyc(f, 75, 2)})
    C.append(c)
    # ---- walk: heavy 4-beat walk
    WALK_P, WALK_V = 36, 1.1
    c = Clip("walk", WALK_P, loop=True, ground_speed=WALK_V)
    c.key(0)
    c.layer(gait_layer(WALK_P, 0.65, WALK_V, {"LH": 0.0, "LF": 0.25, "RH": 0.5, "RF": 0.75}, 0.09, 0.08, 45, 25, 15))
    c.layer(lambda f, cl: {"body.up": -0.015 + 0.012 * cyc(f, WALK_P, 2), "body.roll": 2.5 * cyc(f, WALK_P, 1),
                           "neck.pitch": -5 + 3 * cyc(f, WALK_P, 2, 0.2), "head.yaw": 3 * cyc(f, WALK_P, 1, 0.1),
                           "spine.yaw": 2 * cyc(f, WALK_P, 1), "tail.lift": -12, "tail.wag": 10 * cyc(f, WALK_P, 1)})
    C.append(c)
    # ---- run / run_combat: heavy trot (diagonal pairs) with a big body bounce, head low
    RUN_P, RUN_V = 20, 4.4
    for nm in ("run", "run_combat"):
        c = Clip(nm, RUN_P, loop=True, ground_speed=RUN_V)
        c.key(0)
        c.layer(gait_layer(RUN_P, 0.42, RUN_V, {"LH": 0.0, "RF": 0.04, "RH": 0.5, "LF": 0.54}, 0.15, 0.13, 70, 35, 18))
        low = nm == "run_combat"
        c.layer(lambda f, cl, low=low: {
            "body.up": (-0.05 if low else -0.03) + 0.03 * cyc(f, RUN_P, 2, 0.1), "body.pitch": 2 * cyc(f, RUN_P, 2, 0.3),
            "body.roll": 2 * cyc(f, RUN_P, 1), "spine.pitch": 2 * cyc(f, RUN_P, 2, 0.5),
            "neck.pitch": (-16 if low else -9) + 4 * cyc(f, RUN_P, 2, 0.8), "head.pitch": -6 if low else -2,
            "ears": 25 if low else 12, "tail.lift": 15 + 8 * cyc(f, RUN_P, 2, 0.2), "jaw": 6})
        C.append(c)
    # ---- reactions
    c = Clip("hit_light", 12)
    c.key(0).key(3, body_fwd=-0.05, body_pitch=4, neck_pitch=12, head_pitch=6, neck_yaw=8, ears=30, jaw=12)
    c.key(12, body_fwd=0, body_pitch=0, neck_pitch=0, head_pitch=0, neck_yaw=0, ears=0, jaw=0)
    C.append(c)
    c = Clip("hit_heavy", 18)
    c.key(0).key(4, body_fwd=-0.12, body_up=-0.05, body_pitch=7, body_roll=5, neck_pitch=20, head_pitch=10,
                 neck_yaw=14, ears=45, jaw=20, tail_lift=-20, LF_f=0.06, RF_f=0.04)
    c.key(9, body_fwd=-0.1, body_up=-0.04, body_pitch=5, body_roll=3, neck_pitch=12, head_pitch=4, neck_yaw=8,
          ears=35, jaw=8, tail_lift=-16, LF_f=0.1, RF_f=0.06)
    c.key(18, body_fwd=0, body_up=0, body_pitch=0, body_roll=0, neck_pitch=0, head_pitch=0, neck_yaw=0, ears=0,
          jaw=0, tail_lift=0, LF_f=0, RF_f=0)
    C.append(c)
    c = Clip("stagger_small", 24)
    c.key(0).key(5, body_fwd=-0.09, body_side=-0.05, body_roll=-7, body_pitch=5, neck_pitch=14, neck_yaw=-16,
                 ears=35, tail_lift=-16)
    c.key(9, LF_up=0.08, LF_f=-0.03, body_fwd=-0.12, body_side=-0.06, body_roll=-8, neck_pitch=10, neck_yaw=-12)
    c.key(14, LF_up=0.0, LF_f=-0.12, RH_f=-0.08, body_fwd=-0.1, body_roll=-4, body_side=-0.03, neck_pitch=6)
    c.key(24, LF_f=0, RH_f=0, body_fwd=0, body_side=0, body_roll=0, body_pitch=0, neck_pitch=0, neck_yaw=0, ears=0,
          tail_lift=0)
    C.append(c)
    c = Clip("knockback", 27)
    c.key(0).key(4, body_fwd=-0.2, body_up=0.03, body_pitch=12, neck_pitch=18, ears=45, jaw=22, tail_lift=-24,
                 LF_up=0.14, RF_up=0.1, LF_f=0.08, RF_f=0.1, LH_f=0.16, RH_f=0.14, hips_pitch=-6)
    c.key(11, body_fwd=-0.3, body_up=-0.08, body_pitch=5, neck_pitch=8, ears=40, jaw=8, tail_lift=-24,
          LF_up=0.0, RF_up=0.0, LF_f=0.12, RF_f=0.08, LH_f=0.2, RH_f=0.18, hips_pitch=-3)
    c.key(18, body_fwd=-0.18, body_up=-0.05, body_pitch=2, neck_pitch=4, ears=20, jaw=4, tail_lift=-14,
          LF_f=0.06, RF_f=0.02, LH_f=0.1, RH_f=0.12, hips_pitch=0)
    c.key(27, body_fwd=0, body_up=0, body_pitch=0, neck_pitch=0, ears=0, jaw=0, tail_lift=0, LF_f=0, RF_f=0,
          LH_f=0, RH_f=0)
    C.append(c)
    # ---- deaths
    C.append(death_clip("death", side=1, first="front"))
    C.append(death_clip("death_back", side=-1, first="hind"))
    # ---- alert: head up, snort, paws the ground with the right foreleg
    c = Clip("alert", 30)
    c.key(0).key(7, neck_pitch=14, head_pitch=-6, ears=-12, tail_lift=25, body_up=0.02, jaw=10)
    c.key(12, neck_pitch=6, head_pitch=-4, ears=-10, tail_lift=25, RF_up=0.1, RF_f=0.08, jaw=4)
    c.key(17, neck_pitch=0, head_pitch=-2, ears=-10, tail_lift=25, RF_up=0.0, RF_f=-0.06, jaw=2)
    c.key(22, neck_pitch=-6, head_pitch=-4, ears=-10, tail_lift=22, RF_up=0.06, RF_f=0.03)
    c.key(30, neck_pitch=-4, head_pitch=0, ears=-6, tail_lift=12, body_up=0.0, RF_up=0, RF_f=0, jaw=0)
    C.append(c)
    # ---- attacks
    # boar_gore: head dips low, then a hooking upward swipe of the tusks (toward its right), recover
    c = Clip("boar_gore", 30, hits=[[11 / FPS, 16 / FPS]])
    c.key(0).key(8, body_fwd=-0.06, body_up=-0.06, body_pitch=-5, neck_pitch=-22, head_pitch=-18, neck_yaw=10,
                 ears=30, tail_lift=10, LH_f=0.04, RH_f=0.04)
    c.key(12, body_fwd=0.18, body_up=-0.03, body_pitch=-2, neck_pitch=4, head_pitch=6, neck_yaw=-6, head_roll=-10,
          jaw=10, ears=35, LF_f=0.14, RF_f=0.1)
    c.key(16, body_fwd=0.22, body_up=0.02, body_pitch=6, neck_pitch=26, head_pitch=22, neck_yaw=-16, head_yaw=-10,
          head_roll=-18, jaw=14, LF_f=0.18, RF_f=0.14, LF_up=0.04)
    c.key(21, body_fwd=0.14, body_pitch=3, neck_pitch=14, head_pitch=10, neck_yaw=-10, head_yaw=-6, head_roll=-8,
          jaw=6, LF_f=0.16, RF_f=0.12, LF_up=0.0)
    c.key(30, body_fwd=0, body_up=0, body_pitch=0, neck_pitch=0, head_pitch=0, neck_yaw=0, head_yaw=0, head_roll=0,
          jaw=0, ears=0, tail_lift=0, LF_f=0, RF_f=0, LH_f=0, RH_f=0)
    C.append(c)
    # boar_charge: head-down charging gallop, 1.0 s = 2 gait cycles; first frame == last frame (replayable)
    CH_P, CH_V = 15, 6.0
    c = Clip("boar_charge", 30, hits=[[3 / FPS, 27 / FPS]], ground_speed=CH_V)
    base = dict(neck_pitch=-24, head_pitch=-12, ears=35, tail_lift=30, jaw=6, body_up=-0.07, body_pitch=-3)
    c.key(0, **base).key(30, **base)
    c.layer(gait_layer(CH_P, 0.36, CH_V, {"LH": 0.0, "RH": 0.12, "RF": 0.45, "LF": 0.57}, 0.16, 0.14, 75, 38, 18))
    c.layer(lambda f, cl: {"body.up": 0.03 * cyc(f, CH_P, 1, 0.1), "body.pitch": 3 * cyc(f, CH_P, 1, 0.35),
                           "spine.pitch": 4 * cyc(f, CH_P, 1, 0.55), "neck.pitch": 3 * cyc(f, CH_P, 1, 0.8),
                           "head.yaw": 3 * cyc(f, 30, 1)})
    C.append(c)
    # boar_stomp: rears up on the hind legs, then slams both forelegs down
    c = Clip("boar_stomp", 36, hits=[[19 / FPS, 22 / FPS]])
    c.key(0).key(5, body_up=-0.05, body_pitch=-4, neck_pitch=-8, LF_f=-0.04, RF_f=-0.04, LH_f=-0.05, RH_f=-0.05)
    c.key(13, body_up=0.06, body_fwd=-0.06, body_pitch=24, neck_pitch=16, head_pitch=6, jaw=24, ears=30,
          tail_lift=-10, hips_pitch=-6, LF_up=0.42, RF_up=0.4, LF_f=0.12, RF_f=0.1, LF_phi=55, RF_phi=55,
          LH_f=0.1, RH_f=0.1)
    c.key(16, body_up=0.07, body_fwd=-0.04, body_pitch=27, neck_pitch=20, head_pitch=8, jaw=28, ears=30,
          tail_lift=-10, hips_pitch=-7, LF_up=0.48, RF_up=0.46, LF_f=0.14, RF_f=0.12, LF_phi=60, RF_phi=60,
          LH_f=0.1, RH_f=0.1)
    c.key(20, body_up=-0.09, body_fwd=0.08, body_pitch=-8, neck_pitch=-18, head_pitch=-10, jaw=10, ears=40,
          tail_lift=6, hips_pitch=2, LF_up=0.0, RF_up=0.0, LF_f=0.2, RF_f=0.19, LF_phi=0, RF_phi=0, LH_f=0.02,
          RH_f=0.02)
    c.key(25, body_up=-0.07, body_fwd=0.07, body_pitch=-6, neck_pitch=-14, head_pitch=-6, jaw=4, LF_f=0.2,
          RF_f=0.19)
    c.key(36, body_up=0, body_fwd=0, body_pitch=0, neck_pitch=0, head_pitch=0, jaw=0, ears=0, tail_lift=0,
          hips_pitch=0, LF_f=0, RF_f=0, LH_f=0, RH_f=0)
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
    k3 = dict(body_up=-0.6, body_pitch=0, body_roll=r, body_side=-0.1 * side, neck_pitch=-14, neck_yaw=-6 * side,
              head_pitch=-10, head_roll=10 * side, ears=50, jaw=18, tail_lift=-6, tail_yaw=12 * side)
    legs = {"LF": (0.18, 0.12), "RF": (0.08, 0.2), "LH": (-0.12, 0.2), "RH": (0.02, 0.24)}
    for k, (lf, lup) in legs.items():
        k3[k + "_loc"] = 1.0
        k3[k + "_lf"] = lf
        k3[k + "_lup"] = lup
    c.key(30, **k3)
    k4 = dict(k3, body_up=-0.62, neck_pitch=-20, head_pitch=-14, jaw=12, ears=60)
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
    import kit_warren as KW
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

    TORSO_B = ["hips", "spine", "chest", "neck", "scap.L", "scap.R", "thigh.L", "thigh.R", "tail.1"]
    TORSO_BIAS = {"scap.L": 1.5, "scap.R": 1.5, "thigh.L": 1.35, "thigh.R": 1.35, "tail.1": 1.6, "neck": 1.2}
    BACK_B = ["hips", "spine", "chest", "neck"]
    # ---- barrel body with high withers; rings rump -> front (y, z centre, half width, top, bottom)
    BODY = [(0.74, 0.9, 0.08, 0.07, 0.08), (0.67, 0.9, 0.17, 0.13, 0.17), (0.54, 0.9, 0.22, 0.16, 0.23),
            (0.36, 0.9, 0.25, 0.17, 0.3), (0.16, 0.9, 0.26, 0.18, 0.33), (-0.04, 0.9, 0.27, 0.21, 0.34),
            (-0.22, 0.9, 0.27, 0.24, 0.33), (-0.38, 0.88, 0.24, 0.22, 0.29), (-0.5, 0.85, 0.2, 0.19, 0.24),
            (-0.6, 0.81, 0.16, 0.15, 0.18)]
    rings = [ring(y, z, rx, rt, rb, n=22) for (y, z, rx, rt, rb) in BODY]
    V, F = M.loft(rings[::-1], cap0=True, cap1=True)
    body = M.Part(V, F, "BH_Fur", name="body")
    body.V += rng.normal(size=body.V.shape) * 0.004
    add(body, bones=TORSO_B, bias=TORSO_BIAS)

    def top_z(y):
        for (y0, z0, rx0, rt0, rb0), (y1, z1, rx1, rt1, rb1) in zip(BODY, BODY[1:]):
            if y1 <= y <= y0:
                t = (y0 - y) / (y0 - y1)
                return z0 + (z1 - z0) * t + rt0 + (rt1 - rt0) * t, rx0 + (rx1 - rx0) * t, rt0 + (rt1 - rt0) * t
        return BODY[-1][1] + BODY[-1][3], BODY[-1][2], BODY[-1][3]

    # ---- neck + wedge head
    NECK = [(-0.54, 0.83, 0.19, 0.18, 0.21), (-0.64, 0.8, 0.17, 0.15, 0.18), (-0.72, 0.78, 0.15, 0.13, 0.15)]
    V, F = M.loft([ring(*r, n=16) for r in NECK][::-1], cap0=False, cap1=False)
    add(M.Part(V, F, "BH_Fur", name="neck"), bones=["chest", "neck", "head"], bias={"head": 1.3})
    SKULL = [(-0.66, 0.83, 0.12, 0.13, 0.12), (-0.76, 0.8, 0.14, 0.13, 0.13), (-0.86, 0.75, 0.125, 0.1, 0.11),
             (-0.96, 0.69, 0.095, 0.075, 0.085), (-1.04, 0.635, 0.075, 0.06, 0.065), (-1.1, 0.6, 0.064, 0.052, 0.055),
             (-1.14, 0.585, 0.058, 0.048, 0.05)]
    V, F = M.loft([ring(*r, n=16) for r in SKULL][::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Fur", name="skull"), bone="head")
    # snout disc + nostrils
    V, F = M.sphere(0.064, 12, 5, center=(0, -1.155, 0.585), scale=(1.0, 0.35, 0.85))
    add(M.Part(V, F, "BH_Flesh", name="snout"), bone="head")
    for sx in (1, -1):
        V, F = M.sphere(0.015, 6, 4, center=(sx * 0.024, -1.175, 0.583), scale=(1.0, 0.5, 1.3))
        add(M.Part(V, F, "BH_Shadow", name="nostril"), bone="head")
    JAW = [(-0.8, 0.66, 0.09, 0.03, 0.045), (-0.92, 0.6, 0.075, 0.025, 0.035), (-1.03, 0.56, 0.055, 0.02, 0.026)]
    V, F = M.loft([ring(*r, n=12) for r in JAW][::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Fur", name="jaw"), bone="jaw")
    V, F = M.loft([ring(y, z + 0.03, rx * 1.02, 0.008, 0.01, n=12) for (y, z, rx, rt, rb) in JAW][::-1])
    add(M.Part(V, F, "BH_Shadow", name="lips"), bone="jaw")
    # tusks: big curving pale-wood tusks from the lower jaw, sweeping out, up and back
    for sx in (1, -1):
        pts = [(sx * 0.06, -0.99, 0.6), (sx * 0.11, -1.07, 0.64), (sx * 0.17, -1.08, 0.72), (sx * 0.2, -1.03, 0.8),
               (sx * 0.19, -0.96, 0.86)]
        add(KW.root(pts, 0.03, 0.004, "BH_Bone", n=8, seed=3 + (sx > 0), knot=0.05), bone="jaw")
        # small upper tusk
        add(KW.root([(sx * 0.055, -1.05, 0.6), (sx * 0.085, -1.09, 0.65), (sx * 0.1, -1.08, 0.7)], 0.014, 0.003,
                    "BH_Bone", n=6, seed=9), bone="head")
    # eyes: small, amber, deep-set under a bristly brow
    for sx in (1, -1):
        V, F = M.sphere(0.016, 8, 5, center=(sx * 0.105, -0.86, 0.8), scale=(0.8, 1.1, 0.8))
        add(M.Part(V, F, "BH_Aether", name="eye"), bone="head")
        V, F = M.sphere(0.03, 8, 4, center=(sx * 0.1, -0.85, 0.825), scale=(1.1, 1.3, 0.45))
        add(M.Part(V, F, "BH_Hair", name="brow"), bone="head")
    # ears: small leaf ears, cupped
    for s, sx in (("L", 1), ("R", -1)):
        h = H["ear." + s]
        V, F = M.prism(np.array([(-0.045, -0.01), (0.045, -0.01), (0.02, 0.08), (0.0, 0.11), (-0.02, 0.08)]),
                       0.018, axis="y")
        e = M.Part(V, F, "BH_Fur", name="ear")
        e.V[:, 1] += 0.02 * (np.abs(e.V[:, 0]) / 0.045) ** 2
        e.rot(Rz(-25 * sx)).rot(Rx(-20)).move(h + (0, 0, -0.01))
        add(e, bone="ear." + s)
        V, F = M.prism(np.array([(-0.028, 0.0), (0.028, 0.0), (0.0, 0.075)]), 0.004, axis="y")
        add(M.Part(V, F, "BH_Flesh", name="ear_in").rot(Rz(-25 * sx)).rot(Rx(-20)).move(h + (0, -0.012, 0.0)),
            bone="ear." + s)

    # ---- legs: short and sturdy, hooves
    def leg_tube(chain, radii, mat="BH_Fur"):
        pts = [H[chain[0]]] + [T[b] for b in chain]
        V, F = M.tube(pts, radii, n=12, up=(0, -1, 0))
        return M.Part(V, F, mat, name="leg")
    for s, sx in (("L", 1), ("R", -1)):
        p = leg_tube(["scap." + s, "upperarm." + s, "forearm." + s, "fpaw." + s],
                     [(0.13, 0.16), (0.13, 0.14), (0.09, 0.1), (0.065, 0.07), (0.055, 0.06)])
        add(p, bones=["scap." + s, "upperarm." + s, "forearm." + s, "fpaw." + s, "chest"], power=8,
            bias={"chest": 1.6})
        p = leg_tube(["thigh." + s, "shin." + s, "hpaw." + s],
                     [(0.15, 0.18), (0.12, 0.14), (0.075, 0.08), (0.055, 0.06)])
        p.V[:, 0] += 0.01 * sx
        add(p, bones=["hips", "thigh." + s, "shin." + s, "hpaw." + s], power=8, bias={"hips": 1.8})
        V, F = M.sphere(0.17, 14, 8, center=(0.12 * sx, 0.5, 0.78), scale=(0.7, 1.1, 1.2))
        add(M.Part(V, F, "BH_Fur", name="haunch"), bones=["hips", "thigh." + s], power=6, bias={"hips": 0.9})
        for toe, meta in (("ftoe." + s, "fpaw." + s), ("htoe." + s, "hpaw." + s)):
            c = H[toe]
            for dx in (-0.022, 0.022):          # cloven hoof
                V, F = M.lathe([(0.0, 0.0), (0.03, 0.0), (0.026, 0.05), (0.0, 0.062)], 8)
                hf = M.Part(V, F, "BH_Shadow", name="hoof").scale((0.8, 1.3, 1.0)).rot(Rx(-35)).move(
                    c + (dx, -0.035, -0.035))
                add(hf, bone=toe)
            V, F = M.sphere(0.05, 10, 5, center=c + (0, 0.01, 0.03), scale=(0.95, 1.0, 0.9))
            add(M.Part(V, F, "BH_Fur", name="pastern"), bone=meta)
            for dx in (-0.04, 0.04):            # dew claws
                V, F = M.sphere(0.012, 6, 3, center=H[meta] + (T[meta] - H[meta]) * 0.7 + (dx, 0.04, 0.0))
                add(M.Part(V, F, "BH_Shadow", name="dew"), bone=meta)

    # ---- short tail with a black tuft
    pts = [H["tail.1"] + (0, -0.02, 0.01)] + [T["tail.%d" % i] for i in range(1, 5)]
    V, F = M.tube(pts, [(0.03, 0.03), (0.025, 0.025), (0.02, 0.02), (0.016, 0.016), (0.012, 0.012)], n=8,
                  up=(1, 0, 0))
    add(M.Part(V, F, "BH_Fur", name="tail"), bones=["hips", "tail.1", "tail.2", "tail.3", "tail.4"], power=8,
        bias={"hips": 2.0})
    for k in range(6):
        d = np.array([0.4 * (rng.random() - 0.5), 0.2, -1.0])
        b = T["tail.4"] + (0, 0, 0.04)
        V, F = M.tube([b, b + d * 0.06, b + d * 0.12], [(0.012, 0.008), (0.009, 0.006), (0.002, 0.002)], n=4,
                      up=(1, 0, 0))
        add(M.Part(V, F, "BH_Hair", name="tuft"), bone="tail.4")

    # ---- bristles: crest along the neck and a coarse coat on the flanks / cheeks
    def tuft(base, direction, length, width, mat="BH_Hair"):
        d = direction / np.linalg.norm(direction)
        V, F = M.tube([base, base + d * length * 0.55, base + d * length], [(width, width * 0.6),
                      (width * 0.7, width * 0.4), (0.002, 0.002)], n=4, up=(1, 0, 0) if abs(d[0]) < 0.8 else (0, 0, 1))
        return M.Part(V, F, mat, name="tuft")
    for i in range(26):                          # crest over the neck / withers (in front of the plates)
        y = -0.72 + 0.4 * rng.random()
        zt, rx, rt = top_z(y) if y > -0.6 else (0.93 + (y + 0.72) * 0.6, 0.15, 0.13)
        base = np.array([(rng.random() - 0.5) * 0.06, y, zt - 0.01])
        add(tuft(base, np.array([0, 0.7, 1.0]) + rng.normal(size=3) * 0.2, 0.14 + 0.06 * rng.random(), 0.024),
            bones=["neck", "chest", "head"], power=6, bias={"head": 1.3})
    for i in range(40):                          # coarse bristles on the flanks
        y = -0.5 + 1.1 * rng.random()
        sx = 1 if i % 2 else -1
        zt, rx, rt = top_z(y)
        a = math.radians(-30 + 40 * rng.random())
        base = np.array([sx * rx * math.cos(a), y, zt - rt + rt * math.sin(a) * 0.7])
        add(tuft(base, np.array([sx * 0.6, 0.8, -0.4]) + rng.normal(size=3) * 0.2, 0.06, 0.015, "BH_Fur"),
            bones=TORSO_B, power=6, bias=TORSO_BIAS)
    for i in range(10):                          # cheek bristles
        sx = 1 if i % 2 else -1
        base = np.array([sx * 0.12, -0.8 - 0.06 * rng.random(), 0.74 + 0.05 * rng.random()])
        add(tuft(base, np.array([sx * 0.8, 0.6, -0.4]) + rng.normal(size=3) * 0.2, 0.08, 0.018),
            bones=["head", "neck"], power=6)

    # ---- back armour: overlapping bark plates from the withers to the rump
    plate_rows = [(-0.36, 3), (-0.2, 3), (-0.04, 3), (0.12, 3), (0.28, 3), (0.44, 3), (0.58, 2)]
    for j, (y, cnt) in enumerate(plate_rows):
        zt, rx, rt = top_z(y)
        for k in range(cnt):
            f = (k - (cnt - 1) / 2) / max(cnt - 1, 1)
            a = f * 1.0                           # radians around the back from the top
            nrm = np.array([math.sin(a), 0.25, math.cos(a)])
            nrm /= np.linalg.norm(nrm)
            c = np.array([rx * 0.95 * math.sin(a), y, zt - rt + rt * math.cos(a)]) + nrm * 0.02
            w, ln = 0.2 - 0.03 * abs(f), 0.2
            V, F = M.box(w, ln, 0.035)
            pl = M.bevel(M.Part(V, F, "BH_Wood", name="plate"), 0.012, 1)
            pl.V[:, 2] += 0.35 * (pl.V[:, 0] / w) ** 2 * -0.1 + 0.05 * (pl.V[:, 1] / ln)   # curved, shingled
            pl.V += rng.normal(size=pl.V.shape) * 0.004
            R = np.stack([np.cross((0, 1, 0), nrm) / max(np.linalg.norm(np.cross((0, 1, 0), nrm)), 1e-6),
                          np.cross(nrm, np.cross((0, 1, 0), nrm)) / max(np.linalg.norm(np.cross((0, 1, 0), nrm)), 1e-6),
                          nrm], 1)
            pl.V = pl.V @ R.T + c
            add(pl, bones=BACK_B, power=6)
            # bark grain ridges
            for g in (-0.4, 0.0, 0.4):
                q0 = c + R @ np.array([g * w * 0.5, -ln * 0.45, 0.02])
                q1 = c + R @ np.array([g * w * 0.5, ln * 0.45, 0.022])
                V, F = M.tube([q0, q1], [(0.006, 0.004)] * 2, n=4, up=nrm)
                add(M.Part(V, F, "BH_Horn", name="grain"), bones=BACK_B, power=6)
    # thorny root spines between / on the plates, raked backwards; tallest over the withers
    for i in range(22):
        y = -0.42 + 1.0 * (i / 21) + 0.02 * rng.random()
        zt, rx, rt = top_z(y)
        a = (rng.random() - 0.5) * 1.3
        nrm = np.array([math.sin(a), 0.0, math.cos(a)])
        base = np.array([rx * 0.9 * math.sin(a), y, zt - rt + rt * math.cos(a)]) + nrm * 0.02
        h = (0.3 if y < 0.0 else 0.2) * (0.6 + 0.5 * rng.random())
        d = nrm + np.array([0, 0.7, 0.0])
        d /= np.linalg.norm(d)
        pts = [base, base + d * h * 0.5 + nrm * 0.02, base + d * h + np.array([0, 0.03, 0.02])]
        add(KW.root(pts, 0.03, 0.002, "BH_Horn", n=6, seed=100 + i, knot=0.2), bones=BACK_B, power=6)
    # moss on the plates and small glowing fungi
    for i in range(12):
        y = -0.4 + 1.0 * rng.random()
        zt, rx, rt = top_z(y)
        a = (rng.random() - 0.5) * 1.6
        nrm = np.array([math.sin(a), 0.1, math.cos(a)])
        c = np.array([rx * math.sin(a), y, zt - rt + rt * math.cos(a)]) + nrm * 0.04
        V, F = M.sphere(0.04 + 0.03 * rng.random(), 8, 4, scale=(1.2, 1.3, 0.35))
        m = M.Part(V, F, "BH_Cloth_Secondary", name="moss")
        m.V += rng.normal(size=m.V.shape) * 0.006
        m.rot(KW.M_align_z(nrm)).move(c)
        add(m, bones=BACK_B, power=6)
    for i in range(9):
        y = -0.35 + 0.95 * (i / 8)
        zt, rx, rt = top_z(y)
        a = (0.8 if i % 2 else -0.8) + 0.3 * (rng.random() - 0.5)
        nrm = np.array([math.sin(a), 0.1, math.cos(a)])
        c = np.array([rx * math.sin(a), y, zt - rt + rt * math.cos(a)]) + nrm * 0.035
        for k in range(2):
            off = np.array([0.03 * k, 0.03 * k, 0.0])
            for p in KW.mushroom(c + off, nrm + np.array([0, 0, 0.5]), 0.05 + 0.03 * k, 0.01, 0.035 - 0.008 * k,
                                 0.025, "BH_Skin", "BH_Emissive", "BH_Emissive", n=8, seed=i * 3 + k):
                add(p, bones=BACK_B, power=6)
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
    mats = MT.make_materials(NAME, vertex_color=False, extra=PALETTE)
    arm = build_armature()
    parts = build_mesh(mats)
    mesh = M.build_skinned(NAME, parts, arm, mats, sharp_angle=50)
    MT.bake_vertex_ao(mesh, rays=16, dist=0.25, strength=0.6)
    acts = {}
    for c in clips():
        if only and c.name not in only:
            continue
        acts[c.name] = (c, bake(arm, c))
    return arm, mesh, acts


def write_meta(acts, path, tris=0, bones=0):
    """Merge ONLY this model's keys: animations.boar_* and models.rootback_boar. Re-read right before writing (other
    builders merge into the same file), keep every other key, write, re-read and verify."""
    mine = {}
    clips_all = {}
    for name, (c, act) in acts.items():
        d = {"length": round(c.frames / FPS, 3), "loop": bool(c.loop)}
        if "hits" in c.meta:
            d["hits"] = [[round(a, 3), round(b, 3)] for a, b in c.meta["hits"]]
        if "ground_speed" in c.meta:
            d["ground_speed"] = c.meta["ground_speed"]
        clips_all[name] = d
        if name.startswith("boar_"):
            mine[name] = d
    model = {"generator": "tools/blender/creatures/build_rootback_boar.py",
             "glb": "res://assets/characters/rootback_boar.glb", "clips": clips_all, "tris": tris, "bones": bones}
    with open(path) as fh:
        data = json.load(fh)
    before = json.dumps({k: v for k, v in data.get("animations", {}).items() if not k.startswith("boar_")},
                        sort_keys=True)
    data.setdefault("animations", {}).update(mine)
    data.setdefault("models", {})[NAME] = model
    with open(path, "w") as fh:
        json.dump(data, fh, indent=1)
    with open(path) as fh:
        chk = json.load(fh)
    after = json.dumps({k: v for k, v in chk["animations"].items() if not k.startswith("boar_")}, sort_keys=True)
    ok = before == after and all(chk["animations"].get(k) == v for k, v in mine.items()) and NAME in chk["models"]
    print(f"[{NAME}] meta merged {sorted(mine)} + models.{NAME} -> {path} (verified: {ok})")


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
    print(f"[rootback_boar] -> {OUT_GLB} ({os.path.getsize(OUT_GLB) / 1e6:.1f} MB)")
    bad, got = GX.check_lengths(OUT_GLB, {n: c.frames / FPS for n, (c, a) in acts.items()})
    print(f"[rootback_boar] {len(got)} animations in the GLB; length mismatches: {bad}")


def preview(arm, acts, out_dir, clip_names, frames, views, res=300, tag="", dist=3.8, tz=0.5):
    import bpy
    import preview_enemy as PE
    PE.material_colors()
    cam = PE.setup(res)
    rows = []
    tmp = os.path.join(out_dir, "_boar")
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
    out = os.path.join(out_dir, f"rootback_boar_{tag or '_'.join(clip_names)[:60]}.png")
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
    print(f"[rootback_boar] mesh {M.tri_count(mesh)} tris, {len(acts)} clips")
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        preview(arm, acts, a.preview, names, [float(x) for x in a.frames.split(",")],
                [float(x) for x in a.views.split(",")], a.res, a.tag, a.dist, a.tz)
    if not a.no_export:
        write_meta(acts, OUT_META, M.tri_count(mesh), len(arm.data.bones))
        export(arm, mesh, acts)


if __name__ == "__main__":
    main()
