"""Zarael wilds, Bridge of Death and Heart Citadel kit (run bh-029, Builder K2), category `zarael_wild`.

Zarael's ancient builders, the Wirewrights, laid gold-bright wire through the island's stone (the Heartwire). Every
glowing line here is *inlaid engineering*: a wire (`BH_Wire`) seated in a dark carved channel bed and held by bronze
clamps; glyphs (`BH_Glyph`) are carved cartouches with lit strokes. Corrupted pieces use `BH_Blackwire`.
Theme is visual only (stepped talus-and-panel tiers, stepped-fret bands, serpent heads, jade, obsidian, turquoise).

Conventions as the rest of the kit: metres, Blender Z-up exported Y-up, Blender -Y is the Godot +Z front, origin at the
bottom centre unless the asset says otherwise, `<name>-colonly` collision children, sockets as child empties.
Exceptions (origin):
  zr_bridge_span_8m, zr_jetty_wood  - deck-top centre (deck at y=0; spans tile end to end along Godot Z)
  zr_bridge_pier                    - top centre (hangs down to y=-45)
  zr_bridge_pylon                   - top of its foundation at y=0 (a stepped corbel hangs to y=-5 so it reads as a
                                      buttress cantilevered off the bridge's side)
  zr_gate_*                         - centre of the 3 m clear teleporter disc (portal behind it on Godot -Z)
  zr_relay_chains                   - same origin as zr_relay_pylon
  zr_vine_curtain                   - bottom of the curtain on the wall face (strands hang toward Godot +Z)
zr_dawn_engine exports three bronze rings as child mesh nodes `ring_1`, `ring_2`, `ring_3`; each ring lies in its
node's local XY plane in Blender (= local XZ in Godot) so the game spins it about its local up axis.
"""
import math

import bmesh
from mathutils import Vector, Matrix, noise as mnoise

import kit
from kit import *  # noqa
from masonry import *  # noqa
from registry import asset
import market_common  # noqa  (registers BH_Brass, BH_Copper, BH_Verdigris, BH_Rope, BH_Cloth* export colours)
from assets_nature import rand_unit, align_z, rock_piece
from assets_dungeon import chain, crystal, attach_children

CAT = "zarael_wild"

# bh-029 contract materials (export colours are linear previews; Godot swaps them by name via MaterialLibrary.ENV).
EXTRA_MATERIALS = {
    "BH_GlyphStone":     ((0.42, 0.38, 0.31, 1), 0.88, 0.0, None),
    "BH_GlyphStoneDark": ((0.15, 0.15, 0.12, 1), 0.92, 0.0, None),
    "BH_Jade":           ((0.04, 0.24, 0.12, 1), 0.3, 0.0, None),
    "BH_Obsidian":       ((0.012, 0.01, 0.016, 1), 0.08, 0.0, None),
    "BH_LimePlaster":    ((0.46, 0.31, 0.13, 1), 0.95, 0.0, None),
    "BH_LimePlasterRed": ((0.34, 0.06, 0.04, 1), 0.95, 0.0, None),
    "BH_TerracePave":    ((0.3, 0.27, 0.22, 1), 0.9, 0.0, None),
    "BH_Turquoise":      ((0.04, 0.3, 0.28, 1), 0.45, 0.0, None),
    "BH_Wire":           ((0.8, 0.2, 0.42, 1), 0.35, 0.6, ((0.9, 0.16, 0.42), 6.0)),
    "BH_Glyph":          ((0.1, 0.7, 0.6, 1), 0.4, 0.0, ((0.15, 0.85, 0.72), 4.0)),
    "BH_Blackwire":      ((0.5, 0.04, 0.28, 1), 0.35, 0.0, ((0.75, 0.08, 0.38), 6.0)),
    "BH_Feather":        ((0.03, 0.24, 0.17, 1), 0.85, 0.0, None),
    "BH_FeatherRed":     ((0.4, 0.03, 0.02, 1), 0.85, 0.0, None),
    "BH_JungleLeaf":     ((0.035, 0.11, 0.025, 1), 0.7, 0.0, None),
    # K2 request (not in the contract table): layered ochre sandstone for rocks/cliffs, texture set `cliff_ochre`.
    # Until MaterialLibrary.ENV has it, Godot keeps this flat ochre glTF material.
    "BH_CliffOchre":     ((0.36, 0.16, 0.07, 1), 0.92, 0.0, None),
}
for _n, _v in EXTRA_MATERIALS.items():
    kit.MATERIALS.setdefault(_n, _v)
    if _n not in kit.MATERIAL_NAMES:
        kit.MATERIAL_NAMES.append(_n)

GS, GSD = "BH_GlyphStone", "BH_GlyphStoneDark"
UP, DOWN = Vector((0, 0, 1)), Vector((0, 0, -1))


# ---------------------------------------------------------------------------------------------------------------
# generic helpers
def mossy(k, thresh=0.72, scale=0.9, bias=0.05):
    return moss_fn(k, thresh, scale, bias)


def blk(k, sx, sy, sz, M=None, mat=GS, chips=2, chipd=None, bev=0.04, moss=None, jit=0.008):
    """Chipped, bevelled stone block centred at M."""
    t = box(sx, sy, sz, bev=bev)
    if chips:
        chip(t, k.r, chips, chipd if chipd is not None else min(sx, sy, sz) * 0.16 + 0.02)
    if jit:
        jitter(t, k.r, jit)
    k.put(t, mat, M=M, mat_fn=mossy(k, *moss) if moss else None)


def hx(k, c, mat=GS, M=None, bev=0.04, chips=2, chipd=0.1, moss=None):
    t = hexa(c, bev)
    if chips:
        chip(t, k.r, chips, chipd)
    k.put(t, mat, M=M, mat_fn=mossy(k, *moss) if moss else None)


def frame_of(a, b, n):
    """Matrix with origin at the a-b midpoint, local Z along a->b, local Y along n (made perpendicular)."""
    a, b, n = Vector(a), Vector(b), Vector(n)
    d = b - a
    L = d.length
    z = d / L
    n = (n - z * n.dot(z)).normalized()
    x = n.cross(z).normalized()
    c = (a + b) / 2
    return Matrix(((x.x, n.x, z.x, c.x), (x.y, n.y, z.y, c.y), (x.z, n.z, z.z, c.z), (0, 0, 0, 1))), L, n


def strip(k, a, b, n, w, th, mat, off=0.0, M=None, bev=0.0):
    """Flat bar from a to b lying on a surface with outward normal n: width w across, thickness th outward from
    the surface (shifted by off along n)."""
    if (Vector(b) - Vector(a)).length < 1e-4:
        return
    F, L, nn = frame_of(a, b, n)
    F = F @ T(0, th / 2 + off, 0)
    k.put(box(w, th, L, bev=bev), mat, M=(M @ F) if M is not None else F)


def wire_run(k, a, b, n, w=0.14, M=None, clamps=1.6, mat="BH_Wire", bed=True, sunk=0.0, bed_mat=GSD):
    """A Heartwire run inlaid in a carved channel: dark channel bed, glowing wire, bronze clamps."""
    a, b = Vector(a), Vector(b)
    if bed:
        strip(k, a, b, n, w * 2.3, 0.035, bed_mat, off=-sunk, M=M)
    strip(k, a, b, n, w, 0.07, mat, off=-sunk, M=M)
    if clamps:
        d = b - a
        L = d.length
        dn = d / L
        m = max(1, int(L / clamps))
        for i in range(m):
            p = a + dn * (L * (i + 0.5) / m)
            strip(k, p - dn * 0.08, p + dn * 0.08, n, w * 1.9, 0.1, "BH_Brass", off=-sunk, M=M)


def wire_path(k, pts, n, **kw):
    for a, b in zip(pts[:-1], pts[1:]):
        wire_run(k, a, b, n, **kw)


