"""Veinbound Knight (bh-029, Builder M4, Zarael / the Veinworks elite melee): a knight grown inside the sleeping
Gigas. Its armour is the giant's own bone: overlapping rib-like plates over raw dark sinew, bound together by
white-glowing wire veins (the Heartwire gone wrong) that lash the plates, coil round the forearms and shins and run
down the chest like stitches. Huge curved bone pauldrons with three hooked spurs each, a closed bone helm with a
jaw-bone face guard (a row of teeth under the glowing eye slit) and two horns sweeping back from the temples, a
ridge of small spurs over the crown. A long, tattered dark cloak (cape bones) torn into tongues. Right hand: a broad
greatsword of grey stone and bone - a stone slab blade with a bone spine, jaw-tooth serrations on both edges, a
glowing wire inlay in the fuller, a guard of two curved bone hooks and a vertebra pommel (rigid on weapon.R).

~2.0 m to the helm crown (K = 1.1 standard skeleton, broadened torso); the horns and pauldron spurs rise ~0.15 m
higher. Glow rule (bh-029): every glow is pure white BH_Emissive. Clips: gs_1 gs_2 gs_heavy war_cry (+ boss_slam,
cast_heavy as extras). Built on the knight plate kit through enemy_hollow_soldier.Scaled (frost_revenant pattern)."""
import math
import numpy as np

import bh_mesh as M
import bh_weapons as WP
from bh_body import Body, torso_loft, front_y, back_y, dome, fist, smoothstep, interp_rows, M_align_z
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
import char_knight as KN
from char_knight import TORSO, rows_between, thick_band, arc_band
import enemy_hollow_soldier as HS
from enemy_hollow_soldier import P, rtube, ball, Scaled, add_weapon, ragged
import enemy_boss_warden as BW
import enemy_bandit_cutthroat as K
import enemy_glyphbound_warrior as Z
import kit_a_common as A

KS = 1.1
PROPS = proportions(KS)
EXTRA_BONES = [(n, tuple(np.array(h) * KS), tuple(np.array(t) * KS), par, z) for (n, h, t, par, z) in KN.CAPE_BONES]
PALETTE = "vein_knight"
PALETTE_COLORS = {
    "BH_Bone": ((0.44, 0.4, 0.32), 0.0, 0.55, None, 0.0, 1.0),               # giant's bone plates (ivory-grey)
    "BH_Horn": ((0.22, 0.19, 0.15), 0.0, 0.6, None, 0.0, 1.0),                # older, darker bone (spurs, horns)
    "BH_Flesh": ((0.13, 0.04, 0.045), 0.0, 0.45, None, 0.0, 1.0),           # raw dark sinew under the plates
    "BH_Stone": ((0.2, 0.2, 0.21), 0.0, 0.8, None, 0.0, 1.0),               # grey stone of the blade
    "BH_Bronze": ((0.3, 0.17, 0.08), 0.9, 0.5, None, 0.0, 1.0),             # dark copper wire / clasps
    "BH_Cloth_Primary": ((0.045, 0.035, 0.04), 0.0, 0.92, None, 0.0, 1.0),  # tattered dark cloak / tassets
    "BH_Leather": ((0.06, 0.035, 0.03), 0.0, 0.7, None, 0.0, 1.0),          # sinew-leather belt / grip
    "BH_Shadow": ((0.012, 0.01, 0.012), 0.0, 0.85, None, 0.0, 1.0),          # helm interior / grooves
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),   # white wire veins, eyes
}
CLIPS = ["gs_1", "gs_2", "gs_heavy", "war_cry", "boss_slam", "cast_heavy"]
PREVIEW_HEIGHT = 2.45

GLOW = "BH_Emissive"
TB = [(r[0], r[1] * 1.1 + 0.01, r[2] * 1.08 + 0.008, r[3] * 1.1 + 0.01, r[4]) for r in TORSO]
CHEST_W = KN.chest_spine_w(1.24, 1.30)
TORSO_W = K.zspec_w([(0.99, "hips"), (1.10, "spine"), (1.22, "spine"), (1.32, "chest")])


