"""Orvul Dram, the Leash-Abbot (bh-029, Builder M4, Zarael / the Heart Citadel FINAL BOSS): the master of the
Kharvenn chain-priests, a towering ~3.6 m high priest. Layered robes - a long grey under-robe to the floor, a black
over-robe split down the front, a black tattered drape down the back - banded with iron; a mantle of overlapping
grey-iron lames over the shoulders; a stole of iron rune-plaques hanging down his front. Rune-chains are wrapped round
him (shoulder to hip, round both forearms) and trail from his belt and wrists toward the floor; every few links a
rune-tablet link burns pure white. A gaunt grey face behind an iron face-cage, white eyes; a tall iron crown-mitre
(ribbed, a spiked crown band, a glowing rune plate at the front, chains hanging from its sides like lappets).

Weapon.R: the great chain-censer - an iron grip, a short heavy chain (rigid) and a big iron cage with a white light
burning inside (a flail head: it swings through boss_sweep / boss_slam). An iron-bound book on a chain at the left
hip. Glow rule (bh-029): every glow is pure white (BH_Emissive). Kharvenn are foreigners: grey iron and black cloth,
no Zarael stone.

Authored at true size (SCALE 1.73: the mitre peak at ~3.6 m) in the standard 1.8 m space (K kit SB; robe helpers from
enemy_ashen_cultist, the over-robe / drape pattern of enemy_necromancer).
Clips: boss_roar boss_slam boss_summon boss_sweep cast_area cast_heavy cast_ultimate cast_weapon (+ boss_charge,
staff_heavy)."""
import math
import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep, M_align_z
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C
import enemy_hollow_soldier as HS
import kit_a_common as A

SCALE = 1.73
PROPS = proportions(SCALE, shoulder_x=0.2 * SCALE)
PREVIEW_HEIGHT = 4.2
PALETTE = "leash_abbot"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.24, 0.235, 0.24), 0.0, 0.9, None, 0.0, 1.0),        # grey under-robe
    "BH_Cloth_Secondary": ((0.025, 0.022, 0.025), 0.0, 0.92, None, 0.0, 1.0),  # black over-robe / drape
    "BH_DarkSteel": ((0.16, 0.16, 0.17), 0.9, 0.5, None, 0.0, 1.0),           # grey iron: bands, mantle, mitre
    "BH_Steel": ((0.07, 0.07, 0.075), 0.9, 0.55, None, 0.0, 1.0),             # blackened iron: chains, cage
    "BH_Skin": ((0.36, 0.35, 0.36), 0.0, 0.6, None, 0.0, 1.0),                # gaunt grey skin
    "BH_Leather": ((0.05, 0.04, 0.035), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Bone": ((0.42, 0.38, 0.3), 0.0, 0.7, None, 0.0, 1.0),                 # book pages
    "BH_Shadow": ((0.012, 0.01, 0.012), 0.0, 0.85, None, 0.0, 1.0),
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),    # white runes, eyes, censer light
}
CLIPS = ["boss_roar", "boss_slam", "boss_summon", "boss_sweep", "cast_area", "cast_heavy", "cast_ultimate",
         "cast_weapon", "boss_charge", "staff_heavy"]

GLOW = "BH_Emissive"
TORSO = [(r[0], r[1] * 1.04, r[2] * 1.02, r[3] * 1.04, r[4] * 0.6) for r in K.TORSO]
G = 0.014
ROBE_W = C.ROBE_W
CHEST_W = K.zspec_w([(1.2, "spine"), (1.3, "chest")])


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


P = A.P


# ------------------------------------------------------------------------------------------------ chains
def link_mesh(length, width, wire, n=3):
    """One elongated chain link (stadium torus) along local Z, ring plane XZ."""
    pts = []
    a = max(length / 2 - width / 2, 0.0)
    for i in range(n * 2):
        t = 2 * math.pi * i / (n * 2)
        x = width / 2 * math.cos(t)
        z = width / 2 * math.sin(t) + (a if math.sin(t) >= 0 else -a)
        pts.append((x, 0.0, z))
    pts = np.array(pts + [pts[0]])
    V, F = M.tube(pts, [(wire, wire)] * len(pts), n=4, up=(0, 1, 0), cap0=False, cap1=False)
    return np.asarray(V, float), F


