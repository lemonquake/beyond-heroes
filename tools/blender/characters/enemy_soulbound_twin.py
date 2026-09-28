"""Soulbound Twin (bh-013, Builder B1 "warriors"; humanoid knight that spawns in pairs, twin link): a knight in
tarnished black plate with polished silver pauldrons, couters, knee cops and trim, a long tattered ashen tabard, and
an open-faced helm (black bascinet with a silver brow band and face rim, mail aventail) showing a pale gaunt face with
glowing cyan eyes. A black padlock sits on the chest; from it hangs a BROKEN spectral chain of glowing cyan links
(BH_Emissive) - a long strand sagging to the left hip ending in a split link, and a short snapped stub to the right.
Weapon: a black-hilted longsword with a faint cyan line down the fuller (weapon.R).

The base palette is deliberately neutral (black / silver / ash grey / pale skin) so the game's per-twin tint reads.
~1.95 m to the helm crown (standard skeleton x 1.05). Knight plate kit (char_knight) via enemy_hollow_soldier.Scaled,
face from the enemy_bandit_cutthroat kit.
Clips: sword_1, sword_2, sword_3, sword_heavy, taunt, cast_quick (+ the enemy base set)."""
import math
import numpy as np

import bh_mesh as M
import bh_weapons as WP
from bh_body import torso_loft, front_y, back_y, dome, fist, interp_rows, fan_plate, smoothstep
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
import char_knight as KN
from char_knight import TORSO, rows_between, thick_band, arc_band
import enemy_bandit_cutthroat as KB
import enemy_hollow_soldier as HS
from enemy_hollow_soldier import P, rtube, ball, Scaled, add_weapon, ragged
import kit_a_common as A

