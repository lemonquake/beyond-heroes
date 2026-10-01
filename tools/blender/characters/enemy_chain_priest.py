"""Kharvenn Chain-Priest (bh-029, Builder M2, Zarael / the Glasswire Barrens and the Heart Citadel caster/support):
a foreign priest of the Dominion that leashes Gigas with pain. Long grey wool robes banded with dark iron hoops and
riveted iron lames down the skirt, a black scapular over chest and back bearing the Kharvenn emblem (a circle of
iron chain), a deep black hood under a tall peaked iron mitre with a white-glowing rune, a veil of short chains
hanging across the face (white eye-glints behind it). Rune-chains wind round both sleeves; more hang from the iron
belt, ending in rune-weights whose runes burn white. Right hand (weapon.R): a rune-iron rod - a dark iron shaft with
chain wound round it and a caged head holding a white rune-core. Left hand (weapon.L): a smoking iron censer on a
chain (the chain hangs from the fist on the `censer` bone and swings with gravity via secondary()).

GLOW: pure white (BH_Emissive (1, 1, 1), energy 5) - runes, rune-core, censer. Not Zarael stone: grey iron and
black cloth. ~1.85 m (mitre peak ~2.15 m). Clips: cast_area cast_quick cast_weapon staff_1."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz, R_axis, slerp_mat
from bh_skeleton import proportions, joints
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C
import kit_a_common as A
import enemy_glyphbound_warrior as Z

SCALE = 1.85 / 1.82
PROPS = proportions(SCALE, shoulder_x=0.185 * SCALE, hip_x=0.098 * SCALE)
PREVIEW_HEIGHT = 2.5
PALETTE = "chain_priest"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.25, 0.25, 0.255), 0.0, 0.93, None, 0.0, 1.0),        # grey wool robe
    "BH_Cloth_Secondary": ((0.024, 0.023, 0.027), 0.0, 0.9, None, 0.0, 1.0),   # black hood / scapular
    "BH_DarkSteel": ((0.1, 0.1, 0.108), 1.0, 0.55, None, 0.0, 1.0),            # dark iron bands, mitre, rod
    "BH_Steel": ((0.27, 0.27, 0.28), 1.0, 0.48, None, 0.0, 1.0),               # worn iron chains
    "BH_Skin": ((0.36, 0.33, 0.31), 0.0, 0.6, None, 0.0, 1.0),                 # pale grey skin
    "BH_Leather": ((0.055, 0.05, 0.045), 0.0, 0.7, None, 0.0, 1.0),            # gloves, boots
    "BH_Bone": ((0.33, 0.33, 0.34), 0.0, 1.0, None, 0.0, 1.0),                 # censer smoke
    "BH_Shadow": ((0.01, 0.01, 0.012), 0.0, 0.85, None, 0.0, 1.0),             # hood interior
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),     # runes (pure white)
}
CLIPS = ["cast_area", "cast_quick", "cast_weapon", "staff_1"]

TORSO = [(r[0], r[1] * 0.97, r[2] * 0.97, r[3] * 0.97, r[4]) for r in K.TORSO]
G = 0.014
P = Z.P


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


# censer chain bone: head at the LEFT grip (rest), parented to hand.L; secondary() makes it hang with gravity
_J = joints(PROPS)
_GRIP_L = _J["weapon.L"][0]
EXTRA_BONES = [("censer", tuple(_GRIP_L), tuple(_GRIP_L + np.array([0.0, 0.0, -0.4 * SCALE])), "hand.L", (0, -1, 0))]
CHAIN = 0.36


def _model_hand_L():
    from bh_anim import Rig, DEFAULTS
    from bh_body import MODEL_POSE
    c = dict(DEFAULTS)
    c.update(MODEL_POSE)
    Q, t, D = Rig(PROPS).evaluate(c)
    return D["hand.L"].R


def secondary(anim, frames):
    """Pendulum (enemy_ashen_acolyte's, on the left hand): the censer keeps its modelled hanging orientation, swings
    back against the hand's horizontal velocity and follows the hand rigidly near the ground (deaths)."""
    Rm = _model_hand_L()
    n = len(frames)
    heads = np.array([fr[3]["hand.L"].apply(_GRIP_L) for fr in frames])
    loop = bool(getattr(anim, "loop", False))
    vel = np.zeros((n, 3))
    for f in range(n):
        a, b = max(f - 1, 0), min(f + 1, n - 1)
        if loop and n > 2:
            a, b = (f - 1) % (n - 1), (f + 1) % (n - 1)
        vel[f] = (heads[b] - heads[a]) * 30.0 / max(1, (b - a) % max(n - 1, 1) or 2)
    sm = vel.copy()
    for f in range(n):
        sm[f] = vel[max(f - 3, 0):f + 1].mean(0)
    out = []
    for f in range(n):
        Rp = frames[f][3]["hand.L"].R
        v = sm[f].copy()
        v[2] = 0.0
        sp = float(np.linalg.norm(v))
        Rs = np.eye(3)
        if sp > 1e-3:
            axis = normalize(np.cross(np.array([0, 0, -1.0]), -v))
            Rs = R_axis(axis, min(40.0, 22.0 * sp))
        hang = Rs @ Rm
        w = float(smoothstep(0.3, 0.65, heads[f][2]))
        out.append({"censer": Rp.T @ slerp_mat(Rp, hang, w)})
    return out


# ================================================================================================= chain kit
def link(c, d, a, size, r, mat):
    """One chain link: an elongated ring centred at c, long axis d, ring plane spanned by d and a."""
    d, a = normalize(d), normalize(a)
    pts = [c + d * (size * 0.5 * math.cos(q)) + a * (size * 0.3 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 7)]
    V, F = M.tube(pts, [(r, r)] * len(pts), n=3, up=tuple(np.cross(d, a)), cap0=False, cap1=False)
    return P(V, F, mat, "link")


def chain(pts, size=0.034, r=0.0045, mat="BH_Steel", runes=(), rune_mat="BH_Emissive"):
    """Chain of alternating links laid along a polyline. runes: link indices that carry a small glowing rune tag."""
    pts = np.asarray(pts, float)
    segl = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(segl)])
    out = []
    cnt = max(1, int(L[-1] / (size * 0.72)))
    for i in range(cnt):
        t = (i + 0.5) * L[-1] / cnt
        j = min(np.searchsorted(L, t, side="right") - 1, len(segl) - 1)
        u = (t - L[j]) / max(segl[j], 1e-9)
        c = pts[j] * (1 - u) + pts[j + 1] * u
        d = normalize(pts[j + 1] - pts[j])
        a = normalize(np.cross(d, (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)))
        if i % 2:
            a = normalize(np.cross(d, a))
        out.append(link(c, d, a, size, r, mat))
        if i in runes:
            b = np.cross(d, a)
            V, F = M.box(size * 0.55, size * 0.12, size * 0.75)
            R = np.stack([a, b, d], 1)
            out.append(P(np.asarray(V) @ R.T + c + b * size * 0.18, F, "BH_DarkSteel", "tag"))
            out.append(A.tube([c + b * size * 0.26 - d * size * 0.25, c + b * size * 0.26 + d * size * 0.25],
                              (r * 0.9, r * 0.5), rune_mat, n=4, up=tuple(b)))
    return out


