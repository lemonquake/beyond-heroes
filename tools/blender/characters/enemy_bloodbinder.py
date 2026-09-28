"""Bloodbinder (bh-013, Builder A; blood mage that tethers a draining beam to the hero): a tall (~1.9 m) pale, hollow-
cheeked mage with long dark hair falling in two curtains over the chest and red-glowing eyes. Dark crimson robe to
the floor over black, a black waist cincher with silver buckles, and a high stiff black collar lined crimson that
flares up round the back of the head (the silhouette key). A belt and a bandolier (right shoulder to left hip) hung
with glass vials of glowing red blood. The right sleeve is long and black with a crimson flared cuff; the left
sleeve is pushed up to the elbow, the bare pale forearm and open hand traced with red glowing veins. Right hand: a
hooked sickle (weapon.R) with a black-iron crescent blade, a blood groove and a red jewel.

Clips: dagger_1, dagger_2, dagger_heavy, cast_quick, cast_heavy, cast_area (+ the shared enemy base clips).
Robe helpers: enemy_ashen_cultist; kit: enemy_bandit_cutthroat (SB) + kit_a_common + kit_e_orrery."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C
import enemy_hollow_soldier as HS
import kit_a_common as A
import kit_e_orrery as O

SCALE = 1.9 / 1.83
PROPS = proportions(SCALE, shoulder_x=0.168 * SCALE, hip_x=0.09 * SCALE, upper_len=0.295 * SCALE,
                    fore_len=0.28 * SCALE)
PREVIEW_HEIGHT = 2.3
PALETTE = "bloodbinder"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.24, 0.018, 0.03), 0.0, 0.75, None, 0.0, 1.0),      # dark crimson robe
    "BH_Cloth_Secondary": ((0.018, 0.014, 0.016), 0.0, 0.8, None, 0.0, 1.0),   # black under-robe, collar, sleeve
    "BH_Skin": ((0.72, 0.67, 0.66), 0.0, 0.5, None, 0.0, 1.0),                 # corpse-pale
    "BH_Hair": ((0.025, 0.018, 0.02), 0.0, 0.55, None, 0.0, 1.0),              # long dark hair
    "BH_Leather": ((0.04, 0.025, 0.022), 0.0, 0.6, None, 0.0, 1.0),            # belts, bandolier, boots, grip
    "BH_Steel": ((0.72, 0.72, 0.74), 1.0, 0.3, None, 0.0, 1.0),                # silver buckles, vial caps, sickle edge
    "BH_DarkSteel": ((0.08, 0.07, 0.075), 1.0, 0.45, None, 0.0, 1.0),          # sickle blade, fittings
    "BH_Shadow": ((0.03, 0.01, 0.012), 0.0, 0.8, None, 0.0, 1.0),              # sockets, mouth
    "BH_Emissive": ((1.0, 0.08, 0.06), 0.0, 0.4, (1.0, 0.07, 0.05), 10.0, 1.0),  # blood-light: vials, veins, eyes
}
CLIPS = ["dagger_1", "dagger_2", "dagger_heavy", "cast_quick", "cast_heavy", "cast_area"]

TORSO = [(r[0], r[1] * 0.9, r[2] * 0.88, r[3] * 0.92, r[4] * 0.6) for r in K.TORSO]
G = 0.012
CHEST_W = K.zspec_w([(1.2, "spine"), (1.3, "chest")])


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="body"), weights=C.ROBE_W)
    # ---- robes: crimson robe over black, a black under-skirt showing in the front slit
    C.robe_top(sb, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", g=G, rows=TORSO, v_open=0.05)
    C.robe_skirt(sb, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", z_top=1.07, z_bot=0.05, flare=0.16, folds=0.014,
                 front_gap=0.05, g=G - 0.02)
    underskirt(sb)
    cincher(sb)
    bandolier(sb)
    collar(sb)
    head(sb)
    # ---- arms
    C.bell_sleeve(sb, "R", "BH_Cloth_Secondary", trim="BH_Cloth_Primary", cuff_r=0.075, end=0.78)
    K.add_fist(sb, "R", "BH_Skin", "BH_Skin", scale=0.95)
    left_arm(sb)
    # ---- legs (hidden) + boots
    K.trousers(sb, "BH_Cloth_Secondary", loose=0.85)
    K.boots(sb, "BH_Leather", "BH_Leather", shaft_top=0.4, cuff=False)
    # ---- sickle
    K.add_weapon(sb, "R", sickle(SCALE))


# ================================================================================================= robes
def centre_w(leg=0.5):
    base = HS.cloth_w(chest_z=1.3, belt_z=1.03, leg=0.0)

    def wfn(V):
        out = base(V)
        for i, v in enumerate(V):
            if v[2] < 1.0:
                s_ = float(smoothstep(1.0, 0.5, v[2])) * leg
                out[i] = {"hips": 1 - s_, "thigh.L": s_ / 2, "thigh.R": s_ / 2} if s_ > 1e-3 else {"hips": 1.0}
        return out
    return wfn


def underskirt(sb):
    """Black under-skirt panel filling the front slit of the crimson robe."""
    def fn(u, v):
        z = 1.02 + (0.06 - 1.02) * v
        hw = 0.07 + 0.08 * v
        x = (u - 0.5) * 2 * hw
        y = front_y(TORSO, x * 0.6, 1.02) - G + 0.008 - 0.13 * v ** 1.05
        return (x, y, z)
    V, F = M.grid(fn, 5, 10)
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Secondary", name="underskirt"), 0.006, offset=-1.0), weights=centre_w(0.55))


def cincher(sb):
    """Black waist cincher with three silver buckle straps; a belt of blood vials under it."""
    V, F = K.band(TORSO, 0.99, 1.16, G + 0.022, G - 0.004, n=28)
    sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="cincher"), weights=K.zspec_w([(1.02, "hips"), (1.12, "spine")]))
    for z in (1.03, 1.08, 1.13):
        p, _ = K.on_ring(TORSO, z, G + 0.03, 0.0)
        V, F = M.box(0.13, 0.008, 0.014, center=p)
        sb.add(M.Part(V, F, "BH_Leather", name="strap"), "hips" if z < 1.06 else "spine")
        V, F = M.box(0.024, 0.01, 0.022, center=p + np.array([0.0, -0.005, 0.0]))
        sb.add(M.Part(V, F, "BH_Steel", name="buckle"), "hips" if z < 1.06 else "spine")
    # vial belt round the hips
    V, F = K.band(TORSO, 0.955, 0.985, G + 0.036, G + 0.004, n=28)
    sb.add(M.Part(V, F, "BH_Leather", name="vialbelt"), "hips")
    for frac in (0.08, 0.14, 0.2, 0.8, 0.86, 0.92, 0.35, 0.65):
        p, ang = K.on_ring(TORSO, 0.955, G + 0.05, frac)
        out = normalize(np.array([p[0], p[1], 0.0]))
        for prt in vial(p + np.array([0, 0, -0.03]), (0, 0, 1), out, h=0.09, r=0.019):
            sb.add(prt, "hips")


def vial(base, up, out, h=0.06, r=0.012):
    """Glass vial of glowing blood: blood body (emissive), silver cap + collar, leather loop."""
    up = normalize(up)
    b = np.asarray(base, float)
    parts = [O.P(*M.lathe([(0.0, 0.0), (r, 0.006), (r, h * 0.72), (r * 0.55, h * 0.8), (0.0, h * 0.8)], 7),
                 "BH_Emissive", "vial")]
    parts.append(O.P(*M.lathe([(0.0, h * 0.78), (r * 0.62, h * 0.78), (r * 0.62, h), (0.0, h)], 6), "BH_Steel", "cap"))
    for p in parts:
        O.orient(p, b, up, up=out)
    loop = O.ring(b + up * h * 0.45 + normalize(out) * 0.0, up, r + 0.003, 0.003, "BH_Leather", n=8, m=3)
    parts.append(loop)
    return parts


def bandolier(sb):
    """Strap from the right shoulder across the chest to the left hip (and round the back), vials along the front."""
    g = G + 0.028
    pts, ups = [], []
    for t in np.linspace(0, 1, 9):
        x = -0.12 + 0.26 * t
        z = 1.48 - 0.47 * t
        y = front_y(TORSO, x, max(z, 1.0)) - g
        pts.append((x, y, z))
        ups.append((0.2 * x, -1, 0))
    w = K.zspec_w([(1.02, "hips"), (1.12, "spine"), (1.22, "spine"), (1.32, "chest")])
    sb.add(K.strip(pts, 0.045, 0.01, "BH_Leather", ups=ups), weights=w)
    back = [(-0.12 + 0.26 * t, back_y(TORSO, -0.12 + 0.26 * t, max(1.48 - 0.47 * t, 1.0)) + g, 1.48 - 0.47 * t)
            for t in np.linspace(0, 1, 7)]
    sb.add(K.strip(back, 0.045, 0.01, "BH_Leather", ups=[(0, 1, 0)] * 7), weights=w)
    over = []
    for t in np.linspace(0, 1, 7):
        a = math.pi * (0.5 - t) * 0.95
        over.append((-0.12, -0.11 * math.sin(a) + 0.005, 1.47 + 0.05 * math.cos(a)))
    sb.add(K.strip(over, 0.045, 0.01, "BH_Leather", ups=[(0, -math.sin(math.pi * (0.5 - t) * 0.95),
                                                            math.cos(math.pi * (0.5 - t) * 0.95))
                                                        for t in np.linspace(0, 1, 7)]), "chest")
    d = normalize(np.array(pts[0]) - np.array(pts[-1]))
    for t in (0.14, 0.27, 0.4, 0.53, 0.66, 0.79):
        i = t * (len(pts) - 1)
        i0 = int(i)
        c = np.array(pts[i0]) * (1 - (i - i0)) + np.array(pts[min(i0 + 1, 8)]) * (i - i0)
        for prt in vial(c + np.array([0, -0.014, -0.03]), (0.25, 0, 1.0), (0, -1, 0), h=0.082, r=0.017):
            sb.add(prt, weights=w)
    p = np.array(pts[1]) + np.array([0, -0.012, 0])
    sb.add(O.disc(p, (0, -1, 0.2), 0.024, 0.008, "BH_Steel", n=10), "chest")
    sb.add(O.ball(p + np.array([0, -0.006, 0]), 0.011, "BH_Emissive", n=6, rings=4), "chest")


def collar(sb):
    """High stiff collar standing round the back and sides of the head, flaring outward: black outside, crimson
    lining inside, a silver rim; open at the front."""
    zb = 1.47
    nu, nv = 17, 5
    outer, inner = [], []

    def pt(a, v, g=0.0):
        r = math.radians(a)                      # 0 = back (+Y)
        back = math.cos(r)
        h = 0.14 + 0.2 * max(back, 0.0) ** 1.2
        z = zb + h * v
        rad = 0.125 + 0.1 * v ** 1.3 + g
        return np.array([rad * math.sin(r), 0.015 + rad * math.cos(r) * 0.95, z])
    angs = np.linspace(-135, 135, nu)
    V = [pt(a, v) for v in np.linspace(0, 1, nv) for a in angs]
    F = []
    for j in range(nv - 1):
        for i in range(nu - 1):
            F.append((j * nu + i, j * nu + i + 1, (j + 1) * nu + i + 1, (j + 1) * nu + i))
    out = M.Part(np.array(V), F, "BH_Cloth_Secondary", name="collar")
    # decide the outward side from the face normal at the back
    a, b_, c = out.V[F[8][0]], out.V[F[8][1]], out.V[F[8][2]]
    if np.cross(b_ - a, c - a)[1] < 0:
        out.flip()
    lin = M.Part(np.array([pt(a_, v, -0.008) for v in np.linspace(0, 1, nv) for a_ in angs]), list(out.F),
                 "BH_Cloth_Primary", name="collar_lining").flip()
    sb.add(out, "chest")
    sb.add(lin, "chest")
    rim = [pt(a_, 1.0, -0.004) for a_ in angs]
    sb.add(A.tube(rim, (0.007, 0.007), "BH_Steel", n=4, up=(0, 0, 1)), "chest")
    for k in (0, nu - 1):
        edge = [pt(angs[k], v, -0.004) for v in np.linspace(0, 1, nv)]
        sb.add(A.tube(edge, 0.006, "BH_Steel", n=4), "chest")
    # silver clasp chain across the throat
    l, r = pt(-135, 0.1), pt(135, 0.1)
    mid = (l + r) / 2 + np.array([0, -0.03, -0.03])
    sb.add(A.tube([l, mid, r], 0.0035, "BH_Steel", n=4), "chest")
    sb.add(O.ball(mid, 0.012, "BH_Emissive", n=6, rings=4), "chest")


HEAD_ROWS = [(z, rx * 0.93, ryf * 0.98, ryb, kl, cy) for (z, rx, ryf, ryb, kl, cy) in K.HEAD]


def head(sb):
    V, F = M.tube([(0, 0.0, 1.46), (0, -0.004, 1.54), (0, -0.01, 1.62)], [(0.05, 0.048), (0.044, 0.042),
                                                                          (0.046, 0.046)], n=10, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Skin", name="neck"), weights=K.HEAD_W)
    V, F = torso_loft(HEAD_ROWS, n=22, p=2.1, cap0=True, cap1=True)
    hd = M.Part(V, F, "BH_Skin", name="head")

    def hollow(v):
        x, y, z = v
        if y < -0.01 and 1.61 < z < 1.69 and abs(x) > 0.035:
            k = math.sin(math.pi * (z - 1.61) / 0.08) * min(1.0, (abs(x) - 0.035) / 0.03)
            x -= np.sign(x) * 0.011 * k
        return (x, y, z)
    sb.add(hd.warp(hollow), "head")
    parts = [A.tube([(-0.048, -0.058, 1.716), (0.0, -0.07, 1.72), (0.048, -0.058, 1.716)], (0.007, 0.005), "BH_Skin",
                    n=6, up=(0, -1, 0)),
             A.tube([(0, -0.076, 1.712), (0, -0.088, 1.684), (0, -0.094, 1.662), (0, -0.087, 1.652)],
                    [(0.006, 0.006), (0.008, 0.008), (0.011, 0.009), (0.007, 0.005)], "BH_Skin", n=6, up=(0, -1, 0)),
             A.tube([(-0.022, -0.074, 1.624), (0, -0.078, 1.62), (0.022, -0.074, 1.624)], 0.0045, "BH_Shadow", n=4)]
    for sx in (1, -1):
        parts.append(A.ball((sx * 0.029, -0.066, 1.699), 0.015, "BH_Shadow", n=8, rings=5, scale=(1.2, 0.6, 0.75)))
        parts.append(A.ball((sx * 0.029, -0.073, 1.699), 0.0075, "BH_Emissive", n=6, rings=4, scale=(1.3, 0.7, 0.8)))
        parts.append(A.ball((sx * 0.072, 0.0, 1.69), 0.02, "BH_Skin", n=6, rings=4, scale=(0.35, 0.8, 1.2)))
    for p in parts:
        sb.add(p, "head")
    hair(sb)


def hair_cap(sb, g=0.011, z_front=1.755, z_back=1.6):
    """Domed hair cap on the (narrowed) head rows with a centre parting: the hairline dips from the forehead to the
    nape; the top rings close to a rounded crown instead of a flat fan."""
    rows = K.grow_rows(HEAD_ROWS, g)
    nu = 24
    rings = []
    for v in np.linspace(0, 1, 7):
        ring = []
        for i in range(nu):
            f = i / nu
            back = 0.5 - 0.5 * math.cos(2 * math.pi * f)
            z0 = z_front + (z_back - z_front) * back
            z = z0 + (1.812 - z0) * v ** 0.8
            q = K.ring_frac(rows, min(z, 1.812), 0.0, [f], p=2.1)[0]
            q[2] = z
            ring.append(q)
        rings.append(np.array(ring))
    top = rings[-1]
    c = top.mean(0)
    for k, (sc, dz) in enumerate(((0.72, 0.012), (0.38, 0.02))):
        r_ = c + (top - c) * sc
        r_[:, 2] = c[2] + dz
        # centre parting: a slight groove along x = 0
        r_[:, 2] -= 0.004 * np.exp(-(r_[:, 0] / 0.012) ** 2)
        rings.append(r_)
    V, F = M.loft(rings, cap0=False, cap1=True)
    sb.add(M.Part(V, F, "BH_Hair", name="hair"), "head")


def hair(sb):
    """Long dark hair: a cap with a widow's peak, the back hair falling inside the collar, and two long curtains
    falling over the front of the shoulders to the chest."""
    hair_cap(sb)
    wh = K.zspec_w([(1.44, "chest"), (1.56, "neck"), (1.66, "head")])
    # back hair (inside the collar)
    def fn(u, v):
        a = (u - 0.5) * 2
        z = 1.72 - 0.34 * v
        x = a * (0.075 + 0.02 * v)
        y = 0.07 + 0.03 * v - 0.03 * a * a + 0.012 * math.sin(u * 9) * v
        return (x, y, z)
    V, F = M.grid(fn, 7, 6)
    p = M.Part(V, F, "BH_Hair", name="backhair").flip()
    sb.add(M.solidify(p, 0.012, offset=1.0), weights=wh)
    # front curtains: from the temples over the collarbones to the chest
    for sx in (1, -1):
        pts = [(sx * 0.07, -0.03, 1.72), (sx * 0.085, -0.035, 1.62), (sx * 0.1, -0.06, 1.52), (sx * 0.11, -0.1, 1.42),
               (sx * 0.11, -0.12, 1.3), (sx * 0.1, -0.125, 1.2)]
        V, F = M.tube(pts, [(0.03, 0.012), (0.035, 0.014), (0.04, 0.016), (0.04, 0.015), (0.035, 0.012),
                            (0.02, 0.006)], n=6, up=(0, -1, 0))
        sb.add(M.Part(V, F, "BH_Hair", name="curtain"), weights=wh)


# ================================================================================================= arms
def left_arm(sb):
    """Black sleeve pushed up to the elbow (crimson roll), the bare pale forearm and open hand traced with glowing
    red veins."""
    s = "L"
    ua, fa, ha = "upper_arm.L", "forearm.L", "hand.L"
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    K.bare_arm(sb, s, r_up=0.046, r_fore=0.038, r_wrist=0.029)
    pts = [sh + (-0.04, 0, 0.025), sh, sh + (el - sh) * 0.5, el + (el - sh) * 0.06]
    prof = [(0.052, 0.056), (0.064, 0.066), (0.06, 0.062), (0.058, 0.06)]
    V, F = M.tube(pts, prof, n=12, up=(0, -1, 0), cap1=False)
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Secondary", name="sleeve"), 0.006, offset=-1.0),
           weights=sb.seg(["chest", "shoulder.L", ua, fa], power=9))
    c = el + (el - sh) * 0.05
    sb.add(O.ring(c, el - sh, 0.058, 0.014, "BH_Cloth_Primary", n=12, m=5), weights=sb.seg([ua, fa], power=9))
    for prt in A.open_palm(sb.b, s, "BH_Skin", s=SCALE * 0.95):
        sb.add_real(prt, ha)
    for prt in A.bony_fingers(sb.b, s, "BH_Skin", length=0.09 * SCALE, r=0.0068 * SCALE, curl=0.6, spread=1.1,
                              open_hand=True, nails="BH_Shadow"):
        sb.add_real(prt, ha)
    # veins: branching lines on the forearm surface (forearm bone) running into the hand
    d = normalize(wr - el)
    side = normalize(np.cross(d, (0, 1, 0)))
    fw = np.cross(side, d)
    rng = np.random.default_rng(5)
    for k, a0 in enumerate((200, 250, 300, 20)):
        pts = []
        for i in range(7):
            u = 0.15 + 0.85 * i / 6
            a = math.radians(a0 + 25 * math.sin(u * 7 + k))
            nr = side * math.cos(a) + fw * math.sin(a)
            r = 0.041 - 0.011 * u
            pts.append(el + (wr - el) * u + nr * (r + 0.002))
        sb.add(A.tube(pts, (0.0035, 0.0022), "BH_Emissive", n=3), fa)
        j = 2 + k % 3
        a = math.radians(a0 + 40)
        nr = side * math.cos(a) + fw * math.sin(a)
        br = [pts[j], el + (wr - el) * (0.15 + 0.85 * (j + 1.2) / 6) + nr * 0.036]
        sb.add(A.tube(br, (0.0028, 0.002), "BH_Emissive", n=3), fa)
    # veins over the back of the hand
    L_, Ah = A.hand_frame(sb.b, "L")
    for y in (-0.025, 0.0, 0.025):
        pts = [L_(-0.07 * SCALE, y * 0.4 * SCALE, 0.022 * SCALE), L_(-0.03 * SCALE, y * 0.8 * SCALE, 0.024 * SCALE),
               L_(0.015 * SCALE, y * SCALE, 0.02 * SCALE)]
        sb.add_real(A.tube(pts, (0.0035, 0.0022), "BH_Emissive", n=3), ha)


# ================================================================================================= weapon
def sickle(s=1.0):
    """Hooked sickle (weapon space: grip at origin, +Z = up the handle, knuckle side +X): wrapped wooden-black grip,
    a black-iron crescent blade sweeping forward (+X) and hooking back down, a silver inner edge, a glowing blood
    groove and a red jewel in the pommel."""
    parts = []
    parts.append(A.lathe_part([(0.0, -0.11), (0.02, -0.105), (0.019, 0.0), (0.017, 0.12), (0.0, 0.125)], "BH_Leather",
                              n=8))
    for z in (-0.06, 0.0, 0.06):
        parts.append(A.lathe_part([(0.0, z - 0.006), (0.021, z - 0.006), (0.021, z + 0.006), (0.0, z + 0.006)],
                                  "BH_DarkSteel", n=8))
    parts.append(A.lathe_part([(0.0, -0.14), (0.018, -0.13), (0.024, -0.115), (0.02, -0.1), (0.0, -0.1)],
                              "BH_DarkSteel", n=8))
    parts.append(A.ball((0, 0, -0.145), 0.013, "BH_Emissive", n=6, rings=4))
    parts.append(A.lathe_part([(0.0, 0.1), (0.024, 0.1), (0.028, 0.13), (0.02, 0.15), (0.0, 0.15)], "BH_DarkSteel",
                              n=8))
    # crescent: centre of the arc ahead of the handle top; spine outside, edge inside
    cx, cz, R = 0.11, 0.2, 0.13
    rings_b, edge_pts, groove = [], [], []
    n = 14
    for i in range(n + 1):
        t = i / n
        ang = math.radians(170 - 250 * t)        # from behind the top, over, forward and down (hook)
        rr = R * (1 - 0.18 * t)
        cxy = np.array([cx + rr * math.cos(ang), cz + rr * math.sin(ang)])
        nrm = np.array([math.cos(ang), math.sin(ang)])       # outward = spine
        wdt = 0.05 * (1 - t ** 1.5) + 0.004
        th = 0.007 * (1 - 0.6 * t) + 0.0015
        spine = cxy + nrm * wdt * 0.5
        edge = cxy - nrm * wdt * 0.5
        mid = cxy
        rings_b.append(np.array([(spine[0], th, spine[1]), (mid[0], th * 1.1, mid[1]), (edge[0], 0.0005, edge[1]),
                                 (mid[0], -th * 1.1, mid[1]), (spine[0], -th, spine[1])]))
        edge_pts.append((edge[0], 0.0, edge[1]))
        groove.append(cxy + nrm * wdt * 0.12)
    V, F = M.loft(rings_b)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="crescent"))
    ep = np.array(edge_pts[1:-1])
    parts.append(A.tube(ep, (0.0035, 0.0018), "BH_Steel", n=4, up=(0, 1, 0)))
    for sy in (1, -1):
        g = np.array([(q[0], sy * 0.0075, q[1]) for q in groove[2:-3]])
        parts.append(A.tube(g, (0.004, 0.0012), "BH_Emissive", n=4, up=(0, sy, 0)))
    # socket joining the blade root to the handle top
    parts.append(A.tube([(0.0, 0.0, 0.14), (0.0, 0.0, 0.2), (-0.01, 0.0, 0.23)], 0.016, "BH_DarkSteel", n=6))
    for p in parts:
        p.V = p.V * s
    return parts
