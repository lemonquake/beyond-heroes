"""Reusable painted-emblem objects. Every function draws in local coordinates; callers place them with
`with d.g(transform)` so gradients stay simple (defined in the local frame)."""
from __future__ import annotations

import math

from bh_svg import (Doc, EL, STEEL, CRIMSON, GOLD, BRONZE, INDIGO, ARCANE, LEATHER, WOOD, BONE, OUTLINE, f, poly,
                    smooth, mix, lt, dk, ribbon, ribbon_pts, taper, arc_pts, bez, qbez, star_pts, ngon, jag_line,
                    blob, teardrop, circle_path, rrect_path, faceted, polar, rot, lerp, lerp2)


def T(x=0, y=0, a=0, s=1, sy=None):
    t = f"translate({f(x)} {f(y)})"
    if a:
        t += f" rotate({f(a)})"
    if s != 1 or (sy is not None and sy != s):
        t += f" scale({f(s)} {f(sy if sy is not None else s)})"
    return t


# --------------------------------------------------------------------------------------------
# weapons (local frame: origin at the guard/grip junction, blade pointing to -y)
# --------------------------------------------------------------------------------------------

def blade(d: Doc, L=64, W=11, pal=STEEL, fuller=True, ow=2.2, tip=1.25, flare=0.0, glow=None):
    tipy = -L
    sh = -L + W * tip
    pts = [(-W / 2, 0), (-W / 2 * (1 - flare), sh * 0.5), (-W / 2, sh), (0, tipy), (W / 2, sh), (W / 2 * (1 - flare), sh * 0.5), (W / 2, 0)]
    dpath = poly(pts)
    if glow:
        d.glow_stroke(poly([(0, 0), (0, tipy)], closed=False), glow, W * 1.1, op=0.5)
    d.path(dpath, stroke=OUTLINE, sw=ow * 2)
    g = d.lin([(0, pal["light"]), (0.47, lt(pal["base"], 0.35)), (0.53, pal["base"]), (1, pal["dark"])], -W / 2, 0, W / 2, 0)
    d.path(dpath, fill=g)
    # ridge / fuller
    if fuller:
        d.path(poly([(0, -2), (0, sh + 2)], closed=False), stroke=dk(pal["base"], 0.45), sw=max(1.0, W * 0.14), op=0.8)
        d.path(poly([(-W * 0.12, -2), (-W * 0.12, sh + 2)], closed=False), stroke=pal["light"], sw=0.7, op=0.7)
    # edge glint
    d.path(poly([(-W / 2 + 0.8, -3), (-W / 2 + 0.8, sh), (-0.6, tipy + 2.5)], closed=False), stroke="#ffffff", sw=0.9, op=0.75)


def guard(d: Doc, w=30, h=5.5, pal=GOLD, ow=2.0, curve=3.0):
    pts = [(-w / 2, -h / 2 - curve), (-w * 0.3, -h / 2), (w * 0.3, -h / 2), (w / 2, -h / 2 - curve),
           (w / 2 + 1.5, h / 2 - curve + 1), (w * 0.3, h / 2), (-w * 0.3, h / 2), (-w / 2 - 1.5, h / 2 - curve + 1)]
    dd = smooth(pts, tension=0.6)
    d.path(dd, stroke=OUTLINE, sw=ow * 2)
    d.path(dd, fill=d.lin([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], 0, -h / 2 - curve, 0, h / 2))
    for sx in (-1, 1):
        d.circle(sx * (w / 2 + 0.5), -curve + 0.2, h * 0.55, fill=d.rad([(0, pal["light"]), (1, pal["dark"])], sx * (w / 2) - 1, -curve - 1.5, h * 0.8), stroke=OUTLINE, stroke_width=1.2)
    d.circle(0, 0, h * 0.55, fill=CRIMSON["base"], stroke=OUTLINE, stroke_width=1.0)
    d.circle(-0.6, -0.8, h * 0.2, fill="#ffffff", opacity=0.7)


def grip(d: Doc, L=16, W=5, pal=LEATHER, metal=GOLD, pommel=4.5, ow=2.0):
    dd = rrect_path(-W / 2, 0, W, L, 1.5)
    d.path(dd, stroke=OUTLINE, sw=ow * 2)
    d.path(dd, fill=d.lin([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], -W / 2, 0, W / 2, 0))
    for i in range(1, int(L // 3.2) + 1):
        y = i * 3.2
        d.path(f"M{f(-W / 2)},{f(y - 1.2)} L{f(W / 2)},{f(y + 0.4)}", stroke=pal["dark"], sw=0.9, op=0.9)
    if pommel:
        d.circle(0, L + pommel * 0.8, pommel, fill=d.rad([(0, metal["light"]), (0.6, metal["base"]), (1, metal["dark"])], -1, L + pommel * 0.4, pommel * 1.3), stroke=OUTLINE, stroke_width=ow)


def sword(d: Doc, L=64, W=11, pal=STEEL, hilt=GOLD, grip_pal=LEATHER, glow=None, guard_w=None):
    grip(d, L=W * 1.45, W=W * 0.48, pal=grip_pal, metal=hilt, pommel=W * 0.42)
    blade(d, L=L, W=W, pal=pal, glow=glow)
    guard(d, w=guard_w or W * 3.0, h=W * 0.5, pal=hilt)


def greatsword(d: Doc, L=78, W=14, pal=STEEL, hilt=GOLD):
    grip(d, L=W * 2.0, W=W * 0.42, pal=LEATHER, metal=hilt, pommel=W * 0.4)
    blade(d, L=L, W=W, pal=pal, flare=0.12, tip=1.0)
    # ricasso wrap
    d.path(rrect_path(-W * 0.36, -W * 0.9, W * 0.72, W * 0.75, 1), fill=CRIMSON["base"], stroke=OUTLINE, stroke_width=1)
    guard(d, w=W * 3.3, h=W * 0.5, pal=hilt, curve=4)


def dagger(d: Doc, L=34, W=9, pal=STEEL, hilt=BRONZE):
    grip(d, L=W * 1.5, W=W * 0.55, pal=LEATHER, metal=hilt, pommel=W * 0.45)
    # curved leaf blade
    pts = [(-W / 2, 0), (-W * 0.6, -L * 0.45), (-W * 0.15, -L * 0.9), (0, -L), (W * 0.35, -L * 0.7), (W * 0.55, -L * 0.35), (W / 2, 0)]
    dd = smooth(pts, tension=0.8)
    d.path(dd, stroke=OUTLINE, sw=4.2)
    d.path(dd, fill=d.lin([(0, pal["light"]), (0.45, lt(pal["base"], 0.3)), (0.55, pal["base"]), (1, pal["dark"])], -W / 2, 0, W / 2, 0))
    d.path(smooth([(-W * 0.3, -2), (-W * 0.35, -L * 0.45), (-W * 0.05, -L * 0.9)], closed=False), stroke="#ffffff", sw=0.9, op=0.7)
    guard(d, w=W * 2.4, h=W * 0.5, pal=hilt, curve=-2)


def haft(d: Doc, y0, y1, W=5, pal=WOOD, bands=()):
    dd = rrect_path(-W / 2, y0, W, y1 - y0, W / 2)
    d.path(dd, stroke=OUTLINE, sw=4.2)
    d.path(dd, fill=d.lin([(0, pal["light"]), (0.45, pal["base"]), (1, pal["dark"])], -W / 2, 0, W / 2, 0))
    d.path(f"M{f(-W * 0.15)},{f(y0 + 2)} L{f(-W * 0.15)},{f(y1 - 2)}", stroke=pal["dark"], sw=0.6, op=0.6)
    for by, bh, bp in bands:
        bd = rrect_path(-W / 2 - 0.8, by, W + 1.6, bh, 0.8)
        d.path(bd, stroke=OUTLINE, sw=2.4)
        d.path(bd, fill=d.lin([(0, bp["light"]), (0.5, bp["base"]), (1, bp["dark"])], -W / 2, 0, W / 2, 0))


def axe(d: Doc, H=84, pal=STEEL, wood=WOOD):
    """Origin at the axe head centre on the haft; haft runs down."""
    haft(d, -10, H - 10, W=6, pal=wood, bands=((H - 22, 6, LEATHER), (H - 16, 3, GOLD)))
    # crescent bearded blade to the left (-x)
    outer = qbez((-6, -16), (-44, -14), (-40, 18), n=16)
    inner = [(-24, 10), (-14, 4), (-6, 6)]
    pts = [(-4, -9)] + outer + [(-34, 17)] + inner
    dd = smooth(pts, tension=0.5)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, dk(pal["base"], 0.2)), (0.55, pal["base"]), (1, pal["light"])], -4, 0, -42, 0))
    # bright honed edge
    edge = qbez((-12, -15), (-43, -12), (-39, 17), n=16)
    d.path(ribbon(edge, taper(16, 4.0, 0.1, 0.1)), fill=pal["light"], op=0.9)
    # back spike
    sp = [(4, -7), (18, -1), (4, 5)]
    d.shape(poly(sp), fill=d.lin([(0, pal["light"]), (1, pal["dark"])], 4, -7, 4, 5), ow=2.2)
    # socket
    d.shape(rrect_path(-5, -12, 10, 20, 2), fill=d.lin([(0, "#6a6e76"), (1, "#23262c")], -5, 0, 5, 0), ow=2)
    for yy in (-8, 4):
        d.circle(0, yy, 1.4, fill=GOLD["light"])


