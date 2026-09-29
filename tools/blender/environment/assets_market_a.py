"""bh-018 trade-quarter stands, part A (see work/lemondev/bh-018/contracts/stands.md).

Five purpose-built shop stands; the goods on and around each stand are the sign (no lettering):
  stand_provisions  Tovin, Provisioner     green canvas lean-to rising to the front, draught crates, sacks, barrels
  stand_arcana      Seris, Aether Mystic   violet hexagonal pavilion, crescent-and-star finial, crystal ball
  stand_lapidary    Ysolde Marr, Lapidary  verdigris copper monopitch, gem wheel, lens arm, glowing crystal cabinet
  stand_smithy      Brannoc, Blacksmith    slate lean-to on a stone forge wall, chimney, coals, anvil yard
  stand_wagon       The Hooded Stranger    black bow-top wagon, side hatch let down on chains as a counter

Conventions (contract): metres, Z-up, origin at the bottom centre of the footprint, front (customer side) = -Y,
recenter=False. Colour comes only from the BH_* material choice (the game ignores vertex tint). Head-visibility rule:
from the npc head (z 1.8) the ray toward the game camera rises 1.38 m per metre toward -Y and must clear every roof.
"""
import math

import bmesh
from mathutils import Matrix, Vector

from kit import *  # noqa
from masonry import masonry  # noqa
import market_common  # noqa  (registers the extra BH_* materials)
from registry import asset
from assets_props import plank, rivet, flame_tip, wheel, skull, sword, shield_round, helmet
from assets_town2 import keg, hang_lantern
from assets_interior import candle, spear, book

CAM = Vector((0.0, -math.cos(math.radians(54)), math.sin(math.radians(54))))


# ---------------------------------------------------------------------------------------------------------------
# generic helpers
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
    """Square timber from a to b (over = extra length at both ends)."""
    M, L = along(a, b)
    k.put(box(w, h or w, L + 2 * over, bev=bev), mat, M=M @ T(0, 0, L / 2), tint=tint)


def pole(k, a, b, r, mat="BH_WoodDark", segs=8, tint=0.6, r2=None):
    M, L = along(a, b)
    k.put(cyl(r, L, segs, r2=r2), mat, M=M, tint=tint, smooth=40)


def rope(k, a, b, sag=0.05, r=0.012, n=6, mat="BH_Rope", segs=4):
    a, b = Vector(a), Vector(b)
    pts = []
    for i in range(n + 1):
        t = i / n
        p = a.lerp(b, t)
        p.z -= sag * 4 * t * (1 - t)
        pts.append(p)
    k.put(tube(pts, r, segs), mat, smooth=40)


def lashing(k, M, r=0.07, n=3):
    """A few turns of rope around a joint (rings in the local XY plane)."""
    for i in range(n):
        k.put(torus(r, 0.011, 8, 3), "BH_Rope", M=M @ T(0, 0, (i - (n - 1) / 2) * 0.026))


def footing(k, x, y, s=0.34, h=0.16, mat="BH_Stone"):
    t = box(s, s, h, bev=0.03)
    chip(t, k.r, 2, 0.03)
    k.put(t, mat, M=TRS(x, y, h / 2, 0, 0, k.r.uniform(-8, 8)), tint=0.85)


def post(k, x, y, h, w=0.14, mat="BH_WoodDark", foot=True, z0=0.0):
    if foot:
        footing(k, x, y)
        z0 = max(z0, 0.14)
    k.put(box(w, w, h - z0, bev=0.018), mat, M=T(x, y, z0 + (h - z0) / 2), tint=k.r.uniform(0.5, 0.7))


def surface(k, fn, nu, nv, mat, thick=0.025, tint=0.85, smooth=40):
    """Grid surface from fn(u, v) -> (x, y, z), u,v in [0, 1], solidified."""
    t = tb()
    vs = [[t.verts.new(fn(i / nu, j / nv)) for i in range(nu + 1)] for j in range(nv + 1)]
    for j in range(nv):
        for i in range(nu):
            t.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    bmesh.ops.recalc_face_normals(t, faces=t.faces)
    if thick:
        bmesh.ops.solidify(t, geom=list(t.faces), thickness=thick)
    k.put(t, mat, tint=tint, smooth=smooth, tile=1.5)


# ---------------------------------------------------------------------------------------------------------------
# goods
def potion(k, M, liquid, h=0.2, r=0.06, kind="round", segs=6):
    """Corked draught: glowing liquid body (Gem material), dark glass neck, cork. Origin at the base."""
    if kind == "round":
        body = [(0.0, 0.0), (r * 0.8, 0.01), (r, r * 0.8), (r * 0.7, r * 1.55), (0.0, r * 1.8)]
        nz = r * 1.72
    elif kind == "tall":
        body = [(0.0, 0.0), (r * 0.8, 0.0), (r * 0.8, h * 0.62), (r * 0.5, h * 0.7), (0.0, h * 0.7)]
        nz = h * 0.68
    elif kind == "lo":  # cheap shelf stock: faceted body + neck
        k.put(cyl(r, h * 0.62, 5), liquid, M=M, uvoff=False)
        k.put(cyl(r * 0.3, h * 0.38, 4, r2=r * 0.25), "BH_Bottle", M=M @ T(0, 0, h * 0.62))
        return
    else:  # squat flat-shouldered
        body = [(0.0, 0.0), (r, 0.0), (r * 1.02, h * 0.35), (r * 0.7, h * 0.5), (0.0, h * 0.5)]
        nz = h * 0.48
    k.put(lathe(body, segs), liquid, M=M, smooth=60, uv="keep")
    nh = max(h - nz - 0.025, 0.03)
    k.put(cyl(r * 0.28, nh, 5, r2=r * 0.24), "BH_Bottle", M=M @ T(0, 0, nz - 0.01), smooth=50)
    k.put(cyl(r * 0.36, 0.03, 5, r2=r * 0.3), "BH_Wood", M=M @ T(0, 0, nz + nh - 0.012), tint=0.7)


