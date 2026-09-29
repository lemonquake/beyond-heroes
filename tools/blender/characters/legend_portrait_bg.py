"""Composite a transparent legend portrait render over the portraits' dark radial backdrop with a coloured glow.
  python legend_portrait_bg.py <render.png> <out.png> [r,g,b glow 0..1]"""
import sys

import numpy as np
from PIL import Image, ImageFilter

src, out = sys.argv[1], sys.argv[2]
glow = np.array([float(x) for x in (sys.argv[3] if len(sys.argv) > 3 else "0.23,0.42,0.69").split(",")])
fg = Image.open(src).convert("RGBA")
n = 512
fg = fg.resize((n, n), Image.LANCZOS)
yy, xx = np.mgrid[0:n, 0:n].astype(float) / n
r = np.sqrt((xx - 0.5) ** 2 + (yy - 0.39) ** 2) / 0.74
c0, c1, c2 = np.array([0.08, 0.14, 0.22]), np.array([0.04, 0.06, 0.1]), np.array([0.016, 0.008, 0.03])
bg = np.where(r[..., None] < 0.55, c0 + (c1 - c0) * (r[..., None] / 0.55), c1 + (c2 - c1) * np.clip((r[..., None] - 0.55) / 0.45, 0, 1))
g = np.exp(-((xx - 0.63) ** 2 + (yy - 0.54) ** 2) / 0.06)[..., None] * glow * 0.35
bg = np.clip(bg + g, 0, 1)
base = Image.fromarray((bg * 255).astype(np.uint8), "RGB").convert("RGBA")
# a soft coloured halo behind the figure
a = fg.split()[3].filter(ImageFilter.GaussianBlur(14))
halo = Image.new("RGBA", (n, n), tuple(int(v * 255) for v in glow) + (0,))
halo.putalpha(a.point(lambda v: int(v * 0.45)))
base = Image.alpha_composite(base, halo)
base = Image.alpha_composite(base, fg)
# vignette
v = np.clip(1.0 - np.maximum(0, np.sqrt((xx - 0.5) ** 2 + (yy - 0.5) ** 2) - 0.36) * 1.6, 0.35, 1.0)
arr = np.asarray(base.convert("RGB"), float) * v[..., None]
Image.fromarray(arr.astype(np.uint8)).save(out)
print("saved", out)
