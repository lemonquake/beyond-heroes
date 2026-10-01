"""bh-029: clean base art for the Zarael Island atlas (the M map), same painted style and size as salmonan_atlas.py.
No text, roads, markers or fog: those are native UI layers drawn by WorldMapWindow from DataIsland.

Output (2x the 1000 x 850 atlas coordinate space -> 2000 x 1700):
  game/assets/ui/atlas/zarael_atlas.png        the island painting (RGB)  (+ .import copied from salmonan_atlas)
Evidence:
  work/lemondev/bh-029/evidence/textures/atlas_regions.png   the painting with the region centres/boxes overlaid

Geography (atlas units, 1000 x 850): an island elongated west->east.
  Agdao            south-west coast: a harbour bay with the town on a stepped hillside above it, the Crown of Steps
                   pyramid at its north edge
  The Coilwood     jungle north and east of Agdao (old step-farms and an aqueduct under the canopy)
  Glasswire Barrens red cracked plain with violet glints east of the jungle, a fallen colossus lying in it
  the gorge        a deep chasm running north->south across the island's middle, open to the sea at both ends
  Bridge of Death  a stone span crossing the gorge west->east, north of the Barrens
  Heart Citadel    a walled temple-fortress on a high plateau east of the gorge; step-farms south of it
  mountains        along the north coast
Run: python tools/ui_art/bh029_atlas.py
"""
import hashlib
import math
import pathlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "game" / "assets" / "ui" / "atlas"
EVI = ROOT / "work" / "lemondev" / "bh-029" / "evidence" / "textures"
S = 2
W, H = 1000 * S, 850 * S
RNG = np.random.default_rng(20261001)

# ---- region centres and painted footprints (atlas units). Reported to the Orchestrator.
REGIONS = {
    # map origins / walkable bounds at 1 m per atlas px (game/src/data/data_island.gd ZR_MAP_ORIGIN, the map builders)
    "agdao": dict(centre=(230, 705), box=(145, 625, 315, 785)),
    "zr_coilwood": dict(centre=(456, 649), box=(316, 549, 596, 749)),
    "zr_barrens": dict(centre=(728, 647), box=(598, 547, 858, 747)),
    "bridge_of_death": dict(centre=(758, 393), box=(718, 228, 798, 558)),
    "zr_citadel": dict(centre=(758, 149), box=(658, 64, 858, 234)),
}
AGDAO = (230.0, 669.0)
PYRAMID = (230.0, 643.0)
BAY = (222.0, 759.0)
CITADEL = (758.0, 125.0)
COLOSSUS = (776.0, 619.0)
BRIDGE_X, BRIDGE_N, BRIDGE_S = 758.0, 236.0, 542.0
GORGE_Y = 389.0
DX, DY = 36.0, 69.0            # Agdao's town art moved from its first painting to the map's real place

COAST_PTS = [(70, 560), (60, 500), (80, 440), (70, 380), (96, 330), (110, 270), (140, 220), (170, 170), (220, 140), (270, 120),
             (330, 110), (390, 96), (450, 104), (510, 92), (560, 80), (610, 52), (660, 30), (720, 20), (790, 18), (850, 32),
             (900, 58), (940, 100), (958, 150), (950, 210), (966, 260), (950, 320), (962, 380), (948, 440), (960, 500),
             (944, 560), (950, 620), (930, 680), (940, 730), (910, 772), (870, 792), (820, 802), (770, 794), (720, 808),
             (670, 800), (620, 812), (570, 802), (520, 810), (470, 800), (420, 806), (370, 796), (330, 800), (304, 790),
             (290, 772), (274, 758), (252, 750), (226, 748), (202, 752), (184, 762), (170, 780), (150, 794), (120, 792),
             (96, 772), (80, 732), (66, 682), (74, 620)]
ISLETS = [((122, 818), (16, 7)), ((978, 560), (10, 16)), ((40, 300), (9, 14)), ((604, 834), (13, 6)), ((984, 120), (9, 7))]
# a rift from the western highlands to the east coast, widest (the bridge's 300 m) where the Bridge of Death crosses
GORGE = [(330, 352), (400, 346), (470, 366), (540, 384), (610, 380), (680, 388), (758, 389), (830, 380), (900, 372), (990, 366)]


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
        a, b = dense[(i - 1) % k] if closed else dense[max(i - 1, 0)], dense[(i + 1) % k] if closed else dense[min(i + 1, k - 1)]
        t = b - a
        nrm = np.array([-t[1], t[0]]) / (np.linalg.norm(t) + 1e-6)
        u = i / k * 2 * math.pi
        off = (math.sin(u * 23 + phase[0]) * 0.5 + math.sin(u * 57 + phase[1]) * 0.3 + math.sin(u * 131 + phase[2]) * 0.2) * jitter
        res.append(tuple(q + nrm * off))
    return res


