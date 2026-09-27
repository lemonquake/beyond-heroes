"""bh-010 new painted motifs (ranger / shadowblade / aura / passive vocabulary). Same conventions as bh_shapes: every
function draws in local coordinates around the origin unless it takes (cx, cy); callers place it with d.g(T(...))."""
from __future__ import annotations

import math
import random

from bh_svg import (Doc, EL, STEEL, CRIMSON, GOLD, BRONZE, ARCANE, LEATHER, WOOD, BONE, OUTLINE, f, poly, smooth, mix, lt,
                    dk, ribbon, taper, arc_pts, bez, qbez, star_pts, ngon, jag_line, blob, teardrop, polar, faceted,
                    rrect_path, circle_path, lerp)
from bh_shapes import T, grip, guard, haft, smooth_pts

BRIGHT_STEEL = dict(dark="#3a4250", base="#b4bfcc", light="#ffffff", glow="#e8f0ff")
DARK_STEEL = dict(dark="#14121c", base="#5a5668", light="#d8d2ec", glow="#b890ff")
HOLY = dict(dark="#8a5a14", base="#ffd870", light="#fffbe6", glow="#ffe8a0")
VENOM = dict(dark="#0e4a0a", base="#5ad02a", light="#e0ffb0", glow="#7aff3a")
VIOLET = dict(dark="#2a0a4a", base="#8a3ae0", light="#e2c4ff", glow="#b060ff")
BLOOD = dict(dark="#3a0408", base="#b0141e", light="#ff6a6a", glow="#ff3040")
FOREST = dict(dark="#12301a", base="#3f7a3c", light="#a8d88a", glow="#9aff9a")
MANA = dict(dark="#0a1a6a", base="#2a6ae8", light="#a8d8ff", glow="#5aa0ff")
HEAL = dict(dark="#0e4a2c", base="#46c888", light="#d8ffe8", glow="#9affc8")
FLETCH_GREEN = dict(dark="#1a3a1a", base="#4a8a3a", light="#a8d88a")
FLETCH_WHITE = dict(dark="#6a6a70", base="#d8d8dc", light="#ffffff")


# ------------------------------------------------------------------------------------------ weapons

def arrow2(d: Doc, L=70, head=STEEL, fletch=FLETCH_GREEN, shaft=WOOD, head_scale=1.0, glow=None, ow=1.8, shaft_w=2.0):
    """Arrow pointing -y, nock at origin. Bigger, broadhead-style head than bh_shapes.arrow."""
    if glow:
        d.glow_stroke(f"M0,-4 L0,{f(-L)}", glow, 6, op=0.5)
    d.path(f"M0,0 L0,{f(-L + 8)}", stroke=OUTLINE, sw=shaft_w + 2.4)
    d.path(f"M0,0 L0,{f(-L + 8)}", stroke=d.lin([(0, shaft["light"]), (1, shaft["base"])], -1, 0, 1, 0), sw=shaft_w)
    hs = head_scale
    hd = [(0, -L - 4 * hs), (5.5 * hs, -L + 9 * hs), (1.4, -L + 6.5 * hs), (1.4, -L + 10), (-1.4, -L + 10), (-1.4, -L + 6.5 * hs), (-5.5 * hs, -L + 9 * hs)]
    d.shape(poly(hd), fill=d.lin([(0, head["light"]), (0.5, head["base"]), (1, head["dark"])], -5 * hs, 0, 5 * hs, 0), ow=ow)
    d.path(f"M0,{f(-L - 2 * hs)} L0,{f(-L + 7 * hs)}", stroke="#ffffff", sw=0.7, op=0.6)
    for s in (-1, 1):
        fl = [(0, -1), (s * 5.5, 2), (s * 5.5, -9), (0, -15)]
        d.shape(poly(fl), fill=fletch["base"] if s < 0 else fletch["light"], ow=1.3)
    d.path("M-2.4,1 L2.4,1", stroke=OUTLINE, sw=2)


def javelin(d: Doc, L=100, head=BRIGHT_STEEL, shaft=WOOD, wrap=LEATHER):
    """Throwing javelin pointing -y, butt at origin."""
    d.path(f"M0,0 L0,{f(-L + 20)}", stroke=OUTLINE, sw=5.4)
    d.path(f"M0,0 L0,{f(-L + 20)}", stroke=d.lin([(0, shaft["light"]), (1, shaft["dark"])], -2, 0, 2, 0), sw=3.0)
    for y in (-L * 0.42, -L * 0.36, -L * 0.30):
        d.path(f"M-2.4,{f(y)} L2.4,{f(y + 3)}", stroke=OUTLINE, sw=3)
        d.path(f"M-2.2,{f(y)} L2.2,{f(y + 3)}", stroke=wrap["light"], sw=1.6)
    hd = [(0, -L), (5, -L + 14), (2, -L + 22), (-2, -L + 22), (-5, -L + 14)]
    d.shape(poly(hd), fill=d.lin([(0, head["light"]), (0.5, head["base"]), (1, head["dark"])], -5, 0, 5, 0), ow=1.8)
    d.path(f"M0,{f(-L + 1)} L0,{f(-L + 20)}", stroke=head["dark"], sw=0.8, op=0.8)


