"""Dev helper: render one or more raster builders to a scratch folder composited on a dark background.

Usage: python tools/ui_art/preview.py OUTDIR name [name ...]
"""
from __future__ import annotations

import os
import sys
import time

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def find(name):
    import raster_all
    return raster_all.builders()[name]


def main(argv):
    out = argv[0]
    os.makedirs(out, exist_ok=True)
    for name in argv[1:]:
        fn, meta = find(name)
        t = time.time()
        cv = fn()
        img = cv.image() if hasattr(cv, "image") else cv
        bg = Image.new("RGBA", img.size, (40, 34, 44, 255))
        bg.alpha_composite(img)
        base = name.replace("/", "__")
        bg.save(os.path.join(out, base + "_bg.png"))
        img.save(os.path.join(out, base + ".png"))
        print(name, img.size, f"{time.time() - t:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
