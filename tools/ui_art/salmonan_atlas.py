"""Clean base art for the Salmonan island atlas (the M map). No text, roads, markers or fog: those are native UI
layers drawn by WorldMapWindow from DataIsland, so names, routes and discovery can change without repainting.

Output (2x the atlas coordinate space of DataIsland: 1000 x 850 -> 2000 x 1700):
  game/assets/ui/atlas/salmonan_atlas.png   the island painting (RGB)
  game/assets/ui/atlas/atlas_mist.png       tileable mist for uncharted areas (RGBA)

Geography must agree with the game data:
  - the west and south coast come from Westreach's LAND outline (src/world/maps/westreach.gd), mapped to the atlas
    with its origin (400, 544) and 0.7 m per atlas pixel (DataIsland.MAP_ORIGIN / PX_M);
  - Malasugue sits at (240, 527) (47 m plateau radius), the Ruined Forest map at (366, 402) (144 x 96 m),
  - the millstream follows Westreach's STREAM; Stillwater Lake is centred at (575, 392).
  - Olivar's origin is (601.5, 514) and Wyman Outpost's (618.7, 681) (bh-007); their walls, houses and tents are painted
    from the same layout constants as src/world/maps/olivar.gd and wyman_outpost.gd.
The north and east coast follow the concept atlas (work/map-concept-2026-09-27/atlas-preview.html).

Run: python tools/ui_art/salmonan_atlas.py
"""
import math
import pathlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "game" / "assets" / "ui" / "atlas"
S = 2                      # art pixels per atlas unit
W, H = 1000 * S, 850 * S
PX_M = 0.7
RNG = np.random.default_rng(20260927)

WESTREACH_ORIGIN = (400.0, 544.0)
WESTREACH_LAND = [(-212, -90), (-203, -60), (-201, -30), (-205, 0), (-200, 40), (-199, 62), (-203, 78), (-207, 94), (-200, 104),
                  (-189, 108), (-176, 111), (-163, 110), (-153, 114), (-146, 126), (-130, 134), (-100, 138), (-70, 140),
                  (-40, 142), (-10, 140), (20, 136), (50, 134), (80, 138), (120, 150)]
STREAM = [(74, -66), (46, -44), (24, -32), (16, -22), (15.5, -10), (19, 2), (26, 20), (42, 48), (54, 78), (62, 108), (66, 134)]
TOWN = (240.0, 527.0)
OLIVAR = (601.5, 514.0)        # DataIsland.MAP_ORIGIN (bh-007)
WYMAN = (618.7, 681.0)
FOREST = (366.0, 402.0)
LAKE = (575.0, 392.0)


def wr(p):
    return (WESTREACH_ORIGIN[0] + p[0] / PX_M, WESTREACH_ORIGIN[1] + p[1] / PX_M)


# north/east coast from the concept atlas, joined to Westreach's real west/south shore
NORTH_EAST = [(137, 374), (151, 343), (138, 310), (155, 277), (143, 246), (168, 227), (174, 184), (243, 166), (270, 124), (325, 128),
              (351, 92), (413, 112), (453, 87), (497, 107), (538, 79), (577, 112), (623, 100), (655, 126), (719, 139), (747, 162),
              (788, 153), (814, 196), (846, 227), (833, 268), (870, 299), (859, 347), (890, 387), (868, 433), (882, 480), (852, 514),
              (850, 563), (817, 593), (831, 636), (790, 663), (781, 705), (737, 731), (697, 762), (632, 757)]


def organic(pts, jitter, smooth=3, step=2.5, closed=False, seed=0):
    """Chaikin-smooth then subdivide and push each point along its normal by smooth noise (jitter atlas px)."""
    r = np.random.default_rng(seed)
    p = [np.array(q, float) for q in pts]
    for _ in range(smooth):
        out = [p[0]] if not closed else []
        rng_ = range(len(p)) if closed else range(len(p) - 1)
        for i in rng_:
            a, b = p[i], p[(i + 1) % len(p)]
            out += [a * 0.75 + b * 0.25, a * 0.25 + b * 0.75]
        if not closed:
            out.append(p[-1])
        p = out
    dense = []
    for i in range(len(p) - (0 if closed else 1)):
        a, b = p[i], p[(i + 1) % len(p)]
        n = max(1, int(np.linalg.norm(b - a) / step))
        for j in range(n):
            dense.append(a + (b - a) * j / n)
    if not closed:
        dense.append(p[-1])
    k = len(dense)
    phase = r.uniform(0, 100, 4)
    res = []
    for i, q in enumerate(dense):
        a, b = dense[max(i - 1, 0)], dense[min(i + 1, k - 1)]
        t = b - a
        nrm = np.array([-t[1], t[0]]) / (np.linalg.norm(t) + 1e-6)
        u = i / k * 2 * math.pi
        off = (math.sin(u * 23 + phase[0]) * 0.5 + math.sin(u * 57 + phase[1]) * 0.3 + math.sin(u * 131 + phase[2]) * 0.2) * jitter
        res.append(tuple(q + nrm * off))
    return res


