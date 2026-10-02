"""bh-023: the hero body's landmarks, shape keys (the creator's sliders) and shader attributes.

All positions are in the conformed rest space (hero_conform): metres, Z up, the hero faces -Y, left = +X.

Shape keys are smooth, landmark-driven displacements, so they extrapolate: the creator drives them past 1.0 for the
silly end of a slider (a nose as long as a forearm) and below 0 for the opposite trait (thin lips, a gaunt face).

Shader attributes on every vertex (read by res://src/actors/hero/hero_skin.gdshader):
  UV2      = rest (x, z) in metres: the face plane the eyes and brows are drawn in, and the rest position for the
             skin patterns and the covered-by-clothing cut-outs
  COLOR.r  = 1 on the front of the head (so the face is not mirrored onto the back of the skull)
  COLOR.g  = rest y, packed as (y + Y_PACK) / (2 * Y_PACK)
"""
import os

import numpy as np

Y_PACK = 0.32

# ---- landmarks -----------------------------------------------------------------------------------------------------
EYE = np.array([0.0335, -0.128, 1.687])          # left eye (mirror x for the right)
BROW_Z = 1.708
NOSE_TIP = np.array([0.0, -0.160, 1.653])
NOSE_BASE = np.array([0.0, -0.122, 1.657])
MOUTH = np.array([0.0, -0.143, 1.616])
MOUTH_HALF = 0.029
CHIN = np.array([0.0, -0.128, 1.577])
EAR = np.array([0.083, -0.040, 1.666])           # where the left ear meets the skull
JAW = np.array([0.062, -0.065, 1.600])
HEAD_JOINT_Z = 1.60
HEAD_TOP = 1.80

LANDMARKS = {
    "eye": EYE, "brow_z": BROW_Z, "nose_tip": NOSE_TIP, "nose_base": NOSE_BASE, "mouth": MOUTH, "mouth_half": MOUTH_HALF,
    "chin": CHIN, "ear": EAR, "jaw": JAW, "head_joint_z": HEAD_JOINT_Z, "head_top": HEAD_TOP,
}


def _fall(V, c, r):
    """Smooth bump: 1 at c, 0 at the ellipsoid of radii r."""
    d = np.linalg.norm((V - np.asarray(c, float)) / np.asarray(r, float), axis=1)
    return (1.0 - np.clip(d, 0.0, 1.0) ** 2) ** 2


