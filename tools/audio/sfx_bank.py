"""All SFX recipes. Each recipe is fn(r, v) -> mono float array (v = variation index).

File names are a contract (see work/lemondev/bh-001/contracts/audio.md). Mono, 44.1 kHz.
"""
from __future__ import annotations

import zlib

import numpy as np

from kit import (BAR, bellnote, brass, bubble, burst, choir, click, crackle, debris, electric,
                 flame, grains, metal, nz, pebble, ping, sparkle, stickslip, swell_noise, thump,
                 verb, voice, whoosh, wood_knock)
from synth import (N, SR, TAU, additive, dc_block, env_ad, env_exp, env_lin, env_swell, fade,
                   filt, fm, formant, hp, loop_crossfade, lp, mix, mtof, normalize, peq, pink,
                   resample, resonator, sat, saw, sine, square, tri, trim, tvec, tvf, varispeed,
                   white, brown, bp, place, circ)

REG: dict[str, tuple] = {}


def sfx(*names, loop=False):
    def deco(fn):
        for i, nm in enumerate(names):
            REG[nm] = (fn, i, loop)
        return fn
    return deco


def seed_of(name: str) -> int:
    return zlib.crc32(name.encode()) & 0x7FFFFFFF


def finalize(x, loop=False):
    if loop:  # process as if the loop had been playing forever -> seam stays continuous
        x = circ(dc_block, x, len(x))
    else:
        x = dc_block(x)
    if not loop:
        x = trim(x, -64.0)
        tail = min(0.06, 0.25 * len(x) / SR)
        x = fade(x, 0.0012, tail)
    return normalize(x, -1.0)


def render(name):
    fn, v, loop = REG[name]
    r = np.random.default_rng(seed_of(name))
    x = fn(r, v)
    return finalize(x, loop), loop


PV = [1.0, 0.93, 1.07, 0.88]  # pitch ratios per variation


# ============================================================================================
# WEAPONS
# ============================================================================================
@sfx("swing_light_1", "swing_light_2", "swing_light_3")
def swing_light(r, v):
    p = PV[v]
    d = 0.30 + 0.03 * v
    w = whoosh(r, d, 500 * p, 2600 * p, q=1.3, peak=0.5 + 0.05 * v, sing=0.35, sing_q=8)
    air = whoosh(r, d * 0.9, 2500 * p, 6500 * p, q=0.9, peak=0.5)
    cloth = swell_noise(r, 0.08, 400, 2500, peak=0.3)
    return mix((w, 0, 1.0), (air, 0.01, 0.35), (cloth, 0, 0.15))


@sfx("swing_heavy_1", "swing_heavy_2", "swing_heavy_3")
def swing_heavy(r, v):
    p = PV[v]
    d = 0.58 + 0.04 * v
    w = whoosh(r, d, 180 * p, 1300 * p, q=0.9, peak=0.58, rise=2.6, fall=1.4, body=0.6)
    sing = whoosh(r, d, 700 * p, 2200 * p, q=6.0, peak=0.6, rise=3.0)
    rumble = lp(white(N(d), r), 220) * env_swell(N(d), 0.6, 2.5, 1.5)
    grunt = voice(r, 0.22, np.linspace(120, 95, N(0.22)), [(0, "u"), (1, "a")], breath=0.5,
                  rough=0.2, env=env_swell(N(0.22), 0.3))
    y = mix((w, 0, 1.0), (sing, 0, 0.25), (nz(rumble), 0, 0.45), (grunt, d * 0.35, 0.08))
    return sat(y, 1.4)


@sfx("swing_dagger_1", "swing_dagger_2")
def swing_dagger(r, v):
    p = PV[v] * 1.05
    w = whoosh(r, 0.17, 1400 * p, 5200 * p, q=1.8, peak=0.45, rise=1.8, fall=1.8, sing=0.5, sing_q=10)
    return mix((w, 0, 1.0), (click(r, 6000, 0.004), 0, 0.06))


@sfx("swing_blunt_1", "swing_blunt_2")
def swing_blunt(r, v):
    p = PV[v]
    d = 0.5
    n = N(d)
    w = whoosh(r, d, 140 * p, 800 * p, q=0.8, peak=0.55, rise=2.4, fall=1.5, body=0.9, src="pink")
    e = env_swell(n, 0.55, 2.4, 1.5)
    wub = sine(np.linspace(75, 55, n) * p, n) * e * (0.6 + 0.4 * np.sin(TAU * 18 * tvec(n)))
    return sat(mix((w, 0, 1.0), (nz(wub), 0, 0.35)), 1.5)


@sfx("bow_draw")
def bow_draw(r, v):
    d = 0.85
    n = N(d)
    e = np.clip(tvec(n) / d, 0, 1) ** 1.3 * np.clip((d - tvec(n)) / 0.05, 0, 1)
    creak = stickslip(r, d, 60, 140, res=((520, 10), (1250, 14), (2600, 18)), jitter=0.3, env=e)
    string = stickslip(r, d, 180, 260, res=((900, 25), (1800, 25)), jitter=0.05, env=e ** 2)
    rub = swell_noise(r, d, 1500, 6000, peak=0.85, rise=1.5, fall=0.5)
    leather = swell_noise(r, 0.25, 300, 2500, peak=0.4)
    return mix((creak, 0, 0.8), (string, 0, 0.3), (rub, 0, 0.25), (leather, 0, 0.3))


@sfx("bow_release")
def bow_release(r, v):
    n = N(0.55)
    t = tvec(n)
    f = 98 * (1 + 0.5 * np.exp(-t / 0.01))
    twang = sine(f, n) + 0.5 * sine(2 * f, n) + 0.25 * sine(3.01 * f, n) + 0.15 * saw(f, n)
    twang = nz(lp(twang, 2500) * env_ad(n, 0.0005, 0.35))
    thwip = whoosh(r, 0.16, 4500, 1600, q=1.6, peak=0.12, rise=1.0, fall=2.0)
    return mix((click(r, 2500, 0.004), 0, 0.7), (twang, 0, 0.8), (thwip, 0.005, 0.8),
               (thump(r, 160, 80, 0.08, 0.01), 0, 0.35))


@sfx("arrow_impact_1", "arrow_impact_2")
def arrow_impact(r, v):
    p = PV[v]
    n = N(0.45)
    t = tvec(n)
    thunk = thump(r, 230 * p, 95 * p, 0.12, 0.012, 0.08, 2.0)
    wood = wood_knock(r, 700 * p, 7, 0.09)
    quiver = sine(310 * p, n) * (0.5 + 0.5 * np.sin(TAU * 26 * t)) * env_ad(n, 0.002, 0.35)
    quiver += 0.4 * sine(620 * p * 1.01, n) * env_ad(n, 0.002, 0.2)
    y = mix((click(r, 3000, 0.004), 0, 0.8), (thunk, 0, 0.9), (wood, 0, 0.6),
            (burst(r, 0.04, 400, 4000, 0.03), 0, 0.5), (nz(quiver), 0.01, 0.22))
    return verb(sat(y, 1.5), "room", 0.08)


# ============================================================================================
# IMPACTS
# ============================================================================================
def _squelch(r, dur, f, rate):
    n = N(dur)
    t = tvec(n)
    fc = f * (1 + 0.6 * np.sin(TAU * rate * t + r.uniform(0, TAU))) * np.exp(-t * 3)
    return nz(tvf(white(n, r), "bp", np.maximum(fc, 120), 4.0) * env_ad(n, 0.004, dur * 0.8))


@sfx("hit_flesh_1", "hit_flesh_2", "hit_flesh_3")
def hit_flesh(r, v):
    p = PV[v]
    body = thump(r, 140 * p, 55 * p, 0.25, 0.03, 0.2, 2.2)
    smack = burst(r, 0.09, 200, 2600 * p, 0.07)
    sq = _squelch(r, 0.18, 700 * p, r.uniform(16, 28))
    y = mix((body, 0, 1.0), (smack, 0, 0.8), (sq, 0.006, 0.45), (click(r, 2500, 0.004), 0, 0.25))
    y = peq(sat(y, 1.8), 250, 3.0, 0.8)
    return verb(y, "room", 0.07)


@sfx("hit_bone_1", "hit_bone_2", "hit_bone_3")
def hit_bone(r, v):
    p = PV[v]
    cr = np.zeros(N(0.08))
    for _ in range(r.integers(3, 7)):
        k = click(r, r.uniform(1500, 3200), r.uniform(0.002, 0.007))
        place(cr, k, N(r.uniform(0, 0.035)), r.uniform(0.3, 1.0))
    knock = nz(mix((wood_knock(r, 1100 * p, 10, 0.08), 0, 1.0), (wood_knock(r, 2400 * p, 14, 0.05), 0, 0.5)))
    body = thump(r, 170 * p, 75, 0.16, 0.02, 0.12, 1.6)
    y = mix((body, 0, 0.75), (nz(cr), 0, 0.9), (knock, 0.002, 0.6),
            (burst(r, 0.05, 300, 3000, 0.04), 0, 0.45))
    return verb(sat(y, 1.6), "room", 0.07)


