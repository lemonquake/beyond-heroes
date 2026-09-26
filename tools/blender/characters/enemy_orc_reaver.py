"""Orc Reaver (Builder C): tall, broad-shouldered green-grey tusked orc raider. Bone-and-leather armour (rib-bone
chest plate over a leather harness, leather war-kilt, bracers), one spiked shoulder guard (left), red war-paint
across the eyes, black topknot on a shaved skull, a strip of Sulvane red cloth tied on the right arm (mercenary
token), and a heavy two-bladed war-axe in the right hand. ~2.0 m standing."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "creatures"))

import bh_mesh as M  # noqa: E402
from bh_body import Body, torso_loft, dome, smoothstep  # noqa: E402
from bh_math import normalize, Rx, Ry, Rz, R_axis  # noqa: E402
from bh_skeleton import proportions  # noqa: E402
import greenskin_kit as K  # noqa: E402

S = 1.1
PROPS = proportions(
    S,
    pelvis_h=1.06, hip_h=1.02, knee_h=0.565, ankle_h=0.09, hip_x=0.125,
    hips_len=0.11, spine_len=0.19, chest_len=0.28, neck_len=0.085, head_len=0.21,
    clav_x0=0.05, clav_drop=0.05, shoulder_x=0.265, upper_len=0.32, fore_len=0.30, hand_len=0.115, grip_x=0.085,
)
L = K.levels(PROPS)

PALETTE = "orc_reaver"
PALETTE_COLORS = {
    "BH_Skin": ((0.13, 0.18, 0.09), 0.0, 0.55, None, 0.0, 1.0),          # green-grey
    "BH_Flesh": ((0.06, 0.075, 0.045), 0.0, 0.55, None, 0.0, 1.0),
    "BH_Leather": ((0.075, 0.042, 0.022), 0.0, 0.65, None, 0.0, 1.0),
    "BH_Bone": ((0.58, 0.52, 0.40), 0.0, 0.6, None, 0.0, 1.0),
    "BH_Cloth_Primary": ((0.42, 0.025, 0.02), 0.0, 0.85, None, 0.0, 1.0),   # Sulvane red / war-paint
    "BH_Cloth_Secondary": ((0.07, 0.06, 0.05), 0.0, 0.9, None, 0.0, 1.0),   # trousers
    "BH_DarkSteel": ((0.11, 0.105, 0.10), 1.0, 0.5, None, 0.0, 1.0),
    "BH_Steel": ((0.45, 0.45, 0.44), 1.0, 0.38, None, 0.0, 1.0),
    "BH_Rust": ((0.25, 0.12, 0.06), 0.5, 0.8, None, 0.0, 1.0),
    "BH_Wood": ((0.11, 0.065, 0.035), 0.0, 0.72, None, 0.0, 1.0),
    "BH_Hair": ((0.03, 0.025, 0.022), 0.0, 0.65, None, 0.0, 1.0),
    "BH_Emissive": ((1.0, 0.55, 0.12), 0.0, 0.4, (1.0, 0.5, 0.1), 5.0, 1.0),  # small eye glints
    "BH_Shadow": ((0.03, 0.025, 0.02), 0.0, 0.8, None, 0.0, 1.0),
}

CLIPS = ["axe_1", "axe_3", "axe_heavy", "war_cry"]


def finish_mesh(mesh_ob):
    K.make_socket_deform(mesh_ob)


def torso_rows():
    zh, zs, zc, zn = L["hips"], L["spine"], L["chest"], L["neck"]
    return [
        (zh - 0.10, 0.165, 0.11, 0.115, 0.0, 0.0),
        (zh + 0.02, 0.17, 0.12, 0.115, 0.02, 0.0),
        (zs + 0.06, 0.175, 0.13, 0.115, 0.06, 0.0),
        (zc + 0.02, 0.2, 0.145, 0.125, 0.1, 0.0),
        (zc + 0.14, 0.235, 0.16, 0.14, 0.12, 0.005),
        (zn - 0.06, 0.25, 0.15, 0.15, 0.08, 0.012),
        (zn - 0.01, 0.2, 0.12, 0.13, 0.03, 0.02),
        (zn + 0.035, 0.09, 0.08, 0.085, 0.0, 0.015),
    ]


HEAD = [  # (dz, rx, ryf, ryb, keel, cy) relative to the head joint: wide jaw, heavy brow, sloped skull
    (-0.045, 0.040, 0.040, 0.030, 0.0, -0.035),
    (-0.030, 0.080, 0.085, 0.050, 0.10, -0.030),
    (0.000, 0.092, 0.100, 0.060, 0.12, -0.022),
    (0.035, 0.088, 0.100, 0.075, 0.10, -0.012),
    (0.075, 0.084, 0.098, 0.090, 0.06, -0.006),
    (0.110, 0.088, 0.090, 0.098, 0.02, 0.000),
    (0.150, 0.084, 0.078, 0.096, 0.0, 0.006),
    (0.185, 0.066, 0.060, 0.080, 0.0, 0.010),
    (0.210, 0.036, 0.034, 0.046, 0.0, 0.012),
]


def build(body: Body):
    add = body.add
    TW = K.torso_w(PROPS)
    V, F = torso_loft(torso_rows(), n=22, p=2.2, cap0=True, cap1=False)
    add(M.Part(V, F, "BH_Skin", name="torso"), weights=TW)
    # pectoral / belly shapes
    zc = L["chest"]
    for sx in (1, -1):
        add(K.blob((sx * 0.1, -0.13, zc + 0.15), 0.1, "BH_Skin", scale=(1.05, 0.45, 0.7), n=10, rings=6), weights=TW)

    # ---------------- armour: leather harness, rib-bone chest plate, belt, war-kilt
    chest_armour(body)
    kilt(body)

    # ---------------- legs: dark trousers, leather-wrapped shins, boots
    for s in ("L", "R"):
        K.leg(body, s, [(0.1, 0.105), (0.088, 0.092), (0.07, 0.074), (0.068, 0.07), (0.07, 0.074), (0.052, 0.055)],
              "BH_Cloth_Secondary", n=12)
        shin_wrap(body, s)
        K.bare_foot(body, s, "BH_Leather", length=0.3, width=0.058, height=0.075, toes=0)
        hx = PROPS["hip_x"] * (1 if s == "L" else -1)
        V, F = M.box(0.13, 0.3, 0.025, center=(hx, -0.07, 0.0125))
        add(M.bevel(M.Part(V, F, "BH_DarkSteel", name="sole"), 0.006, 1), "foot." + s)

    # ---------------- arms: skin, big deltoids, bracers, fists
    for s in ("L", "R"):
        K.arm(body, s, [(0.075, 0.08), (0.066, 0.07), (0.058, 0.06), (0.06, 0.06), (0.062, 0.058),
                        (0.045, 0.043)], "BH_Skin", n=12, deltoid=0.092)
        K.hand(body, s, "BH_Skin", scale=1.3)
        fa, ha = body.head("forearm." + s), body.head("hand." + s)
        V, F = M.tube([fa + (ha - fa) * 0.35, fa + (ha - fa) * 0.7, fa + (ha - fa) * 1.02],
                      [(0.07, 0.066), (0.067, 0.063), (0.056, 0.053)], n=12, up=(0, -1, 0))
        add(M.bevel(M.Part(V, F, "BH_Leather", name="bracer"), 0.004, 1, angle=50), "forearm." + s)
        for u in (0.45, 0.62, 0.8):   # bone studs on the bracer
            q = fa + (ha - fa) * u
            add(K.cone(q + (0, 0, 0.055), q + (0, 0, 0.09), 0.012, "BH_Bone", n=5), "forearm." + s)
    spiked_pauldron(body)
    red_armband(body)

    head(body)
    K.weapon_to_socket(body, "R", war_axe())


def chest_armour(body):
    add = body.add
    TW = K.torso_w(PROPS, shoulder_blend=False)
    zc, zn, zs = L["chest"], L["neck"], L["spine"]
    # leather harness: two straps over the shoulders crossing on the chest and back
    for sx in (1, -1):
        pts = [(sx * 0.13, 0.15, zn - 0.02), (sx * 0.15, 0.0, zn + 0.005), (sx * 0.13, -0.15, zn - 0.05),
               (sx * 0.02, -0.19, zc + 0.12), (-sx * 0.12, -0.165, zs + 0.06), (-sx * 0.17, -0.02, zs + 0.0),
               (-sx * 0.14, 0.12, zs + 0.04), (-sx * 0.02, 0.15, zc + 0.1), (sx * 0.13, 0.15, zn - 0.02)]
        add(K.rtube(pts, (0.026, 0.008), "BH_Leather", n=6, up=(0, 0, 1), p=3.0), weights=TW)
    # rib-bone chest plate: 4 curved bone bars + a sternum bone
    for i, z in enumerate(np.linspace(zc + 0.17, zc + 0.02, 4)):
        w = 0.19 - 0.02 * i
        pts = []
        for t in np.linspace(-1, 1, 9):
            x = t * w
            y = -0.2 + 0.1 * t * t - 0.01 * (1 - abs(t))
            pts.append((x, y + 0.015 * i, z - 0.03 * t * t))
        add(K.rtube(pts, (0.022, 0.014), "BH_Bone", n=6, up=(0, -1, 0)), weights=TW)
    add(K.rtube([(0, -0.215, zc + 0.2), (0, -0.21, zc + 0.08), (0, -0.19, zc - 0.03)], [0.028, 0.024, 0.02],
                "BH_Bone", n=7), weights=TW)
    # a skull-shaped boss where the harness crosses (big readable shape)
    add(K.blob((0, -0.225, zc + 0.12), 0.05, "BH_Bone", scale=(1, 0.7, 1.1), n=10, rings=6), weights=TW)
    for sx in (1, -1):
        add(K.blob((sx * 0.018, -0.258, zc + 0.125), 0.013, "BH_Shadow", scale=(1, 0.5, 1), n=6, rings=4),
            weights=TW)


def kilt(body):
    add = body.add
    zh = L["hips"]
    # wide belt
    V, F = torso_loft([(zh - 0.04, 0.188, 0.135, 0.13, 0.0), (zh + 0.06, 0.19, 0.14, 0.13, 0.02)], n=22)
    add(M.bevel(M.Part(V, F, "BH_Leather", name="belt"), 0.004, 1), "hips")
    add(K.blob((0, -0.15, zh + 0.01), 0.05, "BH_DarkSteel", scale=(1.2, 0.35, 1), n=10, rings=5), "hips")
    # seat
    V, F = torso_loft([(zh - 0.16, 0.17, 0.115, 0.12, 0.0), (zh - 0.04, 0.18, 0.125, 0.125, 0.0)], n=22)
    add(M.Part(V, F, "BH_Cloth_Secondary", name="seat"), weights=K.seat_w(body, zh - 0.03, zh - 0.16, 0.7))
    # leather tassets (6 hanging flaps around the hips, bone-studded)
    for k in range(7):
        ang = math.radians(-90 + (k - 3) * 38)
        if k in (0, 6):
            ang = math.radians(90 + (k - 3) * 10)
        ca, sa = math.cos(ang), math.sin(ang)
        r0x, r0y = 0.2, 0.15

        def fn(u, v, ca=ca, sa=sa):
            w = 0.09 + 0.015 * v
            tx, ty = -sa, ca
            px = (r0x + 0.05 * v) * ca + (u - 0.5) * w * tx / 0.19 * 0.19
            py = (r0y + 0.05 * v) * sa + (u - 0.5) * w * ty
            return (px, py, zh - 0.02 - 0.33 * v)
        V, F = M.grid(fn, 3, 4)
        fl = M.Part(V, F, "BH_Leather", name="tasset")
        if (np.cross(fl.V[1] - fl.V[0], fl.V[3] - fl.V[0])[:2] @ np.array([ca, sa])) < 0:
            fl.flip()
        add(M.solidify(fl, 0.01, offset=1.0), weights=K.seat_w(body, zh - 0.04, zh - 0.36, 0.85, center_w=0.03))
        c = np.array([(r0x + 0.045) * ca, (r0y + 0.045) * sa, zh - 0.26])
        add(K.blob(c, 0.016, "BH_Bone", n=6, rings=4), weights=K.seat_w(body, zh - 0.04, zh - 0.36, 0.85,
                                                                            center_w=0.03))


def shin_wrap(body, s):
    sh = "shin." + s
    k, a = body.head(sh), body.tail(sh)
    V, F = M.tube([a + (0, 0, 0.02), a + (k - a) * 0.5, a + (k - a) * 0.9],
                  [(0.062, 0.066), (0.078, 0.082), (0.074, 0.078)], n=12, up=(0, -1, 0))
    body.add(M.Part(V, F, "BH_Leather", name="wrap"), sh)
    for u in (0.25, 0.5, 0.75):
        q = a + (k - a) * u
        V, F = M.tube([q + (0, 0, 0.012), q - (0, 0, 0.012)], [(0.08, 0.084)] * 2, n=12, up=(0, -1, 0))
        body.add(M.Part(V, F, "BH_Cloth_Secondary", name="binding"), sh)
    # bone knee guard
    V, F = dome(k + (0, -0.06, 0.03), (0, -1, 0.2), 0.062, a_max=60, n=12, rings=4)
    body.add(M.solidify(M.Part(V, F, "BH_Bone", name="knee"), 0.012, offset=-1.0), weights=lambda V, s=s: [
        {"thigh." + s: 0.35, "shin." + s: 0.65}] * len(V))


def spiked_pauldron(body):
    s = "L"
    ua = "upper_arm." + s
    sh = body.head(ua)
    el = body.head("forearm." + s)
    axis = normalize(np.array([0.7, 0.0, 1.0]))
    c = sh + np.array([0.01, 0.0, 0.02])
    parts = []
    for i, (r, off) in enumerate(((0.165, 0.0), (0.14, -0.07), (0.12, -0.13))):
        V, F = dome(c + np.array([0.02 * i, 0, -0.0]) + normalize(el - sh) * (-off), axis, r, a_max=70, n=16,
                    rings=5, scale=(1.0, 1.15, 1.0))
        mat = "BH_DarkSteel" if i == 0 else "BH_Leather"
        parts.append(M.solidify(M.Part(V, F, mat, name="pauldron"), 0.012, offset=-1.0))
    # three big spikes (dark iron) + bone rim
    for k, (a, l) in enumerate(((-35, 0.2), (0, 0.26), (35, 0.2))):
        d = R_axis((0, 1, 0), 0) @ axis
        base = c + R_axis(axis, 0) @ (R_axis((1, 0, 0), a) @ (axis * 0.15))
        dirn = normalize(base - c + axis * 0.08)
        parts.append(K.cone(base - dirn * 0.03, base + dirn * l, 0.035, "BH_Bone", n=7))
    for p in parts:
        body.add(p, weights=lambda V: [{"shoulder.L": 0.3, "upper_arm.L": 0.7}] * len(V))
    # strap across the chest holding it
    zn = L["neck"]
    body.add(K.rtube([sh + (-0.05, -0.1, -0.05), (0.1, -0.18, zn - 0.12), (-0.05, -0.2, L["chest"] + 0.05),
                      (-0.2, -0.12, L["chest"] - 0.02)], (0.022, 0.007), "BH_Leather", n=6, up=(0, 0, 1), p=3.0),
             weights=K.torso_w(PROPS))


def red_armband(body):
    s = "R"
    ua = "upper_arm." + s
    sh, el = body.head(ua), body.head("forearm." + s)
    d = normalize(el - sh)
    q = sh + (el - sh) * 0.55
    V, F = M.tube([q - d * 0.04, q + d * 0.04], [(0.078, 0.082)] * 2, n=12, up=(0, -1, 0))
    body.add(M.Part(V, F, "BH_Cloth_Primary", name="armband"), ua)
    # knot + two hanging tails
    kpt = q + np.array([-0.075, -0.02, 0.0])
    body.add(K.blob(kpt, 0.025, "BH_Cloth_Primary", n=8, rings=5), ua)
    for dz, dy in ((-0.14, -0.03), (-0.12, 0.03)):
        pts = [kpt, kpt + (-0.02, dy * 0.5, dz * 0.5), kpt + (-0.015, dy, dz)]
        body.add(K.rtube(pts, [(0.022, 0.004), (0.02, 0.004), (0.018, 0.004)], "BH_Cloth_Primary", n=4,
                         up=(1, 0, 0), p=3.0),
                 weights=lambda V: [{"upper_arm.R": 0.8, "forearm.R": 0.2}] * len(V))


def head(body):
    add = body.add
    z0 = L["head"]
    H = K.head_rows(HEAD, z0)
    zn = L["neck"]
    V, F = M.tube([(0, 0.02, zn - 0.03), (0, 0.005, zn + 0.05), (0, -0.01, z0 + 0.03)],
                  [(0.085, 0.08), (0.078, 0.072), (0.07, 0.068)], n=12, up=(0, -1, 0))
    add(M.Part(V, F, "BH_Skin", name="neck"),
        weights=K.zspec_w([(zn - 0.0, "chest"), (zn + 0.03, "neck"), (z0 - 0.01, "neck"), (z0 + 0.03, "head")]))
    V, F = torso_loft(H, n=22, p=2.2, cap0=True, cap1=True)
    add(M.Part(V, F, "BH_Skin", name="head"), "head")
    # heavy brow ridge
    zb = z0 + 0.1
    yb = K.front_of(H, 0, zb)
    add(K.rtube([(-0.08, yb + 0.03, zb - 0.01), (-0.035, yb - 0.004, zb + 0.004), (0, yb + 0.002, zb - 0.006),
                 (0.035, yb - 0.004, zb + 0.004), (0.08, yb + 0.03, zb - 0.01)], 0.02, "BH_Skin", n=6,
                up=(0, -1, 0)), "head")
    # red war-paint band across the eyes (thin shell on the face)
    rows = []
    for z in (z0 + 0.058, z0 + 0.092):
        r = []
        for x in np.linspace(-0.095, 0.095, 11):
            xx = min(abs(x), 0.083) * np.sign(x)
            r.append((x, K.front_of(H, xx, z, p=2.2) - 0.003 + 0.6 * max(0.0, abs(x) - 0.06), z))
        rows.append(np.array(r))
    V, F = M.loft(rows, cap0=False, cap1=False, closed=False)
    add(M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="warpaint").flip(), 0.004, offset=1.0), "head")
    # eyes
    for sx in (1, -1):
        ye = K.front_of(H, 0.035, z0 + 0.075, p=2.2)
        add(K.blob((sx * 0.036, ye - 0.004, z0 + 0.075), 0.017, "BH_Shadow", scale=(1.2, 0.5, 0.6), n=8, rings=4),
            "head")
        add(K.blob((sx * 0.037, ye - 0.01, z0 + 0.076), 0.007, "BH_Emissive", scale=(1.3, 0.6, 0.7), n=6, rings=4),
            "head")
    # broad flat nose
    yn = K.front_of(H, 0, z0 + 0.05, p=2.2)
    add(K.rtube([(0, yn + 0.004, z0 + 0.085), (0, yn - 0.022, z0 + 0.05), (0, yn - 0.02, z0 + 0.03)],
                [(0.016, 0.012), (0.03, 0.018), (0.028, 0.014)], "BH_Skin", n=8, up=(0, 0, 1)), "head")
    # jaw: underbite lower lip + two big tusks + mouth slit
    zm = z0 + 0.005
    ym = K.front_of(H, 0, zm, p=2.2)
    add(K.rtube([(x, K.front_of(H, x, zm, p=2.2) - 0.004, zm - 0.004 + 3 * x * x) for x in np.linspace(-0.06, 0.06, 7)],
                (0.007, 0.004), "BH_Shadow", n=5), "head")
    for sx in (1, -1):
        b = np.array([sx * 0.04, K.front_of(H, 0.04, zm - 0.01, p=2.2) + 0.008, zm - 0.012])
        add(K.rtube([b, b + (sx * 0.006, -0.012, 0.035), b + (sx * 0.016, -0.004, 0.068)], [0.013, 0.01, 0.002],
                    "BH_Bone", n=7), "head")
    # pointed ears swept back
    for sx in (1, -1):
        rx, cy = K.side_of(H, z0 + 0.07)
        root = (sx * (rx - 0.01), cy + 0.02, z0 + 0.07)
        add(K.ear(root, 0.1, 0.06, "BH_Skin", out=(sx * 0.8, 0.8, 0.3), up=(0, 0, 1), thick=0.014), "head")
        # iron ear rings
        add(K.rtube([np.array(root) + (sx * 0.03, 0.03, -0.02) + 0.013 * np.array([0, math.cos(a), math.sin(a)])
                     for a in np.linspace(0, 2 * math.pi, 9)], 0.004, "BH_DarkSteel", n=4, cap=False), "head")
    # topknot: tied hair rising from the crown then falling back
    top = np.array([0, 0.03, z0 + 0.205])
    add(K.rtube([top - (0, 0, 0.02), top + (0, 0.0, 0.03)], [0.035, 0.03], "BH_Leather", n=8), "head")
    pts = [top + (0, 0.0, 0.02), top + (0, 0.02, 0.09), top + (0, 0.07, 0.12), top + (0, 0.13, 0.08),
           top + (0, 0.17, 0.0), top + (0, 0.19, -0.1)]
    add(K.rtube(pts, [0.032, 0.036, 0.034, 0.03, 0.024, 0.012], "BH_Hair", n=8, up=(1, 0, 0)), "head")


def war_axe():
    """Heavy two-bladed war-axe: long haft (grip at origin, left hand ~0.16 m below), two crescent bits at the top,
    a spike on the head, iron bands. Long axis +Z, flats +-Y, bits toward +-X."""
    parts = []
    V, F = M.lathe([(0, -0.46), (0.03, -0.46), (0.034, -0.43), (0.024, -0.4), (0.022, 0.2), (0.024, 0.8),
                    (0.02, 0.86), (0, 0.87)], 10)
    parts.append(M.Part(V, F, "BH_Wood", name="haft"))
    for z0, z1 in ((-0.1, 0.08), (-0.34, -0.16)):
        V, F = M.lathe([(0, z0), (0.027, z0), (0.027, z1), (0, z1)], 10)
        parts.append(M.Part(V, F, "BH_Leather", name="grip"))
    for z in (0.12, 0.3, 0.5):
        V, F = M.lathe([(0, z - 0.012), (0.028, z - 0.012), (0.028, z + 0.012), (0, z + 0.012)], 10)
        parts.append(M.Part(V, F, "BH_DarkSteel", name="band"))
    # two crescent bits (mirrored), thick at the eye, thin at the edge
    out = [(0.03, 0.66), (0.09, 0.64), (0.16, 0.56), (0.25, 0.50), (0.29, 0.58), (0.31, 0.68), (0.31, 0.78),
           (0.29, 0.88), (0.25, 0.96), (0.16, 0.9), (0.09, 0.82), (0.03, 0.8)]
    o = M.resample_closed(np.array(out), 36)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    for sx in (1, -1):
        V, F = M.prism(o, 0.05, axis="y")
        bit = M.Part(V, F, "BH_Steel", name="bit")
        bit.warp(lambda v: (v[0], v[1] * (1.0 - 0.85 * min(max((v[0] - 0.04) / 0.26, 0), 1)), v[2]))
        bit = M.bevel(bit, 0.003, 1, angle=50)
        if sx < 0:
            bit = bit.mirrored(False)
        parts.append(bit)
        # dark inner plate (reads as a heavy forged head)
        V, F = M.prism(np.array([(0.03, 0.64), (0.11, 0.62), (0.11, 0.84), (0.03, 0.82)]), 0.062, axis="y")
        pl = M.Part(V, F, "BH_DarkSteel", name="cheek")
        if sx < 0:
            pl = pl.mirrored(False)
        parts.append(pl)
    V, F = M.lathe([(0, 0.62), (0.04, 0.62), (0.045, 0.73), (0.04, 0.85), (0.0, 0.86)], 10)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="eye"))
    V, F = M.lathe([(0, 0.85), (0.03, 0.86), (0.012, 0.95), (0.0, 1.0)], 8)
    parts.append(M.Part(V, F, "BH_Steel", name="spike"))
    V, F = M.lathe([(0, -0.52), (0.035, -0.48), (0.04, -0.46), (0.0, -0.44)], 8)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="butt"))
    return parts
