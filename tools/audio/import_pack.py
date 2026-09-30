"""Bring the recorded audio pack in `audio/` into the game (bh-025).

    python tools/audio/import_pack.py            # sound effects + music
    python tools/audio/import_pack.py --only sfx # sfx | music

Sound effects (`audio/weapon/*.mp3`) become mono 44.1 kHz WAVs in game/assets/audio/sfx, named as `Audio` expects its
variations (`sword_hit_1.wav`, ...). Each one is cut to the sound itself: the silence in front (a blow has to sound on
the frame it lands; `bow_attack1` carries 0.37 s of it) and the padding behind, then a short fade, a -1 dB peak and a
loudness ceiling so the loud recordings do not tower over the rest. A few sounds the pack does not have are derived
from the ones it does (great weapons: the same steel, heavier).

Music (`audio/*.mp3`) is copied as it is to game/assets/audio/music; `MusicDirector.TRACKS` trims each track's gain.
The loudness this prints is where those trims come from.

Needs `miniaudio` (pip install miniaudio) to decode MP3.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[1]
SRC = ROOT / "audio"
SFX_DIR = ROOT / "game" / "assets" / "audio" / "sfx"
MUS_DIR = ROOT / "game" / "assets" / "audio" / "music"

from kit import thump  # noqa: E402
from synth import SR, fade, lufs, mix, normalize, resample, rng, todb, undb, write_wav  # noqa: E402

LEAD_DB = -34.0      # relative to the peak: where the sound starts
TAIL_DB = -50.0      # ... and where it has ended
MAX_LEN = 2.6        # seconds; nothing in the pack but the blizzard needs more
CEIL_RMS = -15.0     # dBFS over the sound's body; louder recordings are turned down to this

# source file (without .mp3) -> name in the game
SFX = {
    "attack_woosh": "attack_woosh_1",
    "sword_hit1": "sword_hit_1", "sword_hit2": "sword_hit_2", "sword_hit3": "sword_hit_3",
    "axe_hit1": "axe_hit_1", "axe_hit2": "axe_hit_2", "axe_hit3": "axe_hit_3",
    "hammer_hit1": "hammer_hit_1", "hammer_hit2": "hammer_hit_2", "hammer_hit3": "hammer_hit_3",
    "generic_hit_metal": "hit_metal_1",
    "bow_attack1": "bow_attack_1", "bow_attack2": "bow_attack_2", "bow_attack3": "bow_attack_3",
    "cleave1": "cleave_1", "cleave2": "cleave_2",
    "mage_attack1": "mage_attack_1", "mage_attack2": "mage_attack_2",
    "mage_strong_attack": "mage_strong_attack",
    "fireball_cast": "fireball_cast", "fireball_hit": "fireball_hit",
    "meteor_cast": "meteor_cast", "meteor_hit": "meteor_hit",
    "blizzard_cast": "blizzard_cast", "chain_lightning": "chain_lightning",
}

# name in the game -> (imported sound, playback speed, low thump gain): what the pack has no recording of
DERIVED = {
    "attack_woosh_2": ("attack_woosh_1", 0.92, 0.0), "attack_woosh_3": ("attack_woosh_1", 1.09, 0.0),
    "hit_metal_2": ("hit_metal_1", 0.93, 0.0), "hit_metal_3": ("hit_metal_1", 1.08, 0.0),
    "greatsword_hit_1": ("sword_hit_1", 0.76, 0.55), "greatsword_hit_2": ("sword_hit_2", 0.74, 0.55),
    "greatsword_hit_3": ("sword_hit_3", 0.78, 0.55),
    "greataxe_hit_1": ("axe_hit_1", 0.8, 0.5), "greataxe_hit_2": ("axe_hit_2", 0.78, 0.5),
    "greataxe_hit_3": ("axe_hit_3", 0.82, 0.5),
}

MUSIC = ["main_theme", "battle_theme", "boss_theme", "dungeon_theme1", "fire_dungeon_theme", "ice_dungeon_theme", "aljay_theme"]


def decode(path: Path, channels: int) -> np.ndarray:
    import miniaudio
    d = miniaudio.decode_file(str(path), output_format=miniaudio.SampleFormat.FLOAT32, nchannels=channels, sample_rate=SR)
    x = np.frombuffer(d.samples, dtype=np.float32).astype(float)
    return x if channels == 1 else x.reshape(-1, channels)


def cut(x: np.ndarray, max_len: float = MAX_LEN) -> np.ndarray:
    """The sound without the silence around it."""
    a = np.abs(x)
    pk = a.max()
    lead = np.nonzero(a > pk * undb(LEAD_DB))[0]
    start = max(0, int(lead[0]) - int(0.002 * SR))
    # tail: where it first stays under the floor for a fifth of a second (the files end on a click of encoder noise,
    # so "the last loud sample" would keep all the padding)
    w = int(0.01 * SR)
    env = np.sqrt(np.convolve(x * x, np.ones(w) / w, mode="same"))
    quiet = env < pk * undb(TAIL_DB)
    hold = int(0.2 * SR)
    run = np.convolve(quiet.astype(float), np.ones(hold), mode="valid") >= hold - 0.5
    after = np.nonzero(run[start:])[0]
    end = min(len(x), start + int(after[0]) + w) if len(after) else len(x)
    return x[start:min(end, start + int(max_len * SR))]


def level(x: np.ndarray) -> np.ndarray:
    x = normalize(x, -1.0)
    body = x[:max(1, min(len(x), int(0.6 * SR)))]
    rms = todb(float(np.sqrt(np.mean(body * body))) + 1e-9)
    if rms > CEIL_RMS:
        x = x * undb(CEIL_RMS - rms)
    return x


def finish(x: np.ndarray) -> np.ndarray:
    return level(fade(x, 0.001, min(0.12, 0.25 * len(x) / SR)))


def import_sfx() -> None:
    done: dict[str, np.ndarray] = {}
    for src, name in SFX.items():
        raw = decode(SRC / "weapon" / f"{src}.mp3", 1)
        x = finish(cut(raw, 5.0 if name == "blizzard_cast" else MAX_LEN))
        done[name] = x
        write_wav(SFX_DIR / f"{name}.wav", x)
        print(f"[sfx ] {src:22s} -> {name:22s} {len(raw) / SR:5.2f}s -> {len(x) / SR:5.2f}s  peak {todb(np.abs(x).max()):5.1f} dB")
    r = rng(25)
    for name, (base, speed, low) in DERIVED.items():
        x = resample(done[base], speed)
        if low > 0.0:
            x = mix((x, 0, 1.0), (thump(r, 120 * speed, 42, 0.32, 0.035, 0.26, 2.0), 0, low))
        x = finish(x)
        write_wav(SFX_DIR / f"{name}.wav", x)
        print(f"[made] {base:22s} -> {name:22s} x{speed:.2f}  {len(x) / SR:5.2f}s")


def import_music() -> None:
    MUS_DIR.mkdir(parents=True, exist_ok=True)
    for name in MUSIC:
        src = SRC / f"{name}.mp3"
        shutil.copyfile(src, MUS_DIR / f"{name}.mp3")
        x = decode(src, 2)
        print(f"[music] {name:20s} {len(x) / SR:6.1f}s  {lufs(x.mean(axis=1)):6.1f} LUFS  peak {todb(np.abs(x).max()):5.1f} dB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["sfx", "music"], default=None)
    a = ap.parse_args()
    if a.only in (None, "sfx"):
        import_sfx()
    if a.only in (None, "music"):
        import_music()


if __name__ == "__main__":
    main()
