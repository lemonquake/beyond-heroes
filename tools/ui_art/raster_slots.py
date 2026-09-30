"""slots/: inventory + equipment cells, slot glyphs, the ten rarity overlay frames, rarity glows, hotbar bezels."""
from __future__ import annotations

import math

import numpy as np

from rast import (Canvas, MAT, C, cov, sd_circle, sd_box, sd_rect, sd_chamfer_box, sd_poly, sd_stroke, union, sub, inter,
                  ring_of, shell, profile, metal, shade, groove_h, paint, gem, blur, spiral, arc, bez3, catmull, xf, star,
                  ngon, leaf, canvas_noise, fnoise, tint_mat, cmix, vgrad, hgrad, rgrad, desaturate, ramp, even_ramp, F)
from raster_orn import (corner_bastion, aether_channel, draw_part, inner_shadow, hammered, rune_band_sd, AETHER, AETHER_HI,
                        place, diag_mirror)
from raster_frames import stud, diamond

SLOTS = {}


def reg(name, use, margins=None, scale=0.5, **extra):
    def deco(fn):
        SLOTS[name] = (fn, dict(margins=margins, use=use, scale=scale, **extra))
        return fn
    return deco


# ------------------------------------------------------------------------------------------ inventory cells

def _cell(state):
    S = 128
    cv = Canvas(S, S)
    outer = sd_rect(cv, 4, 4, S - 4, S - 4, 10)
    inner = sd_rect(cv, 13, 13, S - 13, S - 13, 5)
    cv.shadow(cov(cv, outer), 0, 2, 3, 0.7)
    well_c = {"normal": ("#1d1714", "#0a0807"), "hover": ("#2c2119", "#0e0a08"), "selected": ("#16252a", "#070c0e"),
              "disabled": ("#151414", "#080808"), "locked": ("#100e0d", "#050404")}[state]
    cv.over(rgrad(cv, 64, 58, 70, [(0, well_c[0]), (1, well_c[1])]), cov(cv, outer), 0.92)
    inner_shadow(cv, inner, 18, op=0.85)
    rim_mat = {"normal": MAT["iron_warm"], "hover": MAT["bronze"], "selected": MAT["gold"], "disabled": MAT["iron"],
               "locked": MAT["iron"]}[state]
    if state == "selected":
        cv.over(AETHER, np.clip(1 + inner / 20, 0, 1) ** 2 * cov(cv, inner), 0.35)
    if state == "hover":
        cv.over("#ffb060", np.clip(1 + inner / 22, 0, 1) ** 2 * cov(cv, inner), 0.22)
    cv.put(metal(cv, sub(outer, inner), rim_mat, bevel=5, noise=canvas_noise(cv, 5, 2), noise_amt=0.05,
                 extra_h=hammered(cv, 9, 0.2)))
    paint(cv, np.abs(sd_rect(cv, 15.5, 15.5, S - 15.5, S - 15.5, 4)) - 0.5, "#000000", 0.7)
    # corner brackets
    bm = {"normal": "bronze", "hover": "gold", "selected": "gold", "disabled": "iron", "locked": "iron"}[state]
    for (ox, oy, sx, sy) in ((4, 4, 1, 1), (S - 4, 4, -1, 1), (4, S - 4, 1, -1), (S - 4, S - 4, -1, -1)):
        br = sd_stroke(cv, [(ox + sx * 3, oy + sy * 26), (ox + sx * 3, oy + sy * 3), (ox + sx * 26, oy + sy * 3)], 5.5)
        draw_part(cv, br, MAT[bm], bevel=2.6, shadow=(0.5, 1, 1, 0.6))
        diamond(cv, ox + sx * 4, oy + sy * 4, 4.5, mat="gold" if state in ("hover", "selected") else bm)
    if state == "selected":
        aether_channel(cv, np.abs(sd_rect(cv, 9, 9, S - 9, S - 9, 7)), core=0.8, glow_sigma=3, strength=0.9)
    if state == "locked":
        # padlock + chain
        for a, b in (((18, 30), (110, 98)), ((18, 98), (110, 30))):
            n = 7
            for i in range(n):
                t = (i + 0.5) / n
                x = a[0] + (b[0] - a[0]) * t
                y = a[1] + (b[1] - a[1]) * t
                ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
                link = ring_of(sd_poly(cv, xf([(-7, -3.5), (7, -3.5), (7, 3.5), (-7, 3.5)], x, y, ang if i % 2 else ang), margin=3), 2.4) \
                    if i % 2 == 0 else sd_stroke(cv, xf([(-5, 0), (5, 0)], x, y, ang), 2.6)
                draw_part(cv, link, MAT["iron"], bevel=1.3, shadow=(0.5, 1.2, 1.2, 0.8), bright=1.3)
        shk = ring_of(sd_rect(cv, 52, 40, 76, 72, 11), 5)
        shk = np.maximum(shk, cv.Y - 62 + 0 * shk)
        draw_part(cv, shk, MAT["steel"], bevel=2.5, shadow=(0.6, 1.5, 1.5, 0.8), bright=0.8)
        body = sd_rect(cv, 46, 58, 82, 88, 5)
        draw_part(cv, body, MAT["iron_warm"], bevel=4, shadow=(0.8, 2, 2, 0.9), bright=1.4)
        kh = union(sd_circle(cv, 64, 70, 3.4), sd_poly(cv, [(62, 71), (66, 71), (67.5, 80), (60.5, 80)], margin=2))
        paint(cv, kh, "#050303", 1.0)
        paint(cv, np.abs(sd_rect(cv, 48, 60, 80, 86, 4)) - 0.4, "#c09050", 0.5)
    if state == "disabled":
        desaturate(cv, 0.9, 0.7)
        cv.a *= 0.85
    return cv


