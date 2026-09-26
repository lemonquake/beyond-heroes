"""tree/: skill & talent tree node frames (locked / available / allocated), connector, class backdrops."""
from __future__ import annotations

import math

import numpy as np

from rast import (Canvas, MAT, C, cov, sd_circle, sd_ellipse, sd_box, sd_rect, sd_chamfer_box, sd_poly, sd_stroke, union,
                  sub, inter, ring_of, shell, profile, metal, shade, groove_h, paint, gem, blur, spiral, arc, catmull, xf,
                  star, ngon, leaf, canvas_noise, fnoise, tint_mat, cmix, vgrad, rgrad, desaturate, ramp, even_ramp, F)
from raster_orn import aether_channel, draw_part, inner_shadow, hammered, rune_strokes, AETHER, AETHER_HI
from raster_frames import stud, diamond

TREE = {}

STATE_MAT = {"locked": "iron", "available": "bronze", "allocated": "gold"}


def _finish(cv, ring_sd, state, inner_sd, gems=()):
    """Shared state styling: glow + channel for allocated, faint aether rim for available, dim iron for locked."""
    mat = MAT[STATE_MAT[state]]
    if state == "allocated":
        cv.glow(cov(cv, ring_sd), AETHER, 5, 0.65, gain=1.5)
    draw_part(cv, ring_sd, mat, bevel=4.5, shadow=(0.8, 2, 2.5, 0.85), extra_h=hammered(cv, 3, 0.04),
              noise=canvas_noise(cv, 5, 2), noise_amt=0.02, bright=0.85 if state == "locked" else 1.0)
    edge = np.abs(inner_sd) - 0.8
    if state == "allocated":
        aether_channel(cv, np.abs(inner_sd + 2.0), core=0.8, glow_sigma=3, strength=0.9)
        cv.over(AETHER, np.clip(1 + inner_sd / 14, 0, 1) ** 2 * cov(cv, inner_sd), 0.25)
    elif state == "available":
        paint(cv, np.abs(inner_sd + 2.0) - 0.6, AETHER, 0.45)
    else:
        paint(cv, edge, "#000000", 0.9)
    for (x, y, r) in gems:
        if state == "allocated":
            gem(cv, x, y, r, MAT["aether"], glow=AETHER, glow_sigma=r * 0.9, glow_str=0.6, setting="gold", setting_w=r * 0.35)
        elif state == "available":
            gem(cv, x, y, r, MAT["aether"], setting="bronze", setting_w=r * 0.35)
        else:
            gem(cv, x, y, r, MAT["iron"], setting="iron", setting_w=r * 0.35)
    if state == "locked":
        desaturate(cv, 0.7, 0.8)
    return cv


def node_minor(state):
    S, c = 96, 48
    cv = Canvas(S, S)
    ring = sub(sd_circle(cv, c, c, 42), sd_circle(cv, c, c, 32))
    return _finish(cv, ring, state, sd_circle(cv, c, c, 32))


def node_major(state):
    S, c = 128, 64
    cv = Canvas(S, S)
    rot = -math.pi / 2 + math.pi / 8
    ring = sub(sd_poly(cv, ngon(c, c, 58, 8, rot), margin=4), sd_poly(cv, ngon(c, c, 45, 8, rot), margin=4))
    gems = [(c + 51.5 * math.cos(a), c + 51.5 * math.sin(a), 3.6) for a in (-math.pi / 2, 0, math.pi / 2, math.pi)]
    return _finish(cv, ring, state, sd_poly(cv, ngon(c, c, 45, 8, rot), margin=4), gems)


