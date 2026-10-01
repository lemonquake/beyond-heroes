"""Townsfolk (bh-029, Zarael): Wirekeeper Halvessa Orn, keeper of the Heartwire (top of the Crown of Steps).

An older woman, scholar and engineer, a little stooped: a long deep-teal robe (BH_Cloth_Primary, tinted by the game)
with a brick-red stepped-fret hem, a cream sleeveless over-robe open at the front, a short turquoise mosaic collar,
elbow sleeves with copper wire coiled round both bare forearms (a faint white glow in the coils), a leather satchel of
tools on a strap, round spectacles, grey hair falling at the sides and bound up in a high knot wrapped in copper bands
with a turquoise stone, and a tall bronze wire gauge (rigid to hand.R) wound with copper, its tip glowing white.
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import front_y, back_y, interp_rows, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import town_matron as K
from town_matron import Kit, P_, pal, rope, lerp
from town_elder import shawl_surface, shawl_w
from char_mage import ring_frac
import town_terax as Z

PROPS = proportions(0.94, shoulder_x=0.168 * 0.94, hip_x=0.097 * 0.94)
PALETTE = "town_wirekeeper"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.05, 0.17, 0.17)),              # preview: deep teal robe (game tint 0.2,0.45,0.45)
    "BH_Cloth_Secondary": pal((0.62, 0.56, 0.44), 0.92),      # cream over-robe
    "BH_Cloth_Accent": pal((0.38, 0.08, 0.05), 0.88),         # brick-red fret hems
    "BH_Turquoise": pal((0.10, 0.50, 0.48), 0.35),            # mosaic collar, hair stone
    "BH_Coral": pal((0.55, 0.16, 0.08), 0.5),                 # red mosaic chips
    "BH_Bronze": pal((0.46, 0.29, 0.12), 0.4, 1.0),           # gauge rod
    "BH_Gold": pal((0.74, 0.44, 0.20), 0.35, 1.0),            # copper wire, spectacle rims
    "BH_Skin": pal((0.42, 0.27, 0.18), 0.6),
    "BH_Hair": pal((0.62, 0.61, 0.58), 0.7),                  # grey
    "BH_Leather": pal((0.15, 0.085, 0.045), 0.65),
    "BH_Wood": pal((0.18, 0.11, 0.06), 0.75),
    "BH_Emissive": Z.WHITE_GLOW,                              # faint wire glow + the gauge tip
})

W_TORSO = K.torso_rows(chest=0.9, waist=0.95, hip=1.05, depth=1.0, bust=0.012, hump=0.024, shoulder=0.92)
FWD = -0.02
OVER_G = 0.014


def build(body):
    k = Kit(body)
    rows = W_TORSO
    # ---- long teal robe with a fret hem
    K.body_shell(k, rows, 0.98, 1.53, "BH_Cloth_Primary", n=24, cap1=True, name="robe_top")
    sk_rows = K.flare_rows(1.07, 0.06, (0.152, 0.104, 0.116), (0.235, 0.215, 0.24), n=8, curve=0.95)
    sk, rings = K.skirt(sk_rows, "BH_Cloth_Primary", folds=8, amp=0.01)
    k.add(sk, w=k.skirt_w(1.02, 0.5, max_leg=0.8, center_w=0.08))
    hem_fret(k, sk_rows, 0.12, k.skirt_w(1.02, 0.5, max_leg=0.8, center_w=0.08))
    # ---- cream over-robe, open at the front, to below the knee
    over_robe(k, rows)
    # ---- sleeves to the elbow, bare forearms coiled with copper wire
    for s in "LR":
        K.sleeve(k, s, K.SHOULDER_CAP + [(0.4, 0.054, 0.056), (0.85, 0.06, 0.062), (1.02, 0.066, 0.066)],
                 "BH_Cloth_Primary", n=12, solid=0.005, cap1=False)
        K.arm_ring(k, s, 1.0, 0.068, 0.03, "BH_Cloth_Accent", name="cuff")
        K.bare_arm(k, s, t0=0.95, r_el=0.036, r_wr=0.028, r_up=0.044)
        coil(k, s)
        K.mitten(k, s, size=0.94, curl=2.2 if s == "R" else 1.0)
    for s in "LR":
        K.leg_tube(k, s, [(0.15, 0.065, 0.065), (1.0, 0.045, 0.047), (1.9, 0.035, 0.037)], "BH_Cloth_Primary", n=8)
    K.shoes(k, "BH_Leather", sole="BH_Wood", width=0.9)
    # ---- turquoise collar, satchel, gauge staff
    collar(k, rows)
    satchel(k, rows)
    gauge(k)
    # ---- head: grey hair bound high, spectacles
    hr = K.head(k, jaw=0.92, width=0.95, fwd=FWD, nose=1.06, brow=0.85, neck_r=0.045)
    hair(k, hr)
    spectacles(k)
    K.check_normals(body, "wirekeeper")


def hem_fret(k, sk_rows, z, w):
    """Brick-red band with cream step blocks near the robe's hem."""
    ring_lo = K.ring_frac(sk_rows, z - 0.02, 0.006, np.linspace(0, 1, 28, endpoint=False), p=2.2)
    ring_hi = K.ring_frac(sk_rows, z + 0.02, 0.006, np.linspace(0, 1, 28, endpoint=False), p=2.2)
    V, F = M.loft([ring_lo, ring_hi], cap0=False, cap1=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Accent", "hem_band"), 0.005, offset=1.0), w=w)
    n = 22
    for i in range(n):
        f = (i + 0.5) / n
        zz = z + (0.006 if i % 2 else -0.006)
        q = K.ring_frac(sk_rows, zz, 0.013, [f], p=2.2)[0]
        ang = math.degrees(2 * math.pi * f)
        V, F = M.box(0.024, 0.006, 0.014)
        k.add(P_(V, F, "BH_Cloth_Secondary", "fret_step").rot(Rz(ang)).move(q), w=w)


def over_robe(k, rows):
    zs = [0.98, 1.06, 1.14, 1.22, 1.30, 1.37, 1.43, 1.48, 1.52]
    nu = 24
    rings = []
    for z in zs:
        t = (z - 0.98) / 0.54
        a0 = 0.07 + 0.05 * t
        fr = a0 + (1 - 2 * a0) * np.linspace(0, 1, nu)
        rings.append(ring_frac(rows, z, OVER_G, fr))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Secondary", "over"), 0.007, offset=1.0), w=k.torso_w())
    for kk in (0, -1):
        edge = np.array([r[kk] for r in rings]) + np.array([0, -0.004, 0])
        V, F = M.tube(edge, [(0.012, 0.005)] * len(edge), n=5, up=(0, -1, 0), p=3.0)
        k.add(P_(V, F, "BH_Cloth_Accent", "over_edge"), w=k.torso_w())
    # long split skirt of the over-robe
    r0 = interp_rows(rows, 1.0)
    g = OVER_G + 0.008
    sk_rows = K.flare_rows(1.0, 0.44, (r0[1] + g, r0[2] + g, r0[3] + g), (0.26, 0.23, 0.26), n=6)
    sk, rr = K.skirt(sk_rows, "BH_Cloth_Secondary", folds=6, amp=0.009, n=26, gap=0.07)
    w = k.skirt_w(1.0, 0.5, max_leg=0.85)
    k.add(sk, w=w)
    hem = rr[0] + np.array([0, 0, 0.016])
    V, F = M.tube(hem, [(0.016, 0.004)] * len(hem), n=4, up=(0, 0, 1), p=3.0, cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Cloth_Accent", "over_hem"), w=w)
    for i in range(1, len(hem) - 1, 2):
        V, F = M.box(0.02, 0.008, 0.012)
        c = hem[i] + (hem[i] - np.array([0, 0, hem[i][2]])) * 0.0
        out = normalize(np.array([hem[i][0], hem[i][1], 0.0]))
        ang = math.degrees(math.atan2(out[0], -out[1]))
        k.add(P_(V, F, "BH_Cloth_Secondary", "hem_step").rot(Rz(ang)).move(c + out * 0.006 + (0, 0, 0.004 if i % 4 == 1 else -0.004)),
              w=w)
    # waist cord
    K.band(k, rows, 1.05, 1.075, "BH_Cloth_Accent", g_out=OVER_G + 0.014, g_in=OVER_G, n=24, bev=0.0)
    q, ang = K.on_ring(rows, 1.06, OVER_G + 0.016, 0.0)
    q = np.asarray(q)
    for sx in (1, -1):
        k.add(rope([q + (sx * 0.01, 0, 0), q + (sx * 0.02, -0.01, -0.12), q + (sx * 0.024, -0.012, -0.24)], 0.007,
                   "BH_Cloth_Accent"), w=k.skirt_w(1.02, 0.6, max_leg=0.4, center_w=0.3))


def collar(k, rows):
    rings = shawl_surface(30, 4, math.radians(16), (0.095, 0.08, 0.085), (0.205, 0.165, 0.17), 0.1, 0.09, 0.1, 1.585)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Turquoise", "collar"), 0.01, offset=1.0), w=Z_shawl(k))
    hem = rings[0]
    V, F = M.tube(hem, [(0.008, 0.008)] * len(hem), n=6, up=(0, 0, 1))
    k.add(P_(V, F, "BH_Gold", "collar_rim"), w=Z_shawl(k))
    # coral and cream mosaic chips along the outer band
    mid = rings[1]
    for j in range(2, 2 * (len(mid) - 1) - 1):
        i, f = j // 2, (j % 2) * 0.5
        p = (mid[i] * (1 - f) + mid[i + 1] * f) * 0.5 + (hem[i] * (1 - f) + hem[i + 1] * f) * 0.5
        out = normalize(np.array([p[0], p[1] - 0.012, 0.25]))
        V, F = M.box(0.014, 0.014, 0.005)
        mat = ("BH_Coral", "BH_Cloth_Secondary", "BH_Gold")[j % 3]
        R = K.M_align_z(out, (0, 0, 1))
        V = V @ R.T + p + out * 0.008
        k.add(P_(V, F, mat, "chip"), w=Z_shawl(k))


def Z_shawl(k):
    return shawl_w(k)


def coil(k, s):
    """Copper wire coiled round the bare forearm (elbow -> wrist), two faint white threads in it."""
    Z.wrap_spiral(k, "forearm." + s, "hand." + s, 0.12, 0.9, 0.04, 7.0, "BH_Gold", w=0.005, th=0.004)
    for t in (1.35, 1.7):
        K.arm_ring(k, s, t, 0.043, 0.012, "BH_Emissive", name="wire_glow")


def satchel(k, rows):
    pts = []
    for t in np.linspace(0, 1, 8):
        x = lerp(0.12, -0.16, t)
        z = lerp(1.47, 1.04, t)
        y = front_y(rows, x * 0.95, z) - OVER_G - 0.022
        pts.append((x, y, z))
    V, F = M.tube(pts, [(0.016, 0.004)] * len(pts), n=6, up=(0, -1, 0), p=3.0)
    k.add(P_(V, F, "BH_Leather", "strap"), w=k.torso_w())
    pts = []
    for t in np.linspace(0, 1, 6):
        x = lerp(0.12, -0.16, t)
        z = lerp(1.47, 1.04, t)
        pts.append((x, back_y(rows, x * 0.95, z) + OVER_G + 0.022, z))
    V, F = M.tube(pts, [(0.016, 0.004)] * len(pts), n=6, up=(0, 1, 0), p=3.0)
    k.add(P_(V, F, "BH_Leather", "strap_b"), w=k.torso_w())
    q, ang = K.on_ring(rows, 0.97, 0.06, 0.74)
    q = np.asarray(q)
    V, F = M.box(0.16, 0.07, 0.14)
    k.add(M.bevel(P_(V, F, "BH_Leather", "satchel"), 0.018, 2).rot(Rz(ang)).move(q), "hips")
    V, F = M.box(0.165, 0.076, 0.06, center=(0, -0.002, 0.045))
    k.add(M.bevel(P_(V, F, "BH_Leather", "flap"), 0.01, 1).rot(Rz(ang)).move(q), "hips")
    # tools: a copper coil, a bronze rule and two wooden handles
    for dx, h, r, mat in ((-0.05, 0.1, 0.009, "BH_Wood"), (-0.02, 0.13, 0.006, "BH_Bronze"), (0.03, 0.09, 0.01, "BH_Wood")):
        c = q + Rz(ang) @ np.array([dx, 0.015, 0.05])
        V, F = M.tube([c, c + (0, 0, h)], [(r, r)] * 2, n=6, up=(0, -1, 0))
        k.add(P_(V, F, mat, "tool"), "hips")
    c = q + Rz(ang) @ np.array([0.0, -0.04, -0.01])
    ring = K.ring_pts(c, 0.035, Rz(ang) @ np.array([0, -1.0, 0]), n=12)
    V, F = M.tube(ring, [(0.006, 0.006)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Gold", "coil"), "hips")


def gauge(k):
    """Wire gauge staff: a bronze rod upright in the right hand (rigid to hand.R), copper-wound near the top, a
    notched gauge ring and a small white-glowing tip."""
    b = k.b
    g = b.head("weapon.R")
    top = g + np.array([0.0, -0.03, 0.62 * k.s])
    foot = np.array([g[0] - 0.02, g[1] - 0.06, 0.0])
    d = normalize(top - foot)
    V, F = M.tube([foot, foot + (top - foot) * 0.5, top], [(0.013, 0.013), (0.014, 0.014), (0.016, 0.016)], n=8,
                  up=(0, -1, 0))
    b.add(P_(V, F, "BH_Bronze", "rod"), "hand.R")
    # copper winding below the head
    e1 = normalize(np.cross(d, (0, 1.0, 0)))
    e2 = np.cross(d, e1)
    pts = []
    for i in range(41):
        t = i / 40
        c = top - d * lerp(0.32, 0.06, t)
        a = t * 2 * math.pi * 9
        pts.append(c + (e1 * math.cos(a) + e2 * math.sin(a)) * 0.02)
    V, F = M.tube(pts, [(0.004, 0.004)] * len(pts), n=4, up=tuple(d))
    b.add(P_(V, F, "BH_Gold", "winding"), "hand.R")
    # gauge ring with notches (open ring facing forward)
    c = top + d * 0.06
    ring = K.ring_pts(c, 0.055, (0, -1.0, 0), n=16)
    V, F = M.tube(ring, [(0.006, 0.009)] * len(ring), n=5, up=(0, -1, 0), cap0=False, cap1=False)
    b.add(P_(V, F, "BH_Bronze", "gauge_ring"), "hand.R")
    for a in np.linspace(0, 2 * math.pi, 8, endpoint=False):
        p = c + np.array([math.cos(a), 0, math.sin(a)]) * 0.055
        V, F = M.box(0.012, 0.016, 0.012, center=p)
        b.add(P_(V, F, "BH_Gold", "notch"), "hand.R")
    V, F = M.tube([top, c - np.array([0, 0, 0.055])], [(0.008, 0.008)] * 2, n=6, up=(0, -1, 0))
    b.add(P_(V, F, "BH_Bronze", "stem"), "hand.R")
    # glowing tip in the centre of the ring
    V, F = M.sphere(0.016, 10, 6, center=c)
    b.add(P_(V, F, "BH_Emissive", "tip"), "hand.R")
    V, F = M.tube([c - np.array([0, 0, 0.055]), c - np.array([0, 0, 0.016])], [(0.004, 0.004)] * 2, n=5,
                  up=(0, -1, 0))
    b.add(P_(V, F, "BH_Gold", "tip_wire"), "hand.R")


def hair(k, hr):
    line = K.hairline(1.75, 1.67, 1.61)
    V, F = K.head_shell(hr, lambda v: 0.012 + 0.004 * (1 - v), line, nu=24, nv=6, top_bulge=0.01)
    k.add(M.solidify(P_(V, F, "BH_Hair", "hair"), 0.008, offset=-1.0), "head")
    # long locks falling at the sides, in front of the ears to the collar
    for sx in (1, -1):
        pts = [(sx * 0.074, -0.012 + FWD, 1.73), (sx * 0.08, -0.008 + FWD, 1.66), (sx * 0.082, -0.0 + FWD, 1.59),
               (sx * 0.085, 0.01, 1.53)]
        V, F = M.tube(pts, [(0.03, 0.007), (0.034, 0.008), (0.03, 0.008), (0.022, 0.006)], n=8, up=(1, 0, 0))
        k.add(P_(V, F, "BH_Hair", "lock"), w=k.zw([(1.5, "chest"), (1.56, "neck"), (1.62, "head")]))
    # high bound knot: a tall cylinder of hair wrapped in copper bands, a turquoise stone in front
    top = hr[-1][0]
    c0 = np.array([0.0, 0.02 + FWD, top - 0.01])
    prof = [(0.0, 0.0), (0.05, 0.0), (0.058, 0.03), (0.06, 0.08), (0.056, 0.12), (0.04, 0.14), (0.0, 0.145)]
    V, F = M.lathe(prof, 14)
    k.add(K.outward(P_(V, F, "BH_Hair", "knot").rot(Rx(-8)).move(c0)), "head")
    for z in (0.03, 0.075, 0.118):
        r = 0.062 if z < 0.11 else 0.054
        V, F = M.tube([(0, 0, z - 0.006), (0, 0, z + 0.006)], [(r, r)] * 2, n=14, up=(0, -1, 0), cap0=False,
                      cap1=False)
        k.add(M.solidify(P_(V, F, "BH_Gold", "knot_band"), 0.006, offset=1.0).rot(Rx(-8)).move(c0), "head")
    V, F = M.sphere(0.016, 10, 6, center=(0, -0.062, 0.075), scale=(1, 0.6, 1))
    k.add(P_(V, F, "BH_Turquoise", "knot_stone").rot(Rx(-8)).move(c0), "head")
    # one long wooden hair-stick through the knot, slanting, with small copper caps
    a = np.array([-0.1, 0.01, 0.07])
    b2 = np.array([0.11, -0.005, 0.115])
    V, F = M.tube([a, b2], [(0.0045, 0.0045)] * 2, n=6, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Wood", "stick").rot(Rx(-8)).move(c0), "head")
    for e in (a, b2):
        V, F = M.sphere(0.007, 6, 4, center=e)
        k.add(P_(V, F, "BH_Gold", "stick_cap").rot(Rx(-8)).move(c0), "head")


def spectacles(k):
    for sx in (1, -1):
        c = np.array([sx * 0.03, -0.082 + FWD, 1.70])
        ring = K.ring_pts(c, 0.018, (0, -1, 0), n=12)[::-1]
        V, F = M.tube(ring, [(0.0025, 0.0025)] * len(ring), n=5, up=(0, -1, 0), cap0=False, cap1=False)
        k.add(P_(V, F, "BH_Gold", "lens_rim"), "head")
        k.add(rope([c + (sx * 0.018, 0, 0.004), (sx * 0.072, -0.04 + FWD, 1.705), (sx * 0.074, FWD, 1.698)], 0.002,
                   "BH_Gold", n=4), "head")
    k.add(rope([(-0.012, -0.084 + FWD, 1.703), (0, -0.088 + FWD, 1.706), (0.012, -0.084 + FWD, 1.703)], 0.0022,
               "BH_Gold", n=4), "head")
