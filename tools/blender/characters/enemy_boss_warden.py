"""Morthar, the Hollow Warden (boss, builder A): a towering knight in tarnished, gold-trimmed oath-plate. The
breastplate is split open down the middle over a hollow chest cavity (dark, a few ribs, a violet grave-light
burning inside). Cracked great helm under a crown with tall horn-like crest spikes, violet light behind the visor
slit. Layered pauldrons with violet channels, torn royal cape (cape bones) and tabard, a huge runed greatsword.
On the back plate, between the shoulder blades, a glowing rune: his weak point (BH_WeakPoint)."""
import math
import numpy as np

import bh_mesh as M
import bh_weapons as WP
from bh_body import Body, torso_loft, front_y, back_y, dome, fist, smoothstep, interp_rows
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import char_knight as KN
from char_knight import TORSO, rows_between, thick_band, arc_band
from char_mage import ring_frac
import enemy_hollow_soldier as HS
from enemy_hollow_soldier import P, rtube, ball, Scaled, add_weapon, dent, ragged

K = 2.0 / 1.8
PROPS = proportions(K)
EXTRA_BONES = [(n, tuple(np.array(h) * K), tuple(np.array(t) * K), par, z) for (n, h, t, par, z) in KN.CAPE_BONES]
PALETTE = "boss_warden"
PALETTE_COLORS = {
    "BH_Steel": ((0.30, 0.31, 0.33), 1.0, 0.42, None, 0.0, 1.0),          # tarnished oath-plate
    "BH_DarkSteel": ((0.08, 0.08, 0.10), 1.0, 0.5, None, 0.0, 1.0),
    "BH_Gold": ((0.50, 0.36, 0.14), 1.0, 0.38, None, 0.0, 1.0),           # aged gold trim
    "BH_Cloth_Primary": ((0.075, 0.025, 0.09), 0.0, 0.88, None, 0.0, 1.0),  # royal violet-black
    "BH_Leather": ((0.05, 0.035, 0.03), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Bone": ((0.45, 0.41, 0.33), 0.0, 0.62, None, 0.0, 1.0),
    "BH_Shadow": ((0.03, 0.02, 0.045), 0.0, 0.8, (0.06, 0.02, 0.1), 0.4, 1.0),
    "BH_Emissive": ((0.55, 0.25, 1.0), 0.0, 0.4, (0.6, 0.28, 1.0), 9.0, 1.0),
}
CLIPS = ["boss_sweep", "boss_slam", "boss_charge", "cast_heavy", "boss_roar", "boss_summon"]


def finish_mesh(mesh_ob):
    HS.enable_weapon_deform(mesh_ob)


def secondary(anim, frames):
    """The knight's cape logic, plus gravity for the long lower cape when the body lies/kneels face down: if the
    lower cape bone would point upward (hips raised in death_crumple etc.), fold it down at the cape.2 joint."""
    from bh_math import R_axis
    out = KN.secondary(anim, frames)
    d_rest = normalize(np.array([0.0, 0.09, -1.0]))
    down = np.array([0.0, 0.0, -1.0])
    for f, d in enumerate(out):
        W1 = frames[f][3]["chest"].R @ d["cape.1"]
        W2 = W1 @ d["cape.2"]
        d2 = W2 @ d_rest
        w = float(smoothstep(-0.55, 0.35, d2[2]))
        if w <= 1e-4:
            continue
        ax = np.cross(d2, down)
        if np.linalg.norm(ax) < 1e-6:
            ax = W1 @ np.array([1.0, 0, 0])
        ang = math.degrees(math.acos(float(np.clip(np.dot(d2, down), -1, 1)))) * 0.8 * w
        Rw = R_axis(normalize(ax), ang)
        d["cape.2"] = W1.T @ Rw @ W1 @ d["cape.2"]
    return out


def remat(parts, src, dst):
    for p in parts:
        if p.mat == src:
            p.mat = dst
    return parts


CHEST_W = KN.chest_spine_w(1.24, 1.30)


# --------------------------------------------------------------------------------------------------- weapon
def runed_greatsword():
    parts = WP.greatsword()
    for p in parts:
        if p.name == "blade":
            p.mat = "BH_DarkSteel"
        elif p.mat == "BH_Gold":
            pass
        p.scale((1.12, 1.12, 1.12))
    # violet rune dashes on both flats
    for sy in (1, -1):
        for i, z in enumerate(np.linspace(0.3, 1.25, 9)):
            h = 0.05 if i % 2 else 0.028
            V, F = M.box(0.012 if i % 3 else 0.03, 0.004, h, center=(0.0, sy * 0.0068, z))
            parts.append(P(V, F, "BH_Emissive", "rune"))
    return parts


# --------------------------------------------------------------------------------------------------- torso
def split_breastplate():
    """Breastplate open down the front between z 1.2 and the collar (jagged torn edges)."""
    zs = [1.215, 1.25, 1.29, 1.33, 1.37, 1.41, 1.45, 1.49, 1.53]
    nu = 30
    rings = []
    for k, z in enumerate(zs):
        t = smoothstep(1.2, 1.3, z)
        a0 = 0.012 + t * (0.075 + 0.03 * math.sin(k * 2.3) + 0.025 * (k % 2))
        rings.append(ring_frac(TORSO, z, 0.0, a0 + (1 - 2 * a0) * np.linspace(0, 1, nu)))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    return M.solidify(P(V, F, "BH_Steel", "breastplate"), 0.012, offset=1.0), rings


def cavity():
    parts = []
    rows = [(1.22, 0.12, 0.08, 0.07, 0.0), (1.3, 0.135, 0.095, 0.08, 0.0), (1.42, 0.13, 0.09, 0.08, 0.0),
            (1.5, 0.09, 0.06, 0.06, 0.0)]
    rings = [ring_frac(rows, r[0], 0.0, np.linspace(0.12, 0.88, 14)) for r in rows]
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    parts.append(P(V, F, "BH_Shadow", "cavity").flip())
    # the hollow heart: violet grave-light
    parts.append(ball((0, -0.06, 1.36), 0.06, "BH_Emissive", 10, 6, (1, 0.8, 1.25)))
    for zc, r in ((1.3, 0.03), (1.43, 0.028)):
        parts.append(ball((0.02 * (1 if zc > 1.35 else -1), -0.06, zc), r, "BH_Emissive", 6, 4))
    # ribs inside the cavity (inner arcs)
    for i, z in enumerate((1.44, 1.39, 1.34, 1.29)):
        for sx in (1, -1):
            pts = []
            for th in np.linspace(math.radians(40), math.radians(150), 6):
                pts.append((sx * 0.11 * math.sin(th), 0.02 + 0.075 * math.cos(th) - 0.02, z - 0.04 * (th / math.pi)))
            parts.append(rtube(pts, 0.007, "BH_Bone", n=4))
    return parts


def weak_rune():
    """Glowing rune on the back plate between the shoulder blades (BH_WeakPoint)."""
    parts = []
    zc = 1.36
    yb = back_y(TORSO, 0, zc) + 0.004
    ring = [(0.085 * math.cos(a), back_y(TORSO, 0.085 * math.cos(a), zc + 0.085 * math.sin(a)) + 0.022,
             zc + 0.085 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 21)]
    V, F = M.tube(ring, [(0.013, 0.008)] * len(ring), n=4, up=(0, 1, 0), cap0=False, cap1=False)
    parts.append(P(V, F, "BH_WeakPoint", "rune_ring"))
    for (x0, z0, x1, z1) in ((0, zc + 0.11, 0, zc - 0.12), (-0.06, zc + 0.03, 0.06, zc + 0.03),
                             (-0.04, zc - 0.05, 0.0, zc - 0.02), (0.04, zc - 0.05, 0.0, zc - 0.02)):
        pts = [(x, back_y(TORSO, x, z) + 0.024, z) for x, z in ((x0, z0), ((x0 + x1) / 2, (z0 + z1) / 2), (x1, z1))]
        parts.append(rtube(pts, 0.012, "BH_WeakPoint", n=4, up=(0, 1, 0)))
    # gold setting around it
    ring2 = [(0.11 * math.cos(a), back_y(TORSO, 0.11 * math.cos(a), zc + 0.11 * math.sin(a)) + 0.018,
              zc + 0.11 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 25)]
    V, F = M.tube(ring2, [(0.009, 0.006)] * len(ring2), n=4, up=(0, 1, 0), cap0=False, cap1=False)
    parts.append(P(V, F, "BH_Gold", "rune_set"))
    return parts


def crown_and_horns():
    parts = []
    zc = 1.80
    # crown band around the helm top
    V, F = M.lathe([(0.122, zc - 0.02), (0.128, zc - 0.018), (0.128, zc + 0.02), (0.122, zc + 0.022)], 20, cap=False)
    band = P(V, F, "BH_Gold", "crown").scale((1.0, 1.08, 1.0)).move((0, 0.008, 0))
    parts.append(M.solidify(band, 0.006, offset=-1))
    # crown points (one broken off)
    for k in range(8):
        a = 2 * math.pi * k / 8 - math.pi / 2
        if k == 3:
            continue
        h = 0.07 if k % 2 == 0 else 0.045
        c = np.array([0.125 * math.cos(a), 0.008 + 0.135 * math.sin(a), zc + 0.02])
        out = normalize(np.array([math.cos(a), math.sin(a), 0.0]))
        parts.append(rtube([c, c + np.array([0, 0, h]) + out * 0.015], 0.014, "BH_Gold", n=4, r1=0.002))
    # tall horn-like crest: two swept horns rising from the temples
    for sx in (1, -1):
        pts = []
        for t in np.linspace(0, 1, 8):
            pts.append((sx * (0.1 + 0.07 * t - 0.04 * t ** 2), 0.02 + 0.12 * t ** 1.6, zc + 0.01 + 0.3 * t - 0.05 * t ** 3))
        parts.append(rtube(pts, 0.03, "BH_DarkSteel", n=6, r1=0.004))
        # gold ring at the base
        parts.append(ball(pts[0], 0.034, "BH_Gold", 8, 4, (1, 1, 0.5)))
    # central crest blade
    pts = [(0, -0.05, zc + 0.05), (0, 0.03, zc + 0.2), (0, 0.1, zc + 0.24)]
    V, F = M.tube(pts, [(0.008, 0.05), (0.006, 0.05), (0.002, 0.01)], n=4, up=(0, -1, 0.5), p=3.0)
    parts.append(P(V, F, "BH_DarkSteel", "crestblade"))
    return parts


def torn_cape():
    """Two torn halves hanging from the shoulders; the tear between them leaves the weak-point rune bare."""
    nu, nv = 7, 13
    out = []
    for side in (1, -1):
        def fn(u, v, side=side):
            half = 0.22 + 0.1 * v
            gap = 0.125 * (1 - smoothstep(0.0, 0.42, v))        # tear width at the top, closes near z 1.12
            x = side * (gap + (half - gap) * u)
            zb = 0.3 + ragged(0.5 + side * 0.5 * u, 1.7, 0.28, 4)
            z = 1.47 + (zb - 1.47) * v
            if v < 0.2:
                yb = back_y(TORSO, x * 0.95, min(max(z, 1.3), 1.47)) + 0.05
            else:
                yb = back_y(TORSO, x * 0.95, 1.3) + 0.05
            y = yb + 0.08 * v ** 1.2 + 0.02 * math.sin(u * math.pi * 3.0 + side) * v
            y -= 0.06 * u ** 3 * (1 - v) ** 2
            return (x, y, z)
        V, F = M.grid(fn, nu, nv)
        p = P(V, F, "BH_Cloth_Primary", "cape")
        if side < 0:
            p.flip()
        out.append(M.solidify(p, 0.012, offset=1.0))
    return out


# --------------------------------------------------------------------------------------------------- build
def build(real: Body):
    body = Scaled(real, K, EXTRA_BONES)
    add = body.add
    # ---- torso
    bp, rings = split_breastplate()
    dent(bp, (-0.14, -0.1, 1.42), (1, 0.6, 0), 0.015, 0.035)
    add(bp, weights=CHEST_W)
    # gold edging along the torn edges
    for k in (0, -1):
        pts = np.array([r[k] for r in rings])[1:]
        add(rtube(pts, 0.008, "BH_Gold", n=4), weights=CHEST_W)
    for prt in cavity():
        add(prt, weights=CHEST_W)
    V, F = torso_loft(rows_between(TORSO, 0.99, 1.24, n_extra=2), n=26, cap0=True)
    add(P(V, F, "BH_Steel", "plackart"), weights=KN.spine_hips_w(1.0, 1.04))
    V, F = thick_band(TORSO, 1.212, 1.232, 0.012, 0.0, n=26)
    add(P(V, F, "BH_Gold", "rim"), weights=CHEST_W)
    prof = [(0.158, 1.45), (0.135, 1.49), (0.098, 1.527), (0.084, 1.565), (0.074, 1.565), (0.088, 1.527),
            (0.125, 1.49), (0.148, 1.45), (0.158, 1.45)]
    V, F = M.lathe(prof, 20)
    add(P(V, F, "BH_DarkSteel", "gorget").scale((1.0, 0.85, 1.0)), "chest")
    for prt in weak_rune():
        add(prt, "chest")
    # belt, faulds, tabard strips
    V, F = thick_band(TORSO, 1.02, 1.07, 0.03, 0.012, n=26)
    add(P(V, F, "BH_Leather", "belt"), "hips")
    by = front_y(TORSO, 0, 1.045) - 0.032
    V, F = M.box(0.07, 0.016, 0.06, center=(0, by, 1.045))
    add(M.bevel(P(V, F, "BH_Gold", "buckle"), 0.005, 1), "hips")
    for side_a in ((0.12, 0.38), (0.62, 0.88)):
        for i in range(3):
            z1 = 1.025 - 0.045 * i
            V, F = arc_band(TORSO, z1 - 0.06, z1, 0.035 + 0.018 * i, side_a[0], side_a[1], n=10)
            lame = P(V, F, "BH_Steel", "fauld")
            lame.warp(lambda v, z1=z1: (v[0] * (1 + 0.25 * (z1 - v[2])), v[1] * (1 + 0.25 * (z1 - v[2])), v[2]))
            add(M.solidify(lame, 0.006, offset=1.0), weights=body.skirt_weights(1.0, 0.8, max_leg=0.35, center_w=0.05))
    V, F = torso_loft([(0.97, 0.162, 0.112, 0.108, 0.0), (0.86, 0.176, 0.118, 0.115, 0.0),
                       (0.76, 0.185, 0.12, 0.118, 0.0)], n=26)
    add(P(V, F, "BH_DarkSteel", "mailskirt"), weights=body.skirt_weights(0.98, 0.76, max_leg=0.8))
    for front in (True, False):
        add(HS.cloth_panel(TORSO, 1.03, 0.36, lambda z: 0.1 + 0.03 * (1.03 - z), front=front, nu=7, nv=10,
                           seed=0.9 if front else 2.6, rag=0.16, teeth=3, gap=0.03, belt_z=1.03),
            weights=HS.cloth_w(belt_z=1.03))

    # ---- legs (plate)
    for s in ("L",):
        th, sh = "thigh." + s, "shin." + s
        am = body.add_mirror
        am(M.bevel(body.limb(th, [(-0.02, 0.085, 0.09), (0.3, 0.084, 0.088), (0.93, 0.064, 0.068)], "BH_Steel", n=12,
                             p=2.4), 0.003, 1, angle=50), th)
        k = body.head(sh)
        V, F = dome(k + (0, -0.045, 0.0), (0, -1, 0.15), 0.064, a_max=78, n=12, rings=4)
        am(M.solidify(P(V, F, "BH_Steel", "poleyn"), 0.007, offset=-1),
           weights=lambda V, th=th, sh=sh: [{th: 0.5, sh: 0.5}] * len(V))
        V, F = dome(k + (0, -0.1, 0.0), (0, -1, 0.1), 0.02, a_max=85, n=8, rings=2)
        am(P(V, F, "BH_Gold", "kneeboss"), weights=lambda V, th=th, sh=sh: [{th: 0.5, sh: 0.5}] * len(V))
        am(M.bevel(body.limb(sh, [(0.03, 0.062, 0.064), (0.3, 0.068, 0.072), (0.85, 0.05, 0.052), (1.0, 0.054, 0.056)],
                             "BH_Steel", n=12, p=2.3), 0.003, 1, angle=50), sh)
        for part, bone in KN.sabaton(body, s):
            am(part, bone)

    # ---- arms (plate, big pauldrons with violet channels)
    for s in ("L",):
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        am = body.add_mirror
        am(body.limb(ua, [(0.35, 0.064, 0.066), (0.95, 0.055, 0.057)], "BH_Steel", n=12, p=2.3), ua)
        el = body.head(fa)
        V, F = dome(el + (0.0, 0.03, 0.0), (0, 1, 0.1), 0.055, a_max=80, n=12, rings=4)
        am(M.solidify(P(V, F, "BH_Steel", "couter"), 0.006, offset=-1),
           weights=lambda V, ua=ua, fa=fa: [{ua: 0.5, fa: 0.5}] * len(V))
        am(body.limb(fa, [(0.1, 0.052, 0.054), (0.5, 0.05, 0.052), (0.93, 0.044, 0.046)], "BH_Steel", n=12, p=2.3), fa)
        cuff = body.limb(fa, [(0.8, 0.048, 0.05), (1.0, 0.062, 0.062), (1.1, 0.068, 0.066)], "BH_Gold", n=12,
                         cap0=False, cap1=False)
        am(M.solidify(cuff, 0.005, offset=1.0), ha)
        for prt in fist(body, s, "BH_Steel", "BH_DarkSteel", scale=1.08):
            am(prt, ha)
        pd = remat(KN.pauldron(body, s), "BH_Aether", "BH_Emissive")
        for prt in pd:
            prt.scale((1.15, 1.15, 1.15), center=body.head(ua))
            am(prt, ua)
        # spikes on the pauldron crowns
        sh_ = body.head(ua)
        for dy in (-0.05, 0.0, 0.05):
            base = sh_ + np.array([0.04, dy, 0.13])
            am(rtube([base, base + np.array([0.03, 0, 0.09 - 0.025 * abs(dy) / 0.05])], 0.018, "BH_DarkSteel", n=5,
                     r1=0.002), ua)

    # ---- helm: the knight's great helm (no plume) cracked, with violet eyes, crown and horns
    helm = [p for p in KN.helm(body) if p.name not in ("crest", "crest_base")]
    for p in helm:
        if p.name == "helm_up":
            dent(p, (0.06, -0.1, 1.78), (-0.4, 1, 0), 0.02, 0.03)
        add(p, "head")
    for sx in (1, -1):
        add(ball((sx * 0.036, -0.116, 1.706), 0.016, "BH_Emissive", 6, 4, (1.5, 0.5, 0.75)), "head")
    # crack running down from the crown (dark)
    add(rtube([(0.05, -0.117, 1.84), (0.07, -0.12, 1.79), (0.055, -0.128, 1.745), (0.075, -0.126, 1.724)], 0.005,
              "BH_Emissive", n=4, up=(0, -1, 0)), "head")
    for prt in crown_and_horns():
        add(prt, "head")

    # ---- cape
    for half in torn_cape():
        add(half, weights=KN.cape_w())

    # ---- weapon
    add_weapon(body, "R", runed_greatsword())
