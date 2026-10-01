"""Townsfolk (bh-029, Zarael): Terax, Warden of Agdao.

A broad-shouldered, seasoned warrior-guard: a quilted cotton armour vest (cream / ochre) with brick-red stepped-fret
borders over a jade-green under-tunic and kilt (BH_Cloth_Primary, tinted by the game), a short shoulder cape of teal
feathers, bronze forearm guards wound with copper wire (one thin white-glowing wire at each wrist), a jade pendant, a
jade-green crested helm with a fan of teal feathers tipped red (the portrait), short dark hair, a scar through the
right brow, laced sandals with leg wraps and an obsidian-bladed spear slung diagonally across the back (rigid to the
chest bone).

This module also holds the small ZARAEL TOWNSFOLK KIT (feathers, stepped-fret bands, wire bracelets, the white glow
spec) used by the other bh-029 Agdao modules (town_wirekeeper, town_ilsa, town_agdao_*).
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import front_y, back_y, interp_rows, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import town_matron as K
from town_matron import Kit, P_, pal, rope, lerp
from town_elder import shawl_surface, shawl_w
from char_mage import ring_frac

# ================================================================================================================
# ZARAEL TOWNSFOLK KIT
# ================================================================================================================
# The one glow of Zarael: PURE WHITE (albedo and emission 1,1,1), moderate energy; always small on townsfolk.
WHITE_GLOW = ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 4.5, 1.0)


def feather(base, d, L, W, side, mat="BH_Feather", tip_mat=None, tip=0.28, bend=0.08, nv=5, th=0.004,
            name="feather"):
    """Flat two-sided feather (vane with a slight V across the rib) from `base` along `d`, its flat across `side`.
    The last `tip` fraction uses tip_mat (e.g. red-tipped crest feathers). Model-space units (no Kit scaling)."""
    base = np.asarray(base, float)
    d = normalize(np.asarray(d, float))
    s = np.asarray(side, float)
    s = normalize(s - d * np.dot(s, d))
    nrm = np.cross(d, s)

    def mk(v0, v1, n):
        def fn(u, v):
            vv = v0 + (v1 - v0) * v
            w = W * math.sin(math.pi * min(1.0, 0.1 + 0.9 * vv)) ** 0.55 * (1 - 0.25 * vv)
            uu = (u - 0.5) * 2
            return base + d * L * vv + s * uu * w + nrm * (bend * L * vv * vv - 0.22 * w * abs(uu))
        V, F = M.grid(fn, 3, n)
        return V, F
    parts = []
    if tip_mat and tip > 0:
        V, F = mk(0.0, 1.0 - tip, max(2, nv - 1))
        parts.append(M.solidify(P_(V, F, mat, name), th, offset=0.0))
        V, F = mk(1.0 - tip, 1.0, 3)
        parts.append(M.solidify(P_(V, F, tip_mat, name + "_tip"), th, offset=0.0))
    else:
        V, F = mk(0.0, 1.0, nv)
        parts.append(M.solidify(P_(V, F, mat, name), th, offset=0.0))
    return parts


def fret_band(k, rows, z, g, h=0.03, band_mat="BH_Cloth_Accent", step_mat="BH_Cloth_Secondary", n=22,
              w=None, bone="hips", fr=None):
    """Stepped-fret border around a garment ring at height z (standard units): a coloured band with a row of small
    raised step blocks alternating high / low (reads as the stepped key pattern up close, as a bright border far).
    fr: optional (a0, a1) angle-fraction span for open garments."""
    if fr is None:
        K.band(k, rows, z - h / 2, z + h / 2, band_mat, g_out=g + 0.006, g_in=g - 0.002, n=24, bone=bone, w=w, bev=0.0)
        fracs = [(i + 0.5) / n for i in range(n)]
    else:
        from char_knight import arc_band
        V, F = arc_band(rows, z - h / 2, z + h / 2, g + 0.006, fr[0], fr[1], n=max(6, n))
        p = M.solidify(P_(V, F, band_mat, "fret_band"), 0.006, offset=1.0)
        k.add(p, bone=None if w else bone, w=w)
        fracs = [fr[0] + (fr[1] - fr[0]) * (i + 0.5) / n for i in range(n)]
    for i, f in enumerate(fracs):
        q, ang = K.on_ring(rows, z + (0.0055 if i % 2 else -0.0055) * (h / 0.03), g + 0.008, f)
        bw = 0.6 * (2 * math.pi * 0.16 / n)
        V, F = M.box(bw, 0.006, h * 0.42)
        p = P_(V, F, step_mat, "fret_step").rot(Rz(ang)).move(q)
        k.add(p, bone=None if w else bone, w=w)


def wire_bracelet(k, side, t, r, glow=True, turns=3, mat="BH_Gold"):
    """Copper wire wound round the forearm at arm parameter t (see K.sleeve): a few thin turns, the middle one a
    white-glowing Heartwire thread (small)."""
    for i in range(turns):
        tt = t + (i - (turns - 1) / 2) * 0.035
        m = "BH_Emissive" if (glow and i == turns // 2) else mat
        rr = r + (0.002 if m == "BH_Emissive" else 0.0)
        K.arm_ring(k, side, tt, rr, 0.016 if m == "BH_Emissive" else 0.02, m, name="wire")


def wrap_spiral(k, bone_a, bone_b, t0, t1, r, turns, mat="BH_Leather", w=0.012, th=0.004, n=40, bone=None):
    """Strip wound round the segment head(bone_a) -> head(bone_b) between fractions t0..t1 (model space)."""
    b = k.b
    a, c = b.head(bone_a), b.head(bone_b)
    dd = normalize(c - a)
    e1 = normalize(np.cross(dd, (0, 1.0, 0)) if abs(dd[1]) < 0.9 else np.cross(dd, (1.0, 0, 0)))
    e2 = np.cross(dd, e1)
    pts = []
    for i in range(n + 1):
        t = i / n
        p = a + (c - a) * lerp(t0, t1, t)
        ang = t * 2 * math.pi * turns
        pts.append(p + (e1 * math.cos(ang) + e2 * math.sin(ang)) * r * k.s)
    V, F = M.tube(pts, [(th * k.s, w * k.s)] * len(pts), n=4, up=tuple(dd), p=3.0)
    b.add(P_(V, F, mat, "wrap"), bone or bone_a)


# ================================================================================================================
# TERAX
# ================================================================================================================
PROPS = proportions(1.02, shoulder_x=0.205 * 1.02, hip_x=0.103 * 1.02)
PALETTE = "town_terax"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.10, 0.24, 0.17)),              # preview: jade-green tunic / kilt (game tint 0.3,0.5,0.4)
    "BH_Cloth_Secondary": pal((0.60, 0.50, 0.34), 0.92),      # quilted cotton armour (cream / ochre)
    "BH_Cloth_Accent": pal((0.36, 0.07, 0.04), 0.88),         # brick-red fret borders, sash
    "BH_Feather": pal((0.03, 0.27, 0.24), 0.7),               # teal feathers
    "BH_FeatherRed": pal((0.50, 0.06, 0.04), 0.7),            # scarlet feather tips
    "BH_Jade": pal((0.07, 0.36, 0.25), 0.3),                  # helm, pendant
    "BH_Bronze": pal((0.50, 0.31, 0.13), 0.4, 1.0),           # arm guards
    "BH_Gold": pal((0.74, 0.46, 0.20), 0.35, 1.0),            # copper wire, fittings
    "BH_Obsidian": pal((0.02, 0.02, 0.025), 0.12, 0.3),       # spear blade
    "BH_Skin": pal((0.36, 0.21, 0.13), 0.55),
    "BH_Scar": pal((0.55, 0.34, 0.26), 0.6),
    "BH_Hair": pal((0.03, 0.022, 0.018), 0.6),
    "BH_Wood": pal((0.20, 0.12, 0.06), 0.7),                  # spear shaft
    "BH_Leather": pal((0.14, 0.08, 0.04), 0.65),
    "BH_Emissive": WHITE_GLOW,                                # wrist wires (small)
})

T_TORSO = K.torso_rows(chest=1.12, waist=1.02, hip=1.02, depth=1.07, shoulder=1.1)
VEST_G = 0.022


def build(body):
    k = Kit(body)
    rows = T_TORSO
    # ---- under-tunic (tinted) + quilted armour vest
    K.body_shell(k, rows, 0.96, 1.53, "BH_Cloth_Primary", n=26, cap1=True, name="tunic")
    vest(k, rows)
    # ---- kilt + front flap, sash belt
    kilt(k, rows)
    # ---- arms: bare muscular upper arms, bronze forearm guards, copper wire, white wrist thread
    for s in "LR":
        K.sleeve(k, s, [(-0.2, 0.03, 0.034), (-0.13, 0.055, 0.058), (-0.05, 0.066, 0.068), (0.05, 0.068, 0.07),
                        (0.4, 0.064, 0.066), (0.75, 0.056, 0.056), (1.0, 0.05, 0.05), (1.2, 0.053, 0.05)],
                 "BH_Skin", n=12, name="arm")
        K.arm_ring(k, s, 0.42, 0.069, 0.035, "BH_Gold", name="armband")
        K.sleeve(k, s, [(1.12, 0.056, 0.054), (1.4, 0.06, 0.056), (1.75, 0.052, 0.048), (1.92, 0.056, 0.05)],
                 "BH_Bronze", n=12, name="vambrace")
        for t in (1.3, 1.52):
            K.arm_ring(k, s, t, 0.063, 0.02, "BH_Gold", name="wire")
        K.arm_ring(k, s, 1.9, 0.059, 0.016, "BH_Emissive", name="wrist_glow")
        K.mitten(k, s, size=1.06)
    # ---- legs: bare legs under the kilt, laced sandals and leg wraps
    for s in "LR":
        K.leg_tube(k, s, [(-0.02, 0.085, 0.088), (0.4, 0.074, 0.078), (1.0, 0.052, 0.055), (1.35, 0.056, 0.058),
                          (1.75, 0.04, 0.042), (2.0, 0.036, 0.038)], "BH_Skin", n=10)
        wrap_spiral(k, "shin." + s, "foot." + s, 0.08, 0.92, 0.05, 4.5, "BH_Leather", w=0.011)
        b = k.b
        kn = b.head("shin." + s)
        a = b.tail("shin." + s)
        c = kn + (a - kn) * 0.07
        V, F = M.tube([c - (0, 0, 0.025), c + (0, 0, 0.02)], [(0.06, 0.064), (0.062, 0.066)], n=12, up=(0, -1, 0),
                      cap0=False, cap1=False)
        b.add(M.solidify(P_(V, F, "BH_Bronze", "knee_guard"), 0.006, offset=-1.0), "shin." + s)
    K.bare_foot(k, sandal="BH_Leather")
    # ---- feather cape, pendant, spear
    cape(k, rows)
    pendant(k, rows)
    spear(k, rows)
    # ---- head: strong jaw, heavy brow, scar, short hair, crested helm
    hr = K.head(k, jaw=1.08, width=1.03, nose=1.06, brow=1.35, neck_r=0.058)
    scar(k, hr)
    helm(k, hr)
    K.check_normals(body, "terax")


def vest(k, rows):
    K.body_shell(k, rows, 0.97, 1.50, "BH_Cloth_Secondary", g=VEST_G, n=26, cap1=False, name="vest")
    # quilting: raised horizontal ridges
    for z in (1.07, 1.15, 1.23, 1.31, 1.39):
        K.band(k, rows, z - 0.012, z + 0.012, "BH_Cloth_Secondary", g_out=VEST_G + 0.008, g_in=VEST_G - 0.004, n=26,
               w=k.torso_w(), bev=0.0)
    # shoulder line: a thick rolled collar of the vest
    top = []
    for a in np.linspace(0, 2 * math.pi, 21):
        top.append((0.105 * math.sin(a), 0.004 - 0.085 * math.cos(a), 1.505 + 0.01 * math.cos(a)))
    V, F = M.tube(top, [(0.014, 0.014)] * len(top), n=6, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Cloth_Accent", "collar"), "chest")
    # stepped-fret border at the hem
    fret_band(k, rows, 0.995, VEST_G, h=0.034, n=24, w=k.torso_w())
    # sleeve holes: dark band where the arms leave the vest (reads as an armhole edge)


def kilt(k, rows):
    r0 = interp_rows(rows, 0.98)
    g = 0.03
    sk_rows = K.flare_rows(0.99, 0.6, (r0[1] + g, r0[2] + g, r0[3] + g), (0.215, 0.17, 0.18), n=5, curve=1.0)
    sk, rings = K.skirt(sk_rows, "BH_Cloth_Primary", folds=10, amp=0.008, n=30)
    k.add(sk, w=k.skirt_w(1.0, 0.6, max_leg=0.85))
    # brick-red hem stripe
    hem = rings[0] + np.array([0, 0, 0.012])
    V, F = M.tube(np.vstack([hem, hem[:1]]), [(0.012, 0.004)] * (len(hem) + 1), n=4, up=(0, 0, 1), p=3.0,
                  cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Cloth_Accent", "kilt_hem"), w=k.skirt_w(1.0, 0.6, max_leg=0.85))
    # wide sash belt (brick red) with a knot and tails at the left hip
    K.band(k, rows, 0.965, 1.035, "BH_Cloth_Accent", g_out=VEST_G + 0.02, g_in=VEST_G - 0.004, n=26)
    q, ang = K.on_ring(rows, 0.99, VEST_G + 0.03, 0.2)
    q = np.asarray(q)
    V, F = M.sphere(0.03, 8, 6, center=q, scale=(0.8, 1.0, 1.0))
    k.add(P_(V, F, "BH_Cloth_Accent", "sash_knot"), "hips")
    for dy, L in ((-0.012, 0.22), (0.014, 0.17)):
        V, F = M.tube([q + (0.004, dy, -0.01), q + (0.012, dy, -L)], [(0.006, 0.026), (0.006, 0.03)], n=6,
                      up=(0, -1, 0), p=3.0)
        k.add(P_(V, F, "BH_Cloth_Accent", "sash_tail"), w=k.skirt_w(1.0, 0.75, max_leg=0.4))
    # front flap: cream panel with a fret hem hanging between the legs
    def fn(u, v):
        x = (u - 0.5) * 2 * lerp(0.085, 0.1, v)
        z = lerp(0.96, 0.5, v)
        y = front_y(sk_rows, x, min(z, 0.99), p=2.2) - 0.012 - 0.01 * v
        return (x, y, z)
    V, F = M.grid(fn, 5, 7)
    fl = M.solidify(P_(V, F, "BH_Cloth_Secondary", "flap").flip(), 0.006, offset=-1.0)
    fw = k.skirt_w(1.0, 0.6, max_leg=0.6, center_w=0.4)
    k.add(fl, w=fw)
    for zz, mat in ((0.53, "BH_Cloth_Accent"), (0.585, "BH_Cloth_Accent")):
        V, F = M.box(0.2, 0.008, 0.022 if zz < 0.55 else 0.012)
        y = front_y(sk_rows, 0, 0.6, p=2.2) - 0.022 - 0.01 * (0.96 - zz) / 0.46
        k.add(P_(V, F, mat, "flap_band").move((0, y, zz)), w=fw)
    for i in range(5):
        x = -0.08 + i * 0.04
        V, F = M.box(0.018, 0.008, 0.016)
        y = front_y(sk_rows, 0, 0.6, p=2.2) - 0.024 - 0.01 * (0.96 - 0.56) / 0.46
        k.add(P_(V, F, "BH_Gold", "flap_step").move((x, y, 0.556 + (0.008 if i % 2 else -0.004))), w=fw)


def cape(k, rows):
    """Short shoulder cape: a teal feather-cloth mantle, its hem layered with hanging feathers."""
    rings = shawl_surface(36, 6, math.radians(26), (0.11, 0.09, 0.095), (0.31, 0.21, 0.23), 0.13, 0.22, 0.30, 1.585)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Feather", "cape"), 0.012, offset=1.0), w=shawl_w(k))
    # collar roll of red cloth
    V, F = M.tube(rings[-1][::2], [(0.012, 0.012)] * len(rings[-1][::2]), n=6, up=(0, 0, 1))
    k.add(P_(V, F, "BH_Cloth_Accent", "cape_collar"), w=shawl_w(k))
    # two layers of hanging feathers along the hem and the middle ring
    s = k.s
    for ring, L, every, tipm in ((rings[0], 0.13, 2, "BH_FeatherRed"), (rings[2], 0.11, 4, None)):
        c0 = ring.mean(0)
        for i in range(1, len(ring) - 1, every):
            p = ring[i]
            out = normalize(np.array([p[0] - c0[0], p[1] - c0[1], 0.0]))
            d = normalize(np.array([0, 0, -1.0]) + out * 0.35)
            side = np.cross(d, out)
            for prt in feather(p * s - d * 0.01 * s, d, L * s, 0.026 * s, side, "BH_Feather", tipm, tip=0.3,
                               bend=-0.12, nv=4, th=0.003 * s):
                k.b.add(prt, weights=shawl_w(k))
    # jade-and-copper clasps at the collarbones
    for sx in (1, -1):
        V, F = M.lathe([(0, -0.006), (0.02, -0.005), (0.022, 0.004), (0, 0.007)], 10)
        k.add(P_(V, F, "BH_Gold", "clasp").rot(Rx(90)).move((sx * 0.085, -0.115, 1.49)), "chest")
        V, F = M.sphere(0.012, 8, 5, center=(sx * 0.085, -0.124, 1.49), scale=(1, 0.6, 1))
        k.add(P_(V, F, "BH_Jade", "clasp_stone"), "chest")


def pendant(k, rows):
    pts = []
    for a in np.linspace(-1.0, 1.0, 11):
        x = 0.075 * math.sin(a)
        z = 1.47 - 0.11 * math.cos(a) ** 2
        pts.append((x, front_y(rows, x, z) - VEST_G - 0.016, z))
    k.add(rope(pts, 0.0035, "BH_Leather"), "chest")
    c = np.array([0.0, front_y(rows, 0, 1.33) - VEST_G - 0.02, 1.33])
    V, F = M.lathe([(0, -0.007), (0.03, -0.006), (0.034, 0.0), (0.03, 0.006), (0, 0.007)], 14)
    k.add(P_(V, F, "BH_Jade", "pendant").rot(Rx(90)).move(c), "chest")
    ring = K.ring_pts(c + (0, -0.002, 0), 0.034, (0, -1, 0), n=14)[::-1]
    V, F = M.tube(ring, [(0.004, 0.004)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Gold", "pendant_rim"), "chest")
    # carved step glyph on the face (gold inlay)
    for dx, dz, w, h in ((0, -0.008, 0.03, 0.007), (0, 0.004, 0.016, 0.017)):
        V, F = M.box(w, 0.004, h, center=c + (dx, -0.008, dz))
        k.add(P_(V, F, "BH_Gold", "glyph"), "chest")


def spear(k, rows):
    """Spear slung across the back: butt low on the right, head above the left shoulder (rigid to the chest)."""
    a = np.array([-0.22, 0.24, 0.62])
    b = np.array([0.30, 0.22, 2.02])
    d = normalize(b - a)
    side = normalize(np.cross(d, (0, 1.0, 0)))
    V, F = M.tube([a, a + (b - a) * 0.5, b], [(0.016, 0.016)] * 3, n=8, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Wood", "shaft"), "chest")
    # copper-wire bindings + butt cap
    for t in (0.0, 0.93, 0.96):
        c = a + (b - a) * t
        V, F = M.tube([c - d * 0.016, c + d * 0.016], [(0.02, 0.02)] * 2, n=8, up=(0, -1, 0))
        k.add(P_(V, F, "BH_Gold" if t > 0 else "BH_Bronze", "binding"), "chest")
    # obsidian leaf blade (flat, faces the back)
    L, W = 0.24, 0.04
    outline = []
    for t in np.linspace(0, 1, 7):
        outline.append((W * math.sin(math.pi * min(1, 0.15 + t)) ** 0.7 * (1 - t * 0.6), t * L))
    pts2 = [(-u, v) for u, v in outline] + [(u, v) for u, v in outline[::-1]]
    V = []
    for u, v in pts2:
        V.append(b + d * (v + 0.01) + side * u)
    V = np.array(V)
    n = len(pts2)
    yb = np.cross(d, side) * 0.006
    Vb = np.vstack([V + yb, V - yb, (b + d * (L * 0.45))[None] + yb * 2.2, (b + d * (L * 0.45))[None] - yb * 2.2])
    F = []
    cf, cb = 2 * n, 2 * n + 1
    for i in range(n):
        j = (i + 1) % n
        F.append((i, j, cf))
        F.append((n + j, n + i, cb))
        F.append((i, n + i, n + j, j))
    blade = K.outward(P_(Vb, F, "BH_Obsidian", "blade"))
    k.add(blade, "chest")
    # feather tassel under the head
    c = a + (b - a) * 0.9
    for i, ang in enumerate((-30, 0, 30)):
        dd = normalize(Rz(ang) @ np.array([0, 0.3, -1.0]))
        for prt in feather(c + side * 0.01 * (i - 1), dd, 0.1, 0.018, side, "BH_Feather", "BH_FeatherRed", tip=0.35,
                           nv=4, th=0.003):
            k.add(prt, "chest")


def scar(k, hr):
    pts = []
    for t in np.linspace(0, 1, 5):
        x = lerp(-0.052, -0.016, t)
        z = lerp(1.742, 1.664, t)
        y = front_y(hr, x, z, p=2.1) - 0.0035
        pts.append((x, y, z))
    k.add(rope(pts, 0.0035, "BH_Scar", n=5), "head")


def helm(k, hr):
    # short dark hair: sideburns and nape under the helm
    line = K.hairline(1.745, 1.665, 1.62, sharp=0.8)
    V, F = K.head_shell(hr, 0.008, line, nu=22, nv=4)
    k.add(P_(V, F, "BH_Hair", "hair"), "head")
    # jade-green helm cap
    hl = K.hairline(1.772, 1.725, 1.69, sharp=0.9)
    V, F = K.head_shell(hr, lambda v: 0.02 + 0.008 * (1 - v), hl, nu=26, nv=6, top_bulge=0.016)
    k.add(M.solidify(P_(V, F, "BH_Jade", "helm"), 0.008, offset=-1.0), "head")
    # gold fret rim
    us = np.linspace(0, 1, 27)
    rim = [K.ring_frac(hr, hl(u), 0.03, [u], p=2.1)[0] for u in us]
    rim = [(r[0], r[1], hl(u)) for r, u in zip(rim, us)]
    V, F = M.tube(rim, [(0.008, 0.013)] * len(rim), n=6, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Gold", "helm_rim"), "head")
    for i, u in enumerate(np.linspace(-0.2, 0.2, 9)):
        q = K.ring_frac(hr, hl(u), 0.036, [u], p=2.1)[0]
        V, F = M.box(0.012, 0.006, 0.01)
        ang = math.degrees(2 * math.pi * u)
        k.add(P_(V, F, "BH_Cloth_Accent", "helm_step").rot(Rz(ang)).move((q[0], q[1], hl(u) + (0.006 if i % 2 else -0.004))),
              "head")
    # crest socket on the crown and a fan of teal feathers tipped red, fanned side to side, leaning back
    top = np.array([0.0, 0.005, hr[-1][0] + 0.03])
    V, F = M.box(0.05, 0.03, 0.03, center=top + (0, 0, -0.004))
    k.add(M.bevel(P_(V, F, "BH_Gold", "crest_socket"), 0.005, 1), "head")
    V, F = M.sphere(0.009, 8, 5, center=top + (0, -0.017, -0.002))
    k.add(P_(V, F, "BH_Jade", "crest_stone"), "head")
    for i, ang in enumerate(np.linspace(-38, 38, 7)):
        d = normalize(Ry(ang) @ normalize(np.array([0, 0.28, 1.0])))
        L = 0.24 - 0.05 * abs(ang) / 38
        for prt in feather(top + (math.sin(math.radians(ang)) * 0.012, 0.004 * (i % 2), 0.0), d, L, 0.03,
                           (1.0, 0.0, 0.0), "BH_Feather", "BH_FeatherRed", tip=0.22, bend=0.06, nv=5, th=0.004):
            k.add(prt, "head")
