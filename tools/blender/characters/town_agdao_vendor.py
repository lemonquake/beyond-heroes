"""Townsfolk (bh-029, Zarael): Agdao's traders (Dorrit Vask, Brisa Kettle, Sorrel the fishmonger).

A market woman: a long woven tunic (BH_Cloth_Primary, tinted per NPC) with ochre-and-cream stepped-fret borders at the
neck and hem, short sleeves, a cream apron with a red stripe, three strands of turquoise / coral / jade beads, a woven
shoulder bag on a strap across the body, a tall striped headwrap (the portrait), jade drop earrings, copper bracelets
(one with a thin white-glowing wire) and sandals.
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

PROPS = proportions(0.95, shoulder_x=0.172 * 0.95, hip_x=0.099 * 0.95)
PALETTE = "town_agdao_vendor"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.42, 0.17, 0.10)),              # preview: madder tunic (game tint per NPC)
    "BH_Cloth_Secondary": pal((0.64, 0.58, 0.45), 0.92),      # cream apron, fret steps
    "BH_Cloth_Accent": pal((0.62, 0.40, 0.10), 0.88),         # ochre borders, headwrap band
    "BH_Cloth_Red": pal((0.42, 0.07, 0.05), 0.88),            # apron stripe, headwrap band
    "BH_Cloth_Teal": pal((0.06, 0.32, 0.30), 0.88),           # headwrap band
    "BH_Wicker": pal((0.45, 0.33, 0.17), 0.9),                # woven bag
    "BH_Turquoise": pal((0.10, 0.50, 0.48), 0.35),
    "BH_Coral": pal((0.55, 0.16, 0.08), 0.5),
    "BH_Jade": pal((0.08, 0.38, 0.24), 0.3),
    "BH_Gold": pal((0.72, 0.42, 0.18), 0.35, 1.0),            # copper bracelets
    "BH_Skin": pal((0.44, 0.27, 0.17), 0.55),
    "BH_Hair": pal((0.04, 0.028, 0.02), 0.6),
    "BH_Leather": pal((0.15, 0.085, 0.045), 0.65),
    "BH_Emissive": Z.WHITE_GLOW,                              # one thin wire bracelet
})

V_TORSO = K.torso_rows(chest=0.92, waist=0.9, hip=1.1, depth=1.0, bust=0.02, shoulder=0.94)


def build(body):
    k = Kit(body)
    rows = V_TORSO
    # ---- tunic: bodice + skirt to mid-calf, fret borders
    K.body_shell(k, rows, 0.98, 1.53, "BH_Cloth_Primary", n=24, cap1=True, name="bodice")
    sk_rows = K.flare_rows(1.07, 0.3, (0.152, 0.104, 0.112), (0.23, 0.2, 0.22), n=7, curve=0.95)
    sk, rings = K.skirt(sk_rows, "BH_Cloth_Primary", folds=9, amp=0.01)
    sw = k.skirt_w(1.02, 0.5, max_leg=0.8, center_w=0.08)
    k.add(sk, w=sw)
    hem_fret(k, sk_rows, 0.36, sw)
    neck_fret(k, rows)
    # ---- apron + waist sash
    apron(k, rows, sk_rows)
    K.band(k, rows, 1.05, 1.09, "BH_Cloth_Red", g_out=0.014, g_in=0.004, n=24, bev=0.0)
    # ---- arms: short sleeves, bare forearms, copper bracelets
    for s in "LR":
        K.sleeve(k, s, K.SHOULDER_CAP + [(0.35, 0.056, 0.058), (0.62, 0.062, 0.062)], "BH_Cloth_Primary", n=12,
                 solid=0.005, cap1=False)
        K.arm_ring(k, s, 0.6, 0.062, 0.03, "BH_Cloth_Accent", name="sleeve_hem")
        K.bare_arm(k, s, t0=0.55, r_up=0.044, r_el=0.037, r_wr=0.029)
        K.arm_ring(k, s, 1.82, 0.034, 0.016, "BH_Gold", name="bracelet")
        K.mitten(k, s, size=0.95)
    K.arm_ring(k, "R", 1.74, 0.035, 0.012, "BH_Emissive", name="wire_glow")
    for s in "LR":
        K.leg_tube(k, s, [(0.15, 0.07, 0.07), (1.0, 0.048, 0.05), (1.6, 0.04, 0.041), (2.0, 0.034, 0.036)], "BH_Skin",
                   n=8)
    K.bare_foot(k, sandal="BH_Leather")
    # ---- necklaces, bag
    beads(k, rows)
    bag(k, rows)
    # ---- head: headwrap, earrings
    hr = K.head(k, jaw=0.93, width=0.96, nose=0.98, brow=0.8)
    headwrap(k, hr)
    K.check_normals(body, "agdao_vendor")


def hem_fret(k, sk_rows, z, w):
    fr = np.linspace(0, 1, 30, endpoint=False)
    lo = K.ring_frac(sk_rows, z - 0.025, 0.004, fr, p=2.2)
    hi = K.ring_frac(sk_rows, z + 0.025, 0.004, fr, p=2.2)
    V, F = M.loft([lo, hi], cap0=False, cap1=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Accent", "hem_band"), 0.005, offset=1.0), w=w)
    n = 24
    for i in range(n):
        f = (i + 0.5) / n
        q = K.ring_frac(sk_rows, z + (0.008 if i % 2 else -0.008), 0.012, [f], p=2.2)[0]
        V, F = M.box(0.026, 0.006, 0.016)
        k.add(P_(V, F, "BH_Cloth_Secondary", "fret_step").rot(Rz(math.degrees(2 * math.pi * f))).move(q), w=w)


def neck_fret(k, rows):
    ring = []
    for a in np.linspace(0, 2 * math.pi, 21):
        ring.append((0.1 * math.sin(a), 0.0 - 0.09 * math.cos(a), 1.5 + 0.012 * math.cos(a)))
    V, F = M.tube(ring, [(0.018, 0.006)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False, p=3.0)
    k.add(P_(V, F, "BH_Cloth_Accent", "neck_band"), "chest")


def apron(k, rows, sk_rows):
    def fn(u, v):
        x = (u - 0.5) * 2 * (0.12 + 0.04 * v)
        z = lerp(1.06, 0.48, v)
        y = front_y(sk_rows, x, min(z, 1.06), p=2.2) - 0.014 - 0.008 * v
        y += 0.005 * math.sin(u * math.pi * 5) * v
        return (x, y, z)
    V, F = M.grid(fn, 7, 7)
    w = k.skirt_w(1.02, 0.5, max_leg=0.8, center_w=0.1)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Secondary", "apron").flip(), 0.006, offset=-1.0), w=w)
    for zz in (0.55, 0.585):
        def fs(u, v, zz=zz):
            x = (u - 0.5) * 2 * (0.12 + 0.04 * (1.06 - zz) / 0.58 + 0.002)
            z = zz + 0.01 * (v - 0.5)
            t = (1.06 - z) / 0.58
            return (x, front_y(sk_rows, x, min(z, 1.06), p=2.2) - 0.0215 - 0.008 * t, z)
        V, F = M.grid(fs, 7, 2)
        k.add(P_(V, F, "BH_Cloth_Red", "apron_stripe"), w=w)


def strand(k, pts, r, mats, name="beads"):
    """A bead strand: a lobed tube (one bump per bead), split in alternating colour runs."""
    pts = np.asarray(pts, float)
    dense = []
    for i in range(len(pts) - 1):
        for t in np.linspace(0, 1, 4, endpoint=False):
            dense.append(pts[i] + (pts[i + 1] - pts[i]) * t)
    dense.append(pts[-1])
    dense = np.array(dense)
    runs = np.array_split(np.arange(len(dense)), len(mats))
    for j, idx in enumerate(runs):
        if j < len(runs) - 1:
            idx = np.append(idx, runs[j + 1][0])
        seg = dense[idx]
        prof = [(r * (0.75 + 0.25 * abs(math.cos(i * math.pi / 2))),) * 2 for i in range(len(seg))]
        V, F = M.tube(seg, prof, n=6, up=(0, -1, 0))
        k.add(P_(V, F, mats[j], name), "chest")


def beads(k, rows):
    for i, (depth, mats) in enumerate(((0.06, ("BH_Turquoise", "BH_Coral", "BH_Turquoise")),
                                       (0.1, ("BH_Coral", "BH_Jade", "BH_Coral")),
                                       (0.14, ("BH_Jade", "BH_Turquoise", "BH_Jade")))):
        pts = []
        for a in np.linspace(-1.05, 1.05, 9):
            x = 0.085 * math.sin(a)
            z = 1.505 - depth * math.cos(a) ** 2
            pts.append((x, front_y(rows, x, z) - 0.012 - 0.003 * i, z))
        strand(k, pts, 0.008, mats)


def bag(k, rows):
    # strap from the right shoulder across the chest to the left hip
    pts = []
    for t in np.linspace(0, 1, 8):
        x = lerp(-0.12, 0.16, t)
        z = lerp(1.48, 1.03, t)
        pts.append((x, front_y(rows, x * 0.95, z) - 0.03, z))
    V, F = M.tube(pts, [(0.018, 0.004)] * len(pts), n=5, up=(0, -1, 0), p=3.0)
    k.add(P_(V, F, "BH_Cloth_Red", "strap"), w=k.torso_w())
    pts = []
    for t in np.linspace(0, 1, 6):
        x = lerp(-0.12, 0.16, t)
        z = lerp(1.48, 1.03, t)
        pts.append((x, back_y(rows, x * 0.95, z) + 0.016, z))
    V, F = M.tube(pts, [(0.018, 0.004)] * len(pts), n=5, up=(0, 1, 0), p=3.0)
    k.add(P_(V, F, "BH_Cloth_Red", "strap_b"), w=k.torso_w())
    q, ang = K.on_ring(rows, 0.95, 0.075, 0.34)
    q = np.asarray(q)
    V, F = M.lathe([(0.0, -0.1), (0.09, -0.095), (0.11, -0.05), (0.115, 0.03), (0.1, 0.07), (0.0, 0.075)], 12)
    p = K.outward(P_(V, F, "BH_Wicker", "bag"))
    p.V = p.V * np.array([1.12, 0.46, 1.12])
    k.add(p.rot(Rz(ang)).move(q), "hips")
    for z, mat in ((-0.03, "BH_Cloth_Red"), (0.02, "BH_Cloth_Teal")):
        V, F = M.lathe([(0.114, z - 0.01), (0.118, z), (0.114, z + 0.01)], 12, cap=False)
        V = V * np.array([1.12, 0.48, 1.12])
        k.add(P_(V, F, mat, "bag_band").rot(Rz(ang)).move(q), "hips")
    # a few fish / greens poking out of the top
    for dx, h, mat in ((-0.04, 0.09, "BH_Cloth_Teal"), (0.02, 0.07, "BH_Jade")):
        c = q + Rz(ang) @ np.array([dx, 0.0, 0.07])
        V, F = M.sphere(0.03, 8, 5, center=c + (0, 0, h * 0.4), scale=(0.6, 0.6, 1.4))
        k.add(P_(V, F, mat, "greens"), "hips")


def headwrap(k, hr):
    line = K.hairline(1.75, 1.69, 1.63)
    V, F = K.head_shell(hr, 0.006, line, nu=20, nv=4)
    k.add(P_(V, F, "BH_Hair", "hair"), "head")
    # wrap: hugs the skull from the brow, then rises in a tall stack of striped bands, leaning back a little
    hl = K.hairline(1.765, 1.715, 1.66, sharp=0.9)
    V, F = K.head_shell(hr, lambda v: 0.018 + 0.006 * (1 - v), hl, nu=24, nv=5, top_bulge=0.01)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Accent", "wrap"), 0.008, offset=-1.0), "head")
    top = hr[-1][0]
    c0 = np.array([0.0, 0.012, top - 0.02])
    bands = (("BH_Cloth_Red", 0.093, 0.0, 0.035), ("BH_Cloth_Teal", 0.098, 0.035, 0.068),
             ("BH_Cloth_Accent", 0.1, 0.068, 0.1), ("BH_Cloth_Red", 0.098, 0.1, 0.128), ("BH_Cloth_Secondary", 0.09, 0.128, 0.152))
    for mat, r, z0, z1 in bands:
        prof = [(r * 0.96, z0), (r, z0 + 0.008), (r, z1 - 0.008), (r * 0.96, z1)]
        V, F = M.lathe(prof, 16, cap=False)
        V = V * np.array([1.0, 0.86, 1.0])
        k.add(P_(V, F, mat, "wrap_band").rot(Rx(-10)).move(c0), "head")
    V, F = M.lathe([(0.09 * 0.96, 0.152), (0.07, 0.162), (0.0, 0.166)], 16)
    V = V * np.array([1.0, 0.86, 1.0])
    k.add(P_(V, F, "BH_Cloth_Secondary", "wrap_top").rot(Rx(-10)).move(c0), "head")
    # a jade bead pinned at the front of the wrap
    V, F = M.sphere(0.014, 8, 5, center=(0, -0.086, 0.05), scale=(1.2, 0.6, 1.0))
    k.add(P_(V, F, "BH_Jade", "wrap_pin").rot(Rx(-10)).move(c0), "head")
    # jade drop earrings
    for sx in (1, -1):
        c = np.array([sx * 0.074 * 0.96, -0.004, 1.655])
        k.add(rope([c, c - (0, 0, 0.014)], 0.0018, "BH_Gold", n=4), "head")
        V, F = M.sphere(0.009, 8, 5, center=c - (0, 0, 0.026), scale=(0.8, 0.8, 1.4))
        k.add(P_(V, F, "BH_Jade", "earring"), "head")
