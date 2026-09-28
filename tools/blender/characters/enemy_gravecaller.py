"""Gravecaller (bh-013, Builder A; undead SUMMONER that raises a ring of Bone Thralls): a gaunt, stooped, grey-skinned
grave-priest (~1.95 m to the crown). Layered robes: a floor-length bone-white under-robe with a ragged hem, a moss-green
over-robe split at the front and a long moss-green back drape, bell sleeves with tatters. A mantle of small vertebrae
strung in rows over a moss-green shoulder capelet (strands dangle past its hem). The head wears a bleached stag skull
as a headdress (snout jutting over the brow, empty sockets with green glints) with a tall pair of branching antlers
hung with moss rags and bone charms: the silhouette key, rising to ~2.4 m. Hollow-cheeked grey face with green eyes.
Right hand: a long crooked staff (weathered grey wood, knotted and bent) topped by a ribcage cage holding a green
soul-flame, small skulls tied on cords under it (weapon.R). Left hand open, long clawed grey fingers.

Clips: staff_1, staff_heavy, cast_quick, cast_area, cast_heavy, boss_summon (+ the shared enemy base clips).
Robe helpers: enemy_ashen_cultist; kit: enemy_bandit_cutthroat (SB standard-space authoring) + kit_a_common."""
import math

import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep, M_align_z
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C
import enemy_hollow_soldier as HS
import kit_a_common as A

SCALE = 1.95 / 1.835
PROPS = proportions(SCALE, shoulder_x=0.17 * SCALE, hip_x=0.09 * SCALE, upper_len=0.3 * SCALE,
                    fore_len=0.285 * SCALE, hand_len=0.11 * SCALE)
PREVIEW_HEIGHT = 2.6
PALETTE = "gravecaller"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.47, 0.45, 0.39), 0.0, 0.92, None, 0.0, 1.0),       # bone-white under-robe (grave linen)
    "BH_Cloth_Secondary": ((0.085, 0.15, 0.055), 0.0, 0.9, None, 0.0, 1.0),    # moss-green over-robe / capelet
    "BH_Skin": ((0.33, 0.34, 0.33), 0.0, 0.6, None, 0.0, 1.0),                 # grey dead skin
    "BH_Bone": ((0.74, 0.71, 0.62), 0.0, 0.62, None, 0.0, 1.0),                # bleached stag skull, vertebrae, ribs
    "BH_Horn": ((0.4, 0.34, 0.25), 0.0, 0.7, None, 0.0, 1.0),                  # antlers (darker bone)
    "BH_Wood": ((0.2, 0.18, 0.15), 0.0, 0.85, None, 0.0, 1.0),                 # weathered grey staff wood
    "BH_Leather": ((0.06, 0.05, 0.04), 0.0, 0.75, None, 0.0, 1.0),             # cords, straps, boots
    "BH_Fur": ((0.05, 0.1, 0.03), 0.0, 0.95, None, 0.0, 1.0),                  # hanging moss rags
    "BH_Shadow": ((0.02, 0.025, 0.02), 0.0, 0.8, None, 0.0, 1.0),              # sockets
    "BH_Emissive": ((0.35, 1.0, 0.5), 0.0, 0.4, (0.35, 1.0, 0.5), 9.0, 1.0),   # green soul-flame, eyes
}
CLIPS = ["staff_1", "staff_heavy", "cast_quick", "cast_area", "cast_heavy", "boss_summon"]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


# gaunt torso with a hump at the upper back (stoop)
TORSO = [(r[0], r[1] * 0.86, r[2] * 0.82, r[3] * (0.9 + 0.45 * max(0.0, 1 - abs(r[0] - 1.42) / 0.11)), r[4] * 0.5)
         for r in K.TORSO]
G = 0.012
HEAD_DY, HEAD_DZ = -0.04, -0.028       # head carried forward and low (stooped)
OFF = np.array([0.0, HEAD_DY, HEAD_DZ])


