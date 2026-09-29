"""bh-018 trade-quarter stands, part B (see work/lemondev/bh-018/contracts/stands.md).

Five purpose-built shop stands, each with its own roof shape and material (the game camera sees mostly roofs):
  stand_jeweller     3.6 x 2.6  teal ogee bell canopy, scalloped gold-fringed valance, gilded crane finial
  stand_apothecary   4.6 x 3.2  steep thatched gable turned to the front (open A-front), herbs drying from the rafters
  stand_armsbroker   5.0 x 3.4  twin-peaked crimson marquee with black scalloped valance and gold pole finials
  stand_gemcutter    3.8 x 3.8  open octagonal kiosk, concave lead-grey slate spire, big glowing crystal finial
  stand_crystal_cart 3.6 x 2.6  prospector's handcart under a twisted ochre sail (hyperbolic shade) on two poles

Conventions (contract): metres, Z-up, front (customer side) toward -Y, origin at the bottom centre of the footprint,
recenter=False. Colour comes from material choice only (the game ignores vertex tint). BH_Glass is an opaque, warm,
self-lit lantern pane in game, so it is used for lantern glass only; display glass and specimen cloches are drawn as
gilded frames / brass cages around the goods instead of panes.
Sockets: npc, customer, light_a, light_b (+ flame at the apothecary's still). Head-visibility: from (npc, z 1.8) the ray
rising 1.38 m per metre toward -Y clears every roof (checked in work/lemondev/bh-018/scratch/builder_b/render_stands.py).
"""
import math

import bmesh
from mathutils import Vector, Matrix

from kit import *  # noqa
import market_common  # noqa  (registers the extra BH_* materials)
from registry import asset
from assets_props import plank, rivet, wheel, flame_tip
from assets_town2 import hang_lantern, keg
from assets_nature import align_z

GEMS = ("BH_GemRed", "BH_GemAqua", "BH_GemAmber", "BH_GemGreen", "BH_GemViolet", "BH_GemGold")


# =================================================================================================================
# shared helpers
def grid(fn, nu, nv):
    """Open quad grid from fn(u, v) -> (x, y, z), u, v in [0, 1]."""
    t = tb()
    rows = [[t.verts.new(Vector(fn(i / nu, j / nv))) for i in range(nu + 1)] for j in range(nv + 1)]
    for j in range(nv):
        for i in range(nu):
            t.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    return t


def solid(t, th):
    """Give an open sheet a real thickness (single-sided cloth would vanish from below with back-face culling)."""
    bmesh.ops.recalc_face_normals(t, faces=list(t.faces))
    bmesh.ops.solidify(t, geom=list(t.faces), thickness=th)
    bmesh.ops.recalc_face_normals(t, faces=list(t.faces))
    return t


def sheet(k, fn, nu, nv, mat, th=0.02, smooth=40):
    k.put(solid(grid(fn, nu, nv), th), mat, smooth=smooth)


def rod(k, p0, p1, r_, mat, segs=6):
    k.put(tube([p0, p1], r_, segs), mat, smooth=40)


def rope_line(k, pts, r_=0.012, mat="BH_Rope"):
    k.put(tube(pts, r_, 4), mat, smooth=40)


def sag_pts(p0, p1, sag, n=6):
    p0, p1 = Vector(p0), Vector(p1)
    return [p0.lerp(p1, i / n) - Vector((0, 0, sag * 4 * (i / n) * (1 - i / n))) for i in range(n + 1)]


def valance(k, p0, p1, ztop, band, lobe, n, mat, edge=None, tassel=None, per=6, th=0.012):
    """Scalloped hanging border from p0 to p1 (xy), top at ztop: straight band then n rounded tongues. An optional
    edge material binds the scalloped hem; optional tassels hang from each tongue tip."""
    p0, p1 = Vector(p0), Vector(p1)

    def bot(u):
        f = (u * n) % 1.0
        return ztop - band - lobe * math.sqrt(max(0.0, 1.0 - (2.0 * f - 1.0) ** 2))

    def P(u, z):
        return (p0.x + (p1.x - p0.x) * u, p0.y + (p1.y - p0.y) * u, z)
    k.put(solid(grid(lambda u, v: P(u, lerp(ztop, bot(u), v)), n * per, 1), th), mat, smooth=None)
    if edge:
        k.put(solid(grid(lambda u, v: P(u, bot(u) + 0.04 * (1 - v) - 0.004), n * per, 1), th * 1.8), edge, smooth=None)
    if tassel:
        for i in range(n):
            u = (i + 0.5) / n
            x, y, z = P(u, bot(u))
            k.put(cyl(0.005, 0.03, 4), tassel, M=T(x, y, z - 0.028))
            k.put(cyl(0.02, 0.075, 6, r2=0.007), tassel, M=T(x, y, z - 0.1))


def rect_roof(k, hx, hy, prof, mat, cy=0.0, per=(10, 7), th=0.035, sag=0.0):
    """Roof over a rectangle (+-hx, cy+-hy) following prof [(scale, z)] from eave (scale 1) to apex (scale 0).
    sag lowers the middle of every side a little (cloth between the hip ribs)."""
    t = tb()
    nx, ny = per

    def ring(s, z):
        pts = []
        sides = (((-hx, -hy), (hx, -hy), nx), ((hx, -hy), (hx, hy), ny), ((hx, hy), (-hx, hy), nx),
                 ((-hx, hy), (-hx, -hy), ny))
        for (a, b, n) in sides:
            for i in range(n):
                f = i / n
                x = lerp(a[0], b[0], f) * s
                y = lerp(a[1], b[1], f) * s + cy
                pts.append(Vector((x, y, z - sag * math.sin(math.pi * f) * s)))
        return pts
    rings = [[t.verts.new(p) for p in ring(s, z)] for (s, z) in prof[:-1]]
    apex = t.verts.new((0.0, cy, prof[-1][1]))
    m = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(m):
            j = (i + 1) % m
            t.faces.new((a[i], a[j], b[j], b[i]))
    for i in range(m):
        t.faces.new((rings[-1][i], rings[-1][(i + 1) % m], apex))
    k.put(solid(t, th), mat, smooth=50)


def gem(k, M, s, mat, segs=6):
    """Cut stone (crown + pavilion), table up, ~2*s wide."""
    k.put(lathe([(0.0, -0.75 * s), (s, 0.0), (0.62 * s, 0.38 * s), (0.0, 0.38 * s)], segs), mat, M=M)


def spike(k, base, d, L, r_, mat, segs=6, tip=0.3):
    """Hexagonal crystal point from base along direction d."""
    prof = [(r_ * 0.78, -0.04 * L), (r_, 0.12 * L), (r_ * 0.9, L * (1 - tip)), (0.0, L)]
    t = lathe(prof, segs)
    jitter(t, k.r, r_ * 0.05)
    k.put(t, mat, M=T(*Vector(base)) @ align_z(Vector(d), k.r.uniform(0, 6.283)))


def cluster(k, M, n, L, r_, mats, spread=0.55, rad=None):
    """n crystal points growing from a small patch at M (local +Z = growth direction)."""
    r = k.r
    rad = r_ * 1.2 if rad is None else rad
    R3 = M.to_3x3()
    for i in range(n):
        a = r.uniform(0, 6.283)
        b = Vector((math.cos(a) * rad * r.uniform(0.0, 1.0), math.sin(a) * rad * r.uniform(0.0, 1.0), 0.0))
        d = Vector((b.x / max(rad, 1e-4) * spread + r.uniform(-0.15, 0.15),
                    b.y / max(rad, 1e-4) * spread + r.uniform(-0.15, 0.15), 1.0))
        s = 1.0 if i == 0 else r.uniform(0.45, 0.85)
        spike(k, M @ b, R3 @ d, L * s, r_ * (s if i else 1.0), mats[i % len(mats)])


def ore_rock(k, M, s, mat="BH_StoneDark", target=40):
    r = k.r
    t = rock(r, (s, s * r.uniform(0.7, 0.95), s * r.uniform(0.55, 0.8)), cuts=6, subd=1, noise_amp=0.05,
             seed_off=r.uniform(0, 40), target=target)
    k.put(t, mat, M=M, smooth=None)


def geode_half(k, M, R_=0.16, lining="BH_GemViolet", n=9):
    """Split geode: rough stone cup with its cut face toward local +Z, lined with crystal points."""
    r = k.r
    t = lathe([(0.0, -R_), (R_ * 0.72, -R_ * 0.72), (R_, -0.02), (R_ * 0.78, 0.0), (R_ * 0.7, -R_ * 0.45),
               (0.0, -R_ * 0.66)], 9)
    jitter(t, r, R_ * 0.06)
    k.put(t, "BH_StoneDark", M=M, smooth=None)
    k.put(torus(R_ * 0.8, R_ * 0.07, 9, 3), "BH_Stone", M=M @ T(0, 0, -0.005))
    for i in range(n):
        a = math.tau * i / n + r.uniform(-0.2, 0.2)
        rr = R_ * r.uniform(0.25, 0.6)
        base = M @ Vector((math.cos(a) * rr, math.sin(a) * rr, -R_ * 0.45 + (rr / R_) * 0.12 * R_))
        d = M.to_3x3() @ Vector((-math.cos(a) * 0.5, -math.sin(a) * 0.5, 1.0))
        spike(k, base, d, R_ * r.uniform(0.35, 0.55), R_ * 0.09, lining, segs=5)


def ring_jewel(k, M, metal, stone, R_=0.022):
    """Finger ring lying in its local XY plane with the stone at +Y."""
    k.put(torus(R_, R_ * 0.26, 10, 4), metal, M=M, smooth=40)
    gem(k, M @ T(0, R_ * 1.05, R_ * 0.45), R_ * 0.55, stone, segs=6)


def amulet(k, M, metal, stone):
    """Pendant disc + stone with its chain loop, lying in local XY (loop toward +Y)."""
    k.put(cyl(0.034, 0.01, 12), metal, M=M)
    k.put(torus(0.034, 0.005, 12, 3), metal, M=M @ T(0, 0, 0.008))
    gem(k, M @ T(0, 0, 0.018), 0.018, stone, segs=6)
    k.put(torus(0.07, 0.004, 16, 3), metal, M=M @ T(0, 0.098, 0.002) @ S(0.75, 1.0, 1.0))


def necklace(k, top, w, h, metal, stone):
    """Chain loop hanging from a hook point (in the XZ plane) with a pendant stone at the bottom."""
    top = Vector(top)
    pts = []
    for i in range(13):
        a = math.tau * i / 12
        pts.append(top + Vector((0.5 * w * math.sin(a), 0.0, -h * (1 - math.cos(a)) / 2)))
    k.put(tube(pts, 0.0035, 3, closed=True), metal)
    gem(k, T(top.x, top.y - 0.004, top.z - h - 0.012) @ R(90, 0, 0), 0.016, stone, segs=6)


def herb_bundle(k, top, L=0.3, mat="BH_Moss", tip=None, string=0.1):
    """Bunch of herbs hung upside down from `top` on a short string: tie at the top, leaves fanning downward."""
    r = k.r
    x, y, z = top
    rope_line(k, [(x, y, z), (x, y, z - string)], 0.006)
    t = cyl(0.022, L, 6, r2=r.uniform(0.06, 0.085))
    subdiv(t, 1)
    ndisp(t, 9.0, 0.018, k.noff + Vector((x, y, z)))
    jitter(t, r, 0.008)
    zt = z - string
    k.put(t, mat, M=T(x, y, zt) @ R(180 + r.uniform(-6, 6), r.uniform(-6, 6), r.uniform(0, 90)), smooth=35)
    k.put(torus(0.026, 0.008, 6, 3), "BH_Rope", M=T(x, y, zt - 0.04))
    if tip:
        for i in range(5):
            a = math.tau * i / 5 + r.uniform(-0.3, 0.3)
            k.put(ico(0.022, 1), tip, M=T(x + math.cos(a) * 0.045, y + math.sin(a) * 0.045, zt - L + 0.01))


def lantern_on_hook(k, x, y, z, s=0.55):
    """Iron lantern hanging from a ring at (x, y, z); returns the light point."""
    lp = hang_lantern(k, T(x, y, z), s)
    return (x + lp[0], y + lp[1], z + lp[2])


# =================================================================================================================
# 6. stand_jeweller - Elsbeth Crane, Crane's Fine Settings
def carved_post(k, x, y, H, mat="BH_WoodDark", trim="BH_Gold"):
    k.put(box(0.25, 0.25, 0.06, bev=0.012, base=True), mat, M=T(x, y, 0))
    k.put(box(0.21, 0.21, 0.28, bev=0.015, base=True), mat, M=T(x, y, 0.05))
    prof = [(0.082, 0.32), (0.094, 0.36), (0.072, 0.44), (0.06, 0.95), (0.068, 1.25), (0.06, 1.5), (0.078, 1.58),
            (0.092, 1.64), (0.078, 1.7), (0.058, 1.8), (0.055, H - 0.4), (0.07, H - 0.3), (0.088, H - 0.2),
            (0.1, H - 0.1), (0.1, H)]
    k.put(lathe(prof, 8), mat, M=T(x, y, 0), smooth=40)
    for z in (0.36, 1.64, H - 0.3):
        k.put(torus(0.09, 0.013, 8, 3), trim, M=T(x, y, z))


def crane_bird(k, M, mat="BH_Gold"):
    """Gilded crane standing on one leg, wings half raised, facing +X; feet at the origin, ~0.42 m tall."""
    b = ico(1.0, 2)
    for v in b.verts:
        v.co = Vector((v.co.x * 0.12, v.co.y * 0.055, v.co.z * 0.065))
    k.put(b, mat, M=M @ TRS(0, 0, 0.23, 0, -14, 0), smooth=50)
    k.put(tube([(0.09, 0, 0.25), (0.14, 0, 0.3), (0.12, 0, 0.36), (0.135, 0, 0.41)], [0.024, 0.018, 0.015, 0.014], 6),
          mat, M=M, smooth=50)
    k.put(ico(0.024, 1), mat, M=M @ T(0.145, 0, 0.415), smooth=50)
    k.put(cyl(0.011, 0.11, 5, r2=0.0), mat, M=M @ TRS(0.16, 0, 0.412, 0, 96, 0))
    # tail plumes
    k.put(prism([(0.0, 0.0), (-0.1, -0.05), (-0.13, -0.02), (-0.06, 0.03)], 0.05), mat, M=M @ T(-0.08, 0, 0.23))
    # wings: feathered plates lifted outward
    wing = [(0.06, 0.0), (-0.05, -0.03), (-0.17, 0.02), (-0.2, 0.09), (-0.15, 0.13), (-0.1, 0.19), (-0.03, 0.2),
            (0.02, 0.15), (0.07, 0.07)]
    for sy in (-1, 1):
        k.put(prism(wing, 0.012), mat, M=M @ T(0.0, sy * 0.045, 0.25) @ R(-sy * 38, 0, 0), smooth=None)
    # legs: one straight, one tucked
    k.put(tube([(0.0, 0.0, 0.18), (0.01, 0.0, 0.08), (0.0, 0.0, 0.0)], 0.007, 4), mat, M=M)
    k.put(tube([(0.0, 0.02, 0.18), (0.05, 0.03, 0.12), (0.0, 0.03, 0.1)], 0.007, 4), mat, M=M)
    k.put(box(0.07, 0.03, 0.01), mat, M=M @ T(0.015, 0, 0.005))


