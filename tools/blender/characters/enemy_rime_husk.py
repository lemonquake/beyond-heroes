"""Rimebound Husk (bh-012, Builder D, Rimeglass Barrow grunt): a stiff, gaunt frozen corpse risen from the barrow ice.
Blue-grey dead skin stretched over the ribs, sunken cheeks, empty eye sockets with a faint blue light, frost-white
scraggly hair with frozen strands, icicles hanging from the jaw and both elbows. It is half-encased in jagged
faceted ice: a big crust of ice on the back (shards jutting up past the shoulders), the whole left arm locked in ice
blocks and the right leg in an ice sheath from the thigh down. Frost-glazed burial rags: a shroud over the left
shoulder, a ragged loin wrap and rag-bound feet. Weapon: a snapped, frost-rimed old sword (rigid on weapon.R) whose
broken blade is continued by a jagged spur of ice.

~1.8 m (standard skeleton, K = 1.0; the back ice rises ~0.1 m above the shoulders, not above the head).

Also holds the small ice helpers shared by the other Rimeglass Barrow modules (barrow_jarl, winter_crown).
"""
import math
import numpy as np

import bh_mesh as M
import bh_weapons as WP
from bh_body import torso_loft, front_y, back_y, dome, fist, M_align_z, smoothstep
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
import enemy_bandit_cutthroat as KB
import enemy_hollow_soldier as HS
from enemy_hollow_soldier import P, rtube, ball, Scaled, add_weapon, ragged, cloth_panel, cloth_w
import kit_a_common as A

K = 1.0
PROPS = proportions(K)
PALETTE = "rime_husk"
PALETTE_COLORS = {
    "BH_Skin": ((0.36, 0.43, 0.49), 0.0, 0.62, None, 0.0, 1.0),             # blue-grey frozen dead skin
    "BH_Cloth_Primary": ((0.11, 0.15, 0.21), 0.0, 0.85, None, 0.0, 1.0),    # frost-stiff deep-blue burial rags
    "BH_Cloth_Secondary": ((0.06, 0.075, 0.1), 0.0, 0.9, None, 0.0, 1.0),   # darker grave rags / foot wraps
    "BH_Stone": ((0.74, 0.92, 1.0), 0.0, 0.08, (0.2, 0.42, 0.55), 0.35, 1.0),  # faceted barrow ice (glassy)
    "BH_Hair": ((0.74, 0.8, 0.85), 0.0, 0.7, None, 0.0, 1.0),               # frost-white hair
    "BH_Bone": ((0.58, 0.6, 0.58), 0.0, 0.6, None, 0.0, 1.0),               # teeth
    "BH_Steel": ((0.42, 0.46, 0.5), 0.9, 0.5, None, 0.0, 1.0),              # old sword blade
    "BH_DarkSteel": ((0.1, 0.11, 0.13), 0.9, 0.55, None, 0.0, 1.0),
    "BH_Leather": ((0.07, 0.065, 0.065), 0.0, 0.75, None, 0.0, 1.0),
    "BH_Shadow": ((0.01, 0.018, 0.03), 0.0, 0.8, None, 0.0, 1.0),           # sockets / mouth
    "BH_Emissive": ((0.55, 0.85, 1.0), 0.0, 0.3, (0.45, 0.8, 1.0), 5.0, 1.0),  # faint cold eye-light / ice glow
}
CLIPS = ["sword_1", "sword_2", "sword_heavy"]


def finish_mesh(mesh_ob):
    KB.enable_weapon_deform(mesh_ob)


# ================================================================================================ shared ice kit
def ice_chunk(center, radii, seed, axis=(0, 0, 1), up=(1, 0, 0), mat="BH_Stone", n=7, rings=4, jit=0.22):
    """Faceted ice block: a low-poly ellipsoid with jittered vertices (flat facets read as ice at distance).
    radii = (rx, ry, r_along_axis); the block's long axis is `axis`."""
    rng = np.random.default_rng(seed)
    V, F = M.sphere(1.0, n, rings)
    k = 1.0 + jit * (rng.random(len(V)) - 0.5) * 2
    V = V * k[:, None] * np.asarray(radii, float)
    R = M_align_z(axis, up)
    V = V @ R.T + np.asarray(center, float)
    return P(V, F, mat, "ice")


