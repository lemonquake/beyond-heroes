"""bh-003 guild banners and crests (game/assets/ui/guilds/).

  swordfin_banner.svg / lantern_banner.svg   viewBox 0 0 256 384, hanging swallow-tailed banner on a rod
  swordfin_crest.svg  / lantern_crest.svg    viewBox 0 0 128 128, round crest for HUD / sheet / name plates
  swordfin_banner.png / lantern_banner.png   512x768 cloth texture (same art, cloth only - no rod - so it maps onto a
                                             3D cloth mesh), rendered from an in-memory SVG variant with resvg.

Colours (LORE §5/§8): Swordfin = deep sea-blue + silver; Lantern = dusk violet + gold, Aether-cyan eye.
Motto text is emitted as glyph outlines (bh003_text), never <text>.
"""
from __future__ import annotations

import math

from bh_svg import Doc, OUTLINE, STEEL, GOLD, WOOD, f, poly, smooth, mix, lt, dk, ribbon, polar, star_pts
from bh_shapes import T, sword, smooth_pts
from bh003_text import text_path, cap_height, BOOK_SERIF_BOLD

GUILDS = {}
AE_C = "#7ff3ff"

SEA = dict(dark="#061a3c", base="#123e7a", light="#2e6cb4", deep="#030c1e")
SILVER = dict(dark="#46505c", base="#b8c4d0", light="#ffffff")
DUSK = dict(dark="#150a2c", base="#3e2470", light="#6c4aa8", deep="#08041a")
GOLDT = dict(dark="#6a4210", base="#d8a838", light="#fff0b0")
BRIGHT_STEEL = dict(dark="#3a4250", base="#b4bfcc", light="#ffffff", glow="#e8f0ff")


def reg(name, w, h, **kw):
    def deco(fn):
        def build():
            d = Doc(w, h, name=name)
            fn(d, **kw)
            return d
        GUILDS[name] = build
        return fn
    return deco


# ------------------------------------------------------------------------------------------ symbols (local frame)

