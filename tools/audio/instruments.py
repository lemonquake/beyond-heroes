"""Synthesized instruments + a small song/sequencer framework for the music loops.

Every instrument returns a mono float array (note + its natural release tail) at 44.1 kHz.
"""
from __future__ import annotations

import numpy as np

from kit import bellnote, burst, metal, nz, thump, wood_knock
from synth import (N, SR, TAU, VOWELS, circ, compress, convolve, env_ad, env_swell, filt,
                   fold_loop, hp, limiter, lp, lufs, make_ir, mtof, pan, pink, place, saw, sine,
                   square, tvec, tvf, undb, white, _full, sat, bp)


# --------------------------------------------------------------------------------------------
# plucked strings: Karplus-Strong (block-vectorized), tuned exactly via internal resampling
# --------------------------------------------------------------------------------------------
def karplus(r, f, dur, t60=2.5, bright=0.5, pos=0.18, taps=None):
    """y[n] = g * sum_k h[k] y[n-Nd-k]  with h = [.5,.5] (bright) or [.25,.5,.25] (warm).
    Computed one period per numpy block; exact tuning via internal sample rate + resampling."""
    from scipy.signal import lfilter
    h = np.array([0.5, 0.5]) if (taps or (2 if f >= 300 else 3)) == 2 else np.array([0.25, 0.5, 0.25])
    delay_frac = (len(h) - 1) / 2.0
    Nd = int(np.ceil(SR / f - delay_frac))
    sr_int = f * (Nd + delay_frac)
    total = int(dur * sr_int) + Nd + 4
    y = np.zeros(total)
    exc = r.uniform(-1, 1, Nd)
    fc = min(f * (3 + 14 * bright), 9000.0)
    a = np.exp(-TAU * fc / sr_int)
    exc = lfilter([1 - a], [1, -a], exc)
    exc = exc - np.roll(exc, max(1, int(Nd * pos)))  # pluck-position comb
    exc -= exc.mean()
    y[:Nd] = exc
    g = 10 ** (-3.0 / (f * t60))
    ypad = np.concatenate([np.zeros(len(h)), y])  # ypad[i + len(h)] == y[i]
    o = len(h)
    k = Nd
    while k < total:
        e = min(k + Nd, total)
        m = e - k
        acc = np.zeros(m)
        for j, hj in enumerate(h):
            s0 = k - Nd - j + o
            acc += hj * ypad[s0:s0 + m]
        ypad[k + o:e + o] = g * acc
        k = e
    y = ypad[o:]
    n_out = N(dur)
    src = np.arange(n_out) * (sr_int / SR)
    return np.interp(src, np.arange(total), y)


def lute(r, f, dur, vel=0.8, t60=None, bright=0.45):
    t60 = t60 or float(np.clip(3.2 * (220 / f) ** 0.5, 0.8, 5.0))
    d = max(dur + 0.4, min(t60, 4.0))
    x = karplus(r, f, d, t60, bright * (0.6 + 0.5 * vel), 0.17)
    x = filt(x, "peak", 220, 1.2, 4.0)  # wooden body
    x = filt(x, "peak", 480, 1.5, 2.5)
    x = lp(x, 5500)
    n = len(x)
    rel = np.clip((d - tvec(n)) / 0.08, 0, 1)
    damp = np.where(tvec(n) > dur + 0.25, np.exp(-(tvec(n) - dur - 0.25) / 0.12), 1.0)
    return nz(x * rel * damp) * vel


def harp(r, f, dur, vel=0.8):
    t60 = float(np.clip(4.0 * (330 / f) ** 0.4, 1.2, 6.0))
    x = karplus(r, f, min(t60, 5.0), t60, 0.3 + 0.3 * vel, 0.5)
    x = lp(x, 7000)
    n = len(x)
    return nz(x * np.clip((n / SR - tvec(n)) / 0.1, 0, 1)) * vel


def pizz(r, f, dur, vel=0.8):
    x = karplus(r, f, 0.6, 0.35, 0.25, 0.3)
    return nz(lp(x, 3000)) * vel


