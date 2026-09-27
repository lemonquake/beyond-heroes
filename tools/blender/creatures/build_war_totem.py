"""War Totem (Builder C, bh-010): stationary orc totem pole planted by an Orc Shaman. Own minimal rig (root, base, pole,
top, rune, 4 dangling cords), skinned mesh and baked procedural clips.

  blender -b --factory-startup --python build_war_totem.py -- [--evidence] [--no-export] [--clips a,b] [--prev DIR --sheet a,b]

Conventions: Blender Z-up, carved face / rune toward -Y (= +Z in Godot), origin on the ground at the foot of the pole,
meters, 30 fps. The cords hang toward world-down (channel `cords.hang`, 1 by default) whatever the pole does, plus
per-cord swing channels, so they react to wobbles / the topple with lag.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import creature_kit_c as K  # noqa: E402
from creature_kit_c import Clip, Xf, Rx, Ry, cyc, pulse, spine_rot, FPS, I3  # noqa: E402

import numpy as np  # noqa: E402

CID = "war_totem"
OUT_GLB = os.path.join(K.CHAR_OUT, f"{CID}.glb")
PALETTE = {
    "BH_Wood": ((0.16, 0.11, 0.075), 0.0, 0.78, None, 0.0, 1.0),            # hewn pole, crossbar
    "BH_Cloth_Primary": ((0.52, 0.045, 0.025), 0.0, 0.8, None, 0.0, 1.0),  # red paint bands, red feathers
    "BH_Cloth_Secondary": ((0.78, 0.74, 0.64), 0.0, 0.85, None, 0.0, 1.0),  # pale feathers
    "BH_Bone": ((0.8, 0.74, 0.6), 0.0, 0.55, None, 0.0, 1.0),              # orc skull, tusks, hanging bones
    "BH_Horn": ((0.2, 0.15, 0.1), 0.0, 0.45, None, 0.0, 1.0),              # horns
    "BH_Leather": ((0.17, 0.095, 0.05), 0.0, 0.7, None, 0.0, 1.0),         # cords, lashings
    "BH_Gold": ((0.8, 0.56, 0.2), 1.0, 0.32, None, 0.0, 1.0),              # beads
    "BH_Stone": ((0.34, 0.32, 0.29), 0.0, 0.88, None, 0.0, 1.0),           # base stones
    "BH_Fur": ((0.2, 0.14, 0.09), 0.0, 0.95, None, 0.0, 1.0),              # dirt mound
    "BH_DarkSteel": ((0.15, 0.15, 0.16), 0.85, 0.5, None, 0.0, 1.0),       # iron ring around the rune
    "BH_Hair": ((0.07, 0.06, 0.06), 0.0, 0.7, None, 0.0, 1.0),             # dark feathers
    "BH_Shadow": ((0.015, 0.008, 0.008), 0.0, 0.8, None, 0.0, 1.0),        # eye sockets, carved mouths
    "BH_Emissive": ((1.0, 0.22, 0.08), 0.0, 0.3, (1.0, 0.16, 0.05), 8.0, 1.0),   # rune stone, skull eye glints
}

POLE_TOP = 1.62
CROSS_Z = 1.5
RUNE_C = np.array([0.0, -0.136, 1.04])
CORDS = {"cord.1": (0.41, 0.0, CROSS_Z - 0.03, 0.5), "cord.2": (0.2, -0.03, CROSS_Z - 0.035, 0.34),
         "cord.3": (-0.2, -0.03, CROSS_Z - 0.035, 0.38), "cord.4": (-0.41, 0.0, CROSS_Z - 0.03, 0.46)}
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.3), None),
    "base": ((0, 0, 0), (0, -0.3, 0), "root"),
    "pole": ((0, 0, 0), (0, 0, POLE_TOP), "root"),
    "top": ((0, 0, POLE_TOP), (0, 0, 2.2), "pole"),
    "rune": (tuple(RUNE_C), tuple(RUNE_C + np.array([0, -0.1, 0])), "pole"),
}
for _c, (_x, _y, _z, _L) in CORDS.items():
    BONES[_c] = ((_x, _y, _z), (_x, _y, _z - _L), "pole")
RIG = K.Rig(BONES)
H, T = RIG.H, RIG.T
CORD_IDS = list(CORDS)
DOWN = np.array([0.0, 0.0, -1.0])


# ------------------------------------------------------------------------------------------------ pose
def evaluate(c):
    X = {}
    g = c.get
    t = np.array([0.0, 0.0, g("body.up", 0.0)])
    X["root"] = Xf.move(t)
    X["base"] = Xf.about(I3, np.zeros(3), 1.0 + g("base.s", 0.0))
    RIG.fk(X, "pole", spine_rot(c, "pole"))
    RIG.fk(X, "top", spine_rot(c, "top"), off=np.array([g("top.side", 0.0), -g("top.fwd", 0.0), g("top.up", 0.0)]))
    RIG.fk(X, "rune", s=1.0 + g("rune.s", 0.0))
    hang = min(max(1.0 + g("cords.hang", 0.0), 0.0), 1.0)
    for i, cb in enumerate(CORD_IDS):
        P = X["pole"]
        head = P.apply(H[cb])
        d1 = P.R @ RIG.rdir(cb)                      # follows the pole
        dt = K.unit(d1 * (1 - hang) + DOWN * hang)   # hangs toward world down
        sw = Rx(g(cb + ".sx", 0.0) + g("cords.sx", 0.0)) @ Ry(g(cb + ".sy", 0.0) + g("cords.sy", 0.0))
        d = K.unit(sw @ dt)
        R = K.min_rot(d1, d) @ P.R
        X[cb] = Xf(R, head - R @ H[cb])
    return X


# ------------------------------------------------------------------------------------------------ clips
def cord_sway(f, period, amp=5.0, k=1):
    out = {}
    for i, cb in enumerate(CORD_IDS):
        out[cb + ".sx"] = amp * cyc(f, period, k, 0.23 * i)
        out[cb + ".sy"] = 0.7 * amp * cyc(f, period, k, 0.17 + 0.31 * i)
    return out


def ring_out(f, f0, period, amp, decay):
    """damped oscillation starting at f0 (0 before)."""
    if f < f0:
        return 0.0
    return amp * math.sin(2 * math.pi * (f - f0) / period) * math.exp(-(f - f0) / decay)


def clips():
    C = []
    c = Clip("idle", 90, loop=True)
    c.key(0)
    c.layer(lambda f, cl: dict(cord_sway(f, 90, 6.0, 1), **{
        "top.roll": 0.8 * cyc(f, 90, 1, 0.1), "top.pitch": 0.6 * cyc(f, 90, 2, 0.3),
        "pole.roll": 0.25 * cyc(f, 90, 1, 0.4), "rune.s": 0.05 * cyc(f, 90, 3)}))
    C.append(c)
    # ---- pulse: the rune flares, the pole shudders, the skull jolts, cords fling out and settle
    c = Clip("totem_pulse", 24)
    c.key(0).key(3, rune_s=0.5, top_up=0.045, top_pitch=-6).key(7, rune_s=0.25, top_up=0.0, top_pitch=2)
    c.key(24, rune_s=0.0, top_up=0.0, top_pitch=0)
    c.layer(lambda f, cl: dict(
        {"pole.roll": 1.4 * math.sin(2 * math.pi * f / 3.0) * pulse(f, 0, 11),
         "pole.pitch": 0.8 * math.sin(2 * math.pi * f / 4.0) * pulse(f, 0, 11),
         "top.roll": ring_out(f, 3, 8, 4.0, 7)},
        **{cb + ".sy": (-1 if H[cb][0] > 0 else 1) * (40 * pulse(f, 1, 9) + ring_out(f, 9, 14, 10, 8))
           for cb in CORD_IDS},
        **{cb + ".sx": ring_out(f, 2 + i, 12, 12, 8) for i, cb in enumerate(CORD_IDS)}))
    C.append(c)
    # ---- hits: the pole rocks back about its base, the skull lags, cords swing
    for nm, n, amp in (("hit_light", 12, 3.0), ("hit_heavy", 18, 7.0)):
        c = Clip(nm, n)
        c.key(0).key(n)
        c.layer(lambda f, cl, amp=amp, n=n: dict(
            {"pole.pitch": ring_out(f, 0, n * 0.55, amp, n * 0.35),
             "pole.roll": ring_out(f, 1, n * 0.6, amp * 0.35, n * 0.35),
             "top.pitch": ring_out(f, 2, n * 0.5, amp * 0.9, n * 0.3),
             "rune.s": 0.15 * pulse(f, 0, 6) * amp / 7},
            **{cb + ".sx": ring_out(f, 1 + i % 2, n * 0.6, -amp * 5, n * 0.4) for i, cb in enumerate(CORD_IDS)},
            **{cb + ".sy": ring_out(f, 2, n * 0.7, amp * 2 * (1 if i % 2 else -1), n * 0.4)
               for i, cb in enumerate(CORD_IDS)}))
        C.append(c)
    # ---- death: rune flares and dies, the pole creaks, topples backward, the skull cracks off at the impact
    c = Clip("death", 45)
    c.key(0)
    c.key(5, rune_s=0.55, pole_pitch=-2)
    c.key(9, rune_s=0.1, pole_pitch=3, pole_roll=-1)
    c.key(15, rune_s=-0.2, pole_pitch=18, pole_roll=-4, cords_hang=-0.2)
    c.key(20, rune_s=-0.35, pole_pitch=52, pole_roll=-8, top_pitch=4, cords_hang=-0.6)
    c.key(24, rune_s=-0.45, pole_pitch=84, pole_roll=-9, top_pitch=6, top_fwd=0.0, top_up=0.0, cords_hang=-1.0)
    c.key(27, rune_s=-0.5, pole_pitch=80, pole_roll=-9, top_pitch=16, top_fwd=0.06, top_up=0.12, top_roll=-8,
          top_side=-0.03, cords_hang=-1.0)
    c.key(31, rune_s=-0.55, pole_pitch=85, pole_roll=-9, top_pitch=10, top_fwd=0.08, top_up=0.16, top_roll=-18,
          top_side=-0.06, cords_hang=-1.0)
    c.key(45, rune_s=-0.6, pole_pitch=84.5, pole_roll=-9, top_pitch=9, top_fwd=0.08, top_up=0.17, top_roll=-22,
          top_side=-0.07, cords_hang=-1.0)
    c.layer(lambda f, cl: dict(
        {"pole.roll": 0.8 * math.sin(2 * math.pi * f / 3.0) * pulse(f, 0, 9)},
        **{cb + ".sx": ring_out(f, 24, 8, 10, 5) for cb in CORD_IDS}))
    C.append(c)
    # ---- alert (0.6 s): bursts up out of the ground as it is planted, overshoots, settles; mound heaps up
    c = Clip("alert", 18)
    c.key(0, body_up=-2.35, base_s=-0.85, rune_s=0.0)
    c.key(9, body_up=0.07, base_s=0.08, rune_s=0.2)
    c.key(12, body_up=-0.025, base_s=-0.02, rune_s=0.4)
    c.key(15, body_up=0.006, base_s=0.0, rune_s=0.15)
    c.key(18, body_up=0.0, base_s=0.0, rune_s=0.0)
    c.layer(lambda f, cl: dict(
        {"top.pitch": ring_out(f, 9, 7, -5, 5), "pole.roll": ring_out(f, 9, 6, 1.2, 4)},
        **{cb + ".sx": ring_out(f, 9, 9, -25 + 5 * i, 6) for i, cb in enumerate(CORD_IDS)}))
    C.append(c)
    return C


# ------------------------------------------------------------------------------------------------ mesh
def build_mesh():
    import bh_mesh as M
    parts = []
    rng = np.random.default_rng(23)

    def add(p, **kw):
        K.bind(p, RIG, **kw)
        parts.append(p)
        return p

    def solid(V, F, mat, name):
        return M.recalc_normals(M.Part(V, F, mat, name=name))

    def pole_r(z):
        """hewn pole radius profile with carved ridges."""
        r = 0.135 - 0.025 * z / POLE_TOP
        for zc, h, w in ((0.3, 0.025, 0.04), (0.9, 0.02, 0.04), (1.42, 0.025, 0.035), (0.44, -0.012, 0.05)):
            r += h * math.exp(-((z - zc) / w) ** 2)
        return r

    # ---- base: dirt mound + ring of stones (base bone)
    V, F = M.sphere(0.42, 16, 6, center=(0, 0, 0.0), scale=(1.0, 1.0, 0.2))
    add(M.Part(V, F, "BH_Fur", name="mound"), bone="base")
    for i in range(8):
        a = 2 * math.pi * i / 8 + 0.3 * rng.random()
        r = 0.27 + 0.06 * rng.random()
        s = 0.07 + 0.04 * rng.random()
        V, F = M.sphere(s, 7, 4, center=(r * math.cos(a), r * math.sin(a), 0.035),
                        scale=(1.2, 0.9 + 0.3 * rng.random(), 0.75))
        V = (V - V.mean(0)) @ K.Rz(math.degrees(a)).T + V.mean(0)
        add(M.Part(V, F, "BH_Stone", name="stone"), bone="base")
    # ---- pole (octagonal, hewn), stake below ground, painted bands
    zs = [-0.25] + list(np.linspace(0.0, POLE_TOP + 0.05, 34))
    prof = [(0.03, -0.3)] + [(pole_r(max(z, 0.0)) * (0.8 if z < 0 else 1.0), z) for z in zs]
    V, F = M.lathe(prof + [(0.0, POLE_TOP + 0.05)], n=8)
    V = V @ K.Rz(22.5).T
    add(solid(V, F, "BH_Wood", "pole"), bone="pole")
    for z0, z1 in ((0.2, 0.26), (0.34, 0.37), (0.84, 0.88), (0.94, 0.97), (1.36, 1.46)):
        pr = [(pole_r(z) + 0.006, z) for z in np.linspace(z0, z1, 3)]
        V, F = M.lathe(pr, n=8, cap=False)
        V = V @ K.Rz(22.5).T
        add(M.Part(V, F, "BH_Cloth_Primary", name="paint"), bone="pole")
    # red painted fangs/chevrons running down the front
    for i in range(3):
        z = 0.12 + 0.05 * i
        V, F = M.box(0.05, 0.012, 0.03, center=(0, -pole_r(z) - 0.002, z))
        add(solid(V, F, "BH_Cloth_Primary", "chevron"), bone="pole")
    # ---- carved orc face at z ~0.62 (front)
    fz = 0.62
    fr = pole_r(fz)
    V, F = M.box(0.2, 0.06, 0.045, center=(0, -fr - 0.005, fz + 0.075))
    add(solid(V, F, "BH_Wood", "brow"), bone="pole")
    for sx in (1, -1):
        V, F = M.sphere(0.03, 8, 4, center=(sx * 0.05, -fr + 0.004, fz + 0.035), scale=(1.1, 0.5, 0.8))
        add(M.Part(V, F, "BH_Shadow", name="socket"), bone="pole")
        V, F = M.sphere(0.03, 8, 4, center=(sx * 0.05, -fr - 0.012, fz + 0.035), scale=(1.2, 0.35, 0.28))
        add(M.Part(V, F, "BH_Cloth_Primary", name="eye_paint"), bone="pole")
    V, F = M.prism([(-0.03, 0.0), (0.03, 0.0), (0.0, 0.07)], 0.06, axis="y", center=-fr - 0.02)
    V = V + np.array([0, 0, fz - 0.03])
    add(solid(V, F, "BH_Wood", "nose"), bone="pole")
    V, F = M.box(0.13, 0.02, 0.035, center=(0, -fr + 0.002, fz - 0.075))
    add(solid(V, F, "BH_Shadow", "mouth"), bone="pole")
    for sx in (1, -1):
        b = np.array([sx * 0.045, -fr - 0.01, fz - 0.09])
        V, F = M.tube([b, b + np.array([sx * 0.008, -0.012, 0.035]), b + np.array([sx * 0.02, -0.02, 0.07])],
                      [(0.014, 0.012), (0.01, 0.009), (0.002, 0.002)], n=6, up=(0, -1, 0))
        add(M.Part(V, F, "BH_Bone", name="tusk"), bone="pole")
    # ---- rune stone (emissive) in an iron ring, on its own bone (flares by scaling)
    V, F = M.sphere(1.0, 10, 6, center=RUNE_C, scale=(0.065, 0.035, 0.09))
    add(M.Part(V, F, "BH_Emissive", name="rune"), bone="rune")
    ang = np.linspace(0, 2 * math.pi, 13)
    pts = [RUNE_C + np.array([0.078 * math.cos(a), 0.012, 0.102 * math.sin(a)]) for a in ang]
    V, F = M.tube(pts, [(0.012, 0.012)] * len(pts), n=6, up=(0, -1, 0))
    add(M.Part(V, F, "BH_DarkSteel", name="rune_ring"), bone="pole")
    for sx in (1, -1):         # rune glyph scratches painted around it
        for j in range(2):
            z = RUNE_C[2] - 0.06 + 0.12 * j
            V, F = M.box(0.05, 0.01, 0.012, center=(sx * 0.1, -pole_r(z) + 0.012, z))
            V = (V - V.mean(0)) @ K.Ry(sx * (35 if j else -35)).T + V.mean(0)
            add(solid(V, F, "BH_Cloth_Primary", "glyph"), bone="pole")
    # ---- crossbar with lashings
    V, F = M.tube([(-0.46, 0.0, CROSS_Z), (0.0, -0.02, CROSS_Z + 0.015), (0.46, 0.0, CROSS_Z)],
                  [(0.035, 0.04), (0.04, 0.045), (0.035, 0.04)], n=7, up=(0, 0, 1))
    add(solid(V, F, "BH_Wood", "crossbar"), bone="pole")
    for k in range(4):
        a = math.radians(45 + 90 * k)
        V, F = M.tube([(0.11 * math.cos(a), 0.11 * math.sin(a) - 0.01, CROSS_Z - 0.06),
                       (0.06 * math.cos(a), 0.06 * math.sin(a) - 0.05, CROSS_Z + 0.06)], [(0.009, 0.009)] * 2,
                      n=4, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Leather", name="lashing"), bone="pole")
    for x in (-0.44, 0.44):     # tied-on horn tips on the crossbar ends
        s = 1 if x > 0 else -1
        pts = [(x, 0, CROSS_Z), (x + s * 0.06, -0.01, CROSS_Z + 0.03), (x + s * 0.1, -0.02, CROSS_Z + 0.09)]
        V, F = M.tube(pts, [(0.028, 0.028), (0.018, 0.018), (0.003, 0.003)], n=6, up=(0, -1, 0))
        add(M.Part(V, F, "BH_Bone", name="bar_tusk"), bone="pole")
    # ---- cords: leather thong + beads + feathers / a small bone, each rigid on its cord bone
    for i, cb in enumerate(CORD_IDS):
        h, tl = H[cb], T[cb]
        V, F = M.tube([h + np.array([0, 0, 0.02]), h * 0.5 + tl * 0.5, tl], [(0.007, 0.007)] * 3, n=5,
                      up=(0, -1, 0))
        add(M.Part(V, F, "BH_Leather", name="cord"), bone=cb)
        for j in range(3 + i % 2):
            q = h + (tl - h) * (0.3 + 0.15 * j)
            mat = "BH_Gold" if (i + j) % 2 else "BH_Bone"
            V, F = M.sphere(0.02 if mat == "BH_Gold" else 0.024, 7, 4, center=q, scale=(1, 1, 0.8))
            add(M.Part(V, F, mat, name="bead"), bone=cb)
        if i in (0, 3):     # a hanging bone
            q0 = tl + np.array([0, 0, 0.0])
            V, F = M.tube([q0, q0 + np.array([0, 0, -0.14])], [(0.013, 0.013)] * 2, n=6, up=(0, -1, 0))
            add(M.Part(V, F, "BH_Bone", name="hang_bone"), bone=cb)
            for dz in (0.0, -0.14):
                for dx in (-0.012, 0.012):
                    V, F = M.sphere(0.017, 6, 4, center=q0 + np.array([dx, 0, dz]))
                    add(M.Part(V, F, "BH_Bone", name="knob"), bone=cb)
        for fk in range(2):
            ang_ = (-12 + 24 * fk) * (1 if i % 2 else -1)
            base = tl + np.array([0, 0, 0.01 if i in (0, 3) else 0.0])
            d = K.Ry(ang_) @ np.array([0.0, 0.0, -1.0])
            V, F = M.sphere(1.0, 8, 5, center=(0, 0, 0), scale=(0.028, 0.005, 0.1))
            V = V @ K.min_rot([0, 0, -1.0], d).T + base + d * 0.1 + (np.array([0, 0, -0.14]) if i in (0, 3) else 0)
            mat = ("BH_Cloth_Primary", "BH_Cloth_Secondary", "BH_Hair")[(i + fk) % 3]
            add(M.Part(V, F, mat, name="feather"), bone=cb)
    # ---- top: orc skull with tusks and horns, feather crown (top bone)
    V, F = M.tube([(0, 0, POLE_TOP - 0.03), (0, 0, 1.78)], [(0.05, 0.05), (0.04, 0.04)], n=8, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Wood", name="neck"), bone="top")
    V, F = M.sphere(0.17, 16, 10, center=(0, 0.03, 1.9), scale=(1.0, 1.12, 0.88))
    add(M.Part(V, F, "BH_Bone", name="cranium"), bone="top")
    V, F = M.tube([(-0.13, -0.1, 1.86), (0.0, -0.15, 1.88), (0.13, -0.1, 1.86)], [(0.04, 0.035)] * 3, n=8,
                  up=(0, 0, 1))
    add(M.Part(V, F, "BH_Bone", name="brow"), bone="top")
    V, F = M.sphere(1.0, 12, 6, center=(0, -0.12, 1.755), scale=(0.12, 0.11, 0.075))
    add(M.Part(V, F, "BH_Bone", name="muzzle"), bone="top")
    V, F = M.sphere(1.0, 12, 6, center=(0, -0.1, 1.67), scale=(0.135, 0.12, 0.045))
    add(M.Part(V, F, "BH_Bone", name="jaw"), bone="top")
    for sx in (1, -1):
        V, F = M.sphere(0.042, 10, 6, center=(sx * 0.068, -0.14, 1.83), scale=(1.0, 0.6, 0.85))
        add(M.Part(V, F, "BH_Shadow", name="socket"), bone="top")
        V, F = M.sphere(0.013, 6, 4, center=(sx * 0.068, -0.162, 1.828))
        add(M.Part(V, F, "BH_Emissive", name="glint"), bone="top")
        b = np.array([sx * 0.085, -0.17, 1.665])
        V, F = M.tube([b, b + np.array([sx * 0.015, -0.03, 0.08]), b + np.array([sx * 0.045, -0.035, 0.17])],
                      [(0.026, 0.024), (0.018, 0.017), (0.003, 0.003)], n=7, up=(0, -1, 0))
        add(M.Part(V, F, "BH_Bone", name="tusk"), bone="top")
        pts = [(sx * 0.13, 0.02, 1.96), (sx * 0.24, -0.02, 2.0), (sx * 0.33, -0.06, 2.07), (sx * 0.39, -0.06, 2.16),
               (sx * 0.4, -0.02, 2.22)]
        V, F = M.tube(pts, [(0.05, 0.045), (0.04, 0.036), (0.03, 0.027), (0.018, 0.016), (0.003, 0.003)], n=8,
                      up=(0, 0, 1))
        add(M.Part(V, F, "BH_Horn", name="horn"), bone="top")
        for j in range(3):
            q = np.array(pts[j]) * 0.6 + np.array(pts[j + 1]) * 0.4
            V, F = M.tube([q + (0, 0.0, -0.045 + 0.005 * j), q + (0, 0.0, 0.045 - 0.005 * j)],
                          [(0.052 - 0.01 * j, 0.052 - 0.01 * j)] * 2, n=8, up=(1, 0, 0))
            V = (V - q) @ K.Ry(sx * 20).T + q
            add(M.Part(V, F, "BH_Horn", name="horn_ridge"), bone="top")
    V, F = M.sphere(1.0, 8, 4, center=(0, -0.178, 1.77), scale=(0.028, 0.012, 0.035))
    add(M.Part(V, F, "BH_Shadow", name="nose"), bone="top")
    for k in range(5):
        a = -40 + 20 * k
        d = K.Ry(a) @ K.Rx(-18) @ np.array([0.0, 0.0, 1.0])
        base = np.array([0, 0.14, 1.9]) + d * 0.02
        V, F = M.sphere(1.0, 8, 5, center=(0, 0, 0), scale=(0.04, 0.006, 0.15))
        V = V @ K.min_rot([0, 0, 1.0], d).T + base + d * 0.13
        add(M.Part(V, F, ("BH_Cloth_Primary", "BH_Hair", "BH_Cloth_Secondary")[k % 3], name="feather"), bone="top")
    return parts


# ------------------------------------------------------------------------------------------------ main
def main():
    a = K.std_args()
    import bh_mesh as M
    C = clips()
    only = set(x for x in a.clips.split(",") if x) or None
    arm, mesh, acts = K.build_all(CID, RIG, evaluate, C, build_mesh, PALETTE, only=only, ao=(16, 0.2, 0.55))
    tris = M.tri_count(mesh)
    print(f"[{CID}] mesh {tris} tris, {len(mesh.data.vertices)} verts, {len(RIG.ORDER)} bones, {len(acts)} clips")
    cd = next(x for x in C if x.name == "death")
    X = evaluate(cd.channels(float(cd.frames)))
    low = min(min(RIG.head(X, b)[2], RIG.tail(X, b)[2]) for b in ("pole", "top"))
    print(f"[{CID}] death end: lowest pole/top bone point z {low:.3f}")
    K.quick_preview(CID, arm, acts, a, 1.1, 5.4, yaw=35, pitch=8)
    if a.evidence:
        K.evidence_rest(CID, arm, 1.1, 5.4, "War Totem - rest (4 views + 3/4 + gameplay iso)")
        spec = [("idle", [0, 0.25, 0.5, 0.75]), ("totem_pulse", [0, 3 / 24, 7 / 24, 1.0]),
                ("alert", [0, 5 / 18, 9 / 18, 12 / 18, 1.0]), ("hit_heavy", [3 / 18, 7 / 18]),
                ("death", [9 / 45, 15 / 45, 20 / 45, 24 / 45, 31 / 45, 1.0])]
        K.evidence_clips(CID, arm, acts, spec, 0.9, 6.6, "War Totem - clips (view yaw 35)", yaw=35, pitch=10,
                         cols=6)
    if not a.no_export and not only:
        K.merge_meta(CID, C, "tools/blender/creatures/build_war_totem.py", {"tris": tris, "bones": len(RIG.ORDER),
                                                                             "stationary": True})
        bad, got = K.export(CID, arm, mesh, acts, OUT_GLB)
        assert not bad, bad
    notes = [f"Generator: `tools/blender/creatures/build_war_totem.py` -> `game/assets/characters/{CID}.glb`",
             "", "- Size: 2.2 m (horn tips 2.22 m, skull crown ~2.05 m); crossbar 0.92 m + tusk tips; base mound "
             "0.84 m across.",
             f"- Triangles: {tris}; vertices {len(mesh.data.vertices)}; bones {len(RIG.ORDER)} (root non-deform).",
             f"- Materials: {', '.join(sorted(m.name for m in mesh.data.materials))}",
             "- Bones: " + ", ".join(f"`{b}`" for b in RIG.ORDER),
             "- Stationary (no locomotion clips). `rune` bone scales the emissive rune stone for flares; cords hang "
             "toward world-down with per-cord swing.",
             f"- Death end pose: lowest pole/top bone point z {low:.3f} m (lies on the ground, skull cracked off).",
             "", "## Clips", ""] + K.clip_table(C)
    K.write_md(CID, "War Totem (war_totem.glb)", notes)


if __name__ == "__main__":
    main()