def knife(d: Doc, L=30, W=7, pal=BRIGHT_STEEL, hilt=DARK_STEEL, ow=1.8):
    """Slim throwing knife pointing -y, blade base at origin (short ring-pommel grip below)."""
    bl = [(-W / 2, 0), (-W / 2, -L * 0.6), (0, -L), (W / 2, -L * 0.55), (W / 2, 0)]
    d.shape(poly(bl), fill=d.lin([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], -W / 2, 0, W / 2, 0), ow=ow)
    d.path(f"M{f(-W * 0.15)},-2 L{f(-W * 0.15)},{f(-L * 0.7)}", stroke="#ffffff", sw=0.8, op=0.7)
    gr = rrect_path(-W * 0.3, 0, W * 0.6, L * 0.34, 1)
    d.shape(gr, fill=d.lin([(0, hilt["light"]), (1, hilt["dark"])], -W / 2, 0, W / 2, 0), ow=ow * 0.8)
    d.circle(0, L * 0.34 + 3, 2.8, stroke=OUTLINE, stroke_width=3)
    d.circle(0, L * 0.34 + 3, 2.8, stroke=hilt["base"], stroke_width=1.4)


def dagger2(d: Doc, L=46, W=10, pal=BRIGHT_STEEL, hilt=DARK_STEEL, gem=VIOLET, glow=None):
    """Assassin's dagger: straight double-edged blade, swept guard, wrapped grip, gem pommel. Blade -y from origin."""
    if glow:
        d.glow_stroke(f"M0,-2 L0,{f(-L)}", glow, W, op=0.45)
    gp = rrect_path(-W * 0.24, 0, W * 0.48, W * 1.5, 1.2)
    d.shape(gp, fill=d.lin([(0, "#4a3a5a"), (1, "#140c1c")], -W * 0.24, 0, W * 0.24, 0), ow=1.8)
    for i in range(4):
        y = 2 + i * W * 0.34
        d.path(f"M{f(-W * 0.24)},{f(y)} L{f(W * 0.24)},{f(y + 1.6)}", stroke="#0a0610", sw=0.8)
    d.circle(0, W * 1.5 + W * 0.3, W * 0.32, fill=d.rad([(0, gem["light"]), (0.6, gem["base"]), (1, gem["dark"])], -1, W * 1.6, W * 0.4), stroke=OUTLINE, stroke_width=1.4)
    bl = [(-W / 2, 0), (-W * 0.42, -L * 0.7), (0, -L), (W * 0.42, -L * 0.7), (W / 2, 0)]
    dd = smooth(bl, tension=0.25)
    d.path(dd, stroke=OUTLINE, sw=4)
    d.path(dd, fill=d.lin([(0, pal["light"]), (0.48, lt(pal["base"], 0.3)), (0.52, pal["base"]), (1, pal["dark"])], -W / 2, 0, W / 2, 0))
    d.path(f"M0,-2 L0,{f(-L * 0.86)}", stroke=dk(pal["base"], 0.4), sw=1.0, op=0.8)
    d.path(f"M{f(-W * 0.32)},-3 L{f(-W * 0.2)},{f(-L * 0.72)}", stroke="#ffffff", sw=0.8, op=0.75)
    gd = [(-W * 1.1, 1), (-W * 1.25, -3.5), (-W * 0.4, -2.2), (0, -3.2), (W * 0.4, -2.2), (W * 1.25, -3.5), (W * 1.1, 1), (W * 0.4, 2.4), (-W * 0.4, 2.4)]
    d.shape(smooth(gd, tension=0.4), fill=d.lin([(0, hilt["light"]), (0.5, hilt["base"]), (1, hilt["dark"])], 0, -4, 0, 3), ow=1.6)
    d.circle(0, -0.4, 1.6, fill=gem["base"], stroke=OUTLINE, stroke_width=0.8)


