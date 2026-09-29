"""Paul David, the Tempest Blade (bh-021, contracts/story.md): Class SX, Lv 251. The last of the Dawnbreakers who can
still be found: an old soldier living quietly by the lake in Olivar.

Lean and tall, grey at the temples, hair tied back, a short grey beard and a moustache, an old scar down the left
cheek. A long storm-blue riding coat with silver trim over a brigandine and mail, a single steel pauldron on the left
shoulder, leather bracers, tall boots, a longsword (Stormwake) sheathed on the left hip — its hilt uses material
BH_Hilt so the game can hide it when the blade is drawn (the drawn sword is the stormwake weapon GLB). His right hand
carries Kethrax's brand: violet chain-marks burned round the wrist and over the back of the glove.
A sculpted face (not the townsfolk head): brow ridge, cheekbones, eye sockets with eyes and lids, a real nose, lips,
ears. The game scales him to ~1.86 m.
"""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, interp_rows, front_y, back_y, dome, M_align_z, smoothstep
from bh_math import normalize, R_axis, Rx, Rz
from bh_skeleton import proportions
import town_matron as K
from town_matron import Kit, P_, outward, rope
from char_mage import ring_frac
import legend_kit as LK

PROPS = proportions(1.0, shoulder_x=0.192, hip_x=0.1)
PALETTE = "paul_david"
CLIPS_ONLY = ["idle", "idle_look", "interact_talk", "walk", "run", "idle_1h", "sword_1", "sword_2", "sword_heavy",
              "hit_heavy", "cs_pd_idle", "cs_pd_shard", "cs_pd_hand", "cs_pd_gesture", "cs_pd_branded", "cs_pd_ready",
              "cs_pd_reach", "cs_pd_look"]
PREVIEW_HEIGHT = 1.95

PALETTE_COLORS = {
    "BH_Cloth_Primary": LK.mat((0.07, 0.11, 0.2), 0.0, 0.88),
    "BH_Cloth_Secondary": LK.mat((0.06, 0.06, 0.07), 0.0, 0.9),
    "BH_Silver": LK.mat((0.72, 0.74, 0.78), 1.0, 0.3),
    "BH_Steel": LK.mat((0.55, 0.56, 0.6), 1.0, 0.32),
    "BH_Hilt": LK.mat((0.72, 0.74, 0.78), 1.0, 0.3),
    "BH_Mail": LK.mat((0.4, 0.4, 0.42), 1.0, 0.45),
    "BH_Leather": LK.mat((0.12, 0.07, 0.04), 0.0, 0.6),
    "BH_Skin": LK.mat((0.52, 0.35, 0.26), 0.0, 0.55),
    "BH_Scar": LK.mat((0.62, 0.42, 0.36), 0.0, 0.45),
    "BH_Hair": LK.mat((0.045, 0.036, 0.03), 0.0, 0.85),
    "BH_Beard": LK.mat((0.19, 0.175, 0.165), 0.0, 0.65),
    "BH_EyeWhite": LK.mat((0.78, 0.76, 0.72), 0.0, 0.25),
    "BH_Iris": LK.mat((0.1, 0.16, 0.2), 0.0, 0.15),
    "BH_Shadow": LK.mat((0.02, 0.012, 0.01), 0.0, 0.8),
    "BH_Lip": LK.mat((0.46, 0.27, 0.22), 0.0, 0.5),
    "BH_Emissive": LK.mat((0.4, 0.75, 1.0), 0.0, 0.3, (0.35, 0.75, 1.0), 5.0),
    "BH_Brand": LK.mat((0.35, 0.12, 0.6), 0.0, 0.4, (0.55, 0.2, 1.0), 3.0),
}

TORSO = K.torso_rows(chest=1.04, waist=0.94, hip=1.0, depth=1.02, shoulder=1.02)
COAT_G = 0.024


def finish_mesh(ob):
    LK.finish_mesh(ob)


