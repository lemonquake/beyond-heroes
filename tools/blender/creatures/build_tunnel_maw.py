"""Tunnel Maw (bh-013, Builder C; burrowing worm): a giant segmented worm whose body rises ~3.2 m vertically out of a
ring-shaped mound of broken earth and rocks (the mound is part of the model, around the base). Sandy-ochre armour
bands with flared lower lips and dorsal studs over soft dark flesh, a round lamprey mouth at the top made of four
armoured jaw petals that open like a flower, three concentric rows of teeth down a dark red gullet with a small
red glow deep inside, and five feeler tendrils under the rim.

Rig: root -> mound (scaled flat when it burrows); root -> base (ground pivot, sinks the whole worm) -> seg1..seg7
spine -> head (mouth rim) -> petal1..4; seg7 -> feeler1..5.

  "<blender>" -b --factory-startup --python build_tunnel_maw.py -- [--no-export] [--evidence rest|clips|both] ...
Export: game/assets/characters/tunnel_maw.glb (+ .import); merges ONLY animations.maw_* and models.tunnel_maw into
creature_meta.json. Faces -Y (= +Z in Godot), origin on the ground at the centre of the mound, 30 fps, in place.
maw_burrow ends with the whole worm below y=0 (mound flattened); maw_emerge starts there.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_c13 as K  # noqa: E402
from kit_c13 import Rx, Ry, Rz, cyc, damp, normalize  # noqa: E402
import numpy as np  # noqa: E402

NAME = "tunnel_maw"
PREFIX = "maw_"
FPS = K.FPS
PALETTE = {
    "BH_Horn": ((0.56, 0.42, 0.2), 0.0, 0.62, None, 0.0, 1.0),        # sandy-ochre armour bands / petals
    "BH_Wood": ((0.3, 0.2, 0.09), 0.0, 0.7, None, 0.0, 1.0),          # darker band lips, studs, grooves
    "BH_Flesh": ((0.3, 0.13, 0.12), 0.0, 0.45, None, 0.0, 1.0),        # soft flesh between the bands, lip ring
    "BH_Ichor": ((0.2, 0.025, 0.03), 0.0, 0.3, None, 0.0, 1.0),        # dark red gullet / inner petals
    "BH_Bone": ((0.86, 0.8, 0.64), 0.0, 0.5, None, 0.0, 1.0),          # teeth
    "BH_Emissive": ((1.0, 0.22, 0.08), 0.0, 0.4, (1.0, 0.2, 0.06), 5.0, 1.0),   # red glow deep in the gullet
    "BH_Skin": ((0.5, 0.3, 0.24), 0.0, 0.5, None, 0.0, 1.0),           # feelers
    "BH_Leather": ((0.17, 0.12, 0.075), 0.0, 0.95, None, 0.0, 1.0),    # broken earth
    "BH_Stone": ((0.25, 0.23, 0.2), 0.0, 0.85, None, 0.0, 1.0),        # rocks
    "BH_Shadow": ((0.02, 0.015, 0.012), 0.0, 0.8, None, 0.0, 1.0),     # the hole
}

NSEG = 7
SEG_L = 0.45
Z_TOP = 3.1       # top of seg7 (the head / mouth rim above it)
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.25), None),
    "mound": ((0, 0, 0), (0, 0, 0.35), "root"),
    "base": ((0, 0, 0), (0, 0, -0.7), "root"),
}
_prev = "base"
for _i in range(1, NSEG + 1):
    _z0 = SEG_L * (_i - 1)
    _z1 = min(_z0 + SEG_L, Z_TOP)
    BONES[f"seg{_i}"] = ((0, 0, _z0), (0, 0, _z1), _prev)
    _prev = f"seg{_i}"
BONES["head"] = ((0, 0, Z_TOP), (0, 0, 3.35), "seg7")
RIM_R = 0.4
RIM_Z = 3.3
PETAL_OPEN = 32.0          # rest (authored) petal angle outward from vertical
PETAL_L = 0.62
PETAL_A = [math.radians(45 + 90 * k) for k in range(4)]
for _k, _a in enumerate(PETAL_A):
    _r = np.array([math.cos(_a), math.sin(_a), 0.0])
    _d = np.array([0, 0, math.cos(math.radians(PETAL_OPEN))]) + _r * math.sin(math.radians(PETAL_OPEN))
    _h = _r * RIM_R + np.array([0, 0, RIM_Z])
    BONES[f"petal{_k + 1}"] = (tuple(_h), tuple(_h + _d * PETAL_L), "head")
FEELER_A = [math.radians(a) for a in (-90 + 36, -90 - 36, -90 + 108, -90 - 108, 90)]
for _k, _a in enumerate(FEELER_A):
    _r = np.array([math.cos(_a), math.sin(_a), 0.0])
    _h = _r * 0.42 + np.array([0, 0, 2.98])
    BONES[f"feeler{_k + 1}"] = (tuple(_h), tuple(_h + _r * 0.35 + np.array([0, 0, -0.08])), "seg7")
RIG = K.Rig(BONES)
H, T = RIG.H, RIG.T
SEGS = [f"seg{i}" for i in range(1, NSEG + 1)]
CURL_W = [((i + 1) / NSEG) ** 1.5 * 2.2 for i in range(NSEG)]      # 'curl' grows toward the top


def body_r(z):
    """Flesh tube radius at height z."""
    return float(np.interp(z, [-0.8, 0.0, 1.5, 2.9, 3.2, 3.32], [0.52, 0.52, 0.49, 0.44, 0.43, 0.42]))


def evaluate(c):
    """Channels: depth (m, sinks the worm), base.lean/tilt/yaw/fwd, bend (deg per segment, + = forward),
    curl (deg, weighted toward the top), side (deg per segment, + = toward its left), twist (deg per segment),
    seg<i>.lean/tilt/yaw, head.lean/tilt/yaw, petal (deg, + = open wider than rest, - = close), petal<k>,
    feel (deg, + = feelers lift), mound.h / mound.w (scale deltas)."""
    Rd, S, L = {}, {}, {}
    Rd["base"] = Rz(c.get("base.yaw", 0.0)) @ Rx(c.get("base.lean", 0.0)) @ Ry(c.get("base.tilt", 0.0))
    L["base"] = np.array([c.get("base.side", 0.0), -c.get("base.fwd", 0.0), -c.get("depth", 0.0)])
    for i, b in enumerate(SEGS):
        lean = c.get(b + ".lean", 0.0) + c.get("bend", 0.0) + c.get("curl", 0.0) * CURL_W[i]
        tilt = c.get(b + ".tilt", 0.0) + c.get("side", 0.0)
        yaw = c.get(b + ".yaw", 0.0) + c.get("twist", 0.0)
        Rd[b] = Rz(yaw) @ Rx(lean) @ Ry(tilt)
    Rd["head"] = Rz(c.get("head.yaw", 0.0)) @ Rx(c.get("head.lean", 0.0)) @ Ry(c.get("head.tilt", 0.0))
    for k, a in enumerate(PETAL_A):
        t = np.array([-math.sin(a), math.cos(a), 0.0])
        Rd[f"petal{k + 1}"] = K.R_axis(t, c.get("petal", 0.0) + c.get(f"petal{k + 1}", 0.0))
    for k, a in enumerate(FEELER_A):
        t = np.array([-math.sin(a), math.cos(a), 0.0])
        Rd[f"feeler{k + 1}"] = Rz(c.get(f"feeler{k + 1}.yaw", 0.0)) @ K.R_axis(t, -c.get("feel", 0.0) -
                                                                                   c.get(f"feeler{k + 1}", 0.0))
    h = max(1.0 + c.get("mound.h", 0.0), 0.05)
    w = 1.0 + c.get("mound.w", 0.0)
    S["mound"] = (w, h, w)
    X = RIG.fk(Rd, S, L)
    return Rd, S, L, X


# ------------------------------------------------------------------------------------------------ clips
def wave(per, lean_amp, side_amp, lag=0.09, k=1):
    """Travelling sway up the body (loop-safe when k is an integer)."""
    def fn(f, cl):
        out = {}
        for i, b in enumerate(SEGS):
            out[b + ".lean"] = lean_amp * cyc(f, per, k, -lag * i)
            out[b + ".tilt"] = side_amp * cyc(f, per, k, 0.25 - lag * i)
        return out
    return fn


def flutter(per, amp=6.0, k=2):
    def fn(f, cl):
        out = {f"petal{j + 1}": amp * cyc(f, per, k, 0.23 * j) for j in range(4)}
        out.update({f"feeler{j + 1}": 12 * cyc(f, per, k, 0.17 * j) for j in range(5)})
        out.update({f"feeler{j + 1}.yaw": 10 * cyc(f, per, 1, 0.3 + 0.21 * j) for j in range(5)})
        return out
    return fn


def recoil(f0, amp, freq=2.5, decay=4.0):
    def fn(f, cl):
        j = damp(f, f0, freq, decay, amp)
        return {"curl": -0.35 * j, "head.lean": -0.5 * j}
    return fn


def clips():
    C = []
    # ---- idle: slow sway, the top looks down at the ground in front, petals breathe, feelers wave (3.0 s)
    P = 90
    c = K.Clip("idle", P, loop=True)
    c.key(0)
    c.layer(lambda f, cl: {"curl": 4.0 + 1.5 * cyc(f, P, 1, 0.1), "head.lean": 14 + 3 * cyc(f, P, 2),
                           "petal": 2 + 6 * cyc(f, P, 2, 0.3), "feel": 8, "twist": 2 * cyc(f, P, 1, 0.4)})
    c.layer(wave(P, 1.6, 2.4))
    c.layer(flutter(P, 4.0))
    C.append(c)
    # ---- idle_look: the top swings to its left, then right, feelers lift (2.5 s)
    c = K.Clip("idle_look", 75)
    c.key(0, curl=4.0, head_lean=14, feel=8).key(18, curl=3, head_lean=8, side=3.5, twist=5, head_yaw=10, feel=24,
                                                 petal=10)
    c.key(32, curl=3, head_lean=8, side=4, twist=6, head_yaw=14, feel=26, petal=8)
    c.key(50, curl=3, head_lean=8, side=-3.5, twist=-5, head_yaw=-10, feel=22, petal=12)
    c.key(62, curl=3.5, head_lean=10, side=-3, twist=-4, head_yaw=-8, feel=16, petal=6)
    c.key(75, curl=4.0, head_lean=14, side=0, twist=0, head_yaw=0, feel=8, petal=2)
    c.layer(flutter(75, 3.0))
    C.append(c)
    # ---- walk / run / run_combat: low sway (the game hides it underground while it travels)
    for nm, per, v, amp in (("walk", 40, 1.5, 1.0), ("run", 24, 4.0, 1.4), ("run_combat", 24, 4.0, 1.4)):
        c = K.Clip(nm, per, loop=True, ground_speed=v)
        c.key(0)
        cmb = nm == "run_combat"
        c.layer(lambda f, cl, per=per, amp=amp, cmb=cmb: {
            "curl": (6.0 if cmb else 4.5) + 1.5 * amp * cyc(f, per, 2), "head.lean": (18 if cmb else 12),
            "petal": (14 if cmb else 0) + 5 * cyc(f, per, 2, 0.2), "feel": 14})
        c.layer(wave(per, 2.5 * amp, 4.0 * amp, lag=0.12))
        c.layer(flutter(per, 4.0))
        C.append(c)
    # ---- reactions: the top recoils back (hit from the front) and wobbles
    base = dict(curl=4.0, head_lean=14, feel=8)
    c = K.Clip("hit_light", 12)
    c.key(0, **base).key(3, curl=1.0, head_lean=0, bend=-1.2, petal=-12, feel=30).key(12, **base, bend=0, petal=0)
    c.layer(recoil(3, 3.0, freq=3.5, decay=8))
    C.append(c)
    c = K.Clip("hit_heavy", 18)
    c.key(0, **base).key(4, curl=-2.0, head_lean=-12, bend=-2.5, side=1.5, petal=-20, feel=40, twist=6)
    c.key(9, curl=1.0, head_lean=4, bend=-1.0, side=0.8, petal=-8, feel=24, twist=3)
    c.key(18, **base, bend=0, side=0, petal=0, twist=0)
    c.layer(recoil(4, 4.0, freq=2.8, decay=6))
    C.append(c)
    c = K.Clip("stagger_small", 24)
    c.key(0, **base).key(5, curl=1.0, head_lean=4, bend=-1.5, side=-3.5, twist=-8, petal=-14, feel=30)
    c.key(12, curl=3.0, head_lean=10, bend=-0.5, side=2.0, twist=4, petal=4, feel=18)
    c.key(24, **base, bend=0, side=0, twist=0, petal=0)
    C.append(c)
    c = K.Clip("knockback", 27)
    c.key(0, **base).key(4, curl=-4.0, head_lean=-18, bend=-4.0, petal=-25, feel=45, mound_h=0.05)
    c.key(11, curl=-1.0, head_lean=-6, bend=-2.5, petal=-10, feel=30)
    c.key(19, curl=5.0, head_lean=18, bend=0.8, petal=4, feel=12)
    c.key(27, **base, bend=0, petal=0, mound_h=0)
    c.layer(recoil(11, 2.5, freq=2.2, decay=4))
    C.append(c)
    # ---- deaths: collapses sideways onto the ground (death: to its right; death_back: backward)
    for nm, sd, bk in (("death", -1, 0), ("death_back", 0, 1)):
        c = K.Clip(nm, 54)
        c.key(0, **base)
        c.key(8, curl=-2.0, head_lean=-16, bend=-1.5 * bk, side=2.0 * sd, petal=30, feel=40, twist=6)
        c.key(18, curl=0.0, head_lean=10, bend=-6.0 * bk, side=6.0 * sd, petal=20, feel=10, twist=10, depth=0.1,
              base_tilt=8 * sd, base_lean=-8 * bk)
        c.key(28, curl=0.0, head_lean=12, bend=-13.0 * bk, side=13.0 * sd, petal=8, feel=-20, twist=12, depth=0.26,
              base_tilt=16 * sd, base_lean=-16 * bk, seg1_tilt=8 * sd, seg1_lean=-8 * bk)
        c.key(34, curl=0.0, head_lean=6, bend=-14.3 * bk, side=14.3 * sd, petal=14, feel=-10, twist=12, depth=0.3,
              base_tilt=18.5 * sd, base_lean=-18.5 * bk, seg1_tilt=9 * sd, seg1_lean=-9 * bk)
        c.key(54, curl=0.0, head_lean=8, bend=-14.0 * bk, side=14.0 * sd, petal=-6, feel=-30, twist=12, depth=0.3,
              base_tilt=18 * sd, base_lean=-18 * bk, seg1_tilt=9 * sd, seg1_lean=-9 * bk)
        c.layer(lambda f, cl: {"curl": damp(f, 30, 3.0, 5.0, 1.0)})
        C.append(c)
    # ---- alert: rears up tall, petals flare, feelers spread, then looks down at the target
    c = K.Clip("alert", 30)
    c.key(0, **base).key(9, curl=-3.0, head_lean=-10, petal=38, feel=45, bend=-0.5)
    c.key(15, curl=-2.0, head_lean=-6, petal=34, feel=40, bend=-0.3)
    c.key(30, curl=5.0, head_lean=16, petal=6, feel=12, bend=0.3)
    c.layer(flutter(30, 5.0, k=3))
    C.append(c)
    # ---- maw_bite (1.0 s): rears back, petals open wide, lunges forward and down, petals snap shut ~0.5 s
    c = K.Clip("maw_bite", 30, hits=[[14 / FPS, 17 / FPS]])
    c.key(0, **base).key(8, curl=-5.0, head_lean=-14, bend=-1.5, petal=40, feel=40)
    c.key(12, curl=6.0, head_lean=22, bend=4.0, petal=48, feel=30)
    c.key(15, curl=11.0, head_lean=34, bend=7.0, petal=-26, feel=10, depth=-0.05)
    c.key(18, curl=11.5, head_lean=34, bend=7.3, petal=-30, feel=6, depth=-0.05)
    c.key(30, **base, bend=0, petal=0, depth=0)
    C.append(c)
    # ---- maw_slam (1.4 s): rears far back, then crashes the whole top half down onto the ground in front ~0.7 s
    c = K.Clip("maw_slam", 42, hits=[[20 / FPS, 23 / FPS]])
    c.key(0, **base).key(12, curl=-7.0, head_lean=-18, bend=-3.0, petal=30, feel=45, depth=-0.1)
    c.key(15, curl=-7.5, head_lean=-20, bend=-3.4, petal=34, feel=48, depth=-0.12)
    c.key(21, curl=7.0, head_lean=10, bend=12.5, petal=-12, feel=-10, depth=0.12, mound_h=0.08, mound_w=0.03)
    c.key(27, curl=7.0, head_lean=12, bend=12.2, petal=-6, feel=-20, depth=0.12, mound_h=0.0, mound_w=0.0)
    c.key(42, **base, bend=0, petal=0, depth=0)
    c.layer(lambda f, cl: {"bend": damp(f, 21, 4.0, 9.0, -0.6)})
    C.append(c)
    # ---- maw_spit (0.9 s): contracts back with the mouth shut, then thrusts forward, petals flare, release ~0.45 s
    c = K.Clip("maw_spit", 27, hits=[[13 / FPS, 15 / FPS]])
    c.key(0, **base).key(9, curl=-4.0, head_lean=-12, bend=-1.2, petal=-24, feel=35, depth=0.08)
    c.key(13, curl=7.0, head_lean=28, bend=1.5, petal=55, feel=10, depth=-0.05)
    c.key(16, curl=6.0, head_lean=26, bend=1.3, petal=50, feel=12, depth=-0.04)
    c.key(27, **base, bend=0, petal=0, depth=0)
    c.layer(recoil(14, 2.0, freq=3.0, decay=6))
    C.append(c)
    # ---- maw_burrow (1.0 s): petals shut, the worm sinks straight down until it is all below y=0; mound flattens
    c = K.Clip("maw_burrow", 30)
    c.key(0, **base).key(6, curl=-2.0, head_lean=0, petal=-30, feel=-35, depth=-0.12)
    c.key(30, curl=0.0, head_lean=0, petal=-32, feel=-40, depth=DEPTH_HIDE, mound_h=-0.72, mound_w=-0.12)
    c.layer(lambda f, cl: {"side": 2.5 * math.sin(f * 0.9) * (f / 30), "twist": 8 * math.sin(f * 0.6)})
    C.append(c)
    # ---- maw_emerge (0.8 s): bursts up from below with an overshoot, the mound heaves back up, petals open
    c = K.Clip("maw_emerge", 24)
    c.key(0, curl=0.0, head_lean=0, petal=-32, feel=-40, depth=DEPTH_HIDE, mound_h=-0.72, mound_w=-0.12)
    c.key(8, curl=-2.0, head_lean=-6, petal=-20, feel=-10, depth=0.6, mound_h=0.12, mound_w=0.06)
    c.key(13, curl=-3.5, head_lean=-12, petal=44, feel=40, depth=-0.25, mound_h=0.05, mound_w=0.03)
    c.key(24, **base, petal=0, depth=0, mound_h=0, mound_w=0)
    C.append(c)
    return C


DEPTH_HIDE = 4.05      # base drop that puts the petal tips below y = 0


# ------------------------------------------------------------------------------------------------ mesh
def rock(rng, center, size, up=(0, 0, 1), flat=0.6, mat="BH_Stone"):
    import bh_mesh as M
    V, F = M.sphere(1.0, 7, 4)
    V = V * (1 + 0.28 * (rng.random(len(V)) - 0.5))[:, None]
    V *= np.array([size * (0.8 + 0.4 * rng.random()), size * (0.8 + 0.4 * rng.random()), size * flat])
    R = K.align_z(up) @ Rz(rng.random() * 360)
    return M.Part(V @ R.T + np.asarray(center, float), F, mat, name="rock")


def build_mesh(mats):
    import bh_mesh as M
    parts = []
    rng = np.random.default_rng(31)

    def add(p, bone=None, bones=None, power=6.0, bias=None, top=3, W=None):
        if W is not None:
            p.W = W
        elif bone:
            p.W = [{bone: 1.0}] * len(p.V)
        else:
            p.W = K.dist_weights(RIG, p.V, bones, power=power, bias=bias, top=top)
        parts.append(p)
        return p

    SPINE_B = ["base"] + SEGS + ["head"]
    # ---- soft flesh tube from below ground to the mouth rim
    NA = 24
    zs = np.concatenate([np.linspace(-0.75, 0.0, 3)[:-1], np.linspace(0.0, 3.26, 30)])
    rings = []
    for z in zs:
        r = body_r(z)
        rings.append(np.array([(r * math.cos(2 * math.pi * i / NA), r * math.sin(2 * math.pi * i / NA), z)
                               for i in range(NA)]))
    V, F = M.loft(rings, cap0=True, cap1=False)
    add(M.Part(V, F, "BH_Flesh", name="flesh"), bones=SPINE_B, power=5, top=3)
    # ---- armour bands: one flared, fluted band per segment (rigid on its segment), dark lower lip, dorsal studs
    for i, b in enumerate(SEGS):
        z0 = SEG_L * i + 0.03
        z1 = min(z0 + SEG_L - 0.06, Z_TOP - 0.02) if i < NSEG - 1 else Z_TOP - 0.05
        r0, r1 = body_r(z0), body_r(z1)
        prof = [(r1 - 0.005, z1 + 0.01), (r1 + 0.035, z1 - 0.01), (r1 + 0.05, z1 - 0.08),
                ((r0 + r1) / 2 + 0.075, (z0 + z1) / 2), (r0 + 0.1, z0 + 0.06), (r0 + 0.1, z0 + 0.02),
                (r0 + 0.07, z0 - 0.01), (r0 + 0.01, z0 + 0.01)][::-1]      # bottom -> top: normals out
        V, F = M.lathe(prof, 32, cap=False)
        a = np.arctan2(V[:, 1], V[:, 0])
        rr = np.hypot(V[:, 0], V[:, 1])
        k = 1 + 0.03 * np.cos(9 * a + i) + 0.015 * np.cos(4 * a + 2 * i)
        V[:, 0] *= k
        V[:, 1] *= k
        band = M.Part(V, F, "BH_Horn", name="band")
        add(band, bone=b)
        # dark lower lip
        V, F = M.lathe([(r0 + 0.075, z0 - 0.018), (r0 + 0.108, z0 + 0.005), (r0 + 0.105, z0 + 0.035)], 32, cap=False)
        a = np.arctan2(V[:, 1], V[:, 0])
        k = 1 + 0.03 * np.cos(9 * a + i) + 0.015 * np.cos(4 * a + 2 * i)
        V[:, 0] *= k
        V[:, 1] *= k
        add(M.Part(V, F, "BH_Wood", name="lip"), bone=b)
        # dorsal studs (back and back-sides) and a groove plate line
        for j, ang in enumerate((90, 60, 120, 30, 150)):
            if i == 0 and j > 2:
                continue
            aa = math.radians(ang + 6 * math.sin(i * 1.7))
            nrm = np.array([math.cos(aa), math.sin(aa), 0.0])
            zc = (z0 + z1) / 2 + 0.02
            base_p = nrm * ((r0 + r1) / 2 + 0.06) + np.array([0, 0, zc])
            hgt = (0.13 if j == 0 else 0.08) * (1.0 - 0.25 * i / NSEG)
            V, F = M.lathe([(0.055 if j == 0 else 0.04, 0.0), (0.03, hgt * 0.6), (0.0, hgt)], 8)
            st = M.Part(V, F, "BH_Wood", name="stud")
            st.rot(K.align_z(normalize(nrm + np.array([0, 0, -0.35])))).move(base_p)
            add(st, bone=b)
    # ---- the mouth: flesh lip ring, gullet funnel, three rows of teeth, red glow deep inside
    V, F = M.tube([np.array([RIM_R * math.cos(t), RIM_R * math.sin(t), RIM_Z - 0.03]) for t in
                   np.linspace(0, 2 * math.pi, 29)[:-1]], [(0.07, 0.06)] * 28, n=8, up=(0, 0, 1), cap0=False,
                  cap1=False)
    # close the ring: loft of a closed polyline -> connect last ring to first
    nring = len(V) // 28
    F = list(F) + [(27 * nring + q, 27 * nring + (q + 1) % nring, (q + 1) % nring, q) for q in range(nring)]
    add(M.Part(V, F, "BH_Flesh", name="lip_ring"), bone="head")
    gul = [(0.4, RIM_Z - 0.02), (0.33, RIM_Z - 0.05), (0.26, RIM_Z - 0.16), (0.2, RIM_Z - 0.3), (0.14, RIM_Z - 0.46),
           (0.08, RIM_Z - 0.6), (0.0, RIM_Z - 0.64)]
    V, F = M.lathe(gul, 20)
    g = M.Part(V, F, "BH_Ichor", name="gullet")      # rim -> down: faces point into the mouth
    add(g, bones=["head", "seg7"], power=6, bias={"seg7": 1.5})
    V, F = M.sphere(0.07, 10, 5, center=(0, 0, RIM_Z - 0.56), scale=(1, 1, 0.6))
    add(M.Part(V, F, "BH_Emissive", name="glow"), bones=["head", "seg7"], power=6, bias={"seg7": 1.5})
    for q, (rr, zz, n, ln) in enumerate(((0.35, RIM_Z - 0.05, 16, 0.1), (0.27, RIM_Z - 0.16, 13, 0.085),
                                          (0.2, RIM_Z - 0.3, 10, 0.07))):
        for j in range(n):
            a = 2 * math.pi * (j + 0.5 * q) / n
            rh = np.array([math.cos(a), math.sin(a), 0.0])
            d = normalize(-rh * 0.9 + np.array([0, 0, -0.45]))
            V, F = M.lathe([(0.026 * ln / 0.1, 0.0), (0.016 * ln / 0.1, ln * 0.55), (0.0, ln)], 6)
            tt = M.Part(V, F, "BH_Bone", name="tooth")
            tt.rot(K.align_z(d)).move(rh * rr + np.array([0, 0, zz]))
            add(tt, bone="head")
    # ---- four jaw petals: armoured outside, dark red inside with hooked teeth, curled tips
    for k, a in enumerate(PETAL_A):
        b = f"petal{k + 1}"
        rh = np.array([math.cos(a), math.sin(a), 0.0])
        tg = np.array([-math.sin(a), math.cos(a), 0.0])
        d = normalize(T[b] - H[b])
        n_in = normalize(np.cross(d, tg))            # toward the mouth axis
        base = H[b] + rh * 0.02
        NU, NV = 9, 8

        def P(u, v, inner):
            w = 0.3 * (1 - v) ** 0.8 * (1 - 0.15 * v) + 0.015
            cup = 0.1 * u * u * (0.4 + 0.6 * v)
            hook = 0.16 * v ** 3
            thick = (0.045 * (1 - v) + 0.012) * (1 - 0.4 * u * u)
            p = base + d * PETAL_L * v + tg * u * w + n_in * (cup + hook)
            return p + n_in * (thick if inner else 0.0)
        us = np.linspace(-1, 1, NU)
        vs = np.linspace(0, 1, NV)
        Vo = [P(u, v, False) for v in vs for u in us]
        Vi = [P(u, v, True) for v in vs for u in us]
        Fo, Fi = [], []
        for j in range(NV - 1):
            for i in range(NU - 1):
                q = (j * NU + i, j * NU + i + 1, (j + 1) * NU + i + 1, (j + 1) * NU + i)
                Fo.append(q)
                Fi.append(tuple(reversed(q)))
        # outer shell + side walls (inner perimeter vertices duplicated into the outer part)
        per = [j * NU for j in range(NV)][::-1] + list(range(NU)) + [j * NU + NU - 1 for j in range(NV)]
        per = [0] + list(range(1, NU)) + [j * NU + NU - 1 for j in range(1, NV)] + \
            [(NV - 1) * NU + i for i in range(NU - 2, -1, -1)] + [j * NU for j in range(NV - 2, 0, -1)]
        Vall = list(Vo) + [Vi[q] for q in per]
        off = len(Vo)
        m = len(per)
        Fw = [(per[t], per[(t + 1) % m], off + (t + 1) % m, off + t) for t in range(m)]
        outer = M.Part(np.array(Vall), Fo + Fw, "BH_Horn", name="petal")
        add(outer, bone=b)
        add(M.Part(np.array(Vi), Fi, "BH_Ichor", name="petal_in"), bone=b)
        # ridge down the back of the petal
        V, F = M.tube([P(0, v, False) - n_in * 0.02 for v in (0.02, 0.35, 0.7, 0.95)],
                      [(0.035, 0.02), (0.03, 0.018), (0.02, 0.012), (0.008, 0.006)], n=6, up=tuple(-n_in))
        add(M.Part(V, F, "BH_Wood", name="petal_ridge"), bone=b)
        # hooked teeth in two rows on the inner face
        for v, cnt, ln in ((0.25, 4, 0.08), (0.55, 3, 0.065), (0.8, 2, 0.05)):
            for i in range(cnt):
                u = (i - (cnt - 1) / 2) / max(cnt - 1, 1) * 1.3 if cnt > 1 else 0.0
                u = max(min(u, 0.8), -0.8)
                p = P(u, v, True)
                dd = normalize(n_in * 0.8 - d * 0.5)
                V, F = M.lathe([(0.022 * ln / 0.08, 0.0), (0.012 * ln / 0.08, ln * 0.55), (0.0, ln)], 6)
                tt = M.Part(V, F, "BH_Bone", name="ptooth")
                tt.rot(K.align_z(dd)).move(p - n_in * 0.005)
                add(tt, bone=b)
    # ---- feelers: tapering tendrils curling out and down under the rim
    for k, a in enumerate(FEELER_A):
        b = f"feeler{k + 1}"
        rh = np.array([math.cos(a), math.sin(a), 0.0])
        h0 = H[b] - rh * 0.05
        pts = [h0, h0 + rh * 0.14 + np.array([0, 0, 0.03]), h0 + rh * 0.3 + np.array([0, 0, -0.02]),
               h0 + rh * 0.42 + np.array([0, 0, -0.14]), h0 + rh * 0.45 + np.array([0, 0, -0.28]),
               h0 + rh * 0.4 + np.array([0, 0, -0.36])]
        V, F = M.tube(pts, [(0.045, 0.04), (0.038, 0.034), (0.03, 0.027), (0.022, 0.02), (0.014, 0.013),
                            (0.006, 0.006)], n=7, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Skin", name="feeler"), bone=b)
    # ---- the mound: a lumpy ring of broken earth around the base, with rocks and clods, and a dark hole
    NA2, NR = 44, 11
    ph = rng.random(5) * 6.28
    rs = np.linspace(0.36, 1.75, NR)

    def mh(r, a):
        h = 0.46 * math.exp(-((r - 0.68) / 0.36) ** 2) + 0.06 * math.exp(-((r - 1.2) / 0.3) ** 2)
        lump = (1 + 0.28 * math.sin(3 * a + ph[0]) + 0.18 * math.sin(7 * a + ph[1] + r * 3)
                + 0.1 * math.sin(11 * a + ph[2]))
        return max(h * lump, 0.0) if r > 0.4 else -0.08
    Vm, Fm = [], []
    for j, r in enumerate(rs):
        for i in range(NA2):
            a = 2 * math.pi * i / NA2
            rr = r * (1 + 0.06 * math.sin(5 * a + ph[3]) * (r > 0.5))
            Vm.append((rr * math.cos(a), rr * math.sin(a), mh(r, a) - (0.02 if j == NR - 1 else 0.0)))
    for j in range(NR - 1):
        for i in range(NA2):
            i2 = (i + 1) % NA2
            Fm.append((j * NA2 + i, (j + 1) * NA2 + i, (j + 1) * NA2 + i2, j * NA2 + i2))
    add(M.Part(np.array(Vm), Fm, "BH_Leather", name="mound"), bone="mound")
    V, F = M.lathe([(0.0, 0.012), (0.42, 0.012)], 24)
    add(M.Part(V, F, "BH_Shadow", name="hole").flip(), bone="mound")
    for i in range(30):          # rocks: big broken slabs tilted out around the inner rim, smaller ones further out
        a = 2 * math.pi * (i + rng.random() * 0.6) / 30
        inner = i % 3 != 2
        r = (0.58 + 0.25 * rng.random()) if inner else (0.95 + 0.6 * rng.random())
        sz = (0.12 + 0.12 * rng.random()) if inner else (0.06 + 0.07 * rng.random())
        rh = np.array([math.cos(a), math.sin(a), 0.0])
        up = normalize(np.array([0, 0, 1.0]) + rh * (0.9 if inner else 0.3) + rng.normal(size=3) * 0.2)
        c = rh * r + np.array([0, 0, mh(r, a) * 0.85 + sz * 0.2])
        add(rock(rng, c, sz, up, flat=0.55 if inner else 0.7), bone="mound")
    for i in range(22):          # soil clods
        a = rng.random() * 2 * math.pi
        r = 0.5 + 1.1 * rng.random()
        rh = np.array([math.cos(a), math.sin(a), 0.0])
        sz = 0.04 + 0.05 * rng.random()
        add(rock(rng, rh * r + np.array([0, 0, mh(r, a) + sz * 0.1]), sz, (0, 0, 1), flat=0.7, mat="BH_Leather"),
            bone="mound")
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


REST_CFG = dict(views=[("front 3/4", (0, 0, 1.6), 9.5, 30, 10), ("side", (0, 0, 1.6), 9.5, 90, 8),
                       ("mouth from above", (0, 0, 3.2), 3.2, 20, 62), ("mound / base", (0, 0, 0.3), 4.5, 140, 25)],
                game=[(16, 0, 1.0), (16, 150, 1.0), (24, 60, 1.0)], target_z=1.2)


def clip_cfg():
    return dict(clips=["idle", "maw_bite", "maw_slam", "maw_spit", "maw_burrow", "maw_emerge", "death"],
                target=(0, -0.6, 1.4), dist=10.5, yaw=70, pitch=12)


if __name__ == "__main__":
    K.run_main(build_all, NAME, PREFIX, "tools/blender/creatures/build_tunnel_maw.py", REST_CFG, clip_cfg, RIG,
               evaluate)
