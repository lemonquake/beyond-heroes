"""Locomotion: procedural slide-free cycles (bh_gait) plus keyed starts, stops, turns and dodges."""
import math

import bh_gait as G
from lib_common import anim, breath, ramp_layer
from lib_poses import (U, RELAX, ST_1H, tw, torso, look, hips, clav, arm, grip, foot, feet, leg_fk, mirror,
                       L_GUARD, SWORD_READY)

WALK = dict(frames=26, speed=1.6, duty=0.58, lift=0.08, bob=0.018, drop=0.045, reach_bias=-0.08, toe_strike=14,
            heel_off=32, lean=3, arm_swing=17, elbow=16, elbow_swing=14)
RUN = dict(frames=20, speed=5.0, duty=0.26, lift=0.21, bob=0.02, bob_phase="run", drop=0.05, reach_bias=-0.1,
           toe_strike=5, heel_off=45, lean=11, pelvis_yaw=14, pelvis_roll=5, arm_el=-58, arm_out=14, elbow=88,
           elbow_swing=18, arm_swing=34, swing_tangent=0.45, lift_skew=0.55, heel_lift_swing=0.6)
WALK_BACK = dict(frames=20, speed=1.8, direction=180, duty=0.55, lift=0.07, bob=0.012, drop=0.05, reach_bias=0.0,
                 toe_strike=12, heel_off=25, lean=-2, arm_swing=10, elbow=22)
STRAFE = dict(frames=20, speed=3.2, direction=90, duty=0.34, lift=0.12, bob=0.02, bob_phase="run", drop=0.07,
              reach_bias=-0.08, toe_strike=6, heel_off=30, hips_face=40, pelvis_yaw=6, arm_swing=8, arm_el=-70,
              elbow=40, lean=5)
RUN_COMBAT = dict(frames=20, speed=4.6, duty=0.28, lift=0.16, bob=0.02, bob_phase="run", drop=0.09,
                  reach_bias=-0.1, toe_strike=5, heel_off=40, lean=14, pelvis_yaw=10, upper=False)
WALK_HURT = dict(frames=30, speed=1.1, lift=0.06, bob=0.015, drop=0.05, toe_strike=10, heel_off=24, limp=1.0,
                 duty=0.66, duty_R=0.5, phase_R=0.56, lean=8, arm_swing=6)
RUN_HURT = dict(frames=22, speed=3.0, lift=0.13, bob=0.02, bob_phase="run", drop=0.1, reach_bias=-0.08,
                toe_strike=6, heel_off=35, limp=1.0, duty=0.42, duty_R=0.3, phase_R=0.54, lean=12, arm_swing=14,
                arm_el=-64, elbow=70)

RIB_HOLD = grip("L", -70, 0.10, 1.2, -60, 30, 0, pole=15)


def gait_anim(name, params, props="none", upper_pose=None, layers=(), lag=None):
    g = G.Gait(**params)
    keys = [(0, upper_pose or {}), (g.T, upper_pose or {})]
    gl = g.layer() if upper_pose is None else _gait_keep_arms(g, upper_pose)
    a = anim(name, g.T, keys, loop=True, props=props, lag=lag, layers=[gl] + list(layers))
    a.meta.update(g.meta())
    a.meta["footsteps"] = g.footsteps()
    a.gait = g
    return a


def _gait_keep_arms(g, pose):
    arm_keys = [k for k in pose if k.startswith(("arm.", "fore.", "hand.", "hik.", "armik.", "clav."))]

    def fn(f, c):
        gc = g.channels(f)
        for k, v in gc.items():
            if k in arm_keys:
                continue
            c[k] = v
    return fn


def gait_blend(g, offset, w0, w1, w2=None, w3=None, legs_only=False):
    """Blend towards gait channels (sampled at f + offset) with weight rising over [w0, w1] (and falling over
    [w2, w3] if given)."""
    def fn(f, c):
        if f <= w0:
            w = 0.0
        elif f < w1:
            w = (f - w0) / (w1 - w0)
        else:
            w = 1.0
        if w2 is not None:
            if f >= w3:
                w = 0.0
            elif f > w2:
                w = min(w, 1.0 - (f - w2) / (w3 - w2))
        if w <= 0:
            return
        w = w * w * (3 - 2 * w)
        gc = g.channels(f + offset)
        for k, v in gc.items():
            if legs_only and k.startswith(("arm.", "fore.", "hand.")):
                continue
            c[k] = c[k] + (v - c[k]) * w
    return fn