def chain(pts, link=0.034, wire=0.0055, rune_every=5, mat="BH_Steel", glow=True, start=0):
    """Chain of alternating links along a polyline (standard space). Every `rune_every`-th link is an iron rune
    tablet with a white glyph. Returns parts."""
    pts = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    step = link * 0.72
    out = []
    i = 0
    s = 0.0
    while s <= cum[-1]:
        j = min(int(np.searchsorted(cum, s, side="right") - 1), len(seg) - 1)
        u = (s - cum[j]) / max(seg[j], 1e-9)
        c = pts[j] * (1 - u) + pts[j + 1] * u
        d = normalize(pts[j + 1] - pts[j])
        R = M_align_z(d)
        R = R @ Rz(90.0 * ((i + start) % 2))
        k = i + start
        if glow and rune_every and k % rune_every == rune_every - 1:
            V, F = M.box(link * 0.7, link * 0.32, link * 1.05)
            out.append(P(np.asarray(V) @ R.T + c, F, mat, "tablet"))
            V, F = M.box(link * 0.22, link * 0.36, link * 0.62)
            out.append(P(np.asarray(V) @ R.T + c, F, GLOW, "rune"))
        else:
            V, F = link_mesh(link, link * 0.62, wire)
            out.append(P(V @ R.T + c, F, mat, "link"))
        i += 1
        s += step
    return out


def helix_on_torso(z0, z1, turns, g, phase=0.0, n=40, rows=None):
    rows = rows or TORSO
    pts = []
    for i in range(n):
        t = i / (n - 1)
        z = z0 + (z1 - z0) * t
        f = (phase + turns * t) % 1.0
        pts.append(K.ring_frac(rows, z, g, [f])[0])
    return pts


def limb_helix(a, b, r, turns, n=24, phase=0.0):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = normalize(b - a)
    side = normalize(np.cross(d, (0, 1, 0))) if abs(d[1]) < 0.9 else np.array([1.0, 0, 0])
    fw = np.cross(side, d)
    out = []
    for i in range(n):
        t = i / (n - 1)
        ang = 2 * math.pi * (turns * t + phase)
        out.append(a + (b - a) * t + (side * math.cos(ang) + fw * math.sin(ang)) * r)
    return out


def hang(top, length, sway=(0.0, 0.0), n=6, droop=0.0):
    top = np.asarray(top, float)
    return [top + np.array([sway[0] * t * t, sway[1] * t * t - droop * math.sin(math.pi * t), -length * t])
            for t in np.linspace(0, 1, n)]