for _st, _use in (("", "Inventory cell (128x128 at 2x -> 64 px). Dark well ~92% opaque; draw the item icon above it."),
                  ("_hover", "Inventory cell, hovered (warm inner light, gold corners)."),
                  ("_selected", "Inventory cell, selected / picked up (gold rim + aether channel)."),
                  ("_disabled", "Inventory cell, disabled (desaturated)."),
                  ("_locked", "Inventory cell, locked (chains + padlock).")):
    SLOTS["slot" + _st] = ((lambda s: (lambda: _cell(s or "normal")))(_st[1:]), dict(margins=None, use=_use, scale=0.5))


@reg("equip_slot", "Equipment paper-doll slot (160x160 at 2x -> 80 px). Draw a glyph_* overlay in it when empty.")
def equip_slot():
    S = 160
    cv = Canvas(S, S)
    outer = sd_chamfer_box(cv, 80, 80, 74, 74, 16)
    inner = sd_chamfer_box(cv, 80, 80, 60, 60, 10)
    cv.shadow(cov(cv, outer), 0, 3, 4, 0.8)
    cv.over(rgrad(cv, 80, 74, 86, [(0, "#221a15"), (1, "#080605")]), cov(cv, outer), 0.94)
    inner_shadow(cv, inner, 22, op=0.85)
    cv.put(metal(cv, sub(outer, inner), MAT["iron_warm"], bevel=7, extra_h=hammered(cv, 13, 0.3),
                 noise=canvas_noise(cv, 3, 2), noise_amt=0.05))
    ring = ring_of(sd_chamfer_box(cv, 80, 80, 64, 64, 12), 3.5)
    draw_part(cv, ring, MAT["bronze"], bevel=1.8, shadow=(0.5, 1, 1.2, 0.7))
    aether_channel(cv, np.abs(sd_chamfer_box(cv, 80, 80, 70, 70, 14)), core=0.7, glow_sigma=2.5, strength=0.65)
    for (ox, oy, sx, sy) in ((4, 4, 1, 1), (S - 4, 4, -1, 1), (4, S - 4, 1, -1), (S - 4, S - 4, -1, -1)):
        sds = []
        for pts in (catmull([(10, 26), (10, 10), (26, 10)], 4),):
            sds.append(sd_stroke(cv, place(pts, ox, oy, sx, sy), 6.5))
        for P in (spiral(40, 12, 6, 1.2, math.pi, math.pi * 2.7, 20), diag_mirror(spiral(40, 12, 6, 1.2, math.pi, math.pi * 2.7, 20))):
            sds.append(sd_stroke(cv, place(catmull([(24, 10), (34, 7)], 3) + P, ox, oy, sx, sy), 3.2, 1.2))
        sds.append(sd_poly(cv, place(leaf((14, 14), (32, 32), 8), ox, oy, sx, sy), margin=3))
        draw_part(cv, union(*sds), MAT["gold"], bevel=2.6, shadow=(0.8, 1.6, 1.8, 0.8))
        gx, gy = place([(11, 11)], ox, oy, sx, sy)[0]
        gem(cv, gx, gy, 5, MAT["aether"], glow=AETHER, glow_sigma=4, glow_str=0.5, setting="gold", setting_w=1.8)
    return cv