# --------------------------------------------------------------------------------------------
# bowed / sustained
# --------------------------------------------------------------------------------------------
def strings(r, f, dur, vel=0.7, attack=0.25, release=0.6, bright=0.5, voices=5, detune=9.0,
            vib=0.004, block=64):
    d = dur + release
    n = N(d)
    t = tvec(n)
    a = np.clip(t / max(attack, 1e-3), 0, 1)
    a = a * a * (3 - 2 * a)
    rl = np.clip((d - t) / release, 0, 1)
    e = a * rl
    vd = np.clip((t - 0.3) / 0.6, 0, 1) * vib
    x = np.zeros(n)
    for k in range(voices):
        c = (k - (voices - 1) / 2) / max((voices - 1) / 2, 1) * detune
        fk = f * 2 ** (c / 1200) * (1 + vd * np.sin(TAU * r.uniform(4.8, 6.0) * t + r.uniform(0, TAU)))
        x += saw(fk, n, r.random())
    fc = np.minimum(f * (1.5 + 5.0 * bright * (0.4 + 0.6 * vel) * e) + 300, 14000)
    x = tvf(x, "lp", fc, 0.7, block=block)
    x = filt(x, "peak", 2500, 1.0, -3.0)
    return nz(x) * e * vel


def spiccato(r, f, dur, vel=0.8, bright=0.8):
    d = max(dur, 0.08)
    x = strings(r, f, d * 0.6, vel, attack=0.008, release=0.09, bright=bright, voices=3, detune=7, vib=0.0,
                block=16)
    n = len(x)
    bite = nz(hp(white(n, r), 2000)) * env_ad(n, 0.0005, 0.03) * 0.25
    return (x + bite * vel)


def cello(r, f, dur, vel=0.7, attack=0.2, release=0.5):
    return strings(r, f, dur, vel, attack, release, bright=0.35, voices=3, detune=5, vib=0.005, block=128)


def pad(r, f, dur, vel=0.6, attack=1.2, release=2.0, bright=0.25):
    return strings(r, f, dur, vel, attack, release, bright=bright, voices=5, detune=12, vib=0.002, block=256)


def brassn(r, f, dur, vel=0.8, swell=0.06, release=0.18, bright=1.0, growl=0.1):
    d = dur + release
    n = N(d)
    t = tvec(n)
    a = np.clip(t / swell, 0, 1) ** 1.5
    rl = np.clip((d - t) / release, 0, 1)
    e = a * rl
    fs = f * (1 - 0.02 * np.exp(-t / 0.03))  # lip scoop
    x = saw(fs * 2 ** (5 / 1200), n) + saw(fs * 2 ** (-5 / 1200), n) + 0.6 * square(fs, n, 0.42)
    x = x * (1 + growl * sine(fs * 0.5, n))
    fc = np.minimum(f * (1.2 + 7.0 * bright * vel * e) + 150, 12000)
    x = tvf(x, "lp", fc, 1.1, block=32)
    return sat(nz(x) * e, 1.4) * vel


def flute(r, f, dur, vel=0.7):
    rel = 0.15
    d = dur + rel
    n = N(d)
    t = tvec(n)
    a = np.clip(t / 0.07, 0, 1)
    e = a * np.clip((d - t) / rel, 0, 1)
    vib = 1 + 0.005 * np.clip((t - 0.25) / 0.4, 0, 1) * np.sin(TAU * 5.2 * t)
    fs = f * vib * (1 - 0.01 * np.exp(-t / 0.05))
    x = sine(fs, n) + 0.22 * sine(2 * fs, n) + 0.07 * sine(3 * fs, n)
    br = filt(white(n, r), "bp", f * 2, 1.5) * 0.12
    return (nz(x) + br) * e * vel


def choir(r, freqs, dur, vel=0.6, vowel="o", attack=0.8, release=1.5, voices=3):
    """Static-vowel choir (fast): detuned vibrato saw voices -> parallel formant bank."""
    d = dur + release
    n = N(d)
    t = tvec(n)
    src = np.zeros(n)
    for f in np.atleast_1d(freqs):
        for v in range(voices):
            det = 2 ** (r.uniform(-14, 14) / 1200)
            vb = 1 + 0.007 * np.sin(TAU * r.uniform(4.5, 6.0) * t + r.uniform(0, TAU))
            src += saw(f * det * vb, n, r.random())
    src = lp(src, 3500)
    y = np.zeros(n)
    for fr, bw, g in VOWELS[vowel]:
        y += filt(src, "bp", fr, fr / bw) * g
    y += 0.03 * nz(filt(white(n, r), "bp", 2500, 1.0))
    a = np.clip(t / attack, 0, 1)
    e = a * a * (3 - 2 * a) * np.clip((d - t) / release, 0, 1)
    return nz(y) * e * vel


