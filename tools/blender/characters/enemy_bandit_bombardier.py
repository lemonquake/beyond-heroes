"""Bandit Bombardier (bandits, artillery; Builder B, bh-010): a stocky, broad bandit sapper (~1.8 m). Quilted ochre
padded shirt under a soot-stained leather apron, faded red bandana with brass goggles pushed up on it, a bushy beard,
thick leather gloves with flared cuffs, a bandolier of round black bombs across the chest and more bombs on the belt,
a big wooden POWDER KEG strapped to the back with a lit fuse (glowing ember tip = BH_Emissive), a heavy short knife in
the right hand and a cudgel hanging at the left hip. Same bandit browns / leathers as the Cutthroat and Marksman,
different silhouette (keg hump, wide body, apron). Uses the Builder-B kit in enemy_bandit_cutthroat (SB = authored in
the standard 1.8 m space, scaled on add)."""
import math
import numpy as np

import bh_mesh as M
from bh_body import torso_loft, front_y, back_y, smoothstep
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K

SCALE = 1.8 / 1.85          # bandana + goggles top out at ~1.85 standard units
PROPS = proportions(SCALE, shoulder_x=0.218 * SCALE, clav_x0=0.045 * SCALE, hip_x=0.112 * SCALE,
                    upper_len=0.275 * SCALE, fore_len=0.255 * SCALE)
PALETTE = "bandit_bombardier"
PALETTE_COLORS = {
    "BH_Leather": ((0.085, 0.05, 0.028), 0.0, 0.68, None, 0.0, 1.0),          # apron, gloves, boots
    "BH_Horn": ((0.21, 0.135, 0.075), 0.0, 0.7, None, 0.0, 1.0),              # lighter straps / pocket / fuse cord
    "BH_Cloth_Primary": ((0.3, 0.06, 0.04), 0.0, 0.9, None, 0.0, 1.0),        # faded bandit red bandana
    "BH_Cloth_Secondary": ((0.25, 0.185, 0.095), 0.0, 0.92, None, 0.0, 1.0),  # quilted ochre padded shirt
    "BH_Fur": ((0.06, 0.055, 0.05), 0.0, 0.92, None, 0.0, 1.0),               # dark trousers
    "BH_Skin": ((0.46, 0.3, 0.21), 0.0, 0.55, None, 0.0, 1.0),
    "BH_Hair": ((0.09, 0.05, 0.03), 0.0, 0.75, None, 0.0, 1.0),               # red-brown beard
    "BH_Shadow": ((0.022, 0.02, 0.018), 0.0, 0.95, None, 0.0, 1.0),           # soot / eye sockets
    "BH_DarkSteel": ((0.03, 0.03, 0.034), 0.6, 0.5, None, 0.0, 1.0),          # black iron bombs, soles
    "BH_Gold": ((0.5, 0.36, 0.14), 1.0, 0.38, None, 0.0, 1.0),                # brass goggles / bomb collars
    "BH_Rust": ((0.24, 0.13, 0.07), 0.5, 0.8, None, 0.0, 1.0),                # keg hoops
    "BH_Wood": ((0.2, 0.12, 0.06), 0.0, 0.7, None, 0.0, 1.0),                 # keg staves, cudgel
    "BH_Bone": ((0.62, 0.56, 0.44), 0.0, 0.8, None, 0.0, 1.0),                # painted powder mark
    "BH_Steel": ((0.5, 0.5, 0.5), 1.0, 0.4, None, 0.0, 1.0),                  # knife blade
    "BH_Bronze": ((0.12, 0.1, 0.07), 0.3, 0.2, None, 0.0, 1.0),               # smoked goggle lenses
    "BH_Emissive": ((1.0, 0.5, 0.12), 0.0, 0.4, (1.0, 0.45, 0.08), 7.0, 1.0),  # fuse ember
}
CLIPS = ["cast_quick", "cast_heavy", "dagger_1", "shield_bash"]


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


# body under the clothes (standard space): wide chest, round belly, thick waist
TORSO = [
    (0.94, 0.168, 0.112, 0.106, 0.00),
    (1.02, 0.162, 0.128, 0.102, 0.02),
    (1.11, 0.168, 0.146, 0.102, 0.04),
    (1.21, 0.178, 0.14, 0.106, 0.06),
    (1.31, 0.192, 0.128, 0.112, 0.06),
    (1.39, 0.198, 0.12, 0.114, 0.04),
    (1.455, 0.172, 0.1, 0.102, 0.00),
    (1.505, 0.11, 0.072, 0.074, 0.00),
    (1.535, 0.072, 0.06, 0.06, 0.00),
]
TW = K.TORSO_W
APRON_G = 0.014