def build(body):
    k = Kit(body)
    rows = TORSO
    # ---- mail and brigandine under the coat
    K.body_shell(k, rows, 0.96, 1.535, "BH_Mail", g=0.004, n=26, cap1=True, name="hauberk")
    V, F = torso_loft(K.grow(K.rows_span(rows, 1.1, 1.49), 0.014), n=28)
    k.add(M.bevel(P_(V, F, "BH_Leather", "brigandine"), 0.003, 1), w=k.zw([(1.18, "spine"), (1.3, "chest")]))
    for z in (1.16, 1.24, 1.32, 1.40, 1.46):
        for x in (-0.07, -0.035, 0.035, 0.07):
            V, F = M.sphere(0.006, 6, 4, center=LK.on_front(rows, x, z, 0.016))
            k.add(P_(V, F, "BH_Silver", "rivet"), w=k.zw([(1.18, "spine"), (1.3, "chest")]))
    coat(k, rows)
    # ---- belt, sword, pouches
    K.band(k, rows, 1.02, 1.065, "BH_Leather", g_out=COAT_G + 0.018, g_in=COAT_G, n=28)
    by = front_y(rows, 0, 1.043) - COAT_G - 0.022
    V, F = M.box(0.055, 0.014, 0.05, center=(0, by, 1.043))
    k.add(M.bevel(P_(V, F, "BH_Silver", "buckle"), 0.005, 1), "hips")
    sword(k, rows)
    for frac in (0.62, 0.7):
        q, ang = K.on_ring(rows, 1.0, COAT_G + 0.03, frac)
        for prt in K.pouch(q, ang, (0.065, 0.035, 0.07)):
            k.add(prt, "hips")
    pauldron(k, body)
    # ---- arms: coat sleeves, bracers, gloves; the brand on the right hand
    for s in "LR":
        K.sleeve(k, s, K.SHOULDER_CAP + [(0.5, 0.058, 0.06), (1.0, 0.052, 0.054), (1.5, 0.047, 0.048)],
                 "BH_Cloth_Primary", n=12)
        K.sleeve(k, s, [(1.45, 0.05, 0.051), (1.6, 0.047, 0.048), (1.92, 0.04, 0.041)], "BH_Leather", n=12, name="bracer")
        for t in (1.55, 1.85):
            K.arm_ring(k, s, t, 0.051, 0.02, "BH_Silver", name="bracer_band")
        K.mitten(k, s, mat="BH_Leather", size=1.05, curl=1.3)
        K.arm_ring(k, s, 1.98, 0.042, 0.05, "BH_Leather", name="glove_cuff", bone="hand." + s)
    brand(k, body)
    # ---- legs: breeches, knee cops, tall boots
    K.trousers(k, "BH_Cloth_Secondary", knee_r=0.052, ankle_r=0.044, t_end=1.6, n=12)
    K.shoes(k, "BH_Leather", sole="BH_Leather", shaft=0.4, shaft_r=0.052, width=1.0)
    for s in "LR":
        b = k.b
        kn = b.head("shin." + s)
        V, F = dome(kn + (0, -0.05, 0.02), (0, -1, 0.2), 0.05, a_max=70, n=12, rings=4)
        b.add(M.solidify(P_(V, F, "BH_Steel", "knee"), 0.005, offset=-1),
              weights=lambda V, s=s: [{"thigh." + s: 0.4, "shin." + s: 0.6}] * len(V))
    # ---- head
    face(k, body)


