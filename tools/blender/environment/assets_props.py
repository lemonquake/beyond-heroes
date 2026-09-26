"""Props / storytelling pieces and breakables (intact + fragments).

Wood is built from individual planks (chipped, jittered, per-plank tint), iron gets rivets, stone gets chips.
Breakables register `fragments=True` and put each piece into a fragment group as well as the intact mesh.
Sockets (child empties) mark where the game attaches lights/flames: `flame`, `light`.
"""
import math

import bmesh
from mathutils import Vector

from kit import *  # noqa
from masonry import *  # noqa
from registry import asset


# ---------------------------------------------------------------------------------------------------------------
# shared helpers
def plank(k, L, w, th, M, mat="BH_Wood", tint=(0.7, 1.0), group=None, chips=1, main=True, warp=0.0):
    r = k.r
    t = box(L, w, th, bev=min(0.012, th * 0.3))
    if warp:
        bmesh.ops.subdivide_edges(t, edges=[e for e in t.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > L * 0.5],
                                  cuts=3)
        for v in t.verts:
            v.co.z += warp * math.sin((v.co.x / L + 0.5) * math.pi)
    if chips:
        chip(t, r, r.randint(0, chips), min(0.03, th * 0.5))
    jitter(t, r, 0.003)
    k.put(t, mat, M=M, tint=r.uniform(*tint) if isinstance(tint, tuple) else tint, group=group, main=main)


def rivet(k, M, r_=0.018, group=None):
    k.put(cyl(r_, 0.012, 6), "BH_Iron", M=M, group=group)


def frag_put(k, t, mat, seeds, tint=1.0, smooth=None, first=0):
    """Put the closed temp bmesh t (already in asset space) into the intact mesh and its Voronoi pieces into
    fragment groups g<first+i>."""
    for i in range(len(seeds)):
        c = voronoi_clip(t, seeds, i)
        if c is not None:
            k.put(c, mat, tint=tint, smooth=smooth, uvoff=False, group="g%02d" % (first + i), main=False)
    k.put(t, mat, tint=tint, smooth=smooth, uvoff=False)


def xform(t, M):
    bmesh.ops.transform(t, matrix=M, verts=t.verts)
    if M.determinant() < 0:
        bmesh.ops.reverse_faces(t, faces=t.faces)
    return t


def wheel(k, M, R_=0.5, spokes=8, broken=0, mat="BH_Wood"):
    """Cart wheel in the XZ plane (axle along Y). broken: number of missing spokes/rim sections."""
    r = k.r
    k.put(torus(R_ - 0.03, 0.05, 20, 6), mat, M=M @ R(90, 0, 0), tint=r.uniform(0.7, 0.9), smooth=40)
    k.put(torus(R_, 0.022, 24, 4), "BH_Iron", M=M @ R(90, 0, 0), smooth=40)
    k.put(cyl(0.09, 0.22, 10, bev=0.01), mat, M=M @ TRS(0, 0.11, 0, 90, 0, 0), tint=0.6)
    k.put(cyl(0.1, 0.04, 10), "BH_Iron", M=M @ TRS(0, 0.13, 0, 90, 0, 0))
    for i in range(spokes):
        if i < broken:
            continue
        a = 360.0 * i / spokes
        L = R_ - 0.12
        k.put(box(0.05, 0.045, L, bev=0.008), mat, M=M @ R(0, a, 0) @ T(0, 0, 0.07 + L / 2), tint=r.uniform(0.7, 0.95))


def hay(k, M, size=(1.4, 0.9, 0.5)):
    t = ico(1.0, 2)
    for v in t.verts:
        v.co = Vector((v.co.x * size[0] / 2, v.co.y * size[1] / 2, max(v.co.z, -0.2) * size[2]))
    ndisp(t, 3.0, 0.08, k.noff)
    jitter(t, k.r, 0.03)
    k.put(t, "BH_Thatch", M=M, tint=k.r.uniform(0.85, 1.05), tile=1.0)
    for i in range(14):
        s = card(0.02, k.r.uniform(0.2, 0.4))
        k.put(s, "BH_Thatch", M=M @ TRS(k.r.uniform(-0.6, 0.6) * size[0] / 1.4, k.r.uniform(-0.35, 0.35) * size[1] / 0.9,
                                           size[2] * 0.6, k.r.uniform(-60, 60), k.r.uniform(-60, 60), k.r.uniform(0, 180)),
              uv="keep", tint=0.9)


def skull(k, M, s=1.0, group=None):
    """Stylised skull ~0.22 m long looking toward -Y."""
    t = ico(0.1 * s, 2)
    for v in t.verts:
        v.co.y *= 1.15
        if v.co.z < -0.02 * s:
            v.co.z = -0.02 * s + (v.co.z + 0.02 * s) * 0.4
    k.put(t, "BH_Bone", M=M, tint=k.r.uniform(0.75, 1.0), smooth=50, group=group)
    k.put(box(0.12 * s, 0.09 * s, 0.07 * s, bev=0.02 * s), "BH_Bone", M=M @ T(0, -0.07 * s, -0.05 * s),
          tint=k.r.uniform(0.7, 0.9), group=group)
    for sx in (-1, 1):  # eye sockets (dark insets)
        k.put(cyl(0.024 * s, 0.03 * s, 8), "BH_StoneDark", M=M @ TRS(sx * 0.037 * s, -0.103 * s, 0.01 * s, 90, 0, 0),
              tint=0.05, group=group)
    k.put(cyl(0.014 * s, 0.03 * s, 3), "BH_StoneDark", M=M @ TRS(0, -0.118 * s, -0.025 * s, 90, 0, 0), tint=0.05,
          group=group)


def bone(k, M, L=0.4, r_=0.02):
    t = tube([(0, 0, 0), (L * 0.5, 0, 0.006), (L, 0, 0)], [r_ * 0.9, r_ * 0.7, r_ * 0.9], 6)
    k.put(t, "BH_Bone", M=M, tint=k.r.uniform(0.7, 0.95), smooth=50)
    for x in (0.0, L):
        for dy in (-1, 1):
            k.put(ico(r_ * 1.25, 1), "BH_Bone", M=M @ T(x, dy * r_ * 0.7, 0), tint=k.r.uniform(0.75, 0.95), smooth=50)


def flame_tip(k, M, h=0.05):
    t = cyl(h * 0.28, h, 6, r2=0.0)
    k.put(t, "BH_Flame", M=M, uvoff=False)


def sword(k, M, L=1.0, broken=False):
    blade = L * (0.45 if broken else 0.75)
    t = box(0.055, 0.012, blade, bev=0.004)
    if not broken:
        slice_plane(t, (0.0, 0, blade / 2 - 0.04), (0.6, 0, 1))
        slice_plane(t, (0.0, 0, blade / 2 - 0.04), (-0.6, 0, 1))
    else:
        slice_plane(t, (0.0, 0, blade / 2 - 0.02), (0.35, 0, 1))
    k.put(t, "BH_Metal", M=M @ T(0, 0, 0.2 + blade / 2), tint=k.r.uniform(0.6, 0.9))
    k.put(box(0.22, 0.03, 0.03, bev=0.006), "BH_Iron", M=M @ T(0, 0, 0.2))
    k.put(cyl(0.017, 0.18, 6), "BH_WoodDark", M=M @ T(0, 0, 0.02), tint=0.7)
    k.put(ico(0.03, 1), "BH_Iron", M=M @ T(0, 0, 0.0))


def shield_round(k, M, R_=0.34):
    k.put(cyl(R_, 0.04, 16, bev=0.008), "BH_Wood", M=M, tint=k.r.uniform(0.6, 0.8))
    k.put(torus(R_, 0.018, 20, 4), "BH_Iron", M=M @ T(0, 0, 0.02))
    k.put(ico(0.07, 1), "BH_Iron", M=M @ TRS(0, 0, 0.04, s=(1, 1, 0.55)))
    for i in range(8):
        a = math.tau * i / 8
        rivet(k, M @ T(math.cos(a) * (R_ - 0.05), math.sin(a) * (R_ - 0.05), 0.04))


