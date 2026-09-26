"""menu/: title wordmark, menu column frame, menu vignette, class plinth glow."""
from __future__ import annotations

import math

import numpy as np

from rast import (catmull as _cm, Canvas, MAT, C, cov, sd_circle, sd_ellipse, sd_rect, sd_chamfer_box, sd_poly, sd_stroke, union, sub,
                  ring_of, profile, metal, shade, paint, gem, blur, spiral, catmull, star, leaf, canvas_noise, fnoise,
                  tint_mat, cmix, vgrad, rgrad, ramp, even_ramp, F)
from raster_orn import (corner_bastion, aether_channel, draw_part, inner_shadow, center_fill, hammered, AETHER, AETHER_HI,
                        place, diag_mirror)
from raster_frames import stud, diamond, iron_band, molding
from raster_title import GLYPHS

MENU = {}


def reg(name, use, margins=None, scale=0.5, **extra):
    def deco(fn):
        MENU[name] = (fn, dict(margins=margins, use=use, scale=scale, **extra))
        return fn
    return deco


# ------------------------------------------------------------------------------------------ wordmark

TITLE_GOLD = dict(ramp=even_ramp(["#1a0e04", "#5a3a12", "#a8782c", "#e2b85a", "#ffe8a8", "#fffaf0"]), spec="#ffffff", sp=0.7, pw=30)


def layout(text, cap, initial_scale, tracking, x0, baseline):
    """Returns [(glyph, scale, ox, oy)] and total width."""
    out = []
    x = x0
    first = True
    for ch in text:
        if ch == " ":
            x += 300 * cap / 1000
            first = True
            continue
        g = GLYPHS[ch]()
        s = cap / 1000 * (initial_scale if first else 1.0)
        out.append((g, s, x, baseline - 1000 * s))
        x += g["w"] * s + tracking
        first = False
    return out, x - tracking - x0


def glyph_sd(cv, g, s, ox, oy):
    T = lambda pts: [(ox + x * s, oy + y * s) for x, y in pts]
    adds = [sd_poly(cv, T(p), margin=6) for p in g["add"]]
    for spine, widths in g.get("strokes", []):
        k = 8
        P = T(catmull(spine, k))
        wd = np.interp(np.arange(len(P)) / k, np.arange(len(widths)), widths)
        for i in range(len(P) - 1):
            adds.append(sd_stroke(cv, [P[i], P[i + 1]], wd[i] * s, wd[i + 1] * s, margin=2))
    sd = union(*adds)
    if g["sub"]:
        sd = sub(sd, union(*[sd_poly(cv, T(p), margin=6) for p in g["sub"]]))
    return sd


@reg("title_logo", "Main-menu 'BEYOND HEROES' wordmark (1600x420, drawn at 0.5 for 1080p -> 800x210). Own vector letterforms, gold chiselled metal, aether glow. Subtitle band y 300..410 left empty.",
     subtitle_rect=[300, 300, 1000, 110])
