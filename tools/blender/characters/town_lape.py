"""Townsfolk: Lape the Ancient, relic appraiser of Malasugue (bh-019, work/lemondev/bh-019/contracts/art.md section 4).

A very tall, slightly stooped old figure (~1.9 m) in a floor-length near-black robe (BH_Cloth_Primary, tinted almost
black by the game) whose charcoal hem is worn ragged, a short cowl-cape and a deep pointed hood that droops back.
The face stays in the hood's shadow: only two faint pale eyes and a long white beard spilling out over the chest.
Long wide sleeves leave only bony fingers showing. A hemp rope belt with two pouches and knotted ends, an old key on
a cord below the beard. In the right hand an enormous gnarled staff (2.6 m, 0.7 m taller than him): two twisted
dead-wood strands grown together, the head a tangle of roots cradling a glowing violet orb, with bone and brass charms
and a tattered ribbon hanging under it. The staff is rigid to hand.R (weapon.R is non-deforming), so it stays in the
hand through every clip.
"""
import math
import numpy as np

import bh_mesh as M
from bh_body import front_y, back_y, torso_loft, interp_rows, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import town_matron as K
from town_matron import Kit, P_, pal, rope, lerp
from town_elder import shawl_surface, shawl_w
from char_mage import ring_frac

PROPS = proportions(1.04, shoulder_x=0.18 * 1.04, hip_x=0.098 * 1.04)
PALETTE = "town_lape"
TINTABLE = ("BH_Cloth_Primary",)
CLIPS_ONLY = list(K.TOWN_CLIPS)
PALETTE_COLORS = dict(K.BASE_COLORS)
PALETTE_COLORS.update({
    "BH_Cloth_Primary": pal((0.05, 0.045, 0.055), 0.95),      # preview: the game tints it (0.06, 0.05, 0.07)
    "BH_Cloth_Secondary": pal((0.062, 0.06, 0.063), 0.95),   # charcoal hem, cuffs, cowl edge
    "BH_Cloth_Accent": pal((0.20, 0.035, 0.03), 0.9),         # the staff's faded crimson ribbon
    "BH_Skin": pal((0.40, 0.35, 0.31), 0.6),                  # old, bloodless fingers
    "BH_Hair": pal((0.80, 0.79, 0.75), 0.75),                 # white beard
    "BH_Wood": pal((0.075, 0.052, 0.036), 0.8),               # dead dark wood of the staff
    "BH_Rope": pal((0.36, 0.28, 0.17), 0.95),                 # hemp belt
    "BH_Bronze": pal((0.42, 0.27, 0.11), 0.45, 1.0),          # the old key, charm caps
    "BH_Bone": pal((0.66, 0.60, 0.48), 0.7),                  # charms
    "BH_Gold": pal((0.60, 0.44, 0.18), 0.4, 1.0),
    "BH_Shadow": ((0.008, 0.007, 0.01), 0.0, 0.95, None, 0.0, 1.0),          # the hood's darkness (no glow)
    "BH_Aether": ((0.78, 0.82, 0.9), 0.0, 0.5, (0.72, 0.8, 1.0), 1.4, 1.0),  # two faint pale eyes
    "BH_Emissive": ((0.55, 0.28, 0.95), 0.0, 0.35, (0.66, 0.34, 1.0), 6.0, 1.0),  # the staff orb
})

L_TORSO = K.torso_rows(chest=0.95, waist=0.98, hip=1.0, depth=1.0, hump=0.034, shoulder=0.94)
FWD = -0.032          # head carried forward (stoop)
STAFF_LEN = 2.6