def build(body):
    sb = K.SB(body, SCALE)
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="body"), weights=C.ROBE_W)
    # ---- robes: bone-white under-robe to the floor, moss-green split over-robe + back drape
    C.robe_top(sb, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", g=G, rows=TORSO, v_open=0.03)
    C.robe_skirt(sb, "BH_Cloth_Primary", trim=None, z_top=1.07, z_bot=0.06, flare=0.15, folds=0.016, ragged=0.08,
                 g=G - 0.02)
    over_robe(sb)
    belt_and_charms(sb)
    bone_mantle(sb)
    head(sb)
    headdress(sb)
    # ---- arms: bell sleeves with tatters, grey bony hands
    for s in ("L", "R"):
        C.bell_sleeve(sb, s, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", cuff_r=0.08, end=0.74)
        sleeve_tatters(sb, s)
    K.add_fist(sb, "R", "BH_Skin", "BH_Skin", scale=0.95)
    for prt in A.bony_fingers(sb.b, "R", "BH_Skin", length=0.06 * SCALE, r=0.0066 * SCALE, curl=0.6,
                              nails="BH_Shadow", s=1.0):
        sb.add_real(prt, "hand.R")
    for prt in A.open_palm(sb.b, "L", "BH_Skin", s=SCALE * 0.95):
        sb.add_real(prt, "hand.L")
    for prt in A.bony_fingers(sb.b, "L", "BH_Skin", length=0.14 * SCALE, r=0.0066 * SCALE, curl=0.9, spread=1.1,
                              nails="BH_Shadow", open_hand=True):
        sb.add_real(prt, "hand.L")
    # ---- legs (hidden) + wrapped feet
    K.trousers(sb, "BH_Cloth_Primary", loose=0.85)
    K.boots(sb, "BH_Leather", "BH_Leather", shaft_top=0.35, cuff=False, wraps="BH_Cloth_Primary")
    # ---- staff
    K.add_weapon(sb, "R", ribcage_staff(SCALE))


# ================================================================================================= robes
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


def over_robe(sb):
    """Moss-green over-robe: two front panels from the collar to mid-shin (split at the centre so the bone-white
    under-robe shows, ragged hems), wrapping round to the sides, and a long tattered moss drape down the back."""
    for sx, seed in ((1, 1.3), (-1, 3.1)):
        side = "L" if sx > 0 else "R"

        def fn(u, v, sx=sx, seed=seed):
            zb = 0.42 + HS.ragged(u, seed, 0.16, 3)
            zt = 1.47
            z = zt + (zb - zt) * v
            # u: 0 = centre opening, 1 = side seam (wraps a little round the side)
            a0 = 0.06 + 0.05 * max(0.0, 1.1 - z)          # the opening widens below the belt
            ang = a0 + u * (0.27 - a0)                    # ring fraction from the front toward the side
            if z >= 1.05:
                p = K.ring_frac(TORSO, z, G + 0.012, [ang])[0]
            else:
                p = K.ring_frac(TORSO, 1.05, G + 0.012 + 0.11 * (1.05 - z) ** 1.05, [ang])[0]
                p[2] = z
            x = sx * abs(p[0])
            y = p[1] - 0.004 * math.sin(u * 7 + seed) * max(0.0, 1.05 - z) * 4
            if z < 1.05:
                y -= 0.03 * (1.05 - z) * (1 - u)
            return (x, y, z)
        V, F = M.grid(fn, 7, 13)
        p = M.Part(V, F, "BH_Cloth_Secondary", name="overrobe")
        if sx < 0:
            p.flip()
        sb.add(M.solidify(p, 0.008, offset=1.0), weights=panel_w(side))

    def fn(u, v):
        zb = 0.27 + HS.ragged(u, 5.3, 0.18, 6)
        z = 1.47 + (zb - 1.47) * v
        hw = 0.17 + 0.12 * v
        x = (u - 0.5) * 2 * hw
        if z > 1.2:
            y = back_y(TORSO, x * 0.95, z) + G + 0.022
        else:
            y = back_y(TORSO, x * 0.95, 1.2) + G + 0.022 + 0.07 * (1.2 - z)
        y += 0.014 * math.sin(u * math.pi * 5) * v
        return (x, y, z)
    V, F = M.grid(fn, 10, 13)
    p = M.Part(V, F, "BH_Cloth_Secondary", name="drape").flip()
    sb.add(M.solidify(p, 0.009, offset=1.0), weights=drape_w(0.4))


def drape_w(leg):
    """Back drape: chest/spine/hips above the belt; below it both thighs share the leg influence equally, so the
    drape follows the average of the legs (no tearing down the middle when they swing apart)."""
    base = HS.cloth_w(chest_z=1.34, belt_z=1.05, leg=0.0)

    def wfn(V):
        out = base(V)
        for i, v in enumerate(V):
            if v[2] < 1.02:
                s_ = float(smoothstep(1.02, 0.55, v[2])) * leg
                out[i] = {"hips": 1 - s_, "thigh.L": s_ / 2, "thigh.R": s_ / 2} if s_ > 1e-3 else {"hips": 1.0}
        return out
    return wfn


def belt_and_charms(sb):
    V, F = K.band(TORSO, 0.99, 1.08, G + 0.032, G - 0.004, n=28)
    sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="sash"), "hips")
    C.rope_belt(sb, z=1.02, g=G + 0.042, mat="BH_Leather", knot_frac=0.9, tails=0.3, rows=TORSO)
    w = sb.skirt(1.0, 0.6, max_leg=0.45, center_w=0.05)
    for frac, ln, kind in ((0.05, 0.16, "bones"), (0.14, 0.22, "skull"), (0.62, 0.2, "bones"), (0.8, 0.14, "skull")):
        p, ang = K.on_ring(TORSO, 1.0, G + 0.05, frac)
        bot = p + np.array([0, 0, -ln])
        sb.add(A.tube([p, (p + bot) / 2 + (0, -0.005, 0), bot], 0.0035, "BH_Leather", n=4, up=(1, 0, 0)), weights=w)
        out = normalize(np.array([p[0], p[1], 0.0]))
        if kind == "skull":
            for prt in A.skull_charm(bot + (0, 0, -0.03), 0.032, "BH_Bone", "BH_Shadow", eyes="BH_Emissive", face=out,
                                     n=8):
                sb.add(prt, weights=w)
        else:
            for k, dx in enumerate((-0.012, 0.0, 0.012)):
                q = bot + np.array([dx, 0, -0.01 * k])
                sb.add(A.tube([q, q + (dx * 0.6, 0, -0.07)], 0.006, "BH_Bone", n=5), weights=w)