# ------------------------------------------------------------------------------------------ glyphs

PALE = dict(ramp=even_ramp(["#2a2420", "#6a5e50", "#a8987e", "#d8c8a8", "#f4e8cc"]), spec="#fff8e8", sp=0.2, pw=12)


def _glyph(shapes, strokes=(), holes=()):
    """Pale engraved silhouette: shapes/strokes unioned, then carved (sunken) into the surface."""
    S = 128
    cv = Canvas(S, S)
    sds = [sd_poly(cv, catmull(p, 5, closed=True) if smooth else p, margin=4) for p, smooth in shapes]
    sds += [sd_stroke(cv, p, w0, w1) for p, w0, w1 in strokes]
    sd = union(*sds)
    for p in holes:
        sd = sub(sd, sd_poly(cv, p, margin=3))
    h = -profile(sd, 3.0, "round") * 2.2
    rgb = shade(cv, h, PALE, flat_level=0.62)
    cv.over(rgb, cov(cv, sd), 0.55)
    paint(cv, np.abs(sd) - 0.5, "#fff4dc", 0.35)
    return cv


GLYPHS = {
    "main_weapon": lambda: _glyph([([(36, 88), (82, 30), (98, 22), (94, 38), (40, 92)], False),
                                   ([(26, 82), (34, 76), (52, 94), (46, 102)], False)],
                                  strokes=[([(40, 98), (26, 112)], 7, 7)]),
    "sub_weapon": lambda: _glyph([([(64, 18), (100, 28), (98, 66), (64, 110), (30, 66), (28, 28)], True)],
                                 holes=[[(60, 34), (68, 34), (68, 52), (84, 52), (84, 60), (68, 60), (68, 90), (60, 90), (60, 60), (44, 60), (44, 52), (60, 52)]]),
    "helm": lambda: _glyph([([(64, 16), (92, 26), (100, 56), (98, 104), (30, 104), (28, 56), (36, 26)], True)],
                           holes=[[(38, 56), (90, 56), (90, 63), (38, 63)], [(61, 63), (67, 63), (67, 94), (61, 94)]]),
    "inner_garment": lambda: _glyph([([(48, 20), (80, 20), (104, 32), (116, 62), (100, 68), (92, 50), (92, 108), (36, 108), (36, 50),
                                       (28, 68), (12, 62), (24, 32)], False)],
                                    holes=[[(56, 20), (72, 20), (64, 36)]]),
    "armor": lambda: _glyph([([(44, 24), (84, 24), (98, 30), (98, 70), (90, 106), (38, 106), (30, 70), (30, 30)], True),
                             ([(12, 44), (22, 24), (46, 22), (44, 48), (26, 56)], True),
                             ([(116, 44), (106, 24), (82, 22), (84, 48), (102, 56)], True)],
                            holes=[[(54, 24), (74, 24), (64, 40)], [(62, 48), (66, 48), (66, 96), (62, 96)]]),
    "gloves": lambda: _glyph([([(40, 60), (40, 34), (47, 30), (52, 34), (52, 56), (54, 24), (61, 20), (66, 24), (66, 54), (68, 26), (75, 23),
                                (80, 28), (78, 58), (82, 36), (89, 34), (92, 40), (90, 72), (104, 58), (110, 62), (96, 86), (86, 96),
                                (84, 114), (44, 114), (42, 90)], True)]),
    "boots": lambda: _glyph([([(40, 16), (78, 16), (80, 70), (110, 86), (114, 106), (34, 106), (36, 70)], True)],
                            holes=[[(40, 30), (78, 30), (78, 36), (40, 36)]]),
    # bh-024: a pair of trousers, waistband cut across the top
    "leggings": lambda: _glyph([([(36, 14), (92, 14), (97, 40), (94, 72), (90, 114), (70, 114), (66, 72), (64, 60), (62, 72), (58, 114),
                                  (38, 114), (34, 72), (31, 40)], False)],
                               holes=[[(36, 23), (92, 23), (92, 29), (36, 29)]]),
    "accessory": lambda: _glyph([],
                                strokes=[(arc(52, 50, 22, 0, 2 * math.pi, 48), 8, 8), (catmull([(70, 20), (96, 34), (100, 62)], 8), 3, 3)],
                                ) if False else _glyph_accessory(),
}


