"""Raster UI-art toolkit for Beyond Heroes (bh-002).

Signed-distance-field shapes + height-field lighting, rendered with numpy/scipy and supersampled, so frames get real
bevels, engraving, gem domes and glows without any third-party image data. Everything is deterministic.

Conventions
-----------
* A ``Canvas`` is authored in *design pixels* (= final texture pixels). Internally it is ``ss`` times larger and
  box-filtered down on export, giving clean anti-aliasing.
* SDFs are full-size float32 arrays in design-pixel units, negative inside. Shapes built from point lists are only
  evaluated inside their bounding box (+margin); outside they read ``BIG``.
* Colours are sRGB floats 0..1. The canvas stores premultiplied RGB + alpha.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image
from scipy import ndimage

BIG = 1.0e4
F = np.float32

# light from the top-left, slightly in front
LIGHT = np.array([-0.52, -0.62, 0.59], F)
LIGHT /= np.linalg.norm(LIGHT)


# ------------------------------------------------------------------------------------------ colour

def C(c, a=None):
    """'#rrggbb' -> np.array([r,g,b]) floats."""
    if isinstance(c, np.ndarray):
        return c.astype(F)
    if isinstance(c, (tuple, list)):
        return np.array(c[:3], F)
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], F)


def cmix(a, b, t):
    return C(a) * (1 - t) + C(b) * t


def ramp(values, stops):
    """Map a float array (0..1) through colour stops [(pos, '#hex'), ...] -> (...,3)."""
    pos = np.array([s[0] for s in stops], F)
    cols = np.stack([C(s[1]) for s in stops])
    v = np.clip(values, 0, 1)
    out = np.empty(v.shape + (3,), F)
    for k in range(3):
        out[..., k] = np.interp(v, pos, cols[:, k])
    return out


def even_ramp(colors):
    n = len(colors)
    return [(i / (n - 1), c) for i, c in enumerate(colors)]


# ------------------------------------------------------------------------------------------ materials
# ramp: colours indexed by lambert term (0 = facing away, 1 = facing the light).  Flat tops read ~0.6.

MAT = {
    "gold": dict(ramp=even_ramp(["#1e1004", "#5c3a10", "#a8741e", "#e0b050", "#ffe49a", "#fff6d8"]), spec="#fff8e0", sp=0.55, pw=28),
    "gold_dim": dict(ramp=even_ramp(["#140a03", "#3c260c", "#7a5420", "#b88c52", "#e8c888"]), spec="#ffe8c0", sp=0.35, pw=22),
    "bronze": dict(ramp=even_ramp(["#140a04", "#3a220e", "#6b4a26", "#b88c52", "#e8c08a", "#fbe2bc"]), spec="#ffe6c4", sp=0.45, pw=24),
    "iron": dict(ramp=even_ramp(["#040405", "#0d0d10", "#18171c", "#26252c", "#403e48", "#6e6a78"]), spec="#b8b0c4", sp=0.28, pw=18),
    "iron_warm": dict(ramp=even_ramp(["#070504", "#15100d", "#261d17", "#3c3029", "#5e4d40", "#8a7461"]), spec="#d8c4a8", sp=0.28, pw=18),
    "steel": dict(ramp=even_ramp(["#0c0e12", "#2a2f38", "#566070", "#8e98a8", "#cfd6e0", "#ffffff"]), spec="#ffffff", sp=0.55, pw=30),
    "silver": dict(ramp=even_ramp(["#10141c", "#34405a", "#6e7e9c", "#aebcd4", "#e4ecf8", "#ffffff"]), spec="#ffffff", sp=0.6, pw=30),
    "stone": dict(ramp=even_ramp(["#070608", "#141216", "#1f1c22", "#2d2a31", "#403c44"]), spec="#8a8490", sp=0.10, pw=10),
    "leather": dict(ramp=even_ramp(["#070403", "#130c09", "#1e1510", "#2a1e17", "#3a2a20"]), spec="#6a5040", sp=0.08, pw=8),
    "crimson": dict(ramp=even_ramp(["#140204", "#3e060e", "#7a1020", "#b81a2a", "#ea5a60", "#ffc0b8"]), spec="#ffe0d8", sp=0.5, pw=26),
    "blue_steel": dict(ramp=even_ramp(["#040814", "#0e1c3c", "#23407a", "#4a78c4", "#9ec0f4", "#eef6ff"]), spec="#ffffff", sp=0.55, pw=28),
    "aether": dict(ramp=even_ramp(["#02202a", "#0a5a6e", "#20a8c0", "#7ff3ff", "#d8fdff", "#ffffff"]), spec="#ffffff", sp=0.9, pw=40),
    "violet": dict(ramp=even_ramp(["#0e0420", "#2e0e5a", "#5c2aa8", "#9e73ff", "#dcc8ff", "#ffffff"]), spec="#ffffff", sp=0.7, pw=34),
    "ruby": dict(ramp=even_ramp(["#1a0204", "#50060e", "#a0101e", "#ff3a40", "#ffb0a8", "#ffffff"]), spec="#ffffff", sp=0.8, pw=40),
    "glass": dict(ramp=even_ramp(["#05070c", "#0b1018", "#121a24", "#1c2632", "#2c3a48"]), spec="#e8fbff", sp=0.55, pw=36),
}


def tint_mat(base: str, dark="#050404", light="#ffffff", sp=0.45, pw=24, spec=None, steps=(0.93, 0.72, 0.42, 0.0, 0.45, 0.85)):
    """Build a metal ramp around an arbitrary base colour."""
    cols = []
    for i, s in enumerate(steps):
        if i < 3:
            cols.append(cmix(base, dark, s))
        elif i == 3:
            cols.append(C(base))
        else:
            cols.append(cmix(base, light, s))
    return dict(ramp=[(i / 5, c) for i, c in enumerate(cols)], spec=spec or light, sp=sp, pw=pw)


# ------------------------------------------------------------------------------------------ canvas

class Canvas:
    def __init__(self, w: int, h: int, ss: int = 2):
        self.w, self.h, self.ss = int(w), int(h), int(ss)
        self.W, self.H = self.w * self.ss, self.h * self.ss
        xs = ((np.arange(self.W, dtype=F) + 0.5) / self.ss).astype(F)
        ys = ((np.arange(self.H, dtype=F) + 0.5) / self.ss).astype(F)
        self.X, self.Y = np.meshgrid(xs, ys)
        self.rgb = np.zeros((self.H, self.W, 3), F)
        self.a = np.zeros((self.H, self.W), F)

    # ---- compositing (premultiplied)
    def over(self, color, alpha, op=1.0):
        a = np.clip(alpha * op, 0, 1).astype(F)
        col = C(color) if not isinstance(color, np.ndarray) or color.ndim == 1 else color
        self.rgb = col * a[..., None] + self.rgb * (1 - a[..., None])
        self.a = a + self.a * (1 - a)

    def put(self, layer):
        """Composite a (rgb, alpha) layer."""
        rgb, a = layer
        self.over(rgb, a)

    def add_light(self, color, amount):
        """Additive light that only affects already-painted pixels (keeps alpha)."""
        self.rgb = self.rgb + C(color) * (np.clip(amount, 0, None) * self.a)[..., None]

    def glow(self, mask, color, sigma, strength=1.0, gain=1.0):
        """Soft halo from a coverage mask: composited *over* (visible on transparent areas too)."""
        g = ndimage.gaussian_filter(mask.astype(F), sigma * self.ss) * gain
        self.over(color, np.clip(g, 0, 1) * strength)
        return g

    def shadow(self, mask, dx=1.5, dy=2.5, blur=3.0, op=0.7, color="#000000"):
        m = ndimage.shift(mask.astype(F), (dy * self.ss, dx * self.ss), order=1, mode="constant")
        m = ndimage.gaussian_filter(m, blur * self.ss)
        self.over(color, np.clip(m, 0, 1), op)

    def erase(self, mask):
        k = 1 - np.clip(mask, 0, 1)
        self.rgb *= k[..., None]
        self.a *= k

    def clamp(self):
        self.rgb = np.minimum(self.rgb, self.a[..., None])

    # ---- export
    def image(self) -> Image.Image:
        s = self.ss
        rgb = np.minimum(np.clip(self.rgb, 0, None), self.a[..., None] + 1e-6)
        rgb = rgb.reshape(self.h, s, self.w, s, 3).mean(axis=(1, 3))
        a = self.a.reshape(self.h, s, self.w, s).mean(axis=(1, 3))
        out = np.zeros((self.h, self.w, 4), F)
        nz = a > 1e-5
        out[..., :3][nz] = rgb[nz] / a[nz][:, None]
        out[..., 3] = a
        return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")

    def save(self, path):
        self.image().save(path, optimize=True)
        return path

    # ---- coordinate helpers
    def region(self, x0, y0, x1, y1, m=6.0):
        s = self.ss
        i0 = max(0, int(math.floor((y0 - m) * s)))
        i1 = min(self.H, int(math.ceil((y1 + m) * s)))
        j0 = max(0, int(math.floor((x0 - m) * s)))
        j1 = min(self.W, int(math.ceil((x1 + m) * s)))
        if i1 <= i0 or j1 <= j0:
            return None
        return (slice(i0, i1), slice(j0, j1))

    def empty(self, v=BIG):
        return np.full((self.H, self.W), v, F)


# ------------------------------------------------------------------------------------------ SDF primitives

def cov(cv: Canvas, sd, soft=0.0):
    """Coverage 0..1 from a signed distance (design px); AA width = 1 internal pixel (+soft)."""
    w = 1.0 / cv.ss + soft
    return np.clip(0.5 - sd / w, 0, 1).astype(F)


def sd_circle(cv, cx, cy, r):
    return (np.hypot(cv.X - cx, cv.Y - cy) - r).astype(F)


def sd_ellipse(cv, cx, cy, rx, ry):
    # cheap approximation, good near the boundary for moderate eccentricity
    k = np.hypot((cv.X - cx) / rx, (cv.Y - cy) / ry)
    return ((k - 1.0) * min(rx, ry)).astype(F)


def sd_box(cv, cx, cy, hw, hh, r=0.0):
    qx = np.abs(cv.X - cx) - (hw - r)
    qy = np.abs(cv.Y - cy) - (hh - r)
    out = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    return out.astype(F)


def sd_rect(cv, x0, y0, x1, y1, r=0.0):
    return sd_box(cv, (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, r)


def sd_chamfer_box(cv, cx, cy, hw, hh, c):
    """Box with 45-degree cut corners of size c."""
    ax = np.abs(cv.X - cx)
    ay = np.abs(cv.Y - cy)
    b = np.maximum(ax - hw, ay - hh)
    d = (ax + ay - (hw + hh - c)) / math.sqrt(2)
    return np.maximum(b, d).astype(F)


def sd_poly(cv, pts, margin=6.0):
    """Exact signed distance to a polygon (even-odd), evaluated in its bbox."""
    P = np.asarray(pts, dtype=np.float64)
    out = cv.empty()
    sl = cv.region(P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max(), margin)
    if sl is None:
        return out
    X = cv.X[sl].astype(np.float64)
    Y = cv.Y[sl].astype(np.float64)
    d = np.full(X.shape, np.inf)
    s = np.ones(X.shape)
    n = len(P)
    for i in range(n):
        ax, ay = P[i]
        bx, by = P[i - 1]
        ex, ey = bx - ax, by - ay
        wx, wy = X - ax, Y - ay
        ee = ex * ex + ey * ey
        t = np.clip((wx * ex + wy * ey) / ee, 0, 1) if ee > 0 else np.zeros_like(X)
        dx, dy = wx - ex * t, wy - ey * t
        np.minimum(d, dx * dx + dy * dy, out=d)
        c1 = Y >= ay
        c2 = Y < by
        c3 = ex * wy > ey * wx
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s[flip] *= -1
    out[sl] = (s * np.sqrt(d)).astype(F)
    return out


def sd_stroke(cv, pts, w0, w1=None, closed=False, margin=None, cap=True):
    """Distance to a polyline minus a half-width linearly interpolated w0->w1 along its length (tapered strokes)."""
    P = np.asarray(pts, dtype=np.float64)
    if closed:
        P = np.vstack([P, P[:1]])
    w1 = w0 if w1 is None else w1
    seg = np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1]))
    L = np.concatenate([[0], np.cumsum(seg)])
    tot = L[-1] if L[-1] > 0 else 1.0
    wmax = max(w0, w1)
    out = cv.empty()
    m = (margin if margin is not None else 3.0) + wmax
    sl = cv.region(P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max(), m)
    if sl is None:
        return out
    X = cv.X[sl].astype(np.float64)
    Y = cv.Y[sl].astype(np.float64)
    best = np.full(X.shape, np.inf)
    for i in range(len(P) - 1):
        ax, ay = P[i]
        bx, by = P[i + 1]
        ex, ey = bx - ax, by - ay
        ee = ex * ex + ey * ey
        wx, wy = X - ax, Y - ay
        t = np.clip((wx * ex + wy * ey) / ee, 0, 1) if ee > 0 else np.zeros_like(X)
        dist = np.hypot(wx - ex * t, wy - ey * t)
        u = (L[i] + seg[i] * t) / tot
        hw = (w0 + (w1 - w0) * u) / 2.0
        np.minimum(best, dist - hw, out=best)
    out[sl] = best.astype(F)
    return out


def union(*sds):
    out = sds[0]
    for s in sds[1:]:
        out = np.minimum(out, s)
    return out


def inter(a, b):
    return np.maximum(a, b)


def sub(a, b):
    return np.maximum(a, -b)


def smooth_union(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return (b * (1 - h) + a * h - k * h * (1 - h)).astype(F)


def ring_of(sd, w):
    """Outline band of width w centred on the boundary of sd."""
    return (np.abs(sd) - w / 2.0).astype(F)


def shell(sd, w):
    """Inner band of width w just inside the boundary."""
    return np.maximum(sd, -sd - w).astype(F)


# ------------------------------------------------------------------------------------------ curve helpers

def bez3(p0, p1, p2, p3, n=24):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
    return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3).tolist()


def bez2(p0, p1, p2, n=20):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = (np.asarray(p, float) for p in (p0, p1, p2))
    return ((1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2).tolist()


def arc(cx, cy, r, a0, a1, n=32, ry=None):
    ry = r if ry is None else ry
    t = np.linspace(a0, a1, n)
    return list(zip(cx + r * np.cos(t), cy + ry * np.sin(t)))


def spiral(cx, cy, r0, r1, a0, a1, n=48):
    """Archimedean-ish spiral from radius r0 at a0 to r1 at a1 (radians)."""
    t = np.linspace(0, 1, n)
    a = a0 + (a1 - a0) * t
    r = r0 + (r1 - r0) * t
    return list(zip(cx + r * np.cos(a), cy + r * np.sin(a)))


def catmull(pts, n=12, closed=False):
    P = [np.asarray(p, float) for p in pts]
    out = []
    m = len(P)
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = P[(i - 1) % m] if closed else P[max(i - 1, 0)]
        p1 = P[i]
        p2 = P[(i + 1) % m]
        p3 = P[(i + 2) % m] if closed else P[min(i + 2, m - 1)]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            v = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            out.append(v.tolist())
    if not closed:
        out.append(P[-1].tolist())
    return out


def xf(pts, tx=0.0, ty=0.0, a=0.0, s=1.0, sx=None, sy=None, mx=False, my=False, cx=0.0, cy=0.0):
    """Transform points: optional mirror about (cx,cy), scale, rotate (deg), translate."""
    sx = s if sx is None else sx
    sy = s if sy is None else sy
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    out = []
    for x, y in pts:
        x, y = x - cx, y - cy
        if mx:
            x = -x
        if my:
            y = -y
        x, y = x * sx, y * sy
        x, y = x * ca - y * sa, x * sa + y * ca
        out.append((x + cx + tx, y + cy + ty))
    return out


def star(cx, cy, n, r1, r2, rot=-math.pi / 2):
    return [(cx + (r1 if i % 2 == 0 else r2) * math.cos(rot + i * math.pi / n),
             cy + (r1 if i % 2 == 0 else r2) * math.sin(rot + i * math.pi / n)) for i in range(2 * n)]


def ngon(cx, cy, r, n, rot=-math.pi / 2):
    return [(cx + r * math.cos(rot + i * 2 * math.pi / n), cy + r * math.sin(rot + i * 2 * math.pi / n)) for i in range(n)]


def leaf(p0, p1, w, bend=0.0, n=16):
    """Pointed leaf / petal polygon from p0 to p1 with max width w."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = np.hypot(*d) or 1.0
    nrm = np.array([-d[1], d[0]]) / L
    t = np.linspace(0, 1, n)
    wid = np.sin(np.pi * t) ** 0.8 * w / 2
    off = np.sin(np.pi * t) * bend
    left = p0 + d * t[:, None] + nrm * (wid + off)[:, None]
    right = p0 + d * t[:, None] - nrm * (wid - off)[:, None]
    return np.vstack([left, right[::-1][1:-1]]).tolist()


