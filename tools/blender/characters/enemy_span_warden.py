"""Span Warden (bh-029, Builder M3, Zarael / the Bridge of Death shield construct): a ~2.3 m Wirewright keeper of the
bridge, a frame of cast bronze dressed in pale carved glyph stone. A broad stone cuirass with a stepped-fret band and
a glyph eye on the breast, stepped two-tier stone pauldrons, bronze limbs with stone bracers and greaves, slab feet.
The head is a small stepped capital (like the tops of the bridge's own pylons) over a flat glyph face with a T-shaped
slit of white light. Every carved channel holds the old current, white; the Blackwire shows only as the damage it has
done: cracked stone, broken channels, a snapped Kharvenn rune-chain wound round the left forearm.

Left hand (weapon.L, face -Y): a tall tower shield carved like a bridge pylon (a tapering stone slab in stacked
courses on a plinth, a stepped capital, bronze edges, a white channel running up the face into a glyph eye).
Right hand (weapon.R): a short heavy bronze sword with a glyph-stone guard and a white channel in the fuller.

Built at true size on the shared skeleton (proportions x1.25, broad shoulders). Clips: shield_bash sword_1
sword_heavy (+ sword_2, the enemy base set).

Also holds the small "bridge construct" kit M3's other Wirewright models share (deathspan_colossus, ward_eye):
`glow`/palette constants, `chan` (carved white channel), `crack`, `fret_pts`, `coil_stud`, `stepped_capital`."""
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
import enemy_bandit_cutthroat as KB  # noqa: E402
import enemy_glyphbound_warrior as Z  # noqa: E402
import kit_a_common as A  # noqa: E402

S = 1.25
PROPS = proportions(S, shoulder_x=0.27, hip_x=0.13, upper_len=0.33, fore_len=0.32, hand_len=0.12, grip_x=0.09,
                    clav_x0=0.05, clav_drop=0.06)
L = GK.levels(PROPS)
PREVIEW_HEIGHT = 2.7

# the Zarael glow rule: every glow pure white, moderate energy
WHITE_GLOW = ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0)
PALETTE = "span_warden"
PALETTE_COLORS = {
    "BH_Stone": ((0.5, 0.465, 0.39), 0.0, 0.9, None, 0.0, 1.0),            # pale weathered glyph limestone
    "BH_Bronze": ((0.44, 0.28, 0.12), 1.0, 0.45, None, 0.0, 1.0),          # cast bronze frame
    "BH_Gold": ((0.62, 0.42, 0.17), 1.0, 0.35, None, 0.0, 1.0),            # brighter bronze trim / rims
    "BH_DarkSteel": ((0.075, 0.07, 0.065), 0.3, 0.8, None, 0.0, 1.0),      # dark joint stones / core column
    "BH_Horn": ((0.1, 0.38, 0.37), 0.0, 0.35, None, 0.0, 1.0),             # turquoise mosaic inlays
    "BH_Steel": ((0.24, 0.24, 0.26), 0.9, 0.5, None, 0.0, 1.0),            # the Kharvenn chain (grey iron)
    "BH_Shadow": ((0.018, 0.016, 0.015), 0.0, 0.85, None, 0.0, 1.0),       # carved grooves / cracks
    "BH_Emissive": WHITE_GLOW,                                              # the old current, white
}
CLIPS = ["shield_bash", "sword_1", "sword_heavy", "sword_2"]

P = Z.P
FRONT, BACK = np.array([0, -1.0, 0]), np.array([0, 1.0, 0])
block, slab, band, stone_limb, joint_ring, local_box = RG.block, RG.slab, RG.band, RG.stone_limb, RG.joint_ring, \
    RG.local_box
fy, by = RG.fy, RG.by


def finish_mesh(mesh_ob):
    KB.enable_weapon_deform(mesh_ob)


# ================================================================================================= bridge kit
def chan(pts, nrm, r=0.012, broken=()):
    """Carved channel with the white current in it (dark groove + glowing wire just proud of it)."""
    return Z.channel(pts, nrm, r=r, broken=broken)


def crack(pts, nrm, r=0.006):
    """A corruption crack: a dark jagged groove."""
    return GK.rtube(np.asarray(pts, float) - np.asarray(nrm, float) * 0.003, r, "BH_Shadow", n=4)


