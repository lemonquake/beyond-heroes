"""bh-024: worn leggings (slot `leggings`) and the plain legwear the game adds itself (`_breeches`, `_under_legs`).

Each piece mirrors its item model's spec (tools/blender/items/item_gear.py GEAR `legs`, depth_specs.json) so the worn
leggings are recognisably the thing in the icon: same kind, same palette keys, same trims.

Layers: the cloth is cut from the legs (hero_wear_torso.cloth), tucked in at the waist (3.5 mm) so every shirt and coat
closes over it, full thickness (6-9 mm) below the body garments' hems and tight again below the calf (<= 6.5 mm) so boot
shafts close over it. Everything that stands further out is sorted into mesh groups the game hides when something is
worn over it (HeroWear.plan):

  wear          the cloth, mail, laces, seams, stripes and gems on it              always
  wear_waist    belt, buckle, sash, hanging panel, tassets                          only when no shirt or coat is worn
  wear_hip      thigh plates (cuisses), leather guards, pouches, sheaths, feathers  not under skirts that reach below 0.80
  wear_knee     knee cops and pads                                                  not under skirts that reach below 0.45
  wear_ankle_L / wear_ankle_R   ankle cuffs and the wraps below the calf            not in a boot on that side
"""
import json
import math
import os

import numpy as np

import item_gear as G
import hero_wear_kit as WK
import hero_wear_torso as T
import hero_wear_ends as E
from hero_wear_kit import K, M, item, pal, shell, attach

TINT = "raw:BH_Cloth_Primary"
TOP = 1.095          # the waistband: over the underwear, just below the navel
HEM = 0.105          # the ankle
TUCK = 0.0035        # offset under the body garments
LOW = 0.43           # below this a boot shaft may close over the leggings (the tallest reach 0.42)
KNEE_Z = 0.51
HIDE = {"z": [0.13, 1.065]}

with open(os.path.join(WK.ITEMS, "depth_specs.json"), encoding="utf-8") as _f:
    DEPTH = {k: v[1] for k, v in json.load(_f).items() if v[0] == "legs"}


def spec_of(id):
    s = dict(DEPTH[id]) if id in DEPTH else dict(G.GEAR[id][1])
    if s.get("kind") == "plate" and "plate" not in s:        # as item_gear.legs: depth specs name the plate colour
        s["plate"], s["mat"] = s.get("mat", "iron"), "darkleather"
    return s


# ---- the left leg's axis ------------------------------------------------------------------------------------------------
_AXIS = None


def axis():
    """(z samples, centre x, centre y) of the left leg's convex sections, for fields on the body's vertices."""
    global _AXIS
    if _AXIS is None:
        zs = np.linspace(0.08, 1.04, 49)
        cs = np.array([T.LEG.hull(z)[1] for z in zs])
        _AXIS = (zs, cs[:, 0], cs[:, 1])
    return _AXIS


def around(V):
    """-> (angle in degrees around the left leg — 0 outside (+X), 90 back, 270 front — and distance from its axis);
    the right leg is mirrored onto the left."""
    zs, cx, cy = axis()
    x = np.abs(V[:, 0])
    dx = x - np.interp(V[:, 2], zs, cx)
    dy = V[:, 1] - np.interp(V[:, 2], zs, cy)
    return np.degrees(np.arctan2(dy, dx)) % 360.0, np.hypot(dx, dy)


def leg_patch(z0, z1, a0, a1, feather=4.0):
    """A field over both legs: heights z0..z1, angles a0..a1 around each leg (front = 270)."""
    def f(V):
        ang, _ = around(V)
        mid = (a0 + a1) / 2.0
        half = (a1 - a0) / 2.0
        d = np.abs((ang - mid + 180.0) % 360.0 - 180.0)
        _, dist = around(V)
        return np.minimum.reduce([V[:, 2] - z0, z1 - V[:, 2], (half - d) / 1000.0 * feather, np.abs(V[:, 0]) - 0.035,
                                  0.16 - dist])
    return f


def ring_pts(z, grow, src=None, n=20, a0=0.0, a1=360.0, lim=None):
    return T.LEG.ring(z, n, grow, src, a0, a1, lim)


