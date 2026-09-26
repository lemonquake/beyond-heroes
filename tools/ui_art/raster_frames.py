"""frames/: 9-slice panels, buttons, tabs and controls (authored at 2x; draw at scale 0.5 for 1080p logical size)."""
from __future__ import annotations

import math

import numpy as np

from rast import (Canvas, MAT, C, cov, sd_circle, sd_box, sd_rect, sd_chamfer_box, sd_poly, sd_stroke, union, sub, inter,
                  ring_of, shell, profile, metal, shade, groove_h, paint, gem, blur, spiral, arc, bez3, catmull, xf, star,
                  ngon, leaf, canvas_noise, fnoise, tint_mat, cmix, vgrad, hgrad, rgrad, desaturate, F)
from raster_orn import (corner_bastion, aether_channel, draw_part, inner_shadow, center_fill, hammered, AETHER, AETHER_HI,
                        GOLD_C, EMBER, place, diag_mirror)

FRAMES = {}   # name -> (builder, manifest entry)


def reg(name, margins, use, scale=0.5, **extra):
    def deco(fn):
        FRAMES[name] = (fn, dict(margins=list(margins) if margins else None, use=use, scale=scale, **extra))
        return fn
    return deco


# ------------------------------------------------------------------------------------------ shared band builders

def iron_band(cv, x0, y0, x1, y1, r_out, width, seed, mat="iron", grooves=(0.5,), bevel=9.0, shadow=(0, 3, 5, 0.85)):
    outer = sd_rect(cv, x0, y0, x1, y1, r_out)
    inner = sd_rect(cv, x0 + width, y0 + width, x1 - width, y1 - width, max(r_out - width, 2))
    band = sub(outer, inner)
    eh = hammered(cv, seed, 0.35)
    for g in grooves:
        o = width * g
        line = np.abs(sd_rect(cv, x0 + o, y0 + o, x1 - o, y1 - o, max(r_out - o, 2)))
        eh = eh + groove_h(cv, line, 2.6, 1.4)
    draw_part(cv, band, MAT[mat], bevel=bevel, kind="round", shadow=shadow, extra_h=eh,
              noise=canvas_noise(cv, seed + 7, 1.5), noise_amt=0.05)
    return band


def molding(cv, x0, y0, x1, y1, r, w, mat="bronze", bevel=None, shadow=(0.8, 1.5, 1.8, 0.8), bright=1.0):
    sd = ring_of(sd_rect(cv, x0, y0, x1, y1, r), w)
    draw_part(cv, sd, MAT[mat] if isinstance(mat, str) else mat, bevel=bevel or w * 0.5, kind="round", shadow=shadow,
              bright=bright)
    return sd


def stud(cv, x, y, r, mat="gold", shadow=True):
    sd = sd_circle(cv, x, y, r)
    draw_part(cv, sd, MAT[mat] if isinstance(mat, str) else mat, bevel=r, shadow=(0.6, 1.0, 1.0, 0.7) if shadow else None)


def diamond(cv, x, y, rx, ry=None, mat="gold", shadow=True, bevel=None):
    ry = rx if ry is None else ry
    sd = sd_poly(cv, [(x, y - ry), (x + rx, y), (x, y + ry), (x - rx, y)], margin=3)
    draw_part(cv, sd, MAT[mat] if isinstance(mat, str) else mat, bevel=bevel or min(rx, ry) * 0.8, kind="chisel",
              shadow=(0.6, 1.2, 1.2, 0.7) if shadow else None)
    return sd


# ------------------------------------------------------------------------------------------ panels

@reg("panel_main", (112, 112, 112, 112), "Primary window frame (inventory, character, skills, talents, shop). Centre patch is periodic noise + faint rune lattice: AXIS_STRETCH tile, tile-fit or stretch all work.",
     content_margins=[60, 60, 60, 60])
def panel_main():
    S = 512
    cv = Canvas(S, S)
    m = 112
    body = sd_rect(cv, 30, 30, S - 30, S - 30, 10)
    rgb = center_fill(cv, m, m, S - m, S - m, base="#15100d", seed=11, amt=0.03, cw=S - 2 * m, ch=S - 2 * m,
                      runes=0.45, cells=(3, 3))
    cv.over(rgb, cov(cv, body))
    inner_shadow(cv, sd_rect(cv, 50, 50, S - 50, S - 50, 8), 48, op=0.75)
    iron_band(cv, 6, 6, S - 6, S - 6, 16, 44, seed=21, grooves=(0.5,))
    aether_channel(cv, np.abs(sd_rect(cv, 28, 28, S - 28, S - 28, 5)), core=1.0, glow_sigma=4.0, strength=1.0)
    molding(cv, 10, 10, S - 10, S - 10, 13, 3.2, mat="gold_dim", shadow=None)
    molding(cv, 49, 49, S - 49, S - 49, 8, 7.0, mat="bronze")
    molding(cv, 56, 56, S - 56, S - 56, 5, 1.6, mat="gold_dim", shadow=(0.5, 1, 1, 0.6))
    for (ox, oy, sx, sy) in ((4, 4, 1, 1), (S - 4, 4, -1, 1), (4, S - 4, 1, -1), (S - 4, S - 4, -1, -1)):
        corner_bastion(cv, ox, oy, sx, sy, S=108)
    return cv