def sleeve_tatters(sb, s):
    fa, ha = "forearm." + s, "hand." + s
    el, wr = sb.head(fa), sb.head(ha)
    d = normalize(wr - el)
    c = el + (wr - el) * 0.72
    side = normalize(np.cross(d, (0, 1, 0)))
    fw = np.cross(side, d)
    for k, ang in enumerate((200, 250, 300, 340)):
        a = math.radians(ang)
        nrm = side * math.cos(a) + fw * math.sin(a)
        top = c + nrm * 0.076
        down = normalize(d * 0.6 + np.array([0, 0, -1.0]) * 0.8 + nrm * 0.2)
        mat = "BH_Cloth_Secondary" if k % 2 else "BH_Cloth_Primary"
        sb.add(A.rag_strip(top, down, 0.1 + 0.05 * (k % 2), 0.045, mat, out=nrm, seed=k), fa)


# ================================================================================================= bone mantle
def vertebra(c, d, out, r=0.016, h=0.011, mat="BH_Bone"):
    """One small vertebra (low poly): a drum along the strand direction d, two short side wings and a spinous
    process angled down the strand and out (along `out`)."""
    d = normalize(d)
    o = normalize(np.asarray(out, float) - d * np.dot(out, d))
    R = M_align_z(d, o)
    V, F = M.lathe([(0.0, -h), (r, -h * 0.45), (r, h * 0.45), (0.0, h)], 5)
    parts = [M.Part(np.asarray(V) @ R.T + c, F, mat, name="vert")]
    pd = normalize(o * 0.55 + d * 0.8)
    parts.append(A.tube([c + o * r * 0.4, c + o * r * 0.4 + pd * (r * 1.3)], [(0.006, 0.004), (0.003, 0.002)], mat,
                        n=3, cap=False, name="spine"))
    wing = normalize(np.cross(d, o))
    parts.append(A.tube([c - wing * r * 1.5, c + wing * r * 1.5], (0.004, 0.004), mat, n=3, cap=False, name="wing"))
    return parts


