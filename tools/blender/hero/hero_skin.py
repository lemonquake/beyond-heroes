"""bh-023: the hero's skin textures, made from the source body texture (models/generic_body.jpg).

  python tools/blender/hero/hero_skin.py        (system Python: numpy + PIL; run after `hero_body.py -- export`,
                                                 which writes the mesh it needs to work/lemondev/bh-023/scratch)

Every texel is given its position on the conformed body (UV rasterisation), which lets regions be chosen by where
they are on the figure rather than by hand in the atlas:

  hero_skin.png   RGB = the source texture divided by its mean skin colour (stored / 2), with the painted eyes, brows,
                  scalp stubble and beard shadow smoothed away: the game multiplies it by the chosen skin colour and
                  draws eyes, brows, stubble and lip colour itself, so they can be customised
  hero_masks.png  R = underwear, G = scalp (where hair grows), B = beard area, A = lips
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCRATCH = os.path.join(ROOT, "work", "lemondev", "bh-023", "scratch")
OUT = os.path.join(ROOT, "game", "assets", "characters", "hero")
SRC_TEX = os.path.join(ROOT, "models", "generic_body.jpg")
SIZE = 1024


def _step(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def texel_positions(V, T, UV, size):
    """-> (pos (size, size, 3), valid (size, size)) with row 0 at the top of the image."""
    pos = np.zeros((size, size, 3), np.float32)
    valid = np.zeros((size, size), bool)
    P = UV.copy()
    P[..., 0] = UV[..., 0] * size - 0.5
    P[..., 1] = (1.0 - UV[..., 1]) * size - 0.5
    for t in range(len(T)):
        a, b, c = P[t]
        x0 = max(int(np.floor(min(a[0], b[0], c[0]))) - 1, 0)
        x1 = min(int(np.ceil(max(a[0], b[0], c[0]))) + 1, size - 1)
        y0 = max(int(np.floor(min(a[1], b[1], c[1]))) - 1, 0)
        y1 = min(int(np.ceil(max(a[1], b[1], c[1]))) + 1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        w2 = 1.0 - w0 - w1
        eps = -0.08          # a little bleed over the triangle's edge, so seams stay covered
        m = (w0 >= eps) & (w1 >= eps) & (w2 >= eps)
        if not m.any():
            continue
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        va, vb, vc = V[T[t]]
        p = w0[..., None] * va + w1[..., None] * vb + w2[..., None] * vc
        yy, xx = ys[m], xs[m]
        keep = inside[m] | ~valid[yy, xx]
        pos[yy[keep], xx[keep]] = p[m][keep]
        valid[yy[keep], xx[keep]] = True
    return pos, valid


def hairline(y):
    """Height of the hairline as the head turns from the forehead (most negative y) to the nape."""
    ys = np.array([-0.17, -0.150, -0.12, -0.09, -0.06, -0.035, -0.01, 0.02, 0.10])
    zs = np.array([1.756, 1.754, 1.748, 1.734, 1.712, 1.700, 1.668, 1.632, 1.612])
    return np.interp(y, ys, zs)


def beard_top(ax):
    xs = np.array([0.0, 0.02, 0.03, 0.045, 0.06, 0.075, 0.088, 0.12])
    zs = np.array([1.640, 1.640, 1.633, 1.624, 1.632, 1.656, 1.678, 1.678])
    return np.interp(ax, xs, zs)


def masks(pos, valid):
    x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
    ax = np.abs(x)
    head = _step(1.545, 1.56, z) * (ax < 0.14) * valid
    front = 1 - _step(-0.10, -0.075, y)
    scalp = _step(-0.014, 0.010, z - hairline(y)) * head
    ex, ez = (ax - 0.035) / 0.033, (z - 1.696) / 0.026
    orbit = (1 - _step(0.75, 1.0, np.sqrt(ex * ex + ez * ez))) * head * front
    lx, lz = x / 0.033, (z - 1.6155) / 0.0125
    lips = (1 - _step(0.7, 1.0, np.sqrt(lx * lx + lz * lz))) * head * (1 - _step(-0.125, -0.11, y))
    side = _step(-0.12, -0.07, y)                 # 0 under the chin, 1 along the jaw and neck
    low = _step(1.545 + 0.025 * side, 1.578 + 0.03 * side, z)
    beard = (1 - _step(-0.012, 0.010, z - beard_top(ax))) * low * (1 - _step(-0.04, -0.012, y)) * head
    return dict(head=head, scalp=scalp, orbit=orbit, lips=lips, beard=beard)


def inpaint(img, hole, valid, iters=900):
    """Fill `hole` by diffusion from the surrounding valid texels (texture space, inside the UV islands)."""
    out = img.copy()
    known = valid & ~hole
    if not known.any():
        return out
    out[hole] = img[known].mean(0)
    for _ in range(iters):
        acc = np.zeros_like(out)
        cnt = np.zeros(out.shape[:2], np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(out, (dy, dx), (0, 1))
            sv = np.roll(valid, (dy, dx), (0, 1))
            acc += sh * sv[..., None]
            cnt += sv
        new = acc / np.maximum(cnt, 1.0)[..., None]
        out[hole] = new[hole]
    return out


def pad(img, valid, steps=12):
    """Edge padding: grow the islands into the empty atlas so filtering never pulls in background."""
    out = img.copy()
    v = valid.copy()
    for _ in range(steps):
        acc = np.zeros_like(out)
        cnt = np.zeros(out.shape[:2], np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(out, (dy, dx), (0, 1))
            sv = np.roll(v, (dy, dx), (0, 1))
            acc += sh * sv[..., None]
            cnt += sv
        grow = (~v) & (cnt > 0)
        out[grow] = acc[grow] / cnt[grow][..., None]
        v |= grow
    return out


def main():
    d = np.load(os.path.join(SCRATCH, "hero_mesh.npz"))
    V, T, UV = d["V"], d["T"], d["UV"]
    src = Image.open(SRC_TEX).convert("RGB").resize((SIZE, SIZE), Image.BICUBIC)
    img = np.asarray(src, np.float32) / 255.0
    pos, valid = texel_positions(V, T, UV, SIZE)
    m = masks(pos, valid)
    lum = img @ np.array([0.299, 0.587, 0.114], np.float32)
    z, ax = pos[..., 2], np.abs(pos[..., 0])
    under_zone = (z > 0.70) & (z < 1.16) & (ax < 0.32) & valid
    under = under_zone & (lum < 0.30)
    # drop the thin dark seams at island edges: keep only solid areas of cloth
    solid = np.asarray(Image.fromarray((under * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4.0)), np.float32) > 140
    under = under & solid
    und = np.asarray(Image.fromarray((under * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255.0
    skin_ref = valid & ~under_zone & (m["head"] < 0.5) & (lum > 0.3)
    mean = img[skin_ref].mean(0)
    print("[skin] mean skin colour (sRGB)", mean.round(4).tolist())
    hole = ((m["scalp"] > 0.02) | (m["orbit"] > 0.02) | ((m["beard"] > 0.02) & (m["lips"] < 0.6))) & valid
    clean = inpaint(img, hole, valid)
    # keep a soft transition from the untouched skin into the smoothed areas
    soft = np.clip(np.maximum.reduce([m["scalp"], m["orbit"], m["beard"] * (1 - m["lips"])]), 0.0, 1.0)[..., None]
    clean = img * (1 - soft) + clean * soft
    detail = clean / mean
    ug = lum / max(float(lum[under].mean()), 1e-3) if under.any() else lum
    detail = detail * (1 - und[..., None]) + np.clip(ug, 0.0, 2.0)[..., None] * und[..., None]
    detail = pad(detail, valid)
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray((np.clip(detail * 0.5, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, "hero_skin.png"))
    lips = m["lips"] * np.clip((img[..., 0] - img[..., 1]) / 0.12, 0.35, 1.0)
    def soft(a, r=2.0):
        return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255.0
    mk = np.stack([und, soft(m["scalp"] * valid), soft(m["beard"] * (1 - m["lips"]) * valid), soft(lips * valid, 1.0)], -1)
    mk = pad(mk.astype(np.float32), valid, 6)
    Image.fromarray((np.clip(mk, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, "hero_masks.png"))
    with open(os.path.join(OUT, "hero_skin.json"), "w") as f:
        import json
        json.dump({"mean_skin_srgb": [round(float(c), 4) for c in mean], "size": SIZE}, f)
    # debug views for the evidence folder
    Image.fromarray((np.clip(clean, 0, 1) * 255).astype(np.uint8)).save(os.path.join(SCRATCH, "skin_clean.png"))
    Image.fromarray((np.clip(mk[..., :3], 0, 1) * 255).astype(np.uint8)).save(os.path.join(SCRATCH, "skin_masks_rgb.png"))
    print("[skin] ->", OUT)


if __name__ == "__main__":
    sys.exit(main())