def finish_mesh(mesh_ob):
    HS.enable_weapon_deform(mesh_ob)


secondary = BW.secondary


def remat(parts, table):
    for p in parts:
        p.mat = table.get(p.mat, p.mat)
    return parts


TR = {"BH_Steel": "BH_Bone", "BH_Gold": "BH_Bronze", "BH_Aether": GLOW, "BH_Rust": "BH_Horn",
      "BH_DarkSteel": "BH_Horn"}


# ------------------------------------------------------------------------------------------------ small kit
def horn(base, d0, d1, length, r0, mat="BH_Horn", n=6, k=7, r1=0.002):
    """Curved tapering bone horn / spur: the direction turns from d0 (at the base) to d1 (at the tip)."""
    d0, d1 = normalize(d0), normalize(d1)
    pts = [np.asarray(base, float)]
    for i in range(1, k):
        t = i / (k - 1)
        d = normalize(d0 * (1 - t) + d1 * t)
        pts.append(pts[-1] + d * length / (k - 1))
    rr = [r0 * (1 - t) ** 0.8 + r1 for t in np.linspace(0, 1, k)]
    return A.tube(pts, rr, mat, n=n, name="horn")


def vein(pts, r=0.0065):
    """A glowing wire vein lying on a surface (white), with a thin dark copper wire twisted alongside."""
    pts = np.asarray(pts, float)
    return [A.tube(pts, r, GLOW, n=5, name="vein")]


def lashing(c, axis, r, turns=2.5, wire=0.005):
    """A short coil of glowing wire lashing something round axis at c (radius r)."""
    a = normalize(axis)
    L = wire * 2.6 * turns
    return Z.coil(np.asarray(c) - a * L / 2, np.asarray(c) + a * L / 2, r, turns, wire, GLOW, n=4, pts_per_turn=6)


def rib_lame(z, h, g, a0, a1, mat="BH_Bone", thick=0.012, n=14, bow=0.0):
    """One curved bone plate following the torso rows (front arc a0..a1), slightly thicker in the middle."""
    V, F = arc_band(TB, z, z + h, g, a0, a1, n=n)
    p = P(V, F, mat, "lame")
    if bow:
        p.warp(lambda v: (v[0], v[1] - bow * max(0.0, 1 - abs(v[0]) / 0.2), v[2]))
    return M.solidify(p, thick, offset=1.0)


