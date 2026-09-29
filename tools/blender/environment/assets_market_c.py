"""bh-018 trade-quarter stands, part C (see work/lemondev/bh-018/contracts/stands.md).

Two Wyman Outpost stands and the three town crafting stations; the goods are the sign (no lettering):
  stand_quartermaster  4.4 x 3.4  Hobb Tanner, Quartermaster: cream military wall tent broadside to the front, its front
                                  wall propped out as an awning on two poles (lantern on the pole), door flaps rolled and
                                  tied in the gable end, broad-arrow branded supply crates, trestle table of draughts
  stand_fieldsmith     5.0 x 3.6  Greta Stonehand, Field Smith: campaign forge on iron legs with a sheet-iron hood and
                                  pipe chimney in the open, anvil on a stump, grindstone; a brown multi-peaked camp fly on
                                  six poles over lashed-pole weapon racks, shields and armour
  station_alchemy      3.2 x 2.0  Alchemy Table: heavy oak bench, copper alembic, retorts, brazier under a flask, reagent
                                  hutch with a little shingled pent roof, rune-etching tray with a sword in it
  station_workbench    3.0 x 1.8  Workbench: tinker's bench with a vice, tool board, sawhorse, powder kegs, scroll
                                  corner, charm-stringing board
  station_forge        3.6 x 3.0  Town forge: stone hearth with a brick hood and chimney, coals, anvil, quench trough,
                                  bellows, tool rack

Conventions (contract): metres, Z-up, origin at the bottom centre of the footprint, front (customer side) = -Y,
recenter=False. Colour comes only from the BH_* material choice (the game ignores vertex tint). BH_Glass is a warm
self-lit lantern pane in game, so it is only used in lanterns; alchemical glassware is BH_Bottle with Gem liquids.
Head-visibility rule: from the npc head (z 1.8) the ray toward the camera rises 1.38 m per metre toward -Y and must
clear every roof. Stations have no npc/customer: sockets use / flame / smoke / light_a only.
"""
import math

import bmesh
from mathutils import Matrix, Vector, noise as mnoise

from kit import *  # noqa
import market_common  # noqa  (registers the extra BH_* materials)
from registry import asset
from assets_props import plank, rivet, flame_tip, sword, helmet, skull
from assets_town2 import keg, hang_lantern
from assets_nature import align_z


# =================================================================================================================
# generic helpers (patterns copied from assets_market_a / assets_market_b)
def along(a, b):
    """Frame with origin at a and local +Z pointing to b. Returns (matrix, length)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    z = d / L
    up = Vector((0, 0, 1)) if abs(z.z) < 0.95 else Vector((1, 0, 0))
    x = up.cross(z).normalized()
    y = z.cross(x)
    M = Matrix(((x.x, y.x, z.x, a.x), (x.y, y.y, z.y, a.y), (x.z, y.z, z.z, a.z), (0, 0, 0, 1)))
    return M, L


def beam(k, a, b, w, h=None, mat="BH_WoodDark", tint=0.6, bev=0.012, over=0.0):
    M, L = along(a, b)
    k.put(box(w, h or w, L + 2 * over, bev=bev), mat, M=M @ T(0, 0, L / 2), tint=tint)


def pole(k, a, b, r, mat="BH_WoodDark", segs=7, tint=0.6, r2=None):
    M, L = along(a, b)
    k.put(cyl(r, L, segs, r2=r2), mat, M=M, tint=tint, smooth=40)


def rope(k, a, b, sag=0.05, r=0.011, n=6, mat="BH_Rope", segs=4):
    a, b = Vector(a), Vector(b)
    pts = []
    for i in range(n + 1):
        t = i / n
        p = a.lerp(b, t)
        p.z -= sag * 4 * t * (1 - t)
        pts.append(p)
    k.put(tube(pts, r, segs), mat, smooth=40)


def lashing(k, M, r=0.07, n=3, rr=0.011):
    for i in range(n):
        k.put(torus(r, rr, 8, 3), "BH_Rope", M=M @ T(0, 0, (i - (n - 1) / 2) * 0.026))


def peg(k, x, y, lean=(0, 0)):
    k.put(box(0.035, 0.035, 0.26, bev=0.006), "BH_Wood", M=TRS(x, y, 0.06, lean[0], lean[1], k.r.uniform(0, 90)), tint=0.6)


def grid(fn, nu, nv):
    t = tb()
    rows = [[t.verts.new(Vector(fn(i / nu, j / nv))) for i in range(nu + 1)] for j in range(nv + 1)]
    for j in range(nv):
        for i in range(nu):
            t.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    return t


def solid(t, th):
    bmesh.ops.recalc_face_normals(t, faces=list(t.faces))
    bmesh.ops.solidify(t, geom=list(t.faces), thickness=th)
    bmesh.ops.recalc_face_normals(t, faces=list(t.faces))
    return t


def sheet(k, fn, nu, nv, mat, th=0.022, smooth=40, tile=1.5):
    k.put(solid(grid(fn, nu, nv), th), mat, smooth=smooth, tile=tile)


def rod(k, p0, p1, r_, mat, segs=6):
    k.put(tube([p0, p1], r_, segs), mat, smooth=40)


def lantern_on_hook(k, x, y, z, s=0.55):
    """Hang a lantern from a ring at (x, y, z); returns a light point just under the lantern (outside its opaque
    glass, so the game's light is not boxed in by the lantern's own mesh)."""
    hang_lantern(k, T(x, y, z), s)
    return (x, y, z - 1.25 * s)


# ---- goods ----------------------------------------------------------------------------------------------------
def potion(k, M, liquid, h=0.2, r=0.055, kind="round", segs=6):
    """Corked draught: glowing liquid body (Gem material), glass neck, cork. Origin at the base."""
    if kind == "round":
        body = [(0.0, 0.0), (r * 0.8, 0.01), (r, r * 0.8), (r * 0.7, r * 1.55), (0.0, r * 1.8)]
        nz = r * 1.72
    elif kind == "tall":
        body = [(0.0, 0.0), (r * 0.8, 0.0), (r * 0.8, h * 0.62), (r * 0.5, h * 0.7), (0.0, h * 0.7)]
        nz = h * 0.68
    else:  # squat
        body = [(0.0, 0.0), (r, 0.0), (r * 1.02, h * 0.35), (r * 0.7, h * 0.5), (0.0, h * 0.5)]
        nz = h * 0.48
    k.put(lathe(body, segs), liquid, M=M, smooth=60, uv="keep")
    nh = max(h - nz - 0.025, 0.03)
    k.put(cyl(r * 0.28, nh, 5, r2=r * 0.24), "BH_Bottle", M=M @ T(0, 0, nz - 0.01), smooth=50)
    k.put(cyl(r * 0.36, 0.03, 5, r2=r * 0.3), "BH_Wood", M=M @ T(0, 0, nz + nh - 0.012), tint=0.7)


def crate_open(k, M, w, d, h, mat="BH_Wood", straw=True):
    th = 0.022
    plank(k, w, d, th, M @ T(0, 0, th / 2), mat=mat, chips=0)
    for sy in (-1, 1):
        plank(k, w, th, h - 0.006, M @ T(0, sy * (d / 2 - th / 2), h / 2), mat=mat, chips=1)
    for sx in (-1, 1):
        plank(k, th, d - 2 * th, h - 0.006, M @ T(sx * (w / 2 - th / 2), 0, h / 2), mat=mat, chips=1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(box(0.035, 0.035, h + 0.01), "BH_WoodDark", M=M @ T(sx * (w / 2 - 0.02), sy * (d / 2 - 0.02), h / 2),
                  tint=0.5)
    if straw:
        t = box(w - 0.05, d - 0.05, 0.02)
        subdiv(t, 1)
        jitter(t, k.r, 0.012)
        k.put(t, "BH_Thatch", M=M @ T(0, 0, h * 0.45), tint=0.9)


def potion_crate(k, M, liquids, nx=4, ny=3, kind="round"):
    r = 0.05
    step = 0.125
    w = nx * step + 0.06
    d = ny * step + 0.06
    crate_open(k, M, w, d, 0.16)
    for i in range(nx):
        for j in range(ny):
            liq = liquids[(i + j * 2) % len(liquids)] if len(liquids) > 1 and (i + j) % 3 == 1 else liquids[0]
            x = -((nx - 1) * step) / 2 + i * step + k.r.uniform(-0.008, 0.008)
            y = -((ny - 1) * step) / 2 + j * step + k.r.uniform(-0.008, 0.008)
            potion(k, M @ TRS(x, y, 0.03, k.r.uniform(-4, 4), k.r.uniform(-4, 4), k.r.uniform(0, 90)), liq, 0.2, r, kind)


def sack(k, M, h=0.62, r=0.24, mat="BH_Cloth", squash=0.8, tint=0.85):
    prof = [(r * 0.8, 0.0), (r, h * 0.14), (r * 1.03, h * 0.45), (r * 0.94, h * 0.72), (r * 0.62, h * 0.88),
            (r * 0.24, h * 0.95), (r * 0.12, h)]
    t = lathe(prof, 9)
    for v in t.verts:
        v.co.y *= squash
    ndisp(t, 5.0, 0.025, k.noff + Vector((M[0][3], M[1][3], 0)))
    k.put(t, mat, M=M, tint=tint, smooth=50)
    k.put(torus(r * 0.22, 0.014, 8, 3), "BH_Rope", M=M @ T(0, 0, h * 0.93))
    t2 = cyl(r * 0.2, 0.1, 6, r2=r * 0.34)
    jitter(t2, k.r, 0.01)
    k.put(t2, mat, M=M @ T(0, 0, h * 0.95), tint=0.8)


def sack_lying(k, M, L=0.7, r=0.2, mat="BH_Cloth"):
    """Filled sack lying on its side along local X, bottom at z=0."""
    t = lathe([(r * 0.5, 0.0), (r * 0.95, L * 0.1), (r, L * 0.5), (r * 0.9, L * 0.85), (r * 0.35, L), (r * 0.15, L * 1.08)],
              8)
    for v in t.verts:
        v.co.y *= 0.7
    ndisp(t, 5.0, 0.02, k.noff + Vector((M[0][3], M[1][3], 0)))
    k.put(t, mat, M=M @ TRS(-L / 2, 0, r * 0.7, 0, 90, 0), smooth=50)
    k.put(torus(r * 0.3, 0.012, 7, 3), "BH_Rope", M=M @ TRS(L / 2 - 0.02, 0, r * 0.7, 0, 90, 0))


def scroll(k, M, L=0.32, r=0.024, ribbon="BH_ClothRed"):
    """Rolled parchment along local X, resting on its side (origin at the bottom centre)."""
    k.put(cyl(r, L, 7), "BH_Paper", M=M @ TRS(-L / 2, 0, r, 0, 90, 0), smooth=40)
    k.put(torus(r + 0.003, 0.006, 7, 3), ribbon, M=M @ TRS(0, 0, r, 0, 90, 0))


def barrel(k, M, H=0.9, R_=0.3, mat="BH_Wood", segs=10, lid=True):
    prof = [(R_ * 0.86, 0.0), (R_ * 0.97, H * 0.22), (R_, H * 0.5), (R_ * 0.97, H * 0.78), (R_ * 0.86, H)]
    k.put(lathe(prof, segs, uv_tile=0.5), mat, M=M, smooth=50, uv="keep")
    for z, rr in ((H * 0.1, 0.9), (H * 0.9, 0.9), (H * 0.5, 1.0)):
        k.put(cyl(R_ * rr + 0.008, 0.035, segs, caps=False), "BH_Iron", M=M @ T(0, 0, z - 0.017), smooth=50)
    if lid:
        k.put(cyl(R_ * 0.82, 0.02, segs), "BH_WoodDark", M=M @ T(0, 0, H - 0.03))


def broad_arrow(k, M, s=0.2, mat="BH_ClothBlack"):
    """The quartermaster's broad-arrow property mark (three strokes, no letters) in the local XZ plane, facing -Y."""
    w = 0.028 * s / 0.2
    k.put(box(w, 0.006, s * 0.85), mat, M=M @ T(0, 0, -s * 0.04))          # shaft
    ang = 32.0
    La = s * 0.5
    for sx in (-1, 1):                                                         # the two barbs of the head (an up arrow)
        c = Vector((sx * math.sin(math.radians(ang)) * La / 2, 0, s * 0.38 - math.cos(math.radians(ang)) * La / 2))
        k.put(box(w, 0.006, La), mat, M=M @ T(*c) @ R(0, -sx * ang, 0))


def ring_mark(k, M, s=0.18, mat="BH_ClothRed"):
    """Painted wheel/cross mark (circle with a cross) in the local XZ plane, facing -Y."""
    k.put(torus(s * 0.5, 0.012, 14, 3), mat, M=M @ R(90, 0, 0))
    k.put(box(s * 0.95, 0.006, 0.022), mat, M=M)
    k.put(box(0.022, 0.006, s * 0.95), mat, M=M)


def supply_crate(k, M, w=0.6, d=0.5, h=0.5, mark="arrow", lid_ajar=False):
    """Closed plank crate with corner battens and a branded mark on the -Y face (origin bottom centre)."""
    r = k.r
    t = box(w - 0.02, d - 0.02, h - 0.02, bev=0.01)
    k.put(t, "BH_Wood", M=M @ T(0, 0, h / 2), tint=r.uniform(0.6, 0.9))
    # battens: vertical at the corners of the long faces, horizontal top/bottom bands
    for sy in (-1, 1):
        for sx in (-1, 1):
            k.put(box(0.06, 0.02, h), "BH_WoodDark", M=M @ T(sx * (w / 2 - 0.03), sy * (d / 2 - 0.0), h / 2))
        for z in (0.04, h - 0.04):
            k.put(box(w - 0.12, 0.02, 0.06), "BH_WoodDark", M=M @ T(0, sy * (d / 2 - 0.0), z))
    for sx in (-1, 1):
        for z in (0.04, h - 0.04):
            k.put(box(0.02, d, 0.06), "BH_WoodDark", M=M @ T(sx * (w / 2), 0, z))
    for sx in (-1, 1):
        rivet(k, M @ TRS(sx * (w / 2 - 0.03), -d / 2 - 0.01, h - 0.04, 90, 0, 0), 0.012)
        rivet(k, M @ TRS(sx * (w / 2 - 0.03), -d / 2 - 0.01, 0.04, 90, 0, 0), 0.012)
    Mf = M @ T(0, -d / 2 - 0.013, h / 2 + 0.01)
    if mark == "arrow":
        broad_arrow(k, Mf, min(h, w) * 0.5)
    elif mark == "ring":
        ring_mark(k, Mf, min(h, w) * 0.45)
    elif mark == "bars":
        for i in range(3):
            k.put(box(0.03, 0.006, h * 0.45), "BH_ClothRed", M=Mf @ T((i - 1) * 0.06, 0, 0) @ R(0, 18, 0))
    if lid_ajar:
        k.put(box(w, d, 0.03, bev=0.006), "BH_Wood", M=M @ T(0.04, 0.06, h + 0.015) @ R(0, 0, 9), tint=0.7)


