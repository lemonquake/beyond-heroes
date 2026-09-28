"""Barrow Jarl (bh-012, Builder D, Rimeglass Barrow elite shield warrior): a broad undead chieftain risen from his
frozen grave-mound. Skull face with cold blue eyes behind the spectacle face guard of a horned iron helm, a beard of
frozen braids (gold rings, icicle tips) spilling over the chest, a long coat of iron scale armour rimed white with
frost (scale skirt to the knee), a thick fur mantle frozen stiff and hung with icicles, a wide belt of gold rings,
fur-wrapped boots. Right hand: a bearded axe (weapon.R). Left hand: a round wooden shield painted with a faded
frost rune that still glows faintly (weapon.L, face -Y).

~2.1 m to the helm crown (K = 1.13 standard skeleton, broadened torso); the horns rise ~0.1 m higher.
Kit: enemy_hollow_soldier (Scaled, skull, cloth weights), enemy_bandit_cutthroat (SB helpers),
enemy_rime_husk (ice helpers)."""
import math
import numpy as np

import bh_mesh as M
import bh_weapons as WP
from bh_body import torso_loft, front_y, back_y, dome, fist, M_align_z, smoothstep, interp_rows
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
from char_knight import thick_band
import enemy_bandit_cutthroat as KB
import enemy_hollow_soldier as HS
from enemy_hollow_soldier import P, rtube, ball, Scaled, add_weapon, ragged, cloth_w
import enemy_rime_husk as RH
import kit_a_common as A