# ------------------------------------------------------------------------------------------------------------ coat
def coat(k, rows):
    zs = [0.98, 1.06, 1.14, 1.22, 1.30, 1.37, 1.43, 1.475, 1.51, 1.535]
    nu = 26
    rings = []
    for z in zs:
        t = (z - 0.98) / 0.555
        a0 = 0.055 + 0.075 * t ** 1.3
        fr = a0 + (1 - 2 * a0) * np.linspace(0, 1, nu)
        rings.append(ring_frac(rows, z, COAT_G, fr))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Primary", "coat"), 0.009, offset=1.0), w=k.torso_w())
    top = rings[-1]
    V, F = M.tube(top + np.array([0, 0.004, 0.018]), [(0.014, 0.03)] * len(top), n=6, up=(0, 0, 1))
    k.add(P_(V, F, "BH_Cloth_Primary", "collar"), "chest")
    V, F = M.tube(top + np.array([0, 0.004, 0.048]), [(0.004, 0.004)] * len(top), n=5, up=(0, 0, 1))
    k.add(P_(V, F, "BH_Silver", "collar_trim"), "chest")
    for kk in (0, -1):
        pts = np.array([r[kk] for r in rings]) + np.array([0, -0.007, 0])
        V, F = M.tube(pts, [(0.013, 0.005)] * len(pts), n=6, up=(0, -1, 0), p=3.0)
        k.add(P_(V, F, "BH_Silver", "lapel"), w=k.torso_w())
    # silver toggles down the left lapel
    for z in (1.2, 1.28, 1.36, 1.44):
        q = ring_frac(rows, z, COAT_G + 0.01, [0.055 + 0.075 * ((z - 0.98) / 0.555) ** 1.3])[0]
        V, F = M.sphere(0.009, 8, 5, center=q, scale=(1.4, 0.7, 0.8))
        k.add(P_(V, F, "BH_Silver", "toggle"), w=k.torso_w())
    # the skirt: split at the front and at a back vent, to below the knee
    r0 = interp_rows(rows, 1.0)
    g = COAT_G
    sk_rows = K.flare_rows(1.0, 0.36, (r0[1] + g, r0[2] + g, r0[3] + g), (0.26, 0.22, 0.25), n=7)
    for lo, hi in ((0.07, 0.48), (0.52, 0.93)):
        fr = np.linspace(lo, hi, 13)
        rr = []
        for r in sorted(sk_rows, key=lambda r: r[0]):
            pts = ring_frac(sk_rows, r[0], 0.0, fr, p=2.2)
            t = (1.0 - r[0]) / 0.64
            fold = 0.012 * t * np.sin(fr * 2 * math.pi * 7)
            rad = K.normalize_rows(pts[:, :2])
            pts[:, 0] += rad[:, 0] * fold
            pts[:, 1] += rad[:, 1] * fold
            rr.append(pts)
        V, F = M.loft(rr, cap0=False, cap1=False, closed=False)
        k.add(M.solidify(P_(V, F, "BH_Cloth_Primary", "coat_skirt"), 0.009, offset=-1.0), w=k.skirt_w(1.0, 0.5, max_leg=0.85))
        hem = rr[0] + np.array([0, 0, 0.012])
        V, F = M.tube(hem, [(0.006, 0.01)] * len(hem), n=6, up=(0, 0, 1), p=3.0)
        k.add(P_(V, F, "BH_Silver", "hem"), w=k.skirt_w(1.0, 0.5, max_leg=0.85))
        for edge in (0, -1):
            pts = np.array([r[edge] for r in rr])
            V, F = M.tube(pts, [(0.006, 0.008)] * len(pts), n=5, up=(0, 0, 1), p=3.0)
            k.add(P_(V, F, "BH_Silver", "skirt_edge"), w=k.skirt_w(1.0, 0.5, max_leg=0.85))


def sword(k, rows):
    """Stormwake sheathed on the left hip: hilt (BH_Hilt, hidden by the game when drawn) forward-up, scabbard down-back."""
    g = np.array([0.185, -0.075, 1.0])
    d = normalize(np.array([0.05, 0.45, -0.9]))
    side = normalize(np.cross(d, np.array([1.0, 0, 0])))
    L = 0.98
    tip = g + d * L
    V, F = M.tube([g, g + d * 0.5, tip - d * 0.08, tip], [(0.03, 0.013), (0.028, 0.012), (0.022, 0.011), (0.008, 0.006)],
                  n=8, up=(1, 0, 0), p=2.6)
    k.add(P_(V, F, "BH_Cloth_Secondary", "scabbard"), "hips")
    for t in (0.0, 0.3, L - 0.07):
        c = g + d * t
        V, F = M.tube([c - d * 0.015, c + d * 0.015], [(0.033, 0.016)] * 2, n=8, up=(1, 0, 0), p=2.6)
        k.add(P_(V, F, "BH_Silver", "fitting"), "hips")
    # the hilt, exactly where the Stormwake GLB's guard would sit
    for sx in (1, -1):
        V, F = M.tube([g, g + side * sx * 0.1 - d * 0.03], [(0.012, 0.01), (0.005, 0.005)], n=6, up=tuple(d))
        k.add(P_(V, F, "BH_Hilt", "guard"), "hips")
    V, F = M.tube([g - d * 0.01, g - d * 0.2], [(0.019, 0.019), (0.018, 0.018)], n=8, up=(1, 0, 0))
    k.add(P_(V, F, "BH_Hilt", "grip"), "hips")
    V, F = M.sphere(0.026, 8, 6, center=g - d * 0.225)
    k.add(P_(V, F, "BH_Hilt", "pommel"), "hips")
    q = np.array([0.17, -0.03, 1.04])
    k.add(rope([q, g + d * 0.06 + np.array([0.02, 0, 0])], 0.006, "BH_Leather"), "hips")
    q2 = np.array([0.18, 0.08, 1.04])
    k.add(rope([q2, g + d * 0.26 + np.array([0.02, 0, 0])], 0.006, "BH_Leather"), "hips")