def crate_open(k, M, w, d, h, mat="BH_Wood", straw=True):
    """Low open crate of planks (origin bottom centre)."""
    th = 0.022
    plank(k, w, d, th, M @ T(0, 0, th / 2), mat=mat, chips=0)
    for sy in (-1, 1):
        for j in range(2):
            plank(k, w, th, h / 2 - 0.006, M @ T(0, sy * (d / 2 - th / 2), h / 4 + j * h / 2), mat=mat, chips=1)
    for sx in (-1, 1):
        for j in range(2):
            plank(k, th, d - 2 * th, h / 2 - 0.006, M @ T(sx * (w / 2 - th / 2), 0, h / 4 + j * h / 2), mat=mat, chips=1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(box(0.035, 0.035, h + 0.01), "BH_WoodDark", M=M @ T(sx * (w / 2 - 0.02), sy * (d / 2 - 0.02), h / 2),
                  tint=0.5)
    if straw:
        t = box(w - 0.05, d - 0.05, 0.02)
        subdiv(t, 2)
        jitter(t, k.r, 0.012)
        k.put(t, "BH_Thatch", M=M @ T(0, 0, h * 0.45), tint=0.9)


def potion_crate(k, M, liquid, nx=4, ny=3, kind="round", w=None, d=None, alt=None):
    r = 0.052
    step = 0.13
    w = w or nx * step + 0.06
    d = d or ny * step + 0.06
    crate_open(k, M, w, d, 0.16)
    for i in range(nx):
        for j in range(ny):
            liq = alt if (alt and (i + j) % 3 == 1) else liquid
            x = -((nx - 1) * step) / 2 + i * step + k.r.uniform(-0.008, 0.008)
            y = -((ny - 1) * step) / 2 + j * step + k.r.uniform(-0.008, 0.008)
            potion(k, M @ TRS(x, y, 0.03, k.r.uniform(-4, 4), k.r.uniform(-4, 4), k.r.uniform(0, 90)), liq, 0.2, r, kind)


def sack(k, M, h=0.62, r=0.24, open_=False, fill="BH_Thatch", mat="BH_Cloth", squash=0.8):
    prof = [(r * 0.8, 0.0), (r, h * 0.14), (r * 1.03, h * 0.45), (r * 0.94, h * 0.72), (r * 0.62, h * 0.88)]
    if not open_:
        prof += [(r * 0.24, h * 0.95), (r * 0.12, h)]
    t = lathe(prof, 10, cap_top=not open_)
    for v in t.verts:
        v.co.y *= squash
    ndisp(t, 5.0, 0.025, k.noff + Vector((M[0][3], M[1][3], 0)))
    k.put(t, mat, M=M, tint=k.r.uniform(0.7, 0.95), smooth=50)
    if open_:
        # rolled-down lip and the grain inside
        k.put(torus(r * 0.64, 0.035, 10, 4), mat, M=M @ S(1, squash, 1) @ T(0, 0, h * 0.88), tint=0.8, smooth=50)
        g = lathe([(r * 0.62, 0.0), (r * 0.45, 0.04), (0.0, 0.06)], 10, cap_bot=False)
        k.put(g, fill, M=M @ S(1, squash, 1) @ T(0, 0, h * 0.86), tint=0.95, smooth=40)
    else:
        k.put(torus(r * 0.22, 0.014, 8, 3), "BH_Rope", M=M @ T(0, 0, h * 0.93))
        t2 = cyl(r * 0.2, 0.1, 6, r2=r * 0.34)
        jitter(t2, k.r, 0.01)
        k.put(t2, mat, M=M @ T(0, 0, h * 0.95), tint=0.8)


def scroll(k, M, L=0.32, r=0.024, ribbon="BH_ClothRed", seal=False):
    """Rolled parchment along local X, resting on its side (origin at the bottom centre)."""
    k.put(cyl(r, L, 8), "BH_Paper", M=M @ TRS(-L / 2, 0, r, 0, 90, 0), tint=k.r.uniform(0.8, 1.0), smooth=40)
    k.put(cyl(r * 0.45, L + 0.02, 6), "BH_Paper", M=M @ TRS(-L / 2 - 0.01, 0, r, 0, 90, 0), tint=0.6)
    k.put(torus(r + 0.003, 0.006, 8, 3), ribbon, M=M @ TRS(0, 0, r, 0, 90, 0))
    if seal:
        k.put(cyl(0.02, 0.008, 8), "BH_ClothRed", M=M @ TRS(0, -r, r, 90, 0, 0), tint=0.6)


def basket(k, M, r=0.2, h=0.18, mat="BH_Thatch"):
    t = lathe([(r * 0.72, 0.0), (r, h), (r * 0.94, h), (r * 0.68, 0.02), (0.0, 0.02)], 12, cap_top=False)
    k.put(t, mat, M=M, tint=0.8, smooth=40)
    k.put(torus(r, 0.014, 12, 4), "BH_Wood", M=M @ T(0, 0, h), tint=0.6)


def herb_bundle(k, top, L=0.42, r=0.07, mat="BH_Moss"):
    """Bundle of herbs hung head-down from a string: tied stems at the top, ragged leafy mass below."""
    top = Vector(top)
    k.put(cyl(0.004, 0.12, 3), "BH_Rope", M=T(top.x, top.y, top.z - 0.12))
    zt = top.z - 0.12
    k.put(cyl(0.02, 0.1, 6), "BH_Thatch", M=T(top.x, top.y, zt - 0.08), tint=0.7)
    k.put(torus(0.022, 0.008, 6, 3), "BH_Rope", M=T(top.x, top.y, zt - 0.03))
    prof = [(0.02, 0.0), (r * 0.7, -L * 0.3), (r, -L * 0.65), (r * 0.8, -L * 0.9), (r * 0.3, -L)]
    prof = [(a, b) for a, b in prof[::-1]]
    t = lathe(prof, 7, cap_bot=False, cap_top=False)
    ndisp(t, 9.0, 0.02, k.noff + top)
    jitter(t, k.r, 0.012)
    k.put(t, mat, M=TRS(top.x, top.y, zt - 0.08, 0, 0, k.r.uniform(0, 60)), tint=0.9, smooth=30)


def garlic_string(k, top, L=0.6):
    top = Vector(top)
    k.put(tube([top, top + Vector((0.0, 0.0, -L))], 0.008, 4), "BH_Rope")
    n = 8
    prof = [(0.0, 0.0), (0.03, 0.012), (0.036, 0.03), (0.02, 0.055), (0.0, 0.07)]
    for i in range(n):
        a = i * 2.4
        z = top.z - 0.08 - (L - 0.08) * i / n
        rr = 0.04
        k.put(lathe(prof, 6), "BH_Bone", M=TRS(top.x + math.cos(a) * rr, top.y + math.sin(a) * rr, z - 0.035,
                                                  math.cos(a) * 25, math.sin(a) * 25, 0), tint=0.9, smooth=60)


def bomb(k, M, r=0.07):
    k.put(ico(r, 1), "BH_Iron", M=M @ T(0, 0, r), smooth=50)
    k.put(cyl(r * 0.35, 0.03, 6), "BH_Brass", M=M @ T(0, 0, r * 1.85))
    k.put(tube([(0, 0, r * 2.1), (0.01, 0.01, r * 2.5), (0.035, 0.0, r * 2.75)], 0.007, 3), "BH_Rope")


def rope_coil(k, M, R_=0.14, turns=4):
    for i in range(turns):
        k.put(torus(R_ - i * 0.004, 0.018, 10, 3), "BH_Rope", M=M @ T(0, 0, 0.018 + i * 0.03), tint=0.85)


def torch_bundle(k, M, n=5):
    for i in range(n):
        a = math.tau * i / n
        x, y = math.cos(a) * 0.035, math.sin(a) * 0.035
        k.put(cyl(0.018, 0.5, 5), "BH_WoodDark", M=M @ TRS(x, y, 0.0, 0, 0, 0), tint=0.6)
        k.put(cyl(0.03, 0.1, 6), "BH_Cloth", M=M @ T(x, y, 0.4), tint=0.35)
    k.put(torus(0.06, 0.01, 8, 3), "BH_Rope", M=M @ T(0, 0, 0.18))


def waterskin(k, M):
    t = ico(0.1, 1)
    for v in t.verts:
        v.co.x *= 0.7
        v.co.z *= 1.3
    k.put(t, "BH_Leather", M=M @ T(0, 0, 0.12), smooth=50)
    k.put(cyl(0.022, 0.06, 6), "BH_Wood", M=M @ T(0, 0, 0.24), tint=0.6)


def barrel(k, M, H=0.9, R_=0.3, mat="BH_Wood", tint=0.75, segs=9, lid=True):
    """Light barrel: bulged staves (lathe) + three iron bands as open shells. Origin at the bottom centre."""
    prof = [(R_ * 0.86, 0.0), (R_ * 0.97, H * 0.22), (R_, H * 0.5), (R_ * 0.97, H * 0.78), (R_ * 0.86, H)]
    k.put(lathe(prof, segs, uv_tile=0.5), mat, M=M, tint=tint, smooth=50, uv="keep")
    for z, rr in ((H * 0.1, 0.9), (H * 0.9, 0.9), (H * 0.5, 1.0)):
        k.put(cyl(R_ * rr + 0.008, 0.035, segs, caps=False), "BH_Iron", M=M @ T(0, 0, z - 0.017), smooth=50)
    if lid:
        k.put(cyl(R_ * 0.82, 0.02, segs), "BH_WoodDark", M=M @ T(0, 0, H - 0.03), tint=0.6)


def lantern_on_hook(k, x, y, z_hook, s=0.55):
    """Hook ring hanging point at (x, y, z_hook); returns the light point."""
    lp = hang_lantern(k, T(x, y, z_hook), s)
    return (x + lp[0], y + lp[1], z_hook + lp[2])


# ---------------------------------------------------------------------------------------------------------------
@asset("stand_provisions", "market")
def stand_provisions(k):
    """Tovin, Provisioner of Malasugue. 4.4 x 3.0. Plank stall with a green canvas lean-to that rises toward the front
    (back 2.4 m, front 3.15 m) on two forward poles; draughts, scrolls, bombs and supplies on the counter."""
    r = k.r
    W, D = 4.4, 3.0
    yb = 1.36         # back posts
    yf = -1.18        # front poles / front beam
    zb, zf = 2.4, 3.1  # beam tops
    yc0, yc1 = -1.36, -0.84  # counter depth (front face .. back)
    xc0, xc1 = -1.78, 1.12   # counter length
    zc = 1.0

    # --- frame: back posts, front poles (round, forward-propped), side rails, back beam, rafters
    for sx in (-1, 1):
        post(k, sx * 2.02, yb, zb, 0.15)
        # front pole: round, slightly leaning out, on a stone
        footing(k, sx * 2.05, yf, 0.3, 0.12)
        pole(k, (sx * 2.04, yf, 0.1), (sx * 2.08, yf - 0.03, zf + 0.16), 0.065, tint=0.55)
        k.put(ico(0.075, 1), "BH_WoodDark", M=T(sx * 2.08, yf - 0.03, zf + 0.2), tint=0.5)
        # side rail at counter height joins back post and front pole
        beam(k, (sx * 2.03, yb, 1.05), (sx * 2.04, yf, 1.05), 0.09, 0.1, tint=0.55)
        # knee brace at the back
        beam(k, (sx * 2.02, yb, 1.75), (sx * 2.02, yb - 0.55, zb - 0.06), 0.08, tint=0.55)
        # guy rope from the pole top down to a peg at the side
        px, pz = sx * 2.1, 0.02
        rope(k, (sx * 2.08, yf - 0.03, zf + 0.12), (sx * 2.18, yf - 0.28, 0.1), 0.02, 0.009)
        k.put(box(0.04, 0.04, 0.22), "BH_WoodDark", M=TRS(sx * 2.18, yf - 0.28, 0.08, 18, 0, 0), tint=0.5)
    beam(k, (-2.2, yb, zb - 0.06), (2.2, yb, zb - 0.06), 0.14, 0.14, tint=0.55)
    pole(k, (-2.2, yf, zf - 0.02), (2.2, yf, zf - 0.02), 0.06, tint=0.55)  # front beam (a round spar)
    rafters = (-2.04, -0.68, 0.68, 2.04)
    for x in rafters:
        beam(k, (x, yb + 0.1, zb + 0.03), (x, yf - 0.06, zf + 0.06), 0.06, 0.06, tint=0.6)
        k.put(torus(0.075, 0.012, 8, 3), "BH_Rope", M=TRS(x, yf, zf, 0, 90, 0))

    # --- canvas: sags between rafters, bellies a little along the slope, rolled hem at the front
    x0, x1 = -2.2, 2.2
    y0, y1 = yb + 0.12, yf - 0.08
    z0, z1 = zb + 0.1, zf + 0.12

    def canvas(u, v):
        x = lerp(x0, x1, u)
        y = lerp(y0, y1, v)
        z = lerp(z0, z1, v)
        # sag between the four rafters (u segments) and along the run
        seg = (x - rafters[0]) / (rafters[1] - rafters[0])
        f = seg - math.floor(seg)
        sag = 0.11 * math.sin(math.pi * min(max(f, 0.0), 1.0)) ** 0.8 if -2.04 <= x <= 2.04 else 0.0
        sag *= math.sin(math.pi * min(max(v, 0.0), 1.0)) ** 0.5
        z -= sag + 0.03 * math.sin(math.pi * v)
        z += mnoise.noise(Vector((x * 2.1, y * 2.3, 0.5)) + k.noff) * 0.012
        return (x, y, z)
    surface(k, canvas, 30, 9, "BH_ClothGreen", 0.025, 0.9)
    k.put(tube([(x0 - 0.02, y1 - 0.02, z1 - 0.02), (x1 + 0.02, y1 - 0.02, z1 - 0.02)], 0.045, 8), "BH_ClothGreen",
          tint=0.8, smooth=40)  # rolled hem
    # side drops: short triangular side flaps tied to the poles
    for sx in (-1, 1):
        x = sx * 2.2
        def flap(u, v, x=x):
            y = lerp(y0, y1, u)
            zt = lerp(z0, z1, u)
            return (x + sx * 0.005, y, zt - 0.02 - v * (0.32 - 0.12 * u))
        surface(k, flap, 8, 2, "BH_ClothGreen", 0.02, 0.75)
    # sewn-on patches that follow the canvas, and lashings along the back beam
    for (pu0, pu1, pv0, pv1) in ((0.66, 0.74, 0.3, 0.46), (0.17, 0.22, 0.62, 0.72)):
        def patch(u, v, a=(pu0, pu1, pv0, pv1)):
            x, y, z = canvas(lerp(a[0], a[1], u), lerp(a[2], a[3], v))
            return (x, y, z + 0.016)
        surface(k, patch, 3, 2, "BH_Cloth", 0.006, 0.6)
    for x in (-1.5, -0.3, 0.9, 1.9):
        k.put(torus(0.07, 0.01, 8, 3), "BH_Rope", M=TRS(x, yb, zb, 0, 90, 0))

    # --- back wall of planks with three shelves of stock
    for i in range(12):
        x = -1.94 + (3.88 / 12) * (i + 0.5)
        plank(k, 3.88 / 12 - 0.012, 0.035, 1.95, T(x, yb + 0.1, 1.0), mat="BH_Wood", tint=(0.5, 0.75))
    for z in (0.62, 1.12, 1.62):
        plank(k, 3.9, 0.3, 0.04, T(0, yb - 0.08, z), mat="BH_Wood", tint=(0.6, 0.8))
        for sx in (-1, 0, 1):
            k.put(prism([(0, 0), (0.22, 0), (0, -0.2)], 0.04), "BH_WoodDark", M=T(sx * 1.5, yb + 0.02, z - 0.02) @ R(0, 0, 90),
                  tint=0.5)
    liquids = ("BH_GemRed", "BH_GemAqua", "BH_GemRed", "BH_GemGreen", "BH_GemAqua")
    for si, z in enumerate((0.64, 1.14, 1.64)):
        x = -1.85
        while x < 1.8:
            kind = r.choice(("round", "tall", "squat"))
            roll = r.random()
            if roll < 0.2:  # stoneware jars with cloth lids
                k.put(cyl(0.075, 0.17, 7), "BH_Bone" if r.random() < 0.6 else "BH_Wood",
                      M=T(x + 0.08, yb - 0.1, z + 0.02), tint=r.uniform(0.6, 0.9))
                k.put(cyl(0.08, 0.03, 7), "BH_Cloth", M=T(x + 0.08, yb - 0.1, z + 0.18), tint=0.6)
                x += 0.2
                continue
            if roll < 0.32:  # a small box or a folded cloth stack
                bw = r.uniform(0.2, 0.3)
                k.put(box(bw, 0.2, r.uniform(0.1, 0.18), bev=0.01), r.choice(("BH_Wood", "BH_Cloth", "BH_Leather")),
                      M=TRS(x + bw / 2, yb - 0.12, z + 0.02, 0, 0, r.uniform(-8, 8)) @ T(0, 0, 0.06), tint=0.7)
                x += bw + 0.04
                continue
            # a group of two or three draughts of one colour
            liq = liquids[(si * 2 + int((x + 2) * 2)) % len(liquids)]
            for g in range(r.randint(2, 3)):
                potion(k, TRS(x + 0.05, yb - 0.1 + r.uniform(-0.04, 0.04), z + 0.02, 0, 0, r.uniform(0, 90)),
                       liq, r.uniform(0.18, 0.24), r.uniform(0.045, 0.06), "lo")
                x += r.uniform(0.11, 0.14)
            x += 0.06
    # rolled bedrolls and a lantern on the top shelf ends
    for sx in (-1, 1):
        k.put(cyl(0.1, 0.5, 10), "BH_Cloth" if sx < 0 else "BH_ClothRed", M=TRS(sx * 1.55 - 0.25, yb - 0.12, 2.0, 0, 90, 0),
              tint=0.7, smooth=40)
        k.put(torus(0.102, 0.012, 10, 3), "BH_Leather", M=TRS(sx * 1.55 - 0.1, yb - 0.12, 2.0, 0, 90, 0))

    # --- counter: plank top on trestles, vertical plank front with a skirting board
    ycm = (yc0 + yc1) / 2
    for i in range(4):
        plank(k, xc1 - xc0 + 0.1, (yc1 - yc0) / 4 - 0.01, 0.05,
              T((xc0 + xc1) / 2, yc0 + (yc1 - yc0) * (i + 0.5) / 4, zc - 0.025), tint=(0.65, 0.9))
    n = 10
    for i in range(n):
        x = xc0 + (xc1 - xc0) * (i + 0.5) / n
        plank(k, (xc1 - xc0) / n - 0.01, 0.035, zc - 0.08, T(x, yc0 + 0.03, (zc - 0.08) / 2), mat="BH_Wood",
              tint=(0.45, 0.7))
    for z in (0.18, zc - 0.14):
        k.put(box(xc1 - xc0 + 0.02, 0.06, 0.1, bev=0.01), "BH_WoodDark", M=T((xc0 + xc1) / 2, yc0 + 0.0, z), tint=0.5)
    for x in (xc0 + 0.05, xc1 - 0.05):
        k.put(box(0.1, yc1 - yc0, zc - 0.05, bev=0.01), "BH_WoodDark", M=T(x, ycm, (zc - 0.05) / 2), tint=0.55)
    plank(k, xc1 - xc0 - 0.2, 0.3, 0.04, T((xc0 + xc1) / 2, ycm + 0.05, 0.4), tint=(0.5, 0.7))  # under-shelf
    for x in (-1.3, 0.5):
        k.put(box(0.4, 0.3, 0.3, bev=0.02), "BH_Wood", M=TRS(x, ycm + 0.05, 0.57, 0, 0, r.uniform(-8, 8)), tint=0.6)

    # goods on the counter (seen from above-front)
    potion_crate(k, TRS(-1.42, ycm - 0.02, zc, 0, 0, 3), "BH_GemRed", 4, 3, "round")
    potion_crate(k, TRS(-0.72, ycm - 0.02, zc, 0, 0, -4), "BH_GemAqua", 3, 3, "round")
    basket(k, T(-0.12, ycm - 0.02, zc), 0.19, 0.16)
    for i in range(7):
        a = i * 2.3
        L = r.uniform(0.34, 0.44)
        rr = r.uniform(0.02, 0.028)
        x, y = -0.12 + math.cos(a) * 0.08 * (i % 3) / 2, ycm - 0.02 + math.sin(a) * 0.08 * (i % 3) / 2
        tilt = r.uniform(-28, 28)
        k.put(cyl(rr, L, 8), "BH_Paper", M=TRS(x, y, zc + 0.03, tilt, r.uniform(-25, 25), 0), tint=r.uniform(0.75, 1.0),
              smooth=40)
        k.put(cyl(rr + 0.004, 0.02, 7, caps=False), ("BH_ClothRed", "BH_ClothBlue", "BH_Rope")[i % 3],
              M=TRS(x, y, zc + 0.03, tilt, r.uniform(-25, 25), 0) @ T(0, 0, L * 0.55))
    scroll(k, TRS(0.26, ycm - 0.12, zc, 0, 0, 18), 0.34, 0.026, seal=True)
    scroll(k, TRS(0.3, ycm + 0.1, zc, 0, 0, -12), 0.3, 0.022, "BH_ClothBlue")
    # bombs in a small crate + loose ones, fuse coil
    crate_open(k, TRS(0.75, ycm - 0.01, zc, 0, 0, -6), 0.4, 0.34, 0.14, straw=True)
    for (x, y) in ((-0.1, -0.07), (0.05, -0.08), (-0.05, 0.07), (0.1, 0.06), (0.0, 0.0)):
        bomb(k, TRS(0.75 + x, ycm - 0.01 + y, zc + 0.05, 0, 0, r.uniform(0, 90)), 0.062)
    bomb(k, T(0.98, yc0 + 0.12, zc), 0.06)
    # a few loose draughts at the front edge, like just handed over
    potion(k, T(-1.0, yc0 + 0.1, zc), "BH_GemRed", 0.22, 0.06, "round")
    potion(k, T(-0.85, yc0 + 0.08, zc), "BH_GemAqua", 0.22, 0.055, "tall")
    # coin dish
    k.put(cyl(0.09, 0.03, 10, r2=0.1), "BH_Wood", M=T(-0.35, yc0 + 0.14, zc), tint=0.5)
    for i in range(5):
        k.put(cyl(0.018, 0.006, 8), "BH_Gold", M=TRS(-0.35 + r.uniform(-0.04, 0.04), yc0 + 0.14 + r.uniform(-0.04, 0.04),
                                                     zc + 0.03 + i * 0.004, r.uniform(-10, 10), 0, 0))

    # --- left end: grain sacks (one open with a scoop), a crate of supplies with rope, torches, waterskins
    sack(k, TRS(-1.98, -1.05, 0, 0, 0, 20), 0.66, 0.24)
    sack(k, TRS(-1.98, -0.55, 0, 0, 0, -10), 0.6, 0.24, open_=True)
    sack(k, TRS(-1.95, -0.8, 0.5, 70, 0, 80), 0.6, 0.22)  # lying on top of the pair
    k.put(cyl(0.04, 0.08, 8), "BH_Wood", M=TRS(-1.94, -0.52, 0.56, 30, 0, 0), tint=0.6)  # scoop
    k.put(cyl(0.012, 0.16, 5), "BH_Wood", M=TRS(-1.94, -0.52, 0.56, 30, 0, 0) @ TRS(0, 0.0, 0.04, -90, 0, 0), tint=0.6)
    k.put(box(0.6, 0.5, 0.5, bev=0.02), "BH_Wood", M=TRS(-1.78, 0.4, 0.25, 0, 0, 6), tint=0.7)
    rope_coil(k, TRS(-1.78, 0.38, 0.5, 0, 0, 0), 0.16)
    torch_bundle(k, TRS(-1.9, 0.9, 0.0, 0, -8, 0))
    waterskin(k, TRS(-1.55, 0.1, 0.5, 0, 0, 30))

    # --- right end: two barrels, a small powder keg, a crate
    barrel(k, TRS(1.52, -1.02, 0, 0, 0, 12), 0.95, 0.33, tint=0.75)
    barrel(k, TRS(1.95, -0.62, 0, 0, 0, 40), 0.88, 0.31, tint=0.65)
    k.put(cyl(0.29, 0.03, 12), "BH_WoodDark", M=T(1.52, -1.02, 0.95), tint=0.5)  # lid
    barrel(k, TRS(1.52, -1.02, 0.97, 0, 0, 0), 0.34, 0.14, mat="BH_WoodDark", tint=0.5, segs=8)  # powder keg
    k.put(tube([(1.52, -1.02, 1.31), (1.56, -1.05, 1.36), (1.62, -1.1, 1.33)], 0.008, 3), "BH_Rope")
    k.put(box(0.55, 0.5, 0.45, bev=0.02), "BH_Wood", M=TRS(1.85, 0.4, 0.225, 0, 0, -8), tint=0.7)
    k.put(box(0.45, 0.42, 0.38, bev=0.02), "BH_Wood", M=TRS(1.82, 0.42, 0.64, 0, 0, 10), tint=0.6)

    # --- drying herbs and garlic from the front spar (clear of the npc head ray at x -0.9..0.0)
    for x, mat in ((-1.85, "BH_Moss"), (-1.62, "BH_Thatch"), (-1.38, "BH_Moss"), (-1.12, "BH_Moss"),
                   (0.3, "BH_Thatch"), (0.55, "BH_Moss"), (1.55, "BH_Moss"), (1.78, "BH_Thatch")):
        herb_bundle(k, (x, yf, zf - 0.07), r.uniform(0.34, 0.46), r.uniform(0.06, 0.08), mat)
    garlic_string(k, (1.02, yf, zf - 0.06), 0.62)
    garlic_string(k, (1.25, yf, zf - 0.06), 0.52)
    # lantern hanging from the front spar
    light = lantern_on_hook(k, 0.8, yf, zf - 0.07, 0.5)

    # --- sockets and collision
    npc = (-0.45, -0.36, 0.0)
    k.sockets.append(("npc", npc))
    k.sockets.append(("customer", (-0.45, -1.95, 0.0)))
    k.sockets.append(("light_a", light))
    k.sockets.append(("light_b", (-0.9, 0.9, 2.0)))
    k.col_box(xc1 - xc0 + 0.1, yc1 - yc0, zc + 0.3, T((xc0 + xc1) / 2, ycm, (zc + 0.3) / 2))
    k.col_box(W - 0.2, 0.4, 2.2, T(0, yb, 1.1))
    k.col_box(0.6, 1.1, 1.0, T(-1.98, -0.8, 0.5))
    k.col_box(0.7, 0.9, 1.1, T(-1.8, 0.55, 0.55))
    k.col_box(0.95, 0.95, 1.2, T(1.7, -0.82, 0.6))
    k.col_box(0.6, 0.6, 1.0, T(1.85, 0.4, 0.5))
    for sx in (-1, 1):
        k.col_box(0.2, 0.2, 2.2, T(sx * 2.05, yf, 1.1))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# arcana / lapidary helpers
def hexv(R_, i, z=0.0):
    """Vertex i of a hexagon with a flat side facing -Y (between vertices 4 and 5)."""
    a = math.radians(60 * i)
    return Vector((R_ * math.cos(a), R_ * math.sin(a), z))


def crescent_pts(R_=1.0, ratio=0.84, d=0.36, n=10, rot=0.0, cx=0.0, cy=0.0):
    """Crescent outline (outer circle minus an inner circle shifted by d*R toward +X), CCW, rotated by rot degrees."""
    r_ = ratio
    x = (1 - r_ * r_ + d * d) / (2 * d)
    y = math.sqrt(max(0.0, 1 - x * x))
    ao = math.atan2(y, x)
    ai = math.atan2(y, x - d)
    pts = [(math.cos(a), math.sin(a)) for a in [lerp(ao, math.tau - ao, i / n) for i in range(n + 1)]]
    pts += [(d + r_ * math.cos(a), r_ * math.sin(a)) for a in [lerp(math.tau - ai, ai, i / n) for i in range(1, n)]]
    c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(cx + (px * c - py * s_) * R_, cy + (px * s_ + py * c) * R_) for px, py in pts]


def star_pts(ro, ri, n=5, cx=0.0, cy=0.0):
    return [(cx + math.cos(math.radians(90 + 180 / n * j)) * (ro if j % 2 == 0 else ri),
             cy + math.sin(math.radians(90 + 180 / n * j)) * (ro if j % 2 == 0 else ri)) for j in range(2 * n)]


def crescent_star(k, M, s=1.0, mat="BH_Gold"):
    """Crescent moon (horns up-right) with a five-point star in its hollow, relief in the XZ plane facing -Y; origin
    at the crescent's bottom."""
    k.put(prism(crescent_pts(0.2 * s, 0.8, 0.42, 12, 40, 0.0, 0.2 * s), 0.035 * s), mat, M=M, tint=0.95)
    k.put(prism(star_pts(0.075 * s, 0.032 * s, 5, 0.1 * s, 0.3 * s), 0.03 * s), mat, M=M, tint=1.0)


def crystal(k, M, mat, h=0.16, r=0.028, segs=6):
    """Single hexagonal crystal with a pointed tip; origin at the base, grows along +Z."""
    k.put(cyl(r, h * 0.75, segs, caps=False), mat, M=M, uvoff=False)
    k.put(cyl(r, h * 0.25, segs, r2=0.0, caps=False), mat, M=M @ T(0, 0, h * 0.75), uvoff=False)


def crystal_cluster(k, M, mat, n=5, h=0.2, r=0.03, base=True):
    rr = k.r
    if base:
        t = cyl(r * 2.6, r * 1.5, 6, r2=r * 1.6)
        jitter(t, rr, r * 0.4)
        k.put(t, "BH_StoneDark", M=M, tint=0.6)
    for i in range(n):
        a = rr.uniform(0, 360)
        tilt = 0 if i == 0 else rr.uniform(18, 42)
        hh = h * (1.0 if i == 0 else rr.uniform(0.45, 0.8))
        crystal(k, M @ TRS(0, 0, r * 0.8, 0, 0, a) @ R(tilt, 0, 0) @ R(0, 0, rr.uniform(0, 60)), mat, hh,
                r * (1.0 if i == 0 else rr.uniform(0.6, 0.85)))


def cut_gem(k, M, mat, r=0.03):
    k.put(cyl(r, r * 0.5, 6, r2=r * 0.6, caps=False), mat, M=M @ T(0, 0, r * 0.7), uvoff=False)
    k.put(cyl(r, r * 0.7, 6, r2=0.0, caps=False), mat, M=M @ TRS(0, 0, r * 0.7, 180, 0, 0), uvoff=False)
    k.put(cyl(r * 0.6, 0.001, 6), mat, M=M @ T(0, 0, r * 1.2), uvoff=False)


def ring_jewel(k, M, gem="BH_GemRed", r=0.028):
    k.put(torus(r, 0.006, 10, 3), "BH_Gold", M=M @ TRS(0, 0, r, 90, 0, k.r.uniform(0, 180)))
    k.put(ico(0.009, 0), gem, M=M @ T(0, 0, 2 * r + 0.004))


def amulet(k, M, gem="BH_GemAqua", r=0.04):
    """Amulet lying flat: gold disc with a set stone, chain loop."""
    k.put(cyl(r, 0.01, 8), "BH_Gold", M=M)
    k.put(cyl(r * 0.45, 0.012, 6), gem, M=M @ T(0, 0, 0.006))
    k.put(torus(r * 1.6, 0.003, 12, 3), "BH_Gold", M=M @ T(r * 1.5, 0, 0.004) @ S(1.0, 0.7, 1.0))


