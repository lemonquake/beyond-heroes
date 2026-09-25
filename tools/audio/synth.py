"""Core DSP library for Beyond Heroes procedural audio.

Everything here is deterministic given an explicit numpy Generator. Signals are float64 numpy
arrays: mono = shape (n,), stereo = shape (n, 2). Sample rate is fixed at 44.1 kHz.
"""
from __future__ import annotations

import struct
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.ndimage import maximum_filter1d, uniform_filter1d

SR = 44100
TAU = 2.0 * np.pi


# --------------------------------------------------------------------------------------------
# basics
# --------------------------------------------------------------------------------------------
def N(dur: float) -> int:
    return max(1, int(round(dur * SR)))


def tvec(n: int) -> np.ndarray:
    return np.arange(n) / SR


def rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def undb(d: float) -> float:
    return 10.0 ** (d / 20.0)


def todb(x: float) -> float:
    return 20.0 * np.log10(max(float(x), 1e-12))


def mtof(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=float) - 69.0) / 12.0)


def cents(c):
    return 2.0 ** (np.asarray(c, dtype=float) / 1200.0)


def _full(v, n):
    a = np.asarray(v, dtype=float)
    if a.ndim == 0:
        return np.full(n, float(a))
    if len(a) != n:
        a = np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(a)), a)
    return a


# --------------------------------------------------------------------------------------------
# envelopes
# --------------------------------------------------------------------------------------------
def env_lin(points, n):
    """Piecewise linear envelope from [(t_sec, value), ...]."""
    ts = np.array([p[0] for p in points], float)
    vs = np.array([p[1] for p in points], float)
    return np.interp(tvec(n), ts, vs)


def env_exp(points, n, floor=1e-5):
    """Piecewise exponential envelope (interpolates in log domain)."""
    ts = np.array([p[0] for p in points], float)
    vs = np.log(np.maximum(np.array([p[1] for p in points], float), floor))
    e = np.exp(np.interp(tvec(n), ts, vs))
    e[e <= floor * 1.0001] = 0.0
    return e


def env_ad(n, attack=0.002, t60=0.5, hold=0.0, curve=1.0):
    """Attack (smooth raised-sine) then exponential decay reaching -60 dB after t60 seconds."""
    t = tvec(n)
    a = np.ones(n) if attack <= 0 else np.sin(0.5 * np.pi * np.clip(t / attack, 0, 1)) ** 2
    td = np.clip(t - attack - hold, 0, None)
    d = 10.0 ** (-3.0 * (td / max(t60, 1e-4)) ** curve)
    return a * d


def env_adsr(n, a, d, s, r, gate):
    """Classic ADSR; `gate` in seconds (note length), release follows the gate."""
    t = tvec(n)
    e = np.empty(n)
    a = max(a, 1e-4)
    att = t < a
    e[att] = t[att] / a
    dec = (t >= a) & (t < gate)
    e[dec] = s + (1 - s) * np.exp(-(t[dec] - a) / max(d, 1e-4))
    rel = t >= gate
    level_at_gate = s + (1 - s) * np.exp(-(max(gate - a, 0)) / max(d, 1e-4)) if gate > a else min(gate / a, 1)
    e[rel] = level_at_gate * np.exp(-(t[rel] - gate) / max(r / 4.6, 1e-4))
    return e


def env_swell(n, peak=0.5, rise_pow=2.0, fall_pow=2.0):
    """0 -> 1 at `peak` (fraction of length) -> 0 using power curves. Good for whooshes."""
    x = np.linspace(0, 1, n)
    e = np.where(x < peak, (x / max(peak, 1e-6)) ** rise_pow,
                 ((1 - x) / max(1 - peak, 1e-6)) ** fall_pow)
    return e


# --------------------------------------------------------------------------------------------
# oscillators
# --------------------------------------------------------------------------------------------
def phase(freq, n, phase0=0.0):
    f = _full(freq, n)
    inc = f / SR
    ph = np.cumsum(inc) - inc + phase0
    return ph, inc


def sine(freq, n, phase0=0.0):
    ph, _ = phase(freq, n, phase0)
    return np.sin(TAU * ph)