def title_logo():
    W, H = 1600, 420
    cv = Canvas(W, H)
    cap, ini, track = 134, 1.22, 20
    items, tw = layout("BEYOND HEROES", cap, ini, track, 0, 0)
    x0 = (W - tw) / 2
    base = 246
    sds = []
    for g, s, ox, oy in items:
        sds.append(glyph_sd(cv, g, s, ox + x0, oy + base))
    sd = union(*sds)
    m = cov(cv, sd)
    # aether aura behind the letters
    cv.glow(m, "#1a6a8a", 34, 0.55, gain=1.2)
    cv.glow(m, AETHER, 12, 0.55, gain=1.3)
    # dark backing plate (outline) + drop shadow
    back = sd - 5.0
    cv.shadow(cov(cv, back), 0, 6, 7, 0.9)
    cv.over("#0a0604", cov(cv, back))
    # thin bronze outer edge
    edge = sd - 2.2
    cv.put(metal(cv, edge, MAT["bronze"], bevel=2.2, bright=0.9))
    # chiselled gold face with vertical metallic gradient
    h = profile(sd, 11.0, "chisel") * 9.0
    rgb = shade(cv, h, TITLE_GOLD, flat_level=0.6)
    top = base - cap * ini
    g = np.clip((cv.Y - top) / (base - top), 0, 1)
    tint = ramp(g, [(0, "#fff4dc"), (0.45, "#ffe4a8"), (0.55, "#d8a860"), (1, "#a8783a")])
    rgb = rgb * tint * 1.08
    cv.put((rgb, m))
    # horizon glint line across the upper third of the letters
    band = np.clip(1 - np.abs(cv.Y - (top + (base - top) * 0.36)) / 2.0, 0, 1) * m
    cv.over("#ffffff", band, 0.25)
    # rule + crest under the wordmark
    ry = 282
    rule = [(260, ry), (720, ry - 3.5), (800, ry - 5), (880, ry - 3.5), (1340, ry), (880, ry + 3.5), (800, ry + 5), (720, ry + 3.5)]
    rsd = sd_poly(cv, rule, margin=4)
    draw_part(cv, rsd, MAT["gold"], bevel=2.5, shadow=(0, 2, 2.5, 0.85))
    aether_channel(cv, np.abs(sd_stroke(cv, [(420, ry), (1180, ry)], 0)), core=0.7, glow_sigma=3.5, strength=0.8)
    fil = []
    for sx in (1, -1):
        for sy in (1, -1):
            pts = catmull([(800 + sx * 26, ry + sy * 4), (800 + sx * 60, ry + sy * 16), (800 + sx * 100, ry + sy * 14), (800 + sx * 118, ry + sy * 5)], 8)
            fil.append(sd_stroke(cv, pts, 5, 1.8))
        fil.append(sd_poly(cv, leaf((800 + sx * 120, ry), (800 + sx * 190, ry), 8), margin=3))
    draw_part(cv, union(*fil), MAT["gold"], bevel=2, shadow=(0, 1.5, 2, 0.8))
    dsd = sd_poly(cv, [(800, ry - 26), (826, ry), (800, ry + 26), (774, ry)], margin=4)
    draw_part(cv, dsd, MAT["gold"], bevel=7, kind="chisel", shadow=(0, 2.5, 3, 0.9))
    gem(cv, 800, ry, 9, MAT["aether"], glow=AETHER, glow_sigma=10, glow_str=0.7, setting="gold", setting_w=2.5)
    # sparkles on a few serifs
    rng = np.random.default_rng(3)
    for (x, y, r) in ((x0 + 8, top + 4, 11), (W - x0 - 30, base - 8, 9), (800 - 190, ry, 8), (800 + 190, ry, 8)):
        s_ = sd_poly(cv, star(x, y, 4, r, r * 0.16), margin=2)
        cv.glow(cov(cv, s_), AETHER_HI, 3, 0.7, gain=1.5)
        paint(cv, s_, "#ffffff", 0.95)
    return cv


# ------------------------------------------------------------------------------------------ menu frame

@reg("menu_frame", "Vertical ornate frame for the main-menu button column (512x1024 at 2x). Stretch vertically only (keep width): margins top 208 / bottom 176 hold the crest and base.",
     margins=[0, 208, 0, 176], content_margins=[72, 200, 72, 150], stretch="v")
