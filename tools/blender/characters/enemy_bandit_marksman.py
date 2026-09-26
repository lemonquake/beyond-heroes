"""Bandit Marksman (bandits): archer in a wide-brim leather hat, green-brown hooded cape (hood down, bunched behind the
neck, cape on cape.1/cape.2 bones), dull tunic, leather bracer on the bow arm, a recurve bow in the left hand and an
arrow quiver on the right hip. Uses the Builder-B kit from enemy_bandit_cutthroat."""
import math
import numpy as np

import bh_mesh as M
import bh_weapons as WP
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
from char_knight import secondary as _cape_secondary
import enemy_bandit_cutthroat as K

SCALE = 1.75 / 1.87          # the hat crown tops out at ~1.87 standard units
PROPS = proportions(SCALE)
PALETTE = "bandit_marksman"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.075, 0.085, 0.04), 0.0, 0.9, None, 0.0, 1.0),     # green-brown cape / hood
    "BH_Cloth_Secondary": ((0.13, 0.095, 0.06), 0.0, 0.9, None, 0.0, 1.0),    # dull tunic
    "BH_Leather": ((0.11, 0.065, 0.035), 0.0, 0.62, None, 0.0, 1.0),          # hat, bracer, quiver, boots
    "BH_Horn": ((0.2, 0.13, 0.07), 0.0, 0.66, None, 0.0, 1.0),                # light straps / hat band
    "BH_Fur": ((0.05, 0.05, 0.045), 0.0, 0.9, None, 0.0, 1.0),                # trousers
    "BH_Skin": ((0.5, 0.33, 0.24), 0.0, 0.55, None, 0.0, 1.0),
    "BH_Hair": ((0.05, 0.035, 0.025), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Shadow": ((0.03, 0.024, 0.02), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Wood": ((0.16, 0.09, 0.045), 0.0, 0.65, None, 0.0, 1.0),
    "BH_Bone": ((0.5, 0.47, 0.4), 0.0, 0.7, None, 0.0, 1.0),                  # fletching
    "BH_DarkSteel": ((0.14, 0.14, 0.15), 1.0, 0.5, None, 0.0, 1.0),
    "BH_Gold": ((0.4, 0.3, 0.15), 1.0, 0.45, None, 0.0, 1.0),                 # brass riser bands
}
CLIPS = ["bow_release", "bow_draw_hold"]

EXTRA_BONES = [
    ("cape.1", tuple(np.array((0, 0.15, 1.46)) * SCALE), tuple(np.array((0, 0.19, 1.08)) * SCALE), "chest", (0, -1, 0)),
    ("cape.2", tuple(np.array((0, 0.19, 1.08)) * SCALE), tuple(np.array((0, 0.22, 0.66)) * SCALE), "cape.1", (0, -1, 0)),
]


def secondary(anim, frames):
    return _cape_secondary(anim, frames)


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


TORSO = K.TORSO
TUNIC_G = 0.012