def glyph(k, M, s=0.8, mat="BH_Glyph", frame_mat=GSD, d=0.05, frame=True):
    """Carved cartouche on a face whose outward normal is local -Y (centre at the local origin), with an abstract lit
    glyph of grid strokes (never lettering)."""
    r = k.r
    th = s * 0.11
    if frame:
        for (cx, cz, sx, sz) in ((0, s / 2 - th / 2, s, th), (0, -s / 2 + th / 2, s, th),
                                 (-s / 2 + th / 2, 0, th, s - 2 * th), (s / 2 - th / 2, 0, th, s - 2 * th)):
            k.put(box(sx, d * 1.7, sz, bev=0.01), frame_mat, M=M @ T(cx, -d * 0.85, cz))
    # a symmetric sigil: a random walk on the left half of a 5x5 grid, mirrored, plus a central mark
    g = (s - 2 * th) * 0.19
    sw = s * 0.075
    cur = (r.randint(-2, 0), r.randint(-2, 2))
    segs = []
    for i in range(r.randint(3, 4)):
        opts = [(cur[0] + dx, cur[1] + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if -2 <= cur[0] + dx <= 0 and abs(cur[1] + dz) <= 2]
        nxt = r.choice(opts)
        segs.append((cur, nxt))
        cur = nxt
    segs += [((-a_[0], a_[1]), (-b_[0], b_[1])) for (a_, b_) in segs]
    if r.random() < 0.5:
        segs.append(((0, -1), (0, 1)))
    else:
        segs.append(((0, 0), (0, 0)))
    for (a_, b_) in segs:
        ax, az, bx, bz = a_[0] * g, a_[1] * g, b_[0] * g, b_[1] * g
        k.put(box(abs(bx - ax) + sw, d, abs(bz - az) + sw), mat, M=M @ T((ax + bx) / 2, -d * 0.75, (az + bz) / 2))


def fret_band(k, x0, x1, zc, h, M=None, mat=GS, back=GSD, d=0.07, back_d=0.04, unit_cells=12):
    """Stepped-fret relief band on a face with outward normal local -Y: border strips and interlocking stepped teeth
    (one rising from the bottom border, one hanging from the top border per unit)."""
    M = M or T()
    L = x1 - x0
    ch = h / 5.0
    n = max(1, int(round(L / (unit_cells * ch))))
    cw = L / (n * unit_cells)
    z0 = zc - h / 2
    xm = (x0 + x1) / 2
    k.put(box(L, back_d, h), back, M=M @ T(xm, -back_d / 2, zc))
    yb = -back_d - d / 2
    for row in (0, 4):
        t = box(L, d, ch, bev=0.008)
        k.put(t, mat, M=M @ T(xm, yb, z0 + ch * (row + 0.5)))
    up_c, dn_c = unit_cells / 4.0, unit_cells * 3 / 4.0
    half = unit_cells // 4 - 1
    for u in range(n):
        for row in (1, 2, 3):
            fill = []
            for c in range(unit_cells):
                du = abs(c - up_c)
                dd = min(abs(c - dn_c), abs(c + unit_cells - dn_c))
                fill.append(du <= (3 - row) * half / 2.0 + 1e-6 or dd <= (row - 1) * half / 2.0 + 1e-6)
            c = 0
            while c < unit_cells:
                if not fill[c]:
                    c += 1
                    continue
                c0 = c
                while c < unit_cells and fill[c]:
                    c += 1
                ln = c - c0
                x = x0 + (u * unit_cells + c0 + ln / 2) * cw
                k.put(box(ln * cw, d, ch), mat, M=M @ T(x, yb, z0 + ch * (row + 0.5)))


def face_M(side, dist, z=0.0):
    """Frame for a vertical face of a centred box: side in 'front' (-Y), 'back' (+Y), 'left' (-X), 'right' (+X).
    The returned frame has its local -Y as the face's outward normal and local X along the face."""
    return {"front": T(0, -dist, z), "back": T(0, dist, z) @ R(0, 0, 180),
            "left": T(-dist, 0, z) @ R(0, 0, 90), "right": T(dist, 0, z) @ R(0, 0, -90)}[side]


def tier(k, w, d, z0, h, talus=0.42, inset=None, mat=GS, trim=GS, M=None, moss=True, chips=4, panel_mat=None):
    """Talus-and-panel tier: a sloped talus, then a vertical panel framed by a proud sill and cornice.
    Returns the top z."""
    r = k.r
    M = M or T()
    inset = inset if inset is not None else h * talus * 0.45
    zt = z0 + h * talus
    c = [(-w / 2, -d / 2, z0), (w / 2, -d / 2, z0), (w / 2, d / 2, z0), (-w / 2, d / 2, z0),
         (-w / 2 + inset, -d / 2 + inset, zt), (w / 2 - inset, -d / 2 + inset, zt),
         (w / 2 - inset, d / 2 - inset, zt), (-w / 2 + inset, d / 2 - inset, zt)]
    t = hexa(c, 0.05)
    chip(t, r, chips, min(w, d) * 0.02 + 0.1)
    jitter(t, r, 0.012)
    k.put(t, mat, M=M, mat_fn=mossy(k, 0.45, 0.6, 0.15) if moss else None)
    pw, pd = w - 2 * inset + 0.24, d - 2 * inset + 0.24
    ph = h - h * talus
    t = box(pw - 0.2, pd - 0.2, ph, bev=0.04)
    chip(t, r, 2, 0.08)
    k.put(t, panel_mat or mat, M=M @ T(0, 0, zt + ph / 2))
    for (zz, hh, grow) in ((zt + 0.1, 0.2, 0.0), (zt + ph - 0.15, 0.3, 0.08)):
        t = box(pw + grow, pd + grow, hh, bev=0.03)
        chip(t, r, chips, 0.1)
        jitter(t, r, 0.008)
        k.put(t, trim, M=M @ T(0, 0, zz), mat_fn=mossy(k, 0.8, 0.8, 0.0) if moss else None)
    return zt + ph


def coil(k, z, R_, h=1.0, turns=3, M=None, segs=28, core_mat="BH_Copper", flange="BH_Brass", wire="BH_Wire"):
    """A wound arc coil (bobbin) centred on the local Z axis: bronze flanges, copper drum, glowing windings."""
    M = M or T()
    for zz in (z - h / 2, z + h / 2):
        t = cyl(R_ + 0.18, 0.14, segs, bev=0.02)
        k.put(t, flange, M=M @ T(0, 0, zz - 0.07), smooth=30)
    k.put(cyl(R_ * 0.78, h, segs), core_mat, M=M @ T(0, 0, z - h / 2), smooth=30)
    rr = h / (turns * 2) * 0.82
    for i in range(turns):
        zz = z - h / 2 + h * (i + 0.5) / turns
        k.put(torus(R_ - rr * 0.3, rr, segs, 6), wire, M=M @ T(0, 0, zz), smooth=50)


def toroid_coil(k, z, R_, rb, turns, M=None, segs=28, body="BH_Copper", wire="BH_Wire", rw=0.045):
    """A copper ring (torus) hand-wound with a helical glowing wire, lying in the local XY plane at height z."""
    M = M or T()
    k.put(torus(R_, rb, segs, 8), body, M=M @ T(0, 0, z), smooth=50)
    n = turns * 7
    rr = rb + rw * 0.35
    pts = []
    for i in range(n):
        t = math.tau * i / n
        ph = turns * t
        rad = R_ + rr * math.cos(ph)
        pts.append((rad * math.cos(t), rad * math.sin(t), z + rr * math.sin(ph)))
    k.put(tube(pts, rw, 4, closed=True), wire, M=M, smooth=50)


def beam_(k, a, b, w, mat, h=None, M=None):
    """Square bar from a to b."""
    a, b = Vector(a), Vector(b)
    F, L, _ = frame_of(a, b, UP if abs((b - a).normalized().z) < 0.9 else Vector((1, 0, 0)))
    k.put(box(w, h or w, L, bev=0.01), mat, M=(M @ F) if M is not None else F)


def serpent_head(k, M, s=1.0, mat=GS, accent="BH_Turquoise", eye="BH_Jade", fang=GS, tongue="BH_LimePlasterRed",
                 plume_mat=None, gape=0.3, plumes=7, lower=True):
    """Feathered-serpent head, mouth open, facing local -Y; back of the skull at y=+0.6*s, bottom at z=0."""
    r = k.r

    def P(x, y, z):
        return (x * s, y * s, z * s)
    zu = 0.3 + gape  # upper jaw underside at the front
    up = [P(-0.5, -1.0, zu), P(0.5, -1.0, zu), P(0.62, 0.6, 0.42), P(-0.62, 0.6, 0.42),
          P(-0.4, -1.08, zu + 0.42), P(0.4, -1.08, zu + 0.42), P(0.6, 0.6, 1.12), P(-0.6, 0.6, 1.12)]
    hx(k, up, mat, M, bev=0.05 * s, chips=3, chipd=0.07 * s)
    if lower:
        lo = [P(-0.46, -0.9, 0.0), P(0.46, -0.9, 0.0), P(0.56, 0.6, 0.0), P(-0.56, 0.6, 0.0),
              P(-0.42, -0.92, 0.24), P(0.42, -0.92, 0.24), P(0.56, 0.6, 0.42), P(-0.56, 0.6, 0.42)]
        hx(k, lo, mat, M, bev=0.05 * s, chips=2, chipd=0.06 * s)
        # inside of the mouth (dark) and tongue
        k.put(box(0.8 * s, 1.1 * s, 0.1 * s), GSD, M=M @ T(0, -0.15 * s, 0.3 * s))
        k.put(box(0.18 * s, 0.9 * s, 0.05 * s), tongue, M=M @ TRS(0, -0.75 * s, 0.3 * s, -12, 0, 0))
        for sx in (-1, 1):
            k.put(box(0.07 * s, 0.3 * s, 0.05 * s), tongue, M=M @ TRS(sx * 0.07 * s, -1.25 * s, 0.2 * s, -12, 0, sx * 18))
            k.put(cyl(0.06 * s, 0.22 * s, 6, r2=0.0), fang, M=M @ T(sx * 0.34 * s, -0.8 * s, 0.22 * s))
    else:
        k.put(box(1.0 * s, 1.3 * s, 0.06 * s), GSD, M=M @ T(0, -0.2 * s, (zu + 0.03) * s))
    # fangs
    for sx in (-1, 1):
        k.put(cyl(0.08 * s, gape * 0.95 * s, 6, r2=0.0), fang, M=M @ T(sx * 0.36 * s, -0.92 * s, zu * s) @ R(180, 0, 0))
    # brow ridges with a stepped curl, eyes, nostril scrolls
    for sx in (-1, 1):
        k.put(box(0.3 * s, 0.6 * s, 0.16 * s, bev=0.02), mat, M=M @ TRS(sx * 0.5 * s, -0.1 * s, 1.08 * s, 0, sx * 8, 0))
        k.put(box(0.2 * s, 0.24 * s, 0.14 * s, bev=0.02), mat, M=M @ TRS(sx * 0.56 * s, -0.42 * s, 1.0 * s, 0, sx * 8, 0))
        k.put(ico(0.13 * s, 1), eye, M=M @ TRS(sx * 0.55 * s, -0.12 * s, 0.9 * s, s=(0.8, 1.2, 0.8)))
        k.put(torus(0.1 * s, 0.035 * s, 10, 4), mat, M=M @ TRS(sx * 0.22 * s, -1.0 * s, (zu + 0.42) * s, 70, 0, 0))
    # stepped scale ridges along the top (accent mosaic)
    for i in range(3):
        y = (0.35 - i * 0.38) * s
        k.put(box((1.0 - i * 0.12) * s, 0.16 * s, 0.07 * s), accent, M=M @ T(0, y, (1.1 - i * 0.07) * s + 0.03 * s))
    # plume collar behind the head
    if plumes:
        pm = plume_mat or mat
        for i in range(plumes):
            a = -75 + 150 * i / (plumes - 1)
            Lp = (0.95 + 0.25 * math.cos(math.radians(a))) * s
            wp = 0.32 * s
            out = [(-wp / 2, 0), (wp / 2, 0), (wp * 0.45, Lp * 0.72), (0, Lp), (-wp * 0.45, Lp * 0.72)]
            t = prism(out, 0.12 * s, bev=0.015 * s)
            k.put(t, pm if i % 2 == 0 else accent if accent else pm,
                  M=M @ T(0, 0.62 * s, 0.62 * s) @ R(0, a, 0) @ T(0, 0, 0.25 * s))


def wire_lamp(k, base, out_dir, z_bracket, M=None):
    """Bronze bracket from a wall carrying a copper wire cage around a glowing core. Returns the core position."""
    M = M or T()
    base = Vector(base)
    od = Vector(out_dir).normalized()
    tip = base + od * 0.8
    k.put(tube([base, base + od * 0.45 + Vector((0, 0, 0.12)), tip + Vector((0, 0, 0.05))], 0.06, 6), "BH_Brass",
          M=M, smooth=40)
    core = tip + Vector((0, 0, -0.35))
    k.put(ico(0.16, 1), "BH_Wire", M=M @ T(*core))
    for i in range(6):
        a = math.tau * i / 6
        pts = [tip + Vector((0, 0, -0.02)), core + Vector((math.cos(a) * 0.24, math.sin(a) * 0.24, 0.12)),
               core + Vector((math.cos(a) * 0.22, math.sin(a) * 0.22, -0.18)), core + Vector((0, 0, -0.34))]
        k.put(tube(pts, 0.018, 4), "BH_Copper", M=M, smooth=40)
    k.put(cyl(0.12, 0.1, 8), "BH_Brass", M=M @ T(*(tip + Vector((0, 0, -0.06)))))
    return M @ core


# ---------------------------------------------------------------------------------------------------------------
# THE BRIDGE OF DEATH
@asset("zr_bridge_span_8m", CAT)
def zr_bridge_span_8m(k):
    """Deck segment 8 m along Godot Z (Blender Y) x 12 m wide, deck top at the origin; tiles end to end."""
    r = k.r
    W, L = 12.0, 8.0
    HL = L / 2
    walk = 10.6
    # paving and the processional fret runner of turquoise mosaic down the middle
    for sx in (-1, 1):
        hw = (walk / 2 - 0.85)
        slab_floor(k, hw, L, 0.0, th=0.22, rows=(1.3, 2.0), lens=(1.4, 2.4), mat="BH_TerracePave", gap=0.05,
                   crack_p=0.3, sink=0.03, M=T(sx * (0.85 + hw / 2), 0, 0))
    blk(k, 1.7, L, 0.2, T(0, 0, -0.17), GSD, chips=0, bev=0.0, jit=0)
    Mrun = T(0, 0, -0.07) @ R(0, 0, 90) @ R(-90, 0, 0)
    fret_band(k, -HL, HL, 0.0, 1.6, M=Mrun, mat=GS, back="BH_Turquoise", d=0.04, back_d=0.035)
    # two Heartwire channels along the deck
    for x in (-2.7, 2.7):
        wire_run(k, (x, -HL, 0.0), (x, HL, 0.0), UP, w=0.2, clamps=2.0, sunk=0.05)
    # deck body with a stepped-fret fascia on both outer faces
    blk(k, W, L, 0.82, T(0, 0, -0.63), GS, chips=0)
    for sx, side in ((-1, "left"), (1, "right")):
        fret_band(k, -HL, HL, -0.6, 0.66, M=face_M(side, W / 2), mat=GS, back=GSD)
    # parapets: two courses of long blocks + capstones, glyph posts every 4 m (they tile)
    for sx in (-1, 1):
        xp = sx * (W / 2 - 0.35)
        Mp = T(xp, 0, 0) @ R(0, 0, 90)
        masonry(k, -HL, HL, 0.0, 0.92, 0.7, mat=GS, M=Mp, course=(0.42, 0.5), blen=(1.3, 2.1), core_mat=GSD,
                tint=(0.85, 1.0))
        capstones(k, -HL, HL, 0.92, 0.7, h=0.2, mat=GS, lens=(1.4, 2.2), M=Mp)
        for yp in (-2.0, 2.0):
            blk(k, 1.0, 1.0, 1.5, T(xp, yp, 0.75), GS, chips=2)
            blk(k, 1.2, 1.2, 0.18, T(xp, yp, 1.58), GS, chips=2, moss=(0.8, 1.0, -0.35))
            blk(k, 0.8, 0.8, 0.2, T(xp, yp, 1.76), GS, chips=1)
            k.put(box(0.5, 0.5, 0.04), "BH_Glyph", M=T(xp, yp, 1.875))
            k.put(box(0.2, 0.2, 0.06), GSD, M=T(xp, yp, 1.89))
            for side in ("left", "right"):
                glyph(k, T(xp, yp, 0.82) @ face_M(side, 0.5), s=0.62)
    # side girders under each edge: an inverted stepped profile, two blocks long per step
    for sx in (-1, 1):
        for i in range(4):
            xo = W / 2 - 0.2 - i * 0.6
            wdt = 1.7
            z1 = -1.04 - i * 1.0
            for yy in (-2.0, 2.0):
                blk(k, wdt, 3.96, 0.98, T(sx * (xo - wdt / 2), yy, z1 - 0.49), GS if i == 0 else GSD, chips=3,
                    chipd=0.14)
        # Heartwire along the girder's outer face (seen from the gorge)
        wire_run(k, (sx * (W / 2 - 0.2), -HL, -1.55), (sx * (W / 2 - 0.2), HL, -1.55), Vector((sx, 0, 0)), w=0.16,
                 clamps=2.0)
        # bronze straps binding the steps at y = +-2
        for yy in (-2.0, 2.0):
            for i in range(4):
                xo = W / 2 - 0.2 - i * 0.6
                strip(k, (sx * xo, yy, -1.04 - i * 1.0), (sx * xo, yy, -2.04 - i * 1.0), Vector((sx, 0, 0)), 0.36,
                      0.06, "BH_Brass")
    # cross diaphragm at y=0 (stepped inverted arch) and bronze tie rods with turnbuckles
    blk(k, 9.0, 0.9, 0.9, T(0, 0, -1.49), GSD, chips=2)
    for sx in (-1, 1):
        blk(k, 1.4, 0.9, 0.9, T(sx * 3.6, 0, -2.39), GSD, chips=2)
        blk(k, 0.8, 0.9, 0.9, T(sx * 3.2, 0, -3.29), GSD, chips=2)
    for yy in (-2.0, 2.0):
        k.put(tube([(-3.4, yy, -4.55), (3.4, yy, -4.55)], 0.09, 6), "BH_Brass", smooth=40)
        k.put(cyl(0.2, 0.8, 8), "BH_Brass", M=T(-0.4, yy, -4.55) @ R(0, 90, 0), smooth=30)
    for sgn in (-1, 1):
        k.put(tube([(-3.4, -HL + 0.3, -4.4), (3.4, HL - 0.3, -4.4)][::sgn], 0.07, 6), "BH_Brass", smooth=40)
    # collision: deck slab and the parapets (posts included)
    k.col_box(W, L, 1.04, T(0, 0, -0.52))
    for sx in (-1, 1):
        k.col_box(0.7, L, 1.5, T(sx * (W / 2 - 0.35), 0, 0.75))
    return dict(recenter=False)


@asset("zr_bridge_pylon", CAT)
def zr_bridge_pylon(k):
    """Ward pylon 16 m: stone mast ringed in bronze, glyph collar, three stacked arc coils, crown with the `arc`
    socket. Origin on top of its foundation; the foundation corbel hangs to -5 m."""
    r = k.r
    for i, (w, z0, z1) in enumerate(((4.4, -1.0, 0.0), (3.6, -2.2, -1.0), (2.8, -3.4, -2.2), (2.0, -5.0, -3.4))):
        blk(k, w, w, z1 - z0, T(0, 0, (z0 + z1) / 2), GS if i == 0 else GSD, chips=3, chipd=0.15)
    for sx in (-1, 1):
        wire_run(k, (sx * 2.2, -1.6, -0.5), (sx * 2.2, 1.6, -0.5), Vector((sx, 0, 0)), w=0.14, clamps=1.6)
    z = 0.0
    for (w, h) in ((4.0, 0.55), (3.3, 0.5), (2.6, 0.45)):
        blk(k, w, w, h, T(0, 0, z + h / 2), GS, chips=3, chipd=0.12, moss=(0.8, 0.9, 0.0))
        z += h
    # mast drums (tapering) separated by bronze rings
    drums = ((z, 4.6, 1.75, 1.6), (4.85, 7.3, 1.58, 1.45), (8.55, 10.1, 1.42, 1.32))
    for (z0, z1, w0, w1) in drums:
        c = [(-w0 / 2, -w0 / 2, z0), (w0 / 2, -w0 / 2, z0), (w0 / 2, w0 / 2, z0), (-w0 / 2, w0 / 2, z0),
             (-w1 / 2, -w1 / 2, z1), (w1 / 2, -w1 / 2, z1), (w1 / 2, w1 / 2, z1), (-w1 / 2, w1 / 2, z1)]
        hx(k, c, GS, bev=0.05, chips=3, chipd=0.1)
        for side, nrm in (("front", (0, -1, 0)), ("back", (0, 1, 0)), ("left", (-1, 0, 0)), ("right", (1, 0, 0))):
            nv = Vector(nrm)
            wire_run(k, nv * (w0 / 2) + Vector((0, 0, z0 + 0.15)), nv * (w1 / 2) + Vector((0, 0, z1 - 0.15)), nv,
                     w=0.13, clamps=1.2)
    for zb, wb in ((4.6, 1.8), (7.3, 1.62), (10.1, 1.45)):
        blk(k, wb + 0.14, wb + 0.14, 0.25, T(0, 0, zb + 0.125), "BH_Brass", chips=0, bev=0.03, jit=0)
    # glyph collar
    blk(k, 2.2, 2.2, 1.25, T(0, 0, 7.55 + 0.5), GS, chips=3)
    blk(k, 2.45, 2.45, 0.2, T(0, 0, 8.65), GS, chips=2, moss=(0.85, 1.0, 0.0))
    for side in ("front", "back", "left", "right"):
        glyph(k, face_M(side, 1.1, 8.05), s=0.85)
    # three arc coils: copper toroids hand-wound with Heartwire, clamped to the mast by bronze arms
    blk(k, 1.15, 1.15, 4.3, T(0, 0, 10.1 + 2.15), GSD, chips=2)
    for zc, Rc in ((10.85, 1.6), (12.1, 1.38), (13.3, 1.16)):
        toroid_coil(k, zc, Rc, 0.24, 20)
        blk(k, 1.5, 1.5, 0.28, T(0, 0, zc + 0.62), GS, chips=2, moss=(0.85, 1.0, 0.1))
        for i in range(4):
            a_ = math.tau * i / 4 + math.pi / 4
            beam_(k, (math.cos(a_) * 0.55, math.sin(a_) * 0.55, zc), (math.cos(a_) * (Rc - 0.1), math.sin(a_) * (Rc - 0.1), zc),
                  0.16, "BH_Brass")
    z = 14.4
    for (w, h) in ((1.7, 0.3), (1.3, 0.3)):
        blk(k, w, w, h, T(0, 0, z + h / 2), GS, chips=2)
        z += h
    for i in range(4):
        a_ = math.tau * i / 4
        pts = [(math.cos(a_) * 0.55, math.sin(a_) * 0.55, z), (math.cos(a_) * 0.7, math.sin(a_) * 0.7, z + 0.5),
               (math.cos(a_) * 0.32, math.sin(a_) * 0.32, z + 1.05)]
        k.put(tube(pts, 0.07, 6), "BH_Brass", smooth=40)
    k.put(ico(0.36, 2), "BH_Wire", M=T(0, 0, z + 0.62), smooth=60)
    k.put(cyl(0.05, 0.5, 6, r2=0.0), "BH_Brass", M=T(0, 0, z + 1.0))
    k.sockets.append(("arc", (0, 0, 15.9)))
    k.sockets.append(("light", (0, 0, 12.1)))
    k.col_box(4.0, 4.0, 1.5, T(0, 0, 0.75))
    k.col_box(1.8, 1.8, 13.5, T(0, 0, 1.5 + 6.75))
    return dict(recenter=False)


def merlons(k, x0, x1, y, z, n, h=1.1, w=0.7, d=0.7, mat=GS):
    """Row of stepped merlons along X at depth y, standing on z."""
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n if n > 1 else x0
        blk(k, w, d, h * 0.55, T(x, y, z + h * 0.275), mat, chips=1)
        blk(k, w * 0.6, d * 0.85, h * 0.45, T(x, y, z + h * 0.55 + h * 0.225), mat, chips=1, moss=(0.85, 1.2, 0.0))


@asset("zr_bridge_gatehouse", CAT)
def zr_bridge_gatehouse(k):
    """Monumental gatehouse, 20 m wide, 14 m tall, a 10 m passage along Godot Z (floor at y=0, origin)."""
    r = k.r
    # passage floor continuing the bridge deck: paving, fret runner and the two Heartwire channels
    for sx in (-1, 1):
        slab_floor(k, 4.15, 10.0, 0.0, th=0.22, rows=(1.3, 2.0), lens=(1.4, 2.4), mat="BH_TerracePave", gap=0.05,
                   crack_p=0.3, sink=0.03, M=T(sx * (0.85 + 4.15 / 2), 0, 0))
    blk(k, 20.0, 10.0, 0.5, T(0, 0, -0.47), GSD, chips=0)
    Mrun = T(0, 0, -0.07) @ R(0, 0, 90) @ R(-90, 0, 0)
    fret_band(k, -5.0, 5.0, 0.0, 1.6, M=Mrun, mat=GS, back="BH_Turquoise", d=0.04, back_d=0.035)
    for x in (-2.7, 2.7):
        wire_run(k, (x, -5.0, 0.0), (x, 5.0, 0.0), UP, w=0.2, clamps=2.0, sunk=0.05)
    tiers = ((5.0, 10.0, 0.0, 6.0, 0.4, 0.6), (3.8, 8.6, 6.0, 3.8, 0.35, 0.45), (3.0, 7.6, 9.8, 2.0, 0.35, 0.35))
    ztop = 11.8
    for sx in (-1, 1):
        cx = sx * 7.5
        for (w, d, z0, h, ta, ins) in tiers:
            tier(k, w, d, z0, h, talus=ta, inset=ins, M=T(cx, 0, 0), chips=5, moss=z0 < 9.0)
        # merlons on the tower crowns (front and back edges, and the outer side)
        for yy in (-3.3, 3.3):
            merlons(k, cx - 1.1, cx + 1.1, yy, ztop, 3, h=1.2, w=0.62, d=0.62)
        # ward finial: a hand-wound coil on a bronze tripod over a stepped plinth
        blk(k, 1.8, 1.8, 0.4, T(cx, 0, ztop + 0.2), GS, chips=2)
        blk(k, 1.2, 1.2, 0.3, T(cx, 0, ztop + 0.55), GS, chips=1)
        for i in range(3):
            a_ = math.tau * i / 3 + 0.5
            k.put(tube([(cx + math.cos(a_) * 0.5, math.sin(a_) * 0.5, ztop + 0.7),
                        (cx + math.cos(a_) * 0.82, math.sin(a_) * 0.82, ztop + 1.2),
                        (cx + math.cos(a_) * 0.7, math.sin(a_) * 0.7, ztop + 1.62)], 0.06, 5), "BH_Brass", smooth=40)
        toroid_coil(k, ztop + 1.62, 0.78, 0.15, 13, M=T(cx, 0, 0), segs=20)
        k.put(ico(0.3, 2), "BH_Wire", M=T(cx, 0, ztop + 1.62), smooth=60)
        k.put(cyl(0.04, 0.55, 5, r2=0.0), "BH_Brass", M=T(cx, 0, ztop + 1.85))
        for face_y in (-1, 1):
            rot = R(0, 0, 0) if face_y < 0 else R(0, 0, 180)
            # tier-1 panel: a big glyph cartouche; tier-2 panel: a stepped-fret band; Heartwire along both cornices
            yf1 = face_y * (10.0 / 2 - 0.6 + 0.12 - 0.1)
            yf2 = face_y * (8.6 / 2 - 0.45 + 0.12 - 0.1)
            glyph(k, T(cx + sx * 0.35, yf1, 4.15) @ rot, s=1.7, d=0.08)
            fret_band(k, -1.55, 1.55, 8.85, 1.25, M=T(cx, yf2, 0) @ rot, mat=GS, back=GSD)
            wire_run(k, (cx - 2.0, yf1, 5.55), (cx + 2.0, yf1, 5.55), Vector((0, face_y, 0)), w=0.16, clamps=1.4)
            wire_run(k, (cx - 1.55, yf2, 7.95), (cx + 1.55, yf2, 7.95), Vector((0, face_y, 0)), w=0.14, clamps=1.4)
            # vertical Heartwire on the passage-side edge of the tower faces
            xe = cx - sx * 1.55
            wire_run(k, (xe, yf1, 2.75), (xe, yf1, 5.4), Vector((0, face_y, 0)), w=0.14, clamps=1.0)
            wire_run(k, (xe + sx * 0.2, yf2, 7.45), (xe + sx * 0.2, yf2, 9.6), Vector((0, face_y, 0)), w=0.14, clamps=1.0)
            # serpent-head balustrade end on a pedestal beside the passage mouth
            yh = face_y * 5.0
            blk(k, 1.9, 2.8, 0.9, T(sx * 5.9, yh + face_y * 1.1, 0.45), GS, chips=3, moss=(0.8, 1.0, -0.2))
            serpent_head(k, T(sx * 5.9, yh + face_y * 0.75, 0.9) @ rot, s=1.45, accent="BH_LimePlasterRed", gape=0.34)
    # the great lintel and its fret, Heartwire under the fret
    blk(k, 14.0, 7.6, 2.3, T(0, 0, 8.25 + 1.15), GS, chips=6, chipd=0.18)
    for face_y in (-1, 1):
        rot = R(0, 0, 0) if face_y < 0 else R(0, 0, 180)
        fret_band(k, -5.6, 5.6, 9.75, 1.1, M=T(0, face_y * 3.8, 0) @ rot, mat=GS, back="BH_LimePlasterRed")
        wire_run(k, (-5.6, face_y * 3.8, 8.75), (5.6, face_y * 3.8, 8.75), Vector((0, face_y, 0)), w=0.2, clamps=1.4)
    # underside of the lintel: bronze ward-bars
    for x in (-3.0, 0.0, 3.0):
        strip(k, (x, -3.6, 8.25), (x, 3.6, 8.25), DOWN, 0.4, 0.12, "BH_Brass")
    # roof comb carrying the Ward roundel
    zc = 10.55
    blk(k, 9.4, 1.4, 0.5, T(0, 0, zc + 0.25), GS, chips=3)
    for (w, z0, h) in ((8.4, zc + 0.5, 1.2), (6.4, zc + 1.7, 1.0), (4.2, zc + 2.7, 0.8)):
        for sx in (-1, 1):
            blk(k, 1.0, 1.0, h, T(sx * (w / 2 - 0.5), 0, z0 + h / 2), GS, chips=2)
        blk(k, w, 1.0, 0.36, T(0, 0, z0 + h - 0.18), GS, chips=2, moss=(0.85, 1.0, 0.1))
    blk(k, 2.0, 1.0, 0.45, T(0, 0, zc + 3.5 + 0.22), GS, chips=2)
    for face_y in (-1, 1):
        rot = 90 if face_y < 0 else -90
        k.put(cyl(1.55, 0.5, 20, bev=0.04), GS, M=T(0, face_y * 0.3, 12.05) @ R(rot, 0, 0))
        k.put(cyl(1.15, 0.6, 20), GSD, M=T(0, face_y * 0.3, 12.05) @ R(rot, 0, 0))
        k.put(ico(0.42, 2), "BH_Wire", M=T(0, face_y * 0.85, 12.05), smooth=60)
        for i in range(12):
            a = math.tau * i / 12
            p = Vector((math.cos(a) * 1.33, face_y * 0.62, 12.05 + math.sin(a) * 1.33))
            k.put(box(0.3, 0.1, 0.16), "BH_Glyph", M=T(*p) @ R(0, -math.degrees(a), 0))
        for i in range(4):
            a = math.tau * i / 4 + math.pi / 4
            p0 = Vector((math.cos(a) * 0.4, face_y * 0.78, 12.05 + math.sin(a) * 0.4))
            p1 = Vector((math.cos(a) * 1.05, face_y * 0.7, 12.05 + math.sin(a) * 1.05))
            strip(k, p0, p1, Vector((0, face_y, 0)), 0.1, 0.06, "BH_Wire")
    # wire lamps flanking the passage mouth (front)
    la = wire_lamp(k, (-5.3, -4.52, 4.9), (0.35, -1, 0), 4.9)
    lb = wire_lamp(k, (5.3, -4.52, 4.9), (-0.35, -1, 0), 4.9)
    k.sockets.append(("light_a", tuple(la)))
    k.sockets.append(("light_b", tuple(lb)))
    # collision: floor, towers, lintel, serpent pedestals
    k.col_box(20.0, 10.0, 0.5, T(0, 0, -0.25))
    for sx in (-1, 1):
        k.col_box(5.0, 10.0, 11.8, T(sx * 7.5, 0, 5.9))
        for face_y in (-1, 1):
            k.col_box(1.9, 2.9, 2.6, T(sx * 5.9, face_y * 6.4, 1.3))
    k.col_box(14.0, 7.6, 2.3, T(0, 0, 9.4))
    return dict(recenter=False)


@asset("zr_bridge_pier", CAT)
def zr_bridge_pier(k):
    """Support column 6 x 6 m, 45 m tall, origin at the top centre (all geometry below y=0)."""
    r = k.r
    H = 45.0
    # stepped capital (wider across the bridge to catch both girders)
    blk(k, 8.6, 7.0, 1.0, T(0, 0, -0.5), GS, chips=4, chipd=0.2)
    blk(k, 7.6, 6.6, 1.0, T(0, 0, -1.5), GS, chips=4, chipd=0.2)
    blk(k, 6.8, 6.4, 0.6, T(0, 0, -2.3), GSD, chips=3, chipd=0.2)
    for face in ("front", "back"):
        fret_band(k, -4.3, 4.3, -0.5, 0.8, M=face_M(face, 3.5), mat=GS, back=GSD)
    # shaft core, string courses, corner quoins
    blk(k, 6.0, 6.0, H - 6.6, T(0, 0, -2.6 - (H - 6.6) / 2), GS, chips=0)
    courses = [-8.5, -16.0, -23.5, -31.0, -38.5]
    for zc in courses:
        blk(k, 6.5, 6.5, 0.55, T(0, 0, zc), GS, chips=5, chipd=0.15, moss=(0.85, 1.0, 0.2))
    z = -2.6
    i = 0
    while z > -40.4:
        h = r.uniform(1.6, 2.1)
        long_x = i % 2 == 0
        for sx in (-1, 1):
            for sy in (-1, 1):
                lx, ly = (1.5, 0.9) if long_x else (0.9, 1.5)
                blk(k, lx, ly, h - 0.05, T(sx * (3.0 - lx / 2 + 0.06), sy * (3.0 - ly / 2 + 0.06), z - h / 2), GS,
                    chips=r.randint(1, 2), chipd=0.12, bev=0.05)
        z -= h
        i += 1
    # Heartwire channels down the middle of each face, broken at the string courses
    for side, nrm in (("front", (0, -1, 0)), ("back", (0, 1, 0)), ("left", (-1, 0, 0)), ("right", (1, 0, 0))):
        nv = Vector(nrm)
        stops = [-2.6] + courses + [-40.5]
        for z0, z1 in zip(stops[:-1], stops[1:]):
            wire_run(k, nv * 3.0 + Vector((0, 0, z0 - 0.4)), nv * 3.0 + Vector((0, 0, z1 + 0.4)), nv, w=0.2,
                     clamps=2.2)
        # glyph cartouches above every second string course
        for zc in courses[::2]:
            M = face_M(side, 3.0, zc + 1.6)
            glyph(k, M @ T(-1.3, 0, 0), s=1.3, d=0.07)
            glyph(k, M @ T(1.3, 0, 0), s=1.3, d=0.07)
    # Heartwire cables sagging between the corners under the upper string courses
    for zc in courses[:2]:
        for (a, b) in (((-3.1, -3.1), (3.1, -3.1)), ((3.1, -3.1), (3.1, 3.1)), ((3.1, 3.1), (-3.1, 3.1)),
                       ((-3.1, 3.1), (-3.1, -3.1))):
            pts = []
            for j in range(9):
                t = j / 8
                x = a[0] + (b[0] - a[0]) * t
                y = a[1] + (b[1] - a[1]) * t
                n = Vector((x, y, 0)).normalized() * 0.18
                pts.append((x + n.x, y + n.y, zc - 0.35 - 1.3 * math.sin(math.pi * t)))
            k.put(tube(pts, 0.07, 5), "BH_Wire", smooth=50)
            k.put(cyl(0.16, 0.3, 6), "BH_Brass", M=T(a[0], a[1], zc - 0.5))
    # foot: flared, broken, rooted into raw rock
    blk(k, 6.8, 6.8, 2.0, T(0, 0, -41.6), GSD, chips=6, chipd=0.4)
    for i in range(6):
        a = math.tau * i / 6 + r.uniform(-0.3, 0.3)
        rock_piece(k, (r.uniform(2.0, 3.0), r.uniform(1.6, 2.4), r.uniform(1.6, 2.4)), 160,
                   pos=(math.cos(a) * 3.6, math.sin(a) * 3.6, -H), rz=r.uniform(0, 360), mat="BH_CliffOchre", moss=False)
    k.col_box(8.6, 7.0, 2.6, T(0, 0, -1.3))
    k.col_box(6.4, 6.4, H - 2.6, T(0, 0, -2.6 - (H - 2.6) / 2))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# JUNGLE FLORA (leaves are real two-sided geometry, so no alpha cards are needed)
def leaf(k, base, d, L, W, droop=0.3, fold=0.12, mat="BH_JungleLeaf", n=4, roll=0.0, zig=0.0, heart=0.0, M=None,
         thick=0.012):
    """One broad leaf: a V-folded blade along a drooping midrib, both sides modelled. base/d in local space."""
    from mathutils import Quaternion
    base, d = Vector(base), Vector(d).normalized()
    side = d.cross(UP)
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    if roll:
        side.rotate(Quaternion(d, roll))
    nrm = side.cross(d).normalized()
    t = tb()
    top, bot = [], []
    for i in range(n + 1):
        s = i / n
        p = base + d * (L * s) + DOWN * (droop * L * s * s)
        w = W * (math.sin(math.pi * min(1.0, s * 0.94 + 0.03)) ** 0.75)
        if heart and s < 0.3:
            w = max(w, W * heart)
        if zig and 0 < i < n:
            w *= (1 + zig) if i % 2 else (1 - zig * 0.6)
        lv = p - side * (w / 2) - nrm * (fold * w)
        rv = p + side * (w / 2) - nrm * (fold * w)
        top.append([t.verts.new(lv), t.verts.new(p), t.verts.new(rv)])
        off = -nrm * thick
        bot.append([t.verts.new(lv + off), t.verts.new(p + off), t.verts.new(rv + off)])
    for i in range(n):
        a, b = top[i], top[i + 1]
        t.faces.new((a[0], a[1], b[1], b[0]))
        t.faces.new((a[1], a[2], b[2], b[1]))
        a, b = bot[i], bot[i + 1]
        t.faces.new((b[0], b[1], a[1], a[0]))
        t.faces.new((b[1], b[2], a[2], a[1]))
    k.put(t, mat, M=M, smooth=70)


def clump(k, ctr, rad, flat=0.5, mat="BH_JungleLeaf", leaves=7, lsize=1.0, M=None):
    """Foliage mass: a flattened noisy blob fringed with drooping leaves (reads as a canopy layer from above)."""
    r = k.r
    ctr = Vector(ctr)
    t = ico(1.0, 2)
    for v in t.verts:
        v.co = Vector((v.co.x * rad, v.co.y * rad, v.co.z * rad * flat))
    ndisp(t, 1.4 / rad, rad * 0.22, k.noff + ctr * 0.3)
    k.put(t, mat, M=(M or T()) @ T(*ctr), smooth=70)
    for i in range(leaves):
        a = math.tau * i / leaves + r.uniform(-0.3, 0.3)
        d = Vector((math.cos(a), math.sin(a), r.uniform(-0.25, 0.15)))
        p = ctr + Vector((math.cos(a) * rad * 0.8, math.sin(a) * rad * 0.8, r.uniform(-0.2, 0.25) * rad * flat))
        leaf(k, p, d, r.uniform(0.9, 1.3) * lsize, r.uniform(0.45, 0.6) * lsize, droop=0.35, n=3, M=M,
             roll=r.uniform(-0.4, 0.4))


def pinnate(k, base, d, L, ll, pairs, droop=0.45, lw=0.13, hang=0.55, mat="BH_JungleLeaf", rach=0.035, M=None):
    """Feather frond: a drooping rachis with pairs of narrow leaflets hanging in a V (both sides modelled)."""
    base, d = Vector(base), Vector(d).normalized()
    n = 8
    pts = [base + d * (L * i / n) + DOWN * (droop * L * (i / n) ** 2) for i in range(n + 1)]
    k.put(tube(pts, [rach * (1 - 0.7 * i / n) for i in range(n + 1)], 3), mat, M=M, smooth=50)
    side0 = d.cross(UP)
    if side0.length < 1e-3:
        side0 = Vector((1, 0, 0))
    side0.normalize()
    t = tb()
    for j in range(pairs):
        s = 0.12 + 0.85 * j / max(1, pairs - 1)
        fi = s * n
        i0 = min(int(fi), n - 1)
        p = pts[i0].lerp(pts[i0 + 1], fi - i0)
        tg = (pts[i0 + 1] - pts[i0]).normalized()
        sd = tg.cross(UP)
        sd = sd.normalized() if sd.length > 1e-3 else side0
        lenj = ll * (math.sin(math.pi * (0.15 + 0.8 * s)) ** 0.6)
        for sg in (-1, 1):
            dirv = (sd * sg * 0.8 + tg * 0.45 + DOWN * hang).normalized()
            wv = tg * (lw / 2)
            q = p + dirv * lenj
            nn = dirv.cross(wv).normalized() * 0.01
            a0, a1, b0, b1 = p - wv, p + wv, q - wv * 0.3, q + wv * 0.3
            vs = [t.verts.new(v) for v in (a0, a1, b1, b0)]
            ws = [t.verts.new(v + nn) for v in (a0, a1, b1, b0)]
            t.faces.new(vs)
            t.faces.new(ws[::-1])
    k.put(t, mat, M=M, smooth=None)


@asset("zr_tree_ceiba", CAT)
def zr_tree_ceiba(k):
    """Giant buttressed jungle tree ~16 m: pale bottle trunk, plank buttress fins, an umbrella crown, hanging vines."""
    r = k.r
    top = Vector((0.35, 0.2, 10.8))
    pts = [Vector((0, 0, -0.3))]
    rad = [1.75, 1.85, 1.7, 1.42, 1.15, 0.95, 0.8, 0.7]
    for i in range(1, 8):
        s = i / 7
        pts.append(Vector((top.x * s * s, top.y * s * s, -0.3 + (top.z + 0.3) * s)))
    k.put(tube(pts, rad, 12, cap_start=False, uv_tile=1.5), "BH_Bark", uv="keep", smooth=60)
    # buttress fins
    nf = 7
    for i in range(nf):
        a = math.tau * i / nf + r.uniform(-0.25, 0.25)
        R0 = r.uniform(4.0, 5.4)
        Hf = r.uniform(4.6, 6.2)
        ph = r.uniform(0, 6)
        topc = []
        for j in range(7):
            u = j / 6
            topc.append((1.3 + (R0 - 1.3) * u, Hf * (1 - u) ** 2.1 + 0.12))
        outline = topc + [(x, -0.3) for (x, _) in topc[::-1]]
        t = prism(outline[::-1], r.uniform(0.34, 0.46))
        for v in t.verts:
            v.co.y += math.sin(v.co.x * 0.85 + ph) * 0.38 * (v.co.x / R0)
        k.put(t, "BH_Bark", M=R(0, 0, math.degrees(a)), smooth=45)
        # surface root continuing from the fin
        d0 = Vector((math.cos(a), math.sin(a), 0))
        sd = Vector((-d0.y, d0.x, 0))
        rp = [d0 * (R0 - 0.3) + Vector((0, 0, 0.05))]
        for j in range(1, 4):
            rp.append(d0 * (R0 + j * r.uniform(0.6, 0.9)) + sd * r.uniform(-0.5, 0.5) + Vector((0, 0, -0.05 * j)))
        k.put(tube(rp, [0.2, 0.15, 0.1, 0.05], 6), "BH_Bark", smooth=50)
    # limbs and canopy
    limbs = 6
    ends = []
    for i in range(limbs):
        a = math.tau * i / limbs + r.uniform(-0.3, 0.3)
        L = r.uniform(5.0, 7.0)
        el = math.radians(r.uniform(12, 28))
        z0 = top.z - r.uniform(0.0, 1.0)
        d = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
        p0 = Vector((top.x, top.y, z0))
        lp = [p0, p0 + d * L * 0.35 + Vector((0, 0, 0.5)), p0 + d * L * 0.7 + Vector((0, 0, 0.6)), p0 + d * L]
        k.put(tube(lp, [0.5, 0.36, 0.24, 0.14], 8), "BH_Bark", smooth=55)
        ends.append((lp[-1], d))
        # one sub-branch
        sa = a + r.choice((-1, 1)) * r.uniform(0.5, 0.9)
        sd_ = Vector((math.cos(sa), math.sin(sa), 0.25)).normalized()
        sp = lp[2]
        e = sp + sd_ * r.uniform(2.2, 3.2)
        k.put(tube([sp, sp + sd_ * 1.2 + Vector((0, 0, 0.2)), e], [0.18, 0.12, 0.07], 6), "BH_Bark", smooth=50)
        ends.append((e, sd_))
    for (p, d) in ends:
        clump(k, p + Vector((0, 0, 0.6)), r.uniform(2.4, 3.1), flat=0.3, leaves=6, lsize=1.3)
    clump(k, top + Vector((0, 0, 2.2)), 3.6, flat=0.32, leaves=8, lsize=1.4)
    for i in range(5):
        a = math.tau * i / 5 + 0.6
        clump(k, top + Vector((math.cos(a) * 3.3, math.sin(a) * 3.3, 1.2)), r.uniform(2.0, 2.5), flat=0.3,
              leaves=0)
    # hanging vines
    for i in range(9):
        (p, d) = ends[i % len(ends)]
        base = p - d * r.uniform(1.0, 2.5) + Vector((0, 0, -0.1))
        Lv = r.uniform(3.5, 7.5)
        vp = [base + Vector((math.sin(j * 1.3 + i) * 0.15, math.cos(j * 1.1 + i) * 0.15, -Lv * j / 4)) for j in range(5)]
        k.put(tube(vp, 0.045, 4), "BH_JungleLeaf", smooth=50)
        leaf(k, vp[-1], Vector((r.uniform(-1, 1), r.uniform(-1, 1), -0.6)), 0.5, 0.3, droop=0.2, n=2)
        leaf(k, vp[2], Vector((r.uniform(-1, 1), r.uniform(-1, 1), -0.2)), 0.45, 0.28, droop=0.2, n=2)
    k.col_mesh(cyl(1.9, 7.0, 10))
    return dict(recenter=False)


@asset("zr_palm", CAT)
def zr_palm(k):
    """Leaning ringed palm ~7 m with a drooping crown of feathery fronds and a coconut cluster."""
    r = k.r
    top = Vector((1.1, 0.3, 6.6))
    pts, rads = [], []
    for i in range(15):
        s = i / 14
        pts.append(Vector((top.x * s ** 1.8, top.y * s ** 1.8, top.z * s - 0.15 * (1 - s))))
        rads.append((0.26 - 0.09 * s) * (1.07 if i % 2 else 0.97) + (0.12 * (1 - s) ** 6))
    k.put(tube(pts, rads, 8, cap_start=False), "BH_Bark", smooth=50)
    for i in range(5):
        a = math.tau * i / 5 + 0.3
        k.put(cyl(0.12, 0.6, 5, r2=0.02), "BH_Bark", M=T(*top) @ R(0, 0, math.degrees(a)) @ R(0, 70, 0) @ T(0, 0, -0.1))
    nf = 11
    for i in range(nf):
        a = math.tau * i / nf + r.uniform(-0.15, 0.15)
        el = r.uniform(5, 40)
        d = Vector((math.cos(a) * math.cos(math.radians(el)), math.sin(a) * math.cos(math.radians(el)),
                    math.sin(math.radians(el))))
        pinnate(k, top + Vector((0, 0, 0.15)), d, r.uniform(3.0, 3.6), r.uniform(0.85, 1.05), 15, droop=0.45,
                lw=0.15, hang=0.7)
    for i in range(6):
        a = math.tau * i / 6
        k.put(ico(0.14, 1), "BH_WoodDark", M=T(top.x + math.cos(a) * 0.22, top.y + math.sin(a) * 0.22,
                                               top.z - 0.2 - (i % 2) * 0.14))
    M, L, _ = frame_of(pts[0], pts[9], Vector((1, 0, 0)))
    k.col_mesh(cyl(0.3, L, 6), M @ T(0, 0, -L / 2))
    return dict(recenter=False)


@asset("zr_fern_giant", CAT, col=False)
def zr_fern_giant(k):
    """Tree fern ~2.5 m: a short shaggy trunk and a crown of arching pinnate fronds."""
    r = k.r
    k.put(tube([(0, 0, -0.1), (0.06, 0.02, 0.75), (0.12, 0.06, 1.55)], [0.26, 0.21, 0.17], 7), "BH_Bark", smooth=50)
    for i in range(14):
        a = math.tau * i / 7 + (i // 7) * 0.45
        k.put(cyl(0.05, 0.3, 4, r2=0.0), "BH_Bark",
              M=T(math.cos(a) * 0.18, math.sin(a) * 0.18, 0.25 + (i % 5) * 0.25) @ R(0, 0, math.degrees(a)) @ R(0, 110, 0))
    tp = Vector((0.12, 0.06, 1.55))
    n = 13
    for i in range(n):
        a = math.tau * i / n + r.uniform(-0.15, 0.15)
        el = r.uniform(45, 70)
        d = Vector((math.cos(a) * math.cos(math.radians(el)), math.sin(a) * math.cos(math.radians(el)),
                    math.sin(math.radians(el))))
        pinnate(k, tp, d, r.uniform(1.75, 2.1), r.uniform(0.38, 0.46), 12, droop=0.62, lw=0.12, hang=0.25,
                rach=0.025)
    for i in range(2):
        a = math.tau * i / 2 + 0.7
        k.put(torus(0.07, 0.025, 8, 4), "BH_JungleLeaf", M=T(tp.x + math.cos(a) * 0.12, tp.y + math.sin(a) * 0.12, tp.z + 0.3) @ R(90, 0, math.degrees(a)))
    return dict(recenter=False)


@asset("zr_agave", CAT, col=False)
def zr_agave(k):
    """Agave rosette ~1.5 m of thick, pointed blue-green leaves."""
    r = k.r
    n = 24
    for i in range(n):
        a = i * 2.39996 + r.uniform(-0.1, 0.1)
        el = 78 - 55 * (i / n) + r.uniform(-6, 6)
        L = 1.45 - 0.55 * (i / n) + r.uniform(-0.1, 0.1)
        d = Vector((math.cos(a) * math.cos(math.radians(el)), math.sin(a) * math.cos(math.radians(el)),
                    math.sin(math.radians(el))))
        pts = [d * L * s + Vector((0, 0, 0.05)) + Vector((0, 0, -0.18 * L * s * s * (1 - el / 90.0))) for s in (0, 0.35, 0.7, 1.0)]
        t = tube(pts, [0.11, 0.1, 0.06, 0.0], 3, flat=(1.0, 0.45))
        k.put(t, "BH_Feather", smooth=40)
    k.put(ico(0.2, 1), "BH_Feather", M=T(0, 0, 0.12), smooth=40)
    return dict(recenter=False)


@asset("zr_bush_jungle", CAT, col=False)
def zr_bush_jungle(k):
    """Jungle undergrowth ~1.8 m: broad heart-shaped leaves on long stalks over a low leafy mass."""
    r = k.r
    clump(k, (0, 0, 0.3), 0.75, flat=0.6, leaves=7, lsize=0.8)
    for i in range(14):
        a = i * 2.39996 + r.uniform(-0.2, 0.2)
        h = r.uniform(0.7, 1.55)
        out = r.uniform(0.25, 0.75)
        tip = Vector((math.cos(a) * out, math.sin(a) * out, h))
        k.put(tube([(0, 0, 0.05), (math.cos(a) * out * 0.3, math.sin(a) * out * 0.3, h * 0.6), tip], 0.025, 4),
              "BH_JungleLeaf", smooth=50)
        d = Vector((math.cos(a), math.sin(a), r.uniform(0.1, 0.45)))
        leaf(k, tip, d, r.uniform(0.85, 1.15), r.uniform(0.65, 0.85), droop=0.45, n=5, heart=0.75, fold=0.1,
             roll=r.uniform(-0.3, 0.3))
    return dict(recenter=False)


@asset("zr_vine_curtain", CAT, col=False)
def zr_vine_curtain(k):
    """4 m curtain of hanging vines for a ruin wall. The wall face is the y=0 plane (Godot z=0); the vines hang in
    front of it (toward Godot +Z) from a mossy roll at 4.1 m down to near the ground. Origin bottom centre."""
    r = k.r
    rp = [Vector((-2.1 + 4.2 * i / 8, -0.18 + math.sin(i * 1.7) * 0.05, 4.1 + math.sin(i * 2.3) * 0.08)) for i in range(9)]
    k.put(tube(rp, 0.2, 6), "BH_Moss", smooth=50)
    for i in range(7):
        clump(k, (-1.8 + 3.6 * i / 6 + r.uniform(-0.2, 0.2), -0.32, 4.15), r.uniform(0.32, 0.45), flat=0.6, leaves=4,
              lsize=0.45)
    for i in range(18):
        x = -1.95 + 3.9 * (i + r.uniform(0.1, 0.9)) / 18
        Lv = r.uniform(1.6, 3.95)
        ph = r.uniform(0, 6)
        vp = [Vector((x + math.sin(ph + j) * 0.06, -0.2 - 0.18 * math.sin(math.pi * j / 6) - r.uniform(0, 0.05),
                      4.05 - Lv * j / 6)) for j in range(7)]
        k.put(tube(vp, 0.03, 3), "BH_JungleLeaf", smooth=50)
        for j in range(1, 7, 2):
            p = vp[j]
            sx = r.choice((-1, 1))
            leaf(k, p, Vector((sx * 0.7, -0.6, -0.4)), r.uniform(0.22, 0.32), r.uniform(0.15, 0.22), droop=0.15, n=2)
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# OVERGROWN WIREWRIGHT RUINS (Coilwood)
def moss_cap(k, p, s, flat=0.35):
    t = ico(1.0, 1)
    for v in t.verts:
        v.co = Vector((v.co.x * s, v.co.y * s * 0.8, max(v.co.z, -0.3) * s * flat))
    ndisp(t, 2.0 / s, s * 0.15, k.noff + Vector(p))
    k.put(t, "BH_Moss", M=T(*p), smooth=60)


def hang_vines(k, x0, x1, ztop, y, n, lmax=2.0):
    r = k.r
    for i in range(n):
        x = x0 + (x1 - x0) * (i + r.uniform(0.1, 0.9)) / n
        Lv = r.uniform(0.6, lmax)
        vp = [Vector((x + math.sin(i + j) * 0.04, y - 0.05 - 0.06 * math.sin(math.pi * j / 4), ztop - Lv * j / 4))
              for j in range(5)]
        k.put(tube(vp, 0.025, 3), "BH_JungleLeaf", smooth=50)
        leaf(k, vp[-1], Vector((r.uniform(-0.5, 0.5), -0.6, -0.5)), 0.28, 0.18, droop=0.1, n=2)
        leaf(k, vp[2], Vector((r.uniform(-0.5, 0.5), -0.6, -0.3)), 0.25, 0.16, droop=0.1, n=2)


def chain_links(k, a, b, R_=0.12, r_=0.032, mat="BH_Iron", segs=5):
    a, b = Vector(a), Vector(b)
    d = b - a
    pitch = R_ * 2.15
    n = max(1, int(d.length / pitch))
    A = align_z(d)
    for i in range(n):
        p = a + d.normalized() * (pitch * (i + 0.5))
        k.put(torus(R_, r_, segs, 3), mat, M=T(*p) @ A @ R(0, 0, 90 * (i % 2)) @ R(90, 0, 0) @ S(1, 1.55, 1))


def chain_path(k, pts, **kw):
    for a, b in zip(pts[:-1], pts[1:]):
        chain_links(k, a, b, **kw)


def rune_spike(k, base, lean_dir, H=2.5, w=0.4, M=None):
    """Kharvenn rune-spike: a square iron stake with a heavy collar and ring, violet-red runes along it."""
    M = M or T()
    ld = Vector(lean_dir)
    A = T(*Vector(base)) @ align_z(Vector((0, 0, 1)) + ld * 0.18)
    t = hexa([(-w * 0.22, -w * 0.22, -0.6), (w * 0.22, -w * 0.22, -0.6), (w * 0.22, w * 0.22, -0.6), (-w * 0.22, w * 0.22, -0.6),
              (-w / 2, -w / 2, H - 0.35), (w / 2, -w / 2, H - 0.35), (w / 2, w / 2, H - 0.35), (-w / 2, w / 2, H - 0.35)], 0.02)
    k.put(t, "BH_Iron", M=M @ A)
    k.put(box(w * 1.45, w * 1.45, 0.24, bev=0.03), "BH_Iron", M=M @ A @ T(0, 0, H - 0.3))
    k.put(box(w * 1.1, w * 1.1, 0.2, bev=0.03), "BH_Iron", M=M @ A @ T(0, 0, H - 0.1))
    k.put(torus(w * 0.42, w * 0.11, 10, 4), "BH_Iron", M=M @ A @ T(0, 0, H + w * 0.3) @ R(90, 0, 0))
    for side in range(4):
        rot = R(0, 0, 90 * side)
        for j in range(2):
            z = 0.35 + j * (H - 0.9) / 2
            ww = w * (0.22 + 0.28 * (z + 0.6) / (H + 0.25))
            k.put(box(w * 0.16, 0.04, 0.22), "BH_Blackwire", M=M @ A @ rot @ T(0, -ww - 0.005, z + 0.12))
            k.put(box(w * 0.3, 0.04, 0.05), "BH_Blackwire", M=M @ A @ rot @ T(0, -ww - 0.005, z))
    return M @ A @ Vector((0, 0, H + w * 0.3))


@asset("zr_ruin_wall", CAT)
def zr_ruin_wall(k):
    """Broken Wirewright wall, 4 m long, up to 3.6 m tall, 0.9 m thick, with a fret band and a dead wire channel."""
    r = k.r

    def prof(x):
        return 3.55 - 1.25 * max(0.0, x + 0.4) ** 1.25 + 0.25 * math.sin(x * 2.7)
    blk(k, 4.4, 1.3, 0.42, T(0, 0, 0.21), GSD, chips=4)
    masonry(k, -2.0, 2.0, 0.42, 3.8, 0.9, mat=GS, top_profile=prof, course=(0.4, 0.52), blen=(0.6, 1.15), core_mat=GSD,
            chip_rng=(1, 2))
    fret_band(k, -2.0, 0.2, 2.35, 0.6, M=T(0, -0.45, 0), mat=GS, back=GSD)
    wire_run(k, (-2.0, -0.45, 1.45), (1.3, -0.45, 1.45), Vector((0, -1, 0)), w=0.12, clamps=1.1, mat="BH_Verdigris")
    for x in (-1.7, -0.9, -0.1, 0.6):
        moss_cap(k, (x, 0.0, prof(x) - 0.05), r.uniform(0.35, 0.5))
    hang_vines(k, -1.9, 0.3, 3.2, -0.47, 6, 2.2)
    for i in range(6):
        blk(k, r.uniform(0.5, 0.9), r.uniform(0.4, 0.6), r.uniform(0.35, 0.45),
            TRS(r.uniform(0.3, 2.3), r.uniform(-1.6, -0.6), 0.18, r.uniform(-12, 12), r.uniform(-12, 12), r.uniform(0, 90)),
            GS, chips=3)
    k.put(box(1.0, 0.3, 0.6), GS, M=TRS(1.2, -1.9, 0.18, 80, 0, 25))
    k.col_box(4.4, 1.3, 3.0, T(0, 0, 1.5))
    return dict(recenter=False)


@asset("zr_ruin_column", CAT)
def zr_ruin_column(k):
    """A standing broken square column (3.7 m) with carved fret bands, and its fallen twin lying beside it."""
    r = k.r
    W = 0.95
    blk(k, 1.5, 1.5, 0.4, T(0, 0, 0.2), GS, chips=3, moss=(0.8, 1.0, 0.1))
    blk(k, 1.25, 1.25, 0.25, T(0, 0, 0.52), GS, chips=2)
    z = 0.65
    for i, h in enumerate((1.0, 0.95, 0.9)):
        blk(k, W, W, h - 0.03, TRS(0, 0, z + h / 2, 0, 0, r.uniform(-2, 2)), GS, chips=2)
        z += h
    t = box(W, W, 0.6, bev=0.04)
    slice_plane(t, (0, 0, 0.05), (0.5, 0.3, 1))
    chip(t, r, 3, 0.1)
    k.put(t, GS, M=T(0, 0, z + 0.3))
    for side in ("front", "back", "left", "right"):
        fret_band(k, -W / 2, W / 2, 2.85, 0.5, M=face_M(side, W / 2), mat=GS, back=GSD, unit_cells=12)
        wire_run(k, (0, 0, 0.7), (0, 0, 2.5), Vector((0, -1, 0)), w=0.1, clamps=0.9, mat="BH_Verdigris",
                 M=face_M(side, W / 2))
    moss_cap(k, (0.1, 0.0, z + 0.25), 0.45)
    hang_vines(k, -0.4, 0.4, z + 0.2, -W / 2, 3, 2.0)
    # fallen twin: three drums and a capital, rolled apart
    yaw = 28
    Mf = T(1.2, -0.6, 0) @ R(0, 0, yaw)
    for i, (x, h) in enumerate(((0.6, 1.0), (1.75, 0.95), (2.95, 0.9))):
        blk(k, h - 0.04, W, W, Mf @ TRS(x + i * 0.12, r.uniform(-0.12, 0.12), W / 2 - 0.06, r.uniform(-4, 4), 0, r.uniform(-8, 8)),
            GS, chips=3, moss=(0.75, 1.0, 0.1))
    blk(k, 1.3, 1.3, 0.4, Mf @ TRS(4.0, 0.3, 0.55, 0, 70, 20), GS, chips=3)
    k.col_box(1.5, 1.5, 3.7, T(0, 0, 1.85))
    k.col_mesh(box(3.6, W, W), Mf @ T(1.8, 0, W / 2))
    return dict(recenter=False)


@asset("zr_ruin_shrine", CAT)
def zr_ruin_shrine(k):
    """Small roofless shrine, 6 x 6 m walls on a stepped base (top at 1.4 m), stair on the front (Godot +Z), an
    altar stele at the back and a dead wire channel running from it out of the door. Origin: base centre on the
    ground; the stair reaches to Godot z=+6.4."""
    r = k.r
    z = 0.0
    for (w, h) in ((8.4, 0.5), (7.6, 0.5), (6.9, 0.4)):
        blk(k, w, w, h, T(0, 0, z + h / 2), GS if h > 0.45 else GSD, chips=6, chipd=0.15, moss=(0.7, 0.7, 0.1))
        z += h
    zt = z
    slab_floor(k, 6.0, 6.0, zt + 0.06, th=0.12, rows=(0.8, 1.2), lens=(0.9, 1.5), mat="BH_TerracePave", gap=0.04,
               crack_p=0.3, missing=0.06)
    # front stair (7 steps) with low cheeks
    n, rise, run = 7, zt / 7, 0.33
    for i in range(n):
        y0 = -4.2 - run * (n - i)
        blk(k, 2.6, -3.8 - y0, rise, T(0, (y0 - 3.8) / 2, rise * i + rise / 2), GS, chips=2, chipd=0.06)
    for sx in (-1, 1):
        t = hexa([(sx * 1.3, -4.2 - run * n, 0), (sx * 1.75, -4.2 - run * n, 0), (sx * 1.75, -3.8, 0), (sx * 1.3, -3.8, 0),
                  (sx * 1.3, -4.2 - run * n, 0.35), (sx * 1.75, -4.2 - run * n, 0.35), (sx * 1.75, -3.8, zt + 0.35),
                  (sx * 1.3, -3.8, zt + 0.35)], 0.04)
        chip(t, r, 3, 0.08)
        k.put(t, GS)
    # walls, broken to different heights, a door gap on the front
    th = 0.7
    walls = (("front", (-3.0 + th / 2, 3.0 - th / 2)), ("back", None), ("left", None), ("right", None))
    for side, _ in walls:
        M = face_M(side, 3.0 - th / 2, zt) @ T(0, 0, 0)
        ph = r.uniform(0, 6)
        cuts = (RectCut(-0.95, 0.95, 0.0, 2.6),) if side == "front" else ()

        def prof(x, ph=ph, side=side):
            return 2.9 + 0.6 * math.sin(x * 0.9 + ph) - (1.2 if side == "right" and x > 0.5 else 0.0)
        masonry(k, -3.0, 3.0, 0.0, 3.6, th, mat=GS, M=M, top_profile=prof, cuts=cuts, course=(0.38, 0.5),
                blen=(0.55, 1.1), core_mat=GSD, chip_rng=(1, 2))
        if side == "front":
            blk(k, 2.6, th + 0.1, 0.45, T(0, -3.0 + th / 2, zt + 2.6 + 0.22), GS, chips=3)
        for x in (-2.0, 0.0, 2.0):
            if side == "front" and abs(x) < 1:
                continue
            moss_cap(k, tuple(M @ Vector((x, 0, prof(x) - 0.05))), r.uniform(0.3, 0.45))
    # fret band on the outside of the back wall and glyph cartouches flanking the door
    fret_band(k, -2.8, 2.8, zt + 2.0, 0.55, M=face_M("back", 3.0) @ T(0, 0, 0), mat=GS, back=GSD)
    for sx in (-1, 1):
        glyph(k, T(sx * 1.85, -3.0, zt + 1.6), s=0.7, mat="BH_Turquoise")
    # altar stele inside, dead wire from it out through the door and down the stair
    blk(k, 1.6, 0.8, 0.6, T(0, 2.0, zt + 0.3), GS, chips=3)
    blk(k, 1.1, 0.5, 2.0, T(0, 2.15, zt + 0.6 + 1.0), GS, chips=3)
    blk(k, 1.4, 0.65, 0.25, T(0, 2.15, zt + 2.72), GS, chips=2, moss=(0.8, 1.0, 0.1))
    glyph(k, T(0, 1.9, zt + 1.75), s=0.75, mat="BH_Verdigris")
    wire_run(k, (0, 1.55, zt + 0.06), (0, -3.6, zt + 0.06), UP, w=0.14, clamps=1.0, mat="BH_Verdigris")
    for i in range(3):
        blk(k, r.uniform(0.5, 0.8), r.uniform(0.4, 0.6), 0.4,
            TRS(r.uniform(-2.2, 2.2), r.uniform(-1.8, 1.0), zt + 0.25, r.uniform(-10, 10), r.uniform(-10, 10), r.uniform(0, 90)),
            GS, chips=3)
    hang_vines(k, -2.6, 2.6, zt + 2.8, -3.0 - 0.05, 7, 2.6)
    # collision: walkable base top, the stair ramp, walls (door left open), stele
    k.col_box(8.4, 8.4, zt, T(0, 0, zt / 2))
    L = math.hypot(run * n, zt)
    k.col_mesh(box(2.6, L, 0.2), TRS(0, -4.2 - run * n / 2, zt / 2 - 0.1, math.degrees(math.atan2(zt, run * n)), 0, 0))
    for side in ("back", "left", "right"):
        k.col_mesh(box(6.0, th, 3.0), face_M(side, 3.0 - th / 2, zt) @ T(0, 0, 1.5))
    for sx in (-1, 1):
        k.col_box(2.05, th, 3.0, T(sx * 1.97, -3.0 + th / 2, zt + 1.5))
    k.col_box(1.6, 0.8, 2.6, T(0, 2.0, zt + 1.3))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# HEARTWIRE RELAYS AND THE KHARVENN CHAINS
@asset("zr_relay_pylon", CAT)
def zr_relay_pylon(k):
    """Heartwire relay pylon 6.4 m on a stepped plinth: wired stone mast and two hand-wound coils. Socket `light`."""
    r = k.r
    z = 0.0
    for (w, h) in ((3.2, 0.4), (2.6, 0.35), (2.0, 0.3)):
        blk(k, w, w, h, T(0, 0, z + h / 2), GS, chips=4, chipd=0.1, moss=(0.75, 0.9, 0.1))
        z += h
    for side in ("front", "back", "left", "right"):
        fret_band(k, -1.0, 1.0, 0.58, 0.3, M=face_M(side, 1.3), mat=GS, back=GSD, unit_cells=12)
    z0, z1, w0, w1 = z, 4.45, 0.95, 0.74
    hx(k, [(-w0 / 2, -w0 / 2, z0), (w0 / 2, -w0 / 2, z0), (w0 / 2, w0 / 2, z0), (-w0 / 2, w0 / 2, z0),
           (-w1 / 2, -w1 / 2, z1), (w1 / 2, -w1 / 2, z1), (w1 / 2, w1 / 2, z1), (-w1 / 2, w1 / 2, z1)], GS, chips=3, chipd=0.06)
    for side, nrm in (("front", (0, -1, 0)), ("back", (0, 1, 0)), ("left", (-1, 0, 0)), ("right", (1, 0, 0))):
        nv = Vector(nrm)
        wire_run(k, nv * (w0 / 2) + Vector((0, 0, z0 + 0.1)), nv * (w1 / 2) + Vector((0, 0, z1 - 0.1)), nv, w=0.1, clamps=0.9)
    blk(k, 0.98, 0.98, 0.16, T(0, 0, 2.7), "BH_Brass", chips=0, bev=0.02, jit=0)
    for side in ("front", "back"):
        glyph(k, face_M(side, 0.43, 1.8) @ T(0.0, -0.02, 0), s=0.42, d=0.04)
    blk(k, 0.55, 0.55, 1.3, T(0, 0, 4.45 + 0.65), GSD, chips=0)
    toroid_coil(k, 4.75, 0.8, 0.16, 14, segs=22)
    toroid_coil(k, 5.3, 0.66, 0.14, 12, segs=20)
    for zc, Rc in ((4.75, 0.8), (5.3, 0.66)):
        for i in range(4):
            a_ = math.tau * i / 4 + math.pi / 4
            beam_(k, (math.cos(a_) * 0.27, math.sin(a_) * 0.27, zc), (math.cos(a_) * (Rc - 0.08), math.sin(a_) * (Rc - 0.08), zc),
                  0.08, "BH_Brass")
    blk(k, 0.9, 0.9, 0.18, T(0, 0, 5.84), GS, chips=2)
    blk(k, 0.6, 0.6, 0.16, T(0, 0, 6.01), GS, chips=1)
    for i in range(3):
        a_ = math.tau * i / 3
        k.put(tube([(math.cos(a_) * 0.22, math.sin(a_) * 0.22, 6.08), (math.cos(a_) * 0.3, math.sin(a_) * 0.3, 6.3),
                    (math.cos(a_) * 0.12, math.sin(a_) * 0.12, 6.5)], 0.035, 5), "BH_Brass", smooth=40)
    k.put(ico(0.17, 2), "BH_Wire", M=T(0, 0, 6.32), smooth=60)
    k.sockets.append(("light", (0, 0, 5.0)))
    k.col_box(3.2, 3.2, 1.05, T(0, 0, 0.525))
    k.col_box(1.0, 1.0, 5.0, T(0, 0, 3.5))
    return dict(recenter=False)


@asset("zr_relay_chains", CAT, col=False)
def zr_relay_chains(k):
    """Kharvenn rune-chains wrapped round zr_relay_pylon and spiked into the ground. Same origin as the pylon, so the
    game can delete this node when the hero cuts the chains."""
    r = k.r
    # iron clamp collars with runes on the mast
    for zc, w in ((1.75, 0.98), (3.85, 0.86)):
        k.put(box(w + 0.12, w + 0.12, 0.22, bev=0.02), "BH_Iron", M=T(0, 0, zc))
        for side in ("front", "back", "left", "right"):
            k.put(box(0.3, 0.05, 0.12), "BH_Blackwire", M=face_M(side, (w + 0.12) / 2, zc))
    # spiral wrap (two turns)
    pts = []
    for i in range(17):
        s = i / 16
        a = math.tau * 2.0 * s + 0.4
        rad = 0.66 - 0.08 * s
        pts.append((math.cos(a) * rad, math.sin(a) * rad, 1.35 + 2.75 * s))
    chain_path(k, pts, R_=0.13, r_=0.034)
    # four chains to rune-spikes driven into the ground
    for i in range(4):
        a = math.tau * i / 4 + math.pi / 4 + r.uniform(-0.2, 0.2)
        dirv = Vector((math.cos(a), math.sin(a), 0))
        dist = r.uniform(2.9, 3.4)
        top = rune_spike(k, dirv * dist + Vector((0, 0, -0.05)), dirv, H=1.25, w=0.26)
        start = Vector((math.cos(a) * 0.62, math.sin(a) * 0.62, r.uniform(2.6, 3.6)))
        mid = start.lerp(top, 0.5) + Vector((0, 0, -0.35))
        chain_path(k, [start, mid, top], R_=0.13, r_=0.034)
        for j in range(4):
            aa = a + (j - 1.5) * 0.4
            p = dirv * dist + Vector((math.cos(aa) * 0.5, math.sin(aa) * 0.5, 0.01))
            strip(k, dirv * dist, p, UP, 0.05, 0.02, "BH_Blackwire")
    return dict(recenter=False)


@asset("zr_chain_spike", CAT)
def zr_chain_spike(k):
    """A Kharvenn rune-spike 2.5 m driven into cracked ground, its chain trailing off toward +X."""
    r = k.r
    top = rune_spike(k, (0, 0, 0), (0.3, -0.2, 0), H=2.5, w=0.42)
    # heaved, cracked ground plates with lit cracks
    for i in range(7):
        a = math.tau * i / 7 + r.uniform(-0.2, 0.2)
        d = r.uniform(0.55, 0.9)
        t = box(r.uniform(0.7, 1.0), r.uniform(0.5, 0.75), 0.18, bev=0.02)
        chip(t, r, 3, 0.1)
        k.put(t, "BH_Dirt", M=TRS(math.cos(a) * d, math.sin(a) * d, 0.04, r.uniform(-14, 14), r.uniform(-14, 14),
                                  math.degrees(a)))
        a2 = a + math.tau / 14
        strip(k, (math.cos(a2) * 0.3, math.sin(a2) * 0.3, 0.0), (math.cos(a2) * r.uniform(1.3, 1.8), math.sin(a2) * r.uniform(1.3, 1.8), 0.0),
              UP, 0.05, 0.03, "BH_Blackwire")
    # trailing chain: from the ring down to the ground and away along it
    g0 = Vector((0.6, -0.1, 0.1))
    chain_path(k, [top, top.lerp(g0, 0.5) + Vector((0.15, 0, -0.2)), g0, Vector((1.6, 0.3, 0.1)), Vector((2.6, 0.1, 0.1)),
                   Vector((3.4, 0.6, 0.1))], R_=0.12, r_=0.032)
    k.col_box(0.7, 0.7, 2.6, T(0.15, -0.1, 1.3))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# GLASSWIRE BARRENS
def partial_ring(k, M, R_, r_, a0, a1, mat, segs=20, rsegs=8):
    n = max(2, int(segs * (a1 - a0) / math.tau) + 1)
    pts = [(math.cos(a0 + (a1 - a0) * i / (n - 1)) * R_, math.sin(a0 + (a1 - a0) * i / (n - 1)) * R_, 0) for i in range(n)]
    k.put(tube(pts, r_, rsegs), mat, M=M, smooth=50)


def mound(k, p, sx, sy, h, mat="BH_Dirt"):
    t = ico(1.0, 2)
    for v in t.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, max(v.co.z, -0.2) * h))
    ndisp(t, 0.8, 0.25, k.noff + Vector(p))
    k.put(t, mat, M=T(*p), smooth=50)


