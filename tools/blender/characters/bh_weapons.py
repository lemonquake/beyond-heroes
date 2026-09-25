"""Weapon builders. Origin = main-hand grip center (shield: handle, arrow: center). Long axis +Z.
Blade flats face +-Y, edges +-X. Shield face -Y. Bow: string on -X side (archer), belly faces +X... (target +X).
Each builder returns a list of Parts (bone field unused)."""
import math
import numpy as np

import bh_mesh as M
from bh_math import Rx, Ry, Rz


def _blade(z0, z1, w0, w1, t, tip=0.12, n_sec=8, fuller=True, mat="BH_Steel"):
    """Double-edged blade along Z from z0 (base) to z1 (tip) with lenticular/fullered section."""
    rings = []
    zs = list(np.linspace(z0, z1 - tip, n_sec)) + list(np.linspace(z1 - tip, z1, 5)[1:])
    for z in zs:
        if z <= z1 - tip:
            u = (z - z0) / max(z1 - tip - z0, 1e-6)
            w = w0 + (w1 - w0) * u
            th = t * (1 - 0.25 * u)
        else:
            u = (z - (z1 - tip)) / tip
            w = w1 * max(1 - u, 0.0) ** 0.8 + 0.0005
            th = t * 0.75 * max(1 - u, 0.0) ** 0.7 + 0.0004
        hw = w / 2
        f = 0.55 if fuller else 0.9
        sec = [(hw, 0), (0.45 * hw, th), (0.15 * hw, th * f), (-0.15 * hw, th * f), (-0.45 * hw, th),
               (-hw, 0), (-0.45 * hw, -th), (-0.15 * hw, -th * f), (0.15 * hw, -th * f), (0.45 * hw, -th)]
        rings.append(np.array([(x, y, z) for x, y in sec]))
    V, F = M.loft(rings, cap0=True, cap1=True)
    return M.Part(V, F, mat, name="blade")


def _grip(z0, z1, r, ridges=6, mat="BH_Leather"):
    prof = []
    n = ridges * 2 + 1
    for i in range(n + 1):
        z = z0 + (z1 - z0) * i / n
        rr = r * (1.0 + (0.12 if i % 2 else 0.0)) * (1 + 0.1 * math.sin(math.pi * i / n))
        prof.append((rr, z))
    prof = [(0.0, z0)] + prof + [(0.0, z1)]
    V, F = M.lathe(prof, 10)
    return M.Part(V, F, mat, name="grip")


def _crossguard(z, half, h=0.022, t=0.02, curve=0.02, mat="BH_Gold"):
    pts, prof = [], []
    for i in range(9):
        u = -1 + 2 * i / 8
        x = u * half
        pts.append((x, 0, z + curve * u * u))
        s = 1.0 + 0.5 * abs(u) ** 4
        prof.append((t * 0.5 * s, h * 0.5 * s, 3.0))
    V, F = M.tube(pts, prof, n=8, up=(0, 0, 1))
    # tube: rx across (perp to up) = Y thickness, ry along up = Z height
    return M.Part(V, F, mat, name="guard")


def _pommel(z, r, mat="BH_Gold"):
    prof = [(0, z - r * 0.9), (r * 0.55, z - r * 0.85), (r, z - r * 0.35), (r * 1.02, z), (r * 0.8, z + r * 0.5),
            (r * 0.4, z + r * 0.8), (0, z + r * 0.85)]
    V, F = M.lathe(prof, 12)
    p = M.Part(V, F, mat, name="pommel")
    p.scale((1.0, 0.6, 1.0), center=(0, 0, z))
    return p


def sword():
    parts = [
        _blade(0.105, 0.88, 0.052, 0.036, 0.0065, tip=0.13),
        M.bevel(_crossguard(0.09, 0.115), 0.003, 1),
        _grip(-0.085, 0.078, 0.0155, 6),
        M.bevel(_pommel(-0.1, 0.028), 0.002, 1),
    ]
    # ricasso collar
    V, F = M.lathe([(0, 0.078), (0.02, 0.078), (0.022, 0.09), (0.0, 0.1)], 10)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="collar"))
    return parts