def _glyph_accessory():
    S = 128
    cv = Canvas(S, S)
    ring = ring_of(sd_circle(cv, 48, 76, 22), 8)
    stone = sd_poly(cv, ngon(48, 50, 10, 6, 0), margin=3)
    chain = sd_stroke(cv, catmull([(66, 22), (84, 30), (98, 44), (102, 62)], 8), 3)
    chain2 = sd_stroke(cv, catmull([(66, 22), (74, 40), (88, 56), (102, 62)], 8), 3)
    pend = sd_poly(cv, [(102, 60), (112, 74), (102, 94), (92, 74)], margin=3)
    sd = union(ring, stone, chain, chain2, pend)
    h = -profile(sd, 3.0, "round") * 2.2
    cv.over(shade(cv, h, PALE, flat_level=0.62), cov(cv, sd), 0.55)
    paint(cv, np.abs(sd) - 0.5, "#fff4dc", 0.35)
    return cv


for _g, _fn in GLYPHS.items():
    SLOTS[f"glyph_{_g}"] = (_fn, dict(margins=None, use=f"Pale engraved silhouette for an empty '{_g}' equipment slot (128x128; centre it in equip_slot).", scale=0.5))


# ------------------------------------------------------------------------------------------ rarity frames

RARITY = [
    ("Beginner", "#8a7a66"), ("Common", "#d8dde4"), ("Basic", "#4ec25a"), ("Advanced", "#3a86ff"), ("Licensed", "#22c4b0"),
    ("Elite", "#f5cc4a"), ("Master", "#f08a2a"), ("Mythical", "#d24af0"), ("Legendary", "#ff4a1a"), ("Aether", "#7ff3ff"),
]


