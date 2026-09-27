"""Weapon models for every weapon base (bh-006). Hand-socket convention (same as tools/blender/characters/bh_weapons):
origin = main-hand grip centre, long axis +Z (blade / shaft / head), blade flats face +-Y, edges +-X.
Bows: grip at the origin, limbs along +-Z, string on -X.

Each builder takes a spec dict (see SPECS at the bottom) so the five weapons of a category share a construction
method but differ in silhouette, proportions, materials and ornament."""
import math

import numpy as np

import item_kit as K
from item_kit import M, Rx, Ry, Rz


# ---- blades --------------------------------------------------------------------------------------------------------

def blade(z0, z1, width, thick, tip, mat="steel", curve=None, single=False, fuller=True, n_sec=10, wave=0.0, tip_bias=0.0):
    """Blade along +Z. width(u)->full width at u in [0,1] (u over the straight part); curve(u)->x offset of the centre
    line; single: single edge (+X is the edge, -X the thick spine); wave: flamberge amplitude; tip_bias: tip point
    shifted toward the spine (-X) as a fraction of the half width (clip points)."""
    rings = []
    zb = z1 - tip
    zs = list(np.linspace(z0, zb, n_sec)) + list(np.linspace(zb, z1, 6)[1:])
    w_end = width(1.0)
    for z in zs:
        if z <= zb + 1e-9:
            u = (z - z0) / max(zb - z0, 1e-6)
            w = width(u)
            th = thick * (1.0 - 0.3 * u)
            cx = curve(u) if curve else 0.0
            if wave:
                cx += wave * math.sin(u * math.pi * 5.0) * (1 - 0.6 * u)
        else:
            v = (z - zb) / tip
            w = w_end * max(1 - v, 0.0) ** 0.85 + 0.0005
            th = thick * 0.7 * max(1 - v, 0.0) ** 0.7 + 0.0004
            cx = (curve(1.0) if curve else 0.0) - tip_bias * w_end * 0.5 * v
        hw = w / 2
        if single:
            sec = [(hw, 0), (0.55 * hw, 0.45 * th), (0.1 * hw, 0.85 * th), (-0.45 * hw, th), (-hw, th * 0.9),
                   (-hw, -th * 0.9), (-0.45 * hw, -th), (0.1 * hw, -0.85 * th), (0.55 * hw, -0.45 * th), (0.8 * hw, -0.2 * th)]
        else:
            f = 0.55 if fuller else 0.9
            sec = [(hw, 0), (0.45 * hw, th), (0.15 * hw, th * f), (-0.15 * hw, th * f), (-0.45 * hw, th),
                   (-hw, 0), (-0.45 * hw, -th), (-0.15 * hw, -th * f), (0.15 * hw, -th * f), (0.45 * hw, -th)]
        rings.append(np.array([(x + cx, y, z) for x, y in sec]))
    V, F = M.loft(rings, cap0=True, cap1=True)
    return M.Part(V, F, mat, name="blade")


def grip(z0, z1, r, mat="leather", ridges=6, n=10):
    prof = []
    k = ridges * 2 + 1
    for i in range(k + 1):
        z = z0 + (z1 - z0) * i / k
        rr = r * (1.0 + (0.12 if i % 2 else 0.0)) * (1 + 0.08 * math.sin(math.pi * i / k))
        prof.append((rr, z))
    return K.lathe([(0.0, z0)] + prof + [(0.0, z1)], mat, n, "grip")


def crossguard(z, half, mat="gold", h=0.022, t=0.02, curve=0.02, flare=0.5):
    pts, prof = [], []
    for i in range(11):
        u = -1 + 2 * i / 10
        pts.append((u * half, 0, z + curve * u * u))
        s = 1.0 + flare * abs(u) ** 4
        prof.append((t * 0.5 * s, h * 0.5 * s, 3.0))
    V, F = M.tube(pts, prof, n=8, up=(0, 0, 1))
    return M.bevel(M.Part(V, F, mat, name="guard"), 0.002, 1)


def disc_guard(z, r, mat="darksteel", t=0.012):
    return K.lathe([(0, z - t / 2), (r * 0.9, z - t / 2), (r, z), (r * 0.9, z + t / 2), (0, z + t / 2)], mat, 18, "guard").scale((1, 0.55, 1), (0, 0, z))


def winged_guard(z, half, mat="gold", depth=0.016):
    parts = []
    for sx in (1, -1):
        o = [(0.01, -0.012), (half * 0.55, -0.006), (half, 0.03), (half * 0.9, 0.012), (half * 0.6, 0.02), (half * 0.45, 0.045),
             (half * 0.3, 0.018), (0.01, 0.014)]
        o = [(sx * x, zz + z) for x, zz in o]
        parts.append(M.bevel(K.slab(o, depth, mat), 0.002, 1))
    parts.append(K.box(0.03, depth * 1.4, 0.034, (0, 0, z + 0.002), mat, 0.003))
    return parts


def pommel(z, r, mat="gold", style="round"):
    if style == "disc":
        p = K.lathe([(0, z - r * 0.5), (r * 0.8, z - r * 0.45), (r, z), (r * 0.8, z + r * 0.45), (0, z + r * 0.5)], mat, 16, "pommel")
        return M.bevel(p.rot(Rx(90), (0, 0, z)).scale((1, 0.7, 1), (0, 0, z)), 0.0015, 1)
    if style == "spike":
        return K.lathe([(0, z - r * 1.8), (r * 0.5, z - r * 1.0), (r, z - r * 0.2), (r * 0.8, z + r * 0.4), (0, z + r * 0.6)], mat, 8, "pommel")
    if style == "ring":
        return K.ring_tube((0, 0, z - r), r, r * 0.28, mat, axis="y", n=18)
    prof = [(0, z - r * 0.9), (r * 0.55, z - r * 0.85), (r, z - r * 0.35), (r * 1.02, z), (r * 0.8, z + r * 0.5),
            (r * 0.4, z + r * 0.8), (0, z + r * 0.85)]
    p = K.lathe(prof, mat, 12, "pommel")
    p.scale((1.0, 0.6, 1.0), center=(0, 0, z))
    return M.bevel(p, 0.0015, 1)


def channel(z0, z1, w0, w1, t, mat, x=0.0):
    """Thin glowing inlay strip on both blade flats (element / rune channel)."""
    parts = []
    for sy in (1, -1):
        rings = []
        for z in np.linspace(z0, z1, 6):
            u = (z - z0) / (z1 - z0)
            w = (w0 + (w1 - w0) * u) / 2
            rings.append(np.array([(x - w, sy * t * 0.3, z), (x + w, sy * t * 0.3, z), (x + w, sy * (t + 0.0012), z),
                                   (x - w, sy * (t + 0.0012), z)]))
        V, F = M.loft(rings)
        p = M.Part(V, F, mat, name="channel")
        if sy < 0:
            p.flip()
        parts.append(p)
    return parts