def jitter(part, amp, seed=1):
    rng = np.random.default_rng(seed)
    part.V = part.V + rng.normal(size=part.V.shape) * amp
    return part


def const_w(wfn, c):
    """Rigid prop on a blended region: every vertex gets the weights of the prop's centre."""
    w = wfn(np.asarray([c], float))[0]
    return lambda V: [dict(w)] * len(V)


def front_n(x, z, rows=TORSO):
    """Approximate outward normal of the torso front at (x, z)."""
    e = 0.01
    y0 = front_y(rows, x, z)
    dx = (front_y(rows, x + e, z) - y0) / e
    dz = (front_y(rows, x, z + e) - y0) / e
    return normalize(np.array([dx, -1.0, dz]) * np.array([-1, 1, -1]))


# ================================================================================================= build
def build(body):
    sb = K.SB(body, SCALE)
    # ---- padded shirt torso + quilting ridges (visible at the sides / back around the apron and keg)
    V, F = torso_loft(K.rows_between(TORSO, 0.94, 1.535, n_extra=4), n=28, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="shirt"), weights=TW)
    for z in (1.08, 1.16, 1.24, 1.32, 1.4):
        V, F = K.band(TORSO, z - 0.006, z + 0.006, 0.006, -0.004, n=28)
        sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="quilt"), weights=TW)
    # ---- apron (bib + long skirt, one sheet), straps, soot, pocket
    apron(sb)
    # ---- belt, bombs, pouches, cudgel
    K.belt(sb, TORSO, z=0.985, h=0.05, g=APRON_G + 0.012, mat="BH_Leather", buckle="BH_Gold")
    belt_bombs(sb)
    K.pouch(sb, TORSO, 0.33, 0.96, APRON_G + 0.03, size=(0.08, 0.045, 0.075), mat="BH_Horn")
    K.pouch(sb, TORSO, 0.58, 0.96, APRON_G + 0.03, size=(0.07, 0.04, 0.065), mat="BH_Leather")
    cudgel(sb)
    bandolier(sb)
    # ---- powder keg on the back + harness
    keg(sb)
    # ---- head: face, bushy beard, bandana, goggles, soot smudges
    K.neck_and_head(sb, nose=True)
    beard(sb)
    bandana(sb)
    goggles(sb)
    # ---- arms: padded sleeves, thick gloves with flared cuffs
    for s in ("L", "R"):
        sleeve(sb, s)
        glove(sb, s)
    # ---- legs
    K.pelvis_seat(sb, "BH_Fur", g=0.01)
    K.trousers(sb, "BH_Fur", loose=1.12)
    K.boots(sb, "BH_Leather", "BH_DarkSteel", shaft_top=0.62, wraps="BH_Horn")
    # ---- heavy short knife in the right hand
    K.add_weapon(sb, "R", sapper_knife())


