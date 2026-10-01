"""Obsidian Golem (bh-029, Builder M6, Zarael / the Obsidian Engine brute construct): a ~2.9 m Wirewright engine-guard
knapped out of black volcanic glass. Every part of it is faceted - flat, glossy planes meeting at hard ridges - and
held together by a frame of old copper: bands round the waist and chest, collars at every joint, clamps over the
breast. Where the glass has cracked, the copper has run molten into the cracks and still burns (white, the bh-029
glow rule): a branching seam network over the breast from a clamped seam-knot, down the arms and legs, a V of white
light for eyes in a small six-sided crystal head sunk between the shoulders. Huge glass clusters have grown out of
it like a crest - a ridge of tall shards up the back and over each shoulder (the silhouette key from the gameplay
camera) - and its forearms swell into massive faceted glass fists studded with shard knuckles.

Built at true size on the shared humanoid skeleton (custom construct proportions; every part rigid to one bone, faceted
joint balls cover the gaps, the rune_golem / mossback_idol pattern). No weapon: the fists strike.
Clips: boss_charge boss_slam gs_1 gs_2 (+ cast_heavy).

Also holds the small "obsidian kit" the other M6 Obsidian Engine models share (engine_heart, stoker_thrall,
shardcaster): `Facet` (faceted loft with flat-face surface queries), `flimb` (faceted limb), `seam` (copper-lipped
white seam), `jag`, `ridge` (shard clusters)."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, interp_rows  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz, R_axis  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as GK  # noqa: E402
import enemy_rune_golem as RG  # noqa: E402
import kit_a_common as A  # noqa: E402

PROPS = proportions(
    1.6,
    pelvis_h=1.2, hip_h=1.13, knee_h=0.6, ankle_h=0.15, hip_x=0.27, ball_fwd=0.28, ball_h=0.05, toe_len=0.14,
    heel_back=0.12,
    hips_len=0.2, spine_len=0.36, chest_len=0.74, neck_len=0.06, head_len=0.34,
    clav_x0=0.12, clav_drop=0.2, shoulder_x=0.64, upper_len=0.54, fore_len=0.62, hand_len=0.24, grip_x=0.14,
    grip_drop=0.03,
)
L = GK.levels(PROPS)
PREVIEW_HEIGHT = 3.3

PALETTE = "obsidian_golem"
GLASS = ((0.042, 0.042, 0.052), 0.25, 0.1, None, 0.0, 1.0)          # black volcanic glass, glossy
PALETTE_COLORS = {
    "BH_Stone": GLASS,                                                  # the knapped glass body
    "BH_Horn": ((0.06, 0.052, 0.08), 0.3, 0.06, None, 0.0, 1.0),        # shard crystals (a touch smoky violet-black)
    "BH_DarkSteel": ((0.016, 0.016, 0.02), 0.2, 0.3, None, 0.0, 1.0),   # inner glass core / joint balls
    "BH_Bronze": ((0.5, 0.24, 0.11), 1.0, 0.42, None, 0.0, 1.0),        # old copper frame: bands, collars, clamps
    "BH_Gold": ((0.62, 0.36, 0.16), 1.0, 0.32, None, 0.0, 1.0),         # bright copper lips of the seams
    "BH_Shadow": ((0.01, 0.01, 0.012), 0.0, 0.85, None, 0.0, 1.0),      # deep cracks
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),  # molten seams, eyes (Zarael: white)
}
CLIPS = ["boss_charge", "boss_slam", "gs_1", "gs_2", "cast_heavy"]

P = RG.P
FRONT, BACK = np.array([0, -1.0, 0]), np.array([0, 1.0, 0])


# ================================================================================================= obsidian kit
def fring(z, rx, ryf, ryb, cy=0.0, n=8, k=None):
    """Polygon ring (flat face at the front: the first edge straddles -Y), CCW from above (loft faces outward)."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n - math.pi / 2
        c, s = math.cos(a), math.sin(a)
        f = 1.0 if k is None else k[i]
        pts.append((rx * c * f, cy + (ryf if s < 0 else ryb) * s * f, z))
    return np.array(pts)


