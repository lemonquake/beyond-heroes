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
