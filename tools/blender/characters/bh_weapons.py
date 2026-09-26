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
    V, F = M.lathe([(0, -0.372), (0.0042, -0.372), (0.0046, -0.36), (0.0046, 0.3), (0.0042, 0.318), (0, 0.322)], 14)
    parts.append(M.Part(V, F, "BH_Wood", name="shaft"))
    # nock
    V, F = M.lathe([(0, -0.382), (0.0052, -0.382), (0.006, -0.37), (0.0052, -0.358), (0, -0.356)], 14)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="nock"))
    # bodkin-leaf head with a socket
    V, F = M.lathe([(0, 0.3), (0.0062, 0.302), (0.0065, 0.318), (0.0, 0.322)], 14)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="socket"))
    rings = []
    for z, w, t in ((0.316, 0.006, 0.004), (0.33, 0.017, 0.0035), (0.35, 0.02, 0.003), (0.368, 0.01, 0.002),
                    (0.38, 0.0008, 0.0006)):
        rings.append(np.array([(w, 0, z), (0.3 * w, t, z), (-0.3 * w, t, z), (-w, 0, z), (-0.3 * w, -t, z),
                               (0.3 * w, -t, z)]))
    V, F = M.loft(rings)
    parts.append(M.Part(V, F, "BH_Steel", name="head"))
    # three curved vanes + binding wraps
    for k in range(3):
        o = [(0.0045, -0.345), (0.012, -0.338), (0.021, -0.322), (0.022, -0.29), (0.018, -0.25), (0.0045, -0.228)]
        V, F = M.prism(M.resample_closed(o, 18), 0.0014, axis="y")
        vane = M.Part(V, F, "BH_Cloth_Primary", name="fletch")
        vane.warp(lambda v: (v[0], v[1] + 0.02 * (v[2] + 0.29) ** 2 * 10, v[2]))
        parts.append(vane.rot(Rz(120 * k + 30)))
    for z in (-0.352, -0.222):
        V, F = M.lathe([(0, z - 0.004), (0.0054, z - 0.004), (0.0056, z), (0.0054, z + 0.004), (0, z + 0.004)], 14)
        parts.append(M.Part(V, F, "BH_Gold", name="wrap"))
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
    # slender tapered shaft with a slight organic wobble
    pts, prof = [], []
    for k in range(11):
        u = k / 10
        z = -0.09 + 0.29 * u
        pts.append((0.0015 * math.sin(u * 7.0), 0.0012 * math.cos(u * 5.0), z))
        r = 0.0095 - 0.0038 * u + 0.0008 * math.sin(u * 19)
        prof.append((r, r))
    V, F = M.tube(pts, prof, n=12, up=(0, -1, 0))
    parts.append(M.Part(V, F, "BH_Wood", name="wand"))
    parts.append(_grip(-0.07, 0.04, 0.0105, 5))
    for z in (0.045, 0.1):
        V, F = M.lathe([(0, z - 0.004), (0.0098, z - 0.004), (0.0105, z), (0.0098, z + 0.004), (0, z + 0.004)], 12)
        parts.append(M.Part(V, F, "BH_Gold", name="band"))
    # claw setting holding the gem
    V, F = M.lathe([(0, 0.188), (0.008, 0.19), (0.011, 0.2), (0.0, 0.205)], 12)
    parts.append(M.Part(V, F, "BH_Gold", name="setting"))
    for k in range(4):
        a = math.radians(90 * k + 45)
        claw = [(0.008 * math.cos(a), 0.008 * math.sin(a), 0.198), (0.013 * math.cos(a), 0.013 * math.sin(a), 0.215),
                (0.007 * math.cos(a), 0.007 * math.sin(a), 0.232)]
        V, F = M.tube(claw, [(0.0022, 0.0022), (0.0018, 0.0018), (0.001, 0.001)], n=5, up=(0, 0, 1))
        parts.append(M.Part(V, F, "BH_Gold", name="claw"))
    V, F = M.lathe([(0, 0.2), (0.0105, 0.212), (0.012, 0.222), (0.0085, 0.236), (0.0, 0.25)], 8)
    parts.append(M.Part(V, F, "BH_Emissive", name="gem"))
    V, F = M.lathe([(0, -0.11), (0.011, -0.106), (0.013, -0.097), (0.011, -0.09), (0, -0.088)], 12)
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


# ---------------------------------------------------------------------------------------------------------------
# Aether variants: same silhouette family + glowing BH_Aether channels + a floating crystal element
def _crystal(center, length, radius, sides=6, rot=(0, 0, 0), mat="BH_Aether"):
    V, F = M.lathe([(0, -length / 2), (radius * 0.75, -length * 0.2), (radius, 0.0), (radius * 0.8, length * 0.16),
                    (0, length / 2)], sides)
    return M.Part(V, F, mat, name="crystal").rot(Rx(rot[0]) @ Ry(rot[1]) @ Rz(rot[2])).move(center)