# ---- cloth --------------------------------------------------------------------------------------------------------------
def offset_fn(base, loose=0.0):
    """Tucked in at the waist, `base` below the body garments' hems, fuller over thigh and knee for a loose cut,
    no more than 6.5 mm below the calf so boots close over it."""
    def f(V):
        z = V[:, 2]
        waist = WK.step(0.70, 0.86, z)
        out = base * (1.0 - waist) + TUCK * waist
        out = out + np.minimum(loose * 0.045, 0.012) * WK.step(0.38, 0.55, z) * (1.0 - WK.step(0.60, 0.84, z))
        low = 1.0 - WK.step(0.30, 0.40, z)
        return out * (1.0 - low) + np.minimum(out, 0.0065) * low
    return f


BASE = {"plate": 0.0068, "mail": 0.0085, "trousers": 0.0068, "silk": 0.0062, "hide": 0.0072, "chaps": 0.0072, "wrap": 0.0058}


def cloth_legs(s, z0=HEM, z1=TOP):
    kind = s.get("kind", "trousers")
    mat = WK.mail("mail_" + s.get("mat", "iron"), "a8acb4") if kind == "mail" else pal(s.get("mat", "wool"))
    return T.cloth(T.region(legs=(z0, z1)), offset_fn(BASE.get(kind, 0.0068), s.get("loose", 0.0)), mat, "legs",
                   relax=4 if kind in ("mail", "plate") else 3)


def split_low(parts):
    """-> (upper, left ankle, right ankle): authored parts sorted by where they are (x sign, height)."""
    up, al, ar = [], [], []
    for p in parts:
        c = p.V.mean(0)
        if c[2] < LOW:
            (al if c[0] > 0 else ar).append(p)
        else:
            up.append(p)
    return up, al, ar


# ---- authored parts -----------------------------------------------------------------------------------------------------
def hoop(z, mat, src, grow=0.002, width=0.014, n=18, lim=None):
    return T.hoop(z, width, mat, src, grow, n, T.LEG, lim=lim)


def tilted_cord(z, amp, mat, src, grow=0.003, r=0.0038, n=20, phase=0.0):
    """A strap wound round the left leg, rising `amp` on the outside and falling on the inside (a wrap)."""
    P = ring_pts(z, grow, src, n)
    a = np.radians(np.linspace(0, 360, n, endpoint=False)) + phase
    P = P.copy()
    P[:, 2] += amp * np.cos(a)
    return T.cord(P, r, mat, sides=4, closed=True)


def seam_cord(z0, z1, angle, mat, src, grow=0.002, r=0.0026, steps=12, zig=0.0):
    """A cord down the left leg at `angle` (0 = the outer seam) — laces zig-zag across it by `zig` degrees."""
    P = []
    for i in range(steps + 1):
        z = z0 + (z1 - z0) * i / steps
        a = angle + (zig if i % 2 else -zig)
        P.append(ring_pts(z, grow, src, 3, a, a + 0.001)[0])
    return T.cord(P, r, mat, sides=4)


def on_surface(z, angle, grow, src=None):
    return ring_pts(z, grow, src, 3, angle, angle + 0.001)[0]


def plate_bands(s, S):
    """Cuisses: three overlapping lames down the front and outside of each thigh, each hemmed with the trim."""
    plate, trim = WK.plate(s.get("plate", "iron")), pal(s.get("trim", "iron"))
    out, left = [], []
    bands = [(0.80, 0.905, 0.0205), (0.70, 0.815, 0.0185), (0.59, 0.715, 0.0165)]
    for z0, z1, off in bands:
        raw = shell(leg_patch(z0, z1, 195.0, 345.0), off, plate, "cuisse", rim=False, relax=10)
        out.append(shell(leg_patch(z0, z1, 195.0, 345.0), off, plate, "cuisse", relax=10))
        loops = [lp for lp in E.border_loops(raw) if raw.V[lp][:, 0].mean() > 0]
        if loops:
            lp = max(loops, key=len)
            left.append(E.cord_on(raw, lp, 0.0036, trim, n=30, name="lame_trim"))
    if s.get("rivets"):
        pts = []
        for z in (0.61, 0.72, 0.83):
            for a in (215.0, 250.0, 290.0, 325.0):
                pts.append(on_surface(z, a, 0.021 + (0.002 if z > 0.8 else 0.0)))
        left += attach(T.studs(pts, lambda p: (0.105, 0.0, p[2]), 0.0048, trim), bones=["thigh.L"], k=6)
    if s.get("fluted"):
        for a in (250.0, 272.0, 294.0):
            P = [on_surface(z, a, 0.0235 - 0.0035 * (0.9 - z) / 0.3) for z in np.linspace(0.61, 0.89, 7)]
            left += attach(T.cord(P, 0.0032, trim, sides=4), bones=["thigh.L"], k=6)
    return out + WK.both(left)