# ------------------------------------------------------------------------------------------------- clothes
def apron(sb):
    g = APRON_G

    Z_TOP, Z_SLIT, Z_HEM = 1.43, 0.84, 0.58

    def surf(x, z, u):
        zz = max(z, 0.96)
        y = front_y(TORSO, x * 0.97, zz) - g
        if z < 0.96:
            y -= 0.03 * ((0.96 - z) / 0.38) ** 1.2
        y += 0.006 * math.sin(u * math.pi * 6.0) * max(0.0, (1.0 - z) / 0.42)   # soft folds
        return y

    def half_w(z):
        if z > 1.0:
            return 0.105 + 0.07 * ((1.43 - z) / 0.43) ** 1.5
        return 0.175 + 0.045 * (1.0 - z) / 0.42

    def upper(u, v):
        z = Z_TOP + (Z_SLIT - 0.02 - Z_TOP) * v
        x = (u - 0.5) * 2 * half_w(z)
        return (x, surf(x, z, u), z)

    skirt = sb.skirt(1.0, 0.76, max_leg=0.75, center_w=0.1)

    def w(V):
        out = []
        for v, a, b in zip(V, TW(V), skirt(V)):
            t = float(smoothstep(0.97, 1.03, v[2]))
            d = {}
            for k, x in a.items():
                d[k] = d.get(k, 0) + x * t
            for k, x in b.items():
                d[k] = d.get(k, 0) + x * (1 - t)
            out.append({k: x for k, x in d.items() if x > 1e-4})
        return out
    sb.add(K.cloth_panel(upper, 11, 12, "BH_Leather", thick=0.01), weights=w)
    # lower apron split up the middle (a slit from the hem to the thighs) so each half follows its own leg
    def leg_w(V):
        out = []
        for v in V:
            t = float(smoothstep(0.99, 0.74, v[2]))
            side = "thigh.L" if v[0] > 0 else "thigh.R"
            out.append({k: x for k, x in (("hips", 1 - t), (side, t)) if x > 1e-4})
        return out
    for sx in (1, -1):
        def lower(u, v, sx=sx):
            z = Z_SLIT + 0.01 + (Z_HEM - Z_SLIT - 0.01) * v
            hw = half_w(z)
            x = sx * (0.012 + (hw - 0.012) * u)
            uu = 0.5 + 0.5 * sx * u
            zz = z - (0.012 * math.sin(uu * 17.0) ** 2 if v > 0.97 else 0.0)
            return (x, surf(x, z, uu) - 0.002, zz)
        pnl = K.cloth_panel(lower, 6, 6, "BH_Leather", thick=0.01, flip=sx < 0)
        sb.add(pnl, weights=leg_w)
        # a pocket on each half
        zp = 0.74
        xp = sx * 0.095
        yp = surf(xp, zp, 0.5 + 0.5 * sx * 0.5) - 0.012
        V, F = M.box(0.1, 0.012, 0.09, center=(xp, yp, zp))
        sb.add(M.bevel(M.Part(V, F, "BH_Horn", name="pocket"), 0.004, 1), weights=const_w(leg_w, (xp, yp, zp)))
    # neck strap: from the bib corners up round the back of the neck
    for sx in (1, -1):
        pts, ups = [], []
        for t in np.linspace(0, 1, 7):
            a = math.pi * t
            x = sx * (0.1 - 0.03 * math.sin(a))
            y = -0.1 * math.cos(a) + 0.01
            z = 1.43 + 0.1 * math.sin(a) ** 0.7
            pts.append((x, y if t > 0 else front_y(TORSO, 0.1, 1.43) - g, z))
            ups.append((0, -math.cos(a), math.sin(a)))
        sb.add(K.strip(pts, 0.028, 0.008, "BH_Leather", ups=ups), weights=TW)
    # waist ties round the back
    V, F = K.band(TORSO, 1.03, 1.055, g + 0.006, g - 0.004, n=28)
    sb.add(M.Part(V, F, "BH_Leather", name="apron_tie"), "hips")
    V, F = M.sphere(0.02, 8, 5, center=(0.0, back_y(TORSO, 0, 1.045) + g + 0.012, 1.045), scale=(1.4, 0.8, 1.0))
    sb.add(M.Part(V, F, "BH_Leather", name="tie_knot"), "hips")
    for sx in (1, -1):
        pts = [(0.01 * sx, 0.125, 1.04), (0.03 * sx, 0.14, 0.97), (0.035 * sx, 0.15, 0.9)]
        sb.add(K.strip(pts, 0.024, 0.006, "BH_Leather", ups=[(0, 1, 0)] * 3), "hips")
    # soot stains (flat dark splotches on the apron front)
    rng = np.random.default_rng(21)
    for (x, z, r) in ((0.06, 1.3, 0.05), (-0.04, 1.18, 0.04), (0.09, 1.08, 0.035), (-0.1, 0.76, 0.06),
                      (0.07, 0.68, 0.05), (-0.02, 1.37, 0.03), (0.12, 0.8, 0.04)):
        u = x / 0.4 + 0.5
        # sample the apron surface
        if z > 1.0:
            y = front_y(TORSO, x * 0.97, z) - g - 0.003
            wfn = TW
        else:
            y = front_y(TORSO, x * 0.97, 0.96) - g - 0.03 * max(0.0, (0.96 - z) / 0.38) ** 1.2 - 0.005
            wfn = const_w(leg_w if z < Z_SLIT else skirt, (x, y, z))
        V, F = M.sphere(r, 10, 4, center=(0, 0, 0), scale=(1.0 + 0.3 * rng.random(), 0.04, 0.7 + 0.3 * rng.random()))
        p = M.Part(V, F, "BH_Shadow", name="soot").rot(Ry(rng.random() * 180)).move((x, y, z))
        jitter(p, 0.0015, seed=int(rng.integers(1000)))
        sb.add(p, weights=wfn)


