"""The four music loops, written as actual compositions (progressions, melodies, sections).

music_menu    D minor, 66 BPM 4/4, 32 bars  : Intro | A (lute motif) | B (strings) | A' (tutti) | Outro
music_town    A minor, 78 BPM 3/4, 48 bars  : Intro | A (flute) | A2 | B (strings, relative major) | A3 | C (cello) | Outro
music_dungeon C phrygian, 88 BPM 4/4, 44 bars: Intro | A (pulse+keys) | B (+ostinato) | C (build) | D (breakdown) | A'
music_boss    E minor, 140 BPM 4/4, 64 bars : Intro | A (ostinato+stabs) | B (brass theme) | C (choir breakdown) | D (climax) | T
music_legend  D minor, 72 BPM 4/4, 40 bars  : Intro (heartbeat, choir) | A (cello lament) | B (horn theme) | C (choir, betrayal) | B' (tutti) | Outro

Loops are seamless by construction: every note is written into a buffer that wraps modulo the
loop length (tails that ring past the end continue at the start), reverb is a circular
convolution and the master dynamics run in wrap mode (see instruments.Song.render).
"""
from __future__ import annotations

import zlib

import numpy as np

import instruments as I
from instruments import Song, bass_of, nm, song_ir, voicing
from synth import SR, circ, filt, hp, lp, mtof, N

TRACKS = ["music_menu", "music_town", "music_dungeon", "music_boss", "music_legend"]


def seed_of(name):
    return zlib.crc32(name.encode()) & 0x7FFFFFFF


# --------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------
def play_mel(s, bus, inst, bar0, mel, vel=0.8, pan=0.0, transpose=0, gain=1.0, legato=1.0, **kw):
    for i, barnotes in enumerate(mel):
        for (b, d, name) in barnotes:
            m = nm(name) + transpose
            v = vel * (1 + s.r.uniform(-0.06, 0.06)) * (1.08 if b == 0 else 1.0)
            x = inst(s.r, float(mtof(m)), s.beats(d) * legato, min(v, 1.0), **kw)
            s.add(bus, x, s.t(bar0 + i, b), gain, pan)


def merged(prog):
    """[(chord, start_index, length_in_bars)] merging repeated chords."""
    out = []
    for i, c in enumerate(prog):
        if out and out[-1][0] == c:
            out[-1][2] += 1
        else:
            out.append([c, i, 1])
    return out


def play_pads(s, bus, prog, bar0, vel, low=50, inst=I.pad, pan_spread=0.6, early=0.3, **kw):
    for ch, i, nb in merged(prog):
        tones = voicing(ch, low)
        for j, m in enumerate(tones):
            x = inst(s.r, float(mtof(m)), s.beats(s.meter * nb) + early, vel, **kw)
            p = pan_spread * ((j / max(len(tones) - 1, 1)) * 2 - 1)
            s.add(bus, x, s.t(bar0 + i) - early, 1.0, p, humanize=0)


def play_bass(s, bus, prog, bar0, vel, low=36, inst=I.cello, merge=True, **kw):
    items = merged(prog) if merge else [[c, i, 1] for i, c in enumerate(prog)]
    for ch, i, nb in items:
        x = inst(s.r, float(mtof(bass_of(ch, low))), s.beats(s.meter * nb), vel, **kw)
        s.add(bus, x, s.t(bar0 + i), 1.0, 0.0)


def arp(s, bus, inst, prog, bar0, pattern, step, vel=0.6, low=50, pan=0.0, accent=(0,), gain=1.0, **kw):
    """Arpeggiate chords: pattern = indexes into [root, 3rd, 5th, 8ve, 10th, 12th]."""
    for i, ch in enumerate(prog):
        pc, q = I.parse_chord(ch)
        root = low + ((pc - low) % 12)
        tones = I.chord_tones(root, q)[:3]
        ext = tones + [t + 12 for t in tones]
        for k, idx in enumerate(pattern):
            beat = k * step
            if beat >= s.meter:
                break
            v = vel * (1.15 if beat in accent else 1.0) * (1 + s.r.uniform(-0.08, 0.08))
            x = inst(s.r, float(mtof(ext[idx])), s.beats(step * 1.5), min(v, 1.0), **kw)
            s.add(bus, x, s.t(bar0 + i, beat), gain, pan)


def hit(s, bus, fn, bar, beat=0.0, vel=1.0, pan=0.0, **kw):
    s.add(bus, fn(s.r, vel, **kw), s.t(bar, beat), 1.0, pan, humanize=0.003)


def swell_into(s, bus, bar, dur=1.6, vel=0.5):
    x = I.swell_cym(s.r, dur, vel)
    s.add(bus, x, s.t(bar) - len(x) / SR, 1.0, 0.0, humanize=0)


