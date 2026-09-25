"""Core SVG authoring helpers for Beyond Heroes UI art.

Only emits the ThorVG-safe SVG subset used by Godot 4.4's SVG importer:
<svg>, <defs>, <linearGradient>, <radialGradient>, <stop>, <g>, <path>, <circle>, <ellipse>, <rect>.
No filters, masks, clip paths, CSS, text, images or external references.
"""
from __future__ import annotations

import math
import random
from contextlib import contextmanager

# --------------------------------------------------------------------------------------------
# colour helpers
# --------------------------------------------------------------------------------------------


def _rgb(c: str):
    c = c.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in rgb)


def mix(a: str, b: str, t: float) -> str:
    ra, rb = _rgb(a), _rgb(b)
    return _hex([ra[i] + (rb[i] - ra[i]) * t for i in range(3)])


def lt(c: str, t: float) -> str:
    """Lighten toward white."""
    return mix(c, "#ffffff", t)


def dk(c: str, t: float) -> str:
    """Darken toward black."""
    return mix(c, "#000000", t)


# --------------------------------------------------------------------------------------------
# palettes
# --------------------------------------------------------------------------------------------

EL = {
    # name: dark, base, light, glow
    "physical": dict(dark="#3c444e", base="#aab4be", light="#f2f6fa", glow="#dfe8f0"),
    "fire": dict(dark="#7a1206", base="#f2551a", light="#ffd34a", glow="#ff6a14"),
    "ice": dict(dark="#1f5a7a", base="#7fd6ec", light="#eafcff", glow="#9eeeff"),
    "lightning": dict(dark="#4a2a9a", base="#ffe23a", light="#fffbe0", glow="#b88aff"),
    "earth": dict(dark="#3e2610", base="#a8733a", light="#e6bf7c", glow="#d89a48"),
    "wind": dict(dark="#2c6a4c", base="#9ee0a6", light="#ecffec", glow="#b8ffc8"),
    "water": dict(dark="#062a44", base="#138a9c", light="#76e2ea", glow="#30c4d4"),
    "light": dict(dark="#9a6c20", base="#ffe08a", light="#fffff2", glow="#fff0b0"),
    "dark": dict(dark="#10041a", base="#5a2a7e", light="#b684ea", glow="#8a3ad0"),
}

STEEL = dict(dark="#2e343c", base="#8e98a4", light="#eef2f6", glow="#dfe8f0")
CRIMSON = dict(dark="#3a0610", base="#a0182a", light="#e8506a", glow="#ff3a4a")
GOLD = dict(dark="#5a3a0c", base="#c8962e", light="#ffe9a0", glow="#ffd070")
BRONZE = dict(dark="#4a2a10", base="#a0683a", light="#e8b884", glow="#e0a060")
INDIGO = dict(dark="#0e0c2e", base="#2c2a7a", light="#6a68c8", glow="#5a50d0")
ARCANE = dict(dark="#2a0e5a", base="#8a4ae0", light="#e0c4ff", glow="#a060ff")
LEATHER = dict(dark="#2a160c", base="#6a3e22", light="#b07c50", glow="#c08050")
WOOD = dict(dark="#2a1608", base="#6e4424", light="#b88452", glow="#c08a50")
BONE = dict(dark="#6a5a40", base="#d8ccae", light="#fbf6e6", glow="#fff4d8")
CLOTH_RED = dict(dark="#3a0a10", base="#8a1e2a", light="#d05060", glow="#ff4050")
LINEN = dict(dark="#4a3a24", base="#a8906a", light="#e8d8b4", glow="#f0e0c0")

OUTLINE = "#0a0610"

# --------------------------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------------------------


def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def poly(pts, closed=True) -> str:
    out = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts)
    return out + (" Z" if closed else "")


def smooth(pts, closed=True, tension=1.0) -> str:
    """Catmull-Rom spline through pts, emitted as cubic beziers."""
    n = len(pts)
    if n < 3:
        return poly(pts, closed)
    d = f"M{f(pts[0][0])},{f(pts[0][1])}"
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed else pts[max(i - 1, 0)]
        p1 = pts[i]
        p2 = pts[(i + 1) % n] if closed else pts[i + 1]
        p3 = pts[(i + 2) % n] if closed else pts[min(i + 2, n - 1)]
        k = tension / 6.0
        c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
        c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
        d += f" C{f(c1[0])},{f(c1[1])} {f(c2[0])},{f(c2[1])} {f(p2[0])},{f(p2[1])}"
    return d + (" Z" if closed else "")


