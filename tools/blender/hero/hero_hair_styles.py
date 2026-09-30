"""bh-023: the hero's hair styles.  Each function takes (head, rng) and returns a hero_hair_kit.HairMesh.

A style is a scalp shell (`cap`) that guarantees the skin never shows, with sculpted locks on top: strands are laid on
the fitted skull (`skull_strand`), or hang in model space and are pushed clear of the body (`hang_strand`), and swept
into locks.  The `length` displacement is set per lock: roots stay, tips travel along the growth direction, so the key
extrapolates in a straight line when the game drives it past 1.
"""
import math

import numpy as np

from hero_hair_kit import (C, DOWN, UP, HairMesh, arc_t, az_pol, blob, cap, dirv, grid, lock, perp, pw, slerp,
                           spline, sstep, tangents, unit)

BACK = np.array([0.0, 1.0, 0.0])


# ---- strands ---------------------------------------------------------------------------------------------------------

def _resample2(P, N, k):
    t = arc_t(P)
    ts = np.linspace(0, 1, k)
    Pk = np.stack([np.interp(ts, t, P[:, i]) for i in range(3)], 1)
    Nk = unit(np.stack([np.interp(ts, t, N[:, i]) for i in range(3)], 1))
    return Pk, Nk


def skull_strand(head, ways, k, lift=0.006, dense=30):
    """A strand lying on the skull through the way directions (great-circle arcs); lift: constant or pw() knots.
    -> (P (k, 3), N (k, 3))"""
    ways = [unit(w) for w in ways]
    ang = np.array([math.acos(float(np.clip(a @ b, -1, 1))) for a, b in zip(ways[:-1], ways[1:])])
    cum = np.concatenate([[0.0], np.cumsum(ang)]) / max(ang.sum(), 1e-9)
    u = np.linspace(0, 1, dense)
    D = np.empty((dense, 3))
    for i, x in enumerate(u):
        s = min(int(np.searchsorted(cum, x, side="right")) - 1, len(ang) - 1)
        D[i] = slerp(ways[s], ways[s + 1], (x - cum[s]) / max(cum[s + 1] - cum[s], 1e-9))
    P, N = head.surf(D, pw(lift, u))
    return _resample2(P, N, k)


def hang_strand(head, ctrl, k, margin=0.006):
    """A strand through control points in model space, kept `margin` clear of the body; the up vectors point away
    from the body."""
    P = spline(ctrl, k)
    P = head.push(P, margin)
    P[1:-1] = 0.5 * P[1:-1] + 0.25 * (P[:-2] + P[2:])
    P = head.push(P, margin)
    N = head.away(P)
    N[1:-1] = unit(N[1:-1] + 0.5 * (N[:-2] + N[2:]))
    return P, perp(tangents(P), N)


def cap_ride(head, P, N, grow, rim=0.45):
    """The displacement of points riding on a cap() that thickens by `grow` (same rim taper as the cap)."""
    f = head.f_of(P)
    return N * (grow * (1.0 - (1.0 - rim) * sstep(0.62, 1.0, f)))[:, None]


def comb(m, strands, rng, loop=False, ov=1.6, wmin=0.005, wmax=0.032, taper=(1.0, 1.0, 0.92, 0.6), h=0.005,
         hprof=(0.3, 1.0, 1.0, 0.85, 0.45), sect="roof", sway=(0.6, 0.15), G=(0.6, 1.0), grow=None, tip="point",
         layer=0.0012, gw=0.0, ride=None):
    """Turn an ordered fan of strands (same ring count) into overlapping locks: each lock is as wide as the gap to
    its neighbours, so the fan covers what is under it.
    h      the ridge height (scalar or f(i)), shaped along the lock by hprof
    grow   None, a lock() grow tuple, or f(i, P, N) -> tuple;  ride: None or f(P, N) -> (k, 3)"""
    n = len(strands)
    for i, (P, N) in enumerate(strands):
        nb = []
        if loop or i > 0:
            nb.append(strands[(i - 1) % n][0])
        if loop or i < n - 1:
            nb.append(strands[(i + 1) % n][0])
        d = np.mean([np.linalg.norm(P - Q, axis=1) for Q in nb], 0)
        t = arc_t(P)
        w = np.clip(0.5 * ov * d, wmin, wmax) * pw(taper, t)
        hh = (h(i) if callable(h) else h) * pw(hprof, t)
        g = grow(i, P, N) if callable(grow) else grow
        sw = sway(i) if callable(sway) else sway
        lock(m, P + N * (layer if i % 2 else 0.0), N, w, hh, sect=sect, tip=tip, sway=sw,
             G=rng.uniform(*G), grow=g, gw=gw, ride=None if ride is None else ride(P, N))


def tip_dir(P, N, along=1.0, out=0.0, down=0.0, up=0.0):
    return unit(tangents(P)[-1] * along + N[-1] * out + DOWN * down + UP * up)


# ---- short styles ----------------------------------------------------------------------------------------------------

def _lat_strand(head, d0, f_end, k, lift, back=True):
    """A strand combed straight back (or forward) from the direction d0: it keeps d0's sideways component and turns
    about the left-right axis until it reaches the fraction f_end of the hairline on the far side."""
    rho = math.sqrt(max(1 - d0[0] ** 2, 1e-6))
    sgn = 1.0 if back else -1.0
    th = math.atan2(d0[2], -d0[1]) + sgn * np.radians(np.arange(0, 300, 1.0))
    dirs = np.stack([np.full(len(th), d0[0]), -rho * np.cos(th), rho * np.sin(th)], 1)
    az, pol = az_pol(dirs)
    f = pol / head.hl(az)
    past = np.nonzero((np.arange(len(th)) > 25) & (f >= f_end) & ((dirs[:, 1] > 0) == back))[0]
    dirs = dirs[:(past[0] if len(past) else len(th) - 1) + 1]
    P, N = head.surf(dirs, pw(lift, np.linspace(0, 1, len(dirs))))
    return _resample2(P, N, k)


