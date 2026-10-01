"""Glyphbound Warrior (bh-029, Builder M1, Zarael / the Coilwood melee grunt): a corrupted Agdao terrace guard.
Thick quilted-cotton armour (horizontal quilting ridges, padded collar and shoulder rolls, a quilted skirt), a red
sash and kilt flaps with a stepped-fret hem, bare muscled arms scarred with violet-red Blackwire (glowing inlaid
scars), quilted bracers and shin wraps, sandals. A lacquered wooden crest helm with a jade brow band, cheek flaps and
a tall fan of teal feathers tipped scarlet, jade ear spools, a black paint band across glowing violet-red eyes, a
jade glyph plaque on the chest. Right hand: an obsidian-edged wooden war club (two rows of black glass teeth, a
violet-red wire inlay). Left hand: a round hide shield painted with a stepped fret, feather fringe at the bottom.

~1.85 m to the helm top (the feather fan rises ~0.3 m higher). Clips: axe_1 axe_2 axe_heavy shield_bash.

Also holds the small Zarael kit the other M1 modules share (feathers, stepped frets, wire coils, inlaid wire
channels, bead strings): `zfeather`, `fret_wave`, `coil`, `channel`, `beads`."""
import math

import numpy as np

import bh_mesh as M
import bh_weapons as WP
from bh_body import torso_loft, torso_ring, front_y, back_y, smoothstep, interp_rows
from bh_math import normalize, Rx, Ry, Rz
from bh_skeleton import proportions
import enemy_bandit_cutthroat as K
import enemy_ashen_cultist as C
import enemy_hollow_soldier as HS
import kit_a_common as A
import kit_e_orrery as O

SCALE = 1.85 / 1.84
PROPS = proportions(SCALE, shoulder_x=0.198 * SCALE)
PREVIEW_HEIGHT = 2.35
PALETTE = "glyphbound_warrior"
PALETTE_COLORS = {
    "BH_Cloth_Primary": ((0.5, 0.42, 0.3), 0.0, 0.95, None, 0.0, 1.0),          # undyed quilted cotton (grimy)
    "BH_Cloth_Secondary": ((0.34, 0.055, 0.04), 0.0, 0.9, None, 0.0, 1.0),      # red sash / kilt / paint
    "BH_Skin": ((0.3, 0.19, 0.13), 0.0, 0.55, None, 0.0, 1.0),                  # sun-dark skin
    "BH_Hair": ((0.03, 0.3, 0.27), 0.0, 0.7, None, 0.0, 1.0),                   # teal feathers
    "BH_Flesh": ((0.5, 0.06, 0.04), 0.0, 0.7, None, 0.0, 1.0),                  # scarlet feather tips
    "BH_Stone": ((0.1, 0.4, 0.32), 0.0, 0.35, None, 0.0, 1.0),                  # jade
    "BH_Wood": ((0.15, 0.085, 0.045), 0.0, 0.7, None, 0.0, 1.0),                # club, helm (dark lacquer)
    "BH_Leather": ((0.11, 0.065, 0.035), 0.0, 0.7, None, 0.0, 1.0),             # sandals, straps, grip
    "BH_Horn": ((0.018, 0.016, 0.024), 0.35, 0.1, None, 0.0, 1.0),              # obsidian teeth
    "BH_Bone": ((0.56, 0.46, 0.31), 0.0, 0.8, None, 0.0, 1.0),                  # hide shield face
    "BH_Gold": ((0.72, 0.38, 0.18), 1.0, 0.35, None, 0.0, 1.0),                 # copper wire / studs
    "BH_Shadow": ((0.018, 0.014, 0.014), 0.0, 0.8, None, 0.0, 1.0),             # black paint, grooves
    "BH_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.4, (1.0, 1.0, 1.0), 5.0, 1.0),  # Zarael glows are white
}
CLIPS = ["axe_1", "axe_2", "axe_heavy", "shield_bash"]

TORSO = [(r[0], r[1] * 1.06, r[2] * 1.05, r[3] * 1.04, r[4]) for r in K.TORSO]
QG = 0.026                       # quilted cotton thickness over the body
TORSO_W = K.TORSO_W


def finish_mesh(mesh_ob):
    K.enable_weapon_deform(mesh_ob)


# ================================================================================================= Zarael kit
def P(V, F, mat, name="part"):
    return M.Part(np.asarray(V, float), F, mat, name=name)


