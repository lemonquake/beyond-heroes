"""Townsfolk (bh-029, Zarael): Captain Ilsa Rhondar, master of the Sunwake (the ship between Wyman and Agdao).

A weathered sea captain: a long sea-blue coat (BH_Cloth_Primary, tinted by the game) with a tall turned collar, wide
dark cuffs and two rows of brass buttons, open over a cream shirt and a red neckerchief; a wide ochre sash under a
leather belt; a short curved sword in its scabbard at the left hip; a brass spyglass in a holster at the right hip;
dark breeches and folded-top sea boots; brown hair streaked grey, tied back in a long braid; a gold hoop earring.
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

PROPS = proportions(0.97, shoulder_x=0.178 * 0.97, hip_x=0.1 * 0.97)
PALETTE = "town_ilsa"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.06, 0.11, 0.19)),              # preview: sea-blue coat (game tint 0.22,0.32,0.4)
    "BH_Cloth_Secondary": pal((0.66, 0.60, 0.48), 0.9),       # cream shirt
    "BH_Cloth_Accent": pal((0.55, 0.36, 0.10), 0.85),         # ochre sash
    "BH_Cloth_Red": pal((0.42, 0.06, 0.05), 0.85),            # neckerchief
    "BH_Cloth_Dark": pal((0.06, 0.055, 0.06), 0.9),           # breeches, cuffs, collar facing
    "BH_Gold": pal((0.74, 0.54, 0.22), 0.32, 1.0),            # buttons, earring, spyglass brass
    "BH_Steel": pal((0.5, 0.5, 0.52), 0.35, 1.0),
    "BH_Leather": pal((0.12, 0.07, 0.04), 0.6),
    "BH_Skin": pal((0.48, 0.30, 0.20), 0.6),                  # sun-browned, freckled
    "BH_Hair": pal((0.16, 0.09, 0.05), 0.6),                  # brown
    "BH_HairGrey": pal((0.52, 0.5, 0.47), 0.7),               # grey streaks
    "BH_Wood": pal((0.1, 0.06, 0.035), 0.7),
})

I_TORSO = K.torso_rows(chest=0.96, waist=0.92, hip=1.04, depth=1.0, bust=0.014, shoulder=0.97)
COAT_G = 0.018


def build(body):
    k = Kit(body)
    rows = I_TORSO
    # ---- shirt + neckerchief
    K.body_shell(k, rows, 0.98, 1.53, "BH_Cloth_Secondary", n=24, cap1=True, name="shirt")
    neckerchief(k, rows)
    # ---- coat
    coat(k, rows)
    # ---- sash + belt, sword, spyglass
    K.band(k, rows, 1.0, 1.1, "BH_Cloth_Accent", g_out=COAT_G + 0.012, g_in=COAT_G - 0.002, n=26, bev=0.0)
    K.band(k, rows, 1.035, 1.065, "BH_Leather", g_out=COAT_G + 0.022, g_in=COAT_G + 0.01, n=26, bev=0.0)
    by = front_y(rows, 0, 1.05) - COAT_G - 0.026
    V, F = M.box(0.05, 0.012, 0.04, center=(0, by, 1.05))
    k.add(M.bevel(P_(V, F, "BH_Gold", "buckle"), 0.004, 1), "hips")
    q, ang = K.on_ring(rows, 1.03, COAT_G + 0.02, 0.62)          # sash knot + tails at the right-back hip
    q = np.asarray(q)
    V, F = M.sphere(0.03, 8, 6, center=q, scale=(1.0, 0.8, 1.0))
    k.add(P_(V, F, "BH_Cloth_Accent", "sash_knot"), "hips")
    for dx, L in ((-0.012, 0.24), (0.014, 0.19)):
        V, F = M.tube([q + (dx, 0.01, -0.01), q + (dx * 1.5, 0.02, -L)], [(0.026, 0.006), (0.03, 0.006)], n=6,
                      up=(1, 0, 0), p=3.0)
        k.add(P_(V, F, "BH_Cloth_Accent", "sash_tail"), w=k.skirt_w(1.02, 0.7, max_leg=0.4))
    sword(k)
    spyglass(k, rows)
    # ---- breeches + folded sea boots
    K.trousers(k, "BH_Cloth_Dark", knee_r=0.05, ankle_r=0.042, t_end=1.6, n=10)
    K.shoes(k, "BH_Leather", sole="BH_Wood", shaft=0.34, shaft_r=0.05, width=0.95)
    for s in "LR":
        b = k.b
        kn, a = b.head("shin." + s), b.tail("shin." + s)
        c = kn + (a - kn) * 0.16
        V, F = M.tube([c - (0, 0, 0.05), c + (0, 0, 0.02)], [(0.06, 0.066), (0.066, 0.072)], n=12, up=(0, -1, 0),
                      cap0=False, cap1=False)
        b.add(M.solidify(P_(V, F, "BH_Leather", "boot_fold"), 0.007, offset=-1.0), "shin." + s)
    # ---- head
    hr = K.head(k, jaw=0.95, width=0.96, nose=1.0, brow=0.85)
    hair(k, hr)
    K.check_normals(body, "ilsa")


def neckerchief(k, rows):
    ring = []
    for a in np.linspace(0, 2 * math.pi, 17):
        ring.append((0.066 * math.sin(a), -0.004 - 0.062 * math.cos(a), 1.535 + 0.008 * math.cos(a)))
    V, F = M.tube(ring, [(0.022, 0.016)] * len(ring), n=6, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Cloth_Red", "kerchief"), w=k.zw([(1.5, "chest"), (1.57, "neck")]))
    # the point hanging down the chest inside the coat opening
    y0 = front_y(rows, 0, 1.46) - 0.012
    V = np.array([(-0.05, y0 + 0.004, 1.51), (0.05, y0 + 0.004, 1.51), (0.0, y0, 1.38)])
    p = M.solidify(P_(V, [(0, 2, 1)], "BH_Cloth_Red", "kerchief_pt"), 0.006, offset=0.0)
    k.add(p, "chest")
    V, F = M.sphere(0.018, 8, 5, center=(0, y0 - 0.006, 1.5), scale=(1.1, 0.7, 0.9))
    k.add(P_(V, F, "BH_Cloth_Red", "kerchief_knot"), "chest")


def coat(k, rows):
    zs = [0.98, 1.06, 1.14, 1.22, 1.30, 1.37, 1.43, 1.475, 1.51, 1.535]
    nu = 26
    rings = []
    for z in zs:
        t = (z - 0.98) / 0.555
        a0 = 0.05 + 0.085 * t ** 1.3
        fr = a0 + (1 - 2 * a0) * np.linspace(0, 1, nu)
        rings.append(ring_frac(rows, z, COAT_G, fr))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Primary", "coat"), 0.008, offset=1.0), w=k.torso_w())
    # tall turned collar: flared band rising behind the neck, dark facing
    top = rings[-1]
    c_in, c_out = [], []
    for p in top:
        out = normalize(np.array([p[0], p[1] - 0.01, 0.0]))
        c_in.append(p + (0, 0, 0.0))
        c_out.append(p + out * 0.03 + np.array([0, 0, 0.075]))
    V, F = M.loft([np.array(c_in), np.array(c_out)], cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Primary", "collar").flip(), 0.008, offset=1.0),
          w=k.zw([(1.5, "chest"), (1.6, "neck")]))
    V, F = M.tube(c_out, [(0.006, 0.006)] * len(c_out), n=5, up=(0, 0, 1))
    k.add(P_(V, F, "BH_Cloth_Dark", "collar_edge"), w=k.zw([(1.5, "chest"), (1.6, "neck")]))
    # lapel facings + two rows of brass buttons
    for kk, sx in ((0, 1), (-1, -1)):
        pts = np.array([r[kk] for r in rings]) + np.array([0, -0.006, 0])
        V, F = M.tube(pts, [(0.016, 0.005)] * len(pts), n=5, up=(0, -1, 0), p=3.0)
        k.add(P_(V, F, "BH_Cloth_Dark", "lapel"), w=k.torso_w())
        for z in (1.16, 1.25, 1.34, 1.43):
            i = int(np.argmin([abs(r[kk][2] - z) for r in rings]))
            p = rings[i][kk]
            x = p[0] + sx * 0.035
            V, F = M.sphere(0.011, 8, 4, center=(x, front_y(rows, x, z) - COAT_G - 0.012, z), scale=(1, 0.5, 1))
            k.add(P_(V, F, "BH_Gold", "button"), w=k.torso_w())
    # coat skirt: split front and back vent, to mid-calf
    r0 = interp_rows(rows, 1.0)
    g = COAT_G
    sk_rows = K.flare_rows(1.0, 0.34, (r0[1] + g, r0[2] + g, r0[3] + g), (0.26, 0.22, 0.25), n=7)
    for lo, hi in ((0.06, 0.485), (0.515, 0.94)):
        fr = np.linspace(lo, hi, 12)
        rr = []
        for r in sorted(sk_rows, key=lambda r: r[0]):
            pts = ring_frac(sk_rows, r[0], 0.0, fr, p=2.2)
            t = (1.0 - r[0]) / 0.66
            fold = 0.011 * t * np.sin(fr * 2 * math.pi * 7)
            rad = K.normalize_rows(pts[:, :2])
            pts[:, 0] += rad[:, 0] * fold
            pts[:, 1] += rad[:, 1] * fold
            rr.append(pts)
        V, F = M.loft(rr, cap0=False, cap1=False, closed=False)
        w = k.skirt_w(1.0, 0.5, max_leg=0.85)
        k.add(M.solidify(P_(V, F, "BH_Cloth_Primary", "coat_skirt"), 0.008, offset=-1.0), w=w)
        hem = rr[0] + np.array([0, 0, 0.012])
        V, F = M.tube(hem, [(0.006, 0.012)] * len(hem), n=5, up=(0, 0, 1), p=3.0)
        k.add(P_(V, F, "BH_Cloth_Dark", "hem"), w=w)
    # sleeves with wide dark cuffs and a brass button on each
    for s in "LR":
        K.sleeve(k, s, K.SHOULDER_CAP + [(0.5, 0.054, 0.056), (1.0, 0.05, 0.052), (1.6, 0.046, 0.047),
                                         (1.84, 0.047, 0.047)], "BH_Cloth_Primary", n=12)
        K.arm_ring(k, s, 1.72, 0.06, 0.13, "BH_Cloth_Dark", name="cuff")
        K.mitten(k, s, size=0.98)
        b = k.b
        el, wr = b.head("forearm." + s), b.head("hand." + s)
        c = el + (wr - el) * 0.74 + np.array([0, -0.066 * k.s, 0])
        V, F = M.sphere(0.01, 8, 4, center=c, scale=(1, 0.5, 1))
        b.add(P_(V, F, "BH_Gold", "cuff_button"), "forearm." + s)


def sword(k):
    """Short curved sword in a leather scabbard at the left hip (rigid to hips), hilt forward."""
    g = np.array([0.18, -0.08, 0.99]) * k.s
    d = normalize(np.array([0.06, 0.5, -0.86]))
    side = normalize(np.cross(d, np.array([1.0, 0, 0])))
    L = 0.6 * k.s
    pts = []
    for t in np.linspace(0, 1, 6):
        pts.append(g + d * L * t + side * (-0.06 * k.s) * t ** 2)
    prof = [(0.03, 0.011)] * 4 + [(0.026, 0.01), (0.012, 0.007)]
    V, F = M.tube(pts, [(a * k.s, b * k.s) for a, b in prof], n=8, up=(1, 0, 0), p=2.6)
    k.b.add(P_(V, F, "BH_Leather", "scabbard"), "hips")
    for i, mat in ((0, "BH_Gold"), (5, "BH_Gold")):
        c = pts[i] if i == 0 else pts[-1] - d * 0.02
        V, F = M.tube([c - d * 0.012, c + d * 0.012], [(0.033 * k.s, 0.014 * k.s)] * 2, n=8, up=(1, 0, 0), p=2.6)
        k.b.add(P_(V, F, mat, "fitting"), "hips")
    # hilt: shell guard, wrapped grip, pommel
    V, F = M.sphere(0.04 * k.s, 10, 5, center=g - d * 0.01 * k.s, scale=(0.45, 1.0, 1.0))
    k.b.add(P_(V, F, "BH_Gold", "guard"), "hips")
    V, F = M.tube([g - d * 0.02 * k.s, g - d * 0.12 * k.s], [(0.013 * k.s, 0.013 * k.s)] * 2, n=8, up=(1, 0, 0))
    k.b.add(P_(V, F, "BH_Leather", "grip"), "hips")
    V, F = M.sphere(0.018 * k.s, 8, 5, center=g - d * 0.135 * k.s)
    k.b.add(P_(V, F, "BH_Gold", "pommel"), "hips")


def spyglass(k, rows):
    """Brass spyglass in a leather holster at the right hip (hanging, slightly slanted back)."""
    q, ang = K.on_ring(rows, 1.0, COAT_G + 0.03, 0.8)
    q = np.asarray(q)
    d = normalize(Rz(ang) @ np.array([0.0, 0.25, -1.0]))
    V, F = M.tube([q + d * 0.02, q + d * 0.2], [(0.026, 0.026), (0.024, 0.024)], n=10, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Leather", "holster"), "hips")
    for t0, t1, r in ((-0.06, 0.02, 0.019), (-0.12, -0.06, 0.016), (-0.165, -0.12, 0.013)):
        V, F = M.tube([q + d * t0, q + d * t1], [(r, r)] * 2, n=10, up=(0, -1, 0))
        k.add(P_(V, F, "BH_Gold", "spyglass"), "hips")
    V, F = M.tube([q - d * 0.17, q - d * 0.155], [(0.021, 0.021)] * 2, n=10, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Gold", "eyepiece"), "hips")
    k.add(rope([q + d * 0.03 + (0, 0, 0.0), q + (0, 0, 0.06)], 0.005, "BH_Leather"), "hips")


def hair(k, hr):
    line = K.hairline(1.765, 1.69, 1.625, sharp=0.8)
    V, F = K.head_shell(hr, lambda v: 0.01 + 0.004 * (1 - v), line, nu=24, nv=6, top_bulge=0.008)
    k.add(M.solidify(P_(V, F, "BH_Hair", "hair"), 0.008, offset=-1.0), "head")
    # grey streaks swept back from the temples
    for sx in (1, -1):
        pts = []
        for t in np.linspace(0, 1, 7):
            u = lerp(0.075, 0.42, t)
            uu = u if sx > 0 else 1 - u
            z = lerp(1.762, 1.70, t) + 0.028 * math.sin(math.pi * t)
            q = K.ring_frac(hr, min(z, hr[-1][0] - 0.03), 0.0135, [uu], p=2.1)[0]
            pts.append((q[0], q[1], z))
        V, F = M.tube(pts, [(0.003, 0.007)] * len(pts), n=5, up=(0, 0, 1))
        k.add(P_(V, F, "BH_HairGrey", "streak"), "head")
    # long braid from the nape down between the shoulder blades
    yb = K.back_y(hr, 0, 1.66) + 0.008
    pts = np.array([(0.0, yb, 1.67), (0.0, yb + 0.03, 1.58), (0.0, 0.15, 1.48), (0.0, 0.16, 1.38),
                    (0.0, 0.155, 1.28)])
    wf = k.zw([(1.40, "chest"), (1.52, "neck"), (1.60, "head")])
    dense, prof = [], []
    for i in range(len(pts) - 1):
        for t in np.linspace(0, 1, 5, endpoint=False):
            j = len(dense)
            c = pts[i] + (pts[i + 1] - pts[i]) * t
            dense.append(c + (0.005 * math.sin(j * math.pi / 2), 0, 0))
            r = 0.022 * (1 - 0.3 * j / (5 * len(pts)))
            lobe = 0.8 + 0.2 * abs(math.cos(j * math.pi / 3))
            prof.append((r * lobe, r * 0.75 * lobe))
    dense.append(pts[-1])
    prof.append((0.012, 0.01))
    V, F = M.tube(dense, prof, n=8, up=(0, 1, 0))
    k.add(P_(V, F, "BH_Hair", "braid"), w=wf)
    k.add(rope([pts[-1] + (0, 0, 0.012), pts[-1] - (0, 0, 0.004)], 0.017, "BH_Cloth_Red"), w=wf)
    # gold hoop earring on the right ear
    c = np.array([-0.074 * 0.96, -0.004, 1.655])
    ring = K.ring_pts(c, 0.014, (1, 0, 0), n=12)[::-1]
    V, F = M.tube(ring, [(0.0025, 0.0025)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Gold", "earring"), "head")