def helmet(k, M):
    t = lathe([(0.0, 0.26), (0.08, 0.25), (0.13, 0.2), (0.15, 0.1), (0.155, 0.0)], 14, cap_top=False)
    k.put(t, "BH_Iron", M=M, smooth=50, tint=0.9)
    k.put(box(0.05, 0.02, 0.14, bev=0.005), "BH_Iron", M=M @ T(0, -0.15, 0.05))
    k.put(torus(0.155, 0.012, 16, 4), "BH_Iron", M=M @ T(0, 0, 0.005))


# ---------------------------------------------------------------------------------------------------------------
# breakables
@asset("crate", "props", fragments=True)
def crate(k):
    r = k.r
    S = 0.9
    faces = {"top": R(0, 0, 0), "bottom": R(180, 0, 0), "px": R(0, 90, 0), "nx": R(0, -90, 0),
             "py": R(-90, 0, 0), "ny": R(90, 0, 0)}
    gi = 0
    for fname, Rf in faces.items():
        Mf = T(0, 0, S / 2) @ Rf @ T(0, 0, S / 2 - 0.025)
        side = fname not in ("top", "bottom")
        n = 3
        w = (S - 0.16) / n
        groups = []
        for i in range(n):
            g = "g%02d" % (gi + (1 if side and i == 2 else 0))
            groups.append(g)
            y = -S / 2 + 0.08 + w * (i + 0.5)
            plank(k, S - 0.16, w - 0.012, 0.035, Mf @ T(0, y, 0), group=g, warp=0.004)
        # diagonal brace on sides
        if side:
            d = math.hypot(S - 0.16, S - 0.16)
            plank(k, d - 0.06, 0.08, 0.03, Mf @ TRS(0, 0, 0.03, 0, 0, 45), mat="BH_WoodDark", group=groups[0])
        # battens along two edges of this face
        for sy in (-1, 1):
            plank(k, S, 0.08, 0.05, Mf @ T(0, sy * (S / 2 - 0.04), 0.01), mat="BH_WoodDark",
                  group=groups[0] if sy < 0 else groups[-1])
            for sx in (-1, 1):
                rivet(k, Mf @ T(sx * (S / 2 - 0.06), sy * (S / 2 - 0.04), 0.036), 0.012,
                      group=groups[0] if sy < 0 else groups[-1])
        gi += 2 if side else 1
    # iron corner caps on the top/bottom groups
    for sz, g in ((1, "g00"), (-1, "g01")):
        for sx in (-1, 1):
            for sy in (-1, 1):
                k.put(box(0.1, 0.1, 0.1, bev=0.01), "BH_Iron",
                      M=T(sx * (S / 2 - 0.035), sy * (S / 2 - 0.035), S / 2 + sz * (S / 2 - 0.035)), group=g)
    k.col_box(S, S, S, T(0, 0, S / 2))
    return dict(recenter=True)


def _stave(a0, a1, prof, H, th, nz=8):
    t = tb()
    rings = []
    for i in range(nz + 1):
        z = H * i / nz
        rr = prof(z)
        ring = [(math.cos(a0) * rr, math.sin(a0) * rr, z), (math.cos(a1) * rr, math.sin(a1) * rr, z),
                (math.cos(a1) * (rr - th), math.sin(a1) * (rr - th), z), (math.cos(a0) * (rr - th), math.sin(a0) * (rr - th), z)]
        rings.append([t.verts.new(p) for p in ring])
    for i in range(nz):
        a, b = rings[i], rings[i + 1]
        for j in range(4):
            j2 = (j + 1) % 4
            t.faces.new((a[j], a[j2], b[j2], b[j]))
    t.faces.new(rings[0][::-1])
    t.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(t, faces=t.faces)
    return t