def rot_foot(s, ang, r=0.12, up=0.0, heel=0.0, base_yaw=8.0, knee=5.0):
    """Foot placed at its home position rotated by `ang` degrees around the body axis (CCW = turning left)."""
    sx = 1.0 if s == "L" else -1.0
    a = math.radians(ang)
    x0, y0 = sx * r, 0.0
    x = x0 * math.cos(a) - y0 * math.sin(a)
    y = x0 * math.sin(a) + y0 * math.cos(a)
    return foot(s, fwd=-y, out=sx * x, yaw=base_yaw + sx * ang, up=up, heel=heel, knee=knee)


def build():
    out = []
    out.append(gait_anim("walk", WALK))
    out.append(gait_anim("run", RUN, layers=[]))
    out.append(gait_anim("walk_back", WALK_BACK))
    sl = gait_anim("strafe_l", STRAFE)
    out.append(sl)
    sr_params = dict(STRAFE, direction=-90, hips_face=-40)
    out.append(gait_anim("strafe_r", sr_params))
    upper = U(SWORD_READY, L_GUARD, clav("L", 4, 6), clav("R", 4, 6), look(0, 4))
    upper = U(upper, grip("R", 45, 0.30, 1.12, 20, 30, 0, pole=0))
    out.append(gait_anim("run_combat", RUN_COMBAT, props="sword", upper_pose=upper))
    out.append(gait_anim("walk_hurt", WALK_HURT, upper_pose=None, layers=[_rib_hold(), breath(15, 1.2, hurt=True)]))
    out.append(gait_anim("run_hurt", RUN_HURT, layers=[_rib_hold(), breath(11, 1.0, hurt=True)]))

    # ---- run_start: dip, lean, drive into the run cycle (ends exactly on run frame 0) ------------------------
    grun = G.Gait(**RUN)
    L = 14
    k0 = U(RELAX)
    k1 = U(RELAX, hips(0, -0.02, -0.07), torso(4, 14, 0, 0, 8, 0, 0, 4, 0), look(0, -10),
           arm("L", -62, 50, 70), arm("R", -60, -30, 60), foot("R", -0.08, 0.13, 10, heel=25))
    a = anim("run_start", L, [(0, k0), (4, k1, "out"), (L, k1)],
             layers=[gait_blend(grun, -L, 3, L - 1)], footsteps=[5, 10], ground_speed=RUN["speed"])
    out.append(a)

    # ---- run_stop: plant, brake with the body leaning back, settle to idle -----------------------------------
    brake = U(RELAX, hips(0, 0.03, -0.14), torso(-6, -6, 0, 0, -4, 0, 0, -6, 0), look(0, 6),
              foot("L", 0.34, 0.13, 10, toe=16, knee=8), foot("R", -0.14, 0.14, 14, heel=28, knee=6),
              arm("L", -55, 55, 60), arm("R", -60, 40, 55))
    settle = U(RELAX, hips(0, 0.0, -0.05), torso(0, 6, 0, 0, 4, 0, 0, 3, 0), foot("L", 0.12, 0.12, 8),
               foot("R", -0.02, 0.13, 10))
    a = anim("run_stop", 24, [(0, brake), (6, brake, "out"), (10, U(brake, hips(0, 0.0, -0.12), torso(-4, 10, 0, 0, 8, 0, 0, 6, 0))),
                              (16, settle), (24, RELAX)],
             layers=[gait_blend(grun, 0, -1, -0.5, 1, 6)], footsteps=[4, 12])
    out.append(a)

    # ---- turns (90 deg in place, ends rotated: the game turns the capsule by 90 deg) -------------------------
    t0 = RELAX
    t1 = U(RELAX, look(35, 0), torso(4, 0, 0, 4, 0, 0, 10, 0, 0), hips(-0.02, 0, -0.035), foot("R", 0, 0.12, 8))
    t2 = U(RELAX, look(28, 0), torso(40, 0, 0, 6, 0, 0, 8, 0, 0), hips(-0.015, 0, -0.05),
           rot_foot("L", 45, up=0.07), rot_foot("R", 0, heel=10), arm("L", -76, -10, 18), arm("R", -72, 30, 18))
    t3 = U(RELAX, look(12, 0), torso(66, 0, 0, 4, 0, 0, 4, 0, 0), hips(0.0, 0, -0.045),
           rot_foot("L", 90), rot_foot("R", 20, heel=18))
    t4 = U(RELAX, look(4, 0), torso(82, 0, 0, 2, 0, 0, 2, 0, 0), hips(0.0, 0, -0.04),
           rot_foot("L", 90), rot_foot("R", 55, up=0.06), arm("L", -76, 20, 18), arm("R", -78, -4, 16))
    t5 = U(RELAX, torso(90, 0, 0, 0, 0, 0, 0, 0, 0), hips(0, 0, -0.02), rot_foot("L", 90), rot_foot("R", 90))
    tl = anim("turn_l", 22, [(0, t0), (3, t1), (8, t2), (12, t3), (16, t4), (20, t5), (22, t5)],
              lag={"arm": 1.5, "head": -1}, footsteps=[11, 19], turn=90)
    out.append(tl)
    tr = anim("turn_r", 22, [(f, mirror(p)) for f, p in [(0, t0), (3, t1), (8, t2), (12, t3), (16, t4), (20, t5),
                                                          (22, t5)]],
              lag={"arm": 1.5, "head": -1}, footsteps=[11, 19], turn=-90)
    out.append(tr)

    # ---- dodge_roll: dive, tucked forward roll over the shoulder, come up ready -------------------------------
    d0 = U(RELAX, hips(0, 0, -0.03))
    d1 = U(RELAX, hips(0, 0.05, -0.2), torso(0, 30, 0, 0, 14, 0, 0, 8, 0), look(0, -10),
           foot("L", 0.22, 0.12, 8, knee=6), foot("R", -0.18, 0.12, 10, heel=35),
           arm("L", -20, 80, 30), arm("R", -25, 80, 30))
    tuckleg = U(leg_fk("L", 125, 135, 30), leg_fk("R", 115, 140, 30))
    tuckarm = U(arm("L", -10, 75, 115, 0, 20), arm("R", -10, 75, 115, 0, 20))
    d2 = U(tuckarm, hips(0, 0.1, -0.5), torso(0, 75, 0, 0, 30, 0, 0, 25, 0), look(0, 45),
           leg_fk("L", 110, 120, 20), leg_fk("R", 20, 30, 45))
    d3 = U(tuckarm, tuckleg, hips(0, 0.0, -0.58), torso(0, 170, 0, 0, 32, 0, 0, 25, 0), look(0, 45))
    d4 = U(tuckarm, tuckleg, hips(0, 0.0, -0.58), torso(0, 260, 0, 0, 30, 0, 0, 22, 0), look(0, 40))
    d5 = U(arm("L", -40, 60, 60), arm("R", -40, 60, 60), hips(0, 0.02, -0.42), torso(0, 330, 0, 0, 22, 0, 0, 14, 0),
           look(0, 20), leg_fk("L", 100, 125, 15), leg_fk("R", 95, 130, 15))
    d6 = U(RELAX, hips(0, 0.02, -0.3), torso(0, 360 + 28, 0, 0, 14, 0, 0, 8, 0), look(0, -12),
           foot("L", 0.14, 0.13, 10, knee=8), foot("R", -0.1, 0.13, 14, heel=20, knee=8),
           arm("L", -50, 50, 60), arm("R", -50, 40, 60))
    d7 = U(RELAX, hips(0, 0.0, -0.07), torso(0, 360 + 5, 0, 0, 3, 0, 0, 2, 0), foot("L", 0.1, 0.13, 10),
           foot("R", -0.06, 0.13, 12))
    out.append(anim("dodge_roll", 22, [(0, d0), (3, d1), (6, d2), (9, d3), (12, d4), (15, d5), (18, d6),
                                       (22, d7)],
                    iframes=[2, 15], travel=4.0, footsteps=[17], lag={"head": 1}))

    # ---- dodge_step: quick hop backward -------------------------------------------------------------------
    s0 = U(RELAX, hips(0, 0, -0.03))
    s1 = U(RELAX, hips(0, 0.02, -0.1), torso(0, 8, 0, 0, 4, 0, 0, 2, 0), feet(0.04, -0.04, 0.13, 0.13, 10, 12, 8, 8),
           arm("L", -70, 30, 30), arm("R", -70, 30, 30))
    s2 = U(RELAX, hips(0, -0.04, 0.0), torso(0, 12, 0, 0, 6, 0, 0, 4, 0), look(0, -6),
           foot("L", 0.12, 0.14, 10, up=0.1, toe=-15, knee=8), foot("R", 0.0, 0.14, 12, up=0.08, toe=-20, knee=8),
           arm("L", -45, 40, 40), arm("R", -45, 40, 40))
    s3 = U(RELAX, hips(0, 0.02, -0.12), torso(0, 14, 0, 0, 8, 0, 0, 4, 0),
           foot("L", 0.1, 0.14, 10, heel=10, knee=8), foot("R", -0.08, 0.14, 14, heel=16, knee=8),
           arm("L", -60, 40, 40), arm("R", -62, 35, 40))
    s4 = U(RELAX, hips(0, 0.0, -0.04), foot("L", 0.08, 0.13, 10), foot("R", -0.05, 0.13, 12))
    out.append(anim("dodge_step", 14, [(0, s0), (2, s1, "in"), (5, s2, "out"), (8, s3), (14, s4)],
                    iframes=[1, 7], travel=1.8, footsteps=[8]))
    return out


def _rib_hold():
    def fn(f, c):
        for k, v in RIB_HOLD.items():
            c[k] = v
        c["chest.roll"] += -3.0
        c["head.roll"] += 2.0
    return fn
