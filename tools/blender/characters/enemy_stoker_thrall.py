"""Stoker Thrall (bh-029, Builder M6, Zarael / the Obsidian Engine fire bomber): an Agdao engine worker the Engine
never let go. A squat iron firebox is strapped high on his back - a stepped Wirewright furnace of blackened iron bound
in copper, glyph channels down its flanks, an open grate on top and a barred fire-door behind where the coals burn
orange (real fire: BH_Coals), a copper chimney rising over his right shoulder. Copper feed-wires run from the furnace
straight into his spine and spread under the soot-dark skin of his back, shoulders and arms as white-glowing veins
(the bh-029 glow rule: every wire/vein/glyph glow is pure white; only the fire itself is orange). A thick split
leather apron with a copper-studded stepped-fret hem over an ochre quilted kilt, a broad padded belt hung with spare
fire-pots, heavy leather heat-gauntlets, wrapped boots. Head: a tight leather cap with a heat flap down the neck, a
copper breathing mask with a slotted grille and round goggles whose glass burns white.

Right hand (weapon.R): long iron furnace tongs gripping a glowing coal. Left hand (weapon.L): a clay fire-pot bound in
copper wire, hanging by its bail, coals glowing in its open mouth (the game throws a copy as the projectile).

~1.85 m (chimney top ~2.2 m). Authored in the standard 1.8 m space with the bandit kit (SB), scaled.
Clips: axe_1 cast_heavy cast_quick cast_weapon (axe_1 = tongs swing; cast_* = pot throws / furnace blasts)."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
from enemy_bandit_cutthroat import SB, zspec_w, grow_rows, ring_frac, strip
import enemy_glyphbound_warrior as Z
import kit_a_common as A
import kit_ember as E

SCALE = 1.85 / 1.818
PROPS = proportions(SCALE, hip_x=0.108 * SCALE, shoulder_x=0.222 * SCALE, clav_x0=0.045 * SCALE)
PREVIEW_HEIGHT = 2.5
PALETTE = "stoker_thrall"
PALETTE_COLORS = {
    "BH_Skin": ((0.15, 0.118, 0.1), 0.0, 0.55, None, 0.0, 1.0),            # soot-dark skin
    "BH_Flesh": ((0.2, 0.065, 0.05), 0.0, 0.5, None, 0.0, 1.0),           # raw skin round the wire roots
    "BH_Leather": ((0.26, 0.125, 0.055), 0.0, 0.7, None, 0.0, 1.0),       # apron, cap, gauntlets
    "BH_Horn": ((0.085, 0.052, 0.03), 0.0, 0.7, None, 0.0, 1.0),          # straps, belt, boot wraps
    "BH_Cloth_Primary": ((0.46, 0.3, 0.13), 0.0, 0.95, None, 0.0, 1.0),   # ochre quilted kilt
    "BH_Cloth_Secondary": ((0.07, 0.06, 0.05), 0.0, 0.92, None, 0.0, 1.0),  # trousers
    "BH_DarkSteel": ((0.085, 0.08, 0.08), 1.0, 0.55, None, 0.0, 1.0),     # blackened iron: furnace, tongs
    "BH_Bronze": ((0.5, 0.25, 0.11), 1.0, 0.42, None, 0.0, 1.0),          # copper bands, chimney, mask, wire
    "BH_Stone": ((0.34, 0.155, 0.08), 0.0, 0.85, None, 0.0, 1.0),         # terracotta fire-pots
    "BH_Shadow": ((0.018, 0.015, 0.014), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Coals": ((0.62, 0.16, 0.05), 0.0, 0.7, (1.0, 0.32, 0.06), 4.0, 1.0),  # real fire (furnace, pots, tongs)
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),    # wires, glyphs, goggles: white
}
CLIPS = ["axe_1", "cast_heavy", "cast_quick", "cast_weapon"]

TORSO = [  # standard space (z, rx, ry_front, ry_back, keel): thick-set worker, a little barrel-chested
    (0.96, 0.158, 0.104, 0.104, 0.0),
    (1.04, 0.152, 0.106, 0.1, 0.02),
    (1.14, 0.158, 0.116, 0.102, 0.05),
    (1.25, 0.176, 0.124, 0.108, 0.08),
    (1.35, 0.19, 0.126, 0.112, 0.06),
    (1.43, 0.19, 0.116, 0.112, 0.03),
    (1.49, 0.155, 0.095, 0.096, 0.0),
    (1.53, 0.084, 0.068, 0.068, 0.0),
]
TW = zspec_w([(0.99, "hips"), (1.10, "spine"), (1.22, "spine"), (1.32, "chest")])
P = Z.P
FC = np.array([0.0, 0.29, 1.43])         # furnace centre (standard space)
FW, FD, FH = 0.42, 0.27, 0.46            # furnace width / depth / height


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


def tp(f, z, g=0.0):
    return E.torso_point(TORSO, f % 1.0, z, g, 2.3)


def vein(pts, nrm, r=0.006):
    """A wire vein under the skin: a raw dark welt with the white wire just proud of it."""
    return Z.channel(pts, nrm, r=r, groove="BH_Flesh")


def build(body):
    sb = SB(body, SCALE)
    V, F = torso_loft(TORSO, n=24, p=2.3, cap1=True)
    sb.add(M.Part(V, F, "BH_Skin", name="torso"), weights=TW)
    for sx in (1, -1):        # pectoral line
        p = [tp(f, 1.33)[0] for f in np.linspace(sx * 0.02, sx * 0.13, 4)]
        sb.add(K.rtube(p, 0.01, "BH_Skin", n=5), weights=TW)
    apron(sb)
    harness(sb)
    furnace(sb)
    back_wires(sb)
    head(sb)
    for s in ("L", "R"):
        arm(sb, s)
    K.pelvis_seat(sb, "BH_Cloth_Secondary", g=0.012)
    K.trousers(sb, "BH_Cloth_Secondary", loose=1.1)
    K.boots(sb, "BH_Leather", "BH_DarkSteel", wraps="BH_Horn")
    belt(sb)
    K.add_weapon(sb, "R", tongs())
    K.add_weapon(sb, "L", fire_pot(held=True))


# ------------------------------------------------------------------------------------------------- clothing
def apron(sb):
    """Split leather apron: a bib over the chest, two long skirt flaps (front left / right) with a copper fret hem;
    an ochre quilted kilt shows in the split and at the sides."""
    g = 0.022
    rings = []
    for z in (1.03, 1.12, 1.22, 1.32, 1.42):
        hw = 0.13 + 0.02 * (z < 1.2)
        rings.append(np.array([tp(f, z, g)[0] for f in np.linspace(-hw, hw, 9) * 0.55]))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    sb.add(M.solidify(M.Part(V, F, "BH_Leather", name="bib"), 0.012, offset=1.0), weights=TW)
    for z in (1.18, 1.3, 1.4):
        for sx in (1, -1):
            q, n = tp(sx * 0.066, z, g + 0.012)
            sb.add(E.rivet_on(q, n, 0.009, mat="BH_Bronze"), weights=TW)
    # quilted kilt under the apron (front + back panels and side lappets)
    import enemy_hollow_soldier as HS
    for front in (True, False):
        pnl = HS.cloth_panel(grow_rows(TORSO, 0.024), 1.02, 0.6, lambda z: 0.16, front=front, nu=9, nv=7,
                             mat="BH_Cloth_Primary", gap=0.012, hang=0.05, rag=0.0, thick=0.01, belt_z=1.0)
        sb.add(pnl, weights=Z.centre_w(1.0, 0.55, 0.6))
    # the two apron flaps (split up the middle), stiff leather, a copper fret along the hem
    yb = tp(0.0, 1.02, g)[0][1]
    for sx in (1, -1):
        def fn(u, v, sx=sx):
            x = sx * (0.012 + 0.17 * u + 0.03 * v * u)
            z = 1.03 - 0.52 * v
            y = yb - 0.012 - 0.045 * v + 0.07 * u ** 2 * (0.6 + v)
            return (x, y, z)
        V, F = M.grid(fn, 6, 6)
        fl = M.Part(V, F, "BH_Leather", name="flap")
        if sx < 0:
            fl.flip()
        sb.add(M.solidify(fl, 0.014, offset=1.0), weights=sb.skirt(1.0, 0.56, max_leg=0.7, center_w=0.1))
        hem = [np.array(fn(u, 0.93)) + (0, -0.012, 0) for u in np.linspace(0.05, 0.95, 2)]
        x0, x1 = hem[0][0], hem[1][0]
        pts = [(x0 + (x1 - x0) * a, hem[0][1] + (hem[1][1] - hem[0][1]) * a, 0.53 + 0.05 * b) for a, b in Z.fret_wave(2)]
        sb.add(A.tube(pts, (0.006, 0.003), "BH_Bronze", n=4, up=(0, -1, 0)),
               weights=sb.skirt(1.0, 0.56, max_leg=0.7, center_w=0.1))
        # scorch marks
        q = np.array(fn(0.55, 0.45)) + (0, -0.016, 0)
        V, F = M.sphere(0.03, 8, 4, center=q, scale=(1, 0.2, 1.2))
        sb.add(M.Part(V, F, "BH_Shadow", name="scorch"), weights=sb.skirt(1.0, 0.56, max_leg=0.7, center_w=0.1))


def harness(sb):
    """Two broad straps from the furnace over the shoulders, down the chest to the belt, a cross strap with a copper
    buckle on the sternum."""
    g = 0.03
    for sx in (1, -1):
        pts, ups = [], []
        for t in np.linspace(0, 1, 6):
            a = math.pi * (0.5 - t) * 0.95
            pts.append((sx * 0.115, -0.105 * math.sin(a) + 0.02, 1.47 + 0.065 * math.cos(a)))
            ups.append((0, -math.sin(a), math.cos(a)))
        sb.add(strip(pts, 0.06, 0.014, "BH_Horn", ups=ups), "chest")
        pts = [tp(sx * 0.075 - 0.0, z, g)[0] for z in np.linspace(1.44, 1.06, 6)]
        sb.add(strip(pts, 0.055, 0.012, "BH_Horn", ups=[(0.15 * sx, -1, 0)] * 6), weights=TW)
        for z in (1.4, 1.2):
            q, n = tp(sx * 0.075, z, g + 0.008)
            sb.add(E.rivet_on(q, n, 0.011, mat="BH_Bronze"), weights=TW)
    pts = [tp(f, 1.3, g + 0.004)[0] for f in np.linspace(-0.08, 0.08, 5)]
    sb.add(strip(pts, 0.045, 0.012, "BH_Horn", ups=[(0, -1, 0)] * 5), weights=TW)
    q, n = tp(0.0, 1.3, g + 0.016)
    V, F = M.box(0.06, 0.016, 0.06)
    sb.add(M.bevel(P(V, F, "BH_Bronze", "buckle").move(q), 0.004, 1), weights=TW)
    # padded back pad under the furnace
    V, F = M.box(0.3, 0.03, 0.36)
    sb.add(M.bevel(P(V, F, "BH_Leather", "pad").move((0, back_y(TORSO, 0, 1.36) + 0.012, 1.36)), 0.01, 1), "chest")


def belt(sb):
    K.belt(sb, TORSO, z=0.99, h=0.07, g=0.03, mat="BH_Horn", buckle="BH_Bronze")
    # two spare fire-pots hanging at the hips (pot axis vertical, mouth up)
    for frac, z in ((0.22, 0.93), (0.68, 0.94)):
        q, n = tp(frac, z, 0.09)
        for prt in fire_pot(held=False, s=0.82):
            prt.V = prt.V + q
            sb.add(prt, weights=sb.skirt(1.0, 0.8, max_leg=0.35, center_w=0.1))
        top = q + (0, 0, 0.1)
        sb.add(K.rtube([top, top + (0, -n[1] * 0.02, 0.06), tp(frac, 1.0, 0.04)[0]], 0.006, "BH_Horn", n=4), "hips")


def head(sb):
    K.neck_and_head(sb, skin="BH_Skin", eyes="BH_Shadow", eye_glow=None, nose=False)
    # tight leather cap + a heat flap down the back of the neck
    K.hair_cap(sb, mat="BH_Leather", g=0.009, z_front=1.74, z_back=1.6, messy=0.0)
    rows = grow_rows(K.HEAD, 0.012)

    def flap(u, v):
        a = math.radians(-70 + 140 * u)
        q = ring_frac(rows, 1.64, 0.0, [0.5 + 0.18 * math.sin(a)])[0]
        return (q[0] * (1 + 0.25 * v), q[1] + 0.03 * v, 1.66 - 0.13 * v)
    V, F = M.grid(flap, 7, 4)
    sb.add(M.solidify(P(V, F, "BH_Leather", "flap").flip(), 0.01, offset=1.0), weights=K.HEAD_W)
    # copper breathing mask over the nose and mouth, slotted grille
    rings = []
    for z in (1.6, 1.625, 1.655, 1.682):
        r = ring_frac(rows, max(z, 1.60), 0.0, np.linspace(-0.19, 0.19, 11) % 1.0, p=2.1)
        r[:, 2] = z
        rings.append(r)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    sb.add(M.solidify(P(V, F, "BH_Bronze", "mask"), 0.008, offset=1.0), "head")
    V, F = M.box(0.07, 0.02, 0.05, center=(0, -0.104, 1.63))
    sb.add(M.bevel(P(V, F, "BH_Bronze", "snout"), 0.006, 1), "head")
    for z in (1.615, 1.628, 1.641):
        V, F = M.box(0.06, 0.006, 0.005, center=(0, -0.115, z))
        sb.add(P(V, F, "BH_Shadow", "slot"), "head")
    for f in (-0.19, 0.19):
        q = ring_frac(rows, 1.67, 0.008, [f % 1.0], p=2.1)[0]
        sb.add(E.rivet(q, 0.006, mat="BH_DarkSteel"), "head")
    # goggles: copper cups with white-burning glass, a strap round the cap
    for sx in (1, -1):
        c = np.array([sx * 0.031, -0.078, 1.702])
        V, F = M.tube([c + (0, 0.012, 0), c + (0, -0.016, 0)], [(0.021, 0.021), (0.019, 0.019)], n=10, up=(0, 0, 1))
        sb.add(P(V, F, "BH_Bronze", "goggle"), "head")
        V, F = M.sphere(0.016, 8, 4, center=c + (0, -0.016, 0), scale=(1, 0.35, 1))
        sb.add(P(V, F, "BH_Emissive", "lens"), "head")
    pts = [ring_frac(rows, 1.705, 0.002, [f], p=2.1)[0] for f in np.linspace(0.17, 0.83, 11)]
    sb.add(K.rtube(pts, 0.008, "BH_Horn", n=4), "head")


def arm(sb, s):
    sx = 1 if s == "L" else -1
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    K.bare_arm(sb, s, skin="BH_Skin", r_up=0.058, r_fore=0.05, r_wrist=0.035, bulk=1.06)
    K.add_fist(sb, s, "BH_Leather", "BH_Leather", gauntlet=True, scale=1.12)
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    V, F = M.sphere(0.066, 12, 7, center=sh + (el - sh) * 0.1 + (0, 0, 0.012), scale=(1.0, 1.05, 0.95))
    sb.add(P(V, F, "BH_Skin", "deltoid"), weights=lambda V, s=s: [{"shoulder." + s: 0.35, "upper_arm." + s: 0.65}] * len(V))
    # heavy leather heat-gauntlet (flared cuff) + a copper cuff band
    d = normalize(wr - el)
    V, F = M.tube([el + (wr - el) * 0.3, el + (wr - el) * 0.62, wr + d * 0.02],
                  [(0.07, 0.072), (0.06, 0.062), (0.052, 0.055)], n=12, up=(0, -1, 0))
    sb.add(P(V, F, "BH_Leather", "gauntlet"), fa)
    c = el + (wr - el) * 0.3
    V, F = M.tube([c - d * 0.012, c + d * 0.012], [(0.074, 0.076)] * 2, n=12, up=(0, -1, 0))
    sb.add(P(V, F, "BH_Bronze", "cuff"), fa)
    # white wire veins from the shoulder down the outside of the upper arm
    w = sb.seg(["chest", "shoulder." + s, ua, fa, ha], power=9)
    for th0, seed in ((-0.3, 1.0), (0.6, 2.2)):
        pts, nrm = [], []
        for i in range(8):
            t = i / 7
            q = sh + (el - sh) * (0.02 + 0.93 * t)
            dd = normalize(el - sh)
            side = normalize(np.cross(dd, (0, 1, 0))) * sx
            fw = -np.cross(side, dd)
            th = th0 + 0.3 * math.sin(seed * 3 + t * 8)
            nn = side * math.cos(th) + fw * math.sin(th) * 0.6 + np.array([0, 0, 0.6 * (1 - t)])
            nn = normalize(nn)
            pts.append(q + nn * (0.058 * 1.06 + 0.002))
            nrm.append(nn)
        for prt in vein(pts, nrm, r=0.008):
            sb.add(prt, weights=w)


def furnace(sb):
    """The firebox on the back (rigid to chest): stepped iron body with copper bands, glyph channels, a barred fire-door
    behind and an open grate on top (orange coals), a copper chimney over the right shoulder."""
    c = FC
    add = lambda prt: sb.add(prt, "chest")  # noqa: E731
    # body: a slightly tapered iron box (wider at the base)
    rings = []
    for z, k in ((-FH / 2, 1.06), (-FH / 2 + 0.06, 1.06), (FH / 2 - 0.04, 0.96), (FH / 2, 0.92)):
        hw, hd = FW / 2 * k, FD / 2 * k
        rings.append(np.array([(c[0] + x * hw, c[1] + y * hd, c[2] + z) for x, y in
                               ((-1, -1), (1, -1), (1, 1), (-1, 1))]))
    V, F = M.loft(rings)
    add(M.bevel(P(V, F, "BH_DarkSteel", "firebox"), 0.012, 2, angle=30))
    # copper bands top / bottom / middle, corner straps with rivets
    for z, k in ((-FH / 2 + 0.03, 1.07), (0.02, 1.01), (FH / 2 - 0.03, 0.96)):
        V, F = M.box(FW * k + 0.02, FD * k + 0.02, 0.035, center=c + (0, 0, z))
        add(M.bevel(P(V, F, "BH_Bronze", "fband"), 0.006, 1))
    for sxx in (1, -1):
        for syy in (1, -1):
            q0 = c + (sxx * FW / 2 * 1.06, syy * FD / 2 * 1.06, -FH / 2)
            q1 = c + (sxx * FW / 2 * 0.93, syy * FD / 2 * 0.93, FH / 2)
            add(A.tube([q0, q1], 0.016, "BH_Bronze", n=4))
    # stepped roof around the open top grate
    zt = c[2] + FH / 2
    for i, (w, d) in enumerate(((FW * 0.98, FD * 1.0), (FW * 0.8, FD * 0.84))):
        V, F = M.box(w, d, 0.05, center=c + (0, 0, FH / 2 + 0.025 + 0.05 * i))
        add(M.bevel(P(V, F, "BH_DarkSteel", "roof"), 0.008, 1))
    V, F = M.box(FW * 0.5, FD * 0.56, 0.02, center=(c[0], c[1], zt + 0.095))
    add(P(V, F, "BH_Shadow", "pit"))
    for k in range(5):
        V, F = M.sphere(0.035, 8, 4, center=(c[0] - 0.08 + 0.04 * k, c[1] + 0.02 * (-1) ** k, zt + 0.1),
                        scale=(1, 1, 0.6))
        add(P(V, F, "BH_Coals", "coal"))
    for x in np.linspace(-FW * 0.22, FW * 0.22, 5):
        V, F = M.box(0.014, FD * 0.6, 0.016, center=(c[0] + x, c[1], zt + 0.112))
        add(P(V, F, "BH_DarkSteel", "grate"))
    # fire-door on the back face: a copper frame, iron bars, the fire behind
    yb = c[1] + FD / 2 * 1.0
    zd = c[2] - 0.06
    V, F = M.box(0.22, 0.02, 0.17, center=(0, yb + 0.0, zd))
    add(P(V, F, "BH_Coals", "fire"))
    V, F = M.box(0.27, 0.03, 0.22, center=(0, yb + 0.006, zd))
    frame = M.bevel(P(V, F, "BH_Bronze", "doorframe"), 0.006, 1)
    add(frame)
    for x in np.linspace(-0.08, 0.08, 5):
        V, F = M.box(0.016, 0.03, 0.19, center=(x, yb + 0.022, zd))
        add(P(V, F, "BH_DarkSteel", "bar"))
    # glyph channels (white) on both flanks: a stepped fret with a vertical glyph line
    for sxx in (1, -1):
        xf = c[0] + sxx * (FW / 2 * 1.0 + 0.004)
        pts = [(xf, c[1] - FD * 0.38 + FD * 0.76 * a, c[2] + 0.06 + 0.09 * b) for a, b in Z.fret_wave(2, steps=2)]
        for prt in Z.channel(pts, (sxx, 0, 0), r=0.007):
            add(prt)
        for prt in Z.channel([(xf, c[1], c[2] - 0.17), (xf, c[1], c[2] - 0.04)], (sxx, 0, 0), r=0.008):
            add(prt)
    # chimney: copper pipe out of the right-hand top corner, a stepped cap, a ring of fire glow in its mouth
    base = c + (-FW * 0.3, FD * 0.18, FH / 2 + 0.05)
    top = base + (-0.05, 0.03, 0.42)
    V, F = M.tube([base, base + (top - base) * 0.5, top], [(0.045, 0.045), (0.042, 0.042), (0.04, 0.04)], n=10,
                  up=(1, 0, 0))
    add(P(V, F, "BH_Bronze", "chimney"))
    for u in (0.3, 0.7):
        q = base + (top - base) * u
        V, F = M.tube([q - (0, 0, 0.012), q + (0, 0, 0.012)], [(0.052, 0.052)] * 2, n=10, up=(1, 0, 0))
        add(P(V, F, "BH_DarkSteel", "pipering"))
    V, F = M.lathe([(0.0, 0.0), (0.06, 0.0), (0.07, 0.03), (0.055, 0.06), (0.04, 0.06), (0.0, 0.04)], 10)
    add(P(V, F, "BH_DarkSteel", "cap").move(top))
    V, F = M.sphere(0.035, 8, 4, center=top + (0, 0, 0.055), scale=(1, 1, 0.3))
    add(P(V, F, "BH_Coals", "mouth"))


def back_wires(sb):
    """Copper feed-wires from the furnace's front face into his spine; white veins spread from the roots."""
    yf = FC[1] - FD / 2 * 1.0
    roots = []
    for (x, z) in ((0.06, 1.3), (-0.07, 1.27), (0.02, 1.2), (0.11, 1.4), (-0.12, 1.42)):
        q, n = tp(0.5 - x * 0.9, z, 0.0)
        roots.append((q, n))
        a = np.array([x * 0.9, yf, z + 0.04])
        mid = (a + q) / 2 + (0, 0.02, -0.04)
        sb.add(K.rtube([a, mid, q + n * 0.004], 0.009, "BH_Bronze", n=5), "chest")
        V, F = M.sphere(0.018, 8, 4, center=q, scale=(1, 0.5, 1))
        sb.add(P(V, F, "BH_Flesh", "root"), weights=TW)
    # the veins have crept round to the front: over the trapezius and collarbones, up the neck, down the flanks
    for sx in (1, -1):
        for (f0, f1, z0, z1, sd) in ((0.36, 0.16, 1.47, 1.44, 0.0), (0.4, 0.06, 1.49, 1.46, 1.3), (0.33, 0.24, 1.38, 1.08, 2.1)):
            pts, nrm = [], []
            for t in np.linspace(0, 1, 7):
                pp, nn = tp(sx * (f0 + (f1 - f0) * t) + 0.012 * math.sin(t * 11 + sd), z0 + (z1 - z0) * t, 0.002)
                pts.append(pp)
                nrm.append(nn)
            for prt in vein(pts, nrm, r=0.0075):
                sb.add(prt, weights=TW)
        pts = [(sx * (0.045 - 0.004 * t), -0.035 + 0.01 * t, 1.5 + 0.08 * t) for t in np.linspace(0, 1, 4)]
        for prt in vein(pts, (0, -1, 0), r=0.0065):
            sb.add(prt, weights=K.NECK_W)
    rng = np.random.default_rng(3)
    for (q, n) in roots:
        for k in range(2):
            pts, nrm = [], []
            f0 = math.atan2(q[0], q[1]) / (2 * math.pi)
            dz = (rng.random() - 0.3) * 0.12
            df = (rng.random() - 0.5) * 0.18
            for t in np.linspace(0, 1, 5):
                pp, nn = tp(0.5 - f0 * 1.0 + df * t + 0.02 * math.sin(t * 9 + k), q[2] + dz * t, 0.002)
                pts.append(pp)
                nrm.append(nn)
            for prt in vein(pts, nrm, r=0.0075):
                sb.add(prt, weights=TW)


