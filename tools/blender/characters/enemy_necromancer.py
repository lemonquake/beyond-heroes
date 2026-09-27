"""Necromancer (bh-010, Builder A; undead summoner caster): a tall, gaunt, slightly hunched grave-priest in layered,
tattered black and violet robes. A high collar of curved rib bones fans up behind the head (the silhouette key), a
ribcage breastplate is strapped over the robe, the face is a pale skull with sunken violet-glowing eyes under a
circlet of finger bones. Long bony fingers (the left hand open and clawed), a rope belt hung with bone charms and
small skulls, and a long bone staff topped with an iron cage holding a skull wreathed in violet grave-light.
~1.95 m to the crown (the rib collar rises higher behind it). Robe helpers: enemy_ashen_cultist; kit:
enemy_bandit_cutthroat (standard-space authoring)."""
import math
import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz, R_axis
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C
import enemy_hollow_soldier as HS
import kit_a_common as A

SCALE = 1.95 / 1.83
PROPS = proportions(SCALE, shoulder_x=0.172 * SCALE, hip_x=0.09 * SCALE, upper_len=0.3 * SCALE,
                    fore_len=0.285 * SCALE, hand_len=0.11 * SCALE)
PALETTE = "necromancer"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.03, 0.022, 0.04), 0.0, 0.9, None, 0.0, 1.0),        # black grave-robe
    "BH_Cloth_Secondary": ((0.17, 0.045, 0.24), 0.0, 0.85, None, 0.0, 1.0),     # violet over-robe / stole
    "BH_Skin": ((0.56, 0.54, 0.58), 0.0, 0.55, None, 0.0, 1.0),                 # corpse-pale, skull face
    "BH_Bone": ((0.62, 0.58, 0.47), 0.0, 0.6, None, 0.0, 1.0),                  # collar ribs, staff, charms
    "BH_Leather": ((0.05, 0.035, 0.03), 0.0, 0.7, None, 0.0, 1.0),              # straps, rope, boots
    "BH_DarkSteel": ((0.1, 0.095, 0.11), 1.0, 0.5, None, 0.0, 1.0),             # lantern cage, buckles
    "BH_Shadow": ((0.02, 0.012, 0.03), 0.0, 0.8, None, 0.0, 1.0),               # sockets / mouth
    "BH_Emissive": ((0.62, 0.3, 1.0), 0.0, 0.4, (0.64, 0.3, 1.0), 9.0, 1.0),    # violet grave-light
    "BH_Horn": ((0.3, 0.25, 0.2), 0.0, 0.7, None, 0.0, 1.0),                    # old bone (darker charms)
}
CLIPS = ["staff_1", "cast_quick", "cast_area", "cast_heavy", "cast_weapon", "boss_summon"]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


# gaunt torso (narrow chest, slight hump at the upper back)
TORSO = [(r[0], r[1] * 0.88, r[2] * 0.84, r[3] * (0.9 + 0.35 * max(0.0, 1 - abs(r[0] - 1.42) / 0.1)), r[4] * 0.6)
         for r in K.TORSO]
