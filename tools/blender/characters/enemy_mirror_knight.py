"""Mirror Knight (bh-013, Builder B1 "warriors"; armored humanoid, mirror stance): a tall knight in heavy plate of
pale sandstone-gold trimmed with polished silver. A LARGE round mirror shield on the left arm (convex polished
silver face, thick gold rim), a tall sugarloaf helm whose visor is one smooth mirrored faceplate (no slit, no face),
a silver sun-disc on the chest of a short sand-coloured tabard, and a curved single-edged sabre with a gold knuckle
bow in the right hand.

~2.1 m to the helm finial (standard skeleton x 1.08). Built on the knight's plate kit (char_knight parts) through
enemy_hollow_soldier.Scaled. Mirror surfaces use BH_Aether (keeps its exported PBR in the game: metallic, very low
roughness, a faint pale emission floor so the mirror reads bright even in dark dungeons).

Clips: sword_1, sword_2, sword_heavy, shield_bash, taunt, war_cry (+ the enemy base set)."""
import math
import numpy as np

import bh_mesh as M
import bh_weapons as WP
from bh_body import torso_loft, front_y, back_y, dome, fist, interp_rows, fan_plate, M_align_z
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
import char_knight as KN
from char_knight import TORSO, rows_between, thick_band, arc_band
import enemy_hollow_soldier as HS
from enemy_hollow_soldier import P, rtube, ball, Scaled, add_weapon
import kit_a_common as A