K = 1.13
PROPS = proportions(K)
PALETTE = "barrow_jarl"
PALETTE_COLORS = {
    "BH_DarkSteel": ((0.16, 0.18, 0.21), 0.85, 0.55, None, 0.0, 1.0),      # iron scales / helm
    "BH_Steel": ((0.46, 0.5, 0.54), 0.9, 0.42, None, 0.0, 1.0),            # axe edge, face guard
    "BH_Stone": ((0.84, 0.92, 0.97), 0.0, 0.25, None, 0.0, 1.0),           # white rime frost / icicles
    "BH_Fur": ((0.2, 0.18, 0.165), 0.0, 0.95, None, 0.0, 1.0),             # frozen grey-brown fur mantle
    "BH_Hair": ((0.8, 0.85, 0.9), 0.0, 0.6, None, 0.0, 1.0),               # frozen white braids
    "BH_Gold": ((0.72, 0.52, 0.2), 1.0, 0.35, None, 0.0, 1.0),             # belt rings, braid rings, bands
    "BH_Leather": ((0.07, 0.052, 0.042), 0.0, 0.72, None, 0.0, 1.0),
    "BH_Bone": ((0.56, 0.56, 0.53), 0.0, 0.62, None, 0.0, 1.0),            # cold skull
    "BH_Horn": ((0.6, 0.56, 0.48), 0.0, 0.5, None, 0.0, 1.0),              # helm horns
    "BH_Wood": ((0.13, 0.095, 0.07), 0.0, 0.8, None, 0.0, 1.0),            # shield planks, axe haft
    "BH_Cloth_Primary": ((0.24, 0.36, 0.47), 0.0, 0.85, None, 0.0, 1.0),   # faded frost-blue shield paint
    "BH_Cloth_Secondary": ((0.08, 0.09, 0.115), 0.0, 0.9, None, 0.0, 1.0),  # dark wool trousers
    "BH_Shadow": ((0.01, 0.018, 0.03), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((0.5, 0.85, 1.0), 0.0, 0.3, (0.45, 0.8, 1.0), 7.0, 1.0),  # cold eyes, shield rune
}
CLIPS = ["shield_bash", "axe_1", "axe_2", "axe_heavy", "war_cry"]
PREVIEW_HEIGHT = 2.5


def finish_mesh(mesh_ob):
    HS.enable_weapon_deform(mesh_ob)


ENV = [  # standard-space envelope of the scale coat (broad chest, thick waist)
    (0.86, 0.19, 0.13, 0.13, 0.0),
    (0.96, 0.185, 0.128, 0.126, 0.0),
    (1.05, 0.176, 0.126, 0.118, 0.02),
    (1.16, 0.172, 0.132, 0.114, 0.04),
    (1.25, 0.186, 0.148, 0.118, 0.08),
    (1.34, 0.2, 0.155, 0.124, 0.08),
    (1.43, 0.194, 0.14, 0.12, 0.04),
    (1.49, 0.156, 0.108, 0.104, 0.0),
    (1.535, 0.092, 0.072, 0.072, 0.0),
]
TORSO_W = KB.zspec_w([(1.0, "hips"), (1.1, "spine"), (1.2, "spine"), (1.3, "chest")])


def skirt_rows():
    return [(z, 0.19 + 0.1 * (0.98 - z), 0.13 + 0.08 * (0.98 - z), 0.13 + 0.1 * (0.98 - z), 0.0)
            for z in (0.98, 0.9, 0.8, 0.7, 0.6)]


# --------------------------------------------------------------------------------------------------- scale coat
def scale_plate(p, t, n, up, w, h, tilt=14.0, thick=0.007, mat="BH_DarkSteel"):
    """One pointed scale centred at p (top overlapped by the row above), tangent t, outward normal n."""
    t, n = normalize(t), normalize(n)
    u = normalize(np.asarray(up, float) - n * np.dot(up, n))
    ut = normalize(u - n * math.tan(math.radians(tilt)))       # bottom edge flares outward
    o = [(-w / 2, h / 2), (-w / 2, -h * 0.12), (0.0, -h / 2), (w / 2, -h * 0.12), (w / 2, h / 2)]
    V, F = M.prism(o, thick, axis="y")
    Vw = np.array([p + t * x + n * (-y) + ut * z for x, y, z in V])
    return P(Vw, F, mat, "scale")


def scale_rows(rows, z_top, z_bot, dz, n_around, g, w, h, fr=(0.0, 1.0), seed=0, tilt=14.0, pz=None):
    """Staggered rows of scales round the envelope rows; fr = ring fraction range (0 front, .25 left, .5 back)."""
    out = []
    zs = np.arange(z_top, z_bot - 1e-6, -dz)
    for i, z in enumerate(zs):
        k = n_around
        for j in range(k):
            f = fr[0] + (fr[1] - fr[0]) * (j + 0.5 * (i % 2) + 0.25) / k
            if fr != (0.0, 1.0) and not (fr[0] <= f <= fr[1]):
                continue
            q = KB.ring_frac(rows, max(z, rows[0][0]), g, [f - 0.004, f, f + 0.004])
            q[:, 2] = z
            tng = q[2] - q[0]
            nrm = np.array([q[1][0], q[1][1], 0.0]) - np.array([0.0, interp_rows(rows, z)[5]
                                                                if len(rows[0]) > 5 else 0.0, 0.0])
            nrm = normalize(np.cross(tng, (0, 0, 1)))
            if np.dot(nrm, q[1][:2].tolist() + [0]) < 0:
                nrm = -nrm
            out.append(scale_plate(q[1], tng, nrm, (0, 0, 1), w, h, tilt=tilt))
    return out


def rime_patch(c, nrm, size, seed, flat=0.35):
    """White rime frost: a few flattened lumps on a surface."""
    rng = np.random.default_rng(seed)
    n = normalize(nrm)
    out = []
    for k in range(2):
        off = (rng.random(3) - 0.5) * size
        off -= n * np.dot(off, n)
        b = A.ball((0, 0, 0), size * (0.45 + 0.3 * rng.random()), "BH_Stone", n=6, rings=3, scale=(1.0, 1.0, flat))
        b.V = b.V @ M_align_z(n).T + np.asarray(c, float) + off
        out.append(b)
    return out


# --------------------------------------------------------------------------------------------------- helm / head
def horned_helm(hz):
    """Iron dome helm with a gold brow band, crest ridge, spectacle face guard + nose bar, cheek plates, mail
    aventail at the back/sides and two big up-swept horns. hz = head bone z (standard 1.6)."""
    parts = []
    c = np.array([0.0, 0.012, 0.0])
    prof = [(0.0, 0.272), (0.05, 0.266), (0.088, 0.24), (0.11, 0.2), (0.12, 0.155), (0.122, 0.12)]
    V, F = M.lathe(prof, 18, cap=False)
    shell = P(V, F, "BH_DarkSteel", "helm").scale((1.0, 1.08, 1.0)).move(c + (0, 0, hz))
    parts.append(M.solidify(shell, 0.007, offset=1))
    V, F = M.lathe([(0.12, 0.1), (0.128, 0.104), (0.128, 0.132), (0.12, 0.136)], 18, cap=False)
    parts.append(P(V, F, "BH_Gold", "browband").scale((1.0, 1.08, 1.0)).move(c + (0, 0, hz)))
    pts = [(0, 0.012 + 1.08 * 0.126 * math.sin(a), hz + 0.14 + 0.13 * math.cos(a)) for a in np.linspace(-1.2, 1.3, 8)]
    parts.append(rtube(pts, 0.011, "BH_DarkSteel", n=5, up=(1, 0, 0)))
    # spectacle guard: two eye rings, a bridge, the nose bar
    ez = hz + 0.1
    for sx in (1, -1):
        ring = [(sx * 0.033 + 0.03 * math.cos(a), -0.128 + 0.012 * math.sin(a) ** 2, ez + 0.022 * math.sin(a))
                for a in np.linspace(0, 2 * math.pi, 13)]
        V, F = M.tube(ring, [(0.008, 0.006)] * len(ring), n=5, up=(0, -1, 0), cap0=False, cap1=False)
        parts.append(P(V, F, "BH_Steel", "spectacle"))
        # cheek plates
        V, F = M.grid(lambda u, v, sx=sx: (sx * (0.1 + 0.02 * u), -0.07 + 0.1 * u - 0.02 * v,
                                           hz + 0.12 - 0.11 * v - 0.02 * u), 4, 4)
        cp = P(V, F, "BH_DarkSteel", "cheek")
        if sx < 0:
            cp.flip()
        parts.append(M.solidify(cp, 0.007, offset=-1))
    V, F = M.tube([(0, -0.132, ez + 0.03), (0, -0.138, ez - 0.02), (0, -0.132, ez - 0.06)],
                  [(0.012, 0.005), (0.011, 0.005), (0.008, 0.004)], n=5, up=(0, -1, 0), p=3.0)
    parts.append(P(V, F, "BH_Steel", "nosebar"))
    # mail aventail (sides + back of the neck)
    def fn(u, v):
        a = math.radians(-120 + 240 * u)                  # 0 = back
        r = 0.122 + 0.05 * v
        return (r * math.sin(a), 0.012 + 1.08 * r * math.cos(a), hz + 0.11 - 0.14 * v)
    V, F = M.grid(fn, 11, 4)
    parts.append(M.solidify(P(V, F, "BH_DarkSteel", "aventail").flip(), 0.008, offset=-1))
    # horns: from the temples, out and up, tips curling forward; gold ring at the root
    for sx in (1, -1):
        pts = []
        for t in np.linspace(0, 1, 9):
            pts.append((sx * (0.105 + 0.19 * t - 0.04 * t ** 3), 0.02 - 0.05 * t ** 2,
                        hz + 0.17 + 0.05 * t + 0.2 * t ** 2.2))
        parts.append(A.taper(pts, 0.036, 0.004, "BH_Horn", n=7, power=1.3))
        parts.append(A.ball(pts[0], 0.04, "BH_Gold", n=8, rings=4, scale=(0.6, 1.0, 1.0)))
        for q, sz, sd in ((pts[3], 0.022, 1 + sx), (pts[6], 0.016, 5 + sx)):
            parts += rime_patch(np.asarray(q) + (0, 0, 0.02), (0.2 * sx, 0, 1), sz, sd)
    # rime on the dome
    parts += rime_patch((0.05, -0.06, hz + 0.24), (0.3, -0.6, 1), 0.035, 21)
    parts += rime_patch((-0.07, 0.05, hz + 0.22), (-0.4, 0.4, 1), 0.03, 22)
    return parts


def beard(hz):
    """Five frozen braids from the jaw spilling over the chest: bead chains (braid look), gold rings, icicle tips.
    Returns (part, is_upper) pairs."""
    out = []
    rng = np.random.default_rng(7)
    for k, x0 in enumerate((-0.05, -0.025, 0.0, 0.025, 0.05)):
        ln = 0.26 + 0.07 * (1 - abs(x0) / 0.05) + 0.02 * rng.random()
        top = np.array([x0, -0.075 + 0.02 * abs(x0) / 0.05, hz + 0.0])
        bot = np.array([x0 * 1.6, -0.19 - 0.02 * (1 - abs(x0) / 0.05), hz - ln])
        mid = (top + bot) / 2 + np.array([0, -0.035, 0])
        n = 8
        for i in range(n):
            t = i / (n - 1)
            q = (1 - t) ** 2 * top + 2 * (1 - t) * t * mid + t ** 2 * bot
            r = 0.02 * (1 - 0.35 * t)
            b = A.ball(q, r, "BH_Hair", n=5, rings=4, scale=(1.0, 0.8, 1.3))
            b.V = (b.V - q) @ Ry(25 * (1 if i % 2 else -1)).T + q
            out.append(b)
        for tr in (0.35, 0.78):
            q = (1 - tr) ** 2 * top + 2 * (1 - tr) * tr * mid + tr ** 2 * bot
            V, F = M.lathe([(0.0, -0.011), (0.022, -0.011), (0.022, 0.011), (0.0, 0.011)], 8)
            out.append(P(V, F, "BH_Gold", "braidring").move(q))
        out.append(A.taper([bot, bot + (0, -0.005, -0.05), bot + (0, 0, -0.09 - 0.03 * rng.random())], 0.012, 0.001,
                           "BH_Stone", n=4))
    # moustache / jaw mass under the face guard
    out.append(A.ball((0, -0.07, hz + 0.01), 0.055, "BH_Hair", n=8, rings=4, scale=(1.2, 0.6, 0.55)))
    return out


# --------------------------------------------------------------------------------------------------- mantle, belt
def fur_mantle():
    """Thick fur collar round the shoulders + a stiff frozen mantle down the back with an icicle hem.
    Returns (collar_parts, back_parts, hem points)."""
    collar = []
    rng = np.random.default_rng(3)
    loop = []
    for a in np.linspace(0, 2 * math.pi, 25):
        rx, ry = 0.215, 0.165
        z = 1.49 + 0.02 * math.cos(a) - 0.035 * max(0.0, -math.sin(a)) ** 2   # dips at the front
        loop.append((rx * math.cos(a), 0.01 + ry * math.sin(a), z))
    V, F = M.tube(loop, [(0.07, 0.055)] * len(loop), n=10, up=(0, 0, 1), cap0=False, cap1=False)
    V = V * (1 + 0.06 * np.sin(V[:, 0] * 71 + V[:, 1] * 53) * np.cos(V[:, 2] * 97))[:, None] \
        + np.array([0, 0, 0]) * 0
    collar.append(P(V, F, "BH_Fur", "collar"))
    for sx in (1, -1):         # big shoulder tufts
        collar.append(RH.ice_chunk((sx * 0.2, 0.01, 1.5), (0.11, 0.12, 0.07), 60 + sx, axis=(sx * 0.3, 0, 1),
                                   mat="BH_Fur", n=9, rings=5, jit=0.18))
    for k in range(10):        # rime on the collar top
        a = 2 * math.pi * k / 10 + rng.random() * 0.4
        c = (0.215 * math.cos(a), 0.01 + 0.165 * math.sin(a), 1.535 + 0.02 * math.cos(a))
        collar += rime_patch(c, (0.2 * math.cos(a), 0.2 * math.sin(a), 1), 0.035, 70 + k)
    back = []
    nu, nv = 9, 8

    def fn(u, v):
        half = 0.2 + 0.07 * v
        x = (u - 0.5) * 2 * half
        zb = 1.02 + ragged(u, 2.3, 0.1, 4)
        z = 1.49 + (zb - 1.49) * v
        yb = back_y(ENV, x * 0.9, max(min(z, 1.43), 1.16)) + 0.05 + 0.04 * v
        return (x, yb + 0.012 * math.sin(u * math.pi * 6) * v, z)
    V, F = M.grid(fn, nu, nv)
    back.append(M.solidify(P(V, F, "BH_Fur", "mantle"), 0.035, offset=1.0))
    hem = [np.array(fn(u, 1.0)) + (0, 0.02, 0.01) for u in np.linspace(0.05, 0.95, 8)]
    for (u, v, sd) in ((0.3, 0.2, 81), (0.7, 0.35, 82), (0.45, 0.6, 83), (0.8, 0.75, 84)):
        back += rime_patch(np.array(fn(u, v)) + (0, 0.04, 0), (0, 1, 0.2), 0.04, sd)
    return collar, back, hem


def ring_belt(z=1.02, h=0.07):
    parts = []
    V, F = thick_band(ENV, z, z + h, 0.034, 0.012, n=26)
    parts.append(M.bevel(P(V, F, "BH_Leather", "belt"), 0.003, 1))
    by = front_y(ENV, 0, z + h / 2) - 0.036
    V, F = M.box(0.1, 0.02, 0.085, center=(0, by, z + h / 2))
    parts.append(M.bevel(P(V, F, "BH_Gold", "buckle"), 0.008, 1))
    V, F = M.box(0.05, 0.022, 0.04, center=(0, by - 0.004, z + h / 2))
    parts.append(P(V, F, "BH_DarkSteel", "buckle_inset"))
    for k in range(10):        # gold rings threaded on the belt, hanging
        f = 0.07 + 0.86 * k / 9
        if abs(f - 0.0) < 0.05 or abs(f - 1.0) < 0.05:
            continue
        q = KB.ring_frac(ENV, z + 0.01, 0.045, [f - 0.01, f, f + 0.01])
        t = normalize(q[2] - q[0])
        nrm = normalize(np.array([q[1][0], q[1][1], 0]))
        c = q[1] + np.array([0, 0, -0.012])
        ring = [c + t * 0.026 * math.cos(a) + np.array([0, 0, 1]) * 0.026 * math.sin(a)
                for a in np.linspace(0, 2 * math.pi, 9)]
        V, F = M.tube(ring, [(0.0055, 0.0055)] * len(ring), n=4, up=tuple(nrm), cap0=False, cap1=False)
        parts.append(P(V, F, "BH_Gold", "beltring"))
    return parts


# --------------------------------------------------------------------------------------------------- weapons
def bearded_axe():
    """One-handed bearded war axe: dark ash haft with gold bands, iron head whose long beard hooks down, frost
    crust along the edge, rime on the cheek."""
    parts = []
    prof = [(0, -0.24), (0.022, -0.24), (0.025, -0.22), (0.019, -0.19), (0.018, 0.4), (0.019, 0.7), (0.015, 0.74),
            (0, 0.75)]
    V, F = M.lathe(prof, 8)
    parts.append(P(V, F, "BH_Wood", "haft"))
    parts.append(WP._grip(-0.13, 0.1, 0.0205, 6, mat="BH_Leather"))
    for z in (0.14, 0.44):
        V, F = M.lathe([(0.0, z - 0.012), (0.024, z - 0.012), (0.024, z + 0.012), (0.0, z + 0.012)], 8)
        parts.append(P(V, F, "BH_Gold", "band"))
    out = [(0.02, 0.6), (0.09, 0.61), (0.16, 0.67), (0.23, 0.74), (0.25, 0.64), (0.25, 0.52), (0.23, 0.4),
           (0.2, 0.3), (0.16, 0.28), (0.15, 0.34), (0.12, 0.44), (0.07, 0.52), (0.02, 0.54)]
    o = np.array(out)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    V, F = M.prism(M.resample_closed(o, 34), 0.034, axis="y")
    head = P(V, F, "BH_DarkSteel", "axehead")
    head.warp(lambda v: (v[0], v[1] * (1.0 - 0.82 * min(max((v[0] - 0.04) / 0.2, 0), 1)), v[2]))
    parts.append(M.bevel(head, 0.002, 1, angle=50))
    # bright edge
    edge = [(0.232, 0.0, 0.72), (0.245, 0.0, 0.64), (0.245, 0.0, 0.52), (0.226, 0.0, 0.4), (0.196, 0.0, 0.31)]
    parts.append(rtube(edge, 0.006, "BH_Steel", n=4))
    V, F = M.lathe([(0, 0.52), (0.03, 0.52), (0.032, 0.55), (0.032, 0.64), (0.027, 0.66), (0.0, 0.67)], 8)
    parts.append(P(V, F, "BH_DarkSteel", "socket"))
    rng = np.random.default_rng(5)
    for q in edge[1:]:
        parts.append(A.ball(np.array(q) + (-0.02, 0, 0), 0.016 + 0.006 * rng.random(), "BH_Stone", n=5, rings=3,
                            scale=(0.8, 0.9, 1.4)))
    parts.append(A.ball((0.12, 0.0, 0.56), 0.035, "BH_Stone", n=6, rings=3, scale=(1.2, 0.35, 0.9)))
    parts.append(A.taper([(0.17, 0.0, 0.3), (0.17, 0.0, 0.25), (0.172, 0.0, 0.21)], 0.01, 0.001, "BH_Stone", n=4))
    return parts


def rune_shield(r=0.4):
    """Round shield (weapon space: handle at origin, face -Y): planked wood disk painted faded frost blue, iron rim
    and domed boss, a faded frost rune (glowing faintly, BH_Emissive) painted round the boss, rime on the rim."""
    parts = []
    yf = -0.07                                # face plane

    def disk(profile, mat, name, n=28):
        V, F = M.lathe(profile, n)
        p = P(V, F, mat, name)
        return p.rot(Rx(90))                  # lathe +Z -> -Y (face direction)
    # wooden body (back at y ~ -0.045), painted face disk slightly in front
    parts.append(disk([(0.0, -yf - 0.024), (r, -yf - 0.02), (r, -yf), (0.0, -yf + 0.004)], "BH_Wood", "shield"))
    parts.append(disk([(0.0, -yf + 0.006), (r * 0.94, -yf + 0.002), (r * 0.94, -yf + 0.0005), (0.0, -yf + 0.0045)],
                      "BH_Cloth_Primary", "paint"))
    # plank seams
    for x in (-0.24, -0.12, 0.0, 0.12, 0.24):
        hz = math.sqrt(max(r * r * 0.88 - x * x, 0.0))
        V, F = M.box(0.006, 0.006, 2 * hz, center=(x, yf - 0.0045, 0.0))
        parts.append(P(V, F, "BH_Shadow", "seam"))
    # iron rim + boss
    rim = [(r * math.cos(a), yf + 0.008, r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 33)]
    V, F = M.tube(rim, [(0.016, 0.02)] * len(rim), n=6, up=(0, -1, 0), cap0=False, cap1=False)
    parts.append(P(V, F, "BH_DarkSteel", "rim"))
    parts.append(disk([(0.0, -yf + 0.075), (0.045, -yf + 0.065), (0.08, -yf + 0.03), (0.095, -yf + 0.008),
                       (0.1, -yf + 0.0), (0.0, -yf)], "BH_DarkSteel", "boss", n=16))
    V, F = M.lathe([(0.1, -yf + 0.0), (0.115, -yf + 0.003), (0.115, -yf + 0.012), (0.1, -yf + 0.012)], 16,
                   cap=False)
    parts.append(P(V, F, "BH_Gold", "bossring").rot(Rx(90)))
    for k in range(12):
        a = 2 * math.pi * k / 12
        parts.append(A.ball((0.36 * math.cos(a), yf - 0.004, 0.36 * math.sin(a)), 0.011, "BH_Gold", n=6, rings=3,
                            scale=(1, 0.6, 1)))
    # the frost rune: a stave above and below the boss, arrow-branch chevrons at both ends, a cross bar and
    # three snowflake spokes; drawn in broken strokes (faded paint), glowing faintly
    yr = yf - 0.0065
    strokes = [
        [(0.0, 0.13), (0.0, 0.3)], [(0.0, -0.13), (0.0, -0.3)],
        [(0.0, 0.27), (-0.09, 0.19)], [(0.0, 0.27), (0.09, 0.19)],
        [(0.0, -0.27), (-0.09, -0.19)], [(0.0, -0.27), (0.09, -0.19)],
        [(-0.3, 0.0), (-0.13, 0.0)], [(0.13, 0.0), (0.3, 0.0)],
        [(-0.25, -0.07), (-0.25, 0.07)], [(0.25, -0.07), (0.25, 0.07)],
        [(0.1, 0.1), (0.21, 0.21)], [(-0.1, -0.1), (-0.21, -0.21)], [(-0.1, 0.1), (-0.18, 0.18)],
    ]
    for i, st in enumerate(strokes):
        a, b = np.array(st[0]), np.array(st[1])
        if i in (1, 7, 11):      # faded: a gap in the stroke
            m1, m2 = a + (b - a) * 0.4, a + (b - a) * 0.62
            segs = [(a, m1), (m2, b)]
        else:
            segs = [(a, b)]
        for s0, s1 in segs:
            pts = [(s0[0], yr, s0[1]), ((s0[0] + s1[0]) / 2, yr, (s0[1] + s1[1]) / 2), (s1[0], yr, s1[1])]
            V, F = M.tube(pts, [(0.013, 0.003)] * 3, n=4, up=(0, -1, 0), p=3.0)
            parts.append(P(V, F, "BH_Emissive", "rune"))
    # rime on the rim / face edge + icicles under the rim
    for (a, sd) in ((1.9, 91), (3.6, 92), (5.4, 93), (0.4, 94)):
        parts += rime_patch((0.37 * math.cos(a), yf - 0.01, 0.37 * math.sin(a)), (0, -1, 0), 0.05, sd, flat=0.3)
    bot = [(0.39 * math.cos(a), yf + 0.005, 0.39 * math.sin(a)) for a in np.linspace(-2.2, -0.9, 5)]
    for prt in RH.icicles(bot, 0.08, seed=4, r=0.01):
        parts.append(prt)
    # grip (back side): bar across the boss hollow + arm strap
    V, F = M.tube([(-0.08, -0.035, 0.0), (-0.05, 0.02, 0.0), (0.05, 0.02, 0.0), (0.08, -0.035, 0.0)],
                  [(0.013, 0.035)] * 4, n=6, up=(0, 0, 1))
    parts.append(P(V, F, "BH_Leather", "handle"))
    V, F = M.box(0.3, 0.012, 0.05, center=(0, -0.04, 0.2))
    parts.append(P(V, F, "BH_Leather", "strap"))
    return parts


# --------------------------------------------------------------------------------------------------- build
def build(real):
    body = Scaled(real, K)
    sb = KB.SB(real, K)
    add = body.add
    hz = body.head("head")[2]
    # ---- skull, neck
    for prt in HS.skull(body, eye_mat="BH_Emissive", jaw_open=10.0):
        add(prt, "head")
    add(rtube([(0, 0.02, 1.47), (0, 0.01, 1.62)], 0.03, "BH_Bone", n=8), weights=HS.NECK_W)
    for prt in horned_helm(hz):
        add(prt, "head")
    bw = KB.zspec_w([(1.36, "chest"), (1.5, "neck"), (1.58, "head")])
    for prt in beard(hz):
        add(prt, weights=bw)
    # ---- scale coat: under-layer, torso scales, collar edge, rime
    V, F = torso_loft([r for r in ENV if r[0] >= 0.96], n=26, cap1=True)
    add(P(V, F, "BH_DarkSteel", "coat"), weights=TORSO_W)
    for prt in scale_rows(ENV, 1.47, 1.07, 0.056, 16, 0.004, 0.078, 0.074):
        add(prt, weights=TORSO_W)
    # scale skirt: front and back halves (legs move between them)
    SK = skirt_rows()
    cw = cloth_w(belt_z=1.0, leg=0.62)
    for fr in ((-0.2, 0.2), (0.3, 0.7)):
        for prt in scale_rows(SK, 0.97, 0.64, 0.058, 18, 0.004, 0.08, 0.078, fr=fr, tilt=10):
            prt.V[:, 0] = prt.V[:, 0]
            add(prt, weights=cw)
    # side mail under the skirt split (dark)
    for sx in (1, -1):
        V, F = M.grid(lambda u, v, sx=sx: (sx * (0.19 + 0.06 * v), -0.08 + 0.16 * u, 0.98 - 0.3 * v), 4, 4)
        pnl = P(V, F, "BH_DarkSteel", "sidemail")
        if sx < 0:
            pnl.flip()
        add(M.solidify(pnl, 0.008, offset=0.0), weights=cw)
    for (x, z, front, sd) in ((0.1, 1.38, True, 1), (-0.12, 1.2, True, 2), (0.05, 1.28, False, 3),
                              (-0.08, 0.84, True, 4), (0.14, 0.76, False, 5)):
        rows = ENV if z > 0.97 else SK
        y = front_y(rows, x, z) - 0.03 if front else back_y(rows, x, z) + 0.03
        for prt in rime_patch((x, y, z), (x * 2, -1 if front else 1, 0.3), 0.05, sd):
            add(prt, weights=TORSO_W if z > 0.97 else cw)
    # ---- mantle + belt
    collar, back, hem = fur_mantle()
    for prt in collar:
        add(prt, "chest")
    mw = KB.zspec_w([(1.12, "spine"), (1.3, "chest")])
    for prt in back:
        add(prt, weights=mw)
    for prt in RH.icicles(hem, 0.14, seed=17, r=0.013):
        add(prt, weights=mw)
    fr = [(0.215 * math.cos(a), 0.01 + 0.165 * math.sin(a) - 0.04, 1.44) for a in np.linspace(-2.4, -0.74, 6)]
    for prt in RH.icicles(fr, 0.09, seed=19, r=0.01):
        add(prt, "chest")
    for prt in ring_belt():
        add(prt, "hips")
    # ---- arms: scale sleeves, leather bracers with gold rings, iron gauntlets
    for s in ("L", "R"):
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        add(body.limb(ua, [(-0.05, 0.082, 0.084), (0.35, 0.074, 0.076), (0.95, 0.064, 0.066)], "BH_DarkSteel", n=12,
                      p=2.3), weights=body.seg_weights(["chest", "shoulder." + s, ua], power=9))
        Lu = body.p["upper_len"]
        for u in (0.18, 0.5):
            for k in range(6):
                a = 2 * math.pi * (k + 0.5 * (u > 0.3)) / 6
                q = body.lpt(ua, [(0.078 * math.cos(a), u * Lu, 0.078 * math.sin(a))])[0]
                d = normalize(body.tail(ua) - body.head(ua))
                nrm = normalize(q - (body.head(ua) + d * np.dot(q - body.head(ua), d)))
                add(scale_plate(q, np.cross(d, nrm), nrm, -d * 0 + d * -1.0, 0.08, 0.1, tilt=12), ua)
        el = body.head(fa)
        V, F = dome(el + (0, 0.03, 0), (0, 1, 0.1), 0.05, a_max=75, n=10, rings=4)
        add(M.solidify(P(V, F, "BH_DarkSteel", "couter"), 0.006, offset=-1),
            weights=lambda V, s=s: [{"upper_arm." + s: 0.5, "forearm." + s: 0.5}] * len(V))
        add(body.limb(fa, [(0.05, 0.058, 0.06), (0.5, 0.056, 0.058), (0.95, 0.05, 0.052)], "BH_Leather", n=12, p=2.3),
            fa)
        Lf = body.p["fore_len"]
        for u in (0.35, 0.7):
            V, F = M.tube(body.lpt(fa, [(0, (u - 0.03) * Lf, 0), (0, (u + 0.03) * Lf, 0)]), [(0.064, 0.066)] * 2, n=12,
                          up=(0, 0, 1))
            add(P(V, F, "BH_Gold", "armring"), fa)
        for prt in fist(body, s, "BH_DarkSteel", "BH_Leather", gauntlet=True, scale=1.12):
            add(prt, ha)
    # ---- legs: wool trousers, fur-wrapped boots with cross bindings
    for s in ("L", "R"):
        th, sh = "thigh." + s, "shin." + s
        add(body.limb(th, [(-0.02, 0.09, 0.094), (0.4, 0.084, 0.088), (0.95, 0.066, 0.07)], "BH_Cloth_Secondary",
                      n=12, p=2.2), weights=body.seg_weights([th, sh], power=10))
        add(body.limb(sh, [(0.0, 0.066, 0.07), (0.5, 0.062, 0.066)], "BH_Cloth_Secondary", n=12, p=2.2), sh)
        k, a = body.head(sh), body.tail(sh)
        V, F = M.tube([a + (0, 0.0, 0.02), a + (k - a) * 0.35, a + (k - a) * 0.62],
                      [(0.066, 0.072), (0.072, 0.078), (0.074, 0.08)], n=12, up=(0, -1, 0))
        V = V * (1 + 0.05 * np.sin(V[:, 2] * 90 + V[:, 0] * 40))[:, None] * np.array([1, 1, 1]) + \
            np.array([0, 0, 0])
        boot = P(V, F, "BH_Fur", "furboot")
        boot.V[:, 0] = boot.V[:, 0]
        add(boot, sh)
        for zf in (0.12, 0.3, 0.48):
            c = a + (k - a) * zf
            V, F = M.tube([c + (0, 0, -0.012), c + (0, -0.004, 0.012)], [(0.08, 0.086)] * 2, n=12, up=(0, -1, 0))
            add(P(V, F, "BH_Leather", "binding"), sh)
        for prt, b in HS.boot(body, s, mat="BH_Leather", top=0.12, r=1.12):
            add(prt, b)
        V, F = dome(k + (0, -0.04, 0.0), (0, -1, 0.15), 0.058, a_max=70, n=10, rings=4, scale=(1.1, 1.2, 0.8))
        add(M.solidify(P(V, F, "BH_DarkSteel", "kneecop"), 0.006, offset=-1),
            weights=lambda V, s=s: [{"thigh." + s: 0.5, "shin." + s: 0.5}] * len(V))
    # ---- weapons
    add_weapon(body, "R", bearded_axe())
    add_weapon(body, "L", rune_shield())