G = 0.012
CHEST_W = K.zspec_w([(1.2, "spine"), (1.3, "chest")])
HEAD_DY, HEAD_DZ = -0.028, -0.018       # head carried forward and low (hunch)


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="body"), weights=C.ROBE_W)
    # ---- robes: black under-robe to the floor (ragged), violet over-robe front panels, black tattered back drape
    C.robe_top(sb, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", g=G, rows=TORSO, v_open=0.04)
    C.robe_skirt(sb, "BH_Cloth_Primary", trim=None, z_top=1.07, z_bot=0.06, flare=0.16, folds=0.016, ragged=0.07,
                 g=G - 0.02)
    over_robe(sb)
    sash_and_charms(sb)
    # ---- ribcage breastplate + high rib collar
    ribcage_plate(sb)
    rib_collar(sb)
    # ---- head: pale skull face, circlet of finger bones, violet eyes
    head(sb)
    # ---- arms: bell sleeves with tatters, long bony hands
    for s in ("L", "R"):
        C.bell_sleeve(sb, s, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", cuff_r=0.078, end=0.74)
        sleeve_tatters(sb, s)
    K.add_fist(sb, "R", "BH_Skin", "BH_Skin", scale=0.95)
    for prt in A.bony_fingers(sb.b, "R", "BH_Skin", length=0.06 * SCALE, r=0.0068 * SCALE, curl=0.6,
                              nails="BH_Shadow", s=1.0):
        sb.add_real(prt, "hand.R")
    for prt in A.open_palm(sb.b, "L", "BH_Skin", s=SCALE * 0.95):
        sb.add_real(prt, "hand.L")
    for prt in A.bony_fingers(sb.b, "L", "BH_Skin", length=0.13 * SCALE, r=0.0068 * SCALE, curl=0.8, spread=1.05,
                              nails="BH_Shadow", open_hand=True):
        sb.add_real(prt, "hand.L")
    # ---- legs (mostly hidden) + pointed boots
    K.trousers(sb, "BH_Cloth_Primary", loose=0.85)
    K.boots(sb, "BH_Leather", "BH_Leather", shaft_top=0.35, cuff=False, wraps="BH_Horn")
    # ---- staff
    K.add_weapon(sb, "R", lantern_staff(SCALE))


# ================================================================================================= robes
def over_robe(sb):
    """Violet over-robe: two long front panels from the collar to the shins (split at the centre, ragged hems) and a
    black tattered drape down the back from the shoulder blades."""
    def half(z):
        return 0.085 + 0.05 * max(0.0, 1.05 - z)
    for sx, seed in ((1, 0.8), (-1, 2.3)):
        side = "L" if sx > 0 else "R"

        def fn(u, v, sx=sx, seed=seed):
            zb = 0.34 + HS.ragged(u, seed, 0.14, 3)
            zt = 1.47
            z = zt + (zb - zt) * v
            x = sx * (0.012 + 2 * half(z) * u)
            gap = G + 0.012
            if z >= 1.05:
                y = front_y(TORSO, x, z) - gap
            else:
                y = front_y(TORSO, x, 1.05) - gap - 0.09 * (1.05 - z) ** 1.1
            y += 0.006 * math.sin(u * 7 + seed) * max(0.0, 1.05 - z) * 4
            return (x, y, z)
        V, F = M.grid(fn, 6, 12)
        p = M.Part(V, F, "BH_Cloth_Secondary", name="overrobe")
        if sx < 0:
            p.flip()
        sb.add(M.solidify(p, 0.008, offset=1.0), weights=panel_w(side))
    # back drape: hangs from the shoulders to the calves, torn into tongues
    def fn(u, v):
        zb = 0.3 + HS.ragged(u, 4.1, 0.22, 5)
        z = 1.49 + (zb - 1.49) * v
        hw = 0.16 + 0.1 * v
        x = (u - 0.5) * 2 * hw
        if z > 1.2:
            y = back_y(TORSO, x * 0.95, z) + G + 0.02
        else:
            y = back_y(TORSO, x * 0.95, 1.2) + G + 0.02 + 0.06 * (1.2 - z)
        y += 0.012 * math.sin(u * math.pi * 5) * v
        return (x, y, z)
    V, F = M.grid(fn, 9, 12)
    p = M.Part(V, F, "BH_Cloth_Primary", name="drape").flip()
    sb.add(M.solidify(p, 0.009, offset=1.0), weights=HS.cloth_w(chest_z=1.34, belt_z=1.05, leg=0.32))


def panel_w(side):
    def wfn(V):
        out = []
        for v in V:
            z = v[2]
            if z >= 1.30:
                out.append({"chest": 1.0})
            elif z >= 1.18:
                t = float(smoothstep(1.18, 1.30, z))
                out.append({"chest": t, "spine": 1 - t})
            elif z >= 1.03:
                t = float(smoothstep(1.03, 1.12, z))
                out.append({"spine": t, "hips": 1 - t} if t > 0 else {"hips": 1.0})
            else:
                s = float(smoothstep(1.0, 0.5, z)) * 0.8
                d = {"hips": 1 - s}
                if s > 1e-3:
                    d["thigh." + side] = s
                out.append(d)
        return out
    return wfn


def sash_and_charms(sb):
    V, F = K.band(TORSO, 0.99, 1.1, G + 0.04, G - 0.004, n=28)
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="sash"), "hips")
    knot = C.rope_belt(sb, z=1.02, g=G + 0.05, mat="BH_Leather", knot_frac=0.93, tails=0.3, rows=TORSO)
    # charms hanging from the belt: small skulls, finger bones and a bone disc
    charms = ((0.06, 0.16, "skull"), (0.17, 0.2, "bones"), (0.3, 0.14, "skull"), (0.62, 0.18, "bones"),
              (0.75, 0.22, "skull"), (0.85, 0.15, "disc"))
    for frac, ln, kind in charms:
        p, ang = K.on_ring(TORSO, 1.0, G + 0.058, frac)
        w = sb.skirt(1.0, 0.6, max_leg=0.45, center_w=0.05)
        bot = p + np.array([0, 0, -ln])
        sb.add(A.tube([p, (p + bot) / 2 + (0, -0.005, 0), bot], 0.0035, "BH_Leather", n=4, up=(1, 0, 0)), weights=w)
        out = normalize(np.array([p[0], p[1], 0.0]))
        if kind == "skull":
            for prt in A.skull_charm(bot + (0, 0, -0.03), 0.033, "BH_Bone", "BH_Shadow", face=out, n=8):
                sb.add(prt, weights=w)
        elif kind == "bones":
            for k, dx in enumerate((-0.012, 0.0, 0.012)):
                q = bot + np.array([dx, 0, -0.01 * k])
                sb.add(A.tube([q, q + (dx * 0.6, 0, -0.07)], 0.006, "BH_Bone", n=5), weights=w)
                sb.add(A.ball(q + (dx * 0.6, 0, -0.072), 0.009, "BH_Bone", n=5, rings=3), weights=w)
        else:
            V, F = M.lathe([(0.0, -0.005), (0.035, -0.004), (0.036, 0.0), (0.035, 0.004), (0.0, 0.005)], 10)
            disc = M.Part(V, F, "BH_Bone", name="disc").rot(Rx(90)).rot(Rz(ang)).move(bot + (0, 0, -0.035))
            sb.add(disc, weights=w)
            sb.add(A.ball(bot + (0, 0, -0.035) + out * 0.006, 0.011, "BH_Emissive", n=6, rings=4), weights=w)


