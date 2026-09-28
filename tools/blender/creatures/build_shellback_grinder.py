"""Shellback Grinder (bh-013, Builder C): a heavy armadillo / pangolin beast ~2.2 m long and ~1.2 m tall. Rows of
overlapping pointed plates (iron-grey, some rust-brown) armour its back and tail, it has a pale soft underbelly, a
small plated head with a toothy snout and a snout horn, small glowing amber eyes, and short legs with big digging
claws. It rolls up into a tight armoured ball: a flexible spine chain (hips, spine1, spine2, chest, neck, head,
tail.1-4) curls ~360 degrees, the legs tuck in.

Rig / planar leg IK / gait machinery: kit_c13.Quadruped (ported from build_rootback_boar.py / build_wolf.py, which are
not modified).

  "<blender>" -b --factory-startup --python build_shellback_grinder.py -- [--no-export] [--evidence rest|clips|both]
Export: game/assets/characters/shellback_grinder.glb (+ .import); merges ONLY animations.shell_* and
models.shellback_grinder into creature_meta.json. Faces -Y (= +Z in Godot), origin on the ground under the body.
shell_roll is the curled ball spinning forward in place about its side axis (loop, 0.6 s per turn); shell_curl
ends and shell_uncurl starts in that ball pose; shell_flipped loops on its back, belly up.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_c13 as K  # noqa: E402
from kit_c13 import Rx, Ry, Rz, cyc, damp, normalize  # noqa: E402
import numpy as np  # noqa: E402

NAME = "shellback_grinder"
PREFIX = "shell_"
FPS = K.FPS
PALETTE = {
    "BH_Steel": ((0.33, 0.34, 0.36), 0.35, 0.55, None, 0.0, 1.0),          # iron-grey plates
    "BH_Rust": ((0.37, 0.17, 0.07), 0.25, 0.8, None, 0.0, 1.0),            # rust-brown plates / plate edges
    "BH_Skin": ((0.62, 0.52, 0.42), 0.0, 0.65, None, 0.0, 1.0),            # pale soft underbelly, face, legs
    "BH_Flesh": ((0.42, 0.22, 0.2), 0.0, 0.5, None, 0.0, 1.0),             # gums, inner mouth
    "BH_Bone": ((0.8, 0.74, 0.58), 0.0, 0.5, None, 0.0, 1.0),              # teeth, snout horn, claws
    "BH_Horn": ((0.16, 0.14, 0.13), 0.0, 0.55, None, 0.0, 1.0),            # dark claws tips, nose
    "BH_Shadow": ((0.03, 0.02, 0.02), 0.0, 0.6, None, 0.0, 1.0),           # mouth
    "BH_Emissive": ((1.0, 0.55, 0.12), 0.0, 0.3, (1.0, 0.5, 0.1), 5.0, 1.0),  # small amber eyes
}

BONES = {
    "root": ((0, 0, 0), (0, 0, 0.25), None),
    "hips": ((0, 0.55, 0.66), (0, 0.3, 0.74), "root"),
    "spine1": ((0, 0.3, 0.74), (0, 0.05, 0.78), "hips"),
    "spine2": ((0, 0.05, 0.78), (0, -0.2, 0.78), "spine1"),
    "chest": ((0, -0.2, 0.78), (0, -0.45, 0.73), "spine2"),
    "neck": ((0, -0.45, 0.72), (0, -0.66, 0.62), "chest"),
    "head": ((0, -0.66, 0.62), (0, -1.0, 0.45), "neck"),
    "jaw": ((0, -0.74, 0.5), (0, -0.98, 0.4), "head"),
    "tail.1": ((0, 0.6, 0.62), (0, 0.78, 0.5), "hips"),
    "tail.2": ((0, 0.78, 0.5), (0, 0.93, 0.38), "tail.1"),
    "tail.3": ((0, 0.93, 0.38), (0, 1.06, 0.26), "tail.2"),
    "tail.4": ((0, 1.06, 0.26), (0, 1.17, 0.16), "tail.3"),
}
for _s, _x in (("L", 1.0), ("R", -1.0)):
    BONES.update({
        f"scap.{_s}": ((0.2 * _x, -0.3, 0.72), (0.24 * _x, -0.34, 0.5), "chest"),
        f"upperarm.{_s}": ((0.24 * _x, -0.34, 0.5), (0.24 * _x, -0.27, 0.3), f"scap.{_s}"),
        f"forearm.{_s}": ((0.24 * _x, -0.27, 0.3), (0.24 * _x, -0.32, 0.12), f"upperarm.{_s}"),
        f"fpaw.{_s}": ((0.24 * _x, -0.32, 0.12), (0.24 * _x, -0.36, 0.045), f"forearm.{_s}"),
        f"ftoe.{_s}": ((0.24 * _x, -0.36, 0.045), (0.24 * _x, -0.52, 0.02), f"fpaw.{_s}"),
        f"thigh.{_s}": ((0.22 * _x, 0.46, 0.6), (0.24 * _x, 0.34, 0.35), "hips"),
        f"shin.{_s}": ((0.24 * _x, 0.34, 0.35), (0.24 * _x, 0.48, 0.14), f"thigh.{_s}"),
        f"hpaw.{_s}": ((0.24 * _x, 0.48, 0.14), (0.24 * _x, 0.45, 0.045), f"shin.{_s}"),
        f"htoe.{_s}": ((0.24 * _x, 0.45, 0.045), (0.24 * _x, 0.32, 0.02), f"hpaw.{_s}"),
    })
RIG = K.Rig(BONES)
H, T = RIG.H, RIG.T
LEGS = {
    "LF": ("scap.L", "upperarm.L", "forearm.L", "fpaw.L", "ftoe.L"),
    "RF": ("scap.R", "upperarm.R", "forearm.R", "fpaw.R", "ftoe.R"),
    "LH": ("hips", "thigh.L", "shin.L", "hpaw.L", "htoe.L"),
    "RH": ("hips", "thigh.R", "shin.R", "hpaw.R", "htoe.R"),
}
SCAP = {"LF": "scap.L", "RF": "scap.R"}
SPINE = ("hips", "spine1", "spine2", "chest", "neck", "head")
TAILB = [f"tail.{i}" for i in range(1, 5)]


def extra(c, Rd, S, L):
    Rd["jaw"] = Rx(c.get("jaw", 0.0))
    for i in range(1, 5):
        Rd[f"tail.{i}"] = Rz(c.get("tail.yaw", 0.0) * (0.6 + 0.2 * i) + c.get("tail.wag", 0.0) * 0.25 * i) @ \
            Rx(c.get("tail.lift", 0.0) * (1.0 if i == 1 else 0.35) - c.get("tail.curl", 0.0))
    # 'ball' (0..1): the whole spine curls belly-in; blended on top of the other spine channels
    b = c.get("ball", 0.0)
    if b:
        for bn, a in BALL_SPINE.items():
            Rd[bn] = Rd.get(bn, np.eye(3)) @ Rx(a * b)
        for i in range(1, 5):
            Rd[f"tail.{i}"] = Rd[f"tail.{i}"] @ Rx(-BALL_TAIL * b)
        Rd["jaw"] = Rd["jaw"] @ Rx(-6 * b)


# nose-down / belly-in bend (degrees about +X in armature axes) per spine bone at ball = 1
BALL_SPINE = {"spine1": 34.0, "spine2": 40.0, "chest": 44.0, "neck": 48.0, "head": 52.0}
BALL_TAIL = 44.0
PIVOT = np.array([0.0, 0.05, 0.72])
QD = K.Quadruped(RIG, LEGS, pivot=PIVOT, spine=SPINE, extra=extra, scap_bones=tuple(SCAP.values()))
evaluate = QD.evaluate


# ------------------------------------------------------------------------------------------------ ground contact
# Filled by build_all() from a numpy skin of the finished mesh (see ground_z): body.up offsets that keep the ball /
# the flipped body resting on the ground. Defaults are only used by --design.
GROUND = {"ball": 0.08, "roll": [0.0] * 18, "flip": -0.3, "death": -0.3, "death_back": -0.3}
BALL_Y = 0.05          # where the ball centre sits (y), close to the standing body pivot


def ball_center():
    """Centre of the curled spine chain (root identity)."""
    Rd, S, L, X = evaluate({"ball": 1.0})
    chain = ["tail.4", "tail.3", "tail.2", "tail.1", "hips", "spine1", "spine2", "chest", "neck", "head"]
    P = np.array([X[b].apply(H[b]) for b in chain] + [X["head"].apply(T["head"]), X["tail.4"].apply(T["tail.4"])])
    return P.mean(0), P


BALL_CEN = ball_center()[0]     # replaced in fit_ground() by the centre of the skinned ball's bounding box


def ball_pose(b=1.0, up=None):
    """Channels of the curled ball (b = 0..1): spine curl, legs tucked into the belly, the ball moved over the origin
    and lifted onto the ground; the pivot sits at the ball centre so body.pitch rolls it about its own centre."""
    d = {"ball": b, "body.fwd": (BALL_CEN[1] - BALL_Y) * b, "body.up": (GROUND["ball"] if up is None else up) * b,
         "piv.y": BALL_CEN[1] - PIVOT[1], "piv.z": BALL_CEN[2] - PIVOT[2], "neck.pitch": -6 * b, "head.pitch": -8 * b}
    for k, (lf, lup) in {"LF": (-0.1, 0.34), "RF": (-0.1, 0.34), "LH": (0.16, 0.32), "RH": (0.16, 0.32)}.items():
        d[k + ".loc"] = b
        d[k + ".lf"] = lf * b
        d[k + ".lup"] = lup * b
    return d


def flip_pose(up=None):
    """On its back, belly up: rolled 180 degrees about the long axis, legs up in the air (leg targets in body space)."""
    d = {"body.roll": 180.0, "body.up": GROUND["flip"] if up is None else up, "neck.pitch": 10, "head.pitch": 8,
         "tail.lift": 14, "jaw": 12, "ball": 0.12}
    for k in ("LF", "RF", "LH", "RH"):
        d[k + ".loc"] = 1.0
        d[k + ".lup"] = 0.08
    return d


def roll_channels(f, n):
    return {"body.pitch": -360.0 * f / n}


# ------------------------------------------------------------------------------------------------ clips
def clips():
    C = []
    P = 90
    c = K.Clip("idle", P, loop=True)
    c.key(0)
    c.layer(lambda f, cl: {"chest.pitch": 1.0 * cyc(f, P, 2), "spine1.pitch": 0.8 * cyc(f, P, 2, 0.1),
                           "body.up": 0.006 * cyc(f, P, 2), "neck.pitch": -4 + 3 * cyc(f, P, 1, 0.1),
                           "head.yaw": 6 * cyc(f, P, 1, 0.3), "head.pitch": -4 + 3 * cyc(f, P, 3),
                           "tail.yaw": 5 * cyc(f, P, 1), "jaw": 2 + 2 * cyc(f, P, 3, 0.4)})
    C.append(c)
    c = K.Clip("idle_look", 75)
    c.key(0).key(15, neck_yaw=20, head_yaw=16, neck_pitch=10, head_pitch=4, tail_yaw=-8, body_up=0.02)
    c.key(30, neck_yaw=22, head_yaw=18, neck_pitch=12, head_pitch=6, tail_yaw=-10, jaw=8, body_up=0.02)
    c.key(46, neck_yaw=-20, head_yaw=-16, neck_pitch=8, head_roll=-5, tail_yaw=10, jaw=0, body_up=0.01)
    c.key(60, neck_yaw=-16, head_yaw=-12, neck_pitch=4, tail_yaw=8)
    c.key(75, neck_yaw=0, head_yaw=0, neck_pitch=0, head_pitch=0, head_roll=0, tail_yaw=0, jaw=0, body_up=0)
    C.append(c)
    WALK_P, WALK_V = 28, 0.6
    c = K.Clip("walk", WALK_P, loop=True, ground_speed=WALK_V)
    c.key(0)
    c.layer(K.gait_layer(WALK_P, 0.65, WALK_V, {"LH": 0.0, "LF": 0.25, "RH": 0.5, "RF": 0.75}, 0.09, 0.08, 30, 20, 10,
                         scap_gain=-50.0, scap=SCAP))
    c.layer(lambda f, cl: {"body.up": -0.03 + 0.008 * cyc(f, WALK_P, 2), "body.roll": 3.0 * cyc(f, WALK_P, 1, 0.1),
                           "body.yaw": 2.0 * cyc(f, WALK_P, 1, 0.35), "neck.pitch": -5 + 2 * cyc(f, WALK_P, 2, 0.2),
                           "head.yaw": -2 * cyc(f, WALK_P, 1, 0.35), "tail.yaw": -6 * cyc(f, WALK_P, 1, 0.45)})
    C.append(c)
    RUN_P, RUN_V = 12, 2.4
    for nm in ("run", "run_combat"):
        low = nm == "run_combat"
        c = K.Clip(nm, RUN_P, loop=True, ground_speed=RUN_V)
        c.key(0)
        c.layer(K.gait_layer(RUN_P, 0.42, RUN_V, {"LF": 0.0, "RH": 0.04, "RF": 0.5, "LH": 0.54}, 0.13, 0.12, 50, 30,
                             12, scap_gain=-50.0, scap=SCAP))
        c.layer(lambda f, cl, low=low: {
            "body.up": (-0.09 if low else -0.06) + 0.02 * cyc(f, RUN_P, 2, 0.1), "body.pitch": 1.5 * cyc(f, RUN_P, 2),
            "body.roll": 2.5 * cyc(f, RUN_P, 1, 0.1), "neck.pitch": (-14 if low else -8) + 3 * cyc(f, RUN_P, 2, 0.6),
            "head.pitch": 2 if low else 0, "tail.lift": 8, "tail.yaw": 5 * cyc(f, RUN_P, 1, 0.3),
            "jaw": 10 if low else 3, "ball": 0.12 if low else 0.05})
        C.append(c)
    # ---- reactions
    c = K.Clip("hit_light", 12)
    c.key(0).key(3, body_fwd=-0.05, body_pitch=3, neck_pitch=10, head_pitch=6, neck_yaw=8, jaw=14, ball=0.08)
    c.key(12, body_fwd=0, body_pitch=0, neck_pitch=0, head_pitch=0, neck_yaw=0, jaw=0, ball=0)
    C.append(c)
    c = K.Clip("hit_heavy", 18)
    c.key(0).key(4, body_fwd=-0.12, body_up=-0.04, body_pitch=6, body_roll=5, neck_pitch=16, head_pitch=10,
                 neck_yaw=14, jaw=22, tail_yaw=12, LF_f=0.05, RF_f=0.04, ball=0.18)
    c.key(9, body_fwd=-0.1, body_up=-0.03, body_pitch=4, body_roll=3, neck_pitch=8, head_pitch=4, neck_yaw=8,
          jaw=8, tail_yaw=8, LF_f=0.07, RF_f=0.05, ball=0.1)
    c.key(18, body_fwd=0, body_up=0, body_pitch=0, body_roll=0, neck_pitch=0, head_pitch=0, neck_yaw=0, jaw=0,
          tail_yaw=0, LF_f=0, RF_f=0, ball=0)
    C.append(c)
    c = K.Clip("stagger_small", 24)
    c.key(0).key(5, body_fwd=-0.08, body_side=-0.05, body_roll=-7, body_pitch=4, neck_pitch=10, neck_yaw=-16,
                 tail_yaw=14)
    c.key(9, LF_up=0.07, LF_f=-0.03, body_fwd=-0.1, body_side=-0.06, body_roll=-8, neck_pitch=6, neck_yaw=-12)
    c.key(14, LF_up=0.0, LF_f=-0.08, RH_f=-0.06, body_fwd=-0.08, body_roll=-3, body_side=-0.03, neck_pitch=3)
    c.key(24, LF_f=0, RH_f=0, body_fwd=0, body_side=0, body_roll=0, body_pitch=0, neck_pitch=0, neck_yaw=0,
          tail_yaw=0)
    C.append(c)
    c = K.Clip("knockback", 27)
    c.key(0).key(4, body_fwd=-0.2, body_up=0.03, body_pitch=9, neck_pitch=14, jaw=20, tail_lift=-6, ball=0.2,
                 LF_up=0.1, RF_up=0.08, LF_f=0.06, RF_f=0.08, LH_f=0.1, RH_f=0.08)
    c.key(11, body_fwd=-0.3, body_up=-0.05, body_pitch=3, neck_pitch=5, jaw=8, ball=0.1, LF_up=0.0, RF_up=0.0,
          LF_f=0.1, RF_f=0.06, LH_f=0.14, RH_f=0.12)
    c.key(18, body_fwd=-0.18, body_up=-0.03, body_pitch=1, neck_pitch=2, jaw=3, ball=0.04, LF_f=0.05, RF_f=0.02,
          LH_f=0.08, RH_f=0.08)
    c.key(27, body_fwd=0, body_up=0, body_pitch=0, neck_pitch=0, jaw=0, tail_lift=0, ball=0, LF_f=0, RF_f=0,
          LH_f=0, RH_f=0)
    C.append(c)
    C.append(death_clip("death"))
    C.append(death_back_clip("death_back"))
    # ---- alert: rears up on its hind legs a little (pangolin-like), sniffs, snout horn up, then drops back down
    c = K.Clip("alert", 30)
    c.key(0).key(8, body_pitch=16, body_up=0.03, piv_y=0.35, neck_pitch=12, head_pitch=10, jaw=10, tail_lift=-8,
                 LF_up=0.12, RF_up=0.1, LF_f=0.02, RF_f=0.02)
    c.key(15, body_pitch=17, body_up=0.03, piv_y=0.35, neck_pitch=8, head_pitch=14, head_yaw=8, jaw=18,
          tail_lift=-8, LF_up=0.12, RF_up=0.11)
    c.key(22, body_pitch=6, body_up=0.0, piv_y=0.35, neck_pitch=2, head_pitch=4, head_yaw=-4, jaw=6, tail_lift=-3,
          LF_up=0.03, RF_up=0.0, LF_f=0.0, RF_f=0.0)
    c.key(30, body_pitch=0, body_up=0.0, piv_y=0.0, neck_pitch=0, head_pitch=0, head_yaw=0, jaw=0, tail_lift=0,
          LF_up=0, RF_up=0)
    C.append(c)
    # ---- shell_bite (0.9 s): head draws back, lunges forward-down, toothy snout snaps shut ~0.45 s
    c = K.Clip("shell_bite", 27, hits=[[13 / FPS, 16 / FPS]])
    c.key(0).key(8, body_fwd=-0.08, body_pitch=3, neck_pitch=14, head_pitch=8, jaw=32, LH_f=0.03, RH_f=0.03,
                 tail_lift=4)
    c.key(12, body_fwd=0.16, body_pitch=-5, neck_pitch=-16, head_pitch=-10, jaw=38, LF_f=0.1, RF_f=0.08)
    c.key(14, body_fwd=0.2, body_pitch=-6, neck_pitch=-20, head_pitch=-12, jaw=2, LF_f=0.12, RF_f=0.09)
    c.key(18, body_fwd=0.17, body_pitch=-4, neck_pitch=-12, head_pitch=-5, jaw=5, LF_f=0.1, RF_f=0.07)
    c.key(27, body_fwd=0, body_pitch=0, neck_pitch=0, head_pitch=0, jaw=0, LF_f=0, RF_f=0, LH_f=0, RH_f=0,
          tail_lift=0)
    C.append(c)
    # ---- shell_swipe (0.9 s): rears the forequarters, raises the right fore-claw high, rakes it down and across
    #      in front ~0.5 s
    c = K.Clip("shell_swipe", 27, hits=[[14 / FPS, 17 / FPS]])
    c.key(0).key(9, body_pitch=12, body_up=0.02, body_yaw=10, body_fwd=-0.04, piv_y=0.3, neck_pitch=8,
                 head_yaw=-8, jaw=14, RF_up=0.34, RF_f=0.06, RF_phi=-40, LF_f=0.03, tail_yaw=-10)
    c.key(12, body_pitch=13, body_up=0.02, body_yaw=12, piv_y=0.3, neck_pitch=6, head_yaw=-10, jaw=18,
          RF_up=0.38, RF_f=0.1, RF_phi=-50)
    c.key(15, body_pitch=2, body_up=-0.03, body_yaw=-12, body_fwd=0.12, piv_y=0.3, neck_pitch=-8, head_yaw=10,
          jaw=24, RF_up=0.06, RF_f=0.32, RF_phi=30, LF_f=0.08, tail_yaw=12)
    c.key(18, body_pitch=-1, body_up=-0.04, body_yaw=-16, body_fwd=0.14, piv_y=0.3, neck_pitch=-10, head_yaw=12,
          jaw=16, RF_up=0.02, RF_f=0.28, RF_phi=20, LF_f=0.1, tail_yaw=14)
    c.key(27, body_pitch=0, body_up=0, body_yaw=0, body_fwd=0, piv_y=0, neck_pitch=0, head_yaw=0, jaw=0, RF_up=0,
          RF_f=0, RF_phi=0, LF_f=0, tail_yaw=0)
    C.append(c)
    # ---- shell_curl (0.6 s): tucks the head, humps the back and rolls up into the ball (ends in the roll's pose)
    n = 18
    c = K.Clip("shell_curl", n)
    c.key(0).keyd(5, dict(ball_pose(0.3), **{"body.fwd": 0.0, "body.up": -0.03, "neck.pitch": -18, "head.pitch": -14}))
    c.keyd(12, ball_pose(0.85)).keyd(n, ball_pose(1.0))
    C.append(c)
    # ---- shell_roll (0.6 s LOOP): the ball spins forward in place about its side axis, one turn per cycle
    c = K.Clip("shell_roll", n, loop=True)
    c.keyd(0, ball_pose(1.0)).keyd(n, ball_pose(1.0))
    c.layer(lambda f, cl: dict(roll_channels(f, n), **{"body.up": GROUND["roll"][int(round(f)) % n] - GROUND["ball"]}))
    C.append(c)
    # ---- shell_uncurl (0.6 s): the ball opens, legs come down, a small settle
    c = K.Clip("shell_uncurl", n)
    c.keyd(0, ball_pose(1.0)).keyd(6, ball_pose(0.7))
    c.keyd(12, dict(ball_pose(0.0), **{"body.up": 0.03, "neck.pitch": 6, "head.pitch": 4, "tail.lift": 4}))
    c.keyd(n, dict(ball_pose(0.0), **{"body.up": 0.0}))
    C.append(c)
    # ---- shell_flipped (1.0 s LOOP): on its back, belly up, rocking, legs flailing, head and tail thrashing
    F = 30
    c = K.Clip("shell_flipped", F, loop=True)
    c.keyd(0, flip_pose()).keyd(F, flip_pose())

    def flail(f, cl):
        d = {"body.roll": 7 * cyc(f, F, 1), "body.yaw": 3 * cyc(f, F, 1, 0.25), "neck.yaw": 14 * cyc(f, F, 1, 0.1),
             "head.pitch": 8 * cyc(f, F, 2), "jaw": 10 * cyc(f, F, 2, 0.2), "tail.yaw": 18 * cyc(f, F, 1, 0.4),
             "tail.lift": 6 * cyc(f, F, 2, 0.1)}
        for k, ph in (("LF", 0.0), ("RF", 0.5), ("LH", 0.3), ("RH", 0.8)):
            d[k + ".lf"] = 0.1 * cyc(f, F, 2, ph)
            d[k + ".lup"] = 0.1 + 0.08 * cyc(f, F, 2, ph + 0.25)
        return d
    c.layer(flail)
    C.append(c)
    return C


def death_clip(name):
    """Legs buckle, it slumps onto its left side and half curls up."""
    c = K.Clip(name, 45)
    c.key(0)
    c.key(8, body_up=-0.08, body_pitch=-6, neck_pitch=-10, head_pitch=-8, jaw=24, LF_f=0.06, RF_f=0.06, LF_phi=20,
          RF_phi=20, ball=0.1)
    k2 = dict(body_up=-0.22, body_roll=30, body_side=0.04, neck_pitch=-6, neck_yaw=10, jaw=30, tail_yaw=-14, ball=0.2)
    for k in ("LF", "RF", "LH", "RH"):
        k2.update({k + "_loc": 0.6, k + "_lf": 0.08, k + "_lup": 0.16})
    c.key(18, **k2)
    k3 = dict(body_up=GROUND["death"], body_roll=84, body_side=0.12, neck_pitch=-12, neck_yaw=6, head_roll=-10,
              jaw=18, tail_yaw=-10, ball=0.4)
    for k, (lf, lup) in {"LF": (0.18, 0.12), "RF": (0.06, 0.2), "LH": (-0.08, 0.16), "RH": (0.04, 0.22)}.items():
        k3.update({k + "_loc": 1.0, k + "_lf": lf, k + "_lup": lup})
    c.key(30, **k3)
    c.key(45, **dict(k3, neck_pitch=-16, jaw=12))
    return c


def death_back_clip(name):
    """Rears back, topples over sideways onto its back and ends belly-up with the legs limp in the air."""
    c = K.Clip(name, 45)
    c.key(0)
    c.key(8, body_pitch=10, body_up=0.02, piv_y=0.3, neck_pitch=16, head_pitch=10, jaw=26, LF_up=0.1, RF_up=0.1)
    k2 = dict(body_pitch=4, piv_y=0.3, body_roll=-80, body_up=-0.12, body_side=-0.12, neck_pitch=10, jaw=30, ball=0.1)
    for k in ("LF", "RF", "LH", "RH"):
        k2.update({k + "_loc": 0.8, k + "_lup": 0.1})
    c.key(20, **k2)
    k3 = dict(body_pitch=0, piv_y=0.0, body_roll=-176, body_up=GROUND["death_back"], body_side=-0.25, neck_pitch=14,
              neck_yaw=-10, head_pitch=12, jaw=20, tail_lift=12, tail_yaw=10, ball=0.1)
    for k, (lf, lup) in {"LF": (0.06, 0.1), "RF": (-0.04, 0.14), "LH": (0.1, 0.12), "RH": (0.02, 0.08)}.items():
        k3.update({k + "_loc": 1.0, k + "_lf": lf, k + "_lup": lup})
    c.key(32, **k3)
    c.key(45, **dict(k3, neck_pitch=18, jaw=14, tail_lift=8))
    return c


# ------------------------------------------------------------------------------------------------ mesh
# armour path from the shoulders down the back and tail: (y, z, rx, rz); the body is lofted along it too
PATH = [(-0.6, 0.68, 0.23, 0.2), (-0.47, 0.72, 0.33, 0.28), (-0.25, 0.745, 0.39, 0.34), (0.0, 0.755, 0.42, 0.37),
        (0.25, 0.74, 0.4, 0.35), (0.45, 0.71, 0.34, 0.3), (0.6, 0.65, 0.25, 0.22), (0.75, 0.53, 0.17, 0.16),
        (0.92, 0.39, 0.13, 0.12), (1.06, 0.27, 0.1, 0.09), (1.17, 0.18, 0.07, 0.065), (1.27, 0.12, 0.04, 0.035)]
BELLY_F = [0.8, 0.72, 0.7, 0.7, 0.7, 0.74, 0.85, 0.95, 1.0, 1.0, 1.0, 1.0]
BODY_B = ["hips", "spine1", "spine2", "chest", "neck", "tail.1", "tail.2", "tail.3", "tail.4"]
XA = np.array([1.0, 0.0, 0.0])


class Path:
    def __init__(self, pts):
        P = np.array([(0.0, y, z) for (y, z, rx, rz) in pts])
        self.P = P
        self.RX = np.array([p[2] for p in pts])
        self.RZ = np.array([p[3] for p in pts])
        self.S = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        self.len = self.S[-1]

    def at(self, s):
        s = min(max(s, 0.0), self.len)
        c = np.array([np.interp(s, self.S, self.P[:, k]) for k in range(3)])
        a = np.array([np.interp(max(s - 0.02, 0), self.S, self.P[:, k]) for k in range(3)])
        b = np.array([np.interp(min(s + 0.02, self.len), self.S, self.P[:, k]) for k in range(3)])
        t = normalize(b - a)
        u = normalize(np.cross(XA, t))
        if u[2] < 0:
            u = -u
        return c, u, float(np.interp(s, self.S, self.RX)), float(np.interp(s, self.S, self.RZ))

    def surf(self, s, a, off=0.0):
        """a: angle from the top (0) toward +X (degrees)."""
        c, u, rx, rz = self.at(s)
        r = math.radians(a)
        return c + (rx + off) * math.sin(r) * XA + (rz + off) * math.cos(r) * u


def build_mesh(mats):
    import bh_mesh as M
    parts = []
    rng = np.random.default_rng(1307)

    def add(p, bone=None, bones=None, power=6.0, bias=None, top=3, closed=True):
        if closed:
            M.recalc_normals(p)
        if bone:
            p.W = [{bone: 1.0}] * len(p.V)
        else:
            p.W = K.dist_weights(RIG, p.V, bones, power=power, bias=bias, top=top)
        parts.append(p)
        return p

    def ring(c, u, rx, rt, rb, n=24):
        pts = []
        for i in range(n):
            t = 2 * math.pi * i / n
            s, co = math.sin(t), math.cos(t)
            pts.append(c + rx * co * XA + (rt if s > 0 else rb) * s * u)
        return np.array(pts)

    def band(path, s0, L, amax, n, mat, bones=None, bone=None, lift=0.05, tip=0.22, thick=0.022):
        """One row of overlapping pointed plates: a curved shingle from angle -amax..amax around the path, its rear
        edge lifted and cut into points (each point = one scale tip)."""
        rows = []
        for j, v in enumerate((0.0, 0.5, 1.0)):
            row = []
            for i in range(n):
                a = -amax + 2 * amax * i / (n - 1)
                s = s0 + L * v
                if j == 2:
                    s += L * (tip if i % 2 == 0 else -0.08)
                off = 0.012 + lift * v ** 1.5
                row.append(path.surf(s, a, off))
            rows.append(row)
        V = np.array([p for r in rows for p in r])
        F = []
        for j in range(2):
            for i in range(n - 1):
                F.append((j * n + i, j * n + i + 1, (j + 1) * n + i + 1, (j + 1) * n + i))
        p = M.Part(V, F, mat, name="plate")
        M.solidify(p, thickness=thick, offset=-1.0)
        return add(p, bone=bone, bones=bones, power=6, top=2)

    # ---- body + tail: one loft along the armour path, pale soft belly
    body_path = Path(PATH)
    rings = []
    for i, (y, z, rx, rz) in enumerate(PATH):
        s = body_path.S[i]
        c, u, _, _ = body_path.at(s)
        rings.append(ring(c, u, rx, rz, rz * BELLY_F[i]))
    V, F = M.loft(rings, cap0=True, cap1=True)
    body = M.Part(V, F, "BH_Skin", name="body")
    body.V += rng.normal(size=body.V.shape) * 0.003
    add(body, bones=BODY_B + ["scap.L", "scap.R", "thigh.L", "thigh.R"],
        bias={"scap.L": 1.5, "scap.R": 1.5, "thigh.L": 1.5, "thigh.R": 1.5, "neck": 1.3})
    # ---- plate rows: shoulders to tail tip, alternating iron-grey / rust
    s = 0.0
    k = 0
    while s < body_path.len - 0.07:
        c, u, rx, rz = body_path.at(s)
        L = 0.1 + 0.5 * rz
        tail = s > body_path.S[6] - 0.02
        amax = 128 if tail else 104
        n = 13 if rx < 0.12 else (17 if rx < 0.3 else 23)
        mat = "BH_Rust" if k % 3 == 2 else "BH_Steel"
        band(body_path, s, L, amax, n, mat, bones=BODY_B, lift=0.03 + 0.08 * rz, thick=0.018 + 0.02 * rz)
        s += L * 0.58
        k += 1
    # ---- neck + small head: pale skin, a hood of plates, toothy snout, snout horn, small amber eyes
    NECK = [(-0.5, 0.71, 0.25, 0.22, 0.19), (-0.62, 0.66, 0.2, 0.17, 0.15), (-0.7, 0.62, 0.17, 0.15, 0.13)]
    V, F = M.loft([ring(np.array([0, y, z]), np.array([0, 0, 1.0]), rx, rt, rb, n=18) for (y, z, rx, rt, rb) in NECK])
    add(M.Part(V, F, "BH_Skin", name="neck"), bones=["chest", "neck", "head"], bias={"head": 1.3})
    neck_path = Path([(-0.5, 0.71, 0.25, 0.22), (-0.62, 0.66, 0.2, 0.17), (-0.72, 0.62, 0.17, 0.15)])
    band(neck_path, 0.0, 0.13, 100, 15, "BH_Steel", bones=["chest", "neck", "head"], lift=0.03)
    band(neck_path, 0.08, 0.13, 96, 15, "BH_Rust", bones=["neck", "head"], lift=0.03)
    SKULL = [(-0.64, 0.63, 0.16, 0.14, 0.12), (-0.76, 0.6, 0.145, 0.12, 0.1), (-0.87, 0.555, 0.11, 0.09, 0.07),
             (-0.96, 0.515, 0.075, 0.065, 0.05), (-1.03, 0.485, 0.045, 0.04, 0.035)]
    up_h = normalize(np.array([0, -0.3, 1.0]))
    V, F = M.loft([ring(np.array([0, y, z]), up_h, rx, rt, rb, n=18) for (y, z, rx, rt, rb) in SKULL])
    add(M.Part(V, F, "BH_Skin", name="skull"), bone="head")
    head_path = Path([(y, z, rx, rt) for (y, z, rx, rt, rb) in SKULL])
    band(head_path, 0.0, 0.12, 80, 11, "BH_Steel", bone="head", lift=0.02, thick=0.016)
    band(head_path, 0.09, 0.11, 74, 11, "BH_Steel", bone="head", lift=0.02, thick=0.016)
    band(head_path, 0.17, 0.1, 66, 9, "BH_Rust", bone="head", lift=0.015, thick=0.014)
    # snout horn (bone), curved up-forward, plus a small second nub behind it
    base = np.array([0, -0.9, 0.62])
    pts = [base, base + np.array([0, -0.05, 0.08]), base + np.array([0, -0.06, 0.16]), base + np.array([0, -0.04, 0.22])]
    V, F = M.tube(pts, [(0.045, 0.05), (0.032, 0.035), (0.018, 0.02), (0.003, 0.003)], n=8, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Bone", name="horn"), bone="head")
    V, F = M.lathe([(0.03, 0.0), (0.015, 0.04), (0.0, 0.06)], 7)
    add(M.Part(V, F, "BH_Bone", name="nub").rot(Rx(-20)).move((0, -0.8, 0.67)), bone="head")
    # nose pad
    V, F = M.sphere(0.04, 8, 4, center=(0, -1.045, 0.485), scale=(1.1, 0.7, 0.85))
    add(M.Part(V, F, "BH_Horn", name="nose"), bone="head")
    # lower jaw, mouth, gums and teeth
    JAW = [(-0.74, 0.49, 0.12, 0.03, 0.05), (-0.86, 0.455, 0.1, 0.025, 0.04), (-0.97, 0.425, 0.065, 0.02, 0.03),
           (-1.02, 0.415, 0.04, 0.015, 0.02)]
    V, F = M.loft([ring(np.array([0, y, z]), np.array([0, 0, 1.0]), rx, rt, rb, n=14) for (y, z, rx, rt, rb) in JAW])
    add(M.Part(V, F, "BH_Skin", name="jaw"), bone="jaw")
    V, F = M.loft([ring(np.array([0, y, z + 0.025]), np.array([0, 0, 1.0]), rx * 0.85, 0.012, 0.012, n=14)
                   for (y, z, rx, rt, rb) in JAW])
    add(M.Part(V, F, "BH_Shadow", name="mouth"), bone="jaw")
    for sx in (1, -1):
        V, F = M.tube([(sx * 0.1, -0.76, 0.52), (sx * 0.08, -0.9, 0.49), (sx * 0.045, -1.01, 0.455)],
                      [(0.018, 0.012), (0.016, 0.011), (0.012, 0.009)], n=6, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Flesh", name="gum"), bone="head")
        for i in range(6):
            y = -0.8 - 0.038 * i
            rx = float(np.interp(-y, [0.74, 0.86, 0.97, 1.02], [0.12, 0.1, 0.065, 0.04])) * 0.85
            V, F = M.lathe([(0.011, 0.0), (0.005, 0.028), (0.0, 0.042)], 6)
            add(M.Part(V + np.array([sx * rx, y, 0.505 - 0.012 * i + 0.012]), F, "BH_Bone", name="tooth"), bone="jaw")
            V, F = M.lathe([(0.012, 0.0), (0.006, 0.03), (0.0, 0.05)], 6)
            p = M.Part(V, F, "BH_Bone", name="utooth").rot(Rx(180)).move((sx * rx * 1.03, y + 0.015,
                                                                           0.535 - 0.013 * i))
            add(p, bone="head")
        # small glowing amber eyes under a plate brow
        ec = np.array([sx * 0.112, -0.775, 0.655])
        V, F = M.sphere(0.03, 10, 5, center=ec)
        add(M.Part(V, F, "BH_Emissive", name="eye"), bone="head")
        V, F = M.sphere(0.05, 8, 4, center=ec + np.array([sx * 0.0, 0.01, 0.03]), scale=(1.1, 1.2, 0.4))
        add(M.Part(V, F, "BH_Steel", name="brow"), bone="head")
        # small ears
        V, F = M.sphere(0.04, 8, 4, center=(sx * 0.13, -0.68, 0.7), scale=(0.5, 0.9, 1.0))
        add(M.Part(V, F, "BH_Flesh", name="ear"), bone="head")

    # ---- short thick legs, a plate on each upper leg, broad paws with big digging claws (front)
    def leg_tube(chain, radii):
        pts = [H[chain[0]]] + [T[b] for b in chain]
        V, F = M.tube(pts, radii, n=12, up=(0, -1, 0))
        return M.Part(V, F, "BH_Skin", name="leg")
    for s, sx in (("L", 1), ("R", -1)):
        p = leg_tube(["scap." + s, "upperarm." + s, "forearm." + s, "fpaw." + s],
                     [(0.14, 0.15), (0.12, 0.13), (0.095, 0.1), (0.075, 0.075), (0.065, 0.06)])
        add(p, bones=["chest", "scap." + s, "upperarm." + s, "forearm." + s, "fpaw." + s], power=8,
            bias={"chest": 1.7})
        p = leg_tube(["thigh." + s, "shin." + s, "hpaw." + s],
                     [(0.16, 0.17), (0.12, 0.13), (0.085, 0.085), (0.065, 0.06)])
        add(p, bones=["hips", "thigh." + s, "shin." + s, "hpaw." + s], power=8, bias={"hips": 1.7})
        for lb, cen, sc in (("upperarm." + s, (sx * 0.3, -0.33, 0.44), (0.07, 0.14, 0.13)),
                            ("thigh." + s, (sx * 0.32, 0.41, 0.5), (0.07, 0.16, 0.15))):
            V, F = M.sphere(1.0, 12, 6, center=cen, scale=sc)
            add(M.Part(V, F, "BH_Steel", name="legplate"), bone=lb)
        for toe, meta, ncl, clen in (("ftoe." + s, "fpaw." + s, 3, 0.15), ("htoe." + s, "hpaw." + s, 4, 0.07)):
            c = H[toe]
            V, F = M.sphere(0.085, 12, 5, center=c + np.array([0, -0.03, 0.01]), scale=(1.0, 1.05, 0.5))
            add(M.Part(V, F, "BH_Skin", name="foot"), bone=toe)
            V, F = M.sphere(0.07, 10, 5, center=H[meta] + np.array([0, -0.01, 0.0]), scale=(1.0, 1.0, 0.85))
            add(M.Part(V, F, "BH_Skin", name="ankle"), bone=meta)
            angs = (-24, 0, 24) if ncl == 3 else (-36, -12, 12, 36)
            for ang in angs:
                d = Rz(ang) @ np.array([0.0, -1.0, 0.0])
                b0 = c + np.array([0, -0.04, 0.03]) + d * 0.04
                b1 = b0 + d * clen * 0.5 + np.array([0, 0, 0.005])
                b2 = b0 + d * clen * 0.85 + np.array([0, 0, -0.02])
                b3 = b0 + d * clen + np.array([0, 0, -0.045])
                w = 0.028 if ncl == 3 else 0.018
                V, F = M.tube([b0, b1, b2], [(w, w * 0.8), (w * 0.8, w * 0.65), (w * 0.5, w * 0.4)], n=6, up=(0, 0, 1))
                add(M.Part(V, F, "BH_Bone", name="claw"), bone=toe)
                V, F = M.tube([b2, b3], [(w * 0.5, w * 0.4), (0.002, 0.002)], n=6, up=(0, 0, 1))
                add(M.Part(V, F, "BH_Horn", name="claw_tip"), bone=toe)
    return parts


# ------------------------------------------------------------------------------------------------ ground contact
def skin_points(parts, c, stride=3):
    Rd, S, L, X = evaluate(c)
    out = []
    for p in parts:
        V = p.V[::stride]
        W = p.W[::stride]
        P = np.zeros_like(V)
        tot = np.zeros(len(V))
        for b in set(k for d in W for k in d):
            w = np.array([d.get(b, 0.0) for d in W])
            P += w[:, None] * (V @ X[b].R.T + X[b].t)
            tot += w
        out.append(P / tot[:, None])
    return np.vstack(out)


def ground_z(parts, c):
    return float(skin_points(parts, c)[:, 2].min())


def fit_ground(parts):
    """body.up values that put the lowest skinned vertex on the ground (+1 cm) for the ball (every roll frame),
    the flipped pose and the final death poses."""
    global BALL_CEN
    for _ in range(2):      # roll about the centre of the skinned ball's bounds (not the bone-chain centre)
        b0 = ball_pose(1.0, up=0.0)
        P = skin_points(parts, b0)
        t = np.array([0.0, -b0["body.fwd"], 0.0])
        BALL_CEN = np.array([0.0, *((P.min(0) + P.max(0)) / 2 - t)[1:]])
    b0 = ball_pose(1.0, up=0.0)
    GROUND["ball"] = 0.01 - ground_z(parts, b0)
    GROUND["roll"] = [0.01 - ground_z(parts, dict(b0, **roll_channels(f, 18))) for f in range(18)]
    GROUND["flip"] = 0.01 - ground_z(parts, flip_pose(up=0.0))
    for nm, fn in (("death", death_clip), ("death_back", death_back_clip)):
        cl = fn(nm)
        ch = cl.channels(float(cl.frames))
        ch["body.up"] = 0.0
        GROUND[nm] = 0.0 - ground_z(parts, ch)
    P = skin_points(parts, ball_pose(1.0))
    cen = P.mean(0)
    r = np.linalg.norm(P - cen, axis=1)
    print(f"[{NAME}] ground fit: ball up {GROUND['ball']:.3f}, roll up {min(GROUND['roll']):.3f}..{max(GROUND['roll']):.3f}"
          f", flip {GROUND['flip']:.3f}, death {GROUND['death']:.3f}, death_back {GROUND['death_back']:.3f}")
    print(f"[{NAME}] ball: centre {cen.round(3)}, bounds {P.min(0).round(2)} .. {P.max(0).round(2)}, "
          f"radius p50 {np.percentile(r, 50):.3f} p95 {np.percentile(r, 95):.3f} max {r.max():.3f}")


# ------------------------------------------------------------------------------------------------ Blender side
def build_all(only=None):
    import bpy
    import bh_mesh as M
    import bh_materials as MT
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    mats = MT.make_materials(NAME, vertex_color=False, extra=PALETTE)
    arm = K.build_armature(RIG)
    parts = build_mesh(mats)
    fit_ground(parts)
    mesh = M.build_skinned(NAME, parts, arm, mats, sharp_angle=50)
    MT.bake_vertex_ao(mesh, rays=12, dist=0.25, strength=0.55)
    acts = {}
    for c in clips():
        if only and c.name not in only:
            continue
        acts[c.name] = (c, K.bake(arm, RIG, c, evaluate))
    return arm, mesh, acts


REST_CFG = dict(views=[("front 3/4", (0, 0, 0.55), 5.2, 35, 12), ("side", (0, 0.1, 0.55), 5.2, 90, 6),
                       ("back 3/4", (0, 0, 0.55), 5.2, 215, 18), ("head close-up", (0, -0.85, 0.6), 1.6, 30, 10)],
                game=[(16, 0, 1.0), (16, 150, 1.0), (24, 60, 1.0)], target_z=0.55)


def clip_cfg():
    return dict(clips=["shell_bite", "shell_swipe", "shell_curl", "shell_roll", "shell_uncurl", "shell_flipped", "walk",
                       "death_back"], target=(0, 0.0, 0.55), dist=5.4, yaw=60, pitch=14)


if __name__ == "__main__" and "--design" in sys.argv:
    print("ball centre", BALL_CEN.round(3))
    for c in clips():
        for f in range(0, c.frames + 1, max(c.frames // 3, 1)):
            evaluate(c.channels(float(f)))
    print("clips evaluate OK")
    sys.exit(0)

if __name__ == "__main__":
    K.run_main(build_all, NAME, PREFIX, "tools/blender/creatures/build_shellback_grinder.py", REST_CFG, clip_cfg,
               RIG, evaluate)
