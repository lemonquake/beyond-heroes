"""Ambience loops (stereo, 44.1 kHz, 45 s, seamless).

Construction rule that keeps every loop seamless:
  * continuous beds are generated longer than the loop and equal-power crossfaded into the head
    (synth.loop_crossfade) AFTER all their filtering;
  * discrete events are rendered into an oversized buffer and wrapped onto the loop
    (synth.fold_loop), so a tail that runs past the end continues at the start;
  * reverb is applied as circular convolution (convolve + fold); limiter uses wrap mode.
"""
from __future__ import annotations

import zlib

import numpy as np

from kit import (bellnote, burst, choir, click, crackle, flame, metal, nz, ping, thump, voice,
                 wood_knock, stickslip)
from synth import (N, SR, TAU, convolve, env_ad, env_lin, env_swell, filt, fold_loop, formant,
                   hp, limiter, loop_crossfade, lp, lufs, make_ir, mtof, pan, pink, place, saw,
                   sine, square, tvec, tvf, undb, white, brown, bp, _full, VOWELS, sat)

AMB_LEN = 45.0
XF = 3.0
TARGET_LUFS = -20.0
AMBIENCES = ["amb_town", "amb_forest", "amb_catacombs", "amb_temple", "amb_arena"]


def seed_of(name):
    return zlib.crc32(name.encode()) & 0x7FFFFFFF


def slow(r, n, rate):
    """Smooth random curve in [-1, 1] with ~`rate` knots per second (cosine interpolated)."""
    k = int(n / SR * rate) + 3
    knots = r.uniform(-1, 1, k)
    pos = tvec(n) * rate
    i = np.floor(pos).astype(int)
    fr = pos - i
    w = (1 - np.cos(np.pi * fr)) / 2
    return knots[i] * (1 - w) + knots[i + 1] * w


class Loop:
    """Stereo loop builder with dry bus + reverb send, seamless by construction."""

    def __init__(self, r, length=AMB_LEN, xf=XF):
        self.r = r
        self.L = N(length)
        self.xf = N(xf)
        self.n = self.L + self.xf
        self.dry = np.zeros((self.L, 2))
        self.send = np.zeros((self.L, 2))
        self.ev = np.zeros((self.L + N(20.0), 2))
        self.ev_send = np.zeros((self.L + N(20.0), 2))

    def bed(self, x, gain=1.0, send=0.0):
        """x: stereo (n,2) or mono of length >= L+xf; crossfaded into a loop."""
        if x.ndim == 1:
            x = np.stack([x, x], axis=1)
        y = loop_crossfade(x[: self.n], self.L, self.xf)
        self.dry += y * gain
        self.send += y * gain * send

    def event(self, x, t, gain=1.0, pan_=0.0, send=0.0):
        s = pan(x, pan_) if x.ndim == 1 else x
        place(self.ev, s, N(t), gain)
        place(self.ev_send, s, N(t), gain * send)

    def render(self, ir, target=TARGET_LUFS, ceiling_db=-3.0):
        dry = self.dry + fold_loop(self.ev, self.L)
        send = self.send + fold_loop(self.ev_send, self.L)
        wet = fold_loop(convolve(send, ir), self.L)
        y = dry + wet
        y = y * undb(target - lufs(y))
        y = limiter(y, undb(ceiling_db), 0.005, circular=True)
        return y


def stereo_bed(r, n, fn, corr=0.3):
    a, b = fn(r, n), fn(r, n)
    return np.stack([a + corr * b, b + corr * a], axis=1) / (1 + corr)


def wind(r, n, base=400.0, spread=300.0, q=1.2, rate=0.12, gust=0.6):
    fc = base + spread * slow(r, n, rate)
    amp = (1 - gust) + gust * ((slow(r, n, rate * 0.8) + 1) / 2) ** 2
    return nz(tvf(pink(n, r), "bp", fc, q, block=256) * amp)


def whistles(r, n, freqs=(620, 910, 1240), q=22.0, rate=0.07):
    y = np.zeros(n)
    for f in freqs:
        fc = f * (1 + 0.06 * slow(r, n, 0.1))
        amp = np.clip(slow(r, n, rate), 0, 1) ** 2
        y += tvf(pink(n, r), "bp", fc, q, block=256) * amp
    return nz(y)


# --------------------------------------------------------------------------------------------
# event sounds
# --------------------------------------------------------------------------------------------
def chirp_bird(r):
    out = []
    base = r.uniform(2600, 4200)
    for k in range(r.integers(3, 7)):
        d = r.uniform(0.04, 0.09)
        n = N(d)
        f = base * (1 + r.uniform(0.2, 0.6) * np.sin(np.linspace(0, np.pi, n))) * r.uniform(0.9, 1.1)
        s = sine(f * (1 + 0.03 * np.sin(TAU * 60 * tvec(n))), n) * env_swell(n, 0.3, 1.0, 1.5)
        out.append((s, k * r.uniform(0.09, 0.16)))
    buf = np.zeros(N(1.2))
    for s, t in out:
        place(buf, s, N(t))
    return nz(buf)