def sleeve_tatters(sb, s):
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    el, wr = sb.head(fa), sb.head(ha)
    d = normalize(wr - el)
    c = el + (wr - el) * 0.72
    side = normalize(np.cross(d, (0, 1, 0)))
    fw = np.cross(side, d)
    for k, ang in enumerate((200, 250, 300, 340)):
        a = math.radians(ang)
        nrm = side * math.cos(a) + fw * math.sin(a)
        top = c + nrm * 0.074
        down = normalize(d * 0.6 + np.array([0, 0, -1.0]) * 0.8 + nrm * 0.2)
        sb.add(A.rag_strip(top, down, 0.1 + 0.04 * (k % 2), 0.045, "BH_Cloth_Primary", out=nrm, seed=k), fa)


# ================================================================================================= bone armour
def ribcage_plate(sb):
    """Ribcage breastplate strapped over the robe: a sternum and curved ribs on the chest front + two straps."""
    parts = []
    for i in range(5):
        z = 1.43 - 0.045 * i
        for sx in (1, -1):
            pts = []
            for t in np.linspace(0, 1, 7):
                x = sx * (0.012 + 0.12 * math.sin(t * 1.35))
                zz = z - 0.05 * t ** 1.5
                y = front_y(TORSO, min(abs(x), 0.12) * np.sign(x), zz) - G - 0.022 + 0.01 * t
                pts.append((x, y, zz))
            parts.append(A.taper(pts, 0.012, 0.0075, "BH_Bone", n=4, up=(0, -1, 0)))
    zt, zb = 1.45, 1.22
    pts = [(0, front_y(TORSO, 0, z) - G - 0.028, z) for z in np.linspace(zt, zb, 5)]
    V, F = M.tube(pts, [(0.02, 0.009)] * 5, n=6, up=(0, -1, 0))
    parts.append(M.Part(V, F, "BH_Bone", name="sternum"))
    for prt in parts:
        sb.add(prt, weights=CHEST_W)
    # straps around the torso holding it
    for z in (1.27, 1.36):
        ring = K.ring_frac(TORSO, z, G + 0.012, np.linspace(0.2, 0.8, 13))
        V, F = M.tube(ring, [(0.012, 0.004)] * len(ring), n=4, up=(0, 0, 1), p=3.0)
        sb.add(M.Part(V, F, "BH_Leather", name="strap"), weights=CHEST_W)


