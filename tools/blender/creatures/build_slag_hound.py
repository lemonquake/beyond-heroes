"""Slag Hound (Builder C, bh-012, Emberforge Depths): a lean hound (~0.95 m at the shoulder) of cooled slag and
basalt plates with molten seams glowing between them (a glowing core body under the plate crust), a mane of jagged
obsidian spikes, a glowing open maw, ember eyes and a long whip tail with a spiked tip.

Rig / gaits / clip machinery: reused from build_wolf.py by import (not edited): same skeleton, same channel set.

  blender -b --factory-startup --python build_slag_hound.py -- [--no-export] [--evidence DIR]

Clips (30 fps, in place): the generic set (idle idle_look walk run run_combat hit_light hit_heavy stagger_small
knockback death death_back alert) + hound_bite, hound_lunge (pounce), hound_breath (plants and breathes fire forward).
creature_meta.json: only the hound_* keys are merged into "animations" (the generic keys are the wolf's, same rig).
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
OUT_GLB = os.path.join(ROOT_DIR, "game", "assets", "characters", "slag_hound.glb")
OUT_META = os.path.join(ROOT_DIR, "game", "assets", "characters", "creature_meta.json")

import numpy as np  # noqa: E402

import build_wolf as W  # noqa: E402

NAME = "slag_hound"
FPS = W.FPS
PALETTE = {
    "BH_Stone": ((0.075, 0.068, 0.066), 0.0, 0.9, None, 0.0, 1.0),        # cooled slag / basalt plates
    "BH_Fur": ((0.05, 0.045, 0.044), 0.0, 0.92, None, 0.0, 1.0),          # dark slag skin (legs, head)
    "BH_Horn": ((0.03, 0.026, 0.04), 0.3, 0.12, None, 0.0, 1.0),          # obsidian spikes, claws
    "BH_Bone": ((0.05, 0.04, 0.045), 0.3, 0.2, None, 0.0, 1.0),           # obsidian teeth
    "BH_Shadow": ((0.02, 0.015, 0.012), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Emissive": ((1.0, 0.45, 0.1), 0.0, 0.35, (1.0, 0.45, 0.1), 10.0, 1.0),  # molten core, seams, eyes, maw
}
GENERIC = ["idle", "idle_look", "walk", "run", "run_combat", "hit_light", "hit_heavy", "stagger_small", "knockback",
           "death", "death_back", "alert"]
H, T = W.H, W.T


def clips():
    base = {c.name: c for c in W.clips()}
    out = [base[n] for n in GENERIC]
    b = copy.deepcopy(base["wolf_bite"])
    b.name = "hound_bite"
    out.append(b)
    p = copy.deepcopy(base["wolf_pounce"])
    p.name = "hound_lunge"
    out.append(p)
    # hound_breath: plant, draw back with the maw opening, then a 0.8 s fire breath forward with a small head sweep
    c = W.Clip("hound_breath", 42, hits=[[13 / FPS, 37 / FPS]])
    c.key(0)
    c.key(8, body_fwd=-0.06, body_up=-0.03, body_pitch=4, neck_pitch=14, head_pitch=10, jaw=18, ears=-10,
          tail_lift=10, LF_f=0.08, RF_f=0.02, LH_f=-0.04, RH_f=-0.06)
    c.key(13, body_fwd=0.06, body_up=-0.08, body_pitch=-6, neck_pitch=-14, head_pitch=4, jaw=46, ears=30,
          tail_lift=-4, LF_f=0.14, RF_f=0.1, LH_f=-0.02, RH_f=-0.04, hips_pitch=4)
    c.key(25, body_fwd=0.07, body_up=-0.09, body_pitch=-7, neck_pitch=-16, head_pitch=2, jaw=48, ears=35,
          tail_lift=-6, LF_f=0.14, RF_f=0.1, LH_f=-0.02, RH_f=-0.04, hips_pitch=4)
    c.key(37, body_fwd=0.06, body_up=-0.08, body_pitch=-6, neck_pitch=-14, head_pitch=4, jaw=44, ears=30,
          tail_lift=-4, LF_f=0.14, RF_f=0.1, LH_f=-0.02, RH_f=-0.04, hips_pitch=4)
    c.key(42, body_fwd=0, body_up=0, body_pitch=0, neck_pitch=0, head_pitch=0, jaw=0, ears=0, tail_lift=0,
          LF_f=0, RF_f=0, LH_f=0, RH_f=0, hips_pitch=0)
    c.layer(lambda f, cl: {"head.yaw": 9 * math.sin(2 * math.pi * (f - 13) / 24) if 13 <= f <= 37 else 0.0,
                           "neck.yaw": 5 * math.sin(2 * math.pi * (f - 13) / 24) if 13 <= f <= 37 else 0.0,
                           "chest.pitch": 1.5 * math.sin(2 * math.pi * f / 6) if 13 <= f <= 37 else 0.0})
    out.append(c)
    return out


# ------------------------------------------------------------------------------------------------ mesh
def _frame(n):
    n = n / np.linalg.norm(n)
    a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(n, a)
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    return np.stack([u, v, n], 1)


def build_mesh(mats):
    import bh_mesh as M
    parts = []
    rng = np.random.default_rng(33)

    def add(p, bone=None, bones=None, power=6.0, bias=None):
        if bone:
            p.W = [{bone: 1.0}] * len(p.V)
        else:
            p.W = W.dist_weights(p.V, bones, power=power, bias=bias)
        parts.append(p)
        return p

    def ring(y, zc, rx, rt, rb, n=18):
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            s, co = math.sin(a), math.cos(a)
            pts.append((rx * co, y, zc + (rt if s > 0 else rb) * s))
        return np.array(pts)

    def plate(c, nrm, w, l, t, along, mat="BH_Stone"):
        """Slag plate centred on a surface point: w across, l along `along`, thickness t outward."""
        V, F = M.box(w, l, t)
        p = M.Part(V, F, mat, name="plate")
        p.V[:, 2] += t * 0.3
        p.V += rng.normal(size=p.V.shape) * t * 0.18
        nz = nrm / np.linalg.norm(nrm)
        ay = along - nz * (along @ nz)
        ay /= np.linalg.norm(ay)
        ax = np.cross(ay, nz)
        R = np.stack([ax, ay, nz], 1)
        p.rot(R).move(c)
        return p

    BODYB = ["hips", "spine", "chest", "neck", "scap.L", "scap.R", "thigh.L", "thigh.R", "tail.1"]
    BIAS = {"scap.L": 1.5, "scap.R": 1.5, "thigh.L": 1.35, "thigh.R": 1.35, "tail.1": 1.6, "neck": 1.2}
    # ---- lean body: glowing molten core (visible in the seams between the slag plates)
    BODY = [(0.58, 0.8, 0.045, 0.045, 0.045), (0.5, 0.81, 0.085, 0.07, 0.085), (0.4, 0.815, 0.105, 0.075, 0.1),
            (0.28, 0.83, 0.1, 0.07, 0.09), (0.15, 0.85, 0.085, 0.07, 0.075), (0.02, 0.855, 0.095, 0.08, 0.13),
            (-0.12, 0.85, 0.115, 0.095, 0.2), (-0.26, 0.85, 0.12, 0.105, 0.21), (-0.36, 0.87, 0.11, 0.105, 0.17),
            (-0.43, 0.9, 0.095, 0.1, 0.12)]
    rings = [ring(y, z, rx * 1.1, rt, rb, n=18) for (y, z, rx, rt, rb) in BODY]
    V, F = M.loft(rings[::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Emissive", name="core"), bones=BODYB, bias=BIAS)
    # plates: rows along the body, around the top / sides (belly left mostly as dark slag strips)
    for i in range(1, len(BODY) - 1):
        y, z, rx, rt, rb = BODY[i]
        dy = abs(BODY[i + 1][0] - BODY[i - 1][0]) / 2
        for a in np.linspace(-180, 180, 10 if rx > 0.1 else 9, endpoint=False):
            ar = math.radians(a + 90)          # 90 = top
            s, co = math.sin(ar), math.cos(ar)
            r_ = rt if s > 0 else rb
            c = np.array([rx * 1.1 * co, y, z + r_ * s])
            n = np.array([co / (rx * 1.1), 0, s / r_])
            n /= np.linalg.norm(n)
            w = 2 * math.pi * rx * 1.1 / 8 * 0.95
            p = plate(c + n * 0.004, n, w, dy * 0.92, 0.035 if s > -0.3 else 0.02, np.array([0, 1.0, 0]),
                      "BH_Stone" if s > -0.6 else "BH_Fur")
            add(p, bones=BODYB, bias=BIAS)
    # ---- neck + head (dark slag, plated brow and cheeks)
    NECK = [(-0.34, 0.9, 0.1, 0.11, 0.14), (-0.44, 0.96, 0.09, 0.09, 0.12), (-0.52, 1.02, 0.078, 0.075, 0.09),
            (-0.56, 1.05, 0.07, 0.065, 0.075)]
    V, F = M.loft([ring(*r, n=14) for r in NECK][::-1], cap0=False, cap1=False)
    add(M.Part(V, F, "BH_Emissive", name="neck"), bones=["chest", "neck", "head"], bias={"head": 1.3})
    for (y, z, rx, rt, rb) in NECK[:3]:
        for a in np.linspace(-180, 180, 7, endpoint=False):
            ar = math.radians(a + 90)
            s, co = math.sin(ar), math.cos(ar)
            r_ = rt if s > 0 else rb
            c = np.array([rx * co, y, z + r_ * s])
            n = np.array([co / rx, 0.25, s / r_])
            add(plate(c, n, 0.06, 0.08, 0.028, np.array([0, 1.0, 0.6])), bones=["chest", "neck", "head"],
                bias={"head": 1.3})
    SKULL = [(-0.48, 1.06, 0.058, 0.058, 0.05), (-0.54, 1.075, 0.075, 0.07, 0.065), (-0.6, 1.068, 0.078, 0.066, 0.066),
             (-0.65, 1.052, 0.058, 0.052, 0.052), (-0.7, 1.03, 0.042, 0.038, 0.034),
             (-0.76, 1.015, 0.036, 0.033, 0.026), (-0.81, 1.008, 0.028, 0.026, 0.018), (-0.84, 1.0, 0.014, 0.012, 0.01)]
    V, F = M.loft([ring(*r, n=14) for r in SKULL][::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Fur", name="skull"), bone="head")
    # brow plates (angry ridge) + cheek plates
    for sx in (1, -1):
        add(plate(np.array([sx * 0.045, -0.63, 1.095]), np.array([sx * 0.4, -0.3, 1]), 0.055, 0.09, 0.022,
                  np.array([0, -1.0, 0.2])), bone="head")
        add(plate(np.array([sx * 0.07, -0.56, 1.05]), np.array([sx, 0, 0.2]), 0.07, 0.08, 0.02,
                  np.array([0, -1.0, 0])), bone="head")
        # ember eyes
        V, F = M.sphere(0.014, 8, 5, center=(sx * 0.047, -0.652, 1.078), scale=(0.9, 1.3, 0.7))
        add(M.Part(V, F, "BH_Emissive", name="eye"), bone="head")
    add(plate(np.array([0, -0.72, 1.052]), np.array([0, -0.2, 1]), 0.05, 0.12, 0.018, np.array([0, -1.0, -0.3])),
        bone="head")
    # glowing maw: jaw (dark), glowing tongue / throat, obsidian fangs
    JAW = [(-0.58, 0.985, 0.048, 0.02, 0.03), (-0.66, 0.975, 0.038, 0.016, 0.026), (-0.74, 0.968, 0.029, 0.013, 0.02),
           (-0.8, 0.964, 0.019, 0.01, 0.014)]
    V, F = M.loft([ring(*r, n=12) for r in JAW][::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Fur", name="jaw"), bone="jaw")
    V, F = M.loft([ring(y, z + 0.013, rx * 0.8, 0.007, 0.006, n=10) for (y, z, rx, rt, rb) in JAW[:3]][::-1])
    add(M.Part(V, F, "BH_Emissive", name="tongue"), bone="jaw")
    V, F = M.loft([ring(y, z - 0.024, rx * 0.8, 0.008, 0.01, n=12) for (y, z, rx, rt, rb) in SKULL[2:6]][::-1])
    add(M.Part(V, F, "BH_Emissive", name="palate"), bone="head")
    V, F = M.sphere(0.04, 10, 6, center=(0, -0.57, 1.0), scale=(1.0, 0.7, 0.8))
    add(M.Part(V, F, "BH_Emissive", name="throat"), bone="head")
    for sx in (1, -1):
        for y, Lh in ((-0.79, 0.04), (-0.74, 0.03), (-0.69, 0.024)):
            V, F = M.lathe([(0.0, -Lh), (0.006, -Lh * 0.3), (0.007, 0.0), (0.0, 0.004)], 4)
            add(M.Part(V, F, "BH_Bone").move((sx * 0.024, y, 0.99)), bone="head")
        for y in (-0.775, -0.72):
            V, F = M.lathe([(0.0, 0.0), (0.006, 0.003), (0.005, 0.024), (0.0, 0.03)], 4)
            add(M.Part(V, F, "BH_Bone").move((sx * 0.02, y, 0.972)), bone="jaw")
    V, F = M.sphere(0.02, 8, 5, center=(0, -0.835, 1.012), scale=(1.1, 0.8, 0.8))
    add(M.Part(V, F, "BH_Shadow", name="nose"), bone="head")
    # ears: short swept-back obsidian blades
    for s, sx in (("L", 1), ("R", -1)):
        h = H["ear." + s]
        add(_shard(M, h + (0, 0.01, -0.01), np.array([sx * 0.3, 0.6, 0.75]), 0.11, 0.022, "BH_Horn", 3), bone="ear." + s)

    # ---- legs: dark slag tubes with a few plates and glowing seams, obsidian claws
    def leg_tube(chain, radii, mat="BH_Fur"):
        pts = [H[chain[0]]] + [T[b] for b in chain]
        V, F = M.tube(pts, radii, n=10, up=(0, -1, 0))
        return M.Part(V, F, mat, name="leg")
    for s, sx in (("L", 1), ("R", -1)):
        fr = ["scap." + s, "upperarm." + s, "forearm." + s, "fpaw." + s]
        add(leg_tube(fr, [(0.075, 0.1), (0.068, 0.082), (0.048, 0.054), (0.032, 0.036), (0.027, 0.03)]),
            bones=fr + ["chest"], power=8, bias={"chest": 1.6})
        hi = ["thigh." + s, "shin." + s, "hpaw." + s]
        p = leg_tube(hi, [(0.1, 0.125), (0.072, 0.085), (0.04, 0.045), (0.027, 0.03)])
        p.V[:, 0] += 0.01 * sx
        add(p, bones=["hips"] + hi, power=8, bias={"hips": 1.8})
        V, F = M.sphere(0.105, 12, 7, center=(0.075 * sx, 0.38, 0.72), scale=(0.75, 1.1, 1.25))
        add(M.Part(V, F, "BH_Stone", name="haunch"), bones=["hips", "thigh." + s], power=6, bias={"hips": 0.9})
        # plates on shoulder and haunch, seams down the legs
        for bone_, c, n in (("upperarm." + s, (H["upperarm." + s] + T["upperarm." + s]) / 2, (sx, -0.2, 0.1)),
                            ("forearm." + s, (H["forearm." + s] * 0.6 + T["forearm." + s] * 0.4), (sx, -0.5, 0)),
                            ("shin." + s, (H["shin." + s] + T["shin." + s]) / 2, (sx, 0.4, 0)),
                            ("thigh." + s, (H["thigh." + s] * 0.4 + T["thigh." + s] * 0.6), (sx, 0.1, 0.1))):
            n = np.array(n, float)
            add(plate(np.asarray(c) + n / np.linalg.norm(n) * 0.055, n, 0.07, 0.12, 0.022,
                      T[bone_] - H[bone_]), bone=bone_)
        for chain in (fr[1:3], hi[:2]):
            for b in chain:
                a_, t_ = H[b], T[b]
                d = t_ - a_
                side = np.array([sx * 1.0, -0.3, 0.0])
                side /= np.linalg.norm(side)
                r0 = 0.06 if "thigh" in b or "upper" in b else 0.045
                pts = [a_ + d * u + side * r0 * (1.0 - 0.3 * u) + np.array([0, 0.01 * math.sin(9 * u), 0])
                       for u in np.linspace(0.15, 0.85, 4)]
                V, F = M.tube(pts, [(0.006, 0.006)] * 4, n=4, up=(0, 0, 1))
                add(M.Part(V, F, "BH_Emissive", name="seam"), bone=b)
        for toe, meta in (("ftoe." + s, "fpaw." + s), ("htoe." + s, "hpaw." + s)):
            c = H[toe]
            V, F = M.sphere(0.042, 10, 6, center=c + (0, -0.03, -0.005), scale=(0.95, 1.3, 0.55))
            add(M.Part(V, F, "BH_Fur", name="paw"), bone=toe)
            V, F = M.sphere(0.034, 8, 5, center=c + (0, 0.015, 0.0), scale=(0.9, 1.0, 0.6))
            add(M.Part(V, F, "BH_Fur", name="heel"), bone=meta)
            for k in range(4):
                x = (k - 1.5) * 0.019
                V, F = M.tube([c + (x, -0.075, 0.006), c + (x, -0.104, -0.014)], [(0.007, 0.007), (0.001, 0.001)],
                              n=4, up=(0, 0, 1))
                add(M.Part(V, F, "BH_Horn", name="claw"), bone=toe)

    # ---- whip tail: thin, long, glowing seam along the top, spiked obsidian tip
    pts = [H["tail.1"] + (0, -0.03, 0.01)] + [T["tail.%d" % i] for i in range(1, 5)]
    ext = T["tail.4"] + (T["tail.4"] - H["tail.4"]) * 1.6
    pts = pts + [ext]
    V, F = M.tube(pts, [(0.03, 0.034), (0.025, 0.028), (0.02, 0.022), (0.016, 0.018), (0.012, 0.013),
                        (0.007, 0.008)], n=10, up=(1, 0, 0))
    add(M.Part(V, F, "BH_Fur", name="tail"), bones=["hips", "tail.1", "tail.2", "tail.3", "tail.4"], power=8,
        bias={"hips": 2.0})
    top = [np.asarray(p) + (0, 0, r) for p, r in zip(pts[1:5], (0.026, 0.021, 0.017, 0.012))]
    V, F = M.tube(top, [(0.006, 0.006)] * 4, n=4, up=(1, 0, 0))
    add(M.Part(V, F, "BH_Emissive", name="tailseam"), bones=["tail.1", "tail.2", "tail.3", "tail.4"], power=8)
    tipdir = ext - T["tail.4"]
    for k, (d, ln) in enumerate(((tipdir, 0.13), (tipdir + np.array([0.12, 0, 0.1]), 0.07),
                                 (tipdir + np.array([-0.12, 0, 0.1]), 0.07))):
        add(_shard(M, ext - tipdir * 0.2, d, ln, 0.018, "BH_Horn", 3 + k), bone="tail.4")

    # ---- obsidian mane: jagged spikes along the neck crest, withers and spine
    for i in range(22):
        t = i / 21
        y = -0.56 + 0.52 * t
        if y < -0.34:
            u = (y + 0.56) / 0.22
            zc = 1.07 - 0.15 * u
            base_r = 0.07 + 0.03 * u
        else:
            zc = 0.965 - 0.03 * (y + 0.34) / 0.3
            base_r = 0.0
        side = (-1) ** i * (0.02 + 0.03 * rng.random())
        base = np.array([side, y, zc + base_r * 0.2])
        d = np.array([side * 3.0, 0.8 + 0.4 * rng.random(), 1.0])
        ln = 0.2 * (1 - abs(t - 0.35) * 1.1) + 0.05 + 0.04 * rng.random()
        bones = ["neck", "chest", "head"] if y < -0.34 else ["chest", "spine"]
        add(_shard(M, base, d, ln, 0.028, "BH_Horn", 10 + i), bones=bones, power=6, bias={"head": 1.4})
    for i in range(7):                       # smaller spikes along the spine to the rump
        y = -0.02 + 0.075 * i
        base = np.array([0.0, y, 0.92 - 0.015 * i])
        add(_shard(M, base, np.array([0, 0.9, 1.0]), 0.08 - 0.006 * i, 0.02, "BH_Horn", 40 + i),
            bones=["hips", "spine", "chest"], power=6)
    return parts


def _shard(M, base, direction, length, width, mat, seed):
    d = np.asarray(direction, float)
    d /= np.linalg.norm(d)
    up = (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)
    b = np.asarray(base, float)
    V, F = M.tube([b - d * width * 0.5, b + d * length * 0.5, b + d * length],
                  [(width, width * 0.7, 1.3), (width * 0.7, width * 0.5, 1.3), (0.001, 0.001, 1.3)], n=4, up=up,
                  twist=[0.0, 0.2 + 0.1 * (seed % 3), 0.0])
    return M.Part(V, F, mat, name="shard")


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
    mesh = M.build_skinned(NAME, parts, arm, mats, sharp_angle=40)
    MT.bake_vertex_ao(mesh, rays=16, dist=0.25, strength=0.6)
    acts = {}
    for c in clips():
        acts[c.name] = (c, W.bake(arm, c))
    return arm, mesh, acts


def merge_meta(acts, path):
    """Merge ONLY the hound_* clip keys into creature_meta.json["animations"] (re-read right before writing)."""
    mine = {}
    for name, (c, act) in acts.items():
        if not name.startswith("hound_"):
            continue
        d = {"length": round(c.frames / FPS, 3), "loop": bool(c.loop)}
        if "hits" in c.meta:
            d["hits"] = [[round(a, 3), round(b, 3)] for a, b in c.meta["hits"]]
        mine[name] = d
    with open(path) as fh:
        data = json.load(fh)
    before = {k: v for k, v in data.get("animations", {}).items() if not k.startswith("hound_")}
    data.setdefault("animations", {}).update(mine)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=1)
    with open(path) as fh:
        chk = json.load(fh)
    assert all(chk["animations"][k] == v for k, v in mine.items()), "hound keys not written"
    assert all(chk["animations"][k] == v for k, v in before.items()), "other keys changed"
    print(f"[{NAME}] merged {sorted(mine)} into {path}")
    return mine


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


def evidence(arm, mesh, acts, out):
    """<out>/slag_hound_rest_iso.png and slag_hound_clips.png (Workbench, kit_b_evidence helpers)."""
    import bpy
    import kit_b_evidence as KB
    tiles = os.path.join(os.environ.get("BH_SCRATCH", out), NAME)
    os.makedirs(tiles, exist_ok=True)
    KB.material_colors()
    cam = KB.setup(360)
    lo, hi = KB.mesh_bounds(mesh)
    print(f"[{NAME}] rest bounds min {np.round(lo, 3)} max {np.round(hi, 3)}")
    paths, labels = [], []
    for yaw in (90, 35, 0, 200):
        KB.place(cam, (0, -0.1, 0.55), 3.4, yaw, 10)
        paths.append(KB.render(os.path.join(tiles, f"rest_{yaw}.png")))
        labels.append(f"rest yaw {yaw}")
    KB.set_action(arm, acts["idle"][1], 0)
    KB.place(cam, (0, -0.5, 0.9), 1.3, 30, 6)
    paths.append(KB.render(os.path.join(tiles, "closeup.png")))
    labels.append("idle close-up (head / maw)")
    for dist, yaw in ((16, 0), (16, 150), (24, 60)):
        KB.place(cam, (0, 0, 0.6), dist, 0, 54, fov=40)
        arm.rotation_euler.z = math.radians(yaw)
        p = KB.render(os.path.join(tiles, f"game_{dist}_{yaw}.png"), res=1080)
        KB.crop_center(p, 360)
        paths.append(p)
        labels.append(f"game cam {dist} m, facing {yaw} (1:1 px @1080p)")
    arm.rotation_euler.z = 0
    bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = 360
    KB.compose(paths, labels, os.path.join(out, f"{NAME}_rest_iso.png"), 4,
               f"{NAME}: rest / gameplay camera (shoulder ~{hi[2]:.2f} m top incl. spikes)", cell=360)
    paths, labels = [], []
    for cn in ("walk", "run", "hound_bite", "hound_lunge", "hound_breath", "hit_heavy", "death"):
        c, act = acts[cn]
        for fr in (0.0, 0.25, 0.5, 0.75, 1.0):
            f = int(round(fr * c.frames))
            KB.set_action(arm, act, f)
            KB.place(cam, (0, -0.2, 0.55), 3.6, 60, 12)
            paths.append(KB.render(os.path.join(tiles, f"{cn}_{f}.png")))
            labels.append(f"{cn} f{f}/{c.frames}")
    KB.compose(paths, labels, os.path.join(out, f"{NAME}_clips.png"), 5, f"{NAME}: clips (3/4 view)", cell=360)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--evidence", default="")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    import bh_mesh as M
    arm, mesh, acts = build_all()
    print(f"[{NAME}] mesh {M.tri_count(mesh)} tris, {len(acts)} clips, {len(arm.data.bones)} bones")
    if a.evidence:
        evidence(arm, mesh, acts, a.evidence)
    if not a.no_export:
        merge_meta(acts, OUT_META)
        export(arm, mesh, acts)


if __name__ == "__main__":
    main()
