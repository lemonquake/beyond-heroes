"""Ashen Cultist (Ashen Circle): ankle-length ash-grey robe with ember-orange trim, a deep hood over a cracked ceramic
ash-mask with ember eyes, a rope belt hung with cords of burnt paper prayers, the left hand wrapped and charred,
and a short ritual staff in the right hand topped with a burning brazier cage.
Robe / hood helpers here are shared with enemy_ashen_acolyte. Kit: enemy_bandit_cutthroat."""
import math
import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K

SCALE = 1.75 / 1.87          # hood peak ~1.87 standard units
PROPS = proportions(SCALE)
PALETTE = "ashen_cultist"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.16, 0.15, 0.14), 0.0, 0.92, None, 0.0, 1.0),      # ash-grey robe
    "BH_Cloth_Secondary": ((0.45, 0.12, 0.025), 0.0, 0.85, None, 0.0, 1.0),   # ember-orange trim
    "BH_Bone": ((0.55, 0.52, 0.47), 0.0, 0.45, None, 0.0, 1.0),               # ceramic ash-mask
    "BH_Horn": ((0.36, 0.3, 0.2), 0.0, 0.8, None, 0.0, 1.0),                  # prayer papers
    "BH_Ichor": ((0.035, 0.028, 0.024), 0.0, 0.8, None, 0.0, 1.0),            # charred wraps / soot
    "BH_Leather": ((0.08, 0.06, 0.045), 0.0, 0.7, None, 0.0, 1.0),            # rope, boots
    "BH_Skin": ((0.42, 0.3, 0.24), 0.0, 0.6, None, 0.0, 1.0),
    "BH_Shadow": ((0.025, 0.02, 0.02), 0.0, 0.8, None, 0.0, 1.0),             # hood interior
    "BH_Emissive": ((1.0, 0.35, 0.05), 0.0, 0.4, (1.0, 0.38, 0.06), 9.0, 1.0),  # embers
    "BH_DarkSteel": ((0.1, 0.095, 0.09), 1.0, 0.55, None, 0.0, 1.0),          # brazier iron
    "BH_Wood": ((0.07, 0.05, 0.035), 0.0, 0.75, None, 0.0, 1.0),              # scorched staff
}
CLIPS = ["cast_quick", "cast_area"]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


TORSO = K.TORSO
ROBE_G = 0.014
ROBE_W = K.zspec_w([(0.99, "hips"), (1.10, "spine"), (1.22, "spine"), (1.32, "chest")])


# ================================================================================================= robe helpers
def robe_top(sb, mat, trim=None, g=ROBE_G, z0=0.98, v_open=0.0, rows=None):
    rows = rows or TORSO
    """Upper robe (closed or with a small V at the throat) + collar trim."""
    zs = [z0, 1.06, 1.14, 1.22, 1.30, 1.37, 1.43, 1.475, 1.505]
    nu = 34
    rings = []
    for z in zs:
        t = (z - z0) / (1.505 - z0)
        a0 = 0.002 + v_open * max(0, (t - 0.6) / 0.4) ** 1.5
        fr = a0 + (1 - 2 * a0) * np.linspace(0, 1, nu)
        rings.append(K.ring_frac(rows, z, g + 0.006 * (1 - t), fr))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    sb.add(M.solidify(M.Part(V, F, mat, name="robe_top"), 0.008, offset=1.0), weights=ROBE_W)
    top = rings[-1]
    V, F = M.tube(top, [(0.013, 0.013)] * len(top), n=6, up=(0, 0, 1))
    sb.add(M.Part(V, F, trim or mat, name="collar"), "chest")
    if v_open > 0 and trim:
        for k in (0, -1):
            pts = np.array([r[k] for r in rings[4:]]) + np.array([0, -0.006, 0])
            V, F = M.tube(pts, [(0.012, 0.005)] * len(pts), n=6, up=(0, -1, 0), p=3.0)
            sb.add(M.Part(V, F, trim, name="lapel"), weights=ROBE_W)


def robe_panel_w(sb, side, back, leg_max=None):
    lm = leg_max if leg_max is not None else (0.62 if back else 0.85)
    s = sb.s

    def wfn(V):
        out = []
        for v in V:
            z = v[2]
            tl = float(smoothstep(1.02, 0.62, z)) * lm
            ts = float(smoothstep(0.56, 0.25, z)) * 0.4
            d = {"hips": 1 - tl}
            if tl > 1e-4:
                d["thigh." + side] = tl * (1 - ts)
                if ts > 1e-4:
                    d["shin." + side] = tl * ts
            out.append({k: x for k, x in d.items() if x > 1e-4})
        return out
    return wfn