def rib_collar(sb):
    """High collar of curved rib bones standing on a bone yoke round the neck, fanning up behind and beside the head
    (tallest at the back), plus a spine of vertebrae up the centre back."""
    zb = 1.47
    # yoke: thick bone band round the base of the neck (open at the front)
    ring = []
    for a in np.linspace(-150, 150, 17):          # 0 = back (+Y)
        r = math.radians(a)
        ring.append((0.15 * math.sin(r), 0.022 + 0.11 * math.cos(r), zb + 0.01 * math.cos(r)))
    sb.add(A.tube(ring, (0.02, 0.016), "BH_Bone", n=6, up=(0, 0, 1)), "chest")
    sb.add(A.tube([(x + 0.0, y + 0.0, z + 0.022) for (x, y, z) in ring], (0.012, 0.01), "BH_Leather", n=5,
                  up=(0, 0, 1)), "chest")
    for k, a in enumerate(np.linspace(-120, 120, 9)):
        r = math.radians(a)
        back = math.cos(r)                          # 1 at the back, lower toward the sides
        h = 0.2 + 0.24 * back ** 1.5 if back > 0 else 0.2
        base = np.array([0.15 * math.sin(r), 0.022 + 0.11 * math.cos(r), zb + 0.01])
        outd = normalize(np.array([math.sin(r), math.cos(r), 0.0]))
        pts = []
        for t in np.linspace(0, 1, 7):
            flare = 0.1 * math.sin(math.pi * t * 0.85) + 0.02 * t
            pts.append(base + outd * flare + np.array([0, 0, h * t]) - outd * 0.05 * t ** 2.5)
        sb.add(A.taper(pts, 0.021, 0.005, "BH_Bone", n=6, up=tuple(outd)), "chest")
        # small knob at the rib root
        sb.add(A.ball(base + outd * 0.006, 0.02, "BH_Bone", n=6, rings=4), "chest")
    # vertebrae up the back of the collar
    for i, z in enumerate(np.linspace(zb + 0.05, zb + 0.42, 7)):
        y = 0.16 + 0.06 * math.sin(math.pi * (z - zb) / 0.5)
        V, F = M.lathe([(0, -0.011), (0.022 - 0.0015 * i, -0.01), (0.024 - 0.0015 * i, 0.0),
                        (0.022 - 0.0015 * i, 0.01), (0, 0.011)], 8)
        sb.add(M.Part(V, F, "BH_Bone", name="vert").move((0, y, z)), "chest")
        sb.add(A.taper([(0, y + 0.01, z), (0, y + 0.045, z + 0.01)], 0.008, 0.003, "BH_Bone", n=4), "chest")
    sb.add(A.tube([(0, 0.13, zb + 0.02), (0, 0.19, zb + 0.2), (0, 0.18, zb + 0.44)], 0.012, "BH_Leather", n=5),
           "chest")