# ------------------------------------------------------------------------------------------------ weapon
def bone_greatsword():
    """Broad greatsword of grey stone and bone (weapon space: grip at origin, +Z blade, flats +-Y): a stone slab
    blade, a raised bone spine down both flats, jaw-tooth bone serrations along both edges, a glowing white wire
    inlay in the fuller, two curved bone hooks for a guard, a sinew-wrapped grip and a vertebra pommel."""
    parts = []
    z0, z1 = 0.14, 1.34
    parts.append(WP._blade(z0, z1, 0.17, 0.13, 0.016, tip=0.24, n_sec=12, fuller=False, mat="BH_Stone"))
    # bone spine over both flats (raised ridge) and the glowing inlay beside it
    for sy in (1, -1):
        pts = [(0.0, sy * 0.012, z) for z in np.linspace(z0 + 0.02, z1 - 0.3, 6)]
        parts.append(A.tube(pts, [(0.018, 0.008)] * 6, "BH_Bone", n=6, up=(0, sy, 0)))
        for sx in (1, -1):
            pv = [(sx * 0.036, sy * 0.0105, z) for z in np.linspace(z0 + 0.08, z1 - 0.34, 5)]
            parts.append(A.tube(pv, 0.0055, GLOW, n=5))
    # serrated bone teeth along both edges (like a jaw), set in a darker bone strip
    for sx in (1, -1):
        zs = np.linspace(z0 + 0.1, z1 - 0.3, 11)
        edge = []
        for z in zs:
            u = (z - z0) / (z1 - 0.24 - z0)
            hw = (0.17 + (0.13 - 0.17) * u) / 2
            edge.append((sx * (hw - 0.006), 0.0, z))
        parts.append(A.tube(edge, [(0.012, 0.012)] * len(edge), "BH_Horn", n=5, up=(0, 1, 0)))
        for i, q in enumerate(edge):
            d = normalize(np.array([sx * 1.0, 0.0, 0.55]))
            ln = 0.045 + 0.012 * (i % 2)
            t = A.shard(np.array(q) + (sx * 0.004, 0, 0), d, ln, 0.017, "BH_Bone", sides=4, up=(0, 1, 0), mid=0.25)
            t.V[:, 1] = t.V[:, 1] * 0.5
            parts.append(t)
    # guard: two curved bone hooks + a bone collar with a wire lashing
    for sx in (1, -1):
        parts.append(horn((sx * 0.03, 0, 0.13), (sx, 0, 0.15), (sx * 0.4, 0, 1.0), 0.2, 0.026, mat="BH_Bone", n=6))
    V, F = M.box(0.13, 0.05, 0.07, center=(0, 0, 0.125))
    parts.append(M.bevel(P(V, F, "BH_Horn", "collar"), 0.01, 1))
    parts.append(lashing((0, 0, 0.125), (1, 0, 0), 0.034, turns=3.0, wire=0.0055))
    # grip: sinew wrap, a dark copper ferrule, vertebra pommel with its processes
    parts.append(WP._grip(-0.34, 0.09, 0.02, 9, mat="BH_Leather"))
    V, F = M.lathe([(0.0, -0.36), (0.034, -0.36), (0.042, -0.39), (0.036, -0.42), (0.0, -0.425)], 10)
    parts.append(P(V, F, "BH_Bone", "pommel"))
    for a in (0, 120, 240):
        d = np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), -0.4])
        parts.append(horn((0, 0, -0.39), d, d + (0, 0, -0.3), 0.06, 0.012, mat="BH_Bone", n=5, k=4))
    V, F = M.lathe([(0.0, -0.355), (0.025, -0.355), (0.025, -0.34), (0.0, -0.34)], 10)
    parts.append(P(V, F, "BH_Bronze", "ferrule"))
    return parts


# ------------------------------------------------------------------------------------------------ pieces
def helm(body, add):
    """The knight's great helm re-made in bone: horns from the temples, a spur ridge over the crown, a jaw-bone
    face guard with a row of teeth under the glowing slit."""
    hp = [p for p in KN.helm(body) if p.name not in ("crest", "crest_base", "cross", "breath")]
    for p in remat(hp, TR):
        add(p, "head")
    for sx in (1, -1):
        add(ball((sx * 0.037, -0.128, 1.706), 0.018, GLOW, 6, 4, (1.7, 0.5, 0.72)), "head")
    V, F = torso_loft([(1.695, 0.112, 0.126, 0.1, 0.06, 0.008), (1.716, 0.112, 0.126, 0.1, 0.06, 0.008)], n=20, p=2.6)
    add(P(V, F, GLOW, "slit_glow"), "head")
    # jaw-bone face guard: a curved bone bar under the slit with teeth pointing up
    jaw = [(0.118 * math.sin(a), -0.128 * math.cos(a) + 0.008, 1.672 - 0.02 * abs(a)) for a in np.linspace(-1.1, 1.1, 9)]
    add(A.tube(jaw, [(0.014, 0.012)] * 9, "BH_Horn", n=6), "head")
    for a in np.linspace(-0.85, 0.85, 7):
        b = np.array([0.122 * math.sin(a), -0.133 * math.cos(a) + 0.008, 1.68 - 0.02 * abs(a)])
        add(A.taper([b, b + (0, -0.004, 0.028)], 0.0085, 0.0015, "BH_Bone", n=5), "head")
    # vertical bone nasal ridge
    add(A.tube([(0, -0.137, 1.73), (0, -0.142, 1.77), (0, -0.13, 1.815)], [(0.016, 0.008)] * 3, "BH_Bone", n=6,
               up=(0, -1, 0)), "head")
    # horns sweeping back from the temples
    for sx in (1, -1):
        add(horn((sx * 0.105, -0.03, 1.79), (sx * 0.75, 0.35, 0.45), (sx * 0.15, 1.0, -0.2), 0.4, 0.034, n=7, k=8),
            "head")
        add(lashing((sx * 0.112, -0.025, 1.79), (sx * 0.8, 0.1, 0.6), 0.036, turns=2.0, wire=0.0048), "head")
    # spur ridge over the crown
    for i, (y, h) in enumerate(((-0.08, 0.07), (-0.03, 0.09), (0.02, 0.1), (0.07, 0.085), (0.11, 0.06))):
        zb = 1.84 - 0.18 * max(0.0, y) ** 2 * 8
        add(horn((0, y, zb - 0.01), (0, 0.15, 1.0), (0, 0.8, 0.6), h, 0.016, n=5, k=4), "head")


