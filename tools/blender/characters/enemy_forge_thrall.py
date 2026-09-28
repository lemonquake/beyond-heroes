"""Forge Thrall (Builder C, bh-012, Emberforge Depths): a stocky, soot-blackened chained smith-slave (~1.9 m). Bare
scarred arms with faintly glowing burn scars, a heavy leather apron over bare torso, an iron collar with broken chain
links hanging, a riveted iron half-mask over the nose and mouth, shackle cuffs. A heavy forge hammer (weapon.R, hot
striking face) and a small tower shield made from a furnace door with a glowing grille (weapon.L, face -Y).
Authored in the standard 1.8 m space with the bandit kit (SB) and scaled to 1.9 m."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, interp_rows, front_y, back_y
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as BK
from enemy_bandit_cutthroat import SB, zspec_w, grow_rows, ring_frac, strip, rtube
import kit_ember as E

SCALE = 1.9 / 1.818
PROPS = proportions(SCALE, hip_x=0.112, shoulder_x=0.232, clav_x0=0.045)
PALETTE = "forge_thrall"
PALETTE_COLORS = {
    "BH_Skin": ((0.2, 0.125, 0.09), 0.0, 0.55, None, 0.0, 1.0),            # soot-blackened skin
    "BH_Flesh": ((0.26, 0.06, 0.035), 0.0, 0.5, None, 0.0, 1.0),          # raw burn scars
    "BH_Leather": ((0.2, 0.11, 0.055), 0.0, 0.72, None, 0.0, 1.0),        # heavy apron (reads against the soot)
    "BH_Horn": ((0.09, 0.055, 0.03), 0.0, 0.7, None, 0.0, 1.0),           # straps, bracers
    "BH_Cloth_Secondary": ((0.06, 0.055, 0.05), 0.0, 0.92, None, 0.0, 1.0),  # trousers
    "BH_DarkSteel": ((0.09, 0.085, 0.085), 1.0, 0.55, None, 0.0, 1.0),    # blackened iron (mask, collar, door)
    "BH_Rust": ((0.2, 0.1, 0.05), 0.6, 0.78, None, 0.0, 1.0),             # chains, shackles
    "BH_Wood": ((0.1, 0.06, 0.035), 0.0, 0.75, None, 0.0, 1.0),           # hammer haft
    "BH_Hair": ((0.03, 0.026, 0.024), 0.0, 0.8, None, 0.0, 1.0),          # stubble
    "BH_Shadow": ((0.02, 0.016, 0.015), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": E.EMBER,
}
CLIPS = ["shield_bash", "axe_1", "axe_heavy", "sword_1"]

TORSO = [  # standard space (z, rx, ry_front, ry_back, keel): broad, thick, barrel-chested
    (0.96, 0.165, 0.108, 0.106, 0.0),
    (1.04, 0.16, 0.112, 0.102, 0.02),
    (1.14, 0.166, 0.124, 0.104, 0.06),
    (1.25, 0.186, 0.13, 0.11, 0.09),
    (1.35, 0.2, 0.132, 0.116, 0.07),
    (1.43, 0.2, 0.12, 0.116, 0.04),
    (1.49, 0.162, 0.098, 0.1, 0.0),
    (1.53, 0.086, 0.07, 0.07, 0.0),
]
TW = zspec_w([(0.99, "hips"), (1.10, "spine"), (1.22, "spine"), (1.32, "chest")])
HEAD_W = BK.HEAD_W


def finish_mesh(mesh_ob):
    BK.enable_weapon_deform(mesh_ob)


def build(body):
    sb = SB(body, SCALE)
    rng = np.random.default_rng(31)
    V, F = torso_loft(TORSO, n=24, p=2.3, cap1=True)
    sb.add(M.Part(V, F, "BH_Skin", name="torso"), weights=TW)
    # pectoral / belly definition
    for sx in (1, -1):
        p = [E.torso_point(TORSO, f, 1.33, 0.0, 2.3)[0] for f in np.linspace(sx * 0.02, sx * 0.13, 4) % 1.0]
        sb.add(rtube(p, 0.01, "BH_Skin", n=5), weights=TW)
    # burn scars: raw red weals with a faint glowing core
    for p in E.torso_cracks(TORSO, rng, 3, (0.1, 0.3), (1.2, 1.44), r=0.006, steps=4, step=0.03,
                            groove="BH_Flesh", p=2.3, branch=0.0):
        sb.add(p, weights=TW)
    for p in E.torso_cracks(TORSO, rng, 4, (0.35, 0.65), (1.1, 1.44), r=0.006, steps=4, step=0.035,
                            groove="BH_Flesh", p=2.3, branch=0.3):
        sb.add(p, weights=TW)
    apron(sb)
    collar(sb)
    # ---- head: stubbled scalp, faint ember eyes, riveted iron half-mask
    BK.neck_and_head(sb, skin="BH_Skin", nose=False, eyes="BH_Shadow", eye_glow="BH_Emissive")
    BK.hair_cap(sb, mat="BH_Hair", g=0.003, z_front=1.765, z_back=1.64, messy=0.0)
    half_mask(sb)
    # ---- arms: bare, scarred, heavy; leather bracers and iron shackle cuffs with broken chains
    for s in ("L", "R"):
        BK.bare_arm(sb, s, r_up=0.06, r_fore=0.052, r_wrist=0.036, bulk=1.08)
        BK.add_fist(sb, s, "BH_Skin", "BH_Skin", gauntlet=False, scale=1.1)
        ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
        sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
        # deltoid
        V, F = M.sphere(0.07, 12, 7, center=sh + (el - sh) * 0.1 + (0, 0, 0.012), scale=(1.0, 1.05, 0.95))
        sb.add(M.Part(V, F, "BH_Skin", name="deltoid"),
               weights=lambda V, s=s: [{"shoulder." + s: 0.35, "upper_arm." + s: 0.65}] * len(V))
        for p in E.limb_cracks(sh, el, 0.064, rng, 2, r=0.006, groove="BH_Flesh", face=(0, -1, 0)):
            sb.add(p, ua)
        for p in E.limb_cracks(el, wr, 0.055, rng, 1, r=0.0055, groove="BH_Flesh", u_range=(0.1, 0.4)):
            sb.add(p, fa)
        d = normalize(wr - el)
        V, F = M.tube([el + (wr - el) * 0.5, el + (wr - el) * 0.82], [(0.058, 0.06), (0.05, 0.052)], n=12,
                      up=(0, -1, 0))
        sb.add(M.Part(V, F, "BH_Horn", name="bracer"), fa)
        q = el + (wr - el) * 0.9
        V, F = M.tube([q - d * 0.028, q + d * 0.028], [(0.058, 0.058)] * 2, n=12, up=(0, -1, 0))
        sb.add(M.bevel(M.Part(V, F, "BH_Rust", name="shackle"), 0.004, 1), fa)
        for lk in E.chain(q + (0, 0, -0.06), 3 if s == "R" else 2, 0.026, 0.007, mat="BH_Rust"):
            sb.add(lk, fa)
    # ---- legs
    BK.pelvis_seat(sb, "BH_Cloth_Secondary", g=0.012)
    BK.trousers(sb, "BH_Cloth_Secondary", loose=1.12)
    BK.boots(sb, "BH_Horn", "BH_DarkSteel", wraps="BH_Rust")
    BK.belt(sb, TORSO, z=1.0, h=0.05, g=0.02, mat="BH_Horn", buckle="BH_DarkSteel")
    tongs(sb)
    # ---- weapons
    BK.add_weapon(sb, "R", forge_hammer())
    BK.add_weapon(sb, "L", furnace_door())


def apron(sb):
    """Heavy leather apron: bib over the chest (torso weights), skirt from the belt to below the knees."""
    g = 0.022
    zs = [1.03, 1.12, 1.22, 1.32, 1.42]
    rings = []
    for z in zs:
        hw = 0.14 + 0.02 * (z < 1.2)
        fr = np.linspace(-hw, hw, 9) * 0.55
        pts = [E.torso_point(TORSO, f % 1.0, z, g, 2.3)[0] for f in fr]
        rings.append(np.array(pts))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    sb.add(M.solidify(M.Part(V, F, "BH_Leather", name="bib"), 0.012, offset=1.0), weights=TW)
    yb = E.torso_point(TORSO, 0.0, 1.02, g, 2.3)[0][1]

    def fn(u, v):
        w = 0.36 + 0.06 * v
        x = (u - 0.5) * w
        z = 1.03 - 0.5 * v
        y = yb - 0.012 - 0.05 * v + 0.05 * (2 * u - 1) ** 2 * (0.6 + v)
        return (x, y, z)
    V, F = M.grid(fn, 9, 6)
    sk = M.Part(V, F, "BH_Leather", name="apron")
    sk.V[-9:, 2] += np.array([0.0, 0.01, -0.008, 0.012, 0.0, -0.01, 0.006, 0.012, 0.0])
    sb.add(M.solidify(sk, 0.014, offset=1.0), weights=sb.skirt(1.0, 0.56, max_leg=0.7, center_w=0.12))
    # scorch marks + a glowing ember burn hole on the skirt
    for (x, z, r) in ((0.09, 0.78, 0.035), (-0.06, 0.9, 0.028)):
        V, F = M.sphere(r, 8, 4, center=(x, fn(0.5 + x / 0.38, (1.03 - z) / 0.5)[1] - 0.012, z), scale=(1, 0.2, 1))
        sb.add(M.Part(V, F, "BH_Shadow", name="scorch"), weights=sb.skirt(1.0, 0.56, max_leg=0.7, center_w=0.12))
    V, F = M.sphere(0.01, 6, 4, center=(0.09, fn(0.5 + 0.09 / 0.38, 0.5)[1] - 0.016, 0.78), scale=(1, 0.3, 1))
    sb.add(M.Part(V, F, "BH_Emissive", name="ember"), weights=sb.skirt(1.0, 0.56, max_leg=0.7, center_w=0.12))
    # rivets along the bib edge
    for z in (1.18, 1.3, 1.4):
        for sx in (1, -1):
            q, n = E.torso_point(TORSO, (sx * 0.068) % 1.0, z, g + 0.012, 2.3)
            sb.add(E.rivet_on(q, n, 0.009), weights=TW)
    # neck strap and back ties
    for sx in (1, -1):
        a = E.torso_point(TORSO, (sx * 0.075) % 1.0, 1.42, g, 2.3)[0]
        pts = [a, (sx * 0.09, -0.07, 1.5), (sx * 0.08, 0.0, 1.535), (sx * 0.06, 0.07, 1.51)]
        sb.add(strip(pts, 0.032, 0.008, "BH_Horn", ups=[(0, -1, 0.5), (0, -0.5, 1), (0, 0, 1), (0, 0.6, 1)]),
               weights=zspec_w([(1.44, "chest"), (1.56, "chest")]))
    for sgn in (1, -1):
        pts = [E.torso_point(TORSO, f % 1.0, 1.06 + 0.2 * (sgn > 0) * (f - 0.2), g - 0.01, 2.3)[0]
               for f in np.linspace(0.08, 0.5, 7)]
        pts = [(p[0] * sgn, p[1], p[2]) for p in pts]
        sb.add(strip(pts, 0.028, 0.008, "BH_Horn", ups=[(q[0], q[1], 0) for q in pts]), weights=TW)


def collar(sb):
    zc = 1.52
    pts = [(0.098 * math.cos(a), 0.09 * math.sin(a) + 0.004, zc) for a in np.linspace(0, 2 * math.pi, 19)]
    V, F = M.tube(pts, [(0.018, 0.03)] * len(pts), n=6, up=(0, 0, 1), p=3.0, cap0=False, cap1=False)
    W = lambda V: [{"chest": 0.5, "neck": 0.5}] * len(V)  # noqa: E731
    sb.add(M.bevel(M.Part(V, F, "BH_DarkSteel", name="collar"), 0.004, 1), weights=W)
    for a in np.linspace(0, 2 * math.pi, 9, endpoint=False):
        sb.add(E.rivet((0.118 * math.cos(a), 0.11 * math.sin(a) + 0.004, zc), 0.009), weights=W)
    # front ring with a broken chain down the chest, two links hanging at the back
    ring = [(0.02 * math.cos(a), -0.113, zc - 0.028 + 0.02 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9)]
    sb.add(rtube(ring, 0.0055, "BH_Rust", n=4, cap=False), weights=W)
    for j, lk in enumerate(E.chain((0.0, -0.118, zc - 0.05), 4, 0.022, 0.0065, direction=(0.05, -0.12, -1),
                                   mat="BH_Rust")):
        sb.add(lk, "chest")
    for lk in E.chain((0.02, 0.11, zc - 0.03), 3, 0.022, 0.0065, direction=(0.1, 0.3, -1), mat="BH_Rust"):
        sb.add(lk, "chest")


def half_mask(sb):
    """Riveted iron half-mask over the nose and mouth, strapped round the head."""
    rows = grow_rows(BK.HEAD, 0.012)
    rings = []
    for z in (1.6, 1.625, 1.655, 1.68, 1.696):
        fr = np.linspace(-0.2, 0.2, 11)
        r = ring_frac(rows, max(z, 1.60), 0.0, fr % 1.0, p=2.1)
        r[:, 2] = z
        if z < 1.61:
            r[:, 1] += 0.004
        rings.append(r)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    sb.add(M.solidify(M.Part(V, F, "BH_DarkSteel", name="mask"), 0.008, offset=1.0), "head")
    # nose ridge, breathing slits, rivets
    V, F = M.tube([(0, -0.102, 1.61), (0, -0.108, 1.65), (0, -0.103, 1.694)], [(0.012, 0.008)] * 3, n=5, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_DarkSteel", name="ridge"), "head")
    for z in (1.618, 1.632):
        for sx in (1, -1):
            V, F = M.box(0.028, 0.006, 0.005, center=(sx * 0.03, -0.1, z))
            sb.add(M.Part(V, F, "BH_Shadow", name="slit").rot(Rz(sx * 12), center=(sx * 0.03, -0.1, z)), "head")
    for f in np.linspace(-0.19, 0.19, 7):
        q = ring_frac(rows, 1.69, 0.009, [f % 1.0], p=2.1)[0]
        sb.add(E.rivet(q, 0.0055), "head")
    for f in (-0.19, 0.19):
        for z in (1.63, 1.66):
            q = ring_frac(rows, z, 0.009, [f % 1.0], p=2.1)[0]
            sb.add(E.rivet(q, 0.0055), "head")
    rows2 = grow_rows(BK.HEAD, 0.006)
    ring = [ring_frac(rows2, 1.665, 0.0, [f], p=2.1)[0] for f in np.linspace(0.19, 0.81, 11)]
    sb.add(rtube(ring, 0.009, "BH_Horn", n=4), "head")


def tongs(sb):
    """Smith's tongs hanging from the right hip."""
    base = np.array([-0.2, -0.02, 0.97])
    for dx in (-0.012, 0.012):
        sb.add(rtube([base + (dx, 0, 0.02), base + (dx * 1.4, 0.0, -0.2), base + (dx * 3, -0.01, -0.3)],
                     0.0075, "BH_DarkSteel", n=5), weights=sb.skirt(0.99, 0.66, max_leg=0.5, center_w=0.15))
    sb.add(rtube([base + (-0.02, 0, 0.0), base + (0.02, 0, 0.0)], 0.014, "BH_DarkSteel", n=6), "hips")