def helix(a, b, r0, r1, turns, n=40, phase=0.0):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = normalize(b - a)
    s = normalize(np.cross(d, (0, 1, 0)) if abs(d[1]) < 0.9 else np.cross(d, (1, 0, 0)))
    f = np.cross(s, d)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        ang = phase + 2 * math.pi * turns * t
        pts.append(a + (b - a) * t + (s * math.cos(ang) + f * math.sin(ang)) * (r0 + (r1 - r0) * t))
    return pts


# ================================================================================================= build
def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(P(V, F, "BH_Cloth_Primary", "body"), weights=C.ROBE_W)
    C.robe_top(sb, "BH_Cloth_Primary", trim="BH_DarkSteel", g=G, rows=TORSO)
    C.robe_skirt(sb, "BH_Cloth_Primary", trim="BH_DarkSteel", flare=0.13, folds=0.012, g=G - 0.004)
    iron_bands(sb)
    scapular(sb)
    belt_chains(sb)
    head(sb)
    for s in ("L", "R"):
        C.bell_sleeve(sb, s, "BH_Cloth_Primary", trim="BH_DarkSteel", cuff_r=0.082, end=0.74)
        sleeve_chain(sb, s)
        K.add_fist(sb, s, "BH_Leather", "BH_Leather", gauntlet=False)
    K.trousers(sb, "BH_Cloth_Secondary", loose=0.9)
    K.boots(sb, "BH_Leather", "BH_DarkSteel", shaft_top=0.4, cuff=False, wraps="BH_DarkSteel")
    censer(sb)
    K.add_weapon(sb, "R", rune_rod(SCALE))