def build(body):
    k = Kit(body)
    rows = L_TORSO
    # ---- robe: bodice + floor-length skirt, a ragged charcoal hem
    K.body_shell(k, rows, 0.98, 1.53, "BH_Cloth_Primary", n=24, cap1=True, name="robe_top")
    sk_rows = K.flare_rows(1.07, 0.1, (0.152, 0.104, 0.116), (0.25, 0.23, 0.27), n=8, curve=0.9)
    sk, _ = K.skirt(sk_rows, "BH_Cloth_Primary", folds=8, amp=0.012)
    k.add(sk, w=k.skirt_w(1.02, 0.5, max_leg=0.8, center_w=0.08))
    hem(k, sk_rows)
    # front seam trim down the robe (charcoal), so the silhouette is not one flat black mass
    pts = [(0, front_y(rows, 0, z) - 0.004, z) for z in np.linspace(1.5, 1.08, 5)]
    pts += [(0, front_y(sk_rows, 0, z, p=2.2) - 0.006, z) for z in np.linspace(1.0, 0.2, 6)]
    V, F = M.tube(pts, [(0.012, 0.004)] * len(pts), n=6, up=(0, -1, 0), p=3.0)
    k.add(P_(V, F, "BH_Cloth_Secondary", "seam"),
          w=lambda V: [a if v[2] > 1.04 * k.s else b for v, a, b in
                       zip(V, k.torso_w()(V), k.skirt_w(1.02, 0.5, max_leg=0.8, center_w=0.08)(V))])
    # ---- long wide sleeves reaching over the hands; thin bony wrists and fingers
    for s in "LR":
        K.sleeve(k, s, K.SHOULDER_CAP + [(0.5, 0.058, 0.06), (1.0, 0.064, 0.066), (1.5, 0.084, 0.084),
                                         (1.95, 0.1, 0.1), (2.2, 0.104, 0.1)], "BH_Cloth_Primary", n=14,
                 solid=0.006, cap1=False)
        K.arm_ring(k, s, 1.97, 0.104, 0.03, "BH_Cloth_Secondary", name="cuff")
        K.sleeve(k, s, [(1.4, 0.032, 0.032), (2.0, 0.026, 0.024)], "BH_Skin", n=8, name="wrist")
        K.mitten(k, s, size=0.9, curl=2.4 if s == "R" else 1.4)
    for s in "LR":
        K.leg_tube(k, s, [(0.15, 0.065, 0.065), (1.0, 0.045, 0.047), (1.9, 0.036, 0.038)], "BH_Cloth_Secondary", n=8)
    K.shoes(k, "BH_Leather", sole="BH_Wood", width=0.9)
    # ---- cowl-cape over the shoulders, rope belt with pouches, the key on its cord
    cowl(k)
    belt(k, rows)
    key_pendant(k, rows)
    # ---- head in shadow, faint eyes, beard, deep pointed hood
    head_shadowed(k)
    beard(k, rows)
    hood(k)
    staff(k)
    K.check_normals(body, "lape")


# ---------------------------------------------------------------------------------------------------------------- robe
def hem(k, sk_rows):
    """Charcoal hem band hanging over the robe's bottom, its lower edge torn into uneven tongues."""
    n = 40
    fr = np.linspace(0, 1, n, endpoint=False)
    rings = []
    rng = np.random.default_rng(1731)
    jag = np.abs(np.sin(fr * 2 * math.pi * 7 + 0.4)) ** 0.6 * 0.045 + rng.uniform(0.0, 0.03, n)
    for z, g in ((0.2, 0.004), (0.14, 0.008), (0.09, 0.012)):
        rings.append(ring_frac(sk_rows, z, g, fr, p=2.2))
    bot = ring_frac(sk_rows, 0.1, 0.016, fr, p=2.2)
    bot[:, 2] = 0.012 + jag
    # the torn bottom flares out a little
    rad = bot[:, :2] / np.linalg.norm(bot[:, :2], axis=1)[:, None]
    bot[:, :2] += rad * 0.012
    rings.append(bot)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=True)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Secondary", "hem"), 0.007, offset=-1.0),
          w=k.skirt_w(1.02, 0.5, max_leg=0.8, center_w=0.08))