def spear_head(d: Doc, L=30, W=12, pal=STEEL):
    pts = [(-W * 0.22, 0), (-W / 2, -L * 0.35), (0, -L), (W / 2, -L * 0.35), (W * 0.22, 0)]
    dd = smooth(pts, tension=0.55)
    d.path(dd, stroke=OUTLINE, sw=4.4)
    d.path(dd, fill=d.lin([(0, pal["light"]), (0.48, lt(pal["base"], 0.3)), (0.52, pal["base"]), (1, pal["dark"])], -W / 2, 0, W / 2, 0))
    d.path(f"M0,-2 L0,{f(-L * 0.85)}", stroke=pal["dark"], sw=1.0, op=0.7)
    d.shape(rrect_path(-W * 0.24, -1, W * 0.48, 8, 1.5), fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], -3, 0, 3, 0), ow=1.8)


def spear(d: Doc, H=100, pal=STEEL, W=5, head_w=12):
    haft(d, 0, H * 0.72, W=W, pal=WOOD, bands=((H * 0.36, 5, LEATHER), (H * 0.68, 4, BRONZE)))
    spear_head(d, L=H * 0.3, W=head_w, pal=pal)
    # tassel
    for i, a in enumerate((-0.35, 0.0, 0.35)):
        p = [(0, 8), (math.sin(a) * 6 - 2, 14), (math.sin(a) * 8 - 3, 22)]
        d.path(ribbon(qbez(*p, n=10), taper(10, 3.2, 0.9, 0.2, peak=0.2)), fill=CRIMSON["base"] if i != 1 else CRIMSON["light"], stroke=OUTLINE, stroke_width=0.8)


def crystal(d: Doc, cx, cy, r, pal, sides=6, stretch=1.6, glow=True):
    pts = [(cx, cy - r * stretch), (cx + r * 0.8, cy - r * 0.45), (cx + r * 0.75, cy + r * 0.55), (cx, cy + r * stretch * 0.8),
           (cx - r * 0.75, cy + r * 0.55), (cx - r * 0.8, cy - r * 0.45)]
    if glow:
        d.glow(cx, cy, r * 3.2, pal["glow"], 0.7)
    faceted(d, pts, (cx - r * 0.15, cy - r * 0.2), pal["dark"], pal["light"], ow=2.0)
    d.path(poly([(cx, cy - r * stretch), (cx - r * 0.2, cy), (cx, cy + r * stretch * 0.8)], closed=False), stroke="#ffffff", sw=0.8, op=0.6)
    d.sparkle(cx - r * 0.35, cy - r * 0.55, r * 0.7, "#ffffff", 0.9)


def staff(d: Doc, H=100, pal=ARCANE, wood=WOOD, thick=6.0, crystal_r=7.5):
    """Origin at the top crystal centre; shaft runs down."""
    # gnarled shaft as a wavy ribbon
    sp = bez((0, 6), (5, H * 0.3), (-5, H * 0.6), (1, H), n=24)
    dd = ribbon(sp, taper(24, thick, 1.1, 0.7, peak=0.1))
    d.path(dd, stroke=OUTLINE, sw=4.2)
    d.path(dd, fill=d.lin([(0, wood["light"]), (0.5, wood["base"]), (1, wood["dark"])], -4, 0, 4, 0))
    d.path(smooth([(p[0] - 1.2, p[1]) for p in sp[2:-2:3]], closed=False), stroke=wood["light"], sw=0.8, op=0.6)
    for yy in (H * 0.35, H * 0.38):
        d.path(f"M-3.5,{f(yy)} L3.5,{f(yy + 1)}", stroke=GOLD["base"], sw=1.6)
    # claw prongs holding the crystal
    for sx in (-1, 1):
        pr = bez((sx * 2, 12), (sx * 12, 8), (sx * 12, -6), (sx * 4, -14), n=14)
        pd = ribbon(pr, taper(14, 4.0, 1.0, 0.15, peak=0.05))
        d.path(pd, stroke=OUTLINE, sw=3.6)
        d.path(pd, fill=d.lin([(0, wood["light"]), (1, wood["dark"])], -10, 0, 10, 0))
    crystal(d, 0, 0, crystal_r, pal)


def wand(d: Doc, H=60, pal=ARCANE, thick=1.0):
    sp = [(0, 4), (0, H)]
    dd = ribbon(sp, [3.2 * thick, 5.0 * thick])
    d.path(dd, stroke=OUTLINE, sw=4)
    d.path(dd, fill=d.lin([(0, "#3a2a4a"), (0.5, "#1a1026"), (1, "#0a0610")], -3, 0, 3, 0))
    for yy in (H * 0.55, H * 0.62, H * 0.69):
        d.path(f"M-2.6,{f(yy)} L2.6,{f(yy)}", stroke=GOLD["base"], sw=1.4)
    d.shape(rrect_path(-3.5, 2, 7, 5, 1.5), fill=d.lin([(0, GOLD["light"]), (1, GOLD["dark"])], -3, 0, 3, 0), ow=1.6)
    crystal(d, 0, -3, 4.2, pal, stretch=1.7)