def iron_bands(sb):
    rows = [(r[0], r[1] + G + 0.006, r[2] + G + 0.006, r[3] + G + 0.006, r[4]) for r in TORSO]
    for z, h in ((1.33, 0.03), (1.18, 0.025)):
        V, F = K.band(rows, z, z + h, 0.008, -0.002, n=28)
        sb.add(P(V, F, "BH_DarkSteel", "hoop"), weights=C.ROBE_W)
    # wide iron belt with rivets
    V, F = K.band(rows, 0.97, 1.05, 0.014, -0.002, n=30)
    sb.add(P(V, F, "BH_DarkSteel", "belt"), "hips")
    for k in range(14):
        p, _ = K.on_ring(rows, 1.01, 0.016, k / 14)
        sb.add(A.ball(p, 0.007, "BH_Steel", n=5, rings=3), "hips")
    # riveted iron lames down the skirt (front, per leg) + hoops low on the skirt, per panel
    for side, sx in (("L", 1), ("R", -1)):
        for back in (False, True):
            w = C.robe_panel_w(sb, side, back)
            for x in (0.05, 0.12):
                z0, z1 = 0.94, 0.42
                pts = []
                for z in np.linspace(z0, z1, 5):
                    t = (1.07 - z) / (1.07 - 0.14)
                    fl = 0.13 * t
                    yy = (0.098 + G - 0.004 + fl) if not back else (0.1 + G - 0.004 + fl * 1.1)
                    pts.append((sx * x * (1 + 1.2 * t), (-1 if not back else 1) * (yy * 0.96 + 0.012), z))
                sb.add(K.strip(pts, 0.03, 0.006, "BH_DarkSteel", ups=[(0, -1 if not back else 1, 0)] * 5),
                       weights=w)


