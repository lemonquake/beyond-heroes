"""Tileable procedural texture helpers for Beyond Heroes (numpy / scipy / PIL).

Everything here is periodic on an N x N torus so every output tiles seamlessly:
- spectral noise is synthesised in the Fourier domain (periodic by construction),
- Voronoi uses a periodic cKDTree (boxsize=N),
- stamps / strokes are drawn with wrap-around copies.
All functions take explicit seeds so results are deterministic.
"""
import numpy as np
from scipy.spatial import cKDTree
from scipy import ndimage
from PIL import Image, ImageDraw

N = 1024

_fx = np.fft.fftfreq(N) * N
_FX, _FY = np.meshgrid(_fx, _fx)  # _FX varies along columns (x), _FY along rows (y)
YY, XX = np.mgrid[0:N, 0:N].astype(np.float32)


def rng(seed):
    return np.random.default_rng(seed)


def std(a):
    a = a - a.mean()
    s = a.std()
    return a / (s if s > 1e-9 else 1.0)


def noise(seed, beta=2.0, fmin=1.0, fmax=None, ax=1.0, ay=1.0):
    """Zero-mean, unit-std periodic noise with 1/f^beta power spectrum.
    ax>1 stretches features along x (frequencies along x are compressed), ay likewise along y."""
    w = rng(seed).standard_normal((N, N))
    f = np.sqrt((_FX * ax) ** 2 + (_FY * ay) ** 2)
    f[0, 0] = 1.0
    amp = f ** (-beta / 2.0)
    amp *= 1.0 / (1.0 + np.exp(np.clip(-(f - fmin) * 4.0, -60, 60)))  # soft low cut
    if fmax is not None:
        amp *= np.exp(-(f / fmax) ** 2)
    amp[0, 0] = 0.0
    out = np.real(np.fft.ifft2(np.fft.fft2(w) * amp))
    return std(out).astype(np.float32)


def remap(a, lo, hi):
    a = np.asarray(a, np.float32)
    mn, mx = float(a.min()), float(a.max())
    return lo + (a - mn) / max(mx - mn, 1e-9) * (hi - lo)


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def blur(a, s):
    return ndimage.gaussian_filter(a, s, mode="wrap")


def warp_coords(seed, amp, beta=2.5, fmin=2.0):
    wx = noise(seed, beta, fmin) * amp
    wy = noise(seed + 1, beta, fmin) * amp
    return (XX + wx) % N, (YY + wy) % N


def sample_wrap(img, x, y, order=1):
    """Sample a periodic image at float coords (x=col, y=row)."""
    if img.ndim == 2:
        return ndimage.map_coordinates(img, [y, x], order=order, mode="grid-wrap")
    return np.stack([ndimage.map_coordinates(img[..., c], [y, x], order=order, mode="grid-wrap")
                     for c in range(img.shape[2])], -1)


def jittered_points(nx, ny, seed, jitter=0.8):
    r = rng(seed)
    gx, gy = np.meshgrid(np.arange(nx), np.arange(ny))
    px = (gx + 0.5 + (r.random(gx.shape) - 0.5) * jitter) * (N / nx)
    py = (gy + 0.5 + (r.random(gy.shape) - 0.5) * jitter) * (N / ny)
    return np.stack([px.ravel() % N, py.ravel() % N], 1)


def voronoi(pts, x=None, y=None):
    """Periodic Voronoi. Returns (F1, edge_dist, id1, id2). edge_dist = true distance to the cell border."""
    if x is None:
        x, y = XX, YY
    tree = cKDTree(pts, boxsize=N)
    q = np.stack([x.ravel() % N, y.ravel() % N], 1)
    d, i = tree.query(q, k=2)
    f1 = d[:, 0].reshape(N, N)
    f2 = d[:, 1].reshape(N, N)
    i1 = i[:, 0].reshape(N, N)
    i2 = i[:, 1].reshape(N, N)
    dp = pts[i2] - pts[i1]
    dp = (dp + N / 2) % N - N / 2
    sep = np.sqrt((dp ** 2).sum(-1)).reshape(N, N)
    edge = (f2 ** 2 - f1 ** 2) / (2 * np.maximum(sep, 1e-6))
    return f1.astype(np.float32), edge.astype(np.float32), i1, i2