def crop(head, rng):
    """A short neat cut: close on the sides and back, the top a little longer and brushed forward to a lifted
    fringe.  With `length` it grows out into a shaggy mop."""
    m = HairMesh()
    g = 0.009
    cap(m, head, thick=lambda a, f: 0.0075 - 0.0025 * sstep(0.40, 0.85, f), n_az=24, G=0.62, g_jit=0.05, grow=g,
        ridge=0.06, rng=rng, rim=0.25)
    ride = lambda P, N: cap_ride(head, P, N, g, 0.25)                                       # noqa: E731
    # the top, combed forward from the crown
    n = 11
    S = []
    for i in range(n):
        dx = -0.66 + 1.32 * i / (n - 1) + rng.uniform(-0.02, 0.02)
        pol0, rho = math.radians(34 + 10 * abs(dx)), math.sqrt(1 - dx * dx)
        d0 = np.array([dx, rho * math.sin(pol0), rho * math.cos(pol0)])       # behind the crown
        j = rng.uniform(-0.0012, 0.0012)
        S.append(_lat_strand(head, d0, 0.945 + rng.uniform(-0.05, 0.02), 7,
                             [0.0045, 0.0075 + j, 0.0085 + j, 0.0090 + j, 0.0105 + j, 0.0135 + 2 * j], back=False))
    hs = 0.0062 * rng.uniform(0.72, 1.12, n)
    comb(m, S, rng, ov=1.75, h=lambda i: hs[i], sect="tri", sway=(0.6, 0.12), ride=ride, G=(0.78, 1.0), wmax=0.022,
         layer=0.002,
         taper=(0.8, 1.0, 1.0, 0.95, 0.62),
         grow=lambda i, P, N: (tip_dir(P, N, 0.55, 0.9, up=0.35) * 0.034, 0.25))
    # the crown and the short sides: low locks that only show as texture until they grow out
    whorl = dirv(180, 30)
    tiers = [(9, 95, 265, None, 0.62, 6, [0.0050, 0.0072, 0.0070, 0.0050], 0.0050, (0.6, 0.8, 0.0, 0.030)),
             (19, 66, 294, 0.60, 1.0, 4, [0.0040, 0.0052, 0.0042, 0.0018], 0.0036, (0.8, 0.6, 0.0, 0.040))]
    for cnt, a0, a1, f0, f1, swirl, lift, h, gr in tiers:
        S = []
        for i in range(cnt):
            az = a0 + (i + 0.5 + rng.uniform(-0.12, 0.12)) * (a1 - a0) / cnt
            root = slerp(whorl, head.H(az, 0.5), 0.15) if f0 is None else head.H(az, f0)
            S.append(skull_strand(head, [root, head.H(az + swirl, f1 + rng.uniform(-0.02, 0.0))], 4, lift))
        comb(m, S, rng, ov=1.8, h=h, sect="tri", sway=(0.5, 0.10), ride=ride, G=(0.80, 0.98), wmax=0.026,
             grow=lambda i, P, N, gr=gr: (tip_dir(P, N, gr[0], gr[1], up=gr[2]) * gr[3], 0.0))
    return m


def sidepart(head, rng):
    """Parted on the hero's left and swept across the top to the right, with some height at the fringe."""
    m = HairMesh()
    g = 0.004
    cap(m, head, thick=0.0055, n_az=22, G=0.46, grow=g, rng=rng)
    ride = lambda P, N: cap_ride(head, P, N, g)                                             # noqa: E731
    p0, p1 = head.H(34, 0.985), head.H(152, 0.30)
    big, small = [], []
    n1, n2 = 13, 9
    for i in range(n1):
        u = i / (n1 - 1)
        az_t = -42 - 136 * u ** 0.85
        f_t = (0.99 if u < 0.2 else 1.03) + rng.uniform(-0.015, 0.015)
        vol = 1.0 - 0.55 * sstep(0.1, 0.7, u)
        lift = [0.0058, 0.007 + 0.011 * vol, 0.007 + 0.013 * vol, 0.006 + 0.008 * vol, 0.003 + 0.004 * vol]
        big.append(skull_strand(head, [slerp(p0, p1, u * 0.97), head.H(az_t, f_t)], 7, lift))
    for i in range(n2):
        u = i / (n2 - 1)
        f_t = 1.03 + rng.uniform(-0.015, 0.015)
        small.append(skull_strand(head, [slerp(p0, p1, u * 0.97), head.H(52 + 126 * u, f_t)], 5,
                                  [0.0058, 0.008, 0.007, 0.003]))

    def grow_big(i, P, N):
        if i / (n1 - 1) < 0.25:            # the fringe grows down beside the temple, never across the eyes
            return (unit(tip_dir(P, N, 0.55, 0.35, 0.75) + np.array([-0.35, 0.25, 0])) * 0.05, 0.4)
        return (tip_dir(P, N, 0.6, 0.35, 0.6) * 0.06, 0.45)
    comb(m, big, rng, ov=1.6, h=0.0065, sect="tri", sway=(0.55, 0.35), grow=grow_big, wmax=0.03, ride=ride)
    comb(m, small, rng, ov=1.6, h=0.006, sect="tri", sway=(0.55, 0.3), wmax=0.03, ride=ride,
         grow=lambda i, P, N: (tip_dir(P, N, 0.6, 0.35, 0.6) * 0.055, 0.35))
    return m


