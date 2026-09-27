"""Backgrounds and frames for the icon families."""
from __future__ import annotations

import math

from bh_svg import Doc, OUTLINE, GOLD, STEEL, ARCANE, CRIMSON, f, poly, mix, lt, dk, rrect_path, circle_path, ngon, star_pts, polar

KNIGHT_METAL = dict(dark="#4a3010", base="#b88a3a", light="#ffe2a0")
MAGE_METAL = dict(dark="#2a2050", base="#8c80c8", light="#ece4ff")


def backdrop(d: Doc, inner: str, outer: str = "#040208", haze=None, haze2=None, cy=58):
    """Full-bleed painted background: radial tint + soft haze blotches."""
    d.rect(0, 0, 128, 128, fill=d.rad([(0, inner), (0.55, mix(inner, outer, 0.55)), (1, outer)], 64, cy, 92))
    rng = d.rng
    for col, n in ((haze, 3), (haze2, 2)):
        if not col:
            continue
        for _ in range(n):
            x, y, r = rng.uniform(20, 108), rng.uniform(20, 108), rng.uniform(26, 48)
            d.circle(x, y, r, fill=d.rad([(0, col, 0.22), (1, col, 0)], x, y, r))
    # faint diagonal brush grain
    for i in range(7):
        y = rng.uniform(-20, 130)
        d.path(f"M-10,{f(y)} L140,{f(y - 60 + rng.uniform(-10, 10))}", stroke="#ffffff", sw=rng.uniform(4, 10), op=0.018)


def vignette(d: Doc, strength=0.78, cy=62):
    d.rect(0, 0, 128, 128, fill=d.rad([(0, "#000000", 0), (0.58, "#000000", 0), (0.85, "#000000", strength * 0.55), (1, "#000000", strength)], 64, cy, 92))


def skill_frame(d: Doc, metal=KNIGHT_METAL):
    """Square framed bezel for active skills."""
    # outer dark rim
    d.path("M0,0 L128,0 L128,128 L0,128 Z M4,4 L4,124 L124,124 L124,4 Z", fill="#050307", fill_rule="evenodd")
    # bevel ring (light top-left -> dark bottom-right)
    bev = d.lin([(0, metal["light"]), (0.35, metal["base"]), (0.7, metal["dark"]), (1, dk(metal["dark"], 0.4))], 0, 0, 128, 128)
    d.path(rrect_path(5, 5, 118, 118, 5), stroke=bev, sw=3.2)
    d.path(rrect_path(8.2, 8.2, 111.6, 111.6, 3.5), stroke="#000000", sw=1.2, op=0.8)
    d.path(rrect_path(9.4, 9.4, 109.2, 109.2, 3), stroke=metal["light"], sw=0.6, op=0.35)
    # corner studs
    for (x, y) in ((6.5, 6.5), (121.5, 6.5), (6.5, 121.5), (121.5, 121.5)):
        d.path(poly([(x, y - 5), (x + 5, y), (x, y + 5), (x - 5, y)]), fill=d.lin([(0, metal["light"]), (1, metal["dark"])], x - 4, y - 4, x + 4, y + 4), stroke="#000000", stroke_width=1.0)
        d.circle(x - 0.8, y - 0.8, 1.0, fill="#ffffff", opacity=0.7)


