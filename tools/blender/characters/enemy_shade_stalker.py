"""Shade Stalker (corrupted): very lean, long-limbed figure bound head to foot in smoke-black cloth strips, a tight
wrapped hood with two violet eye-slits, a hood tail and ragged strips trailing from the forearms and the hips,
long curved daggers in both hands. Kit: enemy_bandit_cutthroat; hood: enemy_ashen_cultist."""
import math
import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C

SCALE = 1.80 / 1.915
PROPS = proportions(SCALE, upper_len=0.31 * SCALE, fore_len=0.30 * SCALE, hand_len=0.11 * SCALE,
                    shoulder_x=0.175 * SCALE, hip_x=0.09 * SCALE, neck_len=0.14 * SCALE)
PALETTE = "shade_stalker"
PALETTE_COLORS = {
    "BH_Shadow": ((0.03, 0.026, 0.045), 0.0, 0.75, (0.05, 0.02, 0.1), 0.5, 1.0),   # smoke-black body wraps
    "BH_Cloth_Primary": ((0.06, 0.05, 0.08), 0.0, 0.85, None, 0.0, 1.0),          # lighter binding strips
    "BH_Cloth_Secondary": ((0.02, 0.018, 0.028), 0.0, 0.9, None, 0.0, 1.0),       # face wrap / hood lining
    "BH_Emissive": ((0.65, 0.35, 1.0), 0.0, 0.4, (0.7, 0.35, 1.0), 7.0, 1.0),     # violet eyes / blade runes
    "BH_Skin": ((0.2, 0.19, 0.22), 0.0, 0.55, None, 0.0, 1.0),                   # grey fingers
    "BH_DarkSteel": ((0.1, 0.1, 0.12), 1.0, 0.35, None, 0.0, 1.0),               # blackened blades
    "BH_Leather": ((0.045, 0.035, 0.035), 0.0, 0.7, None, 0.0, 1.0),
}
CLIPS = ["dagger_heavy", "dagger_1"]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


# very lean torso (z, rx, ryf, ryb, keel) - slightly tapered waist, narrow chest
TORSO = [
    (0.96, 0.125, 0.085, 0.09, 0.00),
    (1.04, 0.11, 0.08, 0.082, 0.02),
    (1.14, 0.108, 0.084, 0.085, 0.04),
    (1.25, 0.125, 0.095, 0.092, 0.08),
    (1.35, 0.14, 0.1, 0.098, 0.06),
    (1.43, 0.145, 0.095, 0.098, 0.03),
    (1.49, 0.122, 0.08, 0.086, 0.00),
    (1.53, 0.07, 0.058, 0.06, 0.00),
]
TORSO_W = K.TORSO_W
HEAD_W = K.zspec_w([(1.52, "chest"), (1.56, "neck"), (1.6, "neck"), (1.64, "head")])


def spiral(sb, rows, z0, z1, turns, g, w, mat, phase=0.0, weights=None, bone=None, n_per=14):
    n = int(turns * n_per) + 1
    pts, ups = [], []
    for i in range(n):
        t = i / (n - 1)
        z = z0 + (z1 - z0) * t
        f = (phase + turns * t) % 1.0
        q = K.ring_frac(rows, z, g, [f])[0]
        pts.append(q)
        a = 2 * math.pi * f - math.pi / 2
        ups.append((math.cos(a), math.sin(a), 0))
    p = K.strip(pts, w, 0.006, mat, ups=ups, n=4)
    sb.add(p, bone, weights)


def limb_wrap(sb, a, b, r0, r1, mat, turns=4, w=0.028, phase=0.0, bone=None, weights=None):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = normalize(b - a)
    side = normalize(np.cross(d, (0, 1, 0))) if abs(d[1]) < 0.9 else np.array([1.0, 0, 0])
    fw = np.cross(side, d)
    n = int(turns * 9) + 1
    pts, ups = [], []
    for i in range(n):
        t = i / (n - 1)
        ang = 2 * math.pi * (turns * t + phase)
        nrm = side * math.cos(ang) + fw * math.sin(ang)
        pts.append(a + (b - a) * t + nrm * (r0 + (r1 - r0) * t))
        ups.append(nrm)
    V, F = M.tube(pts, [(w / 2, 0.003)] * n, n=4, up=[np.asarray(u) for u in ups], p=3.0)
    sb.add(M.Part(V, F, mat, name="limbwrap"), bone, weights)


