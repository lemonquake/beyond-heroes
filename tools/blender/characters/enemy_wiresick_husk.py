"""Wire-sick Husk (bh-029, Builder M2, Zarael / the Glasswire Barrens swarm fodder): what the Blackwire leaves of an
Agdao wire-worker. A gaunt, hunched townsperson (head pushed forward and down, a hump between the shoulders) in a
torn ochre work shirt ripped open down the back, rolled dark trousers, a scorched leather work apron and wrapped
shoes. Copper wire has grown OUT of the body: a crown of thick wire cables erupts from the raw back between the
shoulder blades and arcs up and back, frayed ends burning white; glowing white wire veins run under the skin down
both arms and spread over the back from the wire roots. The right forearm is wound in wire and ends not in a hand
but in a tangled knot of wire drawn out into a braided spike (rigid on weapon.R: the dagger clips stab with it). The
left hand is a bony open claw with glowing veins. Sunken white-glinting eyes, slack mouth, thin hair.

GLOW: pure white (BH_Emissive albedo / emission (1, 1, 1), energy 5). ~1.75 m (hunched; ~1.8 m upright).
Clips: cast_quick dagger_1 dagger_2 (dagger_* = right-hand wire-spike slashes)."""
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
import enemy_glyphbound_warrior as Z

SCALE = 1.8 / 1.818
PROPS = proportions(SCALE, shoulder_x=0.178 * SCALE, hip_x=0.092 * SCALE, upper_len=0.29 * SCALE,
                    fore_len=0.28 * SCALE)
PREVIEW_HEIGHT = 2.3
PALETTE = "wiresick_husk"
PALETTE_COLORS = {
    "BH_Skin": ((0.3, 0.27, 0.23), 0.0, 0.6, None, 0.0, 1.0),                  # ashen, sallow skin
    "BH_Flesh": ((0.3, 0.09, 0.075), 0.0, 0.45, None, 0.0, 1.0),               # raw sores round the wire roots
    "BH_Cloth_Primary": ((0.34, 0.25, 0.13), 0.0, 0.95, None, 0.0, 1.0),       # faded ochre work shirt
    "BH_Cloth_Secondary": ((0.11, 0.085, 0.06), 0.0, 0.95, None, 0.0, 1.0),    # dark rolled trousers
    "BH_Leather": ((0.13, 0.075, 0.042), 0.0, 0.7, None, 0.0, 1.0),            # scorched work apron, shoes
    "BH_Hair": ((0.05, 0.045, 0.04), 0.0, 0.75, None, 0.0, 1.0),
    "BH_Gold": ((0.55, 0.3, 0.16), 1.0, 0.42, None, 0.0, 1.0),                 # grown copper wire
    "BH_Shadow": ((0.018, 0.015, 0.015), 0.0, 0.85, None, 0.0, 1.0),           # sockets, mouth, burns
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),     # the wire's glow (pure white)
}
CLIPS = ["cast_quick", "dagger_1", "dagger_2"]

# gaunt torso with a hump between the shoulder blades
TORSO = []
for _r in K.TORSO:
    _hump = 0.035 * math.exp(-((_r[0] - 1.38) / 0.07) ** 2)
    TORSO.append((_r[0], _r[1] * 0.9, _r[2] * 0.86, _r[3] * 0.93 + _hump, _r[4] * 0.5))
SHIRT_G = 0.012
HD = np.array([0.0, -0.05, -0.035])           # head pushed forward and down (hunch)
P = Z.P


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


