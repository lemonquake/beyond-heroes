"""bh-023: the hero's beards.  Each function takes (head, rng) and returns a hero_hair_kit.HairMesh.

The face is addressed by columns: `phi` is the angle round the vertical axis through (0, AXIS_Y) (0 = the chin's
centre, +-70 = just in front of the ears) and z the height.  A beard is a smooth shell over the columns from the upper
limit of beard growth (hero_skin.beard_top, the lips left open, a sideburn rising in front of the ear) down to the jaw
line and hanging below it, shingled with chunky locks; moustaches are locks laid along the upper lip.
"""
import math

import numpy as np

from hero_hair_kit import (AXIS_Y, DOWN, HairMesh, arc_t, beard_top, grid, lock, perp, pw, spline, sstep, tangents,
                           unit)
from hero_hair_styles import _braid, hang_strand

JAW_PHI = np.array([0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0])
JAW_Z = np.array([1.578, 1.578, 1.582, 1.589, 1.598, 1.608, 1.618])
LIP_Z, LIP_HW, LIP_HH = 1.6155, 0.036, 0.0150       # the mouth that every beard leaves open
BURN_Z = 1.697                                      # where a sideburn meets the hair in front of the ear


def jaw_z(phi):
    return float(np.interp(abs(phi), JAW_PHI, JAW_Z))


def radial(phi):
    return np.array([math.sin(math.radians(phi)), -math.cos(math.radians(phi)), 0.0])


def top_z(head, phi, lips=True, burn=True):
    """The height at which the beard begins on the column phi."""
    rise = float(sstep(57, 69, abs(phi))) if burn else 0.0
    for z in np.arange(1.700, 1.560, -0.001):
        p, _ = head.face(phi, z)
        if p is None:
            continue
        bt = beard_top(abs(p[0]))
        if z > bt + (BURN_Z - bt) * rise:
            continue
        if lips and (p[0] / LIP_HW) ** 2 + ((z - LIP_Z) / LIP_HH) ** 2 < 1.0:
            continue
        if lips and abs(p[0]) < LIP_HW and z > LIP_Z:
            continue                                     # the strip above the lip belongs to the moustache
        return float(z)
    return 1.56


def skin(head, phi, z, lift=0.0):
    p, n = head.face(phi, z)
    if p is None:
        p, n = np.array([0.0, AXIS_Y, z]) + radial(phi) * 0.06, radial(phi)
    return p + n * lift, n


def gvec(grow, phi, amount, flare=0.0):
    """The growth displacement on the column phi: (x towards that side, y, z) * amount, plus a flare outwards."""
    return np.array([grow[0] * (1 if phi >= 0 else -1), grow[1], grow[2]]) * amount + radial(phi) * flare * amount


def shell(m, head, rng, phis, hang, thick, close=(True, True), G=(0.62, 0.05), grow=(0.0, -0.10, -1.0),
          grow_len=0.06, flare=0.0, n_face=4, sway=0.7, lips=True, burn=True, top=None):
    """The fitted body of a beard over the columns `phis`.

    hang(phi)   how far it hangs below the jaw line;  thick(phi) its thickness at the jaw
    close       (first, last): tuck that side edge into the skin
    grow        the direction the hanging rim travels with `length` (x is mirrored for phi < 0), grow_len how far
    top(phi)    overrides the height at which the column starts
    """
    phis = list(phis)
    cols = [(p, 1.0) for p in phis]
    if close[0]:
        cols.insert(0, (phis[0] - 2.5 * (1 if phis[1] > phis[0] else -1), 0.0))
    if close[1]:
        cols.append((phis[-1] + 2.5 * (1 if phis[-1] > phis[-2] else -1), 0.0))
    U, Kr = len(cols), n_face + 3
    V, Nr, D = np.zeros((U, Kr, 3)), np.zeros((U, Kr, 3)), np.zeros((U, Kr, 3))
    R, Gg = np.zeros((U, Kr)), np.zeros((U, Kr))
    prof = np.interp(np.linspace(0, 1, n_face), [0, 0.3, 0.65, 1.0], [0.03, 0.55, 0.92, 1.0])
    for u, (phi, k) in enumerate(cols):
        zj = jaw_z(phi) + 0.002
        z0 = max(top_z(head, phi, lips, burn) if top is None else top(phi), zj + 0.004)
        th = thick(phi) * k
        L = hang(phi)
        out = radial(phi)
        for r, z in enumerate(np.linspace(z0, zj, n_face)):
            V[u, r], Nr[u, r] = skin(head, phi, z, th * prof[r] + (0.0006 if r == 0 else 0.0))
        pj, nj = V[u, n_face - 1], Nr[u, n_face - 1]
        g = gvec(grow, phi, grow_len, flare)
        V[u, n_face] = pj + DOWN * 0.50 * L + out * (0.003 + flare * 0.25 * L)       # the belly
        V[u, n_face + 1] = pj + DOWN * L - out * (0.45 * th) + out * flare * 0.4 * L  # the lowest edge
        under = pj + DOWN * 0.40 * L - nj * (th + 0.004) - out * 0.018
        V[u, n_face + 2] = head.push(under[None], 0.0015)[0]
        Nr[u, n_face:] = [unit(out + DOWN * 0.3), unit(out * 0.4 + DOWN), -out]
        f = min(L / 0.008, 1.0)
        D[u, n_face - 1] = g * 0.10 * f
        D[u, n_face], D[u, n_face + 1], D[u, n_face + 2] = g * 0.65 * f, g * f, g * 0.80 * f
        R[u, n_face - 1:] = np.array([0.1, 0.5, 1.0, 0.5]) * sway * f
        Gg[u] = np.clip(G[0] + G[1] * rng.uniform(-1, 1), 0.35, 1.0)
    Gg[:, -1] = 0.45
    grid(m, V, Nr, R=R, G=Gg, D=D)


