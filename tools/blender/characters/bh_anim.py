"""Pose-keyframe DSL, FK/IK evaluator and Blender action baker.

Poses are flat dicts of semantic channels (degrees / meters of the standard 1.8 m human). Every animation
is evaluated per frame (30 fps) on a specific character rig (its own bone lengths), including
two-bone IK for planted feet and two-handed grips, and baked to one Blender action with a key on every
frame for every bone (quaternion rotation) plus hips translation.

Channel semantics (L side; R side uses the same numbers and is mirrored automatically):
  hips.side/fwd/up        hips offset (m): side = toward character's left, fwd = forward (-Y), up = +Z
  <b>.pitch/yaw/roll      for hips, spine, chest, neck, head: pitch + = bend forward, yaw + = turn to own left,
                          roll + = lean to own left
  clav.S.raise/fwd        shoulder shrug / protraction
  arm.S.el/az/tw          upper arm direction: el = elevation (-90 hanging, 0 horizontal, +90 up),
                          az = azimuth (0 out to the side, 90 forward, -90 backward, >90 across the body),
                          tw = twist about the arm axis
  fore.S.bend/tw          elbow flexion, forearm twist
  hand.S.flex/dev         wrist flexion toward palm, deviation toward thumb
  wpn.S.x/y/z             weapon socket rotation (armature axes, usually 0)
  armik.S                 0..1 weight: hand grips the OTHER hand's weapon at armik.S.grip meters along the
                          weapon axis (negative = toward pommel), armik.S.rot = rotation around the grip
  hik.S                   0..1 weight: hand IK driven by a weapon-grip target in chest space:
                          grip position (standard rest coordinates, polar around the body axis):
                          hik.S.r = horizontal distance, hik.S.az = azimuth (0 = straight ahead, + = toward own side,
                          - = across the body), hik.S.z = height; hik.S.x / hik.S.fwd = extra cartesian offsets.
                          hik.S.yaw/pitch = blade direction (yaw + = toward own side, pitch + = up),
                          hik.S.roll = knuckle/true-edge direction about the blade: 0 = up (blade level),
                          +90 = toward the body midline, -90 = outward, 180 = down. hik.S.pole = elbow swivel
  legik.S                 0..1 weight of foot IK (1 = planted/targeted foot, 0 = FK thigh/shin/foot angles)
  foot.S.out/fwd/up       IK ankle target: lateral outward, forward, height above rest ankle height (m)
  foot.S.yaw              toes outward (deg); foot.S.heel = heel lift about the ball; foot.S.toe = toe lift
                          about the heel; toe.S.bend extra toe bend
  knee.S.out              knee pole rotation outward (deg)
  thigh.S.flex/abd/tw, shin.S.knee, foot.S.point   FK leg channels
"""
import math
import numpy as np

from bh_math import (Rx, Ry, Rz, R_axis, min_rot, mirror_rot, mat_to_quat, quat_to_mat, slerp_mat,
                     normalize, Xf, sample_channel, monotone_tangents, solve_two_bone)
from bh_skeleton import BONE_ORDER, PARENT, STD, joints, rest_frames

SIDES = ("L", "R")
MIRROR_V = np.array([-1.0, 1.0, 1.0])
SX = {"L": 1.0, "R": -1.0}
OTHER = {"L": "R", "R": "L"}

DEFAULTS = {}
for _b in ("hips", "spine", "chest", "neck", "head"):
    for _c in ("pitch", "yaw", "roll"):
        DEFAULTS[_b + "." + _c] = 0.0
