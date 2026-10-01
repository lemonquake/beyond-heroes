"""Wireback Stalker (bh-029, Builder M1, Zarael / the Coilwood pouncing charger): a long, low great cat ~2.5 m from
nose to tail tip (~0.9 m at the shoulder). Dark umber hide with near-black rosettes and spots, a pale throat and belly,
a broad heavy head with long fangs and violet-red eyes, big paws, a long thick tail ringed black at the end. Along the
spine runs a ridge of copper wire coils grown into the hide, burning violet-red (the Blackwire), with glowing veins
branching down the flanks from it.

Rig / planar leg IK / gait / clip machinery: build_wolf.py (imported, not edited). The wolf module's skeleton tables
are replaced at import time by this cat's (W.H / W.T / W.PAR / W.R0 / leg rest data), so every wolf function
(evaluate, solve_leg, bake, build_armature, the gait layers, death_clip) works on the cat skeleton unchanged.

  "<blender>" -b --factory-startup --python build_wireback_stalker.py -- [--no-export] [--evidence DIR]

Clips (30 fps, in place): idle idle_look walk run run_combat hit_light hit_heavy stagger_small knockback death
death_back alert + cat_swipe, cat_bite, cat_pounce (leap forward), cat_roar.
creature_meta.json: merges ONLY animations.cat_* and models.wireback_stalker (re-read right before writing).
Conventions: Blender Z-up, faces -Y (= +Z in Godot), origin on the ground under the body, meters.
"""
import argparse
import copy
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHAR = os.path.join(HERE, "..", "characters")
sys.path.insert(0, HERE)
sys.path.insert(0, CHAR)
ROOT_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
NAME = "wireback_stalker"
OUT_GLB = os.path.join(ROOT_DIR, "game", "assets", "characters", NAME + ".glb")
OUT_META = os.path.join(ROOT_DIR, "game", "assets", "characters", "creature_meta.json")

import numpy as np  # noqa: E402

import build_wolf as W  # noqa: E402

FPS = W.FPS
PALETTE = {
    "BH_Fur": ((0.165, 0.108, 0.06), 0.0, 0.92, None, 0.0, 1.0),          # dark umber hide
    "BH_Hair": ((0.022, 0.018, 0.018), 0.0, 0.9, None, 0.0, 1.0),          # rosettes, spots, tail rings
    "BH_Stone": ((0.34, 0.28, 0.2), 0.0, 0.9, None, 0.0, 1.0),             # pale throat / belly / muzzle
    "BH_Bone": ((0.66, 0.6, 0.48), 0.0, 0.45, None, 0.0, 1.0),             # fangs, claws
    "BH_Flesh": ((0.3, 0.08, 0.09), 0.0, 0.5, None, 0.0, 1.0),             # mouth, inner ears
    "BH_Shadow": ((0.02, 0.016, 0.016), 0.0, 0.5, None, 0.0, 1.0),          # nose, lips, pads
    "BH_Gold": ((0.72, 0.38, 0.18), 1.0, 0.35, None, 0.0, 1.0),            # copper wire coils
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),  # Zarael glows are white, eyes
}
GENERIC = ["idle", "idle_look", "walk", "run", "run_combat", "hit_light", "hit_heavy", "stagger_small", "knockback",
           "death", "death_back", "alert"]

# ------------------------------------------------------------------------------------------------ skeleton
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.25), None),
    "hips": ((0, 0.6, 0.86), (0, 0.3, 0.88), "root"),
    "spine": ((0, 0.3, 0.88), (0, -0.05, 0.89), "hips"),
    "chest": ((0, -0.05, 0.89), (0, -0.42, 0.885), "spine"),
    "neck": ((0, -0.42, 0.9), (0, -0.63, 1.0), "chest"),
    "head": ((0, -0.63, 1.0), (0, -0.93, 0.96), "neck"),
    "jaw": ((0, -0.7, 0.95), (0, -0.9, 0.93), "head"),
    "tail.1": ((0, 0.66, 0.86), (0, 0.88, 0.79), "hips"),
    "tail.2": ((0, 0.88, 0.79), (0, 1.08, 0.66), "tail.1"),
    "tail.3": ((0, 1.08, 0.66), (0, 1.26, 0.52), "tail.2"),
    "tail.4": ((0, 1.26, 0.52), (0, 1.46, 0.46), "tail.3"),
}
for _s, _x in (("L", 1.0), ("R", -1.0)):
    BONES.update({
        f"ear.{_s}": ((0.075 * _x, -0.68, 1.075), (0.09 * _x, -0.67, 1.14), "head"),
        f"scap.{_s}": ((0.11 * _x, -0.3, 0.9), (0.145 * _x, -0.38, 0.66), "chest"),
        f"upperarm.{_s}": ((0.145 * _x, -0.38, 0.66), (0.145 * _x, -0.28, 0.42), f"scap.{_s}"),
        f"forearm.{_s}": ((0.145 * _x, -0.28, 0.42), (0.145 * _x, -0.34, 0.12), f"upperarm.{_s}"),
        f"fpaw.{_s}": ((0.145 * _x, -0.34, 0.12), (0.145 * _x, -0.38, 0.035), f"forearm.{_s}"),
        f"ftoe.{_s}": ((0.145 * _x, -0.38, 0.035), (0.145 * _x, -0.47, 0.02), f"fpaw.{_s}"),
        f"thigh.{_s}": ((0.13 * _x, 0.5, 0.82), (0.14 * _x, 0.36, 0.52), "hips"),
        f"shin.{_s}": ((0.14 * _x, 0.36, 0.52), (0.14 * _x, 0.57, 0.24), f"thigh.{_s}"),
        f"hpaw.{_s}": ((0.14 * _x, 0.57, 0.24), (0.14 * _x, 0.53, 0.035), f"shin.{_s}"),
        f"htoe.{_s}": ((0.14 * _x, 0.53, 0.035), (0.14 * _x, 0.44, 0.02), f"hpaw.{_s}"),
    })