def tufts(m, head, rng, spec, thick, w=0.0135, h=0.0085, grow=(0.0, -0.10, -1.0), grow_len=0.06, flare=0.0,
          inward=0.25, k=4, sect="tri"):
    """Chunky locks laid on the shell.  spec: (phi, z_root, z_tip, lift scale) each; a tip below the jaw line hangs
    free.  The locks lean towards the chin (`inward`) the way a beard grows."""
    for phi, zr, zt, ls in spec:
        phi = phi + rng.uniform(-1.5, 1.5)
        zj = jaw_z(phi) + 0.002
        th = thick(phi)
        out = radial(phi)
        pts = []
        zs = np.linspace(zr, max(zt, zj), 3)
        span = max(zr - zj, 1e-4)
        for z in zs:
            a = np.clip((zr - z) / span, 0, 1)               # 0 at the root .. 1 at the jaw
            ph = phi * (1 - inward * 0.25 * a)
            p, n = skin(head, ph, z, (0.35 + 0.65 * a) * th * ls + 0.001)
            pts.append(p)
        if zt < zj:                                          # the free end below the jaw
            L = zj - zt
            pj = pts[-1]
            inw = np.array([-math.copysign(1.0, phi) if abs(phi) > 3 else 0.0, 0.0, 0.0]) * inward
            pts.append(pj + DOWN * 0.55 * L + out * (0.003 + flare * 0.5 * L) + inw * 0.3 * L)
            pts.append(pj + DOWN * L + out * (flare * L - 0.002) + inw * L
                       + np.array([rng.uniform(-0.003, 0.003), 0, 0]))
        P = spline(pts, k)
        N = perp(tangents(P), out)
        free = float(np.clip((zj - zt) / 0.02, 0, 1))
        g = gvec(grow, phi, grow_len * (0.25 + 0.75 * free), flare)
        ww = w * rng.uniform(0.85, 1.15)
        lock(m, P, N, [ww * 0.72, ww, ww * 0.78, 0.0], [h * 0.55, h, h * 0.8, 0.0], sect=sect,
             sway=(0.4, 0.2 + 0.7 * free), G=rng.uniform(0.74, 1.0), grow=(g, 0.35), gw=0.08)


def lip_strand(head, pts, k):
    """pts: (x, z, lift) along the face seen from the front -> (P, N) strand on the skin."""
    xs = spline(np.array([(x, 0.0, z) for x, z, _l in pts]), 28)
    ts0 = arc_t(np.array([(x, 0.0, z) for x, z, _l in pts]))
    lf = np.interp(arc_t(xs), ts0, [l for _x, _z, l in pts])
    P, N = [], []
    for (x, _y, z), l in zip(xs, lf):
        p, n = head.front(x, z)
        P.append(p + n * l)
        N.append(n)
    P, N = np.array(P), np.array(N)
    t = arc_t(P)
    ts = np.linspace(0, 1, k)
    Pk = np.stack([np.interp(ts, t, P[:, i]) for i in range(3)], 1)
    Nk = unit(np.stack([np.interp(ts, t, N[:, i]) for i in range(3)], 1))
    Nk[1:-1] = unit(Nk[1:-1] + 0.5 * (Nk[:-2] + Nk[2:]))
    return Pk, Nk


