"""Ossric Vael, the Drowned Bell (bh-012, Builder A; Saltmouth Deeps BOSS): a drowned knight-commander in barnacled
green-bronze plate. His signature: the head is enclosed in an ancient sunken bronze bell worn as a cage-helm, a
cross-shaped slit in its face burning teal and teal light spilling from inside the bell's mouth, weed and short chain
lengths hanging from the rim, a hanging-loop (canon) on the crown. Layered verdigris pauldrons crusted with barnacles,
kelp trailing from the shoulders, a tattered deep-green sea-cloak (cape bones) with a ragged weed-hung hem, a torn
tabard, chains hanging from the belt. Weapon (rigid on weapon.R, spear clips): a halberd whose head is a small anchor
fused with an axe blade (crescent blade on +X, anchor arm + fluke hooking back on -X, the shank rising into a spike).
Author ~2.3 m to the bell's crown (the game scales it ~1.9x). Kit: char_knight plate via enemy_hollow_soldier.Scaled
(the frost_revenant / boss_warden layout), kit_deeps."""
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
import kit_deeps as D

K = 2.3 / 1.98
PROPS = proportions(K)
EXTRA_BONES = [(n, tuple(np.array(h) * K), tuple(np.array(t) * K), par, z) for (n, h, t, par, z) in KN.CAPE_BONES]
PALETTE = "bell_warden"
PALETTE_COLORS = {
    "BH_Steel": ((0.24, 0.3, 0.22), 0.75, 0.5, None, 0.0, 1.0),            # green-bronze plate
    "BH_Bronze": ((0.36, 0.3, 0.16), 0.9, 0.42, None, 0.0, 1.0),           # the bell (old bronze)
    "BH_Gold": ((0.17, 0.3, 0.24), 0.35, 0.6, None, 0.0, 1.0),             # verdigris trim
    "BH_DarkSteel": ((0.06, 0.08, 0.075), 0.8, 0.55, None, 0.0, 1.0),
    "BH_Rust": ((0.27, 0.14, 0.07), 0.45, 0.8, None, 0.0, 1.0),            # chains
    "BH_Cloth_Primary": ((0.04, 0.1, 0.09), 0.0, 0.85, None, 0.0, 1.0),    # deep sea-green cloak / tabard
    "BH_Leather": ((0.06, 0.055, 0.045), 0.0, 0.75, None, 0.0, 1.0),
    "BH_Bone": ((0.72, 0.72, 0.66), 0.0, 0.85, None, 0.0, 1.0),            # barnacles
    "BH_Fur": ((0.06, 0.15, 0.07), 0.0, 0.55, None, 0.0, 1.0),             # kelp / weed
    "BH_Wood": ((0.1, 0.09, 0.07), 0.0, 0.75, None, 0.0, 1.0),             # halberd haft
    "BH_Shadow": ((0.01, 0.02, 0.025), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": D.TEAL,                                                 # bell slit / mouth glow
}
CLIPS = ["spear_1", "spear_2", "spear_heavy", "boss_sweep", "boss_slam", "boss_charge", "boss_roar", "boss_summon",
         "cast_heavy"]
PREVIEW_HEIGHT = 2.7


def finish_mesh(mesh_ob):
    HS.enable_weapon_deform(mesh_ob)


secondary = BW.secondary

TB = [(r[0], r[1] * 1.08 + 0.01, r[2] * 1.06 + 0.008, r[3] * 1.08 + 0.01, r[4]) for r in TORSO]
CHEST_W = KN.chest_spine_w(1.24, 1.30)
TR = {"BH_Aether": "BH_Emissive"}

# the bell (r, z): open mouth at the bottom resting just above the gorget, crown on top
BELL = [(0.198, 1.535), (0.203, 1.55), (0.19, 1.585), (0.165, 1.64), (0.145, 1.7), (0.136, 1.76), (0.132, 1.82),
        (0.124, 1.87), (0.1, 1.905), (0.06, 1.922), (0.0, 1.926)]
BELL_CY = 0.01


def bell_r(z):
    zs = [p[1] for p in BELL]
    rs = [p[0] for p in BELL]
    return float(np.interp(z, zs, rs))


def remat(parts, table):
    for p in parts:
        p.mat = table.get(p.mat, p.mat)
    return parts


# --------------------------------------------------------------------------------------------------- bell helm
def bell_helm():
    parts = []
    V, F = M.lathe(BELL, 28, cap=False)
    shell = M.Part(V, F, "BH_Bronze", "bell").move((0, BELL_CY, 0))
    dent(shell, (0.1, -0.08 + BELL_CY, 1.8), (-1, 0.8, 0), 0.012, 0.035)
    parts.append(M.solidify(shell, 0.014, offset=-1.0))
    # raised bands (sound-bow lip, waist, shoulder)
    for z, dr in ((1.552, 0.008), (1.6, 0.005), (1.84, 0.006)):
        r = bell_r(z) + dr
        V, F = M.lathe([(r - 0.006, z - 0.012), (r, z - 0.008), (r, z + 0.008), (r - 0.006, z + 0.012)], 28, cap=False)
        parts.append(P(V, F, "BH_Gold", "bellband").move((0, BELL_CY, 0)))
    # canon: hanging loop on the crown (plane XZ) + a stub
    loop = [(0.045 * math.cos(a), BELL_CY, 1.965 + 0.04 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 13)]
    parts.append(rtube(loop, 0.014, "BH_Bronze", n=6, up=(0, 1, 0)))
    V, F = M.lathe([(0.0, 1.92), (0.04, 1.92), (0.03, 1.935), (0.0, 1.94)], 10)
    parts.append(P(V, F, "BH_Bronze", "canon_base").move((0, BELL_CY, 0)))
    # cross-shaped slit in the face: dark recess + glowing teal core (horizontal eye slit + a vertical drop)
    zs = 1.715
    for mat, w, off in (("BH_Shadow", 0.03, 0.001), ("BH_Emissive", 0.018, 0.004)):
        arc = []
        for a in np.linspace(-55, 55, 9):
            r = bell_r(zs) + off
            arc.append((r * math.sin(math.radians(a)), BELL_CY - r * math.cos(math.radians(a)), zs))
        V, F = M.tube(arc, [(0.005, w)] * len(arc), n=4, up=(0, 0, 1), p=3.0)
        parts.append(P(V, F, mat, "slit_h"))
        col = [(0.0, BELL_CY - bell_r(z) - off, z) for z in np.linspace(zs - 0.004, 1.585, 5)]
        V, F = M.tube(col, [(w * 0.75, 0.005)] * len(col), n=4, up=(0, -1, 0), p=3.0)
        parts.append(P(V, F, mat, "slit_v"))
    # glow flare at the slit ends (reads at gameplay distance)
    for sx in (1, -1):
        a = math.radians(40 * sx)
        r = bell_r(zs) + 0.005
        parts.append(ball((r * math.sin(a), BELL_CY - r * math.cos(a), zs), 0.016, "BH_Emissive", 6, 4, (1.3, 0.6, 0.9)))
    # teal light filling the inside of the mouth (inner band + a disc of light under the dark interior)
    V, F = M.lathe([(0.182, 1.53), (0.178, 1.57), (0.165, 1.6)], 28, cap=False)
    parts.append(P(V, F, "BH_Emissive", "mouth_glow").move((0, BELL_CY, 0)).flip())
    V, F = M.lathe([(0.0, 1.62), (0.16, 1.605)], 20)
    parts.append(P(V, F, "BH_Shadow", "inner_dark").move((0, BELL_CY, 0)).flip())
    # barnacles on the bell shoulder / flank, weed + chain stubs hanging from the rim
    for (a, z, n, sd) in ((130, 1.8, 7, 3), (-150, 1.66, 6, 4), (70, 1.62, 4, 5)):
        ar = math.radians(a)
        r = bell_r(z)
        c = np.array([r * math.sin(ar), BELL_CY - r * math.cos(ar), z])
        parts += D.barnacle_cluster(c, (math.sin(ar), -math.cos(ar), 0.3), 0.05, count=n, seed=sd, rmin=0.009,
                                    rmax=0.018, sides=5)
    rng = np.random.default_rng(9)
    for k in range(10):
        a = math.radians(-160 + 320 * k / 9 + 8 * rng.random())
        c = np.array([0.2 * math.sin(a), BELL_CY - 0.2 * math.cos(a), 1.54])
        out = np.array([math.sin(a), -math.cos(a), 0.0])
        if abs(math.degrees(a)) < 35:
            continue            # keep the front clear
        if k % 3 == 0:
            parts += chain_links(c + (0, 0, -0.005), c + out * 0.02 + (0, 0, -0.16), 0.022)
        else:
            parts += D.kelp(c, out * 0.3 + np.array([0, 0, -1.0]), 0.14 + 0.08 * rng.random(), 0.028, "BH_Fur",
                            out=out, amp=0.01, seed=k)
    return parts


def chain_links(a, b, size, mat="BH_Rust"):
    """Short hanging chain from a to b (alternating link planes)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = normalize(b - a)
    n = max(2, int(np.linalg.norm(b - a) / (size * 1.5)))
    x = normalize(np.cross(d, (0.3, 0.2, 0.9)))
    y = np.cross(d, x)
    out = []
    for i in range(n):
        c = a + d * size * 1.5 * (i + 0.5)
        pl = x if i % 2 else y
        loop = [c + d * size * math.cos(t) + pl * size * 0.55 * math.sin(t) for t in np.linspace(0, 2 * math.pi, 9)]
        V, F = M.tube(loop, [(size * 0.2, size * 0.2)] * 9, n=4, up=tuple(np.cross(d, pl)), cap0=False, cap1=False)
        out.append(P(V, F, mat, "link"))
    return out


# --------------------------------------------------------------------------------------------------- weapon
def anchor_halberd():
    """Weapon space (grip at origin, +Z to the head, axe edge +X). Haft -0.95..1.2, head ~1.05..1.62."""
    parts = []
    V, F = M.lathe([(0, -0.95), (0.016, -0.95), (0.022, -0.9), (0.021, 0.0), (0.02, 1.1), (0, 1.12)], 8)
    parts.append(P(V, F, "BH_Wood", "haft"))
    parts.append(WP._grip(-0.12, 0.12, 0.0225, 5, mat="BH_Leather"))
    parts.append(WP._grip(0.24, 0.46, 0.0225, 5, mat="BH_Leather"))
    V, F = M.lathe([(0, -1.02), (0.012, -1.02), (0.026, -0.96), (0.026, -0.88), (0, -0.87)], 8)
    parts.append(P(V, F, "BH_Steel", "butt"))
    # socket + langets
    V, F = M.lathe([(0, 1.0), (0.028, 1.0), (0.032, 1.05), (0.03, 1.2), (0.036, 1.24), (0, 1.25)], 10)
    parts.append(P(V, F, "BH_Steel", "socket"))
    # anchor shank rising into a spike, with a ring near the top
    V, F = M.tube([(0, 0, 1.22), (0, 0, 1.45), (0, 0, 1.58), (0, 0, 1.68)], [(0.026, 0.02), (0.022, 0.017),
                  (0.016, 0.012), (0.001, 0.001)], n=6, up=(0, -1, 0))
    parts.append(P(V, F, "BH_Steel", "shank"))
    # axe blade (crescent) on +X
    out = [(0.02, 1.16), (0.1, 1.13), (0.19, 1.08), (0.25, 1.1), (0.27, 1.2), (0.265, 1.3), (0.24, 1.4),
           (0.19, 1.43), (0.1, 1.38), (0.02, 1.36)]
    V, F = M.prism(M.resample_closed(out, 30)[::-1], 0.028, axis="y")
    head = P(V, F, "BH_Steel", "axe")
    head.warp(lambda v: (v[0], v[1] * (1.0 - 0.8 * min(max((v[0] - 0.05) / 0.22, 0), 1)), v[2]))
    parts.append(M.bevel(head, 0.002, 1, angle=50))
    # anchor arm curving down on -X, ending in a fluke (hooked back toward the haft)
    arm = [(-0.02, 0, 1.24), (-0.1, 0, 1.25), (-0.17, 0, 1.3), (-0.2, 0, 1.37)]
    V, F = M.tube(arm, [(0.024, 0.02), (0.022, 0.018), (0.02, 0.016), (0.018, 0.014)], n=6, up=(0, 1, 0))
    parts.append(P(V, F, "BH_Steel", "anchorarm"))
    fl = [(0.0, 0.0), (-0.07, 0.03), (-0.05, 0.13), (0.0, 0.16)]
    o = np.array(fl)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    V, F = M.prism(o, 0.018, axis="y")
    parts.append(M.bevel(P(V, F, "BH_Steel", "fluke").move((-0.2, 0, 1.3)), 0.003, 1))
    # verdigris collar bands, barnacles and a weed streamer
    for z in (0.96, 1.26):
        V, F = M.lathe([(0.0, z - 0.012), (0.034, z - 0.012), (0.036, z), (0.034, z + 0.012), (0, z + 0.012)], 10)
        parts.append(P(V, F, "BH_Gold", "band"))
    parts += D.barnacle_cluster((0.12, -0.015, 1.24), (0, -1, 0), 0.05, count=5, seed=71, rmin=0.008, rmax=0.015,
                                sides=5)
    parts += D.barnacle_cluster((-0.03, 0.02, 1.1), (-0.5, 1, 0), 0.035, count=3, seed=72, rmin=0.007, rmax=0.013,
                                sides=5)
    parts += D.kelp((-0.19, 0.0, 1.33), (-0.1, 0.1, -1.0), 0.3, 0.03, "BH_Fur", out=(0, -1, 0), amp=0.016)
    return parts          # (Scaled.add applies K)


# --------------------------------------------------------------------------------------------------- cloak
def sea_cloak():
    nu, nv = 11, 13

    def fn(u, v):
        half = 0.24 + 0.12 * v
        x = (u - 0.5) * 2 * half
        zb = 0.24 + ragged(u, 5.1, 0.3, 6)
        z = 1.47 + (zb - 1.47) * v
        if v < 0.2:
            yb = back_y(TB, x * 0.95, min(max(z, 1.3), 1.47)) + 0.05
        else:
            yb = back_y(TB, x * 0.95, 1.3) + 0.05
        y = yb + 0.08 * v ** 1.2 + 0.022 * math.sin(u * math.pi * 5.0) * v
        y -= 0.06 * (abs(u - 0.5) * 2) ** 3 * (1 - v) ** 2
        return (x, y, z)
    V, F = M.grid(fn, nu, nv)
    p = M.solidify(P(V, F, "BH_Cloth_Primary", "cloak"), 0.013, offset=1.0)
    hem = [fn(u, 1.0) for u in np.linspace(0.04, 0.96, 8)]
    return p, hem, fn


# --------------------------------------------------------------------------------------------------- build
def build(real: Body):
    body = Scaled(real, K, EXTRA_BONES)
    add = body.add
    am = body.add_mirror
    # ---- torso plate
    V, F = torso_loft(rows_between(TB, 1.215, 1.53, n_extra=3), n=28, cap1=True)
    bp = P(V, F, "BH_Steel", "breastplate")
    dent(bp, (-0.12, -0.14, 1.38), (1, 1, 0), 0.015, 0.04)
    add(M.bevel(bp, 0.004, 1, angle=50), weights=CHEST_W)
    V, F = torso_loft(rows_between(TB, 0.99, 1.30, scale=0.985, n_extra=2), n=28, cap0=True)
    add(P(V, F, "BH_Steel", "plackart"), weights=KN.spine_hips_w(1.0, 1.04))
    V, F = thick_band(TB, 1.212, 1.232, 0.012, 0.0, n=28)
    add(P(V, F, "BH_Gold", "rim"), weights=CHEST_W)
    prof = [(0.17, 1.45), (0.145, 1.49), (0.104, 1.527), (0.088, 1.57), (0.076, 1.57), (0.092, 1.527),
            (0.135, 1.49), (0.16, 1.45), (0.17, 1.45)]
    V, F = M.lathe(prof, 20)
    add(P(V, F, "BH_DarkSteel", "gorget").scale((1.0, 0.85, 1.0)), "chest")
    # an embossed verdigris anchor on the breastplate
    for pts in (((0, 1.46), (0, 1.3)), ((-0.05, 1.42), (0.05, 1.42))):
        q = [(x, front_y(TB, x, z) - 0.006, z) for x, z in pts]
        add(rtube(q, 0.01, "BH_Gold", n=5, up=(0, -1, 0)), weights=CHEST_W)
    arc = [(0.07 * math.sin(a), front_y(TB, 0.07 * math.sin(a), 1.33 - 0.05 * math.cos(a)) - 0.006,
            1.33 - 0.05 * math.cos(a)) for a in np.linspace(-1.4, 1.4, 7)]
    add(rtube(arc, 0.009, "BH_Gold", n=5, up=(0, -1, 0)), weights=CHEST_W)
    # barnacle crust on the chest / belly / back
    for (x, z, f, sd) in ((0.12, 1.26, 0, 1), (-0.1, 1.12, 0, 2)):
        c = np.array([x, front_y(TB, x, z) + 0.003, z])
        for prt in D.barnacle_cluster(c, (x * 2, -1, 0.1), 0.06, count=7, seed=sd, rmin=0.01, rmax=0.02, sides=5):
            add(prt, weights=CHEST_W if z > 1.22 else KN.spine_hips_w(1.0, 1.04))
    # ---- belt, faulds, mail skirt, torn tabard, hanging chains
    V, F = thick_band(TB, 1.02, 1.07, 0.03, 0.012, n=26)
    add(P(V, F, "BH_Leather", "belt"), "hips")
    by = front_y(TB, 0, 1.045) - 0.032
    V, F = M.box(0.08, 0.018, 0.07, center=(0, by, 1.045))
    add(M.bevel(P(V, F, "BH_Gold", "buckle"), 0.006, 1), "hips")
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
        add(HS.cloth_panel(TB, 1.03, 0.38, lambda z: 0.11 + 0.03 * (1.03 - z), front=front, nu=7, nv=9,
                           seed=2.3 if front else 3.9, rag=0.18, teeth=3, gap=0.03, belt_z=1.03),
            weights=HS.cloth_w(belt_z=1.03, leg=0.5))
    for frac in (0.2, 0.8):
        from char_mage import ring_frac
        q = ring_frac(TB, 1.03, 0.04, [frac])[0]
        for prt in chain_links(q, q + np.array([0.0, -0.02, -0.3]), 0.026):
            add(prt, weights=body.skirt_weights(1.02, 0.7, max_leg=0.5, center_w=0.05))
    # ---- legs
    for s in ("L",):
        th, sh = "thigh." + s, "shin." + s
        am(M.bevel(body.limb(th, [(-0.02, 0.092, 0.097), (0.3, 0.091, 0.095), (0.93, 0.07, 0.074)], "BH_Steel", n=12,
                             p=2.4), 0.003, 1, angle=50), th)
        k = body.head(sh)
        V, F = dome(k + (0, -0.05, 0.0), (0, -1, 0.15), 0.07, a_max=78, n=12, rings=4)
        am(M.solidify(P(V, F, "BH_Steel", "poleyn"), 0.008, offset=-1),
           weights=lambda V, th=th, sh=sh: [{th: 0.5, sh: 0.5}] * len(V))
        V, F = dome(k + (0, -0.11, 0.0), (0, -1, 0.1), 0.022, a_max=85, n=8, rings=2)
        am(P(V, F, "BH_Gold", "kneeboss"), weights=lambda V, th=th, sh=sh: [{th: 0.5, sh: 0.5}] * len(V))
        am(M.bevel(body.limb(sh, [(0.03, 0.068, 0.07), (0.3, 0.074, 0.078), (0.85, 0.055, 0.057), (1.0, 0.059, 0.061)],
                             "BH_Steel", n=12, p=2.3), 0.003, 1, angle=50), sh)
        for part, bone in KN.sabaton(body, s):
            part.scale((1.08, 1.06, 1.08), center=(body.head(th)[0], 0, 0))
            am(part, bone)
        for prt in D.barnacle_cluster(k + (0.03, -0.075, -0.18), (0.3, -1, 0), 0.045, count=5, seed=81, rmin=0.009,
                                      rmax=0.017, sides=5):
            am(prt, sh)
    # ---- arms: plate, big verdigris pauldrons with teal channels, barnacles and trailing kelp
    for s in ("L",):
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        am(body.limb(ua, [(0.3, 0.068, 0.07), (0.95, 0.058, 0.06)], "BH_Steel", n=12, p=2.3), ua)
        el = body.head(fa)
        V, F = dome(el + (0.0, 0.034, 0.0), (0, 1, 0.1), 0.06, a_max=80, n=12, rings=4)
        am(M.solidify(P(V, F, "BH_Steel", "couter"), 0.007, offset=-1),
           weights=lambda V, ua=ua, fa=fa: [{ua: 0.5, fa: 0.5}] * len(V))
        am(body.limb(fa, [(0.1, 0.056, 0.058), (0.5, 0.054, 0.056), (0.93, 0.048, 0.05)], "BH_Steel", n=12, p=2.3), fa)
        cuff = body.limb(fa, [(0.8, 0.052, 0.054), (1.0, 0.068, 0.068), (1.1, 0.074, 0.072)], "BH_Gold", n=12,
                         cap0=False, cap1=False)
        am(M.solidify(cuff, 0.005, offset=1.0), ha)
        for prt in fist(body, s, "BH_Steel", "BH_DarkSteel", scale=1.12):
            am(prt, ha)
        pd = remat(KN.pauldron(body, s), TR)
        for prt in pd:
            prt.scale((1.3, 1.25, 1.1), center=body.head(ua) + np.array([-0.03, 0.0, 0.0]))
            am(prt, ua)
        sh_ = body.head(ua)
        for prt in D.barnacle_cluster(sh_ + np.array([0.08, 0.0, 0.15]), (0.6, 0.1, 1.0), 0.09, count=11, seed=91,
                                      rmin=0.011, rmax=0.024, sides=5):
            am(prt, ua)
        for k in range(4):
            top = sh_ + np.array([0.13 + 0.03 * k, -0.07 + 0.05 * k, 0.07])
            for prt in D.kelp(top, (0.25, 0.1 * (k - 1.5), -1.0), 0.26 + 0.1 * (k % 2), 0.034, "BH_Fur",
                              out=(1, 0, 0.3), amp=0.018, seed=k):
                am(prt, ua)
    # ---- the bell helm
    for p in bell_helm():
        add(p, "head")
    # ---- cloak with weed on the hem
    cl, hem, cfn = sea_cloak()
    add(cl, weights=KN.cape_w())
    for i, q in enumerate(hem):
        if i % 2 == 0:
            for prt in D.kelp(np.array(q) + (0, 0.01, 0.02), (0, 0.1, -1), 0.14, 0.03, "BH_Fur", out=(0, 1, 0),
                              amp=0.01, seed=i):
                add(prt, weights=KN.cape_w())
    for (u, v, sd) in ((0.3, 0.2, 61), (0.72, 0.4, 62)):
        q = np.array(cfn(u, v)) + (0, 0.012, 0)
        for prt in D.barnacle_cluster(q, (0, 1, 0), 0.05, count=5, seed=sd, rmin=0.008, rmax=0.016, sides=5):
            add(prt, weights=KN.cape_w())
    # ---- weapon
    add_weapon(body, "R", anchor_halberd())