class Shifted:
    """SB proxy that moves every part by d before adding (the head / neck pushed forward)."""

    def __init__(self, sb, d):
        self.sb, self.d = sb, np.asarray(d, float)

    def add(self, part, bone=None, weights=None):
        part.move(self.d)
        return self.sb.add(part, bone, weights)


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.96], n=24, cap1=True)
    sb.add(P(V, F, "BH_Skin", "torso"), weights=K.TORSO_W)
    shirt(sb)
    back_wires(sb)
    head(sb)
    for s in ("L", "R"):
        arm(sb, s)
    left_claw(sb)
    K.pelvis_seat(sb, "BH_Cloth_Secondary")
    K.trousers(sb, "BH_Cloth_Secondary", loose=0.92, end=0.6)
    K.boots(sb, "BH_Leather", "BH_Leather", shaft_top=0.26, cuff=False, wraps="BH_Cloth_Primary")
    shin_rags(sb)
    apron(sb)
    K.add_weapon(sb, "R", wire_knot())


# ================================================================================================= clothes
def shirt(sb):
    """Ochre work shirt torn open down the back (the wire roots show), ragged hem, a sagging collar."""
    rows = TORSO
    zs = [0.93, 1.0, 1.08, 1.16, 1.25, 1.33, 1.41, 1.47, 1.505]
    nu = 30
    rings = []
    for z in zs:
        t = (z - 0.93) / (1.505 - 0.93)
        tear = 0.03 + 0.12 * t ** 1.2          # half-width of the back tear (fraction of the circumference)
        fr = np.linspace(0.5 + tear, 1.5 - tear, nu)
        ring = K.ring_frac(rows, max(z, 0.97), SHIRT_G + 0.006 * (1 - t), fr)
        ring[:, 2] = z
        if z < 0.95:
            for i in range(nu):
                ring[i, 2] -= HS.ragged(i / (nu - 1), 2.3, 0.05, 5)
                ring[i, :2] *= 1.04
        rings.append(ring)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    sb.add(M.solidify(P(V, F, "BH_Cloth_Primary", "shirt"), 0.008, offset=1.0), weights=K.TORSO_W)
    # torn edges curl outward (darker frayed rolls)
    for k in (0, -1):
        pts = np.array([r[k] for r in rings])
        sb.add(A.tube(pts, (0.007, 0.005), "BH_Cloth_Primary", n=4), weights=K.TORSO_W)
    # collar
    top = rings[-1]
    sb.add(A.tube(top, (0.012, 0.01), "BH_Cloth_Primary", n=5), "chest")
    # patches and burn holes on the front
    for (frac, z, w, h, rot, mat) in ((0.1, 1.28, 0.07, 0.06, 14, "BH_Cloth_Secondary"),
                                      (0.88, 1.12, 0.05, 0.04, -20, "BH_Shadow"),
                                      (0.95, 1.38, 0.04, 0.035, 8, "BH_Shadow")):
        p, ang = K.on_ring(rows, z, SHIRT_G + 0.012, frac)
        V, F = M.box(w, 0.006, h)
        sb.add(P(V, F, mat, "patch").rot(Ry(rot)).rot(Rz(ang)).move(p), weights=K.TORSO_W)
    # rope belt
    C.rope_belt(sb, z=1.0, g=SHIRT_G + 0.016, mat="BH_Leather", knot_frac=0.12, tails=0.22, rows=rows)


def apron(sb):
    """Scorched leather work apron (front), a pocket with a pair of pliers."""
    rows = [(r[0], r[1] + 0.03, r[2] + 0.03, r[3] + 0.03, r[4]) for r in TORSO]
    pnl = HS.cloth_panel(rows, 1.04, 0.52, lambda z: 0.115 + 0.02 * (1.0 - z), front=True, nu=7, nv=8,
                         mat="BH_Leather", gap=0.008, hang=0.07, rag=0.05, teeth=3, thick=0.01, belt_z=1.0)
    sb.add(pnl, weights=Z.centre_w(1.0, 0.55, 0.55))
    y0 = front_y(rows, 0, 1.0) - 0.008 - 0.07 * 0.2 - 0.016
    V, F = M.box(0.1, 0.012, 0.08, center=(0.05, y0, 0.8))
    sb.add(P(V, F, "BH_Leather", "pocket"), weights=Z.centre_w(1.0, 0.55, 0.55))
    for dx in (-0.006, 0.006):        # pliers handles sticking out of the pocket
        sb.add(A.tube([(0.05 + dx, y0 - 0.004, 0.83), (0.05 + dx * 2.5, y0 - 0.01, 0.9)], 0.006, "BH_Gold", n=4),
               weights=Z.centre_w(1.0, 0.55, 0.55))
    # scorch marks
    for (x, z, r) in ((-0.06, 0.7, 0.03), (0.02, 0.62, 0.025)):
        V, F = M.box(r * 2, 0.004, r * 1.5, center=(x, front_y(rows, 0, 1.0) - 0.008 - 0.07 * (1.0 - z) - 0.02, z))
        sb.add(P(V, F, "BH_Shadow", "scorch"), weights=Z.centre_w(1.0, 0.55, 0.55))