@reg("panel_inset", (40, 40, 40, 40), "Recessed inner well for lists, stat blocks, item grids inside a panel_main. Centre periodic.",
     content_margins=[22, 22, 22, 22])
def panel_inset():
    S = 256
    cv = Canvas(S, S)
    m = 40
    body = sd_rect(cv, 6, 6, S - 6, S - 6, 8)
    rgb = center_fill(cv, m, m, S - m, S - m, base="#0d0a08", seed=31, amt=0.03, cw=S - 2 * m, ch=S - 2 * m)
    cv.over(rgb, cov(cv, body))
    inner_shadow(cv, sd_rect(cv, 6, 6, S - 6, S - 6, 8), 26, op=0.85)
    lip = sub(sd_rect(cv, 2, 2, S - 2, S - 2, 10), sd_rect(cv, 7, 7, S - 7, S - 7, 7))
    cv.put(metal(cv, lip, MAT["bronze"], bevel=3.0, height=-1.0))   # inverted = sunken lip
    molding(cv, 9.5, 9.5, S - 9.5, S - 9.5, 6, 1.2, mat="gold_dim", shadow=None, bright=0.8)
    for (x, y) in ((12, 12), (S - 12, 12), (12, S - 12), (S - 12, S - 12)):
        diamond(cv, x, y, 5.5, mat="gold_dim")
    return cv


@reg("panel_header", (104, 44, 104, 44), "Title banner strip for window headers; stretch horizontally (STRETCH mode; the lacquer centre is not periodic). Put panel_header_crest.png centred on top for the crest.",
     content_margins=[96, 30, 96, 30], stretch="h")
def panel_header():
    W, H = 768, 128
    cv = Canvas(W, H)
    cy = H / 2
    band = [(40, 22), (W - 40, 22), (W - 8, cy), (W - 40, H - 22), (40, H - 22), (8, cy)]
    bsd = sd_poly(cv, band, margin=8)
    cv.shadow(cov(cv, bsd), 0, 4, 6, 0.8)
    lac = vgrad(cv, 22, H - 22, [(0, "#3a1210"), (0.45, "#24090a"), (1, "#120405")])
    n = canvas_noise(cv, 41, 2.0)
    cv.over(lac * (1 + n[..., None] * 0.04), cov(cv, bsd))
    sheen = np.clip(1 - np.abs(cv.Y - 34) / 10, 0, 1) * cov(cv, bsd)
    cv.over("#ff9a70", sheen, 0.10)
    for y in (22, H - 22):
        rail = sd_stroke(cv, [(40, y), (W - 40, y)], 7)
        draw_part(cv, rail, MAT["gold"], bevel=3.5, shadow=(0, 1.5, 2, 0.7))
    for y in (31, H - 31):
        paint(cv, sd_stroke(cv, [(52, y), (W - 52, y)], 1.4), "#c9a060", 0.55)
    for sx, ox in ((1, 0), (-1, W)):
        cap = [(ox + sx * 8, cy), (ox + sx * 48, 12), (ox + sx * 92, 22), (ox + sx * 92, H - 22), (ox + sx * 48, H - 12)]
        csd = sd_poly(cv, cap, margin=8)
        draw_part(cv, csd, MAT["gold_dim"], bevel=5, shadow=(sx * 1.5, 2.5, 3, 0.85), noise=canvas_noise(cv, 5, 2), noise_amt=0.05)
        inner = [(ox + sx * 20, cy), (ox + sx * 50, 22), (ox + sx * 84, 29), (ox + sx * 84, H - 29), (ox + sx * 50, H - 22)]
        isd = sd_poly(cv, inner, margin=6)
        cv.put((shade(cv, -profile(isd, 3, "round") * 3, MAT["iron"], flat_level=0.45), cov(cv, isd)))
        gem(cv, ox + sx * 54, cy, 10, MAT["aether"], glow=AETHER, glow_sigma=8, glow_str=0.55, setting="gold", setting_w=3)
        stud(cv, ox + sx * 80, cy - 24, 3.2)
        stud(cv, ox + sx * 80, cy + 24, 3.2)
    return cv