def scapular(sb):
    """Black scapular panels front and back; the Kharvenn emblem (a circle of iron chain) on the chest."""
    rows = [(r[0], r[1] + G + 0.014, r[2] + G + 0.014, r[3] + G + 0.014, r[4]) for r in TORSO]
    for front in (True, False):
        def fn(u, v, front=front):
            z = 1.5 - 1.06 * v
            hw = 0.1 - 0.015 * v
            x = (u - 0.5) * 2 * hw
            if z >= 1.0:
                y = front_y(rows, x, z) - 0.004 if front else back_y(rows, x, z) + 0.004
            else:
                y0 = front_y(rows, x, 1.0) - 0.004 if front else back_y(rows, x, 1.0) + 0.004
                y = y0 + (-1 if front else 1) * (0.045 + 0.12 * (1.0 - z))
            return (x, y, z)
        V, F = M.grid(fn, 5, 10)
        p = P(V, F, "BH_Cloth_Secondary", "scapular")
        if not front:
            p.flip()
        sb.add(M.solidify(p, 0.006, offset=1.0), weights=lambda V: [
            {"chest": 1.0} if v[2] > 1.3 else ({"spine": 1.0} if v[2] > 1.12 else
                                               ({"hips": 1.0} if v[2] > 0.98 else
                                                {"hips": 0.55, "thigh.L": 0.225, "thigh.R": 0.225})) for v in V])
    zc = 1.34
    yc = front_y(rows, 0, zc) - 0.012
    ring = [np.array([0.06 * math.cos(a), yc, zc + 0.06 * math.sin(a)]) for a in np.linspace(0, 2 * math.pi, 15)]
    for prt in chain(ring, size=0.03, r=0.0045, mat="BH_Steel"):
        sb.add(prt, "chest")
    sb.add(A.tube([(0, yc - 0.002, zc - 0.035), (0, yc - 0.002, zc + 0.035)], (0.006, 0.003), "BH_Emissive", n=4,
                  up=(0, -1, 0)), "chest")
    sb.add(A.tube([(-0.025, yc - 0.002, zc + 0.012), (0, yc - 0.002, zc - 0.01), (0.025, yc - 0.002, zc + 0.012)],
                  (0.005, 0.003), "BH_Emissive", n=4, up=(0, -1, 0)), "chest")


def belt_chains(sb):
    rows = [(r[0], r[1] + G + 0.03, r[2] + G + 0.03, r[3] + G + 0.03, r[4]) for r in TORSO]
    for k, (frac, ln) in enumerate(((0.12, 0.42), (0.3, 0.34), (0.62, 0.38), (0.84, 0.46))):
        p, ang = K.on_ring(rows, 1.0, 0.0, frac)
        out = normalize(np.array([p[0], p[1], 0.0]))
        pts = [p, p + out * 0.03 + np.array([0, 0, -ln * 0.5]), p + out * 0.05 + np.array([0, 0, -ln])]
        side = "L" if p[0] > 0 else "R"
        w = C.robe_panel_w(sb, side, p[1] > 0, leg_max=0.5)
        for prt in chain(pts, size=0.042, r=0.0055, runes=(3,) if k % 2 else ()):
            sb.add(prt, weights=w)
        # rune weight
        e = np.array(pts[-1]) + np.array([0, 0, -0.04])
        V, F = M.lathe([(0, -0.045), (0.022, -0.04), (0.026, 0.0), (0.02, 0.035), (0, 0.04)], 8)
        sb.add(P(V, F, "BH_DarkSteel", "weight").move(e), weights=w)
        sb.add(A.tube([e + out * 0.026 + (0, 0, -0.025), e + out * 0.026 + (0, 0, 0.022)], (0.005, 0.0025),
                      "BH_Emissive", n=4, up=tuple(out)), weights=w)


def sleeve_chain(sb, s):
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    w = sb.seg(["chest", "shoulder." + s, ua, fa, ha], power=9)
    pts = helix(el + (wr - el) * 0.05, el + (wr - el) * 0.62, 0.074, 0.084, 1.6, n=24, phase=0.5)
    for prt in chain(pts, size=0.042, r=0.0055, runes=(2, 7)):
        sb.add(prt, fa)
    pts = helix(sh + (el - sh) * 0.45, sh + (el - sh) * 0.95, 0.07, 0.068, 0.7, n=12, phase=2.0)
    for prt in chain(pts, size=0.042, r=0.0055, runes=(2,)):
        sb.add(prt, weights=w)


# ================================================================================================= head
MITRE_W = K.zspec_w([(1.49, "chest"), (1.54, "neck"), (1.57, "neck"), (1.62, "head")])


