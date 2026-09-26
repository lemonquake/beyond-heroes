"""Render every raster UI texture (frames/, slots/, hud/, tree/, menu/) into game/assets/ui/ in parallel.

Usage: python tools/ui_art/build_raster.py [filter ...]    (filters are substrings of 'folder/name')
"""
from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
UI = os.path.join(ROOT, "game", "assets", "ui")


def _render(key):
    sys.path.insert(0, HERE)
    import raster_all
    from rast import save_gray
    fn, meta = raster_all.builders()[key]
    t = time.time()
    out = fn()
    path = os.path.join(UI, key + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if hasattr(out, "save") and hasattr(out, "ss"):
        out.save(path)
    elif isinstance(out, tuple) and out[0] == "gray":
        save_gray(out[1], path)
    else:  # PIL image
        out.save(path, optimize=True)
    return key, time.time() - t


def build(filters=None, workers=None):
    import raster_all
    keys = [k for k in raster_all.builders() if not filters or any(f in k for f in filters)]
    done = []
    with ProcessPoolExecutor(max_workers=workers or max(1, (os.cpu_count() or 4) - 2)) as ex:
        for key, dt in ex.map(_render, keys):
            done.append((key, dt))
            print(f"  {key:44s} {dt:5.1f}s", flush=True)
    return done


if __name__ == "__main__":
    t0 = time.time()
    d = build(sys.argv[1:] or None)
    print(f"raster: {len(d)} textures in {time.time() - t0:.1f}s")
