"""Reusable sound-design building blocks (layers) built on synth.py."""
from __future__ import annotations

import numpy as np

from synth import (N, SR, TAU, additive, bp, brown, env_ad, env_swell, filt, formant, hp, lp,
                   make_ir, mix, pink, place, resonator, reverb, sat, saw, sine, square, tvec,
                   tvf, white, _full)


def nz(x):
    pk = np.max(np.abs(x)) if len(x) else 0.0
    return x / pk if pk > 1e-12 else x


_IR = {}
_IR_CFG = {
    "room": dict(rt60=0.45, seed=11, damp=(8000.0, 2500.0), predelay=0.003, early=10),
    "hall": dict(rt60=1.9, seed=12, damp=(7000.0, 1400.0), predelay=0.018, early=8),
    "cave": dict(rt60=3.2, seed=13, damp=(4500.0, 800.0), predelay=0.035, early=6),
    "plate": dict(rt60=1.3, seed=14, damp=(12000.0, 4000.0), predelay=0.0, early=4),
}


def ir(name, stereo=False):
    key = (name, stereo)
    if key not in _IR:
        _IR[key] = make_ir(stereo=stereo, **_IR_CFG[name])
    return _IR[key]


def verb(x, name="room", wet=0.2):
    return reverb(x, ir(name), wet)


# --------------------------------------------------------------------------------------------
# percussive layers
# --------------------------------------------------------------------------------------------
def thump(r, f0=110.0, f1=45.0, dur=0.3, sweep=0.04, t60=None, drive=1.5, attack=0.0008):
    """Pitched-down sine body hit (kick/impact body)."""
    n = N(dur)
    t = tvec(n)
    f = f1 + (f0 - f1) * np.exp(-t / sweep)
    y = sine(f, n) * env_ad(n, attack, t60 or dur)
    return nz(sat(y, drive)) if drive else nz(y)


def burst(r, dur, lo, hi, t60=None, attack=0.0005, order=2, src="white"):
    """Band-limited noise burst with exponential decay."""
    n = N(dur)
    x = white(n, r) if src == "white" else pink(n, r)
    if lo > 20:
        x = hp(x, lo, order=order)
    if hi < SR / 2.1:
        x = lp(x, hi, order=order)
    return nz(x * env_ad(n, attack, t60 or dur))


def swell_noise(r, dur, lo, hi, peak=0.5, rise=2.0, fall=2.0, src="white"):
    n = N(dur)
    x = white(n, r) if src == "white" else pink(n, r)
    x = lp(hp(x, lo, order=2), hi, order=2)
    return nz(x * env_swell(n, peak, rise, fall))


def click(r, f=3500.0, dur=0.006):
    n = N(dur)
    return nz(hp(white(n, r), f, order=2) * env_ad(n, 0.0002, dur))


def wood_knock(r, f=900.0, q=10.0, dur=0.1):
    n = N(dur)
    ex = white(n, r) * env_ad(n, 0.0002, 0.004)
    y = resonator(ex, f, q) + 0.5 * resonator(ex, f * 2.71, q * 1.3) + 0.35 * resonator(ex, f * 0.63, q)
    return nz(y * env_ad(n, 0.0004, dur))


BAR = [1.0, 2.756, 5.404, 8.933, 13.34]


def metal(r, f0, dur, t60, n_parts=10, spread=7.0, bright=0.6, attack=0.0004, ratios=None,
          beat=0.003):
    """Inharmonic struck-metal partials with slight detuned pairs for shimmer/beating."""
    n = N(dur)
    if ratios is None:
        ratios = np.sort(np.concatenate([[1.0], r.uniform(1.25, spread, n_parts - 1)]))
    y = np.zeros(n)
    for ra in ratios:
        f = f0 * ra
        if f > 17000:
            continue
        amp = (1.0 / ra) ** bright * r.uniform(0.5, 1.0)
        tt = t60 * (1.0 / ra) ** 0.55 * r.uniform(0.7, 1.25)
        det = 1.0 + r.uniform(-beat, beat)
        e = env_ad(n, attack, tt)
        y += amp * (sine(f, n, r.random()) + 0.6 * sine(f * det, n, r.random())) * e
    return nz(y)


def ping(r, f, t60=0.1, ratios=(1.0, 2.41, 4.07), dur=None):
    n = N(dur or t60 * 1.2)
    y = np.zeros(n)
    for i, ra in enumerate(ratios):
        if f * ra < 17000:
            y += sine(f * ra, n, r.random()) * env_ad(n, 0.0003, t60 / (1 + i)) / (1 + i)
    return y