@sfx("hit_armor_1", "hit_armor_2", "hit_armor_3")
def hit_armor(r, v):
    p = PV[v]
    m = metal(r, 380 * p, 0.45, 0.28, n_parts=11, spread=7, bright=0.5)
    y = mix((thump(r, 130 * p, 60, 0.18, 0.02, 0.12), 0, 0.8), (m, 0, 0.7),
            (click(r, 4000, 0.005), 0, 0.5), (burst(r, 0.06, 800, 7000, 0.05), 0, 0.5))
    return verb(sat(y, 1.5), "room", 0.1)


@sfx("hit_heavy_1", "hit_heavy_2")
def hit_heavy(r, v):
    p = PV[v]
    boom = thump(r, 95 * p, 32 * p, 1.0, 0.06, 0.75, 2.5)
    body = thump(r, 175 * p, 70 * p, 0.3, 0.02, 0.2, 2.0)
    smack = burst(r, 0.15, 120, 1800, 0.12)
    sq = _squelch(r, 0.22, 450 * p, 14)
    gr = debris(r, 0.12, 300, 0.03, 800, 2500)
    y = mix((boom, 0, 1.0), (body, 0, 0.8), (smack, 0, 0.7), (sq, 0.01, 0.35), (gr, 0.004, 0.25),
            (click(r, 2000, 0.005), 0, 0.3))
    y = filt(sat(y, 2.4), "lowshelf", 110, 0.7, 3.0)
    return verb(y, "room", 0.1)


@sfx("crit_hit")
def crit_hit(r, v):
    base = hit_flesh(r, 0)
    boom = thump(r, 80, 30, 0.9, 0.07, 0.7, 2.5)
    shing = metal(r, 1650, 1.0, 0.6, ratios=[1, 1.5, 2.756, 3.1, 5.404], bright=0.35)
    crack = burst(r, 0.025, 2500, 15000, 0.02)
    snap = whoosh(r, 0.22, 4000, 9000, q=1.0, peak=0.08, rise=1.0, fall=2.5)
    y = mix((crack, 0, 1.0), (base, 0, 0.9), (boom, 0, 0.85), (shing, 0.003, 0.4), (snap, 0, 0.35))
    return verb(sat(y, 2.0), "plate", 0.12)


@sfx("block_1", "block_2")
def block(r, v):
    f0 = [305, 345][v]
    n = N(1.1)
    plate = metal(r, f0, 1.1, 0.75, n_parts=14, spread=9, bright=0.45)
    bar = nz(additive(f0 * 2.2, [(1, 1, 0.6), (BAR[1], 0.6, 0.35), (BAR[2], 0.35, 0.2), (BAR[3], 0.2, 0.12)], n, r))
    y = mix((thump(r, 190, 80, 0.15, 0.015, 0.1), 0, 0.75), (plate, 0, 0.8), (bar, 0, 0.45),
            (click(r, 3000, 0.005), 0, 0.6), (burst(r, 0.035, 1000, 10000, 0.03), 0, 0.5))
    return verb(sat(y, 1.3), "room", 0.14)


@sfx("parry")
def parry(r, v):
    f0 = 1180
    n = N(1.8)
    parts = []
    for ra, a, d in [(1, 1, 1.5), (BAR[1], 0.75, 0.9), (BAR[2], 0.45, 0.55), (BAR[3], 0.25, 0.35), (1.5, 0.3, 0.8)]:
        parts += [(ra, a, d), (ra * 1.0025, a * 0.7, d * 0.9)]
    ring = nz(additive(f0, parts, n, r))
    m = N(0.2)
    scrape = nz(tvf(white(m, r), "bp", np.geomspace(2500, 6500, m), 3.0) * env_swell(m, 0.15, 1.0, 1.5))
    y = mix((click(r, 5000, 0.004), 0, 0.8), (thump(r, 300, 150, 0.08, 0.01), 0, 0.35),
            (ring, 0, 0.8), (scrape, 0, 0.5), (burst(r, 0.02, 3000, 15000, 0.015), 0, 0.5))
    return verb(y, "plate", 0.18)


@sfx("wall_impact_1", "wall_impact_2")
def wall_impact(r, v):
    p = PV[v]
    y = mix((thump(r, 115 * p, 40 * p, 0.55, 0.04, 0.45, 2.5), 0, 1.0),
            (burst(r, 0.3, 60, 1200, 0.22), 0, 0.75),
            (burst(r, 0.04, 800, 6000, 0.03), 0, 0.5),
            (debris(r, 0.55, 90, 0.14, 1400, 4500), 0.02, 0.4),
            (_squelch(r, 0.12, 500, 20), 0, 0.25))
    return verb(sat(y, 2.0), "room", 0.14)


@sfx("body_fall")
def body_fall(r, v):
    h1 = mix((thump(r, 120, 50, 0.3, 0.03, 0.25), 0, 1.0), (burst(r, 0.12, 80, 900, 0.1), 0, 0.7))
    h2 = mix((thump(r, 95, 45, 0.3, 0.03, 0.25), 0, 1.0), (burst(r, 0.1, 80, 1200, 0.08), 0, 0.6))
    cloth = swell_noise(r, 0.25, 300, 3000, peak=0.6)
    rattle = grains(r, 0.3, 90 * np.exp(-tvec(N(0.3)) / 0.1),
                    lambda rr, t: ping(rr, rr.uniform(2500, 6000), rr.uniform(0.02, 0.06)), 1.5)
    y = mix((cloth, 0, 0.35), (h1, 0.08, 1.0), (h2, 0.3, 0.7), (nz(rattle), 0.09, 0.2))
    return verb(lp(sat(y, 1.6), 4000), "room", 0.1)


@sfx("stagger")
def stagger(r, v):
    n = N(0.3)
    grunt = voice(r, 0.3, np.linspace(150, 95, n), [(0, "u"), (0.35, "a"), (1, "o")], breath=0.45,
                  rough=0.25, env=env_swell(n, 0.2, 1.0, 1.5))
    scuff = swell_noise(r, 0.25, 400, 4000, peak=0.3)
    jingle = grains(r, 0.25, 120, lambda rr, t: ping(rr, rr.uniform(2500, 6500), rr.uniform(0.02, 0.07)), 1.5)
    y = mix((thump(r, 90, 50, 0.25, 0.03, 0.2), 0, 0.8), (scuff, 0.02, 0.5), (nz(jingle), 0.01, 0.3),
            (grunt, 0.03, 0.45))
    return verb(sat(y, 1.4), "room", 0.1)


@sfx("shatter_ice")
def shatter_ice(r, v):
    d = 1.0
    shard = grains(r, d, 260 * np.exp(-tvec(N(d)) / 0.18),
                   lambda rr, t: ping(rr, rr.uniform(2200, 9000), rr.uniform(0.03, 0.22), (1.0, 2.32, 4.25)), 1.4)
    y = mix((burst(r, 0.03, 2000, 16000, 0.02), 0, 1.0), (click(r, 4000, 0.004), 0, 0.8),
            (thump(r, 200, 90, 0.1, 0.01, 0.08), 0, 0.5), (nz(shard), 0.005, 0.8),
            (burst(r, 0.5, 4000, 16000, 0.4), 0, 0.3))
    return verb(y, "room", 0.15)


# ============================================================================================
# MAGIC
# ============================================================================================
@sfx("cast_fire")
def cast_fire(r, v):
    d = 0.95
    n = N(d)
    e = env_swell(n, 0.3, 1.4, 1.4)
    roar = nz(tvf(brown(n, r) * 0.5 + pink(n, r) * 0.5, "lp", 250 + 2600 * e, 0.8) * e)
    hiss = nz(tvf(white(n, r), "bp", 2500 + 3000 * e, 0.7) * e ** 1.5)
    cr = crackle(r, n, 25 + 140 * e) * e
    y = mix((roar, 0, 1.0), (hiss, 0, 0.25), (cr, 0, 0.4), (thump(r, 90, 45, 0.6, 0.1, 0.5, 1.5), 0.06, 0.7))
    return verb(sat(y, 1.6), "room", 0.12)


@sfx("fire_whoosh")
def fire_whoosh(r, v):
    d = 1.1
    n = N(d)
    w = whoosh(r, d, 220, 1700, q=0.7, peak=0.45, rise=1.8, fall=1.4, body=0.8, src="pink")
    fl = flame(r, n, 900, 14) * env_swell(n, 0.45, 1.8, 1.4)
    cr = crackle(r, n, 120) * env_swell(n, 0.5, 1.5, 1.2)
    return sat(mix((w, 0, 1.0), (fl, 0, 0.7), (cr, 0, 0.35)), 1.5)