def icicles(pts, ln, seed=0, r=0.011, mat="BH_Stone", down=(0, 0, -1), spread=0.25):
    """Row of icicles hanging from points (length ln * 0.4..1)."""
    rng = np.random.default_rng(seed)
    d0 = normalize(down)
    out = []
    for q in pts:
        q = np.asarray(q, float)
        l = ln * (0.4 + 0.6 * rng.random())
        d = normalize(d0 + (rng.random(3) - 0.5) * spread)
        out.append(A.taper([q - d * 0.006, q + d * l * 0.55, q + d * l], r * (0.8 + 0.4 * rng.random()), 0.0008, mat,
                           n=4))
    return out


def shards(base, normal, size, seed, mat="BH_Stone", count=4, spread=30.0, sides=5):
    return A.cluster(base, normal, size, mat, count=count, seed=seed, spread=spread, sides=sides)


# ================================================================================================ body
GAUNT = [  # standard space (z, rx, ry_front, ry_back, keel): starved torso, sunken waist, ribs
    (0.90, 0.145, 0.095, 0.1, 0.0),
    (0.97, 0.138, 0.09, 0.095, 0.0),
    (1.05, 0.114, 0.072, 0.085, 0.0),
    (1.14, 0.118, 0.078, 0.088, 0.03),
    (1.25, 0.142, 0.1, 0.094, 0.1),
    (1.35, 0.156, 0.106, 0.098, 0.08),
    (1.43, 0.158, 0.1, 0.1, 0.04),
    (1.49, 0.132, 0.084, 0.09, 0.0),
    (1.53, 0.076, 0.06, 0.062, 0.0),
]
TORSO_W = KB.TORSO_W
CHEST_W = KB.zspec_w([(1.2, "spine"), (1.3, "chest")])


def gaunt_head(body):
    """Skin head (bandit head rows) with sunken cheeks and temples, a heavy brow, empty sockets with a faint blue
    light, a rotted-off nose (dark cavity), lipless mouth with teeth; frost-white scraggly hair."""
    parts = []
    V, F = torso_loft(KB.HEAD, n=22, p=2.1, cap0=True, cap1=True)
    h = P(V, F, "BH_Skin", "head")
    for sx in (1, -1):
        HS.dent(h, (sx * 0.06, -0.05, 1.655), (-sx * 0.6, 0.6, 0), 0.012, 0.022)     # hollow cheeks
        HS.dent(h, (sx * 0.07, -0.03, 1.735), (-sx * 1, 0.2, 0), 0.008, 0.02)        # sunken temples
        HS.dent(h, (sx * 0.03, -0.07, 1.7), (0, 1, 0), 0.012, 0.018)                 # eye pits
    parts.append(h)
    # heavy brow ridge + cheekbones
    parts.append(rtube([(-0.055, -0.066, 1.722), (0.0, -0.079, 1.726), (0.055, -0.066, 1.722)], 0.011, "BH_Skin",
                       n=6))
    for sx in (1, -1):
        parts.append(rtube([(sx * 0.03, -0.074, 1.676), (sx * 0.058, -0.052, 1.68), (sx * 0.07, -0.02, 1.69)], 0.008,
                           "BH_Skin", n=5))
        parts.append(ball((sx * 0.03, -0.062, 1.699), 0.019, "BH_Shadow", 8, 5, (1.1, 0.7, 0.85)))
        parts.append(ball((sx * 0.03, -0.074, 1.698), 0.0085, "BH_Emissive", 6, 4, (1.2, 0.7, 0.9)))
        parts.append(ball((sx * 0.074, 0.0, 1.69), 0.018, "BH_Skin", 6, 4, (0.35, 0.8, 1.1)))   # withered ears
    # rotted nose: a dark triangular cavity
    V, F = M.prism([(-0.013, 0.0), (0.013, 0.0), (0.0, 0.03)], 0.012, axis="y")
    parts.append(P(V, F, "BH_Shadow", "nose").rot(Rx(12)).move((0, -0.082, 1.662)))
    # mouth: gaping dark hole, lipless, a few teeth left
    parts.append(ball((0, -0.066, 1.617), 0.024, "BH_Shadow", 8, 5, (1.0, 0.55, 1.1)))
    for (x, zz) in ((-0.016, 1.636), (0.0, 1.638), (0.017, 1.635), (-0.01, 1.597), (0.012, 1.598)):
        up = 1 if zz > 1.62 else -1
        parts.append(A.taper([(x, -0.083, zz), (x, -0.084, zz - up * 0.012)], 0.0055, 0.002, "BH_Bone", n=4))
    # chin / jaw hanging open
    parts.append(rtube([(-0.045, -0.04, 1.6), (-0.028, -0.07, 1.588), (0.0, -0.078, 1.585), (0.028, -0.07, 1.588),
                        (0.045, -0.04, 1.6)], 0.012, "BH_Skin", n=6))
    return parts