def _polyblep(t, dt):
    y = np.zeros_like(t)
    dt = np.maximum(dt, 1e-9)
    m = t < dt
    x = t[m] / dt[m]
    y[m] = x + x - x * x - 1.0
    m = t > 1.0 - dt
    x = (t[m] - 1.0) / dt[m]
    y[m] = x * x + x + x + 1.0
    return y


def saw(freq, n, phase0=0.0):
    """Band-limited (polyBLEP) sawtooth."""
    ph, dt = phase(freq, n, phase0)
    p = ph % 1.0
    return 2.0 * p - 1.0 - _polyblep(p, dt)


def square(freq, n, pw=0.5, phase0=0.0):
    """Band-limited (polyBLEP) pulse wave; pw may be an array."""
    ph, dt = phase(freq, n, phase0)
    p = ph % 1.0
    pw = _full(pw, n)
    y = np.where(p < pw, 1.0, -1.0)
    y += _polyblep(p, dt)
    y -= _polyblep((p + 1.0 - pw) % 1.0, dt)
    return y


def tri(freq, n, phase0=0.0):
    ph, _ = phase(freq, n, phase0)
    p = (ph + 0.25) % 1.0
    return 4.0 * np.abs(p - 0.5) - 1.0


def fm(fc, ratio, index, n, phase0=0.0):
    """2-operator phase modulation. `index` may be an envelope array."""
    ph, _ = phase(fc, n, phase0)
    idx = _full(index, n)
    return np.sin(TAU * ph + idx * np.sin(TAU * ph * ratio))


def fm3(fc, r1, i1, r2, i2, n):
    """Carrier modulated by a modulator that is itself modulated (stacked FM)."""
    ph, _ = phase(fc, n)
    m2 = _full(i2, n) * np.sin(TAU * ph * r2)
    m1 = _full(i1, n) * np.sin(TAU * ph * r1 + m2)
    return np.sin(TAU * ph + m1)


def additive(f0, partials, n, r: np.random.Generator | None = None, attack=0.001):
    """Sum of sine partials: partials = [(ratio, amp, t60), ...]. f0 may be an array."""
    out = np.zeros(n)
    f0 = _full(f0, n)
    for i, (ratio, amp, t60) in enumerate(partials):
        ph0 = 0.0 if r is None else r.random()
        f = f0 * ratio
        if np.all(f >= SR * 0.48):
            continue
        s = sine(f, n, ph0) * amp * env_ad(n, attack, t60)
        s[f >= SR * 0.48] = 0.0
        out += s
    return out


BELL_PARTIALS = [  # Risset-style bell (ratio, amp, relative decay)
    (0.56, 1.0, 1.0), (0.56 * 1.0018, 0.67, 0.9), (0.92, 1.0, 0.65), (0.92 * 1.0019, 1.8, 0.55),
    (1.19, 2.67, 0.325), (1.70, 1.67, 0.35), (2.00, 1.46, 0.25), (2.74, 1.33, 0.2),
    (3.00, 1.33, 0.15), (3.76, 1.0, 0.1), (4.07, 1.33, 0.075),
]


def bell(freq, n, t60=3.0, bright=1.0, r=None):
    parts = [(ra, a * (bright ** (i / 4)), t60 * d) for i, (ra, a, d) in enumerate(BELL_PARTIALS)]
    y = additive(freq / 0.56 * 0.5, parts, n, r)  # fundamental-ish at `freq`
    return y / 6.0


# --------------------------------------------------------------------------------------------
# noise
# --------------------------------------------------------------------------------------------
def white(n, r):
    return r.standard_normal(n)


def pink(n, r):
    x = r.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = 1.0
    X /= np.sqrt(np.maximum(f, 10.0))
    X[0] = 0
    y = np.fft.irfft(X, n)
    return y / (np.std(y) + 1e-12)


def brown(n, r):
    x = r.standard_normal(n)
    y = signal.lfilter([1.0], [1.0, -0.997], x)
    y = filt(y, "hp", 18.0)
    return y / (np.std(y) + 1e-12)


def impulses(n, r, rate, amp_pow=3.0, jitter=True):
    """Sparse random impulse train (Poisson, `rate` per second). Amplitudes skewed so most are
    small and a few are big (like crackles)."""
    rate = _full(rate, n)
    p = np.clip(rate / SR, 0, 1)
    hits = r.random(n) < p
    amps = r.random(n) ** amp_pow * np.where(r.random(n) < 0.5, -1.0, 1.0)
    return np.where(hits, amps, 0.0)