def robe_skirt(sb, mat, trim=None, z_top=1.07, z_bot=0.14, flare=0.15, folds=0.012, front_gap=0.004, ragged=0.0,
               g=ROBE_G):
    """Long robe skirt as 4 panels (front/back x L/R) so the legs can move; trim band at the hem."""
    zs = list(np.linspace(z_bot, z_top, 8))
    span = z_top - z_bot
    rows = []
    for z in zs:
        t = (z_top - z) / span
        rows.append((z, 0.15 + g + flare * t, 0.098 + g + flare * t, 0.1 + g + flare * 1.1 * t, 0.0))
    for side, sgn in (("L", 1), ("R", -1)):
        for back in (False, True):
            nu = 9
            rings = []
            for z in zs:
                t = (z_top - z) / span
                gf = front_gap + 0.006 * t
                a, b = (gf, 0.25) if not back else (0.25, 0.5 - 0.002)
                fr = np.linspace(a, b, nu)
                pts = K.ring_frac(rows, z, 0.0, fr, p=2.2)
                ang = np.linspace(0, 1, nu)
                fold = folds * t ** 1.3 * np.sin(ang * math.pi * 3 + (0.6 if back else 0.0))
                rad = K.norm_rows(pts[:, :2])
                pts[:, 0] += rad[:, 0] * fold
                pts[:, 1] += rad[:, 1] * fold
                if ragged and t > 0.99:
                    pts[:, 2] += ragged * (0.5 + 0.5 * np.sin(ang * 17 + (3 if back else 0) + sgn))
                if sgn < 0:
                    pts[:, 0] *= -1
                rings.append(pts)
            if sgn < 0:
                rings = [r[::-1] for r in rings]
            V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
            w = robe_panel_w(sb, side, back)
            sb.add(M.solidify(M.Part(V, F, mat, name="robe_panel"), 0.008, offset=1.0), weights=w)
            if trim:
                hem = rings[0] + np.array([0, 0, 0.02])
                hem[:, :2] += K.norm_rows(hem[:, :2]) * 0.009
                V, F = M.tube(hem, [(0.007, 0.02)] * len(hem), n=6, up=(0, 0, 1), p=3.0)
                sb.add(M.Part(V, F, trim, name="hem"), weights=w)


def bell_sleeve(sb, s, mat, trim=None, cuff_r=0.085, end=0.72, bone_hand=True):
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    sx = 1 if s == "L" else -1
    pts = [sh + (-0.04 * sx, 0, 0.025), sh, sh + (el - sh) * 0.5, el, el + (wr - el) * 0.4, el + (wr - el) * end]
    prof = [(0.052, 0.056), (0.066, 0.068), (0.062, 0.064), (0.06, 0.062), (0.068, 0.07), (cuff_r, cuff_r)]
    V, F = M.tube(pts, prof, n=14, up=(0, -1, 0), cap1=False)
    sb.add(M.solidify(M.Part(V, F, mat, name="sleeve"), 0.007, offset=-1.0),
           weights=sb.seg(["chest", "shoulder." + s, ua, fa, ha], power=9))
    c = el + (wr - el) * end
    d = normalize(wr - el)
    if trim:
        V, F = M.tube([c - d * 0.022, c + d * 0.002], [(cuff_r + 0.004, cuff_r + 0.004)] * 2, n=14, up=(0, -1, 0))
        sb.add(M.Part(V, F, trim, name="sleeve_trim"), fa)
    # forearm under the bell
    V, F = M.tube([el + (wr - el) * 0.4, wr], [(0.042, 0.044), (0.035, 0.037)], n=10, up=(0, -1, 0))
    sb.add(M.Part(V, F, mat, name="underarm"), fa)


# deep hood: z, rx, ry_front, ry_back, cy, opening half-angle (deg)
HOOD_DEEP = [
    (1.500, 0.155, 0.13, 0.145, 0.015, 30),
    (1.555, 0.125, 0.125, 0.132, 0.0, 40),
    (1.620, 0.115, 0.13, 0.13, -0.012, 44),
    (1.680, 0.116, 0.135, 0.132, -0.02, 44),
    (1.740, 0.112, 0.135, 0.132, -0.018, 40),
    (1.790, 0.098, 0.125, 0.125, -0.005, 30),
    (1.830, 0.072, 0.095, 0.11, 0.015, 16),
    (1.862, 0.036, 0.05, 0.08, 0.04, 6),
    (1.885, 0.006, 0.006, 0.024, 0.09, 2),
]
HOOD_W = K.zspec_w([(1.49, "chest"), (1.54, "neck"), (1.57, "neck"), (1.62, "head")])


