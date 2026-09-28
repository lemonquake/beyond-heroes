"""Brinecaller (bh-012, Builder A; Saltmouth Deeps caster): a gaunt drowned priestess. Tattered sea-green layered robes
(a long under-robe and a darker mantle) fraying at the hem into long kelp-like ribbons, bell sleeves with tatters,
long wet dark hair threaded with kelp, a crown of branching bleached coral spines tipped with teal polyps, pale
blue-grey skin, hollow cheeks and teal glowing eyes, strings of shells and pearls across the chest and at the belt.
Staff: a bleached, twisted driftwood shaft topped by a spiral conch cradling a glowing teal pearl (rigid on weapon.R).
Left hand open, long fingers. ~1.85 m (the coral crown rises ~0.15 m above the head).
Kit: enemy_bandit_cutthroat / enemy_ashen_cultist robe helpers / kit_a_common / kit_deeps."""
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
import kit_deeps as D

SCALE = 1.85 / 1.83
PROPS = proportions(SCALE, shoulder_x=0.168 * SCALE, hip_x=0.09 * SCALE, upper_len=0.29 * SCALE,
                    fore_len=0.275 * SCALE, hand_len=0.105 * SCALE)
PALETTE = "brinecaller"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.1, 0.21, 0.18), 0.0, 0.8, None, 0.0, 1.0),      # sea-green robe
    "BH_Cloth_Secondary": ((0.035, 0.085, 0.08), 0.0, 0.85, None, 0.0, 1.0), # deep green mantle
    "BH_Fur": ((0.06, 0.16, 0.08), 0.0, 0.55, None, 0.0, 1.0),               # kelp ribbons
    "BH_Skin": ((0.5, 0.58, 0.62), 0.0, 0.45, None, 0.0, 1.0),               # pale blue-grey
    "BH_Hair": ((0.02, 0.03, 0.035), 0.0, 0.35, None, 0.0, 1.0),             # wet black hair
    "BH_Horn": ((0.68, 0.55, 0.5), 0.0, 0.8, None, 0.0, 1.0),                # bleached coral
    "BH_Bone": ((0.78, 0.76, 0.68), 0.0, 0.6, None, 0.0, 1.0),               # shells
    "BH_Gold": ((0.86, 0.87, 0.84), 0.35, 0.18, None, 0.0, 1.0),             # pearls
    "BH_Wood": ((0.4, 0.38, 0.34), 0.0, 0.85, None, 0.0, 1.0),               # bleached driftwood
    "BH_Leather": ((0.12, 0.11, 0.09), 0.0, 0.85, None, 0.0, 1.0),           # cords
    "BH_Shadow": ((0.01, 0.02, 0.025), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": D.TEAL,                                                   # eyes, polyps, pearl
}
CLIPS = ["staff_1", "cast_quick", "cast_heavy", "cast_area", "cast_weapon"]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


TORSO = [(r[0], r[1] * 0.86, r[2] * 0.82, r[3] * 0.9, r[4] * 0.5) for r in K.TORSO]
G = 0.012
# gaunt head: hollow cheeks, narrow jaw (z, rx, ryf, ryb, keel, cy) — eye rows kept at the kit depth
HEAD = [(z, rx * (0.84 if 1.6 < z < 1.67 else 0.94), ryf * (0.9 if z < 1.66 else 1.0), ryb * 0.96, k, cy)
        for (z, rx, ryf, ryb, k, cy) in K.HEAD]
