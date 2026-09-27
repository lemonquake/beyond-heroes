"""Ranger hero: hunter of the broken frontier (bow / javelin class).

Lean athletic build on the standard skeleton. Short tintable mantle (BH_Cloth_Primary, class tint green) over the
shoulders with a dagged hem and the hood lying down at the nape, fur collar, layered leather jerkin with a laced front and
tan chest plates, split jerkin skirt, belt with pouches, a hunting knife on the right hip and a signal horn on the left,
archery bracer on the left forearm, leather wraps on the right, fingerless gloves, wrapped trousers and soft high
boots. A quiver of fletched arrows rides diagonally on the back with its mouth over the right shoulder (right-hand
draw). Rugged bare face: stubble, swept-back hair tied at the nape.

Same skeleton / proportions / rest pose as the Knight and Mage; exports the whole action library.
Materials use the "ranger" palette (exported as BH_*__ranger so the colours survive in Godot) except the tintable
BH_Cloth_Primary, which the game recolours with the class tint.
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import Body, torso_loft, interp_rows, front_y, back_y, fist, smoothstep, M_align_z
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
from char_mage import ring_frac, strip_tube, round_tube, zspec_w, normalize_rows, panel_w, mantle_w, HEAD
from char_knight import thick_band

PROPS = proportions()
EXTRA_BONES = []
PALETTE = "ranger"
TINTABLE = ("BH_Cloth_Primary",)


def _lin(c):
    return tuple(round(x ** 2.2, 4) for x in c)


PALETTE_COLORS = {
    # preview value = the in-game class tint Color(0.3, 0.55, 0.28) in linear space (the game replaces it anyway)
    "BH_Cloth_Primary": (_lin((0.3, 0.55, 0.28)), 0.0, 0.88, None, 0.0, 1.0),
    "BH_Cloth_Secondary": ((0.045, 0.05, 0.032), 0.0, 0.92, None, 0.0, 1.0),     # moss shirt / trousers
    "BH_Leather": ((0.13, 0.07, 0.036), 0.0, 0.64, None, 0.0, 1.0),              # jerkin, boots, quiver
    "BH_LeatherDark": ((0.05, 0.03, 0.018), 0.0, 0.6, None, 0.0, 1.0),           # belts, straps, gloves
    "BH_Horn": ((0.30, 0.20, 0.11), 0.0, 0.62, None, 0.0, 1.0),                  # tan plates, laces, trims
    "BH_Fur": ((0.15, 0.1, 0.06), 0.0, 0.95, None, 0.0, 1.0),                  # collar
    "BH_Wrap": ((0.16, 0.15, 0.105), 0.0, 0.95, None, 0.0, 1.0),                 # linen leg / arm wraps
    "BH_Bone": ((0.62, 0.57, 0.45), 0.0, 0.62, None, 0.0, 1.0),                  # horn bell, fletching, toggles
    "BH_Wood": ((0.2, 0.12, 0.06), 0.0, 0.7, None, 0.0, 1.0),                    # arrow shafts
    "BH_Bronze": ((0.42, 0.27, 0.12), 1.0, 0.42, None, 0.0, 1.0),                # buckles, rims
    "BH_Steel": ((0.5, 0.5, 0.5), 1.0, 0.38, None, 0.0, 1.0),
    "BH_Skin": ((0.52, 0.34, 0.24), 0.0, 0.55, None, 0.0, 1.0),                  # weathered
    "BH_Hair": ((0.085, 0.05, 0.026), 0.0, 0.62, None, 0.0, 1.0),
    "BH_Shadow": ((0.03, 0.022, 0.02), 0.0, 0.8, None, 0.0, 1.0),
    "BH_EyeWhite": ((0.07, 0.05, 0.035), 0.0, 0.35, None, 0.0, 1.0),
}

# lean body under the clothes (z, rx, ry_front, ry_back, keel)
TORSO = [
    (0.96, 0.146, 0.098, 0.098, 0.00),
    (1.04, 0.132, 0.092, 0.090, 0.02),
    (1.14, 0.134, 0.100, 0.092, 0.05),
    (1.25, 0.150, 0.110, 0.098, 0.09),
    (1.35, 0.162, 0.114, 0.102, 0.08),
    (1.43, 0.162, 0.106, 0.100, 0.04),
    (1.49, 0.134, 0.088, 0.090, 0.00),
    (1.53, 0.078, 0.062, 0.062, 0.00),
]
JG = 0.012          # jerkin offset over the body
TORSO_W = zspec_w([(0.99, "hips"), (1.10, "spine"), (1.22, "spine"), (1.32, "chest")])
HEAD_W = zspec_w([(1.50, "chest"), (1.54, "neck"), (1.58, "neck"), (1.61, "head")])
CHEST_W = zspec_w([(1.20, "spine"), (1.32, "chest")])

# quiver axis (model space): bottom behind the left hip, mouth over the right shoulder
Q_BOT = np.array([0.075, 0.175, 1.0])
Q_TOP = np.array([-0.15, 0.165, 1.555])


def build(body: Body):
    torso(body)
    skirt(body)
    belt(body)
    legs(body)
    arms(body)
    head(body)
    mantle(body)
    collar(body)
    quiver(body)


# ================================================================================================ torso
def torso(body):
    add = body.add
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    add(M.Part(V, F, "BH_Cloth_Secondary", name="shirt"), weights=TORSO_W)
    # jerkin: closed body with a narrow laced slit up the front
    zs = [0.99, 1.06, 1.14, 1.22, 1.30, 1.37, 1.43, 1.475, 1.505]
    nu = 32
    rings = []
    for z in zs:
        t = (z - 0.99) / 0.515
        a0 = 0.012 + 0.03 * t ** 1.5
        rings.append(ring_frac(TORSO, z, JG, a0 + (1 - 2 * a0) * np.linspace(0, 1, nu)))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    add(M.solidify(M.Part(V, F, "BH_Leather", name="jerkin"), 0.008, offset=1.0), weights=TORSO_W)
    # edge piping on the slit
    for k in (0, -1):
        pts = np.array([r[k] for r in rings]) + np.array([0, -0.004, 0])
        add(round_tube(pts, 0.005, "BH_Horn", n=5), weights=TORSO_W)
    # cross lacing
    for z in np.linspace(1.12, 1.44, 8)[:-1]:
        dz = 0.04
        pa = ring_frac(TORSO, z, JG + 0.006, [0.016 + 0.03 * ((z - 0.99) / 0.515) ** 1.5])[0]
        pb = ring_frac(TORSO, z + dz, JG + 0.006, [1 - 0.016 - 0.03 * ((z + dz - 0.99) / 0.515) ** 1.5])[0]
        pc = pa.copy(); pc[0] = -pc[0]
        pd = pb.copy(); pd[0] = -pd[0]
        add(round_tube([pa, (pa + pb) / 2 + np.array([0, -0.004, 0]), pb], 0.0028, "BH_Horn", n=4), weights=TORSO_W)
        add(round_tube([pc, (pc + pd) / 2 + np.array([0, -0.004, 0]), pd], 0.0028, "BH_Horn", n=4), weights=TORSO_W)
    # tan chest plates (layered leather), stitched down with dark piping
    for sgn in (1, -1):
        rr = []
        for z in (1.27, 1.31, 1.36, 1.41, 1.45):
            f0, f1 = 0.05, 0.19
            fr = np.linspace(f0, f1, 9) if sgn > 0 else 1 - np.linspace(f1, f0, 9)
            q = ring_frac(TORSO, z, JG + 0.009, fr)
            rr.append(q)
        V, F = M.loft(rr, cap0=False, cap1=False, closed=False)
        pl = M.Part(V, F, "BH_Horn", name="chestplate")
        add(M.solidify(pl, 0.006, offset=1.0, bevel_w=0.0015), weights=CHEST_W)
        edge = np.array([r[0 if sgn > 0 else -1] for r in rr]) + np.array([0, -0.006, 0])
        add(round_tube(edge, 0.0035, "BH_LeatherDark", n=4), weights=CHEST_W)
        bot = rr[0] + np.array([0, -0.004, 0.002])
        add(round_tube(bot, 0.0035, "BH_LeatherDark", n=4), weights=CHEST_W)
    # side seams (darker leather strips) under the arms
    for sx in (1, -1):
        pts = [ring_frac(TORSO, z, JG + 0.008, [0.25 if sx > 0 else 0.75])[0] for z in np.linspace(1.08, 1.40, 6)]
        add(strip_tube(pts, 0.026, 0.004, "BH_LeatherDark", up=[(sx, 0, 0)] * 6), weights=TORSO_W)


# ================================================================================================ jerkin skirt
def skirt_rows():
    rows = []
    for z in (0.78, 0.84, 0.90, 0.96, 1.02, 1.06):
        t = 1.06 - z
        rows.append((z, 0.150 + 0.19 * t, 0.104 + 0.16 * t, 0.104 + 0.2 * t, 0.0))
    return rows


def skirt(body):
    rows = skirt_rows()
    zs = [r[0] for r in rows]
    for side, sgn in (("L", 1), ("R", -1)):
        for back in (False, True):
            nu = 8
            rings = []
            for z in zs:
                t = (1.06 - z) / 0.28
                gf = 0.018 + 0.03 * t
                sg = 0.006 + 0.02 * t
                sb = 0.004 + 0.012 * t
                a, b = (gf, 0.25 - sg) if not back else (0.25 + sg, 0.5 - sb)
                pts = ring_frac(rows, z, 0.0, np.linspace(a, b, nu), p=2.2)
                ang = np.linspace(0, 1, nu)
                fold = 0.006 * t * np.sin(ang * math.pi * 2 + (0.8 if back else 0.0))
                rad = normalize_rows(pts[:, :2])
                pts[:, 0] += rad[:, 0] * fold
                pts[:, 1] += rad[:, 1] * fold
                if sgn < 0:
                    pts[:, 0] *= -1
                rings.append(pts)
            if sgn < 0:
                rings = [r[::-1] for r in rings]
            w = panel_w(side, back)
            V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
            body.add(M.solidify(M.Part(V, F, "BH_Leather", name="skirt"), 0.007, offset=1.0, bevel_w=0.0015),
                     weights=w)
            hem = rings[0] + np.array([0, 0, 0.008])
            ho = hem.copy()
            ho[:, :2] += normalize_rows(hem[:, :2]) * 0.008
            V, F = M.tube(ho, [(0.005, 0.009)] * len(ho), n=5, up=(0, 0, 1), p=3.0)
            body.add(M.Part(V, F, "BH_Horn", name="skirt_hem"), weights=w)
            # stitched vertical seam in the middle of each panel
            mid = np.array([r[len(r) // 2] for r in rings])
            mo = mid.copy()
            mo[:, :2] += normalize_rows(mid[:, :2]) * 0.008
            body.add(round_tube(mo, 0.0028, "BH_LeatherDark", n=4), weights=w)


# ================================================================================================ belt + gear
def on_belt(frac, dz=0.0, out=0.0):
    p = ring_frac(TORSO, 1.05, JG + 0.028 + out, [frac])[0]
    a = 2 * math.pi * frac - math.pi / 2
    return p + np.array([0, 0, dz]), math.degrees(a) + 90


def pouch(body, frac, size, dz=-0.04):
    p, ang = on_belt(frac, dz, 0.005)
    w, d, h = size
    V, F = M.box(w, d, h)
    body.add(M.bevel(M.Part(V, F, "BH_Leather", name="pouch"), 0.009, 2).rot(Rz(ang)).move(p), "hips")
    V, F = M.box(w * 1.06, d * 1.12, h * 0.42, center=(0, -0.002, h * 0.33))
    body.add(M.bevel(M.Part(V, F, "BH_LeatherDark", name="flap"), 0.007, 1).rot(Rz(ang)).move(p), "hips")
    V, F = M.sphere(0.007, 6, 4, center=(0, -d * 0.62, h * 0.14))
    body.add(M.Part(V, F, "BH_Bone", name="toggle").rot(Rz(ang)).move(p), "hips")


def belt(body):
    V, F = thick_band(TORSO, 1.028, 1.074, JG + 0.024, JG + 0.004, n=28)
    body.add(M.bevel(M.Part(V, F, "BH_LeatherDark", name="belt"), 0.003, 1), "hips")
    by = front_y(TORSO, 0, 1.051) - JG - 0.028
    V, F = M.box(0.056, 0.012, 0.05, center=(0, by, 1.051))
    body.add(M.bevel(M.Part(V, F, "BH_Bronze", name="buckle"), 0.004, 1), "hips")
    V, F = M.box(0.036, 0.016, 0.03, center=(0, by - 0.001, 1.051))
    body.add(M.Part(V, F, "BH_LeatherDark", name="buckle_in"), "hips")
    V, F = M.box(0.006, 0.014, 0.04, center=(0.004, by - 0.004, 1.051))
    body.add(M.Part(V, F, "BH_Bronze", name="prong"), "hips")
    pouch(body, 0.12, (0.07, 0.036, 0.075))
    pouch(body, 0.63, (0.085, 0.04, 0.085), dz=-0.045)
    pouch(body, 0.55, (0.06, 0.034, 0.065), dz=-0.035)
    knife(body)
    horn(body)


def knife(body):
    """Hunting knife in a tooled sheath on the right hip, handle up and slightly forward."""
    top, _ = on_belt(0.83, 0.01, 0.01)
    d = normalize(np.array([-0.08, -0.25, -1.0]))       # down, a little forward and outward
    bot = top + d * 0.22
    pts = [top, top + d * 0.08, top + d * 0.17, bot]
    V, F = M.tube(pts, [(0.024, 0.012), (0.023, 0.012), (0.018, 0.01), (0.004, 0.005)], n=8,
                  up=(1, 0, 0), p=2.6)
    body.add(M.Part(V, F, "BH_Leather", name="sheath"), "hips")
    for u in (0.02, 0.1):
        c = top + d * u
        V, F = M.tube([c - d * 0.006, c + d * 0.006], [(0.027, 0.015)] * 2, n=8, up=(1, 0, 0), p=2.6)
        body.add(M.Part(V, F, "BH_LeatherDark", name="sheath_band"), "hips")
    V, F = M.tube([bot - d * 0.03, bot + d * 0.004], [(0.008, 0.007), (0.004, 0.004)], n=6, up=(1, 0, 0))
    body.add(M.Part(V, F, "BH_Bronze", name="chape"), "hips")
    # guard + antler handle + pommel
    g = top - d * 0.004
    V, F = M.box(0.06, 0.014, 0.01)
    body.add(M.Part(V, F, "BH_Steel", name="guard").rot(M_align_z(-d, (1, 0, 0))).move(g), "hips")
    hp = [g - d * 0.008, g - d * 0.05, g - d * 0.095]
    V, F = M.tube(hp, [(0.012, 0.011), (0.013, 0.012), (0.011, 0.01)], n=7, up=(1, 0, 0))
    body.add(M.Part(V, F, "BH_Horn", name="handle"), "hips")
    V, F = M.sphere(0.014, 8, 5, center=g - d * 0.1, scale=(1.0, 0.8, 0.8))
    body.add(M.Part(V, F, "BH_Bronze", name="pommel"), "hips")


def horn(body):
    """Signal horn slung at the left hip (bell toward the back)."""
    p, _ = on_belt(0.36, -0.07, 0.03)
    pts, prof = [], []
    for i, t in enumerate(np.linspace(0, 1, 9)):
        a = math.radians(-20 + 150 * t)
        pts.append(p + np.array([0.012 * math.sin(math.pi * t), 0.09 * math.cos(a) - 0.02, -0.03 * math.sin(a) + 0.02]))
        r = 0.032 * (1 - t) ** 1.3 + 0.006
        prof.append((r, r))
    V, F = M.tube(pts, prof, n=10, up=(1, 0, 0))
    body.add(M.Part(V, F, "BH_Bone", name="horn"), "hips")
    for k in (0, 1):
        q = pts[k]
        d = normalize(pts[k + 1] - pts[k])
        r = prof[k][0] + 0.003
        V, F = M.tube([q + d * 0.003 * k, q + d * (0.012 + 0.003 * k)], [(r, r)] * 2, n=10, up=(1, 0, 0))
        body.add(M.Part(V, F, "BH_Bronze", name="horn_rim"), "hips")
    V, F = M.tube([pts[-1], pts[-1] + normalize(pts[-1] - pts[-2]) * 0.02], [(0.007, 0.007), (0.006, 0.006)], n=6,
                  up=(1, 0, 0))
    body.add(M.Part(V, F, "BH_Bronze", name="mouthpiece"), "hips")
    top, _ = on_belt(0.36, -0.01, 0.0)
    body.add(round_tube([top, (top + pts[1]) / 2 + np.array([0.01, 0, 0]), pts[1]], 0.0035, "BH_LeatherDark", n=4),
             "hips")
    body.add(round_tube([top, (top + pts[6]) / 2 + np.array([0.012, 0, 0]), pts[6]], 0.0035, "BH_LeatherDark", n=4),
             "hips")


# ================================================================================================ legs
def spiral(body, bone, u0, u1, r, turns, mat, width=0.02, thick=0.005, n_per=10, phase=0.0, L=None):
    """Flat wrap strip spiralling around a bone (model space), radius r (float or fn(u))."""
    A = body.axes(bone)
    o = body.head(bone)
    L = L or float(np.linalg.norm(body.tail(bone) - o))
    n = max(int(turns * n_per), 4)
    pts, ups = [], []
    for i in range(n + 1):
        t = i / n
        u = u0 + (u1 - u0) * t
        a = 2 * math.pi * turns * t + phase
        rr = r(u) if callable(r) else r
        loc = np.array([rr * math.cos(a), u * L, rr * math.sin(a)])
        pts.append(o + A @ loc)
        ups.append(A @ np.array([math.cos(a), 0, math.sin(a)]))
    return strip_tube(pts, width, thick, mat, n=6, up=ups)


def legs(body):
    V, F = torso_loft([(0.84, 0.146, 0.09, 0.098, 0.0), (0.92, 0.148, 0.096, 0.102, 0.0),
                       (1.0, 0.142, 0.094, 0.098, 0.0)], n=24)
    body.add(M.Part(V, F, "BH_Cloth_Secondary", name="seat"),
             weights=body.skirt_weights(0.98, 0.84, max_leg=0.7, center_w=0.05))
    for s in ("L", "R"):
        th, sh = "thigh." + s, "shin." + s
        h, k, a = body.head(th), body.head(sh), body.tail(sh)
        pts = [h + (0, 0, 0.04), h + (k - h) * 0.4, k + (0, 0, 0.02), k + (a - k) * 0.35, k + (a - k) * 0.62]
        prof = [(0.074, 0.078), (0.066, 0.07), (0.052, 0.056), (0.049, 0.052), (0.043, 0.045)]
        V, F = M.tube(pts, prof, n=12, up=(0, -1, 0))
        body.add(M.Part(V, F, "BH_Cloth_Secondary", name="trouser"), weights=body.seg_weights([th, sh], power=10))
        # linen wraps: over the knee down to the boot top, and a band on the lower thigh
        Lsh = float(np.linalg.norm(a - k))
        Lth = float(np.linalg.norm(k - h))
        body.add(spiral(body, sh, 0.05, 0.3, lambda u: 0.056 - 0.012 * u, 3.0, "BH_Wrap", width=0.024, thick=0.005,
                        L=Lsh), sh)
        body.add(spiral(body, th, 0.72, 0.9, lambda u: 0.058 + 0.004 * (1 - u), 1.6, "BH_Wrap", width=0.022,
                        thick=0.005, L=Lth, phase=1.0), th)
        for part, bone in boot(body, s):
            body.add(part, bone)


def boot(body, s):
    sgn = 1 if s == "L" else -1
    hx = PROPS["hip_x"] * sgn
    sh = "shin." + s
    out = []
    k, a = body.head(sh), body.tail(sh)
    pts = [a + (0, 0.004, 0.03), a + (k - a) * 0.3, a + (k - a) * 0.58]
    V, F = M.tube(pts, [(0.049, 0.053), (0.052, 0.056), (0.055, 0.059)], n=14, up=(0, -1, 0), cap1=False)
    out.append((M.solidify(M.Part(V, F, "BH_Leather", name="boot"), 0.004, offset=-1.0), sh))
    # soft slouched fold-over cuff, higher at the front
    c0 = a + (k - a) * 0.56
    rings = []
    for dz, rr in ((0.0, 0.058), (0.035, 0.064), (0.052, 0.066)):
        ring = []
        for i in range(16):
            ang = 2 * math.pi * i / 16
            fwd = -math.cos(ang)       # +1 at the front (-Y)
            ring.append(c0 + np.array([rr * math.sin(ang), -rr * 1.05 * math.cos(ang),
                                       dz + 0.018 * max(fwd, 0) * (dz > 0) - 0.004 * math.sin(3 * ang)]))
        rings.append(np.array(ring))
    V, F = M.loft(rings, cap0=False, cap1=False)
    out.append((M.solidify(M.Part(V, F, "BH_Leather", name="cuff"), 0.005, offset=-1.0, bevel_w=0.0015), sh))
    V, F = M.tube(rings[-1], [(0.004, 0.004)] * 16, n=5, up=(0, 0, 1), cap0=False, cap1=False)
    out.append((M.Part(V, F, "BH_Horn", name="cuff_rim"), sh))
    # front lacing up the shaft
    for i, z in enumerate(np.linspace(0.13, 0.33, 6)):
        y = -0.052 - 0.004
        p0 = np.array([hx - 0.02, y, z])
        p1 = np.array([hx + 0.02, y, z + 0.03])
        q0 = np.array([hx + 0.02, y, z])
        q1 = np.array([hx - 0.02, y, z + 0.03])
        out.append((round_tube([p0, p1], 0.0026, "BH_Horn", n=4), sh))
        out.append((round_tube([q0, q1], 0.0026, "BH_Horn", n=4), sh))

    def rings_(spec):
        R = []
        for y, w, top in spec:
            pts = []
            for i in range(12):
                ang = 2 * math.pi * i / 12
                c, sn = math.cos(ang), math.sin(ang)
                x = w * np.sign(c) * abs(c) ** 0.8
                z = top / 2 + top / 2 * np.sign(sn) * abs(sn) ** 0.7
                pts.append((hx + x, y, max(z, 0.012)))
            R.append(np.array(pts))
        return R
    foot = rings_([(0.065, 0.034, 0.075), (0.045, 0.041, 0.108), (0.0, 0.045, 0.116), (-0.06, 0.046, 0.086),
                   (-0.12, 0.045, 0.062)])
    V, F = M.loft(foot[::-1])
    out.append((M.bevel(M.Part(V, F, "BH_Leather", name="bootfoot"), 0.003, 1, angle=45), "foot." + s))
    toe = rings_([(-0.115, 0.045, 0.062), (-0.168, 0.042, 0.052), (-0.208, 0.031, 0.04), (-0.226, 0.013, 0.028)])
    V, F = M.loft(toe[::-1])
    out.append((M.bevel(M.Part(V, F, "BH_Leather", name="boottoe"), 0.003, 1, angle=45), "toe." + s))
    V, F = M.box(0.092, 0.2, 0.014, center=(hx, -0.03, 0.007))
    out.append((M.bevel(M.Part(V, F, "BH_LeatherDark", name="sole"), 0.004, 1), "foot." + s))
    V, F = M.box(0.074, 0.098, 0.012, center=(hx, -0.178, 0.006))
    out.append((M.bevel(M.Part(V, F, "BH_LeatherDark", name="sole_t"), 0.004, 1), "toe." + s))
    # ankle strap with a bronze buckle on the outside
    V, F = M.tube([(hx, 0.02, 0.105), (hx, -0.012, 0.095)], [(0.049, 0.051), (0.049, 0.051)], n=12, up=(0, -1, 0))
    out.append((M.Part(V, F, "BH_LeatherDark", name="strap"), "foot." + s))
    V, F = M.box(0.01, 0.02, 0.02, center=(hx + 0.049 * sgn, 0.004, 0.1))
    out.append((M.Part(V, F, "BH_Bronze", name="buckle"), "foot." + s))
    return out


# ================================================================================================ arms
def arms(body):
    for s in ("L", "R"):
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
        d = normalize(wr - el)
        # shirt sleeve, slightly loose above the elbow
        pts = [sh + (sh - el) * 0.05, sh + (el - sh) * 0.35, sh + (el - sh) * 0.8, el, el + (wr - el) * 0.35,
               el + (wr - el) * 0.75, wr]
        prof = [(0.056, 0.06), (0.058, 0.062), (0.052, 0.055), (0.05, 0.052), (0.047, 0.049), (0.041, 0.043),
                (0.037, 0.039)]
        V, F = M.tube(pts, prof, n=12, up=(0, -1, 0))
        body.add(M.Part(V, F, "BH_Cloth_Secondary", name="sleeve"), weights=body.seg_weights([ua, fa], power=10))
        # leather arm band on the upper arm
        c = sh + (el - sh) * 0.62
        du = normalize(el - sh)
        V, F = M.tube([c - du * 0.014, c + du * 0.014], [(0.058, 0.061)] * 2, n=12, up=(0, -1, 0))
        body.add(M.Part(V, F, "BH_LeatherDark", name="armband"), ua)
        Lf = PROPS["fore_len"]
        if s == "L":
            bracer_L(body, fa, el, wr, d, Lf)
        else:
            body.add(spiral(body, fa, 0.3, 0.92, lambda u: 0.047 - 0.008 * u, 3.2, "BH_LeatherDark", width=0.022,
                            thick=0.005, L=Lf), fa)
            b = wr - d * 0.012
            V, F = M.tube([b - d * 0.02, b + d * 0.01], [(0.043, 0.045), (0.042, 0.044)], n=12, up=(0, -1, 0))
            body.add(M.Part(V, F, "BH_Leather", name="cuff"), fa)
        for prt in fist(body, s, "BH_Skin", "BH_LeatherDark", gauntlet=True):
            if prt.name == "handplate":
                prt.mat = "BH_LeatherDark"
            elif prt.name == "thumb":
                prt.mat = "BH_Skin"
            body.add(prt, ha)
        # glove cuff at the wrist
        V, F = M.tube([wr - d * 0.005, wr + d * 0.03], [(0.041, 0.043), (0.039, 0.041)], n=12, up=(0, -1, 0))
        body.add(M.Part(V, F, "BH_LeatherDark", name="glove_cuff"), ha)


def bracer_L(body, fa, el, wr, d, Lf):
    """Archery guard: long laced leather bracer with a tooled tan plate on the outer forearm and three straps."""
    b0, b1 = el + (wr - el) * 0.2, wr + (wr - el) * 0.02
    V, F = M.tube([b0, (b0 + b1) / 2, b1], [(0.05, 0.052), (0.047, 0.049), (0.043, 0.045)], n=14, up=(0, -1, 0))
    body.add(M.bevel(M.Part(V, F, "BH_Leather", name="bracer"), 0.003, 1, angle=50), fa)
    A = body.axes(fa)
    o = body.head(fa)

    def fn(u, v):
        uu = 0.24 + 0.72 * v
        rr = 0.052 - 0.007 * (uu - 0.24) / 0.72 + 0.002
        a = math.radians(-58 + 116 * u)
        return o + A @ np.array([rr * math.sin(a), uu * Lf, rr * math.cos(a)])
    V, F = M.grid(fn, 9, 8)
    plate = M.solidify(M.Part(V, F, "BH_Horn", name="guard_plate").flip(), 0.004, offset=1.0, bevel_w=0.0012)
    body.add(plate, fa)
    for uu in (0.34, 0.62, 0.9):
        c = o + A @ np.array([0, uu * Lf, 0])
        rr = 0.057 - 0.007 * (uu - 0.24) / 0.72
        V, F = M.tube([c - d * 0.008, c + d * 0.008], [(rr, rr)] * 2, n=14, up=(0, -1, 0))
        body.add(M.Part(V, F, "BH_LeatherDark", name="bracer_strap"), fa)
        V, F = M.box(0.012, 0.02, 0.018)
        bk = M.Part(V, F, "BH_Bronze", name="bracer_buckle")
        bk.rot(np.stack([A[:, 0], A[:, 1], A[:, 2]], 1)).move(o + A @ np.array([rr + 0.002, uu * Lf, 0.0]))
        body.add(bk, fa)
    # lacing on the inner seam
    for uu in np.linspace(0.3, 0.86, 5):
        p0 = o + A @ np.array([-0.012, uu * Lf, -0.05])
        p1 = o + A @ np.array([0.012, (uu + 0.08) * Lf, -0.048])
        q0 = o + A @ np.array([0.012, uu * Lf, -0.05])
        q1 = o + A @ np.array([-0.012, (uu + 0.08) * Lf, -0.048])
        body.add(round_tube([p0, p1], 0.0024, "BH_Horn", n=4), fa)
        body.add(round_tube([q0, q1], 0.0024, "BH_Horn", n=4), fa)


# ================================================================================================ head
def head(body):
    add = body.add
    V, F = M.tube([(0, 0.0, 1.47), (0, -0.004, 1.54), (0, -0.01, 1.62)], [(0.056, 0.053), (0.051, 0.049), (0.05, 0.05)],
                  n=12, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="neck"), weights=HEAD_W)
    V, F = torso_loft(HEAD, n=22, p=2.1, cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Skin", name="head"), "head")
    # heavy brow, cheekbones, strong nose
    V, F = M.tube([(-0.052, -0.066, 1.714), (-0.02, -0.078, 1.722), (0.0, -0.079, 1.72), (0.02, -0.078, 1.722),
                   (0.052, -0.066, 1.714)], [(0.011, 0.009)] * 5, n=6, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="brow"), "head")
    V, F = M.tube([(0, -0.076, 1.712), (0, -0.088, 1.686), (0, -0.096, 1.663), (0, -0.09, 1.651)],
                  [(0.007, 0.006), (0.009, 0.009), (0.012, 0.01), (0.009, 0.006)], n=6, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="nose"), "head")
    for sx in (1, -1):
        V, F = M.sphere(0.013, 8, 5, center=(sx * 0.029, -0.068, 1.699), scale=(1.15, 0.6, 0.72))
        add(M.Part(V, F, "BH_Shadow", name="socket"), "head")
        V, F = M.sphere(0.0052, 8, 4, center=(sx * 0.029, -0.0718, 1.697), scale=(1.25, 0.7, 0.6))
        add(M.Part(V, F, "BH_EyeWhite", name="eye"), "head")
        # ears
        V, F = M.sphere(0.02, 6, 4, center=(sx * 0.074, 0.0, 1.69), scale=(0.35, 0.8, 1.2))
        add(M.Part(V, F, "BH_Skin", name="ear"), "head")
    # mouth line
    V, F = M.tube([(-0.02, -0.079, 1.632), (0, -0.083, 1.63), (0.02, -0.079, 1.632)], [(0.0025, 0.002)] * 3, n=4,
                  up=(0, -1, 0))
    add(M.Part(V, F, "BH_Shadow", name="mouth"), "head")
    # short beard / heavy stubble along the jaw and chin, moustache
    w = 0.21
    cols = np.linspace(-w, w, 13)
    rows = []
    for t in np.linspace(0, 1, 4):
        r = []
        for f in cols:
            a = abs(f) / w
            zb = 1.575 + 0.05 * a ** 2
            zt = 1.618 + 0.05 * a ** 1.4
            z = zb + (zt - zb) * t
            q = ring_frac(HEAD, max(z, 1.60), 0.004, [f], p=2.1)[0]
            q[2] = z
            if z < 1.6:
                q[1] -= (1.6 - z) * 0.3
            r.append(q)
        rows.append(np.array(r))
    V, F = M.loft(rows, cap0=False, cap1=False, closed=False)
    add(M.solidify(M.Part(V, F, "BH_Hair", name="beard"), 0.006, offset=1.0), "head")
    V, F = M.tube([(-0.03, -0.079, 1.642), (-0.012, -0.087, 1.647), (0.012, -0.087, 1.647), (0.03, -0.079, 1.642)],
                  [(0.005, 0.005), (0.006, 0.006), (0.006, 0.006), (0.005, 0.005)], n=6, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Hair", name="moustache"), "head")
    hair(body)
    hood_down(body)


def hair(body):
    """Swept-back hair: cap over the head from a hairline above the brow to the nape, strand ridges, tied tail."""
    rows = [(r[0], r[1] + 0.009, r[2] + 0.009, r[3] + 0.012) + tuple(r[4:]) for r in HEAD if r[0] < 1.77]
    rows += [(1.795, 0.078, 0.066, 0.096, 0.0, 0.004), (1.815, 0.064, 0.052, 0.08, 0.0, 0.007),
             (1.83, 0.042, 0.034, 0.054, 0.0, 0.01), (1.838, 0.012, 0.01, 0.016, 0.0, 0.012)]
    nu = 28
    rings = []
    for v in np.linspace(0, 1, 7):
        ring = []
        for i in range(nu):
            f = i / nu
            back = 0.5 - 0.5 * math.cos(2 * math.pi * f)
            side = abs(math.sin(2 * math.pi * f))
            z0 = 1.752 + (1.615 - 1.752) * back ** 1.6 - 0.012 * side * (1 - back)
            z = z0 + (1.838 - z0) * v ** 0.75
            q = ring_frac(rows, min(z, 1.838), 0.0, [f], p=2.1)[0]
            q[2] = z
            # swept-back strands: ridges running from the hairline over the crown
            ring.append(q)
        rings.append(np.array(ring))
    V, F = M.loft(rings, cap0=False, cap1=True)
    body.add(M.Part(V, F, "BH_Hair", name="hair"), "head")
    # swept-back locks: each runs from the hairline over the crown and down to the nape

    def S(f, v):
        back = 0.5 - 0.5 * math.cos(2 * math.pi * f)
        side = abs(math.sin(2 * math.pi * f))
        z0 = 1.752 + (1.615 - 1.752) * back ** 1.6 - 0.012 * side * (1 - back)
        z = z0 + (1.838 - z0) * v ** 0.75
        q = ring_frac(rows, min(z, 1.838), 0.0, [f], p=2.1)[0]
        q[2] = z
        return q
    ctr = np.array([0.0, 0.01, 1.70])
    for k, f in enumerate(np.linspace(-0.19, 0.19, 11)):
        vs = [0.0, 0.3, 0.6, 0.85, 0.97]
        pts = [S(f, v) for v in [0.06] + vs[1:]] + [S(0.5 - f, v) for v in vs[::-1][1:]]
        pts = np.array(pts)
        nrm = [normalize(p - ctr) for p in pts]
        pts = pts + np.array(nrm) * 0.004
        pts[0] -= nrm[0] * 0.003       # front of each lock tucks into the hairline
        n = len(pts)
        prof = []
        for i in range(n):
            t = i / (n - 1)
            w = 0.02 + 0.01 * math.sin(math.pi * min(t * 1.4, 1.0))
            prof.append((w * (0.4 if i == n - 1 else 0.7 if i == 0 else 1.0), 0.008 * (0.25 if i in (0, n - 1) else 1.0)))
        V, F = M.tube(pts, prof, n=6, up=nrm, p=2.4)
        body.add(M.Part(V, F, "BH_Hair", name="lock"), "head")
    # tied tail at the nape
    pts = [(0, 0.094, 1.668), (0, 0.114, 1.64), (0, 0.124, 1.61), (0, 0.122, 1.585), (0, 0.112, 1.565)]
    V, F = M.tube(pts, [(0.021, 0.017), (0.026, 0.021), (0.022, 0.018), (0.014, 0.011), (0.004, 0.004)], n=8,
                  up=(0, 1, 0))
    body.add(M.Part(V, F, "BH_Hair", name="tail"), weights=zspec_w([(1.56, "neck"), (1.62, "head")]))
    V, F = M.tube([(0, 0.098, 1.652), (0, 0.103, 1.638)], [(0.02, 0.018)] * 2, n=8, up=(0, 1, 0))
    body.add(M.Part(V, F, "BH_LeatherDark", name="hair_tie"), "head")


def hood_down(body):
    """Hood lowered: a soft bunched cowl lying on the upper back, opening up, with a short pointed tip."""
    c = np.array([0.03, 0.118, 1.47])
    V, F = M.sphere(0.1, 16, 8, center=(0, 0, 0), scale=(1.0, 0.5, 0.72))
    hood = M.Part(V, F, "BH_Cloth_Primary", name="hood_down")

    def w(v):
        x, y, z = v
        # squash the front half flat against the back, make a soft fold ridge
        y = y if y > 0 else y * 0.35
        z = z - 0.012 * math.cos(3.0 * math.atan2(x, y + 1e-6)) * (z > 0)
        return (x, y, z)
    hood.warp(w).move(c)
    body.add(hood, "chest")
    # open rim (turned back edge) + dark inside
    rim = []
    for i in range(21):
        a = 2 * math.pi * i / 20
        rim.append(c + np.array([0.078 * math.cos(a), 0.028 + 0.03 * math.sin(a), 0.068 - 0.006 * math.sin(a)]))
    V, F = M.tube(rim, [(0.009, 0.009)] * len(rim), n=6, up=(0, 0, 1), cap0=False, cap1=False)
    body.add(M.Part(V, F, "BH_Cloth_Primary", name="hood_rim"), "chest")
    V, F = M.sphere(0.074, 12, 4, center=c + np.array([0, 0.028, 0.062]), scale=(1.0, 0.4, 0.12))
    body.add(M.Part(V, F, "BH_Shadow", name="hood_in"), "chest")
    # pointed tip falling down the back
    tip = [c + np.array([0.0, 0.05, -0.04]), c + np.array([0.004, 0.06, -0.1]), c + np.array([0.01, 0.052, -0.17])]
    V, F = M.tube(tip, [(0.04, 0.016), (0.026, 0.012), (0.004, 0.004)], n=8, up=(0, 1, 0))
    body.add(M.Part(V, F, "BH_Cloth_Primary", name="hood_tip"), "chest")


# ================================================================================================ mantle + collar
def mantle(body):
    nu, nv = 56, 7
    gap = math.radians(11)
    rings = []
    teeth = 16
    for j in range(nv):
        v = j / (nv - 1)
        ring = []
        for i in range(nu):
            th = gap + (2 * math.pi - 2 * gap) * i / (nu - 1)
            st, ct = math.sin(th), math.cos(th)
            fr, bk = max(ct, 0.0), max(-ct, 0.0)
            rx = 0.10 + 0.20 * v
            ry = (0.086 + 0.10 * v) if ct > 0 else (0.09 + 0.11 * v)
            drop = 0.135 + 0.055 * fr ** 2 + 0.16 * bk ** 2 + 0.07 * bk ** 10
            saw = abs(((th * teeth / (2 * math.pi)) % 1.0) - 0.5) * 2      # 0..1 triangle wave -> dagged hem
            z = 1.575 - drop * v ** 2 - 0.028 * saw * v ** 5
            x, y = rx * st, 0.012 - ry * ct
            # drape onto the body below the shoulders (front and back)
            if z < 1.47 and abs(x) < 0.15:
                if ct < 0:
                    y = min(y, back_y(TORSO, x, max(z, 1.0)) + JG + 0.03 + 0.02 * (1 - bk))
                else:
                    y = max(y, front_y(TORSO, x, max(z, 1.0)) - JG - 0.032 - 0.02 * (1 - fr))
            ring.append((x, y, z))
        rings.append(np.array(ring))
    rings = rings[::-1]
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    body.add(M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="mantle"), 0.009, offset=1.0), weights=mantle_w())
    hem = rings[0] + np.array([0, 0, 0.003])
    V, F = M.tube(hem, [(0.0055, 0.0055)] * len(hem), n=5, up=(0, 0, 1))
    body.add(M.Part(V, F, "BH_Horn", name="mantle_hem"), weights=mantle_w())
    # front edges piping
    for k in (0, -1):
        e = np.array([r[k] for r in rings])
        V, F = M.tube(e, [(0.005, 0.005)] * len(e), n=5, up=(0, -1, 0))
        body.add(M.Part(V, F, "BH_Horn", name="mantle_edge"), weights=mantle_w())
    # antler-toggle clasp at the throat
    for sx in (1, -1):
        c = np.array([sx * 0.03, -0.102, 1.49])
        V, F = M.lathe([(0, -0.005), (0.013, -0.004), (0.015, 0.003), (0, 0.005)], 10)
        body.add(M.Part(V, F, "BH_Bronze", name="clasp").rot(Rx(90)).move(c), "chest")
    V, F = M.tube([(-0.045, -0.114, 1.498), (0.0, -0.118, 1.49), (0.045, -0.114, 1.482)],
                  [(0.008, 0.008), (0.009, 0.009), (0.006, 0.006)], n=6, up=(0, -1, 0))
    body.add(M.Part(V, F, "BH_Bone", name="toggle"), "chest")


def collar(body):
    """Fur collar: lumpy roll around the neck line over the mantle, with tufts."""
    n = 40
    pts, prof, W = [], [], []
    for i in range(n + 1):
        th = 2 * math.pi * i / n
        fr = max(-math.cos(th), 0.0)      # front at th = pi
        x, y = 0.1 * math.sin(th), 0.012 + 0.094 * math.cos(th)
        z = 1.582 - 0.04 * fr ** 2
        pts.append((x, y, z))
        r = 0.026 + 0.006 * math.sin(7 * th) + 0.004 * math.sin(13 * th + 1)
        prof.append((r, r * 0.8))
    V, F = M.tube(pts, prof, n=8, up=(0, 0, 1), cap0=False, cap1=False)
    body.add(M.Part(V, F, "BH_Fur", name="collar"), weights=zspec_w([(1.5, "chest"), (1.6, "neck")]))
    for i in range(28):
        th = 2 * math.pi * (i + 0.5) / 28
        fr = max(-math.cos(th), 0.0)
        base = np.array([0.1 * math.sin(th), 0.012 + 0.094 * math.cos(th), 1.582 - 0.04 * fr ** 2])
        out = normalize(np.array([math.sin(th), math.cos(th), 0.9 + 0.3 * math.sin(3 * th)]))
        L = 0.036 + 0.01 * math.sin(5 * th)
        V, F = M.tube([base, base + out * L * 0.55, base + out * L + np.array([0, 0, -0.016])],
                      [(0.016, 0.011), (0.011, 0.008), (0.002, 0.002)], n=5, up=(0, 0, 1))
        body.add(M.Part(V, F, "BH_Fur", name="tuft"), weights=zspec_w([(1.5, "chest"), (1.6, "neck")]))


# ================================================================================================ quiver
def quiver(body):
    add = body.add
    d = normalize(Q_TOP - Q_BOT)
    L = float(np.linalg.norm(Q_TOP - Q_BOT))
    side = normalize(np.cross(d, np.array([0, 1.0, 0])))     # across the quiver, in the back plane
    back = normalize(np.cross(side, d))                      # away from the body (+Y)
    if back[1] < 0:
        back = -back

    def P(u, a=0.0, b=0.0):
        return Q_BOT + d * (u * L) + side * a + back * b
    pts = [P(u) for u in (0.0, 0.05, 0.4, 0.8, 0.97, 1.0)]
    prof = [(0.035, 0.026), (0.042, 0.03), (0.046, 0.033), (0.05, 0.036), (0.054, 0.038), (0.055, 0.039)]
    V, F = M.tube(pts, prof, n=14, up=back, p=2.2, cap0=True, cap1=False)
    add(M.solidify(M.Part(V, F, "BH_Leather", name="quiver"), 0.004, offset=-1.0), "chest")
    # rims and bands
    for u, r, w, mat in ((1.0, (0.058, 0.041), 0.02, "BH_Horn"), (0.86, (0.053, 0.038), 0.016, "BH_LeatherDark"),
                         (0.3, (0.047, 0.034), 0.016, "BH_LeatherDark"), (0.02, (0.04, 0.03), 0.03, "BH_Horn")):
        c = P(u)
        V, F = M.tube([c - d * w / 2, c + d * w / 2], [r, r], n=14, up=back, p=2.2, cap0=False, cap1=False)
        add(M.solidify(M.Part(V, F, mat, name="quiver_band"), 0.003, offset=1.0), "chest")
    # tooled centre strip + stitched edge
    strip = [P(u, 0, 0.0) + back * (0.034 + 0.005 * u) for u in np.linspace(0.34, 0.82, 6)]
    add(strip_tube(strip, 0.03, 0.004, "BH_Horn", up=[back] * 6), "chest")
    V, F = M.lathe([(0, 0), (0.012, 0.0), (0.012, 0.006), (0, 0.006)], 8)
    for u in (0.44, 0.58, 0.72):
        stud = M.Part(V.copy(), list(F), "BH_Bronze", name="stud").rot(M_align_z(back)).move(P(u) + back * 0.038)
        add(stud, "chest")
    # arrows: shafts fanning slightly out of the mouth, bone / brown fletching, nocks
    rng = np.random.default_rng(11)
    offs = [(-0.022, -0.012), (0.0, -0.016), (0.022, -0.01), (-0.03, 0.008), (-0.01, 0.004), (0.012, 0.006),
            (0.03, 0.01), (-0.015, 0.02), (0.008, 0.022), (0.024, 0.024)]
    for k, (a, b) in enumerate(offs):
        ext = 0.10 + 0.05 * rng.random()
        dd = normalize(d + side * a * 0.9 + back * b * 0.6)
        start = P(0.62, a, b)
        mouth = P(1.0, a, b)
        tipp = mouth + dd * ext
        V, F = M.tube([start, mouth, tipp], [(0.0045, 0.0045)] * 3, n=5, up=back)
        add(M.Part(V, F, "BH_Wood", name="shaft"), "chest")
        V, F = M.tube([tipp, tipp + dd * 0.012], [(0.0055, 0.0055), (0.0045, 0.0045)], n=5, up=back)
        add(M.Part(V, F, "BH_Horn" if k % 3 else "BH_Bone", name="nock"), "chest")
        mat = "BH_Bone" if k % 3 != 1 else "BH_Fur"
        Rm = M_align_z(dd, back)
        spin = 25.0 * k
        for j in range(3):
            o = np.array([(0.0, 0.0), (0.0145, 0.012), (0.0145, 0.062), (0.004, 0.075), (0.0, 0.074)])
            Vv, Fv = M.prism(o, 0.0022, axis="y")
            vane = M.Part(Vv, Fv, mat, name="vane")
            vane.move((0.003, 0, 0)).rot(Rz(spin + 120 * j)).rot(Rm).move(tipp - dd * 0.085)
            add(vane, "chest")
    # carrying strap: from the quiver mouth over the right shoulder, diagonally across the chest to the left hip
    front = []
    for t in np.linspace(0, 1, 9):
        x = -0.13 + 0.27 * t
        z = 1.40 - 0.35 * t
        front.append((x, front_y(TORSO, x, z) - JG - 0.016, z))
    add(strip_tube(front, 0.034, 0.006, "BH_LeatherDark", up=[(0.2 * p[0], -1, 0) for p in front]), weights=TORSO_W)
    bc = np.array(front[4]) + np.array([0, -0.006, 0])
    V, F = M.box(0.036, 0.01, 0.04)
    add(M.bevel(M.Part(V, F, "BH_Bronze", name="strap_buckle"), 0.003, 1).rot(Ry(-38)).move(bc), weights=TORSO_W)
    # lower strap from the quiver foot around the left flank
    low = []
    for t in np.linspace(0, 1, 6):
        fr = 0.44 - 0.2 * t
        q = ring_frac(TORSO, 1.06 + 0.02 * t, JG + 0.03, [fr])[0]
        low.append(q)
    low = [P(0.08) + back * 0.0] + low
    add(strip_tube(low, 0.026, 0.005, "BH_LeatherDark", up=[(0, 0, 1)] * len(low)), weights=TORSO_W)