def hood(sb, mat, trim=None, rows=HOOD_DEEP, lining="BH_Shadow"):
    nu = 22
    rings = []
    for (z, rx, ryf, ryb, cy, th) in rows:
        ring = []
        for u in np.linspace(0, 1, nu):
            a = math.radians(th + (360 - 2 * th) * u)
            sa, ca = math.sin(a), math.cos(a)
            ring.append((rx * sa, cy - (ryf if ca > 0 else ryb) * ca, z))
        rings.append(np.array(ring))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    sb.add(M.solidify(M.Part(V, F, mat, name="hood"), 0.012, offset=-1.0), weights=HOOD_W)
    if trim:
        edge = [r[0] for r in rings] + [r[-1] for r in rings[::-1]]
        V, F = M.tube(np.array(edge), [(0.009, 0.009)] * len(edge), n=6, up=(0, 0, 1))
        sb.add(M.Part(V, F, trim, name="hood_trim"), weights=HOOD_W)
    inner = []
    for (z, rx, ryf, ryb, cy, th) in rows[1:6]:
        ring = []
        for u in np.linspace(0, 1, nu):
            a = math.radians(th + (360 - 2 * th) * u)
            ring.append((rx * 0.9 * math.sin(a), cy - (ryf if math.cos(a) > 0 else ryb) * 0.9 * math.cos(a), z))
        inner.append(np.array(ring))
    V, F = M.loft(inner, cap0=False, cap1=False, closed=False)
    sb.add(M.Part(V, F, lining, name="hood_lining").flip(), weights=HOOD_W)


def rope_belt(sb, z=1.02, g=ROBE_G + 0.012, mat="BH_Leather", knot_frac=0.1, tails=0.28, rows=None):
    rows = rows or TORSO
    ring = K.ring_frac(rows, z, g, np.linspace(0, 1, 29)[:-1])
    ring = np.vstack([ring, ring[:1]])
    V, F = M.tube(ring, [(0.011, 0.011)] * len(ring), n=6, up=(0, 0, 1), cap0=False, cap1=False)
    sb.add(M.Part(V, F, mat, name="rope"), "hips")
    p, _ = K.on_ring(rows, z, g + 0.01, knot_frac)
    V, F = M.sphere(0.02, 8, 5, center=p)
    sb.add(M.Part(V, F, mat, name="knot"), "hips")
    for dx, ln in ((0.01, tails), (-0.012, tails * 0.8)):
        pts = [p + (dx, 0, -0.01), p + (dx * 2, -0.01, -ln * 0.5), p + (dx * 2.5, -0.005, -ln)]
        sb.add(K.rtube(pts, 0.008, mat, n=5), weights=sb.skirt(1.0, 0.6, max_leg=0.5, center_w=0.05))
    return p


def prayer_cord(sb, top, length, paper="BH_Horn", cord="BH_Leather", n_tags=3, weights=None, bone=None, sway=0.0):
    """A cord hanging from `top` with small paper tags (burnt prayers)."""
    top = np.asarray(top, float)
    bot = top + np.array([sway, -0.01, -length])
    V, F = M.tube([top, (top + bot) / 2 + (0, -0.006, 0), bot], [(0.004, 0.004)] * 3, n=4, up=(1, 0, 0))
    parts = [M.Part(V, F, cord, name="cord")]
    for i in range(n_tags):
        u = (i + 0.7) / n_tags
        c = top + (bot - top) * u
        V, F = M.box(0.034, 0.004, 0.06, center=(0, 0, 0))
        tag = M.Part(V, F, paper, name="paper").rot(Rz(20 * (i % 2) - 10)).move(c + (0, -0.006, -0.02))
        parts.append(tag)
        # scorched lower edge
        V, F = M.box(0.036, 0.0045, 0.012, center=(0, 0, 0))
        parts.append(M.Part(V, F, "BH_Ichor", name="scorch").rot(Rz(20 * (i % 2) - 10)).move(c + (0, -0.006, -0.048)))
    for p in parts:
        if bone:
            sb.add(p, bone)
        else:
            sb.add(p, weights=weights)


