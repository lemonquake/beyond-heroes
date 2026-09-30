"""bh-023: the generic body conformed to the shared Beyond Heroes skeleton.

The source figure (hero_src) is scaled to 1.80 m and its limbs are carried onto the standard rest pose
(bh_skeleton.joints: exact T-pose, legs straight down at hip_x): every source bone gets an affine map that takes its
own segment onto the matching standard segment (minimal rotation + stretch along the bone), blended with the source
skin weights. The open hands are then curled into fists around the weapon sockets, because every clip in the library
holds its weapon in a closed hand and the rig has no finger bones.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CHARS = os.path.abspath(os.path.join(HERE, "..", "characters"))
for p in (HERE, CHARS):
    if p not in sys.path:
        sys.path.insert(0, p)

import bh_skeleton as S  # noqa: E402

PROPS = S.proportions()
HEIGHT = 1.80
CENTER_Y = 0.030          # source depth that becomes y = 0 (between the torso's middle and the limb joints)


def _rot_between(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1.0 / (1.0 + c))


def _axis_rot(axis, ang):
    axis = axis / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K


def seg_map(a0, a1, b0, b1, stretch=True, extra=None):
    """3x4 affine carrying segment a0->a1 onto b0->b1. extra: a rotation applied after the alignment, about b0."""
    da, db = a1 - a0, b1 - b0
    R = _rot_between(da, db)
    if extra is not None:
        R = extra @ R
    seg_map.last_R = R
    A = R
    if stretch:
        u = da / np.linalg.norm(da)
        k = np.linalg.norm(db) / np.linalg.norm(da)
        A = R @ (np.eye(3) + (k - 1.0) * np.outer(u, u))
    t = b0 - A @ a0
    return np.hstack([A, t[:, None]])


def conform(src):
    """-> (V in the standard rest pose, info dict)."""
    V = src["V"]
    s = HEIGHT / float(V[:, 2].max())
    c0 = np.array([0.0, CENTER_Y, 0.0])

    def P(p):
        return (np.asarray(p, float) - c0) * s

    V0 = P(V)
    Js = {b: (P(h), P(t)) for b, (h, t) in src["joints"].items()}
    J = S.joints(PROPS)
    W = src["W"]
    ident = np.hstack([np.eye(3), np.zeros((3, 1))])
    maps = {b: ident for b in W}
    rots = {b: np.eye(3) for b in src["joints"]}

    def put(name, m):
        maps[name] = m
        rots[name] = seg_map.last_R
    for side, k in (("L", "Left"), ("R", "Right")):
        sh, ua, fa, hd, he = (Js[k + n][0] for n in ("Shoulder", "Arm", "ForeArm", "Hand", "Hand_End"))
        put(k + "Shoulder", seg_map(sh, ua, J["shoulder." + side][0], J["upper_arm." + side][0]))
        put(k + "Arm", seg_map(ua, fa, J["upper_arm." + side][0], J["forearm." + side][0]))
        put(k + "ForeArm", seg_map(fa, hd, J["forearm." + side][0], J["hand." + side][0]))
        # the hand stays rigid; roll it so the flat of the hand is level (palm down, as the weapon sockets assume)
        hw = W[k + "Hand"] + W.get(k + "Hand_End", 0.0)
        pts = V0[hw > 0.9]
        n = np.linalg.svd(pts - pts.mean(0))[2][2]          # the hand's flat normal
        b0, b1 = J["hand." + side][0], J["hand." + side][1]
        R0 = _rot_between(he - hd, b1 - b0)
        n1 = R0 @ n
        ax = (b1 - b0) / np.linalg.norm(b1 - b0)
        n1 = n1 - ax * np.dot(n1, ax)
        roll = math.atan2(float(np.dot(np.cross(n1, (0, 0, 1)), ax)), float(np.dot(n1, (0, 0, 1))))
        if abs(roll) > math.pi / 2:                          # the normal's sign is arbitrary: take the small roll
            roll -= math.copysign(math.pi, roll)
        m = seg_map(hd, he, b0, b1, stretch=False, extra=_axis_rot(ax, roll))
        put(k + "Hand", m)
        rots[k + "Hand_End"] = rots[k + "Hand"]
        if k + "Hand_End" in maps:
            maps[k + "Hand_End"] = m
        ul, ll, ft, tb = (Js[k + n][0] for n in ("UpLeg", "Leg", "Foot", "ToeBase"))
        te = Js[k + "ToeBase"][1]
        hx = J["thigh." + side][0][0]
        knee = J["shin." + side][0]
        hip = np.array([hx, 0.0, ul[2]])
        ank = np.array([hx, 0.0, ft[2]])
        put(k + "UpLeg", seg_map(ul, ll, hip, knee))
        put(k + "Leg", seg_map(ll, ft, knee, ank))
        d = te - ft
        yaw = math.atan2(d[0], -d[1])                       # toes forward (-Y)
        Rz = _axis_rot(np.array([0.0, 0.0, 1.0]), yaw)
        mf = np.hstack([Rz, (ank - Rz @ ft)[:, None]])
        for n in ("Foot", "ToeBase", "Toe_end"):
            rots[k + n] = Rz
            if k + n in maps:
                maps[k + n] = mf
    out = np.zeros_like(V0)
    Vh = np.hstack([V0, np.ones((len(V0), 1))])
    for b, w in W.items():
        out += w[:, None] * (Vh @ maps[b].T)
    out[:, 2] = np.maximum(out[:, 2], 0.0)
    info = dict(scale=s, J=J, P=P, R=rots, Js=Js)
    return out, info


def make_fists(V, W, radius=0.027, drop=0.010, knuckle=0.002):
    """Curl both hands around the weapon sockets. W: source weights (to find the hands)."""
    J = S.joints(PROPS)
    V = V.copy()
    for side, k, sx in (("L", "Left", 1.0), ("R", "Right", -1.0)):
        grip = J["weapon." + side][0]
        hw = W[k + "Hand"] + W.get(k + "Hand_End", 0.0) + W[k + "ForeArm"] * 0.0
        xk = (grip[0] - sx * knuckle) * sx                   # bend starts here (along the arm, mirrored to +x)
        zc = grip[2] - drop
        idx = np.where((hw > 0.5) & (V[:, 0] * sx > xk))[0]
        d = V[idx, 0] * sx - xk
        rad = np.maximum(V[idx, 2] - zc, 0.004)
        a = d / radius
        # beyond a closed curl the fingertips tuck in instead of spiralling through the palm
        a = np.where(a > 3.5, 3.5 + (a - 3.5) * 0.25, a)
        V[idx, 0] = (xk + rad * np.sin(a)) * sx
        V[idx, 2] = zc + rad * np.cos(a)
    return V
