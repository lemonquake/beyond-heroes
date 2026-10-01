"""Glasswire Scorpion (bh-029, Builder M2, Zarael / the Glasswire Barrens tank/striker): a ~3 m scorpion (pincer tips
to the raised tail's curl ~2.6 m on the ground, ~3.3 m with the tail stretched) whose shell is smoky dark glass, the
Blackwire-grown glass of the Barrens. Under the glass, along every plate, leg and tail segment, runs white-glowing
wire; copper wire is wound round the joints. A flat prosoma shield with two glowing median eyes, seven overlapping
glass tergites with a keel of glass shards, two heavy chelae (serrated glass fingers), eight long faceted legs, and a
six-segment tail raised over the back ending in a glowing bulb and a black curved sting with a white-hot tip.

  "<blender>" -b --factory-startup --python build_glasswire_scorpion.py -- [--no-export] [--evidence] [--prev DIR]
                                                                       [--sheet a,b] [--clips a,b]

Rig / pose machinery: creature_kit_c (imported, not edited); the layout follows build_reef_crawler.py (pincers: FK
chains claw.1..claw.4; legs: 4 bones each solved per frame with creature_kit_c.plane_leg, stance feet world-fixed,
alternating tetrapod gait L1 R2 L3 R4 / R1 L2 R3 L4) plus an FK tail chain tail.1..tail.6 + sting.
Conventions: Blender Z-up, faces -Y (= +Z in Godot), origin on the ground under the body, meters, 30 fps, in place.
Clips: generic set (idle idle_look walk run run_combat hit_light hit_heavy stagger_small knockback death death_back
alert) + scorp_pinch (both chelae snap forward), scorp_sting (tail strikes forward over the head), scorp_spray (tail
held forward sweeps an arc, for a cone). creature_meta.json: merges ONLY animations.scorp_* and
models.glasswire_scorpion (re-read right before writing, verified after).
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

CID = "glasswire_scorpion"
OUT_GLB = os.path.join(K.CHAR_OUT, f"{CID}.glb")
SCRATCH = os.path.join(K.ROOT_DIR, "work", "lemondev", "bh-029", "scratch", "m2", "ev", "scorp")
PALETTE = {
    "BH_Horn": ((0.1, 0.09, 0.12), 0.3, 0.1, None, 0.0, 1.0),          # smoky dark glass shell
    "BH_Stone": ((0.3, 0.27, 0.36), 0.1, 0.08, None, 0.0, 1.0),           # lighter glass: rims, keel shards, teeth
    "BH_Leather": ((0.035, 0.03, 0.036), 0.0, 0.55, None, 0.0, 1.0),      # dark joint membranes
    "BH_Flesh": ((0.09, 0.08, 0.09), 0.0, 0.5, None, 0.0, 1.0),           # underside plates
    "BH_Gold": ((0.6, 0.34, 0.18), 1.0, 0.38, None, 0.0, 1.0),            # copper wire wound round the joints
    "BH_DarkSteel": ((0.025, 0.024, 0.03), 0.4, 0.25, None, 0.0, 1.0),    # black sting / claw tips / leg tips
    "BH_Shadow": ((0.012, 0.01, 0.014), 0.0, 0.6, None, 0.0, 1.0),        # mouth
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),  # wire inside the glass (pure white)
}

# ------------------------------------------------------------------------------------------------ skeleton
BZ = 0.52                       # body (pedicel) height
PIVOT = np.array([0.0, 0.0, BZ])
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.25), None),
    "body": ((0, 0.6, BZ), (0, -0.62, BZ), "root"),
}
CK = 1.75                        # chela scale vs the reef crawler's
for _s, _x in (("L", 1.0), ("R", -1.0)):
    sh = np.array([0.2 * _x, -0.6, BZ - 0.02])
    el = sh + np.array([0.17 * _x, -0.15, 0.06]) * CK
    wr = el + np.array([-0.07 * _x, -0.2, 0.0]) * CK
    tip = wr + np.array([-0.04 * _x, -0.24, -0.03]) * CK
    hinge = wr + (tip - wr) * 0.45 + np.array([0.035 * _x, 0, 0.0]) * CK
    BONES.update({
        f"claw.1.{_s}": (tuple(sh), tuple(el), "body"),
        f"claw.2.{_s}": (tuple(el), tuple(wr), f"claw.1.{_s}"),
        f"claw.3.{_s}": (tuple(wr), tuple(tip), f"claw.2.{_s}"),
        f"claw.4.{_s}": (tuple(hinge), tuple(hinge + np.array([-0.025 * _x, -0.38, -0.03]) * CK), f"claw.3.{_s}"),
    })
# tail: rest arc rising from the back of the body, curling forward over the back
TAIL_PTS = [(0, 0.6, BZ + 0.08), (0, 0.86, BZ + 0.2), (0, 1.04, BZ + 0.42), (0, 1.1, BZ + 0.68), (0, 1.03, BZ + 0.93),
            (0, 0.86, BZ + 1.1), (0, 0.63, BZ + 1.15), (0, 0.5, BZ + 1.03)]
TAIL = [f"tail.{i}" for i in range(1, 7)] + ["sting"]
for _i, _b in enumerate(TAIL):
    BONES[_b] = (TAIL_PTS[_i], TAIL_PTS[_i + 1], "body" if _i == 0 else TAIL[_i - 1])
# walking legs n: (attach on the L side, azimuth deg (+ = toward the front), foot reach)
LEG_SPEC = {1: ((0.22, -0.4, BZ - 0.02), 36.0, 0.78), 2: ((0.26, -0.2, BZ - 0.02), 10.0, 0.86),
            3: ((0.26, 0.0, BZ - 0.02), -16.0, 0.86), 4: ((0.22, 0.2, BZ - 0.02), -42.0, 0.82)}
LEGS = {}
for _s, _x in (("L", 1.0), ("R", -1.0)):
    for _n, (_p, _az, _R) in LEG_SPEC.items():
        _P = np.array([_p[0] * _x, _p[1], _p[2]])
        _u = np.array([_x * math.cos(math.radians(_az)), -math.sin(math.radians(_az)), 0.0])

        def _pt(r, z, P=_P, u=_u):
            return tuple(P + u * r + np.array([0.0, 0.0, z - P[2]]))
        names = (f"coxa.{_n}.{_s}", f"femur.{_n}.{_s}", f"tibia.{_n}.{_s}", f"tarsus.{_n}.{_s}")
        pts = [tuple(_P), _pt(0.08, _P[2] + 0.02), _pt(0.48 * _R, 0.78), _pt(0.84 * _R, 0.3), _pt(_R, 0.015)]
        for i, nm in enumerate(names):
            BONES[nm] = (pts[i], pts[i + 1], "body" if i == 0 else names[i - 1])
        LEGS[f"{_s}{_n}"] = names
RIG = K.Rig(BONES)
H, T = RIG.H, RIG.T
LEG_IDS = [f"{s}{n}" for n in (1, 2, 3, 4) for s in ("L", "R")]
NEUTRAL = {k: T[v[3]].copy() for k, v in LEGS.items()}
OUTW = {k: K.unit(np.array([(T[v[3]] - H[v[0]])[0], (T[v[3]] - H[v[0]])[1], 0.0])) for k, v in LEGS.items()}
BETA = {k: math.degrees(math.atan2(H[v[3]][2] - T[v[3]][2],
                                   np.linalg.norm((T[v[3]] - H[v[3]])[:2]))) for k, v in LEGS.items()}
GROUP_A = ("L1", "R2", "L3", "R4")
CURL = (-40.0, -150.0, 140.0)
FLOOR = 0.015
# per-segment weight of the global tail curl (the upper segments do most of the striking)
CURL_W = [0.5, 0.8, 1.0, 1.0, 0.9, 0.7, 0.5]


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
        RIG.fk(X, f"claw.4.{s}", Rz(sx * 34.0 * ch("open")))
    for i, b in enumerate(TAIL):
        pitch = g("tail.curl", 0.0) * CURL_W[i] + g(f"tail.{i + 1}", 0.0)
        yaw = (g("tail.yaw", 0.0) if i == 0 else 0.0) + g("tail.sway", 0.0) * (0.25 if i > 0 else 0.0)
        RIG.fk(X, b, Rz(yaw) @ Rx(pitch))
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
            ph = (0.0 if k in GROUP_A else 0.5) + 0.04 * (4 - int(k[1]))
            ff, up, sw = K.gait_foot(t - ph, duty, sweep, lift)
            out[k + ".f"] = ff
            out[k + ".up"] = up
            out[k + ".beta"] = -12.0 * math.sin(math.pi * sw) if sw >= 0 else 0.0
        return out
    return fn


def legs(**kw):
    out = {}
    groups = {"front": ("L1", "R1"), "mid": ("L2", "R2", "L3", "R3"), "back": ("L4", "R4"), "all": tuple(LEG_IDS)}
    for k in LEG_IDS:
        groups[k] = (k,)
    for gname, d in kw.items():
        for k in groups[gname]:
            for chn, v in d.items():
                out[f"{k}_{chn}"] = v
    return out


def clips():
    C = []
    # ---- idle: shell breathes, tail sways and twitches, claws flex
    c = Clip("idle", 90, loop=True)
    c.key(0)
    c.layer(lambda f, cl: {"body.up": 0.008 * cyc(f, 90, 2), "shell.pitch": 1.0 * cyc(f, 90, 1, 0.2),
                           "tail.curl": 3.0 * cyc(f, 90, 1), "tail.sway": 4.0 * cyc(f, 90, 1, 0.3),
                           "tail.6": 4.0 * cyc(f, 45, 1), "claw.lift": 3.0 * cyc(f, 90, 2, 0.1),
                           "claw.R.open": 0.3 * max(0.0, cyc(f, 90, 3)) ** 2,
                           "claw.L.open": 0.25 * max(0.0, cyc(f, 90, 2, 0.4)) ** 2})
    C.append(c)
    # ---- idle_look: body turns left / right, tail follows, claws feel
    c = Clip("idle_look", 75)
    c.key(0).key(15, body_yaw=12, tail_yaw=-10, claw_L_lift=10, claw_L_open=0.5)
    c.key(32, body_yaw=13, tail_yaw=-8, claw_L_lift=4, claw_L_open=0.0)
    c.key(48, body_yaw=-12, tail_yaw=10, claw_L_lift=0, claw_R_lift=10, claw_R_open=0.5)
    c.key(62, body_yaw=-10, tail_yaw=8, claw_R_lift=4, claw_R_open=0.0)
    c.key(75, body_yaw=0, tail_yaw=0, claw_R_lift=0)
    c.layer(lambda f, cl: {"tail.6": 5.0 * cyc(f, 25, 1)})
    C.append(c)
    # ---- walk / run: alternating tetrapod, claws carried, tail bobbing
    WP, WV = 26, 1.5
    c = Clip("walk", WP, loop=True, ground_speed=WV)
    c.key(0)
    c.layer(gait_layer(WP, 0.62, WV, 0.13))
    c.layer(lambda f, cl: {"body.up": -0.01 + 0.01 * cyc(f, WP, 2, 0.1), "body.roll": 1.5 * cyc(f, WP, 1, 0.1),
                           "shell.yaw": 1.5 * cyc(f, WP, 1, 0.25), "claw.lift": 6 + 3 * cyc(f, WP, 1),
                           "tail.curl": 2.0 * cyc(f, WP, 2), "tail.sway": 4.0 * cyc(f, WP, 1, 0.3)})
    C.append(c)
    for nm, v, crouch in (("run", 4.2, -0.03), ("run_combat", 3.8, -0.07)):
        RP = 14
        c = Clip(nm, RP, loop=True, ground_speed=v)
        c.key(0)
        c.layer(gait_layer(RP, 0.5, v, 0.16))
        c.layer(lambda f, cl, cr=crouch: {
            "body.up": cr + 0.012 * cyc(f, RP, 2, 0.15), "body.pitch": -2.0 + 1.5 * cyc(f, RP, 2, 0.4),
            "body.roll": 2.0 * cyc(f, RP, 1, 0.1), "claw.lift": 12 + (8 if cr < -0.05 else 0),
            "claw.fold": 10.0 if cr < -0.05 else 4.0, "claw.open": 0.3 if cr < -0.05 else 0.1,
            "tail.curl": (8.0 if cr < -0.05 else 4.0) + 3.0 * cyc(f, RP, 2), "tail.sway": 5.0 * cyc(f, RP, 1, 0.3)})
        C.append(c)
    # ---- reactions
    c = Clip("hit_light", 12)
    c.key(0).key(3, body_fwd=-0.05, body_up=0.02, body_pitch=5, claw_lift=12, claw_open=0.4, tail_curl=-8,
                 legs_follow=0.3)
    c.key(12, body_fwd=0, body_up=0, body_pitch=0, claw_lift=0, claw_open=0, tail_curl=0, legs_follow=0)
    C.append(c)
    c = Clip("hit_heavy", 18)
    c.key(0).key(4, body_fwd=-0.13, body_up=-0.04, body_pitch=9, body_roll=5, claw_lift=24, claw_yaw=14,
                 claw_open=0.8, tail_curl=-16, tail_yaw=10, legs_spread=0.05, legs_follow=0.4)
    c.key(9, body_fwd=-0.1, body_up=-0.06, body_pitch=4, body_roll=2, claw_lift=10, claw_yaw=6, claw_open=0.4,
          tail_curl=-6, tail_yaw=4, legs_spread=0.06, legs_follow=0.3)
    c.key(18, body_fwd=0, body_up=0, body_pitch=0, body_roll=0, claw_lift=0, claw_yaw=0, claw_open=0, tail_curl=0,
          tail_yaw=0, legs_spread=0, legs_follow=0)
    C.append(c)
    c = Clip("stagger_small", 24)
    c.key(0).key(5, body_fwd=-0.07, body_side=-0.06, body_roll=-8, body_yaw=-8, claw_R_lift=16, claw_L_lift=6,
                 claw_open=0.5, tail_yaw=12, legs_follow=0.35, **legs(R2=dict(up=0.1), L1=dict(up=0.08)))
    c.key(10, body_fwd=-0.08, body_side=-0.08, body_roll=-5, body_yaw=-6, claw_R_lift=8, claw_L_lift=2, tail_yaw=6,
          legs_follow=0.3, **legs(R2=dict(up=0.0, side=0.08), L1=dict(up=0.0, f=-0.04)))
    c.key(16, body_fwd=-0.04, body_side=-0.03, body_roll=-2, body_yaw=-2, tail_yaw=2, legs_follow=0.15)
    c.key(24, body_fwd=0, body_side=0, body_roll=0, body_yaw=0, claw_R_lift=0, claw_L_lift=0, claw_open=0, tail_yaw=0,
          legs_follow=0, **legs(R2=dict(side=0.0), L1=dict(f=0.0)))
    C.append(c)
    c = Clip("knockback", 27)
    c.key(0).key(4, body_fwd=-0.22, body_up=0.06, body_pitch=12, claw_lift=30, claw_yaw=18, claw_open=0.9,
                 tail_curl=-20, legs_follow=0.7, **legs(front=dict(up=0.2, f=0.08), mid=dict(up=0.06)))
    c.key(11, body_fwd=-0.38, body_up=-0.05, body_pitch=2, claw_lift=8, claw_yaw=8, claw_open=0.3, tail_curl=-6,
          legs_follow=0.85, **legs(front=dict(up=0.0, f=0.1), mid=dict(up=0.0)))
    c.key(18, body_fwd=-0.18, body_up=-0.02, body_pitch=0, claw_lift=2, claw_yaw=2, tail_curl=0, legs_follow=0.6,
          **legs(front=dict(f=0.03)))
    c.key(27, body_fwd=0, body_up=0, claw_lift=0, claw_yaw=0, claw_open=0, legs_follow=0, **legs(front=dict(f=0.0)))
    C.append(c)
    # ---- deaths
    c = Clip("death", 45)          # legs buckle, it rolls onto its side, the tail uncurls and drops, legs curl
    c.key(0)
    c.key(6, body_up=-0.12, claw_lift=-10, claw_open=0.9, tail_curl=-14, legs_spread=0.08, legs_curl=0.1)
    c.key(14, body_up=0.06, body_side=0.12, body_roll=60, claw_lift=20, claw_yaw=20, tail_curl=-30, tail_yaw=20,
          legs_follow=0.8, legs_curl=0.45)
    c.key(22, body_up=-0.12, body_side=0.24, body_roll=95, body_pitch=-4, claw_lift=30, claw_yaw=24, claw_fold=20,
          tail_curl=-45, tail_yaw=30, legs_follow=1.0, legs_curl=0.8)
    c.key(30, body_up=-0.16, body_side=0.26, body_roll=92, body_pitch=-6, claw_lift=34, claw_fold=26,
          tail_curl=-52, tail_yaw=34, legs_follow=1.0, legs_curl=1.0, claw_open=0.5)
    c.key(45, body_up=-0.16, body_side=0.26, body_roll=92, body_pitch=-6, claw_lift=36, claw_yaw=24, claw_fold=30,
          tail_curl=-54, tail_yaw=34, legs_follow=1.0, legs_curl=1.0, claw_open=0.3)
    c.layer(lambda f, cl: {k + ".curl": 0.12 * pulse(f, 28 + 2 * i, 40 + 2 * i) * (1 if i % 2 else -1)
                           for i, k in enumerate(LEG_IDS)})
    C.append(c)
    c = Clip("death_back", 45)     # rears, then drops flat, legs splay, tail slumps behind
    c.key(0)
    c.key(8, body_up=0.06, body_fwd=-0.05, body_pitch=14, claw_lift=30, claw_yaw=16, claw_open=1.0, tail_curl=-18,
          **legs(front=dict(up=0.2, f=0.08)))
    c.key(18, body_up=-0.3, body_fwd=-0.03, body_pitch=-3, claw_lift=-14, claw_yaw=22, claw_open=0.6, tail_curl=-46,
          legs_spread=0.28, **legs(front=dict(up=0.0, f=0.14)))
    c.key(24, body_up=-0.34, body_pitch=-5, claw_lift=-20, claw_yaw=26, claw_open=0.5, tail_curl=-56,
          legs_spread=0.4, legs_curl=0.2, **legs(front=dict(f=0.16)))
    c.key(45, body_up=-0.35, body_pitch=-6, claw_lift=-22, claw_yaw=28, claw_open=0.4, tail_curl=-58,
          legs_spread=0.42, legs_curl=0.35, **legs(front=dict(f=0.16)))
    C.append(c)
    # ---- alert: rear up, chelae wide and open, tail raised high and quivering
    c = Clip("alert", 30)
    c.key(0).key(9, body_up=0.06, body_pitch=8, claw_lift=36, claw_yaw=24, claw_wrist=18, claw_open=1.0,
                 tail_curl=-10, tail_6=10, **legs(front=dict(f=-0.04)))
    c.key(20, body_up=0.05, body_pitch=7, claw_lift=32, claw_yaw=20, claw_wrist=14, claw_open=0.7, tail_curl=-8,
          tail_6=8, **legs(front=dict(f=-0.04)))
    c.key(30, body_up=0.0, body_pitch=0, claw_lift=6, claw_yaw=4, claw_wrist=2, claw_open=0.1, tail_curl=0, tail_6=0,
          **legs(front=dict(f=0.0)))
    c.layer(lambda f, cl: {"tail.sway": 6.0 * cyc(f, 6, 1) * (1 if 8 < f < 22 else 0),
                           "claw.open": 0.3 * max(0.0, cyc(f, 8, 1)) * (1 if 8 < f < 22 else 0)})
    C.append(c)
    # ---- attacks
    # scorp_pinch: both chelae open wide, lunge, snap shut (hit 0.4-0.5 s)
    c = Clip("scorp_pinch", 27, hits=[[12 / FPS, 15 / FPS]])
    c.key(0).key(8, body_fwd=-0.08, body_up=0.04, body_pitch=5, claw_lift=24, claw_yaw=26, claw_fold=-8,
                 claw_wrist=12, claw_open=1.0, tail_curl=-6, **legs(front=dict(f=-0.03)))
    c.key(12, body_fwd=0.24, body_up=-0.02, body_pitch=-4, claw_lift=6, claw_yaw=-10, claw_fold=8, claw_wrist=-4,
          claw_open=0.9, tail_curl=6, legs_follow=0.25, **legs(front=dict(f=0.12), mid=dict(f=0.06)))
    c.key(14, body_fwd=0.26, body_up=-0.03, body_pitch=-5, claw_lift=4, claw_yaw=-14, claw_fold=10, claw_wrist=-6,
          claw_open=-0.05, tail_curl=8, legs_follow=0.25, **legs(front=dict(f=0.12), mid=dict(f=0.06)))
    c.key(27, body_fwd=0, body_up=0, body_pitch=0, claw_lift=0, claw_yaw=0, claw_fold=0, claw_wrist=0, claw_open=0,
          tail_curl=0, legs_follow=0, **legs(front=dict(f=0.0), mid=dict(f=0.0)))
    C.append(c)
    # scorp_sting: tail draws back high, then strikes forward over the head down in front (hit 0.53-0.67 s)
    c = Clip("scorp_sting", 33, hits=[[16 / FPS, 20 / FPS]])
    c.key(0).key(11, body_fwd=-0.06, body_up=0.05, body_pitch=6, tail_curl=-18, tail_5=-10, tail_6=-12,
                 claw_lift=14, claw_yaw=18, claw_open=0.4, **legs(front=dict(f=-0.03)))
    # strike pose (solved with scratch/m2/tools/scorp_tail_probe.py): the tail arches over the prosoma, the sting
    # lands ~1.0 m in front of the body centre at ~0.6 m height
    strike = dict(tail_curl=0, tail_1=88, tail_2=10, tail_3=10, tail_4=-30, tail_5=-30, tail_6=-20, sting=-20)
    c.key(16, body_fwd=0.2, body_up=-0.02, body_pitch=-6, claw_lift=10, claw_yaw=24, legs_follow=0.2,
          **legs(front=dict(f=0.08)), **strike)
    strike2 = dict(strike, tail_1=92, tail_6=-16, sting=-14)
    c.key(20, body_fwd=0.22, body_up=-0.03, body_pitch=-7, claw_lift=8, claw_yaw=24, legs_follow=0.2,
          **legs(front=dict(f=0.08)), **strike2)
    c.key(33, body_fwd=0, body_up=0, body_pitch=0, tail_curl=0, tail_1=0, tail_2=0, tail_3=0, tail_4=0, tail_5=0,
          tail_6=0, sting=0, claw_lift=0, claw_yaw=0, claw_open=0, legs_follow=0, **legs(front=dict(f=0.0)))
    c.layer(lambda f, cl: {"tail.sway": 2.5 * math.sin(2 * math.pi * (f - 20) / 5) * pulse(f, 20, 30)})
    C.append(c)
    # scorp_spray: tail arches forward over the head and sweeps left -> right spraying (hit 0.47-0.93 s)
    c = Clip("scorp_spray", 42, hits=[[14 / FPS, 28 / FPS]])
    fwd = dict(body_up=0.03, body_pitch=4, tail_1=30, tail_2=30, tail_3=30, tail_4=-30, tail_5=-30, tail_6=-20,
               sting=-20, claw_lift=12, claw_yaw=20)
    c.key(0).key(10, tail_yaw=-34, body_yaw=-6, **fwd)
    c.key(14, tail_yaw=-30, body_yaw=-5, **fwd)
    c.key(28, tail_yaw=30, body_yaw=5, **fwd)
    c.key(32, tail_yaw=32, body_yaw=6, **fwd)
    c.key(42, tail_yaw=0, body_yaw=0, body_up=0, body_pitch=0, tail_1=0, tail_2=0, tail_3=0, tail_4=0, tail_5=0,
          tail_6=0, sting=0, claw_lift=0, claw_yaw=0)
    c.layer(lambda f, cl: {"tail.6": 3.0 * math.sin(2 * math.pi * f / 4) * pulse(f, 13, 29)})
    C.append(c)
    return C


# ------------------------------------------------------------------------------------------------ mesh
def build_mesh():
    import bh_mesh as M
    import kit_a_common as A
    parts = []
    pending = []
    rng = np.random.default_rng(23)

    def add(p, **kw):
        pending.append((p, kw))
        return p

    def P(V, F, mat, name="part"):
        return M.Part(np.asarray(V, float), F, mat, name=name)

    def ring(y, zc, rx, rt, rb, n=22, p=0.8):
        a = np.linspace(0, 2 * math.pi, n, endpoint=False)
        return np.array([(rx * np.sign(math.cos(t)) * abs(math.cos(t)) ** p, y,
                          zc + (rt if math.sin(t) > 0 else rb) * math.sin(t)) for t in a])

    def wire_line(pts, r=0.008, groove=True):
        """White wire under the glass: a glowing strand with a dark seat below it."""
        out = [A.tube(pts, r, "BH_Emissive", n=4)]
        if groove:
            out.append(A.tube(np.asarray(pts) - np.array([0, 0, r * 0.8]), r * 1.6, "BH_Leather", n=4))
        return out

    # ---- prosoma (head shield): flat, rounded front with a notch
    PRO = [(-0.66, BZ + 0.02, 0.1, 0.03, 0.03), (-0.62, BZ + 0.04, 0.2, 0.07, 0.05), (-0.5, BZ + 0.05, 0.27, 0.1, 0.07),
           (-0.32, BZ + 0.06, 0.31, 0.12, 0.08), (-0.14, BZ + 0.06, 0.32, 0.12, 0.08), (-0.06, BZ + 0.05, 0.3, 0.1, 0.07)]
    V, F = M.loft([ring(*r) for r in PRO], cap0=True, cap1=True)
    add(M.recalc_normals(P(V, F, "BH_Horn", "prosoma")), bone="body")
    # median eyes on a tubercle + lateral eye dots
    add(A.ball((0, -0.46, BZ + 0.16), 0.05, "BH_Horn", n=8, rings=5, scale=(1.2, 1.0, 0.6)), bone="body")
    for sx in (1, -1):
        add(A.ball((sx * 0.022, -0.48, BZ + 0.18), 0.017, "BH_Emissive", n=6, rings=4), bone="body")
        for k in range(3):
            add(A.ball((sx * (0.22 + 0.015 * k), -0.6 + 0.02 * k, BZ + 0.08), 0.008, "BH_Emissive", n=5, rings=3),
                bone="body")
    # wire pattern under the prosoma glass
    for sx in (1, -1):
        pts = [(sx * 0.03, -0.42, BZ + 0.17), (sx * 0.12, -0.36, BZ + 0.175), (sx * 0.2, -0.24, BZ + 0.17),
               (sx * 0.22, -0.1, BZ + 0.16)]
        for prt in wire_line(pts, 0.008):
            add(prt, bone="body")
        pts = [(sx * 0.12, -0.36, BZ + 0.175), (sx * 0.12, -0.18, BZ + 0.18), (sx * 0.05, -0.1, BZ + 0.18)]
        for prt in wire_line(pts, 0.007):
            add(prt, bone="body")
    # mouth + chelicerae
    add(A.ball((0, -0.66, BZ - 0.02), 0.06, "BH_Shadow", n=8, rings=4, scale=(1.2, 0.6, 0.6)), bone="body")
    for sx in (1, -1):
        add(A.tube([(sx * 0.04, -0.62, BZ), (sx * 0.035, -0.72, BZ - 0.01), (sx * 0.015, -0.76, BZ - 0.03)],
                   [0.025, 0.018, 0.006], "BH_Horn", n=6), bone="body")
        add(A.taper([(sx * 0.02, -0.75, BZ - 0.02), (sx * 0.005, -0.79, BZ - 0.05)], 0.01, 0.002, "BH_DarkSteel",
                    n=4), bone="body")
    # ---- mesosoma: seven overlapping tergites (glass plates) over a dark body
    V, F = M.loft([ring(y, BZ + 0.03, rx * 0.92, rt * 0.8, rb, n=18) for y, rx, rt, rb in
                   ((-0.1, 0.27, 0.1, 0.1), (0.1, 0.31, 0.12, 0.12), (0.35, 0.29, 0.12, 0.11), (0.6, 0.18, 0.09, 0.08),
                    (0.66, 0.1, 0.06, 0.05))], cap0=True, cap1=True)
    add(M.recalc_normals(P(V, F, "BH_Flesh", "abdomen")), bone="body")
    ys = np.linspace(-0.08, 0.56, 7)
    for i, y in enumerate(ys):
        w = 0.33 - 0.12 * ((y - 0.15) / 0.45) ** 2
        rows = [(y - 0.06, w * 0.96, 0.12, 0.02), (y, w, 0.145, 0.03), (y + 0.06, w * 0.95, 0.13, 0.02)]
        V, F = M.loft([ring(yy, BZ + 0.04, rx, rt, rb, n=20, p=0.6) for yy, rx, rt, rb in rows], cap0=True, cap1=True)
        add(M.bevel(M.recalc_normals(P(V, F, "BH_Horn", "tergite")), 0.006, 1), bone="body")
        # glowing wire across each plate (zig-zag) + a rim of lighter glass on the trailing edge
        pts = [(x, y + 0.01 * (1 if j % 2 else -1), BZ + 0.04 + 0.14 * math.sqrt(max(1 - (x / w) ** 2, 0)) + 0.004)
               for j, x in enumerate(np.linspace(-w * 0.8, w * 0.8, 7))]
        for prt in wire_line(pts, 0.011, groove=False):
            add(prt, bone="body")
        rim = [(x, y + 0.058, BZ + 0.04 + 0.13 * math.sqrt(max(1 - (x / (w * 0.95)) ** 2, 0)) + 0.002)
               for x in np.linspace(-w * 0.9, w * 0.9, 9)]
        add(A.tube(rim, 0.009, "BH_Stone", n=4), bone="body")
        # keel shards along the spine
        q = np.array([0.0, y, BZ + 0.04 + 0.145])
        add(A.shard(q - np.array([0, 0, 0.02]), (0, 0.25, 1.0), 0.07 + 0.02 * (i % 2), 0.024, "BH_Stone", sides=4,
                    up=(0, 1, 0)), bone="body")
        for sx in (1, -1):
            if i % 2 == 0:
                qq = np.array([sx * w * 0.55, y, BZ + 0.04 + 0.12])
                add(A.shard(qq - np.array([0, 0, 0.015]), (sx * 0.5, 0.2, 1.0), 0.05, 0.016, "BH_Stone", sides=4,
                            up=(0, 1, 0)), bone="body")
    # underside sternites
    for y in np.linspace(-0.05, 0.5, 5):
        V, F = M.box(0.32, 0.1, 0.02, center=(0, y, BZ - 0.08))
        add(M.bevel(P(V, F, "BH_Flesh", "sternite"), 0.008, 1), bone="body")
    # ---- chelae
    for s, sx in (("L", 1), ("R", -1)):
        b1, b2, b3, b4 = (f"claw.{i}.{s}" for i in (1, 2, 3, 4))
        k = CK
        V, F = M.tube([H[b1] + (H[b1] - T[b1]) * 0.1, (H[b1] + T[b1]) / 2, T[b1]],
                      [(0.05 * k, 0.055 * k), (0.056 * k, 0.06 * k), (0.05 * k, 0.054 * k)], n=8, up=(0, 0, 1))
        add(P(V, F, "BH_Horn", "merus"), chain=[b1, b2], blend=0.3)
        V, F = M.tube([H[b2], (H[b2] + T[b2]) / 2, T[b2]], [(0.054 * k, 0.058 * k), (0.064 * k, 0.066 * k),
                      (0.058 * k, 0.06 * k)], n=8, up=(0, 0, 1))
        add(P(V, F, "BH_Horn", "carpus"), chain=[b2, b3], blend=0.3)
        for bb, nb in ((b1, b2), (b2, b3)):
            add(A.ball(T[bb], 0.062 * k, "BH_Leather", n=8, rings=5), chain=[bb, nb], blend=0.5)
            add(K_coil(T[bb] - RIG.rdir(bb) * 0.05, T[bb] - RIG.rdir(bb) * 0.005, 0.06 * k), chain=[bb, nb],
                blend=0.5)
        for bb in (b1, b2):
            d = RIG.rdir(bb)
            up = np.cross(K.unit(np.cross(d, (0, 0, 1))), d)
            for prt in wire_line([H[bb] + d * 0.05 + up * 0.056 * k, T[bb] - d * 0.05 + up * 0.058 * k], 0.006,
                                 groove=False):
                add(prt, bone=bb)
        # palm: a swollen glass lozenge + fixed finger
        d3 = RIG.rdir(b3)
        side = K.unit(np.cross(d3, (0, 0, 1)))
        up3 = np.cross(side, d3)
        rings = []
        for u, rr, rz in ((-0.02, 0.055, 0.05), (0.04, 0.095, 0.068), (0.11, 0.11, 0.075), (0.18, 0.1, 0.068),
                          (0.23, 0.065, 0.048)):
            p0 = H[b3] + d3 * u * k
            rings.append(np.array([p0 + side * rr * k * math.cos(t) + up3 * rz * k * math.sin(t)
                                   for t in np.linspace(0, 2 * math.pi, 14, endpoint=False)]))
        V, F = M.loft(rings, cap0=True, cap1=True)
        add(M.recalc_normals(P(V, F, "BH_Horn", "palm")), bone=b3)
        c = H[b3] + d3 * 0.1 * k
        for prt in wire_line([c - d3 * 0.08 * k + up3 * 0.065 * k + side * 0.03 * k,
                              c + up3 * 0.078 * k, c + d3 * 0.08 * k + up3 * 0.062 * k - side * 0.03 * k], 0.011,
                             groove=False):
            add(prt, bone=b3)
        outv = np.array([float(sx), 0.0, 0.0])          # outward (the dactyl's side)
        for prt in wire_line([c - d3 * 0.06 * k + outv * 0.115 * k, c + d3 * 0.06 * k + outv * 0.11 * k],
                             0.007, groove=False):
            add(prt, bone=b3)
        base = H[b3] + d3 * 0.22 * k - outv * 0.03 * k
        fx = [base, base + d3 * 0.15 * k - outv * 0.005 * k, base + d3 * 0.3 * k + outv * 0.025 * k]
        V, F = M.tube(fx, [(0.038 * k, 0.032 * k), (0.026 * k, 0.024 * k), (0.004, 0.004)], n=6, up=(0, 0, 1))
        add(P(V, F, "BH_Horn", "finger"), bone=b3)
        V, F = M.tube([fx[1] + d3 * 0.07 * k, fx[2] + d3 * 0.012], [(0.016 * k, 0.016 * k), (0.002, 0.002)], n=5,
                      up=(0, 0, 1))
        add(P(V, F, "BH_DarkSteel", "fingertip"), bone=b3)
        for i in range(5):        # glass teeth on the inner edge of the fixed finger
            q = base + d3 * (0.03 + 0.055 * i) * k + outv * 0.02 * k
            add(A.shard(q, outv + d3 * 0.3, 0.025 * k, 0.007 * k, "BH_Stone", sides=4, up=tuple(up3)),
                bone=b3)
        # movable finger (dactyl), on the outer side
        d4 = RIG.rdir(b4)
        dd = [H[b4], H[b4] + d4 * 0.2 * k - outv * 0.014 * k, T[b4]]
        V, F = M.tube(dd, [(0.032 * k, 0.03 * k), (0.022 * k, 0.02 * k), (0.004, 0.004)], n=6, up=(0, 0, 1))
        add(P(V, F, "BH_Horn", "dactyl"), bone=b4)
        V, F = M.tube([dd[1] + d4 * 0.05 * k, T[b4] + d4 * 0.01], [(0.015 * k, 0.015 * k), (0.002, 0.002)], n=5,
                      up=(0, 0, 1))
        add(P(V, F, "BH_DarkSteel", "dactyltip"), bone=b4)
        for i in range(4):
            q = H[b4] + d4 * (0.06 + 0.07 * i) * k - outv * 0.018 * k
            add(A.shard(q, -outv + d4 * 0.3, 0.022 * k, 0.006 * k, "BH_Stone", sides=4, up=tuple(up3)),
                bone=b4)
        # glass shards on the palm's back
        for i in range(3):
            q = c + up3 * 0.09 * k + d3 * (i - 1) * 0.06 * k
            add(A.shard(q, up3 + outv * 0.3, 0.05, 0.016, "BH_Stone", sides=4, up=tuple(d3)), bone=b3)
    # ---- walking legs: faceted glass tubes, wire down each segment, copper at the knees
    for kk, (cx, fe, ti, ta) in LEGS.items():
        pts, prof = [], []
        segs = [(cx, 2, 0.05, 0.048), (fe, 5, 0.046, 0.04), (ti, 5, 0.038, 0.028), (ta, 4, 0.024, 0.006)]
        pts.append(H[cx] - RIG.rdir(cx) * 0.02)
        prof.append((0.04, 0.045))
        for b, nseg, r0, r1 in segs:
            for i in range(1, nseg + 1):
                t = i / nseg
                pts.append(H[b] * (1 - t) + T[b] * t)
                r = r0 * (1 - t) + r1 * t
                prof.append((r * 0.85, r * 1.15))
        prof[-1] = (0.003, 0.003)
        V, F = M.tube(pts, prof, n=6, up=(0, 0, 1))
        add(P(V, F, "BH_Horn", "leg"), chain=[cx, fe, ti, ta], blend=0.28)
        for b, nb, r in ((fe, ti, 0.05), (ti, ta, 0.04)):
            add(A.ball(T[b], r, "BH_Leather", n=7, rings=4), chain=[b, nb], blend=0.5)
            add(K_coil(T[b] - RIG.rdir(b) * 0.045, T[b] - RIG.rdir(b) * 0.005, r * 0.95, wire=0.0045, turns=3),
                bone=b)
        for b, r in ((fe, 0.044), (ti, 0.034)):
            d = RIG.rdir(b)
            up = np.cross(K.unit(np.cross(d, [0, 0, 1.0])), d)
            for prt in wire_line([H[b] + d * 0.04 + up * r, T[b] - d * 0.06 + up * r * 0.85], 0.005, groove=False):
                add(prt, bone=b)
        d = RIG.rdir(ta)
        V, F = M.tube([T[ta] - d * 0.09, T[ta] + d * 0.006], [(0.012, 0.012), (0.002, 0.002)], n=5, up=(0, 0, 1))
        add(P(V, F, "BH_DarkSteel", "legtip"), bone=ta)
    # ---- tail: barrel segments of glass with keels, glowing joints, the bulb and sting
    TR = [0.105, 0.1, 0.095, 0.09, 0.085, 0.08]
    for i, b in enumerate(TAIL[:6]):
        h, t = H[b], T[b]
        d = RIG.rdir(b)
        L = np.linalg.norm(t - h)
        side = np.array([1.0, 0.0, 0.0])
        up = np.cross(side, d)               # away from the inside of the curl (outer side of the arc)
        r = TR[i]
        rings = []
        for u, rr in ((0.02, 0.8), (0.15, 1.0), (0.6, 1.05), (0.9, 0.95), (1.02, 0.78)):
            p0 = h + (t - h) * u
            rings.append(np.array([p0 + side * rr * r * 1.05 * math.cos(a) + up * rr * r * 0.95 * math.sin(a)
                                   for a in np.linspace(0, 2 * math.pi, 14, endpoint=False)]))
        V, F = M.loft(rings, cap0=True, cap1=True)
        add(M.bevel(M.recalc_normals(P(V, F, "BH_Horn", "tailseg")), 0.006, 1), bone=b)
        # paired keels (lighter glass ridges) along the outer face + a glowing wire between them
        for sx in (1, -1):
            add(A.tube([h + d * L * 0.15 + up * r * 0.9 + side * sx * r * 0.45,
                        h + d * L * 0.85 + up * r * 0.88 + side * sx * r * 0.42], 0.012, "BH_Stone", n=4), bone=b)
        for prt in wire_line([h + d * L * 0.12 + up * r * 1.0, h + d * L * 0.88 + up * r * 0.97], 0.012,
                             groove=False):
            add(prt, bone=b)
        # glowing joint ring (the wire seen through the membrane) + copper winding
        add(A.tube([h - d * 0.005, h + d * 0.03], r * 0.82, "BH_Emissive", n=10), bone=b)
        add(K_coil(h + d * 0.035, h + d * 0.075, r * 0.98, wire=0.006, turns=2.5), bone=b)
        # a glass spur on top of each segment
        add(A.shard(h + d * L * 0.55 + up * r * 0.9, up + d * 0.4, 0.06, 0.016, "BH_Stone", sides=4,
                    up=(1, 0, 0)), bone=b)
    # telson bulb (on tail.6's tail / sting head) and the curved sting
    hs = H["sting"]
    ds = RIG.rdir("sting")
    rings = []
    for u, rr in ((-0.06, 0.07), (0.0, 0.1), (0.07, 0.11), (0.13, 0.09), (0.18, 0.05)):
        p0 = hs + ds * u
        rings.append(np.array([p0 + np.array([1.0, 0, 0]) * rr * math.cos(a) +
                               np.cross([1.0, 0, 0], ds) * rr * 0.95 * math.sin(a)
                               for a in np.linspace(0, 2 * math.pi, 14, endpoint=False)]))
    V, F = M.loft(rings, cap0=True, cap1=True)
    add(M.recalc_normals(P(V, F, "BH_Horn", "bulb")), bone="sting")
    add(A.ball(hs + ds * 0.06, 0.085, "BH_Emissive", n=10, rings=6), bone="sting")   # glow showing through
    upS = np.cross([1.0, 0, 0], ds)
    for sx in (1, -1):
        for prt in wire_line([hs + ds * -0.02 + np.array([sx * 0.1, 0, 0]), hs + ds * 0.08 + np.array([sx * 0.105, 0, 0]),
                              hs + ds * 0.15 + np.array([sx * 0.06, 0, 0])], 0.007, groove=False):
            add(prt, bone="sting")
    sting = [hs + ds * 0.16, hs + ds * 0.26 - upS * 0.02, hs + ds * 0.34 - upS * 0.07, hs + ds * 0.38 - upS * 0.14]
    add(A.tube(sting, [0.045, 0.03, 0.016, 0.002], "BH_DarkSteel", n=7), bone="sting")
    add(A.taper([sting[2], sting[3] - upS * 0.004], 0.008, 0.0015, "BH_Emissive", n=5), bone="sting")
    for p, kw in pending:
        K.bind(p, RIG, **kw)
        parts.append(p)
    return parts


def K_coil(a, b, r, wire=0.007, turns=3, mat="BH_Gold"):
    """Copper wire wound round a joint (helix from a to b)."""
    import bh_mesh as M
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = K.unit(b - a)
    s = K.unit(np.cross(d, (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)))
    f = np.cross(d, s)
    n = int(turns * 8) + 1
    pts = [a + (b - a) * (i / (n - 1)) + (s * math.cos(2 * math.pi * turns * i / (n - 1)) +
                                         f * math.sin(2 * math.pi * turns * i / (n - 1))) * r for i in range(n)]
    V, F = M.tube(np.array(pts), [(wire, wire)] * n, n=4, up=tuple(d))
    return M.Part(V, F, mat, name="coil")


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


def sting_tip(clip, f):
    X = evaluate(clip.channels(float(f)))
    return RIG.tail(X, "sting")


def merge_meta(C, tris, bones):
    """Merge ONLY animations.scorp_* and models.glasswire_scorpion; re-read right before writing, keep every other
    key, write, re-read and verify."""
    mine = {c.name: K.clip_entry(c) for c in C if c.name.startswith("scorp_")}
    model = {"generator": "tools/blender/creatures/build_glasswire_scorpion.py",
             "glb": f"res://assets/characters/{CID}.glb", "clips": {c.name: K.clip_entry(c) for c in C},
             "tris": tris, "bones": bones}
    with open(K.META) as fh:
        data = json.load(fh)
    before_a = {k: v for k, v in data.get("animations", {}).items() if not k.startswith("scorp_")}
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
        if c.name in ("scorp_sting", "scorp_spray"):
            for f in (0, int(c.meta["hits"][0][0] * FPS), int(c.meta["hits"][0][1] * FPS)):
                print(f"[{CID}] {c.name} f{f} sting tip at {np.round(sting_tip(c, f), 3)}")
    print(f"[{CID}] worst IK reach miss per clip (mm): " +
          ", ".join(f"{c.name} {reach_report(c) * 1000:.1f}" for c in C if not only or c.name in only))
    K.quick_preview(CID, arm, acts, a, 0.6, 6.0)
    if a.evidence:
        K.evidence_rest(CID, arm, 0.65, 6.2, "Glasswire Scorpion - rest (4 views + 3/4 + gameplay iso 26 m / 55 deg)",
                        iso_scales=(1.0,), base=SCRATCH)
        spec = [("idle", [0.0]), ("walk", [0, 0.25, 0.5, 0.75]), ("scorp_pinch", [0, 8 / 27, 12 / 27, 14 / 27, 1.0]),
                ("scorp_sting", [0, 11 / 33, 16 / 33, 20 / 33, 26 / 33, 1.0]),
                ("scorp_spray", [0, 10 / 42, 14 / 42, 21 / 42, 28 / 42, 1.0]), ("alert", [0.3]),
                ("hit_heavy", [0.22]), ("death", [0.3, 0.6, 1.0]), ("death_back", [0.5, 1.0])]
        K.evidence_clips(CID, arm, acts, spec, 0.7, 6.6, "Glasswire Scorpion - clips (view yaw 50)", yaw=50, cols=6,
                         base=SCRATCH)
    if not a.no_export and not only:
        bad, got = K.export(CID, arm, mesh, acts, OUT_GLB)
        assert not bad, bad
        merge_meta(C, tris, len(RIG.ORDER))


if __name__ == "__main__":
    main()