def crow_caw(r, count=None):
    buf = np.zeros(N(2.2))
    t = 0.0
    for _ in range(count or r.integers(2, 5)):
        d = r.uniform(0.24, 0.36)
        n = N(d)
        f0 = r.uniform(430, 560) * env_lin([(0, 0.85), (d * 0.3, 1.05), (d, 0.8)], n)
        c = voice(r, d, f0, [(0, "a"), (0.6, "a"), (1, "o")], shift=1.7, jitter=0.12, rough=0.9, breath=0.8,
                  env=env_lin([(0, 0), (0.02, 1), (d * 0.6, 0.8), (d, 0)], n))
        place(buf, sat(c, 3.0), N(t))
        t += d + r.uniform(0.12, 0.3)
    return nz(hp(buf, 300))


def owl(r):
    buf = np.zeros(N(2.0))
    for k, (t, f) in enumerate([(0, 390), (0.55, 385), (0.8, 380), (1.25, 360)]):
        d = 0.32 if k != 2 else 0.18
        n = N(d)
        s = sine(f * env_lin([(0, 1.02), (d, 0.96)], n), n) + 0.2 * sine(2 * f, n)
        s = s * env_swell(n, 0.3, 1.2, 1.5) + 0.05 * nz(bp(white(n, r), f, 2)) * env_swell(n, 0.3)
        place(buf, s, N(t))
    return nz(buf)


def drip(r):
    d = 0.05
    n = N(d)
    f = r.uniform(700, 1100) * np.geomspace(1, r.uniform(1.8, 2.6), n)
    s = sine(f, n) * env_ad(n, 0.0005, 0.04)
    sp = hp(white(N(0.02), r), 3000) * env_ad(N(0.02), 0.0003, 0.015) * 0.2
    return nz(np.concatenate([s, np.zeros(N(0.02))])[: n] + np.pad(sp, (0, n - len(sp))))


def church_bell(r, f=196.0, dur=6.0):
    return lp(bellnote(r, f, dur, t60=5.0, bright=0.7), 3500)


def hammer(r):
    buf = np.zeros(N(4.0))
    for k in range(r.integers(3, 6)):
        m = metal(r, r.uniform(1150, 1250), 0.8, 0.5, 8, 5, 0.6)
        place(buf, m, N(k * r.uniform(0.55, 0.7)), 1.0 if k % 2 == 0 else 0.7)
    return nz(lp(buf, 3500))


def creak(r):
    d = r.uniform(1.2, 2.2)
    e = env_swell(N(d), r.uniform(0.3, 0.7), 1.2, 1.2)
    return stickslip(r, d, r.uniform(14, 22), r.uniform(22, 35), res=((170, 7), (410, 9), (880, 12)),
                     jitter=0.35, env=e)


def rumble(r, d=4.0):
    n = N(d)
    return nz(lp(brown(n, r), 90, order=2) * env_swell(n, 0.4, 1.5, 1.5))


def war_drum(r):
    return nz(mix_(thump(r, 85, 48, 0.8, 0.03, 0.6, 1.8), burst(r, 0.12, 60, 800, 0.1)))


def mix_(*xs):
    n = max(len(x) for x in xs)
    y = np.zeros(n)
    for x in xs:
        y[: len(x)] += x
    return y


# --------------------------------------------------------------------------------------------
# ambiences
# --------------------------------------------------------------------------------------------
def amb_town(r):
    lp_ = Loop(r)
    n = lp_.n
    lp_.bed(stereo_bed(r, n, lambda rr, m: wind(rr, m, 350, 200, 0.9, 0.1, 0.5)), 0.5, 0.1)
    fire = np.stack([flame(r, n, 500, 3) * 0.6 + crackle(r, n, 18, 1200, 6000) * 0.5] * 2, axis=1)
    fire = lp(fire, 5000)
    lp_.bed(fire * np.array([0.8, 0.45]), 0.35, 0.15)
    # faint church bells (tolls) and a small chapel bell pair
    for t in (4.0, 7.2, 10.4):
        lp_.event(church_bell(r, 196.0), t, 0.28, -0.3, 0.6)
    for t in (29.0, 29.9):
        lp_.event(church_bell(r, 523.25, 3.0), t, 0.1, 0.5, 0.7)
    # birds
    for t in r.uniform(0, AMB_LEN, 7):
        lp_.event(chirp_bird(r), t, 0.07, r.uniform(-0.9, 0.9), 0.3)
    # distant blacksmith
    for t in (15.0, 37.0):
        lp_.event(hammer(r), t, 0.12, 0.6, 0.5)
    # a crow somewhere
    lp_.event(crow_caw(r, 2), 22.0, 0.08, -0.7, 0.4)
    return lp_.render(ir_("town"))