def shin_rags(sb):
    for s in ("L", "R"):
        sh = "shin." + s
        k, a = sb.head(sh), sb.tail(sh)
        K.wrap_band(sb, sh, "foot." + s, 0.35, 0.75, 0.049, "BH_Cloth_Primary", turns=2.5, width=0.026)


# ================================================================================================= wires
def back_wires(sb):
    """Thick copper wire cables erupting from the raw back between the shoulder blades, arcing up and back; frayed
    ends burn white. Glowing veins spread from the roots over the back."""
    rows = TORSO
    cables = [  # (root x, root z, out dir, length, radius)
        (0.0, 1.42, (0.0, 1.0, 1.1), 0.5, 0.017),
        (0.05, 1.36, (0.55, 1.0, 0.8), 0.46, 0.015),
        (-0.05, 1.36, (-0.55, 1.0, 0.8), 0.46, 0.015),
        (0.09, 1.27, (0.9, 1.0, 0.35), 0.36, 0.013),
        (-0.09, 1.27, (-0.9, 1.0, 0.35), 0.36, 0.013),
        (0.03, 1.2, (0.3, 1.0, 0.1), 0.26, 0.011),
        (-0.04, 1.16, (-0.35, 1.0, -0.1), 0.22, 0.011),
    ]
    for i, (x, z, d, ln, r) in enumerate(cables):
        r *= 1.35
        root = np.array([x, back_y(rows, x, z) - 0.01, z])
        d = normalize(np.asarray(d, float))
        sx = 1 if x > 0 else (-1 if x < 0 else 0)
        # arc: out of the back, up, then the end droops back and out (smooth quadratic-ish curve)
        ctrl = [root - d * 0.02, root + d * ln * 0.35, root + d * ln * 0.7 + np.array([sx * 0.05, 0.05, 0.05]),
                root + d * ln * 0.88 + np.array([sx * 0.1, 0.14, -0.08])]
        pts = []
        for j in range(13):
            t = j / 12
            # cubic Bezier through the 4 control points
            b = ((1 - t) ** 3 * ctrl[0] + 3 * (1 - t) ** 2 * t * ctrl[1] + 3 * (1 - t) * t * t * ctrl[2] +
                 t ** 3 * ctrl[3])
            pts.append(b)
        pts = np.array(pts)
        rr = [r * (1.0 - 0.45 * j / 12) for j in range(13)]
        # twisted bundle: two copper strands wound round a glowing core strand
        T = np.gradient(pts, axis=0)
        for k in range(2):
            q = []
            for j in range(13):
                tj = normalize(T[j])
                s1 = normalize(np.cross(tj, (0, 0, 1)) + np.array([1e-4, 0, 0]))
                s2 = np.cross(tj, s1)
                a = math.pi * k + 7.0 * j / 12 + i
                q.append(pts[j] + (s1 * math.cos(a) + s2 * math.sin(a)) * rr[j] * 0.62)
            sb.add(A.tube(q, [x_ * 0.62 for x_ in rr], "BH_Gold", n=5), "chest")
        sb.add(A.tube(pts, [x_ * 0.5 for x_ in rr], "BH_Emissive", n=5), "chest")
        p3, p4 = pts[-2], pts[-1]
        # sore at the root
        sb.add(A.ball(root + np.array([0, 0.004, 0]), r * 1.7, "BH_Flesh", n=8, rings=4, scale=(1, 0.45, 1)), "chest")
        # frayed tip: three short strands splaying, glowing
        tip = np.array(p4)
        dt = normalize(tip - np.array(p3))
        side = normalize(np.cross(dt, (0, 0, 1)) + 1e-6)
        upv = np.cross(side, dt)
        for k in range(3):
            a = 2 * math.pi * k / 3 + i
            e = tip + dt * (0.05 + 0.015 * k) + (side * math.cos(a) + upv * math.sin(a)) * 0.03
            sb.add(A.taper([tip - dt * 0.01, (tip + e) / 2 + upv * 0.006, e], r * 0.45, r * 0.15, "BH_Emissive", n=4),
                   "chest")
    # glowing veins spreading over the back from the roots
    rng = np.random.default_rng(29)
    for k in range(9):
        x0 = 0.1 * (rng.random() - 0.5)
        z0 = 1.2 + 0.24 * rng.random()
        a = rng.random() * 2 * math.pi
        pts = []
        for j in range(5):
            t = j / 4
            x = x0 + math.cos(a) * 0.17 * t + 0.015 * math.sin(j * 2.3 + k)
            z = z0 + math.sin(a) * 0.15 * t
            z = min(max(z, 1.0), 1.47)
            pts.append((x, back_y(rows, x, z) + 0.002, z))
        sb.add(A.tube(pts, [0.0055, 0.005, 0.0042, 0.0032, 0.002], "BH_Emissive", n=4), weights=K.TORSO_W)


