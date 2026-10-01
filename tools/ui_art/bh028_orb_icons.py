"""bh-028: finish the celestial orb icons (Sora, Luna, Sol, Airah x Fragment, Shard, Crystalline, Orbital).

Input : work/lemondev/bh-028/scratch/orb_raw/<family>_<grade>.png  (rendered by game/tests/tools/render_orb_icons.tscn)
Output: game/assets/ui/icons/crystals/<family>_<fragment|shard|crystalline|orbital>.png  (256 px RGBA)

Adds the soft grey backdrop disc the other crystal icons have, a halo in the family colour, the family's motif behind
the stone (Sol: sun rays; Luna: a crescent; Sora: a ring of sky; Airah: wind streaks) and a few sparkles.
Deterministic. Run: python tools/ui_art/bh028_orb_icons.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW = os.path.join(ROOT, "work", "lemondev", "bh-028", "scratch", "orb_raw")
OUT = os.path.join(ROOT, "game", "assets", "ui", "icons", "crystals")
GRADES = ["fragment", "shard", "crystalline", "orbital"]
FAMILIES = {
    "sora": (0.55, 0.85, 1.0),
    "luna": (0.72, 0.68, 1.0),
    "sol": (1.0, 0.72, 0.25),
    "airah": (0.6, 1.0, 0.82),
}
S = 256
C = S / 2


def col(c, a=255, k=1.0):
    return tuple(max(0, min(255, int(v * 255 * k))) for v in c) + (a,)


def backdrop():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(60, 0, -1):
        r = S * 0.48 * i / 60
        a = int(150 * (1 - i / 60) ** 0.6)
        g = int(225 - 40 * i / 60)
        d.ellipse([C - r, C - r, C + r, C + r], fill=(g, g, g + 4, a))
    return im.filter(ImageFilter.GaussianBlur(3))


def halo(c, strength):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(40, 0, -1):
        r = S * 0.36 * i / 40
        d.ellipse([C - r, C - r, C + r, C + r], fill=col(c, int(strength * (1 - i / 40) ** 1.5)))
    return im.filter(ImageFilter.GaussianBlur(6))


def motif(fam, c, grade):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    a = 70 + 30 * grade
    if fam == "sol":
        n = 12
        for i in range(n):
            t = 2 * math.pi * i / n + 0.13
            r0, r1 = S * 0.22, S * (0.42 if i % 2 == 0 else 0.34)
            w = 0.09
            pts = [(C + math.cos(t - w) * r0, C + math.sin(t - w) * r0), (C + math.cos(t) * r1, C + math.sin(t) * r1),
                   (C + math.cos(t + w) * r0, C + math.sin(t + w) * r0)]
            d.polygon(pts, fill=col(c, a))
    elif fam == "luna":
        r = S * 0.36
        d.ellipse([C - r, C - r, C + r, C + r], fill=col(c, a))
        d.ellipse([C - r + S * 0.13, C - r - S * 0.05, C + r + S * 0.13, C + r - S * 0.05], fill=(0, 0, 0, 0))
    elif fam == "sora":
        for k, rr in enumerate([0.40, 0.33]):
            r = S * rr
            d.ellipse([C - r, C - r, C + r, C + r], outline=col(c, a - 20 * k), width=5 - 2 * k)
        for i in range(3):
            x = C - S * 0.3 + i * S * 0.25
            y = C + S * 0.24 - (i % 2) * S * 0.06
            d.ellipse([x - 16, y - 9, x + 22, y + 11], fill=(255, 255, 255, a // 2))
    elif fam == "airah":
        for i in range(4):
            y = C - S * 0.22 + i * S * 0.13
            box = [C - S * 0.42, y - S * 0.1, C + S * 0.3, y + S * 0.1]
            d.arc(box, 200, 340, fill=col(c, a), width=4)
    return im.filter(ImageFilter.GaussianBlur(1.6))


def sparkles(c, grade, seed):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rng = random.Random(seed)
    for _ in range(4 + grade * 3):
        x, y = rng.uniform(S * 0.18, S * 0.82), rng.uniform(S * 0.15, S * 0.85)
        r = rng.uniform(1.2, 2.6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col(c, 200, 1.0))
    # one star glint
    x, y = S * 0.66, S * 0.3
    for w, a in ((14, 120), (8, 230)):
        d.line([x - w, y, x + w, y], fill=(255, 255, 255, a), width=2)
        d.line([x, y - w, x, y + w], fill=(255, 255, 255, a), width=2)
    return im.filter(ImageFilter.GaussianBlur(0.6))


def main():
    os.makedirs(OUT, exist_ok=True)
    sheet = Image.new("RGBA", (S * 4, S * 4), (28, 26, 32, 255))
    for fi, (fam, c) in enumerate(FAMILIES.items()):
        for g, gname in enumerate(GRADES):
            im = backdrop()
            im.alpha_composite(halo(c, 120 + 30 * g))
            im.alpha_composite(motif(fam, c, g))
            gem = Image.open(os.path.join(RAW, "%s_%d.png" % (fam, g))).convert("RGBA")
            glow = gem.split()[3].filter(ImageFilter.GaussianBlur(8))
            glow_im = Image.new("RGBA", (S, S), col(c, 255))
            glow_im.putalpha(glow.point(lambda v: int(v * 0.55)))
            im.alpha_composite(glow_im)
            im.alpha_composite(gem)
            im.alpha_composite(sparkles(c, g, fi * 10 + g))
            im.save(os.path.join(OUT, "%s_%s.png" % (fam, gname)))
            sheet.alpha_composite(im, (g * S, fi * S))
    sheet.resize((S * 2, S * 2), Image.LANCZOS).save(os.path.join(ROOT, "work", "lemondev", "bh-028", "evidence", "orb_icons.png"))
    print("16 orb icons ->", OUT)


if __name__ == "__main__":
    main()