def cowl(k):
    """Short cape falling from the hood over the shoulders, dropping to a point at the back; ragged edge."""
    rings = shawl_surface(40, 6, math.radians(14), (0.1, 0.085, 0.09), (0.25, 0.19, 0.22), 0.2, 0.2, 0.34, 1.575)
    # tear the lower edge: pull some hem vertices up
    bot = rings[0]
    for i in range(len(bot)):
        bot[i][2] += 0.025 * abs(math.sin(i * 1.7)) + (0.02 if i % 5 == 2 else 0.0)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Primary", "cowl"), 0.01, offset=1.0), w=shawl_w(k))
    V, F = M.tube(rings[0], [(0.006, 0.006)] * len(rings[0]), n=5, up=(0, 0, 1))
    k.add(P_(V, F, "BH_Cloth_Secondary", "cowl_hem"), w=shawl_w(k))


def belt(k, rows):
    K.band(k, rows, 1.05, 1.085, "BH_Rope", g_out=0.016, g_in=0.004, n=24, bev=0.0)
    # a second loose turn, sagging to the right hip
    pts = []
    for fr in np.linspace(0.62, 1.12, 13):
        z = 1.045 - 0.035 * math.sin(math.pi * (fr - 0.62) / 0.5)
        pts.append(ring_frac(rows, z, 0.024, [fr % 1.0])[0])
    k.add(rope(pts, 0.008, "BH_Rope", cap=False), "hips")
    # knot at the front-left and two knotted, frayed ends
    q, ang = K.on_ring(rows, 1.065, 0.03, 0.08)
    q = np.asarray(q)
    V, F = M.sphere(0.022, 8, 6, center=q, scale=(1.2, 0.8, 1.0))
    k.add(P_(V, F, "BH_Rope", "knot"), "hips")
    for dx, L in ((0.0, 0.3), (0.03, 0.22)):
        e = [q + (dx * 0.3, -0.004, -0.01), q + (dx, -0.012, -L * 0.5), q + (dx * 1.2, -0.02, -L)]
        k.add(rope(e, 0.008, "BH_Rope"), w=k.skirt_w(1.05, 0.7, max_leg=0.5))
        V, F = M.sphere(0.013, 6, 4, center=e[-1] + (0, 0, 0.01), scale=(1, 1, 1.3))
        k.add(P_(V, F, "BH_Rope", "end_knot"), w=k.skirt_w(1.05, 0.7, max_leg=0.5))
    # two small pouches (left hip, right back)
    for frac, size in ((0.23, (0.07, 0.035, 0.08)), (0.66, (0.06, 0.03, 0.065))):
        q, ang = K.on_ring(rows, 1.0, 0.03, frac)
        for prt in K.pouch(q, ang, size):
            k.add(prt, "hips")