def lobes(m, head, rng, pts, w, h, k=6, grow=(1.0, -0.2, -0.3), grow_len=0.03, t0=0.25, sway=(0.55, 0.6), gw=0.15,
          G=(0.80, 0.98), sect="fat"):
    """The two halves of a moustache along the (x, z, lift) points of the hero's left half."""
    for s in (1, -1):
        P, N = lip_strand(head, [(x * s, z, l) for x, z, l in pts], k)
        g = np.array([grow[0] * s, grow[1], grow[2]]) * grow_len
        lock(m, P, perp(tangents(P), N), w, h, sect=sect, root="cap", sway=sway, G=rng.uniform(*G), grow=(g, t0),
             gw=gw)


# ---- the beards ------------------------------------------------------------------------------------------------------

# a moustache fills the strip between the nose (z 1.638) and the upper lip (1.626) and thickens past the corners
M_PTS = [(-0.005, 1.6322, 0.0015), (0.009, 1.6318, 0.002), (0.021, 1.6290, 0.002), (0.0315, 1.6232, 0.0022),
         (0.0405, 1.6150, 0.0025), (0.0470, 1.6050, 0.003)]
M_W = [0.0056, 0.0062, 0.0070, 0.0078, 0.0066, 0.0]
M_H = [0.0080, 0.0100, 0.0098, 0.0088, 0.0064, 0.002]


def moustache(head, rng):
    """A full moustache over the upper lip, drooping a little past the corners of the mouth."""
    m = HairMesh()
    lobes(m, head, rng, M_PTS, M_W, M_H, k=7, grow=(1.0, -0.25, -0.55), grow_len=0.030, gw=0.2)
    # a second, shorter layer on top gives it body
    top = [(-0.003, 1.6338, 0.0050), (0.010, 1.6330, 0.0060), (0.022, 1.6300, 0.0055), (0.0315, 1.6250, 0.0040)]
    lobes(m, head, rng, top, [0.0040, 0.0046, 0.0040, 0.0], [0.0050, 0.0058, 0.0046, 0.001], k=5,
          grow=(1.0, -0.25, -0.45), grow_len=0.020, t0=0.2, G=(0.62, 0.74), gw=0.2)
    return m


def handlebar(head, rng):
    """A long moustache waxed out sideways past the cheeks, the ends curled up."""
    m = HairMesh()
    face = [(-0.005, 1.6322, 0.0015), (0.009, 1.6318, 0.002), (0.022, 1.6290, 0.0025), (0.033, 1.6245, 0.004),
            (0.041, 1.6205, 0.006)]
    curl = [(0.011, 0.002, -0.0025), (0.021, 0.008, 0.0005), (0.0275, 0.014, 0.0085), (0.0265, 0.018, 0.0185),
            (0.0195, 0.020, 0.0235)]                       # offsets from the end of the part on the face
    w = [0.0056, 0.0062, 0.0064, 0.0058, 0.0052, 0.0046, 0.0040, 0.0034, 0.0026, 0.0]
    h = [0.0075, 0.0092, 0.0086, 0.0070, 0.0058, 0.0048, 0.0040, 0.0034, 0.0026]
    for s in (1, -1):
        Pf, _ = lip_strand(head, [(x * s, z, l) for x, z, l in face], 6)
        ctrl = np.vstack([Pf, Pf[-1] + np.array(curl) * np.array([s, 1.0, 1.0])])
        P = spline(ctrl, 12)
        N = perp(tangents(P), np.array([0.30 * s, -1.0, 0.0]))
        g = np.array([1.0 * s, 0.08, 0.20]) * 0.035
        lock(m, P, N, w, h, sect="fat", root="cap", sway=(0.45, 0.7), G=rng.uniform(0.80, 0.98), grow=(g, 0.32),
             gw=0.30)
    return m