def talent_frame(d: Doc, metal=KNIGHT_METAL, kind="normal"):
    """Round bezel. kind: normal | keystone | minor."""
    r = 56 if kind != "minor" else 54
    # darken corners outside the ring
    d.path("M0,0 L128,0 L128,128 L0,128 Z " + circle_path(64, 64, r), fill="#000000", op=0.55, fill_rule="evenodd")
    d.path("M0,0 L128,0 L128,128 L0,128 Z M3,3 L3,125 L125,125 L125,3 Z", fill="#050307", fill_rule="evenodd")
    if kind == "keystone":
        # spiked gold star-ring behind the bezel
        sp = []
        for i in range(16):
            a = -math.pi / 2 + i * math.pi / 8
            r_ = (62.5 if (i // 2) % 2 == 0 else 80) if i % 2 == 0 else 53
            sp.append(polar(64, 64, r_, a))
        d.path(poly(sp), stroke="#000000", sw=3, op=0.9)
        d.path(poly(sp) + " " + circle_path(64, 64, 52), fill=d.lin([(0, metal["light"]), (0.5, metal["base"]), (1, metal["dark"])], 0, 0, 128, 128), fill_rule="evenodd")
        sp2 = [polar(64, 64, (59 if (i // 2) % 2 == 0 else 70) if i % 2 == 0 else 55, -math.pi / 2 + i * math.pi / 8) for i in range(16)]
        d.path(poly(sp2), stroke=metal["dark"], sw=1.2, op=0.7)
    bev = d.lin([(0, metal["light"]), (0.4, metal["base"]), (0.75, metal["dark"]), (1, dk(metal["dark"], 0.4))], 20, 10, 108, 118)
    w = {"normal": 4.4, "keystone": 6.0, "minor": 2.6}[kind]
    d.circle(64, 64, r, stroke="#000000", stroke_width=w + 3)
    d.circle(64, 64, r, stroke=bev, stroke_width=w)
    d.circle(64, 64, r - w / 2 - 1.2, stroke="#000000", stroke_width=1.2, opacity=0.8)
    d.circle(64, 64, r + w / 2 - 0.6, stroke=metal["light"], stroke_width=0.6, opacity=0.4)
    if kind == "keystone":
        for i in range(4):
            a = -math.pi / 2 + i * math.pi / 2
            x, y = polar(64, 64, r, a)
            d.path(poly([(x, y - 6), (x + 4.5, y), (x, y + 6), (x - 4.5, y)]), fill=d.lin([(0, "#ff9a9a"), (1, CRIMSON["dark"])], x - 4, y - 6, x + 4, y + 6), stroke="#000000", stroke_width=1.2)
            d.circle(x - 1, y - 1.8, 1.1, fill="#ffffff", opacity=0.8)
    elif kind == "normal":
        for i in range(4):
            a = -math.pi / 4 + i * math.pi / 2
            x, y = polar(64, 64, r, a)
            d.circle(x, y, 2.6, fill=d.rad([(0, metal["light"]), (1, metal["dark"])], x - 1, y - 1, 3.5), stroke="#000000", stroke_width=0.8)


def badge_bg(d: Doc, inner, rim, shape="rounded"):
    """Dark badge for status icons (rounded square) with coloured bevel rim."""
    if shape == "rounded":
        outer = rrect_path(2, 2, 124, 124, 18)
        d.path(outer, fill="#050307")
        d.path(rrect_path(6, 6, 116, 116, 15), fill=d.rad([(0, inner), (0.6, mix(inner, "#050307", 0.55)), (1, "#050307")], 64, 56, 84))


def badge_rim(d: Doc, rim):
    bev = d.lin([(0, lt(rim, 0.55)), (0.45, rim), (1, dk(rim, 0.6))], 0, 0, 128, 128)
    d.path(rrect_path(6, 6, 116, 116, 15), stroke=bev, sw=4)
    d.path(rrect_path(9.5, 9.5, 109, 109, 12), stroke="#000000", sw=1.2, op=0.7)
    d.path(rrect_path(3, 3, 122, 122, 18), stroke="#000000", sw=2)


def medallion_bg(d: Doc, inner, rim_metal=None, r=58):
    d.circle(64, 64, r + 3, fill="#050307")
    d.circle(64, 64, r, fill=d.rad([(0, inner), (0.65, mix(inner, "#050307", 0.6)), (1, "#050307")], 60, 54, r * 1.1))


def medallion_rim(d: Doc, rim_metal, r=58, w=5):
    bev = d.lin([(0, rim_metal["light"]), (0.45, rim_metal["base"]), (1, rim_metal["dark"])], 20, 10, 108, 118)
    d.circle(64, 64, r, stroke="#000000", stroke_width=w + 3)
    d.circle(64, 64, r, stroke=bev, stroke_width=w)
    d.circle(64, 64, r - w / 2 - 1, stroke="#000000", stroke_width=1.0, opacity=0.7)


def octagon_bg(d: Doc, inner, r=60):
    pts = ngon(64, 64, r, 8, rot0=-math.pi / 2 + math.pi / 8)
    d.path(poly(ngon(64, 64, r + 3.5, 8, rot0=-math.pi / 2 + math.pi / 8)), fill="#050307")
    d.path(poly(pts), fill=d.rad([(0, inner), (0.65, mix(inner, "#050307", 0.6)), (1, "#050307")], 60, 54, r * 1.1))


def octagon_rim(d: Doc, metal, r=60, w=4.6):
    bev = d.lin([(0, metal["light"]), (0.45, metal["base"]), (1, metal["dark"])], 20, 10, 108, 118)
    pts = ngon(64, 64, r, 8, rot0=-math.pi / 2 + math.pi / 8)
    d.path(poly(pts), stroke="#000000", sw=w + 3)
    d.path(poly(pts), stroke=bev, sw=w)
    d.path(poly(ngon(64, 64, r - w / 2 - 1.2, 8, rot0=-math.pi / 2 + math.pi / 8)), stroke="#000000", sw=1.0, op=0.7)


# ------------------------------------------------------------------------------------------ bh-010 additions (new styles only)

RANGER_METAL = dict(dark="#232410", base="#8a7c44", light="#e6dca2")      # weathered bronze
RANGER_ACCENT = dict(dark="#12301a", base="#3f7a3c", light="#a8d88a")     # green leather / moss
SHADOW_METAL = dict(dark="#07060b", base="#3e3a4c", light="#aaa4bc")      # blackened steel
SHADOW_ACCENT = dict(dark="#2a0a4a", base="#8a3ae0", light="#e2c4ff")     # violet
AURA_OFF_METAL = dict(dark="#4a120a", base="#c8703a", light="#ffe0a0")    # red-gold (offensive auras)
AURA_DEF_METAL = dict(dark="#1a2a44", base="#8aa4c8", light="#f2f8ff")    # blue-silver (defensive auras)


def skill_frame_accent(d: Doc, metal, accent):
    """skill_frame plus an accent: inner stitched leather band (ranger) or violet gem studs + hairline (shadowblade)."""
    skill_frame(d, metal)
    d.path(rrect_path(10.4, 10.4, 107.2, 107.2, 2.6), stroke=accent["base"], sw=1.0, op=0.75)
    # stitches along the inner band
    for i in range(12):
        t = 16 + i * 8.6
        for (x0, y0, x1, y1) in ((t, 11.2, t + 3.6, 11.2), (t, 116.8, t + 3.6, 116.8), (11.2, t, 11.2, t + 3.6), (116.8, t, 116.8, t + 3.6)):
            d.path(f"M{f(x0)},{f(y0)} L{f(x1)},{f(y1)}", stroke=accent["light"], sw=0.9, op=0.55)
    for (x, y) in ((6.5, 6.5), (121.5, 6.5), (6.5, 121.5), (121.5, 121.5)):
        d.circle(x, y, 2.4, fill=d.rad([(0, accent["light"]), (0.6, accent["base"]), (1, accent["dark"])], x - 0.8, y - 0.8, 3), stroke="#000000", stroke_width=0.7)
        d.circle(x - 0.7, y - 0.7, 0.7, fill="#ffffff", opacity=0.8)


def aura_frame(d: Doc, metal, glow):
    """Aura icons: pointy-top hexagonal bezel; the corners outside the hex carry faint radiant rays in the aura colour."""
    hexp = ngon(64, 64, 62, 6, rot0=-math.pi / 2)
    d.path("M0,0 L128,0 L128,128 L0,128 Z " + poly(hexp), fill="#050307", fill_rule="evenodd")
    for i in range(24):
        a = -math.pi / 2 + i * math.pi / 12 + math.pi / 24
        p0, p1 = polar(64, 64, 58, a - 0.035), polar(64, 64, 58, a + 0.035)
        p2 = polar(64, 64, 96, a)
        d.path(poly([p0, p2, p1]), fill=glow, op=0.22 if i % 2 == 0 else 0.12)
    bev = d.lin([(0, metal["light"]), (0.4, metal["base"]), (0.75, metal["dark"]), (1, dk(metal["dark"], 0.4))], 10, 4, 118, 124)
    d.path(poly(hexp), stroke="#000000", sw=8)
    d.path(poly(hexp), stroke=bev, sw=4.6)
    d.path(poly(ngon(64, 64, 58.6, 6, rot0=-math.pi / 2)), stroke="#000000", sw=1.2, op=0.8)
    d.path(poly(ngon(64, 64, 57.4, 6, rot0=-math.pi / 2)), stroke=metal["light"], sw=0.6, op=0.35)
    for (x, y) in hexp:
        d.glow(x, y, 7, glow, 0.7)
        d.path(poly([(x, y - 4.2), (x + 3.4, y), (x, y + 4.2), (x - 3.4, y)]), fill=d.lin([(0, "#ffffff"), (0.4, glow), (1, dk(glow, 0.5))], x - 3, y - 4, x + 3, y + 4), stroke="#000000", stroke_width=0.9)


def aura_halo(d: Doc, color, r=40, rays=True):
    """Glowing halo ring that marks every aura icon (drawn behind the emblem)."""
    d.circle(64, 64, r + 12, fill=d.rad([(0, color, 0), (0.62, color, 0), (0.78, color, 0.38), (0.86, color, 0.5), (1, color, 0)], 64, 64, r + 12))
    if rays:
        for i in range(32):
            a = i * math.pi / 16
            L = 9 if i % 2 == 0 else 5
            p0, p1 = polar(64, 64, r + 3, a), polar(64, 64, r + 3 + L, a)
            d.path(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}", stroke=lt(color, 0.3), sw=1.4, op=0.55)
    d.circle(64, 64, r, stroke="#000000", stroke_width=5, opacity=0.55)
    d.circle(64, 64, r, stroke=color, stroke_width=3.2)
    d.circle(64, 64, r, stroke=lt(color, 0.75), stroke_width=1.1)
    d.circle(64, 64, r - 5, stroke=color, stroke_width=0.8, opacity=0.55)


def passive_frame(d: Doc, metal, patina="#000000", r=52):
    """Passive medallion: coin-like disc with knurled thick rim and a bead ring; the field is muted by a patina wash."""
    d.circle(64, 64, r - 4, fill=d.rad([(0, patina, 0.10), (0.7, patina, 0.26), (1, patina, 0.55)], 58, 54, r))
    d.path("M0,0 L128,0 L128,128 L0,128 Z " + circle_path(64, 64, r + 2), fill="#050307", fill_rule="evenodd")
    d.path("M0,0 L128,0 L128,128 L0,128 Z M3,3 L3,125 L125,125 L125,3 Z", fill="#000000", fill_rule="evenodd")
    # soft corner filigree so the square slot is not empty
    for (x, y, sx, sy) in ((0, 0, 1, 1), (128, 0, -1, 1), (0, 128, 1, -1), (128, 128, -1, -1)):
        d.path(f"M{f(x + sx * 6)},{f(y + sy * 22)} Q{f(x + sx * 8)},{f(y + sy * 8)} {f(x + sx * 22)},{f(y + sy * 6)}", stroke=metal["base"], sw=1.4, op=0.55)
        d.circle(x + sx * 9, y + sy * 9, 1.8, fill=metal["base"], opacity=0.7)
    bev = d.lin([(0, metal["light"]), (0.45, metal["base"]), (0.8, metal["dark"]), (1, dk(metal["dark"], 0.4))], 20, 10, 108, 118)
    w = 8.0
    d.circle(64, 64, r, stroke="#000000", stroke_width=w + 3.4)
    d.circle(64, 64, r, stroke=bev, stroke_width=w)
    # knurling on the rim
    ticks = []
    for i in range(48):
        a = i * math.pi / 24
        p0, p1 = polar(64, 64, r - w / 2 + 0.6, a), polar(64, 64, r + w / 2 - 0.6, a)
        ticks.append(f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])}")
    d.path(" ".join(ticks), stroke=metal["dark"], sw=0.9, op=0.55)
    d.circle(64, 64, r - w / 2 - 0.8, stroke="#000000", stroke_width=1.4, opacity=0.85)
    d.circle(64, 64, r + w / 2 - 0.5, stroke=metal["light"], stroke_width=0.6, opacity=0.5)
    # bead ring engraved in the field
    for i in range(36):
        x, y = polar(64, 64, r - w / 2 - 4.2, i * math.pi / 18)
        d.circle(x, y, 0.9, fill=metal["light"], opacity=0.35)
    # engraved groove: dark lower-right, light upper-left
    d.path(circle_path(64, 64, r - w / 2 - 7.5), stroke=d.lin([(0, "#000000", 0.1), (1, "#000000", 0.55)], 30, 30, 98, 98), sw=1.4)
    d.path(circle_path(64, 64, r - w / 2 - 6.4), stroke=d.lin([(0, metal["light"], 0.45), (1, metal["light"], 0.0)], 30, 30, 98, 98), sw=0.7)