def claw(d: Doc, pal=BRIGHT_STEEL, hilt=DARK_STEEL, L=44):
    """Katar-style claw: three curved blades rising from a crossbar grip. Origin at the crossbar centre."""
    for i, (x, bend) in enumerate(((-9, -6), (0, 0), (9, 6))):
        pts = qbez((x, 0), (x + bend * 0.2, -L * 0.5), (x + bend, -L + abs(x) * 0.4), n=14)
        dd = ribbon(pts, taper(14, 6.4, 1.0, 0.0, peak=0.0))
        d.path(dd, stroke=OUTLINE, sw=3.6)
        d.path(dd, fill=d.lin([(0, pal["light"]), (1, pal["dark"])], x - 3, 0, x + 3, 0))
        d.path(poly([(p[0] - 1.2, p[1]) for p in pts[1:-2]], closed=False), stroke="#ffffff", sw=0.7, op=0.7)
    d.shape(rrect_path(-16, -1, 32, 7, 2), fill=d.lin([(0, hilt["light"]), (1, hilt["dark"])], 0, -1, 0, 6), ow=1.8)
    for sx in (-1, 1):
        d.shape(rrect_path(sx * 12 - 2.5, 5, 5, 16, 1.5), fill=d.lin([(0, hilt["light"]), (1, hilt["dark"])], -3, 0, 3, 0), ow=1.6)
    d.shape(rrect_path(-12, 14, 24, 5, 2), fill=d.lin([(0, "#4a3a5a"), (1, "#140c1c")], 0, 14, 0, 19), ow=1.6)


def warhammer(d: Doc, H=70, head=HOLY, shaft=WOOD, glow=None):
    """Two-faced warhammer, head centred at origin, haft running down to +H."""
    haft(d, 4, H, W=6, pal=shaft, bands=((H * 0.55, 4, head), (H - 8, 5, LEATHER)))
    if glow:
        d.glow(0, 0, 34, glow, 0.75)
    blk = [(-22, -11), (22, -11), (26, -14), (26, 14), (22, 11), (-22, 11), (-26, 14), (-26, -14)]
    d.shape(poly(blk), fill=d.lin([(0, head["light"]), (0.45, head["base"]), (1, head["dark"])], 0, -14, 0, 14), ow=2.4)
    d.path("M-22,-4 L22,-4", stroke=head["light"], sw=1.2, op=0.8)
    d.path("M-22,6 L22,6", stroke=head["dark"], sw=1.2, op=0.8)
    for sx in (-1, 1):
        d.path(f"M{sx * 26},-14 L{sx * 26},14", stroke="#ffffff", sw=1.0, op=0.6)
    d.shape(poly(ngon(0, 0, 8, 4, rot0=0)), fill=d.lin([(0, "#ffffff"), (1, head["base"])], -6, -6, 6, 6), ow=1.4)
    d.shape(poly([(-5, -11), (0, -22), (5, -11)]), fill=d.lin([(0, head["light"]), (1, head["dark"])], -5, 0, 5, 0), ow=1.6)


def shuriken(d: Doc, cx, cy, r, pal=BRIGHT_STEEL, n=4, rot0=0.0):
    pts = []
    for i in range(n):
        a = rot0 + i * 2 * math.pi / n
        pts.append(polar(cx, cy, r * 0.28, a - math.pi / n))
        pts.append(polar(cx, cy, r * 0.42, a - 0.3))
        pts.append(polar(cx, cy, r, a))
        pts.append(polar(cx, cy, r * 0.32, a + 0.55))
    d.path(poly(pts), stroke=OUTLINE, sw=4)
    d.path(poly(pts), fill=d.lin([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], cx - r, cy - r, cx + r, cy + r))
    for i in range(n):
        a = rot0 + i * 2 * math.pi / n
        p0, p1 = polar(cx, cy, r * 0.3, a), polar(cx, cy, r * 0.9, a)
        d.path(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}", stroke="#ffffff", sw=1.0, op=0.6)
    d.circle(cx, cy, r * 0.14, fill="#0a0610", stroke=pal["light"], stroke_width=1.2)


def saw_blade(d: Doc, cx, cy, r, pal=BRIGHT_STEEL, teeth=10, rot0=0.0):
    pts = []
    for i in range(teeth):
        a = rot0 + i * 2 * math.pi / teeth
        pts.append(polar(cx, cy, r * 0.74, a))
        pts.append(polar(cx, cy, r, a + 0.12))
        pts.append(polar(cx, cy, r * 0.8, a + 2 * math.pi / teeth * 0.8))
    d.path(poly(pts), stroke=OUTLINE, sw=4)
    d.path(poly(pts), fill=d.rad([(0, pal["light"]), (0.6, pal["base"]), (1, pal["dark"])], cx - r * 0.3, cy - r * 0.3, r * 1.2))
    d.circle(cx, cy, r * 0.44, stroke=pal["dark"], stroke_width=1.2, opacity=0.8)
    for i in range(3):
        a = rot0 + i * 2 * math.pi / 3
        x, y = polar(cx, cy, r * 0.26, a)
        d.circle(x, y, r * 0.09, fill="#0a0610")
    d.circle(cx, cy, r * 0.12, fill=GOLD["base"], stroke=OUTLINE, stroke_width=1.2)


