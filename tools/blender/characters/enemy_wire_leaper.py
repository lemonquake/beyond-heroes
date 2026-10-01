"""Wire Leaper (bh-029, Builder M3, Zarael / the Bridge of Death + Heart Citadel duelist): one of Agdao's old
wire-runners, who climbed the pylons to mend the lines, taken by the Blackwire. A lithe ~1.9 m acrobat in light
leather: a cross-strapped harness over a bare, lean torso, a wide wrapped waist sash, a short red loincloth, dark
leggings with wrapped shins, foot wraps. Wire tattoos (thin inlaid lines of white light in stepped patterns) run down
both arms, across the chest and down the spine; corruption shows in the copper wires that have grown out through the
skin of the shoulders and back (bent, frayed, white at their tips). A narrow obsidian visor across the eyes with two
white slits, a black topknot with a fan of short feathers, jade ear spools. A feather cloak (cape bones) of dark
teal feathers tipped scarlet hangs from a feather mantle to the knees.

Both hands: knapped obsidian blades (weapon.R / weapon.L): long, slightly curved black glass blades with stepped
knapped edges, wire-wound grips with a white-glowing ring at the hilt.

~1.9 m (topknot feathers ~2.0 m). Clips: dual_1 dual_2 dual_heavy leap_slam (+ dagger_1, the enemy base set)."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import char_knight as KN
import enemy_bandit_cutthroat as K
import enemy_hollow_soldier as HS
import kit_a_common as A
import enemy_glyphbound_warrior as Z

SCALE = 1.9 / 1.84
PROPS = proportions(SCALE, shoulder_x=0.182 * SCALE, hip_x=0.094 * SCALE)
EXTRA_BONES = [(n, tuple(np.array(h) * SCALE), tuple(np.array(t) * SCALE), par, z) for (n, h, t, par, z) in KN.CAPE_BONES]
PREVIEW_HEIGHT = 2.35
PALETTE = "wire_leaper"
PALETTE_COLORS = {
    "BH_Skin": ((0.3, 0.19, 0.13), 0.0, 0.55, None, 0.0, 1.0),                  # sun-dark skin
    "BH_Leather": ((0.2, 0.115, 0.06), 0.0, 0.62, None, 0.0, 1.0),             # light leather harness / bracers
    "BH_Cloth_Primary": ((0.33, 0.05, 0.04), 0.0, 0.9, None, 0.0, 1.0),        # red loincloth / sash
    "BH_Cloth_Secondary": ((0.055, 0.05, 0.045), 0.0, 0.92, None, 0.0, 1.0),   # dark leggings / wraps
    "BH_Hair": ((0.025, 0.16, 0.15), 0.0, 0.7, None, 0.0, 1.0),                # dark teal feathers
    "BH_Flesh": ((0.46, 0.06, 0.04), 0.0, 0.7, None, 0.0, 1.0),                # scarlet feather tips
    "BH_Fur": ((0.02, 0.018, 0.02), 0.0, 0.75, None, 0.0, 1.0),                # black hair / cloak backing
    "BH_Horn": ((0.02, 0.02, 0.026), 0.35, 0.08, None, 0.0, 1.0),              # obsidian (blades, visor)
    "BH_Stone": ((0.09, 0.38, 0.29), 0.0, 0.3, None, 0.0, 1.0),                # jade
    "BH_Gold": ((0.72, 0.38, 0.18), 1.0, 0.35, None, 0.0, 1.0),                # copper wire
    "BH_Wood": ((0.12, 0.07, 0.04), 0.0, 0.7, None, 0.0, 1.0),                 # grips
    "BH_Bone": ((0.6, 0.53, 0.4), 0.0, 0.6, None, 0.0, 1.0),                   # quills, pins
    "BH_Shadow": ((0.015, 0.012, 0.014), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),     # wire tattoos (white)
}
CLIPS = ["dual_1", "dual_2", "dual_heavy", "leap_slam", "dagger_1"]

TORSO = [(r[0], r[1] * 0.93, r[2] * 0.92, r[3] * 0.94, r[4] * 0.6) for r in K.TORSO]
P = Z.P


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


def secondary(anim, frames):
    return KN.secondary(anim, frames)


def build(body):
    sb = K.SB(body, SCALE)
    torso(sb)
    waist(sb)
    cloak(sb)
    mantle(sb)
    head(sb)
    for s in ("L", "R"):
        arm(sb, s)
        K.add_fist(sb, s, "BH_Leather", "BH_Skin", scale=0.95)
    K.trousers(sb, "BH_Cloth_Secondary", loose=0.86, end=0.95)
    K.boots(sb, "BH_Cloth_Secondary", "BH_Leather", shaft_top=0.55, cuff=False, wraps="BH_Leather")
    for s in ("L", "R"):
        legwraps(sb, s)
    K.add_weapon(sb, "R", obsidian_blade(SCALE, seed=1))
    K.add_weapon(sb, "L", obsidian_blade(SCALE, seed=2))


# ================================================================================================= helpers
def tattoo(pts, r=0.0042):
    """A wire tattoo: a thin line of white light on the skin."""
    return A.tube(np.asarray(pts, float), r, "BH_Emissive", n=4)


def on_front(x, z, out=0.0015):
    return (x, front_y(TORSO, x, z) - out, z)


def on_back(x, z, out=0.0015):
    return (x, back_y(TORSO, x, z) + out, z)


def grown_wire(base, d, length, seed, r=0.0045):
    """A copper wire grown out through the skin: a bent strand with a frayed white tip."""
    rng = np.random.default_rng(seed)
    d = normalize(np.asarray(d, float))
    side = normalize(np.cross(d, (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)))
    pts = [np.asarray(base, float) - d * 0.01]
    for i in range(1, 5):
        t = i / 4
        pts.append(np.asarray(base, float) + d * length * t + side * 0.02 * math.sin(t * 3 + seed) +
                   (0, 0, -0.03 * t * t))
    out = [A.taper(pts, r, r * 0.7, "BH_Gold", n=4)]
    tip = pts[-1]
    out.append(A.ball(tip, r * 1.4, "BH_Emissive", n=5, rings=3))
    for k in range(2):
        dd = normalize(d + side * (0.6 if k else -0.6) + rng.normal(size=3) * 0.2)
        out.append(A.taper([tip, tip + dd * 0.035], r * 0.5, r * 0.2, "BH_Gold", n=3))
    out.append(A.ball(np.asarray(base, float), r * 2.4, "BH_Shadow", n=6, rings=3, scale=(1, 1, 0.5)))
    return out


# ================================================================================================= body
def torso(sb):
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.96], n=24, cap1=True)
    sb.add(P(V, F, "BH_Skin", "torso"), weights=K.TORSO_W)
    # lean muscle: faint pectoral / ab ridges
    for z in (1.15, 1.2):
        pts = K.ring_frac(TORSO, z, 0.002, np.linspace(-0.08, 0.08, 5) % 1.0)
        sb.add(A.tube(pts, 0.005, "BH_Skin", n=4), weights=K.TORSO_W)
    # wire tattoos: a stepped line down the sternum branching to the ribs, a spine line with cross bars
    sb.add(tattoo([on_front(0, z) for z in np.linspace(1.44, 1.08, 6)]), weights=K.TORSO_W)
    for sx in (1, -1):
        sb.add(tattoo([on_front(0, 1.34), on_front(sx * 0.05, 1.34), on_front(sx * 0.05, 1.28), on_front(sx * 0.1, 1.28),
                       on_front(sx * 0.1, 1.2)]), weights=K.TORSO_W)
        sb.add(tattoo([on_front(0, 1.16), on_front(sx * 0.06, 1.16), on_front(sx * 0.06, 1.1)]), weights=K.TORSO_W)
    sb.add(tattoo([on_back(0, z) for z in np.linspace(1.47, 1.02, 7)]), weights=K.TORSO_W)
    for z in (1.4, 1.3, 1.2, 1.1):
        w = 0.05 + 0.02 * (z > 1.25)
        sb.add(tattoo([on_back(-w, z), on_back(-w, z + 0.02), on_back(w, z + 0.02), on_back(w, z)]), weights=K.TORSO_W)
    # cross-strapped leather harness (X over the chest and back) with a jade plaque at the crossing
    rows = K.grow_rows(TORSO, 0.006)
    for sx in (1, -1):
        pts = [(sx * 0.12, front_y(rows, sx * 0.12, 1.47), 1.47), (sx * 0.04, front_y(rows, sx * 0.04, 1.33), 1.33),
               (-sx * 0.06, front_y(rows, -sx * 0.06, 1.2), 1.2), (-sx * 0.12, front_y(rows, -sx * 0.12, 1.06), 1.06)]
        sb.add(K.strip(pts, 0.035, 0.006, "BH_Leather"), weights=K.TORSO_W)
        pts = [(sx * 0.12, back_y(rows, sx * 0.12, 1.47), 1.47), (sx * 0.04, back_y(rows, sx * 0.04, 1.33), 1.33),
               (-sx * 0.06, back_y(rows, -sx * 0.06, 1.2), 1.2), (-sx * 0.12, back_y(rows, -sx * 0.12, 1.06), 1.06)]
        sb.add(K.strip(pts, 0.035, 0.006, "BH_Leather", ups=[(0, 1, 0)] * 4), weights=K.TORSO_W)
        # shoulder pad (light leather, two lames) over the strap
    zc = 1.265
    y = front_y(rows, 0, zc) - 0.008
    V, F = M.box(0.06, 0.012, 0.06)
    sb.add(M.bevel(P(V, F, "BH_Stone", "plaque").rot(Ry(45)).move((0, y, zc)), 0.006, 1), "chest")
    sb.add(A.ball((0, y - 0.008, zc), 0.01, "BH_Emissive", n=6, rings=4, scale=(1, 0.5, 1)), "chest")
    # corruption: copper wires grown out through the shoulders and the upper back
    for k, (x, z, d, ln) in enumerate(((0.1, 1.47, (0.4, 0.5, 1.0), 0.12), (-0.11, 1.46, (-0.5, 0.4, 1.0), 0.14),
                                       (0.05, 1.38, (0.3, 1.0, 0.4), 0.1), (-0.04, 1.3, (-0.3, 1.0, 0.2), 0.09),
                                       (0.07, 1.22, (0.5, 1.0, -0.2), 0.08))):
        base = on_back(x, z, -0.002)
        for prt in grown_wire(base, d, ln, 5 + k):
            sb.add(prt, "chest")


def waist(sb):
    rows = K.grow_rows(TORSO, 0.012)
    # wrapped sash (red) with leather belt over it
    V, F = K.band(rows, 0.97, 1.07, 0.01, -0.004, n=28)
    sb.add(P(V, F, "BH_Cloth_Primary", "sash"), "hips")
    for z in (0.99, 1.02, 1.05):
        ring = K.ring_frac(rows, z, 0.012, np.linspace(0, 1, 21))
        ring[:, 2] += 0.008 * np.sin(np.linspace(0, 6 * math.pi, 21))
        sb.add(A.tube(ring, 0.006, "BH_Cloth_Primary", n=4, cap=False), "hips")
    K.belt(sb, rows, z=0.955, h=0.035, g=0.006, mat="BH_Leather", buckle="BH_Stone")
    # short loincloth flaps front and back + a knotted sash tail
    for front in (True, False):
        pnl = HS.cloth_panel(rows, 0.96, 0.66, lambda z: 0.07 + 0.015 * (0.96 - z), front=front, nu=5, nv=7,
                             mat="BH_Cloth_Primary", gap=0.012, hang=0.05, rag=0.25, thick=0.007, belt_z=0.95)
        sb.add(pnl, weights=Z.centre_w(0.95, 0.6, 0.5))
    p, _ = K.on_ring(rows, 1.0, 0.02, 0.8)
    for dx, ln in ((0.0, 0.32), (0.025, 0.26)):
        pts = [p + (dx, 0, -0.02), p + (dx - 0.02, 0.01, -ln * 0.5), p + (dx - 0.03, 0.02, -ln)]
        sb.add(K.strip(pts, 0.045, 0.006, "BH_Cloth_Primary", ups=[(1, 0, 0)] * 3),
               weights=sb.skirt(1.0, 0.6, max_leg=0.5, center_w=0.05))
    # a small pouch of wire at the hip
    K.pouch(sb, rows, 0.3, 0.92, 0.012, size=(0.07, 0.035, 0.06), mat="BH_Leather")


def legwraps(sb, s):
    sh = "shin." + s
    K.wrap_band(sb, sh, "foot." + s, 0.05, 0.75, 0.054, "BH_Leather", turns=4, width=0.022, thick=0.006, bone=sh)
    th = "thigh." + s
    h, k = sb.head(th), sb.head(sh)
    # tattoo down the outer thigh (through a slit in the leggings: shows as a glowing line)
    sx = 1 if s == "L" else -1
    pts = [h + (k - h) * t + np.array([sx * (0.08 - 0.02 * t), 0.0, 0.0]) for t in np.linspace(0.15, 0.8, 4)]
    sb.add(tattoo(pts, 0.004), th)


# ================================================================================================= cloak
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


def cloak(sb):
    """Feather cloak to the knees: a dark backing sheet + overlapping rows of teal feathers, scarlet-tipped hem."""
    def fn(u, v):
        zb = 0.6 + 0.06 * math.cos((u - 0.5) * math.pi) - 0.08 * abs(u - 0.5)
        z = 1.5 + (zb - 1.5) * v
        side = (u - 0.5) * 2
        half = 0.16 + 0.12 * v ** 0.8
        x = side * half
        yb = back_y(TORSO, np.clip(x, -0.12, 0.12), min(max(z, 1.3), 1.48)) + 0.05 * (1 - abs(side))
        y = yb + 0.1 * v ** 1.2 + 0.03 * (1 - v) * (1 - side * side)
        y -= 0.09 * abs(side) ** 2.2 * v ** 0.9
        y -= 0.05 * abs(side) ** 3 * (1 - v) ** 2
        return (x, y, z)
    V, F = M.grid(fn, 9, 9)
    w = cape_w()
    back = P(V, F, "BH_Fur", "cloak")
    N = np.zeros_like(V)
    for f in F:
        a, b_, c = V[f[0]], V[f[1]], V[f[2]]
        n = np.cross(b_ - a, c - a)
        for i in f:
            N[i] += n
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    if np.mean(N[:, 1]) < 0:
        back.flip()
    sb.add(M.solidify(back, 0.009, offset=-1.0), weights=w)

    def nrm_at(u, v):
        e = 0.02
        p0 = np.array(fn(u, v))
        du = np.array(fn(min(u + e, 1), v)) - np.array(fn(max(u - e, 0), v))
        dv = np.array(fn(u, min(v + e, 1))) - np.array(fn(u, max(v - e, 0)))
        n = normalize(np.cross(du, dv))
        return p0, (n if n[1] > 0 else -n), normalize(dv), normalize(du)
    rows = [(0.1, 7, 0.2, 0.06, None), (0.32, 8, 0.22, 0.065, None), (0.55, 8, 0.24, 0.07, None),
            (0.78, 9, 0.24, 0.072, "BH_Flesh")]
    for ri, (v, cnt, ln, wd, tipm) in enumerate(rows):
        for i in range(cnt):
            u = (i + 0.5 * (ri % 2) + 0.25) / (cnt + 0.5)
            p, n, dv, du = nrm_at(u, v)
            d = normalize(dv + n * 0.12)
            for prt in Z.zfeather(p + n * (0.012 + 0.004 * ri), d, ln, wd, du,
                                  mats=("BH_Hair", tipm), tip=0.32 if tipm else 0.0, bend=-0.04, quill=False, k=5):
                sb.add(prt, weights=w)


def mantle(sb):
    """Feather mantle round the shoulders (short teal feathers, open at the throat)."""
    ring = K.ring_frac(TORSO, 1.48, 0.026, np.linspace(0, 1, 21)[:-1])
    ring = np.vstack([ring, ring[:1]])
    V, F = M.tube(ring, [(0.028, 0.024)] * len(ring), n=5, up=(0, 0, 1), cap0=False, cap1=False)
    sb.add(P(V, F, "BH_Hair", "mantle_roll"), "chest")
    n = 14
    for i in range(n):
        f = i / n
        if f < 0.1 or f > 0.9:
            continue
        q = K.ring_frac(TORSO, 1.47, 0.045, [f])[0]
        out = normalize(np.array([q[0], q[1], 0.0]))
        d = normalize(out * 0.8 + np.array([0, 0, -1.0]))
        tng = normalize(np.cross((0, 0, 1), out))
        for prt in Z.zfeather(q + (0, 0, 0.02), d, 0.14, 0.055, tng, mats=("BH_Hair", "BH_Flesh"), tip=0.25,
                              bend=0.03, quill=False, k=5):
            sb.add(prt, "chest")


# ================================================================================================= head
def head(sb):
    K.neck_and_head(sb, skin="BH_Skin", eyes="BH_Shadow", nose=True)
    K.hair_cap(sb, mat="BH_Fur", z_front=1.775, z_back=1.64, messy=0.004)
    # obsidian visor across the eyes with two white slits
    rows = K.grow_rows(K.HEAD, 0.008)
    rings = []
    for z in (1.682, 1.7, 1.718):
        rings.append(K.ring_frac(rows, z, 0.0, np.linspace(-0.24, 0.24, 13) % 1.0, p=2.1))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    sb.add(M.solidify(P(V, F, "BH_Horn", "visor"), 0.006, offset=1.0), "head")
    for sx in (1, -1):
        pts = K.ring_frac(rows, 1.7, 0.007, [(sx * f) % 1.0 for f in (0.03, 0.06, 0.09)], p=2.1)
        sb.add(A.tube(pts, (0.004, 0.0035), "BH_Emissive", n=4), "head")
        # jade ear spools
        V, F = M.lathe([(0.0, -0.006), (0.022, -0.006), (0.024, 0.0), (0.022, 0.006), (0.0, 0.006)], 10)
        sb.add(P(V, F, "BH_Stone", "spool").rot(Ry(90 * sx)).move((sx * 0.078, 0.0, 1.685)), "head")
        # tattoo lines from the visor down the cheeks
        sb.add(tattoo([K.ring_frac(K.grow_rows(K.HEAD, 0.001), z, 0.0, [(sx * 0.11) % 1.0], p=2.1)[0]
                       for z in (1.68, 1.66, 1.635)], 0.0032), "head")
    # topknot: a bound tail of black hair rising and falling back, a fan of short feathers in its binding
    knot = [(0, 0.03, 1.81), (0, 0.04, 1.86), (0, 0.07, 1.89), (0, 0.12, 1.86), (0, 0.15, 1.78), (0, 0.16, 1.7)]
    sb.add(A.tube(knot, [0.03, 0.028, 0.026, 0.022, 0.016, 0.008], "BH_Fur", n=6), "head")
    V, F = M.tube([(0, 0.035, 1.835), (0, 0.04, 1.865)], [(0.032, 0.032)] * 2, n=8, up=(0, -1, 0))
    sb.add(P(V, F, "BH_Gold", "binding"), "head")
    for i in range(5):
        a = math.radians(-50 + 25 * i)
        d = normalize(np.array([math.sin(a) * 0.8, 0.5, math.cos(a)]))
        for prt in Z.zfeather((0, 0.04, 1.86), d, 0.15, 0.04, (math.cos(a), 0, -math.sin(a)),
                              mats=("BH_Hair", "BH_Flesh"), tip=0.3, bend=0.02, quill=False, k=5):
            sb.add(prt, "head")


def arm(sb, s):
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    sx = 1 if s == "L" else -1
    K.bare_arm(sb, s, skin="BH_Skin", r_up=0.044, r_fore=0.038, r_wrist=0.029, bulk=1.0)
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    w = sb.seg(["chest", "shoulder." + s, ua, fa, ha], power=9)
    # leather bracer with lacing
    V, F = M.tube([el + (wr - el) * 0.4, el + (wr - el) * 0.7, wr + (wr - el) * 0.03],
                  [(0.042, 0.044), (0.04, 0.042), (0.034, 0.036)], n=10, up=(0, -1, 0))
    sb.add(P(V, F, "BH_Leather", "bracer"), fa)
    # light leather shoulder guard (two lames) on the outer shoulder
    for k in range(2):
        def fn(u, v, k=k):
            a = math.radians(-60 + 120 * u)
            b = math.radians(15 + 60 * v)
            r = 0.07 - 0.008 * k
            return (sh[0] + sx * (r * math.sin(b) + 0.008 + 0.03 * k), sh[1] + r * math.sin(a) * math.cos(b) * 1.1,
                    sh[2] + 0.03 + r * math.cos(a) * math.cos(b) * 0.5 - 0.04 * k)
        V, F = M.grid(fn, 6, 3)
        p = P(V, F, "BH_Leather", "spaulder")
        if sx > 0:
            p.flip()
        sb.add(M.solidify(p, 0.008, offset=0), weights=lambda V, s=s: [{"shoulder." + s: 0.4, "upper_arm." + s: 0.6}]
               * len(V))
    # wire tattoos: stepped lines down the outside of the arm (upper arm + forearm)
    for (a0, a1, th0, bone, rr) in ((sh, el, 0.0, ua, 0.046), (el, wr, 0.4, fa, 0.04)):
        dd = normalize(a1 - a0)
        side = normalize(np.cross(dd, (0, 1, 0))) * sx
        fw = np.cross(side, dd) * -1
        pts = []
        for i in range(7):
            t = 0.12 + 0.7 * i / 6
            th = th0 + (0.35 if (i // 2) % 2 else -0.35)
            nn = side * math.cos(th) + fw * math.sin(th)
            pts.append(a0 + (a1 - a0) * t + nn * (rr + 0.001))
        if bone == ua:
            sb.add(tattoo(pts, 0.0038), weights=w)
        else:
            sb.add(tattoo(pts, 0.0038), fa)
    # a copper armlet
    c = sh + (el - sh) * 0.45
    dd = normalize(el - sh)
    V, F = M.tube([c - dd * 0.01, c + dd * 0.01], [(0.05, 0.05)] * 2, n=10, up=(0, -1, 0))
    sb.add(P(V, F, "BH_Gold", "armlet"), ua)


# ================================================================================================= blades
def obsidian_blade(s=1.0, seed=1):
    """Knapped obsidian blade (weapon space: grip at origin, +Z blade, flats +-Y, edge +X): a long, slightly
    curved black glass blade with stepped knapped edges on a wire-wound wooden grip, a white-glowing hilt ring."""
    parts = []
    rng = np.random.default_rng(seed)
    V, F = M.lathe([(0.0, -0.12), (0.022, -0.12), (0.024, -0.105), (0.017, -0.09), (0.017, 0.04), (0.0, 0.04)], 8)
    parts.append(P(V, F, "BH_Wood", "grip"))
    parts.append(Z.coil((0, 0, -0.085), (0, 0, 0.03), 0.019, 6, 0.0035, "BH_Gold", n=4, pts_per_turn=8))
    parts.append(A.ball((0, 0, -0.13), 0.02, "BH_Stone", n=8, rings=4))
    V, F = M.lathe([(0.022, 0.035), (0.026, 0.045), (0.022, 0.055)], 10, cap=False)
    parts.append(P(V, F, "BH_Emissive", "hiltring"))
    V, F = M.lathe([(0.0, 0.03), (0.026, 0.03), (0.03, 0.06), (0.02, 0.075), (0.0, 0.075)], 8)
    parts.append(P(V, F, "BH_Gold", "ferrule").scale((1.3, 0.7, 1.0)))
    # blade outline: stepped (knapped) edges, slight back-curve toward -X near the tip
    n = 12
    L = 0.56
    edge, spine = [], []
    for i in range(n + 1):
        t = i / n
        z = 0.07 + L * t
        xc = -0.05 * t ** 2
        w = 0.032 * (1 - t ** 3) + 0.004
        if 0 < i < n:
            w += 0.006 * (1 if i % 2 else -1) + 0.003 * rng.random()
        edge.append((xc + w * 0.6, z))
        spine.append((xc - w * 0.45, z + (0.012 if 0 < i < n and i % 2 == 0 else 0.0)))
    o = np.array([edge[0]] + edge[1:] + [(edge[-1][0] - 0.02, 0.07 + L + 0.035)] + spine[::-1])
    if 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1]) < 0:
        o = o[::-1]
    V, F = M.prism(o, 0.014, axis="y")
    bl = P(V, F, "BH_Horn", "blade")
    # thin toward the edges (a lens section)
    bl.warp(lambda v: (v[0], v[1] * (0.35 + 0.65 * max(0.0, 1 - abs(v[0] + 0.025 * ((v[2] - 0.07) / L) ** 2) / 0.04)),
                       v[2]))
    parts.append(bl)
    # wire binding the glass into the ferrule + a white wire inlaid along the spine
    parts.append(Z.coil((-0.005, 0, 0.07), (-0.005, 0, 0.11), 0.03, 3, 0.003, "BH_Gold", n=4, pts_per_turn=8))
    for sy in (1, -1):
        pts = [(-0.012 - 0.05 * (t * 0.8) ** 2, sy * 0.005, 0.1 + L * 0.8 * t) for t in np.linspace(0, 1, 6)]
        parts.append(A.tube(pts, 0.0028, "BH_Emissive", n=4))
    for p in parts:
        p.V = p.V * s
    return parts