# ------------------------------------------------------------------------------------------------ weapon
def chain_censer():
    """Great chain-censer (weapon space: grip at origin, +Z away from the fist): an iron grip, a short heavy rigid
    chain, a big iron cage (bars, crown, spiked foot) with a white light burning inside."""
    parts = []
    V, F = M.lathe([(0.0, -0.16), (0.03, -0.16), (0.034, -0.13), (0.022, -0.1), (0.022, 0.08), (0.03, 0.1),
                    (0.03, 0.13), (0.0, 0.14)], 8)
    parts.append(P(V, F, "BH_DarkSteel", "grip"))
    V, F = M.lathe([(0.0, -0.1), (0.025, -0.1), (0.025, 0.07), (0.0, 0.07)], 8)
    parts.append(P(V, F, "BH_Leather", "wrap"))
    V, F = M.lathe([(0.0, 0.13), (0.03, 0.135), (0.0, 0.17)], 6)
    parts.append(P(V, F, "BH_DarkSteel", "eye"))
    parts += chain([(0, 0, 0.16), (0, 0, 0.36)], link=0.06, wire=0.011, rune_every=3, glow=True)
    # the cage
    zc0, zc1 = 0.39, 0.81
    rmax = 0.16
    V, F = M.lathe([(0.0, zc0 - 0.02), (0.06, zc0 - 0.02), (0.1, zc0 + 0.02), (0.07, zc0 + 0.04), (0.0, zc0 + 0.03)], 12)
    parts.append(P(V, F, "BH_DarkSteel", "crown"))
    for k in range(8):
        a = 2 * math.pi * k / 8
        bar = []
        for i in range(7):
            u = i / 6
            r = 0.06 + (rmax - 0.06) * math.sin(math.pi * u) ** 0.8
            bar.append((r * math.cos(a), r * math.sin(a), zc0 + 0.02 + (zc1 - zc0 - 0.04) * u))
        parts.append(A.tube(bar, 0.012, "BH_Steel", n=5))
    for zf in (0.38, 0.62):
        z = zc0 + 0.02 + (zc1 - zc0 - 0.04) * zf
        r = 0.06 + (rmax - 0.06) * math.sin(math.pi * zf) ** 0.8
        V, F = M.lathe([(r - 0.004, z - 0.012), (r + 0.012, z - 0.008), (r + 0.012, z + 0.008), (r - 0.004, z + 0.012)],
                       16, cap=False)
        parts.append(P(V, F, "BH_DarkSteel", "hoop"))
    V, F = M.lathe([(0.0, zc1 + 0.04), (0.07, zc1 + 0.02), (0.1, zc1 - 0.02), (0.06, zc1 - 0.03), (0.0, zc1 - 0.02)], 12)
    parts.append(P(V, F, "BH_DarkSteel", "foot"))
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4
        d = np.array([math.cos(a) * 0.6, math.sin(a) * 0.6, 1.0])
        parts.append(A.taper([(0.07 * math.cos(a), 0.07 * math.sin(a), zc1 + 0.0), np.array([0.07 * math.cos(a), 0.07 *
                                                                                             math.sin(a), zc1]) + d * 0.09],
                             0.018, 0.002, "BH_DarkSteel", n=5))
    parts.append(A.taper([(0, 0, zc1 + 0.03), (0, 0, zc1 + 0.15)], 0.025, 0.002, "BH_DarkSteel", n=6))
    # the light inside: a white core + a few shards of it
    zm = (zc0 + zc1) / 2
    parts.append(A.ball((0, 0, zm), 0.085, GLOW, n=10, rings=6, scale=(1, 1, 1.15)))
    for k in range(5):
        a = 2 * math.pi * k / 5
        d = np.array([math.cos(a), math.sin(a), 0.3 * (k % 2 * 2 - 1)])
        parts.append(A.shard((0, 0, zm), d, 0.12, 0.022, GLOW, sides=4, twist=20 * k))
    return parts


def iron_book():
    """Iron-bound book (local: spine along Z, cover faces -Y), centred at the origin."""
    parts = []
    V, F = M.box(0.13, 0.05, 0.17)
    parts.append(P(V, F, "BH_Bone", "pages"))
    for sy in (1, -1):
        V, F = M.box(0.145, 0.012, 0.185, center=(0, sy * 0.03, 0))
        parts.append(M.bevel(P(V, F, "BH_DarkSteel", "cover"), 0.003, 1))
    V, F = M.box(0.02, 0.07, 0.185, center=(-0.072, 0, 0))
    parts.append(P(V, F, "BH_DarkSteel", "spine"))
    for z in (-0.06, 0.06):
        V, F = M.box(0.15, 0.075, 0.018, center=(0, 0, z))
        parts.append(P(V, F, "BH_Steel", "band"))
    gl = [(-0.03, -0.038, -0.04), (-0.03, -0.038, 0.04), (0.03, -0.038, 0.04), (0.0, -0.038, 0.0), (0.03, -0.038, -0.04)]
    parts.append(A.tube(gl, 0.005, GLOW, n=4))
    return parts