def rarity_frame(tier):
    S = 128
    cv = Canvas(S, S)
    name, col = RARITY[tier]
    w = [5, 5, 6, 6, 7, 7, 8, 8, 8, 9][tier]
    o = 5.0
    outer = sd_rect(cv, o, o, S - o, S - o, 10)
    inner = sd_rect(cv, o + w, o + w, S - o - w, S - o - w, max(10 - w, 3))
    band = sub(outer, inner)
    if tier >= 5:
        # outer + inner glow in the tier colour
        cv.glow(cov(cv, band), col, 2.5 + (tier - 5) * 0.8, 0.35 + (tier - 5) * 0.1, gain=1.4)
    mat = tint_mat(col, sp=0.5, pw=26)
    eh = None
    noise = canvas_noise(cv, 100 + tier, 2)
    if tier == 0:
        mat = MAT["iron_warm"]
        eh = hammered(cv, 3, 0.8)
        # chips / wear
        rng = np.random.default_rng(7)
        for _ in range(9):
            side = rng.integers(0, 4)
            t = rng.uniform(20, 108)
            x, y = [(t, o), (S - o, t), (t, S - o), (o, t)][side]
            band = sub(band, sd_circle(cv, x, y, rng.uniform(1.5, 3.2)))
    elif tier == 1:
        mat = MAT["steel"]
    elif tier == 6:
        # engraved chevrons along the band
        lines = []
        for i in range(10):
            t = 16 + i * 10.6
            for (a, b) in (((t - 3, o + 1.5), (t + 3, o + w - 1.5)), ((t - 3, S - o - 1.5), (t + 3, S - o - w + 1.5)),
                           ((o + 1.5, t - 3), (o + w - 1.5, t + 3)), ((S - o - 1.5, t - 3), (S - o - w + 1.5, t + 3))):
                lines.append(sd_stroke(cv, [a, b], 0))
        eh = groove_h(cv, union(*lines), 1.6, 1.2)
    elif tier == 9:
        # prismatic: hue drifts cyan -> white -> violet-blue around the frame
        ang = (np.arctan2(cv.Y - 64, cv.X - 64) / (2 * math.pi) + 0.5)
        prism = ramp(ang, [(0, "#7ff3ff"), (0.2, "#d8fdff"), (0.4, "#9ec8ff"), (0.6, "#c8b0ff"), (0.8, "#b0fff0"), (1, "#7ff3ff")])
        mat = dict(ramp=even_ramp(["#06303a", "#1a7890", "#50c8e0", "#a8f4ff", "#e8feff", "#ffffff"]), spec="#ffffff", sp=0.9, pw=40)
    cv.shadow(cov(cv, band), 0, 1.5, 1.5, 0.7)
    rgb, a = metal(cv, band, mat, bevel=w * 0.55, extra_h=eh, noise=noise, noise_amt=0.05)
    if tier == 9:
        rgb = rgb * 0.55 + prism * rgb.mean(-1, keepdims=True) * 0.75
    cv.put((rgb, a))
    if tier == 0:
        cv.over("#3a2a1a", cov(cv, band) * np.clip(canvas_noise(cv, 44, 1.2) * 0.5 + 0.2, 0, 1), 0.5)  # rust patches
    # per-tier ornament
    corners = ((o, o, 1, 1), (S - o, o, -1, 1), (o, S - o, 1, -1), (S - o, S - o, -1, -1))
    if tier == 2:
        for (ox, oy, sx, sy) in corners:
            stud(cv, ox + sx * w / 2, oy + sy * w / 2, 3.2, mat=tint_mat(col, sp=0.5))
    if tier == 3:
        paint(cv, np.abs(sd_rect(cv, o + w + 3, o + w + 3, S - o - w - 3, S - o - w - 3, 3)) - 0.5, col, 0.55)
        for (ox, oy, sx, sy) in corners:
            diamond(cv, ox + sx * w / 2, oy + sy * w / 2, 6, mat=tint_mat(col, sp=0.6))
    if tier == 4:
        for (ox, oy, sx, sy) in corners[:3]:
            br = sd_stroke(cv, [(ox + sx * (w + 3), oy + sy * 26), (ox + sx * (w + 3), oy + sy * (w + 3)), (ox + sx * 26, oy + sy * (w + 3))], 2.6)
            draw_part(cv, br, mat, bevel=1.3, shadow=None)
        # stamped license seal (bottom-right)
        cx, cy = S - 22, S - 22
        seal = sd_poly(cv, star(cx, cy, 12, 17, 15), margin=3)
        draw_part(cv, seal, tint_mat("#1a9a8a", sp=0.5), bevel=4, shadow=(0.8, 1.8, 2, 0.9))
        paint(cv, np.abs(sd_circle(cv, cx, cy, 10.5)) - 0.6, "#062a26", 0.8)
        st = sd_poly(cv, star(cx, cy, 5, 7.5, 3), margin=2)
        draw_part(cv, st, MAT["gold"], bevel=2.5, kind="chisel", shadow=None)
    if tier == 5:
        for (ox, oy, sx, sy) in corners:
            sds = [sd_stroke(cv, place(catmull([(3, 22), (3, 3), (22, 3)], 3), ox, oy, sx, sy), 4.5)]
            for P in (spiral(28, 9, 5, 1, math.pi, math.pi * 2.6, 18), diag_mirror(spiral(28, 9, 5, 1, math.pi, math.pi * 2.6, 18))):
                sds.append(sd_stroke(cv, place(P, ox, oy, sx, sy), 2.6, 1.0))
            draw_part(cv, union(*sds), MAT["gold"], bevel=2, shadow=(0.5, 1, 1, 0.7))
            gx, gy = place([(5, 5)], ox, oy, sx, sy)[0]
            gem(cv, gx, gy, 4.2, tint_mat("#ffd040", sp=0.9, pw=40), glow="#ffe080", glow_sigma=3, glow_str=0.5, setting="gold", setting_w=1.5)
    if tier == 6:
        for (ox, oy, sx, sy) in corners:
            sds = [sd_poly(cv, place(leaf((2, 2), (26, 26), 11), ox, oy, sx, sy), margin=3)]
            for P in (catmull([(4, 14), (8, 26), (4, 36)], 6), diag_mirror(catmull([(4, 14), (8, 26), (4, 36)], 6))):
                sds.append(sd_stroke(cv, place(P, ox, oy, sx, sy), 3.2, 1.0))
            draw_part(cv, union(*sds), tint_mat("#e08a3a", sp=0.6), bevel=2.5, shadow=(0.5, 1, 1, 0.7))
    if tier == 7:
        # glowing runes along the band
        r1 = union(rune_band_sd(cv, 26, 102, o + w / 2, w * 0.8, seed=71, gap=2.0),
                   rune_band_sd(cv, 26, 102, S - o - w / 2, w * 0.8, seed=72, gap=2.0))
        m = np.clip(1 - np.abs(r1) / 0.8, 0, 1)
        # vertical sides: transpose a horizontal band
        side = rune_band_sd(cv, 26, 102, o + w / 2, w * 0.8, seed=74, gap=2.0)
        ms = np.clip(1 - np.abs(side) / 0.8, 0, 1)
        m = np.maximum(m, ms.T)
        ms2 = np.clip(1 - np.abs(rune_band_sd(cv, 26, 102, S - o - w / 2, w * 0.8, seed=75, gap=2.0)) / 0.8, 0, 1)
        m = np.maximum(m, ms2.T)
        cv.glow(m, "#ff80ff", 1.5, 0.8, gain=2)
        cv.over("#ffe0ff", m, 0.95)
        for (ox, oy, sx, sy) in corners:
            gem(cv, ox + sx * w / 2, oy + sy * w / 2, 5.5, MAT["violet"], glow="#e060ff", glow_sigma=5, glow_str=0.7,
                setting=tint_mat("#b040d0", sp=0.5), setting_w=2)
    if tier == 8:
        for (ox, oy, sx, sy) in corners:
            sds = []
            for (p0, p1, wd, bend) in (((0, 0), (30, 6), 9, -3), ((0, 0), (6, 30), 9, 3), ((2, 2), (34, 34), 10, 0),
                                       ((8, 2), (22, -2), 5, -2), ((2, 8), (-2, 22), 5, 2)):
                sds.append(sd_poly(cv, place(leaf(p0, p1, wd, bend=bend), ox, oy, sx, sy), margin=3))
            fl = union(*sds)
            cv.glow(cov(cv, fl), "#ff6a14", 4, 0.8, gain=1.5)
            h = profile(fl, 3, "round") * 3
            t = np.clip(np.hypot(cv.X - ox, cv.Y - oy) / 36, 0, 1)
            rgb = shade(cv, h, tint_mat("#ff5a18", sp=0.6))
            rgb = rgb * (1 - t[..., None] * 0.5) + C("#ffe070") * (t[..., None] * 0.6)
            cv.put((rgb, cov(cv, fl)))
        # ember glow along inside
        cv.over("#ff6020", np.clip(1 + inner / 14, 0, 1) ** 2 * cov(cv, inner), 0.3)
    if tier == 9:
        aether_channel(cv, np.abs(sd_rect(cv, o + w / 2, o + w / 2, S - o - w / 2, S - o - w / 2, 8)), core=0.8,
                       glow_sigma=3, strength=1.0, color="#9ff6ff", core_color="#ffffff")
        for (ox, oy, sx, sy) in corners:
            # crystal shards bursting from the corners
            for (ang, L, wd) in ((45, 30, 10), (20, 22, 6.5), (70, 22, 6.5)):
                a = math.radians(ang)
                tipx, tipy = ox + sx * math.cos(a) * L, oy + sy * math.sin(a) * L
                bx, by = ox + sx * 1, oy + sy * 1
                dx, dy = tipx - bx, tipy - by
                nl = math.hypot(dx, dy)
                nx, ny = -dy / nl * wd / 2, dx / nl * wd / 2
                pts = [(bx + nx * 0.5, by + ny * 0.5), (bx + dx * 0.7 + nx, by + dy * 0.7 + ny), (tipx, tipy),
                       (bx + dx * 0.7 - nx, by + dy * 0.7 - ny), (bx - nx * 0.5, by - ny * 0.5)]
                sd = sd_poly(cv, pts, margin=3)
                cv.glow(cov(cv, sd), AETHER, 4, 0.6, gain=1.6)
                draw_part(cv, sd, MAT["aether"], bevel=wd * 0.5, kind="chisel", shadow=(0.4, 1, 1, 0.6))
            cv.over("#ffffff", cov(cv, sd_circle(cv, ox + sx * 7, oy + sy * 7, 2.6), soft=0.8), 0.9)
        cv.over(AETHER, np.clip(1 + inner / 18, 0, 1) ** 2 * cov(cv, inner), 0.35)
    return cv