def crack_lines(k, ctr, n, r0, r1, mat="BH_Blackwire", w=0.06):
    r = k.r
    c = Vector(ctr)
    for i in range(n):
        a = math.tau * i / n + r.uniform(-0.3, 0.3)
        p0 = c + Vector((math.cos(a) * r0, math.sin(a) * r0, 0.01))
        mid = c + Vector((math.cos(a + 0.2) * (r0 + r1) / 2, math.sin(a + 0.2) * (r0 + r1) / 2, 0.01))
        p1 = c + Vector((math.cos(a - 0.1) * r1, math.sin(a - 0.1) * r1, 0.01))
        strip(k, p0, mid, UP, w, 0.03, mat)
        strip(k, mid, p1, UP, w * 0.7, 0.03, mat)


@asset("zr_colossus_fallen", CAT)
def zr_colossus_fallen(k):
    """A fallen Wirewright colossus ~27 m long lying half sunk on its back: head (-X), chest and shoulder, and an
    arm stretched along +X ending in an open hand. Bronze and stone, broken coils, Blackwire in the cracks."""
    r = k.r
    BR, VG, CU = "BH_Brass", "BH_Verdigris", "BH_Copper"
    # ---- head, built upright in its own frame (face toward local -Y), then laid down
    lay = Matrix(((0, 0, -1, 0), (1, 0, 0, 0), (0, -1, 0, 0), (0, 0, 0, 1)))  # face up, crown toward -X
    Mh = T(-6.9, 0.4, -0.7) @ R(32, 0, 0) @ lay @ S(1.3)
    blk(k, 4.4, 4.6, 4.8, Mh @ T(0, 0.3, 2.4), GS, chips=6, chipd=0.4)
    blk(k, 3.8, 0.6, 3.6, Mh @ T(0, -2.1, 2.2), GS, chips=3, chipd=0.2)
    blk(k, 4.3, 0.95, 0.6, Mh @ T(0, -2.45, 3.4), GS, chips=4, chipd=0.15)
    for sx in (-1, 1):
        k.put(box(1.05, 0.3, 0.42), "BH_Blackwire", M=Mh @ T(sx * 0.92, -2.35, 2.85))
        wire_run(k, (sx * 1.45, -2.4, 2.6), (sx * 1.45, -2.4, 0.9), Vector((0, -1, 0)), w=0.14, clamps=0.7, mat=CU, M=Mh)
    blk(k, 0.65, 0.6, 1.3, Mh @ T(0, -2.55, 2.2), GS, chips=2)
    for i in range(3):
        k.put(box(2.0, 0.14, 0.15, bev=0.02), BR, M=Mh @ T(0, -2.45, 1.0 + i * 0.27))
    blk(k, 2.8, 0.9, 0.75, Mh @ T(0, -2.0, 0.4), GS, chips=3)
    strip(k, (-1.4, -2.95, 3.65), (0.2, -2.95, 3.3), Vector((0, -1, 0)), 0.07, 0.04, "BH_Blackwire", M=Mh)
    strip(k, (0.2, -2.95, 3.3), (0.9, -2.95, 3.7), Vector((0, -1, 0)), 0.06, 0.04, "BH_Blackwire", M=Mh)
    # bronze crest of fins along the skull ridge
    for i, y in enumerate((-1.5, -0.5, 0.5, 1.5)):
        out = [(-0.8, 0), (0.8, 0), (0.55, 1.4), (0.0, 2.1 - abs(i - 1.5) * 0.3), (-0.5, 1.2)]
        t = prism(out, 0.3, bev=0.03)
        k.put(t, VG, M=Mh @ T(0, y, 4.7) @ R(0, 0, 90) @ R(0, -10 - i * 8, 0))
    # ear discs with dead coils
    for sx in (-1, 1):
        Me = Mh @ T(sx * 2.45, 0.3, 2.4) @ R(0, 90, 0)
        k.put(cyl(1.15, 0.45, 18, bev=0.04), BR, M=Me @ T(0, 0, -0.22))
        toroid_coil(k, sx * 0.25, 0.82, 0.17, 12, M=Me, segs=20, body=VG, wire=CU)
    # neck ring
    k.put(cyl(1.5, 1.6, 12), GSD, M=T(-6.3, 0.4, 0.0) @ R(0, 90, 0) @ T(0, 0, -0.8))
    k.put(torus(1.65, 0.28, 16, 6), BR, M=T(-6.2, 0.4, 0.0) @ R(0, 90, 0), smooth=40)
    # ---- chest, sunk to the armpits
    hx(k, [(-6.2, -3.4, -2.0), (1.2, -3.6, -2.0), (1.2, 3.4, -2.0), (-6.2, 3.2, -2.0),
           (-5.8, -2.8, 1.7), (0.8, -3.0, 1.6), (0.8, 2.8, 1.6), (-5.8, 2.6, 1.7)], GS, chips=6, chipd=0.35)
    for sy in (-1, 1):
        blk(k, 3.2, 2.7, 0.4, TRS(-3.0, sy * 1.45, 1.82, sy * -7, 0, 0), VG, chips=3, chipd=0.12)
        wire_run(k, (-4.4, sy * 1.45, 2.06), (-1.6, sy * 1.45, 2.06), UP, w=0.16, clamps=0.9, mat=CU)
    strip(k, (-1.2, -0.2, 1.65), (0.4, 0.4, 1.6), UP, 0.1, 0.05, "BH_Blackwire")
    strip(k, (0.4, 0.4, 1.6), (0.7, 1.4, 1.55), UP, 0.08, 0.05, "BH_Blackwire")
    glyph(k, T(-2.9, -3.1, 0.5) @ R(-8, 0, 0), s=1.2, mat="BH_Blackwire", d=0.07)
    # broken coil pack bursting from under the back (+Y side)
    toroid_coil(k, 0.0, 2.1, 0.32, 18, M=T(-2.6, 3.9, 0.2) @ R(90, 0, 15), segs=26, body=CU, wire="BH_Blackwire")
    partial_ring(k, T(0.4, 3.6, 0.1) @ R(90, 0, -20), 1.7, 0.28, 0.2, 3.6, CU)
    partial_ring(k, T(0.4, 3.6, 0.1) @ R(90, 0, -20), 1.7, 0.33, 0.6, 1.9, VG, rsegs=6)
    # ---- shoulder pauldron, upper arm, elbow, forearm, hand
    sh, el, wr = Vector((1.6, -3.0, 0.2)), Vector((7.6, -3.8, 0.15)), Vector((12.8, -2.6, 0.2))
    t = lathe([(2.7, -0.6), (2.65, 0.4), (2.25, 1.3), (1.4, 1.95), (0.0, 2.15)], 16)
    k.put(t, VG, M=T(*sh) @ R(0, -24, 0), smooth=35)
    k.put(torus(2.68, 0.16, 18, 4), BR, M=T(*sh) @ R(0, -24, 0) @ T(0, 0, 0.2), smooth=40)
    k.put(torus(2.3, 0.13, 18, 4), BR, M=T(*sh) @ R(0, -24, 0) @ T(0, 0, 1.15), smooth=40)
    k.put(tube([sh, sh.lerp(el, 0.5), el], [1.3, 1.22, 1.12], 9), GS, smooth=35)
    for s_ in (0.25, 0.75):
        p = sh.lerp(el, s_)
        k.put(torus(1.32 - s_ * 0.1, 0.16, 16, 4), BR, M=T(*p) @ align_z(el - sh), smooth=40)
    k.put(ico(1.2, 2), BR, M=T(*el), smooth=40)
    k.put(tube([el, el.lerp(wr, 0.5), wr], [1.05, 0.98, 0.85], 9), GS, smooth=35)
    strip(k, el.lerp(wr, 0.12), el.lerp(wr, 0.88), UP, 1.5, 0.3, VG, off=0.72)
    wire_run(k, el.lerp(wr, 0.15) + Vector((0, 0, 1.03)), el.lerp(wr, 0.85) + Vector((0, 0, 0.95)), UP, w=0.13,
             clamps=0.8, mat=CU)
    strip(k, el.lerp(wr, 0.45) + Vector((0, 0.3, 1.06)), el.lerp(wr, 0.6) + Vector((0, -0.2, 1.04)), UP, 0.07, 0.04,
          "BH_Blackwire")
    Mw = T(*wr) @ R(0, 0, -14)
    blk(k, 2.3, 2.0, 0.8, Mw @ T(1.3, 0, 0.0), GS, chips=4, chipd=0.15)
    for i, yy in enumerate((-0.72, -0.24, 0.24, 0.72)):
        p = Vector((2.45, yy, 0.0))
        ang = 0.0
        for j, L in enumerate((0.95, 0.8, 0.65)):
            ang += (-12, 18, 26)[j] + i * 3
            d = Vector((math.cos(math.radians(ang)), 0, math.sin(math.radians(ang)) * 0.5))
            q = p + d * L
            beam_(k, p, q, 0.42, GS, M=Mw)
            p = q
    beam_(k, (0.9, -1.05, 0.0), (1.6, -1.8, 0.1), 0.45, GS, M=Mw)
    beam_(k, (1.6, -1.8, 0.1), (2.3, -2.1, 0.0), 0.4, GS, M=Mw)
    # sunk into the ground: earth mounds and rubble around every mass
    for (p, sx, sy, h) in (((-9.6, 0.6, 0.0), 4.2, 4.0, 1.3), ((-11.6, -2.0, 0.0), 2.0, 1.6, 0.8), ((-6.4, -3.2, 0.0), 2.6, 1.6, 0.9),
                           ((-2.5, -3.8, 0.0), 4.2, 1.4, 1.0), ((-2.5, 3.6, 0.0), 4.0, 1.6, 0.8),
                           ((2.5, -1.2, 0.0), 2.4, 2.0, 0.7), ((7.6, -3.8, 0.0), 2.2, 2.0, 0.6),
                           ((12.6, -2.6, 0.0), 1.8, 1.8, 0.45), ((4.6, -4.8, 0.0), 2.6, 1.0, 0.5)):
        mound(k, p, sx, sy, h)
    for i in range(10):
        blk(k, r.uniform(0.4, 1.0), r.uniform(0.4, 0.9), r.uniform(0.3, 0.6),
            TRS(r.uniform(-11, 14), r.uniform(-6.5, -4.5) if i % 2 else r.uniform(4.0, 6.0), 0.15, r.uniform(-20, 20),
                r.uniform(-20, 20), r.uniform(0, 90)), GS if i % 3 else VG, chips=3)
    crack_lines(k, (-2.6, 5.4, 0.0), 6, 0.5, 2.6)
    # collision on the big masses
    k.col_mesh(box(6.8, 6.4, 3.4), T(-9.9, 0.4, 1.0))
    k.col_box(7.4, 6.8, 2.0, T(-2.5, 0, 0.6))
    k.col_mesh(cyl(2.6, 1.9, 10), T(1.6, -3.0, 0.0))
    for a, b, rr in ((sh, el, 1.2), (el, wr, 1.0)):
        F, L, _ = frame_of(a, b, UP)
        k.col_mesh(box(rr * 2, rr * 2, L), F)
    k.col_mesh(box(2.6, 2.4, 0.9), Mw @ T(1.6, -0.2, 0.0))
    k.col_mesh(cyl(2.0, 2.6, 10), T(-2.6, 3.9, -0.4))
    return dict(recenter=False)