# ------------------------------------------------------------------------------------------------ pieces
def over_robe(sb):
    """Black over-robe: two front panels from the collar to the shins (split down the centre) + a tattered back drape."""
    def half(z):
        return 0.095 + 0.06 * max(0.0, 1.05 - z)

    for sx, seed in ((1, 0.8), (-1, 2.3)):
        side = "L" if sx > 0 else "R"

        def fn(u, v, sx=sx, seed=seed):
            zb = 0.3 + HS.ragged(u, seed, 0.1, 3)
            zt = 1.47
            z = zt + (zb - zt) * v
            x = sx * (0.03 + 2 * half(z) * u)
            gap = G + 0.012
            if z >= 1.05:
                y = front_y(TORSO, x, z) - gap
            else:
                y = front_y(TORSO, x, 1.05) - gap - 0.1 * (1.05 - z) ** 1.1
            return (x, y, z)
        V, F = M.grid(fn, 6, 11)
        p = P(V, F, "BH_Cloth_Secondary", "overrobe")
        if sx < 0:
            p.flip()
        sb.add(M.solidify(p, 0.008, offset=1.0), weights=panel_w(side))
        # iron band hem
        hem = [np.array(fn(u, 0.98)) + (0, -0.006, 0.0) for u in np.linspace(0, 1, 6)]
        sb.add(A.tube(hem, (0.009, 0.006), "BH_DarkSteel", n=4), weights=panel_w(side))

    def fn(u, v):
        zb = 0.12 + HS.ragged(u, 4.1, 0.18, 5)
        z = 1.49 + (zb - 1.49) * v
        hw = 0.17 + 0.12 * v
        x = (u - 0.5) * 2 * hw
        if z > 1.2:
            y = back_y(TORSO, x * 0.95, z) + G + 0.03
        else:
            y = back_y(TORSO, x * 0.95, 1.2) + G + 0.03 + 0.07 * (1.2 - z)
        y += 0.012 * math.sin(u * math.pi * 5) * v
        return (x, y, z)
    V, F = M.grid(fn, 9, 12)
    p = P(V, F, "BH_Cloth_Secondary", "drape").flip()
    sb.add(M.solidify(p, 0.009, offset=1.0), weights=HS.cloth_w(chest_z=1.34, belt_z=1.05, leg=0.32))


def panel_w(side):
    def wfn(V):
        out = []
        for v in V:
            z = v[2]
            if z >= 1.30:
                out.append({"chest": 1.0})
            elif z >= 1.18:
                t = float(smoothstep(1.18, 1.30, z))
                out.append({"chest": t, "spine": 1 - t})
            elif z >= 1.03:
                t = float(smoothstep(1.03, 1.12, z))
                out.append({"spine": t, "hips": 1 - t} if t > 0 else {"hips": 1.0})
            else:
                s = float(smoothstep(1.0, 0.5, z)) * 0.8
                d = {"hips": 1 - s}
                if s > 1e-3:
                    d["thigh." + side] = s
                out.append(d)
        return out
    return wfn


def mantle_w(V):
    out = []
    for v in V:
        s = float(smoothstep(0.1, 0.24, abs(v[0]))) * 0.55
        b = "shoulder.L" if v[0] > 0 else "shoulder.R"
        out.append({"chest": 1 - s, b: s} if s > 1e-3 else {"chest": 1.0})
    return out


def mantle(sb):
    """Overlapping grey-iron lames over the shoulders (three tiers, flaring down), riveted, with a white rune row."""
    for k, (zt, zb, g0, g1) in enumerate(((1.53, 1.43, 0.03, 0.07), (1.47, 1.37, 0.06, 0.1), (1.41, 1.3, 0.09, 0.13))):
        rings = []
        for z, g in ((zb, g1), (zt, g0)):
            r = K.ring_frac(TORSO, max(min(z, 1.5), 1.0), g, np.linspace(0, 1, 33)[:-1])
            r[:, 2] = z
            rings.append(np.vstack([r, r[:1]]))
        V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
        sb.add(M.solidify(P(V, F, "BH_DarkSteel", "mantle"), 0.009, offset=1.0), weights=mantle_w)
        lo = rings[0][:-1]
        V, F = M.tube(np.vstack([lo, lo[:1]]), [(0.007, 0.007)] * (len(lo) + 1), n=4, up=(0, 0, 1), cap0=False,
                      cap1=False)
        sb.add(P(V, F, "BH_Steel", "mantle_rim"), weights=mantle_w)
        if k == 2:
            for i in range(0, 32, 2):
                q = lo[i]
                nrm = normalize(np.array([q[0], q[1], 0.0]))
                V, F = M.box(0.012, 0.006, 0.026)
                R = M_align_z(nrm)
                sb.add(P(np.asarray(V) @ Rx(90).T @ R.T * 1.0 + q + nrm * 0.006 + (0, 0, 0.03), F, GLOW, "rune"),
                       weights=mantle_w)
    # high iron collar behind the head
    rows = []
    for z, g in ((1.5, 0.03), (1.62, 0.05), (1.7, 0.075)):
        r = K.ring_frac(TORSO, min(z, 1.5), g, np.linspace(0.18, 0.82, 13))
        r[:, 2] = z
        rows.append(r)
    V, F = M.loft(rows, cap0=False, cap1=False, closed=False)
    sb.add(M.solidify(P(V, F, "BH_DarkSteel", "collar").flip(), 0.01, offset=1.0), "chest")