def bow(d: Doc, H=96, pal=WOOD, limb=6.5):
    """Vertical recurve bow, grip at origin, belly facing -x (string on the right)."""
    top = bez((0, 0), (-16, -14), (-12, -H * 0.42), (2, -H / 2), n=20)
    bot = [(x, -y) for x, y in top]
    for limb_pts in (top, bot):
        dd = ribbon(limb_pts, taper(20, limb, 1.0, 0.25, peak=0.0))
        d.path(dd, stroke=OUTLINE, sw=4.2)
        d.path(dd, fill=d.lin([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], -14, 0, 0, 0))
        d.path(smooth([(x - 1.4, y) for x, y in limb_pts[1:-2:2]], closed=False), stroke=GOLD["light"], sw=0.7, op=0.5)
    # string
    d.path(f"M2,{f(-H / 2)} L2,{f(H / 2)}", stroke="#e8e0cc", sw=1.1)
    # grip wrap
    d.shape(rrect_path(-4, -7, 8, 14, 2), fill=d.lin([(0, CRIMSON["light"]), (1, CRIMSON["dark"])], -4, 0, 4, 0), ow=1.6)
    for yy in (-4, 0, 4):
        d.path(f"M-4,{yy} L4,{yy + 1.5}", stroke=CRIMSON["dark"], sw=0.8)
    for s in (-1, 1):
        d.circle(2, s * H / 2, 2.0, fill=GOLD["base"], stroke=OUTLINE, stroke_width=1)


def arrow(d: Doc, L=70, pal=STEEL, fletch=CRIMSON):
    """Arrow pointing -y, nock at origin."""
    d.path(f"M0,0 L0,{-L + 8}", stroke=OUTLINE, sw=4.2)
    d.path(f"M0,0 L0,{-L + 8}", stroke=WOOD["light"], sw=1.8)
    head = [(0, -L), (4.5, -L + 10), (0, -L + 7.5), (-4.5, -L + 10)]
    d.shape(poly(head), fill=d.lin([(0, pal["light"]), (1, pal["dark"])], -4, 0, 4, 0), ow=1.8)
    for s in (-1, 1):
        fl = [(0, -2), (s * 5, 0), (s * 5, -12), (0, -16)]
        d.shape(poly(fl), fill=fletch["base"] if s < 0 else fletch["light"], ow=1.4)


# --------------------------------------------------------------------------------------------
# shields / armour
# --------------------------------------------------------------------------------------------

def heater_pts(w=60, h=70):
    top = -h * 0.42
    return [(-w / 2, top), (-w * 0.25, top - 3), (0, top - 4), (w * 0.25, top - 3), (w / 2, top), (w / 2, top + h * 0.3),
            (w * 0.4, top + h * 0.62), (w * 0.2, top + h * 0.86), (0, top + h), (-w * 0.2, top + h * 0.86),
            (-w * 0.4, top + h * 0.62), (-w / 2, top + h * 0.3)]


def heater_shield(d: Doc, w=60, h=70, field=CRIMSON, rim=STEEL, emblem="cross", boss=GOLD, ow=2.6):
    pts = heater_pts(w, h)
    outer = smooth(pts, tension=0.55)
    d.path(outer, stroke=OUTLINE, sw=ow * 2)
    d.path(outer, fill=d.lin([(0, rim["light"]), (0.5, rim["base"]), (1, rim["dark"])], -w / 2, -h / 2, w / 2, h / 2))
    inner_pts = [(x * 0.84, y * 0.84 - 1) for x, y in pts]
    inner = smooth(inner_pts, tension=0.55)
    d.path(inner, fill=d.rad([(0, lt(field["base"], 0.15)), (0.6, field["base"]), (1, field["dark"])], -w * 0.15, -h * 0.2, w * 0.8))
    if emblem == "cross":
        cw = w * 0.13
        d.shape(poly([(-cw / 2, -h * 0.34), (cw / 2, -h * 0.34), (cw / 2, -h * 0.08), (w * 0.3, -h * 0.08), (w * 0.3, h * 0.04),
                      (cw / 2, h * 0.04), (cw / 2, h * 0.42), (-cw / 2, h * 0.42), (-cw / 2, h * 0.04), (-w * 0.3, h * 0.04),
                      (-w * 0.3, -h * 0.08), (-cw / 2, -h * 0.08)]),
                fill=d.lin([(0, boss["light"]), (0.5, boss["base"]), (1, boss["dark"])], -w * 0.3, -h * 0.3, w * 0.3, h * 0.3), ow=1.4)
    elif emblem == "boss":
        d.circle(0, -2, w * 0.14, fill=d.rad([(0, boss["light"]), (0.6, boss["base"]), (1, boss["dark"])], -2, -5, w * 0.18), stroke=OUTLINE, stroke_width=1.6)
    # right-side shade + top-left sheen
    shade = [(0, -h * 0.5)] + [p for p in pts if p[0] > 0] + [(0, h * 0.58)]
    d.path(smooth([(x, y) for x, y in pts if x >= 0] + [(0, h * 0.2)], tension=0.55), fill="#000000", op=0.18)
    d.path(smooth([(-w * 0.42, -h * 0.4), (-w * 0.1, -h * 0.44), (-w * 0.3, -h * 0.3), (-w * 0.42, -h * 0.05)], tension=0.6), fill="#ffffff", op=0.18)
    d.path(smooth(inner_pts, tension=0.55), stroke=dk(rim["dark"], 0.3), sw=1.0, op=0.8)
    # rivets
    for p in pts[::2]:
        x, y = p[0] * 0.92, p[1] * 0.92 - 0.5
        d.circle(x, y, 1.5, fill=rim["light"], stroke=OUTLINE, stroke_width=0.6)


def tower_shield(d: Doc, w=54, h=80, face=STEEL, band=GOLD, ow=2.6):
    pts = [(-w / 2, -h / 2 + 10), (-w * 0.3, -h / 2 + 2), (0, -h / 2), (w * 0.3, -h / 2 + 2), (w / 2, -h / 2 + 10), (w / 2, h / 2 - 12),
           (w * 0.3, h / 2 - 3), (0, h / 2), (-w * 0.3, h / 2 - 3), (-w / 2, h / 2 - 12)]
    dd = smooth(pts, tension=0.35)
    d.path(dd, stroke=OUTLINE, sw=ow * 2)
    d.path(dd, fill=d.lin([(0, face["light"]), (0.35, face["base"]), (0.75, dk(face["base"], 0.25)), (1, face["dark"])], -w / 2, 0, w / 2, 0))
    # vertical ridge + bands
    d.path(f"M0,{f(-h / 2 + 2)} L0,{f(h / 2 - 2)}", stroke=face["light"], sw=2.2, op=0.7)
    d.path(f"M1.6,{f(-h / 2 + 2)} L1.6,{f(h / 2 - 2)}", stroke=face["dark"], sw=1.2, op=0.7)
    for yy in (-h * 0.26, h * 0.22):
        bd = poly([(-w / 2 + 1, yy - 3.5), (w / 2 - 1, yy - 3.5), (w / 2 - 1, yy + 3.5), (-w / 2 + 1, yy + 3.5)])
        d.path(bd, fill=d.lin([(0, band["light"]), (0.5, band["base"]), (1, band["dark"])], 0, yy - 3.5, 0, yy + 3.5), stroke=OUTLINE, stroke_width=1.2)
        for xx in (-w * 0.36, -w * 0.12, w * 0.12, w * 0.36):
            d.circle(xx, yy, 1.4, fill=band["light"], stroke=OUTLINE, stroke_width=0.5)
    d.path(smooth([(x * 0.9, y * 0.92) for x, y in pts], tension=0.35), stroke="#ffffff", sw=0.9, op=0.25)