# ------------------------------------------------------------------------------------------------- weapons
def tongs(s=1.0):
    """Furnace tongs (weapon space: grip at origin, +Z forward along the tongs, flats +-Y): two long iron arms riveted
    at a pivot, curved jaws gripping a glowing coal."""
    parts = []
    for sxx in (1, -1):
        pts = [(sxx * 0.012, 0, -0.16), (sxx * 0.014, 0, 0.1), (sxx * 0.016, 0, 0.42), (sxx * -0.01, 0, 0.5),
               (sxx * 0.04, 0, 0.58), (sxx * 0.035, 0, 0.66)]
        parts.append(A.tube(pts, (0.009, 0.0075), "BH_DarkSteel", n=6, up=(0, 1, 0)))
        parts.append(A.ball((sxx * 0.012, 0, -0.165), 0.013, "BH_DarkSteel", n=6, rings=4))
    parts.append(A.tube([(0, -0.02, 0.45), (0, 0.02, 0.45)], 0.016, "BH_Bronze", n=8))
    V, F = M.lathe([(0, -0.1), (0.022, -0.1), (0.024, 0.08), (0, 0.08)], 8)
    parts.append(P(V, F, "BH_Leather", "wrap"))
    coal = A.ball((0, 0, 0.64), 0.04, "BH_Coals", n=7, rings=5, scale=(0.9, 0.8, 1.1))
    parts.append(GK_jitter(coal, 0.006, 5))
    for p in parts:
        p.V = p.V * s
    return parts