def amb_forest(r):
    lp_ = Loop(r)
    n = lp_.n
    lp_.bed(stereo_bed(r, n, lambda rr, m: wind(rr, m, 500, 350, 1.0, 0.12, 0.7)), 0.7, 0.1)
    lp_.bed(stereo_bed(r, n, lambda rr, m: whistles(rr, m, (560, 830, 1170), 25, 0.06), 0.1), 0.18, 0.2)
    # dry leaves rustle following gusts
    g = np.clip(slow(r, n, 0.15), 0, 1) ** 2
    rus = np.stack([nz(hp(white(n, r), 2500) * (0.3 + 0.7 * nz(lp(white(n, r), 12)) ** 2) * g) for _ in range(2)], axis=1)
    lp_.bed(rus, 0.12, 0.05)
    for t in (3.0, 19.0, 34.0):
        lp_.event(crow_caw(r), t + r.uniform(-1, 1), 0.3, r.uniform(-0.8, 0.8), 0.45)
    for t in (9.0, 27.0, 40.0):
        lp_.event(creak(r), t, 0.35, r.uniform(-0.6, 0.6), 0.3)
    for t in r.uniform(0, AMB_LEN, 3):
        lp_.event(wood_knock(r, r.uniform(1500, 2500), 5, 0.05), t, 0.1, r.uniform(-1, 1), 0.3)
    lp_.event(owl(r), 13.5, 0.12, 0.7, 0.6)
    return lp_.render(ir_("forest"))


def amb_catacombs(r):
    lp_ = Loop(r)
    n = lp_.n
    t = tvec(n)
    # low drones: beating sines + resonant low noise band + hollow air tone (all loop-periodic
    # material still goes through the crossfade, so nothing has to be phase-exact)
    dr = (sine(41.2, n) + 0.7 * sine(41.6, n) + 0.5 * sine(61.7, n) * (0.6 + 0.4 * slow(r, n, 0.05))
          + 0.3 * sine(82.4, n) * (0.5 + 0.5 * slow(r, n, 0.07)))
    band = tvf(pink(n, r), "bp", 95 + 25 * slow(r, n, 0.05), 3.0, block=512)
    air = tvf(pink(n, r), "bp", 220 * (1 + 0.01 * slow(r, n, 0.1)), 18.0, block=512) * (0.5 + 0.5 * slow(r, n, 0.08))
    lp_.bed(np.stack([nz(dr) + 0.5 * nz(band), nz(dr) + 0.5 * nz(band[::-1])], axis=1), 0.55, 0.2)
    lp_.bed(pan(nz(air), 0.3), 0.12, 0.6)
    # drips: one steady spot + random others
    tt = 0.7
    while tt < AMB_LEN:
        lp_.event(drip(r), tt, 0.35, -0.55, 0.9)
        tt += r.uniform(2.6, 3.4)
    for tt in r.uniform(0, AMB_LEN, 14):
        lp_.event(drip(r), tt, r.uniform(0.1, 0.3), r.uniform(-1, 1), 0.9)
    for tt in (6.0, 24.0, 36.0):
        lp_.event(rumble(r, r.uniform(3.5, 5.0)), tt, 0.5, r.uniform(-0.4, 0.4), 0.4)
    # distant stone scrape and a chain
    lp_.event(lp(nz(tvf(white(N(1.5), r), "bp", np.geomspace(500, 300, N(1.5)), 4.0)) * env_swell(N(1.5), 0.5), 1500),
              15.0, 0.12, 0.8, 0.8)
    ch = np.zeros(N(1.0))
    for k in range(6):
        place(ch, ping(r, r.uniform(1800, 3200), 0.08, (1.0, 2.2, 3.9)), N(k * r.uniform(0.08, 0.15)))
    lp_.event(lp(nz(ch), 3000), 31.0, 0.08, -0.8, 0.9)
    return lp_.render(ir_("catacombs"))