def forge_hammer():
    """Heavy forge hammer: haft along +Z, square flat face on +X glowing hot, cross-peen on -X."""
    parts = []
    V, F = M.lathe([(0, -0.3), (0.024, -0.3), (0.026, -0.27), (0.02, -0.24), (0.021, 0.6), (0.024, 0.66), (0, 0.66)],
                   8)
    parts.append(E.P(V, F, "BH_Wood", "haft"))
    V, F = M.lathe([(0, -0.1), (0.025, -0.1), (0.025, 0.09), (0, 0.09)], 8)
    parts.append(E.P(V, F, "BH_Horn", "wrap"))
    zc = 0.66
    V, F = M.box(0.2, 0.11, 0.12, center=(0.02, 0, zc))
    parts.append(M.bevel(E.P(V, F, "BH_DarkSteel", "head"), 0.008, 1))
    V, F = M.box(0.05, 0.13, 0.14, center=(0.12, 0, zc))
    parts.append(M.bevel(E.P(V, F, "BH_DarkSteel", "face"), 0.006, 1))
    V, F = M.box(0.012, 0.11, 0.12, center=(0.148, 0, zc))
    parts.append(E.P(V, F, "BH_Emissive", "hotface"))
    rings = [np.array([(x, y, zc + z) for y, z in ((w, t), (-w, t), (-w, -t), (w, -t))])
             for x, w, t in ((-0.08, 0.055, 0.055), (-0.14, 0.05, 0.03), (-0.17, 0.045, 0.008))]
    V, F = M.loft(rings)
    parts.append(E.P(V, F, "BH_DarkSteel", "peen"))
    V, F = M.lathe([(0, zc - 0.08), (0.032, zc - 0.08), (0.032, zc + 0.08), (0, zc + 0.08)], 8)
    parts.append(E.P(V, F, "BH_Rust", "wedge"))
    return parts


