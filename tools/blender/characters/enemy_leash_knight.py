"""Kharvenn Leash-Knight (bh-029, Builder M3, Zarael / the Heart Citadel elite): a Dominion knight who walks beside a
leashed giant. Heavy dark iron plate (a broad breastplate, plackart, faulds, full limb harness) trimmed with grey
iron and wound with rune-chains whose small rune plates glow white; a short black surcoat with a grey border; a
closed flat-topped great helm with a narrow eye slit, a white rune band round the brow and a CHAIN-VEIL (hanging
strands of chain) over the face; rounded pauldrons ringed with white runes, a rune-chain bandolier across the chest
and chains looped from the belt.

Right hand (weapon.R): a chain-flail: an iron haft with a rune-ringed head, a short chain held taut (the swing
carries it) and a spiked iron ball with white rune bands. Left hand (weapon.L, face -Y): a grey-painted iron kite shield
with a black chain-circle emblem (a ring of chain links round a black iron boss), a black rim.

~2.05 m to the helm top (standard skeleton x 1.12, bulkier plate). Built on the knight's plate kit (char_knight
parts, the mirror_knight harness) through enemy_hollow_soldier.Scaled. Clips: axe_1 axe_heavy shield_bash war_cry
whirlwind (+ axe_2, the enemy base set)."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, dome, fist, fan_plate
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import char_knight as KN
from char_knight import TORSO, rows_between, thick_band, arc_band
import enemy_hollow_soldier as HS
from enemy_hollow_soldier import P, rtube, Scaled, add_weapon
import enemy_mirror_knight as MK
import enemy_span_warden as SW
import kit_a_common as A

K = 1.12
PROPS = proportions(K)
PALETTE = "leash_knight"
PALETTE_COLORS = {
    "BH_Steel": ((0.24, 0.24, 0.255), 0.55, 0.45, None, 0.0, 1.0),           # dark iron plate
    "BH_Bronze": ((0.5, 0.5, 0.52), 0.6, 0.4, None, 0.0, 1.0),          # grey iron trim / chains / shield face
    "BH_Gold": ((0.03, 0.03, 0.034), 0.3, 0.6, None, 0.0, 1.0),          # blackened iron (emblem, rims)
    "BH_DarkSteel": ((0.12, 0.12, 0.13), 0.6, 0.5, None, 0.0, 1.0),       # mail, under-plates
    "BH_Cloth_Primary": ((0.028, 0.028, 0.032), 0.0, 0.92, None, 0.0, 1.0),  # black surcoat
    "BH_Cloth_Secondary": ((0.16, 0.16, 0.17), 0.0, 0.9, None, 0.0, 1.0),  # grey border
    "BH_Leather": ((0.07, 0.055, 0.045), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Stone": ((0.42, 0.42, 0.44), 0.2, 0.55, None, 0.0, 1.0),           # grey-painted iron shield face
    "BH_Shadow": ((0.012, 0.012, 0.014), 0.0, 0.85, None, 0.0, 1.0),
    "BH_Emissive": SW.WHITE_GLOW,                                           # the runes (white)
}
CLIPS = ["axe_1", "axe_heavy", "shield_bash", "war_cry", "whirlwind", "axe_2"]
PREVIEW_HEIGHT = 2.45

TB = [(r[0], r[1] * 1.13 + 0.012, r[2] * 1.1 + 0.01, r[3] * 1.12 + 0.012, r[4]) for r in TORSO]
CHEST_W = KN.chest_spine_w(1.24, 1.30)
HIPS_W = KN.spine_hips_w(1.0, 1.04)
REMAP = {"BH_Gold": "BH_Bronze", "BH_Aether": "BH_Emissive"}


def chain_links(pts, link=0.05, r=0.007, mat="BH_Bronze"):
    """Low-poly links (hexagonal, 3-sided wire: 36 triangles a link)."""
    return SW.chain_links(pts, link=link, r=r, mat=mat, sides=6, n=3)



def finish_mesh(mesh_ob):
    HS.enable_weapon_deform(mesh_ob)


def remat(parts, table=REMAP):
    for p in parts:
        p.mat = table.get(p.mat, p.mat)
    return parts


def rune_chain(pts, add_fn, link=0.046, r=0.0062, every=4, plate=0.016, nrm=None):
    """A rune-chain: grey iron links with a small white-glowing rune plate every few links."""
    pts = np.asarray(pts, float)
    links = chain_links(pts, link=link, r=r, mat="BH_Bronze")
    for p in links:
        add_fn(p)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    Lc = np.concatenate([[0], np.cumsum(seg)])
    n = len(links)
    for i in range(every // 2, n, every):
        t = (i + 0.5) * Lc[-1] / n
        j = min(int(np.searchsorted(Lc, t, side="right") - 1), len(seg) - 1)
        u = (t - Lc[j]) / max(seg[j], 1e-9)
        c = pts[j] * (1 - u) + pts[j + 1] * u
        d = normalize(pts[j + 1] - pts[j])
        nn = np.asarray(nrm if nrm is not None else (0, -1, 0), float)
        nn = normalize(nn - d * np.dot(nn, d))
        sd = np.cross(nn, d)
        V, F = M.box(plate * 1.5, plate * 0.45, plate * 1.0)
        R = np.stack([sd, nn, d], 1)
        add_fn(P(V @ R.T + c, F, "BH_DarkSteel", "runeplate"))
        V, F = M.box(plate * 0.9, plate * 0.2, plate * 0.55)
        add_fn(P(V @ R.T + c + nn * plate * 0.25, F, "BH_Emissive", "rune"))


def build(real):
    body = Scaled(real, K)
    add = body.add
    am = body.add_mirror
    # ---- torso plate (bulkier than the mirror knight)
    V, F = torso_loft(rows_between(TB, 1.215, 1.53, n_extra=3), n=28, cap1=True)
    add(M.bevel(P(V, F, "BH_Steel", "breastplate"), 0.004, 1, angle=50), weights=CHEST_W)
    V, F = torso_loft(rows_between(TB, 0.99, 1.30, scale=0.985, n_extra=2), n=28, cap0=True)
    add(P(V, F, "BH_Steel", "plackart"), weights=HIPS_W)
    V, F = thick_band(TB, 1.212, 1.232, 0.012, 0.0, n=28)
    add(P(V, F, "BH_Bronze", "rim"), weights=CHEST_W)
    V, F = thick_band(TB, 1.505, 1.525, 0.006, -0.01, n=28)
    add(P(V, F, "BH_Bronze", "rim2"), "chest")
    # gorget + mail coif
    prof = [(0.185, 1.45), (0.155, 1.49), (0.11, 1.527), (0.092, 1.575), (0.08, 1.575), (0.097, 1.527),
            (0.145, 1.49), (0.175, 1.45), (0.185, 1.45)]
    V, F = M.lathe(prof, 20)
    add(P(V, F, "BH_Steel", "gorget").scale((1.0, 0.85, 1.0)), "chest")
    V, F = M.lathe([(0.0, 1.46), (0.074, 1.47), (0.07, 1.56), (0.064, 1.6), (0.0, 1.6)], 12)
    add(P(V, F, "BH_DarkSteel", "coif").scale((1, 0.9, 1), center=(0, 0, 1.5)), "neck")
    # central ridge on the breastplate + grey edging
    ridge = [(0.0, front_y(TB, 0.0, z) - 0.004, z) for z in np.linspace(1.49, 1.24, 6)]
    add(rtube(ridge, 0.01, "BH_Bronze", n=5, up=(0, -1, 0)), weights=CHEST_W)
    for sx in (1, -1):
        pts = []
        for t in np.linspace(0, 1, 7):
            z = 1.47 - 0.24 * t
            x = sx * (0.16 + 0.03 * math.sin(math.pi * t))
            pts.append((x, front_y(TB, x, z) - 0.002, z))
        add(rtube(pts, 0.008, "BH_Bronze", n=5, up=(0, -1, 0)), weights=CHEST_W)
    # rune-chain bandolier across the chest (left shoulder -> right hip) and a chain round the breastplate rim
    pts = []
    for t in np.linspace(0, 1, 9):
        x = 0.15 - 0.3 * t
        z = 1.5 - 0.35 * t
        pts.append((x, front_y(TB, x, z) - 0.016, z))
    rune_chain(pts, lambda p: add(p, weights=CHEST_W))
    # ---- black surcoat (front + back) with a grey hem
    for front in (True, False):
        add(remat([MK.tabard(front)], {})[0], weights=HS.cloth_w(belt_z=1.03, leg=0.55))
        add(MK.tabard_hem(front), weights=HS.cloth_w(belt_z=1.03, leg=0.55))
    # ---- belt, faulds, mail skirt, chains looped from the belt
    V, F = thick_band(TB, 1.025, 1.072, 0.032, 0.012, n=28)
    add(M.bevel(P(V, F, "BH_Leather", "belt"), 0.003, 1), "hips")
    by = front_y(TB, 0, 1.048) - 0.036
    V, F = M.box(0.075, 0.018, 0.062, center=(0, by, 1.048))
    add(M.bevel(P(V, F, "BH_Bronze", "buckle"), 0.006, 1), "hips")
    add(P(*M.box(0.04, 0.008, 0.026, center=(0, by - 0.012, 1.048)), "BH_Emissive", "buckle_rune"), "hips")
    for side_a in ((0.12, 0.38), (0.62, 0.88)):
        for i in range(3):
            z1 = 1.025 - 0.05 * i
            V, F = arc_band(TB, z1 - 0.065, z1, 0.035 + 0.02 * i, side_a[0], side_a[1], n=10)
            lame = P(V, F, "BH_Steel" if i < 2 else "BH_Bronze", "fauld")
            lame.warp(lambda v, z1=z1: (v[0] * (1 + 0.3 * (z1 - v[2])), v[1] * (1 + 0.3 * (z1 - v[2])), v[2]))
            add(M.solidify(lame, 0.007, offset=1.0), weights=body.skirt_weights(1.0, 0.8, max_leg=0.35, center_w=0.05))
    V, F = torso_loft([(0.97, 0.18, 0.125, 0.12, 0.0), (0.86, 0.196, 0.132, 0.128, 0.0),
                       (0.76, 0.205, 0.134, 0.132, 0.0)], n=26)
    add(P(V, F, "BH_DarkSteel", "mailskirt"), weights=body.skirt_weights(0.98, 0.76, max_leg=0.8))
    for sx in (-1,):
        x0, x1 = sx * 0.17, sx * 0.21
        ya = front_y(TB, x0, 1.03) - 0.04
        loop = [(x0, ya, 1.03), (x0 + sx * 0.01, ya - 0.012, 0.93), (x0 + sx * 0.03, ya - 0.006, 0.88),
                (x1 + sx * 0.02, ya + 0.04, 0.93), (x1 + sx * 0.02, ya + 0.06, 1.03)]
        rune_chain(loop, lambda p: add(p, weights=body.skirt_weights(1.03, 0.85, max_leg=0.5, center_w=0.05)),
                   link=0.046, r=0.0055, every=3, plate=0.014)
    # ---- legs (mirrored)
    s = "L"
    th, sh = "thigh." + s, "shin." + s
    am(body.limb(th, [(-0.02, 0.088, 0.093), (0.4, 0.08, 0.085), (0.95, 0.06, 0.064)], "BH_DarkSteel", n=12), th)
    cu = body.limb(th, [(0.18, 0.1, 0.104), (0.24, 0.098, 0.102), (0.55, 0.09, 0.094), (0.93, 0.071, 0.075)],
                   "BH_Steel", n=14, p=2.4, offs=[(0, 0.004)] * 4)
    am(M.bevel(cu, 0.003, 1, angle=50), th)
    c0 = body.lpt(th, [(0, 0.2 * 0.43, 0)])[0]
    V, F = M.tube([c0 + (0, 0, 0.012), c0 + (0, 0, -0.006)], [(0.104, 0.108)] * 2, n=14, up=(0, -1, 0))
    am(P(V, F, "BH_Bronze", "cuisse_rim"), th)
    knee = body.head(sh)
    V, F = dome(knee + (0, -0.05, 0.0), (0, -1, 0.15), 0.07, a_max=78, n=14, rings=5)
    am(M.solidify(P(V, F, "BH_Bronze", "poleyn"), 0.008, offset=-1), weights=lambda V: [{th: 0.5, sh: 0.5}] * len(V))
    V, F = fan_plate(knee + (0.06, -0.01, 0.0), (1, 0, 0), (0, 0, 1), 0.06, 100, 260, n=8, thick=0.006)
    am(M.bevel(P(V, F, "BH_Steel", "kneefan"), 0.002, 1), weights=lambda V: [{th: 0.5, sh: 0.5}] * len(V))
    am(A.taper([knee + (0, -0.105, 0.0), knee + (0, -0.135, 0.01)], 0.014, 0.002, "BH_Bronze", n=5), sh)
    gr = body.limb(sh, [(0.03, 0.069, 0.071), (0.3, 0.075, 0.08), (0.55, 0.067, 0.069), (0.85, 0.055, 0.057),
                        (1.0, 0.059, 0.062)], "BH_Steel", n=14, p=2.3,
                   offs=[(0, 0.0), (0, -0.012), (0, -0.006), (0, 0.0), (0, 0.0)])
    am(M.bevel(gr, 0.003, 1, angle=50), sh)
    c1 = body.lpt(sh, [(0, 0.97 * 0.43, 0)])[0]
    V, F = M.tube([c1 + (0, 0, 0.012), c1 + (0, 0, -0.006)], [(0.065, 0.069)] * 2, n=14, up=(0, -1, 0))
    am(P(V, F, "BH_Bronze", "greave_rim"), sh)
    kx, ky, kz = knee
    ridge = [(kx, -0.086, kz - 0.09), (kx, -0.089, kz - 0.17), (kx, -0.077, kz - 0.26), (kx, -0.066, kz - 0.33)]
    am(rtube(ridge, 0.007, "BH_Bronze", n=5, up=(0, -1, 0)), sh)
    for part, bone in KN.sabaton(body, s):
        part.scale((1.12, 1.08, 1.1), center=(body.head(th)[0], 0, 0))
        am(remat([part])[0], bone)
    # ---- arms (mirrored)
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    am(body.limb(ua, [(-0.05, 0.066, 0.066), (0.5, 0.062, 0.064), (1.0, 0.054, 0.056)], "BH_DarkSteel", n=12), ua)
    rb = body.limb(ua, [(0.4, 0.071, 0.073), (0.44, 0.069, 0.071), (0.95, 0.06, 0.062)], "BH_Steel", n=12, p=2.3)
    am(M.bevel(rb, 0.003, 1, angle=50), ua)
    el = body.head(fa)
    V, F = dome(el + (0.0, 0.034, 0.0), (0, 1, 0.1), 0.06, a_max=80, n=12, rings=5)
    am(M.solidify(P(V, F, "BH_Bronze", "couter"), 0.007, offset=-1), weights=lambda V: [{ua: 0.5, fa: 0.5}] * len(V))
    V, F = fan_plate(el + (0.055, 0.012, 0.0), (1, 0, 0), (0, 0, 1), 0.056, 20, 200, n=8, thick=0.005)
    am(M.bevel(P(V, F, "BH_Steel", "couterfan"), 0.002, 1), weights=lambda V: [{ua: 0.5, fa: 0.5}] * len(V))
    am(A.taper([el + (0.0, 0.07, 0.0), el + (0.0, 0.11, -0.01)], 0.016, 0.002, "BH_Bronze", n=5), fa)
    vb = body.limb(fa, [(0.1, 0.057, 0.059), (0.5, 0.054, 0.056), (0.93, 0.046, 0.048)], "BH_Steel", n=12, p=2.3)
    am(M.bevel(vb, 0.003, 1, angle=50), fa)
    cuff = body.limb(fa, [(0.8, 0.052, 0.054), (1.0, 0.067, 0.067), (1.1, 0.073, 0.071)], "BH_Steel", n=12,
                     cap0=False, cap1=False)
    am(M.solidify(cuff, 0.005, offset=1.0), ha)
    V, F = M.tube([body.lpt(fa, [(0, 1.08 * 0.26, 0)])[0], body.lpt(fa, [(0, 1.11 * 0.26, 0)])[0]],
                  [(0.074, 0.072)] * 2, n=12, up=(0, -1, 0))
    am(P(V, F, "BH_Bronze", "cuffrim"), ha)
    for prt in fist(body, s, "BH_Steel", "BH_DarkSteel", scale=1.12):
        am(prt, ha)
    paul = KN.pauldron(body, s)
    lames = [p for p in paul if p.name == "lame"]
    for prt in remat([p for p in paul if p.name != "lame"] + lames[:2]):
        prt.scale((1.38, 1.3, 1.2), center=body.head(ua) + np.array([-0.03, 0.0, 0.0]))
        am(prt, ua)
    # ---- helm with the chain-veil
    for prt in great_helm():
        add(prt, "head")
    # ---- weapons
    add_weapon(body, "R", chain_flail())
    add_weapon(body, "L", kite_shield())


# --------------------------------------------------------------------------------------------------- helm
HELM = [(1.552, 0.11, 0.122, 0.12, 0.08), (1.6, 0.116, 0.13, 0.125, 0.1), (1.66, 0.12, 0.134, 0.128, 0.1),
        (1.72, 0.12, 0.134, 0.128, 0.06), (1.78, 0.118, 0.13, 0.126, 0.03), (1.83, 0.112, 0.122, 0.12, 0.0),
        (1.855, 0.1, 0.108, 0.108, 0.0), (1.865, 0.07, 0.075, 0.075, 0.0)]
HCY = 0.008
HELM_C = [h + (HCY,) for h in HELM]


def great_helm():
    """Closed, flat-topped great helm of dark iron: a narrow eye slit and breaths, a white rune band at the brow,
    a grey crown rim with short spikes, and the chain-veil: strands of chain hanging over the face from the brow."""
    parts = []
    V, F = torso_loft(HELM_C, n=28, p=2.6, cap0=False, cap1=True)
    parts.append(M.bevel(P(V, F, "BH_Steel", "helm"), 0.003, 1, angle=55))
    # vertical ridge down the face
    ridge = [(0.0, front_y(HELM_C, 0.0, z, p=2.6) - 0.004, z) for z in np.linspace(1.84, 1.57, 7)]
    parts.append(rtube(ridge, 0.009, "BH_Bronze", n=5, up=(0, -1, 0)))
    # eye slit (dark) across the front
    for sx in (1, -1):
        sl = [(sx * x, front_y(HELM_C, sx * x, 1.715, p=2.6) - 0.002, 1.715) for x in np.linspace(0.015, 0.1, 5)]
        parts.append(rtube(sl, 0.006, "BH_Shadow", n=4))
    # crown: grey rim, white rune band below it, short spikes round the top
    V, F = thick_band(HELM, 1.82, 1.85, 0.01, -0.002, n=28, p=2.6)
    parts.append(P(V, F, "BH_Bronze", "crownrim"))
    V, F = thick_band(HELM, 1.758, 1.772, 0.004, -0.001, n=28, p=2.6)
    parts.append(P(V, F, "BH_Gold", "runeband"))
    for k in range(12):
        a = 2 * math.pi * (k + 0.5) / 12
        if math.sin(a) < -0.85:
            continue                                 # gap at the front for the veil hook
        q = np.array([0.118 * math.cos(a), HCY + 0.13 * math.sin(a), 1.765])
        nrm = normalize(np.array([math.cos(a), math.sin(a), 0.0]))
        V, F = M.box(0.018, 0.006, 0.01)
        R = np.stack([np.cross((0, 0, 1), nrm), nrm, (0, 0, 1)], 1)
        parts.append(P(V @ R.T + q + nrm * 0.005, F, "BH_Emissive", "rune"))
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8
        base = np.array([0.1 * math.cos(a), HCY + 0.11 * math.sin(a), 1.855])
        parts.append(A.taper([base, base + np.array([0.02 * math.cos(a), 0.02 * math.sin(a), 0.055])], 0.012, 0.002,
                             "BH_Bronze", n=5))
    # chain-veil: strands hanging from a brow bar over the eye slit down past the chin
    bar = [(x, front_y(HELM_C, x, 1.77, p=2.6) - 0.014, 1.77) for x in np.linspace(-0.11, 0.11, 7)]
    parts.append(rtube(bar, 0.008, "BH_Bronze", n=5))
    for k, x in enumerate(np.linspace(-0.09, 0.09, 5)):
        ln = 0.26 + 0.04 * math.cos(x * 20)
        yb = front_y(HELM_C, x, 1.77, p=2.6) - 0.018
        pts = [(x, yb, 1.765), (x, yb - 0.008, 1.69), (x * 1.05, yb - 0.004, 1.77 - ln)]
        parts += chain_links(pts, link=0.04, r=0.005, mat="BH_Bronze")
    return parts


# --------------------------------------------------------------------------------------------------- weapons
def chain_flail():
    """Chain-flail (weapon space: grip at origin, +Z along the weapon): iron haft with a rune-ringed head, a taut
    chain, a spiked iron ball with two white rune bands."""
    parts = []
    V, F = M.lathe([(0.0, -0.16), (0.03, -0.16), (0.034, -0.14), (0.02, -0.12), (0.019, 0.3), (0.026, 0.33),
                    (0.0, 0.34)], 10)
    parts.append(P(V, F, "BH_DarkSteel", "haft"))
    parts.append(A.tube([(0, 0, -0.11), (0, 0, 0.08)], 0.023, "BH_Leather", n=8))
    V, F = M.lathe([(0.0, 0.3), (0.035, 0.3), (0.04, 0.33), (0.035, 0.37), (0.0, 0.38)], 10)
    parts.append(P(V, F, "BH_Bronze", "head"))
    V, F = M.lathe([(0.041, 0.318), (0.043, 0.33), (0.041, 0.342)], 12, cap=False)
    parts.append(P(V, F, "BH_Emissive", "headrune"))
    # chain (a slight droop toward -X so it reads as hanging)
    pts = [(0, 0, 0.38), (-0.02, 0, 0.52), (-0.03, 0, 0.66), (-0.025, 0, 0.75)]
    parts += chain_links(pts, link=0.05, r=0.0075, mat="BH_Bronze")
    # spiked ball
    c = np.array([-0.025, 0.0, 0.85])
    parts.append(A.ball(c, 0.085, "BH_Steel", n=12, rings=7))
    for zz in (-0.035, 0.035):
        V, F = M.lathe([(0.083, -0.008), (0.087, 0.0), (0.083, 0.008)], 16, cap=False)
        parts.append(P(V, F, "BH_Emissive", "ballrune").move(c + (0, 0, zz)))
    for k in range(11):
        # spikes on a Fibonacci sphere
        y = 1 - 2 * (k + 0.5) / 11
        r = math.sqrt(1 - y * y)
        th = k * 2.39996
        d = np.array([r * math.cos(th), r * math.sin(th), y])
        parts.append(A.taper([c + d * 0.07, c + d * 0.15], 0.02, 0.002, "BH_Bronze", n=5))
    V, F = M.lathe([(0.0, -0.02), (0.025, -0.02), (0.025, 0.02), (0.0, 0.02)], 8)
    parts.append(P(V, F, "BH_Bronze", "eye").move(c + (0, 0, -0.09)))
    return parts


def kite_shield():
    """Kite shield (weapon space: handle at origin, face -Y, +Z up): grey iron face, black rim, a black chain-circle
    emblem (a ring of chain links round a black iron boss with a white rune)."""
    parts = []
    top, bottom, hw = 0.4, -0.62, 0.29
    side = []
    for i in range(14):
        u = i / 13
        z = top - (top - bottom) * u
        k = max(0.0, (0.16 - z) / (0.16 - bottom))
        x = hw * (1 - k ** 1.6) if z < 0.16 else hw * (1 - 0.15 * ((z - 0.16) / (top - 0.16)) ** 2)
        side.append((x, z))
    top_edge = [(-hw * 0.85 + 2 * hw * 0.85 * i / 8, top + 0.04 * math.sin(math.pi * i / 8)) for i in range(1, 8)]
    o = [(0.0, bottom)] + list(reversed(side[:-1])) + top_edge[::-1] + [(-x, z) for x, z in side[:-1]]
    o = np.array(o)
    if 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1]) < 0:
        o = o[::-1]
    o = M.resample_closed(o, 48)
    yf = -0.07
    V, F = M.prism(o, 0.03, axis="y", center=yf + 0.015)
    face = P(V, F, "BH_Stone", "face")
    face.warp(lambda v: (v[0], v[1] + 0.12 * (v[0] / hw) ** 2 * 0.3, v[2]))      # curved round the arm
    parts.append(M.bevel(face, 0.004, 1, angle=40))
    rim = [(x, yf - 0.002 + 0.036 * (x / hw) ** 2, z) for x, z in np.vstack([o, o[:1]])]
    V, F = M.tube(rim, [(0.016, 0.02)] * len(rim), n=4, up=(0, -1, 0), cap0=False, cap1=False)
    parts.append(P(V, F, "BH_Gold", "rim"))
    # emblem: chain circle + black boss + white rune
    ce = np.array([0.0, yf - 0.012, 0.03])
    ring = [ce + 0.15 * np.array([math.cos(a), 0, math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 25)]
    for p in chain_links(ring, link=0.06, r=0.01, mat="BH_Gold"):
        parts.append(p)
    parts.append(A.ball(ce + (0, 0.005, 0), 0.075, "BH_Gold", n=14, rings=6, scale=(1, 0.35, 1)))
    for a in (0, 90, 180, 270):
        ra = math.radians(a)
        parts.append(A.tube([ce + 0.085 * np.array([math.cos(ra), 0, math.sin(ra)]),
                             ce + 0.13 * np.array([math.cos(ra), 0, math.sin(ra)])], (0.012, 0.006), "BH_Gold", n=4,
                            up=(0, -1, 0)))
    rune = [(-0.025, -0.03), (0.0, 0.03), (0.025, -0.03), (-0.03, 0.005), (0.03, 0.005)]
    parts.append(A.tube([ce + (x, -0.03, z) for x, z in rune], 0.0055, "BH_Emissive", n=4))
    # black studs round the rim, a chain hanging from the point
    for k in range(6):
        q = o[int(k * len(o) / 6)]
        x, z = q * 0.88
        parts.append(A.ball((x, yf - 0.006 + 0.036 * (x / hw) ** 2, z), 0.012, "BH_Gold", n=6, rings=3,
                            scale=(1, 0.6, 1)))
    # grip + strap on the back
    V, F = M.tube([(-0.08, -0.035, 0.0), (-0.05, 0.02, 0.0), (0.05, 0.02, 0.0), (0.08, -0.035, 0.0)],
                  [(0.013, 0.035)] * 4, n=6, up=(0, 0, 1))
    parts.append(P(V, F, "BH_Leather", "handle"))
    V, F = M.box(0.3, 0.012, 0.05, center=(0, -0.045, 0.2))
    parts.append(P(V, F, "BH_Leather", "strap"))
    return parts