# --------------------------------------------------------------------------------------------
# MENU - "Ashes of the Old Crown"
# --------------------------------------------------------------------------------------------
MENU_A = [
    [(0, 1.5, "A4"), (1.5, 0.5, "D5"), (2, 1, "E5"), (3, 1, "F5")],
    [(0, 1.5, "E5"), (1.5, 0.5, "D5"), (2, 2, "D5")],
    [(0, 1, "G4"), (1, 1, "Bb4"), (2, 1.5, "D5"), (3.5, 0.5, "C5")],
    [(0, 2, "C#5"), (2, 2, "A4")],
    [(0, 1.5, "A4"), (1.5, 0.5, "D5"), (2, 1, "E5"), (3, 1, "F5")],
    [(0, 1.5, "A5"), (1.5, 0.5, "G5"), (2, 1, "F5"), (3, 1, "E5")],
    [(0, 1, "D5"), (1, 1, "Bb4"), (2, 1, "G4"), (3, 1, "E5")],
    [(0, 1, "E5"), (1, 1, "C#5"), (2, 2, "A4")],
]
MENU_B = [
    [(0, 3, "F5"), (3, 1, "D5")],
    [(0, 2, "C5"), (2, 1, "A4"), (3, 1, "C5")],
    [(0, 2, "Bb4"), (2, 2, "D5")],
    [(0, 4, "A4")],
    [(0, 2, "F5"), (2, 1, "G5"), (3, 1, "A5")],
    [(0, 2, "G5"), (2, 2, "E5")],
    [(0, 2, "C#5"), (2, 2, "E5")],
    [(0, 2, "A5"), (2, 1, "G5"), (3, 1, "E5")],
]
MENU_B_CELLO = [
    [(0, 4, "Bb2")], [(0, 2, "A2"), (2, 2, "F2")], [(0, 4, "G2")], [(0, 2, "D3"), (2, 2, "F3")],
    [(0, 4, "Bb2")], [(0, 2, "C3"), (2, 2, "E3")], [(0, 4, "A2")], [(0, 2, "A2"), (2, 2, "C#3")],
]
MENU_OUTRO = [
    [(0, 1.5, "A4"), (1.5, 0.5, "D5"), (2, 1, "E5"), (3, 1, "F5")],
    [(0, 4, "E5")], [(0, 4, "D5")], [(0, 4, "C#5")],
]


def music_menu(r):
    s = Song(r, bpm=66, bars=32, meter=4)
    s.bus("pad", 0.34, 0.45, eq=lambda z: lp(z, 4500))
    s.bus("bass", 0.5, 0.25, eq=lambda z: lp(z, 1500))
    s.bus("lute", 1.9, 0.3)
    s.bus("harp", 0.9, 0.45)
    s.bus("str", 0.6, 0.45)
    s.bus("choir", 0.45, 0.6)
    s.bus("bell", 0.9, 0.6)
    s.bus("perc", 0.9, 0.35)
    s.bus("sub", 0.2, 0.0)

    intro = ["Dm", "Bb", "Gm", "A"]
    progA = ["Dm", "Bb", "Gm", "A", "Dm", "F", "Gm", "A"]
    progB = ["Bb", "F", "Gm", "Dm", "Bb", "C", "A", "A"]
    form = intro + progA + progB + progA + intro

    # pads + sub drone across the whole loop, dynamics by section
    vel = [0.45] * 4 + [0.5] * 8 + [0.62] * 8 + [0.7] * 8 + [0.45] * 4
    for i, ch in enumerate(form):
        play_pads(s, "pad", [ch], i, vel[i], low=50)
        x = I.sub(r, float(mtof(bass_of(ch, 26))), s.beats(4), 0.6, attack=0.8, release=1.2)
        s.add("sub", x, s.t(i), 1.0, 0.0, humanize=0)
    # cello bass from A onwards
    play_bass(s, "bass", progA, 4, 0.45, low=38)
    play_mel(s, "bass", I.cello, 12, MENU_B_CELLO, 0.55, pan=-0.2)
    play_bass(s, "bass", progA, 20, 0.6, low=38)

    # intro: bells + harp shimmer
    for b, note in [(0, "D5"), (1, "F5"), (2, "D5"), (3, "C#5")]:
        s.add("bell", I.bell(r, float(mtof(nm(note))), 3.0, 0.5, 3.5), s.t(b), 1.0, 0.3)
    arp(s, "harp", I.harp, intro, 0, [0, 1, 2, 3], 1.0, vel=0.35, low=62, pan=0.4)

    # A: lute motif, harp quarter arps
    play_mel(s, "lute", I.lute, 4, MENU_A, 0.85, pan=-0.1)
    arp(s, "harp", I.harp, progA, 4, [0, 2, 3, 4], 1.0, vel=0.3, low=57, pan=0.45)

    # B: strings melody, lute eighth-note arps, choir, soft taiko
    play_mel(s, "str", I.strings, 12, MENU_B, 0.75, pan=0.15, attack=0.18, release=0.7, bright=0.55)
    arp(s, "lute", I.lute, progB, 12, [0, 1, 2, 3, 2, 1, 2, 3], 0.5, vel=0.45, low=50, pan=-0.3)
    for i, ch in enumerate(progB):
        s.add("choir", I.choir(r, mtof(np.array(voicing(ch, 55))), s.beats(4), 0.5, "o", 0.9, 1.4), s.t(12 + i),
              1.0, 0.0, humanize=0)
    for i in range(0, 8, 2):
        hit(s, "perc", I.taiko, 12 + i, 0, 0.55)
    swell_into(s, "perc", 20, 1.6, 0.45)

    # A': tutti - lute + strings an octave below as doubling, choir, bells on phrase heads
    hit(s, "perc", I.boom, 20, 0, 0.8)
    play_mel(s, "lute", I.lute, 20, MENU_A, 0.95, pan=-0.1)
    play_mel(s, "str", I.strings, 20, MENU_A, 0.5, pan=0.2, transpose=-12, attack=0.12, release=0.6, bright=0.45)
    arp(s, "harp", I.harp, progA, 20, [0, 1, 2, 3, 4, 3, 2, 1], 0.5, vel=0.28, low=62, pan=0.5)
    for i, ch in enumerate(progA):
        s.add("choir", I.choir(r, mtof(np.array(voicing(ch, 57))), s.beats(4), 0.6, "a", 0.7, 1.4), s.t(20 + i),
              1.0, 0.0, humanize=0)
        hit(s, "perc", I.taiko, 20 + i, 0, 0.6 if i % 2 == 0 else 0.4)
        hit(s, "perc", I.frame_drum, 20 + i, 2.5, 0.25)
    for i in (0, 2, 4, 6):
        note = MENU_A[i][0][2]
        s.add("bell", I.bell(r, float(mtof(nm(note) + 12)), 2.5, 0.35, 2.5), s.t(20 + i), 1.0, 0.35)

    # outro: motif fragment, thinning to the loop point
    play_mel(s, "lute", I.lute, 28, MENU_OUTRO, 0.6, pan=-0.1)
    s.add("bell", I.bell(r, float(mtof(nm("A4"))), 3.0, 0.35, 3.5), s.t(31), 1.0, -0.3)
    return s.render(song_ir("menu"))