COAST = organic(COAST_PTS, 6.5, smooth=2, closed=True, seed=11)


def px(pts):
    return [(x * S, y * S) for x, y in pts]


def noise(shape, scale, octaves=5, persistence=0.5):
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


def polyline_dist(pts, ax, ay):
    """Distance (atlas units) from every pixel to a polyline."""
    d = np.full(ax.shape, 1e9, np.float32)
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        vx, vy = x1 - x0, y1 - y0
        L2 = vx * vx + vy * vy
        t = np.clip(((ax - x0) * vx + (ay - y0) * vy) / L2, 0, 1)
        dx, dy = ax - (x0 + t * vx), ay - (y0 + t * vy)
        d = np.minimum(d, np.sqrt(dx * dx + dy * dy))
    return d


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    EVI.mkdir(parents=True, exist_ok=True)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ax, ay = xx / S, yy / S

    islets = []
    for k, (c, r) in enumerate(ISLETS):
        pts = [(c[0] + math.cos(a) * r[0] * (1 + 0.18 * math.sin(a * 3 + k)), c[1] + math.sin(a) * r[1] * (1 + 0.15 * math.cos(a * 2 + k)))
               for a in np.linspace(0, 2 * math.pi, 28, endpoint=False)]
        islets.append(organic(pts, 1.5, smooth=2, closed=True, seed=40 + k))
    land = np.clip(mask_from_poly(COAST) + sum(mask_from_poly(q) for q in islets), 0, 1)
    land_soft = np.clip(mask_from_poly(COAST, blur=3) + sum(mask_from_poly(q, blur=3) for q in islets), 0, 1)
    d_in = ndimage.distance_transform_edt(land > 0.5) / S
    d_out = ndimage.distance_transform_edt(land < 0.5) / S

    # ---- the gorge: a meandering chasm from coast to coast, narrowest where the bridge crosses
    gline = organic(GORGE, 9.0, smooth=2, seed=12)
    gd = polyline_dist(gline, ax, ay)
    gn = noise((H, W), 30, 3)
    half = 34 + 92 * smoothstep(520, 730, ax) * (1 - 0.25 * smoothstep(800, 980, ax)) + gn * 5
    gorge = smoothstep(half + 2, half - 2, gd)            # the chasm floor (unseen depth)
    rim = smoothstep(half + 16, half, gd) * (1 - gorge)    # the falling walls

    # ---- height
    n1 = noise((H, W), 220)
    n2 = noise((H, W), 60, 4)
    ridge = 1.0 - np.abs(noise((H, W), 120, 4))
    north = smoothstep(330, 170, ay) * (1 - 0.7 * smoothstep(640, 700, ax))
    plateau_m = np.clip(ellipse_mask(CITADEL, (112, 96), blur=10) * 1.0, 0, 1)
    hill_agdao = np.exp(-(((ax - PYRAMID[0]) / 70) ** 2 + ((ay - PYRAMID[1]) / 56) ** 2))
    height = 0.24 + n1 * 0.16 + n2 * 0.06 + north * (0.55 + ridge * 0.6) + plateau_m * 0.42 + hill_agdao * 0.22
    height *= 0.35 + 0.65 * smoothstep(0, 10, d_in)
    height = height - rim * 0.22 - gorge * 0.5
    bd_ = np.sqrt(((ax - 728) / 140) ** 2 + ((ay - 640) / 112) ** 2) + noise((H, W), 60, 4) * 0.22
    barrens = smoothstep(1.02, 0.86, bd_) * land
    barrens *= smoothstep(8, 20, gd - half)
    height = height * (1 - barrens * 0.35)

    gy, gx = np.gradient(height * 260.0)
    nx, ny, nz = -gx, -gy, np.ones_like(gx)
    nl = np.sqrt(nx * nx + ny * ny + nz * nz)
    shade = np.clip((nx * -0.55 + ny * -0.55 + nz * 0.62) / nl + 0.28, 0.45, 1.25)
    shade = ndimage.gaussian_filter(shade, 1.2)

    # ---- land colour: warm jungle lowland, ochre rock, red barrens, pale limestone plateau
    low = np.array([0.18, 0.27, 0.17])
    meadow = np.array([0.29, 0.34, 0.19])
    rock = np.array([0.45, 0.38, 0.29])
    crest = np.array([0.6, 0.55, 0.47])
    col = lerp(low, meadow, smoothstep(0.1, 0.4, height + n2 * 0.08))
    col = lerp(col, rock, smoothstep(0.6, 0.9, height))
    col = lerp(col, crest, smoothstep(1.15, 1.45, height + n2 * 0.12) * 0.6)
    lime = np.array([0.55, 0.5, 0.4])
    col = lerp(col, lime * (0.94 + 0.06 * n2[..., None]), plateau_m * 0.55 * smoothstep(0.3, 0.7, 1 - rim))
    # barrens: red cracked plain, a crack web and glassy violet glints
    red = lerp(np.array([0.46, 0.27, 0.19]), np.array([0.36, 0.2, 0.16]), smoothstep(-0.4, 0.6, noise((H, W), 40, 3)))
    col = lerp(col, red, barrens * 0.92)
    # beaches, cliffs, the coast lip
    sand = np.array([0.57, 0.5, 0.37])
    beach = np.clip(np.exp(-(((ax - BAY[0]) / 44) ** 2 + ((ay - BAY[1] + 6) / 22) ** 2)) * 1.4
                    + np.exp(-(((ax - 560) / 100) ** 2 + ((ay - 800) / 14) ** 2)), 0, 1)
    col = lerp(col, sand, np.clip(beach * smoothstep(10, 0, d_in) * 1.4, 0, 1))
    cliff = smoothstep(3.5, 0.5, d_in) * (1 - beach)
    col = lerp(col, np.array([0.38, 0.32, 0.26]), cliff * 0.9)
    lip = smoothstep(5.0, 3.5, d_in) * smoothstep(2.5, 3.5, d_in) * (1 - beach)
    col = lerp(col, np.array([0.55, 0.5, 0.4]), lip * 0.3)
    col *= shade[..., None]
    # the gorge: walls of layered ochre rock falling into blackness
    strata = 0.5 + 0.5 * np.sin(gd * 0.9 + gn * 2)
    wall = lerp(np.array([0.36, 0.25, 0.18]), np.array([0.5, 0.37, 0.26]), strata)
    col = lerp(col, wall * (0.75 + 0.25 * shade[..., None]), rim * 0.9)
    abyss = lerp(np.array([0.15, 0.11, 0.1]), np.array([0.045, 0.045, 0.06]), smoothstep(half * 0.9, half * 0.1, gd))
    abyss = lerp(abyss, np.array([0.16, 0.18, 0.21]), (smoothstep(half * 0.5, 0, gd) * smoothstep(-0.2, 0.8, noise((H, W), 24, 3)) * 0.35))
    col = lerp(col, abyss, gorge)

    # step-farms: curved contour bands (old ones in the jungle, kept ones east of the gorge)
    farms = Image.new("RGB", (W, H), (0, 0, 0))
    fm = Image.new("L", (W, H), 0)
    fdr, fmd = ImageDraw.Draw(farms), ImageDraw.Draw(fm)
    tones = [(110, 112, 58), (92, 104, 50), (128, 116, 64), (84, 92, 46)]
    for (cx, cy, n, r0, a0, a1, kept) in [(880, 200, 7, 26, 200, 340, True), (900, 270, 5, 18, 190, 330, True),
                                          (420, 610, 5, 22, 0, 160, False), (530, 700, 4, 18, 200, 330, False)]:
        for i in range(n):
            r = r0 + i * 7
            pts = [(cx + math.cos(math.radians(a)) * r, cy + math.sin(math.radians(a)) * r * 0.62) for a in np.linspace(a0, a1, 24)]
            fdr.line(px(pts), fill=tones[i % len(tones)], width=int(5 * S), joint="curve")
            fmd.line(px(pts), fill=190 if kept else 110, width=int(5 * S), joint="curve")
    fm = fm.filter(ImageFilter.GaussianBlur(1.0))
    fmask = (np.asarray(fm, np.float32) / 255.0) * land * (1 - gorge - rim).clip(0, 1)
    col = lerp(col, (np.asarray(farms, np.float32) / 255.0) * shade[..., None], fmask)

    # ---- sea
    sea_deep = np.array([0.02, 0.07, 0.10])
    sea_mid = np.array([0.04, 0.15, 0.19])
    sea_shallow = np.array([0.1, 0.3, 0.31])
    sea = lerp(sea_mid, sea_deep, smoothstep(10, 120, d_out))
    sea = lerp(sea, sea_shallow, smoothstep(16, 0, d_out))
    waves = noise((H, W), 10, 2)
    sea *= (0.93 + 0.07 * waves)[..., None]
    rings = (np.sin(d_out * 0.9) * 0.5 + 0.5) * smoothstep(40, 6, d_out) * smoothstep(3, 8, d_out)
    sea = lerp(sea, sea_shallow * 1.2, rings * 0.12)
    foam = smoothstep(2.5, 0.0, d_out) * (1 - land)
    sea = lerp(sea, np.array([0.6, 0.7, 0.7]), foam * 0.55)
    img = lerp(sea, col, land_soft)
    rgb = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    base = Image.fromarray(rgb, "RGB").convert("RGBA")

    # ---- barrens detail: a web of dark cracks, violet glass growths, the fallen colossus
    det = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(det)
    for _ in range(140):
        x, y = RNG.uniform(590, 870), RNG.uniform(540, 750)
        if barrens[int(y * S), int(x * S)] < 0.55:
            continue
        a = RNG.uniform(0, 2 * math.pi)
        pts = [(x, y)]
        for _s in range(int(RNG.integers(3, 8))):
            a += RNG.normal(0, 0.5)
            x += math.cos(a) * 5
            y += math.sin(a) * 5
            pts.append((x, y))
        dd.line(px(pts), fill=(44, 22, 20, 200), width=S)
    for _ in range(70):
        x, y = RNG.uniform(600, 860), RNG.uniform(550, 740)
        if barrens[int(y * S), int(x * S)] < 0.6:
            continue
        s = RNG.uniform(1.2, 3.2)
        dd.polygon(px([(x, y - s * 1.6), (x + s * 0.6, y), (x, y + s * 0.4), (x - s * 0.6, y)]), fill=(120, 70, 140, 230))
        dd.point([(x * S, (y - s) * S)], fill=(210, 170, 230, 255))
    cx, cy = COLOSSUS
    ang = math.radians(-28)

    def rot(p, k=0.8):
        return (cx + k * (p[0] * math.cos(ang) - p[1] * math.sin(ang)), cy + k * (p[0] * math.sin(ang) + p[1] * math.cos(ang)))
    parts = [
        [(-30, -8), (10, -10), (20, -5), (19, 6), (8, 10), (-30, 8)],          # torso slab
        [(26, -7), (36, -6), (38, 5), (28, 8), (24, 1)],                       # the head, broken off
        [(6, -10), (-2, -22), (-7, -21), (1, -8)], [(-10, -26), (-16, -32), (-20, -30), (-14, -24)],   # an arm, snapped at the elbow
        [(4, 10), (-8, 18), (-14, 19), (-6, 12)],
        [(-30, -7), (-48, -9), (-50, -3), (-30, 0)], [(-30, 2), (-46, 8), (-47, 12), (-30, 7)],  # legs sunk into the plain
    ]
    parts = [[rot(p) for p in q] for q in parts]
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdr = ImageDraw.Draw(sh)
    for q in parts:
        sdr.polygon(px([(x + 2.2, y + 2.6) for x, y in q]), fill=(0, 0, 0, 130))
    sh = sh.filter(ImageFilter.GaussianBlur(2))
    base.alpha_composite(det)
    base.alpha_composite(sh)
    cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cdr = ImageDraw.Draw(cl)
    for k, q in enumerate(parts):
        c = (78 + (k % 3) * 6, 70 + (k % 3) * 5, 62 + (k % 3) * 4)
        cdr.polygon(px(q), fill=c + (255,), outline=(34, 28, 24, 255))
        cdr.line(px(q[:2]), fill=(126, 116, 100, 255), width=S)    # lit edge toward the north-west
    for _ in range(26):   # rubble around it
        a = RNG.uniform(0, 2 * math.pi)
        rr = RNG.uniform(16, 40)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.7
        s_ = RNG.uniform(0.8, 2.0)
        cdr.ellipse([(x - s_) * S, (y - s_) * S, (x + s_) * S, (y + s_) * S], fill=(92, 84, 74, 255), outline=(36, 30, 26, 255))
    for t in (-0.5, -0.1, 0.3):   # a seam of dead wire down its back
        q = rot((t * 40, -1))
        cdr.ellipse([(q[0] - 1.1) * S, (q[1] - 1.1) * S, (q[0] + 1.1) * S, (q[1] + 1.1) * S], fill=(200, 200, 196, 255))
    base.alpha_composite(cl)

    # ---- jungle: dense canopy stamps, emergent giants; thinner toward the barrens and on the east lobe
    density = np.zeros((H, W), np.float32)
    density += np.clip(ellipse_mask((456, 649), (170, 115), blur=40) * 1.3, 0, 1)
    density += np.clip(ellipse_mask((120, 560), (60, 100), blur=30), 0, 1) * 0.9
    density += np.clip(ellipse_mask((905, 650), (70, 110), blur=40), 0, 1) * 0.55
    density += np.clip(ellipse_mask((900, 150), (60, 80), blur=30), 0, 1) * 0.5
    density += smoothstep(340, 240, ay) * 0.4 * (1 - smoothstep(0.95, 1.2, height))
    density += np.clip(ellipse_mask((520, 770), (260, 40), blur=40), 0, 1) * 0.28   # scattered trees on the southern slopes
    clear_town = np.clip(ellipse_mask(AGDAO, (110, 100), blur=10), 0, 1)
    clear_cit = np.clip(ellipse_mask(CITADEL, (82, 72), blur=10), 0, 1)
    density *= land * (1 - barrens) * (1 - clear_town) * (1 - clear_cit) * (1 - fmask * 0.8) * smoothstep(6, 14, d_in)
    density *= smoothstep(10, 26, gd - half) * (1 - smoothstep(1.05, 1.3, height))
    density *= np.clip(0.7 + noise((H, W), 50, 3) * 0.6, 0, 1)
    density = np.clip(density, 0, 1)
    trees = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(trees)
    shadows = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadows)
    n_try = 300000
    xs = RNG.uniform(0, W, n_try)
    ys = RNG.uniform(0, H, n_try)
    keep = RNG.uniform(0, 1, n_try) < density[ys.astype(int), xs.astype(int)] * 0.5
    order = np.argsort(ys[keep])
    for x, y in zip(xs[keep][order], ys[keep][order]):
        big = RNG.random() < 0.05
        r = RNG.uniform(7.5, 10.5) if big else RNG.uniform(3.8, 6.4)
        sd.ellipse([x - r + 2.8, y - r * 0.8 + 3.6, x + r + 2.8, y + r * 0.8 + 3.6], fill=(0, 0, 0, 110))
        g = RNG.uniform(0.75, 1.12)
        if big:
            c = (int(46 * g), int(70 * g), int(40 * g), 255)
        else:
            c = (int(22 * g), int(52 * g), int(36 * g), 255) if RNG.random() < 0.7 else (int(34 * g), int(60 * g), int(30 * g), 255)
        td.ellipse([x - r, y - r, x + r, y + r], fill=c)
        hl = (int(c[0] * 1.5 + 8), int(c[1] * 1.45 + 8), int(c[2] * 1.3 + 4), 200)
        td.ellipse([x - r * 0.65, y - r * 0.75, x + r * 0.15, y + r * 0.05], fill=hl)
    shadows = shadows.filter(ImageFilter.GaussianBlur(1.6))
    base.alpha_composite(shadows)
    base.alpha_composite(trees)


    # ---- mountains along the north coast and around the citadel plateau
    mt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(mt)
    peaks = []
    for _ in range(200):
        x, y = RNG.uniform(100, 960), RNG.uniform(60, 330)
        ix, iy = int(x * S), int(y * S)
        if not (0 <= ix < W and 0 <= iy < H):
            continue
        if height[iy, ix] > 0.72 and gd[iy, ix] > half[iy, ix] + 14 and land[iy, ix] > 0.5 and d_in[iy, ix] > 8:
            peaks.append((x, y, height[iy, ix]))
    peaks.sort(key=lambda p: p[1])
    for x, y, hv in peaks:
        s = RNG.uniform(11, 18) * min(1.3, hv)
        pts = [(x - s, y + s * 0.55), (x - s * 0.1, y - s * 0.9), (x + s, y + s * 0.55)]
        md.polygon(px(pts), fill=(92, 78, 62, 235))
        md.polygon(px([(x - s * 0.1, y - s * 0.9), (x + s, y + s * 0.55), (x + s * 0.2, y + s * 0.55)]), fill=(56, 46, 38, 235))
        md.polygon(px([(x - s * 0.36, y - s * 0.38), (x - s * 0.1, y - s * 0.9), (x + s * 0.18, y - s * 0.4)]), fill=(168, 152, 128, 235))
    base.alpha_composite(mt)

    # ---- the Bridge of Death: a stone span over the gorge with gatehouses and three ward pylons
    br = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(br)
    X, N_, S_ = BRIDGE_X, BRIDGE_N, BRIDGE_S
    bd.line(px([(X + 4, N_ + 2), (X + 4, S_ + 2)]), fill=(0, 0, 0, 150), width=int(6 * S))
    bd.line(px([(X, N_), (X, S_)]), fill=(40, 34, 30, 255), width=int(7 * S))
    bd.line(px([(X, N_), (X, S_)]), fill=(132, 120, 100, 255), width=int(4.4 * S))
    bd.line(px([(X - 1.2, N_), (X - 1.2, S_)]), fill=(170, 158, 134, 255), width=S)
    for t in (0.3, 0.5, 0.7):   # the three ward pylons
        y = N_ + (S_ - N_) * t
        bd.rectangle([(X - 6) * S, (y - 2.4) * S, (X + 6) * S, (y + 2.4) * S], fill=(70, 62, 54, 255), outline=(30, 26, 22, 255))
        bd.ellipse([(X - 1.2) * S, (y - 1.2) * S, (X + 1.2) * S, (y + 1.2) * S], fill=(236, 236, 232, 255))
    for y in (N_ - 5, S_ + 5):   # gatehouses
        bd.rectangle([(X - 9) * S, (y - 7) * S, (X + 9) * S, (y + 7) * S], fill=(112, 102, 86, 255), outline=(36, 30, 26, 255), width=S)
        bd.rectangle([(X - 6) * S, (y - 4) * S, (X + 6) * S, (y + 4) * S], fill=(86, 78, 66, 255))
    base.alpha_composite(br)

    # ---- the Heart Citadel: stepped walls on the plateau, the Dawn Engine's pyramid, a dim corrupted glow
    ct = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(ct)
    cx, cy = CITADEL
    for k, (hw, hh, c) in enumerate([(52, 44, (96, 90, 74)), (44, 37, (112, 104, 86)), (36, 30, (104, 98, 80))]):
        cd.rectangle([(cx - hw) * S, (cy - hh) * S, (cx + hw) * S, (cy + hh) * S], fill=c + (255,), outline=(44, 38, 32, 255), width=S)
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):   # corner towers
        tx, ty = cx + sx * 52, cy + sy * 44
        cd.rectangle([(tx - 6) * S, (ty - 6) * S, (tx + 6) * S, (ty + 6) * S], fill=(120, 110, 92, 255), outline=(40, 34, 30, 255), width=S)
    cd.rectangle([(cx - 4) * S, (cy + 40) * S, (cx + 4) * S, (cy + 50) * S], fill=(70, 64, 54, 255))   # south gate
    for k in range(5):   # the stepped pyramid of the Dawn Engine
        s = 20 - k * 4
        g = 128 + k * 12
        cd.rectangle([(cx - s) * S, (cy - s) * S, (cx + s) * S, (cy + s) * S], fill=(g, g - 10, g - 30, 255), outline=(50, 44, 36, 255), width=S)
        cd.rectangle([(cx) * S, (cy - s) * S, (cx + s) * S, (cy + s) * S], fill=(int(g * 0.8), int((g - 10) * 0.78), int((g - 30) * 0.76), 255), outline=(50, 44, 36, 255), width=S)
    for (x, y) in [(cx - 30, cy + 22), (cx + 24, cy - 24), (cx - 22, cy - 26), (cx + 28, cy + 20), (cx - 10, cy + 30), (cx + 8, cy - 30)]:
        cd.rectangle([(x - 4) * S, (y - 3) * S, (x + 4) * S, (y + 3) * S], fill=(140, 120, 96, 255))
    for (x, y) in [(cx - 22, cy + 62), (cx - 34, cy + 70), (cx + 20, cy + 66), (cx + 32, cy + 74)]:   # siege tents
        cd.polygon(px([(x - 4, y + 3), (x, y - 4), (x + 4, y + 3)]), fill=(70, 66, 64, 255), outline=(30, 28, 28, 255))
    base.alpha_composite(ct)
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([(cx - 14) * S, (cy - 14) * S, (cx + 14) * S, (cy + 14) * S], fill=(235, 235, 230, 90))
    gl = gl.filter(ImageFilter.GaussianBlur(10))
    base.alpha_composite(gl)

    # ---- Agdao: contour terraces stepping down from the Crown of Steps to the quay on the bay
    tw = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tdw = ImageDraw.Draw(tw)
    px0, py0 = PYRAMID
    radii = [22, 35, 48, 61, 74, 86]
    a0, a1 = 4, 176
    wob = np.random.default_rng(31).uniform(0, 6.28, 3)

    def sector(r_in, r_out, ky=0.86):
        def rr(r, a):
            return r * (1 + 0.07 * math.sin(math.radians(a) * 3 + wob[0]) + 0.04 * math.sin(math.radians(a) * 7 + wob[1])) if r else 0
        outer = [(px0 + math.cos(math.radians(a)) * rr(r_out, a), py0 + math.sin(math.radians(a)) * rr(r_out, a) * ky) for a in np.linspace(a0, a1, 40)]
        inner = [(px0 + math.cos(math.radians(a)) * rr(r_in, a), py0 + math.sin(math.radians(a)) * rr(r_in, a) * ky) for a in np.linspace(a1, a0, 40)]
        return outer, inner
    for k in range(len(radii) - 1, -1, -1):   # outermost (lowest) first
        r_out = radii[k]
        r_in = radii[k - 1] if k else 0
        outer, inner = sector(r_in, r_out)
        g = 104 + (len(radii) - k) * 6
        tdw.polygon(px(outer + inner), fill=(g, g - 7, g - 24, 255))
        tdw.line(px(outer), fill=(40, 34, 28, 255), width=int(2.2 * S))         # the riser's shadow
        tdw.line(px([(x, y - 1.4) for x, y in outer]), fill=(g + 34, g + 26, g + 6, 255), width=S)   # lit lip
    for a in (64, 118):   # stairs down the terraces
        p0 = (px0 + math.cos(math.radians(a)) * 16, py0 + math.sin(math.radians(a)) * 14)
        p1 = (px0 + math.cos(math.radians(a)) * 86, py0 + math.sin(math.radians(a)) * 74)
        tdw.line(px([p0, p1]), fill=(176, 166, 140, 255), width=int(3 * S))
        tdw.line(px([p0, p1]), fill=(120, 110, 92, 255), width=S)
    hr = np.random.default_rng(29)
    for i_ in range(150):   # houses on the terraces: lime plaster walls, flat roofs (pale, ochre, red)
        k = int(hr.integers(1, len(radii)))
        rr = hr.uniform(radii[k - 1] + 4, radii[k] - 3)
        a = math.radians(hr.uniform(a0 + 6, a1 - 6))
        if any(abs(math.degrees(a) - st) < 5 for st in (64, 118)):
            continue
        x, y = px0 + math.cos(a) * rr, py0 + math.sin(a) * rr * 0.86
        w, h = hr.uniform(2.4, 4.2), hr.uniform(1.8, 3.0)
        roof = [(186, 172, 146), (166, 120, 78), (146, 74, 56), (178, 152, 116)][int(hr.integers(0, 4))]
        tdw.rectangle([(x - w) * S, (y - h) * S, (x + w) * S, (y + h) * S], fill=roof + (255,), outline=(46, 38, 30, 255))
        tdw.rectangle([(x - w) * S, (y + h * 0.35) * S, (x + w) * S, (y + h) * S], fill=tuple(int(v * 0.68) for v in roof) + (255,))
    for k in range(5):   # the Crown of Steps
        s_ = 16 - k * 3
        g = 150 + k * 10
        tdw.rectangle([(px0 - s_) * S, (py0 - s_) * S, (px0 + s_) * S, (py0 + s_) * S], fill=(g, g - 8, g - 26, 255), outline=(52, 44, 36, 255), width=S)
        tdw.rectangle([px0 * S, (py0 - s_) * S, (px0 + s_) * S, (py0 + s_) * S], fill=(int(g * 0.8), int((g - 8) * 0.78), int((g - 26) * 0.76), 255), outline=(52, 44, 36, 255), width=S)
    wall = [(px0 + math.cos(math.radians(a)) * 30, py0 + math.sin(math.radians(a)) * 26) for a in np.linspace(186, 354, 24)]
    tdw.line(px(wall), fill=(52, 44, 38, 255), width=int(3.2 * S), joint="curve")
    tdw.line(px(wall), fill=(150, 138, 114, 255), width=int(1.6 * S), joint="curve")
    for a in (300, 322):   # towers flanking the north-east gate of the upper town
        q = (px0 + math.cos(math.radians(a)) * 30, py0 + math.sin(math.radians(a)) * 26)
        tdw.rectangle([(q[0] - 3) * S, (q[1] - 3) * S, (q[0] + 3) * S, (q[1] + 3) * S], fill=(140, 128, 106, 255), outline=(40, 34, 28, 255))
    harbour = [(x + DX, y + DY) for x, y in [(140, 636), (248, 636), (240, 664), (226, 670), (200, 666), (176, 666), (156, 672), (146, 664)]]
    tdw.polygon(px(harbour), fill=(112, 104, 86, 255), outline=(44, 38, 30, 255))   # the harbour terrace
    for i_ in range(14):
        x, y = 150 + DX + i_ * 6.6 + hr.uniform(-1, 1), 646 + DY + hr.uniform(-4, 4)
        tdw.rectangle([(x - 2.4) * S, (y - 2) * S, (x + 2.4) * S, (y + 2) * S], fill=(160, 120, 80, 255), outline=(46, 38, 30, 255))
    quay = [(x + DX, y + DY) for x, y in [(150, 666), (176, 664), (204, 664), (230, 668)]]
    tdw.line(px(quay), fill=(48, 40, 32, 255), width=int(5 * S), joint="curve")
    tdw.line(px(quay), fill=(132, 122, 100, 255), width=int(3.4 * S), joint="curve")
    for (x0, x1, y1) in [(170, 174, 694), (188, 192, 702), (206, 210, 692)]:   # piers into the bay
        tdw.rectangle([(x0 + DX) * S, (666 + DY) * S, (x1 + DX) * S, (y1 + DY) * S], fill=(96, 72, 48, 255), outline=(40, 30, 22, 255))
    base.alpha_composite(tw)
    lights = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lights)
    for _ in range(16):   # the few lamps still burning (Zarael's glows are all white)
        a = math.radians(RNG.uniform(-5, 185))
        rr = RNG.uniform(20, 90)
        x, y = PYRAMID[0] + math.cos(a) * rr, PYRAMID[1] + math.sin(a) * rr * 0.86
        ld.ellipse([(x - 1.6) * S, (y - 1.6) * S, (x + 1.6) * S, (y + 1.6) * S], fill=(240, 240, 236, 170))
    lights = lights.filter(ImageFilter.GaussianBlur(2.2))
    base.alpha_composite(lights)

    # ---- grain and vignette (as Salmonan)
    arr = np.asarray(base.convert("RGB"), np.float32) / 255.0
    grain = RNG.normal(0, 0.018, (H, W, 1)).astype(np.float32)
    vx = (xx / W - 0.5) * 2
    vy = (yy / H - 0.5) * 2
    vig = 1.0 - 0.35 * smoothstep(0.55, 1.45, np.sqrt(vx * vx + vy * vy))
    arr = np.clip((arr + grain) * vig[..., None] * np.array([1.02, 1.0, 0.96]), 0, 1)
    out = Image.fromarray((arr * 255).astype(np.uint8), "RGB")
    out.save(OUT / "zarael_atlas.png", optimize=True)
    write_import()

    # ---- evidence: region centres and footprints over the painting (labels only here, never in the art)
    ev = out.resize((1000, 850), Image.LANCZOS).convert("RGBA")
    ov = Image.new("RGBA", ev.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for name, r in REGIONS.items():
        x0, y0, x1, y1 = r["box"]
        od.rectangle([x0, y0, x1, y1], outline=(255, 230, 140, 200), width=2)
        cx, cy = r["centre"]
        od.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 80, 80, 255))
        od.text((x0 + 4, y0 + 4), f"{name} {r['centre']}", fill=(255, 245, 210, 255))
    ev.alpha_composite(ov)
    ev.convert("RGB").save(EVI / "atlas_regions.png")
    print("wrote", OUT / "zarael_atlas.png")


def write_import():
    src = OUT / "salmonan_atlas.png.import"
    txt = src.read_text(encoding="utf-8")
    res = "res://assets/ui/atlas/zarael_atlas.png"
    md5 = hashlib.md5(res.encode()).hexdigest()
    lines = []
    for line in txt.splitlines():
        if line.startswith("uid="):
            continue
        line = line.replace("res://assets/ui/atlas/salmonan_atlas.png", res)
        line = line.replace("salmonan_atlas.png-8849b1eed644bbf6c83378b2affa2069", f"zarael_atlas.png-{md5}")
        lines.append(line)
    (OUT / "zarael_atlas.png.import").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
