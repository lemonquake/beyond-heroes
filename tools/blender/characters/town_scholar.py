"""Townsfolk: the scholar (Archivist Oren Vale, Keeper Tomas Dalisay, cartographer Ibarra Quell).

A robed man: ankle-length robe with wide sleeves (BH_Cloth_Primary, tinted), a short shoulder cape with a hood
gathered at the back, round spectacles, a neat trimmed beard, a satchel of scrolls on a strap across the chest and a
book hanging at the left hip from the sash.
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import town_matron as K
from town_matron import Kit, P_, pal, rope, lerp
from town_elder import shawl_surface, shawl_w

PROPS = proportions(0.98, shoulder_x=0.185 * 0.98)
PALETTE = "town_scholar"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.10, 0.06, 0.16)),              # preview: Lantern violet robe
    "BH_Cloth_Secondary": pal((0.26, 0.22, 0.16), 0.9),       # cape / sash (dun wool)
    "BH_Skin": pal((0.50, 0.33, 0.22), 0.55),
    "BH_Hair": pal((0.12, 0.09, 0.07), 0.6),
    "BH_Gold": pal((0.62, 0.45, 0.18), 0.35, 1.0),            # spectacle rims, clasp
    "BH_Bone": pal((0.66, 0.60, 0.46), 0.8),                  # paper: scrolls, pages
    "BH_Wood": pal((0.14, 0.08, 0.04), 0.8),
})

SC_TORSO = K.torso_rows(chest=0.97, waist=1.0, hip=1.0, depth=1.0)


def build(body):
    k = Kit(body)
    rows = SC_TORSO
    # ---- robe
    K.body_shell(k, rows, 0.98, 1.53, "BH_Cloth_Primary", n=24, cap1=True, name="robe_top")
    sk_rows = K.flare_rows(1.06, 0.07, (0.152, 0.102, 0.106), (0.22, 0.2, 0.25), n=8, curve=1.0)
    sk, _ = K.skirt(sk_rows, "BH_Cloth_Primary", folds=7, amp=0.009)
    k.add(sk, w=k.skirt_w(1.02, 0.5, max_leg=0.8, center_w=0.08))
    # front placket trim down the robe
    pts = [(0, K.front_y(rows, 0, z) - 0.004, z) for z in np.linspace(1.5, 1.07, 6)]
    pts += [(0, K.front_y(sk_rows, 0, z, p=2.2) - 0.004, z) for z in np.linspace(1.0, 0.1, 7)]
    V, F = M.tube(pts, [(0.018, 0.004)] * len(pts), n=6, up=(0, -1, 0), p=3.0)
    k.add(P_(V, F, "BH_Cloth_Secondary", "placket"),
          w=lambda V: [a if v[2] > 1.04 * k.s else b for v, a, b in
                       zip(V, k.torso_w()(V), k.skirt_w(1.02, 0.5, max_leg=0.8, center_w=0.08)(V))])
    # sash
    K.band(k, rows, 1.05, 1.09, "BH_Cloth_Secondary", g_out=0.014, g_in=0.004, n=24, bev=0.0)
    # ---- wide sleeves
    for s in "LR":
        K.sleeve(k, s, K.SHOULDER_CAP + [(0.5, 0.056, 0.058), (1.0, 0.06, 0.062), (1.5, 0.075, 0.076),
                                         (1.88, 0.088, 0.088)], "BH_Cloth_Primary", n=14, solid=0.006, cap1=False)
        K.arm_ring(k, s, 1.86, 0.09, 0.03, "BH_Cloth_Secondary", name="cuff")
        K.sleeve(k, s, [(1.3, 0.038, 0.038), (2.0, 0.031, 0.029)], "BH_Skin", n=8, name="wrist")
        K.mitten(k, s)
    for s in "LR":
        K.leg_tube(k, s, [(0.15, 0.07, 0.07), (1.0, 0.05, 0.052), (1.9, 0.04, 0.042)], "BH_Cloth_Secondary", n=8)
    K.shoes(k, "BH_Leather", sole="BH_Wood")
    # ---- short cape with a gathered hood at the back
    rings = shawl_surface(40, 6, math.radians(12), (0.10, 0.085, 0.09), (0.29, 0.2, 0.21), 0.19, 0.2, 0.22, 1.575)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Secondary", "cape"), 0.01, offset=1.0), w=shawl_w(k))
    V, F = M.tube(rings[0], [(0.008, 0.008)] * len(rings[0]), n=6, up=(0, 0, 1))
    k.add(P_(V, F, "BH_Cloth_Primary", "cape_hem"), w=shawl_w(k))
    hood_back(k, rows)
    V, F = M.lathe([(0, -0.006), (0.018, -0.005), (0.02, 0.003), (0, 0.006)], 10)
    k.add(P_(V, F, "BH_Gold", "clasp").rot(Rx(90)).move((0, -0.112, 1.50)), "chest")
    # ---- satchel + book
    satchel(k, rows)
    book(k, rows)
    # ---- head
    hr = K.head(k, jaw=1.0, nose=1.05, brow=1.0)
    hair_beard(k, hr)
    spectacles(k)
    K.check_normals(body, "scholar")


def hood_back(k, rows):
    """Lowered hood: a soft roll of cloth lying on the cape behind the neck."""
    rings = []
    for z, rx, ry, cy in ((1.56, 0.07, 0.03, 0.07), (1.52, 0.11, 0.05, 0.1), (1.46, 0.12, 0.055, 0.13),
                          (1.40, 0.10, 0.045, 0.15), (1.36, 0.05, 0.02, 0.155)):
        rings.append(np.array([(rx * math.cos(a), cy + ry * math.sin(a), z)
                               for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]))
    V, F = M.loft(rings)
    k.add(K.outward(P_(V, F, "BH_Cloth_Secondary", "hood")), "chest")
    # dark fold showing the hood's inside


def satchel(k, rows):
    # strap from the left shoulder across the chest to the right hip
    pts = []
    for t in np.linspace(0, 1, 9):
        x = lerp(0.12, -0.17, t)
        z = lerp(1.47, 1.06, t)
        y = front_y(rows, x * 0.95, z) - 0.02 - (0.01 if t < 0.3 else 0.0)
        pts.append((x, y, z))
    V, F = M.tube(pts, [(0.018, 0.004)] * len(pts), n=6, up=(0, -1, 0), p=3.0)
    k.add(P_(V, F, "BH_Leather", "strap"), w=k.torso_w())
    pts = []
    for t in np.linspace(0, 1, 7):
        x = lerp(0.12, -0.17, t)
        z = lerp(1.47, 1.06, t)
        pts.append((x, back_y(rows, x * 0.95, z) + 0.02, z))
    V, F = M.tube(pts, [(0.018, 0.004)] * len(pts), n=6, up=(0, 1, 0), p=3.0)
    k.add(P_(V, F, "BH_Leather", "strap_b"), w=k.torso_w())
    # the bag on the right hip
    q, ang = K.on_ring(rows, 0.98, 0.05, 0.74)
    q = np.asarray(q)
    V, F = M.box(0.17, 0.06, 0.15)
    bag = M.bevel(P_(V, F, "BH_Leather", "satchel"), 0.02, 2).rot(Rz(ang)).move(q)
    k.add(bag, "hips")
    V, F = M.box(0.175, 0.066, 0.07, center=(0, -0.002, 0.05))
    k.add(M.bevel(P_(V, F, "BH_Leather", "flap"), 0.01, 1).rot(Rz(ang)).move(q), "hips")
    # scroll tubes sticking out of the bag top
    for dx, dz, r, tilt in ((-0.05, 0.12, 0.018, 8), (-0.01, 0.15, 0.02, -4), (0.035, 0.1, 0.016, -12)):
        c = q + Rz(ang) @ np.array([dx, 0.012, 0.0])
        top = c + Rz(ang) @ (Ry(tilt) @ np.array([0, 0, dz + 0.06]))
        V, F = M.tube([c, top], [(r, r), (r, r)], n=8, up=(0, -1, 0))
        k.add(P_(V, F, "BH_Bone", "scroll"), "hips")
        V, F = M.tube([top - (top - c) * 0.25, top - (top - c) * 0.18], [(r * 1.08, r * 1.08)] * 2, n=8, up=(0, -1, 0))
        k.add(P_(V, F, "BH_Cloth_Primary", "ribbon"), "hips")


def book(k, rows):
    q, ang = K.on_ring(rows, 1.0, 0.045, 0.2)
    q = np.asarray(q)
    V, F = M.box(0.12, 0.045, 0.16)
    k.add(M.bevel(P_(V, F, "BH_Leather", "book"), 0.008, 1).rot(Rz(ang)).move(q), "hips")
    V, F = M.box(0.108, 0.05, 0.146, center=(0.006, 0, 0))
    k.add(P_(V, F, "BH_Bone", "pages").rot(Rz(ang)).move(q), "hips")
    V, F = M.box(0.13, 0.052, 0.016, center=(0, 0, 0.02))
    k.add(P_(V, F, "BH_Gold", "book_band").rot(Rz(ang)).move(q), "hips")
    top = q + (0, 0, 0.085)
    k.add(rope([top, top + (0, 0.0, 0.05)], 0.005, "BH_Leather"), "hips")


def hair_beard(k, hr):
    line = K.hairline(1.775, 1.70, 1.635, sharp=0.7)
    V, F = K.head_shell(hr, lambda v: 0.008 + 0.006 * (1 - v), line, nu=24, nv=6, top_bulge=0.006)
    k.add(M.solidify(P_(V, F, "BH_Hair", "hair"), 0.008, offset=-1.0), "head")

    # short trimmed beard along the jaw and chin
    def fn(u, v):
        uu = -0.27 + 0.54 * u
        top = lerp(1.675, 1.638, math.cos(uu * math.pi / 0.54) ** 2)
        z = lerp(1.586, top, v)
        q = K.ring_frac(hr, max(z, 1.59), 0.006, [uu], p=2.1)[0]
        q[2] = z
        if z < 1.6:
            q[1] -= (1.6 - z) * 0.4
        return q
    V, F = M.grid(fn, 13, 5)
    k.add(M.solidify(P_(V, F, "BH_Hair", "beard"), 0.009, offset=1.0), "head")
    V, F = M.tube([(-0.032, -0.08, 1.645), (-0.012, -0.09, 1.652), (0.012, -0.09, 1.652), (0.032, -0.08, 1.645)],
                  [(0.005, 0.005), (0.007, 0.006), (0.007, 0.006), (0.005, 0.005)], n=6, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Hair", "moustache"), "head")


def spectacles(k):
    for sx in (1, -1):
        c = np.array([sx * 0.03, -0.082, 1.70])
        ring = K.ring_pts(c, 0.017, (0, -1, 0), n=12)
        V, F = M.tube(ring, [(0.0025, 0.0025)] * len(ring), n=5, up=(0, -1, 0), cap0=False, cap1=False)
        k.add(P_(V, F, "BH_Gold", "lens_rim"), "head")
        k.add(rope([c + (sx * 0.017, 0, 0.004), (sx * 0.072, -0.04, 1.705), (sx * 0.074, 0.0, 1.698)], 0.002, "BH_Gold",
                   n=4), "head")
    k.add(rope([(-0.013, -0.084, 1.703), (0, -0.088, 1.706), (0.013, -0.084, 1.703)], 0.0022, "BH_Gold", n=4), "head")