@reg("panel_header_crest", None, "Centre crest overlay for panel_header: draw centred horizontally over the header at the same scale (not 9-slice).")
def panel_header_crest():
    W, H = 224, 144
    cv = Canvas(W, H)
    cx, cy = W / 2, H / 2
    sds = []
    for sx in (1, -1):
        for sy in (1, -1):
            pts = catmull([(cx + sx * 30, cy + sy * 8), (cx + sx * 60, cy + sy * 26), (cx + sx * 88, cy + sy * 24), (cx + sx * 100, cy + sy * 10)], 8)
            sds.append(sd_stroke(cv, pts, 7, 2.5))
        sds.append(sd_poly(cv, leaf((cx + sx * 36, cy), (cx + sx * 90, cy), 12), margin=3))
    draw_part(cv, union(*sds), MAT["gold"], bevel=3, shadow=(1, 2.5, 3, 0.85))
    sh = [(cx, cy - 52), (cx + 34, cy - 40), (cx + 36, cy + 4), (cx, cy + 56), (cx - 36, cy + 4), (cx - 34, cy - 40)]
    shd = sd_poly(cv, catmull(sh, 6, closed=True), margin=6)
    draw_part(cv, shd, MAT["gold_dim"], bevel=6, shadow=(1.5, 3, 4, 0.9), noise=canvas_noise(cv, 8, 2), noise_amt=0.05)
    inner = [(cx, cy - 42), (cx + 26, cy - 33), (cx + 27, cy + 2), (cx, cy + 44), (cx - 27, cy + 2), (cx - 26, cy - 33)]
    isd = sd_poly(cv, catmull(inner, 6, closed=True), margin=4)
    rgb = shade(cv, -profile(isd, 3, "round") * 3, MAT["iron"], flat_level=0.4)
    cv.put((rgb, cov(cv, isd)))
    st = sd_poly(cv, star(cx, cy - 2, 4, 24, 6), margin=3)
    cv.glow(cov(cv, st), AETHER, 6, 0.7, gain=1.5)
    draw_part(cv, st, MAT["aether"], bevel=5, kind="chisel", shadow=None)
    gem(cv, cx, cy - 2, 7, MAT["aether"], glow=AETHER_HI, glow_sigma=5, glow_str=0.5, setting="gold", setting_w=2.2)
    return cv


@reg("panel_tooltip", (28, 28, 28, 28), "Thin gold-edged tooltip frame (body 94% opaque). Centre flat + faint noise.",
     content_margins=[18, 16, 18, 16])
def panel_tooltip():
    S = 160
    cv = Canvas(S, S)
    m = 28
    body = sd_rect(cv, 4, 4, S - 4, S - 4, 6)
    cv.shadow(cov(cv, body), 0, 2, 3, 0.6)
    rgb = center_fill(cv, m, m, S - m, S - m, base="#100c0b", seed=51, amt=0.02, cw=S - 2 * m, ch=S - 2 * m)
    cv.over(rgb, cov(cv, body), 0.94)
    molding(cv, 6, 6, S - 6, S - 6, 5, 2.4, mat="gold", shadow=None)
    paint(cv, np.abs(sd_rect(cv, 11, 11, S - 11, S - 11, 3)) - 0.5, "#8a6a3a", 0.8)
    for (x, y) in ((6, 6), (S - 6, 6), (6, S - 6), (S - 6, S - 6)):
        diamond(cv, x, y, 6, mat="gold")
    return cv


@reg("panel_dialogue", (136, 72, 136, 48), "Wide NPC dialogue box with an ornate top edge; put panel_dialogue_crest.png centred on the top edge (speaker plate).",
     content_margins=[72, 56, 72, 36])
def panel_dialogue():
    W, H = 1024, 320
    cv = Canvas(W, H)
    body = sd_rect(cv, 20, 34, W - 20, H - 8, 10)
    rgb = center_fill(cv, 136, 72, W - 136, H - 48, base="#120e0c", seed=61, amt=0.03, cw=W - 272, ch=H - 120)
    cv.shadow(cov(cv, body), 0, 4, 8, 0.8)
    cv.over(rgb, cov(cv, body), 0.96)
    inner_shadow(cv, sd_rect(cv, 30, 46, W - 30, H - 18, 6), 34, op=0.7)
    molding(cv, 22, 36, W - 22, H - 10, 9, 5, mat="bronze", shadow=(0, 2, 3, 0.7))
    molding(cv, 29, 44, W - 29, H - 17, 5, 1.4, mat="gold_dim", shadow=None)
    beam = sd_rect(cv, 14, 18, W - 14, 50, 6)
    draw_part(cv, beam, MAT["iron"], bevel=7, shadow=(0, 3, 5, 0.9), extra_h=hammered(cv, 7, 0.3),
              noise=canvas_noise(cv, 71, 1.5), noise_amt=0.05)
    aether_channel(cv, np.abs(sd_stroke(cv, [(60, 34), (W - 60, 34)], 0)), core=1.0, glow_sigma=4, strength=1.0)
    for y in (18, 50):
        draw_part(cv, sd_stroke(cv, [(24, y), (W - 24, y)], 4.2), MAT["gold"], bevel=2, shadow=(0, 1, 1.5, 0.7))
    for (ox, sx) in ((10, 1), (W - 10, -1)):
        corner_bastion(cv, ox, 8, sx, 1, S=92, glow_str=0.6)
    for (ox, sx) in ((22, 1), (W - 22, -1)):
        br = catmull([(ox + sx * 2, H - 44), (ox + sx * 2, H - 12), (ox + sx * 36, H - 10)], 6)
        draw_part(cv, sd_stroke(cv, br, 6, 3), MAT["gold"], bevel=2.5)
        diamond(cv, ox + sx * 2, H - 10, 7, mat="gold")
    return cv


