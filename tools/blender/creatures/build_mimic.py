"""Treasure Mimic (Builder C, bh-010): an iron-banded wooden chest that is secretly a monster. Own rig (root, body, lid,
6-bone tongue, 4 three-bone clawed legs), skinned mesh and baked procedural clips.

  blender -b --factory-startup --python build_mimic.py -- [--evidence] [--no-export] [--clips a,b] [--prev DIR --sheet a,b]

Conventions: Blender Z-up, faces -Y (= +Z in Godot), origin on the ground under the chest, meters, 30 fps.
The REST pose is the awake stance (chest lifted LIFT m on its legs, lid shut). `mimic_dormant` drops the chest onto the
ground and shrinks every leg to 1.5 % about its root, which sits inside the solid bottom of the box, so nothing but a
closed chest is visible. The tongue bones translate along their own polyline and the tongue mesh uses linear 'hat'
weights between the joints, so the tongue stretches uniformly (no thickening) up to ~3 m for `mimic_tongue`.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import creature_kit_c as K  # noqa: E402
from creature_kit_c import Clip, Xf, Rx, Rz, cyc, pulse, spine_rot, FPS  # noqa: E402

import numpy as np  # noqa: E402

CID = "treasure_mimic"
OUT_GLB = os.path.join(K.CHAR_OUT, f"{CID}.glb")
PALETTE = {
    "BH_Wood": ((0.26, 0.145, 0.07), 0.0, 0.72, None, 0.0, 1.0),          # chest planks
    "BH_Hair": ((0.07, 0.04, 0.022), 0.0, 0.8, None, 0.0, 1.0),           # plank seams
    "BH_DarkSteel": ((0.16, 0.16, 0.17), 0.85, 0.5, None, 0.0, 1.0),      # iron bands, rivets
    "BH_Gold": ((0.88, 0.62, 0.2), 1.0, 0.28, None, 0.0, 1.0),            # coins, lock plate
    "BH_Bone": ((0.86, 0.8, 0.64), 0.0, 0.45, None, 0.0, 1.0),            # teeth
    "BH_Flesh": ((0.5, 0.06, 0.2), 0.0, 0.35, None, 0.0, 1.0),            # purple-red tongue
    "BH_Leather": ((0.2, 0.035, 0.06), 0.0, 0.5, None, 0.0, 1.0),         # gums / mouth lining
    "BH_Skin": ((0.24, 0.15, 0.17), 0.0, 0.6, None, 0.0, 1.0),            # dusky legs
    "BH_Horn": ((0.1, 0.075, 0.06), 0.0, 0.4, None, 0.0, 1.0),            # claws
    "BH_Shadow": ((0.012, 0.004, 0.008), 0.0, 0.8, None, 0.0, 1.0),       # maw, pupils, keyhole
    "BH_Emissive": ((1.0, 0.78, 0.25), 0.0, 0.3, (1.0, 0.72, 0.16), 6.0, 1.0),   # gold eyes
}

# ------------------------------------------------------------------------------------------------ dimensions
LIFT = 0.30                     # chest bottom height in the awake rest pose
W2, D2 = 0.5, 0.325             # half width (x), half depth (y)
Z0, ZR = LIFT, LIFT + 0.48      # box bottom, rim
LID_H = 0.27                    # lid height (0.75 m closed total)
WALL = 0.035
FLOOR = ZR - 0.255              # interior floor (maw)

# ------------------------------------------------------------------------------------------------ skeleton
PIVOT = np.array([0.0, 0.0, Z0 + 0.25])
EDGE_B = np.array([0.0, D2, Z0])
TJ = [np.array([0.0, 0.1 - 0.065 * i, 0.62]) for i in range(6)]
TTIP = np.array([0.0, TJ[5][1] - 0.055, 0.62])
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.25), None),
    "body": ((0, 0, Z0 + 0.15), (0, -0.3, Z0 + 0.15), "root"),
    "lid": ((0, D2, ZR), (0, -D2, ZR), "body"),
}
for _i in range(6):
    BONES[f"tongue.{_i}"] = (tuple(TJ[_i]), tuple(TJ[_i + 1] if _i < 5 else TTIP),
                             "body" if _i == 0 else f"tongue.{_i - 1}")
LEG_SPEC = {"F": (-0.19, 25.0), "B": (0.19, -25.0)}      # y of the root, azimuth (+ = toward the front)
LEGS = {}
for _s, _x in (("L", 1.0), ("R", -1.0)):
    for _fb, (_y, _az) in LEG_SPEC.items():
        _P = np.array([0.30 * _x, _y, LIFT + 0.03])
        _u = np.array([_x * math.cos(math.radians(_az)), -math.sin(math.radians(_az)), 0.0])

        def _pt(r, z, P=_P, u=_u):
            return tuple(P + u * r + np.array([0.0, 0.0, z - P[2]]))
        k = f"{_fb}{_s}"
        names = (f"thigh.{k}", f"shin.{k}", f"foot.{k}")
        pts = [tuple(_P), _pt(0.30, LIFT + 0.10), _pt(0.42, 0.075), _pt(0.50, 0.012)]
        for i, nm in enumerate(names):
            BONES[nm] = (pts[i], pts[i + 1], "body" if i == 0 else names[i - 1])
        LEGS[k] = names
RIG = K.Rig(BONES)
H, T = RIG.H, RIG.T
LEG_IDS = ["FL", "FR", "BL", "BR"]
NEUTRAL = {k: T[v[2]].copy() for k, v in LEGS.items()}
OUTW = {k: K.unit(np.array([(T[v[2]] - H[v[0]])[0], (T[v[2]] - H[v[0]])[1], 0.0])) for k, v in LEGS.items()}
BETA = {k: math.degrees(math.atan2(H[v[2]][2] - T[v[2]][2],
                                   np.linalg.norm((T[v[2]] - H[v[2]])[:2]))) for k, v in LEGS.items()}
CURL = (-35.0, -115.0, -175.0)     # legs pulled in under the belly (hop tuck / dead bug)
FLOORZ = 0.012
TSEG, TTIP_L = 0.065, 0.055


# ------------------------------------------------------------------------------------------------ pose
def evaluate(c):
    X = {}
    g = c.get
    t = np.array([g("body.side", 0.0), -g("body.fwd", 0.0), g("body.up", 0.0)])
    X["root"] = Xf.move(t) @ Xf.about(Rx(-g("body.tipb", 0.0)), EDGE_B) @ Xf.about(spine_rot(c, "body"), PIVOT)
    RIG.fk(X, "body")
    RIG.fk(X, "lid", Rx(-g("lid.open", 0.0)))
    # tongue: joints laid along a polyline (droop = pitch of the first segment, + = down; curl = extra pitch per
    # joint; ext = extra length factor of the 5 stretch segments; yaw/wave = sideways)
    ext = 1.0 + g("tongue.ext", 0.0)
    th, step = g("tongue.droop", 0.0), g("tongue.curl", 0.0)
    yaw, wave, wph = g("tongue.yaw", 0.0), g("tongue.wave", 0.0), g("tongue.wph", 0.0)
    p = TJ[0] + np.array([0.0, -g("tongue.push", 0.0), 0.0])
    for i in range(6):
        b = f"tongue.{i}"
        yw = yaw + wave * math.sin(2 * math.pi * (0.15 * i + wph))
        d = Rz(yw) @ Rx(th + step * i) @ np.array([0.0, -1.0, 0.0])
        R = K.min_rot(RIG.rdir(b), d)
        X[b] = X["body"] @ Xf(R, p - R @ H[b])
        p = p + d * (TSEG * ext if i < 5 else TTIP_L)
    fold = min(max(g("legs.fold", 0.0), 0.0), 1.0)
    for k in LEG_IDS:
        th_, sh, ft = LEGS[k]
        off = np.array([0.0, -(g(k + ".f", 0.0) + g("legs.f", 0.0)), g(k + ".up", 0.0) + g("legs.up", 0.0)])
        off = off + OUTW[k] * (g(k + ".side", 0.0) + g("legs.spread", 0.0))
        tw = NEUTRAL[k] + off
        w = min(max(g("legs.follow", 0.0) + g(k + ".follow", 0.0), 0.0), 1.0)
        tgt = tw * (1 - w) + X["root"].apply(tw) * w
        tgt[2] = max(tgt[2], FLOORZ)
        curl = min(max(g("legs.curl", 0.0) + g(k + ".curl", 0.0) + fold, 0.0), 1.0)
        K.plane_leg(RIG, X, X["body"], [th_, sh, ft], tgt, beta=BETA[k] + g(k + ".beta", 0.0), curl=curl,
                    curl_ang=CURL, scale=1.0 - 0.985 * fold)
    return X


def foot(X, k):
    return RIG.tail(X, LEGS[k][2])


def tongue_tip(X):
    return RIG.tail(X, "tongue.5")


# ------------------------------------------------------------------------------------------------ clips
IDLE = dict(lid_open=34.0, tongue_ext=1.5, tongue_droop=-60.0, tongue_curl=30.0)
DORMANT = dict(body_up=-LIFT, legs_fold=1.0, lid_open=0.0, tongue_ext=0.0, tongue_droop=0.0, tongue_curl=0.0)
ZERO = dict(body_up=0.0, body_fwd=0.0, body_side=0.0, body_pitch=0.0, body_roll=0.0, body_yaw=0.0, body_tipb=0.0,
            legs_fold=0.0, legs_follow=0.0, legs_spread=0.0, legs_curl=0.0, legs_f=0.0, legs_up=0.0,
            tongue_wave=0.0, tongue_yaw=0.0, tongue_push=0.0)


def I(**kw):
    d = dict(IDLE)
    d.update(kw)
    return d


def E(**kw):
    """idle + every other channel back to 0 (clip start / end)."""
    d = dict(ZERO)
    d.update(IDLE)
    d.update(kw)
    return d


def legs(**kw):
    out = {}
    groups = {"front": ("FL", "FR"), "back": ("BL", "BR"), "all": tuple(LEG_IDS), "L": ("FL", "BL"),
              "R": ("FR", "BR"), "FL": ("FL",), "FR": ("FR",), "BL": ("BL",), "BR": ("BR",)}
    for gname, d in kw.items():
        for k in groups[gname]:
            for ch, v in d.items():
                out[f"{k}_{ch}"] = v
    return out


def gait_layer(period, duty, speed, lift, phases):
    sweep = speed * duty * period / FPS

    def fn(f, clip):
        out = {}
        for k in LEG_IDS:
            ff, up, sw = K.gait_foot(f / period - phases[k], duty, sweep, lift)
            out[k + ".f"] = ff
            out[k + ".up"] = up
            out[k + ".beta"] = -18.0 * math.sin(math.pi * sw) if sw >= 0 else 0.0
        return out
    return fn


def clips():
    C = []
    # ---- dormant: a closed chest on the ground, legs retracted inside the box bottom, perfectly still
    c = Clip("mimic_dormant", 30, loop=True)
    c.key(0, **dict(ZERO, **DORMANT)).key(30, **dict(ZERO, **DORMANT))
    C.append(c)
    # ---- wake: shudder, lid bursts open, tongue whips up, legs unfold and it stands up (ends on idle frame 0)
    c = Clip("mimic_wake", 36)
    c.key(0, **dict(ZERO, **DORMANT))
    c.key(5, **dict(DORMANT, lid_open=7.0))
    c.key(9, body_up=-0.26, legs_fold=0.55, lid_open=105, tongue_ext=2.4, tongue_droop=-88, tongue_curl=8,
          tongue_wave=18, body_pitch=6)
    c.key(15, body_up=0.1, legs_fold=0.0, lid_open=80, tongue_ext=2.0, tongue_droop=-75, tongue_curl=22,
          tongue_wave=10, body_pitch=8)
    c.key(21, body_up=-0.04, lid_open=48, tongue_ext=1.6, tongue_droop=-62, tongue_curl=30, tongue_wave=4,
          body_pitch=-2)
    c.key(27, body_up=0.015, lid_open=30, body_pitch=1, tongue_wave=0, **{k: v for k, v in IDLE.items()
                                                                          if k != "lid_open"})
    c.key(36, **E())
    c.layer(lambda f, cl: {"body.roll": 2.5 * math.sin(2 * math.pi * f / 3.0) * pulse(f, 1, 9),
                           "lid.open": 4.0 * max(0.0, math.sin(2 * math.pi * f / 4.0)) * pulse(f, 1, 7),
                           "tongue.wph": f / 12.0})
    C.append(c)
    # ---- idle: lid breathing, tongue lolling over the front rim
    c = Clip("idle", 60, loop=True)
    c.key(0, **E()).key(60, **E())
    c.layer(lambda f, cl: {"lid.open": 5.0 * cyc(f, 60, 2), "body.up": 0.008 * cyc(f, 60, 2, 0.1),
                           "body.pitch": 1.2 * cyc(f, 60, 2, 0.35), "tongue.wave": 7.0 * cyc(f, 60, 1),
                           "tongue.wph": f / 60.0, "tongue.droop": 4.0 * cyc(f, 60, 2, 0.2),
                           "tongue.ext": 0.1 * cyc(f, 60, 1, 0.3), "body.yaw": 1.5 * cyc(f, 60, 1, 0.6)})
    C.append(c)
    # ---- walk: scuttling trot (diagonal pairs), waddle, chattering lid
    WP, WV = 14, 1.2
    c = Clip("walk", WP, loop=True, ground_speed=WV)
    c.key(0, **E()).key(WP, **E())
    c.layer(gait_layer(WP, 0.6, WV, 0.09, {"FL": 0.0, "BR": 0.0, "FR": 0.5, "BL": 0.5}))
    c.layer(lambda f, cl: {"body.up": -0.012 + 0.014 * cyc(f, WP, 2, 0.05), "body.roll": 3.0 * cyc(f, WP, 1, 0.05),
                           "body.yaw": 2.5 * cyc(f, WP, 1, 0.3), "body.pitch": 1.5 * cyc(f, WP, 2, 0.3),
                           "lid.open": 8.0 * cyc(f, WP, 2, 0.4), "tongue.wave": 10 * cyc(f, WP, 1, 0.2),
                           "tongue.wph": f / WP})
    C.append(c)
    # ---- run / run_combat: bounding hop (front pair then back pair), lid flapping
    for nm, v, lid, ext in (("run", 3.2, 10.0, 0.0), ("run_combat", 3.0, 30.0, 0.6)):
        RP = 10
        c = Clip(nm, RP, loop=True, ground_speed=v)
        c.key(0, **E(lid_open=34 + lid, tongue_ext=1.5 + ext)).key(RP, **E(lid_open=34 + lid, tongue_ext=1.5 + ext))
        c.layer(gait_layer(RP, 0.42, v, 0.13, {"FL": 0.0, "FR": 0.06, "BL": 0.5, "BR": 0.56}))
        c.layer(lambda f, cl, lid=lid: {
            "body.up": 0.02 + 0.045 * max(0.0, cyc(f, RP, 2, 0.3)), "body.pitch": 5.0 * cyc(f, RP, 1, 0.1),
            "body.roll": 2.0 * cyc(f, RP, 1, 0.3), "lid.open": (10.0 + 0.3 * lid) * cyc(f, RP, 1, 0.35),
            "tongue.wave": 12 * cyc(f, RP, 1, 0.1), "tongue.wph": f / RP, "tongue.droop": 8 * cyc(f, RP, 1, 0.4)})
        C.append(c)
    # ---- reactions
    c = Clip("hit_light", 12)
    c.key(0, **E()).key(3, **I(body_fwd=-0.05, body_pitch=7, body_up=0.02, lid_open=12, tongue_ext=0.8,
                               tongue_droop=-40, legs_follow=0.25))
    c.key(12, **E())
    C.append(c)
    c = Clip("hit_heavy", 18)
    c.key(0, **E()).key(4, **I(body_fwd=-0.13, body_pitch=13, body_roll=5, body_up=0.03, lid_open=78, tongue_ext=2.2,
                               tongue_droop=-80, tongue_curl=15, tongue_wave=25, legs_follow=0.35))
    c.key(9, **I(body_fwd=-0.1, body_pitch=3, body_roll=2, body_up=-0.04, lid_open=14, tongue_ext=1.0,
                 tongue_droop=-50, tongue_wave=8, legs_follow=0.25))
    c.key(18, **E())
    C.append(c)
    c = Clip("stagger_small", 24)
    c.key(0, **E()).key(5, **I(body_fwd=-0.06, body_side=-0.08, body_roll=-10, body_yaw=-9, lid_open=55,
                               tongue_yaw=-20, legs_follow=0.35, **legs(FR=dict(up=0.1))))
    c.key(10, **I(body_fwd=-0.08, body_side=-0.1, body_roll=-5, body_yaw=-6, lid_open=22, tongue_yaw=10,
                  legs_follow=0.3, **legs(FR=dict(up=0.0, side=0.08), BL=dict(f=-0.05))))
    c.key(16, **I(body_fwd=-0.03, body_side=-0.04, body_roll=-1.5, body_yaw=-2, lid_open=30, tongue_yaw=0,
                  legs_follow=0.12))
    c.key(24, **E(**legs(FR=dict(side=0.0), BL=dict(f=0.0))))
    C.append(c)
    c = Clip("knockback", 27)
    c.key(0, **E()).key(4, **I(body_fwd=-0.2, body_up=0.08, body_pitch=15, lid_open=90, tongue_ext=2.0,
                               tongue_droop=-85, tongue_wave=20, legs_follow=0.7, **legs(front=dict(up=0.12))))
    c.key(11, **I(body_fwd=-0.4, body_up=-0.05, body_pitch=-3, lid_open=18, tongue_ext=0.9, tongue_droop=-45,
                  legs_follow=0.85, **legs(front=dict(up=0.0, f=0.08))))
    c.key(18, **I(body_fwd=-0.2, body_up=-0.02, body_pitch=1, lid_open=28, legs_follow=0.5, **legs(front=dict(f=0.03))))
    c.key(27, **E(**legs(front=dict(f=0.0))))
    C.append(c)
    # ---- alert: rears up, lid gapes, tongue whips high, snaps shut once
    c = Clip("alert", 30)
    c.key(0, **E()).key(8, **I(body_pitch=14, body_up=0.08, lid_open=100, tongue_ext=2.6, tongue_droop=-85,
                               tongue_curl=12, tongue_wave=22, **legs(front=dict(f=0.05))))
    c.key(16, **I(body_pitch=12, body_up=0.07, lid_open=92, tongue_ext=2.2, tongue_droop=-80, tongue_curl=16,
                  tongue_wave=14))
    c.key(20, **I(body_pitch=4, body_up=0.0, lid_open=16, tongue_ext=1.0, tongue_droop=-50))
    c.key(30, **E(**legs(front=dict(f=0.0))))
    c.layer(lambda f, cl: {"tongue.wph": f / 10.0})
    C.append(c)
    # ---- deaths
    c = Clip("death", 45)          # shudders, collapses onto the ground, lid slams shut, legs splay out
    c.key(0, **E())
    c.key(5, **I(body_up=0.04, body_pitch=8, lid_open=85, tongue_ext=2.2, tongue_droop=-80, tongue_wave=25))
    c.key(11, **I(body_up=-0.18, body_pitch=-4, body_roll=4, lid_open=70, tongue_ext=0.4, tongue_droop=-20,
                  tongue_curl=5, tongue_wave=0, legs_spread=0.06))
    c.key(16, **I(body_up=-LIFT + 0.01, body_pitch=-2, body_roll=5, lid_open=55, tongue_ext=0.0, tongue_droop=0,
                  tongue_curl=0, legs_spread=0.16, legs_curl=0.1))
    c.key(20, **I(body_up=-LIFT, body_pitch=0, body_roll=4, lid_open=0, tongue_ext=0.0, tongue_droop=0,
                  tongue_curl=0, legs_spread=0.2, legs_curl=0.12))
    c.key(24, **I(body_up=-LIFT + 0.02, body_roll=3, lid_open=7, tongue_ext=0.0, tongue_droop=0, tongue_curl=0))
    c.key(29, **I(body_up=-LIFT, body_roll=4, lid_open=0, tongue_ext=0.0, tongue_droop=0, tongue_curl=0,
                  legs_spread=0.22, legs_curl=0.15))
    c.key(45, **I(body_up=-LIFT, body_roll=4, lid_open=0, tongue_ext=0.0, tongue_droop=0, tongue_curl=0,
                  legs_spread=0.22, legs_curl=0.15))
    c.layer(lambda f, cl: {"body.roll": 1.5 * math.sin(2 * math.pi * f / 3) * pulse(f, 2, 10),
                           **{k + ".up": 0.05 * pulse(f, 30 + 3 * i, 38 + 3 * i) for i, k in enumerate(LEG_IDS)}})
    C.append(c)
    c = Clip("death_back", 45)     # knocked back onto its back, legs curl up in the air, lid clamps shut
    c.key(0, **E())
    c.key(6, **I(body_fwd=-0.12, body_up=0.03, body_tipb=16, lid_open=80, tongue_ext=1.8, tongue_droop=-75,
                 tongue_wave=20, legs_follow=0.5))
    c.key(14, **I(body_fwd=-0.2, body_up=-0.12, body_tipb=58, lid_open=30, tongue_ext=0.3, tongue_droop=-10,
                  tongue_curl=5, tongue_wave=0, legs_follow=1.0, legs_curl=0.5))
    c.key(20, **I(body_fwd=-0.22, body_up=-LIFT, body_tipb=93, lid_open=0, tongue_ext=0.0, tongue_droop=0,
                  tongue_curl=0, legs_follow=1.0, legs_curl=0.9))
    c.key(24, **I(body_fwd=-0.22, body_up=-LIFT, body_tipb=84, lid_open=6, tongue_ext=0.0, tongue_droop=0,
                  tongue_curl=0, legs_follow=1.0, legs_curl=1.0))
    c.key(30, **I(body_fwd=-0.22, body_up=-LIFT, body_tipb=90, lid_open=0, tongue_ext=0.0, tongue_droop=0,
                  tongue_curl=0, legs_follow=1.0, legs_curl=1.0))
    c.key(45, **I(body_fwd=-0.22, body_up=-LIFT, body_tipb=90, lid_open=0, tongue_ext=0.0, tongue_droop=0,
                  tongue_curl=0, legs_follow=1.0, legs_curl=1.0))
    c.layer(lambda f, cl: {k + ".curl": -0.15 * pulse(f, 28 + 3 * i, 38 + 3 * i) for i, k in enumerate(LEG_IDS)})
    C.append(c)
    # ---- attacks
    c = Clip("mimic_bite", 24, hits=[[13 / FPS, 16 / FPS]])     # rear, lunge, lid chomps shut
    c.key(0, **E())
    c.key(6, **I(body_fwd=-0.1, body_up=0.05, body_pitch=14, lid_open=102, tongue_ext=0.9, tongue_droop=-75,
                 tongue_curl=22, **legs(front=dict(f=-0.04), back=dict(f=-0.04))))
    c.key(9, **I(body_fwd=0.2, body_up=0.03, body_pitch=2, lid_open=100, tongue_ext=0.3, tongue_droop=-30,
                 tongue_curl=10, **legs(front=dict(f=0.14, up=0.09), back=dict(f=0.12, up=0.07))))
    c.key(12, **I(body_fwd=0.46, body_up=-0.02, body_pitch=-10, lid_open=90, tongue_ext=0.0, tongue_droop=-8,
                  tongue_curl=3, **legs(front=dict(f=0.3, up=0.0), back=dict(f=0.28, up=0.0))))
    c.key(13, **I(body_fwd=0.48, body_up=-0.03, body_pitch=-6, lid_open=0, tongue_ext=0.0, tongue_droop=-8,
                  tongue_curl=3, **legs(front=dict(f=0.3), back=dict(f=0.28))))
    c.key(16, **I(body_fwd=0.46, body_up=-0.01, body_pitch=-3, lid_open=4, tongue_ext=0.0, tongue_droop=-8,
                  tongue_curl=3, **legs(front=dict(f=0.3), back=dict(f=0.28))))
    c.key(19, **I(body_fwd=0.3, body_up=0.03, lid_open=15, tongue_ext=0.6, tongue_droop=-40, tongue_curl=18,
                  **legs(front=dict(f=0.2, up=0.07), back=dict(f=0.16, up=0.07))))
    c.key(24, **E(**legs(front=dict(f=0.0, up=0.0), back=dict(f=0.0, up=0.0))))
    C.append(c)
    c = Clip("mimic_tongue", 36, hits=[[12 / FPS, 15 / FPS]])  # tongue lashes ~3 m forward and reels back in
    c.key(0, **E())
    c.key(6, **I(body_fwd=-0.08, body_pitch=10, body_up=0.03, lid_open=88, tongue_ext=0.5, tongue_droop=-80,
                 tongue_curl=12, **legs(back=dict(f=-0.03))))
    c.key(12, **I(body_fwd=0.15, body_pitch=-4, body_up=0.0, lid_open=86, tongue_ext=8.4, tongue_droop=-33,
                  tongue_curl=12.5, **legs(back=dict(f=0.0), front=dict(f=0.06))))
    c.key(15, **I(body_fwd=0.14, body_pitch=-3, lid_open=84, tongue_ext=8.35, tongue_droop=-32, tongue_curl=12.6,
                  **legs(front=dict(f=0.06))))
    c.key(22, **I(body_fwd=0.02, body_pitch=3, lid_open=70, tongue_ext=1.2, tongue_droop=-62, tongue_curl=26,
                  **legs(front=dict(f=0.02))))
    c.key(36, **E(**legs(front=dict(f=0.0))))
    c.layer(lambda f, cl: {"tongue.wave": 7.0 * pulse(f, 8, 24), "tongue.wph": f / 6.0})
    C.append(c)
    c = Clip("mimic_slam", 36, hits=[[22 / FPS, 25 / FPS]])     # crouch, hop up, slam down lid-first
    c.key(0, **E())
    c.key(7, **I(body_up=-0.12, body_pitch=-4, lid_open=14, tongue_ext=0.4, tongue_droop=-40, legs_spread=0.03))
    c.key(13, **I(body_up=0.55, body_fwd=0.2, body_pitch=10, lid_open=75, tongue_ext=1.6, tongue_droop=-82,
                  tongue_wave=15, legs_follow=1.0, legs_curl=0.25, legs_up=0.05))
    c.key(18, **I(body_up=0.72, body_fwd=0.35, body_pitch=0, lid_open=45, tongue_ext=0.2, tongue_droop=-20,
                  tongue_curl=5, tongue_wave=0, legs_follow=1.0, legs_curl=0.35, legs_up=0.05))
    c.key(22, **I(body_up=-0.24, body_fwd=0.4, body_pitch=-3, lid_open=0, tongue_ext=0.0, tongue_droop=0,
                  tongue_curl=0, legs_follow=0.0, legs_curl=0.0, legs_up=0.0, legs_spread=0.12, legs_f=0.4))
    c.key(25, **I(body_up=-0.2, body_fwd=0.4, body_pitch=-1, lid_open=8, tongue_ext=0.0, tongue_droop=0,
                  tongue_curl=0, legs_spread=0.12, legs_f=0.4))
    c.key(30, **I(body_up=-0.04, body_fwd=0.2, lid_open=26, legs_spread=0.04, legs_f=0.2,
                  **legs(front=dict(up=0.06), back=dict(up=0.04))))
    c.key(36, **E(legs_f=0.0, **legs(front=dict(up=0.0), back=dict(up=0.0))))
    C.append(c)
    return C


# ------------------------------------------------------------------------------------------------ mesh
def rrect(rx, ry, z, n=48, p=9.0):
    xy = K_se(n, rx, ry, p)
    return np.array([(x, y, z) for x, y in xy])


def K_se(n, rx, ry, p):
    import bh_mesh as M
    return M.superellipse(n, rx, ry, p)


def lid_profile(off=0.0, n=16):
    """Closed YZ cross-section of the lid (front-bottom -> arch -> back-bottom -> flat bottom), offset outward."""
    pts = [(-D2 - off, ZR + 0.0), (-D2 - off, ZR + 0.06)]
    for i in range(1, n):
        ph = math.pi * i / n
        pts.append((-(D2 + off) * math.cos(ph), ZR + 0.06 + (LID_H - 0.06 + off) * math.sin(ph)))
    pts += [(D2 + off, ZR + 0.06), (D2 + off, ZR + 0.0)]
    return pts


def lid_arch(t, off=0.0):
    """Point + outward normal on the lid's outer surface; t 0..1 from front-bottom over the top to back-bottom."""
    a = 0.06 / (0.06 + math.pi * 0.2 + 0.06)
    if t < a:
        return np.array([0.0, -D2 - off, ZR + 0.06 * t / a]), np.array([0.0, -1.0, 0.0])
    if t > 1 - a:
        return np.array([0.0, D2 + off, ZR + 0.06 * (1 - t) / a]), np.array([0.0, 1.0, 0.0])
    ph = math.pi * (t - a) / (1 - 2 * a)
    ry, rz = D2, LID_H - 0.06
    p = np.array([0.0, -ry * math.cos(ph), ZR + 0.06 + rz * math.sin(ph)])
    nrm = K.unit(np.array([0.0, -math.cos(ph) / ry, math.sin(ph) / rz]))
    return p + nrm * off, nrm