# ------------------------------------------------------------------------------------------ noise

def fnoise(h, w, seed, beta=2.0, lo=1.0, hi=None):
    """Periodic (tileable) 1/f^beta noise, zero mean, unit std. Frequencies below `lo` are removed."""
    rng = np.random.default_rng(seed)
    wn = rng.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.fftfreq(w)[None, :] * w
    fr = np.hypot(fx, fy)
    amp = np.where(fr >= lo, 1.0 / np.maximum(fr, 1e-6) ** (beta / 2), 0.0)
    if hi is not None:
        amp = amp * np.exp(-(fr / hi) ** 2)
    out = np.real(np.fft.ifft2(np.fft.fft2(wn) * amp))
    sd = out.std() or 1.0
    return ((out - out.mean()) / sd).astype(F)


def canvas_noise(cv, seed, beta=2.0, scale=1.0, lo=1.0):
    """Noise sized to the internal canvas; `scale` ~ feature size multiplier."""
    n = fnoise(cv.H, cv.W, seed, beta, lo=lo, hi=max(cv.H, cv.W) / (2.0 * scale * cv.ss) if scale else None)
    return n


# ------------------------------------------------------------------------------------------ height + lighting

def profile(sd, bevel, kind="round"):
    """Height 0..1 from a signed distance: rises over `bevel` px inside the shape."""
    t = np.clip(-sd / max(bevel, 1e-3), 0, 1)
    if kind == "round":
        return np.sqrt(np.clip(1 - (1 - t) ** 2, 0, 1)).astype(F)
    if kind == "chisel":
        return t.astype(F)
    if kind == "soft":
        return (t * t * (3 - 2 * t)).astype(F)
    if kind == "cove":  # concave: rises late
        return (t ** 2).astype(F)
    raise ValueError(kind)