def grains(n, r, rate, kernel_fn, amp_pow=2.0):
    """Place kernel_fn(r) outputs at Poisson times. rate may be an array (per second)."""
    rate = _full(rate, n)
    out = np.zeros(n)
    p = np.clip(rate / SR, 0, 1)
    idx = np.nonzero(r.random(n) < p)[0]
    for i in idx:
        k = kernel_fn(r) * (r.random() ** amp_pow)
        m = min(len(k), n - i)
        out[i:i + m] += k[:m]
    return out


# --------------------------------------------------------------------------------------------
# filters (RBJ biquads, static and block-time-varying)
# --------------------------------------------------------------------------------------------
def biquad(kind, f, q=0.7071, gain_db=0.0):
    f = float(np.clip(f, 5.0, SR * 0.49))
    w0 = TAU * f / SR
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / (2.0 * max(q, 1e-3))
    A = 10.0 ** (gain_db / 40.0)
    if kind == "lp":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]; a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "hp":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]; a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "bp":  # constant 0 dB peak gain
        b = [alpha, 0.0, -alpha]; a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "notch":
        b = [1.0, -2 * cw, 1.0]; a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "peak":
        b = [1 + alpha * A, -2 * cw, 1 - alpha * A]; a = [1 + alpha / A, -2 * cw, 1 - alpha / A]
    elif kind == "lowshelf":
        sA = 2 * np.sqrt(A) * alpha
        b = [A * ((A + 1) - (A - 1) * cw + sA), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sA)]
        a = [(A + 1) + (A - 1) * cw + sA, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sA]
    elif kind == "highshelf":
        sA = 2 * np.sqrt(A) * alpha
        b = [A * ((A + 1) + (A - 1) * cw + sA), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - sA)]
        a = [(A + 1) - (A - 1) * cw + sA, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - sA]
    else:
        raise ValueError(kind)
    b = np.array(b) / a[0]
    a = np.array(a) / a[0]
    return b, a


def filt(x, kind, f, q=0.7071, gain_db=0.0, order=1):
    """Static biquad along axis 0 (works for mono and stereo). order = cascade count."""
    b, a = biquad(kind, f, q, gain_db)
    y = x
    for _ in range(order):
        y = signal.lfilter(b, a, y, axis=0)
    return y


def lp(x, f, q=0.7071, order=1):
    return filt(x, "lp", f, q, order=order)


def hp(x, f, q=0.7071, order=1):
    return filt(x, "hp", f, q, order=order)


def bp(x, f, q=1.0, order=1):
    return filt(x, "bp", f, q, order=order)


def peq(x, f, gain_db, q=1.0):
    return filt(x, "peak", f, q, gain_db)


def tvf(x, kind, freq, q=0.7071, block=32, gain_db=0.0):
    """Time-varying biquad, coefficients updated every `block` samples. freq/q may be arrays."""
    if x.ndim == 2:
        return np.stack([tvf(x[:, c], kind, freq, q, block, gain_db) for c in range(x.shape[1])], axis=1)
    n = len(x)
    fr = _full(freq, n)
    qq = _full(q, n)
    y = np.empty(n)
    zi = np.zeros(2)
    for i in range(0, n, block):
        j = min(i + block, n)
        m = (i + j) // 2
        b, a = biquad(kind, fr[m], qq[m], gain_db)
        y[i:j], zi = signal.lfilter(b, a, x[i:j], zi=zi)
    return y


def onepole_lp(x, f):
    a = np.exp(-TAU * f / SR)
    return signal.lfilter([1 - a], [1, -a], x, axis=0)


def dc_block(x):
    return filt(x, "hp", 18.0)


def resonator(x, f, q):
    """Resonant bandpass with gain proportional to q (rings)."""
    return filt(x, "bp", f, q) * np.sqrt(q)


