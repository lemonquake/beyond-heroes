"""hud/: HP/mana orbs, bars, boss bar, minimap frame, buff frames, vignettes, particles, cursors."""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage

from rast import (Canvas, MAT, C, cov, sd_circle, sd_ellipse, sd_box, sd_rect, sd_chamfer_box, sd_poly, sd_stroke, union,
                  sub, inter, ring_of, shell, profile, metal, shade, groove_h, paint, gem, blur, spiral, arc, bez3, catmull,
                  xf, star, ngon, leaf, canvas_noise, fnoise, tint_mat, cmix, vgrad, hgrad, rgrad, desaturate, ramp,
                  even_ramp, F)
from raster_orn import (aether_channel, draw_part, inner_shadow, hammered, AETHER, AETHER_HI, place, diag_mirror)
from raster_frames import stud, diamond

HUD = {}


def reg(name, use, margins=None, scale=0.5, **extra):
    def deco(fn):
        HUD[name] = (fn, dict(margins=margins, use=use, scale=scale, **extra))
        return fn
    return deco


# ------------------------------------------------------------------------------------------ orbs

ORB = dict(size=320, c=160, r_in=112)


def lion_crest(cv, cx, cy, s):
    """Sun-rayed medallion with a stylised lion mask."""
    rays = sd_poly(cv, star(cx, cy, 16, 40 * s, 24 * s), margin=4)
    draw_part(cv, rays, MAT["gold"], bevel=5 * s, kind="chisel", shadow=(0, 2.5, 3, 0.9))
    med = sd_circle(cv, cx, cy, 25 * s)
    draw_part(cv, med, MAT["gold_dim"], bevel=5 * s, shadow=(0, 1.5, 2, 0.8))
    field = sd_circle(cv, cx, cy, 20 * s)
    cv.put(metal(cv, field, MAT["crimson"], bevel=3 * s, height=-0.8))
    # mane: wavy star, face: shield, muzzle
    mane = sd_poly(cv, star(cx, cy + 1 * s, 11, 16 * s, 11 * s), margin=3)
    face = sd_poly(cv, catmull([(cx, cy - 10 * s), (cx + 8 * s, cy - 6 * s), (cx + 7 * s, cy + 5 * s), (cx, cy + 13 * s),
                                (cx - 7 * s, cy + 5 * s), (cx - 8 * s, cy - 6 * s)], 5, closed=True), margin=3)
    draw_part(cv, mane, MAT["gold"], bevel=3 * s, kind="chisel", shadow=(0, 1, 1.2, 0.8))
    draw_part(cv, face, MAT["gold"], bevel=3.5 * s, shadow=(0, 1, 1.2, 0.8))
    for sx in (1, -1):
        paint(cv, sd_stroke(cv, [(cx + sx * 2.2 * s, cy - 3 * s), (cx + sx * 5.5 * s, cy - 4.2 * s)], 1.6 * s), "#3a0808", 0.95)
    paint(cv, sd_poly(cv, [(cx - 3 * s, cy + 3 * s), (cx + 3 * s, cy + 3 * s), (cx, cy + 6.5 * s)], margin=2), "#5a1a0a", 0.9)
    paint(cv, sd_stroke(cv, [(cx, cy - 8 * s), (cx, cy + 2 * s)], 1.2 * s), "#7a4a10", 0.6)


def moon_crest(cv, cx, cy, s):
    rays = sd_poly(cv, star(cx, cy, 8, 40 * s, 16 * s, rot=-math.pi / 2), margin=4)
    draw_part(cv, rays, MAT["silver"], bevel=5 * s, kind="chisel", shadow=(0, 2.5, 3, 0.9))
    rays2 = sd_poly(cv, star(cx, cy, 8, 30 * s, 14 * s, rot=-math.pi / 2 + math.pi / 8), margin=4)
    draw_part(cv, rays2, MAT["silver"], bevel=4 * s, kind="chisel", shadow=(0, 1, 2, 0.7), bright=0.85)
    med = sd_circle(cv, cx, cy, 25 * s)
    draw_part(cv, med, MAT["silver"], bevel=5 * s, shadow=(0, 1.5, 2, 0.8))
    field = sd_circle(cv, cx, cy, 20 * s)
    cv.put(metal(cv, field, MAT["blue_steel"], bevel=3 * s, height=-0.8, bright=0.8))
    moon = sub(sd_circle(cv, cx - 2 * s, cy, 14 * s), sd_circle(cv, cx + 5 * s, cy - 4 * s, 12 * s))
    cv.glow(cov(cv, moon), "#9ec8ff", 3, 0.6)
    draw_part(cv, moon, MAT["silver"], bevel=3 * s, shadow=(0, 1, 1, 0.8))
    st = sd_poly(cv, star(cx + 8 * s, cy + 3 * s, 4, 7 * s, 1.8 * s), margin=2)
    cv.glow(cov(cv, st), AETHER, 2.5, 0.8, gain=1.5)
    paint(cv, st, AETHER_HI)