# --------------------------------------------------------------------------------------------
# TOWN - "Hearth of Greyhollow"
# --------------------------------------------------------------------------------------------
TOWN_A = [
    [(0, 1.5, "E5"), (1.5, 0.5, "D5"), (2, 1, "C5")],
    [(0, 2, "A4"), (2, 1, "C5")],
    [(0, 1, "G4"), (1, 1, "C5"), (2, 1, "E5")],
    [(0, 3, "D5")],
    [(0, 1.5, "E5"), (1.5, 0.5, "F5"), (2, 1, "E5")],
    [(0, 1.5, "D5"), (1.5, 0.5, "C5"), (2, 1, "A4")],
    [(0, 1, "B4"), (1, 1, "G#4"), (2, 1, "B4")],
    [(0, 3, "E5")],
]
TOWN_A2_END = [[(0, 1, "B4"), (1, 1, "D5"), (2, 1, "G#4")], [(0, 3, "A4")]]
TOWN_B = [
    [(0, 2, "G5"), (2, 1, "E5")],
    [(0, 2, "D5"), (2, 1, "B4")],
    [(0, 1, "C5"), (1, 1, "E5"), (2, 1, "A5")],
    [(0, 3, "G5")],
    [(0, 1.5, "A5"), (1.5, 0.5, "G5"), (2, 1, "F5")],
    [(0, 2, "E5"), (2, 1, "C5")],
    [(0, 1, "D5"), (1, 1, "F5"), (2, 1, "A5")],
    [(0, 3, "G#5")],
]
TOWN_B_FLUTE = [
    [(0, 3, "E5")], [(0, 3, "D5")], [(0, 3, "C5")], [(0, 3, "B4")],
    [(0, 3, "C5")], [(0, 3, "G4")], [(0, 3, "A4")], [(0, 1.5, "B4"), (1.5, 1.5, "E5")],
]
TOWN_C = [
    [(0, 2, "A3"), (2, 1, "C4")],
    [(0, 2, "B3"), (2, 1, "D4")],
    [(0, 1.5, "E4"), (1.5, 0.5, "D4"), (2, 1, "B3")],
    [(0, 3, "C4")],
    [(0, 2, "F4"), (2, 1, "E4")],
    [(0, 1, "C4"), (1, 1, "B3"), (2, 1, "A3")],
    [(0, 2, "G#3"), (2, 1, "B3")],
    [(0, 3, "E4")],
]


