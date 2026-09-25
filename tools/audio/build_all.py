"""Regenerate every Beyond Heroes audio asset (deterministic).

    python tools/audio/build_all.py                 # everything + report + spectrograms
    python tools/audio/build_all.py --only sfx      # sfx | amb | music | report
    python tools/audio/build_all.py --names hit_flesh_1 parry
"""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[1]
SFX_DIR = ROOT / "game" / "assets" / "audio" / "sfx"
MUS_DIR = ROOT / "game" / "assets" / "audio" / "music"
EVID_DIR = ROOT / "work" / "lemondev" / "bh-001" / "evidence" / "audio"


def _job(kind_name):
    kind, name = kind_name
    sys.path.insert(0, str(HERE))
    from synth import write_wav
    t0 = time.time()
    if kind == "sfx":
        import sfx_bank
        x, loop = sfx_bank.render(name)
        write_wav(SFX_DIR / f"{name}.wav", x, loop=loop)
    elif kind == "amb":
        import ambience
        x = ambience.render(name)
        write_wav(MUS_DIR / f"{name}.wav", x, loop=True)
    elif kind == "music":
        import music
        x = music.render(name)
        write_wav(MUS_DIR / f"{name}.wav", x, loop=True)
    return kind, name, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["sfx", "amb", "music", "report"], default=None)
    ap.add_argument("--names", nargs="*", default=None)
    ap.add_argument("--jobs", type=int, default=8)
    a = ap.parse_args()

    import ambience
    import music
    import sfx_bank

    jobs = []
    if a.only in (None, "music"):
        jobs += [("music", n) for n in music.TRACKS]
    if a.only in (None, "amb"):
        jobs += [("amb", n) for n in ambience.AMBIENCES]
    if a.only in (None, "sfx"):
        jobs += [("sfx", n) for n in sfx_bank.REG]
    if a.names:
        jobs = [j for j in jobs if j[1] in a.names]

    t0 = time.time()
    if jobs:
        with ProcessPoolExecutor(max_workers=a.jobs) as ex:
            for kind, name, dt in ex.map(_job, jobs):
                print(f"[{kind:5s}] {name:28s} {dt:6.1f}s", flush=True)
    print(f"rendered {len(jobs)} files in {time.time() - t0:.1f}s")

    if a.only in (None, "report") and not a.names:
        import analyze
        analyze.main(SFX_DIR, MUS_DIR, EVID_DIR)


if __name__ == "__main__":
    main()