def rarity_glow(tier):
    S = 128
    cv = Canvas(S, S)
    name, col = RARITY[tier]
    inner = sd_rect(cv, 10, 10, S - 10, S - 10, 8)
    depth = 18 + (tier - 5) * 4
    t = np.clip(1 + inner / depth, 0, 1) * cov(cv, sd_rect(cv, 4, 4, S - 4, S - 4, 12))
    cv.over(col, t ** 1.8, 0.55 + (tier - 5) * 0.08)
    cv.over(cmix(col, "#ffffff", 0.6), t ** 5, 0.5)
    return cv


for _t in range(10):
    SLOTS[f"rarity_{_t}"] = ((lambda t: (lambda: rarity_frame(t)))(_t), dict(
        margins=None, use=f"Rarity overlay frame tier {_t} ({RARITY[_t][0]}, {RARITY[_t][1]}); transparent centre, draw over slot*.png at the same size.",
        scale=0.5, tier=_t, tier_name=RARITY[_t][0], color=RARITY[_t][1]))
for _t in range(5, 10):
    SLOTS[f"rarity_glow_{_t}"] = ((lambda t: (lambda: rarity_glow(t)))(_t), dict(
        margins=None, use=f"Soft inner glow for tier {_t} ({RARITY[_t][0]}); additive/pulsing layer under rarity_{_t}.",
        scale=0.5, tier=_t, blend="add or mix"))