def grains(r, dur, rate, kernel, amp_pow=2.0, start=0.0):
    """Poisson-scheduled grains; `rate` (per second) may be an array/envelope; kernel(r, t)."""
    n = N(dur)
    rate = _full(rate, n)
    out = np.zeros(n)
    p = np.clip(rate / SR, 0, 1)
    idx = np.nonzero(r.random(n) < p)[0]
    for i in idx:
        k = kernel(r, i / SR) * (r.random() ** amp_pow)
        place(out, k, i)
    return out


def pebble(r, t=0.0, lo=1500, hi=5000):
    n = N(r.uniform(0.006, 0.025))
    ex = white(n, r) * env_ad(n, 0.0002, 0.003)
    return nz(resonator(ex, r.uniform(lo, hi), r.uniform(3, 9)) * env_ad(n, 0.0003, n / SR))


def debris(r, dur, rate0=120.0, tau=0.15, lo=1500, hi=5000, amp_pow=2.0):
    n = N(dur)
    rate = rate0 * np.exp(-tvec(n) / tau)
    return nz(grains(r, dur, rate, lambda rr, t: pebble(rr, t, lo, hi), amp_pow))


def crackle(r, n, rate, lo=1200.0, hi=8000.0, amp_pow=3.0):
    """Fire crackle: sparse impulses thickened by a tiny noise kernel, band-limited."""
    rate = _full(rate, n)
    p = np.clip(rate / SR, 0, 1)
    hits = r.random(n) < p
    amps = r.random(n) ** amp_pow * np.where(r.random(n) < 0.5, -1.0, 1.0)
    imp = np.where(hits, amps, 0.0)
    k = white(N(0.0015), r) * np.exp(-np.arange(N(0.0015)) / (0.0004 * SR))
    y = np.convolve(imp, k)[:n]
    return nz(lp(hp(y, lo, order=2), hi))


def flame(r, n, cutoff=600.0, flutter=6.0):
    """Roaring flame body: brown/pink noise, lowpassed, with random amplitude flutter."""
    x = lp(brown(n, r) * 0.6 + pink(n, r) * 0.4, cutoff, order=2)
    am = lp(white(n, r), flutter)
    am = 0.6 + 0.4 * nz(am)
    return nz(x * am)


def sparkle(r, dur, rate, lo=3000, hi=9000, t60=(0.05, 0.25)):
    return grains(r, dur, rate,
                  lambda rr, t: ping(rr, rr.uniform(lo, hi), rr.uniform(*t60), (1.0, 2.76, 5.4)),
                  amp_pow=1.5)


def bubble(r, f, dur):
    n = N(dur)
    t = tvec(n)
    fr = f * (1 + 1.8 * t / dur)
    return sine(fr, n) * env_ad(n, 0.001, dur)


def whoosh(r, dur, f_lo, f_hi, q=1.2, peak=0.55, rise=2.2, fall=1.6, sing=0.0, sing_q=7.0,
           body=0.0, src="white"):
    """Air-displacement whoosh: noise through a band-pass whose centre tracks the swell."""
    n = N(dur)
    e = env_swell(n, peak, rise, fall)
    fc = f_lo + (f_hi - f_lo) * e ** 0.8
    x = white(n, r) if src == "white" else pink(n, r)
    y = nz(tvf(x, "bp", fc, q))
    if sing:
        y = y + sing * nz(tvf(white(n, r), "bp", fc * 1.7, sing_q))
    if body:
        y = y + body * nz(tvf(pink(n, r), "lp", fc * 0.35, 0.9))
    return nz(y * e)


def voice(r, dur, f0, vowels="a", shift=1.0, jitter=0.02, rough=0.0, sub=0.0, breath=0.2,
          vib=(5.5, 0.0), env=None):
    """Formant-filtered glottal source: groans, growls, roars, chant."""
    n = N(dur)
    f = _full(f0, n)
    j = nz(lp(white(n, r), 25.0))
    f = f * (1 + jitter * j) * (1 + vib[1] * np.sin(TAU * vib[0] * tvec(n)))
    src = 0.75 * saw(f, n) + 0.25 * square(f, n, 0.3)
    if rough:
        am = sine(f * 0.5, n, r.random())
        src = src * (1 + rough * am)
    if sub:
        src = src + sub * saw(f * 0.5, n)
    src = lp(src, 5000)
    y = nz(formant(src, vowels, shift))
    if breath:
        y = y + breath * nz(formant(white(n, r), vowels, shift))
    if env is not None:
        y = y * _full(env, n)
    return nz(lp(hp(y, 50), 6500 * min(1.0, shift + 0.2), order=2))