def ingot_stack(k, M, n_layers=3, mat="BH_Iron"):
    """Criss-crossed stack of bar ingots (origin bottom centre)."""
    for j in range(n_layers):
        for i in range(3):
            rot = 90 if j % 2 else 0
            Mi = M @ R(0, 0, rot) @ T((i - 1) * 0.085, 0, 0.022 + j * 0.045)
            t = box(0.07, 0.26, 0.045)
            for v in t.verts:
                if v.co.z > 0:
                    v.co.x *= 0.75
                    v.co.y *= 0.9
            k.put(t, mat, M=Mi)


def hide_roll(k, M, L=0.5, r=0.09):
    k.put(cyl(r, L, 9), "BH_Leather", M=M @ TRS(-L / 2, 0, r, 0, 90, 0), smooth=40)
    k.put(cyl(r * 0.5, L + 0.01, 7), "BH_Leather", M=M @ TRS(-L / 2 - 0.005, 0, r, 0, 90, 0), tint=0.5)
    for x in (-L * 0.3, L * 0.3):
        k.put(torus(r + 0.004, 0.009, 9, 3), "BH_Rope", M=M @ TRS(x, 0, r, 0, 90, 0))


def lump(k, M, s=(0.06, 0.05, 0.045), mat="BH_StoneDark"):
    """Cheap faceted lump (coal, ore, cobble): a jittered icosahedron, 20 triangles."""
    t = ico(1.0, 1)
    for v in t.verts:
        v.co = Vector((v.co.x * s[0], v.co.y * s[1], v.co.z * s[2]))
    jitter(t, k.r, min(s) * 0.25)
    k.put(t, mat, M=M @ R(0, 0, k.r.uniform(0, 360)))


def rope_coil(k, M, R_=0.14, turns=4):
    for i in range(turns):
        k.put(torus(R_ - i * 0.004, 0.018, 10, 3), "BH_Rope", M=M @ T(0, 0, 0.018 + i * 0.03))


def bedroll(k, M, L=0.7, r=0.12, mat="BH_ClothRed"):
    k.put(cyl(r, L, 10), mat, M=M @ TRS(-L / 2, 0, r, 0, 90, 0), smooth=40)
    k.put(cyl(r * 0.55, L + 0.012, 8), "BH_Cloth", M=M @ TRS(-L / 2 - 0.006, 0, r, 0, 90, 0))
    for x in (-L * 0.28, L * 0.28):
        k.put(torus(r + 0.005, 0.012, 10, 3), "BH_Leather", M=M @ TRS(x, 0, r, 0, 90, 0))


def arrow_sheaf(k, M, n=14, L=0.8):
    """Bundle of arrows standing point-down in a barrel: shafts + fletching fanning out at the top."""
    r = k.r
    for i in range(n):
        a = i * 2.4
        rr = 0.03 + 0.09 * math.sqrt((i + 0.5) / n)
        x, y = math.cos(a) * rr, math.sin(a) * rr
        tilt = Vector((x, y, 1.0)).normalized()
        top = Vector((x * 2.2, y * 2.2, L))
        base = Vector((x * 0.6, y * 0.6, 0.0))
        k.put(tube([base, top], 0.006, 3), "BH_Wood", M=M, tint=0.8)
        d = (top - base).normalized()
        for f in range(2):
            k.put(box(0.004, 0.035, 0.12), "BH_Cloth" if i % 3 else "BH_ClothRed",
                  M=M @ T(*(top - d * 0.08)) @ align_z(d, f * 1.57 + a))


def spear(k, M, L=2.0, head="BH_Iron"):
    k.put(cyl(0.017, L, 6), "BH_Wood", M=M, tint=0.7)
    t = lathe([(0.0, 0.0), (0.03, 0.06), (0.024, 0.16), (0.0, 0.26)], 4)
    for v in t.verts:
        v.co.y *= 0.3
    k.put(t, head, M=M @ T(0, 0, L - 0.02))
    k.put(cyl(0.022, 0.05, 6), head, M=M @ T(0, 0, L - 0.05))