def great_helm(d: Doc, w=44, h=52, pal=STEEL, trim=GOLD, horns=False, plume=None):
    if horns:
        for s in (-1, 1):
            hp = bez((s * w * 0.42, -h * 0.1), (s * w * 0.95, -h * 0.2), (s * w * 1.0, -h * 0.75), (s * w * 0.7, -h * 1.0), n=20)
            dd = ribbon(hp, taper(20, 11, 1.0, 0.05, peak=0.0))
            d.path(dd, stroke=OUTLINE, sw=4.4)
            d.path(dd, fill=d.lin([(0, BONE["light"]), (0.6, BONE["base"]), (1, BONE["dark"])], 0, -h, 0, 0))
            for i in range(3, 16, 3):
                x, y = hp[i]
                d.path(f"M{f(x - 3)},{f(y - 2)} L{f(x + 3)},{f(y + 2)}", stroke=BONE["dark"], sw=0.9, op=0.7)
    pts = [(-w / 2, h * 0.5), (-w / 2, -h * 0.15), (-w * 0.42, -h * 0.38), (-w * 0.2, -h * 0.5), (0, -h * 0.53), (w * 0.2, -h * 0.5),
           (w * 0.42, -h * 0.38), (w / 2, -h * 0.15), (w / 2, h * 0.5)]
    dd = smooth(pts, closed=False, tension=0.5) + " Z"
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, pal["light"]), (0.3, pal["base"]), (0.7, dk(pal["base"], 0.3)), (1, pal["dark"])], -w / 2, 0, w / 2, 0))
    d.path(smooth([(-w * 0.38, -h * 0.3), (-w * 0.2, -h * 0.44), (0, -h * 0.47)], closed=False), stroke="#ffffff", sw=1.6, op=0.45)
    # visor slits
    for yy in (-h * 0.02,):
        d.path(rrect_path(-w * 0.44, yy - 2.6, w * 0.88, 5.2, 2.4), fill="#07050a")
        d.path(f"M{f(-w * 0.4)},{f(yy + 3.3)} L{f(w * 0.4)},{f(yy + 3.3)}", stroke=pal["light"], sw=0.8, op=0.6)
    # cross reinforcement
    cp = poly([(-2.5, -h * 0.5), (2.5, -h * 0.5), (2.5, -h * 0.07), (-2.5, -h * 0.07)])
    d.path(cp, fill=d.lin([(0, trim["light"]), (1, trim["dark"])], -2.5, 0, 2.5, 0), stroke=OUTLINE, stroke_width=1)
    cp2 = poly([(-2.5, h * 0.05), (2.5, h * 0.05), (2.5, h * 0.48), (-2.5, h * 0.48)])
    d.path(cp2, fill=d.lin([(0, trim["light"]), (1, trim["dark"])], -2.5, 0, 2.5, 0), stroke=OUTLINE, stroke_width=1)
    for yy in (h * 0.15, h * 0.26, h * 0.37):
        for s in (-1, 1):
            d.path(rrect_path(s * w * 0.18 - 3, yy - 1, 6, 2.2, 1), fill="#07050a", op=0.9)
    d.path(f"M{f(-w / 2)},{f(h * 0.5)} L{f(w / 2)},{f(h * 0.5)}", stroke=trim["base"], sw=2.4)


def cuirass(d: Doc, w=60, h=62, pal=STEEL, trim=GOLD):
    body = [(-w * 0.2, -h * 0.5), (-w * 0.08, -h * 0.4), (w * 0.08, -h * 0.4), (w * 0.2, -h * 0.5), (w * 0.34, -h * 0.44),
            (w * 0.34, -h * 0.2), (w * 0.3, h * 0.12), (w * 0.26, h * 0.4), (w * 0.3, h * 0.5), (0, h * 0.56), (-w * 0.3, h * 0.5),
            (-w * 0.26, h * 0.4), (-w * 0.3, h * 0.12), (-w * 0.34, -h * 0.2), (-w * 0.34, -h * 0.44)]
    dd = smooth(body, tension=0.35)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, pal["light"]), (0.3, pal["base"]), (0.5, lt(pal["base"], 0.2)), (0.52, dk(pal["base"], 0.1)), (1, pal["dark"])], -w * 0.34, 0, w * 0.34, 0))
    # pectoral contour and ridge
    d.path(smooth([(-w * 0.28, -h * 0.05), (-w * 0.12, h * 0.02), (0, -h * 0.05), (w * 0.12, h * 0.02), (w * 0.28, -h * 0.05)], closed=False), stroke=pal["dark"], sw=1.4, op=0.8)
    d.path(f"M0,{f(-h * 0.38)} L0,{f(h * 0.52)}", stroke=pal["dark"], sw=1.2, op=0.6)
    d.path(f"M-1.2,{f(-h * 0.38)} L-1.2,{f(h * 0.5)}", stroke="#ffffff", sw=0.8, op=0.5)
    # faulds (waist lames)
    for i, yy in enumerate((h * 0.3, h * 0.42)):
        d.path(smooth([(-w * 0.28, yy), (0, yy + 4), (w * 0.28, yy)], closed=False), stroke=OUTLINE, sw=1.4)
        d.path(smooth([(-w * 0.28, yy - 1.2), (0, yy + 2.8), (w * 0.28, yy - 1.2)], closed=False), stroke=pal["light"], sw=0.8, op=0.5)
    # gold neck trim
    d.path(smooth([(-w * 0.2, -h * 0.48), (-w * 0.08, -h * 0.38), (w * 0.08, -h * 0.38), (w * 0.2, -h * 0.48)], closed=False), stroke=trim["base"], sw=2.4)
    # pauldrons
    for s in (-1, 1):
        pp = [(s * w * 0.18, -h * 0.5), (s * w * 0.42, -h * 0.52), (s * w * 0.52, -h * 0.34), (s * w * 0.5, -h * 0.12), (s * w * 0.36, -h * 0.16), (s * w * 0.3, -h * 0.34)]
        pd = smooth(pp, tension=0.6)
        d.path(pd, stroke=OUTLINE, sw=4.4)
        d.path(pd, fill=d.rad([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], s * w * 0.34 - 4, -h * 0.46, w * 0.3))
        d.path(smooth([(s * w * 0.28, -h * 0.4), (s * w * 0.42, -h * 0.44), (s * w * 0.49, -h * 0.3)], closed=False), stroke=trim["base"], sw=1.8)
    d.path(dd, fill="#000000", op=0.0)


# --------------------------------------------------------------------------------------------
# elemental motifs
# --------------------------------------------------------------------------------------------

def flame(d: Doc, cx, cy, s=1.0, pal=None, lean=0.0, tongues=True, core=True, glow=True):
    """Flame whose base sits around (cx, cy); height ~ 60*s."""
    pal = pal or EL["fire"]
    if glow:
        d.glow(cx, cy - 18 * s, 44 * s, pal["glow"], 0.55)
    outer = teardrop(cx, cy, 18 * s, 58 * s, lean * s, curl=6 * s)
    d.path(outer, stroke=OUTLINE, sw=3.6 * max(s, 0.6))
    d.path(outer, fill=d.lin([(0, pal["dark"]), (0.6, dk(pal["base"], 0.1)), (1, pal["dark"])], cx, cy - 58 * s, cx, cy + 18 * s))
    if tongues:
        for sx, hh, rr, ln in ((-1, 36, 9, -9), (1, 40, 9, 10)):
            d.path(teardrop(cx + sx * 11 * s, cy + 2 * s, rr * s, hh * s, ln * s, curl=sx * 3 * s), fill=pal["dark"])
            d.path(teardrop(cx + sx * 11 * s, cy + 3 * s, rr * 0.7 * s, hh * 0.8 * s, ln * s, curl=sx * 3 * s), fill=pal["base"], op=0.9)
    d.path(teardrop(cx, cy + 2 * s, 13.5 * s, 46 * s, lean * 0.8 * s, curl=4 * s), fill=d.lin([(0, pal["base"]), (1, lt(pal["base"], 0.25))], cx, cy - 44 * s, cx, cy + 14 * s))
    if core:
        d.path(teardrop(cx, cy + 5 * s, 9 * s, 30 * s, lean * 0.5 * s, curl=2 * s), fill=d.lin([(0, pal["light"]), (1, lt(pal["light"], 0.5))], cx, cy - 25 * s, cx, cy + 14 * s))
        d.path(teardrop(cx, cy + 8 * s, 5 * s, 16 * s, lean * 0.3 * s), fill="#fffbe8", op=0.9)