@asset("stand_jeweller", "market")
def stand_jeweller(k):
    r = k.r
    PX, PYF, PYB, PH = 1.55, -0.98, 1.08, 3.24     # carved posts (x, front y, back y, height)
    ZB = 3.22                                       # frame beam centre
    HX, HY, CY = 1.72, 1.17, 0.05                   # canopy base rectangle (eave), y from -1.12 to 1.22
    ZE = 3.33                                       # canopy eave height

    # ---- carved posts, frame, scroll brackets ---------------------------------------------------------------
    for x in (-PX, PX):
        for y in (PYF, PYB):
            carved_post(k, x, y, PH)
    for y in (PYF, PYB):
        k.put(box(2 * PX + 0.3, 0.13, 0.18, bev=0.02), "BH_WoodDark", M=T(0, y, ZB))
    for x in (-PX, PX):
        k.put(box(0.13, PYB - PYF + 0.2, 0.18, bev=0.02), "BH_WoodDark", M=T(x, (PYF + PYB) / 2, ZB))
    k.put(box(2 * PX + 0.3, 0.02, 0.035), "BH_Gold", M=T(0, PYF - 0.07, ZB - 0.03))
    k.put(box(2 * PX + 0.3, 0.02, 0.02), "BH_Gold", M=T(0, PYF - 0.07, ZB + 0.06))
    for sx in (-1, 1):
        for y in (PYF, PYB):
            pts = [(sx * (PX - 0.43 + 0.43 * math.cos(math.radians(a))), y, ZB - 0.09 - 0.43 + 0.43 * math.sin(math.radians(a)))
                   for a in range(0, 91, 15)]
            pts = [(sx * PX - sx * 0.0 + (p[0] - sx * PX), p[1], p[2]) for p in pts]
            k.put(tube(pts[::-1], 0.03, 6), "BH_WoodDark", smooth=40)
            k.put(torus(0.035, 0.01, 8, 3), "BH_Gold", M=TRS(sx * (PX - 0.43), y, ZB - 0.12, 90, 0, 0))

    # ---- teal ogee bell canopy with gilded hip ribs --------------------------------------------------------
    prof = [(1.0, 0.0), (0.9, 0.07), (0.79, 0.18), (0.67, 0.33), (0.55, 0.52), (0.43, 0.72), (0.31, 0.9),
            (0.19, 1.05), (0.08, 1.14), (0.0, 1.17)]
    prof = [(s, ZE + dz) for s, dz in prof]
    rect_roof(k, HX, HY, prof, "BH_ClothTeal", cy=CY, per=(10, 7), th=0.035, sag=0.05)
    for sx in (-1, 1):
        for sy in (-1, 1):
            pts = [(sx * HX * s * 1.01, CY + sy * HY * s * 1.01, z + 0.03) for s, z in prof[:-1]]
            k.put(tube(pts + [(0, CY, prof[-1][1] + 0.02)], 0.022, 5), "BH_Gold", smooth=40)
    # carved crane finial on a gilded orb
    zt = prof[-1][1]
    k.put(cyl(0.05, 0.12, 8, r2=0.03), "BH_Gold", M=T(0, CY, zt - 0.02), smooth=40)
    k.put(ico(0.065, 2), "BH_Gold", M=T(0, CY, zt + 0.15), smooth=50)
    crane_bird(k, T(0.0, CY, zt + 0.205) @ R(0, 0, 0))

    # ---- scalloped valance with gold hem and tassels ------------------------------------------------------
    y0, y1 = CY - HY, CY + HY
    corners = [(-HX, y0), (HX, y0), (HX, y1), (-HX, y1)]
    for i, n in enumerate((12, 8, 12, 8)):
        a, b = corners[i], corners[(i + 1) % 4]
        o = 0.015
        a2 = (a[0] + (o if a[0] > 0 else -o), a[1] + (o if a[1] > CY else -o))
        b2 = (b[0] + (o if b[0] > 0 else -o), b[1] + (o if b[1] > CY else -o))
        valance(k, a2, b2, ZE + 0.02, 0.08, 0.15, n, "BH_ClothTeal", edge="BH_Gold",
                tassel="BH_Gold" if i != 2 else None)
    k.put(tube([(c[0] * 1.012, CY + (c[1] - CY) * 1.015, ZE + 0.02) for c in corners], 0.02, 4, closed=True), "BH_Gold")

    # ---- display counter: carved dark wood, raised gilded panels ------------------------------------------
    CZ = 0.98
    k.put(box(2.46, 0.44, 0.1, bev=0.015, base=True), "BH_WoodDark", M=T(0, -1.06, 0))
    k.put(box(2.36, 0.36, CZ - 0.16, base=True), "BH_WoodDark", M=T(0, -1.04, 0.1))
    k.put(box(2.5, 0.46, 0.06, bev=0.015), "BH_WoodDark", M=T(0, -1.06, CZ - 0.03))
    k.put(box(2.52, 0.02, 0.028), "BH_Gold", M=T(0, -1.295, CZ - 0.03))
    k.put(box(2.48, 0.02, 0.022), "BH_Gold", M=T(0, -1.29, 0.1))
    for px in (-0.8, 0.0, 0.8):
        k.put(box(0.68, 0.03, 0.56, bev=0.012), "BH_WoodDark", M=T(px, -1.235, 0.54))
        for (sx_, sz_, dx, dz) in ((0.6, 0.016, 0, 0.25), (0.6, 0.016, 0, -0.25), (0.016, 0.5, 0.3, 0), (0.016, 0.5, -0.3, 0)):
            k.put(box(sx_, 0.012, sz_), "BH_Gold", M=T(px + dx, -1.255, 0.54 + dz))
        k.put(cyl(0.05, 0.02, 10), "BH_Gold", M=TRS(px, -1.25, 0.54, 90, 0, 0))
        k.put(ico(0.03, 1), "BH_GemRed" if px == 0 else "BH_Gold", M=T(px, -1.265, 0.54))

    # ---- sloped vitrine on the counter: velvet bed, gilded glazing bars, rings and amulets -----------------
    vx0, vx1, vyf, vyb = -0.72, 0.62, -1.24, -0.9
    zf, zb = CZ + 0.07, CZ + 0.27
    xc, w = (vx0 + vx1) / 2, vx1 - vx0
    k.put(hexa([(vx0, vyf, CZ), (vx1, vyf, CZ), (vx1, vyb, CZ), (vx0, vyb, CZ),
                (vx0, vyf, zf), (vx1, vyf, zf), (vx1, vyb, zb), (vx0, vyb, zb)], 0.01), "BH_WoodDark")
    ang = math.degrees(math.atan2(zb - zf, vyb - vyf))
    slen = math.hypot(zb - zf, vyb - vyf)
    a_r = math.radians(ang)
    Sd = Vector((0, math.cos(a_r), math.sin(a_r)))
    Nd = Vector((0, -math.sin(a_r), math.cos(a_r)))
    C = Vector((xc, (vyf + vyb) / 2, (zf + zb) / 2))
    k.put(box(w - 0.05, slen - 0.04, 0.02), "BH_Velvet", M=T(*(C + Nd * 0.006)) @ R(ang, 0, 0))

    def on_slope(u, v, h=0.0):
        return T(*(C + Vector((u, 0, 0)) + Sd * v + Nd * (0.016 + h))) @ R(ang, 0, 0)
    for u in (-w / 2 + 0.01, w / 2 - 0.01, -w / 6, w / 6):
        k.put(box(0.018, slen + 0.01, 0.018), "BH_Gold", M=on_slope(u, 0, 0.03))
    for v in (-slen / 2, slen / 2):
        k.put(box(w + 0.02, 0.018, 0.018), "BH_Gold", M=on_slope(0, v, 0.03))
    for sgn in (-1, 1):
        for row in (-0.075, 0.07):
            for col in (-0.13, 0.0, 0.13):
                u = sgn * w / 3 + col
                metal = "BH_Gold" if (col == 0.0) == (sgn > 0) else "BH_Silver"
                ring_jewel(k, on_slope(u, row - 0.01, 0.0), metal, r.choice(GEMS))
    for col in (-0.14, 0.0, 0.14):
        amulet(k, on_slope(col, -0.1, 0.0), "BH_Gold" if col else "BH_Silver", r.choice(("BH_GemRed", "BH_GemAqua",
                                                                                           "BH_GemViolet")))

    # ---- jewellery tree (left of the case) --------------------------------------------------------------------
    tx, ty = -0.96, -1.07
    k.put(cyl(0.1, 0.03, 12), "BH_WoodDark", M=T(tx, ty, CZ))
    k.put(cyl(0.085, 0.02, 12), "BH_Gold", M=T(tx, ty, CZ + 0.03))
    k.put(tube([(tx, ty, CZ + 0.04), (tx + 0.01, ty, CZ + 0.25), (tx - 0.01, ty, CZ + 0.45), (tx, ty, CZ + 0.62)],
               [0.016, 0.013, 0.01, 0.007], 6), "BH_Gold", smooth=40)
    branches = [(0.3, 0.0, 0.15), (0.36, 180, 0.14), (0.44, 20, 0.12), (0.49, 200, 0.11), (0.55, 0, 0.08),
                (0.58, 180, 0.07)]
    for (bz, a, L) in branches:
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        p0 = Vector((tx, ty, CZ + bz))
        p1 = p0 + Vector((c * L * 0.6, s_ * L * 0.3, 0.03))
        p2 = p0 + Vector((c * L, s_ * L * 0.4, 0.07))
        k.put(tube([p0, p1, p2], [0.007, 0.005, 0.004], 4), "BH_Gold", smooth=40)
        k.put(ico(0.009, 1), "BH_Gold", M=T(*p2))
    for (bz, a, L), stone, metal in zip(branches[:4], ("BH_GemRed", "BH_GemAqua", "BH_GemGreen", "BH_GemViolet"),
                                        ("BH_Gold", "BH_Silver", "BH_Gold", "BH_Gold")):
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        hook = Vector((tx + c * L * 0.8, ty + s_ * L * 0.35 - 0.012, CZ + bz + 0.05))
        necklace(k, hook, 0.05, 0.13 + 0.02 * (bz < 0.4), metal, stone)

    # ---- brass balance scale, coins, loupe (right of the case) --------------------------------------------
    bx, by = 0.93, -1.07
    k.put(cyl(0.075, 0.03, 12), "BH_Brass", M=T(bx, by, CZ))
    k.put(cyl(0.012, 0.36, 6), "BH_Brass", M=T(bx, by, CZ + 0.03))
    k.put(ico(0.02, 1), "BH_Brass", M=T(bx, by, CZ + 0.41))
    k.put(box(0.36, 0.014, 0.014), "BH_Brass", M=TRS(bx, by, CZ + 0.38, 0, 5, 0))
    for sx, zp in ((-1, 0.17), (1, 0.14)):
        ex = bx + sx * 0.17
        ez = CZ + 0.38 - sx * 0.015
        for a in (0, 120, 240):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            rod(k, (ex, by, ez), (ex + ca * 0.05, by + sa * 0.05, CZ + zp), 0.0025, "BH_Brass", 3)
        k.put(lathe([(0.0, 0.0), (0.035, 0.004), (0.06, 0.02), (0.056, 0.022), (0.0, 0.008)], 10), "BH_Brass",
              M=T(ex, by, CZ + zp - 0.005))
    gem(k, T(bx - 0.17, by, CZ + 0.18), 0.022, "BH_GemAmber")
    k.put(cyl(0.02, 0.03, 8), "BH_Brass", M=T(bx + 0.17, by, CZ + 0.14))
    for i, (dx, dy, n) in enumerate(((0.12, -0.14, 5), (0.17, -0.1, 3), (-0.16, -0.14, 4))):
        for j in range(n):
            k.put(cyl(0.02, 0.006, 10), "BH_Gold", M=TRS(bx + dx + r.uniform(-0.003, 0.003), by + dy, CZ + j * 0.0065))
    k.put(torus(0.028, 0.006, 10, 4), "BH_Brass", M=TRS(bx - 0.12, by + 0.12, CZ + 0.008))
    k.put(cyl(0.006, 0.07, 5), "BH_WoodDark", M=TRS(bx - 0.12 + 0.028, by + 0.12, CZ + 0.008, 0, 90, 20))

    # ---- back cabinet: three arched velvet niches with a goblet, a tiara on a bust and a salver ------------
    cy0 = 1.12
    k.put(box(2.7, 0.28, 2.1, bev=0.02, base=True), "BH_WoodDark", M=T(0, cy0, 0))
    k.put(box(2.8, 0.34, 0.1, bev=0.02), "BH_WoodDark", M=T(0, cy0 - 0.02, 2.13))
    k.put(box(2.82, 0.02, 0.03), "BH_Gold", M=T(0, cy0 - 0.195, 2.1))
    k.put(box(2.76, 0.32, 0.12, bev=0.02, base=True), "BH_WoodDark", M=T(0, cy0 - 0.01, 0))
    for i, nx in enumerate((-0.85, 0.0, 0.85)):
        arch = [(-0.32, 0.0), (0.32, 0.0), (0.32, 0.72)] + [(math.cos(math.radians(a)) * 0.32, 0.72 + math.sin(math.radians(a)) * 0.32)
                                                            for a in range(15, 180, 15)] + [(-0.32, 0.72)]
        k.put(prism(arch, 0.03), "BH_Velvet", M=T(nx, cy0 - 0.14, 0.95))
        edge = [(math.cos(math.radians(a)) * 0.34, 0.72 + math.sin(math.radians(a)) * 0.34) for a in range(0, 181, 15)]
        k.put(tube([(nx + e[0], cy0 - 0.16, 0.95 + e[1]) for e in edge], 0.012, 4), "BH_Gold")
        for sx in (-1, 1):
            rod(k, (nx + sx * 0.34, cy0 - 0.16, 0.95), (nx + sx * 0.34, cy0 - 0.16, 1.67), 0.012, "BH_Gold", 4)
        k.put(box(0.72, 0.2, 0.04), "BH_WoodDark", M=T(nx, cy0 - 0.2, 0.95))
        k.put(box(0.74, 0.02, 0.02), "BH_Gold", M=T(nx, cy0 - 0.3, 0.95))
        zb2 = 0.97
        if i == 0:   # gold goblet
            k.put(lathe([(0.06, 0.0), (0.05, 0.01), (0.015, 0.03), (0.012, 0.12), (0.03, 0.14), (0.065, 0.2),
                         (0.07, 0.28), (0.064, 0.28), (0.0, 0.16)], 12), "BH_Gold", M=T(nx, cy0 - 0.2, zb2), smooth=40)
            for a in range(0, 360, 90):
                gem(k, T(nx + math.cos(math.radians(a)) * 0.066, cy0 - 0.2 + math.sin(math.radians(a)) * 0.066, zb2 + 0.23)
                    @ R(0, 90, a), 0.012, "BH_GemRed")
        elif i == 1:  # velvet bust wearing a tiara and a collar
            k.put(lathe([(0.12, 0.0), (0.13, 0.05), (0.08, 0.12), (0.05, 0.3), (0.06, 0.38), (0.075, 0.46),
                         (0.04, 0.52), (0.0, 0.53)], 10), "BH_Velvet", M=T(nx, cy0 - 0.2, zb2), smooth=40)
            k.put(torus(0.065, 0.008, 12, 4), "BH_Gold", M=T(nx, cy0 - 0.2, zb2 + 0.47))
            for a in range(-90, 91, 30):
                ca, sa = math.cos(math.radians(a - 90)), math.sin(math.radians(a - 90))
                k.put(cyl(0.012, 0.05 if a else 0.08, 4, r2=0.0), "BH_Gold", M=T(nx + ca * 0.066, cy0 - 0.2 + sa * 0.066, zb2 + 0.47))
            gem(k, T(nx, cy0 - 0.27, zb2 + 0.52) @ R(90, 0, 0), 0.016, "BH_GemAqua")
            k.put(torus(0.07, 0.01, 12, 4), "BH_Gold", M=TRS(nx, cy0 - 0.21, zb2 + 0.28, 10, 0, 0))
            gem(k, T(nx, cy0 - 0.29, zb2 + 0.24) @ R(90, 0, 0), 0.02, "BH_GemRed")
        else:        # silver salver stood upright with a stand
            k.put(cyl(0.2, 0.015, 16), "BH_Silver", M=TRS(nx, cy0 - 0.15, zb2 + 0.22, 75, 0, 0))
            k.put(torus(0.2, 0.01, 16, 4), "BH_Silver", M=TRS(nx, cy0 - 0.16, zb2 + 0.22, 75, 0, 0))
            k.put(lathe([(0.04, 0.0), (0.03, 0.02), (0.012, 0.03), (0.012, 0.13), (0.035, 0.18), (0.0, 0.12)], 8),
                  "BH_Silver", M=T(nx + 0.2, cy0 - 0.24, zb2), smooth=40)
    for sx in (-1, 1):  # candlesticks on the cabinet
        k.put(lathe([(0.06, 0.0), (0.02, 0.03), (0.015, 0.2), (0.04, 0.22), (0.0, 0.23)], 8), "BH_Gold",
              M=T(sx * 1.12, cy0 - 0.02, 2.18), smooth=40)
        k.put(cyl(0.018, 0.14, 8), "BH_Candle", M=T(sx * 1.12, cy0 - 0.02, 2.41))
        flame_tip(k, T(sx * 1.12, cy0 - 0.02, 2.56), 0.045)

    # ---- side screens: carved lattice between the posts --------------------------------------------------
    for sx in (-1, 1):
        x = sx * PX
        y0s, y1s = PYF + 0.14, PYB - 0.14
        yc_, L = (y0s + y1s) / 2, y1s - y0s
        k.put(box(0.07, L, 0.1, bev=0.01), "BH_WoodDark", M=T(x, yc_, 0.05))
        k.put(box(0.05, L, 0.42), "BH_WoodDark", M=T(x, yc_, 0.31))
        k.put(box(0.09, L + 0.04, 0.07, bev=0.01), "BH_WoodDark", M=T(x, yc_, 1.05))
        k.put(box(0.1, L + 0.04, 0.015), "BH_Gold", M=T(x, yc_, 1.09))
        k.put(box(0.08, L, 0.05), "BH_WoodDark", M=T(x, yc_, 0.54))
        n = 5
        for i in range(n):
            yy = y0s + L * (i + 0.5) / n
            for s_ in (-1, 1):
                k.put(box(0.03, 0.03, 0.62), "BH_WoodDark", M=TRS(x, yy, 0.79, s_ * 34, 0, 0))
        for i in range(n + 1):
            k.put(ico(0.018, 1), "BH_Gold", M=T(x - sx * 0.03, y0s + L * i / n, 0.79))

    # ---- velvet rug, stool, strongbox of settings ---------------------------------------------------------
    k.put(box(2.3, 1.72, 0.012), "BH_Velvet", M=T(0, 0.05, 0.006))
    for (sx_, sy_, dx, dy) in ((2.3, 0.07, 0, -0.8), (2.3, 0.07, 0, 0.9), (0.07, 1.72, -1.12, 0.05), (0.07, 1.72, 1.12, 0.05)):
        k.put(box(sx_, sy_, 0.014), "BH_ClothTeal", M=T(dx, dy, 0.007))
    k.put(lathe([(0.17, 0.44), (0.18, 0.48), (0.15, 0.53), (0.0, 0.54)], 10), "BH_Velvet", M=T(1.05, 0.5, 0), smooth=40)
    k.put(cyl(0.17, 0.05, 10), "BH_WoodDark", M=T(1.05, 0.5, 0.4))
    for a in (0, 120, 240):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        rod(k, (1.05 + ca * 0.11, 0.5 + sa * 0.11, 0.41), (1.05 + ca * 0.17, 0.5 + sa * 0.17, 0.0), 0.022, "BH_WoodDark")
    # small open casket on the stool... rather on the counter end behind the scale
    k.put(box(0.2, 0.13, 0.07, bev=0.008, base=True), "BH_WoodDark", M=T(0.55, -0.95, CZ))
    k.put(box(0.18, 0.11, 0.01), "BH_Velvet", M=T(0.55, -0.95, CZ + 0.065))
    k.put(box(0.2, 0.02, 0.12, bev=0.006), "BH_WoodDark", M=TRS(0.55, -0.885, CZ + 0.13, -12, 0, 0))
    for j in range(5):
        k.put(ico(0.012, 1), "BH_Bone" if j % 2 else "BH_Silver", M=T(0.49 + j * 0.03, -0.96 + (j % 2) * 0.02, CZ + 0.075))

    # ---- lanterns hanging from the front beam -----------------------------------------------------------
    la = lantern_on_hook(k, -1.2, PYF, ZB - 0.09, 0.5)
    lb = lantern_on_hook(k, 1.2, PYF, ZB - 0.09, 0.5)

    k.sockets.append(("npc", (0.0, -0.38, 0.0)))
    k.sockets.append(("customer", (0.0, -1.95, 0.0)))
    k.sockets.append(("light_a", la))
    k.sockets.append(("light_b", lb))

    k.col_box(2.5, 0.46, 1.0, T(0, -1.06, 0.5))
    for x in (-PX, PX):
        for y in (PYF, PYB):
            k.col_box(0.26, 0.26, 2.2, T(x, y, 1.1))
        k.col_box(0.12, PYB - PYF, 1.1, T(x, (PYF + PYB) / 2, 0.55))
    k.col_box(2.8, 0.34, 2.2, T(0, cy0, 1.1))
    k.col_box(0.36, 0.36, 0.55, T(1.05, 0.5, 0.27))
    return dict(recenter=False)


