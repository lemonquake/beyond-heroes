"""Hollow Soldier (undead fodder, builder A): a skeleton of the fallen forest garrison in a rotten crimson surcoat
(torn off the left chest so the ribcage and spine show), a dented kettle helm tipped back, a single rusted pauldron
(left; the right one is missing and the shoulder is bare bone), a leather bracer, rotten boots, and a notched rusty
arming sword. Faint teal grave-light in the eye sockets.

Also holds the small helpers the other builder-A undead modules share (skeleton pieces, socket-space weapons,
ragged cloth panels)."""
import math
import numpy as np

import bh_mesh as M
import bh_weapons as WP
from bh_body import Body, torso_loft, interp_rows, front_y, back_y, dome, fist, smoothstep, M_align_z
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
from char_mage import zspec_w
from char_knight import thick_band

PROPS = proportions()
PALETTE = "hollow_soldier"
PALETTE_COLORS = {
    "BH_Bone": ((0.50, 0.46, 0.35), 0.0, 0.62, None, 0.0, 1.0),
    "BH_Rust": ((0.24, 0.12, 0.06), 0.4, 0.8, None, 0.0, 1.0),
    "BH_DarkSteel": ((0.13, 0.17, 0.15), 0.85, 0.55, None, 0.0, 1.0),      # verdigris-tinged old iron
    "BH_Cloth_Primary": ((0.17, 0.045, 0.035), 0.0, 0.92, None, 0.0, 1.0),  # rotten garrison crimson
    "BH_Leather": ((0.07, 0.045, 0.028), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Shadow": ((0.03, 0.035, 0.04), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((0.3, 0.9, 0.8), 0.0, 0.4, (0.3, 1.0, 0.85), 7.0, 1.0),
}
CLIPS = ["sword_1", "sword_2", "sword_heavy"]


def finish_mesh(mesh_ob):
    enable_weapon_deform(mesh_ob)


def enable_weapon_deform(mesh_ob):
    """The weapon sockets are non-deform bones in bh_skeleton (DEFORM_EXCLUDE); a mesh weapon weighted to them would
    stay in the T-pose, so turn deform on for the sockets this mesh uses (also keeps their skin weights in the glTF)."""
    arm = mesh_ob.parent
    for bn in ("weapon.L", "weapon.R"):
        if bn in arm.data.bones and bn in mesh_ob.vertex_groups:
            arm.data.bones[bn].use_deform = True

SPINE_W = zspec_w([(1.02, "hips"), (1.12, "spine"), (1.22, "spine"), (1.30, "chest")])
NECK_W = zspec_w([(1.47, "chest"), (1.50, "neck")])

# cloth envelope (over the ribcage / pelvis)
ENV = [
    (0.86, 0.165, 0.11, 0.115, 0.0),
    (0.95, 0.16, 0.105, 0.11, 0.0),
    (1.05, 0.145, 0.10, 0.10, 0.0),
    (1.15, 0.14, 0.11, 0.10, 0.0),
    (1.25, 0.15, 0.125, 0.10, 0.0),
    (1.35, 0.16, 0.13, 0.105, 0.0),
    (1.43, 0.16, 0.115, 0.105, 0.0),
    (1.49, 0.12, 0.085, 0.085, 0.0),
]


# =================================================================================================== helpers
def P(V, F, mat, name="part"):
    return M.Part(V, F, mat, name=name)


def rtube(pts, r, mat, n=6, r1=None, up=None, cap=True):
    pts = np.asarray(pts, float)
    r1 = r if r1 is None else r1
    prof = [(r + (r1 - r) * i / max(len(pts) - 1, 1),) * 2 for i in range(len(pts))]
    if up is None:
        d = normalize(pts[-1] - pts[0])
        up = (0, 0, 1) if abs(d[2]) < 0.85 else (0, -1, 0)
    V, F = M.tube(pts, prof, n=n, up=up, cap0=cap, cap1=cap)
    return P(V, F, mat)


def ball(c, r, mat, n=8, rings=5, scale=(1, 1, 1)):
    V, F = M.sphere(r, n, rings, center=c, scale=scale)
    return P(V, F, mat, "ball")


def socket_parts(body, side, parts):
    """Weapon parts authored in weapon-GLB space (grip origin, +Z blade, flats +-Y) -> model space at the socket,
    matching an identity weapon attachment in Godot (GLB (x, y, z) -> bone-local (x, z, -y))."""
    A = body.axes("weapon." + side)
    o = body.head("weapon." + side)
    out = []
    for p in parts:
        q = p.copy()
        loc = np.stack([q.V[:, 0], q.V[:, 2], -q.V[:, 1]], 1)
        q.V = o + loc @ A.T
        out.append(q)
    return out


def add_weapon(body, side, parts):
    for p in socket_parts(body, side, parts):
        body.add(p, "weapon." + side)


def dent(part, center, direction, depth, radius):
    c = np.asarray(center, float)
    d = normalize(direction)
    r2 = np.sum((part.V - c) ** 2, 1)
    part.V = part.V + d[None] * (depth * np.exp(-r2 / radius ** 2))[:, None]
    return part


def ragged(u, seed, amp=0.05, teeth=5):
    """Deterministic ragged-hem offset (0..amp) along u in [0,1]."""
    v = 0.5 + 0.5 * math.sin(u * math.pi * 2 * teeth + seed) * math.cos(u * math.pi * 3.3 + 1.7 * seed)
    tooth = abs(((u * teeth * 2.0 + seed * 0.37) % 2.0) - 1.0)
    return amp * (0.55 * v + 0.45 * tooth)


def cloth_panel(rows, z_top, z_bot, x_half, front=True, nu=9, nv=12, mat="BH_Cloth_Primary", gap=0.014,
                hang=0.04, seed=1.0, rag=0.06, teeth=4, top_rag=0.0, thick=0.009, belt_z=1.05):
    """Surcoat panel following the envelope rows above belt_z, hanging free below it; ragged bottom (and optional
    ragged/torn top). x_half(z) -> half width."""
    def fn(u, v):
        zt = z_top - (ragged(u, seed + 3.1, top_rag, 3) if top_rag else 0.0)
        zb = z_bot + ragged(u, seed, rag, teeth)
        z = zt + (zb - zt) * v
        hw = x_half(z)
        x = (u - 0.5) * 2 * hw
        if z >= belt_z:
            y = front_y(rows, x, z) - gap if front else back_y(rows, x, z) + gap
        else:
            y0 = front_y(rows, x, belt_z) - gap if front else back_y(rows, x, belt_z) + gap
            d = belt_z - z
            y = y0 - hang * d if front else y0 + hang * 1.3 * d
            y += 0.008 * math.sin(u * math.pi * 5 + seed) * d / 0.5
        return (x, y, z)
    V, F = M.grid(fn, nu, nv)
    p = P(V, F, mat, "surcoat")
    if not front:
        p.flip()
    return M.solidify(p, thick, offset=1.0)


def cloth_w(chest_z=1.30, belt_z=1.03, leg=0.75, knee_z=0.55):
    def wfn(V):
        out = []
        for v in V:
            z = v[2]
            if z >= chest_z:
                out.append({"chest": 1.0})
            elif z >= 1.18:
                t = float(smoothstep(1.18, chest_z, z))
                out.append({"chest": t, "spine": 1 - t})
            elif z >= belt_z:
                t = float(smoothstep(belt_z, 1.12, z))
                out.append({"spine": t, "hips": 1 - t} if t > 0 else {"hips": 1.0})
            else:
                s = float(smoothstep(belt_z - 0.03, knee_z, z)) * leg
                side = float(smoothstep(-0.06, 0.06, v[0]))
                d = {"hips": 1 - s}
                if s * side > 1e-3:
                    d["thigh.L"] = s * side
                if s * (1 - side) > 1e-3:
                    d["thigh.R"] = s * (1 - side)
                out.append(d)
        return out
    return wfn


# =================================================================================================== skeleton
def skull(body, eye_mat="BH_Emissive", jaw_open=6.0, s=1.0):
    """Skull on the head bone (model space). Returns parts."""
    parts = []
    hz = body.head("head")[2]            # 1.60 for the standard skeleton
    z0 = hz + 0.035 * s
    rows = [
        (z0 + 0.000, 0.046, 0.050, 0.040, 0.0, -0.012),
        (z0 + 0.030, 0.060, 0.068, 0.058, 0.0, -0.006),
        (z0 + 0.065, 0.066, 0.074, 0.078, 0.0, 0.0),
        (z0 + 0.105, 0.072, 0.074, 0.088, 0.0, 0.006),
        (z0 + 0.145, 0.068, 0.064, 0.084, 0.0, 0.012),
        (z0 + 0.175, 0.052, 0.046, 0.064, 0.0, 0.014),
        (z0 + 0.193, 0.026, 0.022, 0.034, 0.0, 0.016),
    ]
    rows = [(r[0],) + tuple(x * s for x in r[1:]) for r in rows]
    V, F = torso_loft(rows, n=18, p=2.2, cap0=True, cap1=True)
    parts.append(P(V, F, "BH_Bone", "cranium"))
    ez = z0 + 0.068 * s
    for sx in (1, -1):
        parts.append(ball((sx * 0.029 * s, -0.066 * s, ez), 0.021 * s, "BH_Shadow", 8, 5, (1.0, 0.6, 0.85)))
        parts.append(ball((sx * 0.029 * s, -0.077 * s, ez - 0.002), 0.0095 * s, eye_mat, 6, 4, (1.0, 0.8, 0.8)))
        # cheekbone
        parts.append(rtube([(sx * 0.03 * s, -0.07 * s, ez - 0.024 * s), (sx * 0.062 * s, -0.04 * s, ez - 0.02 * s),
                            (sx * 0.07 * s, -0.0, ez - 0.012 * s)], 0.009 * s, "BH_Bone", n=5))
    # brow ridge
    parts.append(rtube([(-0.06 * s, -0.064 * s, ez + 0.022 * s), (0, -0.078 * s, ez + 0.024 * s),
                        (0.06 * s, -0.064 * s, ez + 0.022 * s)], 0.011 * s, "BH_Bone", n=6))
    # nasal cavity
    V, F = M.prism([(-0.012, 0.0), (0.012, 0.0), (0.0, 0.028)], 0.01, axis="y")
    parts.append(P(V, F, "BH_Shadow", "nose").scale(s).rot(Rx(15)).move((0, -0.076 * s, ez - 0.045 * s)))
    # upper teeth
    tz = z0 - 0.002
    teeth = [(0.03 * math.sin(a) * s, (-0.05 - 0.012 * math.cos(a)) * s, tz) for a in np.linspace(-1.2, 1.2, 6)]
    parts.append(rtube(teeth, 0.008 * s, "BH_Bone", n=5, up=(0, 0, 1)))
    # mandible (slightly agape): hinge near the ears, rotated about the hinge axis
    hinge = np.array([0, 0.0, z0 + 0.03 * s])
    jaw = []
    for sx in (1, -1):
        pts = [(sx * 0.058 * s, -0.005 * s, z0 + 0.03 * s), (sx * 0.056 * s, -0.012 * s, z0 - 0.02 * s),
               (sx * 0.04 * s, -0.045 * s, z0 - 0.035 * s), (0.0, -0.062 * s, z0 - 0.036 * s)]
        jaw.append(rtube(pts, 0.011 * s, "BH_Bone", n=6, r1=0.013 * s))
    lt = [(0.028 * math.sin(a) * s, (-0.048 - 0.01 * math.cos(a)) * s, z0 - 0.022 * s) for a in np.linspace(-1.1, 1.1, 5)]
    jaw.append(rtube(lt, 0.007 * s, "BH_Bone", n=5, up=(0, 0, 1)))
    for j in jaw:
        j.rot(Rx(-jaw_open), center=hinge)
    parts += jaw
    return parts


def spine_column(body, y=0.035, z0=0.93, z1=1.50, r=0.017):
    parts = []
    parts.append((rtube([(0, y, z0), (0, y - 0.012, 1.12), (0, y + 0.004, 1.32), (0, y, z1)], r, "BH_Bone", n=6),
                  SPINE_W))
    for z in np.arange(z0 + 0.03, z1, 0.045):
        yy = y - 0.012 * math.sin(math.pi * (z - z0) / (z1 - z0))
        V, F = M.lathe([(0, -0.009), (0.026, -0.008), (0.028, 0.0), (0.026, 0.008), (0, 0.009)], 8)
        parts.append((P(V, F, "BH_Bone", "vert").scale((1, 0.8, 1)).move((0, yy, z)), SPINE_W))
        parts.append((rtube([(0, yy + 0.01, z), (0, yy + 0.04, z - 0.012)], 0.008, "BH_Bone", n=4, r1=0.005),
                      SPINE_W))
    return parts


def ribcage(body, s=1.0, cy=-0.012, n_ribs=7, z_top=1.435, dz=0.034, sternum=True):
    """Ribs (chest bone) + sternum. Returns parts."""
    parts = []
    rxs = [0.075, 0.10, 0.118, 0.128, 0.13, 0.126, 0.118, 0.11][:n_ribs]
    for i, rx in enumerate(rxs):
        zb = z_top - dz * i
        th_max = math.radians(158 if i < 5 else 128 - 8 * (i - 5))
        ryf = (0.075 + 0.028 * min(i, 3) / 3) * s
        ryb = 0.06 * s
        for sx in (1, -1):
            pts = []
            for t in np.linspace(0, 1, 9):
                th = math.radians(12) + (th_max - math.radians(12)) * t
                x = sx * rx * s * math.sin(th)
                yv = cy + (ryb * math.cos(th) if math.cos(th) > 0 else ryf * math.cos(th))
                z = zb - 0.075 * s * t ** 1.4 + 0.01 * math.sin(math.pi * t)
                pts.append((x, yv, z))
            parts.append(rtube(pts, 0.0085 * s, "BH_Bone", n=5, r1=0.007 * s))
    if sternum:
        zt, zbm = z_top - 0.03, z_top - 0.03 - dz * 4.6
        V, F = M.tube([(0, cy - 0.083 * s, zt), (0, cy - 0.1 * s, (zt + zbm) / 2), (0, cy - 0.094 * s, zbm)],
                      [(0.018 * s, 0.007 * s), (0.016 * s, 0.007 * s), (0.008 * s, 0.006 * s)], n=6, up=(0, -1, 0))
        parts.append(P(V, F, "BH_Bone", "sternum"))
    return parts


def pelvis(body, s=1.0):
    parts = []
    for sx in (1, -1):
        V, F = dome((sx * 0.07 * s, 0.01, 0.985), (sx * 0.8, -0.35, 0.3), 0.075 * s, a_max=65, n=10, rings=3,
                    scale=(1.0, 1.3, 1.0))
        parts.append(M.solidify(P(V, F, "BH_Bone", "ilium"), 0.01, offset=-1))
        parts.append(rtube([(sx * 0.11 * s, -0.01, 0.97), (sx * 0.07 * s, -0.06 * s, 0.91), (0, -0.075 * s, 0.9)],
                           0.013 * s, "BH_Bone", n=6))
    V, F = M.tube([(0, 0.05, 1.0), (0, 0.06, 0.93), (0, 0.045, 0.88)], [(0.045, 0.012), (0.035, 0.012), (0.012, 0.01)],
                  n=6, up=(0, 1, 0))
    parts.append(P(V, F, "BH_Bone", "sacrum"))
    return parts


def bone_arm(body, s, r=1.0, hand=True, hand_scale=0.9):
    """Humerus, radius+ulna, bony fist for side s. Returns list of (part, bone)."""
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    out = []
    out.append((body.limb(ua, [(0.0, 0.03 * r, 0.03 * r), (0.1, 0.02 * r, 0.02 * r), (0.5, 0.017 * r, 0.017 * r),
                                (0.9, 0.02 * r, 0.02 * r), (1.0, 0.03 * r, 0.026 * r)], "BH_Bone", n=7), ua))
    L = body.p["fore_len"]
    for dx, rr in ((0.012, 0.012), (-0.012, 0.0135)):
        pts = body.lpt(fa, [(dx * r, u * L, 0.0) for u in (0.02, 0.2, 0.6, 0.97)])
        out.append((rtube(pts, rr * r, "BH_Bone", n=5, r1=rr * 1.2 * r), fa))
    if hand:
        for prt in fist(body, s, "BH_Bone", "BH_Bone", gauntlet=False, scale=hand_scale):
            out.append((prt, ha))
    return out


def bone_leg(body, s, r=1.0, foot=True):
    th, sh = "thigh." + s, "shin." + s
    out = []
    out.append((body.limb(th, [(-0.02, 0.034 * r, 0.034 * r), (0.08, 0.024 * r, 0.024 * r), (0.5, 0.021 * r, 0.022 * r),
                                (0.92, 0.026 * r, 0.026 * r), (1.0, 0.036 * r, 0.03 * r)], "BH_Bone", n=7), th))
    k = body.head(sh)
    out.append((ball(k + (0, -0.03 * r, 0.01), 0.02 * r, "BH_Bone", 7, 4, (1, 0.6, 1.1)), sh))
    L = body.p["knee_h"] - body.p["ankle_h"]
    for dx, rr in ((0.0, 0.02), (0.022, 0.01)):
        pts = body.lpt(sh, [(dx * r, u * L, 0.0) for u in (0.03, 0.15, 0.6, 0.97)])
        out.append((rtube(pts, rr * 1.25 * r, "BH_Bone", n=6, r1=rr * r), sh))
    return out


def boot(body, s, mat="BH_Leather", top=0.30, r=1.0, wrap_mat=None):
    """Rotten boot: shaft to `top` height, foot + toe. Returns (part, bone) list."""
    hx = body.p["hip_x"] * (1 if s == "L" else -1)
    sh = "shin." + s
    out = []
    k, a = body.head(sh), body.tail(sh)
    u = (top - a[2]) / (k[2] - a[2])
    pts = [a + (0, 0.006, 0.02), a + (k - a) * (u * 0.5), a + (k - a) * u]
    V, F = M.tube(pts, [(0.045 * r, 0.05 * r), (0.043 * r, 0.047 * r), (0.05 * r, 0.054 * r)], n=10, up=(0, -1, 0))
    shaft = P(V, F, mat, "boot")
    shaft.warp(lambda v: (v[0], v[1], v[2] - 0.012 * math.sin(v[0] * 60 + v[1] * 40) * smoothstep(top - 0.06, top, v[2])))
    out.append((shaft, sh))
    if wrap_mat:
        for zz in np.linspace(a[2] + 0.06, top - 0.03, 3):
            c = a + (k - a) * ((zz - a[2]) / (k[2] - a[2]))
            V, F = M.tube([c + (0, 0, -0.01), c + (0, -0.01, 0.012)], [(0.05 * r, 0.055 * r)] * 2, n=10, up=(0, -1, 0))
            out.append((P(V, F, wrap_mat, "wrap"), sh))

    def rings(spec):
        R = []
        for y, w, tp in spec:
            pts = []
            for i in range(10):
                ang = 2 * math.pi * i / 10
                c, sn = math.cos(ang), math.sin(ang)
                x = w * r * np.sign(c) * abs(c) ** 0.8
                z = tp / 2 + tp / 2 * np.sign(sn) * abs(sn) ** 0.7
                pts.append((hx + x, y * r, max(z * r, 0.012)))
            R.append(np.array(pts))
        return R
    foot = rings([(0.06, 0.034, 0.075), (0.04, 0.042, 0.105), (0.0, 0.046, 0.11), (-0.06, 0.047, 0.085),
                  (-0.12, 0.045, 0.06)])
    V, F = M.loft(foot[::-1])
    out.append((P(V, F, mat, "bootfoot"), "foot." + s))
    toe = rings([(-0.115, 0.045, 0.06), (-0.17, 0.042, 0.05), (-0.21, 0.03, 0.04), (-0.228, 0.012, 0.028)])
    V, F = M.loft(toe[::-1])
    out.append((P(V, F, mat, "boottoe"), "toe." + s))
    return out


# =================================================================================================== weapon
def notched_sword(length=0.84, mat="BH_Rust"):
    blade = WP._blade(0.1, length, 0.05, 0.036, 0.006, tip=0.12, n_sec=24, mat=mat)
    notches = [(0.34, 1, 0.4), (0.52, -1, 0.3), (0.63, 1, 0.45), (0.45, 1, 0.2)]

    def w(v):
        x = v[0]
        for zn, side, dpt in notches:
            if x * side > 0.004:
                x *= 1 - dpt * math.exp(-((v[2] - zn) / 0.013) ** 2)
        # bent tip
        yb = 0.012 * max(v[2] - (length - 0.2), 0) / 0.2
        return (x + 0.01 * max(v[2] - (length - 0.25), 0) / 0.25, v[1] + yb, v[2])
    blade.warp(w)
    parts = [blade,
             M.bevel(WP._crossguard(0.09, 0.1, mat="BH_DarkSteel"), 0.003, 1),
             WP._grip(-0.085, 0.078, 0.0155, 5, mat="BH_Leather"),
             WP._pommel(-0.1, 0.026, mat="BH_DarkSteel")]
    return parts


# =================================================================================================== armour
def kettle_helm(body, s=1.12, tilt=(-12, 7), mat="BH_DarkSteel", rim_mat="BH_Rust", brim=0.15):
    hz = body.head("head")[2]
    c = np.array([0, 0.016, hz + 0.118 * s])
    prof = [(0.0, 0.09), (0.035, 0.087), (0.065, 0.074), (0.086, 0.048), (0.094, 0.018), (0.096, 0.0)]
    V, F = M.lathe([(r * s, z * s) for r, z in prof], 16, cap=False)
    Fr = [tuple(reversed(f)) for f in F]
    dome_p = M.solidify(P(V, F, mat, "helm"), 0.006, offset=1)
    # brim: flared, drooping ring
    rings = []
    for rr, dz in ((0.094, 0.0), (0.12, -0.012), (brim, -0.03), (brim + 0.012, -0.042)):
        ring = []
        for i in range(20):
            a = 2 * math.pi * i / 20
            ring.append((rr * s * math.cos(a), rr * s * math.sin(a) * 1.06, dz * s))
        rings.append(np.array(ring))
    V, F = M.loft(rings, cap0=False, cap1=False)
    brim_p = M.solidify(P(V, F, mat, "brim"), 0.006, offset=1)
    # ridge over the crown (front-back)
    ridge = rtube([(0, (0.09 * math.sin(a)) * s, 0.09 * math.cos(a) * s + 0.004) for a in np.linspace(-1.3, 1.3, 9)],
                  0.008 * s, rim_mat, n=5, up=(1, 0, 0))
    rim = []
    for i in range(21):
        a = 2 * math.pi * i / 20
        rim.append(((brim + 0.012) * s * math.cos(a), (brim + 0.012) * s * math.sin(a) * 1.06, -0.042 * s))
    V, F = M.tube(rim, [(0.006 * s, 0.006 * s)] * len(rim), n=5, up=(0, 0, 1), cap0=False, cap1=False)
    rim_p = P(V, F, rim_mat, "helm_rim")
    parts = [dome_p, brim_p, rim_p]
    # dents
    dent(dome_p, (0.05 * s, -0.05 * s, 0.06 * s), (-1, 1, -0.5), 0.018 * s, 0.03 * s)
    dent(dome_p, (-0.06 * s, 0.02 * s, 0.07 * s), (1, 0, -0.6), 0.012 * s, 0.028 * s)
    for p in (brim_p, rim_p):
        dent(p, (-0.12 * s, -0.1 * s, -0.03 * s), (0, 0, 1), 0.02 * s, 0.05 * s)
    for p in parts:
        p.rot(Rx(tilt[0]) @ Ry(tilt[1])).move(c)
    return parts


def rust_pauldron(body, s="L", r=0.12, mat="BH_Rust", trim="BH_DarkSteel", lames=1, flat=0.62):
    parts = []
    sh = body.head("upper_arm." + s)
    el = body.head("forearm." + s)
    sx = 1 if s == "L" else -1
    armdir = normalize(el - sh)
    axis = normalize(np.array([0.8 * sx, 0.0, 0.75]))
    c = sh + np.array([0.004 * sx, 0.0, -0.004])
    V, F = dome((0, 0, 0), (0, 0, 1), r, a_max=72, n=14, rings=5, scale=(1.0, 1.12, flat))
    Ra = M_align_z(axis, (0, 0, 1))
    V = V @ Ra.T + c + axis * r * (1 - flat) * 0.4
    d = M.solidify(P(V, F, mat, "pauldron"), 0.007, offset=-1)
    dent(d, c + axis * r + np.array([0, -0.04, 0]), -axis, 0.015, 0.03)
    parts.append(d)
    Rm = M_align_z(axis, (0, 0, 1))
    rim = []
    for i in range(19):
        a = 2 * math.pi * i / 18
        rr, z = r * math.sin(math.radians(72)), r * math.cos(math.radians(72)) * flat + r * (1 - flat) * 0.4
        rim.append(c + Rm @ np.array([rr * math.cos(a), rr * math.sin(a) * 1.12, z]))
    V, F = M.tube(rim, [(0.007, 0.007)] * len(rim), n=5, up=axis, cap0=False, cap1=False)
    parts.append(P(V, F, trim, "prim"))
    out = np.array([float(sx), 0, 0])
    ax_side = normalize(out - armdir * np.dot(out, armdir))
    ax_fwd = np.cross(armdir, ax_side)
    for i in range(lames):
        rr = r * 0.8 - 0.008 * i
        ctr = sh + armdir * (0.09 + 0.05 * i)
        loops = []
        for z_off in (0.0, 0.05):
            loop = []
            for k in range(11):
                a = math.radians(-100 + 200 * k / 10)
                pdir = ax_side * math.cos(a) + ax_fwd * math.sin(a) * 1.1
                loop.append(ctr + armdir * (z_off - 0.025) + pdir * (rr + 0.01 * (z_off > 0)))
            loops.append(np.array(loop))
        if sx < 0:
            loops = [l[::-1] for l in loops]
        V, F = M.loft(loops, cap0=False, cap1=False, closed=False)
        parts.append(M.solidify(P(V, F, mat, "lame"), 0.005, offset=1))
    return parts


# =================================================================================================== build
def build(body: Body):
    add = body.add
    # ---- skeleton
    for prt in skull(body):
        add(prt, "head")
    for z in np.arange(1.495, 1.61, 0.032):
        V, F = M.lathe([(0, -0.008), (0.022, -0.007), (0.024, 0.0), (0.022, 0.007), (0, 0.008)], 8)
        add(P(V, F, "BH_Bone", "cvert").move((0, 0.012, z)), weights=NECK_W if z < 1.51 else None,
            bone=None if z < 1.51 else "neck")
    add(rtube([(0, 0.02, 1.47), (0, 0.01, 1.62)], 0.013, "BH_Bone", n=6), weights=NECK_W)
    for prt, w in spine_column(body):
        add(prt, weights=w)
    for prt in ribcage(body):
        add(prt, "chest")
    for prt in pelvis(body):
        add(prt, "hips")
    for sx, s in ((1, "L"), (-1, "R")):
        sh = body.head("upper_arm." + s)
        add(rtube([(sx * 0.02, -0.075, 1.445), (sx * 0.1, -0.05, 1.462), (sh[0] - sx * 0.01, -0.01, sh[2] + 0.02)],
                  0.011, "BH_Bone", n=5), "shoulder." + s)
        # scapula
        V, F = M.prism([(0.0, 0.0), (0.02, -0.12), (0.09, 0.03)], 0.008, axis="y")
        sc = P(V, F, "BH_Bone", "scapula")
        if sx < 0:
            sc = sc.mirrored(False)
        add(sc.move((sx * 0.07, 0.075, 1.44)), "chest")
        add(ball(sh + (0, 0, 0.0), 0.03, "BH_Bone", 8, 5), "upper_arm." + s)
        for prt, b in bone_arm(body, s):
            add(prt, b)
        for prt, b in bone_leg(body, s):
            add(prt, b)
        for prt, b in boot(body, s, top=0.3, wrap_mat="BH_Cloth_Primary" if s == "R" else None):
            add(prt, b)

    # ---- surcoat: back panel (shoulders to knees), front skirt from the belt, torn right-chest flap
    def half_back(z):
        return 0.15 if z > 1.2 else 0.13 + 0.06 * (1.2 - z)
    add(cloth_panel(ENV, 1.47, 0.52, half_back, front=False, nu=10, nv=13, seed=2.0, rag=0.08, teeth=5),
        weights=cloth_w())
    add(cloth_panel(ENV, 1.07, 0.55, lambda z: 0.125 + 0.07 * (1.07 - z), front=True, nu=9, nv=8, seed=0.7,
                    rag=0.09, teeth=4), weights=cloth_w())
    # right-chest flap: hangs from the right shoulder, torn off at the sternum
    nu, nv = 6, 6

    def flap(u, v):
        x = -0.155 + 0.13 * u - 0.03 * v * u
        z = 1.47 - (0.2 + ragged(u, 5.0, 0.08, 2)) * v - 0.02 * u
        return (x, front_y(ENV, x, z) - 0.014, z)
    V, F = M.grid(flap, nu, nv)
    add(M.solidify(P(V, F, "BH_Cloth_Primary", "flap"), 0.008, offset=1.0), weights=cloth_w())
    # shoulder straps joining front flap / back panel
    for sx in (1, -1):
        pts = [(sx * 0.13, front_y(ENV, 0.13, 1.44) - 0.012, 1.45), (sx * 0.14, 0.0, 1.5),
               (sx * 0.13, back_y(ENV, 0.13, 1.44) + 0.012, 1.45)]
        V, F = M.tube(pts, [(0.022, 0.005)] * 3, n=4, up=(0, 0, 1), p=3.0)
        add(P(V, F, "BH_Cloth_Primary", "strap"), "chest")
    # belt with a rusty buckle
    V, F = thick_band(ENV, 1.035, 1.075, 0.026, 0.012, n=20)
    add(P(V, F, "BH_Leather", "belt"), "hips")
    by = front_y(ENV, 0, 1.055) - 0.03
    V, F = M.box(0.055, 0.012, 0.05, center=(0.02, by, 1.055))
    add(P(V, F, "BH_Rust", "buckle"), "hips")
    # a hanging belt tail
    add(rtube([(0.05, by, 1.04), (0.06, by - 0.01, 0.95), (0.055, by - 0.02, 0.88)], 0.01, "BH_Leather", n=4),
        weights=cloth_w())

    # ---- armour bits
    for prt in kettle_helm(body):
        add(prt, "head")
    for prt in rust_pauldron(body, "L", r=0.105, flat=0.7):
        add(prt, "upper_arm.L")
    # right leather bracer (reads the forearm at distance)
    fa = "forearm.R"
    L = body.p["fore_len"]
    V, F = M.tube(body.lpt(fa, [(0, u * L, 0) for u in (0.45, 0.72, 0.98)]), [(0.036, 0.038), (0.035, 0.037),
                                                                             (0.032, 0.034)], n=8, up=(0, 0, 1))
    add(P(V, F, "BH_Leather", "bracer"), fa)
    # left knee cop (rusted)
    k = body.head("shin.L")
    V, F = dome(k + (0, -0.012, 0.0), (0, -1, 0.15), 0.045, a_max=60, n=10, rings=3, scale=(1.1, 1.3, 0.55))
    add(M.solidify(P(V, F, "BH_Rust", "poleyn"), 0.006, offset=-1),
        weights=lambda V: [{"thigh.L": 0.5, "shin.L": 0.5}] * len(V))

    # ---- weapon
    add_weapon(body, "R", notched_sword())


# =================================================================================================== scaling
class Scaled:
    """Author a uniformly scaled character with standard-skeleton coordinates. proportions(k) scales every length
    and the modelling pose is angle based, so scaling standard model-space parts by k lands them on the real rig.
    Landmark queries (head/tail/axes/lpt/limb/weight helpers) answer in standard space; add() scales by k."""

    def __init__(self, real, k, extra_bones=None):
        from bh_body import Body as _B
        self.real, self.k = real, float(k)
        ex = [(n, tuple(np.array(h) / k), tuple(np.array(t) / k), par, z) for (n, h, t, par, z) in (extra_bones or [])]
        self.std = _B(proportions(), extra_bones=ex)
        self.p, self.D, self.rig = self.std.p, self.std.D, self.std.rig

    def __getattr__(self, name):          # head, tail, axes, lpt, limb, seg_weights, skirt_weights, blend2 ...
        return getattr(self.std, name)

    def _w(self, weights):
        if weights is None:
            return None
        k = self.k
        return lambda V, f=weights: f(np.asarray(V) / k)

    def add(self, part, bone=None, weights=None):
        part.V = part.V * self.k
        return self.real.add(part, bone, self._w(weights))

    def add_mirror(self, part, bone=None, weights=None):
        part.V = part.V * self.k
        return self.real.add_mirror(part, bone, self._w(weights))