def pauldron(k, body):
    """One old steel pauldron on the left shoulder, strapped across the chest."""
    s = "L"
    sh = body.head("upper_arm." + s)
    axis = normalize(np.array([0.7, 0.0, 0.85]))
    c = sh + np.array([0.01, 0.0, 0.012])
    V, F = dome(c, axis, 0.12, a_max=76, n=18, rings=6, scale=(1.0, 1.12, 1.0))
    body.add(M.solidify(P_(V, F, "BH_Steel", "pauldron"), 0.008, offset=-1, bevel_w=0.003), "upper_arm.L")
    Rm = M_align_z(axis, (0, 0, 1))
    rim = [c + Rm @ np.array([0.12 * math.sin(math.radians(76)) * math.cos(a), 0.12 * math.sin(math.radians(76)) * math.sin(a) * 1.12,
                              0.12 * math.cos(math.radians(76))]) for a in np.linspace(0, 2 * math.pi, 29)]
    V, F = M.tube(rim, [(0.006, 0.006)] * 29, n=5, up=tuple(axis), cap0=False, cap1=False)
    body.add(P_(V, F, "BH_Silver", "pauldron_rim"), "upper_arm.L")
    # strap across the chest to the right armpit
    pts = []
    for t in np.linspace(0, 1, 8):
        x = 0.17 - 0.3 * t
        z = 1.45 - 0.18 * t
        pts.append((x, front_y(TORSO, x * 0.97, z) - COAT_G - 0.012, z))
    V, F = M.tube(pts, [(0.018, 0.005)] * 8, n=6, up=(0, -1, 0), p=3.0)
    k.add(P_(V, F, "BH_Leather", "strap"), w=k.zw([(1.22, "spine"), (1.3, "chest")]), std=False)


def brand(k, body):
    """Kethrax's chain-brand: violet links burned round the right wrist and across the back of the glove."""
    b = body
    fa, ha = "forearm.R", "hand.R"
    wr = b.head(ha)
    el = b.head(fa)
    d = normalize(wr - el)
    side = normalize(np.cross(d, (0, 1, 0)))
    up = np.cross(side, d)
    for t, (a0, a1) in ((0.0, (0, 360)), (-0.03, (0, 360))):
        c = wr + d * t
        for i in range(9):
            a = math.radians(a0 + (a1 - a0) * i / 9 + (20 if t else 0))
            n = side * math.cos(a) + up * math.sin(a)
            q = c + n * 0.049
            ring = K.ring_pts(q, 0.008, n if i % 2 else d, n=8)
            V, F = M.tube(ring, [(0.0022, 0.0022)] * len(ring), n=4, up=tuple(d), cap0=False, cap1=False)
            b.add(P_(V, F, "BH_Brand", "brand_link"), fa if t < 0 else ha)
    # a chain of links down the back of the hand
    A = b.axes(ha)
    o = b.head(ha)
    for i in range(4):
        q = o + A @ np.array([0.0, 0.02 + 0.022 * i, -0.019 if False else 0.0]) + A @ np.array([0, 0, 0.0])
        q = b.lpt(ha, [(0.0, 0.025 + 0.02 * i, 0.021)])[0]
        ring = K.ring_pts(q, 0.008, A[:, 0] if i % 2 else A[:, 2], n=8)
        V, F = M.tube(ring, [(0.0022, 0.0022)] * len(ring), n=4, up=tuple(A[:, 1]), cap0=False, cap1=False)
        b.add(P_(V, F, "BH_Brand", "brand_link"), ha)


# ------------------------------------------------------------------------------------------------------------ face
HC = np.array((0.0, -0.004, 1.702))
HR = np.array((0.073, 0.093, 0.116))


def _g(a, b):
    return math.exp(-a * a - b * b)