def ice_shard(d: Doc, L=30, W=10, pal=None, ow=2.0):
    """Shard pointing -y from origin (base)."""
    pal = pal or EL["ice"]
    tip = (0, -L)
    ls, rs = (-W / 2, -L * 0.35), (W / 2, -L * 0.35)
    lb, rb = (-W * 0.3, 0), (W * 0.3, 0)
    d.path(poly([tip, rs, rb, lb, ls]), stroke=OUTLINE, sw=ow * 2)
    d.path(poly([tip, (0, -L * 0.3), (0, 0), lb, ls]), fill=d.lin([(0, pal["light"]), (1, pal["base"])], 0, -L, 0, 0))
    d.path(poly([tip, rs, rb, (0, 0), (0, -L * 0.3)]), fill=d.lin([(0, pal["base"]), (1, pal["dark"])], 0, -L, 0, 0))
    d.path(poly([tip, (0, -L * 0.3), ls]), fill="#ffffff", op=0.45)
    d.path(f"M0,{f(-L)} L0,0", stroke="#ffffff", sw=0.6, op=0.6)


def snowflake(d: Doc, cx, cy, r, pal=None, width=4.0, glow=True):
    pal = pal or EL["ice"]
    if glow:
        d.glow(cx, cy, r * 1.5, pal["glow"], 0.55)
    arms = []
    for i in range(6):
        a = -math.pi / 2 + i * math.pi / 3
        p1 = polar(cx, cy, r, a)
        arms.append(f"M{f(cx)},{f(cy)} L{f(p1[0])},{f(p1[1])}")
        for k, bl in ((0.5, 0.32), (0.75, 0.22)):
            b0 = polar(cx, cy, r * k, a)
            for s in (-1, 1):
                b1 = polar(b0[0], b0[1], r * bl, a + s * 0.8)
                arms.append(f"M{f(b0[0])},{f(b0[1])} L{f(b1[0])},{f(b1[1])}")
    dd = " ".join(arms)
    d.path(dd, stroke=OUTLINE, sw=width + 3)
    d.path(dd, stroke=pal["base"], sw=width)
    d.path(dd, stroke=pal["light"], sw=width * 0.4)
    d.path(poly(ngon(cx, cy, r * 0.22, 6)), fill=pal["light"], stroke=OUTLINE, stroke_width=1)


def bolt(d: Doc, pts, width=7, pal=None, glow=True, core_color="#ffffff"):
    pal = pal or EL["lightning"]
    path = poly(pts, closed=False)
    if glow:
        d.path(path, stroke=pal["glow"], sw=width * 4.2, op=0.12)
        d.path(path, stroke=pal["glow"], sw=width * 2.6, op=0.22)
        d.path(path, stroke=pal["dark"], sw=width * 1.6, op=0.55)
    n = len(pts)
    dd = ribbon(pts, taper(n, width, 0.6, 0.15, peak=0.25))
    d.path(dd, stroke=OUTLINE, sw=1.4, op=0.8)
    d.path(dd, fill=pal["base"])
    d.path(ribbon(pts, taper(n, width * 0.45, 0.6, 0.1, peak=0.25)), fill=core_color)


def zig_bolt(d: Doc, cx, cy, h, pal=None, glow=True, lean=0.0):
    """Classic stylised lightning-bolt glyph centred on (cx, cy), height h."""
    pal = pal or EL["lightning"]
    w = h * 0.62
    norm = [(0.56, 0.0), (0.16, 0.54), (0.44, 0.54), (0.26, 1.0), (0.86, 0.40), (0.57, 0.40), (0.82, 0.0)]
    pts = [(cx + (x - 0.5) * w + (0.5 - y) * lean * h, cy + (y - 0.5) * h) for x, y in norm]
    if glow:
        d.glow(cx, cy, h * 0.75, pal["glow"], 0.6)
    d.path(poly(pts), stroke=OUTLINE, sw=max(3.0, h * 0.05))
    d.path(poly(pts), fill=d.lin([(0, pal["light"]), (0.45, pal["base"]), (1, mix(pal["base"], "#ff9a20", 0.45))], cx, cy - h / 2, cx, cy + h / 2))
    hl = [pts[0], pts[1], (pts[1][0] + w * 0.08, pts[1][1] - h * 0.02), (pts[0][0] + w * 0.08, pts[0][1] + h * 0.01)]
    d.path(poly(hl), fill="#ffffff", op=0.75)


def rock(d: Doc, cx, cy, r, pal=None, seed=1, n=8, jitter=0.22, sx=1.0, sy=1.0, ow=2.4, light_dir=(-0.6, -0.8), rot0=0.0):
    import random as _r
    pal = pal or EL["earth"]
    rng = _r.Random(seed)
    pts = blob(cx, cy, r, n, jitter, rng, rot0=rot0, sx=sx, sy=sy)
    faceted(d, pts, (cx - r * 0.2 * sx, cy - r * 0.25 * sy), pal["dark"], pal["light"], ow=ow, light_dir=light_dir)
    return pts


def swirl(d: Doc, cx, cy, r0, r1, a0, turns, width, color, op=1.0, n=40, outline=True, cw=True):
    pts = []
    for i in range(n):
        t = i / (n - 1)
        a = a0 + (1 if cw else -1) * turns * 2 * math.pi * t
        r = lerp(r0, r1, t)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    dd = ribbon(pts, taper(n, width, 0.05, 0.05, peak=0.55))
    if outline:
        d.path(dd, stroke=OUTLINE, sw=2.2, op=op)
    d.path(dd, fill=color, op=op)
    return pts


def gust(d: Doc, pts, width, color, op=1.0, outline=True, hl=None, peak=0.5, start=0.05, end=0.02):
    n = len(pts)
    dd = ribbon(pts, taper(n, width, start, end, peak=peak))
    if outline:
        d.path(dd, stroke=OUTLINE, sw=2.2, op=op)
    d.path(dd, fill=color, op=op)
    if hl:
        d.path(ribbon(pts, taper(n, width * 0.35, start, end, peak=peak)), fill=hl, op=op * 0.9)


def droplet(d: Doc, cx, cy, r, pal=None, ow=2.0):
    pal = pal or EL["water"]
    dd = teardrop(cx, cy, r, r * 2.4)
    d.path(dd, stroke=OUTLINE, sw=ow * 2)
    d.path(dd, fill=d.rad([(0, pal["light"]), (0.45, pal["base"]), (1, pal["dark"])], cx - r * 0.3, cy - r * 0.2, r * 1.8))
    d.path(teardrop(cx - r * 0.35, cy - r * 0.15, r * 0.25, r * 1.1, lean=r * 0.15), fill="#ffffff", op=0.7)