def key_pendant(k, rows):
    """Cord round the neck (under the beard) and a big old key hanging below the beard's tip."""
    zk = 1.2
    pts = []
    for sx in (1, -1):
        side = []
        for t in np.linspace(0, 1, 6):
            x = sx * lerp(0.075, 0.01, t)
            z = lerp(1.49, zk + 0.06, t)
            side.append((x, front_y(L_TORSO, x, z) - 0.03, z))
        pts.append(side)
    k.add(rope(pts[0], 0.003, "BH_Leather"), "chest")
    k.add(rope(pts[1], 0.003, "BH_Leather"), "chest")
    y = front_y(L_TORSO, 0, zk) - 0.032
    c = np.array([0, y, zk + 0.04])
    ring = K.ring_pts(c, 0.018, (0, -1, 0), n=12)
    V, F = M.tube(ring, [(0.0045, 0.0045)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
    k.add(P_(V, F, "BH_Bronze", "key_bow"), "chest")
    k.add(rope([c + (0, 0, -0.018), c + (0, 0, -0.11)], 0.0045, "BH_Bronze"), "chest")
    for dz, w in ((-0.1, 0.022), (-0.08, 0.016)):
        V, F = M.box(w, 0.005, 0.012, center=(w / 2, 0, 0))
        k.add(P_(V, F, "BH_Bronze", "key_bit").move(c + (0.002, 0, dz)), "chest")


# ---------------------------------------------------------------------------------------------------------------- head
def head_shadowed(k):
    """The head exists only as a dark shape inside the hood: shadow skin, a hint of nose, two faint pale eyes."""
    hr = K.head_rows(jaw=0.95, width=0.93, fwd=FWD)
    V, F = M.tube([(0, 0.0, 1.47), (0, -0.004 + FWD * 0.5, 1.54), (0, -0.01 + FWD, 1.62)],
                  [(0.05, 0.046), (0.046, 0.044), (0.046, 0.046)], n=12, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Shadow", "neck"), w=k.head_w())
    V, F = torso_loft(hr, n=20, p=2.1, cap0=True, cap1=True)
    k.add(P_(V, F, "BH_Shadow", "head"), "head")
    V, F = M.tube([(0, -0.076 + FWD, 1.712), (0, -0.09 + FWD, 1.684), (0, -0.098 + FWD, 1.66), (0, -0.088 + FWD, 1.648)],
                  [(0.0065, 0.006), (0.009, 0.008), (0.011, 0.009), (0.007, 0.005)], n=6, up=(0, -1, 0))
    k.add(P_(V, F, "BH_Shadow", "nose"), "head")
    for sx in (1, -1):
        V, F = M.sphere(0.0058, 6, 4, center=(sx * 0.028, -0.073 + FWD, 1.702), scale=(1.4, 0.6, 0.7))
        k.add(P_(V, F, "BH_Aether", "eye"), "head")
    return hr


def beard(k, rows):
    """Long white beard from under the nose, spilling out of the hood and down the chest to a ragged point."""
    spec = [  # z, half width, half depth
        (1.665, 0.05, 0.02), (1.63, 0.066, 0.032), (1.59, 0.072, 0.036), (1.54, 0.07, 0.034),
        (1.48, 0.062, 0.03), (1.41, 0.05, 0.026), (1.34, 0.036, 0.02), (1.29, 0.022, 0.014), (1.255, 0.008, 0.006)]
    rings = []
    for i, (z, hw, hd) in enumerate(spec):
        if z > 1.56:
            yc = -0.066 + FWD - hd * 0.4
        else:
            yc = front_y(rows, 0, z) - 0.018 - hd
            yc = min(yc, -0.07 + FWD * (z - 1.3) / 0.3)
        ring = []
        for j in range(14):
            a = 2 * math.pi * j / 14
            lobe = 1.0 + 0.1 * math.cos(a * 4 + i * 0.9)  # strands
            ring.append((hw * math.sin(a) * lobe, yc - hd * math.cos(a) * lobe, z - 0.008 * math.cos(a * 2)))
        rings.append(np.array(ring))
    V, F = M.loft(rings, cap0=True, cap1=True)
    k.add(K.outward(P_(V, F, "BH_Hair", "beard")), w=k.zw([(1.38, "chest"), (1.5, "neck"), (1.6, "head")]))
    # drooping moustache wings
    for sx in (1, -1):
        pts = [(sx * 0.008, -0.092 + FWD, 1.648), (sx * 0.035, -0.086 + FWD, 1.636), (sx * 0.05, -0.078 + FWD, 1.585),
               (sx * 0.055, -0.08 + FWD, 1.54)]
        V, F = M.tube(pts, [(0.009, 0.007), (0.01, 0.008), (0.008, 0.007), (0.004, 0.004)], n=6, up=(0, -1, 0))
        k.add(P_(V, F, "BH_Hair", "moustache"), w=k.zw([(1.5, "neck"), (1.6, "head")]))


# z, rx, ry_front, ry_back, cy, opening half-angle (deg): a deep cowl whose rim stands well in front of the face,
# closing over the brow, then a long point that droops backward
HOOD = [
    (1.49, 0.16, 0.14, 0.15, 0.02, 34),
    (1.55, 0.135, 0.15, 0.14, 0.0, 40),
    (1.62, 0.122, 0.165, 0.138, -0.012, 40),
    (1.69, 0.122, 0.17, 0.14, -0.014, 38),
    (1.75, 0.118, 0.168, 0.14, -0.01, 32),
    (1.80, 0.105, 0.15, 0.132, 0.0, 22),
    (1.845, 0.082, 0.11, 0.118, 0.02, 8),
    (1.88, 0.056, 0.07, 0.096, 0.05, 2),
    (1.905, 0.036, 0.04, 0.07, 0.09, 1),
    (1.915, 0.02, 0.02, 0.045, 0.14, 1),
    (1.905, 0.009, 0.008, 0.02, 0.2, 1),
    (1.88, 0.002, 0.002, 0.004, 0.245, 1),
]


def hood(k):
    nu = 26
    rings = []
    for (z, rx, ryf, ryb, cy, th) in HOOD:
        ring = []
        cyy = cy + FWD * float(smoothstep(1.5, 1.62, z))
        for u in np.linspace(0, 1, nu):
            a = math.radians(th + (360 - 2 * th) * u)
            sa, ca = math.sin(a), math.cos(a)
            ring.append((rx * sa, cyy - (ryf if ca > 0 else ryb) * ca, z))
        rings.append(np.array(ring))
    wf = k.zw([(1.49, "chest"), (1.54, "neck"), (1.57, "neck"), (1.62, "head")])
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    k.add(M.solidify(P_(V, F, "BH_Cloth_Primary", "hood"), 0.012, offset=-1.0), w=wf)
    # the rim: a worn, thicker charcoal edge
    edge = [r[0] for r in rings[:8]] + [r[-1] for r in rings[:8][::-1]]
    V, F = M.tube(edge, [(0.008, 0.008)] * len(edge), n=6, up=(0, 0, 1))
    k.add(P_(V, F, "BH_Cloth_Secondary", "hood_rim"), w=wf)
    # the darkness inside the cowl
    inner = []
    for (z, rx, ryf, ryb, cy, th) in HOOD[1:7]:
        ring = []
        cyy = cy + FWD * float(smoothstep(1.5, 1.62, z))
        for u in np.linspace(0, 1, nu):
            a = math.radians(th + (360 - 2 * th) * u)
            ring.append((rx * 0.9 * math.sin(a), cyy - (ryf if math.cos(a) > 0 else ryb) * 0.9 * math.cos(a), z))
        inner.append(np.array(ring))
    V, F = M.loft(inner, cap0=False, cap1=False, closed=False)
    k.add(P_(V, F, "BH_Shadow", "hood_lining").flip(), w=wf)


# ---------------------------------------------------------------------------------------------------------------- staff
def staff(k):
    """Enormous gnarled staff, rigid to hand.R: foot planted a little inside the right foot, shaft through the fist,
    head of tangled roots around a glowing violet orb 2.6 m above the ground."""
    b = k.b
    g = np.asarray(b.head("weapon.R"), float)
    foot = np.array([g[0] + 0.035, g[1] + 0.03, 0.0])
    d = normalize(g - foot)
    top = foot + d * STAFF_LEN
    side = normalize(np.cross(d, (0, 0, 1)))
    up2 = np.cross(side, d)
    parts = []

    def at(t, r_off=0.0, ang=0.0):
        return foot + d * (STAFF_LEN * t) + (side * math.cos(ang) + up2 * math.sin(ang)) * r_off

    # two strands twisting round each other (fused below, parting and knotting higher up)
    for s_i, ph in enumerate((0.0, math.pi)):
        pts, prof = [], []
        for i in range(34):
            t = i / 33 * 0.9
            sep = 0.006 + 0.012 * smoothstep(0.35, 0.85, t)
            ang = ph + t * 16.0
            p = at(t, sep, ang) + side * 0.01 * math.sin(t * 9 + s_i) + up2 * 0.008 * math.cos(t * 7)
            pts.append(p)
            r = 0.019 - 0.004 * t + 0.004 * math.sin(t * 31 + s_i * 2) ** 2
            prof.append((r, r * 0.9))
        V, F = M.tube(pts, prof, n=7, up=tuple(up2))
        parts.append(P_(V, F, "BH_Wood", "strand"))
    # knots / burls along the shaft
    for t, a in ((0.22, 0.6), (0.47, 2.4), (0.63, 4.1), (0.78, 1.2)):
        V, F = M.sphere(0.026, 7, 5, center=at(t, 0.012, a), scale=(1.0, 1.0, 1.5))
        parts.append(K.outward(P_(V, F, "BH_Wood", "burl")))
    # iron-shod foot
    V, F = M.tube([foot + d * 0.0, foot + d * 0.07], [(0.024, 0.024), (0.026, 0.026)], n=8, up=tuple(up2))
    parts.append(P_(V, F, "BH_Bronze", "ferrule"))
    # the head: roots curling up and over the orb from the top of the shaft
    oc = at(0.955)
    orb_r = 0.058
    V, F = M.sphere(orb_r, 12, 8, center=oc)
    parts.append(P_(V, F, "BH_Emissive", "orb"))
    base = at(0.885)
    for i in range(6):
        a0 = i * math.pi / 3 + 0.3
        pts = []
        for j in range(8):
            u = j / 7
            rad = (0.022 + 0.05 * math.sin(math.pi * min(u * 1.1, 1.0))) if u < 0.9 else 0.03
            ang = a0 + u * 1.6 * (1 if i % 2 else -1)
            z_t = 0.885 + 0.12 * u + (0.012 if i % 3 == 0 else 0.0) * u
            p = at(z_t, rad + (orb_r * 0.95 * math.sin(math.pi * u) if 0.3 < u < 0.95 else 0.0) * 0.4, ang)
            pts.append(p)
        prof = [(0.014 * (1 - 0.75 * j / 7) + 0.003,) * 2 for j in range(8)]
        V, F = M.tube(pts, prof, n=5, up=tuple(d))
        parts.append(P_(V, F, "BH_Wood", "root"))
    # a collar where the roots leave the shaft
    V, F = M.tube([at(0.875), at(0.895)], [(0.03, 0.03), (0.034, 0.034)], n=8, up=tuple(up2))
    parts.append(P_(V, F, "BH_Wood", "collar"))
    # hanging charms: bone, brass bead, a small tooth, on cords from the root cage
    for i, (a, L, mat) in enumerate(((0.4, 0.2, "BH_Bone"), (2.2, 0.15, "BH_Bronze"), (4.2, 0.24, "BH_Bone"))):
        hang = at(0.9, 0.05, a)
        low = hang + np.array([0, 0, -L])
        parts.append(rope([hang, low], 0.0025, "BH_Rope"))
        if mat == "BH_Bone":
            V, F = M.tube([low, low + np.array([0.0, 0.0, -0.05])], [(0.008, 0.008), (0.002, 0.002)], n=5)
        else:
            V, F = M.sphere(0.012, 6, 4, center=low + np.array([0, 0, -0.012]))
        parts.append(P_(V, F, mat, "charm"))
    # tattered ribbon tied under the head: two strips, torn ends
    knot = at(0.87, 0.02, 3.3)
    for dx, L in ((0.0, 0.42), (0.03, 0.3)):
        pts = [knot, knot + side * (0.015 + dx) + np.array([0, 0.01, -L * 0.35]),
               knot + side * (0.03 + dx) + np.array([0, 0.02, -L * 0.7]), knot + side * (0.02 + dx) + np.array([0, 0.03, -L])]
        V, F = M.tube(pts, [(0.018, 0.0025), (0.02, 0.0025), (0.017, 0.0025), (0.008, 0.002)], n=4, up=(0, 1, 0), p=3.0)
        parts.append(P_(V, F, "BH_Cloth_Accent", "ribbon"))
    V, F = M.sphere(0.016, 6, 4, center=knot)
    parts.append(P_(V, F, "BH_Cloth_Accent", "ribbon_knot"))
    for prt in parts:
        b.add(prt, "hand.R")