def feather(base, direction, length, width, mat, side=(1, 0, 0), bend=0.15, k=9, thick=0.003):
    """kit_a_common.feather with a selectable outline resolution k (k=5: a ~30-triangle feather)."""
    d = normalize(direction)
    sd = normalize(np.asarray(side, float) - d * np.dot(side, d))
    nrm = np.cross(d, sd)
    outline = []
    for i in range(k):
        t = i / (k - 1)
        outline.append((t, 0.5 * width * math.sin(math.pi * min(t * 1.08, 1.0)) ** 0.8 * (1.0 if t < 0.95 else 0.4)))
    top = [(t * length, w) for t, w in outline]
    bot = [(t * length, -w * 0.8) for t, w in outline[::-1]][1:-1]
    o = np.array(top + bot)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    V, F = M.prism(o, thick, axis="z")
    b = np.asarray(base, float)
    Vn = [b + d * x + sd * y + nrm * (z + bend * (x / length) ** 2 * length) for x, y, z in V]
    return P(np.array(Vn), F, mat, "feather")


def zfeather(base, direction, length, width, side, mats=("BH_Hair", "BH_Flesh"), tip=0.3, bend=0.12, lift=0.003,
             quill=True, k=9):
    """Flat feather (quill + vane in the plane of direction x side) with a coloured tip band. Returns parts."""
    d = normalize(direction)
    out = [feather(base, d, length, width, mats[0], side=side, bend=bend, k=k)]
    if tip > 0 and mats[1]:
        sd = normalize(np.asarray(side, float) - d * np.dot(side, d))
        nrm = np.cross(d, sd)
        b2 = np.asarray(base, float) + d * length * (1 - tip) + nrm * (lift + bend * (1 - tip) ** 2 * length)
        out.append(feather(b2, d, length * tip * 1.02, width * 0.82, mats[1], side=side, bend=bend * 0.4,
                           k=max(5, k - 2)))
    if quill:
        out.append(A.taper([np.asarray(base, float) - d * 0.02, np.asarray(base, float) + d * length * 0.35], 0.004,
                           0.0015, "BH_Bone", n=4))
    return out


def fret_wave(n_periods, steps=3):
    """A stepped-fret band as a 2D polyline in (u, v), u in [0, 1] along the band, v in [0, 1] across: each period
    climbs `steps` stairs, runs along the top, drops, and hooks back in (the stepped spiral of the old carvings)."""
    pts = []
    for k in range(n_periods):
        u0 = k / n_periods
        du = 1.0 / n_periods
        s = du / (2 * steps + 2)
        u = u0
        v = 0.0
        pts.append((u, v))
        for i in range(steps):
            u += s
            pts.append((u, v))
            v += 1.0 / steps
            pts.append((u, v))
        u += s * 2
        pts.append((u, v))
        pts.append((u, 0.35))                 # the hook drops inside the top run
        pts.append((u - s * 0.9, 0.35))
        pts.append((u - s * 0.9, 0.62))
        pts.append((u + s * 0.4, 0.62))
        pts.append((u + s * 0.4, 1.0))
        u += s * 1.2
        pts.append((u, 1.0))
        pts.append((u, 0.0))
        u = u0 + du
        pts.append((u, 0.0))
    return np.array(pts)