def wave(d: Doc, pal=None, s=1.0):
    """Big curling wave; local frame ~ x in [-50,50], y in [-45, 40]."""
    pal = pal or EL["water"]
    body = [(-52, 40), (-46, 8), (-30, -18), (-8, -38), (16, -44), (36, -38), (46, -24), (44, -10), (34, -4), (26, -12),
            (30, -22), (22, -28), (8, -22), (-2, -6), (4, 14), (22, 30), (52, 40)]
    pts = [(x * s, y * s) for x, y in body]
    dd = smooth(pts, tension=0.7)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, pal["light"]), (0.35, pal["base"]), (1, pal["dark"])], 0, -44 * s, 0, 40 * s))
    # inner curl shadow
    d.path(smooth([(p[0] * s, p[1] * s) for p in [(26, -12), (30, -22), (22, -28), (8, -22), (-2, -6), (4, 14), (14, 10), (12, -6), (18, -16)]], tension=0.7), fill=pal["dark"], op=0.55)
    # foam crest
    crest = [(p[0] * s, p[1] * s) for p in [(-40, -2), (-26, -24), (-6, -40), (16, -46), (36, -40), (46, -26), (42, -12)]]
    d.path(ribbon(smooth_pts(crest, 30), taper(30, 6.0 * s, 0.1, 0.4, peak=0.55)), fill="#eafcff", op=0.95)
    for (x, y, r) in ((40, -48, 3), (48, -40, 2.2), (28, -52, 2), (52, -30, 1.6), (18, -52, 1.4)):
        d.circle(x * s, y * s, r * s, fill="#eafcff", op=0.9)
    # streaks
    for k in range(3):
        yy = 10 + k * 9
        d.path(smooth([(-44 * s, (yy + 12) * s), (-24 * s, yy * s), (-8 * s, (yy + 4) * s)], closed=False), stroke=pal["light"], sw=1.4 * s, op=0.5)


def smooth_pts(pts, n=30):
    """Sample a Catmull-Rom open spline into n points."""
    out = []
    m = len(pts)
    segs = m - 1
    for i in range(n):
        t = i / (n - 1) * segs
        k = min(int(t), segs - 1)
        u = t - k
        p0 = pts[max(k - 1, 0)]
        p1 = pts[k]
        p2 = pts[k + 1]
        p3 = pts[min(k + 2, m - 1)]
        u2, u3 = u * u, u * u * u
        x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * u + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3)
        y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * u + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)
        out.append((x, y))
    return out


def sun(d: Doc, cx, cy, r, pal=None, rays=12, ray_len=1.9, glow=True):
    pal = pal or EL["light"]
    if glow:
        d.glow(cx, cy, r * 3.2, pal["glow"], 0.75, core="#ffffff")
    long_ = star_pts(cx, cy, rays, r * ray_len, r * 0.8, rot0=-math.pi / 2)
    d.path(poly(long_), stroke=OUTLINE, sw=3.4, op=0.8)
    d.path(poly(long_), fill=d.rad([(0, "#ffffff"), (0.5, pal["light"]), (1, pal["base"])], cx, cy, r * ray_len))
    short = star_pts(cx, cy, rays, r * 1.35, r * 0.8, rot0=-math.pi / 2 + math.pi / rays)
    d.path(poly(short), fill=pal["base"], op=0.9)
    d.circle(cx, cy, r, fill=d.rad([(0, "#ffffff"), (0.5, pal["light"]), (1, pal["base"])], cx - r * 0.3, cy - r * 0.3, r * 1.3), stroke=pal["dark"], stroke_width=1.4)


def void_orb(d: Doc, cx, cy, r, pal=None):
    pal = pal or EL["dark"]
    d.glow(cx, cy, r * 2.2, pal["glow"], 0.7)
    d.circle(cx, cy, r + 2.4, fill=OUTLINE)
    d.circle(cx, cy, r, fill=d.rad([(0, "#000000"), (0.6, pal["dark"]), (0.88, pal["base"]), (1, pal["light"])], cx, cy, r))
    d.path(smooth(arc_pts(cx, cy, r * 0.82, math.pi * 1.1, math.pi * 1.55, 6), closed=False), stroke=pal["light"], sw=1.6, op=0.7)


def tendril(d: Doc, pts, width, pal=None, op=1.0):
    pal = pal or EL["dark"]
    sp = smooth_pts(pts, 28)
    dd = ribbon(sp, taper(28, width, 1.0, 0.0, peak=0.0))
    d.path(dd, stroke=OUTLINE, sw=2.0, op=op)
    d.path(dd, fill=d.lin([(0, pal["dark"]), (1, pal["base"])], sp[0][0], sp[0][1], sp[-1][0], sp[-1][1]), op=op)
    d.path(ribbon(sp, taper(28, width * 0.3, 1.0, 0.0, peak=0.0)), fill=pal["light"], op=0.45 * op)