def lower(z):
    """Height warp applied to the authored skeleton and mesh: the body sits 0.12 m lower on shorter legs (a low,
    long-bodied cat); everything above the shoulder joint moves down rigidly, the legs are compressed."""
    z = np.asarray(z, float)
    return np.where(z >= 0.66, z - 0.12, np.where(z >= 0.12, 0.11 + (z - 0.12) * (0.43 / 0.54), z * 0.11 / 0.12))


H0 = {b: np.array(v[0], float) for b, v in BONES.items()}       # authored (unwarped) landmarks for the mesh code
T0 = {b: np.array(v[1], float) for b, v in BONES.items()}


def install_skeleton():
    """Point build_wolf's module-level skeleton tables at the cat (functions look them up at call time)."""
    W.BONES = BONES
    W.ORDER = list(BONES)
    W.H = {b: np.array([v[0][0], v[0][1], float(lower(v[0][2]))]) for b, v in BONES.items()}
    W.T = {b: np.array([v[1][0], v[1][1], float(lower(v[1][2]))]) for b, v in BONES.items()}
    W.PAR = {b: v[2] for b, v in BONES.items()}
    W.PIVOT = np.array([0.0, 0.1, float(lower(0.86))])
    W.R0 = W.rest_frames()
    W.NEUTRAL_BALL = {k: W.H[v[4]].copy() for k, v in W.LEGS.items()}
    W.REST_META_DIR = {k: (W.H[v[4]] - W.H[v[3]]) / np.linalg.norm(W.H[v[4]] - W.H[v[3]]) for k, v in W.LEGS.items()}
    W.REST_TOE_DIR = {k: (W.T[v[4]] - W.H[v[4]]) / np.linalg.norm(W.T[v[4]] - W.H[v[4]]) for k, v in W.LEGS.items()}


install_skeleton()
H, T = W.H, W.T