def keys(r, f, dur, vel=0.7):
    """Dark felt-piano-like tone: slightly inharmonic additive partials + soft hammer."""
    t60 = float(np.clip(5.0 * (262 / f) ** 0.6, 1.5, 9.0))
    d = min(max(dur + 0.3, 1.0), t60)
    n = N(d)
    t = tvec(n)
    B = 0.0003
    y = np.zeros(n)
    for k in range(1, 12):
        fk = k * f * np.sqrt(1 + B * k * k)
        if fk > 12000:
            break
        amp = (1 / k ** 1.3) * (0.6 + 0.4 * vel) ** (k / 3)
        y += amp * sine(fk, n, r.random()) * env_ad(n, 0.002, t60 / k ** 0.7)
    ham = nz(lp(white(N(0.02), r), 2500)) * env_ad(N(0.02), 0.0005, 0.01) * 0.1
    y[:len(ham)] += ham
    y *= np.clip((d - t) / 0.2, 0, 1)
    return nz(lp(y, 5000)) * vel


def bell(r, f, dur, vel=0.6, t60=3.0):
    return bellnote(r, f, max(dur, t60), t60, 0.8) * vel


def sub(r, f, dur, vel=0.6, attack=0.5, release=1.0):
    d = dur + release
    n = N(d)
    t = tvec(n)
    e = np.clip(t / attack, 0, 1) * np.clip((d - t) / release, 0, 1)
    x = sine(f, n) + 0.25 * lp(saw(f, n), f * 3)
    return nz(x) * e * vel


# --------------------------------------------------------------------------------------------
# percussion
# --------------------------------------------------------------------------------------------
def taiko(r, vel=1.0, pitch=1.0):
    y = thump(r, 95 * pitch, 46 * pitch, 0.9, 0.03, 0.55, 1.6)
    skin = burst(r, 0.12, 120, 1500, 0.08)
    slap = burst(r, 0.02, 1000, 5000, 0.015)
    n = max(len(y), len(skin))
    out = np.zeros(n)
    out[:len(y)] += y
    out[:len(skin)] += 0.45 * skin
    out[:len(slap)] += 0.15 * slap
    return sat(nz(out), 1.3) * vel


def tom(r, vel=0.8, pitch=1.0):
    y = thump(r, 170 * pitch, 95 * pitch, 0.45, 0.025, 0.3, 1.3)
    skin = burst(r, 0.07, 200, 2500, 0.05)
    out = y.copy()
    out[:len(skin)] += 0.35 * skin
    return nz(out) * vel


def snare(r, vel=0.8):
    n = N(0.3)
    tone = sine(np.linspace(210, 180, n), n) * env_ad(n, 0.0005, 0.09)
    nzs = nz(filt(hp(white(n, r), 900), "peak", 4000, 0.8, 4.0)) * env_ad(n, 0.0005, 0.18)
    return nz(0.6 * tone + nzs) * vel


def frame_drum(r, vel=0.6):
    y = thump(r, 130, 85, 0.5, 0.03, 0.35, 1.0)
    jn = nz(bp(white(N(0.15), r), 3000, 0.8)) * env_ad(N(0.15), 0.001, 0.1)
    y[:len(jn)] += 0.2 * jn
    return nz(lp(y, 4000)) * vel


def shaker(r, vel=0.4):
    n = N(0.07)
    return nz(hp(white(n, r), 6000)) * env_swell(n, 0.35, 1.5, 2.0) * vel


def tick(r, vel=0.4, f=2400.0):
    return wood_knock(r, f, 10, 0.05) * vel


def anvil(r, vel=0.5, f=900.0):
    return metal(r, f, 1.2, 0.7, 9, 5, 0.6) * vel


def boom(r, vel=1.0):
    y = thump(r, 65, 24, 2.5, 0.08, 2.0, 2.2)
    b = burst(r, 0.6, 40, 400, 0.5, src="pink")
    y[:len(b)] += 0.4 * b
    return nz(y) * vel


def cymbal(r, dur=2.5, vel=0.5):
    n = N(dur)
    x = hp(white(n, r), 4000, order=2)
    ring = metal(r, 420, dur, dur * 0.8, 14, 12, 0.3)
    return nz(x * env_ad(n, 0.001, dur) + 0.5 * ring * np.linspace(1, 0, n)) * vel


def swell_cym(r, dur=1.5, vel=0.5):
    return cymbal(r, dur, vel)[::-1].copy()


def heartbeat(r, vel=0.7):
    a = thump(r, 60, 38, 0.35, 0.03, 0.25, 1.2)
    b = thump(r, 55, 36, 0.35, 0.03, 0.25, 1.2) * 0.7
    out = np.zeros(N(0.6))
    place(out, a, 0)
    place(out, b, N(0.19))
    return nz(lp(out, 400)) * vel