def stole(sb):
    """A black stole down the front hung with iron rune plaques."""
    for sx in (1, -1):
        pts, ups = [], []
        for t in np.linspace(0, 1, 9):
            z = 1.48 - 1.0 * t
            x = sx * (0.05 + 0.012 * t)
            if z > 1.05:
                y = front_y(TORSO, x, z) - G - 0.03
            else:
                y = front_y(TORSO, x, 1.05) - G - 0.03 - 0.1 * (1.05 - z) ** 1.1
            pts.append((x, y, z))
            ups.append((0, -1, 0))
        side = "L" if sx > 0 else "R"
        top = [q for q in pts if q[2] >= 1.0]
        low = [q for q in pts if q[2] <= 1.1]
        sb.add(K.strip(top, 0.05, 0.006, "BH_Cloth_Secondary", ups=ups[:len(top)]), weights=ROBE_W)
        sb.add(K.strip(low, 0.05, 0.006, "BH_Cloth_Secondary", ups=ups[:len(low)]), weights=panel_w(side))
        for i, z in enumerate((1.36, 1.2, 0.98, 0.76)):
            q = np.array(pts[min(range(9), key=lambda j: abs(pts[j][2] - z))]) + (0, -0.008, 0)
            V, F = M.box(0.05, 0.01, 0.065)
            w = ROBE_W if z > 1.05 else panel_w(side)
            sb.add(M.bevel(P(V, F, "BH_DarkSteel", "plaque").move(q), 0.004, 1), weights=w)
            g = [q + (-0.012, -0.007, -0.02), q + (-0.012, -0.007, 0.02), q + (0.012, -0.007, 0.0),
                 q + (0.012, -0.007, -0.02)]
            sb.add(A.tube(g, 0.0035, GLOW, n=4), weights=w)


def head(sb):
    K.neck_and_head(sb, skin="BH_Skin", eyes="BH_Shadow", eye_glow=GLOW, nose=True)
    # hollow cheeks / brow shadow
    for sx in (1, -1):
        V, F = M.sphere(0.02, 6, 4, center=(sx * 0.045, -0.06, 1.66), scale=(0.8, 0.4, 1.2))
        sb.add(P(V, F, "BH_Shadow", "cheek"), "head")
    # iron face-cage: a brow band and vertical bars curving under the chin
    band = [(0.085 * math.sin(a), -0.092 * math.cos(a) - 0.0, 1.735) for a in np.linspace(-1.5, 1.5, 11)]
    sb.add(A.tube(band, (0.01, 0.012), "BH_DarkSteel", n=5), "head")
    for a in np.linspace(-0.9, 0.9, 7):
        top = np.array([0.087 * math.sin(a), -0.095 * math.cos(a), 1.735])
        mid = np.array([0.083 * math.sin(a), -0.105 * math.cos(a), 1.66])
        bot = np.array([0.06 * math.sin(a), -0.085 * math.cos(a), 1.6])
        sb.add(A.tube([top, mid, bot], 0.0055, "BH_Steel", n=4), "head")
    chin = [(0.062 * math.sin(a), -0.087 * math.cos(a), 1.6) for a in np.linspace(-1.2, 1.2, 9)]
    sb.add(A.tube(chin, 0.007, "BH_DarkSteel", n=4), "head")
    mitre(sb)