def sword(s):
    L = s.get("len", 0.78)
    z0 = s.get("z0", 0.105)
    w0, w1 = s.get("w", (0.052, 0.036))
    shape = s.get("shape", "straight")
    th = s.get("thick", 0.0065)
    mat = s.get("blade", "steel")
    curve = None
    width = lambda u: w0 + (w1 - w0) * u  # noqa: E731
    single = False
    tip = s.get("tip", 0.13)
    tb = 0.0
    if shape == "falchion":
        width = lambda u: w0 + (w1 - w0) * u ** 1.4  # noqa: E731
        single, tb = True, 0.7
    elif shape == "sabre":
        curve = lambda u: -0.05 * u ** 2  # noqa: E731
        single, tb = True, 0.4
    elif shape == "leaf":
        width = lambda u: w0 * (1.0 + 0.35 * math.sin(math.pi * min(u * 1.15, 1.0)))  # noqa: E731
    elif shape == "waisted":
        width = lambda u: w0 * (1.0 - 0.18 * math.sin(math.pi * u)) + (w1 - w0) * u  # noqa: E731
    parts = [blade(z0, z0 + L, width, th, tip, mat, curve=curve, single=single, fuller=not single, tip_bias=tb,
                   wave=s.get("wave", 0.0))]
    gz = z0 - 0.015
    g = s.get("guard", "bar")
    gm = s.get("guard_mat", "gold")
    if g == "bar":
        parts.append(crossguard(gz, s.get("guard_half", 0.11), gm, curve=s.get("guard_curve", 0.02)))
    elif g == "swept":
        parts.append(crossguard(gz, s.get("guard_half", 0.1), gm, curve=0.05, flare=1.2))
        # knuckle bow
        parts.append(K.tube([(0.08, 0, gz + 0.004), (0.07, 0, gz - 0.08), (0.03, 0, gz - 0.16), (0.0, 0, gz - 0.175)],
                            [0.006, 0.005, 0.005, 0.005], gm, n=6, up=(0, 1, 0)))
    elif g == "disc":
        parts.append(disc_guard(gz, s.get("guard_half", 0.05), gm))
    elif g == "winged":
        parts += winged_guard(gz - 0.01, s.get("guard_half", 0.12), gm)
    gl = s.get("grip_len", 0.16)
    parts.append(grip(gz - 0.012 - gl, gz - 0.012, s.get("grip_r", 0.0155), s.get("grip_mat", "leather")))
    parts.append(pommel(gz - 0.02 - gl, s.get("pommel_r", 0.027), s.get("pommel_mat", gm), s.get("pommel", "round")))
    if s.get("ricasso"):
        parts.append(K.box(w0 * 1.25, th * 3.2, 0.05, (0, 0, z0 + 0.02), s.get("ricasso"), 0.003))
    if s.get("glow"):
        parts += channel(z0 + 0.03, z0 + L * 0.8, w0 * 0.24, w1 * 0.1, th * 0.55, s["glow"])
    if s.get("gem"):
        parts.append(K.gem((0, 0, gz), 0.013, s["gem"], rot=(90, 0, 0)))
    if s.get("lugs"):
        for sx in (1, -1):
            o = [(0.0, 0.0), (0.045, 0.02), (0.05, 0.035), (0.0, 0.03)]
            p = K.slab([(sx * x, z) for x, z in o], 0.012, s.get("guard_mat", "darksteel"))
            parts.append(M.bevel(p.move((sx * w0 * 0.45, 0, z0 + L * 0.16)), 0.002, 1))
    if s.get("serrate"):
        for i in range(8):
            z = z0 + 0.1 + i * L * 0.075
            parts.append(K.cone_spike((-w0 * 0.45, 0, z), (-w0 * 0.72, 0, z + 0.02), 0.006, mat))
    return parts


# ---- hafted --------------------------------------------------------------------------------------------------------

def haft(z0, z1, r, mat="wood", n=10, taper=0.85, knot=0.0):
    prof = [(0, z0), (r * 0.9, z0), (r * 1.05, z0 + 0.02)]
    for i in range(1, 8):
        u = i / 8
        rr = r * (1.0 - (1 - taper) * u)
        if knot:
            rr *= 1 + knot * math.sin(u * 23.0) * 0.5
        prof.append((rr, z0 + (z1 - z0) * u))
    prof += [(r * taper * 0.95, z1), (0, z1 + 0.005)]
    return K.lathe(prof, mat, n, "haft")


AXE_HEADS = {
    "bearded": [(0.02, 0.46), (0.08, 0.47), (0.15, 0.52), (0.21, 0.60), (0.225, 0.54), (0.23, 0.46), (0.225, 0.38),
                (0.20, 0.30), (0.17, 0.33), (0.12, 0.40), (0.06, 0.43), (0.02, 0.42)],
    "hatchet": [(0.02, 0.44), (0.1, 0.46), (0.155, 0.5), (0.165, 0.44), (0.16, 0.38), (0.1, 0.4), (0.02, 0.405)],
    "tomahawk": [(0.02, 0.45), (0.09, 0.455), (0.16, 0.49), (0.17, 0.455), (0.168, 0.41), (0.09, 0.425), (0.02, 0.428)],
    "crescent": [(0.02, 0.44), (0.1, 0.48), (0.17, 0.58), (0.2, 0.6), (0.23, 0.5), (0.235, 0.44), (0.23, 0.36), (0.2, 0.28),
                 (0.17, 0.3), (0.1, 0.4), (0.02, 0.41)],
    "cleaver": [(0.02, 0.44), (0.05, 0.6), (0.24, 0.62), (0.26, 0.5), (0.25, 0.34), (0.1, 0.38), (0.02, 0.4)],
    "broad": [(0.02, 0.43), (0.1, 0.45), (0.2, 0.55), (0.3, 0.66), (0.33, 0.52), (0.335, 0.4), (0.32, 0.26), (0.2, 0.22),
              (0.18, 0.28), (0.1, 0.37), (0.02, 0.4)],
    "moon": [(0.02, 0.42), (0.12, 0.47), (0.22, 0.6), (0.3, 0.72), (0.34, 0.6), (0.36, 0.44), (0.35, 0.28), (0.3, 0.14),
             (0.22, 0.22), (0.12, 0.35), (0.02, 0.38)],
}


def axe_head(outline, mat, thick=0.03, zoff=0.0, scale=1.0, mirror=False):
    o = [(x * scale, (z - 0.44) * scale + 0.44 + zoff) for x, z in outline]
    if mirror:
        o = [(-x, z) for x, z in o]
    head = K.slab(M.resample_closed(np.array(o), 44), thick * scale, mat, name="axehead")
    lim = max(abs(x) for x, _ in o)
    head.warp(lambda v: (v[0], v[1] * (1.0 - 0.82 * min(max((abs(v[0]) - 0.03) / max(lim - 0.03, 0.01), 0), 1)), v[2]))
    return M.bevel(head, 0.002, 1, angle=50)


