"""Character modeling helpers. Parts are authored in MODEL SPACE (natural standing pose: arms hanging,
legs straight) and converted to the T-pose rest space through the inverse bone transforms."""
import math
import numpy as np

import bh_mesh as M
from bh_math import normalize, R_axis, Rx, Ry, Rz, Xf
from bh_anim import Rig, DEFAULTS, P
from bh_skeleton import joints

MODEL_POSE = P(arm_L_el=-80, arm_L_az=4, fore_L_bend=10, hand_L_flex=0, fore_L_tw=0,
               arm_R_el=-80, arm_R_az=4, fore_R_bend=10, hand_R_flex=0, fore_R_tw=0,
               legik_L=0, legik_R=0)


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


class Body:
    def __init__(self, props, extra_bones=None):
        self.p = props
        self.rig = Rig(props)
        c = dict(DEFAULTS)
        c.update(MODEL_POSE)
        Q, t, D = self.rig.evaluate(c)
        self.D = dict(D)
        self.extra = {}
        for (name, head, tail, parent, zhint) in (extra_bones or []):
            # extra bones do not move in the modeling pose relative to their parent (parents are torso bones)
            self.D[name] = self.D[parent]
            self.extra[name] = (np.array(head, float), np.array(tail, float))
        self.parts = []

    # ---- posed landmarks ------------------------------------------------------------------------
    def rest_head(self, b):
        return self.extra[b][0] if b in self.extra else self.rig.h[b]

    def rest_tail(self, b):
        return self.extra[b][1] if b in self.extra else self.rig.J[b][1]

    def head(self, b):
        return self.D[b].apply(self.rest_head(b))

    def tail(self, b):
        return self.D[b].apply(self.rest_tail(b))

    def axes(self, b):
        """Bone local axes (columns X, Y(along bone), Z) in model space."""
        return self.D[b].R @ self.rig.R0[b]

    def lpt(self, b, pts, origin=None):
        """Bone-local points (x, y along bone, z) -> model space."""
        A = self.axes(b)
        o = self.head(b) if origin is None else np.asarray(origin, float)
        return o + np.asarray(pts, float).reshape(-1, 3) @ A.T

    # ---- adding parts ---------------------------------------------------------------------------
    def add(self, part, bone=None, weights=None):
        """part in model space. bone: rigid. weights: fn(V_model)->list[dict]."""
        if bone is None and weights is None:
            bone = part.bone
        if bone is not None:
            part.V = np.array([self.D[bone].inv().apply(v) for v in part.V]) if len(part.V) else part.V
            part.bone = bone
            part.W = None
        else:
            W = weights(part.V)
            Vr = np.empty_like(part.V)
            for i, (v, w) in enumerate(zip(part.V, W)):
                R = np.zeros((3, 3))
                t = np.zeros(3)
                for b, wt in w.items():
                    R += wt * self.D[b].R
                    t += wt * self.D[b].t
                Vr[i] = np.linalg.solve(R, v - t)
            part.V = Vr
            part.W = W
            part.bone = None
        self.parts.append(part)
        return part

    def add_mirror(self, part, bone=None, weights=None):
        """Add a part authored for the LEFT side and its mirror for the right side."""
        m = part.mirrored(False)
        self.add(part, bone, weights)
        bm = None if bone is None else (bone[:-2] + ".R" if bone.endswith(".L") else bone)
        wm = None
        if weights is not None:
            def wm(V, f=weights):
                Vm = V.copy()
                Vm[:, 0] *= -1
                return [{M.swap_lr(k): v for k, v in d.items()} for d in f(Vm)]
        self.add(m, bm, wm)

    # ---- weight helpers (model space) ------------------------------------------------------------
    def seg_weights(self, bones, power=8.0, top=3):
        segs = [(self.head(b), self.tail(b)) for b in bones]

        def wfn(V):
            D = np.stack([M.seg_dist(V, a, b)[0] for a, b in segs], 1) + 0.01
            W = 1.0 / D ** power
            out = []
            for row in W:
                idx = np.argsort(-row)[:top]
                s = row[idx].sum()
                out.append({bones[i]: float(row[i] / s) for i in idx if row[i] / s > 0.01})
            return out
        return wfn

    def blend2(self, a, b, center, axis, width):
        """Blend between bone a and b along axis across `width` around center (model space)."""
        c = np.asarray(center, float)
        ax = normalize(axis)

        def wfn(V):
            s = smoothstep(-width / 2, width / 2, (V - c) @ ax)
            return [{a: float(1 - x), b: float(x)} if 0 < x < 1 else ({b: 1.0} if x >= 1 else {a: 1.0}) for x in s]
        return wfn

    def skirt_weights(self, z_top, z_bot, max_leg=0.85, shin_from=None, center_w=0.06, upper="hips"):
        """Cloth hanging from the hips: blend hips -> thighs (by side) as it goes down; optionally shins."""
        kz = self.p["knee_h"]

        def wfn(V):
            out = []
            for v in V:
                s = float(smoothstep(z_top, z_bot, v[2])) * max_leg
                side = float(smoothstep(-center_w, center_w, v[0]))
                d = {}
                if 1 - s > 1e-3:
                    d[upper] = 1 - s
                sh = 0.0
                if shin_from is not None:
                    sh = float(smoothstep(shin_from, kz - 0.1, v[2])) * 0.5
                for bn, w in (("L", side), ("R", 1 - side)):
                    if w * s > 1e-3:
                        if sh > 0:
                            d["thigh." + bn] = d.get("thigh." + bn, 0) + w * s * (1 - sh)
                            d["shin." + bn] = w * s * sh
                        else:
                            d["thigh." + bn] = w * s
                tot = sum(d.values())
                out.append({k: x / tot for k, x in d.items()})
            return out
        return wfn

    # ---- geometry generators (model space) -------------------------------------------------------
    def limb(self, b, prof, mat, n=12, p=2.2, front=(0, -1, 0), offs=None, cap0=True, cap1=True):
        """Tube along posed bone b. prof: list of (u, rx, ry) with u along the bone (0 head, 1 tail);
        ry is measured along `front`. offs: optional list of (dx, dy) offsets per ring (dy along front)."""
        h, t = self.head(b), self.tail(b)
        pts = [h + (t - h) * u for u, _, _ in prof]
        pr = [(rx, ry) for _, rx, ry in prof]
        up = np.asarray(front, float)
        V, F = M.tube(pts, pr, n=n, up=up, p=p, cap0=cap0, cap1=cap1,
                      offsets=[(o[0], o[1]) for o in offs] if offs else None)
        return M.Part(V, F, mat, name=b + "_limb")

    def path_tube(self, pts, prof, mat, n=10, p=2.0, up=(0, -1, 0), cap0=True, cap1=True):
        V, F = M.tube(pts, prof, n=n, up=up, p=p, cap0=cap0, cap1=cap1)
        return M.Part(V, F, mat)