K = 1.05
PROPS = proportions(K)
PALETTE = "soulbound_twin"
PALETTE_COLORS = {
    "BH_DarkSteel": ((0.07, 0.07, 0.075), 0.85, 0.5, None, 0.0, 1.0),       # tarnished black plate
    "BH_Steel": ((0.64, 0.66, 0.7), 1.0, 0.3, None, 0.0, 1.0),              # polished silver
    "BH_Cloth_Primary": ((0.42, 0.41, 0.39), 0.0, 0.92, None, 0.0, 1.0),    # ashen tabard
    "BH_Cloth_Secondary": ((0.11, 0.11, 0.11), 0.0, 0.9, None, 0.0, 1.0),   # dark under-cloth
    "BH_Skin": ((0.6, 0.61, 0.6), 0.0, 0.6, None, 0.0, 1.0),                # pale, bloodless face
    "BH_Leather": ((0.05, 0.045, 0.045), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Shadow": ((0.02, 0.025, 0.03), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((0.4, 0.95, 1.0), 0.0, 0.3, (0.3, 0.9, 1.0), 6.0, 1.0),   # spectral chain, eyes, fuller
}
CLIPS = ["sword_1", "sword_2", "sword_3", "sword_heavy", "taunt", "cast_quick"]
PREVIEW_HEIGHT = 2.3


def finish_mesh(mesh_ob):
    HS.enable_weapon_deform(mesh_ob)


TB = [(r[0], r[1] * 1.03 + 0.004, r[2] * 1.03 + 0.004, r[3] * 1.03 + 0.004, r[4]) for r in TORSO]
CHEST_W = KN.chest_spine_w(1.24, 1.30)
HIPS_W = KN.spine_hips_w(1.0, 1.04)
REMAP = {"BH_Gold": "BH_Steel", "BH_Aether": "BH_DarkSteel"}


def remat(parts, table=REMAP):
    for p in parts:
        p.mat = table.get(p.mat, p.mat)
    return parts


# --------------------------------------------------------------------------------------------------- helm
def open_helm(sb):
    """Open-faced bascinet over the cutthroat HEAD rows: black shell with the face left open (sides come forward as
    cheek guards), silver brow band + face rim, a low silver ridge, mail aventail over the throat and shoulders."""
    parts = []
    g = 0.024
    rows = KB.grow_rows(KB.HEAD, g)
    # lower shell: open at the front
    rings = []
    for z in (1.585, 1.62, 1.66, 1.70, 1.735, 1.758):
        t = (z - 1.585) / (1.758 - 1.585)
        a0 = 0.105 + 0.035 * math.sin(math.pi * min(t * 1.2, 1.0))    # cheek guards come forward at the jaw
        a0 = a0 if z < 1.75 else 0.03
        fr = np.linspace(a0, 1 - a0, 23)
        rings.append(KB.ring_frac(rows, z, 0.0, fr, p=2.1))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    parts.append(M.solidify(P(V, F, "BH_DarkSteel", "helm_low"), 0.008, offset=1.0))
    # upper dome
    up = [r for r in rows if r[0] >= 1.755]
    up = [(1.75,) + tuple(interp_rows(rows, 1.75)[1:])] + up
    V, F = torso_loft(up, n=24, p=2.1, cap0=False, cap1=True)
    parts.append(M.bevel(P(V, F, "BH_DarkSteel", "helm_up"), 0.003, 1, angle=55))
    # silver brow band
    V, F = KB.band(rows, 1.748, 1.772, 0.008, -0.002, n=24, p=2.1)
    parts.append(P(V, F, "BH_Steel", "browband"))
    # silver face rim down both edges of the opening
    for side in (0, 1):
        pts = []
        for z in (1.585, 1.62, 1.66, 1.70, 1.735, 1.752):
            t = (z - 1.585) / (1.758 - 1.585)
            a0 = 0.105 + 0.035 * math.sin(math.pi * min(t * 1.2, 1.0))
            f = a0 if side == 0 else 1 - a0
            pts.append(KB.ring_frac(rows, z, 0.004, [f], p=2.1)[0])
        V, F = M.tube(pts, [(0.009, 0.009)] * len(pts), n=5, up=(0, -1, 0))
        parts.append(P(V, F, "BH_Steel", "facerim"))
    # low ridge over the crown
    ridge = [KB.ring_frac(rows, z, 0.004, [0.0])[0] for z in (1.77, 1.8)] + \
            [np.array([0.0, 0.006, 1.845])] + [KB.ring_frac(rows, z, 0.004, [0.5])[0] for z in (1.8, 1.72, 1.64)]
    V, F = M.tube(ridge, [(0.009, 0.011)] * len(ridge), n=5, up=(1, 0, 0))
    parts.append(P(V, F, "BH_Steel", "ridge"))
    return parts


def aventail():
    """Mail aventail: from the helm edge over the throat down onto the shoulders."""
    rows = KB.grow_rows(KB.HEAD, 0.028)
    r0 = interp_rows(rows, 1.6)
    rings = []
    for i, z in enumerate((1.6, 1.56, 1.52, 1.48)):
        t = i / 3
        rx = r0[1] + (0.165 - r0[1]) * t ** 1.3
        ryf = r0[2] + 0.018 + (0.125 - r0[2]) * t ** 1.3
        ryb = r0[3] + (0.12 - r0[3]) * t ** 1.3
        cy = r0[5] * (1 - t)
        from bh_body import torso_ring
        rings.append(torso_ring(z, rx, ryf, ryb, 0.0, 2.3, 24, cy=cy))
    V, F = M.loft(rings, cap0=False, cap1=False)
    return M.solidify(P(V, F, "BH_DarkSteel", "aventail"), 0.012, offset=1.0)


# --------------------------------------------------------------------------------------------------- chain
def link(c, d, side, length=0.096, width=0.062, wire=0.015, arc=360.0, mat="BH_Emissive"):
    """One chain link: an elongated ring around centre c, long axis d, lying in the plane (d, side)."""
    d = normalize(d)
    s = normalize(np.asarray(side, float) - d * np.dot(side, d))
    n = 12 if arc >= 359 else 10
    pts = []
    for a in np.linspace(0.0, math.radians(arc), n + 1):
        pts.append(np.asarray(c, float) + d * (length / 2 - wire) * math.cos(a) + s * (width / 2 - wire) * math.sin(a))
    closed = arc >= 359
    V, F = M.tube(pts, [(wire, wire)] * len(pts), n=5, up=tuple(np.cross(d, s)), cap0=not closed, cap1=not closed)
    return P(V, F, mat, "link")


def chain_along(pts, pitch=0.072, broken_end=True, seed=0):
    """Links along a polyline (alternating orientation); the last link is split open when broken_end."""
    pts = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    out = []
    k = 0
    s = pitch * 0.5
    while s < cum[-1]:
        i = min(np.searchsorted(cum, s) - 1, len(seg) - 1)
        i = max(i, 0)
        t = (s - cum[i]) / max(seg[i], 1e-9)
        c = pts[i] + (pts[i + 1] - pts[i]) * t
        d = pts[i + 1] - pts[i]
        side = (1.0, 0.0, 0.0) if k % 2 == 0 else (0.0, -1.0, 0.0)
        last = s + pitch >= cum[-1]
        out.append((c, d, side, last))
        s += pitch
        k += 1
    parts = []
    for c, d, side, last in out:
        parts.append(link(c, d, side, arc=(250.0 if (last and broken_end) else 360.0)))
    return parts


def padlock(c):
    """Black padlock (faces -Y) with a silver shackle and keyhole, centred at c (standard space)."""
    parts = []
    V, F = M.box(0.1, 0.04, 0.086, center=c)
    parts.append(M.bevel(P(V, F, "BH_DarkSteel", "lock"), 0.01, 2))
    sh = [np.asarray(c) + (0.032 * math.cos(a), 0.0, 0.04 + 0.04 * math.sin(a)) for a in np.linspace(0, math.pi, 9)]
    V, F = M.tube(sh, [(0.01, 0.01)] * len(sh), n=6, up=(0, -1, 0))
    parts.append(P(V, F, "BH_Steel", "shackle"))
    V, F = M.box(0.072, 0.006, 0.062, center=np.asarray(c) + (0, -0.021, 0.0))
    parts.append(M.bevel(P(V, F, "BH_Steel", "lockplate"), 0.004, 1))
    parts.append(A.ball(np.asarray(c) + (0, -0.025, 0.006), 0.008, "BH_Shadow", n=6, rings=4, scale=(1, 0.5, 1)))
    V, F = M.box(0.006, 0.006, 0.016, center=np.asarray(c) + (0, -0.025, -0.006))
    parts.append(P(V, F, "BH_Shadow", "keyslot"))
    return parts


# --------------------------------------------------------------------------------------------------- weapon
def longsword():
    parts = [
        WP._blade(0.105, 0.97, 0.052, 0.034, 0.0065, tip=0.14, n_sec=9, fuller=True, mat="BH_Steel"),
        M.bevel(WP._crossguard(0.09, 0.13, h=0.024, t=0.022, curve=-0.02, mat="BH_DarkSteel"), 0.003, 1),
        WP._grip(-0.15, 0.078, 0.016, 8, mat="BH_Leather"),
        M.bevel(WP._pommel(-0.17, 0.03, mat="BH_Steel"), 0.002, 1),
    ]
    V, F = M.lathe([(0, 0.078), (0.021, 0.078), (0.023, 0.09), (0.0, 0.1)], 10)
    parts.append(P(V, F, "BH_DarkSteel", "collar"))
    for sy in (1, -1):   # faint spectral line in the fuller
        V, F = M.box(0.007, 0.002, 0.66, center=(0.0, sy * 0.0037, 0.47))
        parts.append(P(V, F, "BH_Emissive", "fuller_glow"))
    return parts


def tabard_half_w(z):
    return 0.115 + 0.035 * max(0.0, (1.05 - z) / 0.6)


def tabard_half(front, hx, z_top=0.99, z_bot=0.42, gap=0.018, hang=0.035, belt_z=1.05):
    """One tattered half of the lower tabard (hx = +1 own left / -1 right), hanging free below the belt."""
    seed = (0.7 if front else 2.3) + (0.0 if hx > 0 else 1.9)

    def fn(u, v):
        zb = z_bot + ragged(u, seed, 0.14, 3)
        z = z_top + (zb - z_top) * v
        x = hx * (0.006 + u * (tabard_half_w(z) - 0.006))
        y0 = front_y(TB, x, belt_z) - gap - 0.004 if front else back_y(TB, x, belt_z) + gap + 0.004
        d = belt_z - z
        y = y0 - hang * d if front else y0 + hang * 1.3 * d
        y += 0.008 * math.sin(u * math.pi * 3 + seed) * d / 0.5
        return (x, y, z)
    V, F = M.grid(fn, 5, 9)
    p = P(V, F, "BH_Cloth_Primary", "tabard_half")
    if (not front) != (hx < 0):
        p.flip()
    return M.solidify(p, 0.009, offset=1.0)


def leg_flap_w(thigh, z_top, z_bot, max_leg):
    def wfn(V):
        out = []
        for v in V:
            t = float(smoothstep(z_top, z_bot, v[2])) * max_leg
            out.append({"hips": 1 - t, thigh: t} if t > 1e-3 else {"hips": 1.0})
        return out
    return wfn


# --------------------------------------------------------------------------------------------------- build
def build(real):
    body = Scaled(real, K)
    sb = KB.SB(real, K)
    add = body.add
    am = body.add_mirror
    # ---- torso plate (black) with silver rims
    V, F = torso_loft(rows_between(TB, 1.215, 1.53, n_extra=3), n=28, cap1=True)
    add(M.bevel(P(V, F, "BH_DarkSteel", "breastplate"), 0.004, 1, angle=50), weights=CHEST_W)
    V, F = torso_loft(rows_between(TB, 0.99, 1.30, scale=0.985, n_extra=2), n=28, cap0=True)
    add(P(V, F, "BH_DarkSteel", "plackart"), weights=HIPS_W)
    V, F = thick_band(TB, 1.212, 1.232, 0.012, 0.0, n=28)
    add(P(V, F, "BH_Steel", "rim"), weights=CHEST_W)
    V, F = thick_band(TB, 1.49, 1.51, 0.008, -0.01, n=28)
    add(P(V, F, "BH_Steel", "rim2"), "chest")
    # ---- head: pale gaunt face, big cyan eyes, open helm, aventail
    KB.neck_and_head(sb, skin="BH_Skin", eyes="BH_Shadow", eye_glow=None, nose=True)
    for sx in (1, -1):
        add(ball((sx * 0.029, -0.074, 1.699), 0.0105, "BH_Emissive", 8, 4, (1.35, 0.6, 0.8)), "head")
        # sunken cheeks: dark hollows under the cheekbones
        add(ball((sx * 0.045, -0.058, 1.655), 0.016, "BH_Shadow", 6, 4, (0.7, 0.35, 1.2)), "head")
    for prt in open_helm(sb):
        add(prt, "head")
    add(aventail(), weights=KB.zspec_w([(1.47, "chest"), (1.53, "neck"), (1.585, "head")]))
    # ---- long tattered ashen tabard (front + back)
    # upper panel to the hips, then two tattered halves (slit front and back) that each follow their own leg
    for front in (True, False):
        add(HS.cloth_panel(TB, 1.47, 0.93, tabard_half_w, front=front, nu=9, nv=7, seed=0.7, rag=0.0, gap=0.018,
                           hang=0.035, thick=0.009, belt_z=1.05),
            weights=HS.cloth_w(belt_z=1.05, leg=0.3))
        for hx in (1, -1):
            add(tabard_half(front, hx), weights=leg_flap_w("thigh.L" if hx > 0 else "thigh.R", 1.0, 0.55, 0.75))
    # ---- belt, faulds (black, silver edges), mail skirt
    V, F = thick_band(TB, 1.025, 1.068, 0.034, 0.014, n=28)
    add(M.bevel(P(V, F, "BH_Leather", "belt"), 0.003, 1), "hips")
    by = front_y(TB, 0, 1.047) - 0.04
    V, F = M.box(0.06, 0.016, 0.05, center=(0, by, 1.047))
    add(M.bevel(P(V, F, "BH_Steel", "buckle"), 0.005, 1), "hips")
    for side_a in ((0.12, 0.38), (0.62, 0.88)):
        for i in range(3):
            z1 = 1.025 - 0.048 * i
            V, F = arc_band(TB, z1 - 0.062, z1, 0.035 + 0.019 * i, side_a[0], side_a[1], n=10)
            lame = P(V, F, "BH_DarkSteel" if i < 2 else "BH_Steel", "fauld")
            lame.warp(lambda v, z1=z1: (v[0] * (1 + 0.28 * (z1 - v[2])), v[1] * (1 + 0.28 * (z1 - v[2])), v[2]))
            add(M.solidify(lame, 0.007, offset=1.0), weights=body.skirt_weights(1.0, 0.8, max_leg=0.35, center_w=0.05))
    V, F = torso_loft([(0.97, 0.164, 0.114, 0.11, 0.0), (0.88, 0.178, 0.12, 0.117, 0.0),
                       (0.79, 0.186, 0.122, 0.12, 0.0)], n=26)
    add(P(V, F, "BH_DarkSteel", "mailskirt"), weights=body.skirt_weights(0.98, 0.78, max_leg=0.8))
    # ---- lock + broken spectral chain on the chest
    lc = np.array([0.0, front_y(TB, 0.0, 1.33) - 0.05, 1.33])
    for prt in padlock(lc):
        add(prt, weights=CHEST_W)
    cw = HS.cloth_w(belt_z=1.05, leg=0.3)
    main = [lc + (0.0, -0.004, -0.05)]
    for t in np.linspace(0, 1, 8)[1:]:
        z = 1.28 - 0.4 * t
        x = 0.13 * t + 0.04 * math.sin(math.pi * t)
        y = min(front_y(TB, x, max(z, 1.06)), front_y(TB, x, 1.06) - 0.035 * max(0.0, 1.06 - z) / 0.1) - 0.05
        main.append(np.array([x, y, z]))
    for prt in chain_along(main, pitch=0.05):
        add(prt, weights=cw)
    stub = [lc + (-0.05, -0.004, -0.01), lc + (-0.1, 0.0, -0.04), lc + (-0.13, 0.006, -0.1), lc + (-0.14, 0.006, -0.14)]
    stub = [np.array([q[0], front_y(TB, q[0], q[2]) - 0.045, q[2]]) for q in stub]
    for prt in chain_along(stub, pitch=0.05):
        add(prt, weights=CHEST_W)
    # ---- legs (mirrored): black plate, silver knee cops + rims
    s = "L"
    th, sh = "thigh." + s, "shin." + s
    am(body.limb(th, [(-0.02, 0.078, 0.082), (0.4, 0.07, 0.075), (0.95, 0.052, 0.055)], "BH_Cloth_Secondary", n=12), th)
    cu = body.limb(th, [(0.2, 0.088, 0.092), (0.24, 0.085, 0.089), (0.55, 0.079, 0.084), (0.93, 0.064, 0.068)],
                   "BH_DarkSteel", n=14, p=2.4, offs=[(0, 0.004)] * 4)
    am(M.bevel(cu, 0.003, 1, angle=50), th)
    knee = body.head(sh)
    V, F = dome(knee + (0, -0.046, 0.0), (0, -1, 0.15), 0.064, a_max=78, n=14, rings=5)
    am(M.solidify(P(V, F, "BH_Steel", "poleyn"), 0.007, offset=-1), weights=lambda V: [{th: 0.5, sh: 0.5}] * len(V))
    V, F = fan_plate(knee + (0.057, -0.01, 0.0), (1, 0, 0), (0, 0, 1), 0.056, 100, 260, n=8, thick=0.006)
    am(M.bevel(P(V, F, "BH_Steel", "kneefan"), 0.002, 1), weights=lambda V: [{th: 0.5, sh: 0.5}] * len(V))
    gr = body.limb(sh, [(0.03, 0.06, 0.062), (0.3, 0.066, 0.07), (0.55, 0.058, 0.06), (0.85, 0.048, 0.05),
                        (1.0, 0.052, 0.055)], "BH_DarkSteel", n=14, p=2.3,
                   offs=[(0, 0.0), (0, -0.012), (0, -0.006), (0, 0.0), (0, 0.0)])
    am(M.bevel(gr, 0.003, 1, angle=50), sh)
    c1 = body.lpt(sh, [(0, 0.97 * 0.43, 0)])[0]
    V, F = M.tube([c1 + (0, 0, 0.01), c1 + (0, 0, -0.006)], [(0.058, 0.061)] * 2, n=14, up=(0, -1, 0))
    am(P(V, F, "BH_Steel", "greave_rim"), sh)
    for part, bone in KN.sabaton(body, s):
        part.mat = "BH_DarkSteel" if part.mat == "BH_Steel" else part.mat
        am(part, bone)
    # ---- arms (mirrored): black plate, silver couters / cuffs, silver pauldrons with black lames
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    am(body.limb(ua, [(-0.05, 0.058, 0.058), (0.5, 0.054, 0.056), (1.0, 0.046, 0.048)], "BH_Cloth_Secondary", n=12),
       ua)
    rb = body.limb(ua, [(0.4, 0.062, 0.064), (0.44, 0.06, 0.062), (0.95, 0.053, 0.055)], "BH_DarkSteel", n=12, p=2.3)
    am(M.bevel(rb, 0.003, 1, angle=50), ua)
    el = body.head(fa)
    V, F = dome(el + (0.0, 0.031, 0.0), (0, 1, 0.1), 0.053, a_max=80, n=12, rings=5)
    am(M.solidify(P(V, F, "BH_Steel", "couter"), 0.006, offset=-1), weights=lambda V: [{ua: 0.5, fa: 0.5}] * len(V))
    vb = body.limb(fa, [(0.1, 0.05, 0.052), (0.5, 0.047, 0.049), (0.93, 0.04, 0.042)], "BH_DarkSteel", n=12, p=2.3)
    am(M.bevel(vb, 0.003, 1, angle=50), fa)
    cuff = body.limb(fa, [(0.84, 0.044, 0.046), (1.0, 0.057, 0.057), (1.08, 0.061, 0.059)], "BH_Steel", n=12,
                     cap0=False, cap1=False)
    am(M.solidify(cuff, 0.005, offset=1.0), ha)
    for prt in fist(body, s, "BH_DarkSteel", "BH_DarkSteel"):
        am(prt, ha)
    pd = KN.pauldron(body, s)
    for i, prt in enumerate(pd):
        prt.mat = {"pauldron": "BH_Steel", "ridge": "BH_DarkSteel", "pauldron_rim": "BH_DarkSteel",
                   "pauldron_aether": "BH_Emissive", "lame": "BH_DarkSteel"}.get(prt.name, prt.mat)
        prt.scale((1.1, 1.08, 1.05), center=body.head(ua))
        am(prt, ua)
    # ---- weapon
    add_weapon(body, "R", longsword())