def marlin(d):
    """Silver swordfish facing right, local x[-96,114] y[-60,40]. Origin mid-body."""
    n = 26
    spine = []
    for i in range(n):
        t = i / (n - 1)
        spine.append((-62 + 110 * t, -10 * math.sin(math.pi * t)))
    ws = [5 + 25 * math.sin(math.pi * min(1.0, (i / (n - 1)) ** 1.2 * 0.88)) for i in range(n)]
    top = lambda k: (spine[k][0], spine[k][1] - ws[k] / 2)
    hx, hy = spine[-1]
    body = ribbon(spine, ws)
    silver = d.lin([(0, "#6a7f98"), (0.35, "#b8c8d8"), (0.6, "#eef4fa"), (1, "#ffffff")], 0, -22, 0, 16)
    fin_col = d.lin([(0, "#dfe8f0"), (0.5, "#8aa0b8"), (1, "#3a4a64")], 0, -60, 0, 0)
    # tail (lunate)
    tail = (f"M-58,-3 Q-70,-16 -96,-40 Q-84,-12 -74,0 Q-84,12 -94,36 Q-70,16 -58,3 Z")
    d.path(tail, stroke=OUTLINE, sw=5)
    d.path(tail, fill=fin_col)
    # dorsal sail (tall in front, falling back) with rays
    k0, k1 = 8, 20
    base = [top(k) for k in range(k0, k1 + 1)]
    bx0, by0 = base[0]
    bx1, by1 = base[-1]
    sail = [(bx1, by1), (bx1 - 4, by1 - 40), (bx1 - 16, by1 - 44), (bx1 - 34, by1 - 34), (bx0 + 16, by0 - 16), (bx0, by0 - 2)]
    sd = smooth(sail, closed=False, tension=0.5) + " " + " ".join(f"L{f(x)},{f(y)}" for x, y in base) + " Z"
    d.path(sd, stroke=OUTLINE, sw=5)
    d.path(sd, fill=d.lin([(0, "#e8f0fa"), (0.5, "#7a94b4"), (1, "#2a3c5a")], 0, by1 - 44, 0, by1))
    for j in range(1, 7):
        bx, by = base[min(len(base) - 1, j * 2)]
        d.path(f"M{f(bx)},{f(by)} L{f(bx - 6 - j)},{f(by - 38 + j * 4.2)}", stroke="#2a3c5a", sw=1.1, op=0.7)
    # anal / pelvic fins
    af = "M-34,10 Q-40,24 -50,26 Q-44,14 -42,8 Z"
    d.path(af, stroke=OUTLINE, sw=4)
    d.path(af, fill=fin_col)
    # body
    d.path(body, stroke=OUTLINE, sw=5.5)
    d.path(body, fill=silver)
    # bill (upper jaw sword) + lower jaw
    bill = f"M{f(hx - 6)},{f(hy - 6)} L{f(hx + 66)},{f(hy - 5)} L{f(hx - 4)},{f(hy + 1.5)} Z"
    d.path(bill, stroke=OUTLINE, sw=4.5)
    d.path(bill, fill=d.lin([(0, "#ffffff"), (1, "#8aa0b8")], 0, hy - 6, 0, hy + 2))
    jaw = f"M{f(hx - 6)},{f(hy + 1)} L{f(hx + 12)},{f(hy + 2)} L{f(hx - 6)},{f(hy + 6)} Z"
    d.path(jaw, stroke=OUTLINE, sw=3.5)
    d.path(jaw, fill="#c8d4e0")
    # dark back band + marlin bars
    back = smooth_pts([(-56, -4), (-30, -16), (0, -22), (26, -20), (44, -10)], 20)
    d.path(ribbon(back, [2 + 5 * math.sin(math.pi * i / 19) for i in range(20)]), fill="#3a5478", op=0.7)
    for x in range(-44, 24, 9):
        i = min(n - 1, max(0, round((x + 62) / 110 * (n - 1))))
        cy, w = spine[i][1], ws[i]
        d.path(f"M{f(x)},{f(cy - w * 0.38)} L{f(x - 2)},{f(cy + w * 0.2)}", stroke="#5a8ad0", sw=2.2, op=0.55)
    # lateral highlight
    hl = smooth_pts([(-50, -1), (-20, -6), (10, -10), (36, -8)], 16)
    d.path(poly(hl, closed=False), stroke="#ffffff", sw=1.6, op=0.8)
    # gill + eye + pectoral fin
    d.path(f"M{f(hx - 16)},{f(hy - 9)} Q{f(hx - 11)},{f(hy)} {f(hx - 16)},{f(hy + 7)}", stroke="#3a4a64", sw=1.6)
    pf = f"M{f(hx - 18)},{f(hy + 4)} Q{f(hx - 30)},{f(hy + 20)} {f(hx - 44)},{f(hy + 24)} Q{f(hx - 30)},{f(hy + 10)} {f(hx - 22)},{f(hy + 2)} Z"
    d.path(pf, stroke=OUTLINE, sw=3.5)
    d.path(pf, fill=fin_col)
    ex, ey = hx - 6, hy - 3
    d.circle(ex, ey, 3.6, fill=OUTLINE)
    d.circle(ex, ey, 2.6, fill="#0a1a30")
    d.circle(ex - 0.8, ey - 0.9, 0.9, fill="#ffffff")


def spray(d, pts, col="#dff4ff"):
    for (x, y, r) in pts:
        d.circle(x, y, r + 1.2, fill=OUTLINE, opacity=0.6)
        d.circle(x, y, r, fill=col)