def build_mesh():
    import bh_mesh as M
    parts = []
    rng = np.random.default_rng(7)

    def add(p, **kw):
        K.bind(p, RIG, **kw)
        parts.append(p)
        return p

    def solid(V, F, mat, name):
        return M.recalc_normals(M.Part(V, F, mat, name=name))

    def tooth(base, d, length, r, mat="BH_Bone"):
        d = K.unit(d)
        V, F = M.tube([base, base + d * length * 0.55, base + d * length], [(r, r * 0.8), (r * 0.6, r * 0.5),
                      (0.0015, 0.0015)], n=5, up=(1, 0, 0) if abs(d[0]) < 0.9 else (0, 1, 0), cap1=False)
        return M.Part(V, F, mat, name="tooth")

    # ---- box: one watertight cup (outer walls, bevelled bottom, rim, inner walls, interior floor)
    rings = [rrect(W2 - 0.018, D2 - 0.018, Z0), rrect(W2, D2, Z0 + 0.018), rrect(W2, D2, ZR - 0.004),
             rrect(W2 - 0.006, D2 - 0.006, ZR), rrect(W2 - WALL, D2 - WALL, ZR),
             rrect(W2 - WALL, D2 - WALL, FLOOR)]
    V, F = M.loft(rings, cap0=True, cap1=True)
    add(solid(V, F, "BH_Wood", "box"), bone="body")
    # mouth lining (inward-facing flesh walls + floor)
    li = [rrect(W2 - WALL - 0.004, D2 - WALL - 0.004, ZR - 0.008), rrect(W2 - WALL - 0.004, D2 - WALL - 0.004,
                                                                        FLOOR + 0.004)]
    V, F = M.loft(li, cap0=False, cap1=True)
    add(K.orient(M.Part(V, F, "BH_Leather", name="lining"), (0, 0, ZR + 0.3)), bone="body")
    # maw (dark pit in the floor, front-center) with a gum ring
    V, F = M.sphere(1.0, 20, 6, center=(0, -0.08, FLOOR + 0.006), scale=(0.3, 0.15, 0.012))
    add(M.Part(V, F, "BH_Shadow", name="maw"), bone="body")
    V, F = M.tube([(0, 0.02, FLOOR + 0.03), (0, 0.09, FLOOR + 0.07), (0, TJ[0][1] + 0.02, TJ[0][2] - 0.01)],
                  [(0.1, 0.05), (0.085, 0.05), (0.06, 0.03)], n=10, up=(0, 0, 1))
    add(M.Part(V, F, "BH_Leather", name="tongue_root"), bone="body")
    # gold heap at the back + scattered coins
    V, F = M.sphere(1.0, 20, 8, center=(0, 0.14, FLOOR), scale=(0.4, 0.16, 0.11))
    add(M.Part(V, F, "BH_Gold", name="heap"), bone="body")
    for i in range(46):
        if i < 30:
            a = rng.random() * 2 * math.pi
            r = math.sqrt(rng.random())
            x, y = 0.38 * r * math.cos(a), 0.14 + 0.15 * r * math.sin(a)
            z = FLOOR + 0.11 * math.sqrt(max(0.0, 1 - (x / 0.4) ** 2 - ((y - 0.14) / 0.16) ** 2)) + 0.004
        else:
            x = (rng.random() - 0.5) * 0.82
            y = -0.2 + 0.1 * rng.random() if abs(x) > 0.3 else 0.0
            if abs(x) <= 0.3:
                x = math.copysign(0.32 + 0.1 * rng.random(), x)
                y = (rng.random() - 0.5) * 0.4
            z = FLOOR + 0.008
        V, F = M.lathe([(0.0, -0.002), (0.022, -0.002), (0.022, 0.002), (0.0, 0.002)], n=10)
        R = K.R_axis(rng.normal(size=3), 25 + 40 * rng.random())
        V = V @ R.T + np.array([x, y, z])
        add(M.Part(V, F, "BH_Gold", name="coin"), bone="body")
    # plank seams (dark grooves) on the outer walls
    for z in (Z0 + 0.16, Z0 + 0.32):
        V, F = M.loft([rrect(W2 - 0.003, D2 - 0.003, z - 0.005), rrect(W2 + 0.0025, D2 + 0.0025, z - 0.005),
                       rrect(W2 + 0.0025, D2 + 0.0025, z + 0.005), rrect(W2 - 0.003, D2 - 0.003, z + 0.005)],
                      cap0=False, cap1=False)
        add(solid(V, F, "BH_Hair", "seam"), bone="body")
    # iron bands (box): bottom + top rings, vertical straps front/back, corner caps, rivets
    for z0, z1 in ((Z0 + 0.03, Z0 + 0.085), (ZR - 0.07, ZR - 0.015)):
        V, F = M.loft([rrect(W2 - 0.004, D2 - 0.004, z0), rrect(W2 + 0.01, D2 + 0.01, z0),
                       rrect(W2 + 0.01, D2 + 0.01, z1), rrect(W2 - 0.004, D2 - 0.004, z1)], cap0=False, cap1=False)
        add(solid(V, F, "BH_DarkSteel", "band"), bone="body")
    for sx in (1, -1):
        for sy in (1, -1):
            V, F = M.box(0.075, 0.014, ZR - Z0 - 0.02, center=(sx * 0.3, sy * (D2 + 0.006), (Z0 + ZR) / 2))
            add(solid(V, F, "BH_DarkSteel", "strap"), bone="body")
            V, F = M.box(0.012, 0.09, ZR - Z0 - 0.02, center=(sx * (W2 + 0.006), sy * (D2 - 0.06), (Z0 + ZR) / 2))
            add(solid(V, F, "BH_DarkSteel", "corner"), bone="body")
            V, F = M.box(0.09, 0.012, ZR - Z0 - 0.02, center=(sx * (W2 - 0.06), sy * (D2 + 0.006), (Z0 + ZR) / 2))
            add(solid(V, F, "BH_DarkSteel", "corner"), bone="body")
            for z in (Z0 + 0.057, ZR - 0.043, (Z0 + ZR) / 2):
                V, F = M.sphere(0.011, 6, 3, center=(sx * 0.3, sy * (D2 + 0.014), z))
                add(M.Part(V, F, "BH_DarkSteel", name="rivet"), bone="body")
    # side handles (iron rings)
    for sx in (1, -1):
        ang = np.linspace(math.pi, 2 * math.pi, 9)
        pts = [(sx * (W2 + 0.03), 0.09 * math.cos(a), Z0 + 0.33 + 0.07 * math.sin(a)) for a in ang]
        V, F = M.tube(pts, [(0.011, 0.011)] * len(pts), n=6, up=(1, 0, 0))
        add(M.Part(V, F, "BH_DarkSteel", name="handle"), bone="body")
        for y in (-0.09, 0.09):
            V, F = M.box(0.02, 0.05, 0.05, center=(sx * (W2 + 0.012), y, Z0 + 0.33))
            add(solid(V, F, "BH_DarkSteel", "handle_mount"), bone="body")
    # keyhole plate on the box front
    V, F = M.box(0.13, 0.014, 0.12, center=(0, -D2 - 0.006, ZR - 0.1))
    add(solid(V, F, "BH_Gold", "lockplate"), bone="body")
    V, F = M.box(0.016, 0.01, 0.045, center=(0, -D2 - 0.012, ZR - 0.11))
    add(solid(V, F, "BH_Shadow", "keyhole"), bone="body")
    V, F = M.sphere(0.014, 8, 4, center=(0, -D2 - 0.012, ZR - 0.082), scale=(1, 0.5, 1))
    add(M.Part(V, F, "BH_Shadow", name="keyhole"), bone="body")
    # box teeth: jagged, along the inner rim (front, sides, a few at the back), pointing up / slightly inward
    xy = K_se(34, W2 - WALL - 0.02, D2 - WALL - 0.02, 9.0)
    for i, (x, y) in enumerate(xy):
        if y > D2 - 0.07 and i % 2:
            continue
        L = (0.06 + 0.04 * rng.random()) * (1.3 if abs(x) < 0.2 and y < 0 else 1.0)
        base = np.array([x, y, ZR - 0.035])
        d = np.array([-x * 0.25, -y * 0.3, 1.0]) + rng.normal(size=3) * 0.08
        add(tooth(base, d, L + 0.035, 0.02), bone="body")
    # ---- lid (bound to the lid bone)
    prof = lid_profile()
    xs = [-W2, -W2 + 0.012, W2 - 0.012, W2]
    rings = []
    for j, x in enumerate(xs):
        sh = 0.012 if j in (0, 3) else 0.0
        rings.append(np.array([(x, y * (1 - sh / D2), ZR + (z - ZR) * (1 - sh / LID_H) if z > ZR else z)
                               for (y, z) in prof]))
    V, F = M.loft(rings, cap0=True, cap1=True)
    add(solid(V, F, "BH_Wood", "lid"), bone="lid")
    # lid seams (planks along the barrel)
    for t in (0.33, 0.5, 0.67):
        pts, ups = [], []
        p, nrm = lid_arch(t, 0.0015)
        for x in np.linspace(-W2 + 0.02, W2 - 0.02, 3):
            pts.append(p + np.array([x, 0, 0]))
        V, F = M.tube(pts, [(0.004, 0.004)] * 3, n=4, up=tuple(nrm))
        add(M.Part(V, F, "BH_Hair", name="lid_seam"), bone="lid")
    # lid iron straps over the arch (x = +-0.3 and the two edges) + rivets
    for x, wdt in ((0.3, 0.038), (-0.3, 0.038), (W2 - 0.03, 0.03), (-W2 + 0.03, 0.03)):
        ts = np.linspace(0, 1, 22)
        pts, ups = [], []
        for t in ts:
            p, nrm = lid_arch(t, 0.006)
            pts.append(p + np.array([x, 0, 0]))
            ups.append(nrm)
        V, F = M.tube(pts, [(wdt, 0.008, 8.0)] * len(pts), n=8, up=ups, cap0=True, cap1=True)
        add(solid(V, F, "BH_DarkSteel", "lid_strap"), bone="lid")
        if abs(x) < 0.4:
            for t in (0.12, 0.3, 0.5, 0.7, 0.88):
                p, nrm = lid_arch(t, 0.014)
                V, F = M.sphere(0.011, 6, 3, center=p + np.array([x, 0, 0]))
                add(M.Part(V, F, "BH_DarkSteel", name="rivet"), bone="lid")
    # hinges at the back
    for x in (0.3, -0.3):
        V, F = M.tube([(x - 0.05, D2 + 0.018, ZR), (x + 0.05, D2 + 0.018, ZR)], [(0.018, 0.018)] * 2, n=8,
                      up=(0, 0, 1))
        add(M.Part(V, F, "BH_DarkSteel", name="hinge"), bone="lid")
    # hasp (gold) hanging over the box front from the lid
    V, F = M.box(0.08, 0.014, 0.1, center=(0, -D2 - 0.016, ZR - 0.02))
    add(solid(V, F, "BH_Gold", "hasp"), bone="lid")
    V, F = M.box(0.1, 0.02, 0.05, center=(0, -D2 - 0.01, ZR + 0.035))
    add(solid(V, F, "BH_Gold", "hasp_top"), bone="lid")
    # underside: gum sheet, teeth pointing down, the two glowing eyes
    V, F = M.box(2 * (W2 - WALL - 0.008), 2 * (D2 - WALL - 0.008), 0.012, center=(0, 0, ZR - 0.004))
    add(solid(V, F, "BH_Leather", "gums"), bone="lid")
    xy = K_se(30, W2 - WALL - 0.045, D2 - WALL - 0.045, 9.0)
    for i, (x, y) in enumerate(xy):
        if y > D2 - 0.1:
            continue
        L = (0.05 + 0.04 * rng.random()) * (1.3 if abs(x) < 0.2 and y < 0 else 1.0)
        base = np.array([x, y, ZR - 0.008])
        d = np.array([-x * 0.2, -y * 0.25, -1.0]) + rng.normal(size=3) * 0.08
        add(tooth(base, d, L, 0.018), bone="lid")
    for sx in (1, -1):
        c0 = np.array([sx * 0.14, 0.03, ZR - 0.035])
        V, F = M.sphere(0.075, 12, 6, center=c0 + (0, 0, 0.012), scale=(1.0, 0.9, 0.5))
        add(M.Part(V, F, "BH_Leather", name="eye_socket"), bone="lid")
        V, F = M.sphere(0.052, 14, 8, center=c0)
        add(M.Part(V, F, "BH_Emissive", name="eye"), bone="lid")
        V, F = M.sphere(0.05, 10, 6, center=c0 + (0, 0, -0.031), scale=(0.22, 0.9, 0.5))
        add(M.Part(V, F, "BH_Shadow", name="pupil"), bone="lid")
    # ---- tongue: dense flattened tube along the joint polyline, hat weights (stretches without thickening)
    pts = [TJ[0] + (TJ[-1] - TJ[0]) * (i / 30.0) for i in range(31)]
    pts += [TJ[-1] + (TTIP - TJ[-1]) * (i / 5.0) for i in range(1, 6)]
    prof = []
    for i, q in enumerate(pts):
        s = i / (len(pts) - 1)
        w = 0.052 * (1 - 0.35 * s)
        h = 0.022 * (1 - 0.4 * s)
        if i >= len(pts) - 3:
            k = (len(pts) - 1 - i) / 3.0
            w, h = w * (0.35 + 0.65 * k), h * (0.4 + 0.6 * k)
        prof.append((w, h))
    prof[-1] = (0.006, 0.004)
    V, F = M.tube(pts, prof, n=12, up=(0, 0, 1))
    tp = M.Part(V, F, "BH_Flesh", name="tongue")
    tp.W = K.hat_weights(V, TJ + [TTIP], [f"tongue.{i}" for i in range(6)])
    parts.append(tp)
    # ---- legs: dusky fleshy crab legs with a horn claw + two side toes
    for k, (th, sh, ft) in LEGS.items():
        pts, prof = [H[th] - RIG.rdir(th) * 0.02], [(0.068, 0.068)]
        for b, nseg, r0, r1 in ((th, 4, 0.075, 0.064), (sh, 5, 0.064, 0.042)):
            for i in range(1, nseg + 1):
                t = i / nseg
                pts.append(H[b] * (1 - t) + T[b] * t)
                r = r0 * (1 - t) + r1 * t
                prof.append((r, r * 1.1))
        V, F = M.tube(pts, prof, n=9, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Skin", name="leg"), chain=[th, sh, ft], blend=0.3)
        V, F = M.sphere(0.074, 10, 6, center=T[th])
        add(M.Part(V, F, "BH_Skin", name="knee"), chain=[th, sh], blend=0.5)
        d = RIG.rdir(ft)
        V, F = M.tube([H[ft] - d * 0.02, H[ft] + d * 0.05, T[ft] + d * 0.01], [(0.042, 0.04), (0.028, 0.026),
                      (0.003, 0.003)], n=7, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Horn", name="claw"), chain=[sh, ft], blend=0.25)
        side = K.unit(np.cross(d, [0, 0, 1.0]))
        for sgn in (1, -1):
            dd = K.unit(d + side * 0.8 * sgn)
            b0 = H[ft] + d * 0.02
            V, F = M.tube([b0, b0 + dd * 0.05, b0 + dd * 0.085 + np.array([0, 0, -0.035])],
                          [(0.016, 0.015), (0.011, 0.01), (0.002, 0.002)], n=5, up=(0, 0, 1))
            add(M.Part(V, F, "BH_Horn", name="toe"), bone=ft)
        # a few bristles
        for i in range(4):
            t = 0.2 + 0.2 * i
            b = th if i < 2 else sh
            q = H[b] * (1 - t) + T[b] * t + np.array([0, 0, 0.04])
            V, F = M.tube([q, q + np.array([0, 0.01, 0.045])], [(0.006, 0.006), (0.001, 0.001)], n=4, up=(1, 0, 0))
            add(M.Part(V, F, "BH_Hair", name="bristle"), bone=b)
    return parts


# ------------------------------------------------------------------------------------------------ analysis
def reach_report(clip):
    worst = 0.0
    for f in range(clip.frames + 1):
        c = clip.channels(float(f % clip.frames if clip.loop else f))
        if c.get("legs.fold", 0.0) > 0.01:
            continue
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
            tgt[2] = max(tgt[2], FLOORZ)
            worst = max(worst, float(np.linalg.norm(foot(X, k) - tgt)))
    return worst


def dormant_check():
    """Every vertex that is not chest/lid/body-rigid must end up inside the closed box in mimic_dormant: report the
    lowest point and the max |x|,|y| of all leg + tongue bone heads/tails (with the leg mesh radius they stay hidden)."""
    c = next(x for x in clips() if x.name == "mimic_dormant")
    X = evaluate(c.channels(0.0))
    pts = []
    for k in LEG_IDS:
        for b in LEGS[k]:
            pts += [RIG.head(X, b), RIG.tail(X, b)]
    for i in range(6):
        pts += [RIG.head(X, f"tongue.{i}"), RIG.tail(X, f"tongue.{i}")]
    P = np.array(pts)
    return float(P[:, 2].min()), float(P[:, 2].max()), float(np.abs(P[:, 0]).max()), float(np.abs(P[:, 1]).max())


# ------------------------------------------------------------------------------------------------ main
def main():
    a = K.std_args()
    import bh_mesh as M
    C = clips()
    only = set(x for x in a.clips.split(",") if x) or None
    arm, mesh, acts = K.build_all(CID, RIG, evaluate, C, build_mesh, PALETTE, only=only, ao=(16, 0.25, 0.6))
    tris = M.tri_count(mesh)
    print(f"[{CID}] mesh {tris} tris, {len(mesh.data.vertices)} verts, {len(RIG.ORDER)} bones, {len(acts)} clips")
    slide = {c.name: K.foot_slide(c, evaluate, foot, LEG_IDS, c.meta["ground_speed"], FLOORZ + 0.012)
             for c in C if "ground_speed" in c.meta}
    for n, v in slide.items():
        print(f"[{CID}] foot slip {n}: max {v[0] * 1000:.2f} mm/frame, mean {v[1] * 1000:.2f}, stance {v[2]:.2f}")
    reach = {c.name: reach_report(c) for c in C}
    print(f"[{CID}] worst IK reach miss per clip (mm): " + ", ".join(f"{n} {v * 1000:.1f}" for n, v in reach.items()))
    dz = dormant_check()
    print(f"[{CID}] dormant: leg/tongue bone points z {dz[0]:.3f}..{dz[1]:.3f}, |x| <= {dz[2]:.3f}, |y| <= {dz[3]:.3f}"
          f" (box: z 0..{ZR - LIFT:.2f}, |x| < {W2}, |y| < {D2})")
    ct = next(x for x in C if x.name == "mimic_tongue")
    tip = [tongue_tip(evaluate(ct.channels(float(f)))) for f in range(ct.frames + 1)]
    reach_t = max(-p[1] for p in tip)
    ftip = int(np.argmax([-p[1] for p in tip]))
    print(f"[{CID}] mimic_tongue: tip reaches {reach_t:.2f} m in front of the origin at f{ftip} "
          f"(tip height {tip[ftip][2]:.2f} m)")
    K.quick_preview(CID, arm, acts, a, 0.5, 3.6)
    if a.evidence:
        K.evidence_rest(CID, arm, 0.5, 3.4, "Treasure Mimic - rest pose (awake stance, lid shut)")
        K.evidence_rest(CID, arm, 0.4, 3.4, "Treasure Mimic - mimic_dormant (what the player sees)",
                        pose=("mimic_dormant", 0), acts=acts)
        K.evidence_rest(CID, arm, 0.5, 3.4, "Treasure Mimic - idle frame 0", pose=("idle", 0), acts=acts)
        spec = [("mimic_wake", [0, 5 / 36, 9 / 36, 15 / 36, 21 / 36, 1.0]),
                ("walk", [0, 0.25, 0.5, 0.75]), ("run", [0, 0.5]),
                ("mimic_bite", [6 / 24, 9 / 24, 12 / 24, 13 / 24, 16 / 24, 1.0]),
                ("mimic_slam", [7 / 36, 13 / 36, 18 / 36, 22 / 36, 25 / 36, 1.0]),
                ("death", [5 / 45, 11 / 45, 20 / 45, 1.0]), ("death_back", [6 / 45, 14 / 45, 1.0]),
                ("alert", [8 / 30]), ("hit_heavy", [4 / 18]), ("knockback", [4 / 27])]
        K.evidence_clips(CID, arm, acts, spec, 0.5, 4.4, "Treasure Mimic - clips (view yaw 55)", yaw=55, cols=6)
        K.evidence_clips(CID, arm, acts, [("mimic_tongue", [0, 6 / 36, 12 / 36, 15 / 36, 22 / 36, 1.0])], 0.7, 6.5,
                         "Treasure Mimic - mimic_tongue (side view; hit = full ~3 m extension)", yaw=90, pitch=8,
                         name="tongue_side", cols=6)
        K.evidence_clips(CID, arm, acts, [("walk", [i / 7 for i in range(7)])], 0.45, 3.6,
                         "Treasure Mimic - walk cycle, side view", yaw=90, pitch=6, name="walk_side", cols=7)
    if not a.no_export and not only:
        K.merge_meta(CID, C, "tools/blender/creatures/build_mimic.py", {"tris": tris, "bones": len(RIG.ORDER)})
        bad, got = K.export(CID, arm, mesh, acts, OUT_GLB)
        assert not bad, bad
    notes = [f"Generator: `tools/blender/creatures/build_mimic.py` -> `game/assets/characters/{CID}.glb`",
             "", "- Size: chest 1.00 m wide x 0.65 m deep x 0.75 m tall closed; awake stance lifts it 0.30 m on four "
             "legs (foot span ~1.45 m).",
             f"- Triangles: {tris}; vertices {len(mesh.data.vertices)}; bones {len(RIG.ORDER)} (root non-deform).",
             f"- Materials: {', '.join(sorted(m.name for m in mesh.data.materials))}",
             "- Bones: " + ", ".join(f"`{b}`" for b in RIG.ORDER),
             "- Rest pose = awake stance with the lid shut. `mimic_dormant` = chest on the ground, legs scaled to 1.5 % "
             "about their roots (inside the solid box bottom), lid shut, tongue inside, no motion.",
             f"- Dormant check: leg/tongue bone points z {dz[0]:.3f}..{dz[1]:.3f} m, |x| <= {dz[2]:.3f}, "
             f"|y| <= {dz[3]:.3f} (closed box spans z 0..{ZR - LIFT + LID_H:.2f}, |x| < {W2}, |y| < {D2}).",
             f"- mimic_tongue: tongue tip reaches {reach_t:.2f} m in front of the origin at frame {ftip} "
             f"({ftip / FPS:.2f} s), {tip[ftip][2]:.2f} m high.", "",
             "## Clips", ""] + K.clip_table(C) + [
             "", "## Foot contact (in-place clips; stance feet slide back at exactly ground_speed)", "",
             "| clip | max slip mm/frame | mean slip mm/frame | stance fraction |", "|---|---|---|---|"] + [
             f"| {n} | {v[0] * 1000:.2f} | {v[1] * 1000:.2f} | {v[2]:.2f} |" for n, v in slide.items()] + [
             "", "Worst IK reach miss per clip (mm; folded / curled legs excluded): " +
             ", ".join(f"{n} {v * 1000:.1f}" for n, v in reach.items())]
    K.write_md(CID, "Treasure Mimic (treasure_mimic.glb)", notes)


if __name__ == "__main__":
    main()