# --------------------------------------------------------------------------------------------
# song framework
# --------------------------------------------------------------------------------------------
STEM_STATS: dict = {}


class Bus:
    def __init__(self, n, gain, send, eq):
        self.buf = np.zeros((n, 2))
        self.gain, self.send, self.eq = gain, send, eq


class Song:
    def __init__(self, r, bpm, bars, meter=4, tail=12.0):
        self.r = r
        self.bpm, self.bars, self.meter = bpm, bars, meter
        self.spb = 60.0 / bpm
        self.length = bars * meter * self.spb
        self.L = N(self.length)
        self.n = self.L + N(tail)
        self.buses: dict[str, Bus] = {}

    def bus(self, name, gain=1.0, send=0.25, eq=None):
        self.buses[name] = Bus(self.n, gain, send, eq)

    def t(self, bar, beat=0.0):
        return (bar * self.meter + beat) * self.spb

    def beats(self, b):
        return b * self.spb

    def add(self, bus, x, time, gain=1.0, pan_=0.0, humanize=0.006):
        time = time + (self.r.uniform(-humanize, humanize) if humanize else 0.0)
        s = pan(x, pan_) if x.ndim == 1 else x
        # anything starting before 0 or past the loop end wraps around the loop
        pos = int(round(time * SR)) % self.L
        place(self.buses[bus].buf, s, pos, gain)

    def render(self, ir, target_lufs=-14.0, ceiling_db=-1.0):
        dry = np.zeros((self.L, 2))
        send = np.zeros((self.L, 2))
        STEM_STATS.clear()
        for name, b in self.buses.items():
            x = fold_loop(b.buf, self.L)
            if b.eq is not None:
                x = circ(b.eq, x, N(2.0))
            dry += x * b.gain
            send += x * b.gain * b.send
            STEM_STATS[name] = 20 * np.log10(np.sqrt(np.mean((x * b.gain) ** 2)) + 1e-12)
        wet = fold_loop(convolve(send, ir), self.L)
        y = dry + wet
        y = compress(y, thresh_db=-20.0, ratio=2.0, window=0.08, circular=True)
        y = y * undb(target_lufs - lufs(y))
        y = limiter(y, undb(ceiling_db - 0.1), 0.004, circular=True)
        return y


def chord_tones(root_midi, quality):
    iv = {"m": [0, 3, 7], "M": [0, 4, 7], "d": [0, 3, 6], "7": [0, 4, 7, 10], "m7": [0, 3, 7, 10],
          "sus4": [0, 5, 7], "sus2": [0, 2, 7]}[quality]
    return [root_midi + i for i in iv]


NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
        "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def parse_chord(sym):
    """'Dm' 'Bb' 'A7' 'Bdim' 'Esus4' -> (root pitch class, quality)."""
    root = sym[:2] if len(sym) > 1 and sym[1] in "#b" else sym[:1]
    rest = sym[len(root):]
    q = {"": "M", "m": "m", "dim": "d", "7": "7", "m7": "m7", "sus4": "sus4", "sus2": "sus2"}[rest]
    return NOTE[root], q


def voicing(sym, low=48, spread=True):
    """Close-ish voicing with the root at or above `low` (midi)."""
    pc, q = parse_chord(sym)
    root = low + ((pc - low) % 12)
    tones = chord_tones(root, q)
    if spread and len(tones) == 3:
        tones = [tones[0], tones[2], tones[1] + 12]  # open voicing r-5-10
    return tones


def bass_of(sym, low=36):
    pc, _ = parse_chord(sym)
    return low + ((pc - low) % 12)


def nm(s):
    """'D5' / 'C#4' / 'Bb3' -> midi."""
    name = s[:-1]
    octv = int(s[-1])
    return 12 * (octv + 1) + NOTE[name]


def song_ir(kind):
    cfg = {"menu": dict(rt60=3.2, seed=201, damp=(7000.0, 1300.0), predelay=0.035),
           "town": dict(rt60=2.0, seed=202, damp=(8000.0, 1800.0), predelay=0.02),
           "dungeon": dict(rt60=4.5, seed=203, damp=(5000.0, 900.0), predelay=0.045),
           "boss": dict(rt60=2.4, seed=204, damp=(7000.0, 1500.0), predelay=0.02)}[kind]
    return make_ir(stereo=True, **cfg)
