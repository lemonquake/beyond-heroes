"""Goblin Sapper (bh-013, Builder B2 "brutes"; goblin demolition skirmisher): a small wiry mustard-green goblin in a
long soot-black leather apron and thick leather gloves, a quilted ochre padded cap with brass goggles pushed up on the
brow, a bandolier of fuse sticks and coiled fuse cord across the chest, and - the silhouette key - a big wooden
pack-frame on its back loaded with clay fire-pots and black iron bombs lashed with rope, every one trailing a lit
fuse with a small orange spark (BH_Emissive). A short knife in the right hand, a round studded clay mine with a
sputtering fuse held in the left hand.

~1.15 m to the top of the cap (the bomb stack and its sparks peak at ~1.2 m behind the head). Same goblin skeleton
proportions as the Goblin Skulker (greenskin kit), different head gear, clothing, palette and back load.
Clips: dagger_1, dagger_2 (knife), cast_quick (lob a bomb), cast_weapon (plant / throw the mine), blink (dive-roll
escape) + the enemy base set."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft, dome  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz  # noqa: E402
import greenskin_kit as K  # noqa: E402
import enemy_goblin_skulker as GS  # noqa: E402

PROPS = GS.PROPS
L = GS.L

PALETTE = "goblin_sapper"
PALETTE_COLORS = {
    "BH_Skin": ((0.2, 0.19, 0.055), 0.0, 0.6, None, 0.0, 1.0),               # mustard-green
    "BH_Flesh": ((0.11, 0.1, 0.03), 0.0, 0.6, None, 0.0, 1.0),               # inner ear / mottling
    "BH_Leather": ((0.05, 0.035, 0.025), 0.0, 0.7, None, 0.0, 1.0),          # soot-black apron, gloves, straps
    "BH_Cloth_Primary": ((0.24, 0.07, 0.035), 0.0, 0.9, None, 0.0, 1.0),     # rust-red breeches / fuse wraps
    "BH_Cloth_Secondary": ((0.5, 0.33, 0.12), 0.0, 0.92, None, 0.0, 1.0),    # ochre quilted cap, rope, fuse cord
    "BH_Stone": ((0.46, 0.17, 0.07), 0.0, 0.85, None, 0.0, 1.0),             # terracotta fire-pots / mine
    "BH_DarkSteel": ((0.06, 0.06, 0.065), 0.8, 0.5, None, 0.0, 1.0),         # black iron bombs, pot bands
    "BH_Steel": ((0.4, 0.4, 0.39), 1.0, 0.4, None, 0.0, 1.0),                # knife
    "BH_Bronze": ((0.72, 0.5, 0.2), 1.0, 0.35, None, 0.0, 1.0),              # brass goggles, buckles, mine studs
    "BH_Aether": ((0.45, 0.62, 0.62), 0.6, 0.08, None, 0.0, 1.0),            # goggle glass
    "BH_Wood": ((0.2, 0.12, 0.06), 0.0, 0.75, None, 0.0, 1.0),               # pack frame
    "BH_Bone": ((0.6, 0.55, 0.42), 0.0, 0.6, None, 0.0, 1.0),                # teeth, toe claws
    "BH_Shadow": ((0.03, 0.025, 0.02), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((1.0, 0.55, 0.1), 0.0, 0.4, (1.0, 0.5, 0.08), 9.0, 1.0),  # fuse sparks + eyes
}

CLIPS = ["dagger_1", "dagger_2", "cast_quick", "cast_weapon", "blink"]


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def build(body: Body):
    add = body.add
    TW = K.torso_w(PROPS)
    rows = GS.torso_rows()
    V, F = torso_loft(rows, n=20, p=2.2, cap0=True, cap1=False)
    add(M.Part(V, F, "BH_Skin", name="torso"), weights=TW)

    # breeches seat
    zh = L["hips"]
    V, F = torso_loft([(zh - 0.085, 0.097, 0.073, 0.075, 0.0), (zh - 0.03, 0.099, 0.075, 0.075, 0.0),
                       (zh + 0.035, 0.097, 0.075, 0.073, 0.0)], n=20)
    add(M.Part(V, F, "BH_Cloth_Primary", name="seat"), weights=K.seat_w(body, zh + 0.02, zh - 0.09, 0.7))

    # legs: short breeches over wiry bowed legs, big bare feet
    for s in ("L", "R"):
        pts = K.leg(body, s, [(0.05, 0.052), (0.043, 0.045), (0.033, 0.035), (0.035, 0.035), (0.033, 0.035),
                              (0.022, 0.024)], "BH_Skin", bow=0.04, n=10)
        th = "thigh." + s
        V, F = M.tube([pts[0] + (0, 0, 0.01), pts[1], pts[2] + (pts[3] - pts[2]) * 0.3],
                      [(0.058, 0.06), (0.052, 0.054), (0.044, 0.046)], n=12, up=(0, -1, 0))
        add(M.Part(V, F, "BH_Cloth_Primary", name="breeches"), weights=body.seg_weights([th, "shin." + s], power=10))
        K.bare_foot(body, s, "BH_Skin", length=0.2, width=0.042, height=0.045, claw_mat="BH_Bone", toes=3,
                    toe_r=0.013)
        # leather knee pad (crawling in tunnels)
        k = body.head("shin." + s)
        add(K.blob(k + (0, -0.03, 0.0), 0.034, "BH_Leather", scale=(1.0, 0.55, 1.1), n=8, rings=5),
            weights=lambda V, s=s: [{"thigh." + s: 0.4, "shin." + s: 0.6}] * len(V))
        # shin wrap
        a = body.tail("shin." + s)
        add(K.rtube([k + (a - k) * 0.55, k + (a - k) * 0.8], [(0.032, 0.033), (0.027, 0.028)], "BH_Cloth_Secondary",
                    n=8), "shin." + s)

    # arms, thick leather gloves with flared cuffs
    for s in ("L", "R"):
        K.arm(body, s, [(0.035, 0.035), (0.029, 0.03), (0.025, 0.026), (0.027, 0.027), (0.029, 0.027),
                        (0.022, 0.021)], "BH_Skin", n=10, deltoid=0.036)
        K.hand(body, s, "BH_Leather", scale=1.05)
        fa, ha = body.head("forearm." + s), body.head("hand." + s)
        V, F = M.tube([fa + (ha - fa) * 0.5, fa + (ha - fa) * 0.8, fa + (ha - fa) * 1.02],
                      [(0.043, 0.042), (0.036, 0.035), (0.029, 0.028)], n=10, up=(0, -1, 0))
        add(M.Part(V, F, "BH_Leather", name="glove_cuff"), "forearm." + s)

    apron(body, rows, TW)
    head(body)
    bandolier(body, rows, TW)
    pack(body, TW)
    K.weapon_to_socket(body, "R", GS.knife())
    K.weapon_to_socket(body, "L", mine())


# ----------------------------------------------------------------------------------------------------- apron
def apron(body, rows, TW):
    add = body.add
    zh = L["hips"]
    # bib: follows the chest front from the belly up to the chest
    z0, z1 = zh + 0.01, L["chest"] + 0.07

    def bib(u, v):
        z = z0 + (z1 - z0) * v
        w = 0.17 - 0.05 * v
        x = (u - 0.5) * w
        return (x, K.front_of(rows, x, z) - 0.012, z)
    V, F = M.grid(bib, 7, 6)
    add(M.solidify(M.Part(V, F, "BH_Leather", name="bib"), 0.008, offset=1.0), weights=TW)

    # skirt to the knees (hangs from the belt, follows the legs)
    zb = 0.26

    def skirt(u, v):
        z = zh + 0.02 - (zh + 0.02 - zb) * v
        w = 0.19 + 0.05 * v
        x = (u - 0.5) * w
        y = -(0.083 + 0.035 * v) - 0.02 * (1 - (2 * u - 1) ** 2) + 0.005 * math.sin(u * 11 + v * 4) * v
        return (x, y, z)
    V, F = M.grid(skirt, 8, 7)
    sk = M.Part(V, F, "BH_Leather", name="apron")
    sk.flip()
    add(M.solidify(sk, 0.008, offset=1.0), weights=K.seat_w(body, zh + 0.02, zb, 0.5, center_w=0.05))
    # scorch patch + brass buckles on the bib
    add(K.blob((0.03, K.front_of(rows, 0.03, zh - 0.06) - 0.06, zh - 0.12), 0.035, "BH_Shadow", scale=(1.0, 0.2, 1.3),
               n=8, rings=4), weights=K.seat_w(body, zh, zb, 0.5, center_w=0.05))
    for sx in (1, -1):
        p = np.array([sx * 0.06, K.front_of(rows, sx * 0.06, z1 - 0.01) - 0.02, z1 - 0.01])
        add(K.blob(p, 0.011, "BH_Bronze", scale=(1.0, 0.4, 1.0), n=6, rings=3), weights=TW)
        # neck straps up over the shoulders
        add(K.rtube([p, p + (sx * 0.0, 0.0, 0.07), (sx * 0.05, -0.02, L["neck"] + 0.01), (sx * 0.05, 0.05, L["neck"])],
                    (0.009, 0.004), "BH_Leather", n=5, up=(0, 0, 1)), weights=TW)
    # waist tie + belt with pouches
    belt = K.rtube([(0.104 * math.cos(a), 0.082 * math.sin(a), zh + 0.03) for a in np.linspace(0, 2 * math.pi, 17)],
                   0.011, "BH_Leather", n=6, up=(0, 0, 1), cap=False)
    add(belt, "hips")
    add(K.blob((0.0, -0.088, zh + 0.03), 0.016, "BH_Bronze", scale=(1.2, 0.5, 1.0), n=6, rings=3), "hips")
    for ang in (160, 20):
        a = math.radians(ang)
        c = np.array([0.112 * math.cos(a), 0.09 * math.sin(a) + 0.01, zh - 0.0])
        add(K.blob(c, 0.035, "BH_Leather", scale=(0.9, 0.65, 1.0), n=8, rings=5), "hips")
    # one spare black bomb hanging from the right hip
    c = np.array([-0.12, -0.02, zh - 0.05])
    for prt in bomb(0.035, fuse=False):
        prt.move(c)
        add(prt, "hips")


# ------------------------------------------------------------------------------------------------------ head
def head(body):
    add = body.add
    z0 = L["head"]
    H = K.head_rows(GS.HEAD, z0, sx=1.08, sy=1.06, sz=1.0, dy=-0.012)
    V, F = M.tube([(0, 0.012, L["neck"] - 0.02), (0, 0.0, L["neck"] + 0.03), (0, -0.018, z0 + 0.02)],
                  [(0.036, 0.034), (0.033, 0.03), (0.035, 0.033)], n=10, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="neck"),
        weights=K.zspec_w([(L["neck"] - 0.01, "chest"), (L["neck"] + 0.02, "neck"), (z0 + 0.0, "neck"),
                           (z0 + 0.02, "head")]))
    V, F = torso_loft(H, n=20, p=2.1, cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Skin", name="head"), "head")
    zb = z0 + 0.075
    yb = K.front_of(H, 0, zb) + 0.004
    add(K.rtube([(-0.058, yb + 0.02, zb - 0.006), (-0.025, yb - 0.004, zb + 0.002), (0.0, yb - 0.002, zb - 0.004),
                 (0.025, yb - 0.004, zb + 0.002), (0.058, yb + 0.02, zb - 0.006)], 0.012, "BH_Skin", n=6,
                up=(0, -1, 0)), "head")
    for sx in (1, -1):
        ye = K.front_of(H, 0.03, z0 + 0.058)
        add(K.blob((sx * 0.031, ye + 0.006, z0 + 0.058), 0.018, "BH_Shadow", scale=(1.2, 0.5, 0.7), n=8, rings=4),
            "head")
        add(K.blob((sx * 0.032, ye - 0.001, z0 + 0.059), 0.0075, "BH_Emissive", scale=(1.3, 0.6, 0.8), n=6, rings=4),
            "head")
    # long pointed nose (straighter than the skulker's hook)
    yn = K.front_of(H, 0, z0 + 0.05)
    add(K.rtube([(0, yn + 0.005, z0 + 0.066), (0, yn - 0.04, z0 + 0.05), (0, yn - 0.08, z0 + 0.036),
                 (0, yn - 0.1, z0 + 0.03)],
                [(0.015, 0.013), (0.017, 0.015), (0.012, 0.01), (0.004, 0.004)], "BH_Skin", n=8, up=(0, 0, 1)), "head")
    # grin with a row of small teeth
    ym = K.front_of(H, 0, z0 - 0.002)
    mouth = [(x, K.front_of(H, x, z0 - 0.002 + 5 * x * x) + 0.002, z0 - 0.002 + 5 * x * x)
             for x in np.linspace(-0.052, 0.052, 7)]
    add(K.rtube(mouth, (0.008, 0.005), "BH_Shadow", n=5), "head")
    for x in (-0.03, -0.012, 0.012, 0.03):
        add(K.cone((x, ym + 0.003, z0 + 0.004 + 3 * x * x), (x, ym - 0.004, z0 - 0.012 + 3 * x * x), 0.005, "BH_Bone",
                   n=4), "head")
    # ears: long, drooping down and back out from under the cap
    for sx in (1, -1):
        rx, cy = K.side_of(H, z0 + 0.05)
        root = (sx * (rx - 0.012), cy + 0.02, z0 + 0.055)
        add(K.ear(root, 0.2, 0.09, "BH_Skin", out=(sx * 1.0, 0.45, -0.05), up=(0, 0.2, 1), droop=0.05, thick=0.013),
            "head")
        add(K.ear(np.array(root) + (sx * 0.025, 0.004, 0.004), 0.14, 0.05, "BH_Flesh", out=(sx * 1.0, 0.45, -0.05),
                  up=(0, 0.2, 1), droop=0.035, thick=0.004), "head")
    cap_and_goggles(body, z0)


def cap_and_goggles(body, z0):
    add = body.add
    parts = []
    # quilted padded cap: dome with raised meridian seams and a rolled rim
    V, F = dome((0, 0, 0), (0, 0, 1), 0.106, a_max=92, n=20, rings=7, scale=(1.0, 1.08, 0.9))
    parts.append(M.solidify(M.Part(V, F, "BH_Cloth_Secondary", name="cap"), 0.012, offset=1.0))
    for k in range(8):
        a = 2 * math.pi * k / 8
        pts = []
        for t in np.linspace(0.0, 1.0, 6):
            el = math.radians(90 * t)
            pts.append((0.112 * math.cos(el) * math.cos(a), 0.112 * 1.08 * math.cos(el) * math.sin(a),
                        0.112 * 0.9 * math.sin(el)))
        parts.append(K.rtube(pts, 0.006, "BH_Cloth_Secondary", n=4))
    parts.append(K.rtube([(0.113 * math.cos(a), 0.113 * 1.08 * math.sin(a), -0.006)
                          for a in np.linspace(0, 2 * math.pi, 21)], 0.013, "BH_Cloth_Secondary", n=6, cap=False))
    # goggle strap round the cap + goggles pushed up on the brow
    parts.append(K.rtube([(0.117 * math.cos(a), 0.117 * 1.08 * math.sin(a), 0.035)
                          for a in np.linspace(0, 2 * math.pi, 21)], (0.006, 0.012), "BH_Leather", n=5, up=(0, 0, 1),
                         cap=False))
    for sx in (1, -1):
        c = np.array([sx * 0.04, -0.118, 0.045])
        nrm = normalize(np.array([sx * 0.25, -1.0, 0.55]))
        t1 = normalize(np.cross(nrm, (0, 0, 1)))
        t2 = np.cross(nrm, t1)
        ring = [c + 0.028 * (t1 * math.cos(a) + t2 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 13)]
        parts.append(K.rtube(ring, 0.009, "BH_Bronze", n=5, cap=False))
        cup = [c - nrm * 0.012 + 0.03 * (t1 * math.cos(a) + t2 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 13)]
        parts.append(K.rtube(cup, 0.007, "BH_Leather", n=4, cap=False))
        parts.append(K.blob(c + nrm * 0.002, 0.024, "BH_Aether", scale=(1, 1, 0.3), n=10, rings=3,
                            rot=_align(nrm)))
    parts.append(K.rtube([(0.012, -0.12, 0.05), (0.0, -0.126, 0.056), (-0.012, -0.12, 0.05)], 0.006, "BH_Bronze", n=4))
    for p in parts:
        p.rot(Rx(12)).move((0.0, 0.004, z0 + 0.105))
        add(p, "head")


def _align(n):
    from bh_body import M_align_z
    return M_align_z(normalize(np.asarray(n, float)))


# -------------------------------------------------------------------------------------------------- bandolier
def bandolier(body, rows, TW):
    """Diagonal strap (right shoulder -> left hip) with fuse sticks and a coil of fuse cord."""
    add = body.add
    zn, zc, zs, zh = L["neck"], L["chest"], L["spine"], L["hips"]
    pts = [(-0.075, 0.07, zn - 0.02), (-0.09, -0.01, zn - 0.035), (-0.05, -0.08, zc + 0.05),
           (0.02, -0.09, zc - 0.01), (0.075, -0.085, zs + 0.0), (0.1, -0.03, zh + 0.03), (0.09, 0.06, zh + 0.03),
           (0.02, 0.1, zc - 0.02), (-0.06, 0.1, zc + 0.08), (-0.075, 0.07, zn - 0.02)]
    add(K.rtube(pts, (0.014, 0.005), "BH_Leather", n=5, up=(0, 0, 1), p=3.0), weights=TW)
    # fuse sticks tucked in loops across the chest
    for k, u in enumerate((0.2, 0.32, 0.44, 0.56)):
        a = np.array(pts[2]) + (np.array(pts[4]) - np.array(pts[2])) * u
        a = a + np.array([0, -0.012, 0])
        d = normalize(np.array([0.35, 0.0, 1.0]))
        add(K.rtube([a - d * 0.03, a + d * 0.035], 0.0085, "BH_Cloth_Primary", n=6), weights=TW)
        add(K.blob(a + d * 0.04, 0.007, "BH_Cloth_Secondary", n=5, rings=3), weights=TW)
    # coil of fuse cord hanging at the left side
    c = np.array([0.1, -0.055, zs + 0.02])
    for r, dz in ((0.03, 0.0), (0.028, -0.008), (0.031, 0.008)):
        ring = [c + (r * math.cos(a) * 0.4, r * math.sin(a) * 0.2 - 0.004, r * math.sin(a + 1.6) + dz)
                for a in np.linspace(0, 2 * math.pi, 11)]
        add(K.rtube(ring, 0.005, "BH_Cloth_Secondary", n=4, cap=False), weights=TW)


# -------------------------------------------------------------------------------------------------- the pack
def spark(c, s=1.0):
    """Lit fuse tip: bright core + four short rays (reads as a sputtering spark at the gameplay camera)."""
    s = s * 1.25
    out = [K.blob(c, 0.013 * s, "BH_Emissive", n=6, rings=4)]
    for d in ((1, 0.2, 0.9), (-0.9, 0.3, 0.8), (0.2, -1, 0.7), (-0.2, 0.9, 1.0)):
        d = normalize(np.array(d, float))
        out.append(K.cone(c, c + d * 0.034 * s, 0.006 * s, "BH_Emissive", n=4))
    return out


def fire_pot(r, fuse_dir=(0.3, 0.2, 1.0), seed=0):
    parts = []
    V, F = M.lathe([(0.0, -r), (r * 0.55, -r * 0.98), (r * 0.95, -r * 0.55), (r * 1.0, 0.0), (r * 0.82, r * 0.55),
                    (r * 0.42, r * 0.82), (r * 0.5, r * 0.98), (r * 0.32, r * 1.02), (0, r * 1.0)], 10)
    parts.append(M.Part(V, F, "BH_Stone", name="pot"))
    for zz in (0.25, -0.35):
        rr = r * math.sqrt(max(0.0, 1 - zz * zz)) * 1.02
        parts.append(K.rtube([(rr * math.cos(a), rr * math.sin(a), r * zz) for a in np.linspace(0, 2 * math.pi, 11)],
                             r * 0.08, "BH_DarkSteel", n=4, cap=False))
    top = np.array([0, 0, r * 1.0])
    d = normalize(np.array(fuse_dir, float))
    tip = top + d * r * 0.9 + np.array([0, 0, r * 0.2])
    parts.append(K.rtube([top, top + d * r * 0.4 + (0, 0, r * 0.25), tip], 0.0045, "BH_Cloth_Secondary", n=4))
    parts += spark(tip, 0.9 + 0.2 * (seed % 2))
    return parts


def bomb(r, fuse=True, fuse_dir=(0.0, 0.3, 1.0)):
    parts = []
    V, F = M.sphere(r, 12, 8)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="bomb"))
    V, F = M.lathe([(0.0, r * 0.85), (r * 0.32, r * 0.85), (r * 0.32, r * 1.2), (0.0, r * 1.2)], 8)
    parts.append(M.Part(V, F, "BH_Bronze", name="bomb_neck"))
    if fuse:
        top = np.array([0, 0, r * 1.2])
        d = normalize(np.array(fuse_dir, float))
        tip = top + d * r * 0.8
        parts.append(K.rtube([top, top + (0, 0, r * 0.35), tip], 0.0045, "BH_Cloth_Secondary", n=4))
        parts += spark(tip)
    return parts


def pack(body, TW):
    add = body.add
    zc, zn = L["chest"], L["neck"]
    yb = 0.115                          # frame plane just behind the shoulder blades
    parts = []
    # wooden A-frame: two uprights, cross bars, a bottom shelf - wider than the goblin's shoulders
    for sx in (1, -1):
        parts.append(K.rtube([(sx * 0.19, yb, 0.46), (sx * 0.2, yb + 0.01, 0.8), (sx * 0.17, yb, 1.16)], 0.015,
                             "BH_Wood", n=6))
        parts.append(K.blob((sx * 0.17, yb, 1.17), 0.02, "BH_Wood", n=6, rings=4))
    for z in (0.5, 0.8, 1.05):
        parts.append(K.rtube([(-0.2, yb, z), (0.2, yb, z)], 0.012, "BH_Wood", n=5))
    V, F = M.box(0.42, 0.21, 0.02, center=(0.0, yb + 0.1, 0.49))
    parts.append(M.Part(V, F, "BH_Wood", name="shelf"))
    parts.append(K.rtube([(-0.2, yb + 0.2, 0.5), (0.2, yb + 0.2, 0.5)], 0.011, "BH_Wood", n=5))
    # the load: fire-pots and bombs stacked on the shelf, spilling over the frame top
    load = [("pot", 0.08, (-0.12, yb + 0.1, 0.585), (-0.8, 0.3, 1.0)),
            ("bomb", 0.06, (0.005, yb + 0.12, 0.565), (0.1, 0.8, 1.0)),
            ("pot", 0.078, (0.125, yb + 0.1, 0.585), (0.8, 0.4, 1.0)),
            ("pot", 0.07, (-0.1, yb + 0.1, 0.76), (-0.9, 0.5, 1.0)),
            ("bomb", 0.062, (0.02, yb + 0.11, 0.72), (0.2, 0.9, 0.6)),
            ("pot", 0.068, (0.125, yb + 0.1, 0.755), (0.9, 0.2, 1.0)),
            ("pot", 0.074, (-0.05, yb + 0.1, 0.925), (-0.5, 0.4, 1.0)),
            ("bomb", 0.056, (0.09, yb + 0.12, 0.905), (0.8, 0.3, 0.8)),
            ("bomb", 0.05, (-0.1, yb + 0.1, 1.06), (-0.6, 0.3, 1.0)),
            ("pot", 0.058, (0.05, yb + 0.1, 1.06), (0.5, 0.3, 1.0)),
            ("bomb", 0.042, (-0.02, yb + 0.12, 1.15), (0.1, 0.4, 1.0))]
    for k, (kind, r, c, fd) in enumerate(load):
        pp = fire_pot(r, fd, seed=k) if kind == "pot" else bomb(r, fuse_dir=fd)
        for p in pp:
            p.move(c)
        parts += pp
    # rope lashing round the stack
    for z, w, d in ((0.66, 0.215, 0.11), (0.84, 0.205, 0.1), (1.0, 0.16, 0.09)):
        ring = [(w * math.cos(a), yb + 0.1 + d * math.sin(a), z + 0.01 * math.sin(3 * a))
                for a in np.linspace(0, 2 * math.pi, 17)]
        parts.append(K.rtube(ring, 0.007, "BH_Cloth_Secondary", n=4, cap=False))
    for p in parts:
        add(p, "chest")
    # shoulder straps: frame top -> over the shoulder -> down the front -> under the arm to the frame bottom
    for sx in (1, -1):
        pts = [(sx * 0.1, yb, zn - 0.05), (sx * 0.075, 0.06, zn + 0.005), (sx * 0.075, -0.02, zn - 0.01),
               (sx * 0.08, -0.075, zc + 0.03), (sx * 0.105, -0.05, zc - 0.06), (sx * 0.12, 0.04, zc - 0.08),
               (sx * 0.14, yb, 0.52)]
        add(K.rtube(pts, (0.013, 0.005), "BH_Leather", n=5, up=(0, 0, 1), p=3.0), weights=TW)


# --------------------------------------------------------------------------------------------------- the mine
def mine():
    """Round studded clay mine held in the left fist (socket space: grip at origin, +Z along the fingers' curl axis)."""
    parts = []
    r = 0.07
    V, F = M.sphere(r, 14, 8, scale=(1.0, 1.0, 0.55))
    parts.append(M.Part(V, F, "BH_Stone", name="mine"))
    parts.append(K.rtube([(r * 1.0 * math.cos(a), r * 1.0 * math.sin(a), 0.0) for a in np.linspace(0, 2 * math.pi, 17)],
                         0.008, "BH_DarkSteel", n=4, cap=False))
    for k in range(8):
        a = 2 * math.pi * k / 8
        parts.append(K.blob((r * 0.78 * math.cos(a), r * 0.78 * math.sin(a), r * 0.38), 0.009, "BH_Bronze", n=5,
                            rings=3))
    top = np.array([0.0, 0.0, r * 0.55])
    parts.append(K.rtube([top, top + (0.01, 0.0, 0.03), top + (0.035, 0.0, 0.045)], 0.0045, "BH_Cloth_Secondary", n=4))
    parts += spark(top + np.array([0.035, 0.0, 0.045]), 0.9)
    # seat the disc on the palm: flat face toward the palm (socket -X), shifted out of the fist a little
    for p in parts:
        p.rot(Ry(90)).move((-0.02, 0.0, 0.03))
    return parts