def orb_frame(kind):
    S, c, r = ORB["size"], ORB["c"], ORB["r_in"]
    cv = Canvas(S, S)
    hp = kind == "hp"
    acc = tint_mat("#b81a1a" if hp else "#3373f2", sp=0.6)
    trim = MAT["gold"] if hp else MAT["silver"]
    trim_dim = MAT["bronze"] if hp else MAT["blue_steel"]
    glow_c = "#ff3a2a" if hp else "#5aa0ff"
    # lower wings
    wings = []
    for sx in (1, -1):
        for (r0, a0, a1, w0, w1) in ((142, 20, 88, 14, 3), (150, 34, 80, 7, 2)):
            angs = np.linspace(math.radians(a0), math.radians(a1), 28)
            pts = [(c + sx * r0 * math.cos(a), c + r0 * math.sin(a)) for a in angs]
            wings.append(sd_stroke(cv, pts[::-1], w0, w1))
        # feather blades hanging off the lower arc
        for i, a in enumerate(np.linspace(math.radians(24), math.radians(72), 5)):
            p0 = (c + sx * 134 * math.cos(a), c + 134 * math.sin(a))
            p1 = (c + sx * (158 - i * 1.5) * math.cos(a), c + (158 - i * 1.5) * math.sin(a) + 2)
            wings.append(sd_poly(cv, leaf(p0, p1, 9, bend=2 * sx), margin=3))
    wsd = union(*wings)
    draw_part(cv, wsd, trim, bevel=3, shadow=(0, 2.5, 3, 0.85))
    # iron ring
    outer = sd_circle(cv, c, c, 138)
    band = sub(outer, sd_circle(cv, c, c, r))
    eh = hammered(cv, 31, 0.35)
    ticks = []
    for i in range(36):
        a = i * math.pi / 18
        if i % 9 == 0:
            continue
        ticks.append(sd_stroke(cv, [(c + 121 * math.cos(a), c + 121 * math.sin(a)), (c + 131 * math.cos(a), c + 131 * math.sin(a))], 0))
    eh = eh + groove_h(cv, union(*ticks), 2.2, 1.3)
    draw_part(cv, band, MAT["iron"], bevel=10, extra_h=eh, shadow=(0, 4, 6, 0.9), noise=canvas_noise(cv, 7, 1.5), noise_amt=0.05)
    # energy channel ring inside the iron
    aether_channel(cv, np.abs(sd_circle(cv, c, c, 117.5)), core=1.0, glow_sigma=3.5, strength=0.9, color=glow_c,
                   core_color="#ffd0c8" if hp else "#d8ecff")
    draw_part(cv, ring_of(sd_circle(cv, c, c, r + 1.5), 5), trim, bevel=2.5, shadow=None)
    draw_part(cv, ring_of(sd_circle(cv, c, c, 137), 4.5), trim_dim, bevel=2.2, shadow=(0, 1, 1.5, 0.7))
    # cardinal studs and gems on the ring
    for i, deg in enumerate((180, 0, 135, 45)):
        a = math.radians(deg)
        x, y = c + 128 * math.cos(a), c + 128 * math.sin(a)
        if deg in (180, 0):
            dsd = sd_poly(cv, [(x, y - 16), (x + 12, y), (x, y + 16), (x - 12, y)], margin=3)
            draw_part(cv, dsd, trim, bevel=5, kind="chisel", shadow=(0, 2, 2, 0.8))
            gem(cv, x, y, 6, MAT["ruby"] if hp else MAT["blue_steel"], glow=glow_c, glow_sigma=5, glow_str=0.5, setting=None)
        else:
            stud(cv, x, y, 4.5, mat="gold" if hp else "silver")
    # bottom keystone with aether gem
    ks = sd_poly(cv, [(c - 20, c + 128), (c + 20, c + 128), (c + 12, c + 154), (c, c + 158), (c - 12, c + 154)], margin=4)
    draw_part(cv, ks, trim, bevel=5, shadow=(0, 2, 3, 0.85))
    gem(cv, c, c + 140, 7.5, MAT["aether"], glow=AETHER, glow_sigma=6, glow_str=0.55, setting="gold" if hp else "silver", setting_w=2.2)
    # top crest
    if hp:
        lion_crest(cv, c, 30, 1.0)
    else:
        moon_crest(cv, c, 30, 1.0)
    return cv