def head_point(X, Y, Z, grow=0.0):
    """Sculpted head surface at unit direction (X, Y, Z) (-Y = face), grown outward by `grow` metres."""
    x, y, z = X * HR[0], Y * HR[1], Z * HR[2]
    front = max(0.0, -Y)
    ax = abs(X)
    s = 1.0 if X >= 0 else -1.0
    # jaw: narrower toward the chin, the lower back of the skull tucks into the neck
    tj = float(smoothstep(0.0, -0.95, Z))
    x *= 1 - 0.3 * tj
    y -= HR[1] * 0.45 * max(0.0, Y) * float(smoothstep(-0.2, -0.9, Z))
    # a fuller cranium behind and above
    cr = float(smoothstep(0.0, 0.6, Z)) * float(smoothstep(-0.3, 0.3, Y))
    x *= 1 + 0.05 * cr
    y *= 1 + 0.06 * cr
    # flatter face, planes at the sides
    y += 0.02 * front * float(smoothstep(0.35, 0.85, ax))
    # eye sockets, brow ridge, cheekbones, muzzle, chin, temples
    y += 0.0095 * front * _g((ax - 0.39) / 0.16, (Z - 0.1) / 0.11)
    y -= 0.0085 * front * _g((ax - 0.33) / 0.36, (Z - 0.27) / 0.07)
    cb = front * _g((ax - 0.62) / 0.15, (Z + 0.08) / 0.12)
    y -= 0.005 * cb
    x += s * 0.004 * cb
    y -= 0.009 * front * _g(X / 0.36, (Z + 0.45) / 0.2)
    ch = front * _g(X / 0.28, (Z + 0.82) / 0.13)
    y -= 0.012 * ch
    x -= s * 0.004 * _g((ax - 0.82) / 0.14, (Z - 0.18) / 0.2)
    p = HC + np.array([x, y, z])
    if grow:
        d = normalize(np.array([X / HR[0], Y / HR[1], Z / HR[2]]))
        p = p + d * grow
    return p


def unit_dir(th, ph):
    """th: angle round the head from the face (0) toward its left (+X); ph: elevation (-90..90 deg)."""
    t, p = math.radians(th), math.radians(ph)
    return math.cos(p) * math.sin(t), -math.cos(p) * math.cos(t), math.sin(p)