@reg("panel_dialogue_crest", None, "Speaker name-plate crest for the top edge of panel_dialogue (centre it on the top beam; not 9-slice).")
def panel_dialogue_crest():
    W, H = 384, 104
    cv = Canvas(W, H)
    cx, cy = W / 2, H / 2
    plate = [(cx - 150, cy), (cx - 124, cy - 30), (cx + 124, cy - 30), (cx + 150, cy), (cx + 124, cy + 30), (cx - 124, cy + 30)]
    psd = sd_poly(cv, plate, margin=6)
    draw_part(cv, psd, MAT["gold_dim"], bevel=5, shadow=(0, 3, 5, 0.9), noise=canvas_noise(cv, 81, 2), noise_amt=0.05)
    inner = [(cx - 138, cy), (cx - 118, cy - 22), (cx + 118, cy - 22), (cx + 138, cy), (cx + 118, cy + 22), (cx - 118, cy + 22)]
    isd = sd_poly(cv, inner, margin=4)
    rgb = vgrad(cv, cy - 22, cy + 22, [(0, "#1e1612"), (1, "#0a0807")])
    cv.put((rgb, cov(cv, isd)))
    inner_shadow(cv, isd, 8, op=0.7)
    for sx in (1, -1):
        gem(cv, cx + sx * 150, cy, 8, MAT["aether"], glow=AETHER, glow_sigma=7, glow_str=0.5, setting="gold", setting_w=2.6)
        fl = catmull([(cx + sx * 12, cy - 31), (cx + sx * 40, cy - 40), (cx + sx * 70, cy - 40), (cx + sx * 92, cy - 32)], 8)
        draw_part(cv, sd_stroke(cv, fl, 4.5, 1.6), MAT["gold"], bevel=2, shadow=(0.5, 1, 1, 0.6))
        draw_part(cv, sd_stroke(cv, spiral(cx + sx * 96, cy - 37, 5, 1, math.pi / 2 if sx > 0 else math.pi / 2, (math.pi / 2 - 1.7 * math.pi) if sx > 0 else (math.pi / 2 + 1.7 * math.pi), 20), 2.6, 1.0), MAT["gold"], bevel=1.4, shadow=None)
    diamond(cv, cx, cy - 32, 9, 7, mat="gold")
    return cv


@reg("panel_glass", (36, 36, 36, 36), "Translucent dark-glass HUD plate (skill bar backing, objective tracker). Body ~70% alpha; bevel highlight in the top margin only.",
     content_margins=[18, 18, 18, 18])
def panel_glass():
    S = 192
    cv = Canvas(S, S)
    m = 36
    body = sd_rect(cv, 4, 4, S - 4, S - 4, 12)
    rgb = center_fill(cv, m, m, S - m, S - m, base="#0a0e14", seed=91, amt=0.02, cw=S - 2 * m, ch=S - 2 * m)
    cv.over(rgb, cov(cv, body), 0.70)
    rim = shell(body, 5)
    h = profile(body, 5, "round") * 5
    lam = shade(cv, h, MAT["glass"], flat_level=0.4)
    cv.over(lam, cov(cv, rim), 0.9)
    top = np.clip(1 - (cv.Y - 6) / 18, 0, 1) * cov(cv, sd_rect(cv, 8, 6, S - 8, 30, 8))
    cv.over("#cfefff", top ** 2, 0.10)
    paint(cv, np.abs(sd_rect(cv, 7, 7, S - 7, S - 7, 9)) - 0.5, "#a8e8f4", 0.30)
    paint(cv, np.abs(sd_rect(cv, 4, 4, S - 4, S - 4, 12)) - 0.8, "#000000", 0.85)
    for (x, y, sx, sy) in ((4, 4, 1, 1), (S - 4, 4, -1, 1), (4, S - 4, 1, -1), (S - 4, S - 4, -1, -1)):
        L = [(x + sx * 4, y + sy * 26), (x + sx * 4, y + sy * 4), (x + sx * 26, y + sy * 4)]
        aether_channel(cv, np.abs(sd_stroke(cv, L, 0)), core=0.9, glow_sigma=2.5, strength=0.8)
    return cv


# ------------------------------------------------------------------------------------------ buttons

BTN = {
    "button": dict(size=(384, 104), rim="bronze", rim_w=6, body=("#2a1f18", "#140e0b"), orn="gold_dim",
                   use="Standard bronze button."),
    "button_primary": dict(size=(384, 112), rim="gold", rim_w=7, body=("#5a1614", "#260808"), orn="gold",
                           use="Primary/confirm button (Play, Confirm, Buy): gold trim, deep crimson lacquer."),
}
STATES = ("normal", "hover", "pressed", "disabled", "focus")


def _btn_shape(cv, W, H, pad, c):
    return sd_chamfer_box(cv, W / 2, H / 2, W / 2 - pad, H / 2 - pad, c)