DEFAULTS.update({"hips.side": 0.0, "hips.fwd": 0.0, "hips.up": 0.0})
for _s in SIDES:
    DEFAULTS.update({
        f"clav.{_s}.raise": 0.0, f"clav.{_s}.fwd": 0.0,
        f"arm.{_s}.el": -76.0, f"arm.{_s}.az": 8.0, f"arm.{_s}.tw": 0.0,
        f"fore.{_s}.bend": 14.0, f"fore.{_s}.tw": 0.0,
        f"hand.{_s}.flex": 6.0, f"hand.{_s}.dev": 0.0,
        f"wpn.{_s}.x": 0.0, f"wpn.{_s}.y": 0.0, f"wpn.{_s}.z": 0.0,
        f"armik.{_s}": 0.0, f"armik.{_s}.grip": -0.13, f"armik.{_s}.rot": 0.0, f"armik.{_s}.pole": 0.0,
        f"hik.{_s}": 0.0, f"hik.{_s}.x": 0.0, f"hik.{_s}.fwd": 0.0, f"hik.{_s}.z": 1.15,
        f"hik.{_s}.r": 0.43, f"hik.{_s}.az": 35.0, f"hik.{_s}.rollfree": 0.0, f"hik.{_s}.rollauto": 1.0,
        f"hik.{_s}.yaw": 0.0, f"hik.{_s}.pitch": 0.0, f"hik.{_s}.roll": 0.0, f"hik.{_s}.pole": 0.0,
        f"legik.{_s}": 1.0,
        f"foot.{_s}.out": 0.115, f"foot.{_s}.fwd": 0.0, f"foot.{_s}.up": 0.0, f"foot.{_s}.yaw": 7.0,
        f"foot.{_s}.heel": 0.0, f"foot.{_s}.toe": 0.0, f"toe.{_s}.bend": 0.0, f"knee.{_s}.out": 4.0,
        f"thigh.{_s}.flex": 0.0, f"thigh.{_s}.abd": 0.0, f"thigh.{_s}.tw": 0.0,
        f"shin.{_s}.knee": 0.0, f"foot.{_s}.point": 0.0,
    })
CHANNELS = sorted(DEFAULTS)


def P(*bases, **kw):
    """Build a pose dict: merge base dicts left to right, then keyword overrides.
    Keyword names use '_' for '.', e.g. arm_L_el=-30 -> 'arm.L.el'."""
    out = {}
    for b in bases:
        out.update(b)
    for k, v in kw.items():
        out[k.replace("_", ".")] = v
    return out


def mirror_pose(p):
    """Swap L/R channels (for mirrored moves). Center yaw/roll/side values are negated."""
    out = {}
    for k, v in p.items():
        if ".L." in k or k.endswith(".L"):
            out[k.replace(".L", ".R")] = v
        elif ".R." in k or k.endswith(".R"):
            out[k.replace(".R", ".L")] = v
        elif k.endswith(".yaw") or k.endswith(".roll") or k == "hips.side":
            out[k] = -v
        else:
            out[k] = v
    return out