# =================================================================================================================
# 11. stand_quartermaster - Hobb Tanner, Quartermaster of Wyman Outpost
@asset("stand_quartermaster", "market")
def stand_quartermaster(k):
    """4.4 x 3.4. Cream canvas wall tent seen broadside (ridge along X). Its front wall is propped out as an awning
    on two poles (lantern on the left pole); the gable end on the left has its door flaps rolled up and tied.
    Branded supply crates stacked on the right, trestle table of draughts, scrolls and materials in front."""
    r = k.r
    x0, x1 = -2.0, 0.8          # tent gable ends
    yf, yb = -0.12, 1.58        # front / back walls
    yc = (yf + yb) / 2
    zw, zr = 2.3, 3.45          # eave, ridge
    ov = 0.12                   # roof overhang past the walls
    yp, zp = -1.3, 3.2          # awning front pole line / pole top
    cream = "BH_ClothCream"

    def roof_z(y):
        return zr - (zr - zw) * abs(y - yc) / (yc - yf)

    # ---- roof canvas: two slopes, slight belly between the ridge ends, rope-bound hem, reinforcing tapes -------
    for side in (-1, 1):
        ye = (yf - 0.02) if side < 0 else (yb + ov)

        def slope(u, v, ye=ye):
            x = lerp(x0 - 0.1, x1 + 0.1, u)
            y = lerp(yc, ye, v)
            z = zr - (zr - zw) * v * (abs(ye - yc) / (yc - yf))
            z -= 0.06 * math.sin(math.pi * u) * math.sin(math.pi * min(v * 1.1, 1.0))
            z += mnoise.noise(Vector((x * 1.7, y * 1.9, 0.3)) + k.noff) * 0.012
            return (x, y, z)
        sheet(k, slope, 14, 6, cream, 0.025)
        # hem rope along the eave and a darker drip valance
        hem = [slope(i / 10, 1.0) for i in range(11)]
        k.put(tube([Vector(p) - Vector((0, 0, 0.012)) for p in hem], 0.018, 4), "BH_Rope", smooth=40)
        # vertical seams (sewn panels) as thin raised tapes
        for i in range(1, 5):
            u = i / 5
            pts = [Vector(slope(u, j / 6)) + Vector((0, 0, 0.018)) for j in range(7)]
            k.put(tube(pts, 0.009, 3), "BH_Cloth", smooth=40, tint=0.6)
    # ridge tape + ridge pole ends and spindles poking through the canvas
    k.put(tube([(x0 - 0.12, yc, zr + 0.01), (x1 + 0.12, yc, zr + 0.01)], 0.035, 6), "BH_Cloth", smooth=40)
    for x in (x0, x1):
        k.put(cyl(0.022, 0.2, 6), "BH_WoodDark", M=T(x, yc, zr - 0.05))
        k.put(ico(0.03, 1), "BH_WoodDark", M=T(x, yc, zr + 0.16))

    # ---- walls: back wall, right gable (closed), left gable with a door whose flaps are rolled and tied -------
    def back(u, v):
        x = lerp(x0, x1, u)
        z = lerp(0.03, zw - 0.02, v)
        return (x, yb + 0.03 * math.sin(math.pi * u) * (1 - v) + mnoise.noise(Vector((x * 2, 0.5, z * 2)) + k.noff) * 0.01, z)
    sheet(k, back, 10, 4, cream, 0.02)

    def gable(xg, y0, y1, z_top=True):
        def fn(u, v):
            y = lerp(y0, y1, u)
            top = roof_z(y) - 0.02
            z = lerp(0.03, top, v)
            return (xg + 0.02 * math.sin(math.pi * v) * (1 if xg > 0 else -1) * 0.5, y, z)
        return fn
    sheet(k, gable(x1, yf, yb), 8, 5, cream, 0.02)
    door0, door1 = yc - 0.46, yc + 0.46     # left gable door opening
    dz = 2.05
    sheet(k, gable(x0, yf, door0), 3, 4, cream, 0.02)
    sheet(k, gable(x0, door1, yb), 3, 4, cream, 0.02)

    def above_door(u, v):
        y = lerp(door0, door1, u)
        return (x0, y, lerp(dz, roof_z(y) - 0.02, v))
    sheet(k, above_door, 4, 2, cream, 0.02)
    for yy in (door0, door1):     # rolled flaps tied up at the door sides
        k.put(cyl(0.075, dz - 0.35, 8), cream, M=T(x0 - 0.06, yy, 0.35), smooth=40, tint=0.8)
        for z in (0.7, 1.55):
            k.put(torus(0.08, 0.012, 8, 3), "BH_Rope", M=T(x0 - 0.06, yy, z))
    # sod cloth: dark dirt-stained skirt along the bottom of every wall
    for (a, b) in (((x0, yb + 0.03), (x1, yb + 0.03)), ((x1 + 0.02, yf), (x1 + 0.02, yb)), ((x0 - 0.02, yf), (x0 - 0.02, door0)),
                   ((x0 - 0.02, door1), (x0 - 0.02, yb))):
        a, b = Vector((*a, 0.0)), Vector((*b, 0.0))
        d = (b - a)
        mid = (a + b) / 2
        ang = math.degrees(math.atan2(d.y, d.x))
        k.put(box(d.length, 0.03, 0.2), "BH_Cloth", M=T(mid.x, mid.y, 0.1) @ R(0, 0, ang), tint=0.5)

    # ---- frame visible inside: uprights at the gable ends, ridge pole, eave rails ------------------------------
    for x in (x0 + 0.08, x1 - 0.08):
        k.put(cyl(0.05, zr - 0.08, 8), "BH_Wood", M=T(x, yc, 0.0), smooth=40, tint=0.65)
    pole(k, (x0 + 0.02, yc, zr - 0.09), (x1 - 0.02, yc, zr - 0.09), 0.045, "BH_Wood", 7)
    pole(k, (x0 - 0.02, yf + 0.02, zw - 0.04), (x1 + 0.02, yf + 0.02, zw - 0.04), 0.035, "BH_Wood", 6)

    # ---- the awning: front wall laced to the eave, propped out on two poles -----------------------------------
    ax0, ax1 = x0 - 0.05, x1 + 0.05

    def awning(u, v):
        x = lerp(ax0, ax1, u)
        y = lerp(yf - 0.02, yp - 0.1, v)
        z = lerp(zw - 0.03, zp + 0.02, v)
        z -= 0.09 * math.sin(math.pi * u) * math.sin(math.pi * min(v * 1.08, 1.0)) ** 0.7
        z += mnoise.noise(Vector((x * 2.1, y * 2.2, 0.7)) + k.noff) * 0.01
        return (x, y, z)
    sheet(k, awning, 14, 5, cream, 0.022)
    for i in range(1, 4):   # sewn panel seams on the awning
        pts = [Vector(awning(i / 4, j / 5)) + Vector((0, 0, 0.016)) for j in range(6)]
        k.put(tube(pts, 0.008, 3), "BH_Cloth", smooth=40, tint=0.6)
    front_hem = [Vector(awning(i / 12, 1.0)) for i in range(13)]
    k.put(tube([p - Vector((0, 0, 0.01)) for p in front_hem], 0.02, 4), "BH_Rope", smooth=40)
    # scalloped drip edge hanging from the awning front hem (one continuous piece of the same canvas)
    nl = 7

    def drip(u, v):
        p = Vector(awning(u, 1.0))
        f = (u * nl) % 1.0
        depth = 0.05 + 0.08 * math.sqrt(max(0.0, 1.0 - (2.0 * f - 1.0) ** 2))
        return (p.x, p.y - 0.004, p.z - 0.01 - depth * v)
    sheet(k, drip, nl * 6, 1, cream, 0.012, smooth=None)
    # lacing along the eave
    for i in range(8):
        x = lerp(x0 + 0.05, x1 - 0.05, (i + 0.5) / 8)
        k.put(torus(0.03, 0.007, 5, 3), "BH_Rope", M=TRS(x, yf - 0.02, zw - 0.03, 90, 0, 0))
    # poles (round, on flat stones), guy ropes out to the sides and pegs
    for px in (x0 + 0.05, x1 - 0.05):
        k.put(cyl(0.16, 0.06, 7), "BH_Stone", M=T(px, yp, 0.0), tint=0.8)
        k.put(cyl(0.05, zp + 0.14, 8, r2=0.042), "BH_Wood", M=T(px, yp, 0.04), smooth=40, tint=0.65)
        k.put(ico(0.05, 1), "BH_Wood", M=T(px, yp, zp + 0.2))
        lashing(k, T(px, yp, zp - 0.02), 0.06, 2)
        sx = -1 if px < 0 else 1
        gx, gy = (px - 0.2, yp - 0.34) if sx < 0 else (px + 0.04, yp - 0.36)
        rope(k, (px, yp, zp + 0.1), (gx, gy, 0.12), 0.02)
        peg(k, gx, gy, (22, 0))
    # guy ropes at the back eave and gable ends
    for (px, py, gx, gy) in ((x0 + 0.3, yb + ov, x0 + 0.3, 1.62), (x1 - 0.3, yb + ov, x1 - 0.3, 1.62),
                             (x0 - 0.04, yb - 0.2, -2.12, 1.56)):
        rope(k, (px, py, zw - 0.02), (gx, gy, 0.12), 0.02)
        peg(k, gx, gy, (-20, 0))

    # ---- lantern hanging on the left awning pole over the table end ------------------------------------------
    lx = x0 + 0.05
    hz = 2.2
    k.put(tube([(lx + 0.04, yp, hz), (lx + 0.2, yp - 0.02, hz + 0.05), (lx + 0.3, yp - 0.03, hz)], 0.012, 4), "BH_Iron")
    la = lantern_on_hook(k, lx + 0.3, yp - 0.03, hz, 0.5)
    rx = x1 - 0.05          # a second lantern on the right pole, over the crates and the arrow barrel
    k.put(tube([(rx - 0.04, yp, hz), (rx + 0.14, yp - 0.02, hz + 0.05), (rx + 0.28, yp - 0.03, hz)], 0.012, 4), "BH_Iron")
    lb = lantern_on_hook(k, rx + 0.28, yp - 0.03, hz, 0.5)

    # ---- trestle table across the awning's pole line ------------------------------------------------------------
    tx0, tx1 = -1.68, 0.3
    ty0, ty1 = -1.52, -1.04
    tz = 0.84
    tcx, tcy = (tx0 + tx1) / 2, (ty0 + ty1) / 2
    for j in range(3):
        plank(k, tx1 - tx0, (ty1 - ty0) / 3 - 0.008, 0.045, T(tcx, ty0 + (ty1 - ty0) * (j + 0.5) / 3, tz - 0.022),
              tint=(0.6, 0.85))
    for x in (tx0 + 0.22, tx1 - 0.22):          # A-trestles
        for s_ in (-1, 1):
            k.put(box(0.06, 0.06, 0.9), "BH_WoodDark", M=TRS(x, tcy + s_ * 0.13, (tz - 0.05) / 2, s_ * -14, 0, 0))
        k.put(box(0.07, ty1 - ty0 - 0.02, 0.06), "BH_WoodDark", M=T(x, tcy, tz - 0.08))
    k.put(box(tx1 - tx0 - 0.4, 0.05, 0.05), "BH_WoodDark", M=T(tcx, tcy, 0.25))
    # goods: draught crates (red / blue), scroll bundle, ledger + ink, ingots, coin box
    potion_crate(k, TRS(-1.36, tcy + 0.02, tz, 0, 0, 4), ("BH_GemRed",), 3, 3)
    potion_crate(k, TRS(-0.86, tcy + 0.02, tz, 0, 0, -3), ("BH_GemAqua",), 3, 3)
    for i, (dx, dy, rot, rib) in enumerate(((0.0, 0.0, 8, "BH_ClothRed"), (0.02, 0.06, -4, "BH_ClothBlue"),
                                            (0.01, 0.03, 2, "BH_ClothRed"))):
        scroll(k, TRS(-0.4 + dx, tcy - 0.12 + dy, tz + i * 0.042, 0, 0, rot), 0.36, 0.024, rib)
    k.put(box(0.3, 0.22, 0.04, bev=0.006), "BH_Leather", M=TRS(-0.36, tcy + 0.12, tz + 0.02, 0, 0, -10))      # ledger
    k.put(box(0.28, 0.2, 0.01), "BH_Paper", M=TRS(-0.36, tcy + 0.12, tz + 0.045, 0, 0, -10))
    k.put(cyl(0.028, 0.05, 7), "BH_Bottle", M=T(-0.16, tcy + 0.17, tz))
    k.put(tube([(-0.16, tcy + 0.17, tz + 0.04), (-0.19, tcy + 0.1, tz + 0.2)], [0.006, 0.012], 3), "BH_Paper")  # quill
    ingot_stack(k, TRS(0.1, tcy + 0.03, tz, 0, 0, 12), 3)
    k.put(box(0.2, 0.14, 0.1, bev=0.01), "BH_WoodDark", M=TRS(-0.1, tcy - 0.16, tz + 0.05, 0, 0, -6))    # coin box
    for i in range(4):
        k.put(cyl(0.02, 0.007, 8), "BH_Gold", M=T(-0.08 + i * 0.012, tcy - 0.17 + (i % 2) * 0.02, tz + 0.1 + i * 0.006))
    # under the table: sacks and a small keg
    sack(k, TRS(-1.3, tcy + 0.02, 0, 0, 0, 20), 0.5, 0.2)
    sack(k, TRS(-0.9, tcy + 0.05, 0, 0, 0, -30), 0.46, 0.19)
    keg(k, T(-0.15, tcy, 0), 0.46, 0.18)

    # ---- right yard: stepped pyramid of branded crates facing the front, barrels behind, sheaf of arrows ----------
    supply_crate(k, TRS(1.3, -0.05, 0, 0, 0, 2), 0.62, 0.52, 0.52, "arrow")
    supply_crate(k, TRS(1.92, -0.08, 0, 0, 0, -4), 0.5, 0.5, 0.48, "ring")
    supply_crate(k, TRS(1.32, 0.5, 0, 0, 0, -2), 0.62, 0.5, 0.52, "bars")
    supply_crate(k, TRS(1.9, 0.5, 0, 0, 0, 5), 0.52, 0.5, 0.5, "arrow")
    supply_crate(k, TRS(1.34, 0.42, 0.52, 0, 0, 5), 0.58, 0.5, 0.48, "arrow")
    supply_crate(k, TRS(1.88, 0.46, 0.5, 0, 0, -6), 0.5, 0.48, 0.44, "ring")
    supply_crate(k, TRS(1.6, 0.5, 0.98, 0, 0, 3), 0.54, 0.46, 0.42, "arrow", lid_ajar=True)
    bedroll(k, TRS(1.34, 0.02, 0.52, 0, 0, 90), 0.5, 0.11, "BH_ClothRed")
    bedroll(k, TRS(1.34, 0.02, 0.74, 0, 0, 90), 0.48, 0.1, "BH_ClothBlue")
    barrel(k, T(1.3, 1.2, 0), 0.82, 0.27)
    barrel(k, T(1.9, 1.15, 0), 0.9, 0.28)
    rope_coil(k, T(1.3, 1.2, 0.82), 0.13, 3)
    # barrel of arrows at the front right corner
    barrel(k, T(1.85, -0.98, 0), 0.72, 0.25, lid=False)
    arrow_sheaf(k, T(1.85, -0.98, 0.22), 14, 0.9)
    # spear bundle leaning against the crate pyramid's right flank
    for i in range(4):
        spear(k, TRS(2.1 - i * 0.04, 0.95 + i * 0.05, 0.0, 12 - i * 2, -8, 0), 2.05)
    k.put(torus(0.085, 0.012, 8, 3), "BH_Rope", M=TRS(2.0, 0.7, 1.38, 12, -8, 0))
    # ingots on a pallet + hide rolls in front of the crates
    k.put(box(0.55, 0.42, 0.08, bev=0.01), "BH_WoodDark", M=T(1.3, -0.9, 0.04))
    ingot_stack(k, TRS(1.18, -0.9, 0.08, 0, 0, 90), 3)
    hide_roll(k, TRS(1.42, -0.95, 0.08, 0, 0, 80), 0.46, 0.085)

    # ---- inside the tent: cot with bedrolls, sacks, a barrel, draught stock --------------------------------------
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(box(0.05, 0.05, 0.42), "BH_WoodDark", M=T(-1.2 + sx * 0.5, 1.2 + sy * 0.26, 0.21))
    k.put(box(1.1, 0.6, 0.05), "BH_Cloth", M=T(-1.2, 1.2, 0.44))
    for i in range(3):
        bedroll(k, TRS(-1.4 + i * 0.3, 1.2, 0.46, 0, 0, 90), 0.5, 0.1, ("BH_ClothRed", "BH_Cloth", "BH_ClothBlue")[i])
    sack(k, TRS(-0.3, 1.3, 0, 0, 0, 10), 0.6, 0.23)
    sack(k, TRS(0.1, 1.28, 0, 0, 0, -20), 0.56, 0.22)
    sack_lying(k, TRS(-0.1, 0.85, 0, 0, 0, 12), 0.62, 0.2)
    barrel(k, T(0.5, 1.25, 0), 0.8, 0.26)
    supply_crate(k, TRS(-1.45, 0.45, 0, 0, 0, 90), 0.5, 0.45, 0.42, "arrow")
    for i in range(3):                                   # folded blankets on the crate
        k.put(box(0.42 - i * 0.02, 0.34, 0.06, bev=0.02), ("BH_ClothRed", "BH_Cloth", "BH_ClothBlue")[i],
              M=TRS(-1.45, 0.45, 0.45 + i * 0.06, 0, 0, 90 + i * 5))

    # ---- sockets ------------------------------------------------------------------------------------------------
    npc = (-0.62, -0.56, 0.0)
    k.sockets.append(("npc", npc))
    k.sockets.append(("customer", (-0.62, -2.15, 0.0)))
    k.sockets.append(("light_a", la))
    k.sockets.append(("light_b", lb))

    # ---- collision ----------------------------------------------------------------------------------------------
    k.col_box(x1 - x0, yb - 0.25, 2.2, T((x0 + x1) / 2, (0.25 + yb) / 2 + 0.02, 1.1))   # tent body behind the npc zone
    k.col_box(tx1 - tx0, ty1 - ty0, tz, T(tcx, tcy, tz / 2))
    k.col_box(1.15, 1.6, 1.4, T(1.62, 0.55, 0.7))      # crates + barrels
    k.col_box(1.1, 0.5, 0.8, T(1.55, -0.95, 0.4))      # arrows / ingots / hides
    for px in (x0 + 0.05, x1 - 0.05):
        k.col_box(0.2, 0.2, 2.2, T(px, yp, 1.1))
    return dict(recenter=False)


# =================================================================================================================
# smithing helpers
def anvil(k, M, s=1.0, stump=0.55):
    """Anvil (horn toward local -X) on a banded tree stump; origin at the stump's foot. Returns the face height."""
    t = tube([(0, 0, 0), (0, 0, stump * 0.5), (0, 0, stump)], [0.3 * s, 0.27 * s, 0.26 * s], 10)
    ndisp(t, 4.0, 0.012, k.noff + Vector((M[0][3], M[1][3], 0)))
    k.put(t, "BH_Bark", M=M, smooth=35)
    k.put(cyl(0.255 * s, 0.02, 10), "BH_Wood", M=M @ T(0, 0, stump))
    k.put(torus(0.285 * s, 0.012, 12, 3), "BH_Iron", M=M @ T(0, 0, stump * 0.75))
    outline = [(-0.35, 0.0), (0.25, 0.0), (0.25, 0.1), (0.2, 0.12), (0.22, 0.2), (0.3, 0.26), (0.3, 0.3),
               (-0.28, 0.3), (-0.55, 0.28), (-0.55, 0.26), (-0.3, 0.2), (-0.26, 0.12), (-0.35, 0.1)]
    k.put(prism([(x * s, z * s) for x, z in outline], 0.16 * s, bev=0.01), "BH_Iron", M=M @ T(0.05 * s, 0, stump + 0.01))
    k.put(box(0.5 * s, 0.1 * s, 0.012), "BH_Metal", M=M @ T(0.05 * s, 0, stump + 0.01 + 0.3 * s))   # worn bright face
    return stump + 0.01 + 0.3 * s + 0.006


def hammer(k, M, L=0.36, head=0.12):
    """Smith's hammer lying on its side, handle along local +X from the head."""
    k.put(cyl(0.014, L, 6), "BH_Wood", M=M @ TRS(0, 0, 0.022, 0, 90, 0), tint=0.7)
    k.put(box(0.05, head, 0.045, bev=0.006), "BH_Iron", M=M @ T(-0.005, 0, 0.024))


def tongs_hung(k, top, L=0.6):
    """Tongs hanging jaws-down from a hook point."""
    x, y, z = top
    for sx in (-1, 1):
        k.put(tube([(x + sx * 0.012, y, z), (x + sx * 0.004, y, z - L * 0.62), (x + sx * 0.02, y, z - L * 0.8),
                    (x + sx * 0.008, y, z - L)], 0.008, 4), "BH_Iron")


def hammer_hung(k, top, L=0.4):
    x, y, z = top
    k.put(cyl(0.013, L, 6), "BH_Wood", M=T(x, y, z - L), tint=0.7)
    k.put(box(0.13, 0.05, 0.05, bev=0.006), "BH_Iron", M=T(x, y, z - L - 0.02))


def axe(k, M, L=0.9):
    """Bearded axe; handle along local +Z, blade toward local +X."""
    k.put(cyl(0.017, L, 6), "BH_Wood", M=M, tint=0.7)
    pts = [(-0.04, L - 0.03), (0.02, L - 0.02), (0.17, L + 0.04), (0.19, L - 0.05), (0.17, L - 0.19),
           (0.08, L - 0.11), (0.02, L - 0.12), (-0.04, L - 0.11)]
    k.put(prism(pts, 0.03), "BH_Iron", M=M)


def round_shield(k, M, R_=0.34, face="BH_Wood", boss="BH_Iron", paint=None):
    """Round shield lying in local XY (face toward +Z); optional two painted quarters."""
    k.put(cyl(R_, 0.035, 14), face, M=M)
    k.put(torus(R_, 0.016, 16, 3), "BH_Iron", M=M @ T(0, 0, 0.02))
    if paint:
        for a0 in (0, 180):
            pts = [(0.0, 0.0)] + [(math.cos(math.radians(a0 + a)) * R_ * 0.93, math.sin(math.radians(a0 + a)) * R_ * 0.93)
                                  for a in range(0, 91, 15)]
            t = tb()
            vs = [t.verts.new((x, y, 0.0)) for x, y in pts]
            t.faces.new(vs)
            bmesh.ops.solidify(t, geom=list(t.faces), thickness=0.004)
            k.put(t, paint, M=M @ T(0, 0, 0.036))
    k.put(ico(0.065, 1), boss, M=M @ TRS(0, 0, 0.035, s=(1, 1, 0.55)))


