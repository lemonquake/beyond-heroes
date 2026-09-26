"""Procedural, slide-free locomotion cycles.

A gait is defined in the character frame (in place). Each foot alternates a stance phase, during which its ground
contact point moves backward at exactly the ground speed (so the feet never slide when the capsule moves at that
speed), and a swing phase (Hermite curve with retraction before contact, lift arc, heel-off / toe-strike roll).
Pelvis yaw, arm swing and head stabilization are derived from the foot positions, so the whole body stays coherent.

All distances are standard-rig meters (bh_skeleton.STD); a rig with leg scale k moves at k * speed.
"""
import math

import numpy as np

from bh_math import hermite

FPS = 30.0


def smoothstep(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


class Gait:
    def __init__(self, frames, speed, direction=0.0, duty=0.6, lift=0.09, width=0.11, reach_bias=0.0,
                 toe_strike=14.0, heel_off=32.0, swing_toe=8.0, bob=0.02, bob_phase="walk", drop=0.0,
                 sway=0.018, pelvis_yaw=7.0, pelvis_roll=4.0, lean=3.0, chest_counter=0.8, arm_swing=18.0,
                 arm_el=-78.0, arm_out=9.0, elbow=14.0, elbow_swing=10.0, hips_face=0.0, knee_out=5.0,
                 foot_yaw=6.0, phase_R=0.5, duty_R=None, limp=0.0, upper=True, head_stab=0.85,
                 swing_tangent=0.55, lift_skew=0.45, heel_lift_swing=0.45):
        self.T = int(frames)
        self.v = float(speed)
        self.dir = float(direction)          # 0 = forward, 90 = toward own left, -90 = right, 180 = backward
        self.duty = {"L": duty, "R": duty if duty_R is None else duty_R}
        self.phase0 = {"L": 0.0, "R": phase_R}
        self.lift = lift
        self.width = width
        self.reach_bias = reach_bias         # shifts the stance interval forward (+) / back (-) relative to the hip
        self.toe_strike = toe_strike
        self.heel_off = heel_off
        self.swing_toe = swing_toe
        self.bob = bob
        self.bob_phase = bob_phase
        self.drop = drop
        self.sway = sway
        self.pelvis_yaw = pelvis_yaw
        self.pelvis_roll = pelvis_roll
        self.lean = lean
        self.chest_counter = chest_counter
        self.arm_swing = arm_swing
        self.arm_el = arm_el
        self.arm_out = arm_out
        self.elbow = elbow
        self.elbow_swing = elbow_swing
        self.hips_face = hips_face           # constant pelvis yaw toward the motion (strafes)
        self.knee_out = knee_out
        self.foot_yaw = foot_yaw
        self.limp = limp                     # 0..1: right leg injured
        self.upper = upper
        self.head_stab = head_stab
        self.swing_tangent = swing_tangent
        self.lift_skew = lift_skew
        self.heel_lift_swing = heel_lift_swing
        th = math.radians(self.dir)
        self.u = np.array([math.sin(th), -math.cos(th)])       # motion direction (world XY, character frame)
        self.travel = {s: self.v * self.duty[s] * self.T / FPS for s in "LR"}

    # ------------------------------------------------------------------------------------------
    @property
    def cycle_time(self):
        return self.T / FPS

    def stride(self):
        return self.v * self.cycle_time

    def phase(self, f, s):
        return ((f / self.T) - self.phase0[s]) % 1.0

    def footsteps(self):
        """Frames of foot contact (L then R)."""
        return sorted(((self.phase0[s] * self.T) % self.T) for s in "LR")

    def foot_q(self, f, s):
        """Scalar position along the motion direction of the foot reference point, lift, heel, toe angles."""
        b = self.duty[s]
        L = self.travel[s]
        a = L * 0.5 + self.reach_bias
        bb = L - a
        ph = self.phase(f, s)
        back = math.cos(math.radians(self.dir)) < -0.3
        if ph < b:
            st = ph / b
            q = a - st * L
            up = 0.0
            if back:   # walking backward: land on the ball, finish on the heel with the toes lifting
                heel = self.toe_strike * (1.0 - smoothstep(0.0, 0.3, st))
                toe = self.heel_off * 0.4 * smoothstep(0.6, 1.0, st)
                return q, up, heel, toe, True
            toe = self.toe_strike * (1.0 - smoothstep(0.0, 0.2, st))
            heel = self.heel_off * smoothstep(0.5, 1.0, st) ** 1.6
            return q, up, heel, toe, True
        u = (ph - b) / (1.0 - b)
        # Hermite from -bb to a; end tangents keep the stance velocity (continuity) scaled down a little
        m = -L / b * (1.0 - b) * self.swing_tangent
        q = hermite(-bb, a, m, m, 1.0, u)
        sk = self.lift_skew
        w = u / sk * 0.5 if u < sk else 0.5 + (u - sk) / (1 - sk) * 0.5
        up = self.lift * math.sin(math.pi * w) ** 1.1
        if back:
            toe = self.heel_off * 0.4 * (1.0 - smoothstep(0.0, 0.4, u))
            heel = self.toe_strike * smoothstep(0.5, 1.0, u)
            return q, up, heel, toe, False
        heel = self.heel_off * (1.0 - smoothstep(0.0, self.heel_lift_swing, u))
        toe = self.toe_strike * smoothstep(0.55, 1.0, u) + self.swing_toe * math.sin(math.pi * u) * 0.3
        return q, up, heel, toe, False

    # ------------------------------------------------------------------------------------------
    def channels(self, f):
        c = {}
        th_face = math.radians(self.hips_face)
        fwd_pos = {}
        for s in "LR":
            sx = 1.0 if s == "L" else -1.0
            q, up, heel, toe, planted = self.foot_q(f, s)
            # home position rotates with the constant pelvis facing (strafes)
            hx, hy = sx * self.width, 0.0
            hx, hy = (hx * math.cos(th_face) - hy * math.sin(th_face), hx * math.sin(th_face) + hy * math.cos(th_face))
            limp = self.limp if s == "R" else 0.0
            x = hx + q * self.u[0]
            y = hy + q * self.u[1]
            fwd_pos[s] = -y
            c[f"legik.{s}"] = 1.0
            c[f"foot.{s}.out"] = sx * x
            c[f"foot.{s}.fwd"] = -y
            c[f"foot.{s}.up"] = up * (1.0 - 0.45 * limp)
            c[f"foot.{s}.heel"] = heel * (1.0 - 0.6 * limp)
            c[f"foot.{s}.toe"] = toe * (1.0 - 0.5 * limp)
            c[f"foot.{s}.yaw"] = self.foot_yaw + sx * self.hips_face
            c[f"knee.{s}.out"] = self.knee_out
        ph = (f / self.T) % 1.0
        bL = self.duty["L"]
        mid_L = bL * 0.5
        # vertical bob: walk = high at mid-stance, run = low at mid-stance
        cyc = math.cos(4 * math.pi * (ph - mid_L))
        bob = self.bob * cyc if self.bob_phase == "walk" else -self.bob * cyc
        if self.limp:
            # hip drops hard when the injured (R) leg takes weight
            phR = self.phase(f, "R")
            bob -= self.limp * 0.035 * math.sin(math.pi * min(phR / self.duty["R"], 1.0)) if phR < self.duty["R"] else 0.0
        c["hips.up"] = -self.drop + bob
        sway = math.cos(2 * math.pi * (ph - mid_L))
        c["hips.side"] = self.sway * sway * (1.0 if not self.limp else 1.0 + 0.8 * self.limp)
        span = max(self.travel["L"], 1e-3)
        dq = (fwd_pos["L"] - fwd_pos["R"]) / span        # ~ +-0.5
        c["hips.yaw"] = -self.pelvis_yaw * dq * 2.0 + self.hips_face
        c["hips.roll"] = -self.pelvis_roll * sway
        c["hips.pitch"] = self.lean * 0.5
        c["spine.pitch"] = self.lean * 0.3
        c["chest.pitch"] = self.lean * 0.2 + (2.0 if self.limp else 0.0)
        cy = -c["hips.yaw"] * self.chest_counter
        c["spine.yaw"] = cy * 0.45 - self.hips_face * 0.35
        c["chest.yaw"] = cy * 0.55 - self.hips_face * 0.35
        c["spine.roll"] = -c["hips.roll"] * 0.5
        c["chest.roll"] = -c["hips.roll"] * 0.3 + (-4.0 * self.limp)
        tot_yaw = c["hips.yaw"] + c["spine.yaw"] + c["chest.yaw"]
        tot_pitch = self.lean
        c["neck.yaw"] = -tot_yaw * self.head_stab * 0.5
        c["head.yaw"] = -tot_yaw * self.head_stab * 0.5
        c["neck.pitch"] = -tot_pitch * 0.4 - bob * 20
        c["head.pitch"] = -tot_pitch * 0.3
        c["head.roll"] = c["hips.roll"] * 0.3
        if self.upper:
            for s in "LR":
                o = "R" if s == "L" else "L"
                sw = (fwd_pos[o] - fwd_pos[s]) / span        # arm opposite to its own leg
                if abs(self.dir) > 100:                        # walking backward: arms still oppose the legs
                    sw = sw
                c[f"arm.{s}.el"] = self.arm_el + abs(sw) * 4.0
                c[f"arm.{s}.az"] = self.arm_out + self.arm_swing * sw * 2.0
                c[f"arm.{s}.tw"] = 0.0
                c[f"fore.{s}.bend"] = self.elbow + self.elbow_swing * max(sw * 2.0, 0.0)
                c[f"hand.{s}.flex"] = 8.0
        return c

    def layer(self, legs_only=False):
        """As an Anim layer: overwrite channels with gait values (legs/hips only if legs_only)."""
        def fn(f, c):
            g = self.channels(f)
            for k, v in g.items():
                if legs_only and (k.startswith("arm.") or k.startswith("fore.") or k.startswith("hand.")):
                    continue
                c[k] = v
        return fn

    def meta(self):
        return dict(ground_speed=self.v, footsteps=self.footsteps(), direction=self.dir)