def music_town(r):
    s = Song(r, bpm=78, bars=48, meter=3)
    s.bus("lute", 1.0, 0.25)
    s.bus("flute", 0.4, 0.35)
    s.bus("str", 0.55, 0.35)
    s.bus("pad", 0.32, 0.4, eq=lambda z: lp(z, 4000))
    s.bus("bass", 0.5, 0.2, eq=lambda z: lp(z, 1800))
    s.bus("harp", 0.9, 0.4)
    s.bus("perc", 1.1, 0.25)
    s.bus("bell", 1.0, 0.5)

    intro = ["Am", "F", "C", "E"]
    progA = ["Am", "F", "C", "G", "Am", "Dm", "E", "E"]
    progB = ["C", "G", "Am", "Em", "F", "C", "Dm", "E"]
    progC = ["F", "G", "Em", "Am", "Dm", "Am", "E", "E"]
    outro = ["Am", "F", "Dm", "E"]
    form = intro + progA + progA + progB + progA + progC + outro
    lute_vel = [0.55] * 4 + [0.5] * 8 + [0.5] * 8 + [0.55] * 8 + [0.55] * 8 + [0.45] * 8 + [0.5] * 4

    # fingerpicked lute in 3/4 throughout: bass, then 8th-note broken chord
    for i, ch in enumerate(form):
        pc, q = I.parse_chord(ch)
        root = 45 + ((pc - 45) % 12)
        tones = I.chord_tones(root, q)[:3]
        seq = [(0.0, tones[0] - 12, 1.1), (0.5, tones[2], 0.8), (1.0, tones[0] + 12, 0.9), (1.5, tones[1] + 12, 0.8),
               (2.0, tones[2] + 12, 0.85), (2.5, tones[1] + 12, 0.75)]
        for beat, m, acc in seq:
            v = lute_vel[i] * acc * (1 + r.uniform(-0.08, 0.08))
            s.add("lute", I.lute(r, float(mtof(m)), s.beats(1.0), min(v, 1.0)), s.t(i, beat), 1.0, -0.25 + 0.1 * (m % 3))

    # A: flute
    play_mel(s, "flute", I.flute, 4, TOWN_A, 0.75, pan=0.2)
    # A2: flute + pad + cello bass
    play_mel(s, "flute", I.flute, 12, TOWN_A[:6] + TOWN_A2_END, 0.8, pan=0.2)
    play_pads(s, "pad", progA, 12, 0.4, low=52)
    play_bass(s, "bass", progA, 12, 0.5, low=33, merge=False)
    # B: strings melody (relative major), flute counterline, frame drum + shaker
    play_mel(s, "str", I.strings, 20, TOWN_B, 0.75, pan=-0.15, attack=0.15, release=0.6, bright=0.5)
    play_mel(s, "flute", I.flute, 20, TOWN_B_FLUTE, 0.45, pan=0.35)
    play_pads(s, "pad", progB, 20, 0.45, low=52)
    play_bass(s, "bass", progB, 20, 0.55, low=33, merge=False)
    for i in range(8):
        hit(s, "perc", I.frame_drum, 20 + i, 0, 0.55)
        hit(s, "perc", I.frame_drum, 20 + i, 2, 0.25)
        for k in range(6):
            hit(s, "perc", I.shaker, 20 + i, k * 0.5, 0.18 if k % 2 else 0.25, pan=0.4)
    s.add("bell", I.bell(r, float(mtof(nm("E6"))), 3.0, 0.4, 3.0), s.t(20), 1.0, 0.4)
    # A3: flute melody, harp countermelody, fuller
    play_mel(s, "flute", I.flute, 28, TOWN_A[:6] + TOWN_A2_END, 0.85, pan=0.2)
    arp(s, "harp", I.harp, progA, 28, [3, 4, 5, 4, 3, 2], 0.5, vel=0.35, low=57, pan=0.45)
    play_pads(s, "pad", progA, 28, 0.5, low=52)
    play_bass(s, "bass", progA, 28, 0.6, low=33, merge=False)
    for i in range(8):
        hit(s, "perc", I.frame_drum, 28 + i, 0, 0.5)
        hit(s, "perc", I.frame_drum, 28 + i, 2, 0.22)
    s.add("bell", I.bell(r, float(mtof(nm("A5"))), 3.0, 0.35, 3.0), s.t(28), 1.0, -0.4)
    # C: solo cello over a soft pad (the melancholic bridge)
    play_mel(s, "str", I.cello, 36, TOWN_C, 0.8, pan=-0.1, attack=0.2, release=0.6)
    play_pads(s, "pad", progC, 36, 0.35, low=52)
    # outro: flute fragment
    play_mel(s, "flute", I.flute, 44, [TOWN_A[0], TOWN_A[1], [(0, 3, "F4")], [(0, 3, "G#4")]], 0.55, pan=0.2)
    return s.render(song_ir("town"))


# --------------------------------------------------------------------------------------------
# DUNGEON - "The Drowned Catacombs"
# --------------------------------------------------------------------------------------------
DUN_KEYS = [
    [(0, 1, "C4"), (1, 1, "Db4"), (2, 2, "Eb4")],
    [(0, 1.5, "Db4"), (1.5, 0.5, "C4"), (2, 2, "G3")],
    [(0, 2, "F4"), (2, 1, "Eb4"), (3, 1, "Db4")],
    [(0, 4, "C4")],
    [(0, 1, "G4"), (1, 1, "Ab4"), (2, 2, "G4")],
    [(0, 1, "F4"), (1, 1, "Eb4"), (2, 2, "C4")],
    [(0, 2, "B3"), (2, 2, "D4")],
    [(0, 4, "G3")],
]
DUN_HIGH = [
    [(0, 4, "G5")], [(0, 4, "Ab5")], [(0, 2, "G5"), (2, 2, "Eb5")], [(0, 4, "F5")],
    [(0, 2, "Eb5"), (2, 2, "C5")], [(0, 4, "D5")], [(0, 2, "Eb5"), (2, 2, "F5")], [(0, 4, "B4")],
]


