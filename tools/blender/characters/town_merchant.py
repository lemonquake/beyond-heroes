"""Townsfolk: the merchant (provisioner Tovin; scribe Lio Sanvar with a younger tint).

A portly trader: a long sleeveless over-vest split at the front (BH_Cloth_Primary, tinted) over a linen shirt with
full sleeves, a wide wrapped sash around the belly, dark trousers and shoes, a soft rolled cap, a round face with a
moustache, a coin purse and a ledger hanging at the belt.
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

PROPS = proportions(0.97, shoulder_x=0.19 * 0.97, hip_x=0.106 * 0.97)
PALETTE = "town_merchant"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.05, 0.12, 0.10)),              # preview: deep teal over-vest
    "BH_Cloth_Secondary": pal((0.58, 0.52, 0.40), 0.9),       # linen shirt
    "BH_Cloth_Accent": pal((0.34, 0.07, 0.04), 0.85),         # red sash, cap
    "BH_Cloth_Dark": pal((0.07, 0.055, 0.045), 0.9),          # trousers
    "BH_Skin": pal((0.52, 0.32, 0.20), 0.55),
    "BH_Hair": pal((0.06, 0.04, 0.03), 0.6),
    "BH_Gold": pal((0.70, 0.50, 0.20), 0.35, 1.0),            # coins, buttons
    "BH_Bone": pal((0.66, 0.60, 0.46), 0.8),                  # ledger pages
    "BH_Wood": pal((0.12, 0.07, 0.035), 0.8),
})

ME_TORSO = K.torso_rows(chest=1.08, waist=1.2, hip=1.12, depth=1.05, belly=0.11)


def build(body):
    k = Kit(body)
    rows = ME_TORSO
    # ---- shirt torso (mostly under the vest) + full sleeves with cuffs
    K.body_shell(k, rows, 0.95, 1.53, "BH_Cloth_Secondary", n=24, cap1=True, name="shirt")
    for s in "LR":
        K.sleeve(k, s, K.SHOULDER_CAP + [(0.5, 0.06, 0.062), (1.0, 0.06, 0.062), (1.55, 0.062, 0.062),
                                         (1.85, 0.05, 0.05)], "BH_Cloth_Secondary", n=12)
        K.arm_ring(k, s, 1.88, 0.043, 0.04, "BH_Cloth_Secondary", name="cuff")
        K.mitten(k, s, size=1.02)
    # ---- over-vest: open-front torso + long split skirt
    vest(k, rows)
    # ---- sash around the belly with a hanging knot end
    K.band(k, rows, 1.04, 1.13, "BH_Cloth_Accent", g_out=0.03, g_in=0.012, n=26, bev=0.0)
    q, ang = K.on_ring(rows, 1.08, 0.035, 0.12)
    q = np.asarray(q)
    V, F = M.sphere(0.03, 8, 6, center=q, scale=(1.1, 0.8, 1.0))
    k.add(P_(V, F, "BH_Cloth_Accent", "sash_knot"), "hips")
    for dx, L in ((0.0, 0.26), (0.03, 0.2)):
        V, F = M.tube([q + (dx, -0.005, -0.01), q + (dx + 0.01, -0.02, -L * 0.5), q + (dx + 0.015, -0.03, -L)],
                      [(0.028, 0.006), (0.032, 0.006), (0.034, 0.006)], n=6, up=(0, -1, 0), p=3.0)
        k.add(P_(V, F, "BH_Cloth_Accent", "sash_end"), w=k.skirt_w(1.05, 0.7, max_leg=0.5))
    # ---- trousers + shoes
    K.trousers(k, "BH_Cloth_Dark", knee_r=0.058, ankle_r=0.05, t_end=1.8)
    K.shoes(k, "BH_Leather", sole="BH_Wood", width=1.04)
    # ---- purse (right front) and ledger (left hip)
    purse(k, rows)
    ledger(k, rows)
    # ---- head: round face, moustache, rolled cap
    hr = K.head(k, jaw=1.1, width=1.07, nose=1.1, brow=1.0, neck_r=0.06)
    V, F = M.sphere(0.05, 10, 6, center=(0, -0.045, 1.60), scale=(1.2, 0.8, 0.55))
    k.add(P_(V, F, "BH_Skin", "chin"), w=k.zw([(1.55, "neck"), (1.6, "head")]))
    V, F = M.tube([(-0.04, -0.082, 1.64), (-0.014, -0.093, 1.651), (0.014, -0.093, 1.651), (0.04, -0.082, 1.64)],
                  [(0.007, 0.006), (0.009, 0.008), (0.009, 0.008), (0.007, 0.006)], n=6, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Hair", "moustache"), "head")
    line = K.hairline(1.74, 1.68, 1.63)
    V, F = K.head_shell(hr, 0.007, line, nu=24, nv=4)
    k.add(M.solidify(P_(V, F, "BH_Hair", "hair"), 0.006, offset=-1.0), "head")
    cap(k, hr)
    K.check_normals(body, "merchant")


def vest(k, rows):
    zs = [1.0, 1.08, 1.16, 1.24, 1.32, 1.39, 1.45, 1.49, 1.52]
    nu = 32
    rings = []
    for z in zs:
        t = (z - 1.0) / 0.52
        a0 = 0.035 + 0.075 * t ** 1.4
        fr = a0 + (1 - 2 * a0) * np.linspace(0, 1, nu)
        rings.append(ring_frac(rows, z, 0.014, fr))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Primary", "vest"), 0.008, offset=1.0), w=k.torso_w())
    for kk in (0, -1):
        edge = np.array([r[kk] for r in rings]) + np.array([0, -0.004, 0])
        V, F = M.tube(edge, [(0.01, 0.006)] * len(edge), n=6, up=(0, -1, 0))
        k.add(P_(V, F, "BH_Cloth_Primary", "vest_edge"), w=k.torso_w())
    # long split skirt of the vest (front gap) from the waist to below the knee
    r0 = interp_rows(rows, 1.0)
    sk_rows = K.flare_rows(1.02, 0.5, (r0[1] + 0.016, r0[2] + 0.016, r0[3] + 0.016), (0.25, 0.2, 0.22), n=6)
    sk, rings2 = K.skirt(sk_rows, "BH_Cloth_Primary", folds=6, amp=0.01, n=28, gap=0.06)
    k.add(sk, w=k.skirt_w(1.0, 0.55, max_leg=0.85))
    # buttons on the shirt front showing in the opening
    for z in (1.2, 1.28, 1.36, 1.44):
        V, F = M.sphere(0.009, 6, 4, center=(0, front_y(rows, 0, z) - 0.006, z), scale=(1, 0.5, 1))
        k.add(P_(V, F, "BH_Gold", "button"), w=k.torso_w())


def purse(k, rows):
    q, ang = K.on_ring(rows, 1.02, 0.04, 0.86)
    q = np.asarray(q) + (0, 0, -0.07)
    V, F = M.lathe([(0, -0.055), (0.03, -0.05), (0.045, -0.025), (0.042, 0.005), (0.022, 0.03), (0.018, 0.04),
                    (0.028, 0.055), (0, 0.058)], 10)
    k.add(K.outward(P_(V, F, "BH_Leather", "purse").move(q)), "hips")
    V, F = M.tube([q + (0, 0, 0.03), q + (0, 0, 0.036)], [(0.022, 0.022)] * 2, n=10, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Gold", "drawstring"), "hips")
    k.add(rope([q + (0, 0, 0.055), q + (0, 0, 0.1)], 0.004, "BH_Leather"), "hips")
    # a couple of coins peeking out of the belt
    for dx in (-0.02, 0.0):
        V, F = M.lathe([(0, -0.002), (0.012, -0.002), (0.012, 0.002), (0, 0.002)], 10)
        k.add(P_(V, F, "BH_Gold", "coin").rot(Rx(80)).rot(Rz(ang)).move(q + Rz(ang) @ np.array([dx, -0.03, 0.09])),
              "hips")


def ledger(k, rows):
    q, ang = K.on_ring(rows, 1.0, 0.05, 0.24)
    q = np.asarray(q) + (0, 0, -0.06)
    V, F = M.box(0.13, 0.04, 0.17)
    k.add(M.bevel(P_(V, F, "BH_Leather", "ledger"), 0.008, 1).rot(Rz(ang)).move(q), "hips")
    V, F = M.box(0.118, 0.046, 0.156, center=(0.006, 0, 0))
    k.add(P_(V, F, "BH_Bone", "pages").rot(Rz(ang)).move(q), "hips")
    V, F = M.box(0.02, 0.05, 0.176, center=(-0.03, 0, 0))
    k.add(P_(V, F, "BH_Cloth_Accent", "ledger_strap").rot(Rz(ang)).move(q), "hips")
    k.add(rope([q + (0, 0, 0.085), q + (0, 0, 0.13)], 0.005, "BH_Leather"), "hips")


def cap(k, hr):
    # soft cap: a puffy crown over the skull + a thick rolled brim around the head
    line = K.hairline(1.755, 1.73, 1.70)
    V, F = K.head_shell(hr, lambda v: 0.02 + 0.03 * math.sin(math.pi * min(v, 0.999) * 0.8), line, nu=24, nv=6,
                        top_bulge=0.03)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Accent", "cap"), 0.008, offset=-1.0), "head")
    ring = []
    for u in np.linspace(0, 1, 25):
        z = line(u)
        ring.append(ring_frac(hr, z, 0.022, [u], p=2.1)[0])
    V, F = M.tube(ring, [(0.017, 0.017)] * len(ring), n=8, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Cloth_Accent", "cap_roll"), "head")