# ------------------------------------------------------------------------------------------ hunter gear

def quiver(d: Doc, H=60, pal=LEATHER, trim=BRONZE, fletch=FLETCH_GREEN):
    """Quiver, mouth at origin, body down to +H, three arrow fletchings poking out."""
    for i, x in enumerate((-6, 0, 6)):
        y = -12 - (4 if i == 1 else 0)
        d.path(f"M{x},0 L{x},{y}", stroke=OUTLINE, sw=3.4)
        d.path(f"M{x},0 L{x},{y}", stroke=WOOD["light"], sw=1.4)
        for s in (-1, 1):
            fl = [(x, y + 2), (x + s * 4, y + 4), (x + s * 4, y - 6), (x, y - 10)]
            d.shape(poly(fl), fill=fletch["light"] if s > 0 else fletch["base"], ow=1.1)
    body = [(-11, 0), (11, 0), (9, H), (-9, H)]
    d.shape(smooth(body, tension=0.15), fill=d.lin([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], -11, 0, 11, 0), ow=2.2)
    for y in (4, H - 6):
        d.shape(rrect_path(-11.5, y - 2.5, 23, 5, 1.5), fill=d.lin([(0, trim["light"]), (1, trim["dark"])], 0, y - 2, 0, y + 2), ow=1.4)
    d.path(f"M-6,10 L-5,{H - 10}", stroke=pal["dark"], sw=1.0, op=0.7)


def trap_jaws(d: Doc, w=70, pal=STEEL, open_=0.75, teeth=7):
    """Front view of a steel-jaw trap: two toothed half-rings hinged at the sides over a base plate. Local ~ x[-w/2,w/2]."""
    r = w / 2
    # base plate + spring
    d.shape(rrect_path(-r * 0.55, 8, r * 1.1, 8, 3), fill=d.lin([(0, "#6a6e76"), (1, "#23262c")], 0, 8, 0, 16), ow=2)
    d.shape(poly(ngon(0, 12, 6, 4, rot0=0)), fill=GOLD["base"], ow=1.2)
    top = arc_pts(0, 8, r, math.pi, 2 * math.pi, 24, ry=r * (0.25 + 0.55 * open_))
    bot = arc_pts(0, 12, r, 0, math.pi, 24, ry=r * 0.28)
    for jaw, sgn in ((top, -1), (bot, 1)):
        dd = ribbon(jaw, [6.5] * len(jaw))
        d.path(dd, stroke=OUTLINE, sw=4)
        d.path(dd, fill=d.lin([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], -r, -r, r, r))
        # teeth on the inner edge
        for k in range(1, teeth + 1):
            t = k / (teeth + 1)
            i = int(t * (len(jaw) - 1))
            x, y = jaw[i]
            nx, ny = (0 - x), (10 - y)
            L = math.hypot(nx, ny) or 1
            nx, ny = nx / L, ny / L
            tx, ty = -ny, nx
            tip = (x + nx * 9, y + ny * 9)
            tooth = [(x + tx * 3.4 + nx * 2, y + ty * 3.4 + ny * 2), tip, (x - tx * 3.4 + nx * 2, y - ty * 3.4 + ny * 2)]
            d.shape(poly(tooth), fill=d.lin([(0, "#ffffff"), (1, pal["base"])], *tooth[0], *tip), ow=1.1)
    for sx in (-1, 1):
        d.circle(sx * r, 10, 5, fill=d.rad([(0, pal["light"]), (1, pal["dark"])], sx * r - 1, 8, 6), stroke=OUTLINE, stroke_width=1.8)
        d.circle(sx * r, 10, 1.6, fill="#0a0610")