COAST = organic(NORTH_EAST, 7.0, smooth=3, seed=1) + organic([wr(p) for p in reversed(WESTREACH_LAND)], 2.2, smooth=2, seed=2)


def px(pts):
    return [(x * S, y * S) for x, y in pts]


def noise(shape, scale, octaves=5, persistence=0.5):
    """Smooth fractal value noise in [-1, 1]."""
    h, w = shape
    out = np.zeros(shape, np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        cell = max(2, int(scale / (2 ** o)))
        gh, gw = h // cell + 3, w // cell + 3
        grid = RNG.standard_normal((gh, gw)).astype(np.float32)
        up = ndimage.zoom(grid, cell, order=3)[:h, :w]
        out += up * amp
        total += amp
        amp *= persistence
    out /= total
    return out / (np.abs(out).max() + 1e-6)


def mask_from_poly(pts, blur=0.0):
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).polygon(px(pts), fill=255)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im, np.float32) / 255.0


def ellipse_mask(c, r, blur=0.0):
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).ellipse([(c[0] - r[0]) * S, (c[1] - r[1]) * S, (c[0] + r[0]) * S, (c[1] + r[1]) * S], fill=255)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im, np.float32) / 255.0


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t[..., None] if np.ndim(t) == 2 else a + (b - a) * t


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ax, ay = xx / S, yy / S

    land = mask_from_poly(COAST)
    land_soft = mask_from_poly(COAST, blur=3)
    d_in = ndimage.distance_transform_edt(land > 0.5) / S          # atlas px inland
    d_out = ndimage.distance_transform_edt(land < 0.5) / S         # atlas px offshore

    # ---- height: rolling lowlands, the northern heights, the eastern mountains around the temple
    n1 = noise((H, W), 220)
    n2 = noise((H, W), 60, 4)
    ridge = 1.0 - np.abs(noise((H, W), 140, 4))
    north = smoothstep(330, 120, ay) * (1.0 - smoothstep(700, 860, ax) * 0.2)
    east = np.exp(-(((ax - 770) / 120) ** 2 + ((ay - 250) / 150) ** 2))
    height = 0.25 + n1 * 0.18 + n2 * 0.06 + (north * 0.9 + east * 0.8) * (0.55 + ridge * 0.6)
    height *= 0.35 + 0.65 * smoothstep(0, 10, d_in)
    lake_pts = []
    for i in range(48):
        a = 2 * math.pi * i / 48
        rr = 1.0 + 0.10 * math.sin(a * 3 + 0.8) + 0.06 * math.sin(a * 7 + 2.0) + 0.04 * math.sin(a * 11)
        lake_pts.append((LAKE[0] + math.cos(a) * 100 * rr, LAKE[1] + math.sin(a) * 74 * rr))
    lake_pts = organic(lake_pts, 2.0, smooth=2, closed=True, seed=3)
    lake = np.clip(mask_from_poly(lake_pts, blur=2) + ellipse_mask((515, 438), (24, 16), blur=6), 0, 1)
    lake_m = lake > 0.5
    town = ellipse_mask(TOWN, (70, 70), blur=6)
    height = height * (1 - town * 0.8) + town * 0.32
    height = height * (1 - lake * 0.9)

    # hillshade (light from the north-west)
    gy, gx = np.gradient(height * 260.0)
    nx, ny, nz = -gx, -gy, np.ones_like(gx)
    nl = np.sqrt(nx * nx + ny * ny + nz * nz)
    shade = np.clip((nx * -0.55 + ny * -0.55 + nz * 0.62) / nl + 0.28, 0.45, 1.25)
    shade = ndimage.gaussian_filter(shade, 1.2)

    # ---- land colour ramp
    low = np.array([0.23, 0.29, 0.17])
    meadow = np.array([0.33, 0.37, 0.21])
    rock = np.array([0.40, 0.38, 0.33])
    snow = np.array([0.78, 0.77, 0.74])
    col = lerp(low, meadow, smoothstep(0.1, 0.35, height + n2 * 0.08))
    col = lerp(col, rock, smoothstep(0.55, 0.85, height))
    col = lerp(col, snow, smoothstep(1.12, 1.4, height + n2 * 0.12) * 0.8)
    # beaches and cliffs
    sand = np.array([0.55, 0.5, 0.38])
    cove_beach = np.exp(-(((ax - 146) / 36) ** 2 + ((ay - 690) / 18) ** 2))
    col = lerp(col, sand, np.clip(cove_beach * smoothstep(12, 0, d_in) * 1.4, 0, 1))
    cliff = smoothstep(3.5, 0.5, d_in) * (1 - cove_beach)
    col = lerp(col, np.array([0.34, 0.32, 0.29]), cliff * 0.9)
    lip = smoothstep(5.0, 3.5, d_in) * smoothstep(2.5, 3.5, d_in) * (1 - cove_beach)
    col = lerp(col, np.array([0.5, 0.5, 0.4]), lip * 0.35)
    col *= shade[..., None]

    # fields: a patchwork around Lantern Fields and the mill
    fields = Image.new("RGB", (W, H), (0, 0, 0))
    fm = Image.new("L", (W, H), 0)
    fd, fmd = ImageDraw.Draw(fields), ImageDraw.Draw(fm)
    tones = [(118, 112, 62), (96, 104, 52), (132, 118, 70), (84, 92, 48), (110, 96, 58)]
    for cx, cy, n in [(420, 690, 14), (370, 650, 8), (460, 640, 7), (300, 690, 7)]:
        for i in range(n):
            px0 = cx + RNG.uniform(-50, 50)
            py0 = cy + RNG.uniform(-28, 28)
            w, h = RNG.uniform(12, 26), RNG.uniform(7, 14)
            a = math.radians(RNG.uniform(-25, 25))
            pts = [(px0 + math.cos(a) * dx - math.sin(a) * dy, py0 + math.sin(a) * dx + math.cos(a) * dy)
                   for dx, dy in [(-w, -h), (w, -h), (w, h), (-w, h)]]
            fd.polygon(px(pts), fill=tones[i % len(tones)])
            fmd.polygon(px(pts), fill=210)
    fm = fm.filter(ImageFilter.GaussianBlur(1.2))
    fmask = (np.asarray(fm, np.float32) / 255.0) * land * (1 - lake) * (1 - town)
    col = lerp(col, (np.asarray(fields, np.float32) / 255.0) * shade[..., None], fmask)

    # the marsh: mottled wet ground in the south-east
    marsh = np.clip(ellipse_mask((720, 640), (110, 70), blur=30) * 1.3, 0, 1) * land
    mot = smoothstep(-0.1, 0.4, noise((H, W), 16, 3))
    col = lerp(col, lerp(np.array([0.2, 0.28, 0.2]), np.array([0.12, 0.24, 0.26]), mot), marsh * 0.8)

    # ---- sea: depth bands, shallows and a foam line
    sea_deep = np.array([0.02, 0.07, 0.10])
    sea_mid = np.array([0.05, 0.16, 0.20])
    sea_shallow = np.array([0.11, 0.30, 0.33])
    sea = lerp(sea_mid, sea_deep, smoothstep(10, 120, d_out))
    sea = lerp(sea, sea_shallow, smoothstep(14, 0, d_out))
    waves = noise((H, W), 10, 2)
    sea *= (0.93 + 0.07 * waves)[..., None]
    rings = (np.sin(d_out * 0.9) * 0.5 + 0.5) * smoothstep(40, 6, d_out) * smoothstep(3, 8, d_out)
    sea = lerp(sea, sea_shallow * 1.2, rings * 0.12)
    foam = smoothstep(2.5, 0.0, d_out) * (1 - land)
    sea = lerp(sea, np.array([0.6, 0.7, 0.7]), foam * 0.55)
    lake_col = lerp(np.array([0.06, 0.2, 0.23]), np.array([0.12, 0.33, 0.35]), smoothstep(0.6, 1.0, 1 - lake) + 0.3)
    col = lerp(col, lake_col * (0.95 + 0.05 * waves[..., None]), lake)

    img = lerp(sea, col, land_soft)
    rgb = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    base = Image.fromarray(rgb, "RGB").convert("RGBA")

    # ---- the millstream and the lake's outflow
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    stream = [wr(p) for p in STREAM]
    od.line(px(stream), fill=(22, 60, 66, 255), width=int(4.5 * S), joint="curve")
    od.line(px(stream), fill=(64, 128, 128, 255), width=int(2.2 * S), joint="curve")
    falls = [(620, 250), (600, 290), (590, 318)]
    od.line(px(falls), fill=(64, 128, 128, 255), width=int(2.4 * S), joint="curve")
    base.alpha_composite(ov)

    # ---- forests: canopy stamps with shadows; the Ruined Forest is darker, burnt, with a few embers
    density = np.zeros((H, W), np.float32)
    density += np.clip(ellipse_mask(FOREST, (118, 80), blur=24) * 1.2, 0, 1)
    density += np.clip(ellipse_mask((250, 250), (120, 90), blur=40), 0, 1) * 0.8
    density += np.clip(ellipse_mask((600, 520), (90, 34), blur=30), 0, 1) * 0.6
    density += np.clip(ellipse_mask((700, 300), (90, 80), blur=40), 0, 1) * 0.55
    density += smoothstep(360, 200, ay) * 0.45 * (1 - smoothstep(0.85, 1.1, height))
    density += np.clip(ellipse_mask((290, 600), (60, 40), blur=24), 0, 1) * 0.35
    clear_olv = np.clip(ellipse_mask((OLIVAR[0], OLIVAR[1] + 4), (78, 66), blur=10), 0, 1)
    clear_wy = np.clip(ellipse_mask(WYMAN, (52, 52), blur=10), 0, 1)
    density *= land * (1 - lake) * (1 - town) * (1 - fmask) * (1 - marsh * 0.8) * smoothstep(6, 14, d_in) * (1 - clear_olv) * (1 - clear_wy)
    density *= np.clip(0.7 + noise((H, W), 50, 3) * 0.6, 0, 1)
    density = np.clip(density, 0, 1)
    burnt = ellipse_mask((330, 408), (60, 40), blur=24)
    trees = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(trees)
    shadows = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadows)
    n_try = 260000
    xs = RNG.uniform(0, W, n_try)
    ys = RNG.uniform(0, H, n_try)
    keep = RNG.uniform(0, 1, n_try) < density[ys.astype(int), xs.astype(int)] * 0.5
    order = np.argsort(ys[keep])
    for x, y in zip(xs[keep][order], ys[keep][order]):
        b = burnt[int(y), int(x)]
        r = RNG.uniform(3.6, 6.0) * (1.0 - 0.3 * b)
        sd.ellipse([x - r + 2.6, y - r * 0.8 + 3.4, x + r + 2.6, y + r * 0.8 + 3.4], fill=(0, 0, 0, 110))
        g = RNG.uniform(0.75, 1.1)
        c = (int(30 * g + 30 * b), int(52 * g - 12 * b), int(30 * g - 6 * b), 255)
        td.ellipse([x - r, y - r, x + r, y + r], fill=c)
        hl = (int(c[0] * 1.5 + 8), int(c[1] * 1.45 + 8), int(c[2] * 1.3 + 4), 200)
        td.ellipse([x - r * 0.65, y - r * 0.75, x + r * 0.15, y + r * 0.05], fill=hl)
    shadows = shadows.filter(ImageFilter.GaussianBlur(1.6))
    base.alpha_composite(shadows)
    base.alpha_composite(trees)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(22):
        x = (330 + RNG.normal(0, 26)) * S
        y = (408 + RNG.normal(0, 16)) * S
        gd.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 120, 40, 200))
    glow = glow.filter(ImageFilter.GaussianBlur(2.5))
    base.alpha_composite(glow)

    # ---- mountains: ridge strokes and snow for the northern heights and the temple range
    mt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(mt)
    peaks = []
    for _ in range(90):
        x, y = RNG.uniform(250, 880), RNG.uniform(90, 330)
        hv = height[int(y * S), int(x * S)] if 0 <= y * S < H and 0 <= x * S < W else 0
        if hv > 0.7 and not lake_m[int(y * S), int(x * S)]:
            peaks.append((x, y, hv))
    peaks.sort(key=lambda p: p[1])
    for x, y, hv in peaks:
        s = RNG.uniform(12, 20) * min(1.3, hv)
        pts = [(x - s, y + s * 0.55), (x - s * 0.1, y - s * 0.9), (x + s, y + s * 0.55)]
        md.polygon(px(pts), fill=(72, 68, 60, 235))
        md.polygon(px([(x - s * 0.1, y - s * 0.9), (x + s, y + s * 0.55), (x + s * 0.2, y + s * 0.55)]), fill=(46, 43, 40, 235))
        md.polygon(px([(x - s * 0.42, y - s * 0.3), (x - s * 0.1, y - s * 0.9), (x + s * 0.22, y - s * 0.34)]), fill=(205, 204, 196, 235))
    base.alpha_composite(mt)

    # ---- Malasugue: the plateau, the palisade ring, rooftops and warm windows
    tw = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tdw = ImageDraw.Draw(tw)
    r_town = 47 / PX_M
    cx, cy = TOWN
    tdw.ellipse([(cx - r_town) * S, (cy - r_town) * S, (cx + r_town) * S, (cy + r_town) * S], fill=(58, 58, 44, 255),
                outline=(96, 80, 56, 255), width=int(1.5 * S))
    rf = 40 / PX_M
    for i in range(90):
        a = 2 * math.pi * i / 90
        if abs(math.degrees(a) - 90) < 7:
            continue
        x, y = cx + math.cos(a) * rf, cy + math.sin(a) * rf
        tdw.rectangle([(x - 1.1) * S, (y - 1.1) * S, (x + 1.1) * S, (y + 1.1) * S], fill=(82, 60, 40, 255))
    for i in range(34):
        a = RNG.uniform(0, 2 * math.pi)
        d = RNG.uniform(16, 50)
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        w, h = RNG.uniform(4, 7), RNG.uniform(3, 5)
        tdw.rectangle([(x - w) * S, (y - h) * S, (x + w) * S, (y + h) * S], fill=(96, 50, 38, 255))
        tdw.rectangle([(x - w) * S, (y - h) * S, (x + w) * S, (y - h * 0.2) * S], fill=(128, 70, 50, 255))
    tdw.ellipse([(cx - 7) * S, (cy - 3) * S, (cx + 7) * S, (cy + 11) * S], fill=(70, 110, 120, 255))
    base.alpha_composite(tw)

    # ---- Olivar (bh-007): the walled square above the lake, rooftops, the plaza, the trading house and the pier
    def olv(x, z):
        return (OLIVAR[0] + x / PX_M, OLIVAR[1] + z / PX_M)
    ow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od2 = ImageDraw.Draw(ow)
    a0, a1 = olv(-46, -36), olv(46, 42)
    od2.rectangle([a0[0] * S, a0[1] * S, a1[0] * S, a1[1] * S], fill=(62, 62, 46, 255))
    for (x0, z0, x1, z1) in [(-46, -36, -46, 42), (-46, 42, 46, 42), (46, 42, 46, -36)]:
        steps = int(max(abs(x1 - x0), abs(z1 - z0)) / 3)
        for i in range(steps + 1):
            t = i / max(1, steps)
            x, z = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t
            if (x0 == x1 and abs(z - 12) < 4.5) or (z0 == z1 and abs(x - 20) < 4.5):
                continue
            q = olv(x, z)
            od2.rectangle([(q[0] - 1.1) * S, (q[1] - 1.1) * S, (q[0] + 1.1) * S, (q[1] + 1.1) * S], fill=(82, 60, 40, 255))
    pc = olv(0, 4)
    od2.ellipse([(pc[0] - 13) * S, (pc[1] - 13) * S, (pc[0] + 13) * S, (pc[1] + 13) * S], fill=(92, 88, 76, 255))
    for (x, z, w, h) in [(-30, 22, 5, 6), (-33, 34.5, 5, 5), (30, 22, 5, 6), (33, 34, 5, 5), (-5, 32, 6, 5), (31, -24, 5, 5),
                         (-36, -23, 5, 5), (7, 32.5, 6, 5), (-31, -9, 5, 6), (31, -2, 7, 9)]:
        q = olv(x, z)
        od2.rectangle([(q[0] - w) * S, (q[1] - h) * S, (q[0] + w) * S, (q[1] + h) * S], fill=(96, 50, 38, 255))
        od2.rectangle([(q[0] - w) * S, (q[1] - h) * S, (q[0] + w) * S, (q[1] - h * 0.2) * S], fill=(128, 70, 50, 255))
    pier0, pier1 = olv(2, -44), olv(6, -62)
    od2.rectangle([pier0[0] * S, pier1[1] * S, pier1[0] * S, pier0[1] * S], fill=(92, 70, 46, 255))
    base.alpha_composite(ow)

    # ---- Wyman Outpost (bh-007): the round stockade, tents around the bonfire, the overlook above the marsh
    def wy(x, z):
        return (WYMAN[0] + x / PX_M, WYMAN[1] + z / PX_M)
    ww = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(ww)
    c = wy(0, 0)
    rr = 31 / PX_M
    wd.ellipse([(c[0] - rr) * S, (c[1] - rr) * S, (c[0] + rr) * S, (c[1] + rr) * S], fill=(66, 60, 42, 255))
    for i in range(80):
        a = 2 * math.pi * i / 80
        deg = math.degrees(a)
        if abs(((deg + 80) + 180) % 360 - 180) < 8 or abs(((deg - 158) + 180) % 360 - 180) < 8:
            continue
        q = (c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr)
        wd.rectangle([(q[0] - 1.1) * S, (q[1] - 1.1) * S, (q[0] + 1.1) * S, (q[1] + 1.1) * S], fill=(82, 60, 40, 255))
    for (x, z) in [(-19, -11), (-9, -26), (13, -21), (21, -10), (10, 22), (20, 17), (3, 26), (-24, 3), (-6, -22)]:
        q = wy(x, z)
        wd.polygon([((q[0] - 3.2) * S, (q[1] + 2.4) * S), (q[0] * S, (q[1] - 2.8) * S), ((q[0] + 3.2) * S, (q[1] + 2.4) * S)], fill=(150, 128, 92, 255))
        wd.line([(q[0] * S, (q[1] - 2.8) * S), (q[0] * S, (q[1] + 2.4) * S)], fill=(100, 84, 60, 255), width=S)
    wbase = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdw = ImageDraw.Draw(wbase)
    f = wy(-4, -2)
    gdw.ellipse([(f[0] - 6) * S, (f[1] - 6) * S, (f[0] + 6) * S, (f[1] + 6) * S], fill=(255, 150, 60, 170))
    wbase = wbase.filter(ImageFilter.GaussianBlur(5))
    base.alpha_composite(ww)
    base.alpha_composite(wbase)

    # ---- grain and a vignette so it reads as an old chart under the UI frame
    arr = np.asarray(base.convert("RGB"), np.float32) / 255.0
    grain = RNG.normal(0, 0.018, (H, W, 1)).astype(np.float32)
    vx = (xx / W - 0.5) * 2
    vy = (yy / H - 0.5) * 2
    vig = 1.0 - 0.35 * smoothstep(0.55, 1.45, np.sqrt(vx * vx + vy * vy))
    arr = np.clip((arr + grain) * vig[..., None] * np.array([1.02, 1.0, 0.96]), 0, 1)
    Image.fromarray((arr * 255).astype(np.uint8), "RGB").save(OUT / "salmonan_atlas.png", optimize=True)

    # ---- mist for uncharted land (tileable: noise wrapped by blending edges)
    m = 512
    mn = noise((m * 2, m * 2), 120, 5)
    mn = mn[:m, :m] * 0.5 + mn[m:, m:] * 0.5
    a = smoothstep(-0.5, 0.8, mn)
    mist = np.zeros((m, m, 4), np.uint8)
    mist[..., 0] = 150
    mist[..., 1] = 168
    mist[..., 2] = 184
    mist[..., 3] = (a * 255).astype(np.uint8)
    # make it tile: cross-fade with a half-offset copy
    rolled = np.roll(np.roll(mist, m // 2, 0), m // 2, 1)
    wx = np.abs(np.linspace(-1, 1, m))[None, :]
    wy = np.abs(np.linspace(-1, 1, m))[:, None]
    w = np.clip(np.maximum(wx, wy) * 1.4 - 0.4, 0, 1)
    mist[..., 3] = (mist[..., 3] * (1 - w) + rolled[..., 3] * w).astype(np.uint8)
    Image.fromarray(mist, "RGBA").save(OUT / "atlas_mist.png", optimize=True)
    print("wrote", OUT / "salmonan_atlas.png", "and atlas_mist.png")


if __name__ == "__main__":
    main()