def mantle_w(Vs):
    out = []
    for v in Vs:
        a = float(smoothstep(0.1, 0.26, abs(v[0])))
        s = "shoulder.L" if v[0] > 0 else "shoulder.R"
        out.append({"chest": 1 - 0.6 * a, s: 0.6 * a} if a > 1e-3 else {"chest": 1.0})
    return out


def bone_mantle(sb):
    """Moss-green shoulder capelet with strands of vertebrae laid over it from the collar down past the hem."""
    zs = (1.51, 1.47, 1.42, 1.36, 1.3)
    nu = 32
    rings = []
    for k, z in enumerate(zs):
        t = k / (len(zs) - 1)
        r = K.ring_frac(TORSO, max(z, 1.4), G + 0.024 + 0.055 * t, np.linspace(0, 1, nu + 1)[:-1])
        r[:, 0] *= 1.0 + 0.16 * t
        r[:, 2] = z - 0.02 * t * np.cos(np.linspace(0, 1, nu + 1)[:-1] * 2 * math.pi) ** 2
        rings.append(r)
    V, F = M.loft(rings[::-1], cap0=False, cap1=False)
    sb.add(M.solidify(M.Part(V, F, "BH_Cloth_Secondary", name="capelet"), 0.01, offset=1.0), weights=mantle_w)
    # vertebra strands (skip the very front so the chest reads)
    for i in range(1, nu, 2):
        frac = i / nu
        if frac < 0.06 or frac > 0.94:
            continue
        pts = []
        for k in range(len(zs)):
            q = rings[k][i]
            nrm = normalize(np.array([q[0], q[1] - 0.0, 0.0]))
            pts.append(q + nrm * 0.016)
        pts = np.array(pts)
        nrm_top = normalize(np.array([pts[0][0], pts[0][1], 0.0]))
        # dangling tail past the hem (longer at the back and over the shoulders)
        dangle = 0.05 + 0.1 * (0.5 + 0.5 * math.sin(i * 2.3)) * (1.0 if 0.2 < frac < 0.8 else 0.5)
        tail = pts[-1] + np.array([0, 0, -dangle]) + nrm_top * 0.01
        path = np.vstack([pts, tail])
        seglen = np.linalg.norm(np.diff(path, axis=0), axis=1)
        L = np.concatenate([[0], np.cumsum(seglen)])
        sb.add(A.tube(path, 0.003, "BH_Leather", n=3, cap=False), weights=mantle_w)
        n_v = max(2, int(L[-1] / 0.043))
        for j in range(n_v):
            s_ = (j + 0.5) * L[-1] / n_v
            m = min(np.searchsorted(L, s_) - 1, len(path) - 2)
            u = (s_ - L[m]) / max(seglen[m], 1e-6)
            c = path[m] + (path[m + 1] - path[m]) * u
            d = path[m + 1] - path[m]
            r = 0.019 - 0.005 * (s_ / L[-1])
            for prt in vertebra(c, d, nrm_top, r=r, h=r * 0.8):
                sb.add(prt, weights=mantle_w)
    # heavier collar of vertebrae round the neck
    ring = K.ring_frac(TORSO, 1.52, G + 0.03, np.linspace(0.08, 0.92, 11))
    for k in range(len(ring)):
        q = ring[k]
        nxt = ring[min(k + 1, len(ring) - 1)] - ring[max(k - 1, 0)]
        for prt in vertebra(q + (0, 0, 0.012), nxt, (0, 0, 1), r=0.024, h=0.014):
            sb.add(prt, "chest")