def node_keystone(state):
    S, c = 192, 96
    cv = Canvas(S, S)
    # sunburst behind the ring
    rays = []
    for i in range(16):
        a = -math.pi / 2 + i * math.pi / 8
        L = 94 if i % 2 == 0 else 82
        w = 0.16 if i % 2 == 0 else 0.12
        rays.append(sd_poly(cv, [(c + 64 * math.cos(a - w), c + 64 * math.sin(a - w)), (c + L * math.cos(a), c + L * math.sin(a)),
                                 (c + 64 * math.cos(a + w), c + 64 * math.sin(a + w))], margin=3))
    rsd = union(*rays)
    mat = MAT[STATE_MAT[state]]
    if state == "allocated":
        cv.glow(cov(cv, rsd), AETHER, 8, 0.5, gain=1.3)
    draw_part(cv, rsd, mat, bevel=6, kind="chisel", shadow=(0.8, 2, 3, 0.85), bright=0.9 if state == "locked" else 1.0)
    ring = sub(sd_circle(cv, c, c, 74), sd_circle(cv, c, c, 58))
    inner = sd_circle(cv, c, c, 58)
    # second decorative ring with rune ticks
    gems = [(c + 66 * math.cos(a), c + 66 * math.sin(a), 5.2) for a in (-math.pi / 2, 0, math.pi / 2, math.pi)]
    _finish(cv, ring, state, inner, gems)
    ticks = [sd_stroke(cv, [(c + 61 * math.cos(a), c + 61 * math.sin(a)), (c + 71 * math.cos(a), c + 71 * math.sin(a))], 0.9)
             for a in np.linspace(0, 2 * math.pi, 48, endpoint=False) if abs(math.sin(2 * a)) > 0.18]
    paint(cv, union(*ticks), "#000000", 0.55)
    return cv


def node_skill(state):
    S = 144
    cv = Canvas(S, S)
    outer = sd_chamfer_box(cv, 72, 72, 66, 66, 14)
    inner = sd_rect(cv, 20, 20, S - 20, S - 20, 4)
    ring = sub(outer, inner)
    gems = [(72, 13, 4.5), (72, S - 13, 4.5)]
    _finish(cv, ring, state, inner, gems)
    for (ox, oy, sx, sy) in ((6, 6, 1, 1), (S - 6, 6, -1, 1), (6, S - 6, 1, -1), (S - 6, S - 6, -1, -1)):
        diamond(cv, ox + sx * 9, oy + sy * 9, 5.5, mat="gold" if state == "allocated" else ("bronze" if state == "available" else "iron"))
    return cv


def node_upgrade(state):
    S, c = 112, 56
    cv = Canvas(S, S)
    outer = sd_poly(cv, [(c, 3), (S - 3, c), (c, S - 3), (3, c)], margin=4)
    inner = sd_poly(cv, [(c, 18), (S - 18, c), (c, S - 18), (18, c)], margin=4)
    gems = [(c, 10, 3.4), (c, S - 10, 3.4)]
    return _finish(cv, sub(outer, inner), state, inner, gems)


NODES = {
    "node_minor": (node_minor, "Minor talent node, circle (96x96 at 2x -> 48 px). Transparent disc r=32 at the centre for the icon.", dict(icon_radius=32)),
    "node_major": (node_major, "Major talent node, octagon (128x128 at 2x -> 64 px). Transparent octagon r=45.", dict(icon_radius=45)),
    "node_keystone": (node_keystone, "Keystone node, sunburst + ring (192x192 at 2x -> 96 px). Transparent disc r=58.", dict(icon_radius=58)),
    "node_skill": (node_skill, "Skill node, square bezel (144x144 at 2x -> 72 px). Transparent window (20,20)-(124,124).", dict(icon_rect=[20, 20, 104, 104])),
    "node_upgrade": (node_upgrade, "Skill upgrade node, diamond (112x112 at 2x -> 56 px). Transparent diamond inset 18 px.", dict(icon_radius=38)),
}
for _n, (_fn, _use, _extra) in NODES.items():
    for _st in ("locked", "available", "allocated"):
        TREE[f"{_n}_{_st}"] = ((lambda f, s: (lambda: f(s)))(_fn, _st), dict(margins=None, use=f"{_use} State: {_st}.", scale=0.5, **_extra))


