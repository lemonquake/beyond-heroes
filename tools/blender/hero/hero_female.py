"""bh-031: the female body, fitted from the player's own female model (models/female_generic.obj).

The scan has no rig, no UVs and short, slightly lowered arms. Instead of building a second body (a second skeleton
fit, second skin weights, second clothing kit), the hero body itself is fitted onto the scan's surface and the result
is stored as one more shape key, "female". Everything that already works on the hero (all clips, every worn piece,
hair, beards, the face drawn by the skin shader, the creator's sliders) then works on her too, and the clothing follows
the key like it follows "muscle" or "belly".

Runs with plain Python (numpy + scipy), not inside Blender:
  blender -b --factory-startup --python tools/blender/hero/hero_female_src.py      # scan -> female_src.npz
  python tools/blender/hero/hero_female.py                                          # -> data/female_delta.npz

Steps
1. scale the scan to 1.80 m (the rig's height; the game's height slider makes her shorter);
2. conform it to the rig's rest pose: torso centred like the hero's; each arm straightened onto the hero's arm line
   (z = 1.44, y = 0) and stretched along the bone so the wrist lands on the rig's wrist; each leg carried onto the
   hero's leg line;
3. shrink-wrap the hero body onto it: every vertex moves to the nearest scan point whose normal agrees, the moves are
   smoothed over the mesh, four rounds. The head (its face is drawn by the shader at fixed landmarks) and the fists
   (every clip holds a weapon in a closed hand) keep the hero's shape; the neck and wrists blend.
"""
import os
import sys

import numpy as np
from scipy import sparse
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC = os.path.join(ROOT, "work", "lemondev", "bh-031", "scratch", "female", "female_src.npz")
HERO = os.path.join(ROOT, "work", "lemondev", "bh-023", "scratch", "hero_mesh.npz")
OUT = os.path.join(HERE, "data", "female_delta.npz")
sys.path.insert(0, HERE)

import hero_shapes as SH  # noqa: E402

HEIGHT = 1.80
SHOULDER_X = 0.19
HERO_WRIST_X = 0.73
ARM_Z = 1.44
LEG_X = 0.105