def hair(sb):
    """Mostly bald, frost-bitten scalp: a thin ragged hair fringe low round the back of the skull only."""
    KB.hair_cap(sb, mat="BH_Hair", g=0.004, z_front=1.83, z_back=1.64, messy=0.016)


def hair_strands(body):
    """Long lank frozen strands hanging from the scalp round the sides and back (stiff, icicle tips)."""
    parts = []
    rng = np.random.default_rng(3)
    for k in range(14):
        a = math.radians(-100 + 200 * k / 13 + (rng.random() - 0.5) * 12)       # 0 = straight back
        x, y = 0.072 * math.sin(a), 0.08 * math.cos(a) + 0.005
        zt = 1.78 - 0.05 * abs(math.sin(a))
        top = np.array([x, y, zt])
        ln = 0.2 + 0.16 * rng.random()
        out = normalize(np.array([x, y + 0.03, 0.0]))
        pts = [top, top + out * 0.035 + (0, 0, -ln * 0.35), top + out * 0.06 + (0, 0.02, -ln)]
        parts.append(A.taper(pts, 0.011, 0.0015, "BH_Hair", n=4))
    return parts


def build(real):
    body = Scaled(real, K)
    sb = KB.SB(real, K)
    add = body.add
    # ---------------------------------------------------------------- torso (starved skin, ribs)
    V, F = torso_loft([r for r in GAUNT if r[0] >= 0.97], n=24, cap1=True)
    add(P(V, F, "BH_Skin", "torso"), weights=TORSO_W)
    for i, z in enumerate((1.4, 1.36, 1.32, 1.28, 1.24)):
        for sx in (1, -1):
            pts = []
            for t in np.linspace(0, 1, 5):
                x = sx * (0.03 + 0.105 * t)
                zz = z - 0.03 * t - 0.004 * i
                pts.append((x, front_y(GAUNT, x, zz) + 0.004, zz))
            add(rtube(pts, 0.0065, "BH_Skin", n=4, r1=0.005), weights=CHEST_W)
    for sx in (1, -1):   # collarbones
        pts = [(sx * 0.02, front_y(GAUNT, 0.02, 1.47) + 0.004, 1.47), (sx * 0.1, front_y(GAUNT, 0.1, 1.475), 1.478),
               (sx * 0.16, -0.02, 1.47)]
        add(rtube(pts, 0.009, "BH_Skin", n=5), "chest")
    # neck (thin, sinewy)
    V, F = M.tube([(0, 0.0, 1.46), (0, -0.004, 1.54), (0, -0.01, 1.62)], [(0.048, 0.045), (0.042, 0.04),
                                                                         (0.045, 0.045)], n=12, up=(0, -1, 0))
    add(P(V, F, "BH_Skin", "neck"), weights=KB.HEAD_W)
    for sx in (1, -1):
        add(rtube([(sx * 0.03, -0.035, 1.47), (sx * 0.018, -0.04, 1.54), (sx * 0.035, -0.02, 1.61)], 0.008, "BH_Skin",
                  n=4), weights=KB.HEAD_W)
    # ---------------------------------------------------------------- head, hair, jaw icicles
    for prt in gaunt_head(body):
        add(prt, "head")
    for prt in hair_strands(body):
        add(prt, "head")
    jaw = [(0.055 * math.sin(a), -0.068 * math.cos(a) + 0.006, 1.6 + 0.012 * abs(math.sin(a)))
           for a in np.linspace(-1.2, 1.2, 7)]
    for prt in icicles(jaw, 0.1, seed=5, r=0.009):
        add(prt, "head")
    add(ice_chunk((0.05, -0.02, 1.795), (0.035, 0.03, 0.02), 7, axis=(0.4, -0.3, 1)), "head")   # frost on the scalp
    # ---------------------------------------------------------------- arms
    for s in ("L", "R"):
        KB.bare_arm(sb, s, skin="BH_Skin", r_up=0.041, r_fore=0.035, r_wrist=0.027)
        KB.add_fist(sb, s, "BH_Skin", "BH_Skin", gauntlet=False)
    KB.wrap_band(sb, "forearm.R", "hand.R", 0.55, 0.98, 0.037, "BH_Cloth_Primary", turns=2.5, width=0.026)
    # right elbow: icicles hanging behind the elbow
    el = body.head("forearm.R")
    for prt in icicles([el + (-0.012, 0.04, 0.0), el + (0.0, 0.045, -0.015), el + (0.01, 0.038, 0.01)], 0.1, seed=11,
                       r=0.009, down=(0, 0.5, -1)):
        add(prt, weights=lambda V: [{"upper_arm.R": 0.4, "forearm.R": 0.6}] * len(V))
    # left arm locked in ice: blocks along the upper arm and forearm, shards jutting out, elbow icicles
    ua, fa, ha = "upper_arm.L", "forearm.L", "hand.L"
    sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
    du, df = normalize(el - sh), normalize(wr - el)
    add(ice_chunk(sh + (el - sh) * 0.55 + (0.012, 0.0, 0.0), (0.075, 0.08, 0.16), 21, axis=du), ua)
    add(ice_chunk(sh + (0.03, 0.0, 0.04), (0.085, 0.09, 0.07), 22, axis=(0.5, 0, 1)), ua)
    add(ice_chunk(el + (wr - el) * 0.5 + (0.01, 0.005, 0.0), (0.07, 0.075, 0.17), 23, axis=df), fa)
    add(ice_chunk(wr + df * 0.06, (0.065, 0.07, 0.075), 24, axis=df), ha)          # the fist frozen in a lump
    for (b, c, nrm, sz, sd) in ((ua, sh + (0.07, 0.0, 0.06), (1, 0.1, 0.9), 0.17, 31),
                                (ua, sh + (el - sh) * 0.6 + (0.06, 0.02, 0), (1, 0.3, 0.2), 0.12, 32),
                                (fa, el + (wr - el) * 0.4 + (0.05, -0.02, 0), (1, -0.4, 0.3), 0.13, 33),
                                (fa, el + (wr - el) * 0.7 + (0.02, 0.05, 0), (0.4, 1, 0.1), 0.1, 34)):
        for prt in shards(c, nrm, sz, sd, count=3, spread=26):
            add(prt, b)
    add(A.shard(sh + (0.08, 0.0, 0.08), (0.7, 0.0, 1.0), 0.14, 0.022, "BH_Emissive", sides=4), ua)
    for prt in icicles([el + (0.0, 0.07, -0.02), el + (0.03, 0.065, -0.03), el + (-0.02, 0.06, -0.035)], 0.14,
                       seed=13, r=0.012, down=(0, 0.45, -1)):
        add(prt, weights=lambda V: [{ua: 0.4, fa: 0.6}] * len(V))
    # ---------------------------------------------------------------- back ice crust
    yb = back_y(GAUNT, 0, 1.36)
    for (c, r, sd, ax) in (((0.02, yb + 0.03, 1.36), (0.13, 0.07, 0.14), 41, (0, 0.2, 1)),
                           ((0.1, yb + 0.02, 1.42), (0.08, 0.06, 0.09), 42, (0.6, 0.2, 1)),
                           ((-0.08, yb + 0.02, 1.27), (0.08, 0.055, 0.1), 43, (-0.3, 0.2, 1))):
        add(ice_chunk(c, r, sd, axis=ax), weights=CHEST_W)
    for (c, nrm, sz, sd) in (((0.06, yb + 0.07, 1.44), (0.35, 0.5, 1.0), 0.32, 51),
                             ((-0.06, yb + 0.07, 1.4), (-0.45, 0.6, 0.8), 0.26, 52),
                             ((0.0, yb + 0.08, 1.3), (0.0, 1.0, 0.4), 0.16, 53),
                             ((0.12, yb + 0.03, 1.2), (0.6, 0.7, 0.2), 0.12, 54)):
        for prt in shards(c, nrm, sz, sd, count=4, spread=24):
            add(prt, weights=CHEST_W)
    for (c, d, ln) in (((0.03, yb + 0.08, 1.42), (0.1, 0.5, 1.0), 0.2), ((-0.04, yb + 0.08, 1.36), (-0.3, 0.8, 0.7),
                                                                         0.15)):
        add(A.shard(c, d, ln, ln * 0.14, "BH_Emissive", sides=4), weights=CHEST_W)
    # ---------------------------------------------------------------- burial rags
    # loin wrap (band) + ragged front / back panels
    V, F = KB.band(GAUNT, 0.93, 1.03, 0.022, 0.006, n=24)
    add(P(V, F, "BH_Cloth_Secondary", "loinwrap"), "hips")
    add(cloth_panel(GAUNT, 1.0, 0.56, lambda z: 0.1 + 0.05 * (1.0 - z), front=True, nu=7, nv=8, seed=2.2, rag=0.12,
                    teeth=4, gap=0.03, belt_z=1.0, mat="BH_Cloth_Primary"), weights=cloth_w(belt_z=1.0, leg=0.65))
    add(cloth_panel(GAUNT, 1.0, 0.5, lambda z: 0.13 + 0.04 * (1.0 - z), front=False, nu=7, nv=8, seed=5.1, rag=0.14,
                    teeth=5, gap=0.03, belt_z=1.0, mat="BH_Cloth_Primary"), weights=cloth_w(belt_z=1.0, leg=0.6))
    # burial shroud over the left shoulder, crossing to the right hip (front and back), ragged tail at the hip
    g = 0.02
    for front in (True, False):
        pts, ups = [], []
        for t in np.linspace(0, 1, 8):
            x = 0.12 - 0.26 * t
            z = 1.47 - 0.46 * t
            y = (front_y(GAUNT, x, z) - g) if front else (back_y(GAUNT, x, z) + g + (0.05 if 1.2 < z < 1.46 else 0))
            pts.append((x, y, z))
            ups.append((0.15 * x, -1 if front else 1, 0))
        add(KB.strip(pts, 0.11, 0.008, "BH_Cloth_Primary", ups=ups), weights=TORSO_W)
    pts, ups = [], []
    for t in np.linspace(0, 1, 7):
        a = math.pi * (0.5 - t) * 0.95
        pts.append((0.125, -0.1 * math.sin(a) + 0.005, 1.47 + 0.05 * math.cos(a)))
        ups.append((0, -math.sin(a), math.cos(a)))
    add(KB.strip(pts, 0.12, 0.008, "BH_Cloth_Primary", ups=ups), "chest")
    for k, (x, ln) in enumerate(((-0.13, 0.26), (-0.17, 0.2))):
        top = np.array([x, front_y(GAUNT, x, 1.02) - 0.03, 1.02])
        add(A.rag_strip(top, (0.1 * k, -0.2, -1), ln, 0.07, "BH_Cloth_Primary", n=5, seed=k + 1.0, out=(0, -1, 0)),
            weights=cloth_w(belt_z=1.05, leg=0.5))
    # frost glaze patches on the rags
    for (x, z, sd) in ((0.05, 1.33, 61), (-0.09, 1.16, 62)):
        add(ice_chunk((x, front_y(GAUNT, x, z) - 0.03, z), (0.03, 0.012, 0.025), sd, axis=(0, -1, 0)),
            weights=TORSO_W)
    # ---------------------------------------------------------------- legs (thin skin, rag-bound feet)
    KB.trousers(sb, "BH_Skin", loose=0.72, end=0.72)
    for s in ("L", "R"):
        for prt, b in HS.boot(body, s, mat="BH_Cloth_Secondary", top=0.3, r=0.95, wrap_mat="BH_Cloth_Primary"):
            add(prt, b)
        # bony knee
        k = body.head("shin." + s)
        add(ball(k + (0, -0.045, 0.01), 0.03, "BH_Skin", 7, 4, (1.0, 0.7, 1.1)),
            weights=lambda V, s=s: [{"thigh." + s: 0.5, "shin." + s: 0.5}] * len(V))
    KB.wrap_band(sb, "thigh.L", "shin.L", 0.55, 0.85, 0.058, "BH_Cloth_Primary", turns=1.5, width=0.03)
    # right leg sheathed in ice: thigh block, knee block, shin block, shards
    th, sh_ = "thigh.R", "shin.R"
    hp, kn, an = body.head(th), body.head(sh_), body.tail(sh_)
    add(ice_chunk(hp + (kn - hp) * 0.62 + (-0.01, -0.01, 0), (0.085, 0.09, 0.15), 71, axis=normalize(kn - hp)), th)
    add(ice_chunk(kn + (-0.005, -0.03, 0.0), (0.085, 0.09, 0.08), 72, axis=(0, 0, 1)),
        weights=lambda V: [{th: 0.5, sh_: 0.5}] * len(V))
    add(ice_chunk(kn + (an - kn) * 0.5 + (0, -0.005, 0), (0.075, 0.08, 0.17), 73, axis=normalize(an - kn)), sh_)
    for (b, c, nrm, sz, sd) in ((th, hp + (kn - hp) * 0.5 + (-0.07, -0.02, 0), (-1, -0.3, 0.3), 0.14, 81),
                                (sh_, kn + (-0.06, -0.06, 0.0), (-0.8, -0.8, 0.5), 0.13, 82),
                                (sh_, kn + (an - kn) * 0.6 + (-0.05, 0.04, 0), (-0.6, 0.8, 0.1), 0.11, 83)):
        for prt in shards(c, nrm, sz, sd, count=3, spread=26):
            add(prt, b)
    # ---------------------------------------------------------------- weapon
    add_weapon(body, "R", broken_sword())


