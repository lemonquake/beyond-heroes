"""Gloam Ooze (bh-013, Builder C; dungeon splitter slime): a dark-teal blob ~1.3 m tall and ~1.6 m wide with a
violet emissive rim (inverted hull shell: its back faces draw a glowing outline around the silhouette), a lumpy
crown of bubbles, cyan glowing bubbles on its skin, two stubby pseudopods and bones pressing against its skin (a
skull at the front whose jaw opens to spit, ribs on its flank, a femur out of its back). No legs: a short spine
chain + 4 radial wobble bones squash, stretch and bulge it (bone scale + translation), 2 pseudopod chains.

  "<blender>" -b --factory-startup --python build_gloam_ooze.py -- [--no-export] [--evidence rest|clips|both]
                                                                   [--clips a,b --tag t --frames 0,0.5,1]
Export: game/assets/characters/gloam_ooze.glb (+ .import); merges ONLY animations.ooze_* and models.gloam_ooze into
creature_meta.json. Faces -Y (= +Z in Godot), origin on the ground at the centre, meters, 30 fps, clips in place.
The game spawns scaled copies (0.65 / 0.45) of the same model when it splits.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_c13 as K  # noqa: E402
from kit_c13 import Rx, Ry, Rz, cyc, damp, normalize  # noqa: E402
import numpy as np  # noqa: E402

NAME = "gloam_ooze"
PREFIX = "ooze_"
FPS = K.FPS
PALETTE = {
    "BH_Ichor": ((0.018, 0.105, 0.115), 0.0, 0.16, (0.02, 0.17, 0.2), 1.0, 1.0),      # dark teal slime body
    "BH_Flesh": ((0.07, 0.19, 0.24), 0.0, 0.14, (0.05, 0.14, 0.22), 1.0, 1.0),       # lighter crown lumps
    "BH_Aether": ((0.62, 0.36, 1.0), 0.0, 0.3, (0.6, 0.34, 1.0), 4.0, 1.0),           # violet rim shell
    "BH_Emissive": ((0.35, 0.95, 1.0), 0.0, 0.3, (0.35, 0.95, 1.0), 5.0, 1.0),        # cyan bubbles
    "BH_Bone": ((0.74, 0.69, 0.54), 0.0, 0.62, None, 0.0, 1.0),                        # bone ivory
    "BH_Shadow": ((0.02, 0.03, 0.035), 0.0, 0.6, None, 0.0, 1.0),                      # skull sockets
    "BH_Horn": ((0.19, 0.33, 0.32), 0.0, 0.3, None, 0.0, 1.0),                         # submerged bones
}

# ------------------------------------------------------------------------------------------------ skeleton
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.25), None),
    "body": ((0, 0, 0.04), (0, 0, 0.44), "root"),
    "spine1": ((0, 0, 0.44), (0, 0, 0.75), "body"),
    "spine2": ((0, 0, 0.75), (0, 0, 0.98), "spine1"),
    "crown": ((0, 0, 0.98), (0, 0, 1.22), "spine2"),
    "wobF": ((0, -0.15, 0.32), (0, -0.78, 0.26), "body"),
    "wobB": ((0, 0.15, 0.32), (0, 0.78, 0.26), "body"),
    "wobL": ((0.15, 0, 0.32), (0.78, 0, 0.26), "body"),
    "wobR": ((-0.15, 0, 0.32), (-0.78, 0, 0.26), "body"),
    "skull": ((0.09, -0.55, 0.54), (0.1, -0.75, 0.55), "spine1"),
    "jaw": ((0.09, -0.64, 0.45), (0.1, -0.78, 0.4), "skull"),
    "podL1": ((0.44, -0.5, 0.33), (0.56, -0.73, 0.3), "spine1"),
    "podL2": ((0.56, -0.73, 0.3), (0.65, -0.9, 0.27), "podL1"),
    "podR1": ((-0.44, -0.5, 0.33), (-0.56, -0.73, 0.3), "spine1"),
    "podR2": ((-0.56, -0.73, 0.3), (-0.65, -0.9, 0.27), "podR1"),
}
RIG = K.Rig(BONES)
RIM = 0.042
SKULL_A = math.radians(-82)   # angle around the body (front = -90)
SKULL_Z = 0.52
H, T = RIG.H, RIG.T
VERT = ("body", "spine1", "spine2", "crown")
WOB = ("wobF", "wobB", "wobL", "wobR")


def evaluate(c):
    """Channels: body.fwd/side/up (m), body.yaw/lean/tilt (root, about the ground centre + piv.y);
    <v>.lean (+ forward) / .tilt (+ toward its left, +X) / .yaw and <v>.st (stretch: h = 1 + st, width 1/sqrt(h)),
    <v>.w (extra width), <v>.wx / .wy (extra width along X / Y) for the vertical chain; <wob>.out (m, along the
    bone), <wob>.s (uniform bulge scale); pod.lift / podL.lift / podL.yaw / podL.curl (and R); skull.* ; jaw."""
    Rd, S, L = {}, {}, {}
    Rb = Rz(c.get("body.yaw", 0.0)) @ Rx(c.get("body.lean", 0.0)) @ Ry(c.get("body.tilt", 0.0))
    piv = np.array([0.0, c.get("piv.y", 0.0), c.get("piv.z", 0.0)])
    t = np.array([c.get("body.side", 0.0), -c.get("body.fwd", 0.0), c.get("body.up", 0.0)])
    Xr = K.Xf(np.eye(3), t) @ K.Xf.about(Rb, piv)
    Rd["root"] = Rb
    L["root"] = Xr.apply(H["root"]) - H["root"]
    for b in VERT:
        Rd[b] = Rz(c.get(b + ".yaw", 0.0)) @ Rx(c.get(b + ".lean", 0.0)) @ Ry(c.get(b + ".tilt", 0.0))
        h = max(1.0 + c.get(b + ".st", 0.0), 0.05)
        w = (1.0 / math.sqrt(h)) * (1.0 + c.get(b + ".w", 0.0))
        # vertical bone: local X = world Y, local Y = along the bone (world Z), local Z = world X
        S[b] = (w * (1 + c.get(b + ".wy", 0.0)), h, w * (1 + c.get(b + ".wx", 0.0)))
    for b in WOB:
        d = normalize(T[b] - H[b])
        L[b] = d * c.get(b + ".out", 0.0)
        s = max(1.0 + c.get(b + ".s", 0.0), 0.05)
        S[b] = (s, s, s)
        lift = c.get(b + ".lift", 0.0)      # + raises the outer end (bulges that side upward)
        Rd[b] = {"wobL": Ry(-lift), "wobR": Ry(lift), "wobF": Rx(-lift), "wobB": Rx(lift)}[b]
    for s_, sx in (("L", 1), ("R", -1)):
        lift = c.get("pod.lift", 0.0) + c.get(f"pod{s_}.lift", 0.0)
        yaw = (c.get("pod.yaw", 0.0) + c.get(f"pod{s_}.yaw", 0.0)) * sx
        curl = c.get("pod.curl", 0.0) + c.get(f"pod{s_}.curl", 0.0)
        Rd[f"pod{s_}1"] = Rz(yaw) @ R_about_side(sx, lift)
        Rd[f"pod{s_}2"] = R_about_side(sx, curl)
        S[f"pod{s_}1"] = (1.0, 1.0 + c.get("pod.st", 0.0), 1.0)
    Rd["skull"] = Rz(c.get("skull.yaw", 0.0)) @ Rx(-c.get("skull.pitch", 0.0)) @ Ry(c.get("skull.roll", 0.0))
    Rd["jaw"] = Rx(-c.get("jaw", 0.0))
    X = RIG.fk(Rd, S, L)
    return Rd, S, L, X


def R_about_side(sx, lift):
    """Raise a forward-out pseudopod by `lift` degrees (rotation about its horizontal side axis)."""
    ax = normalize(np.cross((sx * 0.55, -0.83, 0.0), (0, 0, 1)))
    return K.R_axis(ax, lift)


# ------------------------------------------------------------------------------------------------ clips
def jiggle(f0, amp, freq=3.2, decay=5.0):
    """Damped squash / wobble layer after an impact at frame f0."""
    def fn(f, cl):
        j = damp(f, f0, freq, decay, amp)
        j2 = damp(f, f0 + 2, freq * 1.3, decay, amp)
        return {"body.st": -0.5 * j, "spine1.st": 0.6 * j2, "spine2.st": -0.5 * j, "crown.st": 0.8 * j2,
                "wobL.s": 0.5 * j, "wobR.s": 0.5 * j, "wobF.s": -0.4 * j2, "wobB.s": -0.4 * j2,
                "spine2.tilt": 25 * j2, "crown.lean": -20 * j}
    return fn


def clips():
    C = []
    # ---- idle: slow breathing squash / stretch, rippling sides, pods sway (2.0 s)
    P = 60
    c = K.Clip("idle", P, loop=True)
    c.key(0)
    c.layer(lambda f, cl: {"body.st": 0.035 * cyc(f, P), "spine1.st": 0.03 * cyc(f, P, 1, 0.15),
                           "spine2.st": 0.045 * cyc(f, P, 1, 0.3), "crown.st": 0.06 * cyc(f, P, 1, 0.45),
                           "crown.tilt": 4 * cyc(f, P, 1, 0.1), "spine2.lean": 2 * cyc(f, P, 1, 0.6),
                           "wobL.s": 0.05 * cyc(f, P, 1, 0.25), "wobR.s": 0.05 * cyc(f, P, 1, 0.75),
                           "wobF.s": 0.04 * cyc(f, P, 2, 0.1), "wobB.s": 0.04 * cyc(f, P, 2, 0.6),
                           "podL.lift": 8 * cyc(f, P, 1, 0.2), "podR.lift": 8 * cyc(f, P, 1, 0.7),
                           "pod.curl": -6 + 6 * cyc(f, P, 1, 0.4), "jaw": 4 + 4 * cyc(f, P, 1, 0.3),
                           "skull.roll": 3 * cyc(f, P, 1)})
    C.append(c)
    # ---- idle_look: the upper body leans / turns left, then right, pods lift (2.5 s)
    c = K.Clip("idle_look", 75)
    c.key(0).key(16, spine1_tilt=8, spine2_tilt=10, crown_tilt=8, spine1_yaw=18, spine2_yaw=10, podL_lift=20,
                  body_st=0.06, wobR_s=0.08)
    c.key(30, spine1_tilt=9, spine2_tilt=11, crown_tilt=10, spine1_yaw=20, spine2_yaw=12, podL_lift=24, body_st=0.05,
          wobR_s=0.08, jaw=10)
    c.key(46, spine1_tilt=-8, spine2_tilt=-10, crown_tilt=-8, spine1_yaw=-18, spine2_yaw=-12, podR_lift=22,
          body_st=0.06, wobL_s=0.08, podL_lift=0, wobR_s=0, jaw=0)
    c.key(60, spine1_tilt=-6, spine2_tilt=-8, crown_tilt=-6, spine1_yaw=-14, spine2_yaw=-10, podR_lift=16,
          body_st=0.04, wobL_s=0.06)
    c.key(75, spine1_tilt=0, spine2_tilt=0, crown_tilt=0, spine1_yaw=0, spine2_yaw=0, podR_lift=0, podL_lift=0,
          body_st=0, wobL_s=0, wobR_s=0, jaw=0)
    c.layer(lambda f, cl: {"crown.st": 0.04 * cyc(f, 75, 2)})
    C.append(c)
    # ---- walk / run / run_combat: squash-and-slide wobble (squash, then surge forward stretching the front)
    for nm, per, v, amp in (("walk", 40, 1.0, 1.0), ("run", 24, 2.8, 1.5), ("run_combat", 24, 2.8, 1.5)):
        c = K.Clip(nm, per, loop=True, ground_speed=v)
        c.key(0)
        low = 1.0 if nm == "run_combat" else 0.0

        def lay(f, cl, per=per, amp=amp, low=low):
            s = cyc(f, per)              # +: surging forward / stretched, -: gathering / squashed
            s2 = cyc(f, per, 1, 0.12)
            return {"body.st": 0.07 * amp * s - 0.04 * low, "body.lean": 5 * amp * s2 + 3 * amp + 3 * low,
                    "spine1.lean": 4 * amp * cyc(f, per, 1, 0.2) + 2 * amp, "spine1.st": 0.05 * amp * s2,
                    "spine2.lean": 5 * amp * cyc(f, per, 1, 0.3) + 2, "spine2.st": -0.05 * amp * s,
                    "crown.lean": 8 * amp * cyc(f, per, 1, 0.4) - 4 * low, "crown.st": 0.08 * amp * cyc(f, per, 1, 0.45),
                    "wobF.s": 0.14 * amp * s, "wobF.out": 0.05 * amp * s + 0.03 * amp,
                    "wobB.s": -0.08 * amp * s, "wobB.out": -0.05 * amp * cyc(f, per, 1, 0.1),
                    "wobL.s": 0.06 * amp * cyc(f, per, 1, 0.5), "wobR.s": 0.06 * amp * cyc(f, per, 1, 0.5),
                    "body.tilt": 2.5 * amp * cyc(f, per, 0.5 if False else 1, 0.25) * 0.0 + 2 * cyc(f, per, 1, 0.7),
                    "pod.lift": 10 * amp * cyc(f, per, 1, 0.35) + 6 * amp + 10 * low, "pod.curl": -8 * amp * s2,
                    "jaw": 5 + 6 * low, "skull.pitch": -2 * amp * s}
        c.layer(lay)
        C.append(c)
    # ---- reactions
    c = K.Clip("hit_light", 12)
    c.key(0).key(3, spine1_lean=-9, spine2_lean=-8, crown_lean=-6, body_st=-0.06, wobB_s=0.08, jaw=10)
    c.key(12, spine1_lean=0, spine2_lean=0, crown_lean=0, body_st=0, wobB_s=0, jaw=0)
    c.layer(jiggle(3, 0.06, freq=4.0, decay=9.0))
    C.append(c)
    c = K.Clip("hit_heavy", 20)
    c.key(0).key(4, body_fwd=-0.1, spine1_lean=-16, spine2_lean=-14, crown_lean=-12, body_st=-0.14, wobB_s=0.16,
                 wobF_s=-0.1, jaw=18, pod_lift=25, skull_pitch=12)
    c.key(9, body_fwd=-0.12, spine1_lean=-8, spine2_lean=-4, crown_lean=4, body_st=-0.04, wobB_s=0.06, jaw=8,
          pod_lift=10, skull_pitch=4)
    c.key(20, body_fwd=0, spine1_lean=0, spine2_lean=0, crown_lean=0, body_st=0, wobB_s=0, wobF_s=0, jaw=0, pod_lift=0,
          skull_pitch=0)
    c.layer(jiggle(4, 0.1, freq=3.5, decay=6.5))
    C.append(c)
    c = K.Clip("stagger_small", 24)
    c.key(0).key(5, body_fwd=-0.08, body_side=-0.06, spine1_tilt=-12, spine2_tilt=-10, crown_tilt=-8, body_st=-0.1,
                 wobR_s=0.15, wobL_s=-0.06, podR_lift=25, jaw=12)
    c.key(11, body_fwd=-0.12, body_side=-0.08, spine1_tilt=7, spine2_tilt=8, crown_tilt=10, body_st=0.02, wobR_s=0.02,
          wobL_s=0.06, podR_lift=5, podL_lift=15, jaw=6)
    c.key(24, body_fwd=0, body_side=0, spine1_tilt=0, spine2_tilt=0, crown_tilt=0, body_st=0, wobR_s=0, wobL_s=0,
          podR_lift=0, podL_lift=0, jaw=0)
    c.layer(jiggle(5, 0.07, freq=3.0, decay=5.5))
    C.append(c)
    c = K.Clip("knockback", 27)
    c.key(0).key(4, body_fwd=-0.25, body_up=0.04, spine1_lean=-20, spine2_lean=-16, crown_lean=-14, body_st=0.12,
                 wobF_s=-0.15, wobB_s=0.1, pod_lift=40, jaw=22, skull_pitch=15)
    c.key(9, body_fwd=-0.42, body_up=0.0, spine1_lean=-6, spine2_lean=4, crown_lean=10, body_st=-0.22, wobF_s=0.1,
          wobB_s=0.22, wobL_s=0.15, wobR_s=0.15, pod_lift=-5, jaw=10, skull_pitch=4)
    c.key(17, body_fwd=-0.3, spine1_lean=3, spine2_lean=4, crown_lean=2, body_st=0.04, wobF_s=0.02, wobB_s=0.04,
          wobL_s=0.02, wobR_s=0.02, pod_lift=5, jaw=4, skull_pitch=0)
    c.key(27, body_fwd=0, spine1_lean=0, spine2_lean=0, crown_lean=0, body_st=0, wobF_s=0, wobB_s=0, wobL_s=0,
          wobR_s=0, pod_lift=0, jaw=0)
    c.layer(jiggle(9, 0.07, freq=3.5, decay=6.0))
    C.append(c)
    # ---- deaths: collapse into a glowing puddle (death: slumps forward, death_back: topples back first)
    for nm, lean in (("death", 1), ("death_back", -1)):
        c = K.Clip(nm, 45)
        c.key(0)
        c.key(7, spine1_lean=-10 * lean, spine2_lean=-8 * lean, body_st=0.12, crown_st=0.15, pod_lift=35, jaw=25,
              skull_pitch=10 * lean)
        c.key(16, spine1_lean=18 * lean, spine2_lean=14 * lean, crown_lean=10 * lean, body_st=-0.3, body_w=-0.05,
              spine1_st=-0.2, spine1_w=-0.06, spine2_st=-0.15, crown_st=-0.2, wobF_s=0.06, wobB_s=0.06, wobL_s=0.06,
              wobR_s=0.06,
              pod_lift=-10, pod_curl=-20, jaw=30, skull_pitch=-15 * lean, skull_roll=15)
        c.key(28, spine1_lean=10 * lean, spine2_lean=8 * lean, crown_lean=6 * lean, body_st=-0.5, body_w=-0.12,
              spine1_st=-0.3, spine1_w=-0.14, spine2_st=-0.35, spine2_w=-0.18, crown_st=-0.45, crown_w=-0.2,
              wobF_s=0.08, wobB_s=0.08, wobL_s=0.08, wobR_s=0.08,
              wobF_out=0.08 * (1 if lean > 0 else 0.4), wobB_out=0.08 * (1 if lean < 0 else 0.4), wobL_out=0.06,
              wobR_out=0.06, pod_lift=-25, pod_curl=-10, pod_yaw=20, jaw=34, skull_pitch=-30 * lean, skull_roll=30)
        c.key(45, spine1_lean=8 * lean, spine2_lean=6 * lean, crown_lean=4 * lean, body_st=-0.58, body_w=-0.14,
              spine1_st=-0.35, spine1_w=-0.18, spine2_st=-0.4, spine2_w=-0.22, crown_st=-0.5, crown_w=-0.24,
              wobF_s=0.1, wobB_s=0.1, wobL_s=0.1, wobR_s=0.1,
              wobF_out=0.1 * (1 if lean > 0 else 0.4), wobB_out=0.1 * (1 if lean < 0 else 0.4), wobL_out=0.08,
              wobR_out=0.08, pod_lift=-28, pod_curl=-8, pod_yaw=25, jaw=36, skull_pitch=-35 * lean, skull_roll=35)
        C.append(c)
    # ---- alert: stretches up tall and leans at the target, pods raised, then settles tense
    c = K.Clip("alert", 30)
    c.key(0).key(8, body_st=0.14, spine1_st=0.12, spine2_st=0.1, crown_st=0.15, spine1_lean=-6, pod_lift=40, jaw=20,
                  wobF_s=-0.06, wobB_s=-0.06, wobL_s=-0.06, wobR_s=-0.06)
    c.key(14, body_st=0.1, spine1_st=0.08, spine2_st=0.06, spine1_lean=8, spine2_lean=8, crown_lean=6, pod_lift=30,
          jaw=26, skull_pitch=-8)
    c.key(30, body_st=0.0, spine1_st=0, spine2_st=0, crown_st=0, spine1_lean=3, spine2_lean=3, crown_lean=2,
          pod_lift=10, jaw=6, skull_pitch=0, wobF_s=0, wobB_s=0, wobL_s=0, wobR_s=0)
    c.layer(jiggle(14, 0.05, freq=3.0, decay=5.0))
    C.append(c)
    # ---- ooze_slam (1.07 s): rears up tall and back, pods high, then slams down forward, blow lands ~0.55 s
    c = K.Clip("ooze_slam", 32, hits=[[15 / FPS, 19 / FPS]])
    c.key(0).key(10, body_st=0.2, spine1_st=0.12, spine2_st=0.08, crown_st=0.04, crown_w=0.12, body_lean=-4, spine1_lean=-12,
                  spine2_lean=-12, crown_lean=-8, pod_lift=65, pod_curl=-20, jaw=28, wobF_s=-0.12, wobB_s=-0.05,
                  wobL_s=-0.12, wobR_s=-0.12)
    c.key(13, body_st=0.23, spine1_st=0.14, spine2_st=0.1, crown_st=0.05, crown_w=0.14, body_lean=-5, spine1_lean=-15,
          spine2_lean=-14, crown_lean=-10, pod_lift=72, pod_curl=-25, jaw=32, wobF_s=-0.14, wobL_s=-0.14, wobR_s=-0.14)
    c.key(16, body_st=-0.3, spine1_st=-0.1, spine2_st=0.0, crown_st=-0.1, crown_w=0.0, body_lean=12, spine1_lean=22,
          spine2_lean=20, crown_lean=14, body_fwd=0.12, pod_lift=-22, pod_curl=15, jaw=10, wobF_s=0.3, wobF_out=0.12,
          wobB_s=-0.05, wobL_s=0.15, wobR_s=0.15, skull_pitch=-10)
    c.key(19, body_st=-0.36, spine1_st=-0.14, spine2_st=-0.05, crown_st=-0.16, body_lean=10, spine1_lean=18,
          spine2_lean=16, crown_lean=10, body_fwd=0.14, pod_lift=-24, pod_curl=10, jaw=8, wobF_s=0.34, wobF_out=0.14,
          wobL_s=0.2, wobR_s=0.2, skull_pitch=-12)
    c.key(32, body_st=0, spine1_st=0, spine2_st=0, crown_st=0, body_lean=0, spine1_lean=0, spine2_lean=0, crown_lean=0,
          body_fwd=0, pod_lift=0, pod_curl=0, jaw=0, wobF_s=0, wobF_out=0, wobB_s=0, wobL_s=0, wobR_s=0,
          skull_pitch=0)
    c.layer(jiggle(19, 0.08, freq=3.4, decay=6.0))
    C.append(c)
    # ---- ooze_spit (0.9 s): contracts, then lurches forward and spits through the skull's jaw, release ~0.45 s
    c = K.Clip("ooze_spit", 27, hits=[[13 / FPS, 15 / FPS]])
    c.key(0).key(9, body_st=-0.14, spine1_st=-0.12, spine2_st=-0.2, crown_st=-0.2, spine1_lean=-10, spine2_lean=-12,
                  crown_lean=-8, body_w=-0.04, wobF_s=-0.1, wobL_s=0.06, wobR_s=0.06, pod_lift=20, pod_curl=-25,
                  jaw=4, skull_pitch=10)
    c.key(13, body_st=0.05, spine1_st=0.08, spine2_st=0.12, crown_st=0.04, body_lean=6, spine1_lean=16, spine2_lean=14,
          crown_lean=10, body_w=0.0, wobF_s=0.2, wobF_out=0.08, wobL_s=0.0, wobR_s=0.0, pod_lift=-5, pod_curl=5,
          jaw=48, skull_pitch=-14)
    c.key(16, body_st=0.04, spine1_st=0.08, spine2_st=0.14, crown_st=0.05, body_lean=5, spine1_lean=12,
          spine2_lean=10, crown_lean=6, wobF_s=0.14, wobF_out=0.06, jaw=40, skull_pitch=-10)
    c.key(27, body_st=0, spine1_st=0, spine2_st=0, crown_st=0, body_lean=0, spine1_lean=0, spine2_lean=0, crown_lean=0,
          wobF_s=0, wobF_out=0, pod_lift=0, pod_curl=0, jaw=0, skull_pitch=0)
    c.layer(jiggle(14, 0.05, freq=3.6, decay=7.0))
    C.append(c)
    # ---- ooze_split (0.9 s): bulges wide, then pinches in two along its middle (left / right lobes pull apart)
    c = K.Clip("ooze_split", 27, hits=[[24 / FPS, 27 / FPS]])
    c.key(0).key(9, body_st=-0.1, body_w=0.06, spine1_st=-0.06, wobL_s=0.12, wobR_s=0.12, wobF_s=0.06, wobB_s=0.06,
                  crown_st=-0.1, pod_lift=25, jaw=20)
    c.key(18, body_st=-0.12, body_wx=0.12, spine1_st=-0.2, spine1_wx=-0.3, spine2_st=-0.3, spine2_wx=-0.35,
          crown_st=-0.35, crown_wx=-0.2, wobL_s=0.14, wobR_s=0.14, wobL_lift=22, wobR_lift=22, wobL_out=0.08,
          wobR_out=0.08, wobF_s=-0.28, wobB_s=-0.28, wobF_out=-0.12, wobB_out=-0.12, pod_lift=10, podL_yaw=-25,
          jaw=30, skull_roll=20)
    c.key(24, body_st=-0.14, body_wx=0.18, spine1_st=-0.3, spine1_wx=-0.42, spine2_st=-0.4, spine2_wx=-0.45,
          crown_st=-0.45, crown_wx=-0.25, wobL_s=0.16, wobR_s=0.16, wobL_lift=34, wobR_lift=34, wobL_out=0.14,
          wobR_out=0.14, wobF_s=-0.52, wobB_s=-0.52, wobF_out=-0.28, wobB_out=-0.28, pod_lift=0, podL_yaw=-35, jaw=34,
          skull_roll=28)
    c.key(27, body_st=-0.15, body_wx=0.2, spine1_st=-0.32, spine1_wx=-0.45, spine2_st=-0.42, spine2_wx=-0.48,
          crown_st=-0.47, crown_wx=-0.27, wobL_s=0.17, wobR_s=0.17, wobL_lift=36, wobR_lift=36, wobL_out=0.15,
          wobR_out=0.15, wobF_s=-0.55, wobB_s=-0.55, wobF_out=-0.3, wobB_out=-0.3, pod_lift=0, podL_yaw=-36,
          jaw=34, skull_roll=30)
    c.layer(lambda f, cl: {"wobL.lift": 5 * math.sin(f * 1.3) * (f / 27) ** 2,
                           "wobR.lift": -5 * math.sin(f * 1.1) * (f / 27) ** 2})
    C.append(c)
    return C


# ------------------------------------------------------------------------------------------------ mesh
def resample(pts, n):
    p = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    Ls = np.concatenate([[0], np.cumsum(seg)])
    out = []
    for t in np.linspace(0, Ls[-1], n):
        i = min(np.searchsorted(Ls, t, side="right") - 1, len(seg) - 1)
        u = (t - Ls[i]) / max(seg[i], 1e-9)
        out.append(p[i] * (1 - u) + p[i + 1] * u)
    return np.array(out)


def chaikin(p, it=2):
    p = np.asarray(p, float)
    for _ in range(it):
        q = [p[0]]
        for a, b in zip(p[:-1], p[1:]):
            q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        q.append(p[-1])
        p = np.array(q)
    return p


def vertex_normals(V, F):
    N = np.zeros_like(V)
    for f in F:
        for i in range(1, len(f) - 1):
            a, b, c = V[f[0]], V[f[i]], V[f[i + 1]]
            n = np.cross(b - a, c - a)
            for k in (f[0], f[i], f[i + 1]):
                N[k] += n
    ln = np.linalg.norm(N, axis=1, keepdims=True)
    return N / np.maximum(ln, 1e-12)


PROFILE = [(0.0, 0.0), (0.55, 0.0), (0.76, 0.013), (0.82, 0.062), (0.81, 0.17), (0.77, 0.3), (0.7, 0.47),
           (0.61, 0.64), (0.5, 0.8), (0.36, 0.94), (0.22, 1.05), (0.09, 1.115), (0.0, 1.13)]
ZTOP = 1.13
_PROF = None
_PH = np.random.default_rng(5).random(6) * 6.28


def prof():
    global _PROF
    if _PROF is None:
        _PROF = chaikin(PROFILE, 2)
    return _PROF


def lump(a, t):
    ph = _PH
    return 1 + (0.055 * math.sin(3 * a + ph[0]) * math.sin(math.pi * min(t * 1.4, 1.0))
                + 0.035 * math.sin(5 * a + ph[1] + 5 * t) * math.sin(math.pi * t)
                + 0.025 * math.sin(7 * a + ph[2] - 3 * t) * min(t / 0.08, 1.0)
                + 0.03 * math.sin(2 * a + ph[3]) * t)


def blob_xy(r, a, z):
    k = lump(a, z / ZTOP)
    x, y = r * k * math.cos(a), r * k * math.sin(a)
    if y < 0:
        y *= 1.04                       # a little fuller at the front
    return x, y


def blob_surface(na=40, nz=26):
    pr = resample(prof(), nz)
    V, F = [], []
    rows = []
    for j, (r, z) in enumerate(pr):
        if r < 1e-6:
            rows.append([len(V)] * na)
            V.append((0.0, 0.0, z))
            continue
        row = []
        for i in range(na):
            a = 2 * math.pi * i / na
            x, y = blob_xy(r, a, z)
            row.append(len(V))
            V.append((x, y, z))
        rows.append(row)
    for j in range(len(rows) - 1):
        for i in range(na):
            i2 = (i + 1) % na
            q = [rows[j][i], rows[j][i2], rows[j + 1][i2], rows[j + 1][i]]
            face = []
            for v in q:
                if v not in face:
                    face.append(v)
            if len(face) >= 3:
                F.append(tuple(face))
    return np.array(V, float), F


def surf_point(a, z, push=0.0):
    """Point on the rest blob surface at angle a (rad, 0 = +X / its left, -pi/2 = front) and height z, with the
    outward normal (numerical)."""
    def P(a_, z_):
        r = float(np.interp(z_, prof()[:, 1], prof()[:, 0]))
        x, y = blob_xy(r, a_, z_)
        return np.array([x, y, z_])
    p = P(a, z)
    e = 1e-3
    ta = P(a + e, z) - P(a - e, z)
    tz = P(a, z + e) - P(a, z - e)
    n = normalize(np.cross(ta, tz))
    if np.dot(n, p - np.array([0, 0, z * 0.6])) < 0:
        n = -n
    return p + n * push, n


def build_mesh(mats):
    import bh_mesh as M
    parts = []
    rng = np.random.default_rng(13)
    BLOB_B = ["body", "spine1", "spine2", "crown", "wobF", "wobB", "wobL", "wobR"]
    BLOB_BIAS = {"body": 1.25, "spine1": 1.15, "spine2": 1.05, "crown": 1.0}

    def add(p, bone=None, bones=None, power=4.0, bias=None, top=3, W=None):
        if W is not None:
            p.W = W
        elif bone:
            p.W = [{bone: 1.0}] * len(p.V)
        else:
            p.W = K.dist_weights(RIG, p.V, bones, power=power, bias=bias, top=top)
        parts.append(p)
        return p

    # ---- the blob and its glowing rim shell (inverted hull: flipped faces, pushed out along the normals)
    V, F = blob_surface()
    Wb = K.dist_weights(RIG, V, BLOB_B, power=3.5, bias=BLOB_BIAS, top=4)
    add(M.Part(V, F, "BH_Ichor", name="blob"), W=Wb)
    N = vertex_normals(V, F)
    Vh = V + N * RIM
    Vh[:, 2] = np.maximum(Vh[:, 2], 0.0)
    add(M.Part(Vh, [tuple(reversed(f)) for f in F], "BH_Aether", name="rim"), W=Wb)

    def shell(V, F, W, t=RIM * 0.8):
        Nn = vertex_normals(V, F)
        add(M.Part(V + Nn * t, [tuple(reversed(f)) for f in F], "BH_Aether", name="shell"), W=W)

    # ---- pseudopods: stubby fat lobes out of the front-sides, bulb tips (and their rim shell)
    for s_, sx in (("L", 1), ("R", -1)):
        d = normalize(T[f"pod{s_}2"] - H[f"pod{s_}1"])
        pts = [H[f"pod{s_}1"] - d * 0.08, H[f"pod{s_}1"] + d * 0.06, H[f"pod{s_}2"], T[f"pod{s_}2"] - d * 0.05]
        prof = [(0.22, 0.2), (0.19, 0.17), (0.15, 0.13), (0.12, 0.105)]
        V, F = M.tube(pts, prof, n=14, up=(0, 0, 1))
        bones = [f"pod{s_}1", f"pod{s_}2", "spine1", "body"]
        Wp = K.dist_weights(RIG, V, bones, power=5, bias={"spine1": 1.8, "body": 2.0})
        add(M.Part(V, F, "BH_Ichor", name="pod"), W=Wp)
        shell(V, F, Wp)
        c = T[f"pod{s_}2"] - d * 0.05
        V, F = M.sphere(0.125, 14, 7, center=c, scale=(1.0, 1.0, 0.88))
        add(M.Part(V, F, "BH_Ichor", name="pod_tip"), bone=f"pod{s_}2")
        shell(V, F, [{f"pod{s_}2": 1.0}] * len(V))
        for k in range(4):   # glowing nubs on the pod tip
            dd = normalize(d + np.array([0.35 * (k - 1.5), 0.0, 0.35 * ((k % 2) - 0.3)]))
            V, F = M.sphere(0.024, 8, 4, center=c + dd * 0.115)
            add(M.Part(V, F, "BH_Emissive", name="nub"), bone=f"pod{s_}2")

    # ---- the skull pressing out of the front skin (a bit more than half out), jaw on its own bone (opens to spit)
    sp, sn = surf_point(SKULL_A, SKULL_Z)
    sc = sp - sn * 0.02
    yaw = math.degrees(math.atan2(sn[0], -sn[1]))
    Rs = Rz(yaw) @ Rx(-8)          # skull authored facing -Y, turned to face along the skin normal

    def sk(V):
        return (np.asarray(V, float) - sc) @ Rs.T + sc
    S = 1.6
    V, F = M.sphere(0.1 * S, 14, 8, center=sc + np.array((0, 0.02, 0.03)) * S, scale=(0.88, 1.0, 0.92))
    add(M.Part(sk(V), F, "BH_Bone", name="cranium"), bone="skull")
    V, F = M.sphere(0.075 * S, 12, 6, center=sc + np.array((0, -0.05, -0.035)) * S, scale=(0.9, 0.75, 0.75))
    add(M.Part(sk(V), F, "BH_Bone", name="face"), bone="skull")
    for sx in (1, -1):
        V, F = M.sphere(0.03 * S, 10, 5, center=sc + np.array((sx * 0.036, -0.098, -0.005)) * S,
                        scale=(1.0, 0.55, 0.95))
        add(M.Part(sk(V), F, "BH_Shadow", name="socket"), bone="skull")
        V, F = M.sphere(0.011 * S, 6, 4, center=sc + np.array((sx * 0.036, -0.112, -0.005)) * S)
        add(M.Part(sk(V), F, "BH_Emissive", name="socket_glint"), bone="skull")
        V, F = M.sphere(0.03 * S, 8, 4, center=sc + np.array((sx * 0.07, -0.06, -0.035)) * S, scale=(0.7, 1.2, 0.6))
        add(M.Part(sk(V), F, "BH_Bone", name="cheek"), bone="skull")
    V, F = M.sphere(0.015 * S, 6, 4, center=sc + np.array((0, -0.118, -0.05)) * S, scale=(0.8, 0.5, 1.4))
    add(M.Part(sk(V), F, "BH_Shadow", name="nose"), bone="skull")
    for i in range(6):   # upper teeth
        a = math.radians(-50 + 20 * i)
        V, F = M.box(0.012 * S, 0.01 * S, 0.022 * S,
                     center=sc + np.array((0.045 * math.sin(a), -0.095 * math.cos(a) + 0.005, -0.085)) * S)
        add(M.Part(sk(V), F, "BH_Bone", name="tooth"), bone="skull")
    jaw_pts = [(0.06, -0.01, -0.07), (0.05, -0.07, -0.1), (0.0, -0.1, -0.11), (-0.05, -0.07, -0.1),
               (-0.06, -0.01, -0.07)]
    V, F = M.tube(sk([sc + np.array(p) * S for p in jaw_pts]), [(0.016 * S, 0.022 * S)] * 5, n=6,
                  up=tuple(Rs @ np.array((0, 0, 1.0))))
    add(M.Part(V, F, "BH_Bone", name="jaw"), bone="jaw")
    for i in range(5):
        a = math.radians(-40 + 20 * i)
        V, F = M.box(0.011 * S, 0.009 * S, 0.02 * S,
                     center=sc + np.array((0.042 * math.sin(a), -0.09 * math.cos(a) + 0.005, -0.1)) * S)
        add(M.Part(sk(V), F, "BH_Bone", name="ltooth"), bone="jaw")

    # ---- ribs arching out of the left-back flank, a femur jutting from the back, finger bones near the top
    for k in range(4):
        a0 = math.radians(45 + 12 * k)
        z = 0.3 + 0.11 * k
        pts = []
        for u in np.linspace(0, 1, 8):
            aa = a0 + math.radians(-38 + 76 * u)
            p, n = surf_point(aa, z + 0.07 * math.sin(math.pi * u), push=0.05 * math.sin(math.pi * u) - 0.02)
            pts.append(p)
        V, F = M.tube(pts, [(0.022, 0.028)] * 8, n=6, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Bone", name="rib"), bones=BLOB_B, power=3.5, bias=BLOB_BIAS, top=4)
    p0, n0 = surf_point(math.radians(118), 0.55, push=-0.1)
    d = normalize(n0 + np.array([0.0, 0.3, 0.55]))
    pts = [p0, p0 + d * 0.2, p0 + d * 0.38]
    V, F = M.tube(pts, [(0.03, 0.03), (0.024, 0.024), (0.03, 0.03)], n=8, up=(1, 0, 0))
    add(M.Part(V, F, "BH_Bone", name="femur"), bones=BLOB_B, power=3.5, bias=BLOB_BIAS, top=4)
    for sx in (-1, 1):
        V, F = M.sphere(0.042, 8, 5, center=pts[-1] + np.array([sx * 0.03, 0, 0.01]))
        add(M.Part(V, F, "BH_Bone", name="femur_head"), bones=BLOB_B, power=3.5, bias=BLOB_BIAS, top=4)
    for k, (aa, z) in enumerate(((-0.6, 0.9), (2.4, 0.84), (-2.2, 0.7))):
        p, n = surf_point(aa, z, push=0.0)
        d = normalize(n + rng.normal(size=3) * 0.4)
        V, F = M.tube([p - d * 0.04, p + d * 0.06, p + d * 0.1], [(0.014, 0.014), (0.012, 0.012), (0.015, 0.015)],
                      n=6, up=(0, 0, 1))
        add(M.Part(V, F, "BH_Bone", name="knuckle"), bones=BLOB_B, power=3.5, bias=BLOB_BIAS, top=4)

    # ---- submerged bones: muted teal-ivory shapes flush with the skin (read as bones seen through the jelly)
    def ghost_arc(a0, a1, z0, z1, r, n=9, bulge=0.05):
        pts = []
        for u in np.linspace(0, 1, n):
            p, nn = surf_point(a0 + (a1 - a0) * u, z0 + (z1 - z0) * u + bulge * math.sin(math.pi * u), push=0.004)
            pts.append((p, nn))
        P = [p for p, _ in pts]
        ups = [nn for _, nn in pts]
        V, F = M.tube(P, [(r, r * 0.25)] * n, n=6, up=ups)
        add(M.Part(V, F, "BH_Horn", name="ghost"), bones=BLOB_B, power=3.5, bias=BLOB_BIAS, top=4)
    for k in range(4):                                     # ghost ribcage on the right-back flank
        ghost_arc(math.radians(160 + 8 * k), math.radians(222 + 6 * k), 0.3 + 0.12 * k, 0.26 + 0.12 * k, 0.026)
    for k in range(7):                                     # ghost spine up the back
        z = 0.24 + 0.1 * k
        a = math.radians(92 + 8 * math.sin(k * 0.9))
        ghost_arc(a - 0.06, a + 0.06, z, z, 0.03, n=3, bulge=0.0)
    for k in range(3):                                     # a ghost hand on the left-front flank
        a = math.radians(-20 + 9 * k)
        ghost_arc(a, a + 0.04, 0.34, 0.52 + 0.03 * math.sin(k * 1.6), 0.016, n=5, bulge=0.01)

    # ---- the lumpy crown of bubbles (lighter teal, rim-shelled) + glowing ones
    crown = [(0.0, 1.0, 0.16, 0.0), (1.0, 0.94, 0.12, 0.12), (2.6, 0.92, 0.13, 0.13), (-2.2, 0.9, 0.12, 0.16),
             (-0.9, 0.95, 0.11, 0.14), (1.8, 0.86, 0.09, 0.2), (-1.6, 0.82, 0.1, 0.22), (0.3, 0.88, 0.08, 0.26)]
    for q, (aa, z, r, off) in enumerate(crown):
        if off == 0:
            p = np.array([0.0, 0.03, ZTOP - 0.02])
            n = np.array([0, 0, 1.0])
        else:
            p, n = surf_point(aa, z)
        c = p + n * r * 0.3
        V, F = M.sphere(r, 14, 7, center=c, scale=(1.0, 1.0, 0.92))
        Wc = K.dist_weights(RIG, V, ["spine2", "crown", "spine1"], power=4)
        add(M.Part(V, F, "BH_Flesh", name="crown_bubble"), W=Wc)
        add(M.Part(c + (V - c) * ((r + RIM * 0.7) / r), [tuple(reversed(f)) for f in F], "BH_Aether", name="cb_rim"),
            W=Wc)
        V, F = M.sphere(r * (0.3 if q % 3 else 0.45), 8, 4,
                        center=c + normalize(n + np.array([0.3, -0.4, 0.8])) * r * 0.8)
        add(M.Part(V, F, "BH_Emissive", name="crown_glint"), W=K.dist_weights(RIG, V, ["spine2", "crown"], power=4))
    for i in range(22):   # glowing bubbles in the skin
        aa = rng.random() * 2 * math.pi
        z = 0.2 + 0.72 * rng.random()
        if math.cos(aa - SKULL_A) > 0.75 and 0.3 < z < 0.8:
            continue   # keep the skull area clear
        p, n = surf_point(aa, z)
        r = 0.02 + 0.032 * rng.random()
        V, F = M.sphere(r, 8, 5, center=p + n * r * 0.1)
        add(M.Part(V, F, "BH_Emissive", name="bubble"), bones=BLOB_B, power=3.5, bias=BLOB_BIAS, top=4)
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
    for m in mats.values():   # single-sided everywhere (the rim shell relies on back-face culling)
        m.use_backface_culling = True
    arm = K.build_armature(RIG)
    parts = build_mesh(mats)
    mesh = M.build_skinned(NAME, parts, arm, mats, sharp_angle=70)
    MT.bake_vertex_ao(mesh, rays=12, dist=0.2, strength=0.5)
    acts = {}
    for c in clips():
        if only and c.name not in only:
            continue
        acts[c.name] = (c, K.bake(arm, RIG, c, evaluate))
    return arm, mesh, acts


REST_CFG = dict(views=[("front 3/4", (0, 0, 0.6), 4.4, 30, 10), ("side", (0, 0, 0.6), 4.4, 90, 8),
                       ("back 3/4", (0, 0, 0.6), 4.4, 200, 12), ("skull close-up", (0.05, -0.55, 0.7), 1.6, 20, 8)],
                game=[(16, 0, 1.0), (16, 150, 1.0), (24, 60, 1.0), (16, 20, 0.65), (16, 20, 0.45), (24, 20, 0.45)],
                target_z=0.5)


def clip_cfg():
    return dict(clips=["ooze_slam", "ooze_spit", "ooze_split", "walk", "death", "idle"], target=(0, -0.1, 0.65),
                dist=4.8, yaw=55, pitch=14)


if __name__ == "__main__":
    K.run_main(build_all, NAME, PREFIX, "tools/blender/creatures/build_gloam_ooze.py", REST_CFG, clip_cfg, RIG,
               evaluate)