@asset("zr_glass_growth", CAT)
def zr_glass_growth(k):
    """Blackwire glass bursting from heaved, cracked ground: obsidian prisms 1-3 m with lit violet-red shards."""
    r = k.r
    for i in range(9):
        a = math.tau * i / 9 + r.uniform(-0.2, 0.2)
        d = r.uniform(0.7, 1.6)
        t = box(r.uniform(0.8, 1.2), r.uniform(0.6, 0.9), 0.22, bev=0.02)
        chip(t, r, 3, 0.12)
        k.put(t, "BH_Dirt", M=TRS(math.cos(a) * d, math.sin(a) * d, 0.05, r.uniform(-18, 18), r.uniform(-18, 18),
                                  math.degrees(a)))
    crack_lines(k, (0, 0, 0), 7, 0.9, 2.5, w=0.07)
    crystal(k, (0, 0, -0.2), (0.12, 0.05, 1), 3.1, 0.5, mat="BH_Obsidian", tip=0.28, segs=6)
    crystal(k, (0.05, -0.05, -0.1), (0.05, -0.12, 1), 2.4, 0.26, mat="BH_Blackwire", tip=0.3, segs=5)
    for i in range(11):
        a = math.tau * i / 11 + r.uniform(-0.25, 0.25)
        dist = r.uniform(0.35, 1.25)
        lean = math.radians(r.uniform(18, 55))
        d = Vector((math.cos(a) * math.sin(lean), math.sin(a) * math.sin(lean), math.cos(lean)))
        big = i % 3 != 0
        crystal(k, (math.cos(a) * dist, math.sin(a) * dist, -0.15), d, r.uniform(1.1, 2.3) if big else r.uniform(0.7, 1.3),
                r.uniform(0.2, 0.36) if big else r.uniform(0.12, 0.2), mat="BH_Obsidian" if big else "BH_Blackwire",
                tip=0.3, segs=6 if big else 5)
    k.col_mesh(cyl(1.3, 2.4, 8))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# THE THREE VAULT GATES (origin = centre of the 3 m clear disc for the teleporter dais; portal behind, on +Y)
