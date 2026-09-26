"""bh-002 interface glyphs (icons/ui/): 64x64 viewBox, bold near-white shapes with a dark outline so they read at
24-64 px and tint cleanly with modulate (white base * colour)."""
from __future__ import annotations

import math

from bh_svg import Doc, OUTLINE, f, poly, smooth, star_pts, ngon, polar, rrect_path, circle_path, arc_pts, qbez

UI_ICONS = {}
OW = 2.4          # outline half-width


def icon(fn):
    def build():
        d = Doc(64, 64, name="ui_" + fn.__name__)
        fn(d)
        return d
    UI_ICONS[fn.__name__] = build
    return fn


def fill(d):
    return d.lin([(0, "#ffffff"), (0.55, "#f1ede6"), (1, "#c9c2b6")], 0, 6, 0, 58)


def G(d, dd, rule=None, ow=OW):
    """Outlined glyph: dark outline then the white body."""
    d.path(dd, stroke=OUTLINE, sw=ow * 2, fill_rule=rule)
    d.path(dd, fill=fill(d), fill_rule=rule)


def S(d, dd, w=5.0, ow=OW):
    """Outlined stroke glyph."""
    d.path(dd, stroke=OUTLINE, sw=w + ow * 2)
    d.path(dd, stroke="#f4f0ea", sw=w)


def detail(d, dd, w=1.6, op=0.85):
    d.path(dd, stroke=OUTLINE, sw=w, op=op)


@icon
def gold(d):
    for (x, y) in ((22, 40), (22, 32), (22, 24)):
        G(d, f"M{x - 13},{y} a13,5 0 1 0 26,0 a13,5 0 1 0 -26,0 Z M{x - 13},{y} L{x - 13},{y + 5} a13,5 0 0 0 26,0 L{x + 13},{y}")
    G(d, "M30,46 a14,6 0 1 0 28,0 a14,6 0 1 0 -28,0 Z M30,46 L30,52 a14,6 0 0 0 28,0 L58,46")
    detail(d, "M38,46 L44,43 L50,46 L44,49 Z", 1.4)


@icon
def aether(d):
    G(d, poly([(32, 4), (44, 20), (40, 48), (32, 60), (24, 48), (20, 20)]))
    detail(d, "M32,4 L30,30 L32,60 M20,20 L30,30 L44,20 M24,48 L30,30 L40,48", 1.3, 0.6)
    G(d, poly([(50, 30), (56, 38), (50, 50), (46, 40)]))
    G(d, poly([(14, 34), (18, 42), (14, 52), (10, 42)]))


@icon
def level(d):
    G(d, poly(star_pts(32, 34, 5, 26, 11)))
    S(d, "M32,44 L32,24 M24,31 L32,23 L40,31", w=4.2, ow=1.4)


@icon
def xp(d):
    G(d, circle_path(32, 32, 14))
    for i in range(8):
        a = i * math.pi / 4
        p0, p1 = polar(32, 32, 18, a), polar(32, 32, 28 if i % 2 == 0 else 24, a)
        S(d, f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}", w=4 if i % 2 == 0 else 3)
    detail(d, poly(star_pts(32, 32, 4, 8, 2.5)), 1.4)


@icon
def sort(d):
    S(d, "M18,52 L18,12 M8,22 L18,12 L28,22", w=5)
    S(d, "M46,12 L46,52 M36,42 L46,52 L56,42", w=5)


@icon
def filter(d):
    G(d, poly([(6, 10), (58, 10), (38, 32), (38, 52), (26, 58), (26, 32)]))
    detail(d, "M14,16 L50,16", 1.2, 0.5)


@icon
def search(d):
    d.path(circle_path(26, 26, 16) + " " + circle_path(26, 26, 10), stroke=OUTLINE, sw=OW * 2)
    d.path(circle_path(26, 26, 16) + " " + circle_path(26, 26, 10), fill=fill(d), fill_rule="evenodd")
    S(d, "M38,38 L56,56", w=8)