def mitre(sb):
    """Tall iron crown-mitre: ribbed, pointed (front view), a spiked crown band, a rune plate, chain lappets."""
    rows = []
    for t in np.linspace(0, 1, 9):
        z = 1.76 + 0.34 * t
        rx = 0.108 * (1 - t) ** 0.85 + 0.008
        ry = 0.122 - 0.075 * t
        rows.append((z, rx, ry, ry, 0.0, 0.01))
    V, F = torso_loft(rows, n=20, p=2.4, cap0=False, cap1=True)
    sb.add(M.bevel(P(V, F, "BH_DarkSteel", "mitre"), 0.003, 1, angle=50), "head")
    # vertical ribs front and back + the seam over the top
    for sy in (-1, 1):
        rib = [(0.0, sy * (r[2] + 0.004) + 0.01, r[0]) for r in rows[:-1]]
        sb.add(A.tube(rib, (0.011, 0.008), "BH_Steel", n=5, up=(0, sy, 0)), "head")
    for sx in (1, -1):
        rib = [(sx * (r[1] * 0.98 + 0.002), 0.01, r[0]) for r in rows[:-1]]
        sb.add(A.tube(rib, 0.006, "BH_Steel", n=4), "head")
    # crown band with spikes
    V, F = M.lathe([(0.118, 1.74), (0.128, 1.745), (0.128, 1.795), (0.118, 1.8)], 20, cap=False)
    sb.add(M.solidify(P(V, F, "BH_Steel", "crownband").scale((1.0, 1.1, 1.0)).move((0, 0.01, 0)), 0.006, offset=-1),
           "head")
    for k in range(12):
        a = 2 * math.pi * k / 12
        c = np.array([0.13 * math.sin(a), 0.01 - 0.143 * math.cos(a), 1.79])
        out = np.array([math.sin(a), -math.cos(a), 0.0])
        h = 0.07 if k % 2 == 0 else 0.045
        sb.add(A.taper([c, c + normalize(out * 0.25 + np.array([0, 0, 1.0])) * h], 0.014, 0.0015, "BH_Steel", n=4),
               "head")
    # rune plate at the front of the mitre (white glyph: the chain-circle)
    y = -0.122 + 0.01 - 0.012
    V, F = M.box(0.07, 0.012, 0.09, center=(0, y, 1.86))
    sb.add(M.bevel(P(V, F, "BH_Steel", "plate"), 0.004, 1), "head")
    circ = [(0.024 * math.cos(a), y - 0.008, 1.86 + 0.028 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 13)]
    sb.add(A.tube(circ, 0.0045, GLOW, n=4), "head")
    sb.add(A.tube([(0, y - 0.008, 1.83), (0, y - 0.008, 1.89)], 0.0045, GLOW, n=4), "head")
    # chain lappets from the band down past the ears to the shoulders (head-bound, short)
    for sx in (1, -1):
        for dy in (0.0,):
            top = np.array([sx * 0.128, 0.01 + dy, 1.75])
            for prt in chain(hang(top, 0.17, sway=(sx * 0.02, 0.02)), link=0.026, wire=0.0042, rune_every=4,
                             start=int(dy > 0)):
                sb.add(prt, "head")