def swordfin_symbol(d, scale=1.0, glow=True):
    """Marlin leaping over two crossed blades. Local frame ~ x[-100,100] y[-90,90]."""
    if glow:
        d.glow(0, 0, 110, "#6ab0ff", 0.35)
    for sx in (-1, 1):
        with d.g(T(sx * -50, 58, sx * 38, 1.0)):
            sword(d, L=112, W=13, pal=BRIGHT_STEEL, hilt=dict(dark="#3a4250", base="#9aa8b8", light="#ffffff"),
                  grip_pal=dict(dark="#061a3c", base="#123e7a", light="#2e6cb4"))
    # a curl of wave between the hilts
    wv = poly([(x, 84 - 6 * math.sin(x / 8.0)) for x in range(-30, 31, 3)], closed=False)
    d.path(wv, stroke=OUTLINE, sw=6)
    d.path(wv, stroke="#9ad8ff", sw=3)
    spray(d, [(-78, 30, 3.2), (-68, 16, 2.2), (82, 30, 3), (74, 16, 2.0), (90, 14, 1.6)])
    with d.g(T(-4, -30, -22, 0.9)):
        marlin(d)


def eye_flame(d, cx, cy, s=1.0):
    """Flame whose heart is an open eye (the Lantern's light)."""
    d.glow(cx, cy, 46 * s, "#ffd070", 0.7, core="#ffffff")
    outer = (f"M{f(cx)},{f(cy - 44 * s)} C{f(cx + 8 * s)},{f(cy - 30 * s)} {f(cx + 26 * s)},{f(cy - 14 * s)} {f(cx + 26 * s)},{f(cy + 4 * s)} "
             f"C{f(cx + 26 * s)},{f(cy + 22 * s)} {f(cx + 14 * s)},{f(cy + 32 * s)} {f(cx)},{f(cy + 32 * s)} "
             f"C{f(cx - 14 * s)},{f(cy + 32 * s)} {f(cx - 26 * s)},{f(cy + 22 * s)} {f(cx - 26 * s)},{f(cy + 4 * s)} "
             f"C{f(cx - 26 * s)},{f(cy - 12 * s)} {f(cx - 12 * s)},{f(cy - 22 * s)} {f(cx - 6 * s)},{f(cy - 30 * s)} "
             f"C{f(cx - 4 * s)},{f(cy - 22 * s)} {f(cx - 2 * s)},{f(cy - 30 * s)} {f(cx)},{f(cy - 44 * s)} Z")
    d.path(outer, stroke=OUTLINE, sw=4 * s)
    d.path(outer, fill=d.lin([(0, "#fff6c0"), (0.4, "#ffc038"), (1, "#e0601a")], cx, cy - 44 * s, cx, cy + 32 * s))
    # the eye
    w, h = 21 * s, 12 * s
    ey = cy + 8 * s
    eye = f"M{f(cx - w)},{f(ey)} Q{f(cx)},{f(ey - h * 1.6)} {f(cx + w)},{f(ey)} Q{f(cx)},{f(ey + h * 1.6)} {f(cx - w)},{f(ey)} Z"
    d.path(eye, stroke=OUTLINE, sw=3.4 * s)
    d.path(eye, fill=d.rad([(0, "#ffffff"), (1, "#ffe9b0")], cx, ey, w))
    d.circle(cx, ey, 8.4 * s, fill=OUTLINE)
    d.circle(cx, ey, 7.2 * s, fill=d.rad([(0, "#ffffff"), (0.45, AE_C), (1, "#1a7a9a")], cx - 1.5 * s, ey - 1.5 * s, 8 * s))
    d.path(f"M{f(cx)},{f(ey - 5.4 * s)} Q{f(cx + 2.2 * s)},{f(ey)} {f(cx)},{f(ey + 5.4 * s)} Q{f(cx - 2.2 * s)},{f(ey)} {f(cx)},{f(ey - 5.4 * s)} Z", fill="#06121c")
    d.circle(cx - 2.6 * s, ey - 2.6 * s, 1.5 * s, fill="#ffffff")