@asset("barrel", "props", fragments=True)
def barrel(k):
    r = k.r
    H, rE, bul = 1.05, 0.33, 0.07

    def prof(z):
        return rE + bul * math.sin(math.pi * z / H)
    n = 18
    for i in range(n):
        a0 = math.tau * i / n + 0.004
        a1 = math.tau * (i + 1) / n - 0.004
        t = _stave(a0, a1, prof, H, 0.035)
        jitter(t, r, 0.002)
        g = "g%02d" % (i * 5 // n)
        k.put(t, "BH_Wood", tint=r.uniform(0.55, 0.85), group=g, rotuv=True)
    for z, g in ((0.1, "g05"), (0.3, "g05"), (H - 0.3, "g06"), (H - 0.1, "g06")):
        k.put(torus(prof(z) + 0.004, 0.016, 28, 4, ), "BH_Iron", M=T(0, 0, z), smooth=40, group=g)
    for z, g in ((0.07, "g05"), (H - 0.1, "g06")):
        k.put(cyl(rE - 0.005, 0.035, 18), "BH_WoodDark", M=T(0, 0, z), tint=0.8, group=g)
    # bung + stencil band
    k.put(cyl(0.035, 0.03, 8), "BH_WoodDark", M=TRS(prof(H / 2), 0, H / 2, 0, 90, 0), group="g00")
    k.col_mesh(cyl(rE + bul * 0.7, H, 10))
    return dict(recenter=True)


@asset("urn", "props", fragments=True)
def urn(k):
    r = k.r
    prof = [(0.1, 0.0), (0.17, 0.03), (0.26, 0.2), (0.29, 0.34), (0.25, 0.5), (0.15, 0.62), (0.1, 0.7), (0.1, 0.76),
            (0.15, 0.8), (0.14, 0.84)]
    seeds = [(r.uniform(-0.25, 0.25), r.uniform(-0.25, 0.25), r.uniform(0.05, 0.8)) for _ in range(9)]
    frag_put(k, lathe(prof, 16), "BH_Brick", seeds, tint=0.85, smooth=45)
    frag_put(k, xform(torus(0.285, 0.018, 20, 4), T(0, 0, 0.36)), "BH_StoneDark", seeds, tint=0.5, smooth=45)
    frag_put(k, xform(torus(0.2, 0.014, 18, 4), T(0, 0, 0.56)), "BH_StoneDark", seeds, tint=0.5, smooth=45)
    for sx in (-1, 1):  # handles
        t = tube([(sx * 0.12, 0, 0.7), (sx * 0.24, 0, 0.72), (sx * 0.25, 0, 0.55)], 0.022, 6)
        k.put(t, "BH_Brick", tint=0.8, smooth=40, group="g00" if sx < 0 else "g01")
    k.col_mesh(cyl(0.27, 0.84, 8))
    return dict(recenter=True)


@asset("statue_small", "props", fragments=True)
def statue_small(k):
    r = k.r
    seeds = [(r.uniform(-0.3, 0.3), r.uniform(-0.3, 0.3), z) for z in (0.15, 0.2, 0.55, 0.75, 0.95, 1.1, 1.25, 1.45, 0.6, 1.0)]
    base = box(0.7, 0.7, 0.3, bev=0.03)
    chip(base, r, 2, 0.05)
    frag_put(k, xform(base, T(0, 0, 0.15)), "BH_Stone", seeds, tint=0.8)
    robe = lathe([(0.26, 0.0), (0.24, 0.3), (0.2, 0.6), (0.19, 0.8), (0.22, 0.95), (0.12, 1.05), (0.06, 1.1)], 12)
    ndisp(robe, 6.0, 0.012, k.noff)
    frag_put(k, xform(robe, T(0, 0, 0.3)), "BH_Stone", seeds, tint=0.95, smooth=35)
    head = ico(0.11, 2)
    for v in head.verts:
        v.co.z *= 1.15
    frag_put(k, xform(head, T(0, -0.02, 1.52)), "BH_Stone", seeds, tint=1.0, smooth=50)
    hood = lathe([(0.14, 0.0), (0.15, 0.1), (0.12, 0.22), (0.0, 0.28)], 12, cap_bot=True)
    frag_put(k, xform(hood, T(0, 0.03, 1.4)), "BH_Stone", seeds, tint=0.9, smooth=40)
    for sx in (-1, 1):  # praying arms
        t = tube([(sx * 0.2, 0, 1.3), (sx * 0.2, -0.12, 1.1), (sx * 0.04, -0.2, 1.18)], [0.05, 0.045, 0.04], 6)
        k.put(t, "BH_Stone", tint=0.9, smooth=40, group="g%02d" % (7 if sx < 0 else 8))
    k.col_box(0.7, 0.7, 1.7, T(0, 0, 0.85))
    return dict(recenter=True)


# ---------------------------------------------------------------------------------------------------------------
# furniture / camp
@asset("table", "props")
def table(k):
    r = k.r
    L, W, H = 2.0, 0.95, 0.8
    n = 4
    for i in range(n):
        plank(k, L, W / n - 0.012, 0.06, T(0, -W / 2 + W / n * (i + 0.5), H - 0.03), warp=0.005)
    for sx in (-1, 1):
        plank(k, W - 0.1, 0.1, 0.05, TRS(sx * (L / 2 - 0.25), 0, H - 0.085, 0, 0, 90), mat="BH_WoodDark")
        for sy in (-1, 1):
            k.put(box(0.09, 0.09, H - 0.11, bev=0.01), "BH_WoodDark", M=T(sx * (L / 2 - 0.2), sy * (W / 2 - 0.12), (H - 0.11) / 2),
                  tint=r.uniform(0.7, 0.9))
        plank(k, W - 0.3, 0.07, 0.05, TRS(sx * (L / 2 - 0.2), 0, 0.22, 0, 0, 90), mat="BH_WoodDark")
    plank(k, L - 0.45, 0.07, 0.05, T(0, 0, 0.22), mat="BH_WoodDark")
    # clutter: tankard, plate, candle stub
    k.put(cyl(0.05, 0.12, 10), "BH_Iron", M=T(0.4, 0.15, H))
    k.put(cyl(0.13, 0.02, 14), "BH_Metal", M=T(-0.3, -0.1, H), tint=0.5)
    k.put(cyl(0.03, 0.09, 8), "BH_Candle", M=T(-0.75, 0.25, H))
    k.col_box(L, W, H, T(0, 0, H / 2))
    return dict(recenter=True)


@asset("chair", "props")
def chair(k):
    r = k.r
    S, H = 0.48, 0.46
    for i in range(3):
        plank(k, S, S / 3 - 0.01, 0.04, T(0, -S / 2 + S / 3 * (i + 0.5), H))
    for sx in (-1, 1):
        for sy in (-1, 1):
            h = H + (0.55 if sy > 0 else 0)
            k.put(box(0.05, 0.05, h, bev=0.008), "BH_WoodDark", M=T(sx * (S / 2 - 0.03), sy * (S / 2 - 0.03), h / 2),
                  tint=r.uniform(0.7, 0.9))
    for z in (H + 0.3, H + 0.5):
        plank(k, S - 0.04, 0.08, 0.03, TRS(0, S / 2 - 0.03, z, 90, 0, 0), mat="BH_WoodDark")
    k.col_box(S, S, H, T(0, 0, H / 2))
    return dict(recenter=True)


@asset("bookshelf", "props")
def bookshelf(k):
    r = k.r
    W, D, H = 1.6, 0.4, 2.2
    for sx in (-1, 1):
        plank(k, H, D, 0.05, TRS(sx * (W / 2 - 0.025), 0, H / 2, 0, 90, 0), mat="BH_WoodDark", warp=0.0)
    plank(k, W, D + 0.04, 0.06, T(0, 0, H - 0.03), mat="BH_WoodDark")
    plank(k, W - 0.1, 0.03, H - 0.1, T(0, D / 2 - 0.015, H / 2 + 0.02), mat="BH_WoodDark", tint=0.5, chips=0)
    shelves = [0.08, 0.6, 1.12, 1.64]
    for z in shelves:
        plank(k, W - 0.1, D - 0.02, 0.04, T(0, 0, z), mat="BH_Wood")
    for zi, z in enumerate(shelves):
        x = -W / 2 + 0.08
        while x < W / 2 - 0.15:
            if r.random() < 0.12:
                x += r.uniform(0.1, 0.25)
                continue
            bw = r.uniform(0.04, 0.08)
            bh = r.uniform(0.26, 0.42)
            lean = r.uniform(-8, 8) if r.random() < 0.2 else 0.0
            mat = r.choice(("BH_ClothRed", "BH_Cloth", "BH_Cloth", "BH_WoodDark"))
            k.put(box(bw, r.uniform(0.2, 0.28), bh, bev=0.008), mat, M=TRS(x + bw / 2, -0.02, z + 0.02 + bh / 2, 0, lean, 0),
                  tint=r.uniform(0.5, 1.0))
            x += bw + 0.005
        if zi == 3:
            skull(k, TRS(W / 2 - 0.2, -0.05, z + 0.12, 0, 0, 200), 0.8)
    for i in range(3):  # fallen books at the foot
        k.put(box(0.2, 0.28, 0.05, bev=0.008), r.choice(("BH_ClothRed", "BH_Cloth")),
              M=TRS(r.uniform(-0.5, 0.5), -D / 2 - 0.25, 0.025 + i * 0.05, 0, 0, r.uniform(0, 90)), tint=r.uniform(0.5, 0.9))
    k.col_box(W, D, H, T(0, 0, H / 2))
    return dict(recenter=True)


@asset("bed", "props")
def bed(k):
    r = k.r
    L, W = 2.1, 1.0
    for sy in (-1, 1):
        plank(k, L, 0.08, 0.2, T(0, sy * (W / 2 - 0.04), 0.3), mat="BH_WoodDark")
    for sx, h in ((-1, 1.0), (1, 0.6)):
        plank(k, W, 0.08, h, TRS(sx * (L / 2 - 0.04), 0, h / 2, 0, 0, 90), mat="BH_WoodDark")
    mat_ = box(L - 0.16, W - 0.12, 0.18, bev=0.06, seg=2)
    ndisp(mat_, 4.0, 0.015, k.noff)
    k.put(mat_, "BH_Cloth", M=T(0, 0, 0.45), tint=0.8, smooth=40)
    pil = box(0.35, W * 0.7, 0.12, bev=0.05, seg=2)
    k.put(pil, "BH_Cloth", M=TRS(-L / 2 + 0.3, 0, 0.58, 0, -8, 0), tint=1.0, smooth=40)
    blanket = box(L * 0.55, W - 0.04, 0.05, bev=0.02)
    subdiv(blanket, 3)
    for v in blanket.verts:
        if abs(v.co.y) > W / 2 - 0.1:
            v.co.z -= 0.1
    ndisp(blanket, 5.0, 0.02, k.noff)
    k.put(blanket, "BH_ClothRed", M=T(L * 0.18, 0, 0.56), tint=0.8, smooth=40)
    k.col_box(L, W, 0.6, T(0, 0, 0.3))
    return dict(recenter=True)


@asset("bedroll", "props")
def bedroll(k):
    t = box(1.8, 0.75, 0.05, bev=0.02)
    subdiv(t, 2)
    ndisp(t, 4.0, 0.015, k.noff)
    k.put(t, "BH_Cloth", M=T(0, 0, 0.03), tint=0.7, smooth=40)
    k.put(cyl(0.15, 0.75, 12), "BH_ClothRed", M=TRS(-0.95, 0, 0.15, 90, 0, 0) @ T(0, 0, -0.375), tint=0.7, smooth=40)
    for y in (-0.25, 0.25):
        k.put(torus(0.155, 0.012, 14, 4), "BH_Cloth", M=TRS(-0.95, y, 0.15, 90, 0, 0), tint=0.4)
    k.put(box(0.4, 0.3, 0.12, bev=0.04, seg=2), "BH_Cloth", M=T(0.6, 0, 0.1), tint=0.9, smooth=40)
    return dict(recenter=True)


@asset("rug", "props")
def rug(k):
    r = k.r
    L, W = 3.0, 2.0
    k.put(box(L, W, 0.02), "BH_ClothRed", M=T(0, 0, 0.01), tint=0.8, uvoff=False)
    for s, w in ((0.85, 0.12), (0.55, 0.06)):
        for sy in (-1, 1):
            k.put(box(L * s, w, 0.022), "BH_Cloth", M=T(0, sy * W * s * 0.4, 0.012), tint=0.9)
        for sx in (-1, 1):
            k.put(box(w, W * s * 0.8, 0.022), "BH_Cloth", M=T(sx * L * s * 0.5, 0, 0.012), tint=0.9)
    k.put(box(0.4, 0.4, 0.023), "BH_Gold", M=TRS(0, 0, 0.012, 0, 0, 45), tint=0.7)
    for sx in (-1, 1):
        for i in range(24):
            y = -W / 2 + W * (i + 0.5) / 24
            k.put(box(0.12, 0.012, 0.006), "BH_Cloth", M=TRS(sx * (L / 2 + 0.05), y, 0.004, 0, 0, r.uniform(-12, 12)), tint=0.8)
    return dict(recenter=True)


@asset("chest", "props")
def chest(k):
    r = k.r
    L, W, H = 1.0, 0.6, 0.5
    for i in range(3):
        plank(k, L, 0.03, H / 3 - 0.01, TRS(0, -W / 2 + 0.015, H / 6 + H / 3 * i), group=None)
        plank(k, L, 0.03, H / 3 - 0.01, TRS(0, W / 2 - 0.015, H / 6 + H / 3 * i))
    for sx in (-1, 1):
        plank(k, W - 0.06, 0.03, H, TRS(sx * (L / 2 - 0.015), 0, H / 2, 0, 0, 90))
    k.put(box(L - 0.06, W - 0.06, 0.03), "BH_WoodDark", M=T(0, 0, 0.03), tint=0.6)
    lid = [(math.cos(a) * W / 2, math.sin(a) * 0.2) for a in [math.pi * i / 8 for i in range(9)]]
    t = prism([(x, z) for x, z in lid], L)
    k.put(t, "BH_Wood", M=T(0, 0, H) @ R(0, 0, 90), tint=0.8, smooth=30)
    for x in (-L / 2 + 0.12, 0.0, L / 2 - 0.12):
        k.put(box(0.07, W + 0.02, H - 0.02), "BH_Iron", M=T(x, 0, H / 2))
        t = prism([(math.cos(a) * (W / 2 + 0.012), math.sin(a) * 0.212) for a in [math.pi * i / 8 for i in range(9)]], 0.07)
        k.put(t, "BH_Iron", M=T(x, 0, H) @ R(0, 0, 90))
    k.put(box(0.12, 0.04, 0.14, bev=0.01), "BH_Gold", M=T(0, -W / 2 - 0.02, H - 0.02))
    k.col_box(L, W, H + 0.2, T(0, 0, (H + 0.2) / 2))
    return dict(recenter=True)


@asset("coffin", "props")
def coffin(k):
    r = k.r
    # hexagonal coffin outline in XY (head toward +X)
    outline = [(-1.0, -0.2), (0.45, -0.33), (1.0, -0.24), (1.0, 0.24), (0.45, 0.33), (-1.0, 0.2)]

    def slab(z0, h, inset, mat, tint):
        t = tb()
        bot = [t.verts.new((x * (1 - inset), y * (1 - inset * 2), z0)) for x, y in outline]
        top = [t.verts.new((x * (1 - inset), y * (1 - inset * 2), z0 + h)) for x, y in outline]
        t.faces.new(bot[::-1])
        t.faces.new(top)
        for i in range(len(outline)):
            j = (i + 1) % len(outline)
            t.faces.new((bot[i], bot[j], top[j], top[i]))
        bmesh.ops.recalc_face_normals(t, faces=t.faces)
        _ = bmesh.ops.bevel(t, geom=list(t.edges), offset=0.012, segments=1, affect="EDGES", clamp_overlap=True)
        jitter(t, r, 0.003)
        k.put(t, mat, tint=tint)
    slab(0.0, 0.45, 0.0, "BH_WoodDark", 0.8)
    slab(0.45, 0.08, -0.02, "BH_WoodDark", 1.0)
    slab(0.53, 0.04, 0.08, "BH_Wood", 0.6)
    k.put(box(0.05, 0.3, 0.012), "BH_Iron", M=T(0.3, 0, 0.575))
    k.put(box(0.6, 0.05, 0.012), "BH_Iron", M=T(0.3, 0, 0.575))
    for x in (-0.7, 0.0, 0.7):
        for sy in (-1, 1):
            k.put(torus(0.04, 0.008, 10, 4), "BH_Iron", M=TRS(x, sy * (0.3 if x > 0.4 else 0.24), 0.28, 90, 0, 0))
    k.col_box(2.0, 0.66, 0.58, T(0, 0, 0.29))
    return dict(recenter=True)


@asset("campfire", "props")
def campfire(k):
    r = k.r
    n = 9
    for i in range(n):
        a = math.tau * i / n + r.uniform(-0.1, 0.1)
        t = rock(r, (0.18, 0.14, 0.12), cuts=6, subd=1, noise_amp=0.05, seed_off=i * 1.3)
        k.put(t, "BH_Stone", M=TRS(math.cos(a) * 0.55, math.sin(a) * 0.55, 0, 0, 0, math.degrees(a)), tint=r.uniform(0.5, 0.8))
    k.put(cyl(0.45, 0.02, 14), "BH_Dirt", M=T(0, 0, 0.0), tint=0.25)
    for i in range(5):
        a = math.tau * i / 5
        L = 0.7
        t = tube([(0, 0, 0), (L, 0, 0)], [0.055, 0.045], 7)
        k.put(t, "BH_Bark", M=TRS(math.cos(a) * 0.3, math.sin(a) * 0.3, 0.05, 0, -28, math.degrees(a) + 180), tint=0.35,
              smooth=40)
    for i in range(6):
        k.put(rock(r, (0.06, 0.05, 0.04), cuts=4, subd=1), "BH_Flame", M=T(r.uniform(-0.15, 0.15), r.uniform(-0.15, 0.15), 0.01),
              tint=0.3)
    k.sockets.append(("flame", (0, 0, 0.35)))
    k.col_mesh(cyl(0.65, 0.25, 8))
    return dict(recenter=False)


@asset("tent_old", "props")
def tent_old(k):
    r = k.r
    L, W, H = 2.6, 2.2, 1.7
    for sy in (-1, 1):
        t = box(L, 0.03, math.hypot(W / 2, H), bev=0.0)
        subdiv(t, 5)
        for v in t.verts:
            # sag + tattered hem
            v.co.y -= 0.06 * math.sin((v.co.x / L + 0.5) * math.pi) * (0.5 - v.co.z / math.hypot(W / 2, H))
        ndisp(t, 3.0, 0.03, k.noff)
        ang = math.degrees(math.atan2(W / 2, H))
        k.put(t, "BH_Cloth", M=TRS(0, sy * W / 4, H / 2, sy * ang, 0, 0), tint=r.uniform(0.6, 0.8), smooth=40)
        # torn flap
    for sx in (-1, 1):
        k.put(cyl(0.035, H + 0.1, 6), "BH_Wood", M=T(sx * (L / 2 + 0.02), 0, 0), tint=0.6)
        for sy in (-1, 1):
            t = tube([(sx * (L / 2 + 0.02), 0, H), (sx * (L / 2 + 0.7), sy * 0.6, 0.02)], 0.008, 4)
            k.put(t, "BH_Cloth", tint=0.5)
            k.put(cyl(0.02, 0.2, 4, r2=0.005), "BH_Wood", M=T(sx * (L / 2 + 0.7), sy * 0.6, -0.08), tint=0.5)
    k.put(cyl(0.03, L + 0.1, 6), "BH_Wood", M=TRS(-(L + 0.1) / 2, 0, H, 0, 90, 0), tint=0.6)
    k.col_box(L, W, H, T(0, 0, H / 2))
    return dict(recenter=True)


@asset("weapon_rack", "props")
def weapon_rack(k):
    r = k.r
    W, H = 1.6, 1.5
    for sx in (-1, 1):
        k.put(box(0.1, 0.1, H, bev=0.01), "BH_WoodDark", M=T(sx * W / 2, 0, H / 2), tint=0.8)
        k.put(box(0.1, 0.5, 0.08, bev=0.01), "BH_WoodDark", M=T(sx * W / 2, 0, 0.04), tint=0.7)
    for z in (0.35, 1.2):
        plank(k, W, 0.08, 0.06, T(0, 0, z), mat="BH_Wood")
    for i in range(5):
        x = -W / 2 + 0.25 + i * 0.28
        if i % 2 == 0:
            sword(k, TRS(x, -0.06, 0.12, r.uniform(-4, 4), 0, 0), 1.1)
        else:
            k.put(cyl(0.02, 1.9, 6), "BH_Wood", M=TRS(x, -0.06, 0.05, r.uniform(-3, 3), r.uniform(-3, 3), 0), tint=0.7)
            k.put(cyl(0.035, 0.25, 4, r2=0.0), "BH_Metal", M=T(x, -0.06, 1.95), tint=0.7)
    k.col_box(W + 0.1, 0.5, H, T(0, 0, H / 2))
    return dict(recenter=True)


@asset("weapons_discarded", "props")
def weapons_discarded(k):
    r = k.r
    sword(k, TRS(0.0, 0.0, 0.02, 90, 0, 30), 1.0)
    sword(k, TRS(0.6, 0.5, 0.02, 90, 0, 150), 1.0, broken=True)
    shield_round(k, TRS(-0.5, 0.4, 0.05, 12, 8, 0))
    helmet(k, TRS(0.7, -0.4, 0.0, 70, 0, 40))
    k.put(cyl(0.02, 1.8, 6), "BH_Wood", M=TRS(-0.9, -0.5, 0.03, 90, 0, 75), tint=0.6)
    k.put(cyl(0.035, 0.25, 4, r2=0.0), "BH_Metal", M=TRS(-0.9, -0.5, 0.03, 90, 0, 75) @ T(0, 0, 1.8), tint=0.6)
    return dict(recenter=True)


@asset("skull_pile", "props")
def skull_pile(k):
    r = k.r
    k.put(cyl(0.6, 0.15, 12, r2=0.3), "BH_Dirt", tint=0.4)
    pos = []
    for layer, (n, rad, z) in enumerate(((8, 0.45, 0.12), (6, 0.28, 0.3), (3, 0.12, 0.46), (1, 0.0, 0.6))):
        for i in range(n):
            a = math.tau * i / max(n, 1) + layer
            pos.append((math.cos(a) * rad, math.sin(a) * rad, z))
    for p in pos:
        skull(k, TRS(p[0], p[1], p[2], r.uniform(-20, 20), r.uniform(-20, 20), r.uniform(0, 360)), r.uniform(0.9, 1.1))
    for i in range(10):
        a = r.uniform(0, math.tau)
        bone(k, TRS(math.cos(a) * 0.6, math.sin(a) * 0.6, 0.03, 0, r.uniform(-10, 10), r.uniform(0, 360)), r.uniform(0.25, 0.45))
    return dict(recenter=True)


@asset("bones_scatter", "props")
def bones_scatter(k):
    r = k.r
    for i in range(14):
        bone(k, TRS(r.uniform(-0.9, 0.9), r.uniform(-0.9, 0.9), 0.02, 0, 0, r.uniform(0, 360)), r.uniform(0.2, 0.5),
             r.uniform(0.015, 0.025))
    skull(k, TRS(0.3, -0.2, 0.08, 0, -30, 40))
    skull(k, TRS(-0.5, 0.4, 0.07, 10, 80, 160), 0.9)
    # ribcage
    for i in range(6):
        for sx in (-1, 1):
            t = tube([(0, 0, 0), (sx * 0.12, 0, 0.08), (sx * 0.18, 0, 0.0)], 0.012, 4)
            k.put(t, "BH_Bone", M=TRS(-0.2 + i * 0.06, 0.5, 0.0, 0, 0, 90), tint=0.8)
    bone(k, TRS(-0.25, 0.5, 0.02, 0, 0, 0), 0.4, 0.018)
    return dict(recenter=True)


@asset("candles_cluster", "props")
def candles_cluster(k):
    r = k.r
    k.put(cyl(0.3, 0.02, 16), "BH_Candle", tint=0.8)
    for i in range(9):
        a = r.uniform(0, math.tau)
        d = r.uniform(0.0, 0.24)
        h = r.uniform(0.08, 0.35)
        rr = r.uniform(0.025, 0.045)
        x, y = math.cos(a) * d, math.sin(a) * d
        c = cyl(rr, h, 10)
        for v in c.verts:
            if v.co.z > h - 0.01:
                v.co.z -= r.uniform(0, 0.02)
        k.put(c, "BH_Candle", M=T(x, y, 0.02), tint=r.uniform(0.85, 1.0), smooth=40)
        for j in range(2):  # drips
            aa = r.uniform(0, math.tau)
            k.put(cyl(0.008, h * r.uniform(0.3, 0.7), 4), "BH_Candle", M=T(x + math.cos(aa) * rr, y + math.sin(aa) * rr, 0.02))
        flame_tip(k, T(x, y, h + 0.03), 0.05)
    k.sockets.append(("light", (0, 0, 0.4)))
    return dict(recenter=False)


@asset("cobweb", "props", col=False)
def cobweb(k):
    """Web spanning a wall corner at ceiling height; local corner at origin, walls along +X and +Y, hangs down."""
    r = k.r
    R_ = 1.1
    spokes = 7
    pts = []
    for i in range(spokes):
        a = math.radians(90 * i / (spokes - 1))
        pts.append(Vector((math.cos(a), math.sin(a), 0)))
    for i, p in enumerate(pts):
        end = Vector((p.x * R_, p.y * R_, -R_ * 0.55 * math.sin(math.pi * i / (spokes - 1)) - 0.05))
        k.put(tube([(0, 0, 0), end], 0.005, 3), "BH_Bone", tint=0.9, uvoff=False)
    for ring in range(1, 7):
        s = ring / 7.0
        path = []
        for i in range(spokes):
            p = pts[i]
            sag = -R_ * 0.55 * math.sin(math.pi * i / (spokes - 1)) * s - 0.05 * s - r.uniform(0, 0.04)
            path.append((p.x * R_ * s, p.y * R_ * s, sag))
        k.put(tube(path, 0.004, 3), "BH_Bone", tint=0.85, uvoff=False)
    return dict(recenter=False)


@asset("banner_torn", "props", col=False)
def banner_torn(k):
    r = k.r
    W, H = 1.2, 2.6
    k.put(cyl(0.03, W + 0.3, 8), "BH_WoodDark", M=TRS(-(W + 0.3) / 2, 0, 0, 0, 90, 0), tint=0.8)
    for sx in (-1, 1):
        k.put(ico(0.045, 1), "BH_Gold", M=T(sx * (W / 2 + 0.15), 0, 0))
    t = tb()
    nx, nz = 8, 12
    vs = []
    for j in range(nz + 1):
        row = []
        for i in range(nx + 1):
            x = -W / 2 + W * i / nx
            z = -H * j / nz
            if j == nz:  # ragged hem
                z += r.uniform(0.0, 0.5) if i % 2 else r.uniform(0.2, 0.6)
            y = 0.04 * math.sin(i * 1.3 + j * 0.7) + 0.02 * j / nz
            row.append(t.verts.new((x, y, z)))
        vs.append(row)
    for j in range(nz):
        for i in range(nx):
            if j > nz - 4 and r.random() < 0.12:
                continue  # holes
            t.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    bmesh.ops.solidify(t, geom=list(t.faces), thickness=0.012)
    k.put(t, "BH_ClothRed", M=T(0, 0, -0.04), tint=0.75, smooth=40, uvoff=False)
    # emblem: gold chevron + sun disc
    k.put(cyl(0.18, 0.02, 16), "BH_Gold", M=TRS(0, -0.03, -0.8, 90, 0, 0), tint=0.8)
    for sx in (-1, 1):
        k.put(box(0.5, 0.02, 0.07), "BH_Gold", M=TRS(sx * 0.16, -0.03, -1.3, 0, sx * 35, 0), tint=0.8)
    return dict(recenter=False)


@asset("torch_sconce", "props", col=False)
def torch_sconce(k):
    """Wall mounted; back plate at y=0 on the wall, torch leans out toward -Y. Socket `flame` at the torch head."""
    k.put(box(0.16, 0.03, 0.3, bev=0.008), "BH_Iron", M=T(0, -0.015, 0))
    for z in (-0.1, 0.1):
        rivet(k, TRS(0, -0.032, z, 90, 0, 0), 0.02)
    k.put(tube([(0, -0.03, -0.08), (0, -0.2, -0.02), (0, -0.24, 0.08)], 0.018, 6), "BH_Iron", smooth=40)
    k.put(torus(0.06, 0.014, 12, 4), "BH_Iron", M=T(0, -0.24, 0.08))
    lean = R(22, 0, 0)
    k.put(cyl(0.035, 0.5, 8, r2=0.045), "BH_WoodDark", M=T(0, -0.25, -0.15) @ lean, tint=0.8)
    k.put(cyl(0.06, 0.14, 8, r2=0.05), "BH_Cloth", M=T(0, -0.25, -0.15) @ lean @ T(0, 0, 0.42), tint=0.3)
    k.sockets.append(("flame", tuple(T(0, -0.25, -0.15) @ lean @ Vector((0, 0, 0.62)))))
    return dict(recenter=False)


@asset("brazier", "props")
def brazier(k):
    r = k.r
    bowl = lathe([(0.12, 0.0), (0.3, 0.1), (0.42, 0.28), (0.44, 0.34), (0.4, 0.34), (0.38, 0.28), (0.26, 0.12), (0.0, 0.06)], 16,
                 cap_bot=True, cap_top=False)
    k.put(bowl, "BH_Iron", M=T(0, 0, 0.75), smooth=40)
    for i in range(3):
        a = math.tau * i / 3
        k.put(tube([(math.cos(a) * 0.15, math.sin(a) * 0.15, 0.85), (math.cos(a) * 0.38, math.sin(a) * 0.38, 0.35),
                    (math.cos(a) * 0.42, math.sin(a) * 0.42, 0.0)], 0.025, 6), "BH_Iron", smooth=40)
        k.put(cyl(0.05, 0.03, 8), "BH_Iron", M=T(math.cos(a) * 0.42, math.sin(a) * 0.42, 0.0))
    k.put(torus(0.43, 0.018, 20, 4), "BH_Iron", M=T(0, 0, 1.09))
    for i in range(12):
        a = r.uniform(0, math.tau)
        d = r.uniform(0, 0.25)
        mat = "BH_Flame" if r.random() < 0.5 else "BH_Dirt"
        k.put(rock(r, (0.08, 0.07, 0.06), cuts=4, subd=1, seed_off=i), mat,
              M=T(math.cos(a) * d, math.sin(a) * d, 0.95 + r.uniform(0, 0.05)), tint=0.35 if mat == "BH_Flame" else 0.2)
    k.sockets.append(("flame", (0, 0, 1.2)))
    k.col_mesh(cyl(0.44, 1.1, 8))
    return dict(recenter=False)


@asset("lamp_post", "props")
def lamp_post(k):
    H = 3.2
    k.put(cyl(0.16, 0.25, 8, bev=0.02), "BH_Stone", tint=0.8)
    k.put(cyl(0.05, H, 8, r2=0.04), "BH_Iron", M=T(0, 0, 0.2), smooth=40)
    k.put(tube([(0, 0, H - 0.3), (0.25, 0, H), (0.55, 0, H - 0.05)], 0.025, 6), "BH_Iron", smooth=40)
    x = 0.55
    k.put(cyl(0.012, 0.15, 4), "BH_Iron", M=T(x, 0, H - 0.2))
    k.put(cyl(0.14, 0.05, 6, r2=0.05), "BH_Iron", M=T(x, 0, H - 0.25))
    k.put(cyl(0.11, 0.35, 6, r2=0.13), "BH_Glass", M=T(x, 0, H - 0.6))
    for i in range(6):
        a = math.tau * i / 6 + math.pi / 6
        k.put(box(0.015, 0.015, 0.36), "BH_Iron", M=T(x + math.cos(a) * 0.12, math.sin(a) * 0.12, H - 0.42))
    k.put(cyl(0.13, 0.03, 6), "BH_Iron", M=T(x, 0, H - 0.63))
    k.put(cyl(0.025, 0.1, 8), "BH_Candle", M=T(x, 0, H - 0.6))
    flame_tip(k, T(x, 0, H - 0.5), 0.07)
    k.sockets.append(("light", (x, 0, H - 0.45)))
    k.col_box(0.3, 0.3, H, T(0, 0, H / 2))
    return dict(recenter=False)


@asset("anvil", "props")
def anvil(k):
    r = k.r
    t = tube([(0, 0, 0), (0, 0, 0.55)], [0.3, 0.26], 10)
    k.put(t, "BH_Bark", tint=0.6)
    k.put(cyl(0.27, 0.02, 10), "BH_Wood", M=T(0, 0, 0.55), tint=0.8)
    outline = [(-0.35, 0.0), (0.25, 0.0), (0.25, 0.1), (0.2, 0.12), (0.22, 0.2), (0.3, 0.26), (0.3, 0.3), (-0.28, 0.3),
               (-0.55, 0.28), (-0.55, 0.26), (-0.3, 0.2), (-0.26, 0.12), (-0.35, 0.1)]
    k.put(prism(outline, 0.16, bev=0.01), "BH_Iron", M=T(0.05, 0, 0.57), tint=0.9)
    k.put(box(0.3, 0.05, 0.05), "BH_WoodDark", M=TRS(0.1, 0.2, 0.9, 0, 0, 20))
    k.put(box(0.1, 0.07, 0.07, bev=0.01), "BH_Iron", M=TRS(0.26, 0.26, 0.9, 0, 0, 20))
    k.col_box(0.9, 0.6, 0.9, T(0, 0, 0.45))
    return dict(recenter=True)


@asset("cart_hay", "props")
def cart_hay(k):
    r = k.r
    L, W = 2.2, 1.3
    for i in range(6):
        plank(k, L, W / 6 - 0.01, 0.05, T(0, -W / 2 + W / 6 * (i + 0.5), 0.6))
    for sy in (-1, 1):
        for z in (0.72, 0.9):
            plank(k, L, 0.04, 0.12, T(0, sy * W / 2, z), mat="BH_WoodDark")
        for x in (-L / 2 + 0.1, 0, L / 2 - 0.1):
            k.put(box(0.06, 0.06, 0.45), "BH_WoodDark", M=T(x, sy * W / 2, 0.8))
        wheel(k, T(0.1, sy * (W / 2 + 0.12), 0.5), 0.5)
    k.put(cyl(0.04, W + 0.3, 8), "BH_WoodDark", M=TRS(0.1, (W + 0.3) / 2, 0.5, 90, 0, 0))
    for sy in (-0.4, 0.4):
        plank(k, 1.6, 0.07, 0.07, TRS(L / 2 + 0.7, sy, 0.45, 0, 12, 0), mat="BH_WoodDark")
    hay(k, T(0, 0, 0.62), (L * 0.95, W * 0.9, 0.7))
    k.col_box(L + 1.4, W + 0.4, 1.2, T(0.5, 0, 0.6))
    return dict(recenter=True)


@asset("wagon_broken", "props")
def wagon_broken(k):
    r = k.r
    L, W = 3.2, 1.6
    tilt = TRS(0, 0, 0.35, 0, 0, 0) @ R(-9, 6, 0)
    for i in range(7):
        if i == 5:
            continue  # missing plank
        plank(k, L, W / 7 - 0.01, 0.05, tilt @ T(0, -W / 2 + W / 7 * (i + 0.5), 0.4), warp=0.01)
    for sy in (-1, 1):
        plank(k, L, 0.06, 0.1, tilt @ T(0, sy * W * 0.35, 0.33), mat="BH_WoodDark")
        for z in (0.55, 0.78):
            if sy > 0 and z > 0.7:
                plank(k, L * 0.55, 0.04, 0.14, tilt @ TRS(-L * 0.22, sy * W / 2, z, 0, 0, 0), mat="BH_Wood")
                continue
            plank(k, L, 0.04, 0.14, tilt @ T(0, sy * W / 2, z), mat="BH_Wood")
        for x in (-L / 2 + 0.1, -0.5, 0.5, L / 2 - 0.1):
            k.put(box(0.07, 0.07, 0.5), "BH_WoodDark", M=tilt @ T(x, sy * W / 2, 0.65))
    wheel(k, T(-0.9, -W / 2 - 0.15, 0.55) @ R(0, 0, 0), 0.58)
    wheel(k, T(0.9, -W / 2 - 0.15, 0.55), 0.58)
    wheel(k, T(-0.9, W / 2 + 0.12, 0.45) @ R(0, -10, 0), 0.58, broken=3)
    wheel(k, T(1.3, W / 2 + 1.2, 0.08) @ R(90, 0, 25), 0.58, broken=1)  # fallen wheel
    k.put(cyl(0.05, W + 0.4, 8), "BH_WoodDark", M=TRS(-0.9, (W + 0.4) / 2 - 0.2, 0.5, 90, 0, 0))
    plank(k, 2.2, 0.08, 0.08, TRS(-L / 2 - 0.9, 0.2, 0.25, 0, 14, 8), mat="BH_WoodDark")
    plank(k, 1.2, 0.08, 0.08, TRS(-L / 2 - 0.5, -0.5, 0.12, 0, 4, -25), mat="BH_WoodDark")  # snapped shaft
    # spilled cargo
    for i in range(3):
        k.put(box(0.5, 0.4, 0.4, bev=0.03), "BH_Wood", M=TRS(0.9 + i * 0.35, -W / 2 - 0.9 - r.uniform(0, 0.4), 0.2,
                                                               0, 0, r.uniform(0, 60)), tint=r.uniform(0.6, 0.8))
    t = box(1.4, 0.9, 0.03, bev=0.01)
    subdiv(t, 3)
    ndisp(t, 3.0, 0.08, k.noff)
    k.put(t, "BH_Cloth", M=tilt @ TRS(0.4, 0.1, 0.9, 0, 0, 10), tint=0.6, smooth=40)
    k.col_box(L, W + 0.3, 1.1, T(0, 0, 0.55))
    return dict(recenter=True)


@asset("chains_hanging", "props", col=False)
def chains_hanging(k):
    """Two chains hanging from a ceiling bracket at z=3.2 down to ~1.2 m, hooks at the ends."""
    for cx, n in ((-0.2, 24), (0.25, 18)):
        for i in range(n):
            z = 3.2 - 0.075 * i
            rot = R(0, 0, 90) if i % 2 else R(0, 0, 0)
            k.put(torus(0.035, 0.009, 8, 4), "BH_Iron", M=T(cx, 0, z) @ rot @ R(90, 0, 0) @ S(1, 1.6, 1))
        zb = 3.2 - 0.075 * n
        k.put(tube([(cx, 0, zb), (cx, 0, zb - 0.12), (cx + 0.08, 0, zb - 0.16), (cx + 0.1, 0, zb - 0.08)], 0.014, 6),
              "BH_Iron", smooth=40)
    k.put(box(0.8, 0.12, 0.08, bev=0.01), "BH_Iron", M=T(0, 0, 3.26))
    return dict(recenter=False)


@asset("spikes_trap_plate", "props")
def spikes_trap_plate(k):
    r = k.r
    k.put(box(2.0, 2.0, 0.06, bev=0.01), "BH_Iron", M=T(0, 0, 0.03), tint=0.8)
    for i in range(5):
        for j in range(5):
            x, y = -0.8 + i * 0.4, -0.8 + j * 0.4
            k.put(cyl(0.05, 0.02, 8), "BH_StoneDark", M=T(x, y, 0.055), tint=0.1)
            h = r.uniform(0.25, 0.45)
            k.put(cyl(0.035, h, 6, r2=0.0), "BH_Metal", M=T(x, y, 0.05), tint=r.uniform(0.4, 0.7))
    for sx in (-1, 1):
        for sy in (-1, 1):
            rivet(k, T(sx * 0.92, sy * 0.92, 0.06), 0.03)
    return dict(recenter=False)


# ---------------------------------------------------------------------------------------------------------------
# reference-derived pieces (cistern / scaffolding)
@asset("ladder", "props")
def ladder(k):
    r = k.r
    H, W = 3.0, 0.5
    for sx in (-1, 1):
        k.put(box(0.06, 0.08, H, bev=0.01), "BH_Wood", M=TRS(sx * W / 2, 0, H / 2), tint=r.uniform(0.6, 0.8))
    for i in range(9):
        z = 0.3 + i * 0.3
        k.put(cyl(0.022, W + 0.06, 6), "BH_WoodDark", M=TRS(-(W + 0.06) / 2, 0, z, 0, 90, 0), tint=0.8)
        for sx in (-1, 1):
            k.put(box(0.07, 0.09, 0.03), "BH_Cloth", M=T(sx * W / 2, 0, z), tint=0.4)
    k.col_box(W + 0.1, 0.1, H, T(0, 0, H / 2))
    return dict(recenter=False)


@asset("scaffold_platform", "props")
def scaffold_platform(k):
    r = k.r
    S, H = 2.0, 3.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(box(0.12, 0.12, H + (1.0 if sy > 0 else 0.0), bev=0.015), "BH_WoodDark",
                  M=T(sx * (S / 2 - 0.06), sy * (S / 2 - 0.06), (H + (1.0 if sy > 0 else 0.0)) / 2), tint=r.uniform(0.6, 0.8))
    for i in range(8):
        if i == 6 and r.random() < 1.0:
            plank(k, S + 0.1, S / 8 - 0.01, 0.05, TRS(0, -S / 2 + S / 8 * (i + 0.5), H - 0.04, 0, 3, 0), warp=0.01)
            continue
        plank(k, S + 0.1, S / 8 - 0.01, 0.05, T(0, -S / 2 + S / 8 * (i + 0.5), H), warp=0.006)
    for sx in (-1, 1):
        plank(k, S, 0.1, 0.1, TRS(sx * (S / 2 - 0.06), 0, H - 0.1, 0, 0, 90), mat="BH_WoodDark")
        d = math.hypot(S - 0.2, H - 0.6)
        plank(k, d, 0.08, 0.05, TRS(sx * (S / 2 - 0.06) - sx * 0.07, 0, H / 2 - 0.1, 0,
                                     math.degrees(math.atan2(H - 0.6, S - 0.2)), 90), mat="BH_WoodDark")
    plank(k, S, 0.08, 0.08, T(0, S / 2 - 0.06, H + 0.9), mat="BH_Wood")  # rail
    plank(k, S, 0.06, 0.06, T(0, S / 2 - 0.06, H + 0.45), mat="BH_Wood")
    for sy in (-1, 1):
        plank(k, S, 0.1, 0.1, T(0, sy * (S / 2 - 0.06), H - 0.1), mat="BH_WoodDark")
    # rope lashings
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.put(cyl(0.085, 0.12, 8), "BH_Cloth", M=T(sx * (S / 2 - 0.06), sy * (S / 2 - 0.06), H - 0.2), tint=0.45)
    k.col_box(S + 0.1, S, 0.12, T(0, 0, H + 0.01))
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.col_box(0.12, 0.12, H, T(sx * (S / 2 - 0.06), sy * (S / 2 - 0.06), H / 2))
    k.col_box(S, 0.12, 1.0, T(0, S / 2 - 0.06, H + 0.5))
    return dict(recenter=False)


@asset("dock_planks", "props")
def dock_planks(k):
    """4 m jetty section, deck top at z=0, posts reach down to z=-1.6 (into water)."""
    r = k.r
    L, W = 4.0, 2.0
    n = 16
    for i in range(n):
        if i == 11:
            continue
        plank(k, W, L / n - 0.02, 0.06, TRS(0, -L / 2 + L / n * (i + 0.5), -0.03, 0, 0, k.r.uniform(-1.5, 1.5)))
    for sx in (-1, 1):
        plank(k, L, 0.12, 0.16, T(sx * (W / 2 - 0.1), 0, -0.14), mat="BH_WoodDark", tint=(0.5, 0.7))
        for y in (-L / 2 + 0.2, L / 2 - 0.2):
            t = tube([(0, 0, -1.6), (0, 0, 0.35)], [0.11, 0.1], 8)
            k.put(t, "BH_WoodDark", M=T(sx * (W / 2 + 0.05), y, 0), tint=0.6, smooth=40)
            k.put(torus(0.115, 0.02, 10, 4), "BH_Cloth", M=T(sx * (W / 2 + 0.05), y, 0.15), tint=0.4)
    k.put(box(0.3, 0.3, 0.3, bev=0.02), "BH_Wood", M=TRS(0.4, 1.2, 0.15, 0, 0, 20), tint=0.7)
    k.col_box(W, L, 0.2, T(0, 0, -0.1))
    return dict(recenter=False)


@asset("boat_rowing", "props")
def boat_rowing(k):
    r = k.r
    L = 3.4
    nsec = 13
    prof_n = 7

    def section(u):
        x = -L / 2 + L * u
        w = 0.72 * math.sqrt(max(0.0, 1 - (2 * u - 1) ** 4)) + 0.04
        d = 0.42 - 0.1 * (1 - math.sin(math.pi * u))
        sheer = 0.55 + 0.15 * (2 * u - 1) ** 2
        pts = []
        for j in range(prof_n):
            a = math.pi * j / (prof_n - 1)
            pts.append((x, -math.cos(a) * w, sheer - math.sin(a) * d))
        return pts
    t = tb()
    outer, inner = [], []
    for s in range(nsec):
        sec = section(s / (nsec - 1))
        outer.append([t.verts.new(p) for p in sec])
        inner.append([t.verts.new((p[0], p[1] * 0.88, p[2] + (0.05 if 0 < j < prof_n - 1 else 0.0) + 0.0))
                      for j, p in enumerate(sec)])
    for s in range(nsec - 1):
        for j in range(prof_n - 1):
            t.faces.new((outer[s][j], outer[s + 1][j], outer[s + 1][j + 1], outer[s][j + 1]))
            t.faces.new((inner[s][j + 1], inner[s + 1][j + 1], inner[s + 1][j], inner[s][j]))
        for j in (0, prof_n - 1):
            t.faces.new((outer[s][j], inner[s][j], inner[s + 1][j], outer[s + 1][j]))
    for s in (0, nsec - 1):
        ring = outer[s] + inner[s][::-1]
        t.faces.new(ring if s else ring[::-1])
    bmesh.ops.recalc_face_normals(t, faces=t.faces)
    k.put(t, "BH_Wood", tint=0.65, smooth=35, uvoff=False)
    for u in (0.3, 0.55, 0.78):  # thwarts
        x = -L / 2 + L * u
        w = 0.72 * math.sqrt(max(0.0, 1 - (2 * u - 1) ** 4))
        plank(k, 0.25, w * 1.7, 0.04, T(x, 0, 0.42), mat="BH_WoodDark")
    for sy in (-1, 1):  # gunwale strakes
        k.put(box(L * 0.8, 0.04, 0.05), "BH_WoodDark", M=T(0, sy * 0.72, 0.53), tint=0.7)
    k.put(cyl(0.02, 2.4, 6), "BH_Wood", M=TRS(-0.3, 0.2, 0.46, 0, 88, 12) @ T(0, 0, -1.2), tint=0.7)
    k.put(box(0.14, 0.02, 0.5), "BH_Wood", M=TRS(-0.3, 0.2, 0.46, 0, 88, 12) @ T(0, 0, -1.2), tint=0.7)
    k.put(torus(0.12, 0.02, 12, 4), "BH_Cloth", M=T(L / 2 - 0.35, 0, 0.3), tint=0.4)
    k.col_box(L, 1.5, 0.6, T(0, 0, 0.3))
    return dict(recenter=True)


@asset("winch", "props")
def winch(k):
    """Timber winch over a shaft: two A-frames 2.6 m tall, drum with rope, crank, rope + bucket hanging at x=0."""
    r = k.r
    H, W = 2.6, 1.8
    for sy in (-1, 1):
        for sx in (-1, 1):
            plank(k, H * 1.05, 0.14, 0.14, TRS(sx * 0.35, sy * W / 2, H / 2, 0, -sx * 14, 0) @ R(0, 90, 0), mat="BH_WoodDark")
        plank(k, 1.1, 0.12, 0.12, T(0, sy * W / 2, 0.4), mat="BH_WoodDark")
        k.put(box(0.3, 0.2, 0.2, bev=0.02), "BH_WoodDark", M=T(0, sy * W / 2, H - 0.05))
    k.put(cyl(0.2, W - 0.3, 12), "BH_Wood", M=TRS(0, -(W - 0.3) / 2, H - 0.05, -90, 0, 0), tint=0.7, smooth=40)
    for i in range(10):
        k.put(torus(0.215, 0.018, 16, 4), "BH_Cloth", M=TRS(0, -0.3 + i * 0.045, H - 0.05, 90, 0, 0), tint=0.5)
    k.put(cyl(0.035, W + 0.4, 8), "BH_Iron", M=TRS(0, -(W + 0.4) / 2, H - 0.05, -90, 0, 0))
    k.put(box(0.05, 0.05, 0.5), "BH_Iron", M=T(0, W / 2 + 0.2, H - 0.3))
    k.put(cyl(0.03, 0.3, 6), "BH_WoodDark", M=TRS(0, W / 2 + 0.2, H - 0.55, -90, 0, 0))
    k.put(cyl(0.015, 1.6, 4), "BH_Cloth", M=T(0, 0.2, H - 1.8), tint=0.5)
    b = lathe([(0.14, 0.0), (0.18, 0.35), (0.16, 0.35), (0.12, 0.03), (0.0, 0.03)], 12, cap_bot=True, cap_top=False)
    k.put(b, "BH_Wood", M=T(0, 0.2, H - 2.2), tint=0.6, smooth=40)
    k.put(torus(0.175, 0.012, 14, 4), "BH_Iron", M=T(0, 0.2, H - 1.95))
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.col_box(0.2, 0.2, H, T(sx * 0.35, sy * W / 2, H / 2))
    return dict(recenter=False)