def connector():
    W, H = 128, 32
    cv = Canvas(W, H)
    cy = H / 2
    n = fnoise(cv.H, cv.W, 3, beta=2.0, lo=1)   # periodic in x -> tiles seamlessly
    groove = sd_rect(cv, -10, cy - 7, W + 10, cy + 7, 3)
    h = -profile(groove, 3, "round") * 2.5 + n * 0.15
    base = dict(ramp=even_ramp(["#202020", "#5a5a5a", "#9a9a9a", "#d4d4d4", "#ffffff"]), spec="#ffffff", sp=0.3, pw=16)
    cv.put((shade(cv, h, base, flat_level=0.45), cov(cv, groove)))
    core = np.clip(1 - np.abs(cv.Y - cy) / 2.2, 0, 1)
    cv.over("#ffffff", core, 0.85)
    # periodic studs every 64 px (2 per tile)
    for x in (32, 96):
        s = sd_circle(cv, x, cy, 3.2)
        cv.put(metal(cv, s, base, bevel=3.2))
    paint(cv, np.abs(cv.Y - (cy - 7)) - 0.5 + 0 * cv.X, "#000000", 0.6)
    paint(cv, np.abs(cv.Y - (cy + 7)) - 0.5 + 0 * cv.X, "#000000", 0.6)
    return cv


TREE["connector"] = (connector, dict(margins=None, use="Tileable (x) link texture between tree nodes, grey-white: modulate grey when inactive, gold #f5cc75 / aether when active. 128x32 at 2x; repeat along the link (TextureRect tile or Line2D texture_mode TILE).",
                                     scale=0.5, tileable="x"))


# ------------------------------------------------------------------------------------------ backdrops