def rag(pts_top, direction, length, width, mat, sway=(0, 0, 0), n=5, normal=None):
    """Ragged hanging cloth strip starting at pts_top going along direction, tapering to a point."""
    d = normalize(direction)
    pts, prof = [], []
    for i in range(n):
        t = i / (n - 1)
        pts.append(np.asarray(pts_top, float) + d * length * t + np.asarray(sway) * math.sin(math.pi * t * 0.9) * t)
        prof.append((width / 2 * (1 - 0.75 * t ** 1.5), 0.003))
    if normal is None:
        up = normalize(np.cross(d, (0, 0, 1))) if abs(d[2]) < 0.9 else np.array([0, 1.0, 0])
    else:
        nn = np.asarray(normal, float)
        up = normalize(nn - d * np.dot(nn, d))
    V, F = M.tube(pts, prof, n=4, up=up, p=3.0)
    return M.Part(V, F, mat, name="rag")


def build(body):
    sb = K.SB(body, SCALE)
    # torso wrapped in strips
    V, F = torso_loft(K.rows_between(TORSO, 0.9, 1.53, n_extra=2), n=22, cap1=True, cap0=True)
    sb.add(M.Part(V, F, "BH_Shadow", name="torso"), weights=TORSO_W)
    for ph, t0, t1 in ((0.0, 0.98, 1.5), (0.5, 1.0, 1.45)):
        spiral(sb, TORSO, t0, t1, 3.0, 0.006, 0.035, "BH_Cloth_Primary", phase=ph, weights=TORSO_W)
    # crossed binding over the chest
    for sx in (1, -1):
        pts = [(sx * 0.1, front_y(TORSO, 0.1, 1.47) - 0.012, 1.47), (0, front_y(TORSO, 0, 1.3) - 0.014, 1.3),
               (-sx * 0.1, front_y(TORSO, 0.1, 1.12) - 0.012, 1.12)]
        sb.add(K.strip(pts, 0.04, 0.007, "BH_Cloth_Primary"), weights=TORSO_W)
    # tattered strip skirt from the hips
    rng = np.random.default_rng(3)
    for k in range(12):
        f = (k + 0.3 * rng.random()) / 12
        top = K.ring_frac(TORSO, 1.0, 0.012, [f])[0]
        a = 2 * math.pi * f - math.pi / 2
        out = np.array([math.cos(a), math.sin(a), 0])
        ln = 0.3 + 0.28 * rng.random() + (0.12 if 0.35 < f < 0.65 else 0.0)
        sb.add(rag(top, out * 0.25 + np.array([0, 0.1, -1.0]), ln, 0.075, "BH_Shadow", normal=out),
               weights=sb.skirt(1.0, 0.55, max_leg=0.75, center_w=0.05, shin_from=0.6))
    # head: tight hood + face wrap with eye slits
    V, F = M.tube([(0, 0.0, 1.47), (0, -0.006, 1.56), (0, -0.012, 1.64)], [(0.05, 0.048), (0.046, 0.044), (0.046, 0.046)],
                  n=10, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Shadow", name="neck"), weights=HEAD_W)
    head_rows = [(r[0] + 0.03, r[1] * 0.95, r[2] * 1.02, r[3] * 0.95, r[4], r[5] - 0.012) for r in K.HEAD]
    V, F = torso_loft(head_rows, n=20, p=2.1)
    sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="head"), "head")
    hood = [(z + 0.03, rx * 0.88, ryf * 0.9, ryb * 0.95, cy - 0.01, th * 0.75) for (z, rx, ryf, ryb, cy, th) in
            C.HOOD_DEEP]
    C.hood(sb, "BH_Shadow", trim=None, rows=hood, lining="BH_Cloth_Secondary")
    for sx in (1, -1):
        c = np.array([sx * 0.028, -0.092, 1.728])
        V, F = M.box(0.034, 0.012, 0.009)
        sb.add(M.Part(V, F, "BH_Emissive", name="eye").rot(Ry(-sx * 14)).rot(Rz(sx * 12)).move(c), "head")
    # face bands across the wrap
    for z in (1.66, 1.77):
        V, F = K.band([(r[0], r[1], r[2], r[3], r[4], r[5]) for r in head_rows], z, z + 0.022, 0.006, -0.002, n=20,
                      p=2.1)
        sb.add(M.Part(V, F, "BH_Cloth_Primary", name="faceband"), "head")
    # hood tail down the back
    tail = np.array([(0, 0.1, 1.83), (0.005, 0.118, 1.7), (0.012, 0.13, 1.57), (0.02, 0.118, 1.44),
                     (0.03, 0.112, 1.3)])
    V, F = M.tube(tail, [(0.05, 0.004), (0.048, 0.004), (0.04, 0.004), (0.028, 0.004), (0.008, 0.003)], n=4,
                  up=(0, 1, 0), p=3.0)
    sb.add(M.Part(V, F, "BH_Shadow", name="hood_tail"), weights=K.zspec_w([(1.45, "chest"), (1.6, "neck"),
                                                                          (1.72, "head")]))
    # arms: thin wrapped limbs, grey clawed fingers, trailing rags
    for s in ("L", "R"):
        K.bare_arm(sb, s, skin="BH_Shadow", r_up=0.04, r_fore=0.036, r_wrist=0.028, bulk=0.9)
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        limb_wrap(sb, sb.head(ua) + (sb.head(fa) - sb.head(ua)) * 0.1, sb.head(fa), 0.042, 0.038, "BH_Cloth_Primary",
                  turns=3, bone=ua)
        limb_wrap(sb, sb.head(fa), sb.head(ha), 0.038, 0.03, "BH_Cloth_Primary", turns=3.5, phase=0.3, bone=fa)
        K.add_fist(sb, s, "BH_Shadow", "BH_Skin")
        sx = 1 if s == "L" else -1
        for u, ln, dy in ((0.35, 0.42, 0.06), (0.6, 0.32, 0.1), (0.15, 0.36, 0.03)):
            top = sb.head(fa) + (sb.head(ha) - sb.head(fa)) * u + np.array([sx * 0.03, 0.02, 0])
            sb.add(rag(top, (sx * 0.25, 0.55 + dy, -1.0), ln, 0.05, "BH_Shadow", sway=(0, 0.04, 0),
                       normal=(sx, 0.3, 0)), fa)
    # legs: thin wrapped legs, wrapped feet
    for s in ("L", "R"):
        th, sh, ft = "thigh." + s, "shin." + s, "foot." + s
        h, k, a = sb.head(th), sb.head(sh), sb.tail(sh)
        V, F = M.tube([h + (0, 0, 0.05), h + (k - h) * 0.5, k, k + (a - k) * 0.5, a + (0, 0, 0.03)],
                      [(0.07, 0.074), (0.058, 0.062), (0.045, 0.05), (0.045, 0.05), (0.034, 0.038)], n=10, up=(0, -1, 0))
        sb.add(M.Part(V, F, "BH_Shadow", name="leg"), weights=sb.seg([th, sh], power=10))
        limb_wrap(sb, h + (k - h) * 0.3, k + (a - k) * 0.05, 0.062, 0.048, "BH_Cloth_Primary", turns=3, bone=th)
        limb_wrap(sb, k + (a - k) * 0.15, a + (0, 0, 0.04), 0.048, 0.038, "BH_Cloth_Primary", turns=4, bone=sh,
                  phase=0.4)
        hx = h[0]
        V, F = M.tube([(hx, 0.03, 0.09), (hx, -0.02, 0.05), (hx, -0.1, 0.03)], [(0.036, 0.04), (0.04, 0.035),
                      (0.034, 0.024)], n=8, up=(0, 0, 1))
        sb.add(M.Part(V, F, "BH_Shadow", name="foot"), ft)
        V, F = M.tube([(hx, -0.1, 0.03), (hx, -0.18, 0.018), (hx, -0.21, 0.012)], [(0.034, 0.024), (0.03, 0.017),
                      (0.012, 0.008)], n=8, up=(0, 0, 1))
        sb.add(M.Part(V, F, "BH_Shadow", name="toe"), "toe." + s)
    # daggers: long curved, blackened, a violet rune line on the flat
    for s in ("L", "R"):
        K.add_weapon(sb, s, shade_dagger())


def shade_dagger():
    parts = K.curved_knife(length=0.44, width=0.038, curve=0.1, mat="BH_DarkSteel", grip_mat="BH_Shadow")
    # rune groove on both flats
    for sy in (1, -1):
        pts = []
        for u in np.linspace(0.1, 0.7, 6):
            z = 0.05 + 0.44 * u
            pts.append((-0.1 * u ** 2 + 0.002, sy * 0.0052 * (1 - 0.6 * u), z))
        V, F = M.tube(pts, [(0.0028, 0.0014)] * 6, n=4, up=(0, sy, 0))
        parts.append(M.Part(V, F, "BH_Emissive", name="rune"))
    return parts