HAIR_W = K.zspec_w([(1.5, "chest"), (1.58, "neck"), (1.64, "head")])


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="body"), weights=C.ROBE_W)
    C.robe_top(sb, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", g=G, rows=TORSO, v_open=0.035)
    C.robe_skirt(sb, "BH_Cloth_Primary", trim=None, z_top=1.07, z_bot=0.1, flare=0.14, folds=0.016, ragged=0.08,
                 g=G - 0.02)
    mantle(sb)
    hem_ribbons(sb)
    necklaces(sb)
    head(sb)
    for s in ("L", "R"):
        C.bell_sleeve(sb, s, "BH_Cloth_Secondary", trim="BH_Cloth_Primary", cuff_r=0.08, end=0.74)
        sleeve_ribbons(sb, s)
    K.add_fist(sb, "R", "BH_Skin", "BH_Skin", scale=0.92)
    for prt in A.bony_fingers(sb.b, "R", "BH_Skin", length=0.055 * SCALE, r=0.0065 * SCALE, curl=0.6, s=1.0):
        sb.add_real(prt, "hand.R")
    for prt in A.open_palm(sb.b, "L", "BH_Skin", s=SCALE * 0.92):
        sb.add_real(prt, "hand.L")
    for prt in A.bony_fingers(sb.b, "L", "BH_Skin", length=0.12 * SCALE, r=0.0065 * SCALE, curl=0.7, spread=1.05,
                              nails="BH_Shadow", open_hand=True):
        sb.add_real(prt, "hand.L")
    feet(sb)
    K.add_weapon(sb, "R", conch_staff())


# ================================================================================================= robes
def mantle(sb):
    """Darker mantle: front panels split at the centre down to the thighs, a tattered back drape to the calves."""
    for sx, seed in ((1, 0.4), (-1, 1.9)):
        side = "L" if sx > 0 else "R"

        def fn(u, v, sx=sx, seed=seed):
            zb = 0.62 + HS.ragged(u, seed, 0.14, 3)
            z = 1.47 + (zb - 1.47) * v
            x = sx * (0.02 + 2 * (0.08 + 0.04 * max(0.0, 1.05 - z)) * u)
            y = (front_y(TORSO, x, z) if z >= 1.05 else front_y(TORSO, x, 1.05) - 0.08 * (1.05 - z)) - G - 0.014
            return (x, y, z)
        V, F = M.grid(fn, 6, 10)
        p = M.Part(V, F, "BH_Cloth_Secondary", name="mantle")
        if sx < 0:
            p.flip()
        sb.add(M.solidify(p, 0.008, offset=1.0), weights=HS.cloth_w(belt_z=1.05, leg=0.55))

    def fn(u, v):
        zb = 0.28 + HS.ragged(u, 3.3, 0.2, 5)
        z = 1.49 + (zb - 1.49) * v
        x = (u - 0.5) * 2 * (0.15 + 0.1 * v)
        y = (back_y(TORSO, x * 0.95, z) if z > 1.2 else back_y(TORSO, x * 0.95, 1.2) + 0.06 * (1.2 - z)) + G + 0.02
        return (x, y + 0.01 * math.sin(u * math.pi * 5) * v, z)
    V, F = M.grid(fn, 9, 12)
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Secondary", name="drape").flip(), 0.009, offset=1.0),
           weights=HS.cloth_w(chest_z=1.34, belt_z=1.05, leg=0.32))


def hem_ribbons(sb):
    """Long kelp-like ribbons fraying off the robe hem all round (front ones shorter so the legs stay clear)."""
    rng = np.random.default_rng(5)
    rows = [(0.1 + 0.03, 0.15 + G + 0.12, 0.098 + G + 0.12, 0.1 + G + 0.13, 0.0)]
    for k in range(16):
        f = (k + 0.5) / 16
        front = math.cos(2 * math.pi * f)          # 1 at the front
        z = 0.22 + 0.04 * rng.random()
        q = K.ring_frac([(z, 0.15 + G + 0.12, 0.098 + G + 0.12, 0.1 + G + 0.135, 0.0),
                         (z + 0.1, 0.15 + G + 0.11, 0.098 + G + 0.11, 0.1 + G + 0.12, 0.0)], z, -0.01, [f], p=2.2)[0]
        out = normalize(np.array([q[0], q[1], 0.0]))
        ln = 0.14 + 0.1 * rng.random() - 0.05 * max(front, 0)
        side = "L" if q[0] > 0 else "R"
        back = q[1] > 0
        w = C.robe_panel_w(sb, side, back)
        for prt in D.kelp(q, out * 0.25 + np.array([0, 0, -1.0]), ln, 0.035, "BH_Fur" if k % 3 else
                          "BH_Cloth_Primary", out=out, amp=0.02, seed=k * 1.3):
            sb.add(prt, weights=w)