def light_terms(cv, h, blur=0.35, light=LIGHT, pw=24):
    """Return (lambert 0..1, specular 0..1) for a height field in design px."""
    if blur:
        h = ndimage.gaussian_filter(h, blur * cv.ss)
    gy, gx = np.gradient(h)
    gx = gx * cv.ss
    gy = gy * cv.ss
    nz = 1.0 / np.sqrt(gx * gx + gy * gy + 1.0)
    nx, ny = -gx * nz, -gy * nz
    lam = nx * light[0] + ny * light[1] + nz * light[2]
    # blinn half-vector with viewer at +z
    hv = light + np.array([0, 0, 1], F)
    hv /= np.linalg.norm(hv)
    nh = np.clip(nx * hv[0] + ny * hv[1] + nz * hv[2], 0, 1)
    spec = nh ** pw
    lam01 = np.clip(0.5 + 0.5 * lam, 0, 1)  # remap -1..1 -> 0..1 (flat ~0.79)
    return lam01.astype(F), spec.astype(F)


def shade(cv, h, mat, tint_noise=None, noise_amt=0.0, bright=1.0, flat_level=None):
    """Colour a height field with a material dict -> rgb array."""
    lam, spec = light_terms(cv, h, pw=mat.get("pw", 24))
    # flat surfaces map to ~0.79 lambert; pull the ramp so a flat top reads as the material's mid tone
    v = (lam - 0.79) * 1.9 + (flat_level if flat_level is not None else 0.55)
    if tint_noise is not None and noise_amt:
        v = v + tint_noise * noise_amt
    rgb = ramp(v * bright, mat["ramp"])
    rgb = rgb + C(mat["spec"]) * (spec * mat.get("sp", 0.4))[..., None]
    return rgb