# ----------------------------------------------------------------------------------------------
class Rig:
    """Numpy model of one character's skeleton (rest data) used for evaluation and measurement."""

    def __init__(self, props):
        self.p = props
        self.warm = None            # dict side -> (swivel, roll) while evaluating an animation sequentially
        self.J = joints(props)
        self.R0 = rest_frames(self.J)
        self.h = {b: self.J[b][0] for b in BONE_ORDER}
        self.k = props["hip_h"] / STD["hip_h"]      # leg scale: targets/hips offsets scale with it
        arm_len = props["upper_len"] + props["fore_len"] + props["grip_x"]
        self.arm_ratio = arm_len / (STD["upper_len"] + STD["fore_len"] + STD["grip_x"])
        Js = joints(STD)
        self.sh_std = {s: Js[f"upper_arm.{s}"][0] for s in SIDES}

    # --- semantic rotations (armature axes) -------------------------------------------------
    @staticmethod
    def q_spine(c, b):
        return Rz(c[b + ".yaw"]) @ Rx(c[b + ".pitch"]) @ Ry(c[b + ".roll"])

    @staticmethod
    def side(Q, s):
        return Q if s == "L" else mirror_rot(Q)

    def q_clav(self, c, s):
        return self.side(Rz(-c[f"clav.{s}.fwd"]) @ Ry(-c[f"clav.{s}.raise"]), s)

    def q_upper(self, c, s):
        el = math.radians(c[f"arm.{s}.el"])
        az = math.radians(c[f"arm.{s}.az"])
        d = np.array([math.cos(el) * math.cos(az), -math.cos(el) * math.sin(az), math.sin(el)])
        Q = R_axis(d, c[f"arm.{s}.tw"]) @ min_rot(np.array([1.0, 0, 0]), d)
        return self.side(Q, s)

    def q_fore(self, c, s):
        return self.side(Rz(-c[f"fore.{s}.bend"]) @ Rx(c[f"fore.{s}.tw"]), s)

    def q_hand(self, c, s):
        return self.side(Rz(-c[f"hand.{s}.dev"]) @ Ry(c[f"hand.{s}.flex"]), s)

    def q_wpn(self, c, s):
        return self.side(Rz(c[f"wpn.{s}.z"]) @ Ry(c[f"wpn.{s}.y"]) @ Rx(c[f"wpn.{s}.x"]), s)

    def q_thigh(self, c, s):
        return self.side(Rz(c[f"thigh.{s}.tw"]) @ Ry(-c[f"thigh.{s}.abd"]) @ Rx(-c[f"thigh.{s}.flex"]), s)

    # --- evaluation ---------------------------------------------------------------------------
    def evaluate(self, c):
        """c: full channel dict. Returns (Q dict bone->3x3 in armature axes, hips translation, D dict)."""
        h = self.h
        k = self.k
        self.dbg = {}
        Q = {b: np.eye(3) for b in BONE_ORDER}
        D = {}
        D["root"] = Xf()
        t_hips = k * np.array([c["hips.side"], -c["hips.fwd"], c["hips.up"]])
        Q["hips"] = self.q_spine(c, "hips")
        D["hips"] = D["root"] @ Xf.trans(t_hips) @ Xf.rot_about(Q["hips"], h["hips"])
        for b in ("spine", "chest", "neck", "head"):
            Q[b] = self.q_spine(c, b)
            D[b] = D[PARENT[b]] @ Xf.rot_about(Q[b], h[b])

        # arms: FK side first, then IK side
        order = sorted(SIDES, key=lambda s: c[f"armik.{s}"] > c[f"hik.{s}"])
        for s in order:
            self._arm(c, s, Q, D)
        for s in SIDES:
            self._leg(c, s, Q, D)
        return Q, t_hips, D

    def _chain(self, Q, D, names):
        for b in names:
            D[b] = D[PARENT[b]] @ Xf.rot_about(Q[b], self.h[b])

    def _arm(self, c, s, Q, D):
        h = self.h
        cl, up, fo, ha, wp = (f"shoulder.{s}", f"upper_arm.{s}", f"forearm.{s}", f"hand.{s}", f"weapon.{s}")
        Q[cl] = self.q_clav(c, s)
        D[cl] = D["chest"] @ Xf.rot_about(Q[cl], h[cl])
        fk = {up: self.q_upper(c, s), fo: self.q_fore(c, s), ha: self.q_hand(c, s)}
        wh = c[f"hik.{s}"]
        wa = c[f"armik.{s}"]
        w = max(wh, wa)
        if w <= 1e-4:
            Q.update(fk)
        else:
            Y = np.array([0, 1.0, 0])
            if wh >= wa:
                Pt, _ = self.hand_target(c, s, D)
                r_auth = c[f"hik.{s}.roll"]
                span = 90.0 * min(max(c[f"hik.{s}.rollfree"], 0.0), 1.0)
                pole = c[f"hik.{s}.pole"]

                def Wfn(r, c=c, s=s, D=D):
                    return self.hand_target(c, s, D, roll=r)[1]
            else:
                o = OTHER[s]
                wo = f"weapon.{o}"
                Wf = D[wo].R @ self.R0[wo]
                Pw = D[wo].apply(h[wo])
                Pt = Pw + Wf @ np.array([0, c[f"armik.{s}.grip"] * self.arm_ratio, 0])
                r_auth = c[f"armik.{s}.rot"]
                span = 80.0
                pole = c[f"armik.{s}.pole"]

                # other hand's socket X is mirrored (knuckle convention): 180 deg about the grip axis
                def Wfn(r, Wf=Wf):
                    return Wf @ R_axis(Y, 180.0 + r)
            phi, r = self._solve_arm(s, D, Pt, Wfn, pole, r_auth, span)
            self._arm_ik(s, Q, D, Pt, Wfn(r), phi)
            self.dbg[f"arm.{s}"] = (Pt, w, "grip" if wa > wh else "hik")
            if w < 0.9999:
                for b in (up, fo, ha):
                    Q[b] = slerp_mat(fk[b], Q[b], w)
        self._chain(Q, D, (up, fo, ha))
        Q[wp] = self.q_wpn(c, s)
        D[wp] = D[ha] @ Xf.rot_about(Q[wp], h[wp])

    def hand_target(self, c, s, D, roll=None):
        """Desired weapon-socket world position and frame from hik.* channels (chest space).

        The knuckle roll is relative to a natural grip: knuckles along the shoulder->hand line (perpendicular to
        the blade), which is where a relaxed wrist puts them. hik.S.roll is an offset from that (deg).
        Targets beyond comfortable reach are pulled in smoothly (the arm extends instead of snapping straight)."""
        sx = SX[s]
        yaw = math.radians(c[f"hik.{s}.yaw"])
        pit = math.radians(c[f"hik.{s}.pitch"])
        d = np.array([math.sin(yaw) * math.cos(pit), -math.cos(yaw) * math.cos(pit), math.sin(pit)])
        e0 = np.array([-math.sin(yaw) * math.sin(pit), math.cos(yaw) * math.sin(pit), math.cos(pit)])
        az = math.radians(c[f"hik.{s}.az"])
        r = c[f"hik.{s}.r"]
        pL = np.array([r * math.sin(az) + c[f"hik.{s}.x"], -(r * math.cos(az) + c[f"hik.{s}.fwd"]), c[f"hik.{s}.z"]])
        shL = self.sh_std["L"]
        v = pL - shL
        # smooth reach limit (standard-rig meters)
        reach = (STD["upper_len"] + STD["fore_len"] + STD["grip_x"]) * 0.98
        Lv = float(np.linalg.norm(v))
        k0 = 0.8 * reach
        if Lv > k0:
            Ln = k0 + (reach - k0) * math.tanh((Lv - k0) / (reach - k0))
            v = v * (Ln / Lv)
            pL = shL + v
        vp = v - d * np.dot(v, d)
        auto = c.get(f"hik.{s}.rollauto", 1.0)
        base = 0.0
        if auto > 0 and np.linalg.norm(vp) > 1e-4:
            vp = vp / np.linalg.norm(vp)
            base = math.degrees(math.atan2(float(np.dot(np.cross(e0, vp), d)), float(np.dot(e0, vp)))) * auto
        e = R_axis(d, base + (c[f"hik.{s}.roll"] if roll is None else roll)) @ e0
        if s == "R":
            d = MIRROR_V * d
            e = MIRROR_V * e
            pL = MIRROR_V * pL
        # e = knuckle / true-edge direction. Socket X = +knuckles on the right hand, -knuckles on the left.
        Y = normalize(d)
        X = normalize(e - Y * np.dot(e, Y)) * (1.0 if s == "R" else -1.0)
        Z = np.cross(X, Y)
        W = np.stack([X, Y, Z], axis=1)
        sh_std = self.sh_std[s]
        p_char = self.h[f"upper_arm.{s}"] + (pL - sh_std) * self.arm_ratio
        return D["chest"].apply(p_char), D["chest"].R @ W

    # ---- arm IK --------------------------------------------------------------------------------------
    def _arm_geom(self, s, D, Pt, Rh, phi):
        h = self.h
        cl, up, fo, ha = (f"shoulder.{s}", f"upper_arm.{s}", f"forearm.{s}", f"hand.{s}")
        sx = SX[s]
        th = Pt - Rh @ h[f"weapon.{s}"]
        wrist = Rh @ h[ha] + th
        shoulder = D[cl].apply(h[up])
        pole0 = D["chest"].R @ normalize(np.array([sx * 0.55, 0.55, -1.0]))
        pole_w = R_axis(wrist - shoulder, sx * phi) @ pole0
        bend_axis = np.array([0, 0, -1.0]) if s == "L" else np.array([0, 0, 1.0])
        Qu, kappa = solve_two_bone(h[up], h[fo], h[ha], bend_axis, np.array([0, 1.0, 0]),
                                   D[cl].inv().apply(wrist), D[cl].R.T @ pole_w)
        Rb = R_axis(bend_axis, kappa)
        Qh = (D[cl].R @ Qu @ Rb).T @ Rh
        return Qu, Rb, Qh

    @staticmethod
    def _twist(Qh, a):
        q = mat_to_quat(Qh)
        tw = 2 * math.degrees(math.atan2(float(np.dot(q[1:], a)), q[0]))
        return (tw + 180) % 360 - 180

    def _wrist_cost(self, s, Qh):
        sx = SX[s]
        a = np.array([sx, 0, 0])
        d = Qh @ a
        dx = max(float(d[0] * sx), 1e-4)
        flex = math.degrees(math.atan2(-d[2], dx))
        dev = math.degrees(math.atan2(-d[1], dx))
        tw = self._twist(Qh, a)
        c = (flex / (70.0 if flex > 0 else 55.0)) ** 2 + (dev / (22.0 if dev > 0 else 32.0)) ** 2
        c += max(abs(0.75 * tw) - 75.0, 0.0) ** 2 / 400.0
        return c

    def _solve_arm(self, s, D, Pt, Wfn, pole, r_auth, span):
        """Choose elbow swivel phi and grip roll r (within r_auth +- span) minimizing wrist strain.
        Warm-started from the previous frame when an animation is evaluated sequentially (self.warm)."""
        cache = {}
        wcache = {}

        def W(r):
            k = round(r, 3)
            if k not in wcache:
                wcache[k] = Wfn(r) @ self.R0[f"weapon.{s}"].T
            return wcache[k]

        def f(phi, r):
            key = (round(phi, 3), round(r, 3))
            if key not in cache:
                _, _, Qh = self._arm_geom(s, D, Pt, W(r), phi)
                v = self._wrist_cost(s, Qh) + ((phi - pole) / 70.0) ** 2
                if span > 0:
                    v += ((r - r_auth) / 75.0) ** 2
                cache[key] = v
            return cache[key]

        def line(g, x, step, lo=-1e9, hi=1e9):
            fx = g(x)
            for _ in range(5):
                a, b = max(x - step, lo), min(x + step, hi)
                fa, fb = g(a), g(b)
                if fa < fx and fa <= fb:
                    x, fx = a, fa
                elif fb < fx:
                    x, fx = b, fb
                else:
                    den = fa - 2 * fx + fb
                    if den > 1e-12 and a < x < b:
                        xm = x + 0.5 * step * (fa - fb) / den
                        xm = min(max(xm, a), b)
                        if g(xm) < fx:
                            x = xm
                    break
            return x

        rlo, rhi = r_auth - span, r_auth + span
        warm = None if self.warm is None else self.warm.get(s)
        if warm is None:
            rs = [r_auth + span * (i / 2.0 - 1.0) for i in range(5)] if span > 0 else [r_auth]
            best = min((f(p, r), p, r) for r in rs for p in [pole + d for d in range(-90, 91, 30)])
            phi, r = best[1], best[2]
            dphi, dr = 15.0, max(span / 4.0, 1.0)
        else:
            phi, r = warm
            r = min(max(r, rlo), rhi)
            dphi, dr = 8.0, 8.0
        for _ in range(3):
            phi = line(lambda p: f(p, r), phi, dphi)
            if span > 0:
                r = line(lambda x: f(phi, x), r, dr, rlo, rhi)
            dphi *= 0.5
            dr *= 0.5
        if self.warm is not None:
            self.warm[s] = (phi, r)
        self.dbg[f"swivel.{s}"] = phi
        self.dbg[f"roll.{s}"] = r
        return phi, r

    def _arm_ik(self, s, Q, D, Pt, Rw, phi):
        h = self.h
        cl, up, fo, ha, wp = (f"shoulder.{s}", f"upper_arm.{s}", f"forearm.{s}", f"hand.{s}", f"weapon.{s}")
        Rh = Rw @ self.R0[wp].T
        Qu, Rb, Qh = self._arm_geom(s, D, Pt, Rh, phi)
        a = np.array([SX[s], 0, 0])
        Q[up] = Qu
        D[up] = D[cl] @ Xf.rot_about(Qu, h[up])
        Q[fo] = Rb @ R_axis(a, 0.75 * self._twist(Qh, a))
        D[fo] = D[up] @ Xf.rot_about(Q[fo], h[fo])
        Q[ha] = D[fo].R.T @ Rh

    def _leg(self, c, s, Q, D):
        h = self.h
        p = self.p
        k = self.k
        th, sh, ft, to = (f"thigh.{s}", f"shin.{s}", f"foot.{s}", f"toe.{s}")
        fk = {th: self.q_thigh(c, s), sh: Rx(c[f"shin.{s}.knee"]), ft: Rx(c[f"foot.{s}.point"]),
              to: Rx(-c[f"toe.{s}.bend"])}
        w = c[f"legik.{s}"]
        if w <= 1e-4:
            Q.update(fk)
        else:
            sx = SX[s]
            A = np.array([sx * k * c[f"foot.{s}.out"], -k * c[f"foot.{s}.fwd"], p["ankle_h"] + k * c[f"foot.{s}.up"]])
            Ryaw = Rz(sx * c[f"foot.{s}.yaw"])
            heel = c[f"foot.{s}.heel"]
            toe = c[f"foot.{s}.toe"]
            if abs(heel) > 1e-6:
                ball = A + Ryaw @ np.array([0, -p["ball_fwd"], p["ball_h"] - p["ankle_h"]])
                A = ball + Ryaw @ Rx(heel) @ Ryaw.T @ (A - ball)
            if abs(toe) > 1e-6:
                hp = A + Ryaw @ Rx(heel) @ np.array([0, p["heel_back"], -p["ankle_h"]])
                A = hp + Ryaw @ Rx(heel) @ Rx(-toe) @ Rx(-heel) @ Ryaw.T @ (A - hp)
            Wfoot = Ryaw @ Rx(heel - toe)
            pole_w = normalize(Ryaw @ Rz(sx * c[f"knee.{s}.out"]) @ np.array([0, -1.0, 0]) +
                               0.35 * (D["hips"].R @ np.array([0, -1.0, 0])))
            self.dbg[f"leg.{s}"] = (A.copy(), w)
            Tp = D["hips"].inv().apply(A)
            Pp = D["hips"].R.T @ pole_w
            Qt, kappa = solve_two_bone(h[th], h[sh], h[ft], np.array([1.0, 0, 0]), np.array([0, -1.0, 0]), Tp, Pp)
            Q[th] = Qt
            Q[sh] = Rx(kappa)
            D[th] = D["hips"] @ Xf.rot_about(Q[th], h[th])
            D[sh] = D[th] @ Xf.rot_about(Q[sh], h[sh])
            Q[ft] = D[sh].R.T @ Wfoot
            Q[to] = Rx(-(heel + c[f"toe.{s}.bend"]))
            if w < 0.9999:
                for b in (th, sh, ft, to):
                    Q[b] = slerp_mat(fk[b], Q[b], w)
        self._chain(Q, D, (th, sh, ft, to))