def axe(s):
    two = s.get("two_handed", False)
    top = s.get("haft_top", 1.25 if two else 0.66)
    bot = s.get("haft_bot", -0.35 if two else -0.16)
    r = s.get("haft_r", 0.02 if two else 0.017)
    parts = [haft(bot, top, r, s.get("haft_mat", "wood"), taper=0.9)]
    parts.append(grip(-0.11, 0.1, r * 1.05, s.get("grip_mat", "leather"), 5))
    if two:
        parts.append(grip(0.35, 0.52, r * 1.02, s.get("grip_mat", "leather"), 4))
    zoff = top - 0.66 + (0.0 if not two else -0.06)
    sc = s.get("head_scale", 1.35 if two else 1.0)
    shape = AXE_HEADS[s.get("head", "bearded")]
    hm = s.get("head_mat", "steel")
    parts.append(axe_head(shape, hm, s.get("head_thick", 0.03), zoff, sc))
    if s.get("double"):
        parts.append(axe_head(shape, hm, s.get("head_thick", 0.03), zoff, sc * 0.95, mirror=True))
    elif s.get("spike", True):
        zc = 0.47 + zoff
        parts.append(K.tube([(-0.01, 0, zc), (-0.09 * sc, 0, zc - 0.005), (-0.14 * sc, 0, zc - 0.03)],
                            [(0.018, 0.022), (0.01, 0.012), (0.001, 0.001)], s.get("spike_mat", "darksteel"), n=6, up=(0, 0, 1)))
    # socket and bands
    zs = 0.4 + zoff
    parts.append(K.lathe([(0, zs), (r * 1.5, zs), (r * 1.6, zs + 0.03), (r * 1.6, zs + 0.13 * sc), (r * 1.35, zs + 0.15 * sc), (0.0, zs + 0.16 * sc)],
                         s.get("socket_mat", "darksteel"), 10, "socket"))
    for z in s.get("bands", [zs - 0.05, zs - 0.08]):
        parts.append(K.band(z, r * 1.2, 0.014, s.get("band_mat", "gold")))
    if s.get("glow"):
        # glowing edge inlay along the bit
        o = [(x * sc, (z - 0.44) * sc + 0.44 + zoff) for x, z in shape]
        xmax = max(x for x, _ in o)
        edge = sorted([p for p in o if p[0] > xmax * 0.8], key=lambda p: p[1])
        pts = [(x - 0.012, 0, z) for x, z in edge]
        if len(pts) >= 2:
            parts.append(K.tube(pts, [0.005] * len(pts), s["glow"], n=6, up=(1, 0, 0)))
    if s.get("pommel"):
        parts.append(K.lathe([(0, bot - 0.04), (r * 1.4, bot - 0.03), (r * 1.5, bot), (0, bot + 0.02)], s.get("band_mat", "gold"), 10))
    if s.get("wrap"):
        for i in range(6):
            parts.append(K.band(0.15 + i * 0.03, r * 1.12, 0.008, s["wrap"], n=10))
    if s.get("feathers"):
        for k in range(2):
            fz = zs - 0.12 - 0.03 * k
            p = K.slab([(0.0, 0.0), (0.012, -0.03), (0.01, -0.09), (0.0, -0.11), (-0.008, -0.05)], 0.003, s["feathers"])
            parts.append(p.rot(Rz(20 + 40 * k)).move((r * 1.1, 0, fz)))
    return parts


# ---- polearms / thrown ---------------------------------------------------------------------------------------------

def leaf_head(z0, length, w, mat, t=0.012):
    rings = []
    for u, ww in ((0.0, 0.3), (0.12, 0.65), (0.35, 1.0), (0.6, 0.85), (0.85, 0.45), (0.97, 0.12), (1.0, 0.02)):
        hw = w * ww / 2
        th = t * ww + 0.002
        z = z0 + length * u
        rings.append(np.array([(hw, 0, z), (0, th, z), (-hw, 0, z), (0, -th, z)]))
    V, F = M.loft(rings)
    return M.Part(V, F, mat, name="spearhead")


def spear(s):
    top = s.get("shaft_top", 0.98)
    bot = s.get("shaft_bot", -0.9)
    r = s.get("shaft_r", 0.019)
    parts = [haft(bot, top, r, s.get("shaft_mat", "wood"), taper=0.9)]
    parts.append(grip(-0.1, 0.1, r * 1.03, s.get("grip_mat", "leather"), 5))
    hm = s.get("head_mat", "steel")
    head = s.get("head", "leaf")
    hz = top + 0.01
    hl = s.get("head_len", 0.31)
    if head == "leaf":
        parts.append(leaf_head(hz, hl, s.get("head_w", 0.078), hm))
    elif head == "partisan":
        parts.append(leaf_head(hz + 0.02, hl, s.get("head_w", 0.07), hm))
        for sx in (1, -1):
            o = [(0.02, hz + 0.02), (0.1, hz + 0.08), (0.075, hz + 0.05), (0.03, hz + 0.06)]
            parts.append(M.bevel(K.slab([(sx * x, z) for x, z in o], 0.012, hm), 0.002, 1))
    elif head == "glaive":
        width = lambda u: 0.07 * (1.0 + 0.3 * math.sin(math.pi * u))  # noqa: E731
        parts.append(blade(hz, hz + hl, width, 0.008, 0.12, hm, curve=lambda u: -0.06 * u * u, single=True, tip_bias=0.6))
        parts.append(K.cone_spike((-0.03, 0, hz + 0.07), (-0.09, 0, hz + 0.1), 0.01, hm))
    elif head == "trident":
        parts.append(K.box(0.2, 0.02, 0.025, (0, 0, hz + 0.02), hm, 0.004))
        for x in (-0.085, 0.0, 0.085):
            ln = hl * (1.0 if x == 0 else 0.78)
            parts.append(leaf_head(hz + 0.03, ln, 0.035, hm, 0.008).move((x, 0, 0)))
            if x != 0:
                parts.append(K.cone_spike((x, 0, hz + 0.06), (x * 1.35, 0, hz + 0.1), 0.006, hm))
    elif head == "lance":
        parts.append(K.lathe([(0, hz), (0.03, hz), (0.034, hz + 0.05), (0.026, hz + hl * 0.5), (0.012, hz + hl * 0.85), (0, hz + hl)], hm, 8, "lance"))
        for k in range(3):
            o = [(0.02, hz + 0.02), (0.07, hz + 0.05), (0.03, hz + 0.16)]
            parts.append(K.slab(o, 0.008, hm).rot(Rz(120 * k)))
    elif head == "pilum":
        parts.append(K.lathe([(0, hz), (0.012, hz), (0.008, hz + 0.05), (0.006, hz + hl * 0.8), (0.0, hz + hl * 0.8 + 0.005)], "iron", 8))
        parts.append(K.lathe([(0, hz + hl * 0.78), (0.018, hz + hl * 0.84), (0.0, hz + hl)], hm, 4, "tip"))
    elif head == "barbed":
        parts.append(leaf_head(hz, hl, s.get("head_w", 0.05), hm))
        for sx in (1, -1):
            parts.append(K.cone_spike((sx * 0.012, 0, hz + 0.03), (sx * 0.04, 0, hz - 0.015), 0.006, hm))
    elif head == "bolt":
        # a stylised lightning bolt blade
        o = [(0.0, hz), (0.03, hz + 0.08), (0.005, hz + 0.1), (0.04, hz + 0.2), (0.0, hz + hl), (-0.012, hz + 0.16),
             (0.012, hz + 0.14), (-0.02, hz + 0.05)]
        parts.append(M.bevel(K.slab(o, 0.014, hm), 0.002, 1))
    elif head == "sun":
        parts.append(leaf_head(hz + 0.03, hl, 0.055, hm))
        for k in range(8):
            a = k * 45
            parts.append(K.cone_spike((0, 0, hz + 0.05), (0.06 * math.cos(math.radians(a)), 0.02 * math.sin(math.radians(a)), hz + 0.05 + 0.04 * math.sin(math.radians(a))), 0.006, s.get("orn", "gold")))
    # socket, bands, butt
    parts.append(K.lathe([(0, top - 0.07), (r * 1.1, top - 0.07), (r * 1.3, top - 0.02), (r * 1.1, top + 0.02), (0.0, top + 0.03)],
                         s.get("socket_mat", "darksteel"), 10, "socket"))
    for z in s.get("bands", [top - 0.09, bot + 0.12]):
        parts.append(K.band(z, r * 1.15, 0.018, s.get("band_mat", "gold")))
    if s.get("butt", True):
        parts.append(K.lathe([(0, bot - 0.06), (r * 0.5, bot - 0.06), (r * 1.1, bot - 0.02), (r * 1.1, bot + 0.02), (0, bot + 0.03)],
                             s.get("socket_mat", "darksteel"), 8))
    if s.get("tassel"):
        parts.append(K.tube([(r, 0, top - 0.1), (r * 3, 0.01, top - 0.16), (r * 3.5, 0.02, top - 0.26)], [0.008, 0.012, 0.004], s["tassel"], n=6))
    if s.get("glow"):
        parts.append(K.ring_tube((0, 0, top - 0.04), r * 1.5, 0.004, s["glow"], axis="z", n=16))
        parts.append(K.gem((0, 0, hz + 0.04), 0.012, s["glow"], rot=(90, 0, 0)))
    if s.get("fins"):
        for k in range(3):
            o = [(r, bot + 0.02), (r + 0.035, bot - 0.01), (r + 0.03, bot + 0.1), (r, bot + 0.12)]
            parts.append(K.slab(o, 0.003, s["fins"]).rot(Rz(120 * k + 30)))
    return parts