def heater_shield(k, M, field, device, dmat, rim="BH_Iron", w=0.48, h=0.62):
    """Heater shield in the XZ plane facing -Y, top edge centred on the origin (after assets_market_b)."""
    pts = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, -h * 0.3)]
    for i in range(1, 7):
        a = math.radians(90 * i / 7)
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
    elif device == "bend":
        k.put(prism([(-w / 2 + 0.01, -0.02), (-w / 2 + 0.13, -0.02), (w / 2 - 0.01, -h * 0.6), (w / 2 - 0.05, -h * 0.75)],
                    0.02), dmat, M=D)


def mail_stand(k, M):
    """Mail shirt and helm on a cross-pole armour tree, origin at the foot."""
    k.put(cyl(0.2, 0.06, 8), "BH_Bark", M=M)
    k.put(cyl(0.035, 1.55, 6), "BH_WoodDark", M=M @ T(0, 0, 0.05))
    k.put(box(0.62, 0.05, 0.05), "BH_WoodDark", M=M @ T(0, 0, 1.42))
    body = lathe([(0.19, 0.0), (0.2, 0.2), (0.17, 0.45), (0.2, 0.62), (0.22, 0.7), (0.1, 0.76), (0.06, 0.78)], 10,
                 cap_bot=False)
    for v in body.verts:
        v.co.y *= 0.7
    k.put(body, "BH_Iron", M=M @ T(0, 0, 0.72), smooth=45)
    for sx in (-1, 1):
        k.put(tube([(sx * 0.2, 0, 1.4), (sx * 0.3, -0.01, 1.2), (sx * 0.31, -0.02, 1.05)], [0.07, 0.06, 0.055], 7),
              "BH_Iron", M=M, smooth=40)
    k.put(box(0.36, 0.26, 0.05), "BH_Leather", M=M @ T(0, 0, 1.02))   # belt
    k.put(cyl(0.02, 0.06, 6), "BH_Brass", M=M @ TRS(0, -0.13, 1.02, 90, 0, 0))
    helmet(k, M @ T(0, 0, 1.55))


def weapon_rack_lashed(k, x0, x1, y, h=1.35):
    """A-frame rack of rough lashed poles: X-trestles at both ends, a top rail and a low foot rail in front."""
    for x in (x0, x1):
        for s_ in (-1, 1):
            a = (x + 0.05 * s_, y - 0.42 * s_, 0.0)
            b = (x - 0.05 * s_, y + 0.18 * s_, h + 0.15)
            k.put(tube([a, b], [0.04, 0.032], 6), "BH_Bark", smooth=40)
        lashing(k, T(x, y - 0.05, h - 0.03) @ R(90, 0, 0), 0.05, 2)
    rod(k, (x0 - 0.12, y - 0.06, h - 0.02), (x1 + 0.12, y - 0.06, h - 0.02), 0.035, "BH_Bark", 6)
    rod(k, (x0, y - 0.38, 0.2), (x1, y - 0.38, 0.2), 0.03, "BH_Bark", 6)
    for x in (x0, x1):
        k.put(torus(0.045, 0.01, 6, 3), "BH_Rope", M=TRS(x, y - 0.38, 0.2, 0, 90, 0))


# =================================================================================================================
# 12. stand_fieldsmith - Greta Stonehand, Field Smith of Wyman Outpost (+ the Field Forge station)
@asset("stand_fieldsmith", "market")
def stand_fieldsmith(k):
    """5.0 x 3.6. Campaign forge in the open on the right: stone-lined iron forge on legs, sheet-iron hood, pipe chimney
    with a rain cap, bellows, anvil on a stump, grindstone, quench tub. On the left a brown camp fly pulled up into
    peaks by eight poles shelters a lashed-pole weapon rack, shields and a mail stand."""
    r = k.r

    # ---- the fly: canvas height field pulled up into peaks by its poles ---------------------------------------
    FX0, FX1, FY0, FY1 = -2.42, 0.42, -1.3, 1.62
    poles = [(-2.3, -1.18, 2.9, 0.42), (-0.95, -1.2, 3.05, 0.42), (0.3, -1.18, 2.9, 0.42),
             (-2.3, 1.5, 2.4, 0.42), (-0.95, 1.52, 2.55, 0.42), (0.3, 1.5, 2.4, 0.42),
             (-1.95, 0.14, 3.38, 0.62), (-0.98, 0.1, 3.68, 0.64), (-0.02, 0.14, 3.38, 0.62)]

    def fly_z(x, y):
        best = -9.0
        for (px, py, h, sl) in poles:
            d = math.hypot(x - px, y - py)
            best = max(best, h - sl * d ** 0.7)
        return best

    def fly(u, v):
        x = lerp(FX0, FX1, u)
        y = lerp(FY0, FY1, v)
        z = fly_z(x, y) + mnoise.noise(Vector((x * 1.6, y * 1.6, 2.0)) + k.noff) * 0.02
        return (x, y, z)
    sheet(k, fly, 24, 20, "BH_Cloth", 0.025, smooth=35)
    # hem rope round the edge, leather reinforcing pads at every pole, a few sewn patches
    hem = [fly(t / 16, 0) for t in range(17)] + [fly(1, t / 14) for t in range(1, 15)] + \
          [fly(1 - t / 16, 1) for t in range(1, 17)] + [fly(0, 1 - t / 14) for t in range(1, 14)]
    k.put(tube([Vector(p) - Vector((0, 0, 0.012)) for p in hem], 0.018, 4, closed=True), "BH_Rope", smooth=40)
    for (px, py, h, sl) in poles:
        k.put(cyl(0.1, 0.05, 7, r2=0.04), "BH_Leather", M=T(px, py, h - 0.04))
    # sewn seams radiating from the two peaks
    for (px, py, h, sl) in poles[6:]:
        for a in range(0, 360, 45):
            pts = []
            for j in range(7):
                d = 0.08 + j * 0.2
                x = px + math.cos(math.radians(a)) * d
                y = py + math.sin(math.radians(a)) * d
                own = h - sl * math.hypot(x - px, y - py) ** 0.7
                if not (FX0 < x < FX1 and FY0 < y < FY1) or fly_z(x, y) > own + 0.03:
                    break
                pts.append(Vector((x, y, fly_z(x, y) + 0.02)))
            if len(pts) > 2:
                k.put(tube(pts, 0.008, 3), "BH_Leather", smooth=40)
    # poles (rough, bark), iron pins through the canvas, guy ropes to pegs
    for (px, py, h, sl) in poles:
        k.put(tube([(px, py, 0.0), (px, py, h + 0.12)], [0.055, 0.042], 7), "BH_Bark", smooth=40)
        k.put(cyl(0.012, 0.12, 4), "BH_Iron", M=T(px, py, h + 0.1))
    for (px, py, h, sl), (gx, gy) in zip(poles[:6], ((-2.44, -1.66), (-1.25, -1.7), (0.02, -1.7), (-2.44, 1.7),
                                                   (-0.95, 1.7), (0.62, 1.7))):
        rope(k, (px, py, h + 0.05), (gx, gy, 0.12), 0.03)
        peg(k, gx, gy, (20 if gy < 0 else -20, 0))

    # ---- under the fly: lashed-pole weapon rack with swords, axes and spears -----------------------------------
    ry = -0.12
    weapon_rack_lashed(k, -2.05, -0.55, ry, 1.3)
    xs = [-1.95 + i * 0.14 for i in range(11)]
    for i, x in enumerate(xs):
        kind = ("sword", "spear", "axe", "sword", "sword", "spear", "axe", "sword", "spear", "sword", "axe")[i]
        foot = (x + r.uniform(-0.02, 0.02), ry - 0.42, 0.0)
        top = Vector((x, ry - 0.1, 1.3))
        d = (top - Vector(foot)).normalized()
        Mw = T(*foot) @ align_z(d, 0.0)
        if kind == "sword":
            sword(k, Mw @ T(0, 0, 0.05) @ R(0, 0, 90), r.uniform(1.0, 1.25))
        elif kind == "spear":
            spear(k, Mw, r.uniform(2.0, 2.3))
        else:
            axe(k, Mw, r.uniform(0.85, 1.0))
    # shields leaning against a log at the front left
    k.put(tube([(-2.3, -0.84, 0.1), (-1.15, -0.9, 0.1)], 0.1, 7), "BH_Bark", smooth=40)
    for i, (x, kind) in enumerate(((-2.08, "round"), (-1.7, "heater"), (-1.32, "round"))):
        if kind == "round":
            round_shield(k, TRS(x, -1.04, 0.36, 72, 0, r.uniform(-8, 8)), 0.34, "BH_Wood",
                         paint=("BH_ClothRed" if i == 0 else "BH_ClothBlue"))
        else:
            heater_shield(k, TRS(x, -1.06, 0.72, -16, 0, 4), "BH_ClothGreen", "chevron", "BH_ClothCream")
    heater_shield(k, TRS(-0.9, -0.92, 0.7, -14, 0, -6), "BH_ClothRed", "bend", "BH_Iron")
    # mail stand, a helm on a stake and a kettle hat on a stake at the right edge of the fly
    mail_stand(k, TRS(-0.2, 0.95, 0.0, 0, 0, -12))
    # armourer's bench under the front edge: helms, a kettle hat, gauntlets, a mail coif
    bcx, bcy, bz_ = -0.1, -0.62, 0.52
    Mb = TRS(bcx, bcy, 0, 0, 0, -6)
    for sx in (-1, 1):
        k.put(cyl(0.13, bz_ - 0.05, 8), "BH_Bark", M=Mb @ T(sx * 0.33, 0, 0), smooth=35)
    for j in range(2):
        plank(k, 0.95, 0.17, 0.05, Mb @ T(0, (j - 0.5) * 0.18, bz_ - 0.025), tint=(0.6, 0.8))
    helmet(k, Mb @ T(-0.28, 0.02, bz_))
    k.put(lathe([(0.0, 0.2), (0.1, 0.19), (0.15, 0.1), (0.16, 0.0)], 10), "BH_Iron", M=Mb @ T(0.05, 0.03, bz_ + 0.02),
          smooth=45)                                                                    # kettle hat
    k.put(torus(0.2, 0.02, 14, 3), "BH_Iron", M=Mb @ T(0.05, 0.03, bz_ + 0.03))
    for i in range(2):                                                                  # gauntlets
        k.put(box(0.1, 0.18, 0.06, bev=0.02), "BH_Iron", M=Mb @ TRS(0.32 + i * 0.1, -0.02, bz_ + 0.03, 0, 0, 10 - i * 25))
        k.put(cyl(0.05, 0.1, 7, r2=0.06), "BH_Leather", M=Mb @ TRS(0.32 + i * 0.1, 0.08, bz_ + 0.05, -80, 0, 10 - i * 25))
    # chest of arrows, a keg and a bedroll at the back
    supply_crate(k, TRS(-1.9, 1.15, 0, 0, 0, 4), 0.6, 0.45, 0.45, "arrow")
    keg(k, T(-1.3, 1.25, 0), 0.6, 0.22)
    bedroll(k, TRS(-0.7, 1.28, 0, 0, 0, 5), 0.7, 0.13, "BH_ClothGreen")

    # ---- the forge (out in the open, right) ---------------------------------------------------------------------
    fx, fy = 1.45, 1.08
    fw, fd = 1.0, 0.66
    fz = 0.78
    for sx in (-1, 1):
        for sy in (-1, 1):
            rod(k, (fx + sx * (fw / 2 - 0.02), fy + sy * (fd / 2 - 0.02), fz),
                (fx + sx * (fw / 2 + 0.06), fy + sy * (fd / 2 + 0.05), 0.0), 0.028, "BH_Iron", 5)
    rod(k, (fx - fw / 2 - 0.02, fy - fd / 2, 0.3), (fx + fw / 2 + 0.02, fy - fd / 2, 0.3), 0.018, "BH_Iron", 4)
    k.put(box(fw, fd, 0.24, bev=0.01), "BH_Iron", M=T(fx, fy, fz + 0.12))                 # iron pan
    for sx in (-1, 1):                                                                     # stone lining rim
        k.put(box(0.2, fd + 0.04, 0.12, bev=0.02), "BH_Stone", M=T(fx + sx * (fw / 2 - 0.1), fy, fz + 0.3), tint=0.8)
    for sy in (-1, 1):
        k.put(box(fw - 0.36, 0.14, 0.12, bev=0.02), "BH_Stone", M=T(fx, fy + sy * (fd / 2 - 0.07), fz + 0.3), tint=0.8)
    cz = fz + 0.3
    k.put(box(fw - 0.4, fd - 0.28, 0.04), "BH_StoneDark", M=T(fx, fy, cz))
    for i in range(14):
        a = r.uniform(0, 6.28)
        d = r.uniform(0, 0.16)
        lump(k, T(fx + math.cos(a) * d * 1.4, fy + math.sin(a) * d * 0.7, cz + 0.04), (0.06, 0.05, 0.04),
             "BH_Coals" if i % 3 else "BH_StoneDark")
    # sheet-iron hood on two straps, pipe chimney with a rain cap
    hz0, hz1 = 1.5, 1.95
    hood = lathe([(0.52, 0.0), (0.14, hz1 - hz0)], 4, cap_bot=False, cap_top=False, angle0=math.pi / 4)
    for v in hood.verts:
        v.co.y *= 0.75
    k.put(solid(hood, 0.02), "BH_Iron", M=T(fx, fy + 0.05, hz0), smooth=None)
    for sx in (-1, 1):
        rod(k, (fx + sx * 0.36, fy + fd / 2 - 0.02, fz + 0.24), (fx + sx * 0.3, fy + 0.25, hz0 + 0.05), 0.015, "BH_Iron", 4)
    pipe_top = 3.7
    k.put(cyl(0.1, pipe_top - hz1 + 0.05, 10), "BH_Iron", M=T(fx, fy + 0.05, hz1 - 0.05), smooth=40)
    for z in (2.4, 3.05):
        k.put(torus(0.105, 0.014, 10, 3), "BH_Iron", M=T(fx, fy + 0.05, z))
    for a in (0, 120, 240):
        c_, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        rod(k, (fx + c_ * 0.09, fy + 0.05 + s_ * 0.09, pipe_top - 0.02),
            (fx + c_ * 0.12, fy + 0.05 + s_ * 0.12, pipe_top + 0.1), 0.008, "BH_Iron", 3)
    k.put(cyl(0.24, 0.12, 10, r2=0.02), "BH_Iron", M=T(fx, fy + 0.05, pipe_top + 0.1), smooth=40)
    # a stay wire from the pipe down to a peg keeps the chimney upright
    rope(k, (fx, fy + 0.05, 3.2), (2.36, 1.66, 0.1), 0.02, 0.006, mat="BH_Iron")
    peg(k, 2.36, 1.66, (-15, 15))
    # bellows on a trestle at the right end, nozzle into the firepot, lever with a chain
    bx, by, bz = fx + fw / 2 + 0.3, fy, 0.72
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(box(0.05, 0.05, bz), "BH_WoodDark", M=T(bx + sx * 0.18, by + sy * 0.2, bz / 2))
    k.put(box(0.45, 0.5, 0.05), "BH_WoodDark", M=T(bx, by, bz))
    bel = [(-0.2, 0.0), (0.2, 0.0), (0.26, 0.2), (0.2, 0.36), (0.0, 0.42), (-0.14, 0.36), (-0.2, 0.2)]
    for dz in (0.04, 0.2):
        k.put(prism(bel, 0.03), "BH_Wood", M=T(bx + 0.2, by, bz + dz) @ R(0, 0, -90) @ R(90, 0, 0))
    leather = lathe([(0.19, 0.0), (0.23, 0.07), (0.19, 0.14)], 8)
    k.put(leather, "BH_Leather", M=T(bx, by, bz + 0.05), smooth=40)
    rod(k, (bx - 0.2, by, bz + 0.12), (fx + 0.25, fy - 0.05, cz + 0.05), 0.03, "BH_Iron", 6)       # tuyere pipe
    rod(k, (bx + 0.15, by + 0.3, bz), (bx + 0.15, by + 0.3, 1.55), 0.025, "BH_WoodDark", 5)          # lever post
    rod(k, (bx + 0.15, by + 0.4, 1.52), (bx + 0.1, by - 0.35, 1.62), 0.02, "BH_Wood", 5)            # lever arm
    rope(k, (bx + 0.12, by + 0.05, 1.55), (bx + 0.02, by + 0.02, bz + 0.26), 0.0, 0.006, n=2, mat="BH_Iron")
    # tongs + hammers hanging from a bar on the forge's front edge
    rod(k, (fx - 0.45, fy - fd / 2 - 0.06, fz + 0.2), (fx + 0.45, fy - fd / 2 - 0.06, fz + 0.2), 0.012, "BH_Iron", 4)
    for i, x in enumerate((-0.35, -0.2, -0.05, 0.12, 0.3)):
        if i % 2 == 0:
            tongs_hung(k, (fx + x, fy - fd / 2 - 0.07, fz + 0.19), 0.55)
        else:
            hammer_hung(k, (fx + x, fy - fd / 2 - 0.07, fz + 0.19), 0.34)
    # coal box and quench tub beside the forge
    crate_open(k, TRS(0.85, 1.25, 0, 0, 0, -6), 0.5, 0.4, 0.3, straw=False)
    for i in range(14):
        lump(k, T(0.85 + r.uniform(-0.15, 0.15), 1.25 + r.uniform(-0.1, 0.1), 0.26 + r.uniform(0, 0.06)),
             (0.07, 0.06, 0.05), "BH_StoneDark")
    tub_x, tub_y = 2.14, -0.05
    k.put(lathe([(0.3, 0.0), (0.33, 0.45), (0.3, 0.45), (0.27, 0.04), (0.0, 0.04)], 10), "BH_Wood", M=T(tub_x, tub_y, 0),
          smooth=40)
    for z in (0.08, 0.38):
        k.put(torus(0.3 + z * 0.06, 0.012, 10, 3), "BH_Iron", M=T(tub_x, tub_y, z))
    k.put(cyl(0.29, 0.01, 10), "BH_Iron", M=T(tub_x, tub_y, 0.34))        # dark quench water
    k.put(tube([(tub_x - 0.1, tub_y - 0.05, 0.39), (tub_x + 0.25, tub_y + 0.05, 0.75)], 0.012, 4), "BH_Iron")

    # ---- anvil on a stump, work in progress on it ---------------------------------------------------------------
    ax_, ay_ = 1.22, -0.55
    face = anvil(k, TRS(ax_, ay_, 0, 0, 0, 8), 1.0, 0.5)
    sword(k, TRS(ax_, ay_, face + 0.012, 0, 0, 8) @ T(-0.52, 0.0, 0) @ R(0, 90, 0) @ R(0, 0, 90), 0.8)
    hammer(k, TRS(ax_ + 0.25, ay_ + 0.02, face - 0.005, 0, 0, 30), 0.36)
    # grindstone on a frame (front right)
    gx, gy = 2.05, -0.95
    k.put(cyl(0.34, 0.09, 16), "BH_Stone", M=TRS(gx, gy, 0.62, 0, 90, 0) @ T(0, 0, -0.045), smooth=30)
    rod(k, (gx - 0.3, gy, 0.62), (gx + 0.34, gy, 0.62), 0.02, "BH_Iron", 5)
    rod(k, (gx + 0.34, gy, 0.62), (gx + 0.34, gy - 0.16, 0.62), 0.014, "BH_Iron", 4)
    rod(k, (gx + 0.34, gy - 0.16, 0.62), (gx + 0.44, gy - 0.16, 0.62), 0.02, "BH_Wood", 5)
    for sx in (-1, 1):
        for sy in (-1, 1):
            rod(k, (gx + sx * 0.12, gy, 0.62), (gx + sx * 0.18, gy + sy * 0.3, 0.0), 0.03, "BH_WoodDark", 5)
    k.put(box(0.36, 0.5, 0.05), "BH_WoodDark", M=T(gx, gy, 0.22))
    k.put(lathe([(0.16, 0.0), (0.18, 0.12), (0.16, 0.12), (0.14, 0.02), (0.0, 0.02)], 8), "BH_Wood",
          M=T(gx, gy, 0.245), smooth=40)
    k.put(cyl(0.16, 0.01, 8), "BH_Iron", M=T(gx, gy, 0.32))

    # ---- lantern: hung from the front-middle fly pole on an iron arm, over the shields and the rack ------------
    px, py, ph, _ = poles[1]
    hz = 2.45
    k.put(tube([(px, py + 0.04, hz), (px + 0.02, py + 0.22, hz + 0.06), (px + 0.03, py + 0.4, hz)], 0.012, 4), "BH_Iron")
    la = lantern_on_hook(k, px + 0.03, py + 0.4, hz, 0.5)

    # ---- sockets ------------------------------------------------------------------------------------------------
    k.sockets.append(("npc", (1.35, 0.2, 0.0)))
    k.sockets.append(("customer", (0.8, -1.5, 0.0)))
    k.sockets.append(("use", (1.25, -1.3, 0.0)))
    k.sockets.append(("flame", (fx, fy, cz + 0.12)))
    k.sockets.append(("smoke", (fx, fy + 0.05, pipe_top + 0.25)))
    k.sockets.append(("light_a", la))

    # ---- collision ----------------------------------------------------------------------------------------------
    k.col_box(fw + 0.2, fd + 0.15, 1.2, T(fx, fy, 0.6))                  # forge
    k.col_box(0.55, 0.6, 1.0, T(bx, by, 0.5))                          # bellows
    k.col_box(0.6, 0.6, 0.8, T(ax_, ay_, 0.4))                         # anvil
    k.col_box(0.7, 0.7, 0.9, T(gx, gy, 0.45))                          # grindstone
    k.col_box(0.66, 0.66, 0.5, T(tub_x, tub_y, 0.25))                  # quench tub
    k.col_box(0.55, 0.45, 0.35, T(0.85, 1.25, 0.17))                   # coal box
    k.col_box(1.75, 0.95, 1.4, T(-1.3, ry - 0.15, 0.7))                # weapon rack
    k.col_box(1.3, 0.4, 0.8, T(-1.75, -0.7, 0.4))                      # shields
    k.col_box(1.9, 0.55, 0.8, T(-1.3, 1.2, 0.4))                       # chest / keg / bedroll
    k.col_box(0.5, 0.5, 1.7, T(-0.2, 0.95, 0.85))                      # mail stand
    k.col_box(0.95, 0.45, 0.6, T(bcx, bcy, 0.3))                       # armourer's bench
    for (px, py, h, sl) in poles:
        k.col_box(0.14, 0.14, 2.2, T(px, py, 1.1))
    return dict(recenter=False)