def sleeve(sb, s):
    """Padded sleeve with quilted rings, ending under the glove cuff."""
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    sx = 1 if s == "L" else -1
    pts = [sh + (-0.05 * sx, 0, 0.03), sh + (0, 0, 0.005), sh + (el - sh) * 0.45, el, el + (wr - el) * 0.5,
           el + (wr - el) * 0.75]
    prof = [(0.06, 0.066), (0.074, 0.076), (0.068, 0.07), (0.06, 0.062), (0.054, 0.056), (0.05, 0.052)]
    V, F = M.tube(pts, prof, n=14, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="sleeve"),
           weights=sb.seg(["chest", "shoulder." + s, ua, fa, ha], power=9))
    for u, r in ((0.25, 0.074), (0.5, 0.071), (0.75, 0.067)):
        c = sh + (el - sh) * u
        d = normalize(el - sh)
        V, F = M.tube([c - d * 0.006, c + d * 0.006], [(r, r + 0.002)] * 2, n=12, up=(0, -1, 0))
        sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="quilt_ring"), ua)
    # shoulder seam roll (makes the shoulders read broad from above)
    c = sh + (-0.01 * sx, 0.0, 0.035)
    V, F = M.sphere(0.07, 12, 6, center=c, scale=(1.0, 1.1, 0.75))
    sb.add(M.Part(V, F, "BH_Cloth_Secondary", name="shoulder_pad"),
           weights=lambda V, s=s: [{"shoulder." + s: 0.45, "upper_arm." + s: 0.55}] * len(V))


def glove(sb, s):
    fa, ha = "forearm." + s, "hand." + s
    a, b = sb.head(fa), sb.head(ha)
    d = normalize(b - a)
    K.add_fist(sb, s, "BH_Leather", "BH_Leather", gauntlet=True, scale=1.18)
    # flared gauntlet cuff up the forearm
    V, F = M.tube([a + (b - a) * 0.45, a + (b - a) * 0.75, b + d * 0.02],
                  [(0.07, 0.072), (0.06, 0.062), (0.047, 0.05)], n=14, up=(0, -1, 0), cap0=False)
    sb.add(M.solidify(M.Part(V, F, "BH_Leather", name="cuff"), 0.008, offset=-1.0), fa)
    c = a + (b - a) * 0.72
    V, F = M.tube([c - d * 0.009, c + d * 0.009], [(0.066, 0.068)] * 2, n=14, up=(0, -1, 0))
    sb.add(M.Part(V, F, "BH_Horn", name="cuff_strap"), fa)
    # soot on the back of the glove
    A = sb.axes("weapon." + s)
    o = sb.head("weapon." + s)
    xs = 1.0 if s == "R" else -1.0
    q = o + A @ (np.array([-0.02 * xs, 0.0, 0.058]) * 1.18)
    V, F = M.sphere(0.03, 8, 4, center=(0, 0, 0), scale=(1.3, 1.0, 0.1))
    p = M.Part(V, F, "BH_Shadow", name="glove_soot")
    from bh_body import M_align_z
    p.rot(M_align_z(A[:, 2], A[:, 0])).move(q)
    sb.add(p, ha)


def beard(sb):
    """Bushy full beard: a closed volume hugging the jaw (front arc of the head rows grown out), filling in under
    the chin and ending in a rounded point on the upper chest; moustache and brows on top."""
    rings = []
    fr = np.linspace(-0.3, 0.3, 15)
    for z, g, fwd, sc in ((1.652, 0.004, 0.0, 1.0), (1.63, 0.012, 0.004, 1.0), (1.605, 0.018, 0.012, 0.98),
                          (1.58, 0.02, 0.026, 0.9), (1.555, 0.016, 0.04, 0.72), (1.53, 0.01, 0.05, 0.45),
                          (1.515, 0.004, 0.052, 0.2)):
        front = K.ring_frac(K.HEAD, max(z, 1.6), g, fr, p=2.1)
        front[:, 2] = z
        front[:, 0] *= sc
        front[:, 1] = (front[:, 1] - 0.0) * (0.9 + 0.1 * sc) - fwd * 0.4 - (0.02 if z < 1.6 else 0.0)
        # close the ring behind the jaw line (inside the head / neck)
        back = np.array([(x * 0.55, 0.01 + 0.02 * (1 - abs(x) / 0.12), z) for x in front[::-1, 0][1:-1]])
        rings.append(np.vstack([front, back]))
    V, F = M.loft(rings[::-1], cap0=True, cap1=True)
    bd = M.Part(V, F, "BH_Hair", name="beard")
    bd.flip()
    jitter(bd, 0.0018, seed=4)
    sb.add(M.recalc_normals(bd), "head")
    # moustache
    for sx in (1, -1):
        pts = [(sx * 0.004, -0.092, 1.648), (sx * 0.03, -0.086, 1.642), (sx * 0.05, -0.074, 1.625)]
        sb.add(K.rtube(pts, [0.011, 0.01, 0.006], "BH_Hair", n=6), "head")
    # bushy brows
    for sx in (1, -1):
        pts = [(sx * 0.012, -0.08, 1.726), (sx * 0.035, -0.078, 1.73), (sx * 0.056, -0.066, 1.724)]
        sb.add(K.rtube(pts, [0.007, 0.008, 0.005], "BH_Hair", n=5), "head")