# ------------------------------------------------------------------------------------------------ clips
def clips():
    base = {c.name: c for c in W.clips()}
    out = []
    for n in GENERIC:
        c = copy.deepcopy(base[n])
        if n in ("walk", "run", "run_combat", "idle", "idle_look"):
            # cats carry the tail low with an upturned tip and the head low in motion
            c.layer(lambda f, cl: {"tail.lift": -6.0, "tail.curl": 14.0, "neck.pitch": -4.0})
        out.append(c)
    # cat_swipe: rear back onto the hind legs, the left forepaw rises and rakes forward-down across the target
    c = W.Clip("cat_swipe", 24, hits=[[9 / FPS, 13 / FPS]])
    c.key(0)
    c.key(6, body_fwd=-0.08, body_up=0.04, body_pitch=8, body_roll=-6, neck_pitch=6, head_yaw=10, jaw=18, ears=40,
          tail_lift=6, LF_up=0.36, LF_f=-0.02, LF_phi=60, RF_f=0.04, LH_f=0.08, RH_f=0.06, scap_L=-12)
    c.key(9, body_fwd=0.06, body_up=0.0, body_pitch=0, body_roll=4, neck_pitch=-8, head_yaw=-6, jaw=30, ears=45,
          tail_lift=0, LF_up=0.26, LF_f=0.34, LF_phi=10, RF_f=0.08, LH_f=0.02, RH_f=0.0, scap_L=-30)
    c.key(12, body_fwd=0.12, body_up=-0.04, body_pitch=-6, body_roll=8, body_yaw=-10, neck_pitch=-14, head_yaw=-12,
          jaw=22, LF_up=0.02, LF_f=0.42, LF_phi=-10, RF_f=0.1, LH_f=-0.04, RH_f=-0.04, scap_L=-26)
    c.key(16, body_fwd=0.08, body_up=-0.03, body_pitch=-3, body_roll=3, body_yaw=-6, neck_pitch=-8, head_yaw=-6, jaw=10,
          LF_up=0.0, LF_f=0.3, LF_phi=0, RF_f=0.08, LH_f=-0.02, RH_f=-0.02, scap_L=-16)
    c.key(24, body_fwd=0, body_up=0, body_pitch=0, body_roll=0, body_yaw=0, neck_pitch=0, head_yaw=0, jaw=0, ears=0,
          tail_lift=0, LF_up=0, LF_f=0, LF_phi=0, RF_f=0, LH_f=0, RH_f=0, scap_L=0)
    out.append(c)
    # cat_bite: crouch, lunge the head forward, jaws snap shut, worry the prey
    c = W.Clip("cat_bite", 24, hits=[[10 / FPS, 13 / FPS]])
    c.key(0).key(6, body_fwd=-0.1, body_up=-0.08, body_pitch=-4, neck_pitch=-8, head_pitch=-10, jaw=10, ears=40,
                 tail_lift=-4, LH_f=0.05, RH_f=0.05)
    c.key(9, body_fwd=0.24, body_up=-0.03, body_pitch=-6, neck_pitch=-24, head_pitch=-8, jaw=52, ears=45,
          LF_f=0.2, RF_f=0.14, LH_f=-0.02, RH_f=-0.02)
    c.key(11, body_fwd=0.34, body_up=-0.04, body_pitch=-7, neck_pitch=-28, head_pitch=-2, jaw=2, ears=45,
          LF_f=0.32, RF_f=0.26, LH_f=-0.05, RH_f=-0.05)
    c.key(14, body_fwd=0.3, neck_pitch=-22, head_pitch=4, head_yaw=12, head_roll=10, jaw=0, LF_f=0.32, RF_f=0.26)
    c.key(18, body_fwd=0.24, neck_pitch=-16, head_pitch=6, head_yaw=-14, head_roll=-12, jaw=4, LF_f=0.3, RF_f=0.24)
    c.key(24, body_fwd=0, body_up=0, body_pitch=0, neck_pitch=0, head_pitch=0, head_yaw=0, head_roll=0, jaw=0,
          ears=0, tail_lift=0, LF_f=0, RF_f=0, LH_f=0, RH_f=0)
    out.append(c)
    # cat_pounce: a low crouch with a tail twitch, the leap (forelegs reaching, jaws wide), the landing with both
    # forepaws driving down; the game moves the body forward (dash), the clip leaps in place
    c = W.Clip("cat_pounce", 42, hits=[[22 / FPS, 27 / FPS]])
    c.key(0)
    c.key(10, body_up=-0.2, body_fwd=-0.1, body_pitch=-5, neck_pitch=-20, head_pitch=-2, ears=45, jaw=8,
          tail_lift=-4, hips_pitch=8, LH_f=0.12, RH_f=0.12, LF_f=0.03, RF_f=0.03)
    c.key(15, body_up=0.32, body_fwd=0.18, body_pitch=16, neck_pitch=-6, head_pitch=-12, ears=50, jaw=44,
          tail_lift=12, hips_pitch=-10, LF_f=0.55, RF_f=0.5, LF_up=0.62, RF_up=0.6, LF_phi=45, RF_phi=45,
          LH_f=-0.34, RH_f=-0.34, LH_up=0.22, RH_up=0.22, LH_phi=60, RH_phi=60)
    c.key(20, body_up=0.34, body_fwd=0.42, body_pitch=-4, neck_pitch=-20, head_pitch=-4, jaw=54, tail_lift=16,
          LF_f=0.85, RF_f=0.8, LF_up=0.34, RF_up=0.36, LF_phi=-20, RF_phi=-20, LH_f=-0.22, RH_f=-0.2,
          LH_up=0.44, RH_up=0.44, LH_phi=50, RH_phi=50)
    c.key(24, body_up=-0.12, body_fwd=0.6, body_pitch=-12, neck_pitch=-30, head_pitch=6, jaw=0,
          LF_f=0.78, RF_f=0.76, LF_up=0.0, RF_up=0.0, LF_phi=0, RF_phi=0, LH_f=0.34, RH_f=0.32, LH_up=0.1,
          RH_up=0.1, LH_phi=10, RH_phi=10, hips_pitch=4)
    c.key(28, body_up=-0.14, body_fwd=0.6, body_pitch=-8, neck_pitch=-22, head_pitch=10, head_yaw=12, jaw=8,
          LF_f=0.78, RF_f=0.76, LH_f=0.42, RH_f=0.4, LH_up=0.0, RH_up=0.0, LH_phi=0, RH_phi=0)
    c.key(42, body_up=0, body_fwd=0, body_pitch=0, neck_pitch=0, head_pitch=0, head_yaw=0, jaw=0, ears=0,
          tail_lift=0, hips_pitch=0, LF_f=0, RF_f=0, LH_f=0, RH_f=0)
    c.layer(lambda f, cl: {"tail.yaw": 18 * math.sin(2 * math.pi * f / 8) if f < 10 else 0.0})
    out.append(c)
    # cat_roar: rear up a little on stiff forelegs, the head thrown forward and up, jaws wide, ears flat
    c = W.Clip("cat_roar", 54)
    c.key(0).key(10, body_up=0.03, body_pitch=8, body_fwd=-0.04, neck_pitch=14, head_pitch=-6, jaw=20, ears=55,
                 ears_out=20, tail_lift=10, LF_f=0.06, RF_f=0.06)
    c.key(18, body_up=0.04, body_pitch=10, body_fwd=0.04, neck_pitch=20, head_pitch=-14, jaw=58, ears=60,
          ears_out=24, tail_lift=16, LF_f=0.08, RF_f=0.08)
    c.key(40, body_up=0.04, body_pitch=10, body_fwd=0.04, neck_pitch=18, head_pitch=-12, jaw=54, ears=60,
          ears_out=24, tail_lift=14, LF_f=0.08, RF_f=0.08)
    c.key(54, body_up=0, body_pitch=0, body_fwd=0, neck_pitch=0, head_pitch=0, jaw=0, ears=0, ears_out=0,
          tail_lift=0, LF_f=0, RF_f=0)
    c.layer(lambda f, cl: {"head.yaw": 6 * math.sin(2 * math.pi * (f - 18) / 22) if 18 <= f <= 40 else 0.0,
                           "jaw": 3 * math.sin(2 * math.pi * f / 5) if 18 <= f <= 40 else 0.0,
                           "chest.pitch": 1.5 * math.sin(2 * math.pi * f / 4) if 18 <= f <= 40 else 0.0})
    out.append(c)
    return out


