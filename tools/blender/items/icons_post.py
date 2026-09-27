"""Icon compositor for the item models (bh-006), system Python + PIL.

  python icons_post.py [sheet NAME] [game]

`game`   writes 128 px icons (soft dark radial backdrop + contact shadow, like the SVG item icons) to
         game/assets/ui/icons/items3d/<id>.png for every base whose icon path points there (items.json icon_path).
`sheet`  composes every raw render into a labelled contact sheet work/lemondev/bh-006/evidence/<NAME>.png.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RAW = os.path.join(ROOT, "work", "lemondev", "bh-006", "evidence", "icons", "raw")
GAME_ICONS = os.path.join(ROOT, "game", "assets", "ui", "icons", "items3d")
EVID = os.path.join(ROOT, "work", "lemondev", "bh-006", "evidence")


def backdrop(size=128):
    """Soft dark radial pool, alpha 0.55 at the centre fading to 0 (the SVG item icons' r1 gradient)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    c = (size - 1) / 2
    R = size * 0.46
    for y in range(size):
        for x in range(size):
            d = ((x - c) ** 2 + (y - c) ** 2) ** 0.5 / R
            if d < 1.0:
                a = 0.55 * (1 - d) if d > 0.6 else 0.55 - (0.55 - 0.25 * 0.55 / 0.55) * 0 - 0.3 * d / 0.6 * 0.55
                a = max(0.0, 0.55 * (1.0 - d) ** 0.9)
                px[x, y] = (0, 0, 0, int(a * 255))
    return img


def game_icon(raw_path, size=128):
    src = Image.open(raw_path).convert("RGBA")
    src = src.resize((size, size), Image.LANCZOS)
    out = backdrop(size)
    # contact shadow: the silhouette, darkened, blurred and nudged down-right
    alpha = src.split()[3]
    sh = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sh.putalpha(alpha.point(lambda a: int(a * 0.6)))
    sh = sh.filter(ImageFilter.GaussianBlur(3))
    out.alpha_composite(sh, (3, 4))
    out.alpha_composite(src)
    return out


def write_game_icons():
    with open(os.path.join(HERE, "items.json"), encoding="utf-8") as f:
        items = json.load(f)
    os.makedirs(GAME_ICONS, exist_ok=True)
    n = 0
    missing = []
    for it in items:
        if "items3d" not in it.get("icon_path", ""):
            continue
        raw = os.path.join(RAW, it["id"] + ".png")
        if not os.path.exists(raw):
            missing.append(it["id"])
            continue
        game_icon(raw).save(os.path.join(GAME_ICONS, it["id"] + ".png"))
        n += 1
    print(f"[icons] wrote {n} game icons; missing renders: {missing}")


def sheet(name, ids=None, cols=10, cell=150):
    files = sorted(f for f in os.listdir(RAW) if f.endswith(".png"))
    if ids:
        files = [f for f in files if f[:-4] in ids]
    rows = (len(files) + cols - 1) // cols
    img = Image.new("RGB", (cols * cell, rows * (cell + 18)), (26, 24, 28))
    dr = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 11)
    except OSError:
        font = ImageFont.load_default()
    for i, f in enumerate(files):
        x, y = (i % cols) * cell, (i // cols) * (cell + 18)
        ic = game_icon(os.path.join(RAW, f), cell - 10)
        bg = Image.new("RGBA", ic.size, (44, 40, 46, 255))
        bg.alpha_composite(ic)
        img.paste(bg.convert("RGB"), (x + 5, y + 5))
        dr.text((x + 6, y + cell - 2), f[:-4][:24], fill=(215, 205, 180), font=font)
    path = os.path.join(EVID, name + ".png")
    img.save(path)
    print(f"[icons] sheet {path} ({len(files)} icons)")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "game" in args:
        write_game_icons()
    if "sheet" in args:
        i = args.index("sheet")
        name = args[i + 1] if i + 1 < len(args) else "icons_sheet"
        sheet(name)