def bandana(sb):
    """Faded red bandana tied over the skull, knot + tails at the back."""
    rows = K.grow_rows(K.HEAD, 0.011)
    nu = 26
    rings = []
    for v in np.linspace(0, 1, 7):
        ring = []
        for i in range(nu):
            f = i / nu
            back = 0.5 - 0.5 * math.cos(2 * math.pi * f)
            z0 = 1.738 + (1.655 - 1.738) * back
            z = z0 + (1.815 - z0) * v ** 0.85
            q = K.ring_frac(rows, min(z, 1.818), 0.0, [f], p=2.1)[0]
            q[2] = z
            ring.append(q)
        rings.append(np.array(ring))
    top = rings[-1]
    cen = top.mean(0)
    for k, (dz, sc) in enumerate(((0.006, 0.8), (0.011, 0.5))):
        r = cen + (top - cen) * np.array([sc, sc, 0.0])
        r[:, 2] = top[:, 2] + dz
        rings.append(r)
    V, F = M.loft(rings, cap0=False, cap1=True)
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="bandana"), "head")
    V, F = M.sphere(0.024, 8, 5, center=(0, 0.103, 1.675), scale=(1.3, 0.8, 1.0))
    sb.add(M.Part(V, F, "BH_Cloth_Primary", name="knot"), "head")
    for sx, ln in ((1, 0.13), (-1, 0.1)):
        pts = [(0.012 * sx, 0.112, 1.67), (0.035 * sx, 0.13, 1.62), (0.05 * sx, 0.14, 1.67 - ln)]
        sb.add(K.strip(pts, 0.036, 0.006, "BH_Cloth_Primary", ups=[(0, 1, 0)] * 3), "head")


def goggles(sb):
    """Brass goggles pushed up on the forehead (lenses tilted up), strap round the head."""
    rows = K.grow_rows(K.HEAD, 0.014)
    z = 1.772
    ring = K.ring_frac(rows, z, 0.0, np.linspace(0, 1, 29)[:-1], p=2.1)
    ring = np.vstack([ring, ring[:1]])
    V, F = M.tube(ring, [(0.004, 0.009)] * len(ring), n=4, up=(0, 0, 1), cap0=False, cap1=False)
    sb.add(M.Part(V, F, "BH_Leather", name="goggle_strap"), "head")
    for sx in (1, -1):
        x = sx * 0.036
        q = K.ring_frac(rows, z, 0.0, [(-math.atan2(x, 0.06) / (2 * math.pi)) % 1.0], p=2.1)[0]
        axis = normalize(np.array([sx * 0.25, -1.0, 0.75]))
        V, F = M.tube([q - axis * 0.002, q + axis * 0.024], [(0.026, 0.026), (0.024, 0.024)], n=12,
                      up=(0, 0, 1))
        sb.add(M.Part(V, F, "BH_Gold", name="goggle_rim"), "head")
        V, F = M.sphere(0.021, 10, 4, center=q + axis * 0.024, scale=(1, 1, 0.35))
        from bh_body import M_align_z
        lens = M.Part(V, F, "BH_Bronze", name="lens")
        lens.V = (lens.V - (q + axis * 0.024)) @ M_align_z(axis).T + (q + axis * 0.024)
        sb.add(lens, "head")
    # bridge
    q0 = K.ring_frac(rows, z, 0.004, [0.0], p=2.1)[0]
    V, F = M.box(0.02, 0.01, 0.01, center=q0 + (0, -0.006, 0))
    sb.add(M.Part(V, F, "BH_Gold", name="goggle_bridge"), "head")