# ================================================================================================= head
def head(sb):
    hs = Shifted(sb, HD)
    K.neck_and_head(hs, skin="BH_Skin", eyes="BH_Shadow", eye_glow="BH_Emissive", nose=True)
    # extra neck bridging the forward-thrust head to the hump
    V, F = M.tube([(0, 0.02, 1.43), (0, -0.01, 1.5), (0, -0.04, 1.56)], [(0.06, 0.058), (0.054, 0.052), (0.05, 0.05)],
                  n=12, up=(0, -1, 0))
    sb.add(P(V, F, "BH_Skin", "neck2"), weights=K.HEAD_W)
    # slack open mouth
    hs.add(A.ball((0, -0.074, 1.628), 0.019, "BH_Shadow", n=8, rings=4, scale=(1.1, 0.5, 0.9)), "head")
    # thin, receding, matted hair + a few lank strands down the nape
    K.hair_cap(hs, mat="BH_Hair", g=0.005, z_front=1.785, z_back=1.64, messy=0.012)
    for k, x in enumerate((-0.05, -0.015, 0.03, 0.06)):
        pts = [(x, 0.085, 1.7), (x * 1.2, 0.1, 1.64), (x * 1.3, 0.1 + 0.01 * k, 1.58)]
        hs.add(K.strip(pts, 0.022, 0.005, "BH_Hair", ups=[(0, 1, 0)] * 3), "head")
    # wires from the back of the skull down into the cable crown
    for sx in (1, -1):
        a = np.array([sx * 0.03, 0.075, 1.66]) + HD
        b = np.array([sx * 0.04, 0.11, 1.55])
        c = np.array([sx * 0.02, back_y(TORSO, sx * 0.02, 1.44) - 0.005, 1.44])
        w = K.zspec_w([(1.44, "chest"), (1.56, "neck"), (1.62, "head")])
        sb.add(A.tube([a, b, c], [0.008, 0.009, 0.01], "BH_Gold", n=5), weights=w)
        sb.add(A.ball(a, 0.012, "BH_Flesh", n=6, rings=3), "head")
    # glowing veins on the temples
    for sx in (1, -1):
        pts = [np.array([sx * 0.07, -0.02, 1.7]), np.array([sx * 0.074, 0.01, 1.73]), np.array([sx * 0.066, 0.04, 1.76])]
        hs.add(A.tube(pts, [0.004, 0.0035, 0.002], "BH_Emissive", n=4), "head")