def _explosion(r, scale=1.0, dur=2.2):
    n = N(dur)
    t = tvec(n)
    boom = thump(r, 75 / scale ** 0.3, 28 / scale ** 0.2, dur, 0.12 * scale, 1.3 * scale, 3.0)
    blast = nz(tvf(brown(n, r) * 0.6 + white(n, r) * 0.4, "lp", 300 + 6000 * np.exp(-t / 0.15), 0.7)
               * env_ad(n, 0.002, 1.1 * scale))
    roar = nz(tvf(pink(n, r), "lp", 400 + 1200 * np.exp(-t / 0.4), 0.8) * env_swell(n, 0.08, 1.0, 2.0))
    deb = debris(r, dur, 140, 0.35 * scale, 1200, 5000)
    cr = crackle(r, n, 200 * np.exp(-t / (0.6 * scale)))
    return mix((boom, 0, 1.0), (burst(r, 0.08, 1500, 14000, 0.06), 0, 0.8), (blast, 0, 0.9),
               (roar, 0, 0.6), (deb, 0.05, 0.3), (cr, 0.02, 0.25))


@sfx("fire_explode")
def fire_explode(r, v):
    return verb(sat(_explosion(r, 1.0, 2.2), 2.5), "hall", 0.22)


@sfx("burn_loop", loop=True)
def burn_loop(r, v):
    L, xf = N(4.0), N(0.5)
    n = L + xf
    fl = flame(r, n, 550, 4)
    cr = crackle(r, n, 45)
    hiss = nz(hp(white(n, r), 4000)) * 0.5
    y = mix((fl, 0, 1.0), (cr, 0, 0.45), (hiss, 0, 0.08))
    return loop_crossfade(y, L, xf)


def _glass_rise(r, d, rate, f_lo, f_hi):
    n = N(d)
    out = np.zeros(n)
    rr = np.clip(rate / SR, 0, 1)
    idx = np.nonzero(r.random(n) < rr)[0]
    for i in idx:
        fr = f_lo * (f_hi / f_lo) ** (i / n) * r.uniform(0.8, 1.25)
        place(out, ping(r, fr, r.uniform(0.05, 0.3), (1.0, 2.32, 4.25)) * r.uniform(0.2, 1), i)
    return nz(out)


@sfx("cast_ice")
def cast_ice(r, v):
    d = 1.0
    n = N(d)
    t = tvec(n)
    e = env_swell(n, 0.7, 1.4, 1.5)
    sh = _glass_rise(r, d, 30 + 250 * t / d, 1800, 6000)
    hiss = nz(tvf(white(n, r), "bp", 4000 + 5000 * e, 1.5) * e)
    chord = nz(sum(sine(mtof(m), n, r.random()) for m in (88, 95, 100, 102)) * e)
    breath = nz(tvf(pink(n, r), "lp", 300 + 700 * e, 0.7) * e)
    y = mix((sh, 0, 0.7), (hiss, 0, 0.45), (chord, 0, 0.25), (breath, 0, 0.35))
    return verb(y, "plate", 0.25)


@sfx("ice_nova")
def ice_nova(r, v):
    d = 1.6
    n = N(d)
    t = tvec(n)
    exp_w = nz(tvf(white(n, r), "bp", 900 + 3000 * np.exp(-t / 0.3), 1.0) * env_ad(n, 0.01, 1.2))
    sh = grains(r, d, 380 * np.exp(-t / 0.3),
                lambda rr, tt: ping(rr, rr.uniform(2000, 9500), rr.uniform(0.04, 0.3), (1.0, 2.32, 4.25)), 1.3)
    ring = nz(sum(sine(mtof(m), n, r.random()) * env_ad(n, 0.002, 1.2) for m in (86, 93, 98, 105)))
    y = mix((burst(r, 0.04, 1500, 16000, 0.03), 0, 1.0), (thump(r, 140, 50, 0.4, 0.03, 0.3), 0, 0.7),
            (exp_w, 0, 0.7), (nz(sh), 0.01, 0.6), (ring, 0.01, 0.25))
    return verb(y, "hall", 0.2)


@sfx("freeze")
def freeze(r, v):
    d = 1.3
    n = N(d)
    t = tvec(n)
    rate = 20 + 500 * np.clip(t / 0.85, 0, 1) ** 2 * (t < 0.9)
    cr = crackle(r, n, rate, 1800, 9000)
    creak = stickslip(r, 0.85, 30, 90, res=((900, 18), (2300, 20)), jitter=0.4,
                      env=np.linspace(0.2, 1, N(0.85)))
    ring = nz(sum(ping(r, mtof(m), 0.9, (1.0, 2.32, 4.25), dur=0.45) for m in (96, 103)))
    y = mix((cr, 0, 0.7), (creak, 0, 0.35), (ring, 0.86, 0.6), (click(r, 5000, 0.004), 0.86, 0.6),
            (swell_noise(r, 0.9, 3000, 12000, 0.9, 1.5, 0.3), 0, 0.3))
    return verb(y, "plate", 0.18)


@sfx("cast_lightning")
def cast_lightning(r, v):
    d = 0.8
    n = N(d)
    t = tvec(n)
    e = np.clip(t / d, 0, 1) ** 1.5
    buzz = electric(r, n, base=70, gate_rate=60, density=0.4 + 0.5 * float(np.mean(e)))
    buzz = nz(tvf(buzz, "bp", 900 + 2500 * e, 0.8)) * e
    st = crackle(r, n, 40 + 900 * e, 2000, 12000) * e
    whine = nz(sine(np.geomspace(300, 1400, n), n) * e ** 2)
    y = mix((buzz, 0, 0.9), (st, 0, 0.6), (whine, 0, 0.12), (burst(r, 0.04, 2000, 15000, 0.03), d - 0.06, 0.8))
    return sat(y, 1.4)


@sfx("lightning_zap_1", "lightning_zap_2")
def lightning_zap(r, v):
    d = 0.45 + 0.05 * v
    n = N(d)
    t = tvec(n)
    buzz = electric(r, n, base=[58, 66][v], gate_rate=140, density=0.7) * env_ad(n, 0.001, d * 0.8)
    buzz = hp(buzz, 350, order=2)
    sweep = nz(tvf(white(n, r), "bp", 2000 + 7000 * np.exp(-t / 0.08), 2.0) * env_ad(n, 0.001, d * 0.6))
    cr = crackle(r, n, 900 * np.exp(-t / 0.12), 2500, 14000)
    y = mix((burst(r, 0.015, 2000, 18000, 0.012), 0, 1.0), (click(r, 3000, 0.003), 0, 0.8),
            (nz(buzz), 0.002, 0.75), (sweep, 0, 0.45), (cr, 0, 0.5), (thump(r, 160, 70, 0.1, 0.01), 0, 0.22))
    return verb(sat(y, 1.8), "room", 0.1)


@sfx("thunder_strike")
def thunder_strike(r, v):
    d = 3.4
    n = N(d)
    rum = np.zeros(n)
    for k in range(9):
        st = r.uniform(0.05, 1.6)
        m = N(r.uniform(0.6, 1.6))
        seg = lp(brown(m, r), r.uniform(150, 400)) * env_ad(m, r.uniform(0.02, 0.15), m / SR)
        place(rum, seg, N(st), r.uniform(0.4, 1.0) * np.exp(-st / 1.2))
    crack = mix((burst(r, 0.06, 800, 16000, 0.05), 0, 1.0), (click(r, 2000, 0.005), 0, 0.8),
                (electric(r, N(0.12), 90, 200, 0.8) * env_ad(N(0.12), 0.001, 0.1), 0, 0.5))
    y = mix((crack, 0, 1.0), (thump(r, 60, 25, 2.6, 0.1, 2.0, 2.0), 0, 0.9), (nz(rum), 0.03, 0.9))
    return verb(sat(y, 2.2), "hall", 0.3)


@sfx("cast_earth")
def cast_earth(r, v):
    d = 1.0
    n = N(d)
    e = env_swell(n, 0.7, 1.3, 2.0)
    grind = nz(tvf(brown(n, r), "lp", 120 + 400 * e, 1.0) * e)
    gr = debris(r, d, 60, 1.0, 400, 1800) * e
    y = mix((grind, 0, 1.0), (gr, 0, 0.5), (thump(r, 90, 38, 0.35, 0.03, 0.3, 2.2), 0.7, 0.9),
            (burst(r, 0.05, 300, 3000, 0.04), 0.7, 0.4))
    return sat(y, 1.8)


@sfx("earth_quake")
def earth_quake(r, v):
    d = 3.0
    n = N(d)
    t = tvec(n)
    e = env_lin([(0, 0), (0.1, 1), (1.8, 0.8), (3.0, 0)], n)
    am = 0.55 + 0.45 * nz(lp(white(n, r), 9))
    rumble = nz(lp(brown(n, r), 140, order=2) * am * e)
    sub = nz(sine(34 + 4 * np.sin(TAU * 0.7 * t), n) * e * am)
    gr = debris(r, d, 70, 3.0, 500, 3000) * e
    y = mix((burst(r, 0.08, 400, 8000, 0.06), 0, 0.6), (thump(r, 80, 30, 0.8, 0.06, 0.6), 0, 0.8),
            (rumble, 0, 1.0), (sub, 0, 0.6), (gr, 0, 0.35))
    return sat(y, 2.0)