def slick(head, rng):
    """Combed straight back from the brow and the temples, flicking out at the nape."""
    m = HairMesh()
    cap(m, head, thick=0.005, n_az=22, G=0.50, rng=rng)
    azs = np.linspace(-100, 100, 801)
    Hd = head.H(azs, np.where(np.abs(azs) < 70, 0.985, 1.0))
    n = 13
    S = []
    for i in range(n):
        dx = (-0.95 + 1.90 * i / (n - 1)) + (rng.uniform(-0.045, 0.045) if 0 < i < n - 1 else 0.0)
        d0 = Hd[int(np.argmin(np.abs(Hd[:, 0] - dx)))]
        jit = rng.uniform(-0.001, 0.001)
        S.append(_lat_strand(head, d0, 1.05 + rng.uniform(-0.03, 0.03), 9,
                             [0.002, 0.010 + jit, 0.010 + jit, 0.008, 0.007, 0.007 + jit, 0.008, 0.010, 0.015]))
    hs = 0.0058 * rng.uniform(0.65, 1.15, n)
    comb(m, S, rng, ov=2.0, h=lambda i: hs[i], sect="tri", sway=(0.8, 0.5), wmax=0.030, layer=0.0015,
         taper=(0.85, 1.0, 1.0, 1.0, 0.85, 0.5), hprof=(0.15, 1.0, 1.0, 1.0, 0.9, 0.6), G=(0.74, 1.0),
         grow=lambda i, P, N: (unit(tip_dir(P, N, 0.7, 0.25, 0.8) + BACK * 0.2) * 0.10, 0.80))
    return m


def spiky(head, rng):
    """Short hair pulled up into stiff, broad spikes."""
    m = HairMesh()
    g = 0.004
    cap(m, head, thick=0.0095, n_az=24, G=0.48, grow=g, ridge=0.10, rng=rng, rim=0.35)
    rows = [(1, 0.0), (5, 0.26), (9, 0.50), (12, 0.72), (11, 0.92)]
    for ri, (cnt, f) in enumerate(rows):
        for i in range(cnt):
            az = -180 + (i + 0.5 * (ri % 2) + rng.uniform(-0.15, 0.15)) * 360.0 / cnt
            ff = max(f + rng.uniform(-0.04, 0.04), 0.0)
            root, N = head.on(az, ff, 0.003)
            out = np.array([N[0], N[1], 0.0])
            front = abs(az) < 62 and f > 0.5
            axis = unit(N + UP * (0.95 if front else 0.55 - 0.5 * max(f - 0.7, 0.0) / 0.2) + BACK * 0.22
                        + out * (0.0 if front else 0.15)
                        + rng.normal(0, 0.10, 3))
            if f > 0.9 and abs(az) < 66:
                continue                                  # no spikes down over the brow
            L = rng.uniform(0.060, 0.082) * (0.9 if f > 0.6 else 1.0) * (0.72 if f > 0.9 else 1.0)
            bend = unit(UP * 0.6 + BACK * 0.5 - axis * (axis @ (UP * 0.6 + BACK * 0.5)) + rng.normal(0, 0.15, 3))
            s = np.linspace(0, 1, 5)
            P = root + axis * (s * L)[:, None] + bend * ((s ** 2) * L * 0.22)[:, None]
            w0 = rng.uniform(0.021, 0.026)
            lock(m, P, perp(tangents(P), bend), [w0, w0 * 0.92, w0 * 0.62, w0 * 0.28, 0.0],
                 [w0 * 0.55, w0 * 0.52, w0 * 0.36, w0 * 0.17, 0.0], sect="blade", sway=(0.15, 0.55),
                 G=rng.uniform(0.62, 1.0), grow=(unit(axis + bend * 0.3) * 0.062, 0.0), gw=0.18)
    return m