def arms(sb):
    for s in ("L", "R"):
        sx = 1 if s == "L" else -1
        C.bell_sleeve(sb, s, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", cuff_r=0.085, end=0.7)
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
        # iron vambrace under the cuff + chain wound round the forearm, its end hanging from the wrist
        V, F = M.tube([el + (wr - el) * 0.6, wr + (wr - el) * 0.05], [(0.05, 0.052), (0.046, 0.048)], n=12, up=(0, -1, 0))
        sb.add(P(V, F, "BH_DarkSteel", "vambrace"), fa)
        for prt in chain(limb_helix(el + (wr - el) * 0.62, wr, 0.058, 1.4, n=16), link=0.03, wire=0.0048,
                         rune_every=6):
            sb.add(prt, fa)
        tail = [wr + np.array([0, 0.0, -0.01]) + np.array([0.0, 0.01 * t, -0.18 * t]) for t in np.linspace(0, 1, 5)]
        for prt in chain(tail, link=0.026, wire=0.0045, rune_every=4, start=1):
            sb.add(prt, ha)
        # upper-arm iron band
        c = sh + (el - sh) * 0.55
        d = normalize(el - sh)
        V, F = M.tube([c - d * 0.02, c + d * 0.02], [(0.07, 0.072)] * 2, n=12, up=(0, -1, 0))
        sb.add(P(V, F, "BH_DarkSteel", "armband"), ua)
    # hands: grey gaunt fists, iron knuckle plates
    K.add_fist(sb, "R", "BH_DarkSteel", "BH_Skin", gauntlet=True, scale=1.05)
    K.add_fist(sb, "L", "BH_DarkSteel", "BH_Skin", gauntlet=True, scale=1.05)


def belt_and_chains(sb):
    rows = K.grow_rows(TORSO, G + 0.012)
    V, F = K.band(TORSO, 0.99, 1.07, G + 0.03, G + 0.006, n=30)
    sb.add(P(V, F, "BH_DarkSteel", "belt"), "hips")
    by = front_y(TORSO, 0, 1.03) - G - 0.035
    V, F = M.box(0.09, 0.02, 0.1, center=(0, by, 1.03))
    sb.add(M.bevel(P(V, F, "BH_Steel", "buckle"), 0.006, 1), "hips")
    circ = [(0.03 * math.cos(a), by - 0.012, 1.03 + 0.03 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 13)]
    sb.add(A.tube(circ, 0.005, GLOW, n=4), "hips")
    # iron bands on the robe chest
    for z in (1.18, 1.3):
        V, F = K.band(TORSO, z, z + 0.03, G + 0.018, G + 0.002, n=28)
        sb.add(P(V, F, "BH_DarkSteel", "band"), weights=ROBE_W)
    # the great rune-chain wrapped round the body: right shoulder -> across -> left hip, twice round
    pts = helix_on_torso(1.44, 1.06, 1.6, G + 0.03, phase=0.82)
    for prt in chain(pts, link=0.042, wire=0.0068, rune_every=5):
        sb.add(prt, weights=ROBE_W)
    # chains trailing from the belt toward the floor (front-left, right hip, back)
    for frac, ln, side, st in ((0.08, 0.72, "L", 0), (0.72, 0.62, "R", 1), (0.47, 0.76, "R", 0)):
        p, _ = K.on_ring(TORSO, 1.0, G + 0.04, frac)
        out = normalize(np.array([p[0], p[1], 0.0]))
        pts = [p + out * 0.04 * math.sin(math.pi * t * 0.8) * 2 + np.array([0, 0, -ln * t]) for t in np.linspace(0, 1, 7)]
        w = sb.skirt(1.02, 0.4, max_leg=0.55, center_w=0.06)
        for prt in chain(pts, link=0.04, wire=0.0065, rune_every=4, start=st):
            sb.add(prt, weights=w)
    # the iron book on a short chain at the left hip
    p, ang = K.on_ring(TORSO, 1.0, G + 0.05, 0.21)
    top = p + np.array([0, 0, -0.02])
    bc = top + np.array([0.02, 0.0, -0.2])
    w = sb.skirt(1.02, 0.6, max_leg=0.45, center_w=0.06)
    for prt in chain([top, bc + (0, 0, 0.09)], link=0.026, wire=0.0045, rune_every=0):
        sb.add(prt, weights=w)
    for prt in iron_book():
        prt.rot(Rz(ang + 90)).move(bc)
        sb.add(prt, weights=w)


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(P(V, F, "BH_Cloth_Primary", "body"), weights=ROBE_W)
    C.robe_top(sb, "BH_Cloth_Primary", trim="BH_DarkSteel", g=G, rows=TORSO, v_open=0.0)
    C.robe_skirt(sb, "BH_Cloth_Primary", trim="BH_DarkSteel", z_top=1.07, z_bot=0.03, flare=0.2, folds=0.018,
                 ragged=0.0, g=G)
    over_robe(sb)
    mantle(sb)
    stole(sb)
    belt_and_chains(sb)
    head(sb)
    arms(sb)
    K.trousers(sb, "BH_Cloth_Secondary", loose=0.9)
    K.boots(sb, "BH_DarkSteel", "BH_Steel", shaft_top=0.3, cuff=False)
    cz = chain_censer()
    for prt in cz:
        prt.V = prt.V * SCALE
    K.add_weapon(sb, "R", cz)