# ------------------------------------------------------------------------------------------------- props
def bomb(center, r=0.046, fuse_dir=(0, 0, 1)):
    """Round black iron bomb: sphere + brass collar + short cord fuse."""
    c = np.asarray(center, float)
    d = normalize(np.asarray(fuse_dir, float))
    parts = [jitter(M.Part(*M.sphere(r, 12, 7, center=c), "BH_DarkSteel", name="bomb"), 0.0008, seed=3)]
    V, F = M.tube([c + d * (r * 0.8), c + d * (r * 1.12)], [(r * 0.34, r * 0.34)] * 2, n=8,
                  up=(1, 0, 0) if abs(d[0]) < 0.9 else (0, 1, 0))
    parts.append(M.Part(V, F, "BH_Gold", name="collar"))
    side = normalize(np.cross(d, (1, 0, 0) if abs(d[0]) < 0.9 else (0, 1, 0)))
    pts = [c + d * r * 1.1, c + d * r * 1.45 + side * r * 0.12, c + d * r * 1.7 + side * r * 0.35]
    parts.append(K.rtube(pts, [r * 0.12, r * 0.1, r * 0.08], "BH_Horn", n=5))
    return parts


def bandolier(sb):
    """Leather bandolier (left shoulder -> right hip) over the apron, with six bombs in loops."""
    g = APRON_G + 0.018
    front, ups = [], []
    for t in np.linspace(0, 1, 11):
        x = 0.14 - 0.3 * t
        z = 1.47 - 0.45 * t
        front.append((x, front_y(TORSO, x, z) - g, z))
        ups.append(tuple(front_n(x, z)))
    sb.add(K.strip(front, 0.055, 0.012, "BH_Horn", ups=ups), weights=TW)
    back = []
    for t in np.linspace(0, 1, 8):
        x = 0.14 - 0.3 * t
        z = 1.47 - 0.45 * t
        back.append((x, back_y(TORSO, x, z) + g, z))
    sb.add(K.strip(back, 0.055, 0.012, "BH_Horn", ups=[(0, 1, 0)] * 8), weights=TW)
    pts, ups = [], []
    for t in np.linspace(0, 1, 7):
        a = math.pi * (0.5 - t) * 0.95
        pts.append((0.14, -0.118 * math.sin(a) + 0.004, 1.47 + 0.055 * math.cos(a)))
        ups.append((0, -math.sin(a), math.cos(a)))
    sb.add(K.strip(pts, 0.055, 0.012, "BH_Horn", ups=ups), "chest")
    fr = np.asarray(front)
    for k, t in enumerate((0.1, 0.25, 0.4, 0.55, 0.7, 0.85)):
        i = t * (len(fr) - 1)
        i0 = int(i)
        c = fr[i0] * (1 - (i - i0)) + fr[min(i0 + 1, len(fr) - 1)] * (i - i0)
        n = front_n(c[0], c[2])
        r = 0.042
        bc = c + n * (r + 0.004)
        for prt in bomb(bc, r, fuse_dir=(0.35, -0.2, 1.0)):
            sb.add(prt, weights=const_w(TW, bc))
        # loop strap over the bomb
        V, F = M.tube([bc + (0.05, 0, -0.01), bc + (0, 0, -0.012) + n * (r * 0.95), bc + (-0.05, 0, -0.01)],
                      [(0.009, 0.004)] * 3, n=5, up=(0, 0, 1))
        sb.add(M.Part(V, F, "BH_Leather", name="bomb_loop").move(-n * 0.004), weights=const_w(TW, bc))
    # brass buckle on the strap
    c = fr[2]
    V, F = M.box(0.05, 0.012, 0.04, center=c + front_n(c[0], c[2]) * 0.008)
    sb.add(M.Part(V, F, "BH_Gold", name="bandolier_buckle").rot(Ry(-35), center=c), weights=const_w(TW, c))


def belt_bombs(sb):
    """Three bombs hanging from the belt on short cords (right front, right side, left back) + hooks."""
    hang = sb.skirt(1.0, 0.7, max_leg=0.25, center_w=0.06)
    for frac, dz in ((0.87, 0.0), (0.76, -0.01), (0.4, -0.005)):
        p, ang = K.on_ring(TORSO, 0.965, APRON_G + 0.06, frac)
        c = np.asarray(p) + np.array([0, 0, -0.06 + dz])
        parts = bomb(c, 0.048, fuse_dir=(0, 0, 1))
        top = np.asarray(p) + np.array([0, 0, 0.005])
        parts.append(K.rtube([top, c + (0, 0, 0.07)], 0.006, "BH_Horn", n=5))
        V, F = M.tube([top + (0, 0, -0.008), top + (0, 0, 0.018)], [(0.013, 0.013)] * 2, n=8, up=(0, -1, 0))
        parts.append(M.Part(V, F, "BH_Gold", name="hook"))
        for prt in parts:
            sb.add(prt, weights=const_w(hang, c))


