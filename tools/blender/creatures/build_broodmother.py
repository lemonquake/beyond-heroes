"""Broodmother (Builder C, bh-010): giant cave spider with its own 8-leg rig, skinned mesh and baked procedural clips.
The game also uses this GLB scaled to 0.42 for Spiderling helpers.

  blender -b --factory-startup --python build_broodmother.py -- [--evidence] [--no-export] [--clips a,b]

Conventions: Blender Z-up, faces -Y (= +Z in Godot), origin on the ground under the pedicel, meters, 30 fps.
Legs: 4 bones each (coxa / femur / tibia / tarsus), solved per frame with creature_kit_c.plane_leg (the coxa yaws about
the body's up axis, femur + tibia are a 2-bone hinge IK with the knee up, the tarsus keeps a steep pitch). Stance feet
are world-fixed (in-place clips: they slide back at exactly ground_speed). Gait: alternating tetrapod
(L1 R2 L3 R4 vs R1 L2 R3 L4) with a slight back-to-front ripple inside each group.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import creature_kit_c as K  # noqa: E402
from creature_kit_c import Clip, Xf, Rx, Ry, Rz, cyc, pulse, spine_rot, smooth, FPS  # noqa: E402

import numpy as np  # noqa: E402

CID = "broodmother"
OUT_GLB = os.path.join(K.CHAR_OUT, f"{CID}.glb")
PALETTE = {
    "BH_Fur": ((0.042, 0.034, 0.03), 0.0, 0.82, None, 0.0, 1.0),        # near-black hairy chitin (legs, sternum)
    "BH_Horn": ((0.15, 0.085, 0.05), 0.0, 0.42, None, 0.0, 1.0),        # glossy chestnut carapace, claws, spinnerets
    "BH_Hair": ((0.36, 0.29, 0.2), 0.0, 0.92, None, 0.0, 1.0),          # coarse tawny hair tufts / spines
    "BH_Flesh": ((0.88, 0.24, 0.035), 0.0, 0.5, None, 0.0, 1.0),        # warning markings + knee bands
    "BH_Bone": ((0.8, 0.78, 0.68), 0.0, 0.85, None, 0.0, 1.0),          # silk egg sacs
    "BH_Shadow": ((0.012, 0.01, 0.01), 0.0, 0.25, None, 0.0, 1.0),      # fangs, mouth
    "BH_Emissive": ((0.55, 1.0, 0.28), 0.0, 0.3, (0.45, 1.0, 0.18), 5.0, 1.0),   # venom-green eyes / venom drops
}

# ------------------------------------------------------------------------------------------------ skeleton
PIVOT = np.array([0.0, -0.12, 0.56])
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.25), None),
    "body": ((0, 0.02, 0.56), (0, -0.62, 0.6), "root"),            # cephalothorax (pivots at the pedicel)
    "abdomen": ((0, 0.0, 0.6), (0, 1.02, 0.74), "root"),           # pivots at the pedicel
}
for _s, _x in (("L", 1.0), ("R", -1.0)):
    BONES.update({
        f"chel.{_s}": ((0.062 * _x, -0.58, 0.54), (0.068 * _x, -0.67, 0.37), "body"),
        f"fang.{_s}": ((0.068 * _x, -0.67, 0.37), (0.046 * _x, -0.61, 0.33), f"chel.{_s}"),
        f"palp.1.{_s}": ((0.11 * _x, -0.6, 0.5), (0.15 * _x, -0.75, 0.5), "body"),
        f"palp.2.{_s}": ((0.15 * _x, -0.75, 0.5), (0.145 * _x, -0.81, 0.3), f"palp.1.{_s}"),
    })
# leg n: (attach point on the L side, azimuth deg (+ = toward the front), horizontal reach of the foot)
LEG_SPEC = {1: ((0.15, -0.5, 0.49), 55.0, 1.08), 2: ((0.21, -0.38, 0.48), 22.0, 0.96),
            3: ((0.22, -0.24, 0.48), -18.0, 0.92), 4: ((0.19, -0.1, 0.49), -48.0, 1.02)}
LEGS = {}
for _s, _x in (("L", 1.0), ("R", -1.0)):
    for _n, (_p, _az, _R) in LEG_SPEC.items():
        _P = np.array([_p[0] * _x, _p[1], _p[2]])
        _u = np.array([_x * math.cos(math.radians(_az)), -math.sin(math.radians(_az)), 0.0])

        def _pt(r, z, P=_P, u=_u):
            return tuple(P + u * r + np.array([0.0, 0.0, z - P[2]]))
        k = f"{_s}{_n}"
        names = (f"coxa.{_n}.{_s}", f"femur.{_n}.{_s}", f"tibia.{_n}.{_s}", f"tarsus.{_n}.{_s}")
        pts = [tuple(_P), _pt(0.09, _P[2] + 0.04), _pt(0.40 * _R, 0.97), _pt(0.80 * _R, 0.60), _pt(_R, 0.015)]
        for i, nm in enumerate(names):
            BONES[nm] = (pts[i], pts[i + 1], "body" if i == 0 else names[i - 1])
        LEGS[k] = names
RIG = K.Rig(BONES)
H, T = RIG.H, RIG.T
LEG_IDS = [f"{s}{n}" for n in (1, 2, 3, 4) for s in ("L", "R")]
NEUTRAL = {k: T[v[3]].copy() for k, v in LEGS.items()}
OUTW = {k: K.unit(np.array([(T[v[3]] - H[v[0]])[0], (T[v[3]] - H[v[0]])[1], 0.0])) for k, v in LEGS.items()}
BETA = {k: math.degrees(math.atan2(H[v[3]][2] - T[v[3]][2],
                                   np.linalg.norm((T[v[3]] - H[v[3]])[:2]))) for k, v in LEGS.items()}
GROUP_A = ("L1", "R2", "L3", "R4")
# dead-spider curl (leg plane angles: femur, tibia, tarsus; + = toward the body's back/up side)
CURL = (-38.0, -152.0, 146.0)
FLOOR = 0.015


# ------------------------------------------------------------------------------------------------ pose
def evaluate(c):
    X = {}
    g = c.get
    t = np.array([g("body.side", 0.0), -g("body.fwd", 0.0), g("body.up", 0.0)])
    X["root"] = Xf.move(t) @ Xf.about(spine_rot(c, "body"), PIVOT)
    RIG.fk(X, "body", spine_rot(c, "ceph"))
    RIG.fk(X, "abdomen", spine_rot(c, "abd"), s=1.0 + g("abd.scale", 0.0))
    for s, sx in (("L", 1.0), ("R", -1.0)):
        RIG.fk(X, f"chel.{s}", Rx(-g("chel", 0.0) - g("chel." + s, 0.0)) @ Ry(-sx * g("chel.spread", 0.0)))
        RIG.fk(X, f"fang.{s}", Rx(-110.0 * g("fang", 0.0)) @ Rz(sx * 12.0 * g("fang", 0.0)))
        RIG.fk(X, f"palp.1.{s}", Rx(-g("palp", 0.0) - g("palp." + s, 0.0)) @ Rz(sx * g("palp.out", 0.0)))
        RIG.fk(X, f"palp.2.{s}", Rx(g("palp.fold", 0.0) + g("palp.fold." + s, 0.0)))
    fol_all = g("legs.follow", 0.0)
    for k in LEG_IDS:
        cx, fe, ti, ta = LEGS[k]
        off = np.array([0.0, -(g(k + ".f", 0.0) + g("legs.f", 0.0)), g(k + ".up", 0.0) + g("legs.up", 0.0)])
        off = off + OUTW[k] * (g(k + ".side", 0.0) + g("legs.spread", 0.0))
        tw = NEUTRAL[k] + off
        w = min(max(fol_all + g(k + ".follow", 0.0), 0.0), 1.0)
        tgt = tw * (1 - w) + X["root"].apply(tw) * w
        tgt[2] = max(tgt[2], FLOOR)
        curl = min(max(g("legs.curl", 0.0) + g(k + ".curl", 0.0), 0.0), 1.0)
        K.plane_leg(RIG, X, X["body"], [fe, ti, ta], tgt, beta=BETA[k] + g(k + ".beta", 0.0), curl=curl,
                    curl_ang=CURL, coxa=cx)
    return X


def foot(X, k):
    return RIG.tail(X, LEGS[k][3])


# ------------------------------------------------------------------------------------------------ clips
def gait_layer(period, duty, speed, lift, wave=0.035):
    sweep = speed * duty * period / FPS

    def fn(f, clip):
        out = {}
        t = f / period
        for k in LEG_IDS:
            n = int(k[1])
            ph = (0.0 if k in GROUP_A else 0.5) + wave * (4 - n)
            ff, up, sw = K.gait_foot(t - ph, duty, sweep, lift * (1.0 if n in (1, 4) else 0.9))
            out[k + ".f"] = ff
            out[k + ".up"] = up
            out[k + ".beta"] = -14.0 * math.sin(math.pi * sw) if sw >= 0 else 0.0     # tarsus reaches during swing
        return out
    return fn


def legs(**kw):
    """legs(front=dict(up=..), mid=.., back=..) or per-id: expands to <id>_<ch> keys for Clip.key."""
    out = {}
    groups = {"front": ("L1", "R1"), "mid": ("L2", "R2", "L3", "R3"), "back": ("L4", "R4"),
              "all": tuple(LEG_IDS), "L1": ("L1",), "R1": ("R1",), "L2": ("L2",), "R2": ("R2",), "L3": ("L3",),
              "R3": ("R3",), "L4": ("L4",), "R4": ("R4",)}
    for gname, d in kw.items():
        for k in groups[gname]:
            for ch, v in d.items():
                out[f"{k}_{ch}"] = v
    return out


def clips():
    C = []
    # ---- idle: breathing abdomen, palps feeling, fang twitches, a front leg tap
    c = Clip("idle", 90, loop=True)
    c.key(0)
    c.layer(lambda f, cl: {"abd.scale": 0.012 * cyc(f, 90, 2), "abd.pitch": 1.5 * cyc(f, 90, 1, 0.2),
                           "body.up": 0.006 * cyc(f, 90, 2, 0.1), "ceph.yaw": 2.0 * cyc(f, 90, 1, 0.3),
                           "palp.L": 10 * cyc(f, 90, 3), "palp.R": 10 * cyc(f, 90, 3, 0.4), "palp": 8.0,
                           "fang": 0.12 * max(0.0, cyc(f, 90, 2, 0.1)) ** 6,
                           "L1.up": 0.1 * pulse(f, 38, 50) + 0.06 * pulse(f, 52, 60),
                           "L1.f": 0.06 * pulse(f, 38, 60)})
    C.append(c)
    # ---- idle_look: turn the cephalothorax left then right (feet stay planted), front legs lift & feel
    c = Clip("idle_look", 75)
    c.key(0).key(14, ceph_yaw=16, ceph_pitch=6, palp=20, **legs(L1=dict(up=0.22, f=0.1)))
    c.key(30, ceph_yaw=18, ceph_pitch=5, palp=16, **legs(L1=dict(up=0.0, f=0.12)))
    c.key(44, ceph_yaw=-16, ceph_pitch=6, palp=20, **legs(L1=dict(up=0.0, f=0.0), R1=dict(up=0.22, f=0.1)))
    c.key(58, ceph_yaw=-14, ceph_pitch=4, palp=12, **legs(R1=dict(up=0.0, f=0.08)))
    c.key(75, ceph_yaw=0, ceph_pitch=0, palp=0, **legs(R1=dict(up=0.0, f=0.0)))
    c.layer(lambda f, cl: {"abd.scale": 0.01 * cyc(f, 75, 2), "palp.L": 8 * cyc(f, 25, 1)})
    C.append(c)
    # ---- walk: alternating tetrapod
    WP, WV = 20, 1.6
    c = Clip("walk", WP, loop=True, ground_speed=WV)
    c.key(0)
    c.layer(gait_layer(WP, 0.58, WV, 0.15))
    c.layer(lambda f, cl: {"body.up": -0.015 + 0.012 * cyc(f, WP, 2, 0.1), "body.roll": 1.5 * cyc(f, WP, 1, 0.1),
                           "ceph.yaw": 2.0 * cyc(f, WP, 1, 0.25), "abd.yaw": -3.0 * cyc(f, WP, 1, 0.35),
                           "abd.pitch": 1.5 * cyc(f, WP, 2, 0.3), "palp": 14 + 8 * cyc(f, WP, 1),
                           "palp.L": 10 * cyc(f, WP, 1), "palp.R": -10 * cyc(f, WP, 1)})
    C.append(c)
    # ---- run / run_combat: fast tetrapod, low body, abdomen bounce
    for nm, v, crouch in (("run", 5.0, -0.06), ("run_combat", 4.6, -0.11)):
        RP = 10
        c = Clip(nm, RP, loop=True, ground_speed=v)
        c.key(0)
        c.layer(gait_layer(RP, 0.46, v, 0.2, wave=0.02))
        c.layer(lambda f, cl, cr=crouch: {
            "body.up": cr + 0.018 * cyc(f, RP, 2, 0.15), "body.pitch": -3.0 + 1.5 * cyc(f, RP, 2, 0.4),
            "body.roll": 2.0 * cyc(f, RP, 1, 0.1), "abd.pitch": -4.0 + 4.0 * cyc(f, RP, 2, 0.55),
            "abd.yaw": -3.0 * cyc(f, RP, 1, 0.3), "palp": 30, "palp.fold": 25,
            "fang": 0.35 if cr < -0.08 else 0.0, "chel.spread": 8 if cr < -0.08 else 0})
        C.append(c)
    # ---- reactions
    c = Clip("hit_light", 12)
    c.key(0).key(3, body_fwd=-0.06, body_up=0.03, ceph_pitch=9, abd_pitch=-6, fang=0.5, palp=25, legs_follow=0.3,
                 **legs(front=dict(up=0.08)))
    c.key(12, body_fwd=0, body_up=0, ceph_pitch=0, abd_pitch=0, fang=0, palp=0, legs_follow=0,
          **legs(front=dict(up=0.0)))
    C.append(c)
    c = Clip("hit_heavy", 18)
    c.key(0).key(4, body_fwd=-0.14, body_up=-0.05, body_roll=6, ceph_pitch=16, abd_pitch=-12, abd_yaw=8, fang=0.8,
                 chel_spread=14, palp=40, legs_spread=0.06, legs_follow=0.4, **legs(front=dict(up=0.16, f=0.06)))
    c.key(9, body_fwd=-0.12, body_up=-0.07, body_roll=3, ceph_pitch=8, abd_pitch=-4, abd_yaw=-4, fang=0.5,
          chel_spread=8, palp=20, legs_spread=0.08, legs_follow=0.3, **legs(front=dict(up=0.0, f=0.02)))
    c.key(18, body_fwd=0, body_up=0, body_roll=0, ceph_pitch=0, abd_pitch=0, abd_yaw=0, fang=0, chel_spread=0,
          palp=0, legs_spread=0, legs_follow=0, **legs(front=dict(up=0.0, f=0.0)))
    C.append(c)
    c = Clip("stagger_small", 24)
    c.key(0).key(5, body_fwd=-0.08, body_side=-0.07, body_roll=-9, body_yaw=-8, ceph_pitch=8, abd_yaw=10,
                 legs_follow=0.35, fang=0.4, **legs(R2=dict(up=0.12), L1=dict(up=0.1)))
    c.key(10, body_fwd=-0.1, body_side=-0.09, body_roll=-6, body_yaw=-6, ceph_pitch=4, abd_yaw=-6,
          legs_follow=0.3, **legs(R2=dict(up=0.0, side=0.1), L1=dict(up=0.0, f=-0.05)))
    c.key(16, body_fwd=-0.05, body_side=-0.04, body_roll=-2, body_yaw=-2, abd_yaw=3, legs_follow=0.15)
    c.key(24, body_fwd=0, body_side=0, body_roll=0, body_yaw=0, ceph_pitch=0, abd_yaw=0, legs_follow=0, fang=0,
          **legs(R2=dict(side=0.0), L1=dict(f=0.0)))
    C.append(c)
    c = Clip("knockback", 27)
    c.key(0).key(4, body_fwd=-0.22, body_up=0.06, body_pitch=10, ceph_pitch=12, abd_pitch=-10, fang=0.9, palp=45,
                 legs_follow=0.7, **legs(front=dict(up=0.25, f=0.1), mid=dict(up=0.08)))
    c.key(11, body_fwd=-0.38, body_up=-0.06, body_pitch=2, ceph_pitch=4, abd_pitch=4, fang=0.4, palp=20,
          legs_follow=0.85, **legs(front=dict(up=0.0, f=0.12), mid=dict(up=0.0)))
    c.key(18, body_fwd=-0.2, body_up=-0.03, body_pitch=0, ceph_pitch=0, abd_pitch=2, fang=0.1, palp=8,
          legs_follow=0.6, **legs(front=dict(f=0.04)))
    c.key(27, body_fwd=0, body_up=0, abd_pitch=0, fang=0, palp=0, legs_follow=0, **legs(front=dict(f=0.0)))
    C.append(c)
    # ---- deaths
    c = Clip("death", 45)          # legs buckle, it rolls over onto its back, legs curl up
    c.key(0)
    c.key(6, body_up=-0.14, ceph_pitch=-5, abd_pitch=6, fang=0.9, palp=40, legs_spread=0.1, legs_curl=0.1)
    c.key(12, body_up=0.12, body_side=0.12, body_roll=60, ceph_pitch=6, abd_pitch=-4, legs_follow=0.8,
          legs_curl=0.45, fang=0.6, palp=30)
    c.key(20, body_up=-0.06, body_side=0.2, body_roll=170, body_pitch=-6, abd_pitch=-8, legs_follow=1.0,
          legs_curl=0.85, fang=0.3)
    c.key(24, body_up=-0.1, body_side=0.2, body_roll=184, body_pitch=-10, abd_pitch=-10, legs_follow=1.0,
          legs_curl=1.0, fang=0.2)
    c.key(30, body_up=-0.07, body_side=0.2, body_roll=178, body_pitch=-8, abd_pitch=-10, legs_follow=1.0,
          legs_curl=1.0)
    c.key(45, body_up=-0.08, body_side=0.2, body_roll=180, body_pitch=-9, abd_pitch=-10, legs_follow=1.0,
          legs_curl=1.0, fang=0.15, palp=20, palp_fold=40)
    c.layer(lambda f, cl: {k + ".curl": 0.12 * pulse(f, 28 + 2 * i, 40 + 2 * i) * (1 if i % 2 else -1)
                           for i, k in enumerate(LEG_IDS)})
    C.append(c)
    c = Clip("death_back", 45)     # rears up, drops flat on its belly, legs splay and the tips curl in
    c.key(0)
    c.key(8, body_up=0.08, body_fwd=-0.06, ceph_pitch=22, abd_pitch=-10, fang=1.0, palp=50, chel_spread=12,
          **legs(front=dict(up=0.35, f=0.12)))
    c.key(18, body_up=-0.28, body_fwd=-0.04, ceph_pitch=-4, abd_pitch=8, fang=0.6, palp=10, chel_spread=6,
          legs_spread=0.3, **legs(front=dict(up=0.0, f=0.2)))
    c.key(24, body_up=-0.33, body_fwd=-0.04, ceph_pitch=-7, abd_pitch=11, fang=0.4, legs_spread=0.42,
          legs_curl=0.25, **legs(front=dict(f=0.22)))
    c.key(45, body_up=-0.34, body_fwd=-0.04, ceph_pitch=-8, abd_pitch=12, fang=0.3, palp_fold=50,
          legs_spread=0.45, legs_curl=0.4, **legs(front=dict(f=0.22)))
    C.append(c)
    # ---- alert: rear the front, raise the first legs, fangs bared
    c = Clip("alert", 30)
    c.key(0).key(9, ceph_pitch=16, body_up=0.05, abd_pitch=-10, fang=1.0, chel=18, chel_spread=12, palp=45,
                 **legs(front=dict(up=0.42, f=0.18), L2=dict(up=0.1), R2=dict(up=0.1)))
    c.key(20, ceph_pitch=13, body_up=0.04, abd_pitch=-8, fang=0.9, chel=14, chel_spread=10, palp=40,
          **legs(front=dict(up=0.36, f=0.2), L2=dict(up=0.0), R2=dict(up=0.0)))
    c.key(30, ceph_pitch=4, body_up=0.01, abd_pitch=-3, fang=0.3, chel=4, chel_spread=3, palp=12,
          **legs(front=dict(up=0.0, f=0.05)))
    c.layer(lambda f, cl: {"L1.up": 0.05 * cyc(f, 10, 1) * (1 if 8 < f < 22 else 0),
                           "R1.up": -0.05 * cyc(f, 10, 1) * (1 if 8 < f < 22 else 0)})
    C.append(c)
    # ---- attacks
    c = Clip("spider_bite", 24, hits=[[11 / FPS, 14 / FPS]])
    c.key(0).key(7, body_fwd=-0.08, body_up=0.05, ceph_pitch=14, abd_pitch=-6, fang=1.0, chel=22, chel_spread=12,
                 palp=45, **legs(front=dict(up=0.22, f=0.1)))
    c.key(11, body_fwd=0.38, body_up=-0.1, ceph_pitch=-12, abd_pitch=6, fang=0.15, chel=-8, chel_spread=0, palp=10,
          **legs(front=dict(up=0.05, f=0.46), mid=dict(f=0.15), back=dict(f=0.1)))
    c.key(14, body_fwd=0.34, body_up=-0.09, ceph_pitch=-10, abd_pitch=5, fang=0.0, chel=-10, palp=8,
          **legs(front=dict(up=0.0, f=0.42), mid=dict(f=0.15), back=dict(f=0.1)))
    c.key(24, body_fwd=0, body_up=0, ceph_pitch=0, abd_pitch=0, fang=0, chel=0, palp=0,
          **legs(front=dict(f=0.0), mid=dict(f=0.0), back=dict(f=0.0)))
    c.layer(lambda f, cl: {"ceph.roll": 5 * math.sin(2 * math.pi * f / 5) * pulse(f, 13, 19)})
    C.append(c)
    c = Clip("spider_spit", 36, hits=[[18 / FPS, 20 / FPS]])
    c.key(0).key(12, ceph_pitch=26, body_up=0.1, body_fwd=-0.05, abd_pitch=-18, fang=1.0, chel=24, chel_spread=16,
                 palp=55, **legs(front=dict(up=0.45, f=0.2), L2=dict(up=0.12, f=0.06), R2=dict(up=0.12, f=0.06)))
    c.key(16, ceph_pitch=30, body_up=0.12, body_fwd=-0.07, abd_pitch=-24, abd_scale=0.05, fang=1.0, chel=28,
          chel_spread=18, palp=60, **legs(front=dict(up=0.5, f=0.22), L2=dict(up=0.0), R2=dict(up=0.0)))
    c.key(18, ceph_pitch=10, body_up=0.06, body_fwd=0.12, abd_pitch=8, abd_scale=-0.06, fang=0.7, chel=-18,
          chel_spread=4, palp=30, **legs(front=dict(up=0.3, f=0.3)))
    c.key(20, ceph_pitch=8, body_up=0.05, body_fwd=0.14, abd_pitch=10, abd_scale=-0.05, fang=0.6, chel=-16,
          **legs(front=dict(up=0.24, f=0.3)))
    c.key(27, ceph_pitch=6, body_up=0.02, body_fwd=0.05, abd_pitch=3, abd_scale=0.0, fang=0.4, chel=0,
          chel_spread=2, palp=15, **legs(front=dict(up=0.0, f=0.1)))
    c.key(36, ceph_pitch=0, body_up=0, body_fwd=0, abd_pitch=0, fang=0, chel_spread=0, palp=0,
          **legs(front=dict(f=0.0)))
    C.append(c)
    c = Clip("spider_pounce", 42, hits=[[24 / FPS, 27 / FPS]])
    c.key(0)
    c.key(10, body_up=-0.2, body_pitch=-5, ceph_pitch=-4, abd_pitch=8, fang=0.6, chel_spread=8, palp=20,
          legs_follow=0.0, **legs(front=dict(f=0.05), back=dict(f=-0.04)))
    c.key(14, body_up=0.42, body_fwd=0.5, body_pitch=10, ceph_pitch=10, abd_pitch=-10, fang=1.0, chel_spread=16,
          chel=20, palp=50, legs_follow=1.0, **legs(front=dict(f=0.36, up=0.26), L2=dict(f=0.22, up=0.14),
                                                      R2=dict(f=0.22, up=0.14), back=dict(f=-0.24, up=0.1)))
    c.key(19, body_up=0.55, body_fwd=0.95, body_pitch=-2, ceph_pitch=0, abd_pitch=-4, fang=1.0, chel=24,
          legs_follow=1.0, **legs(front=dict(f=0.5, up=0.12), L2=dict(f=0.2, up=0.1), R2=dict(f=0.2, up=0.1),
                                  back=dict(f=-0.2, up=0.15)))
    c.key(24, body_up=-0.12, body_fwd=1.3, body_pitch=-8, ceph_pitch=-12, abd_pitch=10, fang=0.05, chel=-10,
          chel_spread=0, palp=10, legs_follow=1.0,
          **legs(front=dict(f=0.2, up=0.0), L2=dict(f=0.08, up=0.0), R2=dict(f=0.08, up=0.0), back=dict(f=0.0, up=0.0)))
    c.key(28, body_up=-0.1, body_fwd=1.3, body_pitch=-6, ceph_pitch=-9, abd_pitch=6, fang=0.0, chel=-8,
          legs_follow=1.0, **legs(front=dict(f=0.2), L2=dict(f=0.06), R2=dict(f=0.06)))
    c.key(42, body_up=0, body_fwd=0, body_pitch=0, ceph_pitch=0, abd_pitch=0, fang=0, chel=0, palp=0,
          legs_follow=0.0, **legs(front=dict(f=0.0), L2=dict(f=0.0), R2=dict(f=0.0)))
    C.append(c)
    c = Clip("spider_brood", 60)
    c.key(0).key(12, body_up=-0.06, body_pitch=3, ceph_pitch=-4, abd_pitch=24, legs_spread=0.06, palp=20,
                 **legs(back=dict(f=-0.08, side=0.06)))
    c.key(48, body_up=-0.07, body_pitch=3, ceph_pitch=-5, abd_pitch=26, legs_spread=0.06, palp=22,
          **legs(back=dict(f=-0.08, side=0.06)))
    c.key(60, body_up=0, body_pitch=0, ceph_pitch=0, abd_pitch=0, legs_spread=0, palp=0,
          **legs(back=dict(f=0.0, side=0.0)))
    c.layer(lambda f, cl: {"abd.scale": 0.085 * max(0.0, math.sin(2 * math.pi * (f - 12) / 12)) ** 1.5
                           * (1 if 12 <= f <= 48 else 0),
                           "abd.pitch": 3.0 * math.sin(2 * math.pi * (f - 12) / 12) * (1 if 12 <= f <= 48 else 0),
                           "body.up": -0.012 * max(0.0, math.sin(2 * math.pi * (f - 12) / 12))
                           * (1 if 12 <= f <= 48 else 0)})
    C.append(c)
    return C


# ------------------------------------------------------------------------------------------------ mesh
def build_mesh():
    import bh_mesh as M
    parts = []
    rng = np.random.default_rng(41)

    def add(p, **kw):
        K.bind(p, RIG, **kw)
        parts.append(p)
        return p

    def ring(y, zc, rx, rt, rb, n=20):
        a = np.linspace(0, 2 * math.pi, n, endpoint=False)
        return np.array([(rx * math.cos(t), y, zc + (rt if math.sin(t) > 0 else rb) * math.sin(t)) for t in a])

    def solid(V, F, mat, name):
        p = M.Part(V, F, mat, name=name)
        return M.recalc_normals(p)

    def orient(p, center):
        """Flip faces of an open sheet so they face away from center."""
        F = []
        for f in p.F:
            a, b, c3 = p.V[f[0]], p.V[f[1]], p.V[f[2]]
            n = np.cross(b - a, c3 - a)
            F.append(f if np.dot(n, p.V[list(f)].mean(0) - center) >= 0 else tuple(reversed(f)))
        p.F = F
        return p

    def spike(base, d, length, r, mat="BH_Hair", n=4):
        d = K.unit(d)
        V, F = M.tube([base, base + d * length * 0.5, base + d * length], [(r, r), (r * 0.55, r * 0.55),
                      (0.0015, 0.0015)], n=n, up=(0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0), cap1=False)
        return M.Part(V, F, mat, name="spike")

    # ---- cephalothorax (glossy carapace) + sternum
    CEPH = [(0.05, 0.56, 0.05, 0.035, 0.035), (0.0, 0.57, 0.15, 0.09, 0.1), (-0.12, 0.575, 0.23, 0.13, 0.14),
            (-0.26, 0.58, 0.25, 0.15, 0.155), (-0.4, 0.585, 0.235, 0.155, 0.16), (-0.5, 0.59, 0.2, 0.14, 0.14),
            (-0.57, 0.59, 0.15, 0.115, 0.11), (-0.62, 0.58, 0.09, 0.07, 0.07), (-0.645, 0.575, 0.03, 0.025, 0.025)]
    V, F = M.loft([ring(*r, n=24) for r in CEPH], cap0=True, cap1=True)
    carap = solid(V, F, "BH_Horn", "carapace")
    add(carap, bone="body")
    # sternum / underside (dark, hairy) just under the carapace
    V, F = M.loft([ring(y, zc - 0.012, rx * 0.8, 0.02, rb * 0.9, n=16) for (y, zc, rx, rt, rb) in CEPH[1:7]],
                  cap0=True, cap1=True)
    add(solid(V, F, "BH_Fur", "sternum"), bone="body")
    # radial dark grooves on the carapace + fovea
    for i in range(7):
        a = math.radians(-150 + 300 * i / 6)
        p0 = np.array([0.0, -0.26, 0.74])
        d = np.array([math.sin(a) * 0.2, -math.cos(a) * 0.17, 0.0])
        pts = [p0 + d * 0.35, p0 + d * 0.7, p0 + d]
        pts = [np.array([q[0], q[1], 0.0]) for q in pts]
        for q in pts:          # drop onto the carapace surface (approx)
            q[2] = 0.585 + 0.152 * math.sqrt(max(0.0, 1 - (q[0] / 0.245) ** 2)) + 0.003
        V, F = M.tube(pts, [(0.006, 0.002)] * 3, n=4, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Fur", name="groove"), bone="body")
    # ---- eyes: 8, venom green (two big front medians)
    EYES = [(0.033, -0.622, 0.628, 0.026), (0.086, -0.6, 0.634, 0.019), (0.042, -0.585, 0.69, 0.02),
            (0.1, -0.555, 0.685, 0.017)]
    for (x, y, z, r) in EYES:
        for sx in (1, -1):
            V, F = M.sphere(r, 10, 6, center=(sx * x, y, z))
            add(M.Part(V, F, "BH_Emissive", name="eye"), bone="body")
            V, F = M.sphere(r * 1.25, 10, 4, center=(sx * x, y + 0.004, z + 0.006), scale=(1, 1, 0.55))
            add(M.Part(V, F, "BH_Horn", name="eyebrow"), bone="body")
    # ocular hump
    V, F = M.sphere(0.07, 12, 6, center=(0, -0.58, 0.66), scale=(1.3, 1.0, 0.6))
    add(M.Part(V, F, "BH_Horn", name="ocular"), bone="body")
    # carapace hairs
    for i in range(22):
        x = (rng.random() - 0.5) * 0.4
        y = -0.5 + 0.45 * rng.random()
        z = 0.585 + 0.15 * math.sqrt(max(0.0, 1 - (x / 0.24) ** 2)) - 0.005
        add(spike(np.array([x, y, z]), np.array([x * 2, 0.6, 0.6]), 0.04 + 0.03 * rng.random(), 0.005), bone="body")
    # ---- chelicerae (bulky, hairy), fangs (black), venom drops, mouth
    for s, sx in (("L", 1), ("R", -1)):
        ch = "chel." + s
        pts = [H[ch] + (0, 0.02, 0.02), H[ch] * 0.5 + T[ch] * 0.5 + (sx * 0.008, -0.012, 0), T[ch] + (0, 0.005, 0.01)]
        V, F = M.tube(pts, [(0.05, 0.056), (0.052, 0.05), (0.036, 0.034)], n=10, up=(0, -1, 0))
        add(M.Part(V, F, "BH_Fur", name="chel"), bone=ch)
        for i in range(5):
            b = H[ch] * (1 - 0.2 * i) + T[ch] * 0.2 * i + np.array([sx * 0.03, -0.035, 0.0])
            add(spike(b, np.array([sx * 0.4, -1.0, 0.1]), 0.035, 0.005), bone=ch)
        fg = "fang." + s
        a, b = H[fg], T[fg]
        mid = a * 0.5 + b * 0.5 + np.array([sx * 0.006, -0.012, -0.012])
        V, F = M.tube([a, mid, b], [(0.02, 0.02), (0.013, 0.013), (0.002, 0.002)], n=6, up=(1, 0, 0))
        add(M.Part(V, F, "BH_Shadow", name="fang"), bone=fg)
        V, F = M.sphere(0.008, 6, 4, center=b + (0, 0, -0.006), scale=(1, 1, 1.4))
        add(M.Part(V, F, "BH_Emissive", name="venom"), bone=fg)
        # pedipalps
        p1, p2 = "palp.1." + s, "palp.2." + s
        V, F = M.tube([H[p1], T[p1], T[p2]], [(0.03, 0.03), (0.026, 0.026), (0.02, 0.02)], n=8, up=(1, 0, 0))
        add(M.Part(V, F, "BH_Fur", name="palp"), chain=[p1, p2], blend=0.3)
        V, F = M.sphere(0.026, 8, 5, center=T[p2], scale=(1, 1, 1.3))
        add(M.Part(V, F, "BH_Horn", name="palp_tip"), bone=p2)
        for i in range(3):
            add(spike(T[p1] * (0.3 + 0.3 * i) + H[p1] * (0.7 - 0.3 * i) + (0, 0, 0.02), np.array([sx * 0.3, 0.2, 1]),
                      0.035, 0.004), bone=p1)
    V, F = M.sphere(0.05, 10, 5, center=(0, -0.6, 0.47), scale=(1.1, 0.7, 0.7))
    add(M.Part(V, F, "BH_Shadow", name="mouth"), bone="body")

    # ---- abdomen: big egg-shaped bulb with warning markings, hair tufts, egg sacs, spinnerets
    AC = np.array([0.0, 0.5, 0.7])
    AR = np.array([0.42, 0.52, 0.40])

    def abd(u, v, off=0.0):
        """u 0..1 front->rear, v angle from the top (+ = toward +X). Returns (point, normal)."""
        egg = 1.0 + 0.14 * (u - 0.45)
        rho = math.sin(math.pi * u)
        p = np.array([AR[0] * egg * rho * math.sin(v), AC[1] - AR[1] * math.cos(math.pi * u),
                      AC[2] + AR[2] * egg * rho * math.cos(v)])
        n = K.unit(np.array([(p[0]) / (AR[0] * egg) ** 2, (p[1] - AC[1]) / AR[1] ** 2,
                             (p[2] - AC[2]) / (AR[2] * egg) ** 2]))
        return p + n * off, n
    NU, NV = 18, 28
    rings = []
    for i in range(1, NU):
        u = i / NU
        rings.append(np.array([abd(u, 2 * math.pi * j / NV)[0] for j in range(NV)]))
    V, F = M.loft(rings, cap0=True, cap1=True)
    add(solid(V, F, "BH_Fur", "abdomen"), bone="abdomen")
    # pedicel
    V, F = M.tube([(0, 0.07, 0.6), (0, 0.02, 0.575), (0, -0.04, 0.565)], [(0.07, 0.06), (0.06, 0.05), (0.07, 0.06)],
                  n=10, up=(0, 0, 1))
    add(M.Part(V, F, "BH_Fur", name="pedicel"), bones=["body", "abdomen"], power=4)

    def sheet(fn, nu, nv, mat="BH_Flesh", name="mark"):
        V, F = M.grid(fn, nu, nv)
        return orient(M.Part(V, F, mat, name=name), AC)

    # dorsal chevrons (V tips forward)
    for i in range(5):
        u0 = 0.3 + 0.12 * i
        vw = 0.62 - 0.07 * i
        du = 0.05 - 0.005 * i

        def chev(a, b, u0=u0, vw=vw, du=du):
            v = (a - 0.5) * 2 * vw
            u = u0 + 0.09 * abs(v) / vw + b * du
            return abd(u, v, 0.005)[0]
        add(sheet(chev, 11, 3), bone="abdomen")
    # lateral stripes + a front crescent
    for sx in (1, -1):
        def stripe(a, b, sx=sx):
            u = 0.18 + 0.66 * a
            v = sx * (1.25 + 0.12 * math.sin(math.pi * a) + (b - 0.5) * 0.16 * math.sin(math.pi * a + 0.2))
            return abd(u, v, 0.005)[0]
        add(sheet(stripe, 14, 2), bone="abdomen")
        for j in range(3):          # spots
            u, v = 0.3 + 0.2 * j, sx * (0.62 + 0.1 * j)

            def spot(a, b, u=u, v=v):
                ang = 2 * math.pi * a
                r = 0.035 * max(b, 0.1)
                return abd(u + r * math.cos(ang) * 1.2, v + r * math.sin(ang) * 2.0, 0.005)[0]
            add(sheet(spot, 9, 2), bone="abdomen")

    def crescent(a, b):
        v = (a - 0.5) * 1.6
        return abd(0.16 + 0.03 * b + 0.05 * (v / 0.8) ** 2, v, 0.005)[0]
    add(sheet(crescent, 11, 2), bone="abdomen")
    # hair tufts (coarse, swept back)
    for i in range(40):
        u = 0.12 + 0.8 * rng.random()
        v = (rng.random() - 0.5) * 2 * 2.2
        p, n = abd(u, v, -0.004)
        d = n * 0.8 + np.array([0.0, 0.7, 0.0]) + rng.normal(size=3) * 0.15
        for j in range(3):
            q = p + rng.normal(size=3) * 0.012
            add(spike(q, d + rng.normal(size=3) * 0.2, 0.06 + 0.05 * rng.random(), 0.007), bone="abdomen")
    # spinnerets
    for sx in (1, -1):
        p, n = abd(0.965, math.pi * 0.85 * sx, -0.01)
        V, F = M.tube([p, p + np.array([sx * 0.02, 0.05, -0.02])], [(0.02, 0.02), (0.008, 0.008)], n=6,
                      up=(0, 0, 1))
        add(M.Part(V, F, "BH_Horn", name="spinneret"), bone="abdomen")
    # egg sacs: lumpy silk balls clinging to the lower flanks / rear, wrapped in threads
    for (u, v, r) in ((0.62, 1.95, 0.13), (0.72, -1.9, 0.115), (0.9, 2.75, 0.09)):
        p, n = abd(u, v)
        c0 = p + n * r * 0.45
        V, F = M.sphere(r, 12, 8, center=(0, 0, 0))
        V = V * (1.0 + 0.06 * np.sin(V[:, 0] * 60) * np.cos(V[:, 1] * 50) + 0.04 * np.sin(V[:, 2] * 70))[:, None]
        V = V * np.array([1.0, 1.1, 0.92]) + c0
        add(M.Part(V, F, "BH_Bone", name="eggsac"), bone="abdomen")
        for j in range(3):
            ax = K.unit(rng.normal(size=3))
            ref = K.unit(np.cross(ax, [0.3, 0.2, 0.9]))
            ref2 = np.cross(ax, ref)
            pts = [c0 + (ref * math.cos(t) + ref2 * math.sin(t)) * r * 1.03 for t in np.linspace(0.3, 2.6, 6)]
            V, F = M.tube(pts, [(0.004, 0.004)] * 6, n=4, up=tuple(ax))
            add(M.Part(V, F, "BH_Bone", name="silk"), bone="abdomen")
    # ---- legs: banded, hairy, clean joints (chain weights), knee knobs
    for k, (cx, fe, ti, ta) in LEGS.items():
        n = int(k[1])
        sc = LEG_SPEC[n][2] / 1.0
        pts, prof = [], []
        segs = [(cx, 2, 0.056, 0.054), (fe, 5, 0.052, 0.042), (ti, 5, 0.041, 0.03), (ta, 5, 0.028, 0.011)]
        pts.append(H[cx] - RIG.rdir(cx) * 0.02)
        prof.append((0.05 * sc, 0.05 * sc))
        for b, nseg, r0, r1 in segs:
            for i in range(1, nseg + 1):
                t = i / nseg
                pts.append(H[b] * (1 - t) + T[b] * t)
                r = (r0 * (1 - t) + r1 * t) * (0.85 + 0.15 * sc)
                prof.append((r, r * 1.08))
        prof[-1] = (0.004, 0.004)
        V, F = M.tube(pts, prof, n=8, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Fur", name="leg"), chain=[cx, fe, ti, ta], blend=0.28)
        # warning bands at the end of the femur and the tibia + knee knobs
        for b, t0, t1, r in ((fe, 0.84, 0.98, 0.047), (ti, 0.82, 0.97, 0.036)):
            q = [H[b] * (1 - t) + T[b] * t for t in (t0, (t0 + t1) / 2, t1)]
            V, F = M.tube(q, [(r, r * 1.08)] * 3, n=8, up=(0, 0, 1))
            add(M.Part(V, F, "BH_Flesh", name="band"), chain=[fe, ti, ta], blend=0.28)
        V, F = M.sphere(0.047, 8, 5, center=T[fe])
        add(M.Part(V, F, "BH_Fur", name="knee"), chain=[fe, ti], blend=0.5)
        V, F = M.sphere(0.034, 8, 4, center=T[ti])
        add(M.Part(V, F, "BH_Fur", name="ankle"), chain=[ti, ta], blend=0.5)
        # claw tip
        d = RIG.rdir(ta)
        V, F = M.tube([T[ta] - d * 0.03, T[ta] + d * 0.008 + np.array([0, 0, -0.004])], [(0.012, 0.012),
                      (0.002, 0.002)], n=5, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Horn", name="claw"), bone=ta)
        # spines along femur and tibia (outer/upper side)
        out = K.unit(np.cross(RIG.rdir(fe), np.cross(np.array([0, 0, 1.0]), RIG.rdir(fe))))
        for b, cnt in ((fe, 6), (ti, 6), (ta, 3)):
            d = RIG.rdir(b)
            side = K.unit(np.cross(d, [0, 0, 1.0]))
            for i in range(cnt):
                t = (i + 0.5) / cnt
                ang = rng.random() * 2 * math.pi
                nrm = K.unit(side * math.cos(ang) + np.cross(side, d) * math.sin(ang))
                base = H[b] * (1 - t) + T[b] * t + nrm * 0.03
                add(spike(base, nrm * 0.8 + d * 0.9, 0.05 + 0.03 * rng.random(), 0.006), bone=b)
    return parts


# ------------------------------------------------------------------------------------------------ analysis
def foot_slide(clip, ev, feet_fn, ids, speed, floor):
    """Stance-foot slip vs the ideal in-place slide (+speed along +Y). Returns (max m/frame, mean, contact frac)."""
    P = []
    for f in range(clip.frames + 1):
        X = ev(clip.channels(float(f % clip.frames)))
        P.append({k: feet_fn(X, k) for k in ids})
    res = []
    cont = 0
    for f in range(clip.frames):
        for k in ids:
            a, b = P[f][k], P[f + 1][k]
            if a[2] < floor and b[2] < floor:
                cont += 1
                res.append(np.linalg.norm((b - a) - np.array([0.0, speed / FPS, 0.0])))
    return (max(res) if res else 0.0), (float(np.mean(res)) if res else 0.0), cont / (clip.frames * len(ids))


def reach_report(clip):
    """Largest foot-target miss in a clip (IK reach), meters."""
    worst = 0.0
    for f in range(clip.frames + 1):
        c = clip.channels(float(f % clip.frames if clip.loop else f))
        X = evaluate(c)
        for k in LEG_IDS:
            if c.get("legs.curl", 0.0) + c.get(k + ".curl", 0.0) > 0.01:
                continue
            off = np.array([0.0, -(c.get(k + ".f", 0.0) + c.get("legs.f", 0.0)),
                            c.get(k + ".up", 0.0) + c.get("legs.up", 0.0)])
            off = off + OUTW[k] * (c.get(k + ".side", 0.0) + c.get("legs.spread", 0.0))
            tw = NEUTRAL[k] + off
            w = min(max(c.get("legs.follow", 0.0) + c.get(k + ".follow", 0.0), 0.0), 1.0)
            tgt = tw * (1 - w) + X["root"].apply(tw) * w
            tgt[2] = max(tgt[2], FLOOR)
            worst = max(worst, float(np.linalg.norm(foot(X, k) - tgt)))
    return worst


def wolf_slide():
    try:
        import build_wolf as W
    except Exception as e:
        return {"error": str(e)}
    out = {}
    for c in W.clips():
        if c.name not in ("walk", "run"):
            continue

        def ev(ch):
            return W.evaluate(ch)[1]

        def ff(X, k):
            return X[W.LEGS[k][4]].apply(W.H[W.LEGS[k][4]])
        floor = W.H["ftoe.L"][2] + 0.012
        out[c.name] = foot_slide(c, ev, ff, list(W.LEGS), c.meta["ground_speed"], floor)
    return out


# ------------------------------------------------------------------------------------------------ main
def main():
    a = K.std_args()
    import bh_mesh as M
    C = clips()
    only = set(x for x in a.clips.split(",") if x) or None
    arm, mesh, acts = K.build_all(CID, RIG, evaluate, C, build_mesh, PALETTE, only=only, ao=(16, 0.3, 0.6))
    tris = M.tri_count(mesh)
    print(f"[{CID}] mesh {tris} tris, {len(mesh.data.vertices)} verts, {len(RIG.ORDER)} bones, {len(acts)} clips")
    # foot sliding (vs the wolf, same metric) + IK reach
    slide = {}
    for c in C:
        if "ground_speed" in c.meta:
            slide[c.name] = foot_slide(c, evaluate, foot, LEG_IDS, c.meta["ground_speed"], FLOOR + 0.012)
    wolf = wolf_slide()
    reach = {c.name: reach_report(c) for c in C}
    for n, v in slide.items():
        print(f"[{CID}] foot slip {n}: max {v[0] * 1000:.2f} mm/frame, mean {v[1] * 1000:.2f}, stance {v[2]:.2f}")
    for n, v in wolf.items():
        print(f"[dire_wolf] foot slip {n}: {v}")
    print(f"[{CID}] worst IK reach miss per clip (mm): " +
          ", ".join(f"{n} {v * 1000:.1f}" for n, v in reach.items()))
    K.quick_preview(CID, arm, acts, a, 0.5, 4.6)
    if a.evidence:
        K.evidence_rest(CID, arm, 0.5, 4.6, "Broodmother - rest (4 views + 3/4 + gameplay iso at 1.0 and 0.42 "
                        "Spiderling scale)", iso_scales=(1.0, 0.42))
        K.evidence_rest(CID, arm, 0.5, 4.6, "Broodmother - idle frame 0", pose=("idle", 0), acts=acts,
                        iso_scales=(1.0,))
        spec = [("walk", [0, 0.25, 0.5, 0.75]), ("run", [0, 0.25, 0.5, 0.75]),
                ("spider_bite", [0, 7 / 24, 11 / 24, 14 / 24, 1.0]),
                ("spider_spit", [12 / 36, 16 / 36, 18 / 36, 27 / 36]),
                ("spider_pounce", [10 / 42, 14 / 42, 19 / 42, 24 / 42, 34 / 42]),
                ("spider_brood", [0.2, 0.3, 0.45, 0.6]),
                ("death", [0.13, 0.27, 0.45, 1.0]), ("death_back", [0.18, 0.4, 1.0]),
                ("alert", [0.3, 0.66]), ("hit_heavy", [0.22]), ("knockback", [0.4]), ("idle_look", [0.2, 0.6])]
        K.evidence_clips(CID, arm, acts, spec, 0.55, 6.2, "Broodmother - clips (view yaw 55)", yaw=55, cols=6)
        K.evidence_clips(CID, arm, acts, [("walk", [i / 8 for i in range(8)])], 0.45, 4.6,
                         "Broodmother - walk cycle, side view (ground_speed 1.6 m/s)", yaw=90, pitch=6,
                         name="walk_side", cols=8)
    if not a.no_export and not only:
        K.merge_meta(CID, C, "tools/blender/creatures/build_broodmother.py",
                     {"spiderling_scale": 0.42, "tris": tris, "bones": len(RIG.ORDER)})
        bad, got = K.export(CID, arm, mesh, acts, OUT_GLB)
        assert not bad, bad
    notes = [f"Generator: `tools/blender/creatures/build_broodmother.py` -> `game/assets/characters/{CID}.glb`",
             "", f"- Size: abdomen top 1.10 m, leg span ~2.6 m (L1 foot to R4 foot); Spiderling = same GLB x0.42.",
             f"- Triangles: {tris}; vertices {len(mesh.data.vertices)}; bones {len(RIG.ORDER)} (root non-deform).",
             f"- Materials: {', '.join(sorted(m.name for m in mesh.data.materials))}",
             "- Bones: " + ", ".join(f"`{b}`" for b in RIG.ORDER), "",
             "## Clips", ""] + K.clip_table(C) + [
             "", "## Foot contact (in-place clips; stance feet should slide back at exactly ground_speed)", "",
             "| clip | max slip mm/frame | mean slip mm/frame | stance fraction |", "|---|---|---|---|"] + [
             f"| {n} | {v[0] * 1000:.2f} | {v[1] * 1000:.2f} | {v[2]:.2f} |" for n, v in slide.items()] + [
             f"| dire_wolf {n} (same metric) | {v[0] * 1000:.2f} | {v[1] * 1000:.2f} | {v[2]:.2f} |"
             for n, v in wolf.items() if isinstance(v, tuple)] + [
             "", "Worst IK reach miss per clip (mm; legs in FK curl excluded): " +
             ", ".join(f"{n} {v * 1000:.1f}" for n, v in reach.items())]
    K.write_md(CID, "Broodmother (broodmother.glb)", notes)


if __name__ == "__main__":
    main()
