"""Townsfolk: the smith (Brannoc, quartermaster Dax Mercado).

Broad and heavy-armed: bald head with a thick beard, a short-sleeved work shirt (BH_Cloth_Primary, tinted per NPC)
rolled over the biceps and matching work trousers (same tinted cloth), bare forearms, a heavy leather apron from the chest to the knees, leather work gloves, a wide
belt with a hammer (right hip) and tongs (left hip), trousers and work boots.
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import front_y, back_y, interp_rows, torso_loft
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import town_matron as K
from town_matron import Kit, P_, pal, rope, lerp

PROPS = proportions(1.0, shoulder_x=0.205, hip_x=0.105)
PALETTE = "town_smith"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.16, 0.20, 0.24)),             # preview: faded blue-grey shirt
    "BH_Leather": pal((0.16, 0.085, 0.04), 0.6),             # apron, gloves, belt
    "BH_Skin": pal((0.40, 0.22, 0.13), 0.5),
    "BH_Hair": pal((0.05, 0.03, 0.02), 0.6),
    "BH_DarkSteel": pal((0.10, 0.10, 0.11), 0.5, 1.0),       # hammer head / tongs
    "BH_Steel": pal((0.42, 0.42, 0.43), 0.4, 1.0),           # buckles, rivets
    "BH_Wood": pal((0.20, 0.12, 0.06), 0.7),                 # handles, soles
})

S_TORSO = K.torso_rows(chest=1.12, waist=1.08, hip=1.04, depth=1.1, belly=0.02, shoulder=1.1)


def build(body):
    k = Kit(body)
    rows = S_TORSO
    # ---- shirt (tinted): torso + short sleeves
    K.body_shell(k, rows, 0.94, 1.53, "BH_Cloth_Primary", n=26, cap1=True, name="shirt")
    # open collar: a skin V at the throat
    def fv(u, v):
        x = (u - 0.5) * 2 * 0.045 * (1 - v)
        z = 1.53 - 0.11 * v
        return (x, front_y(rows, x, z) - 0.003, z)
    V, F = M.grid(fv, 5, 5)
    k.add(P_(V, F, "BH_Skin", "throat").flip(), w=k.torso_w())
    for s in "LR":
        K.sleeve(k, s, [(-0.2, 0.026, 0.03), (-0.13, 0.05, 0.054), (-0.05, 0.064, 0.066), (0.05, 0.068, 0.07),
                        (0.35, 0.066, 0.066)], "BH_Cloth_Primary", n=12)
        K.arm_ring(k, s, 0.4, 0.068, 0.06, "BH_Cloth_Primary", name="rolled")
        # muscular bare arm: biceps -> forearm -> wrist
        K.sleeve(k, s, [(0.35, 0.062, 0.064), (0.6, 0.063, 0.066), (0.95, 0.05, 0.05), (1.25, 0.057, 0.052),
                        (1.6, 0.046, 0.04), (1.82, 0.037, 0.032)], "BH_Skin", n=12, name="arm")
        glove(k, s)
    # ---- trousers + boots
    K.trousers(k, "BH_Cloth_Primary", knee_r=0.058, ankle_r=0.05, t_end=1.8)
    K.shoes(k, "BH_Leather", sole="BH_Wood", shaft=0.13, shaft_r=0.054, width=1.06)
    # ---- heavy leather apron
    apron(k, rows)
    # ---- belt with tools
    K.band(k, rows, 1.02, 1.085, "BH_Leather", g_out=0.03, g_in=0.012, n=26)
    by = front_y(rows, 0, 1.052) - 0.034
    V, F = M.box(0.07, 0.014, 0.058, center=(0, by, 1.052))
    k.add(M.bevel(P_(V, F, "BH_Steel", "buckle"), 0.006, 1), "hips")
    hammer(k, rows)
    tongs(k, rows)
    q, ang = K.on_ring(rows, 1.0, 0.04, 0.42)
    for prt in K.pouch(q, ang, (0.09, 0.045, 0.08)):
        k.add(prt, "hips")
    # ---- head: bald, heavy brow, thick beard
    hr = K.head(k, jaw=1.08, width=1.03, nose=1.08, brow=1.4, neck_r=0.06)
    beard(k, hr)
    K.check_normals(body, "smith")


def glove(k, s):
    b = k.b
    K.mitten(k, s, mat="BH_Leather", size=1.08)
    # flared gauntlet cuff over the wrist
    fa, ha = "forearm." + s, "hand." + s
    el, wr = b.head(fa), b.head(ha)
    d = normalize(wr - el)
    pts = [wr - d * 0.07, wr - d * 0.02, wr + d * 0.02]
    V, F = M.tube(pts, [(0.05, 0.052), (0.046, 0.048), (0.04, 0.042)], n=12, up=(0, -1, 0), cap0=False, cap1=False)
    b.add(M.solidify(P_(V, F, "BH_Leather", "cuff"), 0.005, offset=1.0), fa)


def apron(k, rows):
    z_top, z_bot = 1.42, 0.50

    def fn(u, v):
        z = lerp(z_top, z_bot, v)
        half = 0.12 + 0.105 * min(1.0, v * 1.8)
        x = (u - 0.5) * 2 * half
        if z > 1.0:
            y = front_y(rows, x * 0.95, z) - 0.012
        else:
            y = front_y(rows, x * 0.95, 1.0) - 0.012 - 0.03 * (1.0 - z)
        # wrap the edges around the flanks a little
        y += 0.05 * abs(u - 0.5) ** 2 * min(1.0, v * 2)
        return (x, y, z)
    V, F = M.grid(fn, 11, 13)
    ap = M.solidify(P_(V, F, "BH_Leather", "apron").flip(), 0.009, offset=-1.0, bevel_w=0.002)

    def aw(V):
        top = k.torso_w()(V)
        low = k.skirt_w(1.02, 0.55, max_leg=0.6, center_w=0.12)(V)
        out = []
        for v, a, b in zip(V, top, low):
            t = float(K.smoothstep(1.06 * k.s, 0.98 * k.s, v[2]))
            d = {}
            for kk, x in a.items():
                d[kk] = d.get(kk, 0) + x * (1 - t)
            for kk, x in b.items():
                d[kk] = d.get(kk, 0) + x * t
            out.append({kk: x for kk, x in d.items() if x > 1e-4})
        return out
    k.add(ap, w=aw)
    # neck strap and waist ties
    for sx in (1, -1):
        pts = [(sx * 0.11, front_y(rows, 0.11, 1.42) - 0.014, 1.425), (sx * 0.09, front_y(rows, 0.09, 1.5) - 0.01, 1.5),
               (sx * 0.075, -0.02, 1.545), (sx * 0.07, 0.04, 1.545), (sx * 0.07, back_y(rows, 0.07, 1.5) + 0.01, 1.5)]
        k.add(rope(pts, 0.009, "BH_Leather"), "chest")
    # rivets at the strap corners
    for sx in (1, -1):
        V, F = M.sphere(0.009, 6, 4, center=(sx * 0.11, front_y(rows, 0.11, 1.41) - 0.024, 1.41))
        k.add(P_(V, F, "BH_Steel", "rivet"), "chest")


def hammer(k, rows):
    """Hammer hanging head-up through a belt loop on the right hip."""
    q, ang = K.on_ring(rows, 1.03, 0.05, 0.80)    # right side, slightly forward
    q = np.asarray(q)
    Rt = Rz(ang)
    parts = []
    # loop
    ring = K.ring_pts(q, 0.024, (0, 0, 1), n=12)
    V, F = M.tube(ring, [(0.006, 0.01)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
    parts.append(P_(V, F, "BH_Leather", "loop"))
    # handle down from the loop
    V, F = M.tube([q + (0, 0, 0.04), q + (0, 0, -0.2)], [(0.013, 0.013), (0.015, 0.015)], n=8, up=(0, -1, 0))
    parts.append(P_(V, F, "BH_Wood", "handle"))
    # head resting on the loop, lying along the tangent of the belt
    V, F = M.box(0.12, 0.042, 0.045)
    hd = M.bevel(P_(V, F, "BH_DarkSteel", "hammer_head"), 0.006, 1)
    hd.rot(Rt).move(q + (0, 0, 0.066))
    parts.append(hd)
    for p in parts:
        k.add(p, "hips")


def tongs(k, rows):
    q, ang = K.on_ring(rows, 1.03, 0.05, 0.22)    # left hip
    q = np.asarray(q)
    Rt = Rz(ang)
    parts = []
    ring = K.ring_pts(q, 0.02, (0, 0, 1), n=12)
    V, F = M.tube(ring, [(0.006, 0.01)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
    parts.append(P_(V, F, "BH_Leather", "loop"))
    for dx in (-0.008, 0.008):
        a = q + Rt @ np.array([dx, 0, 0.05])
        b = q + Rt @ np.array([dx * 1.5, 0, -0.03])
        c = q + Rt @ np.array([dx * 2.8, 0, -0.26])
        d = q + Rt @ np.array([dx * 1.2, 0.0, -0.33])
        V, F = M.tube([a, b, c, d], [(0.006, 0.006)] * 4, n=6, up=(0, -1, 0))
        parts.append(P_(V, F, "BH_DarkSteel", "tong"))
    V, F = M.sphere(0.012, 8, 5, center=q + Rt @ np.array([0, 0, -0.03]))
    parts.append(P_(V, F, "BH_DarkSteel", "pivot"))
    for p in parts:
        k.add(p, "hips")


def beard(k, hr):
    # jaw shell: from ear to ear below the cheekbones, down under the chin
    def fn(u, v):
        uu = -0.3 + 0.6 * u
        top = lerp(1.668, 1.640, math.cos(uu * math.pi / 0.6) ** 2)
        z = lerp(1.585, top, v)
        q = K.ring_frac(hr, max(z, 1.59), 0.012, [uu], p=2.1)[0]
        q[2] = z
        return q
    V, F = M.grid(fn, 15, 5)
    k.add(M.solidify(P_(V, F, "BH_Hair", "beard_jaw"), 0.012, offset=1.0), "head")
    # hanging bulk under the chin (spade beard) down onto the upper chest
    rings = []
    for z, rx, ry, cy in ((1.655, 0.052, 0.03, -0.062), (1.62, 0.07, 0.045, -0.068), (1.585, 0.068, 0.05, -0.07),
                          (1.54, 0.056, 0.042, -0.085), (1.50, 0.036, 0.028, -0.098), (1.475, 0.012, 0.012, -0.104)):
        rings.append(np.array([(rx * math.cos(a), cy + ry * math.sin(a), z)
                               for a in np.linspace(0, 2 * math.pi, 14, endpoint=False)]))
    V, F = M.loft(rings)
    k.add(K.outward(P_(V, F, "BH_Hair", "beard")), w=k.zw([(1.52, "neck"), (1.58, "head")]))
    V, F = M.tube([(-0.045, -0.078, 1.64), (-0.02, -0.092, 1.652), (0.02, -0.092, 1.652), (0.045, -0.078, 1.64)],
                  [(0.008, 0.008), (0.011, 0.01), (0.011, 0.01), (0.008, 0.008)], n=6, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Hair", "moustache"), "head")
    # short fringe of hair around the back of the skull (bald on top)
    line = K.hairline(1.69, 1.655, 1.62)
    rings = []
    for v in (0.0, 1.0):
        ring = []
        for u in np.linspace(0.22, 0.78, 13):
            z = line(u) + 0.04 * v
            ring.append(K.ring_frac(hr, z, 0.004 + 0.004 * (1 - v), [u], p=2.1)[0])
        rings.append(np.array(ring))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Hair", "fringe"), 0.006, offset=1.0), "head")