# ================================================================================================= head
HEAD_ROWS = [(z, rx * 0.92, ryf * 0.98, ryb, kl, cy) for (z, rx, ryf, ryb, kl, cy) in K.HEAD]


def head(sb):
    V, F = M.tube([(0, 0.01, 1.46), (0, -0.012 + HEAD_DY * 0.5, 1.54), (0, -0.012 + HEAD_DY, 1.62 + HEAD_DZ)],
                  [(0.044, 0.042), (0.038, 0.036), (0.042, 0.04)], n=10, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Skin", name="neck"), weights=K.HEAD_W)
    for sx in (1, -1):      # sinews
        sb.add(A.tube([(sx * 0.02, -0.02, 1.47), (sx * 0.028, -0.03 + HEAD_DY * 0.6, 1.56),
                       (sx * 0.035, -0.012 + HEAD_DY, 1.63 + HEAD_DZ)], 0.009, "BH_Skin", n=5), weights=K.HEAD_W)
    V, F = torso_loft(HEAD_ROWS, n=22, p=2.1, cap0=True, cap1=True)
    hd = M.Part(V, F, "BH_Skin", name="head")

    def hollow(v):     # sunken cheeks + temples
        x, y, z = v
        if y < -0.01 and 1.61 < z < 1.69 and abs(x) > 0.035:
            k = math.sin(math.pi * (z - 1.61) / 0.08) * min(1.0, (abs(x) - 0.035) / 0.03)
            x -= np.sign(x) * 0.012 * k
        return (x, y, z)
    hd.warp(hollow)
    sb.add(hd.move(OFF), "head")
    # face: heavy brow, long thin nose, deep sockets with green eyes, thin grim mouth
    parts = [A.tube([(-0.05, -0.066, 1.716), (0.0, -0.082, 1.722), (0.05, -0.066, 1.716)], (0.013, 0.009),
                    "BH_Skin", n=6, up=(0, -1, 0)),
             A.tube([(0, -0.076, 1.712), (0, -0.09, 1.68), (0, -0.098, 1.652), (0, -0.09, 1.642)],
                    [(0.006, 0.006), (0.008, 0.008), (0.011, 0.009), (0.007, 0.005)], "BH_Skin", n=6, up=(0, -1, 0)),
             A.tube([(-0.024, -0.074, 1.622), (0, -0.078, 1.62), (0.024, -0.074, 1.622)], 0.004, "BH_Shadow", n=4)]
    for sx in (1, -1):
        parts.append(A.ball((sx * 0.029, -0.066, 1.699), 0.016, "BH_Shadow", n=8, rings=5, scale=(1.15, 0.6, 0.8)))
        parts.append(A.ball((sx * 0.029, -0.073, 1.699), 0.0085, "BH_Emissive", n=6, rings=4, scale=(1.3, 0.7, 0.8)))
        parts.append(A.tube([(sx * 0.06, -0.045, 1.66), (sx * 0.05, -0.066, 1.63), (sx * 0.028, -0.078, 1.612)], 0.006,
                            "BH_Skin", n=4))      # gaunt jaw line
        parts.append(A.ball((sx * 0.072, 0.0, 1.69), 0.02, "BH_Skin", n=6, rings=4, scale=(0.35, 0.8, 1.2)))
    for p in parts:
        sb.add(p.move(OFF), "head")
    # a few lank grey strands of hair from under the skull
    for k, x in enumerate((-0.06, -0.03, 0.03, 0.06)):
        top = np.array([x, 0.05, 1.74]) + OFF
        pts = [top, top + (x * 0.3, 0.035, -0.08), top + (x * 0.5, 0.05, -0.18), top + (x * 0.6, 0.06, -0.27 - 0.03 * k)]
        sb.add(A.taper(pts, 0.012, 0.004, "BH_Horn", n=5), weights=K.HEAD_W)


def antler(base, sx, s=1.0):
    """One tall antler (standard space): main beam rising up, out and back, with three forward tines and a crown fork."""
    b = np.asarray(base, float)
    beam = [b, b + (sx * 0.05, 0.02, 0.1), b + (sx * 0.1, 0.05, 0.22), b + (sx * 0.13, 0.06, 0.34),
            b + (sx * 0.13, 0.04, 0.46), b + (sx * 0.1, 0.02, 0.56)]
    beam = [b + (p - b) * s for p in beam]
    parts = [A.taper(beam, 0.02, 0.008, "BH_Horn", n=6)]
    # burr at the base
    parts.append(A.ball(b + (sx * 0.004, 0, 0.012), 0.027, "BH_Horn", n=7, rings=4, scale=(1, 1, 0.6)))
    tines = [(1, (sx * 0.01, -0.1, 0.07), 0.013), (2, (sx * 0.02, -0.1, 0.1), 0.012), (3, (sx * 0.04, -0.07, 0.12), 0.011),
             (4, (-sx * 0.02, -0.05, 0.12), 0.009), (4, (sx * 0.05, 0.04, 0.1), 0.009), (5, (sx * 0.03, -0.02, 0.07), 0.007)]
    for i, d, r in tines:
        p0 = beam[i]
        d = np.asarray(d) * s
        parts.append(A.taper([p0, p0 + d * 0.55 + (0, 0, 0.01), p0 + d], r, 0.003, "BH_Horn", n=5))
    return parts, beam


def headdress(sb):
    """Bleached stag skull worn over the crown (snout jutting over the brow) with tall antlers, moss rags and charms."""
    parts = []
    # cranium cap over the top of the head
    rows = [(1.7, 0.084, 0.088, 0.1, 0.0, -0.004), (1.74, 0.088, 0.095, 0.105, 0.0, -0.004),
            (1.78, 0.084, 0.096, 0.1, 0.0, -0.004), (1.82, 0.07, 0.085, 0.085, 0.0, -0.002),
            (1.85, 0.046, 0.062, 0.06, 0.0, 0.0), (1.866, 0.012, 0.02, 0.02, 0.0, 0.0)]
    V, F = torso_loft(rows, n=18, p=2.2, cap0=False, cap1=True)
    parts.append(M.Part(V, F, "BH_Bone", name="skullcap"))
    # long snout forward over the brow (tapers, slightly down-turned), nasal ridge
    sn = [(0, -0.07, 1.8), (0, -0.14, 1.79), (0, -0.2, 1.77), (0, -0.25, 1.745), (0, -0.275, 1.73)]
    parts.append(A.tube(sn, [(0.056, 0.042), (0.048, 0.036), (0.036, 0.03), (0.026, 0.022), (0.012, 0.01)], "BH_Bone",
                        n=8, up=(0, 0, 1)))
    parts.append(A.tube([(0, -0.1, 1.832), (0, -0.2, 1.8), (0, -0.26, 1.765)], 0.01, "BH_Bone", n=4))
    for sx in (1, -1):
        parts.append(A.ball((sx * 0.062, -0.1, 1.8), 0.026, "BH_Shadow", n=8, rings=5, scale=(0.6, 1.0, 0.8)))
        parts.append(A.ball((sx * 0.068, -0.1, 1.8), 0.01, "BH_Emissive", n=6, rings=4))
        parts.append(A.tube([(sx * 0.02, -0.235, 1.745), (sx * 0.024, -0.265, 1.735)], 0.007, "BH_Shadow", n=4))
        # cheek plates down the sides of the wearer's face
        parts.append(A.tube([(sx * 0.085, -0.03, 1.74), (sx * 0.09, -0.05, 1.68), (sx * 0.075, -0.06, 1.63)],
                            (0.014, 0.022), "BH_Bone", n=5, up=(sx, 0, 0)))
    for p in parts:
        sb.add(p.move(OFF), "head")
    # antlers + what hangs from them
    for sx in (1, -1):
        prts, beam = antler(np.array([sx * 0.055, 0.0, 1.83]) + OFF, sx, s=1.0)
        for p in prts:
            sb.add(p, "head")
        # moss rags and a bone charm on cords from the beam
        for k, (i, ln) in enumerate(((2, 0.16), (3, 0.24))):
            top = beam[i] + np.array([sx * 0.012, 0.01, -0.01])
            sb.add(A.rag_strip(top, (sx * 0.1, 0.1, -1.0), ln, 0.035, "BH_Fur", out=(sx, 0.3, 0), seed=k + sx), "head")
        top = beam[1] + np.array([sx * 0.02, -0.01, 0.0])
        bot = top + np.array([sx * 0.01, 0.0, -0.13])
        sb.add(A.tube([top, bot], 0.003, "BH_Leather", n=4, up=(1, 0, 0)), "head")
        for q in range(3):
            c = bot + np.array([0, 0, -0.012 - 0.02 * q])
            sb.add(A.ball(c, 0.009, "BH_Bone", n=5, rings=3, scale=(1, 1, 1.3)), "head")


# ================================================================================================= staff
def ribcage_staff(s=1.0):
    """Long crooked staff (weapon space: grip at origin, +Z up): weathered grey wood, bent at knots, a claw foot; at
    the top a spine continues into a ribcage cage holding a green soul-flame; small skulls tied on cords below it."""
    parts = []
    # crooked shaft: bends at knots
    knots = [(-1.1, 0.0, 0.0), (-0.72, 0.02, 0.012), (-0.36, -0.018, -0.008), (0.0, 0.0, 0.0), (0.28, 0.024, 0.01),
             (0.5, -0.012, 0.004), (0.66, 0.018, 0.012)]
    pts = []
    for (z, x, y) in knots:
        pts.append((x, y, z))
    fine = []
    for a, b in zip(pts, pts[1:]):
        a, b = np.array(a), np.array(b)
        for t in np.linspace(0, 1, 3, endpoint=False):
            fine.append(a + (b - a) * t)
    fine.append(np.array(pts[-1]))
    rr = [0.02 + 0.003 * math.sin(i * 1.7) for i in range(len(fine))]
    rr[-1] = 0.017
    parts.append(A.tube(fine, rr, "BH_Wood", n=8, up=(0, -1, 0)))
    for (z, x, y) in knots[1:-1]:
        parts.append(A.ball((x, y, z), 0.028, "BH_Wood", n=7, rings=4, scale=(1, 1, 1.3)))
    # side twig stubs
    for z, d in ((-0.55, (0.06, 0.01, 0.08)), (0.4, (-0.05, 0.02, 0.07))):
        p0 = np.array([0.0, 0.0, z])
        parts.append(A.taper([p0, p0 + np.array(d)], 0.012, 0.003, "BH_Wood", n=5))
    parts.append(A.lathe_part([(0, -0.1), (0.024, -0.1), (0.025, 0.0), (0.024, 0.1), (0, 0.1)], "BH_Leather", n=8))
    for z in (-0.08, 0.0, 0.08):
        parts.append(A.lathe_part([(0.0, z - 0.008), (0.027, z - 0.008), (0.027, z + 0.008), (0.0, z + 0.008)],
                                  "BH_Bone", n=8))
    # foot: three bone claws
    for k in range(3):
        a = math.radians(120 * k)
        d = np.array([math.cos(a), math.sin(a), 0.0])
        parts.append(A.taper([(0, 0, -1.07), d * 0.035 + (0, 0, -1.11), d * 0.05 + (0, 0, -1.14)], 0.01, 0.003,
                             "BH_Bone", n=4))
    # spine up the back of the cage (+Y side), vertebrae
    top0 = np.array(pts[-1])
    spine = [top0, top0 + (0, 0.05, 0.08), top0 + (0, 0.07, 0.18), top0 + (0, 0.06, 0.28), top0 + (0, 0.02, 0.36)]
    parts.append(A.tube(spine, 0.012, "BH_Bone", n=6))
    for i in range(1, 9):
        u = i / 9
        k = min(int(u * 4), 3)
        t = u * 4 - k
        c = np.array(spine[k]) + (np.array(spine[k + 1]) - np.array(spine[k])) * t
        parts.append(A.ball(c, 0.019, "BH_Bone", n=6, rings=4, scale=(1, 1, 0.6)))
    # ribs: from the spine round each side toward the front, sloping down (a cage around the flame)
    cz = top0[2] + 0.17
    ctr = np.array([top0[0], 0.0, cz])
    for i in range(5):
        z = cz + 0.11 - 0.055 * i
        rr_ = 0.07 + 0.035 * math.sin(math.pi * (i + 0.5) / 5)
        for sx in (1, -1):
            rib = []
            for a in np.linspace(90, -62, 8):
                r = math.radians(a)
                x = sx * rr_ * math.cos(r)
                y = rr_ * math.sin(r) * 0.95
                rib.append(ctr + np.array([x, y, z - cz - 0.05 * (90 - a) / 152]))
            parts.append(A.taper(rib, 0.009, 0.005, "BH_Bone", n=5, up=(0, 0, 1)))
    # a sternum stub at the bottom front and a skull crowning the spine
    parts.append(A.tube([ctr + (0, -0.095, -0.04), ctr + (0, -0.1, -0.13)], (0.014, 0.008), "BH_Bone", n=5,
                        up=(0, -1, 0)))
    parts += A.skull_charm(np.array(spine[-1]) + (0, -0.02, 0.035), 0.045, "BH_Bone", "BH_Shadow", eyes="BH_Emissive",
                           face=(0, -1, -0.2), n=8)
    # green soul-flame: core + tongues rising through the ribs
    parts.append(A.ball(ctr + (0, 0.005, -0.02), 0.05, "BH_Emissive", n=9, rings=6, scale=(1.0, 0.95, 1.15)))
    for k in range(6):
        a = math.radians(60 * k + 15)
        b = ctr + np.array([0.04 * math.cos(a), 0.04 * math.sin(a), 0.0])
        parts.append(A.taper([b, b + np.array([0.02 * math.cos(a), 0.02 * math.sin(a), 0.07]),
                              ctr + np.array([0.01 * math.cos(a), 0.01 * math.sin(a), 0.14 + 0.02 * (k % 2)])],
                             0.016, 0.002, "BH_Emissive", n=4))
    parts.append(A.lathe_part([(0.0, 0.0), (0.028, 0.04), (0.022, 0.1), (0.008, 0.16), (0.0, 0.2)], "BH_Emissive",
                              n=6).move(ctr + (0.0, 0.0, 0.03)))
    # skulls and bones on cords under the cage
    for k, (a, ln, kind) in enumerate(((30, 0.14, "skull"), (150, 0.2, "skull"), (270, 0.11, "bones"))):
        r = math.radians(a)
        top = ctr + np.array([0.075 * math.cos(r), 0.075 * math.sin(r), -0.12])
        bot = top + np.array([0.01 * math.cos(r), 0.01 * math.sin(r), -ln])
        parts.append(A.tube([top, bot], 0.0035, "BH_Leather", n=4, up=(1, 0, 0)))
        if kind == "skull":
            parts += A.skull_charm(bot + (0, 0, -0.028), 0.03, "BH_Bone", "BH_Shadow", eyes="BH_Emissive",
                                   face=(math.cos(r), math.sin(r), 0), n=7)
        else:
            parts.append(A.tube([bot, bot + (0, 0, -0.06)], 0.006, "BH_Bone", n=5))
            parts.append(A.ball(bot + (0, 0, -0.062), 0.009, "BH_Bone", n=5, rings=3))
    for p in parts:
        p.V = p.V * s
    return parts