# --------------------------------------------------------------------------------------------
# formants (voice-like filtering)
# --------------------------------------------------------------------------------------------
VOWELS = {  # (freq, bandwidth, gain) - adult male-ish
    "a": [(730, 90, 1.0), (1090, 110, 0.50), (2440, 170, 0.22), (3400, 250, 0.08)],
    "o": [(570, 80, 1.0), (840, 100, 0.45), (2410, 170, 0.12), (3300, 250, 0.05)],
    "u": [(300, 70, 1.0), (870, 100, 0.25), (2240, 170, 0.08), (3200, 250, 0.03)],
    "e": [(530, 80, 1.0), (1840, 120, 0.40), (2480, 170, 0.25), (3500, 250, 0.08)],
    "i": [(270, 60, 1.0), (2290, 120, 0.30), (3010, 170, 0.20), (3700, 250, 0.08)],
    "ah": [(650, 100, 1.0), (1080, 120, 0.45), (2650, 200, 0.18), (3500, 250, 0.06)],
}


def formant(x, vowels, shift=1.0, block=64):
    """Parallel formant filter bank. `vowels` is a vowel key, or a list of (t_frac, key) that are
    morphed over time. `shift` scales formant frequencies (bigger creature = lower)."""
    n = len(x)
    if isinstance(vowels, str):
        seq = [(0.0, vowels), (1.0, vowels)]
    else:
        seq = vowels
    ts = np.array([s[0] for s in seq]) * (n - 1)
    out = np.zeros(n)
    idx = np.arange(n)
    shift = _full(shift, n)
    for k in range(4):
        fr = np.interp(idx, ts, [VOWELS[v][k][0] for _, v in seq]) * shift
        bw = np.interp(idx, ts, [VOWELS[v][k][1] for _, v in seq]) * np.sqrt(shift)
        g = np.interp(idx, ts, [VOWELS[v][k][2] for _, v in seq])
        out += tvf(x, "bp", fr, fr / bw, block=block) * g
    return out


# --------------------------------------------------------------------------------------------
# shaping / dynamics
# --------------------------------------------------------------------------------------------
def sat(x, drive=2.0):
    """tanh saturation, level-preserving at peak."""
    pk = np.max(np.abs(x)) + 1e-12
    return np.tanh(drive * x / pk) / np.tanh(drive) * pk


def softclip(x, ceiling=1.0):
    return ceiling * np.tanh(x / ceiling)


def foldback(x, amt=2.0):
    pk = np.max(np.abs(x)) + 1e-12
    return np.sin(0.5 * np.pi * amt * x / pk) * pk


def crush(x, bits=8, hold=1):
    q = 2 ** (bits - 1)
    y = np.round(x * q) / q
    if hold > 1:
        y = np.repeat(y[::hold], hold)[: len(x)]
    return y


def limiter(x, ceiling=0.89, window=0.006, circular=False):
    """Look-ahead peak limiter (non-causal, offline). Guarantees |y| <= ceiling."""
    a = np.abs(x) if x.ndim == 1 else np.max(np.abs(x), axis=1)
    w = max(1, N(window))
    mode = "wrap" if circular else "nearest"
    pk = maximum_filter1d(a, size=2 * w + 1, mode=mode)
    g = np.minimum(1.0, ceiling / np.maximum(pk, 1e-9))
    g = uniform_filter1d(g, size=2 * w + 1, mode=mode)
    y = x * (g if x.ndim == 1 else g[:, None])
    return np.clip(y, -ceiling, ceiling)


def compress(x, thresh_db=-18.0, ratio=3.0, window=0.03, circular=False, makeup_db=0.0):
    """Offline RMS compressor (centered window -> no pumping artifacts from lag)."""
    p = x ** 2 if x.ndim == 1 else np.mean(x ** 2, axis=1)
    mode = "wrap" if circular else "nearest"
    rms = np.sqrt(uniform_filter1d(p, size=max(1, N(window)), mode=mode) + 1e-12)
    lvl = 20 * np.log10(rms)
    over = np.maximum(lvl - thresh_db, 0)
    gdb = -over * (1 - 1 / ratio) + makeup_db
    g = 10 ** (gdb / 20)
    g = uniform_filter1d(g, size=max(1, N(window / 2)), mode=mode)
    return x * (g if x.ndim == 1 else g[:, None])


# --------------------------------------------------------------------------------------------
# time / mixing
# --------------------------------------------------------------------------------------------
def pad(x, n):
    if len(x) >= n:
        return x[:n]
    shape = (n - len(x),) + x.shape[1:]
    return np.concatenate([x, np.zeros(shape)])