def build(body):
    sb = K.SB(body, SCALE)
    # tunic body + short skirt
    V, F = torso_loft(K.rows_between(TORSO, 0.98, 1.53, g=TUNIC_G), n=24, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="tunic"), weights=K.TORSO_W)
    V, F = torso_loft([(0.80, 0.19, 0.14, 0.14, 0.0), (0.9, 0.172, 0.122, 0.124, 0.0),
                       (1.0, 0.155, 0.108, 0.11, 0.0)], n=24)
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Secondary", name="tunic_skirt"), 0.008, offset=1.0),
           weights=sb.skirt(1.0, 0.8, max_leg=0.75, center_w=0.06))
    K.belt(sb, TORSO, z=1.0, g=TUNIC_G + 0.004, mat="BH_Leather", buckle="BH_Gold")
    # quiver strap across the chest (right shoulder -> left hip), quiver hangs on the right hip
    g = TUNIC_G + 0.012
    pts, ups = [], []
    for t in np.linspace(0, 1, 8):
        x = -0.12 + 0.26 * t
        z = 1.47 - 0.42 * t
        pts.append((x, front_y(TORSO, x, z) - g, z))
        ups.append((0.2 * x, -1, 0))
    sb.add(K.strip(pts, 0.035, 0.008, "BH_Horn", ups=ups), weights=K.TORSO_W)
    quiver(sb)
    K.pouch(sb, TORSO, 0.14, 0.97, TUNIC_G + 0.02, size=(0.07, 0.04, 0.065))
    # head: short beard, hat
    K.neck_and_head(sb)
    K.hair_cap(sb, z_front=1.72, z_back=1.6, g=0.006)
    beard(sb)
    hat(sb)
    hood_and_mantle(sb)
    cape(sb)
    # arms: tunic sleeves, gloves, bracer on the bow arm
    for s in ("L", "R"):
        sleeve(sb, s)
        K.add_fist(sb, s, "BH_Leather", "BH_Leather", gauntlet=True)
    fa, ha = sb.head("forearm.L"), sb.head("hand.L")
    V, F = M.tube([fa + (ha - fa) * 0.35, fa + (ha - fa) * 0.7, fa + (ha - fa) * 1.02],
                  [(0.052, 0.056), (0.05, 0.053), (0.045, 0.048)], n=12, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Leather", name="bracer"), "forearm.L")
    for u in (0.45, 0.8):
        c = fa + (ha - fa) * u
        d = normalize(ha - fa)
        V, F = M.tube([c - d * 0.007, c + d * 0.007], [(0.056, 0.058)] * 2, n=12, up=(0, -1, 0))
        sb.add(M.Part(V, F, "BH_Horn", name="bracer_strap"), "forearm.L")
    # legs
    K.pelvis_seat(sb, "BH_Fur")
    K.trousers(sb, "BH_Fur")
    K.boots(sb, "BH_Leather", "BH_DarkSteel", shaft_top=0.7, wraps="BH_Horn")
    # bow in the left fist (bh_weapons recurve: limbs along +-Z, string on -X)
    K.add_weapon(sb, "L", big_bow())


def big_bow():
    parts = WP.bow()
    for p in parts:
        p.scale((1.0, 1.0, 1.12))
    return parts


def sleeve(sb, s):
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    sx = 1 if s == "L" else -1
    pts = [sh + (-0.04 * sx, 0, 0.025), sh, sh + (el - sh) * 0.5, el, el + (wr - el) * 0.5, wr - (wr - el) * 0.02]
    prof = [(0.05, 0.055), (0.064, 0.066), (0.058, 0.06), (0.052, 0.054), (0.047, 0.049), (0.038, 0.04)]
    V, F = M.tube(pts, prof, n=12, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="sleeve"), weights=sb.seg(["chest", "shoulder." + s, ua, fa, ha],
                                                                             power=9))


def beard(sb):
    rows = []
    w = 0.2
    cols = np.linspace(-w, w, 11)
    for t in np.linspace(0, 1, 4):
        r = []
        for f in cols:
            a = abs(f) / w
            zb = 1.575 + 0.05 * a ** 2
            zt = 1.625 + 0.04 * a ** 1.3
            z = zb + (zt - zb) * t
            q = K.ring_frac(K.HEAD, max(z, 1.60), 0.005, [f], p=2.1)[0]
            q[2] = z
            if z < 1.6:
                q[1] -= (1.6 - z) * 0.3
            r.append(q)
        rows.append(np.array(r))
    V, F = M.loft(rows, cap0=False, cap1=False, closed=False)
    sb.add(M.solidify(M.Part(V, F, "BH_Hair", name="beard"), 0.009, offset=1.0), "head")


