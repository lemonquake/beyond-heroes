"""Storm Herald (bh-013, Builder A2; lightning caller): a tall (~2.0 m) gaunt elder with a long storm-white beard and
cyan-glowing eyes, wearing a crown of copper spikes. Slate-grey upper robe over a storm-blue skirt with a ragged,
wind-torn hem; two tiers of stiff storm-blue shoulder mantles with jagged, copper-trimmed hems (the silhouette key),
a storm-blue tabard with a copper lightning-bolt appliqué. Sleeves end at the elbow; the bare forearms are wound
with copper coils ending in cyan nodes. Right hand: a tall copper lightning-rod staff with a coiled tip, three
prongs and a floating cyan spark above them. Left hand open.

Clips: staff_1, staff_heavy, cast_quick, cast_area, cast_heavy, cast_ultimate (+ the shared enemy base clips).
Kits: enemy_bandit_cutthroat (SB), enemy_ashen_cultist (robe / sleeves), kit_a_common, kit_e_orrery."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, smoothstep
from bh_math import normalize
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C
import enemy_bloodbinder as BB
import enemy_hollow_soldier as HS
import kit_a_common as A
import kit_e_orrery as O

SCALE = 2.0 / 1.93           # crown spike tips ~1.93 standard units
PROPS = proportions(SCALE, shoulder_x=0.172 * SCALE, hip_x=0.09 * SCALE, upper_len=0.3 * SCALE,
                    fore_len=0.28 * SCALE)
PREVIEW_HEIGHT = 2.5
PALETTE = "storm_herald"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.2, 0.21, 0.23), 0.0, 0.85, None, 0.0, 1.0),       # slate-grey robe
    "BH_Cloth_Secondary": ((0.05, 0.12, 0.3), 0.0, 0.8, None, 0.0, 1.0),      # storm-blue skirt, mantles, tabard
    "BH_Bronze": ((0.78, 0.38, 0.19), 0.85, 0.35, None, 0.0, 1.0),            # copper: crown, staff, coils, trims
    "BH_Skin": ((0.6, 0.46, 0.38), 0.0, 0.6, None, 0.0, 1.0),                 # weathered skin
    "BH_Hair": ((0.72, 0.74, 0.76), 0.0, 0.7, None, 0.0, 1.0),                # storm-white hair + beard
    "BH_Leather": ((0.06, 0.05, 0.05), 0.0, 0.65, None, 0.0, 1.0),            # belt, boots, grip
    "BH_Shadow": ((0.03, 0.035, 0.045), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((0.25, 0.9, 1.0), 0.0, 0.3, (0.2, 0.88, 1.0), 11.0, 1.0),  # electric cyan: spark, nodes, eyes
}
CLIPS = ["staff_1", "staff_heavy", "cast_quick", "cast_area", "cast_heavy", "cast_ultimate"]

TORSO = [(r[0], r[1] * 0.9, r[2] * 0.88, r[3] * 0.92, r[4] * 0.6) for r in K.TORSO]
G = 0.012
HEAD_ROWS = [(z, rx * 0.93, ryf * 0.98, ryb, kl, cy) for (z, rx, ryf, ryb, kl, cy) in K.HEAD]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="body"), weights=C.ROBE_W)
    C.robe_top(sb, "BH_Cloth_Primary", trim="BH_Bronze", g=G, rows=TORSO, v_open=0.04)
    C.robe_skirt(sb, "BH_Cloth_Secondary", trim="BH_Cloth_Primary", z_top=1.07, z_bot=0.05, flare=0.16, folds=0.018,
                 ragged=0.07, g=G - 0.02)
    tabard(sb)
    K.belt(sb, TORSO, z=1.02, h=0.045, g=G + 0.02, mat="BH_Leather", buckle="BH_Bronze")
    mantles(sb)
    head(sb)
    for s in ("L", "R"):
        short_sleeve(sb, s)
        K.bare_arm(sb, s, r_up=0.044, r_fore=0.037, r_wrist=0.029)
        coils(sb, s)
    K.add_fist(sb, "R", "BH_Skin", "BH_Skin", scale=0.95)
    for prt in A.open_palm(sb.b, "L", "BH_Skin", s=SCALE * 0.95):
        sb.add_real(prt, "hand.L")
    for prt in A.bony_fingers(sb.b, "L", "BH_Skin", length=0.085 * SCALE, r=0.0068 * SCALE, curl=0.5, spread=1.2,
                              open_hand=True, nails="BH_Shadow"):
        sb.add_real(prt, "hand.L")
    K.trousers(sb, "BH_Cloth_Secondary", loose=0.85)
    K.boots(sb, "BH_Leather", "BH_Leather", shaft_top=0.4, cuff=False)
    K.add_weapon(sb, "R", lightning_rod(SCALE))


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
    t = max(0.0, (1.07 - z) / 1.02)
    ry = 0.098 + (G - 0.02) + 0.16 * t
    rx = 0.15 + (G - 0.02) + 0.16 * t
    k = min(abs(x) / rx, 0.95)
    return -ry * (1 - k ** 2.2) ** (1 / 2.2) - 0.03


def tabard(sb):
    """Storm-blue tabard from the chest to mid-shin, copper edge cords and a copper lightning bolt with cyan tip."""
    z0, z1 = 1.36, 0.42

    def fn(u, v):
        z = z0 + (z1 - z0) * v
        hw = 0.07 + 0.035 * v
        x = (u - 0.5) * 2 * hw
        y = _skirt_front(x, z) if z < 1.04 else front_y(TORSO, x * 0.8, z) - G - 0.03
        return (x, y, z)
    V, F = M.grid(fn, 5, 12)
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Secondary", name="tabard"), 0.007, offset=1.0).flip(),
           weights=centre_w(0.5))
    for sx in (-1, 1):
        pts = [np.array(fn(0.5 + sx * 0.5, v)) + (0, -0.006, 0) for v in np.linspace(0, 1, 10)]
        sb.add(A.tube(pts, (0.008, 0.005), "BH_Bronze", n=4, up=(0, -1, 0)), weights=centre_w(0.5))
    # lightning bolt appliqué (zig-zag), top at the chest, tip at the thigh
    zz = [(0.03, 0.02), (-0.035, 0.18), (0.025, 0.2), (-0.03, 0.42), (0.03, 0.44), (-0.01, 0.7)]
    pts = []
    for x, v in zz:
        p = np.array(fn(0.5 + x / (2 * (0.07 + 0.035 * v)), v))
        pts.append(p + (0, -0.01, 0))
    sb.add(A.tube(pts, (0.016, 0.005), "BH_Bronze", n=4, up=(0, -1, 0)), weights=centre_w(0.5))
    sb.add(O.ball(pts[-1] + (0, -0.004, -0.01), 0.014, "BH_Emissive", n=6, rings=4), weights=centre_w(0.5))


def mantle_w(V):
    out = []
    for v in V:
        ax = abs(v[0])
        s = "L" if v[0] > 0 else "R"
        k = float(smoothstep(0.1, 0.24, ax)) * 0.75
        d = {"chest": 1 - k}
        if k > 1e-3:
            d["shoulder." + s] = k * 0.6
            d["upper_arm." + s] = k * 0.4
        out.append(d)
    return out


def mantles(sb):
    """Two tiers of stiff storm-blue shoulder mantles: each a flared elliptic collar-cape with a jagged hem
    (lightning points) edged in copper; a copper clasp with a cyan node at the throat."""
    for (zt, zb, r0, r1, g, npts, seed) in ((1.515, 1.33, 0.13, 0.31, 0.0, 14, 0.0), (1.53, 1.405, 0.12, 0.25, 0.015,
                                                                                         12, 0.7)):
        nu = 48
        rings = []
        for j, v in enumerate(np.linspace(0, 1, 5)):
            ring = []
            for i in range(nu + 1):
                f = i / nu
                a = 2 * math.pi * (0.03 + 0.94 * f)            # open at the front (f=0 front)
                rad = r0 + (r1 - r0) * v ** 0.85 + g
                rx, ry = rad * 1.0, rad * 0.62 + 0.03
                # jagged hem: zig-zag points on the last row
                z = zt + (zb - zt) * v
                if j == 4:
                    saw = abs(((f * npts + seed) % 1.0) - 0.5) * 2
                    z -= 0.06 * (1 - saw)
                back = 0.5 - 0.5 * math.cos(a)
                ring.append((rx * math.sin(a), -ry * math.cos(a) + 0.015 + 0.02 * back, z - 0.03 * back * v))
            rings.append(np.array(ring))
        V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
        p = M.Part(V, F, "BH_Cloth_Secondary", name="mantle")
        sb.add(M.solidify(p, 0.01, offset=1.0), weights=mantle_w)
        hem = rings[-1] + np.array([0, 0, 0.004])
        sb.add(A.tube(hem, (0.009, 0.009), "BH_Bronze", n=4), weights=mantle_w)
        top = rings[0]
        if g == 0.0:
            sb.add(A.tube(top, (0.008, 0.008), "BH_Bronze", n=4), weights=mantle_w)
    # throat clasp
    c = np.array([0.0, -0.105, 1.5])
    sb.add(O.disc(c, (0, -1, 0.2), 0.03, 0.01, "BH_Bronze", n=10), "chest")
    sb.add(O.ball(c + (0, -0.008, 0), 0.013, "BH_Emissive", n=6, rings=4), "chest")


# ================================================================================================= head
def head(sb):
    K.neck_and_head(sb, skin="BH_Skin", head_rows=HEAD_ROWS, eyes="BH_Shadow", eye_glow="BH_Emissive")
    BB.hair_cap(sb, g=0.01, z_front=1.765, z_back=1.6)     # domed cap on the same narrowed head rows
    # long storm-white beard: moustache + a tapering forked beard to the chest
    parts = []
    for sx in (1, -1):
        parts.append(A.tube([(sx * 0.008, -0.088, 1.647), (sx * 0.03, -0.08, 1.638), (sx * 0.045, -0.07, 1.61)],
                            (0.009, 0.006), "BH_Hair", n=5, up=(0, -1, 0)))
    for p in parts:
        sb.add(p, "head")
    wb = K.zspec_w([(1.4, "chest"), (1.52, "neck"), (1.6, "head")])
    pts = [(0, -0.07, 1.64), (0, -0.09, 1.6), (0, -0.1, 1.54), (0, -0.108, 1.47), (0, -0.112, 1.4), (0, -0.114, 1.33)]
    V, F = M.tube(pts, [(0.055, 0.03), (0.06, 0.035), (0.055, 0.032), (0.045, 0.026), (0.03, 0.018), (0.012, 0.008)],
                  n=8, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Hair", name="beard"), weights=wb)
    for sx in (1, -1):
        pts = [(sx * 0.02, -0.108, 1.44), (sx * 0.03, -0.114, 1.34), (sx * 0.035, -0.116, 1.27)]
        sb.add(A.tube(pts, (0.018, 0.004), "BH_Hair", n=5, up=(0, -1, 0)), weights=wb)
    # back hair to the shoulders
    def fn(u, v):
        a = (u - 0.5) * 2
        z = 1.7 - 0.2 * v
        return (a * (0.07 + 0.02 * v), 0.07 + 0.035 * v - 0.03 * a * a, z)
    V, F = M.grid(fn, 7, 5)
    sb.add(M.solidify(M.Part(V, F, "BH_Hair", name="backhair").flip(), 0.012, offset=1.0),
           weights=K.zspec_w([(1.5, "neck"), (1.62, "head")]))
    crown(sb)


def crown(sb):
    """Copper circlet with nine spikes, tallest at the front centre, splayed slightly outward; a cyan gem at the
    front and small cyan beads at the spike bases."""
    z = 1.765
    rows = K.grow_rows(HEAD_ROWS, 0.016)
    fr = np.linspace(0, 1, 25)[:-1]
    ring = K.ring_frac(rows, z, 0.0, fr, p=2.1)
    ring = np.vstack([ring, ring[:1]])
    sb.add(A.tube(ring, (0.012, 0.007), "BH_Bronze", n=4, up=(0, 0, 1)), "head")
    heights = [0.17, 0.12, 0.1, 0.085, 0.07, 0.07, 0.085, 0.1, 0.12]
    for k, h in enumerate(heights):
        f = k / 9
        q = K.ring_frac(rows, z + 0.005, 0.0, [f], p=2.1)[0]
        out = normalize(np.array([q[0], q[1] - 0.0, 0.0]))
        d = normalize(np.array([0, 0, 1.0]) + out * 0.3)
        sb.add(A.shard(q, d, h, 0.013 if k else 0.017, "BH_Bronze", sides=4, up=out), "head")
        if k:
            sb.add(O.ball(q + out * 0.01 + (0, 0, 0.004), 0.0065, "BH_Emissive", n=6, rings=3), "head")
    q = K.ring_frac(rows, z, 0.0, [0.0], p=2.1)[0]
    sb.add(O.ball(q + (0, -0.012, 0.0), 0.014, "BH_Emissive", n=6, rings=4), "head")


# ================================================================================================= arms
def short_sleeve(sb, s):
    """Slate sleeve from the shoulder flaring to a wide cuff just past the elbow, copper cuff trim."""
    ua, fa = "upper_arm." + s, "forearm." + s
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head("hand." + s)
    sx = 1 if s == "L" else -1
    pts = [sh + (-0.04 * sx, 0, 0.025), sh, sh + (el - sh) * 0.5, el, el + (wr - el) * 0.12]
    prof = [(0.052, 0.056), (0.066, 0.068), (0.062, 0.064), (0.068, 0.07), (0.084, 0.084)]
    V, F = M.tube(pts, prof, n=14, up=(0, -1, 0), cap1=False)
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Primary", name="sleeve"), 0.007, offset=-1.0),
           weights=sb.seg(["chest", "shoulder." + s, ua, fa], power=9))
    d = normalize(wr - el)
    sb.add(O.ring(el + (wr - el) * 0.12, d, 0.086, 0.008, "BH_Bronze", n=14, m=4), fa)


def coils(sb, s):
    """Copper coil wound round the bare forearm, a copper ring at each end, a cyan node on the wrist ring."""
    fa, ha = "forearm." + s, "hand." + s
    K.wrap_band(sb, fa, ha, 0.12, 0.88, 0.043, "BH_Bronze", turns=7, width=0.012, thick=0.008)
    el, wr = sb.head(fa), sb.head(ha)
    d = normalize(wr - el)
    for u in (0.1, 0.9):
        sb.add(O.ring(el + (wr - el) * u, d, 0.044, 0.008, "BH_Bronze", n=12, m=4), fa)
    sb.add(O.ball(el + (wr - el) * 0.9 + np.array([0, 0, 0.05]) * 0.0 + normalize(np.cross(d, (0, 1, 0))) * 0.05,
                  0.011, "BH_Emissive", n=6, rings=4), fa)


# ================================================================================================= weapon
def lightning_rod(s=1.0):
    """Tall copper lightning-rod staff (weapon space: grip at origin, +Z up): copper shaft with dark grip wraps and
    copper collars, a spherical copper knot, a helical coil round the upper rod, three splayed prongs and a floating
    cyan spark (jagged star) hovering above them."""
    parts = []
    parts.append(A.lathe_part([(0.0, -1.02), (0.012, -1.0), (0.017, -0.95), (0.016, 0.0), (0.015, 0.8),
                               (0.0, 0.82)], "BH_Bronze", n=8))
    parts.append(A.lathe_part([(0.0, -0.13), (0.02, -0.13), (0.02, 0.13), (0.0, 0.13)], "BH_Leather", n=8))
    for z in (-0.9, -0.5, -0.14, 0.14, 0.45):
        parts.append(A.lathe_part([(0.0, z - 0.012), (0.024, z - 0.01), (0.026, z), (0.024, z + 0.01),
                                   (0.0, z + 0.012)], "BH_Bronze", n=8))
    parts.append(A.ball((0, 0, 0.62), 0.04, "BH_Bronze", n=10, rings=6))
    parts.append(O.ring((0, 0, 0.62), (0, 0, 1), 0.043, 0.006, "BH_Emissive", n=14, m=4))
    # helical coil round the upper rod
    pts = []
    for i in range(61):
        t = i / 60
        a = 2 * math.pi * 6 * t
        r = 0.045 - 0.012 * t
        pts.append((r * math.cos(a), r * math.sin(a), 0.68 + 0.3 * t))
    parts.append(A.tube(pts, 0.006, "BH_Bronze", n=4))
    parts.append(A.lathe_part([(0.0, 0.8), (0.012, 0.8), (0.009, 1.02), (0.0, 1.04)], "BH_Bronze", n=6))
    # three prongs splaying up from the rod top
    for k in range(3):
        a = 2 * math.pi * k / 3
        o = np.array([math.cos(a), math.sin(a), 0.0])
        pr = [np.array([0, 0, 0.98]), o * 0.05 + (0, 0, 1.04), o * 0.07 + (0, 0, 1.1), o * 0.06 + (0, 0, 1.17)]
        parts.append(A.tube(pr, (0.008, 0.006), "BH_Bronze", n=4))
        parts.append(A.shard(pr[-1], o * 0.2 + (0, 0, 1), 0.05, 0.007, "BH_Bronze", sides=4))
    # floating spark: core ball + jagged rays
    c = np.array([0.0, 0.0, 1.27])
    parts.append(A.ball(c, 0.04, "BH_Emissive", n=8, rings=5))
    rng = np.random.default_rng(3)
    for k in range(8):
        d = normalize(rng.normal(size=3))
        parts.append(A.shard(c + d * 0.03, d, 0.06 + 0.03 * rng.random(), 0.011, "BH_Emissive", sides=3))
    for p in parts:
        p.V = p.V * s
    return parts