def lerp(a, b, t):
    return a + (b - a) * t


def lerp2(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def rot(p, a, c=(0, 0)):
    ca, sa = math.cos(a), math.sin(a)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)


def polar(cx, cy, r, a):
    return (cx + r * math.cos(a), cy + r * math.sin(a))


def arc_pts(cx, cy, r, a0, a1, n=24, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(lerp(a0, a1, i / (n - 1))), cy + ry * math.sin(lerp(a0, a1, i / (n - 1)))) for i in range(n)]


def bez(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def qbez(p0, p1, p2, n=24):
    out = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        out.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return out


def star_pts(cx, cy, n, r1, r2, rot0=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = rot0 + i * math.pi / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def ngon(cx, cy, r, n, rot0=-math.pi / 2):
    return [(cx + r * math.cos(rot0 + i * 2 * math.pi / n), cy + r * math.sin(rot0 + i * 2 * math.pi / n)) for i in range(n)]


def taper(n, w, start=0.0, end=0.0, peak=0.5, power=1.0):
    """Width profile: from start*w to w (at peak) to end*w."""
    out = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0
        if t <= peak:
            u = t / peak if peak > 0 else 1
            s = start + (1 - start) * math.sin(u * math.pi / 2) ** power
        else:
            u = (t - peak) / (1 - peak) if peak < 1 else 1
            s = end + (1 - end) * math.cos(u * math.pi / 2) ** power
        out.append(w * s)
    return out


def ribbon_pts(pts, widths):
    n = len(pts)
    left, right = [], []
    for i in range(n):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L, tx / L
        w = widths[i] / 2.0
        left.append((pts[i][0] + nx * w, pts[i][1] + ny * w))
        right.append((pts[i][0] - nx * w, pts[i][1] - ny * w))
    return left + right[::-1]


def ribbon(pts, widths) -> str:
    return poly(ribbon_pts(pts, widths))


def jag_line(p0, p1, segs, amp, rng: random.Random, taper_ends=True):
    """Jagged polyline for lightning / cracks."""
    pts = [p0]
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    for i in range(1, segs):
        t = i / segs
        k = math.sin(t * math.pi) if taper_ends else 1
        o = rng.uniform(-amp, amp) * (0.4 + 0.6 * k)
        pts.append((p0[0] + dx * t + nx * o, p0[1] + dy * t + ny * o))
    pts.append(p1)
    return pts


def blob(cx, cy, r, n, jitter, rng: random.Random, rot0=0.0, sx=1.0, sy=1.0):
    pts = []
    for i in range(n):
        a = rot0 + i * 2 * math.pi / n + rng.uniform(-0.15, 0.15)
        rr = r * (1 + rng.uniform(-jitter, jitter))
        pts.append((cx + rr * math.cos(a) * sx, cy + rr * math.sin(a) * sy))
    return pts


def teardrop(cx, cy, r, h, lean=0.0, curl=0.0) -> str:
    """Flame tongue / droplet: round bottom centred (cx,cy), tip at (cx+lean, cy-h)."""
    tx, ty = cx + lean, cy - h
    return (f"M{f(tx)},{f(ty)} C{f(tx - r * 0.25 + curl)},{f(ty + h * 0.4)} {f(cx - r)},{f(cy - r * 1.2)} {f(cx - r)},{f(cy)}"
            f" C{f(cx - r)},{f(cy + r * 0.75)} {f(cx - r * 0.55)},{f(cy + r)} {f(cx)},{f(cy + r)}"
            f" C{f(cx + r * 0.55)},{f(cy + r)} {f(cx + r)},{f(cy + r * 0.75)} {f(cx + r)},{f(cy)}"
            f" C{f(cx + r)},{f(cy - r * 1.2)} {f(tx + r * 0.25 + curl)},{f(ty + h * 0.4)} {f(tx)},{f(ty)} Z")


def circle_path(cx, cy, r, ry=None, ccw=False) -> str:
    ry = r if ry is None else ry
    s = 0 if ccw else 1
    return (f"M{f(cx - r)},{f(cy)} A{f(r)},{f(ry)} 0 1 {s} {f(cx + r)},{f(cy)} A{f(r)},{f(ry)} 0 1 {s} {f(cx - r)},{f(cy)} Z")


def rrect_path(x, y, w, h, r) -> str:
    r = min(r, w / 2, h / 2)
    return (f"M{f(x + r)},{f(y)} L{f(x + w - r)},{f(y)} Q{f(x + w)},{f(y)} {f(x + w)},{f(y + r)} L{f(x + w)},{f(y + h - r)}"
            f" Q{f(x + w)},{f(y + h)} {f(x + w - r)},{f(y + h)} L{f(x + r)},{f(y + h)} Q{f(x)},{f(y + h)} {f(x)},{f(y + h - r)}"
            f" L{f(x)},{f(y + r)} Q{f(x)},{f(y)} {f(x + r)},{f(y)} Z")


# --------------------------------------------------------------------------------------------
# document
# --------------------------------------------------------------------------------------------

_ATTR_MAP = {
    "fill_opacity": "fill-opacity", "stroke_opacity": "stroke-opacity", "stroke_width": "stroke-width",
    "stroke_linejoin": "stroke-linejoin", "stroke_linecap": "stroke-linecap", "fill_rule": "fill-rule",
    "stop_color": "stop-color", "stop_opacity": "stop-opacity", "stroke_miterlimit": "stroke-miterlimit",
}


def _attrs(kw) -> str:
    out = []
    for k, v in kw.items():
        if v is None:
            continue
        k = _ATTR_MAP.get(k, k.replace("_", "-"))
        if isinstance(v, float):
            v = f(v)
        out.append(f'{k}="{v}"')
    return " ".join(out)


class Doc:
    def __init__(self, w=128, h=128, name="icon"):
        self.w, self.h = w, h
        self.name = name
        self.defs: list[str] = []
        self.root: list = []
        self.stack = [self.root]
        self.n = 0
        self.rng = random.Random(sum(ord(c) * (i + 7) for i, c in enumerate(name)))

    # ---- ids / gradients
    def uid(self, p="g"):
        self.n += 1
        return f"{p}{self.n}"

    def _stops(self, stops):
        s = []
        for st in stops:
            o, c = st[0], st[1]
            op = st[2] if len(st) > 2 else 1.0
            if op >= 0.999:
                s.append(f'<stop offset="{f(o)}" stop-color="{c}"/>')
            else:
                s.append(f'<stop offset="{f(o)}" stop-color="{c}" stop-opacity="{f(op)}"/>')
        return "".join(s)

    def lin(self, stops, x1, y1, x2, y2) -> str:
        i = self.uid("l")
        self.defs.append(f'<linearGradient id="{i}" gradientUnits="userSpaceOnUse" x1="{f(x1)}" y1="{f(y1)}" '
                         f'x2="{f(x2)}" y2="{f(y2)}">{self._stops(stops)}</linearGradient>')
        return f"url(#{i})"

    def rad(self, stops, cx, cy, r, fx=None, fy=None) -> str:
        i = self.uid("r")
        extra = ""
        if fx is not None:
            extra = f' fx="{f(fx)}" fy="{f(fy)}"'
        self.defs.append(f'<radialGradient id="{i}" gradientUnits="userSpaceOnUse" cx="{f(cx)}" cy="{f(cy)}" '
                         f'r="{f(r)}"{extra}>{self._stops(stops)}</radialGradient>')
        return f"url(#{i})"

    # ---- elements
    def raw(self, s):
        self.stack[-1].append(s)

    def el(self, tag, **kw):
        self.stack[-1].append(f"<{tag} {_attrs(kw)}/>")

    def path(self, d, fill="none", stroke=None, sw=None, op=None, lj="round", lc="round", **kw):
        if "stroke_width" in kw:
            sw = kw.pop("stroke_width")
        if "opacity" in kw:
            op = kw.pop("opacity")
        if stroke is None:
            lj = lc = None
        self.el("path", d=d, fill=fill, stroke=stroke, stroke_width=sw, opacity=op, stroke_linejoin=lj,
                stroke_linecap=lc, **kw)

    def shape(self, d, fill, ow=2.5, oc=OUTLINE, op=None, **kw):
        """Filled path with an external dark outline (outline drawn first, fill on top)."""
        if ow and ow > 0:
            self.path(d, fill="none", stroke=oc, sw=ow * 2, op=op)
        self.path(d, fill=fill, op=op, **kw)

    def circle(self, cx, cy, r, fill="none", **kw):
        self.el("circle", cx=float(cx), cy=float(cy), r=float(r), fill=fill, **kw)

    def ellipse(self, cx, cy, rx, ry, fill="none", **kw):
        self.el("ellipse", cx=float(cx), cy=float(cy), rx=float(rx), ry=float(ry), fill=fill, **kw)

    def rect(self, x, y, w, h, fill="none", rx=None, **kw):
        self.el("rect", x=float(x), y=float(y), width=float(w), height=float(h), rx=None if rx is None else float(rx),
                fill=fill, **kw)

    @contextmanager
    def g(self, transform=None, op=None):
        items: list = []
        self.stack.append(items)
        try:
            yield
        finally:
            self.stack.pop()
            a = _attrs(dict(transform=transform, opacity=op))
            self.stack[-1].append(f"<g {a}>" if a else "<g>")
            self.stack[-1].extend(items)
            self.stack[-1].append("</g>")

    # ---- effects
    def glow(self, cx, cy, r, color, op=0.8, core=None):
        stops = [(0, core or color, op), (0.35, color, op * 0.55), (0.7, color, op * 0.16), (1, color, 0)]
        self.circle(cx, cy, r, fill=self.rad(stops, cx, cy, r))

    def glow_ellipse(self, cx, cy, rx, ry, color, op=0.8):
        # radial gradient on an ellipse via scaled group
        with self.g(f"translate({f(cx)} {f(cy)}) scale(1 {f(ry / rx)})"):
            self.glow(0, 0, rx, color, op)

    def glow_stroke(self, d, color, width, op=0.5, layers=((3.2, 0.10), (2.2, 0.16), (1.5, 0.28))):
        for mult, a in layers:
            self.path(d, stroke=color, sw=width * mult, op=a * op / 0.5)

    def sparkle(self, cx, cy, r, color="#ffffff", op=1.0, glow_color=None, thin=0.18):
        if glow_color:
            self.glow(cx, cy, r * 1.4, glow_color, 0.6 * op)
        pts = [(cx, cy - r), (cx + r * thin, cy - r * thin), (cx + r, cy), (cx + r * thin, cy + r * thin),
               (cx, cy + r), (cx - r * thin, cy + r * thin), (cx - r, cy), (cx - r * thin, cy - r * thin)]
        self.path(poly(pts), fill=color, op=op)

    # ---- output
    def svg(self) -> str:
        body = "\n".join(self.root)
        defs = "<defs>" + "".join(self.defs) + "</defs>\n" if self.defs else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}">\n{defs}{body}\n</svg>\n')


def faceted(doc: Doc, pts, center, dark, light, ow=2.5, light_dir=(-0.6, -0.8), outline=True, gamma=1.0, op=None):
    """Low-poly faceted solid: triangles (center, v_i, v_i+1) shaded by edge normal vs light direction."""
    n = len(pts)
    if outline and ow:
        doc.path(poly(pts), stroke=OUTLINE, sw=ow * 2, op=op)
    lx, ly = light_dir
    Ll = math.hypot(lx, ly)
    lx, ly = lx / Ll, ly / Ll
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        mx, my = (a[0] + b[0]) / 2 - center[0], (a[1] + b[1]) / 2 - center[1]
        m = math.hypot(mx, my) or 1
        dot = (mx * lx + my * ly) / m
        t = ((dot + 1) / 2) ** gamma
        doc.path(poly([center, a, b]), fill=mix(dark, light, t), stroke=mix(dark, light, t), sw=0.4, op=op)
