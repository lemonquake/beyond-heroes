"""Mossback Idol (bh-029, Builder M1, Zarael / the Coilwood construct brute): a squat ~2.8 m Wirewright idol of
pale carved limestone that has walked out of the jungle. A huge blocky head sunk between slab shoulders: a heavy
brow over two deep eye-slots burning violet-red, a stepped nose, a wide fret-mouth (stone teeth in a stepped
pattern, the glow behind them), jade ear spools, a stepped crown with a carved fret front. Wide chest and belly
blocks bound with tarnished copper bands, short pillar legs on slab feet, long arms ending in block fists. The old
wire channels inlaid over every block are cracked: the Blackwire burns in the broken lines. Thick moss on the crown,
shoulders and back, roots grown over the shoulders and hanging down the back and arms.

Built at true size on the shared humanoid skeleton (custom squat proportions). Clips: boss_charge boss_slam
cast_heavy gs_1 (no weapon: the fists strike)."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, interp_rows  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as GK  # noqa: E402
import enemy_rune_golem as RG  # noqa: E402
import enemy_glyphbound_warrior as Z  # noqa: E402

PROPS = proportions(
    1.5,
    pelvis_h=0.95, hip_h=0.89, knee_h=0.5, ankle_h=0.14, hip_x=0.27, ball_fwd=0.27, ball_h=0.05, toe_len=0.13,
    heel_back=0.12,
    hips_len=0.18, spine_len=0.3, chest_len=0.6, neck_len=0.05, head_len=0.45,
    clav_x0=0.12, clav_drop=0.2, shoulder_x=0.6, upper_len=0.5, fore_len=0.56, hand_len=0.22, grip_x=0.14,
    grip_drop=0.03,
)
L = GK.levels(PROPS)
PREVIEW_HEIGHT = 3.1

PALETTE = "mossback_idol"
PALETTE_COLORS = {
    "BH_Stone": ((0.42, 0.39, 0.31), 0.0, 0.92, None, 0.0, 1.0),           # pale weathered limestone
    "BH_DarkSteel": ((0.13, 0.125, 0.11), 0.0, 0.9, None, 0.0, 1.0),      # dark joint stones / core
    "BH_Gold": ((0.42, 0.27, 0.14), 0.85, 0.5, None, 0.0, 1.0),            # tarnished copper bands
    "BH_Bronze": ((0.42, 0.27, 0.14), 0.85, 0.5, None, 0.0, 1.0),          # fist straps (same copper)
    "BH_Cloth_Secondary": ((0.1, 0.19, 0.045), 0.0, 1.0, None, 0.0, 1.0),  # moss
    "BH_Fur": ((0.16, 0.24, 0.07), 0.0, 1.0, None, 0.0, 1.0),              # lighter moss tufts
    "BH_Wood": ((0.11, 0.075, 0.045), 0.0, 0.85, None, 0.0, 1.0),          # roots
    "BH_Horn": ((0.08, 0.33, 0.26), 0.0, 0.35, None, 0.0, 1.0),            # jade spools
    "BH_Shadow": ((0.015, 0.013, 0.012), 0.0, 0.85, None, 0.0, 1.0),       # carved recesses / cracks
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),  # Zarael glows are white
}
CLIPS = ["boss_charge", "boss_slam", "cast_heavy", "gs_1"]

P = Z.P
block, band, slab, local_box, stone_limb = RG.block, RG.band, RG.slab, RG.local_box, RG.stone_limb
fy, by = RG.fy, RG.by
FRONT, BACK = np.array([0, -1.0, 0]), np.array([0, 1.0, 0])

zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
PELV = [(zh - 0.2, 0.34, 0.24, 0.24, 0.0), (zh - 0.1, 0.44, 0.3, 0.29, 0.0), (zh + 0.08, 0.46, 0.31, 0.3, 0.0),
        (zh + 0.17, 0.43, 0.29, 0.28, 0.0)]
ABDO = [(zs - 0.06, 0.42, 0.3, 0.28, 0.0), (zs + 0.08, 0.5, 0.36, 0.3, 0.0), (zs + 0.24, 0.52, 0.37, 0.31, 0.0),
        (zs + 0.32, 0.5, 0.35, 0.3, 0.0)]
CHEST = [(zc - 0.06, 0.5, 0.35, 0.31, 0.0, 0.0), (zc + 0.08, 0.6, 0.4, 0.36, 0.0, -0.01),
         (zc + 0.3, 0.7, 0.44, 0.42, 0.0, -0.02), (zc + 0.5, 0.74, 0.44, 0.46, 0.0, 0.0),
         (zn - 0.02, 0.68, 0.4, 0.44, 0.0, 0.02), (zn + 0.06, 0.5, 0.3, 0.34, 0.0, 0.03)]
HEADB = [(-0.14, 0.27, 0.27, 0.24, 0.0, -0.1), (-0.04, 0.31, 0.31, 0.26, 0.0, -0.12), (0.18, 0.33, 0.33, 0.27, 0.0, -0.13),
         (0.38, 0.32, 0.32, 0.27, 0.0, -0.13), (0.46, 0.29, 0.29, 0.25, 0.0, -0.12)]


def hrows():
    z0 = L["head"]
    return [(z0 + r[0], r[1], r[2], r[3], r[4], r[5]) for r in HEADB]


def addp(body, parts, bone=None, weights=None):
    for prt in parts:
        body.add(prt, bone, weights)


def moss(c, nrm, size, seed, cnt=4, flat=0.32):
    """A mat of moss: a few flattened lumpy blobs + small lighter tufts on a surface (normal nrm)."""
    rng = np.random.default_rng(seed)
    n = normalize(nrm)
    from bh_body import M_align_z
    R = M_align_z(n)
    out = []
    for k in range(cnt):
        off = (rng.random(3) - 0.5) * size * 1.4
        off -= n * np.dot(off, n)
        b = GK.blob((0, 0, 0), size * (0.45 + 0.35 * rng.random()), "BH_Cloth_Secondary", scale=(1.0, 0.9, flat),
                    n=8, rings=4)
        GK.jitter(b, size * 0.06, seed=seed * 10 + k)
        b.V = b.V @ R.T + np.asarray(c, float) + off
        out.append(b)
    for k in range(cnt // 2 + 1):
        off = (rng.random(3) - 0.5) * size * 1.2
        off -= n * np.dot(off, n)
        b = GK.blob((0, 0, 0), size * 0.22, "BH_Fur", scale=(1.0, 1.0, 0.8), n=6, rings=3)
        b.V = b.V @ R.T + np.asarray(c, float) + off + n * size * 0.22
        out.append(b)
    return out


def root(pts, r0, r1, seed=0, n=6):
    pts = np.asarray(pts, float)
    rng = np.random.default_rng(seed)
    q = pts.copy()
    q[1:-1] += rng.normal(size=q[1:-1].shape) * 0.012
    k = len(q)
    return GK.rtube(q, [r0 + (r1 - r0) * i / (k - 1) for i in range(k)], "BH_Wood", n=n)


def strands(edge_pts, out, seed, lmin=0.12, lmax=0.3):
    """Moss / root-hair strands hanging from a ledge: tapered tubes falling from each edge point."""
    rng = np.random.default_rng(seed)
    o = normalize(np.asarray(out, float))
    res = []
    for i, q in enumerate(np.asarray(edge_pts, float)):
        ln = lmin + (lmax - lmin) * rng.random()
        pts = [q, q + o * 0.03 + (0, 0, -ln * 0.4), q + o * 0.04 + rng.normal(size=3) * 0.01 + (0, 0, -ln)]
        res.append(GK.rtube(pts, [0.022, 0.016, 0.004], "BH_Cloth_Secondary" if i % 3 else "BH_Fur", n=4))
    return res


def leaves(c, seed, cnt=5, size=0.22):
    """A young jungle plant rooted in the moss: broad drooping leaves on short stems."""
    rng = np.random.default_rng(seed)
    out = []
    for k in range(cnt):
        a = 2 * math.pi * k / cnt + rng.random() * 0.5
        d = np.array([math.cos(a), math.sin(a), 0.0])
        base = np.asarray(c, float)
        tip = base + d * size * 0.35 + (0, 0, size * 0.45)
        out.append(GK.rtube([base, tip], [0.008, 0.004], "BH_Wood", n=4))
        for prt in Z.zfeather(tip, d * 1.0 + (0, 0, -0.35), size * (0.8 + 0.4 * rng.random()), size * 0.38,
                              np.cross((0, 0, 1), d), mats=("BH_Fur", None), tip=0, bend=-0.18, quill=False, k=6):
            out.append(prt)
    return out


def crack(pts, nrm, r=0.008):
    return GK.rtube(np.asarray(pts, float) - np.asarray(nrm, float) * 0.004, r, "BH_Shadow", n=4)


# ================================================================================================= build
def build(body: Body):
    add = body.add
    core_w = GK.zspec_w([(zh + 0.05, "hips"), (zs + 0.05, "spine"), (zc - 0.05, "spine"), (zc + 0.1, "chest")])
    V, F = M.tube([(0, 0.0, zh - 0.05), (0, 0.0, zs), (0, 0.0, zc), (0, 0.0, zc + 0.3)],
                  [(0.36, 0.25)] * 4, n=14, up=(0, -1, 0))
    add(P(V, F, "BH_DarkSteel", "core"), weights=core_w)
    # ---- pelvis: block, copper band, loin slabs per leg
    add(block(PELV), "hips")
    add(band(PELV, zh + 0.1, 0.07, 0.012, mat="BH_Gold"), "hips")
    for sx in (1, -1):
        lb = "thigh.L" if sx > 0 else "thigh.R"
        c = np.array([sx * 0.2, -0.3, zh - 0.18])
        add(slab((0.28, 0.08, 0.32), c, R=Rx(8), bev=0.016), weights=lambda V, lb=lb: [{"hips": 0.5, lb: 0.5}] * len(V))
        addp(body, Z.channel([c + (sx * -0.06, -0.045, 0.1), c + (sx * -0.06, -0.05, -0.04), c + (sx * 0.06, -0.05, -0.04),
                              c + (sx * 0.06, -0.05, -0.12)], FRONT, 0.016, broken=(1,)),
             weights=lambda V, lb=lb: [{"hips": 0.5, lb: 0.5}] * len(V))
    # central loin slab with a fret
    c = np.array([0, -0.31, zh - 0.12])
    add(slab((0.2, 0.08, 0.42), c, R=Rx(6), bev=0.015), "hips")
    # ---- belly
    add(block(ABDO), "spine")
    add(band(ABDO, zs + 0.27, 0.06, 0.012, mat="BH_Gold"), "spine")
    addp(body, Z.channel(RG.surf_front(ABDO, [(-0.3, zs + 0.06), (-0.12, zs + 0.06), (-0.12, zs + 0.16), (0.12, zs + 0.16),
                                              (0.12, zs + 0.06), (0.3, zs + 0.06)]), FRONT, 0.018, broken=(2,)), "spine")
    chest(body)
    head(body)
    for s in ("L", "R"):
        arm(body, s)
        leg(body, s)


def chest(body):
    add = body.add
    add(block(CHEST, bev=0.018), "chest")
    add(band(CHEST, zc + 0.02, 0.07, 0.012, mat="BH_Gold"), "chest")
    # pectoral slabs with stepped wire channels (cracked)
    for sx in (1, -1):
        zp = zc + 0.36
        xp = sx * 0.34
        c = np.array([xp, fy(CHEST, xp, zp) + 0.02, zp])
        add(slab((0.4, 0.1, 0.34), c, bev=0.02), "chest")
        f = c[1] - 0.052
        pts = [(xp - sx * 0.14, f, zp + 0.1), (xp - sx * 0.02, f, zp + 0.1), (xp - sx * 0.02, f, zp - 0.02),
               (xp + sx * 0.1, f, zp - 0.02), (xp + sx * 0.1, f, zp - 0.12)]
        addp(body, Z.channel(pts, FRONT, 0.018, broken=(2,) if sx > 0 else (0,)), "chest")
        add(crack([(xp + sx * 0.05, f + 0.002, zp + 0.17), (xp + sx * 0.02, f + 0.002, zp + 0.08),
                   (xp + sx * 0.07, f + 0.002, zp + 0.0)], FRONT), "chest")
    # carved sun-disc on the sternum, its ring broken
    zd = zc + 0.14
    yd = fy(CHEST, 0, zd)
    ring = [(0.12 * math.cos(a), yd - 0.004, zd + 0.12 * math.sin(a)) for a in np.linspace(0.3, 2 * math.pi + 0.3, 17)]
    addp(body, Z.channel(ring, FRONT, 0.016, broken=(4, 11)), "chest")
    add(GK.blob((0, yd - 0.01, zd), 0.06, "BH_Emissive", scale=(1, 0.3, 1), n=10, rings=5), "chest")
    add(GK.blob((0, yd + 0.01, zd), 0.085, "BH_Shadow", scale=(1, 0.3, 1), n=10, rings=5), "chest")
    # back: moss mat, roots climbing over the shoulders, a cracked spine channel
    addp(body, Z.channel(RG.surf_back(CHEST, [(0, zc + 0.0), (0, zc + 0.25), (0.0, zc + 0.5)]), BACK, 0.018,
                         broken=(1,)), "chest")
    for k, (x, z, sz) in enumerate(((0.0, zc + 0.45, 0.26), (-0.3, zc + 0.32, 0.22), (0.32, zc + 0.18, 0.2),
                                    (0.1, zc + 0.08, 0.16), (-0.2, zc + 0.02, 0.14))):
        addp(body, moss((x, by(CHEST, x, z), z), (x * 0.6, 1, 0.5), sz, 40 + k, cnt=6), "chest")
    for k, sx in enumerate((1, -1)):
        pts = [(sx * 0.15, by(CHEST, sx * 0.15, zc + 0.55) + 0.02, zc + 0.56), (sx * 0.4, 0.15, zn + 0.05),
               (sx * 0.52, -0.05, zn + 0.08), (sx * 0.6, -0.22, zn - 0.02), (sx * 0.62, -0.3, zn - 0.2)]
        add(root(pts, 0.035, 0.012, seed=5 + k), "chest")
        pts = [(sx * 0.2, by(CHEST, sx * 0.2, zc + 0.5) + 0.02, zc + 0.5), (sx * 0.25, 0.48, zc + 0.2),
               (sx * 0.22, 0.42, zc - 0.1), (sx * 0.26, 0.4, zs)]
        add(root(pts, 0.03, 0.008, seed=9 + k), weights=GK.zspec_w([(zs, "spine"), (zc + 0.2, "chest")]))
    # collar stones round the sunken head
    for sx in (1, -1):
        add(slab((0.22, 0.5, 0.18), (sx * 0.38, 0.03, zn + 0.04), R=Ry(sx * 16), bev=0.016), "chest")


def head(body):
    add = body.add
    H = hrows()
    z0 = L["head"]
    add(block(H, bev=0.02), "head")
    # heavy brow + eye slots
    zb = z0 + 0.3
    yb = fy(H, 0, zb)
    add(slab((0.64, 0.16, 0.1), (0, yb - 0.04, zb + 0.02), R=Rx(-6), bev=0.016), "head")
    for sx in (1, -1):
        ze = z0 + 0.22
        ye = fy(H, 0.14, ze)
        add(slab((0.2, 0.05, 0.085), (sx * 0.14, ye + 0.012, ze), mat="BH_Shadow", bev=0.008), "head")
        add(slab((0.15, 0.02, 0.032), (sx * 0.14, ye - 0.004, ze), mat="BH_Emissive", bev=0.006), "head")
        # jade ear spools
        V, F = M.lathe([(0.0, -0.03), (0.08, -0.03), (0.09, 0.0), (0.08, 0.03), (0.0, 0.03)], 14)
        add(P(V, F, "BH_Horn", "spool").rot(Ry(90 * sx)).move((sx * 0.35, -0.12, z0 + 0.16)), "head")
        add(GK.blob((sx * 0.385, -0.12, z0 + 0.16), 0.035, "BH_Shadow", scale=(0.5, 1, 1)), "head")
        # cheek frets
        pts = [(sx * (0.12 + 0.12 * u), fy(H, sx * (0.12 + 0.12 * u), z0 + 0.06) - 0.006, z0 + 0.04 + 0.07 * v)
               for u, v in Z.fret_wave(1, steps=2)]
        add(GK.rtube(pts, 0.009, "BH_Shadow", n=4), "head")
    # stepped nose
    yn = fy(H, 0, z0 + 0.14)
    add(slab((0.12, 0.08, 0.16), (0, yn - 0.03, z0 + 0.17), bev=0.012), "head")
    add(slab((0.18, 0.06, 0.06), (0, yn - 0.04, z0 + 0.1), bev=0.012), "head")
    # fret-mouth: a wide dark recess, a glow behind, stone teeth in a stepped pattern
    zm = z0 + 0.0
    ym = fy(H, 0, zm)
    add(slab((0.42, 0.06, 0.14), (0, ym + 0.02, zm), mat="BH_Shadow", bev=0.008), "head")
    add(slab((0.36, 0.02, 0.05), (0, ym + 0.0, zm), mat="BH_Emissive", bev=0.005), "head")
    for k in range(7):
        x = -0.18 + 0.06 * k
        up = (k % 2 == 0)
        h = 0.07 if up else 0.05
        zt = zm + (0.07 - h / 2) if up else zm - (0.07 - h / 2)
        add(slab((0.045, 0.06, h), (x, ym - 0.012, zt), bev=0.008), "head")
    # stepped crown with a fret front (its channel cracked), moss on top, roots down the sides
    zt = L["head"] + 0.46
    add(slab((0.62, 0.58, 0.09), (0, -0.12, zt + 0.04), bev=0.02), "head")
    add(slab((0.48, 0.44, 0.09), (0, -0.12, zt + 0.12), bev=0.02), "head")
    add(slab((0.5, 0.06, 0.14), (0, -0.41, zt + 0.05), R=Rx(-4), bev=0.014), "head")
    pts = [(-0.21 + 0.42 * u, -0.447, zt + 0.0 + 0.1 * v) for u, v in Z.fret_wave(3, steps=2)]
    addp(body, Z.channel(pts, FRONT, 0.009, broken=(9, 22)), "head")
    addp(body, moss((0.05, -0.12, zt + 0.17), (0, 0, 1), 0.24, 7, cnt=6), "head")
    addp(body, leaves((0.08, -0.1, zt + 0.2), 3, cnt=5, size=0.24), "head")
    addp(body, strands([(x, -0.42, zt - 0.0) for x in (-0.25, 0.27)] + [(0.31, y, zt - 0.0) for y in (-0.25, 0.0)],
                       (0, -1, 0), 12, 0.08, 0.2), "head")
    addp(body, moss((-0.24, 0.0, zt + 0.1), (-0.5, 0.2, 1), 0.1, 8, cnt=3), "head")
    for k, sx in enumerate((1, -1)):
        pts = [(sx * 0.1, 0.02, zt + 0.17), (sx * 0.3, -0.05, zt + 0.08), (sx * 0.34, -0.2, z0 + 0.3),
               (sx * 0.36, -0.3, z0 + 0.05), (sx * 0.33, -0.36, z0 - 0.12)]
        add(root(pts, 0.03, 0.008, seed=21 + k), "head")
    # carved channel on the forehead between the brows (cracked)
    addp(body, Z.channel([(0, yb - 0.115, zb + 0.07), (0, yb - 0.11, zb + 0.13)], FRONT, 0.012), "head")


def arm(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    sh_b, ua, fa, ha = "shoulder." + s, "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
    add(GK.blob(sh, 0.21, "BH_DarkSteel", n=14, rings=8), ua)
    add(stone_limb(body, ua, [(0.12, 0.17, 0.18), (0.5, 0.185, 0.19), (0.9, 0.165, 0.17)]), ua)
    add(RG.joint_ring(sh + (el - sh) * 0.6, el - sh, 0.215, w=0.07, mat="BH_Gold"), ua)
    A = body.axes(ua)
    ul = body.p["upper_len"]
    addp(body, Z.channel(body.lpt(ua, [(0.0, u * ul, 0.19) for u in (0.18, 0.32, 0.46)]), A[:, 2], 0.016,
                         broken=(0,)), ua)
    # slab pauldron (on the clavicle bone) with moss on top
    c = sh + np.array([sx * 0.03, 0.0, 0.17])
    R = Ry(-sx * 12)
    add(slab((0.5, 0.56, 0.26), c, R=R, bev=0.03), sh_b)
    add(slab((0.4, 0.46, 0.1), c + R @ np.array([sx * 0.03, 0, 0.16]), R=R, bev=0.02), sh_b)
    add(slab((0.52, 0.06, 0.26), c + R @ np.array([0, -0.26, -0.02]), R=R, mat="BH_Gold", bev=0.01), sh_b)
    top = c + R @ np.array([sx * 0.03, 0, 0.215])
    addp(body, moss(top + (0, 0.04, 0), (sx * 0.1, 0, 1), 0.22, 30 + (sx > 0), cnt=6), sh_b)
    edge = [c + R @ np.array([sx * (0.25 - 0.03 * k), 0.26 - 0.12 * k, 0.1]) for k in range(5)]
    addp(body, strands(edge, (sx, 0.3, 0), 33 + (sx > 0)), sh_b)
    front = c + R @ np.array([0, -0.287, 0.02])
    addp(body, Z.channel([front + (-0.15, 0, 0.06), front + (-0.05, 0, 0.06), front + (-0.05, 0, -0.06),
                          front + (0.05, 0, -0.06), front + (0.05, 0, 0.06), front + (0.15, 0, 0.06)], FRONT, 0.014,
                         broken=(3,)), sh_b)
    # elbow + forearm + fist
    add(GK.blob(el, 0.18, "BH_DarkSteel", n=14, rings=8), fa)
    add(stone_limb(body, fa, [(0.05, 0.19, 0.19), (0.45, 0.24, 0.24), (0.8, 0.25, 0.25), (0.97, 0.22, 0.22)], p=3.8),
        fa)
    fl = body.p["fore_len"]
    add(RG.joint_ring(el + (wr - el) * 0.88, wr - el, 0.27, w=0.08, mat="BH_Gold"), fa)
    A = body.axes(fa)
    addp(body, Z.channel(body.lpt(fa, [(-0.07, 0.3 * fl, 0.245), (-0.07, 0.55 * fl, 0.255), (0.07, 0.55 * fl, 0.255),
                                       (0.07, 0.78 * fl, 0.25)]), A[:, 2], 0.017, broken=(1,)), fa)
    add(crack(body.lpt(fa, [(0.19, 0.4 * fl, -0.14), (0.21, 0.55 * fl, -0.1), (0.18, 0.7 * fl, -0.15)]), -A[:, 2]), fa)
    # a root wound round the forearm
    pts = [body.lpt(fa, [(0.25 * math.cos(a), (0.15 + 0.6 * a / (2 * math.pi * 1.3)) * fl, 0.25 * math.sin(a))])[0]
           for a in np.linspace(0, 2 * math.pi * 1.3, 12)]
    add(root(pts, 0.022, 0.012, seed=60 + (sx > 0)), fa)
    RG.fist(body, s)


def leg(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    th, sh, ft, toe = "thigh." + s, "shin." + s, "foot." + s, "toe." + s
    hip, k, a = body.head(th), body.head(sh), body.tail(sh)
    add(GK.blob(hip, 0.21, "BH_DarkSteel", n=14, rings=8), th)
    add(stone_limb(body, th, [(0.05, 0.23, 0.24), (0.5, 0.25, 0.25), (0.92, 0.22, 0.23)]), th)
    add(GK.blob(k + (0, -0.02, 0), 0.2, "BH_DarkSteel", n=14, rings=8), sh)
    add(stone_limb(body, sh, [(0.08, 0.23, 0.23), (0.4, 0.25, 0.26), (0.85, 0.26, 0.27), (1.0, 0.24, 0.25)]), sh)
    add(RG.joint_ring(k + (a - k) * 0.72, a - k, 0.29, w=0.08, mat="BH_Gold"), sh)
    add(slab((0.3, 0.1, 0.22), k + (0, -0.2, 0.0), R=Rx(-8), bev=0.02), sh)
    addp(body, Z.channel([k + (-0.06, -0.255, 0.05), k + (0.0, -0.26, -0.04), k + (0.06, -0.255, 0.05)], FRONT, 0.016),
         sh)
    addp(body, Z.channel([hip + (sx * 0.25, 0, -0.1), k + (sx * 0.25, 0, 0.12)], np.array([sx, 0, 0.0]), 0.016), th)
    addp(body, moss(hip + (sx * 0.12, 0.18, -0.1), (sx * 0.3, 1, 0.2), 0.11, 50 + (sx > 0), cnt=3), th)
    hx = body.p["hip_x"] * sx
    add(slab((0.42, 0.46, 0.16), (hx, -0.02, 0.08), bev=0.03), ft)
    add(slab((0.38, 0.08, 0.1), (hx, -0.21, 0.18), R=Rx(-30), mat="BH_Gold", bev=0.01), ft)
    add(slab((0.4, 0.16, 0.12), (hx, -0.31, 0.06), bev=0.025), toe)
    addp(body, moss((hx + sx * 0.12, 0.1, 0.17), (sx * 0.3, 0.3, 1), 0.08, 70 + (sx > 0), cnt=3), ft)