class Facet:
    """Faceted block lofted from rows (z, rx, ryf, ryb[, cy]) with n flat sides; per-side radius factors (seeded) make
    the knapped planes irregular but keep every side flat. .part = the Part; .front(x, z) / .back(x, z) = the y of the
    flat surface (so seams and plates sit flush on it)."""

    def __init__(self, rows, n=8, seed=0, amp=0.07, mat="BH_Stone", cap=True):
        self.rows = [tuple(r) + (0.0,) * (5 - len(r)) for r in rows]
        rng = np.random.default_rng(seed)
        self.n = n
        self.k = 1.0 + (rng.random(n) - 0.5) * 2 * amp
        rings = [fring(r[0], r[1], r[2], r[3], r[4], n, self.k) for r in self.rows]
        V, F = M.loft(rings, cap0=cap, cap1=cap)
        self.part = P(V, F, mat, "facet")

    def _poly(self, z):
        r = interp_rows(self.rows, z)
        return fring(z, r[1], r[2], r[3], r[4], self.n, self.k)[:, :2], r[4]

    def _hit(self, x, z, front):
        poly, cy = self._poly(z)
        ys = []
        for i in range(len(poly)):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
            if (x0 - x) * (x1 - x) <= 0 and abs(x1 - x0) > 1e-9:
                t = (x - x0) / (x1 - x0)
                ys.append(y0 + (y1 - y0) * t)
        if not ys:
            return cy
        return min(ys) if front else max(ys)

    def band(self, z, h, g, mat="BH_Bronze"):
        """A copper band hugging the facets (same polygon, grown by g) between z - h/2 and z + h/2."""
        r = interp_rows(self.rows, z)
        rings = [fring(zz, r[1] + g, r[2] + g, r[3] + g, r[4], self.n, self.k) for zz in (z - h / 2, z + h / 2)]
        V, F = M.loft(rings, cap0=True, cap1=True)
        return P(V, F, mat, "fband")

    def front(self, x, z):
        return self._hit(x, z, True)

    def back(self, x, z):
        return self._hit(x, z, False)

    def fpts(self, xz, out=0.0):
        return [(x, self.front(x, z) - out, z) for x, z in xz]

    def bpts(self, xz, out=0.0):
        return [(x, self.back(x, z) + out, z) for x, z in xz]


def flimb(body, b, prof, mat="BH_Stone", n=6, front=(0, -1, 0)):
    """Faceted limb along a posed bone (flat sides, hard ridges): prof (u, rx, ry)."""
    return body.limb(b, prof, mat, n=n, p=2.0, front=front)