# ------------------------------------------------------------------------------------------ hotbar

def _skill_bezel(empty):
    S = 128
    cv = Canvas(S, S)
    outer = sd_rect(cv, 6, 6, S - 6, S - 6, 12)
    inner = sd_rect(cv, 16, 16, S - 16, S - 16, 5)
    cv.shadow(cov(cv, outer), 0, 2, 3, 0.8)
    # ornate ring behind the square (shows at the corners)
    ring = ring_of(sd_circle(cv, 64, 64, 58), 6)
    ring = sub(ring, sd_rect(cv, 12, 12, S - 12, S - 12, 8))
    if empty:
        cv.over(rgrad(cv, 64, 60, 60, [(0, "#1c1714"), (1, "#070605")]), cov(cv, inner))
        inner_shadow(cv, inner, 20, op=0.85)
        rr = ring_of(sd_circle(cv, 64, 64, 28), 1.2)
        paint(cv, rr, "#5a4a38", 0.35)
        st = sd_poly(cv, star(64, 64, 4, 18, 4), margin=2)
        paint(cv, np.abs(st) - 0.6, "#5a4a38", 0.35)
    band = sub(outer, inner)
    cv.put(metal(cv, band, MAT["bronze"], bevel=6, extra_h=hammered(cv, 17, 0.2), noise=canvas_noise(cv, 4, 2), noise_amt=0.05))
    paint(cv, np.abs(sd_rect(cv, 11, 11, S - 11, S - 11, 7)) - 0.6, "#3a2410", 0.8)
    paint(cv, np.abs(sd_rect(cv, 16.5, 16.5, S - 16.5, S - 16.5, 5)) - 0.7, "#000000", 0.9)
    for (ox, oy, sx, sy) in ((6, 6, 1, 1), (S - 6, 6, -1, 1), (6, S - 6, 1, -1), (S - 6, S - 6, -1, -1)):
        arcp = arc(ox + sx * 30, oy + sy * 30, 26, 0, 2 * math.pi, 64)
        a0 = math.atan2(-sy, -sx)
        seg = arc(ox + sx * 30, oy + sy * 30, 25, a0 - 0.95, a0 + 0.95, 24)
        draw_part(cv, sd_stroke(cv, seg, 5.0), MAT["gold"], bevel=2.3, shadow=(0.6, 1.2, 1.2, 0.8))
        gem(cv, ox + sx * 7, oy + sy * 7, 4.2, MAT["aether"], glow=AETHER, glow_sigma=3, glow_str=0.45, setting="gold", setting_w=1.6)
    diamond(cv, 64, 9, 7, 5, mat="gold")
    return cv