def head(sb):
    K.neck_and_head(sb, skin="BH_Skin", eyes="BH_Shadow", eye_glow="BH_Emissive", nose=True)
    C.hood(sb, "BH_Cloth_Secondary", trim="BH_DarkSteel", rows=C.HOOD_DEEP)
    # chain veil hanging from the brim across the face
    for k, x in enumerate(np.linspace(-0.066, 0.066, 5)):
        ztop = 1.77 - 0.03 * (abs(x) / 0.07) ** 2
        y = -0.128 + 0.03 * (abs(x) / 0.07) ** 2
        for prt in chain([(x, y, ztop), (x, y - 0.006, ztop - 0.15 + 0.03 * (k % 2))], size=0.03, r=0.0038):
            sb.add(prt, "head")
    # tall peaked iron mitre rising from the hood: front + back plates leaning together
    zb = 1.79
    o = np.array([(-0.105, 0.0), (0.105, 0.0), (0.095, 0.12), (0.06, 0.25), (0.0, 0.34), (-0.06, 0.25),
                  (-0.095, 0.12)])
    for sy in (-1, 1):
        V, F = M.prism(o, 0.012, axis="y")
        pl = P(V, F, "BH_DarkSteel", "mitre").rot(Rx(sy * 8)).move((0, sy * 0.045 - 0.01, zb))
        sb.add(M.bevel(M.recalc_normals(pl), 0.003, 1), "head")
        # rim band along the edge
        edge = [np.array([x, 0.0, z]) for x, z in o[[1, 2, 3, 4, 5, 6, 0]]]
        pts = [Rx(sy * 8) @ e + np.array([0, sy * 0.045 - 0.01 + sy * 0.008, zb]) for e in edge]
        sb.add(A.tube(pts, (0.007, 0.006), "BH_Steel", n=4, cap=False), "head")
        # rune: a spine with chevrons, white
        yr = sy * 0.045 - 0.01 + sy * 0.009
        rune = [[(0.0, 0.05), (0.0, 0.27)], [(-0.04, 0.1), (0.0, 0.14), (0.04, 0.1)],
                [(-0.03, 0.18), (0.0, 0.21), (0.03, 0.18)]]
        for ln in rune:
            pts = [Rx(sy * 8) @ np.array([x, 0.0, z]) + np.array([0, yr, zb]) for x, z in ln]
            sb.add(A.tube(pts, (0.0055, 0.003), "BH_Emissive", n=4, up=(0, sy, 0)), "head")
    V, F = M.lathe([(0.11, -0.02), (0.118, -0.01), (0.118, 0.025), (0.11, 0.032)], 16, cap=False)
    sb.add(P(V, F, "BH_DarkSteel", "mitreband").scale((1.0, 0.85, 1.0)).move((0, -0.005, zb)), "head")
    # lappets: two black cloth strips hanging from the mitre's back down the shoulders
    for sx in (1, -1):
        pts = [(sx * 0.06, 0.1, 1.8), (sx * 0.08, 0.15, 1.62), (sx * 0.1, 0.17, 1.48)]
        sb.add(K.strip(pts, 0.05, 0.006, "BH_Cloth_Secondary", ups=[(0, 1, 0)] * 3), weights=MITRE_W)