def menu_frame():
    W, H = 512, 1024
    cv = Canvas(W, H)
    x0, x1, y0, y1 = 36, W - 36, 96, H - 60
    body = sd_rect(cv, x0 + 10, y0 + 10, x1 - 10, y1 - 10, 12)
    rgb = center_fill(cv, 100, 208, W - 100, H - 176, base="#100c0a", seed=301, amt=0.03, cw=W - 200, ch=H - 384)
    cv.over(rgb, cov(cv, body), 0.88)
    inner_shadow(cv, sd_rect(cv, x0 + 26, y0 + 26, x1 - 26, y1 - 26, 8), 40, op=0.8)
    iron_band(cv, x0, y0, x1, y1, 16, 30, seed=303, grooves=(0.5,))
    aether_channel(cv, np.abs(sd_rect(cv, x0 + 15, y0 + 15, x1 - 15, y1 - 15, 6)), core=0.9, glow_sigma=3.5, strength=0.9)
    molding(cv, x0 + 30, y0 + 30, x1 - 30, y1 - 30, 7, 6, mat="bronze")
    # arched crest on top
    cx = W / 2
    arch = catmull([(cx - 170, y0 + 8), (cx - 120, 52), (cx, 18), (cx + 120, 52), (cx + 170, y0 + 8)], 10) + [(cx + 150, y0 + 30), (cx - 150, y0 + 30)]
    asd = sd_poly(cv, arch, margin=6)
    draw_part(cv, asd, MAT["gold_dim"], bevel=7, shadow=(0, 3, 4, 0.9), noise=canvas_noise(cv, 7, 2), noise_amt=0.05)
    inner = catmull([(cx - 138, y0 + 14), (cx - 100, 64), (cx, 36), (cx + 100, 64), (cx + 138, y0 + 14)], 10) + [(cx + 120, y0 + 22), (cx - 120, y0 + 22)]
    isd = sd_poly(cv, inner, margin=4)
    cv.put((shade(cv, -profile(isd, 3, "round") * 3, MAT["iron"], flat_level=0.4), cov(cv, isd)))
    st = sd_poly(cv, star(cx, 68, 8, 30, 9), margin=3)
    cv.glow(cov(cv, st), AETHER, 7, 0.6, gain=1.5)
    draw_part(cv, st, MAT["gold"], bevel=6, kind="chisel", shadow=(0, 1.5, 2, 0.8))
    gem(cv, cx, 68, 10, MAT["aether"], glow=AETHER_HI, glow_sigma=8, glow_str=0.6, setting="gold", setting_w=3)
    for sx in (1, -1):
        corner_bastion(cv, cx + sx * (cx - 32), y0 - 4, -sx, 1, S=96)
        corner_bastion(cv, cx + sx * (cx - 32), y1 + 4, -sx, -1, S=96)
    # base: bronze plinth with a hanging gem
    pl = [(cx - 150, y1 - 6), (cx + 150, y1 - 6), (cx + 120, y1 + 30), (cx + 30, y1 + 36), (cx, y1 + 52), (cx - 30, y1 + 36), (cx - 120, y1 + 30)]
    draw_part(cv, sd_poly(cv, pl, margin=6), MAT["gold_dim"], bevel=6, shadow=(0, 3, 4, 0.9))
    gem(cv, cx, y1 + 22, 9, MAT["aether"], glow=AETHER, glow_sigma=8, glow_str=0.6, setting="gold", setting_w=2.5)
    return cv


@reg("vignette_menu", "Main-menu vignette (1920x1080): darkens edges, faint warm floor light. Stretch to the viewport.", scale=1.0)
def vignette_menu():
    W, H = 1920, 1080
    cv = Canvas(W, H, ss=1)
    d = np.hypot((cv.X - W / 2) / (W / 2), (cv.Y - H * 0.45) / (H / 2))
    t = np.clip((d - 0.35) / 1.0, 0, 1) ** 1.4
    n = fnoise(H, W, 71, beta=2.4, lo=2)
    cv.over("#000000", np.clip(t * (1 + n * 0.1), 0, 1) * 0.92)
    top = np.clip(1 - cv.Y / (H * 0.25), 0, 1) ** 2
    cv.over("#000000", top * 0.5)
    return cv


@reg("class_plinth_glow", "Additive elliptical aether glow under the hero on the class-select plinth (512x256, white-cyan).", scale=1.0)
def class_plinth_glow():
    W, H = 512, 256
    cv = Canvas(W, H)
    cx, cy = W / 2, H / 2
    d = np.hypot((cv.X - cx) / 230, (cv.Y - cy) / 100)
    cv.over(AETHER, np.clip(1 - d, 0, 1) ** 2.2, 0.8)
    ring = np.clip(1 - np.abs(d - 0.78) / 0.05, 0, 1)
    cv.over(AETHER_HI, ring, 0.7)
    cv.over("#ffffff", np.clip(1 - np.abs(d - 0.78) / 0.015, 0, 1), 0.7)
    # rune ticks on the ring
    ang = np.arctan2((cv.Y - cy) / 100, (cv.X - cx) / 230)
    ticks = (np.abs(np.sin(ang * 24)) > 0.92) * np.clip(1 - np.abs(d - 0.88) / 0.035, 0, 1)
    cv.over(AETHER, ticks, 0.55)
    cv.over("#ffffff", np.clip(1 - d / 0.35, 0, 1) ** 2, 0.5)
    return cv