# ================================================================================================= head
def head(sb):
    off = np.array([0, HEAD_DY, HEAD_DZ])
    # corpse-pale neck (sinewy)
    V, F = M.tube([(0, 0.01, 1.46), (0, -0.01 + HEAD_DY * 0.5, 1.54), (0, -0.012 + HEAD_DY, 1.62 + HEAD_DZ)],
                  [(0.042, 0.04), (0.036, 0.034), (0.038, 0.036)], n=10, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Skin", name="neck"), weights=K.HEAD_W)
    for sx in (1, -1):
        sb.add(A.tube([(sx * 0.02, -0.02, 1.47), (sx * 0.028, -0.03 + HEAD_DY * 0.6, 1.56),
                       (sx * 0.035, -0.01 + HEAD_DY, 1.63 + HEAD_DZ)], 0.009, "BH_Skin", n=5), weights=K.HEAD_W)
    parts = HS.skull(sb, eye_mat="BH_Emissive", jaw_open=9.0, s=1.06)
    for p in parts:
        if p.mat == "BH_Bone":
            p.mat = "BH_Skin"
        p.move(off)
        sb.add(p, "head")
    # sunken eye glow a little bigger (reads at distance)
    hz = sb.head("head")[2]
    ez = hz + 0.035 * 1.06 + 0.068 * 1.06 - 0.002
    for sx in (1, -1):
        sb.add(A.ball(np.array([sx * 0.031, -0.078, ez]) + off, 0.012, "BH_Emissive", n=6, rings=4,
                      scale=(1.2, 0.6, 0.8)), "head")
    # circlet of finger bones round the crown
    zc = hz + 0.035 * 1.06 + 0.15
    ring = [np.array([0.07 * math.cos(a), 0.008 + 0.08 * math.sin(a), zc - 0.012 * math.sin(a)]) + off
            for a in np.linspace(0, 2 * math.pi, 19)]
    sb.add(A.tube(ring, 0.008, "BH_DarkSteel", n=5, up=(0, 0, 1), cap=False), "head")
    for k in range(7):
        a = math.radians(-90 + (k - 3) * 26)
        base = np.array([0.07 * math.cos(a), 0.008 + 0.08 * math.sin(a), zc - 0.012 * math.sin(a)]) + off
        outd = normalize(np.array([math.cos(a), math.sin(a), 0.0]))
        h = 0.075 if k == 3 else (0.06 if k in (2, 4) else 0.045)
        tip = base + outd * 0.02 + np.array([0, 0, h])
        sb.add(A.taper([base, (base + tip) / 2 + outd * 0.004, tip], 0.008, 0.003, "BH_Bone", n=5), "head")
        if k == 3:
            sb.add(A.ball(base + outd * 0.006 + (0, 0, 0.004), 0.013, "BH_Emissive", n=6, rings=4), "head")
    # a few long lank strands of grey hair from the back of the skull
    for k, x in enumerate((-0.05, -0.02, 0.02, 0.05)):
        top = np.array([x, 0.06, hz + 0.14]) + off
        pts = [top, top + (x * 0.3, 0.035, -0.08), top + (x * 0.5, 0.05, -0.2), top + (x * 0.6, 0.06, -0.3 - 0.03 * k)]
        sb.add(A.taper(pts, 0.012, 0.004, "BH_Horn", n=5), weights=K.HEAD_W)


# ================================================================================================= staff
def lantern_staff(s=1.0):
    """Long bone staff (weapon space, grip at origin, +Z up) topped with an iron cage holding a skull wreathed in
    violet grave-light; knuckle joints along the shaft, leather grip, bone charms under the cage."""
    parts = []
    pts, prof = [], []
    for i in range(15):
        u = i / 14
        z = -1.08 + 1.66 * u
        pts.append((0.01 * math.sin(u * 7.0), 0.007 * math.cos(u * 5.0), z))
        r = 0.019 + 0.002 * math.sin(u * 19)
        prof.append((r, r))
    V, F = M.tube(pts, prof, n=8, up=(0, -1, 0))
    parts.append(M.Part(V, F, "BH_Bone", name="shaft"))
    for z in (-0.82, -0.5, -0.2, 0.2, 0.42):          # joint knobs (joined long bones)
        x = 0.01 * math.sin((z + 1.08) / 1.66 * 7.0)
        y = 0.007 * math.cos((z + 1.08) / 1.66 * 5.0)
        V, F = M.lathe([(0, -0.03), (0.022, -0.028), (0.03, -0.012), (0.026, 0.0), (0.03, 0.012), (0.022, 0.028),
                        (0, 0.03)], 8)
        parts.append(M.Part(V, F, "BH_Bone", name="joint").move((x, y, z)))
    V, F = M.lathe([(0, -0.11), (0.023, -0.11), (0.024, 0.0), (0.023, 0.11), (0, 0.11)], 8)
    parts.append(M.Part(V, F, "BH_Leather", name="grip"))
    # butt: a clawed foot of finger bones
    for k in range(3):
        a = math.radians(120 * k)
        d = np.array([math.cos(a), math.sin(a), 0.0])
        parts.append(A.taper([(0, 0, -1.04), d * 0.03 + (0, 0, -1.08), d * 0.045 + (0, 0, -1.11)], 0.009, 0.003,
                             "BH_Bone", n=4))
    # collar under the cage
    V, F = M.lathe([(0, 0.56), (0.03, 0.56), (0.05, 0.6), (0.052, 0.62), (0.0, 0.62)], 10)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="collar"))
    # the cage: six curved iron bars, two hoops, a cap with a hook ring
    zc0, zc1 = 0.61, 0.9
    for k in range(6):
        a = math.radians(60 * k + 15)
        bar = []
        for i in range(7):
            u = i / 6
            r = 0.05 + 0.062 * math.sin(math.pi * u)
            bar.append((r * math.cos(a), r * math.sin(a), zc0 + (zc1 - zc0) * u))
        parts.append(A.tube(bar, 0.0065, "BH_DarkSteel", n=5, up=(0, 0, 1)))
    for u in (0.3, 0.7):
        r = 0.05 + 0.062 * math.sin(math.pi * u)
        z = zc0 + (zc1 - zc0) * u
        V, F = M.lathe([(r, z - 0.006), (r + 0.007, z), (r, z + 0.006), (r - 0.004, z)], 14, cap=False)
        parts.append(M.Part(V, F, "BH_DarkSteel", name="hoop"))
    V, F = M.lathe([(0.052, zc1 - 0.01), (0.056, zc1), (0.03, zc1 + 0.02), (0.0, zc1 + 0.026)], 10)
    parts.append(M.Part(V, F, "BH_DarkSteel", name="cap"))
    ring = [(0.0, 0.028 * math.cos(a), zc1 + 0.052 + 0.028 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 11)]
    parts.append(A.tube(ring, 0.005, "BH_DarkSteel", n=4, up=(1, 0, 0), cap=False))
    # skull inside (faces -Y = the staff's front flat), violet eyes; grave-light core + wisp
    parts += A.skull_charm((0.0, -0.012, 0.755), 0.06, "BH_Bone", "BH_Shadow", eyes="BH_Emissive", face=(0, -1, 0),
                           n=8)
    parts.append(A.ball((0.0, 0.045, 0.76), 0.045, "BH_Emissive", n=8, rings=5, scale=(1.1, 0.8, 1.15)))
    for k in range(5):     # grave-light tongues licking up round the skull
        a = math.radians(72 * k + 30)
        b = np.array([0.045 * math.cos(a), 0.045 * math.sin(a) + 0.01, 0.72])
        parts.append(A.taper([b, b * 1.25 + (0, 0, 0.06), b * 0.6 + (0, 0, 0.12)], 0.013, 0.002, "BH_Emissive", n=4))
    V, F = M.lathe([(0.0, 0.8), (0.035, 0.83), (0.03, 0.87), (0.012, 0.93), (0.0, 0.97)], 7)
    parts.append(M.Part(V, F, "BH_Emissive", name="wisp").rot(Rz(20)))
    # charms under the cage
    for k, (a, ln) in enumerate(((40, 0.14), (160, 0.1), (280, 0.12))):
        r = math.radians(a)
        top = np.array([0.045 * math.cos(r), 0.045 * math.sin(r), 0.57])
        bot = top + np.array([0.01 * math.cos(r), 0.01 * math.sin(r), -ln])
        parts.append(A.tube([top, bot], 0.0035, "BH_Leather", n=4, up=(1, 0, 0)))
        if k == 0:
            parts += A.skull_charm(bot + (0, 0, -0.025), 0.024, "BH_Bone", "BH_Shadow",
                                   face=(math.cos(r), math.sin(r), 0), n=6, jaw=False)
        else:
            parts.append(A.tube([bot, bot + (0, 0, -0.05)], 0.006, "BH_Bone", n=5))
            parts.append(A.ball(bot + (0, 0, -0.052), 0.009, "BH_Bone", n=5, rings=3))
    for p in parts:
        p.V = p.V * s
    return parts