K = 1.08
PROPS = proportions(K)
PALETTE = "mirror_knight"
PALETTE_COLORS = {
    "BH_Steel": ((0.8, 0.68, 0.46), 0.9, 0.4, None, 0.0, 1.0),               # pale sandstone-gold plate
    "BH_Bronze": ((0.86, 0.88, 0.92), 1.0, 0.16, None, 0.0, 1.0),            # polished silver trim / sabre
    "BH_Gold": ((0.82, 0.54, 0.15), 1.0, 0.28, None, 0.0, 1.0),              # gold rims, knuckle bow
    "BH_Aether": ((0.92, 0.94, 0.98), 0.6, 0.1, (0.74, 0.8, 0.88), 1.0, 1.0),  # mirror (shield face, visor)
    "BH_DarkSteel": ((0.2, 0.17, 0.13), 0.85, 0.5, None, 0.0, 1.0),           # mail, under-plates
    "BH_Cloth_Primary": ((0.62, 0.48, 0.28), 0.0, 0.9, None, 0.0, 1.0),      # sand tabard
    "BH_Cloth_Secondary": ((0.3, 0.2, 0.1), 0.0, 0.9, None, 0.0, 1.0),       # tabard border
    "BH_Leather": ((0.16, 0.1, 0.055), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Shadow": ((0.03, 0.025, 0.02), 0.0, 0.8, None, 0.0, 1.0),
}
CLIPS = ["sword_1", "sword_2", "sword_heavy", "shield_bash", "taunt", "war_cry"]
PREVIEW_HEIGHT = 2.5


def finish_mesh(mesh_ob):
    HS.enable_weapon_deform(mesh_ob)


# bulkier plate than the knight (standard space; everything is scaled by K on add)
TB = [(r[0], r[1] * 1.1 + 0.01, r[2] * 1.08 + 0.008, r[3] * 1.1 + 0.01, r[4]) for r in TORSO]
CHEST_W = KN.chest_spine_w(1.24, 1.30)
HIPS_W = KN.spine_hips_w(1.0, 1.04)
REMAP = {"BH_Gold": "BH_Bronze", "BH_Aether": "BH_Gold"}


def remat(parts, table=REMAP):
    for p in parts:
        p.mat = table.get(p.mat, p.mat)
    return parts


def disk_y(profile, mat, name, n=28):
    """Lathe around +Z turned to face -Y (profile (r, d): d = distance toward -Y)."""
    V, F = M.lathe(profile, n)
    return P(V, F, mat, name).rot(Rx(90))


def ring_y(r, y, prof, mat, n=36, name="ring"):
    pts = [(r * math.cos(a), y, r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, n + 1)]
    V, F = M.tube(pts, [prof] * len(pts), n=6, up=(0, -1, 0), cap0=False, cap1=False)
    return P(V, F, mat, name)


# --------------------------------------------------------------------------------------------------- weapons
def mirror_shield(r=0.41):
    """Large round shield (weapon space: handle at origin, face -Y). Convex mirror face (BH_Aether) filling almost
    the whole disc, a thick gold rim, a thin silver inner ring, sandstone back plate, leather grip + arm strap."""
    parts = []
    yf = -0.075
    d0 = -yf
    parts.append(disk_y([(0.0, d0 - 0.03), (r - 0.01, d0 - 0.024), (r, d0 - 0.012), (r, d0), (0.0, d0 + 0.002)],
                        "BH_Steel", "shield_back"))
    # the mirror: gently convex, polished
    parts.append(disk_y([(0.0, d0 + 0.032), (0.12, d0 + 0.029), (0.24, d0 + 0.02), (0.33, d0 + 0.01),
                         (r - 0.035, d0 + 0.003), (r - 0.035, d0 - 0.002), (0.0, d0 - 0.002)], "BH_Aether",
                        "mirror", n=32))
    # thick gold rim + a silver inner ring
    parts.append(ring_y(r - 0.012, yf - 0.004, (0.03, 0.026), "BH_Gold", name="rim"))
    parts.append(ring_y(r - 0.042, yf - 0.006, (0.008, 0.008), "BH_Bronze", n=32, name="inner_ring"))
    # four small gold sun-ray studs on the rim (N/E/S/W) so the rim reads as ornate, the face stays clean
    for k in range(8):
        a = 2 * math.pi * k / 8
        parts.append(A.ball(((r - 0.012) * math.cos(a), yf - 0.03, (r - 0.012) * math.sin(a)), 0.02 if k % 2 == 0
                            else 0.014, "BH_Bronze", n=6, rings=3, scale=(1, 0.6, 1)))
    # grip (back side): bar across + arm strap
    V, F = M.tube([(-0.08, -0.035, 0.0), (-0.05, 0.02, 0.0), (0.05, 0.02, 0.0), (0.08, -0.035, 0.0)],
                  [(0.013, 0.035)] * 4, n=6, up=(0, 0, 1))
    parts.append(P(V, F, "BH_Leather", "handle"))
    V, F = M.box(0.3, 0.012, 0.05, center=(0, -0.04, 0.2))
    parts.append(P(V, F, "BH_Leather", "strap"))
    return parts


def sabre(length=0.82, width=0.05, curve=0.13):
    """Curved single-edged sabre (weapon space): edge on +X (knuckle side), the blade sweeping back toward -X near
    the tip; polished silver blade, gold cross-guard with a knuckle bow, leather grip, silver pommel cap."""
    parts = []
    rings = []
    n = 14
    for i in range(n + 1):
        u = i / n
        z = 0.045 + length * u
        xc = -curve * u ** 2
        w = width * (1 - 0.1 * u) * (1 - u ** 4) + 0.003
        t = 0.0065 * (1 - 0.6 * u) + 0.001
        spine = xc - w * 0.45 + 0.3 * w * u ** 3
        edge = xc + w * 0.55
        rings.append(np.array([(edge, 0, z), (edge - 0.3 * (edge - spine), t * 0.6, z), (spine, t, z),
                               (spine, -t, z), (edge - 0.3 * (edge - spine), -t * 0.6, z)]))
    V, F = M.loft(rings)
    parts.append(P(V, F, "BH_Bronze", "sabre_blade"))
    # gold guard: short cross bar + langets, knuckle bow sweeping down to the pommel on the edge side
    parts.append(M.bevel(WP._crossguard(0.03, 0.06, h=0.016, t=0.022, curve=0.015, mat="BH_Gold"), 0.003, 1))
    bow = [(0.058, 0.0, 0.03), (0.085, 0.0, -0.005), (0.09, 0.0, -0.06), (0.07, 0.0, -0.11), (0.02, 0.0, -0.135)]
    parts.append(rtube(bow, 0.008, "BH_Gold", n=6, up=(0, -1, 0)))
    parts.append(WP._grip(-0.125, 0.02, 0.016, 5, mat="BH_Leather"))
    V, F = M.lathe([(0, -0.155), (0.018, -0.15), (0.022, -0.136), (0.016, -0.125), (0.0, -0.123)], 8)
    parts.append(P(V, F, "BH_Bronze", "pommel"))
    return parts


# --------------------------------------------------------------------------------------------------- helm
HELM = [(1.552, 0.106, 0.117, 0.117, 0.10), (1.585, 0.112, 0.124, 0.122, 0.12), (1.64, 0.116, 0.129, 0.125, 0.12),
        (1.70, 0.117, 0.13, 0.126, 0.08), (1.76, 0.115, 0.126, 0.124, 0.04), (1.81, 0.107, 0.115, 0.115, 0.0),
        (1.86, 0.09, 0.095, 0.095, 0.0), (1.905, 0.066, 0.069, 0.069, 0.0), (1.94, 0.038, 0.04, 0.04, 0.0),
        (1.962, 0.012, 0.012, 0.012, 0.0)]
HCY = 0.008
HELM_C = [h + (HCY,) for h in HELM]


def tall_helm():
    """Sugarloaf great helm (sandstone) rising to a silver finial; the whole face is one smooth convex mirror plate
    (BH_Aether) framed in gold; silver crest ridge over the crown; flared silver neck guard."""
    parts = []
    V, F = torso_loft(HELM_C, n=28, p=2.5, cap0=False, cap1=True)
    parts.append(M.bevel(P(V, F, "BH_Steel", "helm"), 0.003, 1, angle=55))
    # mirror faceplate: convex oval following the helm front
    ax, az, zc = 0.084, 0.098, 1.668

    def fn(u, v):
        a = 2 * math.pi * u
        x = ax * v * math.cos(a)
        z = zc + az * v * math.sin(a)
        y = front_y(HELM_C, x * 1.0, z, p=2.5) - 0.006 - 0.012 * (1 - v * v)
        return (x, y, z)
    V, F = M.grid(fn, 24, 6, closed_u=True)
    face = P(V, F, "BH_Aether", "faceplate")
    parts.append(M.solidify(face, 0.006, offset=1.0))
    frame = [np.array(fn(u, 1.0)) + (0, -0.001, 0) for u in np.linspace(0, 1, 25)]
    V, F = M.tube(frame, [(0.011, 0.008)] * len(frame), n=6, up=(0, -1, 0), cap0=False, cap1=False)
    parts.append(P(V, F, "BH_Gold", "faceframe"))
    # gold brow band round the helm just above the faceplate
    V, F = thick_band(HELM, 1.776, 1.8, 0.008, -0.002, n=28, p=2.5)
    parts.append(P(V, F, "BH_Gold", "browband"))
    # silver crest ridge from the brow over the crown to the nape
    ridge = []
    for z in np.linspace(1.8, 1.95, 6):
        ridge.append((0.0, front_y(HELM_C, 0.0, z, p=2.5) - 0.004, z))
    for z in np.linspace(1.95, 1.62, 7)[1:]:
        ridge.append((0.0, back_y(HELM_C, 0.0, z, p=2.5) + 0.004, z))
    V, F = M.tube(ridge, [(0.011, 0.012)] * len(ridge), n=6, up=(1, 0, 0))
    parts.append(P(V, F, "BH_Bronze", "crest"))
    # finial: silver ball + spike
    parts.append(A.ball((0, HCY, 1.972), 0.026, "BH_Bronze", n=10, rings=5))
    parts.append(A.taper([(0, HCY, 1.99), (0, HCY, 2.02), (0, HCY, 2.06)], 0.013, 0.002, "BH_Bronze", n=6))
    # flared neck guard (silver lames) at the back and sides
    for i, z in enumerate((1.57, 1.535)):
        def gfn(u, v, z=z, i=i):
            a = math.radians(-110 + 220 * u)          # 0 = back
            r = 0.122 + 0.02 * i + 0.03 * v
            return (r * math.sin(a), HCY + 1.06 * r * math.cos(a), z - 0.045 * v)
        V, F = M.grid(gfn, 11, 2)
        parts.append(M.solidify(P(V, F, "BH_Bronze", "neckguard").flip(), 0.006, offset=-1))
    return parts


def sun_disc(c, r, add_fn):
    """Mirror sun emblem: a small convex mirror disc with a gold ring and eight gold rays (faces -Y)."""
    d = disk_y([(0.0, 0.012), (r * 0.6, 0.009), (r, 0.0), (0.0, -0.002)], "BH_Aether", "sun", n=16)
    add_fn(d.move(c))
    add_fn(ring_y(r, 0.0, (0.007, 0.006), "BH_Gold", n=20, name="sun_ring").move(c))
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8
        ln = r * (0.75 if k % 2 else 0.5)
        p0 = np.array(c) + (r * 1.05 * math.cos(a), 0.002, r * 1.05 * math.sin(a))
        p1 = p0 + (ln * math.cos(a), 0.004, ln * math.sin(a))
        add_fn(A.taper([p0, p1], 0.009, 0.001, "BH_Gold", n=4, up=(0, -1, 0)))


# --------------------------------------------------------------------------------------------------- build
def build(real):
    body = Scaled(real, K)
    add = body.add
    am = body.add_mirror
    # ---- torso plate
    V, F = torso_loft(rows_between(TB, 1.215, 1.53, n_extra=3), n=28, cap1=True)
    add(M.bevel(P(V, F, "BH_Steel", "breastplate"), 0.004, 1, angle=50), weights=CHEST_W)
    V, F = torso_loft(rows_between(TB, 0.99, 1.30, scale=0.985, n_extra=2), n=28, cap0=True)
    add(P(V, F, "BH_Steel", "plackart"), weights=HIPS_W)
    V, F = thick_band(TB, 1.212, 1.232, 0.012, 0.0, n=28)
    add(P(V, F, "BH_Bronze", "rim"), weights=CHEST_W)
    V, F = thick_band(TB, 1.505, 1.525, 0.006, -0.01, n=28)
    add(P(V, F, "BH_Bronze", "rim2"), "chest")
    prof = [(0.17, 1.45), (0.145, 1.49), (0.104, 1.527), (0.088, 1.57), (0.076, 1.57), (0.092, 1.527),
            (0.135, 1.49), (0.16, 1.45), (0.17, 1.45)]
    V, F = M.lathe(prof, 20)
    add(P(V, F, "BH_Bronze", "gorget").scale((1.0, 0.85, 1.0)), "chest")
    V, F = M.lathe([(0.0, 1.46), (0.074, 1.47), (0.07, 1.56), (0.064, 1.6), (0.0, 1.6)], 12)
    add(P(V, F, "BH_DarkSteel", "coif").scale((1, 0.9, 1), center=(0, 0, 1.5)), "neck")
    # silver edging down the breastplate flanks (reads as trim at distance)
    for sx in (1, -1):
        pts = []
        for t in np.linspace(0, 1, 7):
            z = 1.47 - 0.24 * t
            x = sx * (0.15 + 0.03 * math.sin(math.pi * t))
            pts.append((x, front_y(TB, x, z) - 0.002, z))
        add(rtube(pts, 0.008, "BH_Bronze", n=5, up=(0, -1, 0)), weights=CHEST_W)
    # ---- short sand tabard (front + back) with a dark border, silver-mirror sun on the chest
    for front in (True, False):
        pnl = tabard(front)
        add(pnl, weights=HS.cloth_w(belt_z=1.03, leg=0.55))
        hem = tabard_hem(front)
        add(hem, weights=HS.cloth_w(belt_z=1.03, leg=0.55))
    zc = 1.34
    sun_disc((0.0, front_y(TB, 0, zc) - 0.03, zc), 0.058, lambda p: add(p, weights=CHEST_W))
    # ---- belt, faulds, mail skirt
    V, F = thick_band(TB, 1.025, 1.072, 0.032, 0.012, n=28)
    add(M.bevel(P(V, F, "BH_Leather", "belt"), 0.003, 1), "hips")
    by = front_y(TB, 0, 1.048) - 0.036
    V, F = M.box(0.075, 0.018, 0.062, center=(0, by, 1.048))
    add(M.bevel(P(V, F, "BH_Gold", "buckle"), 0.006, 1), "hips")
    for side_a in ((0.12, 0.38), (0.62, 0.88)):
        for i in range(3):
            z1 = 1.025 - 0.05 * i
            V, F = arc_band(TB, z1 - 0.065, z1, 0.035 + 0.02 * i, side_a[0], side_a[1], n=10)
            lame = P(V, F, "BH_Steel" if i < 2 else "BH_Bronze", "fauld")
            lame.warp(lambda v, z1=z1: (v[0] * (1 + 0.3 * (z1 - v[2])), v[1] * (1 + 0.3 * (z1 - v[2])), v[2]))
            add(M.solidify(lame, 0.007, offset=1.0), weights=body.skirt_weights(1.0, 0.8, max_leg=0.35, center_w=0.05))
    V, F = torso_loft([(0.97, 0.175, 0.122, 0.118, 0.0), (0.86, 0.19, 0.128, 0.125, 0.0),
                       (0.76, 0.198, 0.13, 0.128, 0.0)], n=26)
    add(P(V, F, "BH_DarkSteel", "mailskirt"), weights=body.skirt_weights(0.98, 0.76, max_leg=0.8))
    # ---- legs (mirrored)
    s = "L"
    th, sh = "thigh." + s, "shin." + s
    am(body.limb(th, [(-0.02, 0.085, 0.09), (0.4, 0.078, 0.082), (0.95, 0.058, 0.062)], "BH_DarkSteel", n=12), th)
    cu = body.limb(th, [(0.18, 0.096, 0.1), (0.24, 0.094, 0.098), (0.55, 0.086, 0.09), (0.93, 0.068, 0.072)],
                   "BH_Steel", n=14, p=2.4, offs=[(0, 0.004)] * 4)
    am(M.bevel(cu, 0.003, 1, angle=50), th)
    c0 = body.lpt(th, [(0, 0.2 * 0.43, 0)])[0]
    V, F = M.tube([c0 + (0, 0, 0.012), c0 + (0, 0, -0.006)], [(0.1, 0.104)] * 2, n=14, up=(0, -1, 0))
    am(P(V, F, "BH_Bronze", "cuisse_rim"), th)
    knee = body.head(sh)
    V, F = dome(knee + (0, -0.05, 0.0), (0, -1, 0.15), 0.068, a_max=78, n=14, rings=5)
    am(M.solidify(P(V, F, "BH_Bronze", "poleyn"), 0.008, offset=-1),
       weights=lambda V: [{th: 0.5, sh: 0.5}] * len(V))
    V, F = fan_plate(knee + (0.06, -0.01, 0.0), (1, 0, 0), (0, 0, 1), 0.06, 100, 260, n=8, thick=0.006)
    am(M.bevel(P(V, F, "BH_Steel", "kneefan"), 0.002, 1), weights=lambda V: [{th: 0.5, sh: 0.5}] * len(V))
    gr = body.limb(sh, [(0.03, 0.066, 0.068), (0.3, 0.072, 0.077), (0.55, 0.064, 0.066), (0.85, 0.052, 0.054),
                        (1.0, 0.056, 0.059)], "BH_Steel", n=14, p=2.3,
                   offs=[(0, 0.0), (0, -0.012), (0, -0.006), (0, 0.0), (0, 0.0)])
    am(M.bevel(gr, 0.003, 1, angle=50), sh)
    c1 = body.lpt(sh, [(0, 0.97 * 0.43, 0)])[0]
    V, F = M.tube([c1 + (0, 0, 0.012), c1 + (0, 0, -0.006)], [(0.062, 0.066)] * 2, n=14, up=(0, -1, 0))
    am(P(V, F, "BH_Bronze", "greave_rim"), sh)
    kx, ky, kz = knee
    ridge = [(kx, -0.083, kz - 0.09), (kx, -0.086, kz - 0.17), (kx, -0.074, kz - 0.26), (kx, -0.063, kz - 0.33)]
    am(rtube(ridge, 0.007, "BH_Bronze", n=5, up=(0, -1, 0)), sh)
    for part, bone in KN.sabaton(body, s):
        part.scale((1.1, 1.08, 1.1), center=(body.head(th)[0], 0, 0))
        am(part, bone)
    # ---- arms (mirrored)
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    am(body.limb(ua, [(-0.05, 0.064, 0.064), (0.5, 0.06, 0.062), (1.0, 0.052, 0.054)], "BH_DarkSteel", n=12), ua)
    rb = body.limb(ua, [(0.4, 0.068, 0.07), (0.44, 0.066, 0.068), (0.95, 0.058, 0.06)], "BH_Steel", n=12, p=2.3)
    am(M.bevel(rb, 0.003, 1, angle=50), ua)
    el = body.head(fa)
    V, F = dome(el + (0.0, 0.034, 0.0), (0, 1, 0.1), 0.058, a_max=80, n=12, rings=5)
    am(M.solidify(P(V, F, "BH_Bronze", "couter"), 0.007, offset=-1), weights=lambda V: [{ua: 0.5, fa: 0.5}] * len(V))
    V, F = fan_plate(el + (0.055, 0.012, 0.0), (1, 0, 0), (0, 0, 1), 0.056, 20, 200, n=8, thick=0.005)
    am(M.bevel(P(V, F, "BH_Steel", "couterfan"), 0.002, 1), weights=lambda V: [{ua: 0.5, fa: 0.5}] * len(V))
    vb = body.limb(fa, [(0.1, 0.055, 0.057), (0.5, 0.052, 0.054), (0.93, 0.044, 0.046)], "BH_Steel", n=12, p=2.3)
    am(M.bevel(vb, 0.003, 1, angle=50), fa)
    cuff = body.limb(fa, [(0.8, 0.05, 0.052), (1.0, 0.064, 0.064), (1.1, 0.07, 0.068)], "BH_Steel", n=12,
                     cap0=False, cap1=False)
    am(M.solidify(cuff, 0.005, offset=1.0), ha)
    V, F = M.tube([body.lpt(fa, [(0, 1.08 * 0.26, 0)])[0], body.lpt(fa, [(0, 1.11 * 0.26, 0)])[0]],
                  [(0.071, 0.069)] * 2, n=12, up=(0, -1, 0))
    am(P(V, F, "BH_Bronze", "cuffrim"), ha)
    for prt in fist(body, s, "BH_Steel", "BH_DarkSteel", scale=1.1):
        am(prt, ha)
    for prt in remat(KN.pauldron(body, s)):
        prt.scale((1.32, 1.28, 1.15), center=body.head(ua) + np.array([-0.03, 0.0, 0.0]))
        am(prt, ua)
    # ---- helm
    for prt in tall_helm():
        add(prt, "head")
    # ---- weapons
    add_weapon(body, "R", sabre())
    add_weapon(body, "L", mirror_shield())


def tabard(front):
    nu, nv = 9, 12
    z_top = 1.46 if front else 1.455
    bottom = 0.64

    def fn(u, v):
        z = z_top + (bottom - z_top) * v
        x_half = 0.1 + 0.045 * max(0.0, (1.1 - z) / 0.46)
        x = (u - 0.5) * 2 * x_half
        if z >= 1.06:
            y = front_y(TB, x, z) - 0.018 if front else back_y(TB, x, z) + 0.018
        else:
            y0 = front_y(TB, x, 1.06) - 0.018 if front else back_y(TB, x, 1.06) + 0.018
            d = 1.06 - z
            y = y0 - 0.04 * d if front else y0 + 0.055 * d
            y += 0.006 * math.sin(u * math.pi * 4) * d
        return (x, y, z)
    V, F = M.grid(fn, nu, nv)
    p = P(V, F, "BH_Cloth_Primary", "tabard")
    if not front:
        p.flip()
    return M.solidify(p, 0.01, offset=1.0)


def tabard_hem(front):
    """Dark border band along the tabard hem."""
    z_top, bottom = (1.46 if front else 1.455), 0.64

    def fn(u, v):
        z = bottom + 0.05 * (1 - v)
        x_half = 0.1 + 0.045 * max(0.0, (1.1 - z) / 0.46) + 0.002
        x = (u - 0.5) * 2 * x_half
        y0 = front_y(TB, x, 1.06) - 0.018 if front else back_y(TB, x, 1.06) + 0.018
        d = 1.06 - z
        y = y0 - 0.04 * d if front else y0 + 0.055 * d
        y += 0.006 * math.sin(u * math.pi * 4) * d
        y += -0.004 if front else 0.004
        return (x, y, z)
    V, F = M.grid(fn, 9, 2)
    p = P(V, F, "BH_Cloth_Secondary", "tabard_hem")
    if not front:
        p.flip()
    return M.solidify(p, 0.006, offset=1.0)