def _flat_channel(z0, z1, w0, w1, t, x=0.0, mat="BH_Aether"):
    """Thin raised strip on both blade flats (+-Y) from z0 to z1 (tapering)."""
    parts = []
    for sy in (1, -1):
        rings = []
        for z in np.linspace(z0, z1, 6):
            u = (z - z0) / (z1 - z0)
            w = (w0 + (w1 - w0) * u) / 2
            rings.append(np.array([(x - w, sy * t * 0.2, z), (x + w, sy * t * 0.2, z), (x + w, sy * (t + 0.0012), z),
                                   (x - w, sy * (t + 0.0012), z)]))
        V, F = M.loft(rings)
        p = M.Part(V, F, mat, name="channel")
        if sy < 0:
            p.flip()
        parts.append(p)
    return parts


def _ring(center, r, tube_r, axis="z", n=24, mat="BH_Aether"):
    pts = []
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        if axis == "z":
            pts.append((center[0] + r * math.cos(a), center[1] + r * math.sin(a), center[2]))
        else:
            pts.append((center[0] + r * math.cos(a), center[1], center[2] + r * math.sin(a)))
    V, F = M.tube(pts, [(tube_r, tube_r)] * len(pts), n=5, up=(0, 0, 1) if axis == "y" else (1, 0, 0),
                  cap0=False, cap1=False)
    return M.Part(V, F, mat, name="ring")


def sword_aether():
    parts = sword()
    for p in parts:
        if p.name == "collar":
            p.mat = "BH_DarkSteel"
    # the fuller holds an aether channel on both flats
    parts += _flat_channel(0.12, 0.70, 0.012, 0.004, 0.0065 * 0.55)
    parts.append(_crystal((0, 0, 0.093), 0.034, 0.016, rot=(90, 0, 0)))          # gem through the guard
    # floating crystals hovering beyond the guard tips
    for sx in (1, -1):
        parts.append(_crystal((sx * 0.148, 0, 0.122), 0.05, 0.011, rot=(0, -sx * 35, 0)))
    return parts


def greatsword_aether():
    parts = greatsword()
    parts += _flat_channel(0.17, 1.12, 0.016, 0.005, 0.0075 * 0.55)
    parts.append(_crystal((0, 0, 0.14), 0.05, 0.02, rot=(90, 0, 0)))
    for sx in (1, -1):   # floating shards beside the parrying lugs
        parts.append(_crystal((sx * 0.1, 0, 0.29), 0.07, 0.014, rot=(0, sx * 18, 0)))
    return parts


def staff_aether():
    parts = [p for p in staff() if p.name != "crystal"]
    # larger free-floating aether crystal inside the prongs, with two orbit rings
    parts.append(_crystal((0, 0, 0.7), 0.2, 0.042, sides=6, rot=(0, 0, 15)))
    parts.append(_ring((0, 0, 0.7), 0.075, 0.003, axis="z", n=28))
    parts.append(_ring((0, 0, 0.7), 0.068, 0.0025, axis="y", n=28).rot(Rz(35), center=(0, 0, 0.7)))
    # spiral channel down the upper shaft
    pts = []
    for i in range(25):
        u = i / 24
        z = 0.48 - 0.5 * u
        a = u * 4 * math.pi
        r = 0.0245
        pts.append((r * math.cos(a) + 0.012 * math.sin(((z + 1.05) / 1.62) * 9.0),
                    r * math.sin(a) + 0.01 * math.cos(((z + 1.05) / 1.62) * 7.0), z))
    V, F = M.tube(pts, [(0.003, 0.003)] * len(pts), n=5, up=(0, 0, 1))
    parts.append(M.Part(V, F, "BH_Aether", name="spiral"))
    return parts


def wand_aether():
    parts = [p for p in wand() if p.name != "gem"]
    parts.append(_crystal((0, 0, 0.243), 0.042, 0.011, sides=5))
    parts.append(_ring((0, 0, 0.24), 0.019, 0.0018, axis="z", n=20))
    pts = []
    for i in range(17):
        u = i / 16
        z = 0.18 - 0.2 * u
        a = u * 3 * math.pi
        r = 0.0092 - 0.0015 * (1 - u)
        pts.append((r * math.cos(a), r * math.sin(a), z))
    V, F = M.tube(pts, [(0.0018, 0.0018)] * len(pts), n=4, up=(0, 0, 1))
    parts.append(M.Part(V, F, "BH_Aether", name="spiral"))
    return parts


WEAPONS = {
    "sword": sword, "greatsword": greatsword, "axe": axe, "spear": spear, "dagger": dagger, "bow": bow,
    "staff": staff, "wand": wand, "shield": shield, "arrow": arrow,
    "sword_aether": sword_aether, "greatsword_aether": greatsword_aether, "staff_aether": staff_aether,
    "wand_aether": wand_aether,
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
