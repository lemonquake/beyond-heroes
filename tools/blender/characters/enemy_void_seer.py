"""Void Seer (bh-012, Builder E; The Shattered Orrery, gravity caster): a tall (~1.95 m) robed astronomer-cultist.
Floor-length midnight-blue robes and bell sleeves hemmed in brass thread, a violet stole down the front embroidered
with brass constellation lines (small glowing star nodes), a short midnight shoulder mantle, a brass astrolabe on a
chain at the chest and a second one hanging from the belt. A deep hood with nothing inside but void and one huge
glowing violet lens-eye floating in the dark (brass-ringed). Dark gloves, the left hand open for casting. Staff: a
brass telescope-staff (extending draw-tubes, eyepiece, lens) topped with a small armillary sphere around a glowing
star (weapon.R).

Clips: staff_1, cast_quick, cast_heavy, cast_area, cast_channel (base clip, loop), blink.
Robe / hood helpers: enemy_ashen_cultist; kit: enemy_bandit_cutthroat (SB standard space) + kit_e_orrery."""
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

SCALE = 1.95 / 1.885
PROPS = proportions(SCALE, shoulder_x=0.178 * SCALE, hip_x=0.094 * SCALE, upper_len=0.29 * SCALE,
                    fore_len=0.275 * SCALE)
PALETTE = "void_seer"
PALETTE_COLORS = {
    "BH_Cloth_Primary": O.MIDNIGHT,        # robes, hood, mantle
    "BH_Cloth_Secondary": O.VIOLET,        # stole
    "BH_Bronze": O.BRASS,                  # embroidery thread, astrolabes, telescope
    "BH_Horn": O.BRASS_OLD,                # tarnished brass (draw tubes, chain)
    "BH_Gold": O.GOLD,
    "BH_Leather": ((0.03, 0.028, 0.04), 0.0, 0.7, None, 0.0, 1.0),   # gloves, belt
    "BH_DarkSteel": O.IRON,
    "BH_Shadow": O.VOID,                   # the void inside the hood
    "BH_Emissive": O.GLOW,                 # lens-eye, star nodes, staff star
}
CLIPS = ["staff_1", "cast_quick", "cast_heavy", "cast_area", "cast_channel", "blink"]

TORSO = [(r[0], r[1] * 0.9, r[2] * 0.88, r[3] * 0.92, r[4] * 0.6) for r in K.TORSO]
G = 0.012
HOOD = [(z, rx * 1.12, ryf * 1.18, ryb * 1.1, cy - 0.012, th) for (z, rx, ryf, ryb, cy, th) in C.HOOD_DEEP]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


def constellation(pts, line_r=0.0035, star_r=0.009):
    parts = [A.tube(pts, line_r, "BH_Bronze", n=4)]
    for p in pts:
        parts.append(O.speck(p, star_r, "BH_Emissive", seed=int(abs(p[0] * 1000 + p[2] * 100))))
    return parts


def astrolabe(center, normal, r, up=(0, 0, 1)):
    """Brass astrolabe: tarnished mater disc, polished rim + inner rings, rete pointers, glowing centre jewel."""
    parts = [O.disc(center, normal, r, 0.008, "BH_Horn", n=18, up=up),
             O.ring(center + normalize(normal) * 0.005, normal, r, 0.006, "BH_Bronze", n=20, m=4, up=up),
             O.ring(center + normalize(normal) * 0.006, normal, r * 0.62, 0.003, "BH_Bronze", n=16, m=4, up=up),
             O.ring(center + normalize(normal) * 0.007, normal, r * 0.4, 0.003, "BH_Gold", n=12, m=4, up=up)]
    for a in (0, 70, 150, 230, 300):
        parts.append(O.star4(center + normalize(normal) * 0.008 + O.ring_points((0, 0, 0), normal, r * 0.75, 1,
                                                                                 up=up, phase=math.radians(a))[0],
                             r * 0.14, normal, "BH_Bronze", up=up, thick=0.003))
    parts.append(O.ball(center + normalize(normal) * 0.008, r * 0.14, "BH_Emissive", n=8, rings=5))
    parts.append(O.ring(center + np.array([0, 0, r + 0.01]), (1, 0, 0), 0.014, 0.004, "BH_Gold", n=10, m=4))
    return parts