def lantern_symbol(d, glow=True, rays_on=True):
    """Golden lantern holding an eye-shaped flame. Local frame ~ x[-60,60] y[-100,80]."""
    G = GOLDT
    gold_v = lambda y0, y1: d.lin([(0, G["light"]), (0.45, G["base"]), (1, G["dark"])], 0, y0, 0, y1)
    gold_h = lambda x0, x1: d.lin([(0, G["light"]), (0.5, G["base"]), (1, G["dark"])], x0, 0, x1, 0)
    if glow:
        d.glow(0, 4, 116, "#ffc050", 0.45)
    if rays_on:
        for i in range(16):
            a = -math.pi / 2 + i * 2 * math.pi / 16
            L = 104 if i % 2 == 0 else 86
            p0, p1, p2 = polar(0, 4, 58, a - 0.07), polar(0, 4, L, a), polar(0, 4, 58, a + 0.07)
            d.path(poly([p0, p1, p2]), fill="#ffe08a", op=0.55 if i % 2 == 0 else 0.35)
    # handle ring
    d.circle(0, -88, 11, stroke=OUTLINE, stroke_width=8)
    d.circle(0, -88, 11, stroke=G["base"], stroke_width=4.4)
    d.path("M-6,-96 Q0,-99 6,-96", stroke=G["light"], sw=1.4)
    # roof
    roof = "M-40,-58 L-14,-78 L14,-78 L40,-58 Z"
    d.path(roof, stroke=OUTLINE, sw=5)
    d.path(roof, fill=gold_h(-40, 40))
    d.path("M-12,-74 L12,-74", stroke=G["light"], sw=1.4, op=0.8)
    d.path("M-8,-78 L8,-78 L5,-84 L-5,-84 Z", fill=G["base"], stroke=OUTLINE, stroke_width=2)
    # glass chamber (lit)
    glass = "M-34,-54 L34,-54 L28,44 L-28,44 Z"
    d.path(glass, stroke=OUTLINE, sw=5)
    d.path(glass, fill=d.rad([(0, "#fff6d0"), (0.45, "#ffb840"), (1, "#8a3a10")], 0, 4, 60))
    eye_flame(d, 0, 2, 1.0)
    # glass sheen
    d.path("M-26,-48 L-22,36", stroke="#ffffff", sw=2.4, op=0.35)
    # frame posts
    for sx in (-1, 1):
        post = poly([(sx * 34, -56), (sx * 40, -56), (sx * 33, 46), (sx * 27, 46)])
        d.path(post, stroke=OUTLINE, sw=3.4)
        d.path(post, fill=gold_h(sx * 27, sx * 40))
    # top and bottom bands
    for (y0, y1, x0) in ((-60, -50, 42), (42, 52, 38)):
        band = poly([(-x0, y0), (x0, y0), (x0, y1), (-x0, y1)])
        d.path(band, stroke=OUTLINE, sw=4)
        d.path(band, fill=gold_v(y0, y1))
    foot = "M-26,52 L26,52 L20,64 L-20,64 Z"
    d.path(foot, stroke=OUTLINE, sw=4)
    d.path(foot, fill=gold_v(52, 64))
    for x in (-20, 0, 20):
        d.circle(x, 47, 2.2, fill=G["light"], stroke=OUTLINE, stroke_width=1)


# ------------------------------------------------------------------------------------------ banner

def motto_ribbon(d, lines, cy, fill, ink, trim, x0=22, x1=234, h=None, size=18):
    h = h or (16 + size * 1.25 * len(lines))
    top, bot = cy - h / 2, cy + h / 2
    sag = 8
    # folded tails
    for sx, xe in ((-1, x0), (1, x1)):
        xi = xe - sx * 4
        xo = xe + sx * 16
        tail = poly([(xi, top + 10), (xo, top + 10), (xo - sx * 8, (top + bot) / 2 + 10), (xo, bot + 10), (xi, bot + 10)])
        d.path(tail, stroke=OUTLINE, sw=5)
        d.path(tail, fill=dk(fill["base"], 0.35))
        d.path(poly([(xi, bot), (xi + sx * 10, bot + 10), (xi, bot + 10)]), fill=dk(fill["base"], 0.65), stroke=OUTLINE, stroke_width=1.5)
    band = (f"M{x0},{f(top)} Q128,{f(top + sag)} {x1},{f(top)} L{x1},{f(bot)} Q128,{f(bot + sag)} {x0},{f(bot)} Z")
    d.path(band, stroke=OUTLINE, sw=5)
    d.path(band, fill=d.lin([(0, fill["light"]), (0.5, fill["base"]), (1, fill["dark"])], 0, top, 0, bot + sag))
    for yy in (top + 3.5, bot - 3.5):
        d.path(f"M{x0 + 4},{f(yy)} Q128,{f(yy + sag)} {x1 - 4},{f(yy)}", stroke=trim, sw=1.4, op=0.9)
    ch = cap_height(size, BOOK_SERIF_BOLD)
    n = len(lines)
    gap = size * 1.18
    for i, line in enumerate(lines):
        yc = cy + sag / 2 + (i - (n - 1) / 2) * gap
        dd, w = text_path(line, size, 128, yc + ch / 2, font=BOOK_SERIF_BOLD, tracking=1.2)
        if w > (x1 - x0) - 16:  # squash to fit
            dd, w = text_path(line, size, 128, yc + ch / 2, font=BOOK_SERIF_BOLD, tracking=1.2, sx=((x1 - x0) - 16) / w)
        d.path(dd, fill=lt(fill["light"], 0.3), op=0.6, transform="translate(0 1)")
        d.path(dd, fill=ink)


