"""Townsfolk (bh-029, Zarael): Agdao's elders and healers (Mother Ysenne, Speaker Caius Wend).

An elder, slightly stooped (rounded back, head carried forward): a long robe (BH_Cloth_Primary, tinted per NPC) under a
long cream mantle with a brick-red and teal stepped-fret hem, a collar of overlapping teal feathers over a scarlet
under-row (the portrait), jade ear-spool discs, white hair in a top-knot bound with a cream cloth and a jade pin, white
brows, sandals, and a carved walking staff with a stepped head and a jade inset (rigid to hand.R), copper-bound, with
one thin white-glowing wire ring under the head.
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
from town_traveler import cloak_w
import town_terax as Z

PROPS = proportions(0.93, shoulder_x=0.172 * 0.93, hip_x=0.098 * 0.93)
PALETTE = "town_agdao_elder"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.34, 0.26, 0.18)),              # preview: robe (game tint per NPC)
    "BH_Cloth_Secondary": pal((0.68, 0.63, 0.52), 0.92),      # cream mantle
    "BH_Cloth_Accent": pal((0.40, 0.08, 0.05), 0.88),         # brick-red fret band
    "BH_Cloth_Teal": pal((0.06, 0.32, 0.30), 0.88),           # teal fret steps
    "BH_Feather": pal((0.05, 0.36, 0.32), 0.7),               # teal collar feathers
    "BH_FeatherRed": pal((0.52, 0.08, 0.05), 0.7),            # scarlet under-row
    "BH_Jade": pal((0.08, 0.40, 0.28), 0.3),
    "BH_Gold": pal((0.72, 0.42, 0.18), 0.35, 1.0),
    "BH_Skin": pal((0.38, 0.24, 0.16), 0.62),
    "BH_Hair": pal((0.82, 0.81, 0.78), 0.75),                 # white
    "BH_Wood": pal((0.24, 0.15, 0.08), 0.75),                 # carved staff
    "BH_Leather": pal((0.15, 0.085, 0.045), 0.65),
    "BH_Emissive": Z.WHITE_GLOW,                              # thin wire ring on the staff
})

E_TORSO = K.torso_rows(chest=0.92, waist=0.98, hip=1.03, depth=1.0, hump=0.032, shoulder=0.92)
FWD = -0.03


def build(body):
    k = Kit(body)
    rows = E_TORSO
    # ---- long robe
    K.body_shell(k, rows, 0.98, 1.53, "BH_Cloth_Primary", n=24, cap1=True, name="robe_top")
    sk_rows = K.flare_rows(1.07, 0.07, (0.152, 0.104, 0.116), (0.22, 0.2, 0.22), n=8, curve=1.0)
    sk, _ = K.skirt(sk_rows, "BH_Cloth_Primary", folds=8, amp=0.009)
    k.add(sk, w=k.skirt_w(1.02, 0.5, max_leg=0.8, center_w=0.08))
    K.band(k, rows, 1.05, 1.08, "BH_Cloth_Accent", g_out=0.012, g_in=0.004, n=24, bev=0.0)
    # ---- long sleeves
    for s in "LR":
        K.sleeve(k, s, K.SHOULDER_CAP + [(0.4, 0.05, 0.052), (1.0, 0.048, 0.05), (1.6, 0.05, 0.051),
                                         (1.9, 0.056, 0.056)], "BH_Cloth_Primary", n=12, solid=0.005, cap1=False)
        K.sleeve(k, s, [(1.4, 0.034, 0.034), (2.0, 0.029, 0.027)], "BH_Skin", n=8, name="wrist")
        K.arm_ring(k, s, 1.86, 0.058, 0.028, "BH_Cloth_Secondary", name="cuff")
        K.mitten(k, s, size=0.93, curl=2.2 if s == "R" else 1.0)
    for s in "LR":
        K.leg_tube(k, s, [(0.15, 0.065, 0.065), (1.0, 0.045, 0.047), (1.7, 0.036, 0.037), (2.0, 0.032, 0.034)],
                   "BH_Skin", n=8)
    K.bare_foot(k, sandal="BH_Leather")
    # ---- mantle + feather collar
    mantle(k, rows)
    feather_collar(k)
    # ---- head
    hr = K.head(k, jaw=0.93, width=0.97, fwd=FWD, nose=1.08, brow=0.95, neck_r=0.046)
    hair(k, hr)
    staff(k)
    K.check_normals(body, "agdao_elder")


def mantle(k, rows):
    """Long cream mantle: a back panel from the shoulders to mid-calf wrapping round the sides, open in front."""
    nu, nv = 19, 11

    def fn(u, v):
        z = lerp(1.48, 0.3, v)
        half = lerp(0.21, 0.33, v)
        x = (u - 0.5) * 2 * half
        yb = back_y(rows, min(abs(x), 0.14) * 0.9, min(max(z, 1.15), 1.47)) + 0.035
        y = yb + 0.07 * v ** 1.1
        e = abs(u - 0.5) * 2
        y -= (0.16 * (1 - v) + 0.1) * e ** 2.0
        y += 0.012 * math.sin(u * math.pi * 8) * v
        return (x, y, z)
    V, F = M.grid(fn, nu, nv)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Secondary", "mantle").flip(), 0.01, offset=-1.0), w=cloak_w(k))
    # fret hem: red band + teal steps along the bottom edge
    hem = np.array([fn(i / (nu - 1), 1.0) for i in range(nu)])
    up = np.array([fn(i / (nu - 1), 0.93) for i in range(nu)])
    band = np.array([h + (u2 - h) * 0.45 for h, u2 in zip(hem, up)])
    V, F = M.tube(band, [(0.02, 0.005)] * len(band), n=4, up=(0, 1, 0), p=3.0)
    k.add(P_(V, F, "BH_Cloth_Accent", "mantle_fret"), w=cloak_w(k))
    for i in range(nu - 1):
        c = (band[i] + band[i + 1]) / 2 + np.array([0, 0.0, 0.008 if i % 2 else -0.008])
        d = normalize(band[i + 1] - band[i])
        out = normalize(np.cross(d, (0, 0, 1.0)))
        if out[1] < 0:
            out = -out
        V, F = M.box(0.024, 0.008, 0.012)
        ang = math.degrees(math.atan2(d[1], d[0]))
        k.add(P_(V, F, "BH_Cloth_Teal", "fret_step").rot(Rz(ang)).move(c + out * 0.006), w=cloak_w(k))
    # mantle over the shoulders
    rings = shawl_surface(34, 6, math.radians(20), (0.10, 0.085, 0.09), (0.28, 0.2, 0.22), 0.2, 0.2, 0.24, 1.58)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Secondary", "mantle_top"), 0.01, offset=1.0), w=shawl_w(k))
    # front edges (red)
    for kk in (0, -1):
        edge = np.array([r[kk] for r in rings])
        V, F = M.tube(edge, [(0.008, 0.008)] * len(edge), n=5, up=(0, 0, 1))
        k.add(P_(V, F, "BH_Cloth_Accent", "mantle_edge"), w=shawl_w(k))


def feather_collar(k):
    """Short collar of overlapping feathers: a scarlet under-row and a longer teal top row, all round the shoulders."""
    s = k.s
    base = shawl_surface(26, 3, math.radians(14), (0.10, 0.085, 0.09), (0.21, 0.16, 0.17), 0.08, 0.07, 0.07, 1.6)
    V, F = M.loft(base, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Accent", "collar_base"), 0.008, offset=1.0), w=shawl_w(k))
    top = base[-1]
    c0 = top.mean(0)
    for row, (L, W, mat, off, dz, bend) in enumerate(((0.145, 0.026, "BH_FeatherRed", 0.006, 0.0, -0.08),
                                                       (0.115, 0.032, "BH_Feather", 0.03, 0.02, -0.22))):
        for i in range(0, len(top)):
            p = top[i]
            out = normalize(np.array([p[0] - c0[0], p[1] - c0[1], 0.0]))
            d = normalize(np.array([0, 0, -1.0]) + out * 1.25)
            side = np.cross(d, out)
            b0 = (p + out * off + np.array([0, 0, dz])) * s
            for prt in Z.feather(b0, d, L * s, W * s, side, mat, None, bend=bend, nv=3, th=0.003 * s):
                k.b.add(prt, weights=shawl_w(k))
    # jade bead clasp at the throat
    V, F = M.sphere(0.016, 8, 5, center=(0, -0.122, 1.5), scale=(1, 0.6, 1.2))
    k.add(P_(V, F, "BH_Jade", "clasp"), "chest")


def hair(k, hr):
    line = K.hairline(1.755, 1.675, 1.62)
    V, F = K.head_shell(hr, lambda v: 0.01 + 0.004 * (1 - v), line, nu=24, nv=6, top_bulge=0.01)
    k.add(M.solidify(P_(V, F, "BH_Hair", "hair"), 0.008, offset=-1.0), "head")
    # white brows
    for sx in (1, -1):
        V, F = M.tube([(sx * 0.014, -0.08 + FWD, 1.722), (sx * 0.034, -0.079 + FWD, 1.728), (sx * 0.056, -0.068 + FWD, 1.72)],
                      [(0.006, 0.004)] * 3, n=5, up=(0, -1, 0))
        k.add(P_(V, F, "BH_Hair", "brow"), "head")
    # top-knot bound in a cream cloth, a jade pin through it
    top = hr[-1][0]
    c = np.array([0.0, 0.01 + FWD, top + 0.01])
    V, F = M.sphere(0.042, 10, 6, center=c + (0, 0, 0.02), scale=(1.0, 0.9, 0.85))
    k.add(K.outward(P_(V, F, "BH_Hair", "knot")), "head")
    V, F = M.lathe([(0.046, 0.0), (0.052, 0.012), (0.05, 0.03), (0.04, 0.042)], 14, cap=False)
    k.add(P_(V, F, "BH_Cloth_Secondary", "knot_cloth").move(c), "head")
    V, F = M.tube([c + (-0.058, -0.005, 0.03), c + (0.058, -0.005, 0.03)], [(0.0045, 0.0045)] * 2, n=6, up=(0, 0, 1))
    k.add(P_(V, F, "BH_Jade", "pin"), "head")
    for sx in (1, -1):
        V, F = M.sphere(0.0065, 8, 5, center=c + (sx * 0.06, -0.005, 0.03))
        k.add(P_(V, F, "BH_Jade", "pin_end"), "head")
    # jade ear-spool discs
    for sx in (1, -1):
        cc = np.array([sx * 0.077 * 0.97, 0.004 + FWD, 1.672])
        V, F = M.lathe([(0.0, -0.004), (0.016, -0.004), (0.018, 0.0), (0.016, 0.004), (0.0, 0.004)], 12)
        k.add(P_(V, F, "BH_Jade", "ear_spool").rot(Ry(90)).move(cc), "head")
        V, F = M.lathe([(0.0, -0.005), (0.007, -0.005), (0.007, 0.005), (0.0, 0.005)], 8)
        k.add(P_(V, F, "BH_Gold", "spool_core").rot(Ry(90)).move(cc + (sx * 0.002, 0, 0)), "head")


def staff(k):
    """Carved walking staff upright in the right hand (rigid to hand.R): a stepped head with a jade inset, copper
    bands, one thin white-glowing wire ring."""
    b = k.b
    g = b.head("weapon.R")
    top = g + np.array([0.0, -0.03, 0.42 * k.s])
    foot = np.array([g[0] - 0.03, g[1] - 0.08, 0.0])
    d = normalize(top - foot)
    V, F = M.tube([foot, foot + (top - foot) * 0.5, top], [(0.017, 0.017), (0.019, 0.019), (0.022, 0.022)], n=8,
                  up=(0, -1, 0))
    b.add(P_(V, F, "BH_Wood", "staff"), "hand.R")
    for t, mat, r in ((0.82, "BH_Gold", 0.025), (0.86, "BH_Emissive", 0.024), (0.9, "BH_Gold", 0.025),
                      (0.02, "BH_Gold", 0.02)):
        c = foot + (top - foot) * t
        V, F = M.tube([c - d * 0.01, c + d * 0.01], [(r, r)] * 2, n=8, up=(0, -1, 0))
        b.add(P_(V, F, mat, "band"), "hand.R")
    # stepped head: a stack of blocks narrowing upward, a jade inset in front
    z = top.copy()
    for w, h in ((0.07, 0.03), (0.11, 0.035), (0.075, 0.03), (0.04, 0.03)):
        V, F = M.box(w, 0.045, h, center=z + np.array([0, 0, h / 2]))
        b.add(M.bevel(P_(V, F, "BH_Wood", "step"), 0.004, 1), "hand.R")
        z = z + np.array([0, 0, h])
    V, F = M.box(0.03, 0.01, 0.026, center=top + np.array([0, -0.025, 0.048]))
    b.add(P_(V, F, "BH_Jade", "inset"), "hand.R")