def greatsword():
    parts = [
        _blade(0.135, 1.32, 0.064, 0.042, 0.0075, tip=0.16, n_sec=10),
        M.bevel(_crossguard(0.115, 0.19, h=0.03, t=0.026, curve=-0.03), 0.004, 1),
        _grip(-0.25, 0.1, 0.017, 9),
        M.bevel(_pommel(-0.27, 0.035), 0.002, 1),
    ]
    # ricasso + parrying lugs (distinct silhouette)
    for sx in (1, -1):
        V, F = M.prism([(0.0, 0.0), (0.045, 0.02), (0.05, 0.035), (0.0, 0.03)], 0.012, axis="y")
        p = M.Part(V, F, "BH_DarkSteel", name="lug")
        if sx < 0:
            p = p.mirrored(False)
        p.move((sx * 0.03, 0, 0.26))
        parts.append(M.bevel(p, 0.002, 1))
    V, F = M.box(0.07, 0.022, 0.05, center=(0, 0, 0.14))
    parts.append(M.bevel(M.Part(V, F, "BH_DarkSteel", name="ricasso"), 0.004, 2))
    return parts


def axe():
    parts = []
    # haft
    prof = [(0, -0.16), (0.02, -0.16), (0.022, -0.14), (0.017, -0.12), (0.016, 0.3), (0.017, 0.62), (0.014, 0.66), (0, 0.67)]
    V, F = M.lathe(prof, 10)
    parts.append(M.Part(V, F, "BH_Wood", name="haft"))
    parts.append(_grip(-0.11, 0.1, 0.0175, 5))
    # bearded head on +X
    out = [(0.02, 0.46), (0.08, 0.47), (0.15, 0.52), (0.21, 0.60), (0.225, 0.54), (0.23, 0.46), (0.225, 0.38),
           (0.20, 0.30), (0.17, 0.33), (0.12, 0.40), (0.06, 0.43), (0.02, 0.42), (0.02, 0.44)]
    out = list(reversed(out)) if False else out
    V, F = M.prism(M.resample_closed(out, 40)[::-1], 0.03, axis="y")
    head = M.Part(V, F, "BH_Steel", name="axehead")
    head.warp(lambda v: (v[0], v[1] * (1.0 - 0.8 * min(max((v[0] - 0.03) / 0.2, 0), 1)), v[2]))
    parts.append(M.bevel(head, 0.002, 1, angle=50))
    # back spike
    V, F = M.tube([(-0.01, 0, 0.47), (-0.09, 0, 0.465), (-0.135, 0, 0.44)], [(0.018, 0.022), (0.01, 0.012), (0.001, 0.001)],
                  n=6, up=(0, 0, 1))
    parts.append(M.Part(V, F, "BH_DarkSteel", name="spike"))
    # socket / langets
    V, F = M.lathe([(0, 0.40), (0.026, 0.40), (0.028, 0.43), (0.028, 0.53), (0.024, 0.55), (0.0, 0.56)], 10)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="socket"))
    for z in (0.36, 0.33):
        V, F = M.lathe([(0.0, z - 0.008), (0.021, z - 0.008), (0.021, z + 0.008), (0, z + 0.008)], 10)
        parts.append(M.Part(V, F, "BH_Gold", name="band"))
    return parts


def spear():
    parts = []
    prof = [(0, -0.9), (0.006, -0.9), (0.017, -0.84), (0.019, -0.78), (0.018, 0.0), (0.017, 0.98), (0.0, 0.99)]
    V, F = M.lathe(prof, 10)
    parts.append(M.Part(V, F, "BH_Wood", name="shaft"))
    parts.append(_grip(-0.1, 0.1, 0.0195, 5))
    parts.append(_grip(0.4, 0.6, 0.0195, 5))
    # leaf head
    rings = []
    for z, w in ((0.99, 0.024), (1.03, 0.05), (1.10, 0.078), (1.17, 0.07), (1.24, 0.04), (1.29, 0.012), (1.30, 0.002)):
        hw = w / 2
        th = 0.012 * (w / 0.078) + 0.002
        rings.append(np.array([(hw, 0, z), (0, th, z), (-hw, 0, z), (0, -th, z)]))
    V, F = M.loft(rings)
    parts.append(M.Part(V, F, "BH_Steel", name="spearhead"))
    V, F = M.lathe([(0, 0.92), (0.02, 0.92), (0.024, 0.96), (0.02, 1.0), (0.0, 1.01)], 10)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="socket"))
    for z in (0.9, -0.76):
        V, F = M.lathe([(0.0, z - 0.01), (0.022, z - 0.01), (0.022, z + 0.01), (0, z + 0.01)], 10)
        parts.append(M.Part(V, F, "BH_Gold", name="band"))
    return parts