def cloth_outline(x0, x1, top, bot, notch):
    cx = (x0 + x1) / 2
    return [(x0, top), (x1, top), (x1, bot), (cx, notch), (x0, bot)]


def banner(d, cloth, trim, symbol, motto, pole=True, png=False):
    W, H = d.w, d.h
    k = W / 256.0
    if png:
        # texture variant: cloth fills the canvas (no rod); same art scaled via a group
        x0, x1, top, bot, notch = 0, 256, 0, 384, 318
    else:
        x0, x1, top, bot, notch = 26, 230, 30, 376, 318
    with d.g(f"scale({f(k)})" if k != 1 else None):
        cx = 128
        if pole and not png:
            # cords to a hook
            d.path("M40,28 L128,6 L216,28", stroke=OUTLINE, sw=4)
            d.path("M40,28 L128,6 L216,28", stroke=trim["dark"], sw=2)
            d.circle(128, 6, 4, fill=trim["base"], stroke=OUTLINE, stroke_width=1.6)
        shape = cloth_outline(x0, x1, top, bot, notch)
        dd = poly(shape)
        if not png:
            d.path(dd, stroke=OUTLINE, sw=6)
        # cloth with vertical folds
        folds = [(0, cloth["dark"]), (0.08, cloth["base"]), (0.2, cloth["light"]), (0.34, cloth["base"]), (0.46, dk(cloth["base"], 0.2)),
                 (0.58, cloth["light"]), (0.72, cloth["base"]), (0.86, dk(cloth["base"], 0.25)), (1, cloth["dark"])]
        d.path(dd, fill=d.lin(folds, x0, 0, x1, 0))
        d.path(dd, fill=d.lin([(0, "#000000", 0.0), (0.7, "#000000", 0.15), (1, "#000000", 0.45)], 0, top, 0, bot))
        d.path(dd, fill=d.rad([(0, "#ffffff", 0.12), (1, "#ffffff", 0)], cx, 150, 120))
        # trim border inset
        ins = 9
        inner = [(x0 + ins, top + ins + 20), (x1 - ins, top + ins + 20), (x1 - ins, bot - ins * 1.6), (cx, notch - ins * 1.2), (x0 + ins, bot - ins * 1.6)]
        d.path(poly(inner), stroke=OUTLINE, sw=6)
        d.path(poly(inner), stroke=trim["base"], sw=3)
        d.path(poly(inner), stroke=trim["light"], sw=0.9, op=0.8)
        # header sleeve for the rod
        sleeve = poly([(x0, top), (x1, top), (x1, top + 22), (x0, top + 22)])
        d.path(sleeve, fill=d.lin([(0, dk(cloth["base"], 0.4)), (0.5, cloth["dark"]), (1, "#000000")], 0, top, 0, top + 22), op=0.9)
        d.path(f"M{x0},{top + 22} L{x1},{top + 22}", stroke=OUTLINE, sw=4)
        d.path(f"M{x0},{top + 22} L{x1},{top + 22}", stroke=trim["base"], sw=2.2)
        for i in range(7):
            x = x0 + 18 + i * (x1 - x0 - 36) / 6
            d.path(poly(star_pts(x, top + 11, 4, 4.2, 1.4)), fill=trim["light"], op=0.85)
        # tassels on the tails
        if not png:
            for tx in (x0 + 2, x1 - 2):
                d.path(f"M{tx},{bot} L{tx},{bot + 4}", stroke=OUTLINE, sw=5)
                d.path(poly([(tx - 4, bot + 2), (tx + 4, bot + 2), (tx + 2, bot + 8), (tx - 2, bot + 8)]), fill=trim["base"], stroke=OUTLINE, stroke_width=1.4)
        # emblem
        with d.g(T(cx, 158, 0, 0.92)):
            symbol(d)
        motto_ribbon(d, *motto)
        if pole and not png:
            # rod + finials in front of the sleeve
            d.path("M8,30 L248,30", stroke=OUTLINE, sw=10)
            d.path("M8,30 L248,30", stroke=d.lin([(0, WOOD["light"]), (0.5, WOOD["base"]), (1, WOOD["dark"])], 0, 25, 0, 35), sw=6)
            for x in (8, 248):
                d.circle(x, 30, 8, fill=OUTLINE)
                d.circle(x, 30, 6, fill=d.rad([(0, trim["light"]), (0.6, trim["base"]), (1, trim["dark"])], x - 2, 28, 8))