def javelin(s):
    s = dict(s)
    s.setdefault("shaft_top", 0.78)
    s.setdefault("shaft_bot", -0.62)
    s.setdefault("shaft_r", 0.012)
    s.setdefault("head_len", 0.2)
    s.setdefault("butt", False)
    s.setdefault("bands", [0.7, -0.5])
    return spear(s)


# ---- blunt ---------------------------------------------------------------------------------------------------------

def club(s):
    top = s.get("top", 0.58)
    r = s.get("r", 0.018)
    parts = []
    kind = s.get("kind", "cudgel")
    if kind == "cudgel":
        prof = [(0, -0.16), (r, -0.16), (r * 1.1, -0.1)]
        for i in range(1, 12):
            u = i / 11
            z = -0.1 + (top + 0.05) * u
            rr = r * (1.0 + 2.2 * u ** 2.2) * (1 + 0.1 * math.sin(u * 31))
            prof.append((rr, z))
        prof.append((0, top + 0.1))
        parts.append(K.lathe(prof, s.get("wood", "wood"), 10, "cudgel"))
        rng = np.random.default_rng(3)
        for i in range(7):   # knots
            u = 0.4 + 0.55 * rng.random()
            a = rng.random() * 6.28
            z = -0.1 + (top + 0.05) * u
            rr = r * (1.0 + 2.2 * u ** 2.2)
            parts.append(K.sphere(rr * 0.35, (rr * 0.85 * math.cos(a), rr * 0.85 * math.sin(a), z), s.get("wood", "wood"), 6, 4))
        if s.get("spikes"):
            for i in range(12):
                u = 0.45 + 0.5 * (i / 12)
                a = i * 2.4
                z = -0.1 + (top + 0.05) * u
                rr = r * (1.0 + 2.2 * u ** 2.2)
                d = np.array([math.cos(a), math.sin(a), 0.2])
                parts.append(K.cone_spike(np.array([0, 0, z]) + d * rr * 0.9, np.array([0, 0, z]) + d * (rr + 0.045), 0.008, s.get("spike_mat", "iron")))
            parts.append(K.band(0.3, r * 1.7, 0.02, "iron"))
    else:
        parts.append(haft(-0.17, top, r, s.get("haft_mat", "darkwood"), taper=1.0))
        hz = top + 0.02
        hm = s.get("head_mat", "iron")
        if kind == "flanged":
            parts.append(K.lathe([(0, hz - 0.03), (r * 1.4, hz - 0.03), (r * 1.6, hz + 0.1), (r * 1.2, hz + 0.16), (0, hz + 0.17)], hm, 10))
            for k in range(s.get("flanges", 7)):
                o = [(r * 1.2, hz - 0.01), (0.055, hz + 0.02), (0.06, hz + 0.1), (r * 1.2, hz + 0.15)]
                parts.append(M.bevel(K.slab(o, 0.009, hm), 0.002, 1).rot(Rz(360 / s.get("flanges", 7) * k)))
            parts.append(K.lathe([(0, hz + 0.16), (0.012, hz + 0.16), (0, hz + 0.21)], hm, 6))
        elif kind == "morningstar":
            parts.append(K.band(hz - 0.02, r * 1.5, 0.04, hm))
            c = (0, 0, hz + 0.08)
            parts.append(K.sphere(0.06, c, hm, 12, 8))
            parts += K.spikes_on_sphere(c, 0.06, 0.05, s.get("spike_mat", "steel"), count=14, base=0.011)
    parts.append(grip(-0.12, 0.08, r * 1.08, s.get("grip_mat", "leather"), 5))
    parts.append(K.lathe([(0, -0.2), (r * 1.3, -0.19), (r * 1.4, -0.16), (0, -0.14)], s.get("cap", "darksteel"), 8))
    if s.get("glow"):
        hz = top + 0.02
        parts.append(K.sphere(0.03, (0, 0, hz + 0.075), s["glow"], 10, 6))
        parts.append(K.ring_tube((0, 0, hz + 0.075), 0.05, 0.004, s["glow"], axis="z", n=18))
    return parts


# ---- short blades / fist weapons ---------------------------------------------------------------------------------

def dagger(s):
    L = s.get("len", 0.28)
    z0 = 0.05
    w0, w1 = s.get("w", (0.036, 0.022))
    shape = s.get("shape", "straight")
    mat = s.get("blade", "steel")
    curve = None
    width = lambda u: w0 + (w1 - w0) * u  # noqa: E731
    single = False
    tb = 0.0
    if shape == "skinner":
        curve = lambda u: 0.025 * u ** 2  # noqa: E731
        single, tb = True, -0.4
        width = lambda u: w0 * (1 + 0.25 * math.sin(math.pi * u))  # noqa: E731
    elif shape == "kukri":
        curve = lambda u: 0.07 * math.sin(math.pi * u * 0.9)  # noqa: E731
        width = lambda u: w0 * (0.8 + 0.7 * u)  # noqa: E731
        single = True
    elif shape == "kris":
        pass
    elif shape == "crescent":
        curve = lambda u: -0.06 * math.sin(math.pi * u * 0.8)  # noqa: E731
        single, tb = True, 0.3
    parts = [blade(z0, z0 + L, width, s.get("thick", 0.005), s.get("tip", 0.07), mat, curve=curve, single=single,
                   fuller=not single, wave=0.012 if shape == "kris" else 0.0, tip_bias=tb, n_sec=8)]
    g = s.get("guard", "bar")
    gm = s.get("guard_mat", "gold")
    if g == "bar":
        parts.append(crossguard(0.042, s.get("guard_half", 0.06), gm, h=0.014, t=0.016, curve=s.get("guard_curve", 0.012)))
    elif g == "wide":
        parts.append(crossguard(0.042, 0.1, gm, h=0.016, t=0.016, curve=0.04, flare=1.5))
    elif g == "disc":
        parts.append(disc_guard(0.042, 0.035, gm))
    parts.append(grip(-0.05, 0.035, s.get("grip_r", 0.013), s.get("grip_mat", "leather"), 4))
    parts.append(pommel(-0.062, 0.018, s.get("pommel_mat", gm), s.get("pommel", "round")))
    if s.get("glow"):
        parts += channel(z0 + 0.03, z0 + L * 0.75, w0 * 0.2, w1 * 0.08, 0.005 * 0.55, s["glow"])
    if s.get("gem"):
        parts.append(K.gem((0, 0, 0.042), 0.009, s["gem"], rot=(90, 0, 0)))
    return parts