# ----------------------------------------------------------------------------------------------
class Anim:
    """Keyed or procedural animation spec (frames at 30 fps)."""

    def __init__(self, name, length, loop=False, fn=None, lag=None, layers=None, **meta):
        self.name = name
        self.length = int(length)
        self.loop = loop
        self.fn = fn
        self.keys = []
        self.lag = lag or {}
        self.layers = list(layers or [])   # callables (f, channels) -> None, applied after sampling (additive)
        self.meta = meta          # frames: hits=[(f0,f1)], cancel_after, combo_window, footsteps, release, iframes
        self.wind = None          # (vx, vy) m/s apparent wind for secondary motion (locomotion)
        self._cache = None

    def key(self, f, pose, ease="smooth"):
        full = dict(DEFAULTS)
        full.update(pose)
        self.keys.append((float(f), full, ease))
        self._cache = None
        return self

    def _prep(self):
        keys = sorted(self.keys, key=lambda k: k[0])
        if self.loop:
            assert abs(keys[-1][0] - self.length) < 1e-6, f"{self.name}: loop must end with a key at length"
        times = [k[0] for k in keys]
        cache = {}
        for ch in CHANNELS:
            vals = [k[1][ch] for k in keys]
            eases = []
            for k in keys:
                e = k[2]
                if isinstance(e, dict):
                    ee = e.get("default", "smooth")
                    best = -1
                    for pref, v in e.items():
                        if pref != "default" and ch.startswith(pref) and len(pref) > best:
                            ee, best = v, len(pref)
                    e = ee
                eases.append(e)
            tang = monotone_tangents(times, vals, cyclic=self.loop)
            cache[ch] = (vals, eases, tang)
        self._cache = (times, cache)

    def lag_of(self, ch):
        best, lag = -1, 0.0
        for pref, v in self.lag.items():
            if ch.startswith(pref) and len(pref) > best:
                best, lag = len(pref), v
        return lag

    def channels(self, f):
        if self.fn is not None:
            out = dict(DEFAULTS)
            out.update(self.fn(f))
        else:
            if self._cache is None:
                self._prep()
            times, cache = self._cache
            out = {}
            for ch in CHANNELS:
                vals, eases, tang = cache[ch]
                t = f - self.lag_of(ch)
                if self.loop:
                    t = t % self.length
                out[ch] = sample_channel(times, vals, eases, t, self.loop, tang)
        for layer in self.layers:
            layer(f, out)
        return out

    def add_layer(self, fn):
        self.layers.append(fn)
        return self


