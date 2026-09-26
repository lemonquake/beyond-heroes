"""Shared helpers for the library modules: animation construction, breathing / sway layers, timing meta."""
import math

from bh_anim import Anim, DEFAULTS
from lib_poses import PROPS, U

FPS = 30


def anim(name, length, keys, loop=False, props="none", lag=None, layers=None, **meta):
    """keys: [(frame, pose[, ease])]. For loops the last key must be at `length` (it is added automatically as a copy
    of the first key when missing). Meta values are in FRAMES (converted to seconds by bh_library.write_meta)."""
    a = Anim(name, length, loop=loop, lag=lag, layers=layers)
    ks = list(keys)
    if loop and abs(ks[-1][0] - length) > 1e-6:
        ks.append((length, ks[0][1]) + tuple(ks[0][2:]))
    for k in ks:
        a.key(k[0], k[1], k[2] if len(k) > 2 else "smooth")
    a.meta.update(meta)
    a.meta.setdefault("props", PROPS[props] if isinstance(props, str) else props)
    a.meta["family"] = props if isinstance(props, str) else "custom"
    return a


def breath(period, amp=1.0, phase=0.0, hurt=False):
    """Additive breathing: chest lift/expand, shoulders rise, slight head counter motion. `period` in frames
    (must divide the loop length)."""
    def fn(f, c):
        x = math.sin(2 * math.pi * (f / period + phase))
        y = math.sin(2 * math.pi * (f / period + phase) - 0.6)
        c["chest.pitch"] -= 1.6 * amp * x
        c["spine.pitch"] -= 0.6 * amp * x
        c["neck.pitch"] += 1.2 * amp * x
        c["head.pitch"] += 0.6 * amp * y
        c["clav.L.raise"] += 1.8 * amp * x
        c["clav.R.raise"] += 1.8 * amp * x
        c["hips.up"] += 0.002 * amp * x
        if hurt:
            c["chest.pitch"] -= 1.5 * amp * x
            c["clav.L.raise"] += 1.5 * amp * x
            c["clav.R.raise"] += 1.5 * amp * x
    return fn


def sway(period, amp=1.0, phase=0.0):
    """Slow weight shift for idles (hips side-to-side with counter-balance)."""
    def fn(f, c):
        x = math.sin(2 * math.pi * (f / period + phase))
        c["hips.side"] += 0.008 * amp * x
        c["hips.roll"] += 0.8 * amp * x
        c["spine.roll"] -= 0.5 * amp * x
        c["chest.roll"] -= 0.4 * amp * x
        c["head.roll"] -= 0.3 * amp * x
    return fn


def ramp_layer(fn, f0, f1, f2, f3):
    """Apply layer fn with weight ramping 0 -> 1 over [f0, f1] and 1 -> 0 over [f2, f3] (additive blend of deltas)."""
    def out(f, c):
        if f <= f0 or f >= f3:
            return
        w = min((f - f0) / max(f1 - f0, 1e-6), 1.0) if f < f1 else (1.0 - (f - f2) / max(f3 - f2, 1e-6) if f > f2 else 1.0)
        w = w * w * (3 - 2 * w)
        tmp = dict(c)
        fn(f, tmp)
        for k in c:
            c[k] += (tmp[k] - c[k]) * w
    return out


def sec(frames):
    return round(frames / FPS, 3)