# ------------------------------------------------------------------------------------------------
def torso_ring(z, rx, ryf, ryb, keel=0.0, p=2.3, n=24, cx=0.0, cy=0.0, flat_back=0.0):
    """Horizontal torso cross-section. Front is -Y. keel pushes the front center forward."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2  # start at front (-Y)
        c, s = math.cos(a), math.sin(a)
        e = 2.0 / p
        x = rx * np.sign(c) * abs(c) ** e
        if s < 0:
            y = ryf * np.sign(s) * abs(s) ** e
            y *= 1 + keel * max(0.0, 1 - abs(c) * 1.6) ** 2
        else:
            y = ryb * np.sign(s) * abs(s) ** e * (1 - flat_back * (1 - abs(c)))
        pts.append((cx + x, cy + y, z))
    # CCW when seen from above so faces point outward in loft (rings go upward)
    return np.array(pts)


def torso_loft(rows, n=24, p=2.3, cap0=False, cap1=False):
    """rows: list of (z, rx, ryf, ryb, keel[, cy])."""
    rings = []
    for r in rows:
        z, rx, ryf, ryb, keel = r[:5]
        cy = r[5] if len(r) > 5 else 0.0
        rings.append(torso_ring(z, rx, ryf, ryb, keel, p, n, cy=cy))
    return M.loft(rings, cap0, cap1)


def interp_rows(rows, z):
    """Interpolate torso row params at height z."""
    rows = sorted(rows, key=lambda r: r[0])
    if z <= rows[0][0]:
        return rows[0]
    for a, b in zip(rows, rows[1:]):
        if a[0] <= z <= b[0]:
            u = (z - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * u for i in range(len(a)))
    return rows[-1]


def front_y(rows, x, z, p=2.3):
    r = interp_rows(rows, z)
    _, rx, ryf, ryb, keel = r[:5]
    cy = r[5] if len(r) > 5 else 0.0
    ax = min(abs(x) / rx, 0.999)
    # superellipse: (|x|/rx)^p + (|y|/ry)^p = 1  (approximate with the parametrization used in torso_ring)
    yy = ryf * (1 - ax ** p) ** (1 / p)
    c = ax ** (p / 2)
    yy *= 1 + keel * max(0.0, 1 - c * 1.6) ** 2
    return cy - yy


def back_y(rows, x, z, p=2.3):
    r = interp_rows(rows, z)
    _, rx, ryf, ryb, keel = r[:5]
    cy = r[5] if len(r) > 5 else 0.0
    ax = min(abs(x) / rx, 0.999)
    return cy + ryb * (1 - ax ** p) ** (1 / p)


def dome(center, axis, radius, a_max=80.0, n=16, rings=6, scale=(1, 1, 1), up_hint=(0, 0, 1)):
    """Spherical cap around `axis` (outward), opening angle a_max deg. Returns (V, F) open shell."""
    prof = [(radius * math.sin(math.radians(a_max * i / rings)), radius * math.cos(math.radians(a_max * i / rings)))
            for i in range(rings + 1)]
    V, F = M.lathe(prof, n, cap=False)
    V = V * np.asarray(scale, float)
    R = M_align_z(axis, up_hint)
    V = V @ R.T + np.asarray(center, float)
    return V, [tuple(reversed(f)) for f in F]


def M_align_z(axis, up_hint=(0, 0, 1)):
    """Rotation whose +Z maps to axis (and X roughly toward up_hint x axis)."""
    z = normalize(axis)
    x = np.asarray(up_hint, float)
    x = x - z * np.dot(x, z)
    if np.linalg.norm(x) < 1e-6:
        x = np.array([1.0, 0, 0]) - z * z[0]
    x = normalize(x)
    y = np.cross(z, x)
    return np.stack([x, y, z], 1)


def fist(body, side, mat_back, mat_fingers, gauntlet=True, scale=1.0, claw=False):
    """Closed fist around the weapon grip of hand.<side>. Returns list of parts (model space, bone hand.S)."""
    wb = "weapon." + side
    parts = []
    s = scale
    # local frame of weapon socket: X = knuckles (distal), Y = blade/thumb side, Z = back of hand (R) / palm (L)
    A = body.axes(wb)
    o = body.head(wb)
    # socket-local: +Z = back of the hand on both sides; knuckles = +X (right hand) / -X (left hand)
    xs = 1.0 if side == "R" else -1.0
    zsgn = 1.0

    def L(x, y, z):
        return o + A @ np.array([x * xs, y, z]) * s
    # palm/back block
    rings = []
    for x, wy, hz, zc in ((-0.07, 0.03, 0.022, 0.018), (-0.05, 0.042, 0.03, 0.012), (-0.01, 0.046, 0.036, 0.004),
                          (0.02, 0.045, 0.035, 0.0), (0.034, 0.04, 0.028, 0.0)):
        ring = []
        for i in range(10):
            a = 2 * math.pi * i / 10
            yy = wy * np.sign(math.cos(a)) * abs(math.cos(a)) ** 0.7
            zz = zc + hz * np.sign(math.sin(a)) * abs(math.sin(a)) ** 0.7
            ring.append(L(x, yy, zz))
        rings.append(np.array(ring))
    V, F = M.loft(rings)
    parts.append(M.Part(V, F, mat_fingers, name="fist"))
    # knuckle ridge / finger lames
    for k in range(4):
        y = -0.03 + 0.02 * k
        V, F = M.box(0.02, 0.018, 0.02)
        pts = np.array([L(0.03 + 0.003 * (k == 1), y, 0.012) for _ in range(1)])
        prt = M.Part(V, F, mat_back, name="knuckle")
        prt.rot(A).scale(s).move(pts[0])
        parts.append(prt)
    # thumb over the front of the grip
    tp = [L(-0.05, 0.04, 0.0), L(-0.012, 0.05, -0.022), L(0.014, 0.042, -0.034)]
    V, F = M.tube(tp, [(0.012 * s, 0.013 * s)] * 3, n=6, up=A[:, 2])
    parts.append(M.Part(V, F, mat_fingers, name="thumb"))
    if gauntlet:
        # back-of-hand plate
        pts = [L(-0.085, 0.0, 0.034), L(-0.02, 0.0, 0.042), L(0.02, 0.0, 0.038)]
        V, F = M.tube(pts, [(0.05 * s, 0.009 * s), (0.052 * s, 0.009 * s), (0.046 * s, 0.008 * s)], n=8, up=A[:, 2] * zsgn, p=3.0)
        parts.append(M.Part(V, F, mat_back, name="handplate"))
    return parts


def fan_plate(center, normal, up, r, a0, a1, n=8, thick=0.006):
    """Flat fan/wing plate (half-disc-ish) in the plane with normal `normal`."""
    R = M_align_z(normal, up)
    pts = [(0.0, 0.0)]
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((r * math.cos(a), r * math.sin(a)))
    o = np.array(pts)
    V, F = M.prism(o, thick, axis="z")
    V = V @ R.T + np.asarray(center, float)
    return V, F