@sfx("rock_impact")
def rock_impact(r, v):
    y = mix((thump(r, 105, 38, 0.7, 0.04, 0.55, 2.6), 0, 1.0), (burst(r, 0.05, 600, 8000, 0.04), 0, 0.7),
            (burst(r, 0.25, 80, 1500, 0.2), 0, 0.7), (debris(r, 0.9, 150, 0.2, 1200, 4500), 0.01, 0.45))
    return verb(sat(y, 2.2), "room", 0.14)


@sfx("wind_gust")
def wind_gust(r, v):
    d = 1.9
    n = N(d)
    e = env_swell(n, 0.45, 1.6, 1.4)
    wob = 1 + 0.15 * nz(lp(white(n, r), 3))
    whistle = nz(tvf(pink(n, r), "bp", (350 + 900 * e) * wob, 3.0) * e)
    body = nz(tvf(pink(n, r), "bp", (250 + 1500 * e) * wob, 0.5) * e)
    return mix((body, 0, 1.0), (whistle, 0, 0.5))


@sfx("water_splash")
def water_splash(r, v):
    d = 0.9
    b = np.zeros(N(d))
    for _ in range(34):
        st = r.uniform(0.01, 0.55) ** 1.3
        place(b, bubble(r, r.uniform(350, 1600), r.uniform(0.025, 0.08)), N(st), r.uniform(0.2, 1.0))
    y = mix((burst(r, 0.07, 200, 3000, 0.06), 0, 0.9), (thump(r, 220, 110, 0.12, 0.02, 0.1), 0, 0.6),
            (swell_noise(r, 0.45, 2000, 12000, 0.12, 1.0, 2.0), 0, 0.7), (nz(b), 0.01, 0.5))
    return verb(y, "room", 0.12)


@sfx("water_wave")
def water_wave(r, v):
    d = 2.1
    n = N(d)
    e = env_swell(n, 0.5, 1.8, 1.5)
    surge = nz(tvf(pink(n, r), "lp", 300 + 2700 * e, 0.8) * e)
    spray = nz(tvf(white(n, r), "bp", 5000, 0.8) * env_swell(n, 0.55, 3.0, 2.0))
    b = np.zeros(n)
    for _ in range(40):
        st = r.uniform(0.7, 1.9)
        place(b, bubble(r, r.uniform(300, 1300), r.uniform(0.03, 0.09)), N(st), r.uniform(0.1, 1.0))
    y = mix((surge, 0, 1.0), (spray, 0, 0.45), (nz(b), 0, 0.3),
            (nz(lp(brown(n, r), 120) * e), 0, 0.5))
    return verb(y, "room", 0.1)


@sfx("holy_chime")
def holy_chime(r, v):
    notes = [81, 85, 88, 93]  # A5 C#6 E6 A6
    y = mix(*[(bellnote(r, mtof(m), 2.0, 1.8), 0.06 * i, 1.0 - 0.1 * i) for i, m in enumerate(notes)],
            (sparkle(r, 1.4, 40, 5000, 11000), 0.02, 0.35))
    return verb(y, "hall", 0.35)


@sfx("holy_strike")
def holy_strike(r, v):
    ch = choir(r, mtof(np.array([57, 64, 69, 73])), 1.4, "ah", attack=0.03, release=1.0)
    bells = mix(*[(bellnote(r, mtof(m), 1.6, 1.4), 0.03 * i, 0.8) for i, m in enumerate([81, 88, 93])])
    y = mix((burst(r, 0.03, 1500, 16000, 0.02), 0, 1.0), (thump(r, 130, 48, 0.8, 0.04, 0.6, 2.2), 0, 0.9),
            (ch, 0.01, 0.55), (bells, 0.005, 0.5), (sparkle(r, 1.2, 70, 5000, 12000), 0, 0.35))
    return verb(y, "hall", 0.32)


@sfx("heal")
def heal(r, v):
    notes = [74, 78, 81, 86, 88]  # D5 F#5 A5 D6 E6
    tones = [(nz(additive(mtof(m), [(1, 1, 1.2), (2, 0.3, 0.7), (3, 0.12, 0.4)], N(1.6), r, attack=0.03)),
              0.11 * i, 0.8) for i, m in enumerate(notes)]
    pad = nz(sum(sine(mtof(m), N(1.8), r.random()) for m in (62, 66, 69)) * env_swell(N(1.8), 0.4, 1.5, 1.5))
    y = mix(*tones, (pad, 0, 0.4), (sparkle(r, 1.6, 50 * env_swell(N(1.6), 0.5), 4000, 10000), 0, 0.3),
            (swell_noise(r, 1.4, 3000, 10000, 0.5, 1.5, 1.5), 0, 0.15))
    return verb(y, "hall", 0.4)


def _whisper(r, d, vowels=((0, "i"), (0.5, "a"), (1, "u")), shift=1.0):
    n = N(d)
    return nz(hp(formant(white(n, r), list(vowels), shift), 900) * env_swell(n, 0.5, 1.5, 1.5))


@sfx("dark_cast")
def dark_cast(r, v):
    d = 1.25
    n = N(d)
    e = env_swell(n, 0.65, 1.8, 1.2)
    drone = sum(saw(mtof(m) * (1 + 0.003 * k), n, r.random()) for k, m in enumerate([38, 39, 45, 50]))
    drone = nz(tvf(drone, "lp", 180 + 1300 * e, 1.5) * e)
    rev = nz(tvf(white(n, r), "bp", 400 + 2500 * e, 1.2) * np.clip(tvec(n) / (d * 0.7), 0, 1) ** 3
             * (tvec(n) < d * 0.72))
    y = mix((drone, 0, 1.0), (rev, 0, 0.45), (_whisper(r, d), 0, 0.4),
            (thump(r, 70, 35, 0.5, 0.05, 0.4), d * 0.7, 0.6))
    return verb(sat(y, 1.6), "hall", 0.3)


@sfx("dark_curse")
def dark_curse(r, v):
    d = 1.5
    n = N(d)
    bend = 2 ** (-np.linspace(0, 1.2, n) / 12)
    cl = sum(saw(mtof(m) * bend * (1 + 0.004 * k), n, r.random()) for k, m in enumerate([45, 46, 51, 57, 58]))
    cl = nz(tvf(cl, "lp", 1600 * np.exp(-tvec(n) / 0.8) + 200, 1.2) * env_ad(n, 0.02, 1.4))
    scrape = nz(tvf(white(n, r), "bp", np.geomspace(3500, 900, n), 9.0) * env_ad(n, 0.01, 1.0))
    y = mix((thump(r, 70, 30, 0.9, 0.06, 0.7, 2.2), 0, 0.9), (cl, 0, 0.8), (scrape, 0, 0.3),
            (_whisper(r, d, ((0, "a"), (0.4, "u"), (1, "o")), 0.8), 0.05, 0.35))
    return verb(sat(y, 1.8), "hall", 0.3)


@sfx("drain")
def drain(r, v):
    d = 1.3
    n = N(d)
    t = tvec(n)
    e = env_swell(n, 0.6, 1.5, 1.5)
    suck = nz(tvf(white(n, r), "bp", np.geomspace(6000, 300, n), 3.0) * e)
    pulse = nz(sine(55, n) * (0.5 + 0.5 * np.sin(TAU * 3.0 * t) ** 8) * e)
    slurp = nz(formant(pink(n, r), [(0, "i"), (1, "u")], 0.9) * e)
    y = mix((suck, 0, 0.8), (pulse, 0, 0.6), (slurp, 0, 0.4), (sparkle(r, d, 30, 2000, 5000)[::-1], 0, 0.2))
    return verb(y, "hall", 0.25)


@sfx("blink")
def blink(r, v):
    n = N(0.45)
    t = tvec(n)
    f = 300 * (2500 / 300) ** np.clip(t / 0.06, 0, 1)
    up = nz(fm(f, 1.5, 2.0 * np.exp(-t / 0.1), n) * env_ad(n, 0.002, 0.25))
    y = mix((up, 0, 0.7), (burst(r, 0.03, 500, 5000, 0.025), 0.05, 0.7),
            (whoosh(r, 0.3, 3000, 900, q=1.2, peak=0.1), 0.04, 0.5), (sparkle(r, 0.35, 90, 5000, 11000), 0.04, 0.3))
    return verb(y, "plate", 0.15)


@sfx("arcane_charge")
def arcane_charge(r, v):
    d = 1.35
    n = N(d)
    t = tvec(n)
    x = np.clip(t / d, 0, 1)
    f = 220 * 2 ** x
    trem = 0.6 + 0.4 * np.sin(TAU * np.cumsum(6 + 20 * x ** 2) / SR)
    tone = nz(fm(f, 2.0, 0.5 + 3.5 * x, n) + 0.5 * fm(f * 1.5, 1.0, 1 + 2 * x, n)) * trem * x ** 1.2
    sp = _glass_rise(r, d, 20 + 200 * x, 2500, 8000) * x
    hum = nz(sine(110, n) + 0.4 * sine(220.5, n)) * x
    y = mix((tone, 0, 0.8), (sp, 0, 0.35), (hum, 0, 0.4))
    return verb(y, "plate", 0.18)


