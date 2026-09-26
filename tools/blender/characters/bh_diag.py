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


def refine_hits(P, windows, frac=0.3, min_frames=3):
    """For each authored strike window (f0, f1) (frames), find the contiguous run of frames around the tip-speed peak
    where the tip moves at >= frac * peak: that is the visible sweep through the contact arc. The window spans from
    the frame where that fast motion starts to the frame where it ends, widened symmetrically (toward the faster
    neighbour) to at least `min_frames` frames so a 60 Hz game loop always samples it. Returns [(t0, t1)] seconds."""
    v = tip_speed(P)
    n = len(v)
    out = []
    for (f0, f1) in windows:
        i0, i1 = max(int(math.floor(f0)), 1), min(int(math.ceil(f1)) + 1, n - 1)
        seg = v[i0:i1 + 1]
        if len(seg) == 0:
            out.append((round(f0 / FPS, 3), round(f1 / FPS, 3)))
            continue
        pk = i0 + int(np.argmax(seg))
        thr = frac * v[pk]
        a = pk
        while a - 1 >= i0 and v[a - 1] >= thr:
            a -= 1
        b = pk
        while b + 1 <= i1 and v[b + 1] >= thr:
            b += 1
        s0, s1 = a - 1, b          # speed at frame i = motion from i-1 to i
        while s1 - s0 < min_frames:
            left = v[s0] if s0 >= 1 else -1.0
            right = v[s1 + 1] if s1 + 1 < n else -1.0
            if right >= left and s1 + 1 < n:
                s1 += 1
            elif s0 >= 1:
                s0 -= 1
            else:
                break
        out.append([s0, s1])
    for k in range(len(out) - 1):          # multi-hit clips: windows never overlap
        if out[k][1] > out[k + 1][0]:
            m = (out[k][1] + out[k + 1][0]) // 2
            out[k][1], out[k + 1][0] = m, m
    return [(round(a / FPS, 3), round(b / FPS, 3)) for a, b in out]


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