HUD["orb_frame_hp"] = (lambda: orb_frame("hp"), dict(margins=None, use="HP orb frame (320x320 at 2x). Transparent interior circle centre (160,160) r=112; draw liquid + orb_glass under/over it. Sun-and-lion crest.",
                                                    scale=0.5, orb_center=[160, 160], orb_radius=112))
HUD["orb_frame_mana"] = (lambda: orb_frame("mana"), dict(margins=None, use="Mana orb frame (320x320 at 2x), blue/silver with a moon-and-star crest. Interior centre (160,160) r=112.",
                                                        scale=0.5, orb_center=[160, 160], orb_radius=112))


@reg("orb_glass", "Glass overlay drawn above the orb liquid and below orb_frame_*: specular highlight, rim shade, bottom caustic. Same 320 canvas, circle (160,160) r=112.",
     orb_center=[160, 160], orb_radius=112)
def orb_glass():
    S, c, r = ORB["size"], ORB["c"], ORB["r_in"] + 2
    cv = Canvas(S, S)
    disc = sd_circle(cv, c, c, r)
    m = cov(cv, disc)
    d = np.hypot(cv.X - c, cv.Y - c) / r
    cv.over("#000000", np.clip((d - 0.55) / 0.45, 0, 1) ** 2.2 * m, 0.75)     # rim shading
    # big soft specular crescent top-left
    hl = sub(sd_ellipse(cv, c - 26, c - 46, 70, 46), sd_ellipse(cv, c - 10, c - 22, 80, 54))
    cv.over("#ffffff", blur(cv, cov(cv, hl), 4) * m, 0.45)
    cv.over("#ffffff", cov(cv, sd_ellipse(cv, c - 50, c - 60, 16, 10), soft=3) * m, 0.65)
    # thin rim light bottom-right + caustic
    rim = np.clip(1 - np.abs(d - 0.96) / 0.03, 0, 1) * np.clip((cv.X - c + cv.Y - c) / (r * 1.2), 0, 1)
    cv.over("#ffffff", rim * m, 0.35)
    ca = sd_ellipse(cv, c + 10, c + 84, 44, 12)
    cv.over("#ffffff", blur(cv, cov(cv, ca), 5) * m, 0.18)
    return cv


@reg("orb_liquid_noise", "Tileable 256x256 grayscale swirl noise for the orb liquid shader (sample with UV scroll/rotation). Not scaled.",
     scale=1.0, tileable=True)
def orb_liquid_noise():
    N = 256
    base = fnoise(N, N, 5, beta=2.6, lo=1)
    wx = fnoise(N, N, 6, beta=3.0, lo=1) * 14
    wy = fnoise(N, N, 7, beta=3.0, lo=1) * 14
    yy, xx = np.mgrid[0:N, 0:N].astype(F)
    # swirl: rotate the warp field locally
    warped = ndimage.map_coordinates(base, [yy + wy, xx + wx], order=3, mode="wrap")
    fine = fnoise(N, N, 8, beta=1.8, lo=4)
    fine_w = ndimage.map_coordinates(fine, [yy + wy * 0.6, xx + wx * 0.6], order=3, mode="wrap")
    v = warped * 0.75 + fine_w * 0.35
    v = (v - v.min()) / (v.max() - v.min())
    v = np.clip((v - 0.5) * 1.25 + 0.5, 0, 1)
    return ("gray", v)


# ------------------------------------------------------------------------------------------ bars

