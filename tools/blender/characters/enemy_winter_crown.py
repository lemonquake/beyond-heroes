"""Skaldra, the Winter Crown (bh-012, Builder D, Rimeglass Barrow BOSS): a tall, slender undead queen. Pale ice-plate
cuirass, pauldrons and vambraces over a long frozen gown of deep ice-blue that ends in a train trailing on the floor
behind her; long bell sleeves with an ice-crust trim; a mantle of frost feathers over the shoulders with a high fan of
long feathers rising behind her head; a cracked porcelain-white mask face with two cold blue eye-lights (one crack
leaks light); a pale veil falling from the crown down her back; and a tall crown of long icicle spikes (the
tallest at the brow, glowing cores). Weapon: a long glaive with a silver haft and a curved blade of glowing blue ice
(rigid on weapon.R; spear clips).

Author height ~2.1 m to the top of the head (K = 1.16), crown spikes to ~2.45 m; the game scales it ~1.9x.
Readability keys at gameplay distance: the icicle crown (emissive cores), the feather fan, the long glowing glaive."""
import math
import numpy as np

import bh_mesh as M
import bh_weapons as WP
from bh_body import torso_loft, front_y, back_y, dome, fist, M_align_z, smoothstep, interp_rows
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
from char_knight import thick_band, arc_band
import enemy_bandit_cutthroat as KB
import enemy_ashen_cultist as AC
import enemy_hollow_soldier as HS
from enemy_hollow_soldier import P, rtube, ball, Scaled, add_weapon, ragged, cloth_w
import enemy_rime_husk as RH
import kit_a_common as A