def knee_cop(s, pad=False):
    """A knee cop (or a leather pad) on the left knee, half on the thigh and half on the shin, with a fan outside."""
    mat = pal(s.get("knee_pad")) if pad else WK.plate(s.get("knee", s.get("plate", "iron")))
    trim = pal(s.get("trim", "iron"))
    H, c = T.LEG.hull(KNEE_Z)
    front = float(H[:, 1].min())
    cx = float(c[0])
    parts = [K.sphere(0.05 if pad else 0.056, (cx, front + 0.012, KNEE_Z + 0.01), mat, 16, 8,
                      scale=(1.02, 0.5 if pad else 0.46, 1.0 if pad else 1.12))]
    if not pad:
        fan = [(0.0, 0.035), (0.04, 0.028), (0.052, -0.02), (0.0, -0.04)]
        parts.append(K.slab(fan, 0.006, mat, axis="x").move((cx + 0.05, front + 0.03, KNEE_Z + 0.005)))
        parts.append(K.sphere(0.0085, (cx, front - 0.026, KNEE_Z + 0.01), trim, 6, 4))
        if s.get("wings"):
            o = [(0.0, 0.0), (0.035, 0.045), (0.012, 0.038), (0.03, 0.07), (-0.01, 0.02)]
            parts.append(K.slab(o, 0.005, pal(s["wings"]), axis="x").move((cx + 0.056, front + 0.03, KNEE_Z + 0.02)))
        if s.get("frost"):
            for i in range(3):
                parts.append(K.crystal((cx - 0.02 + i * 0.02, front - 0.018, KNEE_Z + 0.03), 0.05 - i * 0.008, 0.009,
                                       pal(s["frost"]), rot=(-20 + i * 20, 15, 0)))
    else:
        parts.append(T.cord([(cx - 0.058, front + 0.03, KNEE_Z + 0.045), (cx, front - 0.012, KNEE_Z + 0.05),
                             (cx + 0.058, front + 0.03, KNEE_Z + 0.045)], 0.0035, pal(s.get("straps", "darkleather"))))
    return T.rigid_mix(parts, [("thigh.L", 0.5), ("shin.L", 0.5)])


def guards(s):
    """Chaps: leather over the front and outside of each thigh, strapped round it."""
    g = pal(s.get("guards", "tan"))
    st = pal(s.get("straps", "darkleather"))
    raw = shell(leg_patch(0.58, 0.93, 190.0, 360.0), 0.0125, g, "guard", rim=False, relax=4)
    out = [shell(leg_patch(0.58, 0.93, 190.0, 360.0), 0.0125, g, "guard", relax=4)]
    left = []
    loops = [lp for lp in E.border_loops(raw) if raw.V[lp][:, 0].mean() > 0]
    if loops:
        left.append(E.cord_on(raw, max(loops, key=len), 0.0028, st, n=48, name="guard_edge"))
    GS = T.surf(out[0])
    for z in (0.66, 0.84):
        left += attach(hoop(z, st, GS, 0.002, 0.016, 18), bones=["thigh.L"], k=6)
    return out + WK.both(left)


def thigh_plates(s):
    """Two small plates sewn onto the front of each thigh (dark leather or blackened iron), riveted at the corners."""
    m = WK.plate(s["plates"]) if s.get("plates") in ("blackiron", "darksteel", "iron", "steel") else pal(s.get("plates", "darkleather"))
    trim = pal(s.get("trim", "iron"))
    left = []
    for z, w in ((0.80, 0.046), (0.70, 0.042)):
        c = on_surface(z, 285.0, 0.004)
        _, ctr = T.LEG.hull(z)
        nrm = np.array([c[0] - ctr[0], c[1] - ctr[1], 0.0])
        nrm /= max(np.linalg.norm(nrm), 1e-9)
        p = K.sphere(1.0, (0.0, 0.0, 0.0), m, 12, 6, scale=(w, 0.012, 0.042))
        yaw = math.degrees(math.atan2(nrm[0], -nrm[1]))
        p.rot(WK.Rz(yaw))
        p.move(tuple(c + nrm * 0.004))
        left.append(p)
        for dz in (-0.03, 0.03):
            q = on_surface(z + dz, 285.0 - 14.0, 0.016)
            left.append(K.sphere(0.0042, tuple(q), trim, 6, 4))
            q = on_surface(z + dz, 285.0 + 14.0, 0.016)
            left.append(K.sphere(0.0042, tuple(q), trim, 6, 4))
    return WK.both(attach(left, bones=["thigh.L"], k=6))