def bar_frame(W, H, win, cap_w, style="resource"):
    """Horizontal bar frame with a transparent window win=(y0,y1); ornate caps inside cap_w px on each end."""
    cv = Canvas(W, H)
    y0, y1 = win
    cy = (y0 + y1) / 2
    ht = (y1 - y0) / 2
    t = {"resource": 7, "xp": 4, "boss": 9, "target": 6}[style]
    outer = sd_rect(cv, cap_w * 0.35, y0 - t, W - cap_w * 0.35, y1 + t, t + 2)
    inner = sd_rect(cv, cap_w * 0.35 + t, y0, W - cap_w * 0.35 - t, y1, 2)
    band = sub(outer, inner)
    draw_part(cv, band, MAT["iron"], bevel=t * 0.8, shadow=(0, 2, 3, 0.8), extra_h=hammered(cv, 5, 0.2),
              noise=canvas_noise(cv, 9, 1.5), noise_amt=0.05)
    draw_part(cv, ring_of(sd_rect(cv, cap_w * 0.35 + t - 1, y0 - 1, W - cap_w * 0.35 - t + 1, y1 + 1, 3), 2.2),
              MAT["gold_dim"], bevel=1.2, shadow=None)
    # subtle inner shadow at the top of the window (drawn over the fill)
    top = np.clip(1 - (cv.Y - y0) / (ht * 0.7), 0, 1) * cov(cv, inner)
    cv.over("#000000", top ** 2, 0.45)
    for sx, ox in ((1, 0), (-1, W)):
        if style == "xp":
            cap = [(ox + sx * 4, cy), (ox + sx * 18, y0 - t - 2), (ox + sx * 40, y0 - t), (ox + sx * 40, y1 + t), (ox + sx * 18, y1 + t + 2)]
            draw_part(cv, sd_poly(cv, cap, margin=4), MAT["gold_dim"], bevel=3, shadow=(sx, 1.5, 2, 0.8))
            diamond(cv, ox + sx * 22, cy, 4, 6, mat="gold")
        elif style in ("resource", "target"):
            cap = [(ox + sx * 6, cy), (ox + sx * 24, y0 - t - 8), (ox + sx * (cap_w - 4), y0 - t), (ox + sx * (cap_w - 4), y1 + t),
                   (ox + sx * 24, y1 + t + 8)]
            draw_part(cv, sd_poly(cv, cap, margin=4), MAT["gold_dim"], bevel=4, shadow=(sx, 2, 2.5, 0.85),
                      noise=canvas_noise(cv, 3, 2), noise_amt=0.05)
            for sy in (1, -1):
                curl = catmull([(ox + sx * 20, cy + sy * (ht + t + 4)), (ox + sx * 36, cy + sy * (ht + t + 10)), (ox + sx * 52, cy + sy * (ht + t + 7))], 6)
                draw_part(cv, sd_stroke(cv, curl, 4, 1.6), MAT["gold"], bevel=1.8, shadow=(0.5, 1, 1, 0.7))
            gem(cv, ox + sx * 30, cy, min(8, ht + 2), MAT["aether"], glow=AETHER, glow_sigma=5, glow_str=0.5, setting="gold", setting_w=2.2)
        elif style == "boss":
            boss_cap(cv, ox, sx, cy, ht, t, cap_w)
    return cv