def music_dungeon(r):
    s = Song(r, bpm=88, bars=44, meter=4)
    s.bus("drone", 0.28, 0.3, eq=lambda z: lp(z, 900))
    s.bus("pad", 0.35, 0.5, eq=lambda z: lp(z, 2500))
    s.bus("pulse", 0.9, 0.2)
    s.bus("tick", 2.0, 0.5)
    s.bus("ost", 0.45, 0.3)
    s.bus("keys", 1.0, 0.55)
    s.bus("high", 0.25, 0.7)
    s.bus("brass", 0.55, 0.4)
    s.bus("choir", 0.45, 0.6)
    s.bus("fx", 0.7, 0.6)

    intro = ["Cm"] * 4
    progA = ["Cm", "Cm", "Db", "Cm", "Cm", "Ab", "G", "G"]
    progC = ["Cm", "Db", "Cm", "Db", "Ab", "G", "Ab", "G"]
    progD = ["Cm", "Cm", "Cm", "Cm", "Db", "Db", "G", "G"]
    form = intro + progA + progA + progC + progD + progA

    # drone: C2 sub + low cello, re-articulated every 4 bars with slow swells
    for b in range(0, 44, 4):
        s.add("drone", I.sub(r, float(mtof(36)), s.beats(16), 0.7, attack=2.0, release=3.0), s.t(b), 1.0, 0.0,
              humanize=0)
        s.add("drone", I.cello(r, float(mtof(36)), s.beats(16), 0.4, attack=2.5, release=3.0), s.t(b), 1.0, -0.2,
              humanize=0)
    # dark pads following the harmony
    play_pads(s, "pad", form, 0, 0.45, low=48, bright=0.12)

    # bell tolls at phrase heads
    for b in (0, 12, 20, 36):
        s.add("fx", I.bell(r, float(mtof(48)), 5.0, 0.7, 5.0), s.t(b), 1.0, -0.3, humanize=0)

    # heartbeat pulse
    for b in range(4, 28):
        hit(s, "pulse", I.heartbeat, b, 0, 0.8)
        hit(s, "pulse", I.heartbeat, b, 2, 0.55)
    for b in range(28, 36):
        hit(s, "pulse", I.heartbeat, b, 0, 0.55)
    for b in range(36, 44):
        hit(s, "pulse", I.heartbeat, b, 0, 0.75)
        hit(s, "pulse", I.heartbeat, b, 2, 0.5)

    # keys melody in A and A' (A' an octave lower and softer on its second half)
    play_mel(s, "keys", I.keys, 4, DUN_KEYS, 0.6, pan=0.2)
    play_mel(s, "keys", I.keys, 36, DUN_KEYS[:4], 0.5, pan=0.2)
    play_mel(s, "keys", I.keys, 40, DUN_KEYS[4:], 0.45, pan=0.2, transpose=-12)

    # B + C + A': ticking eighths, spiccato ostinato
    osti = [0, 0, 1, 0, 0, 0, -1, 0]
    for b in list(range(12, 28)) + list(range(36, 42)):
        ch = form[b]
        pc, _ = I.parse_chord(ch)
        root = 43 + ((pc - 43) % 12)
        amp = 0.6 if b < 20 else (0.75 if b < 28 else 0.45)
        for k in range(8):
            m = root + osti[k]
            s.add("ost", I.spiccato(r, float(mtof(m)), s.beats(0.5), amp * (1.0 if k % 4 == 0 else 0.7), bright=0.45),
                  s.t(b, k * 0.5), 1.0, -0.3)
            hit(s, "tick", I.tick, b, k * 0.5, 0.35 if k % 2 == 0 else 0.2, pan=0.55, f=2600 if k % 2 == 0 else 3100)
    for b in (12, 16, 20, 24):
        hit(s, "fx", I.anvil, b, 0, 0.35, pan=0.6)

    # high dissonant swells every 4 bars from A on
    for j, b in enumerate(range(4, 44, 4)):
        if 28 <= b < 36:
            continue
        pair = [(79, 80), (84, 85), (74, 75), (79, 80)][j % 4]
        for m, p in zip(pair, (-0.6, 0.6)):
            s.add("high", I.strings(r, float(mtof(m)), s.beats(10), 0.35, attack=3.0, release=2.5, bright=0.7,
                                    voices=3, block=128), s.t(b), 1.0, p, humanize=0)

    # C: build - high string line, low brass swells, choir, tom 8ths
    play_mel(s, "high", I.strings, 20, DUN_HIGH, 0.7, pan=0.0, attack=0.5, release=1.0, bright=0.5)
    for b in (21, 23, 25, 27):
        s.add("brass", I.brassn(r, float(mtof(bass_of(form[b], 31))), s.beats(4), 0.6, swell=1.2, release=0.5,
                                bright=0.6, growl=0.2), s.t(b), 1.0, 0.0, humanize=0)
    for i, ch in enumerate(progC):
        s.add("choir", I.choir(r, mtof(np.array(voicing(ch, 48))), s.beats(4), 0.55, "u", 1.0, 1.5), s.t(20 + i), 1.0,
              0.0, humanize=0)
        for k in (1, 3, 5, 7):
            hit(s, "pulse", I.tom, 20 + i, k * 0.5, 0.25 + 0.04 * i, pitch=0.8)
    swell_into(s, "fx", 20, 2.0, 0.4)
    s.add("fx", I.boom(r, 0.7), s.t(20), 1.0, 0.0, humanize=0)

    # D: breakdown - drip-like pizzicato in C phrygian over halftime pulse
    scale = [60, 61, 63, 65, 67, 68, 70, 72, 73, 75]
    for b in range(28, 36):
        for k in range(8):
            if r.random() < 0.3:
                m = int(r.choice(scale))
                s.add("keys", I.pizz(r, float(mtof(m)), 0.3, r.uniform(0.3, 0.55)), s.t(b, k * 0.5), 1.0,
                      r.uniform(-0.7, 0.7))
    swell_into(s, "fx", 36, 2.0, 0.4)
    s.add("fx", I.boom(r, 0.6), s.t(36), 1.0, 0.0, humanize=0)
    return s.render(song_ir("dungeon"))