def goatee(head, rng):
    """A pointed chin beard joined to a moustache round the mouth."""
    m = HairMesh()
    hang = lambda p: 0.006 + 0.036 * max(0.0, 1 - abs(p) / 23.0) ** 0.9         # noqa: E731
    thick = lambda p: 0.0095                                                    # noqa: E731
    gr = (0.0, -0.12, -1.0)
    shell(m, head, rng, [-20, -13, -6.5, 0, 6.5, 13, 20], hang, thick, grow=gr, grow_len=0.07, burn=False)
    zc = jaw_z(0)
    tufts(m, head, rng, [(-13, 1.597, zc - 0.030, 1.0), (13, 1.597, zc - 0.030, 1.0), (-6, 1.598, zc - 0.040, 1.1),
                         (6, 1.598, zc - 0.040, 1.1), (0, 1.599, zc - 0.052, 1.25)], thick, w=0.0115, grow=gr,
          grow_len=0.075, inward=0.5)
    pts = M_PTS[:4] + [(0.0385, 1.6160, 0.0022), (0.0400, 1.6060, 0.0030), (0.0375, 1.5965, 0.0050)]
    lobes(m, head, rng, pts, [0.0054, 0.0060, 0.0062, 0.0060, 0.0054, 0.0050, 0.0], [0.0070, 0.0085, 0.0080, 0.0070,
          0.0062, 0.0058], k=8, grow=(0.3, -0.15, -1.0), grow_len=0.02, t0=0.5, gw=0.1)
    return m


FULL_PHI = [-70, -66, -59, -50, -40, -31, -24, -18, -9, 0, 9, 18, 24, 31, 40, 50, 59, 66, 70]


def _full_hang(chin, side=0.008):
    return lambda p: side + chin * math.cos(math.radians(min(abs(p) * 1.25, 90))) ** 1.5


def _full_tufts(m, head, rng, thick, hang, grow, grow_len, extra=0.010):
    spec = []
    for phi in (-62, -46, -30, 30, 46, 62):                 # the cheeks
        spec.append((phi, jaw_z(phi) + 0.030, jaw_z(phi) - 0.4 * hang(phi), 1.0))
    for phi in (-66, -54, -38, -22, -8, 8, 22, 38, 54, 66):  # the jaw and chin
        spec.append((phi, jaw_z(phi) + 0.012, jaw_z(phi) - hang(phi) - extra * rng.uniform(0.3, 1.0), 1.12))
    tufts(m, head, rng, spec, thick, grow=grow, grow_len=grow_len)


def full(head, rng):
    """A full beard from the sideburns round the jaw and chin, with a moustache."""
    m = HairMesh()
    hang = _full_hang(0.038)
    thick = lambda p: 0.0115 - 0.005 * sstep(45, 70, abs(p))                               # noqa: E731
    shell(m, head, rng, FULL_PHI, hang, thick, grow_len=0.07)
    _full_tufts(m, head, rng, thick, hang, (0.0, -0.10, -1.0), 0.075)
    lobes(m, head, rng, M_PTS, M_W, M_H, k=6, grow=(0.6, -0.2, -0.8), grow_len=0.02)
    return m