def claw(s):
    """Katar-style claw: an H-frame gripped at the origin; blades project along +Z from a knuckle plate."""
    parts = []
    fm = s.get("frame_mat", "darksteel")
    # side bars along the forearm
    for sx in (1, -1):
        parts.append(K.box(0.012, 0.03, 0.2, (sx * 0.045, 0, -0.02), fm, 0.003))
    parts.append(grip(-0.04, 0.04, 0.013, s.get("grip_mat", "leather"), 3).rot(Ry(90)))
    # knuckle plate
    plate = K.box(0.12, 0.04, 0.035, (0, 0, 0.09), s.get("plate_mat", fm), 0.006)
    parts.append(plate)
    n = s.get("blades", 3)
    L = s.get("len", 0.24)
    bm = s.get("blade", "steel")
    hook = s.get("hook", 0.03)
    for i in range(n):
        k = i - (n - 1) / 2
        x = k * s.get("spacing", 0.038)
        width = lambda u: 0.028 * (1 - 0.35 * u)  # noqa: E731
        side = 1.0 if k >= 0 else -1.0
        b = blade(0.105, 0.105 + L * (1.0 - 0.1 * abs(k)), width, 0.005, 0.06, bm,
                  curve=lambda u, sd=side: sd * hook * u ** 2, single=True, fuller=False, n_sec=7)
        # a fan: flats toward the front (+-Y), outer blades splayed a little
        parts.append(b.move((x, 0, 0)).rot(Ry(-k * 7.0), (x, 0, 0.1)))
    if s.get("spikes"):
        for sx in (1, -1):
            parts.append(K.cone_spike((sx * 0.06, 0, 0.09), (sx * 0.1, 0, 0.12), 0.012, bm))
    if s.get("glow"):
        parts.append(K.gem((0, -0.022, 0.09), 0.014, s["glow"], rot=(90, 0, 0)))
        parts.append(K.gem((0, 0.022, 0.09), 0.014, s["glow"], rot=(-90, 0, 0)))
    if s.get("scales"):
        for i in range(5):
            parts.append(K.sphere(0.018, (-0.04 + 0.02 * i, 0.02, 0.07), s["scales"], 6, 4, scale=(1, 0.4, 1.2)))
    return parts


def knuckles(s):
    """Knuckle-duster: finger rings stacked along the grip axis (Z), striking ridge on +X."""
    parts = []
    km = s.get("mat", "brass")
    kind = s.get("kind", "duster")
    if kind == "cestus":
        # a studded fist wrap: rounded knuckle block (+X), wrap bands around the grip axis, a wrist cuff below
        w = s.get("wrap", "tan")
        parts.append(K.sphere(0.05, (0.012, 0, 0.0), w, 14, 10, scale=(0.75, 0.62, 1.35)))
        for z in np.linspace(-0.05, 0.05, 5):
            parts.append(K.ring_tube((0.012, 0, z), 1.0, 0.0035, "darkleather", axis="z", n=18).scale((0.04, 0.032, 1), (0.012, 0, z)))
        for i in range(4):
            z = -0.045 + i * 0.03
            parts.append(K.sphere(0.012, (0.05, 0, z), s.get("stud", "iron"), 8, 6, scale=(0.8, 1, 1)))
            parts.append(K.cone_spike((0.058, 0, z), (0.075, 0, z), 0.007, s.get("stud", "iron")))
        parts.append(K.lathe([(0, -0.16), (0.04, -0.16), (0.045, -0.1), (0.038, -0.065), (0, -0.065)], "darkleather", 14).scale((1, 0.8, 1)).move((0.004, 0, 0)))
        parts.append(K.ring_tube((0.004, 0, -0.12), 1.0, 0.004, "brass", axis="z", n=18).scale((0.046, 0.037, 1), (0.004, 0, -0.12)))
        return parts
    for i in range(4):
        z = -0.045 + i * 0.03
        parts.append(K.ring_tube((0, 0, z), 0.013, 0.0055, km, axis="y", n=14))   # finger holes along Y
    # palm bar
    parts.append(K.tube([(-0.02, 0, -0.07), (-0.026, 0, 0.0), (-0.02, 0, 0.07)], [0.007, 0.009, 0.007], km, n=8, up=(1, 0, 0)))
    # striking ridge
    parts.append(K.box(0.014, 0.02, 0.13, (0.02, 0, -0.0), km, 0.005))
    sp = s.get("spikes", 0)
    for i in range(sp):
        z = -0.045 + i * (0.09 / max(sp - 1, 1))
        parts.append(K.cone_spike((0.025, 0, z), (0.025 + s.get("spike_len", 0.03), 0, z), 0.007, s.get("spike_mat", km)))
    if s.get("plate"):
        parts.append(K.box(0.03, 0.05, 0.15, (0.035, 0, 0), s["plate"], 0.01))
        parts.append(K.box(0.02, 0.07, 0.16, (-0.005, 0, 0), s["plate"], 0.01))
    if s.get("glow"):
        for i in range(4):
            parts.append(K.gem((0.03, 0, -0.045 + i * 0.03), 0.007, s["glow"], rot=(0, 90, 0)))
    return parts


# ---- ranged --------------------------------------------------------------------------------------------------------

def bow(s):
    parts = []
    L = s.get("len", 0.65)
    n = 14
    rec = s.get("recurve", 0.075)
    bend = s.get("bend", 0.11)
    pts_up, prof = [], []
    for i in range(n + 1):
        u = i / n
        z = 0.07 + (L - 0.07) * u
        x = -bend * u ** 1.5 + rec * max(u - 0.72, 0) ** 1.4 / 0.28 ** 1.4
        pts_up.append((x, 0, z))
        w = s.get("limb_w", 0.017) * (1 - 0.6 * u) + 0.004
        prof.append((w, s.get("limb_t", 0.013) * (1 - 0.5 * u) + 0.003))
    V, F = M.tube(pts_up, prof, n=8, up=(1, 0, 0), p=2.4)
    lm = s.get("limb_mat", "wood")
    up_limb = M.Part(V, F, lm, name="limb")
    lo_limb = up_limb.copy().scale((1, 1, -1)).flip()
    parts += [up_limb, lo_limb]
    parts.append(K.tube([(0.005, 0, -0.1), (0.012, 0, 0.0), (0.005, 0, 0.1)], [(0.018, 0.02), (0.022, 0.026), (0.018, 0.02)],
                        s.get("grip_mat", "leather"), n=10, up=(1, 0, 0)))
    for sz in (1, -1):
        p = K.lathe([(0, 0.08), (0.02, 0.08), (0.022, 0.1), (0.0, 0.11)], s.get("orn", "gold"), 8)
        if sz < 0:
            p.scale((1, 1, -1)).flip()
        parts.append(p)
    tip = np.array(pts_up[-1])
    parts.append(K.tube([(tip[0], 0, tip[2] - 0.01), (tip[0], 0, -tip[2] + 0.01)], [0.0018, 0.0018], s.get("string", "linen"), n=5, up=(1, 0, 0)))
    if s.get("horn_tips"):
        for sz in (1, -1):
            p = K.tube([(tip[0], 0, tip[2] - 0.03), (tip[0] + 0.01, 0, tip[2] + 0.02), (tip[0] + 0.035, 0, tip[2] + 0.045)],
                       [0.008, 0.006, 0.001], s["horn_tips"], n=6, up=(1, 0, 0))
            if sz < 0:
                p.scale((1, 1, -1)).flip()
            parts.append(p)
    if s.get("leaf_tips"):
        for sz in (1, -1):
            o = [(tip[0], tip[2] - 0.02), (tip[0] + 0.05, tip[2] - 0.06), (tip[0] + 0.03, tip[2] + 0.02), (tip[0] + 0.01, tip[2] + 0.06)]
            p = K.slab(o, 0.004, s["leaf_tips"])
            if sz < 0:
                p.scale((1, 1, -1)).flip()
            parts.append(p)
    if s.get("wraps"):
        for zz in (0.2, 0.3, -0.2, -0.3):
            u = (abs(zz) - 0.07) / (L - 0.07)
            x = -bend * u ** 1.5
            parts.append(K.band(0, 0.013, 0.012, s["wraps"], n=8).move((x, 0, zz)))
    if s.get("glow"):
        parts.append(K.gem((0.024, 0, 0.0), 0.012, s["glow"], rot=(0, 90, 0)))
        for sz in (1, -1):
            u = 0.5
            parts.append(K.gem((-bend * u ** 1.5 + 0.004, 0, sz * (0.07 + (L - 0.07) * u)), 0.008, s["glow"], rot=(0, 90, 0)))
    if s.get("thick_riser"):
        parts.append(K.box(0.04, 0.03, 0.34, (0.01, 0, 0), s["thick_riser"], 0.008))
    return parts