# ------------------------------------------------------------------------------------------------ mesh
def ring(y, zc, rx, rt, rb, n=18):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        s, co = math.sin(a), math.cos(a)
        pts.append((rx * co, y, zc + (rt if s > 0 else rb) * s))
    return np.array(pts)


def surf(rows, y, a, out=0.0):
    """Point + normal on a lofted ring body at length y and angle a (0 = +X side, pi/2 = top)."""
    ys = [r[0] for r in rows]
    order = np.argsort(ys)

    def prm(yy):
        return [float(np.interp(yy, [ys[i] for i in order], [r[k] for r in [rows[i] for i in order]])) for k in
                range(1, 5)]

    def pt(yy, aa):
        zc, rx, rt, rb = prm(yy)
        s, c = math.sin(aa), math.cos(aa)
        return np.array([rx * c, yy, zc + (rt if s > 0 else rb) * s])
    p = pt(y, a)
    e = 0.01
    du = pt(y, a + e) - pt(y, a - e)
    dv = pt(y + e, a) - pt(y - e, a)
    n = np.cross(dv, du)
    n /= max(np.linalg.norm(n), 1e-9)
    c = np.array([0, y, prm(y)[0]])
    if np.dot(n, p - c) < 0:
        n = -n
    return p + n * out, n


BODY = [(0.68, 0.84, 0.06, 0.05, 0.05), (0.6, 0.85, 0.135, 0.1, 0.15), (0.47, 0.86, 0.16, 0.11, 0.19),
        (0.32, 0.865, 0.15, 0.1, 0.19), (0.17, 0.87, 0.145, 0.095, 0.19), (0.02, 0.875, 0.15, 0.1, 0.21),
        (-0.14, 0.88, 0.165, 0.11, 0.26), (-0.3, 0.885, 0.175, 0.12, 0.29), (-0.42, 0.9, 0.16, 0.12, 0.25),
        (-0.5, 0.93, 0.13, 0.11, 0.17)]
NECK = [(-0.44, 0.93, 0.13, 0.12, 0.17), (-0.54, 0.97, 0.115, 0.105, 0.13), (-0.63, 1.0, 0.1, 0.09, 0.1)]
SKULL = [(-0.6, 1.03, 0.085, 0.06, 0.07), (-0.66, 1.04, 0.122, 0.07, 0.092), (-0.72, 1.035, 0.13, 0.064, 0.092),
         (-0.78, 1.02, 0.112, 0.05, 0.078), (-0.83, 1.0, 0.088, 0.04, 0.062), (-0.87, 0.99, 0.074, 0.034, 0.052),
         (-0.9, 0.986, 0.058, 0.028, 0.042), (-0.918, 0.982, 0.022, 0.015, 0.016)]
JAW = [(-0.72, 0.96, 0.075, 0.02, 0.03), (-0.8, 0.945, 0.062, 0.016, 0.026), (-0.86, 0.942, 0.045, 0.012, 0.02),
       (-0.89, 0.942, 0.022, 0.009, 0.012)]


