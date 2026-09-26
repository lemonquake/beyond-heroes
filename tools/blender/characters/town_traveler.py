"""Townsfolk: the traveler (Zerin Ven, a refugee from Emberhal).

A road-worn woman in a long hooded travel cloak (BH_Cloth_Primary, tinted) with the hood up and a shoulder mantle,
a scarf wound around the neck, a belted tunic over trousers, cloth-wrapped boots, and a pack with a rolled bedroll
strapped on the back.
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import front_y, back_y, interp_rows, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import town_matron as K
from town_matron import Kit, P_, pal, rope, lerp
from town_elder import shawl_surface, shawl_w
from char_mage import ring_frac, HOOD

PROPS = proportions(0.95, shoulder_x=0.172 * 0.95, hip_x=0.097 * 0.95)
PALETTE = "town_traveler"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.16, 0.14, 0.10)),              # preview: dusty road-brown cloak
    "BH_Cloth_Secondary": pal((0.30, 0.25, 0.18), 0.92),      # tunic
    "BH_Cloth_Accent": pal((0.22, 0.10, 0.05), 0.88),         # rust scarf, boot wraps
    "BH_Cloth_Dark": pal((0.08, 0.075, 0.07), 0.9),           # trousers
    "BH_Skin": pal((0.44, 0.27, 0.17), 0.55),
    "BH_Hair": pal((0.04, 0.03, 0.025), 0.6),
    "BH_Bone": pal((0.46, 0.42, 0.33), 0.9),                  # bedroll blanket
    "BH_Shadow": pal((0.02, 0.016, 0.014), 0.9),
})

T_TORSO = K.torso_rows(chest=0.92, waist=0.9, hip=1.04, depth=0.98, bust=0.012, shoulder=0.94)


def build(body):
    k = Kit(body)
    rows = T_TORSO
    # ---- tunic (to mid-thigh) + belt, trousers, wrapped boots
    K.body_shell(k, rows, 0.98, 1.53, "BH_Cloth_Secondary", n=22, cap1=True, name="tunic")
    r0 = interp_rows(rows, 1.0)
    sk_rows = K.flare_rows(1.02, 0.72, (r0[1] + 0.004, r0[2] + 0.004, r0[3] + 0.004), (0.19, 0.15, 0.16), n=4)
    sk, _ = K.skirt(sk_rows, "BH_Cloth_Secondary", folds=6, amp=0.008, n=24)
    k.add(sk, w=k.skirt_w(1.0, 0.7, max_leg=0.75))
    K.band(k, rows, 1.02, 1.05, "BH_Leather", g_out=0.014, g_in=0.004, n=22)
    q, ang = K.on_ring(rows, 1.0, 0.03, 0.8)
    for prt in K.pouch(q, ang, (0.07, 0.035, 0.07)):
        k.add(prt, "hips")
    K.trousers(k, "BH_Cloth_Dark", knee_r=0.05, ankle_r=0.044, t_end=1.6, n=10, seat=False)
    K.shoes(k, "BH_Leather", sole="BH_Wood", shaft=0.18, shaft_r=0.047, width=0.95)
    wraps(k)
    # ---- arms: tunic sleeves, fingerless-glove wraps
    for s in "LR":
        K.sleeve(k, s, K.SHOULDER_CAP + [(0.5, 0.05, 0.052), (1.0, 0.046, 0.048), (1.6, 0.04, 0.041),
                                         (1.9, 0.037, 0.037)], "BH_Cloth_Secondary", n=12)
        K.arm_ring(k, s, 1.82, 0.041, 0.1, "BH_Cloth_Accent", name="wrist_wrap")
        K.mitten(k, s)
    # ---- cloak: mantle + long back panel + hood up
    cloak(k, rows)
    scarf(k, rows)
    pack(k, rows)
    hr = K.head(k, jaw=0.94, width=0.95, nose=1.0, brow=0.9)
    hood(k, hr)
    K.check_normals(body, "traveler")


def wraps(k):
    """Cloth strips wound around the boot shafts / shins."""
    b = k.b
    for s in "LR":
        sh = "shin." + s
        kn, a = b.head(sh), b.tail(sh)
        pts, n = [], 40
        for i in range(n + 1):
            t = i / n
            c = a + (kn - a) * lerp(0.1, 0.62, t)
            ang = t * 2 * math.pi * 5.0
            r = 0.053 * k.s
            pts.append(c + np.array([r * math.cos(ang), r * math.sin(ang), 0.0]))
        V, F = M.tube(pts, [(0.004 * k.s, 0.012 * k.s)] * len(pts), n=4, up=(0, 0, 1), p=3.0)
        b.add(P_(V, F, "BH_Cloth_Accent", "wrap"), sh)


def cloak_w(k):
    def wfn(V):
        top = shawl_w(k)(V)
        low = k.skirt_w(1.0, 0.5, max_leg=0.45, center_w=0.2)(V)
        out = []
        for v, a, b in zip(V, top, low):
            t = float(smoothstep(1.3 * k.s, 1.0 * k.s, v[2]))
            m = float(smoothstep(1.3 * k.s, 1.18 * k.s, v[2])) * (1 - t)
            d = {}
            for kk, x in a.items():
                d[kk] = d.get(kk, 0) + x * (1 - t - m)
            if m > 0:
                d["spine"] = d.get("spine", 0) + m
            for kk, x in b.items():
                d[kk] = d.get(kk, 0) + x * t
            out.append({kk: x for kk, x in d.items() if x > 1e-4})
        return out
    return wfn


def cloak(k, rows):
    # long back panel hanging from the shoulders, open in front of the arms
    nu, nv = 17, 11

    def fn(u, v):
        z = lerp(1.47, 0.34, v)
        # angular span: from the character's right-front shoulder around the back to the left-front
        half = lerp(0.2, 0.33, v)
        x = (u - 0.5) * 2 * half
        yb = back_y(rows, min(abs(x), 0.14) * 0.9, min(max(z, 1.15), 1.47)) + 0.03
        y = yb + 0.08 * v ** 1.1
        # edges wrap forward around the arms (more at the shoulders)
        e = abs(u - 0.5) * 2
        y -= (0.13 * (1 - v) + 0.06) * e ** 2.2
        y += 0.012 * math.sin(u * math.pi * 7) * v
        return (x, y, z)
    V, F = M.grid(fn, nu, nv)
    cp = M.solidify(P_(V, F, "BH_Cloth_Primary", "cloak").flip(), 0.01, offset=-1.0)
    k.add(cp, w=cloak_w(k))
    # ragged hem: small triangular tatters
    for i in range(nu - 1):
        if i % 2:
            continue
        a = np.array(fn(i / (nu - 1), 1.0))
        b2 = np.array(fn((i + 1) / (nu - 1), 1.0))
        tip = (a + b2) / 2 + np.array([0, 0.01, -0.05])
        V = np.array([a, b2, tip])
        prt = M.solidify(P_(V, [(0, 1, 2)], "BH_Cloth_Primary", "tatter"), 0.008, offset=0.0)
        k.add(prt, w=cloak_w(k))
    # shoulder mantle over the top of the cloak
    rings = shawl_surface(34, 6, math.radians(18), (0.10, 0.085, 0.09), (0.29, 0.2, 0.22), 0.2, 0.21, 0.24, 1.58)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Primary", "mantle"), 0.01, offset=1.0), w=shawl_w(k))
    # cloak pin at the throat
    V, F = M.lathe([(0, -0.006), (0.02, -0.005), (0.022, 0.003), (0, 0.006)], 10)
    k.add(P_(V, F, "BH_Leather", "pin").rot(Rx(90)).move((0.05, -0.105, 1.49)), "chest")


def scarf(k, rows):
    ring = []
    for a in np.linspace(0, 2 * math.pi, 19):
        ring.append((0.07 * math.sin(a), -0.006 - 0.066 * math.cos(a), 1.54 + 0.01 * math.cos(a)))
    V, F = M.tube(ring, [(0.03, 0.024)] * len(ring), n=8, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Cloth_Accent", "scarf"), w=k.zw([(1.5, "chest"), (1.57, "neck")]))
    pts = [(-0.03, -0.1, 1.51), (-0.05, -0.13, 1.44), (-0.055, -0.14, 1.36), (-0.05, -0.14, 1.29)]
    V, F = M.tube(pts, [(0.032, 0.006), (0.034, 0.006), (0.034, 0.006), (0.03, 0.005)], n=6, up=(0, -1, 0), p=3.0)
    k.add(P_(V, F, "BH_Cloth_Accent", "scarf_end"), w=k.torso_w())


def pack(k, rows):
    yb = back_y(rows, 0, 1.3) + 0.06          # over the cloak
    c = np.array([0.0, yb + 0.07, 1.26])
    V, F = M.box(0.26, 0.14, 0.3)
    k.add(M.bevel(P_(V, F, "BH_Leather", "pack"), 0.035, 2).move(c), "chest")
    V, F = M.box(0.265, 0.15, 0.1, center=(0, -0.002, 0.12))
    k.add(M.bevel(P_(V, F, "BH_Leather", "pack_flap"), 0.02, 1).move(c), "chest")
    for dx in (-0.07, 0.07):
        V, F = M.box(0.025, 0.155, 0.2, center=(dx, 0.0, 0.03))
        k.add(P_(V, F, "BH_Cloth_Dark", "pack_strap").move(c), "chest")
    # bedroll strapped under the pack
    bc = c + np.array([0.0, 0.0, -0.21])
    V, F = M.tube([bc + (-0.2, 0, 0), bc + (0.2, 0, 0)], [(0.065, 0.065)] * 2, n=12, up=(0, 0, 1))
    k.add(K.outward(P_(V, F, "BH_Bone", "bedroll")), "chest")
    for dx in (-0.12, 0.12):
        V, F = M.tube([bc + (dx - 0.012, 0, 0), bc + (dx + 0.012, 0, 0)], [(0.07, 0.07)] * 2, n=12, up=(0, 0, 1))
        k.add(P_(V, F, "BH_Leather", "roll_strap"), "chest")
    # shoulder straps over the mantle down to the front
    for sx in (1, -1):
        pts = [c + (sx * 0.08, -0.07, 0.12), (sx * 0.1, 0.1, 1.575), (sx * 0.12, -0.06, 1.57),
               (sx * 0.12, front_y(rows, 0.12, 1.45) - 0.07, 1.45), (sx * 0.13, front_y(rows, 0.13, 1.33) - 0.045, 1.33)]
        k.add(rope(pts, 0.011, "BH_Leather"), "chest")


def hood(k, hr):
    nu = 20
    rings = []
    for (z, rx, ryf, ryb, cy, th) in HOOD:
        ring = []
        for u in np.linspace(0, 1, nu):
            a = math.radians(th + (360 - 2 * th) * u)
            sa, ca = math.sin(a), math.cos(a)
            ring.append((rx * sa * 1.04, cy - (ryf if ca > 0 else ryb * 1.05) * ca, z - 0.004))
        rings.append(np.array(ring))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    w = k.zw([(1.49, "chest"), (1.54, "neck"), (1.57, "neck"), (1.62, "head")])
    k.add(M.solidify(P_(V, F, "BH_Cloth_Primary", "hood"), 0.011, offset=-1.0), w=w)
    # shadowed inside of the opening
    inner = []
    for (z, rx, ryf, ryb, cy, th) in HOOD[1:6]:
        ring = []
        for u in np.linspace(0, 1, nu):
            a = math.radians(th + (360 - 2 * th) * u)
            ring.append((rx * 0.92 * math.sin(a), cy - (ryf if math.cos(a) > 0 else ryb) * 0.92 * math.cos(a), z))
        inner.append(np.array(ring))
    V, F = M.loft(inner, cap0=False, cap1=False, closed=False)
    k.add(P_(V, F, "BH_Shadow", "hood_lining").flip(), w=w)
    # dark hair framing the face
    line = K.hairline(1.75, 1.68, 1.62)
    V, F = K.head_shell(hr, 0.006, line, nu=20, nv=4)
    k.add(P_(V, F, "BH_Hair", "hair"), "head")