def staff(s):
    parts = []
    pts, prof = [], []
    wob = s.get("wobble", 0.012)
    for i in range(13):
        u = i / 12
        z = -1.05 + 1.62 * u
        pts.append((wob * math.sin(u * 9.0) + 0.006 * math.sin(u * 23), wob * 0.8 * math.cos(u * 7.0), z))
        r = 0.02 + 0.004 * math.sin(u * 17) + (0.006 if u > 0.9 else 0)
        prof.append((r, r * 0.92))
    V, F = M.tube(pts, prof, n=9, up=(0, -1, 0))
    parts.append(M.Part(V, F, s.get("wood", "wood"), name="shaft"))
    parts.append(grip(-0.1, 0.1, 0.023, s.get("grip_mat", "leather"), 5))
    head = s.get("head", "prongs")
    gm = s.get("gem", "ember")
    if head == "prongs":
        for k in range(4):
            a = k * 90 + 45
            pp = []
            for i in range(7):
                u = i / 6
                rr = 0.02 + 0.055 * math.sin(math.pi * u * 0.95)
                ang = math.radians(a + 40 * u)
                pp.append((rr * math.cos(ang), rr * math.sin(ang), 0.52 + 0.28 * u))
            parts.append(K.tube(pp, [0.009 * (1 - 0.7 * i / 6) + 0.002 for i in range(7)], s.get("metal", "darksteel"), n=6, up=(0, 0, 1)))
        parts.append(K.crystal((0, 0, 0.7), 0.24, 0.04, gm, rot=(0, 0, 15)))
    elif head == "fork":
        for sx in (1, -1):
            parts.append(K.tube([(0, 0, 0.55), (sx * 0.05, 0, 0.66), (sx * 0.06, 0, 0.8), (sx * 0.03, 0, 0.88)], [0.012, 0.01, 0.008, 0.003],
                                s.get("metal", "darksteel"), n=6))
        parts.append(K.crystal((0, 0, 0.72), 0.18, 0.032, gm))
        for k in range(3):
            parts.append(K.ring_tube((0, 0, 0.62 + 0.06 * k), 0.03 + 0.01 * k, 0.003, gm, axis="z", n=14))
    elif head == "shards":
        parts.append(K.crystal((0, 0, 0.72), 0.28, 0.045, gm))
        for k in range(5):
            a = math.radians(k * 72)
            parts.append(K.crystal((0.05 * math.cos(a), 0.05 * math.sin(a), 0.64), 0.14, 0.018, gm, rot=(math.degrees(0.4 * math.sin(a)), math.degrees(-0.4 * math.cos(a)), 0)))
    elif head == "star":
        parts.append(K.ring_tube((0, 0, 0.72), 0.09, 0.008, s.get("metal", "gold"), axis="y", n=28))
        parts.append(K.crystal((0, 0, 0.72), 0.14, 0.035, gm))
        for k in range(8):
            a = math.radians(k * 45)
            parts.append(K.cone_spike((0.09 * math.cos(a), 0, 0.72 + 0.09 * math.sin(a)), (0.13 * math.cos(a), 0, 0.72 + 0.13 * math.sin(a)), 0.008, s.get("metal", "gold")))
    for z in (0.5, 0.2):
        parts.append(K.band(z, 0.028, 0.024, s.get("band", "gold")))
    parts.append(K.lathe([(0, -1.08), (0.018, -1.07), (0.024, -1.03), (0.022, -0.99), (0, -0.98)], s.get("metal", "darksteel"), 8))
    return parts


def wand(s):
    parts = []
    pts, prof = [], []
    for k in range(11):
        u = k / 10
        z = -0.09 + 0.29 * u
        pts.append((0.0015 * math.sin(u * 7.0), 0.0012 * math.cos(u * 5.0), z))
        r = 0.0095 - 0.0038 * u + 0.0008 * math.sin(u * 19)
        prof.append((r, r))
    V, F = M.tube(pts, prof, n=12, up=(0, -1, 0))
    parts.append(M.Part(V, F, s.get("wood", "wood"), name="wand"))
    parts.append(grip(-0.07, 0.04, 0.0105, s.get("grip_mat", "leather"), 5))
    om = s.get("orn", "gold")
    for z in (0.045, 0.1):
        parts.append(K.band(z, 0.0105, 0.008, om, n=12))
    gm = s.get("gem", "sapphire")
    head = s.get("head", "claw")
    if head == "claw":
        parts.append(K.lathe([(0, 0.188), (0.008, 0.19), (0.011, 0.2), (0.0, 0.205)], om, 12))
        for k in range(4):
            a = math.radians(90 * k + 45)
            claw_p = [(0.008 * math.cos(a), 0.008 * math.sin(a), 0.198), (0.013 * math.cos(a), 0.013 * math.sin(a), 0.215),
                      (0.007 * math.cos(a), 0.007 * math.sin(a), 0.232)]
            parts.append(K.tube(claw_p, [0.0022, 0.0018, 0.001], om, n=5, up=(0, 0, 1)))
        parts.append(K.lathe([(0, 0.2), (0.0105, 0.212), (0.012, 0.222), (0.0085, 0.236), (0.0, 0.25)], gm, 8, "gem"))
    elif head == "skull":
        parts.append(K.sphere(0.022, (0, 0, 0.225), "bone", 10, 8, scale=(1, 0.9, 1.1)))
        for sx in (1, -1):
            parts.append(K.sphere(0.006, (sx * 0.008, -0.018, 0.228), gm, 6, 4))
        parts.append(K.box(0.02, 0.012, 0.01, (0, -0.01, 0.205), "bone"))
    elif head == "shell":
        parts.append(K.lathe([(0, 0.19), (0.012, 0.2), (0.022, 0.225), (0.014, 0.25), (0, 0.262)], "pearl", 7))
        parts.append(K.sphere(0.009, (0, 0, 0.228), gm, 8, 6))
    elif head == "sun":
        parts.append(K.sphere(0.013, (0, 0, 0.225), gm, 10, 8))
        for k in range(8):
            a = math.radians(k * 45)
            parts.append(K.cone_spike((0.012 * math.cos(a), 0, 0.225 + 0.012 * math.sin(a)), (0.03 * math.cos(a), 0, 0.225 + 0.03 * math.sin(a)), 0.004, om))
    parts.append(K.lathe([(0, -0.11), (0.011, -0.106), (0.013, -0.097), (0.011, -0.09), (0, -0.088)], om, 12))
    return parts


