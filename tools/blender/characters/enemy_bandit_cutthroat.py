"""Bandit Cutthroat (bandits): road bandit in a patched, sleeveless leather jerkin over a dark shirt, faded red scarf
pulled over the lower face, a bandolier of throwing knives across the chest, bandaged bare forearms, a curved knife in
the right hand and a short dagger in the left.

Also holds the small shared kit used by Builder B's other enemy modules (ashen_cultist, ashen_acolyte, ghoul_brute,
shade_stalker, bandit_marksman): `SB` authors parts in the STANDARD 1.8 m space and scales them to the character,
plus head / arms / legs / boots / weapon-socket helpers.
"""
import math
import numpy as np

import bh_mesh as M
import bh_weapons as WP
from bh_body import torso_loft, torso_ring, interp_rows, front_y, back_y, dome, fist, smoothstep, M_align_z
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions

SCALE = 1.75 / 1.818
PROPS = proportions(SCALE)
PALETTE = "bandit_cutthroat"
PALETTE_COLORS = {
    "BH_Leather": ((0.105, 0.06, 0.034), 0.0, 0.66, None, 0.0, 1.0),          # jerkin
    "BH_Horn": ((0.21, 0.135, 0.075), 0.0, 0.7, None, 0.0, 1.0),              # lighter leather patches / straps
    "BH_Cloth_Primary": ((0.33, 0.055, 0.04), 0.0, 0.9, None, 0.0, 1.0),      # faded red scarf
    "BH_Cloth_Secondary": ((0.075, 0.07, 0.06), 0.0, 0.92, None, 0.0, 1.0),   # trousers / shirt
    "BH_Skin": ((0.47, 0.31, 0.22), 0.0, 0.55, None, 0.0, 1.0),
    "BH_Hair": ((0.035, 0.026, 0.02), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Bone": ((0.42, 0.37, 0.29), 0.0, 0.85, None, 0.0, 1.0),               # bandages
    "BH_Shadow": ((0.03, 0.024, 0.02), 0.0, 0.8, None, 0.0, 1.0),             # eye sockets
    "BH_Steel": ((0.5, 0.5, 0.5), 1.0, 0.4, None, 0.0, 1.0),
    "BH_DarkSteel": ((0.14, 0.14, 0.15), 1.0, 0.5, None, 0.0, 1.0),
    "BH_Wood": ((0.11, 0.065, 0.035), 0.0, 0.7, None, 0.0, 1.0),
}
CLIPS = ["dagger_1", "dual_2", "wand_1"]


def finish_mesh(mesh_ob):
    enable_weapon_deform(mesh_ob)


# ================================================================================================= shared kit
class SB:
    """Standard-space authoring wrapper: parts / weight functions are written for the standard 1.8 m skeleton
    (bh_skeleton.STD, landmarks from the posed Body divided by the scale) and scaled to the character on add."""

    def __init__(self, body, scale):
        self.b = body
        self.s = float(scale)

    # landmarks (standard space)
    def head(self, b):
        return self.b.head(b) / self.s

    def tail(self, b):
        return self.b.tail(b) / self.s

    def axes(self, b):
        return self.b.axes(b)

    def lpt(self, b, pts):
        return self.head(b) + np.asarray(pts, float).reshape(-1, 3) @ self.axes(b).T

    # adding
    def _w(self, weights):
        if weights is None:
            return None
        s = self.s
        return lambda V, f=weights: f(np.asarray(V) / s)

    def add(self, part, bone=None, weights=None):
        part.scale(self.s)
        if bone is None and weights is None:
            bone = part.bone
        return self.b.add(part, bone, self._w(weights))

    def mirror(self, part, bone=None, weights=None):
        part.scale(self.s)
        return self.b.add_mirror(part, bone, self._w(weights))

    def add_real(self, part, bone=None, weights=None):
        return self.b.add(part, bone, weights)

    # weights (functions of standard-space V)
    def seg(self, bones, power=8.0, top=3):
        f = self.b.seg_weights(bones, power, top)
        return lambda V: f(np.asarray(V) * self.s)

    def skirt(self, z_top, z_bot, max_leg=0.85, shin_from=None, center_w=0.06, upper="hips"):
        f = self.b.skirt_weights(z_top * self.s, z_bot * self.s, max_leg,
                                 None if shin_from is None else shin_from * self.s, center_w * self.s, upper)
        return lambda V: f(np.asarray(V) * self.s)


def zspec_w(spec):
    """Blend bones along height: spec = [(z, bone), ...] ascending; smoothstep between consecutive entries."""
    def wfn(V):
        out = []
        for v in V:
            z = v[2]
            if z <= spec[0][0]:
                out.append({spec[0][1]: 1.0})
                continue
            if z >= spec[-1][0]:
                out.append({spec[-1][1]: 1.0})
                continue
            d = {spec[-1][1]: 1.0}
            for (z0, b0), (z1, b1) in zip(spec, spec[1:]):
                if z0 <= z <= z1:
                    if b0 == b1:
                        d = {b0: 1.0}
                    else:
                        t = float(smoothstep(z0, z1, z))
                        d = {b0: 1 - t, b1: t}
                    break
            out.append({k: x for k, x in d.items() if x > 1e-4})
        return out
    return wfn


TORSO_W = zspec_w([(0.99, "hips"), (1.10, "spine"), (1.22, "spine"), (1.32, "chest")])
HEAD_W = zspec_w([(1.50, "chest"), (1.54, "neck"), (1.58, "neck"), (1.61, "head")])
NECK_W = zspec_w([(1.44, "chest"), (1.50, "chest"), (1.56, "neck")])

# body under clothes (z, rx, ry_front, ry_back, keel)
TORSO = [
    (0.96, 0.150, 0.100, 0.100, 0.00),
    (1.04, 0.138, 0.096, 0.094, 0.02),
    (1.14, 0.140, 0.104, 0.096, 0.06),
    (1.25, 0.155, 0.114, 0.100, 0.10),
    (1.35, 0.166, 0.118, 0.104, 0.08),
    (1.43, 0.166, 0.110, 0.104, 0.04),
    (1.49, 0.138, 0.090, 0.092, 0.00),
    (1.53, 0.080, 0.064, 0.064, 0.00),
]

HEAD = [
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


def grow_rows(rows, g, gz=None):
    return [(r[0], r[1] + g, r[2] + g, r[3] + g) + tuple(r[4:]) for r in rows]


def rows_between(rows, z0, z1, g=0.0, n_extra=0):
    zs = sorted(set([z0, z1] + [r[0] for r in rows if z0 < r[0] < z1] + list(np.linspace(z0, z1, n_extra + 2)[1:-1])))
    out = []
    for z in zs:
        r = interp_rows(rows, z)
        out.append((z, r[1] + g, r[2] + g, r[3] + g) + tuple(r[4:]))
    return out


def ring_frac(rows, z, g, fracs, p=2.3):
    """Torso-row ring at height z grown by g, sampled at angle fractions (0 = front, 0.25 = own left, 0.5 = back)."""
    r = interp_rows(rows, z)
    rx, ryf, ryb, keel = r[1] + g, r[2] + g, r[3] + g, r[4]
    cy = r[5] if len(r) > 5 else 0.0
    e = 2.0 / p
    pts = []
    for f in fracs:
        a = 2 * math.pi * f - math.pi / 2
        c, s = math.cos(a), math.sin(a)
        x = rx * np.sign(c) * abs(c) ** e
        if s < 0:
            y = ryf * np.sign(s) * abs(s) ** e * (1 + keel * max(0.0, 1 - abs(c) * 1.6) ** 2)
        else:
            y = ryb * np.sign(s) * abs(s) ** e
        pts.append((x, cy + y, z))
    return np.array(pts)


def band(rows, z0, z1, g_out, g_in=0.0, n=24, p=2.3):
    """Closed thick band following torso rows between z0 and z1 (belts, collars, rims)."""
    def ring(z, g):
        r = interp_rows(rows, z)
        return torso_ring(z, r[1] + g, r[2] + g, r[3] + g, r[4], p, n, cy=r[5] if len(r) > 5 else 0.0)
    loops = [ring(z0, g_in), ring(z0, g_out), ring(z1, g_out), ring(z1, g_in)]
    nn = len(loops[0])
    V = np.vstack(loops)
    F = []
    for k in range(4):
        a, b = k * nn, ((k + 1) % 4) * nn
        for i in range(nn):
            j = (i + 1) % nn
            F.append((a + i, a + j, b + j, b + i))
    return V, F


def strip(pts, w, t, mat, ups=None, n=6):
    """Flat strap along a polyline: width w across, thickness t along `ups` (surface normals)."""
    pts = np.asarray(pts, float)
    ups = ups if ups is not None else [(0, -1, 0)] * len(pts)
    V, F = M.tube(pts, [(w / 2, t / 2)] * len(pts), n=n, up=[np.asarray(u, float) for u in ups], p=3.0)
    return M.Part(V, F, mat, name="strip")


def rtube(pts, r, mat, n=6, cap=True):
    pts = np.asarray(pts, float)
    rr = r if isinstance(r, (list, tuple)) else [r] * len(pts)
    up = (0, 0, 1) if abs(normalize(pts[-1] - pts[0])[2]) < 0.9 else (0, -1, 0)
    V, F = M.tube(pts, [(x, x) for x in rr], n=n, up=up, cap0=cap, cap1=cap)
    return M.Part(V, F, mat, name="rtube")


def norm_rows(A):
    A = np.asarray(A, float)
    return A / np.maximum(np.linalg.norm(A, axis=1, keepdims=True), 1e-9)


# ---------------------------------------------------------------- weapon socket
def to_socket(body, side, part):
    """Weapon-builder space (grip at origin, +Z blade, flats +-Y) -> model space of the posed weapon socket
    (same mapping as preview_chars.attach: socket-local = (x, z, -y)). Returns a REAL-space part."""
    wb = "weapon." + side
    A = body.axes(wb)
    o = body.head(wb)
    V = part.V
    loc = np.stack([V[:, 0], V[:, 2], -V[:, 1]], 1)
    part.V = o + loc @ A.T
    return part


def enable_weapon_deform(mesh_ob):
    """build_chars finish_mesh hook: the weapon sockets are non-deform bones (bh_skeleton.DEFORM_EXCLUDE), so the
    armature modifier would ignore the weapon vertex groups (weapons would stay in the T-pose). Mesh weapons need
    them to deform (also keeps their skin weights in the glTF)."""
    arm = mesh_ob.parent
    for bn in ("weapon.L", "weapon.R"):
        if bn in arm.data.bones and bn in mesh_ob.vertex_groups:
            arm.data.bones[bn].use_deform = True


def add_weapon(sb, side, parts):
    for p in parts:
        sb.add_real(to_socket(sb.b, side, p), "weapon." + side)


def add_fist(sb, side, mat_back, mat_fingers, gauntlet=False, scale=1.0):
    for prt in fist(sb.b, side, mat_back, mat_fingers, gauntlet=gauntlet, scale=scale):
        sb.add_real(prt, "hand." + side)


# ---------------------------------------------------------------- body pieces
def neck_and_head(sb, skin="BH_Skin", head_rows=HEAD, face=True, eyes="BH_Shadow", eye_glow=None, nose=True):
    V, F = M.tube([(0, 0.0, 1.46), (0, -0.004, 1.54), (0, -0.01, 1.62)], [(0.056, 0.053), (0.05, 0.048), (0.05, 0.05)],
                  n=12, up=(0, -1, 0))
    sb.add(M.Part(V, F, skin, name="neck"), weights=HEAD_W)
    V, F = torso_loft(head_rows, n=22, p=2.1, cap0=True, cap1=True)
    sb.add(M.Part(V, F, skin, name="head"), "head")
    if not face:
        return
    V, F = M.tube([(-0.05, -0.068, 1.716), (0.0, -0.08, 1.722), (0.05, -0.068, 1.716)],
                  [(0.012, 0.008)] * 3, n=6, up=(0, -1, 0))
    sb.add(M.Part(V, F, skin, name="brow"), "head")
    if nose:
        V, F = M.tube([(0, -0.076, 1.712), (0, -0.087, 1.684), (0, -0.094, 1.662), (0, -0.088, 1.652)],
                      [(0.0065, 0.006), (0.009, 0.008), (0.012, 0.009), (0.008, 0.005)], n=6, up=(0, -1, 0))
        sb.add(M.Part(V, F, skin, name="nose"), "head")
    for sx in (1, -1):
        V, F = M.sphere(0.013, 8, 5, center=(sx * 0.029, -0.069, 1.699), scale=(1.15, 0.6, 0.75))
        sb.add(M.Part(V, F, eyes, name="socket"), "head")
        if eye_glow:
            V, F = M.sphere(0.0062, 6, 4, center=(sx * 0.029, -0.075, 1.699), scale=(1.3, 0.7, 0.8))
            sb.add(M.Part(V, F, eye_glow, name="eye"), "head")
    for sx in (1, -1):   # ears
        V, F = M.sphere(0.02, 6, 4, center=(sx * 0.074, 0.0, 1.69), scale=(0.35, 0.8, 1.2))
        sb.add(M.Part(V, F, skin, name="ear"), "head")


def hair_cap(sb, mat="BH_Hair", g=0.007, z_front=1.745, z_back=1.63, messy=0.006):
    """Short hair: head rows grown by g above a hairline that dips from the forehead to the nape."""
    rows = grow_rows(HEAD, g)
    nu = 24
    zs = np.linspace(0, 1, 6)
    rings = []
    for v in zs:
        ring = []
        for i in range(nu):
            f = i / nu
            back = 0.5 - 0.5 * math.cos(2 * math.pi * f)       # 0 front, 1 back
            z0 = z_front + (z_back - z_front) * back
            z = z0 + (1.826 - z0) * v ** 0.8
            q = ring_frac(rows, min(z, 1.818), 0.0, [f], p=2.1)[0]
            q[2] = z
            q[:2] *= 1.0 + messy * math.sin(7 * f * 2 * math.pi) * (1 - v) * 6
            ring.append(q)
        rings.append(np.array(ring))
    V, F = M.loft(rings, cap0=False, cap1=True)
    sb.add(M.Part(V, F, mat, name="hair"), "head")


def bare_arm(sb, side, skin="BH_Skin", r_up=0.05, r_fore=0.043, r_wrist=0.032, bulk=1.0):
    """Skin arm from inside the shoulder to the wrist, smoothly weighted (shoulder / upper arm / forearm)."""
    s = side
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    sx = 1 if s == "L" else -1
    inn = np.array([sx * -0.04, 0, 0.0])
    pts = [sh + inn + (0, 0, 0.02), sh + (0, 0, 0.0), sh + (el - sh) * 0.3, sh + (el - sh) * 0.7, el,
           el + (wr - el) * 0.3, el + (wr - el) * 0.7, wr + (wr - el) * 0.08]
    b = bulk
    prof = [(0.045 * b, 0.05 * b), (0.058 * b, 0.06 * b), (r_up * b + 0.004, r_up * b + 0.006), (r_up * b, r_up * b),
            (r_fore * b * 0.95, r_fore * b * 0.95), (r_fore * b, r_fore * b * 1.05), (r_wrist * 1.15, r_wrist * 1.2),
            (r_wrist, r_wrist * 1.1)]
    V, F = M.tube(pts, prof, n=12, up=(0, -1, 0))
    sb.add(M.Part(V, F, skin, name="arm"), weights=sb.seg(["chest", "shoulder." + s, ua, fa, ha], power=9))


def wrap_band(sb, bone_a, bone_b, u0, u1, r, mat, turns=3, width=0.02, thick=0.006, bone=None):
    """Spiral bandage / cord wrapped around a limb segment between fractions u0..u1 of (head(bone_a)->head(bone_b))."""
    a, b = sb.head(bone_a), sb.head(bone_b)
    d = normalize(b - a)
    side = normalize(np.cross(d, (0, 1, 0))) if abs(d[1]) < 0.9 else np.array([1.0, 0, 0])
    fw = np.cross(side, d)
    pts, ups = [], []
    n = int(turns * 10) + 1
    for i in range(n):
        t = i / (n - 1)
        ang = 2 * math.pi * turns * t
        c = a + (b - a) * (u0 + (u1 - u0) * t)
        nrm = side * math.cos(ang) + fw * math.sin(ang)
        pts.append(c + nrm * r)
        ups.append(nrm)
    V, F = M.tube(pts, [(width / 2, thick / 2)] * n, n=4, up=[np.asarray(u) for u in ups], p=3.0)
    p = M.Part(V, F, mat, name="wrap")
    sb.add(p, bone or bone_a)


def pelvis_seat(sb, mat, g=0.0):
    V, F = torso_loft([(0.84, 0.150 + g, 0.092 + g, 0.10 + g, 0.0), (0.92, 0.152 + g, 0.098 + g, 0.104 + g, 0.0),
                       (1.0, 0.146 + g, 0.096 + g, 0.10 + g, 0.0)], n=24)
    sb.add(M.Part(V, F, mat, name="seat"), weights=sb.skirt(0.98, 0.84, max_leg=0.7, center_w=0.05))


def trousers(sb, mat, loose=1.0, end=0.62):
    for s in ("L", "R"):
        th, sh = "thigh." + s, "shin." + s
        h, k, a = sb.head(th), sb.head(sh), sb.tail(sh)
        pts = [h + (0, 0, 0.04), h + (k - h) * 0.4, k + (0, 0, 0.02), k + (a - k) * 0.35, k + (a - k) * end]
        L = loose
        prof = [(0.078 * L, 0.082 * L), (0.07 * L, 0.074 * L), (0.056 * L, 0.06 * L), (0.052 * L, 0.056 * L),
                (0.046 * L, 0.048 * L)]
        V, F = M.tube(pts, prof, n=12, up=(0, -1, 0))
        sb.add(M.Part(V, F, mat, name="trouser"), weights=sb.seg([th, sh], power=10))


def boots(sb, mat="BH_Leather", sole="BH_DarkSteel", shaft_top=0.62, cuff=True, wraps=None, rim=None):
    """Simple leather boots (shaft on shin, foot on foot, toe cap on toe). wraps: material for cross-straps."""
    for s in ("L", "R"):
        hx = sb.head("thigh." + s)[0]
        sh = "shin." + s
        k, a = sb.head(sh), sb.tail(sh)
        pts = [a + (0, 0.004, 0.03), a + (k - a) * 0.4, a + (k - a) * shaft_top]
        V, F = M.tube(pts, [(0.05, 0.054), (0.052, 0.056), (0.056, 0.06)], n=12, up=(0, -1, 0), cap1=False)
        sb.add(M.solidify(M.Part(V, F, mat, name="boot"), 0.004, offset=-1.0), sh)
        if cuff:
            c0 = a + (k - a) * (shaft_top - 0.03)
            c1 = a + (k - a) * (shaft_top + 0.07)
            V, F = M.tube([c0, c1], [(0.062, 0.066), (0.066, 0.07)], n=12, up=(0, -1, 0), cap0=False, cap1=False)
            sb.add(M.solidify(M.Part(V, F, mat, name="cuff"), 0.006, offset=-1.0), sh)
        if wraps:
            for zf in (0.25, 0.45):
                c = a + (k - a) * zf
                V, F = M.tube([c - (0, 0, 0.008), c + (0, 0, 0.008)], [(0.058, 0.062)] * 2, n=12, up=(0, -1, 0))
                sb.add(M.Part(V, F, wraps, name="bootstrap"), sh)

        def rings(spec):
            R = []
            for y, w, top in spec:
                pts = []
                for i in range(12):
                    ang = 2 * math.pi * i / 12
                    c, sn = math.cos(ang), math.sin(ang)
                    x = w * np.sign(c) * abs(c) ** 0.8
                    z = top / 2 + top / 2 * np.sign(sn) * abs(sn) ** 0.7
                    pts.append((hx + x, y, max(z, 0.014)))
                R.append(np.array(pts))
            return R
        foot = rings([(0.065, 0.034, 0.075), (0.045, 0.042, 0.11), (0.0, 0.046, 0.12), (-0.06, 0.047, 0.09),
                      (-0.12, 0.046, 0.065)])
        V, F = M.loft(foot[::-1])
        sb.add(M.Part(V, F, mat, name="bootfoot"), "foot." + s)
        toe = rings([(-0.115, 0.046, 0.065), (-0.17, 0.043, 0.054), (-0.212, 0.032, 0.042), (-0.232, 0.014, 0.03)])
        V, F = M.loft(toe[::-1])
        sb.add(M.Part(V, F, mat, name="boottoe"), "toe." + s)
        V, F = M.box(0.094, 0.2, 0.016, center=(hx, -0.03, 0.008))
        sb.add(M.Part(V, F, sole, name="sole"), "foot." + s)
        V, F = M.box(0.076, 0.1, 0.014, center=(hx, -0.18, 0.007))
        sb.add(M.Part(V, F, sole, name="sole_t"), "toe." + s)


def belt(sb, rows, z=1.03, h=0.045, g=0.016, mat="BH_Leather", buckle="BH_DarkSteel"):
    V, F = band(rows, z, z + h, g + 0.012, g - 0.004, n=28)
    sb.add(M.Part(V, F, mat, name="belt"), "hips")
    by = front_y(rows, 0, z + h / 2) - g - 0.014
    V, F = M.box(0.05, 0.012, 0.042, center=(0, by, z + h / 2))
    sb.add(M.Part(V, F, buckle, name="buckle"), "hips")


def on_ring(rows, z, g, frac):
    """Point on a torso ring + the outward yaw (deg) for orienting props (0 = front)."""
    p = ring_frac(rows, z, g, [frac])[0]
    a = 2 * math.pi * frac - math.pi / 2
    return p, math.degrees(a) + 90


def pouch(sb, rows, frac, z, g, size=(0.08, 0.04, 0.07), mat="BH_Leather", bone="hips"):
    p, ang = on_ring(rows, z, g + size[1] / 2, frac)
    V, F = M.box(*size)
    sb.add(M.bevel(M.Part(V, F, mat, name="pouch"), 0.008, 1).rot(Rz(ang)).move(p), bone)
    V, F = M.box(size[0] * 1.05, size[1] * 1.12, 0.022)
    sb.add(M.Part(V, F, mat, name="flap").rot(Rz(ang)).move(p + (0, 0, size[2] / 2 - 0.006)), bone)


def cloth_panel(fn, nu, nv, mat, thick=0.008, flip=False):
    V, F = M.grid(fn, nu, nv)
    p = M.Part(V, F, mat, name="panel")
    if flip:
        p.flip()
    return M.solidify(p, thick, offset=1.0)


# ---------------------------------------------------------------- weapons (weapon-builder space)
def curved_knife(length=0.34, width=0.042, curve=0.06, mat="BH_Steel", grip_mat="BH_Leather"):
    """Single-edged curved knife: edge on +X (knuckle side), blade sweeping back toward -X near the tip."""
    rings = []
    n = 10
    for i in range(n + 1):
        u = i / n
        z = 0.05 + length * u
        xc = -curve * u ** 2
        w = width * (1 - 0.15 * u) * (1 - u ** 3) + 0.002
        t = 0.0055 * (1 - 0.7 * u) + 0.0008
        spine = xc - w * 0.45 + (0.35 * w * u ** 2)
        edge = xc + w * 0.55
        rings.append(np.array([(edge, 0, z), (edge - 0.25 * (edge - spine), t * 0.6, z), (spine, t, z),
                               (spine, -t, z), (edge - 0.25 * (edge - spine), -t * 0.6, z)]))
    V, F = M.loft(rings)
    parts = [M.Part(V, F, mat, name="knife")]
    parts.append(M.bevel(WP._crossguard(0.045, 0.035, h=0.012, t=0.016, curve=0.0, mat="BH_DarkSteel"), 0.002, 1))
    parts.append(WP._grip(-0.06, 0.04, 0.0135, 4, mat=grip_mat))
    parts.append(WP._pommel(-0.07, 0.016, mat="BH_DarkSteel"))
    return parts


def short_dagger(mat="BH_Steel"):
    return [
        WP._blade(0.045, 0.25, 0.032, 0.02, 0.005, tip=0.06, n_sec=4, fuller=False, mat=mat),
        M.bevel(WP._crossguard(0.04, 0.045, h=0.012, t=0.014, curve=0.01, mat="BH_DarkSteel"), 0.002, 1),
        WP._grip(-0.05, 0.035, 0.0125, 3, mat="BH_Wood"),
        WP._pommel(-0.06, 0.015, mat="BH_DarkSteel"),
    ]


def throwing_knife(center, direction, normal, length=0.15, mat="BH_Steel", grip="BH_Leather"):
    """Small throwing knife lying on a surface (normal), blade along direction. Standard/model space part list."""
    d = normalize(direction)
    nrm = normalize(normal)
    x = normalize(np.cross(nrm, d))
    R = np.stack([x, nrm, d], 1)   # local x across, y out of surface, z along blade
    V, F = M.lathe([(0, -0.0), (0.012, 0.004), (0.012, 0.06), (0.0, 0.065)], 4)
    blade = M.Part(V, F, mat, name="tknife").scale((1, 0.25, length / 0.065 * 0.6))
    V, F = M.box(0.012, 0.01, 0.05, center=(0, 0, -0.025))
    hilt = M.Part(V, F, grip, name="tknife_grip")
    out = []
    for p in (blade, hilt):
        p.rot(R).move(center)
        out.append(p)
    return out


# ================================================================================================= cutthroat
JERKIN_G = 0.016


def build(body):
    sb = SB(body, SCALE)
    # ---- torso: dark shirt under a sleeveless leather jerkin
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="shirt"), weights=TORSO_W)
    jerkin(sb)
    bandolier(sb)
    # ---- head: dark hair, red scarf over the lower face
    neck_and_head(sb, nose=True)
    hair_cap(sb, z_front=1.75, z_back=1.62)
    scarf(sb)
    # ---- arms: bare, bandaged forearms, a leather bracer on the left
    for s in ("L", "R"):
        bare_arm(sb, s, r_up=0.05, r_fore=0.044)
        wrap_band(sb, "forearm." + s, "hand." + s, 0.3, 0.95 if s == "R" else 0.5, 0.046, "BH_Bone", turns=3.5,
                  width=0.024)
        add_fist(sb, s, "BH_Skin", "BH_Skin", gauntlet=False)
    fa, ha = sb.head("forearm.L"), sb.head("hand.L")
    V, F = M.tube([fa + (ha - fa) * 0.55, fa + (ha - fa) * 0.78, fa + (ha - fa) * 1.0],
                  [(0.049, 0.051), (0.048, 0.05), (0.044, 0.046)], n=12, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Horn", name="bracer"), "forearm.L")
    # upper-arm strap with a knife sheath on the right arm
    ua, fa = sb.head("upper_arm.R"), sb.head("forearm.R")
    c = ua + (fa - ua) * 0.45
    V, F = M.tube([c - (0, 0, 0.012), c + (0, 0, 0.012)], [(0.056, 0.056)] * 2, n=10, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Leather", name="armstrap"), "upper_arm.R")
    # ---- legs
    pelvis_seat(sb, "BH_Cloth_Secondary")
    trousers(sb, "BH_Cloth_Secondary", loose=1.05)
    boots(sb, "BH_Leather", "BH_DarkSteel", wraps="BH_Horn")
    belt(sb, TORSO, z=1.0, g=JERKIN_G + 0.004, mat="BH_Horn")
    pouch(sb, TORSO, 0.36, 0.97, JERKIN_G + 0.02, mat="BH_Leather")
    pouch(sb, TORSO, 0.64, 0.97, JERKIN_G + 0.02, size=(0.06, 0.04, 0.06), mat="BH_Horn")
    # empty sheath on the left hip for the curved knife
    p, ang = on_ring(TORSO, 0.9, JERKIN_G + 0.03, 0.2)
    V, F = M.tube([p + (0, 0, 0.08), p + (0.015, -0.02, -0.14)], [(0.022, 0.012), (0.012, 0.007)], n=6,
                  up=(1, 0, 0))
    sb.add(M.Part(V, F, "BH_Leather", name="sheath"), "hips")
    # ---- weapons
    add_weapon(sb, "R", curved_knife())
    add_weapon(sb, "L", short_dagger())


def jerkin(sb):
    g = JERKIN_G
    # body: laced V at the throat, lower hem at 0.86 with side slits (front / back skirt panels)
    zs = [1.0, 1.08, 1.16, 1.25, 1.33, 1.40, 1.46, 1.50]
    nu = 34
    rings = []
    for z in zs:
        t = (z - 1.0) / 0.5
        a0 = 0.005 + 0.05 * max(0, (t - 0.55) / 0.45) ** 1.5
        fr = a0 + (1 - 2 * a0) * np.linspace(0, 1, nu)
        rings.append(ring_frac(TORSO, z, g + 0.004 * (1 - t), fr))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    sb.add(M.solidify(M.Part(V, F, "BH_Leather", name="jerkin"), 0.01, offset=1.0), weights=TORSO_W)
    # shoulder yoke: armholes stay open (the arm tube comes out below it)
    for sx in (1, -1):
        pts, ups = [], []
        for t in np.linspace(0, 1, 7):
            a = math.pi * (0.5 - t)
            x = sx * 0.125
            y = -0.098 * math.sin(a) + 0.005
            z = 1.48 + 0.04 * math.cos(a)
            pts.append((x, y, z))
            ups.append((0, -math.sin(a), math.cos(a)))
        sb.add(strip(pts, 0.085, 0.014, "BH_Leather", ups=ups), "chest")
    # skirt panels
    for back in (False, True):
        rs = []
        for z in (0.84, 0.92, 1.0):
            t = (1.0 - z) / 0.16
            fr = np.linspace(0.3, 0.7, 13) if back else np.concatenate([np.linspace(-0.2, 0.2, 13)])
            pts = ring_frac(TORSO, max(z, 0.96), g + 0.004 + 0.035 * t, fr % 1.0)
            pts[:, 2] = z
            rs.append(pts)
        V, F = M.loft(rs, cap0=False, cap1=False, closed=False)
        p = M.Part(V, F, "BH_Leather", name="jerkin_skirt")
        if back:
            p.flip()
        sb.add(M.solidify(p, 0.01, offset=1.0), weights=sb.skirt(1.0, 0.84, max_leg=0.6, center_w=0.06))
    # patches (lighter leather, stitched on) - big enough to read
    for (frac, z, w, h, rot) in ((0.12, 1.3, 0.08, 0.07, 12), (0.9, 1.12, 0.07, 0.09, -8), (0.47, 1.35, 0.1, 0.08, 5)):
        p, ang = on_ring(TORSO, z, g + 0.012, frac)
        V, F = M.box(w, 0.008, h)
        sb.add(M.Part(V, F, "BH_Horn", name="patch").rot(Ry(rot)).rot(Rz(ang)).move(p), weights=TORSO_W)
    # lacing across the V
    for z in np.linspace(1.36, 1.46, 3):
        y = front_y(TORSO, 0, z) - g - 0.012
        V, F = M.box(0.05, 0.006, 0.006, center=(0, y, z))
        sb.add(M.Part(V, F, "BH_Horn", name="lace"), "chest")


def bandolier(sb):
    g = JERKIN_G + 0.02
    # left shoulder -> right hip, front and back
    pts, ups = [], []
    for t in np.linspace(0, 1, 9):
        x = 0.12 - 0.27 * t
        z = 1.47 - 0.43 * t
        y = front_y(TORSO, x, z) - g
        pts.append((x, y, z))
        ups.append((0.2 * x, -1, 0))
    sb.add(strip(pts, 0.05, 0.01, "BH_Horn", ups=ups), weights=TORSO_W)
    front = pts
    pts = []
    for t in np.linspace(0, 1, 7):
        x = 0.12 - 0.27 * t
        z = 1.47 - 0.43 * t
        pts.append((x, back_y(TORSO, x, z) + g, z))
    sb.add(strip(pts, 0.05, 0.01, "BH_Horn", ups=[(0, 1, 0)] * 7), weights=TORSO_W)
    pts, ups = [], []
    for t in np.linspace(0, 1, 7):
        a = math.pi * (0.5 - t) * 0.95
        pts.append((0.12, -0.11 * math.sin(a) + 0.005, 1.47 + 0.05 * math.cos(a)))
        ups.append((0, -math.sin(a), math.cos(a)))
    sb.add(strip(pts, 0.05, 0.01, "BH_Horn", ups=ups), "chest")
    # knives in loops along the front strap, pointing up toward the left shoulder
    d = np.asarray(front[0]) - np.asarray(front[-1])
    for t in (0.2, 0.34, 0.48, 0.62, 0.76):
        i = t * (len(front) - 1)
        i0 = int(i)
        c = np.asarray(front[i0]) * (1 - (i - i0)) + np.asarray(front[min(i0 + 1, len(front) - 1)]) * (i - i0)
        blade_dir = normalize(np.array([0.35, 0, 1.0]))
        for prt in throwing_knife(c + (0, -0.012, -0.02), blade_dir, (0.0, -1, 0), length=0.16):
            sb.add(prt, weights=TORSO_W)
        V, F = M.box(0.024, 0.016, 0.02)
        sb.add(M.Part(V, F, "BH_Leather", name="loop").rot(Ry(-20)).move(c + (0, -0.008, 0)), weights=TORSO_W)


def scarf(sb):
    """Faded red scarf: band over the nose / mouth, a hanging front triangle over the throat, knot + tails at the back."""
    rows = grow_rows(HEAD, 0.012)
    nu = 22
    rings = []
    for z in (1.59, 1.625, 1.66, 1.682):
        fr = np.linspace(0, 1, nu, endpoint=False)
        r = ring_frac(rows, max(z, 1.60), 0.0, fr, p=2.1)
        r[:, 2] = z
        if z < 1.6:
            r[:, :2] *= 1.05
        rings.append(r)
    V, F = M.loft(rings, cap0=False, cap1=False)
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="scarf"), 0.008, offset=1.0), "head")
    # the cloth drops from the chin over the throat (neck -> chest)
    def fn(u, v):
        w = 0.075 * (1 - v) + 0.012
        x = (u - 0.5) * 2 * w
        z = 1.595 - 0.13 * v
        y = -0.085 + 0.02 * v + 0.012 * abs(u - 0.5)
        return (x, y, z)
    sb.add(cloth_panel(fn, 7, 5, "BH_Cloth_Primary", thick=0.008), weights=NECK_W)
    # neck wrap
    V, F = M.tube([(0, 0.0, 1.5), (0, -0.004, 1.57)], [(0.068, 0.064), (0.062, 0.058)], n=14, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="neckwrap"), weights=HEAD_W)
    # knot + two tails at the back of the head
    V, F = M.sphere(0.024, 8, 5, center=(0, 0.1, 1.645), scale=(1.2, 0.8, 0.9))
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="knot"), "head")
    for sx, ln in ((1, 0.2), (-1, 0.15)):
        pts = [(0.012 * sx, 0.11, 1.64), (0.03 * sx, 0.13, 1.58), (0.04 * sx, 0.14, 1.64 - ln)]
        sb.add(strip(pts, 0.04, 0.006, "BH_Cloth_Primary", ups=[(0, 1, 0)] * 3), weights=HEAD_W)