def staff(k, M, L=1.9, head="crystal", gem="BH_GemViolet"):
    """Staff standing on its foot (origin), shaft along +Z with a distinct head."""
    rr = k.r
    pts = [(0, 0, 0)]
    for i in range(1, 5):
        pts.append((rr.uniform(-0.012, 0.012), rr.uniform(-0.012, 0.012), L * i / 5))
    pts.append((0, 0, L))
    k.put(tube(pts, [0.022, 0.024, 0.024, 0.022, 0.022, 0.026], 5), "BH_WoodDark" if head != "gnarl" else "BH_Bark",
          M=M, tint=0.6, smooth=40)
    k.put(cyl(0.028, 0.06, 6), "BH_Iron", M=M)  # ferrule
    top = M @ T(0, 0, L)
    if head == "crystal":
        for a in (0, 120, 240):  # three prongs holding a crystal
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            k.put(tube([(0, 0, -0.02), (ca * 0.05, sa * 0.05, 0.08), (ca * 0.03, sa * 0.03, 0.2)], 0.008, 4),
                  "BH_Gold", M=top)
        crystal(k, top @ T(0, 0, 0.02), gem, 0.24, 0.035)
    elif head == "crescent":
        k.put(cyl(0.03, 0.05, 6), "BH_Gold", M=top)
        crescent_star(k, top @ T(0.0, 0, 0.03), 0.55)
    elif head == "orb":
        k.put(torus(0.07, 0.009, 12, 3), "BH_Gold", M=top @ TRS(0, 0, 0.09, 90, 0, 0))
        k.put(torus(0.07, 0.009, 12, 3), "BH_Gold", M=top @ TRS(0, 0, 0.09, 90, 0, 90))
        k.put(ico(0.05, 1), gem, M=top @ T(0, 0, 0.09), smooth=50)
    else:  # gnarled root head clutching a stone
        for a in (0, 90, 180, 270):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            cb, sb = math.cos(math.radians(a + 40)), math.sin(math.radians(a + 40))
            k.put(tube([(0, 0, -0.05), (ca * 0.06, sa * 0.06, 0.06), (cb * 0.03, sb * 0.03, 0.14)],
                       [0.018, 0.014, 0.006], 4), "BH_Bark", M=top, tint=0.7)
        k.put(ico(0.04, 1), gem, M=top @ T(0, 0, 0.07))


def drape(k, M, r=0.4, h=0.78, mat="BH_ClothBlue", folds=9, flare=0.08):
    """Round table under a cloth: flat top disc + skirt with folds to the floor."""
    n = folds * 2
    t = tb()
    rows = []
    prof = [(r, h), (r + 0.02, h - 0.05), (r + flare * 0.5, h * 0.5), (r + flare, 0.01)]
    for (rad, z) in prof:
        row = []
        for i in range(n):
            a = math.tau * i / n
            dr = (0.035 if i % 2 == 0 else -0.01) * (1.0 - z / h) + (0.012 if i % 2 == 0 else 0.0)
            row.append(t.verts.new((math.cos(a) * (rad + dr), math.sin(a) * (rad + dr), z)))
        rows.append(row)
    for j in range(len(rows) - 1):
        for i in range(n):
            t.faces.new((rows[j][i], rows[j][(i + 1) % n], rows[j + 1][(i + 1) % n], rows[j + 1][i]))
    t.faces.new(rows[0])
    bmesh.ops.recalc_face_normals(t, faces=t.faces)
    k.put(t, mat, M=M, tint=0.85, smooth=35)


def curtain(a, b, z_top, folds=5, amp=0.05, gather=None, tie=0.55, z_bot=0.02):
    """Surface fn for a hanging curtain from a to b (floor points). gather = 0/1 pulls it to that end below the top
    (tied back)."""
    def fn(u, v):
        if gather is None:
            uu = u
        else:
            if v <= tie:
                w = lerp(1.0, 0.16, (v / tie) ** 0.4)
            else:
                w = lerp(0.16, 0.34, (v - tie) / (1 - tie))
            uu = gather + (u - gather) * w
        p = a.lerp(b, uu)
        d = (b - a).normalized()
        nrm = Vector((d.y, -d.x, 0.0))
        f = math.sin(u * math.pi * 2 * folds) * amp * (1.0 if gather is None else 0.7)
        p = p + nrm * f
        return (p.x, p.y, lerp(z_top, z_bot, v))
    return fn