def mine(d: Doc, cx, cy, r, pal=None, spark=True):
    pal = pal or dict(dark="#14161c", base="#4a4e5a", light="#a8b0c0")
    for i in range(8):
        a = -math.pi / 2 + i * math.pi / 4 + math.pi / 8
        p0, p1 = polar(cx, cy, r * 0.8, a), polar(cx, cy, r * 1.32, a)
        d.path(ribbon([p0, p1], [r * 0.34, 0.8]), stroke=OUTLINE, stroke_width=1.6)
        d.path(ribbon([p0, p1], [r * 0.34, 0.8]), fill=d.lin([(0, pal["light"]), (1, pal["dark"])], *p0, *p1))
    d.circle(cx, cy, r + 2.4, fill=OUTLINE)
    d.circle(cx, cy, r, fill=d.rad([(0, pal["light"]), (0.45, pal["base"]), (1, pal["dark"])], cx - r * 0.35, cy - r * 0.4, r * 1.3))
    d.path(f"M{f(cx - r)},{f(cy + 2)} Q{f(cx)},{f(cy + r * 0.5)} {f(cx + r)},{f(cy + 2)}", stroke=CRIMSON["base"], sw=2.6)
    for x in (-0.5, 0, 0.5):
        d.circle(cx + r * x, cy + r * 0.2 + abs(x) * -2, 1.4, fill=GOLD["light"])
    d.path(smooth([(cx - r * 0.5, cy - r * 0.55), (cx - r * 0.2, cy - r * 0.75)], closed=False), stroke="#ffffff", sw=2.2, op=0.6)
    if spark:
        fz = qbez((cx + r * 0.1, cy - r), (cx + r * 0.3, cy - r * 1.6), (cx + r * 0.9, cy - r * 1.5), n=10)
        d.path(poly(fz, closed=False), stroke=OUTLINE, sw=3.6)
        d.path(poly(fz, closed=False), stroke="#c8a870", sw=1.6)
        sx, sy = fz[-1]
        d.glow(sx, sy, 14, "#ffb040", 0.9)
        d.path(poly(star_pts(sx, sy, 6, 8, 2.2)), fill="#ffe080")
        d.path(poly(star_pts(sx, sy, 6, 4.5, 1.4, rot0=0.3)), fill="#ffffff")


def web(d: Doc, cx, cy, r, color="#e8e8f0", spokes=8, rings=4, op=0.9, sw=1.4):
    ends = [polar(cx, cy, r * (0.92 + 0.08 * ((i * 7) % 3) / 2), -math.pi / 2 + i * 2 * math.pi / spokes) for i in range(spokes)]
    sp = " ".join(f"M{f(cx)},{f(cy)} L{f(x)},{f(y)}" for x, y in ends)
    d.path(sp, stroke=OUTLINE, sw=sw + 1.6, op=op * 0.6)
    d.path(sp, stroke=color, sw=sw, op=op)
    for k in range(1, rings + 1):
        t = k / (rings + 0.3)
        pts = []
        for i in range(spokes):
            a = ends[i]
            b = ends[(i + 1) % spokes]
            pa = (cx + (a[0] - cx) * t, cy + (a[1] - cy) * t)
            pb = (cx + (b[0] - cx) * t, cy + (b[1] - cy) * t)
            mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            sag = (cx + (mid[0] - cx) * 0.9, cy + (mid[1] - cy) * 0.9)
            pts.append(f"M{f(pa[0])},{f(pa[1])} Q{f(sag[0])},{f(sag[1])} {f(pb[0])},{f(pb[1])}")
        d.path(" ".join(pts), stroke=OUTLINE, sw=sw + 1.2, op=op * 0.5)
        d.path(" ".join(pts), stroke=color, sw=sw * 0.8, op=op)


def bullseye(d: Doc, cx, cy, r, a=CRIMSON, b=None, rings=4):
    b = b or dict(dark="#8a7a5a", base="#e8dcc0", light="#fffaf0")
    d.circle(cx, cy, r + 2.6, fill=OUTLINE)
    for i in range(rings):
        rr = r * (1 - i / rings)
        col = a if i % 2 == 0 else b
        d.circle(cx, cy, rr, fill=d.rad([(0, col["light"]), (0.55, col["base"]), (1, col["dark"])], cx - rr * 0.35, cy - rr * 0.35, rr * 1.4))
        d.circle(cx, cy, rr, stroke=OUTLINE, stroke_width=1.2, opacity=0.8)
    d.circle(cx, cy, r * 0.12, fill=GOLD["light"], stroke=OUTLINE, stroke_width=1)


def crosshair(d: Doc, cx, cy, r, color="#ff5a4a", sw=2.4, gap=0.35, ticks=True):
    d.circle(cx, cy, r, stroke=OUTLINE, stroke_width=sw + 2.4)
    d.circle(cx, cy, r, stroke=color, stroke_width=sw)
    arms = []
    for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
        p0, p1 = polar(cx, cy, r * gap, a), polar(cx, cy, r * 1.25, a)
        arms.append(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}")
    d.path(" ".join(arms), stroke=OUTLINE, sw=sw + 2.4)
    d.path(" ".join(arms), stroke=color, sw=sw)
    if ticks:
        tk = []
        for i in range(4):
            a = math.pi / 4 + i * math.pi / 2
            p0, p1 = polar(cx, cy, r * 0.84, a), polar(cx, cy, r * 1.0, a)
            tk.append(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}")
        d.path(" ".join(tk), stroke=color, sw=sw * 0.6)