SWORDFIN_MOTTO = (["STRIKE FIRST.", "STRIKE TRUE."], 282, dict(dark="#7a8898", base="#dfe6ee", light="#ffffff"), "#0a1f48", "#46505c")
LANTERN_MOTTO = (["WE KEEP THE LIGHT"], 286, dict(dark="#9a6a18", base="#f0c860", light="#fff4c8"), "#2a1048", "#6a4210")


@reg("swordfin_banner", 256, 384)
def swordfin_banner(d, png=False):
    banner(d, SEA, SILVER, swordfin_symbol, SWORDFIN_MOTTO, png=png)


@reg("lantern_banner", 256, 384)
def lantern_banner(d, png=False):
    banner(d, DUSK, GOLDT, lantern_symbol, LANTERN_MOTTO, png=png)


def banner_png_svg(name):
    fn = {"swordfin_banner": swordfin_banner, "lantern_banner": lantern_banner}[name]
    d = Doc(256, 384, name=name + "_png")
    fn(d, png=True)
    return d


# ------------------------------------------------------------------------------------------ crests

def crest(d, cloth, trim, symbol, sym_scale, sym_y=0):
    c = 64
    d.circle(c, c, 62, fill=OUTLINE)
    d.circle(c, c, 59, fill=d.lin([(0, trim["light"]), (0.45, trim["base"]), (1, trim["dark"])], 16, 6, 112, 122))
    d.circle(c, c, 51, fill=OUTLINE)
    d.circle(c, c, 49, fill=d.rad([(0, cloth["light"]), (0.6, cloth["base"]), (1, cloth["deep"])], 56, 50, 60))
    for i in range(12):
        a = -math.pi / 2 + (i + 0.5) * 2 * math.pi / 12
        x, y = polar(c, c, 55, a)
        d.circle(x, y, 1.8, fill=trim["light"], stroke=OUTLINE, stroke_width=0.8)
    with d.g(T(c, c + sym_y, 0, sym_scale)):
        symbol(d)
    d.circle(c, c, 49, stroke="#ffffff", stroke_width=1, opacity=0.25)


@reg("swordfin_crest", 128, 128)
def swordfin_crest(d):
    crest(d, SEA, SILVER, lambda dd: swordfin_symbol(dd, glow=False), 0.5, 8)


@reg("lantern_crest", 128, 128)
def lantern_crest(d):
    crest(d, DUSK, GOLDT, lambda dd: lantern_symbol(dd, glow=False, rays_on=False), 0.47, 9)