def boss_cap(cv, ox, sx, cy, ht, t, cap_w):
    # horned skull end-cap
    x = ox + sx * 84
    plate = [(ox + sx * 30, cy), (ox + sx * 60, cy - 44), (ox + sx * 150, cy - ht - t - 4), (ox + sx * (cap_w - 6), cy - ht - t),
             (ox + sx * (cap_w - 6), cy + ht + t), (ox + sx * 150, cy + ht + t + 4), (ox + sx * 60, cy + 44)]
    draw_part(cv, sd_poly(cv, plate, margin=6), MAT["iron_warm"], bevel=6, shadow=(sx * 1.5, 3, 4, 0.9),
              extra_h=hammered(cv, 13, 0.3), noise=canvas_noise(cv, 3, 2), noise_amt=0.05)
    edge = ring_of(sd_poly(cv, plate, margin=6), 3.5)
    draw_part(cv, edge, MAT["bronze"], bevel=1.8, shadow=None)
    # horns curving back and up/down
    for sy in (1, -1):
        hp = catmull([(x + sx * 4, cy + sy * 20), (x - sx * 12, cy + sy * 44), (x - sx * 42, cy + sy * 54), (x - sx * 66, cy + sy * 46)], 10)
        horn = sd_stroke(cv, hp, 17, 1.5)
        h = profile(horn, 6, "round") * 6
        rgb = shade(cv, h, tint_mat("#d8c8a0", sp=0.4))
        t_ = np.clip((np.abs(cv.X - x) - 10) / 60, 0, 1)
        rgb = rgb * (1 - t_[..., None] * 0.55)
        cv.shadow(cov(cv, horn), 0, 2, 3, 0.85)
        cv.put((rgb, cov(cv, horn)))
        for k in range(1, 5):
            p = hp[k * 7]
            paint(cv, np.abs(sd_circle(cv, p[0], p[1], 7 - k)) - 0.4, "#5a4a30", 0.5)
    # skull
    sk = union(sd_ellipse(cv, x, cy - 4, 22, 20), sd_rect(cv, x - 12, cy + 6, x + 12, cy + 22, 4))
    h = profile(sk, 7, "round") * 7
    cv.shadow(cov(cv, sk), 0, 2, 3, 0.9)
    cv.put((shade(cv, h, tint_mat("#e0d4b8", sp=0.35)), cov(cv, sk)))
    for ex in (-8, 8):
        e = sd_ellipse(cv, x + ex, cy - 2, 6, 5.5)
        paint(cv, e, "#0a0404")
        cv.glow(cov(cv, sd_circle(cv, x + ex, cy - 1.5, 2.5)), "#ff3020", 3, 0.9, gain=2)
        paint(cv, sd_circle(cv, x + ex, cy - 1.5, 1.6), "#ffb080")
    paint(cv, sd_poly(cv, [(x - 3, cy + 9), (x + 3, cy + 9), (x, cy + 4)], margin=2), "#1a0c08")
    for tx in (-7.5, -2.5, 2.5, 7.5):
        paint(cv, sd_stroke(cv, [(x + tx, cy + 14), (x + tx, cy + 21)], 1.1), "#2a1a10", 0.9)


HUD["bar_frame_resource"] = (lambda: bar_frame(512, 72, (26, 46), 72, "resource"), dict(
    margins=[76, 0, 76, 0], use="Class resource bar frame (rage/arcane): ornate gem ends; transparent window y 26..46 between x 32..480. Stretch horizontally; draw bar_fill under it.",
    scale=0.5, window=[32, 26, 480, 46], stretch="h"))
HUD["bar_frame_xp"] = (lambda: bar_frame(1024, 28, (9, 19), 44, "xp"), dict(
    margins=[48, 0, 48, 0], use="Long thin XP bar frame; transparent window y 9..19. 9-slice horizontally.",
    scale=0.5, window=[19, 9, 1005, 19], stretch="h"))
HUD["bar_frame_boss"] = (lambda: bar_frame(1024, 136, (54, 82), 176, "boss"), dict(
    margins=[180, 0, 180, 0], use="Boss health bar frame with horned-skull end caps; transparent window y 54..82. Stretch horizontally.",
    scale=0.5, window=[71, 54, 953, 82], stretch="h"))
HUD["bar_frame_target"] = (lambda: bar_frame(512, 64, (22, 42), 64, "target"), dict(
    margins=[68, 0, 68, 0], use="Small target/enemy frame bar; transparent window y 22..42.", scale=0.5, window=[28, 22, 484, 42],
    stretch="h"))


@reg("bar_fill", "White bar fill with a subtle vertical gradient + top gloss; tint (modulate) per resource. Stretch freely.",
     margins=[4, 0, 4, 0], stretch="h")
def bar_fill():
    W, H = 256, 32
    cv = Canvas(W, H)
    rgb = vgrad(cv, 0, H, [(0, "#ffffff"), (0.18, "#f4f4f4"), (0.5, "#d0d0d0"), (0.85, "#9a9a9a"), (1, "#7a7a7a")])
    cv.over(rgb, np.ones((cv.H, cv.W), F))
    cv.over("#ffffff", np.clip(1 - np.abs(cv.Y - 6) / 2.5, 0, 1), 0.55)
    n = canvas_noise(cv, 3, 2.0, scale=4)
    cv.rgb *= (1 + n[..., None] * 0.03)
    return cv


def pip(full):
    cv = Canvas(48, 48)
    c = 24
    dia = sd_poly(cv, [(c, 3), (45, c), (c, 45), (3, c)], margin=3)
    well = sd_poly(cv, [(c, 10), (38, c), (c, 38), (10, c)], margin=3)
    draw_part(cv, sub(dia, well), MAT["gold_dim" if not full else "gold"], bevel=4, kind="chisel", shadow=(0.5, 1.5, 1.5, 0.8))
    if full:
        cv.glow(cov(cv, well), "#b890ff", 5, 0.9, gain=1.6)
        cv.put(metal(cv, well, MAT["violet"], bevel=10, kind="chisel"))
        cv.over("#ffffff", cov(cv, sd_poly(cv, star(c, c, 4, 7, 1.6), margin=2), soft=0.3), 0.9)
    else:
        cv.over("#07050a", cov(cv, well))
        inner_shadow(cv, well, 6, 0.8)
    return cv