@icon
def lock(d):
    S(d, "M20,30 L20,20 C20,8 44,8 44,20 L44,30", w=6)
    G(d, rrect_path(12, 28, 40, 30, 5))
    d.path("M32,38 a4,4 0 1 0 0.01,0 Z M30,43 L34,43 L35,51 L29,51 Z", fill=OUTLINE)


@icon
def favorite(d):
    G(d, poly(star_pts(32, 34, 5, 28, 12)))


@icon
def junk(d):
    # cracked pot shards
    G(d, poly([(10, 50), (14, 30), (26, 26), (30, 36), (24, 42), (28, 54)]))
    G(d, poly([(32, 54), (30, 38), (38, 30), (52, 32), (56, 50)]))
    G(d, poly([(28, 20), (36, 10), (44, 16), (38, 24)]))
    detail(d, "M38,40 L46,44 M16,38 L22,40", 1.4)


@icon
def trash(d):
    G(d, poly([(14, 20), (50, 20), (46, 58), (18, 58)]))
    G(d, rrect_path(8, 12, 48, 8, 2))
    G(d, rrect_path(24, 5, 16, 8, 2))
    detail(d, "M24,28 L25,50 M32,28 L32,50 M40,28 L39,50", 2.2)


@icon
def split(d):
    S(d, "M32,58 L32,34 L14,14 M32,34 L50,14", w=5)
    S(d, "M8,22 L14,14 L22,14 M42,14 L50,14 L56,22", w=4)


@icon
def compare(d):
    S(d, "M32,8 L32,54 M20,56 L44,56", w=4.4)
    S(d, "M10,16 L54,16", w=4)
    G(d, "M4,34 L16,16 L28,34 Z M36,34 L48,16 L60,34 Z")
    G(d, "M4,34 Q16,44 28,34 Z M36,34 Q48,44 60,34 Z")


@icon
def settings(d):
    pts = []
    for i in range(16):
        a = i * math.pi / 8 - math.pi / 16
        r = 28 if i % 2 == 0 else 21
        pts.append(polar(32, 32, r, a))
        pts.append(polar(32, 32, r, a + math.pi / 8 * (0.5 if i % 2 == 0 else 0.5)))
    teeth = []
    for i in range(8):
        a = i * math.pi / 4
        teeth += [polar(32, 32, 21, a - 0.32), polar(32, 32, 28, a - 0.2), polar(32, 32, 28, a + 0.2), polar(32, 32, 21, a + 0.32)]
    G(d, poly(teeth) + " " + circle_path(32, 32, 8), rule="evenodd")


@icon
def save(d):
    G(d, rrect_path(10, 8, 40, 48, 4))
    G(d, rrect_path(10, 8, 8, 48, 3))
    detail(d, "M24,16 L44,16 M24,22 L40,22", 1.4)
    S(d, "M40,30 L40,50 M32,42 L40,50 L48,42", w=4.4)


@icon
def load(d):
    G(d, rrect_path(10, 8, 40, 48, 4))
    G(d, rrect_path(10, 8, 8, 48, 3))
    detail(d, "M24,16 L44,16 M24,22 L40,22", 1.4)
    S(d, "M40,52 L40,30 M32,38 L40,30 L48,38", w=4.4)


@icon
def map(d):
    G(d, poly([(6, 14), (22, 8), (42, 14), (58, 8), (58, 50), (42, 56), (22, 50), (6, 56)]))
    detail(d, "M22,8 L22,50 M42,14 L42,56", 1.4, 0.7)
    d.path("M14,40 Q24,30 32,36 T48,24", stroke=OUTLINE, sw=1.8, stroke_dasharray="3 2.4")
    detail(d, "M44,20 L52,28 M52,20 L44,28", 2.2)


@icon
def teleport(d):
    d.path(circle_path(32, 32, 26, 16) + " " + circle_path(32, 32, 18, 9), stroke=OUTLINE, sw=OW * 2)
    d.path(circle_path(32, 32, 26, 16) + " " + circle_path(32, 32, 18, 9), fill=fill(d), fill_rule="evenodd")
    G(d, poly(star_pts(32, 32, 4, 12, 3)))
    S(d, "M32,4 L32,12 M32,52 L32,60", w=3)