def dagger():
    parts = [
        _blade(0.05, 0.33, 0.036, 0.022, 0.005, tip=0.07, n_sec=5),
        M.bevel(_crossguard(0.042, 0.06, h=0.014, t=0.016, curve=0.012), 0.002, 1),
        _grip(-0.05, 0.035, 0.013, 4),
        M.bevel(_pommel(-0.062, 0.018), 0.002, 1),
    ]
    return parts


def bow():
    """Recurve bow held in the left hand: grip at origin, limbs along +-Z, string on -X (archer side)."""
    parts = []
    pts_up, prof = [], []
    n = 14
    for i in range(n + 1):
        u = i / n
        z = 0.07 + 0.58 * u
        x = -0.11 * u ** 1.5 + 0.075 * max(u - 0.72, 0) ** 1.4 / 0.28 ** 1.4
        pts_up.append((x, 0, z))
        w = 0.017 * (1 - 0.6 * u) + 0.004
        prof.append((w, 0.013 * (1 - 0.5 * u) + 0.003))
    limb = M.tube(pts_up, prof, n=8, up=(1, 0, 0), p=2.4)
    up_limb = M.Part(limb[0], limb[1], "BH_Wood", name="limb")
    lo_limb = up_limb.copy().scale((1, 1, -1)).flip()
    parts += [up_limb, lo_limb]
    # riser / grip
    V, F = M.tube([(0.005, 0, -0.1), (0.012, 0, 0.0), (0.005, 0, 0.1)], [(0.018, 0.02), (0.022, 0.026), (0.018, 0.02)],
                  n=10, up=(1, 0, 0))
    parts.append(M.Part(V, F, "BH_Leather", name="riser"))
    for sz in (1, -1):
        V, F = M.lathe([(0, 0.08), (0.02, 0.08), (0.022, 0.1), (0.0, 0.11)], 8)
        p = M.Part(V, F, "BH_Gold", name="riserband")
        if sz < 0:
            p.scale((1, 1, -1)).flip()
        parts.append(p)
    tip = np.array(pts_up[-1])
    # string
    V, F = M.tube([(tip[0], 0, tip[2] - 0.01), (tip[0], 0, -tip[2] + 0.01)], [(0.0018, 0.0018)] * 2, n=5, up=(1, 0, 0))
    parts.append(M.Part(V, F, "BH_Cloth_Secondary", name="string"))
    return parts


def arrow():
    parts = []
    V, F = M.lathe([(0, -0.37), (0.004, -0.37), (0.0045, 0.32), (0, 0.325)], 6)
    parts.append(M.Part(V, F, "BH_Wood", name="shaft"))
    V, F = M.lathe([(0, 0.31), (0.009, 0.325), (0.0, 0.378)], 4)
    parts.append(M.Part(V, F, "BH_Steel", name="head"))
    for k in range(3):
        V, F = M.prism([(0.004, -0.34), (0.02, -0.33), (0.016, -0.24), (0.004, -0.22)], 0.0012, axis="y")
        parts.append(M.Part(V, F, "BH_Cloth_Primary", name="fletch").rot(Rz(120 * k)))
    return parts