def sleeve_ribbons(sb, s):
    el, wr = sb.head("forearm." + s), sb.head("hand." + s)
    d = normalize(wr - el)
    c = el + (wr - el) * 0.72
    side = normalize(np.cross(d, (0, 1, 0)))
    fw = np.cross(side, d)
    for k, ang in enumerate((200, 260, 320)):
        a = math.radians(ang)
        nrm = side * math.cos(a) + fw * math.sin(a)
        for prt in D.kelp(c + nrm * 0.076, d * 0.5 + np.array([0, 0, -1.0]), 0.14 + 0.04 * (k % 2), 0.03, "BH_Fur",
                          out=nrm, amp=0.012, seed=k * 2.1):
            sb.add(prt, "forearm." + s)


def necklaces(sb):
    """Two drooping strings of shells and pearls across the chest + a shell girdle at the waist."""
    for k, (dz, n) in enumerate(((0.1, 11), (0.19, 13))):
        pts = []
        for t in np.linspace(0, 1, n):
            x = (t - 0.5) * 2 * (0.11 + 0.02 * k)
            z = 1.5 - dz * (1 - (2 * t - 1) ** 2) - 0.02
            pts.append((x, front_y(TORSO, x, z) - G - 0.02, z))
        for prt in D.bead_string(pts, 0.011, ["BH_Gold", "BH_Bone"], cord="BH_Leather"):
            sb.add(prt, "chest")
    # pendant: a scallop shell with a teal bead
    z = 1.5 - 0.19 - 0.035
    c = np.array([0, front_y(TORSO, 0, z) - G - 0.028, z])
    V, F = M.lathe([(0, 0), (0.03, 0.004), (0.032, 0.012), (0.0, 0.016)], 9, a0=-80, a1=80, cap=False)
    sb.add(M.solidify(M.Part(V, F, "BH_Bone", name="scallop").rot(Rx(90)).rot(Rz(-90)).move(c + (0, 0, -0.012)), 0.004),
           "chest")
    sb.add(A.ball(c + (0, -0.01, 0.0), 0.012, "BH_Emissive", n=6, rings=4), "chest")
    # girdle of shells + a knotted cord
    C.rope_belt(sb, z=1.03, g=G + 0.012, mat="BH_Leather", knot_frac=0.1, tails=0.3, rows=TORSO)
    for k in range(9):
        f = 0.62 + 0.76 * k / 8
        p, ang = K.on_ring(TORSO, 1.01, G + 0.03, f % 1.0)
        out = normalize(np.array([p[0], p[1], 0.0]))
        for prt in D.cone_shell(p + (0, 0, -0.01), out * 0.3 + np.array([0, 0, -1.0]), 0.012, 0.045,
                                "BH_Bone" if k % 2 else "BH_Gold"):
            sb.add(prt, weights=sb.skirt(1.05, 0.8, max_leg=0.3, center_w=0.05))