def pouch(s):
    c = on_surface(0.84, 350.0, 0.03)
    m = pal(s.get("pouch", "leather"))
    st = pal(s.get("straps", "darkleather"))
    parts = [K.box(0.03, 0.052, 0.07, tuple(c), m, 0.008), K.box(0.032, 0.054, 0.02, (c[0], c[1], c[2] + 0.03), st, 0.004)]
    return attach(parts, bone="thigh.L", keys=True)


def knife(s):
    c = on_surface(0.72, 10.0, 0.018)
    trim = pal(s.get("trim", "iron"))
    parts = [K.box(0.014, 0.026, 0.19, (c[0], c[1], c[2] - 0.03), pal("darkleather"), 0.006),
             K.tube([(c[0], c[1], c[2] + 0.065), (c[0], c[1], c[2] + 0.12)], [0.0085, 0.0075], pal("wood"), n=6),
             K.sphere(0.0105, (c[0], c[1], c[2] + 0.125), trim, 6, 4),
             K.box(0.018, 0.04, 0.008, (c[0], c[1], c[2] + 0.064), trim, 0.002)]
    return attach(parts, bone="thigh.L", keys=True)


def feathers(s):
    trim = pal(s.get("trim", "gold"))
    fm = pal(s.get("feathers", "white"))
    out = []
    for i in range(3):
        c = on_surface(0.93, 10.0 - 12.0 + i * 12.0, 0.012)
        out.append(K.tube([tuple(c), (c[0] + 0.01, c[1], c[2] - 0.07), (c[0] + 0.014, c[1], c[2] - 0.15 + i * 0.02)],
                          [(0.003, 0.002), (0.012, 0.0025), (0.002, 0.001)], fm if i != 1 else trim, n=6, up=(1, 0, 0)))
    out.append(K.sphere(0.008, tuple(on_surface(0.935, 10.0, 0.014)), trim, 6, 4))
    return attach(out, bones=["hips", "thigh.L"], k=6)


def gems(S, key, zs, angles, r=0.0075):
    m = pal(key)
    out = []
    for z, a in zip(zs, angles):
        p = on_surface(z, a, 0.004, S)
        _, c = T.LEG.hull(z)
        nrm = np.array([p[0] - c[0], p[1] - c[1], 0.0])
        nrm /= max(np.linalg.norm(nrm), 1e-9)
        g = K.gem((0, 0, 0), r, m, facets=6)
        # stand the gem on the cloth: its axis (+Z) along the outward normal
        zax = nrm
        xax = np.cross((0.0, 0.0, 1.0), zax)
        xax /= max(np.linalg.norm(xax), 1e-9)
        yax = np.cross(zax, xax)
        g.V = g.V @ np.stack([xax, yax, zax], 0) + p
        out.append(g)
    return attach(out, bones=["thigh.L", "shin.L"], k=6)