def brass(r, f0, dur, swell=0.08, bright=1.0, rel=0.25, detune=6.0, growl=0.0):
    """Low brass-like: two detuned saws + square, lowpass tracking the amplitude swell."""
    n = N(dur)
    t = tvec(n)
    a = np.clip(t / swell, 0, 1) ** 1.5
    rl = np.clip((dur - t) / rel, 0, 1)
    e = a * rl
    f = _full(f0, n) * (1 + 0.004 * np.sin(TAU * 5.0 * t) * np.clip(t / 0.4, 0, 1))
    x = saw(f * 2 ** (detune / 1200), n) + saw(f * 2 ** (-detune / 1200), n) + 0.5 * square(f, n, 0.4)
    if growl:
        x = x * (1 + growl * sine(f * 0.5, n))
    fc = np.mean(_full(f0, n)) * (1.5 + 7.0 * bright * e)
    y = tvf(x, "lp", np.minimum(fc, 16000), 0.9)
    return nz(y * e)


def choir(r, freqs, dur, vowel="ah", attack=0.25, release=0.5, voices=3, shift=1.0):
    """Ensemble 'aah' pad: several detuned, vibrato'd saw voices per note through formants."""
    n = N(dur)
    t = tvec(n)
    src = np.zeros(n)
    for f in np.atleast_1d(freqs):
        for v in range(voices):
            det = 2 ** (r.uniform(-12, 12) / 1200)
            vib = 1 + 0.006 * np.sin(TAU * r.uniform(4.5, 6.0) * t + r.uniform(0, TAU))
            src += saw(f * det * vib, n, r.random())
    y = nz(formant(lp(src, 4000), vowel, shift)) + 0.08 * nz(formant(white(n, r), vowel, shift))
    e = np.clip(t / attack, 0, 1) ** 2 * np.clip((dur - t) / release, 0, 1)
    return nz(y * e)


def bellnote(r, f, dur, t60=2.0, bright=0.8):
    parts = [(0.5, 0.6, 1.0), (1.0, 1.0, 0.8), (1.19, 0.55, 0.5), (1.5, 0.35, 0.45),
             (2.0, 0.6, 0.4), (2.52, 0.3, 0.3), (2.74, 0.35, 0.25), (3.0, 0.25, 0.2),
             (4.07, 0.2 * bright, 0.12), (5.43, 0.15 * bright, 0.08)]
    n = N(dur)
    y = np.zeros(n)
    for ra, a, d in parts:
        if f * ra < 17000:
            det = 1 + r.uniform(-0.0015, 0.0015)
            y += a * (sine(f * ra, n, r.random()) + 0.5 * sine(f * ra * det, n, r.random())) * \
                env_ad(n, 0.0015, t60 * d)
    return nz(y)


def electric(r, n, base=70.0, gate_rate=90.0, density=0.55):
    """Electrical buzz: jittery saw/square harmonics gated by random on/off segments."""
    t = tvec(n)
    j = nz(lp(white(n, r), 40.0))
    f = base * (1 + 0.25 * j)
    buzz = saw(f, n) + 0.7 * square(f * 2.01, n, 0.2) + 0.5 * saw(f * 3.97, n)
    g = lp(white(n, r), gate_rate)
    g = (nz(g) > (1 - 2 * density)).astype(float)
    g = lp(g, 400.0)
    hiss = hp(white(n, r), 3000)
    y = sat(nz(buzz) * 0.8 + 0.4 * nz(hiss), 3.0) * g
    return nz(hp(y, 150))


def stickslip(r, dur, rate0, rate1, res=((600, 12), (1400, 16)), jitter=0.15, env=None):
    """Creak (hinges, wood, bowstring): irregular impulse train through resonators."""
    n = N(dur)
    rate = np.geomspace(rate0, rate1, n) if rate0 > 0 and rate1 > 0 else np.full(n, rate0)
    rate = rate * (1 + jitter * nz(lp(white(n, r), 8.0)))
    ph = np.cumsum(rate / SR)
    imp = np.zeros(n)
    k = np.nonzero(np.diff(np.floor(ph)) > 0)[0] + 1
    imp[k] = 0.5 + 0.5 * r.random(len(k))
    y = np.zeros(n)
    for f, q in res:
        y += resonator(imp, f, q)
    y = nz(y)
    if env is not None:
        y = y * _full(env, n)
    return nz(y)
