"""Obsidian Shardcaster (bh-029, Builder M6, Zarael / the Obsidian Engine ranged): a lean Engine-watcher who flings
knapped black glass. A coat of obsidian scale armour - row on row of small lozenge scales of glossy black glass
edged in copper - over a deep-red quilted under-tunic; a scale skirt in long split strips to the knee; a dark teal
hood with a crest of three tall glass shards rising from its back (the silhouette key from the gameplay camera); a
smooth black glass face-mask with two white eye-slits and a white glyph line down the brow. A bandolier from the left
shoulder to the right hip holds a row of black shards point-up in copper loops; more shards in a quiver-sheaf at the
right hip. Leather sleeves under obsidian plate bracers; a short obsidian blade lashed along the outside of the right
forearm (the dagger_1 cut). Every glow is pure white (bh-029).

Right hand (weapon.R): the glass sling - two cords strung with obsidian and copper beads hanging from the fist to a
leather cradle holding a big knapped shard with a white glyph burning in it. Left hand (weapon.L): a jagged shard
held ready, point forward.

~1.88 m (shard crest ~2.15 m). Authored in the standard 1.8 m space with the bandit kit (SB), scaled.
Clips: cast_area cast_weapon dagger_1 wand_1 (wand_1 / cast_weapon = sling casts; the game spawns the shards)."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
from bh_body import M_align_z
import enemy_bandit_cutthroat as K
from enemy_bandit_cutthroat import SB, zspec_w, grow_rows, ring_frac, strip
import enemy_ashen_cultist as C
import enemy_glyphbound_warrior as Z
import kit_a_common as A
import kit_ember as E

SCALE = 1.88 / 1.818
PROPS = proportions(SCALE, hip_x=0.096 * SCALE, shoulder_x=0.184 * SCALE, clav_x0=0.034 * SCALE)
PREVIEW_HEIGHT = 2.5
PALETTE = "shardcaster"
PALETTE_COLORS = {
    "BH_Stone": ((0.045, 0.045, 0.055), 0.25, 0.1, None, 0.0, 1.0),      # obsidian scales / mask (glossy)
    "BH_Horn": ((0.06, 0.052, 0.08), 0.3, 0.06, None, 0.0, 1.0),         # loose shards (smoky black glass)
    "BH_Cloth_Primary": ((0.27, 0.05, 0.035), 0.0, 0.92, None, 0.0, 1.0),  # deep-red quilted under-tunic
    "BH_Cloth_Secondary": ((0.035, 0.11, 0.105), 0.0, 0.9, None, 0.0, 1.0),  # dark teal hood
    "BH_Leather": ((0.13, 0.075, 0.04), 0.0, 0.7, None, 0.0, 1.0),       # sleeves, sling cradle, boots
    "BH_Bronze": ((0.52, 0.26, 0.12), 1.0, 0.4, None, 0.0, 1.0),          # copper scale edging, loops, beads
    "BH_Skin": ((0.3, 0.19, 0.13), 0.0, 0.55, None, 0.0, 1.0),
    "BH_Ichor": ((0.05, 0.045, 0.04), 0.0, 0.9, None, 0.0, 1.0),           # dark trousers
    "BH_Shadow": ((0.015, 0.013, 0.013), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),  # eyes, glyphs: white
}
CLIPS = ["cast_area", "cast_weapon", "dagger_1", "wand_1"]

TORSO = [  # standard space: lean, narrow-waisted
    (0.96, 0.142, 0.096, 0.096, 0.0),
    (1.04, 0.134, 0.094, 0.09, 0.02),
    (1.14, 0.138, 0.1, 0.092, 0.05),
    (1.25, 0.152, 0.11, 0.096, 0.08),
    (1.35, 0.162, 0.112, 0.1, 0.06),
    (1.43, 0.162, 0.106, 0.1, 0.03),
    (1.49, 0.136, 0.088, 0.088, 0.0),
    (1.53, 0.078, 0.062, 0.062, 0.0),
]
TW = zspec_w([(0.99, "hips"), (1.10, "spine"), (1.22, "spine"), (1.32, "chest")])
P = Z.P
G = 0.02           # scale-coat offset over the body


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


def tp(f, z, g=0.0, rows=TORSO):
    return E.torso_point(rows, f % 1.0, z, g, 2.3)


def scale_plate(c, nrm, up, w=0.046, h=0.056, t=0.007, tilt=14.0, mat="BH_Stone"):
    """One lozenge scale lying on a surface (normal nrm), its lower point tipped outward by `tilt` degrees."""
    n = normalize(nrm)
    u = normalize(np.asarray(up, float) - n * np.dot(up, n))
    side = np.cross(u, n)
    o = np.array([(0.0, -h * 0.62), (w / 2, 0.0), (0.0, h * 0.38), (-w / 2, 0.0)])
    V, F = M.prism(o, t, axis="z")
    # local x -> side, y -> up, z -> normal; tip the lower half outward
    Vn = []
    for x, y, z in V:
        lift = max(0.0, -y) * math.tan(math.radians(tilt))
        Vn.append(np.asarray(c, float) + side * x + u * y + n * (z + lift))
    return P(np.array(Vn), F, mat, "scale")


def build(body):
    sb = SB(body, SCALE)
    V, F = torso_loft(TORSO, n=24, p=2.3, cap1=True)
    sb.add(P(V, F, "BH_Cloth_Primary", "tunic"), weights=TW)
    scale_coat(sb)
    scale_skirt(sb)
    bandolier(sb)
    head(sb)
    for s in ("L", "R"):
        arm(sb, s)
    K.pelvis_seat(sb, "BH_Cloth_Primary", g=0.012)
    K.trousers(sb, "BH_Ichor", loose=0.98)
    K.boots(sb, "BH_Leather", "BH_Shadow", shaft_top=0.62, cuff=False, wraps="BH_Bronze")
    K.belt(sb, TORSO, z=0.99, h=0.05, g=G + 0.012, mat="BH_Leather", buckle="BH_Bronze")
    hip_sheaf(sb)
    K.add_weapon(sb, "R", glass_sling())
    K.add_weapon(sb, "L", held_shard())


def scale_coat(sb):
    """Rows of overlapping obsidian scales over the torso (front open a hand's width at the throat), copper-edged
    collar and hem."""
    rows = []
    zs = np.arange(1.02, 1.47, 0.042)
    for i, z in enumerate(zs):
        r = TORSO[0]
        circ = 2 * math.pi * 0.16
        n = 24
        off = 0.5 / n if i % 2 else 0.0
        for k in range(n):
            f = k / n + off
            if z > 1.4 and min(f % 1.0, 1 - f % 1.0) < 0.06:     # open at the throat
                continue
            q, nn = tp(f, z, G + 0.004 * (i % 2))
            sb.add(scale_plate(q, nn, (0, 0, 1)), weights=TW)
    # obsidian gorget at the throat opening, a stepped white glyph burning in it
    q, n = tp(0.0, 1.43, G + 0.012)
    V, F = M.lathe([(0.0, -0.006), (0.05, -0.006), (0.056, 0.0), (0.05, 0.007), (0.0, 0.009)], 12)
    sb.add(P(V, F, "BH_Stone", "gorget").rot(Rx(90)).move(q), "chest")
    V, F = M.tube([q + (0.058 * math.cos(a), 0, 0.058 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 13)],
                  [(0.006, 0.006)] * 13, n=4, up=(0, -1, 0), cap0=False, cap1=False)
    sb.add(P(V, F, "BH_Bronze", "gorgetrim"), "chest")
    gl = [q + (x, -0.012, z) for x, z in ((-0.03, -0.02), (-0.03, 0.01), (-0.01, 0.01), (-0.01, -0.01), (0.01, -0.01),
                                          (0.01, 0.025), (0.03, 0.025))]
    for prt in Z.channel(gl, (0, -1, 0), r=0.0045):
        sb.add(prt, "chest")
    # copper-edged collar band and hem band
    for z0, z1 in ((1.47, 1.5), (0.99, 1.02)):
        V, F = K.band(TORSO, z0, z1, G + 0.016, G - 0.004, n=28)
        sb.add(P(V, F, "BH_Bronze", "coatband"), weights=TW)


def scale_skirt(sb):
    """Long split strips of scales hanging from the belt to the knee (front, back, sides): each strip a column of
    scales on a leather backing, weighted like a skirt so the legs move."""
    wside = sb.skirt(1.0, 0.5, max_leg=0.8, center_w=0.06)
    for frac in (0.04, -0.04, 0.16, -0.16, 0.3, -0.3, 0.44, -0.44, 0.5):
        q0, n0 = tp(frac, 0.98, G + 0.02)
        n0 = normalize(np.array([n0[0], n0[1], 0.0]))
        # strips near the centre line hang between the legs: share both thighs (no tearing down the middle)
        w = Z.centre_w(1.0, 0.5, 0.6) if abs(q0[0]) < 0.07 else wside
        pts = [q0 + n0 * (0.06 * (0.98 - z)) + (0, 0, z - 0.98) for z in np.linspace(0.98, 0.56, 6)]
        pts = [np.array([p[0], p[1], z]) for p, z in zip(pts, np.linspace(0.98, 0.56, 6))]
        sb.add(strip(pts, 0.07, 0.008, "BH_Leather", ups=[n0] * 6), weights=w)
        for k, z in enumerate(np.linspace(0.95, 0.6, 7)):
            c = q0 + n0 * (0.06 * (0.98 - z) + 0.008) + (0, 0, z - 0.98)
            c = np.array([c[0], c[1], z])
            sb.add(scale_plate(c, n0, (0, 0, 1), w=0.064, h=0.07, t=0.008, tilt=10), weights=w)
        tip = pts[-1] + n0 * 0.01 + (0, 0, -0.02)
        sb.add(scale_plate(tip, n0, (0, 0, 1), w=0.05, h=0.07, t=0.008, tilt=6, mat="BH_Bronze"), weights=w)


def bandolier(sb):
    """Strap from the left shoulder to the right hip with copper loops holding black shards point-up."""
    g = G + 0.03
    pts, ups = [], []
    for t in np.linspace(0, 1, 9):
        x = 0.11 - 0.25 * t
        z = 1.48 - 0.44 * t
        pts.append((x, front_y(TORSO, x, z) - g, z))
        ups.append((0.2 * x, -1, 0))
    sb.add(strip(pts, 0.045, 0.01, "BH_Leather", ups=ups), weights=TW)
    back = [(0.11 - 0.25 * t, back_y(TORSO, 0.11 - 0.25 * t, 1.48 - 0.44 * t) + g, 1.48 - 0.44 * t)
            for t in np.linspace(0, 1, 7)]
    sb.add(strip(back, 0.045, 0.01, "BH_Leather", ups=[(0, 1, 0)] * 7), weights=TW)
    over = []
    for t in np.linspace(0, 1, 7):
        a = math.pi * (0.5 - t) * 0.95
        over.append(((0.11, -0.11 * math.sin(a) + 0.005, 1.48 + 0.05 * math.cos(a)), (0, -math.sin(a), math.cos(a))))
    sb.add(strip([p for p, _ in over], 0.045, 0.01, "BH_Leather", ups=[u for _, u in over]), "chest")
    d = normalize(np.asarray(pts[0]) - np.asarray(pts[-1]))
    for k, t in enumerate((0.16, 0.3, 0.44, 0.58, 0.72)):
        i = t * (len(pts) - 1)
        i0 = int(i)
        c = np.asarray(pts[i0]) * (1 - (i - i0)) + np.asarray(pts[min(i0 + 1, len(pts) - 1)]) * (i - i0)
        V, F = M.tube([c + (0, -0.006, -0.012), c + (0, -0.006, 0.012)], [(0.02, 0.012)] * 2, n=6, up=(0, -1, 0))
        sb.add(P(V, F, "BH_Bronze", "loop"), weights=TW)
        sb.add(A.shard(c + (0, -0.016, -0.04), normalize(d + np.array([0.0, -0.05, 0.6])), 0.15 + 0.02 * (k % 2), 0.02,
                       "BH_Horn", sides=4), weights=TW)


def hip_sheaf(sb):
    """A short leather quiver at the right hip, a sheaf of long shards sticking out of it."""
    q, n = tp(0.7, 0.92, G + 0.05)
    a = q + (0, 0, -0.1)
    b = q + (0, 0.02, 0.12)
    V, F = M.tube([a, b], [(0.045, 0.035), (0.05, 0.04)], n=8, up=(1, 0, 0))
    w = sb.skirt(1.0, 0.75, max_leg=0.35, center_w=0.1)
    sb.add(P(V, F, "BH_Leather", "quiver"), weights=w)
    V, F = M.tube([b - (0, 0, 0.012), b + (0, 0, 0.012)], [(0.054, 0.044)] * 2, n=8, up=(1, 0, 0))
    sb.add(P(V, F, "BH_Bronze", "quiverrim"), weights=w)
    for k, (dx, dy, ln) in enumerate(((0.0, 0.0, 0.22), (0.02, 0.012, 0.18), (-0.018, -0.01, 0.2), (0.01, -0.02, 0.16))):
        sb.add(A.shard(b + (dx, dy, -0.05), (dx * 3, 0.15 + dy * 3, 1.0), ln, 0.018, "BH_Horn", sides=4), weights=w)


def head(sb):
    K.neck_and_head(sb, skin="BH_Skin", face=False)
    glass_mask(sb)
    C.hood(sb, "BH_Cloth_Secondary", trim="BH_Bronze")
    # crest: three tall glass shards rising from the back of the hood, a copper clasp at their root
    root = np.array([0.0, 0.07, 1.84])
    for (dx, ln, sd) in ((0.0, 0.32, 0), (0.42, 0.24, 1), (-0.42, 0.24, 2)):
        d = normalize(np.array([dx, 0.55, 1.0]))
        sb.add(A.shard(root + np.array([dx * 0.05, 0, -0.02]), d, ln, 0.034, "BH_Horn", sides=5, twist=sd * 20),
               "head")
    V, F = M.sphere(0.04, 8, 5, center=root + (0, 0.0, -0.035), scale=(1.4, 1.0, 0.8))
    sb.add(P(V, F, "BH_Bronze", "clasp"), "head")


def glass_mask(sb):
    """Smooth black glass face-mask, two white eye slits, a white glyph line down the brow."""
    def fn(u, v):
        x = (u - 0.5) * 0.14
        z = 1.6 + 0.16 * v
        ax = abs(x) / 0.085
        y = -0.08 - 0.012 * (1 - ax ** 2) + 0.022 * ax ** 2.2
        y -= 0.008 * math.sin(math.pi * v)
        return (x * (0.7 + 0.3 * v ** 0.5), y, z)
    V, F = M.grid(fn, 9, 8)
    sb.add(M.solidify(P(V, F, "BH_Stone", "mask"), 0.008, offset=-1.0), "head")
    for sx in (1, -1):
        a = np.array([sx * 0.012, -0.099, 1.702])
        b = np.array([sx * 0.05, -0.093, 1.712])
        sb.add(A.tube([a + (0, 0.004, 0), b + (0, 0.004, 0)], 0.008, "BH_Shadow", n=4), "head")
        sb.add(A.tube([a, b], 0.0048, "BH_Emissive", n=5), "head")
    for prt in Z.channel([(0, -0.1, 1.73), (0, -0.098, 1.755), (0.008, -0.094, 1.765), (0, -0.09, 1.775)], (0, -1, 0.2),
                         r=0.0035):
        sb.add(prt, "head")
    for prt in Z.channel([(-0.03, -0.098, 1.64), (0.0, -0.1, 1.632), (0.03, -0.098, 1.64)], (0, -1, 0), r=0.003):
        sb.add(prt, "head")


def arm(sb, s):
    sx = 1 if s == "L" else -1
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    K.bare_arm(sb, s, skin="BH_Leather", r_up=0.047, r_fore=0.041, r_wrist=0.031, bulk=1.05)
    K.add_fist(sb, s, "BH_Leather", "BH_Skin", gauntlet=True)
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    d = normalize(wr - el)
    # scale pauldron: three overlapping rows of scales capping the shoulder
    for i, (dz, rr) in enumerate(((0.06, 0.075), (0.02, 0.08), (-0.025, 0.082))):
        for k in range(7):
            a = math.radians(-70 + 140 * k / 6)
            nrm = normalize(np.array([sx * 0.55, math.sin(a) * 0.8, math.cos(a) * 0.6 + 0.4 - 0.25 * i]))
            c = sh + np.array([sx * 0.02, 0, dz]) + nrm * rr
            sb.add(scale_plate(c, nrm, (sx * 0.8, 0, 0.6), w=0.05, h=0.06, t=0.007),
                   weights=lambda V, s=s: [{"shoulder." + s: 0.4, "upper_arm." + s: 0.6}] * len(V))
    # obsidian plate bracer with a copper rim
    V, F = M.tube([el + (wr - el) * 0.35, el + (wr - el) * 0.95], [(0.052, 0.054), (0.044, 0.046)], n=6, up=(0, -1, 0),
                  p=2.0)
    sb.add(P(V, F, "BH_Stone", "bracer"), fa)
    for u in (0.35, 0.95):
        c = el + (wr - el) * u
        rr = 0.055 - 0.009 * (u > 0.5)
        V, F = M.tube([c - d * 0.006, c + d * 0.006], [(rr, rr + 0.002)] * 2, n=6, up=(0, -1, 0), p=2.0)
        sb.add(P(V, F, "BH_Bronze", "bracerrim"), fa)
    out0 = normalize(np.cross(d, (0, 1, 0))) * sx
    gl = [el + (wr - el) * u + out0 * 0.054 + (0, -0.012 * math.sin(u * 20), 0) for u in np.linspace(0.42, 0.88, 5)]
    for prt in Z.channel(gl, out0, r=0.0045):
        sb.add(prt, fa)
    if s == "R":
        # obsidian blade lashed along the outside of the forearm, point past the elbow
        out = normalize(np.cross(d, (0, 1, 0))) * sx
        base = el + (wr - el) * 0.85 + out * 0.055
        blade = A.shard(base, -d + out * 0.08, 0.36, 0.03, "BH_Horn", sides=4, up=tuple(out), mid=0.3)
        blade.V = blade.V + 0.0
        sb.add(blade, fa)
        for u in (0.45, 0.75):
            c = el + (wr - el) * u
            V, F = M.tube([c - d * 0.008, c + d * 0.008], [(0.062, 0.062)] * 2, n=8, up=(0, -1, 0))
            sb.add(P(V, F, "BH_Leather", "lash"), fa)


# ------------------------------------------------------------------------------------------------- weapons
def glass_sling(s=1.0):
    """Weapon space (weapon.R: grip at origin; distal / hanging = +X for the right hand, +Z = forward): two bead cords
    from the fist down to a leather cradle with a knapped shard in it, a white glyph burning in the shard."""
    parts = []
    L_ = 0.42
    cradle = np.array([L_, 0.0, 0.02])
    for sy in (1, -1):
        pts = [np.array([0.0, sy * 0.012, 0.0]), np.array([0.2, sy * 0.03, 0.01]), cradle + (-0.03, sy * 0.05, 0)]
        parts.append(A.tube(pts, 0.004, "BH_Leather", n=4))
        for prt in Z.beads(pts, 0.009, ("BH_Stone", "BH_Bronze", "BH_Stone"), n=5, rings=3, every=1.6):
            parts.append(prt)
    # cradle: a cupped leather pouch (flattened half-sphere) round the shard
    V, F = M.sphere(0.06, 10, 6, scale=(0.75, 1.0, 0.6))
    cup = P(V, F, "BH_Leather", "cradle")
    cup.V[:, 0] = np.maximum(cup.V[:, 0], -0.01)
    parts.append(cup.move(cradle))
    sh = A.shard(cradle + (-0.02, 0, -0.08), (0.15, 0, 1), 0.2, 0.04, "BH_Horn", sides=5)
    parts.append(sh)
    for prt in Z.channel([cradle + (-0.05, 0.0, 0.0), cradle + (-0.055, 0.0, 0.05), cradle + (-0.047, 0.0, 0.08)],
                         (-1, 0, 0), r=0.004):
        parts.append(prt)
    # wrist loop round the fist
    ring = [(0.03 * math.cos(a), 0.035 * math.sin(a), -0.02) for a in np.linspace(0, 2 * math.pi, 11)]
    parts.append(A.tube(ring, 0.005, "BH_Leather", n=4, cap=False))
    for p in parts:
        p.V = p.V * s
    return parts


def held_shard(s=1.0):
    """A jagged shard held in the left fist, point forward (+Z), a copper-wrapped grip."""
    parts = [A.shard((0, 0, -0.06), (0, 0, 1), 0.34, 0.032, "BH_Horn", sides=4, mid=0.25)]
    parts.append(Z.coil((0, 0, -0.05), (0, 0, 0.06), 0.03, 4, 0.004, "BH_Bronze", n=4, pts_per_turn=8))
    for p in parts:
        p.V = p.V * s
    return parts
