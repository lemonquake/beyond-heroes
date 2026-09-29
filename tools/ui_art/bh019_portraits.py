"""bh-019 portraits: Lape the Ancient, the relic appraiser of Malasugue (game/assets/ui/portraits/lape.svg, 256x256).

Same painted-bust style and helpers as bh018_portraits.py: a very old figure in a deep black hood, face lost in
shadow but for two pale eye-glints and a long white beard, the gnarled head of his huge staff beside him cradling a
violet orb.
    python tools/ui_art/bh019_portraits.py
"""
from __future__ import annotations

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from bh_svg import Doc, OUTLINE, f, poly, smooth, lt, dk  # noqa: E402
from portraits import S, background, vignette, frame, shoulders  # noqa: E402

PORTRAITS = {}


def portrait(fn):
    def build():
        d = Doc(S, S, name="pt19_" + fn.__name__)
        fn(d)
        return d
    PORTRAITS[fn.__name__] = build
    return fn


@portrait
def lape(d):
    """Lape the Ancient: a deep charcoal hood with a frayed rim, two pale glints in the dark, a long white beard in
    wisps, bony fingers round a twisted staff whose root-cage holds a violet orb."""
    rng = random.Random(1901)
    background(d, "#140f1c", haze="#6a3ab0", haze2="#2a1a40", motes="#c8a8ff", seed=191)
    vignette(d)
    cx, cy = 132, 116
    robe = dict(dark="#050407", base="#17141c", light="#3a3444")
    shoulders(d, robe, top=182, spread=1.08)
    # ---- the staff behind the left shoulder: twisted shaft, root cage, orb
    sx0, sy0 = 40, 256
    sx1, sy1 = 46, 90
    shaft = smooth([(sx0 - 7, sy0), (sx0 - 3, 190), (sx1 - 8, 120), (sx1 - 6, sy1), (sx1 + 6, sy1), (sx1 + 6, 120), (sx0 + 9, 190), (sx0 + 8, sy0)], tension=0.35)
    d.path(shaft, stroke=OUTLINE, sw=4)
    d.path(shaft, fill=d.lin([(0, "#3a2818"), (0.5, "#5a4028"), (1, "#20140a")], sx0 - 8, 0, sx0 + 10, 0))
    for i in range(7):   # twist grooves
        y = 96 + i * 22
        d.path(f"M{f(sx1 - 6 + (y - 70) * -0.06)},{y} q8,-6 14,4", stroke="#1a1008", sw=2.2, op=0.7)
    ox, oy = 46, 66
    d.circle(ox, oy, 46, fill=d.rad([(0, "#b070ff", 0.55), (0.5, "#7a3ad0", 0.18), (1, "#7a3ad0", 0)], ox, oy, 46))
    d.circle(ox, oy, 15, fill=d.rad([(0, "#ffffff"), (0.35, "#e0c8ff"), (0.75, "#9a5aff"), (1, "#4a1a90")], ox - 4, oy - 5, 17),
             stroke=OUTLINE, stroke_width=2.4)
    for a0 in (-150, -95, -40, 20, 75, 140):   # roots gripping the orb
        a = math.radians(a0)
        p0 = (ox + math.cos(a) * 26, oy + math.sin(a) * 26 + 10)
        p1 = (ox + math.cos(a) * 17, oy + math.sin(a) * 17)
        p2 = (ox + math.cos(a + 0.5) * 9, oy + math.sin(a + 0.5) * 12 - 6)
        d.path(f"M{f(sx1)},{f(sy1 + 4)} Q{f(p0[0])},{f(p0[1])} {f(p1[0])},{f(p1[1])} T{f(p2[0])},{f(p2[1])}",
               stroke=OUTLINE, sw=6.5, fill="none")
        d.path(f"M{f(sx1)},{f(sy1 + 4)} Q{f(p0[0])},{f(p0[1])} {f(p1[0])},{f(p1[1])} T{f(p2[0])},{f(p2[1])}",
               stroke="#4a3420", sw=3.2, fill="none")
    for (hx, hy, L) in ((58, 96, 30), (36, 100, 22)):   # hanging charms on cords
        d.path(f"M{hx},{hy} L{hx + 1},{hy + L}", stroke="#8a7a5a", sw=1.4)
        d.circle(hx + 1, hy + L + 4, 4, fill="#c8a860", stroke=OUTLINE, stroke_width=1.5)
    d.path(smooth([(sx1 + 6, 84), (sx1 + 22, 96), (sx1 + 16, 132), (sx1 + 26, 160)], closed=False), stroke="#5a1a2a", sw=4, op=0.9)
    # ---- the hood: tall, pointed, sagging; frayed rim; the opening a well of dark
    hood_o = [(cx + 6, 14), (cx + 52, 40), (cx + 74, 100), (cx + 80, 172), (cx + 54, 204), (cx - 54, 204), (cx - 80, 172), (cx - 72, 100), (cx - 44, 42)]
    hd = smooth(hood_o, tension=0.5)
    d.path(hd, stroke=OUTLINE, sw=6)
    d.path(hd, fill=d.lin([(0, robe["light"]), (0.4, robe["base"]), (1, robe["dark"])], cx - 60, 20, cx + 70, 200))
    for pts in (((cx - 26, 44), (cx - 50, 108), (cx - 60, 172)), ((cx + 30, 46), (cx + 56, 110), (cx + 62, 170)), ((cx + 4, 18), (cx + 2, 40))):
        d.path(smooth(pts, closed=False), stroke=robe["dark"], sw=3, op=0.85)
    op_ = smooth([(cx, 52), (cx + 42, 74), (cx + 50, 130), (cx + 36, 184), (cx - 36, 184), (cx - 50, 130), (cx - 42, 74)], tension=0.5)
    d.path(op_, fill=d.rad([(0, "#0e0b12"), (1, "#000000")], cx, cy + 6, 72))
    rim = [(cx - 42, 74), (cx, 52), (cx + 42, 74)]
    d.path(smooth(rim, closed=False), stroke="#4a4454", sw=3, op=0.7)
    for i in range(9):   # frayed threads on the hood rim
        t = i / 8.0
        x = cx - 40 + 80 * t
        y = 74 - 22 * math.sin(math.pi * t) + 2
        d.path(f"M{f(x)},{f(y)} l{f(rng.uniform(-2, 2))},{f(rng.uniform(4, 9))}", stroke="#2a2630", sw=1.6, op=0.8)
    # two pale eye-glints, deep in the dark
    for sx in (-1, 1):
        ex, ey = cx + sx * 15, cy - 4
        d.circle(ex, ey, 9, fill=d.rad([(0, "#d8c8ff", 0.4), (1, "#d8c8ff", 0)], ex, ey, 9))
        d.ellipse(ex, ey, 3.6, 1.3, fill="#efe6ff", opacity=0.9)
    # a hint of a hooked nose and cheekbone catching the orb light
    d.path(smooth([(cx - 2, cy + 2), (cx - 5, cy + 16), (cx + 1, cy + 20)], closed=False), stroke="#5a4a6a", sw=2.2, op=0.55)
    d.path(smooth([(cx - 34, cy + 6), (cx - 24, cy + 14)], closed=False), stroke="#6a5a7a", sw=2, op=0.4)
    # ---- the beard: long white wisps spilling out of the hood onto the robe
    beard = smooth([(cx - 26, cy + 18), (cx, cy + 26), (cx + 26, cy + 18), (cx + 24, cy + 50), (cx + 14, cy + 70), (cx + 18, cy + 96),
                    (cx + 6, cy + 116), (cx + 4, cy + 138), (cx - 4, cy + 120), (cx - 14, cy + 98), (cx - 10, cy + 74), (cx - 24, cy + 52)], tension=0.5)
    d.path(beard, stroke=OUTLINE, sw=4)
    d.path(beard, fill=d.lin([(0, "#e8e4ee"), (0.6, "#b8b2c4"), (1, "#7a7488")], cx, cy + 20, cx, cy + 140))
    for i in range(14):
        x0 = cx - 24 + i * 3.6 + rng.uniform(-1.5, 1.5)
        L = rng.uniform(30, 100) * (1.0 - abs(i - 6.5) / 14.0)
        d.path(f"M{f(x0)},{f(cy + 24)} q{f(rng.uniform(-8, 8))},{f(L * 0.5)} {f(rng.uniform(-6, 6) + (cx - x0) * 0.3)},{f(L)}",
               stroke="#8a8498" if i % 2 else "#ffffff", sw=1.2, op=0.55)
    d.path(smooth([(cx - 22, cy + 22), (cx - 4, cy + 30), (cx + 20, cy + 22)], closed=False), stroke="#fbf8ff", sw=2.2, op=0.6)
    # ---- rope belt knot, the old key pendant, bony fingers round the staff
    d.path(f"M{cx - 60},{234} Q{cx},{246} {cx + 60},{234}", stroke="#5a4a32", sw=5)
    d.circle(cx + 30, 238, 5, fill="#6a5a3a", stroke=OUTLINE, stroke_width=2)
    kx, ky = cx + 38, 196
    d.path(f"M{cx + 22},{cy + 70} L{kx},{ky - 8}", stroke="#8a7a5a", sw=1.4)
    d.circle(kx, ky - 4, 6, fill="none", stroke="#c8a860", sw=3)
    d.path(f"M{kx},{ky + 2} l0,20 m0,-6 l6,0 m-6,6 l5,0", stroke="#c8a860", sw=3, fill="none")
    for i in range(4):
        fy = 176 + i * 11
        fing = smooth([(sx0 - 14, fy), (sx0 + 4, fy - 4), (sx0 + 20, fy + 1), (sx0 + 18, fy + 9), (sx0 + 2, fy + 7), (sx0 - 14, fy + 8)], tension=0.4)
        d.path(fing, stroke=OUTLINE, sw=2.6)
        d.path(fing, fill=d.lin([(0, "#c8b8a8"), (1, "#7a6a60")], 0, fy, 0, fy + 9))
        d.circle(sx0 + 8, fy + 2, 1.8, fill="#e8dcd0", opacity=0.7)
    sleeve = smooth([(sx0 - 34, 256), (sx0 - 30, 186), (sx0 - 12, 172), (sx0 - 4, 200), (sx0 - 6, 256)], tension=0.4)
    d.path(sleeve, stroke=OUTLINE, sw=4)
    d.path(sleeve, fill=d.lin([(0, robe["light"]), (1, robe["dark"])], sx0 - 34, 0, sx0, 0))
    frame(d, dict(dark="#16101e", base="#5a4a70", light="#c8b8e8"), gem_col="#b070ff")


def main():
    out_dir = os.path.abspath(os.path.join(HERE, "..", "..", "game", "assets", "ui", "portraits"))
    paths = []
    for name, fn in PORTRAITS.items():
        p = os.path.join(out_dir, name + ".svg")
        if os.path.exists(p) and "--force" not in sys.argv:
            existing = open(p, encoding="utf-8").read()
            if "pt19_" not in existing:
                raise SystemExit(f"refusing to overwrite existing portrait {name}")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(fn().svg())
        paths.append(p)
        print("WROTE", p)
    return paths


if __name__ == "__main__":
    main()