def disc_ring(k, mat, r0=1.65, r1=1.95, wire=True):
    t = lathe([(r0, 0.0), (r1, 0.0), (r1, 0.04), (r0, 0.04), (r0, 0.0)], 40, cap_bot=False, cap_top=False)
    k.put(t, mat, smooth=30)
    if wire:
        t = lathe([(r1 + 0.05, 0.0), (r1 + 0.13, 0.0), (r1 + 0.13, 0.05), (r1 + 0.05, 0.05), (r1 + 0.05, 0.0)], 40,
                  cap_bot=False, cap_top=False)
        k.put(t, "BH_Wire", smooth=30)


@asset("zr_gate_jade", CAT)
def zr_gate_jade(k):
    """The Jade Sepulchre gate: a jade serpent whose open jaws frame the dais; its gullet is the tomb door."""
    r = k.r
    J = "BH_Jade"
    tier(k, 10.4, 3.2, 0.0, 4.8, talus=0.3, inset=0.3, M=T(0, 3.8, 0), mat=GSD, trim=GS)
    yf = 3.8 - (3.2 / 2 - 0.3 + 0.12 - 0.1)
    # the door: darkness framed by jade jambs and a threshold
    k.put(box(3.2, 0.2, 4.4), "BH_Obsidian", M=T(0, yf - 0.05, 2.2))
    for sx in (-1, 1):
        blk(k, 0.6, 0.8, 4.6, T(sx * 1.9, yf - 0.2, 2.3), J, chips=3)
        glyph(k, T(sx * 3.6, yf, 2.7), s=1.3, mat="BH_Glyph", d=0.07)
        for xx in (2.7, 4.6):
            wire_run(k, (sx * xx, yf, 1.5), (sx * xx, yf, 4.6), Vector((0, -1, 0)), w=0.13, clamps=1.0)
    blk(k, 4.4, 0.75, 0.22, T(0, yf - 0.55, 0.11), J, chips=2)
    fret_band(k, -4.9, 4.9, 4.05, 0.7, M=T(0, yf, 0), mat=J, back=GSD)
    # upper head over the door, jaws open, plume crest fanning out
    serpent_head(k, T(0, 1.75, 3.55), s=2.9, mat=J, accent="BH_Turquoise", eye="BH_Glyph", fang=GS, plume_mat=J,
                 gape=0.42, plumes=9, lower=False)
    # split lower jaw lying on the ground either side of the dais, fangs up
    for sx in (-1, 1):
        c = [(sx * 2.0, 2.4, 0.0), (sx * 3.2, 2.4, 0.0), (sx * 2.75, -2.5, 0.0), (sx * 1.9, -2.5, 0.0),
             (sx * 2.05, 2.4, 1.25), (sx * 3.05, 2.4, 1.25), (sx * 2.65, -2.4, 0.55), (sx * 1.95, -2.4, 0.55)]
        if sx > 0:
            c = [c[1], c[0], c[3], c[2], c[5], c[4], c[7], c[6]]
        hx(k, c, J, bev=0.06, chips=4, chipd=0.1)
        for (y, h) in ((-2.25, 1.0), (-1.2, 0.6), (-0.2, 0.55), (0.8, 0.5)):
            zt = 0.55 + (1.25 - 0.55) * (y + 2.4) / 4.8
            k.put(cyl(0.16 if h > 0.8 else 0.1, h, 6, r2=0.0), GS, M=T(sx * 2.05, y, zt - 0.05))
        wire_run(k, (sx * 2.55, 2.3, 1.27), (sx * 2.35, -2.3, 0.57), UP, w=0.12, clamps=0.9)
        for y in (-1.6, 0.0, 1.5):
            zt = 0.55 + (1.25 - 0.55) * (y + 2.4) / 4.8
            k.put(box(0.5, 0.35, 0.08), "BH_Turquoise", M=T(sx * 2.85, y, zt - 0.05) @ R(0, sx * -20, 0))
    disc_ring(k, J)
    k.sockets.append(("light", (0, 0.4, 4.2)))
    k.col_box(10.4, 3.2, 4.8, T(0, 3.8, 2.4))
    for sx in (-1, 1):
        k.col_box(1.3, 4.9, 1.3, T(sx * 2.55, 0.0, 0.65))
    return dict(recenter=False)


