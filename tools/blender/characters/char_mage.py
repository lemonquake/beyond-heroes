"""Mage hero: arcane traveler. Layered hooded long coat (deep indigo) with split front/back panels over trousers and
boots, scalloped shoulder mantle, chest harness with an aether medallion, one steel pauldron (left), leather bracer
(right), aether-inlaid focus gauntlet with a floating aether ring (left, the casting hand), runic gold/aether trim,
belt with tomes and vials, bearded face under the hood with faint glowing eyes, two floating aether crystals
(crystal.L / crystal.R bones, secondary motion).

Shares the standard skeleton (same proportions / rest pose as the Knight) and the whole action library.
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import Body, torso_ring, torso_loft, interp_rows, front_y, back_y, dome, fist, smoothstep, M_align_z
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions

PROPS = proportions()

CRYSTAL_L = (0.30, 0.20, 1.66)
CRYSTAL_R = (-0.27, 0.23, 1.56)
EXTRA_BONES = [
    ("crystal.L", (0.0, 0.03, 1.40), CRYSTAL_L, "chest", (0, 0, 1)),
    ("crystal.R", (0.0, 0.03, 1.40), CRYSTAL_R, "chest", (0, 0, 1)),
]
PALETTE = "mage"

# torso cross-sections (z, rx, ry_front, ry_back, keel) of the body under the coat
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
COAT_G = 0.013


# ----------------------------------------------------------------------------------------------------------------
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
            d = None
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


def strip_tube(pts, w, t, mat, n=6, up=None):
    """Flat strap / trim along a polyline: width w across, thickness t along `up` (surface normal)."""
    pts = np.asarray(pts, float)
    ups = up if up is not None else [(0, -1, 0)] * len(pts)
    V, F = M.tube(pts, [(w / 2, t / 2)] * len(pts), n=n, up=[np.asarray(u, float) for u in ups], p=3.0)
    return M.Part(V, F, mat)


def round_tube(pts, r, mat, n=6, cap=True, closed=False):
    pts = np.asarray(pts, float)
    V, F = M.tube(pts, [(r, r)] * len(pts), n=n, up=(0, 0, 1) if abs(normalize(pts[-1] - pts[0])[2]) < 0.9 else (0, -1, 0),
                  cap0=cap, cap1=cap)
    return M.Part(V, F, mat)


def crystal(center, length, radius, mat="BH_Aether", sides=6, tilt=(0, 0, 0)):
    c = np.asarray(center, float)
    V, F = M.lathe([(0, -length / 2), (radius * 0.8, -length * 0.18), (radius, 0.0), (radius * 0.85, length * 0.14),
                    (0, length / 2)], sides)
    p = M.Part(V, F, mat, name="crystal")
    p.rot(Rx(tilt[0]) @ Ry(tilt[1]) @ Rz(tilt[2])).move(c)
    return p


# ----------------------------------------------------------------------------------------------------------------
def build(body: Body):
    add = body.add
    torso_parts(body)
    coat_skirt(body)
    legs(body)
    arms(body)
    head_and_hood(body)
    mantle(body)
    belt(body)
    crystals(body)


# ---------------------------------------------------------------- torso: vest, open coat, harness
def torso_parts(body):
    add = body.add
    V, F = torso_loft([r for r in TORSO if 0.98 <= r[0]], n=24, cap1=True)
    add(M.Part(V, F, "BH_Cloth_Secondary", name="vest"), weights=TORSO_W)
    # vest lacing (dark leather cross-stitch down the sternum)
    for z in np.linspace(1.12, 1.42, 6):
        y = front_y(TORSO, 0, z) - 0.004
        V, F = M.box(0.034, 0.006, 0.007, center=(0, y, z))
        p = M.Part(V, F, "BH_Leather").rot(Ry(28), center=(0, y, z))
        add(p, weights=TORSO_W)
    # coat body: open V in the front (half-angle fraction grows toward the collar)
    zs = [1.0, 1.06, 1.14, 1.22, 1.30, 1.37, 1.43, 1.475, 1.505]
    nu = 34
    rings = []
    edges = []
    for z in zs:
        t = (z - 1.0) / 0.505
        a0 = 0.028 + 0.075 * t ** 1.6
        fr = a0 + (1 - 2 * a0) * np.linspace(0, 1, nu)
        g = COAT_G + 0.006 * (1 - t)
        rings.append(ring_frac(TORSO, z, g, fr))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    coat = M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="coat"), 0.008, offset=1.0, bevel_w=0.0)
    add(coat, weights=TORSO_W)
    # collar: rolled band around the neck opening
    top = rings[-1]
    V, F = M.tube(top, [(0.012, 0.012)] * len(top), n=6, up=(0, 0, 1), cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Cloth_Primary", name="collar"), "chest")
    # lapel trims (runic gold) along both open edges
    for k in (0, -1):
        pts = np.array([r[k] for r in rings])
        pts = pts + np.array([0, -0.006, 0])
        V, F = M.tube(pts, [(0.009, 0.005)] * len(pts), n=6, up=(0, -1, 0), p=3.0)
        add(M.Part(V, F, "BH_Gold", name="lapel"), weights=TORSO_W)
    # chest harness: X straps over coat and vest meeting at an aether medallion
    for sx in (1, -1):
        pts, ups = [], []
        for t in np.linspace(0, 1, 9):
            x = sx * (0.13 - 0.26 * t)
            z = 1.47 - 0.40 * t
            y = min(front_y(TORSO, x, z) - COAT_G - 0.016, front_y(TORSO, x, z) - 0.02)
            pts.append((x, y, z))
            ups.append((0.25 * x, -1, 0))
        add(strip_tube(pts, 0.03, 0.006, "BH_Leather", up=ups), weights=TORSO_W)
        # over the shoulder to the back
        pts, ups = [], []
        for t in np.linspace(0, 1, 7):
            a = math.pi * (0.5 - t) * 0.95
            x = sx * 0.13
            y = -0.10 * math.sin(a) + 0.01
            z = 1.47 + 0.035 * math.cos(a)
            pts.append((x, y if t < 0.5 else y + 0.005, z))
            ups.append((0, math.sin(a) * -1, math.cos(a)))
        add(strip_tube(pts, 0.03, 0.006, "BH_Leather", up=ups), "chest")
        pts = []
        for t in np.linspace(0, 1, 7):
            x = sx * (0.13 - 0.26 * t)
            z = 1.47 - 0.38 * t
            y = back_y(TORSO, x, z) + COAT_G + 0.012
            pts.append((x, y, z))
        add(strip_tube(pts, 0.03, 0.006, "BH_Leather", up=[(0, 1, 0)] * 7), weights=TORSO_W)
    zc = 1.27
    yc = front_y(TORSO, 0, zc) - COAT_G - 0.024
    V, F = M.lathe([(0, -0.012), (0.036, -0.010), (0.042, -0.003), (0.044, 0.004), (0.03, 0.008), (0, 0.009)], 16)
    med = M.Part(V, F, "BH_Gold", name="medallion").rot(Rx(90)).move((0, yc, zc))
    add(M.bevel(med, 0.002, 1), weights=TORSO_W)
    add(crystal((0, yc - 0.012, zc), 0.06, 0.018, tilt=(90, 0, 0)), weights=TORSO_W)
    # back buckle
    V, F = M.box(0.05, 0.012, 0.05, center=(0, back_y(TORSO, 0, 1.26) + COAT_G + 0.018, 1.265))
    add(M.bevel(M.Part(V, F, "BH_Gold"), 0.004, 1), weights=TORSO_W)


# ---------------------------------------------------------------- long coat skirt (4 panels)
def skirt_rows():
    rows = []
    for z in (0.30, 0.40, 0.52, 0.64, 0.76, 0.88, 0.98, 1.07):
        t = (1.07 - z)
        rows.append((z, 0.168 + 0.15 * t, 0.112 + 0.15 * t, 0.112 + 0.17 * t, 0.0))
    return rows


def panel_w(side, back):
    leg_max = 0.62 if back else 0.85

    def wfn(V):
        out = []
        for v in V:
            z = v[2]
            tl = float(smoothstep(1.02, 0.62, z)) * leg_max
            ts = float(smoothstep(0.56, 0.30, z)) * 0.32
            d = {"hips": 1 - tl}
            if tl > 1e-4:
                d["thigh." + side] = tl * (1 - ts)
                if ts > 1e-4:
                    d["shin." + side] = tl * ts
            out.append({k: x for k, x in d.items() if x > 1e-4})
        return out
    return wfn


def coat_skirt(body):
    rows = skirt_rows()
    zs = [r[0] for r in rows]
    for side, sgn in (("L", 1), ("R", -1)):
        for back in (False, True):
            nu = 9
            rings = []
            hem = []
            for z in zs:
                t = (1.07 - z) / 0.77
                gf = 0.022 + 0.05 * t
                sg = 0.004 + 0.012 * t
                sb = 0.003 + 0.016 * t
                a, b = (gf, 0.25 - sg) if not back else (0.25 + sg, 0.5 - sb)
                fr = np.linspace(a, b, nu)
                pts = ring_frac(rows, z, 0.0, fr, p=2.2)
                # soft vertical folds grow toward the hem
                ang = np.linspace(0, 1, nu)
                fold = 0.012 * t ** 1.3 * np.sin(ang * math.pi * 3 + (0.6 if back else 0.0))
                rad = normalize_rows(pts[:, :2])
                pts[:, 0] += rad[:, 0] * fold
                pts[:, 1] += rad[:, 1] * fold
                if sgn < 0:
                    pts[:, 0] *= -1
                rings.append(pts)
            if sgn < 0:
                rings = [r[::-1] for r in rings]
            V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
            p = M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="coat_panel"), 0.008, offset=1.0)
            body.add(p, weights=panel_w(side, back))
            # hem trim (gold) and aether rune dashes on the front panels
            hem = rings[0] + np.array([0, 0, 0.012])
            hem_o = hem.copy()
            hem_o[:, :2] += normalize_rows(hem[:, :2]) * 0.009
            V, F = M.tube(hem_o, [(0.006, 0.011)] * len(hem_o), n=6, up=(0, 0, 1), p=3.0)
            body.add(M.Part(V, F, "BH_Gold", name="hem"), weights=panel_w(side, back))
            if not back:
                edge = np.array([r[0] if sgn > 0 else r[-1] for r in rings])
                eo = edge.copy()
                eo[:, :2] += normalize_rows(edge[:, :2]) * 0.009
                V, F = M.tube(eo, [(0.008, 0.005)] * len(eo), n=6, up=(0, -1, 0), p=3.0)
                body.add(M.Part(V, F, "BH_Gold", name="edge"), weights=panel_w(side, back))
                for k in range(1, 8):
                    q = hem_o[k] + np.array([0, 0, 0.035])
                    nrm = np.array([*normalize_rows(hem_o[k:k + 1, :2])[0], 0.0])
                    h = 0.028 if k % 2 else 0.016
                    V, F = M.box(0.007, 0.006, h)
                    rp = M.Part(V, F, "BH_Aether", name="rune")
                    rp.rot(Rz(math.degrees(math.atan2(nrm[1], nrm[0])) + 90)).move(q + nrm * 0.001)
                    body.add(rp, weights=panel_w(side, back))


def normalize_rows(A):
    A = np.asarray(A, float)
    n = np.linalg.norm(A, axis=1, keepdims=True)
    return A / np.maximum(n, 1e-9)


# ---------------------------------------------------------------- legs: trousers + boots
def legs(body):
    # pelvis / seat of the trousers
    V, F = torso_loft([(0.84, 0.150, 0.092, 0.10, 0.0), (0.92, 0.152, 0.098, 0.104, 0.0),
                       (1.0, 0.146, 0.096, 0.10, 0.0)], n=24)
    body.add(M.Part(V, F, "BH_Cloth_Secondary", name="seat"),
             weights=body.skirt_weights(0.98, 0.84, max_leg=0.7, center_w=0.05))
    for s in ("L", "R"):
        th, sh = "thigh." + s, "shin." + s
        h, k, a = body.head(th), body.head(sh), body.tail(sh)
        pts = [h + (0, 0, 0.04), h + (k - h) * 0.4, k + (0, 0, 0.02), k + (a - k) * 0.35, k + (a - k) * 0.62]
        prof = [(0.078, 0.082), (0.068, 0.072), (0.054, 0.058), (0.05, 0.054), (0.044, 0.046)]
        V, F = M.tube(pts, prof, n=12, up=(0, -1, 0))
        body.add(M.Part(V, F, "BH_Cloth_Secondary", name="trouser"), weights=body.seg_weights([th, sh], power=10))
        for part, bone in boot(body, s):
            body.add(part, bone)


def boot(body, s):
    hx = PROPS["hip_x"] * (1 if s == "L" else -1)
    sh = "shin." + s
    out = []
    # shaft
    k, a = body.head(sh), body.tail(sh)
    pts = [a + (0, 0.004, 0.03), a + (k - a) * 0.4, a + (k - a) * 0.66]
    V, F = M.tube(pts, [(0.05, 0.054), (0.052, 0.056), (0.056, 0.06)], n=12, up=(0, -1, 0), cap1=False)
    out.append((M.solidify(M.Part(V, F, "BH_Leather", name="boot"), 0.004, offset=-1.0), sh))
    c0 = a + (k - a) * 0.64
    c1 = a + (k - a) * 0.76
    V, F = M.tube([c0, c1], [(0.063, 0.067), (0.066, 0.07)], n=12, up=(0, -1, 0), cap0=False, cap1=False)
    out.append((M.solidify(M.Part(V, F, "BH_Leather", name="cuff"), 0.006, offset=-1.0, bevel_w=0.002), sh))
    V, F = M.tube([c0 + (0, 0, 0.006), c0 - (0, 0, 0.002)], [(0.066, 0.069)] * 2, n=12, up=(0, -1, 0))
    out.append((M.Part(V, F, "BH_Gold", name="cuff_rim"), sh))

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
    out.append((M.bevel(M.Part(V, F, "BH_Leather", name="bootfoot"), 0.003, 1, angle=45), "foot." + s))
    toe = rings([(-0.115, 0.046, 0.065), (-0.17, 0.043, 0.054), (-0.212, 0.032, 0.042), (-0.232, 0.014, 0.03)])
    V, F = M.loft(toe[::-1])
    out.append((M.bevel(M.Part(V, F, "BH_Leather", name="boottoe"), 0.003, 1, angle=45), "toe." + s))
    V, F = M.box(0.094, 0.2, 0.016, center=(hx, -0.03, 0.008))
    out.append((M.bevel(M.Part(V, F, "BH_DarkSteel", name="sole"), 0.004, 1), "foot." + s))
    V, F = M.box(0.076, 0.1, 0.014, center=(hx, -0.18, 0.007))
    out.append((M.bevel(M.Part(V, F, "BH_DarkSteel", name="sole_t"), 0.004, 1), "toe." + s))
    # ankle strap with a gold buckle
    V, F = M.tube([(hx, 0.02, 0.11), (hx, -0.01, 0.1)], [(0.05, 0.052), (0.05, 0.052)], n=12, up=(0, -1, 0))
    out.append((M.Part(V, F, "BH_Leather", name="strap"), "foot." + s))
    V, F = M.box(0.012, 0.022, 0.022, center=(hx + 0.05 * (1 if s == "L" else -1), 0.004, 0.106))
    out.append((M.Part(V, F, "BH_Gold", name="buckle"), "foot." + s))
    return out


# ---------------------------------------------------------------- arms
def arms(body):
    for s in ("L", "R"):
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
        # coat sleeve: shoulder -> elbow -> bell cuff at 60% of the forearm
        pts = [sh + (sh - el) * 0.05, sh + (el - sh) * 0.3, sh + (el - sh) * 0.75, el,
               el + (wr - el) * 0.3, el + (wr - el) * 0.5, el + (wr - el) * 0.62]
        prof = [(0.058, 0.062), (0.062, 0.066), (0.057, 0.06), (0.056, 0.058), (0.058, 0.06), (0.066, 0.068),
                (0.074, 0.076)]
        V, F = M.tube(pts, prof, n=14, up=(0, -1, 0), cap1=False)
        sl = M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="sleeve"), 0.006, offset=-1.0)
        body.add(sl, weights=body.seg_weights([ua, fa], power=10))
        c = el + (wr - el) * 0.62
        d = normalize(wr - el)
        V, F = M.tube([c - d * 0.012, c + d * 0.004], [(0.077, 0.079)] * 2, n=14, up=(0, -1, 0))
        body.add(M.Part(V, F, "BH_Gold", name="sleeve_trim"), fa)
        # forearm under the bell
        V, F = M.tube([el + (wr - el) * 0.4, wr], [(0.042, 0.044), (0.036, 0.038)], n=10, up=(0, -1, 0))
        body.add(M.Part(V, F, "BH_Cloth_Secondary", name="underarm"), fa)
        if s == "R":
            # leather bracer with gold rims and studs
            b0, b1 = el + (wr - el) * 0.55, wr + (wr - el) * 0.02
            V, F = M.tube([b0, (b0 + b1) / 2, b1], [(0.047, 0.05), (0.046, 0.048), (0.043, 0.045)], n=12,
                          up=(0, -1, 0))
            body.add(M.bevel(M.Part(V, F, "BH_Leather", name="bracer"), 0.003, 1, angle=50), fa)
            for q in (b0, b1):
                V, F = M.tube([q - d * 0.006, q + d * 0.006], [(0.049, 0.052)] * 2, n=12, up=(0, -1, 0))
                body.add(M.Part(V, F, "BH_Gold", name="bracer_rim"), fa)
            for prt in fist(body, s, "BH_Leather", "BH_Leather", gauntlet=True):
                body.add(prt, ha)
        else:
            # focus gauntlet: dark steel vambrace with gold rims, aether channels and a floating aether ring
            b0, b1 = el + (wr - el) * 0.5, wr + (wr - el) * 0.05
            V, F = M.tube([b0, (b0 + b1) / 2, b1], [(0.05, 0.052), (0.049, 0.05), (0.047, 0.049)], n=14,
                          up=(0, -1, 0))
            body.add(M.bevel(M.Part(V, F, "BH_DarkSteel", name="vambrace"), 0.003, 1, angle=50), fa)
            for q in (b0, b1):
                V, F = M.tube([q - d * 0.007, q + d * 0.007], [(0.053, 0.055)] * 2, n=14, up=(0, -1, 0))
                body.add(M.Part(V, F, "BH_Gold", name="vamb_rim"), fa)
            L = PROPS["fore_len"]
            for off in (-0.018, 0.018):
                line = body.lpt(fa, [(off, u * L, 0.05 - 0.004 * u) for u in np.linspace(0.56, 0.98, 6)])
                body.add(round_tube(line, 0.0035, "BH_Aether", n=5), fa)
            ring = body.lpt(fa, [(0.078 * math.cos(a), 1.02 * L, 0.078 * math.sin(a))
                                 for a in np.linspace(0, 2 * math.pi, 25)])
            V, F = M.tube(ring, [(0.005, 0.005)] * len(ring), n=5, up=list(np.array([d] * len(ring))),
                          cap0=False, cap1=False)
            body.add(M.Part(V, F, "BH_Aether", name="focus_ring"), fa)
            for prt in fist(body, s, "BH_Gold", "BH_DarkSteel", gauntlet=True):
                body.add(prt, ha)
            # aether gem on the back of the hand
            A = body.axes("weapon." + s)
            o = body.head("weapon." + s)
            g = o + A @ np.array([0.035, 0.0, 0.05])
            body.add(crystal(g, 0.035, 0.012, tilt=(0, 0, 0)).rot(M_align_z(A[:, 2]), center=g), ha)
    pauldron_L(body)


def pauldron_L(body):
    s = "L"
    ua = "upper_arm." + s
    sh = body.head(ua)
    el = body.head("forearm." + s)
    armdir = normalize(el - sh)
    axis = normalize(np.array([0.55, 0.0, 0.85]))
    c = sh + np.array([0.02, 0.0, 0.02])
    V, F = dome(c, axis, 0.118, a_max=70, n=18, rings=6, scale=(1.0, 1.1, 1.0))
    body.add(M.solidify(M.Part(V, F, "BH_Steel", name="pauldron"), 0.007, offset=-1, bevel_w=0.002), ua)
    Rm = M_align_z(axis, (0, 0, 1))
    # raised gold keel + aether channel along the front-back meridian, gold boss at the apex
    for off, mat, r, rad in ((0.0, "BH_Gold", 0.009, 0.121), (0.03, "BH_Aether", 0.0035, 0.119),
                             (-0.03, "BH_Aether", 0.0035, 0.119)):
        mer = []
        for lat in np.linspace(-62, 62, 13):
            a = math.radians(lat)
            v = np.array([math.sin(math.asin(off / rad)) * rad, rad * math.sin(a) * 1.1, rad * math.cos(a)])
            mer.append(c + Rm @ v)
        V, F = M.tube(mer, [(r, r)] * len(mer), n=6, up=axis)
        body.add(M.Part(V, F, mat, name="p_keel"), ua)
    V, F = M.sphere(0.02, 10, 6, center=c + axis * 0.118, scale=(1, 1, 0.6))
    body.add(M.Part(V, F, "BH_Gold", name="p_boss").rot(M_align_z(axis), center=c + axis * 0.118), ua)
    for lat, mat, r in ((70, "BH_Gold", 0.007),):
        rim = []
        for i in range(25):
            a = 2 * math.pi * i / 24
            rr = 0.118 * math.sin(math.radians(lat))
            z = 0.118 * math.cos(math.radians(lat))
            rim.append(c + Rm @ np.array([rr * math.cos(a), rr * math.sin(a) * 1.1, z + 0.002]))
        V, F = M.tube(rim, [(r, r)] * len(rim), n=6, up=axis, cap0=False, cap1=False)
        body.add(M.Part(V, F, mat, name="p_rim"), ua)
    out = np.array([1.0, 0, 0])
    ax_side = normalize(out - armdir * np.dot(out, armdir))
    ax_fwd = np.cross(armdir, ax_side)
    for i in range(2):
        rr = 0.088 - 0.008 * i
        ctr = sh + armdir * (0.1 + 0.055 * i)
        loops = []
        for z_off in (0.0, 0.055):
            loop = []
            for k in range(13):
                a = math.radians(-110 + 220 * k / 12)
                pdir = ax_side * math.cos(a) + ax_fwd * math.sin(a) * 1.1
                loop.append(ctr + armdir * (z_off - 0.028) + pdir * (rr + 0.01 * (z_off > 0)))
            loops.append(np.array(loop))
        V, F = M.loft(loops, cap0=False, cap1=False, closed=False)
        body.add(M.solidify(M.Part(V, F, "BH_Steel", name="lame"), 0.005, offset=1, bevel_w=0.0015), ua)
    # leather strap under the arm
    pts = [sh + ax_side * 0.07 + ax_fwd * 0.06 + armdir * 0.13, sh - ax_side * 0.055 + armdir * 0.13,
           sh + ax_side * 0.07 - ax_fwd * 0.06 + armdir * 0.13]
    V, F = M.tube(pts, [(0.012, 0.004)] * 3, n=6, up=armdir, p=3.0)
    body.add(M.Part(V, F, "BH_Leather", name="p_strap"), ua)


# ---------------------------------------------------------------- head, face, hood
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

HOOD = [  # z, rx, ry_front, ry_back, cy, opening half-angle (deg)
    (1.500, 0.150, 0.125, 0.140, 0.020, 32),
    (1.555, 0.120, 0.105, 0.128, 0.020, 46),
    (1.620, 0.110, 0.106, 0.128, 0.010, 58),
    (1.680, 0.112, 0.110, 0.130, 0.000, 60),
    (1.740, 0.108, 0.110, 0.130, 0.004, 52),
    (1.790, 0.094, 0.104, 0.122, 0.014, 36),
    (1.830, 0.068, 0.078, 0.106, 0.030, 16),
    (1.862, 0.036, 0.040, 0.076, 0.052, 6),
    (1.885, 0.006, 0.006, 0.024, 0.095, 2),
]

HOOD_W = zspec_w([(1.49, "chest"), (1.54, "neck"), (1.57, "neck"), (1.62, "head")])
HEAD_W = zspec_w([(1.50, "chest"), (1.54, "neck"), (1.58, "neck"), (1.61, "head")])


def head_and_hood(body):
    add = body.add
    V, F = M.tube([(0, 0.0, 1.47), (0, -0.004, 1.54), (0, -0.01, 1.62)], [(0.055, 0.052), (0.05, 0.048), (0.05, 0.05)],
                  n=12, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="neck"), weights=HEAD_W)
    V, F = torso_loft(HEAD, n=22, p=2.1, cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Skin", name="head"), "head")
    # brow ridge, nose, eye sockets, glowing eyes
    V, F = M.tube([(-0.05, -0.068, 1.716), (0.0, -0.08, 1.722), (0.05, -0.068, 1.716)],
                  [(0.012, 0.008)] * 3, n=6, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="brow"), "head")
    V, F = M.tube([(0, -0.076, 1.712), (0, -0.087, 1.684), (0, -0.094, 1.662), (0, -0.088, 1.652)],
                  [(0.0065, 0.006), (0.009, 0.008), (0.012, 0.009), (0.008, 0.005)], n=6, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="nose"), "head")
    for sx in (1, -1):
        V, F = M.sphere(0.013, 8, 5, center=(sx * 0.029, -0.069, 1.699), scale=(1.15, 0.6, 0.75))
        add(M.Part(V, F, "BH_Shadow", name="socket"), "head")
        V, F = M.sphere(0.0062, 6, 4, center=(sx * 0.029, -0.075, 1.699), scale=(1.3, 0.7, 0.8))
        add(M.Part(V, F, "BH_Aether", name="eye"), "head")
    # beard along the jaw line and chin (mouth and cheeks stay visible) + moustache
    w = 0.215
    cols = np.linspace(-w, w, 13)
    rows = []
    for t in np.linspace(0, 1, 5):
        r = []
        for f in cols:
            a = abs(f) / w
            zb = 1.556 + 0.05 * a ** 2
            zt = 1.603 + 0.042 * a ** 1.3
            z = zb + (zt - zb) * t
            q = ring_frac(HEAD, max(z, 1.60), 0.006, [f], p=2.1)[0]
            q[2] = z
            if z < 1.6:
                q[1] -= (1.6 - z) * 0.35
            r.append(q)
        rows.append(np.array(r))
    V, F = M.loft(rows, cap0=False, cap1=False, closed=False)
    beard = M.solidify(M.Part(V, F, "BH_Hair", name="beard"), 0.01, offset=1.0)
    add(beard, "head")
    V, F = M.tube([(-0.034, -0.078, 1.648), (-0.012, -0.088, 1.655), (0.012, -0.088, 1.655), (0.034, -0.078, 1.648)],
                  [(0.006, 0.006), (0.008, 0.007), (0.008, 0.007), (0.006, 0.006)], n=6, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Hair", name="moustache"), "head")
    # hood shell
    nu = 22
    rings = []
    for (z, rx, ryf, ryb, cy, th) in HOOD:
        ring = []
        for u in np.linspace(0, 1, nu):
            a = math.radians(th + (360 - 2 * th) * u)
            sa, ca = math.sin(a), math.cos(a)
            x = rx * sa
            y = cy - (ryf if ca > 0 else ryb) * ca
            ring.append((x, y, z))
        rings.append(np.array(ring))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    hood = M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="hood"), 0.011, offset=-1.0)
    add(hood, weights=HOOD_W)
    edge = [r[0] for r in rings] + [r[-1] for r in rings[::-1]]
    edge = np.array(edge[:-1] if np.allclose(edge[len(rings) - 1], edge[len(rings)]) else edge)
    V, F = M.tube(edge, [(0.007, 0.007)] * len(edge), n=6, up=(0, 0, 1))
    add(M.Part(V, F, "BH_Gold", name="hood_trim"), weights=HOOD_W)
    # shadowed interior lining just inside the opening (reads as depth under the hood)
    inner = []
    for (z, rx, ryf, ryb, cy, th) in HOOD[1:6]:
        ring = []
        for u in np.linspace(0, 1, nu):
            a = math.radians(th + (360 - 2 * th) * u)
            ring.append((rx * 0.9 * math.sin(a), cy - (ryf if math.cos(a) > 0 else ryb) * 0.9 * math.cos(a), z))
        inner.append(np.array(ring))
    V, F = M.loft(inner, cap0=False, cap1=False, closed=False)
    add(M.Part(V, F, "BH_Shadow", name="hood_lining").flip(), weights=HOOD_W)


# ---------------------------------------------------------------- shoulder mantle
def mantle_w():
    def wfn(V):
        out = []
        for v in V:
            s = float(smoothstep(0.14, 0.30, abs(v[0])))
            side = "L" if v[0] > 0 else "R"
            d = {"chest": 1 - 0.55 * s}
            if s > 1e-4:
                d["shoulder." + side] = 0.33 * s
                d["upper_arm." + side] = 0.22 * s
            out.append(d)
        return out
    return wfn


def mantle(body):
    nu, nv = 40, 6
    gap = math.radians(14)
    rings = []
    for j in range(nv):
        v = j / (nv - 1)
        ring = []
        for i in range(nu):
            th = gap + (2 * math.pi - 2 * gap) * i / (nu - 1)
            st, ct = math.sin(th), math.cos(th)
            rx = 0.105 + 0.225 * v
            ry = (0.088 + 0.108 * v) if ct > 0 else (0.09 + 0.115 * v)
            drop = 0.13 + 0.12 * ct * ct
            z = 1.575 - drop * v ** 2 - 0.022 * (1 - math.cos(9 * th)) * 0.5 * v ** 4
            ring.append((rx * st, 0.012 - ry * ct, z))
        rings.append(np.array(ring))
    rings = rings[::-1]
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    body.add(M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="mantle"), 0.009, offset=1.0, bevel_w=0.0),
             weights=mantle_w())
    hem = rings[0] + np.array([0, 0, 0.004])
    V, F = M.tube(hem, [(0.007, 0.007)] * len(hem), n=6, up=(0, 0, 1))
    body.add(M.Part(V, F, "BH_Gold", name="mantle_trim"), weights=mantle_w())
    # clasp at the throat: two gold discs and a chain
    for sx in (1, -1):
        c = np.array([sx * 0.045, -0.105, 1.505])
        V, F = M.lathe([(0, -0.005), (0.018, -0.004), (0.02, 0.003), (0, 0.006)], 10)
        body.add(M.Part(V, F, "BH_Gold").rot(Rx(90)).move(c), "chest")
    V, F = M.tube([(-0.045, -0.112, 1.505), (0, -0.118, 1.49), (0.045, -0.112, 1.505)], [(0.003, 0.003)] * 3, n=5,
                  up=(0, -1, 0))
    body.add(M.Part(V, F, "BH_Gold", name="chain"), "chest")


# ---------------------------------------------------------------- belt with tomes and vials
def belt(body):
    from char_knight import thick_band
    V, F = thick_band(TORSO, 1.03, 1.075, COAT_G + 0.016, COAT_G - 0.002, n=28)
    body.add(M.bevel(M.Part(V, F, "BH_Leather", name="belt"), 0.003, 1), "hips")
    by = front_y(TORSO, 0, 1.052) - COAT_G - 0.02
    V, F = M.lathe([(0, -0.006), (0.03, -0.006), (0.034, 0.0), (0.03, 0.006), (0, 0.007)], 12)
    body.add(M.bevel(M.Part(V, F, "BH_Gold", name="buckle").rot(Rx(90)).scale((1, 1, 0.85)).move((0, by, 1.052)),
                     0.002, 1), "hips")
    body.add(crystal((0, by - 0.007, 1.052), 0.03, 0.01, tilt=(90, 0, 0)), "hips")

    def on_belt(frac, dz=0.0, out=0.0):
        p = ring_frac(TORSO, 1.05, COAT_G + 0.03 + out, [frac])[0]
        a = 2 * math.pi * frac - math.pi / 2
        return p + np.array([0, 0, dz]), math.degrees(a) + 90
    # tomes on the right hip (two books of different size hanging from a strap)
    for frac, (w, d, h), dz in ((0.77, (0.1, 0.04, 0.13), -0.075), (0.69, (0.085, 0.034, 0.11), -0.07)):
        p, ang = on_belt(frac, dz, 0.01)
        V, F = M.box(w, d, h)
        cover = M.bevel(M.Part(V, F, "BH_Leather", name="tome"), 0.006, 2)
        V, F = M.box(w * 0.9, d * 1.08, h * 0.92, center=(0.006, 0, 0))
        pages = M.Part(V, F, "BH_Bone", name="pages")
        V, F = M.box(w * 0.5, d * 1.16, 0.012, center=(0, 0, 0.0))
        band = M.Part(V, F, "BH_Gold", name="clasp")
        V, F = M.box(0.012, d * 1.2, h * 0.3, center=(-w * 0.5, 0, 0))
        rune = M.Part(V, F, "BH_Aether", name="tome_rune")
        for prt in (cover, pages, band, rune):
            prt.rot(Rz(ang)).move(p)
            body.add(prt, "hips")
    # vials on the left front
    for i, frac in enumerate((0.12, 0.155, 0.19)):
        p, ang = on_belt(frac, -0.035, -0.012)
        V, F = M.lathe([(0, -0.045), (0.013, -0.043), (0.015, -0.02), (0.013, 0.01), (0.006, 0.02), (0.006, 0.03),
                        (0, 0.03)], 8)
        vial = M.Part(V, F, "BH_Aether", name="vial").move(p)
        body.add(vial, "hips")
        V, F = M.lathe([(0, 0.022), (0.009, 0.022), (0.009, 0.038), (0, 0.04)], 8)
        body.add(M.Part(V, F, "BH_Gold", name="cork").move(p), "hips")
    # vial holder strap
    pts = [on_belt(f, -0.03, 0.0)[0] for f in np.linspace(0.1, 0.21, 6)]
    V, F = M.tube(pts, [(0.004, 0.012)] * len(pts), n=6, up=(0, 0, 1), p=3.0)
    body.add(M.Part(V, F, "BH_Leather", name="vial_strap"), "hips")
    # pouch at the back
    p, ang = on_belt(0.45, -0.04, 0.0)
    V, F = M.box(0.09, 0.045, 0.08)
    body.add(M.bevel(M.Part(V, F, "BH_Leather", name="pouch"), 0.01, 2).rot(Rz(ang)).move(p), "hips")


# ---------------------------------------------------------------- floating crystals
def crystals(body):
    for bone, c, L, r in (("crystal.L", CRYSTAL_L, 0.17, 0.036), ("crystal.R", CRYSTAL_R, 0.12, 0.027)):
        body.add(crystal(c, L, r, tilt=(12, -10, 20)), bone)
        # two small satellite shards
        for k, (dx, dz, s) in enumerate(((0.05, -0.07, 0.35), (-0.045, 0.06, 0.28))):
            body.add(crystal(np.array(c) + (dx, 0.01, dz), L * s, r * s * 1.2, tilt=(0, 30 * k - 15, 40)), bone)


def secondary(anim, frames):
    """Floating crystal bob/drift (seamless for loops: integer cycles per clip) plus lag behind chest turns."""
    n = len(frames)
    Lf = max(anim.length, 1)
    cyc = max(1, int(round(Lf / 45.0)))
    out = []
    for f in range(n):
        t = f / Lf
        ph = 2 * math.pi * cyc * t
        d = {}
        for bone, p0 in (("crystal.L", 0.0), ("crystal.R", 1.9)):
            yaw = 5.0 * math.sin(ph + p0)
            pitch = 3.5 * math.sin(2 * ph + p0 + 0.7)
            d[bone] = Rz(yaw) @ Rx(pitch)
        out.append(d)
    return out