def long_(head, rng):
    """A wizard's beard: full on the jaw, falling in long locks to a point on the chest."""
    m = HairMesh()
    hang = _full_hang(0.060, 0.010)
    thick = lambda p: 0.0115 - 0.005 * sstep(45, 70, abs(p))                               # noqa: E731
    g = np.array([0.0, -0.05, -1.0])
    shell(m, head, rng, FULL_PHI, hang, thick, grow=tuple(g), grow_len=0.10)
    tufts(m, head, rng, [(p, jaw_z(p) + 0.030, jaw_z(p) - 0.4 * hang(p), 1.0) for p in (-62, -46, -30, 30, 46, 62)],
          thick, grow=tuple(g), grow_len=0.06)
    tipz = 1.315
    for phi in (0, -15, 15, -31, 31, -48, 48):
        zj = jaw_z(phi)
        p0, _ = skin(head, phi, zj + 0.016, 0.006)
        p1, _ = skin(head, phi, zj + 0.003, 0.0125)
        x = p1[0]
        a = abs(phi) / 48.0
        zt = tipz + 0.085 * a + rng.uniform(-0.012, 0.012) + (0.0 if phi == 0 else 0.018)
        zm = zj - 0.050
        wob = rng.uniform(-0.006, 0.006)
        ctrl = [p0, p1, (x * 0.88, p1[1] - 0.006 - 0.010 * (1 - a), zm),
                (x * 0.66 + wob, -0.150 - 0.006 * (1 - a), zm - 0.42 * (zm - zt)),
                (x * 0.34 - wob, -0.158, zt + 0.040), (x * 0.18, -0.158, zt)]
        P, N = hang_strand(head, ctrl, 8, 0.011)
        N = perp(tangents(P), unit(N + np.array([0.0, -1.5, 0.0])))
        w0 = 0.023 if phi == 0 else 0.0185
        t = arc_t(P)
        lock(m, P, N, w0 * pw([0.55, 0.95, 1.0, 0.95, 0.8, 0.55, 0.28, 0.0], t),
             pw([0.007, 0.012, 0.014, 0.013, 0.011, 0.008, 0.004, 0.0], t) * (1.2 if phi == 0 else 1.0),
             sect="diamond", sway=(0.22, 1.0), G=rng.uniform(0.70, 1.0), grow=(g * 0.26, 0.25))
    lobes(m, head, rng, M_PTS[:5] + [(0.0450, 1.6060, 0.0035), (0.0475, 1.5920, 0.006)],
          M_W[:4] + [0.0056, 0.0046, 0.0], M_H[:4] + [0.0062, 0.0048], k=8, grow=(0.25, -0.1, -1.0), grow_len=0.05,
          t0=0.45)
    return m


def chops(head, rng):
    """Mutton chops: side whiskers from the ears flaring out along the jaw, the chin and lip shaved."""
    m = HairMesh()
    gr = (0.50, -0.10, -0.80)
    hang = lambda p: 0.009 + 0.014 * sstep(72, 36, abs(p))                                  # noqa: E731
    thick = lambda p: 0.0105 + 0.0055 * sstep(70, 40, abs(p))                               # noqa: E731
    for s in (1, -1):
        shell(m, head, rng, [s * p for p in (27, 33, 41, 50, 59, 66, 70)], hang, thick, grow=gr, grow_len=0.055,
              flare=0.45)
        spec = [(s * 64, 1.650, jaw_z(64) - 0.004, 1.0), (s * 55, 1.634, jaw_z(55) - 0.012, 1.05),
                (s * 44, 1.622, jaw_z(44) - 0.020, 1.1), (s * 34, 1.614, jaw_z(34) - 0.022, 1.1),
                (s * 60, jaw_z(60) + 0.010, jaw_z(60) - 0.022, 1.2), (s * 48, jaw_z(48) + 0.008, jaw_z(48) - 0.030, 1.2)]
        tufts(m, head, rng, spec, thick, w=0.0140, h=0.0095, grow=gr, grow_len=0.06, flare=0.45, inward=-0.2)
    return m


def braided(head, rng):
    """A thick forked beard: full on the jaw, the chin plaited into two bound braids."""
    m = HairMesh()
    hang = _full_hang(0.022)
    thick = lambda p: 0.0125 - 0.0055 * sstep(45, 70, abs(p))                              # noqa: E731
    shell(m, head, rng, [-70, -64, -54, -42, -30, -20, -10, 0, 10, 20, 30, 42, 54, 64, 70], hang, thick,
          grow_len=0.035)
    tufts(m, head, rng, [(p, jaw_z(p) + 0.028, jaw_z(p) - 0.6 * hang(p), 1.0) for p in (-58, -36, 36, 58)]
          + [(p, jaw_z(p) + 0.012, jaw_z(p) - hang(p) - 0.006, 1.1) for p in (-64, -46, 0, 46, 64)],
          thick, grow_len=0.04, w=0.0150)
    for s in (1, -1):
        p0, _ = skin(head, s * 15, jaw_z(15) + 0.006, 0.004)
        ctrl = [p0, (s * 0.031, -0.148, 1.556), (s * 0.040, -0.156, 1.512), (s * 0.048, -0.158, 1.462),
                (s * 0.052, -0.158, 1.418)]
        _braid(m, head, rng, ctrl, 0.0185, 6, np.array([s * 0.04, -0.04, -1.0]) * 0.22, 0.12, tuft=0.042,
               margin=0.013)
    lobes(m, head, rng, M_PTS, M_W, M_H, k=5, grow=(0.6, -0.2, -0.8), grow_len=0.02)
    return m
