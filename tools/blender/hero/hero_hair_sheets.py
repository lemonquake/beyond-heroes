"""bh-023: contact sheets of the hair / beard previews (system Python + PIL).

  python tools/blender/hero/hero_hair_sheets.py [ids]

Reads the tiles `hero_hair.py -- preview` wrote to work/lemondev/bh-023/scratch/hair/tiles and writes one sheet per
model: rows = the `length` key at 0, 1 and 4; columns = the views.
"""
import os
import sys
import time

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCRATCH = os.path.join(ROOT, "work", "lemondev", "bh-023", "scratch", "hair")
TILES = os.path.join(SCRATCH, "tiles")
HAIR = ["crop", "sidepart", "slick", "spiky", "mohawk", "long", "ponytail", "topknot", "braids", "pigtails", "curly",
        "bowl", "tonsure", "wild"]
BEARD = ["moustache", "handlebar", "goatee", "full", "long", "chops", "braided"]
VIEWS = {"hair": ["front", "q34", "side", "back", "iso", "bodyf", "bodyb"],
         "beard": ["front", "q34", "side", "low", "iso", "bodyf", "bodys"]}


def sheet(kind, name):
    rows = []
    for ln in (0, 1, 4):
        tiles = []
        for v in VIEWS[kind]:
            p = os.path.join(TILES, "%s_%s_L%d_%s.png" % (kind, name, ln, v))
            if not os.path.exists(p):
                return None
            tiles.append(Image.open(p).convert("RGB"))
        rows.append(tiles)
    tw, th = rows[0][0].size
    img = Image.new("RGB", (tw * len(rows[0]), th * 3 + 18), (20, 20, 24))
    d = ImageDraw.Draw(img)
    d.text((4, 3), "%s/%s   rows: length 0, 1, 4   columns: %s" % (kind, name, ", ".join(VIEWS[kind])),
           fill=(230, 230, 230))
    for r, tiles in enumerate(rows):
        for c, t in enumerate(tiles):
            img.paste(t, (c * tw, 18 + r * th))
    out = os.path.join(SCRATCH, "sheet_%s_%s.png" % (kind, name))
    for attempt in range(6):            # a viewer or indexer may hold the old sheet open for a moment
        try:
            img.save(out)
            break
        except OSError:
            if attempt == 5:
                raise
            time.sleep(0.5)
    return out


def main():
    want = sys.argv[1:]
    keys = [("hair", i) for i in HAIR] + [("beard", i) for i in BEARD]
    if want:
        keys = [k for k in keys if k[1] in want or "%s/%s" % k in want]
    for kind, name in keys:
        out = sheet(kind, name)
        print(out or "missing tiles for %s/%s" % (kind, name))


if __name__ == "__main__":
    main()
