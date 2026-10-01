"""Kharvenn Chain-Bearer (bh-029, Builder M2, Zarael / the Glasswire Barrens and the Heart Citadel brute): a 2.9 m
Kharvenn war-thrall, bred and broken to haul the Dominion's leash-chains. Bare grey skin over slab muscle, a small
shaved head with a heavy brow, white eye-glints and an iron muzzle-mask riveted over the jaw; a massive iron collar
with a rune burning white and a hanging ring. A layered iron pauldron on the left shoulder, a leather harness with
an iron chest-plate (the Kharvenn chain-circle in relief), a rune-chain slung from the right shoulder across the
chest, a broad riveted iron belt over a ragged black loincloth, iron bracers and greaves, wrapped feet.
Weapon (weapon.R, two-handed gs clips): a huge iron ship's-anchor used as a hook-maul - a thick shank wound with
rune-chain (white runes), the crown and two flukes curving back at the head end, a ring at the butt with a length of
chain hanging from it.

GLOW: pure white (BH_Emissive (1, 1, 1), energy 5) - runes only (collar, chest-plate, chain tags, shank). Kharvenn,
not Zarael: grey iron, black cloth. ~2.85 m. Clips: boss_charge boss_slam gs_1 gs_heavy (+ the shared base set)."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_hollow_soldier as HS
import kit_a_common as A
import enemy_glyphbound_warrior as Z
import enemy_chain_priest as CP

SCALE = 1.55
PROPS = proportions(SCALE, shoulder_x=0.24 * SCALE, upper_len=0.3 * SCALE, fore_len=0.29 * SCALE,
                    hip_x=0.12 * SCALE, clav_drop=0.06 * SCALE)
PREVIEW_HEIGHT = 3.4
PALETTE = "chain_bearer"
PALETTE_COLORS = {
    "BH_Skin": ((0.37, 0.35, 0.33), 0.0, 0.55, None, 0.0, 1.0),                 # bare grey skin
    "BH_Flesh": ((0.24, 0.12, 0.11), 0.0, 0.5, None, 0.0, 1.0),                # chafed skin under the collar
    "BH_Cloth_Secondary": ((0.025, 0.024, 0.028), 0.0, 0.92, None, 0.0, 1.0),  # black loincloth / wraps
    "BH_DarkSteel": ((0.1, 0.1, 0.108), 1.0, 0.55, None, 0.0, 1.0),            # dark iron plates, anchor
    "BH_Steel": ((0.27, 0.27, 0.28), 1.0, 0.48, None, 0.0, 1.0),               # worn iron chain, rivets
    "BH_Leather": ((0.07, 0.055, 0.045), 0.0, 0.7, None, 0.0, 1.0),            # harness straps
    "BH_Rust": ((0.24, 0.13, 0.08), 0.5, 0.8, None, 0.0, 1.0),                 # rust streaks on the anchor
    "BH_Shadow": ((0.012, 0.012, 0.014), 0.0, 0.85, None, 0.0, 1.0),
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),     # runes (pure white)
}
CLIPS = ["boss_charge", "boss_slam", "gs_1", "gs_heavy"]

TORSO = [
    (0.92, 0.18, 0.12, 0.12, 0.0),
    (1.0, 0.19, 0.13, 0.12, 0.0),
    (1.1, 0.2, 0.14, 0.13, 0.02),
    (1.2, 0.23, 0.155, 0.15, 0.05),
    (1.3, 0.265, 0.17, 0.17, 0.06),
    (1.39, 0.285, 0.17, 0.19, 0.04),
    (1.46, 0.27, 0.15, 0.2, 0.0),
    (1.52, 0.2, 0.12, 0.17, 0.0),
    (1.57, 0.12, 0.085, 0.12, 0.0),
    (1.6, 0.075, 0.06, 0.08, 0.0),
]
TORSO_W = K.zspec_w([(0.99, "hips"), (1.1, "spine"), (1.22, "spine"), (1.32, "chest")])
HEAD = [(r[0], r[1] * 1.08, r[2] * 1.04, r[3] * 1.0) + tuple(r[4:]) for r in K.HEAD]
P = Z.P
chain = CP.chain


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft(K.rows_between(TORSO, 0.92, 1.6, n_extra=6), n=32, p=2.2, cap0=True, cap1=True)
    sb.add(P(V, F, "BH_Skin", "torso"), weights=TORSO_W)
    muscles(sb)
    head(sb)
    collar(sb)
    harness(sb)
    for s in ("L", "R"):
        arm(sb, s)
    pauldron(sb)
    K.pelvis_seat(sb, "BH_Cloth_Secondary", g=0.03)
    legs(sb)
    belt_and_loincloth(sb)
    K.add_weapon(sb, "R", anchor(SCALE * 0.88))


# ================================================================================================= body
def muscles(sb):
    for sx in (1, -1):
        # pectorals
        x = sx * 0.11
        sb.add(A.ball((x, front_y(TORSO, x, 1.36) + 0.03, 1.36), 0.12, "BH_Skin", n=12, rings=7,
                      scale=(1.0, 0.42, 0.62)), "chest")
        # trapezius rising to the neck
        sb.add(A.ball((sx * 0.12, 0.03, 1.53), 0.1, "BH_Skin", n=10, rings=6, scale=(1.1, 0.8, 0.55)), "chest")
        # shoulder blades / lats
        sb.add(A.ball((sx * 0.13, back_y(TORSO, sx * 0.13, 1.36) - 0.04, 1.36), 0.12, "BH_Skin", n=10, rings=6,
                      scale=(0.9, 0.4, 1.0)), "chest")
    # abdominals: three rows of slabs
    for row, z in enumerate((1.12, 1.19, 1.26)):
        for sx in (1, -1):
            x = sx * 0.045
            sb.add(A.ball((x, front_y(TORSO, x, z) + 0.016, z), 0.045, "BH_Skin", n=8, rings=5,
                          scale=(1.0, 0.45, 0.75)), weights=TORSO_W)


def head(sb):
    # thick neck (the collar sits on it)
    V, F = M.tube([(0, 0.02, 1.5), (0, 0.0, 1.57), (0, -0.01, 1.63)], [(0.085, 0.08), (0.075, 0.072), (0.065, 0.065)],
                  n=14, up=(0, -1, 0))
    sb.add(P(V, F, "BH_Skin", "neck"), weights=K.HEAD_W)
    K.neck_and_head(sb, skin="BH_Skin", head_rows=HEAD, eyes="BH_Shadow", eye_glow="BH_Emissive", nose=True)
    # heavy brow ridge
    sb.add(A.tube([(-0.06, -0.058, 1.718), (0.0, -0.074, 1.724), (0.06, -0.058, 1.718)], (0.016, 0.011), "BH_Skin",
                  n=6), "head")
    # iron muzzle-mask over the jaw: curved plate with breathing slots and rivets, straps round the head
    def fn(u, v):
        a = math.radians(-80 + 160 * u)
        z = 1.6 + 0.07 * v
        r = 0.086 + 0.006 * v
        return (r * math.sin(a), -0.004 - r * 1.05 * math.cos(a), z)
    V, F = M.grid(fn, 9, 3)
    sb.add(M.solidify(P(V, F, "BH_DarkSteel", "muzzle"), 0.008, offset=-1.0), "head")
    for x in (-0.03, -0.01, 0.01, 0.03):
        sb.add(A.tube([(x, -0.098, 1.615), (x, -0.098, 1.65)], (0.005, 0.003), "BH_Shadow", n=4, up=(0, -1, 0)),
               "head")
    for sx in (1, -1):
        sb.add(A.ball((sx * 0.07, -0.06, 1.66), 0.008, "BH_Steel", n=5, rings=3), "head")
        pts = K.ring_frac(K.grow_rows(HEAD, 0.004), 1.665, 0.0, np.linspace(0.18, 0.45, 6) if sx > 0 else
                          np.linspace(0.82, 0.55, 6), p=2.1)
        sb.add(A.tube(pts, (0.006, 0.012), "BH_Leather", n=4), "head")
    # a few scars (dark) on the scalp
    sb.add(A.tube([(0.02, -0.04, 1.8), (0.05, 0.0, 1.795), (0.06, 0.04, 1.77)], 0.004, "BH_Flesh", n=4), "head")


def collar(sb):
    """Massive iron collar on the neck base: a thick riveted ring, a white rune on the front, a hanging ring."""
    zc = 1.53
    V, F = M.lathe([(0.11, -0.045), (0.155, -0.04), (0.165, 0.0), (0.155, 0.04), (0.11, 0.045)], 20, cap=False)
    sb.add(P(V, F, "BH_DarkSteel", "collar").scale((1.0, 0.92, 1.0)).move((0, 0.0, zc)), "chest")
    for k in range(10):
        a = 2 * math.pi * k / 10
        sb.add(A.ball((0.163 * math.sin(a), -0.163 * 0.92 * math.cos(a), zc), 0.011, "BH_Steel", n=5, rings=3),
               "chest")
    sb.add(A.ball((0, 0.0, zc - 0.04), 0.14, "BH_Flesh", n=12, rings=4, scale=(1.0, 0.95, 0.12)), "chest")
    y = -0.163 * 0.92 - 0.004
    sb.add(A.tube([(0, y, zc - 0.03), (0, y, zc + 0.03)], (0.006, 0.003), "BH_Emissive", n=4, up=(0, -1, 0)), "chest")
    sb.add(A.tube([(-0.022, y, zc + 0.012), (0, y, zc - 0.01), (0.022, y, zc + 0.012)], (0.005, 0.003), "BH_Emissive",
                  n=4, up=(0, -1, 0)), "chest")
    ring = [(0.04 * math.cos(a), y - 0.012, zc - 0.075 + 0.04 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 13)]
    sb.add(A.tube(ring, 0.009, "BH_Steel", n=5, cap=False), "chest")


def harness(sb):
    """Leather harness (two straps crossing the chest to the back) with an iron chest-plate bearing the chain-circle;
    a rune-chain slung from the right shoulder across the chest to the left hip."""
    g = 0.012
    for sx in (1, -1):
        pts, ups = [], []
        for t in np.linspace(0, 1, 7):
            x = sx * (0.17 - 0.17 * t)
            z = 1.5 - 0.2 * t
            pts.append((x, front_y(TORSO, x, z) - g - 0.03 * math.sin(math.pi * t) * 0.6, z))
            ups.append((0, -1, 0.2))
        sb.add(K.strip(pts, 0.06, 0.012, "BH_Leather", ups=ups), "chest")
        pts = [(sx * 0.17, back_y(TORSO, sx * 0.17, 1.5) + g, 1.5), (0.0, back_y(TORSO, 0.0, 1.3) + g, 1.3)]
        sb.add(K.strip(pts, 0.06, 0.012, "BH_Leather", ups=[(0, 1, 0.2)] * 2), "chest")
    zc = 1.3
    yc = front_y(TORSO, 0, zc) - 0.05
    V, F = M.lathe([(0.0, -0.012), (0.085, -0.01), (0.095, 0.0), (0.085, 0.012), (0.0, 0.016)], 16)
    sb.add(P(V, F, "BH_DarkSteel", "chestplate").rot(Rx(90)).move((0, yc, zc)), "chest")
    ring = [np.array([0.055 * math.cos(a), yc - 0.018, zc + 0.055 * math.sin(a)]) for a in np.linspace(0, 2 * math.pi,
                                                                                                         13)]
    for prt in chain(ring, size=0.03, r=0.005):
        sb.add(prt, "chest")
    sb.add(A.tube([(0, yc - 0.02, zc - 0.03), (0, yc - 0.02, zc + 0.03)], (0.006, 0.003), "BH_Emissive", n=4,
                  up=(0, -1, 0)), "chest")
    # bandolier chain: right shoulder -> left hip (front) and back
    pts = []
    for t in np.linspace(0, 1, 7):
        x = -0.2 + 0.4 * t
        z = 1.52 - 0.5 * t
        pts.append((x, front_y(TORSO, x, z) - 0.035, z))
    for prt in chain(pts, size=0.055, r=0.008, runes=(3, 9)):
        sb.add(prt, weights=TORSO_W)
    pts = []
    for t in np.linspace(0, 1, 6):
        x = -0.2 + 0.4 * t
        z = 1.52 - 0.5 * t
        pts.append((x, back_y(TORSO, x, z) + 0.03, z))
    for prt in chain(pts, size=0.055, r=0.008):
        sb.add(prt, weights=TORSO_W)


def arm(sb, s):
    sx = 1 if s == "L" else -1
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    K.bare_arm(sb, s, skin="BH_Skin", r_up=0.07, r_fore=0.062, r_wrist=0.045, bulk=1.05)
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    w = sb.seg(["chest", "shoulder." + s, ua, fa, ha], power=9)
    # deltoid + biceps bulk
    sb.add(A.ball(sh + np.array([sx * 0.02, 0, -0.02]), 0.1, "BH_Skin", n=10, rings=6, scale=(0.9, 1.0, 1.1)),
           weights=w)
    sb.add(A.ball(sh + (el - sh) * 0.5 + np.array([0, -0.025, 0]), 0.075, "BH_Skin", n=10, rings=6,
                  scale=(1.0, 0.95, 1.6)), ua)
    # iron bracer with rivets + leather under-wrap
    V, F = M.tube([el + (wr - el) * 0.45, wr + (wr - el) * 0.02], [(0.078, 0.08), (0.068, 0.07)], n=14, up=(0, -1, 0))
    sb.add(M.bevel(P(V, F, "BH_DarkSteel", "bracer"), 0.005, 1), fa)
    d = normalize(wr - el)
    for u in (0.55, 0.85):
        c = el + (wr - el) * u
        side = normalize(np.cross(d, (0, 1, 0)))
        for k in range(4):
            a = 2 * math.pi * k / 4
            fw = np.cross(side, d)
            sb.add(A.ball(c + (side * math.cos(a) + fw * math.sin(a)) * 0.08, 0.008, "BH_Steel", n=5, rings=3), fa)
    K.add_fist(sb, s, "BH_Skin", "BH_Skin", gauntlet=False, scale=1.25)
    if s == "L":
        # a length of chain wound round the left forearm above the bracer
        pts = CP.helix(el + (wr - el) * 0.05, el + (wr - el) * 0.42, 0.07, 0.074, 1.5, n=20)
        for prt in chain(pts, size=0.045, r=0.0065, runes=(4,)):
            sb.add(prt, fa)


def pauldron(sb):
    """Layered iron pauldron on the left shoulder (three plates) with rivets and a rune."""
    sh = sb.head("upper_arm.L")
    for k, (r, dz, dx) in enumerate(((0.14, 0.06, 0.0), (0.13, 0.0, 0.035), (0.115, -0.055, 0.065))):
        V, F = M.lathe([(r * math.sin(math.radians(a)), r * math.cos(math.radians(a))) for a in range(0, 75, 12)],
                       14, cap=False)
        prt = P(V, F, "BH_DarkSteel", "pauldron").scale((1.0, 1.15, 0.8)).rot(Ry(-30 - 12 * k))
        prt.move(sh + np.array([dx - 0.02, 0.0, dz]))
        sb.add(M.solidify(prt, 0.012, offset=1.0), "shoulder.L")
    top = sh + np.array([-0.02, 0.0, 0.06]) + Ry(-30) @ np.array([0, 0, 0.115])
    sb.add(A.tube([top + (0, -0.05, 0), top + (0, 0.05, 0)], (0.006, 0.004), "BH_Emissive", n=4,
                  up=tuple(Ry(-30) @ np.array([0, 0, 1.0]))), "shoulder.L")
    for k in range(5):
        a = math.radians(-60 + 30 * k)
        q = sh + np.array([-0.02, 0, 0.06]) + Ry(-30) @ (np.array([0.0, math.sin(a), math.cos(a)]) * 0.14 *
                                                         np.array([1, 1.15, 0.8]))
        sb.add(A.ball(q, 0.01, "BH_Steel", n=5, rings=3), "shoulder.L")


def legs(sb):
    for s in ("L", "R"):
        th, sh = "thigh." + s, "shin." + s
        h, k, a = sb.head(th), sb.head(sh), sb.tail(sh)
        pts = [h + (0, 0, 0.04), h + (k - h) * 0.4, k + (0, 0, 0.02), k + (a - k) * 0.35, k + (a - k) * 0.75, a]
        prof = [(0.1, 0.105), (0.095, 0.1), (0.07, 0.075), (0.072, 0.078), (0.055, 0.058), (0.045, 0.048)]
        V, F = M.tube(pts, prof, n=14, up=(0, -1, 0))
        sb.add(P(V, F, "BH_Skin", "leg"), weights=sb.seg([th, sh], power=10))
        # iron knee cop + greave
        sb.add(A.ball(k + np.array([0, -0.06, 0.0]), 0.065, "BH_DarkSteel", n=10, rings=5, scale=(1.0, 0.55, 1.0)),
               weights=lambda V, s=s: [{"thigh." + s: 0.35, "shin." + s: 0.65}] * len(V))
        V, F = M.tube([k + (a - k) * 0.15, k + (a - k) * 0.8], [(0.082, 0.086), (0.065, 0.07)], n=12, up=(0, -1, 0),
                      cap0=False, cap1=False)
        greave = P(V, F, "BH_DarkSteel", "greave")
        greave.V = greave.V[:]
        sb.add(M.solidify(greave, 0.008, offset=1.0), sh)
        sb.add(A.tube([k + (a - k) * 0.3 + np.array([0, -0.092, 0]), k + (a - k) * 0.65 + np.array([0, -0.08, 0])],
                      (0.005, 0.003), "BH_Emissive", n=4, up=(0, -1, 0)), sh)
    K.boots(sb, "BH_Cloth_Secondary", "BH_Leather", shaft_top=0.2, cuff=False, wraps="BH_Leather")


def belt_and_loincloth(sb):
    rows = [(r[0], r[1] + 0.035, r[2] + 0.035, r[3] + 0.035, r[4]) for r in TORSO]
    for front in (True, False):
        pnl = HS.cloth_panel(rows, 1.0, 0.48, lambda z: 0.13 + 0.02 * (1.0 - z), front=front, nu=7, nv=8,
                             mat="BH_Cloth_Secondary", gap=0.004, hang=0.05, rag=0.07, teeth=4, thick=0.01,
                             belt_z=0.97, seed=2.0 if front else 4.0)
        sb.add(pnl, weights=Z.centre_w(0.98, 0.55, 0.6))
    V, F = K.band(rows, 0.93, 1.03, 0.022, -0.002, n=30)
    sb.add(P(V, F, "BH_DarkSteel", "belt"), "hips")
    for k in range(16):
        p, _ = K.on_ring(rows, 0.98, 0.024, k / 16)
        sb.add(A.ball(p, 0.01, "BH_Steel", n=5, rings=3), "hips")
    # iron belt plate (front) + hanging chain loop on the right hip
    yb = front_y(rows, 0, 0.98) - 0.03
    V, F = M.box(0.16, 0.02, 0.13)
    sb.add(M.bevel(P(V, F, "BH_DarkSteel", "beltplate").move((0, yb, 0.98)), 0.006, 1), "hips")
    sb.add(A.tube([(-0.04, yb - 0.012, 0.98), (0.0, yb - 0.012, 1.02), (0.04, yb - 0.012, 0.98),
                   (0.0, yb - 0.012, 0.94), (-0.04, yb - 0.012, 0.98)], (0.006, 0.003), "BH_Emissive", n=4,
                  up=(0, -1, 0), cap=False), "hips")
    p, _ = K.on_ring(rows, 0.97, 0.03, 0.82)
    for prt in chain([p, p + np.array([-0.04, -0.06, -0.25]), p + np.array([0.0, -0.13, 0.0])], size=0.05, r=0.007):
        sb.add(prt, weights=sb.skirt(1.0, 0.6, max_leg=0.4, center_w=0.05))


# ================================================================================================= weapon
def anchor(s=1.0):
    """Weapon space (grip at origin, +Z toward the crown; arms span +-X, flats +-Y). Shank -0.42..1.0, crown at
    ~1.05 with two arms curving back toward the grip ending in flukes; a ring at the butt with a hanging chain; rune-
    chain wound round the shank."""
    parts = []
    V, F = M.lathe([(0, -0.38), (0.034, -0.38), (0.036, -0.3), (0.03, -0.2), (0.032, 0.6), (0.042, 0.9),
                    (0.05, 1.0), (0, 1.02)], 10)
    shank = P(V, F, "BH_DarkSteel", "shank").scale((1.0, 0.8, 1.0))
    parts.append(shank)
    parts.append(K.WP._grip(-0.16, 0.2, 0.037, 6, mat="BH_Leather"))
    # butt ring + stock bar
    ring = [(0.0, 0.07 * math.cos(a), -0.45 + 0.07 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 15)]
    parts.append(A.tube(ring, 0.016, "BH_DarkSteel", n=6, cap=False))
    V, F = M.box(0.26, 0.04, 0.04, center=(0, 0, -0.3))
    parts.append(M.bevel(P(V, F, "BH_DarkSteel", "stock"), 0.008, 1))
    for sx in (1, -1):
        parts.append(A.ball((sx * 0.135, 0, -0.3), 0.03, "BH_DarkSteel", n=8, rings=5))
    # crown + arms + flukes
    parts.append(A.ball((0, 0, 1.0), 0.07, "BH_DarkSteel", n=10, rings=6, scale=(1.2, 0.85, 0.9)))
    for sx in (1, -1):
        arm = [(0.0, 0, 1.0), (sx * 0.16, 0, 1.0), (sx * 0.3, 0, 0.92), (sx * 0.37, 0, 0.78), (sx * 0.38, 0, 0.66)]
        parts.append(A.tube(arm, [(0.055, 0.045), (0.05, 0.04), (0.046, 0.036), (0.04, 0.032), (0.03, 0.026)],
                            "BH_DarkSteel", n=7, up=(0, 1, 0)))
        # fluke: a broad spade blade at the arm's end, pointing back down at the grip, sharp hooked tip
        o = np.array([(0.0, 0.0), (0.09, -0.02), (0.11, -0.12), (0.05, -0.24), (0.0, -0.3), (-0.04, -0.17),
                      (-0.04, -0.04)])
        o[:, 0] *= sx
        area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
        if area < 0:
            o = o[::-1]
        V, F = M.prism(o, 0.05, axis="y")
        fl = P(V, F, "BH_DarkSteel", "fluke").move((sx * 0.36, 0, 0.82))
        fl.warp(lambda v, sx=sx: (v[0], v[1] * (1.0 - 0.75 * min(abs(v[0] - sx * 0.36) / 0.11, 1.0)), v[2]))
        parts.append(M.bevel(fl, 0.006, 1, angle=45))
        # rust streak on the fluke
        parts.append(A.tube([(sx * 0.38, -0.022, 0.78), (sx * 0.39, -0.022, 0.64)], (0.012, 0.003), "BH_Rust", n=4,
                            up=(0, -1, 0)))
    # crown spike
    parts.append(A.taper([(0, 0, 1.04), (0, 0, 1.2)], 0.035, 0.004, "BH_DarkSteel", n=7))
    # rune channels on both flats of the shank
    for sy in (1, -1):
        parts.append(A.tube([(0, sy * 0.027, 0.62), (0, sy * 0.031, 0.92)], (0.007, 0.003), "BH_Emissive", n=4,
                            up=(0, sy, 0)))
        for z in (0.68, 0.78, 0.88):
            parts.append(A.tube([(-0.018, sy * 0.029, z - 0.015), (0, sy * 0.03, z), (0.018, sy * 0.029, z - 0.015)],
                                (0.005, 0.0025), "BH_Emissive", n=4, up=(0, sy, 0)))
    # rune-chain wound round the shank, and a length hanging from the butt ring
    pts = CP.helix((0, 0, 0.24), (0, 0, 0.56), 0.05, 0.05, 2.0, n=24)
    parts += chain(pts, size=0.05, r=0.008, runes=(5,))
    hang = [(0.0, 0.0, -0.52), (0.04, 0.02, -0.72), (0.02, 0.0, -0.92)]
    parts += chain(hang, size=0.055, r=0.009, runes=(2,))
    for p in parts:
        p.V = p.V * s
    return parts