SLOTS["skill_slot"] = (lambda: _skill_bezel(False), dict(margins=None, use="Hotbar skill bezel (128x128 at 2x). Transparent 96x96 window at (16,16) for the skill icon; draw the icon under the bezel.", scale=0.5, icon_rect=[16, 16, 96, 96]))
SLOTS["skill_slot_empty"] = (lambda: _skill_bezel(True), dict(margins=None, use="Hotbar skill bezel with an engraved empty well.", scale=0.5, icon_rect=[16, 16, 96, 96]))


@reg("cooldown_radial", "White mask for TextureProgressBar (FILL_CLOCKWISE / counter-clockwise); matches the skill_slot icon window (16,16,96,96). Tint e.g. #000000b0.",
     icon_rect=[16, 16, 96, 96])
def cooldown_radial():
    cv = Canvas(128, 128)
    cv.over("#ffffff", cov(cv, sd_rect(cv, 16, 16, 112, 112, 5)))
    return cv


@reg("keybind_badge", "Small plaque for a key label under/over a hotbar slot (64x40 at 2x); 9-slice for wider labels.",
     margins=[16, 14, 16, 14], content_margins=[10, 6, 10, 6], stretch="h")
def keybind_badge():
    W, H = 64, 40
    cv = Canvas(W, H)
    outer = sd_chamfer_box(cv, W / 2, H / 2, W / 2 - 3, H / 2 - 3, 7)
    inner = sd_chamfer_box(cv, W / 2, H / 2, W / 2 - 6, H / 2 - 6, 5)
    cv.shadow(cov(cv, outer), 0, 1.5, 2, 0.8)
    cv.over(vgrad(cv, 3, H - 3, [(0, "#241c16"), (1, "#0c0908")]), cov(cv, outer))
    cv.put(metal(cv, sub(outer, inner), MAT["gold_dim"], bevel=2.5))
    return cv