def pauldron(body, am, s="L"):
    ua = "upper_arm." + s
    pd = remat([q for q in KN.pauldron(body, s) if q.name not in ("pauldron_rim", "pauldron_aether")], TR)
    sh = body.head(ua)
    for prt in pd:
        prt.scale((1.45, 1.35, 1.2), center=sh + np.array([-0.03, 0.0, 0.0]))
        am(prt, ua)
    # extra overlapping bone plate on top (scapula-like) + three hooked spurs + glowing lashings
    V, F = dome(sh + (0.02, 0.0, 0.06), (0.55, 0.0, 1.0), 0.16, a_max=55, n=14, rings=4, scale=(1.0, 1.15, 1.0))
    am(M.solidify(P(V, F, "BH_Bone", "scapula"), 0.012, offset=-1), ua)
    for k, (dy, ln, tilt) in enumerate(((-0.08, 0.17, -0.25), (0.0, 0.24, 0.0), (0.08, 0.18, 0.3))):
        b = sh + np.array([0.09, dy, 0.17 - 0.02 * abs(k - 1)])
        am(horn(b, (0.5, tilt, 1.0), (0.1, tilt + 0.9, 0.45), ln, 0.028, n=7, k=6), ua)
    for dy in (-0.1, 0.1):
        c = sh + np.array([0.13, dy, 0.08])
        am(lashing(c, (0, 1, 0.2), 0.03, turns=2.0, wire=0.005), ua)
    # vein over the plate
    pts = [sh + np.array([0.02 + 0.05 * t, -0.13 + 0.26 * t, 0.2 - 0.06 * abs(t - 0.5)]) for t in np.linspace(0, 1, 6)]
    for prt in vein(pts, 0.0065):
        am(prt, ua)


def cloak():
    """One wide dark cloak from the shoulders, torn into long tongues at the hem."""
    nu, nv = 12, 13

    def fn(u, v):
        half = 0.25 + 0.12 * v
        x = (u - 0.5) * 2 * half
        zb = 0.24 + ragged(u, 2.1, 0.34, 6)
        z = 1.47 + (zb - 1.47) * v
        if v < 0.2:
            yb = back_y(TB, x * 0.95, min(max(z, 1.3), 1.47)) + 0.05
        else:
            yb = back_y(TB, x * 0.95, 1.3) + 0.05
        y = yb + 0.08 * v ** 1.2 + 0.024 * math.sin(u * math.pi * 6.0) * v
        y -= 0.06 * (abs(u - 0.5) * 2) ** 3 * (1 - v) ** 2
        return (x, y, z)
    V, F = M.grid(fn, nu, nv)
    return M.solidify(P(V, F, "BH_Cloth_Primary", "cloak"), 0.013, offset=1.0), fn