def button_art(style, state):
    spec = BTN[style]
    W, H = spec["size"]
    cv = Canvas(W, H)
    pad = 12
    c = 16
    outer = _btn_shape(cv, W, H, pad, c)
    inner = _btn_shape(cv, W, H, pad + spec["rim_w"], c - 2)
    top_c, bot_c = spec["body"]
    if state == "hover":
        top_c, bot_c = cmix(top_c, "#ffb070", 0.14), cmix(bot_c, "#ff9050", 0.08)
    if state == "pressed":
        top_c, bot_c = cmix(bot_c, "#000000", 0.2), cmix(top_c, "#000000", 0.25)
    if state == "focus":
        cv.glow(cov(cv, outer), AETHER, 5, 0.75, gain=1.5)
    cv.shadow(cov(cv, outer), 0, 2 if state != "pressed" else 1, 3, 0.8)
    body = vgrad(cv, pad, H - pad, [(0, top_c), (0.5, cmix(top_c, bot_c, 0.55)), (1, bot_c)])
    n = canvas_noise(cv, 7, 2.0)
    cv.over(body * (1 + n[..., None] * 0.035), cov(cv, outer))
    if state != "pressed":
        sh = np.clip(1 - (cv.Y - (pad + spec["rim_w"])) / ((H - 2 * pad) * 0.42), 0, 1) * cov(cv, inner)
        cv.over("#ffe0c0", sh ** 2, 0.10 if state != "hover" else 0.16)
    else:
        inner_shadow(cv, inner, 14, op=0.7)
    if state == "hover":
        g = np.clip(1 - (H - pad - spec["rim_w"] - cv.Y) / 26, 0, 1) * cov(cv, inner)
        cv.over("#ffb060", g ** 1.5, 0.28)
    rim = sub(outer, inner)
    mat = MAT[spec["rim"]]
    height = -1.0 if state == "pressed" else 1.0
    bright = 1.12 if state == "hover" else 1.0
    cv.put(metal(cv, rim, mat, bevel=spec["rim_w"] * 0.8, height=height, bright=bright,
                 noise=canvas_noise(cv, 3, 2), noise_amt=0.04))
    paint(cv, np.abs(_btn_shape(cv, W, H, pad + spec["rim_w"] + 3, c - 3)) - 0.5,
          "#e8c080" if style == "button_primary" else "#8a6a44", 0.45 if state != "disabled" else 0.2)
    for sx, ox in ((1, pad), (-1, W - pad)):
        for sy, oy in ((1, pad), (-1, H - pad)):
            L = sd_stroke(cv, catmull([(ox + sx * 1, oy + sy * (c + 14)), (ox + sx * (c * 0.5 + 1), oy + sy * (c * 0.5 + 1)),
                                       (ox + sx * (c + 14), oy + sy * 1)], 6), 5, 5)
            draw_part(cv, L, MAT[spec["orn"]], bevel=2.2, shadow=(0.5, 1, 1, 0.6), height=height, bright=bright)
    if state == "focus":
        paint(cv, np.abs(_btn_shape(cv, W, H, pad - 2.5, c + 1)) - 0.9, AETHER_HI, 0.9)
        aether_channel(cv, np.abs(_btn_shape(cv, W, H, pad + spec["rim_w"] + 2.5, c - 3)), core=0.6, glow_sigma=2.5,
                       strength=0.7)
    if state == "disabled":
        desaturate(cv, 0.85, 0.56)
        cv.rgb *= 0.9
        cv.a *= 0.9
    return cv


def menu_button_art(state):
    W, H = 640, 120
    cv = Canvas(W, H)
    cy = H / 2
    pad = 14
    tip = 44

    def shape(p):
        pts = [(pad + p + tip * 0.9, pad + p), (W - pad - p - tip * 0.9, pad + p), (W - pad - p * 0.6, cy),
               (W - pad - p - tip * 0.9, H - pad - p), (pad + p + tip * 0.9, H - pad - p), (pad + p * 0.6, cy)]
        return sd_poly(cv, pts, margin=6)

    outer = shape(0)
    inner = shape(6)
    if state == "focus":
        cv.glow(cov(cv, outer), AETHER, 6, 0.7, gain=1.5)
    cv.shadow(cov(cv, outer), 0, 3, 5, 0.85)
    top_c, bot_c = "#1c1714", "#0b0908"
    if state == "hover":
        top_c, bot_c = "#2a2019", "#110c0a"
    if state == "pressed":
        top_c, bot_c = "#0a0807", "#17120f"
    body = vgrad(cv, pad, H - pad, [(0, top_c), (1, bot_c)])
    n = canvas_noise(cv, 17, 2.0)
    cv.over(body * (1 + n[..., None] * 0.04), cov(cv, outer), 0.97)
    if state == "pressed":
        inner_shadow(cv, inner, 16, op=0.7)
    else:
        sh = np.clip(1 - (cv.Y - pad - 6) / 30, 0, 1) * cov(cv, inner)
        cv.over("#ffe8d0", sh ** 2, 0.07)
    rim = sub(outer, inner)
    height = -1.0 if state == "pressed" else 1.0
    cv.put(metal(cv, rim, MAT["bronze"] if state != "hover" else MAT["gold"], bevel=5, height=height,
                 noise=canvas_noise(cv, 23, 2), noise_amt=0.04))
    paint(cv, np.abs(shape(11)) - 0.5, "#6a5234", 0.6)
    if state in ("hover", "focus"):
        y = H - pad - 16
        g = np.clip(1 - (y + 4 - cv.Y) / 34, 0, 1) * cov(cv, inner)
        cv.over(AETHER, g ** 2, 0.22 if state == "hover" else 0.14)
        aether_channel(cv, np.abs(sd_stroke(cv, [(pad + tip + 30, y), (W - pad - tip - 30, y)], 0)), core=1.1,
                       glow_sigma=5, strength=1.0 if state == "hover" else 0.7)
    for sx, ox in ((1, pad), (-1, W - pad)):
        fin = [(ox + sx * 0, cy), (ox + sx * 26, cy - 22), (ox + sx * 50, cy - 16), (ox + sx * 50, cy + 16), (ox + sx * 26, cy + 22)]
        fsd = sd_poly(cv, fin, margin=5)
        draw_part(cv, fsd, MAT["gold_dim"] if state != "hover" else MAT["gold"], bevel=4, height=height,
                  shadow=(sx * 1, 2, 2.5, 0.8))
        gem(cv, ox + sx * 30, cy, 7.5, MAT["aether"] if state != "disabled" else MAT["iron"],
            glow=AETHER if state in ("hover", "focus") else None, glow_sigma=6, glow_str=0.6, setting="gold", setting_w=2.2)
    if state == "focus":
        paint(cv, np.abs(shape(-3)) - 0.9, AETHER_HI, 0.85)
    if state == "disabled":
        desaturate(cv, 0.9, 0.55)
        cv.a *= 0.9
    return cv


