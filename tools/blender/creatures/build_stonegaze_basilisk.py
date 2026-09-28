"""Stonegaze Basilisk (bh-013, Builder C): a low, heavy four-legged lizard ~3.2 m nose to tail, ~1.1 m at the shoulder.
Slate-grey stony hide with darker scale plates, mossy and pale-lichen patches, a row of stone spikes down the back,
heavy sprawling legs with clawed feet, a long tail ending in a stone club, two big glowing yellow-green eyes and a
tall fan-like frill behind the head (folded back at rest, spread wide during the gaze, glowing eye-spots on it).

Rig / planar leg IK / gait machinery: kit_c13.Quadruped (ported from build_rootback_boar.py / build_wolf.py, which are
not modified). Sprawl: each leg hangs from a horizontal humerus / femur bone (scap.* / femur.*) whose long-axis
rotation swings the leg; the IK plane sits ~0.55 m out from the spine, feet planted wide.

  "<blender>" -b --factory-startup --python build_stonegaze_basilisk.py -- [--no-export] [--evidence rest|clips|both]
Export: game/assets/characters/stonegaze_basilisk.glb (+ .import); merges ONLY animations.basilisk_* and
models.stonegaze_basilisk into creature_meta.json. Faces -Y (= +Z in Godot), origin on the ground under the body.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_c13 as K  # noqa: E402
from kit_c13 import Rx, Ry, Rz, cyc, damp, normalize  # noqa: E402
import numpy as np  # noqa: E402

NAME = "stonegaze_basilisk"
PREFIX = "basilisk_"
FPS = K.FPS
PALETTE = {
    "BH_Stone": ((0.27, 0.29, 0.3), 0.0, 0.85, None, 0.0, 1.0),             # slate hide
    "BH_Horn": ((0.15, 0.16, 0.18), 0.0, 0.7, None, 0.0, 1.0),              # dark scale plates, spikes, brows
    "BH_Skin": ((0.43, 0.41, 0.36), 0.0, 0.7, None, 0.0, 1.0),              # pale belly / throat
    "BH_Cloth_Secondary": ((0.17, 0.27, 0.07), 0.0, 0.95, None, 0.0, 1.0),  # moss
    "BH_Fur": ((0.52, 0.5, 0.3), 0.0, 0.95, None, 0.0, 1.0),                # pale lichen
    "BH_Flesh": ((0.46, 0.25, 0.12), 0.0, 0.6, None, 0.0, 1.0),             # frill membrane (rust)
    "BH_Wood": ((0.09, 0.08, 0.07), 0.0, 0.5, None, 0.0, 1.0),              # claws
    "BH_Bone": ((0.78, 0.74, 0.6), 0.0, 0.5, None, 0.0, 1.0),               # teeth
    "BH_Shadow": ((0.03, 0.02, 0.02), 0.0, 0.6, None, 0.0, 1.0),            # mouth, pupils
    "BH_Emissive": ((0.78, 1.0, 0.18), 0.0, 0.35, (0.75, 1.0, 0.15), 7.0, 1.0),   # yellow-green eyes / eye-spots
}

# ------------------------------------------------------------------------------------------------ skeleton
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.25), None),
    "hips": ((0, 0.5, 0.72), (0, 0.15, 0.74), "root"),
    "spine": ((0, 0.15, 0.74), (0, -0.22, 0.77), "hips"),
    "chest": ((0, -0.22, 0.77), (0, -0.62, 0.8), "spine"),
    "neck": ((0, -0.64, 0.82), (0, -0.93, 0.87), "chest"),
    "head": ((0, -0.93, 0.87), (0, -1.5, 0.78), "neck"),
    "jaw": ((0, -1.0, 0.8), (0, -1.47, 0.69), "head"),
    "frill.C": ((0, -0.9, 0.95), (0, -0.54, 1.57), "head"),
    "frill.L": ((0.05, -0.9, 0.93), (0.5, -0.7, 1.26), "head"),
    "frill.R": ((-0.05, -0.9, 0.93), (-0.5, -0.7, 1.26), "head"),
}
TAIL = [(0, 0.55, 0.7), (0, 0.78, 0.6), (0, 0.99, 0.5), (0, 1.18, 0.4), (0, 1.35, 0.32), (0, 1.5, 0.26),
        (0, 1.63, 0.23)]
for _i in range(6):
    BONES[f"tail.{_i + 1}"] = (TAIL[_i], TAIL[_i + 1], "hips" if _i == 0 else f"tail.{_i}")
FX, HX = 0.56, 0.55          # sprawl: IK plane offsets of the front / hind legs
for _s, _x in (("L", 1.0), ("R", -1.0)):
    BONES.update({
        f"scap.{_s}": ((0.2 * _x, -0.5, 0.7), (FX * _x, -0.52, 0.56), "chest"),
        f"upperarm.{_s}": ((FX * _x, -0.52, 0.56), (FX * _x, -0.45, 0.31), f"scap.{_s}"),
        f"forearm.{_s}": ((FX * _x, -0.45, 0.31), (FX * _x, -0.52, 0.12), f"upperarm.{_s}"),
        f"fpaw.{_s}": ((FX * _x, -0.52, 0.12), (FX * _x, -0.58, 0.05), f"forearm.{_s}"),
        f"ftoe.{_s}": ((FX * _x, -0.58, 0.05), (FX * _x, -0.74, 0.02), f"fpaw.{_s}"),
        f"femur.{_s}": ((0.2 * _x, 0.45, 0.66), (HX * _x, 0.47, 0.54), "hips"),
        f"thigh.{_s}": ((HX * _x, 0.47, 0.54), (HX * _x, 0.38, 0.3), f"femur.{_s}"),
        f"shin.{_s}": ((HX * _x, 0.38, 0.3), (HX * _x, 0.47, 0.12), f"thigh.{_s}"),
        f"hpaw.{_s}": ((HX * _x, 0.47, 0.12), (HX * _x, 0.42, 0.05), f"shin.{_s}"),
        f"htoe.{_s}": ((HX * _x, 0.42, 0.05), (HX * _x, 0.26, 0.02), f"hpaw.{_s}"),
    })
RIG = K.Rig(BONES)
H, T = RIG.H, RIG.T
LEGS = {
    "LF": ("scap.L", "upperarm.L", "forearm.L", "fpaw.L", "ftoe.L"),
    "RF": ("scap.R", "upperarm.R", "forearm.R", "fpaw.R", "ftoe.R"),
    "LH": ("femur.L", "thigh.L", "shin.L", "hpaw.L", "htoe.L"),
    "RH": ("femur.R", "thigh.R", "shin.R", "hpaw.R", "htoe.R"),
}
SCAP = {"LF": "scap.L", "RF": "scap.R", "LH": "femur.L", "RH": "femur.R"}
FRILL_N = Rx(-60) @ np.array([0.0, 1.0, 0.0])      # normal of the (rest, folded-back) frill plane


def extra(c, Rd, S, L):
    Rd["jaw"] = Rx(c.get("jaw", 0.0))
    fr = c.get("frill", 0.0)
    sp = c.get("frill.spread", 0.0)
    Rd["frill.C"] = Rx(fr)
    Rd["frill.L"] = Rx(fr * 0.9) @ K.R_axis(FRILL_N, sp)
    Rd["frill.R"] = Rx(fr * 0.9) @ K.R_axis(FRILL_N, -sp)
    s = 1.0 + 0.004 * max(fr, 0.0)
    for b in ("frill.C", "frill.L", "frill.R"):
        S[b] = (s, s, s)
    for i in range(1, 7):
        w = 0.5 + 0.18 * i
        Rd[f"tail.{i}"] = Rz(c.get("tail.yaw", 0.0) * w / 1.5 + c.get("tail.wag", 0.0) * cyc(i, 6, 1, c.get("tail.ph", 0.0))
                             * 0.35) @ Rx(c.get("tail.lift", 0.0) * (1.0 if i == 1 else 0.3) + c.get("tail.curl", 0.0) * 0.2 * (i - 1))


QD = K.Quadruped(RIG, LEGS, pivot=(0.0, -0.05, 0.75), spine=("hips", "spine", "chest", "neck", "head"), extra=extra,
                 scap_bones=tuple(SCAP.values()))
evaluate = QD.evaluate


# ------------------------------------------------------------------------------------------------ clips
def undulate(per, amp, k=1):
    """Lizard lateral undulation: shoulders and hips swing opposite, the tail follows."""
    def fn(f, cl):
        s = cyc(f, per, k)
        return {"hips.yaw": amp * s, "spine.yaw": -0.5 * amp * s, "chest.yaw": -amp * s,
                "neck.yaw": 0.6 * amp * s, "tail.yaw": -1.4 * amp * cyc(f, per, k, 0.12),
                "body.roll": 0.25 * amp * cyc(f, per, k, 0.25)}
    return fn


def clips():
    C = []
    P = 90
    c = K.Clip("idle", P, loop=True)
    c.key(0)
    c.layer(lambda f, cl: {"chest.pitch": 1.2 * cyc(f, P, 2), "body.up": 0.006 * cyc(f, P, 2),
                           "neck.pitch": 3 + 2 * cyc(f, P, 1, 0.1), "head.yaw": 4 * cyc(f, P, 1, 0.3),
                           "head.pitch": -2 + 1.5 * cyc(f, P, 3), "tail.yaw": 6 * cyc(f, P, 1),
                           "tail.wag": 5 * cyc(f, P, 1, 0.3), "tail.ph": 0.0, "jaw": 2 + 2 * cyc(f, P, 2, 0.4),
                           "frill": 4 + 4 * cyc(f, P, 2, 0.2), "frill.spread": 3 * cyc(f, P, 2, 0.2)})
    C.append(c)
    c = K.Clip("idle_look", 75)
    c.key(0).key(15, neck_yaw=22, head_yaw=16, neck_pitch=8, frill=12, tail_yaw=-10)
    c.key(30, neck_yaw=24, head_yaw=18, neck_pitch=8, frill=14, tail_yaw=-12, jaw=6)
    c.key(46, neck_yaw=-22, head_yaw=-16, neck_pitch=6, head_roll=-4, frill=10, tail_yaw=12, jaw=0)
    c.key(60, neck_yaw=-18, head_yaw=-14, neck_pitch=4, frill=8, tail_yaw=10)
    c.key(75, neck_yaw=0, head_yaw=0, neck_pitch=0, head_roll=0, frill=0, tail_yaw=0, jaw=0)
    C.append(c)
    WALK_P, WALK_V = 40, 1.0
    c = K.Clip("walk", WALK_P, loop=True, ground_speed=WALK_V)
    c.key(0)
    c.layer(K.gait_layer(WALK_P, 0.66, WALK_V, {"LH": 0.0, "RF": 0.05, "RH": 0.5, "LF": 0.55}, 0.1, 0.09, 40, 25, 12,
                         scap_gain=-60.0, scap=SCAP))
    c.layer(undulate(WALK_P, 7.0))
    c.layer(lambda f, cl: {"body.up": -0.01 + 0.01 * cyc(f, WALK_P, 2), "neck.pitch": -2 + 2 * cyc(f, WALK_P, 2, 0.2),
                           "tail.wag": 6, "tail.ph": f / WALK_P})
    C.append(c)
    RUN_P, RUN_V = 22, 3.4
    for nm in ("run", "run_combat"):
        c = K.Clip(nm, RUN_P, loop=True, ground_speed=RUN_V)
        c.key(0)
        c.layer(K.gait_layer(RUN_P, 0.5, RUN_V, {"LH": 0.0, "RF": 0.02, "RH": 0.5, "LF": 0.52}, 0.16, 0.14, 60, 32, 16,
                             scap_gain=-55.0, scap=SCAP))
        c.layer(undulate(RUN_P, 11.0))
        low = nm == "run_combat"
        c.layer(lambda f, cl, low=low: {
            "body.up": (-0.05 if low else -0.02) + 0.025 * cyc(f, RUN_P, 2, 0.1), "body.pitch": 1.5 * cyc(f, RUN_P, 2),
            "neck.pitch": (-10 if low else -4) + 3 * cyc(f, RUN_P, 2, 0.6), "head.pitch": 4 if low else 0,
            "tail.lift": 6, "tail.wag": 8, "tail.ph": f / RUN_P, "jaw": 8 if low else 3, "frill": 14 if low else 0})
        C.append(c)
    # ---- reactions
    c = K.Clip("hit_light", 12)
    c.key(0).key(3, body_fwd=-0.05, body_pitch=3, neck_pitch=12, head_pitch=5, neck_yaw=8, jaw=14, frill=20)
    c.key(12, body_fwd=0, body_pitch=0, neck_pitch=0, head_pitch=0, neck_yaw=0, jaw=0, frill=0)
    C.append(c)
    c = K.Clip("hit_heavy", 18)
    c.key(0).key(4, body_fwd=-0.12, body_up=-0.05, body_pitch=6, body_roll=5, neck_pitch=18, head_pitch=10,
                 neck_yaw=14, jaw=22, frill=30, tail_yaw=12, LF_f=0.05, RF_f=0.04)
    c.key(9, body_fwd=-0.1, body_up=-0.04, body_pitch=4, body_roll=3, neck_pitch=10, head_pitch=4, neck_yaw=8,
          jaw=8, frill=18, tail_yaw=8, LF_f=0.08, RF_f=0.05)
    c.key(18, body_fwd=0, body_up=0, body_pitch=0, body_roll=0, neck_pitch=0, head_pitch=0, neck_yaw=0, jaw=0,
          frill=0, tail_yaw=0, LF_f=0, RF_f=0)
    C.append(c)
    c = K.Clip("stagger_small", 24)
    c.key(0).key(5, body_fwd=-0.08, body_side=-0.05, body_roll=-6, body_pitch=4, neck_pitch=12, neck_yaw=-16,
                 tail_yaw=14, frill=16)
    c.key(9, LF_up=0.08, LF_f=-0.03, body_fwd=-0.11, body_side=-0.06, body_roll=-7, neck_pitch=8, neck_yaw=-12)
    c.key(14, LF_up=0.0, LF_f=-0.1, RH_f=-0.08, body_fwd=-0.09, body_roll=-3, body_side=-0.03, neck_pitch=4)
    c.key(24, LF_f=0, RH_f=0, body_fwd=0, body_side=0, body_roll=0, body_pitch=0, neck_pitch=0, neck_yaw=0,
          tail_yaw=0, frill=0)
    C.append(c)
    c = K.Clip("knockback", 27)
    c.key(0).key(4, body_fwd=-0.2, body_up=0.03, body_pitch=10, neck_pitch=16, jaw=22, frill=30, tail_lift=-6,
                 LF_up=0.12, RF_up=0.1, LF_f=0.08, RF_f=0.1, LH_f=0.14, RH_f=0.12, hips_pitch=-5)
    c.key(11, body_fwd=-0.3, body_up=-0.07, body_pitch=4, neck_pitch=6, jaw=8, frill=20, LF_up=0.0, RF_up=0.0,
          LF_f=0.12, RF_f=0.08, LH_f=0.18, RH_f=0.16, hips_pitch=-2)
    c.key(18, body_fwd=-0.18, body_up=-0.04, body_pitch=2, neck_pitch=3, jaw=3, frill=8, LF_f=0.06, RF_f=0.02,
          LH_f=0.1, RH_f=0.1, hips_pitch=0)
    c.key(27, body_fwd=0, body_up=0, body_pitch=0, neck_pitch=0, jaw=0, frill=0, tail_lift=0, LF_f=0, RF_f=0,
          LH_f=0, RH_f=0)
    C.append(c)
    C.append(death_clip("death", side=1))
    C.append(death_clip("death_back", side=-1))
    # ---- alert: head up, frill flicks open, tail lifts, then a low hiss
    c = K.Clip("alert", 30)
    c.key(0).key(7, neck_pitch=14, head_pitch=-6, frill=45, frill_spread=14, tail_lift=12, body_up=0.03, jaw=16)
    c.key(14, neck_pitch=8, head_pitch=-4, frill=38, frill_spread=10, tail_lift=10, jaw=26)
    c.key(22, neck_pitch=0, head_pitch=0, frill=18, frill_spread=4, tail_lift=6, jaw=10)
    c.key(30, neck_pitch=-2, head_pitch=0, frill=8, frill_spread=0, tail_lift=0, body_up=0.0, jaw=2)
    C.append(c)
    # ---- basilisk_bite (0.9 s): head draws back, then a snapping forward-down lunge; jaws close ~0.45 s
    c = K.Clip("basilisk_bite", 27, hits=[[12 / FPS, 16 / FPS]])
    c.key(0).key(8, body_fwd=-0.08, body_pitch=3, neck_pitch=16, head_pitch=6, jaw=30, frill=30, frill_spread=8,
                 LH_f=0.03, RH_f=0.03)
    c.key(12, body_fwd=0.18, body_pitch=-4, neck_pitch=-18, head_pitch=-8, jaw=38, frill=20, LF_f=0.12, RF_f=0.08)
    c.key(14, body_fwd=0.22, body_pitch=-5, neck_pitch=-22, head_pitch=-10, jaw=2, frill=18, LF_f=0.14, RF_f=0.1)
    c.key(18, body_fwd=0.18, body_pitch=-3, neck_pitch=-14, head_pitch=-4, jaw=4, frill=12, LF_f=0.12, RF_f=0.08)
    c.key(27, body_fwd=0, body_pitch=0, neck_pitch=0, head_pitch=0, jaw=0, frill=0, frill_spread=0, LF_f=0, RF_f=0,
          LH_f=0, RH_f=0)
    C.append(c)
    # ---- basilisk_gaze (1.2 s LOOP, held while channelling): forequarters reared, frill spread wide, head locked
    #      forward at the target, jaw ajar; only a tremble, breathing and a pulsing frill (first frame == last frame)
    G = 36
    c = K.Clip("basilisk_gaze", G, loop=True)
    g = dict(body_pitch=13, body_up=0.06, body_fwd=-0.08, hips_pitch=-5, neck_pitch=-4, head_pitch=-6, jaw=12,
             frill=62, frill_spread=30, tail_lift=-4, LF_f=0.02, RF_f=0.02, LF_phi=-8, RF_phi=-8)
    c.keyd(0, {k.replace("_", "."): v for k, v in g.items()}).keyd(G, {k.replace("_", "."): v for k, v in g.items()})
    c.layer(lambda f, cl: {"frill": 3 * cyc(f, G, 2), "frill.spread": 2 * cyc(f, G, 2, 0.25),
                           "head.yaw": 0.8 * cyc(f, G, 6), "head.roll": 0.6 * cyc(f, G, 5, 0.3),
                           "chest.pitch": 1.0 * cyc(f, G, 1), "body.up": 0.006 * cyc(f, G, 1),
                           "tail.yaw": 5 * cyc(f, G, 1, 0.2), "jaw": 2 * cyc(f, G, 3)})
    C.append(c)
    # ---- basilisk_tail (0.9 s): turns its hips, winds the club tail to its right, then sweeps it round its left
    #      side toward the front; the club passes the front-left flank ~0.6 s
    c = K.Clip("basilisk_tail", 27, hits=[[16 / FPS, 20 / FPS]])
    c.key(0).key(8, body_yaw=10, hips_yaw=12, spine_yaw=4, tail_yaw=-45, tail_lift=8, tail_curl=-4, neck_yaw=-14,
                 frill=20, jaw=10, body_side=-0.04)
    c.key(14, body_yaw=-6, hips_yaw=-10, spine_yaw=-6, tail_yaw=30, tail_lift=12, tail_curl=6, neck_yaw=10,
          frill=24, jaw=16, body_side=0.03)
    c.key(18, body_yaw=-14, hips_yaw=-22, spine_yaw=-12, chest_yaw=-6, tail_yaw=88, tail_lift=10, tail_curl=14,
          neck_yaw=18, frill=26, jaw=18, body_side=0.06)
    c.key(21, body_yaw=-15, hips_yaw=-24, spine_yaw=-12, chest_yaw=-7, tail_yaw=96, tail_lift=6, tail_curl=16,
          neck_yaw=16, frill=22, jaw=12, body_side=0.06)
    c.key(27, body_yaw=0, hips_yaw=0, spine_yaw=0, chest_yaw=0, tail_yaw=0, tail_lift=0, tail_curl=0, neck_yaw=0,
          frill=0, jaw=0, body_side=0)
    C.append(c)
    return C


def death_clip(name, side):
    """Legs buckle, the body drops and rolls onto its side (side=+1: onto its right side); tail flops."""
    c = K.Clip(name, 45)
    r = 80 * side
    c.key(0)
    c.key(8, body_up=-0.1, body_pitch=-8 if side > 0 else 10, neck_pitch=-8 if side > 0 else 18, head_pitch=-10,
          jaw=24, frill=40, frill_spread=16, tail_lift=-10, LF_f=0.08, RF_f=0.08, LF_phi=25, RF_phi=25)
    k2 = dict(body_up=-0.28, body_roll=r * 0.35, body_side=-0.05 * side, neck_pitch=-4, neck_yaw=-12 * side,
              head_pitch=-6, jaw=30, frill=20, frill_spread=10, tail_yaw=20 * side, tail_lift=-12)
    for k in ("LF", "RF", "LH", "RH"):
        k2[k + "_loc"] = 0.6
        k2[k + "_lf"] = 0.1
        k2[k + "_lup"] = 0.2
    c.key(18, **k2)
    k3 = dict(body_up=-0.36, body_pitch=0, body_roll=r, body_side=-0.12 * side, neck_pitch=-12, neck_yaw=-8 * side,
              head_pitch=-10, head_roll=12 * side, jaw=20, frill=-10, frill_spread=-6, tail_yaw=26 * side,
              tail_lift=-4, tail_curl=-4)
    legs = {"LF": (0.2, 0.14), "RF": (0.08, 0.22), "LH": (-0.1, 0.2), "RH": (0.02, 0.24)}
    for k, (lf, lup) in legs.items():
        k3[k + "_loc"] = 1.0
        k3[k + "_lf"] = lf
        k3[k + "_lup"] = lup
    c.key(30, **k3)
    c.key(45, **dict(k3, body_up=-0.37, neck_pitch=-18, head_pitch=-12, jaw=14))
    return c


# ------------------------------------------------------------------------------------------------ mesh
def build_mesh(mats):
    import bh_mesh as M
    import kit_warren as KW
    parts = []
    rng = np.random.default_rng(47)

    def add(p, bone=None, bones=None, power=6.0, bias=None, top=3, W=None):
        if W is not None:
            p.W = W
        elif bone:
            p.W = [{bone: 1.0}] * len(p.V)
        else:
            p.W = K.dist_weights(RIG, p.V, bones, power=power, bias=bias, top=top)
        parts.append(p)
        return p

    def ring(y, zc, rx, rt, rb, n=20, flat=0.0):
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            s, co = math.sin(a), math.cos(a)
            z = zc + (rt if s > 0 else rb) * s
            if s < 0:
                z = zc + rb * (s * (1 - flat) - flat * 0.6 * abs(co) ** 3 * 0 + flat * s ** 3)
            pts.append((rx * co, y, z))
        return np.array(pts)

    TORSO_B = ["hips", "spine", "chest", "neck", "scap.L", "scap.R", "femur.L", "femur.R", "tail.1"]
    TORSO_BIAS = {"scap.L": 1.45, "scap.R": 1.45, "femur.L": 1.4, "femur.R": 1.4, "tail.1": 1.6, "neck": 1.2}
    BACK_B = ["hips", "spine", "chest"]
    BODY = [(0.62, 0.7, 0.2, 0.14, 0.16), (0.48, 0.71, 0.32, 0.2, 0.25), (0.25, 0.73, 0.38, 0.24, 0.3),
            (-0.05, 0.75, 0.4, 0.26, 0.32), (-0.35, 0.77, 0.39, 0.26, 0.32), (-0.58, 0.79, 0.33, 0.22, 0.28),
            (-0.72, 0.82, 0.25, 0.18, 0.2)]
    rings = [ring(*r, n=24) for r in BODY]
    V, F = M.loft(rings[::-1], cap0=True, cap1=True)
    body = M.Part(V, F, "BH_Stone", name="body")
    body.V += rng.normal(size=body.V.shape) * 0.004
    add(body, bones=TORSO_B, bias=TORSO_BIAS)
    # pale belly plates (flat underside band)
    for (y, zc, rx, rt, rb) in BODY[1:-1]:
        V, F = M.sphere(1.0, 12, 4, scale=(rx * 0.75, 0.13, 0.04))
        add(M.Part(V + np.array([0, y, zc - rb * 0.96]), F, "BH_Skin", name="belly"), bones=TORSO_B, bias=TORSO_BIAS)

    def top_z(y):
        for (y0, z0, rx0, rt0, rb0), (y1, z1, rx1, rt1, rb1) in zip(BODY, BODY[1:]):
            if y1 <= y <= y0:
                t = (y0 - y) / (y0 - y1)
                return z0 + (z1 - z0) * t + rt0 + (rt1 - rt0) * t, rx0 + (rx1 - rx0) * t, rt0 + (rt1 - rt0) * t
        return BODY[-1][1] + BODY[-1][3], BODY[-1][2], BODY[-1][3]

    # ---- neck + wedge head with heavy brows, big glowing eyes, a lower jaw with teeth
    NECK = [(-0.6, 0.8, 0.27, 0.2, 0.22), (-0.78, 0.84, 0.22, 0.17, 0.18), (-0.94, 0.87, 0.19, 0.15, 0.15)]
    V, F = M.loft([ring(*r, n=18) for r in NECK][::-1], cap0=False, cap1=False)
    add(M.Part(V, F, "BH_Stone", name="neck"), bones=["chest", "neck", "head"], bias={"head": 1.3})
    SKULL = [(-0.88, 0.88, 0.17, 0.13, 0.12), (-1.0, 0.88, 0.2, 0.12, 0.1), (-1.14, 0.86, 0.19, 0.1, 0.07),
             (-1.28, 0.83, 0.16, 0.08, 0.06), (-1.42, 0.8, 0.12, 0.065, 0.05), (-1.53, 0.78, 0.08, 0.05, 0.04),
             (-1.57, 0.775, 0.05, 0.035, 0.03)]
    V, F = M.loft([ring(*r, n=18) for r in SKULL][::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Stone", name="skull"), bone="head")
    JAW = [(-1.0, 0.78, 0.17, 0.03, 0.06), (-1.2, 0.76, 0.15, 0.03, 0.05), (-1.4, 0.74, 0.1, 0.025, 0.035),
           (-1.53, 0.74, 0.06, 0.02, 0.025)]
    V, F = M.loft([ring(*r, n=14) for r in JAW][::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Stone", name="jaw"), bone="jaw")
    V, F = M.loft([ring(y, z + 0.03, rx * 0.92, 0.01, 0.012, n=14) for (y, z, rx, rt, rb) in JAW][::-1])
    add(M.Part(V, F, "BH_Shadow", name="mouth"), bone="jaw")
    V, F = M.sphere(1.0, 10, 4, scale=(0.12, 0.2, 0.035))
    add(M.Part(V + np.array([0, -1.18, 0.73]), F, "BH_Skin", name="throat"), bone="jaw")
    for sx in (1, -1):
        for i in range(6):
            y = -1.08 - 0.075 * i
            rx = float(np.interp(-y, [1.0, 1.2, 1.4, 1.53], [0.17, 0.15, 0.1, 0.06])) * 0.88
            V, F = M.lathe([(0.012, 0.0), (0.006, 0.03), (0.0, 0.045)], 6)
            add(M.Part(V + np.array([sx * rx, y, 0.8 - 0.004 * i]), F, "BH_Bone", name="tooth"), bone="jaw")
            V, F = M.lathe([(0.012, 0.0), (0.006, 0.03), (0.0, 0.045)], 6)
            p = M.Part(V, F, "BH_Bone", name="utooth").rot(Rx(180)).move((sx * rx * 1.02, y, 0.81 - 0.004 * i))
            add(p, bone="head")
        # eyes: big, bulging on the upper sides of the head (read from above), dark slit pupils, stone brow
        ec = np.array([sx * 0.15, -1.06, 0.97])
        V, F = M.sphere(0.092, 14, 7, center=ec, scale=(0.9, 1.0, 0.95))
        add(M.Part(V, F, "BH_Emissive", name="eye"), bone="head")
        V, F = M.box(0.012, 0.018, 0.1)
        pup = M.Part(V, F, "BH_Shadow", name="pupil").rot(Rz(-25 * sx)).move(ec + np.array([sx * 0.08, -0.012, 0.0]))
        add(pup, bone="head")
        V, F = M.sphere(0.1, 10, 5, center=ec + np.array([sx * 0.01, 0.01, 0.075]), scale=(1.0, 1.35, 0.35))
        add(M.Part(V, F, "BH_Horn", name="brow"), bone="head")
        for k in range(3):     # horn nubs above / behind the eye
            V, F = M.lathe([(0.03, 0.0), (0.015, 0.05), (0.0, 0.08)], 6)
            p = M.Part(V, F, "BH_Horn", name="nub")
            p.rot(K.align_z(normalize(np.array([sx * 0.5, 0.6 + 0.2 * k, 0.6])))).move(
                ec + np.array([sx * 0.02, 0.07 + 0.06 * k, 0.07 - 0.015 * k]))
            add(p, bone="head")
        V, F = M.sphere(0.018, 6, 4, center=(sx * 0.045, -1.56, 0.8), scale=(1.0, 0.6, 0.8))
        add(M.Part(V, F, "BH_Shadow", name="nostril"), bone="head")
    # ---- the frill: a fan of stone spines with a membrane, folded back at rest, glowing eye-spots on it
    C0 = np.array([0.0, -0.9, 0.95])
    thetas = np.linspace(-105, 105, 11)
    FR = Rx(-60)

    def fan(th, r):
        t = math.radians(th)
        return C0 + FR @ np.array([math.sin(t) * r, 0.0, math.cos(t) * r])
    RLEN = [0.44 + 0.28 * math.cos(math.radians(th)) ** 2 for th in thetas]
    FR_B = ["frill.C", "frill.L", "frill.R"]
    rows = []
    for j, u in enumerate(np.linspace(0.18, 1.0, 5)):
        rows.append([fan(th, RLEN[i] * u * (0.9 + 0.1 * math.cos(i * 1.7))) for i, th in enumerate(thetas)])
    Vf = np.array([p for r in rows for p in r])
    n = len(thetas)
    Ff = []
    for j in range(len(rows) - 1):
        for i in range(n - 1):
            Ff.append((j * n + i, j * n + i + 1, (j + 1) * n + i + 1, (j + 1) * n + i))
    Wf = K.dist_weights(RIG, Vf, FR_B, power=4, top=3)
    nrm = FR @ np.array([0.0, -1.0, 0.0])
    add(M.Part(Vf - nrm * 0.008, Ff, "BH_Flesh", name="frill_front"), W=Wf)
    add(M.Part(Vf + nrm * 0.008, [tuple(reversed(f)) for f in Ff], "BH_Flesh", name="frill_back"), W=Wf)
    for i, th in enumerate(thetas):
        tip = fan(th, RLEN[i] * 1.12)
        V, F = M.tube([fan(th, 0.12), fan(th, RLEN[i] * 0.6), tip], [(0.024, 0.02), (0.016, 0.014), (0.004, 0.004)],
                      n=6, up=tuple(nrm))
        add(M.Part(V, F, "BH_Horn", name="frill_spine"), bones=FR_B, power=4, top=2)
        if i % 2 == 1:         # eye-spots on the front face of the membrane
            q = fan(th + 9, RLEN[i] * 0.72)
            V, F = M.sphere(0.04, 10, 4, scale=(1.0, 1.0, 0.35))
            p = M.Part(V, F, "BH_Emissive", name="eyespot").rot(K.align_z(nrm)).move(q + nrm * 0.006)
            add(p, bones=FR_B, power=4, top=2)
            V, F = M.sphere(0.062, 10, 4, scale=(1.0, 1.0, 0.25))
            p = M.Part(V, F, "BH_Horn", name="eyespot_ring").rot(K.align_z(nrm)).move(q + nrm * 0.002)
            add(p, bones=FR_B, power=4, top=2)
    # ---- sprawling legs: thick humerus / femur out to the side, elbow / knee, broad clawed feet
    def leg_tube(chain, radii):
        pts = [H[chain[0]]] + [T[b] for b in chain]
        V, F = M.tube(pts, radii, n=12, up=(0, -1, 0))
        return M.Part(V, F, "BH_Stone", name="leg")
    for s, sx in (("L", 1), ("R", -1)):
        p = leg_tube(["scap." + s, "upperarm." + s, "forearm." + s, "fpaw." + s],
                     [(0.15, 0.17), (0.12, 0.13), (0.1, 0.1), (0.075, 0.07), (0.06, 0.05)])
        add(p, bones=["chest", "scap." + s, "upperarm." + s, "forearm." + s, "fpaw." + s], power=8,
            bias={"chest": 1.7})
        p = leg_tube(["femur." + s, "thigh." + s, "shin." + s, "hpaw." + s],
                     [(0.17, 0.2), (0.14, 0.16), (0.11, 0.11), (0.08, 0.075), (0.06, 0.05)])
        add(p, bones=["hips", "femur." + s, "thigh." + s, "shin." + s, "hpaw." + s], power=8, bias={"hips": 1.7})
        for toe, meta in (("ftoe." + s, "fpaw." + s), ("htoe." + s, "hpaw." + s)):
            c = H[toe]
            V, F = M.sphere(0.09, 12, 5, center=c + np.array([0, -0.03, 0.01]), scale=(1.0, 1.05, 0.45))
            add(M.Part(V, F, "BH_Stone", name="foot"), bone=toe)
            V, F = M.sphere(0.075, 10, 5, center=H[meta] + np.array([0, -0.02, 0.0]), scale=(1.0, 1.0, 0.8))
            add(M.Part(V, F, "BH_Stone", name="ankle"), bone=meta)
            for k, ang in enumerate((-40, -14, 12, 38)):      # four splayed toes with dark hooked claws
                d = Rz(ang) @ np.array([0.0, -1.0, 0.0])
                b0 = c + np.array([0, -0.03, 0.0]) + d * 0.05
                b1 = b0 + d * 0.1 + np.array([0, 0, -0.005])
                V, F = M.tube([b0, b1], [(0.026, 0.02), (0.02, 0.016)], n=6, up=(0, 0, 1))
                add(M.Part(V, F, "BH_Stone", name="toe"), bone=toe)
                V, F = M.tube([b1, b1 + d * 0.05 + np.array([0, 0, -0.01]), b1 + d * 0.08 + np.array([0, 0, -0.03])],
                              [(0.016, 0.014), (0.01, 0.009), (0.002, 0.002)], n=5, up=(0, 0, 1))
                add(M.Part(V, F, "BH_Wood", name="claw"), bone=toe)
    # ---- tail and its stone club
    pts = [np.array(p) for p in TAIL]
    rad = [0.19, 0.15, 0.12, 0.095, 0.075, 0.06, 0.05]
    V, F = M.tube(pts, [(r, r * 0.85) for r in rad], n=12, up=(0, 0, 1))
    add(M.Part(V, F, "BH_Stone", name="tail"), bones=["hips"] + [f"tail.{i}" for i in range(1, 7)], power=7,
        bias={"hips": 2.0})
    cc = np.array(TAIL[-1]) + np.array([0, 0.02, 0.0])
    V, F = M.sphere(0.16, 12, 7, center=cc, scale=(1.0, 1.25, 0.85))
    V = cc + (V - cc) * (1 + 0.12 * (rng.random(len(V))[:, None] - 0.5))
    add(M.Part(V, F, "BH_Horn", name="club"), bone="tail.6")
    for k in range(7):
        a = 2 * math.pi * k / 7
        d = normalize(np.array([math.cos(a), 0.4 * (k % 2), math.sin(a) * 0.8 + 0.25]))
        V, F = M.lathe([(0.05, 0.0), (0.025, 0.06), (0.0, 0.1)], 6)
        add(M.Part(V, F, "BH_Stone", name="club_spike").rot(K.align_z(d)).move(cc + d * 0.14), bone="tail.6")
    # ---- dorsal row of stone spikes from the neck down the tail, dark scale plates, moss and lichen
    for i in range(16):
        y = -0.82 + 0.1 * i
        if y < 0.6:
            zt, rx, rt = top_z(y) if y > -0.72 else (0.87 + 0.17, 0.2, 0.17)
            base = np.array([0, y, zt - 0.02])
            bones = BACK_B + ["neck"]
        else:
            tt = min((y - 0.55) / (1.63 - 0.55) * 6, 5.99)
            i0 = int(tt)
            q = np.array(TAIL[i0]) + (np.array(TAIL[i0 + 1]) - np.array(TAIL[i0])) * (tt - i0)
            base = q + np.array([0, 0, rad[i0] * 0.8])
            bones = ["hips"] + [f"tail.{k}" for k in range(1, 7)]
        h = 0.16 * math.sin(math.pi * min(max((i + 1) / 13, 0), 1)) + 0.05
        V, F = M.lathe([(0.055, 0.0), (0.03, h * 0.55), (0.0, h)], 7)
        p = M.Part(V, F, "BH_Horn", name="spike").rot(Rx(-18)).move(base)
        add(p, bones=bones, power=6)
    for y in np.arange(-0.62, 0.62, 0.13):
        zt, rx, rt = top_z(y)
        for f in (-0.72, -0.36, 0.36, 0.72):
            a = f + 0.08 * math.sin(y * 17)
            nrm2 = normalize(np.array([math.sin(a), 0.15, math.cos(a)]))
            cp = np.array([rx * 0.95 * math.sin(a), y, zt - rt + rt * math.cos(a)]) + nrm2 * 0.012
            V, F = M.box(0.13, 0.11, 0.03)
            pl = M.bevel(M.Part(V, F, "BH_Horn", name="plate"), 0.01, 1)
            pl.V += rng.normal(size=pl.V.shape) * 0.004
            pl.rot(K.align_z(nrm2, hint=(0, -1, 0))).move(cp)
            add(pl, bones=BACK_B, power=6)
    for i in range(14):
        y = -0.6 + 1.15 * rng.random()
        zt, rx, rt = top_z(y)
        a = (rng.random() - 0.5) * 2.2
        nrm2 = normalize(np.array([math.sin(a), 0.1, math.cos(a)]))
        cp = np.array([rx * math.sin(a), y, zt - rt + rt * math.cos(a)]) + nrm2 * 0.03
        V, F = M.sphere(0.05 + 0.04 * rng.random(), 9, 4, scale=(1.2, 1.4, 0.3))
        m = M.Part(V, F, "BH_Cloth_Secondary" if i % 3 else "BH_Fur", name="moss")
        m.V += rng.normal(size=m.V.shape) * 0.007
        m.rot(K.align_z(nrm2)).move(cp)
        add(m, bones=BACK_B, power=6)
    for i in range(6):        # lichen on the head and tail
        if i < 3:
            cp = np.array([0.08 * (i - 1), -1.12 - 0.08 * i, 0.93 - 0.02 * i])
            b = "head"
        else:
            q = np.array(TAIL[i - 1])
            cp = q + np.array([0.05 * (i - 4), 0, rad[i - 1] * 0.95])
            b = f"tail.{i - 2}"
        V, F = M.sphere(0.05, 8, 4, scale=(1.2, 1.3, 0.3))
        m = M.Part(V + cp, F, "BH_Fur" if i % 2 else "BH_Cloth_Secondary", name="lichen")
        add(m, bone=b)
    return parts


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
    mesh = M.build_skinned(NAME, parts, arm, mats, sharp_angle=50)
    MT.bake_vertex_ao(mesh, rays=12, dist=0.25, strength=0.55)
    acts = {}
    for c in clips():
        if only and c.name not in only:
            continue
        acts[c.name] = (c, K.bake(arm, RIG, c, evaluate))
    return arm, mesh, acts


REST_CFG = dict(views=[("front 3/4", (0, 0, 0.6), 6.8, 35, 12), ("side", (0, 0, 0.6), 6.8, 90, 8),
                       ("back 3/4", (0, 0, 0.6), 6.8, 210, 16), ("head close-up", (0, -1.05, 0.95), 2.0, 30, 12)],
                game=[(16, 0, 1.0), (16, 150, 1.0), (24, 60, 1.0)], target_z=0.6)


def clip_cfg():
    return dict(clips=["basilisk_bite", "basilisk_gaze", "basilisk_tail", "walk", "run", "death"],
                target=(0, -0.1, 0.65), dist=7.0, yaw=60, pitch=14)


if __name__ == "__main__":
    K.run_main(build_all, NAME, PREFIX, "tools/blender/creatures/build_stonegaze_basilisk.py", REST_CFG, clip_cfg,
               RIG, evaluate)