def gem(d: Doc, cx, cy, r, pal, sides=8, sparkle=True):
    outer = ngon(cx, cy, r, sides, rot0=-math.pi / 2 + math.pi / sides)
    inner = ngon(cx, cy - r * 0.08, r * 0.55, sides, rot0=-math.pi / 2 + math.pi / sides)
    d.path(poly(outer), stroke=OUTLINE, sw=3.2)
    for i in range(sides):
        a, b = outer[i], outer[(i + 1) % sides]
        ia, ib = inner[i], inner[(i + 1) % sides]
        mx, my = (a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cy
        m = math.hypot(mx, my) or 1
        t = ((-(mx * -0.6 + my * -0.8) / m) + 1) / 2
        d.path(poly([a, b, ib, ia]), fill=mix(pal["light"], pal["dark"], t), stroke=mix(pal["light"], pal["dark"], t), stroke_width=0.3)
    d.path(poly(inner), fill=d.lin([(0, pal["light"]), (1, pal["base"])], cx - r, cy - r, cx + r, cy + r))
    if sparkle:
        d.sparkle(cx - r * 0.3, cy - r * 0.35, r * 0.55, "#ffffff", 0.95)


def rune_ring(d: Doc, cx, cy, r, color, width=2.0, ticks=16, op=1.0, inner=True, seed=3):
    import random as _r
    rng = _r.Random(seed)
    d.circle(cx, cy, r, stroke=color, stroke_width=width, opacity=op)
    if inner:
        d.circle(cx, cy, r - width * 3.2, stroke=color, stroke_width=width * 0.5, opacity=op * 0.8)
    for i in range(ticks):
        a = i * 2 * math.pi / ticks
        r0, r1 = r - width * 2.6, r - width * 0.8
        kind = rng.randint(0, 2)
        p0 = polar(cx, cy, r0, a)
        p1 = polar(cx, cy, r1, a)
        if kind == 0:
            d.path(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}", stroke=color, sw=width * 0.6, op=op)
        elif kind == 1:
            pm = polar(cx, cy, (r0 + r1) / 2, a + 0.08)
            d.path(poly([p0, pm, p1], closed=False), stroke=color, sw=width * 0.5, op=op)
        else:
            pm = polar(cx, cy, (r0 + r1) / 2, a)
            d.circle(pm[0], pm[1], width * 0.45, fill=color, opacity=op)


def motes(d: Doc, pts, color, glow_color=None, size=2.0, op=1.0, diamonds=True):
    for i, (x, y, s) in enumerate(pts):
        r = size * s
        if glow_color:
            d.circle(x, y, r * 2.4, fill=glow_color, opacity=0.18 * op)
        if diamonds:
            d.path(poly([(x, y - r * 1.3), (x + r, y), (x, y + r * 1.3), (x - r, y)]), fill=color, op=op)
        else:
            d.circle(x, y, r, fill=color, opacity=op)


def slash_arc(d: Doc, cx, cy, r, a0, a1, width, pal, n=40, glow=True):
    """Crescent sword-sweep trail: thick in the middle/leading end, tapering."""
    pts = arc_pts(cx, cy, r, a0, a1, n)
    ws = taper(n, width, 0.0, 0.25, peak=0.72, power=0.8)
    if glow:
        d.path(ribbon(pts, [w * 2.2 for w in ws]), fill=pal["glow"], op=0.15)
        d.path(ribbon(pts, [w * 1.5 for w in ws]), fill=pal["glow"], op=0.22)
    dd = ribbon(pts, ws)
    d.path(dd, fill=d.lin([(0, pal["dark"], 0.0), (0.5, pal["base"]), (1, pal["light"])], *pts[0], *pts[-1]))
    inner = arc_pts(cx, cy, r + width * 0.18, a0, a1, n)
    d.path(ribbon(inner, [w * 0.35 for w in ws]), fill="#ffffff", op=0.85)


def humanoid_robed(d: Doc, fill, op=1.0, outline=True):
    """Hooded robed figure, feet at y=0, height ~ 80, centred x=0."""
    pts = [(0, -80), (7, -74), (10, -64), (9, -58), (16, -55), (22, -46), (24, -30), (21, -20), (17, -24), (18, -8), (22, 0),
           (-22, 0), (-18, -8), (-17, -24), (-21, -20), (-24, -30), (-22, -46), (-16, -55), (-9, -58), (-10, -64), (-7, -74)]
    dd = smooth(pts, tension=0.45)
    if outline:
        d.path(dd, stroke=OUTLINE, sw=4.4, op=op)
    d.path(dd, fill=fill, op=op)
    return dd


def fist(d: Doc, pal=STEEL, trim=GOLD, plated=True):
    """Front view clenched gauntlet, local ~ x[-24,24] y[-30,34]."""
    # cuff
    cuff = [(-18, 14), (18, 14), (22, 34), (-22, 34)]
    d.shape(poly(cuff), fill=d.lin([(0, pal["light"]), (0.4, pal["base"]), (1, pal["dark"])], -22, 0, 22, 0), ow=2.4)
    d.path(f"M-20,20 L20,20", stroke=trim["base"], sw=2.2)
    d.path(f"M-21,28 L21,28", stroke=pal["dark"], sw=1.2)
    # back of hand
    back = [(-22, -12), (22, -12), (20, 16), (-20, 16)]
    d.shape(smooth(back, tension=0.3), fill=d.lin([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], -22, 0, 22, 0), ow=2.4)
    # four knuckle rolls
    for i in range(4):
        x = -16.5 + i * 11
        y = -18 + (0 if i in (1, 2) else 2)
        k = rrect_path(x - 5.5, y - 12, 11, 20, 5)
        d.shape(k, fill=d.lin([(0, pal["light"]), (0.55, pal["base"]), (1, pal["dark"])], x - 5, y - 12, x + 5, y + 8), ow=2.0)
        if plated:
            d.path(f"M{f(x - 4.5)},{f(y - 3)} L{f(x + 4.5)},{f(y - 3)}", stroke=pal["dark"], sw=1.0)
            d.circle(x, y - 7, 1.3, fill=trim["light"])
    # thumb across
    th = [(-24, 2), (-10, 0), (6, 2), (8, 8), (-6, 10), (-22, 12)]
    d.shape(smooth(th, tension=0.5), fill=d.lin([(0, pal["light"]), (1, pal["dark"])], 0, 0, 0, 12), ow=2.0)
    if plated:
        d.path("M-8,1.5 L-8,10", stroke=pal["dark"], sw=0.9)
    d.path(smooth([(-20, -26), (-4, -30), (18, -26)], closed=False), stroke="#ffffff", sw=1.2, op=0.35)


def horn(d: Doc, pal=BONE, band=GOLD):
    """War horn curving from mouthpiece (left) to bell (right), local ~ x[-40,40]."""
    c = bez((-40, 20), (-24, 30), (10, 22), (30, -10), n=30)
    ws = [lerp(4, 30, (i / 29) ** 1.6) for i in range(30)]
    dd = ribbon(c, ws)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, pal["light"]), (0.5, pal["base"]), (1, pal["dark"])], 0, -10, 10, 30))
    for t in (8, 15, 22):
        l, r = ribbon_pts(c, ws)[t], ribbon_pts(c, ws)[len(c) * 2 - 1 - t]
        d.path(f"M{f(l[0])},{f(l[1])} L{f(r[0])},{f(r[1])}", stroke=band["base"], sw=2.8)
        d.path(f"M{f(l[0])},{f(l[1])} L{f(r[0])},{f(r[1])}", stroke=band["light"], sw=0.9)
    # bell opening
    end = c[-1]
    prev = c[-2]
    ang = math.degrees(math.atan2(end[1] - prev[1], end[0] - prev[0]))
    with d.g(T(end[0], end[1], ang)):
        d.ellipse(0, 0, 5, 15.5, fill=d.lin([(0, band["light"]), (1, band["dark"])], 0, -15, 0, 15), stroke=OUTLINE, stroke_width=2)
        d.ellipse(1, 0, 3, 12, fill="#140a06")
    # mouthpiece
    d.circle(-41, 20, 3, fill=band["base"], stroke=OUTLINE, stroke_width=1.4)


def banner(d: Doc, field=CRIMSON, trim=GOLD, pole=WOOD, emblem=True):
    """War banner on pole; local ~ x[-34,34] y[-50,50]."""
    haft(d, -44, 50, W=4.5, pal=pole)
    d.circle(0, -47, 4, fill=d.rad([(0, trim["light"]), (1, trim["dark"])], -1, -48, 5), stroke=OUTLINE, stroke_width=1.4)
    d.path("M-26,-38 L26,-38", stroke=OUTLINE, sw=5)
    d.path("M-26,-38 L26,-38", stroke=trim["base"], sw=2.4)
    cloth = [(-24, -38), (24, -38), (26, -8), (22, 22), (12, 12), (0, 30), (-12, 12), (-22, 22), (-26, -8)]
    dd = smooth(cloth, tension=0.25)
    d.path(dd, stroke=OUTLINE, sw=5)
    d.path(dd, fill=d.lin([(0, field["light"]), (0.3, field["base"]), (0.7, field["base"]), (1, field["dark"])], -26, 0, 26, 0))
    for x in (-10, 8):
        d.path(smooth([(x, -36), (x + 2, -10), (x - 1, 14)], closed=False), stroke=field["dark"], sw=2.2, op=0.55)
    d.path(smooth([(x * 0.86, (y + 38) * 0.88 - 38 + 1.5) for x, y in cloth], tension=0.25), stroke=trim["base"], sw=1.6)
    if emblem:
        # gold chevron + star
        d.shape(poly([(-12, -8), (0, -20), (12, -8), (12, -1), (0, -13), (-12, -1)]), fill=d.lin([(0, trim["light"]), (1, trim["dark"])], 0, -20, 0, 0), ow=1.4)
        d.shape(poly(star_pts(0, 5, 5, 6.5, 2.8)), fill=trim["light"], ow=1.2)