HUD["pip_empty"] = (lambda: pip(False), dict(margins=None, use="Arcane charge pip, empty socket (48x48 at 2x).", scale=0.5))
HUD["pip_full"] = (lambda: pip(True), dict(margins=None, use="Arcane charge pip, charged (violet gem with glow).", scale=0.5))


# ------------------------------------------------------------------------------------------ minimap

@reg("minimap_frame", "Circular minimap frame (400x400 at 2x). Transparent interior centre (200,200) r=150; compass spikes, north gem at top.",
     map_center=[200, 200], map_radius=150)
def minimap_frame():
    S, c = 400, 200
    cv = Canvas(S, S)
    R0, R1 = 150, 174
    sp = []
    for deg, L, w in ((270, 197, 30), (0, 192, 22), (90, 192, 22), (180, 192, 22), (315, 186, 14), (45, 186, 14), (135, 186, 14), (225, 186, 14)):
        a = math.radians(deg)
        tip = (c + L * math.cos(a), c + L * math.sin(a))
        b1 = (c + 160 * math.cos(a + w / 160), c + 160 * math.sin(a + w / 160))
        b2 = (c + 160 * math.cos(a - w / 160), c + 160 * math.sin(a - w / 160))
        sp.append(sd_poly(cv, [b1, tip, b2, (c + 150 * math.cos(a), c + 150 * math.sin(a))], margin=3))
    draw_part(cv, union(*sp), MAT["gold"], bevel=7, kind="chisel", shadow=(0, 2.5, 3, 0.85))
    band = sub(sd_circle(cv, c, c, R1), sd_circle(cv, c, c, R0))
    ticks = [sd_stroke(cv, [(c + 164 * math.cos(a), c + 164 * math.sin(a)), (c + 170 * math.cos(a), c + 170 * math.sin(a))], 0)
             for a in np.linspace(0, 2 * math.pi, 72, endpoint=False)]
    eh = hammered(cv, 5, 0.3) + groove_h(cv, union(*ticks), 1.8, 1.0)
    draw_part(cv, band, MAT["iron"], bevel=8, extra_h=eh, shadow=(0, 3, 5, 0.9), noise=canvas_noise(cv, 1, 1.5), noise_amt=0.05)
    draw_part(cv, ring_of(sd_circle(cv, c, c, R0 + 1.5), 4.5), MAT["gold"], bevel=2.2, shadow=None)
    draw_part(cv, ring_of(sd_circle(cv, c, c, R1 - 1), 4), MAT["bronze"], bevel=2, shadow=(0, 1, 1.5, 0.7))
    aether_channel(cv, np.abs(sd_circle(cv, c, c, 158)), core=0.9, glow_sigma=2.5, strength=0.7)
    gem(cv, c, c - 163, 9, MAT["aether"], glow=AETHER, glow_sigma=8, glow_str=0.6, setting="gold", setting_w=3)
    for deg in (0, 90, 180):
        a = math.radians(deg)
        stud(cv, c + 162 * math.cos(a), c + 162 * math.sin(a), 5, "gold")
    for deg in (45, 135, 225, 315):
        a = math.radians(deg)
        stud(cv, c + 162 * math.cos(a), c + 162 * math.sin(a), 3.2, "gold_dim")
    return cv


@reg("minimap_mask", "White disc mask for the minimap viewport (400x400, disc centre (200,200) r=153 so it tucks under the frame lip).",
     map_center=[200, 200], map_radius=153)
def minimap_mask():
    cv = Canvas(400, 400)
    cv.over("#ffffff", cov(cv, sd_circle(cv, 200, 200, 153)))
    return cv