def place(buf, x, pos, gain=1.0):
    """Add x into buf at sample pos (clipped at the end)."""
    pos = int(pos)
    if pos >= len(buf):
        return buf
    if pos < 0:
        x = x[-pos:]
        pos = 0
    m = min(len(x), len(buf) - pos)
    if buf.ndim == 2 and x.ndim == 1:
        buf[pos:pos + m] += (x[:m] * gain)[:, None]
    else:
        buf[pos:pos + m] += x[:m] * gain
    return buf


def mix(*layers):
    """layers: (signal, offset_sec, gain) or just signal. Returns mono/stereo sum."""
    norm = []
    for L in layers:
        if isinstance(L, tuple):
            s, off, g = (L + (1.0,))[:3] if len(L) == 2 else L
        else:
            s, off, g = L, 0.0, 1.0
        norm.append((s, N(off) if off > 0 else 0, g))
    n = max(len(s) + o for s, o, _ in norm)
    stereo = any(s.ndim == 2 for s, _, _ in norm)
    buf = np.zeros((n, 2)) if stereo else np.zeros(n)
    for s, o, g in norm:
        place(buf, s, o, g)
    return buf


def resample(x, ratio):
    """Play x at `ratio` speed (ratio>1 -> higher pitch, shorter)."""
    n = len(x)
    m = max(2, int(n / ratio))
    src = np.arange(m) * ratio
    if x.ndim == 1:
        return np.interp(src, np.arange(n), x)
    return np.stack([np.interp(src, np.arange(n), x[:, c]) for c in range(x.shape[1])], axis=1)


def varispeed(x, speed):
    """Time-varying playback speed (array) -> pitch bends."""
    sp = _full(speed, len(x))
    pos = np.cumsum(sp) - sp[0]
    pos = pos[pos < len(x) - 1]
    return np.interp(pos, np.arange(len(x)), x)


def fade(x, fin=0.002, fout=0.01):
    x = x.copy()
    a, b = N(fin) if fin > 0 else 0, N(fout) if fout > 0 else 0
    if a > 0:
        w = np.sin(0.5 * np.pi * np.linspace(0, 1, a)) ** 2
        x[:a] *= w if x.ndim == 1 else w[:, None]
    if b > 0:
        w = np.cos(0.5 * np.pi * np.linspace(0, 1, b)) ** 2
        x[-b:] *= w if x.ndim == 1 else w[:, None]
    return x


def normalize(x, peak_db=-1.0):
    pk = np.max(np.abs(x))
    return x if pk < 1e-12 else x * (undb(peak_db) / pk)


def trim(x, thresh_db=-60.0, keep_pre=0.0):
    a = np.abs(x) if x.ndim == 1 else np.max(np.abs(x), axis=1)
    pk = np.max(a) + 1e-12
    idx = np.nonzero(a > pk * undb(thresh_db))[0]
    if len(idx) == 0:
        return x
    s = max(0, idx[0] - N(keep_pre)) if keep_pre > 0 else idx[0]
    return x[s: idx[-1] + 1]


def pan(x, p):
    """Equal-power pan of mono x; p in [-1, 1] (may be an array)."""
    pp = (_full(p, len(x)) + 1) * 0.25 * np.pi
    return np.stack([x * np.cos(pp), x * np.sin(pp)], axis=1)


# --------------------------------------------------------------------------------------------
# space: reverb, delay, loops
# --------------------------------------------------------------------------------------------
def make_ir(rt60=1.5, seed=1, damp=(9000.0, 1800.0), predelay=0.012, stereo=False, early=8,
            length=None, diffuse_attack=0.02):
    """Synthetic room impulse response: exponentially decaying noise whose lowpass cutoff falls
    over time (air/wall absorption) + a handful of early reflections. Energy-normalized."""
    r = rng(seed)
    n = N(length if length else rt60 * 1.15)
    t = tvec(n)
    env = 10 ** (-3 * t / rt60) * np.clip(t / diffuse_attack, 0, 1) ** 1.5
    cut = np.geomspace(damp[0], damp[1], n)
    chans = []
    for c in range(2 if stereo else 1):
        nz = r.standard_normal(n)
        tail = tvf(nz, "lp", cut, 0.6, block=256) * env
        er = np.zeros(n)
        for _ in range(early):
            p = int(r.uniform(0.003, 0.06) * SR)
            if p < n:
                er[p] += r.uniform(-1, 1) * 2.5 * (1 - p / (0.07 * SR))
        ir = tail + lp(er, damp[0])
        ir = np.concatenate([np.zeros(N(predelay)), ir])
        chans.append(ir)
    ir = np.stack(chans, axis=1) if stereo else chans[0]
    return ir / np.sqrt(np.sum(ir ** 2) / (2 if stereo else 1))