def _mk_btn(style, state):
    return lambda: button_art(style, state)


for _style, _spec in BTN.items():
    for _st in STATES:
        FRAMES[f"{_style}_{_st}"] = (_mk_btn(_style, _st), dict(
            margins=[44, 40, 44, 40], use=f"{_spec['use']} State: {_st}. Transparent 12px pad around the art holds the focus glow.",
            scale=0.5, content_margins=[40, 26, 40, 26], expand_margins=[12, 12, 12, 12]))

for _st in STATES:
    FRAMES[f"button_menu_{_st}"] = ((lambda s: (lambda: menu_button_art(s)))(_st), dict(
        margins=[72, 44, 72, 44], use=f"Main-menu wide banner button. State: {_st}" + (" (aether glow line)" if _st in ("hover", "focus") else "") + ".",
        scale=0.5, content_margins=[72, 24, 72, 24], expand_margins=[14, 14, 14, 14], stretch="h"))


# ------------------------------------------------------------------------------------------ tabs

def tab_art(state):
    W, H = 256, 88
    cv = Canvas(W, H)
    pad = 6
    sel = state == "selected"
    bottom = H + 10
    pts = [(pad, bottom), (pad, 30), (pad + 22, pad + 4), (W - pad - 22, pad + 4), (W - pad, 30), (W - pad, bottom)]
    outer = sd_poly(cv, pts, margin=12)
    ipts = [(pad + 6, bottom + 6), (pad + 6, 32), (pad + 25, pad + 10), (W - pad - 25, pad + 10), (W - pad - 6, 32), (W - pad - 6, bottom + 6)]
    inner = sd_poly(cv, ipts, margin=12)
    cv.shadow(cov(cv, outer), 0, -1, 3, 0.6)
    if sel:
        body = vgrad(cv, pad, H, [(0, "#2a2019"), (0.5, "#1a1411"), (1, "#15100d")])
    elif state == "hover":
        body = vgrad(cv, pad, H, [(0, "#2a211b"), (1, "#110d0b")])
    else:
        body = vgrad(cv, pad, H, [(0, "#1a1512"), (1, "#0b0908")])
    n = canvas_noise(cv, 27, 2.0)
    cv.over(body * (1 + n[..., None] * 0.04), cov(cv, outer))
    rim = sub(outer, inner)
    mat = MAT["gold"] if sel else (MAT["bronze"] if state == "hover" else MAT["gold_dim"])
    cv.put(metal(cv, rim, mat, bevel=4.5, bright=1.0 if state != "normal" else 0.85))
    if sel:
        aether_channel(cv, np.abs(sd_stroke(cv, [(pad + 32, pad + 15), (W - pad - 32, pad + 15)], 0)), core=0.9,
                       glow_sigma=3.5, strength=0.9)
        f = np.clip((cv.Y - (H - 26)) / 26, 0, 1) * cov(cv, inner)
        cv.over("#15100d", f, 0.9)
    else:
        f = np.clip((cv.Y - (H - 18)) / 18, 0, 1)
        cv.over("#000000", f * cv.a, 0.5)
    if state == "hover":
        g = np.clip(1 - (cv.Y - pad - 8) / 30, 0, 1) * cov(cv, inner)
        cv.over("#ffc080", g ** 2, 0.12)
    for sx, ox in ((1, pad + 22), (-1, W - pad - 22)):
        diamond(cv, ox + sx * 2, pad + 6, 5, mat="gold" if sel else "gold_dim")
    return cv


for _st, _use in (("normal", "Unselected tab (sits behind the panel)."), ("hover", "Hovered tab."),
                  ("selected", "Selected tab: open bottom that joins the panel below (fades to #15100d, the panel_main body colour).")):
    FRAMES[f"tab_{_st}"] = ((lambda s: (lambda: tab_art(s)))(_st), dict(margins=[40, 40, 40, 20], use=_use, scale=0.5,
                                                                        content_margins=[32, 22, 32, 10], stretch="h"))


# ------------------------------------------------------------------------------------------ controls