# =================================================================================================================
# 7. stand_apothecary - Master Aldous Pell, Alchemist of Olivar
EV, AHX, ASL, ATH = 1.97, 2.28, 0.98, 0.3     # eave (underside at |x| = AHX), slope, thatch thickness


def _zu(x):
    """Underside of the apothecary's thatch at |x|."""
    return EV + (AHX - abs(x)) * ASL


def jar(k, M, kind, mat=None):
    """Apothecary vessels: crock, bottle, potion flask, paper-capped jar."""
    r = k.r
    if kind == "crock":
        h = r.uniform(0.16, 0.26)
        rr = h * r.uniform(0.38, 0.5)
        k.put(lathe([(rr * 0.8, 0.0), (rr, h * 0.25), (rr * 0.95, h * 0.8), (rr * 0.6, h * 0.92), (rr * 0.62, h),
                     (0.0, h)], 8), mat or r.choice(("BH_Bone", "BH_Stone", "BH_Brick")), M=M, smooth=40)
        k.put(cyl(rr * 0.66, 0.025, 8), "BH_Wood", M=M @ T(0, 0, h))
        k.put(ico(0.018, 1), "BH_Wood", M=M @ T(0, 0, h + 0.03))
    elif kind == "bottle":
        h = r.uniform(0.2, 0.3)
        rr = r.uniform(0.035, 0.05)
        k.put(lathe([(rr, 0.0), (rr, h * 0.58), (rr * 0.35, h * 0.76), (rr * 0.3, h), (0.0, h)], 6), mat or "BH_Bottle",
              M=M, smooth=40)
        k.put(cyl(rr * 0.34, 0.03, 5), "BH_Wood", M=M @ T(0, 0, h))
    elif kind == "potion":
        rr = r.uniform(0.045, 0.06)
        k.put(lathe([(0.0, 0.0), (rr * 0.7, 0.005), (rr, rr * 0.9), (rr * 0.7, rr * 1.7), (rr * 0.3, rr * 1.95),
                     (rr * 0.28, rr * 2.6), (0.0, rr * 2.6)], 7), mat or r.choice(GEMS[:5]), M=M, smooth=40)
        k.put(cyl(rr * 0.32, 0.03, 5), "BH_Wood", M=M @ T(0, 0, rr * 2.6))
    else:  # paper-capped jar
        h = r.uniform(0.14, 0.2)
        rr = r.uniform(0.05, 0.07)
        k.put(lathe([(rr, 0.0), (rr, h), (0.0, h)], 8), mat or r.choice(("BH_Bottle", "BH_Bone")), M=M, smooth=40)
        k.put(cyl(rr * 1.12, 0.03, 8, r2=rr * 1.04), "BH_Paper", M=M @ T(0, 0, h - 0.005))
        k.put(torus(rr * 1.02, 0.006, 8, 3), "BH_Rope", M=M @ T(0, 0, h - 0.01))


def jar_row(k, x0, x1, y, z, kinds, depth=0.0):
    r = k.r
    x = x0
    while x < x1:
        kind = r.choice(kinds)
        jar(k, T(x, y + r.uniform(-depth, depth), z) @ R(0, 0, r.uniform(0, 360)), kind)
        x += r.uniform(0.1, 0.16)


def basket(k, M, R_=0.2, H=0.16, fill="BH_Moss", tip=None):
    r = k.r
    k.put(lathe([(R_ * 0.72, 0.0), (R_, H * 0.9), (R_ * 1.04, H), (R_ * 0.96, H), (R_ * 0.68, 0.03), (0.0, 0.03)], 10),
          "BH_Thatch", M=M, smooth=40)
    k.put(torus(R_ * 1.0, 0.014, 10, 3), "BH_Wood", M=M @ T(0, 0, H))
    t = ico(1.0, 2)
    for v in t.verts:
        v.co = Vector((v.co.x * R_ * 0.92, v.co.y * R_ * 0.92, max(v.co.z, -0.1) * 0.07))
    ndisp(t, 12.0, 0.02, k.noff + Vector(M.translation))
    k.put(t, fill, M=M @ T(0, 0, H - 0.02), smooth=35)
    if tip:
        for i in range(7):
            a = r.uniform(0, 6.28)
            d = r.uniform(0, R_ * 0.7)
            k.put(ico(0.02, 1), tip, M=M @ T(math.cos(a) * d, math.sin(a) * d, H + 0.04))