def step(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def normals(V, T):
    return SH.vertex_normals(V, T)


def centreline(V, side, axis, values, band, sel):
    """Centres of slices of V (one side) across `axis` at `values` -> (k, 3)."""
    out = []
    for v in values:
        m = sel & (np.abs(V[:, axis] - v) < band) & (V[:, 0] * side > 0)
        s = V[m]
        out.append((s.min(0) + s.max(0)) * 0.5 if len(s) else np.full(3, np.nan))
    return np.array(out)


def find_wrist(V, side):
    """The thinnest slice of the forearm before the hand opens out."""
    best, wx = 9.0, 0.6
    for x in np.arange(0.48, 0.68, 0.005):
        s = V[(np.abs(V[:, 0] * side - x) < 0.004) & (V[:, 2] > 1.2)]
        if len(s) < 8:
            continue
        h = np.ptp(s[:, 2]) + np.ptp(s[:, 1]) * 0.5
        if h < best:
            best, wx = h, x
    return wx


def conform(F):
    F = F.copy()
    # torso: the scan's waist centre onto the hero's
    waist = F[(np.abs(F[:, 2] - 1.18) < 0.01) & (np.abs(F[:, 0]) < 0.15)]
    F[:, 1] += -0.037 - (waist[:, 1].min() + waist[:, 1].max()) * 0.5
    out = F.copy()
    for side in (1.0, -1.0):
        ax = F[:, 0] * side
        arm = step(0.15, 0.24, ax) * step(1.15, 1.25, F[:, 2])
        wrist = find_wrist(F, side)
        k = (HERO_WRIST_X - SHOULDER_X) / (wrist - SHOULDER_X)
        xs = np.arange(0.26, wrist, 0.02)
        cl = centreline(F, side, 0, xs * side, 0.006, F[:, 2] > 1.2)
        ok = ~np.isnan(cl[:, 1])
        py = np.polyfit(xs[ok], cl[ok, 1], 1)
        pz = np.polyfit(xs[ok], cl[ok, 2], 1)
        # straighten: remove the arm line's own offset and slope, put it on (y 0, z ARM_Z)
        lift = step(0.20, 0.30, ax)
        dy = -(np.polyval(py, ax)) * lift
        dz = (ARM_Z - np.polyval(pz, ax)) * lift
        # stretch along the bone, the shoulder fixed: wrist -> the rig's wrist; the hand beyond moves rigidly
        kk = 1.0 + (k - 1.0) * step(SHOULDER_X, 0.30, ax)
        nx = SHOULDER_X + (np.minimum(ax, wrist) - SHOULDER_X) * kk + np.maximum(ax - wrist, 0.0)
        nx = np.where(ax > SHOULDER_X, nx, ax)
        m = arm > 0
        out[m, 0] = F[m, 0] + (nx[m] * side - F[m, 0]) * arm[m]
        out[m, 1] = F[m, 1] + dy[m] * arm[m]
        out[m, 2] = F[m, 2] + dz[m] * arm[m]
        print("arm %+d: wrist %.3f stretch %.3f, line y %.3f%+.3fx z %.3f%+.3fx" % (side, wrist, k, py[1], py[0], pz[1], pz[0]))
        # legs: each leg's centre line onto the hero's (x = LEG_X); y follows the hero's own leg centres
        leg = (1 - step(0.76, 0.88, F[:, 2])) * (F[:, 0] * side > 0)
        zs = np.arange(0.14, 0.76, 0.04)
        cl = centreline(F, side, 2, zs, 0.006, np.abs(F[:, 0]) < 0.3)
        ok = ~np.isnan(cl[:, 0])
        px = np.polyfit(zs[ok], cl[ok, 0] * side, 2)
        dxl = (LEG_X - np.polyval(px, F[:, 2])) * side
        out[:, 0] += dxl * leg
        print("leg %+d: centre x %s" % (side, np.round(np.polyval(px, [0.15, 0.45, 0.75]), 3)))
    return out


def laplacian(n, T):
    i = np.concatenate([T[:, 0], T[:, 1], T[:, 2], T[:, 1], T[:, 2], T[:, 0]])
    j = np.concatenate([T[:, 1], T[:, 2], T[:, 0], T[:, 0], T[:, 1], T[:, 2]])
    A = sparse.coo_matrix((np.ones(len(i)), (i, j)), shape=(n, n)).tocsr()
    A.data[:] = 1.0
    deg = np.asarray(A.sum(1)).ravel()
    return sparse.diags(1.0 / np.maximum(deg, 1)) @ A


def smooth(D, L, iters, keep=None):
    for _ in range(iters):
        S = L @ D
        D = D * 0.5 + S * 0.5 if keep is None else np.where(keep[:, None], D, D * 0.5 + S * 0.5)
    return D


def _fall(V, c, r):
    d = np.linalg.norm((V - np.asarray(c, float)) / np.asarray(r, float), axis=1)
    return (1.0 - np.clip(d, 0.0, 1.0) ** 2) ** 2


BUST_Z = 1.322          # the cups' fullest point on the scan (z 1.32..1.34, x +-0.068)
BUST_X = 0.074
BUST_DEPTH = 0.030      # a touch fuller than the scan's sports bra so it still reads from the game camera


def bust(V, delta, L):
    """The coarse body cannot hold the scan's cups, and the hero's pectorals leave a crease down the sternum: the
    front of the chest is flattened (its positions smoothed) and two round cups are laid over it."""
    P = V + delta
    front = 1 - step(-0.07, -0.03, V[:, 1])
    region = np.clip(_fall(V, (BUST_X, -0.12, BUST_Z), (0.13, 0.14, 0.13)) + _fall(V, (-BUST_X, -0.12, BUST_Z), (0.13, 0.14, 0.13)),
                     0.0, 1.0) * front
    Ps = P.copy()
    for _ in range(25):
        Ps = Ps * 0.5 + (L @ Ps) * 0.5
        Ps = Ps * region[:, None] + P * (1 - region[:, None])
    # positional smoothing pulls the surface in a little: keep the original depth on average
    m = region > 0.5
    Ps[:, 1] += (P[m, 1] - Ps[m, 1]).mean() if m.any() else 0.0
    P = P * (1 - region[:, None]) + Ps * region[:, None]
    for sx in (1.0, -1.0):
        u = ((V[:, 0] - sx * BUST_X) / 0.072) ** 2 + ((V[:, 2] - BUST_Z) / np.where(V[:, 2] < BUST_Z, 0.058, 0.085)) ** 2
        cap = np.clip(1.0 - u, 0.0, 1.0) ** 0.75 * step(0.0, 0.25, 1.0 - u)
        P[:, 1] -= BUST_DEPTH * cap * front
        P[:, 0] += sx * 0.003 * cap * front
    return P - V


def fit(V, T, W, bones, F, FT):
    n = len(V)
    L = laplacian(n, T)
    head = SH.head_mask(V)
    hand = sum(W[:, list(bones).index(b)] for b in ("hand.L", "hand.R"))
    hand = np.clip(hand * 1.6, 0.0, 1.0)
    w = (1 - step(1.52, 1.585, V[:, 2]) * (np.abs(V[:, 0]) < 0.2)) * (1 - hand)
    w = np.clip(smooth(w[:, None], L, 8)[:, 0], 0.0, 1.0)
    FN = normals(F, FT)
    # sample the scan densely (vertices + face centres) so the stretched arms stay covered
    C = F[FT].mean(1)
    CN = FN[FT].sum(1)
    CN /= np.maximum(np.linalg.norm(CN, axis=1, keepdims=True), 1e-9)
    P = np.vstack([F, C])
    PN = np.vstack([FN, CN])
    tree = cKDTree(P)
    cur = V.copy()
    for it, (reach, sm) in enumerate(((0.12, 8), (0.09, 5), (0.07, 3), (0.05, 2), (0.04, 1), (0.05, 0), (0.05, 0), (0.05, 0))):
        N = normals(cur, T)
        d, idx = tree.query(cur, k=24)
        dots = np.einsum("nkj,nj->nk", PN[idx], N)
        cand = np.where(dots > 0.25, d, np.inf)
        best = np.argmin(cand, 1)
        found = np.isfinite(cand[np.arange(n), best]) & (cand[np.arange(n), best] < reach)
        tgt = P[idx[np.arange(n), best]]
        D = np.where(found[:, None], tgt - cur, 0.0)
        # a point-to-plane move along the scan normal keeps vertices from sliding along the surface
        tn = PN[idx[np.arange(n), best]]
        if sm > 0:
            D = tn * np.einsum("nj,nj->n", D, tn)[:, None]
        # the last rounds snap straight onto the surface: the body is coarse (86 vertices across the chest) and any
        # smoothing there flattens the bust
        D = smooth(D * w[:, None], L, sm)
        cur = cur + D
        print("round %d: %d/%d matched, mean move %.4f m, max %.4f" % (it, found.sum(), n, np.linalg.norm(D, axis=1).mean(),
                                                                       np.linalg.norm(D, axis=1).max()))
    delta = cur - V
    delta = 0.6 * delta + 0.4 * smooth(delta, L, 1)
    delta = bust(V, delta, L)
    return delta * w[:, None] + smooth(delta, L, 6) * (1 - w[:, None]) * w[:, None]


def main():
    # the decimated scan from hero_female_src.py, else the copy kept in the repo (the 97 MB OBJ is not committed)
    s = np.load(SRC if os.path.exists(SRC) else os.path.join(HERE, "data", "female_src.npz"))
    F0, FT = s["V"], s["T"]
    F0 = F0 * (HEIGHT / F0[:, 2].max())
    F = conform(F0)
    h = np.load(HERO)
    V, T, W, bones = h["V"], h["T"], h["W"], h["bones"]
    delta = fit(V, T, W, bones, F, FT)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    np.savez_compressed(OUT, V=V.astype(np.float32), delta=delta.astype(np.float32))
    np.savez(os.path.join(os.path.dirname(SRC), "female_fit.npz"), F=F, FT=FT, V=V, T=T, delta=delta)
    print("FEMALE_DELTA", OUT, "max %.3f m" % np.linalg.norm(delta, axis=1).max())


if __name__ == "__main__":
    main()