# ================================================================================================= censer + rod
def censer(sb):
    """Handle in the left fist (weapon.L); chain + an iron cage-censer (white glow within, grey smoke above) hang
    straight down from the grip in the modelling pose, on the `censer` bone."""
    V, F = M.lathe([(0.0, -0.05), (0.012, -0.05), (0.013, 0.05), (0.0, 0.05)], 8)
    K.add_weapon(sb, "L", [P(V, F, "BH_DarkSteel", "grip")])
    g = sb.head("weapon.L")
    L = CHAIN / SCALE
    for prt in chain([g + (0, 0, -0.02), g + (0, 0, -0.03 - L)], size=0.042, r=0.0055):
        sb.add(prt, "censer")
    c = g + (0, 0, -0.03 - L - 0.1)
    # cage: top cap, bottom bowl, 6 bars, glow core inside
    V, F = M.lathe([(0.0, 0.1), (0.03, 0.095), (0.06, 0.07), (0.07, 0.055), (0.0, 0.055)], 10)
    sb.add(P(V, F, "BH_DarkSteel", "cap").move(c), "censer")
    V, F = M.lathe([(0.0, -0.1), (0.03, -0.095), (0.065, -0.065), (0.075, -0.04), (0.0, -0.04)], 10)
    sb.add(P(V, F, "BH_DarkSteel", "bowl").move(c), "censer")
    for k in range(6):
        a = 2 * math.pi * k / 6
        pts = [c + (0.072 * math.cos(a), 0.072 * math.sin(a), -0.045), c + (0.08 * math.cos(a), 0.08 * math.sin(a), 0.0),
               c + (0.068 * math.cos(a), 0.068 * math.sin(a), 0.06)]
        sb.add(A.tube(pts, 0.0065, "BH_DarkSteel", n=4), "censer")
    sb.add(A.ball(c + (0, 0, 0.005), 0.05, "BH_Emissive", n=10, rings=6), "censer")
    V, F = M.lathe([(0.0, -0.13), (0.012, -0.12), (0.006, -0.1), (0.0, -0.1)], 6)
    sb.add(P(V, F, "BH_DarkSteel", "finial").move(c), "censer")
    # smoke puffs above the lid
    for k, (dx, dz, r) in enumerate(((0.0, 0.12, 0.03), (0.02, 0.16, 0.026), (-0.01, 0.2, 0.022))):
        sb.add(A.ball(c + (dx, 0.01 * k, dz), r, "BH_Bone", n=7, rings=4, scale=(1.0, 1.0, 0.8)), "censer")


def rune_rod(s=1.0):
    """Weapon space (grip at origin, +Z up the rod): dark iron shaft -0.4..0.62, chain wound round its upper half,
    a caged iron head holding a white rune-core, a spike on top, a heavy pommel."""
    parts = []
    V, F = M.lathe([(0, -0.42), (0.024, -0.42), (0.026, -0.38), (0.016, -0.34), (0.016, 0.6), (0.0, 0.62)], 8)
    parts.append(P(V, F, "BH_DarkSteel", "shaft"))
    parts.append(K.WP._grip(-0.09, 0.09, 0.0185, 5, mat="BH_Leather"))
    pts = helix((0, 0, 0.18), (0, 0, 0.56), 0.022, 0.022, 3.0, n=30)
    for prt in chain(pts, size=0.026, r=0.0035, runes=(4, 12)):
        parts.append(prt)
    hz = 0.72
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4
        pts = [(0.02 * math.cos(a), 0.02 * math.sin(a), hz - 0.11), (0.06 * math.cos(a), 0.06 * math.sin(a), hz),
               (0.02 * math.cos(a), 0.02 * math.sin(a), hz + 0.11)]
        parts.append(A.tube(pts, [0.009, 0.011, 0.009], "BH_DarkSteel", n=5))
        q = np.array([0.06 * math.cos(a), 0.06 * math.sin(a), hz])
        parts.append(A.taper([q, q + np.array([math.cos(a), math.sin(a), 0.3]) * 0.04], 0.008, 0.0015,
                             "BH_DarkSteel", n=4))
    for z in (hz - 0.11, hz + 0.11):
        V, F = M.lathe([(0.0, z - 0.014), (0.028, z - 0.01), (0.03, z), (0.028, z + 0.01), (0, z + 0.014)], 8)
        parts.append(P(V, F, "BH_Steel", "collar"))
    parts.append(A.ball((0, 0, hz), 0.035, "BH_Emissive", n=8, rings=6, scale=(1, 1, 1.3)))
    parts.append(A.taper([(0, 0, hz + 0.12), (0, 0, hz + 0.24)], 0.014, 0.001, "BH_DarkSteel", n=6))
    for p in parts:
        p.V = p.V * s
    return parts