@sfx("arcane_surge")
def arcane_surge(r, v):
    d = 1.1
    n = N(d)
    t = tvec(n)
    idx = 0.5 + 6 * np.exp(-t / 0.12)
    tone = nz(sum(fm(mtof(m), 2.0, idx, n) for m in (69, 76, 81)) * env_ad(n, 0.002, 0.9))
    y = mix((tone, 0, 0.8), (whoosh(r, 0.6, 3000, 800, q=0.9, peak=0.08), 0, 0.6),
            (sparkle(r, 1.0, 200 * np.exp(-tvec(N(1.0)) / 0.25), 3000, 10000), 0, 0.35),
            (thump(r, 140, 55, 0.4, 0.03, 0.3), 0, 0.6))
    return verb(y, "plate", 0.2)


@sfx("meteor_fall")
def meteor_fall(r, v):
    d = 2.2
    n = N(d)
    t = tvec(n)
    x = np.clip(t / d, 0, 1)
    whistle = nz(tvf(white(n, r), "bp", np.geomspace(3200, 500, n), 6.0) * x ** 1.2)
    roar = nz(tvf(pink(n, r) * 0.5 + brown(n, r) * 0.5, "lp", 250 + 1400 * x, 0.8) * x ** 1.5)
    cr = crackle(r, n, 20 + 250 * x) * x ** 2
    y = mix((whistle, 0, 0.45), (roar, 0, 1.0), (cr, 0, 0.35))
    return sat(y, 1.6)


@sfx("meteor_impact")
def meteor_impact(r, v):
    y = mix((_explosion(r, 1.6, 3.2), 0, 1.0), (thump(r, 55, 20, 2.8, 0.15, 2.2, 2.0), 0, 0.9),
            (debris(r, 2.4, 90, 0.9, 800, 3500), 0.2, 0.3))
    return verb(sat(y, 2.6), "hall", 0.28)


@sfx("war_cry")
def war_cry(r, v):
    d = 1.8
    n = N(d)
    f = 110 * (0.93 + 0.07 * np.clip(tvec(n) / 0.15, 0, 1))
    horn = nz(brass(r, f, d, swell=0.18, bright=1.2, rel=0.5) + 0.6 * brass(r, f * 1.5, d, swell=0.22, bright=1.0, rel=0.5))
    roar = voice(r, d * 0.85, 135 * (1 + 0.08 * np.sin(np.linspace(0, np.pi, N(d * 0.85)))), [(0, "a"), (0.7, "a"), (1, "o")],
                 rough=0.5, sub=0.3, breath=0.5, env=env_lin([(0, 0), (0.1, 1), (1.2, 0.8), (1.53, 0)], N(d * 0.85)))
    y = mix((horn, 0, 0.8), (sat(roar, 3.0), 0.02, 0.7), (thump(r, 90, 45, 0.5, 0.05, 0.4), 0, 0.5))
    return verb(sat(y, 1.5), "hall", 0.3)


@sfx("whirlwind_loop", loop=True)
def whirlwind_loop(r, v):
    Ls, xf = 1.8, N(0.2)
    L = N(Ls)
    n = L + xf
    t = tvec(n)
    period = Ls / 6.0
    ph = (t / period) % 1.0
    e = (0.5 - 0.5 * np.cos(TAU * ph)) ** 2
    blade = nz(tvf(white(n, r), "bp", 600 + 2400 * e, 1.3) * (0.15 + e))
    sing = nz(tvf(white(n, r), "bp", 1200 + 3000 * e, 7.0) * e)
    bed = nz(tvf(pink(n, r), "bp", 500, 0.6))
    y = mix((blade, 0, 1.0), (sing, 0, 0.25), (bed, 0, 0.3))
    return loop_crossfade(y, L, xf)


# ============================================================================================
# MOVEMENT
# ============================================================================================
@sfx("footstep_stone_1", "footstep_stone_2", "footstep_stone_3", "footstep_stone_4")
def footstep_stone(r, v):
    p = PV[v] * r.uniform(0.97, 1.03)
    heel = nz(resonator(white(N(0.02), r) * env_ad(N(0.02), 0.0003, 0.006), 2100 * p, 3.0))
    y = mix((thump(r, 115 * p, 60 * p, 0.09, 0.01, 0.06, 1.3), 0, 0.8), (heel, 0, 0.55),
            (click(r, 3000, 0.004), 0, 0.3), (debris(r, 0.06, 250, 0.03, 2000, 6000), 0.004, 0.25),
            (swell_noise(r, 0.08, 1500, 7000, 0.25), 0.02 + 0.01 * v, 0.2))
    return verb(lp(y, 9000), "room", 0.1)


@sfx("footstep_dirt_1", "footstep_dirt_2", "footstep_dirt_3", "footstep_dirt_4")
def footstep_dirt(r, v):
    p = PV[v] * r.uniform(0.97, 1.03)
    cr = grains(r, 0.12, 700 * np.exp(-tvec(N(0.12)) / 0.04),
                lambda rr, t: nz(bp(white(N(0.004), rr), rr.uniform(700, 2800), 1.5)) * env_ad(N(0.004), 0.0002, 0.003), 1.5)
    y = mix((thump(r, 95 * p, 50 * p, 0.1, 0.012, 0.07, 1.2), 0, 0.9), (nz(cr), 0, 0.6),
            (burst(r, 0.06, 150, 1500, 0.05), 0, 0.4))
    return verb(lp(y, 5500), "room", 0.06)


@sfx("footstep_grass_1", "footstep_grass_2", "footstep_grass_3")
def footstep_grass(r, v):
    p = PV[v]
    sw = swell_noise(r, 0.16, 2500 * p, 9000, 0.3, 1.2, 1.5)
    rus = grains(r, 0.18, 400 * env_swell(N(0.18), 0.3),
                 lambda rr, t: nz(hp(white(N(0.003), rr), 3000)) * env_ad(N(0.003), 0.0002, 0.002), 1.2)
    y = mix((thump(r, 85 * p, 50 * p, 0.09, 0.012, 0.06, 1.1), 0.01, 0.6), (sw, 0, 0.6), (nz(rus), 0, 0.4))
    return lp(y, 10000)


@sfx("footstep_heavy_1", "footstep_heavy_2")
def footstep_heavy(r, v):
    p = PV[v]
    y = mix((thump(r, 90 * p, 34 * p, 0.3, 0.02, 0.22, 2.2), 0, 1.0), (burst(r, 0.07, 80, 1200, 0.06), 0, 0.6),
            (metal(r, 820 * p, 0.2, 0.12, 6, 5, 0.7), 0.005, 0.25), (debris(r, 0.1, 250, 0.04, 1500, 5000), 0.005, 0.3))
    return verb(sat(y, 1.8), "room", 0.1)


@sfx("dodge_roll")
def dodge_roll(r, v):
    jingle = grains(r, 0.5, 90, lambda rr, t: ping(rr, rr.uniform(2500, 6500), rr.uniform(0.02, 0.06)), 1.5)
    y = mix((whoosh(r, 0.42, 300, 1600, q=0.7, peak=0.4, src="pink"), 0, 0.8),
            (thump(r, 110, 55, 0.15, 0.02, 0.12), 0.15, 0.7), (thump(r, 100, 50, 0.15, 0.02, 0.12), 0.36, 0.55),
            (nz(jingle), 0.1, 0.18), (swell_noise(r, 0.22, 500, 5000, 0.3), 0.38, 0.4))
    return lp(y, 8000)


@sfx("armor_rustle_1", "armor_rustle_2")
def armor_rustle(r, v):
    d = 0.45
    ch = grains(r, d, 260 * env_swell(N(d), 0.35 + 0.1 * v, 1.2, 1.5),
                lambda rr, t: ping(rr, rr.uniform(3000, 8500), rr.uniform(0.01, 0.045), (1.0, 1.52, 2.9)), 1.3)
    cloth = swell_noise(r, d, 700, 3500, 0.4)
    return mix((nz(ch), 0, 0.8), (cloth, 0, 0.35))


# ============================================================================================
# ENEMIES
# ============================================================================================
def _clatter(r, d, rate):
    return nz(grains(r, d, rate, lambda rr, t: wood_knock(rr, rr.uniform(700, 2600), rr.uniform(7, 15),
                                                           rr.uniform(0.02, 0.06)), 1.3))


@sfx("skeleton_rattle_1", "skeleton_rattle_2")
def skeleton_rattle(r, v):
    d = 0.75
    n = N(d)
    t = tvec(n)
    rate = 25 + 160 * (np.sin(TAU * (2.5 + v) * t) ** 2) * env_swell(n, 0.4, 1.0, 1.5)
    y = mix((_clatter(r, d, rate), 0, 1.0), (wood_knock(r, 520, 8, 0.07), 0.02, 0.5),
            (wood_knock(r, 480, 8, 0.07), 0.14 + 0.05 * v, 0.45))
    return verb(y, "room", 0.1)