def buff_frame(good):
    cv = Canvas(64, 64)
    col = "#5ad06a" if good else "#e03a2a"
    trim = MAT["gold"] if good else MAT["crimson"]
    outer = sd_rect(cv, 3, 3, 61, 61, 8)
    inner = sd_rect(cv, 8, 8, 56, 56, 4)
    cv.glow(cov(cv, sub(outer, inner)), col, 2.5, 0.45)
    cv.put(metal(cv, sub(outer, inner), trim, bevel=3))
    paint(cv, np.abs(sd_rect(cv, 9.5, 9.5, 54.5, 54.5, 3)) - 0.6, col, 0.8)
    if good:
        for (x, y) in ((6, 6), (58, 6), (6, 58), (58, 58)):
            diamond(cv, x, y, 4, mat="gold")
    else:
        for (x, y, a) in ((6, 6, 225), (58, 6, 315), (6, 58, 135), (58, 58, 45)):
            ang = math.radians(a)
            tip = (x + 7 * math.cos(ang), y + 7 * math.sin(ang))
            base = [(x + 4 * math.cos(ang + 1.9), y + 4 * math.sin(ang + 1.9)), tip, (x + 4 * math.cos(ang - 1.9), y + 4 * math.sin(ang - 1.9))]
            draw_part(cv, sd_poly(cv, base, margin=2), MAT["crimson"], bevel=2, kind="chisel", shadow=None)
    return cv


HUD["buff_frame"] = (lambda: buff_frame(True), dict(margins=None, use="Buff icon border (64x64 at 2x -> 32 px), green-gold; transparent centre 48x48.", scale=0.5))
HUD["debuff_frame"] = (lambda: buff_frame(False), dict(margins=None, use="Debuff icon border (64x64 at 2x), red with barbs.", scale=0.5))


# ------------------------------------------------------------------------------------------ vignettes + particles

def vignette(color, inner, outer, power, amp, sy=1.0, noise=True, W=1920, H=1080):
    cv = Canvas(W, H, ss=1)
    d = np.hypot((cv.X - W / 2) / (W / 2), (cv.Y - H / 2) / (H / 2) * sy)
    t = np.clip((d - inner) / (outer - inner), 0, 1) ** power
    if noise:
        n = fnoise(H, W, 17, beta=2.4, lo=2)
        t = np.clip(t * (1 + n * 0.12), 0, 1)
    cv.over(color, t * amp)
    return cv


HUD["vignette_lowhp"] = (lambda: vignette("#7a0606", 0.55, 1.35, 1.7, 0.85), dict(
    margins=None, use="Low-HP screen vignette (1920x1080, alpha only toward the edges). Stretch to the viewport; pulse its alpha.", scale=1.0))
HUD["vignette_dark"] = (lambda: vignette("#000000", 0.5, 1.4, 1.6, 0.8), dict(
    margins=None, use="Neutral dark screen vignette (1920x1080). Stretch to the viewport.", scale=1.0))


@reg("loot_beam", "Vertical soft beam (64x512, white; tint per rarity). Bottom = ground; use additive blend.", scale=1.0)
def loot_beam():
    W, H = 64, 512
    cv = Canvas(W, H)
    x = (cv.X - W / 2) / (W / 2)
    y = cv.Y / H
    core = np.exp(-(x / 0.12) ** 2)
    halo = np.exp(-(x / 0.45) ** 2)
    fade = np.clip(y, 0, 1) ** 1.6 * np.clip((1 - y) / 0.04, 0, 1)
    a = np.clip((core * 0.9 + halo * 0.45) * fade, 0, 1)
    cv.over("#ffffff", a)
    return cv


@reg("mote", "Soft round particle (32x32, white).", scale=1.0)
def mote():
    cv = Canvas(32, 32)
    d = np.hypot(cv.X - 16, cv.Y - 16) / 15
    cv.over("#ffffff", np.clip(1 - d, 0, 1) ** 2.2)
    return cv


@reg("spark", "Four-point star spark (32x32, white).", scale=1.0)
def spark():
    cv = Canvas(32, 32)
    s = sd_poly(cv, star(16, 16, 4, 15, 2.2), margin=2)
    cv.glow(cov(cv, s), "#ffffff", 2.5, 0.7, gain=1.5)
    cv.over("#ffffff", cov(cv, s, soft=0.4))
    cv.over("#ffffff", np.clip(1 - np.hypot(cv.X - 16, cv.Y - 16) / 5, 0, 1), 1.0)
    return cv


@reg("ember", "Ember flake particle (32x32, orange-gold, hot core).", scale=1.0)
def ember():
    cv = Canvas(32, 32)
    e = sd_poly(cv, catmull([(16, 5), (22, 13), (24, 22), (16, 27), (9, 21), (11, 12)], 5, closed=True), margin=2)
    cv.glow(cov(cv, e), "#ff6a14", 3, 0.9, gain=1.4)
    rgb = rgrad(cv, 16, 18, 10, [(0, "#fff6c0"), (0.45, "#ffb040"), (1, "#e0400a")])
    cv.over(rgb, cov(cv, e, soft=0.6))
    return cv