def leaf(d: Doc, L=22, W=9, pal=FOREST, ow=1.4):
    """Leaf pointing -y from its stem at the origin."""
    lf = smooth([(0, 0), (W / 2, -L * 0.45), (0, -L), (-W / 2, -L * 0.45)], tension=0.9)
    d.path(lf, stroke=OUTLINE, sw=ow * 2)
    d.path(lf, fill=d.lin([(0, pal["light"]), (1, pal["dark"])], -W / 2, -L, W / 2, 0))
    d.path(f"M0,2 L0,{f(-L * 0.9)}", stroke=pal["dark"], sw=0.8)
    for t in (0.3, 0.5, 0.7):
        d.path(f"M0,{f(-L * t)} L{f(W * 0.3)},{f(-L * (t + 0.12))} M0,{f(-L * t)} L{f(-W * 0.3)},{f(-L * (t + 0.12))}", stroke=pal["dark"], sw=0.6, op=0.7)


def boot(d: Doc, pal=LEATHER, trim=BRONZE, cuff=None):
    """Side view of a soft hunting boot, toe to +x, sole at y=0; ~ x[-18,24] y[-44,0]."""
    body = [(-14, -44), (6, -44), (6, -20), (14, -14), (24, -8), (26, 0), (-16, 0), (-16, -20)]
    d.shape(smooth(body, tension=0.25), fill=d.lin([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], -16, -44, 26, 0), ow=2.4)
    d.shape(rrect_path(-17, -3, 44, 5, 2), fill=d.lin([(0, "#3a2a1a"), (1, "#140a04")], 0, -3, 0, 2), ow=1.4)
    cuff = cuff or trim
    d.shape(rrect_path(-16, -48, 24, 8, 2.5), fill=d.lin([(0, cuff["light"]), (1, cuff["dark"])], 0, -48, 0, -40), ow=1.6)
    for y in (-34, -26):
        d.path(f"M-6,{y} L6,{y - 2}", stroke=OUTLINE, sw=2.6)
        d.path(f"M-6,{y} L6,{y - 2}", stroke=trim["light"], sw=1.0)
    d.path(smooth([(-12, -40), (-12, -10)], closed=False), stroke="#ffffff", sw=1.4, op=0.3)


def footprint(d: Doc, cx, cy, s=1.0, a=0.0, fill="#1a1024", op=1.0, rim=None):
    """Boot print (sole + heel) centred at (cx,cy) pointing -y, rotated a degrees."""
    with d.g(T(cx, cy, a, s)):
        sole = smooth([(0, -16), (6, -12), (6.5, -2), (4, 2), (-4, 2), (-6.5, -2), (-6, -12)], tension=0.6)
        heel = smooth([(0, 6), (4.6, 8), (4.2, 15), (0, 16), (-4.2, 15), (-4.6, 8)], tension=0.6)
        if rim:
            d.path(sole + " " + heel, stroke=rim, sw=2.4, op=op)
        d.path(sole + " " + heel, fill=fill, op=op)


def chalice(d: Doc, pal=GOLD, wine=None):
    """Chalice, cup rim at y=-30, foot at y=+34."""
    wine = wine or HEAL
    cup = [(-22, -30), (22, -30), (18, -10), (8, 0), (-8, 0), (-18, -10)]
    d.shape(smooth(cup, tension=0.35), fill=d.lin([(0, pal["light"]), (0.45, pal["base"]), (1, pal["dark"])], -22, 0, 22, 0), ow=2.4)
    d.ellipse(0, -30, 22, 5, fill=d.rad([(0, wine["light"]), (1, wine["base"])], -4, -31, 20), stroke=OUTLINE, stroke_width=2)
    d.shape(rrect_path(-3.5, 0, 7, 22, 2), fill=d.lin([(0, pal["light"]), (1, pal["dark"])], -3, 0, 3, 0), ow=2)
    d.shape(poly(ngon(0, 10, 5, 6)), fill=d.lin([(0, pal["light"]), (1, pal["dark"])], -5, 5, 5, 15), ow=1.6)
    d.shape(smooth([(-18, 34), (-8, 24), (8, 24), (18, 34)], tension=0.4) + " Z", fill=d.lin([(0, pal["light"]), (1, pal["dark"])], 0, 24, 0, 34), ow=2)
    d.circle(0, -18, 3.4, fill=CRIMSON["base"], stroke=OUTLINE, stroke_width=1.2)
    d.path(smooth([(-16, -24), (-12, -12), (-6, -4)], closed=False), stroke="#ffffff", sw=1.8, op=0.5)