def face(k, body):
    add = lambda p: body.add(p, "head")
    # neck
    V, F = M.tube([(0, 0.004, 1.47), (0, 0.0, 1.54), (0, -0.004, 1.61)], [(0.064, 0.06), (0.06, 0.058), (0.058, 0.058)],
                  n=14, up=(0, -1, 0))
    body.add(P_(V, F, "BH_Skin", "neck"), weights=k.head_w())
    # skull + face
    nu, nv = 40, 28
    rings = []
    for j in range(1, nv):
        ph = -90 + 180 * j / nv
        rings.append(np.array([head_point(*unit_dir(360 * i / nu, ph)) for i in range(nu)]))
    rings = [r[::-1] for r in rings]
    V, F = M.loft(rings, cap0=True, cap1=True)
    add(outward(M.subsurf(P_(V, F, "BH_Skin", "head"), 1)))
    # eyes: whites, irises, pupils, upper lids
    for sx in (1, -1):
        X = 0.39
        f = head_point(sx * X, -math.sqrt(1 - X * X - 0.01), 0.1)
        c = f + np.array([0, 0.0095, 0.0])
        add(LK.gem(c, 0.0118, "BH_EyeWhite", scale=(1, 1, 1), name="eye"))
        add(LK.gem(c + np.array([0, -0.0105, 0.0005]), 0.0058, "BH_Iris", scale=(1, 0.35, 1), name="iris"))
        add(LK.gem(c + np.array([0, -0.0122, 0.0005]), 0.0026, "BH_Shadow", scale=(1, 0.3, 1), name="pupil"))
        lid = [c + np.array([sx * dx, -0.0118 * math.cos(dx / 0.014) - 0.001, 0.007 - 0.004 * (dx / 0.014) ** 2])
               for dx in np.linspace(-0.013, 0.013, 7)]
        V, F = M.tube(lid, [(0.003, 0.0022)] * 7, n=6, up=(0, -0.3, 1))
        add(P_(V, F, "BH_Skin", "lid"))
        low = [c + np.array([sx * dx, -0.0112 * math.cos(dx / 0.015), -0.0085 + 0.003 * (dx / 0.013) ** 2])
               for dx in np.linspace(-0.012, 0.012, 6)]
        V, F = M.tube(low, [(0.0018, 0.0016)] * 6, n=5, up=(0, -0.3, -1))
        add(P_(V, F, "BH_Skin", "lower_lid"))
        # brows: grey, heavy, a little knitted
        brow = [head_point(sx * x, -math.sqrt(max(0.05, 1 - x * x - z * z)), z, 0.002) for x, z in
                ((0.12, 0.25), (0.3, 0.29), (0.5, 0.28), (0.66, 0.22))]
        V, F = M.tube(brow, [(0.0055, 0.004), (0.0065, 0.0042), (0.0055, 0.0038), (0.003, 0.003)], n=6, up=(0, -0.2, 1))
        add(P_(V, F, "BH_Beard", "brow"))
    # nose: bridge, tip, nostril wings
    top = head_point(0, -0.97, 0.16)
    tip = top + np.array([0, -0.02, -0.04])
    base = top + np.array([0, -0.008, -0.052])
    V, F = M.tube([top + np.array([0, 0.004, 0.01]), top + np.array([0, -0.008, -0.012]), top + np.array([0, -0.018, -0.03]),
                   tip, base], [(0.0055, 0.005), (0.006, 0.006), (0.0075, 0.0075), (0.0095, 0.0085), (0.007, 0.005)],
                  n=10, up=(0, -1, 0))
    add(outward(M.subsurf(P_(V, F, "BH_Skin", "nose"), 1)))
    for sx in (1, -1):
        add(LK.gem(base + np.array([sx * 0.0125, 0.006, 0.004]), 0.0075, "BH_Skin", scale=(1.0, 1.1, 0.8), name="nostril"))
        add(LK.gem(base + np.array([sx * 0.006, -0.002, -0.001]), 0.0025, "BH_Shadow", scale=(1.2, 1, 0.6), name="nostril_hole"))
    # mouth: lips and the line between
    zm = -0.47
    mouth_y = head_point(0, -0.88, zm)[1]
    upper = [np.array((x, mouth_y - 0.004 + 60 * x * x, HC[2] + zm * HR[2] + 0.004)) for x in np.linspace(-0.022, 0.022, 7)]
    V, F = M.tube(upper, [(0.0035, 0.0028)] * 7, n=6, up=(0, -0.4, 1))
    add(P_(V, F, "BH_Lip", "lip_upper"))
    lower = [np.array((x, mouth_y - 0.002 + 50 * x * x, HC[2] + zm * HR[2] - 0.0045)) for x in np.linspace(-0.018, 0.018, 6)]
    V, F = M.tube(lower, [(0.004, 0.0034)] * 6, n=6, up=(0, -0.4, -1))
    add(P_(V, F, "BH_Lip", "lip_lower"))
    line = [np.array((x, mouth_y - 0.001 + 55 * x * x, HC[2] + zm * HR[2])) for x in np.linspace(-0.023, 0.023, 7)]
    V, F = M.tube(line, [(0.0016, 0.0012)] * 7, n=4, up=(0, -0.4, 1))
    add(P_(V, F, "BH_Shadow", "mouth"))
    # ears
    for sx in (1, -1):
        c = head_point(sx * 1.0, 0.05, 0.02) + np.array([sx * 0.004, 0.004, 0.0])
        V, F = M.sphere(0.026, 10, 7, center=c, scale=(0.3, 0.62, 1.0))
        add(outward(P_(V, F, "BH_Skin", "ear")))
        rim = [c + np.array([sx * 0.006, 0.016 * math.sin(a), 0.024 * math.cos(a)]) for a in np.linspace(-0.3, 3.6, 9)]
        V, F = M.tube(rim, [(0.0035, 0.0035)] * 9, n=5, up=(sx, 0, 0))
        add(P_(V, F, "BH_Skin", "ear_rim"))
    # the scar: forehead, through the left brow, down the cheek
    scar = [head_point(x, -math.sqrt(max(0.05, 1 - x * x - z * z)), z, 0.0012) for x, z in
            ((0.3, 0.45), (0.36, 0.33), (0.47, 0.22), (0.53, 0.0), (0.56, -0.18), (0.55, -0.32))]
    V, F = M.tube(scar, [(0.0018, 0.0014)] * 6, n=5, up=(0, -1, 0))
    add(P_(V, F, "BH_Scar", "scar"))
    hair(k, body)
    beard(k, body)


