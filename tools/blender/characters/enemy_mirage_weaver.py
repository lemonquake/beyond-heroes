"""Mirage Weaver (bh-013, Builder A; illusionist duelist that splits into mirror images): a slender ~1.85 m dancer-
duelist in layered silks. A sand-gold headscarf wound round the head with a long tail down the back, a teal veil over
the lower face (only the kohl-dark eyes show, with a faint rose-pink shimmer), a gold chain of mirror coins across the
brow and down both temples. A fitted teal bodice under a sand-gold shoulder shawl sewn with small round mirror discs,
puffed teal upper sleeves, bare forearms stacked with gold bangles, a knee-length sand-gold over-skirt (mirror discs
along the hem) over wide teal trousers gathered at the ankles, a broad teal sash knotted at the hip whose two long
tails flow down the side. A curved dagger in each hand (weapon.R / weapon.L) with a rose glint in the pommel.

Clips: dual_1, dual_2, dual_heavy, cast_quick, cast_area, blink (+ the shared enemy base clips).
Kit: enemy_bandit_cutthroat (SB, curved_knife), enemy_ashen_cultist (skirt panels + weights), kit_a_common,
kit_e_orrery (discs / rings)."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C
import enemy_hollow_soldier as HS
import kit_a_common as A
import kit_e_orrery as O

SCALE = 1.85 / 1.845
PROPS = proportions(SCALE, shoulder_x=0.165 * SCALE, hip_x=0.088 * SCALE)
PALETTE = "mirage_weaver"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.56, 0.4, 0.17), 0.0, 0.7, None, 0.0, 1.0),        # sand-gold silk
    "BH_Cloth_Secondary": ((0.02, 0.27, 0.27), 0.0, 0.65, None, 0.0, 1.0),    # teal silk
    "BH_Steel": ((0.92, 0.93, 0.95), 1.0, 0.1, None, 0.0, 1.0),               # mirror discs / coins, blades
    "BH_Gold": ((0.8, 0.58, 0.22), 1.0, 0.3, None, 0.0, 1.0),                 # chains, bangles, trims
    "BH_Skin": ((0.5, 0.33, 0.22), 0.0, 0.55, None, 0.0, 1.0),
    "BH_Hair": ((0.03, 0.022, 0.02), 0.0, 0.6, None, 0.0, 1.0),               # kohl
    "BH_Leather": ((0.2, 0.12, 0.06), 0.0, 0.7, None, 0.0, 1.0),              # sandals, grips
    "BH_DarkSteel": ((0.2, 0.18, 0.16), 1.0, 0.4, None, 0.0, 1.0),
    "BH_Shadow": ((0.03, 0.02, 0.02), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((1.0, 0.55, 0.85), 0.0, 0.4, (1.0, 0.5, 0.82), 7.0, 1.0),  # rose shimmer (eyes, jewels)
}
CLIPS = ["dual_1", "dual_2", "dual_heavy", "cast_quick", "cast_area", "blink"]

TORSO = [(r[0], r[1] * 0.9, r[2] * 0.9, r[3] * 0.92, r[4] * 0.8) for r in K.TORSO]
G = 0.01
SK_TOP, SK_BOT, SK_FLARE = 1.06, 0.5, 0.13


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="body"), weights=C.ROBE_W)
    # ---- bodice + shawl
    C.robe_top(sb, "BH_Cloth_Secondary", trim="BH_Gold", g=G, rows=TORSO, v_open=0.05)
    shawl(sb)
    # ---- lower body: wide teal trousers, sand-gold over-skirt with mirror hem, sash
    trousers(sb)
    C.robe_skirt(sb, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", z_top=SK_TOP, z_bot=SK_BOT, flare=SK_FLARE,
                 folds=0.014, front_gap=0.03, g=G - 0.012)
    skirt_mirrors(sb)
    sash(sb)
    # ---- head: scarf, veil, coin chains
    K.neck_and_head(sb, skin="BH_Skin", eyes="BH_Hair", eye_glow="BH_Emissive", nose=False)
    headscarf(sb)
    # ---- arms: puffed teal sleeves, bare forearms with bangles, fists round the daggers
    for s in ("L", "R"):
        K.bare_arm(sb, s, r_up=0.042, r_fore=0.036, r_wrist=0.028)
        sleeve(sb, s)
        bangles(sb, s)
        K.add_fist(sb, s, "BH_Skin", "BH_Skin", scale=0.95)
    # ---- feet
    K.boots(sb, "BH_Leather", "BH_Leather", shaft_top=0.18, cuff=False)
    for s in ("L", "R"):
        k, a = sb.head("shin." + s), sb.tail("shin." + s)
        c = a + (k - a) * 0.12
        sb.add(O.ring(c, k - a, 0.052, 0.006, "BH_Gold", n=12, m=4), "shin." + s)
    # ---- daggers
    K.add_weapon(sb, "R", dagger(SCALE))
    K.add_weapon(sb, "L", dagger(SCALE))


# ================================================================================================= helpers
def centre_w(leg=0.5, top="hips"):
    def wfn(V):
        out = []
        for v in V:
            s_ = float(smoothstep(1.0, 0.5, v[2])) * leg
            out.append({"hips": 1 - s_, "thigh.L": s_ / 2, "thigh.R": s_ / 2} if s_ > 1e-3 else {"hips": 1.0})
        return out
    return wfn


def shawl_w(Vs):
    out = []
    for v in Vs:
        a = float(smoothstep(0.1, 0.24, abs(v[0])))
        s = "shoulder.L" if v[0] > 0 else "shoulder.R"
        out.append({"chest": 1 - 0.6 * a, s: 0.6 * a} if a > 1e-3 else {"chest": 1.0})
    return out


def shawl(sb):
    """Sand-gold shoulder shawl dipping to a point at the front and back, gold-edged, sewn with mirror discs."""
    zs = (1.51, 1.47, 1.42, 1.37, 1.33)
    nu = 32
    fr = np.linspace(0, 1, nu + 1)[:-1]
    rings = []
    for k, z in enumerate(zs):
        t = k / (len(zs) - 1)
        r = K.ring_frac(TORSO, max(z, 1.4), G + 0.02 + 0.045 * t, fr)
        r[:, 0] *= 1.0 + 0.1 * t
        # points at front / back centre dip lower
        r[:, 2] = z - 0.12 * t * np.cos(fr * 4 * math.pi) ** 8 * (np.abs(np.cos(fr * 2 * math.pi)) > 0.7)
        rings.append(r)
    V, F = M.loft(rings[::-1], cap0=False, cap1=False)
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="shawl"), 0.008, offset=1.0), weights=shawl_w)
    hem = np.vstack([rings[-1], rings[-1][:1]]) + np.array([0, 0, 0.004])
    sb.add(A.tube(hem, (0.006, 0.01), "BH_Gold", n=4, up=(0, 0, 1)), weights=shawl_w)
    # mirror discs in two rows, facing out
    for k, row in ((2, range(0, nu, 2)), (3, range(1, nu, 2))):
        for i in row:
            q = rings[k][i]
            nrm = normalize(np.array([q[0], q[1], 0.35]))
            sb.add(O.disc(q + nrm * 0.01, nrm, 0.017, 0.004, "BH_Steel", n=8), weights=shawl_w)
            sb.add(O.ring(q + nrm * 0.009, nrm, 0.018, 0.0028, "BH_Gold", n=8, m=3), weights=shawl_w)


def trousers(sb):
    """Wide teal trousers ballooning over the shins, gathered at the ankle by a gold cuff."""
    for s in ("L", "R"):
        th, sh = "thigh." + s, "shin." + s
        h, k, a = sb.head(th), sb.head(sh), sb.tail(sh)
        pts = [h + (0, 0, 0.04), h + (k - h) * 0.45, k, k + (a - k) * 0.45, k + (a - k) * 0.8, k + (a - k) * 0.92]
        prof = [(0.09, 0.094), (0.092, 0.096), (0.084, 0.088), (0.09, 0.094), (0.078, 0.08), (0.05, 0.052)]
        V, F = M.tube(pts, prof, n=12, up=(0, -1, 0))
        sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="trouser"), weights=sb.seg([th, sh], power=10))
        c = k + (a - k) * 0.9
        sb.add(O.ring(c, a - k, 0.052, 0.008, "BH_Gold", n=12, m=4), sh)
    K.pelvis_seat(sb, "BH_Cloth_Secondary", g=0.01)


def skirt_point(z, frac, lift=0.012):
    """Point on the over-skirt surface (same rows as ashen_cultist.robe_skirt)."""
    span = SK_TOP - SK_BOT
    g = G - 0.012
    rows = []
    for zz in np.linspace(SK_BOT, SK_TOP, 8):
        t = (SK_TOP - zz) / span
        rows.append((zz, 0.15 + g + SK_FLARE * t, 0.098 + g + SK_FLARE * t, 0.1 + g + SK_FLARE * 1.1 * t, 0.0))
    p = K.ring_frac(rows, z, lift, [frac], p=2.2)[0]
    return p


def skirt_mirrors(sb):
    for k, z in enumerate((SK_BOT + 0.05, SK_BOT + 0.13)):
        for i in range(18):
            frac = (i + 0.5 * k) / 18
            if abs(((frac + 0.5) % 1.0) - 0.5) < 0.03:     # keep the front slit clear
                continue
            p = skirt_point(z, frac)
            nrm = normalize(np.array([p[0], p[1], 0.15]))
            side = "L" if p[0] > 0 else "R"
            back = 0.25 < frac < 0.75
            w = C.robe_panel_w(sb, side, back)
            sb.add(O.disc(p, nrm, 0.016, 0.004, "BH_Steel", n=8), weights=w)
            if k == 0:
                sb.add(O.ring(p - nrm * 0.001, nrm, 0.017, 0.0025, "BH_Gold", n=8, m=3), weights=w)


def sash(sb):
    """Broad teal sash knotted at the left hip, two long tails flowing down the side."""
    V, F = K.band(TORSO, 0.98, 1.1, G + 0.03, G - 0.004, n=28)
    sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="sash"), "hips")
    for z in (0.985, 1.095):
        V, F = K.band(TORSO, z - 0.006, z + 0.006, G + 0.034, G + 0.02, n=28)
        sb.add(M.Part(V, F, "BH_Gold", name="sash_trim"), "hips")
    p, ang = K.on_ring(TORSO, 1.04, G + 0.05, 0.18)
    sb.add(A.ball(p, 0.04, "BH_Cloth_Secondary", n=8, rings=5, scale=(1.0, 0.8, 1.1)), "hips")
    sb.add(O.disc(p + np.array([0.02, -0.03, 0.0]), (0.5, -1, 0), 0.02, 0.005, "BH_Steel", n=8), "hips")
    sb.add(O.ball(p + np.array([0.022, -0.036, 0.0]), 0.008, "BH_Emissive", n=6, rings=4), "hips")
    w = sb.skirt(1.0, 0.45, max_leg=0.55, center_w=0.05)
    for k, (dx, dy, ln, wd) in enumerate(((0.03, -0.02, 0.62, 0.075), (0.07, 0.03, 0.5, 0.065))):
        pts, ups = [], []
        for t in np.linspace(0, 1, 9):
            pts.append(p + np.array([dx * t + 0.012 * math.sin(t * 5 + k), dy * t - 0.03 * t * t, -ln * t]))
            ups.append((1.0, -0.3, 0.0))
        tail = K.strip(pts, wd * 1.0, 0.006, "BH_Cloth_Secondary", ups=ups)
        sb.add(tail, weights=w)
        end = pts[-1]
        sb.add(A.tube([end + np.array([-wd / 2, 0, 0.0]), end + np.array([wd / 2, 0, 0.0])], 0.006, "BH_Gold", n=4),
               weights=w)
        for q in range(3):
            c = end + np.array([(q - 1) * wd * 0.35, 0.0, -0.025])
            sb.add(O.disc(c, (1, -0.2, 0), 0.012, 0.003, "BH_Steel", n=6), weights=w)


# ================================================================================================= head
def headscarf(sb):
    """Sand-gold scarf wound over the head, a teal twisted band, a long tail down the back, a teal veil over the
    lower face, a gold chain of mirror coins across the brow and hanging down the temples."""
    K.hair_cap(sb, mat="BH_Cloth_Primary", g=0.016, z_front=1.742, z_back=1.6, messy=0.004)
    # soft wound peak at the back of the crown
    sb.add(A.ball((0, 0.05, 1.79), 0.07, "BH_Cloth_Primary", n=12, rings=6, scale=(0.95, 1.05, 0.55)), "head")
    sb.add(A.ball((0, 0.1, 1.74), 0.035, "BH_Cloth_Primary", n=8, rings=5, scale=(1.2, 0.9, 1.0)), "head")  # knot
    ring = [np.array([0.088 * math.cos(a), 0.0 + 0.1 * math.sin(a), 1.755 + 0.03 * math.sin(a)])
            for a in np.linspace(0, 2 * math.pi, 21)]
    sb.add(A.tube(ring, 0.013, "BH_Cloth_Secondary", n=6, up=(0, 0, 1), cap=False), "head")
    # tail down the back (neck -> chest)
    pts = [(0.0, 0.1, 1.72), (0.01, 0.13, 1.6), (0.02, 0.15, 1.48), (0.03, 0.17, 1.34), (0.035, 0.19, 1.22)]
    sb.add(K.strip(pts, 0.11, 0.008, "BH_Cloth_Primary", ups=[(0, 1, 0)] * 5),
           weights=K.zspec_w([(1.5, "chest"), (1.58, "neck"), (1.64, "head")]))
    # side drapes over the ears to the shoulders
    for sx in (1, -1):
        pts = [(sx * 0.085, 0.0, 1.72), (sx * 0.095, 0.01, 1.64), (sx * 0.1, 0.03, 1.56), (sx * 0.11, 0.05, 1.5)]
        sb.add(K.strip(pts, 0.08, 0.008, "BH_Cloth_Primary", ups=[(sx, 0, 0)] * 4),
               weights=K.zspec_w([(1.5, "chest"), (1.58, "neck"), (1.64, "head")]))
    # veil over the lower face: from under the eyes to below the chin, falling to the chest
    def fn(u, v):
        z = 1.678 - 0.2 * v
        hw = 0.078 + 0.02 * v
        a = (u - 0.5) * 2
        x = a * hw
        yface = -0.086 + 0.075 * a ** 2
        y = yface - 0.004 - 0.018 * v * (1 - 0.5 * a ** 2)
        return (x, y, z)
    V, F = M.grid(fn, 9, 6)
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Secondary", name="veil"), 0.006, offset=1.0),
           weights=K.zspec_w([(1.5, "neck"), (1.62, "head")]))
    edge = np.array([fn(u, 0.0) for u in np.linspace(0, 1, 9)]) + np.array([0, -0.006, 0.004])
    sb.add(A.tube(edge, 0.004, "BH_Gold", n=4), "head")
    # brow chain of mirror coins (drooping across the forehead) + temple chains
    brow = [np.array([0.08 * math.sin(a), -0.075 * math.cos(a) - 0.012, 1.748 - 0.012 * math.cos(a)])
            for a in np.linspace(-1.35, 1.35, 11)]
    sb.add(A.tube(brow, 0.0035, "BH_Gold", n=4), "head")
    for i, q in enumerate(brow[1:-1]):
        nrm = normalize(np.array([q[0], q[1], 0.0]))
        c = q + np.array([0, 0, -0.016]) + nrm * 0.003
        sb.add(O.disc(c, nrm, 0.011 if i != 4 else 0.015, 0.003, "BH_Steel", n=8), "head")
    sb.add(A.ball(brow[5] + np.array([0, -0.006, 0.006]), 0.008, "BH_Emissive", n=6, rings=4), "head")
    for sx in (1, -1):
        top = np.array([sx * 0.085, -0.03, 1.745])
        pts = [top, top + np.array([sx * 0.008, -0.004, -0.07]), top + np.array([sx * 0.012, -0.004, -0.13])]
        sb.add(A.tube(pts, 0.003, "BH_Gold", n=4), "head")
        for k in range(3):
            c = top + np.array([sx * 0.016, -0.004, -0.04 - 0.045 * k])
            sb.add(O.disc(c, (sx, -0.4, 0), 0.012, 0.003, "BH_Steel", n=8), "head")


# ================================================================================================= arms
def sleeve(sb, s):
    ua, fa = "upper_arm." + s, "forearm." + s
    sh, el = sb.head(ua), sb.head(fa)
    sx = 1 if s == "L" else -1
    pts = [sh + (-0.035 * sx, 0, 0.025), sh, sh + (el - sh) * 0.35, sh + (el - sh) * 0.7, el + (el - sh) * 0.02]
    prof = [(0.05, 0.054), (0.066, 0.068), (0.074, 0.076), (0.066, 0.068), (0.046, 0.048)]
    V, F = M.tube(pts, prof, n=12, up=(0, -1, 0), cap1=False)
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Secondary", name="sleeve"), 0.006, offset=-1.0),
           weights=sb.seg(["chest", "shoulder." + s, ua, fa], power=9))
    c = el + (el - sh) * 0.0
    sb.add(O.ring(c, el - sh, 0.047, 0.007, "BH_Gold", n=12, m=4),
           weights=sb.seg([ua, fa], power=9))


def bangles(sb, s):
    fa, ha = "forearm." + s, "hand." + s
    el, wr = sb.head(fa), sb.head(ha)
    d = wr - el
    for k, u in enumerate((0.55, 0.66, 0.74, 0.82, 0.9)):
        r = 0.039 - 0.006 * u + (0.004 if k % 2 else 0.0)
        sb.add(O.ring(el + d * u, d, r, 0.0055, "BH_Gold" if k != 2 else "BH_Steel", n=12, m=4), fa)


# ================================================================================================= weapon
def dagger(s=1.0):
    """Curved dagger (weapon space): mirror-bright curved blade, gold guard and pommel with a rose jewel."""
    parts = K.curved_knife(length=0.36, width=0.046, curve=0.075, mat="BH_Steel", grip_mat="BH_Leather")
    for p in parts:
        if p.mat == "BH_DarkSteel":
            p.mat = "BH_Gold"
    parts.append(A.ball((0, 0, -0.078), 0.012, "BH_Emissive", n=6, rings=4))
    for p in parts:
        p.V = p.V * s
    return parts