def convolve(x, ir):
    """Mono x with mono IR -> mono; mono x with stereo IR -> stereo; stereo x with stereo IR
    -> stereo (channel-wise)."""
    if ir.ndim == 1 and x.ndim == 1:
        return signal.oaconvolve(x, ir)
    if x.ndim == 1:
        return np.stack([signal.oaconvolve(x, ir[:, c]) for c in range(2)], axis=1)
    if ir.ndim == 1:
        return np.stack([signal.oaconvolve(x[:, c], ir) for c in range(x.shape[1])], axis=1)
    return np.stack([signal.oaconvolve(x[:, c], ir[:, c]) for c in range(2)], axis=1)


def reverb(x, ir, wet=0.3, dry=1.0):
    """Returns dry*x + wet*(x*ir), length extended by the IR tail."""
    w = convolve(x, ir) * wet
    if x.ndim == 1 and w.ndim == 2:
        x = np.stack([x, x], axis=1)
    return mix((x, 0.0, dry), (w, 0.0, 1.0))


def delay(x, time=0.25, feedback=0.4, damp=4000.0, taps=12, gain=0.5):
    """Feedback echo built from repeated, progressively darker taps (offline, vectorized)."""
    d = N(time)
    n = len(x) + d * taps
    out = np.zeros((n,) + x.shape[1:])
    place(out, x, 0)
    y = x
    g = gain
    for k in range(1, taps + 1):
        y = onepole_lp(y, damp)
        place(out, y, d * k, g)
        g *= feedback
        if g < 1e-3:
            break
    return out


def fold_loop(x, L):
    """Wrap everything past sample L back onto the start (circular overlap-add)."""
    out = x[:L].copy()
    for k in range(L, len(x), L):
        chunk = x[k:k + L]
        out[:len(chunk)] += chunk
    return out


def loop_crossfade(x, L, xf):
    """Make a seamless loop of length L from x (len >= L + xf): the material after L is
    equal-power crossfaded into the head, so sample L-1 flows straight into sample 0."""
    assert len(x) >= L + xf
    out = x[:L].copy()
    t = np.linspace(0, 1, xf)
    fi = np.sin(0.5 * np.pi * t)
    fo = np.cos(0.5 * np.pi * t)
    if x.ndim == 2:
        fi, fo = fi[:, None], fo[:, None]
    out[:xf] = x[:xf] * fi + x[L:L + xf] * fo
    return out


def circ(fn, x, padlen):
    """Apply a (causal, stateful) process to a loop as if it had been playing forever: prepend
    the last `padlen` samples, process, keep the last len(x) samples."""
    padlen = min(padlen, len(x))
    y = fn(np.concatenate([x[-padlen:], x]))
    return y[padlen:padlen + len(x)]


def seam_stats(x):
    """Loop-seam discontinuity: jump from last to first sample vs. typical sample-to-sample
    differences inside the file."""
    a = x if x.ndim == 2 else x[:, None]
    d = np.abs(np.diff(a, axis=0))
    jump = np.max(np.abs(a[0] - a[-1]))
    return dict(seam_jump=float(jump), diff_median=float(np.median(d)),
                diff_p99=float(np.percentile(d, 99)), diff_p999=float(np.percentile(d, 99.9)),
                diff_max=float(np.max(d)))