def vial(d: Doc, liquid=VENOM, glass="#cfe8f0"):
    """Round-bottomed potion vial; neck top at y=-34, bottom at y=+26."""
    body = circle_path(0, 8, 18)
    neck = rrect_path(-6, -30, 12, 22, 2)
    d.path(neck, stroke=OUTLINE, sw=4.4)
    d.path(body, stroke=OUTLINE, sw=4.4)
    d.path(neck, fill=glass, op=0.35)
    d.path(body, fill=glass, op=0.25)
    d.path(f"M-17,10 A18,18 0 0 0 17,10 Z", fill=d.lin([(0, liquid["light"]), (1, liquid["dark"])], 0, 4, 0, 26))
    d.ellipse(0, 10, 17, 3.4, fill=liquid["light"], opacity=0.8)
    d.shape(rrect_path(-8, -38, 16, 8, 2), fill=d.lin([(0, WOOD["light"]), (1, WOOD["dark"])], 0, -38, 0, -30), ow=1.6)
    d.path(smooth([(-11, 0), (-13, 8), (-10, 16)], closed=False), stroke="#ffffff", sw=2.2, op=0.6)
    for (x, y, r) in ((-4, 16, 2), (5, 19, 1.4), (1, 13, 1)):
        d.circle(x, y, r, fill="#ffffff", opacity=0.6)


def fang(d: Doc, L=22, W=8, pal=BONE):
    """Curved fang pointing +y from its root at the origin."""
    pts = [(-W / 2, 0), (W / 2, 0), (W * 0.2, L * 0.6), (-W * 0.15, L), (-W * 0.35, L * 0.55)]
    dd = smooth(pts, tension=0.5)
    d.path(dd, stroke=OUTLINE, sw=3.2)
    d.path(dd, fill=d.lin([(0, pal["light"]), (1, pal["base"])], -W / 2, 0, W / 2, L))


def gear(d: Doc, cx, cy, r, pal=BRONZE, teeth=10):
    pts = []
    for i in range(teeth):
        a0 = i * 2 * math.pi / teeth
        w = math.pi / teeth
        for a, rr in ((a0 - w * 0.55, r * 0.8), (a0 - w * 0.35, r), (a0 + w * 0.35, r), (a0 + w * 0.55, r * 0.8)):
            pts.append(polar(cx, cy, rr, a))
    d.path(poly(pts) + " " + circle_path(cx, cy, r * 0.34, ccw=True), stroke=OUTLINE, sw=3.4)
    d.path(poly(pts) + " " + circle_path(cx, cy, r * 0.34, ccw=True), fill=d.lin([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], cx - r, cy - r, cx + r, cy + r), fill_rule="evenodd")
    d.circle(cx, cy, r * 0.6, stroke=pal["dark"], stroke_width=1.2, opacity=0.7)


def campfire(d: Doc, cx, cy, s=1.0):
    from bh_shapes import flame
    for a in (-24, 24, 0):
        with d.g(T(cx, cy + 4 * s, a + 90, s)):
            d.shape(rrect_path(-22, -4, 44, 8, 4), fill=d.lin([(0, WOOD["light"]), (1, WOOD["dark"])], 0, -4, 0, 4), ow=1.8)
            d.circle(22, 0, 3.6, fill="#e8c890", stroke=OUTLINE, stroke_width=1.2)
    for i in range(7):
        a = math.pi * (0.1 + 0.8 * i / 6)
        x, y = cx + math.cos(a) * 26 * s, cy + 10 * s + math.sin(a) * 6 * s
        d.path(poly(blob(x, y, 4.5 * s, 6, 0.2, random.Random(i))), fill="#5a5660", stroke=OUTLINE, stroke_width=1.2)
    flame(d, cx, cy - 2 * s, 0.62 * s, EL["fire"])


def smoke(d: Doc, puffs, top="#8a84a0", bottom="#2a2438", op=1.0, outline=True):
    """Soft smoke cloud from (x, y, r) puffs."""
    ys = [p[1] - p[2] for p in puffs] + [p[1] + p[2] for p in puffs]
    g = d.lin([(0, top), (1, bottom)], 0, min(ys), 0, max(ys))
    if outline:
        for (x, y, r) in puffs:
            d.circle(x, y, r + 2.2, fill=OUTLINE, opacity=op)
    for (x, y, r) in puffs:
        d.circle(x, y, r, fill=g, opacity=op)
    for (x, y, r) in puffs:
        d.path(smooth(arc_pts(x, y, r * 0.78, math.radians(200), math.radians(280), 5), closed=False), stroke="#ffffff", sw=1.3, op=0.25 * op)


