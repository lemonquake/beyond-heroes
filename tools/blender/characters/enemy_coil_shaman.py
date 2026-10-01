"""Coil Shaman (bh-029, Builder M1, Zarael / the Coilwood caster): a thin, stooped wire-priest of Agdao gone over to
the Blackwire. A carved jade mask (glowing violet-red eye slits, a stepped-fret mouth, jade ear flares) under a
crown of short teal feathers and two long scarlet plumes, long black hair. A long feather cape (cape bones) of
overlapping teal feathers tipped scarlet over a hunched back, a feather mantle round the shoulders. Bare, bony dark
torso with a copper coil plug in the breastbone and glowing veins spreading from it, bead strings of jade and bone
across the chest. A long dark-green kilt with a copper fret hem, red sash. Thin arms wound with copper wire
(glowing), right hand on the staff, left hand open for casting. The staff: dark wood wound with glowing wire and
copper bands, ending in a carved jade serpent head (open jaws, glowing eyes, a feather crest).

~1.85 m (plumes ~2.0 m). Clips: cast_area cast_quick cast_weapon staff_1."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import char_knight as KN
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C
import enemy_hollow_soldier as HS
import kit_a_common as A
import enemy_glyphbound_warrior as Z

SCALE = 1.85 / 1.84
PROPS = proportions(SCALE, shoulder_x=0.168 * SCALE, hip_x=0.088 * SCALE, upper_len=0.3 * SCALE,
                    fore_len=0.285 * SCALE, hand_len=0.11 * SCALE)
EXTRA_BONES = [(n, tuple(np.array(h) * SCALE), tuple(np.array(t) * SCALE), par, z) for (n, h, t, par, z) in KN.CAPE_BONES]
PREVIEW_HEIGHT = 2.35
PALETTE = "coil_shaman"
PALETTE_COLORS = {
    "BH_Skin": ((0.21, 0.14, 0.1), 0.0, 0.6, None, 0.0, 1.0),                    # dark, ashen skin
    "BH_Cloth_Primary": ((0.36, 0.06, 0.04), 0.0, 0.9, None, 0.0, 1.0),          # red sash
    "BH_Cloth_Secondary": ((0.06, 0.1, 0.075), 0.0, 0.92, None, 0.0, 1.0),       # dark green kilt
    "BH_Hair": ((0.035, 0.27, 0.24), 0.0, 0.7, None, 0.0, 1.0),                  # teal feathers
    "BH_Flesh": ((0.48, 0.07, 0.04), 0.0, 0.7, None, 0.0, 1.0),                  # scarlet feathers
    "BH_Fur": ((0.02, 0.018, 0.02), 0.0, 0.75, None, 0.0, 1.0),                  # black hair, cape underside
    "BH_Stone": ((0.09, 0.38, 0.29), 0.0, 0.3, None, 0.0, 1.0),                  # jade
    "BH_Bone": ((0.6, 0.53, 0.4), 0.0, 0.6, None, 0.0, 1.0),                     # bone beads, quills, fangs
    "BH_Wood": ((0.09, 0.055, 0.035), 0.0, 0.7, None, 0.0, 1.0),                 # staff
    "BH_Leather": ((0.1, 0.06, 0.035), 0.0, 0.7, None, 0.0, 1.0),
    "BH_Gold": ((0.72, 0.38, 0.18), 1.0, 0.35, None, 0.0, 1.0),                  # copper wire / bands
    "BH_Shadow": ((0.015, 0.012, 0.014), 0.0, 0.8, None, 0.0, 1.0),
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),   # Zarael glows are white
}
CLIPS = ["cast_area", "cast_quick", "cast_weapon", "staff_1"]

TORSO = [(r[0], r[1] * 0.86, r[2] * 0.84, r[3] * 0.9, r[4] * 0.4) for r in K.TORSO]
P = Z.P


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


def secondary(anim, frames):
    return KN.secondary(anim, frames)


def build(body):
    sb = K.SB(body, SCALE)
    torso(sb)
    kilt(sb)
    cape(sb)
    mantle(sb)
    head(sb)
    for s in ("L", "R"):
        arm(sb, s)
    K.add_fist(sb, "R", "BH_Skin", "BH_Skin", scale=0.92)
    for prt in A.open_palm(sb.b, "L", "BH_Skin", s=SCALE * 0.92):
        sb.add_real(prt, "hand.L")
    for prt in A.bony_fingers(sb.b, "L", "BH_Skin", length=0.12 * SCALE, r=0.0065 * SCALE, curl=0.7, spread=1.1,
                              nails="BH_Shadow", open_hand=True):
        sb.add_real(prt, "hand.L")
    K.trousers(sb, "BH_Skin", loose=0.78, end=0.7)
    K.boots(sb, "BH_Leather", "BH_Leather", shaft_top=0.5, cuff=False, wraps="BH_Cloth_Primary")
    K.add_weapon(sb, "R", serpent_staff(SCALE))


# ================================================================================================= body
def torso(sb):
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.96], n=24, cap1=True)
    sb.add(P(V, F, "BH_Skin", "torso"), weights=K.TORSO_W)
    # hunched upper back (under the cape)
    V, F = M.sphere(0.13, 12, 7, center=(0, 0.06, 1.38), scale=(1.05, 0.75, 0.85))
    sb.add(P(V, F, "BH_Skin", "hump"), "chest")
    # ribs (bony chest) - faint ridges on the front
    for z in (1.2, 1.25, 1.3):
        pts = K.ring_frac(TORSO, z, 0.003, np.linspace(-0.17, 0.17, 9) % 1.0)
        pts = [q for q in pts]
        sb.add(A.tube(pts, 0.006, "BH_Skin", n=4), weights=K.TORSO_W)
    # copper coil plug in the breastbone with Blackwire veins spreading out
    zc = 1.34
    y = front_y(TORSO, 0, zc)
    sb.add(A.ball((0, y + 0.01, zc), 0.045, "BH_Shadow", n=10, rings=5, scale=(1, 0.4, 1)), "chest")
    for k, r in enumerate((0.036, 0.027, 0.018)):
        ring = [(r * math.cos(a), y - 0.006 - 0.004 * k, zc + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 15)]
        sb.add(A.tube(ring, 0.0055, "BH_Gold", n=4, cap=False), "chest")
    sb.add(A.ball((0, y - 0.012, zc), 0.012, "BH_Emissive", n=8, rings=4), "chest")
    rng = np.random.default_rng(3)
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.3
        pts = []
        for i in range(5):
            t = i / 4
            rr = 0.04 + 0.14 * t
            x = rr * math.cos(a + 0.25 * math.sin(i * 2.1 + k))
            z = zc + rr * math.sin(a + 0.25 * math.sin(i * 2.1 + k)) * 1.1
            pts.append((x, front_y(TORSO, x, min(max(z, 0.99), 1.5)) - 0.002, z))
        sb.add(A.tube(pts, [0.0055, 0.005, 0.0045, 0.0035, 0.002], "BH_Emissive", n=4), weights=K.TORSO_W)
    # bead strings: three loops from the neck over the chest + a long strand to the waist
    for k, (drop, r) in enumerate(((0.08, 0.011), (0.14, 0.012), (0.21, 0.013))):
        pts = []
        for t in np.linspace(-1, 1, 11):
            x = 0.085 * t * (1 + 0.5 * k / 2)
            z = 1.49 - drop * (1 - t * t) - 0.02
            pts.append((x, front_y(TORSO, x, max(z, 1.0)) - 0.012 - 0.01 * k, z))
        mats = ("BH_Stone", "BH_Bone") if k != 1 else ("BH_Bone", "BH_Gold", "BH_Bone")
        for prt in Z.beads(pts, r, mats):
            sb.add(prt, "chest")
    pts = [(0.06, front_y(TORSO, 0.06, 1.45) - 0.03, 1.45), (0.04, front_y(TORSO, 0.04, 1.2) - 0.035, 1.2),
           (0.02, front_y(TORSO, 0.02, 1.08) - 0.03, 1.08)]
    for prt in Z.beads(pts, 0.012, ("BH_Stone", "BH_Stone", "BH_Bone")):
        sb.add(prt, weights=K.TORSO_W)
    sb.add(A.ball((0.02, front_y(TORSO, 0.02, 1.05) - 0.035, 1.05), 0.028, "BH_Stone", n=8, rings=5,
                  scale=(1, 0.5, 1.2)), "spine")


def kilt(sb):
    C.robe_skirt(sb, "BH_Cloth_Secondary", trim="BH_Gold", z_top=1.04, z_bot=0.3, flare=0.12, folds=0.012, g=0.0)
    rows = [(r[0], r[1] + 0.02, r[2] + 0.02, r[3] + 0.02, r[4]) for r in TORSO]
    V, F = K.band(rows, 0.98, 1.06, 0.012, -0.004, n=28)
    sb.add(P(V, F, "BH_Cloth_Primary", "sash"), "hips")
    # front apron with a fret border
    pnl = HS.cloth_panel(rows, 1.02, 0.42, lambda z: 0.075, front=True, nu=5, nv=8, mat="BH_Cloth_Primary",
                         gap=0.02, hang=0.12, rag=0.0, thick=0.007, belt_z=1.0)
    sb.add(pnl, weights=Z.centre_w(1.0, 0.5, 0.5))
    yb = front_y(rows, 0, 1.0) - 0.02 - 0.12 * 0.55 - 0.012
    fw = Z.fret_wave(2)
    pts = [(-0.07 + 0.14 * u, yb, 0.47 + 0.05 * v) for u, v in fw]
    sb.add(A.tube(pts, (0.006, 0.0025), "BH_Gold", n=4, up=(0, -1, 0)), weights=Z.centre_w(1.0, 0.5, 0.5))


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
    """Long cape of overlapping feathers: a dark backing sheet + rows of teal feathers (scarlet-tipped hem row)."""
    def fn(u, v):
        zb = 0.36 + 0.05 * math.cos((u - 0.5) * math.pi)
        z = 1.5 + (zb - 1.5) * v
        side = (u - 0.5) * 2
        half = 0.17 + 0.16 * v ** 0.8
        x = side * half
        yb = back_y(TORSO, np.clip(x, -0.13, 0.13), min(max(z, 1.3), 1.48)) + 0.09 * (1 - abs(side))
        y = yb + 0.12 * v ** 1.2 + 0.035 * (1 - v) * (1 - side * side)
        y -= 0.1 * abs(side) ** 2.2 * v ** 0.9
        y -= 0.05 * abs(side) ** 3 * (1 - v) ** 2
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
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    if np.mean(N[:, 1]) < 0:
        N = -N
        back.flip()
    sb.add(M.solidify(back, 0.01, offset=-1.0), weights=w)

    def nrm_at(u, v):
        e = 0.02
        p0 = np.array(fn(u, v))
        du = np.array(fn(min(u + e, 1), v)) - np.array(fn(max(u - e, 0), v))
        dv = np.array(fn(u, min(v + e, 1))) - np.array(fn(u, max(v - e, 0)))
        n = normalize(np.cross(du, dv))
        return p0, (n if n[1] > 0 else -n), normalize(dv), normalize(du)
    rows = [(0.08, 7, 0.2, 0.06, None), (0.27, 8, 0.24, 0.07, None), (0.48, 9, 0.26, 0.075, None),
            (0.7, 9, 0.28, 0.08, "BH_Flesh"), (0.9, 10, 0.26, 0.08, "BH_Flesh")]
    for ri, (v, cnt, ln, wd, tipm) in enumerate(rows):
        for i in range(cnt):
            u = (i + 0.5 * (ri % 2) + 0.25) / (cnt + 0.5)
            p, n, dv, du = nrm_at(u, v)
            d = normalize(dv + n * 0.12)
            for prt in Z.zfeather(p + n * (0.012 + 0.004 * ri), d, ln, wd, du,
                                  mats=("BH_Hair", tipm), tip=0.3 if tipm else 0, bend=-0.04, quill=False, k=5):
                sb.add(prt, weights=w)


def mantle(sb):
    """Feather mantle round the shoulders: a padded ring with short feathers radiating down and out."""
    ring = K.ring_frac(TORSO, 1.48, 0.03, np.linspace(0, 1, 25)[:-1])
    ring = np.vstack([ring, ring[:1]])
    V, F = M.tube(ring, [(0.035, 0.03)] * len(ring), n=6, up=(0, 0, 1), cap0=False, cap1=False)
    sb.add(P(V, F, "BH_Hair", "mantle_roll"), "chest")
    n = 16
    for i in range(n):
        f = i / n
        q = K.ring_frac(TORSO, 1.47, 0.05, [f])[0]
        out = normalize(np.array([q[0], q[1], 0.0]))
        if abs(f - 0.0) < 0.07 or abs(f - 1.0) < 0.07:
            continue                      # open at the throat (the beads show)
        d = normalize(out * 0.8 + np.array([0, 0, -1.0]))
        tng = normalize(np.cross((0, 0, 1), out))
        for prt in Z.zfeather(q + (0, 0, 0.02), d, 0.16, 0.06, tng, mats=("BH_Hair", "BH_Flesh"), tip=0.25,
                              bend=0.03, quill=False, k=5):
            sb.add(prt, "chest")


# ================================================================================================= head
def head(sb):
    K.neck_and_head(sb, skin="BH_Skin", eyes="BH_Shadow", nose=False)
    K.hair_cap(sb, mat="BH_Fur", z_front=1.76, z_back=1.6, messy=0.008)
    # long hair down the back (under the mantle)
    for k, x in enumerate((-0.05, 0.0, 0.05)):
        pts = [(x, 0.08, 1.72), (x * 1.3, 0.12, 1.6), (x * 1.5, 0.15, 1.45), (x * 1.6, 0.17, 1.32)]
        sb.add(K.strip(pts, 0.06, 0.012, "BH_Fur", ups=[(0, 1, 0)] * 4), weights=K.zspec_w([(1.42, "chest"),
                                                                                         (1.56, "neck"),
                                                                                         (1.62, "head")]))
    # jade mask: a carved plate over the face
    hz = 1.6

    def fn(u, v):
        x = (u - 0.5) * 0.15
        z = hz + 0.005 + 0.2 * v
        bulge = (1 - (2 * u - 1) ** 2) ** 0.5 * (1 - (2 * v - 1) ** 2) ** 0.4
        y = -0.083 - 0.022 * bulge + 0.01 * (2 * v - 1) ** 2
        xs = x * (0.82 + 0.25 * math.sin(math.pi * min(v * 1.2, 1.0)))
        return (xs, y, z)
    V, F = M.grid(fn, 9, 9)
    mask = P(V, F, "BH_Stone", "mask")
    c = V[:, :].mean(0)
    nn = np.cross(V[F[0][1]] - V[F[0][0]], V[F[0][2]] - V[F[0][0]])
    if nn[1] > 0:
        mask.flip()
    sb.add(M.solidify(mask, 0.014, offset=-1.0), "head")

    def surf(x, z, out=0.0):
        u = 0.5 + x / 0.15 / (0.82 + 0.25 * math.sin(math.pi * min((z - hz - 0.005) / 0.2 * 1.2, 1.0)))
        v = (z - hz - 0.005) / 0.2
        return np.array([x, fn(u, v)[1] - out, z])
    # eye slits (dark recess + glowing slit), heavy brow, nose ridge, stepped-fret mouth
    for sx in (1, -1):
        pts = [surf(sx * x, hz + z, 0.002) for x, z in ((0.012, 0.112), (0.03, 0.12), (0.05, 0.116))]
        sb.add(A.tube(pts, (0.016, 0.006), "BH_Shadow", n=4, up=(0, -1, 0)), "head")
        pts = [surf(sx * x, hz + z, 0.006) for x, z in ((0.016, 0.113), (0.03, 0.12), (0.046, 0.117))]
        sb.add(A.tube(pts, (0.009, 0.003), "BH_Emissive", n=4, up=(0, -1, 0)), "head")
        pts = [surf(sx * x, hz + z, 0.006) for x, z in ((0.008, 0.138), (0.034, 0.146), (0.06, 0.136))]
        sb.add(A.tube(pts, 0.009, "BH_Stone", n=4), "head")
        # cheek frets
        fw = Z.fret_wave(1, steps=2)
        pts = [surf(sx * (0.025 + 0.03 * u), hz + 0.065 + 0.025 * v, 0.003) for u, v in fw]
        sb.add(A.tube(pts, (0.0035, 0.002), "BH_Shadow", n=4, up=(0, -1, 0)), "head")
        # ear flares (jade discs) + a dangling bead
        V, F = M.lathe([(0.0, -0.007), (0.03, -0.006), (0.034, 0.0), (0.03, 0.008), (0.0, 0.006)], 12)
        sb.add(P(V, F, "BH_Stone", "flare").rot(Ry(90 * sx)).move((sx * 0.085, -0.005, hz + 0.095)), "head")
        sb.add(A.ball((sx * 0.092, -0.005, hz + 0.095), 0.012, "BH_Gold", n=6, rings=4), "head")
        for prt in Z.beads([(sx * 0.09, -0.01, hz + 0.065), (sx * 0.092, -0.012, hz - 0.01)], 0.009,
                           ("BH_Bone", "BH_Stone")):
            sb.add(prt, "head")
    pts = [surf(0, hz + z, o) for z, o in ((0.13, 0.004), (0.095, 0.012), (0.08, 0.008))]
    sb.add(A.tube(pts, [(0.012, 0.01), (0.015, 0.012), (0.012, 0.008)], "BH_Stone", n=5), "head")
    fw = Z.fret_wave(2, steps=2)
    pts = [surf(-0.04 + 0.08 * u, hz + 0.032 + 0.024 * v, 0.003) for u, v in fw]
    sb.add(A.tube(pts, (0.005, 0.003), "BH_Shadow", n=4, up=(0, -1, 0)), "head")
    # crown: a band with short teal feathers and two long scarlet plumes sweeping back
    V, F = M.lathe([(0.088, 0.168), (0.094, 0.172), (0.094, 0.2), (0.088, 0.204)], 18, cap=False)
    sb.add(P(V, F, "BH_Gold", "crownband").scale((1.0, 1.12, 1.0)).move((0, 0.005, hz)), "head")
    n = 11
    for i in range(n):
        a = math.radians(-120 + 240 * i / (n - 1))
        q = np.array([0.092 * math.sin(a), 0.005 - 0.1 * math.cos(a), hz + 0.2])
        d = normalize(np.array([0.35 * math.sin(a), -0.35 * math.cos(a) + 0.2, 1.0]))
        tng = np.array([math.cos(a), math.sin(a), 0.0])
        for prt in Z.zfeather(q, d, 0.15, 0.05, tng, mats=("BH_Hair", "BH_Flesh"), tip=0.3, bend=0.02, quill=False,
                              k=6):
            sb.add(prt, "head")
    for dx in (-0.3, 0.0, 0.3):
        q = np.array([dx * 0.05, 0.06, hz + 0.21])
        d = normalize(np.array([dx, 1.0, 0.55 + 0.1 * (dx == 0)]))
        for prt in Z.zfeather(q, d, 0.4 + 0.06 * (dx == 0), 0.075, (1, 0, -dx), mats=("BH_Flesh", "BH_Hair"), tip=0.22,
                              bend=-0.1):
            sb.add(prt, "head")
    sb.add(A.ball((0, -0.105, hz + 0.19), 0.022, "BH_Stone", n=8, rings=5, scale=(1, 0.6, 1)), "head")


def arm(sb, s):
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    K.bare_arm(sb, s, skin="BH_Skin", r_up=0.04, r_fore=0.036, r_wrist=0.028, bulk=0.95)
    el, wr = sb.head(fa), sb.head(ha)
    sh = sb.head(ua)
    d = normalize(wr - el)
    # copper wire wound round the forearm, the Blackwire glowing between the turns
    sb.add(Z.coil(el + (wr - el) * 0.25, el + (wr - el) * 0.92, 0.038, 6, 0.0045, "BH_Gold", n=4, pts_per_turn=8), fa)
    V, F = M.tube([el + (wr - el) * 0.27, el + (wr - el) * 0.9], [(0.035, 0.035), (0.03, 0.031)], n=8, up=(0, -1, 0))
    sb.add(P(V, F, "BH_Emissive", "wireglow"), fa)
    # copper armlet on the upper arm with a jade bead
    c = sh + (el - sh) * 0.55
    dd = normalize(el - sh)
    V, F = M.tube([c - dd * 0.012, c + dd * 0.012], [(0.048, 0.048)] * 2, n=10, up=(0, -1, 0))
    sb.add(P(V, F, "BH_Gold", "armlet"), ua)


# ================================================================================================= staff
def serpent_staff(s=1.0):
    """Staff (weapon space, grip at origin, +Z up): dark wood wound with glowing wire and copper bands, ending in a
    carved jade serpent head (faces -Y): open jaws, fangs, glowing eyes, a feather crest; beads hang below."""
    parts = []
    pts = [(0.008 * math.sin(u * 6.0), 0.006 * math.cos(u * 4.0), -1.0 + 1.78 * u) for u in np.linspace(0, 1, 12)]
    parts.append(A.tube(pts, [0.019 + 0.002 * math.sin(i * 1.7) for i in range(12)], "BH_Wood", n=8))
    parts.append(A.ball((0, 0, -1.0), 0.022, "BH_Gold", n=6, rings=4))
    for z0, z1, t in ((0.18, 0.7, 7), (-0.75, -0.35, 4)):
        parts.append(Z.coil((0, 0, z0), (0, 0, z1), 0.024, t, 0.004, "BH_Emissive", n=4, pts_per_turn=8))
    for z in (-0.76, -0.33, 0.16, 0.72):
        V, F = M.lathe([(0.0, z - 0.016), (0.026, z - 0.016), (0.028, z), (0.026, z + 0.016), (0.0, z + 0.016)], 8)
        parts.append(P(V, F, "BH_Gold", "band"))
    parts.append(Z.coil((0, 0, -0.1), (0, 0, 0.12), 0.021, 5, 0.004, "BH_Leather", n=4, pts_per_turn=8))
    # serpent: neck rising from the shaft and curling forward, the head facing -Y
    neck = [(0, 0.0, 0.76), (0, 0.02, 0.84), (0, 0.0, 0.92), (0, -0.04, 0.97), (0, -0.08, 0.99)]
    parts.append(A.tube(neck, [0.026, 0.03, 0.033, 0.036, 0.038], "BH_Stone", n=8))
    for k in range(4):                         # carved scale rings
        q = np.array(neck[k + 1]) * 0.5 + np.array(neck[k]) * 0.5
        parts.append(A.ball(q, 0.034 + 0.003 * k, "BH_Stone", n=8, rings=3, scale=(1, 1, 0.45)))
    upper = [(0, -0.07, 1.0), (0, -0.12, 1.008), (0, -0.17, 1.005), (0, -0.205, 0.995)]
    parts.append(A.tube(upper, [(0.045, 0.034), (0.043, 0.03), (0.032, 0.022), (0.016, 0.012)], "BH_Stone", n=8,
                        p=2.6))
    lower = [(0, -0.075, 0.975), (0, -0.12, 0.945), (0, -0.165, 0.92), (0, -0.19, 0.905)]
    parts.append(A.tube(lower, [(0.034, 0.016), (0.031, 0.014), (0.022, 0.01), (0.012, 0.007)], "BH_Stone", n=6,
                        p=2.4))
    parts.append(A.tube([(0, -0.09, 0.982), (0, -0.17, 0.968)], [(0.025, 0.012), (0.015, 0.008)], "BH_Shadow", n=6))
    for sx in (1, -1):
        parts.append(A.taper([(sx * 0.018, -0.18, 0.985), (sx * 0.017, -0.185, 0.95)], 0.006, 0.001, "BH_Bone", n=4))
        parts.append(A.taper([(sx * 0.012, -0.17, 0.918), (sx * 0.012, -0.172, 0.94)], 0.004, 0.001, "BH_Bone", n=4))
        parts.append(A.ball((sx * 0.033, -0.12, 1.025), 0.011, "BH_Emissive", n=6, rings=4))
        parts.append(A.tube([(sx * 0.02, -0.09, 1.04), (sx * 0.036, -0.13, 1.034), (sx * 0.03, -0.16, 1.02)], 0.008,
                            "BH_Stone", n=4))
        parts.append(A.ball((sx * 0.012, -0.205, 1.0), 0.005, "BH_Shadow", n=5, rings=3))
    # feather crest behind the head
    for k in range(5):
        a = math.radians(-40 + 20 * k)
        d = normalize(np.array([math.sin(a) * 0.7, 0.55, math.cos(a)]))
        for prt in Z.zfeather((0, -0.05, 1.02), d, 0.15, 0.045, (math.cos(a), 0, -math.sin(a)), tip=0.3, bend=0.03,
                              quill=False):
            parts.append(prt)
    # wire ring round the neck + hanging beads and a short glowing wire ribbon
    V, F = M.lathe([(0.04, 0.8), (0.044, 0.81), (0.04, 0.82)], 12, cap=False)
    parts.append(P(V, F, "BH_Gold", "neckring"))
    for k, (a, ln) in enumerate(((30, 0.16), (150, 0.12), (270, 0.18))):
        r = math.radians(a)
        top = np.array([0.04 * math.cos(r), 0.04 * math.sin(r), 0.8])
        bot = top + np.array([0.01 * math.cos(r), 0.01 * math.sin(r), -ln])
        if k == 2:
            parts.append(A.tube([top, (top + bot) / 2 + (0.006, 0, 0), bot], 0.004, "BH_Emissive", n=4))
        else:
            parts += Z.beads([top, bot], 0.01, ("BH_Bone", "BH_Stone"))
    for p in parts:
        p.V = p.V * s
    return parts