@asset("zr_gate_obsidian", CAT)
def zr_gate_obsidian(k):
    """The Obsidian Engine gate: black-glass machine doors with molten-copper seams in a corbel-stepped frame,
    flanked by piston housings."""
    r = k.r
    O, LV, BR = "BH_Obsidian", "BH_Glyph", "BH_Brass"   # seams glow white (every Zarael glow is white)
    blk(k, 10.0, 2.6, 7.0, T(0, 4.0, 3.5), O, chips=6, chipd=0.25)
    for sx in (-1, 1):
        blk(k, 1.9, 2.3, 1.0, T(sx * 2.65, 2.5, 0.5), O, chips=3)
        blk(k, 1.5, 2.0, 4.4, T(sx * 2.65, 2.5, 1.0 + 2.2), O, chips=3)
        for i in range(3):
            blk(k, 1.5, 2.0, 0.55, T(sx * (2.5 - i * 0.42), 2.5, 5.4 + i * 0.55 + 0.27), O, chips=2)
        # molten-copper channel down the pillar face into a bronze trough
        wire_run(k, (sx * 2.65, 1.5, 5.2), (sx * 2.65, 1.5, 0.45), Vector((0, -1, 0)), w=0.16, clamps=1.0, mat=LV,
                 bed_mat=BR)
        blk(k, 1.1, 0.9, 0.35, T(sx * 2.65, 1.05, 0.175), BR, chips=0, bev=0.03)
        k.put(box(0.9, 0.7, 0.05), LV, M=T(sx * 2.65, 1.05, 0.33))
    blk(k, 7.2, 2.4, 1.1, T(0, 2.5, 7.0 + 0.55), O, chips=4)
    for i, (w, h) in enumerate(((8.6, 0.5), (6.0, 0.5), (3.6, 0.5), (1.6, 0.45))):
        blk(k, w, 2.0 - i * 0.2, h, T(0, 3.4, 8.1 + i * 0.5 + h / 2 - 0.05), O, chips=3)
    strip(k, (-3.0, 2.4, 8.62), (3.0, 2.4, 8.62), Vector((0, -1, 0)), 0.1, 0.05, LV)
    strip(k, (-1.8, 2.5, 9.12), (1.8, 2.5, 9.12), Vector((0, -1, 0)), 0.1, 0.05, LV)
    fret_band(k, -3.5, 3.5, 7.55, 0.8, M=T(0, 1.3, 0), mat=BR, back=O)
    # the door leaves
    for sx in (-1, 1):
        blk(k, 1.75, 0.4, 5.3, T(sx * 0.9, 2.3, 2.65), O, chips=1, bev=0.03)
        for z in (1.1, 2.55, 4.0):
            strip(k, (sx * 0.08, 2.1, z), (sx * 1.72, 2.1, z), Vector((0, -1, 0)), 0.07, 0.03, LV)
        for xx in (0.45, 1.35):
            strip(k, (sx * xx, 2.1, 0.1), (sx * xx, 2.1, 5.2), Vector((0, -1, 0)), 0.16, 0.06, BR)
    k.put(box(0.08, 0.1, 5.3), LV, M=T(0, 2.06, 2.65))
    k.put(torus(0.85, 0.12, 20, 6), BR, M=T(0, 2.0, 2.9) @ R(90, 0, 0), smooth=40)
    k.put(cyl(0.3, 0.3, 12), BR, M=T(0, 2.0, 2.9) @ R(90, 0, 0) @ T(0, 0, -0.15))
    k.put(ico(0.16, 1), LV, M=T(0, 1.83, 2.9))
    for i in range(6):
        a = math.tau * i / 6
        strip(k, (math.cos(a) * 0.3, 2.0, 2.9 + math.sin(a) * 0.3), (math.cos(a) * 0.8, 2.0, 2.9 + math.sin(a) * 0.8),
              Vector((0, -1, 0)), 0.1, 0.08, BR)
    # piston housings angled forward on the wings
    for sx in (-1, 1):
        Mw = T(sx * 4.35, 2.2, 0) @ R(0, 0, sx * -22)
        blk(k, 1.9, 3.4, 3.8, Mw @ T(0, 0, 1.9), O, chips=4)
        blk(k, 1.5, 2.8, 0.9, Mw @ T(0, 0.2, 3.8 + 0.45), O, chips=3)
        blk(k, 2.1, 3.6, 0.25, Mw @ T(0, 0, 3.85), BR, chips=0, bev=0.02)
        k.put(cyl(0.95, 0.3, 18, bev=0.03), BR, M=Mw @ T(-sx * 0.0, -1.72, 2.2) @ R(90, 0, 0))
        for i in range(12):
            a = math.tau * i / 12
            k.put(box(0.2, 0.3, 0.22), BR, M=Mw @ T(math.cos(a) * 1.0, -1.72, 2.2 + math.sin(a) * 1.0) @ R(0, -math.degrees(a), 0))
        k.put(ico(0.2, 1), LV, M=Mw @ T(0, -1.9, 2.2))
        for xx in (-0.55, 0.55):
            k.put(cyl(0.22, 2.4, 10), BR, M=Mw @ T(xx, -1.6, 0.3), smooth=30)
            k.put(cyl(0.1, 1.3, 8), "BH_Iron", M=Mw @ T(xx, -1.6, 2.7), smooth=30)
        strip(k, (-0.95, -1.7, 3.6), (0.95, -1.7, 3.6), Vector((0, -1, 0)), 0.12, 0.05, LV, M=Mw)
    disc_ring(k, O)
    k.sockets.append(("light", (0, 0.6, 3.2)))
    k.col_box(10.0, 2.6, 7.0, T(0, 4.0, 3.5))
    k.col_box(7.2, 2.4, 8.0, T(0, 2.5, 4.0))
    for sx in (-1, 1):
        k.col_mesh(box(1.9, 3.4, 4.7), T(sx * 4.35, 2.2, 0) @ R(0, 0, sx * -22) @ T(0, 0, 2.35))
    return dict(recenter=False)


def smooth_pts(pts, sub=3):
    """Catmull-Rom resample of a polyline (sub points per span)."""
    P = [Vector(p) for p in pts]
    out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for j in range(sub):
            t = j / sub
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-1])
    return out


