"""Frost Revenant (bh-010, Builder A; undead elite knight): a massive ancient knight risen from the ice. Dark, rusted
plate crusted with pale frost and jagged glowing ice crystals (big clusters bursting from both pauldrons, a frozen
ridge down the back, shards on the forearms and knees), a crown of ice spikes round the great helm, cold cyan eyes in
the visor slit and icicles hanging from its chin, a tattered frozen cloak (cape bones) with an icicle hem over a
torn frost-blue tabard, and a huge ice-crusted greatsword in the right hand (rigid on weapon.R).
~2.2 m to the top of the helm (the ice crown rises ~0.15 m higher). Built on the knight's plate kit at scale 1.2
(enemy_hollow_soldier.Scaled / char_knight parts, the boss_warden cape logic)."""
import math
import numpy as np

import bh_mesh as M
import bh_weapons as WP
from bh_body import Body, torso_loft, front_y, back_y, dome, fist, smoothstep, interp_rows
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import char_knight as KN
from char_knight import TORSO, rows_between, thick_band, arc_band
import enemy_hollow_soldier as HS
from enemy_hollow_soldier import P, rtube, ball, Scaled, add_weapon, dent, ragged
import enemy_boss_warden as BW
import kit_a_common as A

K = 1.2
PROPS = proportions(K)
EXTRA_BONES = [(n, tuple(np.array(h) * K), tuple(np.array(t) * K), par, z) for (n, h, t, par, z) in KN.CAPE_BONES]
PALETTE = "frost_revenant"
PALETTE_COLORS = {
    "BH_Steel": ((0.17, 0.19, 0.22), 0.8, 0.58, None, 0.0, 1.0),           # dark, cold-rusted plate
    "BH_DarkSteel": ((0.05, 0.055, 0.065), 0.9, 0.55, None, 0.0, 1.0),
    "BH_Rust": ((0.24, 0.12, 0.065), 0.4, 0.82, None, 0.0, 1.0),            # rust on edges / rims
    "BH_Stone": ((0.62, 0.8, 0.9), 0.0, 0.12, None, 0.0, 1.0),              # frost crust / icicles (glassy)
    "BH_Cloth_Primary": ((0.06, 0.08, 0.12), 0.0, 0.88, None, 0.0, 1.0),    # frozen dark-blue cloak / tabard
    "BH_Leather": ((0.045, 0.04, 0.04), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Shadow": ((0.01, 0.02, 0.03), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((0.6, 0.95, 1.0), 0.0, 0.3, (0.45, 0.88, 1.0), 7.0, 1.0),  # glowing ice / eyes
}
CLIPS = ["gs_1", "gs_2", "gs_heavy", "cast_area", "cast_heavy", "boss_slam"]
PREVIEW_HEIGHT = 2.6


def finish_mesh(mesh_ob):
    HS.enable_weapon_deform(mesh_ob)


secondary = BW.secondary        # the knight cape logic + gravity fold for the lower cape when lying down

# bulkier plate: the knight's torso grown outward (standard space; everything is scaled by K on add)
TB = [(r[0], r[1] * 1.1 + 0.01, r[2] * 1.08 + 0.008, r[3] * 1.1 + 0.01, r[4]) for r in TORSO]
CHEST_W = KN.chest_spine_w(1.24, 1.30)


def remat(parts, table):
    for p in parts:
        p.mat = table.get(p.mat, p.mat)
    return parts


def frost(body, add_fn, center, normal, size, seed, glow=True, crust=True, count=4, spread=30.0):
    """Frost crust patch (pale glassy blobs) + a cluster of glowing ice shards at a surface point."""
    n = normalize(normal)
    rng = np.random.default_rng(seed)
    if crust:
        for k in range(3):
            off = (rng.random(3) - 0.5) * size * 0.9
            off -= n * np.dot(off, n)
            b = A.ball(np.asarray(center) + off, size * (0.5 + 0.3 * rng.random()), "BH_Stone", n=7, rings=4,
                       scale=(1.0, 1.0, 0.3))
            from bh_body import M_align_z
            b.V = (b.V - b.V.mean(0)) @ M_align_z(n).T + (np.asarray(center) + off)
            add_fn(b)
    if glow:
        for prt in A.cluster(center, n, size * 2.2, "BH_Emissive", count=count, seed=seed, spread=spread):
            add_fn(prt)


# --------------------------------------------------------------------------------------------------- weapon
def frost_greatsword():
    """Huge greatsword (weapon space) crusted with ice: dark blade, rusted guard, glassy frost along both edges,
    glowing shards bursting from the flats near the guard and at the tip, an ice-shard pommel."""
    parts = []
    parts.append(WP._blade(0.14, 1.38, 0.09, 0.06, 0.009, tip=0.2, n_sec=12, mat="BH_DarkSteel"))
    parts.append(M.bevel(WP._crossguard(0.12, 0.24, h=0.036, t=0.03, curve=-0.05, mat="BH_Rust"), 0.004, 1))
    parts.append(WP._grip(-0.3, 0.1, 0.019, 9, mat="BH_Leather"))
    V, F = M.box(0.1, 0.028, 0.06, center=(0, 0, 0.15))
    parts.append(M.bevel(P(V, F, "BH_Rust", "ricasso"), 0.004, 1))
    # pommel: an ice shard growing out of a rusted cap
    V, F = M.lathe([(0, -0.3), (0.03, -0.3), (0.036, -0.33), (0.0, -0.345)], 8)
    parts.append(P(V, F, "BH_Rust", "pommel"))
    parts.append(A.shard((0, 0, -0.33), (0, 0, -1), 0.12, 0.028, "BH_Emissive", sides=5))
    # frost crust along both edges (glassy blobs) and glowing shards
    rng = np.random.default_rng(4)
    for sx in (1, -1):
        for i, z in enumerate(np.linspace(0.3, 1.18, 9)):
            w = (0.09 + (0.06 - 0.09) * (z - 0.14) / 1.04) / 2
            c = np.array([sx * w * 0.8, 0.0, z])
            parts.append(A.ball(c, 0.022 + 0.01 * rng.random(), "BH_Stone", n=6, rings=4, scale=(0.9, 0.55, 1.6)))
            if i % 2 == 0:
                d = normalize(np.array([sx * 1.0, (rng.random() - 0.5) * 0.6, 0.5 + 0.3 * rng.random()]))
                parts.append(A.shard(c, d, 0.07 + 0.05 * rng.random(), 0.014, "BH_Emissive", sides=4,
                                     twist=rng.random() * 90))
    for sy in (1, -1):   # shards off the flats by the guard
        for k in range(3):
            d = normalize(np.array([(k - 1) * 0.5, sy * 1.0, 0.8]))
            parts.append(A.shard((0.02 * (k - 1), sy * 0.006, 0.2 + 0.03 * k), d, 0.11 - 0.02 * abs(k - 1), 0.02,
                                 "BH_Emissive", sides=5, twist=20 * k))
    # frozen glow running up the fuller
    for sy in (1, -1):
        V, F = M.box(0.014, 0.004, 0.9, center=(0.0, sy * 0.0085, 0.72))
        parts.append(P(V, F, "BH_Emissive", "fuller_ice"))
    # icicles hanging off the guard
    for sx in (1, -1):
        for k in range(2):
            b = np.array([sx * (0.12 + 0.07 * k), 0.0, 0.11])
            parts.append(A.taper([b, b + (0, 0, -0.07 - 0.03 * k)], 0.012, 0.0015, "BH_Stone", n=5))
    return parts


# --------------------------------------------------------------------------------------------------- pieces
def ice_crown():
    """Ring of jagged ice spikes round the helm (tallest at the brow and back), set in a rusted band."""
    parts = []
    zc = 1.8
    V, F = M.lathe([(0.122, zc - 0.022), (0.13, zc - 0.018), (0.13, zc + 0.018), (0.122, zc + 0.022)], 20, cap=False)
    parts.append(M.solidify(P(V, F, "BH_Rust", "crownband").scale((1.0, 1.08, 1.0)).move((0, 0.008, 0)), 0.006,
                            offset=-1))
    for k in range(11):
        a = 2 * math.pi * k / 11 - math.pi / 2
        c = np.array([0.128 * math.cos(a), 0.008 + 0.138 * math.sin(a), zc + 0.01])
        out = np.array([math.cos(a), math.sin(a), 0.0])
        front = -math.sin(a)                       # 1 at the brow
        h = 0.09 + 0.08 * max(front, 0) ** 2 + 0.05 * (k % 2 == 0)
        d = normalize(out * 0.35 + np.array([0, 0, 1.0]))
        parts.append(A.shard(c, d, h, 0.026 if k % 2 == 0 else 0.018, "BH_Emissive", sides=4, twist=k * 23))
    return parts


def icicle_row(pts, ln, mat="BH_Stone", seed=0, r=0.012):
    rng = np.random.default_rng(seed)
    out = []
    for q in pts:
        l = ln * (0.4 + 0.6 * rng.random())
        q = np.asarray(q, float)
        out.append(A.taper([q + (0, 0, 0.005), q + (0, 0, -l * 0.6), q + (0, 0, -l)], r, 0.001, mat, n=4))
    return out


def frozen_cloak():
    """One wide cloak from the shoulders, the hem torn into tongues and hung with icicles."""
    nu, nv = 11, 13

    def fn(u, v):
        half = 0.24 + 0.11 * v
        x = (u - 0.5) * 2 * half
        zb = 0.26 + ragged(u, 3.3, 0.26, 5)
        z = 1.47 + (zb - 1.47) * v
        if v < 0.2:
            yb = back_y(TB, x * 0.95, min(max(z, 1.3), 1.47)) + 0.045
        else:
            yb = back_y(TB, x * 0.95, 1.3) + 0.045
        y = yb + 0.08 * v ** 1.2 + 0.02 * math.sin(u * math.pi * 5.0) * v
        y -= 0.06 * (abs(u - 0.5) * 2) ** 3 * (1 - v) ** 2
        return (x, y, z)
    V, F = M.grid(fn, nu, nv)
    p = M.solidify(P(V, F, "BH_Cloth_Primary", "cloak"), 0.013, offset=1.0)
    hem = [fn(u, 1.0) for u in np.linspace(0.03, 0.97, 9)]
    return p, hem, fn


# --------------------------------------------------------------------------------------------------- build
def build(real: Body):
    body = Scaled(real, K, EXTRA_BONES)
    add = body.add
    TR = {"BH_Gold": "BH_Rust", "BH_Aether": "BH_Emissive"}
    # ---- torso plate
    V, F = torso_loft(rows_between(TB, 1.215, 1.53, n_extra=3), n=28, cap1=True)
    bp = P(V, F, "BH_Steel", "breastplate")
    dent(bp, (0.12, -0.14, 1.4), (-1, 1, 0), 0.015, 0.04)
    add(M.bevel(bp, 0.004, 1, angle=50), weights=CHEST_W)
    V, F = torso_loft(rows_between(TB, 0.99, 1.30, scale=0.985, n_extra=2), n=28, cap0=True)
    add(P(V, F, "BH_Steel", "plackart"), weights=KN.spine_hips_w(1.0, 1.04))
    V, F = thick_band(TB, 1.212, 1.232, 0.012, 0.0, n=28)
    add(P(V, F, "BH_Rust", "rim"), weights=CHEST_W)
    prof = [(0.17, 1.45), (0.145, 1.49), (0.104, 1.527), (0.088, 1.57), (0.076, 1.57), (0.092, 1.527),
            (0.135, 1.49), (0.16, 1.45), (0.17, 1.45)]
    V, F = M.lathe(prof, 20)
    add(P(V, F, "BH_DarkSteel", "gorget").scale((1.0, 0.85, 1.0)), "chest")
    # a frozen wound in the chest: cracked plate with a glowing ice heart
    for prt in A.cluster((0.05, front_y(TB, 0.05, 1.37) + 0.01, 1.37), (0.2, -1, 0.15), 0.07, "BH_Emissive", count=5,
                         seed=7, spread=35):
        add(prt, weights=CHEST_W)
    for pts in (((0.05, 1.37), (0.1, 1.42), (0.13, 1.44)), ((0.05, 1.37), (0.0, 1.31), (-0.03, 1.28)),
                ((0.05, 1.37), (0.11, 1.33))):
        q = [(x, front_y(TB, x, z) - 0.003, z) for x, z in pts]
        add(rtube(q, 0.006, "BH_Emissive", n=4, up=(0, -1, 0)), weights=CHEST_W)
    # frost patches on the chest / belly
    for (x, z, sd) in ((-0.1, 1.42, 1), (0.13, 1.27, 2), (-0.06, 1.12, 3)):
        frost(body, lambda p: add(p, weights=CHEST_W if z > 1.2 else KN.spine_hips_w(1.0, 1.04)),
              (x, front_y(TB, x, z) - 0.004, z), (x * 2, -1, 0.1), 0.03, sd, glow=(sd != 3), count=3)
    # frozen ridge down the back: big shards along the spine
    for i, z in enumerate(np.linspace(1.44, 1.16, 5)):
        yb = back_y(TB, 0, z)
        for prt in A.cluster((0.0, yb - 0.005, z), (0, 1, 0.45), 0.09 - 0.01 * i, "BH_Emissive", count=3, seed=20 + i,
                             spread=25):
            add(prt, weights=CHEST_W if z > 1.25 else KN.chest_spine_w(1.0, 1.25))
    # ---- belt, faulds, mail skirt, torn tabard
    V, F = thick_band(TB, 1.02, 1.07, 0.03, 0.012, n=26)
    add(P(V, F, "BH_Leather", "belt"), "hips")
    by = front_y(TB, 0, 1.045) - 0.032
    V, F = M.box(0.08, 0.018, 0.07, center=(0, by, 1.045))
    add(M.bevel(P(V, F, "BH_Rust", "buckle"), 0.006, 1), "hips")
    for side_a in ((0.12, 0.38), (0.62, 0.88)):
        for i in range(3):
            z1 = 1.025 - 0.05 * i
            V, F = arc_band(TB, z1 - 0.065, z1, 0.035 + 0.02 * i, side_a[0], side_a[1], n=10)
            lame = P(V, F, "BH_Steel", "fauld")
            lame.warp(lambda v, z1=z1: (v[0] * (1 + 0.3 * (z1 - v[2])), v[1] * (1 + 0.3 * (z1 - v[2])), v[2]))
            add(M.solidify(lame, 0.007, offset=1.0), weights=body.skirt_weights(1.0, 0.8, max_leg=0.35, center_w=0.05))
    V, F = torso_loft([(0.97, 0.175, 0.122, 0.118, 0.0), (0.86, 0.19, 0.128, 0.125, 0.0),
                       (0.74, 0.2, 0.13, 0.128, 0.0)], n=26)
    add(P(V, F, "BH_DarkSteel", "mailskirt"), weights=body.skirt_weights(0.98, 0.74, max_leg=0.8))
    for front in (True, False):
        add(HS.cloth_panel(TB, 1.03, 0.4, lambda z: 0.11 + 0.03 * (1.03 - z), front=front, nu=7, nv=9,
                           seed=1.3 if front else 2.9, rag=0.16, teeth=3, gap=0.03, belt_z=1.03),
            weights=HS.cloth_w(belt_z=1.03, leg=0.5))
    # ---- legs
    for s in ("L",):
        th, sh = "thigh." + s, "shin." + s
        am = body.add_mirror
        am(M.bevel(body.limb(th, [(-0.02, 0.095, 0.1), (0.3, 0.094, 0.098), (0.93, 0.072, 0.076)], "BH_Steel", n=12,
                             p=2.4), 0.003, 1, angle=50), th)
        k = body.head(sh)
        V, F = dome(k + (0, -0.05, 0.0), (0, -1, 0.15), 0.072, a_max=78, n=12, rings=4)
        am(M.solidify(P(V, F, "BH_Steel", "poleyn"), 0.008, offset=-1),
           weights=lambda V, th=th, sh=sh: [{th: 0.5, sh: 0.5}] * len(V))
        for prt in A.cluster(k + (0.0, -0.1, 0.02), (0.3, -1, 0.5), 0.06, "BH_Emissive", count=3, seed=31):
            am(prt, weights=lambda V, th=th, sh=sh: [{th: 0.4, sh: 0.6}] * len(V))
        am(M.bevel(body.limb(sh, [(0.03, 0.07, 0.072), (0.3, 0.076, 0.08), (0.85, 0.056, 0.058), (1.0, 0.06, 0.062)],
                             "BH_Steel", n=12, p=2.3), 0.003, 1, angle=50), sh)
        for part, bone in KN.sabaton(body, s):
            part.scale((1.1, 1.08, 1.1), center=(body.head(th)[0], 0, 0))
            am(part, bone)
        # frost on the shin front
        am(A.ball(k + (0.0, -0.068, -0.2), 0.035, "BH_Stone", n=7, rings=4, scale=(1.0, 0.35, 1.6)), sh)
    # ---- arms: heavy plate, huge frost-burst pauldrons
    for s in ("L",):
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        am = body.add_mirror
        am(body.limb(ua, [(0.3, 0.07, 0.072), (0.95, 0.06, 0.062)], "BH_Steel", n=12, p=2.3), ua)
        el = body.head(fa)
        V, F = dome(el + (0.0, 0.035, 0.0), (0, 1, 0.1), 0.062, a_max=80, n=12, rings=4)
        am(M.solidify(P(V, F, "BH_Steel", "couter"), 0.007, offset=-1),
           weights=lambda V, ua=ua, fa=fa: [{ua: 0.5, fa: 0.5}] * len(V))
        am(body.limb(fa, [(0.1, 0.058, 0.06), (0.5, 0.056, 0.058), (0.93, 0.05, 0.052)], "BH_Steel", n=12, p=2.3), fa)
        cuff = body.limb(fa, [(0.8, 0.054, 0.056), (1.0, 0.07, 0.07), (1.1, 0.076, 0.074)], "BH_Rust", n=12,
                         cap0=False, cap1=False)
        am(M.solidify(cuff, 0.005, offset=1.0), ha)
        for prt in fist(body, s, "BH_Steel", "BH_DarkSteel", scale=1.15):
            am(prt, ha)
        # shards along the outer forearm
        L = body.p["fore_len"]
        for u, ln in ((0.35, 0.07), (0.6, 0.09)):
            b = body.lpt(fa, [(0.0, u * L, 0.055)])[0]
            for prt in A.cluster(b, (0.3, 0.3, 1.0), ln, "BH_Emissive", count=2, seed=int(u * 100)):
                am(prt, fa)
        pd = remat(KN.pauldron(body, s), TR)
        for prt in pd:
            prt.scale((1.35, 1.3, 1.12), center=body.head(ua) + np.array([-0.03, 0.0, 0.0]))
            am(prt, ua)
        sh_ = body.head(ua)
        for prt in A.cluster(sh_ + np.array([0.07, 0.0, 0.14]), (0.6, 0.1, 1.0), 0.13, "BH_Emissive", count=5,
                             seed=41, spread=32):
            am(prt, ua)
        for (dx, dy, dz, sd) in ((0.12, -0.08, 0.1, 43), (0.1, 0.1, 0.11, 44)):
            frost(body, lambda p, ua=ua: am(p, ua), sh_ + np.array([dx, dy, dz]), (0.8, dy * 3, 0.8), 0.03, sd,
                  count=2, spread=20)
    # ---- helm: knight's great helm, rusted, cyan eyes, ice crown, icicle beard
    helm = [p for p in KN.helm(body) if p.name not in ("crest", "crest_base")]
    for p in remat(helm, TR):
        if p.name == "helm_up":
            dent(p, (-0.06, -0.1, 1.79), (0.4, 1, 0), 0.018, 0.03)
        add(p, "head")
    for sx in (1, -1):
        add(ball((sx * 0.037, -0.128, 1.706), 0.019, "BH_Emissive", 6, 4, (1.7, 0.5, 0.72)), "head")
    # faint cold light filling the visor slit behind the eyes
    V, F = torso_loft([(1.692, 0.112, 0.126, 0.1, 0.06, 0.008), (1.72, 0.112, 0.126, 0.1, 0.06, 0.008)], n=20, p=2.6)
    add(P(V, F, "BH_Emissive", "slit_glow"), "head")
    for prt in ice_crown():
        add(prt, "head")
    chin = [(0.1 * math.sin(a), -0.118 * math.cos(a) + 0.008, 1.548) for a in np.linspace(-1.0, 1.0, 7)]
    for prt in icicle_row(chin, 0.12, seed=5, r=0.013):
        add(prt, "head")
    frost(body, lambda p: add(p, "head"), (0.07, -0.08, 1.8), (0.6, -1, 0.6), 0.025, 51, glow=False)
    # ---- cloak with icicles along the hem
    cl, hem, cfn = frozen_cloak()
    add(cl, weights=KN.cape_w())
    for prt in icicle_row([np.array(q) + (0, 0.004, 0.0) for q in hem], 0.1, seed=9, r=0.011):
        add(prt, weights=KN.cape_w())
    for (u, v, sd) in ((0.25, 0.25, 61), (0.7, 0.45, 62), (0.45, 0.7, 63)):
        q = np.array(cfn(u, v)) + (0, 0.014, 0)
        frost(body, lambda p: add(p, weights=KN.cape_w()), q, (0, 1, 0), 0.035, sd, glow=False)
    # ---- weapon
    add_weapon(body, "R", frost_greatsword())