# ================================================================================================= arms
def arm(sb, s):
    sx = 1 if s == "L" else -1
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    K.bare_arm(sb, s, skin="BH_Skin", r_up=0.043, r_fore=0.038, r_wrist=0.029, bulk=0.95)
    w = sb.seg(["chest", "shoulder." + s, ua, fa, ha], power=9)
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    # torn short sleeve
    pts = [sh + np.array([-0.035 * sx, 0, 0.02]), sh + (el - sh) * 0.15, sh + (el - sh) * 0.42]
    V, F = M.tube(pts, [(0.055, 0.058), (0.056, 0.058), (0.054, 0.056)], n=12, up=(0, -1, 0), cap0=False, cap1=False)
    sb.add(M.solidify(P(V, F, "BH_Cloth_Primary", "sleeve"), 0.006, offset=1.0), weights=w)
    c = sh + (el - sh) * 0.4
    sb.add(A.rag_strip(c + np.array([0, -0.04, -0.01]), (0.1 * sx, -0.2, -1), 0.1, 0.035, "BH_Cloth_Primary"),
           weights=w)
    # glowing wire veins under the skin from the shoulder to the wrist (two lines, branching)
    rad = (0.043 * 0.95, 0.038 * 0.95)
    for (th0, seed) in ((0.4, 1.0), (2.6, 2.2)):
        pts = []
        for i in range(10):
            t = i / 9
            q = sh + (wr - sh) * (0.05 + 0.92 * t)
            dd = normalize(wr - sh)
            side = normalize(np.cross(dd, (0, 1, 0))) * sx
            fw = np.cross(side, dd) * -1
            th = th0 + 0.35 * math.sin(seed * 3 + t * 8)
            rr = (rad[0] if t < 0.5 else rad[1]) + 0.002
            pts.append(q + (side * math.cos(th) + fw * math.sin(th)) * rr)
        sb.add(A.tube(pts, 0.0045, "BH_Emissive", n=4), weights=w)
        # a branch on the upper arm
        q = np.array(pts[3])
        sb.add(A.tube([q, q + (el - sh) * 0.15 + fw * 0.012, q + (el - sh) * 0.25 + fw * 0.02], 0.0035, "BH_Emissive",
                      n=4), weights=w)
    # copper wire loops piercing out of the upper arm and back in
    for u in (0.3, 0.62):
        a = sh + (el - sh) * u
        dd = normalize(el - sh)
        out = normalize(np.cross(dd, (0, 1, 0))) * sx
        b = a + dd * 0.07
        mid = (a + b) / 2 + out * 0.045 + np.array([0, 0, 0.01])
        sb.add(A.tube([a + out * 0.03, mid, b + out * 0.03], 0.006, "BH_Gold", n=4), ua)
    if s == "R":
        # forearm wound in wire right down into the knot (no hand)
        sb.add(Z.coil(el + (wr - el) * 0.15, wr + (wr - el) * 0.05, 0.042, 7, 0.0055, "BH_Gold", n=4,
                      pts_per_turn=8), fa)
        V, F = M.tube([el + (wr - el) * 0.2, wr], [(0.036, 0.036), (0.034, 0.034)], n=8, up=(0, -1, 0))
        sb.add(P(V, F, "BH_Emissive", "wireglow"), fa)
        # wrist stump swollen with wire (bridges into the knot)
        sb.add(A.ball(wr + (wr - el) * 0.08, 0.042, "BH_Flesh", n=8, rings=5, scale=(1.0, 1.0, 1.15)), fa)