def vein(k, p0, p1, r0, r1, bulge=None, flat_z=False, caps=True, mat="BH_Blackwire", branches=2):
    """A wandering, tapering vein from p0 (thin) to p1 (thick) with a couple of capillaries."""
    r = k.r
    p0, p1 = Vector(p0), Vector(p1)
    n = 6
    pts = []
    for i in range(n + 1):
        t = i / n
        q = p0.lerp(p1, t)
        if 0 < i < n:
            q += Vector((r.uniform(-0.25, 0.25), r.uniform(-0.12, 0.12), 0 if flat_z else r.uniform(-0.25, 0.25)))
            if bulge is not None:
                q += bulge * math.sin(math.pi * t)
        pts.append(q)
    sp = smooth_pts(pts, 3)
    rads = [r0 + (r1 - r0) * (i / (len(sp) - 1)) ** 1.5 for i in range(len(sp))]
    k.put(tube(sp, rads, 5, cap_start=caps), mat, smooth=50)
    for b in range(branches):
        i = r.randint(len(sp) // 4, len(sp) * 3 // 4)
        d = (sp[min(i + 1, len(sp) - 1)] - sp[i]).normalized()
        side = d.cross(Vector((0, 1, 0)) if abs(d.y) < 0.9 else UP).normalized() * r.choice((-1, 1))
        if flat_z:
            side.z = 0
        e = sp[i] + side * r.uniform(0.4, 0.9) - d * r.uniform(0.1, 0.4)
        k.put(tube(smooth_pts([sp[i], sp[i].lerp(e, 0.5) + side * 0.1, e], 2), [rads[i] * 0.6, rads[i] * 0.4, rads[i] * 0.3, 0.015, 0.01], 4),
              mat, smooth=50)


@asset("zr_gate_vein", CAT)
def zr_gate_vein(k):
    """The Veinworks gate: a cleft in the rock held open by a giant's ribs, red-violet veins pulsing into it."""
    r = k.r
    B, V = "BH_Bone", "BH_Blackwire"
    for sx in (-1, 1):
        rock_piece(k, (2.3, 2.6, 4.3), 900, pos=(sx * 3.75, 3.9, 0), rz=sx * 12, mat="BH_CliffOchre", moss=False,
                   tilt=(0, -sx * 7), cuts=10)
        rock_piece(k, (1.4, 1.6, 2.0), 300, pos=(sx * 5.0, 2.2, 0), rz=sx * 40, mat="BH_CliffOchre", moss=False)
    rock_piece(k, (2.6, 2.2, 1.3), 500, pos=(0, 4.1, 5.6), rz=8, mat="BH_CliffOchre", moss=False)
    rock_piece(k, (2.2, 1.4, 3.6), 500, pos=(0, 5.5, 0), mat="BH_CliffOchre", moss=False)
    k.put(box(2.8, 0.3, 5.6), "BH_Obsidian", M=T(0, 4.4, 2.8))
    # the vein knot inside the cleft
    ctr = Vector((0, 4.0, 2.6))
    for i in range(6):
        a = math.tau * i / 6 + 0.3
        p0 = ctr + Vector((math.cos(a) * 1.1, 0.2, math.sin(a) * 1.9))
        vein(k, p0, ctr, 0.03, 0.18, bulge=Vector((0, -0.3, 0)), caps=False)
    k.put(ico(0.36, 2), V, M=T(*ctr) @ S(1, 0.7, 1.25), smooth=60)
    # ribs over the cleft and a spine across the top
    for j, y in enumerate((1.75, 2.6, 3.4)):
        for sx in (-1, 1):
            broken = (j == 0 and sx > 0)
            pts = [Vector((sx * 2.7, y, -0.2)), Vector((sx * 3.0, y, 2.6)), Vector((sx * 2.3, y + 0.1, 5.2)),
                   Vector((sx * 0.7, y + 0.2, 6.6))]
            if broken:
                pts = pts[:3]
                pts[-1] = pts[1].lerp(pts[2], 0.55)
            k.put(tube(smooth_pts(pts, 3), 0.3, 7, flat=(1.0, 0.62)), B, smooth=40)
            for q in (pts[1], pts[2]):
                k.put(ico(0.24, 1), B, M=T(*q) @ S(1.0, 0.8, 1.2), smooth=40)
            k.put(ico(0.42, 1), B, M=T(sx * 2.7, y, 0.1) @ S(1, 1, 0.7), smooth=40)
    for i in range(7):
        y = 1.4 + i * 0.52
        k.put(cyl(0.45, 0.36, 9, bev=0.04), B, M=T(0, y, 6.75) @ R(90, 0, 0), smooth=40)
        k.put(cyl(0.12, 0.6, 5, r2=0.03), B, M=T(0, y, 7.0))
    # veins crawling over the rock faces into the cleft, and along the ground (never into the disc)
    for i in range(10):
        sx = -1 if i % 2 else 1
        p0 = Vector((sx * r.uniform(2.6, 5.4), r.uniform(1.0, 1.8), r.uniform(0.6, 6.0)))
        p1 = Vector((sx * r.uniform(1.2, 1.6), 3.2, r.uniform(1.2, 4.6)))
        vein(k, p0, p1, 0.04, 0.13, bulge=Vector((0, -0.5, 0)))
    for sx in (-1, 1):
        vein(k, Vector((sx * 4.8, -1.2, 0.03)), Vector((sx * 1.3, 2.8, 0.05)), 0.03, 0.12, flat_z=True)
    for i in range(4):
        sx = -1 if i % 2 else 1
        k.put(cyl(0.18, 1.1, 6, r2=0.0), B, M=T(sx * r.uniform(4.0, 5.2), r.uniform(2.0, 3.0), r.uniform(1.5, 5.0)) @
              R(r.uniform(-60, -20), sx * r.uniform(30, 60), 0))
    disc_ring(k, B, wire=False)
    k.sockets.append(("light", (0, 2.4, 2.8)))
    for sx in (-1, 1):
        k.col_box(4.0, 4.6, 6.4, T(sx * 3.9, 3.9, 3.2))
        for y in (1.75, 2.6, 3.4):
            k.col_box(0.7, 0.7, 2.0, T(sx * 2.8, y, 1.0))
    k.col_box(3.0, 2.0, 6.0, T(0, 5.4, 3.0))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# OCHRE SANDSTONE
def strata_rock(k, w, d, h, layers, pos=(0, 0, 0), rz=0.0, target=260, shrink=0.2, drift=(0.0, 0.0)):
    """Layered sandstone: a stack of flattened slabs, each a little smaller and offset, eroded at the edges."""
    r = k.r
    z = 0.0
    px, py, pz = pos
    for i in range(layers):
        hh = h / layers * r.uniform(0.85, 1.15)
        sc = 1.0 - shrink * i / max(1, layers - 1)
        size = (w / 2 * sc * r.uniform(0.9, 1.05), d / 2 * sc * r.uniform(0.9, 1.05), hh * 0.95)
        ox = drift[0] * i + r.uniform(-0.08, 0.08) * w
        oy = drift[1] * i + r.uniform(-0.08, 0.08) * d
        rock_piece(k, size, target, pos=(px + ox, py + oy, pz + z - 0.05), rz=rz + r.uniform(-9, 9), mat="BH_CliffOchre",
                   moss=False, flat_top=0.82, cuts=8, amp=0.035)
        z += hh * 0.9
    return z


@asset("zr_rock_ochre_large", CAT)
def zr_rock_ochre_large(k):
    """Layered ochre sandstone outcrop ~6.5 x 5 m, 4 m tall."""
    r = k.r
    strata_rock(k, 6.5, 5.0, 4.0, 4, target=320)
    strata_rock(k, 2.6, 2.2, 1.6, 2, pos=(3.2, -1.6, 0), rz=30, target=160)
    for i in range(5):
        s = r.uniform(0.25, 0.6)
        rock_piece(k, (s, s * 0.8, s * 0.45), 60, pos=(r.uniform(-3.5, 3.5), r.uniform(-3.2, -2.4), 0), rz=r.uniform(0, 360),
                   mat="BH_CliffOchre", moss=False)
    k.col_box(6.0, 4.6, 3.6, T(0, 0, 1.8))
    k.col_box(2.4, 2.0, 1.5, T(3.2, -1.6, 0.75))
    return dict(recenter=False)


@asset("zr_rock_ochre_medium", CAT)
def zr_rock_ochre_medium(k):
    """Layered ochre sandstone rock ~2.6 x 2 m, 1.8 m tall."""
    r = k.r
    strata_rock(k, 2.6, 2.0, 1.8, 3, target=150)
    rock_piece(k, (0.3, 0.25, 0.18), 40, pos=(1.4, -0.8, 0), rz=20, mat="BH_CliffOchre", moss=False)
    k.col_box(2.3, 1.8, 1.6, T(0, 0, 0.8))
    return dict(recenter=False)


def stratum(k, x0, x1, yf, yb, z0, h, amp=0.28, mat="BH_CliffOchre"):
    """One sandstone bed: a long slab with an eroded, undercut front edge (noise-displaced, chipped)."""
    r = k.r
    t = box(x1 - x0, yb - yf, h)
    bmesh.ops.subdivide_edges(t, edges=list(t.edges), cuts=3, use_grid_fill=True)
    t.normal_update()
    off = k.noff + Vector((x0 * 0.37, z0 * 0.53, yf * 0.21))
    for v in t.verts:
        n = mnoise.fractal(v.co * 0.45 + off, 0.55, 2.0, 3, noise_basis="PERLIN_ORIGINAL")
        front = max(0.0, -v.co.y / ((yb - yf) / 2))
        v.co.y += n * amp * 2.2 * front - 0.18 * front * (1.0 if v.co.z < 0 else 0.0)
        v.co.z += n * amp * 0.35
        v.co.x += n * amp * 0.4
    chip(t, r, 3, h * 0.25)
    k.put(t, mat, M=T((x0 + x1) / 2, (yf + yb) / 2, z0 + h / 2), smooth=35)


@asset("zr_cliff_ochre", CAT)
def zr_cliff_ochre(k):
    """Ochre cliff piece 12 m wide, ~10 m tall: horizontal sandstone beds stepping back, some overhanging; face
    toward Godot +Z, back roughly flat at Godot z = -3.6."""
    r = k.r
    z = 0.0
    yb = 3.6
    i = 0
    while z < 9.6:
        h = r.uniform(1.0, 1.7) if i % 3 != 1 else r.uniform(0.5, 0.8)
        yf = -2.4 + 0.32 * i + (-0.45 if i % 3 == 1 else 0.0) + r.uniform(-0.15, 0.15)
        xs = sorted([-6.1, 6.1] + [r.uniform(-3.5, 3.5) for _ in range(r.randint(0, 1) + 1)])
        for x0, x1 in zip(xs[:-1], xs[1:]):
            stratum(k, x0 - 0.05, x1 + 0.05, yf + r.uniform(-0.2, 0.2), yb, z, min(h, 10.0 - z))
        z += h
        i += 1
    for j in range(8):
        sz = r.uniform(0.3, 0.8)
        rock_piece(k, (sz, sz * 0.8, sz * 0.5), 50, pos=(r.uniform(-5.5, 5.5), r.uniform(-3.6, -2.7), 0), rz=r.uniform(0, 360),
                   mat="BH_CliffOchre", moss=False)
    k.col_box(12.2, 6.0, 4.0, T(0, 0.6, 2.0))
    k.col_box(12.2, 5.2, 4.0, T(0, 1.0, 6.0))
    k.col_box(12.2, 4.4, 2.0, T(0, 1.4, 9.0))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# THE HEART CITADEL
def ring_band(sub, R_, w=0.36, th=0.26, glyphs=16):
    """A bronze ring lying in the local XY plane: flat band, inlaid wire on the inner face, glyph inlays outside."""
    t = lathe([(R_ - w, -th / 2), (R_, -th / 2), (R_, th / 2), (R_ - w, th / 2), (R_ - w, -th / 2)], 64,
              cap_bot=False, cap_top=False)
    sub.put(t, "BH_Brass", smooth=30)
    sub.put(torus(R_ - w - 0.02, 0.06, 64, 5), "BH_Wire", smooth=50)
    for zz in (-th / 2 - 0.02, th / 2 + 0.02):
        sub.put(torus(R_ - 0.02, 0.035, 64, 4), "BH_Brass", M=T(0, 0, zz * 0.9), smooth=50)
    for i in range(glyphs):
        a = math.tau * (i + 0.5) / glyphs
        sub.put(box(0.06, 0.34, th * 0.6), "BH_Glyph", M=T(math.cos(a) * (R_ + 0.01), math.sin(a) * (R_ + 0.01), 0) @
                R(0, 0, math.degrees(a)))
        sub.put(box(0.1, 0.12, th + 0.08), "BH_Brass", M=T(math.cos(a + math.pi / glyphs) * (R_ - w / 2),
                                                           math.sin(a + math.pi / glyphs) * (R_ - w / 2), 0) @
                R(0, 0, math.degrees(a + math.pi / glyphs)))


@asset("zr_dawn_engine", CAT)
def zr_dawn_engine(k):
    """The Dawn Engine: stepped base (top at 3.6 m), a great wire-wound core to ~11.8 m, three bronze rings as child
    nodes ring_1..ring_3 centred at (0, 7.6, 0) Godot, Kharvenn chains clamped round it. Front stair on Godot +Z."""
    r = k.r
    z = 0.0
    for (w, h) in ((14.0, 1.4), (11.0, 1.2), (8.0, 1.0)):
        z = tier(k, w, w, z, h, talus=0.35, inset=0.3, mat=GS, trim=GS, chips=6)
    ztop = z
    for side in ("front", "back", "left", "right"):
        fret_band(k, -5.0, 5.0, 2.05, 0.55, M=face_M(side, 11.0 / 2 - 0.3 + 0.12 - 0.1), mat=GS, back="BH_LimePlasterRed")
        wire_run(k, (-6.4, 0, 0.75), (6.4, 0, 0.75), Vector((0, -1, 0)), w=0.16, clamps=1.6,
                 M=face_M(side, 14.0 / 2 - 0.3 * 0.9 + 0.12 - 0.1))
    # front stair to the top tier, with serpent heads at its foot
    run_y0, run_y1 = -8.4, -3.9
    n = 12
    rise = ztop / n
    for i in range(n):
        y0 = run_y0 + (run_y1 - run_y0) * i / n
        blk(k, 3.2, run_y1 - y0, rise, T(0, (y0 + run_y1) / 2, rise * (i + 0.5)), GS, chips=1, chipd=0.05)
    for sx in (-1, 1):
        hx(k, [(sx * 1.6, run_y0, 0), (sx * 2.2, run_y0, 0), (sx * 2.2, run_y1, 0), (sx * 1.6, run_y1, 0),
               (sx * 1.6, run_y0, 0.6), (sx * 2.2, run_y0, 0.6), (sx * 2.2, run_y1, ztop + 0.5), (sx * 1.6, run_y1, ztop + 0.5)],
           GS, chips=3, chipd=0.1)
        serpent_head(k, T(sx * 1.9, run_y0 - 0.2, 0.0), s=1.05, gape=0.3, accent="BH_Turquoise")
        wire_run(k, (sx * 1.9, run_y0, 0.62), (sx * 1.9, run_y1, ztop + 0.52), UP, w=0.1, clamps=0.8)
    # core plinth and the wire-wound core
    k.put(cyl(2.7, 0.8, 24, bev=0.05), GS, M=T(0, 0, ztop))
    k.put(cyl(2.35, 0.25, 24), "BH_Brass", M=T(0, 0, ztop + 0.8))
    prof = [(1.5, ztop + 1.05), (1.9, 5.6), (2.05, 7.0), (1.9, 8.4), (1.45, 9.6), (0.9, 10.5)]
    k.put(lathe([(0.0, ztop + 1.0)] + prof + [(0.0, 10.55)], 20), "BH_Copper", smooth=40)
    zz = ztop + 1.25
    i = 0
    while zz < 10.3:
        rad = 0
        for (a, b) in zip(prof[:-1], prof[1:]):
            if a[1] <= zz <= b[1]:
                rad = lerp(a[0], b[0], (zz - a[1]) / (b[1] - a[1]))
        if i % 4 == 3:
            k.put(torus(rad + 0.06, 0.12, 24, 5), "BH_Brass", M=T(0, 0, zz), smooth=50)
        else:
            k.put(torus(rad + 0.03, 0.075, 24, 5), "BH_Wire", M=T(0, 0, zz), smooth=50)
        zz += 0.32
        i += 1
    # crown: bronze cage of four ribs over a glowing heart node
    for j in range(4):
        a = math.tau * j / 4 + math.pi / 4
        k.put(tube([(math.cos(a) * 0.85, math.sin(a) * 0.85, 10.4), (math.cos(a) * 1.05, math.sin(a) * 1.05, 11.0),
                    (math.cos(a) * 0.35, math.sin(a) * 0.35, 11.8)], 0.08, 6), "BH_Brass", smooth=40)
    k.put(ico(0.55, 2), "BH_Wire", M=T(0, 0, 11.05), smooth=60)
    k.put(cyl(0.07, 0.8, 6, r2=0.0), "BH_Brass", M=T(0, 0, 11.75))
    # Kharvenn chains: a collar of chain round the core's foot, four chains to iron clamps and rune-spikes
    cz = ztop + 1.6
    pts = [(math.cos(math.tau * i / 16) * 1.8, math.sin(math.tau * i / 16) * 1.8, cz) for i in range(17)]
    chain_path(k, pts, R_=0.2, r_=0.05)
    k.put(box(0.9, 0.9, 0.7, bev=0.04), "BH_Iron", M=T(0, -1.95, cz))
    k.put(box(0.4, 0.06, 0.35), "BH_Blackwire", M=T(0, -2.42, cz))
    for j in range(4):
        a = math.tau * j / 4 + math.pi / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        clamp = d * 3.6 + Vector((0, 0, ztop))
        k.put(box(0.9, 0.9, 0.35, bev=0.04), "BH_Iron", M=T(*(clamp + Vector((0, 0, 0.17)))) @ R(0, 0, math.degrees(a)))
        k.put(box(0.06, 0.4, 0.2), "BH_Blackwire", M=T(*(clamp + d * 0.47 + Vector((0, 0, 0.2)))) @ R(0, 0, math.degrees(a)))
        top = rune_spike(k, d * 8.6 + Vector((0, 0, -0.05)), d, H=2.2, w=0.4)
        chain_path(k, [d * 1.85 + Vector((0, 0, cz)), clamp + Vector((0, 0, 0.4))], R_=0.2, r_=0.05)
        chain_path(k, [clamp + Vector((0, 0, 0.4)), d * 5.6 + Vector((0, 0, 2.1)), d * 7.1 + Vector((0, 0, 1.6)), top],
                   R_=0.2, r_=0.05)
    # the three rings (children; the game spins each about its local up axis)
    subs = []
    for name, R_, rot in (("ring_1", 5.4, (12, 0, -30)), ("ring_2", 4.5, (-25, 0, 50)), ("ring_3", 3.6, (35, 0, 15))):
        sub = kit.Kit(k.name + "_" + name)
        ring_band(sub, R_, glyphs=16 if R_ > 4 else 12)
        subs.append((name, sub, (0, 0, 7.6), rot))
    attach_children(k, subs)
    k.sockets.append(("light", (0, 0, 7.6)))
    k.col_box(14.0, 14.0, 1.4, T(0, 0, 0.7))
    k.col_box(11.0, 11.0, 2.6, T(0, 0, 1.3))
    k.col_box(8.0, 8.0, ztop, T(0, 0, ztop / 2))
    L = math.hypot(run_y1 - run_y0, ztop)
    k.col_mesh(box(3.2, L, 0.25), TRS(0, (run_y0 + run_y1) / 2, ztop / 2 - 0.12,
                                       math.degrees(math.atan2(ztop, run_y1 - run_y0)), 0, 0))
    k.col_mesh(cyl(2.4, 10.6 - ztop, 12), T(0, 0, ztop))
    return dict(recenter=False)


@asset("zr_citadel_wall", CAT)
def zr_citadel_wall(k):
    """Heart Citadel wall segment, 8 m along X, 9 m tall, ~3.6 m thick at the foot; tiles along X."""
    r = k.r
    L = 8.0
    hx(k, [(-L / 2, -1.8, 0), (L / 2, -1.8, 0), (L / 2, 1.8, 0), (-L / 2, 1.8, 0),
           (-L / 2, -1.4, 3.0), (L / 2, -1.4, 3.0), (L / 2, 1.4, 3.0), (-L / 2, 1.4, 3.0)], GS, chips=4, chipd=0.18,
       moss=(0.55, 0.7, -0.1))
    blk(k, L, 2.6, 4.7, T(0, 0, 3.0 + 2.35), GSD, chips=0)
    for face_y in (-1, 1):
        zc = 3.0
        for ci, h in enumerate((1.15, 1.2, 1.1, 1.25)):
            ws, _ = split_lengths(r, L, 1.4, 2.3)
            x = -L / 2
            for w in ws:
                blk(k, w - 0.05, 0.4, h - 0.05, T(x + w / 2, face_y * 1.3, zc + h / 2), GS, chips=2, chipd=0.1)
                x += w
            zc += h
        Mf = T(0, face_y * 1.5, 0) @ (R(0, 0, 0) if face_y < 0 else R(0, 0, 180))
        fret_band(k, -L / 2, L / 2, 6.95, 0.9, M=Mf, mat=GS, back=GSD)
        wire_run(k, (-L / 2, face_y * 1.5, 5.85), (L / 2, face_y * 1.5, 5.85), Vector((0, face_y, 0)), w=0.16,
                 clamps=1.6, mat="BH_Verdigris")
        for xx in (-2.0, 2.0):
            wire_run(k, (xx, face_y * 1.5, 5.75), (xx, face_y * 1.5, 3.1), Vector((0, face_y, 0)), w=0.14, clamps=1.2,
                     mat="BH_Verdigris")
    blk(k, L, 3.3, 0.45, T(0, 0, 7.7 + 0.22), GS, chips=4, moss=(0.85, 1.0, -0.2))
    for face_y in (-1, 1):
        merlons(k, -L / 2, L / 2, face_y * 1.3, 8.15, 4, h=1.0, w=1.2, d=0.7)
    slab_floor(k, L, 1.9, 8.18, th=0.1, rows=(0.8, 1.0), lens=(0.9, 1.4), mat="BH_TerracePave", gap=0.04)
    k.col_box(L, 3.6, 3.0, T(0, 0, 1.5))
    k.col_box(L, 3.3, 6.2, T(0, 0, 3.0 + 3.1))
    return dict(recenter=False)


@asset("zr_citadel_tower", CAT)
def zr_citadel_tower(k):
    """Heart Citadel tower 7 x 7 m, 14 m tall: talus-and-panel tiers, stepped crenels, a doorway on Godot +Z,
    Kharvenn chains hanging down its front."""
    r = k.r
    z = tier(k, 7.0, 7.0, 0.0, 6.0, talus=0.4, inset=0.5, chips=6)
    z = tier(k, 6.2, 6.2, z, 4.6, talus=0.3, inset=0.35, chips=5)
    z = tier(k, 5.4, 5.4, z, 2.2, talus=0.3, inset=0.25, chips=4, moss=False)
    ztop = z
    for yy in (-2.3, 2.3):
        merlons(k, -2.0, 2.0, yy, ztop, 3, h=1.2, w=0.75, d=0.6)
    for xx in (-2.3, 2.3):
        merlons(k, xx, xx, -0.0, ztop, 1, h=1.2, w=0.6, d=0.75)
    p1 = 7.0 / 2 - 0.5 + 0.12 - 0.1
    p2 = 6.2 / 2 - 0.35 + 0.12 - 0.1
    for side in ("front", "back", "left", "right"):
        fret_band(k, -2.4, 2.4, 4.85, 0.8, M=face_M(side, p1), mat=GS, back="BH_LimePlasterRed")
        glyph(k, face_M(side, p2, 8.9), s=1.3, d=0.07, mat="BH_Verdigris")
        for xx in (-1.6, 1.6):
            wire_run(k, (xx, 0, 3.0), (xx, 0, 4.3), Vector((0, -1, 0)), w=0.13, clamps=1.0, mat="BH_Verdigris",
                     M=face_M(side, p1))
            wire_run(k, (xx, 0, 7.6), (xx, 0, 10.2), Vector((0, -1, 0)), w=0.13, clamps=1.0, mat="BH_Verdigris",
                     M=face_M(side, p2))
    # doorway (front)
    yd = -(7.0 / 2)
    k.put(box(1.9, 0.5, 2.9), "BH_Obsidian", M=T(0, yd + 0.3, 1.45))
    for sx in (-1, 1):
        blk(k, 0.5, 0.9, 3.0, T(sx * 1.2, yd + 0.2, 1.5), GS, chips=2)
    blk(k, 3.0, 1.0, 0.6, T(0, yd + 0.2, 3.25), GS, chips=3)
    # Kharvenn chains hanging down the front from the crenels, with a rune plate
    for sx in (-1, 1):
        chain_path(k, [(sx * 1.3, -2.75, ztop + 0.5), (sx * 1.3, -3.1, 9.0), (sx * 1.2, -3.15, 6.4)], R_=0.14, r_=0.035)
    k.put(box(1.4, 0.12, 1.0, bev=0.02), "BH_Iron", M=T(0, -3.12, 8.2))
    for sx in (-1, 1):
        chain_path(k, [(sx * 1.25, -3.1, 6.6), (sx * 0.5, -3.16, 8.6)], R_=0.1, r_=0.028)
    glyph(k, T(0, -3.19, 8.2), s=0.7, mat="BH_Blackwire", frame_mat="BH_Iron", d=0.04)
    k.col_box(7.0, 7.0, ztop, T(0, 0, ztop / 2))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# THE KHARVENN CAMP
def cloth_panel(k, c, nu, nv, sag, mat="BH_Cloth", wave=0.0, th=0.02):
    """Bilinear cloth sheet between corners c=(p00, p10, p11, p01) with a sag vector (max at the middle), both
    sides modelled."""
    r = k.r
    c = [Vector(p) for p in c]
    sag = Vector(sag)
    t = tb()
    grid, grid2 = [], []
    for j in range(nv + 1):
        v = j / nv
        row, row2 = [], []
        for i in range(nu + 1):
            u = i / nu
            p = (c[0] * (1 - u) + c[1] * u) * (1 - v) + (c[3] * (1 - u) + c[2] * u) * v
            p += sag * (math.sin(math.pi * u) * math.sin(math.pi * v) if v < 1 else 0.0)
            if wave:
                p += sag.normalized() * wave * math.sin(u * 9 + v * 3) * v if sag.length > 0 else Vector()
            row.append(t.verts.new(p))
        grid.append(row)
    nrm = (c[1] - c[0]).cross(c[3] - c[0]).normalized()
    for j in range(nv + 1):
        grid2.append([t.verts.new(v.co - nrm * th) for v in grid[j]])
    for j in range(nv):
        for i in range(nu):
            t.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            t.faces.new((grid2[j + 1][i], grid2[j + 1][i + 1], grid2[j][i + 1], grid2[j][i]))
    k.put(t, mat, smooth=50)


@asset("zr_kharvenn_tent", CAT)
def zr_kharvenn_tent(k):
    """Kharvenn chain-priest tent 4 x 4 m: iron frame, grey canvas, side flaps hung on chains, front open (Godot +Z)."""
    r = k.r
    H, A = 2.2, 3.5
    cs = [(-2, -2), (2, -2), (2, 2), (-2, 2)]
    for (x, y) in cs:
        k.put(box(0.12, 0.12, H + 0.15, bev=0.01), "BH_Iron", M=T(x, y, (H + 0.15) / 2))
        k.put(cyl(0.12, 0.25, 6, r2=0.0), "BH_Iron", M=T(x, y, H + 0.15))
        beam_(k, (x, y, H), (0, 0, A), 0.09, "BH_Iron")
    for i in range(4):
        a, b = cs[i], cs[(i + 1) % 4]
        beam_(k, (a[0], a[1], H), (b[0], b[1], H), 0.08, "BH_Iron")
    k.put(cyl(0.05, 0.6, 6, r2=0.0), "BH_Iron", M=T(0, 0, A))
    k.put(torus(0.16, 0.04, 10, 4), "BH_Iron", M=T(0, 0, A + 0.15) @ R(90, 0, 0))
    # roof canvas (four sagging panels)
    for i in range(4):
        a, b = cs[i], cs[(i + 1) % 4]
        cloth_panel(k, [(a[0] * 1.08, a[1] * 1.08, H - 0.1), (b[0] * 1.08, b[1] * 1.08, H - 0.1), (0, 0, A), (0, 0, A)],
                    4, 3, (0, 0, -0.12))
    # walls: back and sides hang on chains from the eave rail; the front is two flaps tied back
    for i, (a, b) in enumerate(((cs[1], cs[2]), (cs[2], cs[3]), (cs[3], cs[0]))):
        a3, b3 = Vector((a[0], a[1], 0.05)), Vector((b[0], b[1], 0.05))
        out = Vector((a[0] + b[0], a[1] + b[1], 0)).normalized() * 0.08
        cloth_panel(k, [a3 + out, b3 + out, b3 + out + Vector((0, 0, H - 0.5)), a3 + out + Vector((0, 0, H - 0.5))],
                    4, 3, out * 1.6)
        for j in range(3):
            p = Vector((a[0], a[1], H)).lerp(Vector((b[0], b[1], H)), (j + 0.5) / 3) + out
            chain_links(k, p, p + Vector((0, 0, -0.45)), R_=0.06, r_=0.016)
        k.put(box(4.0, 0.03, 0.12), "BH_ClothBlack",
              M=T(*((Vector((a[0], a[1], 0)) + Vector((b[0], b[1], 0))) / 2 + out * 1.3 + Vector((0, 0, H - 0.48)))) @
              R(0, 0, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))))
    for sx in (-1, 1):
        cloth_panel(k, [(sx * 2.0, -2.08, 0.1), (sx * 1.1, -2.6, 0.1), (sx * 1.05, -2.5, H - 0.2), (sx * 2.0, -2.08, H - 0.1)],
                    3, 4, (sx * 0.1, -0.15, 0))
        chain_links(k, (sx * 2.0, -2.0, 1.2), (sx * 1.2, -2.55, 1.15), R_=0.06, r_=0.016)
    # rune banner plate over the entrance, guy chains to spikes, a censer stand
    k.put(box(1.0, 0.08, 0.6, bev=0.02), "BH_Iron", M=T(0, -2.1, H - 0.4))
    glyph(k, T(0, -2.14, H - 0.4), s=0.5, mat="BH_Blackwire", frame_mat="BH_Iron", d=0.03)
    for (x, y) in cs:
        d = Vector((x, y, 0)).normalized()
        top = rune_spike(k, Vector((x, y, 0)) + d * 1.3, d, H=0.6, w=0.16)
        chain_links(k, (x, y, H), top, R_=0.06, r_=0.016)
    k.put(cyl(0.05, 1.0, 6), "BH_Iron", M=T(1.4, -3.0, 0))
    k.put(lathe([(0.0, 0.0), (0.25, 0.05), (0.3, 0.25), (0.22, 0.28)], 10), "BH_Iron", M=T(1.4, -3.0, 1.0))
    k.put(ico(0.13, 1), "BH_Blackwire", M=T(1.4, -3.0, 1.2))
    k.put(box(1.8, 0.8, 0.12), "BH_ClothBlack", M=T(0, 1.0, 0.06))
    k.col_box(4.2, 0.3, H, T(0, 2.0, H / 2))
    for sx in (-1, 1):
        k.col_box(0.3, 4.2, H, T(sx * 2.0, 0, H / 2))
    return dict(recenter=False)