def staff():
    parts = []
    pts = []
    prof = []
    for i in range(13):
        u = i / 12
        z = -1.05 + 1.62 * u
        x = 0.012 * math.sin(u * 9.0) + 0.006 * math.sin(u * 23)
        y = 0.01 * math.cos(u * 7.0)
        pts.append((x, y, z))
        r = 0.02 + 0.004 * math.sin(u * 17) + (0.006 if u > 0.9 else 0)
        prof.append((r, r * 0.92))
    V, F = M.tube(pts, prof, n=9, up=(0, -1, 0))
    parts.append(M.Part(V, F, "BH_Wood", name="shaft"))
    parts.append(_grip(-0.1, 0.1, 0.023, 5))
    # prongs cradling the crystal
    for k in range(4):
        a = k * 90 + 45
        pp = []
        for i in range(7):
            u = i / 6
            r = 0.02 + 0.055 * math.sin(math.pi * u * 0.95)
            z = 0.52 + 0.28 * u
            ang = math.radians(a + 40 * u)
            pp.append((r * math.cos(ang), r * math.sin(ang), z))
        V, F = M.tube(pp, [(0.009 * (1 - 0.7 * i / 6) + 0.002,) * 2 for i in range(7)], n=6, up=(0, 0, 1))
        parts.append(M.Part(V, F, "BH_DarkSteel", name="prong"))
    # crystal (elongated bipyramid)
    V, F = M.lathe([(0, 0.57), (0.03, 0.62), (0.04, 0.68), (0.032, 0.74), (0.0, 0.82)], 6)
    parts.append(M.Part(V, F, "BH_Emissive", name="crystal").rot(Rz(15)))
    for z in (0.5, 0.2):
        V, F = M.lathe([(0.0, z - 0.012), (0.027, z - 0.012), (0.029, z), (0.027, z + 0.012), (0, z + 0.012)], 10)
        parts.append(M.Part(V, F, "BH_Gold", name="band"))
    # butt cap
    V, F = M.lathe([(0, -1.08), (0.018, -1.07), (0.024, -1.03), (0.022, -0.99), (0, -0.98)], 8)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="cap"))
    return parts


def wand():
    parts = []
    prof = [(0, -0.1), (0.008, -0.1), (0.011, -0.09), (0.009, -0.07), (0.0095, 0.05), (0.0065, 0.2), (0.0, 0.215)]
    V, F = M.lathe(prof, 8)
    parts.append(M.Part(V, F, "BH_Wood", name="wand"))
    parts.append(_grip(-0.065, 0.05, 0.0105, 4))
    V, F = M.lathe([(0, 0.19), (0.012, 0.2), (0.014, 0.215), (0.0, 0.225)], 8)
    parts.append(M.Part(V, F, "BH_Gold", name="setting"))
    V, F = M.lathe([(0, 0.205), (0.013, 0.225), (0.012, 0.24), (0.0, 0.25)], 6)
    parts.append(M.Part(V, F, "BH_Emissive", name="gem"))
    V, F = M.lathe([(0, -0.11), (0.012, -0.105), (0.013, -0.095), (0, -0.09)], 8)
    parts.append(M.Part(V, F, "BH_Gold", name="cap"))
    return parts


def shield_outline(w=0.64, top=0.4, bottom=-0.5, n=48):
    hw = w / 2
    # heater: flat-ish top, straight upper sides, curving to a point
    side = []
    for i in range(12):
        u = i / 11
        z = top - 0.08 * 0 - (top - bottom) * u
        # width profile
        if z > 0.05:
            x = hw
        else:
            k = (0.05 - z) / (0.05 - bottom)
            x = hw * math.cos(k * math.pi / 2) ** 0.8
        side.append((x, z))
    right = side
    left = [(-x, z) for x, z in side]
    top_edge = [(-hw + 2 * hw * i / 6, top + 0.025 * math.sin(math.pi * i / 6)) for i in range(1, 6)]
    outline = [(0.0, bottom)] + list(reversed([p for p in right[:-1]])) + top_edge[::-1] + [p for p in left[:-1]]
    # CCW in (x,z)
    o = np.array(outline)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    return M.resample_closed(o, n)


