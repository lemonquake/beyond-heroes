"""Aegis Acolyte (bh-013, Builder A2; temple warder that shields its allies): a ~1.85 m acolyte in floor-length white
robes with gold hems, a light gilded breastplate (pale polished plate, gold rims, a gold sun boss) and small domed
gilt pauldrons, a gold-ochre tabard with a gold border hanging in front, and a TALL pointed white hood trimmed in
gold (gold band round the hood and a gold ridge up its back) shading a stern face. Left arm: a tall kite shield
(white face, thick gold rim) with a glowing golden lantern-window in its centre behind a gold lattice. Right hand:
a flanged mace with a gold-banded haft.

Clips: shield_bash, sword_1, sword_2, cast_quick, cast_area, taunt (+ the shared enemy base clips).
Kits: enemy_bandit_cutthroat (SB), enemy_ashen_cultist (robe / hood / sleeves), kit_a_common, kit_e_orrery."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, smoothstep
from bh_math import normalize, Rx
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C
import enemy_hollow_soldier as HS
import kit_a_common as A
import kit_e_orrery as O

SCALE = 1.85 / 1.9           # hood crown ~1.9 standard units (the peak rises a little higher)
PROPS = proportions(SCALE, shoulder_x=0.175 * SCALE, hip_x=0.09 * SCALE, upper_len=0.295 * SCALE,
                    fore_len=0.275 * SCALE)
PREVIEW_HEIGHT = 2.3
PALETTE = "aegis_acolyte"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.8, 0.78, 0.72), 0.0, 0.8, None, 0.0, 1.0),        # white temple robe, hood
    "BH_Cloth_Secondary": ((0.6, 0.4, 0.1), 0.0, 0.75, None, 0.0, 1.0),       # gold-ochre tabard
    "BH_Gold": ((0.9, 0.64, 0.2), 1.0, 0.25, None, 0.0, 1.0),                 # gilt trims, rims, lattice
    "BH_Steel": ((0.86, 0.85, 0.8), 0.55, 0.38, None, 0.0, 1.0),              # pale polished plate, mace head
    "BH_Skin": ((0.62, 0.47, 0.38), 0.0, 0.55, None, 0.0, 1.0),
    "BH_Leather": ((0.36, 0.27, 0.17), 0.0, 0.65, None, 0.0, 1.0),            # tan belt, boots, grips
    "BH_Wood": ((0.2, 0.13, 0.07), 0.0, 0.7, None, 0.0, 1.0),                 # shield core edge
    "BH_Shadow": ((0.05, 0.04, 0.035), 0.0, 0.8, None, 0.0, 1.0),             # hood interior, sockets
    "BH_Emissive": ((1.0, 0.75, 0.3), 0.0, 0.4, (1.0, 0.72, 0.28), 8.0, 1.0),  # lantern-window, sun boss, eyes
}
CLIPS = ["shield_bash", "sword_1", "sword_2", "cast_quick", "cast_area", "taunt"]

TORSO = [(r[0], r[1] * 0.95, r[2] * 0.92, r[3] * 0.95, r[4] * 0.7) for r in K.TORSO]
G = 0.012
CHEST_W = K.zspec_w([(1.12, "spine"), (1.3, "chest")])

# tall pointed hood: z, rx, ry_front, ry_back, cy, opening half-angle (deg)
HOOD = [
    (1.500, 0.158, 0.13, 0.145, 0.015, 30),
    (1.555, 0.128, 0.126, 0.134, 0.0, 40),
    (1.620, 0.118, 0.132, 0.132, -0.012, 44),
    (1.680, 0.118, 0.136, 0.134, -0.02, 44),
    (1.740, 0.114, 0.136, 0.134, -0.018, 40),
    (1.795, 0.103, 0.128, 0.128, -0.008, 32),
    (1.845, 0.084, 0.106, 0.112, 0.0, 22),
    (1.885, 0.066, 0.086, 0.094, 0.01, 14),
    (1.912, 0.042, 0.055, 0.064, 0.018, 6),
    (1.927, 0.014, 0.016, 0.022, 0.024, 2),
]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="body"), weights=C.ROBE_W)
    C.robe_top(sb, "BH_Cloth_Primary", trim="BH_Gold", g=G, rows=TORSO, v_open=0.0)
    C.robe_skirt(sb, "BH_Cloth_Primary", trim="BH_Gold", z_top=1.07, z_bot=0.05, flare=0.17, folds=0.014,
                 g=G - 0.02)
    tabard(sb)
    breastplate(sb)
    K.neck_and_head(sb, skin="BH_Skin", eyes="BH_Shadow", eye_glow="BH_Emissive")
    hood(sb)
    for s in ("L", "R"):
        C.bell_sleeve(sb, s, "BH_Cloth_Primary", trim="BH_Gold", cuff_r=0.066, end=0.55)
        pauldron(sb, s)
        bracer(sb, s)
        K.add_fist(sb, s, "BH_Leather", "BH_Leather", scale=0.97)
    K.trousers(sb, "BH_Cloth_Primary", loose=0.85)
    K.boots(sb, "BH_Leather", "BH_Leather", shaft_top=0.4, cuff=False)
    K.add_weapon(sb, "L", kite_shield())
    K.add_weapon(sb, "R", flanged_mace())


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


def _skirt_front(x, z):
    """y of the robe skirt front at (x, z), a little proud of it."""
    t = max(0.0, (1.07 - z) / 1.02)
    ry = 0.098 + (G - 0.02) + 0.17 * t
    rx = 0.15 + (G - 0.02) + 0.17 * t
    k = min(abs(x) / rx, 0.95)
    return -ry * (1 - k ** 2.2) ** (1 / 2.2) - 0.028


def tabard(sb):
    """Gold-ochre tabard panel hanging from the belt to below the knee in front, gold border and a sun disc."""
    z0, z1 = 1.1, 0.3

    def fn(u, v):
        z = z0 + (z1 - z0) * v
        hw = 0.085 + 0.03 * v
        x = (u - 0.5) * 2 * hw
        y = _skirt_front(x, z) if z < 1.04 else front_y(TORSO, x * 0.8, z) - G - 0.028
        return (x, y, z)
    V, F = M.grid(fn, 5, 10)
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Secondary", name="tabard"), 0.007, offset=1.0).flip(),
           weights=centre_w(0.5))
    for sx in (-1, 1):
        pts = [np.array(fn(0.5 + sx * 0.5, v)) + (0, -0.006, 0) for v in np.linspace(0, 1, 8)]
        sb.add(A.tube(pts, (0.011, 0.005), "BH_Gold", n=4, up=(0, -1, 0)), weights=centre_w(0.5))
    bot = [np.array(fn(u, 1.0)) + (0, -0.006, 0.01) for u in np.linspace(0, 1, 5)]
    sb.add(A.tube(bot, (0.005, 0.012), "BH_Gold", n=4, up=(0, 0, 1)), weights=centre_w(0.5))
    c = np.array(fn(0.5, 0.35)) + (0, -0.01, 0)
    sb.add(O.disc(c, (0, -1, 0), 0.042, 0.008, "BH_Gold", n=12), weights=centre_w(0.5))
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = np.array([math.cos(a), 0, math.sin(a)])
        sb.add(A.shard(c + d * 0.04, d, 0.035 if k % 2 == 0 else 0.022, 0.009, "BH_Gold", sides=4, up=(0, -1, 0)),
               weights=centre_w(0.5))
    # belt with a gold buckle
    K.belt(sb, TORSO, z=1.02, h=0.05, g=G + 0.022, mat="BH_Leather", buckle="BH_Gold")


def breastplate(sb):
    """Light cuirass (pale polished plate) with gold rims top and bottom and a gold sun boss with a glowing heart."""
    V, F = K.band(TORSO, 1.13, 1.44, G + 0.032, G + 0.014, n=28)
    sb.add(M.Part(V, F, "BH_Steel", name="cuirass"), weights=CHEST_W)
    for z0, z1 in ((1.12, 1.15), (1.425, 1.455)):
        V, F = K.band(TORSO, z0, z1, G + 0.042, G + 0.02, n=28)
        sb.add(M.Part(V, F, "BH_Gold", name="rim"), weights=CHEST_W)
    # central keel line + sun boss
    pts = [(0, front_y(TORSO, 0, z) - G - 0.036, z) for z in np.linspace(1.16, 1.42, 6)]
    sb.add(A.tube(pts, (0.006, 0.006), "BH_Gold", n=4), weights=CHEST_W)
    c = np.array([0, front_y(TORSO, 0, 1.33) - G - 0.042, 1.33])
    sb.add(O.disc(c, (0, -1, 0.15), 0.045, 0.012, "BH_Gold", n=14), "chest")
    sb.add(O.ball(c + (0, -0.008, 0), 0.02, "BH_Emissive", n=8, rings=4), "chest")
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8
        d = np.array([math.cos(a), 0, math.sin(a)])
        sb.add(A.shard(c + d * 0.043, d, 0.03, 0.008, "BH_Gold", sides=4, up=(0, -1, 0)), "chest")


def pauldron(sb, s):
    """Small domed gilt pauldron: pale plate cap, gold rim."""
    sx = 1 if s == "L" else -1
    sh = sb.head("upper_arm." + s)
    c = sh + np.array([sx * 0.0, 0.0, 0.035])
    n = normalize(np.array([sx * 0.55, 0, 1.0]))
    sb.add(O.dome(c, n, 0.085, "BH_Steel", n=14, rings=4, depth=0.6), "shoulder." + s)
    sb.add(O.ring(c, n, 0.082, 0.011, "BH_Gold", n=16, m=4), "shoulder." + s)
    sb.add(O.ball(c + n * 0.05, 0.013, "BH_Gold", n=6, rings=4), "shoulder." + s)


def bracer(sb, s):
    """Gold bracer on the forearm below the sleeve."""
    fa, ha = "forearm." + s, "hand." + s
    el, wr = sb.head(fa), sb.head(ha)
    d = normalize(wr - el)
    V, F = M.tube([el + (wr - el) * 0.55, wr - d * 0.005], [(0.041, 0.043), (0.036, 0.038)], n=10, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Gold", name="bracer"), fa)


# ================================================================================================= head
def hood(sb):
    """Tall pointed white hood, gold edge trim, a gold band round it and a gold ridge up the back to the peak."""
    C.hood(sb, "BH_Cloth_Primary", trim="BH_Gold", rows=HOOD, lining="BH_Shadow")
    W = C.HOOD_W
    # band round the hood at z 1.80 (open at the face)
    z, rx, ryf, ryb, cy, th = HOOD[5]
    pts = []
    for u in np.linspace(0, 1, 17):
        a = math.radians(th + (360 - 2 * th) * u)
        sa, ca = math.sin(a), math.cos(a)
        pts.append(((rx + 0.004) * sa, cy - ((ryf if ca > 0 else ryb) + 0.004) * ca, z))
    sb.add(A.tube(pts, (0.012, 0.007), "BH_Gold", n=4, up=(0, 0, 1)), weights=W)
    # ridge up the back
    ridge = [(0.0, r[4] + r[3] + 0.004, r[0]) for r in HOOD[3:]]
    sb.add(A.tube(ridge, (0.008, 0.012), "BH_Gold", n=4), weights=W)
    halo(sb)
    # small gold sun on the brow of the hood
    c = np.array([0.0, HOOD[6][4] - HOOD[6][2] - 0.01, HOOD[6][0] - 0.01])
    sb.add(O.disc(c, (0, -1, 0.35), 0.022, 0.008, "BH_Gold", n=10), weights=W)
    sb.add(O.ball(c + (0, -0.005, 0.0), 0.01, "BH_Emissive", n=6, rings=4), weights=W)


def halo(sb):
    """Gold sun-halo standing behind the hood (rigid on the head): an outer ring, an inner ring, 12 rays between them
    and 12 short spikes outside; a glowing band on the inner ring."""
    c = np.array([0.0, 0.2, 1.8])
    n = (0, 1, 0.12)
    sb.add(O.ring(c, n, 0.2, 0.013, "BH_Gold", n=28, m=4, flat=0.6), "head")
    sb.add(O.ring(c, n, 0.125, 0.009, "BH_Gold", n=22, m=4, flat=0.6), "head")
    sb.add(O.ring(c + (0, 0.004, 0), n, 0.125, 0.005, "BH_Emissive", n=22, m=4), "head")
    nn = normalize(np.array(n, float))
    u = normalize(np.cross(nn, (1, 0, 0)))
    v = np.cross(u, nn)
    for k in range(12):
        a = 2 * math.pi * k / 12
        d = u * math.cos(a) + v * math.sin(a)
        sb.add(A.tube([c + d * 0.13, c + d * 0.195], (0.009, 0.004), "BH_Gold", n=4, up=nn), "head")
        sb.add(A.shard(c + d * 0.205, d, 0.075 if k % 2 == 0 else 0.045, 0.012, "BH_Gold", sides=4, up=nn), "head")


# ================================================================================================= weapons
def kite_shield():
    """Tall kite shield (weapon space: handle at origin, face toward -Y): rounded top, long point, white face with a
    thick gold rim, a gold-framed arched lantern-window glowing warm gold at the centre behind a gold lattice,
    four gold studs."""
    parts = []
    hw, top, bot = 0.27, 0.42, -0.66
    pts = []
    for a in np.linspace(0, math.pi, 13):        # rounded top
        pts.append((hw * math.cos(a), 0.22 + (top - 0.22) * math.sin(a)))
    for u in np.linspace(0, 1, 12)[1:]:          # left side down to the point
        pts.append((-hw * (1 - u) ** 1.25, 0.22 + (bot - 0.22) * u))
    for u in np.linspace(0, 1, 12)[1:-1][::-1]:  # right side back up
        pts.append((hw * (1 - u) ** 1.25, 0.22 + (bot - 0.22) * u))
    o = np.array(pts)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    o = M.resample_closed(o, 48)
    curve = lambda x: 0.5 * x * x - 0.07            # sides bend back toward +Y
    V, F = M.plate_from_outline(o, 0.0, rings=6, bulge=0.04, axis="y")
    face = M.Part(V, F, "BH_Cloth_Primary", name="shield_face")
    face.warp(lambda v: (v[0], v[1] + curve(v[0]), v[2]))
    parts.append(M.solidify(face.copy().to(mat="BH_Wood").move((0, 0.002, 0)), 0.024, offset=-1.0))
    parts.append(face)
    rim = [(x, curve(x) - 0.006, z) for x, z in o] + [(o[0][0], curve(o[0][0]) - 0.006, o[0][1])]
    V, F = M.tube(rim, [(0.022, 0.026)] * len(rim), n=6, up=(0, -1, 0), cap0=False, cap1=False)
    parts.append(M.Part(V, F, "BH_Gold", name="rim"))
    # lantern-window: arched opening, glowing pane, gold frame, lattice
    wz0, wz1, ww = -0.14, 0.12, 0.085
    win = [(ww, wz0), (ww, wz1)]
    for a in np.linspace(0, math.pi, 9)[1:-1]:
        win.append((ww * math.cos(a), wz1 + 0.07 * math.sin(a)))
    win += [(-ww, wz1), (-ww, wz0)]
    w = np.array(win)
    yf = -0.04 - 0.07 - 0.012                      # in front of the bulged face centre
    V, F = M.prism(w[::-1] if 0.5 * np.sum(w[:, 0] * np.roll(w[:, 1], -1) - np.roll(w[:, 0], -1) * w[:, 1]) < 0
                   else w, 0.01, axis="y", center=yf + 0.004)
    parts.append(M.Part(V, F, "BH_Emissive", name="window"))
    fr = [(x, yf - 0.004, z) for x, z in win] + [(win[0][0], yf - 0.004, win[0][1])]
    V, F = M.tube(fr, [(0.016, 0.014)] * len(fr), n=5, up=(0, -1, 0), cap0=False, cap1=False)
    parts.append(M.Part(V, F, "BH_Gold", name="frame"))
    for x in (-ww / 3, ww / 3):
        parts.append(A.tube([(x, yf - 0.006, wz0), (x, yf - 0.006, wz1 + 0.06 * math.cos(x / ww * math.pi / 2))],
                            0.0055, "BH_Gold", n=4))
    for z in (-0.05, 0.05):
        parts.append(A.tube([(-ww, yf - 0.006, z), (ww, yf - 0.006, z)], 0.0055, "BH_Gold", n=4))
    # sill + hood over the window
    V, F = M.box(0.23, 0.03, 0.026, center=(0, yf - 0.006, wz0 - 0.02))
    parts.append(M.Part(V, F, "BH_Gold", name="sill"))
    parts.append(A.shard((0, yf - 0.006, wz1 + 0.085), (0, 0, 1), 0.07, 0.018, "BH_Gold", sides=4, up=(0, -1, 0)))
    # studs
    for (x, z) in ((0.0, 0.33), (0.0, -0.42), (-0.17, 0.06), (0.17, 0.06), (0.0, -0.3)):
        parts.append(A.ball((x, curve(x) - 0.04 * (1 - min(x * x / 0.07 + (z + 0.12) ** 2 / 0.29, 1.5) / 1.5) - 0.012,
                             z), 0.018, "BH_Gold", n=6, rings=4, scale=(1, 0.6, 1)))
    # grip + arm strap on the back
    V, F = M.tube([(-0.08, -0.035, 0.0), (-0.05, 0.02, 0.0), (0.05, 0.02, 0.0), (0.08, -0.035, 0.0)],
                  [(0.013, 0.035)] * 4, n=6, up=(0, 0, 1))
    parts.append(M.Part(V, F, "BH_Leather", name="handle"))
    V, F = M.box(0.28, 0.012, 0.05, center=(0, -0.04, 0.2))
    parts.append(M.Part(V, F, "BH_Leather", name="strap"))
    return parts


def flanged_mace():
    """Flanged mace (weapon space: grip at origin, +Z up the haft): leather grip, gold-banded steel haft, a head of
    seven pale-steel flanges round a gold core, a gold finial; a gold pommel."""
    parts = []
    parts.append(A.lathe_part([(0.0, -0.13), (0.02, -0.125), (0.018, 0.1), (0.016, 0.44), (0.0, 0.45)], "BH_Steel",
                              n=8))
    parts.append(A.lathe_part([(0.0, -0.11), (0.021, -0.11), (0.021, 0.09), (0.0, 0.09)], "BH_Leather", n=8))
    for z in (-0.11, 0.1, 0.25, 0.38):
        parts.append(A.lathe_part([(0.0, z - 0.008), (0.024, z - 0.008), (0.024, z + 0.008), (0.0, z + 0.008)],
                                  "BH_Gold", n=8))
    parts.append(A.lathe_part([(0.0, -0.17), (0.02, -0.165), (0.03, -0.145), (0.022, -0.125), (0.0, -0.125)],
                              "BH_Gold", n=8))
    parts.append(A.lathe_part([(0.0, 0.4), (0.034, 0.41), (0.04, 0.47), (0.034, 0.54), (0.0, 0.56)], "BH_Gold",
                              n=10))
    for k in range(7):
        a = 2 * math.pi * k / 7
        fl = [(0.03, 0.415), (0.07, 0.44), (0.085, 0.49), (0.07, 0.545), (0.03, 0.56)]
        V, F = M.prism(np.array([(r, z) for r, z in fl] + [(0.03, 0.49)]), 0.012, axis="y")
        p = M.Part(V, F, "BH_Steel", name="flange")
        c, s_ = math.cos(a), math.sin(a)
        p.V = np.stack([p.V[:, 0] * c - p.V[:, 1] * s_, p.V[:, 0] * s_ + p.V[:, 1] * c, p.V[:, 2]], 1)
        parts.append(p)
    parts.append(A.lathe_part([(0.0, 0.555), (0.02, 0.56), (0.012, 0.6), (0.0, 0.62)], "BH_Gold", n=8))
    return parts