def bomb(k, M, r=0.07):
    k.put(ico(r, 2), "BH_Iron", M=M @ T(0, 0, r), smooth=50)
    k.put(cyl(r * 0.35, 0.03, 6), "BH_Brass", M=M @ T(0, 0, r * 1.85))
    k.put(tube([(0, 0, r * 2.1), (0.01, 0.01, r * 2.5), (0.035, 0.0, r * 2.75)], 0.007, 3), "BH_Rope", M=M)


def herb_bundle(k, top, L=0.3, mat="BH_Moss", string=0.1):
    """Bunch of herbs hung upside down from `top` on a short string (after assets_market_b)."""
    r = k.r
    x, y, z = top
    k.put(tube([(x, y, z), (x, y, z - string)], 0.006, 4), "BH_Rope")
    t = cyl(0.022, L, 6, r2=r.uniform(0.06, 0.085))
    subdiv(t, 1)
    ndisp(t, 9.0, 0.018, k.noff + Vector((x, y, z)))
    jitter(t, r, 0.008)
    zt = z - string
    k.put(t, mat, M=T(x, y, zt) @ R(180 + r.uniform(-6, 6), r.uniform(-6, 6), r.uniform(0, 90)), smooth=35)
    k.put(torus(0.026, 0.008, 6, 3), "BH_Rope", M=T(x, y, zt - 0.04))


# =================================================================================================================
# station helpers
def saw_outline(L=0.48, h0=0.1, h1=0.14, teeth=14):
    """Hand-saw blade in the XZ plane: straight back, toothed lower edge (heel toward +X)."""
    pts = [(L / 2, h1), (-L / 2, h0 * 0.8)]
    for i in range(teeth + 1):
        x = -L / 2 + L * i / teeth
        pts.append((x, 0.0 if i % 2 == 0 else 0.018))
    return pts


def trestle_bench(k, x0, x1, y0, y1, z, th=0.09, leg=0.13, mat="BH_WoodDark", planks=3, stretcher=0.18):
    """Heavy plank bench top on four square legs with low stretchers."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for j in range(planks):
        plank(k, x1 - x0, (y1 - y0) / planks - 0.008, th, T(cx, y0 + (y1 - y0) * (j + 0.5) / planks, z - th / 2),
              mat=mat, tint=(0.6, 0.85))
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(box(leg, leg, z - th, bev=0.012), mat, M=T(cx + sx * ((x1 - x0) / 2 - 0.12), cy + sy * ((y1 - y0) / 2 - 0.08),
                                                           (z - th) / 2))
        k.put(box(0.07, y1 - y0 - 0.16, 0.08), mat, M=T(cx + sx * ((x1 - x0) / 2 - 0.12), cy, stretcher))
    k.put(box(x1 - x0 - 0.24, 0.07, 0.08), mat, M=T(cx, cy + ((y1 - y0) / 2 - 0.08), stretcher))


def flask(k, M, liquid, r=0.07, neck=0.12, fill=0.6):
    """Round-bottomed glass flask: glowing liquid body, dark glass neck with a lip. Origin at the bottom."""
    k.put(ico(r, 2), liquid, M=M @ T(0, 0, r) @ S(1, 1, 0.95), smooth=60)
    k.put(cyl(r * 0.28, neck, 6), "BH_Bottle", M=M @ T(0, 0, r * 1.7))
    k.put(torus(r * 0.3, 0.006, 6, 3), "BH_Bottle", M=M @ T(0, 0, r * 1.7 + neck))


def retort(k, M, liquid, r=0.07):
    """Retort: liquid bulb and a long glass neck bending down to local +X. Origin at the bulb's foot."""
    k.put(ico(r, 2), liquid, M=M @ T(0, 0, r), smooth=60)
    k.put(tube([(0.0, 0.0, r * 1.6), (0.02, 0.0, r * 2.4), (0.12, 0.0, r * 2.6), (0.3, 0.0, r * 1.2)],
               [r * 0.34, r * 0.26, r * 0.18, r * 0.12], 5), "BH_Bottle", M=M, smooth=50)


def jar(k, M, kind, mat=None):
    """Shelf stock: 'crock' (stoneware with cloth lid), 'bottle' (dark glass), 'potion' (glowing), 'pot' (wood box)."""
    r = k.r
    if kind == "crock":
        h = r.uniform(0.12, 0.2)
        rr = r.uniform(0.05, 0.075)
        k.put(lathe([(rr * 0.8, 0.0), (rr, h * 0.35), (rr * 0.8, h), (0.0, h)], 6), mat or "BH_Bone", M=M, smooth=50)
        k.put(cyl(rr * 0.82, 0.02, 6), "BH_Cloth", M=M @ T(0, 0, h - 0.008))
    elif kind == "bottle":
        h = r.uniform(0.18, 0.26)
        rr = r.uniform(0.035, 0.05)
        k.put(lathe([(rr, 0.0), (rr, h * 0.55), (rr * 0.35, h * 0.75), (rr * 0.3, h), (0.0, h)], 5), mat or "BH_Bottle",
              M=M, smooth=50)
    elif kind == "potion":
        potion(k, M, mat or "BH_GemGreen", r.uniform(0.15, 0.2), r.uniform(0.04, 0.05), r.choice(("round", "tall", "squat")),
               segs=5)
    else:
        k.put(box(0.12, 0.1, 0.08, bev=0.01), mat or "BH_Wood", M=M @ T(0, 0, 0.04))


def shelf_row(k, x0, x1, y, z, kinds, mats=None):
    r = k.r
    x = x0
    i = 0
    while x < x1 - 0.06:
        kind = kinds[i % len(kinds)]
        mat = mats[i % len(mats)] if mats else None
        jar(k, T(x + 0.05, y + r.uniform(-0.03, 0.03), z), kind, mat)
        x += r.uniform(0.13, 0.19)
        i += 1