def build_mesh(mats):
    import bh_mesh as M
    import kit_a_common as A
    import enemy_glyphbound_warrior as Z
    parts = []
    rng = np.random.default_rng(29)
    H, T = H0, T0

    def add(p, bone=None, bones=None, power=6.0, bias=None):
        p.V = np.asarray(p.V, float).copy()
        p.V[:, 2] = lower(p.V[:, 2])
        if bone:
            p.W = [{bone: 1.0}] * len(p.V)
        else:
            p.W = W.dist_weights(p.V, bones, power=power, bias=bias)
        parts.append(p)
        return p
    body_bones = ["hips", "spine", "chest", "neck", "scap.L", "scap.R", "thigh.L", "thigh.R", "tail.1"]
    body_bias = {"scap.L": 1.5, "scap.R": 1.5, "thigh.L": 1.35, "thigh.R": 1.35, "tail.1": 1.6, "neck": 1.2}
    # ---- body / neck / head
    V, F = M.loft([ring(*r, n=22) for r in BODY][::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Fur", name="body"), bones=body_bones, bias=body_bias)
    V, F = M.loft([ring(y, z - 0.012, rx * 0.7, 0.02, rb * 1.02, n=14) for (y, z, rx, rt, rb) in BODY[3:9]][::-1],
                  cap0=False, cap1=False)
    add(M.Part(V, F, "BH_Stone", name="belly"), bones=["spine", "chest", "scap.L", "scap.R"],
        bias={"scap.L": 1.5, "scap.R": 1.5})
    V, F = M.loft([ring(*r, n=18) for r in NECK][::-1], cap0=False, cap1=False)
    add(M.Part(V, F, "BH_Fur", name="neck"), bones=["chest", "neck", "head"], bias={"head": 1.3})
    V, F = M.loft([ring(y, z - 0.015, rx * 0.75, 0.02, rb * 1.03, n=12) for (y, z, rx, rt, rb) in NECK][::-1],
                  cap0=False, cap1=False)
    add(M.Part(V, F, "BH_Stone", name="throat"), bones=["chest", "neck", "head"], bias={"head": 1.3})
    V, F = M.loft([ring(*r, n=18) for r in SKULL][::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Fur", name="skull"), bone="head")
    V, F = M.loft([ring(y, z - 0.01, rx * 0.95, rt * 0.4, rb * 1.05, n=12) for (y, z, rx, rt, rb) in SKULL[4:7]][::-1],
                  cap0=False, cap1=False)
    add(M.Part(V, F, "BH_Stone", name="muzzle"), bone="head")
    for sx in (1, -1):        # whisker pads + cheek ruffs swept back
        V, F = M.sphere(0.03, 10, 6, center=(sx * 0.028, -0.885, 0.975), scale=(1.0, 0.8, 0.75))
        add(M.Part(V, F, "BH_Stone", name="pad"), bone="head")
        V, F = M.tube([(sx * 0.11, -0.74, 0.985), (sx * 0.135, -0.68, 0.97), (sx * 0.12, -0.63, 0.95)],
                      [(0.03, 0.04), (0.026, 0.035), (0.01, 0.012)], n=8, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Stone", name="ruff"), bone="head")
    V, F = M.loft([ring(*r, n=12) for r in JAW][::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Stone", name="jaw"), bone="jaw")
    V, F = M.loft([ring(y, z + 0.013, rx * 0.78, 0.006, 0.006, n=10) for (y, z, rx, rt, rb) in JAW[:3]][::-1])
    add(M.Part(V, F, "BH_Flesh", name="tongue"), bone="jaw")
    V, F = M.loft([ring(y, z - 0.034, rx * 0.95, 0.005, 0.006, n=12) for (y, z, rx, rt, rb) in SKULL[4:7]][::-1],
                  cap0=False, cap1=False)
    add(M.Part(V, F, "BH_Shadow", name="lips"), bone="head")
    V, F = M.prism(np.array([(-0.024, 0.0), (0.024, 0.0), (0.0, -0.022)]), 0.016, axis="z")
    add(M.Part(V, F, "BH_Shadow", name="nose").move((0, -0.915, 1.0)), bone="head")
    for sx in (1, -1):
        V, F = M.sphere(0.018, 8, 5, center=(sx * 0.05, -0.815, 1.036), scale=(1.35, 0.8, 0.75))
        add(M.Part(V, F, "BH_Emissive", name="eye").rot(W.Ry(-14 * sx), center=(sx * 0.05, -0.815, 1.036)),
            bone="head")
        V, F = M.sphere(0.028, 8, 5, center=(sx * 0.05, -0.8, 1.056), scale=(1.3, 1.1, 0.4))
        add(M.Part(V, F, "BH_Fur", name="brow"), bone="head")
        # fangs: long upper canines, small lower ones
        V, F = M.lathe([(0.0, -0.06), (0.008, -0.018), (0.01, 0.0), (0.0, 0.006)], 6)
        add(M.Part(V, F, "BH_Bone").move((sx * 0.03, -0.875, 0.965)), bone="head")
        V, F = M.lathe([(0.0, 0.0), (0.007, 0.004), (0.005, 0.026), (0.0, 0.032)], 5)
        add(M.Part(V, F, "BH_Bone").move((sx * 0.024, -0.86, 0.945)), bone="jaw")
    # ears: small, rounded, black backs with a pale spot
    for s, sx in (("L", 1), ("R", -1)):
        h = H["ear." + s]
        V, F = M.lathe([(0.0, 0.0), (0.04, 0.01), (0.036, 0.05), (0.0, 0.072)], 8)
        e = M.Part(V, F, "BH_Hair", name="ear").scale((1.0, 0.35, 1.0)).rot(W.Rz(-14 * sx)).move(h + (0, 0.0, -0.01))
        add(e, bone="ear." + s)
        V, F = M.sphere(0.022, 6, 4, center=h + (0, -0.012, 0.03), scale=(1, 0.35, 1.2))
        add(M.Part(V, F, "BH_Flesh", name="ear_in"), bone="ear." + s)
    # ---- legs
    def leg_tube(chain, radii, mat="BH_Fur"):
        pts = [H[chain[0]]] + [T[b] for b in chain]
        V, F = M.tube(pts, radii, n=12, up=(0, -1, 0))
        return M.Part(V, F, mat, name="leg")
    for s, sx in (("L", 1), ("R", -1)):
        p = leg_tube(["scap." + s, "upperarm." + s, "forearm." + s, "fpaw." + s],
                     [(0.11, 0.14), (0.108, 0.125), (0.08, 0.085), (0.058, 0.06), (0.052, 0.054)])
        add(p, bones=["scap." + s, "upperarm." + s, "forearm." + s, "fpaw." + s, "chest"], power=8, bias={"chest": 1.6})
        p = leg_tube(["thigh." + s, "shin." + s, "hpaw." + s],
                     [(0.14, 0.17), (0.105, 0.12), (0.062, 0.066), (0.05, 0.052)])
        p.V[:, 0] += 0.012 * sx
        add(p, bones=["hips", "thigh." + s, "shin." + s, "hpaw." + s], power=8, bias={"hips": 1.8})
        V, F = M.sphere(0.14, 14, 8, center=(0.085 * sx, 0.46, 0.74), scale=(0.72, 1.1, 1.2))
        add(M.Part(V, F, "BH_Fur", name="haunch"), bones=["hips", "thigh." + s], power=6, bias={"hips": 0.9})
        V, F = M.sphere(0.1, 12, 7, center=(0.12 * sx, -0.33, 0.74), scale=(0.7, 1.0, 1.3))
        add(M.Part(V, F, "BH_Fur", name="shoulder"), bones=["scap." + s, "upperarm." + s, "chest"], power=6,
            bias={"chest": 1.4})
        for toe, meta, r in (("ftoe." + s, "fpaw." + s, 0.07), ("htoe." + s, "hpaw." + s, 0.062)):
            c = H[toe]
            V, F = M.sphere(r, 12, 7, center=c + (0, -0.03, -0.002), scale=(1.0, 1.25, 0.6))
            add(M.Part(V, F, "BH_Fur", name="paw"), bone=toe)
            V, F = M.sphere(r * 0.8, 10, 5, center=c + (0, 0.02, 0.0), scale=(0.9, 1.0, 0.6))
            add(M.Part(V, F, "BH_Fur", name="heel"), bone=meta)
            for k in range(4):
                x = (k - 1.5) * 0.026
                V, F = M.tube([c + (x, -0.095, 0.01), c + (x, -0.112, -0.014)], [(0.007, 0.007), (0.001, 0.001)],
                              n=5, up=(0, 0, 1))
                add(M.Part(V, F, "BH_Bone", name="claw"), bone=toe)
    # ---- tail: long, thick, black rings toward the end, black tip
    pts = [H["tail.1"] + (0, -0.03, 0.01)] + [T["tail.%d" % i] for i in range(1, 5)]
    pts = [pts[0], pts[0] + (pts[1] - pts[0]) * 0.5] + pts[1:] + [T["tail.4"] + (T["tail.4"] - H["tail.4"]) * 0.25]
    pts = np.array(pts)
    radii = [(0.05, 0.05), (0.052, 0.052), (0.05, 0.05), (0.046, 0.046), (0.042, 0.042), (0.04, 0.04), (0.012, 0.012)]
    V, F = M.tube(pts, radii, n=10, up=(1, 0, 0))
    add(M.Part(V, F, "BH_Fur", name="tail"), bones=["hips", "tail.1", "tail.2", "tail.3", "tail.4"], power=8,
        bias={"hips": 2.0})
    seg = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    for u in (0.55, 0.68, 0.79, 0.88, 0.96):
        sv = u * seg[-1]
        j = min(int(np.searchsorted(seg, sv) - 1), len(pts) - 2)
        t = (sv - seg[j]) / (seg[j + 1] - seg[j])
        c = pts[j] * (1 - t) + pts[j + 1] * t
        d = np.asarray(pts[j + 1] - pts[j])
        d = d / np.linalg.norm(d)
        r = (radii[j][0] * (1 - t) + radii[j + 1][0] * t) + 0.004
        V, F = M.tube([c - d * 0.025, c + d * 0.025], [(r, r)] * 2, n=10, up=(1, 0, 0))
        add(M.Part(V, F, "BH_Hair", name="tailring"), bones=["tail.2", "tail.3", "tail.4"], power=8)
    # ---- rosettes and spots over the hide (dark discs lying on the surface)
    def disc(p, n, r, mat="BH_Hair"):
        V, F = M.lathe([(0.0, 0.0), (r, 0.0), (r * 0.9, 0.003), (0.0, 0.004)], 6)
        from bh_body import M_align_z
        Rm = M_align_z(n)
        prt = M.Part(np.asarray(V) @ Rm.T + p, F, mat, name="spot")
        return prt
    for i in range(64):
        y = -0.48 + 1.12 * rng.random()
        a = math.radians(-35 + 250 * rng.random())
        if abs(math.degrees(a) - 90) < 14:          # keep the spine line clear for the wire ridge
            continue
        c, n = surf(BODY, y, a, 0.0015)
        tng = np.cross(n, (0, 1, 0))
        tng /= max(np.linalg.norm(tng), 1e-9)
        bit = np.cross(n, tng)
        rr = 0.026 + 0.012 * rng.random()
        a0 = rng.random() * 6.28
        for k in range(3):
            arc = [c + (tng * math.cos(a0 + k * 2.1 + w) + bit * math.sin(a0 + k * 2.1 + w)) * rr * (1 + 0.15 * w)
                   for w in (0.0, 0.7, 1.4)]
            V, F = M.tube(np.array(arc), [(0.0025, 0.009), (0.0025, 0.012), (0.0025, 0.008)], n=4, up=tuple(n))
            add(M.Part(V, F, "BH_Hair", name="rosette"), bones=body_bones, bias=body_bias)
    for i in range(46):                              # solid spots on the neck, head top and legs
        k = i % 3
        if k == 0:
            y = -0.46 - 0.16 * rng.random()
            a = math.radians(-20 + 220 * rng.random())
            c, n = surf(NECK, y, a, 0.0015)
            add(disc(c, n, 0.012 + 0.006 * rng.random()), bones=["chest", "neck", "head"], bias={"head": 1.3})
        elif k == 1:
            s = "L" if i % 2 else "R"
            sx = 1 if s == "L" else -1
            ch = ["upperarm." + s, "forearm." + s] if i % 4 < 2 else ["thigh." + s, "shin." + s]
            b = ch[int(rng.random() * 2)]
            u = 0.15 + 0.6 * rng.random()
            q = H[b] + (T[b] - H[b]) * u
            rad = 0.07 if b.startswith(("thigh", "upperarm")) else 0.05
            ang = math.radians(-60 + 120 * rng.random())
            n = np.array([sx * math.cos(ang), math.sin(ang) * 0.6, 0.0])
            n /= np.linalg.norm(n)
            add(disc(q + n * rad, n, 0.011 + 0.004 * rng.random()), bone=b)
        else:
            y = -0.62 - 0.17 * rng.random()
            a = math.radians(25 + 130 * rng.random())
            c, n = surf(SKULL, y, a, 0.0015)
            add(disc(c, n, 0.008 + 0.004 * rng.random()), bone="head")
    # ---- the wire ridge: copper coils along the spine, glowing cores, a cable joining them, veins down the flanks
    ys = np.linspace(-0.44, 0.64, 11)
    prev = None
    for i, y in enumerate(ys):
        rows = NECK if y < -0.44 else BODY
        top, n = surf(rows, y, math.pi / 2, 0.0)
        c = top + np.array([0, 0, 0.032])
        L = 0.075 - 0.012 * abs(i - 5) / 5
        a, b = c - np.array([0, L / 2, 0]), c + np.array([0, L / 2, 0])
        bones = ["chest", "spine", "hips", "neck"]
        c = c + np.array([0, 0, 0.008])
        a, b = c - np.array([0, L / 2, 0]), c + np.array([0, L / 2, 0])
        add(Z.coil(a, b, 0.042 - 0.01 * abs(i - 5) / 5, 4, 0.0075, "BH_Gold", n=4, pts_per_turn=8), bones=bones,
            power=8)
        V, F = M.tube([a, b], [(0.032, 0.032)] * 2, n=8, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Emissive", name="core"), bones=bones, power=8)
        if prev is not None:
            V, F = M.tube([prev + np.array([0, 0, -0.022]), (prev + c) / 2 + np.array([0, 0, -0.026]),
                           c + np.array([0, 0, -0.022])], [(0.01, 0.01)] * 3, n=5, up=(0, 0, 1))
            add(M.Part(V, F, "BH_Gold", name="cable"), bones=bones, power=8)
        prev = c
        if i % 2 == 0 and 0 < i < 10:
            for sx in (1, -1):
                pts = []
                for k in range(5):
                    t = k / 4
                    yy = y + 0.05 * math.sin(t * 4 + i) * t
                    aa = math.pi / 2 - sx * (0.25 + 1.0 * t)
                    p_, _ = surf(BODY, yy, aa, 0.002)
                    pts.append(p_)
                add(A.tube(pts, [0.008, 0.007, 0.006, 0.004, 0.002], "BH_Emissive", n=4), bones=body_bones,
                    bias=body_bias)
    # wire continues a little way down the tail
    tp = [H["tail.1"] + (T["tail.1"] - H["tail.1"]) * u + np.array([0, 0, 0.05]) for u in (0.15, 0.55)]
    for c in tp:
        add(Z.coil(c - np.array([0, 0.03, 0.005]), c + np.array([0, 0.03, -0.012]), 0.03, 3, 0.006, "BH_Gold", n=4,
                   pts_per_turn=8), bones=["tail.1", "tail.2", "hips"], power=8)
        V, F = M.tube([c - np.array([0, 0.03, 0.005]), c + np.array([0, 0.03, -0.012])], [(0.022, 0.022)] * 2, n=8,
                      up=(0, 0, 1))
        add(M.Part(V, F, "BH_Emissive", name="core"), bones=["tail.1", "tail.2", "hips"], power=8)
    return parts


# ------------------------------------------------------------------------------------------------ build / export
def build_all():
    import bpy
    import bh_mesh as M
    import bh_materials as MT
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    mats = MT.make_materials(NAME, vertex_color=False, extra=PALETTE)
    arm = W.build_armature()
    parts = build_mesh(mats)
    mesh = M.build_skinned(NAME, parts, arm, mats, sharp_angle=45)
    MT.bake_vertex_ao(mesh, rays=16, dist=0.25, strength=0.6)
    acts = {}
    for c in clips():
        acts[c.name] = (c, W.bake(arm, c))
    return arm, mesh, acts


def merge_meta(acts, path, tris, bones):
    """Merge ONLY this model's keys: animations.cat_* and models.wireback_stalker. Re-read right before writing
    (other builders merge into the same file), keep every other key, write, re-read and verify."""
    mine, clips_all = {}, {}
    for name, (c, act) in acts.items():
        d = {"length": round(c.frames / FPS, 3), "loop": bool(c.loop)}
        if "hits" in c.meta:
            d["hits"] = [[round(a, 3), round(b, 3)] for a, b in c.meta["hits"]]
        if "ground_speed" in c.meta:
            d["ground_speed"] = c.meta["ground_speed"]
        clips_all[name] = d
        if name.startswith("cat_"):
            mine[name] = d
    model = {"generator": "tools/blender/creatures/build_wireback_stalker.py",
             "glb": "res://assets/characters/%s.glb" % NAME, "clips": clips_all, "tris": tris, "bones": bones}
    with open(path) as fh:
        data = json.load(fh)
    before_a = {k: v for k, v in data.get("animations", {}).items() if not k.startswith("cat_")}
    before_m = {k: v for k, v in data.get("models", {}).items() if k != NAME}
    data.setdefault("animations", {}).update(mine)
    data.setdefault("models", {})[NAME] = model
    with open(path, "w") as fh:
        json.dump(data, fh, indent=1)
    with open(path) as fh:
        chk = json.load(fh)
    ok = (all(chk["animations"].get(k) == v for k, v in mine.items()) and chk["models"].get(NAME) == model
          and all(chk["animations"].get(k) == v for k, v in before_a.items())
          and all(chk["models"].get(k) == v for k, v in before_m.items()))
    print(f"[{NAME}] meta merged {sorted(mine)} + models.{NAME} -> {path} (verified: {ok})")
    if not ok:
        raise RuntimeError("creature_meta merge verification failed")


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
    bad, got = GX.check_lengths(OUT_GLB, {n: c.frames / FPS for n, (c, a) in acts.items()})
    print(f"[{NAME}] -> {OUT_GLB} ({os.path.getsize(OUT_GLB) / 1e6:.1f} MB), {len(got)} animations, "
          f"length mismatches: {bad}")
    if bad:
        raise RuntimeError("clip length mismatch")


def evidence(arm, mesh, acts, out, scratch):
    """<out>/wireback_stalker_rest_iso.png and _clips.png (Workbench, kit_b_evidence helpers)."""
    import bpy
    import kit_b_evidence as KB
    tiles = os.path.join(scratch, NAME)
    os.makedirs(tiles, exist_ok=True)
    KB.material_colors()
    cam = KB.setup(360)
    lo, hi = KB.mesh_bounds(mesh)
    print(f"[{NAME}] rest bounds min {np.round(lo, 3)} max {np.round(hi, 3)}")
    paths, labels = [], []
    KB.set_action(arm, acts["idle"][1], 0)
    for yaw in (90, 35, 0, 200):
        KB.place(cam, (0, 0.15, 0.6), 4.4, yaw, 10)
        paths.append(KB.render(os.path.join(tiles, f"rest_{yaw}.png")))
        labels.append(f"idle f0 yaw {yaw}")
    KB.place(cam, (0, -0.75, 0.98), 1.2, 30, 8)
    paths.append(KB.render(os.path.join(tiles, "closeup.png")))
    labels.append("close-up (head)")
    KB.place(cam, (0, 0.1, 0.95), 2.2, 160, 45)
    paths.append(KB.render(os.path.join(tiles, "back.png")))
    labels.append("wire ridge from above-behind")
    for dist, yaw in ((16, 0), (22, 60)):
        KB.place(cam, (0, 0, 0.6), dist, 0, 54, fov=40)
        arm.rotation_euler.z = math.radians(yaw)
        p = KB.render(os.path.join(tiles, f"game_{dist}_{yaw}.png"), res=1080)
        KB.crop_center(p, 360)
        paths.append(p)
        labels.append(f"game cam {dist} m 54deg, facing {yaw} (1:1 px @1080p)")
    arm.rotation_euler.z = 0
    bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = 360
    KB.compose(paths, labels, os.path.join(out, f"{NAME}_rest_iso.png"), 4,
               f"{NAME}: rest / close-ups / gameplay camera (top {hi[2]:.2f} m, length {hi[1] - lo[1]:.2f} m)",
               cell=360)
    paths, labels = [], []
    for cn in ("walk", "run", "cat_swipe", "cat_bite", "cat_pounce", "cat_roar", "hit_heavy", "death"):
        c, act = acts[cn]
        for fr in (0.0, 0.25, 0.4, 0.55, 0.75, 1.0):
            f = int(round(fr * c.frames))
            KB.set_action(arm, act, f)
            KB.place(cam, (0, 0.0, 0.6), 4.6, 60, 12)
            paths.append(KB.render(os.path.join(tiles, f"{cn}_{f}.png")))
            labels.append(f"{cn} f{f}/{c.frames}")
    KB.compose(paths, labels, os.path.join(out, f"{NAME}_clips.png"), 6, f"{NAME}: clips (3/4 view)", cell=300)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--evidence", default="")
    ap.add_argument("--scratch", default=os.path.join(ROOT_DIR, "work", "lemondev", "bh-029", "scratch", "m1", "ev"))
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    import bh_mesh as M
    arm, mesh, acts = build_all()
    tris = M.tri_count(mesh)
    print(f"[{NAME}] mesh {tris} tris, {len(acts)} clips, {len(arm.data.bones)} bones")
    if a.evidence:
        evidence(arm, mesh, acts, a.evidence, a.scratch)
    if not a.no_export:
        export(arm, mesh, acts)
        merge_meta(acts, OUT_META, tris, len(arm.data.bones))


if __name__ == "__main__":
    main()
