"""Townsfolk: the old fisherman (Old Marrow).

A lean, weathered old man, slightly stooped: an oilskin sou'wester rain hat with a chin cord, an open
sleeveless vest over a bare chest and trousers rolled to mid-calf (both BH_Cloth_Primary, tinted), a rope belt, bare feet in
sandals and a coiled fishing net with wooden floats slung over the left shoulder.
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import town_matron as K
from town_matron import Kit, P_, pal, rope, lerp
from char_mage import ring_frac

PROPS = proportions(0.95, shoulder_x=0.18 * 0.95, hip_x=0.098 * 0.95)
PALETTE = "town_fisher"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.24, 0.16, 0.08)),              # preview: faded ochre vest
    "BH_Cloth_Accent": pal((0.20, 0.23, 0.15), 0.95),         # net twine (green-brown)
    "BH_Skin": pal((0.36, 0.20, 0.12), 0.6),                  # sun-dark
    "BH_Hair": pal((0.42, 0.41, 0.39), 0.7),                  # white
    "BH_Wood": pal((0.30, 0.20, 0.10), 0.8),                  # net floats
    "BH_Leather": pal((0.14, 0.08, 0.04), 0.7),
})

F_TORSO = K.torso_rows(chest=0.9, waist=0.9, hip=0.95, depth=0.94, hump=0.022, shoulder=0.95)
FWD = -0.02


def build(body):
    k = Kit(body)
    rows = F_TORSO
    # ---- bare torso (skin) with a hint of collarbones
    K.body_shell(k, rows, 0.98, 1.53, "BH_Skin", n=22, cap1=True, name="chest")
    vest(k, rows)
    # ---- trousers rolled to mid-calf, rope belt
    V, F = K.torso_loft([(0.84, 0.143, 0.09, 0.098, 0.0), (0.92, 0.145, 0.095, 0.1, 0.0),
                         (1.02, 0.14, 0.094, 0.098, 0.0)], n=22)
    k.add(P_(V, F, "BH_Cloth_Primary", "seat"), w=k.b.skirt_weights(0.98 * k.s, 0.84 * k.s, max_leg=0.7, center_w=0.05))
    for s in "LR":
        K.leg_tube(k, s, [(-0.02, 0.078, 0.082), (0.4, 0.068, 0.072), (1.0, 0.056, 0.06), (1.35, 0.055, 0.057)],
                   "BH_Cloth_Primary", n=12, name="trouser")
        # rolled hem
        b = k.b
        kn, a = b.head("shin." + s), b.tail("shin." + s)
        c = kn + (a - kn) * 0.36
        V, F = M.tube([c + (0, 0, 0.02 * k.s), c - (0, 0, 0.02 * k.s)], [(0.061 * k.s, 0.064 * k.s)] * 2, n=12,
                      up=(0, -1, 0))
        b.add(P_(V, F, "BH_Cloth_Primary", "roll"), "shin." + s)
        K.leg_tube(k, s, [(1.3, 0.042, 0.046), (1.6, 0.036, 0.04), (1.97, 0.03, 0.032)], "BH_Skin", n=10, name="calf")
    K.bare_foot(k, "BH_Skin", sandal="BH_Leather")
    K.band(k, rows, 1.0, 1.03, "BH_Wood", g_out=0.012, g_in=0.0, n=22, bev=0.0)
    q = np.array([0.05, K.front_y(rows, 0.05, 1.0) - 0.012, 0.99])
    k.add(rope([q, q + (0.01, -0.01, -0.08), q + (0.02, -0.012, -0.15)], 0.007, "BH_Wood"),
          w=k.skirt_w(1.0, 0.7, max_leg=0.4))
    # ---- lean bare arms
    for s in "LR":
        K.sleeve(k, s, [(-0.16, 0.03, 0.034), (-0.08, 0.046, 0.05), (0.05, 0.05, 0.052), (0.5, 0.042, 0.044),
                        (1.0, 0.036, 0.037), (1.4, 0.04, 0.037), (2.02, 0.028, 0.025)], "BH_Skin", n=10, name="arm")
        K.mitten(k, s, size=1.02)
    # ---- net over the left shoulder
    net(k, rows)
    # ---- head, hat
    hr = K.head(k, jaw=0.95, width=0.96, fwd=FWD, nose=1.12, brow=1.1, neck_r=0.045)
    hair(k, hr)
    hat(k, hr)
    K.check_normals(body, "fisher")


def vest(k, rows):
    zs = [0.97, 1.04, 1.12, 1.2, 1.28, 1.35, 1.41, 1.46, 1.5, 1.525]
    nu = 30
    rings = []
    for z in zs:
        t = (z - 0.97) / 0.555
        a0 = 0.1 + 0.06 * t                    # open front, widening toward the collar
        fr = a0 + (1 - 2 * a0) * np.linspace(0, 1, nu)
        rings.append(ring_frac(rows, z, 0.012, fr))
    # armholes: pull the side columns in at shoulder height (the vest is sleeveless) by trimming the top rings
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    vs = M.solidify(P_(V, F, "BH_Cloth_Primary", "vest"), 0.008, offset=1.0)
    k.add(vs, w=k.torso_w())
    for kk in (0, -1):
        edge = np.array([r[kk] for r in rings]) + np.array([0, -0.004, 0])
        V, F = M.tube(edge, [(0.008, 0.006)] * len(edge), n=6, up=(0, -1, 0))
        k.add(P_(V, F, "BH_Cloth_Primary", "vest_edge"), w=k.torso_w())
    # side pocket patches
    for sx in (1, -1):
        x, z = sx * 0.1, 1.06
        V, F = M.box(0.07, 0.01, 0.07, center=(x, K.front_y(rows, x, z) - 0.02, z))
        k.add(M.bevel(P_(V, F, "BH_Cloth_Primary", "pocket").rot(Rz(-sx * 25), center=(x, 0, z)), 0.004, 1),
              w=k.torso_w())


def net(k, rows):
    """A coiled net: a thick bundle loop from the left shoulder across the chest to the right hip and back."""
    loop = []
    n = 28
    for i in range(n):
        a = 2 * math.pi * i / n
        t = (1 - math.cos(a)) / 2                 # 0 over the left shoulder, 1 at the right hip
        x = lerp(0.12, -0.19, t)
        z = lerp(1.545, 1.0, t)
        zc = min(max(z, 0.98), 1.5)
        front = math.sin(a) > 0
        depth = abs(math.sin(a)) ** 0.5
        if front:
            y = (K.front_y(rows, x * 0.9, zc) - 0.055) * depth
        else:
            y = (K.back_y(rows, x * 0.9, zc) + 0.055) * depth
        loop.append((x, y, z))
    loop = np.array(loop)
    loop = np.vstack([loop, loop[:1]])
    prof = [(0.062 + 0.016 * math.sin(i * 1.7), 0.042 + 0.01 * math.cos(i * 2.3)) for i in range(len(loop))]
    V, F = M.tube(loop, prof, n=8, up=(0, 1, 0), cap0=False, cap1=False)
    w = k.zw([(1.08, "spine"), (1.3, "chest")])
    k.add(P_(V, F, "BH_Cloth_Accent", "net"), w=w)
    # loose mesh lines wrapped around the bundle
    for off in (0.0, 0.33, 0.66):
        pts = []
        for i in range(len(loop) - 1):
            p, q = loop[i], loop[i + 1]
            d = normalize(q - p)
            side = normalize(np.cross(d, np.array([0, 1.0, 0])))
            ang = (i / 2.0 + off * 6) % (2 * math.pi)
            pts.append(p + side * 0.068 * math.cos(ang) + np.array([0, 0.047, 0]) * math.sin(ang))
        k.add(rope(pts, 0.004, "BH_Cloth_Accent", n=4), w=w)
    # wooden floats tied on the bundle
    for i in (3, 9, 16, 21):
        p = loop[i]
        V, F = M.sphere(0.026, 8, 5, center=p + (0, -0.03 if p[1] < 0 else 0.03, -0.02), scale=(1, 1, 1.3))
        k.add(P_(V, F, "BH_Wood", "float"), w=w)


def hair(k, hr):
    # thin white hair only around the back and sides (under the hat)
    line = K.hairline(1.70, 1.66, 1.62)
    rings = []
    for v in (0.0, 1.0):
        ring = []
        for u in np.linspace(0.2, 0.8, 13):
            z = line(u) + 0.035 * v
            ring.append(ring_frac(hr, z, 0.006, [u], p=2.1)[0])
        rings.append(np.array(ring))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Hair", "hair"), 0.006, offset=1.0), "head")
    # wispy white goatee + moustache
    V, F = M.sphere(0.02, 8, 5, center=(0, -0.066 + FWD, 1.598), scale=(1.0, 0.7, 1.5))
    k.add(P_(V, F, "BH_Hair", "goatee"), "head")
    V, F = M.tube([(-0.035, -0.078 + FWD, 1.64), (-0.012, -0.089 + FWD, 1.65), (0.012, -0.089 + FWD, 1.65),
                   (0.035, -0.078 + FWD, 1.64)], [(0.005, 0.004), (0.006, 0.005), (0.006, 0.005), (0.005, 0.004)],
                  n=6, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Hair", "moustache"), "head")


def hat(k, hr):
    """Oilskin sou'wester: a round stitched crown, the brim turned up a little at the front and sloping long and low
    over the ears and the back of the neck (keeps the spray off). Tarred olive canvas (BH_Cloth_Accent)."""
    y0 = FWD + 0.01
    base_z = 1.768
    prof = [(0.104, base_z - 0.004), (0.107, 1.8), (0.1, 1.84), (0.083, 1.872), (0.052, 1.893), (0.0, 1.9)]
    V, F = M.lathe(prof, 28, cap=True)
    k.add(K.outward(P_(V, F, "BH_Cloth_Accent", "hat_crown").move((0, y0, 0))), "head")

    # brim: u runs around the head (front = -y), v from the crown out to the edge
    def brim_pt(u, v):
        a = u * 2.0 * math.pi
        back = 0.5 * (1.0 + math.sin(a))          # 0 at the front (-y), 1 at the back (+y)
        reach = 0.05 + 0.095 * back ** 1.4
        r = 0.104 + reach * v
        droop = -(0.012 + 0.085 * back ** 1.3) * v ** 1.3
        lift = 0.018 * (1.0 - back) ** 2 * v * v   # the short front brim turns up
        return (r * math.cos(a), y0 + r * math.sin(a), base_z + droop + lift)
    V, F = M.grid(brim_pt, 36, 5, closed_u=True)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Accent", "hat_brim"), 0.007, 0.0), "head")
    # a stitched band where the brim meets the crown
    ring = K.ring_pts((0, y0, base_z + 0.012), 0.108, (0, 0, 1), n=28)
    V, F = M.tube(ring, [(0.006, 0.004)] * len(ring), n=4, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Leather", "hat_band"), "head")
    # inner headband sitting on the skull
    V, F = M.tube([(0, y0 - 0.006, 1.77), (0, y0 - 0.006, 1.81)], [(0.082, 0.098)] * 2, n=16, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Leather", "headband"), "head")
    # chin cord
    for sx in (1, -1):
        k.add(rope([(sx * 0.08, y0 + 0.005, 1.77), (sx * 0.074, y0 - 0.02, 1.66), (sx * 0.05, y0 - 0.05, 1.6),
                    (0, y0 - 0.066, 1.585)], 0.003, "BH_Leather", n=4), "head")