# ------------------------------------------------------------------------------------------------ build
def build(real: Body):
    body = Scaled(real, KS, EXTRA_BONES)
    add = body.add
    # ---- sinew body under everything
    V, F = torso_loft(rows_between(TB, 0.96, 1.53, scale=0.97, n_extra=3), n=26, cap1=True)
    add(P(V, F, "BH_Flesh", "sinew"), weights=TORSO_W)
    # sinew cords (raised muscle bands) visible between the plates
    for sx in (1, -1):
        pts = [(sx * x, front_y(TB, sx * x, z) * 0.97 - 0.004, z) for x, z in ((0.05, 1.46), (0.1, 1.33), (0.12, 1.18),
                                                                             (0.09, 1.04))]
        add(A.tube(pts, 0.014, "BH_Flesh", n=6), weights=TORSO_W)
    # ---- chest: overlapping rib plates, sternum keel, a breast plate at the top
    V, F = torso_loft(rows_between(TB, 1.4, 1.53, extra=0.006, n_extra=1), n=28, cap1=False)
    add(M.bevel(P(V, F, "BH_Bone", "yoke"), 0.004, 1, angle=50), weights=CHEST_W)
    for i, z in enumerate((1.355, 1.3, 1.245)):
        add(rib_lame(z, 0.04, 0.014 + 0.004 * i, -0.36, 0.36, bow=0.006), weights=CHEST_W)
    for i, z in enumerate((1.185, 1.13, 1.075)):
        add(rib_lame(z, 0.04, 0.012 + 0.003 * i, -0.3, 0.3, thick=0.011), weights=TORSO_W)
    # white light burning in the sinew gaps between the plates
    for z, a, w in ((1.398, 0.3, CHEST_W), (1.345, 0.32, CHEST_W), (1.29, 0.32, CHEST_W), (1.237, 0.3, TORSO_W),
                    (1.175, 0.26, TORSO_W), (1.12, 0.26, TORSO_W)):
        ring = K.ring_frac(TB, z, 0.004, np.linspace(-a, a, 13) % 1.0)
        add(A.tube(ring, (0.0065, 0.0065), GLOW, n=4), weights=w)
    zk = np.linspace(1.08, 1.47, 8)
    keel = [(0.0, front_y(TB, 0, z) - 0.03, z) for z in zk]
    add(A.tube(keel, [(0.028, 0.016)] * 8, "BH_Bone", n=6, up=(0, -1, 0)), weights=TORSO_W)
    # back: rib plates round the back under the cloak + spinous processes at the neck
    for z in (1.28, 1.36):
        add(rib_lame(z, 0.05, 0.016, 0.3, 0.7), weights=CHEST_W)
    for i, z in enumerate((1.47, 1.43, 1.39)):
        add(horn((0, back_y(TB, 0, z) + 0.01, z), (0, 1, 0.3), (0, 0.6, 0.9), 0.07 - 0.01 * i, 0.016, n=5, k=4),
            "chest")
    # ---- the white wire veins binding the plates
    for sx in (1, -1):
        pts = []
        for i, z in enumerate(np.linspace(1.47, 1.07, 10)):
            x = sx * (0.085 + 0.02 * (i % 2))
            pts.append((x, front_y(TB, x, z) - 0.042 - 0.006 * (z < 1.22), z))
        for prt in vein(pts, 0.0075):
            add(prt, weights=TORSO_W)
        for z in (1.38, 1.28, 1.16):
            x = sx * 0.095
            c = np.array([x, front_y(TB, x, z) - 0.035, z])
            add(lashing(c, (0, 0, 1), 0.016, turns=2.0, wire=0.0045), weights=TORSO_W)
        # side branches toward the arms
        br = [(sx * 0.1, front_y(TB, sx * 0.1, 1.42) - 0.04, 1.42), (sx * 0.16, front_y(TB, sx * 0.16, 1.44) - 0.03, 1.44),
              (sx * 0.2, front_y(TB, sx * 0.2, 1.46) * 0.6, 1.47)]
        for prt in vein(br, 0.006):
            add(prt, weights=CHEST_W)
    # core knot of glowing wire over the heart, set in the sternum
    zc = 1.33
    c = np.array([0.0, front_y(TB, 0, zc) - 0.045, zc])
    add(ball(c, 0.03, GLOW, 8, 5, (1.0, 0.6, 1.0)), "chest")
    add(lashing(c, (0, 0, 1), 0.034, turns=2.5, wire=0.006), "chest")
    # gorget: dark bone collar
    prof = [(0.17, 1.45), (0.145, 1.49), (0.104, 1.527), (0.088, 1.57), (0.076, 1.57), (0.092, 1.527),
            (0.135, 1.49), (0.16, 1.45), (0.17, 1.45)]
    V, F = M.lathe(prof, 18)
    add(P(V, F, "BH_Horn", "gorget").scale((1.0, 0.85, 1.0)), "chest")
    # ---- belt, faulds, tassets
    V, F = thick_band(TB, 1.02, 1.065, 0.03, 0.01, n=26)
    add(P(V, F, "BH_Leather", "belt"), "hips")
    by = front_y(TB, 0, 1.042) - 0.035
    V, F = M.lathe([(0.0, -0.02), (0.04, -0.02), (0.045, 0.0), (0.04, 0.02), (0.0, 0.02)], 10)
    add(P(V, F, "BH_Bone", "buckle").rot(Rx(90)).move((0, by, 1.042)), "hips")
    for sd in (-1, 1):
        add(horn((sd * 0.045, by - 0.01, 1.042), (sd, -0.3, 0), (sd, 0.2, -0.3), 0.05, 0.012, mat="BH_Bone", n=5,
                 k=4), "hips")
    for side_a in ((0.12, 0.38), (0.62, 0.88)):
        for i in range(3):
            z1 = 1.025 - 0.06 * i
            V, F = arc_band(TB, z1 - 0.075, z1, 0.035 + 0.022 * i, side_a[0], side_a[1], n=10)
            lame = P(V, F, "BH_Bone", "fauld")
            lame.warp(lambda v, z1=z1: (v[0] * (1 + 0.3 * (z1 - v[2])), v[1] * (1 + 0.3 * (z1 - v[2])), v[2]))
            add(M.solidify(lame, 0.009, offset=1.0), weights=body.skirt_weights(1.0, 0.8, max_leg=0.35, center_w=0.05))
    V, F = torso_loft([(0.97, 0.175, 0.122, 0.118, 0.0), (0.86, 0.19, 0.128, 0.125, 0.0),
                       (0.76, 0.198, 0.13, 0.128, 0.0)], n=24)
    add(P(V, F, "BH_Flesh", "underskirt"), weights=body.skirt_weights(0.98, 0.74, max_leg=0.8))
    for front in (True, False):
        add(HS.cloth_panel(TB, 1.03, 0.47, lambda z: 0.11 + 0.035 * (1.03 - z), front=front, nu=7, nv=9,
                           seed=1.7 if front else 3.3, rag=0.2, teeth=3, gap=0.03, belt_z=1.03),
            weights=HS.cloth_w(belt_z=1.03, leg=0.5))
    # ---- legs (left authored, mirrored)
    am = body.add_mirror
    s = "L"
    th, sh = "thigh." + s, "shin." + s
    am(body.limb(th, [(-0.02, 0.092, 0.097), (0.4, 0.088, 0.092), (0.95, 0.068, 0.072)], "BH_Flesh", n=12, p=2.2), th)
    am(M.bevel(body.limb(th, [(0.05, 0.1, 0.104), (0.45, 0.098, 0.1), (0.9, 0.078, 0.082)], "BH_Bone", n=12, p=2.6),
               0.003, 1, angle=50), th)
    k = body.head(sh)
    hp = body.head(th)
    pt = [hp + (k - hp) * u + np.array([0.06 * math.sin(u * 5), -0.1 + 0.02 * u, 0.0]) for u in (0.15, 0.35, 0.55, 0.8)]
    for prt in vein(pt, 0.0065):
        am(prt, th)
    V, F = dome(k + (0, -0.05, 0.0), (0, -1, 0.15), 0.074, a_max=78, n=12, rings=4)
    am(M.solidify(P(V, F, "BH_Bone", "kneecap"), 0.01, offset=-1),
       weights=lambda V, th=th, sh=sh: [{th: 0.5, sh: 0.5}] * len(V))
    am(horn(k + (0, -0.11, 0.02), (0, -1, 0.3), (0, -0.4, 1.0), 0.08, 0.018, n=6, k=5),
       weights=lambda V, th=th, sh=sh: [{th: 0.4, sh: 0.6}] * len(V))
    am(M.bevel(body.limb(sh, [(0.03, 0.072, 0.075), (0.3, 0.079, 0.084), (0.85, 0.058, 0.06), (1.0, 0.062, 0.064)],
                         "BH_Bone", n=12, p=2.4), 0.003, 1, angle=50), sh)
    a = body.tail(sh)
    am(lashing(k + (a - k) * 0.35, a - k, 0.086, turns=3.0, wire=0.005), sh)
    am(lashing(k + (a - k) * 0.75, a - k, 0.068, turns=2.0, wire=0.005), sh)
    pv = [k + (a - k) * u + np.array([0.0, -0.083 + 0.02 * u, 0.0]) for u in (0.15, 0.4, 0.62)]
    for prt in vein(pv, 0.006):
        am(prt, sh)
    for part, bone in KN.sabaton(body, s):
        part.scale((1.1, 1.08, 1.1), center=(body.head(th)[0], 0, 0))
        am(remat([part], TR)[0], bone)
    # ---- arms
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    am(body.limb(ua, [(0.0, 0.07, 0.072), (0.5, 0.068, 0.07), (1.0, 0.058, 0.06)], "BH_Flesh", n=12, p=2.2), ua)
    am(body.limb(ua, [(0.35, 0.075, 0.077), (0.95, 0.064, 0.066)], "BH_Bone", n=12, p=2.4), ua)
    el = body.head(fa)
    V, F = dome(el + (0.0, 0.035, 0.0), (0, 1, 0.1), 0.066, a_max=80, n=12, rings=4)
    am(M.solidify(P(V, F, "BH_Bone", "couter"), 0.008, offset=-1),
       weights=lambda V, ua=ua, fa=fa: [{ua: 0.5, fa: 0.5}] * len(V))
    am(horn(el + (0, 0.09, 0.0), (0, 1, -0.2), (0.0, 0.6, -0.9), 0.09, 0.018, n=6, k=5),
       weights=lambda V, ua=ua, fa=fa: [{ua: 0.3, fa: 0.7}] * len(V))
    am(body.limb(fa, [(0.08, 0.062, 0.064), (0.5, 0.062, 0.064), (0.93, 0.054, 0.056)], "BH_Bone", n=12, p=2.6), fa)
    wr = body.head(ha)
    for u, tw in ((0.3, 2.5), (0.72, 3.0)):
        am(lashing(el + (wr - el) * u, wr - el, 0.069 - 0.008 * u, turns=tw, wire=0.0052), fa)
    L = body.p["fore_len"]
    am(A.tube(body.lpt(fa, [(0.0, u * L, 0.064) for u in (0.12, 0.5, 0.9)]), 0.006, GLOW, n=5), fa)
    cuff = body.limb(fa, [(0.82, 0.058, 0.06), (1.0, 0.074, 0.074), (1.08, 0.078, 0.076)], "BH_Horn", n=12,
                     cap0=False, cap1=False)
    am(M.solidify(cuff, 0.006, offset=1.0), ha)
    for prt in fist(body, s, "BH_Bone", "BH_Flesh", scale=1.15):
        am(prt, ha)
    pauldron(body, am, s)
    # ---- helm
    helm(body, add)
    # ---- cloak
    cl, cfn = cloak()
    add(cl, weights=KN.cape_w())
    # a few wire veins grown into the cloak's shoulders (the cloak is part of it now)
    for u in (0.3, 0.7):
        pts = [np.array(cfn(u + 0.03 * math.sin(v * 7), v)) + (0, 0.016, 0) for v in np.linspace(0.02, 0.32, 5)]
        add(A.tube(pts, [0.006, 0.0055, 0.005, 0.004, 0.002], GLOW, n=4), weights=KN.cape_w())
    # ---- weapon
    add_weapon(body, "R", bone_greatsword())
