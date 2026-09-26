"""Numpy-only measurement and sanity checks of animations on a rig (no Blender needed).

- foot contact / slide / ground speed measurement for locomotion
- weapon tip trajectories -> hit windows that match the visible sweep
- IK reach errors (feet, hands on grips), wrist over-bend, ground penetration
"""
import math

import numpy as np

from bh_math import mat_to_quat

FPS = 30.0


def eval_frames(anim, rig):
    from bh_anim import eval_anim
    return eval_anim(anim, rig)


def sole_points(rig, s):
    p = rig.p
    hx = p["hip_x"] * (1 if s == "L" else -1)
    return {
        "heel": ("foot." + s, np.array([hx, p["heel_back"], 0.0])),
        "ball": ("foot." + s, np.array([hx, -p["ball_fwd"], 0.0])),
        "tip": ("toe." + s, np.array([hx, -p["ball_fwd"] - p["toe_len"], 0.0])),
    }


def foot_track(frames, rig, s):
    """Per frame: (lowest sole point position, its name, all points)."""
    pts = sole_points(rig, s)
    out = []
    for fr in frames:
        D = fr[3]
        P = {k: D[b].apply(v) for k, (b, v) in pts.items()}
        k = min(P, key=lambda kk: P[kk][2])
        out.append((P[k], k, P))
    return out


def measure_gait(anim, rig, frames=None, contact_h=0.003):
    """Returns dict(speed, slide_cm, per_side...) measured from the evaluated skeleton.
    speed = mean velocity of planted sole points along the motion direction."""
    frames = frames or eval_frames(anim, rig)
    n = anim.length
    res = {}
    vels = []
    slide = 0.0
    u = None
    for s in "LR":
        tr = foot_track(frames, rig, s)
        segs = []
        for f in range(n):
            a, b = tr[f], tr[f + 1]
            # the lowest sole point, if planted in both frames (height ~ 0) -> its velocity
            k = a[1]
            pa, pb = a[2][k], b[2][k]
            if pa[2] < contact_h and pb[2] < contact_h:
                segs.append((f, k, (pb - pa) * FPS))
        res[s] = segs
        for f, k, v in segs:
            vels.append(v[:2])
    if not vels:
        return dict(speed=0.0, slide=0.0, n=0)
    V = np.array(vels)
    mean = V.mean(0)
    speed = float(np.linalg.norm(mean))
    dev = np.linalg.norm(V - mean, axis=1)
    return dict(speed=speed, dir=(-mean / max(speed, 1e-9)).tolist(), slide_rms=float(np.sqrt((dev ** 2).mean())),
                slide_max=float(dev.max()), n=len(vels))


def weapon_tip(frames, rig, side="R", length=0.9):
    wb = "weapon." + side
    h = rig.h[wb]
    y = rig.R0[wb][:, 1]
    return np.array([fr[3][wb].apply(h + y * length) for fr in frames])


def tip_speed(P):
    v = np.zeros(len(P))
    v[1:] = np.linalg.norm(np.diff(P, axis=0), axis=1) * FPS
    v[0] = v[1] if len(v) > 1 else 0
    return v


def refine_hits(P, windows, frac=0.55, pad=0.5):
    """For each authored window (f0, f1), find the contiguous interval around the speed peak inside it where the tip
    speed >= frac * peak. Returns list of (t0, t1) seconds."""
    v = tip_speed(P)
    out = []
    for (f0, f1) in windows:
        i0, i1 = int(math.floor(f0)), int(math.ceil(f1))
        i1 = min(i1, len(v) - 1)
        seg = v[i0:i1 + 1]
        if len(seg) == 0:
            out.append((f0 / FPS, f1 / FPS))
            continue
        pk = i0 + int(np.argmax(seg))
        thr = frac * v[pk]
        a = pk
        while a - 1 >= i0 and v[a - 1] >= thr:
            a -= 1
        b = pk
        while b + 1 <= i1 and v[b + 1] >= thr:
            b += 1
        # velocity at frame i is the motion from i-1 to i
        t0 = max(a - 1 + pad * 0.5, 0) / FPS
        t1 = (b + pad * 0.5) / FPS
        out.append((round(t0, 3), round(t1, 3)))
    return out


def ik_errors(frames, rig):
    """Max distance between IK targets and achieved joints: (feet ankle, hand reach (hik), two-hand grip)."""
    ef, eh, eg = 0.0, 0.0, 0.0
    for c, Q, t, D, dbg in frames:
        for s in "LR":
            if f"leg.{s}" in dbg:
                A, w = dbg[f"leg.{s}"]
                if w > 0.99:
                    ef = max(ef, float(np.linalg.norm(D["foot." + s].apply(rig.h["foot." + s]) - A)))
            if f"arm.{s}" in dbg:
                Pt, w, kind = dbg[f"arm.{s}"]
                if w > 0.99:
                    wb = "weapon." + s
                    e = float(np.linalg.norm(D[wb].apply(rig.h[wb]) - Pt))
                    if kind == "grip":
                        eg = max(eg, e)
                    else:
                        eh = max(eh, e)
    return ef, eh, eg


def wrist_bend(frames):
    """Max non-twist wrist rotation (deg) over the animation, per side."""
    out = {}
    for s in "LR":
        m = 0.0
        a = np.array([1.0 if s == "L" else -1.0, 0, 0])
        for fr in frames:
            Qh = fr[1]["hand." + s]
            q = mat_to_quat(Qh)
            # swing part angle: rotation that moves the hand axis
            d = Qh @ a
            ang = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(d, a))))))
            m = max(m, ang)
        out[s] = m
    return out


def lowest_points(frames, rig):
    """Lowest joint heights (hands, knees, head) to catch ground penetration."""
    names = ["hand.L", "hand.R", "shin.L", "shin.R", "head", "hips", "chest"]
    low = {}
    for nm in names:
        low[nm] = min(float(fr[3][nm].apply(rig.h[nm])[2]) for fr in frames)
    return low
