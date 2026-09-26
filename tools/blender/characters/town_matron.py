"""Townsfolk: the matron (innkeeper Pilar Abucay, net-mender Nena Lagdameo, widow Mirasol Hald).

A sturdy woman in a long working dress (BH_Cloth_Primary, tinted per NPC) with a bib apron, sleeves rolled above
the elbows, a knotted headscarf and a ring of keys on the belt.

This module also holds the SHARED TOWNSFOLK KIT (Kit, head, hands, shoes, skirts, sleeves ...) used by every other
town_<id>.py module (the registry treats every town_*.py file as a character, so the kit cannot live in its own
town_ file).
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import Body, torso_ring, torso_loft, interp_rows, front_y, back_y, smoothstep, M_align_z
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
from char_mage import zspec_w, ring_frac, normalize_rows
from char_knight import thick_band

# ================================================================================================================
# SHARED TOWNSFOLK KIT
# All torso / head geometry is authored in STANDARD units (a 1.80 m skeleton) and scaled by Kit.s when added; limb
# geometry is built from the posed skeleton landmarks (already scaled). Weight functions always get model-space
# vertices (use Kit.zw for height-blended weights).
# ================================================================================================================
TOWN_CLIPS = ["idle", "idle_look", "idle_adjust", "interact_talk", "walk", "interact_pickup"]


def pal(rgb, rough=0.85, metal=0.0):
    return (tuple(rgb), metal, rough, None, 0.0, 1.0)


# neutral palette entries shared by most townsfolk (modules update / override them)
BASE_COLORS = {
    "BH_Cloth_Primary": pal((0.30, 0.12, 0.06)),          # preview colour only: the game tints this per NPC
    "BH_Shadow": pal((0.025, 0.018, 0.014), 0.8),         # eyes / mouth (no glow)
    "BH_Leather": pal((0.13, 0.075, 0.04), 0.65),
}


class Kit:
    def __init__(self, body):
        self.b = body
        self.p = body.p
        self.s = body.p["pelvis_h"] / 0.98

    def add(self, part, bone=None, w=None, std=True):
        if std:
            part.scale(self.s)
        if w is not None:
            self.b.add(part, weights=w)
        else:
            self.b.add(part, bone)
        return part

    def addm(self, part, bone=None, w=None, std=True):
        """Add a part authored for the left side and its mirror."""
        if std:
            part.scale(self.s)
        self.b.add_mirror(part, bone, w)

    def zw(self, spec):
        return zspec_w([(z * self.s, b) for z, b in spec])

    def torso_w(self):
        return self.zw([(0.99, "hips"), (1.10, "spine"), (1.22, "spine"), (1.32, "chest")])

    def head_w(self):
        return self.zw([(1.50, "chest"), (1.54, "neck"), (1.58, "neck"), (1.61, "head")])

    def skirt_w(self, z_top=1.0, z_bot=0.55, max_leg=0.85, center_w=0.06, shin=True):
        return self.b.skirt_weights(z_top * self.s, z_bot * self.s, max_leg=max_leg,
                                    shin_from=(0.45 * self.s if shin else None), center_w=center_w)

    def hx(self):
        return self.p["hip_x"] / self.s


def P_(V, F, mat, name="part"):
    return M.Part(V, F, mat, name=name)


def outward(p):
    """Flip a closed, roughly convex part whose faces point inward (Godot culls back faces)."""
    c = p.V.mean(0)
    s = 0.0
    for f in p.F:
        a, b, cc = p.V[f[0]], p.V[f[1]], p.V[f[2]]
        s += float(np.dot(np.cross(b - a, cc - a), (a + b + cc) / 3 - c))
    return p.flip() if s < 0 else p


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- torso rows
TORSO_STD = [
    (0.90, 0.152, 0.100, 0.110, 0.00),
    (0.98, 0.150, 0.100, 0.104, 0.00),
    (1.06, 0.140, 0.098, 0.096, 0.02),
    (1.14, 0.142, 0.104, 0.096, 0.05),
    (1.25, 0.155, 0.112, 0.100, 0.08),
    (1.35, 0.166, 0.116, 0.104, 0.07),
    (1.43, 0.168, 0.110, 0.104, 0.04),
    (1.49, 0.140, 0.090, 0.092, 0.00),
    (1.53, 0.080, 0.064, 0.064, 0.00),
]


def gauss(z, c, w):
    return math.exp(-((z - c) / w) ** 2)


def torso_rows(chest=1.0, waist=1.0, hip=1.0, depth=1.0, bust=0.0, belly=0.0, hump=0.0, shoulder=1.0):
    """Body rows (z, rx, ryf, ryb, keel) in standard units. bust / belly / hump add depth (meters)."""
    out = []
    for z, rx, ryf, ryb, keel in TORSO_STD:
        fh = smoothstep(1.12, 0.98, z)            # hips region
        fw = gauss(z, 1.10, 0.07)                 # waist
        fc = smoothstep(1.12, 1.30, z)            # chest
        fs = smoothstep(1.40, 1.46, z) * (1 - smoothstep(1.49, 1.53, z))
        k = lerp(1.0, hip, float(fh)) * lerp(1.0, waist, fw) * lerp(1.0, chest, float(fc))
        k *= lerp(1.0, shoulder, float(fs))
        rx2 = rx * k + belly * 0.6 * gauss(z, 1.12, 0.13)
        ryf2 = ryf * depth + bust * gauss(z, 1.335, 0.055) + belly * gauss(z, 1.12, 0.12)
        ryb2 = ryb * depth + hump * gauss(z, 1.40, 0.08)
        out.append((z, rx2, ryf2, ryb2, keel * (0.3 if bust > 0 else 1.0)))
    return out


def grow(rows, g, zmin=-1, zmax=9):
    return [(r[0], r[1] + g, r[2] + g, r[3] + g, r[4]) + tuple(r[5:]) for r in rows if zmin <= r[0] <= zmax]


def rows_span(rows, z0, z1, n=None):
    zs = sorted(set([z0, z1] + [r[0] for r in rows if z0 < r[0] < z1]))
    if n:
        zs = sorted(set(zs + list(np.linspace(z0, z1, n))))
    return [interp_rows(rows, z) for z in zs]


def body_shell(k, rows, z0, z1, mat, g=0.0, n=24, cap0=False, cap1=False, name="shell", w=None, solid=0.0):
    """Closed torso-hugging garment between z0 and z1 (standard units)."""
    V, F = torso_loft(grow(rows_span(rows, z0, z1), g), n=n, cap0=cap0, cap1=cap1)
    p = P_(V, F, mat, name)
    if solid:
        p = M.solidify(p, solid, offset=-1.0)
    return k.add(p, w=w or k.torso_w())


def band(k, rows, z0, z1, mat, g_out=0.012, g_in=0.0, n=24, bone="hips", w=None, bev=0.003):
    V, F = thick_band(rows, z0, z1, g_out, g_in, n=n)
    p = P_(V, F, mat, "band")
    if bev:
        p = M.bevel(p, bev, 1)
    return k.add(p, bone=None if w else bone, w=w)


def on_ring(rows, z, g, frac):
    """Point on the (grown) torso ring at angle fraction (0 front, 0.25 own left, 0.5 back) + outward yaw (deg)."""
    q = ring_frac(rows, z, g, [frac])[0]
    a = 2 * math.pi * frac - math.pi / 2
    return q, math.degrees(a) + 90


# ---------------------------------------------------------------- skirts / long garments
def flare_rows(z_top, z_hem, top, hem, n=7, curve=1.0, keel=0.0):
    """Rows from the waist to the hem; top/hem = (rx, ryf, ryb)."""
    rows = []
    for t in np.linspace(0, 1, n):
        z = z_top + (z_hem - z_top) * t
        f = t ** curve
        rows.append((z, lerp(top[0], hem[0], f), lerp(top[1], hem[1], f), lerp(top[2], hem[2], f), keel))
    return sorted(rows, key=lambda r: r[0])


def skirt(rows, mat, folds=9, amp=0.012, n=32, solid=0.008, p=2.2, gap=None, name="skirt"):
    """Closed (or front-split: gap = half-angle fraction) flared skirt with vertical folds growing to the hem."""
    rows = sorted(rows, key=lambda r: r[0])
    z_top, z_hem = rows[-1][0], rows[0][0]
    rings = []
    for r in rows:
        z = r[0]
        t = (z_top - z) / max(z_top - z_hem, 1e-6)
        if gap:
            fr = gap + (1 - 2 * gap) * np.linspace(0, 1, n)
        else:
            fr = np.linspace(0, 1, n, endpoint=False)
        pts = ring_frac(rows, z, 0.0, fr, p=p)
        fold = amp * t ** 1.2 * np.sin(fr * 2 * math.pi * folds)
        rad = normalize_rows(pts[:, :2])
        pts[:, 0] += rad[:, 0] * fold
        pts[:, 1] += rad[:, 1] * fold
        rings.append(pts)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=not gap)
    prt = P_(V, F, mat, name)
    if solid:
        prt = M.solidify(prt, solid, offset=-1.0)
    return prt, rings


# ---------------------------------------------------------------- head
HEAD_STD = [
    (1.588, 0.022, 0.018, 0.020, 0.0, -0.062),
    (1.600, 0.045, 0.035, 0.040, 0.0, -0.045),
    (1.625, 0.060, 0.052, 0.062, 0.05, -0.028),
    (1.655, 0.068, 0.062, 0.078, 0.05, -0.016),
    (1.690, 0.073, 0.068, 0.088, 0.02, -0.010),
    (1.722, 0.076, 0.071, 0.092, 0.08, -0.006),
    (1.760, 0.075, 0.066, 0.092, 0.00, -0.002),
    (1.795, 0.062, 0.052, 0.078, 0.00, 0.003),
    (1.818, 0.036, 0.030, 0.048, 0.00, 0.006),
]


def head_rows(jaw=1.0, width=1.0, fwd=0.0):
    out = []
    for z, rx, ryf, ryb, keel, cy in HEAD_STD:
        j = lerp(jaw, 1.0, float(smoothstep(1.60, 1.70, z)))
        out.append((z, rx * j * width, ryf * j, ryb, keel, cy + fwd))
    return out


def head(k, jaw=1.0, width=1.0, fwd=0.0, nose=1.0, brow=1.0, ears=True, neck_r=0.05, lift=0.0):
    """Skin head + neck + simple face (brow, nose, dark eyes, mouth, ears). fwd shifts the head forward (stoop).
    Returns the head rows (standard units) for hair / hats."""
    rows = head_rows(jaw, width, fwd)
    rows = [(r[0] + lift,) + tuple(r[1:]) for r in rows]
    V, F = M.tube([(0, 0.0, 1.47), (0, -0.004 + fwd * 0.5, 1.54), (0, -0.01 + fwd, 1.62 + lift)],
                  [(neck_r * 1.1, neck_r), (neck_r, neck_r * 0.96), (neck_r, neck_r)], n=12, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Skin", "neck"), w=k.head_w())
    V, F = torso_loft(rows, n=22, p=2.1, cap0=True, cap1=True)
    k.add(P_(V, F, "BH_Skin", "head"), "head")
    y0 = fwd
    zl = lift
    V, F = M.tube([(-0.05, -0.068 + y0, 1.716 + zl), (0.0, -0.079 + y0, 1.721 + zl), (0.05, -0.068 + y0, 1.716 + zl)],
                  [(0.011 * brow, 0.007 * brow)] * 3, n=6, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Skin", "brow"), "head")
    V, F = M.tube([(0, -0.076 + y0, 1.712 + zl), (0, -0.087 * nose + y0, 1.684 + zl),
                   (0, -0.094 * nose + y0, 1.662 + zl), (0, -0.086 * nose + y0, 1.652 + zl)],
                  [(0.0065, 0.006), (0.009, 0.008), (0.012 * nose, 0.009), (0.008, 0.005)], n=6, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Skin", "nose"), "head")
    for sx in (1, -1):
        V, F = M.sphere(0.0085, 8, 5, center=(sx * 0.029, -0.070 + y0, 1.699 + zl), scale=(1.25, 0.6, 0.8))
        k.add(P_(V, F, "BH_Shadow", "eye"), "head")
        if ears:
            V, F = M.sphere(0.026, 8, 6, center=(sx * 0.074 * width, 0.004 + y0, 1.688 + zl), scale=(0.35, 0.62, 1.0))
            k.add(P_(V, F, "BH_Skin", "ear"), "head")
    V, F = M.tube([(-0.02, -0.071 * jaw + y0, 1.628 + zl), (0, -0.075 * jaw + y0, 1.627 + zl),
                   (0.02, -0.071 * jaw + y0, 1.628 + zl)], [(0.004, 0.003)] * 3, n=5, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Shadow", "mouth"), "head")
    return rows


def head_shell(rows, g, line, ztop=None, nu=24, nv=6, p=2.1, top_bulge=0.008, vpow=0.9):
    """Surface hugging the head rows grown by g (float or fn(v)) from a lower edge z = line(u) up to the crown.
    u: 0 front, 0.25 own left, 0.5 back. Open at the bottom, closed at the top. Outward normals."""
    zt = ztop if ztop is not None else rows[-1][0]

    def fn(u, v):
        z0 = line(u)
        z = z0 + (zt - z0) * v ** vpow
        gg = g(v) if callable(g) else g
        return ring_frac(rows, min(z, rows[-1][0]), gg, [u], p=p)[0] + np.array([0, 0, max(0.0, z - rows[-1][0])])
    V, F = M.grid(fn, nu, nv, closed_u=True)
    top = V[-nu:]
    pole = top.mean(0) + np.array([0, 0, top_bulge])
    V = np.vstack([V, pole[None]])
    ip = len(V) - 1
    o = (nv - 1) * nu
    F = list(F) + [(o + i, o + (i + 1) % nu, ip) for i in range(nu)]
    return V, F


def hairline(front, side, back, sharp=1.0):
    """Lower-edge height as a function of u (0 front, 0.25/0.75 sides, 0.5 back)."""
    def fn(u):
        c = math.cos(2 * math.pi * u)            # 1 front, -1 back, 0 sides
        if c >= 0:
            return lerp(side, front, c ** sharp)
        return lerp(side, back, (-c) ** sharp)
    return fn


# ---------------------------------------------------------------- hands, arms
def mitten(k, side="L", mat="BH_Skin", size=1.0, curl=1.0, thumb_mat=None):
    size *= 0.9
    """Relaxed hand (fingers together, slightly curled) in hand-bone space. Author for the left (thumb +X local)."""
    b = k.b
    hb = "hand." + side
    sx = 1.0 if side == "L" else -1.0
    s = size * k.s

    def L(x, y, z):
        return b.lpt(hb, [(x * sx * s, y * s, z * s)])[0]
    spec = [(-0.012, 0.024, 0.021, 0.004), (0.02, 0.034, 0.018, 0.0), (0.06, 0.041, 0.016, -0.002),
            (0.095, 0.043, 0.014, -0.004), (0.13, 0.040, 0.012, -0.012 * curl),
            (0.16, 0.036, 0.011, -0.026 * curl), (0.178, 0.026, 0.009, -0.04 * curl), (0.186, 0.012, 0.006, -0.048 * curl)]
    rings = []
    for y, wx, tz, zc in spec:
        ring = []
        for i in range(10):
            a = 2 * math.pi * i / 10
            ring.append(L(wx * np.sign(math.cos(a)) * abs(math.cos(a)) ** 0.8,
                          y, zc + tz * np.sign(math.sin(a)) * abs(math.sin(a)) ** 0.8))
        rings.append(np.array(ring))
    if sx < 0:
        rings = [r[::-1] for r in rings]
    V, F = M.loft(rings)
    parts = [outward(P_(V, F, mat, "hand"))]
    tp = [L(0.024, 0.012, -0.006), L(0.046, 0.05, -0.02), L(0.05, 0.085, -0.032), L(0.044, 0.105, -0.04)]
    V, F = M.tube(tp, [(0.011 * s, 0.012 * s), (0.011 * s, 0.011 * s), (0.009 * s, 0.009 * s),
                       (0.007 * s, 0.007 * s)], n=6, up=b.axes(hb)[:, 2])
    parts.append(P_(V, F, thumb_mat or mat, "thumb"))
    for prt in parts:
        b.add(prt, hb)
    return parts


def sleeve(k, side, prof, mat, n=12, solid=0.0, cap1=True, name="sleeve"):
    """Tube along shoulder -> elbow -> wrist. prof: list of (t, rx, ry) with t in [-0.1 .. 2]: 0..1 upper arm,
    1..2 forearm (fraction of each segment)."""
    b = k.b
    ua, fa, ha = "upper_arm." + side, "forearm." + side, "hand." + side
    sh, el, wr = b.head(ua), b.head(fa), b.head(ha)
    hd = b.tail(ha)
    pts = []
    for t, _, _ in prof:
        if t <= 1:
            pts.append(sh + (el - sh) * t)
        elif t <= 2:
            pts.append(el + (wr - el) * (t - 1))
        else:
            pts.append(wr + (hd - wr) * (t - 2))
    V, F = M.tube(pts, [(rx * k.s, ry * k.s) for _, rx, ry in prof], n=n, up=(0, -1, 0), cap1=cap1)
    prt = P_(V, F, mat, name)
    if solid:
        prt = M.solidify(prt, solid, offset=-1.0)
    b.add(prt, weights=b.seg_weights(["shoulder." + side, ua, fa], power=9))
    return prt


SHOULDER_CAP = [(-0.2, 0.022, 0.026), (-0.13, 0.042, 0.046), (-0.05, 0.054, 0.057), (0.05, 0.057, 0.059)]


def arm_ring(k, side, t, r, h, mat, name="cuff", bone=None):
    """Short thick ring (rolled sleeve / cuff / bracelet) at arm parameter t (see sleeve)."""
    b = k.b
    ua, fa, ha = "upper_arm." + side, "forearm." + side, "hand." + side
    sh, el, wr = b.head(ua), b.head(fa), b.head(ha)
    if t <= 1:
        c, d = sh + (el - sh) * t, normalize(el - sh)
        bone = bone or ua
    else:
        c, d = el + (wr - el) * (t - 1), normalize(wr - el)
        bone = bone or fa
    s = k.s
    V, F = M.tube([c - d * h * 0.5 * s, c - d * h * 0.2 * s, c + d * h * 0.2 * s, c + d * h * 0.5 * s],
                  [(r * 0.9 * s, r * 0.9 * s), (r * s, r * s), (r * s, r * s), (r * 0.9 * s, r * 0.9 * s)],
                  n=12, up=(0, -1, 0), cap0=False, cap1=False)
    prt = M.solidify(P_(V, F, mat, name), 0.012 * s, offset=-1.0)
    b.add(prt, bone)
    return prt


def bare_arm(k, side, t0=0.95, mat="BH_Skin", r_el=0.04, r_wr=0.031, t1=2.02, n=10, r_up=0.048):
    prof = []
    if t0 < 1:
        prof.append((t0, r_up, r_up))
    prof += [(1.0, r_el, r_el * 1.02), (1.35, r_el * 1.05, r_el * 0.98), (1.75, r_wr * 1.1, r_wr), (t1, r_wr, r_wr * 0.85)]
    return sleeve(k, side, prof, mat, n=n, name="forearm")


# ---------------------------------------------------------------- legs and feet
def leg_tube(k, side, prof, mat, n=10, name="leg"):
    """prof: list of (t, rx, ry): t 0..1 thigh (hip -> knee), 1..2 shin (knee -> ankle)."""
    b = k.b
    th, sh = "thigh." + side, "shin." + side
    h, kn, a = b.head(th), b.head(sh), b.tail(sh)
    pts = [h + (kn - h) * t if t <= 1 else kn + (a - kn) * (t - 1) for t, _, _ in prof]
    V, F = M.tube(pts, [(rx * k.s, ry * k.s) for _, rx, ry in prof], n=n, up=(0, -1, 0))
    prt = P_(V, F, mat, name)
    b.add(prt, weights=b.seg_weights([th, sh], power=10))
    return prt


def trousers(k, mat, knee_r=0.052, ankle_r=0.045, t_end=1.75, seat=True, flare=0.0, n=12):
    if seat:
        V, F = torso_loft([(0.84, 0.150, 0.092, 0.10, 0.0), (0.92, 0.152, 0.098, 0.104, 0.0),
                           (1.0, 0.146, 0.096, 0.10, 0.0)], n=24)
        k.add(P_(V, F, mat, "seat"), w=k.b.skirt_weights(0.98 * k.s, 0.84 * k.s, max_leg=0.7, center_w=0.05))
    for s in "LR":
        leg_tube(k, s, [(-0.02, 0.08, 0.084), (0.4, 0.07, 0.074), (1.0, knee_r, knee_r * 1.05),
                        (1.4, knee_r * 0.95, knee_r), (t_end, ankle_r + flare, ankle_r + flare)], mat, n=n,
                 name="trouser")


def shoe_rings(hx, spec, n=12):
    R = []
    for y, w, top in spec:
        pts = []
        for i in range(n):
            ang = 2 * math.pi * i / n
            c, sn = math.cos(ang), math.sin(ang)
            x = w * np.sign(c) * abs(c) ** 0.8
            z = top / 2 + top / 2 * np.sign(sn) * abs(sn) ** 0.7
            pts.append((hx + x, y, max(z, 0.012)))
        R.append(np.array(pts))
    return R


def shoes(k, mat="BH_Leather", sole="BH_Wood", shaft=0.0, shaft_mat=None, width=1.0, shaft_r=0.048):
    """Low shoes (shaft = 0) or boots (shaft = height of the boot shaft above the ankle, standard units)."""
    hx = k.hx()
    w = width
    parts = []
    foot = shoe_rings(hx, [(0.065, 0.034 * w, 0.075), (0.045, 0.041 * w, 0.10), (0.0, 0.045 * w, 0.105),
                           (-0.06, 0.046 * w, 0.08), (-0.12, 0.045 * w, 0.06)])
    V, F = M.loft(foot[::-1])
    parts.append((outward(P_(V, F, mat, "shoe")), "foot.L"))
    toe = shoe_rings(hx, [(-0.115, 0.045 * w, 0.06), (-0.17, 0.042 * w, 0.05), (-0.205, 0.032 * w, 0.04),
                          (-0.222, 0.014 * w, 0.028)])
    V, F = M.loft(toe[::-1])
    parts.append((outward(P_(V, F, mat, "shoe_toe")), "toe.L"))
    V, F = M.box(0.09 * w, 0.2, 0.014, center=(hx, -0.03, 0.007))
    parts.append((P_(V, F, sole, "sole"), "foot.L"))
    V, F = M.box(0.074 * w, 0.095, 0.012, center=(hx, -0.175, 0.006))
    parts.append((P_(V, F, sole, "sole_t"), "toe.L"))
    for prt, bone in parts:
        k.addm(prt, bone)
    if shaft > 0:
        b = k.b
        for s in "LR":
            sh = "shin." + s
            kn, a = b.head(sh), b.tail(sh)
            L = np.linalg.norm(kn - a) / k.s
            f = min(shaft / L, 0.95)
            pts = [a + (0, 0.004, 0.02 * k.s), a + (kn - a) * (f * 0.5), a + (kn - a) * f]
            V, F = M.tube(pts, [(shaft_r * k.s, shaft_r * 1.08 * k.s)] * 3, n=12, up=(0, -1, 0))
            b.add(P_(V, F, shaft_mat or mat, "boot"), sh)


def bare_foot(k, mat="BH_Skin", sandal="BH_Leather"):
    hx = k.hx()
    foot = shoe_rings(hx, [(0.05, 0.03, 0.07), (0.03, 0.036, 0.085), (-0.02, 0.04, 0.07), (-0.08, 0.043, 0.05),
                           (-0.12, 0.044, 0.04)], n=10)
    V, F = M.loft(foot[::-1])
    k.addm(outward(P_(V, F, mat, "foot")), "foot.L")
    toe = shoe_rings(hx, [(-0.115, 0.044, 0.04), (-0.16, 0.042, 0.034), (-0.19, 0.034, 0.028), (-0.205, 0.016, 0.02)],
                     n=10)
    V, F = M.loft(toe[::-1])
    k.addm(outward(P_(V, F, mat, "toes")), "toe.L")
    if sandal:
        V, F = M.box(0.092, 0.2, 0.012, center=(hx, -0.035, 0.006))
        k.addm(P_(V, F, sandal, "sandal"), "foot.L")
        V, F = M.box(0.08, 0.09, 0.01, center=(hx, -0.18, 0.005))
        k.addm(P_(V, F, sandal, "sandal_t"), "toe.L")
        V, F = M.tube([(hx - 0.045, -0.07, 0.012), (hx, -0.085, 0.048), (hx + 0.045, -0.07, 0.012)],
                      [(0.008, 0.004)] * 3, n=6, up=(0, -1, 0.5), p=3.0)
        k.addm(P_(V, F, sandal, "strap"), "foot.L")
        V, F = M.tube([(hx - 0.044, 0.02, 0.012), (hx, 0.05, 0.075), (hx + 0.044, 0.02, 0.012)],
                      [(0.008, 0.004)] * 3, n=6, up=(0, 1, 0.5), p=3.0)
        k.addm(P_(V, F, sandal, "strap"), "foot.L")


# ---------------------------------------------------------------- small props
def rope(pts, r, mat, n=6, cap=True):
    pts = np.asarray(pts, float)
    d = normalize(pts[-1] - pts[0]) if np.linalg.norm(pts[-1] - pts[0]) > 1e-6 else np.array([1.0, 0, 0])
    up = (0, 0, 1) if abs(d[2]) < 0.9 else (0, -1, 0)
    V, F = M.tube(pts, [(r, r)] * len(pts), n=n, up=up, cap0=cap, cap1=cap)
    return P_(V, F, mat, "rope")


def ring_pts(c, r, axis, n=16, up=(0, 0, 1)):
    R = M_align_z(axis, up)
    return [np.asarray(c, float) + R @ np.array([r * math.cos(a), r * math.sin(a), 0.0])
            for a in np.linspace(0, 2 * math.pi, n + 1)]


def pouch(center, yaw, size=(0.08, 0.04, 0.08), mat="BH_Leather", flap_mat=None):
    V, F = M.box(*size)
    p = M.bevel(P_(V, F, mat, "pouch"), min(size) * 0.25, 2)
    p.rot(Rz(yaw)).move(center)
    V, F = M.box(size[0] * 1.04, size[1] * 1.12, size[2] * 0.4, center=(0, -0.002, size[2] * 0.32))
    f = M.bevel(P_(V, F, flap_mat or mat, "flap"), 0.006, 1)
    f.rot(Rz(yaw)).move(center)
    return [p, f]


def check_normals(body, tag=""):
    """Debug: print parts whose faces point inward on average (hidden in Godot, which culls back faces)."""
    for p in body.parts:
        if not len(p.F):
            continue
        c = p.V.mean(0)
        s = 0.0
        for f in p.F:
            a, b2, cc = p.V[f[0]], p.V[f[1]], p.V[f[2]]
            n = np.cross(b2 - a, cc - a)
            s += float(np.dot(n, (a + b2 + cc) / 3 - c))
        if s < 0:
            print(f"[{tag}] inward part {p.name} ({len(p.F)} faces)")


# ================================================================================================================
# MATRON
# ================================================================================================================
PROPS = proportions(0.95, shoulder_x=0.172 * 0.95, hip_x=0.097 * 0.95)
PALETTE = "town_matron"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(TOWN_CLIPS)
PALETTE_COLORS = dict(BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.20, 0.08, 0.05)),            # preview: madder red dress
    "BH_Cloth_Secondary": pal((0.62, 0.56, 0.44), 0.9),     # undyed linen apron
    "BH_Cloth_Accent": pal((0.06, 0.09, 0.17), 0.88),       # indigo headscarf
    "BH_Skin": pal((0.46, 0.27, 0.16), 0.55),
    "BH_Hair": pal((0.04, 0.025, 0.018), 0.6),
    "BH_Bronze": pal((0.50, 0.33, 0.14), 0.4, 1.0),         # keys
    "BH_Wood": pal((0.14, 0.08, 0.04), 0.8),
})

M_TORSO = torso_rows(chest=0.9, waist=0.88, hip=1.08, depth=0.98, bust=0.018, shoulder=0.93)


def build(body):
    k = Kit(body)
    rows = M_TORSO
    # ---- dress: bodice + long skirt (tinted)
    body_shell(k, rows, 0.98, 1.53, "BH_Cloth_Primary", g=0.0, n=24, cap1=True, name="bodice")
    sk_rows = flare_rows(1.07, 0.09, (0.150, 0.104, 0.110), (0.255, 0.225, 0.25), n=8, curve=0.9)
    sk, rings = skirt(sk_rows, "BH_Cloth_Primary", folds=9, amp=0.012)
    k.add(sk, w=k.skirt_w(1.02, 0.5, max_leg=0.8, center_w=0.08))
    # chemise collar peeking at the neckline (linen)
    band(k, rows, 1.485, 1.53, "BH_Cloth_Secondary", g_out=0.008, g_in=-0.004, n=24, bone="chest", bev=0.0)
    # ---- apron: waist panel + bib, ties and a waistband
    apron(k, rows, sk_rows)
    # ---- belt with keys (leather cord belt over the apron band)
    band(k, rows, 1.055, 1.08, "BH_Leather", g_out=0.02, g_in=0.008, n=24)
    q, ang = on_ring(rows, 1.065, 0.024, 0.19)
    keyring(k, q, ang)
    q, ang = on_ring(rows, 1.03, 0.03, 0.74)
    for prt in pouch(q, ang, (0.07, 0.035, 0.075)):
        k.add(prt, "hips")
    # ---- arms: sleeves rolled above the elbow, bare forearms
    for s in "LR":
        sleeve(k, s, SHOULDER_CAP + [(0.3, 0.054, 0.056), (0.72, 0.05, 0.052)], "BH_Cloth_Primary", n=12)
        arm_ring(k, s, 0.74, 0.056, 0.05, "BH_Cloth_Primary", name="rolled")
        bare_arm(k, s, t0=0.7, r_up=0.042, r_el=0.037, r_wr=0.029)
        mitten(k, s)
    # ---- legs (stockings, mostly under the skirt) + shoes
    for s in "LR":
        leg_tube(k, s, [(0.15, 0.07, 0.07), (1.0, 0.048, 0.05), (1.9, 0.037, 0.04)], "BH_Cloth_Secondary", n=8)
    shoes(k, "BH_Leather", sole="BH_Wood", width=0.92)
    # ---- head + headscarf
    hr = head(k, jaw=0.94, width=0.96, nose=0.95, brow=0.8)
    headscarf(k, hr)
    check_normals(body, "matron")


def apron(k, rows, sk_rows):
    # waist panel following the skirt front
    def fn(u, v):
        x = (u - 0.5) * 2 * (0.13 + 0.05 * v)
        z = 1.06 + (0.36 - 1.06) * v
        y = front_y(sk_rows, x, min(z, 1.06), p=2.2) - 0.012 - 0.01 * v
        y += 0.006 * math.sin(u * math.pi * 5) * v
        return (x, y, z)
    V, F = M.grid(fn, 9, 9)
    prt = M.solidify(P_(V, F, "BH_Cloth_Secondary", "apron").flip(), 0.006, offset=-1.0)
    k.add(prt, w=k.skirt_w(1.02, 0.5, max_leg=0.8, center_w=0.1))

    # bib on the chest
    def fb(u, v):
        half = 0.085 + 0.02 * v
        x = (u - 0.5) * 2 * half
        z = 1.37 + (1.07 - 1.37) * v
        return (x, front_y(rows, x, z) - 0.008, z)
    V, F = M.grid(fb, 7, 7)
    prt = M.solidify(P_(V, F, "BH_Cloth_Secondary", "bib").flip(), 0.005, offset=-1.0)
    k.add(prt, w=k.torso_w())
    # neck straps from the bib corners over the shoulders to the back
    for sx in (1, -1):
        pts = []
        for t in np.linspace(0, 1, 7):
            x = sx * lerp(0.08, 0.06, t)
            z = lerp(1.37, 1.52, t)
            pts.append((x, front_y(rows, x, z) - 0.008, z))
        pts.append((sx * 0.055, 0.0, 1.545))
        pts.append((sx * 0.06, back_y(rows, 0.06, 1.5) + 0.008, 1.5))
        k.add(rope(pts, 0.007, "BH_Cloth_Secondary"), "chest")
    # waist ties: band around the back and a bow with two tails at the back
    band(k, rows, 1.06, 1.085, "BH_Cloth_Secondary", g_out=0.014, g_in=0.004, n=24, bev=0.0)
    yb = back_y(rows, 0, 1.07) + 0.02
    for sx in (1, -1):
        V, F = M.sphere(0.028, 8, 5, center=(sx * 0.03, yb, 1.075), scale=(1.1, 0.5, 0.7))
        k.add(P_(V, F, "BH_Cloth_Secondary", "bow"), "hips")
        k.add(rope([(sx * 0.01, yb, 1.07), (sx * 0.03, yb + 0.012, 0.98), (sx * 0.045, yb + 0.02, 0.86)], 0.009,
                   "BH_Cloth_Secondary"), w=k.skirt_w(1.02, 0.6, max_leg=0.5, center_w=0.05))


def keyring(k, q, ang):
    q = np.asarray(q, float)
    c = q + np.array([0, 0, -0.055])
    ring = ring_pts(c, 0.022, Rz(ang) @ np.array([0, -1.0, 0]), n=14)
    V, F = M.tube(ring, [(0.0035, 0.0035)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Bronze", "keyring"), "hips")
    k.add(rope([q, q + np.array([0, -0.004, -0.035])], 0.004, "BH_Leather"), "hips")
    for i, (dx, L) in enumerate(((-0.014, 0.075), (0.004, 0.09), (0.018, 0.065))):
        top = c + Rz(ang) @ np.array([dx, -0.004, -0.018])
        bot = top + Rz(ang) @ np.array([dx * 0.4, -0.004, -L])
        k.add(rope([top, bot], 0.0045, "BH_Bronze"), "hips")
        V, F = M.box(0.018, 0.005, 0.012)
        bit = P_(V, F, "BH_Bronze", "bit").rot(Rz(ang)).move(bot + np.array([0, 0, 0.012]) + Rz(ang) @ np.array([0.01, 0, 0]))
        k.add(bit, "hips")
        V, F = M.sphere(0.011, 8, 4, scale=(1, 0.35, 1))
        k.add(P_(V, F, "BH_Bronze", "bow").rot(Rz(ang)).move(top + np.array([0, 0, -0.006])), "hips")


def headscarf(k, hr):
    # dark hair showing at the forehead under the scarf
    V, F = head_shell(hr, 0.006, hairline(1.745, 1.70, 1.66), nu=22, nv=4)
    k.add(P_(V, F, "BH_Hair", "hair"), "head")
    # scarf: wraps the skull from the upper forehead to the nape, over the ears
    line = hairline(1.762, 1.665, 1.60, sharp=0.8)
    V, F = head_shell(hr, lambda v: 0.018 + 0.006 * (1 - v), line, nu=26, nv=6, top_bulge=0.012)
    scarf = M.solidify(P_(V, F, "BH_Cloth_Accent", "scarf"), 0.008, offset=-1.0)
    k.add(scarf, "head")
    # rolled front edge
    edge = [ring_frac(hr, line(u), 0.024, [u])[0] for u in np.linspace(-0.3, 0.3, 13)]
    edge = [(e[0], e[1], line(u)) for e, u in zip(edge, np.linspace(-0.3, 0.3, 13))]
    k.add(rope(edge, 0.009, "BH_Cloth_Accent"), "head")
    # knot + two tails at the nape (tails blend onto the neck / chest)
    yb = back_y(hr, 0, 1.62) + 0.03
    V, F = M.sphere(0.03, 10, 6, center=(0, yb, 1.625), scale=(1.2, 0.8, 0.9))
    k.add(P_(V, F, "BH_Cloth_Accent", "knot"), "head")
    for sx in (1, -1):
        pts = [(sx * 0.012, yb + 0.005, 1.62), (sx * 0.03, yb + 0.02, 1.55), (sx * 0.042, yb + 0.03, 1.49)]
        V, F = M.tube(pts, [(0.022, 0.006), (0.026, 0.006), (0.022, 0.005)], n=6, up=(0, 1, 0), p=3.0)
        k.add(P_(V, F, "BH_Cloth_Accent", "tail"), w=k.zw([(1.50, "chest"), (1.56, "neck"), (1.60, "head")]))
    # hair bun bulge under the scarf
    V, F = M.sphere(0.045, 10, 6, center=(0, back_y(hr, 0, 1.7) + 0.006, 1.70), scale=(1.1, 0.7, 0.9))
    k.add(P_(V, F, "BH_Cloth_Accent", "bun"), "head")
