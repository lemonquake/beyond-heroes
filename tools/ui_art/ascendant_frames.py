"""bh-034: inventory slot frames and glows for the four Ascendant tiers (rarity 10-13), from the Aether frame (9).

The Aether frame keeps its shape; each tier is recoloured from its luminance into the tier's two colours, and gets its
corner mark: Cosmic four-point stars, Divine sun discs, Eternal hourglasses, Primordial shards. Run with system Python
(PIL): python tools/ui_art/ascendant_frames.py
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SLOTS = os.path.join(ROOT, "game", "assets", "ui", "slots")
TIERS = {  # rarity: (dark colour, bright colour, mark)
    10: ((70, 52, 200), (214, 220, 255), "star"),
    11: ((176, 120, 34), (255, 248, 214), "sun"),
    12: ((160, 52, 110), (255, 214, 232), "glass"),
    13: ((120, 10, 6), (255, 150, 60), "shard"),
}


def tint(img, dark, bright):
    src = img.convert("RGBA")
    out = Image.new("RGBA", src.size)
    sp, op = src.load(), out.load()
    for y in range(src.size[1]):
        for x in range(src.size[0]):
            r, g, b, a = sp[x, y]
            lum = (0.3 * r + 0.59 * g + 0.11 * b) / 255.0
            k = min(1.0, lum * 1.15)
            op[x, y] = tuple(int(dark[i] + (bright[i] - dark[i]) * k) for i in range(3)) + (a,)
    return out


def mark(d, kind, cx, cy, s, col, glow):
    if kind == "star":
        pts = []
        for i in range(8):
            r = s if i % 2 == 0 else s * 0.3
            a = math.radians(i * 45 - 90)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, fill=col)
    elif kind == "sun":
        d.ellipse((cx - s * 0.45, cy - s * 0.45, cx + s * 0.45, cy + s * 0.45), fill=col)
        for i in range(8):
            a = math.radians(i * 45)
            d.line((cx + s * 0.55 * math.cos(a), cy + s * 0.55 * math.sin(a), cx + s * math.cos(a), cy + s * math.sin(a)), fill=col, width=2)
    elif kind == "glass":
        d.polygon([(cx - s * 0.6, cy - s), (cx + s * 0.6, cy - s), (cx, cy)], fill=col)
        d.polygon([(cx - s * 0.6, cy + s), (cx + s * 0.6, cy + s), (cx, cy)], fill=glow)
    else:
        d.polygon([(cx, cy - s), (cx + s * 0.45, cy - s * 0.1), (cx + s * 0.2, cy + s), (cx - s * 0.35, cy + s * 0.3)], fill=col)
        d.line((cx, cy - s * 0.6, cx + s * 0.1, cy + s * 0.6), fill=glow, width=2)


def main():
    frame9 = Image.open(os.path.join(SLOTS, "rarity_9.png"))
    glow9 = Image.open(os.path.join(SLOTS, "rarity_glow_9.png"))
    W, H = frame9.size
    for r, (dark, bright, kind) in TIERS.items():
        fr = tint(frame9, dark, bright)
        layer = Image.new("RGBA", fr.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for cx, cy in ((11, 11), (W - 12, 11), (11, H - 12), (W - 12, H - 12)):
            mark(d, kind, cx, cy, 8, bright + (255,), dark + (255,))
        halo = layer.filter(ImageFilter.GaussianBlur(2.2))
        fr.alpha_composite(halo)
        fr.alpha_composite(layer)
        fr.save(os.path.join(SLOTS, "rarity_%d.png" % r))
        gl = tint(glow9, dark, bright)
        gl.save(os.path.join(SLOTS, "rarity_glow_%d.png" % r))
        print("wrote rarity_%d" % r)


if __name__ == "__main__":
    main()
