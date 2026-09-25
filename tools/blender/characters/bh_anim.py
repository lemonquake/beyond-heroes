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
                          hik.S.x (outward), hik.S.fwd, hik.S.z = grip position in standard rest coordinates,
                          hik.S.yaw/pitch = blade direction (yaw + = toward own side, pitch + = up),
                          hik.S.roll = rotation of the edge/knuckle side about the blade, hik.S.pole = elbow swivel
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
        f"hik.{_s}": 0.0, f"hik.{_s}.x": 0.25, f"hik.{_s}.fwd": 0.35, f"hik.{_s}.z": 1.15,
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
            if wh >= wa:
                Pt, Wt = self.hand_target(c, s, D)
            else:
                o = OTHER[s]
                wo = f"weapon.{o}"
                Wf = D[wo].R @ self.R0[wo]
                Pw = D[wo].apply(h[wo])
                Pt = Pw + Wf @ np.array([0, c[f"armik.{s}.grip"] * self.arm_ratio, 0])
                Wt = Wf @ R_axis(np.array([0, 1.0, 0]), c[f"armik.{s}.rot"])
                if s == "R" and o == "L":
                    pass
            pole_ang = c[f"hik.{s}.pole"] if wh >= wa else c[f"armik.{s}.pole"]
            self._arm_ik(s, Q, D, Pt, Wt, pole_ang)
            if w < 0.9999:
                for b in (up, fo, ha):
                    Q[b] = slerp_mat(fk[b], Q[b], w)
        self._chain(Q, D, (up, fo, ha))
        Q[wp] = self.q_wpn(c, s)
        D[wp] = D[ha] @ Xf.rot_about(Q[wp], h[wp])

    def hand_target(self, c, s, D):
        """Desired weapon-socket world position and frame from hik.* channels (chest space)."""
        sx = SX[s]
        yaw = math.radians(c[f"hik.{s}.yaw"])
        pit = math.radians(c[f"hik.{s}.pitch"])
        d = np.array([math.sin(yaw) * math.cos(pit), -math.cos(yaw) * math.cos(pit), math.sin(pit)])
        e0 = np.array([-math.sin(yaw) * math.sin(pit), math.cos(yaw) * math.sin(pit), math.cos(pit)])
        e = R_axis(d, c[f"hik.{s}.roll"]) @ e0
        if s == "R":
            d = MIRROR_V * d
            e = MIRROR_V * e
            # R side: knuckle (edge) direction = +e, blade = d
        X = normalize(e)
        Y = normalize(d)
        Z = np.cross(X, Y)
        W = np.stack([X, Y, Z], axis=1)
        p = np.array([sx * c[f"hik.{s}.x"], -c[f"hik.{s}.fwd"], c[f"hik.{s}.z"]])
        sh_std = self.sh_std[s]
        p_char = self.h[f"upper_arm.{s}"] + (p - sh_std) * self.arm_ratio
        return D["chest"].apply(p_char), D["chest"].R @ W

    def _arm_ik(self, s, Q, D, Pt, Wt, pole_ang):
        h = self.h
        cl, up, fo, ha, wp = (f"shoulder.{s}", f"upper_arm.{s}", f"forearm.{s}", f"hand.{s}", f"weapon.{s}")
        Rh = Wt @ self.R0[wp].T                     # desired D_hand rotation
        th = Pt - Rh @ h[wp]
        Dh = Xf(Rh, th)
        wrist = Dh.apply(h[ha])
        sx = SX[s]
        pole_w = D["chest"].R @ normalize(np.array([sx * 0.55, 0.55, -1.0]))
        pole_w = R_axis(wrist - D[cl].apply(h[up]), sx * pole_ang) @ pole_w
        Tp = D[cl].inv().apply(wrist)
        Pp = D[cl].R.T @ pole_w
        bend_axis = np.array([0, 0, -1.0]) if s == "L" else np.array([0, 0, 1.0])
        Qu, kappa = solve_two_bone(h[up], h[fo], h[ha], bend_axis, np.array([0, 1.0, 0]), Tp, Pp)
        Rb = R_axis(bend_axis, kappa)
        Q[up] = Qu
        D[up] = D[cl] @ Xf.rot_about(Qu, h[up])
        D[fo] = D[up] @ Xf.rot_about(Rb, h[fo])
        Qh = D[fo].R.T @ Rh
        a = np.array([sx, 0, 0])
        q = mat_to_quat(Qh)
        tw = 2 * math.degrees(math.atan2(float(np.dot(q[1:], a)), q[0]))
        tw = (tw + 180) % 360 - 180
        Q[fo] = Rb @ R_axis(a, 0.75 * tw)
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

    def __init__(self, name, length, loop=False, fn=None, lag=None, **meta):
        self.name = name
        self.length = int(length)
        self.loop = loop
        self.fn = fn
        self.keys = []
        self.lag = lag or {}
        self.meta = meta          # hits=[(f0,f1)], cancel_after=f, footsteps=[f], release=f, ground_speed=...
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
            full = dict(DEFAULTS)
            full.update(self.fn(f))
            return full
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
        return out


# ----------------------------------------------------------------------------------------------
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
    frames_data = []
    for f in range(n):
        c = anim.channels(f)
        Q, t, D = rig.evaluate(c)
        frames_data.append((c, Q, t, D))
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
        fc = cb.fcurves.new(path, index=idx, group_name=group)
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