def hair(k, body):
    """Swept-back hair (dark, grey at the temples) from a receding hairline, tied at the nape in a short tail."""
    add = lambda p: body.add(p, "head")
    nu, nv = 36, 9
    rings = []
    for j in range(nv):
        v = j / (nv - 1)
        ring = []
        for i in range(nu):
            th = 360 * i / nu
            c = math.cos(math.radians(th))
            # hairline elevation: forehead 38 deg, temples 20, over the ears 12, nape -30
            line = 38 * max(c, 0) ** 1.5 + (20 if c > -0.2 else 12) * (1 - abs(c)) + (-30 * (-c) ** 1.2 if c < 0 else 0)
            line = max(line, -30)
            ph = line + (88 - line) * v ** 0.9
            gr = 0.0012 + 0.0075 * v ** 0.45 + 0.004 * (c < 0) * v + 0.003 * abs(math.sin(math.radians(th) * 13)) * v ** 0.5
            ring.append(head_point(*unit_dir(th, ph), grow=gr))
        rings.append(np.array(ring)[::-1])
    V, F = M.loft(rings, cap0=False, cap1=False)
    add(outward(M.solidify(P_(V, F, "BH_Hair", "hair"), 0.005, offset=-1.0)))
    # the tie and a short tail at the nape
    n0 = head_point(*unit_dir(180, 5), grow=0.012)
    V, F = M.tube([n0 + np.array([0, -0.004, 0.0]), n0 + np.array([0, 0.012, -0.012])], [(0.017, 0.016)] * 2, n=10, up=(0, 0, 1))
    add(outward(P_(V, F, "BH_Leather", "tie")))
    tail = [n0 + np.array([0, 0.01, -0.01]), n0 + np.array([0, 0.028, -0.05]), n0 + np.array([0, 0.03, -0.1]),
            n0 + np.array([0, 0.024, -0.14])]
    V, F = M.tube(tail, [(0.016, 0.013), (0.015, 0.012), (0.011, 0.009), (0.003, 0.003)], n=8, up=(0, 1, 0))
    body.add(outward(P_(V, F, "BH_Hair", "tail")), weights=lambda V: [({"head": 1.0} if v[2] > 1.62 else {"head": 0.5, "neck": 0.5})
                                                                      for v in V])


def beard(k, body):
    """Short grey beard along the jaw and chin, a moustache framing the mouth."""
    add = lambda p: body.add(p, "head")
    nu, nv = 25, 7
    rings = []
    for j in range(nv):
        v = j / (nv - 1)
        ring = []
        for i in range(nu):
            th = -102 + 204 * i / (nu - 1)
            c = math.cos(math.radians(th))
            top = -2 - 40 * c ** 3                      # cheek line at the sides, below the lower lip in front
            bot = -76 + 10 * (1 - c)
            ph = top + (bot - top) * v
            ring.append(head_point(*unit_dir(th, ph), grow=0.002 + 0.01 * math.sin(math.pi * min(1.0, v * 1.4)) ** 0.7 + 0.005 * c * v + 0.0025 * abs(math.sin(math.radians(th) * 11)) * v))
        rings.append(np.array(ring))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    add(outward(M.solidify(P_(V, F, "BH_Beard", "beard"), 0.004, offset=-1.0)))
    zm = HC[2] - 0.47 * HR[2]
    y = head_point(0, -0.88, -0.47)[1]
    for sx in (1, -1):
        pts = [np.array((0.0, y - 0.006, zm + 0.011)), np.array((sx * 0.014, y - 0.005, zm + 0.012)),
               np.array((sx * 0.026, y + 0.001, zm + 0.004)), np.array((sx * 0.03, y + 0.004, zm - 0.012)),
               np.array((sx * 0.029, y + 0.005, zm - 0.028))]
        V, F = M.tube(pts, [(0.004, 0.003), (0.0055, 0.004), (0.005, 0.004), (0.004, 0.0035), (0.002, 0.002)], n=6, up=(0, -1, 0))
        add(outward(P_(V, F, "BH_Beard", "moustache")))