@icon
def quest(d):
    G(d, rrect_path(12, 8, 40, 48, 4))
    G(d, rrect_path(6, 6, 52, 8, 4))
    G(d, rrect_path(6, 50, 52, 8, 4))
    d.path("M29,18 L35,18 L34,38 L30,38 Z M32,42 a3.4,3.4 0 1 0 0.01,0 Z", fill=OUTLINE)


@icon
def talk(d):
    G(d, "M8,14 Q8,6 18,6 L46,6 Q56,6 56,14 L56,34 Q56,42 46,42 L28,42 L14,56 L18,42 Q8,42 8,34 Z")
    for x in (22, 32, 42):
        d.circle(x, 24, 3.4, fill=OUTLINE)


@icon
def shop(d):
    G(d, "M20,14 Q32,22 44,14 L40,24 Q58,34 54,50 Q50,60 32,60 Q14,60 10,50 Q6,34 24,24 Z")
    S(d, "M24,24 Q32,28 40,24", w=3)
    detail(d, "M32,34 L32,52 M26,38 Q32,33 38,38 Q32,44 26,48 Q32,53 38,48", 2.2)


@icon
def repair(d):
    # hammer over an anvil
    G(d, "M8,44 L56,44 L50,50 L42,50 L44,58 L20,58 L22,50 L14,50 Z")
    G(d, "M4,38 L8,34 L50,34 L58,38 L50,42 L8,42 Z")
    S(d, "M14,34 L34,16", w=5)
    G(d, poly([(30, 12), (39, 3), (48, 12), (39, 21)]))


@icon
def buyback(d):
    G(d, circle_path(32, 34, 16))
    detail(d, "M32,24 L32,44 M27,28 Q32,24 37,28 Q32,33 27,38 Q32,44 37,40", 2.2)
    S(d, "M10,26 A24,24 0 0 1 50,12", w=4)
    G(d, poly([(46, 4), (58, 12), (46, 20)]))


@icon
def back(d):
    S(d, "M54,48 Q54,22 26,22 L14,22", w=6)
    G(d, poly([(4, 22), (20, 8), (20, 36)]))


@icon
def close(d):
    S(d, "M14,14 L50,50 M50,14 L14,50", w=8)


@icon
def plus(d):
    S(d, "M32,10 L32,54 M10,32 L54,32", w=9)


@icon
def minus(d):
    S(d, "M10,32 L54,32", w=9)


@icon
def check(d):
    S(d, "M10,34 L26,50 L54,16", w=9)


@icon
def warning(d):
    G(d, "M32,4 L60,56 L4,56 Z")
    d.path("M29,20 L35,20 L34,40 L30,40 Z M32,44 a3.4,3.4 0 1 0 0.01,0 Z", fill=OUTLINE)


@icon
def info(d):
    G(d, circle_path(32, 32, 27))
    d.path("M28,28 L36,28 L36,48 L28,48 Z M32,14 a4,4 0 1 0 0.01,0 Z", fill=OUTLINE)


@icon
def skull(d):
    G(d, "M10,28 Q10,4 32,4 Q54,4 54,28 Q54,40 46,44 L46,56 L18,56 L18,44 Q10,40 10,28 Z")
    d.path("M16,28 Q16,20 24,22 Q30,24 28,32 Q24,38 18,34 Z M48,28 Q48,20 40,22 Q34,24 36,32 Q40,38 46,34 Z M32,36 L28,44 L36,44 Z", fill=OUTLINE)
    detail(d, "M24,48 L24,56 M32,48 L32,56 M40,48 L40,56", 2)


@icon
def crown(d):
    G(d, poly([(6, 18), (20, 32), (32, 10), (44, 32), (58, 18), (52, 50), (12, 50)]))
    G(d, rrect_path(10, 48, 44, 9, 2))
    for (x, y) in ((6, 16), (32, 8), (58, 16)):
        d.circle(x, y, 4, fill=fill(d), stroke=OUTLINE, stroke_width=2.4)
    detail(d, "M32,34 L36,40 L32,46 L28,40 Z", 1.6)