def furnace_door():
    """Tower shield = furnace door. Weapon-GLB space: handle at origin, face -Y, long axis Z."""
    parts = []
    yf = -0.07
    W, Hh, zc = 0.5, 0.74, -0.04
    V, F = M.box(W, 0.05, Hh, center=(0, yf + 0.025, zc))
    parts.append(M.bevel(E.P(V, F, "BH_DarkSteel", "door"), 0.012, 1))
    # raised frame
    for (sx, sz, cx, cz) in ((W + 0.02, 0.05, 0, zc + Hh / 2 - 0.02), (W + 0.02, 0.05, 0, zc - Hh / 2 + 0.02),
                             (0.05, Hh, W / 2 - 0.02, zc), (0.05, Hh, -W / 2 + 0.02, zc)):
        V, F = M.box(sx, 0.07, sz, center=(cx, yf + 0.02, cz))
        parts.append(M.bevel(E.P(V, F, "BH_DarkSteel", "frame"), 0.006, 1))
    # glowing grille window (upper half): glowing back plate + dark bars in front
    gz = zc + 0.15
    V, F = M.box(0.3, 0.02, 0.2, center=(0, yf - 0.002, gz))
    parts.append(E.P(V, F, "BH_Emissive", "fire"))
    for x in np.linspace(-0.12, 0.12, 5):
        V, F = M.box(0.022, 0.03, 0.22, center=(x, yf - 0.014, gz))
        parts.append(E.P(V, F, "BH_DarkSteel", "bar"))
    for z in (gz - 0.11, gz + 0.11):
        V, F = M.box(0.33, 0.032, 0.03, center=(0, yf - 0.014, z))
        parts.append(M.bevel(E.P(V, F, "BH_DarkSteel", "grilleframe"), 0.004, 1))
    # soot-stained lower panel with a cross brace + rivets
    for a in (35, -35):
        V, F = M.box(0.04, 0.02, 0.42, center=(0, yf - 0.006, zc - 0.17))
        parts.append(E.P(V, F, "BH_DarkSteel", "brace").rot(Ry(a), center=(0, 0, zc - 0.17)))
    for x in (-0.21, 0.21):
        for z in np.linspace(zc - Hh / 2 + 0.05, zc + Hh / 2 - 0.05, 5):
            parts.append(E.rivet_on((x, yf - 0.016, z), (0, -1, 0), 0.012, "BH_Rust"))
    # hinge knuckles on +X, latch lever on -X
    for z in (zc + 0.24, zc - 0.24):
        V, F = M.lathe([(0, -0.05), (0.024, -0.05), (0.024, 0.05), (0, 0.05)], 8)
        parts.append(E.P(V, F, "BH_Rust", "hinge").move((W / 2 + 0.02, yf + 0.02, z)))
    parts.append(rtube([(-W / 2 - 0.01, yf - 0.03, zc + 0.02), (-W / 2 + 0.06, yf - 0.05, zc + 0.02),
                        (-W / 2 + 0.1, yf - 0.035, zc - 0.03)], 0.012, "BH_Rust", n=5))
    V, F = M.tube([(-0.1, -0.035, 0.0), (-0.06, 0.02, 0.0), (0.06, 0.02, 0.0), (0.1, -0.035, 0.0)],
                  [(0.014, 0.035)] * 4, n=6, up=(0, 0, 1))
    parts.append(E.P(V, F, "BH_Horn", "handle"))
    return parts
