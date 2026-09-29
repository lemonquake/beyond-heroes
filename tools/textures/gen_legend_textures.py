"""bh-021: tileable PBR sets for the legends (Aljay, Roydo, Paul David) and Kethrax (1024x1024, seamless).

Usage (repo root):  python tools/textures/gen_legend_textures.py [set ...]
Outputs game/assets/textures/legend/<set>_albedo.png (sRGB), _normal.png (OpenGL +Y), _rough.png (linear).
Albedo maps are mostly neutral detail (the model's palette colour tints them in Godot, MaterialLibrary.LEGEND);
forsaken_iron and tyrant_bone carry their own colour.
Evidence: work/lemondev/bh-021/evidence/textures/<set>_2x2.png + legend_textures.png
"""
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texlib import *  # noqa

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "textures", "legend")
EVI = os.path.join(ROOT, "work", "lemondev", "bh-021", "evidence", "textures")


def gray3(g):
    return np.repeat(np.clip(g, 0, 1)[..., None], 3, -1)


# ----------------------------------------------------------------------------------------------------------------
def dragon_scale(seed=2101):
    """Overlapping dragon scales in offset rows, pointing down (-row): domed, a centre keel, sharp overlapping edges."""
    rows, cols = 12, 10
    ph = N / rows                    # row pitch
    pw = N / cols
    h = np.full((N, N), -1.0, np.float32)
    best = np.full((N, N), -9.0, np.float32)
    idm = np.zeros((N, N), np.float32)
    edge = np.zeros((N, N), np.float32)
    r = rng(seed)
    # draw from the top row down so lower rows overlap the ones above (scales overlap downward)
    for j in range(rows):
        for i in range(cols):
            cx = (i + 0.5 * (j % 2)) * pw
            cy = j * ph
            jit = r.random() * 0.12
            # local coords of every pixel relative to this scale, wrapped
            dx = (XX - cx + N / 2) % N - N / 2
            dy = (YY - cy + N / 2) % N - N / 2
            u = dx / (pw * 0.62)
            v = dy / (ph * 1.35)            # scale spans 1.35 rows downward
            # teardrop: wide top, pointed bottom
            inside_v = (v > -0.35) & (v < 1.0)
            half = np.where(v < 0.2, np.sqrt(np.clip(1 - ((v - 0.2) / 0.55) ** 2, 0, 1)), 1 - (v - 0.2) / 0.8)
            half = np.clip(half, 0, 1) ** 0.8
            # the scale from the row above lies on top (its free, pointed edge overlaps this row): at every pixel the
            # scale whose top is farthest away wins, a local rule that stays consistent across the torus wrap
            m = inside_v & (np.abs(u) < half) & (v > best)
            best = np.where(m, v, best)
            if not m.any():
                continue
            d_edge = np.clip(half - np.abs(u), 0, 1)
            dome = (0.55 + 0.45 * np.sqrt(np.clip(d_edge, 0, 1))) * (1.0 - 0.35 * np.clip(v, 0, 1))
            keel = 0.25 * np.clip(1 - np.abs(u) / 0.12, 0, 1) * np.clip(1 - np.abs(v - 0.35) / 0.8, 0, 1)
            val = dome + keel + 0.25 + 0.08 * (j % 3) + jit
            h = np.where(m, val, h)
            idm = np.where(m, r.random(), idm)
            edge = np.where(m, np.clip(d_edge * 6.0, 0, 1), edge)
    h = np.where(h < 0, 0.0, h)
    h = h + noise(seed + 5, 2.0, 30.0) * 0.015 + noise(seed + 6, 1.4, 120.0) * 0.01
    hs = blur(h, 0.8)
    nrm = normal_from_height(hs * 60.0, 1.0)
    rim = 1.0 - edge                      # 1 at the scale's rim
    alb = 0.62 + 0.12 * idm + 0.25 * rim ** 3 - 0.35 * (h < 0.05) + noise(seed + 7, 1.8, 60.0) * 0.04
    alb = np.clip(alb, 0.05, 1.0)
    rough = np.clip(0.42 - 0.18 * rim ** 2 + 0.3 * (h < 0.05) + noise(seed + 8, 2.0, 40.0) * 0.05, 0.12, 0.95)
    return gray3(alb), nrm, rough