@sfx("skeleton_death")
def skeleton_death(r, v):
    d = 1.5
    n = N(d)
    rate = 220 * np.exp(-tvec(n) / 0.35)
    y = mix((hit_bone(r, 0), 0, 0.8), (_clatter(r, d, rate), 0.04, 0.8),
            (wood_knock(r, 350, 6, 0.1), 0.62, 0.7), (thump(r, 140, 70, 0.12, 0.015, 0.1), 0.62, 0.4),
            (wood_knock(r, 420, 6, 0.1), 0.9, 0.5), (burst(r, 0.4, 500, 5000, 0.3, src="pink"), 0.6, 0.12))
    return verb(y, "room", 0.12)


@sfx("ghoul_growl_1", "ghoul_growl_2")
def ghoul_growl(r, v):
    d = 1.15 + 0.2 * v
    n = N(d)
    walk = np.cumsum(r.standard_normal(n)) / np.sqrt(n) * 0.25
    f0 = (74 + 10 * v) * np.exp(walk - walk.mean())
    vows = [(0, "o"), (0.35, "a"), (0.8, "u"), (1, "u")] if v == 0 else [(0, "u"), (0.4, "o"), (0.7, "a"), (1, "o")]
    g = voice(r, d, f0, vows, shift=0.8, jitter=0.06, rough=0.8, sub=0.4, breath=0.35,
              env=env_lin([(0, 0), (0.12, 1), (d * 0.7, 0.8), (d, 0)], n))
    gur = nz(tvf(white(n, r), "bp", 350 + 250 * np.sin(TAU * 23 * tvec(n)), 5.0) *
             (0.5 + 0.5 * np.sign(np.sin(TAU * 11 * tvec(n)))) * env_swell(n, 0.5))
    return verb(sat(mix((g, 0, 1.0), (gur, 0, 0.25)), 2.6), "room", 0.1)


@sfx("ghoul_death")
def ghoul_death(r, v):
    d = 1.6
    n = N(d)
    f0 = env_exp([(0, 110), (0.3, 210), (0.7, 120), (1.6, 55)], n)
    g = voice(r, d, f0, [(0, "a"), (0.2, "i"), (0.5, "a"), (1, "u")], shift=0.85, jitter=0.07,
              rough=0.3, sub=0.3, breath=0.45, env=env_lin([(0, 0), (0.08, 1), (0.9, 0.7), (1.5, 0)], n))
    gur = nz(tvf(white(n, r), "bp", 300 + 200 * np.sin(TAU * 17 * tvec(n)), 5.0) * env_lin([(0, 0), (0.8, 0), (1.1, 1), (1.6, 0)], n))
    y = mix((sat(g, 2.8), 0, 1.0), (gur, 0, 0.35), (body_fall(r, 0), 1.05, 0.5))
    return verb(y, "room", 0.1)


@sfx("cultist_chant")
def cultist_chant(r, v):
    beat = 0.42
    phrase = [(62, "o", 1), (62, "a", 1), (65, "o", 1), (64, "u", 1), (62, "a", 2)]
    total = sum(p[2] for p in phrase) * beat + 0.5
    voices = []
    for vi, (oct_shift, detune, gain) in enumerate([(-12, 0.0, 1.0), (-19, 7.0, 0.8), (-24, -5.0, 0.7)]):
        buf = np.zeros(N(total))
        tt = 0.0
        for m, vow, lenb in phrase:
            dd = lenb * beat + 0.08
            nn = N(dd)
            f = mtof(m + oct_shift) * 2 ** (detune / 1200)
            e = env_lin([(0, 0), (0.06, 1), (dd - 0.12, 0.85), (dd, 0)], nn)
            syl = voice(r, dd, f, vow, jitter=0.01, breath=0.15, vib=(5.0, 0.004), env=e)
            place(buf, syl, N(tt + r.uniform(0, 0.02)))
            place(buf, click(r, 1500, 0.01), N(tt), 0.08)
            tt += lenb * beat
        voices.append((buf, 0, gain))
    y = mix(*voices)
    return verb(y, "hall", 0.45)


@sfx("cultist_death")
def cultist_death(r, v):
    d = 1.0
    n = N(d)
    f0 = env_exp([(0, 190), (0.15, 175), (1.0, 90)], n)
    g = voice(r, d, f0, [(0, "a"), (0.5, "o"), (1, "u")], jitter=0.04, rough=0.2, breath=0.5,
              env=env_lin([(0, 0), (0.05, 1), (0.5, 0.6), (1.0, 0)], n))
    return verb(mix((sat(g, 2.0), 0, 1.0), (body_fall(r, 0), 0.55, 0.45)), "room", 0.1)


@sfx("shade_hiss")
def shade_hiss(r, v):
    d = 1.2
    n = N(d)
    hiss = nz(hp(formant(white(n, r), [(0, "i"), (0.5, "a"), (1, "a")], 1.3), 1500) * env_lin([(0, 0), (0.15, 1), (0.8, 0.7), (1.2, 0)], n))
    ghost = nz(sine(np.geomspace(1300, 850, n) * (1 + 0.01 * np.sin(TAU * 6 * tvec(n))), n) * env_swell(n, 0.4))
    low = nz(resample(hiss, 0.6))
    y = mix((hiss, 0, 1.0), (ghost, 0, 0.18), (low, 0, 0.4))
    return verb(y, "hall", 0.4)


@sfx("boss_roar")
def boss_roar(r, v):
    d = 2.6
    n = N(d)
    f0 = env_exp([(0, 48), (0.35, 68), (1.6, 60), (2.6, 42)], n)
    e = env_lin([(0, 0), (0.18, 1), (1.8, 0.85), (2.6, 0)], n)
    g1 = voice(r, d, f0, [(0, "o"), (0.2, "a"), (0.8, "a"), (1, "o")], shift=0.55, jitter=0.05,
               rough=1.0, sub=0.8, breath=0.5, env=e)
    g2 = voice(r, d, f0 * 1.51, [(0, "a"), (1, "o")], shift=0.7, jitter=0.07, rough=0.6, breath=0.6, env=e)
    flutter = nz(tvf(white(n, r), "bp", 500, 1.0) * (0.5 + 0.5 * np.sin(TAU * 27 * tvec(n))) * e)
    sub = nz(sine(38, n) * e)
    y = mix((sat(g1, 3.5), 0, 1.0), (sat(g2, 3.0), 0, 0.4), (flutter, 0, 0.35), (sub, 0, 0.5))
    return verb(lp(sat(y, 1.6), 7000), "hall", 0.3)


@sfx("boss_slam")
def boss_slam(r, v):
    y = mix((thump(r, 62, 22, 2.0, 0.1, 1.6, 3.0), 0, 1.0), (burst(r, 0.06, 500, 12000, 0.05), 0, 0.8),
            (burst(r, 0.8, 50, 600, 0.6, src="pink"), 0, 0.8), (debris(r, 1.6, 180, 0.35, 900, 4000), 0.02, 0.4),
            (metal(r, 95, 1.0, 0.6, 8, 6, 0.8), 0, 0.3))
    return verb(sat(y, 2.8), "hall", 0.28)


@sfx("boss_charge")
def boss_charge(r, v):
    d = 1.8
    n = N(d)
    x = np.clip(tvec(n) / d, 0, 1)
    rumble = nz(tvf(brown(n, r), "lp", 100 + 700 * x, 1.0) * x ** 1.2)
    growl = voice(r, d, 55 * 2 ** (x * 0.8), [(0, "u"), (0.6, "o"), (1, "a")], shift=0.6, rough=0.9, sub=0.5,
                  breath=0.4, env=x ** 1.5)
    w = whoosh(r, 0.6, 300, 2000, q=0.8, peak=0.7, body=0.6)
    y = mix((rumble, 0, 1.0), (sat(growl, 3.0), 0, 0.6), (w, d - 0.6, 0.6), (debris(r, d, 30, 2.0, 800, 3000), 0, 0.2))
    return sat(y, 1.6)


@sfx("boss_phase")
def boss_phase(r, v):
    d = 3.4
    hit = 2.55
    n = N(d)
    t = tvec(n)
    x = np.clip(t / hit, 0, 1)
    rise = 2 ** (7 * x ** 1.6 / 12)
    cl = sum(saw(mtof(m) * rise * (1 + 0.003 * k), n, r.random()) for k, m in enumerate([38, 45, 50, 51, 57, 62, 63]))
    cl = nz(tvf(cl, "lp", 250 + 5000 * x ** 2, 1.0) * x ** 2 * (t < hit))
    ch = choir(r, mtof(np.array([50, 57, 62])), hit, "a", attack=hit * 0.9, release=0.02)
    ch = ch * x[:len(ch)]
    roll = np.zeros(n)
    tt = 0.3
    while tt < hit - 0.05:
        place(roll, thump(r, 110, 70, 0.2, 0.02, 0.15, 1.4) * (0.2 + 0.8 * (tt / hit) ** 2), N(tt))
        tt += 0.22 * (1 - 0.8 * tt / hit)
    tail = mix((thump(r, 70, 26, 1.4, 0.08, 1.1, 2.5), 0, 1.0), (bellnote(r, mtof(50), 1.5, 2.0), 0, 0.6),
               (burst(r, 0.8, 2000, 14000, 0.7), 0, 0.3))
    y = mix((cl, 0, 0.7), (ch, 0, 0.45), (nz(roll), 0, 0.45), (tail, hit, 1.0))
    return verb(sat(y, 1.5), "hall", 0.35)