def small_brazier(k, M, r_=0.12):
    """Little iron fire bowl on three legs with glowing coals; returns the flame point (local)."""
    k.put(lathe([(0.03, 0.0), (r_ * 0.8, 0.04), (r_, 0.09), (r_ * 0.9, 0.09), (0.0, 0.05)], 9), "BH_Iron",
          M=M @ T(0, 0, 0.1), smooth=40)
    for a in (30, 150, 270):
        c_, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        k.put(tube([(c_ * r_ * 0.5, s_ * r_ * 0.5, 0.12), (c_ * r_ * 0.9, s_ * r_ * 0.9, 0.0)], 0.009, 3), "BH_Iron", M=M)
    for i in range(6):
        a = i * 1.1
        d = 0.03 + (i % 3) * 0.025
        lump(k, M @ T(math.cos(a) * d, math.sin(a) * d, 0.17), (0.03, 0.028, 0.02), "BH_Coals")
    return (0.0, 0.0, 0.22)


def shingle_pent(k, x0, x1, y0, y1, z_back, z_front, mat="BH_Wood", rows=3):
    """Small pent roof of overlapping shingle strips, back (y1) high, front (y0) low."""
    r = k.r
    for j in range(rows):
        f0 = j / rows
        f1 = (j + 1.25) / rows
        ya, yb_ = lerp(y1, y0, f0), lerp(y1, y0, min(f1, 1.05))
        za, zb = lerp(z_back, z_front, f0), lerp(z_back, z_front, min(f1, 1.05))
        n = int((x1 - x0) / 0.16)
        for i in range(n):
            x = x0 + (i + 0.5) * (x1 - x0) / n + (0.05 if j % 2 else 0)
            if x > x1:
                continue
            L = math.hypot(ya - yb_, za - zb)
            ang = math.degrees(math.atan2(za - zb, ya - yb_))
            t = box((x1 - x0) / n - 0.012, L, 0.022)
            jitter(t, r, 0.003)
            k.put(t, mat, M=T(x, (ya + yb_) / 2, (za + zb) / 2 + 0.014 * j) @ R(ang, 0, 0), tint=r.uniform(0.5, 0.8))


def rune_marks(k, M, n, length, r_=0.012, mat="BH_Rune"):
    """Row of small glowing glyph marks (dots, ticks and little rings - never letters) along local +X."""
    for i in range(n):
        x = (i - (n - 1) / 2) * length / max(n - 1, 1)
        g = i % 3
        if g == 0:
            k.put(torus(r_ * 1.4, r_ * 0.35, 6, 3), mat, M=M @ T(x, 0, 0))
        elif g == 1:
            k.put(box(r_ * 0.6, r_ * 3.0, 0.004), mat, M=M @ T(x, 0, 0) @ R(0, 0, 35))
        else:
            k.put(cyl(r_ * 0.7, 0.004, 5), mat, M=M @ T(x, 0, 0))


# =================================================================================================================
# 13. station_alchemy - Alchemy Table (brewing and weapon Enchantment)
@asset("station_alchemy", "market")
def station_alchemy(k):
    """3.2 x 2.0. Heavy oak bench: copper alembic, retorts and a flask over a small brazier, rune-etching tray with a
    sword; reagent hutch at the back under a little shingled pent roof with drying herbs and a lantern."""
    r = k.r
    bx0, bx1, by0, by1, bz = -1.35, 1.35, -0.42, 0.3, 0.92
    trestle_bench(k, bx0, bx1, by0, by1, bz, 0.1, 0.14, "BH_WoodDark")
    # lower shelf between the legs
    plank(k, bx1 - bx0 - 0.3, by1 - by0 - 0.2, 0.04, T(0, (by0 + by1) / 2, 0.3), mat="BH_Wood", tint=(0.5, 0.7))

    # ---- reagent hutch on the back edge ----------------------------------------------------------------------
    hy0, hy1 = 0.42, 0.78
    hyc = (hy0 + hy1) / 2
    top = 2.25
    for sx in (-1, 1):
        k.put(box(0.09, hy1 - hy0, top, bev=0.01), "BH_WoodDark", M=T(sx * 1.3, hyc, top / 2))
    n = 6
    for i in range(n):
        x = -1.25 + 2.5 * (i + 0.5) / n
        k.put(box(2.5 / n - 0.012, 0.03, top - 0.3), "BH_Wood", M=T(x, hy1 - 0.02, 0.3 + (top - 0.3) / 2))
    shelves = (0.62, 1.2, 1.62, 2.02)
    for z in shelves:
        plank(k, 2.52, hy1 - hy0 - 0.04, 0.035, T(0, hyc - 0.02, z), mat="BH_Wood", tint=(0.6, 0.8))
    k.put(box(2.5, 0.05, 0.1), "BH_WoodDark", M=T(0, hy0 - 0.02, 0.62 + 0.05))
    shelf_row(k, -1.2, 1.2, hyc - 0.03, 0.64, ("crock", "crock", "pot", "bottle"))
    shelf_row(k, -1.2, 1.2, hyc - 0.03, 1.22, ("potion", "bottle", "potion", "crock"),
              ("BH_GemGreen", "BH_Bottle", "BH_GemAqua", None, "BH_GemViolet", "BH_Bottle", "BH_GemAmber"))
    shelf_row(k, -1.2, 0.5, hyc - 0.03, 1.64, ("bottle", "potion", "potion", "crock"),
              ("BH_Bottle", "BH_GemAqua", "BH_GemGreen", None))
    for i, x in enumerate((-1.1, -0.75, -0.3, 0.2, 0.55)):          # top shelf: a few big stoneware crocks
        jar(k, T(x, hyc - 0.02, 2.04), "crock", ("BH_Bone", "BH_Leather", "BH_Bone", "BH_WoodDark", "BH_Bone")[i])
    # a skull and a crystal cluster among the stock, books lying on the middle shelf
    skull(k, TRS(0.85, hyc - 0.04, 1.73, 0, 0, 12), 0.9)
    for i in range(3):
        k.put(box(0.2, 0.26, 0.05), ("BH_ClothRed", "BH_Leather", "BH_ClothBlue")[i],
              M=TRS(0.72 + 0.02 * i, hyc - 0.02, 1.665 + i * 0.05, 0, 0, -8 + i * 7))
    # pent roof of shingles on brackets, drying herbs along its front edge
    for sx in (-1, 1):
        beam(k, (sx * 1.3, hy1, top), (sx * 1.3, hy0 - 0.3, top - 0.12), 0.08, 0.08)
        beam(k, (sx * 1.3, hy0 - 0.25, top - 0.12), (sx * 1.3, hy0 + 0.02, top - 0.45), 0.06, 0.06)
    k.put(box(2.8, 0.08, 0.08), "BH_WoodDark", M=T(0, hy0 - 0.26, top - 0.13))
    shingle_pent(k, -1.45, 1.45, hy0 - 0.38, hy1 + 0.1, top + 0.08, top - 0.12, "BH_Wood", 3)
    for i, x in enumerate((-1.15, -0.7, 0.35)):
        herb_bundle(k, (x, hy0 - 0.26, top - 0.17), 0.28, ("BH_Moss", "BH_Thatch", "BH_ClothGreen")[i])
    # lantern hanging from the right end of the front roof bar
    la = lantern_on_hook(k, 0.95, hy0 - 0.26, top - 0.17, 0.45)

    # ---- on the bench, left: copper alembic on a stone slab brazier, arm to a receiver flask ------------------
    ax_, ay_ = -0.95, -0.02
    k.put(box(0.4, 0.4, 0.05, bev=0.01), "BH_Stone", M=T(ax_, ay_, bz + 0.025))
    k.put(box(0.34, 0.34, 0.2, bev=0.01), "BH_Brick", M=T(ax_, ay_, bz + 0.15))
    k.put(box(0.16, 0.06, 0.11), "BH_StoneDark", M=T(ax_, ay_ - 0.15, bz + 0.12))      # fire mouth
    for i in range(3):
        lump(k, T(ax_ - 0.04 + i * 0.04, ay_ - 0.17, bz + 0.08), (0.028, 0.02, 0.018), "BH_Coals")
    k.put(box(0.36, 0.36, 0.03), "BH_Iron", M=T(ax_, ay_, bz + 0.265))
    pz = bz + 0.28
    k.put(lathe([(0.0, 0.0), (0.1, 0.02), (0.14, 0.09), (0.13, 0.18), (0.08, 0.23), (0.07, 0.26), (0.0, 0.26)], 10),
          "BH_Copper", M=T(ax_, ay_, pz), smooth=40)
    k.put(lathe([(0.075, 0.0), (0.1, 0.06), (0.09, 0.14), (0.04, 0.2), (0.02, 0.26), (0.0, 0.26)], 10), "BH_Copper",
          M=T(ax_, ay_, pz + 0.25), smooth=40)
    rx, ry_ = -0.45, -0.1
    k.put(tube([(ax_ + 0.02, ay_, pz + 0.47), (ax_ + 0.18, ay_ - 0.02, pz + 0.45), (rx - 0.05, ry_, pz + 0.22),
                (rx, ry_, bz + 0.2)], [0.02, 0.016, 0.012, 0.01], 6), "BH_Copper", smooth=40)
    flask(k, T(rx, ry_, bz), "BH_GemGreen", 0.075, 0.1)
    # ---- centre: flask of blue liquid on a tripod over the brazier (the station's flame), retorts rack ----------
    fx, fy = -0.05, -0.1
    k.put(box(0.34, 0.34, 0.04, bev=0.01), "BH_Stone", M=T(fx, fy, bz + 0.02))
    fl = small_brazier(k, T(fx, fy, bz + 0.04), 0.12)
    for a in (90, 210, 330):
        c_, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        k.put(tube([(fx + c_ * 0.15, fy + s_ * 0.15, bz + 0.04), (fx + c_ * 0.1, fy + s_ * 0.1, bz + 0.4)], 0.008, 3),
              "BH_Iron")
    k.put(torus(0.1, 0.009, 10, 3), "BH_Iron", M=T(fx, fy, bz + 0.4))
    flask(k, T(fx, fy, bz + 0.33), "BH_GemAqua", 0.09, 0.14)
    for i, (dx, liq) in enumerate(((0.3, "BH_GemGreen"), (0.48, "BH_GemAqua"))):
        k.put(cyl(0.06, 0.02, 8), "BH_Wood", M=T(fx + dx, fy + 0.12, bz))
        retort(k, TRS(fx + dx, fy + 0.12, bz + 0.02, 0, 0, -120 + i * 30), liq, 0.06)
    # mortar and pestle, a recipe book with a candle
    k.put(lathe([(0.06, 0.0), (0.08, 0.05), (0.075, 0.09), (0.06, 0.09), (0.05, 0.03), (0.0, 0.03)], 8), "BH_Stone",
          M=T(0.15, -0.3, bz), smooth=40)
    k.put(cyl(0.012, 0.16, 5), "BH_Wood", M=TRS(0.15, -0.3, bz + 0.06, 20, 10, 0))
    k.put(box(0.34, 0.24, 0.03), "BH_Leather", M=TRS(-0.55, -0.28, bz + 0.015, 0, 0, 8))
    for sx in (-1, 1):
        k.put(box(0.155, 0.22, 0.012), "BH_Paper", M=TRS(-0.55, -0.28, bz + 0.035, 0, sx * 5, 8) @ T(sx * 0.08, 0, 0))
    k.put(cyl(0.025, 0.12, 7), "BH_Candle", M=T(-0.82, -0.3, bz))
    flame_tip(k, T(-0.82, -0.3, bz + 0.135), 0.035)

    # ---- right: the rune-etching tray with a sword laid in it ---------------------------------------------------
    tx, ty = 0.88, -0.08
    Mt = TRS(tx, ty, bz, 0, 0, -4)
    k.put(box(0.34, 1.02, 0.04, bev=0.006), "BH_Slate", M=Mt @ T(0, 0, 0.02) @ R(0, 0, 90))
    for sx in (-1, 1):
        k.put(box(1.02, 0.03, 0.06), "BH_Copper", M=Mt @ T(0, sx * 0.17, 0.03))
        k.put(box(0.03, 0.34, 0.06), "BH_Copper", M=Mt @ T(sx * 0.51, 0, 0.03))
    sword(k, Mt @ T(-0.44, 0.0, 0.052) @ R(0, 90, 0) @ R(0, 0, 90), 0.9)
    k.put(box(0.5, 0.012, 0.004), "BH_Rune", M=Mt @ T(0.08, 0.0, 0.066))              # the glowing etched fuller
    rune_marks(k, Mt @ T(0.1, 0.0, 0.066), 7, 0.36, 0.011)
    rune_marks(k, Mt @ T(0.0, 0.14, 0.064), 7, 0.8, 0.009)
    rune_marks(k, Mt @ T(0.0, -0.14, 0.064), 7, 0.8, 0.009)
    k.put(cyl(0.035, 0.05, 7), "BH_Bottle", M=T(tx - 0.12, ty - 0.32, bz))             # ink of light
    k.put(cyl(0.028, 0.012, 7), "BH_Rune", M=T(tx - 0.12, ty - 0.32, bz + 0.045))
    k.put(tube([(tx - 0.12, ty - 0.32, bz + 0.03), (tx - 0.05, ty - 0.38, bz + 0.18)], [0.005, 0.009], 3), "BH_Brass")

    # ---- under and around: crate of bottles, sacks, a small keg, a stool at the side ---------------------------
    crate_open(k, TRS(-0.75, 0.0, 0.32, 0, 0, 4), 0.5, 0.4, 0.2, straw=True)
    for i in range(4):
        jar(k, T(-0.9 + i * 0.1, 0.0 + (i % 2) * 0.08 - 0.04, 0.35), "bottle")
    sack(k, TRS(0.35, 0.0, 0.34, 0, 0, 10), 0.4, 0.16)
    k.put(cyl(0.12, 0.3, 8), "BH_Bone", M=T(0.82, 0.02, 0.32), smooth=40)          # a lidded stoneware crock
    k.put(cyl(0.1, 0.03, 8), "BH_WoodDark", M=T(0.82, 0.02, 0.62))
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(box(0.04, 0.04, 0.46), "BH_WoodDark", M=TRS(1.42 + sx * 0.1, -0.1 + sy * 0.1, 0.23, sy * 5, -sx * 5, 0))
    k.put(cyl(0.16, 0.04, 9), "BH_Wood", M=T(1.42, -0.1, 0.46))

    k.sockets.append(("use", (0.0, -1.0, 0.0)))
    k.sockets.append(("flame", (fx + fl[0], fy + fl[1], bz + 0.04 + fl[2])))
    k.sockets.append(("light_a", la))
    k.col_box(bx1 - bx0, by1 - by0, bz, T(0, (by0 + by1) / 2, bz / 2))
    k.col_box(2.7, hy1 - hy0 + 0.06, 2.2, T(0, hyc, 1.1))
    k.col_box(0.35, 0.35, 0.5, T(1.42, -0.1, 0.25))
    return dict(recenter=False)