# --------------------------------------------------------------------------------------------
# loudness (ITU-R BS.1770-4 integrated, K-weighted, gated)
# --------------------------------------------------------------------------------------------
def _kweight(x):
    def hs():
        G, Q, fc = 3.99984385397, 0.7071752369554193, 1681.9744509555319
        A = 10 ** (G / 40.0); w0 = TAU * fc / SR; al = np.sin(w0) / (2 * Q); c = np.cos(w0)
        b = [A * ((A + 1) + (A - 1) * c + 2 * np.sqrt(A) * al), -2 * A * ((A - 1) + (A + 1) * c),
             A * ((A + 1) + (A - 1) * c - 2 * np.sqrt(A) * al)]
        a = [(A + 1) - (A - 1) * c + 2 * np.sqrt(A) * al, 2 * ((A - 1) - (A + 1) * c),
             (A + 1) - (A - 1) * c - 2 * np.sqrt(A) * al]
        return np.array(b) / a[0], np.array(a) / a[0]

    def hpf():
        Q, fc = 0.5003270373253953, 38.13547087613982
        w0 = TAU * fc / SR; al = np.sin(w0) / (2 * Q); c = np.cos(w0)
        b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]; a = [1 + al, -2 * c, 1 - al]
        return np.array(b) / a[0], np.array(a) / a[0]

    b, a = hs()
    y = signal.lfilter(b, a, x, axis=0)
    b, a = hpf()
    return signal.lfilter(b, a, y, axis=0)


def lufs(x):
    a = x if x.ndim == 2 else x[:, None]
    y = _kweight(a)
    blk, hop = N(0.4), N(0.1)
    if len(y) < blk:
        z = np.mean(y ** 2, axis=0)[None, :]
    else:
        idx = np.arange(0, len(y) - blk + 1, hop)
        cs = np.concatenate([np.zeros((1, y.shape[1])), np.cumsum(y ** 2, axis=0)])
        z = (cs[idx + blk] - cs[idx]) / blk
    lk = -0.691 + 10 * np.log10(np.sum(z, axis=1) + 1e-20)
    keep = lk > -70
    if not np.any(keep):
        return -70.0
    zz = z[keep]
    rel = -0.691 + 10 * np.log10(np.sum(np.mean(zz, axis=0))) - 10
    keep2 = keep & (lk > rel)
    return float(-0.691 + 10 * np.log10(np.sum(np.mean(z[keep2], axis=0)) + 1e-20))


# --------------------------------------------------------------------------------------------
# WAV I/O (16-bit PCM, optional 'smpl' loop chunk that Godot's importer reads)
# --------------------------------------------------------------------------------------------
def write_wav(path, x, loop=False):
    x = np.asarray(x, dtype=float)
    ch = 1 if x.ndim == 1 else x.shape[1]
    pcm = np.clip(np.round(x * 32767.0), -32768, 32767).astype("<i2")
    data = pcm.tobytes()
    n = len(x)
    chunks = [struct.pack("<4sIHHIIHH", b"fmt ", 16, 1, ch, SR, SR * ch * 2, ch * 2, 16)]
    chunks.append(struct.pack("<4sI", b"data", len(data)) + data + (b"\x00" if len(data) % 2 else b""))
    if loop:
        smpl = struct.pack("<9I", 0, 0, int(1e9 / SR), 60, 0, 0, 0, 1, 0)
        smpl += struct.pack("<6I", 0, 0, 0, n - 1, 0, 0)  # cue id, type fwd, start, end(inclusive), frac, count
        chunks.append(struct.pack("<4sI", b"smpl", len(smpl)) + smpl)
    body = b"WAVE" + b"".join(chunks)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sI", b"RIFF", len(body)) + body)


def read_wav(path):
    """Minimal reader for our own files: returns (float array, sr, loop(start,end) or None)."""
    b = Path(path).read_bytes()
    assert b[:4] == b"RIFF" and b[8:12] == b"WAVE"
    pos, ch, sr, data, loop = 12, 1, SR, None, None
    while pos + 8 <= len(b):
        cid, size = struct.unpack("<4sI", b[pos:pos + 8])
        body = b[pos + 8:pos + 8 + size]
        if cid == b"fmt ":
            _, ch, sr, _, _, bits = struct.unpack("<HHIIHH", body[:16])
            assert bits == 16
        elif cid == b"data":
            data = np.frombuffer(body, dtype="<i2").astype(float) / 32768.0
        elif cid == b"smpl":
            v = struct.unpack("<15I", body[:60])
            loop = (v[11], v[12])
        pos += 8 + size + (size % 2)
    if ch > 1:
        data = data.reshape(-1, ch)
    return data, sr, loop