@sfx("elite_spawn")
def elite_spawn(r, v):
    d0 = 0.65
    swell = nz(tvf(white(N(d0), r), "bp", np.geomspace(300, 3000, N(d0)), 1.5) * np.linspace(0, 1, N(d0)) ** 3)
    cl = mix(*[(bellnote(r, mtof(m), 1.2, 1.0), 0, 0.6) for m in (62, 63, 68)])
    y = mix((swell, 0, 0.6), (thump(r, 80, 30, 1.0, 0.06, 0.8, 2.4), d0, 1.0), (cl, d0, 0.5),
            (_whisper(r, 0.9), d0 + 0.1, 0.3), (burst(r, 0.05, 800, 8000, 0.04), d0, 0.5))
    return verb(y, "hall", 0.35)


@sfx("explode")
def explode(r, v):
    return verb(sat(_explosion(r, 0.9, 1.8), 2.4), "room", 0.18)


# ============================================================================================
# WORLD
# ============================================================================================
@sfx("break_wood_1", "break_wood_2")
def break_wood(r, v):
    p = PV[v]
    spl = grains(r, 0.6, 180 * np.exp(-tvec(N(0.6)) / 0.1),
                 lambda rr, t: wood_knock(rr, rr.uniform(800, 3200) * p, rr.uniform(5, 12), rr.uniform(0.02, 0.07)), 1.5)
    y = mix((burst(r, 0.025, 900, 9000, 0.02), 0, 1.0), (thump(r, 140 * p, 60, 0.2, 0.02, 0.15), 0, 0.8),
            (wood_knock(r, 420 * p, 6, 0.15), 0, 0.7), (nz(spl), 0.005, 0.6),
            (stickslip(r, 0.06, 300, 150, ((700, 8), (1600, 10))), 0, 0.3))
    return verb(y, "room", 0.1)


@sfx("break_pottery_1", "break_pottery_2")
def break_pottery(r, v):
    p = PV[v]
    shards = grains(r, 0.7, 260 * np.exp(-tvec(N(0.7)) / 0.12),
                    lambda rr, t: ping(rr, rr.uniform(1800, 7000) * p, rr.uniform(0.02, 0.1), (1.0, 2.13, 3.37)), 1.4)
    y = mix((metal(r, 1900 * p, 0.3, 0.12, 8, 3.5, 0.5), 0, 0.7), (burst(r, 0.06, 1500, 12000, 0.05), 0, 0.8),
            (thump(r, 220 * p, 110, 0.08, 0.01, 0.06), 0, 0.5), (nz(shards), 0.005, 0.7))
    return verb(y, "room", 0.1)


@sfx("break_stone")
def break_stone(r, v):
    y = mix((burst(r, 0.04, 700, 9000, 0.03), 0, 0.9), (thump(r, 110, 40, 0.5, 0.04, 0.4, 2.3), 0, 1.0),
            (debris(r, 1.0, 200, 0.2, 1000, 4500), 0.005, 0.6), (burst(r, 0.7, 2000, 10000, 0.6, src="pink"), 0.02, 0.15))
    return verb(sat(y, 2.0), "room", 0.12)


@sfx("chest_open")
def chest_open(r, v):
    d = 0.75
    e = env_swell(N(d), 0.5, 1.2, 1.0)
    creak = stickslip(r, d, 70, 160, res=((620, 14), (1350, 18), (2900, 20)), jitter=0.3, env=e)
    y = mix((click(r, 2000, 0.01), 0, 0.5), (wood_knock(r, 1300, 8, 0.05), 0.0, 0.4), (creak, 0.08, 0.8),
            (wood_knock(r, 210, 5, 0.2), 0.95, 0.9), (thump(r, 130, 60, 0.2, 0.02, 0.15), 0.95, 0.7),
            (debris(r, 0.2, 60, 0.1, 600, 2000), 0.97, 0.2))
    return verb(y, "room", 0.12)


@sfx("door_gate")
def door_gate(r, v):
    d = 1.9
    e = env_lin([(0, 0), (0.2, 1), (1.4, 0.9), (1.9, 0)], N(d))
    creak = stickslip(r, d, 45, 65, res=((310, 25), (820, 30), (1900, 30), (3100, 30)), jitter=0.35, env=e)
    chain = grains(r, 2.0, 70, lambda rr, t: metal(rr, rr.uniform(1500, 3500), 0.12, 0.08, 5, 3.0, 0.6), 1.3)
    clank = mix((metal(r, 105, 1.4, 1.0, 12, 8, 0.5), 0, 1.0), (thump(r, 90, 35, 0.6, 0.04, 0.45, 2.4), 0, 1.0),
                (burst(r, 0.04, 800, 9000, 0.03), 0, 0.5))
    y = mix((creak, 0, 0.7), (nz(chain), 0.1, 0.3), (clank, 2.0, 1.0))
    return verb(y, "hall", 0.32)


@sfx("teleport_charge")
def teleport_charge(r, v):
    d = 1.6
    n = N(d)
    x = np.clip(tvec(n) / d, 0, 1)
    f = 110 * 2 ** (2 * x)
    tone = nz(sum(fm(f * m, 1.5, 0.5 + 3 * x, n) / (i + 1) for i, m in enumerate((1, 1.5, 2.0)))) * x ** 1.4
    sp = _glass_rise(r, d, 20 + 260 * x, 2500, 9000) * x
    hum = nz(sine(55, n) + 0.5 * sine(110.3, n)) * x
    sw = nz(tvf(white(n, r), "bp", 800 + 6000 * x ** 2, 1.2)) * x ** 2
    return verb(mix((tone, 0, 0.8), (sp, 0, 0.35), (hum, 0, 0.4), (sw, 0, 0.3)), "plate", 0.2)


@sfx("teleport_whoosh")
def teleport_whoosh(r, v):
    n = N(1.0)
    t = tvec(n)
    down = nz(fm(2000 * (200 / 2000) ** np.clip(t / 0.5, 0, 1), 1.5, 1.5, n) * env_ad(n, 0.002, 0.7))
    y = mix((whoosh(r, 0.6, 700, 5000, q=1.0, peak=0.15, rise=1.2, fall=2.0), 0, 0.9), (down, 0, 0.5),
            (burst(r, 0.04, 400, 5000, 0.03), 0, 0.6), (sparkle(r, 0.9, 150 * np.exp(-tvec(N(0.9)) / 0.3), 4000, 11000), 0, 0.4),
            (thump(r, 120, 45, 0.4, 0.03, 0.3), 0, 0.5))
    return verb(y, "plate", 0.22)


@sfx("teleporter_hum", loop=True)
def teleporter_hum(r, v):
    Ls = 4.0
    L = N(Ls)
    t = tvec(L)
    lfo1 = 0.5 + 0.5 * np.sin(TAU * 0.5 * t)
    lfo2 = 0.5 + 0.5 * np.sin(TAU * 0.25 * t + 1.0)
    hum = sine(55, L) + 0.6 * sine(110, L) + 0.3 * sine(165, L) * lfo1 + 0.2 * sine(220, L) * lfo2
    shimmer = (np.sin(TAU * 440 * t + (1.5 + lfo1) * np.sin(TAU * 660 * t))) * 0.15 * lfo2
    xf = N(0.3)
    sp = sparkle(r, Ls + 0.3, 25, 3000, 9000)
    sp = loop_crossfade(sp, L, xf)
    return mix((nz(hum), 0, 1.0), (shimmer, 0, 1.0), (nz(sp), 0, 0.15))


def _fireloop(r, Ls, cutoff, crackle_rate, pop_rate, roar=1.0):
    L, xf = N(Ls), N(0.6)
    n = L + xf
    fl = flame(r, n, cutoff, 3.0)
    cr = crackle(r, n, crackle_rate, 1500, 9000)
    pops = grains(r, n / SR, pop_rate, lambda rr, t: mix((wood_knock(rr, rr.uniform(500, 1500), 4, 0.03), 0, 1.0),
                                       (thump(rr, 150, 80, 0.05, 0.005, 0.04, 0), 0, 0.5)), 1.2)
    y = mix((fl, 0, roar), (cr, 0, 0.6), (nz(pops), 0, 0.35))
    return loop_crossfade(y, L, xf)


@sfx("torch_crackle", loop=True)
def torch_crackle(r, v):
    return _fireloop(r, 6.0, 450, 30, 1.2, 0.8)


@sfx("fire_campfire", loop=True)
def fire_campfire(r, v):
    return _fireloop(r, 8.0, 800, 60, 2.5, 1.0)


# ============================================================================================
# LOOT / PROGRESSION
# ============================================================================================
@sfx("loot_drop")
def loot_drop(r, v):
    y = mix((thump(r, 220, 100, 0.12, 0.012, 0.08), 0, 0.8), (metal(r, 1400, 0.4, 0.28, 7, 4, 0.6), 0, 0.5),
            (bellnote(r, mtof(96), 0.6, 0.45), 0.02, 0.3), (debris(r, 0.1, 150, 0.03, 1500, 4000), 0, 0.2))
    return verb(y, "room", 0.12)