def engraved_plate(seed=2111):
    """Polished holy plate with engraved scrollwork (vines, leaves, borders) over a faint hammered finish."""
    cv = Canvas("L", 0)
    r = rng(seed)
    # scroll vines: sinusoidal stems in two diagonal families, with spiral curls and leaves
    for k in range(4):
        y0 = k * N / 4 + 60
        pts = []
        for t in np.linspace(0, 1, 260):
            x = t * N
            y = y0 + math.sin(t * math.tau * 2 + k) * 46
            pts.append((x, y))
        cv.line(pts, 255, 7)
        for c in range(8):
            t = (c + 0.25 + 0.5 * (k % 2)) / 8
            bx = t * N
            by = y0 + math.sin(t * math.tau * 2 + k) * 46
            sgn = 1 if c % 2 else -1
            curl = []
            for a in np.linspace(0, math.tau * 1.3, 60):
                rr = 44 * (1 - a / (math.tau * 1.5))
                curl.append((bx + math.cos(a) * rr * 0.9, by + sgn * (38 + math.sin(a) * rr)))
            cv.line(curl, 255, 5)
            # leaf
            lx, ly = bx + 20, by - sgn * 22
            leaf = [(lx, ly), (lx + 18, ly - sgn * 26), (lx + 40, ly - sgn * 30), (lx + 26, ly - sgn * 8)]
            cv.polygon(leaf, 200)
    # border rules
    for yy in (0, N // 2):
        cv.line([(0, yy + 6), (N, yy + 6)], 255, 4)
        cv.line([(0, yy + 20), (N, yy + 20)], 255, 3)
    g = cv.array()
    g = blur(g, 1.2)
    ham = blur(noise(seed + 3, 1.2, 24.0), 2.0) * 0.08
    h = -g * 0.9 + ham + noise(seed + 4, 2.2, 8.0) * 0.03
    nrm = normal_from_height(h * 16.0, 1.0)
    alb = 0.9 - 0.42 * g + noise(seed + 5, 2.0, 16.0) * 0.03
    rough = np.clip(0.26 + 0.34 * g + 0.06 * noise(seed + 6, 1.6, 50.0), 0.12, 0.9)
    return gray3(alb), nrm, rough


def forsaken_iron(seed=2121):
    """Black pitted iron, dents, scratches and rust bleeding from rivets and seams (coloured)."""
    base = noise(seed, 2.2, 3.0)
    pits_pts = jittered_points(64, 64, seed + 1, 1.0)
    f1, e, i1, _ = voronoi(pits_pts)
    pits = np.clip(1 - f1 / 5.5, 0, 1) * (rng(seed + 2).random(len(pits_pts))[i1] > 0.55)
    scratches = Canvas("L", 0)
    r = rng(seed + 3)
    for _ in range(140):
        x, y = r.random() * N, r.random() * N
        a = r.normal(0.6, 0.5)
        L = r.uniform(40, 220)
        scratches.line([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], int(r.uniform(90, 255)), 2)
    sc = blur(scratches.array(), 0.7)
    dents = blur(noise(seed + 4, 1.0, 6.0), 6) * 0.5
    h = dents - pits * 0.6 - sc * 0.25 + base * 0.05
    nrm = normal_from_height(h * 10.0, 1.0)
    rust_n = noise(seed + 5, 1.8, 4.0) + 0.9 * noise(seed + 6, 2.4, 12.0) * 0.5
    streak = blur(noise(seed + 7, 2.0, 2.0, ax=0.15, ay=2.5), 2)
    rust = sstep(0.6, 1.6, rust_n + streak * 0.6)
    iron = lerp(col((0.13, 0.13, 0.14)), col((0.24, 0.235, 0.24)), remap(base, 0, 1))
    iron = iron + sc[..., None] * 0.22
    rustc = lerp(col((0.28, 0.12, 0.05)), col((0.45, 0.22, 0.08)), remap(noise(seed + 8, 1.5, 30.0), 0, 1))
    alb = lerp(iron, rustc, rust * 0.85)
    alb = alb * (1 - 0.5 * pits[..., None])
    rough = np.clip(0.5 + 0.35 * rust - 0.25 * sc + 0.2 * pits, 0.15, 0.97)
    return alb, nrm, rough


def chainmail(seed=2131):
    """Riveted rings, each ring linked through four neighbours (offset rows)."""
    h = np.zeros((N, N), np.float32)
    n = 32
    pitch = N / n
    ro, ri = pitch * 0.62, pitch * 0.36
    # analytic: two offset lattices of tori
    for off in (0.0, 0.5):
        dx = ((XX / pitch + off) % 1.0 - 0.5) * pitch
        dy = ((YY / pitch + off) % 1.0 - 0.5) * pitch
        d = np.sqrt(dx * dx + dy * dy)
        t = np.clip(1 - np.abs(d - (ro + ri) / 2) / ((ro - ri) / 2), 0, 1)
        h = np.maximum(h, np.sqrt(t) * (0.9 + 0.1 * off))
    h = h + noise(seed, 2.0, 40.0) * 0.03
    nrm = normal_from_height(blur(h, 0.6) * 12.0, 1.0)
    alb = 0.25 + 0.7 * np.clip(h, 0, 1) ** 1.5
    rough = np.clip(0.75 - 0.45 * h, 0.2, 0.95)
    return gray3(alb), nrm, rough


def leather_worn(seed=2141):
    pts = jittered_points(90, 90, seed, 0.9)
    f1, e, _, _ = voronoi(pts)
    grain = np.clip(e / 3.0, 0, 1)
    creases = Canvas("L", 0)
    r = rng(seed + 1)
    for _ in range(60):
        x, y = r.random() * N, r.random() * N
        pts2 = [(x, y)]
        a = r.random() * math.tau
        for k in range(8):
            a += r.normal(0, 0.35)
            x += math.cos(a) * 18
            y += math.sin(a) * 18
            pts2.append((x, y))
        creases.line(pts2, int(r.uniform(100, 255)), 2)
    cr = blur(creases.array(), 1.0)
    h = grain * 0.35 - cr * 0.4 + noise(seed + 2, 1.6, 6.0) * 0.08
    nrm = normal_from_height(h * 8.0, 1.0)
    alb = 0.7 + 0.12 * grain - 0.25 * cr + noise(seed + 3, 1.8, 5.0) * 0.07
    rough = np.clip(0.55 + 0.2 * cr - 0.1 * grain + noise(seed + 4, 2.0, 20.0) * 0.05, 0.25, 0.95)
    return gray3(alb), nrm, rough


def storm_wool(seed=2151):
    """Heavy twill wool: diagonal wale, soft fuzz, a few darned threads."""
    t = (XX + YY) * (math.tau / 12.0)
    wale = 0.5 + 0.5 * np.sin(t)
    thread = 0.5 + 0.5 * np.sin(XX * math.tau / 6.0) * np.sin(YY * math.tau / 6.0)
    fuzz = noise(seed, 1.2, 60.0) * 0.12 + noise(seed + 1, 2.0, 8.0) * 0.1
    h = wale * 0.6 + thread * 0.25 + fuzz
    nrm = normal_from_height(blur(h, 0.7) * 5.0, 1.0)
    alb = 0.78 + 0.12 * wale + fuzz * 0.6
    rough = np.clip(0.88 + 0.06 * fuzz, 0.6, 1.0)
    return gray3(alb), nrm, rough


def tyrant_bone(seed=2161):
    """Old ridged bone of a Tyrant: long fibres, growth rings, cracks darkened with grime (coloured)."""
    fib = noise(seed, 2.0, 3.0, ax=0.08, ay=3.0)
    rings = np.sin(YY * math.tau / 128.0 + fib * 1.5) * 0.5 + 0.5
    cr = Canvas("L", 0)
    r = rng(seed + 1)
    for _ in range(40):
        x, y = r.random() * N, r.random() * N
        pts = [(x, y)]
        for k in range(10):
            x += r.normal(0, 6)
            y += r.uniform(8, 20)
            pts.append((x, y))
        cr.line(pts, 255, 2)
    c = blur(cr.array(), 0.8)
    h = fib * 0.12 + rings * 0.1 - c * 0.5
    nrm = normal_from_height(h * 10.0, 1.0)
    bone = lerp(col((0.5, 0.44, 0.34)), col((0.72, 0.66, 0.53)), remap(fib, 0, 1))
    alb = bone * (0.88 + 0.12 * rings[..., None]) * (1 - 0.6 * c[..., None])
    rough = np.clip(0.62 + 0.2 * c - 0.1 * rings, 0.3, 0.95)
    return alb, nrm, rough


SETS = {
    "dragon_scale": dragon_scale, "engraved_plate": engraved_plate, "forsaken_iron": forsaken_iron,
    "chainmail": chainmail, "leather_worn": leather_worn, "storm_wool": storm_wool, "tyrant_bone": tyrant_bone,
}


def main():
    names = [a for a in sys.argv[1:] if a in SETS] or list(SETS)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(EVI, exist_ok=True)
    tiles = []
    for nm in names:
        alb, nrm, rough = SETS[nm]()
        save_rgb(os.path.join(OUT, nm + "_albedo.png"), alb)
        save_rgb(os.path.join(OUT, nm + "_normal.png"), nrm)
        save_gray(os.path.join(OUT, nm + "_rough.png"), rough)
        im = Image.open(os.path.join(OUT, nm + "_albedo.png"))
        two = Image.new("RGB", (1024, 1024))
        sm = im.resize((512, 512))
        for x in (0, 512):
            for y in (0, 512):
                two.paste(sm, (x, y))
        two.save(os.path.join(EVI, nm + "_2x2.png"))
        tiles.append((nm, im.resize((256, 256)), Image.open(os.path.join(OUT, nm + "_normal.png")).resize((256, 256))))
        sx, sy = seam_score(np.asarray(im, np.float32))
        print(f"{nm}: seam {sx:.2f}/{sy:.2f}")
    sheet = Image.new("RGB", (256 * len(tiles), 512), (20, 20, 24))
    for i, (nm, a, n) in enumerate(tiles):
        sheet.paste(a, (i * 256, 0))
        sheet.paste(n, (i * 256, 256))
    sheet.save(os.path.join(EVI, "legend_textures.png"))


if __name__ == "__main__":
    main()