# ================================================================================================= head
def head(sb):
    K.neck_and_head(sb, skin="BH_Skin", head_rows=HEAD, eyes="BH_Shadow", eye_glow=None, nose=True)
    for sx in (1, -1):
        sb.add(A.ball((sx * 0.029, -0.078, 1.699), 0.0105, "BH_Emissive", n=6, rings=4, scale=(1.25, 0.6, 0.8)),
               "head")
        # hollow cheeks: dark hollows under the cheekbones
        sb.add(A.ball((sx * 0.05, -0.05, 1.64), 0.016, "BH_Shadow", n=6, rings=4, scale=(0.6, 0.35, 1.2)), "head")
        sb.add(A.tube([(sx * 0.03, -0.075, 1.678), (sx * 0.06, -0.06, 1.68), (sx * 0.072, -0.03, 1.69)], 0.006,
                      "BH_Skin", n=5), "head")
    sb.add(A.tube([(-0.018, -0.07, 1.613), (0.018, -0.07, 1.613)], 0.004, "BH_Shadow", n=4), "head")
    # long wet hair: cap + heavy strands down the back and over the shoulders, kelp threaded through
    K.hair_cap(sb, mat="BH_Hair", g=0.009, z_front=1.745, z_back=1.6, messy=0.004)
    rng = np.random.default_rng(12)
    for k in range(13):
        a = math.radians(-115 + 230 * k / 12)
        top = np.array([0.078 * math.sin(a), 0.01 + 0.085 * math.cos(a), 1.74])
        back = math.cos(a)
        ln = 0.42 + 0.12 * rng.random() if back > -0.2 else 0.2
        lower = np.array([0.1 * math.sin(a) * 1.2, 0.1 + 0.05 * max(back, 0), 1.74 - ln])
        pts = [top, top + np.array([0.02 * math.sin(a), 0.02, -0.08]),
               (top + lower) / 2 + np.array([0.04 * math.sin(a), 0.05 * max(back, 0.2), 0.0]), lower]
        sb.add(A.taper(pts, 0.018, 0.005, "BH_Hair", n=5), weights=HAIR_W)
        if k % 4 == 1:
            for prt in D.kelp(pts[2], (0.0, 0.2, -1.0), 0.18, 0.024, "BH_Fur", out=(math.sin(a), math.cos(a), 0),
                              amp=0.01, seed=k):
                sb.add(prt, weights=HAIR_W)
    coral_crown(sb)


def coral_crown(sb):
    """Band round the brow with branching coral spines rising up and out (tallest at the back / temples)."""
    zc = 1.765
    ring = [np.array([0.086 * math.cos(a), 0.004 + 0.098 * math.sin(a), zc - 0.014 * math.sin(a)])
            for a in np.linspace(0, 2 * math.pi, 17)]
    sb.add(A.tube(ring, 0.009, "BH_Horn", n=5, up=(0, 0, 1), cap=False), "head")
    for k in range(9):
        a = math.radians(-90 + (k - 4) * 38)            # centred on the front... spread all round
        base = np.array([0.086 * math.cos(a), 0.004 + 0.098 * math.sin(a), zc - 0.014 * math.sin(a)])
        outd = normalize(np.array([math.cos(a), math.sin(a), 0.0]))
        front = -math.sin(a)
        ln = 0.08 + 0.05 * (1 - max(front, 0)) + 0.02 * (k % 2)
        for prt in D.coral(base, outd * 0.45 + np.array([0, 0, 1.0]), ln, 0.011, "BH_Horn", seed=40 + k,
                           depth=2 if k % 2 == 0 else 1, spread=30, n=5, tip="BH_Emissive"):
            sb.add(prt, "head")


def feet(sb):
    for s in ("L", "R"):
        hx = sb.head("thigh." + s)[0]
        V, F = M.tube([(hx, 0.045, 0.07), (hx, 0.0, 0.04), (hx, -0.14, 0.022), (hx, -0.19, 0.014)],
                      [(0.036, 0.04), (0.04, 0.032), (0.036, 0.018), (0.02, 0.01)], n=10, up=(0, 0, 1))
        sb.add(M.Part(V, F, "BH_Skin", name="foot"), weights=lambda V, s=s: [
            {"foot." + s: 1.0} if v[1] > -0.1 else {"toe." + s: 1.0} for v in V])