def GK_jitter(part, amp, seed):
    rng = np.random.default_rng(seed)
    part.V = part.V + rng.normal(size=part.V.shape) * amp
    return part


def fire_pot(held=True, s=1.0):
    """Clay fire-pot bound in copper wire, coals glowing in its open mouth. held: weapon space for weapon.L (the pot
    hangs from its bail below the fist: distal = weapon -X, mouth toward the fist); otherwise a free part with its
    axis vertical, mouth up, centred at the origin."""
    parts = []
    prof = [(0.0, -0.075), (0.045, -0.075), (0.07, -0.04), (0.078, 0.0), (0.066, 0.045), (0.045, 0.07), (0.05, 0.085),
            (0.042, 0.085), (0.036, 0.07)]
    V, F = M.lathe(prof, 12, cap=False)
    parts.append(P(V, F, "BH_Stone", "pot"))
    V, F = M.lathe([(0.0, 0.062), (0.038, 0.062), (0.0, 0.07)], 10)
    parts.append(P(V, F, "BH_Coals", "potcoals"))
    for k in range(3):
        a = 2 * math.pi * k / 3
        parts.append(A.ball((0.016 * math.cos(a), 0.016 * math.sin(a), 0.075), 0.016, "BH_Coals", n=6, rings=4))
    for z in (-0.035, 0.03):          # copper wire bands
        r = math.sqrt(max(0.0, 0.078 ** 2 - (z * 0.9) ** 2)) + 0.004
        ring = [(r * math.cos(a), r * math.sin(a), z) for a in np.linspace(0, 2 * math.pi, 15)]
        parts.append(A.tube(ring, 0.0045, "BH_Bronze", n=4, cap=False))
    for k in range(4):                # vertical wire net
        a = 2 * math.pi * (k + 0.5) / 4
        pts = [(rr * math.cos(a), rr * math.sin(a), z) for rr, z in ((0.05, -0.072), (0.082, 0.0), (0.05, 0.08))]
        parts.append(A.tube(pts, 0.004, "BH_Bronze", n=4))
    # bail: a copper loop over the mouth
    bail = [(0.06 * math.cos(a), 0.0, 0.085 + 0.1 * math.sin(a)) for a in np.linspace(0, math.pi, 9)]
    parts.append(A.tube(bail, 0.0055, "BH_Bronze", n=4))
    if held:
        # pot axis -> weapon -X (hanging distal), bail apex at the grip
        for p in parts:
            p.move((0, 0, -0.185))           # bail apex (z = 0.185) to the origin
            p.rot(Ry(90))                    # +Z (mouth) -> +X (toward the fist); the pot body hangs at -X
    for p in parts:
        p.V = p.V * s
    return parts