@asset("stand_apothecary", "market")
def stand_apothecary(k):
    r = k.r
    YF, YB = -1.6, 1.6
    PXa = 2.02
    ang = math.degrees(math.atan(ASL))
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    # ---- thatch: two thick slabs cut vertical at the eaves, rolled verges, ridge block with hazel liggers -----
    Ls = (AHX + 0.35) / ca
    for sx in (-1, 1):
        t = box(Ls, YB - YF, ATH)
        bmesh.ops.subdivide_edges(t, edges=[e for e in t.edges if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-4],
                                  cuts=5, use_grid_fill=True)
        mid = Vector((sx * (AHX - 0.35) / 2, 0.0, (_zu(AHX) + _zu(-0.35 if sx > 0 else 0.35)) / 2))
        M = T(mid.x + sx * sa * ATH / 2, 0, mid.z + ca * ATH / 2) @ R(0, sx * ang, 0)
        bmesh.ops.transform(t, matrix=M, verts=t.verts)
        slice_plane(t, (sx * AHX, 0, 0), (sx, 0, 0))
        slice_plane(t, (0, 0, 0), (-sx, 0, 0))
        ndisp(t, 2.2, 0.035, k.noff + Vector((sx, 0, 0)))
        k.put(t, "BH_Thatch", smooth=45)
    ztop = lambda x: _zu(x) + ATH / ca
    for y in (YF + 0.1, YB - 0.1):
        for sx in (-1, 1):
            pts = [(sx * AHX * f, y, ztop(AHX * f) - 0.09) for f in (1.0, 0.75, 0.5, 0.25, 0.0)]
            k.put(tube(pts, [0.16, 0.16, 0.15, 0.15, 0.15], 7), "BH_Thatch", smooth=45)
    for sx in (-1, 1):
        k.put(tube([(sx * (AHX - 0.08), YF + 0.08, _zu(AHX) + 0.14), (sx * (AHX - 0.08), YB - 0.08, _zu(AHX) + 0.14)],
                   0.15, 7), "BH_Thatch", smooth=45)
    zr = ztop(0)
    k.put(prism([(-0.62, zr - 0.62), (0.62, zr - 0.62), (0.62, zr - 0.5), (0.2, zr + 0.1), (-0.2, zr + 0.1),
                 (-0.62, zr - 0.5)], YB - YF + 0.08, bev=0.03), "BH_Thatch", M=R(0, 0, 90) @ R(0, 0, -90), smooth=45)
    for sx in (-1, 1):
        for dx, dz in ((0.47, -0.42), (0.14, 0.02)):
            rod(k, (sx * dx, YF + 0.02, zr + dz + 0.04), (sx * dx, YB - 0.02, zr + dz + 0.04), 0.014, "BH_Wood", 4)
    n = 14
    for i in range(n):
        y = YF + 0.1 + (YB - YF - 0.2) * (i + 0.5) / n
        for sx in (-1, 1):
            rod(k, (sx * 0.47, y - 0.1, zr - 0.36), (sx * 0.14, y + 0.1, zr + 0.07), 0.01, "BH_Wood", 3)

    # ---- timber frame: posts, wall plates, rafters, collar, king post, gable boards --------------------------
    wood = "BH_WoodDark"
    for sx in (-1, 1):
        for y in (-1.5, 0.0, 1.45):
            k.put(box(0.15, 0.15, _zu(PXa) - 0.1, bev=0.02, base=True), wood, M=T(sx * PXa, y, 0))
            k.put(box(0.24, 0.24, 0.08, bev=0.02, base=True), "BH_Stone", M=T(sx * PXa, y, 0))
        k.put(box(0.16, YB - YF, 0.14, bev=0.015), wood, M=T(sx * PXa, 0, _zu(PXa) - 0.1))
    for y in (-1.5, 0.0, 1.45):
        for sx in (-1, 1):
            p0 = Vector((sx * (AHX - 0.02), y, _zu(AHX) - 0.09))
            p1 = Vector((0.0, y, _zu(0) - 0.09))
            k.put(tube([p0, p1], 0.07, 6), wood, smooth=40)
    ZC = 3.32
    xc_ = AHX - (ZC + 0.08 - EV) / ASL
    k.put(box(2 * xc_ + 0.1, 0.14, 0.15, bev=0.02), wood, M=T(0, -1.5, ZC))
    k.put(box(2 * xc_ + 0.1, 0.14, 0.15, bev=0.02), wood, M=T(0, 1.45, ZC))
    for y in (-1.5, 1.45):
        k.put(box(0.13, 0.13, _zu(0) - ZC - 0.1, base=True), wood, M=T(0, y, ZC + 0.07))
    x = -xc_ + 0.1
    while x < xc_ - 0.05:     # front gable boarding above the collar
        top = _zu(x) - 0.1
        if top > ZC + 0.15:
            plank(k, 0.17, 0.04, top - ZC - 0.07, T(x, -1.53, (top + ZC + 0.07) / 2) @ R(0, 90, 0), mat="BH_Wood",
                  tint=1.0, chips=1)
        x += 0.18
    # back wall: full gable of vertical boards
    x = -PXa + 0.09
    while x < PXa - 0.05:
        top = _zu(x) - 0.08
        plank(k, top - 0.02, 0.19, 0.045, T(x, 1.52, top / 2 + 0.01) @ R(0, 90, 0), mat="BH_Wood", tint=1.0, chips=1)
        x += 0.2
    # low plank side walls between the posts
    for sx in (-1, 1):
        for z in (0.2, 0.45, 0.7, 0.95):
            plank(k, YB - YF - 0.2, 0.25, 0.04, T(sx * (PXa + 0.02), 0.0, z) @ R(90, 0, 90), mat="BH_Wood", tint=1.0)

    # ---- counter with a basket ledge ---------------------------------------------------------------------
    CZ = 0.95
    cy_ = -1.19
    for i in range(12):
        xx = -1.24 + 2.48 * (i + 0.5) / 12
        plank(k, CZ - 0.08, 0.2, 0.04, T(xx, cy_ - 0.19, (CZ - 0.08) / 2) @ R(0, 90, 0), mat="BH_Wood", tint=1.0)
    for sx in (-1, 1):
        k.put(box(0.1, 0.4, CZ - 0.06, base=True), wood, M=T(sx * 1.2, cy_, 0))
    k.put(box(2.62, 0.5, 0.07, bev=0.02), wood, M=T(0, cy_ - 0.01, CZ - 0.035))
    k.put(box(2.5, 0.22, 0.05, bev=0.015), "BH_Wood", M=T(0, -1.49, 0.42))
    for xx in (-1.0, 0.0, 1.0):
        k.put(prism([(0.0, 0.0), (0.18, 0.0), (0.0, 0.2)], 0.05), wood, M=T(xx, -1.38, 0.2) @ R(0, 0, 90) @ R(0, 0, 0))
    for (bx_, fill, tip) in ((-0.95, "BH_Moss", None), (-0.5, "BH_Thatch", "BH_ClothViolet"), (0.45, "BH_Moss", "BH_ClothGreen"),
                             (0.95, "BH_ClothGreen", "BH_GemGold")):
        basket(k, T(bx_, -1.49, 0.445) @ R(0, 0, r.uniform(0, 90)), 0.17, 0.13, fill, tip)
    # counter top: mortar and pestle, open recipe book, rack of draughts, fresh herbs, candle
    k.put(lathe([(0.1, 0.0), (0.12, 0.08), (0.11, 0.12), (0.09, 0.12), (0.06, 0.05), (0.0, 0.05)], 10), "BH_Stone",
          M=T(-0.78, -1.2, CZ), smooth=40)
    k.put(cyl(0.025, 0.24, 6, r2=0.018), "BH_Bone", M=TRS(-0.78, -1.2, CZ + 0.06, 25, 0, 30))
    k.put(cyl(0.07, 0.02, 8), "BH_Moss", M=T(-0.78, -1.2, CZ + 0.07))
    k.put(box(0.44, 0.3, 0.03, bev=0.005), "BH_Leather", M=TRS(0.32, -1.16, CZ + 0.015, 0, 0, -8))
    for sx in (-1, 1):
        k.put(box(0.2, 0.27, 0.02), "BH_Paper", M=TRS(0.32 + sx * 0.105, -1.16 - sx * 0.015, CZ + 0.04, 0, -sx * 7, -8))
    k.put(cyl(0.02, 0.05, 6), "BH_StoneDark", M=T(0.6, -1.02, CZ))
    k.put(cyl(0.004, 0.2, 3), "BH_Bone", M=TRS(0.6, -1.02, CZ + 0.04, 20, 0, 0))
    k.put(box(0.5, 0.14, 0.08, bev=0.01, base=True), "BH_Wood", M=T(0.95, -1.28, CZ))
    for i, m in enumerate(("BH_GemRed", "BH_GemAqua", "BH_GemGreen", "BH_GemAmber", "BH_GemViolet")):
        jar(k, T(0.77 + i * 0.09, -1.28, CZ + 0.05), "potion", m)
    for i in range(6):
        k.put(cyl(0.006, 0.34, 3), "BH_Moss", M=TRS(-0.3 + i * 0.012, -1.22, CZ + 0.01, 0, 90, 10 + i * 4))
    k.put(ico(0.05, 1), "BH_Moss", M=TRS(-0.12, -1.19, CZ + 0.03, s=(1.6, 1, 0.6)))
    k.put(cyl(0.035, 0.03, 8), "BH_Brass", M=T(-0.45, -1.02, CZ))
    k.put(cyl(0.02, 0.1, 8), "BH_Candle", M=T(-0.45, -1.02, CZ + 0.03))
    flame_tip(k, T(-0.45, -1.02, CZ + 0.145), 0.04)

    # ---- tiered shelves of jars (front left) ----------------------------------------------------------------
    ex0, ex1 = -1.94, -1.34
    steps = ((0.42, -1.52, -1.33), (0.77, -1.33, -1.15), (1.12, -1.15, -0.97))
    for (z, y0, y1) in steps:
        k.put(box(ex1 - ex0, y1 - y0 + 0.02, 0.04, bev=0.01), "BH_Wood", M=T((ex0 + ex1) / 2, (y0 + y1) / 2, z))
        k.put(box(ex1 - ex0, 0.03, z - 0.02, base=True), wood, M=T((ex0 + ex1) / 2, y0 + 0.02, 0))
    for xx in (ex0 + 0.03, ex1 - 0.03):
        k.put(prism([(-1.52, 0.0), (-0.97, 0.0), (-0.97, 1.14), (-1.15, 1.14), (-1.15, 0.79), (-1.33, 0.79), (-1.33, 0.44),
                     (-1.52, 0.44)], 0.04), wood, M=T(xx, 0, 0) @ R(0, 0, 90) @ R(0, 0, 0) @ Matrix(((0, 1, 0, 0), (1, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))))
    for i, (z, y0, y1) in enumerate(steps):
        jar_row(k, ex0 + 0.08, ex1 - 0.04, (y0 + y1) / 2, z + 0.02,
                (("crock", "paper"), ("bottle", "potion", "paper"), ("potion", "bottle", "crock"))[i], 0.02)

    # ---- the still: copper alembic over a tiny brazier on a brick stand (front right) ----------------------
    sx0 = 1.66
    k.put(box(0.56, 0.46, 0.66, bev=0.02, base=True), "BH_Brick", M=T(sx0, -1.22, 0))
    k.put(box(0.62, 0.52, 0.06, bev=0.015), "BH_Stone", M=T(sx0, -1.22, 0.69))
    bz = 0.72
    k.put(lathe([(0.05, 0.0), (0.13, 0.05), (0.15, 0.1), (0.13, 0.1), (0.0, 0.06)], 10), "BH_Iron",
          M=T(sx0, -1.22, bz + 0.07), smooth=40)
    for a in (30, 150, 270):
        c_, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        rod(k, (sx0 + c_ * 0.07, -1.22 + s_ * 0.07, bz + 0.1), (sx0 + c_ * 0.15, -1.22 + s_ * 0.15, bz), 0.012, "BH_Iron", 4)
    for i in range(7):
        a = r.uniform(0, 6.28)
        d = r.uniform(0, 0.08)
        k.put(rock(r, (0.04, 0.035, 0.03), cuts=3, subd=1, seed_off=i), "BH_Coals",
              M=T(sx0 + math.cos(a) * d, -1.22 + math.sin(a) * d, bz + 0.14))
    k.put(torus(0.12, 0.012, 10, 3), "BH_Iron", M=T(sx0, -1.22, bz + 0.2))
    pz = bz + 0.19
    k.put(lathe([(0.0, 0.0), (0.09, 0.02), (0.13, 0.09), (0.12, 0.17), (0.07, 0.22), (0.06, 0.25), (0.0, 0.25)], 10),
          "BH_Copper", M=T(sx0, -1.22, pz), smooth=40)
    k.put(lathe([(0.065, 0.0), (0.1, 0.06), (0.09, 0.14), (0.04, 0.2), (0.02, 0.24), (0.0, 0.25)], 10), "BH_Copper",
          M=T(sx0, -1.22, pz + 0.24), smooth=40)
    k.put(tube([(sx0 - 0.03, -1.22, pz + 0.42), (sx0 - 0.2, -1.2, pz + 0.38), (sx0 - 0.42, -1.18, pz + 0.18),
                (1.1, -1.16, CZ + 0.24)], [0.02, 0.016, 0.012, 0.01], 6), "BH_Copper", smooth=40)
    k.put(lathe([(0.0, 0.0), (0.06, 0.01), (0.08, 0.07), (0.06, 0.13), (0.025, 0.16), (0.022, 0.22), (0.0, 0.22)], 8),
          "BH_GemGreen", M=T(1.1, -1.16, CZ), smooth=40)
    for i in range(3):
        jar(k, T(sx0 + 0.18, -1.08 - i * 0.02, 0.72), "potion" if i else "crock", "BH_GemAmber" if i == 1 else None)
    k.put(box(0.3, 0.2, 0.18, bev=0.01, base=True), "BH_Wood", M=TRS(sx0 + 0.02, -0.72, 0, 0, 0, 8))
    for i in range(5):
        k.put(rock(r, (0.06, 0.05, 0.04), cuts=3, subd=1, seed_off=10 + i), "BH_StoneDark",
              M=T(sx0 + r.uniform(-0.08, 0.1), -0.72 + r.uniform(-0.05, 0.05), 0.18))

    # ---- herbs: bundles along the front rafters and the collar, two drying poles inside -------------------
    mats = (("BH_Moss", None), ("BH_Thatch", "BH_ClothViolet"), ("BH_Moss", "BH_ClothCream"), ("BH_Thatch", None),
            ("BH_ClothGreen", None))
    i = 0
    for sx in (-1, 1):
        for xx in (1.02, 1.3, 1.58, 1.86):
            m, tip = mats[i % len(mats)]
            i += 1
            herb_bundle(k, (sx * xx, -1.5, _zu(xx) - 0.16), r.uniform(0.26, 0.34), m, tip, 0.08 + 0.04 * (i % 2))
        for xx in (0.5, 0.78):
            m, tip = mats[i % len(mats)]
            i += 1
            herb_bundle(k, (sx * xx, -1.5, ZC - 0.075), r.uniform(0.26, 0.32), m, tip, 0.06 + 0.05 * (i % 2))
    for sx in (-1, 1):
        px_, pz_ = sx * 1.42, 2.58
        rod(k, (px_, -1.35, pz_), (px_, 1.3, pz_), 0.022, "BH_Wood", 5)
        for y in (-1.2, 0.0, 1.2):
            rope_line(k, [(px_, y, pz_), (px_, y, _zu(1.42) - 0.12)], 0.008)
        for y in (-1.05, -0.65, -0.25, 0.15, 0.55, 0.95):
            m, tip = mats[i % len(mats)]
            i += 1
            herb_bundle(k, (px_, y, pz_ - 0.02), r.uniform(0.24, 0.32), m, tip, 0.05)

    # ---- shelves of jars: back wall and inside the side walls ------------------------------------------------
    for z in (0.95, 1.4, 1.85):
        k.put(box(3.3, 0.24, 0.04, bev=0.01), "BH_Wood", M=T(0, 1.36, z))
        jar_row(k, -1.55, 1.55, 1.36, z + 0.02, ("crock", "bottle", "paper", "potion", "crock"), 0.02)
    for sx in (-1, 1):
        for z in (1.15, 1.6):
            k.put(box(0.22, 1.9, 0.04, bev=0.01), "BH_Wood", M=T(sx * 1.84, 0.25, z))
            y = -0.62
            while y < 1.15:
                jar(k, T(sx * 1.84, y, z + 0.02) @ R(0, 0, r.uniform(0, 360)), r.choice(("crock", "bottle", "paper",
                                                                                          "potion")))
                y += r.uniform(0.12, 0.18)
    keg(k, T(-1.55, 0.95, 0), 0.6, 0.22)
    for (sx_, sy_) in ((1.55, 0.9), (1.35, 1.1)):
        t = lathe([(0.16, 0.0), (0.22, 0.12), (0.2, 0.36), (0.1, 0.46), (0.05, 0.5), (0.0, 0.5)], 8)
        ndisp(t, 5.0, 0.02, k.noff + Vector((sx_, sy_, 0)))
        k.put(t, "BH_Cloth", M=T(sx_, sy_, 0) @ R(0, 0, r.uniform(0, 90)), smooth=40)

    la = lantern_on_hook(k, -0.42, -1.5, ZC - 0.075, 0.55)
    k.put(tube([(-0.42, -1.5, ZC - 0.075), (-0.42, -1.5, ZC - 0.02)], 0.01, 4), "BH_Iron")

    k.sockets.append(("npc", (0.0, -0.52, 0.0)))
    k.sockets.append(("customer", (0.0, -2.15, 0.0)))
    k.sockets.append(("light_a", la))
    k.sockets.append(("light_b", (sx0, -1.22, bz + 0.35)))
    k.sockets.append(("flame", (sx0, -1.22, bz + 0.16)))

    k.col_box(2.62, 0.62, 1.0, T(0, -1.28, 0.5))
    k.col_box(ex1 - ex0 + 0.05, 0.56, 1.2, T((ex0 + ex1) / 2, -1.25, 0.6))
    k.col_box(0.62, 0.52, 1.2, T(sx0, -1.22, 0.6))
    for sx in (-1, 1):
        k.col_box(0.2, YB - YF, 1.1, T(sx * PXa, 0, 0.55))
        for y in (-1.5, 0.0, 1.45):
            k.col_box(0.24, 0.24, 2.1, T(sx * PXa, y, 1.05))
    k.col_box(2 * PXa, 0.3, 2.1, T(0, 1.42, 1.05))
    return dict(recenter=False)


# =================================================================================================================
# 8. stand_armsbroker - Corvin Ashby, Arms Broker of Olivar
def heater_shield(k, M, field, device, dmat, rim="BH_Iron", w=0.5, h=0.64):
    """Heater shield in the XZ plane facing -Y, top edge centred on the origin."""
    pts = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, -h * 0.3)]
    for i in range(1, 8):
        a = math.radians(90 * i / 8)
        pts.append((w / 2 * math.cos(a), -h * 0.3 - (h * 0.7) * math.sin(a)))
    pts += [(-x, z) for (x, z) in reversed(pts[3:-1])] + [(-w / 2, -h * 0.3)]
    k.put(prism([(x * 1.07, z * 1.05 + 0.012) for x, z in pts], 0.03), rim, M=M @ T(0, 0.012, 0))
    k.put(prism(pts, 0.035), field, M=M @ T(0, -0.008, 0))
    D = M @ T(0, -0.03, 0)
    if device == "chevron":
        k.put(prism([(-w / 2 + 0.02, -h * 0.62), (0.0, -h * 0.2), (w / 2 - 0.02, -h * 0.62), (w / 2 - 0.02, -h * 0.47),
                     (0.0, -h * 0.05), (-w / 2 + 0.02, -h * 0.47)], 0.02), dmat, M=D)
    elif device == "cross":
        k.put(box(0.08, 0.02, h * 0.9), dmat, M=D @ T(0, 0, -h * 0.47))
        k.put(box(w - 0.04, 0.02, 0.08), dmat, M=D @ T(0, 0, -h * 0.33))
    elif device == "pale":
        k.put(prism([(0.0, -0.01)] + [(x, z) for (x, z) in pts if x > 0.001] + [(0.0, -h + 0.01)], 0.02), dmat, M=D)
        k.put(cyl(0.07, 0.02, 12), field if dmat != field else "BH_Gold", M=D @ TRS(0.0, -0.004, -h * 0.35, 90, 0, 0))
    elif device == "roundels":
        for (dx, dz) in ((-0.11, -0.14), (0.11, -0.14), (0.0, -0.36)):
            k.put(cyl(0.065, 0.02, 12), dmat, M=D @ TRS(dx, 0.01, dz, 90, 0, 0))
    k.put(ico(0.03, 1), "BH_Gold", M=M @ T(0, -0.03, -h * 0.02))