def broken_sword():
    """Old arming sword snapped a hand's width past mid-blade (slanted jagged break), frost crust along both edges, an
    ice spur growing out of the break like a new blade tip, icicles off the guard, rag-wrapped grip."""
    parts = []
    blade = WP._blade(0.1, 0.6, 0.05, 0.044, 0.006, tip=0.02, n_sec=10, mat="BH_Steel")

    def brk(v):
        x, y, z = v
        if z > 0.44:
            u = (x + 0.025) / 0.05                       # 0 at -X edge, 1 at +X edge
            zt = 0.44 + (0.16 - 0.1 * u) * (1.0 + 0.25 * math.sin(u * 17))
            z = 0.44 + (z - 0.44) / 0.16 * (zt - 0.44)
        return (x, y, z)
    blade.warp(brk)
    parts.append(blade)
    parts.append(M.bevel(WP._crossguard(0.09, 0.1, h=0.02, t=0.018, curve=0.012, mat="BH_DarkSteel"), 0.002, 1))
    parts.append(WP._grip(-0.085, 0.078, 0.0155, 5, mat="BH_Leather"))
    parts.append(WP._pommel(-0.1, 0.026, mat="BH_DarkSteel"))
    V, F = M.lathe([(0.0, -0.06), (0.019, -0.05), (0.02, 0.0), (0.019, 0.05), (0.0, 0.06)], 7)
    parts.append(P(V, F, "BH_Cloth_Primary", "gripwrap").scale((1.0, 1.0, 0.9)))
    # ice spur continuing the broken blade (slightly off-axis), glowing core shard
    parts.append(A.shard((0.004, 0.0, 0.52), (0.08, 0.0, 1.0), 0.3, 0.026, "BH_Stone", sides=5, twist=20))
    parts.append(A.shard((-0.01, 0.0, 0.54), (-0.15, 0.1, 1.0), 0.16, 0.016, "BH_Emissive", sides=4, twist=10))
    # frost crust on both edges + flats
    rng = np.random.default_rng(9)
    for sx in (1, -1):
        for z in np.linspace(0.16, 0.5, 6):
            c = np.array([sx * 0.021, 0.0, z])
            parts.append(A.ball(c, 0.014 + 0.008 * rng.random(), "BH_Stone", n=5, rings=3, scale=(0.9, 0.6, 1.5)))
    for sy in (1, -1):
        for z in (0.2, 0.33):
            parts.append(A.ball((0.0, sy * 0.005, z), 0.02, "BH_Stone", n=6, rings=3, scale=(1.0, 0.3, 1.8)))
    for sx in (1, -1):
        parts.append(A.taper([(sx * 0.08, 0.0, 0.085), (sx * 0.085, 0.0, 0.04), (sx * 0.088, 0.0, 0.0)], 0.009, 0.001,
                             "BH_Stone", n=4))
    return parts