def coil(a, b, r, turns, wire_r, mat, n=5, pts_per_turn=10):
    """Helix of wire wound round the segment a->b at radius r."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = normalize(b - a)
    side = normalize(np.cross(d, (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)))
    fw = np.cross(d, side)
    k = int(turns * pts_per_turn) + 1
    pts = []
    for i in range(k):
        t = i / (k - 1)
        ang = 2 * math.pi * turns * t
        pts.append(a + (b - a) * t + (side * math.cos(ang) + fw * math.sin(ang)) * r)
    V, F = M.tube(np.array(pts), [(wire_r, wire_r)] * k, n=n, up=tuple(d), cap0=True, cap1=True)
    return P(V, F, mat, "coil")


def channel(pts, nrm, r=0.012, glow="BH_Emissive", groove="BH_Shadow", broken=()):
    """Inlaid wire channel: a dark groove with the glowing wire just proud of it. nrm: outward normal (one or per
    point). broken: indices of segments where the wire is cut (cracked channels show the dark groove only)."""
    pts = np.asarray(pts, float)
    nrm = np.asarray(nrm, float)
    if nrm.ndim == 1:
        nrm = np.repeat(nrm[None], len(pts), 0)
    out = [A.tube(pts - nrm * r * 0.6, r * 1.6, groove, n=4)]
    segs, cur = [], [0]
    for i in range(1, len(pts)):
        if (i - 1) in broken:
            segs.append(cur)
            cur = [i]
        else:
            cur.append(i)
    segs.append(cur)
    for s in segs:
        if len(s) < 2:
            continue
        q = pts[s] - nrm[s] * r * 0.1
        out.append(A.tube(q, r, glow, n=5))
    return out


def beads(pts, r, mats, n=5, rings=3, every=1.0):
    """A string of beads along a polyline (bead spacing ~ 2.1 r), materials cycling through mats."""
    pts = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    L = float(seg.sum())
    cnt = max(int(L / (2.1 * r * every)), 2)
    out = []
    cum = np.concatenate([[0], np.cumsum(seg)])
    for i in range(cnt):
        s = L * i / (cnt - 1)
        j = min(int(np.searchsorted(cum, s, side="right") - 1), len(seg) - 1)
        u = (s - cum[j]) / max(seg[j], 1e-9)
        c = pts[j] * (1 - u) + pts[j + 1] * u
        out.append(A.ball(c, r * (1.15 if i % 5 == 2 else 1.0), mats[i % len(mats)], n=n, rings=rings))
    return out


def centre_w(top=1.0, bot=0.55, leg=0.5):
    """Centre cloth between the legs: both thighs share the leg influence (no tearing down the middle)."""
    def wfn(V):
        out = []
        for v in V:
            s = float(smoothstep(top, bot, v[2])) * leg
            out.append({"hips": 1 - s, "thigh.L": s / 2, "thigh.R": s / 2} if s > 1e-3 else {"hips": 1.0})
        return out
    return wfn


# ================================================================================================= warrior
def build(body):
    sb = K.SB(body, SCALE)
    quilted_armour(sb)
    kilt_and_sash(sb)
    head(sb)
    K.trousers(sb, "BH_Skin", loose=0.92, end=0.7)
    K.boots(sb, "BH_Leather", "BH_Leather", shaft_top=0.5, cuff=False, wraps=None)
    for s in ("L", "R"):
        arm(sb, s)
        leg(sb, s)
    K.add_weapon(sb, "R", war_club(SCALE))
    K.add_weapon(sb, "L", hide_shield(SCALE))


def grown(rows, g):
    return [(r[0], r[1] + g, r[2] + g, r[3] + g, r[4]) for r in rows]


def quilted_armour(sb):
    # body under the armour (fills the neck hole) + the quilted coat itself
    V, F = torso_loft([r for r in TORSO if r[0] >= 0.98], n=24, cap1=True)
    sb.add(P(V, F, "BH_Skin", "body"), weights=TORSO_W)
    coat = grown([r for r in TORSO if r[0] <= 1.5] + [(1.52, 0.11, 0.08, 0.08, 0.0)], QG)
    coat = [(0.95,) + coat[0][1:]] + coat
    V, F = torso_loft(coat, n=28, cap0=False, cap1=False)
    sb.add(P(V, F, "BH_Cloth_Primary", "coat"), weights=TORSO_W)
    # quilting ridges (horizontal) + a few vertical stitch lines
    for z in np.arange(0.99, 1.47, 0.052):
        r = interp_rows(coat, z)
        ring = torso_ring(z, r[1] + 0.004, r[2] + 0.004, r[3] + 0.004, r[4], 2.3, 20)
        ring = np.vstack([ring, ring[:1]])
        V, F = M.tube(ring, [(0.008, 0.008)] * len(ring), n=4, up=(0, 0, 1), cap0=False, cap1=False)
        sb.add(P(V, F, "BH_Cloth_Primary", "quilt"), weights=TORSO_W)
    # padded collar roll
    ring = K.ring_frac(coat, 1.5, 0.01, np.linspace(0, 1, 25)[:-1])
    ring[:, 2] = 1.5 - 0.02 * np.cos(np.linspace(0, 2 * math.pi, 25)[:-1] * 0) * 0
    ring = np.vstack([ring, ring[:1]])
    V, F = M.tube(ring, [(0.03, 0.028)] * len(ring), n=8, up=(0, 0, 1), cap0=False, cap1=False)
    sb.add(P(V, F, "BH_Cloth_Primary", "collar"), "chest")
    # quilted skirt (four panels so the legs move) with a red hem band
    C.robe_skirt(sb, "BH_Cloth_Primary", trim="BH_Cloth_Secondary", z_top=1.0, z_bot=0.78, flare=0.07, folds=0.006,
                 g=QG + 0.006)
    # jade glyph plaque on the chest: a stepped frame with the Blackwire burning in its glyph
    zc = 1.33
    y = front_y(coat, 0, zc) - 0.012
    V, F = M.box(0.13, 0.022, 0.12)
    sb.add(M.bevel(P(V, F, "BH_Stone", "plaque").move((0, y, zc)), 0.01, 1), "chest")
    V, F = M.box(0.15, 0.012, 0.14)
    sb.add(P(V, F, "BH_Gold", "plaque_rim").move((0, y + 0.008, zc)), "chest")
    gl = [(-0.04, zc - 0.035), (-0.04, zc + 0.035), (0.0, zc + 0.035), (0.0, zc - 0.005), (0.035, zc - 0.005),
          (0.035, zc + 0.035)]
    for prt in channel([(x, y - 0.012, z) for x, z in gl], (0, -1, 0), r=0.0065):
        sb.add(prt, "chest")
    sb.add(A.tube([(0.0, y - 0.013, zc - 0.04), (0.04, y - 0.013, zc - 0.04)], 0.0065, "BH_Emissive", n=5), "chest")
    # thongs from the plaque to the collar
    for sx in (1, -1):
        pts = [(sx * 0.06, y + 0.002, zc + 0.05), (sx * 0.08, front_y(coat, sx * 0.08, 1.45) - 0.008, 1.45),
               (sx * 0.085, 0.0, 1.535)]
        sb.add(A.tube(pts, 0.005, "BH_Leather", n=4), "chest")


def kilt_and_sash(sb):
    rows = grown(TORSO, QG + 0.01)
    # red sash band + knot with hanging tails on the left hip
    V, F = K.band(rows, 0.98, 1.05, 0.012, -0.004, n=30)
    sb.add(P(V, F, "BH_Cloth_Secondary", "sash"), "hips")
    p, _ = K.on_ring(rows, 1.0, 0.03, 0.2)
    sb.add(A.ball(p, 0.035, "BH_Cloth_Secondary", n=8, rings=5, scale=(0.7, 1.0, 0.9)), "hips")
    for dx, ln in ((0.0, 0.3), (0.03, 0.24)):
        pts = [p + (dx, 0, -0.02), p + (dx + 0.02, -0.01, -ln * 0.5), p + (dx + 0.03, 0.0, -ln)]
        sb.add(K.strip(pts, 0.05, 0.008, "BH_Cloth_Secondary", ups=[(1, 0, 0)] * 3),
               weights=sb.skirt(1.0, 0.6, max_leg=0.5, center_w=0.05))
    # kilt flaps (front + back) over the quilted skirt, with a stepped-fret hem in jade and copper
    for front in (True, False):
        pnl = HS.cloth_panel(rows, 1.0, 0.6, lambda z: 0.105 + 0.02 * (1.0 - z), front=front, nu=7, nv=8,
                             mat="BH_Cloth_Secondary", gap=0.012, hang=0.06, rag=0.0, thick=0.008, belt_z=0.98)
        sb.add(pnl, weights=centre_w(0.98, 0.55, 0.55))
        yb = (front_y(rows, 0, 0.98) - 0.012 - 0.06 * 0.32 - 0.013) if front else \
            (back_y(rows, 0, 0.98) + 0.012 + 0.06 * 1.3 * 0.32 + 0.013)
        fw = fret_wave(3)
        hw = 0.105 + 0.02 * 0.36
        pts = [(-hw * 0.92 + 2 * hw * 0.92 * u, yb, 0.63 + 0.06 * v) for u, v in fw]
        sb.add(A.tube(pts, (0.0075, 0.003), "BH_Stone", n=4, up=(0, -1 if front else 1, 0)),
               weights=centre_w(0.98, 0.55, 0.55))
        hem = [(-hw, yb, 0.615), (hw, yb, 0.615)]
        sb.add(A.tube(hem, (0.006, 0.004), "BH_Gold", n=4), weights=centre_w(0.98, 0.55, 0.55))


def head(sb):
    K.neck_and_head(sb, skin="BH_Skin", eyes="BH_Shadow", eye_glow="BH_Emissive", nose=True)
    # black paint band across the eyes
    rows = K.grow_rows(K.HEAD, 0.0035)
    rings = []
    for z in (1.682, 1.698, 1.716):
        r = K.ring_frac(rows, z, 0.0, np.linspace(-0.2, 0.2, 13) % 1.0, p=2.1)
        rings.append(r)
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    sb.add(M.solidify(P(V, F, "BH_Shadow", "paint"), 0.002, offset=1.0), "head")
    # helm: lacquered wooden cap, jade brow band with copper studs, quilted cheek flaps
    hz = 1.6
    c = (0.0, 0.01, 0.0)
    prof = [(0.0, 0.258), (0.05, 0.252), (0.085, 0.228), (0.1, 0.185), (0.104, 0.14), (0.104, 0.1)]
    V, F = M.lathe(prof, 20, cap=False)
    shell = P(V, F, "BH_Wood", "helm").scale((1.0, 1.1, 1.0)).move((c[0], c[1], hz))
    sb.add(M.solidify(shell, 0.008, offset=1), "head")
    V, F = M.lathe([(0.106, 0.098), (0.114, 0.102), (0.114, 0.138), (0.106, 0.142)], 20, cap=False)
    sb.add(P(V, F, "BH_Stone", "browband").scale((1.0, 1.1, 1.0)).move((0, 0.01, hz)), "head")
    for k in range(14):
        a = 2 * math.pi * k / 14
        q = np.array([0.117 * math.sin(a), 0.01 - 0.117 * 1.1 * math.cos(a), hz + 0.12])
        V, F = M.box(0.016, 0.008, 0.02)
        sb.add(P(V, F, "BH_Gold", "stud").rot(Rz(math.degrees(a))).move(q), "head")
    for sx in (1, -1):        # cheek flaps (quilted cotton)
        def fn(u, v, sx=sx):
            a = math.radians(-20 + 75 * u)
            r = 0.104 + 0.012 * v
            return (sx * r * math.cos(a), 0.01 + 1.1 * r * math.sin(a) - 0.03, hz + 0.105 - 0.13 * v)
        V, F = M.grid(fn, 5, 4)
        fl = P(V, F, "BH_Cloth_Primary", "flap")
        if sx < 0:
            fl.flip()
        sb.add(M.solidify(fl, 0.012, offset=-1), "head")
        # jade ear spool on the flap
        V, F = M.lathe([(0.0, -0.006), (0.024, -0.006), (0.026, 0.0), (0.024, 0.008), (0.0, 0.008)], 10)
        sp = P(V, F, "BH_Stone", "spool").rot(Ry(90 * sx)).move((sx * 0.125, 0.025, hz + 0.06))
        sb.add(sp, "head")
    # crest: carved holder on the crown, then the fan of feathers (tilted back so it reads from above)
    base = np.array([0.0, 0.05, hz + 0.245])
    V, F = M.lathe([(0.0, -0.03), (0.032, -0.03), (0.038, 0.0), (0.026, 0.03), (0.0, 0.032)], 10)
    sb.add(P(V, F, "BH_Stone", "holder").scale((1.4, 1.0, 1.0)).move(base), "head")
    tb = math.radians(22)
    n = 11
    for i in range(n):
        a = math.radians(-78 + 156 * i / (n - 1))
        d = np.array([math.sin(a), math.sin(tb) * math.cos(a), math.cos(tb) * math.cos(a)])
        tng = np.array([math.cos(a), -math.sin(tb) * math.sin(a), -math.cos(tb) * math.sin(a)])
        ln = 0.3 + 0.1 * math.cos(a) ** 2
        for prt in zfeather(base + d * 0.02, d, ln, 0.07, tng, tip=0.28, bend=0.05):
            sb.add(prt, "head")
    # small inner fan of scarlet feathers
    for i in range(5):
        a = math.radians(-56 + 112 * i / 4)
        d = np.array([math.sin(a), math.sin(tb - 0.1) * math.cos(a), math.cos(tb - 0.1) * math.cos(a)])
        tng = np.array([math.cos(a), 0.0, -math.sin(a)])
        for prt in zfeather(base + d * 0.02 + (0, -0.01, 0), d, 0.17, 0.05, tng, mats=("BH_Flesh", None), tip=0):
            sb.add(prt, "head")


def arm(sb, s):
    sx = 1 if s == "L" else -1
    ua, fa, ha = "upper_arm." + s, "forearm." + s, "hand." + s
    K.bare_arm(sb, s, skin="BH_Skin", r_up=0.052, r_fore=0.045, bulk=1.08)
    K.add_fist(sb, s, "BH_Skin", "BH_Skin", gauntlet=False)
    w = sb.seg(["chest", "shoulder." + s, ua, fa, ha], power=9)
    sh, el, wr = sb.head(ua), sb.head(fa), sb.head(ha)
    # quilted shoulder roll (two padded lames)
    for k, (dz, r) in enumerate(((0.05, 0.085), (-0.0, 0.08))):
        def fn(u, v, dz=dz, r=r):
            a = math.radians(-70 + 140 * u)
            b = math.radians(10 + 75 * v)
            return (sh[0] + sx * (r * math.sin(b) - 0.01 + 0.035 * k), sh[1] + r * math.sin(a) * math.cos(b) * 1.1,
                    sh[2] + dz + r * math.cos(a) * math.cos(b) * 0.55 - 0.04 * k)
        V, F = M.grid(fn, 7, 4)
        p = P(V, F, "BH_Cloth_Primary", "roll")
        if sx > 0:
            p.flip()
        sb.add(M.solidify(p, 0.014, offset=0), weights=lambda V, s=s: [{"shoulder." + s: 0.45, "upper_arm." + s: 0.55}]
               * len(V))
    # copper arm band
    c = sh + (el - sh) * 0.62
    d = normalize(el - sh)
    V, F = M.tube([c - d * 0.014, c + d * 0.014], [(0.058, 0.058)] * 2, n=12, up=(0, -1, 0))
    sb.add(P(V, F, "BH_Gold", "armband"), ua)
    # quilted bracer
    V, F = M.tube([el + (wr - el) * 0.45, el + (wr - el) * 0.75, wr + (wr - el) * 0.02],
                  [(0.05, 0.052), (0.047, 0.05), (0.042, 0.045)], n=12, up=(0, -1, 0))
    sb.add(P(V, F, "BH_Cloth_Primary", "bracer"), fa)
    for u in (0.56, 0.8):
        c = el + (wr - el) * u
        V, F = M.tube([c - d * 0.005, c + d * 0.005], [(0.05 - 0.01 * u, 0.053 - 0.01 * u)] * 2, n=12, up=(0, -1, 0))
        sb.add(P(V, F, "BH_Leather", "bracer_tie"), fa)
    # Blackwire scars: jagged glowing lines down the outside of the arm
    for (u0, u1, th0, seed) in ((0.08, 0.95, -0.2, 1.0), (0.15, 0.85, 0.9, 2.3)):
        pts, nrm = [], []
        for i in range(9):
            t = i / 8
            q = sh + (el - sh) * (u0 + (u1 - u0) * t)
            dd = normalize(el - sh)
            side = normalize(np.cross(dd, (0, 1, 0))) * sx
            fw = np.cross(side, dd) * -1
            th = th0 + 0.35 * math.sin(seed * 3 + t * 9) + (0.25 if i % 2 else -0.25)
            nn = side * math.cos(th) + fw * math.sin(th)
            pts.append(q + nn * (0.052 * 1.08 + 0.002))
            nrm.append(nn)
        for prt in channel(pts, nrm, r=0.0075):
            sb.add(prt, weights=w)
    pts, nrm = [], []
    for i in range(6):
        t = i / 5
        q = el + (wr - el) * (0.05 + 0.38 * t)
        dd = normalize(wr - el)
        side = normalize(np.cross(dd, (0, 1, 0))) * sx
        fw = np.cross(side, dd) * -1
        th = 0.3 + (0.3 if i % 2 else -0.3)
        nn = side * math.cos(th) + fw * math.sin(th)
        pts.append(q + nn * 0.047)
        nrm.append(nn)
    for prt in channel(pts, nrm, r=0.0075):
        sb.add(prt, fa)


def leg(sb, s):
    th, sh = "thigh." + s, "shin." + s
    k, a = sb.head(sh), sb.tail(sh)
    # quilted shin wrap with leather ties
    V, F = M.tube([a + (0, 0, 0.06), a + (k - a) * 0.45, k + (0, -0.01, -0.04)],
                  [(0.055, 0.058), (0.062, 0.066), (0.06, 0.064)], n=12, up=(0, -1, 0))
    sb.add(P(V, F, "BH_Cloth_Primary", "shinwrap"), sh)
    for u in (0.3, 0.7):
        c = a + (k - a) * u
        V, F = M.tube([c - (0, 0, 0.006), c + (0, 0, 0.006)], [(0.066, 0.07)] * 2, n=12, up=(0, -1, 0))
        sb.add(P(V, F, "BH_Leather", "tie"), sh)
    # knee pad (quilted)
    V, F = M.sphere(0.06, 10, 6, center=k + (0, -0.045, 0.0), scale=(0.95, 0.5, 1.0))
    sb.add(P(V, F, "BH_Cloth_Primary", "knee"), weights=lambda V, s=s: [{"thigh." + s: 0.4, "shin." + s: 0.6}] * len(V))


# ================================================================================================= weapons
def war_club(s=1.0):
    """Obsidian-edged wooden war club (weapon space: grip at origin, +Z along the club, flats +-Y): a flat
    hardwood paddle, two rows of black glass teeth set in the edges (+-X), violet-red wire inlaid down both
    flats, copper wire wound above the grip, a jade pommel knob."""
    parts = []
    V, F = M.lathe([(0, -0.2), (0.024, -0.2), (0.026, -0.18), (0.02, -0.15), (0.019, 0.1), (0.024, 0.15), (0, 0.15)],
                   8)
    parts.append(P(V, F, "BH_Wood", "handle"))
    parts.append(WP._grip(-0.12, 0.09, 0.0215, 5, mat="BH_Leather"))
    parts.append(A.ball((0, 0, -0.215), 0.033, "BH_Stone", n=8, rings=5, scale=(1, 1, 0.8)))
    parts.append(coil((0, 0, 0.095), (0, 0, 0.16), 0.024, 4.5, 0.0045, "BH_Gold", n=4, pts_per_turn=8))
    # paddle outline (x half-width along z), thickness along Y
    zs = np.linspace(0.12, 0.9, 14)
    half = [0.03 + 0.032 * smoothstep(0.12, 0.34, z) - 0.03 * smoothstep(0.82, 0.9, z) ** 2 for z in zs]
    o = [(h, z) for h, z in zip(half, zs)] + [(-h, z) for h, z in zip(half[::-1], zs[::-1])]
    o = np.array(o)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    V, F = M.prism(o, 0.034, axis="y")
    pad = P(V, F, "BH_Wood", "paddle")
    pad.warp(lambda v: (v[0], v[1] * (1.0 - 0.45 * min(abs(v[0]) / 0.062, 1.0) ** 2), v[2]))
    parts.append(M.bevel(pad, 0.004, 1, angle=40))
    # teeth: two rows of black glass blades in dark resin grooves
    for sx in (1, -1):
        groove = [(sx * (0.03 + 0.032 * smoothstep(0.12, 0.34, z)), 0.0, z) for z in np.linspace(0.2, 0.84, 8)]
        parts.append(A.tube(groove, (0.007, 0.012), "BH_Shadow", n=4, up=(0, 1, 0)))
        for i, z in enumerate(np.arange(0.22, 0.85, 0.068)):
            hw = 0.03 + 0.032 * smoothstep(0.12, 0.34, z) - 0.03 * smoothstep(0.82, 0.9, z) ** 2
            ln = 0.055 + 0.012 * ((i * 7) % 3) / 2
            sh = A.shard((sx * (hw - 0.006), 0.0, z), (sx, 0.0, 0.22 + 0.05 * (i % 2)), ln, 0.026, "BH_Horn", sides=4,
                         up=(0, 1, 0), mid=0.3)
            sh.V[:, 1] *= 0.42
            parts.append(sh)
    # violet-red wire inlay down both flats (zig-zag glyph line)
    for sy in (1, -1):
        pts = [(0.012 * (1 if i % 2 else -1) * (i not in (0, 9)), sy * 0.0155, 0.2 + 0.065 * i) for i in range(10)]
        for prt in channel(pts, (0, sy, 0), r=0.0045):
            parts.append(prt)
    for p in parts:
        p.V = p.V * s
    return parts


def hide_shield(s=1.0, r=0.34):
    """Round hide shield (weapon space: handle at origin, face -Y): cream hide stretched over a wooden hoop,
    a red stepped-fret band painted round a red-and-black eye disc, jade studs, a feather fringe below."""
    parts = []
    yf = -0.07

    def disk(profile, mat, name, n=28):
        V, F = M.lathe(profile, n)
        return P(V, F, mat, name).rot(Rx(90))
    parts.append(disk([(0.0, -yf - 0.03), (r, -yf - 0.024), (r, -yf), (0.0, -yf + 0.012)], "BH_Bone", "hide"))
    rim = [(r * math.cos(a), yf + 0.004, r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 37)]
    V, F = M.tube(rim, [(0.018, 0.022)] * len(rim), n=6, up=(0, -1, 0), cap0=False, cap1=False)
    parts.append(P(V, F, "BH_Wood", "hoop"))
    for k in range(12):             # lacing over the hoop
        a = 2 * math.pi * (k + 0.5) / 12
        q = np.array([r * math.cos(a), yf + 0.004, r * math.sin(a)])
        nrm = np.array([math.cos(a), 0, math.sin(a)])
        parts.append(A.tube([q - nrm * 0.03 + (0, -0.014, 0), q + (0, -0.026, 0), q + nrm * 0.024],
                            0.004, "BH_Leather", n=4))
    yp = yf - 0.0135
    # painted fret band (stepped spiral in red, outlined black)
    fw = fret_wave(8)
    r0, r1 = 0.17, 0.27
    pts = [(math.cos(2 * math.pi * u) * (r0 + (r1 - r0) * v), yp, math.sin(2 * math.pi * u) * (r0 + (r1 - r0) * v))
           for u, v in fw]
    parts.append(A.tube(pts, (0.011, 0.002), "BH_Cloth_Secondary", n=4, up=(0, -1, 0)))
    for rr in (r0 - 0.012, r1 + 0.012):
        ring = [(rr * math.cos(a), yp, rr * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 41)]
        parts.append(A.tube(ring, (0.007, 0.002), "BH_Shadow", n=4, up=(0, -1, 0), cap=False))
    # centre: red disc, black eye glyph, jade pupil
    parts.append(disk([(0.0, -yp + 0.001), (0.11, -yp + 0.001), (0.11, -yp + 0.003), (0.0, -yp + 0.004)],
                      "BH_Cloth_Secondary", "centre", n=24))
    eye = [(0.08 * math.cos(a), yp - 0.004, 0.045 * math.sin(a) * (1 if math.sin(a) > 0 else 0.8))
           for a in np.linspace(0, 2 * math.pi, 21)]
    parts.append(A.tube(eye, (0.009, 0.002), "BH_Shadow", n=4, up=(0, -1, 0), cap=False))
    parts.append(disk([(0.0, -yp + 0.007), (0.028, -yp + 0.006), (0.03, -yp + 0.004), (0.0, -yp + 0.003)],
                      "BH_Stone", "pupil", n=12))
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        parts.append(A.ball((0.31 * math.cos(a), yp, 0.31 * math.sin(a)), 0.014, "BH_Stone", n=6, rings=3,
                            scale=(1, 0.6, 1)))
    # feather fringe hanging from the lower rim
    for k in range(7):
        a = math.radians(-90 + (k - 3) * 15)
        q = np.array([r * math.cos(a), yf - 0.012, r * math.sin(a)])
        d = normalize(np.array([0.2 * math.cos(a), -0.08, -1.0]))
        parts.append(A.tube([q + (0, 0, 0.02), q - (0, 0, 0.03)], 0.004, "BH_Leather", n=4))
        for prt in zfeather(q - (0, 0, 0.02), d, 0.2 + 0.03 * (k % 2), 0.05, (1, 0, 0), tip=0.3, bend=0.04, quill=False):
            parts.append(prt)
    # grip + arm strap on the back
    V, F = M.tube([(-0.08, -0.035, 0.0), (-0.05, 0.02, 0.0), (0.05, 0.02, 0.0), (0.08, -0.035, 0.0)],
                  [(0.013, 0.035)] * 4, n=6, up=(0, 0, 1))
    parts.append(P(V, F, "BH_Leather", "handle"))
    V, F = M.box(0.28, 0.012, 0.05, center=(0, -0.045, 0.19))
    parts.append(P(V, F, "BH_Leather", "strap"))
    for p in parts:
        p.V = p.V * s
    return parts
