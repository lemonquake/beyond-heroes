"""Reef Crawler (bh-012, Builder A; Saltmouth Deeps shell tank): a giant armoured crab ~1.6 m wide, ~0.9 m tall.
Domed carapace crusted with barnacles, coral growths and seaweed, spined front margin, two big pincers at the front
(the right one larger), six walking legs, eye stalks with small teal-glowing eyes, mandible plates.

  blender -b --factory-startup --python build_reef_crawler.py -- [--evidence] [--no-export] [--clips a,b] [--prev DIR]

Conventions (creature_kit_c / build_broodmother): Blender Z-up, faces -Y (= +Z in Godot), origin on the ground under
the body, meters, 30 fps, clips in place. Legs: 4 bones each (coxa / femur / tibia / tarsus) solved per frame with
creature_kit_c.plane_leg; stance feet world-fixed (alternating tripod gait L1 R2 L3 / R1 L2 R3). Pincers: FK chains
claw.1 (merus) -> claw.2 (carpus) -> claw.3 (palm + fixed finger) -> claw.4 (movable finger / dactyl).
Attack clips (stem `crab_`): crab_snap (quick right-pincer strike), crab_slam (both pincers hammer down),
crab_guard (pincers raised in front of the face; one-shot, holds the guard in the middle).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import creature_kit_c as K  # noqa: E402
from creature_kit_c import Clip, Xf, Rx, Ry, Rz, cyc, pulse, spine_rot, smooth, FPS  # noqa: E402

import numpy as np  # noqa: E402

CID = "reef_crawler"
OUT_GLB = os.path.join(K.CHAR_OUT, f"{CID}.glb")
EVID = os.path.join(K.ROOT_DIR, "work", "lemondev", "bh-012", "evidence", "models_deeps")
PALETTE = {
    "BH_Leather": ((0.17, 0.23, 0.24), 0.0, 0.45, None, 0.0, 1.0),       # drowned blue-grey shell (carapace, legs)
    "BH_Stone": ((0.34, 0.39, 0.37), 0.0, 0.85, None, 0.0, 1.0),         # pale lime-crust mottles
    "BH_Flesh": ((0.5, 0.47, 0.4), 0.0, 0.55, None, 0.0, 1.0),           # pale underside / joints
    "BH_Bone": ((0.72, 0.72, 0.66), 0.0, 0.85, None, 0.0, 1.0),          # barnacles, claw teeth
    "BH_Horn": ((0.64, 0.45, 0.41), 0.0, 0.8, None, 0.0, 1.0),           # coral
    "BH_Fur": ((0.06, 0.15, 0.07), 0.0, 0.55, None, 0.0, 1.0),           # seaweed
    "BH_DarkSteel": ((0.04, 0.05, 0.055), 0.2, 0.4, None, 0.0, 1.0),     # dark claw / leg tips
    "BH_Shadow": ((0.012, 0.015, 0.018), 0.0, 0.4, None, 0.0, 1.0),      # mouth, barnacle apertures
    "BH_Emissive": ((0.2, 0.95, 0.85), 0.0, 0.35, (0.2, 0.95, 0.85), 7.0, 1.0),   # teal eyes / polyps
}

# ------------------------------------------------------------------------------------------------ skeleton
PIVOT = np.array([0.0, -0.05, 0.5])
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.25), None),
    "body": ((0, 0.25, 0.52), (0, -0.4, 0.52), "root"),
}
CLAW_S = {"L": 0.85, "R": 1.1}          # the right pincer is larger
for _s, _x in (("L", 1.0), ("R", -1.0)):
    k = CLAW_S[_s]
    sh = np.array([0.22 * _x, -0.33, 0.49])
    el = sh + np.array([0.15 * _x, -0.14, 0.1]) * k
    wr = el + np.array([-0.08 * _x, -0.17, -0.02]) * k
    tip = wr + np.array([-0.03 * _x, -0.2, -0.06]) * k
    hinge = wr + (tip - wr) * 0.62 + np.array([0, 0, 0.05]) * k
    BONES.update({
        f"claw.1.{_s}": (tuple(sh), tuple(el), "body"),
        f"claw.2.{_s}": (tuple(el), tuple(wr), f"claw.1.{_s}"),
        f"claw.3.{_s}": (tuple(wr), tuple(tip), f"claw.2.{_s}"),
        f"claw.4.{_s}": (tuple(hinge), tuple(hinge + np.array([-0.02 * _x, -0.2, -0.035]) * k), f"claw.3.{_s}"),
        f"eye.{_s}": ((0.075 * _x, -0.4, 0.6), (0.09 * _x, -0.44, 0.74), "body"),
        f"mand.{_s}": ((0.035 * _x, -0.43, 0.5), (0.03 * _x, -0.47, 0.42), "body"),
    })
# walking legs n: (attach on the L side, azimuth deg (+ = toward the front), foot reach)
LEG_SPEC = {1: ((0.4, -0.16, 0.46), 24.0, 0.5), 2: ((0.45, 0.0, 0.46), -8.0, 0.54),
            3: ((0.4, 0.16, 0.46), -40.0, 0.5)}
LEGS = {}
for _s, _x in (("L", 1.0), ("R", -1.0)):
    for _n, (_p, _az, _R) in LEG_SPEC.items():
        _P = np.array([_p[0] * _x, _p[1], _p[2]])
        _u = np.array([_x * math.cos(math.radians(_az)), -math.sin(math.radians(_az)), 0.0])

        def _pt(r, z, P=_P, u=_u):
            return tuple(P + u * r + np.array([0.0, 0.0, z - P[2]]))
        names = (f"coxa.{_n}.{_s}", f"femur.{_n}.{_s}", f"tibia.{_n}.{_s}", f"tarsus.{_n}.{_s}")
        pts = [tuple(_P), _pt(0.06, _P[2] + 0.03), _pt(0.5 * _R, 0.68), _pt(0.86 * _R, 0.3), _pt(_R, 0.015)]
        for i, nm in enumerate(names):
            BONES[nm] = (pts[i], pts[i + 1], "body" if i == 0 else names[i - 1])
        LEGS[f"{_s}{_n}"] = names
# everything above is authored at 1/SIZE; the rig, the mesh and the pivot are scaled uniformly to the final size
SIZE = 0.82
RIG0 = K.Rig(BONES)
H0, T0 = RIG0.H, RIG0.T
BONES = {b: (tuple(np.array(h) * SIZE), tuple(np.array(t) * SIZE), p) for b, (h, t, p) in BONES.items()}
PIVOT = PIVOT * SIZE
RIG = K.Rig(BONES)
H, T = RIG.H, RIG.T
LEG_IDS = [f"{s}{n}" for n in (1, 2, 3) for s in ("L", "R")]
NEUTRAL = {k: T[v[3]].copy() for k, v in LEGS.items()}
OUTW = {k: K.unit(np.array([(T[v[3]] - H[v[0]])[0], (T[v[3]] - H[v[0]])[1], 0.0])) for k, v in LEGS.items()}
BETA = {k: math.degrees(math.atan2(H[v[3]][2] - T[v[3]][2],
                                   np.linalg.norm((T[v[3]] - H[v[3]])[:2]))) for k, v in LEGS.items()}
GROUP_A = ("L1", "R2", "L3")
CURL = (-40.0, -150.0, 140.0)
FLOOR = 0.015


# ------------------------------------------------------------------------------------------------ pose
def evaluate(c):
    X = {}
    g = c.get
    t = np.array([g("body.side", 0.0), -g("body.fwd", 0.0), g("body.up", 0.0)])
    X["root"] = Xf.move(t) @ Xf.about(spine_rot(c, "body"), PIVOT)
    RIG.fk(X, "body", spine_rot(c, "shell"))
    for s, sx in (("L", 1.0), ("R", -1.0)):
        def ch(n, s=s):
            return g("claw." + n, 0.0) + g(f"claw.{s}.{n}", 0.0)
        RIG.fk(X, f"claw.1.{s}", Rz(sx * ch("yaw")) @ Rx(-ch("lift")))
        RIG.fk(X, f"claw.2.{s}", Rz(-sx * ch("fold")) @ Rx(-ch("bend")))
        RIG.fk(X, f"claw.3.{s}", Rx(-ch("wrist")) @ Ry(sx * ch("roll")))
        RIG.fk(X, f"claw.4.{s}", Rx(-38.0 * ch("open")))
        RIG.fk(X, f"eye.{s}", Rx(-g("eyes", 0.0) - g("eye." + s, 0.0)) @ Rz(sx * g("eyes.out", 0.0)))
        RIG.fk(X, f"mand.{s}", Rz(sx * 22.0 * g("mand", 0.0)) @ Rx(-12.0 * g("mand", 0.0)))
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
def gait_layer(period, duty, speed, lift):
    sweep = speed * duty * period / FPS

    def fn(f, clip):
        out = {}
        t = f / period
        for k in LEG_IDS:
            ph = (0.0 if k in GROUP_A else 0.5) + 0.03 * (3 - int(k[1]))
            ff, up, sw = K.gait_foot(t - ph, duty, sweep, lift)
            out[k + ".f"] = ff
            out[k + ".up"] = up
            out[k + ".beta"] = -12.0 * math.sin(math.pi * sw) if sw >= 0 else 0.0
        return out
    return fn


def legs(**kw):
    out = {}
    groups = {"front": ("L1", "R1"), "mid": ("L2", "R2"), "back": ("L3", "R3"), "all": tuple(LEG_IDS),
              "L1": ("L1",), "R1": ("R1",), "L2": ("L2",), "R2": ("R2",), "L3": ("L3",), "R3": ("R3",)}
    for gname, d in kw.items():
        for k in groups[gname]:
            for chn, v in d.items():
                out[f"{k}_{chn}"] = v
    return out


# claw pose presets (channels without the claw_ prefix)
READY = dict(claw_yaw=0.0, claw_lift=0.0, claw_fold=0.0, claw_wrist=0.0, claw_open=0.0)


def clips():
    C = []
    # ---- idle: breathing shell, claws flex, eye stalks and mandibles twitch
    c = Clip("idle", 90, loop=True)
    c.key(0)
    c.layer(lambda f, cl: {"body.up": 0.008 * cyc(f, 90, 2), "shell.pitch": 1.2 * cyc(f, 90, 1, 0.2),
                           "claw.lift": 3.0 * cyc(f, 90, 2, 0.1), "claw.R.open": 0.25 * max(0.0, cyc(f, 90, 3)) ** 2,
                           "claw.L.open": 0.2 * max(0.0, cyc(f, 90, 2, 0.4)) ** 2,
                           "eye.L": 10 * cyc(f, 90, 3), "eye.R": 10 * cyc(f, 90, 2, 0.3),
                           "mand": 0.5 + 0.5 * cyc(f, 30, 1)})
    C.append(c)
    # ---- idle_look: shell turns left / right, eyes swivel, claws feel
    c = Clip("idle_look", 75)
    c.key(0).key(15, body_yaw=14, eyes_out=16, eyes=-10, claw_L_lift=10, claw_L_open=0.5)
    c.key(32, body_yaw=15, eyes_out=18, eyes=-8, claw_L_lift=4, claw_L_open=0.0)
    c.key(48, body_yaw=-13, eyes_out=-10, eyes=-10, claw_L_lift=0, claw_R_lift=10, claw_R_open=0.5)
    c.key(62, body_yaw=-12, eyes_out=-8, claw_R_lift=4, claw_R_open=0.0)
    c.key(75, body_yaw=0, eyes_out=0, eyes=0, claw_R_lift=0)
    c.layer(lambda f, cl: {"mand": 0.5 + 0.5 * cyc(f, 25, 1)})
    C.append(c)
    # ---- walk / run: alternating tripod, claws carried in front
    WP, WV = 22, 1.4
    c = Clip("walk", WP, loop=True, ground_speed=WV)
    c.key(0)
    c.layer(gait_layer(WP, 0.6, WV, 0.14))
    c.layer(lambda f, cl: {"body.up": -0.01 + 0.01 * cyc(f, WP, 2, 0.1), "body.roll": 2.0 * cyc(f, WP, 1, 0.1),
                           "shell.yaw": 1.5 * cyc(f, WP, 1, 0.25), "claw.lift": 6 + 3 * cyc(f, WP, 1),
                           "claw.L.yaw": 4 * cyc(f, WP, 1), "claw.R.yaw": -4 * cyc(f, WP, 1),
                           "eyes": 6 * cyc(f, WP, 2), "mand": 0.3})
    C.append(c)
    for nm, v, crouch in (("run", 3.8, -0.04), ("run_combat", 3.4, -0.08)):
        RP = 12
        c = Clip(nm, RP, loop=True, ground_speed=v)
        c.key(0)
        c.layer(gait_layer(RP, 0.48, v, 0.16))
        c.layer(lambda f, cl, cr=crouch: {
            "body.up": cr + 0.014 * cyc(f, RP, 2, 0.15), "body.pitch": -2.0 + 1.5 * cyc(f, RP, 2, 0.4),
            "body.roll": 2.5 * cyc(f, RP, 1, 0.1), "claw.lift": 12 + (10 if cr < -0.06 else 0),
            "claw.fold": 8.0 if cr < -0.06 else 0.0, "claw.open": 0.4 if cr < -0.06 else 0.1, "eyes": -8.0,
            "mand": 0.6})
        C.append(c)
    # ---- reactions
    c = Clip("hit_light", 12)
    c.key(0).key(3, body_fwd=-0.05, body_up=0.02, body_pitch=5, claw_lift=12, claw_open=0.4, eyes=20, legs_follow=0.3)
    c.key(12, body_fwd=0, body_up=0, body_pitch=0, claw_lift=0, claw_open=0, eyes=0, legs_follow=0)
    C.append(c)
    c = Clip("hit_heavy", 18)
    c.key(0).key(4, body_fwd=-0.12, body_up=-0.04, body_pitch=9, body_roll=5, claw_lift=24, claw_yaw=14,
                 claw_open=0.8, eyes=35, legs_spread=0.05, legs_follow=0.4, mand=1.0)
    c.key(9, body_fwd=-0.1, body_up=-0.06, body_pitch=4, body_roll=2, claw_lift=10, claw_yaw=6, claw_open=0.4,
          eyes=15, legs_spread=0.06, legs_follow=0.3)
    c.key(18, body_fwd=0, body_up=0, body_pitch=0, body_roll=0, claw_lift=0, claw_yaw=0, claw_open=0, eyes=0,
          legs_spread=0, legs_follow=0, mand=0)
    C.append(c)
    c = Clip("stagger_small", 24)
    c.key(0).key(5, body_fwd=-0.07, body_side=-0.06, body_roll=-8, body_yaw=-8, claw_R_lift=16, claw_L_lift=6,
                 claw_open=0.5, legs_follow=0.35, **legs(R2=dict(up=0.1), L1=dict(up=0.08)))
    c.key(10, body_fwd=-0.08, body_side=-0.08, body_roll=-5, body_yaw=-6, claw_R_lift=8, claw_L_lift=2,
          legs_follow=0.3, **legs(R2=dict(up=0.0, side=0.08), L1=dict(up=0.0, f=-0.04)))
    c.key(16, body_fwd=-0.04, body_side=-0.03, body_roll=-2, body_yaw=-2, legs_follow=0.15)
    c.key(24, body_fwd=0, body_side=0, body_roll=0, body_yaw=0, claw_R_lift=0, claw_L_lift=0, claw_open=0,
          legs_follow=0, **legs(R2=dict(side=0.0), L1=dict(f=0.0)))
    C.append(c)
    c = Clip("knockback", 27)
    c.key(0).key(4, body_fwd=-0.2, body_up=0.06, body_pitch=12, claw_lift=30, claw_yaw=18, claw_open=0.9, eyes=35,
                 legs_follow=0.7, **legs(front=dict(up=0.2, f=0.08), mid=dict(up=0.06)))
    c.key(11, body_fwd=-0.36, body_up=-0.05, body_pitch=2, claw_lift=8, claw_yaw=8, claw_open=0.3, eyes=10,
          legs_follow=0.85, **legs(front=dict(up=0.0, f=0.1), mid=dict(up=0.0)))
    c.key(18, body_fwd=-0.18, body_up=-0.02, body_pitch=0, claw_lift=2, claw_yaw=2, legs_follow=0.6,
          **legs(front=dict(f=0.03)))
    c.key(27, body_fwd=0, body_up=0, claw_lift=0, claw_yaw=0, claw_open=0, eyes=0, legs_follow=0,
          **legs(front=dict(f=0.0)))
    C.append(c)
    # ---- deaths
    c = Clip("death", 45)          # legs buckle, it tips over onto its back, legs curl
    c.key(0)
    c.key(6, body_up=-0.12, claw_lift=-10, claw_open=0.9, eyes=30, legs_spread=0.08, legs_curl=0.1, mand=1.0)
    c.key(13, body_up=0.12, body_side=0.12, body_roll=65, claw_lift=20, claw_yaw=20, legs_follow=0.8, legs_curl=0.45)
    c.key(21, body_up=-0.05, body_side=0.22, body_roll=172, body_pitch=-4, claw_lift=30, claw_yaw=24, claw_fold=20,
          legs_follow=1.0, legs_curl=0.85)
    c.key(26, body_up=-0.09, body_side=0.22, body_roll=184, body_pitch=-6, claw_lift=34, claw_fold=26,
          legs_follow=1.0, legs_curl=1.0, claw_open=0.5)
    c.key(45, body_up=-0.08, body_side=0.22, body_roll=180, body_pitch=-6, claw_lift=36, claw_yaw=24, claw_fold=30,
          legs_follow=1.0, legs_curl=1.0, claw_open=0.3, eyes=40, mand=0.0)
    c.layer(lambda f, cl: {k + ".curl": 0.12 * pulse(f, 28 + 2 * i, 40 + 2 * i) * (1 if i % 2 else -1)
                           for i, k in enumerate(LEG_IDS)})
    C.append(c)
    c = Clip("death_back", 45)     # rears, then drops flat, legs splay, claws slump to the ground
    c.key(0)
    c.key(8, body_up=0.06, body_fwd=-0.05, body_pitch=14, claw_lift=30, claw_yaw=16, claw_open=1.0, eyes=35,
          **legs(front=dict(up=0.2, f=0.08)))
    c.key(18, body_up=-0.26, body_fwd=-0.03, body_pitch=-3, claw_lift=-14, claw_yaw=22, claw_open=0.6, eyes=10,
          legs_spread=0.28, **legs(front=dict(up=0.0, f=0.14)))
    c.key(24, body_up=-0.3, body_pitch=-5, claw_lift=-20, claw_yaw=26, claw_open=0.5, eyes=45, legs_spread=0.4,
          legs_curl=0.2, **legs(front=dict(f=0.16)))
    c.key(45, body_up=-0.31, body_pitch=-6, claw_lift=-22, claw_yaw=28, claw_open=0.4, eyes=55, legs_spread=0.42,
          legs_curl=0.35, **legs(front=dict(f=0.16)))
    C.append(c)
    # ---- alert: rear up, pincers raised wide and open, eyes up
    c = Clip("alert", 30)
    c.key(0).key(9, body_up=0.06, body_pitch=10, claw_lift=40, claw_yaw=24, claw_wrist=20, claw_open=1.0, eyes=-18,
                 eyes_out=10, mand=1.0, **legs(front=dict(f=-0.04)))
    c.key(20, body_up=0.05, body_pitch=8, claw_lift=36, claw_yaw=20, claw_wrist=16, claw_open=0.7, eyes=-14,
          eyes_out=8, **legs(front=dict(f=-0.04)))
    c.key(30, body_up=0.0, body_pitch=0, claw_lift=6, claw_yaw=4, claw_wrist=2, claw_open=0.1, eyes=0, eyes_out=0,
          mand=0.2, **legs(front=dict(f=0.0)))
    c.layer(lambda f, cl: {"claw.open": 0.35 * max(0.0, cyc(f, 8, 1)) * (1 if 8 < f < 22 else 0)})
    C.append(c)
    # ---- attacks
    # crab_snap: quick right-pincer jab + snap shut (hit 0.37-0.47 s)
    c = Clip("crab_snap", 24, hits=[[11 / FPS, 14 / FPS]])
    c.key(0).key(7, body_fwd=-0.06, body_yaw=10, body_up=0.03, claw_R_lift=26, claw_R_yaw=22, claw_R_fold=-10,
                 claw_R_wrist=14, claw_R_open=1.0, claw_L_lift=8, eyes=-8, **legs(front=dict(f=-0.02)))
    c.key(11, body_fwd=0.2, body_yaw=-8, body_up=-0.03, body_pitch=-4, claw_R_lift=4, claw_R_yaw=-12,
          claw_R_fold=10, claw_R_wrist=-4, claw_R_open=0.9, claw_L_lift=4, legs_follow=0.25,
          **legs(front=dict(f=0.1), mid=dict(f=0.05)))
    c.key(13, body_fwd=0.22, body_yaw=-9, body_up=-0.03, body_pitch=-5, claw_R_lift=2, claw_R_yaw=-14,
          claw_R_fold=12, claw_R_wrist=-6, claw_R_open=-0.05, legs_follow=0.25,
          **legs(front=dict(f=0.1), mid=dict(f=0.05)))
    c.key(24, body_fwd=0, body_yaw=0, body_up=0, body_pitch=0, claw_R_lift=0, claw_R_yaw=0, claw_R_fold=0,
          claw_R_wrist=0, claw_R_open=0, claw_L_lift=0, eyes=0, legs_follow=0,
          **legs(front=dict(f=0.0), mid=dict(f=0.0)))
    C.append(c)
    # crab_slam: both pincers raised high, then hammered down together (hit 0.8-0.93 s)
    c = Clip("crab_slam", 42, hits=[[24 / FPS, 28 / FPS]])
    c.key(0)
    c.key(14, body_up=0.1, body_fwd=-0.08, body_pitch=14, claw_lift=62, claw_yaw=10, claw_fold=6, claw_wrist=30,
          claw_open=0.3, eyes=-20, mand=1.0, **legs(front=dict(f=-0.05), back=dict(f=0.03)))
    c.key(20, body_up=0.12, body_fwd=-0.1, body_pitch=16, claw_lift=68, claw_yaw=8, claw_fold=8, claw_wrist=34,
          claw_open=0.2, eyes=-22, **legs(front=dict(f=-0.05), back=dict(f=0.03)))
    c.key(24, body_up=-0.1, body_fwd=0.16, body_pitch=-10, claw_lift=-16, claw_yaw=4, claw_fold=14, claw_wrist=-12,
          claw_open=0.0, eyes=10, legs_follow=0.25, **legs(front=dict(f=0.08)))
    c.key(28, body_up=-0.12, body_fwd=0.17, body_pitch=-11, claw_lift=-20, claw_yaw=4, claw_fold=14,
          claw_wrist=-14, eyes=12, legs_follow=0.25, **legs(front=dict(f=0.08)))
    c.key(34, body_up=-0.08, body_fwd=0.12, body_pitch=-7, claw_lift=-14, claw_fold=10, claw_wrist=-8,
          legs_follow=0.2, **legs(front=dict(f=0.06)))
    c.key(42, body_up=0, body_fwd=0, body_pitch=0, claw_lift=0, claw_yaw=0, claw_fold=0, claw_wrist=0, claw_open=0,
          eyes=0, mand=0, legs_follow=0, **legs(front=dict(f=0.0), back=dict(f=0.0)))
    c.layer(lambda f, cl: {"body.roll": 3.0 * math.sin(2 * math.pi * (f - 24) / 6) * pulse(f, 24, 36)})
    C.append(c)
    # crab_guard: pincers raised and folded in front of the face (in 0-9, held 9-27, out 27-36)
    c = Clip("crab_guard", 36)
    guard = dict(body_up=-0.05, body_pitch=6, claw_lift=34, claw_fold=48, claw_yaw=-6, claw_wrist=26, claw_roll=10,
                 claw_open=0.0, eyes=24, mand=0.0, legs_spread=0.06)
    c.key(0).key(9, **guard)
    c.key(27, **guard)
    c.key(36, body_up=0, body_pitch=0, claw_lift=0, claw_fold=0, claw_yaw=0, claw_wrist=0, claw_roll=0, eyes=0,
          legs_spread=0)
    c.layer(lambda f, cl: {"body.up": -0.006 * cyc(f, 12, 1) * (1 if 9 <= f <= 27 else 0),
                           "claw.lift": 2.0 * cyc(f, 12, 1, 0.25) * (1 if 9 <= f <= 27 else 0)})
    C.append(c)
    return C


# ------------------------------------------------------------------------------------------------ mesh
def build_mesh():
    import bh_mesh as M
    import kit_deeps as D
    parts = []
    rng = np.random.default_rng(17)

    H, T = H0, T0                  # author in the unscaled space; scaled + bound at the end
    pending = []

    def add(p, **kw):
        pending.append((p, kw))
        return p

    def addb(plist, bone):
        for p in plist:
            add(p, bone=bone)

    def ring(y, zc, rx, rt, rb, n=26):
        a = np.linspace(0, 2 * math.pi, n, endpoint=False)
        return np.array([(rx * np.sign(math.cos(t)) * abs(math.cos(t)) ** 0.8, y,
                          zc + (rt if math.sin(t) > 0 else rb) * math.sin(t)) for t in a])

    # ---- carapace (domed, wide, spined front margin) + pale underside
    CARA = [(-0.45, 0.53, 0.1, 0.05, 0.03), (-0.41, 0.54, 0.3, 0.13, 0.07), (-0.3, 0.55, 0.45, 0.21, 0.1),
            (-0.15, 0.56, 0.52, 0.27, 0.11), (0.0, 0.56, 0.535, 0.28, 0.11), (0.15, 0.555, 0.49, 0.25, 0.11),
            (0.27, 0.55, 0.38, 0.16, 0.09), (0.35, 0.54, 0.22, 0.08, 0.06), (0.385, 0.53, 0.05, 0.02, 0.02)]

    def top_z(x, y):
        """Carapace top height at (x, y) (interpolated rows, elliptic dome)."""
        ys = [r[0] for r in CARA]
        zc = np.interp(y, ys, [r[1] for r in CARA])
        rx = np.interp(y, ys, [r[2] for r in CARA])
        rt = np.interp(y, ys, [r[3] for r in CARA])
        u = min(abs(x) / max(rx, 1e-3), 0.999)
        return zc + rt * math.sqrt(1 - u ** 2.5)

    def on_top(x, y):
        z = top_z(x, y)
        e = 0.01
        nx = -(top_z(x + e, y) - top_z(x - e, y)) / (2 * e)
        ny = -(top_z(x, y + e) - top_z(x, y - e)) / (2 * e)
        return np.array([x, y, z]), K.unit(np.array([nx, ny, 1.0]))
    V, F = M.loft([ring(*r) for r in CARA], cap0=True, cap1=True)
    add(M.recalc_normals(M.Part(V, F, "BH_Leather", name="carapace")), bone="body")
    V, F = M.loft([ring(y, zc - 0.07, rx * 0.8, 0.02, rb * 0.7, n=16) for (y, zc, rx, rt, rb) in CARA[1:8]],
                  cap0=True, cap1=True)
    add(M.recalc_normals(M.Part(V, F, "BH_Flesh", name="underside")), bone="body")
    # rim ridge along the carapace margin + spines on the front-lateral margins
    for sx in (1, -1):
        rim = [np.array([sx * np.interp(y, [r[0] for r in CARA], [r[2] for r in CARA]) * 0.99, y,
                         np.interp(y, [r[0] for r in CARA], [r[1] for r in CARA])]) for y in np.linspace(-0.42, 0.36, 12)]
        V, F = M.tube(rim, [(0.018, 0.022)] * len(rim), n=5, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Leather", name="rim"), bone="body")
        for i, y in enumerate(np.linspace(-0.38, -0.08, 5)):
            rx = np.interp(y, [r[0] for r in CARA], [r[2] for r in CARA])
            zc = np.interp(y, [r[0] for r in CARA], [r[1] for r in CARA])
            b = np.array([sx * rx * 0.97, y, zc + 0.01])
            d = K.unit(np.array([sx * 1.0, -0.55, 0.25]))
            V, F = M.tube([b, b + d * 0.05, b + d * 0.09], [(0.022, 0.022), (0.012, 0.012), (0.002, 0.002)], n=5,
                          up=(0, 0, 1))
            add(M.Part(V, F, "BH_DarkSteel" if i % 2 else "BH_Leather", name="spine"), bone="body")
    # front brow teeth between the eyes
    for x in (-0.05, 0.0, 0.05):
        b = np.array([x, -0.44, 0.565])
        V, F = M.tube([b, b + (0, -0.05, 0.005)], [(0.018, 0.012), (0.002, 0.002)], n=4, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Leather", name="tooth"), bone="body")
    # mottles / crust on the shell
    for i in range(16):
        x, y = (rng.random() - 0.5) * 0.8, -0.3 + 0.6 * rng.random()
        q, n = on_top(x, y)
        V, F = M.sphere(0.05 + 0.04 * rng.random(), 8, 4, scale=(1.0, 0.8, 0.12))
        from bh_body import M_align_z
        V = np.asarray(V) @ M_align_z(n).T + q - n * 0.005
        add(M.Part(V, F, "BH_Stone", name="mottle"), bone="body")
    # barnacle colonies, coral growth, seaweed
    for i, (x, y, r, cnt) in enumerate(((0.12, 0.05, 0.1, 10), (-0.2, -0.1, 0.09, 8), (0.28, -0.12, 0.07, 6),
                                        (-0.1, 0.2, 0.08, 7), (0.02, -0.22, 0.06, 5))):
        q, n = on_top(x, y)
        addb(D.barnacle_cluster(q, n, r, count=cnt, seed=60 + i, rmin=0.014, rmax=0.032, sides=5,
                                surface=lambda p: on_top(p[0], p[1])), "body")
    for i, (x, y, ln, tip) in enumerate(((-0.18, 0.12, 0.13, "BH_Emissive"), (0.22, 0.14, 0.1, None),
                                         (-0.28, -0.02, 0.09, None), (0.06, 0.24, 0.09, "BH_Emissive"))):
        q, n = on_top(x, y)
        addb(D.coral(q - n * 0.01, n * 0.8 + np.array([0, 0.2, 0.6]), ln, 0.024, "BH_Horn", seed=70 + i, depth=2,
                     spread=38, n=5, branches=3 if i == 0 else 2, tip=tip), "body")
    for k in range(9):
        a = math.radians(-60 + 300 * k / 8 + 90)
        y = 0.1 + 0.25 * math.sin(a) * 0.9
        x = 0.46 * math.cos(a)
        if y < -0.05:
            continue
        q, n = on_top(x * 0.95, y)
        down = np.array([math.cos(a) * 0.6, max(math.sin(a), 0.1) * 0.6, -1.0])
        addb(D.kelp(q, down, 0.22 + 0.1 * rng.random(), 0.04, "BH_Fur", out=n, amp=0.02, seed=k,
                    bladders="BH_Fur" if k % 3 == 0 else None), "body")
    # ---- eye stalks + mandible plates + mouth
    for s, sx in (("L", 1), ("R", -1)):
        e = f"eye.{s}"
        V, F = M.tube([H[e], (H[e] + T[e]) / 2, T[e]], [(0.022, 0.022), (0.017, 0.017), (0.016, 0.016)], n=6,
                      up=(1, 0, 0))
        add(M.Part(V, F, "BH_Leather", name="stalk"), bone=e)
        V, F = M.sphere(0.03, 8, 5, center=T[e] + (0, -0.006, 0.01))
        add(M.Part(V, F, "BH_Emissive", name="eye"), bone=e)
        V, F = M.sphere(0.033, 8, 4, center=T[e] + (0, 0.008, 0.014), scale=(1.05, 0.8, 0.6))
        add(M.Part(V, F, "BH_Leather", name="eyelid"), bone=e)
        m = f"mand.{s}"
        V, F = M.box(0.05, 0.016, 0.1)
        plate = M.Part(V, F, "BH_Flesh", name="mandible").move((H[m] + T[m]) / 2 + (sx * 0.01, 0, 0))
        add(M.bevel(plate, 0.006, 1), bone=m)
        V, F = M.tube([T[m], T[m] + (0, -0.02, -0.03)], [(0.012, 0.006), (0.002, 0.002)], n=4, up=(0, -1, 0))
        add(M.Part(V, F, "BH_DarkSteel", name="mand_tip"), bone=m)
    V, F = M.sphere(0.05, 10, 5, center=(0, -0.43, 0.46), scale=(1.2, 0.5, 0.8))
    add(M.Part(V, F, "BH_Shadow", name="mouth"), bone="body")
    # ---- pincers
    for s, sx in (("L", 1), ("R", -1)):
        k = CLAW_S[s]
        b1, b2, b3, b4 = (f"claw.{i}.{s}" for i in (1, 2, 3, 4))
        V, F = M.tube([H[b1] + (H[b1] - T[b1]) * 0.1, (H[b1] + T[b1]) / 2, T[b1]],
                      [(0.045 * k, 0.05 * k), (0.052 * k, 0.058 * k), (0.046 * k, 0.05 * k)], n=10, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Leather", name="merus"), chain=[b1, b2], blend=0.3)
        V, F = M.tube([H[b2], (H[b2] + T[b2]) / 2, T[b2]], [(0.05 * k, 0.055 * k), (0.06 * k, 0.062 * k),
                      (0.056 * k, 0.058 * k)], n=10, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Leather", name="carpus"), chain=[b2, b3], blend=0.3)
        V, F = M.sphere(0.058 * k, 10, 5, center=T[b1])
        add(M.Part(V, F, "BH_Flesh", name="joint"), chain=[b1, b2], blend=0.5)
        V, F = M.sphere(0.06 * k, 10, 5, center=T[b2])
        add(M.Part(V, F, "BH_Flesh", name="joint"), chain=[b2, b3], blend=0.5)
        # palm: swollen lozenge + fixed finger continuing forward/down
        d3 = RIG.rdir(b3)
        c = H[b3] + d3 * 0.1 * k
        rings = []
        for u, rr, rz in ((-0.02, 0.06, 0.06), (0.03, 0.1, 0.11), (0.1, 0.12, 0.13), (0.16, 0.105, 0.11),
                          (0.2, 0.07, 0.07)):
            p0 = H[b3] + d3 * u * k
            side = K.unit(np.cross(d3, (0, 0, 1)))
            up = np.cross(side, d3)
            rings.append(np.array([p0 + side * rr * k * math.cos(t) + up * rz * k * math.sin(t)
                                   for t in np.linspace(0, 2 * math.pi, 14, endpoint=False)]))
        V, F = M.loft(rings, cap0=True, cap1=True)
        add(M.recalc_normals(M.Part(V, F, "BH_Leather", name="palm")), bone=b3)
        base = H[b3] + d3 * 0.19 * k + np.array([0, 0, -0.03 * k])
        fx = [base, base + d3 * 0.1 * k + np.array([0, 0, -0.01 * k]), base + d3 * 0.2 * k + np.array([0, 0, 0.01 * k])]
        V, F = M.tube(fx, [(0.03 * k, 0.034 * k), (0.022 * k, 0.024 * k), (0.004, 0.004)], n=7, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Leather", name="finger"), bone=b3)
        V, F = M.tube([fx[1] + d3 * 0.06 * k, fx[2] + d3 * 0.012], [(0.018 * k, 0.018 * k), (0.002, 0.002)], n=5,
                      up=(0, 0, 1))
        add(M.Part(V, F, "BH_DarkSteel", name="fingertip"), bone=b3)
        for i in range(4):     # teeth on the fixed finger (upper edge)
            q = base + d3 * (0.03 + 0.04 * i) * k + np.array([0, 0, 0.022 * k])
            V, F = M.tube([q, q + np.array([0, 0, 0.022 * k])], [(0.009 * k, 0.009 * k), (0.002, 0.002)], n=4,
                          up=(1, 0, 0))
            add(M.Part(V, F, "BH_Bone", name="ctooth"), bone=b3)
        # dactyl (movable finger) above
        d4 = RIG.rdir(b4)
        dd = [H[b4], H[b4] + d4 * 0.11 * k + np.array([0, 0, 0.012 * k]), T[b4]]
        V, F = M.tube(dd, [(0.03 * k, 0.03 * k), (0.022 * k, 0.022 * k), (0.004, 0.004)], n=7, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Leather", name="dactyl"), bone=b4)
        V, F = M.tube([dd[1] + d4 * 0.05 * k, T[b4] + d4 * 0.01], [(0.016 * k, 0.016 * k), (0.002, 0.002)], n=5,
                      up=(0, 0, 1))
        add(M.Part(V, F, "BH_DarkSteel", name="dactyltip"), bone=b4)
        for i in range(3):
            q = H[b4] + d4 * (0.05 + 0.045 * i) * k + np.array([0, 0, -0.02 * k])
            V, F = M.tube([q, q + np.array([0, 0, -0.02 * k])], [(0.008 * k, 0.008 * k), (0.002, 0.002)], n=4,
                          up=(1, 0, 0))
            add(M.Part(V, F, "BH_Bone", name="dtooth"), bone=b4)
        # knobs + barnacles on the (big) palm
        up3 = np.cross(K.unit(np.cross(d3, (0, 0, 1))), d3)
        addb(D.barnacle_cluster(c + up3 * 0.09 * k, up3, 0.06 * k, count=6 if s == "R" else 3, seed=80 + (s == "R"),
                                rmin=0.011, rmax=0.02 * k, sides=5), b3)
        for i in range(4):
            q = H[b2] + (T[b2] - H[b2]) * (0.25 + 0.2 * i) + np.array([sx * 0.02, 0, 0.05 * k])
            V, F = M.tube([q, q + np.array([sx * 0.01, -0.01, 0.03])], [(0.012, 0.012), (0.002, 0.002)], n=4,
                          up=(1, 0, 0))
            add(M.Part(V, F, "BH_DarkSteel", name="knob"), bone=b2)
    # ---- walking legs: flattened, banded, spined tips
    for kk, (cx, fe, ti, ta) in LEGS.items():
        pts, prof = [], []
        segs = [(cx, 2, 0.06, 0.058), (fe, 5, 0.058, 0.05), (ti, 5, 0.048, 0.036), (ta, 4, 0.032, 0.01)]
        pts.append(H[cx] - RIG.rdir(cx) * 0.02)
        prof.append((0.045, 0.05))
        for b, nseg, r0, r1 in segs:
            for i in range(1, nseg + 1):
                t = i / nseg
                pts.append(H[b] * (1 - t) + T[b] * t)
                r = r0 * (1 - t) + r1 * t
                prof.append((r * 0.8, r * 1.2))
        prof[-1] = (0.003, 0.003)
        V, F = M.tube(pts, prof, n=7, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Leather", name="leg"), chain=[cx, fe, ti, ta], blend=0.28)
        for b, r in ((fe, 0.056), (ti, 0.045)):
            V, F = M.sphere(r, 7, 4, center=T[b])
            add(M.Part(V, F, "BH_Flesh", name="knee"), chain=[b, ti if b == fe else ta], blend=0.5)
        d = RIG.rdir(ta)
        V, F = M.tube([T[ta] - d * 0.08, T[ta] + d * 0.006], [(0.014, 0.014), (0.002, 0.002)], n=5, up=(0, 0, 1))
        add(M.Part(V, F, "BH_DarkSteel", name="legtip"), bone=ta)
        for b, cnt in ((fe, 3), (ti, 2)):
            db = RIG.rdir(b)
            side = K.unit(np.cross(db, [0, 0, 1.0]))
            upv = np.cross(side, db)
            for i in range(cnt):
                t = (i + 0.5) / cnt
                base = H[b] * (1 - t) + T[b] * t + upv * 0.03
                V, F = M.tube([base, base + (upv * 0.7 + db * 0.7) * 0.04], [(0.008, 0.008), (0.0015, 0.0015)], n=4,
                              up=tuple(side))
                add(M.Part(V, F, "BH_DarkSteel", name="legspine"), bone=b)
    for p, kw in pending:
        p.V = p.V * SIZE
        K.bind(p, RIG, **kw)
        parts.append(p)
    return parts


# ------------------------------------------------------------------------------------------------ analysis
def reach_report(clip):
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


# ------------------------------------------------------------------------------------------------ main
def main():
    a = K.std_args()
    import bh_mesh as M
    C = clips()
    only = set(x for x in a.clips.split(",") if x) or None
    arm, mesh, acts = K.build_all(CID, RIG, evaluate, C, build_mesh, PALETTE, only=only, ao=(16, 0.3, 0.6))
    tris = M.tri_count(mesh)
    co = np.array([v.co[:] for v in mesh.data.vertices])
    print(f"[{CID}] mesh {tris} tris, {len(mesh.data.vertices)} verts, {len(RIG.ORDER)} bones, {len(acts)} clips; "
          f"rest bounds x {co[:, 0].min():.3f}..{co[:, 0].max():.3f} y {co[:, 1].min():.3f}..{co[:, 1].max():.3f} "
          f"z {co[:, 2].min():.3f}..{co[:, 2].max():.3f}")
    for c in C:
        if "ground_speed" in c.meta:
            v = K.foot_slide(c, evaluate, foot, LEG_IDS, c.meta["ground_speed"], FLOOR + 0.012)
            print(f"[{CID}] foot slip {c.name}: max {v[0] * 1000:.2f} mm/frame, mean {v[1] * 1000:.2f}, "
                  f"stance {v[2]:.2f}")
    print(f"[{CID}] worst IK reach miss per clip (mm): " +
          ", ".join(f"{c.name} {reach_report(c) * 1000:.1f}" for c in C if not only or c.name in only))
    K.quick_preview(CID, arm, acts, a, 0.45, 4.4)
    if a.evidence:
        K.evidence_rest(CID, arm, 0.45, 4.4, "Reef Crawler - rest (4 views + 3/4 + gameplay iso 26 m / 55 deg)",
                        iso_scales=(1.0,), base=EVID)
        spec = [("idle", [0.0]), ("walk", [0, 0.25, 0.5, 0.75]), ("crab_snap", [0, 7 / 24, 11 / 24, 13 / 24, 1.0]),
                ("crab_slam", [0, 14 / 42, 20 / 42, 24 / 42, 28 / 42, 1.0]),
                ("crab_guard", [0, 9 / 36, 18 / 36, 27 / 36, 1.0]), ("alert", [0.3]), ("hit_heavy", [0.22]),
                ("death", [0.3, 0.5, 1.0]), ("death_back", [0.2, 1.0])]
        K.evidence_clips(CID, arm, acts, spec, 0.5, 5.0, "Reef Crawler - clips (view yaw 40)", yaw=40, cols=6,
                         base=EVID)
    if not a.no_export and not only:
        K.merge_meta(CID, C, "tools/blender/creatures/build_reef_crawler.py", {"tris": tris, "bones": len(RIG.ORDER)})
        bad, got = K.export(CID, arm, mesh, acts, OUT_GLB)
        assert not bad, bad


if __name__ == "__main__":
    main()