# ================================================================================================= staff
def conch_staff():
    """Weapon space: bleached twisted driftwood (~1.75 m) topped by a spiral conch cradling a glowing teal pearl."""
    parts = []
    pts, prof = [], []
    for i in range(16):
        u = i / 15
        z = -1.05 + 1.62 * u
        pts.append((0.016 * math.sin(u * 8.0) + 0.006 * math.sin(u * 21), 0.012 * math.cos(u * 6.0), z))
        r = 0.02 + 0.004 * math.sin(u * 17) + 0.01 * max(0.0, u - 0.85) / 0.15
        prof.append((r, r * 0.9))
    V, F = M.tube(pts, prof, n=8, up=(0, -1, 0))
    parts.append(M.Part(V, F, "BH_Wood", name="shaft"))
    # gnarls
    for z, a in ((-0.6, 30), (-0.2, 150), (0.25, 260)):
        d = np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), 0.4])
        parts.append(A.taper([(0, 0, z), np.array([0, 0, z]) + d * 0.06], 0.014, 0.004, "BH_Wood", n=5))
    V, F = M.lathe([(0, -0.1), (0.024, -0.1), (0.025, 0.0), (0.024, 0.1), (0, 0.1)], 8)
    parts.append(M.Part(V, F, "BH_Leather", name="grip"))
    # driftwood fingers splaying out to cradle the conch
    top = np.array([pts[-1][0], pts[-1][1], 0.57])
    for k in range(4):
        a = math.radians(90 * k + 20)
        d = np.array([math.cos(a), math.sin(a), 0.0])
        parts.append(A.taper([top, top + d * 0.05 + (0, 0, 0.05), top + d * 0.075 + (0, 0, 0.14)], 0.013, 0.004,
                             "BH_Wood", n=5))
    # conch: a big spiral, apex up, aperture facing -Y (the staff's front) with the pearl inside
    c0 = top + np.array([0, 0, 0.06])
    spts, sprof = [], []
    for i in range(18):
        t = i / 17
        a = 2 * math.pi * 2.3 * t
        rad = 0.055 * (1 - t) ** 1.1
        spts.append(c0 + np.array([rad * math.cos(a), rad * math.sin(a), 0.2 * t]))
        rr = 0.05 * (1 - t) ** 1.2 + 0.003
        sprof.append((rr, rr))
    V, F = M.tube(spts, sprof, n=8, up=(0, 0, 1))
    parts.append(M.Part(V, F, "BH_Bone", name="conch"))
    for i in range(0, 16, 3):          # knobs on the whorls
        q = np.asarray(spts[i])
        parts.append(A.taper([q, q + (q - c0) * np.array([0.6, 0.6, 0.0]) + (0, 0, 0.03)], 0.01, 0.002, "BH_Horn",
                             n=4))
    # flared lip + the glowing pearl in the aperture, a faint halo
    V, F = M.lathe([(0.0, 0.0), (0.06, 0.0), (0.075, 0.02), (0.065, 0.05)], 10, a0=200, a1=340, cap=False)
    parts.append(M.solidify(M.Part(V, F, "BH_Horn", name="lip").move(c0 + (0, 0.0, -0.02)), 0.006))
    parts.append(A.ball(c0 + (0, -0.065, 0.03), 0.044, "BH_Emissive", n=10, rings=6))
    V, F = M.lathe([(0.06, -0.004), (0.066, 0.0), (0.06, 0.004), (0.056, 0.0)], 16, cap=False)
    parts.append(M.Part(V, F, "BH_Emissive", name="halo").rot(Rx(90)).move(c0 + (0, -0.075, 0.03)))
    # shell charms and a kelp tatter under the head
    for k, (a, ln) in enumerate(((40, 0.13), (170, 0.1), (290, 0.16))):
        r = math.radians(a)
        t0 = top + np.array([0.03 * math.cos(r), 0.03 * math.sin(r), -0.02])
        b = t0 + np.array([0.0, 0.0, -ln])
        parts.append(A.tube([t0, b], 0.003, "BH_Leather", n=4, up=(1, 0, 0)))
        if k == 1:
            parts += D.kelp(t0, (0, 0, -1), 0.2, 0.026, "BH_Fur", out=(math.cos(r), math.sin(r), 0), amp=0.01)
        else:
            parts += D.cone_shell(b, (0, 0, -1), 0.014, 0.05, "BH_Bone")
            parts.append(A.ball(b + (0, 0, 0.008), 0.011, "BH_Gold", n=6, rings=4))
    return parts