def plate_mannequin(k, x, y):
    """Polished plate harness on a wooden stand: greaves, faulds, breastplate, pauldrons, arms, great helm, plume."""
    st = "BH_Silver"
    k.put(cyl(0.3, 0.08, 12, bev=0.01), "BH_WoodDark", M=T(x, y, 0))
    k.put(cyl(0.26, 0.03, 12), "BH_Gold", M=T(x, y, 0.08))
    for sx in (-1, 1):
        lx = x + sx * 0.1
        k.put(box(0.1, 0.22, 0.07, bev=0.02), st, M=T(lx, y - 0.04, 0.145))
        k.put(lathe([(0.055, 0.0), (0.065, 0.12), (0.06, 0.3), (0.075, 0.42), (0.07, 0.48)], 8), st,
              M=T(lx, y, 0.16), smooth=40)
        k.put(ico(0.07, 1), st, M=T(lx, y - 0.01, 0.66), smooth=40)
        k.put(lathe([(0.07, 0.0), (0.08, 0.15), (0.09, 0.3)], 8), st, M=T(lx, y, 0.68), smooth=40)
    for i, z in enumerate((0.98, 1.04, 1.1)):
        k.put(lathe([(0.2 - i * 0.01, 0.0), (0.18 - i * 0.012, 0.07)], 12), st, M=T(x, y, z) @ S(1.0, 0.75, 1.0), smooth=40)
    k.put(lathe([(0.17, 0.0), (0.2, 0.12), (0.22, 0.26), (0.2, 0.36), (0.13, 0.42), (0.07, 0.45)], 12), st,
          M=T(x, y, 1.14) @ S(1.0, 0.72, 1.0), smooth=40)
    k.put(box(0.02, 0.02, 0.3), "BH_Gold", M=T(x, y - 0.155, 1.34))
    k.put(torus(0.075, 0.012, 10, 4), "BH_Gold", M=T(x, y, 1.59))
    for sx in (-1, 1):
        sh = ico(1.0, 2)
        for v in sh.verts:
            v.co = Vector((v.co.x * 0.13, v.co.y * 0.12, max(v.co.z, -0.2) * 0.1))
        k.put(sh, st, M=T(x + sx * 0.23, y, 1.5) @ R(0, sx * 25, 0), smooth=45)
        k.put(tube([(x + sx * 0.25, y, 1.45), (x + sx * 0.28, y - 0.02, 1.2), (x + sx * 0.27, y - 0.07, 0.98)],
                   [0.055, 0.05, 0.045], 8), st, smooth=40)
        k.put(box(0.07, 0.1, 0.1, bev=0.02), st, M=T(x + sx * 0.27, y - 0.09, 0.92))
    # great helm with an eye slit and a crimson plume
    k.put(cyl(0.035, 0.05, 8), "BH_WoodDark", M=T(x, y, 1.58))
    k.put(lathe([(0.11, 0.0), (0.12, 0.12), (0.12, 0.24), (0.1, 0.28), (0.0, 0.29)], 10), st, M=T(x, y, 1.62), smooth=35)
    k.put(box(0.16, 0.03, 0.022), "BH_StoneDark", M=T(x, y - 0.115, 1.8))
    k.put(box(0.02, 0.03, 0.18), "BH_Gold", M=T(x, y - 0.118, 1.73))
    for i in range(5):
        a = -50 + i * 25
        k.put(cyl(0.022, 0.2, 5, r2=0.005), "BH_ClothRed", M=T(x, y + 0.02, 1.9) @ R(a * 0.4, a, 0))


@asset("stand_armsbroker", "market")
def stand_armsbroker(k):
    r = k.r
    HX, Y0, Y1 = 2.4, -1.0, 1.62
    CYc, HYc = (Y0 + Y1) / 2, (Y1 - Y0) / 2
    EZ, PK = 3.45, 1.15      # eave height, king poles at x = +-PK

    # ---- twin-peaked crimson marquee -------------------------------------------------------------------------
    def ridge(x):
        return 4.38 + 0.34 * math.exp(-((abs(x) - PK) / 0.32) ** 2)

    def canopy(u, v):
        x = lerp(-HX, HX, u)
        y = lerp(Y0, Y1, v)
        s = max(abs(y - CYc) / HYc, max(0.0, abs(x) - PK) / (HX - PK))
        z = EZ + (ridge(x) - EZ) * (1.0 - s) ** 1.35
        z -= 0.05 * math.sin(math.pi * u * 4) ** 2 * (s > 0.97)
        return (x, y, z)
    sheet(k, canopy, 32, 14, "BH_ClothRed", th=0.03, smooth=45)
    wood = "BH_WoodDark"
    for sx in (-1, 1):
        k.put(cyl(0.065, 4.8, 8, r2=0.05), wood, M=T(sx * PK, CYc, 0), smooth=40)
        k.put(ico(0.065, 2), "BH_Gold", M=T(sx * PK, CYc, 4.87), smooth=50)
        k.put(cyl(0.02, 0.08, 6, r2=0.0), "BH_Gold", M=T(sx * PK, CYc, 4.92))
        k.put(cyl(0.12, 0.08, 8, r2=0.07), "BH_Gold", M=T(sx * PK, CYc, 4.72))
        for y in (Y0 - 0.02, CYc, Y1 - 0.04):
            k.put(cyl(0.06, EZ, 8), wood, M=T(sx * (HX - 0.04), y, 0), smooth=40)
            k.put(ico(0.07, 1), "BH_Gold", M=T(sx * (HX - 0.04), y, EZ + 0.02))
    rod(k, (-HX, Y0 - 0.02, EZ - 0.02), (HX, Y0 - 0.02, EZ - 0.02), 0.045, wood, 8)
    rod(k, (-HX, Y1 - 0.04, EZ - 0.02), (HX, Y1 - 0.04, EZ - 0.02), 0.045, wood, 8)
    for sx in (-1, 1):
        rod(k, (sx * (HX - 0.04), Y0, EZ - 0.02), (sx * (HX - 0.04), Y1, EZ - 0.02), 0.045, wood, 8)
    rod(k, (-PK, CYc, 4.5), (PK, CYc, 4.45), 0.04, wood, 6)
    # black scalloped valance on all four sides, gold tassels at the front
    cs = [(-HX - 0.02, Y0 - 0.06), (HX + 0.02, Y0 - 0.06), (HX + 0.02, Y1 + 0.02), (-HX - 0.02, Y1 + 0.02)]
    for i, n in enumerate((14, 8, 14, 8)):
        valance(k, cs[i], cs[(i + 1) % 4], EZ + 0.04, 0.07, 0.17, n, "BH_ClothBlack",
                tassel="BH_Gold" if i == 0 else None)
    # back curtain and back halves of the side curtains (folded), rug
    sheet(k, lambda u, v: (lerp(-HX + 0.06, HX - 0.06, u), Y1 - 0.02 + 0.045 * math.sin(u * 40), lerp(EZ - 0.02, 0.02, v)),
          60, 2, "BH_ClothRed", th=0.02, smooth=50)
    for sx in (-1, 1):
        sheet(k, lambda u, v, sx=sx: (sx * (HX - 0.02) + 0.045 * math.sin(u * 16) * (1 - 0.6 * v),
                                       lerp(CYc - 0.35 - 0.2 * v, Y1 - 0.02, u), lerp(EZ - 0.02, 0.02, v)),
              24, 3, "BH_ClothRed", th=0.02, smooth=50)
        k.put(torus(0.07, 0.015, 8, 3), "BH_Gold", M=TRS(sx * (HX - 0.02), CYc - 0.4, 1.1, 0, 90, 0))
    k.put(box(3.4, 2.2, 0.012), "BH_ClothBlack", M=T(-0.1, 0.35, 0.006))
    for (sx_, sy_, dx, dy) in ((3.4, 0.08, -0.1, -0.71), (3.4, 0.08, -0.1, 1.41), (0.08, 2.2, -1.76, 0.35), (0.08, 2.2, 1.56, 0.35)):
        k.put(box(sx_, sy_, 0.014), "BH_ClothRed", M=T(dx, dy, 0.007))

    # ---- heavy ledger desk with an open strongbox ------------------------------------------------------------
    dx0, dx1, dy0, dy1, DZ = -0.25, 1.15, -1.2, -0.62, 0.84
    dcx, dcy = (dx0 + dx1) / 2, (dy0 + dy1) / 2
    k.put(box(dx1 - dx0 + 0.08, dy1 - dy0 + 0.06, 0.08, bev=0.02), wood, M=T(dcx, dcy, DZ - 0.04))
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(lathe([(0.07, 0.0), (0.06, 0.08), (0.075, 0.2), (0.05, 0.5), (0.065, DZ - 0.2), (0.06, DZ - 0.08)], 8),
                  wood, M=T(dcx + sx * (dx1 - dx0 - 0.12) / 2, dcy + sy * (dy1 - dy0 - 0.1) / 2, 0), smooth=40)
    k.put(box(dx1 - dx0 - 0.1, 0.04, 0.46), wood, M=T(dcx, dy0 + 0.06, DZ - 0.33))
    for px in (-0.4, 0.0, 0.4):
        k.put(box(0.34, 0.03, 0.3, bev=0.01), wood, M=T(dcx + px, dy0 + 0.035, DZ - 0.33))
        k.put(ico(0.02, 1), "BH_Brass", M=T(dcx + px, dy0 + 0.01, DZ - 0.33))
    k.put(box(dx1 - dx0 - 0.05, 0.03, 0.12), wood, M=T(dcx, dy0 + 0.04, 0.1))
    # writing slope with an open ledger, inkwell and quill
    k.put(hexa([(0.02, -0.98, DZ), (0.62, -0.98, DZ), (0.62, -0.68, DZ), (0.02, -0.68, DZ),
                (0.02, -0.98, DZ + 0.1), (0.62, -0.98, DZ + 0.1), (0.62, -0.68, DZ + 0.03), (0.02, -0.68, DZ + 0.03)], 0.008), wood)
    sl = math.degrees(math.atan2(0.07, 0.3))
    k.put(box(0.5, 0.3, 0.02, bev=0.004), "BH_Leather", M=TRS(0.32, -0.83, DZ + 0.075, -sl, 0, 0))
    for sx in (-1, 1):
        k.put(box(0.23, 0.27, 0.02), "BH_Paper", M=TRS(0.32 + sx * 0.12, -0.83, DZ + 0.09, -sl, -sx * 5, 0))
    k.put(box(0.008, 0.26, 0.006), "BH_ClothRed", M=TRS(0.32, -0.83, DZ + 0.102, -sl, 0, 0))
    k.put(cyl(0.03, 0.05, 8), "BH_Iron", M=T(-0.08, -0.75, DZ))
    k.put(prism([(0.0, 0.0), (0.012, 0.08), (0.004, 0.24), (-0.01, 0.1)], 0.004), "BH_Bone", M=TRS(-0.08, -0.75, DZ + 0.04, 0, 25, 30))
    for (cx_, cy2, n) in ((-0.14, -1.02, 6), (-0.07, -1.08, 4), (-0.02, -0.98, 8), (0.72, -1.08, 3)):
        for j in range(n):
            k.put(cyl(0.022, 0.007, 10), "BH_Gold", M=T(cx_ + r.uniform(-0.003, 0.003), cy2, DZ + j * 0.0075))
    k.put(ico(0.05, 1), "BH_Leather", M=TRS(0.72, -0.8, DZ + 0.035, s=(1, 1, 0.8)))
    k.put(cyl(0.02, 0.04, 6), "BH_Leather", M=T(0.72, -0.8, DZ + 0.07))
    sb = (0.93, -0.95)
    k.put(box(0.36, 0.26, 0.2, bev=0.01, base=True), "BH_Iron", M=T(sb[0], sb[1], DZ))
    k.put(box(0.33, 0.23, 0.02), "BH_Gold", M=T(sb[0], sb[1], DZ + 0.18))
    for i in range(10):
        k.put(cyl(0.022, 0.007, 10), "BH_Gold", M=TRS(sb[0] + r.uniform(-0.12, 0.12), sb[1] + r.uniform(-0.08, 0.08),
                                                         DZ + 0.192, r.uniform(-20, 20), r.uniform(-20, 20), 0))
    gem(k, T(sb[0] - 0.05, sb[1] + 0.02, DZ + 0.2), 0.022, "BH_GemRed")
    gem(k, T(sb[0] + 0.07, sb[1] - 0.04, DZ + 0.2), 0.018, "BH_GemAqua")
    Ml = T(sb[0], sb[1] + 0.13, DZ + 0.2) @ R(-105, 0, 0)
    k.put(box(0.36, 0.26, 0.05, bev=0.01), "BH_Iron", M=Ml @ T(0, -0.13, 0.025))
    for sx in (-1, 0, 1):
        k.put(box(0.035, 0.265, 0.055), "BH_Metal", M=Ml @ T(sx * 0.13, -0.13, 0.025))
    for sx in (-1, 1):
        k.put(box(0.035, 0.27, 0.205, base=True), "BH_Metal", M=T(sb[0] + sx * 0.13, sb[1], DZ))
    k.put(box(0.08, 0.02, 0.07), "BH_Brass", M=T(sb[0], sb[1] - 0.135, DZ + 0.12))

    # ---- tall weapon rack (left): greatsword, spear, long axe, longbow ------------------------------------
    RX0, RX1, RY = -2.22, -0.98, -0.5
    for xx in (RX0, RX1):
        k.put(box(0.1, 0.1, 2.3, bev=0.015, base=True), wood, M=T(xx, RY, 0))
        k.put(box(0.1, 0.5, 0.08, bev=0.015, base=True), wood, M=T(xx, RY, 0))
        k.put(ico(0.06, 1), "BH_Brass", M=T(xx, RY, 2.34))
    k.put(box(RX1 - RX0 + 0.1, 0.1, 0.08, bev=0.015), wood, M=T((RX0 + RX1) / 2, RY, 2.12))
    k.put(box(RX1 - RX0 + 0.1, 0.08, 0.07, bev=0.015), wood, M=T((RX0 + RX1) / 2, RY - 0.02, 1.25))
    k.put(box(RX1 - RX0 + 0.1, 0.3, 0.12, bev=0.015, base=True), wood, M=T((RX0 + RX1) / 2, RY - 0.08, 0.1))
    k.put(box(RX1 - RX0 + 0.1, 0.1, 0.1, bev=0.01), wood, M=T((RX0 + RX1) / 2, RY + 0.03, 0.05))
    for xx in (-2.0, -1.72, -1.46, -1.2):
        k.put(box(0.03, 0.04, 0.06), "BH_Brass", M=T(xx - 0.07, RY - 0.08, 2.12))
        k.put(box(0.03, 0.04, 0.06), "BH_Brass", M=T(xx + 0.07, RY - 0.08, 2.12))
    wy = RY - 0.1
    # greatsword, point up
    gx = -2.0
    k.put(ico(0.035, 1), "BH_Gold", M=T(gx, wy, 0.26))
    k.put(cyl(0.02, 0.26, 6), "BH_Leather", M=T(gx, wy, 0.28))
    k.put(box(0.36, 0.04, 0.035, bev=0.008), "BH_Gold", M=T(gx, wy, 0.56))
    for sx in (-1, 1):
        k.put(ico(0.022, 1), "BH_Gold", M=T(gx + sx * 0.19, wy, 0.56))
    bl = box(0.075, 0.014, 1.32, bev=0.004)
    slice_plane(bl, (0, 0, 0.66 - 0.1), (0.7, 0, 1))
    slice_plane(bl, (0, 0, 0.66 - 0.1), (-0.7, 0, 1))
    k.put(bl, "BH_Silver", M=T(gx, wy, 0.58 + 0.66))
    k.put(box(0.015, 0.018, 1.0), "BH_Metal", M=T(gx, wy, 0.58 + 0.55))
    # spear
    sx_ = -1.72
    k.put(cyl(0.02, 2.3, 6), "BH_Wood", M=T(sx_, wy, 0.2), smooth=40)
    k.put(cyl(0.028, 0.08, 6), "BH_Gold", M=T(sx_, wy, 2.45))
    leaf = [(0.0, 0.0), (0.045, 0.08), (0.03, 0.22), (0.0, 0.3), (-0.03, 0.22), (-0.045, 0.08)]
    k.put(prism(leaf, 0.016), "BH_Silver", M=T(sx_, wy, 2.52))
    k.put(prism(leaf, 0.016), "BH_Silver", M=T(sx_, wy, 2.52) @ R(0, 0, 90))
    # long bearded axe
    ax = -1.46
    k.put(cyl(0.022, 1.9, 6), "BH_WoodDark", M=T(ax, wy, 0.2), smooth=40)
    k.put(cyl(0.03, 0.12, 6), "BH_Gold", M=T(ax, wy, 1.7))
    k.put(prism([(0.0, -0.06), (0.1, -0.02), (0.22, -0.2), (0.3, -0.12), (0.32, 0.14), (0.24, 0.2), (0.1, 0.06), (0.0, 0.06)],
                0.018), "BH_Silver", M=T(ax, wy, 1.86))
    k.put(prism([(0.0, -0.04), (-0.12, -0.02), (-0.14, 0.02), (0.0, 0.04)], 0.03), "BH_Iron", M=T(ax, wy, 1.86))
    # longbow with string
    bw = -1.2
    bpts = [(bw + 0.09 * math.sin(math.pi * i / 10), wy, 0.24 + 1.72 * i / 10) for i in range(11)]
    k.put(tube(bpts, [0.012, 0.016, 0.02, 0.022, 0.024, 0.026, 0.024, 0.022, 0.02, 0.016, 0.012], 5), "BH_WoodDark", smooth=45)
    k.put(cyl(0.03, 0.14, 6), "BH_Leather", M=T(bw + 0.09, wy, 1.03))
    rod(k, bpts[0], bpts[-1], 0.004, "BH_Rope", 3)
    # heraldic shields leaning at the rack foot
    heater_shield(k, T(-1.95, RY - 0.28, 0.6) @ R(-14, 0, -6), "BH_ClothBlue", "chevron", "BH_Gold")
    heater_shield(k, T(-1.38, RY - 0.28, 0.6) @ R(-14, 0, 5), "BH_ClothBlack", "roundels", "BH_Gold")

    # ---- barrel of spears and a bundle of arrows (front left) ---------------------------------------------
    keg(k, T(-1.98, -1.32, 0), 0.72, 0.26, mat="BH_Wood")
    for i, (dx, dy, h, a, head) in enumerate(((-0.08, -0.05, 2.1, 6, "spear"), (0.07, 0.04, 1.85, -8, "spear"),
                                             (0.05, -0.08, 1.6, 10, "fork"), (-0.06, 0.08, 2.25, -4, "halberd"))):
        M = T(-1.98 + dx, -1.32 + dy, 0.3) @ R(a * 0.5, a, 0)
        k.put(cyl(0.018, h - 0.3, 5), "BH_Wood", M=M, smooth=40)
        top = M @ T(0, 0, h - 0.3)
        if head == "spear":
            k.put(prism(leaf, 0.014), "BH_Metal", M=top)
        elif head == "fork":
            for sx in (-1, 0, 1):
                k.put(cyl(0.008, 0.2, 4, r2=0.002), "BH_Metal", M=top @ T(sx * 0.04, 0, 0))
            k.put(box(0.1, 0.02, 0.02), "BH_Metal", M=top)
        else:
            k.put(prism([(0.0, -0.08), (0.2, -0.12), (0.22, 0.06), (0.0, 0.08)], 0.014), "BH_Metal", M=top @ T(0, 0, -0.1))
            k.put(prism(leaf, 0.014), "BH_Metal", M=top)
    for i in range(9):
        a = r.uniform(0, 6.28)
        d = r.uniform(0, 0.05)
        M = T(-1.98 + 0.12 + math.cos(a) * d, -1.32 - 0.1 + math.sin(a) * d, 0.5) @ R(r.uniform(-8, 8), r.uniform(-8, 8), 0)
        k.put(cyl(0.006, 0.55, 3), "BH_Wood", M=M)
        k.put(prism([(0.0, 0.0), (0.03, -0.08), (-0.03, -0.08)], 0.004), "BH_ClothRed", M=M @ T(0, 0, 0.62))

    # ---- open crate of new swords (front, left of the desk) -------------------------------------------------
    cx, cy2 = -0.62, -1.25
    for sy in (-1, 1):
        plank(k, 0.62, 0.03, 0.34, T(cx, cy2 + sy * 0.2, 0.19), mat="BH_Wood", tint=1.0)
    for sx in (-1, 1):
        plank(k, 0.4, 0.03, 0.34, T(cx + sx * 0.3, cy2, 0.19) @ R(0, 0, 90), mat="BH_Wood", tint=1.0)
    k.put(box(0.58, 0.38, 0.03), "BH_Wood", M=T(cx, cy2, 0.03))
    t = box(0.56, 0.36, 0.1)
    subdiv(t, 2)
    ndisp(t, 14, 0.03, k.noff)
    k.put(t, "BH_Thatch", M=T(cx, cy2, 0.32), smooth=30)
    for i, dx in enumerate((-0.18, -0.06, 0.06, 0.18)):
        M = T(cx + dx, cy2 + (0.05 if i % 2 else -0.05), 0.36) @ R(r.uniform(-8, 8), r.uniform(-10, 10), 0)
        k.put(cyl(0.016, 0.2, 5), "BH_Leather", M=M)
        k.put(box(0.18, 0.03, 0.025), "BH_Gold" if i % 2 else "BH_Iron", M=M @ T(0, 0, 0.0))
        k.put(ico(0.025, 1), "BH_Gold" if i % 2 else "BH_Iron", M=M @ T(0, 0, 0.21))
    k.put(box(0.64, 0.06, 0.03), "BH_Wood", M=TRS(cx, cy2 + 0.34, 0.2, 60, 0, 0))

    # ---- armour on its stand (front right), shields hung on the front poles ----------------------------------
    plate_mannequin(k, 1.78, -1.18)
    heater_shield(k, T(-HX + 0.2, Y0 - 0.1, 2.5), "BH_ClothGreen", "cross", "BH_Silver")
    heater_shield(k, T(HX - 0.2, Y0 - 0.1, 2.5), "BH_Gold", "pale", "BH_ClothBlack")
    for sx in (-1, 1):
        k.put(box(0.3, 0.12, 0.05), wood, M=T(sx * (HX - 0.2), Y0 - 0.05, 2.52))

    # ---- lanterns on the front spar ------------------------------------------------------------------------
    la = lantern_on_hook(k, -0.55, Y0 - 0.02, EZ - 0.07, 0.55)
    lb = lantern_on_hook(k, 1.4, Y0 - 0.02, EZ - 0.07, 0.5)

    k.sockets.append(("npc", (0.45, -0.14, 0.0)))
    k.sockets.append(("customer", (0.45, -1.78, 0.0)))
    k.sockets.append(("light_a", la))
    k.sockets.append(("light_b", lb))

    k.col_box(dx1 - dx0 + 0.08, dy1 - dy0 + 0.06, 0.9, T(dcx, dcy, 0.45))
    k.col_box(RX1 - RX0 + 0.2, 0.5, 2.2, T((RX0 + RX1) / 2, RY - 0.05, 1.1))
    k.col_box(0.6, 0.6, 1.2, T(-1.98, -1.32, 0.6))
    k.col_box(0.66, 0.44, 0.4, T(cx, cy2, 0.2))
    k.col_mesh(cyl(0.32, 2.0, 8), T(1.78, -1.18, 0))
    k.col_box(2 * HX, 0.12, 2.2, T(0, Y1 - 0.02, 1.1))
    for sx in (-1, 1):
        k.col_box(0.14, Y1 - CYc + 0.35, 2.2, T(sx * (HX - 0.02), (Y1 + CYc - 0.35) / 2, 1.1))
        for y in (Y0 - 0.02, CYc):
            k.col_box(0.16, 0.16, 2.2, T(sx * (HX - 0.04), y, 1.1))
        k.col_box(0.16, 0.16, 2.2, T(sx * PK, CYc, 1.1))
    return dict(recenter=False)