def hat(sb):
    """Wide-brim leather hat: brim drooping front/back, dented crown, a light band."""
    cy = 0.0
    brim = []
    n = 28
    for r, zr in ((0.085, 1.765), (0.14, 1.758), (0.2, 1.738), (0.222, 1.728)):
        ring = []
        for i in range(n):
            a = 2 * math.pi * i / n
            ca, sa = math.cos(a), math.sin(a)
            droop = 0.03 * abs(sa) ** 2 * (r - 0.085) / 0.137    # front/back (sin) droop, sides curl up
            curl = 0.012 * ca * ca * (r - 0.085) / 0.137
            ring.append((r * ca, cy + r * 1.05 * sa, zr - droop + curl))
        brim.append(np.array(ring))
    V, F = M.loft(brim, cap0=False, cap1=False)
    p = M.solidify(M.Part(V, F, "BH_Leather", name="brim"), 0.01, offset=-1.0)
    sb.add(p, "head")
    V, F = M.lathe([(0.09, 1.75), (0.092, 1.8), (0.084, 1.84), (0.06, 1.862), (0.02, 1.868), (0.0, 1.866)], 20)
    crown = M.Part(V, F, "BH_Leather", name="crown").scale((1.0, 1.1, 1.0), center=(0, 0, 1.8))
    crown.warp(lambda v: (v[0], v[1], v[2] - 0.018 * max(0, 1 - abs(v[0]) / 0.03) * max(0, (v[2] - 1.83) / 0.04)))
    sb.add(crown, "head")
    V, F = M.lathe([(0.0935, 1.768), (0.0955, 1.773), (0.0955, 1.795), (0.0935, 1.8)], 20, cap=False)
    sb.add(M.Part(V, F, "BH_Horn", name="hatband").scale((1.0, 1.1, 1.0), center=(0, 0, 1.8)), "head")
    # a feather on the band
    pts = [(0.09, 0.03, 1.79), (0.11, 0.07, 1.83), (0.115, 0.12, 1.86)]
    sb.add(K.strip(pts, 0.022, 0.004, "BH_Bone", ups=[(1, 0, 0)] * 3), "head")


def hood_and_mantle(sb):
    # short shoulder mantle (capelet) in cape cloth
    nu, nv = 36, 5
    gap = math.radians(10)
    rings = []
    for j in range(nv):
        v = j / (nv - 1)
        ring = []
        for i in range(nu):
            th = gap + (2 * math.pi - 2 * gap) * i / (nu - 1)
            st, ct = math.sin(th), math.cos(th)
            rx = 0.1 + 0.2 * v
            ry = (0.085 + 0.08 * v) if ct > 0 else (0.09 + 0.1 * v)
            drop = 0.08 + 0.1 * ct * ct
            z = 1.56 - drop * v ** 1.6 - 0.018 * (1 - math.cos(11 * th)) * 0.5 * v ** 3
            ring.append((rx * st, 0.01 - ry * ct, z))
        rings.append(np.array(ring))
    rings = rings[::-1]
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)

    def mantle_w(V):
        out = []
        for v in V:
            s = float(smoothstep(0.13, 0.28, abs(v[0])))
            side = "L" if v[0] > 0 else "R"
            d = {"chest": 1 - 0.5 * s}
            if s > 1e-4:
                d["shoulder." + side] = 0.3 * s
                d["upper_arm." + side] = 0.2 * s
            out.append(d)
        return out
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="mantle"), 0.009, offset=1.0), weights=mantle_w)
    # hood down: a bunched roll of cloth around the back of the neck
    pts = []
    for a in np.linspace(-100, 100, 11):
        r = math.radians(a)
        pts.append((0.1 * math.sin(r), 0.085 * math.cos(r) + 0.02, 1.565 + 0.02 * math.cos(r)))
    V, F = M.tube(pts, [(0.03, 0.03)] + [(0.045, 0.04)] * 9 + [(0.03, 0.03)], n=8, up=(0, 0, 1))
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="hood_roll"), weights=K.NECK_W)
    # the hood's pointed bag lying on the upper back
    def fn(u, v):
        w = 0.1 * (1 - v ** 1.5) + 0.01
        x = (u - 0.5) * 2 * w
        z = 1.56 - 0.2 * v
        y = back_y(TORSO, x, max(z, 1.3)) + 0.06 + 0.02 * math.sin(math.pi * u)
        return (x, y, z)
    sb.add(K.cloth_panel(fn, 7, 5, "BH_Cloth_Primary", thick=0.012), "chest")