def pips(d: Doc, pts, lit=5, color=VIOLET, r=5.0):
    for i, (x, y) in enumerate(pts):
        on = i < lit
        if on:
            d.glow(x, y, r * 2.6, color["glow"], 0.7)
        d.path(poly([(x, y - r * 1.3), (x + r, y), (x, y + r * 1.3), (x - r, y)]), stroke=OUTLINE, sw=2.6)
        d.path(poly([(x, y - r * 1.3), (x + r, y), (x, y + r * 1.3), (x - r, y)]),
               fill=d.lin([(0, color["light"] if on else "#4a4458"), (1, color["base"] if on else "#1a1624")], x, y - r, x, y + r))
        if on:
            d.circle(x - r * 0.25, y - r * 0.4, r * 0.25, fill="#ffffff", opacity=0.9)


def hood_silhouette(d: Doc, fill, op=1.0, outline=True, lean=0.0):
    """Hooded assassin bust + cloak (feet at y=0, ~80 tall); lean skews the figure forward (+x)."""
    pts = [(0, -80), (9, -76), (13, -64), (11, -56), (20, -52), (26, -40), (27, -22), (24, -8), (28, 0),
           (-26, 0), (-22, -10), (-24, -26), (-22, -44), (-14, -54), (-11, -58), (-13, -68), (-8, -77)]
    pts = [(x + lean * (-y / 80) * 12, y) for x, y in pts]
    dd = smooth(pts, tension=0.45)
    if outline:
        d.path(dd, stroke=OUTLINE, sw=4.4, op=op)
    d.path(dd, fill=fill, op=op)
    return dd


def cracked_skull(d: Doc, cx, cy, s, pal=BONE, eye_glow=None):
    from bh_shapes import skull
    skull(d, cx, cy, s, pal=pal, eye_glow=eye_glow)
    cr = [(cx + 4 * s, cy - 30 * s), (cx + 1 * s, cy - 22 * s), (cx + 6 * s, cy - 16 * s), (cx + 2 * s, cy - 8 * s)]
    d.path(poly(cr, closed=False), stroke="#0a0410", sw=2.2 * s + 0.6)
    d.path(poly([cr[1], (cx - 6 * s, cy - 20 * s)], closed=False), stroke="#0a0410", sw=1.6 * s + 0.4)


def speed_lines(d: Doc, lines, color="#ffffff", op=0.6):
    for (x0, y0, x1, y1, w) in lines:
        d.path(ribbon([(x0, y0), (x1, y1)], [0.4, w]), fill=color, op=op)


def rune_glyph(d: Doc, cx, cy, s, color, sw=2.4, kind=0):
    """Small angular rune (no letters)."""
    shapes = [
        [[(0, -10), (0, 10)], [(0, -10), (7, -4)], [(0, 0), (-7, -6)]],
        [[(-6, -10), (-6, 10)], [(6, -10), (6, 10)], [(-6, -2), (6, 4)]],
        [[(0, -10), (7, 0), (0, 10), (-7, 0), (0, -10)], [(0, -4), (0, 4)]],
        [[(-7, -10), (7, 10)], [(7, -10), (-7, 10)], [(-7, 0), (7, 0)]],
        [[(0, -10), (0, 10)], [(-7, -10), (0, -3), (7, -10)]],
    ][kind % 5]
    dd = " ".join("M" + " L".join(f"{f(cx + x * s)},{f(cy + y * s)}" for x, y in st) for st in shapes)
    d.path(dd, stroke=OUTLINE, sw=sw + 2.2)
    d.path(dd, stroke=color, sw=sw)


def cloud(d: Doc, circles, top="#b8b0d0", bottom="#3a3060", op=None):
    ys = [c[1] - c[2] for c in circles] + [c[1] + c[2] for c in circles]
    g = d.lin([(0, top), (1, bottom)], 0, min(ys), 0, max(ys))
    for (x, y, r) in circles:
        d.circle(x, y, r + 2.4, fill=OUTLINE)
    for (x, y, r) in circles:
        d.circle(x, y, r, fill=g)
    for (x, y, r) in circles:
        d.path(smooth(arc_pts(x, y, r * 0.8, math.radians(200), math.radians(290), 5), closed=False), stroke="#ffffff", sw=1.4, op=0.35)


def wing_pair(d: Doc, cx, cy, s, pal=None):
    """Two small heraldic wings either side of (cx, cy)."""
    from icons_badges import wing
    pal = pal or dict(dark="#6a6e78", base="#dfe4ee", light="#ffffff")
    for flip in (False, True):
        with d.g(T(cx + (-4 if not flip else 4) * s, cy, 0, s)):
            wing(d, pal, flip=flip)