def _step(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _mirror(c):
    return np.array([-c[0], c[1], c[2]])


def vertex_normals(V, T):
    n = np.zeros_like(V)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    for k in range(3):
        np.add.at(n, T[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def head_mask(V):
    return _step(1.545, 1.575, V[:, 2]) * (np.abs(V[:, 0]) < 0.14)


def ear_mask(V):
    """(left, right): the outer ears."""
    out = []
    for sx in (1.0, -1.0):
        x = V[:, 0] * sx
        m = _step(0.079, 0.084, x) * _step(1.625, 1.638, V[:, 2]) * (1 - _step(1.70, 1.712, V[:, 2])) \
            * _step(-0.075, -0.06, V[:, 1]) * (1 - _step(0.0, 0.012, V[:, 1])) * (np.abs(V[:, 0]) < 0.14)
        out.append(m)
    return out


def nose_mask(V):
    return _fall(V, (0.0, -0.150, 1.660), (0.027, 0.036, 0.046)) * (1 - _step(-0.124, -0.112, V[:, 1]))


def shape_keys(V, T):
    """-> ordered {name: (n,3) delta}."""
    N = vertex_normals(V, T)
    H = head_mask(V)
    Z = np.zeros_like(V)
    out = {}

    def add(name, d):
        out[name] = d

    # ---- nose
    wn = nose_mask(V) * H
    add("nose_size", wn[:, None] * 0.75 * (V - NOSE_BASE))
    t = np.clip((NOSE_BASE[1] - V[:, 1]) / 0.038, 0.0, 1.2)
    d = Z.copy()
    d[:, 1] = -0.055 * wn * t
    add("nose_long", d)
    d = Z.copy()
    d[:, 0] = wn * 0.8 * V[:, 0]
    add("nose_wide", d)
    wt = _fall(V, NOSE_TIP, (0.022, 0.03, 0.02)) * H
    d = Z.copy()
    d[:, 2] = 0.012 * wt
    d[:, 1] = 0.004 * wt
    add("nose_up", d)
    # ---- ears
    eL, eR = ear_mask(V)
    ds, dp, do = Z.copy(), Z.copy(), Z.copy()
    for m, c, sx in ((eL, EAR, 1.0), (eR, _mirror(EAR), -1.0)):
        ds += m[:, None] * 0.9 * (V - c)
        top = _step(1.668, 1.70, V[:, 2])
        back = _step(-0.05, -0.015, V[:, 1])
        dp += (m * top)[:, None] * np.array([sx * 0.006, 0.010, 0.042]) * (0.5 + 0.5 * back)[:, None]
        do[:, 0] += sx * m * 0.85 * np.clip(V[:, 1] + 0.058, 0.0, 0.06)
        do[:, 1] += -m * 0.25 * np.clip(V[:, 1] + 0.058, 0.0, 0.06)
    add("ears_size", ds)
    add("ears_point", dp)
    add("ears_out", do)
    # ---- mouth
    wl = _fall(V, MOUTH, (0.040, 0.034, 0.018)) * H
    d = Z.copy()
    d[:, 1] = -0.009 * wl
    d[:, 2] = 0.75 * wl * (V[:, 2] - MOUTH[2])
    add("lips_full", d)
    wm = _fall(V, MOUTH, (0.058, 0.045, 0.028)) * H
    d = Z.copy()
    d[:, 0] = 0.55 * wm * V[:, 0]
    add("mouth_wide", d)
    d = Z.copy()
    for sx in (1.0, -1.0):
        wc = _fall(V, (sx * MOUTH_HALF, -0.134, MOUTH[2]), (0.024, 0.03, 0.022)) * H
        d += wc[:, None] * np.array([sx * 0.004, 0.002, 0.011])
    add("mouth_smile", d)
    # ---- jaw, chin, cheeks, brow, eyes
    d = Z.copy()
    for sx in (1.0, -1.0):
        c = JAW if sx > 0 else _mirror(JAW)
        wj = _fall(V, c, (0.06, 0.10, 0.06)) * H
        d[:, 0] += sx * 0.013 * wj
    add("jaw_wide", d)
    wc = _fall(V, CHIN, (0.05, 0.055, 0.034)) * H
    add("chin_long", wc[:, None] * np.array([0.0, -0.007, -0.022]))
    d = Z.copy()
    for sx in (1.0, -1.0):
        wk = _fall(V, (sx * 0.052, -0.112, 1.645), (0.042, 0.05, 0.042)) * H
        d += wk[:, None] * np.array([sx * 0.009, -0.009, 0.0])
    add("cheeks", d)
    wb = _fall(V, (0.0, -0.138, BROW_Z), (0.068, 0.034, 0.014)) * H
    add("brow_heavy", wb[:, None] * np.array([0.0, -0.011, -0.002]))
    d = Z.copy()
    for sx in (1.0, -1.0):
        c = EYE if sx > 0 else _mirror(EYE)
        we = _fall(V, c, (0.024, 0.034, 0.016)) * H
        d[:, 1] -= 0.014 * we
    add("eyes_pop", d)
    # ---- body (every mask is smooth: a hard edge would open a crease where the arms meet the trunk)
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    ax = np.abs(x)
    body = (1 - H) * (1 - _step(0.70, 0.74, ax)) * _step(0.07, 0.12, z)     # not the head, the fists or the feet
    torso = (1 - _step(0.17, 0.27, ax)) * _step(0.76, 0.86, z)
    arm = _step(0.17, 0.27, ax) * _step(1.15, 1.25, z)
    upper = arm * (1 - _step(0.42, 0.52, ax))
    fore = arm * _step(0.44, 0.52, ax)
    leg = (1 - _step(0.84, 0.94, z)) * (1 - _step(0.24, 0.3, ax))
    thigh = leg * _step(0.48, 0.60, z)
    calf = leg * (1 - _step(0.44, 0.54, z)) * _step(0.12, 0.2, z)
    chest = torso * _step(1.18, 1.30, z) * (1 - _step(1.42, 1.52, z)) * (1 - _step(-0.02, 0.05, y))
    delt = _fall(V, (0.19, 0.0, 1.45), (0.13, 0.14, 0.13)) + _fall(V, (-0.19, 0.0, 1.45), (0.13, 0.14, 0.13))
    back = torso * _step(1.12, 1.26, z) * (1 - _step(1.42, 1.52, z)) * _step(-0.02, 0.05, y)
    m = np.clip(upper * (0.7 + 0.5 * np.sin(np.clip((ax - 0.2) / 0.27, 0, 1) * np.pi)) + fore * 0.45 + thigh * 0.6 + calf * 0.4
                + chest * 0.75 + delt * 0.8 + back * 0.4, 0.0, 1.5) * body
    add("muscle", N * (0.022 * m)[:, None])
    wbel = _fall(V, (0.0, -0.09, 1.10), (0.21, 0.19, 0.24)) * torso * (1 - _step(0.03, 0.09, y))
    d = Z.copy()
    d[:, 0] = 0.32 * wbel * x
    d[:, 1] = -0.10 * wbel
    d[:, 2] = -0.015 * wbel
    add("belly", d)
    # overall build: thicker (or, negative, thinner) trunk and limbs
    wt = torso * (1 - _step(1.44, 1.56, z))
    d = Z.copy()
    d[:, 0] = 0.16 * wt * x
    d[:, 1] = 0.20 * wt * y
    limb = np.clip(arm + leg * _step(0.1, 0.16, z), 0.0, 1.0)
    d += N * (0.014 * limb * (1 - wt))[:, None]
    neck = _step(1.46, 1.50, z) * (1 - _step(1.57, 1.62, z)) * (1 - _step(0.08, 0.12, ax))
    d += N * (0.010 * neck * (1 - wt))[:, None]
    add("build", d * np.maximum(body, neck)[:, None])
    d = Z.copy()
    for sx in (1.0, -1.0):
        wg = _fall(V, (sx * 0.075, 0.095, 0.94), (0.11, 0.1, 0.12)) * _step(0.78, 0.84, z) * _step(-0.01, 0.04, y)
        d[:, 1] += 0.045 * wg
        d[:, 0] += sx * 0.008 * wg
    add("rear", d)
    fd = female_delta(V)
    if fd is not None:
        # bh-031: her body is fitted from models/female_generic.obj (hero_female.py); the face is the hero's own (the
        # shader draws the eyes and brows at fixed landmarks), softened with the face keys
        for k, c in FEMALE_FACE.items():
            fd = fd + c * out[k]
        add("female", fd)
    return out


FEMALE_DELTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "female_delta.npz")
FEMALE_FACE = {"jaw_wide": -0.55, "brow_heavy": -0.7, "chin_long": -0.15, "nose_size": -0.25, "nose_wide": -0.2,
               "lips_full": 0.45, "cheeks": 0.25}


def female_delta(V):
    """The fitted female displacement for these vertices (nearest stored vertex when the body was rebuilt)."""
    if not os.path.exists(FEMALE_DELTA):
        return None
    d = np.load(FEMALE_DELTA)
    V0, D0 = d["V"].astype(float), d["delta"].astype(float)
    if V0.shape == V.shape and np.abs(V0 - V).max() < 1e-4:
        return D0
    out = np.zeros_like(V)
    for i in range(0, len(V), 512):
        q = V[i:i + 512]
        j = np.argmin(((q[:, None, :] - V0[None, :, :]) ** 2).sum(-1), 1)
        out[i:i + 512] = D0[j]
    print("[hero] female delta re-mapped by nearest vertex (%d -> %d): refit with hero_female.py" % (len(V0), len(V)))
    return out


BODY_KEYS = ("muscle", "belly", "build", "rear", "female")      # the keys clothing must follow
FACE_KEYS = ("nose_size", "nose_long", "nose_wide", "nose_up", "ears_size", "ears_point", "ears_out", "lips_full",
             "mouth_wide", "mouth_smile", "jaw_wide", "chin_long", "cheeks", "brow_heavy", "eyes_pop")


def shader_attributes(V):
    """-> (uv2 (n,2), color (n,4))."""
    uv2 = np.stack([V[:, 0], V[:, 2]], 1)
    front = head_mask(V) * (1 - _step(-0.085, -0.045, V[:, 1]))
    col = np.zeros((len(V), 4))
    col[:, 0] = front
    col[:, 1] = np.clip((V[:, 1] + Y_PACK) / (2 * Y_PACK), 0.0, 1.0)
    col[:, 3] = 1.0
    return uv2, col
