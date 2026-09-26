"""Townsfolk: the guild officer (Commander Rhea Talvanne, retired hero Venna Kail).

A woman in a long officer's coat (BH_Cloth_Primary, tinted: Swordfin sea-blue for Rhea) open over a light steel
breastplate, a sash across the chest, a short cape over the shoulders, leather gloves, tall boots, hair tied back in
a knot, and a sheathed sword at the left hip (scabbard rigid to `hips`, hilt forward).
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
from char_mage import ring_frac

PROPS = proportions(0.97, shoulder_x=0.182 * 0.97, hip_x=0.1 * 0.97)
PALETTE = "town_officer"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.03, 0.08, 0.20)),              # preview: Swordfin sea-blue coat
    "BH_Cloth_Secondary": pal((0.05, 0.05, 0.06), 0.88),      # cape, cuffs
    "BH_Cloth_Accent": pal((0.50, 0.52, 0.55), 0.6),          # silver-grey sash
    "BH_Cloth_Dark": pal((0.08, 0.07, 0.065), 0.9),           # breeches
    "BH_Steel": pal((0.55, 0.56, 0.58), 0.32, 1.0),
    "BH_Gold": pal((0.70, 0.52, 0.22), 0.35, 1.0),
    "BH_Leather": pal((0.09, 0.05, 0.03), 0.6),
    "BH_Skin": pal((0.55, 0.36, 0.25), 0.55),
    "BH_Hair": pal((0.10, 0.05, 0.03), 0.6),
    "BH_Wood": pal((0.08, 0.05, 0.03), 0.7),
})

O_TORSO = K.torso_rows(chest=0.97, waist=0.92, hip=1.03, depth=1.0, bust=0.012, shoulder=0.97)
COAT_G = 0.016


def build(body):
    k = Kit(body)
    rows = O_TORSO
    # ---- breastplate (visible in the coat opening) over a dark doublet
    K.body_shell(k, rows, 0.98, 1.53, "BH_Cloth_Dark", n=24, cap1=True, name="doublet")
    V, F = K.torso_loft(K.grow(K.rows_span(rows, 1.13, 1.49), 0.007), n=26, cap1=False)
    k.add(P_(V, F, "BH_Steel", "breastplate"), w=k.zw([(1.22, "spine"), (1.3, "chest")]))
    K.band(k, rows, 1.12, 1.135, "BH_Gold", g_out=0.012, g_in=0.004, n=26, w=k.zw([(1.22, "spine"), (1.3, "chest")]),
           bev=0.0)
    # ---- coat
    coat(k, rows)
    # ---- belt + sword
    K.band(k, rows, 1.03, 1.07, "BH_Leather", g_out=COAT_G + 0.016, g_in=COAT_G, n=26)
    by = front_y(rows, 0, 1.05) - COAT_G - 0.02
    V, F = M.box(0.05, 0.012, 0.045, center=(0, by, 1.05))
    k.add(M.bevel(P_(V, F, "BH_Gold", "buckle"), 0.004, 1), "hips")
    sword(k, rows)
    # ---- sash across the chest (right shoulder -> left hip) with a knot at the hip
    sash(k, rows)
    # ---- short cape
    rings = shawl_surface(32, 6, math.radians(28), (0.10, 0.085, 0.095), (0.28, 0.19, 0.2), 0.12, 0.2, 0.3, 1.58)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Secondary", "cape"), 0.01, offset=1.0), w=shawl_w(k))
    V, F = M.tube(rings[0], [(0.007, 0.007)] * len(rings[0]), n=6, up=(0, 0, 1))
    k.add(P_(V, F, "BH_Gold", "cape_trim"), w=shawl_w(k))
    for sx in (1, -1):
        V, F = M.lathe([(0, -0.005), (0.016, -0.004), (0.018, 0.003), (0, 0.006)], 10)
        k.add(P_(V, F, "BH_Gold", "clasp").rot(Rx(90)).move((sx * 0.07, -0.105, 1.49)), "chest")
    # ---- legs: breeches + tall boots
    K.trousers(k, "BH_Cloth_Dark", knee_r=0.05, ankle_r=0.042, t_end=1.6, n=10)
    K.shoes(k, "BH_Leather", sole="BH_Wood", shaft=0.36, shaft_r=0.05, width=0.96)
    for s in "LR":
        b = k.b
        kn, a = b.head("shin." + s), b.tail("shin." + s)
        c = kn + (a - kn) * 0.12
        V, F = M.tube([c - (0, 0, 0.03), c + (0, 0, 0.02)], [(0.058, 0.064), (0.062, 0.068)], n=12, up=(0, -1, 0),
                      cap0=False, cap1=False)
        b.add(M.solidify(P_(V, F, "BH_Leather", "boot_cuff"), 0.006, offset=-1.0), "shin." + s)
    # ---- head
    hr = K.head(k, jaw=0.95, width=0.97, nose=1.0, brow=0.9)
    hair(k, hr)
    K.check_normals(body, "officer")


def coat(k, rows):
    zs = [0.98, 1.06, 1.14, 1.22, 1.30, 1.37, 1.43, 1.475, 1.51, 1.535]
    nu = 26
    rings = []
    for z in zs:
        t = (z - 0.98) / 0.555
        a0 = 0.06 + 0.07 * t ** 1.2
        fr = a0 + (1 - 2 * a0) * np.linspace(0, 1, nu)
        rings.append(ring_frac(rows, z, COAT_G, fr))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Primary", "coat"), 0.008, offset=1.0), w=k.torso_w())
    # standing collar
    top = rings[-1]
    V, F = M.tube(top, [(0.012, 0.02)] * len(top), n=6, up=(0, 0, 1), cap0=True, cap1=True)
    k.add(P_(V, F, "BH_Cloth_Primary", "collar"), "chest")
    # lapel trims
    for kk in (0, -1):
        pts = np.array([r[kk] for r in rings]) + np.array([0, -0.006, 0])
        V, F = M.tube(pts, [(0.012, 0.005)] * len(pts), n=6, up=(0, -1, 0), p=3.0)
        k.add(P_(V, F, "BH_Gold", "lapel"), w=k.torso_w())
    # coat skirt: split at the front and with a back vent, to below the knee
    r0 = interp_rows(rows, 1.0)
    g = COAT_G
    sk_rows = K.flare_rows(1.0, 0.42, (r0[1] + g, r0[2] + g, r0[3] + g), (0.25, 0.21, 0.24), n=6)
    for side, lo, hi in (("L", 0.07, 0.49), ("R", 0.51, 0.93)):
        fr = np.linspace(lo, hi, 12)
        rr = []
        for r in sorted(sk_rows, key=lambda r: r[0]):
            pts = ring_frac(sk_rows, r[0], 0.0, fr, p=2.2)
            t = (1.0 - r[0]) / 0.58
            fold = 0.01 * t * np.sin(fr * 2 * math.pi * 7)
            rad = K.normalize_rows(pts[:, :2])
            pts[:, 0] += rad[:, 0] * fold
            pts[:, 1] += rad[:, 1] * fold
            rr.append(pts)
        V, F = M.loft(rr, cap0=False, cap1=False, closed=False)
        sk = M.solidify(P_(V, F, "BH_Cloth_Primary", "coat_skirt"), 0.008, offset=-1.0)
        k.add(sk, w=k.skirt_w(1.0, 0.55, max_leg=0.85))
        hem = rr[0] + np.array([0, 0, 0.01])
        V, F = M.tube(hem, [(0.006, 0.009)] * len(hem), n=6, up=(0, 0, 1), p=3.0)
        k.add(P_(V, F, "BH_Gold", "hem"), w=k.skirt_w(1.0, 0.55, max_leg=0.85))
    # sleeves with turned-back cuffs, gloves
    for s in "LR":
        K.sleeve(k, s, K.SHOULDER_CAP + [(0.5, 0.054, 0.056), (1.0, 0.05, 0.052), (1.6, 0.045, 0.046),
                                         (1.82, 0.046, 0.046)], "BH_Cloth_Primary", n=12)
        K.arm_ring(k, s, 1.72, 0.056, 0.09, "BH_Cloth_Secondary", name="cuff")
        K.mitten(k, s, mat="BH_Leather", size=1.02)
        K.arm_ring(k, s, 1.97, 0.04, 0.05, "BH_Leather", name="glove_cuff", bone="hand." + s)


def sash(k, rows):
    pts = []
    for t in np.linspace(0, 1, 9):
        x = lerp(-0.13, 0.16, t)
        z = lerp(1.49, 1.04, t)
        y = front_y(rows, x * 0.95, z) - COAT_G - 0.02
        pts.append((x, y, z))
    V, F = M.tube(pts, [(0.03, 0.006)] * len(pts), n=6, up=(0, -1, 0), p=3.0)
    k.add(P_(V, F, "BH_Cloth_Accent", "sash"), w=k.torso_w())
    pts = []
    for t in np.linspace(0, 1, 7):
        x = lerp(-0.13, 0.16, t)
        z = lerp(1.49, 1.04, t)
        pts.append((x, back_y(rows, x * 0.95, z) + COAT_G + 0.02, z))
    V, F = M.tube(pts, [(0.03, 0.006)] * len(pts), n=6, up=(0, 1, 0), p=3.0)
    k.add(P_(V, F, "BH_Cloth_Accent", "sash_b"), w=k.torso_w())
    q, ang = K.on_ring(rows, 1.03, COAT_G + 0.03, 0.25)
    q = np.asarray(q)
    V, F = M.sphere(0.026, 8, 6, center=q, scale=(0.8, 1.0, 1.0))
    k.add(P_(V, F, "BH_Cloth_Accent", "sash_knot"), "hips")
    for dy, L in ((-0.01, 0.2), (0.015, 0.15)):
        V, F = M.tube([q + (0.004, dy, -0.01), q + (0.012, dy, -L)], [(0.006, 0.024), (0.006, 0.028)], n=6,
                      up=(0, -1, 0), p=3.0)
        k.add(P_(V, F, "BH_Cloth_Accent", "sash_tail"), w=k.skirt_w(1.02, 0.75, max_leg=0.4))


def sword(k, rows):
    """Arming sword in its scabbard on the left hip: hilt forward-up, scabbard slanting down and back."""
    g = np.array([0.175, -0.07, 1.0])                     # throat of the scabbard (guard position)
    d = normalize(np.array([0.05, 0.42, -0.9]))            # scabbard direction (down / back)
    side = normalize(np.cross(d, np.array([1.0, 0, 0])))
    L = 0.74
    tip = g + d * L
    V, F = M.tube([g, g + d * 0.4, tip - d * 0.06, tip], [(0.026, 0.012), (0.024, 0.011), (0.02, 0.01), (0.008, 0.006)],
                  n=8, up=(1, 0, 0), p=2.6)
    k.add(P_(V, F, "BH_Leather", "scabbard"), "hips")
    for t, mat in ((0.0, "BH_Gold"), (L - 0.05, "BH_Gold"), (0.18, "BH_Steel")):
        c = g + d * t
        V, F = M.tube([c - d * 0.012, c + d * 0.012], [(0.029, 0.015)] * 2, n=8, up=(1, 0, 0), p=2.6)
        k.add(P_(V, F, mat, "fitting"), "hips")
    # hilt: crossguard, grip, pommel
    V, F = M.tube([g - np.array([0.0, 0.0, 0.0]) + side * 0.1, g - side * 0.1], [(0.009, 0.009)] * 2, n=6, up=d)
    k.add(P_(V, F, "BH_Gold", "guard"), "hips")
    V, F = M.tube([g - d * 0.01, g - d * 0.13], [(0.014, 0.014), (0.013, 0.013)], n=8, up=(1, 0, 0))
    k.add(P_(V, F, "BH_Leather", "grip"), "hips")
    V, F = M.sphere(0.022, 8, 6, center=g - d * 0.15)
    k.add(P_(V, F, "BH_Gold", "pommel"), "hips")
    # hanger straps from the belt
    q = np.array([0.16, -0.03, 1.04])
    k.add(rope([q, g + d * 0.05 + np.array([0.02, 0, 0])], 0.006, "BH_Leather"), "hips")
    q2 = np.array([0.17, 0.08, 1.04])
    k.add(rope([q2, g + d * 0.2 + np.array([0.02, 0, 0])], 0.006, "BH_Leather"), "hips")


def hair(k, hr):
    line = K.hairline(1.765, 1.69, 1.625, sharp=0.8)
    V, F = K.head_shell(hr, lambda v: 0.01 + 0.004 * (1 - v), line, nu=24, nv=6, top_bulge=0.008)
    k.add(M.solidify(P_(V, F, "BH_Hair", "hair"), 0.008, offset=-1.0), "head")
    # knot at the back of the head + short tail
    yb = back_y(hr, 0, 1.70) + 0.02
    V, F = M.sphere(0.042, 10, 6, center=(0, yb, 1.69), scale=(1.0, 0.85, 0.9))
    k.add(K.outward(P_(V, F, "BH_Hair", "knot")), "head")
    ring = K.ring_pts((0, yb + 0.03, 1.678), 0.02, (0, 0.5, -1), n=10)
    V, F = M.tube(ring, [(0.005, 0.005)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Gold", "hair_ring"), "head")