# ---- the waist ------------------------------------------------------------------------------------------------------------
def waist(s, S):
    belt_m = pal(s.get("belt", "leather"))
    clasp = pal(s.get("clasp", "brass"))
    trim = pal(s.get("trim", "gold"))
    parts = T.belt(1.03, 1.075, belt_m, S, 0.0035, clasp=clasp)
    if s.get("glow"):
        y = T.front_y(1.052, 0.0, S) - 0.012
        parts.append(K.gem((0.0, y, 1.052), 0.011, pal(s["glow"]), rot=(90, 0, 0)))
    out = attach(parts, bones=["hips", "spine"], k=8)
    if s.get("panel"):
        pm = pal(s["panel"])
        pn = T.panel(-0.085, 0.085, 1.032, 0.56, pm, S, 0.007, nu=5, nv=7, flare=0.35, hem="point", thick=0.004, grow1=0.02)
        out += attach([pn], weights=T.skw(z_top=0.98, z_knee=0.55, centre=0.08, leg=0.7))
        edge = T.vband(-0.088, 0.56, 0.97, 0.01, trim, T.surf(pn), 0.003, 6)
        edge2 = T.vband(0.088, 0.56, 0.97, 0.01, trim, T.surf(pn), 0.003, 6)
        out += attach([edge, edge2], weights=T.skw(z_top=0.98, z_knee=0.55, centre=0.08, leg=0.7))
    if s.get("sash"):
        sm = pal(s["sash"])
        sh = T.panel(0.105, 0.155, 1.032, 0.70, sm, S, 0.008, nu=2, nv=5, flare=0.2, hem="point", thick=0.003, grow1=0.016)
        out += attach([sh], weights=T.skw(z_top=0.98, z_knee=0.55, centre=0.05, leg=0.9))
    if s.get("tassets"):
        plate = WK.plate(s.get("plate", "steel"))
        for sx in (1.0, -1.0):
            x0, x1 = sorted((sx * 0.05, sx * 0.175))
            for i, (z0, z1) in enumerate(((1.028, 0.94), (0.955, 0.87))):
                tp = T.panel(x0, x1, z0, z1, plate, S, 0.016 + 0.004 * i, nu=5, nv=3, flare=0.1, thick=0.005, grow1=0.024 + 0.004 * i)
                out += attach([tp], weights=T.skw(z_top=0.98, z_knee=0.55, centre=0.05, leg=0.85))
                tr = T.vband((x0 + x1) / 2, z1, z1 + 0.012, x1 - x0, trim, T.surf(tp), 0.002, 1)
                out += attach([tr], weights=T.skw(z_top=0.98, z_knee=0.55, centre=0.05, leg=0.85))
    return out


# ---- a pair of leggings -----------------------------------------------------------------------------------------------------
def leggings(id):
    s = spec_of(id)
    kind = s.get("kind", "trousers")
    trim = pal(s.get("trim", "gold"))
    g = {"": [], "waist": [], "hip": [], "knee": [], "ankle_L": [], "ankle_R": []}
    lower = s.get("hose")
    if lower:                                       # breeches: full over the thigh, fitted hose below the knee
        up = T.cloth(T.region(legs=(0.455, TOP)), offset_fn(BASE.get(kind, 0.0068), s.get("loose", 0.0)), pal(s.get("mat", "wool")),
                     "breeches", relax=3)
        lo = T.cloth(T.region(legs=(HEM, 0.47)), 0.0052, pal(lower), "hose", relax=2)
        g[""] += [up, lo]
        US = T.surf(up)
        cuff = pal(s.get("cuff", trim))
        g[""] += WK.both(attach(hoop(0.462, cuff, US, 0.001, 0.022, 18), bones=["thigh.L", "shin.L"], k=6))
        S = US
        cl = up
    else:
        cl = cloth_legs(s)
        g[""].append(cl)
        S = T.surf(cl)
    left = []
    # ---- by kind
    if kind in ("plate", "mail"):
        if kind == "plate":
            g["hip"] += plate_bands(s, S)
        else:
            left += attach(hoop(0.445, pal("leather"), S, 0.0015, 0.016, 18), bones=["shin.L", "thigh.L"], k=6)
        g["knee"] += WK.both(knee_cop(s))
    elif kind in ("trousers", "silk"):
        if s.get("knee_pad"):
            g["knee"] += WK.both(knee_cop(s, pad=True))
    elif kind in ("hide", "chaps", "wrap"):
        if kind == "chaps" or s.get("guards"):
            g["hip"] += guards(s)
        if s.get("knee_pad"):
            g["knee"] += WK.both(knee_cop(s, pad=True))
        if s.get("plates"):
            g["hip"] += thigh_plates(s)
    # laces down the outer seam
    if kind == "hide" or s.get("lacing"):
        lace = pal(s.get("lacing", "darkleather"))
        up_p = attach(seam_cord(0.93, 0.40, 2.0, lace, S, 0.0015, 0.0024, 16, zig=7.0), bones=["thigh.L", "shin.L"], k=6)
        lo_p = attach(seam_cord(0.40, 0.16, 2.0, lace, S, 0.0015, 0.0024, 7, zig=7.0), bones=["shin.L"], k=6)
        left += up_p
        g["ankle_L"] += lo_p
        g["ankle_R"] += WK.mirror(lo_p)
    # a stripe down the outer seam
    if s.get("stripe"):
        left += attach(seam_cord(0.95, 0.14, 0.0, pal(s["stripe"]), S, 0.001, 0.0028, 20), bones=["thigh.L", "shin.L"], k=6)
    # wraps wound round the lower leg
    wraps = s.get("wraps") if kind != "wrap" else s.get("wraps", "darkleather")
    if wraps:
        wm = pal(wraps)
        n = 8
        for i in range(n):
            z = 0.47 - i * (0.47 - 0.15) / (n - 1)
            c = attach(tilted_cord(z, 0.016 if i % 2 else -0.016, wm, S, 0.0025, 0.0036, 18), bones=["shin.L"], k=6)
            if z < LOW:
                g["ankle_L"] += c
                g["ankle_R"] += WK.mirror(c)
            else:
                left += c
    # ankle cuffs
    cuff = s.get("cuff")
    if cuff and kind in ("trousers", "silk") and not lower:
        c = attach(hoop(0.128, pal(cuff), S, 0.0015, 0.02, 18), bones=["shin.L"], k=6)
        g["ankle_L"] += c
        g["ankle_R"] += WK.mirror(c)
    # pouches, sheaths, feathers
    if s.get("pouch"):
        g["hip"] += WK.both(pouch(s))
    if s.get("knife"):
        g["hip"] += knife(s)
    if s.get("feathers"):
        g["hip"] += WK.both(feathers(s))
    # studded gems: runes up the front, stars scattered
    if s.get("runes"):
        left += gems(S, s["runes"], [0.86, 0.76, 0.66, 0.56], [262.0, 268.0, 274.0, 280.0], 0.0072)
    if s.get("stars"):
        zs = [0.9, 0.78, 0.7, 0.6, 0.47]
        left += gems(S, s["stars"], zs, [250.0, 300.0, 225.0, 285.0, 260.0], 0.0058)
    g[""] += WK.both(left)
    g["waist"] += waist(s, S)
    return g