# =================================================================================================================
# 14. station_workbench - Workbench (bombs, scrolls, charms)
@asset("station_workbench", "market")
def station_workbench(k):
    """3.0 x 1.8. Tinker's bench: iron screw vice, tool board with hung tools, charm-stringing board, bomb makings,
    powder kegs underneath, a scroll corner with ink and quill; a sawhorse with a half-sawn plank and shavings."""
    r = k.r
    bx0, bx1, by0, by1, bz = -1.3, 0.75, -0.3, 0.32, 0.88
    trestle_bench(k, bx0, bx1, by0, by1, bz, 0.08, 0.12, "BH_Wood")
    plank(k, bx1 - bx0 - 0.3, by1 - by0 - 0.16, 0.04, T((bx0 + bx1) / 2, (by0 + by1) / 2, 0.24), mat="BH_WoodDark",
          tint=(0.5, 0.7))

    # ---- tool board on two posts behind the bench, with a top shelf and a lantern bracket ----------------------
    ty = 0.42
    for x in (bx0 + 0.05, bx1 - 0.05):
        k.put(box(0.09, 0.09, 2.05, bev=0.01), "BH_WoodDark", M=T(x, ty + 0.04, 1.025))
    n = 9
    for i in range(n):
        x = bx0 + 0.1 + (bx1 - bx0 - 0.2) * (i + 0.5) / n
        plank(k, (bx1 - bx0 - 0.2) / n - 0.01, 0.03, 1.0, T(x, ty, bz + 0.55), mat="BH_Wood", tint=(0.45, 0.7))
    for z in (bz + 0.1, bz + 1.0):
        k.put(box(bx1 - bx0, 0.05, 0.08), "BH_WoodDark", M=T((bx0 + bx1) / 2, ty - 0.03, z))
    plank(k, bx1 - bx0 + 0.1, 0.26, 0.035, T((bx0 + bx1) / 2, ty - 0.1, bz + 1.12), mat="BH_WoodDark", tint=(0.5, 0.7))
    for x in (bx0 + 0.3, bx1 - 0.3):
        k.put(prism([(0, 0), (0.18, 0), (0, -0.16)], 0.04), "BH_WoodDark", M=T(x, ty - 0.02, bz + 1.1) @ R(0, 0, 90))
    # pegs + hung tools: saw, mallet, chisels, hand drill, tongs, a coil of wire, pliers
    fy = ty - 0.03
    zt = bz + 0.9
    sx0 = bx0 + 0.25
    k.put(prism(saw_outline(), 0.008), "BH_Metal", M=T(sx0 + 0.05, fy - 0.01, zt - 0.3))    # saw blade
    k.put(box(0.12, 0.03, 0.14, bev=0.01), "BH_Wood", M=T(sx0 + 0.3, fy - 0.01, zt - 0.23))  # saw handle
    k.put(cyl(0.012, 0.05, 5), "BH_WoodDark", M=TRS(sx0 + 0.3, fy, zt - 0.06, 90, 0, 0))
    x = sx0 + 0.5
    k.put(cyl(0.012, 0.05, 5), "BH_WoodDark", M=TRS(x, fy, zt, 90, 0, 0))
    k.put(cyl(0.013, 0.32, 6), "BH_Wood", M=T(x, fy - 0.04, zt - 0.34))                    # mallet
    k.put(cyl(0.05, 0.14, 8), "BH_WoodDark", M=TRS(x - 0.07, fy - 0.04, zt - 0.36, 0, 90, 0))
    for i in range(4):                                                                      # chisels in a rack
        cx = x + 0.2 + i * 0.06
        k.put(cyl(0.012, 0.1, 6), "BH_Wood", M=T(cx, fy - 0.05, zt - 0.12))
        k.put(box(0.018 - i * 0.003, 0.006, 0.14), "BH_Iron", M=T(cx, fy - 0.05, zt - 0.2))
    k.put(box(0.3, 0.05, 0.03), "BH_WoodDark", M=T(x + 0.29, fy - 0.03, zt - 0.03))
    x += 0.62
    k.put(tube([(x, fy - 0.03, zt - 0.02), (x, fy - 0.03, zt - 0.4)], 0.01, 4), "BH_Iron")    # hand drill
    k.put(tube([(x, fy - 0.03, zt - 0.12), (x + 0.06, fy - 0.03, zt - 0.17), (x, fy - 0.03, zt - 0.22)], 0.008, 3),
          "BH_Iron")
    k.put(ico(0.03, 1), "BH_Wood", M=T(x, fy - 0.03, zt - 0.01))
    for i in range(3):
        k.put(torus(0.07, 0.006, 10, 3), "BH_Copper", M=TRS(x + 0.2, fy - 0.03, zt - 0.1 - i * 0.012, 90, 0, 0))
    k.put(cyl(0.01, 0.05, 5), "BH_WoodDark", M=TRS(x + 0.2, fy, zt - 0.03, 90, 0, 0))
    tongs_hung(k, (x + 0.36, fy - 0.03, zt), 0.42)
    # top shelf: jars of powders, a lantern-oil flask, a box of fuses
    shelf_row(k, bx0 + 0.1, bx1 - 0.35, ty - 0.1, bz + 1.14, ("crock", "bottle", "crock", "pot", "crock"),
              ("BH_Bone", "BH_Bottle", "BH_WoodDark", "BH_Wood", "BH_Leather"))
    k.put(tube([(bx1 - 0.08, ty - 0.02, bz + 1.35), (bx1 + 0.15, ty - 0.1, bz + 1.42), (bx1 + 0.28, ty - 0.14, bz + 1.36)],
               0.013, 4), "BH_Iron")
    la = lantern_on_hook(k, bx1 + 0.28, ty - 0.14, bz + 1.36, 0.45)

    # ---- the vice at the front-left corner, clamping a stock of wood ------------------------------------------
    vx, vy = bx0 + 0.28, by0 + 0.02
    k.put(box(0.12, 0.14, 0.26, bev=0.01), "BH_Iron", M=T(vx, vy + 0.06, bz - 0.13))
    k.put(box(0.12, 0.05, 0.3, bev=0.01), "BH_Iron", M=T(vx, vy - 0.06, bz - 0.1))
    k.put(box(0.14, 0.2, 0.05, bev=0.01), "BH_Iron", M=T(vx, vy, bz + 0.03))
    k.put(cyl(0.018, 0.3, 6), "BH_Iron", M=TRS(vx, vy - 0.08, bz - 0.12, 90, 0, 0))
    k.put(cyl(0.012, 0.3, 5), "BH_Iron", M=TRS(vx - 0.15, vy - 0.12, bz - 0.12, 0, 90, 0))
    for sx in (-1, 1):
        k.put(ico(0.022, 1), "BH_Iron", M=T(vx + sx * 0.15, vy - 0.12, bz - 0.12))
    k.put(box(0.06, 0.05, 0.3, bev=0.006), "BH_Wood", M=TRS(vx, vy - 0.02, bz + 0.1, 0, 0, 0))

    # ---- bomb makings: iron shells in a tray, a funnel, fuse cord ------------------------------------------------
    crate_open(k, TRS(-0.72, -0.05, bz, 0, 0, 6), 0.42, 0.34, 0.1, straw=True)
    for (dx, dy) in ((-0.1, -0.07), (0.05, -0.08), (-0.05, 0.07), (0.1, 0.06)):
        bomb(k, TRS(-0.72 + dx, -0.05 + dy, bz + 0.04, 0, 0, r.uniform(0, 90)), 0.06)
    bomb(k, T(-0.42, -0.2, bz), 0.065)
    k.put(lathe([(0.012, 0.0), (0.012, 0.05), (0.07, 0.12), (0.075, 0.12), (0.017, 0.05), (0.017, 0.0)], 8), "BH_Copper",
          M=T(-0.42, 0.1, bz), smooth=40)
    rope_coil(k, T(-0.3, -0.15, bz), 0.08, 2)
    k.put(lathe([(0.0, 0.0), (0.09, 0.01), (0.08, 0.05), (0.0, 0.06)], 8), "BH_StoneDark", M=T(-0.95, 0.12, bz))   # spilt powder

    # ---- charm-stringing board, propped up: pins, strung beads, finished charms ----------------------------------
    cbx, cby = -0.05, 0.05
    Mc = T(cbx, cby, bz) @ R(58, 0, 0)
    k.put(box(0.5, 0.36, 0.03, bev=0.006), "BH_WoodDark", M=Mc @ T(0, 0.18, 0.015))
    k.put(box(0.05, 0.03, 0.3), "BH_WoodDark", M=TRS(cbx, cby + 0.22, bz + 0.13, -22, 0, 0))
    gems = ("BH_GemRed", "BH_GemAqua", "BH_GemAmber", "BH_GemGreen", "BH_GemViolet", "BH_GemGold")
    for j in range(3):
        yv = 0.07 + j * 0.1
        k.put(tube([(-0.2, yv, 0.035), (0.0, yv + 0.015 * (1 - j), 0.035), (0.2, yv, 0.035)], 0.0035, 3), "BH_Rope", M=Mc)
        for sx in (-1, 1):
            k.put(cyl(0.006, 0.03, 4), "BH_Brass", M=Mc @ T(sx * 0.2, yv, 0.03))
        for i in range(6):
            k.put(ico(0.014, 1), gems[(i + j * 2) % 6] if i % 2 == 0 else "BH_Bone",
                  M=Mc @ T(-0.14 + i * 0.056, yv + 0.006 * math.sin(i), 0.04))
    for i in range(3):                                                                     # finished charms
        k.put(torus(0.03, 0.006, 8, 3), "BH_Brass", M=T(0.3 + i * 0.09, -0.18, bz + 0.006))
        k.put(ico(0.016, 1), gems[i + 1], M=T(0.3 + i * 0.09, -0.18, bz + 0.016))
    k.put(box(0.16, 0.1, 0.04, bev=0.006), "BH_WoodDark", M=T(0.3, 0.1, bz + 0.02))            # bead box
    for i in range(6):
        k.put(ico(0.012, 1), gems[i], M=T(0.25 + (i % 3) * 0.045, 0.08 + (i // 3) * 0.04, bz + 0.045))

    # ---- scroll corner: parchment, rolled scrolls, inkwell and quill, sealing wax, candle ------------------------
    k.put(box(0.3, 0.22, 0.004), "BH_Paper", M=TRS(0.55, -0.1, bz + 0.003, 0, 0, -12))
    k.put(box(0.26, 0.2, 0.004), "BH_Paper", M=TRS(0.58, -0.08, bz + 0.008, 0, 0, 6))
    scroll(k, TRS(0.55, 0.14, bz, 0, 0, 80), 0.3, 0.022, "BH_ClothRed")
    scroll(k, TRS(0.64, 0.16, bz, 0, 0, 72), 0.28, 0.02, "BH_ClothBlue")
    k.put(cyl(0.03, 0.05, 7), "BH_Bottle", M=T(0.42, 0.08, bz))
    k.put(tube([(0.42, 0.08, bz + 0.04), (0.38, 0.02, bz + 0.2)], [0.005, 0.011], 3), "BH_Paper")
    k.put(box(0.1, 0.02, 0.02), "BH_ClothRed", M=TRS(0.68, -0.22, bz + 0.01, 0, 0, 20))
    k.put(cyl(0.025, 0.1, 7), "BH_Candle", M=T(0.66, 0.02, bz))
    flame_tip(k, T(0.66, 0.02, bz + 0.115), 0.035)

    # ---- powder kegs under the bench and at its left end --------------------------------------------------------
    keg(k, T(-0.95, 0.02, 0.26), 0.4, 0.15)
    keg(k, T(-0.55, 0.02, 0.26), 0.4, 0.15)
    keg(k, T(bx0 + 0.1, -0.55, 0), 0.55, 0.2)
    keg(k, TRS(bx0 + 0.05, 0.15, 0, 0, 0, 30), 0.5, 0.19)
    k.put(cyl(0.14, 0.02, 9), "BH_StoneDark", M=T(bx0 + 0.05, 0.15, 0.5))   # opened: black powder

    # ---- sawhorse with a half-sawn plank, shavings and offcuts on the ground ------------------------------------
    hx, hy = 1.12, -0.05
    for sy in (-1, 1):
        for s_ in (-1, 1):
            k.put(box(0.05, 0.05, 0.72), "BH_WoodDark", M=TRS(hx + s_ * 0.15, hy + sy * 0.3, 0.33, 0, s_ * 14, 0))
    k.put(box(0.1, 0.72, 0.08), "BH_WoodDark", M=T(hx, hy, 0.66))
    plank(k, 1.3, 0.22, 0.035, T(hx, hy + 0.08, 0.72) @ R(0, 0, 90), mat="BH_Wood", tint=(0.7, 0.9))
    Ms = T(hx + 0.02, hy - 0.2, 0.74) @ R(0, 0, 90) @ R(0, 18, 0)
    k.put(prism(saw_outline(0.44), 0.008), "BH_Metal", M=Ms)
    k.put(box(0.1, 0.025, 0.12, bev=0.01), "BH_Wood", M=Ms @ T(0.27, 0, 0.07))
    for i in range(14):
        a = r.uniform(0, 6.28)
        d = r.uniform(0.05, 0.4)
        k.put(torus(0.025, 0.004, 5, 3), "BH_Wood", M=TRS(hx + math.cos(a) * d, hy + math.sin(a) * d, 0.006,
                                                           r.uniform(50, 90), 0, r.uniform(0, 180)), tint=1.0)
    for i in range(3):
        k.put(box(r.uniform(0.12, 0.25), 0.08, 0.03), "BH_Wood",
              M=TRS(hx + r.uniform(-0.3, 0.3), hy + r.uniform(-0.45, -0.3), 0.015, 0, 0, r.uniform(0, 180)))

    k.sockets.append(("use", (-0.3, -0.85, 0.0)))
    k.sockets.append(("light_a", la))
    k.col_box(bx1 - bx0, by1 - by0, bz, T((bx0 + bx1) / 2, (by0 + by1) / 2, bz / 2))
    k.col_box(bx1 - bx0 + 0.1, 0.2, 2.05, T((bx0 + bx1) / 2, ty, 1.02))
    k.col_box(0.5, 0.8, 0.75, T(hx, hy, 0.37))
    k.col_box(0.45, 0.45, 0.6, T(bx0 + 0.1, -0.55, 0.3))
    k.col_box(0.4, 0.4, 0.6, T(bx0 + 0.05, 0.15, 0.3))
    return dict(recenter=False)


# =================================================================================================================
# 15. station_forge - the standalone town forge (Olivar)
def stone(k, sx, sy, sz, M, mat="BH_Stone", chips=1):
    t = box(sx, sy, sz, bev=0.025)
    if chips:
        chip(t, k.r, k.r.randint(0, chips), 0.03)
    k.put(t, mat, M=M)


@asset("station_forge", "market")
def station_forge(k):
    """3.6 x 3.0. Stone hearth at the back with glowing coals under a corbelled brick hood and a tall brick chimney;
    great leather bellows on a frame at its side, anvil on a stump, stone quench trough, tool rack, coal and stock."""
    r = k.r
    hx0, hx1, hy0, hy1, hz = -1.25, 0.35, 0.2, 1.22, 0.78     # hearth block
    hcx, hcy = (hx0 + hx1) / 2, (hy0 + hy1) / 2
    # hearth: stacked courses of large stones, a heavy stone top slab with a coal bed
    zc = 0.0
    for ci, h in enumerate((0.26, 0.24, 0.22)):
        x = hx0
        while x < hx1 - 0.05:
            w = min(r.uniform(0.34, 0.55), hx1 - x)
            stone(k, w - 0.02, 0.24, h - 0.02, T(x + w / 2, hy0 + 0.12, zc + h / 2))
            x += w
        for sx, xe in ((-1, hx0), (1, hx1)):
            y = hy0 + 0.24
            while y < hy1 - 0.05:
                d = min(r.uniform(0.3, 0.5), hy1 - y)
                stone(k, 0.24, d - 0.02, h - 0.02, T(xe - sx * 0.12, y + d / 2, zc + h / 2))
                y += d
        zc += h
    k.put(box(hx1 - hx0 - 0.46, hy1 - hy0 - 0.28, zc), "BH_StoneDark", M=T(hcx, hcy + 0.12, zc / 2))   # core fill
    stone(k, hx1 - hx0 + 0.08, 0.2, 0.1, T(hcx, hy0 + 0.06, hz + 0.05), "BH_Stone", 2)                 # front lip
    for sx, xe in ((-1, hx0), (1, hx1)):
        stone(k, 0.3, hy1 - hy0 - 0.2, 0.1, T(xe - sx * 0.11, hcy + 0.1, hz + 0.05), "BH_Stone", 1)
    k.put(box(hx1 - hx0 - 0.5, hy1 - hy0 - 0.3, 0.06), "BH_StoneDark", M=T(hcx, hcy + 0.1, hz + 0.03))
    for i in range(22):
        a = r.uniform(0, 6.28)
        d = r.uniform(0.0, 0.3)
        lump(k, T(hcx + math.cos(a) * d * 1.3, hcy + 0.05 + math.sin(a) * d * 0.8, hz + 0.08),
             (0.07, 0.06, 0.05), "BH_Coals" if (d < 0.2 and i % 3) else "BH_StoneDark")
    # back wall and brick side piers carrying the hood
    stone(k, hx1 - hx0 + 0.1, 0.3, 1.2, T(hcx, hy1 + 0.05, hz + 0.6), "BH_Stone", 2)
    for xe in (hx0 + 0.12, hx1 - 0.12):
        k.put(box(0.26, 0.36, 1.12, bev=0.02), "BH_Brick", M=T(xe, hy1 - 0.3, hz + 0.56))
    # corbelled brick hood: stepped courses shrinking upward, then the chimney stack
    hood_z = hz + 1.12
    steps = [(hx1 - hx0 + 0.24, hy1 - hy0 + 0.1, 0.16), (hx1 - hx0 + 0.1, hy1 - hy0 - 0.05, 0.16),
             (hx1 - hx0 - 0.25, hy1 - hy0 - 0.25, 0.18), (hx1 - hx0 - 0.6, hy1 - hy0 - 0.42, 0.18),
             (0.8, 0.62, 0.2)]
    z = hood_z
    for (w, d, h) in steps:
        k.put(box(w, d, h, bev=0.015), "BH_Brick", M=T(hcx, hy1 + 0.2 - d / 2, z + h / 2))
        k.put(box(w + 0.04, d + 0.04, 0.035), "BH_Stone", M=T(hcx, hy1 + 0.2 - d / 2, z + 0.0175))
        z += h
    ch_w, ch_d = 0.78, 0.6
    ch_y = hy1 + 0.2 - 0.31
    ch_top = 5.3
    k.put(box(ch_w, ch_d, ch_top - z, bev=0.02), "BH_Brick", M=T(hcx, ch_y, (z + ch_top) / 2))
    for zz in (z + 1.2, ch_top - 0.05):
        k.put(box(ch_w + 0.1, ch_d + 0.1, 0.1, bev=0.02), "BH_Stone", M=T(hcx, ch_y, zz))
    k.put(box(ch_w - 0.2, ch_d - 0.2, 0.04), "BH_StoneDark", M=T(hcx, ch_y, ch_top + 0.01))
    for sx in (-1, 1):
        k.put(box(0.12, 0.12, 0.22), "BH_Brick", M=T(hcx + sx * (ch_w / 2 - 0.08), ch_y, ch_top + 0.11))
    k.put(box(ch_w + 0.02, ch_d * 0.5, 0.06), "BH_Stone", M=T(hcx, ch_y, ch_top + 0.25))       # rain slab
    # soot on the hood's underside and an iron hook bar with a hanging kettle
    k.put(box(hx1 - hx0 - 0.3, hy1 - hy0 - 0.2, 0.02), "BH_StoneDark", M=T(hcx, hcy + 0.1, hood_z - 0.005))
    rod(k, (hx0 + 0.3, hy1 - 0.3, hood_z - 0.15), (hx1 - 0.3, hy1 - 0.3, hood_z - 0.15), 0.015, "BH_Iron", 4)

    # ---- great bellows at the right of the hearth, worked by a lever from a post ---------------------------------
    bx, by, bz = 0.95, 0.95, 0.75
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(box(0.07, 0.07, bz), "BH_WoodDark", M=T(bx + sx * 0.25, by + sy * 0.3, bz / 2))
    k.put(box(0.6, 0.72, 0.06), "BH_WoodDark", M=T(bx, by, bz))
    bel = [(-0.28, 0.0), (0.28, 0.0), (0.34, 0.3), (0.26, 0.55), (0.0, 0.66), (-0.2, 0.55), (-0.28, 0.3)]
    for dz in (0.05, 0.3):
        k.put(prism(bel, 0.04), "BH_Wood", M=T(bx + 0.3, by, bz + dz) @ R(0, 0, -90) @ R(90, 0, 0))
    leath = lathe([(0.27, 0.0), (0.32, 0.1), (0.27, 0.2)], 10)
    for v in leath.verts:
        v.co.x *= 1.1
    k.put(leath, "BH_Leather", M=T(bx, by, bz + 0.07), smooth=40)
    rod(k, (bx - 0.32, by, bz + 0.15), (hx1 - 0.1, by - 0.05, hz + 0.1), 0.04, "BH_Iron", 6)       # tuyere
    rod(k, (bx + 0.35, by + 0.45, 0.0), (bx + 0.35, by + 0.45, 1.9), 0.05, "BH_WoodDark", 7)          # lever post
    rod(k, (bx + 0.4, by + 0.45, 1.85), (bx - 0.05, by - 0.4, 1.95), 0.035, "BH_Wood", 6)             # lever
    rope(k, (bx + 0.1, by, 1.9), (bx + 0.05, by, bz + 0.36), 0.0, 0.008, n=2, mat="BH_Iron")
    k.put(tube([(bx - 0.05, by - 0.4, 1.95), (bx - 0.05, by - 0.42, 1.55)], 0.009, 3), "BH_Iron")      # pull chain
    k.put(torus(0.05, 0.01, 8, 3), "BH_Iron", M=TRS(bx - 0.05, by - 0.42, 1.5, 90, 0, 0))

    # ---- tool rack against the left side of the hearth -----------------------------------------------------------
    rx = hx0 - 0.3
    for y in (0.4, 1.2):
        k.put(box(0.08, 0.08, 1.7, bev=0.01), "BH_WoodDark", M=T(rx, y, 0.85))
    k.put(box(0.07, 0.95, 0.08), "BH_WoodDark", M=T(rx, 0.8, 1.55))
    k.put(box(0.07, 0.95, 0.07), "BH_WoodDark", M=T(rx, 0.8, 0.5))
    for i, y in enumerate((0.48, 0.6, 0.72, 0.84, 0.96, 1.08)):
        if i % 2 == 0:
            tongs_hung(k, (rx - 0.05, y, 1.52), 0.62)
        else:
            hammer_hung(k, (rx - 0.05, y, 1.52), 0.4)
    # iron bar stock leaning on the rack, a keg of rods
    for i in range(4):
        k.put(box(0.03, 0.03, 1.3), "BH_Iron", M=TRS(rx - 0.03 - i * 0.02, 1.3 + i * 0.03, 0.62, 0, 9 + i * 2, 0))
    keg(k, T(rx + 0.02, -0.05, 0), 0.5, 0.2, hoops=True)
    for i in range(5):
        k.put(cyl(0.012, 0.7, 4), "BH_Iron", M=TRS(rx + 0.02 + (i - 2) * 0.03, -0.05, 0.2, (i - 2) * 4, 0, 0))

    # ---- anvil on a stump (front right) with work on it -----------------------------------------------------------
    ax_, ay_ = 0.75, -0.5
    face = anvil(k, TRS(ax_, ay_, 0, 0, 0, -6), 1.0, 0.52)
    k.put(box(0.36, 0.05, 0.02), "BH_Coals", M=TRS(ax_ + 0.05, ay_, face + 0.01, 0, 0, -6))   # glowing bar on the face
    tongs_hung(k, (ax_ + 0.34, ay_ + 0.02, face - 0.02), 0.4)
    hammer(k, TRS(ax_ - 0.2, ay_ + 0.03, face - 0.005, 0, 0, 160), 0.36)

    # ---- stone quench trough (front left), coal heap, bucket --------------------------------------------------
    qx, qy = -0.95, -0.55
    for sy in (-1, 1):
        stone(k, 1.0, 0.1, 0.5, T(qx, qy + sy * 0.2, 0.25), "BH_Stone", 1)
    for sx in (-1, 1):
        stone(k, 0.1, 0.5, 0.5, T(qx + sx * 0.45, qy, 0.25), "BH_Stone", 1)
    k.put(box(0.8, 0.3, 0.3), "BH_StoneDark", M=T(qx, qy, 0.15))
    k.put(box(0.82, 0.32, 0.01), "BH_Iron", M=T(qx, qy, 0.42))                  # dark water
    k.put(tube([(qx + 0.2, qy - 0.02, 0.43), (qx + 0.52, qy + 0.05, 0.72)], 0.01, 4), "BH_Iron")   # blade cooling
    for i in range(12):
        a = r.uniform(0, 6.28)
        d = r.uniform(0.0, 0.28)
        lump(k, T(-1.45 + math.cos(a) * d, -1.1 + math.sin(a) * d * 0.7, 0.04 + (0.28 - d) * 0.4), (0.08, 0.07, 0.06),
             "BH_StoneDark")
    k.put(cyl(0.022, 0.8, 5), "BH_Wood", M=TRS(-1.2, -1.3, 0.12, -35, -12, 0))          # coal shovel in the heap
    k.put(box(0.2, 0.26, 0.015), "BH_Iron", M=TRS(-1.2, -1.36, 0.06, -12, 0, 0))

    # ---- light: lantern hung from an iron bracket on the right brick pier ----------------------------------------
    k.put(tube([(hx1 + 0.02, hy1 - 0.45, 2.25), (hx1 + 0.18, hy1 - 0.7, 2.32), (hx1 + 0.28, hy1 - 0.9, 2.25)], 0.013, 4),
          "BH_Iron")
    la = lantern_on_hook(k, hx1 + 0.28, hy1 - 0.9, 2.25, 0.45)

    k.sockets.append(("use", (0.75, -1.28, 0.0)))
    k.sockets.append(("flame", (hcx, hcy + 0.05, hz + 0.2)))
    k.sockets.append(("smoke", (hcx, ch_y, ch_top + 0.35)))
    k.sockets.append(("light_a", la))
    k.col_box(hx1 - hx0, hy1 - hy0 + 0.2, 1.9, T(hcx, hcy + 0.1, 0.95))
    k.col_box(0.8, 1.1, 1.0, T(bx + 0.05, by + 0.1, 0.5))
    k.col_box(0.6, 0.6, 0.8, T(ax_, ay_, 0.4))
    k.col_box(1.0, 0.5, 0.5, T(qx, qy, 0.25))
    k.col_box(0.4, 1.2, 1.7, T(rx - 0.05, 0.8, 0.85))
    k.col_box(0.45, 0.45, 0.6, T(rx + 0.02, -0.05, 0.3))
    return dict(recenter=False)
