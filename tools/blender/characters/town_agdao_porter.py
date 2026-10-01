"""Townsfolk (bh-029, Zarael): Agdao's porters, lift engineers and scouts (Toma Kettridge, Quillan Ashby).

A sturdy working man: a sleeveless quilted vest (BH_Cloth_Primary, tinted per NPC) open over a bare chest, with a
brick-red stepped-fret hem; cream trousers wrapped from ankle to knee with red cloth strips; sandals; a wide leather
tool belt with a hammer, an open-jawed wrench and pouches; a coil of copper wire slung over the left shoulder; a woven
carrying frame on the back (two poles rising above the head, a wicker panel, shoulder straps); a red headband over
short dark hair; leather wrist wraps, one with a thin white-glowing wire bracelet.
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import front_y, back_y, interp_rows, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import town_matron as K
from town_matron import Kit, P_, pal, rope, lerp
from char_mage import ring_frac
import town_terax as Z

PROPS = proportions(0.99, shoulder_x=0.2 * 0.99, hip_x=0.103 * 0.99)
PALETTE = "town_agdao_porter"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.42, 0.30, 0.18)),              # preview: quilted vest (game tint per NPC)
    "BH_Cloth_Secondary": pal((0.60, 0.53, 0.40), 0.92),      # cream trousers
    "BH_Cloth_Accent": pal((0.40, 0.08, 0.05), 0.88),         # brick-red wraps, headband, fret hem
    "BH_Wicker": pal((0.42, 0.30, 0.15), 0.9),                # woven panel of the carrying frame
    "BH_Skin": pal((0.34, 0.20, 0.12), 0.55),
    "BH_Hair": pal((0.03, 0.022, 0.018), 0.6),
    "BH_Leather": pal((0.15, 0.085, 0.045), 0.65),
    "BH_Wood": pal((0.22, 0.14, 0.07), 0.75),
    "BH_Gold": pal((0.72, 0.42, 0.18), 0.35, 1.0),            # copper wire coil
    "BH_DarkSteel": pal((0.12, 0.12, 0.13), 0.5, 1.0),        # hammer head, wrench
    "BH_Emissive": Z.WHITE_GLOW,                              # one thin wire bracelet
})

P_TORSO = K.torso_rows(chest=1.1, waist=1.05, hip=1.03, depth=1.06, belly=0.01, shoulder=1.08)
VEST_G = 0.014


def build(body):
    k = Kit(body)
    rows = P_TORSO
    # ---- bare torso, open quilted vest
    K.body_shell(k, rows, 0.96, 1.53, "BH_Skin", n=24, cap1=True, name="torso")
    vest(k, rows)
    # ---- trousers, wraps, sandals
    K.trousers(k, "BH_Cloth_Secondary", knee_r=0.056, ankle_r=0.046, t_end=1.82)
    for s in "LR":
        Z.wrap_spiral(k, "shin." + s, "foot." + s, 0.04, 0.8, 0.064, 7.0, "BH_Cloth_Accent", w=0.022, th=0.005)
    K.bare_foot(k, sandal="BH_Leather")
    # ---- arms: bare, muscular; leather wrist wraps
    for s in "LR":
        K.sleeve(k, s, [(-0.2, 0.03, 0.034), (-0.13, 0.054, 0.057), (-0.05, 0.064, 0.066), (0.05, 0.066, 0.068),
                        (0.4, 0.062, 0.064), (0.75, 0.054, 0.054), (1.0, 0.048, 0.048), (1.3, 0.052, 0.048),
                        (1.65, 0.042, 0.038), (1.85, 0.036, 0.032)], "BH_Skin", n=12, name="arm")
        K.arm_ring(k, s, 1.8, 0.04, 0.09, "BH_Leather", name="wrist_wrap")
        K.mitten(k, s, size=1.06)
    K.arm_ring(k, "L", 1.66, 0.043, 0.014, "BH_Emissive", name="wire_glow")
    # ---- belt with tools
    tool_belt(k, rows)
    # ---- carrying frame, wire coil
    frame(k, rows)
    wire_coil(k, rows)
    # ---- head: headband, short hair
    hr = K.head(k, jaw=1.04, width=1.0, nose=1.04, brow=1.15, neck_r=0.056)
    hair(k, hr)
    K.check_normals(body, "agdao_porter")


def vest(k, rows):
    zs = [0.97, 1.05, 1.13, 1.21, 1.29, 1.37, 1.43, 1.48, 1.52]
    nu = 28
    rings = []
    for z in zs:
        t = (z - 0.97) / 0.55
        a0 = 0.012 + 0.07 * t ** 3
        fr = a0 + (1 - 2 * a0) * np.linspace(0, 1, nu)
        rings.append(ring_frac(rows, z, VEST_G, fr))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Primary", "vest"), 0.012, offset=1.0), w=k.torso_w())
    # quilt ridges
    for z in (1.08, 1.17, 1.26, 1.35):
        i = int(np.argmin([abs(zz - z) for zz in zs]))
        t = (z - 0.97) / 0.55
        a0 = 0.012 + 0.07 * t ** 3 + 0.01
        fr = a0 + (1 - 2 * a0) * np.linspace(0, 1, nu)
        pts = ring_frac(rows, z, VEST_G + 0.012, fr)
        V, F = M.tube(pts, [(0.006, 0.007)] * len(pts), n=4, up=(0, 0, 1), cap0=False, cap1=False)
        k.add(P_(V, F, "BH_Cloth_Primary", "quilt"), w=k.torso_w())
    # edges and the fret hem
    for kk in (0, -1):
        edge = np.array([r[kk] for r in rings]) + np.array([0, -0.004, 0])
        V, F = M.tube(edge, [(0.011, 0.007)] * len(edge), n=5, up=(0, -1, 0))
        k.add(P_(V, F, "BH_Cloth_Accent", "vest_edge"), w=k.torso_w())
    Z.fret_band(k, rows, 0.985, VEST_G + 0.004, h=0.032, n=18, w=k.torso_w(), fr=(0.02, 0.98))
    # front lacing across the narrow opening
    for z in (1.12, 1.2, 1.28, 1.36):
        y = front_y(rows, 0, z) - VEST_G - 0.012
        for sx in (1, -1):
            k.add(rope([(sx * 0.03, y + 0.002, z + 0.025), (-sx * 0.03, y, z - 0.025)], 0.0045, "BH_Leather", n=4),
                  w=k.torso_w())


def tool_belt(k, rows):
    K.band(k, rows, 0.97, 1.05, "BH_Leather", g_out=0.03, g_in=0.012, n=26, bev=0.0)
    by = front_y(rows, 0, 1.01) - 0.034
    V, F = M.box(0.06, 0.012, 0.05, center=(0, by, 1.01))
    k.add(M.bevel(P_(V, F, "BH_Gold", "buckle"), 0.005, 1), "hips")
    # hammer through a loop on the right hip
    q, ang = K.on_ring(rows, 1.0, 0.045, 0.78)
    q = np.asarray(q)
    ring = K.ring_pts(q, 0.022, (0, 0, 1), n=10)
    V, F = M.tube(ring, [(0.005, 0.009)] * len(ring), n=4, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Leather", "loop"), "hips")
    V, F = M.tube([q + (0, 0, 0.04), q + (0, 0, -0.2)], [(0.012, 0.012), (0.014, 0.014)], n=8, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Wood", "handle"), "hips")
    V, F = M.box(0.11, 0.038, 0.04)
    k.add(M.bevel(P_(V, F, "BH_DarkSteel", "hammer"), 0.005, 1).rot(Rz(ang)).move(q + (0, 0, 0.062)), "hips")
    # open-jawed wrench hanging at the left hip
    q, ang = K.on_ring(rows, 0.99, 0.045, 0.24)
    q = np.asarray(q)
    R = Rz(ang)
    V, F = M.box(0.022, 0.01, 0.2, center=(0, 0, -0.08))
    k.add(P_(V, F, "BH_DarkSteel", "wrench").rot(R).move(q), "hips")
    jaw = []
    for a in np.linspace(math.radians(40), math.radians(320), 9):
        jaw.append((0.032 * math.sin(a), 0.0, -0.2 - 0.032 + 0.032 * math.cos(a) - 0.02))
    V, F = M.tube(jaw, [(0.01, 0.005)] * len(jaw), n=4, up=(0, -1, 0))
    k.add(P_(V, F, "BH_DarkSteel", "wrench_jaw").rot(R).move(q + (0, 0, 0.03)), "hips")
    # pouches at the back
    for f in (0.42, 0.58):
        q, ang = K.on_ring(rows, 0.98, 0.04, f)
        for prt in K.pouch(q, ang, (0.08, 0.04, 0.08)):
            k.add(prt, "hips")


def frame(k, rows):
    """Carrying frame on the back (rigid to the chest): two poles rising above the head, crossbars, a woven panel
    and shoulder straps."""
    yb = back_y(rows, 0, 1.3) + 0.05
    for sx in (1, -1):
        a = np.array([sx * 0.13, yb + 0.03, 0.86])
        b = np.array([sx * 0.15, yb + 0.06, 1.98])
        V, F = M.tube([a, b], [(0.017, 0.017)] * 2, n=8, up=(0, -1, 0))
        k.add(P_(V, F, "BH_Wood", "pole"), "chest")
        V, F = M.sphere(0.022, 8, 5, center=b + (0, 0, 0.01))
        k.add(P_(V, F, "BH_Wood", "pole_cap"), "chest")
    for z in (0.92,):
        t = (z - 0.86) / 1.12
        y = yb + 0.03 + 0.03 * t
        x = 0.13 + 0.02 * t
        V, F = M.tube([(-x, y, z), (x, y, z)], [(0.013, 0.013)] * 2, n=8, up=(0, 0, 1))
        k.add(P_(V, F, "BH_Wood", "bar"), "chest")
    # tall woven pack (wicker) riding the frame up behind the head, with weave ridges and a red band
    c = np.array([0.0, yb + 0.1, 1.36])
    V, F = M.box(0.28, 0.14, 0.82)
    k.add(M.bevel(P_(V, F, "BH_Wicker", "wicker"), 0.03, 2).move(c), "chest")
    for z in np.linspace(-0.36, 0.36, 10):
        V, F = M.tube([c + (-0.14, 0.074, z), c + (0.14, 0.074, z)], [(0.007, 0.007)] * 2, n=5, up=(0, 0, 1))
        k.add(P_(V, F, "BH_Wicker", "weave"), "chest")
    for z in (0.25, -0.2):
        V, F = M.box(0.292, 0.152, 0.035, center=c + (0, 0.0, z))
        k.add(P_(V, F, "BH_Cloth_Accent", "pack_band"), "chest")
    # a rolled cloth bundle lashed on top
    V, F = M.tube([c + (-0.16, 0.0, 0.46), c + (0.16, 0.0, 0.46)], [(0.055, 0.055)] * 2, n=10, up=(0, 0, 1))
    k.add(K.outward(P_(V, F, "BH_Cloth_Secondary", "bundle")), "chest")
    # shoulder straps from the frame over the shoulders down the chest
    for sx in (1, -1):
        pts = [(sx * 0.1, yb, 1.55), (sx * 0.1, 0.08, 1.565), (sx * 0.115, -0.05, 1.55),
               (sx * 0.12, front_y(rows, 0.12, 1.42) - 0.03, 1.42), (sx * 0.125, front_y(rows, 0.125, 1.3) - 0.03, 1.3),
               (sx * 0.13, yb - 0.03, 1.0)]
        V, F = M.tube(pts, [(0.018, 0.005)] * len(pts), n=5, up=(0, 0, 1), p=3.0)
        k.add(P_(V, F, "BH_Leather", "strap"), w=k.torso_w())


def wire_coil(k, rows):
    """A coil of copper wire slung from the left shoulder to the right hip (three loose turns)."""
    for i in range(3):
        pts = []
        for a in np.linspace(0, 2 * math.pi, 29)[:-1]:
            # ellipse round the torso, tilted: high on the left shoulder, low on the right hip; cos(a) > 0 in front
            sa, ca = math.sin(a), math.cos(a)
            x = 0.175 * sa + 0.008 * i
            z = 1.25 + 0.22 * sa + 0.05 * max(0.0, sa) ** 4 + 0.01 * i
            zc = min(max(z, 1.0), 1.47)
            xc = min(abs(x), 0.14) * 0.9
            yf = front_y(rows, xc, zc) - 0.03 - 0.007 * i
            yb = back_y(rows, xc, zc) + 0.03 + 0.006 * i        # between the back and the pack
            y = yb + (yf - yb) * (1 + ca) / 2
            pts.append((x, y, z))
        pts.append(pts[0])
        V, F = M.tube(pts, [(0.0085, 0.0085)] * len(pts), n=5, up=(0, 0, 1), cap0=False, cap1=False)
        k.add(P_(V, F, "BH_Gold", "coil"), w=k.torso_w())


def hair(k, hr):
    line = K.hairline(1.755, 1.68, 1.625, sharp=0.8)
    V, F = K.head_shell(hr, lambda v: 0.008 + 0.006 * (1 - v), line, nu=22, nv=5, top_bulge=0.012)
    k.add(M.solidify(P_(V, F, "BH_Hair", "hair"), 0.008, offset=-1.0), "head")
    # red headband round the brow with a knot and two tails at the back
    us = np.linspace(0, 1, 25)
    ring = []
    for u in us:
        z = lerp(1.755, 1.72, (1 - math.cos(2 * math.pi * u)) / 2)
        q = K.ring_frac(hr, z, 0.016, [u], p=2.1)[0]
        ring.append((q[0], q[1], z))
    V, F = M.tube(ring, [(0.006, 0.014)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Cloth_Accent", "headband"), "head")
    yb = K.back_y(hr, 0, 1.72) + 0.02
    V, F = M.sphere(0.02, 8, 5, center=(0, yb, 1.72), scale=(1.2, 0.8, 0.9))
    k.add(P_(V, F, "BH_Cloth_Accent", "knot"), "head")
    for sx in (1, -1):
        pts = [(sx * 0.01, yb + 0.005, 1.715), (sx * 0.03, yb + 0.03, 1.65), (sx * 0.04, yb + 0.04, 1.6)]
        V, F = M.tube(pts, [(0.014, 0.004), (0.016, 0.004), (0.014, 0.004)], n=5, up=(0, 1, 0), p=3.0)
        k.add(P_(V, F, "BH_Cloth_Accent", "tail"), w=k.zw([(1.56, "neck"), (1.62, "head")]))