def _socket(cv, S, pad, r=8, rim="bronze"):
    outer = sd_rect(cv, pad, pad, S - pad, S - pad, r)
    inner = sd_rect(cv, pad + 6, pad + 6, S - pad - 6, S - pad - 6, max(r - 4, 2))
    cv.shadow(cov(cv, outer), 0, 2, 2.5, 0.7)
    cv.over("#0c0908", cov(cv, outer))
    inner_shadow(cv, inner, 12, op=0.8)
    cv.put(metal(cv, sub(outer, inner), MAT[rim], bevel=4))
    return inner


@reg("checkbox_off", None, "Checkbox, unchecked (64x64 at 2x -> 32 px).")
def checkbox_off():
    cv = Canvas(64, 64)
    _socket(cv, 64, 6)
    for (x, y) in ((12, 12), (52, 12), (12, 52), (52, 52)):
        stud(cv, x, y, 1.8, "gold_dim", shadow=False)
    return cv


@reg("checkbox_on", None, "Checkbox, checked: gold check with aether glow.")
def checkbox_on():
    cv = Canvas(64, 64)
    inner = _socket(cv, 64, 6)
    cv.over(AETHER, np.clip(1 + inner / 14, 0, 1) * cov(cv, inner), 0.18)
    chk = sd_stroke(cv, [(18, 33), (28, 44), (48, 18)], 8.5)
    cv.glow(cov(cv, chk), AETHER, 4, 0.8, gain=1.4)
    draw_part(cv, chk, MAT["gold"], bevel=4, kind="chisel", shadow=(1, 2, 2, 0.8))
    return cv


@reg("slider_track", (18, 14, 18, 14), "Horizontal slider groove (stretch horizontally).", content_margins=[10, 8, 10, 8], stretch="h")
def slider_track():
    W, H = 256, 36
    cv = Canvas(W, H)
    outer = sd_rect(cv, 4, 6, W - 4, H - 6, 12)
    inner = sd_rect(cv, 8, 10, W - 8, H - 10, 8)
    cv.over("#070606", cov(cv, outer))
    inner_shadow(cv, inner, 8, op=0.9)
    cv.put(metal(cv, sub(outer, inner), MAT["bronze"], bevel=3, height=-1))
    paint(cv, np.abs(sd_rect(cv, 3, 5, W - 3, H - 5, 13)) - 0.6, "#000000", 0.8)
    return cv


@reg("slider_fill", (18, 14, 18, 14), "Slider filled portion (aether energy; draw inside slider_track with the same margins).",
     content_margins=[10, 8, 10, 8], stretch="h")
def slider_fill():
    W, H = 256, 36
    cv = Canvas(W, H)
    inner = sd_rect(cv, 8, 10, W - 8, H - 10, 8)
    m = cov(cv, inner)
    cv.glow(m, AETHER, 3, 0.5)
    body = vgrad(cv, 10, H - 10, [(0, "#d8fdff"), (0.35, "#7ff3ff"), (0.7, "#1a90a8"), (1, "#0a4a5a")])
    cv.over(body, m)
    cv.over("#ffffff", np.clip(1 - np.abs(cv.Y - 13.5) / 1.6, 0, 1) * m, 0.6)
    return cv


def grabber_art(hover):
    W, H = 48, 56
    cv = Canvas(W, H)
    cx, cy = W / 2, H / 2
    body = [(cx, 4), (cx + 18, cy - 6), (cx + 18, cy + 8), (cx, H - 4), (cx - 18, cy + 8), (cx - 18, cy - 6)]
    sd = sd_poly(cv, body, margin=4)
    if hover:
        cv.glow(cov(cv, sd), AETHER, 4, 0.7, gain=1.4)
    draw_part(cv, sd, MAT["gold" if hover else "gold_dim"], bevel=6, kind="chisel", shadow=(0.8, 2, 2, 0.8))
    gem(cv, cx, cy + 1, 7, MAT["aether"], glow=AETHER if hover else None, glow_sigma=4, glow_str=0.6, setting=None)
    return cv


FRAMES["slider_grabber"] = (lambda: grabber_art(False), dict(margins=None, use="Slider handle (48x56 at 2x).", scale=0.5))
FRAMES["slider_grabber_hover"] = (lambda: grabber_art(True), dict(margins=None, use="Slider handle, hovered/dragged.", scale=0.5))


@reg("scroll_track", (8, 20, 8, 20), "Vertical scrollbar groove (stretch vertically).", content_margins=[4, 8, 4, 8], stretch="v")
def scroll_track():
    W, H = 28, 256
    cv = Canvas(W, H)
    outer = sd_rect(cv, 4, 4, W - 4, H - 4, 10)
    inner = sd_rect(cv, 8, 8, W - 8, H - 8, 6)
    cv.over("#080707", cov(cv, outer))
    inner_shadow(cv, inner, 6, op=0.9)
    cv.put(metal(cv, sub(outer, inner), MAT["iron_warm"], bevel=3, height=-1))
    return cv


@reg("scroll_grabber", (8, 26, 8, 26), "Vertical scrollbar thumb (stretch vertically).", content_margins=[4, 8, 4, 8], stretch="v")
def scroll_grabber():
    W, H = 28, 128
    cv = Canvas(W, H)
    sd = sd_rect(cv, 6, 6, W - 6, H - 6, 8)
    draw_part(cv, sd, MAT["bronze"], bevel=5, shadow=(0.5, 1.5, 1.5, 0.8), noise=canvas_noise(cv, 3, 2), noise_amt=0.04)
    for y in (18, H - 18):
        diamond(cv, W / 2, y, 4, 5, mat="gold")
    return cv