K = 1.16
PROPS = proportions(K)
PALETTE = "winter_crown"
PALETTE_COLORS = {
    "BH_Steel": ((0.7, 0.8, 0.88), 0.7, 0.28, None, 0.0, 1.0),             # pale ice-plate, silver haft
    "BH_DarkSteel": ((0.2, 0.25, 0.32), 0.8, 0.45, None, 0.0, 1.0),        # plate edging / haft bands
    "BH_Cloth_Primary": ((0.1, 0.17, 0.3), 0.0, 0.75, None, 0.0, 1.0),     # frozen deep ice-blue gown
    "BH_Cloth_Secondary": ((0.55, 0.68, 0.8), 0.0, 0.6, None, 0.0, 1.0),   # pale veil
    "BH_Horn": ((0.86, 0.9, 0.95), 0.0, 0.55, None, 0.0, 1.0),             # frost feathers
    "BH_Bone": ((0.93, 0.93, 0.94), 0.0, 0.25, None, 0.0, 1.0),            # porcelain mask
    "BH_Stone": ((0.72, 0.9, 1.0), 0.0, 0.08, (0.2, 0.45, 0.6), 0.5, 1.0),  # ice (crown, trim, glaive blade)
    "BH_Shadow": ((0.01, 0.018, 0.035), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((0.55, 0.88, 1.0), 0.0, 0.3, (0.45, 0.8, 1.0), 9.0, 1.0),
}
CLIPS = ["spear_1", "spear_2", "spear_heavy", "boss_sweep", "boss_slam", "cast_heavy", "cast_area", "cast_ultimate",
         "boss_summon", "boss_roar"]
PREVIEW_HEIGHT = 2.7


def finish_mesh(mesh_ob):
    HS.enable_weapon_deform(mesh_ob)


SL = [  # slender standard-space torso rows
    (0.96, 0.13, 0.085, 0.09, 0.0),
    (1.04, 0.112, 0.074, 0.078, 0.02),
    (1.14, 0.108, 0.075, 0.075, 0.05),
    (1.25, 0.13, 0.095, 0.085, 0.12),
    (1.35, 0.145, 0.1, 0.09, 0.1),
    (1.43, 0.148, 0.092, 0.092, 0.04),
    (1.49, 0.125, 0.078, 0.08, 0.0),
    (1.53, 0.07, 0.056, 0.056, 0.0),
]
TORSO_W = KB.zspec_w([(0.99, "hips"), (1.1, "spine"), (1.2, "spine"), (1.3, "chest")])
CHEST_W = KB.zspec_w([(1.2, "spine"), (1.3, "chest")])


# --------------------------------------------------------------------------------------------------- head
def mask_head():
    """Porcelain mask head: smooth, high cheekbones, almond sockets with blue light, a thin dark mouth line and
    cracks (one leaking light)."""
    parts = []
    V, F = torso_loft(KB.HEAD, n=22, p=2.1, cap0=True, cap1=True)
    h = P(V, F, "BH_Bone", "mask")
    for sx in (1, -1):
        HS.dent(h, (sx * 0.03, -0.07, 1.7), (0, 1, 0), 0.008, 0.016)
    parts.append(h)
    for sx in (1, -1):
        parts.append(ball((sx * 0.03, -0.068, 1.7), 0.017, "BH_Shadow", 8, 4, (1.35, 0.55, 0.62)))
        parts.append(ball((sx * 0.03, -0.075, 1.7), 0.009, "BH_Emissive", 6, 4, (1.4, 0.6, 0.7)))
        parts.append(rtube([(sx * 0.028, -0.078, 1.672), (sx * 0.056, -0.058, 1.682), (sx * 0.066, -0.03, 1.69)],
                           0.006, "BH_Bone", n=4))
    V, F = M.box(0.034, 0.006, 0.004, center=(0, -0.083, 1.63))
    parts.append(P(V, F, "BH_Shadow", "mouth"))

    def on_face(x, z, lift=0.002):
        return (x, front_y(KB.HEAD, x, z) - lift, z)
    cracks = [([(0.03, 1.79), (0.035, 1.76), (0.024, 1.735), (0.034, 1.715)], "BH_Emissive"),
              ([(0.03, 1.685), (0.042, 1.66), (0.036, 1.64), (0.05, 1.615)], "BH_Emissive"),
              ([(-0.035, 1.78), (-0.045, 1.75), (-0.04, 1.73)], "BH_Shadow"),
              ([(-0.03, 1.685), (-0.024, 1.66), (-0.036, 1.64)], "BH_Shadow"),
              ([(0.036, 1.64), (0.02, 1.625)], "BH_Shadow")]
    for pts, mat in cracks:
        parts.append(rtube([on_face(x, z) for x, z in pts], 0.0032, mat, n=4, up=(0, -1, 0)))
    return parts


def icicle_crown():
    """Silver circlet with 13 long icicle spikes fanning outward, tallest over the brow; alternate spikes have a
    glowing core shard; a jewel of ice on the brow."""
    parts = []
    zc = 1.76
    ring = [(0.083 * math.cos(a), 0.008 + 0.092 * math.sin(a), zc + 0.008 * math.sin(a)) for a in
            np.linspace(0, 2 * math.pi, 25)]
    V, F = M.tube(ring, [(0.008, 0.014)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
    parts.append(P(V, F, "BH_Steel", "circlet"))
    n = 13
    for k in range(n):
        a = -math.pi / 2 + 2 * math.pi * k / n            # k = 0 at the brow (front, -Y)
        out = np.array([math.cos(a), math.sin(a), 0.0])
        front = max(0.0, -math.sin(a))                   # 1 at the brow, 0 at the sides / back
        base = np.array([0.083 * math.cos(a), 0.008 + 0.092 * math.sin(a), zc + 0.01])
        h = 0.15 + 0.2 * front ** 1.5 + (0.03 if k % 2 == 0 else 0.0)
        d = normalize(out * (0.22 + 0.25 * (1 - front)) + np.array([0, 0, 1.0]))
        parts.append(A.shard(base, d, h, 0.02 if k % 2 == 0 else 0.015, "BH_Stone", sides=4, twist=k * 17))
        if k % 2 == 0:
            parts.append(A.shard(base + d * 0.01, d, h * 0.72, 0.009, "BH_Emissive", sides=4, twist=k * 17 + 45))
    parts.append(A.ball((0, -0.092, zc + 0.02), 0.016, "BH_Emissive", n=6, rings=4, scale=(0.9, 0.6, 1.3)))
    return parts


# --------------------------------------------------------------------------------------------------- mantle
def feather_mantle():
    """(shoulder layers on the chest, fan feathers rising behind the head) - frost-white feathers."""
    cape, fan = [], []
    # layered shoulder feathers hanging over the shoulders / upper back / upper chest
    for row, (z, ln, g) in enumerate(((1.5, 0.2, 0.035), (1.44, 0.2, 0.05), (1.38, 0.16, 0.06))):
        m = 16 - 2 * row
        for j in range(m):
            f = (j + 0.5 * (row % 2)) / m
            if 0.9 < f or f < 0.1:            # leave the throat / chest front open
                continue
            q = KB.ring_frac(SL, min(z, 1.49), g + 0.02 * (z > 1.47) * 1.5, [f])[0]
            if z > 1.47:
                q[:2] *= 1.25
            nrm = normalize(np.array([q[0], q[1], 0.0]))
            d = normalize(nrm * 0.45 + np.array([0, 0, -1.0]))
            side = np.cross(d, nrm)
            cape.append(A.feather(q + (0, 0, 0.03), d, ln, 0.065, "BH_Horn", side=side, bend=-0.12))
    # the fan: long feathers rising from the upper back behind the head
    for j in range(11):
        t = -1 + 2 * j / 10
        base = np.array([0.05 * t, 0.1, 1.44])
        d = normalize(np.array([0.75 * t, 0.35, 1.0 - 0.35 * abs(t)]))
        ln = 0.42 - 0.12 * abs(t)
        fan.append(A.feather(base, d, ln, 0.08, "BH_Horn", side=(1, 0, 0) if abs(t) < 0.5 else (0, 1, 0), bend=0.1))
        if j % 2 == 0:
            fan.append(A.shard(base + d * ln * 0.6, d, ln * 0.45, 0.01, "BH_Stone", sides=4))
    return cape, fan


def veil():
    """Pale veil hanging from the back of the crown down the back, between the fan feathers."""
    def fn(u, v):
        half = 0.06 + 0.12 * v
        x = (u - 0.5) * 2 * half
        z = 1.76 - 0.58 * v - ragged(u, 1.7, 0.06, 3) * v
        y = 0.09 + 0.07 * v + 0.012 * math.sin(u * 9) * v
        if z < 1.49:
            y = max(y, back_y(SL, x, max(z, 1.2)) + 0.05)
        return (x, y, z)
    V, F = M.grid(fn, 6, 7)
    return M.solidify(P(V, F, "BH_Cloth_Secondary", "veil"), 0.006, offset=1.0)


def train():
    """Long gown train: from the back of the hips down to the floor and trailing ~0.75 m behind her."""
    def fn(u, v):
        half = 0.18 + 0.22 * v
        x = (u - 0.5) * 2 * half
        if v < 0.55:
            s = v / 0.55
            z = 0.98 - 0.95 * s ** 1.3
            y = back_y(SL, x * 0.7, 1.0) + 0.1 + 0.2 * s ** 2
        else:
            s = (v - 0.55) / 0.45
            z = 0.03 + 0.01 * math.sin(u * 7)
            y = back_y(SL, 0, 1.0) + 0.3 + 0.55 * s
        z += ragged(u, 3.3, 0.02, 4) * (v > 0.97)
        return (x, y, z)
    V, F = M.grid(fn, 9, 10)
    return M.solidify(P(V, F, "BH_Cloth_Primary", "train").flip(), 0.01, offset=1.0)


# --------------------------------------------------------------------------------------------------- glaive
def ice_glaive():
    """Silver haft (weapon space, grip at origin) with dark bands; a long curved blade of blue ice (edge +X) with a
    glowing core, crystal barbs on the spine, an ice collar and an ice butt-spike."""
    parts = []
    prof = [(0, -0.8), (0.012, -0.8), (0.02, -0.76), (0.019, 0.0), (0.019, 0.95), (0.016, 1.0), (0, 1.01)]
    V, F = M.lathe(prof, 8)
    parts.append(P(V, F, "BH_Steel", "haft"))
    parts.append(WP._grip(-0.1, 0.12, 0.0205, 6, mat="BH_DarkSteel"))
    for z in (-0.72, 0.42, 0.9):
        V, F = M.lathe([(0.0, z - 0.014), (0.025, z - 0.014), (0.025, z + 0.014), (0.0, z + 0.014)], 8)
        parts.append(P(V, F, "BH_DarkSteel", "band"))
    parts.append(A.shard((0, 0, -0.78), (0, 0, -1), 0.16, 0.024, "BH_Stone", sides=5))
    V, F = M.lathe([(0.0, 0.93), (0.03, 0.94), (0.038, 0.98), (0.03, 1.03), (0.0, 1.04)], 8)
    parts.append(P(V, F, "BH_Stone", "collar"))
    out = [(-0.03, 0.99), (0.05, 1.0), (0.1, 1.1), (0.125, 1.24), (0.115, 1.38), (0.08, 1.49), (0.03, 1.57),
           (-0.01, 1.62), (-0.015, 1.52), (-0.025, 1.38), (-0.035, 1.22), (-0.045, 1.1)]
    o = np.array(out)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    V, F = M.prism(M.resample_closed(o, 30), 0.03, axis="y")
    blade = P(V, F, "BH_Stone", "blade")
    blade.warp(lambda v: (v[0], v[1] * (1.0 - 0.75 * min(max((v[0] + 0.01) / 0.13, 0), 1)), v[2]))
    parts.append(blade)
    c = o.mean(0)
    inner = (o - c) * np.array([0.55, 0.78]) + c + np.array([0.012, 0.0])
    V, F = M.prism(M.resample_closed(inner, 20), 0.036, axis="y")
    parts.append(P(V, F, "BH_Emissive", "core"))
    for (z, ln) in ((1.12, 0.1), (1.26, 0.13), (1.4, 0.09)):
        parts.append(A.shard((-0.03, 0.0, z), (-1.0, 0.0, 0.8), ln, 0.016, "BH_Stone", sides=4))
    return parts


# --------------------------------------------------------------------------------------------------- build
def build(real):
    body = Scaled(real, K)
    sb = KB.SB(real, K)
    add = body.add
    # ---- head, neck, crown, veil
    V, F = M.tube([(0, 0.0, 1.46), (0, -0.004, 1.54), (0, -0.01, 1.62)], [(0.045, 0.043), (0.04, 0.038),
                                                                         (0.042, 0.042)], n=12, up=(0, -1, 0))
    add(P(V, F, "BH_Bone", "neck"), weights=KB.HEAD_W)
    for prt in mask_head():
        add(prt, "head")
    for prt in icicle_crown():
        add(prt, "head")
    add(veil(), weights=KB.zspec_w([(1.3, "chest"), (1.56, "neck"), (1.66, "head")]))
    # ---- torso: gown bodice, ice-plate cuirass, gorget, hip lames
    V, F = torso_loft([r for r in SL if r[0] >= 0.96], n=24, cap1=True)
    add(P(V, F, "BH_Cloth_Primary", "bodice"), weights=TORSO_W)
    zs = [1.1, 1.18, 1.25, 1.31, 1.37, 1.43, 1.48]
    rows = [(z,) + tuple(x + 0.014 for x in interp_rows(SL, z)[1:4]) + (interp_rows(SL, z)[4],) for z in zs]
    V, F = torso_loft(rows, n=24)
    cui = P(V, F, "BH_Steel", "cuirass")
    add(M.solidify(cui, 0.008, offset=1.0), weights=TORSO_W)
    V, F = thick_band(SL, 1.095, 1.115, 0.026, 0.01, n=24)
    add(P(V, F, "BH_DarkSteel", "cuirass_rim"), weights=TORSO_W)
    pts = [(0, front_y(SL, 0, z) - 0.024, z) for z in np.linspace(1.12, 1.46, 6)]
    add(rtube(pts, 0.008, "BH_DarkSteel", n=5, up=(0, -1, 0)), weights=TORSO_W)
    for sx in (1, -1):        # frost-flower filigree on the breast
        c = np.array([sx * 0.06, front_y(SL, sx * 0.06, 1.36) - 0.024, 1.36])
        for k in range(5):
            a = 2 * math.pi * k / 5
            add(rtube([c, c + np.array([0.035 * math.cos(a), 0, 0.035 * math.sin(a)])], 0.004, "BH_Stone", n=4),
                "chest")
    prof = [(0.14, 1.46), (0.12, 1.5), (0.085, 1.54), (0.072, 1.58), (0.064, 1.58), (0.078, 1.54), (0.11, 1.5),
            (0.13, 1.46), (0.14, 1.46)]
    V, F = M.lathe(prof, 18)
    add(P(V, F, "BH_Steel", "gorget").scale((1.0, 0.85, 1.0)), "chest")
    V, F = thick_band(SL, 1.0, 1.05, 0.022, 0.008, n=24)
    add(P(V, F, "BH_Steel", "girdle"), "hips")
    by = front_y(SL, 0, 1.025) - 0.024
    add(A.ball((0, by, 1.025), 0.022, "BH_Emissive", n=6, rings=4, scale=(1.0, 0.6, 1.2)), "hips")
    for side_a in ((0.1, 0.4), (0.6, 0.9)):
        for i in range(2):
            z1 = 1.0 - 0.055 * i
            V, F = arc_band(SL, z1 - 0.07, z1, 0.035 + 0.02 * i, side_a[0], side_a[1], n=10)
            lame = P(V, F, "BH_Steel", "tasset")
            lame.warp(lambda v, z1=z1: (v[0] * (1 + 0.35 * (z1 - v[2])), v[1] * (1 + 0.35 * (z1 - v[2])), v[2]))
            add(M.solidify(lame, 0.006, offset=1.0), weights=body.skirt_weights(1.0, 0.8, max_leg=0.35, center_w=0.05))
    # ---- gown skirt (4 panels, ice trim) + train
    AC.robe_skirt(sb, "BH_Cloth_Primary", trim="BH_Stone", z_top=1.04, z_bot=0.02, flare=0.2, folds=0.016,
                  front_gap=0.006, ragged=0.02, g=0.012)
    add(train(), weights=body.skirt_weights(1.0, 0.3, max_leg=0.25, center_w=0.1))
    rng = np.random.default_rng(12)
    for k in range(9):        # icicles frozen on the gown hem
        a = 2 * math.pi * k / 9 + rng.random() * 0.3
        c = np.array([0.34 * math.cos(a), 0.3 * math.sin(a), 0.12])
        for prt in RH.shards(c, (math.cos(a), math.sin(a), 0.6), 0.08, 90 + k, count=2, spread=20):
            add(prt, weights=body.skirt_weights(1.0, 0.3, max_leg=0.6 if math.sin(a) < 0 else 0.4, center_w=0.1))
    # ---- mantle of frost feathers
    cape, fan = feather_mantle()
    for prt in cape:
        add(prt, "chest")
    for prt in fan:
        add(prt, "chest")
    # ---- arms: bell sleeves, ice-plate pauldrons + vambraces, gauntlets
    for s in ("L", "R"):
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        sx = 1 if s == "L" else -1
        AC.bell_sleeve(sb, s, "BH_Cloth_Primary", trim="BH_Stone", cuff_r=0.075, end=0.55)
        Lf = body.p["fore_len"]
        V, F = M.tube(body.lpt(fa, [(0, u * Lf, 0) for u in (0.55, 0.78, 1.0)]),
                      [(0.044, 0.046), (0.042, 0.044), (0.04, 0.042)], n=10, up=(0, 0, 1))
        add(M.bevel(P(V, F, "BH_Steel", "vambrace"), 0.003, 1, angle=50), fa)
        for prt in fist(body, s, "BH_Steel", "BH_DarkSteel", gauntlet=True, scale=0.98):
            add(prt, ha)
        sh = body.head(ua)
        for i, (r, dz) in enumerate(((0.1, 0.0), (0.085, -0.055))):
            V, F = dome(sh + np.array([sx * 0.02, 0.0, 0.03 + dz]), (sx * 0.8, 0, 0.7), r, a_max=70, n=12, rings=4,
                        scale=(1.0, 1.1, 0.8))
            add(M.solidify(P(V, F, "BH_Steel" if i == 0 else "BH_DarkSteel", "pauldron"), 0.006, offset=-1), ua)
        for prt in RH.shards(sh + np.array([sx * 0.07, 0.0, 0.1]), (sx * 0.7, 0.0, 1.0), 0.16, 30 + i + sx, count=3,
                             spread=22):
            add(prt, ua)
        rim = [sh + np.array([sx * (0.02 + 0.09 * math.cos(a)), 0.1 * math.sin(a), -0.02]) for a in
               np.linspace(-1.3, 1.3, 5)]
        for prt in RH.icicles(rim, 0.08, seed=40 + sx, r=0.009):
            add(prt, ua)
    # ---- weapon
    add_weapon(body, "R", ice_glaive())
