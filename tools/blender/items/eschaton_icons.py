"""bh-041: game icons for the Eschaton pieces (system Python + PIL).

Takes the raw renders of eschaton_regalia.py, makes the usual 128 px item icon (icons_post.game_icon: soft backdrop and
contact shadow) and sets a few four-point star glints on the brightest chrome highlights, so the tier reads as
sparkling even in a bag cell. The glint places come from the item id, so a rebuild is identical.

  python tools/blender/items/eschaton_icons.py [raw dir]
"""
import hashlib
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import icons_post  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RAW = os.path.join(ROOT, "work", "lemondev", "bh-041", "scratch", "icons_raw")
OUT = os.path.join(ROOT, "game", "assets", "ui", "icons", "items3d")


def glints(icon, seed):
    """3-4 star glints on the brightest opaque pixels, never two close together."""
    rnd = random.Random(seed)
    px = icon.load()
    W, H = icon.size
    bright = []
    for y in range(4, H - 4, 2):
        for x in range(4, W - 4, 2):
            r, g, b, a = px[x, y]
            if a > 200:
                lum = 0.3 * r + 0.59 * g + 0.11 * b
                if lum > 205:
                    bright.append((lum + rnd.random() * 30, x, y))
    bright.sort(reverse=True)
    picked = []
    for _, x, y in bright:
        if all((x - u) ** 2 + (y - v) ** 2 > 22 ** 2 for u, v in picked):
            picked.append((x, y))
        if len(picked) >= rnd.choice((3, 4)):
            break
    layer = Image.new("RGBA", icon.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for k, (x, y) in enumerate(picked):
        s = rnd.uniform(5.5, 9.0) if k == 0 else rnd.uniform(3.5, 6.0)
        w = max(1, int(s * 0.22))
        d.polygon([(x - s, y), (x - w, y - w), (x, y - s), (x + w, y - w), (x + s, y), (x + w, y + w), (x, y + s), (x - w, y + w)],
                  fill=(255, 255, 255, 235))
    halo = layer.filter(ImageFilter.GaussianBlur(2.2))
    out = icon.copy()
    out.alpha_composite(halo)
    out.alpha_composite(halo)
    out.alpha_composite(layer)
    return out


def main():
    raw = sys.argv[1] if len(sys.argv) > 1 else RAW
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for name in sorted(os.listdir(raw)):
        if not (name.startswith("esc_") and name.endswith(".png")):
            continue
        iid = name[:-4]
        icon = icons_post.game_icon(os.path.join(raw, name))
        seed = int(hashlib.md5(iid.encode()).hexdigest()[:8], 16)
        glints(icon, seed).save(os.path.join(OUT, name))
        n += 1
    print("wrote %d Eschaton icons to %s" % (n, OUT))


if __name__ == "__main__":
    main()