# ------------------------------------------------------------------------------------------ cursors (1x, 48 px)

def _cursor_arrow(cv, s=1.0, mat="gold"):
    pts = [(3, 3), (3, 34), (11, 27), (17, 40), (23, 37), (17, 25), (28, 24)]
    pts = [(x * s, y * s) for x, y in pts]
    sd = sd_poly(cv, pts, margin=3)
    paint(cv, sd - 1.6, "#050304")
    draw_part(cv, sd, MAT[mat], bevel=3.2 * s, kind="chisel", shadow=(1.2, 1.8, 1.5, 0.8))
    return sd


def cursor(kind):
    cv = Canvas(48, 48, ss=4)
    if kind == "default":
        _cursor_arrow(cv)
        gem(cv, 8.5, 18, 2.3, MAT["aether"], glow=AETHER, glow_sigma=2, glow_str=0.5, setting=None)
    elif kind == "attack":
        # sword pointing to the top-left hotspot
        blade = [(2, 2), (10, 4), (32, 26), (26, 32), (4, 10)]
        sd = sd_poly(cv, blade, margin=2)
        paint(cv, sd - 1.6, "#050304")
        draw_part(cv, sd, MAT["steel"], bevel=3, kind="chisel", shadow=(1, 1.5, 1.5, 0.8))
        paint(cv, sd_stroke(cv, [(5, 5), (28, 28)], 0.8), "#ffffff", 0.7)
        guard = sd_stroke(cv, [(24, 38), (38, 24)], 5)
        grip = sd_stroke(cv, [(31, 31), (41, 41)], 4)
        pom = sd_circle(cv, 43, 43, 3.2)
        for p, m in ((grip, "leather"), (guard, "crimson"), (pom, "gold")):
            paint(cv, p - 1.4, "#050304")
            draw_part(cv, p, MAT[m] if m != "leather" else tint_mat("#6a3e22"), bevel=2, shadow=None)
    elif kind == "interact":
        _cursor_arrow(cv, 0.85)
        # cog
        cx, cy = 33, 33
        teeth = []
        for i in range(8):
            a = i * math.pi / 4
            teeth.append(sd_poly(cv, xf([(-2.6, -12.5), (2.6, -12.5), (3.2, -7), (-3.2, -7)], cx, cy, math.degrees(a)), margin=2))
        cog = sub(union(sd_circle(cv, cx, cy, 9.5), *teeth), sd_circle(cv, cx, cy, 3.6))
        paint(cv, cog - 1.4, "#050304")
        draw_part(cv, cog, MAT["bronze"], bevel=2.5, shadow=None)
        cv.glow(cov(cv, sd_circle(cv, cx, cy, 3.6)), AETHER, 2, 0.8, gain=2)
    elif kind == "talk":
        _cursor_arrow(cv, 0.85)
        bub = union(sd_ellipse(cv, 33, 30, 13, 10), sd_poly(cv, [(26, 36), (30, 38), (22, 45)], margin=2))
        paint(cv, bub - 1.4, "#050304")
        h = profile(bub, 3, "round") * 3
        cv.put((shade(cv, h, dict(ramp=even_ramp(["#3a2c1a", "#8a7454", "#d8c49c", "#f4e6c4", "#fffaf0"]), spec="#ffffff", sp=0.2, pw=12)), cov(cv, bub)))
        for dx in (-5, 0, 5):
            paint(cv, sd_circle(cv, 33 + dx, 30, 1.6), "#3a2410")
    return cv


for _k, _hs, _use in (("default", (3, 3), "Default pointer: gold arrow."), ("attack", (2, 2), "Attack cursor over enemies: sword."),
                      ("interact", (3, 3), "Interact cursor (doors, chests, teleporters): arrow + aether cog."),
                      ("talk", (3, 3), "Talk cursor over NPCs: arrow + speech bubble.")):
    HUD[f"cursor_{_k}"] = ((lambda k: (lambda: cursor(k)))(_k), dict(margins=None, use=_use + " 48x48, drawn 1:1 (Input.set_custom_image).",
                                                                  scale=1.0, hotspot=list(_hs)))
