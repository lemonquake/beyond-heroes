"""Sepulchre Beetle (bh-029, Builder M5, Zarael / the Jade Sepulchre tank/charger): a ~2.4 m beetle (horn tip to the
end of the wing cases) that ate the Sepulchre's funeral offerings for a thousand years and grew a shell of the jade it
lived in. A domed pronotum and two great elytra of polished jade inlaid with gold wire (stepped-fret bands across
the shoulders, lines down each wing case, gold-edged rims), a dark-jade head carrying a tall curved horn banded in
gold with a white wire channel up its front, serrated black mandibles, white compound eyes, clubbed antennae, a white
glow deep in the mouth (its spit), six spined legs of dark jade with gold joint rings, dark underside plates. The
elytra are on their own bones: they lift and part when it rears, rams or dies.

  "<blender>" -b --factory-startup --python build_sepulchre_beetle.py -- [--no-export] [--evidence] [--prev DIR]
                                                                       [--sheet a,b] [--clips a,b]

Rig / pose machinery: creature_kit_c (imported, not edited); the layout follows build_glasswire_scorpion.py: legs are
4 bones each (coxa, femur, tibia, tarsus) solved per frame with creature_kit_c.plane_leg, stance feet world-fixed;
six legs in an alternating tripod gait (L1 R2 L3 / R1 L2 R3). A beetle has six legs: the 8-leg ("spider") kit is
used with three pairs. Head (FK) with mandible.L/R, elytra.L/R (FK).
Conventions: Blender Z-up, faces -Y (= +Z in Godot), origin on the ground under the body, meters, 30 fps, in place.
Clips: generic set (idle idle_look walk run run_combat hit_light hit_heavy stagger_small knockback death death_back
alert) + beetle_bite (head lunges, mandibles snap), beetle_ram (crouch, paw, head down, lunge horn-first),
beetle_spit (rears, wing cases lift, head thrown forward spitting). creature_meta.json: merges ONLY
animations.beetle_* and models.sepulchre_beetle (re-read right before writing, verified after).
GLOW: pure white (BH_Emissive albedo / emission (1, 1, 1), energy 5).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import creature_kit_c as K  # noqa: E402
from creature_kit_c import Clip, Xf, Rx, Ry, Rz, cyc, pulse, spine_rot, smooth, FPS  # noqa: E402

import numpy as np  # noqa: E402

CID = "sepulchre_beetle"
OUT_GLB = os.path.join(K.CHAR_OUT, f"{CID}.glb")
SCRATCH = os.path.join(K.ROOT_DIR, "work", "lemondev", "bh-029", "scratch", "m5", "ev", "beetle")
PALETTE = {
    "BH_Stone": ((0.1, 0.42, 0.3), 0.0, 0.26, None, 0.0, 1.0),            # polished jade shell
    "BH_Horn": ((0.035, 0.15, 0.1), 0.0, 0.35, None, 0.0, 1.0),          # dark jade: head, horn, legs
    "BH_Gold": ((0.76, 0.54, 0.2), 1.0, 0.3, None, 0.0, 1.0),            # gold wire inlay / rings
    "BH_Flesh": ((0.05, 0.06, 0.045), 0.0, 0.5, None, 0.0, 1.0),         # dark underside plates
    "BH_Leather": ((0.03, 0.03, 0.025), 0.0, 0.6, None, 0.0, 1.0),       # joint membranes, folded wings
    "BH_DarkSteel": ((0.02, 0.022, 0.02), 0.4, 0.25, None, 0.0, 1.0),    # black mandibles / claws / spines
    "BH_Shadow": ((0.01, 0.012, 0.01), 0.0, 0.7, None, 0.0, 1.0),        # mouth, grooves
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),  # eyes, horn channel, mouth (white)
}

# ------------------------------------------------------------------------------------------------ skeleton
BZ = 0.42                       # body centre height
PIVOT = np.array([0.0, 0.05, BZ])
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.25), None),
    "body": ((0, 0.9, BZ), (0, -0.4, BZ), "root"),
    "head": ((0, -0.4, BZ + 0.04), (0, -0.7, BZ), "body"),
}
for _s, _x in (("L", 1.0), ("R", -1.0)):
    BONES[f"mand.{_s}"] = ((0.07 * _x, -0.66, BZ - 0.06), (0.03 * _x, -0.92, BZ - 0.09), "head")
    BONES[f"elytra.{_s}"] = ((0.1 * _x, -0.02, BZ + 0.36), (0.14 * _x, 0.92, BZ + 0.18), "body")
# walking legs n: (attach on the L side, azimuth deg (+ = toward the front), foot reach)
LEG_SPEC = {1: ((0.2, -0.32, BZ - 0.08), 42.0, 0.74), 2: ((0.25, -0.08, BZ - 0.08), -4.0, 0.78),
            3: ((0.24, 0.16, BZ - 0.08), -42.0, 0.84)}
LEGS = {}
for _s, _x in (("L", 1.0), ("R", -1.0)):
    for _n, (_p, _az, _R) in LEG_SPEC.items():
        _P = np.array([_p[0] * _x, _p[1], _p[2]])
        _u = np.array([_x * math.cos(math.radians(_az)), -math.sin(math.radians(_az)), 0.0])

        def _pt(r, z, P=_P, u=_u):
            return tuple(P + u * r + np.array([0.0, 0.0, z - P[2]]))
        names = (f"coxa.{_n}.{_s}", f"femur.{_n}.{_s}", f"tibia.{_n}.{_s}", f"tarsus.{_n}.{_s}")
        pts = [tuple(_P), _pt(0.1, _P[2] - 0.01), _pt(0.46 * _R, 0.56), _pt(0.84 * _R, 0.2), _pt(_R, 0.015)]
        for i, nm in enumerate(names):
            BONES[nm] = (pts[i], pts[i + 1], "body" if i == 0 else names[i - 1])
        LEGS[f"{_s}{_n}"] = names
# everything above (and the mesh) is authored at a 2.0 m body; SC scales the rig and the mesh to the ~2.4 m beetle
SC = 1.22
RIG0 = K.Rig(BONES)
BONES = {k: (tuple(np.array(h) * SC), tuple(np.array(t) * SC), p) for k, (h, t, p) in BONES.items()}
PIVOT = PIVOT * SC
RIG = K.Rig(BONES)
H, T = RIG.H, RIG.T
LEG_IDS = [f"{s}{n}" for n in (1, 2, 3) for s in ("L", "R")]
NEUTRAL = {k: T[v[3]].copy() for k, v in LEGS.items()}
OUTW = {k: K.unit(np.array([(T[v[3]] - H[v[0]])[0], (T[v[3]] - H[v[0]])[1], 0.0])) for k, v in LEGS.items()}
BETA = {k: math.degrees(math.atan2(H[v[3]][2] - T[v[3]][2],
                                   np.linalg.norm((T[v[3]] - H[v[3]])[:2]))) for k, v in LEGS.items()}
GROUP_A = ("L1", "R2", "L3")
CURL = (-30.0, -150.0, 140.0)
FLOOR = 0.015


# ------------------------------------------------------------------------------------------------ pose
def evaluate(c):
    X = {}
    g = c.get
    t = np.array([g("body.side", 0.0), -g("body.fwd", 0.0), g("body.up", 0.0)])
    X["root"] = Xf.move(t) @ Xf.about(spine_rot(c, "body"), PIVOT)
    RIG.fk(X, "body", spine_rot(c, "shell"))
    RIG.fk(X, "head", spine_rot(c, "head"), off=np.array([0.0, -g("head.fwd", 0.0), 0.0]))
    for s, sx in (("L", 1.0), ("R", -1.0)):
        op = g("mand.open", 0.0) + g(f"mand.{s}.open", 0.0)
        RIG.fk(X, f"mand.{s}", Rz(sx * 30.0 * op))
        el = g("elytra.open", 0.0) + g(f"elytra.{s}.open", 0.0)
        RIG.fk(X, f"elytra.{s}", Rx(26.0 * el) @ Ry(-sx * 34.0 * el))
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
            ph = (0.0 if k in GROUP_A else 0.5) + 0.04 * (3 - int(k[1]))
            ff, up, sw = K.gait_foot(t - ph, duty, sweep, lift)
            out[k + ".f"] = ff
            out[k + ".up"] = up
            out[k + ".beta"] = -12.0 * math.sin(math.pi * sw) if sw >= 0 else 0.0
        return out
    return fn


def legs(**kw):
    out = {}
    groups = {"front": ("L1", "R1"), "mid": ("L2", "R2"), "back": ("L3", "R3"), "all": tuple(LEG_IDS)}
    for k in LEG_IDS:
        groups[k] = (k,)
    for gname, d in kw.items():
        for k in groups[gname]:
            for chn, v in d.items():
                out[f"{k}_{chn}"] = v
    return out


def clips():
    C = []
    # ---- idle: shell breathes, head bobs, mandibles work
    c = Clip("idle", 90, loop=True)
    c.key(0)
    c.layer(lambda f, cl: {"body.up": 0.008 * cyc(f, 90, 2), "shell.pitch": 0.8 * cyc(f, 90, 1, 0.2),
                           "head.pitch": 2.0 * cyc(f, 90, 1, 0.4), "head.yaw": 3.0 * cyc(f, 90, 1, 0.1),
                           "mand.open": 0.12 + 0.12 * cyc(f, 30, 1),
                           "elytra.open": 0.02 + 0.02 * cyc(f, 90, 2)})
    C.append(c)
    c = Clip("idle_look", 75)
    c.key(0).key(15, body_yaw=10, head_yaw=14, head_pitch=4, mand_open=0.3)
    c.key(32, body_yaw=11, head_yaw=12, head_pitch=2, mand_open=0.1)
    c.key(48, body_yaw=-10, head_yaw=-14, head_pitch=4, mand_open=0.3)
    c.key(62, body_yaw=-9, head_yaw=-12, head_pitch=2, mand_open=0.1)
    c.key(75, body_yaw=0, head_yaw=0, head_pitch=0, mand_open=0.0)
    C.append(c)
    # ---- walk / run: alternating tripod
    WP, WV = 22, 1.3
    c = Clip("walk", WP, loop=True, ground_speed=WV)
    c.key(0)
    c.layer(gait_layer(WP, 0.6, WV, 0.12))
    c.layer(lambda f, cl: {"body.up": -0.01 + 0.008 * cyc(f, WP, 2, 0.1), "body.roll": 1.5 * cyc(f, WP, 1, 0.1),
                           "shell.yaw": 1.5 * cyc(f, WP, 1, 0.25), "head.yaw": 3.0 * cyc(f, WP, 1, 0.5),
                           "mand.open": 0.1})
    C.append(c)
    for nm, v, crouch in (("run", 4.0, -0.03), ("run_combat", 3.8, -0.07)):
        RP = 10
        c = Clip(nm, RP, loop=True, ground_speed=v)
        c.key(0)
        c.layer(gait_layer(RP, 0.5, v, 0.16))
        c.layer(lambda f, cl, cr=crouch: {
            "body.up": cr + 0.012 * cyc(f, RP, 2, 0.15), "body.pitch": (-4.0 if cr < -0.05 else -2.0) +
            1.5 * cyc(f, RP, 2, 0.4), "body.roll": 2.0 * cyc(f, RP, 1, 0.1),
            "head.pitch": -14.0 if cr < -0.05 else -4.0, "mand.open": 0.25 if cr < -0.05 else 0.1,
            "elytra.open": 0.06 if cr < -0.05 else 0.0})
        C.append(c)
    # ---- reactions
    c = Clip("hit_light", 12)
    c.key(0).key(3, body_fwd=-0.05, body_up=0.02, body_pitch=5, head_pitch=8, mand_open=0.4, legs_follow=0.3)
    c.key(12, body_fwd=0, body_up=0, body_pitch=0, head_pitch=0, mand_open=0, legs_follow=0)
    C.append(c)
    c = Clip("hit_heavy", 18)
    c.key(0).key(4, body_fwd=-0.13, body_up=-0.04, body_pitch=9, body_roll=5, head_pitch=14, head_yaw=10,
                 mand_open=0.8, elytra_open=0.15, legs_spread=0.05, legs_follow=0.4)
    c.key(9, body_fwd=-0.1, body_up=-0.06, body_pitch=4, body_roll=2, head_pitch=6, head_yaw=4, mand_open=0.4,
          elytra_open=0.05, legs_spread=0.06, legs_follow=0.3)
    c.key(18, body_fwd=0, body_up=0, body_pitch=0, body_roll=0, head_pitch=0, head_yaw=0, mand_open=0,
          elytra_open=0, legs_spread=0, legs_follow=0)
    C.append(c)
    c = Clip("stagger_small", 24)
    c.key(0).key(5, body_fwd=-0.07, body_side=-0.06, body_roll=-8, body_yaw=-8, head_yaw=10, mand_open=0.5,
                 legs_follow=0.35, **legs(R2=dict(up=0.1), L1=dict(up=0.08)))
    c.key(10, body_fwd=-0.08, body_side=-0.08, body_roll=-5, body_yaw=-6, head_yaw=6, legs_follow=0.3,
          **legs(R2=dict(up=0.0, side=0.08), L1=dict(up=0.0, f=-0.04)))
    c.key(16, body_fwd=-0.04, body_side=-0.03, body_roll=-2, body_yaw=-2, head_yaw=2, legs_follow=0.15)
    c.key(24, body_fwd=0, body_side=0, body_roll=0, body_yaw=0, head_yaw=0, mand_open=0, legs_follow=0,
          **legs(R2=dict(side=0.0), L1=dict(f=0.0)))
    C.append(c)
    c = Clip("knockback", 27)
    c.key(0).key(4, body_fwd=-0.22, body_up=0.06, body_pitch=12, head_pitch=16, mand_open=0.9, elytra_open=0.25,
                 legs_follow=0.7, **legs(front=dict(up=0.2, f=0.08), mid=dict(up=0.06)))
    c.key(11, body_fwd=-0.38, body_up=-0.05, body_pitch=2, head_pitch=4, mand_open=0.3, elytra_open=0.1,
          legs_follow=0.85, **legs(front=dict(up=0.0, f=0.1), mid=dict(up=0.0)))
    c.key(18, body_fwd=-0.18, body_up=-0.02, body_pitch=0, head_pitch=0, elytra_open=0.0, legs_follow=0.6,
          **legs(front=dict(f=0.03)))
    c.key(27, body_fwd=0, body_up=0, mand_open=0, legs_follow=0, **legs(front=dict(f=0.0)))
    C.append(c)
    # ---- deaths
    c = Clip("death", 45)          # legs buckle, it tips over onto its back, legs curl up
    c.key(0)
    c.key(6, body_up=-0.12, head_pitch=-10, mand_open=0.9, elytra_open=0.2, legs_spread=0.08, legs_curl=0.1)
    c.key(14, body_up=0.12, body_side=0.15, body_roll=70, head_pitch=-6, mand_open=0.7, elytra_open=0.3,
          legs_follow=0.8, legs_curl=0.4)
    c.key(22, body_up=0.22, body_side=0.3, body_roll=150, head_pitch=6, mand_open=0.5, elytra_open=0.35,
          legs_follow=1.0, legs_curl=0.75)
    c.key(30, body_up=0.38, body_side=0.32, body_roll=178, head_pitch=10, mand_open=0.6, elytra_open=0.2,
          legs_follow=1.0, legs_curl=1.0)
    c.key(45, body_up=0.38, body_side=0.32, body_roll=178, head_pitch=12, mand_open=0.3, elytra_open=0.18,
          legs_follow=1.0, legs_curl=1.0)
    c.layer(lambda f, cl: {k + ".curl": 0.12 * pulse(f, 28 + 2 * i, 42 + 2 * i) * (1 if i % 2 else -1)
                           for i, k in enumerate(LEG_IDS)})
    C.append(c)
    c = Clip("death_back", 45)     # rears, then drops flat, legs splay, wing cases fall open
    c.key(0)
    c.key(8, body_up=0.06, body_fwd=-0.05, body_pitch=14, head_pitch=16, mand_open=1.0, elytra_open=0.5,
          **legs(front=dict(up=0.2, f=0.08)))
    c.key(18, body_up=-0.3, body_fwd=-0.03, body_pitch=-3, head_pitch=-14, mand_open=0.6, elytra_open=0.7,
          legs_spread=0.28, **legs(front=dict(up=0.0, f=0.14)))
    c.key(24, body_up=-0.33, body_pitch=-5, head_pitch=-18, mand_open=0.5, elytra_open=0.75, legs_spread=0.4,
          legs_curl=0.2, **legs(front=dict(f=0.16)))
    c.key(45, body_up=-0.34, body_pitch=-6, head_pitch=-20, mand_open=0.4, elytra_open=0.72, legs_spread=0.42,
          legs_curl=0.35, **legs(front=dict(f=0.16)))
    C.append(c)
    # ---- alert: rears on the back legs, wing cases lift, mandibles wide, horn raised
    c = Clip("alert", 30)
    c.key(0).key(9, body_up=0.08, body_pitch=12, head_pitch=14, mand_open=1.0, elytra_open=0.45,
                 **legs(front=dict(f=-0.06, up=0.06)))
    c.key(20, body_up=0.07, body_pitch=10, head_pitch=10, mand_open=0.7, elytra_open=0.4,
          **legs(front=dict(f=-0.06, up=0.0)))
    c.key(30, body_up=0.0, body_pitch=0, head_pitch=0, mand_open=0.1, elytra_open=0.0, **legs(front=dict(f=0.0)))
    c.layer(lambda f, cl: {"elytra.open": 0.06 * cyc(f, 5, 1) * (1 if 8 < f < 22 else 0),
                           "mand.open": 0.25 * max(0.0, cyc(f, 8, 1)) * (1 if 8 < f < 22 else 0)})
    C.append(c)
    # ---- attacks
    # beetle_bite: head draws back, mandibles open wide, lunge and snap shut (hit 0.37-0.47 s)
    c = Clip("beetle_bite", 24, hits=[[11 / FPS, 14 / FPS]])
    c.key(0).key(7, body_fwd=-0.08, body_up=0.03, body_pitch=5, head_pitch=12, head_fwd=-0.03, mand_open=1.0,
                 **legs(front=dict(f=-0.03)))
    c.key(11, body_fwd=0.2, body_up=-0.02, body_pitch=-4, head_pitch=-10, head_fwd=0.06, mand_open=0.9,
          legs_follow=0.25, **legs(front=dict(f=0.1), mid=dict(f=0.05)))
    c.key(13, body_fwd=0.22, body_up=-0.03, body_pitch=-5, head_pitch=-12, head_fwd=0.07, mand_open=-0.25,
          legs_follow=0.25, **legs(front=dict(f=0.1), mid=dict(f=0.05)))
    c.key(24, body_fwd=0, body_up=0, body_pitch=0, head_pitch=0, head_fwd=0, mand_open=0, legs_follow=0,
          **legs(front=dict(f=0.0), mid=dict(f=0.0)))
    c.layer(lambda f, cl: {"head.yaw": 4.0 * math.sin(2 * math.pi * (f - 13) / 6) * pulse(f, 13, 20)})
    C.append(c)
    # beetle_ram: crouch, a front leg paws, head drops with the horn levelled, then a lunge horn-first
    # (hit 0.6-0.73 s; the game then holds run_combat for the charge itself)
    c = Clip("beetle_ram", 30, hits=[[18 / FPS, 22 / FPS]])
    low = dict(body_up=-0.08, body_pitch=-6, head_pitch=-22, mand_open=0.3, elytra_open=0.12)
    c.key(0).key(5, body_fwd=-0.12, body_up=-0.06, body_pitch=-3, head_pitch=-12, mand_open=0.2, elytra_open=0.1,
                 **legs(back=dict(f=-0.05)))
    c.key(9, body_fwd=-0.16, **low, **legs(R1=dict(up=0.12, f=0.06), back=dict(f=-0.06)))
    c.key(12, body_fwd=-0.16, **low, **legs(R1=dict(up=0.0, f=-0.06), back=dict(f=-0.06)))
    c.key(15, body_fwd=-0.18, **low, **legs(R1=dict(up=0.08, f=0.04), back=dict(f=-0.06)))
    c.key(18, body_fwd=0.26, body_up=-0.06, body_pitch=-8, head_pitch=-26, head_fwd=0.08, mand_open=0.35,
          elytra_open=0.18, legs_follow=0.3, **legs(R1=dict(up=0.0, f=0.12), L1=dict(f=0.12), mid=dict(f=0.06),
                                                    back=dict(f=0.0)))
    c.key(22, body_fwd=0.32, body_up=-0.07, body_pitch=-9, head_pitch=-24, head_fwd=0.09, mand_open=0.3,
          elytra_open=0.18, legs_follow=0.35, **legs(R1=dict(f=0.14), L1=dict(f=0.14), mid=dict(f=0.07)))
    c.key(30, body_fwd=0, body_up=0, body_pitch=0, head_pitch=0, head_fwd=0, mand_open=0, elytra_open=0,
          legs_follow=0, **legs(R1=dict(f=0.0), L1=dict(f=0.0), mid=dict(f=0.0)))
    C.append(c)
    # beetle_spit: rears back (wing cases lift, abdomen pumps), head thrown up, then forward and down: the spit
    # leaves the mouth at ~0.9 s (the game's 1.0 s wind-up), hit 0.87-1.03 s
    c = Clip("beetle_spit", 40, hits=[[26 / FPS, 31 / FPS]])
    rear = dict(body_fwd=-0.12, body_up=0.1, body_pitch=16, head_pitch=24, mand_open=0.9, elytra_open=0.45)
    c.key(0).key(14, **rear, **legs(front=dict(up=0.05, f=-0.05)))
    c.key(23, **dict(rear, body_pitch=19, head_pitch=30, elytra_open=0.55), **legs(front=dict(up=0.08, f=-0.06)))
    c.key(27, body_fwd=0.12, body_up=-0.02, body_pitch=-6, head_pitch=-18, head_fwd=0.07, mand_open=1.1,
          elytra_open=0.3, legs_follow=0.2, **legs(front=dict(up=0.0, f=0.08)))
    c.key(31, body_fwd=0.13, body_up=-0.03, body_pitch=-7, head_pitch=-20, head_fwd=0.08, mand_open=1.0,
          elytra_open=0.25, legs_follow=0.2, **legs(front=dict(f=0.08)))
    c.key(40, body_fwd=0, body_up=0, body_pitch=0, head_pitch=0, head_fwd=0, mand_open=0, elytra_open=0,
          legs_follow=0, **legs(front=dict(f=0.0)))
    c.layer(lambda f, cl: {"shell.pitch": 2.5 * math.sin(2 * math.pi * f / 7) * pulse(f, 4, 24),
                           "elytra.open": 0.05 * math.sin(2 * math.pi * f / 5) * pulse(f, 6, 24)})
    C.append(c)
    return C


# ------------------------------------------------------------------------------------------------ mesh
def build_mesh():
    import bh_mesh as M
    import kit_a_common as A
    import enemy_glyphbound_warrior as Z
    parts = []
    pending = []
    H, T = RIG0.H, RIG0.T            # author against the unscaled rig; vertices are scaled by SC before binding

    def add(p, **kw):
        pending.append((p, kw))
        return p

    def P(V, F, mat, name="part"):
        return M.Part(np.asarray(V, float), F, mat, name=name)

    def ring(y, zc, rx, rt, rb, n=22, p=0.8, cx=0.0):
        a = np.linspace(0, 2 * math.pi, n, endpoint=False)
        return np.array([(cx + rx * np.sign(math.cos(t)) * abs(math.cos(t)) ** p, y,
                          zc + (rt if math.sin(t) > 0 else rb) * math.sin(t)) for t in a])

    # ---- underbody (abdomen + thorax underside), dark
    V, F = M.loft([ring(y, BZ + 0.02, rx, rt, rb, n=18) for y, rx, rt, rb in
                   ((-0.42, 0.2, 0.1, 0.1), (-0.25, 0.3, 0.16, 0.13), (0.0, 0.36, 0.2, 0.15), (0.35, 0.38, 0.22, 0.15),
                    (0.7, 0.32, 0.18, 0.12), (0.92, 0.18, 0.1, 0.07))], cap0=True, cap1=True)
    add(M.recalc_normals(P(V, F, "BH_Flesh", "abdomen")), bone="body")
    for y in np.linspace(0.05, 0.8, 6):           # underside plates
        w = 0.3 - 0.25 * ((y - 0.3) / 0.6) ** 2
        V, F = M.box(w * 1.6, 0.1, 0.025, center=(0, y, BZ - 0.12))
        add(M.bevel(P(V, F, "BH_Flesh", "sternite"), 0.008, 1), bone="body")
    # folded wings (dark membrane) on the back, under the elytra
    for sx in (1, -1):
        V, F = M.box(0.2, 0.75, 0.012, center=(sx * 0.12, 0.42, BZ + 0.22))
        add(P(V, F, "BH_Leather", "wing").rot(Ry(sx * 8), center=(sx * 0.12, 0.42, BZ + 0.22)), bone="body")

    # ---- pronotum: a broad domed shield, gold-rimmed, a stepped-fret band in gold, a low keel
    PRO = [(-0.46, BZ + 0.14, 0.22, 0.12, 0.12), (-0.4, BZ + 0.16, 0.3, 0.2, 0.15), (-0.28, BZ + 0.17, 0.37, 0.28, 0.17),
           (-0.12, BZ + 0.17, 0.4, 0.31, 0.17), (0.0, BZ + 0.16, 0.4, 0.3, 0.16), (0.04, BZ + 0.15, 0.37, 0.26, 0.13)]
    V, F = M.loft([ring(*r, n=26, p=0.75) for r in PRO], cap0=True, cap1=True)
    add(M.bevel(M.recalc_normals(P(V, F, "BH_Stone", "pronotum")), 0.008, 1), bone="body")

    def pro_top(x, y, out=0.004):
        """Point on the upper surface of the pronotum at (x, y)."""
        ys = [r[0] for r in PRO]
        zc = np.interp(y, ys, [r[1] for r in PRO])
        rx = np.interp(y, ys, [r[2] for r in PRO])
        rt = np.interp(y, ys, [r[3] for r in PRO])
        u = min(abs(x) / rx, 0.999)
        # superellipse p=0.75: x = rx*|cos|^0.75 -> cos = u^(1/0.75)
        cs = u ** (1 / 0.75)
        sn = math.sqrt(max(1 - cs * cs, 0.0))
        return np.array([x, y, zc + rt * sn + out])
    # gold rim round the pronotum's front edge
    rim = [ring(-0.43, BZ + 0.15, 0.27, 0.16, 0.13, n=26, p=0.75)[i] for i in range(0, 14)]
    add(A.tube(rim, 0.012, "BH_Gold", n=5), bone="body")
    # stepped-fret band across the pronotum (gold wire in a dark groove)
    fw = Z.fret_wave(4, steps=2)
    pts = [pro_top(-0.3 + 0.6 * u, -0.2 + 0.08 * v, 0.002) for u, v in fw]
    add(A.tube(pts, 0.007, "BH_Gold", n=4), bone="body")
    pts = [pro_top(x, -0.215, 0.0) for x in np.linspace(-0.32, 0.32, 9)]
    add(A.tube(pts, 0.006, "BH_Gold", n=4), bone="body")
    pts = [pro_top(x, -0.105, 0.0) for x in np.linspace(-0.32, 0.32, 9)]
    add(A.tube(pts, 0.006, "BH_Gold", n=4), bone="body")
    # keel down the middle with a white knot of wire where the gold lines meet
    add(A.tube([pro_top(0, y, 0.0) for y in np.linspace(-0.4, 0.02, 6)], 0.016, "BH_Stone", n=6), bone="body")
    add(A.ball(pro_top(0, -0.3, 0.012), 0.022, "BH_Gold", n=8, rings=5, scale=(1, 1.3, 0.6)), bone="body")
    add(A.ball(pro_top(0, -0.3, 0.022), 0.011, "BH_Emissive", n=6, rings=4), bone="body")
    # side gold studs
    for sx in (1, -1):
        for y in (-0.32, -0.16, -0.02):
            add(A.ball(pro_top(sx * 0.3, y, 0.0), 0.016, "BH_Gold", n=6, rings=4, scale=(1, 1, 0.6)), bone="body")

    # ---- elytra: two great jade wing cases, gold-wire inlay, gold rims (on the elytra bones)
    def ely(sx, u, v, out=0.0):
        w = 0.42 * (1 - 0.55 * v ** 3)
        Hh = 0.27 * (1 - v ** 2.4) + 0.06
        x = sx * (0.012 + w * math.sin(u * math.pi / 2))
        z = BZ + 0.13 + Hh * math.cos(u * math.pi / 2) ** 0.7 - 0.12 * u ** 3
        y = 0.0 + 0.98 * v - 0.02 * math.sin(u * math.pi) * 0.0
        # rounded end: pull the tip in
        if v > 0.85:
            k = (v - 0.85) / 0.15
            x = sx * (0.012 + (abs(x) - 0.012) * (1 - 0.55 * k ** 2))
        n = np.array([sx * math.sin(u * math.pi / 2) * 1.0, 0.3 * v, math.cos(u * math.pi / 2) + 0.2])
        n = n / np.linalg.norm(n)
        return np.array([x, y, z]) + n * out
    for s, sx in (("L", 1.0), ("R", -1.0)):
        bone = f"elytra.{s}"
        V, F = M.grid(lambda u, v, sx=sx: tuple(ely(sx, u, v)), 9, 12)
        sh = P(V, F, "BH_Stone", "elytron")
        nn = np.cross(V[F[0][1]] - V[F[0][0]], V[F[0][2]] - V[F[0][0]])
        cen = V[F[0][0]]
        if np.dot(nn, cen - np.array([0, 0.4, BZ])) < 0:
            sh.flip()
        add(M.solidify(sh, 0.022, offset=-1.0), bone=bone)
        # inlay lines down the case (gold) + the gold-edged suture and outer rim
        for u0 in (0.28, 0.55, 0.8):
            pts = [ely(sx, u0, v, 0.004) for v in np.linspace(0.06, 0.88, 9)]
            add(A.tube(pts, 0.006, "BH_Gold", n=4), bone=bone)
        add(A.tube([ely(sx, 0.02, v, 0.006) for v in np.linspace(0.0, 0.98, 10)], 0.011, "BH_Gold", n=5), bone=bone)
        add(A.tube([ely(sx, 1.0, v, -0.004) for v in np.linspace(0.0, 0.96, 10)], 0.01, "BH_Gold", n=5), bone=bone)
        # stepped-fret band across the shoulders of the case
        fw = Z.fret_wave(2, steps=2)
        pts = [ely(sx, 0.08 + 0.8 * u, 0.1 + 0.06 * v, 0.004) for u, v in fw]
        add(A.tube(pts, 0.0055, "BH_Gold", n=4), bone=bone)
        # white knots where the lines cross the band, and a row of jade bosses along the middle line
        for u0 in (0.28, 0.55, 0.8):
            add(A.ball(ely(sx, u0, 0.13, 0.008), 0.012, "BH_Emissive", n=6, rings=4), bone=bone)
        for v0 in (0.32, 0.5, 0.68):
            add(A.ball(ely(sx, 0.42, v0, 0.006), 0.02, "BH_Stone", n=8, rings=4, scale=(1, 1, 0.55)), bone=bone)
            add(A.tube([ely(sx, 0.42, v0, 0.0), ely(sx, 0.42, v0, 0.012)], 0.026, "BH_Gold", n=8), bone=bone)

    # ---- head, horn, eyes, antennae, mouth
    hb = "head"
    V, F = M.loft([ring(y, BZ + 0.02 + dz, rx, rt, rb, n=18) for y, dz, rx, rt, rb in
                   ((-0.36, 0.04, 0.2, 0.11, 0.1), (-0.48, 0.03, 0.21, 0.12, 0.1), (-0.6, 0.0, 0.18, 0.1, 0.09),
                    (-0.68, -0.03, 0.13, 0.07, 0.07))], cap0=True, cap1=True)
    add(M.recalc_normals(P(V, F, "BH_Horn", "head")), bone=hb)
    # the horn: a tall curved horn rising from the head's front, flattened sideways, banded in gold
    hp = [(0, -0.5, BZ + 0.1), (0, -0.66, BZ + 0.2), (0, -0.82, BZ + 0.38), (0, -0.9, BZ + 0.58), (0, -0.88, BZ + 0.76),
          (0, -0.8, BZ + 0.88)]
    hr = [(0.09, 0.1), (0.075, 0.085), (0.06, 0.07), (0.045, 0.052), (0.03, 0.035), (0.008, 0.01)]
    add(A.tube(hp, hr, "BH_Horn", n=10), bone=hb)
    hp = np.array(hp)
    for i, u in enumerate((0.18, 0.4, 0.62)):
        k = int(u * (len(hp) - 1))
        t = u * (len(hp) - 1) - k
        q = hp[k] * (1 - t) + hp[k + 1] * t
        d = K.unit(hp[k + 1] - hp[k])
        r = hr[k][1] * (1 - t) + hr[k + 1][1] * t
        add(A.tube([q - d * 0.016, q + d * 0.016], r + 0.008, "BH_Gold", n=10), bone=hb)
    # white channel up the horn's front (the current the beetles drank with the offerings)
    ch = []
    for i in range(len(hp) - 1):
        for t in (0.0, 0.5):
            q = hp[i] * (1 - t) + hp[i + 1] * t
            d = K.unit(hp[i + 1] - hp[i])
            fwd = K.unit(np.cross(d, (1.0, 0, 0)))
            r = hr[i][1] * (1 - t) + hr[i + 1][1] * t
            ch.append(q + fwd * r * 0.98)
    add(A.tube(ch[1:-1], 0.007, "BH_Emissive", n=4), bone=hb)
    # tines at the tip and a lower brow ridge
    for sx in (1, -1):
        add(A.taper([hp[4] + (sx * 0.02, 0.0, 0.0), hp[4] + (sx * 0.08, -0.05, 0.06)], 0.018, 0.003, "BH_Horn", n=5),
            bone=hb)
    # compound eyes: white, ringed dark
    for sx in (1, -1):
        add(A.ball((sx * 0.17, -0.52, BZ + 0.05), 0.048, "BH_Shadow", n=10, rings=6, scale=(0.7, 1.1, 0.9)), bone=hb)
        add(A.ball((sx * 0.18, -0.52, BZ + 0.05), 0.036, "BH_Emissive", n=10, rings=6, scale=(0.7, 1.1, 0.9)),
            bone=hb)
        # clubbed antennae curving out and back
        a = [(sx * 0.12, -0.62, BZ + 0.02), (sx * 0.24, -0.72, BZ + 0.06), (sx * 0.33, -0.7, BZ + 0.13)]
        add(A.tube(a, [0.012, 0.008, 0.007], "BH_DarkSteel", n=5), bone=hb)
        for k in range(3):
            add(A.ball(np.array(a[2]) + np.array([sx * 0.025 * k, 0.012 * k, 0.012 * k]), 0.022 - 0.003 * k,
                       "BH_DarkSteel", n=6, rings=4, scale=(1.0, 0.6, 1.0)), bone=hb)
    # mouth: dark gape with the white spit glow deep inside, palps
    add(A.ball((0, -0.68, BZ - 0.05), 0.07, "BH_Shadow", n=10, rings=5, scale=(1.2, 0.6, 0.7)), bone=hb)
    add(A.ball((0, -0.705, BZ - 0.05), 0.03, "BH_Emissive", n=8, rings=4, scale=(1.2, 0.6, 0.8)), bone=hb)
    for sx in (1, -1):
        add(A.tube([(sx * 0.05, -0.66, BZ - 0.1), (sx * 0.07, -0.74, BZ - 0.16), (sx * 0.06, -0.8, BZ - 0.18)],
                   [0.012, 0.009, 0.006], "BH_Horn", n=5), bone=hb)
    # mandibles: curved black pincers with inner teeth
    for s, sx in (("L", 1.0), ("R", -1.0)):
        b = f"mand.{s}"
        m = [H[b], H[b] + np.array([sx * 0.06, -0.1, -0.01]), H[b] + np.array([sx * 0.04, -0.2, -0.025]),
             T[b] + np.array([-sx * 0.02, -0.02, -0.005])]
        add(A.tube(m, [(0.045, 0.03), (0.04, 0.026), (0.026, 0.018), (0.004, 0.004)], "BH_DarkSteel", n=7,
                   up=(0, 0, 1)), bone=b)
        for k in range(3):
            q = np.array(m[1]) * (1 - k / 3) + np.array(m[2]) * (k / 3) - np.array([sx * 0.03, 0, 0])
            add(A.shard(q, (-sx, -0.3, 0.0), 0.04, 0.012, "BH_DarkSteel", sides=4, up=(0, 0, 1)), bone=b)
        add(A.tube([H[b] + np.array([0, 0.02, 0]), H[b] + np.array([sx * 0.02, -0.04, 0])], 0.05, "BH_Gold", n=8),
            bone=b)

    # ---- legs: dark jade, flattened femora, spined tibiae, gold joint rings, segmented tarsi with claws
    for kk, (cx, fe, ti, ta) in LEGS.items():
        pts, prof = [], []
        segs = [(cx, 2, 0.07, 0.065), (fe, 5, 0.068, 0.055), (ti, 5, 0.05, 0.036), (ta, 4, 0.026, 0.014)]
        pts.append(H[cx] - RIG0.rdir(cx) * 0.02)
        prof.append((0.05, 0.055))
        for b, nseg, r0, r1 in segs:
            for i in range(1, nseg + 1):
                t = i / nseg
                pts.append(H[b] * (1 - t) + T[b] * t)
                r = r0 * (1 - t) + r1 * t
                prof.append((r * (0.75 if b == fe else 0.9), r * (1.3 if b == fe else 1.1)))
        prof[-1] = (0.006, 0.006)
        V, F = M.tube(pts, prof, n=6, up=(0, 0, 1))
        add(P(V, F, "BH_Horn", "leg"), chain=[cx, fe, ti, ta], blend=0.28)
        for b, nb, r in ((fe, ti, 0.05), (ti, ta, 0.037)):
            add(A.ball(T[b], r, "BH_Leather", n=7, rings=4), chain=[b, nb], blend=0.5)
            d = RIG0.rdir(b)
            add(A.tube([T[b] - d * 0.05, T[b] - d * 0.03], r * 1.12, "BH_Gold", n=8), bone=b)
        # tibia spines
        d = RIG0.rdir(ti)
        out = K.unit(np.cross(d, (0, 0, 1)))
        for i in range(4):
            q = H[ti] + (T[ti] - H[ti]) * (0.25 + 0.18 * i)
            add(A.shard(q, out * (1 if kk[0] == "L" else -1) * 0.4 + d * 0.6 + np.array([0, 0, -0.2]), 0.05, 0.01,
                        "BH_DarkSteel", sides=4, up=(0, 0, 1)), bone=ti)
        # tarsal segments + hooked claws
        dt = RIG0.rdir(ta)
        for i in range(3):
            q = H[ta] + (T[ta] - H[ta]) * (0.25 + 0.25 * i)
            add(A.ball(q, 0.02 - 0.003 * i, "BH_Horn", n=6, rings=4, scale=(1, 1, 0.8)), bone=ta)
        for sx in (1, -1):
            side = K.unit(np.cross(dt, (0, 0, 1))) * sx
            add(A.taper([T[ta], T[ta] + dt * 0.03 + side * 0.03 + np.array([0, 0, -0.01])], 0.007, 0.0015,
                        "BH_DarkSteel", n=4), bone=ta)
        # a gold coxa plate
        add(A.ball(H[cx], 0.06, "BH_Horn", n=8, rings=5, scale=(1.0, 1.0, 0.8)), bone="body")
    for p, kw in pending:
        p.V = p.V * SC
        K.bind(p, RIG, **kw)
        parts.append(p)
    return parts


# ------------------------------------------------------------------------------------------------ analysis / meta
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


def horn_tip(clip, f):
    X = evaluate(clip.channels(float(f)))
    return X["head"].apply(np.array([0.0, -0.8, BZ + 0.88]) * SC)


def merge_meta(C, tris, bones):
    """Merge ONLY animations.beetle_* and models.sepulchre_beetle; re-read right before writing, keep every other
    key, write, re-read and verify."""
    mine = {c.name: K.clip_entry(c) for c in C if c.name.startswith("beetle_")}
    model = {"generator": "tools/blender/creatures/build_sepulchre_beetle.py",
             "glb": f"res://assets/characters/{CID}.glb", "clips": {c.name: K.clip_entry(c) for c in C},
             "tris": tris, "bones": bones}
    with open(K.META) as fh:
        data = json.load(fh)
    before_a = {k: v for k, v in data.get("animations", {}).items() if not k.startswith("beetle_")}
    before_m = {k: v for k, v in data.get("models", {}).items() if k != CID}
    data.setdefault("animations", {}).update(mine)
    data.setdefault("models", {})[CID] = model
    with open(K.META, "w") as fh:
        json.dump(data, fh, indent=1)
    with open(K.META) as fh:
        chk = json.load(fh)
    ok = (all(chk["animations"].get(k) == v for k, v in mine.items()) and chk["models"].get(CID) == model
          and all(chk["animations"].get(k) == v for k, v in before_a.items())
          and all(chk["models"].get(k) == v for k, v in before_m.items()))
    print(f"[{CID}] meta merged {sorted(mine)} + models.{CID} -> {K.META} (verified: {ok})")
    if not ok:
        raise RuntimeError("creature_meta merge verification failed")


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
        if only and c.name not in only:
            continue
        if "ground_speed" in c.meta:
            v = K.foot_slide(c, evaluate, foot, LEG_IDS, c.meta["ground_speed"], FLOOR + 0.012)
            print(f"[{CID}] foot slip {c.name}: max {v[0] * 1000:.2f} mm/frame, mean {v[1] * 1000:.2f}, "
                  f"stance {v[2]:.2f}")
        if c.name in ("beetle_ram", "beetle_bite"):
            for f in (0, int(c.meta["hits"][0][0] * FPS), int(c.meta["hits"][0][1] * FPS)):
                print(f"[{CID}] {c.name} f{f} horn tip at {np.round(horn_tip(c, f), 3)}")
    print(f"[{CID}] worst IK reach miss per clip (mm): " +
          ", ".join(f"{c.name} {reach_report(c) * 1000:.1f}" for c in C if not only or c.name in only))
    K.quick_preview(CID, arm, acts, a, 0.6, 6.5)
    if a.evidence:
        K.evidence_rest(CID, arm, 0.65, 6.6, "Sepulchre Beetle - rest (4 views + 3/4 + gameplay iso 26 m / 55 deg)",
                        iso_scales=(1.0,), base=SCRATCH)
        spec = [("idle", [0.0]), ("walk", [0, 0.25, 0.5, 0.75]), ("alert", [0.3]),
                ("beetle_bite", [0, 7 / 24, 11 / 24, 13 / 24, 1.0]),
                ("beetle_ram", [0, 9 / 30, 15 / 30, 18 / 30, 22 / 30, 1.0]),
                ("beetle_spit", [0, 14 / 40, 23 / 40, 27 / 40, 31 / 40, 1.0]),
                ("hit_heavy", [0.22]), ("death", [0.3, 0.6, 1.0]), ("death_back", [0.5, 1.0])]
        K.evidence_clips(CID, arm, acts, spec, 0.7, 7.0, "Sepulchre Beetle - clips (view yaw 50)", yaw=50, cols=6,
                         base=SCRATCH)
    if not a.no_export and not only:
        bad, got = K.export(CID, arm, mesh, acts, OUT_GLB)
        assert not bad, bad
        merge_meta(C, tris, len(RIG.ORDER))


if __name__ == "__main__":
    main()
