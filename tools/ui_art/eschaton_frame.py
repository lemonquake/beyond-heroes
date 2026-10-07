"""bh-041: the inventory slot frame and glow of the Eschaton tier (rarity 14), from the Aether frame (9).

Mirror chrome: the Aether frame's luminance mapped onto a cold chrome ramp (near-black to white), a diagonal sheen,
a thin film of spectrum colours that turns round the frame, and an eclipse in each corner (a black disc in a white
corona with four rays). The glow is the same spectrum. The game adds the moving shimmer on top (ItemSlot).
Run with system Python (PIL): python tools/ui_art/eschaton_frame.py
"""
import colorsys
import math
import os

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SLOTS = os.path.join(ROOT, "game", "assets", "ui", "slots")
RARITY = 14


def chrome(img):
    src = img.convert("RGBA")
    W, H = src.size
    out = Image.new("RGBA", src.size)
    sp, op = src.load(), out.load()
    cx, cy = (W - 1) / 2, (H - 1) / 2
    for y in range(H):
        for x in range(W):
            r, g, b, a = sp[x, y]
            if a == 0:
                op[x, y] = (0, 0, 0, 0)
                continue
            lum = min(1.0, (0.3 * r + 0.59 * g + 0.11 * b) / 255.0 * 1.25)
            # chrome ramp with a hard dark band (what makes polished metal read as mirror)
            t = lum
            band = 0.5 + 0.5 * math.sin(t * 9.0 + (x - y) * 0.06)
            v = 0.12 + 0.88 * (t ** 0.8) * (0.55 + 0.45 * band)
            # diagonal sheen
            d = (x + y) / (W + H)
            sheen = math.exp(-((d - 0.32) / 0.06) ** 2) * 0.55 + math.exp(-((d - 0.7) / 0.04) ** 2) * 0.35
            v = min(1.0, v + sheen)
            # thin-film spectrum turning round the frame
            ang = (math.atan2(y - cy, x - cx) / (2 * math.pi)) % 1.0
            hr, hg, hb = colorsys.hsv_to_rgb(ang, 0.32, 1.0)
            k = 0.35
            col = (v * (1 - k + k * hr), v * (1 - k + k * hg), v * (1 - k + k * hb))
            cool = (0.94, 0.97, 1.0)
            op[x, y] = tuple(int(255 * min(1.0, col[i] * cool[i])) for i in range(3)) + (a,)
    return out


def eclipse(d, cx, cy, s):
    for i in range(4):
        a = math.radians(i * 90 + 45)
        d.line((cx + s * 0.55 * math.cos(a), cy + s * 0.55 * math.sin(a), cx + s * 1.15 * math.cos(a), cy + s * 1.15 * math.sin(a)),
               fill=(245, 248, 255, 255), width=2)
    d.ellipse((cx - s * 0.62, cy - s * 0.62, cx + s * 0.62, cy + s * 0.62), fill=(250, 252, 255, 255))
    d.ellipse((cx - s * 0.46, cy - s * 0.46, cx + s * 0.46, cy + s * 0.46), fill=(8, 8, 14, 255))


def spectrum_glow(img):
    src = img.convert("RGBA")
    W, H = src.size
    out = Image.new("RGBA", src.size)
    sp, op = src.load(), out.load()
    cx, cy = (W - 1) / 2, (H - 1) / 2
    for y in range(H):
        for x in range(W):
            r, g, b, a = sp[x, y]
            ang = (math.atan2(y - cy, x - cx) / (2 * math.pi)) % 1.0
            hr, hg, hb = colorsys.hsv_to_rgb(ang, 0.45, 1.0)
            lum = (0.3 * r + 0.59 * g + 0.11 * b) / 255.0
            op[x, y] = (int(255 * (0.55 + 0.45 * hr)), int(255 * (0.55 + 0.45 * hg)), int(255 * (0.6 + 0.4 * hb)), int(a * min(1.0, 0.5 + lum)))
    return out


def main():
    frame9 = Image.open(os.path.join(SLOTS, "rarity_9.png"))
    glow9 = Image.open(os.path.join(SLOTS, "rarity_glow_9.png"))
    W, H = frame9.size
    fr = chrome(frame9)
    layer = Image.new("RGBA", fr.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for cx, cy in ((11, 11), (W - 12, 11), (11, H - 12), (W - 12, H - 12)):
        eclipse(d, cx, cy, 8)
    halo = layer.filter(ImageFilter.GaussianBlur(2.4))
    fr.alpha_composite(halo)
    fr.alpha_composite(layer)
    fr.save(os.path.join(SLOTS, "rarity_%d.png" % RARITY))
    spectrum_glow(glow9).save(os.path.join(SLOTS, "rarity_glow_%d.png" % RARITY))
    print("wrote rarity_%d and its glow" % RARITY)


if __name__ == "__main__":
    main()