@asset("zr_chain_rack", CAT)
def zr_chain_rack(k):
    """Kharvenn rack of rune-chains and spikes: an iron trestle 3 m long with chains draped over it."""
    r = k.r
    Hb = 2.0
    for sx in (-1.4, 1.4):
        for sy in (-1, 1):
            beam_(k, (sx, sy * 0.7, 0), (sx, 0, Hb), 0.1, "BH_Iron")
        beam_(k, (sx, -0.45, 0.6), (sx, 0.45, 0.6), 0.07, "BH_Iron")
        k.put(box(0.16, 0.3, 0.12), "BH_Iron", M=T(sx, 0, Hb + 0.02))
    beam_(k, (-1.65, 0, Hb + 0.05), (1.65, 0, Hb + 0.05), 0.12, "BH_Iron")
    for i, x in enumerate((-1.0, -0.35, 0.3, 0.95)):
        hang_f = r.uniform(0.8, 1.5)
        hang_b = r.uniform(0.6, 1.4)
        top = Vector((x, 0, Hb + 0.15))
        chain_path(k, [Vector((x + 0.05, -0.18, Hb + 0.05 - hang_f)), Vector((x, -0.12, Hb - hang_f * 0.4)), top,
                       Vector((x, 0.12, Hb - hang_b * 0.4)), Vector((x - 0.04, 0.2, Hb + 0.05 - hang_b))], R_=0.11, r_=0.03)
        k.put(box(0.12, 0.04, 0.1), "BH_Blackwire", M=T(x + 0.05, -0.22, Hb - hang_f - 0.05))
    for j, x in enumerate((-1.1, 0.0, 1.0)):
        rune_spike(k, (0, 0, 0), (0, 0, 0), H=1.7, w=0.22, M=T(x, -0.95, 0.0) @ R(-22, 0, r.uniform(-8, 8)))
    for j in range(3):
        rune_spike(k, (0, 0, 0), (0, 0, 0), H=1.5, w=0.2, M=T(-0.4 + j * 0.45, 1.3, 0.12 + (j % 2) * 0.05) @ R(0, 90, 10 + j * 8))
    k.col_box(3.4, 1.6, 2.2, T(0, 0, 1.1))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# WYMAN OUTPOST
@asset("zr_jetty_wood", CAT)
def zr_jetty_wood(k):
    """Wooden marsh jetty segment, 4 m along Godot Z x 3 m wide, deck top at the origin; piles to -2.5 m.
    Tiles end to end along Godot Z (piles at Godot z = +-1)."""
    from assets_props import plank
    r = k.r
    W, L = 3.0, 4.0
    n = 13
    for i in range(n):
        y = -L / 2 + L * (i + 0.5) / n
        plank(k, W + r.uniform(-0.1, 0.12), L / n - 0.035, 0.07, TRS(r.uniform(-0.05, 0.05), y, -0.035, 0, 0, r.uniform(-1.5, 1.5)),
              mat="BH_Wood", warp=0.01)
    for sx in (-1, 1):
        k.put(box(0.18, L, 0.24, bev=0.02), "BH_WoodDark", M=T(sx * 1.2, 0, -0.19))
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(cyl(0.13, 2.65, 8, r2=0.12), "BH_WoodDark", M=T(sx * 1.35, sy * 1.0, -2.55), smooth=40)
            k.put(cyl(0.135, 0.3, 8), "BH_Moss", M=T(sx * 1.35, sy * 1.0, -1.15), smooth=40)
        beam_(k, (sx * 1.45, -1.0, -0.45), (sx * 1.45, 1.0, -1.9), 0.1, "BH_WoodDark", h=0.16)
    for sy in (-1, 1):
        beam_(k, (-1.35, sy * 1.0, -0.42), (1.35, sy * 1.0, -0.42), 0.12, "BH_WoodDark", h=0.18)
    # mooring post with rope coil and an iron ring
    k.put(cyl(0.16, 3.4, 8, r2=0.14), "BH_WoodDark", M=T(1.62, 0.0, -2.5), smooth=40)
    k.put(cyl(0.17, 0.08, 8), "BH_Iron", M=T(1.62, 0.0, 0.62))
    for j in range(3):
        k.put(torus(0.2, 0.035, 10, 4), "BH_Rope", M=T(1.62, 0.0, 0.25 + j * 0.07), smooth=40)
    k.put(torus(0.1, 0.022, 10, 4), "BH_Iron", M=T(1.78, 0.0, 0.45) @ R(0, 90, 0))
    k.col_box(W, L, 0.3, T(0, 0, -0.15))
    k.col_box(0.35, 0.35, 0.95, T(1.62, 0.0, 0.47))
    return dict(recenter=False)
