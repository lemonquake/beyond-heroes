"""Serpent Oracle (bh-029, Builder M5, Zarael / the Jade Sepulchre caster): a priestess who reads the sleeping king's
dreams. A tall feathered-serpent headdress: a carved jade serpent head sits on her crown with its upper jaw arching
over her brow, its open lower jaw and fangs framing her face down to the chin, white-glowing serpent eyes, a fan of
long teal feathers tipped scarlet rising behind it and a ruff of short feathers round its throat. Her face is painted
with a dark band and a jade bar across the eyes (small white eyes). A broad turquoise mosaic collar (rings of small
turquoise and jade tiles edged in gold) over the shoulders, a long deep-green robe with a gold fret hem, a scarlet
sash with jade tassels, a feather bustle at the back of the waist, long black hair. Bare arms with gold armbands and
turquoise cuffs; the left hand open for casting.

Staff (weapon.R): a tall jade-shod staff of black wood with a carved jade serpent coiling up it; at the head the
serpent rears through a ring of turquoise mosaic with a white light held inside the ring.

~1.84 m (feathers ~2.15 m). Clips: cast_area cast_heavy cast_quick staff_1 (+ cast_weapon, the enemy base set)."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C
import kit_a_common as A
import enemy_glyphbound_warrior as Z
import enemy_jade_sleeper as J

SCALE = 1.84 / 1.84
PROPS = proportions(SCALE, shoulder_x=0.17, hip_x=0.088, upper_len=0.3, fore_len=0.285, hand_len=0.11)
PREVIEW_HEIGHT = 2.4
PALETTE = "serpent_oracle"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.035, 0.13, 0.1), 0.0, 0.9, None, 0.0, 1.0),        # deep green robe
    "BH_Cloth_Secondary": ((0.4, 0.05, 0.035), 0.0, 0.9, None, 0.0, 1.0),      # scarlet sash
    "BH_Skin": ((0.33, 0.21, 0.14), 0.0, 0.55, None, 0.0, 1.0),
    "BH_Hair": ((0.035, 0.29, 0.26), 0.0, 0.7, None, 0.0, 1.0),                # teal feathers
    "BH_Flesh": ((0.5, 0.07, 0.04), 0.0, 0.7, None, 0.0, 1.0),                 # scarlet feather tips
    "BH_Fur": ((0.02, 0.018, 0.02), 0.0, 0.75, None, 0.0, 1.0),                # black hair
    "BH_Stone": ((0.1, 0.42, 0.3), 0.0, 0.28, None, 0.0, 1.0),                 # jade
    "BH_Horn": ((0.1, 0.5, 0.48), 0.0, 0.3, None, 0.0, 1.0),                   # turquoise mosaic
    "BH_Bone": ((0.62, 0.56, 0.44), 0.0, 0.6, None, 0.0, 1.0),                 # fangs, quills
    "BH_Wood": ((0.04, 0.03, 0.025), 0.0, 0.6, None, 0.0, 1.0),                # black staff wood
    "BH_Gold": ((0.74, 0.52, 0.2), 1.0, 0.32, None, 0.0, 1.0),
    "BH_Leather": ((0.1, 0.06, 0.035), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Shadow": ((0.015, 0.012, 0.014), 0.0, 0.85, None, 0.0, 1.0),
    "BH_Emissive": J.WHITE_GLOW,
}
CLIPS = ["cast_area", "cast_heavy", "cast_quick", "staff_1", "cast_weapon"]

TORSO = [(r[0], r[1] * 0.9, r[2] * 0.9, r[3] * 0.92, r[4] * 0.5) for r in K.TORSO]
G = 0.012
P = Z.P


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(P(V, F, "BH_Skin", "body"), weights=K.TORSO_W)
    C.robe_top(sb, "BH_Cloth_Primary", trim="BH_Gold", g=G, rows=TORSO)
    C.robe_skirt(sb, "BH_Cloth_Primary", trim="BH_Gold", z_top=1.06, z_bot=0.08, flare=0.13, folds=0.012, g=G - 0.004)
    hem_fret(sb)
    sash(sb)
    bustle(sb)
    collar(sb)
    head(sb)
    for s in ("L", "R"):
        arm(sb, s)
    K.add_fist(sb, "R", "BH_Skin", "BH_Skin", scale=0.92)
    for prt in A.open_palm(sb.b, "L", "BH_Skin", s=SCALE * 0.92):
        sb.add_real(prt, "hand.L")
    for prt in A.bony_fingers(sb.b, "L", "BH_Skin", length=0.1 * SCALE, r=0.007 * SCALE, curl=0.45, spread=1.15,
                              nails="BH_Stone", open_hand=True):
        sb.add_real(prt, "hand.L")
    K.trousers(sb, "BH_Cloth_Primary", loose=0.9)
    K.boots(sb, "BH_Leather", "BH_Leather", shaft_top=0.3, cuff=False, wraps="BH_Gold")
    K.add_weapon(sb, "R", oracle_staff(SCALE))


# ================================================================================================= robe
def hem_fret(sb):
    """Gold stepped-fret band round the robe above the hem (front + back panels, so it follows the legs)."""
    for side, sx in (("L", 1), ("R", -1)):
        for back in (False, True):
            span = 1.06 - 0.08
            z0 = 0.16
            t = (1.06 - z0) / span
            rows = [(z0 - 0.05, 0.15 + G + 0.13 * t + 0.009, 0.098 + G + 0.13 * t + 0.009,
                     0.1 + G + 0.13 * 1.1 * t + 0.009, 0.0),
                    (z0 + 0.07, 0.15 + G + 0.13 * t + 0.009, 0.098 + G + 0.13 * t + 0.009,
                     0.1 + G + 0.13 * 1.1 * t + 0.009, 0.0)]
            a, b = (0.02, 0.24) if not back else (0.26, 0.48)
            pts = []
            for u, v in Z.fret_wave(3, steps=2):
                f = a + (b - a) * u
                q = K.ring_frac(rows, z0 + 0.05 * v, 0.0, [f], p=2.2)[0]
                q[2] = z0 + 0.05 * v
                if sx < 0:
                    q[0] *= -1
                pts.append(q)
            sb.add(A.tube(pts, 0.0045, "BH_Gold", n=4), weights=C.robe_panel_w(sb, side, back))


def sash(sb):
    rows = K.grow_rows(TORSO, G + 0.012)
    V, F = K.band(rows, 0.98, 1.07, 0.012, -0.004, n=30)
    sb.add(P(V, F, "BH_Cloth_Secondary", "sash"), "hips")
    # sash ends with jade tassels hanging at the front
    for sx, ln in ((1, 0.42), (-1, 0.36)):
        x = sx * 0.035
        y = front_y(rows, x, 1.0) - 0.016
        pts = [(x, y, 1.0), (x * 1.3, y - 0.035, 0.82), (x * 1.5, y - 0.06, 1.0 - ln)]
        side = "L" if sx > 0 else "R"
        sb.add(K.strip(pts, 0.06, 0.007, "BH_Cloth_Secondary", ups=[(0, -1, 0)] * 3),
               weights=C.robe_panel_w(sb, side, False, leg_max=0.5))
        end = np.array(pts[-1])
        sb.add(A.ball(end - (0, 0, 0.02), 0.022, "BH_Stone", n=8, rings=5, scale=(1, 0.8, 1.3)),
               weights=C.robe_panel_w(sb, side, False, leg_max=0.5))
        sb.add(A.tube([end + (0, 0, 0.005), end - (0, 0, 0.002)], 0.032, "BH_Gold", n=8),
               weights=C.robe_panel_w(sb, side, False, leg_max=0.5))


def bustle(sb):
    """A fan of feathers at the back of the waist (reads from the gameplay camera as a crest behind her)."""
    rows = K.grow_rows(TORSO, G + 0.03)
    base = np.array([0.0, back_y(rows, 0, 1.03) + 0.01, 1.03])
    sb.add(A.ball(base, 0.05, "BH_Cloth_Secondary", n=8, rings=5, scale=(1.5, 0.8, 1.0)), "hips")
    n = 9
    for i in range(n):
        a = math.radians(-70 + 140 * i / (n - 1))
        d = normalize(np.array([math.sin(a) * 0.8, 0.75, -0.55 * math.cos(a) - 0.1]))
        tng = normalize(np.cross(d, (0, 0, 1)))
        for prt in Z.zfeather(base + d * 0.03, d, 0.36 + 0.06 * math.cos(a), 0.075, tng, tip=0.3, bend=-0.08, k=6):
            sb.add(prt, "hips")


# ================================================================================================= collar
def collar(sb):
    """Broad turquoise mosaic collar: a gold-edged disc over the shoulders tiled with turquoise and jade."""
    base = K.grow_rows(TORSO, G + 0.012)
    # backing: a sloped ring surface from the neck out over the shoulders
    nu = 32
    rings = []
    for k, (z, g) in enumerate(((1.505, 0.0), (1.47, 0.03), (1.42, 0.065), (1.37, 0.095))):
        rings.append(K.ring_frac(base, z, g, np.linspace(0, 1, nu, endpoint=False)))
    V, F = M.loft(rings, cap0=False, cap1=False)
    sb.add(M.solidify(P(V, F, "BH_Gold", "collar"), 0.008, offset=1.0), "chest")
    rim = np.vstack([rings[-1], rings[-1][:1]])
    sb.add(A.tube(rim, 0.009, "BH_Gold", n=5, cap=False), "chest")
    # mosaic tiles in three rows: turquoise with a jade row between
    for zr, g, cnt, mat, w, h in ((1.485, 0.018, 26, "BH_Horn", 0.032, 0.03),
                                  (1.445, 0.05, 30, "BH_Stone", 0.034, 0.03),
                                  (1.398, 0.083, 34, "BH_Horn", 0.036, 0.034)):
        for i in range(cnt):
            f = (i + 0.5 * (cnt % 2)) / cnt
            q0 = K.ring_frac(base, zr, g, [f])[0]
            q1 = K.ring_frac(base, zr - 0.02, g + 0.02, [f])[0]
            p, R = J.surf_frame(base, f, zr, g)
            down = normalize(q1 - q0)
            nrm = normalize(np.cross(R[:, 0], down))
            if np.dot(nrm, R[:, 1]) > 0:
                nrm = -nrm
            RR = np.stack([R[:, 0], -nrm, -down], 1)
            sb.add(J.plaque(p - nrm * 0.004, RR, w, h, t=0.008, mat=mat, bev=0.0), "chest")
    # a jade pectoral disc hanging at the front, a white glow at its centre
    q = np.array([0.0, front_y(base, 0, 1.33) - 0.03, 1.33])
    V, F = M.lathe([(0.0, -0.01), (0.05, -0.01), (0.056, 0.0), (0.05, 0.012), (0.0, 0.014)], 16)
    sb.add(P(V, F, "BH_Stone", "pectoral").rot(Rx(90)).move(q), "chest")
    ring = [q + (0.044 * math.cos(a), -0.014, 0.044 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 17)]
    sb.add(A.tube(ring, 0.004, "BH_Gold", n=4, cap=False), "chest")
    sb.add(A.ball(q + (0, -0.016, 0), 0.014, "BH_Emissive", n=8, rings=4, scale=(1, 0.5, 1)), "chest")


# ================================================================================================= head
def head(sb):
    K.neck_and_head(sb, skin="BH_Skin", eyes="BH_Shadow", eye_glow="BH_Emissive", nose=True)
    # face paint: a dark band over the eyes with a jade bar across it
    rows = K.grow_rows(K.HEAD, 0.003)
    rings = [K.ring_frac(rows, z, 0.0, np.linspace(-0.2, 0.2, 13) % 1.0, p=2.1) for z in (1.682, 1.7, 1.716)]
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    sb.add(M.solidify(P(V, F, "BH_Shadow", "paint"), 0.002, offset=1.0), "head")
    # long black hair down the back
    K.hair_cap(sb, mat="BH_Fur", z_front=1.77, z_back=1.6, messy=0.004)
    for x in (-0.06, -0.02, 0.02, 0.06):
        pts = [(x, 0.08, 1.72), (x * 1.3, 0.12, 1.58), (x * 1.5, 0.15, 1.42), (x * 1.6, 0.16, 1.26)]
        sb.add(K.strip(pts, 0.05, 0.012, "BH_Fur", ups=[(0, 1, 0)] * 4),
               weights=K.zspec_w([(1.42, "chest"), (1.56, "neck"), (1.62, "head")]))
    serpent_headdress(sb)


def serpent_headdress(sb):
    """A jade serpent head worn as a helm: skull over the crown, upper jaw over the brow, lower jaw and fangs framing
    the face, white eyes, a fan of feathers behind, a feather ruff."""
    # skull / upper head: lofted superellipse rings from the back of the head to the snout over the brow
    sect = [(0.12, 1.74, 0.1, 0.07, 0.09), (0.06, 1.8, 0.118, 0.09, 0.07), (-0.02, 1.83, 0.12, 0.095, 0.05),
            (-0.09, 1.82, 0.11, 0.08, 0.04), (-0.15, 1.8, 0.09, 0.06, 0.035), (-0.2, 1.775, 0.06, 0.04, 0.03)]
    rings = []
    for y, zc, rx, rt, rb in sect:
        a = np.linspace(0, 2 * math.pi, 18, endpoint=False)
        rings.append(np.array([(rx * np.sign(math.cos(t)) * abs(math.cos(t)) ** 0.8, y,
                                zc + (rt if math.sin(t) > 0 else rb) * math.sin(t)) for t in a]))
    V, F = M.loft(rings, cap0=True, cap1=True)
    sb.add(M.recalc_normals(P(V, F, "BH_Stone", "serpent_skull")), "head")
    # scale ridges across the skull (gold-edged carved rows) + a turquoise row down the spine
    for y in (0.07, 0.02, -0.03, -0.08):
        sec = [s for s in sect]
        r = np.interp(-y, [-s[0] for s in sec], [s[2] for s in sec])
        zc = np.interp(-y, [-s[0] for s in sec], [s[1] for s in sec])
        rt = np.interp(-y, [-s[0] for s in sec], [s[3] for s in sec])
        pts = [(r * 1.02 * math.cos(t), y, zc + rt * 1.02 * math.sin(t)) for t in np.linspace(0.15, math.pi - 0.15, 9)]
        sb.add(A.tube(pts, 0.006, "BH_Gold", n=4), "head")
    for y in np.linspace(0.08, -0.16, 7):
        zc = np.interp(-y, [-s[0] for s in sect], [s[1] + s[3] for s in sect])
        sb.add(A.ball((0, y, zc + 0.004), 0.016, "BH_Horn", n=6, rings=3, scale=(1.2, 1.0, 0.5)), "head")
    # brow ridges + white eyes on the sides of the serpent's head
    for sx in (1, -1):
        sb.add(A.tube([(sx * 0.06, -0.06, 1.865), (sx * 0.085, -0.12, 1.85), (sx * 0.07, -0.16, 1.825)],
                      [0.02, 0.022, 0.012], "BH_Stone", n=6), "head")
        sb.add(A.ball((sx * 0.083, -0.12, 1.825), 0.022, "BH_Shadow", n=8, rings=5, scale=(0.6, 1.1, 0.8)), "head")
        sb.add(A.ball((sx * 0.094, -0.122, 1.826), 0.017, "BH_Emissive", n=8, rings=4, scale=(0.6, 1.2, 0.8)), "head")
        sb.add(A.ball((sx * 0.022, -0.2, 1.8), 0.006, "BH_Shadow", n=5, rings=3), "head")   # nostrils
    # upper fangs hanging in front of the brow
    for sx in (1, -1):
        sb.add(A.taper([(sx * 0.045, -0.175, 1.76), (sx * 0.05, -0.16, 1.7)], 0.011, 0.002, "BH_Bone", n=5), "head")
        sb.add(A.taper([(sx * 0.07, -0.13, 1.76), (sx * 0.075, -0.125, 1.725)], 0.007, 0.001, "BH_Bone", n=4), "head")
    # upper lip / jaw edge under the snout (a gold band)
    lip = [(sx * x, y, z) for sx, (x, y, z) in [(-1, (0.1, -0.02, 1.76)), (-1, (0.085, -0.12, 1.765)),
                                                 (1, (0.0, -0.2, 1.765)), (1, (0.085, -0.12, 1.765)),
                                                 (1, (0.1, -0.02, 1.76))]]
    sb.add(A.tube(lip, 0.009, "BH_Gold", n=5), "head")
    # lower jaw: two rami running down beside the cheeks to a chin piece under her chin
    for sx in (1, -1):
        pts = [(sx * 0.1, 0.0, 1.76), (sx * 0.1, -0.03, 1.69), (sx * 0.088, -0.07, 1.62), (sx * 0.055, -0.1, 1.575)]
        sb.add(A.tube(pts, [(0.018, 0.026), (0.02, 0.028), (0.018, 0.024), (0.016, 0.02)], "BH_Stone", n=6,
                      up=(sx, 0, 0)), "head")
        for k, u in enumerate((0.25, 0.5, 0.75)):
            q = np.array(pts[0]) * (1 - u) + np.array(pts[3]) * u + np.array([-sx * 0.012, -0.012, 0.012])
            sb.add(A.taper([q, q + np.array([-sx * 0.006, -0.008, 0.035 - 0.006 * k])], 0.007, 0.0015, "BH_Bone",
                           n=4), "head")
    chin = [(-0.055, -0.1, 1.575), (0.0, -0.118, 1.565), (0.055, -0.1, 1.575)]
    sb.add(A.tube(chin, [(0.016, 0.02)] * 3, "BH_Stone", n=6), "head")
    sb.add(A.tube([(x, -0.124, 1.57) for x in (-0.04, 0.0, 0.04)], 0.0045, "BH_Gold", n=4), "head")
    # feather ruff round the jaw hinge / throat
    for i in range(12):
        a = math.radians(-150 + 300 * i / 11)
        q = np.array([0.11 * math.sin(a), 0.02 + 0.09 * math.cos(a), 1.68 - 0.04 * abs(math.sin(a))])
        if math.cos(a) < -0.55:
            continue
        out = normalize(np.array([math.sin(a), math.cos(a) * 0.9 + 0.3, -0.25]))
        for prt in Z.zfeather(q, out, 0.15, 0.05, (math.cos(a), -math.sin(a), 0), tip=0.3, bend=0.03, quill=False,
                              k=5):
            sb.add(prt, "head")
    # the great fan of feathers rising behind the serpent's head
    base = np.array([0.0, 0.11, 1.8])
    tb = math.radians(28)
    n = 13
    for i in range(n):
        a = math.radians(-80 + 160 * i / (n - 1))
        d = np.array([math.sin(a), math.sin(tb) * math.cos(a), math.cos(tb) * math.cos(a)])
        tng = np.array([math.cos(a), -math.sin(tb) * math.sin(a), -math.cos(tb) * math.sin(a)])
        ln = 0.3 + 0.14 * math.cos(a) ** 2
        for prt in Z.zfeather(base + d * 0.02, d, ln, 0.075, tng, tip=0.3, bend=0.06, k=7):
            sb.add(prt, "head")
    V, F = M.lathe([(0.0, -0.03), (0.04, -0.03), (0.045, 0.0), (0.03, 0.03), (0.0, 0.035)], 10)
    sb.add(P(V, F, "BH_Gold", "fanholder").scale((1.4, 1.0, 1.0)).move(base), "head")


def arm(sb, s):
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    K.bare_arm(sb, s, skin="BH_Skin", r_up=0.041, r_fore=0.036, r_wrist=0.028, bulk=0.95)
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    dd = normalize(el - sh)
    c = sh + (el - sh) * 0.5
    sb.add(A.tube([c - dd * 0.016, c + dd * 0.016], 0.047, "BH_Gold", n=12), ua)
    sb.add(A.tube([c - dd * 0.004, c + dd * 0.004], 0.05, "BH_Horn", n=12), ua)
    d = normalize(wr - el)
    # turquoise mosaic cuff with gold edges
    a, b = el + (wr - el) * 0.6, el + (wr - el) * 0.95
    sb.add(A.tube([a, b], [(0.043, 0.043), (0.038, 0.038)], "BH_Horn", n=12), fa)
    for q in (a, b):
        sb.add(A.tube([q - d * 0.006, q + d * 0.006], 0.045, "BH_Gold", n=12), fa)
    # a thin white wire wound round the left forearm (the casting arm)
    if s == "L":
        sb.add(J.glow_wrap(el + (wr - el) * 0.1, el + (wr - el) * 0.55, 0.04, 2.0, wire=0.0045), fa)


# ================================================================================================= staff
def oracle_staff(s=1.0):
    """Staff (weapon space: grip at origin, +Z up): black wood, jade foot and bands, a carved jade serpent coiling up
    the shaft; at the top the serpent rears through a turquoise mosaic ring holding a white light."""
    parts = []
    parts.append(A.tube([(0, 0, -0.98), (0, 0, 0.82)], [0.019, 0.018], "BH_Wood", n=8))
    V, F = M.lathe([(0.0, -1.06), (0.012, -1.06), (0.026, -1.0), (0.026, -0.95), (0.02, -0.93), (0.0, -0.93)], 8)
    parts.append(P(V, F, "BH_Stone", "foot"))
    for z in (-0.9, 0.82):
        V, F = M.lathe([(0.0, z - 0.02), (0.026, z - 0.02), (0.028, z), (0.026, z + 0.02), (0.0, z + 0.02)], 8)
        parts.append(P(V, F, "BH_Gold", "band"))
    parts.append(Z.coil((0, 0, -0.12), (0, 0, 0.1), 0.021, 5, 0.004, "BH_Leather", n=4, pts_per_turn=8))
    # the coiling serpent body: a tapering helix from low on the shaft up to the ring
    pts, rad = [], []
    turns = 3.2
    for i in range(49):
        t = i / 48
        z = -0.75 + 1.5 * t
        a = 2 * math.pi * turns * t
        r = 0.034
        pts.append((r * math.cos(a), r * math.sin(a), z))
        rad.append(0.008 + 0.012 * math.sin(math.pi * min(t * 1.4, 1.0)) ** 0.6 if t < 0.9 else 0.018)
    parts.append(A.tube(pts, rad, "BH_Stone", n=6))
    for k in range(0, 48, 4):                     # gold scale bands along it
        q = np.array(pts[k])
        dd = normalize(np.array(pts[k + 1]) - q)
        parts.append(A.tube([q - dd * 0.004, q + dd * 0.004], rad[k] + 0.002, "BH_Gold", n=6))
    # neck rising from the last coil into the ring, the head facing -Y over the ring
    top = np.array(pts[-1])
    neck = [top, (0.0, 0.02, 0.85), (0.0, 0.03, 0.98), (0.0, 0.0, 1.1), (0.0, -0.05, 1.15)]
    parts.append(A.tube(neck, [0.019, 0.021, 0.022, 0.022, 0.024], "BH_Stone", n=8))
    head = [(0, -0.04, 1.155), (0, -0.09, 1.165), (0, -0.14, 1.16), (0, -0.17, 1.15)]
    parts.append(A.tube(head, [(0.035, 0.026), (0.034, 0.024), (0.026, 0.018), (0.012, 0.01)], "BH_Stone", n=8, p=2.6))
    jaw = [(0, -0.05, 1.135), (0, -0.1, 1.11), (0, -0.14, 1.1)]
    parts.append(A.tube(jaw, [(0.024, 0.01), (0.02, 0.009), (0.01, 0.006)], "BH_Stone", n=6, p=2.4))
    for sx in (1, -1):
        parts.append(A.ball((sx * 0.026, -0.09, 1.18), 0.009, "BH_Emissive", n=6, rings=4))
        parts.append(A.taper([(sx * 0.014, -0.14, 1.15), (sx * 0.014, -0.142, 1.12)], 0.005, 0.001, "BH_Bone", n=4))
    for k in range(5):                            # small feather crest behind the head
        a = math.radians(-40 + 20 * k)
        d = normalize(np.array([math.sin(a) * 0.6, 0.6, math.cos(a)]))
        for prt in Z.zfeather((0, -0.02, 1.17), d, 0.13, 0.04, (math.cos(a), 0, -math.sin(a)), tip=0.3, bend=0.03,
                              quill=False, k=5):
            parts.append(prt)
    # the ring: gold torus inlaid with turquoise tiles, the light inside it (in front of the coiled neck)
    rc = np.array([0.0, 0.0, 0.98])
    R0 = 0.11
    ring = [rc + (R0 * math.cos(a), 0.0, R0 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 33)]
    parts.append(A.tube(ring, (0.02, 0.016), "BH_Gold", n=6, up=(0, -1, 0), cap=False))
    for k in range(16):
        a = 2 * math.pi * (k + 0.5) / 16
        for sy in (-1, 1):
            q = rc + (R0 * math.cos(a), sy * 0.017, R0 * math.sin(a))
            V, F = M.box(0.03, 0.006, 0.02)
            parts.append(P(V, F, "BH_Horn", "tile").rot(Ry(-math.degrees(a) + 90)).move(q))
    parts.append(A.ball(rc + (0, -0.03, 0), 0.042, "BH_Emissive", n=10, rings=6))
    for k in range(4):                            # gold spokes holding the light
        a = 2 * math.pi * k / 4 + math.pi / 4
        parts.append(A.tube([rc + (0.045 * math.cos(a), -0.03, 0.045 * math.sin(a)),
                             rc + (0.1 * math.cos(a), 0.0, 0.1 * math.sin(a))], 0.0045, "BH_Gold", n=4))
    for p in parts:
        p.V = p.V * s
    return parts