def cape_w(V):
    out = []
    for v in V:
        z = v[2]
        if z > 1.42:
            out.append({"chest": 1.0})
        elif z > 1.3:
            t = float(smoothstep(1.3, 1.42, z))
            out.append({"chest": t, "cape.1": 1 - t})
        elif z > 1.14:
            out.append({"cape.1": 1.0})
        elif z > 1.02:
            t = float(smoothstep(1.02, 1.14, z))
            out.append({"cape.1": t, "cape.2": 1 - t})
        else:
            out.append({"cape.2": 1.0})
    return out


def cape(sb):
    nu, nv = 11, 10

    def fn(u, v):
        half = 0.19 + 0.1 * v
        x = (u - 0.5) * 2 * half
        z = 1.48 + (0.66 - 1.48) * v
        yb = back_y(TORSO, x * 0.95, min(max(z, 1.3), 1.47)) + 0.05
        y = yb + 0.08 * v ** 1.2 + 0.02 * math.sin(u * math.pi * 5.0) * v
        y -= 0.04 * (abs(u - 0.5) * 2) ** 3 * (1 - v) ** 2
        # ragged hem
        if v > 0.95:
            z += 0.04 * (0.5 + 0.5 * math.sin(u * 23.0))
        return (x, y, z)
    sb.add(K.cloth_panel(fn, nu, nv, "BH_Cloth_Primary", thick=0.012), weights=cape_w)


def quiver(sb):
    """Hip quiver on the right side, tilted back, with arrow shafts and pale fletching sticking out."""
    top = np.array([-0.2, 0.06, 1.0])
    bot = np.array([-0.2, -0.04, 0.68])
    d = normalize(top - bot)
    V, F = M.tube([bot, bot + (top - bot) * 0.5, top], [(0.04, 0.034), (0.043, 0.036), (0.046, 0.04)], n=10,
                  up=(1, 0, 0), cap1=False)
    sb.add(M.solidify(M.Part(V, F, "BH_Leather", name="quiver"), 0.006, offset=-1.0),
           "hips")
    for u in (0.2, 0.8):
        c = bot + (top - bot) * u
        V, F = M.tube([c - d * 0.01, c + d * 0.01], [(0.047, 0.04)] * 2, n=10, up=(1, 0, 0))
        sb.add(M.Part(V, F, "BH_Horn", name="quiver_band"), "hips")
    side = np.array([1.0, 0, 0])
    fw = np.cross(d, side)
    for k, (ox, oy) in enumerate(((0.012, 0.01), (-0.014, 0.012), (0.0, -0.016), (0.018, -0.012), (-0.016, -0.01))):
        base = top + side * ox + fw * oy - d * 0.05
        tip = base + d * (0.12 + 0.015 * (k % 2))
        V, F = M.tube([base, tip], [(0.005, 0.005)] * 2, n=5, up=(1, 0, 0))
        sb.add(M.Part(V, F, "BH_Wood", name="shaft"), "hips")
        for j in range(3):
            a = 2 * math.pi * j / 3 + k
            nrm = side * math.cos(a) + fw * math.sin(a)
            f0 = tip - d * 0.075
            V, F = M.tube([f0, tip - d * 0.01], [(0.001, 0.012), (0.001, 0.008)], n=4, up=nrm, p=3.0)
            sb.add(M.Part(V, F, "BH_Bone", name="fletch").move(nrm * 0.008), "hips")