@asset("stand_arcana", "market")
def stand_arcana(k):
    """Seris, Aether Mystic. Round 4.2. Violet six-sided pavilion on carved posts, gold crescent-and-star finial,
    front curtain parted and tied back; crystal ball table in the entrance, staff rack and a casket of rings outside."""
    r = k.r
    Rp, Re = 1.84, 2.08      # post / eave vertex radius
    ze, za = 2.78, 4.42      # eave, apex heights

    # --- floor: wine rug with a violet centre
    k.put(flat_poly([(hexv(1.62, i).x, hexv(1.62, i).y) for i in range(6)], 0.012), "BH_Velvet", tint=0.8)
    k.put(flat_poly([(hexv(1.25, i).x, hexv(1.25, i).y) for i in range(6)], 0.016), "BH_ClothViolet", tint=0.8)

    # --- carved posts with gilded bands, eave plate between them
    prof = [(0.1, 0.0), (0.11, 0.08), (0.08, 0.16), (0.07, 0.3), (0.075, 1.05), (0.095, 1.12), (0.075, 1.2),
            (0.068, 2.2), (0.09, 2.36), (0.1, 2.5), (0.075, ze - 0.12)]
    for i in range(6):
        p = hexv(Rp, i)
        footing(k, p.x, p.y, 0.32, 0.1)
        k.put(lathe(prof, 8), "BH_WoodDark", M=T(p.x, p.y, 0.08), tint=0.6, smooth=45)
        for z in (1.12, 2.36):
            k.put(cyl(0.098, 0.04, 8, caps=False), "BH_Gold", M=T(p.x, p.y, z + 0.06))
        q = hexv(Rp, i + 1)
        beam(k, (p.x, p.y, ze - 0.1), (q.x, q.y, ze - 0.1), 0.1, 0.12, tint=0.5)

    # --- roof: six sagging fabric panels on a concave (bell) pavilion profile, gold cords over the ribs
    def rad_at(v):
        return Re * (1.0 - v) ** 1.35 + 0.05 * v

    def z_at(v):
        return ze + (za - ze) * v

    for i in range(6):
        def panel(u, v, i=i):
            a = hexv(rad_at(v), i)
            b = hexv(rad_at(v), i + 1)
            p = a.lerp(b, u)
            sag = 0.09 * math.sin(math.pi * u) * (1.0 - v) ** 0.7
            c = p.normalized() if p.length > 1e-6 else Vector((0, 0, 0))
            p = p - c * sag * 0.4
            return (p.x, p.y, z_at(v) - sag)
        surface(k, panel, 6, 8, "BH_ClothViolet", 0.025, 0.85)
        # gilt applique stars and small crescents sewn on each panel (follow the cloth)
        for (su, sv, kind) in ((0.3, 0.12, 0), (0.7, 0.2, 1), (0.5, 0.42, 0), (0.62, 0.66, 1), (0.25, 0.5, 2),
                               (0.78, 0.4, 2), (0.45, 0.8, 0)):
            su = su + r.uniform(-0.05, 0.05) + (0.03 if i % 2 else 0.0)
            px, py, pz = panel(su, sv)
            qx, qy, qz = panel(su, sv + 0.02)
            nz = Vector((qx - px, qy - py, qz - pz))
            tilt = math.degrees(math.atan2(nz.z, math.hypot(nz.x, nz.y)))
            yaw = math.degrees(math.atan2(qy - py, qx - px))
            Mst = T(px, py, pz + 0.014) @ R(0, 0, yaw - 90) @ R(tilt, 0, 0)
            if kind == 0:
                pts = star_pts(0.09, 0.037)
            elif kind == 1:
                pts = crescent_pts(0.085, 0.8, 0.42, 8, r.uniform(20, 70))
            else:
                pts = star_pts(0.05, 0.014, 4)
            k.put(prism([(x_, -y_) for x_, y_ in pts], 0.008), "BH_Gold", M=Mst @ R(90, 0, 0), tint=0.9, uvoff=False)
    for i in range(6):
        pts = [hexv(rad_at(v), i, z_at(v) + 0.012) for v in (0.0, 0.15, 0.35, 0.6, 0.85, 1.0)]
        k.put(tube(pts, 0.018, 5), "BH_Gold", tint=0.9, smooth=40)
    # scalloped valance, gold cord along its top, tassels at the corners
    for i in range(6):
        a0, b0 = hexv(Re + 0.01, i), hexv(Re + 0.01, i + 1)

        def val(u, v, a0=a0, b0=b0):
            p = a0.lerp(b0, u)
            depth = 0.1 + 0.12 * abs(math.sin(math.pi * u * 3))
            return (p.x, p.y, ze + 0.02 - v * depth)
        surface(k, val, 18, 1, "BH_ClothViolet", 0.018, 0.7)
        k.put(tube([a0 + Vector((0, 0, ze + 0.02)), b0 + Vector((0, 0, ze + 0.02))], 0.02, 5), "BH_Gold", tint=0.9)
        tz = ze - 0.02
        k.put(cyl(0.012, 0.08, 5), "BH_Gold", M=T(a0.x, a0.y, tz - 0.08))
        k.put(cyl(0.035, 0.14, 6, r2=0.012), "BH_Gold", M=T(a0.x, a0.y, tz - 0.22), tint=0.8)

    # --- finial: gilded collar, ball, spire and the crescent-and-star (top <= 5 m)
    k.put(cyl(0.08, 0.12, 8, r2=0.05), "BH_Gold", M=T(0, 0, za - 0.06))
    k.put(ico(0.085, 1), "BH_Gold", M=T(0, 0, za + 0.12), smooth=50)
    k.put(cyl(0.018, 0.14, 6), "BH_Gold", M=T(0, 0, za + 0.18))
    crescent_star(k, T(-0.03, 0, za + 0.3), 0.95)

    # --- curtain walls: back three closed, front-left/right closed, front parted and tied back
    zc = ze - 0.12
    for i in (0, 1, 2, 3, 5):
        a, b = hexv(Rp - 0.02, i), hexv(Rp - 0.02, i + 1)
        surface(k, curtain(a, b, zc, 4, 0.05), 16, 3, "BH_ClothViolet", 0.02, 0.7)
    pL, pR = hexv(Rp - 0.02, 4), hexv(Rp - 0.02, 5)
    mid = (pL + pR) / 2
    surface(k, curtain(pL, mid, zc, 3, 0.05, gather=0.0), 12, 8, "BH_ClothViolet", 0.02, 0.75)
    surface(k, curtain(mid, pR, zc, 3, 0.05, gather=1.0), 12, 8, "BH_ClothViolet", 0.02, 0.75)
    zt_ = zc - (zc - 0.02) * 0.55
    for p, sx in ((pL, 1), (pR, -1)):
        k.put(torus(0.1, 0.018, 10, 4), "BH_Gold", M=T(p.x + sx * 0.1, p.y, zt_) @ S(1.0, 0.6, 1.0))
        k.put(cyl(0.012, 0.3, 5), "BH_Gold", M=TRS(p.x + sx * 0.18, p.y - 0.03, zt_ - 0.3, 0, sx * 8, 0))
        k.put(cyl(0.03, 0.1, 6, r2=0.01), "BH_Gold", M=T(p.x + sx * 0.22, p.y - 0.03, zt_ - 0.4), tint=0.8)
    k.put(tube([pL + Vector((0, -0.04, zc)), pR + Vector((0, -0.04, zc))], 0.02, 6), "BH_Gold", tint=0.8)

    # --- in the entrance: round draped table with the crystal ball, star chart, candles, mana draughts
    tx, ty = 0.44, -0.98
    drape(k, T(tx, ty, 0.0), 0.4, 0.78, "BH_ClothBlue", 9)
    zt = 0.79
    for a in (0, 120, 240):  # gilded claw stand
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        k.put(tube([(0, 0, 0.0), (ca * 0.08, sa * 0.08, 0.05), (ca * 0.07, sa * 0.07, 0.11)], 0.012, 4), "BH_Gold",
              M=T(tx, ty, zt))
    k.put(cyl(0.06, 0.03, 8), "BH_Gold", M=T(tx, ty, zt))
    k.put(ico(0.135, 2), "BH_GemViolet", M=T(tx, ty, zt + 0.16), smooth=60)
    k.put(box(0.34, 0.26, 0.004), "BH_Paper", M=TRS(tx - 0.14, ty - 0.2, zt + 0.004, 0, 0, 14), tint=0.9)
    for (dx, dy) in ((-0.05, -0.05), (0.06, 0.02), (-0.1, 0.06), (0.1, -0.08), (0.0, 0.08), (-0.02, -0.1)):
        k.put(cyl(0.012, 0.004, 4), "BH_Gold", M=TRS(tx - 0.14 + dx, ty - 0.2 + dy, zt + 0.008, 0, 0, 45))
    k.put(cyl(0.022, 0.26, 8), "BH_Paper", M=TRS(tx - 0.2, ty - 0.37, zt, 0, 90, 14) @ T(0, 0, -0.13), tint=0.8)
    for (dx, dy, h) in ((0.24, 0.1, 0.18), (0.2, 0.2, 0.12), (-0.25, 0.12, 0.15)):
        k.put(cyl(0.035, 0.02, 8), "BH_Brass", M=T(tx + dx, ty + dy, zt))
        candle(k, T(tx + dx, ty + dy, zt + 0.02), h, 0.018)
    potion(k, T(tx + 0.12, ty + 0.26, zt), "BH_GemAqua", 0.2, 0.05, "round")
    potion(k, T(tx + 0.26, ty - 0.08, zt), "BH_GemAqua", 0.18, 0.04, "tall")

    # --- behind: a shelf of tomes, draughts and an armillary globe against the back curtain; floor cushions
    sy = hexv(Rp, 2).y - 0.3
    for z in (0.02, 0.62, 1.2):
        k.put(box(1.4, 0.34, 0.04, bev=0.01), "BH_WoodDark", M=T(0.0, sy, z + 0.02), tint=0.5)
    for sx in (-1, 1):
        k.put(box(0.05, 0.34, 1.6, bev=0.01), "BH_WoodDark", M=T(sx * 0.7, sy, 0.8), tint=0.45)
    x = -0.62
    while x < 0.6:
        w = r.uniform(0.05, 0.09)
        book(k, TRS(x + w / 2, sy, 0.64 + 0.13, 0, r.uniform(-6, 6), 0), w, 0.22, r.uniform(0.2, 0.28))
        x += w + 0.01
    for i, x in enumerate((-0.5, -0.25, 0.05, 0.3, 0.52)):
        potion(k, T(x, sy, 1.24), ("BH_GemAqua", "BH_GemViolet", "BH_GemAqua", "BH_GemGreen", "BH_GemAqua")[i],
               0.2, 0.05, ("round", "tall", "squat", "round", "tall")[i])
    for i in range(3):
        k.put(torus(0.14, 0.008, 14, 3), "BH_Brass", M=TRS(-0.35, sy, 0.24, 90, 0, 60 * i))
    k.put(ico(0.05, 1), "BH_GemGold", M=T(-0.35, sy, 0.24))
    k.put(cyl(0.02, 0.1, 6), "BH_Brass", M=T(-0.35, sy, 0.04))
    k.put(box(0.3, 0.26, 0.24, bev=0.02), "BH_WoodDark", M=T(0.35, sy, 0.16), tint=0.5)
    k.put(box(0.32, 0.28, 0.03), "BH_Gold", M=T(0.35, sy, 0.2))
    for (x, y) in ((-0.9, 0.1), (-0.75, 0.55)):
        k.put(cyl(0.26, 0.12, 8, r2=0.22), "BH_Velvet", M=T(x, y, 0.016), tint=0.8, smooth=50)

    # --- hanging brass lamp over the table (light_a) on a chain from the roof centre
    lx, ly, lz = tx * 0.85, ty * 0.85, 2.2
    k.put(tube([(0.0, 0.0, za - 0.3), (lx, ly, lz)], 0.008, 4), "BH_Iron")
    k.put(lathe([(0.0, -0.18), (0.1, -0.12), (0.12, -0.02), (0.06, 0.0)], 8), "BH_Brass", M=T(lx, ly, lz), smooth=45)
    k.put(cyl(0.06, 0.08, 6), "BH_Glass", M=T(lx, ly, lz - 0.26))
    light = (lx, ly, lz - 0.3)

    # --- outside front-left: staff rack
    rx, ry = -1.42, -1.25
    for dx in (-0.36, 0.36):
        k.put(box(0.07, 0.07, 1.25, bev=0.01), "BH_WoodDark", M=T(rx + dx, ry + 0.12, 0.62), tint=0.5)
        k.put(box(0.07, 0.5, 0.07, bev=0.01), "BH_WoodDark", M=T(rx + dx, ry, 0.04), tint=0.5)
    for z in (0.3, 1.2):
        k.put(box(0.82, 0.08, 0.06, bev=0.01), "BH_WoodDark", M=T(rx, ry + 0.12, z), tint=0.55)
    k.put(box(0.82, 0.3, 0.04, bev=0.01), "BH_WoodDark", M=T(rx, ry, 0.12), tint=0.5)
    heads = (("crystal", "BH_GemViolet"), ("crescent", None), ("orb", "BH_GemAqua"), ("gnarl", "BH_GemGreen"),
             ("crystal", "BH_GemAqua"))
    for i, (hd, gm) in enumerate(heads):
        x = rx - 0.28 + 0.14 * i
        staff(k, T(x, ry - 0.02, 0.14) @ R(-7, r.uniform(-3, 3), 0), r.uniform(1.65, 1.85), hd, gm or "BH_GemViolet")

    # --- outside front-right: draped side table with an open casket of rings, amulets and an amulet tree
    cx, cy = 1.42, -1.22
    rot = -18
    k.put(box(0.62, 0.46, 0.05, bev=0.01), "BH_WoodDark", M=TRS(cx, cy, 0.76, 0, 0, rot), tint=0.5)
    for (dx, dy) in ((-0.26, -0.18), (0.26, -0.18), (-0.26, 0.18), (0.26, 0.18)):
        v = R(0, 0, rot) @ Vector((dx, dy, 0))
        k.put(cyl(0.025, 0.74, 6), "BH_WoodDark", M=T(cx + v.x, cy + v.y, 0.0), tint=0.45)
    k.put(box(0.66, 0.5, 0.012), "BH_Velvet", M=TRS(cx, cy, 0.79, 0, 0, rot), tint=0.8)
    for sx in (-1, 1):  # cloth hanging over the front and back edges
        def hang(u, v, sx=sx):
            p = R(0, 0, rot) @ Vector((lerp(-0.33, 0.33, u), sx * (0.25 + 0.012 * v), 0))
            return (cx + p.x, cy + p.y, 0.795 - 0.22 * v - 0.03 * math.sin(u * math.pi * 3) ** 2 * v)
        surface(k, hang, 8, 2, "BH_Velvet", 0.01, 0.75)
    Mc = TRS(cx - 0.05, cy + 0.02, 0.8, 0, 0, rot)
    k.put(box(0.3, 0.2, 0.1, bev=0.008), "BH_WoodDark", M=Mc @ T(0, 0, 0.05), tint=0.45)
    k.put(box(0.28, 0.18, 0.02), "BH_Velvet", M=Mc @ T(0, 0, 0.095), tint=0.7)
    for sx in (-1, 1):
        for sy_ in (-1, 1):
            k.put(box(0.03, 0.03, 0.105), "BH_Gold", M=Mc @ T(sx * 0.14, sy_ * 0.09, 0.052))
    Ml = Mc @ T(0, 0.1, 0.1) @ R(-105, 0, 0)
    k.put(box(0.3, 0.2, 0.05, bev=0.008), "BH_WoodDark", M=Ml @ T(0, 0.1, 0.0), tint=0.45)
    k.put(box(0.31, 0.03, 0.055), "BH_Gold", M=Ml @ T(0, 0.19, 0.0))
    gems = ("BH_GemRed", "BH_GemAqua", "BH_GemGreen", "BH_GemGold", "BH_GemViolet", "BH_GemAmber")
    for i in range(6):
        ring_jewel(k, Mc @ T(-0.1 + (i % 3) * 0.1, -0.045 + (i // 3) * 0.08, 0.1), gems[i], 0.022)
    amulet(k, TRS(cx - 0.2, cy - 0.16, 0.8, 0, 0, 20), "BH_GemAqua")
    amulet(k, TRS(cx + 0.2, cy - 0.12, 0.8, 0, 0, -40), "BH_GemViolet")
    tx2, ty2 = cx + 0.2, cy + 0.12
    k.put(cyl(0.05, 0.02, 8), "BH_Brass", M=T(tx2, ty2, 0.8))
    k.put(cyl(0.01, 0.34, 5), "BH_Brass", M=T(tx2, ty2, 0.8))
    k.put(cyl(0.008, 0.3, 5), "BH_Brass", M=TRS(tx2 - 0.15, ty2, 1.12, 0, 90, 0))
    for j, dx in enumerate((-0.12, 0.0, 0.12)):
        k.put(cyl(0.002, 0.12, 3), "BH_Gold", M=T(tx2 + dx, ty2, 1.0))
        k.put(cyl(0.03, 0.008, 8), "BH_Gold", M=TRS(tx2 + dx, ty2, 0.98, 90, 0, 0))
        k.put(ico(0.012, 0), gems[j + 2], M=T(tx2 + dx, ty2 - 0.008, 0.98))

    # --- a lantern hung from the front-right eave corner over the casket table (light_b)
    p5 = hexv(Re - 0.12, 5)
    k.put(torus(0.05, 0.01, 8, 3), "BH_Iron", M=TRS(p5.x, p5.y, ze - 0.02, 90, 0, 0))
    k.put(cyl(0.006, 0.3, 4), "BH_Iron", M=T(p5.x, p5.y, ze - 0.36))
    lp = hang_lantern(k, T(p5.x, p5.y, ze - 0.36), 0.42)
    light_b = (p5.x + lp[0], p5.y + lp[1], ze - 0.36 + lp[2])

    # --- crystal chimes from the front-left and right eave corners
    for i in (4, 0):
        p = hexv(Re - 0.08, i)
        for j in range(4):
            a = math.tau * j / 4
            hx, hy = p.x + math.cos(a) * 0.06, p.y + math.sin(a) * 0.06
            L = 0.28 + 0.1 * j
            k.put(cyl(0.003, L, 3), "BH_Silver", M=T(hx, hy, ze - 0.05 - L))
            crystal(k, T(hx, hy, ze - 0.05 - L) @ R(180, 0, 0), ("BH_GemAqua", "BH_GemViolet")[j % 2], 0.12, 0.014)
        k.put(torus(0.07, 0.006, 10, 3), "BH_Silver", M=T(p.x, p.y, ze - 0.05))

    # --- sockets and collision
    k.sockets.append(("npc", (-0.42, -1.45, 0.0)))
    k.sockets.append(("customer", (-0.3, -3.0, 0.0)))
    k.sockets.append(("light_b", light_b))
    k.sockets.append(("light_a", light))
    for i in range(6):
        p = hexv(Rp, i)
        k.col_box(0.26, 0.26, 2.2, T(p.x, p.y, 1.1))
    for i in (0, 1, 2, 3, 5):
        a, b = hexv(Rp, i), hexv(Rp, i + 1)
        m = (a + b) / 2
        k.col_box((b - a).length, 0.12, 2.2, T(m.x, m.y, 1.1) @ R(0, 0, math.degrees(math.atan2(b.y - a.y, b.x - a.x))))
    k.col_box(0.9, 0.9, 0.9, T(tx, ty, 0.45))
    k.col_box(0.9, 0.5, 1.3, T(rx, ry, 0.65))
    k.col_box(0.7, 0.55, 1.0, T(cx, cy, 0.5) @ R(0, 0, rot))
    k.col_box(1.5, 0.4, 1.6, T(0, sy, 0.8))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# lapidary helpers
GEMS6 = ("BH_GemAmber", "BH_GemAqua", "BH_GemGold", "BH_GemViolet", "BH_GemGreen", "BH_GemRed")


def geode(k, M, r=0.13, gem="BH_GemViolet"):
    """Half geode lying cut-face up: rough stone rind, glowing crystal lining (shallow bowl of points)."""
    t = ico(r, 1)
    slice_plane(t, (0, 0, 0.0), (0, 0, 1))
    jitter(t, k.r, r * 0.12)
    k.put(t, "BH_StoneDark", M=M @ T(0, 0, r * 0.95), tint=0.7)
    k.put(lathe([(r * 0.82, 0.0), (r * 0.55, -r * 0.35), (0.0, -r * 0.45)][::-1], 7, cap_bot=False, cap_top=False),
          gem, M=M @ T(0, 0, r * 0.96), smooth=None, uvoff=False)
    k.put(cyl(r * 0.84, 0.012, 7, r2=r * 0.9, caps=False), "BH_Stone", M=M @ T(0, 0, r * 0.94), tint=0.8)
    for i in range(5):
        a = math.tau * i / 5 + 0.3
        crystal(k, M @ T(math.cos(a) * r * 0.4, math.sin(a) * r * 0.4, r * 0.62) @ R(math.sin(a) * 30, -math.cos(a) * 30, 0),
                gem, r * 0.45, r * 0.09)


def ore_chunk(k, M, s=0.2, gem=None):
    t = rock(k.r, (s, s * 0.8, s * 0.6), cuts=5, subd=1, noise_amp=0.05, target=70)
    k.put(t, "BH_StoneDark", M=M, tint=k.r.uniform(0.55, 0.8))
    if gem:
        for i in range(3):
            crystal(k, M @ TRS(k.r.uniform(-s, s) * 0.3, k.r.uniform(-s, s) * 0.25, s * 0.45, k.r.uniform(-30, 30),
                               k.r.uniform(-30, 30), 0), gem, s * k.r.uniform(0.4, 0.7), s * 0.08)


@asset("stand_lapidary", "market")
def stand_lapidary(k):
    """Ysolde Marr, Lapidary (Socket Specialist). 3.8 x 3.0. Stone-footed timber booth under a steep single-pitch
    copper roof gone green, high on the left over a glowing crystal cabinet, low over the treadle gem-wheel on the
    right; lens arm, geodes and a tray of cut stones on the stone counter."""
    r = k.r
    W, D = 3.8, 3.0
    xL, xR = -1.72, 1.72     # wall/post lines
    yB, yF = 1.3, -1.22      # back wall line, front post line
    zL, zR = 4.72, 2.48      # roof top surface at x = -1.9 / +1.9

    def zroof(x):
        return zL + (zR - zL) * (x + 1.9) / 3.8
    slope = math.degrees(math.atan2(zL - zR, 3.8))

    # --- stone footing walls (back and both sides)
    masonry(k, xL - 0.15, xR + 0.15, 0.0, 0.6, 0.32, M=T(0, yB, 0), quoin="both", course=(0.26, 0.34), blen=(0.4, 0.75),
            chip_rng=(0, 1))
    for sx in (-1, 1):
        masonry(k, -0.35, yB - 0.16, 0.0, 0.6, 0.32, M=T(sx * xR, 0, 0) @ R(0, 0, 90), course=(0.26, 0.34),
                blen=(0.4, 0.75), chip_rng=(0, 1))
    # sill beams on the stone
    beam(k, (xL - 0.1, yB, 0.66), (xR + 0.1, yB, 0.66), 0.16, 0.12, tint=0.5)
    for sx in (-1, 1):
        beam(k, (sx * xR, -0.35, 0.66), (sx * xR, yB, 0.66), 0.16, 0.12, tint=0.5)

    # --- timber frame: corner posts, front posts, wall plates following the roof pitch
    for (x, y) in ((xL, yB), (xR, yB), (xL, -0.35), (xR, -0.35)):
        k.put(box(0.16, 0.16, zroof(x) - 0.2 - 0.6, bev=0.015), "BH_WoodDark", M=T(x, y, 0.6 + (zroof(x) - 0.8) / 2),
              tint=0.55)
    for x in (xL, xR):
        post(k, x, yF, zroof(x) - 0.18, 0.16)
    for y in (yB, yF, -0.35):
        beam(k, (-1.9, y, zroof(-1.9) - 0.26), (1.9, y, zroof(1.9) - 0.26), 0.14, 0.16, tint=0.5)
    for sx in (-1, 1):  # knee braces under the front beam
        x = sx * xR
        beam(k, (x, yF, zroof(x) - 0.95), (x - sx * 0.6, yF, zroof(x - sx * 0.6) - 0.3), 0.1, tint=0.5)
    # rafters down the slope, their ends showing at the eave
    for y in (yB, 0.45, -0.35, yF):
        beam(k, (-1.9, y, zroof(-1.9) - 0.12), (1.9, y, zroof(1.9) - 0.12), 0.1, 0.12, tint=0.55)

    # --- infill: vertical boards above the stone on the back and the sides (tall on the left, low on the right)
    nb = 11
    for i in range(nb):
        x = xL + 0.08 + (xR - xL - 0.16) * (i + 0.5) / nb
        top = zroof(x) - 0.3
        plank(k, (xR - xL - 0.16) / nb - 0.012, 0.04, top - 0.72, T(x, yB + 0.04, 0.72 + (top - 0.72) / 2), mat="BH_Wood",
              tint=(0.5, 0.72))
    for sx in (-1, 1):
        x = sx * (xR + 0.03)
        top = zroof(x) - 0.3
        n = 5
        for i in range(n):
            y = -0.35 + (yB + 0.35) * (i + 0.5) / n
            plank(k, (yB + 0.35) / n - 0.012, 0.04, top - 0.72, T(x, y, 0.72 + (top - 0.72) / 2) @ R(0, 0, 90),
                  mat="BH_Wood", tint=(0.5, 0.72))
        # mid rail
        beam(k, (x, -0.35, 1.9 if sx < 0 else 1.5), (x, yB, 1.9 if sx < 0 else 1.5), 0.08, 0.12, tint=0.5)
    # small shuttered window high in the tall left wall (light for the bench), shutter propped open
    k.put(box(0.1, 0.7, 0.6, bev=0.01), "BH_WoodDark", M=T(xL - 0.06, 0.5, 2.9), tint=0.45)
    k.put(box(0.12, 0.5, 0.42), "BH_StoneDark", M=T(xL - 0.07, 0.5, 2.9), tint=0.05)
    k.put(box(0.04, 0.55, 0.46, bev=0.01), "BH_Wood", M=T(xL - 0.14, 0.5, 3.14) @ R(0, -55, 0) @ T(0, 0, 0.23), tint=0.55)

    # --- the roof: boarded, sheathed in standing-seam copper gone green, copper drip edges
    Lr = math.hypot(3.8, zL - zR) + 0.04
    Mroof = T(0, 0, (zL + zR) / 2) @ R(0, slope, 0)   # local X down-slope toward +X, local Z = up from the roof
    k.put(box(Lr, D, 0.05), "BH_WoodDark", M=Mroof @ T(0, 0, -0.06), tint=0.4)
    nseam = 7
    for i in range(nseam):
        y = -D / 2 + D * (i + 0.5) / nseam
        t = box(Lr, D / nseam - 0.006, 0.02)
        subdiv(t, 1)
        jitter(t, r, 0.004, (0, 0, 1))
        k.put(t, "BH_Verdigris", M=Mroof @ T(0, y, -0.02), tint=0.9)
    for i in range(nseam + 1):
        y = -D / 2 + D * i / nseam
        k.put(box(Lr, 0.03, 0.05, bev=0.006), "BH_Verdigris", M=Mroof @ T(0, y, 0.0), tint=0.8)
    # two newer copper sheets let in where the old ones failed (still bright), nailed over the green
    for (x, i, L) in ((0.9, 2, 0.9), (-0.6, 5, 0.7)):
        y = -D / 2 + D * (i + 0.5) / nseam
        k.put(box(L, D / nseam - 0.05, 0.014), "BH_Copper", M=Mroof @ T(x, y, 0.003), tint=0.8)
        for sx in (-1, 1):
            for sy_ in (-1, 1):
                k.put(cyl(0.012, 0.01, 5), "BH_Iron", M=Mroof @ T(x + sx * (L / 2 - 0.05), y + sy_ * 0.15, 0.012))
    # ridge flashing at the high edge, copper drip at the low edge and down the front verge (bright where rubbed)
    k.put(box(0.1, D + 0.04, 0.12, bev=0.01), "BH_Verdigris", M=Mroof @ T(-Lr / 2 + 0.03, 0, -0.02), tint=0.7)
    k.put(cyl(0.035, D + 0.04, 8), "BH_Copper", M=Mroof @ TRS(Lr / 2, D / 2 + 0.02, -0.03, 90, 0, 0), smooth=40)
    k.put(box(Lr, 0.05, 0.1), "BH_Copper", M=Mroof @ T(0, -D / 2 - 0.02, -0.04), tint=0.7)
    # a downpipe from the low eave into a water butt at the back-right corner (the wheel's water)
    k.put(tube([(1.92, 1.2, zR - 0.08), (1.92, 1.2, 1.0)], 0.035, 6), "BH_Copper", smooth=40)
    barrel(k, T(1.95, 1.2, 0), 0.8, 0.26, tint=0.6, lid=False)
    k.put(cyl(0.23, 0.01, 9), "BH_Water", M=T(1.95, 1.2, 0.7))

    # --- the counter: dressed-stone base, thick oak top
    cx0, cx1 = -0.9, 1.02
    cy0, cy1 = -1.3, -0.84
    masonry(k, cx0, cx1, 0.0, 0.9, cy1 - cy0 - 0.06, M=T(0, (cy0 + cy1) / 2, 0), mat="BH_Stone", tint=(0.8, 1.0),
            course=(0.26, 0.34), blen=(0.35, 0.6), quoin=None, chip_rng=(0, 1))
    k.put(box(cx1 - cx0 + 0.12, cy1 - cy0 + 0.1, 0.1, bev=0.02), "BH_WoodDark", M=T((cx0 + cx1) / 2, (cy0 + cy1) / 2, 0.95),
          tint=0.55)
    zc = 1.0
    # velvet tray of cut stones in all six colours
    k.put(box(0.44, 0.3, 0.035, bev=0.008), "BH_WoodDark", M=TRS(-0.4, -1.12, zc + 0.017, 0, 0, 4), tint=0.4)
    k.put(box(0.4, 0.26, 0.01), "BH_Velvet", M=TRS(-0.4, -1.12, zc + 0.03, 0, 0, 4), tint=0.8)
    for i in range(12):
        gx = -0.55 + (i % 4) * 0.1 + r.uniform(-0.015, 0.015)
        gy = -1.2 + (i // 4) * 0.08 + r.uniform(-0.01, 0.01)
        cut_gem(k, TRS(gx, gy, zc + 0.035, r.uniform(-15, 15), r.uniform(-15, 15), r.uniform(0, 60)), GEMS6[i % 6], 0.026)
    # geode halves and a big cluster
    geode(k, TRS(0.02, -1.08, zc, 0, 0, 20), 0.14, "BH_GemViolet")
    geode(k, TRS(0.3, -0.96, zc, 0, 0, 80), 0.1, "BH_GemAqua")
    crystal_cluster(k, TRS(-0.72, -0.98, zc, 0, 0, 10), "BH_GemGreen", 5, 0.2, 0.03)
    # bench block (small anvil), a hammer, tongs and chisels
    k.put(box(0.16, 0.12, 0.1, bev=0.008), "BH_Iron", M=TRS(0.72, -1.06, zc + 0.05, 0, 0, 10))
    k.put(cyl(0.03, 0.08, 6, r2=0.0), "BH_Iron", M=TRS(0.72, -1.06, zc + 0.09, 0, -90, 10) @ T(0, 0, 0.08))
    k.put(cyl(0.012, 0.22, 5), "BH_WoodDark", M=TRS(0.55, -1.18, zc + 0.012, 0, 90, 30), tint=0.6)
    k.put(box(0.07, 0.03, 0.03), "BH_Iron", M=TRS(0.55, -1.18, zc + 0.02, 0, 0, 30) @ T(0.2, 0, 0))
    for j, a in enumerate((12, 20)):
        k.put(box(0.2, 0.012, 0.01), "BH_Iron", M=TRS(0.85, -0.96 + j * 0.012, zc + 0.012, 0, 0, a))
    for j in range(3):
        k.put(box(0.12, 0.012, 0.012), "BH_Iron", M=TRS(0.2 + j * 0.05, -1.24, zc + 0.008, 0, 0, 80 + j * 5))
        k.put(cyl(0.012, 0.07, 5), "BH_Wood", M=TRS(0.2 + j * 0.05, -1.24, zc + 0.012, 0, 0, 80 + j * 5) @ TRS(0.0, 0.06, 0, 90, 0, 0),
              tint=0.6)
    # the big brass lens on an articulated arm, clamped to the counter's back edge
    ax, ay = 0.42, -0.88
    k.put(box(0.1, 0.1, 0.08, bev=0.01), "BH_Brass", M=T(ax, ay, zc + 0.04))
    p0 = Vector((ax, ay, zc + 0.08))
    p1 = Vector((ax - 0.05, ay + 0.05, zc + 0.62))
    p2 = Vector((ax - 0.2, ay - 0.18, zc + 0.46))
    for a_, b_ in ((p0, p1), (p1, p2)):
        pole(k, a_, b_, 0.014, "BH_Brass")
    for p in (p1, p2):
        k.put(ico(0.028, 1), "BH_Brass", M=T(*p), smooth=50)
    lens_c = p2 + Vector((0.0, -0.1, -0.04))
    Ml = T(*lens_c) @ R(55, 0, 0)
    k.put(torus(0.11, 0.014, 16, 4), "BH_Brass", M=Ml, smooth=40)
    k.put(cyl(0.1, 0.012, 16), "BH_Water", M=Ml @ T(0, 0, -0.006), uvoff=False)
    pole(k, p2, lens_c + Vector((0, 0.1, 0.02)), 0.012, "BH_Brass")
    # a candle on a dish by the lens
    k.put(cyl(0.05, 0.015, 8), "BH_Brass", M=T(0.82, -1.2, zc))
    candle(k, T(0.82, -1.2, zc + 0.015), 0.12, 0.02)

    # --- glass-fronted display cabinet of glowing crystals under the high side of the roof (left)
    bx0, bx1 = -1.66, -0.98
    by0, by1 = -1.26, -0.82
    bh = 2.05
    bcx, bcy = (bx0 + bx1) / 2, (by0 + by1) / 2
    k.put(box(bx1 - bx0 + 0.06, by1 - by0 + 0.04, 0.12, bev=0.01), "BH_WoodDark", M=T(bcx, bcy, 0.06), tint=0.45)
    for sx in (-1, 1):
        k.put(box(0.05, by1 - by0, bh - 0.12, bev=0.006), "BH_WoodDark", M=T(bcx + sx * ((bx1 - bx0) / 2 - 0.025), bcy,
                                                                             0.12 + (bh - 0.12) / 2), tint=0.5)
    k.put(box(bx1 - bx0, 0.03, bh - 0.12), "BH_WoodDark", M=T(bcx, by1 - 0.015, 0.12 + (bh - 0.12) / 2), tint=0.3)
    k.put(box(bx1 - bx0 + 0.1, by1 - by0 + 0.08, 0.1, bev=0.015), "BH_WoodDark", M=T(bcx, bcy, bh + 0.05), tint=0.5)
    k.put(box(bx1 - bx0 + 0.02, by1 - by0 + 0.02, 0.06, bev=0.01), "BH_Brass", M=T(bcx, bcy, bh - 0.01))
    shelves = (0.5, 0.88, 1.26, 1.64)
    for z in shelves:
        k.put(box(bx1 - bx0 - 0.08, by1 - by0 - 0.04, 0.025), "BH_Wood", M=T(bcx, bcy, z), tint=0.55)
    # glazing: door frames with glazing bars (the panes themselves are left open so the stones read)
    for sx in (-1, 1):
        dxc = bcx + sx * (bx1 - bx0) / 4
        for z in (0.14, bh - 0.02):
            k.put(box((bx1 - bx0) / 2 - 0.01, 0.03, 0.04), "BH_WoodDark", M=T(dxc, by0 - 0.01, z), tint=0.5)
        k.put(box(0.03, 0.03, bh - 0.14), "BH_WoodDark", M=T(dxc + sx * ((bx1 - bx0) / 4 - 0.02), by0 - 0.01, 0.12 + (bh - 0.14) / 2),
              tint=0.5)
        for z in (0.69, 1.07, 1.45, 1.83):
            k.put(box((bx1 - bx0) / 2 - 0.02, 0.012, 0.012), "BH_Brass", M=T(dxc, by0 - 0.012, z))
    k.put(box(0.03, 0.03, bh - 0.14), "BH_WoodDark", M=T(bcx, by0 - 0.01, 0.12 + (bh - 0.14) / 2), tint=0.45)
    k.put(cyl(0.012, 0.04, 6), "BH_Brass", M=TRS(bcx + 0.03, by0 - 0.03, 1.1, 90, 0, 0))
    for si, z in enumerate(shelves):
        for j in range(3):
            gx = bx0 + 0.12 + j * 0.21
            mat = GEMS6[(si * 3 + j) % 6]
            if si == 0 and j == 1:
                geode(k, TRS(gx, bcy - 0.02, z + 0.012, 0, 0, 30), 0.09, mat)
                continue
            crystal_cluster(k, TRS(gx, bcy - 0.02, z + 0.012, 0, 0, r.uniform(0, 60)), mat, 4, 0.19 if si < 3 else 0.15,
                            0.026)
    for j in range(3):  # loose crystals on top of the cabinet
        crystal_cluster(k, TRS(bx0 + 0.14 + j * 0.2, bcy, bh + 0.1, 0, 0, r.uniform(0, 60)), GEMS6[(j * 2 + 1) % 6], 3,
                        0.16, 0.024)

    # --- treadle gem-wheel at the right end of the counter (wheel faces the customer)
    wx, wy = 1.42, -0.95
    for sy_ in (-1, 1):  # A-frame sides (front and back)
        y = wy + sy_ * 0.16
        beam(k, (wx - 0.26, y, 0.0), (wx - 0.03, y, 1.02), 0.06, tint=0.5)
        beam(k, (wx + 0.26, y, 0.0), (wx + 0.03, y, 1.02), 0.06, tint=0.5)
        beam(k, (wx - 0.28, y, 0.05), (wx + 0.28, y, 0.05), 0.07, tint=0.5)
    k.put(box(0.34, 0.44, 0.05, bev=0.01), "BH_WoodDark", M=T(wx + 0.08, wy, 1.03), tint=0.5)  # bench top
    k.put(cyl(0.018, 0.46, 6), "BH_Iron", M=TRS(wx, wy + 0.23, 1.28, 90, 0, 0))            # spindle along Y
    k.put(cyl(0.22, 0.06, 18), "BH_Stone", M=TRS(wx, wy - 0.1, 1.28, 90, 0, 0), tint=0.9, uvoff=False)  # lap
    k.put(cyl(0.05, 0.03, 10), "BH_Iron", M=TRS(wx, wy - 0.115, 1.28, 90, 0, 0))
    k.put(cyl(0.06, 0.06, 10), "BH_Wood", M=TRS(wx, wy + 0.16, 1.28, 90, 0, 0), tint=0.6)  # pulley
    for sy_ in (-1, 1):  # spindle bearings
        k.put(box(0.07, 0.05, 0.25), "BH_WoodDark", M=T(wx, wy + 0.05 + sy_ * 0.08, 1.16), tint=0.45)
    k.put(box(0.3, 0.05, 0.12, bev=0.01), "BH_WoodDark", M=T(wx, wy - 0.02, 1.47) @ R(-20, 0, 0), tint=0.4)  # splash hood
    # flywheel below, crank, treadle and the belt
    wheel(k, T(wx, wy + 0.16, 0.42), 0.3, 6)
    k.put(tube([(wx - 0.3, wy + 0.2, 0.42), (wx - 0.06, wy + 0.18, 1.28)], 0.009, 3), "BH_Leather")
    k.put(tube([(wx + 0.3, wy + 0.2, 0.42), (wx + 0.06, wy + 0.18, 1.28)], 0.009, 3), "BH_Leather")
    beam(k, (wx + 0.14, wy + 0.3, 0.42), (wx + 0.18, wy + 0.3, 0.1), 0.03, tint=0.5)
    plank(k, 0.6, 0.12, 0.04, TRS(wx + 0.05, wy + 0.3, 0.08, 0, 6, 0), mat="BH_WoodDark")
    # water drip can over the wheel, bucket at its foot, a stool behind
    k.put(cyl(0.012, 0.42, 5), "BH_Iron", M=T(wx + 0.2, wy - 0.02, 1.05))
    k.put(tube([(wx + 0.2, wy - 0.02, 1.47), (wx + 0.08, wy - 0.06, 1.55)], 0.01, 4), "BH_Iron")
    k.put(cyl(0.05, 0.08, 8, r2=0.03), "BH_Copper", M=T(wx + 0.06, wy - 0.06, 1.52), smooth=40)
    k.put(cyl(0.14, 0.24, 8, r2=0.16), "BH_Wood", M=T(wx - 0.02, wy - 0.46, 0.0), tint=0.6)
    k.put(cyl(0.165, 0.025, 8, caps=False), "BH_Iron", M=T(wx - 0.02, wy - 0.46, 0.18))
    k.put(cyl(0.14, 0.01, 8), "BH_Water", M=T(wx - 0.02, wy - 0.46, 0.2))
    k.put(cyl(0.16, 0.05, 8), "BH_WoodDark", M=T(wx, wy + 0.62, 0.55), tint=0.5)
    for a in (0, 120, 240):
        beam(k, (wx, wy + 0.62, 0.55), (wx + math.cos(math.radians(a)) * 0.16, wy + 0.62 + math.sin(math.radians(a)) * 0.16, 0.0),
             0.035, tint=0.5)

    # --- a pendant bar under the high eave: cut crystals on threads catching the light
    for x in (-1.55, -0.72):
        k.put(tube([(x, yF, zroof(x) - 0.34), (x, yF - 0.02, 2.62)], 0.006, 3), "BH_Iron")
    k.put(cyl(0.02, 0.95, 6), "BH_WoodDark", M=TRS(-1.61, yF - 0.02, 2.6, 0, 90, 0), tint=0.5)
    for j in range(7):
        x = -1.52 + j * 0.13
        L = 0.18 + 0.12 * ((j * 3) % 4)
        k.put(cyl(0.003, L, 3), "BH_Silver", M=T(x, yF - 0.02, 2.6 - L))
        crystal(k, T(x, yF - 0.02, 2.6 - L) @ R(180, 0, 0), GEMS6[j % 6], 0.13, 0.018)

    # --- back: shelf of rough ore, tool rack, a chest of uncut stones
    for z in (1.2, 1.7):
        k.put(box(1.8, 0.28, 0.04, bev=0.008), "BH_WoodDark", M=T(0.3, yB - 0.2, z), tint=0.5)
    for i in range(5):
        ore_chunk(k, TRS(-0.4 + i * 0.32, yB - 0.2, 1.22, 0, 0, r.uniform(0, 90)), 0.14, GEMS6[i % 6] if i % 2 == 0 else None)
    for i in range(6):
        x = -0.4 + i * 0.3
        k.put(cyl(0.012, 0.3, 5), "BH_WoodDark", M=T(x, yB - 0.12, 1.4), tint=0.5)  # peg
        k.put(box(0.1, 0.03, 0.05), "BH_Iron", M=T(x, yB - 0.12, 1.4))
    k.put(box(0.7, 0.45, 0.42, bev=0.02), "BH_WoodDark", M=TRS(-0.9, yB - 0.4, 0.21, 0, 0, 4), tint=0.45)
    for (dx, dy, g) in ((-0.15, 0.0, "BH_GemAmber"), (0.1, 0.05, None), (0.2, -0.1, "BH_GemAqua")):
        ore_chunk(k, TRS(-0.9 + dx, yB - 0.4 + dy, 0.4, 0, 0, r.uniform(0, 90)), 0.15, g)

    # --- in front: a crate of raw crystal ore beside the wheel
    ox, oy = 1.4, -1.36
    crate_open(k, TRS(ox, oy - 0.02, 0.0, 0, 0, -6), 0.5, 0.26, 0.28, straw=False)
    for (dx, g) in ((-0.13, "BH_GemAqua"), (0.02, "BH_GemViolet"), (0.15, "BH_GemAmber")):
        ore_chunk(k, TRS(ox + dx, oy - 0.02, 0.22, 0, 0, r.uniform(0, 90)), 0.13, g)

    # --- lantern from the front beam (light_a); light_b in front of the crystal cabinet
    lx = 0.35
    lz = zroof(lx) - 0.34
    light = lantern_on_hook(k, lx, yF, lz, 0.5)
    k.put(box(0.03, 0.03, 0.12), "BH_Iron", M=T(lx, yF, lz + 0.05))

    # --- sockets and collision
    k.sockets.append(("npc", (-0.28, -0.36, 0.0)))
    k.sockets.append(("customer", (-0.2, -1.95, 0.0)))
    k.sockets.append(("light_a", light))
    k.sockets.append(("light_b", (bcx, by0 - 0.4, 2.2)))
    k.col_box(cx1 - cx0 + 0.12, cy1 - cy0 + 0.1, 1.0, T((cx0 + cx1) / 2, (cy0 + cy1) / 2, 0.5))
    k.col_box(bx1 - bx0 + 0.1, by1 - by0 + 0.08, 2.2, T(bcx, bcy, 1.1))
    k.col_box(0.55, 0.65, 1.3, T(wx, wy, 0.65))
    k.col_box(W - 0.1, 0.36, 2.2, T(0, yB, 1.1))
    for sx in (-1, 1):
        k.col_box(0.34, yB + 0.35, 2.2, T(sx * xR, (yB - 0.35) / 2, 1.1))
        k.col_box(0.22, 0.22, 2.2, T(sx * xR, yF, 1.1))
    k.col_box(0.55, 0.32, 0.5, T(ox, oy, 0.25))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# smithy helpers
from masonry import split_lengths  # noqa
from assets_town2 import chimney  # noqa


def axe(k, M, L=0.8, bearded=False):
    """Hand axe standing on its butt (origin), haft along +Z, blade in the XZ plane pointing +X (faces -Y)."""
    k.put(cyl(0.017, L, 6, r2=0.02), "BH_Wood", M=M, tint=0.6, smooth=40)
    if bearded:
        out = [(0.0, -0.02), (0.05, -0.03), (0.12, -0.16), (0.2, -0.12), (0.2, 0.09), (0.05, 0.05), (0.0, 0.06)]
    else:
        out = [(0.0, -0.03), (0.06, -0.035), (0.17, -0.1), (0.2, -0.08), (0.2, 0.09), (0.17, 0.1), (0.06, 0.04),
               (0.0, 0.04)]
    k.put(prism(out, 0.022, bev=0.004), "BH_Metal", M=M @ T(0.0, 0, L - 0.07), tint=0.8)
    k.put(box(0.06, 0.05, 0.08, bev=0.006), "BH_Iron", M=M @ T(-0.005, 0, L - 0.07))


def heater_shield(k, M, s=1.0, face="BH_ClothBlue", device="BH_Gold"):
    """Heater shield hung face toward -Y (origin at its centre), painted field with a plain chevron device."""
    out = [(-0.25, 0.3), (0.25, 0.3), (0.25, 0.02), (0.17, -0.18), (0.0, -0.33), (-0.17, -0.18), (-0.25, 0.02)]
    out = [(x * s, z * s) for x, z in out]
    k.put(prism(out, 0.04 * s, bev=0.008), "BH_Wood", M=M, tint=0.6)
    k.put(prism([(x * 0.9, z * 0.9 + 0.01 * s) for x, z in out], 0.01), face, M=M @ T(0, -0.022 * s, 0), tint=0.85)
    chev = [(-0.2, -0.02), (0.0, 0.14), (0.2, -0.02), (0.2, -0.1), (0.0, 0.06), (-0.2, -0.1)]
    k.put(prism([(x * s, z * s) for x, z in chev], 0.012), device, M=M @ T(0, -0.03 * s, 0), tint=0.9)
    for (x, z) in ((-0.2, 0.26), (0.2, 0.26), (0.0, -0.28)):
        rivet(k, M @ TRS(x * s, -0.024 * s, z * s, 90, 0, 0), 0.014)


def shield_lite(k, M, R_=0.3, face="BH_Wood"):
    """Cheaper round shield for the back wall: board, iron rim, boss."""
    k.put(cyl(R_, 0.04, 12), face, M=M, tint=0.65)
    k.put(torus(R_, 0.016, 12, 3), "BH_Iron", M=M @ T(0, 0, 0.02))
    k.put(ico(0.06, 1), "BH_Iron", M=M @ TRS(0, 0, 0.04, s=(1, 1, 0.55)))


def hammer(k, M, L=0.4, head=0.15, sledge=False):
    """Smith's hammer lying/standing along +Z from the handle end (origin)."""
    k.put(cyl(0.015, L, 6, r2=0.018), "BH_Wood", M=M, tint=0.55)
    if sledge:
        k.put(box(0.2, 0.075, 0.075, bev=0.01), "BH_Iron", M=M @ T(0, 0, L))
    else:
        k.put(box(head * 0.55, 0.045, 0.045, bev=0.006), "BH_Iron", M=M @ T(-head * 0.2, 0, L))
        k.put(cyl(0.02, head * 0.45, 6, r2=0.008), "BH_Iron", M=M @ TRS(head * 0.05, 0, L, 0, 90, 0))


def tongs(k, M, L=0.6, open_=6.0):
    """Blacksmith's tongs: two reins along +Z from the handle ends (origin) to curved jaws at the top."""
    for sx in (-1, 1):
        a = sx * open_ * 0.5
        pts = [(sx * 0.02, 0, 0.0), (sx * 0.012, 0, L * 0.7), (-sx * 0.01, 0, L * 0.82), (sx * 0.004, 0, L * 0.9),
               (sx * 0.02, 0, L)]
        k.put(tube(pts, 0.009, 4), "BH_Iron", M=M @ R(0, a * 0.2, 0))
    k.put(cyl(0.016, 0.03, 6), "BH_Iron", M=M @ TRS(0, -0.015, L * 0.82, 90, 0, 0))


def coal_heap(k, cx, cy, z, R_=0.3, glow="BH_Coals", n=22):
    """Domed bed of coal lumps: glowing centre, black unburnt lumps round the rim."""
    r = k.r
    for i in range(n):
        a = r.uniform(0, math.tau)
        d = R_ * math.sqrt(r.random())
        h = 0.07 * (1 - (d / R_) ** 2)
        t = ico(r.uniform(0.035, 0.055), 0)
        jitter(t, r, 0.012)
        mat = glow if d < R_ * 0.72 else "BH_StoneDark"
        k.put(t, mat, M=TRS(cx + math.cos(a) * d, cy + math.sin(a) * d, z + h + 0.02, r.uniform(0, 90), r.uniform(0, 90), 0),
              tint=0.2 if mat == "BH_StoneDark" else 1.0, uvoff=False)


@asset("stand_smithy", "market")
def stand_smithy(k):
    """Brannoc, Blacksmith of Malasugue, and the town Forge. 5.6 x 4.2. A slate lean-to over the back half (open to the
    front) built against a stone forge corner at the back right: raised hearth with glowing coals under a stone hood,
    a tall stone chimney through the slates, leather bellows on a trestle. The front half is the working yard: anvil
    on a stump with a glowing blade on it, quench barrel, weapon board with swords/axes/shields, spears in a keg,
    armour on a stand, hammers on the front post. npc stands in the open behind the anvil."""
    r = k.r
    W, D = 5.6, 4.2
    ye, ze = -0.02, 2.86     # eave (top surface of the slates at the front edge)
    yr, zr = 1.98, 3.94      # back edge of the roof (top surface)
    yP = 0.25                # front plate / front posts
    yW = 1.84                # back wall line
    xS = 2.6                 # right stone wall centre line

    def zroof(y):
        return ze + (zr - ze) * (y - ye) / (yr - ye)
    slope = math.degrees(math.atan2(zr - ze, yr - ye))
    Ls = math.hypot(yr - ye, zr - ze)
    Mroof = T(0, (ye + yr) / 2, (ze + zr) / 2) @ R(slope, 0, 0)  # local +Y up the slope, local Z out of the roof

    # --- ground: trodden cinder floor under the shed and round the anvil
    pts = []
    for i in range(14):
        a = math.tau * i / 14
        rr = 1.0 + 0.12 * math.sin(a * 3 + 0.7)
        pts.append((0.1 + math.cos(a) * 2.6 * rr, 0.35 + math.sin(a) * 1.55 * rr))
    pts = [(max(-2.75, min(2.75, x)), max(-2.02, min(2.02, y))) for x, y in pts]
    k.put(flat_poly(pts, 0.006), "BH_Dirt", tint=0.7)

    # --- stone forge corner: right side wall and the right half of the back wall, both up to the slates
    masonry(k, -(yW - yP) / 2 - 0.12, (yW - yP) / 2 + 0.12, 0.0, zroof(yW) - 0.05, 0.4, mat="BH_Stone",
            M=T(xS, (yW + yP) / 2, 0) @ R(0, 0, 90), course=(0.38, 0.5), blen=(0.6, 1.1), quoin="start",
            top_profile=lambda x: zroof((yW + yP) / 2 + x) - 0.62, chip_rng=(0, 1), tint=(0.6, 0.85))
    beam(k, (xS, yP - 0.12, zroof(yP - 0.12) - 0.42), (xS, yW + 0.1, zroof(yW + 0.1) - 0.42), 0.38, 0.5, tint=0.45)
    masonry(k, 0.95, xS - 0.2, 0.0, zroof(yW) - 0.2, 0.3, mat="BH_Stone", M=T(0, yW, 0), course=(0.46, 0.6),
            blen=(0.75, 1.2), quoin="start", chip_rng=(0, 0), tint=(0.6, 0.85))

    # --- timber frame: front posts on stones, front plate, back posts, rafters, knee braces
    for x in (-2.62, -0.9):
        post(k, x, yP, zroof(yP) - 0.26, 0.16)
    for x in (-2.62, -0.9, 0.86):
        post(k, x, yW, zroof(yW) - 0.26, 0.15)
    zpl = zroof(yP) - 0.26
    beam(k, (-2.8, yP, zpl + 0.02), (xS - 0.12, yP, zpl + 0.02), 0.16, 0.18, tint=0.5)
    beam(k, (-2.8, yW, zroof(yW) - 0.24), (0.95, yW, zroof(yW) - 0.24), 0.14, 0.16, tint=0.5)
    for x in (-2.7, -1.8, -0.9, 0.0, 0.9, 1.72, 2.62):
        beam(k, (x, ye - 0.06, ze - 0.14), (x, yr, zr - 0.14), 0.08, 0.13, tint=0.55)
    for x, sx in ((-2.62, 1), (-0.9, -1), (-0.9, 1), (xS - 0.2, -1)):
        beam(k, (x + sx * 0.06, yP, zpl - 0.62), (x + sx * 0.62, yP, zpl - 0.06), 0.1, tint=0.5)

    # --- back wall (left part): vertical boards between the posts
    nb = 12
    for i in range(nb):
        x = -2.68 + (0.95 + 2.68) * (i + 0.5) / nb
        top = zroof(yW) - 0.3
        plank(k, (0.95 + 2.68) / nb - 0.012, 0.035, top, T(x, yW + 0.09, top / 2), mat="BH_Wood", tint=(0.45, 0.7), chips=0)
    for z in (0.9, 2.0):
        beam(k, (-2.7, yW - 0.02, z), (0.9, yW - 0.02, z), 0.08, 0.1, tint=0.5)

    # --- the slate roof: sarking boards, then overlapping courses of slates (a few slipped / replaced)
    k.put(box(W + 0.02, Ls + 0.08, 0.05), "BH_WoodDark", M=Mroof @ T(0, 0, -0.07), tint=0.4)
    rows = 8
    rh = Ls / rows
    for j in range(rows):
        y = -Ls / 2 + rh * (j + 0.5)
        ws, _ = split_lengths(r, W + 0.06, 0.28, 0.46)
        x = -(W + 0.06) / 2
        for wi, w in enumerate(ws):
            xc = x + w / 2
            x += w
            if xc > (W + 0.06) / 2:
                continue
            if j == 4 and wi == 9:  # one slate slipped away: the boards show
                continue
            mat = "BH_StoneDark" if r.random() < 0.08 else "BH_Slate"
            k.put(box(w - 0.02, rh * 1.4, 0.028), mat,
                  M=Mroof @ TRS(xc, y - rh * 0.2, -0.012, -4.0, r.uniform(-0.6, 0.6), r.uniform(-1.5, 1.5)),
                  tint=r.uniform(0.55, 0.9))
    # slipped slate lying askew lower down, and a fresher repaired patch
    k.put(box(0.3, 0.36, 0.028), "BH_Slate", M=Mroof @ TRS(0.3, -Ls / 2 + rh * 3.3, 0.02, -2, 3, 24), tint=0.7)
    # eave fascia, barge boards, capping along the back edge (stone flashing where it meets the wall head)
    k.put(box(W + 0.08, 0.05, 0.16, bev=0.01), "BH_WoodDark", M=T(0, ye - 0.04, ze - 0.1), tint=0.45)
    for sx in (-1, 1):
        k.put(box(0.06, Ls + 0.1, 0.2, bev=0.01), "BH_WoodDark", M=Mroof @ T(sx * (W / 2 + 0.02), 0, -0.04), tint=0.45)
    k.put(box(W + 0.08, 0.2, 0.12, bev=0.02), "BH_StoneDark", M=Mroof @ T(0, Ls / 2 - 0.06, 0.03), tint=0.6)

    # --- forge hearth: raised stone block, iron-bound edge, coal bed, bar in the fire
    hx0, hx1, hy0, hy1, hz = 1.22, 2.42, 0.42, yW - 0.12, 0.82
    hcx, hcy = (hx0 + hx1) / 2, (hy0 + hy1) / 2
    masonry(k, hx0, hx1, 0.0, hz - 0.06, hy1 - hy0, mat="BH_Stone", M=T(0, hcy, 0), course=(0.24, 0.3),
            blen=(0.35, 0.6), quoin="both", chip_rng=(0, 1), tint=(0.55, 0.8))
    k.put(box(hx1 - hx0 + 0.1, hy1 - hy0 + 0.06, 0.08, bev=0.015), "BH_StoneDark", M=T(hcx, hcy, hz - 0.04), tint=0.5)
    k.put(box(hx1 - hx0 + 0.12, 0.03, 0.06), "BH_Iron", M=T(hcx, hy0 - 0.045, hz - 0.04))
    fx, fy = 1.84, 0.92
    k.put(cyl(0.34, 0.05, 10, r2=0.3), "BH_StoneDark", M=T(fx, fy, hz), tint=0.25)   # fire-pot rim
    coal_heap(k, fx, fy, hz, 0.3)
    for (dx, dy, h) in ((-0.05, 0.02, 0.1), (0.07, -0.04, 0.08), (0.0, 0.08, 0.07)):
        flame_tip(k, T(fx + dx, fy + dy, hz + 0.09), h)
    # an iron bar pushed into the coals from the front-left, its buried end glowing
    Mb = TRS(fx - 0.62, fy - 0.32, hz + 0.16, 0, 100, 28)
    k.put(box(0.03, 0.03, 0.45), "BH_Iron", M=Mb @ T(0, 0, 0.22))
    k.put(box(0.032, 0.032, 0.2), "BH_Coals", M=Mb @ T(0, 0, 0.54))
    # tongs rack: iron rail on the hearth front with tongs and a poker hanging
    k.put(cyl(0.012, hx1 - hx0 - 0.1, 5), "BH_Iron", M=TRS(hx0 + 0.05, hy0 - 0.09, hz - 0.14, 0, 90, 0))
    for sx in (-1, 1):
        k.put(box(0.03, 0.09, 0.03), "BH_Iron", M=T(hcx + sx * 0.52, hy0 - 0.05, hz - 0.14))
    for i, x in enumerate((1.46, 2.0, 2.24)):
        tongs(k, TRS(x, hy0 - 0.1, hz - 0.1, 180, r.uniform(-4, 4), 0), 0.56 if i % 2 else 0.5)
    # coal scuttle and a shovel by the hearth
    k.put(cyl(0.16, 0.22, 8, r2=0.2), "BH_Iron", M=T(0.95, 0.45, 0.0), tint=0.8)
    coal_heap(k, 0.95, 0.45, 0.12, 0.15, "BH_StoneDark", 7)

    # --- stone hood over the hearth (soot-dark lower course, lighter above) and the chimney through the slates
    k.put(box(hx1 - hx0 + 0.16, 0.22, 0.22, bev=0.02), "BH_WoodDark", M=T(hcx, hy0 - 0.01, 1.72), tint=0.3)  # mantel
    lo = [(hx0 - 0.04, hy0 - 0.08), (hx1 + 0.04, hy0 - 0.08), (hx1 + 0.04, yW), (hx0 - 0.04, yW)]
    hi = [(hcx - 0.44, 1.15), (hcx + 0.44, 1.15), (hcx + 0.44, yW), (hcx - 0.44, yW)]
    zs = (1.83, 2.2, 2.55, 2.9)
    for b in range(3):
        t0, t1 = b / 3, (b + 1) / 3
        c = [(lerp(lo[i][0], hi[i][0], t0), lerp(lo[i][1], hi[i][1], t0), zs[b] + 0.012) for i in range(4)]
        c += [(lerp(lo[i][0], hi[i][0], t1), lerp(lo[i][1], hi[i][1], t1), zs[b + 1] - 0.012) for i in range(4)]
        k.put(hexa(c, 0.03), "BH_StoneDark" if b == 0 else "BH_Stone", tint=(0.35, 0.6, 0.7)[b])
    chimney(k, hcx, 1.55, 4.3, 0.88, 0.8, mat="BH_Stone", z0=2.9)
    chimney(k, hcx, 1.55, 5.42, 0.7, 0.62, mat="BH_Stone", z0=4.3)  # stack steps in above the weathering course
    # rain cap: two stone stubs carrying a slate slab
    for sx in (-1, 1):
        k.put(box(0.14, 0.5, 0.2, bev=0.02), "BH_Stone", M=T(hcx + sx * 0.36, 1.55, 5.72), tint=0.7)
    k.put(box(1.0, 0.86, 0.06, bev=0.01), "BH_Slate", M=TRS(hcx, 1.55, 5.85, 0, 2, 0), tint=0.7)
    # lead flashing collar where the stack meets the slates
    k.put(box(1.04, 0.96, 0.05), "BH_Iron", M=T(hcx, 1.55, 0.0) @ T(0, 0, zroof(1.55) + 0.01) @ R(slope, 0, 0), tint=0.5)

    # --- bellows on a trestle, nozzle into the hearth side, long handle rising at the back
    bx, by, bz = 0.78, 0.98, 0.72
    for dx in (-0.3, 0.2):
        for sy in (-1, 1):
            beam(k, (bx + dx, by + sy * 0.22, 0.0), (bx + dx, by + sy * 0.1, bz - 0.04), 0.06, tint=0.5)
        beam(k, (bx + dx, by - 0.22, 0.25), (bx + dx, by + 0.22, 0.25), 0.05, tint=0.5)
    beam(k, (bx - 0.45, by, bz - 0.02), (bx + 0.42, by, bz - 0.02), 0.07, 0.3, tint=0.5)
    blade = [(0.38, 0.0), (0.22, 0.07), (-0.1, 0.2), (-0.36, 0.2), (-0.44, 0.1), (-0.44, -0.1), (-0.36, -0.2),
             (-0.1, -0.2), (0.22, -0.07)]
    Mbl = T(bx, by, bz + 0.03)
    k.put(prism(blade, 0.04, bev=0.006), "BH_WoodDark", M=Mbl @ R(90, 0, 0) @ T(0, 0, 0), tint=0.5)
    Mtop = Mbl @ T(0.38, 0, 0.0) @ R(0, 11, 0) @ T(-0.38, 0, 0.2)
    k.put(prism(blade, 0.04, bev=0.006), "BH_WoodDark", M=Mtop @ R(90, 0, 0), tint=0.5)
    rings = []
    for (x_, w_) in ((0.36, 0.05), (0.22, 0.08), (0.05, 0.14), (-0.12, 0.19), (-0.3, 0.18), (-0.41, 0.1)):
        ztop = 0.2 + (0.38 - x_) * math.sin(math.radians(11)) - 0.01
        zm, hh = (0.03 + ztop) / 2, (ztop - 0.03) / 2
        ring = []
        for i in range(10):
            a = math.tau * i / 10
            bulge = 1.0 + 0.12 * math.cos(a) ** 2
            ring.append(Mbl @ Vector((x_, math.cos(a) * w_ * bulge, zm + math.sin(a) * hh)))
        rings.append(ring)
    loft(k, rings, "BH_Leather", 0.8, 40)
    k.put(tube([(0.38, 0, 0.12), (0.44, 0, 0.12)], 0.035, 6), "BH_Leather", M=Mbl, smooth=40)
    k.put(cyl(0.035, 0.08, 6, r2=0.02), "BH_Iron", M=Mbl @ TRS(0.44, 0, 0.12, 0, 90, 0))  # nozzle into the hearth
    k.put(tube([(-0.44, 0, 0.3), (-0.62, 0, 0.62), (-0.72, 0, 1.02)], 0.022, 5), "BH_WoodDark", M=Mbl, tint=0.55)
    k.put(cyl(0.03, 0.18, 6), "BH_Wood", M=Mbl @ TRS(-0.72, -0.09, 1.02, 90, 0, 0), tint=0.6)  # grip
    k.put(tube([(-0.36, 0.0, 0.26), (-0.44, 0.0, 0.34)], 0.012, 4), "BH_Iron", M=Mbl)

    # --- anvil on its stump (front right) with a glowing blade on the face, hammer and tongs
    ax, ay = 1.18, -1.1
    t = tube([(0, 0, 0), (0, 0, 0.3), (0, 0, 0.58)], [0.31, 0.28, 0.27], 10)
    ndisp(t, 4.0, 0.02, k.noff)
    k.put(t, "BH_Bark", M=T(ax, ay, 0), tint=0.6, smooth=40)
    k.put(cyl(0.27, 0.02, 10), "BH_Wood", M=T(ax, ay, 0.58), tint=0.7)
    k.put(cyl(0.285, 0.05, 10, caps=False), "BH_Iron", M=T(ax, ay, 0.44))
    outline = [(-0.3, 0.0), (0.28, 0.0), (0.28, 0.1), (0.21, 0.13), (0.24, 0.22), (0.33, 0.27), (0.34, 0.33),
               (-0.3, 0.33), (-0.5, 0.31), (-0.64, 0.28), (-0.5, 0.25), (-0.3, 0.2), (-0.25, 0.12), (-0.33, 0.08)]
    Ma = T(ax + 0.08, ay, 0.6)
    k.put(prism(outline, 0.18, bev=0.012), "BH_Iron", M=Ma, tint=0.9)
    k.put(box(0.03, 0.03, 0.02), "BH_StoneDark", M=Ma @ T(0.22, 0.0, 0.33), tint=0.05)  # hardy hole
    zf = 0.6 + 0.335
    # blade being drawn out: glowing half on the face, dull tang held in tongs over the edge
    k.put(box(0.5, 0.055, 0.012, bev=0.003), "BH_Coals", M=TRS(ax - 0.02, ay - 0.01, zf + 0.006, 0, 0, 6))
    k.put(prism([(-0.02, 0.0), (0.02, 0.0), (0.0, 0.08)], 0.012), "BH_Coals", M=TRS(ax - 0.28, ay - 0.04, zf + 0.006, 0, -90, 6))
    k.put(box(0.2, 0.025, 0.01), "BH_Iron", M=TRS(ax + 0.32, ay + 0.02, zf + 0.004, 0, 0, 6))
    tongs(k, TRS(ax + 0.62, ay + 0.06, zf - 0.02, 0, -86, 6), 0.46, 3.0)
    hammer(k, TRS(ax - 0.05, ay + 0.06, zf + 0.02, 0, 90, 0), 0.38, 0.16)
    # scale and chips on the ground by the stump, a sledge leaning on it
    hammer(k, TRS(ax - 0.62, ay + 0.1, 0.0, 0, 22, 0), 0.7, sledge=True)

    # --- quench barrel beside the anvil: water, a blade and tongs standing in it
    qx, qy = 1.98, -0.62
    barrel(k, TRS(qx, qy, 0, 0, 0, 20), 0.78, 0.3, tint=0.6, lid=False)
    k.put(cyl(0.27, 0.01, 9), "BH_Water", M=T(qx, qy, 0.68), uvoff=False)
    sword(k, TRS(qx - 0.05, qy + 0.06, 0.95, 180, 8, 12), 0.82)
    tongs(k, TRS(qx + 0.1, qy - 0.08, 1.02, 172, 14, 0), 0.62)

    # --- weapon board (front left): planked back on two posts, shields above, swords and axes on pegs
    wx0, wx1, wy = -2.62, -1.3, -0.42
    wcx = (wx0 + wx1) / 2
    for x in (wx0, wx1):
        post(k, x, wy + 0.06, 2.12, 0.12)
    n = 6
    for i in range(n):
        x = wx0 + 0.06 + (wx1 - wx0 - 0.12) * (i + 0.5) / n
        plank(k, (wx1 - wx0 - 0.12) / n - 0.01, 0.035, 1.72, T(x, wy + 0.08, 0.3 + 0.86), mat="BH_Wood", tint=(0.5, 0.7))
    for z in (0.34, 1.98):
        k.put(box(wx1 - wx0 + 0.12, 0.08, 0.1, bev=0.01), "BH_WoodDark", M=T(wcx, wy + 0.08, z), tint=0.5)
    shield_round(k, TRS(wx0 + 0.36, wy + 0.06, 1.62, 90, 0, 0), 0.27)
    heater_shield(k, T(wx1 - 0.38, wy + 0.04, 1.6), 1.05, "BH_ClothRed", "BH_Gold")
    for i, x in enumerate((wx0 + 0.2, wx0 + 0.36, wx0 + 0.52)):
        k.put(cyl(0.012, 0.08, 5), "BH_WoodDark", M=TRS(x, wy + 0.06, 0.6, 90, 0, 0), tint=0.4)
        sword(k, TRS(x, wy - 0.02, 0.44, 0, r.uniform(-2, 2), 0), (0.9, 0.84, 0.78)[i])
    axe(k, TRS(wx1 - 0.52, wy - 0.02, 0.42, 0, -4, 0), 0.74)
    axe(k, TRS(wx1 - 0.3, wy - 0.02, 0.42, 0, 4, 180), 0.66, bearded=True)
    for x in (wx1 - 0.52, wx1 - 0.3):
        k.put(box(0.12, 0.08, 0.03), "BH_WoodDark", M=T(x, wy + 0.02, 0.9), tint=0.4)
    # a lantern on an iron arm off the board's right post lights the weapons (light_b)
    k.put(tube([(wx1, wy + 0.02, 1.84), (wx1, wy - 0.2, 2.02), (wx1, wy - 0.5, 2.06)], 0.014, 5), "BH_Iron")
    k.put(tube([(wx1, wy + 0.02, 1.98), (wx1, wy - 0.4, 2.06)], 0.01, 4), "BH_Iron")
    lb_ = lantern_on_hook(k, wx1, wy - 0.5, 2.04, 0.42)
    light_b = (lb_[0], lb_[1], lb_[2] - 0.28)
    # spears and a bill standing in a keg at the board's end
    kx, ky = -1.02, -0.62
    barrel(k, TRS(kx, ky, 0, 0, 0, 30), 0.62, 0.22, tint=0.6, segs=9, lid=False)
    for i, (dx, dy, a, b, L) in enumerate(((-0.06, 0.04, -9, 4, 2.2), (0.05, -0.03, 6, -5, 2.35), (0.0, 0.07, 3, 10, 2.05))):
        spear(k, TRS(kx + dx, ky + dy, 0.08, b, a, r.uniform(0, 90)), L)
    # a bill-hook head on a fourth pole
    Mh = TRS(kx - 0.06, ky - 0.06, 0.08, -8, -3, 20)
    k.put(cyl(0.02, 2.0, 6), "BH_WoodDark", M=Mh, tint=0.6)
    k.put(prism([(0.0, 0.0), (0.05, 0.0), (0.16, 0.14), (0.1, 0.28), (0.02, 0.36), (0.0, 0.2)], 0.014), "BH_Metal",
          M=Mh @ T(-0.01, 0, 1.92), tint=0.8)

    # --- armour on a stand beside the post: mail skirt, breastplate, pauldrons, helm
    sx_, sy_ = -0.3, 0.08
    Ms = T(sx_, sy_, 0)
    for a in (0, 90):
        k.put(box(0.62, 0.09, 0.07, bev=0.01), "BH_WoodDark", M=Ms @ TRS(0, 0, 0.035, 0, 0, a + 20), tint=0.5)
    k.put(cyl(0.035, 1.62, 6), "BH_WoodDark", M=Ms @ T(0, 0, 0.05), tint=0.55)
    k.put(box(0.6, 0.06, 0.06), "BH_WoodDark", M=Ms @ T(0, 0, 1.44), tint=0.5)
    mail = lathe([(0.2, 0.0), (0.23, 0.22), (0.2, 0.42)], 12, cap_top=False, cap_bot=False)
    for v in mail.verts:
        v.co.y *= 0.75
    bmesh.ops.solidify(mail, geom=list(mail.faces), thickness=0.012)
    k.put(mail, "BH_Iron", M=Ms @ T(0, 0, 0.62), tint=0.8, smooth=45)
    bp = lathe([(0.17, 0.0), (0.19, 0.12), (0.22, 0.3), (0.23, 0.42), (0.2, 0.5), (0.1, 0.56)], 12, cap_top=False,
               cap_bot=False)
    for v in bp.verts:
        v.co.y *= 0.72
        if v.co.y < 0:
            v.co.y *= 1.12
    bmesh.ops.solidify(bp, geom=list(bp.faces), thickness=0.012)
    k.put(bp, "BH_Silver", M=Ms @ T(0, 0, 0.95), tint=0.8, smooth=45)
    k.put(box(0.02, 0.03, 0.42), "BH_Silver", M=Ms @ TRS(0, -0.18, 1.2, -10, 0, 0), tint=0.9)
    k.put(box(0.34, 0.03, 0.05), "BH_Leather", M=Ms @ T(0, -0.17, 0.98), tint=0.7)
    for s in (-1, 1):
        p = ico(0.13, 2)
        for v in p.verts:
            v.co.z = max(v.co.z, -0.02)
        k.put(p, "BH_Silver", M=Ms @ TRS(s * 0.27, 0, 1.43, 0, s * 25, 0) @ S(1.0, 1.0, 0.7), tint=0.8, smooth=45)
    k.put(cyl(0.07, 0.06, 8), "BH_Metal", M=Ms @ T(0, 0, 1.5), tint=0.7)
    helmet(k, Ms @ T(0, 0, 1.56))

    # --- hammer board on the middle front post (faces the yard)
    hbx = -0.9
    k.put(box(0.44, 0.04, 0.6, bev=0.01), "BH_WoodDark", M=T(hbx, yP - 0.1, 1.42), tint=0.5)
    for i, dx in enumerate((-0.14, 0.0, 0.14)):
        k.put(cyl(0.01, 0.06, 4), "BH_Iron", M=TRS(hbx + dx, yP - 0.14, 1.62, 90, 0, 0))
        hammer(k, TRS(hbx + dx, yP - 0.15, 1.64, 180, 0, 0), (0.36, 0.42, 0.3)[i], (0.14, 0.18, 0.12)[i])
    for dx in (-0.12, 0.12):  # horseshoes on nails below
        k.put(torus(0.06, 0.012, 10, 3), "BH_Iron", M=TRS(hbx + dx, yP - 0.13, 1.2, 90, 0, 0))

    # --- back of the shed: workbench with a vice, helms and a mail shirt; shields on the back wall; bar stock
    bx0, bx1, byb = -2.55, -1.1, yW - 0.3
    k.put(box(bx1 - bx0, 0.5, 0.08, bev=0.01), "BH_WoodDark", M=T((bx0 + bx1) / 2, byb, 0.84), tint=0.5)
    for x in (bx0 + 0.08, bx1 - 0.08):
        for dy in (-0.18, 0.18):
            k.put(box(0.08, 0.08, 0.8), "BH_WoodDark", M=T(x, byb + dy, 0.4), tint=0.45)
    k.put(box(0.12, 0.14, 0.16, bev=0.01), "BH_Iron", M=T(bx1 - 0.2, byb - 0.2, 0.96))
    helmet(k, TRS(bx0 + 0.35, byb, 0.88, 0, 0, 30))
    for i in range(4):  # a stack of new blade blanks on the bench
        k.put(box(0.6, 0.05, 0.012), "BH_Iron", M=TRS(bx0 + 0.95, byb + 0.02, 0.886 + i * 0.012, 0, 0, r.uniform(-6, 6)))
    for i, x in enumerate((-2.2, 0.3)):
        shield_lite(k, TRS(x, yW + 0.07, 1.75 + (0.1 if i == 1 else 0.0), 90, 0, 0), 0.26 + 0.03 * (i % 2))
    heater_shield(k, T(-0.3, yW + 0.01, 1.85), 0.95, "BH_ClothBlue", "BH_Silver")
    for i in range(6):
        k.put(box(0.03, 0.03, 1.5), "BH_Iron", M=TRS(0.45 + i * 0.05, yW - 0.2, 0.0, -6, r.uniform(-3, 3), 0) @ T(0, 0, 0.75))
    # charcoal sacks by the bench
    sack(k, TRS(-0.6, yW - 0.4, 0, 0, 0, 20), 0.6, 0.24, open_=True, fill="BH_StoneDark", mat="BH_Cloth")
    sack(k, TRS(-0.2, yW - 0.35, 0, 0, 0, -10), 0.66, 0.24)

    # --- lantern hanging from the front plate over the yard (light_a)
    lp_ = lantern_on_hook(k, 0.3, yP, zpl - 0.07, 0.5)
    k.put(box(0.03, 0.03, 0.1), "BH_Iron", M=T(0.3, yP, zpl - 0.05))
    light = (lp_[0], lp_[1], lp_[2] - 0.32)  # just under the lantern's base (the game light is unshadowed)

    # --- sockets and collision
    k.sockets.append(("npc", (ax, -0.3, 0.0)))
    k.sockets.append(("use", (ax, -1.86, 0.0)))
    k.sockets.append(("customer", (0.1, -1.55, 0.0)))
    k.sockets.append(("flame", (fx, fy, hz + 0.14)))
    k.sockets.append(("smoke", (hcx, 1.55, 5.95)))
    k.sockets.append(("light_a", light))
    k.sockets.append(("light_b", light_b))
    k.col_box(hx1 - hx0 + 0.1, hy1 - hy0 + 0.1, 1.0, T(hcx, hcy, 0.5))
    k.col_box(0.4, yW - yP + 0.3, 2.2, T(xS, (yW + yP) / 2, 1.1))
    k.col_box(W - 0.1, 0.34, 2.2, T(0, yW + 0.02, 1.1))
    k.col_box(0.62, 0.62, 0.95, T(ax, ay, 0.47))
    k.col_box(0.62, 0.62, 0.8, T(qx, qy, 0.4))
    k.col_box(wx1 - wx0 + 0.16, 0.3, 2.1, T(wcx, wy + 0.04, 1.05))
    k.col_box(0.5, 0.5, 1.0, T(kx, ky, 0.5))
    k.col_box(0.55, 0.55, 1.8, T(sx_, sy_, 0.9))
    k.col_box(1.0, 0.5, 1.0, T(bx, by, 0.5))
    k.col_box(bx1 - bx0, 0.55, 0.9, T((bx0 + bx1) / 2, byb, 0.45))
    for x in (-2.62, -0.9):
        k.col_box(0.2, 0.2, 2.2, T(x, yP, 1.1))
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# wagon helpers
from assets_props import bone  # noqa

def loft(k, rings, mat, tint=0.8, smooth=40, cap=True):
    """Skin a list of equal-length closed rings (lists of points) into a closed tube-like solid."""
    t = tb()
    vs = [[t.verts.new(Vector(p)) for p in ring] for ring in rings]
    n = len(rings[0])
    for j in range(len(vs) - 1):
        for i in range(n):
            t.faces.new((vs[j][i], vs[j][(i + 1) % n], vs[j + 1][(i + 1) % n], vs[j + 1][i]))
    if cap:
        t.faces.new(vs[0][::-1])
        t.faces.new(vs[-1])
    bmesh.ops.recalc_face_normals(t, faces=t.faces)
    k.put(t, mat, tint=tint, smooth=smooth)


def chain(k, a, b, sag=0.03, link=0.06):
    """Hanging iron chain of alternating links from a to b."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    n = max(3, int(L / link))
    d = (b - a).normalized()
    for i in range(n):
        t0 = (i + 0.5) / n
        p = a.lerp(b, t0)
        p.z -= sag * 4 * t0 * (1 - t0)
        M, _ = along(p - d * 0.01, p + d * 0.01)
        k.put(torus(0.016, 0.0045, 6, 3), "BH_Iron", M=M @ R(0, 90, 90 * (i % 2)) @ S(1.0, 0.6, 1.0))


def wheel_lite(k, M, R_=0.5, spokes=8, mat="BH_Wood"):
    """Lighter cart wheel for the far side (same silhouette as assets_props.wheel, fewer faces)."""
    k.put(torus(R_ - 0.03, 0.05, 16, 4), mat, M=M @ R(90, 0, 0), tint=0.7, smooth=40)
    k.put(torus(R_, 0.022, 16, 3), "BH_Iron", M=M @ R(90, 0, 0), smooth=40)
    k.put(cyl(0.09, 0.22, 8), mat, M=M @ TRS(0, 0.11, 0, 90, 0, 0), tint=0.6)
    for i in range(spokes):
        L = R_ - 0.12
        k.put(box(0.05, 0.045, L), mat, M=M @ R(0, 360.0 * i / spokes, 0) @ T(0, 0, 0.07 + L / 2), tint=0.8)


def casket(k, M, w=0.3, d=0.2, h=0.15, wood="BH_WoodDark", trim="BH_Brass", lock=True):
    """Ornate little chest: domed (half-round) lid, metal bands and corner caps, hasp and padlock on the -Y face."""
    hb = h * 0.62
    k.put(box(w, d, hb, bev=0.008), wood, M=M @ T(0, 0, hb / 2), tint=0.5)
    t = cyl(d / 2, w, 10)
    slice_plane(t, (0, 0, 0), (1, 0, 0))
    lid_s = (h - hb) / (d / 2)
    Ml = M @ T(0, 0, hb) @ S(1.0, 1.0, lid_s)
    k.put(t, wood, M=Ml @ TRS(-w / 2, 0, 0, 0, 90, 0), tint=0.45)
    for sx in (-1, 1):  # bands over the lid and down the body
        k.put(box(0.022, d + 0.012, hb + 0.004), trim, M=M @ T(sx * w * 0.3, 0, hb / 2))
        b_ = cyl(d / 2 + 0.006, 0.024, 10, caps=False)
        slice_plane(b_, (0, 0, 0), (1, 0, 0))
        k.put(b_, trim, M=Ml @ TRS(sx * w * 0.3 - 0.012, 0, 0, 0, 90, 0))
        for sy in (-1, 1):
            k.put(box(0.035, 0.035, 0.035), trim, M=M @ T(sx * (w / 2 - 0.012), sy * (d / 2 - 0.012), 0.017))
    if lock:
        k.put(box(0.03, 0.012, 0.07), trim, M=M @ T(0, -d / 2 - 0.006, hb - 0.01))
        k.put(torus(0.018, 0.005, 8, 3), "BH_Iron", M=M @ T(0, -d / 2 - 0.02, hb - 0.03) @ R(0, 90, 0))
        k.put(box(0.045, 0.02, 0.04, bev=0.005), "BH_Iron", M=M @ T(0, -d / 2 - 0.02, hb - 0.06))


def idol(k, M, s=1.0):
    """Squat golden idol: pot-bellied, little horns, green-stone collar, ruby eyes, on a dark stone plinth. Faces -Y."""
    k.put(lathe([(0.05 * s, 0.0), (0.065 * s, 0.03 * s), (0.07 * s, 0.07 * s), (0.055 * s, 0.11 * s), (0.035 * s, 0.13 * s)],
                8), "BH_Gold", M=M, tint=0.7, smooth=50)
    k.put(torus(0.036 * s, 0.009 * s, 8, 3), "BH_GemGreen", M=M @ T(0, 0, 0.128 * s))
    t = ico(0.05 * s, 1)
    for v in t.verts:
        v.co.z *= 1.15
        v.co.y *= 0.95
    k.put(t, "BH_Gold", M=M @ T(0, 0, 0.18 * s), tint=0.75, smooth=40)
    for sx in (-1, 1):
        k.put(ico(0.009 * s, 0), "BH_GemRed", M=M @ T(sx * 0.018 * s, -0.045 * s, 0.19 * s))
        k.put(cyl(0.012 * s, 0.05 * s, 5), "BH_Gold", M=M @ TRS(sx * 0.052 * s, 0, 0.23 * s, 0, sx * 35, 0), tint=0.7)  # horns
    k.put(box(0.1 * s, 0.1 * s, 0.02 * s), "BH_StoneDark", M=M @ T(0, 0, -0.005 * s), tint=0.5)


def raven(k, M, s=1.0):
    """Perched raven looking toward -Y: body, head, heavy beak, wedge tail, folded wings, amber eye."""
    t = ico(0.07 * s, 1)
    for v in t.verts:
        v.co.x *= 0.8
        v.co.y *= 1.45
    k.put(t, "BH_ClothBlack", M=M @ TRS(0, 0.02 * s, 0.1 * s, 25, 0, 0), smooth=40)
    k.put(ico(0.045 * s, 1), "BH_ClothBlack", M=M @ T(0, -0.08 * s, 0.19 * s), smooth=40)
    k.put(cyl(0.018 * s, 0.07 * s, 5, r2=0.0), "BH_Iron", M=M @ TRS(0, -0.115 * s, 0.185 * s, 100, 0, 0))
    k.put(prism([(-0.04 * s, 0.0), (0.04 * s, 0.0), (0.03 * s, 0.13 * s), (-0.03 * s, 0.13 * s)], 0.012 * s), "BH_ClothBlack",
          M=M @ TRS(0, 0.1 * s, 0.07 * s, 90 + 60, 0, 0))
    for sx in (-1, 1):
        k.put(box(0.018 * s, 0.16 * s, 0.07 * s, bev=0.01 * s), "BH_ClothBlack", M=M @ TRS(sx * 0.05 * s, 0.03 * s, 0.11 * s, 22, 0, 0))
        k.put(ico(0.006 * s, 0), "BH_GemAmber", M=M @ T(sx * 0.03 * s, -0.1 * s, 0.2 * s))
        k.put(cyl(0.005 * s, 0.05 * s, 3), "BH_Iron", M=M @ T(sx * 0.02 * s, 0.0, 0.0))


@asset("stand_wagon", "market")
def stand_wagon(k):
    """The Hooded Stranger, dealer in rare wares. 4.8 x 2.4 (shafts included). A weathered travelling wagon under a
    tall black bow-top cover on wooden hoops, rope-lashed and patched, a stove pipe through a tin collar and a raven on
    the front hoop; big rear wheels, small front wheels, shafts resting on a log (no horse). The side hatch is let
    down on chains as a counter facing -Y with the curios; a lantern on an iron arm over it. npc stands beside it."""
    r = k.r
    x0, x1 = -1.9, 1.3       # body ends
    hw = 0.7                 # half width of the body
    zb = 0.96                # floor top
    zs = 1.74                # side top: where the hoops spring
    Rc, Hc = 0.84, 1.08      # cover half width at the springing, cover rise
    ox0, ox1 = -0.36, 1.16   # hatch opening along X
    oz0, oz1 = 1.1, 1.6      # hatch opening heights (hinge at oz0)
    hd = 0.42                # hatch depth when let down

    # --- undercarriage: sills, cross bearers, axle beds, axles
    for sy in (-1, 1):
        k.put(box(x1 - x0 + 0.2, 0.12, 0.14, bev=0.015), "BH_WoodDark", M=T((x0 + x1) / 2, sy * 0.5, zb - 0.12), tint=0.45)
    for x in (x0 + 0.05, -1.15, -0.3, 0.55, x1 - 0.05):
        k.put(box(0.1, 2 * hw + 0.04, 0.1, bev=0.01), "BH_WoodDark", M=T(x, 0, zb - 0.1), tint=0.45)
    for (ax_, az, R_) in ((-1.15, 0.64, 0.64), (0.82, 0.44, 0.44)):
        k.put(box(0.16, 2 * hw - 0.1, max(0.08, zb - 0.19 - az), bev=0.015), "BH_WoodDark",
              M=T(ax_, 0, (zb - 0.17 + az) / 2), tint=0.4)
        k.put(cyl(0.045, 2 * 0.88, 8), "BH_Iron", M=TRS(ax_, 0.88, az, 90, 0, 0))
    # front turntable (fifth wheel)
    k.put(cyl(0.34, 0.05, 12), "BH_WoodDark", M=T(0.82, 0, zb - 0.22), tint=0.4)
    k.put(torus(0.34, 0.012, 16, 3), "BH_Iron", M=T(0.82, 0, zb - 0.2))

    # --- wheels: big rear pair outside the body, small front pair under the hatch
    for sy in (-1, 1):
        rz = 180 if sy < 0 else 0
        wfn = wheel if sy < 0 else wheel_lite  # the far pair is barely seen: lighter build
        wfn(k, T(-1.15, sy * 0.88, 0.64) @ R(0, 0, rz), 0.64, 12, mat="BH_WoodDark")
        wfn(k, T(0.82, sy * 0.84, 0.44) @ R(0, 0, rz), 0.44, 10, mat="BH_WoodDark")

    # --- floor and body sides: clapboards on corner/mid posts; the -Y side has the hatch opening
    k.put(box(x1 - x0, 2 * hw, 0.05), "BH_Wood", M=T((x0 + x1) / 2, 0, zb - 0.025), tint=0.5)
    nbd = 4
    bh = (zs - zb) / nbd
    for sy in (-1, 1):
        for j in range(nbd):
            zc = zb + bh * (j + 0.5)
            segs = [(x0, x1)]
            if sy < 0 and oz0 - 0.01 < zc < oz1 + 0.01:
                segs = [(x0, ox0), (ox1, x1)]
            for (a, b) in segs:
                t = box(b - a, 0.035, bh + 0.02, bev=0.008)
                chip(t, r, r.randint(0, 1), 0.02)
                k.put(t, "BH_Wood", M=TRS((a + b) / 2, sy * (hw + 0.01 + 0.008 * (j % 2)), zc, -4 * sy, 0, 0),
                      tint=r.uniform(0.4, 0.6))
        for x in (x0 + 0.04, -1.15 + 0.5, ox0 - 0.05, ox1 + 0.05, x1 - 0.04):
            if sy > 0 and x in (ox0 - 0.05, ox1 + 0.05):
                continue
            k.put(box(0.08, 0.06, zs - zb + 0.06, bev=0.01), "BH_WoodDark", M=T(x, sy * (hw + 0.04), (zb + zs) / 2), tint=0.4)
        k.put(box(x1 - x0 + 0.1, 0.09, 0.08, bev=0.012), "BH_WoodDark", M=T((x0 + x1) / 2, sy * (hw + 0.04), zs + 0.02),
              tint=0.45)  # top rail the hoops stand on
        # carved brackets under the eave rail
        for x in (x0 + 0.25, -0.9 if sy < 0 else -0.4, 0.25 if sy > 0 else 1.0):
            k.put(prism([(0.0, 0.0), (0.1, 0.0), (0.02, -0.16), (0.0, -0.16)], 0.04), "BH_WoodDark",
                  M=TRS(x, sy * (hw + 0.08), zs - 0.02, 0, 0, 90 if sy > 0 else -90) @ R(0, 0, 0), tint=0.4)
    # front and back end boards up to the springing, filling the half-ellipse at the front
    for x, sx in ((x0, -1), (x1, 1)):
        for j in range(nbd):
            k.put(box(0.035, 2 * hw, bh + 0.02, bev=0.008), "BH_Wood", M=T(x + sx * 0.01, 0, zb + bh * (j + 0.5)),
                  tint=r.uniform(0.4, 0.6))
    # the front: planked half-ellipse head with a small dark door and a brass-studded frame
    head = [(math.cos(math.pi * i / 12) * Rc, zs + math.sin(math.pi * i / 12) * Hc) for i in range(13)]
    k.put(prism([(y, z) for y, z in head], 0.04), "BH_WoodDark", M=T(x1 + 0.02, 0, 0) @ R(0, 0, 90), tint=0.4)
    k.put(box(0.05, 0.62, 1.2, bev=0.01), "BH_WoodDark", M=T(x1 + 0.05, 0.05, zb + 0.6 + 0.2), tint=0.25)  # door
    for z in (zb + 0.45, zb + 1.2):
        k.put(box(0.05, 0.64, 0.05), "BH_Iron", M=T(x1 + 0.08, 0.05, z))
    k.put(ico(0.03, 0), "BH_Brass", M=T(x1 + 0.09, -0.18, zb + 0.8))
    # driver's footboard and a water keg on it
    k.put(box(0.36, 2 * hw + 0.1, 0.05, bev=0.01), "BH_WoodDark", M=T(x1 + 0.2, 0, zb - 0.05), tint=0.5)
    for sy in (-1, 1):
        beam(k, (x1 + 0.34, sy * hw, zb - 0.07), (x1 - 0.05, sy * hw, zb - 0.4), 0.05, tint=0.45)
    keg(k, TRS(x1 + 0.2, 0.42, zb - 0.025, 0, 0, 20), 0.36, 0.13, tint=0.55)

    # --- the bow-top: hoops over the body, sagging black cover between them, laced end panel at the back
    hoops = [x0 - 0.06, -1.25, -0.6, 0.05, 0.7, x1 + 0.02]
    for x in hoops:
        end = x in (hoops[0], hoops[-1])
        rr_ = 0.03 if end else -0.01   # inner hoops sit just under the cloth (ridges), the end hoops show
        pts = [(x, -math.cos(math.pi * i / 12) * (Rc + rr_), zs + math.sin(math.pi * i / 12) * (Hc + rr_))
               for i in range(13)]
        k.put(tube(pts, 0.03, 5 if end else 4, flat=(1.0, 0.7)), "BH_WoodDark", tint=0.45, smooth=40)
    cx0, cx1 = x0 - 0.16, x1 + 0.1

    def cover(u, v):
        x = lerp(cx0, cx1, u)
        a = math.pi * v
        # sag toward the axis between hoops, relaxed over the ends
        seg = 0.0
        for h0, h1 in zip(hoops[:-1], hoops[1:]):
            if h0 <= x <= h1:
                seg = math.sin(math.pi * (x - h0) / (h1 - h0))
        sag = 0.045 * seg * math.sin(a) ** 0.6
        rr = 1.0 - sag / Rc
        y = -math.cos(a) * (Rc + 0.05) * rr
        z = zs + math.sin(a) * (Hc + 0.05) * rr
        # the loose skirt at both sides drops a little below the rail
        if v < 0.04 or v > 0.96:
            z -= 0.08
        z += mnoise.noise(Vector((x * 1.7, a * 1.3, 0.3)) + k.noff) * 0.02
        return (x, y, z)
    surface(k, cover, 26, 14, "BH_ClothBlack", 0.025, 0.8, 40)
    # tattered hem along both sides: ragged strips hanging off the springing
    for sy in (-1, 1):
        for i in range(16):
            x = lerp(cx0 + 0.1, cx1 - 0.1, (i + 0.5) / 16)
            L = r.uniform(0.08, 0.2)
            k.put(box(0.2, 0.012, L), "BH_ClothBlack", M=TRS(x, sy * (Rc + 0.08), zs - 0.06 - L / 2, r.uniform(-6, 6) * sy, 0,
                                                            r.uniform(-4, 4)), tint=0.7)
    # back end panel: gathered cloth fan closed with lacing
    def back(u, v):
        a = math.pi * u
        rad = (1.0 - v) + 0.0
        y = -math.cos(a) * (Rc + 0.04) * rad
        z = zs - 0.05 + math.sin(a) * (Hc + 0.04) * rad
        fold = math.sin(u * math.pi * 9) * 0.03 * rad
        return (cx0 + 0.04 - fold - 0.06 * (1 - rad), y, z)
    surface(k, back, 18, 4, "BH_ClothBlack", 0.02, 0.7, 40)
    k.put(tube([(cx0 + 0.02, 0.0, zs - 0.05), (cx0 + 0.02, 0.0, zs + Hc)], 0.01, 4), "BH_Rope")
    # patches (a lighter sacking and an old red one) and rope lashings over the hoops, pegged to the rails
    for (pu0, pu1, pv0, pv1, mat) in ((0.23, 0.29, 0.2, 0.29, "BH_ClothViolet"), (0.62, 0.67, 0.58, 0.66, "BH_ClothRed"),
                                      (0.46, 0.5, 0.1, 0.16, "BH_ClothViolet")):
        def patch(u, v, a=(pu0, pu1, pv0, pv1)):
            # irregular sewn-on patch: the edges wander so it never reads as a clean rectangle
            uu = lerp(a[0], a[1], 0.5 + (u - 0.5) * (1.0 + 0.3 * math.sin(v * 5.0 + a[0] * 20)))
            vv = lerp(a[2], a[3], 0.5 + (v - 0.5) * (1.0 + 0.3 * math.cos(u * 6.0 + a[2] * 30)))
            x, y, z = cover(uu, vv)
            n_ = Vector((0, y, z - zs)).normalized()
            return (x, y + n_.y * 0.018, z + n_.z * 0.018)
        surface(k, patch, 4, 4, mat, 0.006, 0.55)
    for x in (-1.58, 1.02):
        pts = []
        for i in range(15):
            a = math.pi * i / 14
            pts.append((x, -math.cos(a) * (Rc + 0.09), zs + math.sin(a) * (Hc + 0.08)))
        k.put(tube(pts, 0.013, 4), "BH_Rope", smooth=40)
        for sy in (-1, 1):
            k.put(torus(0.03, 0.008, 6, 3), "BH_Iron", M=TRS(x, sy * (hw + 0.1), zs - 0.02, 90, 0, 0))

    # --- stove pipe through a tin collar in the cover, rain hat, guy wire
    px, py = -1.45, 0.42
    zc_ = zs + math.sin(math.acos(py / (Rc + 0.05))) * (Hc + 0.05)
    k.put(cyl(0.055, 3.22 - zc_ + 0.3, 8), "BH_Iron", M=T(px, py, zc_ - 0.3), smooth=40)
    k.put(cyl(0.12, 0.05, 8, r2=0.07), "BH_Iron", M=T(px, py, zc_ - 0.03), tint=0.6)
    k.put(cyl(0.13, 0.08, 8, r2=0.0), "BH_Iron", M=T(px, py, 3.3), smooth=None)
    for sx in (-1, 1):
        k.put(cyl(0.006, 0.1, 3), "BH_Iron", M=T(px + sx * 0.08, py, 3.2))
    k.put(tube([(px, py, 3.1), (px - 0.4, py + 0.2, zc_ - 0.18)], 0.004, 3), "BH_Iron")

    # --- a rolled carpet and a bedroll lashed along the crown of the cover
    ztop_ = zs + Hc + 0.05
    k.put(cyl(0.1, 1.3, 10), "BH_ClothRed", M=TRS(-1.35, -0.06, ztop_ + 0.07, 0, 90, 0), tint=0.7, smooth=40)
    k.put(cyl(0.045, 1.34, 8), "BH_Velvet", M=TRS(-1.37, -0.06, ztop_ + 0.07, 0, 90, 0), tint=0.6)  # rolled core
    k.put(cyl(0.085, 0.6, 8), "BH_Cloth", M=TRS(-0.05, 0.1, ztop_ + 0.07, 0, 90, 0) @ S(1.0, 1.0, 1.0), tint=0.6, smooth=40)
    for (x, y, rr) in ((-1.1, -0.06, 0.104), (-0.35, -0.06, 0.104), (0.1, 0.1, 0.09), (0.4, 0.1, 0.09)):
        k.put(torus(rr, 0.01, 10, 3), "BH_Rope", M=TRS(x, y, ztop_ + 0.07, 0, 90, 0))
    # --- raven on the front hoop crown
    raven(k, TRS(x1 + 0.02, -0.08, zs + Hc + 0.06, 0, 0, -35), 1.5)

    # --- hatch opening: dark cubby with shelves of wares seen through it
    k.put(box(ox1 - ox0, 0.04, oz1 - oz0 + 0.1), "BH_WoodDark", M=T((ox0 + ox1) / 2, -0.22, (oz0 + oz1) / 2), tint=0.2)
    k.put(box(ox1 - ox0, hw - 0.2, 0.03), "BH_WoodDark", M=T((ox0 + ox1) / 2, -(hw + 0.2) / 2, oz1 + 0.03), tint=0.25)
    k.put(box(ox1 - ox0, hw - 0.2, 0.03), "BH_WoodDark", M=T((ox0 + ox1) / 2, -(hw + 0.2) / 2, oz0 - 0.015), tint=0.3)
    for x in (ox0 + 0.01, ox1 - 0.01):
        k.put(box(0.03, hw - 0.2, oz1 - oz0), "BH_WoodDark", M=T(x, -(hw + 0.2) / 2, (oz0 + oz1) / 2), tint=0.25)
    k.put(box(ox1 - ox0, 0.2, 0.025), "BH_WoodDark", M=T((ox0 + ox1) / 2, -0.33, oz0 + 0.24), tint=0.35)
    jars = ("BH_GemGreen", "BH_Bottle", "BH_GemViolet", "BH_Bone", "BH_GemAmber", "BH_Bottle", "BH_Bone", "BH_GemGreen")
    for i, m in enumerate(jars):
        x = ox0 + 0.12 + i * 0.17
        if m in ("BH_Bone", "BH_Bottle"):
            k.put(cyl(0.045, 0.13, 6), m, M=T(x, -0.32, oz0 + 0.255), tint=0.6)
            k.put(cyl(0.05, 0.02, 6), "BH_Leather", M=T(x, -0.32, oz0 + 0.385), tint=0.6)
        else:
            potion(k, T(x, -0.32, oz0 + 0.255), m, 0.16, 0.04, "lo")
    for i in range(4):  # dried things hung inside the opening top
        x = ox0 + 0.25 + i * 0.35
        k.put(cyl(0.004, 0.14, 3), "BH_Rope", M=T(x, -0.4, oz1 - 0.14))
        t = ico(0.035, 0)
        for v in t.verts:
            v.co.z *= 2.2
        k.put(t, ("BH_Bark", "BH_Moss", "BH_Bone", "BH_Bark")[i], M=T(x, -0.4, oz1 - 0.2), tint=0.6)

    # --- the let-down hatch: board with a velvet cloth over it, iron straps, chains to the opening's top corners
    hzt = oz0 + 0.02          # counter top
    hcx = (ox0 + ox1) / 2
    hy = -hw - 0.04 - hd / 2
    k.put(box(ox1 - ox0 - 0.02, hd, 0.045, bev=0.008), "BH_WoodDark", M=T(hcx, hy, hzt - 0.022), tint=0.45)
    for x in (ox0 + 0.12, ox1 - 0.12):
        k.put(box(0.04, hd + 0.01, 0.05), "BH_Iron", M=T(x, hy, hzt - 0.03))
        k.put(cyl(0.02, 0.1, 6), "BH_Iron", M=TRS(x, -hw - 0.04, hzt - 0.03, 0, 90, 0) @ T(0, 0, -0.05))  # hinge knuckle
    k.put(box(ox1 - ox0 - 0.2, hd - 0.06, 0.01), "BH_Velvet", M=T(hcx + 0.05, hy + 0.02, hzt + 0.004), tint=0.8)

    def hang(u, v):
        return (lerp(ox0 + 0.2, ox1 - 0.1, u), hy - hd / 2 + 0.02 - 0.01 * v,
                hzt + 0.005 - 0.13 * v - 0.03 * math.sin(u * math.pi * 5) ** 2 * v)
    surface(k, hang, 10, 2, "BH_Velvet", 0.01, 0.7)
    for x in (ox0 + 0.02, ox1 - 0.02):
        chain(k, (x, -hw - 0.06, oz1 - 0.02), (x, hy - hd / 2 + 0.04, hzt + 0.02), 0.015)

    # --- curios on the counter
    casket(k, TRS(ox0 + 0.26, hy + 0.06, hzt, 0, 0, 8), 0.32, 0.2, 0.16, "BH_WoodDark", "BH_Brass")
    casket(k, TRS(ox0 + 0.28, hy + 0.08, hzt + 0.16, 0, 0, -12), 0.18, 0.12, 0.1, "BH_Velvet", "BH_Gold")
    skull(k, TRS(ox0 + 0.62, hy + 0.02, hzt + 0.06, 0, 0, 14), 0.75)
    k.put(cyl(0.02, 0.07, 6), "BH_Candle", M=T(ox0 + 0.63, hy + 0.04, hzt + 0.125))
    flame_tip(k, T(ox0 + 0.63, hy + 0.04, hzt + 0.2), 0.04)
    for (dx, dy, m, kind, h) in ((0.84, 0.1, "BH_GemGreen", "round", 0.2), (0.96, -0.02, "BH_GemViolet", "tall", 0.26),
                                 (1.07, 0.12, "BH_GemAmber", "squat", 0.16)):
        potion(k, T(ox0 + dx, hy + dy, hzt), m, h, 0.05, kind)
    # a coiled-neck flask
    k.put(ico(0.05, 1), "BH_GemGreen", M=T(ox0 + 1.2, hy - 0.05, hzt + 0.05), smooth=50)
    k.put(tube([(0, 0, 0.09), (0.03, 0.0, 0.13), (0.0, 0.03, 0.17), (-0.03, 0.0, 0.2), (0.0, -0.02, 0.24)], 0.009, 4),
          "BH_Bottle", M=T(ox0 + 1.2, hy - 0.05, hzt), smooth=40)
    scroll(k, TRS(ox0 + 0.86, hy - 0.14, hzt, 0, 0, -8), 0.3, 0.024, "BH_ClothBlack", seal=True)
    idol(k, TRS(ox1 - 0.16, hy + 0.1, hzt + 0.01, 0, 0, 10), 0.9)
    for i in range(6):
        k.put(cyl(0.016, 0.005, 7), "BH_Gold", M=TRS(ox0 + 0.5 + r.uniform(-0.07, 0.07), hy - 0.12 + r.uniform(-0.04, 0.04),
                                                   hzt + 0.005 + 0.004 * (i % 3), r.uniform(-8, 8), 0, 0))
    k.put(box(0.12, 0.07, 0.035, bev=0.006), "BH_Leather", M=TRS(ox0 + 0.42, hy - 0.14, hzt + 0.018, 0, 0, 20), tint=0.7)

    # --- lantern on an iron arm at the hatch's right corner (light_a); charms hung over the counter
    lx, ly = ox1 + 0.05, -hw - 0.05
    k.put(tube([(lx, ly, zs - 0.1), (lx, ly - 0.16, zs + 0.02), (lx, ly - 0.3, zs + 0.02)], 0.014, 5), "BH_Iron")
    k.put(tube([(lx, ly, zs - 0.35), (lx, ly - 0.2, zs + 0.0)], 0.01, 4), "BH_Iron")
    lp_ = lantern_on_hook(k, lx, ly - 0.3, zs - 0.0, 0.46)
    light = (lp_[0], lp_[1], lp_[2] - 0.22)  # just under the lantern (the game light is unshadowed)
    k.put(tube([(lx, ly - 0.3, zs + 0.02), (lx, ly - 0.3, zs - 0.02)], 0.006, 3), "BH_Iron")
    for i, x in enumerate((ox0 + 0.2, ox0 + 0.55)):
        L = 0.24 + 0.08 * i
        k.put(cyl(0.004, L, 3), "BH_Rope", M=T(x, -hw - 0.12, zs - 0.02 - L))
        for j in range(3):
            k.put(ico(0.014, 0), ("BH_Bone", "BH_GemViolet", "BH_Bone")[j], M=T(x, -hw - 0.12, zs - 0.06 - L * (j + 1) / 3))
    bone(k, TRS(ox0 + 0.9, -hw - 0.12, zs - 0.3, 0, 0, 0) @ T(-0.1, 0, 0), 0.2, 0.012)
    k.put(tube([(ox0 + 0.82, -hw - 0.12, zs - 0.02), (ox0 + 0.8, -hw - 0.12, zs - 0.3)], 0.003, 3), "BH_Rope")
    k.put(tube([(ox0 + 1.0, -hw - 0.12, zs - 0.02), (ox0 + 1.0, -hw - 0.12, zs - 0.3)], 0.003, 3), "BH_Rope")

    # --- shafts resting on a log, a horse collar leaned against it
    for sy in (-1, 1):
        pts = [(0.82, sy * 0.36, zb - 0.26), (1.5, sy * 0.52, 0.66), (2.0, sy * 0.56, 0.44), (2.36, sy * 0.56, 0.36)]
        k.put(tube(pts, [0.05, 0.045, 0.04, 0.035], 6), "BH_WoodDark", tint=0.45, smooth=40)
        k.put(cyl(0.045, 0.06, 6, caps=False), "BH_Iron", M=TRS(2.28, sy * 0.56, 0.37, 0, 102, 0))
    k.put(cyl(0.035, 1.0, 6), "BH_WoodDark", M=TRS(1.62, 0.5, 0.62, 90, 0, 0), tint=0.45)  # swingle bar
    k.put(tube([(2.06, -0.72, 0.14), (2.06, 0.72, 0.14)], 0.15, 7), "BH_Bark", tint=0.6, smooth=40)
    t = torus(0.2, 0.06, 12, 6)
    for v in t.verts:
        v.co.y *= 1.3
    k.put(t, "BH_Leather", M=TRS(1.83, -0.2, 0.3, 0, 72, 0), tint=0.7, smooth=40)  # horse collar leaned on the log

    # --- rear rack with a strapped trunk, bucket hung under the back
    k.put(box(0.34, 2 * hw, 0.05, bev=0.01), "BH_WoodDark", M=T(x0 - 0.2, 0, zb - 0.12), tint=0.45)
    for sy in (-1, 1):
        beam(k, (x0 - 0.36, sy * (hw - 0.05), zb - 0.12), (x0 - 0.02, sy * (hw - 0.05), zb - 0.45), 0.05, tint=0.45)
    k.put(box(0.3, 0.8, 0.36, bev=0.02), "BH_Leather", M=T(x0 - 0.2, 0.1, zb - 0.1 + 0.18), tint=0.6)
    for y in (-0.15, 0.35):
        k.put(box(0.32, 0.04, 0.38), "BH_Iron", M=T(x0 - 0.2, y, zb - 0.1 + 0.18))
    k.put(cyl(0.12, 0.2, 8, r2=0.14), "BH_Wood", M=T(-0.3, 0.3, zb - 0.55), tint=0.5)
    k.put(tube([(-0.42, 0.3, zb - 0.35), (-0.3, 0.3, zb - 0.16), (-0.18, 0.3, zb - 0.35)], 0.006, 3), "BH_Iron")

    # --- sockets and collision
    k.sockets.append(("npc", (-0.78, -1.52, 0.0)))
    k.sockets.append(("customer", (0.45, -2.2, 0.0)))
    k.sockets.append(("light_a", light))
    k.col_box(x1 - x0 + 0.1, 2 * hw + 0.1, 2.2, T((x0 + x1) / 2, 0, 1.1))
    for sy in (-1, 1):
        k.col_box(1.36, 0.22, 1.3, T(-1.15, sy * 0.95, 0.65))
    k.col_box(ox1 - ox0, hd + 0.04, hzt + 0.05, T(hcx, hy, (hzt + 0.05) / 2))
    k.col_box(1.1, 1.5, 0.7, T(1.9, 0, 0.35))
    k.col_box(0.4, 2 * hw, 0.9, T(x0 - 0.2, 0, 0.45))
    return dict(recenter=False)