def heart(d: Doc, cx, cy, s, pal, ow=2.6):
    pts = f"M{f(cx)},{f(cy + 30 * s)} C{f(cx - 10 * s)},{f(cy + 20 * s)} {f(cx - 34 * s)},{f(cy + 4 * s)} {f(cx - 32 * s)},{f(cy - 12 * s)} " \
          f"C{f(cx - 30 * s)},{f(cy - 30 * s)} {f(cx - 8 * s)},{f(cy - 30 * s)} {f(cx)},{f(cy - 14 * s)} " \
          f"C{f(cx + 8 * s)},{f(cy - 30 * s)} {f(cx + 30 * s)},{f(cy - 30 * s)} {f(cx + 32 * s)},{f(cy - 12 * s)} " \
          f"C{f(cx + 34 * s)},{f(cy + 4 * s)} {f(cx + 10 * s)},{f(cy + 20 * s)} {f(cx)},{f(cy + 30 * s)} Z"
    d.path(pts, stroke=OUTLINE, sw=ow * 2)
    d.path(pts, fill=d.rad([(0, pal["light"]), (0.45, pal["base"]), (1, pal["dark"])], cx - 12 * s, cy - 10 * s, 44 * s))
    d.path(smooth([(cx - 24 * s, cy - 10 * s), (cx - 20 * s, cy - 20 * s), (cx - 10 * s, cy - 21 * s)], closed=False), stroke="#ffffff", sw=3 * s, op=0.55)
    return pts


def hourglass(d: Doc, cx, cy, s, frame=GOLD, sand=None):
    sand = sand or EL["earth"]
    w, h = 20 * s, 30 * s
    glass = [(cx - w, cy - h), (cx + w, cy - h), (cx + w * 0.9, cy - h * 0.6), (cx + 3 * s, cy - 2 * s), (cx + 3 * s, cy + 2 * s),
             (cx + w * 0.9, cy + h * 0.6), (cx + w, cy + h), (cx - w, cy + h), (cx - w * 0.9, cy + h * 0.6), (cx - 3 * s, cy + 2 * s),
             (cx - 3 * s, cy - 2 * s), (cx - w * 0.9, cy - h * 0.6)]
    gd = smooth(glass, tension=0.4)
    d.path(gd, stroke=OUTLINE, sw=4)
    d.path(gd, fill="#bfe6f0", op=0.25)
    # sand top (lower half of top bulb) and bottom pile
    d.path(poly([(cx - w * 0.72, cy - h * 0.45), (cx + w * 0.72, cy - h * 0.45), (cx + 2 * s, cy - 2 * s), (cx - 2 * s, cy - 2 * s)]), fill=sand["light"])
    d.path(f"M{f(cx)},{f(cy - 2 * s)} L{f(cx)},{f(cy + h * 0.8)}", stroke=sand["light"], sw=1.4 * s)
    d.path(smooth([(cx - w * 0.9, cy + h * 0.95), (cx, cy + h * 0.45), (cx + w * 0.9, cy + h * 0.95)], tension=0.6), fill=sand["base"])
    d.path(smooth([(cx - w * 0.6, cy - h * 0.85), (cx - w * 0.75, cy - h * 0.62)], closed=False), stroke="#ffffff", sw=1.6 * s, op=0.6)
    for yy in (cy - h - 3 * s, cy + h + 3 * s):
        bd = rrect_path(cx - w - 5 * s, yy - 3.5 * s, (w + 5 * s) * 2, 7 * s, 2 * s)
        d.path(bd, stroke=OUTLINE, sw=3.6)
        d.path(bd, fill=d.lin([(0, frame["light"]), (1, frame["dark"])], 0, yy - 3.5 * s, 0, yy + 3.5 * s))
    for sx in (-1, 1):
        d.path(f"M{f(cx + sx * (w + 2 * s))},{f(cy - h - 1 * s)} L{f(cx + sx * (w + 2 * s))},{f(cy + h + 1 * s)}", stroke=OUTLINE, sw=5 * s)
        d.path(f"M{f(cx + sx * (w + 2 * s))},{f(cy - h - 1 * s)} L{f(cx + sx * (w + 2 * s))},{f(cy + h + 1 * s)}", stroke=frame["base"], sw=2.6 * s)


def impact_star(d: Doc, cx, cy, r, color="#ffffff", glow_color="#ffd070", n=8, inner=0.28, rot0=0.0):
    d.glow(cx, cy, r * 1.6, glow_color, 0.7)
    pts = star_pts(cx, cy, n, r, r * inner, rot0=rot0)
    d.path(poly(pts), fill=glow_color, op=0.9)
    pts2 = star_pts(cx, cy, n, r * 0.62, r * inner * 0.6, rot0=rot0)
    d.path(poly(pts2), fill=color)


def eye(d: Doc, cx, cy, w, h, iris, pupil="#07030a", white="#f2e8ff", ow=2.4):
    dd = f"M{f(cx - w)},{f(cy)} Q{f(cx)},{f(cy - h * 2)} {f(cx + w)},{f(cy)} Q{f(cx)},{f(cy + h * 2)} {f(cx - w)},{f(cy)} Z"
    d.path(dd, stroke=OUTLINE, sw=ow * 2)
    d.path(dd, fill=white)
    d.circle(cx, cy, h * 0.85, fill=d.rad([(0, iris["light"]), (0.6, iris["base"]), (1, iris["dark"])], cx, cy, h * 0.9))
    d.ellipse(cx, cy, h * 0.22, h * 0.62, fill=pupil)
    d.circle(cx - h * 0.3, cy - h * 0.35, h * 0.16, fill="#ffffff", opacity=0.9)


def skull(d: Doc, cx, cy, s, pal=BONE, eye_glow=None):
    top = [(cx - 22 * s, cy + 2 * s), (cx - 24 * s, cy - 14 * s), (cx - 14 * s, cy - 28 * s), (cx, cy - 31 * s), (cx + 14 * s, cy - 28 * s),
           (cx + 24 * s, cy - 14 * s), (cx + 22 * s, cy + 2 * s), (cx + 16 * s, cy + 10 * s), (cx + 14 * s, cy + 20 * s),
           (cx - 14 * s, cy + 20 * s), (cx - 16 * s, cy + 10 * s)]
    dd = smooth(top, tension=0.5)
    d.path(dd, stroke=OUTLINE, sw=5 * s)
    d.path(dd, fill=d.rad([(0, pal["light"]), (0.6, pal["base"]), (1, pal["dark"])], cx - 6 * s, cy - 14 * s, 40 * s))
    for sx in (-1, 1):
        ey = smooth([(cx + sx * 4 * s, cy - 4 * s), (cx + sx * 14 * s, cy - 8 * s), (cx + sx * 17 * s, cy + 1 * s), (cx + sx * 9 * s, cy + 5 * s)], tension=0.6)
        d.path(ey, fill="#0a0410")
        if eye_glow:
            d.glow(cx + sx * 10 * s, cy - 1 * s, 9 * s, eye_glow, 0.9)
            d.circle(cx + sx * 10 * s, cy - 1 * s, 2.2 * s, fill=lt(eye_glow, 0.5))
    d.path(poly([(cx, cy + 5 * s), (cx - 3.5 * s, cy + 12 * s), (cx + 3.5 * s, cy + 12 * s)]), fill="#0a0410")
    for i in range(5):
        x = cx - 9 * s + i * 4.5 * s
        d.path(f"M{f(x)},{f(cy + 15 * s)} L{f(x)},{f(cy + 21 * s)}", stroke="#0a0410", sw=1.4 * s)