def _legs_item(id):
    @item(id, hide=HIDE)
    def fn():
        return leggings(id)
    return fn


LEGGINGS = ["iron_cuisses", "mail_chausses", "riveted_legplates", "warden_cuisses", "commander_cuisses", "guardian_cuisses",
            "u_rimewalkers", "u_oathbound_cuisses", "u_echoing_legplates",
            "linen_trousers", "scholars_breeches", "arcanist_legwraps", "magister_silks", "aethersilk_trousers", "sage_leggings",
            "u_stillwater_silks", "u_riftwalker_legwraps",
            "hide_leggings", "trackers_breeches", "staghide_chaps", "longstrider_leggings", "windrunner_leggings",
            "u_windswift_breeches", "u_stormstriders",
            "cutpurse_trousers", "nightweave_leggings", "silentstep_breeches", "duskrunner_leggings", "veilstalker_leggings",
            "u_bloodrunner",
            "depth_deepwarden_cuisses", "depth_prismkeeper_legwraps", "depth_vaultpath_leggings", "depth_gloomthread_leggings"]

for _id in LEGGINGS:
    _legs_item(_id)


# ---- the shared legwear -----------------------------------------------------------------------------------------------------
@item("_under_legs", hide=HIDE)
def under_legs():
    """The plain cloth beneath boss Legguards, in the set's colour (BH_Cloth_Primary takes the game's tint)."""
    return [T.cloth(T.region(legs=(HEM, TOP)), offset_fn(0.0055), TINT, "hose", relax=3)]


@item("_breeches", hide=HIDE)
def breeches():
    """What a hero in a shirt or a coat wears when no leggings are equipped: plain breeches, tinted by the game."""
    cl = T.cloth(T.region(legs=(HEM, TOP)), offset_fn(0.006, 0.4), TINT, "breeches", relax=3)
    S = T.surf(cl)
    band = attach(hoop(0.44, TINT, S, 0.0012, 0.018, 18), bones=["shin.L", "thigh.L"], k=6)
    return [cl] + WK.both(band)
