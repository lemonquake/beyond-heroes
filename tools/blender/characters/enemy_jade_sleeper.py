"""Jade-Wrapped Sleeper (bh-029, Builder M5, Zarael / the Jade Sepulchre fodder): a Wirewright courtier wrapped for
the long sleep beside the king. A gaunt body bound in pale funeral linen (diagonal bandage courses over the torso,
spiral wraps round every limb, loose stained ends hanging), sewn over with small jade plaques stitched in gold wire:
a pectoral of plaques on the breast, a collar of plaques round the neck, a plaque belt, bracers and shin guards. The
white-glowing wire bindings that keep it walking are wound round its chest, arms and legs. The face is hidden by a
carved jade death-mask (heavy brow, white-lit almond eye slits, a dark mouth with jade teeth) with gold ear spools.
Both hands are open claws with long jade nail-guards (it grasps; no weapon).

~1.82 m. Clips: axe_1 axe_2 cast_quick (+ the enemy base set).

Also holds the small Jade Sepulchre kit the other M5 modules share: `surf_frame`, `plaque`, `torso_plaques`,
`glow_wrap`, `linen_wrap`, `death_mask`, `WHITE_GLOW`."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_hollow_soldier as HS
import kit_a_common as A
import enemy_glyphbound_warrior as Z

SCALE = 1.84 / 1.84
PROPS = proportions(SCALE, shoulder_x=0.172, hip_x=0.09, upper_len=0.3, fore_len=0.29)
PREVIEW_HEIGHT = 2.2
WHITE_GLOW = ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0)      # Zarael glow rule: pure white
PALETTE = "jade_sleeper"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.56, 0.5, 0.39), 0.0, 0.95, None, 0.0, 1.0),       # pale funeral linen
    "BH_Cloth_Secondary": ((0.3, 0.25, 0.17), 0.0, 0.95, None, 0.0, 1.0),     # stained, older linen
    "BH_Skin": ((0.16, 0.11, 0.08), 0.0, 0.7, None, 0.0, 1.0),                # dried flesh in the gaps
    "BH_Stone": ((0.11, 0.42, 0.3), 0.0, 0.28, None, 0.0, 1.0),               # polished jade
    "BH_Horn": ((0.06, 0.24, 0.18), 0.0, 0.35, None, 0.0, 1.0),               # dark jade (nail-guards, teeth)
    "BH_Gold": ((0.74, 0.52, 0.2), 1.0, 0.32, None, 0.0, 1.0),                # gold wire stitching / spools
    "BH_Shadow": ((0.016, 0.014, 0.012), 0.0, 0.85, None, 0.0, 1.0),
    "BH_Emissive": WHITE_GLOW,                                                 # the binding wire, the eyes
}
CLIPS = ["axe_1", "axe_2", "cast_quick"]

TORSO = [(r[0], r[1] * 0.9, r[2] * 0.86, r[3] * 0.9, r[4] * 0.5) for r in K.TORSO]
LG = 0.006                       # linen thickness over the body
P = Z.P


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


# ================================================================================================= Jade kit
def surf_frame(rows, frac, z, g):
    """Point + frame on a torso-row surface: (p, e1 along the ring toward own left, e2 inward, e3 up)."""
    p = K.ring_frac(rows, z, g, [frac])[0]
    u = K.ring_frac(rows, z, g, [frac + 0.006])[0] - K.ring_frac(rows, z, g, [frac - 0.006])[0]
    v = K.ring_frac(rows, z + 0.01, g, [frac])[0] - K.ring_frac(rows, z - 0.01, g, [frac])[0]
    e1 = normalize(u)
    n = normalize(np.cross(e1, v))
    e3 = normalize(v - n * np.dot(v, n) - e1 * np.dot(v, e1))
    e2 = np.cross(e3, e1)
    return p, np.stack([e1, e2, e3], 1)


def plaque(c, R, w, h, t=0.008, mat="BH_Stone", bev=0.003, lift=0.0):
    """Bevelled tile centred at c on a surface (R columns: across, inward, up); grows outward from the surface."""
    V, F = M.box(w, t, h)
    p = P(V, F, mat, "plaque")
    if bev:
        p = M.bevel(p, bev, 1)
    return p.rot(R).move(np.asarray(c, float) - R[:, 1] * (t / 2 + lift))


def torso_plaques(rows, fracs, zs, g, w, h, t=0.008, stitch=True, mat="BH_Stone"):
    """A grid of jade plaques on a torso surface + gold wire stitching between them. Returns parts."""
    out = []
    for z in zs:
        for f in fracs:
            p, R = surf_frame(rows, f, z, g)
            out.append(plaque(p, R, w, h, t, mat))
            if stitch:
                for sx in (-1, 1):
                    q = p - R[:, 1] * (t * 0.5) + R[:, 0] * sx * w * 0.36
                    out.append(A.tube([q - R[:, 2] * h * 0.3, q + R[:, 2] * h * 0.3], 0.0028, "BH_Gold", n=4))
    return out


def glow_wrap(a, b, r, turns, wire=0.0055, phase=0.0, mat="BH_Emissive"):
    """A binding wire wound round the segment a -> b at radius r (round wire)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = normalize(b - a)
    side = normalize(np.cross(d, (0, 1, 0))) if abs(d[1]) < 0.9 else np.array([1.0, 0, 0])
    fw = np.cross(side, d)
    n = int(turns * 12) + 2
    pts = []
    for i in range(n):
        t = i / (n - 1)
        ang = 2 * math.pi * turns * t + phase
        pts.append(a + (b - a) * t + (side * math.cos(ang) + fw * math.sin(ang)) * r)
    return A.tube(pts, wire, mat, n=4)