def metal(cv, sd, mat, bevel=4.0, kind="round", height=1.0, extra_h=None, noise=None, noise_amt=0.0, flat=None,
          bright=1.0):
    """Shaded layer (rgb, alpha) for a raised shape."""
    h = profile(sd, bevel, kind) * bevel * height
    if extra_h is not None:
        h = h + extra_h
    rgb = shade(cv, h, mat, noise, noise_amt, bright=bright, flat_level=flat)
    return rgb, cov(cv, sd)


def groove_h(cv, sd_line, width, depth):
    """Negative height for engraved grooves along a stroke SDF (sd_line = distance to centre line)."""
    t = np.clip(1 - np.abs(sd_line + 0) / (width / 2.0), 0, 1)
    return (-depth * np.sqrt(t)).astype(F)


def paint(cv, sd, color, op=1.0, soft=0.0):
    cv.over(color, cov(cv, sd, soft), op)


def gem(cv, cx, cy, r, mat, glow=None, glow_sigma=None, glow_str=0.9, facets=0, rot=0.0, setting="gold", setting_w=None):
    """Domed cabochon (facets=0) or faceted gem in a metal bezel, with optional outer glow."""
    sw = setting_w if setting_w is not None else max(1.5, r * 0.28)
    if setting:
        sds = sd_circle(cv, cx, cy, r + sw)
        cv.shadow(cov(cv, sds), 0.8, 1.4, max(1.0, r * 0.25), 0.8)
        cv.put(metal(cv, sds, MAT[setting] if isinstance(setting, str) else setting, bevel=sw * 0.9))
    if glow:
        m = cov(cv, sd_circle(cv, cx, cy, r))
        cv.glow(m, glow, glow_sigma or r * 0.9, glow_str, gain=1.6)
    if facets:
        pts = ngon(cx, cy, r, facets, rot)
        sd = sd_poly(cv, pts, margin=3)
        # faceted height: pyramid (chisel) profile
        h = profile(sd, r * 0.9, "chisel") * r * 0.55
    else:
        sd = sd_circle(cv, cx, cy, r)
        h = profile(sd, r, "round") * r * 0.9
    lam, spec = light_terms(cv, h, pw=mat.get("pw", 36))
    v = (lam - 0.79) * 2.2 + 0.38
    # inner glow: brighter toward lower-right (light passing through the stone), dark rim
    d = np.hypot(cv.X - (cx + r * 0.25), cv.Y - (cy + r * 0.3)) / max(r, 1e-3)
    v = v + np.clip(0.75 - d, 0, 1) * 0.75
    dc = np.hypot(cv.X - cx, cv.Y - cy) / max(r, 1e-3)
    v = v - np.clip(dc - 0.7, 0, 1) * 0.9
    rgb = ramp(v, mat["ramp"]) + C(mat["spec"]) * (spec * mat.get("sp", 0.7))[..., None]
    cv.put((rgb, cov(cv, sd)))
    # crisp specular dot
    hx, hy = cx - r * 0.38, cy - r * 0.42
    cv.over("#ffffff", cov(cv, sd_circle(cv, hx, hy, max(0.6, r * 0.17)), soft=0.4), 0.9)
    return sd