def fprism(a, b, prof, mat="BH_Stone", n=6, up=(0, -1, 0)):
    """Faceted prism along a -> (points) with per-station radii prof [(rx, ry)...] spaced evenly."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    pts = [a + (b - a) * t for t in np.linspace(0, 1, len(prof))]
    V, F = M.tube(pts, prof, n=n, up=up, p=2.0)
    return P(V, F, mat, "fprism")


def seam(pts, nrm, r=0.018, lip="BH_Gold", glow="BH_Emissive", broken=()):
    """Molten seam: copper-lipped groove with the white melt just proud of it (nrm: outward normal, one or per point).
    broken: segment indices where the melt has gone dark (copper only)."""
    pts = np.asarray(pts, float)
    nrm = np.asarray(nrm, float)
    if nrm.ndim == 1:
        nrm = np.repeat(nrm[None], len(pts), 0)
    out = [A.tube(pts - nrm * r * 0.5, r * 1.75, lip, n=4)]
    segs, cur = [], [0]
    for i in range(1, len(pts)):
        if (i - 1) in broken:
            segs.append(cur)
            cur = [i]
        else:
            cur.append(i)
    segs.append(cur)
    for s in segs:
        if len(s) >= 2:
            out.append(A.tube(pts[s] + nrm[s] * r * 0.25, r, glow, n=5))
    return out


def jag(a, b, n, amp, nrm, seed):
    """Jagged polyline a -> b, offsets across the line in the surface plane (nrm = surface normal)."""
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = normalize(b - a)
    side = normalize(np.cross(np.asarray(nrm, float), d))
    return [a + (b - a) * (i / (n - 1)) + side * (0.0 if i in (0, n - 1) else (rng.random() - 0.5) * 2 * amp)
            for i in range(n)]


def ridge(base, d, length, r, mat="BH_Horn", sides=5, seed=0, count=3, spread=22.0):
    """A cluster: one big shard along d plus `count - 1` smaller ones splayed round it."""
    return A.cluster(base, d, length, mat, count=count, seed=seed, spread=spread, sides=sides)


def addp(body, parts, bone=None, weights=None):
    for p in parts:
        body.add(p, bone, weights)


# ================================================================================================= golem
zh, zs, zc, zn, zhd = L["hips"], L["spine"], L["chest"], L["neck"], L["head"]
HEAD_DY, HEAD_DZ = -0.12, -0.02
PELV = [(zh - 0.22, 0.3, 0.22, 0.22), (zh - 0.08, 0.41, 0.28, 0.27), (zh + 0.1, 0.43, 0.29, 0.28),
        (zh + 0.18, 0.38, 0.26, 0.25)]
ABDO = [(zs - 0.06, 0.3, 0.22, 0.22), (zs + 0.12, 0.36, 0.26, 0.25), (zs + 0.3, 0.4, 0.28, 0.27)]
CHEST = [(zc - 0.12, 0.44, 0.3, 0.3, 0.0), (zc + 0.06, 0.58, 0.38, 0.36, -0.01), (zc + 0.32, 0.72, 0.44, 0.44, -0.02),
         (zc + 0.56, 0.78, 0.45, 0.48, -0.01), (zn - 0.05, 0.72, 0.39, 0.46, 0.01), (zn + 0.07, 0.48, 0.28, 0.34, 0.02)]
HEADR = [(-0.12, 0.16, 0.18, 0.16, -0.1), (0.0, 0.2, 0.23, 0.19, -0.12), (0.16, 0.21, 0.24, 0.2, -0.12),
         (0.27, 0.17, 0.2, 0.17, -0.11), (0.34, 0.08, 0.1, 0.09, -0.1)]


def build(body: Body):
    add = body.add
    # dark glass core column: fills the gaps between the blocks when the torso bends
    core_w = GK.zspec_w([(zh + 0.05, "hips"), (zs + 0.05, "spine"), (zc - 0.05, "spine"), (zc + 0.1, "chest")])
    V, F = M.tube([(0, 0.0, zh - 0.05), (0, 0.0, zs), (0, 0.0, zc), (0, 0.0, zc + 0.3)], [(0.32, 0.22)] * 4, n=8,
                  up=(0, -1, 0), p=2.0)
    add(P(V, F, "BH_DarkSteel", "core"), weights=core_w)
    pelvis(body)
    chest(body)
    back_ridge(body)
    head(body)
    for s in ("L", "R"):
        arm(body, s)
        leg(body, s)


def pelvis(body):
    add = body.add
    pv = Facet(PELV, n=8, seed=1)
    add(pv.part, "hips")
    add(pv.band(zh + 0.12, 0.08, 0.016), "hips")
    # glass tassets (two per side) hanging over the thighs, a copper clasp on each
    for sx in (1, -1):
        lb = "thigh.L" if sx > 0 else "thigh.R"
        tw = (lambda V, lb=lb: [{"hips": 0.55, lb: 0.45}] * len(V))
        for (x, y, w, rz, ln) in ((0.2, -0.3, 0.28, 8, 0.42), (0.44, -0.08, 0.24, 70, 0.36)):
            c = np.array([sx * x, y, zh - 0.2])
            R = Rz(sx * rz) @ Rx(10)
            V, F = M.prism(np.array([(-w / 2, 0.2), (w / 2, 0.2), (w / 2 * 0.8, -0.1), (0.0, -0.2 - ln * 0.3),
                                     (-w / 2 * 0.8, -0.1)]), 0.08, axis="y")
            add(P(V, F, "BH_Stone", "tasset").rot(R).move(c), weights=tw)
            add(RG.slab((w * 0.9, 0.1, 0.05), c + R @ np.array([0, 0, 0.19]), R=R, mat="BH_Bronze", bev=0.008),
                weights=tw)
    ab = Facet(ABDO, n=8, seed=2)
    add(ab.part, "spine")
    add(ab.band(zs + 0.22, 0.06, 0.014), "spine")
    addp(body, seam(ab.fpts([(-0.05, zs + 0.3), (0.02, zs + 0.18), (-0.04, zs + 0.08), (0.03, zs - 0.03)], 0.004),
                    FRONT, 0.018), "spine")


def chest(body):
    add = body.add
    ch = Facet(CHEST, n=10, seed=3)
    add(ch.part, "chest")
    add(ch.band(zc - 0.06, 0.08, 0.016), "chest")
    # breast plates: two big knapped panes, slightly proud, angled
    for sx in (1, -1):
        zp, xp = zc + 0.42, sx * 0.33
        c = np.array([xp, ch.front(xp, zp) - 0.02, zp])
        o = np.array([(-0.2, -0.17), (0.18, -0.2), (0.22, 0.12), (0.05, 0.2), (-0.21, 0.15)])
        o[:, 0] *= sx
        if sx < 0:
            o = o[::-1]
        V, F = M.prism(o, 0.07, axis="y")
        add(P(V, F, "BH_Stone", "pane").rot(Rz(sx * 10)).move(c), "chest")
    # the seam-knot on the sternum: a copper clamp over a white melt pool
    zk = zc + 0.22
    yk = ch.front(0, zk)
    add(GK.blob((0, yk - 0.02, zk), 0.11, "BH_Emissive", scale=(1, 0.4, 1.15), n=8, rings=5), "chest")
    for a in (35, 145, 215, 325):
        ra = math.radians(a)
        cc = np.array([0.13 * math.cos(ra), yk - 0.04, zk + 0.15 * math.sin(ra)])
        add(RG.slab((0.06, 0.06, 0.14), cc, R=Ry(-a + 90), mat="BH_Bronze", bev=0.01), "chest")
    ring = [(0.15 * math.cos(a), yk - 0.03, zk + 0.17 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9)]
    add(A.tube(ring, 0.022, "BH_Bronze", n=5), "chest")
    # molten seams branching from the knot through the glass (jagged, one gone dark)
    paths = [((0.1, zk + 0.1), (0.5, zn - 0.08), 7, 11, ()), ((-0.1, zk + 0.1), (-0.46, zn - 0.02), 7, 12, (3,)),
             ((0.12, zk - 0.05), (0.6, zc + 0.04), 6, 13, ()), ((-0.12, zk - 0.06), (-0.5, zc - 0.04), 6, 14, ()),
             ((0.0, zk - 0.16), (0.04, zc - 0.1), 4, 15, ()), ((0.0, zk + 0.17), (0.0, zn + 0.0), 4, 16, ())]
    for (a, b, n, sd, br) in paths:
        q = jag((a[0], 0, a[1]), (b[0], 0, b[1]), n, 0.045, FRONT, sd)
        addp(body, seam(ch.fpts([(p[0], p[2]) for p in q], 0.003), FRONT, 0.026, broken=br), "chest")
    # a branch off each upper seam
    for sx, sd in ((1, 21), (-1, 22)):
        q = jag((sx * 0.3, 0, zk + 0.26), (sx * 0.2, 0, zn - 0.02), 4, 0.03, FRONT, sd)
        addp(body, seam(ch.fpts([(p[0], p[2]) for p in q], 0.003), FRONT, 0.02), "chest")
    # back: seams between the shard roots
    for sx, sd in ((1, 31), (-1, 32)):
        q = jag((sx * 0.08, 0, zc + 0.05), (sx * 0.5, 0, zn - 0.1), 6, 0.05, BACK, sd)
        addp(body, seam(ch.bpts([(p[0], p[2]) for p in q], 0.003), BACK, 0.024), "chest")
    # copper collar plates round the sunken head
    for sx in (1, -1):
        add(RG.slab((0.18, 0.44, 0.1), (sx * 0.47, 0.06, zn - 0.01), R=Ry(sx * 22), mat="BH_Bronze", bev=0.01),
            "chest")
    body._ch = ch


def back_ridge(body):
    """The crest: tall glass shards in a ridge up the back, splayed outward (the gameplay-camera silhouette)."""
    add = body.add
    ch = body._ch
    for k, (x, z, dx, ln, sd) in enumerate(((0.0, zn - 0.08, 0.0, 0.95, 1), (0.26, zn - 0.16, 0.45, 0.8, 2),
                                           (-0.26, zn - 0.16, -0.45, 0.8, 3), (0.12, zc + 0.3, 0.25, 0.62, 4),
                                           (-0.14, zc + 0.28, -0.25, 0.6, 5), (0.0, zc + 0.08, 0.0, 0.42, 6))):
        base = np.array([x, ch.back(x, z) - 0.06, z])
        d = normalize(np.array([dx, 0.75, 1.0]))
        parts = ridge(base, d, ln, 0.0, seed=40 + sd, count=3 if k < 3 else 2, spread=18)
        addp(body, parts, "chest")
        # a copper socket ring where the big shard grows out
        add(A.tube([base - d * 0.02, base + d * 0.06], ln * 0.22, "BH_Bronze", n=6), "chest")


def head(body):
    add = body.add
    z0 = zhd + HEAD_DZ
    rows = [(z0 + r[0], r[1], r[2], r[3], r[4] + HEAD_DY) for r in HEADR]
    hd = Facet(rows, n=6, seed=7, amp=0.05)
    add(hd.part, "head")
    # brow: two knapped panes meeting in a point over the nose (a V), deep sockets under them with the white eyes
    zb = z0 + 0.2
    yb = hd.front(0, zb)
    for sx in (1, -1):
        o = np.array([(0.0, 0.03), (0.2, 0.09), (0.21, 0.035), (0.0, -0.035)])
        o[:, 0] *= sx
        if sx < 0:
            o = o[::-1]
        V, F = M.prism(o, 0.07, axis="y")
        add(P(V, F, "BH_Stone", "brow").rot(Rx(-14)).move((0, yb - 0.025, zb + 0.0)), "head")
        a = np.array([sx * 0.035, yb - 0.004, z0 + 0.13])
        b = np.array([sx * 0.17, yb + 0.012, z0 + 0.205])
        add(A.tube([a + (0, 0.014, 0), b + (0, 0.014, 0)], 0.04, "BH_Shadow", n=4), "head")
        add(A.tube([a, b], 0.024, "BH_Emissive", n=5), "head")
    ym = hd.front(0, z0 + 0.02)
    add(A.tube(jag((-0.11, ym - 0.002, z0 + 0.03), (0.11, ym - 0.002, z0 + 0.03), 5, 0.014, FRONT, 9), 0.014,
               "BH_Shadow", n=4), "head")
    # molten seam up the forehead into the crest
    addp(body, seam(hd.fpts([(0.0, z0 + 0.25), (0.015, z0 + 0.29), (0.0, z0 + 0.33)], 0.002), (0, -0.7, 0.7), 0.014),
         "head")
    # copper jaw band + crest of three shards on the crown
    add(hd.band(z0 + 0.05, 0.04, 0.01), "head")
    top = np.array([0, HEAD_DY + 0.02, z0 + 0.3])
    addp(body, A.cluster(top, (0, 0.35, 1), 0.4, "BH_Horn", count=3, seed=8, spread=24), "head")


def arm(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    sh_b, ua, fa, ha = "shoulder." + s, "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
    add(GK.blob(sh, 0.22, "BH_DarkSteel", n=8, rings=5), ua)
    add(flimb(body, ua, [(0.08, 0.17, 0.18), (0.5, 0.2, 0.2), (0.92, 0.17, 0.18)], n=6), ua)
    add(RG.joint_ring(sh + (el - sh) * 0.86, el - sh, 0.2, w=0.07, mat="BH_Bronze"), ua)
    Ax = body.axes(ua)
    ul = body.p["upper_len"]
    addp(body, seam(body.lpt(ua, jag((0, 0.2 * ul, 0.2), (0.02, 0.75 * ul, 0.2), 4, 0.03, (0, 0, 1), 50 + (sx > 0))),
                    Ax[:, 2], 0.016), ua)
    # pauldron: a thick knapped slab with a copper rim and a shard cluster bursting up and out of it
    c = sh + np.array([sx * 0.04, 0.0, 0.17])
    R = Ry(-sx * 14)
    V, F = M.tube([c + R @ np.array([0, 0, -0.1]), c + R @ np.array([0, 0, 0.06]), c + R @ np.array([0, 0, 0.14])],
                  [(0.3, 0.32), (0.32, 0.34), (0.22, 0.24)], n=6, up=(1, 0, 0), p=2.0)
    add(P(V, F, "BH_Stone", "pauldron"), sh_b)
    add(A.tube([c + R @ np.array([0, 0, -0.12]), c + R @ np.array([0, 0, -0.06])], 0.33, "BH_Bronze", n=6), sh_b)
    top = c + R @ np.array([sx * 0.03, 0.0, 0.12])
    addp(body, A.cluster(top, (sx * 0.55, 0.25, 1.0), 0.6, "BH_Horn", count=4, seed=60 + (sx > 0), spread=26), sh_b)
    # elbow ball, forearm swelling into the glass fist
    add(GK.blob(el, 0.19, "BH_DarkSteel", n=8, rings=5), fa)
    add(flimb(body, fa, [(0.04, 0.19, 0.19), (0.45, 0.25, 0.25), (0.82, 0.28, 0.28), (1.0, 0.25, 0.25)], n=7), fa)
    add(RG.joint_ring(el + (wr - el) * 0.2, wr - el, 0.24, w=0.06, mat="BH_Bronze"), fa)
    Ax = body.axes(fa)
    fl = body.p["fore_len"]
    for k, (dx, sd) in enumerate(((0.0, 70), (0.12, 71))):
        q = body.lpt(fa, jag((dx, 0.28 * fl, 0.26), (dx * 0.6, 0.85 * fl, 0.28), 5, 0.035, (0, 0, 1), sd + (sx > 0) * 3))
        addp(body, seam(q, Ax[:, 2], 0.017, broken=(1,) if k else ()), fa)
    # shard spurs along the outer forearm edge
    fwd = Ax.T @ np.array([0, -1.0, 0])
    tx = 1.0 if fwd[0] > 0 else -1.0
    for u, ln in ((0.35, 0.3), (0.62, 0.36)):
        b0 = body.lpt(fa, [(-tx * 0.22, u * fl, 0.08)])[0]
        add(A.shard(b0, Ax @ np.array([-tx * 0.7, 0.35, 0.6]), ln, ln * 0.2, "BH_Horn", sides=4), fa)
    fist(body, s)


def fist(body, s):
    """A massive faceted glass fist rigid to hand.<s> (bone-local: y along the hand, z = back of the hand)."""
    add = body.add
    ha = "hand." + s
    Ax = body.axes(ha)
    o = body.head(ha)
    fwd = Ax.T @ np.array([0, -1.0, 0])
    tx = 1.0 if fwd[0] > 0 else -1.0
    a = o + Ax @ np.array([0, -0.02, -0.02])
    b = o + Ax @ np.array([0, 0.36, -0.02])
    add(fprism(a, b, [(0.2, 0.18), (0.25, 0.22), (0.26, 0.23), (0.2, 0.18)], n=6, up=tuple(Ax[:, 2])), ha)
    add(A.tube([o + Ax @ np.array([0, 0.03, -0.02]), o + Ax @ np.array([0, 0.09, -0.02])], 0.26, "BH_Bronze", n=6), ha)
    # shard knuckles on the striking face (distal), a thumb block
    for k, x in enumerate((-0.12, -0.04, 0.04, 0.12)):
        b0 = o + Ax @ np.array([x, 0.3, 0.06])
        add(A.shard(b0, Ax @ np.array([x * 0.8, 1.0, 0.25]), 0.2 + 0.04 * (k % 2), 0.055, "BH_Horn", sides=4), ha)
    add(fprism(o + Ax @ np.array([tx * 0.2, 0.08, -0.1]), o + Ax @ np.array([tx * 0.24, 0.26, -0.14]),
               [(0.07, 0.07), (0.08, 0.08), (0.05, 0.05)], n=5, up=tuple(Ax[:, 2])), ha)
    q = [o + Ax @ np.array([v[0], v[1], 0.21]) for v in ((-0.1, 0.12), (-0.02, 0.2), (0.04, 0.14), (0.12, 0.26))]
    addp(body, seam(q, Ax[:, 2], 0.016), ha)


def leg(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    th, sh, ft, toe = "thigh." + s, "shin." + s, "foot." + s, "toe." + s
    hip, k, a = body.head(th), body.head(sh), body.tail(sh)
    add(GK.blob(hip, 0.22, "BH_DarkSteel", n=8, rings=5), th)
    add(flimb(body, th, [(0.05, 0.22, 0.23), (0.5, 0.25, 0.26), (0.92, 0.21, 0.22)], n=7), th)
    add(GK.blob(k + (0, -0.02, 0), 0.2, "BH_DarkSteel", n=8, rings=5), sh)
    add(flimb(body, sh, [(0.08, 0.21, 0.22), (0.4, 0.25, 0.26), (0.85, 0.24, 0.25), (1.0, 0.21, 0.22)], n=7), sh)
    add(RG.joint_ring(k + (a - k) * 0.82, a - k, 0.27, w=0.08, mat="BH_Bronze"), sh)
    add(RG.joint_ring(hip + (k - hip) * 0.85, k - hip, 0.24, w=0.06, mat="BH_Bronze"), th)
    # knee pane + shard, seams down the shin and outer thigh
    V, F = M.prism(np.array([(-0.15, -0.12), (0.15, -0.12), (0.17, 0.08), (0.0, 0.18), (-0.17, 0.08)]), 0.09, axis="y")
    add(P(V, F, "BH_Stone", "knee").rot(Rx(-8)).move(k + (0, -0.22, 0.0)), sh)
    add(A.shard(k + (0, -0.2, 0.08), (0, -0.5, 1.0), 0.22, 0.05, "BH_Horn", sides=4), sh)
    q = jag(k + (0.02 * sx, -0.25, -0.16), a + (0.0, -0.25, 0.22), 5, 0.03, FRONT, 80 + (sx > 0))
    addp(body, seam(q, FRONT, 0.017, broken=(2,) if sx < 0 else ()), sh)
    q = jag(hip + (sx * 0.25, -0.02, -0.12), k + (sx * 0.24, -0.02, 0.18), 5, 0.03, np.array([sx, 0, 0.0]), 82 + sx)
    addp(body, seam(q, np.array([sx, 0, 0.0]), 0.017), th)
    # slab foot of glass with a copper toe band
    hx = body.p["hip_x"] * sx
    V, F = M.tube([(hx, 0.14, 0.09), (hx, -0.06, 0.1), (hx, -0.22, 0.08)], [(0.2, 0.09), (0.22, 0.1), (0.2, 0.08)],
                  n=6, up=(0, 0, 1), p=2.0)
    add(P(V, F, "BH_Stone", "foot"), ft)
    add(RG.slab((0.38, 0.08, 0.1), (hx, -0.22, 0.17), R=Rx(-30), mat="BH_Bronze", bev=0.01), ft)
    V, F = M.tube([(hx, -0.24, 0.07), (hx, -0.42, 0.05)], [(0.19, 0.07), (0.15, 0.04)], n=6, up=(0, 0, 1), p=2.0)
    add(P(V, F, "BH_Stone", "toe"), toe)