# =================================================================================================================
# 9. stand_gemcutter - Anselm Cray, Gem-cutter (Socket Specialist of Olivar)
def cloche(k, M, mat, rr=0.07, hh=0.2):
    """Specimen under a brass-ribbed cloche (a cage stands in for the glass; BH_Glass is a lantern glow in game)."""
    k.put(cyl(rr + 0.012, 0.022, 12), "BH_Brass", M=M)
    k.put(cyl(rr * 0.6, 0.02, 8), "BH_StoneDark", M=M @ T(0, 0, 0.02))
    cluster(k, M @ T(0, 0, 0.03), 3, hh * 0.62, rr * 0.28, (mat,), spread=0.35, rad=rr * 0.25)
    k.put(torus(rr, 0.005, 12, 3), "BH_Brass", M=M @ T(0, 0, 0.024))
    prof = [(rr, 0.024), (rr * 1.03, hh * 0.45), (rr * 0.85, hh * 0.78), (rr * 0.5, hh * 0.95), (0.0, hh)]
    for a in range(0, 360, 60):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        k.put(tube([M @ Vector((c * p[0], s * p[0], p[1])) for p in prof], 0.0035, 3), "BH_Brass")
    k.put(torus(rr * 0.97, 0.004, 12, 3), "BH_Brass", M=M @ T(0, 0, hh * 0.5))
    k.put(ico(0.014, 1), "BH_Brass", M=M @ T(0, 0, hh + 0.008))