# ------------------------------------------------------------------------------------------ misc utils

def blur(cv, a, sigma):
    return ndimage.gaussian_filter(a.astype(F), sigma * cv.ss)


def dist_inside(cv, mask):
    """Euclidean distance (design px) to the outside of a coverage mask."""
    return (ndimage.distance_transform_edt(mask > 0.5) / cv.ss).astype(F)


def save_gray(arr, path):
    Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), "L").save(path, optimize=True)


def nine_slice(img: Image.Image, margins, size, scale=1.0):
    """Reference 9-slice renderer (stretch mode) used for evidence: margins in texture px, drawn at `scale`."""
    l, t, r, b = margins
    W, H = img.size
    tw, th = size
    ls, ts, rs, bs = (int(round(v * scale)) for v in (l, t, r, b))
    out = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    xs_src = [0, l, W - r, W]
    ys_src = [0, t, H - b, H]
    xs_dst = [0, ls, tw - rs, tw]
    ys_dst = [0, ts, th - bs, th]
    for i in range(3):
        for j in range(3):
            sx0, sx1, sy0, sy1 = xs_src[j], xs_src[j + 1], ys_src[i], ys_src[i + 1]
            dx0, dx1, dy0, dy1 = xs_dst[j], xs_dst[j + 1], ys_dst[i], ys_dst[i + 1]
            if sx1 <= sx0 or sy1 <= sy0 or dx1 <= dx0 or dy1 <= dy0:
                continue
            piece = img.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.LANCZOS)
            out.alpha_composite(piece, (dx0, dy0))
    return out


def vgrad(cv, y0, y1, stops):
    t = np.clip((cv.Y - y0) / max(y1 - y0, 1e-3), 0, 1)
    return ramp(t, stops)


def hgrad(cv, x0, x1, stops):
    t = np.clip((cv.X - x0) / max(x1 - x0, 1e-3), 0, 1)
    return ramp(t, stops)


def rgrad(cv, cx, cy, r, stops, sy=1.0):
    t = np.clip(np.hypot(cv.X - cx, (cv.Y - cy) / sy) / max(r, 1e-3), 0, 1)
    return ramp(t, stops)


def desaturate(cv, amt=1.0, dim=1.0):
    lum = (cv.rgb * np.array([0.3, 0.59, 0.11], F)).sum(-1, keepdims=True)
    cv.rgb = (cv.rgb * (1 - amt) + lum * amt) * dim