# ================================================================================================= cultist
def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="body"), weights=ROBE_W)
    robe_top(sb, "BH_Cloth_Primary", trim="BH_Cloth_Secondary")
    robe_skirt(sb, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", ragged=0.03)
    # tabard-like front stole with ember trim edges (reads as a vertical orange stripe)
    for sx in (1, -1):
        pts, ups = [], []
        for t in np.linspace(0, 1, 10):
            z = 1.49 - 1.2 * t
            x = sx * (0.07 + 0.01 * t)
            if z > 1.0:
                y = front_y(TORSO, x, z) - ROBE_G - 0.012
            else:
                y = front_y(TORSO, x, 1.0) - ROBE_G - 0.012 - 0.1 * (1.0 - z) ** 1.2
            pts.append((x, y, z))
            ups.append((0, -1, 0))
        top = [q for q in pts if q[2] >= 1.0]
        low = [q for q in pts if q[2] <= 1.05]
        sb.add(K.strip(top, 0.035, 0.006, "BH_Cloth_Secondary", ups=ups[:len(top)]), weights=ROBE_W)
        side = "L" if sx > 0 else "R"
        sb.add(K.strip(low, 0.035, 0.006, "BH_Cloth_Secondary", ups=ups[:len(low)]),
               weights=robe_panel_w(sb, side, False))
    knot = rope_belt(sb, knot_frac=0.08)
    # cords of burnt prayers from the belt (front and hips)
    for frac, ln in ((0.03, 0.26), (0.13, 0.2), (0.88, 0.3), (0.8, 0.22), (0.6, 0.25)):
        p, _ = K.on_ring(TORSO, 1.01, ROBE_G + 0.02, frac)
        prayer_cord(sb, p, ln, weights=sb.skirt(1.0, 0.6, max_leg=0.45, center_w=0.05))
    # head, mask, hood
    K.neck_and_head(sb, face=False)
    ash_mask(sb)
    hood(sb, "BH_Cloth_Primary", trim="BH_Cloth_Secondary")
    # prayers hanging from the hood edge at the chest
    for sx in (1, -1):
        prayer_cord(sb, (sx * 0.1, -0.13, 1.5), 0.16, n_tags=2, bone="chest")
    # arms
    for s in ("L", "R"):
        bell_sleeve(sb, s, "BH_Cloth_Primary", trim="BH_Cloth_Secondary")
    K.add_fist(sb, "R", "BH_Skin", "BH_Skin")
    # left hand: charred and wrapped in sooty bandages with ember cracks
    K.add_fist(sb, "L", "BH_Ichor", "BH_Ichor")
    K.wrap_band(sb, "forearm.L", "hand.L", 0.55, 1.0, 0.04, "BH_Ichor", turns=3, width=0.022, bone="forearm.L")
    A = sb.axes("weapon.L")
    o = sb.head("weapon.L")
    for x, y in ((-0.02, 0.02), (0.01, -0.02), (-0.05, -0.01)):
        V, F = M.sphere(0.006, 6, 4, center=o + A @ np.array([-x, y, 0.047]))
        sb.add(M.Part(V, F, "BH_Emissive", name="ember"), "hand.L")
    # feet: plain wrapped boots under the robe
    K.trousers(sb, "BH_Cloth_Primary", loose=0.95)
    K.boots(sb, "BH_Leather", "BH_Ichor", shaft_top=0.45, cuff=False, wraps="BH_Ichor")
    # staff
    K.add_weapon(sb, "R", brazier_staff())


def ash_mask(sb):
    """Cracked ceramic mask over the face: smooth curved plate, dark eye slits with ember pupils, black crack."""
    def fn(u, v):
        x = (u - 0.5) * 0.13
        z = 1.605 + 0.145 * v
        ax = abs(x) / 0.08
        y = -0.078 - 0.012 * (1 - ax ** 2) + 0.02 * ax ** 2.2
        y -= 0.006 * math.sin(math.pi * v)
        # narrow chin
        return (x * (0.75 + 0.25 * v ** 0.5), y, z)
    V, F = M.grid(fn, 9, 8)
    sb.add(M.solidify(M.Part(V, F, "BH_Bone", name="mask"), 0.008, offset=-1.0), "head")
    for sx in (1, -1):
        V, F = M.sphere(0.016, 8, 5, center=(sx * 0.03, -0.092, 1.7), scale=(1.3, 0.4, 0.55))
        sb.add(M.Part(V, F, "BH_Ichor", name="eyehole"), "head")
        V, F = M.sphere(0.0065, 6, 4, center=(sx * 0.03, -0.096, 1.7), scale=(1.2, 0.5, 0.8))
        sb.add(M.Part(V, F, "BH_Emissive", name="eye"), "head")
    # crack: jagged line from the brow down across the left cheek
    pts = [(0.012, -0.097, 1.75), (0.022, -0.098, 1.725), (0.012, -0.099, 1.69), (0.03, -0.096, 1.665),
           (0.022, -0.094, 1.63), (0.04, -0.088, 1.61)]
    sb.add(K.rtube(pts, 0.0028, "BH_Ichor", n=4), "head")
    # mouth slit
    V, F = M.box(0.04, 0.006, 0.005, center=(0, -0.096, 1.638))
    sb.add(M.Part(V, F, "BH_Ichor", name="mouth"), "head")
    # soot smear
    V, F = M.sphere(0.02, 6, 4, center=(-0.035, -0.093, 1.645), scale=(1.0, 0.25, 0.7))
    sb.add(M.Part(V, F, "BH_Ichor", name="soot"), "head")


def brazier_staff():
    """Short ritual staff (weapon space, +Z up the shaft) topped with an iron cage holding glowing coals."""
    parts = []
    pts, prof = [], []
    for i in range(9):
        u = i / 8
        z = -0.62 + 1.14 * u
        pts.append((0.006 * math.sin(u * 8), 0.005 * math.cos(u * 6), z))
        r = 0.019 + 0.003 * math.sin(u * 13)
        prof.append((r, r))
    V, F = M.tube(pts, prof, n=8, up=(0, -1, 0))
    parts.append(M.Part(V, F, "BH_Wood", name="shaft"))
    # cord wraps near the grip
    for z in (-0.1, 0.12):
        V, F = M.lathe([(0, z - 0.02), (0.023, z - 0.02), (0.024, z), (0.023, z + 0.02), (0, z + 0.02)], 8)
        parts.append(M.Part(V, F, "BH_Leather", name="wrap"))
    # collar + cage
    V, F = M.lathe([(0, 0.5), (0.026, 0.5), (0.05, 0.54), (0.055, 0.56), (0.0, 0.56)], 10)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="bowl"))
    for k in range(6):
        a = math.radians(60 * k)
        bar = []
        for i in range(6):
            u = i / 5
            r = 0.052 + 0.03 * math.sin(math.pi * u)
            bar.append((r * math.cos(a), r * math.sin(a), 0.55 + 0.19 * u))
        V, F = M.tube(bar, [(0.0065, 0.0065)] * 6, n=5, up=(0, 0, 1))
        parts.append(M.Part(V, F, "BH_DarkSteel", name="bar"))
    V, F = M.lathe([(0.045, 0.735), (0.05, 0.745), (0.035, 0.755), (0.0, 0.76)], 10)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="cap"))
    for z in (0.62, 0.68):
        r = 0.052 + 0.03 * math.sin(math.pi * (z - 0.55) / 0.19)
        V, F = M.lathe([(r, z - 0.006), (r + 0.006, z), (r, z + 0.006), (r - 0.004, z)], 12, cap=False)
        parts.append(M.Part(V, F, "BH_DarkSteel", name="hoop"))
    # glowing coals + flame tongue
    V, F = M.sphere(0.052, 8, 6, center=(0, 0, 0.605), scale=(1, 1, 0.8))
    parts.append(M.Part(V, F, "BH_Emissive", name="coals"))
    V, F = M.lathe([(0, 0.6), (0.04, 0.63), (0.03, 0.68), (0.014, 0.72), (0.0, 0.76)], 7)
    parts.append(M.Part(V, F, "BH_Emissive", name="flame").rot(Rz(15)))
    # iron butt spike
    V, F = M.lathe([(0.0, -0.7), (0.012, -0.66), (0.021, -0.62), (0.0, -0.61)], 8)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="butt"))
    # paper prayers tied under the cage
    for k in range(3):
        a = math.radians(120 * k + 20)
        c = np.array([0.035 * math.cos(a), 0.035 * math.sin(a), 0.44])
        V, F = M.box(0.03, 0.004, 0.07)
        parts.append(M.Part(V, F, "BH_Horn", name="paper").rot(Rz(120 * k + 110)).move(c))
    return parts