@asset("stand_gemcutter", "market")
def stand_gemcutter(k):
    r = k.r
    RP, RE = 1.78, 2.03          # post ring (vertex radius), roof eave (vertex radius)
    ZE, ZA = 2.98, 4.44          # eave, roof apex
    a0 = math.radians(22.5)
    V = [(math.cos(a0 + i * math.pi / 4), math.sin(a0 + i * math.pi / 4)) for i in range(8)]
    wood = "BH_WoodDark"

    # ---- octagonal stone floor --------------------------------------------------------------------------------
    k.put(lathe([(1.86, 0.0), (1.86, 0.05), (1.8, 0.07), (0.0, 0.07)], 8, angle0=a0), "BH_Stone", smooth=None)
    for i in range(8):
        c, s = V[i]
        k.put(box(1.7, 0.02, 0.012), "BH_StoneDark", M=TRS(c * 0.9, s * 0.9, 0.072, 0, 0, math.degrees(a0 + i * math.pi / 4) + 90))
    k.put(lathe([(0.95, 0.07), (0.95, 0.078), (0.9, 0.078)], 8, angle0=a0, cap_bot=False, cap_top=False), "BH_StoneDark")

    # ---- posts, ring beam, knee brackets, hip rafters --------------------------------------------------------
    for i in range(8):
        c, s = V[i]
        x, y = c * RP, s * RP
        k.put(box(0.26, 0.26, 0.22, bev=0.02, base=True), "BH_Stone", M=TRS(x, y, 0.0, 0, 0, math.degrees(a0 + i * math.pi / 4)))
        k.put(cyl(0.075, ZE - 0.2, 8), wood, M=T(x, y, 0.2), smooth=None)
        k.put(torus(0.08, 0.012, 8, 3), "BH_Iron", M=T(x, y, 0.3))
        c2, s2 = V[(i + 1) % 8]
        x2, y2 = c2 * RP, s2 * RP
        mx, my = (x + x2) / 2, (y + y2) / 2
        L = math.hypot(x2 - x, y2 - y)
        k.put(box(L + 0.1, 0.13, 0.17, bev=0.02), wood,
              M=TRS(mx, my, ZE - 0.05, 0, 0, math.degrees(math.atan2(y2 - y, x2 - x))))
        for (px, py, qx, qy) in ((x, y, x2, y2), (x2, y2, x, y)):
            dx, dy = (qx - px) / L, (qy - py) / L
            pts = [(px + dx * 0.36 * (1 - math.cos(math.radians(a))), py + dy * 0.36 * (1 - math.cos(math.radians(a))),
                    ZE - 0.13 - 0.36 + 0.36 * math.sin(math.radians(a))) for a in range(0, 91, 18)]
            k.put(tube(pts, 0.025, 5), wood, smooth=40)
        k.put(tube([(x, y, ZE + 0.03), (0.0, 0.0, ZA - 0.12)], 0.06, 5), wood, smooth=None)

    # ---- concave slate spire: base shell + stepped courses + lead hip rolls -----------------------------------
    prof = [(RE, ZE), (1.62, ZE + 0.28), (1.22, ZE + 0.6), (0.84, ZE + 0.93), (0.5, ZE + 1.2), (0.22, ZE + 1.38),
            (0.0, ZA)]
    t = lathe([(p[0], p[1]) for p in prof], 8, angle0=a0)
    k.put(solid(t, 0.05), "BH_Slate", smooth=None)
    for j in range(len(prof) - 2):
        (r0, z0), (r1, z1) = prof[j], prof[j + 1]
        for i in range(8):
            c, s = V[i]
            c2, s2 = V[(i + 1) % 8]
            lift = 0.035
            lo = [(c * (r0 + 0.02), s * (r0 + 0.02), z0 - 0.02 + lift), (c2 * (r0 + 0.02), s2 * (r0 + 0.02), z0 - 0.02 + lift)]
            hi = [(c2 * r1, s2 * r1, z1 + lift), (c * r1, s * r1, z1 + lift)]
            pl = hexa([lo[0], lo[1], hi[0], hi[1]] + [(p[0], p[1], p[2] + 0.035) for p in (lo[0], lo[1], hi[0], hi[1])])
            k.put(pl, "BH_Slate", smooth=None)
    for i in range(8):
        c, s = V[i]
        k.put(tube([(c * p[0] * 1.005, s * p[0] * 1.005, p[1] + 0.085) for p in prof[:-1]], 0.035, 5), "BH_Iron", smooth=40)
    k.put(lathe([(RE + 0.02, ZE - 0.04), (RE + 0.02, ZE + 0.04), (RE - 0.1, ZE + 0.08)], 8, angle0=a0,
                cap_bot=False, cap_top=False), "BH_Iron")

    # ---- crowning crystal finial -------------------------------------------------------------------------------
    k.put(lathe([(0.2, 0.0), (0.16, 0.08), (0.09, 0.12), (0.07, 0.2), (0.11, 0.24), (0.0, 0.25)], 8), "BH_Iron",
          M=T(0, 0, ZA - 0.12), smooth=None)
    k.put(torus(0.1, 0.018, 10, 4), "BH_Brass", M=T(0, 0, ZA + 0.1))
    zc = ZA + 0.12
    spike(k, (0, 0, zc), (0.0, 0.0, 1.0), 0.44, 0.085, "BH_GemAqua", segs=6, tip=0.28)
    for i, a in enumerate((20, 110, 200, 290)):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        spike(k, (c * 0.06, s * 0.06, zc + 0.02), (c * 0.55, s * 0.55, 1.0), (0.24, 0.2, 0.26, 0.18)[i], 0.05,
              "BH_GemAqua", segs=6)

    # ---- round workbench with a foot-powered lap -----------------------------------------------------------
    BX, BY, BR, BZ = 0.0, 0.14, 0.62, 0.9
    k.put(cyl(BR, 0.07, 16, bev=0.012), wood, M=T(BX, BY, BZ - 0.07))
    k.put(torus(BR, 0.014, 20, 3), "BH_Brass", M=T(BX, BY, BZ - 0.035))
    k.put(cyl(0.14, BZ - 0.07, 8), wood, M=T(BX, BY, 0.0), smooth=40)
    k.put(cyl(0.3, 0.06, 8), wood, M=T(BX, BY, 0.0))
    k.put(cyl(BR * 0.8, 0.03, 12), "BH_Wood", M=T(BX, BY, 0.3))
    for a in (45, 135, 225, 315):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        rod(k, (BX + c * BR * 0.8, BY + s * BR * 0.8, BZ - 0.07), (BX + c * BR * 0.85, BY + s * BR * 0.85, 0.0), 0.03, wood, 5)
    # lap (horizontal cutting disc) on the right front of the bench, faceting jamb peg, dop stick with a stone
    LX, LY = BX + 0.28, BY - 0.2
    k.put(cyl(0.2, 0.03, 16), "BH_Iron", M=T(LX, LY, BZ))
    k.put(cyl(0.17, 0.034, 16), "BH_Copper", M=T(LX, LY, BZ + 0.002))
    k.put(cyl(0.02, 0.05, 6), "BH_Iron", M=T(LX, LY, BZ + 0.03))
    k.put(box(0.08, 0.08, 0.26, bev=0.01, base=True), wood, M=T(LX - 0.27, LY + 0.06, BZ))
    for z in (0.08, 0.14, 0.2):
        k.put(cyl(0.012, 0.085, 5), "BH_StoneDark", M=TRS(LX - 0.27, LY + 0.06, BZ + z, 0, 90, 0) @ T(0, 0, -0.0425))
    dop0 = Vector((LX - 0.24, LY + 0.06, BZ + 0.2))
    dop1 = Vector((LX - 0.06, LY + 0.02, BZ + 0.05))
    rod(k, dop0, dop1, 0.008, "BH_Wood", 4)
    gem(k, T(*dop1) @ R(0, 0, 0), 0.022, "BH_GemRed")
    k.put(ico(0.018, 1), "BH_Candle", M=T(*(dop1 + (dop0 - dop1).normalized() * 0.03)))
    # flywheel under the bench, crank, pitman rod and treadle
    FW = Vector((BX + 0.42, BY + 0.1, 0.42))
    wheel(k, T(*FW) @ R(0, 0, 90), 0.3, 6, 0, "BH_Wood")
    rod(k, FW + Vector((0.14, 0, 0)), FW + Vector((0.14, 0.12, -0.02)), 0.014, "BH_Iron", 4)
    k.put(box(0.12, 0.62, 0.04, bev=0.01), "BH_Wood", M=TRS(BX + 0.62, BY + 0.05, 0.1, 8, 0, 0))
    k.put(cyl(0.03, 0.2, 6), "BH_Iron", M=TRS(BX + 0.62, BY + 0.34, 0.06, 0, 90, 0) @ T(0, 0, -0.1))
    rod(k, (BX + 0.62, BY - 0.15, 0.13), FW + Vector((0.16, 0.12, -0.02)), 0.012, "BH_Wood", 4)
    rod(k, FW + Vector((0.0, 0.0, 0.3)), Vector((LX + 0.05, LY + 0.02, BZ - 0.07)), 0.008, "BH_Leather", 4)
    rod(k, FW + Vector((0.0, -0.05, 0.28)), Vector((LX - 0.02, LY - 0.02, BZ - 0.07)), 0.008, "BH_Leather", 4)
    # specimens under cloches around the rim, a tray of cut stones, loose rough stones
    for a, m in ((70, "BH_GemViolet"), (105, "BH_GemAmber"), (140, "BH_GemGreen"), (175, "BH_GemRed"), (35, "BH_GemGold"),
                 (210, "BH_GemAqua")):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        cloche(k, T(BX + c * 0.47, BY + s * 0.47, BZ), m)
    k.put(box(0.26, 0.18, 0.03, bev=0.005, base=True), wood, M=TRS(BX - 0.2, BY - 0.38, BZ, 0, 0, -15))
    k.put(box(0.23, 0.15, 0.01), "BH_Velvet", M=TRS(BX - 0.2, BY - 0.38, BZ + 0.03, 0, 0, -15))
    for i in range(12):
        u, v = (i % 4 - 1.5) * 0.05, (i // 4 - 1) * 0.045
        c15, s15 = math.cos(math.radians(-15)), math.sin(math.radians(-15))
        gem(k, T(BX - 0.2 + u * c15 - v * s15, BY - 0.38 + u * s15 + v * c15, BZ + 0.045), 0.012, GEMS[i % 6])
    for i in range(5):
        k.put(rock(r, (0.04, 0.035, 0.03), cuts=4, subd=1, seed_off=30 + i), "BH_StoneDark",
              M=T(BX + r.uniform(-0.1, 0.12), BY + r.uniform(0.0, 0.2), BZ))
    k.put(cyl(0.005, 0.12, 4), "BH_Iron", M=TRS(BX + 0.08, BY - 0.02, BZ + 0.006, 0, 90, 30))

    # ---- front-diagonal display cabinets with split geodes and clusters ------------------------------------
    for side in (-1, 1):
        i0, i1 = (4, 5) if side < 0 else (6, 7)
        c0, s0 = V[i0]
        c1, s1 = V[i1]
        mx, my = (c0 + c1) / 2 * RP, (s0 + s1) / 2 * RP
        nx_, ny_ = -mx / math.hypot(mx, my), -my / math.hypot(mx, my)
        cxb, cyb = mx + nx_ * 0.26, my + ny_ * 0.26
        rot = math.degrees(math.atan2(s1 - s0, c1 - c0))
        Mc = T(cxb, cyb, 0) @ R(0, 0, rot)
        k.put(box(0.92, 0.34, 0.78, bev=0.015, base=True), wood, M=Mc)
        k.put(box(0.98, 0.4, 0.05, bev=0.012), wood, M=Mc @ T(0, 0, 0.8))
        k.put(box(0.99, 0.02, 0.02), "BH_Brass", M=Mc @ T(0, 0.2, 0.8))
        for dx in (-0.22, 0.22):
            k.put(box(0.38, 0.02, 0.26, bev=0.01), wood, M=Mc @ T(dx, 0.175, 0.45))
            k.put(ico(0.018, 1), "BH_Brass", M=Mc @ T(dx, 0.19, 0.45))
        geode_half(k, Mc @ T(-0.18, 0.02, 0.97) @ R(-28, 0, 0), 0.17, "BH_GemViolet" if side < 0 else "BH_GemAmber", 10)
        k.put(cyl(0.1, 0.04, 8), wood, M=Mc @ T(-0.18, 0.05, 0.825))
        cluster(k, Mc @ T(0.22, -0.02, 0.825), 6, 0.2, 0.03, ("BH_GemAqua", "BH_GemGreen") if side < 0 else
                ("BH_GemRed", "BH_GemGold"), spread=0.5, rad=0.05)
        ore_rock(k, Mc @ T(0.22, -0.02, 0.81), 0.07)
        cloche(k, Mc @ T(0.05, -0.1, 0.825), "BH_GemGreen" if side < 0 else "BH_GemViolet", 0.06, 0.16)

    # ---- back: cabinet of stone drawers and a rack of fine tools -------------------------------------------
    c0, s0 = V[1]
    c1, s1 = V[2]
    my = (s0 + s1) / 2 * RP - 0.25
    k.put(box(1.2, 0.36, 0.86, bev=0.015, base=True), wood, M=T(0, my, 0))
    k.put(box(1.26, 0.42, 0.05, bev=0.012), wood, M=T(0, my, 0.88))
    for row in range(3):
        for col in range(4):
            x = -0.43 + col * 0.287
            z = 0.18 + row * 0.25
            k.put(box(0.25, 0.02, 0.2, bev=0.006), "BH_Wood", M=T(x, my - 0.18, z))
            k.put(ico(0.014, 1), "BH_Brass", M=T(x, my - 0.195, z))
    by_ = (s0 + s1) / 2 * RP - 0.08
    k.put(box(1.2, 0.04, 0.78, bev=0.01), "BH_Wood", M=T(0, by_, 1.62))
    k.put(box(1.26, 0.06, 0.06, bev=0.01), wood, M=T(0, by_ - 0.01, 2.03))
    k.put(box(1.26, 0.06, 0.06, bev=0.01), wood, M=T(0, by_ - 0.01, 1.22))
    k.put(box(1.1, 0.12, 0.03), wood, M=T(0, by_ - 0.07, 1.36))
    for i in range(6):
        k.put(box(0.07, 0.07, 0.04, base=True), wood, M=T(-0.45 + i * 0.18, by_ - 0.07, 1.375))
        gem(k, T(-0.45 + i * 0.18, by_ - 0.07, 1.43), 0.02, GEMS[i])
    tools = [("tongs", -0.48), ("file", -0.36), ("file", -0.3), ("hammer", -0.18), ("tweezer", -0.06), ("dop", 0.04),
             ("dop", 0.09), ("dop", 0.14), ("caliper", 0.26), ("bow", 0.42)]
    for kind, x in tools:
        yb = by_ - 0.04
        k.put(cyl(0.008, 0.04, 4), wood, M=TRS(x, yb, 1.95, 90, 0, 0) @ T(0, 0, -0.02))
        if kind == "tongs":
            for sx in (-1, 1):
                rod(k, (x, yb - 0.03, 1.93), (x + sx * 0.03, yb - 0.03, 1.55), 0.007, "BH_Iron", 4)
        elif kind == "file":
            k.put(box(0.02, 0.008, 0.26), "BH_Iron", M=T(x, yb - 0.03, 1.76))
            k.put(cyl(0.012, 0.08, 5), "BH_Wood", M=T(x, yb - 0.03, 1.56))
        elif kind == "hammer":
            k.put(cyl(0.009, 0.28, 4), "BH_Wood", M=T(x, yb - 0.03, 1.62))
            k.put(box(0.1, 0.025, 0.03), "BH_Iron", M=T(x, yb - 0.03, 1.9))
        elif kind == "tweezer":
            for sx in (-1, 1):
                rod(k, (x, yb - 0.03, 1.93), (x + sx * 0.012, yb - 0.03, 1.78), 0.004, "BH_Silver", 3)
        elif kind == "dop":
            rod(k, (x, yb - 0.03, 1.93), (x, yb - 0.03, 1.72), 0.006, "BH_Wood", 4)
            k.put(ico(0.014, 1), "BH_Candle", M=T(x, yb - 0.03, 1.71))
        elif kind == "caliper":
            for sx in (-1, 1):
                k.put(tube([(x, yb - 0.03, 1.93), (x + sx * 0.05, yb - 0.03, 1.8), (x + sx * 0.02, yb - 0.03, 1.66)], 0.005, 3),
                      "BH_Brass")
        else:
            k.put(tube([(x - 0.12, yb - 0.03, 1.8), (x, yb - 0.03, 1.86), (x + 0.12, yb - 0.03, 1.8)], 0.008, 4), "BH_Wood")
            rod(k, (x - 0.12, yb - 0.03, 1.8), (x + 0.12, yb - 0.03, 1.8), 0.003, "BH_Rope", 3)

    # ---- low lattice balustrades on the side and back-diagonal edges ------------------------------------------
    for i in (0, 2, 3, 7):
        c0, s0 = V[i]
        c1, s1 = V[(i + 1) % 8]
        x0, y0, x1, y1 = c0 * RP, s0 * RP, c1 * RP, s1 * RP
        L = math.hypot(x1 - x0, y1 - y0)
        Mb = T((x0 + x1) / 2, (y0 + y1) / 2, 0) @ R(0, 0, math.degrees(math.atan2(y1 - y0, x1 - x0)))
        k.put(box(L - 0.12, 0.08, 0.06, bev=0.01), wood, M=Mb @ T(0, 0, 0.88))
        k.put(box(L - 0.12, 0.06, 0.05), wood, M=Mb @ T(0, 0, 0.16))
        for j in range(5):
            xx = -L / 2 + 0.12 + (L - 0.24) * j / 4
            k.put(lathe([(0.025, 0.0), (0.035, 0.1), (0.022, 0.3), (0.035, 0.5), (0.025, 0.66)], 6), wood,
                  M=Mb @ T(xx, 0, 0.18), smooth=40)

    # ---- lanterns on the front-diagonal beams, hanging prisms at the back ---------------------------------
    lights = []
    for side in (-1, 1):
        i0 = 4 if side < 0 else 6
        c0, s0 = V[i0]
        c1, s1 = V[i0 + 1]
        mx, my = (c0 + c1) / 2 * RP, (s0 + s1) / 2 * RP
        lights.append(lantern_on_hook(k, mx, my, ZE - 0.135, 0.5))
    for (x, y, m) in ((0.9, 1.25, "BH_GemViolet"), (-0.9, 1.25, "BH_GemAmber"), (1.35, 0.5, "BH_GemAqua"), (-1.35, 0.5, "BH_GemGreen")):
        rope_line(k, [(x, y, ZE - 0.02), (x, y, 2.45)], 0.003)
        spike(k, (x, y, 2.47), (0, 0, -1), 0.14, 0.022, m, segs=6, tip=0.35)
        spike(k, (x, y, 2.45), (0, 0, 1), 0.05, 0.02, m, segs=6, tip=0.5)

    k.sockets.append(("npc", (0.0, -1.12, 0.0)))
    k.sockets.append(("customer", (0.0, -2.42, 0.0)))
    k.sockets.append(("light_a", lights[0]))
    k.sockets.append(("light_b", lights[1]))

    k.col_mesh(cyl(BR, 1.0, 10), T(BX, BY, 0))
    k.col_box(0.3, 0.7, 0.3, T(BX + 0.62, BY + 0.1, 0.15))
    for side in (-1, 1):
        i0 = 4 if side < 0 else 6
        c0, s0 = V[i0]
        c1, s1 = V[i0 + 1]
        mx, my = (c0 + c1) / 2 * RP, (s0 + s1) / 2 * RP
        nn = math.hypot(mx, my)
        rot = math.degrees(math.atan2(s1 - s0, c1 - c0))
        k.col_box(0.98, 0.4, 1.0, T(mx - mx / nn * 0.26, my - my / nn * 0.26, 0.5) @ R(0, 0, rot))
    for i in (0, 2, 3, 7):
        c0, s0 = V[i]
        c1, s1 = V[(i + 1) % 8]
        x0, y0, x1, y1 = c0 * RP, s0 * RP, c1 * RP, s1 * RP
        k.col_box(math.hypot(x1 - x0, y1 - y0), 0.14, 1.0,
                  T((x0 + x1) / 2, (y0 + y1) / 2, 0.5) @ R(0, 0, math.degrees(math.atan2(y1 - y0, x1 - x0))))
    c0, s0 = V[1]
    c1, s1 = V[2]
    k.col_box(1.3, 0.45, 2.1, T(0, (s0 + s1) / 2 * RP - 0.2, 1.05))
    for i in range(8):
        c, s = V[i]
        k.col_box(0.26, 0.26, 2.2, T(c * RP, s * RP, 1.1))
    return dict(recenter=False)


# =================================================================================================================
# 10. stand_crystal_cart - Dagna Flint, Crystal Prospector (Socket Specialist of Wyman Outpost)
@asset("stand_crystal_cart", "market")
def stand_crystal_cart(k):
    r = k.r
    A = Vector((-1.66, -1.18, 3.95))   # pole top, front left (high)
    B = Vector((1.66, -1.18, 2.05))    # roped down to the cart's handle
    Cc = Vector((1.66, 1.16, 3.3))     # pole top, back right (high)
    D = Vector((-1.66, 1.16, 1.55))    # roped down to a stake

    # ---- twisted ochre sail (hyperbolic paraboloid) with rope hem and patches ------------------------------
    def sail(u, v):
        p = A * (1 - u) * (1 - v) + B * u * (1 - v) + Cc * u * v + D * (1 - u) * v
        p.z -= 0.14 * 16 * u * (1 - u) * v * (1 - v)
        return p
    sheet(k, sail, 14, 11, "BH_ClothOchre", th=0.02, smooth=45)
    for (u0, u1, v0, v1) in ((0.55, 0.72, 0.3, 0.46), (0.18, 0.3, 0.62, 0.8)):
        sheet(k, lambda u, v, u0=u0, u1=u1, v0=v0, v1=v1: sail(lerp(u0, u1, u), lerp(v0, v1, v)) + Vector((0, 0, 0.018)),
              3, 3, "BH_ClothCream", th=0.012, smooth=45)
    hem = [sail(t / 10, 0) for t in range(11)] + [sail(1, t / 10) for t in range(1, 11)] + \
          [sail(1 - t / 10, 1) for t in range(1, 11)] + [sail(0, 1 - t / 10) for t in range(1, 10)]
    k.put(tube(hem, 0.016, 4, closed=True), "BH_Rope", smooth=40)
    for P in (A, B, Cc, D):
        k.put(torus(0.035, 0.01, 8, 3), "BH_Iron", M=T(*P) @ R(90, 0, 0))

    # ---- two rough poles in stone cairns, stake and tie-down ropes -------------------------------------------
    for P, lean in ((A, (-4, 3)), (Cc, (3, -4))):
        base = Vector((P.x + 0.06 * (1 if P.x < 0 else -1), P.y + 0.06 * (1 if P.y < 0 else -1), 0.0))
        k.put(tube([base, Vector((P.x, P.y, P.z + 0.12))], [0.06, 0.045], 7), "BH_Bark", smooth=40)
        for i in range(6):
            a = math.tau * i / 6 + r.uniform(-0.3, 0.3)
            ore_rock(k, T(base.x + math.cos(a) * 0.15, base.y + math.sin(a) * 0.15, 0) @ R(0, 0, r.uniform(0, 360)),
                     r.uniform(0.1, 0.14), "BH_Stone", 28)
        rope_line(k, [P + Vector((0, 0, 0.1)), P + Vector((0, 0, 0.02))], 0.015)
    stake = Vector((-1.74, 1.24, 0.0))
    k.put(cyl(0.03, 0.32, 5, r2=0.012), "BH_Wood", M=TRS(stake.x, stake.y, -0.05, -10, 10, 0))
    rope_line(k, sag_pts(D, stake + Vector((0, 0, 0.22)), 0.03, 5))

    # ---- miner's handcart (tipped forward onto a log), heaped with glowing ore ------------------------------
    ax_z, cyc = 0.5, 0.42
    Mc = T(1.0, cyc, ax_z) @ R(11, 0, 0)          # cart frame: origin at the axle centre
    wood = "BH_Wood"
    for sx in (-1, 1):
        wheel(k, T(1.0 + sx * 0.56, cyc, ax_z) @ R(0, 0, 90) @ R(0, sx * 7, 0), 0.5, 10, 0, "BH_Wood")
    rod(k, (0.4, cyc, ax_z), (1.6, cyc, ax_z), 0.03, "BH_Iron", 6)
    fl, fz = 0.66, 0.1
    k.put(box(0.9, 1.3, 0.05, bev=0.01), wood, M=Mc @ T(0, 0.05, fz))
    for sx in (-1, 1):
        for j in range(3):
            plank(k, 1.32, 0.13, 0.035, Mc @ T(sx * (0.46 + 0.03 * j), 0.05, fz + 0.08 + j * 0.13) @ R(0, sx * 12 + 90, 0) @ R(0, 90, 0),
                  mat=wood, tint=1.0)
    for sy in (-1, 1):
        for j in range(3):
            plank(k, 0.92 + 0.06 * j, 0.13, 0.035, Mc @ T(0, 0.05 + sy * 0.66, fz + 0.08 + j * 0.13) @ R(90, 0, 0), mat=wood,
                  tint=1.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(box(0.05, 0.05, 0.5, base=True), "BH_WoodDark", M=Mc @ T(sx * 0.49, 0.05 + sy * 0.64, fz))
    for sx in (-1, 1):
        k.put(box(0.07, 1.9, 0.07, bev=0.01), "BH_WoodDark", M=Mc @ T(sx * 0.3, -0.45, fz - 0.06))
        k.put(cyl(0.035, 0.18, 6), "BH_Leather", M=Mc @ TRS(sx * 0.3, -1.3, fz - 0.06, 90, 0, 0))
    for sy in (-0.4, 0.3):
        k.put(box(0.95, 0.06, 0.05), "BH_Iron", M=Mc @ T(0, sy, fz - 0.035))
    k.put(tube([(0.65, -0.88, 0.0), (0.65, -0.9, 0.12), (1.35, -0.9, 0.12), (1.35, -0.88, 0.0)], 0.1, 7), "BH_Bark", smooth=40)
    k.put(cyl(0.1, 0.7, 7), "BH_Bark", M=TRS(0.65, -0.9, 0.12, 0, 90, 0), smooth=40)
    # heap: rocks + crystal points + a split geode on top
    heap = [(0.0, 0.1, 0.22, 0.28), (-0.22, -0.2, 0.18, 0.2), (0.24, -0.25, 0.2, 0.2), (-0.2, 0.35, 0.2, 0.2),
            (0.22, 0.38, 0.18, 0.2), (0.0, -0.45, 0.2, 0.17), (0.05, 0.5, 0.25, 0.17), (-0.25, 0.0, 0.3, 0.15),
            (0.26, 0.05, 0.32, 0.15), (0.02, -0.12, 0.42, 0.16)]
    for i, (hx, hy, hz, s) in enumerate(heap):
        ore_rock(k, Mc @ T(hx, hy, fz + hz - s * 0.4) @ R(0, 0, r.uniform(0, 360)), s,
                 "BH_StoneDark" if i % 3 else "BH_Stone", 40)
    heap_mats = ("BH_GemAqua", "BH_GemViolet", "BH_GemAmber", "BH_GemGreen", "BH_GemRed", "BH_GemGold")
    for i in range(11):
        hx, hy = r.uniform(-0.34, 0.34), r.uniform(-0.55, 0.55)
        hz = 0.5 - 0.35 * (abs(hx) / 0.4) ** 2 - 0.25 * (abs(hy) / 0.6) ** 2
        cluster(k, Mc @ T(hx, hy, fz + hz) @ R(r.uniform(-30, 30), r.uniform(-30, 30), 0), r.randint(2, 4),
                r.uniform(0.1, 0.2), r.uniform(0.022, 0.035), (heap_mats[i % 6],), spread=0.45, rad=0.03)
    geode_half(k, Mc @ T(0.05, -0.28, fz + 0.52) @ R(-40, 0, 8), 0.18, "BH_GemViolet", 11)
    # pick-axe and shovel leaning on the cart's left side
    p0, p1 = Vector((0.2, -0.05, 0.0)), Vector((0.42, 0.28, 1.02))
    rod(k, p0, p1, 0.022, "BH_Wood", 6)
    hd = p1 - (p1 - p0).normalized() * 0.04
    k.put(tube([hd + Vector((0.0, -0.3, -0.06)), hd + Vector((0.0, -0.12, 0.02)), hd, hd + Vector((0.0, 0.14, 0.03)),
                hd + Vector((0.0, 0.3, -0.05))], [0.004, 0.018, 0.028, 0.018, 0.006], 5), "BH_Iron", smooth=40)
    s0, s1 = Vector((0.6, -0.72, 0.0)), Vector((0.7, -0.35, 1.08))
    sd = (s1 - s0).normalized()
    rod(k, s0 + sd * 0.3, s1, 0.02, "BH_Wood", 6)
    k.put(box(0.12, 0.03, 0.025), "BH_Wood", M=T(*(s1 + sd * 0.02)) @ align_z(sd) @ R(0, 90, 0))
    blade = box(0.24, 0.3, 0.012, bev=0.004)
    for v in blade.verts:
        v.co.z += 0.03 * (v.co.x / 0.12) ** 2
    k.put(blade, "BH_Iron", M=T(*(s0 + sd * 0.16)) @ align_z(sd) @ R(90, 0, 0))

    # ---- folding table: scale, splitting block, sorted crystals, a geode half --------------------------------
    TX0, TX1, TY0, TY1, TZ = -1.56, -0.36, -1.14, -0.7, 0.8
    tcx, tcy = (TX0 + TX1) / 2, (TY0 + TY1) / 2
    for j in range(3):
        plank(k, TX1 - TX0, (TY1 - TY0) / 3 - 0.005, 0.035, T(tcx, TY0 + (TY1 - TY0) * (j + 0.5) / 3, TZ - 0.018),
              mat=wood, tint=1.0)
    for sx in (-1, 1):
        x = tcx + sx * (TX1 - TX0 - 0.2) / 2
        for s_ in (-1, 1):
            k.put(box(0.04, 0.06, 0.95), "BH_WoodDark", M=TRS(x, tcy, TZ / 2 - 0.02, s_ * 16, 0, 0))
        k.put(cyl(0.015, 0.08, 5), "BH_Iron", M=TRS(x - 0.04, tcy, TZ / 2 - 0.02, 0, 90, 0))
    k.put(box(TX1 - TX0 - 0.3, 0.035, 0.035), "BH_WoodDark", M=T(tcx, tcy, 0.2))
    # crude iron balance
    sx0 = TX0 + 0.22
    sy0 = tcy + 0.06
    k.put(box(0.14, 0.1, 0.03, base=True), "BH_Iron", M=T(sx0, sy0, TZ))
    rod(k, (sx0, sy0, TZ), (sx0, sy0, TZ + 0.34), 0.01, "BH_Iron", 4)
    k.put(box(0.34, 0.012, 0.014), "BH_Iron", M=TRS(sx0, sy0, TZ + 0.33, 0, -6, 0))
    for sx, dz in ((-1, 0.1), (1, 0.14)):
        ex = sx0 + sx * 0.16
        ez = TZ + 0.33 + sx * 0.017
        for a in (90, 210, 330):
            c_, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
            rod(k, (ex, sy0, ez), (ex + c_ * 0.045, sy0 + s_ * 0.045, TZ + dz), 0.0025, "BH_Rope", 3)
        k.put(lathe([(0.0, 0.0), (0.05, 0.01), (0.055, 0.025), (0.05, 0.025), (0.0, 0.012)], 8), "BH_Copper",
              M=T(ex, sy0, TZ + dz - 0.01))
    spike(k, (sx0 - 0.16, sy0, TZ + 0.1), (0.3, 0.2, 1.0), 0.07, 0.02, "BH_GemGreen")
    for j in range(3):
        k.put(cyl(0.018 - j * 0.004, 0.02, 6), "BH_Iron", M=T(sx0 + 0.16, sy0, TZ + 0.13 + j * 0.02))
    # splitting block: stump section, iron wedge driven into a crystal, mallet
    bxs = tcx + 0.02
    k.put(cyl(0.13, 0.14, 9), "BH_Bark", M=T(bxs, tcy - 0.02, TZ))
    k.put(cyl(0.12, 0.012, 9), "BH_Wood", M=T(bxs, tcy - 0.02, TZ + 0.14))
    spike(k, (bxs - 0.02, tcy - 0.02, TZ + 0.15), (1, 0.2, 0.25), 0.16, 0.035, "BH_GemAqua")
    spike(k, (bxs + 0.05, tcy + 0.02, TZ + 0.15), (-0.8, 0.5, 0.4), 0.1, 0.03, "BH_GemAqua")
    k.put(prism([(-0.015, 0.0), (0.015, 0.0), (0.03, 0.12), (-0.03, 0.12)], 0.035), "BH_Iron", M=T(bxs + 0.03, tcy - 0.02, TZ + 0.16))
    k.put(cyl(0.035, 0.12, 8), "BH_Wood", M=TRS(bxs + 0.12, tcy + 0.14, TZ + 0.035, 0, 90, 25) @ T(0, 0, -0.06))
    rod(k, (bxs + 0.12, tcy + 0.14, TZ + 0.035), (bxs - 0.05, tcy + 0.2, TZ + 0.02), 0.012, "BH_Wood", 4)
    # tray of sorted socket crystals (six colours) and a split geode
    trx = TX1 - 0.2
    k.put(box(0.3, 0.2, 0.04, bev=0.005, base=True), "BH_WoodDark", M=TRS(trx, tcy - 0.05, TZ, 0, 0, 6))
    for i in range(6):
        u, v = (i % 3 - 1) * 0.09, (i // 3 - 0.5) * 0.085
        k.put(box(0.08, 0.075, 0.01), "BH_Cloth", M=TRS(trx + u, tcy - 0.05 + v, TZ + 0.04, 0, 0, 6))
        for j in range(3):
            spike(k, (trx + u + r.uniform(-0.02, 0.02), tcy - 0.05 + v + r.uniform(-0.02, 0.02), TZ + 0.045),
                  (r.uniform(-1, 1), r.uniform(-1, 1), 0.25), 0.045, 0.012, GEMS[i], segs=5)
    geode_half(k, T(TX0 + 0.5, TY0 + 0.08, TZ + 0.1) @ R(-50, 0, 0), 0.12, "BH_GemAmber", 8)
    k.put(ore_rock and cyl(0.06, 0.02, 6), "BH_Cloth", M=T(TX0 + 0.5, TY0 + 0.12, TZ))

    # ---- camp clutter: ore sacks, a crate of raw crystal, water bucket, bedroll ------------------------------
    for (x, y, h) in ((-0.1, 0.95, 0.5), (0.25, 1.08, 0.44)):
        t = lathe([(0.15, 0.0), (0.22, 0.1), (0.21, h * 0.7), (0.12, h * 0.9), (0.06, h), (0.0, h)], 8)
        ndisp(t, 5.0, 0.025, k.noff + Vector((x, y, 0)))
        k.put(t, "BH_Cloth", M=T(x, y, 0) @ R(0, 0, r.uniform(0, 90)), smooth=40)
        k.put(torus(0.07, 0.012, 6, 3), "BH_Rope", M=T(x, y, h * 0.85))
    for i in range(4):
        ore_rock(k, T(-0.28 + i * 0.08, 0.72 + r.uniform(-0.05, 0.05), 0.0) @ R(0, 0, r.uniform(0, 360)), r.uniform(0.06, 0.09),
                 "BH_StoneDark", 24)
    cx, cy2 = -1.2, 0.72
    for sy in (-1, 1):
        plank(k, 0.56, 0.03, 0.36, T(cx, cy2 + sy * 0.2, 0.18), mat=wood, tint=1.0)
    for sx in (-1, 1):
        plank(k, 0.4, 0.03, 0.36, T(cx + sx * 0.265, cy2, 0.18) @ R(0, 0, 90), mat=wood, tint=1.0)
    k.put(box(0.52, 0.38, 0.03), wood, M=T(cx, cy2, 0.03))
    for i in range(6):
        ore_rock(k, T(cx + r.uniform(-0.17, 0.17), cy2 + r.uniform(-0.12, 0.12), 0.2) @ R(0, 0, r.uniform(0, 360)), 0.09,
                 "BH_StoneDark", 24)
    for i in range(4):
        cluster(k, T(cx + r.uniform(-0.15, 0.15), cy2 + r.uniform(-0.1, 0.1), 0.3), 3, 0.14, 0.025,
                (("BH_GemAmber",), ("BH_GemGreen",), ("BH_GemAqua",), ("BH_GemRed",))[i], spread=0.4, rad=0.03)
    k.put(box(0.56, 0.4, 0.03), wood, M=TRS(cx + 0.05, cy2 + 0.36, 0.26, 62, 0, 4))
    k.put(lathe([(0.13, 0.0), (0.15, 0.26), (0.14, 0.26), (0.12, 0.03), (0.0, 0.03)], 10), wood, M=T(-0.1, -0.1, 0), smooth=40)
    k.put(cyl(0.125, 0.01, 10), "BH_Water", M=T(-0.1, -0.1, 0.2))
    for z in (0.05, 0.21):
        k.put(torus(0.14 + z * 0.08, 0.008, 10, 3), "BH_Iron", M=T(-0.1, -0.1, z))
    k.put(cyl(0.11, 0.7, 10), "BH_ClothOchre", M=TRS(-1.45, 0.2, 0.11, 0, 90, 80) @ T(0, 0, -0.35), smooth=40)
    for dy in (-0.2, 0.2):
        k.put(torus(0.115, 0.012, 8, 3), "BH_Leather", M=TRS(-1.45 + dy * math.cos(math.radians(80)) * 0,
                                                              0.2 + dy, 0.11, 90, 0, 80 - 90))

    # ---- lantern on an iron hook on the front pole ----------------------------------------------------------
    hz = 2.35
    k.put(tube([(A.x + 0.05, A.y + 0.02, hz), (A.x + 0.2, A.y + 0.02, hz + 0.05), (A.x + 0.3, A.y + 0.02, hz)], 0.012, 4),
          "BH_Iron")
    la = lantern_on_hook(k, A.x + 0.3, A.y + 0.02, hz, 0.5)

    k.sockets.append(("npc", (-0.95, -0.14, 0.0)))
    k.sockets.append(("customer", (-0.95, -1.8, 0.0)))
    k.sockets.append(("light_a", la))
    k.sockets.append(("light_b", (1.0, 0.1, 1.55)))

    k.col_box(TX1 - TX0, TY1 - TY0, 0.85, T(tcx, tcy, 0.42))
    k.col_box(1.35, 1.45, 1.1, T(1.0, cyc + 0.05, 0.55))
    k.col_box(0.8, 0.9, 0.5, T(1.0, -0.75, 0.25))
    k.col_box(0.6, 0.45, 0.4, T(cx, cy2, 0.2))
    k.col_box(0.65, 0.4, 0.5, T(0.07, 1.0, 0.25))
    for P in (A, Cc):
        k.col_box(0.4, 0.4, 2.0, T(P.x + 0.06 * (1 if P.x < 0 else -1), P.y + 0.06 * (1 if P.y < 0 else -1), 1.0))
    return dict(recenter=False)