def backdrop(kind):
    W, H = 1600, 900
    cv = Canvas(W, H, ss=1)
    knight = kind == "knight"
    base = rgrad(cv, W / 2, H * 0.45, W * 0.75, [(0, "#1c120c" if knight else "#0e0e26"), (0.55, "#0c0807" if knight else "#07071a"),
                                                  (1, "#030202" if knight else "#020208")], sy=1.6)
    cv.over(base, np.ones((cv.H, cv.W), F))
    rng = np.random.default_rng(11 if knight else 12)
    # haze
    n1 = fnoise(H, W, 21 if knight else 22, beta=3.0, lo=1)
    n2 = fnoise(H, W, 23 if knight else 24, beta=2.2, lo=2)
    haze = np.clip(n1 * 0.5 + 0.2, 0, 1) ** 2
    if knight:
        cv.over("#6a2a10", haze, 0.16)
        cv.over("#b86a2a", np.clip(n2 * 0.4, 0, 1) ** 3, 0.08)
    else:
        cv.over("#3a2a8a", haze, 0.20)
        cv.over("#1a7a8a", np.clip(n2 * 0.4, 0, 1) ** 3, 0.12)
    line_c = "#c8964a" if knight else "#9ec8ff"
    # large engraved rings with rune ticks (centred off-axis)
    for (cx, cy, r) in ((W * 0.5, H * 0.52, 360), (W * 0.5, H * 0.52, 300), (W * 0.5, H * 0.52, 420)):
        paint(cv, np.abs(sd_circle(cv, cx, cy, r)) - 0.6, line_c, 0.11)
    ticks = []
    for a in np.linspace(0, 2 * math.pi, 96, endpoint=False):
        ticks.append(sd_stroke(cv, [(W * 0.5 + 360 * math.cos(a), H * 0.52 + 360 * math.sin(a)),
                                    (W * 0.5 + (372 if int(a * 10) % 3 == 0 else 366) * math.cos(a), H * 0.52 + (372 if int(a * 10) % 3 == 0 else 366) * math.sin(a))], 1.0))
    paint(cv, union(*ticks), line_c, 0.12)
    runes = []
    for i, a in enumerate(np.linspace(0, 2 * math.pi, 24, endpoint=False)):
        for ln in rune_strokes(rng, W * 0.5 + 395 * math.cos(a), H * 0.52 + 395 * math.sin(a), 16):
            runes.append(sd_stroke(cv, ln, 1.4))
    paint(cv, union(*runes), line_c, 0.12)
    if knight:
        # faint great sword + shield engraving
        sw = [(W / 2, 110), (W / 2 + 26, 180), (W / 2 + 22, 640), (W / 2, 690), (W / 2 - 22, 640), (W / 2 - 26, 180)]
        paint(cv, np.abs(sd_poly(cv, sw, margin=4)) - 0.8, line_c, 0.10)
        paint(cv, np.abs(sd_stroke(cv, [(W / 2 - 150, 640), (W / 2 + 150, 640)], 16)) - 0.8, line_c, 0.10)
        sh = catmull([(W / 2, 300), (W / 2 + 190, 330), (W / 2 + 180, 560), (W / 2, 760), (W / 2 - 180, 560), (W / 2 - 190, 330)], 8, closed=True)
        paint(cv, np.abs(sd_poly(cv, sh, margin=4)) - 0.8, line_c, 0.08)
    else:
        for (rx, ry, ang) in ((520, 170, -12), (470, 250, 20), (600, 120, 5)):
            pts = [(W / 2 + rx * math.cos(t) * math.cos(math.radians(ang)) - ry * math.sin(t) * math.sin(math.radians(ang)),
                    H * 0.52 + rx * math.cos(t) * math.sin(math.radians(ang)) + ry * math.sin(t) * math.cos(math.radians(ang)))
                   for t in np.linspace(0, 2 * math.pi, 180)]
            paint(cv, sd_stroke(cv, pts, 1.2), line_c, 0.11)
    # constellations
    for k in range(7):
        cx, cy = rng.uniform(120, W - 120), rng.uniform(90, H - 90)
        pts = [(cx, cy)]
        for _ in range(rng.integers(3, 6)):
            a = rng.uniform(0, 2 * math.pi)
            d = rng.uniform(40, 110)
            pts.append((pts[-1][0] + d * math.cos(a), pts[-1][1] + d * math.sin(a)))
        paint(cv, sd_stroke(cv, pts, 1.0), line_c, 0.12)
        for (x, y) in pts:
            cv.glow(cov(cv, sd_circle(cv, x, y, 2.2)), "#ffffff" if not knight else "#ffd8a0", 4, 0.5)
            paint(cv, sd_circle(cv, x, y, 1.8), "#ffffff", 0.8)
    # star dust
    for _ in range(420):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.uniform(0.4, 1.3)
        a = rng.uniform(0.1, 0.5)
        sl = cv.region(x - 3, y - 3, x + 3, y + 3, 0)
        if sl is None:
            continue
        d = np.hypot(cv.X[sl] - x, cv.Y[sl] - y)
        m = np.clip(r + 0.5 - d, 0, 1) * a
        cv.rgb[sl] = cv.rgb[sl] * (1 - m[..., None]) + C("#ffffff") * m[..., None]
    # grain + vignette
    g = fnoise(H, W, 5, beta=0.5, lo=1)
    cv.rgb = np.clip(cv.rgb * (1 + g[..., None] * 0.035), 0, 1)
    d = np.hypot((cv.X - W / 2) / (W / 2), (cv.Y - H / 2) / (H / 2))
    cv.rgb *= (1 - np.clip((d - 0.6) / 0.8, 0, 1) ** 1.5 * 0.75)[..., None]
    return cv


TREE["tree_bg_knight"] = (lambda: backdrop("knight"), dict(margins=None, use="Knight talent/skill tree backdrop (1600x900, opaque): ember haze, engraved sword + shield, rune ring, constellations. Stretch/cover.", scale=1.0))
TREE["tree_bg_mage"] = (lambda: backdrop("mage"), dict(margins=None, use="Mage talent/skill tree backdrop (1600x900, opaque): indigo nebula, orbital rings, rune ring, constellations. Stretch/cover.", scale=1.0))
