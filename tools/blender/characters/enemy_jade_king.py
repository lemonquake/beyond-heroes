"""Quorrath, the Jade Sleeper (bh-029, Builder M5, BOSS of the Jade Sepulchre): the last Wirewright king, a ~4 m
mummified lord in jade throne-armour. Under the armour he is funeral linen and dried flesh bound with white-glowing
wire. The armour: a cuirass of jade plaques stitched in gold with its breast broken open - inside the cavity, under
bone-white ribs, three coils of wire burn white round their cores (the current that woke him); stepped jade
pauldrons edged with turquoise; a long kilt of jade plaque rows over a scarlet loincloth; jade greaves; gold collars
and armlets. His face is a carved jade death-mask with white eye slits under a towering crown: stacked jade tiers
banded in gold with a serpent medallion and a great fan of long teal-and-scarlet feathers behind. A cape of
feathers hangs from his shoulders (cape bones, secondary motion).

Weapon.R: the serpent sceptre - a tall gold-banded jade staff wound with gold wire, crowned by a rearing jade
serpent head with white eyes and gold fangs over a feather collar. Left hand: an open linen-wrapped claw with long
jade nail-guards (casting).

Authored at true size (SCALE 1.95: crown top ~4.1 m, head top ~3.5 m) in the standard 1.8 m space (K kit SB).
Clips: boss_roar boss_slam boss_summon cast_area cast_heavy cast_ultimate staff_heavy (+ boss_sweep, cast_quick,
the enemy base set)."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import char_knight as KN
import enemy_bandit_cutthroat as K
import kit_a_common as A
import enemy_glyphbound_warrior as Z
import enemy_jade_sleeper as J

SCALE = 1.95
PROPS = proportions(SCALE, shoulder_x=0.205 * SCALE, hip_x=0.095 * SCALE)
EXTRA_BONES = [(n, tuple(np.array(h) * SCALE), tuple(np.array(t) * SCALE), par, z) for (n, h, t, par, z) in KN.CAPE_BONES]
PREVIEW_HEIGHT = 4.6
PALETTE = "jade_king"
PALETTE_COLORS = {
    "BH_Stone": ((0.1, 0.42, 0.29), 0.0, 0.26, None, 0.0, 1.0),               # polished jade
    "BH_Horn": ((0.1, 0.48, 0.46), 0.0, 0.3, None, 0.0, 1.0),                 # turquoise
    "BH_Cloth_Primary": ((0.52, 0.46, 0.35), 0.0, 0.95, None, 0.0, 1.0),      # funeral linen
    "BH_Cloth_Secondary": ((0.36, 0.05, 0.035), 0.0, 0.9, None, 0.0, 1.0),    # scarlet loincloth
    "BH_Skin": ((0.14, 0.095, 0.07), 0.0, 0.7, None, 0.0, 1.0),               # dried flesh
    "BH_Bone": ((0.62, 0.57, 0.46), 0.0, 0.6, None, 0.0, 1.0),                # ribs, quills
    "BH_Hair": ((0.035, 0.29, 0.26), 0.0, 0.7, None, 0.0, 1.0),               # teal feathers
    "BH_Flesh": ((0.5, 0.07, 0.04), 0.0, 0.7, None, 0.0, 1.0),                # scarlet feather tips
    "BH_Fur": ((0.03, 0.06, 0.05), 0.0, 0.8, None, 0.0, 1.0),                 # cape backing
    "BH_Gold": ((0.76, 0.54, 0.2), 1.0, 0.3, None, 0.0, 1.0),
    "BH_Shadow": ((0.012, 0.014, 0.012), 0.0, 0.85, None, 0.0, 1.0),
    "BH_Emissive": J.WHITE_GLOW,                                               # chest coils, eyes, bindings
}
CLIPS = ["boss_roar", "boss_slam", "boss_summon", "cast_area", "cast_heavy", "cast_ultimate", "staff_heavy",
         "boss_sweep", "cast_quick"]

TORSO = [(r[0], r[1] * 1.08, r[2] * 1.02, r[3] * 1.04, r[4] * 0.6) for r in K.TORSO]
AG = 0.03                    # armour stand-off over the body
P = Z.P


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


def secondary(anim, frames):
    return KN.secondary(anim, frames)


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.96], n=24, cap1=True)
    sb.add(P(V, F, "BH_Cloth_Primary", "body"), weights=K.TORSO_W)
    cuirass(sb)
    chest_cavity(sb)
    kilt(sb)
    cape(sb)
    head(sb)
    for s in ("L", "R"):
        arm(sb, s)
        leg(sb, s)
    K.trousers(sb, "BH_Cloth_Primary", loose=1.0, end=0.85)
    K.boots(sb, "BH_Cloth_Primary", "BH_Stone", shaft_top=0.3, cuff=False, wraps="BH_Gold")
    K.add_fist(sb, "R", "BH_Cloth_Primary", "BH_Cloth_Primary", scale=1.0)
    for prt in A.open_palm(sb.b, "L", "BH_Cloth_Primary", s=SCALE):
        sb.add_real(prt, "hand.L")
    for prt in A.bony_fingers(sb.b, "L", "BH_Cloth_Primary", length=0.115 * SCALE, r=0.0072 * SCALE, curl=0.7,
                              spread=1.15, nails="BH_Stone", open_hand=True):
        sb.add_real(prt, "hand.L")
    K.add_weapon(sb, "R", serpent_sceptre(SCALE))


# ================================================================================================= armour
def in_cavity(f, z):
    f = (f + 0.5) % 1.0 - 0.5
    return abs(f) < 0.055 and 1.17 < z < 1.42


def cuirass(sb):
    rows = K.grow_rows(TORSO, AG)
    V, F = torso_loft([r for r in rows if 0.98 <= r[0] <= 1.5], n=28)
    sb.add(P(V, F, "BH_Shadow", "underarmour"), weights=K.TORSO_W)
    # plaque courses all round the torso (gold-stitched), leaving the broken breast open
    for z in np.arange(1.04, 1.47, 0.062):
        cnt = 22
        for i in range(cnt):
            f = (i + 0.5 * ((int(z * 100) // 6) % 2)) / cnt
            if in_cavity(f, z):
                continue
            p, R = J.surf_frame(rows, f, z, 0.0)
            w = K.TORSO_W if z < 1.3 else None
            prt = J.plaque(p, R, 0.06, 0.056, t=0.012, bev=0.004)
            if w:
                sb.add(prt, weights=w)
            else:
                sb.add(prt, "chest")
        ring = K.ring_frac(rows, z - 0.031, 0.006, np.linspace(0, 1, 29))
        if z < 1.3:
            sb.add(A.tube(ring, 0.0045, "BH_Gold", n=4, cap=False), weights=K.TORSO_W)
        else:
            sb.add(A.tube(ring, 0.0045, "BH_Gold", n=4, cap=False), "chest")
    # broad gold collar with a turquoise ring + jade gorget plaques
    base = K.grow_rows(TORSO, AG + 0.01)
    rings = [K.ring_frac(base, z, g, np.linspace(0, 1, 28, endpoint=False))
             for z, g in ((1.51, -0.005), (1.48, 0.03), (1.44, 0.06))]
    V, F = M.loft(rings, cap0=False, cap1=False)
    sb.add(M.solidify(P(V, F, "BH_Stone", "collar"), 0.01, offset=1.0), "chest")
    rim = np.vstack([rings[-1], rings[-1][:1]])
    sb.add(A.tube(rim, 0.012, "BH_Gold", n=5, cap=False), "chest")
    ring2 = np.vstack([rings[1], rings[1][:1]])
    sb.add(A.tube(ring2, 0.009, "BH_Horn", n=4, cap=False), "chest")
    # belt: thick gold band with jade plaques
    V, F = K.band(rows, 0.975, 1.05, 0.016, -0.004, n=30)
    sb.add(P(V, F, "BH_Gold", "belt"), "hips")
    for prt in J.torso_plaques(rows, np.linspace(0, 1, 14, endpoint=False), [1.012], 0.02, 0.05, 0.05, t=0.012,
                               stitch=False):
        sb.add(prt, "hips")
    # glowing binding strands crossing the back plates
    for ph in (0.25, 0.75):
        pts = [K.ring_frac(rows, 1.1 + 0.32 * t, 0.016, [ph + 0.12 * (t - 0.5)])[0] for t in np.linspace(0, 1, 9)]
        sb.add(A.tube(pts, 0.005, "BH_Emissive", n=4), weights=K.TORSO_W)


def chest_cavity(sb):
    """The broken breast: a dark cavity, three white wire coils round glowing cores, bone ribs across the opening,
    jagged plaque edges and gold wire torn loose."""
    rows = K.grow_rows(TORSO, AG)
    zc = 1.3
    y0 = front_y(rows, 0, zc)
    sb.add(A.ball((0, y0 + 0.02, zc), 0.1, "BH_Shadow", n=12, rings=7, scale=(0.8, 0.45, 1.3)), "chest")
    for x, z0, z1 in ((-0.045, 1.2, 1.4), (0.0, 1.18, 1.42), (0.045, 1.2, 1.4)):
        y = front_y(rows, x, zc) + 0.005
        sb.add(A.tube([(x, y, z0), (x, y, z1)], 0.011, "BH_Emissive", n=6), "chest")
        sb.add(Z.coil((x, y, z0 + 0.01), (x, y, z1 - 0.01), 0.019, 7, 0.0045, "BH_Gold", n=4, pts_per_turn=8), "chest")
        for zz in (z0, z1):
            sb.add(A.tube([(x, y, zz - 0.008), (x, y, zz + 0.008)], 0.024, "BH_Gold", n=8), "chest")
    # ribs across the opening (bone), curving round from the sides
    for z in (1.2, 1.26, 1.32, 1.38):
        pts = [(x, front_y(rows, x, z) - 0.018 - 0.008 * (1 - (x / 0.08) ** 2), z - 0.012 * abs(x) / 0.08)
               for x in np.linspace(-0.085, 0.085, 7)]
        sb.add(A.tube(pts, 0.0075, "BH_Bone", n=5), "chest")
    # jagged broken plaque edges round the hole
    rng = np.random.default_rng(11)
    for k in range(10):
        a = 2 * math.pi * k / 10
        f = 0.06 * math.cos(a)
        z = zc + 0.13 * math.sin(a)
        p, R = J.surf_frame(rows, f % 1.0, z, 0.0)
        out = R[:, 0] * math.cos(a) + R[:, 2] * math.sin(a)
        sb.add(A.shard(p - out * 0.01, out * 0.7 - R[:, 1] * 0.3, 0.045 + 0.02 * rng.random(), 0.016, "BH_Stone",
                       sides=4, up=tuple(R[:, 2])), "chest")
    # torn gold wires hanging from the edge of the hole
    for x, ln in ((-0.06, 0.12), (0.05, 0.09)):
        q = np.array([x, front_y(rows, x, 1.17) - 0.012, 1.17])
        sb.add(A.tube([q, q + (0.01, -0.02, -ln * 0.5), q + (0.004, -0.015, -ln)], 0.003, "BH_Gold", n=4), "chest")


def kilt(sb):
    rows = K.grow_rows(TORSO, AG + 0.02)
    # scarlet loincloth under the plaques
    import enemy_hollow_soldier as HS
    for front in (True, False):
        pnl = HS.cloth_panel(rows, 1.0, 0.42, lambda z: 0.1, front=front, nu=5, nv=7, mat="BH_Cloth_Secondary",
                             gap=0.012, hang=0.06, rag=0.02, teeth=4, thick=0.008, belt_z=0.98, seed=3.0)
        sb.add(pnl, weights=Z.centre_w(0.98, 0.5, 0.5))
    # plaque panels: front / back hanging straight, and one per side (thigh), rows of plaques on gold bead strings
    for panel, (x0, ang, mode) in enumerate(((0.0, 0.0, "front"), (0.0, 180.0, "back"), (1.0, 90.0, "L"),
                                             (-1.0, -90.0, "R"))):
        cols = 3 if mode in ("front", "back") else 2
        for ci in range(cols):
            for ri, z in enumerate(np.linspace(0.93, 0.6, 5)):
                u = (ci - (cols - 1) / 2) * 0.062
                drop = 0.98 - z
                if mode == "front":
                    c = np.array([u, front_y(rows, u, 0.98) - 0.02 - 0.06 * drop, z])
                    R = np.eye(3)
                    w = Z.centre_w(0.98, 0.5, 0.55)
                elif mode == "back":
                    c = np.array([u, back_y(rows, u, 0.98) + 0.02 + 0.08 * drop, z])
                    R = Rz(180)
                    w = Z.centre_w(0.98, 0.5, 0.5)
                else:
                    sx = 1 if mode == "L" else -1
                    q, RR = J.surf_frame(rows, 0.25 if sx > 0 else 0.75, 0.98, 0.0)
                    out = -RR[:, 1]
                    c = q + out * (0.02 + 0.07 * drop) + RR[:, 0] * u * sx
                    c[2] = z
                    R = np.stack([RR[:, 0], RR[:, 1], np.array([0, 0, 1.0])], 1)
                    lb = "thigh." + mode
                    w = (lambda V, lb=lb: [{"hips": 0.45, lb: 0.55}] * len(V))
                V2, F2 = M.box(0.054, 0.012, 0.064)
                prt = M.bevel(P(V2, F2, "BH_Stone" if (ri + ci) % 4 else "BH_Horn", "kiltplaque"), 0.003, 1)
                if mode in ("front", "back"):
                    prt.rot(R).move(c)
                else:
                    prt.rot(R).move(c)
                sb.add(prt, weights=w)
                sb.add(A.ball(c + np.array([0, 0, 0.038]), 0.008, "BH_Gold", n=5, rings=3), weights=w)


def cape_w():
    def wfn(V):
        out = []
        for v in V:
            z = v[2]
            if z > 1.42:
                out.append({"chest": 1.0})
            elif z > 1.3:
                t = float(smoothstep(1.3, 1.42, z))
                out.append({"chest": t, "cape.1": 1 - t})
            elif z > 1.14:
                out.append({"cape.1": 1.0})
            elif z > 1.0:
                t = float(smoothstep(1.0, 1.14, z))
                out.append({"cape.1": t, "cape.2": 1 - t})
            else:
                out.append({"cape.2": 1.0})
        return out
    return wfn


def cape(sb):
    """Feather cape: a dark backing sheet and rows of long teal feathers, the hem rows scarlet-tipped."""
    rows = K.grow_rows(TORSO, AG + 0.02)

    def fn(u, v):
        zb = 0.3 + 0.05 * math.cos((u - 0.5) * math.pi)
        z = 1.48 + (zb - 1.48) * v
        side = (u - 0.5) * 2
        half = 0.2 + 0.18 * v ** 0.8
        x = side * half
        yb = back_y(rows, np.clip(x, -0.15, 0.15), min(max(z, 1.3), 1.46)) + 0.05 * (1 - abs(side))
        y = yb + 0.13 * v ** 1.2 + 0.03 * (1 - v) * (1 - side * side)
        y -= 0.1 * abs(side) ** 2.2 * v ** 0.9
        return (x, y, z)
    V, F = M.grid(fn, 11, 10)
    w = cape_w()
    back = P(V, F, "BH_Fur", "cape")
    N = np.zeros_like(V)
    for f in F:
        a, b_, c = V[f[0]], V[f[1]], V[f[2]]
        n = np.cross(b_ - a, c - a)
        for i in f:
            N[i] += n
    if np.mean(N[:, 1]) < 0:
        back.flip()
    sb.add(M.solidify(back, 0.012, offset=-1.0), weights=w)

    def nrm_at(u, v):
        e = 0.02
        p0 = np.array(fn(u, v))
        du = np.array(fn(min(u + e, 1), v)) - np.array(fn(max(u - e, 0), v))
        dv = np.array(fn(u, min(v + e, 1))) - np.array(fn(u, max(v - e, 0)))
        n = normalize(np.cross(du, dv))
        return p0, (n if n[1] > 0 else -n), normalize(dv), normalize(du)
    for ri, (v, cnt, ln, wd, tipm) in enumerate(((0.1, 8, 0.24, 0.07, None), (0.32, 9, 0.28, 0.08, None),
                                                 (0.55, 10, 0.3, 0.085, "BH_Flesh"), (0.8, 10, 0.3, 0.085,
                                                                                       "BH_Flesh"))):
        for i in range(cnt):
            u = (i + 0.5 * (ri % 2) + 0.25) / (cnt + 0.5)
            p, n, dv, du = nrm_at(u, v)
            d = normalize(dv + n * 0.12)
            for prt in Z.zfeather(p + n * (0.014 + 0.004 * ri), d, ln, wd, du, mats=("BH_Hair", tipm),
                                  tip=0.3 if tipm else 0, bend=-0.04, quill=False, k=5):
                sb.add(prt, weights=w)


# ================================================================================================= head
def head(sb):
    K.neck_and_head(sb, skin="BH_Cloth_Primary", face=False)
    for z in (1.5, 1.545):
        sb.add(J.linen_wrap((0, 0.0, z - 0.02), (0, -0.004, z + 0.02), 0.055, 1.2, width=0.024), weights=K.HEAD_W)
    parts, surf = J.death_mask(1.596, width=0.162, height=0.2, ytop=-0.085, bulge=0.026)
    for prt in parts:
        sb.add(prt, "head")
    # jade ear flares with gold rims and hanging jade beads
    for sx in (1, -1):
        V, F = M.lathe([(0.0, -0.008), (0.036, -0.007), (0.04, 0.0), (0.036, 0.01), (0.0, 0.008)], 14)
        sb.add(P(V, F, "BH_Stone", "flare").rot(Ry(90 * sx)).move((sx * 0.085, 0.0, 1.69)), "head")
        sb.add(A.tube([(sx * 0.093, 0.0, 1.69 - 0.0), (sx * 0.097, 0.0, 1.69)], 0.04, "BH_Gold", n=12), "head")
        for prt in Z.beads([(sx * 0.092, -0.005, 1.66), (sx * 0.094, -0.01, 1.56)], 0.01, ("BH_Stone", "BH_Gold")):
            sb.add(prt, "head")
    crown(sb)


def crown(sb):
    """Towering crown: stacked jade tiers widening upward (octagonal), gold bands, a serpent medallion in front, a
    fan of long feathers behind."""
    z = 1.775
    tiers = ((0.1, 0.045), (0.11, 0.045), (0.121, 0.05), (0.133, 0.05))
    for k, (r, h) in enumerate(tiers):
        V, F = M.lathe([(0.0, z), (r, z), (r, z + h), (0.0, z + h)], 8, a0=22.5, a1=382.5)
        sb.add(M.bevel(P(V, F, "BH_Stone", "tier").scale((1.0, 1.08, 1.0)), 0.006, 1), "head")
        V, F = M.lathe([(r + 0.006, z - 0.006), (r + 0.006, z + 0.012), (0.0, z + 0.012), (0.0, z - 0.006)], 8,
                       a0=22.5, a1=382.5)
        sb.add(P(V, F, "BH_Gold", "tierband").scale((1.0, 1.08, 1.0)), "head")
        # turquoise studs round each tier
        for i in range(8):
            a = 2 * math.pi * (i + 0.5) / 8
            if k % 2:
                a += math.pi / 8
            rr = r * math.cos(math.pi / 8) + 0.004
            sb.add(A.ball((rr * math.sin(a), -rr * 1.08 * math.cos(a), z + h * 0.55), 0.012, "BH_Horn", n=6, rings=3,
                          scale=(1, 1, 1)), "head")
        z += h
    top = z
    V, F = M.lathe([(0.0, top), (0.145, top), (0.145, top + 0.02), (0.0, top + 0.02)], 8, a0=22.5, a1=382.5)
    sb.add(P(V, F, "BH_Stone", "cap").scale((1.0, 1.08, 1.0)), "head")
    # serpent medallion on the front: a jade disc with a coiled serpent in gold and white eyes
    c = np.array([0.0, -0.142, 1.86])
    V, F = M.lathe([(0.0, -0.01), (0.06, -0.01), (0.066, 0.0), (0.06, 0.014), (0.0, 0.016)], 16)
    sb.add(P(V, F, "BH_Stone", "medallion").rot(Rx(90)).move(c), "head")
    spiral = [c + (0.05 * (1 - t * 0.7) * math.cos(6 * t), -0.016, 0.05 * (1 - t * 0.7) * math.sin(6 * t))
              for t in np.linspace(0, 1, 16)]
    sb.add(A.tube(spiral, [0.008 * (1 - 0.5 * t) for t in np.linspace(0, 1, 16)], "BH_Gold", n=4), "head")
    for sx in (1, -1):
        sb.add(A.ball(c + (sx * 0.012, -0.022, 0.012), 0.007, "BH_Emissive", n=6, rings=3), "head")
    # side jade wings of the crown (flat stepped plates)
    for sx in (1, -1):
        for k in range(3):
            V, F = M.box(0.02, 0.08 - 0.015 * k, 0.05)
            sb.add(M.bevel(P(V, F, "BH_Stone", "wing").move((sx * (0.15 + 0.02 * k), 0.0, 1.82 + 0.04 * k)), 0.004,
                           1), "head")
    # the great feather fan: long teal feathers tipped scarlet, tilted back, an inner fan of shorter ones
    base = np.array([0.0, 0.11, top - 0.05])
    tb = math.radians(24)
    n = 15
    for i in range(n):
        a = math.radians(-82 + 164 * i / (n - 1))
        d = np.array([math.sin(a), math.sin(tb) * math.cos(a), math.cos(tb) * math.cos(a)])
        tng = np.array([math.cos(a), -math.sin(tb) * math.sin(a), -math.cos(tb) * math.sin(a)])
        ln = 0.3 + 0.13 * math.cos(a) ** 2
        for prt in Z.zfeather(base + d * 0.03, d, ln, 0.085, tng, tip=0.26, bend=0.06, k=7):
            sb.add(prt, "head")
    for i in range(7):
        a = math.radians(-60 + 120 * i / 6)
        d = np.array([math.sin(a), math.sin(tb - 0.12) * math.cos(a), math.cos(tb - 0.12) * math.cos(a)])
        tng = np.array([math.cos(a), 0.0, -math.sin(a)])
        for prt in Z.zfeather(base + d * 0.02 + (0, -0.015, 0), d, 0.26, 0.06, tng, mats=("BH_Flesh", None), tip=0,
                              k=6):
            sb.add(prt, "head")


# ================================================================================================= limbs
def arm(sb, s):
    sx = 1 if s == "L" else -1
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    K.bare_arm(sb, s, skin="BH_Cloth_Primary", r_up=0.048, r_fore=0.042, r_wrist=0.032, bulk=1.05)
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    sb.add(J.linen_wrap(sh + (el - sh) * 0.1, el - (el - sh) * 0.05, 0.053, 3.2, width=0.028), ua)
    sb.add(J.glow_wrap(sh + (el - sh) * 0.3, sh + (el - sh) * 0.85, 0.056, 2.0, phase=0.5), ua)
    # stepped jade pauldron: three plates stacked like a stepped roof, turquoise edges
    for k, (dz, r, ox) in enumerate(((0.07, 0.11, 0.0), (0.03, 0.12, 0.03), (-0.01, 0.12, 0.055))):
        c = sh + np.array([sx * (0.0 + ox), 0.0, dz])
        V, F = M.lathe([(0.0, 0.03), (r * 0.75, 0.024), (r, 0.0), (r, -0.016), (0.0, -0.016)], 16)
        pl = P(V, F, "BH_Stone", "pauldron").scale((1.0, 1.15, 0.8)).rot(Ry(-sx * (24 + 10 * k))).move(c)
        sb.add(M.bevel(pl, 0.004, 1), weights=lambda V, s=s: [{"shoulder." + s: 0.55, "upper_arm." + s: 0.45}] * len(V))
        ring = [c + Ry(-sx * (24 + 10 * k)) @ np.array([r * math.cos(a), r * 1.15 * math.sin(a), -0.012]) for a in
                np.linspace(0, 2 * math.pi, 21)]
        sb.add(A.tube(ring, 0.008, "BH_Horn", n=4, cap=False),
               weights=lambda V, s=s: [{"shoulder." + s: 0.55, "upper_arm." + s: 0.45}] * len(V))
    cc = sh + np.array([sx * 0.0, 0.0, 0.1])
    sb.add(A.ball(cc + Ry(-sx * 24) @ np.array([0, 0, 0.01]), 0.022, "BH_Gold", n=8, rings=5),
           weights=lambda V, s=s: [{"shoulder." + s: 0.55, "upper_arm." + s: 0.45}] * len(V))
    # gold armlet, jade bracer plaques, gold wrist cuff
    dd = normalize(el - sh)
    c = sh + (el - sh) * 0.72
    sb.add(A.tube([c - dd * 0.02, c + dd * 0.02], 0.058, "BH_Gold", n=12), ua)
    Ax = sb.axes(fa)
    for k in range(7):
        a = 2 * math.pi * k / 7
        nrm = Ax[:, 0] * math.cos(a) + Ax[:, 2] * math.sin(a)
        cp = el + (wr - el) * 0.62 + nrm * 0.05
        R = np.stack([np.cross(Ax[:, 1], nrm), -nrm, Ax[:, 1]], 1)
        sb.add(J.plaque(cp, R, 0.036, 0.12, t=0.01), fa)
    sb.add(A.tube([el + (wr - el) * 0.9, el + (wr - el) * 0.98], 0.053, "BH_Gold", n=12), fa)
    sb.add(A.tube([el + (wr - el) * 0.36, el + (wr - el) * 0.4], 0.055, "BH_Gold", n=12), fa)
    if s == "L":
        L, Afr = A.hand_frame(sb.b, s)
        for k in range(4):
            y = (-0.03 + 0.02 * k) * 1.15
            lk = 0.115 * (0.85 + 0.15 * (k in (1, 2)))
            tip0 = L(0.02 * SCALE + lk * 0.8 * SCALE, y * 1.45 * SCALE, -lk * 0.25 * 0.7 * SCALE)
            tip1 = L(0.02 * SCALE + lk * 1.05 * SCALE, y * 1.6 * SCALE, -lk * 0.65 * 0.7 * SCALE)
            sb.add_real(A.taper([tip0, tip1], 0.009 * SCALE, 0.0015 * SCALE, "BH_Stone", n=5), ha)


def leg(sb, s):
    th, sh = "thigh." + s, "shin." + s
    h, k, a = sb.head(th), sb.head(sh), sb.tail(sh)
    sb.add(J.linen_wrap(h + (k - h) * 0.3, k - (k - h) * 0.05, 0.08, 3.0, width=0.032), th)
    sb.add(J.glow_wrap(h + (k - h) * 0.45, h + (k - h) * 0.8, 0.084, 1.4, phase=1.0 if s == "L" else 2.4), th)
    # jade greave: a curved plate on the front of the shin with a gold rim, a knee boss
    for i, u in enumerate((0.15, 0.36, 0.57, 0.76)):
        c = k + (a - k) * u + np.array([0, -0.062, 0])
        R = np.stack([np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), normalize(k - a)], 1)
        sb.add(J.plaque(c, R, 0.085 - 0.008 * i, 0.09, t=0.014), sh)
        for sxx in (1, -1):
            q = k + (a - k) * u + np.array([sxx * 0.05, -0.035, 0])
            Rs = np.stack([np.array([0, -sxx * 1.0, 0]) * -1, np.array([-sxx * 1.0, 0, 0]), normalize(k - a)], 1)
            sb.add(J.plaque(q, Rs, 0.04, 0.09, t=0.012, mat="BH_Horn" if i % 2 else "BH_Stone"), sh)
    sb.add(A.ball(k + (0, -0.065, 0.0), 0.05, "BH_Stone", n=12, rings=6, scale=(1, 0.5, 1)),
           weights=lambda V, s=s: [{"thigh." + s: 0.4, "shin." + s: 0.6}] * len(V))
    sb.add(A.ball(k + (0, -0.088, 0.0), 0.018, "BH_Gold", n=8, rings=4),
           weights=lambda V, s=s: [{"thigh." + s: 0.4, "shin." + s: 0.6}] * len(V))


# ================================================================================================= sceptre
def serpent_sceptre(s=1.0):
    """Sceptre (weapon space: grip at origin, +Z up, faces -Y): ~1.95 m standard. A jade staff in gold bands wound
    with gold wire, a feather collar, a rearing jade serpent head with white eyes and gold fangs."""
    parts = []
    parts.append(A.tube([(0, 0, -0.92), (0, 0, 0.88)], [0.024, 0.022], "BH_Stone", n=8))
    V, F = M.lathe([(0.0, -1.02), (0.012, -1.02), (0.032, -0.95), (0.03, -0.9), (0.0, -0.9)], 8)
    parts.append(P(V, F, "BH_Gold", "foot"))
    for z in (-0.6, -0.3, 0.2, 0.5, 0.86):
        V, F = M.lathe([(0.0, z - 0.02), (0.03, z - 0.02), (0.033, z), (0.03, z + 0.02), (0.0, z + 0.02)], 8)
        parts.append(P(V, F, "BH_Gold", "band"))
    parts.append(Z.coil((0, 0, -0.12), (0, 0, 0.14), 0.027, 6, 0.0045, "BH_Gold", n=4, pts_per_turn=8))
    parts.append(Z.coil((0, 0, 0.24), (0, 0, 0.46), 0.026, 4, 0.004, "BH_Emissive", n=4, pts_per_turn=8))
    # feather collar under the head
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = normalize(np.array([0.6 * math.cos(a), 0.6 * math.sin(a), -1.0]))
        parts += Z.zfeather((0.03 * math.cos(a), 0.03 * math.sin(a), 0.9), d, 0.17, 0.05,
                            (-math.sin(a), math.cos(a), 0), tip=0.3, bend=0.02, quill=False, k=5)
    # rearing serpent: an S-curved neck and a big head facing -Y
    neck = [(0, 0, 0.86), (0, 0.04, 0.96), (0, 0.05, 1.06), (0, 0.0, 1.14), (0, -0.07, 1.17)]
    parts.append(A.tube(neck, [0.03, 0.036, 0.04, 0.042, 0.044], "BH_Stone", n=10))
    for k in range(4):
        q = (np.array(neck[k]) + np.array(neck[k + 1])) / 2
        parts.append(A.ball(q, 0.043 + 0.002 * k, "BH_Gold" if k % 2 else "BH_Stone", n=10, rings=3,
                            scale=(1, 1, 0.35)))
    upper = [(0, -0.06, 1.18), (0, -0.12, 1.19), (0, -0.19, 1.185), (0, -0.24, 1.17)]
    parts.append(A.tube(upper, [(0.055, 0.04), (0.054, 0.036), (0.04, 0.026), (0.018, 0.014)], "BH_Stone", n=10,
                        p=2.6))
    lower = [(0, -0.07, 1.15), (0, -0.13, 1.11), (0, -0.19, 1.085), (0, -0.22, 1.075)]
    parts.append(A.tube(lower, [(0.04, 0.016), (0.036, 0.014), (0.026, 0.01), (0.014, 0.007)], "BH_Stone", n=8, p=2.4))
    parts.append(A.tube([(0, -0.09, 1.155), (0, -0.2, 1.135)], [(0.03, 0.014), (0.018, 0.008)], "BH_Shadow", n=6))
    for sx in (1, -1):
        parts.append(A.taper([(sx * 0.024, -0.21, 1.165), (sx * 0.022, -0.215, 1.115)], 0.008, 0.0012, "BH_Gold", n=4))
        parts.append(A.ball((sx * 0.04, -0.12, 1.21), 0.013, "BH_Emissive", n=8, rings=4))
        parts.append(A.tube([(sx * 0.025, -0.08, 1.23), (sx * 0.045, -0.13, 1.225), (sx * 0.035, -0.18, 1.205)],
                            0.011, "BH_Stone", n=4))
    # a crest of feathers on the serpent's head
    for k in range(5):
        a = math.radians(-40 + 20 * k)
        d = normalize(np.array([math.sin(a) * 0.6, 0.55, math.cos(a)]))
        parts += Z.zfeather((0, -0.06, 1.22), d, 0.2, 0.055, (math.cos(a), 0, -math.sin(a)), tip=0.3, bend=0.03,
                            quill=False, k=6)
    for p in parts:
        p.V = p.V * s
    return parts