# ---- specs ---------------------------------------------------------------------------------------------------------
# (glow keys are filled from the item's element by build_items when not set explicitly)

SPECS = {
    # swords (original three + five)
    "iron_longsword": (sword, {"blade": "steel", "guard_mat": "iron", "pommel_mat": "iron"}),
    "knights_arming_sword": (sword, {"len": 0.82, "guard": "winged", "guard_mat": "gold", "w": (0.05, 0.03), "pommel": "disc", "grip_mat": "crimson"}),
    "runed_sword": (sword, {"len": 0.86, "blade": "bright", "guard_half": 0.12, "guard_curve": -0.02, "gem": "topaz", "glow": "holy"}),
    "militia_shortsword": (sword, {"len": 0.58, "w": (0.05, 0.042), "shape": "leaf", "guard": "bar", "guard_half": 0.07, "guard_mat": "bronze",
                                   "pommel_mat": "bronze", "blade": "iron", "grip_mat": "wool"}),
    "riverguard_falchion": (sword, {"len": 0.72, "w": (0.045, 0.075), "shape": "falchion", "guard_half": 0.08, "guard_mat": "darksteel",
                                    "pommel": "disc", "pommel_mat": "darksteel", "tip": 0.09}),
    "duelist_sabre": (sword, {"len": 0.84, "w": (0.034, 0.028), "shape": "sabre", "guard": "swept", "guard_mat": "silver", "pommel_mat": "silver",
                              "grip_mat": "darkleather", "thick": 0.005}),
    "bastard_sword": (sword, {"len": 0.98, "w": (0.058, 0.04), "grip_len": 0.24, "guard_half": 0.14, "guard_mat": "darksteel", "pommel": "disc",
                              "pommel_mat": "darksteel", "ricasso": "darksteel"}),
    "sunsteel_blade": (sword, {"len": 0.9, "blade": "sunsteel", "shape": "waisted", "guard": "winged", "guard_half": 0.14, "guard_mat": "gold",
                               "gem": "ruby", "glow": "ember", "pommel": "spike"}),
    # greatswords
    "rusted_claymore": (sword, {"len": 1.18, "z0": 0.135, "w": (0.062, 0.044), "thick": 0.0075, "blade": "rust", "guard_half": 0.2, "guard_curve": 0.05,
                                "guard_mat": "iron", "grip_len": 0.34, "grip_r": 0.017, "pommel_mat": "iron", "tip": 0.16}),
    "executioner_blade": (sword, {"len": 1.12, "z0": 0.135, "w": (0.1, 0.11), "thick": 0.009, "shape": "straight", "tip": 0.04, "blade": "darksteel",
                                  "guard_half": 0.16, "guard_mat": "blackiron", "grip_len": 0.34, "grip_r": 0.018, "pommel": "ring", "pommel_mat": "blackiron"}),
    "titan_greatsword": (sword, {"len": 1.26, "z0": 0.135, "w": (0.075, 0.05), "thick": 0.009, "blade": "bright", "guard": "winged", "guard_half": 0.2,
                                 "guard_mat": "gold", "grip_len": 0.34, "grip_r": 0.018, "lugs": True, "gem": "sapphire", "pommel": "disc"}),
    # axes
    "hand_axe": (axe, {"head": "bearded"}),
    "bearded_axe": (axe, {"head": "bearded", "head_scale": 1.15, "head_mat": "darksteel", "wrap": "redleather"}),
    "rune_cleaver": (axe, {"head": "cleaver", "head_mat": "bright", "glow": "earth", "band_mat": "bronze"}),
    "woodcutter_hatchet": (axe, {"head": "hatchet", "haft_mat": "ash", "spike": False, "head_mat": "iron", "band_mat": "iron"}),
    "raider_tomahawk": (axe, {"head": "tomahawk", "haft_mat": "redwood", "spike_mat": "iron", "feathers": "white", "wrap": "tan"}),
    "crescent_axe": (axe, {"head": "crescent", "head_mat": "steel", "haft_mat": "darkwood", "band_mat": "silver", "head_scale": 1.1}),
    "rimebite_axe": (axe, {"head": "bearded", "head_mat": "moonsteel", "glow": "ice", "band_mat": "silver", "haft_mat": "darkwood", "head_scale": 1.1}),
    "warlord_cleaver": (axe, {"head": "cleaver", "head_mat": "blackiron", "head_scale": 1.25, "band_mat": "gold", "wrap": "crimson", "pommel": True}),
    # great axes
    "lumber_greataxe": (axe, {"two_handed": True, "head": "hatchet", "haft_mat": "ash", "head_mat": "iron", "band_mat": "iron", "spike": False,
                              "head_scale": 2.0}),
    "double_bit_greataxe": (axe, {"two_handed": True, "head": "crescent", "double": True, "head_mat": "steel", "haft_mat": "wood", "head_scale": 1.2}),
    "northman_greataxe": (axe, {"two_handed": True, "head": "bearded", "head_mat": "darksteel", "head_scale": 1.55, "wrap": "fur", "band_mat": "bronze"}),
    "executioner_moon": (axe, {"two_handed": True, "head": "moon", "head_mat": "bright", "head_scale": 1.3, "haft_mat": "darkwood", "band_mat": "blackiron",
                               "pommel": True}),
    "worldsplitter": (axe, {"two_handed": True, "head": "broad", "double": True, "head_mat": "blackiron", "head_scale": 1.25, "glow": "earth",
                            "band_mat": "gold", "pommel": True}),
    # spears
    "ash_spear": (spear, {"shaft_mat": "ash"}),
    "winged_spear": (spear, {"head": "partisan", "head_w": 0.06, "band_mat": "gold", "tassel": "crimson"}),
    "storm_lance": (spear, {"head": "lance", "head_len": 0.4, "head_mat": "bright", "glow": "storm"}),
    "hunting_spear": (spear, {"head": "barbed", "head_w": 0.06, "shaft_mat": "ash", "band_mat": "rope", "butt": False}),
    "partisan": (spear, {"head": "partisan", "head_len": 0.36, "head_w": 0.08, "shaft_mat": "darkwood", "band_mat": "iron"}),
    "glaive": (spear, {"head": "glaive", "head_len": 0.46, "shaft_mat": "wood", "band_mat": "gold", "tassel": "navy"}),
    "tideguard_trident": (spear, {"head": "trident", "head_len": 0.3, "head_mat": "bronze", "band_mat": "bronze", "shaft_mat": "darkwood", "glow": "tide"}),
    "wyrmtooth_lance": (spear, {"head": "leaf", "head_len": 0.42, "head_w": 0.09, "head_mat": "bone", "shaft_mat": "redwood", "band_mat": "gold",
                                "tassel": "crimson"}),
    # javelins
    "reed_javelin": (javelin, {"head": "leaf", "head_w": 0.035, "shaft_mat": "reed", "head_mat": "iron", "band_mat": "rope", "fins": "white"}),
    "hunters_javelin": (javelin, {"head": "barbed", "head_w": 0.04, "shaft_mat": "ash", "band_mat": "leather", "fins": "tan"}),
    "barbed_pilum": (javelin, {"head": "pilum", "head_len": 0.32, "shaft_mat": "wood", "head_mat": "darksteel", "band_mat": "iron"}),
    "thunderhead_javelin": (javelin, {"head": "bolt", "head_len": 0.26, "head_mat": "bright", "shaft_mat": "darkwood", "band_mat": "gold", "glow": "storm",
                                      "fins": "navy"}),
    "sunpiercer": (javelin, {"head": "sun", "head_len": 0.24, "head_mat": "sunsteel", "shaft_mat": "ash", "band_mat": "gold", "glow": "holy", "fins": "white"}),
    # clubs
    "oak_cudgel": (club, {"kind": "cudgel", "wood": "wood"}),
    "spiked_club": (club, {"kind": "cudgel", "wood": "darkwood", "spikes": True}),
    "flanged_mace": (club, {"kind": "flanged", "head_mat": "steel", "flanges": 6}),
    "morning_star": (club, {"kind": "morningstar", "head_mat": "darksteel", "spike_mat": "steel", "haft_mat": "darkwood"}),
    "emberheart_mace": (club, {"kind": "flanged", "head_mat": "blackiron", "flanges": 8, "glow": "ember", "grip_mat": "redleather"}),
    # daggers
    "rondel_dagger": (dagger, {"guard": "disc", "guard_mat": "iron", "pommel": "disc", "pommel_mat": "iron", "w": (0.028, 0.014)}),
    "shadow_kris": (dagger, {"shape": "kris", "blade": "darksteel", "guard_mat": "gold", "glow": "shadow"}),
    "aether_stiletto": (dagger, {"len": 0.3, "w": (0.018, 0.01), "blade": "moonsteel", "guard_mat": "silver", "gem": "aether", "thick": 0.0045}),
    "skinning_knife": (dagger, {"len": 0.2, "shape": "skinner", "guard": "none", "grip_mat": "horn", "pommel_mat": "bronze", "w": (0.03, 0.028)}),
    "parrying_dirk": (dagger, {"len": 0.3, "guard": "wide", "guard_mat": "steel", "pommel_mat": "steel", "grip_mat": "darkleather"}),
    "kukri": (dagger, {"len": 0.3, "shape": "kukri", "w": (0.03, 0.05), "guard": "disc", "guard_mat": "brass", "grip_mat": "horn", "pommel_mat": "brass"}),
    "viper_fang": (dagger, {"len": 0.27, "shape": "kris", "blade": "blued", "guard_mat": "darksteel", "glow": "venom", "gem": "emerald"}),
    "moonshard_dagger": (dagger, {"len": 0.3, "shape": "crescent", "blade": "moonsteel", "guard_mat": "silver", "glow": "ice", "gem": "sapphire"}),
    # claws
    "iron_talons": (claw, {"blades": 3, "blade": "iron", "frame_mat": "iron"}),
    "tiger_claw": (claw, {"blades": 4, "blade": "steel", "hook": 0.05, "spacing": 0.03, "frame_mat": "darksteel", "plate_mat": "brass"}),
    "hookblade_claws": (claw, {"blades": 2, "len": 0.3, "hook": 0.09, "spacing": 0.05, "blade": "bright", "spikes": True}),
    "nightstalker_claw": (claw, {"blades": 3, "len": 0.28, "hook": 0.06, "blade": "blackiron", "frame_mat": "blackiron", "glow": "shadow"}),
    "drakescale_rend": (claw, {"blades": 3, "len": 0.3, "hook": 0.07, "blade": "sunsteel", "frame_mat": "darksteel", "plate_mat": "redwood",
                               "scales": "redleather", "glow": "ember"}),
    # knuckles
    "brass_knuckles": (knuckles, {"mat": "brass"}),
    "studded_cestus": (knuckles, {"kind": "cestus", "wrap": "tan", "stud": "iron"}),
    "spiked_knucklebars": (knuckles, {"mat": "iron", "spikes": 4, "spike_mat": "steel"}),
    "thunderfist_knuckles": (knuckles, {"mat": "darksteel", "spikes": 2, "spike_mat": "bright", "glow": "storm"}),
    "titanknuckle": (knuckles, {"mat": "blackiron", "plate": "darksteel", "spikes": 3, "spike_len": 0.04, "spike_mat": "gold"}),
    # bows
    "hunters_bow": (bow, {}),
    "composite_bow": (bow, {"limb_mat": "horn", "wraps": "leather", "recurve": 0.1}),
    "warden_longbow": (bow, {"len": 0.82, "bend": 0.13, "recurve": 0.02, "limb_mat": "darkwood", "orn": "silver"}),
    "shortbow": (bow, {"len": 0.5, "bend": 0.09, "recurve": 0.03, "limb_mat": "ash", "orn": "rope"}),
    "recurve_bow": (bow, {"len": 0.62, "recurve": 0.11, "limb_mat": "redwood", "wraps": "tan"}),
    "hornbow": (bow, {"len": 0.58, "bend": 0.13, "recurve": 0.12, "limb_mat": "horn", "horn_tips": "bone", "orn": "bronze"}),
    "siege_greatbow": (bow, {"len": 0.92, "bend": 0.15, "recurve": 0.05, "limb_w": 0.024, "limb_t": 0.018, "limb_mat": "darkwood",
                             "thick_riser": "iron", "orn": "iron"}),
    "galewing_bow": (bow, {"len": 0.7, "bend": 0.12, "recurve": 0.13, "limb_mat": "ash", "leaf_tips": "silver", "orn": "silver", "glow": "wind"}),
    # staves and wands
    "ashwood_staff": (staff, {"wood": "ash", "gem": "ember"}),
    "storm_staff": (staff, {"head": "fork", "gem": "storm", "wood": "darkwood", "metal": "darksteel"}),
    "frost_staff": (staff, {"head": "shards", "gem": "ice", "wood": "darkwood", "band": "silver"}),
    "bone_wand": (wand, {"wood": "bone", "head": "skull", "gem": "shadow", "orn": "darksteel"}),
    "tide_wand": (wand, {"wood": "darkwood", "head": "shell", "gem": "tide", "orn": "silver"}),
    "sunfire_wand": (wand, {"wood": "redwood", "head": "sun", "gem": "holy", "orn": "gold"}),
    # set pieces / uniques
    "sage_staff": (staff, {"head": "star", "gem": "holy", "wood": "darkwood", "metal": "gold", "band": "gold"}),
    "u_dawnbreaker": (sword, {"len": 1.24, "z0": 0.135, "w": (0.072, 0.05), "thick": 0.009, "blade": "sunsteel", "guard": "winged", "guard_half": 0.22,
                              "guard_mat": "gold", "grip_len": 0.34, "grip_r": 0.018, "gem": "aether", "glow": "holy", "pommel": "spike", "lugs": True}),
    "u_riftblade": (sword, {"len": 0.86, "blade": "blackiron", "guard_half": 0.12, "guard_curve": -0.03, "guard_mat": "silver", "gem": "aether",
                            "glow": "aether", "pommel": "disc", "pommel_mat": "silver"}),
    "u_starwhisper": (staff, {"head": "star", "gem": "aether", "wood": "ash", "metal": "silver", "band": "silver"}),
    "u_winters_heart": (wand, {"wood": "moonsteel", "head": "claw", "gem": "ice", "orn": "silver"}),
}
