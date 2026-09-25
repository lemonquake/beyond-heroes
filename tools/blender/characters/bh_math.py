"""Pure numpy math helpers for the Beyond Heroes character pipeline.

Conventions (Blender world / armature space): meters, Z up, character faces -Y, character's
left side is +X. Rotations are 3x3 matrices acting on column vectors. Quaternions are (w, x, y, z).
"""
import math
import numpy as np

DEG = math.pi / 180.0


def Rx(deg):
    a = deg * DEG
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)


def Ry(deg):
    a = deg * DEG
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)


def Rz(deg):
    a = deg * DEG
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)


def R_axis(axis, deg):
    axis = np.asarray(axis, dtype=float)
    n = np.linalg.norm(axis)
    if n < 1e-12:
        return np.eye(3)
    x, y, z = axis / n
    a = deg * DEG
    c, s = math.cos(a), math.sin(a)
    C = 1 - c
    return np.array([
        [c + x * x * C, x * y * C - z * s, x * z * C + y * s],
        [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
        [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


def normalize(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def min_rot(a, b):
    """Minimal rotation matrix taking unit vector a onto unit vector b."""
    a = normalize(a)
    b = normalize(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    s = np.linalg.norm(v)
    if s < 1e-9:
        if c > 0:
            return np.eye(3)
        # 180 deg: pick any perpendicular axis
        p = np.array([0, 0, 1.0]) if abs(a[2]) < 0.9 else np.array([0, 1.0, 0])
        ax = normalize(np.cross(a, p))
        return R_axis(ax, 180)
    return R_axis(v / s, math.degrees(math.atan2(s, c)))


def orth(v, axis):
    """Component of v orthogonal to unit axis, normalized."""
    v = np.asarray(v, float)
    r = v - axis * np.dot(v, axis)
    return normalize(r)


def basis_from(e1, pole):
    e1 = normalize(e1)
    e2 = orth(pole, e1)
    if np.linalg.norm(e2) < 1e-6:
        e2 = orth(np.array([0.0, -1.0, 0.0]) if abs(e1[1]) < 0.9 else np.array([0, 0, 1.0]), e1)
    e3 = np.cross(e1, e2)
    return np.stack([e1, e2, e3], axis=1)


MIRROR = np.diag([-1.0, 1.0, 1.0])


def mirror_rot(R):
    return MIRROR @ R @ MIRROR


def mat_to_quat(M):
    m = M
    t = m[0, 0] + m[1, 1] + m[2, 2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    q = np.array([w, x, y, z])
    return q / np.linalg.norm(q)


def quat_to_mat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def slerp_mat(A, B, t):
    if t <= 0:
        return A
    if t >= 1:
        return B
    qa, qb = mat_to_quat(A), mat_to_quat(B)
    if np.dot(qa, qb) < 0:
        qb = -qb
    d = float(np.clip(np.dot(qa, qb), -1, 1))
    if d > 0.9995:
        q = qa + t * (qb - qa)
    else:
        th = math.acos(d)
        q = (math.sin((1 - t) * th) * qa + math.sin(t * th) * qb) / math.sin(th)
    return quat_to_mat(q / np.linalg.norm(q))


# ----------------------------------------------------------------------------------------------
# Rigid transforms as (R, t): x -> R x + t
class Xf:
    __slots__ = ("R", "t")

    def __init__(self, R=None, t=None):
        self.R = np.eye(3) if R is None else R
        self.t = np.zeros(3) if t is None else np.asarray(t, float)

    def __matmul__(self, o):
        return Xf(self.R @ o.R, self.R @ o.t + self.t)

    def apply(self, p):
        return self.R @ np.asarray(p, float) + self.t

    def inv(self):
        Ri = self.R.T
        return Xf(Ri, -Ri @ self.t)

    @staticmethod
    def rot_about(R, p):
        p = np.asarray(p, float)
        return Xf(R, p - R @ p)

    @staticmethod
    def trans(t):
        return Xf(np.eye(3), t)


# ----------------------------------------------------------------------------------------------
# Interpolation
def monotone_tangents(ts, vs, cyclic=False):
    """Fritsch-Carlson monotone cubic tangents (zero at local extrema -> natural ease)."""
    n = len(ts)
    m = [0.0] * n
    if n < 2:
        return m
    d = [(vs[i + 1] - vs[i]) / (ts[i + 1] - ts[i]) for i in range(n - 1)]
    for i in range(n):
        if 0 < i < n - 1:
            a, b = d[i - 1], d[i]
        elif cyclic and n > 2:
            a, b = d[-1], d[0]
        else:
            m[i] = 0.0
            continue
        if a * b <= 0:
            m[i] = 0.0
        else:
            m[i] = 2 * a * b / (a + b)  # harmonic mean keeps monotonicity
    return m


def hermite(p0, p1, m0, m1, h, u):
    u2, u3 = u * u, u * u * u
    return ((2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u) * h * m0 +
            (-2 * u3 + 3 * u2) * p1 + (u3 - u2) * h * m1)


EASES = {
    "linear": lambda u: u,
    "in": lambda u: u * u,                       # accelerate
    "in3": lambda u: u * u * u,
    "out": lambda u: 1 - (1 - u) ** 2,           # decelerate
    "out3": lambda u: 1 - (1 - u) ** 3,
    "inout": lambda u: u * u * (3 - 2 * u),
    "step": lambda u: 0.0 if u < 1 else 1.0,
}


def sample_channel(times, values, eases, t, cyclic=False, tangents=None):
    """times ascending; eases[i] = ease name for segment i->i+1 ('smooth' = monotone cubic)."""
    n = len(times)
    if n == 1 or t <= times[0]:
        return values[0]
    if t >= times[-1]:
        return values[-1]
    i = 0
    while i < n - 2 and t > times[i + 1]:
        i += 1
    h = times[i + 1] - times[i]
    u = (t - times[i]) / h
    e = eases[i]
    if e == "smooth":
        if tangents is None:
            tangents = monotone_tangents(times, values, cyclic)
        return hermite(values[i], values[i + 1], tangents[i], tangents[i + 1], h, u)
    f = EASES[e](u)
    return values[i] + (values[i + 1] - values[i]) * f


# ----------------------------------------------------------------------------------------------
def solve_two_bone(h0, h1, h2, bend_axis, pole_rest, target, pole):
    """Two-bone IK in the parent's rest space.

    h0,h1,h2: rest positions of root joint, mid joint, end joint (chain must be straight in rest).
    bend_axis: rest-space axis for the mid joint rotation (positive angle = bend).
    pole_rest: rest-space direction the mid joint moves toward (relative to root-end line) when bent.
    target: desired end position (parent rest space). pole: desired mid-joint direction.
    Returns (R_root, bend_deg).
    """
    h0, h1, h2 = (np.asarray(x, float) for x in (h0, h1, h2))
    a = np.linalg.norm(h1 - h0)
    b = np.linalg.norm(h2 - h1)
    v = np.asarray(target, float) - h0
    d = np.linalg.norm(v)
    d = min(max(d, abs(a - b) + 1e-4), a + b - 1e-5)
    cosk = (d * d - a * a - b * b) / (2 * a * b)
    k = math.degrees(math.acos(max(-1.0, min(1.0, cosk))))
    Rb = R_axis(bend_axis, k)
    v_bent = (h1 - h0) + Rb @ (h2 - h1)
    B_rest = basis_from(v_bent, pole_rest)
    B_tgt = basis_from(v if np.linalg.norm(v) > 1e-9 else v_bent, pole)
    return B_tgt @ B_rest.T, k