def cudgel(sb):
    """Short wooden cudgel with an iron band, hanging through a belt loop on the left hip."""
    p, ang = K.on_ring(TORSO, 0.97, APRON_G + 0.05, 0.215)
    p = np.asarray(p)
    d = normalize(np.array([0.12, 0.25, -1.0]))
    parts = []
    prof = [(0.0, -0.12), (0.022, -0.12), (0.024, -0.1), (0.02, 0.0), (0.026, 0.12), (0.036, 0.22),
            (0.04, 0.3), (0.034, 0.34), (0.0, 0.345)]
    V, F = M.lathe(prof, 10)
    club = M.Part(V, F, "BH_Wood", name="cudgel")
    for z in (0.26,):
        V2, F2 = M.lathe([(0, z - 0.02), (0.043, z - 0.02), (0.045, z), (0.043, z + 0.02), (0, z + 0.02)], 10)
        parts.append(M.Part(V2, F2, "BH_Rust", name="cudgel_band"))
    V2, F2 = M.lathe([(0, -0.1), (0.025, -0.1), (0.025, -0.04), (0, -0.04)], 8)
    parts.append(M.Part(V2, F2, "BH_Leather", name="cudgel_grip"))
    parts.append(club)
    from bh_body import M_align_z
    R = M_align_z(-d)          # +Z of the club (head) points down
    loop_c = p + np.array([0, 0, -0.02])
    for prt in parts:
        prt.V = prt.V @ R.T + loop_c + (-d) * -0.06
        sb.add(prt, weights=const_w(sb.skirt(1.0, 0.7, max_leg=0.35, center_w=0.06), loop_c - d * 0.1))
    V, F = M.tube([loop_c + (0, 0, 0.03), loop_c + (0, 0, -0.03)], [(0.034, 0.034)] * 2, n=10, up=(0, -1, 0),
                  cap0=False, cap1=False)
    sb.add(M.solidify(M.Part(V, F, "BH_Leather", name="cudgel_loop"), 0.006), "hips")