# ----------------------------------------------------------------------------------------------
_EVAL_CACHE = {}


def eval_anim(anim, rig):
    """Evaluate every frame (0..length) sequentially with warm-started IK. Loops are evaluated twice so the
    warm state wraps around, and the last frame is the first frame (seamless). Cached per (anim, rig)."""
    key = (anim.name, id(anim), tuple(sorted(rig.p.items())))
    if key in _EVAL_CACHE:
        return _EVAL_CACHE[key]
    n = anim.length + 1
    rig.warm = {}
    out = [None] * n
    passes = 2 if anim.loop else 1
    for p in range(passes):
        for f in range(anim.length if anim.loop else n):
            c = anim.channels(f)
            Q, t, D = rig.evaluate(c)
            out[f] = (c, Q, t, D, dict(rig.dbg))
    if anim.loop:
        out[anim.length] = out[0]
    rig.warm = None
    _EVAL_CACHE[key] = out
    return out


def bake_action(ob, rig, anim, extra=None):
    """Bake anim onto Blender armature object `ob` (pose bones in QUATERNION mode). Returns action.
    extra(anim, frames_data) -> list (per frame) of dict bone -> 3x3 rotation in armature axes for optional
    extra bones (e.g. cape); frames_data = [(channels, Q, hips_t, D), ...]."""
    import bpy
    Rb = {}
    for b in ob.data.bones:
        M = np.array(b.matrix_local)[:3, :3]
        Rb[b.name] = M
    for bn in BONE_ORDER:  # sanity: numpy rest frames == Blender rest frames
        err = np.abs(Rb[bn] - rig.R0[bn]).max()
        assert err < 1e-4, (bn, err)
    n = anim.length + 1
    bone_names = [b.name for b in ob.data.bones]
    quats = {b: np.zeros((n, 4)) for b in bone_names}
    locs = np.zeros((n, 3))
    frames_data = [fr[:4] for fr in eval_anim(anim, rig)]
    ex_all = extra(anim, frames_data) if extra else [{} for _ in range(n)]
    for f, (c, Q, t, D) in enumerate(frames_data):
        ex = ex_all[f]
        for b in bone_names:
            if b in Q:
                Ml = Rb[b].T @ Q[b] @ Rb[b]
            elif b in ex:
                Ml = Rb[b].T @ ex[b] @ Rb[b]
            else:
                Ml = np.eye(3)
            q = mat_to_quat(Ml)
            if f > 0 and np.dot(q, quats[b][f - 1]) < 0:
                q = -q
            quats[b][f] = q
        locs[f] = Rb["hips"].T @ t
    act = bpy.data.actions.get(anim.name)
    if act:
        bpy.data.actions.remove(act)
    act = bpy.data.actions.new(anim.name)
    act.use_fake_user = True
    slot = act.slots.new(id_type="OBJECT", name=ob.name)
    layer = act.layers.new("Layer")
    strip = layer.strips.new(type="KEYFRAME")
    cb = strip.channelbag(slot, ensure=True)
    frames = np.arange(n, dtype=float)

    def put(path, idx, vals, group):
        try:
            fc = cb.fcurves.new(path, index=idx, group_name=group)
        except TypeError:   # Blender 4.4 (bpy module) has no group_name argument
            fc = cb.fcurves.new(path, index=idx)
        fc.keyframe_points.add(n)
        co = np.empty(2 * n)
        co[0::2] = frames
        co[1::2] = vals
        fc.keyframe_points.foreach_set("co", co)
        fc.keyframe_points.foreach_set("interpolation", [1] * n)  # LINEAR
        fc.update()

    for b in bone_names:
        for i in range(4):
            put(f'pose.bones["{b}"].rotation_quaternion', i, quats[b][:, i], b)
    for i in range(3):
        put('pose.bones["hips"].location', i, locs[:, i], "hips")
    act.use_frame_range = True
    act.frame_start = 0
    act.frame_end = anim.length
    act.use_cyclic = bool(anim.loop)
    return act


def assign_action(ob, act):
    if ob.animation_data is None:
        ob.animation_data_create()
    ob.animation_data.action = act
    if ob.animation_data.action_slot is None and len(act.slots):
        ob.animation_data.action_slot = act.slots[0]