def emblem_parts(scale=1.0, mat="BH_Gold", depth=0.008):
    """Order emblem: ring with a downward sword and two wing chevrons. Built in XZ plane, facing -Y."""
    parts = []
    # ring
    ring_o = [(math.cos(a) * 0.1, math.sin(a) * 0.1 + 0.03) for a in np.linspace(0, 2 * math.pi, 32, endpoint=False)]
    V, F = M.lathe([(0.075, -depth / 2), (0.1, -depth / 2), (0.1, depth / 2), (0.075, depth / 2), (0.075, -depth / 2)], 32)
    p = M.Part(V, F, mat, name="ring").rot(Rx(90)).move((0, 0, 0.03))
    parts.append(p)
    # sword pointing down
    sw = [(0.0, -0.2), (0.022, -0.12), (0.022, 0.12), (0.06, 0.12), (0.06, 0.15), (0.018, 0.15), (0.018, 0.2),
          (0.03, 0.22), (0.0, 0.25), (-0.03, 0.22), (-0.018, 0.2), (-0.018, 0.15), (-0.06, 0.15), (-0.06, 0.12),
          (-0.022, 0.12), (-0.022, -0.12)]
    V, F = M.prism(sw[::-1], depth * 1.6, axis="y")
    parts.append(M.Part(V, F, mat, name="esword"))
    for sx in (1, -1):
        wing = [(0.11, 0.05), (0.2, 0.12), (0.19, 0.08), (0.24, 0.07), (0.2, 0.04), (0.23, 0.01), (0.17, 0.0), (0.12, 0.0)]
        if sx < 0:
            wing = [(-x, z) for x, z in wing]
        o = np.array(wing)
        area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
        if area < 0:
            o = o[::-1]
        V, F = M.prism(o, depth, axis="y")
        parts.append(M.Part(V, F, mat, name="wing"))
    for p in parts:
        p.scale(scale)
    return parts


def shield():
    parts = []
    o = shield_outline()
    V, F = M.plate_from_outline(o, 0.0, rings=6, bulge=0.05, axis="y")
    face = M.Part(V, F, "BH_Cloth_Primary", name="shield_face")
    # cylindrical curvature around Z (sides bend back toward +Y)
    face.warp(lambda v: (v[0], v[1] + 0.35 * v[0] ** 2 - 0.06, v[2]))
    body = M.solidify(face.copy().to(mat="BH_Wood").move((0, 0.002, 0)), 0.022, offset=-1.0)
    parts.append(body)
    parts.append(face.scale((0.985, 1, 0.985), center=(0, 0, -0.03)))
    # rim: tube along outline, following curvature
    rim_pts = [(x, 0.35 * x * x - 0.06 - 0.005, z) for x, z in o]
    rim_pts.append(rim_pts[0])
    V, F = M.tube(rim_pts, [(0.016, 0.018)] * len(rim_pts), n=6, up=(0, -1, 0), cap0=False, cap1=False)
    parts.append(M.Part(V, F, "BH_Steel", name="rim"))
    # emblem on the face
    for p in emblem_parts(1.05):
        p.move((0, 0, 0.0))
        p.warp(lambda v: (v[0], v[1] + 0.35 * v[0] ** 2 - 0.06 - 0.05 * (1 - min((v[0] ** 2 / 0.1 + v[2] ** 2 / 0.2), 1.5) / 1.5) - 0.006, v[2]))
        parts.append(M.bevel(p, 0.0015, 1))
    # back: leather straps + handle (origin)
    V, F = M.tube([(-0.09, -0.035, 0.0), (-0.05, 0.02, 0.0), (0.05, 0.02, 0.0), (0.09, -0.035, 0.0)],
                  [(0.012, 0.04)] * 4, n=6, up=(0, 0, 1))
    parts.append(M.Part(V, F, "BH_Leather", name="handle"))
    V, F = M.box(0.26, 0.012, 0.05, center=(0, -0.03, 0.2))
    parts.append(M.Part(V, F, "BH_Leather", name="strap"))
    # boss rivets along the top
    for x in (-0.24, 0.0, 0.24):
        V, F = M.sphere(0.014, 6, 4, center=(x, 0.35 * x * x - 0.083, 0.34))
        parts.append(M.Part(V, F, "BH_Gold", name="rivet"))
    return parts


WEAPONS = {
    "sword": sword, "greatsword": greatsword, "axe": axe, "spear": spear, "dagger": dagger, "bow": bow,
    "staff": staff, "wand": wand, "shield": shield, "arrow": arrow,
}

# Godot-side attachment (BoneAttachment3D child transform, Godot axes), verified in previews.
SOCKETS = {
    "sword": ("weapon.R", (0, 0, 0)),
    "greatsword": ("weapon.R", (0, 0, 0)),
    "axe": ("weapon.R", (0, 0, 0)),
    "spear": ("weapon.R", (0, 0, 0)),
    "dagger": ("weapon.R", (0, 0, 0)),
    "staff": ("weapon.R", (0, 0, 0)),
    "wand": ("weapon.R", (0, 0, 0)),
    "bow": ("weapon.L", (0, 0, 0)),
    "shield": ("weapon.L", (0, 90, 0)),
}