def amb_temple(r):
    lp_ = Loop(r)
    n = lp_.n
    # hollow wind: resonant tube-like partials over a soft broadband wind
    hol = np.zeros(n)
    for k, f in enumerate((110, 165, 220, 330, 440)):
        hol += tvf(pink(n, r), "bp", f * (1 + 0.004 * slow(r, n, 0.1)), 30.0, block=512) * \
            np.clip(0.3 + slow(r, n, 0.06), 0, 1.3) / (1 + 0.4 * k)
    lp_.bed(np.stack([nz(hol), nz(np.roll(hol, N(0.8)))], axis=1), 0.35, 0.8)
    lp_.bed(stereo_bed(r, n, lambda rr, m: wind(rr, m, 300, 150, 0.8, 0.08, 0.6)), 0.4, 0.5)
    # faint choir pad: Dm - Bb - Gm - A, each chord 11.25 s, overlapping so it breathes
    chords = [[50, 57, 62, 65], [46, 53, 58, 62], [43, 50, 55, 58], [45, 52, 57, 61]]
    seg = AMB_LEN / 4
    for i, ch in enumerate(chords):
        c = choir(r, mtof(np.array(ch)), seg + 3.0, "o", attack=3.0, release=3.0, voices=2, shift=0.95)
        lp_.event(c, i * seg, 0.16, 0.3 * (1 if i % 2 else -1), 0.9)
    for t in (8.0, 31.0):
        lp_.event(lp(bellnote(r, mtof(74), 4.0, 3.0, 0.5), 5000), t, 0.05, 0.6, 0.9)
    return lp_.render(ir_("temple"))


def crowd(r, n, voices=12, excite=None):
    """Distant crowd murmur: syllabic voices, each blended between static-vowel formant copies."""
    out = np.zeros((n, 2))
    ex = np.zeros(n) if excite is None else excite
    for v in range(voices):
        f0 = r.uniform(100, 210) * (1 + 0.08 * slow(r, n, 0.5)) * (1 + 0.25 * ex)
        src = 0.6 * saw(f0, n, r.random()) + 0.4 * nz(white(n, r))
        syl = np.clip(slow(r, n, r.uniform(4, 7)) + 0.1 + 0.6 * ex, 0, 1) ** 1.5
        talk = np.clip(slow(r, n, 0.2) + 0.4, 0, 1)
        vs = []
        for vk in ("a", "o", "e"):
            y = np.zeros(n)
            for f, bw, g in VOWELS[vk][:3]:
                y += filt(src, "bp", f, f / bw) * g
            vs.append(y)
        w = np.stack([np.clip(slow(r, n, 3.0) + 0.5, 0, None) for _ in vs])
        w /= w.sum(axis=0) + 1e-9
        y = sum(wk * vk for wk, vk in zip(w, vs)) * syl * talk
        out += pan(nz(y), r.uniform(-0.9, 0.9))
    return out / voices


def amb_arena(r):
    lp_ = Loop(r)
    n = lp_.n
    t = tvec(n)
    # two crowd surges per loop
    ex = np.zeros(n)
    for c in (11.0, 32.0):
        ex += np.exp(-0.5 * ((t - c) / 1.6) ** 2)
    cr = crowd(r, n, 14, ex)
    cr = lp(hp(cr, 150), 2600)
    lp_.bed(cr / np.max(np.abs(cr)), 0.55, 0.5)
    lp_.bed(stereo_bed(r, n, lambda rr, m: wind(rr, m, 450, 250, 0.9, 0.1, 0.5)), 0.25, 0.1)
    for p_ in (-0.7, 0.7):
        f = flame(r, n, 450, 3) * 0.6 + crackle(r, n, 20, 1200, 7000) * 0.5
        lp_.bed(pan(nz(lp(f, 6000)), p_), 0.18, 0.1)
    # distant war drums pattern, twice
    for start in (4.0, 25.0):
        beat = 60 / 72
        for k, acc in enumerate([1, 0.5, 0.7, 0.5, 1, 0.5, 0.8, 0.9]):
            lp_.event(lp(war_drum(r), 1500), start + k * beat, 0.35 * acc, -0.2, 0.7)
    # chains / gate clank
    lp_.event(lp(metal(r, 140, 1.5, 1.0, 10, 7, 0.5), 3000), 18.5, 0.12, 0.5, 0.8)
    return lp_.render(ir_("arena"))


_IRS = {}


def ir_(kind):
    if kind not in _IRS:
        cfg = {"town": dict(rt60=1.6, seed=101, damp=(6000.0, 1200.0), predelay=0.03),
               "forest": dict(rt60=1.2, seed=102, damp=(7000.0, 1500.0), predelay=0.02),
               "catacombs": dict(rt60=4.0, seed=103, damp=(4000.0, 700.0), predelay=0.04),
               "temple": dict(rt60=5.0, seed=104, damp=(6000.0, 1000.0), predelay=0.05),
               "arena": dict(rt60=2.2, seed=105, damp=(6000.0, 1200.0), predelay=0.03)}[kind]
        _IRS[kind] = make_ir(stereo=True, **cfg)
    return _IRS[kind]


FUNCS = {"amb_town": amb_town, "amb_forest": amb_forest, "amb_catacombs": amb_catacombs,
         "amb_temple": amb_temple, "amb_arena": amb_arena}


def render(name):
    r = np.random.default_rng(seed_of(name))
    return FUNCS[name](r)