def keg(sb):
    """Powder keg strapped upright on the back: staved barrel, three rust-iron hoops, a lid with a painted X and a
    bung, a lit fuse curling up behind the right shoulder (ember tip = BH_Emissive), shoulder harness."""
    zc, H, R = 1.235, 0.52, 0.19
    yc = back_y(TORSO, 0, zc) + R * 0.95 + 0.012
    c = np.array([0.015, yc, zc])
    tilt = Rx(-6) @ Ry(-5)
    parts = []
    prof = []
    for i in range(11):
        t = i / 10
        prof.append((R * (0.86 + 0.14 * math.sin(math.pi * t)), -H / 2 + H * t))
    prof = [(0.0, -H / 2)] + prof + [(R * 0.8, H / 2), (R * 0.8, H / 2 - 0.02), (0.0, H / 2 - 0.02)]
    V, F = M.lathe(prof, 28)
    barrel = M.Part(V, F, "BH_Wood", name="keg")

    def staves(v):
        a = math.atan2(v[1], v[0])
        k = 1.0 - 0.025 * (0.5 + 0.5 * math.cos(14 * a)) ** 8
        return (v[0] * k, v[1] * k, v[2])
    barrel.warp(staves)
    parts.append(barrel)
    for zt in (-0.19, 0.19, 0.24):
        rr = R * (0.86 + 0.14 * math.sin(math.pi * (zt + H / 2) / H)) + 0.006
        V, F = M.lathe([(0, zt - 0.018), (rr, zt - 0.018), (rr + 0.006, zt), (rr, zt + 0.018), (0, zt + 0.018)], 28)
        parts.append(M.Part(V, F, "BH_Rust", name="hoop"))
    # painted X on the back of the keg and on the lid (reads from the high camera)
    for a in (35, -35):
        V, F = M.box(0.045, 0.012, 0.3)
        parts.append(M.Part(V, F, "BH_Bone", name="mark").rot(Ry(a)).move((0, R * 0.995, 0.0)))
        V, F = M.box(0.028, 0.2, 0.006)
        parts.append(M.Part(V, F, "BH_Bone", name="lid_mark").rot(Rz(a + 90)).move((0, 0, H / 2 - 0.016)))
    V, F = M.lathe([(0, H / 2 - 0.02), (0.03, H / 2 - 0.02), (0.03, H / 2 + 0.02), (0, H / 2 + 0.02)], 10)
    bung = M.Part(V, F, "BH_Wood", name="bung").move((0.07, -0.05, 0))
    parts.append(bung)
    # fuse: from the bung up behind the right shoulder
    b0 = np.array([0.07, -0.05, H / 2 + 0.02])
    fpts = [b0, b0 + (0.0, 0.0, 0.06), b0 + (-0.04, 0.03, 0.13), b0 + (-0.12, 0.06, 0.17), b0 + (-0.18, 0.1, 0.2)]
    parts.append(K.rtube(fpts, [0.011, 0.01, 0.009, 0.008, 0.007], "BH_Horn", n=6))
    tip = fpts[-1]
    parts.append(M.Part(*M.sphere(0.017, 10, 6, center=tip + (-0.01, 0.005, 0.005)), "BH_Emissive", name="ember"))
    rng = np.random.default_rng(9)
    for k in range(5):
        dd = normalize(rng.normal(size=3) + np.array([-0.4, 0.2, 0.8]))
        parts.append(K.rtube([tip + dd * 0.012, tip + dd * (0.03 + 0.015 * rng.random())], [0.0035, 0.0005], "BH_Emissive", n=4))
    for prt in parts:
        prt.V = prt.V @ tilt.T + c
        sb.add(prt, "chest")
    # harness: two straps from the keg top over the shoulders to the front of the chest, a strap round the keg
    for sx in (1, -1):
        pts = [c + tilt @ np.array([sx * 0.09, -0.12, 0.2]), (sx * 0.12, 0.08, 1.505), (sx * 0.13, -0.02, 1.52),
               (sx * 0.135, -0.11, 1.47), (sx * 0.15, front_y(TORSO, 0.15, 1.36) - 0.02, 1.36),
               (sx * 0.17, front_y(TORSO, 0.17, 1.26) - 0.012, 1.26)]
        ups = [normalize(np.asarray(q) - np.array([0.0, 0.0, 1.3])) for q in pts]
        sb.add(K.strip(pts, 0.044, 0.012, "BH_Leather", ups=ups), weights=TW)
        V, F = M.box(0.034, 0.012, 0.03, center=pts[4] + np.array([0, -0.01, 0]))
        sb.add(M.Part(V, F, "BH_Gold", name="harness_buckle"), "chest")
    ring = []
    for a in np.linspace(0, 2 * math.pi, 25):
        ring.append(c + tilt @ np.array([(R + 0.012) * math.cos(a), (R + 0.012) * math.sin(a), -0.05]))
    V, F = M.tube(ring, [(0.006, 0.02)] * len(ring), n=6, up=(0, 0, 1), cap0=False, cap1=False)
    sb.add(M.Part(V, F, "BH_Leather", name="keg_strap"), "chest")


def sapper_knife():
    """Heavy straight single-edged knife (weapon-builder space: grip at origin, +Z blade)."""
    parts = []
    rings = []
    L = 0.24
    for i in range(9):
        u = i / 8
        z = 0.045 + L * u
        w = 0.05 * (1 - u ** 4) + 0.003
        t = 0.007 * (1 - 0.6 * u) + 0.001
        edge = 0.5 * w
        spine = -0.5 * w + 0.02 * u ** 3
        rings.append(np.array([(edge, 0, z), (edge * 0.5, t * 0.6, z), (spine, t, z), (spine, -t, z),
                               (edge * 0.5, -t * 0.6, z)]))
    V, F = M.loft(rings)
    parts.append(M.Part(V, F, "BH_Steel", name="blade"))
    V, F = M.box(0.075, 0.03, 0.014, center=(0, 0, 0.038))
    parts.append(M.bevel(M.Part(V, F, "BH_Gold", name="guard"), 0.003, 1))
    V, F = M.lathe([(0, -0.07), (0.017, -0.07), (0.015, 0.0), (0.016, 0.03), (0, 0.03)], 8)
    parts.append(M.Part(V, F, "BH_Wood", name="grip"))
    V, F = M.sphere(0.02, 8, 5, center=(0, 0, -0.078))
    parts.append(M.Part(V, F, "BH_Gold", name="pommel"))
    return parts
