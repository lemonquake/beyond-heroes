"""Marrow Hound (bh-029, Builder M4, Zarael / the Veinworks pack hunter): a lean hound (~0.95 m at the shoulder,
~1.9 m nose to tail tip) bred inside the sleeping Gigas. Raw dark sinew with no hide; plates of the giant's bone grown
over it - a long bone skull-mask over the muzzle and brow, curved bone ribs round the barrel, vertebral plates with
small spurs down the spine, plates on the shoulders, haunches and forelegs. White-glowing veins branch over the
exposed sinew (pure white BH_Emissive, the bh-029 glow rule), white eyes deep in the mask, long bone fangs, a thin
whip tail ending in bare vertebrae.

Rig / planar leg IK / gait / clip machinery: build_wolf.py (imported, not edited; the wolf skeleton is used as is).

  "<blender>" -b --factory-startup --python build_marrow_hound.py -- [--no-export] [--evidence DIR]

Clips (30 fps, in place): idle idle_look walk run run_combat hit_light hit_heavy stagger_small knockback death
death_back alert + mhound_bite, mhound_lunge (leap forward), mhound_howl.
creature_meta.json: merges ONLY animations.mhound_* and models.marrow_hound (re-read right before writing).
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
NAME = "marrow_hound"
STEM = "mhound_"
OUT_GLB = os.path.join(ROOT_DIR, "game", "assets", "characters", NAME + ".glb")
OUT_META = os.path.join(ROOT_DIR, "game", "assets", "characters", "creature_meta.json")

import numpy as np  # noqa: E402

import build_wolf as W  # noqa: E402

FPS = W.FPS
PALETTE = {
    "BH_Fur": ((0.085, 0.03, 0.032), 0.0, 0.55, None, 0.0, 1.0),          # raw dark sinew
    "BH_Flesh": ((0.2, 0.055, 0.055), 0.0, 0.45, None, 0.0, 1.0),          # redder muscle bands, gums, tongue
    "BH_Bone": ((0.52, 0.48, 0.39), 0.0, 0.55, None, 0.0, 1.0),            # bone plates, ribs, skull-mask
    "BH_Horn": ((0.27, 0.23, 0.18), 0.0, 0.6, None, 0.0, 1.0),             # old dark bone: spurs, claws, fangs' roots
    "BH_Shadow": ((0.015, 0.012, 0.012), 0.0, 0.6, None, 0.0, 1.0),        # sockets, nose, mouth
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),  # white veins, eyes
}
GENERIC = ["idle", "idle_look", "walk", "run", "run_combat", "hit_light", "hit_heavy", "stagger_small", "knockback",
           "death", "death_back", "alert"]
H, T = W.H, W.T


# ------------------------------------------------------------------------------------------------ clips
def clips():
    base = {c.name: c for c in W.clips()}
    out = []
    for n in GENERIC:
        c = copy.deepcopy(base[n])
        if n in ("walk", "run", "run_combat", "idle", "idle_look"):
            # a hunter's carriage: head low and level, tail straight out
            c.layer(lambda f, cl: {"neck.pitch": -7.0, "head.pitch": 3.0, "tail.lift": 4.0})
        out.append(c)
    b = copy.deepcopy(base["wolf_bite"])
    b.name = STEM + "bite"
    out.append(b)
    p = copy.deepcopy(base["wolf_pounce"])
    p.name = STEM + "lunge"
    out.append(p)
    h = copy.deepcopy(base["wolf_howl"])
    h.name = STEM + "howl"
    out.append(h)
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


# lean, deep-chested body with a tucked waist (y, zc, rx, r_top, r_bottom)
BODY = [(0.56, 0.8, 0.04, 0.04, 0.04), (0.48, 0.81, 0.085, 0.07, 0.08), (0.38, 0.82, 0.095, 0.07, 0.09),
        (0.26, 0.835, 0.085, 0.065, 0.075), (0.14, 0.85, 0.075, 0.065, 0.07), (0.02, 0.855, 0.09, 0.075, 0.13),
        (-0.12, 0.855, 0.11, 0.09, 0.2), (-0.26, 0.855, 0.115, 0.1, 0.21), (-0.36, 0.875, 0.105, 0.1, 0.17),
        (-0.43, 0.9, 0.09, 0.095, 0.12)]
NECK = [(-0.36, 0.9, 0.095, 0.1, 0.13), (-0.44, 0.96, 0.085, 0.085, 0.11), (-0.52, 1.02, 0.072, 0.07, 0.085),
        (-0.56, 1.05, 0.066, 0.062, 0.07)]
SKULL = [(-0.48, 1.06, 0.056, 0.056, 0.05), (-0.54, 1.075, 0.072, 0.068, 0.062), (-0.6, 1.066, 0.074, 0.062, 0.062),
         (-0.65, 1.05, 0.055, 0.05, 0.05), (-0.7, 1.03, 0.04, 0.036, 0.032), (-0.76, 1.016, 0.034, 0.031, 0.025),
         (-0.81, 1.008, 0.027, 0.025, 0.018), (-0.845, 1.0, 0.013, 0.012, 0.01)]
JAW = [(-0.58, 0.985, 0.046, 0.02, 0.03), (-0.66, 0.975, 0.036, 0.016, 0.026), (-0.74, 0.968, 0.028, 0.013, 0.02),
       (-0.8, 0.964, 0.018, 0.01, 0.014)]


def build_mesh(mats):
    import bh_mesh as M
    import kit_a_common as A
    parts = []
    rng = np.random.default_rng(41)

    def add(p, bone=None, bones=None, power=6.0, bias=None):
        if bone:
            p.W = [{bone: 1.0}] * len(p.V)
        else:
            p.W = W.dist_weights(p.V, bones, power=power, bias=bias)
        parts.append(p)
        return p

    def plate(c, nrm, w, l, t, along, mat="BH_Bone", seed=0):
        """Curved bone scute centred on a surface point: w across, l along `along`, t thick (domed)."""
        V, F = M.sphere(1.0, 10, 5)
        V = np.asarray(V, float)
        V[:, 2] = np.where(V[:, 2] < 0, V[:, 2] * 0.2, V[:, 2])
        V = V * np.array([w / 2, l / 2, t])
        p = M.Part(V, F, mat, name="plate")
        p.warp(lambda v: (v[0], v[1], v[2] - 0.6 * t * (v[0] / (w / 2)) ** 2))
        p.V += np.random.default_rng(seed).normal(size=p.V.shape) * t * 0.06
        nz = nrm / np.linalg.norm(nrm)
        ay = along - nz * (along @ nz)
        ay /= np.linalg.norm(ay)
        ax = np.cross(ay, nz)
        p.rot(np.stack([ax, ay, nz], 1)).move(c)
        return p

    def spur(base, d, ln, r, mat="BH_Horn"):
        d = np.asarray(d, float)
        d /= np.linalg.norm(d)
        b = np.asarray(base, float)
        return A.taper([b - d * r, b + d * ln * 0.5, b + d * ln], r, 0.0015, mat, n=5)

    def vein(pts, r=0.0055):
        k = len(pts)
        return A.tube(pts, [r * (1 - 0.6 * i / max(k - 1, 1)) + 0.0015 for i in range(k)], "BH_Emissive", n=4)

    BODYB = ["hips", "spine", "chest", "neck", "scap.L", "scap.R", "thigh.L", "thigh.R", "tail.1"]
    BIAS = {"scap.L": 1.5, "scap.R": 1.5, "thigh.L": 1.35, "thigh.R": 1.35, "tail.1": 1.6, "neck": 1.2}
    # ---- sinew body + neck
    V, F = M.loft([ring(*r, n=20) for r in BODY][::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Fur", name="body"), bones=BODYB, bias=BIAS)
    V, F = M.loft([ring(*r, n=16) for r in NECK][::-1], cap0=False, cap1=False)
    add(M.Part(V, F, "BH_Fur", name="neck"), bones=["chest", "neck", "head"], bias={"head": 1.3})
    # raised muscle bands (redder) along the flanks and the neck
    for sx in (1, -1):
        pts = [surf(BODY, y, math.radians(35), 0.004)[0] * np.array([sx, 1, 1]) for y in (-0.3, -0.16, 0.0, 0.16, 0.3)]
        add(A.tube(pts, [0.016, 0.02, 0.016, 0.014, 0.016], "BH_Flesh", n=5), bones=BODYB, bias=BIAS)
        pts = [surf(NECK, y, math.radians(20), 0.003)[0] * np.array([sx, 1, 1]) for y in (-0.38, -0.46, -0.54)]
        add(A.tube(pts, 0.014, "BH_Flesh", n=5), bones=["chest", "neck", "head"], bias={"head": 1.3})
    # ---- ribs: curved bone bars round the barrel (both sides), a sternum keel under the chest
    for i, y in enumerate(np.linspace(-0.32, 0.02, 6)):
        for sx in (1, -1):
            pts = []
            for a in np.linspace(80, -62 + 6 * i, 6):
                q, n = surf(BODY, y + 0.02 * math.sin(math.radians(a)), math.radians(a), 0.006)
                pts.append(q * np.array([sx, 1, 1]))
            add(A.tube(pts, [(0.016, 0.016)] * 6, "BH_Bone", n=5), bones=BODYB, bias=BIAS)
    keel = [surf(BODY, y, -math.pi / 2, 0.004)[0] for y in (-0.36, -0.24, -0.12, 0.0)]
    add(A.tube(keel, 0.018, "BH_Bone", n=5), bones=BODYB, bias=BIAS)
    # ---- vertebral plates + spurs down the spine
    for i, y in enumerate(np.linspace(-0.4, 0.48, 12)):
        rows = NECK if y < -0.36 else BODY
        q, n = surf(rows, y, math.pi / 2, 0.0)
        add(plate(q, n, 0.075 - 0.02 * (i > 8), 0.075, 0.022, np.array([0, 1.0, 0.0]), seed=i), bones=BODYB, bias=BIAS)
        if i % 2 == 0 and i < 10:
            add(spur(q + n * 0.015, np.array([0, 0.9, 1.0]), 0.07 - 0.004 * i, 0.014), bones=BODYB, bias=BIAS)
    for y in (-0.5, -0.46):
        q, n = surf(NECK, y, math.pi / 2, 0.0)
        add(plate(q, n, 0.07, 0.07, 0.02, np.array([0, 1.0, 0.6]), seed=30), bones=["neck", "chest", "head"],
            bias={"head": 1.3})
    # ---- white veins branching over the sinew (between the ribs, down the flanks and neck)
    for i, y in enumerate(np.linspace(-0.28, 0.06, 5)):
        for sx in (1, -1):
            pts = []
            for k, a in enumerate(np.linspace(60, -40, 5)):
                yy = y + 0.035 + 0.012 * math.sin(k * 2.1 + i)
                pts.append(surf(BODY, yy, math.radians(a), 0.003)[0] * np.array([sx, 1, 1]))
            add(vein(pts), bones=BODYB, bias=BIAS)
    for sx in (1, -1):
        pts = [surf(BODY, y, math.radians(20 + 10 * math.sin(y * 20)), 0.003)[0] * np.array([sx, 1, 1])
               for y in np.linspace(0.08, 0.46, 6)]
        add(vein(pts, 0.006), bones=BODYB, bias=BIAS)
        pts = [surf(NECK, y, math.radians(-10 + 30 * (k % 2)), 0.003)[0] * np.array([sx, 1, 1])
               for k, y in enumerate(np.linspace(-0.36, -0.55, 5))]
        add(vein(pts, 0.006), bones=["chest", "neck", "head"], bias={"head": 1.3})
    # ---- head: sinew skull under a long bone mask (brow + muzzle), deep white eyes, fangs
    V, F = M.loft([ring(*r, n=14) for r in SKULL][::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Fur", name="skull"), bone="head")
    # the bone mask: a shell over the top half of the skull from the brow to the nose, with a ridge down the middle
    mrows = []
    for (y, z, rx, rt, rb) in SKULL[1:7]:
        arc = []
        for a in np.linspace(math.radians(-8), math.radians(188), 11):
            arc.append((rx * 1.12 * math.cos(a), y, z + 0.004 + rt * 1.12 * max(math.sin(a), -0.15)))
        mrows.append(np.array(arc))
    V, F = M.loft(mrows[::-1], cap0=False, cap1=False, closed=False)
    add(M.solidify(M.Part(V, F, "BH_Bone", name="mask"), 0.01, offset=1.0), bone="head")
    ridge = [(0.0, y, z + rt * 1.12 + 0.012) for (y, z, rx, rt, rb) in SKULL[1:7]]
    add(A.tube(ridge, [(0.012, 0.01)] * len(ridge), "BH_Bone", n=5), bone="head")
    for sx in (1, -1):
        add(plate(np.array([sx * 0.06, -0.57, 1.05]), np.array([sx, -0.1, 0.25]), 0.07, 0.08, 0.018,
                  np.array([0, -1.0, 0.0]), seed=60 + (sx > 0)), bone="head")
        # brow ridge: a hard bar over a slanted socket, horns swept back
        add(A.tube([(sx * 0.02, -0.665, 1.105), (sx * 0.055, -0.64, 1.1), (sx * 0.075, -0.6, 1.095)],
                   [0.012, 0.014, 0.01], "BH_Bone", n=5), bone="head")
        # brow ridge horns swept back
        add(spur(np.array([sx * 0.05, -0.6, 1.11]), np.array([sx * 0.4, 1.0, 0.45]), 0.13, 0.02), bone="head")
        V, F = M.sphere(0.02, 8, 5, center=(sx * 0.052, -0.64, 1.082), scale=(0.7, 1.5, 0.5))
        add(M.Part(V, F, "BH_Shadow", name="socket"), bone="head")
        V, F = M.sphere(0.009, 6, 4, center=(sx * 0.057, -0.645, 1.082), scale=(0.9, 1.6, 0.6))
        add(M.Part(V, F, "BH_Emissive", name="eye"), bone="head")
        for y, Lh in ((-0.79, 0.045), (-0.74, 0.032), (-0.69, 0.024)):
            V, F = M.lathe([(0.0, -Lh), (0.006, -Lh * 0.3), (0.007, 0.0), (0.0, 0.004)], 4)
            add(M.Part(V, F, "BH_Bone").move((sx * 0.024, y, 0.99)), bone="head")
        for y in (-0.775, -0.72):
            V, F = M.lathe([(0.0, 0.0), (0.006, 0.003), (0.005, 0.026), (0.0, 0.032)], 4)
            add(M.Part(V, F, "BH_Bone").move((sx * 0.02, y, 0.972)), bone="jaw")
    V, F = M.loft([ring(*r, n=12) for r in JAW][::-1], cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Fur", name="jaw"), bone="jaw")
    V, F = M.loft([ring(y, z + 0.013, rx * 0.8, 0.007, 0.006, n=10) for (y, z, rx, rt, rb) in JAW[:3]][::-1])
    add(M.Part(V, F, "BH_Flesh", name="tongue"), bone="jaw")
    V, F = M.loft([ring(y, z - 0.024, rx * 0.85, 0.008, 0.01, n=12) for (y, z, rx, rt, rb) in SKULL[2:6]][::-1])
    add(M.Part(V, F, "BH_Flesh", name="gums"), bone="head")
    V, F = M.sphere(0.018, 8, 5, center=(0, -0.84, 1.012), scale=(1.1, 0.8, 0.8))
    add(M.Part(V, F, "BH_Shadow", name="nose"), bone="head")
    # jaw bone plate + a vein under the eye
    q, n = surf(JAW, -0.7, -math.pi / 2, 0.0)
    add(plate(q, n, 0.06, 0.14, 0.016, np.array([0, -1.0, 0.0]), seed=70), bone="jaw")
    for sx in (1, -1):
        add(vein([np.array(p_) for p_ in ((sx * 0.06, -0.62, 1.05), (sx * 0.06, -0.58, 1.03), (sx * 0.065, -0.53, 1.04))],
                 0.005), bone="head")
    # ears: short ragged sinew flaps with a bone rim
    for s, sx in (("L", 1), ("R", -1)):
        h = H["ear." + s]
        V, F = M.lathe([(0.0, 0.0), (0.03, 0.01), (0.026, 0.05), (0.0, 0.085)], 6)
        e = M.Part(V, F, "BH_Fur", name="ear").scale((1.0, 0.3, 1.0)).rot(W.Rz(-10 * sx)).rot(W.Rx(-25)).move(h)
        add(e, bone="ear." + s)
        add(spur(h + (0, 0.01, 0.0), np.array([sx * 0.2, 0.5, 1.0]), 0.08, 0.008, mat="BH_Bone"), bone="ear." + s)

    # ---- legs: sinew tubes, bone plates on shoulder / forearm / haunch / shin, veins, bone claws
    def leg_tube(chain, radii, mat="BH_Fur"):
        pts = [H[chain[0]]] + [T[b] for b in chain]
        V, F = M.tube(pts, radii, n=10, up=(0, -1, 0))
        return M.Part(V, F, mat, name="leg")
    for s, sx in (("L", 1), ("R", -1)):
        fr = ["scap." + s, "upperarm." + s, "forearm." + s, "fpaw." + s]
        add(leg_tube(fr, [(0.072, 0.098), (0.065, 0.08), (0.045, 0.05), (0.03, 0.034), (0.026, 0.028)]),
            bones=fr + ["chest"], power=8, bias={"chest": 1.6})
        hi = ["thigh." + s, "shin." + s, "hpaw." + s]
        p = leg_tube(hi, [(0.095, 0.12), (0.068, 0.08), (0.038, 0.043), (0.026, 0.028)])
        p.V[:, 0] += 0.01 * sx
        add(p, bones=["hips"] + hi, power=8, bias={"hips": 1.8})
        V, F = M.sphere(0.1, 12, 7, center=(0.075 * sx, 0.38, 0.72), scale=(0.75, 1.1, 1.25))
        add(M.Part(V, F, "BH_Fur", name="haunch"), bones=["hips", "thigh." + s], power=6, bias={"hips": 0.9})
        add(plate(np.array([0.13 * sx, 0.38, 0.75]), np.array([sx, 0.1, 0.4]), 0.13, 0.17, 0.03, np.array([0, 1.0, 0.0]),
                  seed=80 + (sx > 0)), bones=["hips", "thigh." + s], power=6, bias={"hips": 0.9})
        add(plate(np.array([0.13 * sx, -0.26, 0.78]), np.array([sx, -0.3, 0.5]), 0.12, 0.15, 0.028,
                  np.array([0, 0.3, 1.0]), seed=82 + (sx > 0)), bones=["scap." + s, "chest"], power=6)
        add(spur(np.array([0.15 * sx, -0.25, 0.83]), np.array([sx * 0.4, 0.6, 1.0]), 0.09, 0.016),
            bones=["scap." + s, "chest"], power=6)
        for bone_, c, n in (("forearm." + s, (H["forearm." + s] * 0.6 + T["forearm." + s] * 0.4), (sx * 0.4, -1.0, 0)),
                            ("shin." + s, (H["shin." + s] + T["shin." + s]) / 2, (sx, 0.4, 0))):
            n = np.array(n, float)
            add(plate(np.asarray(c) + n / np.linalg.norm(n) * 0.04, n, 0.06, 0.12, 0.018, T[bone_] - H[bone_],
                      seed=90 + (sx > 0)), bone=bone_)
        for b in (fr[1], hi[0]):
            a_, t_ = H[b], T[b]
            d = t_ - a_
            side = np.array([sx * 1.0, -0.3, 0.0])
            side /= np.linalg.norm(side)
            r0 = 0.07 if "thigh" in b else 0.06
            pts = [a_ + d * u + side * r0 * (1.0 - 0.3 * u) + np.array([0, 0.012 * math.sin(9 * u), 0])
                   for u in np.linspace(0.12, 0.88, 5)]
            add(vein(pts, 0.006), bone=b)
        for toe, meta in (("ftoe." + s, "fpaw." + s), ("htoe." + s, "hpaw." + s)):
            c = H[toe]
            V, F = M.sphere(0.04, 10, 6, center=c + (0, -0.03, -0.005), scale=(0.95, 1.3, 0.55))
            add(M.Part(V, F, "BH_Fur", name="paw"), bone=toe)
            V, F = M.sphere(0.032, 8, 5, center=c + (0, 0.015, 0.0), scale=(0.9, 1.0, 0.6))
            add(M.Part(V, F, "BH_Fur", name="heel"), bone=meta)
            for k in range(4):
                x = (k - 1.5) * 0.019
                V, F = M.tube([c + (x, -0.07, 0.008), c + (x, -0.11, -0.016)], [(0.008, 0.008), (0.001, 0.001)],
                              n=4, up=(0, 0, 1))
                add(M.Part(V, F, "BH_Bone", name="claw"), bone=toe)
    # ---- whip tail: thin sinew, the last third bare vertebrae
    pts = [H["tail.1"] + (0, -0.03, 0.01)] + [T["tail.%d" % i] for i in range(1, 4)]
    V, F = M.tube(pts, [(0.03, 0.032), (0.024, 0.026), (0.018, 0.02), (0.012, 0.013)], n=8, up=(1, 0, 0))
    add(M.Part(V, F, "BH_Fur", name="tail"), bones=["hips", "tail.1", "tail.2", "tail.3"], power=8, bias={"hips": 2.0})
    tp = [T["tail.2"], T["tail.3"], T["tail.4"], T["tail.4"] + (T["tail.4"] - H["tail.4"]) * 0.9]
    V, F = M.tube(tp, [(0.007, 0.007)] * 4, n=5, up=(1, 0, 0))
    add(M.Part(V, F, "BH_Horn", name="tailcord"), bones=["tail.2", "tail.3", "tail.4"], power=8)
    seg = [np.asarray(tp[0]) + (np.asarray(tp[-1]) - np.asarray(tp[0])) * 0.0]
    for i in range(9):
        u = (i + 0.5) / 9
        k = min(int(u * 3), 2)
        f = u * 3 - k
        c = np.asarray(tp[k]) * (1 - f) + np.asarray(tp[k + 1]) * f
        V, F = M.sphere(0.018 - 0.0012 * i, 6, 4, center=c, scale=(1.0, 0.7, 1.0))
        add(M.Part(V, F, "BH_Bone", name="vertebra"), bones=["tail.2", "tail.3", "tail.4"], power=8)
        if i % 2 == 0:
            add(spur(c, np.array([0, 0.3, 1.0]), 0.04 - 0.003 * i, 0.007, mat="BH_Bone"),
                bones=["tail.2", "tail.3", "tail.4"], power=8)
    top = [np.asarray(p) + (0, 0, r) for p, r in zip(pts[1:4], (0.026, 0.02, 0.014))]
    add(vein(top, 0.005), bones=["tail.1", "tail.2", "tail.3"], power=8)
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
    MT.bake_vertex_ao(mesh, rays=16, dist=0.2, strength=0.6)
    acts = {}
    for c in clips():
        acts[c.name] = (c, W.bake(arm, c))
    return arm, mesh, acts


def merge_meta(acts, path, tris, bones):
    """Merge ONLY this model's keys: animations.mhound_* and models.marrow_hound. Re-read right before writing
    (other builders merge into the same file), keep every other key, write, re-read and verify."""
    mine, clips_all = {}, {}
    for name, (c, act) in acts.items():
        d = {"length": round(c.frames / FPS, 3), "loop": bool(c.loop)}
        if "hits" in c.meta:
            d["hits"] = [[round(a, 3), round(b, 3)] for a, b in c.meta["hits"]]
        if "ground_speed" in c.meta:
            d["ground_speed"] = c.meta["ground_speed"]
        clips_all[name] = d
        if name.startswith(STEM):
            mine[name] = d
    model = {"generator": "tools/blender/creatures/build_marrow_hound.py",
             "glb": "res://assets/characters/%s.glb" % NAME, "clips": clips_all, "tris": tris, "bones": bones}
    with open(path) as fh:
        data = json.load(fh)
    before_a = {k: v for k, v in data.get("animations", {}).items() if not k.startswith(STEM)}
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
    """<out>/marrow_hound_rest_iso.png and _clips.png (Workbench, kit_b_evidence helpers)."""
    import bpy
    import kit_b_evidence as KB
    tiles = os.path.join(scratch, NAME)
    os.makedirs(tiles, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    KB.material_colors()
    cam = KB.setup(360)
    lo, hi = KB.mesh_bounds(mesh)
    print(f"[{NAME}] rest bounds min {np.round(lo, 3)} max {np.round(hi, 3)}")
    paths, labels = [], []
    KB.set_action(arm, acts["idle"][1], 0)
    for yaw in (90, 35, 0, 200):
        KB.place(cam, (0, 0.05, 0.6), 3.6, yaw, 10)
        paths.append(KB.render(os.path.join(tiles, f"rest_{yaw}.png")))
        labels.append(f"idle f0 yaw {yaw}")
    KB.place(cam, (0, -0.66, 1.0), 1.0, 30, 8)
    paths.append(KB.render(os.path.join(tiles, "closeup.png")))
    labels.append("close-up (bone mask)")
    KB.place(cam, (0, 0.0, 0.9), 2.0, 160, 45)
    paths.append(KB.render(os.path.join(tiles, "back.png")))
    labels.append("spine plates from above-behind")
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
    for cn in ("walk", "run", STEM + "bite", STEM + "lunge", STEM + "howl", "hit_heavy", "death"):
        c, act = acts[cn]
        for fr in (0.0, 0.25, 0.4, 0.55, 0.75, 1.0):
            f = int(round(fr * c.frames))
            KB.set_action(arm, act, f)
            KB.place(cam, (0, 0.0, 0.6), 4.0, 60, 12)
            paths.append(KB.render(os.path.join(tiles, f"{cn}_{f}.png")))
            labels.append(f"{cn} f{f}/{c.frames}")
    KB.compose(paths, labels, os.path.join(out, f"{NAME}_clips.png"), 6, f"{NAME}: clips (3/4 view)", cell=300)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--evidence", default="")
    ap.add_argument("--scratch", default=os.path.join(ROOT_DIR, "work", "lemondev", "bh-029", "scratch", "m4", "ev"))
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
