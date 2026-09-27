"""Shadowblade hero: an assassin who walks between the lights (dual daggers / claws class).

Slim, agile build on the standard skeleton. Fitted charcoal leathers: quilted leather vest over a dark tunic, two
crossed chest straps carrying throwing knives around a dull-silver ring, a layered dark-steel pauldron on the left
shoulder only, dark-steel tassets on the right hip, low-slung belt with front and back flaps, a sheathed knife on the
left thigh. Deep peaked hood (shadowed lining) with a cloth mask over the lower face and faint violet eyes (BH_Emissive).
Long tattered scarf (tintable BH_Cloth_Primary, class tint violet) wrapped at the throat with two tails down the back on
scarf.1 / scarf.2 bones, and a waist sash (same cloth) knotted on the left hip with a tail on the sash.1 bone
(secondary motion in secondary()). Wrapped forearms, dark-steel knuckle gloves, soft wrapped boots.

Same skeleton / proportions / rest pose as the Knight and Mage; exports the whole action library.
Materials use the "shadowblade" palette (exported as BH_*__shadowblade) except the tintable BH_Cloth_Primary.
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import Body, torso_loft, torso_ring, interp_rows, front_y, back_y, dome, fist, smoothstep, M_align_z
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
from char_mage import ring_frac, strip_tube, round_tube, zspec_w, normalize_rows, HEAD
from char_knight import thick_band

PROPS = proportions()
PALETTE = "shadowblade"
TINTABLE = ("BH_Cloth_Primary",)


def _lin(c):
    return tuple(round(x ** 2.2, 4) for x in c)


PALETTE_COLORS = {
    # preview value = the in-game class tint Color(0.45, 0.2, 0.6) in linear space (the game replaces it anyway)
    "BH_Cloth_Primary": (_lin((0.45, 0.2, 0.6)), 0.0, 0.85, None, 0.0, 1.0),
    "BH_Cloth_Secondary": ((0.05, 0.046, 0.06), 0.0, 0.9, None, 0.0, 1.0),       # tunic, hood, trousers
    "BH_Leather": ((0.028, 0.026, 0.032), 0.0, 0.5, None, 0.0, 1.0),             # vest, boots
    "BH_LeatherDark": ((0.014, 0.013, 0.017), 0.0, 0.55, None, 0.0, 1.0),       # straps, gloves
    "BH_Mask": ((0.075, 0.055, 0.095), 0.0, 0.88, None, 0.0, 1.0),               # face mask
    "BH_Wrap": ((0.12, 0.11, 0.13), 0.0, 0.92, None, 0.0, 1.0),                  # forearm / calf wraps
    "BH_DarkSteel": ((0.075, 0.075, 0.085), 1.0, 0.42, None, 0.0, 1.0),
    "BH_Steel": ((0.36, 0.36, 0.38), 1.0, 0.46, None, 0.0, 1.0),                 # dull silver
    "BH_Skin": ((0.46, 0.33, 0.27), 0.0, 0.55, None, 0.0, 1.0),
    "BH_Emissive": ((0.45, 0.2, 0.85), 0.0, 0.4, (0.62, 0.3, 1.0), 3.0, 1.0),    # eyes (subtle)
}

SCARF_BONES = [
    ("scarf.1", (0.0, 0.12, 1.46), (0.0, 0.15, 1.10), "chest", (0, -1, 0)),
    ("scarf.2", (0.0, 0.15, 1.10), (0.0, 0.19, 0.76), "scarf.1", (0, -1, 0)),
    ("sash.1", (0.155, -0.03, 1.03), (0.175, -0.02, 0.70), "hips", (0, -1, 0)),
]
EXTRA_BONES = SCARF_BONES

TORSO = [
    (0.96, 0.140, 0.094, 0.094, 0.00),
    (1.04, 0.126, 0.088, 0.086, 0.02),
    (1.14, 0.128, 0.096, 0.088, 0.05),
    (1.25, 0.144, 0.106, 0.094, 0.08),
    (1.35, 0.156, 0.110, 0.098, 0.07),
    (1.43, 0.156, 0.102, 0.096, 0.03),
    (1.49, 0.130, 0.086, 0.088, 0.00),
    (1.53, 0.076, 0.060, 0.060, 0.00),
]
TG = 0.008          # tunic over the body
VG = 0.017          # vest over the body
TORSO_W = zspec_w([(0.99, "hips"), (1.10, "spine"), (1.22, "spine"), (1.32, "chest")])
HEAD_W = zspec_w([(1.50, "chest"), (1.54, "neck"), (1.58, "neck"), (1.61, "head")])
HOOD_W = zspec_w([(1.49, "chest"), (1.54, "neck"), (1.57, "neck"), (1.62, "head")])


def build(body: Body):
    torso(body)
    straps(body)
    waist(body)
    legs(body)
    arms(body)
    pauldron(body)
    head(body)
    scarf(body)


# ================================================================================================ secondary motion
def secondary(anim, frames):
    """Scarf tails hang toward gravity (counter the chest pitch/roll while upright), stream back with ground speed and
    flutter at twice the step rate; the sash tail does the same off the hips with less amplitude. Derived only from
    the evaluated frames (loops stay seamless)."""
    from bh_math import slerp_mat
    n = len(frames)
    gait = getattr(anim, "gait", None)
    speed = gait.v if gait is not None else 0.0
    T = max(anim.length, 1)
    d = math.radians(gait.dir) if gait is not None else 0.0
    out = []
    for f in range(n):
        o = {}
        for bone, parent, amp, lim, ph in (("scarf.1", "chest", 9.0, 48.0, 0.0), ("sash.1", "hips", 6.0, 30.0, 1.3)):
            Rp = frames[f][3][parent].R
            fwd = Rp @ np.array([0, -1.0, 0])
            yaw = math.degrees(math.atan2(fwd[0], -fwd[1]))
            up = float(Rp[2, 2])
            w = 0.8 * min(max((up - 0.45) / 0.45, 0.0), 1.0)
            hang = slerp_mat(np.eye(3), Rp.T @ Rz(yaw), w)
            flare = min(lim, amp * speed) + (4.0 * math.sin(4 * math.pi * f / T + ph) if speed > 0 else 0.0)
            fx, fy = max(flare * math.cos(d), 0.0), 0.6 * flare * math.sin(d)
            if bone == "sash.1":
                fy += 0.4 * fx            # the sash hangs at the side: stream out and back
                fx *= 0.8
            o[bone] = hang @ Rx(fx) @ Ry(fy)
            if bone == "scarf.1":
                o["scarf.2"] = Rx(0.55 * fx + (2.5 * math.sin(4 * math.pi * f / T + 0.8) if speed > 0 else 0.0)) @ \
                    Ry(0.5 * fy)
        out.append(o)
    return out


# ================================================================================================ torso
def torso(body):
    add = body.add
    V, F = torso_loft([(r[0], r[1] + TG, r[2] + TG, r[3] + TG, r[4]) for r in TORSO if r[0] >= 0.98], n=24,
                      cap1=True)
    add(M.Part(V, F, "BH_Cloth_Secondary", name="tunic"), weights=TORSO_W)
    # quilted leather vest: closed, high collar at the back, stitched horizontal ridges
    zs = [1.10, 1.16, 1.22, 1.28, 1.34, 1.40, 1.45, 1.49]
    rings = [ring_frac(TORSO, z, VG, np.linspace(0.0, 1.0, 29)[:-1]) for z in zs]
    V, F = M.loft(rings, cap0=False, cap1=False)
    add(M.solidify(M.Part(V, F, "BH_Leather", name="vest"), 0.007, offset=1.0), weights=TORSO_W)
    for z in (1.16, 1.22, 1.28, 1.34, 1.40):
        ring = ring_frac(TORSO, z, VG + 0.007, np.linspace(0.0, 1.0, 29))
        V, F = M.tube(ring, [(0.0035, 0.0035)] * len(ring), n=4, up=(0, 0, 1), cap0=False, cap1=False)
        add(M.Part(V, F, "BH_LeatherDark", name="quilt"), weights=TORSO_W)
    # dull-silver piping at the vest hem and neck
    for z, g in ((1.102, VG + 0.008), (1.487, VG + 0.006)):
        ring = ring_frac(TORSO, z, g, np.linspace(0.0, 1.0, 29))
        V, F = M.tube(ring, [(0.0045, 0.0045)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
        add(M.Part(V, F, "BH_Steel", name="piping"), weights=TORSO_W)
    # asymmetric leather plate over the right ribs
    rr = [ring_frac(TORSO, z, VG + 0.01, np.linspace(0.62, 0.9, 8)) for z in (1.17, 1.22, 1.27, 1.32)]
    V, F = M.loft(rr, cap0=False, cap1=False, closed=False)
    add(M.solidify(M.Part(V, F, "BH_DarkSteel", name="rib_plate"), 0.005, offset=1.0, bevel_w=0.0015), weights=TORSO_W)
    for r in (rr[0], rr[-1]):
        add(round_tube(r + np.array([0, 0, 0]), 0.003, "BH_Steel", n=4), weights=TORSO_W)


def throwing_knife(center, direction, normal, length=0.15):
    """Small throwing knife: diamond blade (dull silver), wrapped grip, ring pommel. `direction` = toward the tip."""
    d = normalize(np.asarray(direction, float))
    nrm = normalize(np.asarray(normal, float) - d * np.dot(normal, d))
    side = np.cross(d, nrm)
    c = np.asarray(center, float)
    parts = []
    lb = length * 0.58
    lg = length * 0.3
    base = c - d * (length * 0.5 - lg)
    # blade: diamond section tapering to a point
    pts = [base, base + d * lb * 0.35, base + d * lb * 0.8, base + d * lb]
    V, F = M.tube(pts, [(0.011, 0.0025), (0.013, 0.003), (0.008, 0.0022), (0.0008, 0.0008)], n=4, up=nrm, p=1.0)
    parts.append(M.Part(V, F, "BH_Steel", name="tk_blade"))
    V, F = M.tube([base - d * lg, base], [(0.006, 0.005), (0.007, 0.005)], n=6, up=nrm)
    parts.append(M.Part(V, F, "BH_LeatherDark", name="tk_grip"))
    ring = [base - d * (lg + 0.012) + (d * math.cos(a) + side * math.sin(a)) * 0.012 for a in
            np.linspace(0, 2 * math.pi, 11)]
    V, F = M.tube(ring, [(0.0025, 0.0025)] * 11, n=4, up=nrm, cap0=False, cap1=False)
    parts.append(M.Part(V, F, "BH_Steel", name="tk_ring"))
    return parts


def straps(body):
    """Two crossed chest straps (X) meeting at a dull-silver ring, each carrying three throwing knives, and continuing
    over the shoulders to cross again on the back."""
    add = body.add
    zc = 1.27
    yc = front_y(TORSO, 0, zc) - VG - 0.016
    for sx in (1, -1):
        pts, ups = [], []
        for t in np.linspace(0, 1, 9):
            x = sx * (0.125 - 0.25 * t)
            z = 1.47 - 0.42 * t
            y = front_y(TORSO, x, z) - VG - 0.013
            pts.append((x, y, z))
            ups.append((0.3 * x, -1, 0))
        add(strip_tube(pts, 0.032, 0.006, "BH_LeatherDark", up=ups), weights=TORSO_W)
        # stitched edges
        # knives on the upper half (handles up, points down along the strap)
        P = np.array(pts)
        for t in (0.12, 0.26, 0.4) if sx > 0 else (0.14, 0.28):
            i = t * 8
            i0 = int(i)
            u = i - i0
            c = P[i0] * (1 - u) + P[i0 + 1] * u
            dd = normalize(P[i0 + 1] - P[i0])
            nrm = normalize(np.array([0.3 * c[0], -1.0, 0.0]))
            for prt in throwing_knife(c + nrm * 0.006, dd * 0.4 + np.array([0, 0, -1.0]) * 0.6, nrm, 0.14):
                add(prt, weights=TORSO_W)
            V, F = M.tube([c - dd * 0.012 + nrm * 0.004, c + dd * 0.012 + nrm * 0.004], [(0.02, 0.004)] * 2, n=4,
                          up=nrm, p=3.0)
            add(M.Part(V, F, "BH_Leather", name="knife_loop"), weights=TORSO_W)
        # over the shoulder and down the back (crossing)
        pts, ups = [], []
        for t in np.linspace(0, 1, 7):
            a = math.pi * (0.5 - t) * 0.95
            pts.append((sx * 0.125, -0.10 * math.sin(a) + 0.008, 1.47 + 0.035 * math.cos(a)))
            ups.append((0, -math.sin(a), math.cos(a)))
        add(strip_tube(pts, 0.032, 0.006, "BH_LeatherDark", up=ups), "chest")
        pts = []
        for t in np.linspace(0, 1, 7):
            x = sx * (0.125 - 0.25 * t)
            z = 1.47 - 0.40 * t
            pts.append((x, back_y(TORSO, x, z) + VG + 0.012, z))
        add(strip_tube(pts, 0.032, 0.006, "BH_LeatherDark", up=[(0, 1, 0)] * 7), weights=TORSO_W)
    ring = [np.array([0.0, yc, zc]) + np.array([math.cos(a), 0, math.sin(a)]) * 0.024 for a in
            np.linspace(0, 2 * math.pi, 17)]
    V, F = M.tube(ring, [(0.006, 0.006)] * 17, n=6, up=(0, -1, 0), cap0=False, cap1=False)
    add(M.Part(V, F, "BH_Steel", name="ring"), weights=TORSO_W)
    V, F = M.sphere(0.013, 10, 6, center=(0, yc - 0.004, zc), scale=(1, 0.5, 1))
    add(M.Part(V, F, "BH_DarkSteel", name="ring_boss"), weights=TORSO_W)


# ================================================================================================ waist
def belt_ring(z_left, z_right, g, fr):
    """Point on a belt loop tilted across the hips (higher on the left)."""
    q = ring_frac(TORSO + [(0.86, 0.146, 0.092, 0.1, 0.0), (0.92, 0.148, 0.096, 0.102, 0.0)], 1.0, g, [fr])[0]
    t = 0.5 + 0.5 * q[0] / 0.16
    q[2] = z_right + (z_left - z_right) * t
    r = interp_rows(sorted(TORSO + [(0.86, 0.146, 0.092, 0.1, 0.0), (0.92, 0.148, 0.096, 0.102, 0.0)]), q[2])
    return q


def waist(body):
    add = body.add
    # sash wrapped around the waist (tintable), knotted on the left hip
    V, F = thick_band(TORSO, 1.03, 1.105, TG + 0.02, TG + 0.004, n=28)
    add(M.Part(V, F, "BH_Cloth_Primary", name="sash"), weights=zspec_w([(1.06, "hips"), (1.12, "spine")]))
    for z in (1.05, 1.08):
        ring = ring_frac(TORSO, z, TG + 0.021, np.linspace(0, 1, 29))
        ring[:, 2] += 0.006 * np.sin(np.linspace(0, 1, 29) * 2 * math.pi * 5)
        V, F = M.tube(ring, [(0.004, 0.004)] * 29, n=4, up=(0, 0, 1), cap0=False, cap1=False)
        add(M.Part(V, F, "BH_Cloth_Primary", name="sash_fold"), "hips")
    kn = ring_frac(TORSO, 1.06, TG + 0.03, [0.2])[0]
    V, F = M.sphere(0.024, 10, 6, center=kn, scale=(0.9, 0.8, 1.0))
    add(M.Part(V, F, "BH_Cloth_Primary", name="sash_knot"), "hips")
    # tail hanging from the knot down the outside of the left thigh (sash.1), tattered end
    nu, nv = 5, 9

    def tail(u, v):
        w = 0.06 - 0.012 * v
        z = 1.05 - 0.37 * v
        teeth = (0.02 * abs(((u * 3.0) % 1.0) - 0.5) * 2) if v > 0.99 else 0.0
        return (kn[0] + 0.02 * v + (u - 0.5) * w * 0.35, kn[1] + 0.012 + (u - 0.5) * w * 0.94 + 0.01 * v,
                z + teeth)
    V, F = M.grid(tail, nu, nv)
    tp = M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="sash_tail"), 0.006, offset=0.0)
    add(tp, weights=zspec_w([(0.98, "sash.1"), (1.04, "hips")]))
    # low-slung belt, tilted (high on the left hip, low on the right), silver buckle
    loop = []
    for fr in np.linspace(0, 1, 33)[:-1]:
        q = ring_frac(TORSO + [(0.9, 0.15, 0.096, 0.104, 0.0)], 1.0, TG + 0.03, [fr])[0]
        q[2] = 0.985 + 0.045 * (q[0] / 0.16)
        loop.append(q)
    loop = np.array(loop)
    V, F = M.tube(np.vstack([loop, loop[:1]]), [(0.018, 0.005)] * 33, n=4, up=(0, 0, 1), p=3.0, cap0=False,
                  cap1=False)
    add(M.Part(V, F, "BH_LeatherDark", name="belt"), "hips")
    bq = loop[0] + np.array([0, -0.006, 0])
    V, F = M.box(0.04, 0.01, 0.034)
    add(M.bevel(M.Part(V, F, "BH_Steel", name="belt_buckle"), 0.003, 1).rot(Ry(-15)).move(bq), "hips")
    # front and back flaps
    for back in (False, True):
        def fn(u, v, back=back):
            w = 0.075 - 0.012 * v
            x = (u - 0.5) * 2 * w
            z0 = 0.985 + 0.045 * (x / 0.16) - 0.005
            z = z0 - (0.25 if not back else 0.3) * v
            y0 = (front_y(TORSO, x, 1.0) - TG - 0.034) if not back else (back_y(TORSO, x, 1.0) + TG + 0.034)
            y = y0 + ((-0.03 if not back else 0.045) * v)
            return (x, y, z)
        V, F = M.grid(fn, 5, 6)
        p = M.Part(V, F, "BH_Cloth_Secondary", name="flap")
        if back:
            p.flip()
        add(M.solidify(p, 0.007, offset=1.0), weights=body.skirt_weights(0.98, 0.7, max_leg=0.55, center_w=0.06))
        edge = np.array([fn(u, 1.0) for u in np.linspace(0, 1, 6)]) + np.array([0, 0, 0.006])
        add(round_tube(edge, 0.0045, "BH_Steel", n=4),
            weights=body.skirt_weights(0.98, 0.7, max_leg=0.55, center_w=0.06))
    # dark-steel tassets on the right hip (two lames with silver edges)
    for i in range(2):
        z1 = 0.975 - 0.07 * i
        rows = [(z1 - 0.085, 0.168 + 0.02 * i, 0.12, 0.12, 0.0), (z1, 0.156 + 0.02 * i, 0.11, 0.11, 0.0)]
        rr = [ring_frac(rows, r[0], 0.0, np.linspace(0.68, 0.84, 9)) for r in rows]
        V, F = M.loft(rr, cap0=False, cap1=False, closed=False)
        lame = M.solidify(M.Part(V, F, "BH_DarkSteel", name="tasset"), 0.006, offset=1.0, bevel_w=0.0015)
        wf = body.skirt_weights(1.0, 0.75, max_leg=0.5, center_w=0.05)
        add(lame, weights=wf)
        add(round_tube(rr[0] + np.array([0, 0, 0.003]) + np.array([0, 0, 0]) * 0, 0.0035, "BH_Steel", n=4), weights=wf)


# ================================================================================================ legs
def spiral(body, bone, u0, u1, r, turns, mat, width=0.02, thick=0.005, n_per=10, phase=0.0, L=None):
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
        pts.append(o + A @ np.array([rr * math.cos(a), u * L, rr * math.sin(a)]))
        ups.append(A @ np.array([math.cos(a), 0, math.sin(a)]))
    return strip_tube(pts, width, thick, mat, n=6, up=ups)


def legs(body):
    V, F = torso_loft([(0.84, 0.14, 0.088, 0.096, 0.0), (0.92, 0.143, 0.093, 0.1, 0.0),
                       (1.0, 0.138, 0.092, 0.096, 0.0)], n=24)
    body.add(M.Part(V, F, "BH_Cloth_Secondary", name="seat"),
             weights=body.skirt_weights(0.98, 0.84, max_leg=0.7, center_w=0.05))
    for s in ("L", "R"):
        sgn = 1 if s == "L" else -1
        th, sh = "thigh." + s, "shin." + s
        h, k, a = body.head(th), body.head(sh), body.tail(sh)
        pts = [h + (0, 0, 0.04), h + (k - h) * 0.4, k + (0, 0, 0.02), k + (a - k) * 0.35, k + (a - k) * 0.62]
        prof = [(0.07, 0.074), (0.062, 0.066), (0.049, 0.053), (0.047, 0.05), (0.041, 0.043)]
        V, F = M.tube(pts, prof, n=12, up=(0, -1, 0))
        body.add(M.Part(V, F, "BH_Cloth_Secondary", name="trouser"), weights=body.seg_weights([th, sh], power=10))
        Lsh = float(np.linalg.norm(a - k))
        # calf wraps from the boot top to just under the knee
        body.add(spiral(body, sh, 0.08, 0.48, lambda u: 0.052 - 0.01 * u, 4.0, "BH_Wrap", width=0.02, thick=0.005,
                        L=Lsh), sh)
        # knee plate (dark steel, silver rim)
        V, F = dome(k + (0, -0.026, 0.0), (0, -1, 0.12), 0.055, a_max=46, n=12, rings=3, scale=(0.8, 1.25, 1.0))
        cap = M.solidify(M.Part(V, F, "BH_DarkSteel", name="kneeplate"), 0.005, offset=-1, bevel_w=0.0015)
        body.add(cap, weights=lambda V, th=th, sh=sh: [{th: 0.5, sh: 0.5}] * len(V))
        for part, bone in boot(body, s):
            body.add(part, bone)
        if s == "L":
            # thigh strap with a sheathed knife on the outside of the left thigh
            Lth = float(np.linalg.norm(k - h))
            A = body.axes(th)
            o = body.head(th)
            for u in (0.42, 0.62):
                ring = [o + A @ np.array([0.068 * math.cos(t), u * Lth, 0.068 * math.sin(t)]) for t in
                        np.linspace(0, 2 * math.pi, 17)]
                V, F = M.tube(ring, [(0.004, 0.012)] * 17, n=4, up=[A @ np.array([0, 1.0, 0])] * 17, p=3.0,
                              cap0=False, cap1=False)
                body.add(M.Part(V, F, "BH_LeatherDark", name="thigh_strap"), th)
            c = o + A @ np.array([0.0, 0.52 * Lth, 0.0]) + np.array([0.074, 0.0, 0.0])
            dn = normalize(A @ np.array([0, 1.0, 0]))
            V, F = M.tube([c - dn * 0.05, c + dn * 0.1, c + dn * 0.14], [(0.006, 0.02), (0.005, 0.016), (0.002, 0.004)],
                          n=6, up=(1, 0, 0), p=2.6)
            body.add(M.Part(V, F, "BH_Leather", name="thigh_sheath"), th)
            for prt in throwing_knife(c - dn * 0.1, -dn, np.array([1.0, 0, 0]), 0.1):
                if prt.name != "tk_blade":
                    body.add(prt, th)


def boot(body, s):
    sgn = 1 if s == "L" else -1
    hx = PROPS["hip_x"] * sgn
    sh = "shin." + s
    out = []
    k, a = body.head(sh), body.tail(sh)
    pts = [a + (0, 0.004, 0.02), a + (k - a) * 0.22, a + (k - a) * 0.36]
    V, F = M.tube(pts, [(0.047, 0.051), (0.046, 0.05), (0.05, 0.054)], n=12, up=(0, -1, 0), cap1=False)
    out.append((M.solidify(M.Part(V, F, "BH_Leather", name="boot"), 0.004, offset=-1.0), sh))
    c0 = a + (k - a) * 0.34
    V, F = M.tube([c0, c0 + (0, 0, 0.014)], [(0.053, 0.057)] * 2, n=12, up=(0, -1, 0), cap0=False, cap1=False)
    out.append((M.Part(V, F, "BH_Steel", name="boot_rim"), sh))

    def rings_(spec):
        R = []
        for y, w, top in spec:
            pts = []
            for i in range(12):
                ang = 2 * math.pi * i / 12
                c, sn = math.cos(ang), math.sin(ang)
                x = w * np.sign(c) * abs(c) ** 0.85
                z = top / 2 + top / 2 * np.sign(sn) * abs(sn) ** 0.75
                pts.append((hx + x, y, max(z, 0.01)))
            R.append(np.array(pts))
        return R
    foot = rings_([(0.062, 0.032, 0.072), (0.042, 0.039, 0.104), (0.0, 0.043, 0.11), (-0.06, 0.043, 0.08),
                   (-0.12, 0.042, 0.056)])
    V, F = M.loft(foot[::-1])
    out.append((M.bevel(M.Part(V, F, "BH_Leather", name="bootfoot"), 0.003, 1, angle=45), "foot." + s))
    toe = rings_([(-0.115, 0.042, 0.056), (-0.17, 0.037, 0.045), (-0.215, 0.022, 0.032), (-0.238, 0.006, 0.02)])
    V, F = M.loft(toe[::-1])
    out.append((M.bevel(M.Part(V, F, "BH_Leather", name="boottoe"), 0.003, 1, angle=45), "toe." + s))
    V, F = M.box(0.086, 0.2, 0.01, center=(hx, -0.03, 0.005))
    out.append((M.bevel(M.Part(V, F, "BH_LeatherDark", name="sole"), 0.003, 1), "foot." + s))
    V, F = M.box(0.068, 0.1, 0.009, center=(hx, -0.18, 0.0045))
    out.append((M.bevel(M.Part(V, F, "BH_LeatherDark", name="sole_t"), 0.003, 1), "toe." + s))
    # foot wraps over the instep
    for y, w in ((0.0, 0.02), (-0.045, 0.018)):
        V, F = M.tube([(hx, y + w / 2, 0.06), (hx, y - w / 2, 0.06)], [(0.047, 0.058)] * 2, n=12, up=(0, 0, 1))
        out.append((M.Part(V, F, "BH_Wrap", name="foot_wrap").move((0, 0, 0.0)), "foot." + s))
    return out


# ================================================================================================ arms
def arms(body):
    for s in ("L", "R"):
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
        d = normalize(wr - el)
        pts = [sh + (sh - el) * 0.05, sh + (el - sh) * 0.35, sh + (el - sh) * 0.8, el, el + (wr - el) * 0.35,
               el + (wr - el) * 0.75, wr]
        prof = [(0.054, 0.058), (0.054, 0.057), (0.048, 0.051), (0.046, 0.048), (0.043, 0.045), (0.038, 0.04),
                (0.035, 0.037)]
        V, F = M.tube(pts, prof, n=12, up=(0, -1, 0))
        body.add(M.Part(V, F, "BH_Cloth_Secondary", name="sleeve"), weights=body.seg_weights([ua, fa], power=10))
        Lf = PROPS["fore_len"]
        body.add(spiral(body, fa, 0.1, 0.96, lambda u: 0.047 - 0.01 * u, 5.0, "BH_Wrap", width=0.022, thick=0.005,
                        L=Lf), fa)
        body.add(spiral(body, fa, 0.2, 0.9, lambda u: 0.05 - 0.01 * u, 2.0, "BH_LeatherDark", width=0.012,
                        thick=0.004, L=Lf, phase=2.0), fa)
        for u in (0.12, 0.95):
            c = body.head(fa) + body.axes(fa) @ np.array([0, u * Lf, 0])
            rr = 0.05 - 0.01 * u
            V, F = M.tube([c - d * 0.005, c + d * 0.005], [(rr, rr)] * 2, n=12, up=(0, -1, 0))
            body.add(M.Part(V, F, "BH_Steel", name="wrap_ring"), fa)
        if s == "R":
            c = sh + (el - sh) * 0.6
            du = normalize(el - sh)
            V, F = M.tube([c - du * 0.016, c + du * 0.016], [(0.056, 0.059)] * 2, n=12, up=(0, -1, 0))
            body.add(M.Part(V, F, "BH_Leather", name="armband"), ua)
            A = body.axes(ua)
            for k in range(3):
                a = math.radians(-40 + 40 * k)
                p = c + A @ np.array([0.059 * math.sin(a), 0.0, 0.059 * math.cos(a)])
                V, F = M.sphere(0.006, 6, 4, center=p)
                body.add(M.Part(V, F, "BH_Steel", name="stud"), ua)
        for prt in fist(body, s, "BH_DarkSteel", "BH_LeatherDark", gauntlet=True):
            body.add(prt, ha)
        V, F = M.tube([wr - d * 0.005, wr + d * 0.028], [(0.039, 0.041), (0.037, 0.039)], n=12, up=(0, -1, 0))
        body.add(M.Part(V, F, "BH_LeatherDark", name="glove_cuff"), ha)


def pauldron(body):
    """Layered dark-steel pauldron on the left shoulder only: leather under-pad, domed cap with a silver keel and rim,
    two lames down the arm."""
    s = "L"
    ua = "upper_arm." + s
    sh = body.head(ua)
    el = body.head("forearm." + s)
    armdir = normalize(el - sh)
    axis = normalize(np.array([0.6, 0.0, 0.8]))
    c = sh + np.array([0.012, 0.0, 0.016])
    V, F = dome(c + np.array([0.0, 0, -0.012]), axis, 0.112, a_max=76, n=16, rings=5, scale=(1.0, 1.15, 1.0))
    body.add(M.solidify(M.Part(V, F, "BH_Leather", name="underpad"), 0.006, offset=-1), ua)
    V, F = dome(c, axis, 0.108, a_max=64, n=16, rings=5, scale=(1.0, 1.12, 1.0))
    body.add(M.solidify(M.Part(V, F, "BH_DarkSteel", name="pauldron"), 0.007, offset=-1, bevel_w=0.002), ua)
    Rm = M_align_z(axis, (0, 0, 1))
    rim = []
    for i in range(25):
        a = 2 * math.pi * i / 24
        r = 0.108 * math.sin(math.radians(64))
        z = 0.108 * math.cos(math.radians(64))
        rim.append(c + Rm @ np.array([r * math.cos(a), r * math.sin(a) * 1.12, z]))
    V, F = M.tube(rim, [(0.0055, 0.0055)] * 25, n=5, up=axis, cap0=False, cap1=False)
    body.add(M.Part(V, F, "BH_Steel", name="p_rim"), ua)
    # swept keel: a raised silver fin running front to back, rising toward the back
    mer = []
    for lat in np.linspace(-55, 60, 11):
        a = math.radians(lat)
        rr = 0.112 + 0.012 * max(lat, 0) / 60
        mer.append(c + Rm @ np.array([0.0, rr * math.sin(a) * 1.12, rr * math.cos(a)]))
    V, F = M.tube(mer, [(0.004, 0.012)] * len(mer), n=5, up=axis, p=2.8)
    body.add(M.Part(V, F, "BH_Steel", name="p_keel"), ua)
    out = np.array([1.0, 0, 0])
    ax_side = normalize(out - armdir * np.dot(out, armdir))
    ax_fwd = np.cross(armdir, ax_side)
    for i in range(2):
        rr = 0.082 - 0.008 * i
        ctr = sh + armdir * (0.1 + 0.05 * i)
        loops = []
        for z_off in (0.0, 0.052):
            loop = []
            for k in range(13):
                a = math.radians(-105 + 210 * k / 12)
                pdir = ax_side * math.cos(a) + ax_fwd * math.sin(a) * 1.1
                loop.append(ctr + armdir * (z_off - 0.026) + pdir * (rr + 0.01 * (z_off > 0)))
            loops.append(np.array(loop))
        V, F = M.loft(loops, cap0=False, cap1=False, closed=False)
        body.add(M.solidify(M.Part(V, F, "BH_DarkSteel", name="lame"), 0.005, offset=1, bevel_w=0.0015), ua)
        V, F = M.tube(loops[1], [(0.003, 0.003)] * 13, n=4, up=armdir, cap0=False, cap1=False)
        body.add(M.Part(V, F, "BH_Steel", name="lame_rim"), ua)
    # strap under the arm
    pts = [sh + ax_side * 0.07 + ax_fwd * 0.055 + armdir * 0.12, sh - ax_side * 0.05 + armdir * 0.12,
           sh + ax_side * 0.07 - ax_fwd * 0.055 + armdir * 0.12]
    V, F = M.tube(pts, [(0.011, 0.004)] * 3, n=6, up=armdir, p=3.0)
    body.add(M.Part(V, F, "BH_LeatherDark", name="p_strap"), ua)


# ================================================================================================ head, mask, hood
HOOD = [  # z, rx, ry_front, ry_back, cy, opening half-angle (deg)
    (1.495, 0.150, 0.126, 0.136, 0.020, 26),
    (1.550, 0.122, 0.112, 0.130, 0.014, 34),
    (1.620, 0.114, 0.118, 0.130, 0.000, 40),
    (1.680, 0.116, 0.126, 0.132, -0.008, 41),
    (1.740, 0.113, 0.130, 0.132, -0.012, 38),
    (1.790, 0.102, 0.126, 0.126, -0.010, 30),
    (1.828, 0.082, 0.110, 0.112, -0.002, 20),
    (1.856, 0.052, 0.080, 0.088, 0.010, 10),
    (1.872, 0.016, 0.036, 0.052, 0.024, 3),
]


def head(body):
    add = body.add
    V, F = M.tube([(0, 0.0, 1.47), (0, -0.004, 1.54), (0, -0.01, 1.62)], [(0.054, 0.051), (0.049, 0.047), (0.05, 0.05)],
                  n=12, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="neck"), weights=HEAD_W)
    V, F = torso_loft(HEAD, n=22, p=2.1, cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Skin", name="head"), "head")
    V, F = M.tube([(-0.05, -0.067, 1.716), (0.0, -0.079, 1.721), (0.05, -0.067, 1.716)],
                  [(0.011, 0.008)] * 3, n=6, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="brow"), "head")
    for sx in (1, -1):
        V, F = M.sphere(0.0135, 8, 5, center=(sx * 0.029, -0.068, 1.699), scale=(1.2, 0.6, 0.72))
        add(M.Part(V, F, "BH_Shadow", name="socket"), "head")
        V, F = M.sphere(0.0062, 8, 4, center=(sx * 0.029, -0.0735, 1.699), scale=(1.7, 0.55, 0.5))
        add(M.Part(V, F, "BH_Emissive", name="eye"), "head")
    # hair wisps at the brow under the hood
    for k, x in enumerate((-0.04, -0.012, 0.018, 0.045)):
        pts = [(x * 0.8, -0.05, 1.79), (x, -0.074, 1.755), (x * 1.15 + 0.004, -0.078, 1.727)]
        V, F = M.tube(pts, [(0.012, 0.004), (0.01, 0.004), (0.002, 0.002)], n=5, up=(0, -1, 0.3))
        add(M.Part(V, F, "BH_Hair", name="wisp"), "head")
    # cloth mask over nose, mouth and chin, pulled up to just under the eyes
    rows = [(r[0], r[1] + 0.01, r[2] + 0.01, r[3] + 0.01) + tuple(r[4:]) for r in HEAD]
    nu = 24
    rings = []
    for z in (1.575, 1.6, 1.63, 1.66, 1.682):
        fr = np.linspace(0, 1, nu, endpoint=False)
        r = ring_frac(rows, max(z, 1.60), 0.0, fr, p=2.1)
        r[:, 2] = z
        # pinch over the nose bridge: the front centre rides higher
        front = np.clip(np.cos(fr * 2 * math.pi), 0, 1) ** 4
        if z > 1.67:
            r[:, 2] += 0.008 * front
            r[:, 1] -= 0.012 * front
        if z < 1.6:
            r[:, :2] *= 1.06
        rings.append(r)
    V, F = M.loft(rings, cap0=False, cap1=False)
    add(M.solidify(M.Part(V, F, "BH_Mask", name="mask"), 0.006, offset=1.0), "head")
    # mask folds
    for z in (1.61, 1.64):
        fr = np.linspace(-0.2, 0.2, 9)
        r = ring_frac(rows, z, 0.008, fr, p=2.1)
        r[:, 2] = z - 0.01 * np.cos(fr * math.pi * 2.5)
        add(round_tube(r, 0.003, "BH_Mask", n=4), "head")
    # the mask drops over the throat to the scarf
    def fn(u, v):
        w = 0.058 * (1 - v) + 0.042
        x = (u - 0.5) * 2 * w
        return (x, -0.084 + 0.026 * v + 6.0 * x * x, 1.585 - 0.07 * v)
    V, F = M.grid(fn, 7, 4)
    add(M.solidify(M.Part(V, F, "BH_Mask", name="mask_drop"), 0.006, offset=1.0),
        weights=zspec_w([(1.52, "chest"), (1.56, "neck"), (1.58, "head")]))
    # deep hood
    nu = 24
    rings = []
    for (z, rx, ryf, ryb, cy, th) in HOOD:
        ring = []
        for u in np.linspace(0, 1, nu):
            a = math.radians(th + (360 - 2 * th) * u)
            sa, ca = math.sin(a), math.cos(a)
            ring.append((rx * sa, cy - (ryf if ca > 0 else ryb) * ca, z))
        rings.append(np.array(ring))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    add(M.solidify(M.Part(V, F, "BH_Cloth_Secondary", name="hood"), 0.011, offset=-1.0), weights=HOOD_W)
    edge = [r[0] for r in rings] + [r[-1] for r in rings[::-1]]
    edge = np.array(edge)
    V, F = M.tube(edge, [(0.0042, 0.0042)] * len(edge), n=5, up=(0, 0, 1))
    add(M.Part(V, F, "BH_Steel", name="hood_trim"), weights=HOOD_W)
    inner = []
    for (z, rx, ryf, ryb, cy, th) in HOOD[1:7]:
        ring = []
        for u in np.linspace(0, 1, nu):
            a = math.radians(th + (360 - 2 * th) * u)
            ring.append((rx * 0.9 * math.sin(a), cy - (ryf if math.cos(a) > 0 else ryb) * 0.9 * math.cos(a), z))
        inner.append(np.array(ring))
    V, F = M.loft(inner, cap0=False, cap1=False, closed=False)
    add(M.Part(V, F, "BH_Shadow", name="hood_lining").flip(), weights=HOOD_W)


def scarf_w():
    def wfn(V):
        out = []
        for v in V:
            z = v[2]
            if z > 1.44:
                out.append({"chest": 1.0})
            elif z > 1.32:
                t = float(smoothstep(1.32, 1.44, z))
                out.append({"chest": t, "scarf.1": 1 - t})
            elif z > 1.14:
                out.append({"scarf.1": 1.0})
            elif z > 1.02:
                t = float(smoothstep(1.02, 1.14, z))
                out.append({"scarf.1": t, "scarf.2": 1 - t})
            else:
                out.append({"scarf.2": 1.0})
        return out
    return wfn


def scarf(body):
    add = body.add
    # bulky wrap around the throat over the collar
    n = 36
    for k, (z, rx, ry, r0) in enumerate(((1.505, 0.094, 0.088, 0.024), (1.54, 0.082, 0.078, 0.02))):
        pts, prof = [], []
        for i in range(n + 1):
            th = 2 * math.pi * i / n
            pts.append((rx * math.sin(th), 0.006 + ry * math.cos(th), z + 0.008 * math.sin(2 * th + k)))
            r = r0 + 0.004 * math.sin(5 * th + k)
            prof.append((r, r * 0.85))
        V, F = M.tube(pts, prof, n=8, up=(0, 0, 1), cap0=False, cap1=False)
        add(M.Part(V, F, "BH_Cloth_Primary", name="scarf_wrap"),
            weights=zspec_w([(1.49, "chest"), (1.56, "neck")]))
    V, F = M.sphere(0.03, 10, 6, center=(0.03, 0.1, 1.5), scale=(1.1, 0.8, 0.9))
    add(M.Part(V, F, "BH_Cloth_Primary", name="scarf_knot"), "chest")
    # two long tattered tails down the back
    for (x0, x1, z1, w0, w1, twist) in ((0.035, 0.07, 0.78, 0.085, 0.07, 0.25), (-0.02, -0.07, 0.95, 0.075, 0.06, -0.3)):
        nu, nv = 6, 14

        def fn(u, v, x0=x0, x1=x1, z1=z1, w0=w0, w1=w1, twist=twist):
            z = 1.49 + (z1 - 1.49) * v
            xc = x0 + (x1 - x0) * v
            w = w0 + (w1 - w0) * v
            if z > 1.02:
                yb = back_y(TORSO, xc, min(max(z, 1.04), 1.47)) + VG + 0.026
            else:
                yb = back_y(TORSO, xc, 1.04) + VG + 0.026 + 0.12 * (1.02 - z)
            ang = twist * v
            x = xc + (u - 0.5) * w * math.cos(ang)
            y = yb + (u - 0.5) * w * math.sin(ang) + 0.008 * math.sin(v * 9)
            if v > 0.999:      # tattered end: ragged notches
                z += 0.035 * abs(((u * 2.5) % 1.0) - 0.5) * 2 - 0.01
            elif v > 0.9:
                z += 0.012 * math.sin(u * 13) * (v - 0.9) * 10
            return (x, y, z)
        V, F = M.grid(fn, nu, nv)
        tp = M.Part(V, F, "BH_Cloth_Primary", name="scarf_tail")
        add(M.solidify(tp, 0.006, offset=0.0), weights=scarf_w())