def linen_wrap(a, b, r, turns, width=0.03, thick=0.007, mat="BH_Cloth_Primary", phase=0.0):
    """A flat bandage wound round a -> b (the bandage courses read as ridges)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = normalize(b - a)
    side = normalize(np.cross(d, (0, 1, 0))) if abs(d[1]) < 0.9 else np.array([1.0, 0, 0])
    fw = np.cross(side, d)
    n = int(turns * 10) + 2
    pts, ups = [], []
    for i in range(n):
        t = i / (n - 1)
        ang = 2 * math.pi * turns * t + phase
        nrm = side * math.cos(ang) + fw * math.sin(ang)
        pts.append(a + (b - a) * t + nrm * r)
        ups.append(nrm)
    V, F = M.tube(pts, [(width / 2, thick / 2)] * n, n=4, up=[np.asarray(u) for u in ups], p=3.0)
    return P(V, F, mat, "wrap")


def death_mask(hz, width=0.16, height=0.21, ytop=-0.083, bulge=0.024, mat="BH_Stone", eyes="BH_Emissive",
               thick=0.016, cx=0.0):
    """Carved jade death-mask over the face (standard space; hz = bottom of the mask). Returns (parts, surf) with
    surf(x, z, out) -> a point on the mask front."""
    def fn(u, v):
        x = (u - 0.5) * width
        z = hz + height * v
        b = (1 - (2 * u - 1) ** 2) ** 0.5 * (1 - (2 * v - 1) ** 2) ** 0.4
        y = ytop - bulge * b + 0.012 * (2 * v - 1) ** 2 + 0.03 * (2 * u - 1) ** 2
        xs = x * (0.8 + 0.26 * math.sin(math.pi * min(v * 1.2, 1.0)))
        return (xs + cx, y, z)
    V, F = M.grid(fn, 9, 9)
    m = P(V, F, mat, "mask")
    nn = np.cross(V[F[0][1]] - V[F[0][0]], V[F[0][2]] - V[F[0][0]])
    if nn[1] > 0:
        m.flip()
    parts = [M.solidify(m, thick, offset=-1.0)]

    def surf(x, z, out=0.0):
        v = (z - hz) / height
        u = 0.5 + (x - cx) / width / (0.8 + 0.26 * math.sin(math.pi * min(max(v, 0.0) * 1.2, 1.0)))
        return np.array([x, fn(min(max(u, 0.0), 1.0), min(max(v, 0.0), 1.0))[1] - out, z])
    # brow ridge, nose, almond eye slits (dark recess + white light), mouth with jade teeth
    for sx in (1, -1):
        pts = [surf(sx * x, hz + z * height, 0.004) for x, z in ((0.008, 0.69), (0.034, 0.74), (0.062, 0.7))]
        parts.append(A.tube(pts, 0.011, mat, n=5))
        pts = [surf(sx * x, hz + z * height, 0.002) for x, z in ((0.012, 0.588), (0.03, 0.608), (0.054, 0.592))]
        parts.append(A.tube(pts, (0.012, 0.006), "BH_Shadow", n=4, up=(0, -1, 0)))
        pts = [surf(sx * x, hz + z * height, 0.006) for x, z in ((0.016, 0.59), (0.031, 0.605), (0.05, 0.593))]
        parts.append(A.tube(pts, (0.0065, 0.003), eyes, n=4, up=(0, -1, 0)))
    pts = [surf(0, hz + z * height, o) for z, o in ((0.66, 0.004), (0.5, 0.013), (0.42, 0.012))]
    parts.append(A.tube(pts, [(0.012, 0.01), (0.016, 0.013), (0.014, 0.008)], mat, n=5))
    m0 = surf(0, hz + 0.24 * height, 0.003)
    parts.append(A.ball(m0, 0.03, "BH_Shadow", n=10, rings=4, scale=(1.25, 0.35, 0.45)))
    for k in range(5):
        x = (k - 2) * 0.011
        q = surf(x, hz + 0.27 * height, 0.008)
        parts.append(A.taper([q + (0, 0, 0.004), q - (0, 0, 0.012)], 0.0045, 0.002, "BH_Horn", n=4))
    # gold band across the brow of the mask
    parts.append(A.tube([surf(x, hz + 0.86 * height, 0.002) for x in np.linspace(-0.06, 0.06, 7)], 0.0045, "BH_Gold",
                        n=4))
    return parts, surf


# ================================================================================================= sleeper
def build(body):
    sb = K.SB(body, SCALE)
    torso(sb)
    loins(sb)
    head(sb)
    for s in ("L", "R"):
        arm(sb, s)
        leg(sb, s)
    K.trousers(sb, "BH_Cloth_Primary", loose=0.8, end=0.85)
    K.boots(sb, "BH_Cloth_Primary", "BH_Cloth_Secondary", shaft_top=0.32, cuff=False)


def torso(sb):
    rows = K.grow_rows(TORSO, LG)
    V, F = torso_loft([r for r in rows if r[0] >= 0.96], n=24, cap1=True)
    sb.add(P(V, F, "BH_Cloth_Primary", "linen"), weights=K.TORSO_W)
    # diagonal bandage courses (each a strip winding round the torso, rising toward the left)
    for k, z0 in enumerate(np.arange(0.97, 1.47, 0.058)):
        pts, ups = [], []
        fr = np.linspace(0, 1, 25)
        for f in fr:
            z = z0 + 0.05 * math.sin(2 * math.pi * f + k * 0.7)
            z = min(max(z, 0.97), 1.49)
            q = K.ring_frac(rows, z, 0.004, [f])[0]
            pts.append(q)
            ups.append(normalize(np.array([q[0], q[1], 0.0])))
        mat = "BH_Cloth_Secondary" if k in (3, 7) else "BH_Cloth_Primary"
        V, F = M.tube(pts, [(0.016, 0.004)] * len(pts), n=4, up=ups, p=3.0)
        sb.add(P(V, F, mat, "course"), weights=K.TORSO_W)
    # sunken ribs showing through a torn patch on the right flank (dried flesh)
    p, R = surf_frame(rows, 0.84, 1.2, 0.0)
    sb.add(A.ball(p + R[:, 1] * 0.006, 0.05, "BH_Skin", n=8, rings=5, scale=(1.0, 0.35, 1.3)).rot(np.eye(3)),
           weights=K.TORSO_W)
    for dz in (-0.03, 0.0, 0.03):
        q, _ = surf_frame(rows, 0.84, 1.2 + dz, 0.002)
        sb.add(A.tube([q + R[:, 0] * 0.035, q, q - R[:, 0] * 0.035], 0.006, "BH_Bone", n=4), weights=K.TORSO_W)
    # jade pectoral: 4 x 5 plaques sewn with gold wire, a larger centre plaque with the binding knot
    for prt in torso_plaques(rows, [-0.085, -0.042, 0.0, 0.042, 0.085], [1.25, 1.31, 1.37, 1.43], 0.012, 0.05, 0.052):
        sb.add(prt, "chest")
    for prt in torso_plaques(rows, np.linspace(0, 1, 14, endpoint=False), [1.485], 0.014, 0.05, 0.03, t=0.01,
                             stitch=False):
        sb.add(prt, "chest")
    # collar edge (gold wire ring above the plaques)
    ring = K.ring_frac(rows, 1.505, 0.012, np.linspace(0, 1, 25))
    sb.add(A.tube(ring, 0.006, "BH_Gold", n=4, cap=False), "chest")
    # plaque belt
    for prt in torso_plaques(rows, np.linspace(0, 1, 16, endpoint=False), [1.01], 0.014, 0.055, 0.05, t=0.012,
                             stitch=False):
        sb.add(prt, "hips")
    V, F = K.band(rows, 0.975, 1.045, 0.01, 0.0, n=28)
    sb.add(P(V, F, "BH_Cloth_Secondary", "belt"), "hips")
    # binding wire: two glowing strands crossing round the chest and a band round the waist (white)
    for ph in (0.0, 0.5):
        pts = []
        for f in np.linspace(0, 1, 33):
            z = 1.24 + 0.1 * math.sin(2 * math.pi * (f + ph))
            pts.append(K.ring_frac(rows, z, 0.018, [f])[0])
        sb.add(A.tube(pts, 0.0055, "BH_Emissive", n=4, cap=False), "chest")
    pts = [K.ring_frac(rows, 1.1 + 0.015 * math.sin(6 * math.pi * f), 0.012, [f])[0] for f in np.linspace(0, 1, 33)]
    sb.add(A.tube(pts, 0.005, "BH_Emissive", n=4, cap=False), weights=K.TORSO_W)
    # binding knot: a gold-wire knot at the breastbone where the strands meet
    q, R = surf_frame(rows, 0.0, 1.2, 0.02)
    sb.add(A.ball(q, 0.02, "BH_Gold", n=8, rings=5, scale=(1.2, 0.6, 1.0)), "chest")
    sb.add(A.ball(q - R[:, 1] * 0.012, 0.009, "BH_Emissive", n=6, rings=4), "chest")
    # back: loose stained bandage ends hanging from the shoulders
    for k, (x, ln) in enumerate(((0.07, 0.34), (-0.05, 0.26), (0.0, 0.42))):
        z = 1.44
        top = np.array([x, back_y(rows, x, z) + 0.008, z])
        sb.add(A.rag_strip(top, (0.0, 0.25, -1.0), ln, 0.04, "BH_Cloth_Secondary", n=5, thick=0.005,
                           sway=(0.02 * (k - 1), 0.03), seed=k + 1.0, out=(0, 1, 0)),
               weights=K.zspec_w([(1.0, "spine"), (1.3, "chest")]))


def loins(sb):
    rows = K.grow_rows(TORSO, LG + 0.022)
    for front in (True, False):
        pnl = HS.cloth_panel(rows, 1.0, 0.56, lambda z: 0.095 + 0.03 * (1.0 - z), front=front, nu=6, nv=7,
                             mat="BH_Cloth_Primary" if front else "BH_Cloth_Secondary", gap=0.01, hang=0.05, rag=0.04,
                             teeth=5, thick=0.007, belt_z=0.98, seed=2.0 if front else 5.0)
        sb.add(pnl, weights=Z.centre_w(0.98, 0.55, 0.55))
    # loose bandage ends hanging from the hip belt (sides)
    for k, (fr, ln) in enumerate(((0.2, 0.36), (0.27, 0.28), (0.74, 0.4), (0.8, 0.3))):
        p, R = surf_frame(rows, fr, 0.99, 0.014)
        lb = "thigh.L" if fr < 0.5 else "thigh.R"
        sb.add(A.rag_strip(p, (0.0, 0.0, -1.0) - R[:, 1] * 0.15, ln, 0.035, "BH_Cloth_Secondary" if k % 2 else
                           "BH_Cloth_Primary", n=5, thick=0.005, seed=k + 4.0, out=-R[:, 1]),
               weights=lambda V, lb=lb: [{"hips": 0.6, lb: 0.4}] * len(V))
    # a jade plaque hanging on the front flap
    y = front_y(rows, 0, 0.98) - 0.012 - 0.05 * 0.18 - 0.012
    V, F = M.box(0.06, 0.012, 0.075)
    sb.add(M.bevel(P(V, F, "BH_Stone", "flapplaque").move((0, y, 0.8)).rot(Rx(-3), center=(0, y, 0.98)), 0.003, 1),
           weights=Z.centre_w(0.98, 0.55, 0.55))
    sb.add(A.tube([(-0.03, y - 0.008, 0.77), (0.0, y - 0.009, 0.83), (0.03, y - 0.008, 0.77)], 0.004, "BH_Emissive",
                  n=4), weights=Z.centre_w(0.98, 0.55, 0.55))


def head(sb):
    K.neck_and_head(sb, skin="BH_Cloth_Primary", face=False)
    rows = K.grow_rows(K.HEAD, 0.004)
    # head wraps: tilted bandage rings over the skull and jaw
    for k, (zc, tilt) in enumerate(((1.62, 6), (1.66, -8), (1.74, 10), (1.78, -6), (1.8, 14))):
        fr = np.linspace(0, 1, 21)
        pts, ups = [], []
        for f in fr:
            a = 2 * math.pi * f
            z = zc + math.sin(a) * math.tan(math.radians(tilt)) * 0.08
            z = min(max(z, 1.592), 1.81)
            q = K.ring_frac(rows, z, 0.0, [f], p=2.1)[0]
            pts.append(q)
            ups.append(normalize(np.array([q[0], q[1], 0.25])))
        V, F = M.tube(pts, [(0.014, 0.004)] * len(pts), n=4, up=ups, p=3.0)
        sb.add(P(V, F, "BH_Cloth_Secondary" if k == 2 else "BH_Cloth_Primary", "headwrap"), "head")
    # neck wraps
    for z in (1.5, 1.545):
        sb.add(linen_wrap((0, 0.0, z - 0.02), (0, -0.004, z + 0.02), 0.054, 1.2, width=0.024), weights=K.HEAD_W)
    parts, surf = death_mask(1.598, width=0.158, height=0.205, ytop=-0.084)
    for prt in parts:
        sb.add(prt, "head")
    # gold ear spools with a jade bead, and a jade brow plaque above the mask
    for sx in (1, -1):
        V, F = M.lathe([(0.0, -0.007), (0.028, -0.006), (0.032, 0.0), (0.028, 0.008), (0.0, 0.006)], 12)
        sb.add(P(V, F, "BH_Gold", "spool").rot(Ry(90 * sx)).move((sx * 0.082, -0.0, 1.69)), "head")
        sb.add(A.ball((sx * 0.09, -0.0, 1.69), 0.013, "BH_Stone", n=6, rings=4), "head")
    q = surf(0, 1.808, 0.0)
    V, F = M.box(0.07, 0.014, 0.034)
    sb.add(M.bevel(P(V, F, "BH_Stone", "browplaque").rot(Rx(-18)).move(q + (0, 0.004, 0.008)), 0.003, 1), "head")


def arm(sb, s):
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    K.bare_arm(sb, s, skin="BH_Cloth_Primary", r_up=0.043, r_fore=0.037, r_wrist=0.029, bulk=0.95)
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    w = sb.seg(["chest", "shoulder." + s, ua, fa, ha], power=9)
    # bandage courses
    sb.add(linen_wrap(sh + (el - sh) * 0.08, el - (el - sh) * 0.05, 0.047, 3.2, width=0.026), ua)
    sb.add(linen_wrap(el + (wr - el) * 0.05, wr + (wr - el) * 0.02, 0.04, 3.4, width=0.024,
                      mat="BH_Cloth_Secondary" if s == "L" else "BH_Cloth_Primary"), fa)
    # glowing binding wire round upper arm and forearm
    sb.add(glow_wrap(sh + (el - sh) * 0.2, sh + (el - sh) * 0.8, 0.05, 2.0, phase=0.4), ua)
    sb.add(glow_wrap(el + (wr - el) * 0.12, el + (wr - el) * 0.4, 0.044, 1.5, phase=1.2), fa)
    # jade bracer: plaques round the lower forearm, gold stitching
    Ax = sb.axes(fa)
    fl = float(np.linalg.norm(wr - el))
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        nrm = Ax[:, 0] * math.cos(a) + Ax[:, 2] * math.sin(a)
        c = el + (wr - el) * 0.7 + nrm * 0.045
        R = np.stack([np.cross(Ax[:, 1], nrm), -nrm, Ax[:, 1]], 1)
        sb.add(plaque(c, R, 0.034, 0.1, t=0.008), fa)
    sb.add(A.tube([el + (wr - el) * 0.52 + 0 * fl, el + (wr - el) * 0.54], 0.05, "BH_Gold", n=10), fa)
    sb.add(A.tube([el + (wr - el) * 0.86, el + (wr - el) * 0.88], 0.047, "BH_Gold", n=10), fa)
    # a loose bandage end from the elbow
    sb.add(A.rag_strip(el + (0, 0.03, -0.02), (0.0, 0.3, -1.0), 0.2, 0.03, "BH_Cloth_Secondary", n=4, thick=0.005,
                       seed=3.0 if s == "L" else 7.0, out=(0, 1, 0)), fa)
    # open claw hand: wrapped palm, long bony fingers, jade nail-guards
    for prt in A.open_palm(sb.b, s, "BH_Cloth_Primary", s=SCALE * 0.95):
        sb.add_real(prt, ha)
    for prt in A.bony_fingers(sb.b, s, "BH_Cloth_Primary", length=0.115 * SCALE, r=0.0068 * SCALE, curl=0.85,
                              spread=1.15, nails="BH_Horn", open_hand=True):
        sb.add_real(prt, ha)
    # (the nail-guards: dark jade cones over the last joint)
    L, Afr = A.hand_frame(sb.b, s)
    for k in range(4):
        y = (-0.03 + 0.02 * k) * 1.15
        lk = 0.115 * (0.85 + 0.15 * (k in (1, 2)))
        tip0 = L(0.02 + lk * 0.8, y * 1.45, -lk * 0.25 * 0.85)
        tip1 = L(0.02 + lk * 1.05, y * 1.6, -lk * 0.72 * 0.85)
        sb.add_real(A.taper([tip0, tip1], 0.0085, 0.0015, "BH_Stone", n=5), ha)


def leg(sb, s):
    th, sh = "thigh." + s, "shin." + s
    h, k, a = sb.head(th), sb.head(sh), sb.tail(sh)
    sb.add(linen_wrap(h + (k - h) * 0.25, k - (k - h) * 0.04, 0.066, 3.4, width=0.03), th)
    sb.add(linen_wrap(k + (a - k) * 0.06, a + (k - a) * 0.12, 0.052, 3.6, width=0.028), sh)
    sb.add(glow_wrap(h + (k - h) * 0.35, h + (k - h) * 0.75, 0.072, 1.6, phase=0.7 if s == "L" else 2.0), th)
    # jade shin guard: three stacked plaques down the front, gold rims
    for i, u in enumerate((0.22, 0.42, 0.62)):
        c = k + (a - k) * u + np.array([0, -0.058, 0])
        R = np.stack([np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), normalize(k - a)], 1)
        sb.add(plaque(c, R, 0.07 - 0.008 * i, 0.085, t=0.01), sh)
    sb.add(A.tube([k + (a - k) * 0.1 + (0, -0.064, 0), k + (a - k) * 0.72 + (0, -0.064, 0)], 0.0035, "BH_Emissive", n=4),
           sh)
    # knee: a round jade plaque
    sb.add(A.ball(k + (0, -0.058, 0.0), 0.038, "BH_Stone", n=10, rings=5, scale=(1, 0.4, 1)),
           weights=lambda V, s=s: [{"thigh." + s: 0.4, "shin." + s: 0.6}] * len(V))