@reg("dropdown_arrow", None, "Gold chevron for OptionButton / dropdowns (32x32 at 2x).")
def dropdown_arrow():
    cv = Canvas(32, 32)
    sd = sd_stroke(cv, [(8, 12), (16, 21), (24, 12)], 5.2)
    draw_part(cv, sd, MAT["gold"], bevel=2.6, kind="chisel", shadow=(0.5, 1.2, 1.2, 0.8))
    return cv


def lineedit_art(focus):
    W, H = 256, 64
    cv = Canvas(W, H)
    outer = sd_rect(cv, 4, 4, W - 4, H - 4, 8)
    inner = sd_rect(cv, 8, 8, W - 8, H - 8, 5)
    if focus:
        cv.glow(cov(cv, outer), AETHER, 4, 0.55, gain=1.3)
    cv.over("#0a0807", cov(cv, outer))
    inner_shadow(cv, inner, 12, op=0.85)
    if focus:
        cv.put(metal(cv, sub(outer, inner), MAT["aether"], bevel=2.5, height=-1, bright=0.8))
        paint(cv, np.abs(sd_rect(cv, 9.5, 9.5, W - 9.5, H - 9.5, 4)) - 0.5, AETHER_HI, 0.5)
    else:
        cv.put(metal(cv, sub(outer, inner), MAT["bronze"], bevel=2.5, height=-1))
    return cv


FRAMES["lineedit"] = (lambda: lineedit_art(False), dict(margins=[20, 20, 20, 20], use="Text field.", scale=0.5,
                                                          content_margins=[16, 12, 16, 12], stretch="h"))
FRAMES["lineedit_focus"] = (lambda: lineedit_art(True), dict(margins=[20, 20, 20, 20], use="Text field with focus (aether rim).",
                                                               scale=0.5, content_margins=[16, 12, 16, 12], stretch="h"))


@reg("separator_h", (112, 0, 112, 0), "Filigree horizontal divider: ornate ends, uniform gold rule in the middle (stretch horizontally only).", stretch="h")
def separator_h():
    W, H = 512, 32
    cv = Canvas(W, H)
    cy = H / 2
    rule = sd_stroke(cv, [(70, cy), (W - 70, cy)], 3.0)
    draw_part(cv, rule, MAT["gold_dim"], bevel=1.5, shadow=(0, 1, 1.2, 0.8))
    paint(cv, sd_stroke(cv, [(80, cy + 4.5), (W - 80, cy + 4.5)], 0.9), "#6a5234", 0.6)
    paint(cv, sd_stroke(cv, [(80, cy - 4.5), (W - 80, cy - 4.5)], 0.9), "#6a5234", 0.6)
    for sx, ox in ((1, 0), (-1, W)):
        sds = [sd_poly(cv, leaf((ox + sx * 6, cy), (ox + sx * 46, cy), 7), margin=3)]
        for sy in (1, -1):
            curl = catmull([(ox + sx * 40, cy), (ox + sx * 60, cy - sy * 9), (ox + sx * 82, cy - sy * 8), (ox + sx * 92, cy - sy * 2)], 8)
            sds.append(sd_stroke(cv, curl, 3.2, 1.3))
        draw_part(cv, union(*sds), MAT["gold"], bevel=1.8, shadow=(0.4, 1, 1, 0.7))
        diamond(cv, ox + sx * 100, cy, 5, 7, mat="gold")
        gem(cv, ox + sx * 48, cy, 3.6, MAT["aether"], glow=AETHER, glow_sigma=3, glow_str=0.5, setting="gold", setting_w=1.4)
    return cv


def close_art(hover):
    cv = Canvas(64, 64)
    cx = cy = 32
    ring = sd_circle(cv, cx, cy, 26)
    if hover:
        cv.glow(cov(cv, ring), "#ff4030", 5, 0.6, gain=1.3)
    draw_part(cv, ring, MAT["bronze" if not hover else "gold"], bevel=5, shadow=(0.6, 1.5, 2, 0.8))
    well = sd_circle(cv, cx, cy, 20)
    cv.over(vgrad(cv, 12, 52, [(0, "#1a0808" if hover else "#120e0c"), (1, "#3a0c0a" if hover else "#1c1512")]), cov(cv, well))
    inner_shadow(cv, well, 6, op=0.8)
    x = union(sd_stroke(cv, [(23, 23), (41, 41)], 5.2), sd_stroke(cv, [(41, 23), (23, 41)], 5.2))
    if hover:
        cv.glow(cov(cv, x), "#ff5a3a", 3, 0.8, gain=1.4)
    draw_part(cv, x, MAT["crimson" if hover else "gold_dim"], bevel=2.6, kind="chisel", shadow=(0.4, 1, 1, 0.8))
    return cv


FRAMES["close_x"] = (lambda: close_art(False), dict(margins=None, use="Window close button (64x64 at 2x).", scale=0.5))
FRAMES["close_x_hover"] = (lambda: close_art(True), dict(margins=None, use="Window close button, hovered (red glow).", scale=0.5))