# --------------------------------------------------------------------------------------------
# BOSS - "Crown of Cinders"
# --------------------------------------------------------------------------------------------
BOSS_THEME = [
    [(0, 1.5, "E4"), (1.5, 0.5, "G4"), (2, 2, "B4")],
    [(0, 1, "A4"), (1, 1, "G4"), (2, 1, "F#4"), (3, 1, "G4")],
    [(0, 2, "E4"), (2, 1, "G4"), (3, 1, "E4")],
    [(0, 4, "C4")],
    [(0, 1.5, "A3"), (1.5, 0.5, "C4"), (2, 2, "E4")],
    [(0, 2, "A4"), (2, 1, "G4"), (3, 1, "E4")],
    [(0, 2, "F#4"), (2, 2, "D#4")],
    [(0, 4, "B3")],
    [(0, 1.5, "E4"), (1.5, 0.5, "G4"), (2, 2, "B4")],
    [(0, 1, "C5"), (1, 1, "B4"), (2, 1, "A4"), (3, 1, "B4")],
    [(0, 2, "C5"), (2, 2, "A4")],
    [(0, 4, "F4")],
    [(0, 2, "G4"), (2, 2, "B4")],
    [(0, 4, "E5")],
    [(0, 2, "D#5"), (2, 2, "B4")],
    [(0, 4, "F#4")],
]