def mohawk(head, rng):
    """A tall serrated crest from the brow over the crown to the nape; the sides are shaved."""
    m = HairMesh()
    ways = [head.H(0, 0.985), dirv(0, 0.0), head.H(180, 0.985)]
    n = 21
    Pc, Nc = skull_strand(head, ways, n, 0.0)
    Tc = tangents(Pc)
    X = np.array([1.0, 0.0, 0.0])
    u = np.linspace(0, 1, n)
    env = np.sin(np.pi * np.clip(u * 1.08, 0, 1)) ** 0.55          # tallest just behind the crown
    ends = np.clip(np.minimum(u, 1 - u) / 0.08, 0.15, 1.0)
    tooth = np.where(np.arange(n) % 2 == 1, 1.0, 0.66)
    Hh = (0.030 + 0.062 * env) * ends
    A = unit(Nc + Tc * 0.30 + UP * 0.10)
    rows = [(0.021, 0.0, 0.0), (0.0165, 0.34, 0.0), (0.0085, 0.72, 0.4), (0.0, 1.0, 1.0)]   # (half width, height, tooth)
    cols = []
    for sgn, order in ((-1, rows[:-1]), (0, rows[-1:]), (1, rows[-2::-1])):
        for hw, hf, tf in order:
            hh = Hh * hf * (1 + (tooth - 1) * tf)
            lean = Tc * (0.012 * tf * tooth)[:, None]
            wide = 1.0 + 0.28 * (tooth - 0.83) / 0.17 * (1.0 if 0 < hf < 1 else 0.0)
            P = (Pc + X * (sgn * hw * ends * wide)[:, None] + A * hh[:, None] + lean
                 - Nc * (0.002 if hf == 0 else 0.0))
            D = A * (0.19 * hf * (1 + (tooth - 1) * tf * 0.5) * ends)[:, None]
            R = np.full(n, 0.65 * hf)
            cols.append((P, D, R))
    V = np.stack([c[0] for c in cols], 1)                         # (n stations, 7 across, 3)
    D = np.stack([c[1] for c in cols], 1)
    R = np.stack([c[2] for c in cols], 1)
    Nref = np.zeros_like(V)
    Nref[:, :3] = -X
    Nref[:, 3] = A
    Nref[:, 4:] = X
    G = np.repeat(np.clip(0.78 + 0.18 * rng.uniform(-1, 1, (n + 1) // 2), 0.35, 1.0), 2)[:n]
    grid(m, V, Nref, R=R, G=np.repeat(G[:, None], V.shape[1], 1), D=D)
    return m


# ---- long styles -----------------------------------------------------------------------------------------------------

def long_(head, rng):
    """Straight hair parted in the middle, falling over the ears and past the shoulders down the back."""
    m = HairMesh()
    cap(m, head, thick=lambda a, f: 0.0035 + 0.003 * sstep(0.0, 0.5, f), n_az=18, fs=(0.2, 0.45, 0.72, 0.93), G=0.42,
        rng=rng)
    a0, b0 = head.H(0, 0.985), head.H(180, 0.34)
    n = 13
    for s in (1, -1):
        S = []
        for i in range(n):
            u = (i + 0.5) / n
            a = 64 + 116 * u ** 0.9                       # where this lock leaves the skull
            f_land = min(1.0, 94.0 / float(head.hl(a)))
            root = unit(slerp(a0, b0, u * 0.95) - np.array([s * 0.012, 0, 0]))
            Ps, _ = skull_strand(head, [root, head.H(s * a, 0.55 * f_land + 0.1), head.H(s * a, f_land)],
                                 5, [0.0062, 0.009, 0.010, 0.010, 0.010])
            land = Ps[-1]
            zt = 1.335 + rng.uniform(-0.035, 0.03)
            if a < 84:                                     # the front locks fall over the collarbones
                x = s * (0.088 + 0.014 * (a - 64) / 20)
                ctrl = [(x * 0.95, -0.070, 1.625), (x, -0.086, 1.535), (x * 1.03, -0.115, 1.455),
                        (x * 1.03, -0.142, 1.385), (x * 1.0, -0.146, zt + 0.02)]
            else:                                          # the rest hangs behind the shoulders
                v = (180 - a) / 96.0
                x = s * 0.158 * v ** 0.8
                y = 0.104 + 0.014 * (1 - v)
                ctrl = [(0.5 * (land[0] + x * 0.8), 0.5 * (land[1] + y * 0.8) + 0.004, 1.585),
                        (x * 0.97, y, 1.475), (x * 1.04, y + 0.014, 1.40), (x * 1.06, y + 0.018, zt)]
            S.append(hang_strand(head, np.vstack([Ps, np.array(ctrl)]), 10, 0.006))

        def grow(i, P, N):
            t = arc_t(P)
            return (DOWN * 0.32, float(np.interp(1.60, P[::-1, 2], t[::-1])))
        comb(m, S, rng, ov=1.6, h=0.010, hprof=(0.25, 0.9, 1.0, 1.0, 0.95, 0.6), sect="tri", wmin=0.012, wmax=0.024,
             taper=(0.8, 1.0, 1.0, 1.0, 0.9, 0.45), sway=(0.32, 1.0), grow=grow, G=(0.58, 1.0))
    # a plain curtain behind the locks, so the neck never shows between them
    azs = np.linspace(100, 260, 11)
    rows = [1.66, 1.585, 1.475, 1.39]
    V = np.zeros((len(azs), len(rows), 3))
    for j, a in enumerate(azs):
        v = abs(180 - a) / 96.0
        sx = 1.0 if a < 180 else -1.0
        x = sx * 0.150 * v ** 0.8
        top, _ = head.on(a if a <= 180 else a - 360, min(1.0, 96.0 / float(head.hl(a))), 0.006)
        y = 0.100 + 0.012 * (1 - v)
        V[j] = [top, (0.5 * (top[0] + x * 0.8), 0.5 * (top[1] + y * 0.8), rows[1]), (x * 0.97, y - 0.004, rows[2]),
                (x * 1.03, y + 0.008, rows[3])]
        V[j, 1:] = head.push(V[j, 1:], 0.004)
    D = np.zeros_like(V)
    D[:, 2] = DOWN * 0.10
    D[:, 3] = DOWN * 0.30
    R = np.tile(np.array([0.0, 0.3, 0.7, 1.0]), (len(azs), 1))
    grid(m, V, head.away(V.reshape(-1, 3)).reshape(V.shape), R=R, G=0.40, D=D)
    return m


def _hairline_starts(head, n, a0=-180.0, a1=180.0, phase=0.5):
    """n directions along the hairline between the azimuths a0..a1 (the front a touch inside it)."""
    az = a0 + (np.arange(n) + phase) * (a1 - a0) / n
    return [head.H(a, 0.992 if abs((a + 180) % 360 - 180) < 70 else 1.02) for a in az]


def _part_starts(head, s, n, f_nape=1.02):
    """n directions along the middle parting from the brow over the crown to the nape, a step to the side s."""
    out = []
    pf, pb = float(head.hl(0)) * 0.985, float(head.hl(180)) * f_nape
    for u in (np.arange(n) + 0.5) / n:
        ang = -pf + u * (pf + pb)                        # angle from the crown: negative = towards the brow
        d = dirv(0.0 if ang < 0 else 180.0, abs(ang))
        out.append(unit(d - np.array([s * 0.012, 0, 0])))      # a touch across, so the two sides overlap
    return out


def _gather(m, head, rng, starts, tie_dir, k=6, lift=(0.0015, 0.0060, 0.0072, 0.0080, 0.0090), loop=True, mid=None,
            h=0.0048, ov=1.7, wmax=0.036, roots=None):
    """Locks combed from the start directions to a tie point.  mid(d) -> an optional way direction; roots: the
    lift of each root (default lift[0]: on the skin at the hairline; a root on a parting must clear the shell)."""
    S = []
    for j, d in enumerate(starts):
        w = mid(d) if mid else None
        lf = list(lift)
        if roots is not None:
            lf[0] = roots[j]
            lf[1] = max(lf[1], roots[j] + 0.0008)
        S.append(skull_strand(head, [d] + ([w] if w is not None else []) + [tie_dir], k, lf))
    comb(m, S, rng, loop=loop, ov=ov, h=h, hprof=(0.12, 0.9, 1.0, 1.0, 0.9, 0.7), sect="roof", sway=(0.9, 0.05),
         taper=(1.0, 1.0, 0.95, 0.8, 0.6), G=(0.72, 1.0), wmin=0.004, wmax=wmax)


def _band(m, c, axis, r, length=0.012, G=0.40, D=None, R=0.0, gw=0.0):
    """A cord wound round a bunch of hair."""
    axis = unit(axis)
    P = np.asarray(c) + axis * np.array([-0.5, 0.0, 0.5])[:, None] * length
    ref = perp(np.tile(axis, (3, 1)), (0.3, 0.2, 0.9))
    rr = np.array([r * 0.9, r * 1.06, r * 0.9])
    lock(m, P, ref, rr, rr, sect="round8", tip="open", sway=(0.0, 0.0), G=G, gw=gw,
         D=None if D is None else np.broadcast_to(np.asarray(D, float), (3, 3)), R=np.full(3, R))


def _tail(m, head, rng, ctrl, r, n=4, k=8, spread=0.014, grow=None, sway=(0.12, 1.0), margin=None,
          taper=(0.62, 1.0, 1.12, 1.05, 0.85, 0.55, 0.0)):
    """A hanging tail of hair: a core lock and n - 1 thinner ones fanned round it with ragged ends."""
    ctrl = np.asarray(ctrl, float)
    T = tangents(ctrl)
    for j in range(n):
        if j == 0:
            c2, rr = ctrl.copy(), r
        else:
            a = 2 * math.pi * (j - 1) / (n - 1) + rng.uniform(-0.3, 0.3)
            e1 = perp(T, (1.0, 0.0, 0.0))
            e2 = np.cross(T, e1)
            off = e1 * math.cos(a) + e2 * math.sin(a)
            c2 = ctrl + off * (spread * np.linspace(0.25, 1.0, len(ctrl)) ** 1.0)[:, None] * rng.uniform(0.8, 1.2)
            c2[-1] = c2[-1] + (c2[-2] - c2[-1]) * rng.uniform(0.1, 0.55)
            rr = r * rng.uniform(0.62, 0.74)
        P, N = hang_strand(head, c2, k, (rr * 0.8 if margin is None else margin))
        w = rr * pw(taper, arc_t(P))
        lock(m, P, N, w, w * 0.9, sect="round6" if j == 0 else "round5", root="cap", sway=sway,
             G=rng.uniform(0.62, 1.0), grow=grow)


def ponytail(head, rng):
    """Hair drawn back to a cord at the back of the head, the tail hanging to the shoulder blades."""
    m = HairMesh()
    cap(m, head, thick=0.0045, n_az=20, G=0.45, rng=rng)
    tie_dir = dirv(180, 66)
    tie, tn = head.surf(tie_dir, 0.010)
    _gather(m, head, rng, _hairline_starts(head, 22), tie_dir,
            mid=lambda d: slerp(d, tie_dir, 0.5) + UP * (0.35 if d[1] < 0.2 else 0.0))
    axis = unit(tn + UP * 0.25)
    _band(m, tie + axis * 0.012, axis, 0.0195, 0.014)
    ctrl = [tie + axis * 0.004, tie + axis * 0.040, tie + axis * 0.066 + DOWN * 0.030,
            (0.0, 0.132, 1.62), (0.0, 0.130, 1.53), (0.0, 0.122, 1.44)]
    _tail(m, head, rng, ctrl, 0.0245, n=4, k=9, grow=(np.array([0.0, 0.03, -1.0]) * 0.28, 0.30), margin=0.016)
    return m


def topknot(head, rng):
    """Hair drawn up into a bound knot on the crown."""
    m = HairMesh()
    cap(m, head, thick=0.0045, n_az=20, G=0.45, rng=rng)
    tie_dir = dirv(180, 13)
    tie, tn = head.surf(tie_dir, 0.005)
    _gather(m, head, rng, _hairline_starts(head, 22), tie_dir, lift=(0.0015, 0.006, 0.0065, 0.007, 0.009))
    axis = unit(tn + BACK * 0.10)
    side = unit(np.cross(axis, (1.0, 0.0, 0.0)))
    sc = 0.55                                              # the knot swells about its foot with `length`

    def dsp(p):
        return (np.asarray(p, float) - tie) * sc
    P = tie + axis * np.array([-0.004, 0.006, 0.014])[:, None]
    rr = np.array([0.024, 0.019, 0.019])
    lock(m, P, perp(np.tile(axis, (3, 1)), side), rr, rr, sect="round8", tip="open", G=0.72, D=dsp(P), gw=sc,
         R=np.array([0.0, 0.05, 0.1]))
    _band(m, tie + axis * 0.011, axis, 0.0210, 0.009, D=dsp(tie + axis * 0.011), R=0.1, gw=sc)
    # the knot: a thick lock coiled one and a half times round the stem, over a core
    bc = tie + axis * 0.020
    e2 = unit(np.cross(axis, side))
    kc = 13
    uu = np.linspace(0, 1, kc)
    ang = 0.6 + uu * 1.6 * 2 * math.pi
    rc = 0.0245 - 0.0085 * uu
    Pk = bc + (side * np.cos(ang)[:, None] + e2 * np.sin(ang)[:, None]) * rc[:, None] + axis * (0.004 + 0.026 * uu)[:, None]
    rad = 0.0175 * pw([0.75, 1.0, 1.0, 1.0, 0.9, 0.6], uu)
    lock(m, Pk, unit(Pk - (bc + axis * 0.014)), rad, rad * 0.92, sect="round6", tip="cap", root="cap", G=0.92,
         D=dsp(Pk), gw=sc, R=np.full(kc, 0.3))
    blob(m, bc + axis * 0.016, 0.0230, axis, n=6, G=0.70, R=0.3, D=dsp(bc + axis * 0.016), squash=1.0,
         grow_r=0.0230 * sc, dome=False)
    bc = bc + axis * 0.026
    for j in range(3):                                   # the loose ends above the knot
        d = unit(axis * 0.75 - side * 0.65 + np.array([0.45 * (j - 1), 0, 0]))
        s = np.linspace(0, 1, 4)
        Pt = bc + d * (0.004 + s * 0.042)[:, None] + DOWN * (s ** 2 * 0.012)[:, None]
        lock(m, Pt, perp(tangents(Pt), axis), [0.010, 0.009, 0.005, 0.0], [0.006, 0.006, 0.004, 0.0], sect="diamond",
             sway=(0.0, 0.8, 0.3), G=rng.uniform(0.7, 1.0), D=dsp(Pt) + d * np.array([0.0, 0.01, 0.02, 0.035])[:, None],
             gw=sc)
    return m


def _braid(m, head, rng, ctrl, r, beads, grow, t0, tuft=0.05, margin=None):
    """A plait along the control points: a tube pinched between beads that lean left and right in turn, a cord at the
    end and a tuft below it."""
    k = 2 * beads + 1
    P, N = hang_strand(head, ctrl, k, (r + 0.002) if margin is None else margin)
    T = tangents(P)
    t = arc_t(P)
    S = unit(np.cross(T, N))
    lean = np.zeros(k)
    lean[1::2] = np.where(np.arange(beads) % 2 == 0, 1.0, -1.0)
    rad = r * np.where(np.arange(k) % 2 == 1, 1.0, 0.52) * np.interp(t, [0, 0.12, 1], [0.75, 1.0, 0.80])
    ramp = np.clip((t - t0) / (1 - t0), 0, 1)
    D = ramp[:, None] * np.asarray(grow)
    Pb = P + S * (lean * r * 0.30)[:, None]
    lock(m, Pb, N, rad, rad * 0.82, sect="round6", tip="open", root="cap", R=sstep(0.1, 1.0, t) * 0.9,
         G=rng.uniform(0.78, 0.95), D=D, roll=lean * 0.5)
    end, e_ax = P[-1], T[-1]
    _band(m, end, e_ax, r * 0.74, 0.012, D=np.asarray(grow), R=0.9, G=0.40)
    s = np.linspace(0, 1, 4)
    Pt = end + e_ax * (0.004 + s * tuft)[:, None]
    lock(m, Pt, np.tile(N[-1], (4, 1)), [r * 0.60, r * 0.98, r * 0.62, 0.0], [r * 0.60, r * 0.9, r * 0.55, 0.0],
         sect="round6", sway=(0.0, 1.0, 0.9), G=rng.uniform(0.8, 1.0), D=np.tile(np.asarray(grow), (4, 1)))


def braids(head, rng):
    """Parted in the middle and plaited into two braids that lie over the shoulders."""
    m = HairMesh()
    cap(m, head, thick=0.0045, n_az=16, fs=(0.3, 0.6, 0.88), G=0.50, rng=rng)
    for s in (1, -1):
        gd = dirv(s * 126, 119)
        gat, gn = head.surf(gd, 0.011)
        starts = _part_starts(head, s, 12) + _hairline_starts(head, 10, s * 174, s * 5)
        roots = [0.0060] * 12 + [0.0015] * 10

        def mid(d, gd=gd):
            w = float(sstep(0.35, -0.30, d[1]))           # hair from the front arcs up and back round the ear
            return slerp(d, gd, 0.5) + UP * 0.55 * w + BACK * 0.15 * w
        _gather(m, head, rng, starts, gd, k=5, mid=mid, lift=(0.0015, 0.0068, 0.0076, 0.0085, 0.0100), h=0.0055,
                roots=roots)
        x = s
        ctrl = [gat - gn * 0.006, (x * 0.082, 0.004, 1.596), (x * 0.092, -0.034, 1.548), (x * 0.098, -0.078, 1.510),
                (x * 0.100, -0.118, 1.462), (x * 0.098, -0.146, 1.395), (x * 0.096, -0.156, 1.315)]
        _braid(m, head, rng, ctrl, 0.0215, 10, np.array([0.0, -0.03, -1.0]) * 0.26, 0.55)
    return m


def pigtails(head, rng):
    """Parted in the middle and tied into two bunches high behind the ears."""
    m = HairMesh()
    cap(m, head, thick=0.0045, n_az=16, fs=(0.3, 0.6, 0.88), G=0.50, rng=rng)
    for s in (1, -1):
        tie_dir = dirv(s * 116, 64)
        tie, tn = head.surf(tie_dir, 0.009)
        starts = _part_starts(head, s, 13) + _hairline_starts(head, 11, s * 174, s * 5)
        _gather(m, head, rng, starts, tie_dir, k=5, lift=(0.0015, 0.0068, 0.0076, 0.0090), h=0.0055,
                roots=[0.0060] * 13 + [0.0015] * 11)
        axis = unit(tn + UP * 0.15 + BACK * 0.25)
        _band(m, tie + axis * 0.010, axis, 0.0185, 0.013)
        ctrl = [tie + axis * 0.002, tie + axis * 0.036, tie + axis * 0.062 + DOWN * 0.020,
                (s * 0.146, 0.060, 1.672), (s * 0.146, 0.080, 1.61), (s * 0.138, 0.090, 1.555)]
        _tail(m, head, rng, ctrl, 0.0235, n=4, k=8, spread=0.015,
              grow=(np.array([s * 0.02, 0.16, -1.0]) * 0.22, 0.30), margin=0.015)
    return m


# ---- big styles ------------------------------------------------------------------------------------------------------

def _low_edge(side, back, front=1.0):
    """f_edge(az) for shells that come down over the ears and the neck."""
    def fe(a):
        a = np.abs((np.asarray(a, float) + 180) % 360 - 180)
        return front + (side - front) * sstep(48, 92, a) + (back - side) * sstep(95, 165, a)
    return fe


def curly(head, rng):
    """A big round mass of curls."""
    m = HairMesh()
    fe = _low_edge(1.22, 1.06)
    th, g = 0.028, 0.046
    cap(m, head, thick=th, n_az=22, fs=(0.16, 0.36, 0.58, 0.80, 0.96), f_edge=fe, G=0.42, grow=g, rng=rng, rim=0.8)
    n = 70
    gold = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        zc = 1 - (i + 0.5) / n * 1.66                     # from the crown down to below the equator
        pol = math.degrees(math.acos(zc))
        az = math.degrees((gold * i) % (2 * math.pi)) - 180.0
        hl = float(head.hl(az)) * float(fe(az))
        if pol > hl - 3:
            continue
        r = rng.uniform(0.024, 0.036)
        edge = float(sstep(hl - 28, hl - 3, pol))         # curls at the rim sit lower so the mass is round
        c, N = head.surf(dirv(az, pol), th - 0.004 - 0.008 * edge + rng.uniform(-0.003, 0.005))
        axis = unit(N + rng.normal(0, 0.2, 3))
        blob(m, c, r, axis, n=6, G=rng.uniform(0.58, 1.0), R=0.45, D=N * g + unit(c - C) * 0.004,
             grow_r=r * 0.48, squash=0.85, dome=edge < 0.5)
    for i in range(12):                                   # and a row of them hiding the rim of the shell
        az = -180 + (i + 0.5) * 30.0
        r = rng.uniform(0.022, 0.028)
        c, N = head.on(az, float(fe(az)) * 0.975, th * 0.62)
        if c[2] < 1.742 and abs(az) < 50:
            c = c + UP * (1.742 - c[2])                   # never down over the brows
        blob(m, c, r, unit(N + DOWN * 0.5), n=6, G=rng.uniform(0.55, 0.9), R=0.45, D=N * g * 0.75 + DOWN * 0.004,
             grow_r=r * 0.48, squash=0.85, dome=False)
    return m


def _cut(m, head, rng, z_edge, th, down, n_az=30, n_lock=20, f_in=None, hem=0.0015, front_down=None):
    """A thick even cut of hair hanging to the height z_edge(az): a shell from the crown (or, with f_in, from the
    rim of a shaved crown) to a turned-under hem, shingled with broad locks.  down(|az|): how far the hem drops at
    length 1."""
    azs = np.linspace(-180, 180, n_az, endpoint=False)
    pols = np.arange(24.0, 156.0, 0.5)

    def f_edge(a):
        a = np.atleast_1d(np.asarray(a, float))
        out = np.zeros(len(a))
        for j, x in enumerate(a):
            P, _ = head.surf(dirv(np.full(len(pols), x), pols))
            out[j] = pols[np.argmax(P[:, 2] <= z_edge(x))] / float(head.hl(x))
        return out

    def place(a, u, k):
        """Points at the fraction u of the way down the column(s) a, at k times the thickness; -> P, N, D, R"""
        a = np.atleast_1d(np.asarray(a, float))
        fe = f_edge(a)
        fi = np.zeros(len(a)) if f_in is None else f_in(a)
        f = fi + (fe - fi) * u
        t = th(np.abs((a + 180) % 360 - 180))
        P, N = head.on(a, f, t * k)
        g = float(sstep(0.35, 1.0, u))
        out = unit(np.stack([N[:, 0], N[:, 1], np.zeros(len(a))], 1))
        dn = down(np.abs((a + 180) % 360 - 180))
        D = (DOWN * dn[:, None] + out * (0.25 * dn)[:, None]) * g + N * (0.004 * (1 - g) * (1.0 if k > 0.3 else 0.0))
        return P, N, D, np.full(len(a), 0.35 * g)
    if f_in is None:
        rows = [(0.0, 1.0), (0.14, 1.0), (0.32, 1.0), (0.56, 1.0), (0.78, 1.0), (0.93, 1.0), (1.0, 0.95), (1.0, 0.08)]
    else:
        rows = [(0.0, -0.1), (0.07, 0.6), (0.26, 1.0), (0.58, 1.08), (0.86, 1.04), (1.0, 0.92), (1.0, 0.08)]
    K = len(rows)
    V, Nr, D, R = (np.zeros((n_az, K, 3)), np.zeros((n_az, K, 3)), np.zeros((n_az, K, 3)), np.zeros((n_az, K)))
    for r, (u, k) in enumerate(rows):
        V[:, r], Nr[:, r], D[:, r], R[:, r] = place(azs, u, k)
    if f_in is None:
        V[:, 0] = V[:, 0].mean(0)
        D[:, 0] = D[:, 0].mean(0)
    G = np.repeat(np.clip(0.50 + 0.05 * rng.uniform(-1, 1, n_az), 0.35, 1.0)[:, None], K, 1)
    grid(m, V[:, :-1], Nr[:, :-1], closed_u=True, R=R[:, :-1], G=G[:, :-1], D=D[:, :-1])
    grid(m, V[:, -2:], Nr[:, -2:] * 0 + DOWN, closed_u=True, R=R[:, -2:], G=0.42, D=D[:, -2:])
    # the shingles
    us = np.array([0.0, 0.24, 0.50, 0.74, 0.93, 1.0]) if f_in is None else np.array([0.10, 0.34, 0.60, 0.84, 1.0])
    S, Ds = [], []
    for i in range(n_lock):
        a = -180 + (i + 0.5 + rng.uniform(-0.12, 0.12)) * 360.0 / n_lock
        pts = [place(a + 4.0 * u, u, 1.0 + (0.12 if u < 1.0 else 0.0)) for u in us]
        P = np.vstack([p[0] for p in pts])
        P[-1] += DOWN * rng.uniform(0.002, 0.007)
        S.append((P, np.vstack([p[1] for p in pts])))
        Ds.append(np.vstack([p[2] for p in pts]))
    n = len(S)
    for i, (P, N) in enumerate(S):
        d = np.mean([np.linalg.norm(P - S[(i - 1) % n][0], axis=1), np.linalg.norm(P - S[(i + 1) % n][0], axis=1)], 0)
        t = arc_t(P)
        w = np.clip(0.8 * d, 0.006, 0.034) * pw((0.9, 1.0, 1.0, 1.0, 0.72), t)
        lock(m, P + N * (0.0012 if i % 2 else 0.0), N, w, 0.0050 * pw((0.3, 1.0, 1.0, 1.0, 0.8, 0.5), t), sect="roof",
             G=rng.uniform(0.66, 1.0), D=Ds[i], R=0.35 * sstep(0.35, 1.0, t))


def bowl(head, rng):
    """A bowl cut: a thick even cap cut straight across the brow and round above the ear lobes."""
    m = HairMesh()

    def z_edge(a):
        a = abs((a + 180) % 360 - 180)
        return 1.731 - 0.057 * float(sstep(38, 96, a)) - 0.022 * float(sstep(100, 170, a))
    _cut(m, head, rng, z_edge, lambda a: 0.0155 + 0.005 * sstep(50, 95, a), lambda a: 0.020 + 0.060 * sstep(40, 95, a))
    return m


def tonsure(head, rng):
    """A monk's ring of hair round a shaved crown."""
    m = HairMesh()
    K = dirv(180, 9)
    pols = np.arange(5.0, 90.0, 0.25)

    def f_in(a):
        out = np.zeros(len(a))
        for j, x in enumerate(a):
            d = dirv(np.full(len(pols), x), pols)
            out[j] = pols[np.argmax(np.degrees(np.arccos(np.clip(d @ K, -1, 1))) >= 37.0)] / float(head.hl(x))
        return out

    def z_edge(a):
        a = abs((a + 180) % 360 - 180)
        return 1.744 - 0.045 * float(sstep(36, 92, a)) - 0.030 * float(sstep(100, 170, a))
    _cut(m, head, rng, z_edge, lambda a: 0.0115 + 0.003 * sstep(50, 95, a), lambda a: 0.018 + 0.045 * sstep(40, 95, a),
         n_az=28, n_lock=22, f_in=f_in)
    return m


def wild(head, rng):
    """A huge untamed mane: long ragged locks thrown up and back, falling round the shoulders."""
    m = HairMesh()
    fe = _low_edge(1.16, 1.04)
    g = 0.010
    cap(m, head, thick=0.016, n_az=22, f_edge=fe, G=0.42, grow=g, rng=rng, rim=0.30)
    tiers = [(6, 0.18, 0.125), (10, 0.47, 0.150), (13, 0.80, 0.170), (12, 1.0, 0.200), (6, 0.955, 0.120)]
    for ti, (cnt, f, L0) in enumerate(tiers):
        for i in range(cnt):
            az = -180 + (i + 0.5 * (ti % 2) + rng.uniform(-0.2, 0.2)) * 360.0 / cnt
            if ti == 3:                                   # the lowest tier only behind the temples
                az = 66 + (i + rng.uniform(0.3, 0.7)) * 228.0 / cnt
                az = az if az <= 180 else az - 360
            if ti == 4:                                   # ... and a fringe rooted on the brow's hairline
                az = -62 + (i + rng.uniform(0.35, 0.65)) * 124.0 / cnt
            ff = f * (float(fe(az)) * 0.97 if ti == 3 else 1.0) * (1.0 if ti == 4 else rng.uniform(0.94, 1.0))
            root, N = head.on(az, ff, 0.006)
            out = unit(np.array([N[0], N[1], 0.0]))
            front = abs(az) < 60
            sgn = math.copysign(1.0, az if abs(az) > 4 else rng.normal())
            side = np.array([sgn, 0.0, 0.0])
            if front:                                     # the fringe sweeps up, aside and back, clear of the eyes
                d = unit(N * 0.6 + UP * 0.55 + side * 0.65 + BACK * 0.75 + rng.normal(0, 0.10, 3))
                droop = 0.22
            else:
                back = float(sstep(60, 150, abs(az)))
                d = unit(N * 0.62 + out * 0.40 + BACK * (0.72 + 0.20 * back) + UP * (0.16 - 0.85 * f)
                         + rng.normal(0, 0.12, 3))
                droop = 0.40 + 0.40 * f
            L = L0 * rng.uniform(0.85, 1.15)
            s = np.linspace(0, 1, 6)
            wav = unit(np.cross(d, N + rng.normal(0, 0.2, 3)))
            ph = rng.uniform(0, 2 * math.pi)
            P = (root + d * (s * L)[:, None] + DOWN * (s ** 2 * L * droop)[:, None]
                 + wav * (np.sin(s * 5.0 + ph) * s * L * 0.09)[:, None])
            P[1:] = head.push(P[1:], 0.012)
            Nn = perp(tangents(P), head.away(P))
            w0 = rng.uniform(0.027, 0.034)
            gdir = unit(d + DOWN * droop * 1.6)
            lock(m, P, Nn, [w0 * 0.8, w0, w0 * 0.95, w0 * 0.75, w0 * 0.45, 0.0],
                 [0.012, 0.016, 0.015, 0.011, 0.006, 0.0], sect="tri", sway=(0.1, 1.0), G=rng.uniform(0.56, 1.0),
                 grow=(gdir * 0.125, 0.10), gw=0.25, ride=np.tile(N * g, (6, 1)) * np.linspace(1, 0, 6)[:, None])
    return m