def left_claw(sb):
    for prt in A.open_palm(sb.b, "L", "BH_Skin", s=SCALE * 0.95):
        sb.add_real(prt, "hand.L")
    for prt in A.bony_fingers(sb.b, "L", "BH_Skin", length=0.115 * SCALE, r=0.0065 * SCALE, curl=0.9, spread=1.1,
                              nails="BH_Gold", open_hand=True):
        sb.add_real(prt, "hand.L")
    # glowing veins over the back of the hand
    L, Ax = A.hand_frame(sb.b, "L")
    for k in range(3):
        y = (-0.02 + 0.02 * k) * SCALE
        pts = [L(-0.07 * SCALE, y * 0.4, 0.024 * SCALE), L(-0.02 * SCALE, y * 0.8, 0.026 * SCALE),
               L(0.03 * SCALE, y, 0.02 * SCALE)]
        sb.add_real(A.tube(pts, 0.004 * SCALE, "BH_Emissive", n=4), "hand.L")


# ================================================================================================= weapon
def wire_knot(s=1.0):
    """The right arm's end (weapon space: grip at origin, +Z forward, -X back toward the wrist): a tangled knot of
    copper wire round a dark burnt core, drawn out into a braided three-strand spike with a glowing heart-strand,
    a white-hot tip, and stray wires running back over the wrist."""
    parts = []
    rng = np.random.default_rng(11)
    parts.append(A.ball((0, 0, 0.01), 0.048, "BH_Shadow", n=10, rings=6, scale=(1.15, 1.0, 1.0)))
    for k in range(7):
        ax = normalize(rng.normal(size=3))
        u = normalize(np.cross(ax, (0.3, 0.5, 0.8)))
        v = np.cross(ax, u)
        r = 0.048 + 0.012 * rng.random()
        c = rng.normal(size=3) * 0.008 + np.array([-0.01, 0, 0.01])
        ring = [c + (u * math.cos(a) + v * math.sin(a)) * r for a in np.linspace(0, 2 * math.pi, 13)]
        parts.append(A.tube(ring, 0.0065, "BH_Gold" if k % 3 else "BH_Emissive", n=4, cap=False))
    # braided spike
    L0, L1 = 0.03, 0.44
    for i in range(3):
        pts, rr = [], []
        for j in range(12):
            t = j / 11
            z = L0 + (L1 - L0) * t
            a = 2 * math.pi * i / 3 + 5.0 * t
            rad = 0.03 * (1 - t) ** 0.8 + 0.002
            pts.append((rad * math.cos(a), rad * math.sin(a) * 0.8, z))
            rr.append(0.011 * (1 - t) + 0.003)
        parts.append(A.tube(pts, rr, "BH_Gold", n=5))
    parts.append(A.taper([(0, 0, 0.02), (0, 0, 0.25), (0, 0, 0.43)], 0.012, 0.004, "BH_Emissive", n=5))
    parts.append(A.taper([(0, 0, 0.4), (0, 0, 0.475)], 0.006, 0.0008, "BH_Emissive", n=5))
    # barbs: short wires hooking back from the spike
    for k, z in enumerate((0.14, 0.22, 0.3)):
        a = 2.1 * k
        b0 = np.array([0.02 * math.cos(a), 0.02 * math.sin(a), z])
        out = np.array([math.cos(a), math.sin(a), 0.0])
        parts.append(A.taper([b0, b0 + out * 0.035 - np.array([0, 0, 0.03])], 0.005, 0.0015, "BH_Gold", n=4))
    # stray wires running back over the wrist (toward -X)
    for k in range(4):
        a = math.pi * 0.5 * k + 0.4
        p0 = np.array([-0.02, 0.04 * math.cos(a), 0.04 * math.sin(a)])
        pts = [p0, p0 + np.array([-0.05, 0.012 * math.cos(a), 0.012 * math.sin(a)]),
               p0 + np.array([-0.11, 0.004 * math.cos(a), 0.004 * math.sin(a)])]
        parts.append(A.tube(pts, [0.006, 0.005, 0.004], "BH_Gold", n=4))
    for p in parts:
        p.V = p.V * s
    return parts