def music_boss(r):
    s = Song(r, bpm=140, bars=64, meter=4)
    s.bus("drums", 0.95, 0.25)
    s.bus("snare", 1.3, 0.3)
    s.bus("ost", 0.55, 0.25, eq=lambda z: hp(z, 60))
    s.bus("vln", 0.35, 0.35)
    s.bus("brass", 0.55, 0.35)
    s.bus("theme", 0.6, 0.35)
    s.bus("choir", 0.55, 0.5)
    s.bus("sub", 0.22, 0.0)
    s.bus("fx", 0.6, 0.5)

    intro = ["Em"] * 4
    progA = ["Em", "Em", "C", "C", "D", "D", "B", "B"] * 2
    progB = ["Em", "Em", "C", "C", "Am", "Am", "B", "B", "Em", "Em", "F", "F", "Em", "Em", "B", "B"]
    progC = ["Am", "Am", "Em", "Em", "C", "C", "B", "B"]
    trans = ["Em", "C", "D", "B"]
    form = intro + progA + progB + progC + progB + trans

    # sub roots
    for ch, i, nb in merged(form):
        s.add("sub", I.sub(r, float(mtof(bass_of(ch, 28))), s.beats(4 * nb), 0.7, attack=0.05, release=0.3), s.t(i),
              1.0, 0.0, humanize=0)

    # 16th spiccato ostinato (3+3+2 accents), from bar 2; lighter 8ths in the breakdown
    acc = {0, 3, 6, 8, 11, 14}
    for b in range(2, 64):
        ch = form[b]
        pc, _ = I.parse_chord(ch)
        root = 40 + ((pc - 40) % 12)
        in_c = 36 <= b < 44
        lvl = 0.55 if b < 4 else (0.5 if in_c else 0.8)
        for k in range(16):
            if in_c and k % 2:
                continue
            m = root + (12 if k in (6, 14) else 0)
            v = lvl * (1.0 if k in acc else 0.6)
            s.add("ost", I.spiccato(r, float(mtof(m)), s.beats(0.25), v, bright=0.7), s.t(b, k * 0.25), 1.0,
                  -0.25 if k % 2 else -0.15, humanize=0.003)

    # drums
    for b in range(64):
        sec = "intro" if b < 4 else "A" if b < 20 else "B" if b < 36 else "C" if b < 44 else "D" if b < 60 else "T"
        if sec == "C":
            hit(s, "drums", I.taiko, b, 0, 0.9)
            if b % 2 == 1:
                hit(s, "drums", I.taiko, b, 2.5, 0.5, pitch=1.25)
            continue
        if sec == "intro":
            for k, v in [(0, 1.0), (6, 0.6), (8, 0.85), (12, 0.6), (14, 0.7)]:
                hit(s, "drums", I.taiko, b, k * 0.25, v)
            if b == 3:
                for k in range(8, 16):
                    hit(s, "drums", I.tom, b, k * 0.25, 0.4 + 0.05 * (k - 8), pitch=1.0 + 0.03 * (k - 8))
            continue
        hit(s, "drums", I.taiko, b, 0, 1.0)
        hit(s, "drums", I.taiko, b, 2, 0.85)
        hit(s, "drums", I.taiko, b, 1.5, 0.55, pitch=1.3)
        hit(s, "drums", I.taiko, b, 3.5, 0.55, pitch=1.3)
        for k in (3, 11):
            hit(s, "drums", I.tom, b, k * 0.25, 0.45, pitch=1.2)
        if sec in ("B", "D", "T"):
            hit(s, "snare", I.snare, b, 1, 0.7)
            hit(s, "snare", I.snare, b, 3, 0.75)
        for k in range(8):
            hit(s, "snare", I.shaker, b, k * 0.5, 0.3 if k % 2 else 0.2, pan=0.5)
        if sec == "D" and b % 8 == 7:
            for k in range(8, 16):
                hit(s, "snare", I.snare, b, k * 0.25, 0.35 + 0.06 * (k - 8), pan=0.1)
        if sec == "T":
            for k in range(16):
                hit(s, "drums", I.tom, b, k * 0.25, 0.3 + 0.02 * k + 0.1 * (b - 60), pitch=0.9 + 0.1 * ((k // 4) % 3))

    # brass stabs (A, D, T) and swells (B)
    for b in range(4, 64):
        ch = form[b]
        tones = voicing(ch, 50)
        if 4 <= b < 20 or 44 <= b < 64:
            for beat, d, v in [(0, 0.5, 0.9), (1.5, 0.35, 0.7)] + ([(3.5, 0.35, 0.75)] if b % 2 else []):
                for m in tones:
                    s.add("brass", I.brassn(r, float(mtof(m)), s.beats(d), v, swell=0.015, release=0.12, bright=1.0,
                                            growl=0.15), s.t(b, beat), 1.0 / len(tones) * 1.6, 0.0, humanize=0.004)
    for ch, i, nb in merged(progB):
        for m in voicing(ch, 50):
            s.add("brass", I.brassn(r, float(mtof(m)), s.beats(4 * nb), 0.5, swell=1.0, release=0.4, bright=0.5),
                  s.t(20 + i), 0.5, 0.0, humanize=0)

    # theme: low brass in B, brass + violins (8va) + choir in D
    play_mel(s, "theme", I.brassn, 20, BOSS_THEME, 0.85, pan=0.1, swell=0.05, release=0.2, bright=1.0, growl=0.1)
    play_mel(s, "theme", I.brassn, 44, BOSS_THEME, 0.95, pan=0.1, swell=0.04, release=0.2, bright=1.2, growl=0.1)
    play_mel(s, "vln", I.strings, 44, BOSS_THEME, 0.8, pan=-0.2, transpose=12, attack=0.06, release=0.4, bright=0.7,
             block=32)
    # choir: soft in B, full in C and D
    for sec_start, prog, v, vow in [(20, progB, 0.35, "o"), (36, progC, 0.7, "a"), (44, progB, 0.6, "a")]:
        for ch, i, nb in merged(prog):
            s.add("choir", I.choir(r, mtof(np.array(voicing(ch, 52))), s.beats(4 * nb), v, vow, 0.3, 0.8), s.t(sec_start + i),
                  1.0, 0.0, humanize=0)
    # C: violins sustain high tension line
    play_mel(s, "vln", I.strings, 36, [[(0, 8, "E5")], [], [(0, 8, "G5")], [], [(0, 8, "E5")], [], [(0, 4, "D#5")],
                                       [(0, 4, "F#5")]], 0.6, pan=0.3, attack=1.0, release=0.8, bright=0.6, block=64)

    # impacts and swells at section heads
    for b in (0, 4, 20, 44):
        s.add("fx", I.boom(r, 0.9), s.t(b), 1.0, 0.0, humanize=0)
        s.add("fx", I.cymbal(r, 2.5, 0.45), s.t(b), 1.0, 0.3, humanize=0)
    for b in (4, 20, 36, 44, 64):
        swell_into(s, "fx", b % 64, 1.7, 0.45)
    s.add("fx", I.boom(r, 0.6), s.t(36), 1.0, 0.0, humanize=0)
    return s.render(song_ir("boss"))


# --------------------------------------------------------------------------------------------
# LEGEND - "The Dawnbreakers" (bh-021: the story's cutscenes)
# --------------------------------------------------------------------------------------------
LEGEND_A = [
    [(0, 2, "D4"), (2, 1, "F4"), (3, 1, "E4")],
    [(0, 3, "D4"), (3, 1, "A#3")],
    [(0, 2, "C4"), (2, 1, "F4"), (3, 1, "A4")],
    [(0, 4, "G4")],
    [(0, 2, "A4"), (2, 1, "G4"), (3, 1, "F4")],
    [(0, 2, "E4"), (2, 2, "D4")],
    [(0, 2, "C#4"), (2, 1, "E4"), (3, 1, "A4")],
    [(0, 4, "A4")],
]
LEGEND_B = [
    [(0, 1.5, "D5"), (1.5, 0.5, "F5"), (2, 2, "A#4")],
    [(0, 2, "C5"), (2, 2, "A4")],
    [(0, 1, "A#4"), (1, 1, "D5"), (2, 2, "G5")],
    [(0, 3, "F5"), (3, 1, "A4")],
    [(0, 1.5, "D5"), (1.5, 0.5, "F5"), (2, 2, "A#5")],
    [(0, 2, "A5"), (2, 1, "G5"), (3, 1, "E5")],
    [(0, 2, "F#5"), (2, 2, "A5")],
    [(0, 4, "D5")],
]
LEGEND_C_VLN = [[(0, 8, "D5")], [], [(0, 8, "D#5")], [], [(0, 8, "D5")], [], [(0, 4, "C#5")], [(0, 4, "E5")]]


def music_legend(r):
    s = Song(r, bpm=72, bars=40, meter=4)
    s.bus("pad", 0.32, 0.5, eq=lambda z: lp(z, 4200))
    s.bus("bass", 0.5, 0.3, eq=lambda z: lp(z, 1500))
    s.bus("cello", 1.0, 0.4)
    s.bus("str", 0.55, 0.5)
    s.bus("brass", 0.5, 0.4)
    s.bus("theme", 0.62, 0.4)
    s.bus("choir", 0.5, 0.65)
    s.bus("bell", 0.8, 0.6)
    s.bus("perc", 0.95, 0.35)
    s.bus("sub", 0.22, 0.0)
    s.bus("fx", 0.6, 0.55)

    intro = ["Dm", "Dm", "Bb", "A"]
    progA = ["Dm", "Bb", "F", "C", "Dm", "Gm", "A", "A"]
    progB = ["Bb", "F", "Gm", "Dm", "Bb", "C", "D", "D"]
    progC = ["Gm", "Eb", "Bb", "A", "Gm", "Eb", "F", "A"]
    outro = ["Dm", "Dm", "Bb", "A"]
    form = intro + progA + progB + progC + progB + outro          # 40 bars

    vel = [0.4] * 4 + [0.48] * 8 + [0.62] * 8 + [0.55] * 8 + [0.72] * 8 + [0.42] * 4
    for i, ch in enumerate(form):
        play_pads(s, "pad", [ch], i, vel[i], low=50)
        s.add("sub", I.sub(r, float(mtof(bass_of(ch, 26))), s.beats(4), 0.62, attack=0.6, release=1.2), s.t(i), 1.0, 0.0,
              humanize=0)
    # intro: a slow heartbeat on the taiko, a choir breathing, a bell tolling the loop's start
    for b in range(4):
        hit(s, "perc", I.heartbeat, b, 0, 0.7)
        hit(s, "perc", I.heartbeat, b, 2, 0.55)
    for ch, i, nb in merged(intro):
        s.add("choir", I.choir(r, mtof(np.array(voicing(ch, 50))), s.beats(4 * nb), 0.35, "o", 1.2, 1.6), s.t(i), 1.0, 0.0,
              humanize=0)
    s.add("bell", I.bell(r, float(mtof(nm("D4"))), 4.0, 0.5, 4.5), s.t(0), 1.0, -0.2)
    # A: the lament on the cello (Aljay), strings holding the chords, bass walking slowly
    play_bass(s, "bass", progA, 4, 0.45, low=38)
    play_mel(s, "cello", I.cello, 4, LEGEND_A, 0.72, pan=-0.15)
    for ch, i, nb in merged(progA):
        for m in voicing(ch, 55):
            s.add("str", I.strings(r, float(mtof(m)), s.beats(4 * nb), 0.32, attack=0.9, release=1.0, bright=0.35),
                  s.t(4 + i), 0.5, 0.2, humanize=0)
    for b in range(4, 12, 2):
        hit(s, "perc", I.taiko, b, 0, 0.45)
    # B: the Dawnbreakers' theme on the horns, strings climbing under it, taiko marching
    hit(s, "fx", I.boom, 12, 0, 0.8)
    s.add("fx", I.cymbal(r, 3.0, 0.4), s.t(12), 1.0, 0.3, humanize=0)
    play_mel(s, "theme", I.brassn, 12, LEGEND_B, 0.8, pan=0.1, swell=0.08, release=0.3, bright=0.9, growl=0.05)
    play_bass(s, "bass", progB, 12, 0.58, low=38)
    arp(s, "str", I.strings, progB, 12, [0, 1, 2, 1], 1.0, vel=0.35, low=55, pan=-0.3, attack=0.05, release=0.3, bright=0.5)
    for b in range(12, 20):
        hit(s, "perc", I.taiko, b, 0, 0.85)
        hit(s, "perc", I.taiko, b, 2, 0.6)
        hit(s, "perc", I.frame_drum, b, 3.5, 0.3)
    # C: the betrayal — choir swells, a high tense violin line, low taiko alone
    for ch, i, nb in merged(progC):
        s.add("choir", I.choir(r, mtof(np.array(voicing(ch, 50))), s.beats(4 * nb), 0.62, "a", 0.8, 1.2), s.t(20 + i), 1.0,
              0.0, humanize=0)
    play_mel(s, "str", I.strings, 20, LEGEND_C_VLN, 0.55, pan=0.25, attack=1.2, release=1.0, bright=0.55, block=64)
    play_bass(s, "bass", progC, 20, 0.5, low=36)
    for b in range(20, 28):
        hit(s, "perc", I.taiko, b, 0, 0.9)
        if b % 2:
            hit(s, "perc", I.taiko, b, 2.5, 0.45, pitch=1.2)
    swell_into(s, "fx", 28, 1.8, 0.5)
    # D: tutti reprise — horns and violins in octaves, choir, bells on the phrase heads
    hit(s, "fx", I.boom, 28, 0, 1.0)
    s.add("fx", I.cymbal(r, 3.0, 0.5), s.t(28), 1.0, 0.3, humanize=0)
    play_mel(s, "theme", I.brassn, 28, LEGEND_B, 0.95, pan=0.1, swell=0.06, release=0.3, bright=1.1, growl=0.08)
    play_mel(s, "str", I.strings, 28, LEGEND_B, 0.7, pan=-0.2, transpose=12, attack=0.08, release=0.5, bright=0.7, block=32)
    play_bass(s, "bass", progB, 28, 0.66, low=38)
    for ch, i, nb in merged(progB):
        s.add("choir", I.choir(r, mtof(np.array(voicing(ch, 52))), s.beats(4 * nb), 0.6, "a", 0.5, 1.0), s.t(28 + i), 1.0, 0.0,
              humanize=0)
    for b in range(28, 36):
        hit(s, "perc", I.taiko, b, 0, 1.0)
        hit(s, "perc", I.taiko, b, 2, 0.7)
        hit(s, "perc", I.snare, b, 1, 0.3)
        hit(s, "perc", I.snare, b, 3, 0.35)
    for b in (28, 30, 32, 34):
        s.add("bell", I.bell(r, float(mtof(nm(LEGEND_B[b - 28][0][2]))), 2.5, 0.35, 2.5), s.t(b), 1.0, 0.35)
    # outro: the lament's first phrase, thinning to the loop point
    play_mel(s, "cello", I.cello, 36, LEGEND_A[:2] + [[(0, 4, "A#3")], [(0, 4, "A3")]], 0.55, pan=-0.15)
    return s.render(song_ir("menu"))


FUNCS = {"music_menu": music_menu, "music_town": music_town, "music_dungeon": music_dungeon, "music_boss": music_boss,
         "music_legend": music_legend}


def render(name):
    r = np.random.default_rng(seed_of(name))
    return FUNCS[name](r)