@sfx("loot_drop_rare")
def loot_drop_rare(r, v):
    y = mix((thump(r, 220, 100, 0.12, 0.012, 0.08), 0, 0.7),
            *[(bellnote(r, mtof(m), 1.1, 0.9), 0.05 + 0.07 * i, 0.7) for i, m in enumerate((88, 95, 100))],
            (sparkle(r, 1.0, 70, 5000, 11000), 0.05, 0.3))
    return verb(y, "plate", 0.3)


@sfx("loot_drop_legendary")
def loot_drop_legendary(r, v):
    d = 2.2
    chord = [50, 57, 62, 66, 69]
    br = mix(*[(brass(r, mtof(m), 1.9, swell=0.25, bright=0.9, rel=0.9), 0.1, 1.0) for m in chord[:3]])
    ch = choir(r, mtof(np.array([62, 66, 69, 74])), 2.0, "ah", attack=0.3, release=1.0)
    arp = mix(*[(bellnote(r, mtof(m), 1.8, 1.5), 0.12 + 0.09 * i, 0.7) for i, m in enumerate((86, 90, 93, 98, 102))])
    sp = sparkle(r, d, 140 * env_swell(N(d), 0.35, 1.0, 1.5), 5000, 12000)
    y = mix((thump(r, 80, 35, 1.0, 0.06, 0.8, 2.0), 0, 0.8), (br, 0, 0.55), (ch, 0.08, 0.35), (arp, 0, 0.65),
            (nz(sp), 0, 0.35), (swell_noise(r, 1.6, 4000, 14000, 0.3, 1.5, 1.5), 0, 0.15))
    return verb(y, "hall", 0.35)


@sfx("gold_pickup")
def gold_pickup(r, v):
    y = mix(*[(ping(r, r.uniform(2600, 4300), r.uniform(0.12, 0.3), (1.0, 2.4, 4.1, 5.9)),
               r.uniform(0, 0.22), r.uniform(0.4, 1.0)) for _ in range(7)])
    return verb(y, "room", 0.1)


@sfx("item_pickup")
def item_pickup(r, v):
    y = mix((swell_noise(r, 0.14, 400, 3500, 0.35), 0, 0.7), (click(r, 1500, 0.01), 0.05, 0.4),
            (thump(r, 200, 110, 0.07, 0.01, 0.05), 0.05, 0.5), (wood_knock(r, 1100, 6, 0.04), 0.05, 0.3))
    return verb(y, "room", 0.08)


@sfx("potion_drink")
def potion_drink(r, v):
    n = N(0.06)
    pop = nz(sine(np.geomspace(400, 1400, n), n) * env_ad(n, 0.0005, 0.05))
    gulps = []
    for i, st in enumerate((0.3, 0.58, 0.84)):
        m = N(0.16)
        g = nz(tvf(white(m, r), "bp", np.geomspace(260, 520, m) * (1 + 0.1 * i), 7.0) * env_swell(m, 0.3))
        gulps.append((mix((g, 0, 1.0), (thump(r, 160, 90, 0.1, 0.015, 0.08), 0.03, 0.5)), st, 0.8))
    y = mix((click(r, 1500, 0.006), 0, 0.5), (pop, 0, 0.6), *gulps, (ping(r, 3400, 0.3, (1.0, 2.7, 5.1)), 1.1, 0.4))
    return verb(y, "room", 0.1)


@sfx("level_up")
def level_up(r, v):
    notes = [62, 66, 69, 74]  # D4 F#4 A4 D5
    br = mix(*[(brass(r, mtof(m), 2.0 - 0.13 * i, swell=0.06, bright=1.0, rel=0.7), 0.13 * i, 0.8)
               for i, m in enumerate(notes)],
             (brass(r, mtof(50), 1.5, swell=0.3, bright=0.6, rel=0.7), 0.4, 0.6))
    bells = mix(*[(bellnote(r, mtof(m + 24), 1.6, 1.5), 0.13 * i, 0.6) for i, m in enumerate(notes + [76])])
    ch = choir(r, mtof(np.array([62, 69, 74, 78])), 1.8, "ah", attack=0.4, release=0.9)
    sp = _glass_rise(r, 1.6, 120, 3000, 10000)
    y = mix((thump(r, 90, 40, 0.8, 0.05, 0.6, 2.0), 0, 0.7), (br, 0, 0.75), (bells, 0, 0.55), (ch, 0.3, 0.35),
            (sp, 0.1, 0.25), (swell_noise(r, 1.2, 5000, 14000, 0.4, 1.5, 1.5), 0.4, 0.12))
    return verb(y, "hall", 0.3)


@sfx("skill_unlock")
def skill_unlock(r, v):
    y = mix((bellnote(r, mtof(81), 1.2, 1.2), 0, 0.7), (bellnote(r, mtof(88), 1.2, 1.2), 0.14, 0.8),
            (sparkle(r, 1.0, 90, 5000, 11000), 0.1, 0.3), (whoosh(r, 0.4, 1500, 5000, q=1.0, peak=0.8), 0, 0.25))
    return verb(y, "plate", 0.3)


@sfx("talent_unlock")
def talent_unlock(r, v):
    y = mix((thump(r, 85, 35, 0.8, 0.06, 0.6, 2.0), 0, 0.8),
            *[(bellnote(r, mtof(m), 1.4, 1.4), 0.02 * i, 0.6) for i, m in enumerate((62, 69, 74, 77))],
            (choir(r, mtof(np.array([50, 57, 62])), 1.2, "o", attack=0.05, release=0.8), 0, 0.3),
            (sparkle(r, 1.0, 60, 4000, 10000), 0.05, 0.25))
    return verb(y, "hall", 0.3)


# ============================================================================================
# UI
# ============================================================================================
@sfx("ui_hover")
def ui_hover(r, v):
    n = N(0.07)
    y = mix((sine(2600, n) * env_ad(n, 0.001, 0.045) + 0.3 * sine(5200, n) * env_ad(n, 0.001, 0.02), 0, 0.6),
            (click(r, 5000, 0.003), 0, 0.2))
    return y


@sfx("ui_click")
def ui_click(r, v):
    y = mix((wood_knock(r, 1800, 6, 0.05), 0, 0.8), (click(r, 3000, 0.004), 0, 0.6),
            (thump(r, 320, 180, 0.04, 0.005, 0.03, 0), 0, 0.4))
    return verb(y, "room", 0.05)


def _paper(r, d, flutter=35.0):
    n = N(d)
    am = 0.4 + 0.6 * np.abs(nz(lp(white(n, r), flutter)))
    return nz(bp(white(n, r), 3000, 0.6) * am * env_swell(n, 0.4, 1.2, 1.5))


@sfx("ui_open")
def ui_open(r, v):
    y = mix((_paper(r, 0.3), 0, 0.7), (whoosh(r, 0.3, 300, 1200, q=0.8, peak=0.5, src="pink"), 0, 0.4),
            (sine(1320, N(0.25)) * env_ad(N(0.25), 0.002, 0.2) + 0.5 * sine(1980, N(0.25)) * env_ad(N(0.25), 0.002, 0.15), 0.18, 0.2))
    return verb(y, "room", 0.08)


@sfx("ui_close")
def ui_close(r, v):
    y = mix((whoosh(r, 0.22, 1400, 300, q=0.8, peak=0.3, src="pink"), 0, 0.6), (_paper(r, 0.15), 0, 0.4),
            (thump(r, 170, 90, 0.1, 0.015, 0.08), 0.16, 0.6))
    return verb(y, "room", 0.08)


@sfx("ui_equip")
def ui_equip(r, v):
    y = mix((swell_noise(r, 0.12, 400, 3000, 0.4), 0, 0.5), (metal(r, 950, 0.35, 0.22, 7, 4, 0.6), 0.07, 0.7),
            (thump(r, 200, 100, 0.08, 0.01, 0.06), 0.07, 0.5))
    return verb(y, "room", 0.08)


@sfx("ui_unequip")
def ui_unequip(r, v):
    m = N(0.15)
    scrape = nz(tvf(white(m, r), "bp", np.geomspace(4000, 1500, m), 4.0) * env_swell(m, 0.3))
    y = mix((scrape, 0, 0.6), (metal(r, 1250, 0.25, 0.15, 6, 4, 0.7), 0.1, 0.45), (swell_noise(r, 0.1, 400, 2500, 0.4), 0.12, 0.3))
    return verb(y, "room", 0.08)


@sfx("ui_error")
def ui_error(r, v):
    out = []
    for i, f in enumerate((185, 139)):
        n = N(0.13)
        x = lp(square(f, n, 0.35) + 0.5 * saw(f * 1.005, n), 1300) * env_lin([(0, 0), (0.005, 1), (0.1, 0.8), (0.13, 0)], n)
        out.append((nz(x), 0.14 * i, 1.0))
    return mix(*out)


@sfx("ui_page")
def ui_page(r, v):
    return mix((_paper(r, 0.32, 55.0), 0, 0.8), (whoosh(r, 0.25, 600, 2500, q=0.7, peak=0.5), 0.03, 0.3))