def normal_from_height(h, strength):
    """OpenGL (+Y up) tangent-space normal map from a periodic height field (rows grow downward)."""
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    drow = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    nx = -dx * strength
    ny = drow * strength  # image-up is -row, so d/dy_up = -d/drow, normal y = -d/dy_up
    nz = np.ones_like(h)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / l, ny / l, nz / l], -1)
    return n * 0.5 + 0.5


def lerp(a, b, t):
    t = np.asarray(t, np.float32)
    if np.ndim(a) and np.shape(a)[-1] == 3 and t.ndim == 2:
        t = t[..., None]
    elif np.ndim(b) and np.shape(b)[-1] == 3 and t.ndim == 2:
        t = t[..., None]
    return a + (b - a) * t


def col(rgb):
    return np.array(rgb, np.float32)


def fill(rgb):
    return np.broadcast_to(col(rgb), (N, N, 3)).astype(np.float32).copy()


def mul(img, m):
    return img * np.asarray(m, np.float32)[..., None]


def wrapped_offsets(x, y, r):
    offs = []
    for ox in (-N, 0, N):
        for oy in (-N, 0, N):
            if -r <= x + ox <= N + r and -r <= y + oy <= N + r:
                offs.append((ox, oy))
    return offs


class Canvas:
    """PIL canvas that draws with wrap-around so strokes tile."""

    def __init__(self, mode="L", fill=0, size=N):
        self.size = size
        self.img = Image.new(mode, (size, size), fill)
        self.d = ImageDraw.Draw(self.img)

    def _offs(self, pts, r):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        rr = max(max(xs) - min(xs), max(ys) - min(ys)) / 2 + r
        s = self.size
        out = []
        for ox in (-s, 0, s):
            for oy in (-s, 0, s):
                if -rr <= cx + ox <= s + rr and -rr <= cy + oy <= s + rr:
                    out.append((ox, oy))
        return out

    def line(self, pts, fill, width=1):
        for ox, oy in self._offs(pts, width):
            self.d.line([(x + ox, y + oy) for x, y in pts], fill=fill, width=width)

    def polygon(self, pts, fill):
        for ox, oy in self._offs(pts, 2):
            self.d.polygon([(x + ox, y + oy) for x, y in pts], fill=fill)

    def ellipse(self, cx, cy, rx, ry, fill):
        for ox, oy in self._offs([(cx - rx, cy - ry), (cx + rx, cy + ry)], 2):
            self.d.ellipse([cx - rx + ox, cy - ry + oy, cx + rx + ox, cy + ry + oy], fill=fill)

    def array(self):
        a = np.asarray(self.img, np.float32) / 255.0
        return a


def save_rgb(path, rgb):
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB").save(path, optimize=True)


def save_rgba(path, rgba):
    Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(path, optimize=True)


def save_gray(path, g):
    Image.fromarray((np.clip(g, 0, 1) * 255 + 0.5).astype(np.uint8), "L").save(path, optimize=True)


def seam_score(img):
    """Ratio of wrap-edge discontinuity to the mean interior neighbour difference (~1.0 means seamless)."""
    a = np.asarray(img, np.float32)
    inner_x = np.abs(np.diff(a, axis=1)).mean()
    inner_y = np.abs(np.diff(a, axis=0)).mean()
    edge_x = np.abs(a[:, 0] - a[:, -1]).mean()
    edge_y = np.abs(a[0, :] - a[-1, :]).mean()
    return float(edge_x / max(inner_x, 1e-6)), float(edge_y / max(inner_y, 1e-6))