def jag(a, b, n, amp, nrm, seed):
    """Jagged polyline from a to b, offsets across the line in the surface plane (nrm = surface normal)."""
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = normalize(b - a)
    side = normalize(np.cross(np.asarray(nrm, float), d))
    pts = []
    for i in range(n):
        t = i / (n - 1)
        off = 0.0 if i in (0, n - 1) else (rng.random() - 0.5) * 2 * amp
        pts.append(a + (b - a) * t + side * off)
    return pts


def fret_pts(origin, u_axis, v_axis, length, height, periods, steps=2):
    """A stepped-fret band laid on a plane: origin = band start, u along, v across."""
    o, u, v = np.asarray(origin, float), np.asarray(u_axis, float), np.asarray(v_axis, float)
    return [o + u * (length * a) + v * (height * b) for a, b in Z.fret_wave(periods, steps=steps)]


def coil_stud(a, b, r, wire, turns=4, mat="BH_Gold", core=True):
    """An arc coil: a bronze helix round a white glowing core rod, capped with bronze collars."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = normalize(b - a)
    out = [Z.coil(a, b, r, turns, wire, mat, n=4, pts_per_turn=8)]
    if core:
        V, F = M.tube([a, b], [(r * 0.62, r * 0.62)] * 2, n=8, up=(0, 0, 1) if abs(d[2]) < 0.9 else (0, -1, 0))
        out.append(P(V, F, "BH_Emissive", "coilcore"))
    for c in (a, b):
        V, F = M.tube([c - d * r * 0.25, c + d * r * 0.25], [(r * 1.25, r * 1.25)] * 2, n=10,
                      up=(0, 0, 1) if abs(d[2]) < 0.9 else (0, -1, 0))
        out.append(P(V, F, "BH_Bronze", "collar"))
    return out


def stepped_capital(c, w, d, h, steps=3, mat="BH_Stone", grow=0.05, bev=0.008):
    """An inverted stepped capital (each course wider than the one below), centred at c (bottom centre)."""
    out = []
    z = c[2]
    for i in range(steps):
        sw, sd = w + grow * i, d + grow * i
        out.append(slab((sw, sd, h), (c[0], c[1], z + h / 2), mat=mat, bev=bev))
        z += h
    return out


def addp(body, parts, bone=None, weights=None):
    for p in parts:
        body.add(p, bone, weights)


# ================================================================================================= body
zh, zs, zc, zn, zhd = L["hips"], L["spine"], L["chest"], L["neck"], L["head"]
PELV = [(zh - 0.13, 0.17, 0.12, 0.13, 0.0), (zh - 0.04, 0.2, 0.14, 0.15, 0.0), (zh + 0.08, 0.205, 0.145, 0.15, 0.0),
        (zh + 0.14, 0.19, 0.135, 0.14, 0.0)]
ABDO = [(zs - 0.03, 0.17, 0.12, 0.12, 0.0), (zs + 0.1, 0.18, 0.125, 0.125, 0.0), (zs + 0.2, 0.2, 0.13, 0.13, 0.0)]
CHEST = [(zc - 0.06, 0.21, 0.14, 0.14, 0.0, 0.0), (zc + 0.06, 0.26, 0.17, 0.16, 0.0, -0.005),
         (zc + 0.18, 0.3, 0.19, 0.18, 0.0, -0.01), (zn - 0.05, 0.31, 0.185, 0.19, 0.0, 0.0),
         (zn + 0.02, 0.25, 0.15, 0.17, 0.0, 0.01), (zn + 0.07, 0.14, 0.1, 0.11, 0.0, 0.01)]
HEADB = [(-0.07, 0.085, 0.09, 0.085, 0.0, -0.015), (0.0, 0.1, 0.11, 0.1, 0.0, -0.02), (0.12, 0.105, 0.115, 0.1, 0.0, -0.02),
         (0.19, 0.095, 0.105, 0.095, 0.0, -0.02)]


def build(body: Body):
    add = body.add
    core_w = GK.zspec_w([(zh + 0.04, "hips"), (zs + 0.04, "spine"), (zc - 0.04, "spine"), (zc + 0.08, "chest")])
    V, F = M.tube([(0, 0.0, zh - 0.05), (0, 0.0, zs), (0, 0.0, zc), (0, 0.0, zc + 0.15)], [(0.15, 0.1)] * 4, n=14,
                  up=(0, -1, 0))
    add(P(V, F, "BH_DarkSteel", "core"), weights=core_w)
    pelvis(body)
    abdomen(body)
    chest(body)
    head(body)
    for s in ("L", "R"):
        arm(body, s)
        leg(body, s)
    chain_wrap(body)
    for p in tower_shield():
        add(KB.to_socket(body, "L", p), "weapon.L")
    for p in heavy_sword():
        add(KB.to_socket(body, "R", p), "weapon.R")


def pelvis(body):
    add = body.add
    add(block(PELV, mat="BH_Bronze", bev=0.01), "hips")
    add(band(PELV, zh + 0.1, 0.05, 0.01, mat="BH_Gold"), "hips")
    # stone loin slabs front and back, side tassets per thigh
    for front in (True, False):
        y = -0.165 if front else 0.17
        c = np.array([0, y, zh - 0.14])
        add(slab((0.2, 0.05, 0.3), c, R=Rx(7 if front else -7), bev=0.012), weights=Z.centre_w(zh, zh - 0.3, 0.45))
        if front:
            addp(body, chan([c + (-0.05, -0.028, 0.1), c + (0, -0.03, 0.02), c + (0.05, -0.028, 0.1)], FRONT, 0.009),
                 weights=Z.centre_w(zh, zh - 0.3, 0.45))
            addp(body, chan([c + (0, -0.03, 0.02), c + (0, -0.032, -0.1)], FRONT, 0.009),
                 weights=Z.centre_w(zh, zh - 0.3, 0.45))
    for sx in (1, -1):
        lb = "thigh.L" if sx > 0 else "thigh.R"
        c = np.array([sx * 0.215, -0.04, zh - 0.12])
        R = Rz(sx * 70) @ Rx(6)
        add(slab((0.2, 0.045, 0.24), c, R=R, bev=0.012), weights=lambda V, lb=lb: [{"hips": 0.6, lb: 0.4}] * len(V))
        add(slab((0.21, 0.05, 0.03), c + (0, 0, 0.12), R=R, mat="BH_Gold", bev=0.006),
            weights=lambda V, lb=lb: [{"hips": 0.6, lb: 0.4}] * len(V))


def abdomen(body):
    add = body.add
    # three bronze ring segments over the core column (they part when the torso bends)
    for k, z in enumerate((zs + 0.0, zs + 0.09, zs + 0.18)):
        rows = [(z - 0.04, 0.165 + 0.012 * k, 0.115 + 0.006 * k, 0.12 + 0.006 * k, 0.0),
                (z + 0.04, 0.17 + 0.012 * k, 0.12 + 0.006 * k, 0.122 + 0.006 * k, 0.0)]
        add(block(rows, mat="BH_Bronze", bev=0.008), "spine")


def chest(body):
    add = body.add
    add(block(CHEST, bev=0.012), "chest")
    add(band(CHEST, zc - 0.03, 0.05, 0.01, mat="BH_Gold"), "chest")
    add(band(CHEST, zn + 0.035, 0.04, 0.01, mat="BH_Gold"), "chest")
    # stepped-fret band across the breast (turquoise mosaic under a carved fret) + the glyph eye
    zb = zc + 0.2
    for x0, x1 in ((-0.26, -0.09), (0.09, 0.26)):
        pts = [(x0 + (x1 - x0) * a, fy(CHEST, x0 + (x1 - x0) * a, zb + 0.06 * b) - 0.004, zb + 0.06 * b)
               for a, b in Z.fret_wave(2, steps=2)]
        add(GK.rtube(pts, 0.008, "BH_Shadow", n=4), "chest")
        q = [(x, fy(CHEST, x, zb - 0.018) - 0.002, zb - 0.018) for x in np.linspace(x0, x1, 6)]
        add(GK.rtube(q, (0.006, 0.006), "BH_Horn", n=4), "chest")
        q = [(x, fy(CHEST, x, zb + 0.078) - 0.002, zb + 0.078) for x in np.linspace(x0, x1, 6)]
        add(GK.rtube(q, (0.006, 0.006), "BH_Horn", n=4), "chest")
    ye = fy(CHEST, 0, zb + 0.03)
    eye = [(0.075 * math.cos(a), ye - 0.006, zb + 0.03 + 0.042 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 17)]
    addp(body, chan(eye, FRONT, 0.008), "chest")
    add(GK.blob((0, ye - 0.006, zb + 0.03), 0.026, "BH_Emissive", scale=(1, 0.45, 1), n=10, rings=5), "chest")
    add(GK.blob((0, ye + 0.004, zb + 0.03), 0.06, "BH_Shadow", scale=(1.3, 0.3, 0.75), n=10, rings=5), "chest")
    # channels down from the eye to the belt, branching (one broken by a crack)
    addp(body, chan([(0, ye - 0.004, zb - 0.02), (0, fy(CHEST, 0, zc + 0.04) - 0.004, zc + 0.04)], FRONT, 0.008),
         "chest")
    for sx in (1, -1):
        pts = [(sx * 0.0, fy(CHEST, 0, zc + 0.1) - 0.004, zc + 0.1), (sx * 0.1, fy(CHEST, sx * 0.1, zc + 0.1) - 0.004,
                                                                        zc + 0.1),
               (sx * 0.1, fy(CHEST, sx * 0.1, zc + 0.0) - 0.004, zc + 0.0)]
        addp(body, chan(pts, FRONT, 0.008, broken=(1,) if sx > 0 else ()), "chest")
    # corruption cracks across the right breast and the left flank
    add(crack(RG.surf_front(CHEST, [(-0.12, zn - 0.03), (-0.16, zc + 0.26), (-0.13, zc + 0.2), (-0.2, zc + 0.12),
                                    (-0.18, zc + 0.05)]), FRONT, 0.007), "chest")
    add(crack(RG.surf_front(CHEST, [(0.22, zc + 0.24), (0.25, zc + 0.15), (0.22, zc + 0.08)]), FRONT, 0.006), "chest")
    # back: spine channel, two stone back slabs, and a carved ring
    addp(body, chan(RG.surf_back(CHEST, [(0, zc - 0.03), (0, zn - 0.02)]), BACK, 0.009, broken=(0,)), "chest")
    for sx in (1, -1):
        c = np.array([sx * 0.15, by(CHEST, sx * 0.15, zc + 0.17) - 0.01, zc + 0.17])
        add(slab((0.17, 0.05, 0.28), c, R=Rz(sx * 6), bev=0.012), "chest")
        addp(body, chan([c + (sx * -0.04, 0.026, 0.1), c + (sx * 0.04, 0.026, 0.1), c + (sx * 0.04, 0.026, -0.08)],
                        BACK, 0.008), "chest")
    # collar stones
    for sx in (1, -1):
        add(slab((0.12, 0.22, 0.08), (sx * 0.17, 0.0, zn + 0.03), R=Ry(sx * 16), bev=0.01), "chest")


def head(body):
    add = body.add
    z0 = zhd
    H = [(z0 + r[0], r[1], r[2], r[3], r[4], r[5]) for r in HEADB]
    add(block(H, mat="BH_Bronze", bev=0.01), "head")
    # flat glyph face plate with a T-slit of white light
    yf = fy(H, 0, z0 + 0.08)
    add(slab((0.19, 0.03, 0.2), (0, yf - 0.006, z0 + 0.08), bev=0.008), "head")
    add(slab((0.15, 0.012, 0.03), (0, yf - 0.022, z0 + 0.12), mat="BH_Shadow", bev=0.003), "head")
    add(slab((0.13, 0.012, 0.016), (0, yf - 0.027, z0 + 0.12), mat="BH_Emissive", bev=0.003), "head")
    add(slab((0.026, 0.012, 0.09), (0, yf - 0.022, z0 + 0.06), mat="BH_Shadow", bev=0.003), "head")
    add(slab((0.012, 0.012, 0.08), (0, yf - 0.027, z0 + 0.06), mat="BH_Emissive", bev=0.002), "head")
    for sx in (1, -1):         # cheek frets
        pts = fret_pts((sx * 0.04, yf - 0.022, z0 + 0.0), (sx * 1.0, 0, 0), (0, 0, 1), 0.05, 0.04, 1, steps=2)
        add(GK.rtube(pts, 0.004, "BH_Shadow", n=4), "head")
        # bronze ear discs with a turquoise centre
        V, F = M.lathe([(0.0, -0.012), (0.045, -0.012), (0.05, 0.0), (0.045, 0.014), (0.0, 0.014)], 12)
        add(P(V, F, "BH_Gold", "earplate").rot(Ry(90 * sx)).move((sx * 0.105, -0.01, z0 + 0.09)), "head")
        add(A.ball((sx * 0.12, -0.01, z0 + 0.09), 0.022, "BH_Horn", n=8, rings=4, scale=(0.4, 1, 1)), "head")
    # the capital: stepped stone courses widening upward, a fret front and a white seam
    top = z0 + 0.19
    for p in stepped_capital((0, -0.02, top), 0.2, 0.2, 0.035, steps=3, grow=0.045):
        add(p, "head")
    add(slab((0.32, 0.3, 0.025), (0, -0.02, top + 0.105 + 0.012), mat="BH_Gold", bev=0.005), "head")
    add(slab((0.24, 0.22, 0.04), (0, -0.02, top + 0.15), bev=0.008), "head")
    pts = fret_pts((-0.13, -0.02 - 0.152, top + 0.05), (1, 0, 0), (0, 0, 1), 0.26, 0.045, 3, steps=2)
    add(GK.rtube(pts, 0.005, "BH_Shadow", n=4), "head")
    add(GK.rtube([(-0.16, -0.02 - 0.142, top + 0.117), (0.16, -0.02 - 0.142, top + 0.117)], 0.006, "BH_Emissive", n=5),
        "head")


def arm(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    sh_b, ua, fa, ha = "shoulder." + s, "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = body.head(ua), body.head(fa), body.head(ha)
    add(GK.blob(sh, 0.105, "BH_DarkSteel", n=12, rings=7), ua)
    add(stone_limb(body, ua, [(0.08, 0.075, 0.08), (0.5, 0.082, 0.085), (0.92, 0.07, 0.072)], mat="BH_Bronze"), ua)
    add(joint_ring(sh + (el - sh) * 0.62, el - sh, 0.09, w=0.03, mat="BH_Gold"), ua)
    # stepped two-tier pauldron on the clavicle
    c = sh + np.array([sx * 0.02, 0.0, 0.08])
    R = Ry(-sx * 14)
    add(slab((0.24, 0.27, 0.11), c, R=R, bev=0.014), sh_b)
    add(slab((0.2, 0.23, 0.06), c + R @ np.array([sx * 0.0, 0, 0.08]), R=R, bev=0.01), sh_b)
    add(slab((0.25, 0.28, 0.022), c + R @ np.array([0, 0, -0.058]), R=R, mat="BH_Gold", bev=0.005), sh_b)
    top = c + R @ np.array([0, 0, 0.112])
    nz = R @ np.array([0, 0, 1.0])
    addp(body, chan([top + R @ np.array([-0.07, -0.08, 0]), top + R @ np.array([0, 0.0, 0]),
                     top + R @ np.array([0.07, -0.08, 0])], nz, 0.008), sh_b)
    fr = c + R @ np.array([0, -0.137, -0.005])
    pts = fret_pts(fr + R @ np.array([-0.1, 0, -0.035]), R @ np.array([1.0, 0, 0]), R @ np.array([0, 0, 1.0]), 0.2,
                   0.045, 2, steps=2)
    add(GK.rtube(pts, 0.0045, "BH_Shadow", n=4), sh_b)
    # elbow + forearm with a stone bracer
    add(GK.blob(el, 0.085, "BH_DarkSteel", n=12, rings=7), fa)
    add(stone_limb(body, fa, [(0.05, 0.072, 0.074), (0.5, 0.075, 0.078), (0.95, 0.06, 0.062)], mat="BH_Bronze"), fa)
    add(stone_limb(body, fa, [(0.28, 0.092, 0.095), (0.5, 0.1, 0.104), (0.86, 0.088, 0.09)], p=3.6), fa)
    add(joint_ring(el + (wr - el) * 0.9, wr - el, 0.093, w=0.028, mat="BH_Gold"), fa)
    Ax = body.axes(fa)
    fl = body.p["fore_len"]
    addp(body, chan(body.lpt(fa, [(0.0, 0.32 * fl, 0.104), (0.0, 0.5 * fl, 0.11), (0.03, 0.62 * fl, 0.106),
                                  (0.03, 0.8 * fl, 0.094)]), Ax[:, 2], 0.008), fa)
    # armoured fist round the grip
    from bh_body import fist
    for prt in fist(body, s, "BH_Bronze", "BH_DarkSteel", gauntlet=True, scale=1.55):
        add(prt, ha)


def leg(body, s):
    add = body.add
    sx = 1 if s == "L" else -1
    th, sh, ft, toe = "thigh." + s, "shin." + s, "foot." + s, "toe." + s
    hip, k, a = body.head(th), body.head(sh), body.tail(sh)
    add(GK.blob(hip, 0.11, "BH_DarkSteel", n=12, rings=7), th)
    add(stone_limb(body, th, [(0.05, 0.105, 0.11), (0.5, 0.11, 0.115), (0.93, 0.085, 0.09)], mat="BH_Bronze"), th)
    add(joint_ring(hip + (k - hip) * 0.6, k - hip, 0.118, w=0.03, mat="BH_Gold"), th)
    add(GK.blob(k + (0, -0.01, 0), 0.09, "BH_DarkSteel", n=12, rings=7), sh)
    add(stone_limb(body, sh, [(0.06, 0.08, 0.082), (0.5, 0.075, 0.078), (0.95, 0.065, 0.068)], mat="BH_Bronze"), sh)
    # stone greave (front + sides) with a carved channel, knee slab
    add(stone_limb(body, sh, [(0.2, 0.1, 0.105), (0.45, 0.106, 0.112), (0.85, 0.09, 0.094)], p=3.4,
                   ), sh)
    add(slab((0.15, 0.06, 0.13), k + (0, -0.095, 0.0), R=Rx(-8), bev=0.012), sh)
    addp(body, chan([k + (-0.035, -0.128, 0.035), k + (0.0, -0.13, -0.025), k + (0.035, -0.128, 0.035)], FRONT, 0.008),
         sh)
    addp(body, chan([k + (0, -0.112, -0.12), a + (0, -0.104, 0.16)], FRONT, 0.008, broken=(0,) if sx < 0 else ()), sh)
    add(crack([k + (sx * 0.06, -0.095, -0.15), k + (sx * 0.075, -0.09, -0.2), k + (sx * 0.06, -0.093, -0.26)], FRONT,
              0.005), sh)
    # slab foot with a bronze toe cap
    hx = body.p["hip_x"] * sx
    add(slab((0.17, 0.27, 0.1), (hx, -0.045, 0.05), bev=0.016), ft)
    add(slab((0.16, 0.05, 0.06), (hx, -0.15, 0.1), R=Rx(-30), mat="BH_Gold", bev=0.008), ft)
    add(slab((0.16, 0.11, 0.075), (hx, -0.2, 0.038), bev=0.014), toe)


def chain_wrap(body):
    """A snapped Kharvenn rune-chain wound round the left forearm, its broken end hanging."""
    fa = "forearm.L"
    fl = body.p["fore_len"]
    pts = []
    for t in np.linspace(0, 1, 22):
        ang = 2 * math.pi * 2.2 * t
        pts.append(body.lpt(fa, [(0.112 * math.cos(ang), (0.22 + 0.45 * t) * fl, 0.112 * math.sin(ang))])[0])
    for p in chain_links(pts, link=0.05, r=0.0075):
        body.add(p, fa)
    end = pts[-1]
    hang = [end, end + (0.0, -0.02, -0.08), end + (0.01, -0.03, -0.17)]
    for p in chain_links(hang, link=0.05, r=0.0075):
        body.add(p, fa)


def chain_links(pts, link=0.05, r=0.007, mat="BH_Steel", sides=8, n=4):
    """Alternating oval links along a polyline (link = link length, r = wire radius; sides x n faces per link)."""
    pts = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    Lc = np.concatenate([[0], np.cumsum(seg)])
    out = []
    cnt = max(1, int(Lc[-1] / (link * 0.74)))
    for i in range(cnt):
        t = (i + 0.5) * Lc[-1] / cnt
        j = min(int(np.searchsorted(Lc, t, side="right") - 1), len(seg) - 1)
        u = (t - Lc[j]) / max(seg[j], 1e-9)
        c = pts[j] * (1 - u) + pts[j + 1] * u
        d = normalize(pts[j + 1] - pts[j])
        a = normalize(np.cross(d, (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)))
        if i % 2:
            a = normalize(np.cross(d, a))
        b = np.cross(d, a)
        ring = [c + d * (link * 0.5 * math.cos(q)) + b * (link * 0.3 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, sides + 1)]
        V, F = M.tube(ring, [(r, r)] * len(ring), n=n, up=tuple(a), cap0=False, cap1=False)
        out.append(P(V, F, mat, "link"))
    return out


# ================================================================================================= weapons
def tower_shield():
    """Pylon tower shield (weapon space: handle at origin, face -Y, +Z up): ~1.45 m tall. A tapering stone slab in
    stacked courses on a stepped plinth, a stepped capital on top, bronze edge strips, a white channel up the face
    into a glyph eye under the capital, a fret band on the capital, cracks across two courses."""
    parts = []
    z0, z1 = -0.86, 0.46           # body of the slab (plinth below z0, capital above z1)
    yf = -0.1                      # front face plane
    th = 0.07

    def half_w(z):
        t = (z - z0) / (z1 - z0)
        return 0.33 - 0.06 * t

    # main slab (front slightly convex)
    o = [(half_w(z0), z0), (half_w(z1), z1), (-half_w(z1), z1), (-half_w(z0), z0)]
    o = np.array(o)
    if 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1]) < 0:
        o = o[::-1]
    V, F = M.prism(o, th, axis="y", center=yf + th / 2)
    slabp = P(V, F, "BH_Stone", "slab")
    parts.append(M.bevel(slabp, 0.012, 1, angle=35))
    # courses: horizontal grooves on the face, offset vertical joints
    zs = np.linspace(z0 + 0.16, z1 - 0.06, 6)
    for i, z in enumerate(zs):
        w = half_w(z)
        parts.append(A.tube([(-w + 0.02, yf - 0.002, z), (w - 0.02, yf - 0.002, z)], (0.009, 0.004), "BH_Shadow", n=4,
                            up=(0, -1, 0)))
        zl = zs[i - 1] if i > 0 else z0 + 0.02
        for xj in ((-0.14, 0.14) if i % 2 else (0.0,)):
            if abs(xj) < w - 0.05:
                parts.append(A.tube([(xj + 0.0 * i, yf - 0.002, zl + 0.012), (xj, yf - 0.002, z - 0.012)], (0.004, 0.004),
                                    "BH_Shadow", n=4, up=(0, -1, 0)))
    # bronze edge strips down both sides + a bronze band at the plinth
    for sx in (1, -1):
        pts = [(sx * half_w(z0), yf + th / 2, z0), (sx * half_w(z1), yf + th / 2, z1)]
        parts.append(A.tube(pts, (0.022, 0.046), "BH_Bronze", n=6, up=(0, -1, 0), p=4.0))
        for z in np.linspace(z0 + 0.1, z1 - 0.1, 5):
            parts.append(A.ball((sx * (half_w(z) + 0.012), yf - 0.016, z), 0.014, "BH_Gold", n=6, rings=4,
                                scale=(1, 0.6, 1)))
    # plinth: two stepped courses wider than the slab
    for i, (w, h) in enumerate(((0.36, 0.06), (0.4, 0.07))):
        zc = z0 - 0.03 - i * 0.065
        parts.append(slab((2 * w, th + 0.04 + 0.02 * i, h), (0, yf + th / 2, zc), bev=0.01))
    parts.append(slab((0.82, th + 0.09, 0.025), (0, yf + th / 2, z0 - 0.168), mat="BH_Bronze", bev=0.006))
    # capital: stepped courses widening upward + a cap stone, fret band, white seam
    zc = z1
    for i, (w, h) in enumerate(((0.3, 0.05), (0.34, 0.05), (0.38, 0.055))):
        parts.append(slab((2 * w, th + 0.03 + 0.02 * i, h), (0, yf + th / 2, zc + h / 2), bev=0.009))
        zc += h
    parts.append(slab((0.8, th + 0.1, 0.022), (0, yf + th / 2, zc + 0.011), mat="BH_Gold", bev=0.005))
    parts.append(slab((0.5, th + 0.04, 0.06), (0, yf + th / 2, zc + 0.052), bev=0.01))
    parts.append(slab((0.26, th + 0.02, 0.05), (0, yf + th / 2, zc + 0.105), bev=0.01))
    yc = yf - 0.015 - 0.02
    pts = fret_pts((-0.3, yc - 0.012, z1 + 0.105), (1, 0, 0), (0, 0, 1), 0.6, 0.04, 4, steps=2)
    parts.append(A.tube(pts, (0.005, 0.003), "BH_Shadow", n=4, up=(0, -1, 0)))
    parts.append(A.tube([(-0.34, yc - 0.024, z1 + 0.042), (0.34, yc - 0.024, z1 + 0.042)], 0.007, "BH_Emissive", n=5))
    # the current: a channel up the centre into a glyph eye under the capital, two side branches
    nrm = np.array([0, -1.0, 0])
    yy = yf - 0.006
    parts += chan([(0, yy, z0 + 0.02), (0, yy, z1 - 0.2)], nrm, 0.011)
    for sx in (1, -1):
        parts += chan([(0, yy, z0 + 0.3), (sx * 0.12, yy, z0 + 0.3), (sx * 0.12, yy, z0 + 0.5),
                       (sx * 0.2, yy, z0 + 0.5), (sx * 0.2, yy, z0 + 0.72)], nrm, 0.009, broken=(3,) if sx > 0 else ())
    ze = z1 - 0.1
    eye = [(0.11 * math.cos(a), yy, ze + 0.06 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 21)]
    parts += chan(eye, nrm, 0.01)
    parts.append(A.ball((0, yy - 0.004, ze), 0.034, "BH_Emissive", n=10, rings=5, scale=(1, 0.4, 1)))
    parts.append(A.ball((0, yy + 0.004, ze), 0.07, "BH_Shadow", n=10, rings=5, scale=(1.35, 0.25, 0.8)))
    # cracks (the Blackwire's damage) across the lower courses
    parts.append(crack(jag((-0.28, yf - 0.001, z0 + 0.42), (-0.05, yf - 0.001, z0 + 0.22), 6, 0.025, nrm, 3), nrm, 0.006))
    parts.append(crack(jag((0.3, yf - 0.001, z0 + 0.9), (0.12, yf - 0.001, z0 + 1.08), 5, 0.02, nrm, 7), nrm, 0.005))
    # a chipped corner: a dark recess at the lower right
    parts.append(slab((0.08, 0.02, 0.07), (0.27, yf - 0.002, z0 + 0.06), R=Ry(25), mat="BH_Shadow", bev=0.004))
    # back: bronze frame bars + grip + arm strap
    for x in (-0.18, 0.18):
        parts.append(slab((0.045, 0.03, z1 - z0 - 0.1), (x, yf + th + 0.012, (z0 + z1) / 2), mat="BH_Bronze", bev=0.005))
    for z in (-0.5, 0.2):
        parts.append(slab((0.42, 0.03, 0.045), (0, yf + th + 0.012, z), mat="BH_Bronze", bev=0.005))
    V, F = M.tube([(-0.08, -0.03, 0.0), (-0.05, 0.02, 0.0), (0.05, 0.02, 0.0), (0.08, -0.03, 0.0)],
                  [(0.018, 0.04)] * 4, n=6, up=(0, 0, 1))
    parts.append(P(V, F, "BH_Bronze", "handle"))
    return parts


def heavy_sword():
    """Short heavy sword (weapon space: grip at origin, +Z blade, flats +-Y): a broad leaf-shaped bronze blade
    (~0.72 m) with a white channel in the fuller, a stepped glyph-stone guard, bronze-wire grip, block pommel."""
    parts = []
    # grip + pommel
    V, F = M.lathe([(0.0, -0.17), (0.03, -0.17), (0.034, -0.15), (0.024, -0.13), (0.022, 0.05), (0.0, 0.05)], 10)
    parts.append(P(V, F, "BH_DarkSteel", "grip"))
    parts.append(Z.coil((0, 0, -0.12), (0, 0, 0.04), 0.025, 7, 0.004, "BH_Gold", n=4, pts_per_turn=8))
    parts.append(slab((0.07, 0.05, 0.06), (0, 0, -0.19), bev=0.01))
    parts.append(A.ball((0, -0.026, -0.19), 0.012, "BH_Emissive", n=6, rings=4, scale=(1, 0.5, 1)))
    # stepped stone guard
    parts.append(slab((0.2, 0.06, 0.05), (0, 0, 0.065), bev=0.01))
    parts.append(slab((0.13, 0.07, 0.035), (0, 0, 0.105), mat="BH_Gold", bev=0.006))
    # blade: leaf outline, thick spine, bevelled edges
    zs = np.linspace(0.11, 0.84, 14)

    def hw(z):
        t = (z - 0.11) / (0.84 - 0.11)
        return 0.045 + 0.03 * math.sin(math.pi * min(t * 1.25, 1.0)) * (1 - t) ** 0.3 - 0.045 * max(t - 0.82, 0) / 0.18
    o = [(hw(z), z) for z in zs] + [(0.0, 0.9)] + [(-hw(z), z) for z in zs[::-1]]
    o = np.array(o)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    V, F = M.prism(o, 0.024, axis="y")
    bl = P(V, F, "BH_Bronze", "blade")
    bl.warp(lambda v: (v[0], v[1] * (1.0 - 0.75 * min(abs(v[0]) / 0.075, 1.0) ** 1.5), v[2]))
    parts.append(M.bevel(bl, 0.003, 1, angle=40))
    for sy in (1, -1):
        parts += chan([(0, sy * 0.0125, 0.13), (0, sy * 0.0125, 0.7)], (0, sy, 0), 0.0055)
        parts.append(A.tube([(-0.04, sy * 0.011, 0.14), (0.04, sy * 0.011, 0.14)], 0.004, "BH_Shadow", n=4))
    return parts