def telescope_staff(s=1.0):
    parts = []
    # draw tubes widening toward the top (telescope), iron shoe at the foot
    secs = [(-1.08, -0.62, 0.017, "BH_Horn"), (-0.62, -0.12, 0.019, "BH_Bronze"), (-0.12, 0.28, 0.022, "BH_Horn"),
            (0.28, 0.6, 0.026, "BH_Bronze")]
    for z0, z1, r, m in secs:
        parts.append(O.tube([(0, 0, z0), (0, 0, z1)], r, m, n=10))
        parts.append(O.ring((0, 0, z1), (0, 0, 1), r + 0.003, 0.005, "BH_Gold", n=12, m=4))
    V, F = M.lathe([(0.0, -1.14), (0.012, -1.13), (0.02, -1.1), (0.018, -1.07), (0.0, -1.07)], 8)
    parts.append(O.P(V, F, "BH_DarkSteel", "shoe"))
    V, F = M.lathe([(0.0, -0.1), (0.024, -0.1), (0.025, 0.1), (0.0, 0.1)], 10)
    parts.append(O.P(V, F, "BH_Leather", "grip"))
    # eyepiece stub on the side + objective lens at the top
    parts.append(O.tube([(0, 0, 0.45), (0.05, -0.02, 0.5)], 0.011, "BH_Bronze", n=8))
    parts.append(O.disc((0, 0, 0.605), (0, 0, 1), 0.024, 0.006, "BH_Emissive", n=12))
    # armillary head: three crossing rings around a glowing star, on a short neck
    c = np.array([0, 0, 0.76])
    parts.append(O.tube([(0, 0, 0.6), (0, 0, 0.68)], 0.012, "BH_Horn", n=8))
    parts += O.armillary(c, 0.085, 0.006, "BH_Bronze", n=22, core="BH_Emissive", core_r=0.034)
    parts.append(O.ring(c, (0.3, 0.2, 1.0), 0.105, 0.004, "BH_Gold", n=24, m=4))
    parts.append(O.tube([c + (0, 0, 0.085), c + (0, 0, 0.13)], [0.006, 0.002], "BH_Gold", n=5))
    parts.append(O.ball(c + (0.1, 0.03, 0.02), 0.012, "BH_Horn", n=6, rings=4))     # little planet on the ring
    for p in parts:
        p.V = p.V * s
    return parts


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="body"), weights=C.ROBE_W)
    # ---- robes
    C.robe_top(sb, "BH_Cloth_Primary", trim="BH_Bronze", g=G, rows=TORSO, v_open=0.0)
    C.robe_skirt(sb, "BH_Cloth_Primary", trim="BH_Bronze", z_top=1.07, z_bot=0.05, flare=0.15, folds=0.014, g=G - 0.02)
    stole(sb)
    mantle(sb)
    # belt + belt astrolabe
    V, F = K.band(TORSO, 1.0, 1.05, G + 0.03, G - 0.004, n=28)
    sb.add(M.Part(V, F, "BH_Leather", name="belt"), "hips")
    p, _ = K.on_ring(TORSO, 1.02, G + 0.04, 0.84)
    for prt in O.rivets([p + (0, 0, -0.01)], 0.012, "BH_Gold"):
        sb.add(prt, "hips")
    wbelt = sb.skirt(1.0, 0.6, max_leg=0.45, center_w=0.05)
    chain = [p, p + (-0.01, -0.02, -0.08), p + (-0.012, -0.03, -0.14)]
    sb.add(A.tube(chain, 0.004, "BH_Horn", n=4), weights=wbelt)
    for prt in astrolabe(np.array(chain[-1]) + (0, -0.005, -0.06), (0.55, -1, 0), 0.055):
        sb.add(prt, weights=wbelt)
    # chest astrolabe on a chain round the neck
    zc = 1.33
    cc = np.array([0.0, front_y(TORSO, 0, zc) - G - 0.03, zc])
    for sx in (1, -1):
        sb.add(A.tube([(sx * 0.06, -0.06, 1.48), (sx * 0.05, cc[1] + 0.01, zc + 0.08), (0, cc[1], zc + 0.075)], 0.004,
                      "BH_Horn", n=4), "chest")
    for prt in astrolabe(cc, (0, -1, 0.15), 0.075):
        sb.add(prt, "chest")
    # ---- hood with the void and the lens-eye
    C.hood(sb, "BH_Cloth_Primary", trim="BH_Bronze", rows=HOOD, lining="BH_Shadow")
    sb.add(O.ball((0, -0.005, 1.7), 0.1, "BH_Shadow", n=14, rings=8, scale=(0.95, 1.0, 1.15)), "head")
    V, F = M.tube([(0, 0.0, 1.46), (0, -0.005, 1.62)], [(0.06, 0.06), (0.07, 0.07)], n=10, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Shadow", name="neckvoid"), weights=K.HEAD_W)
    ec = np.array([0, -0.1, 1.7])
    sb.add(O.ball(ec, 0.052, "BH_Emissive", n=16, rings=10, scale=(1, 0.8, 1)), "head")
    sb.add(O.ring(ec + (0, 0.004, 0), (0, -1, 0), 0.058, 0.007, "BH_Bronze", n=22, m=5), "head")
    sb.add(O.ring(ec + (0, -0.036, 0), (0, -1, 0), 0.02, 0.004, "BH_Shadow", n=12, m=4), "head")     # pupil ring
    sb.add(O.star4(ec + (0, -0.015, 0), 0.09, (0, -1, 0), "BH_Emissive", thick=0.002), "head")   # lens flare
    # ---- arms: bell sleeves, gloves; left hand open (casting)
    for s in ("L", "R"):
        C.bell_sleeve(sb, s, "BH_Cloth_Primary", trim="BH_Bronze", cuff_r=0.082, end=0.74)
    K.add_fist(sb, "R", "BH_Leather", "BH_Leather", scale=1.0)
    for prt in A.open_palm(sb.b, "L", "BH_Leather", s=SCALE):
        sb.add_real(prt, "hand.L")
    for prt in A.bony_fingers(sb.b, "L", "BH_Leather", length=0.09 * SCALE, r=0.0075 * SCALE, curl=0.5, spread=1.1,
                              open_hand=True):
        sb.add_real(prt, "hand.L")
    # ---- legs (hidden) + boots
    K.trousers(sb, "BH_Cloth_Primary", loose=0.85)
    K.boots(sb, "BH_Leather", "BH_Leather", shaft_top=0.35, cuff=False)
    # ---- staff
    K.add_weapon(sb, "R", telescope_staff(SCALE))


def stole(sb):
    """Violet stole down the front (collar -> shins) with brass constellation embroidery."""
    def fn(u, v):
        zb = 0.3
        z = 1.46 + (zb - 1.46) * v
        hw = 0.075 + 0.02 * v
        x = (u - 0.5) * 2 * hw
        if z >= 1.05:
            y = front_y(TORSO, x, z) - G - 0.012
        else:
            y = front_y(TORSO, x, 1.05) - G - 0.012 - 0.1 * (1.05 - z) ** 1.1
        return (x, y, z)
    V, F = M.grid(fn, 5, 14)
    w = HS.cloth_w(chest_z=1.3, belt_z=1.03, leg=0.6)
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Secondary", name="stole"), 0.008, offset=1.0), weights=w)
    for k in (0, 1):
        edge = np.array([fn(float(k), v) for v in np.linspace(0, 1, 12)]) + np.array([0, -0.009, 0])
        sb.add(A.tube(edge, 0.005, "BH_Bronze", n=4), weights=w)
    # constellations (u, v) on the stole surface, pushed just in front of it
    groups = [[(0.3, 0.08), (0.6, 0.14), (0.45, 0.22), (0.7, 0.28)],
              [(0.25, 0.42), (0.5, 0.48), (0.75, 0.44), (0.62, 0.58), (0.35, 0.6)],
              [(0.5, 0.72), (0.3, 0.8), (0.55, 0.88), (0.72, 0.8)]]
    for g in groups:
        pts = [np.array(fn(u, v)) + np.array([0, -0.011, 0]) for u, v in g]
        for prt in constellation(pts):
            sb.add(prt, weights=w)


def mantle(sb):
    """Short midnight shoulder mantle (capelet) flaring over the shoulders, brass-hemmed, a few stars."""
    rings = []
    for k, z in enumerate((1.5, 1.46, 1.41, 1.36)):
        t = k / 3
        r = K.ring_frac(TORSO, max(z, 1.4), G + 0.022 + 0.045 * t, np.linspace(0, 1, 29)[:-1])
        r[:, 0] *= 1.0 + 0.12 * t
        r[:, 2] = z
        rings.append(r)
    V, F = M.loft(rings[::-1], cap0=False, cap1=False)
    w = K.zspec_w([(1.28, "chest"), (1.6, "chest")])

    def mw(Vs):
        out = []
        for v in Vs:
            a = float(smoothstep(0.12, 0.3, abs(v[0])))
            s = "shoulder.L" if v[0] > 0 else "shoulder.R"
            out.append({"chest": 1 - 0.6 * a, s: 0.6 * a} if a > 1e-3 else {"chest": 1.0})
        return out
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="mantle"), 0.01, offset=1.0), weights=mw)
    hem = np.vstack([rings[-1], rings[-1][:1]]) + np.array([0, 0, 0.006])
    sb.add(A.tube(hem, (0.007, 0.012), "BH_Bronze", n=5, up=(0, 0, 1)), weights=mw)
    for frac, dz in ((0.2, 0.05), (0.3, 0.02), (0.7, 0.03), (0.8, 0.06), (0.5, 0.04)):
        i = int(frac * 28)
        p = rings[2][i] * np.array([1.02, 1.02, 1]) + np.array([0, 0, dz * 0.4])
        sb.add(O.speck(p, 0.01, "BH_Emissive", seed=i), weights=mw)
