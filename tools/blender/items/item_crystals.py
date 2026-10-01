"""Socket crystals (bh-018): 8 families x 4 grades = 32 item models, plus their "epic" inventory icons.

Ids are `<family>_<grade>` (FAMILIES x GRADES below). Grade = form (fragment chip < double-terminated shard <
crystal cluster on a geode < faceted gem-sphere in a cradle with orbit rings and satellites); family = colour + a
glowing motif inlaid in the front (and back) facets: flame, droplet, star, forked bolt, serpent eye, blood rift,
mana rift, white-light rift on rainbow facets.

Models (Blender, via build_items.py; independent of items.json):
  blender -b --factory-startup --python build_items.py -- models crystals        # all 32 -> game/assets/items/<id>.glb
  blender -b --factory-startup --python build_items.py -- models ember_shard     # just one
Icon renders (Blender, Cycles):
  blender -b --factory-startup --python build_items.py -- icons crystals         # -> work/lemondev/bh-018/evidence/crystals/raw/
Icon compositing + contact sheets (system Python, PIL + numpy):
  python item_crystals.py post                                                     # -> game/assets/ui/icons/crystals/<id>.png

Materials use the item palette (`BH_<base>__it_<key>`, registered into item_kit.MAT on import) so the game keeps each
crystal's colours and soft glow. Every crystal stands on z = 0, front -Y; parts named `icon_*` are only used by the
icon renders, parts named `back_*` only by the game model.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVID = os.path.join(ROOT, "work", "lemondev", "bh-018", "evidence", "crystals")
RAW = os.path.join(EVID, "raw")
ICON_DIR = os.path.join(ROOT, "game", "assets", "ui", "icons", "crystals")
REPORT = os.path.join(EVID, "models_report.json")
MODEL_RAW = os.path.join(EVID, "model_raw")   # optional plain model renders for the model sheet

# bh-028: the four celestial orbs come last, so the older families keep their seeds (FSEED) and byte-identical models
FAMILIES = ["ember", "aqua", "nova", "thundra", "vipera", "bloodrift", "essencerift", "aetherift", "sora", "luna", "sol", "airah"]
GRADES = ["fragment", "shard", "crystalline", "orbital"]
IDS = [f"{f}_{g}" for f in FAMILIES for g in GRADES]
SIZE = {"fragment": 0.18, "shard": 0.24, "crystalline": 0.28, "orbital": 0.315}   # largest dimension (m)


def is_crystal(iid):
    return iid in IDS


def display_name(iid):
    f, g = iid.split("_")
    return f"{f.capitalize()} {g.capitalize()}"


def items(ids=None):
    """Item dicts for build_items.py (the crystals are not in items.json)."""
    out = []
    for iid in IDS:
        if ids and iid not in ids:
            continue
        f, g = iid.split("_")
        out.append({"id": iid, "category": "crystal", "family": f, "grade": g, "weapon_type": "", "element": 0,
                    "name": display_name(iid)})
    return out


# ---- palette --------------------------------------------------------------------------------------------------------
# family: body (clear gem), dull (frosted outer skin of a raw chip), edge (bevels / terminations), glow (motif),
#         hot (motif core), dark (pupils, voids), metal (orbital cradle + ring), halo (icon backdrop, sRGB 0..255)
FAM = {
    "ember": dict(body=(0.5, 0.02, 0.004), body_em=(1.0, 0.07, 0.005), dull=(0.16, 0.012, 0.003), edge=(0.95, 0.22, 0.01),
                  glow=(1.0, 0.36, 0.02), hot=(1.0, 0.86, 0.42), dark=(0.06, 0.004, 0.0), metal="gold",
                  halo=(255, 70, 16), halo2=(255, 170, 60)),
    "aqua": dict(body=(0.01, 0.1, 0.55), body_em=(0.02, 0.25, 1.0), dull=(0.005, 0.035, 0.16), edge=(0.05, 0.45, 0.9),
                 glow=(0.2, 0.8, 1.0), hot=(0.85, 1.0, 1.0), dark=(0.0, 0.015, 0.06), metal="silver",
                 halo=(20, 110, 255), halo2=(110, 230, 255)),
    "nova": dict(body=(0.95, 0.7, 0.28), body_em=(1.0, 0.72, 0.28), dull=(0.4, 0.3, 0.12), edge=(1.0, 0.9, 0.62),
                 glow=(1.0, 0.95, 0.72), hot=(1.0, 1.0, 1.0), dark=(0.16, 0.08, 0.01), metal="paleg",
                 halo=(255, 200, 90), halo2=(255, 250, 225)),
    "thundra": dict(body=(1.0, 0.68, 0.015), body_em=(1.0, 0.62, 0.02), dull=(0.45, 0.28, 0.01), edge=(0.34, 0.06, 0.9),
                    glow=(0.55, 0.22, 1.0), hot=(1.0, 1.0, 0.85), dark=(0.06, 0.0, 0.12), metal="blackiron",
                    halo=(255, 200, 20), halo2=(160, 80, 255)),
    "vipera": dict(body=(0.04, 0.4, 0.03), body_em=(0.1, 0.72, 0.03), dull=(0.01, 0.06, 0.01), edge=(0.004, 0.035, 0.008),
                   glow=(0.6, 1.0, 0.1), hot=(0.95, 1.0, 0.4), dark=(0.002, 0.006, 0.002), metal="blackiron",
                   halo=(80, 220, 30), halo2=(200, 255, 90)),
    "bloodrift": dict(body=(0.06, 0.001, 0.005), body_em=(0.22, 0.0, 0.008), dull=(0.03, 0.002, 0.004),
                      edge=(0.015, 0.0, 0.003), glow=(1.0, 0.04, 0.02), hot=(1.0, 0.5, 0.3), dark=(0.01, 0.0, 0.0),
                      metal="darksteel", halo=(190, 0, 24), halo2=(255, 60, 40)),
    "essencerift": dict(body=(0.14, 0.08, 0.7), body_em=(0.3, 0.16, 1.0), dull=(0.05, 0.025, 0.22), edge=(0.5, 0.2, 1.0),
                        glow=(0.3, 0.42, 1.0), hot=(0.8, 0.92, 1.0), dark=(0.03, 0.0, 0.1), metal="moonsteel",
                        halo=(100, 60, 255), halo2=(130, 190, 255)),
    "aetherift": dict(body=(0.05, 0.75, 1.0), body_em=(0.1, 0.8, 1.0), dull=(0.2, 0.35, 0.5), edge=(1.0, 0.95, 0.85),
                      glow=(0.95, 0.97, 1.0), hot=(1.0, 1.0, 1.0), dark=(0.12, 0.03, 0.25), metal="paleg",
                      halo=(170, 110, 255), halo2=(110, 255, 235)),
    # bh-028 celestial orbs: sky, moon, sun, wind
    "sora": dict(body=(0.25, 0.55, 0.95), body_em=(0.4, 0.7, 1.0), dull=(0.08, 0.18, 0.35), edge=(0.85, 0.93, 1.0),
                 glow=(0.75, 0.9, 1.0), hot=(1.0, 1.0, 1.0), dark=(0.02, 0.05, 0.12), metal="silver",
                 halo=(120, 180, 255), halo2=(220, 240, 255)),
    "luna": dict(body=(0.42, 0.4, 0.6), body_em=(0.55, 0.52, 0.85), dull=(0.12, 0.11, 0.2), edge=(0.88, 0.88, 1.0),
                 glow=(0.85, 0.86, 1.0), hot=(1.0, 1.0, 1.0), dark=(0.02, 0.02, 0.06), metal="moonsteel",
                 halo=(150, 140, 230), halo2=(225, 225, 255)),
    "sol": dict(body=(0.95, 0.42, 0.04), body_em=(1.0, 0.55, 0.08), dull=(0.35, 0.14, 0.01), edge=(1.0, 0.85, 0.4),
                glow=(1.0, 0.82, 0.3), hot=(1.0, 0.98, 0.85), dark=(0.12, 0.04, 0.0), metal="gold",
                halo=(255, 150, 30), halo2=(255, 230, 140)),
    "airah": dict(body=(0.3, 0.85, 0.7), body_em=(0.4, 1.0, 0.8), dull=(0.08, 0.25, 0.2), edge=(0.85, 1.0, 0.95),
                  glow=(0.8, 1.0, 0.92), hot=(1.0, 1.0, 1.0), dark=(0.01, 0.06, 0.05), metal="paleg",
                  halo=(90, 230, 190), halo2=(210, 255, 240)),
}
OUTLINED = ("nova", "essencerift", "aetherift", "sora", "luna", "airah")    # a dark rim under the motif where the body is pale / same hue
# the prismatic facets of the Aetherift (cyan / magenta / gold / pale)
PRISM = {"body": (0.05, 0.75, 1.0), "mag": (1.0, 0.1, 0.72), "gold": (1.0, 0.66, 0.05), "pale": (0.42, 0.2, 1.0)}


def _register_palette():
    import item_kit as K
    for f, d in FAM.items():
        K.MAT[f"cr_{f}_body"] = ("BH_Gem", d["body"], 0.0, 0.06, d["body_em"], 0.75)
        K.MAT[f"cr_{f}_dull"] = ("BH_Gem", d["dull"], 0.0, 0.42, d["body_em"], 0.22)
        K.MAT[f"cr_{f}_edge"] = ("BH_Gem", d["edge"], 0.0, 0.1, d["edge"], 0.8 if f not in ("vipera", "bloodrift") else 0.0)
        K.MAT[f"cr_{f}_glow"] = ("BH_Emissive", d["glow"], 0.0, 0.3, d["glow"], 2.6)
        K.MAT[f"cr_{f}_hot"] = ("BH_Emissive", d["hot"], 0.0, 0.3, d["hot"], 3.4)
        K.MAT[f"cr_{f}_dark"] = ("BH_Gem", d["dark"], 0.0, 0.15, None, 0)
        K.MAT[f"cr_{f}_core"] = ("BH_Emissive", d["glow"], 0.0, 0.3, d["glow"], 0.6)   # icon-only inner heart
    K.MAT["cr_rock"] = ("BH_Stone", (0.03, 0.026, 0.028), 0.0, 0.8, None, 0)
    for k, c in PRISM.items():
        if k != "body":
            K.MAT[f"cr_aetherift_{k}"] = ("BH_Gem", c, 0.0, 0.06, c, 0.75)


_register_palette()

import item_kit as K  # noqa: E402
from item_kit import M, Rx, Ry, Rz  # noqa: E402


def mk(f, role):
    return f"cr_{f}_{role}"


# ---- mesh helpers ---------------------------------------------------------------------------------------------------

def _bm_from(V, F):
    import bmesh
    bm = bmesh.new()
    vs = [bm.verts.new(tuple(v)) for v in V]
    for f in F:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    return bm


def _bm_to(bm):
    V = np.array([v.co[:] for v in bm.verts])
    idx = {v: i for i, v in enumerate(bm.verts)}
    F = [tuple(idx[v] for v in f.verts) for f in bm.faces]
    return V, F


def hull(points, mat, name="hull", merge_deg=2.0):
    """Convex hull of a point cloud, coplanar triangles merged into facets."""
    import bmesh
    bm = bmesh.new()
    for p in points:
        bm.verts.new(tuple(p))
    res = bmesh.ops.convex_hull(bm, input=bm.verts[:], use_existing_faces=False)
    kill = list({g for g in res["geom_interior"] + res["geom_unused"] if isinstance(g, bmesh.types.BMVert)})
    if kill:
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(merge_deg), verts=bm.verts[:], edges=bm.edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.verts.index_update()
    V, F = _bm_to(bm)
    bm.free()
    return M.Part(V, F, mat, name=name)


def cut_hull(part, planes):
    """Clip a convex part by planes (point, normal: the normal side is removed) and re-hull the rest."""
    V = part.V.copy()
    pts = [tuple(v) for v in V]
    for co, no in planes:
        co, no = np.asarray(co, float), np.asarray(no, float) / np.linalg.norm(no)
        # add the plane/edge intersections, drop the outside points
        P = np.array(pts)
        tmp = hull(P, part.mat)
        new = []
        for f in tmp.F:
            for i in range(len(f)):
                a, b = tmp.V[f[i]], tmp.V[f[(i + 1) % len(f)]]
                da, db = np.dot(a - co, no), np.dot(b - co, no)
                if da * db < 0:
                    t = da / (da - db)
                    new.append(a + (b - a) * t)
        keep = [p for p in P if np.dot(p - co, no) <= 1e-9]
        pts = [tuple(p) for p in keep] + [tuple(p) for p in new]
    return hull(np.array(pts), part.mat, part.name)


def face_normals(V, F):
    out = []
    for f in F:
        P = V[list(f)]
        n = np.zeros(3)
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            n += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
        ln = np.linalg.norm(n)
        out.append(n / ln if ln > 1e-12 else np.array([0, 0, 1.0]))
    return np.array(out)


def offset_planes(part, d):
    """Copy of a closed faceted part with every facet plane pushed out by d (least squares per vertex)."""
    V, F = part.V, part.F
    N = face_normals(V, F)
    adj = [[] for _ in range(len(V))]
    for fi, f in enumerate(F):
        for i in f:
            adj[i].append(fi)
    out = V.copy()
    for vi in range(len(V)):
        ns = N[adj[vi]]
        if len(ns) == 0:
            continue
        # unique normals only
        u = [ns[0]]
        for n in ns[1:]:
            if all(np.dot(n, m) < 0.9995 for m in u):
                u.append(n)
        A = np.array(u)
        b = np.full(len(u), d)
        x, *_ = np.linalg.lstsq(A, b, rcond=None)
        ln = np.linalg.norm(x)
        if ln > 3 * d:
            x = x / ln * 3 * d
        out[vi] = V[vi] + x
    return M.Part(out, list(F), part.mat, name=part.name + "_off")


def _ob(part, name):
    import bpy
    me = bpy.data.meshes.new(name)
    me.from_pydata(part.V.tolist(), [], part.F)
    me.validate(clean_customdata=False)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def boolean(a, b, op="INTERSECT", mat=None, name="bool"):
    import bpy
    oa, ob_ = _ob(a, "ba"), _ob(b, "bb")
    m = oa.modifiers.new("b", "BOOLEAN")
    m.operation = op
    m.object = ob_
    m.solver = "EXACT"
    dg = bpy.context.evaluated_depsgraph_get()
    ev = oa.evaluated_get(dg)
    me2 = bpy.data.meshes.new_from_object(ev)
    V = np.array([v.co[:] for v in me2.vertices]) if len(me2.vertices) else np.zeros((0, 3))
    F = [tuple(p.vertices) for p in me2.polygons]
    for o in (oa, ob_):
        me = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(me)
    bpy.data.meshes.remove(me2)
    if len(F) == 0:
        return None
    return M.Part(V, F, mat or a.mat, name=name)


def prism_y(outline_xz, y0, y1, mat):
    o = np.asarray(outline_xz, float)
    area = 0.5 * np.sum(o[:, 0] * np.roll(o[:, 1], -1) - np.roll(o[:, 0], -1) * o[:, 1])
    if area < 0:
        o = o[::-1]
    V, F = M.prism(o, abs(y1 - y0), axis="y", center=(y0 + y1) / 2)
    p = M.Part(V, F, mat, name="prism")
    M.recalc_normals(p)
    return p


def split_faces(part, fn):
    """Split a part into several parts by a per-face material function fn(face_index, normal, centroid) -> mat."""
    N = face_normals(part.V, part.F)
    groups = {}
    for i, f in enumerate(part.F):
        c = part.V[list(f)].mean(0)
        groups.setdefault(fn(i, N[i], c), []).append(f)
    out = []
    for m, fs in groups.items():
        out.append(M.Part(part.V.copy(), fs, m, name=part.name))
    for p in out:     # drop unused vertices
        used = sorted({i for f in p.F for i in f})
        remap = {o: n for n, o in enumerate(used)}
        p.V = p.V[used]
        p.F = [tuple(remap[i] for i in f) for f in p.F]
    return out


def torus(R, r, mat, nu=48, nv=6, wave=None, name="ring"):
    """Closed torus in the XY plane. wave(u) -> (dz, dR) modulates the ring (ripples, zigzags)."""
    V, F = [], []
    for i in range(nu):
        u = 2 * math.pi * i / nu
        dz, dR = wave(u) if wave else (0.0, 0.0)
        c = np.array([(R + dR) * math.cos(u), (R + dR) * math.sin(u), dz])
        rad = np.array([math.cos(u), math.sin(u), 0.0])
        for j in range(nv):
            v = 2 * math.pi * j / nv
            V.append(c + r * (math.cos(v) * rad + math.sin(v) * np.array([0, 0, 1.0])))
    for i in range(nu):
        for j in range(nv):
            a = i * nv + j
            b = ((i + 1) % nu) * nv + j
            c = ((i + 1) % nu) * nv + (j + 1) % nv
            d = i * nv + (j + 1) % nv
            F.append((a, b, c, d))
    return M.Part(np.array(V), F, mat, name=name)


def octa(center, r, mat, h=1.5, rot=(0, 0, 0), name="gem"):
    V = np.array([(r, 0, 0), (0, r, 0), (-r, 0, 0), (0, -r, 0), (0, 0, r * h), (0, 0, -r * h)])
    F = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (1, 0, 5), (2, 1, 5), (3, 2, 5), (0, 3, 5)]
    return M.Part(V, F, mat, name=name).rot(Rx(rot[0]) @ Ry(rot[1]) @ Rz(rot[2])).move(center)


def drop3d(center, r, mat, n=8, name="drop"):
    """A small teardrop bead, tip up."""
    prof = [(0, -r), (r * 0.7, -r * 0.72), (r, -r * 0.1), (r * 0.72, r * 0.55), (r * 0.3, r * 1.25), (0, r * 1.75)]
    V, F = M.lathe(prof, n)
    return M.Part(V, F, mat, name=name).move(center)


def icosphere(r, mat, sub=1, name="gemsphere"):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    V, F = _bm_to(bm)
    bm.free()
    return M.Part(V, F, mat, name=name)


def hex_crystal(L, r, tip, mat, tip_bot=None, sides=6, squash=0.86, lean=0.18, name="crystal"):
    """Hexagonal prism with a pointed top (and optional pointed bottom), flat front facet facing -Y."""
    if tip_bot is None:
        prof = [(0, 0.0), (r, 0.0), (r, L - tip), (0, L)]
    else:
        prof = [(0, 0.0), (r, tip_bot), (r, L - tip), (0, L)]
    V, F = M.lathe(prof, sides, a0=0.0)
    V = np.asarray(V, float)
    V[:, 1] *= squash
    top = np.isclose(V[:, 2], L) & (np.abs(V[:, 0]) + np.abs(V[:, 1]) < 1e-9)
    V[top, 0] += lean * r
    return M.Part(V, F, mat, name=name)


def thick_line(pts, widths):
    """2D polyline -> closed outline polygon with the given half-widths per point."""
    P = np.asarray(pts, float)
    L, R = [], []
    for i in range(len(P)):
        if i == 0:
            t = P[1] - P[0]
        elif i == len(P) - 1:
            t = P[-1] - P[-2]
        else:
            t = (P[i + 1] - P[i]) / np.linalg.norm(P[i + 1] - P[i]) + (P[i] - P[i - 1]) / np.linalg.norm(P[i] - P[i - 1])
        t = t / np.linalg.norm(t)
        n = np.array([-t[1], t[0]])
        w = widths[i]
        L.append(P[i] + n * w)
        R.append(P[i] - n * w)
    out = L + R[::-1]
    # drop duplicate points (zero-width ends)
    ded = [out[0]]
    for p in out[1:]:
        if np.linalg.norm(p - ded[-1]) > 1e-6:
            ded.append(p)
    if np.linalg.norm(ded[0] - ded[-1]) < 1e-6:
        ded.pop()
    return np.array(ded)


def circle(c, r, n=10):
    return np.array([(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)])


# ---- motifs: 2D layers in a unit box (u right, v up, about -0.5..0.5); later layers sit on top --------------------

def _teardrop(cx, cy, r, tip, n=16):
    """Round bottom (centre cx, cy, radius r), pointed tip at (cx, cy + tip)."""
    d = tip
    a = math.asin(min(0.99, r / d))
    ts = np.linspace(math.pi / 2 + (math.pi / 2 - a), math.pi / 2 - (math.pi / 2 - a) + 2 * math.pi, n)
    pts = [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in ts]
    return np.array([(cx, cy + tip)] + pts[::-1])


def motif_layers(f, rng=None):
    """[(polygon, role, lift_level)] for a family (role -> cr_<f>_<role> material)."""
    L = []
    if f == "ember":
        flame = [(0.0, -0.46), (0.14, -0.43), (0.23, -0.33), (0.26, -0.18), (0.22, -0.02), (0.3, 0.13), (0.15, 0.07),
                 (0.11, 0.2), (0.14, 0.34), (0.05, 0.52), (-0.01, 0.33), (-0.09, 0.22), (-0.24, 0.3), (-0.18, 0.12),
                 (-0.24, -0.04), (-0.26, -0.2), (-0.21, -0.35), (-0.12, -0.43)]
        core = [(0.0, -0.38), (0.1, -0.33), (0.14, -0.2), (0.1, -0.06), (0.06, 0.08), (0.02, 0.22), (-0.04, 0.06),
                (-0.1, -0.06), (-0.13, -0.2), (-0.09, -0.33)]
        L += [(np.array(flame), "glow", 1), (np.array(core), "hot", 2)]
        for (x, y, s) in ((0.36, 0.34, 0.035), (-0.34, 0.46, 0.03), (0.3, -0.36, 0.028)):
            L.append((np.array([(x, y + s * 1.6), (x + s, y), (x, y - s * 1.6), (x - s, y)]), "hot", 1))
    elif f == "aqua":
        L.append((_teardrop(0.0, -0.14, 0.3, 0.66, 20), "glow", 1))
        L.append((_teardrop(-0.08, -0.2, 0.1, 0.24, 10), "hot", 2))
        for (x, y, r) in ((0.34, 0.2, 0.075), (0.42, -0.02, 0.05), (-0.36, 0.3, 0.055), (0.3, 0.42, 0.04)):
            L.append((circle((x, y), r, 10), "hot", 1))
    elif f == "nova":
        pts = []
        for k in range(16):
            a = math.pi / 2 + k * math.pi / 8
            r = (0.52 if k % 4 == 0 else 0.3) if k % 2 == 0 else 0.085
            pts.append((r * math.cos(a), r * math.sin(a)))
        L.append((np.array(pts), "glow", 1))
        L.append((circle((0, 0), 0.1, 12), "hot", 2))
        inner = []
        for k in range(8):
            a = math.pi / 2 + k * math.pi / 4
            r = 0.3 if k % 2 == 0 else 0.05
            inner.append((r * math.cos(a), r * math.sin(a)))
        L.append((np.array(inner), "hot", 2))
    elif f == "thundra":
        main = [(0.12, 0.52), (-0.1, 0.12), (0.06, 0.06), (-0.14, -0.3), (-0.02, -0.34), (-0.12, -0.54)]
        wm = [0.0, 0.095, 0.095, 0.085, 0.07, 0.0]
        fork = [(0.02, 0.08), (0.2, -0.12), (0.12, -0.16), (0.3, -0.4)]
        wf = [0.055, 0.06, 0.045, 0.0]
        L.append((thick_line(main, wm), "glow", 1))
        L.append((thick_line(fork, wf), "glow", 1))
        L.append((thick_line(main, [w * 0.45 for w in wm]), "hot", 2))
        L.append((thick_line(fork, [w * 0.45 for w in wf]), "hot", 2))
    elif f == "vipera":
        t = np.linspace(0, 2 * math.pi, 28, endpoint=False)
        almond = np.stack([0.5 * np.cos(t), 0.27 * np.sin(t) * (1 - 0.35 * np.cos(t) ** 2)], 1)
        L.append((almond, "glow", 1))
        L.append((circle((0, 0), 0.21, 16), "hot", 2))
        s = np.linspace(0, 2 * math.pi, 16, endpoint=False)
        slit = np.stack([0.065 * np.cos(s), 0.25 * np.sin(s)], 1)
        L.append((slit, "dark", 3))
    elif f in ("bloodrift", "essencerift", "aetherift"):
        rng = rng or np.random.default_rng(7)
        L += rift_layers(rng)
    elif f == "sora":
        # the sky's ring: a halo with a bright heart and four points of light
        ring = [(0.42 * math.cos(a), 0.42 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 28, endpoint=False)]
        L.append((np.array(ring), "glow", 1))
        L.append((circle((0, 0), 0.28, 20), "dark", 2))
        L.append((circle((0, 0), 0.12, 14), "hot", 3))
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            L.append((circle((0.5 * math.cos(a), 0.5 * math.sin(a)), 0.045, 8), "hot", 1))
    elif f == "luna":
        # a crescent moon and two stars
        t = np.linspace(-math.pi / 2, math.pi / 2, 18)
        outer = np.stack([0.42 * np.cos(t), 0.48 * np.sin(t)], 1)
        inner = np.stack([0.12 + 0.2 * np.cos(t[::-1]), 0.4 * np.sin(t[::-1])], 1)
        L.append((np.concatenate([outer, inner]) - np.array([0.06, 0.0]), "glow", 1))
        for (x, y, r) in ((-0.3, 0.3, 0.05), (-0.36, -0.12, 0.035)):
            L.append((np.array([(x, y + r * 1.8), (x + r, y), (x, y - r * 1.8), (x - r, y)]), "hot", 1))
    elif f == "sol":
        # the sun: a disc with twelve rays
        rays = []
        for k in range(24):
            a = math.pi / 2 + k * math.pi / 12
            r = 0.5 if k % 2 == 0 else 0.3
            rays.append((r * math.cos(a), r * math.sin(a)))
        L.append((np.array(rays), "glow", 1))
        L.append((circle((0, 0), 0.2, 18), "hot", 2))
    elif f == "airah":
        # three gusts of wind curling to the right
        for (y, w) in ((0.26, 0.06), (0.0, 0.07), (-0.26, 0.06)):
            pts = [(-0.42, y), (-0.1, y + 0.04), (0.18, y + 0.02), (0.32, y - 0.06), (0.26, y - 0.14), (0.16, y - 0.1)]
            L.append((thick_line(pts, [0.0, w, w, w * 0.8, w * 0.5, 0.0]), "glow", 1))
            L.append((thick_line(pts[:3], [0.0, w * 0.4, 0.0]), "hot", 2))
    if f in OUTLINED:
        out = []
        for poly, role, lvl in L:
            if role == "glow":
                P = np.asarray(poly, float)
                c = P.mean(0)
                n = len(P)
                sgn = 1.0 if 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]) > 0 else -1.0
                # grow the polygon outward along its vertex normals
                grown = []
                for i in range(n):
                    a, b, cc = P[i - 1], P[i], P[(i + 1) % n]
                    t = (cc - a)
                    t = t / max(np.linalg.norm(t), 1e-9)
                    nrm = np.array([t[1], -t[0]])
                    grown.append(b + nrm * 0.045 * sgn)
                out.append((np.array(grown), "dark", 1))
        L = out + [(p, r, l + 1) for p, r, l in L]
    return L


def rift_layers(rng, n=13):
    """A torn, jagged lens-shaped opening (wide in the middle), a white-hot seam and hairline side cracks."""
    ys = np.linspace(0.56, -0.56, n)
    t = np.linspace(0, 1, n)
    cx = np.cumsum(np.concatenate([[0], rng.normal(0, 0.035, n - 1)]))
    cx = cx - np.linspace(cx[0], cx[-1], n) * 0.6
    w = 0.01 + 0.105 * np.sin(np.pi * t) ** 1.3
    jl = 0.65 + 0.7 * rng.random(n)
    jr = 0.65 + 0.7 * rng.random(n)
    right = [(cx[i] + w[i] * jr[i], ys[i]) for i in range(1, n - 1)]
    left = [(cx[i] - w[i] * jl[i], ys[i]) for i in range(n - 2, 0, -1)]
    outer = np.array([(cx[0], ys[0])] + right + [(cx[-1], ys[-1])] + left)
    inner = np.array([(cx[0], ys[0] - 0.06)] + [(cx[i] + w[i] * 0.2, ys[i]) for i in range(1, n - 1)] + [(cx[-1], ys[-1] + 0.06)]
                     + [(cx[i] - w[i] * 0.2, ys[i]) for i in range(n - 2, 0, -1)])
    out = [(outer, "glow", 1), (inner, "hot", 2)]
    for i0, sgn in ((3, 1), (5, -1), (8, 1), (10, -1)):
        x0 = cx[i0] + sgn * w[i0] * 0.8
        br = [(x0, ys[i0]), (x0 + sgn * 0.09, ys[i0] + 0.03), (x0 + sgn * 0.17, ys[i0] - 0.02), (x0 + sgn * 0.23, ys[i0] + 0.02)]
        out.append((thick_line(br, [0.022, 0.016, 0.01, 0.0]), "glow", 1))
    return out


# ---- inlays -----------------------------------------------------------------------------------------------------------

def inlay(body, f, center, h, lift=0.0009, rot=0.0, back=True, rng=None, layers=None):
    """Glowing motif inlaid in the front (-Y) facets of a closed faceted body (and mirrored on the back)."""
    parts = []
    layers = layers if layers is not None else motif_layers(f, rng)
    ymin, ymax = body.V[:, 1].min() - 0.02, body.V[:, 1].max() + 0.02
    yc = body.V[:, 1].mean()
    shells = {}
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    cen = body.V.mean(0)
    core = M.Part((body.V - cen) * 0.58 + cen, list(body.F), mk(f, "core"), name="icon_core")
    parts.append(core)
    for poly, role, lvl in layers:
        if lvl not in shells:
            shells[lvl] = offset_planes(body, lift * lvl)
        P = np.asarray(poly, float) * h
        P = np.stack([P[:, 0] * c - P[:, 1] * s, P[:, 0] * s + P[:, 1] * c], 1) + np.asarray(center, float)
        for side in (("front", "back") if back else ("front",)):
            y0, y1 = (ymin, yc) if side == "front" else (yc, ymax)
            pr = prism_y(P, y0, y1, mk(f, role))
            got = boolean(pr, shells[lvl], "INTERSECT", mk(f, role), name=("inlay" if side == "front" else "back_inlay"))
            if got is not None:
                parts.append(got)
    return parts


# ---- grade builders ---------------------------------------------------------------------------------------------------

FSEED = {f: i * 11 + 3 for i, f in enumerate(FAMILIES)}


def _body_mats(f, part, n_mats=None):
    """Aetherift: split the body into rainbow facets; everyone else keeps one body material."""
    if f != "aetherift":
        return [part]
    cyc = [mk(f, "body"), mk(f, "mag"), mk(f, "gold"), mk(f, "pale")]

    def pick(i, n, c):
        a = math.atan2(n[2], n[0]) + 0.7 * n[1]
        return cyc[int(((a / (2 * math.pi)) * 7 + 10 + i * 0.37) % 4)]
    return split_faces(part, pick)


def fragment(f):
    """A rough chip broken off a bigger crystal: an angular, irregular flake with a ridged front, frosted skin and one
    big fresh fracture facet."""
    rng = np.random.default_rng(FSEED[f])
    # silhouette in the view plane (x, z): acute corners, one long snapped point
    outline = [(-0.088, -0.03), (-0.035, -0.062), (0.05, -0.058), (0.094, -0.012), (0.07, 0.036), (0.01, 0.062),
               (-0.03, 0.098), (-0.058, 0.03)]
    pts = []
    for (x, z) in outline:
        x += (rng.random() - 0.5) * 0.012
        z += (rng.random() - 0.5) * 0.012
        pts.append((x, (rng.random() - 0.5) * 0.012, z))
    # ridges on the front and the back give it facets and depth
    for (x, z, y) in ((-0.02, 0.012, -0.036), (0.03, -0.012, -0.034), (-0.012, 0.05, -0.02), (0.012, 0.004, 0.034),
                      (-0.03, -0.02, 0.028)):
        pts.append((x + (rng.random() - 0.5) * 0.01, y, z + (rng.random() - 0.5) * 0.01))
    body = hull(np.array(pts), mk(f, "dull"), "body", merge_deg=1.0)
    # the fresh break across the upper right
    n1 = np.array([0.6, -0.45, 0.66])
    n1 /= np.linalg.norm(n1)
    body = cut_hull(body, [(np.array([0.034, -0.01, 0.03]), n1)])
    # a stepped bite out of the lower left edge makes the outline jagged (concave)
    bite = hull(np.array([(-0.1, -0.06, -0.075), (-0.1, 0.06, -0.075), (-0.028, -0.06, -0.075), (-0.028, 0.06, -0.075),
                          (-0.1, -0.06, -0.006), (-0.1, 0.06, -0.012), (-0.062, -0.06, -0.075), (-0.062, 0.06, -0.075)])
                + np.array([0.0, 0.0, 0.0]), mk(f, "dull"))
    bite.rot(Ry(-14), center=(-0.06, 0, -0.04))
    got = boolean(body, bite, "DIFFERENCE", mk(f, "dull"), name="body")
    if got is not None:
        body = got

    def skin(i, nrm, c):
        if abs(np.dot(nrm, n1)) > 0.995:
            return mk(f, "body")          # fresh fracture: clear and bright
        return mk(f, "dull")
    parts = _body_mats(f, body) if f == "aetherift" else split_faces(body, skin)
    parts += inlay(body, f, (-0.006, 0.006), 0.085, rng=np.random.default_rng(FSEED[f] + 1))
    top = body.V[np.argmax(body.V[:, 2])]
    parts += extras(f, "fragment", {"top": top, "r": 0.03, "center": np.array([0, 0, 0.0]),
                                    "bottom": np.array([-0.01, -0.02, -0.056])})
    return parts


def shard(f):
    L, r = 0.26, 0.042
    body = hex_crystal(L, r, 0.07, mk(f, "body"), tip_bot=0.05, lean=0.12, name="body")
    body.move((0, 0, -L / 2))
    parts = []
    # terminations in the edge colour (thundra's violet ends, vipera's black-green, ...), the prism in the body colour
    zc1, zc2 = -L / 2 + 0.05 - 1e-4, L / 2 - 0.07 + 1e-4

    def ends(i, n, c):
        if f == "aetherift":
            return None
        return mk(f, "edge") if (c[2] > zc2 or c[2] < zc1) else mk(f, "body")
    if f == "aetherift":
        parts += _body_mats(f, body)
    else:
        parts += split_faces(body, ends)
    parts += inlay(body, f, (0.0, 0.004), 0.15, rng=np.random.default_rng(FSEED[f] + 2))
    parts += extras(f, "shard", {"top": np.array([0.12 * r, 0, L / 2]), "r": r, "center": np.array([0, 0, 0.0]),
                                 "bottom": np.array([0, 0, -L / 2]), "L": L})
    for p in parts:
        p.rot(Ry(14)).rot(Rx(-6))
    return parts


def crystalline(f):
    rng = np.random.default_rng(FSEED[f] + 5)
    parts = []
    # rock base (a small geode)
    pts = []
    for i in range(22):
        z = 1 - (i + 0.5) / 22 * 2
        rr = math.sqrt(1 - z * z)
        th = 2.4 * i + rng.random() * 0.5
        k = 0.85 + 0.25 * rng.random()
        pts.append((0.1 * rr * math.cos(th) * k, 0.082 * rr * math.sin(th) * k, 0.04 * z * k))
    rock = hull(np.array(pts), "cr_rock", "rock")
    rock = cut_hull(rock, [((0, 0, -0.022), (0, 0, -1))])
    parts.append(rock)
    for (x, y, z, L, tx, ty) in ((-0.075, -0.02, 0.0, 0.05, 10, -62), (0.08, 0.03, 0.004, 0.045, -8, 66), (0.02, -0.07, -0.004, 0.04, -60, 12)):
        nub = hex_crystal(L, L * 0.2, L * 0.35, mk(f, "dull"), lean=0.1, name="crystal")
        nub.rot(Ry(ty) @ Rx(tx)).move((x, y, z))
        parts += _body_mats(f, nub) if f == "aetherift" else [nub]
    # crystals: (x, y, length, radius, tilt_x, tilt_y, spin, main)
    spec = [(0.0, 0.004, 0.25, 0.034, 0, 0, 0, True),
            (-0.045, 0.015, 0.16, 0.024, 4, -26, 12, False),
            (0.05, 0.012, 0.18, 0.025, -3, 24, -8, False),
            (0.022, 0.05, 0.14, 0.02, 24, 14, 30, False),
            (-0.03, 0.052, 0.12, 0.019, 26, -16, -20, False),
            (0.07, -0.03, 0.085, 0.016, -14, 40, 18, False)]
    for (x, y, L, r, tx, ty, sp, main) in spec:
        c = hex_crystal(L, r, L * 0.26, mk(f, "body"), lean=0.1 + 0.1 * rng.random(), name="crystal")
        loc_parts = []
        if f == "aetherift":
            loc_parts += _body_mats(f, c)
        else:
            zc = L - L * 0.26 + 1e-4
            loc_parts += split_faces(c, lambda i, n, cc, zc=zc: mk(f, "edge") if (cc[2] > zc and f in ("thundra", "vipera", "bloodrift")) else mk(f, "body"))
        if main:
            loc_parts += inlay(c, f, (0.0, L * 0.47), L * 0.5, rng=np.random.default_rng(FSEED[f] + 3))
        R = Ry(ty) @ Rx(tx) @ Rz(sp if not main else 0)
        for p in loc_parts:
            p.move((0, 0, -0.012)).rot(R).move((x, y, 0.004))
        parts += loc_parts
    parts += extras(f, "crystalline", {"top": np.array([0.03, 0.004, 0.245]), "r": 0.034, "center": np.array([0, 0, 0.12]),
                                       "bottom": np.array([0.0, -0.06, 0.02])})
    return parts


RING_MODE = {"aqua": "wave", "thundra": "zigzag"}


def orbital(f):
    d = FAM[f]
    metal = d["metal"]
    parts = []
    zc, r = 0.128, 0.074
    gem = icosphere(r, mk(f, "body"), 2, "gem")
    gem.rot(Rz(18) @ Rx(8))
    gem.scale((1.0, 0.94, 1.04))
    gem.move((0, 0, zc))
    parts += _body_mats(f, gem)
    parts += inlay(gem, f, (0.0, zc), r * 1.18, lift=0.0011, rng=np.random.default_rng(FSEED[f] + 4))
    # cradle: a low foot and stem, a collar and three claws holding the sphere from below
    zt = zc - r * 0.93
    parts.append(K.lathe([(0, 0.0), (0.04, 0.0), (0.043, 0.005), (0.034, 0.011), (0.015, 0.017), (0.009, 0.026),
                          (0.011, zt - 0.012), (0.024, zt - 0.004), (0.02, zt + 0.001), (0, zt + 0.001)], metal, 16, "foot"))
    for k in range(3):
        a = math.radians(90 + 120 * k + 30)
        pts = []
        for t in np.linspace(0, 1, 6):
            ang = -math.pi / 2 + 0.55 + t * 0.85          # from the collar up the side of the gem
            rr = (r + 0.003) * math.cos(ang)
            z = zc + (r + 0.003) * math.sin(ang)
            if t == 0:
                rr, z = 0.021, zt - 0.003
            pts.append((rr * math.cos(a), rr * math.sin(a), z))
        parts.append(K.tube(pts, [(0.0055, 0.004), (0.005, 0.0038), (0.0045, 0.0034), (0.004, 0.003), (0.0034, 0.0025), (0.001, 0.001)],
                            metal, n=6, up=(math.cos(a), math.sin(a), 0), name="claw"))
        tip = pts[-2]
        parts.append(octa(tip, 0.005, mk(f, "glow"), h=1.3, name="claw_gem"))
    # orbit rings: a metal band and a glowing trail (aqua ripples, thundra zigzags)
    mode = RING_MODE.get(f)
    wave = None
    if mode == "wave":
        def wave(u):
            return 0.003 * math.sin(12 * u), 0.0
    elif mode == "zigzag":
        def wave(u):
            ph = (u * 22 / (2 * math.pi)) % 1.0
            return 0.003 * (abs(ph * 2 - 1) * 2 - 1), 0.0
    ring_a = torus(0.138, 0.0034, metal, 64, 6, name="ring")
    ring_a.rot(Rx(26)).rot(Ry(-16)).move((0, 0, zc))
    ring_b = torus(0.124, 0.0022, mk(f, "glow"), 72 if mode else 56, 5, wave=wave, name="ring_glow")
    ring_b.rot(Rx(-30)).rot(Ry(20)).move((0, 0, zc))
    parts += [ring_a, ring_b]
    # satellites riding the rings
    sats = [(ring_a, 0.138, 26, -16, a) for a in (200, 330, 60)] + [(ring_b, 0.124, -30, 20, a) for a in (250, 20)]
    for i, (_, R, rx, ry, a) in enumerate(sats):
        p = np.array([R * math.cos(math.radians(a)), R * math.sin(math.radians(a)), 0.0])
        p = Ry(ry) @ (Rx(rx) @ p) + np.array([0, 0, zc])
        mat = mk(f, "body") if i % 2 == 0 else mk(f, "hot")
        if f == "aetherift":
            mat = [mk(f, "body"), mk(f, "mag"), mk(f, "gold"), mk(f, "pale"), mk(f, "hot")][i]
        parts.append(octa(tuple(p), 0.0085 if i % 2 == 0 else 0.0065, mat, h=1.45, rot=(20 * i, 35, 15 * i), name="sat"))
    parts += extras(f, "orbital", {"top": np.array([0, 0, zc + r]), "r": r, "center": np.array([0, 0, zc]),
                                   "bottom": np.array([0, -r * 0.35, zc - r * 0.9])})
    return parts


def extras(f, grade, a):
    """Per-family floating accents: ember specks, bubbles, star glints, sparks, venom and blood drops, mana motes, halo."""
    parts = []
    top, r, cen = a["top"], a["r"], a["center"]
    big = grade in ("crystalline", "orbital")
    rng = np.random.default_rng(FSEED[f] + 31)
    if f == "ember" and grade != "fragment":
        for i in range(5 if big else 3):
            p = top + np.array([(-1) ** i * (0.02 + 0.03 * rng.random()), -0.01 * rng.random(), 0.015 + 0.03 * rng.random()])
            parts.append(octa(tuple(p), 0.0045 - 0.0005 * i, mk(f, "hot") if i % 2 else mk(f, "glow"), h=1.8, rot=(0, 20 * i, 30 * i), name="speck"))
    if f == "aqua":
        if grade != "fragment":
            for i in range(4 if big else 3):
                p = top + np.array([(-1) ** i * (0.012 + 0.025 * rng.random()), -0.01, 0.012 + 0.024 * i])
                parts.append(K.sphere(0.0045 + 0.0015 * (i % 2), tuple(p), mk(f, "hot"), 8, 5))
    if f == "nova" and grade != "fragment":
        for i in range(3 if big else 2):
            p = top + np.array([(-1) ** i * (0.03 + 0.02 * rng.random()), -0.01, 0.005 + 0.02 * rng.random()])
            parts.append(octa(tuple(p), 0.004, mk(f, "hot"), h=2.2, rot=(0, 45, 0), name="glint"))
    if f == "thundra" and grade != "fragment":
        for i in range(2 if big else 1):
            s = 1 if i == 0 else -1
            p0 = top + np.array([s * 0.006, -0.004, 0.004])
            pts = [p0, p0 + np.array([s * 0.012, 0, 0.012]), p0 + np.array([s * 0.006, 0, 0.02]), p0 + np.array([s * 0.02, 0, 0.034])]
            parts.append(K.tube(pts, [0.0022, 0.002, 0.0016, 0.0004], mk(f, "hot"), n=5, up=(0, -1, 0), name="spark"))
    if f == "vipera":
        b = a["bottom"]
        parts.append(drop3d(tuple(b + np.array([0, -0.004, -0.012])), 0.0075 if big else 0.006, mk(f, "glow"), 8, "venom"))
        if big:
            parts.append(drop3d(tuple(b + np.array([0.03, -0.004, -0.004])), 0.0045, mk(f, "hot"), 8, "venom"))
    if f == "bloodrift":
        b = a["bottom"]
        parts.append(drop3d(tuple(b + np.array([0, -0.006, -0.01])), 0.0085 if big else 0.0065, mk(f, "glow"), 8, "blood"))
    if f == "essencerift" and grade != "fragment":
        n = 7 if big else 4
        for i in range(n):
            t = i / n
            ang = 2 * math.pi * t * 1.3 + 0.6
            rad = r * (1.5 + 0.9 * t)
            p = cen + np.array([rad * math.cos(ang), rad * math.sin(ang) * 0.6, -r * 0.8 + t * r * 2.6])
            parts.append(octa(tuple(p), 0.0032 + 0.0016 * (i % 2), mk(f, "hot") if i % 2 else mk(f, "glow"), h=1.3, rot=(30 * i, 15 * i, 0), name="mote"))
    if f == "aetherift":
        hr = max(0.014, r * (0.55 if grade != "orbital" else 0.5))
        halo = torus(hr, 0.0018 if grade != "fragment" else 0.0014, mk(f, "hot"), 40, 5, name="halo")
        halo.rot(Rx(-18)).move(tuple(top + np.array([0.0, 0.0, 0.022 if grade != "fragment" else 0.018])))
        parts.append(halo)
        if grade != "fragment":
            cols = ["body", "mag", "gold"]
            for i in range(3):
                p = top + np.array([(-1) ** i * (0.028 + 0.012 * i), -0.008, -0.01 - 0.018 * i])
                parts.append(octa(tuple(p), 0.004, mk(f, cols[i]), h=1.6, rot=(15, 30 * i, 0), name="prism_mote"))
    return parts


BUILDERS = {"fragment": fragment, "shard": shard, "crystalline": crystalline, "orbital": orbital}


def build_parts(iid, for_icon=False):
    f, g = iid.split("_")
    parts = BUILDERS[g](f)
    parts = [p for p in parts if not (p.name.startswith("back_") and for_icon) and not (p.name.startswith("icon_") and not for_icon)]
    # normalise: largest dimension = SIZE[g], standing on z = 0, centred in x/y
    V = np.vstack([p.V for p in parts])
    lo, hi = V.min(0), V.max(0)
    s = SIZE[g] / float((hi - lo).max())
    for p in parts:
        p.V = (p.V - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])) * s
    return parts


FACETED = ("body", "chip", "crystal", "gem", "inlay", "back_inlay", "rock", "sat", "claw_gem", "speck", "glint", "mote",
           "prism_mote")


def _explode(p):
    """Per-face vertices: facets stay flat-shaded whatever the smoothing angle."""
    V, F = [], []
    for f in p.F:
        F.append(tuple(range(len(V), len(V) + len(f))))
        V.extend(p.V[list(f)])
    p.V, p.F = np.array(V), F
    return p


def build_object(iid, parts):
    for p in parts:
        try:
            M.recalc_normals(p)
        except Exception:
            pass
        if p.name in FACETED:
            _explode(p)
    keys = sorted({p.mat for p in parts})
    mats = K.make_materials(keys)
    return M.build_static(iid, parts, mats, sharp_angle=60.0)


# ---- icon renders (Blender, Cycles) ---------------------------------------------------------------------------------

FLOATERS = ("speck", "glint", "mote", "prism_mote", "spark", "sphere", "halo")   # left out of the icon framing

POSE = {  # (object rot x, rot z, camera pitch, camera yaw, frame fill)
    "fragment": (0, -8, 16, 10, 0.64),
    "shard": (0, -6, 10, 8, 0.8),
    "crystalline": (0, -10, 16, 10, 0.84),
    "orbital": (0, 0, 12, 0, 0.94),
}


def _icon_material(key):
    """Cycles look for a palette key: clear jewel for gems, strong emission for glows, the palette PBR otherwise."""
    import bpy
    base, rgb, met, rough, erg, estr = K.MAT[key]
    name = "ICON_" + key
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Metallic"].default_value = met
    b.inputs["Roughness"].default_value = rough
    if base == "BH_Gem":
        dark = max(rgb) < 0.12
        lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        b.inputs["Transmission Weight"].default_value = 0.0 if dark else (0.55 if rough > 0.3 else 0.8)
        b.inputs["IOR"].default_value = 1.55
        b.inputs["Roughness"].default_value = 0.04 if rough < 0.2 else 0.28
        try:
            b.inputs["Coat Weight"].default_value = 0.6
            b.inputs["Coat Roughness"].default_value = 0.02
        except KeyError:
            pass
        # facing-weighted inner glow: facets toward the camera glow through, grazing ones stay deep
        if erg and estr > 0:
            lw = nt.nodes.new("ShaderNodeLayerWeight")
            lw.inputs["Blend"].default_value = 0.45
            mr = nt.nodes.new("ShaderNodeMapRange")
            mr.inputs["From Min"].default_value = 0.0
            mr.inputs["From Max"].default_value = 1.0
            mr.inputs["To Min"].default_value = estr * 1.05 / max(lum, 0.25) ** 0.3
            mr.inputs["To Max"].default_value = estr * 0.25
            nt.links.new(lw.outputs["Facing"], mr.inputs["Value"])
            b.inputs["Emission Color"].default_value = (*erg, 1.0)
            nt.links.new(mr.outputs["Result"], b.inputs["Emission Strength"])
        # coloured depth
        va = nt.nodes.new("ShaderNodeVolumeAbsorption")
        va.inputs["Color"].default_value = (*[min(1.0, c * 1.1 + 0.02) for c in rgb], 1.0)
        va.inputs["Density"].default_value = 6.0
        nt.links.new(va.outputs[0], out.inputs["Volume"])
    elif base == "BH_Emissive":
        b.inputs["Emission Color"].default_value = (*erg, 1.0)
        mul = {"glow": 0.6, "hot": 1.6, "core": 2.0 if key.split("_")[1] not in ("bloodrift",) else 0.5}.get(key.rsplit("_", 1)[-1], 1.5)
        b.inputs["Emission Strength"].default_value = estr * mul
    else:
        if erg:
            b.inputs["Emission Color"].default_value = (*erg, 1.0)
            b.inputs["Emission Strength"].default_value = estr
    return m


def _icon_scene(f, res):
    import bpy
    from mathutils import Vector
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for dev_type in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = dev_type
                prefs.get_devices()
                if any(d.type == dev_type for d in prefs.devices):
                    for d in prefs.devices:
                        d.use = d.type == dev_type
                    sc.cycles.device = "GPU"
                    break
            except Exception:
                continue
    except Exception:
        pass
    sc.cycles.samples = 160
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 16
    sc.cycles.transmission_bounces = 16
    sc.cycles.glossy_bounces = 8
    sc.cycles.volume_bounces = 2
    sc.cycles.caustics_refractive = False
    sc.cycles.caustics_reflective = False
    sc.cycles.blur_glossy = 1.0
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    try:
        sc.view_settings.look = "None"
    except Exception:
        pass
    sc.view_settings.exposure = -0.3
    d = FAM[f]
    hc = tuple(c / 255.0 for c in d["halo"])
    h2 = tuple(c / 255.0 for c in d["halo2"])
    w = bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes.get("Background")
    # studio sphere: dark floor, family-tinted horizon, bright top for facet reflections
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    cr = ramp.color_ramp
    cr.elements[0].position = 0.35
    cr.elements[0].color = (0.004, 0.004, 0.006, 1)
    cr.elements[1].position = 0.95
    cr.elements[1].color = (0.55, 0.55, 0.6, 1)
    e = cr.elements.new(0.55)
    e.color = (hc[0] * 0.5, hc[1] * 0.5, hc[2] * 0.5, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.35
    lights = (
        ("Key", (-2.4, -3.0, 3.4), 420, (1.0, 0.95, 0.88), 1.6),
        ("RimL", (-2.8, 2.6, 1.6), 900, h2, 1.2),
        ("RimR", (2.9, 2.4, 2.2), 1100, hc, 1.2),
        ("Fill", (3.0, -2.8, 0.4), 120, (0.8, 0.85, 1.0), 3.0),
    )
    for name, loc, energy, color, size in lights:
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = energy
        ld.color = color
        ld.size = size
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        dv = Vector((0, 0, 0)) - lo.location
        lo.rotation_euler = dv.to_track_quat("-Z", "Y").to_euler()
    cam_d = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_d.lens = 85
    return cam


def render_icon(iid, out_dir=RAW, res=512, log=print):
    import bpy
    from mathutils import Vector
    f, g = iid.split("_")
    parts = build_parts(iid, for_icon=True)
    frame_pts = np.vstack([p.V for p in parts if p.name not in FLOATERS])
    ob = build_object(iid, parts)
    for i, slot in enumerate(ob.material_slots):
        key = slot.material.name.split("__it_", 1)[1]
        ob.data.materials[i] = _icon_material(key)
    cam = _icon_scene(f, res)
    rx, rz, pitch, yaw, fill = POSE[g]
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = (math.radians(rx), 0, math.radians(rz))
    bpy.context.view_layer.update()
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    c = sum(bb, Vector()) / 8.0
    ob.location -= c
    bpy.context.view_layer.update()
    p, y = math.radians(pitch), math.radians(yaw)
    dv = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
    dist = 3.0
    cam.location = dv * dist
    cam.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    # frame: fit the projected vertex bounds to `fill` of the frame
    inv = cam.matrix_world.inverted()
    mw = ob.matrix_world
    xs, ys = [], []
    for v in frame_pts:
        q = inv @ (mw @ Vector(tuple(v)))
        xs.append(q.x / -q.z)
        ys.append(q.y / -q.z)
    ext = max(max(xs) - min(xs), max(ys) - min(ys))
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    sensor = cam.data.sensor_width
    # tan(half fov) = sensor / (2 lens); want ext = fill * 2 tan(half fov)
    cam.data.lens = sensor / (ext / fill)
    cam.data.shift_x = cx / (ext / fill)
    cam.data.shift_y = cy / (ext / fill)
    cam.data.clip_start = 0.01
    cam.data.clip_end = 100
    os.makedirs(out_dir, exist_ok=True)
    bpy.context.scene.render.filepath = os.path.join(out_dir, iid + ".png")
    bpy.ops.render.render(write_still=True)
    log(f"[crystal icon] {iid}")


def render_icons(ids=None, log=print):
    from build import reset
    for iid in (ids or IDS):
        reset()
        render_icon(iid, log=log)


# ---- icon compositing (system Python + PIL) ---------------------------------------------------------------------------
# Works on a 512 px canvas in premultiplied float RGBA, downsampled to 256 at the end.

ICON_SCALE = {"fragment": 0.7, "shard": 0.84, "crystalline": 0.86, "orbital": 0.98}   # crystal size in the frame
GRADE_GLOW = {"fragment": 0.55, "shard": 0.75, "crystalline": 0.9, "orbital": 1.1}
SPARKS = {"fragment": 1, "shard": 2, "crystalline": 3, "orbital": 4}


def _blur(a, sigma):
    from scipy.ndimage import gaussian_filter   # PIL 12 no longer blurs float ("F") images
    if a.ndim == 2:
        return gaussian_filter(a.astype(np.float32), sigma, mode="constant")
    return np.stack([_blur(a[..., c], sigma) for c in range(a.shape[2])], -1)


def _grid(S):
    y, x = np.mgrid[0:S, 0:S].astype(np.float32)
    return x, y


def _add_light(canvas, rgb):
    """Additive light onto a premultiplied RGBA canvas (glows on a transparent background raise the alpha)."""
    canvas[..., :3] += rgb
    canvas[..., 3] = np.maximum(canvas[..., 3], np.clip(rgb.max(-1), 0, 1))
    return canvas


def _over(canvas, layer):
    a = layer[..., 3:4]
    canvas[...] = layer + canvas * (1 - a)
    return canvas


def _star(S, cx, cy, L, t, col, strength=1.0, diag=0.45):
    x, y = _grid(S)
    dx, dy = x - cx, y - cy

    def ray(u, v, L, t):
        return np.exp(-(v / t) ** 2) * np.clip(1 - np.abs(u) / L, 0, 1) ** 2.2
    I = ray(dx, dy, L, t) + ray(dy, dx, L, t)
    r2 = (dx + dy) / math.sqrt(2)
    s2 = (dx - dy) / math.sqrt(2)
    I += diag * (ray(r2, s2, L * 0.45, t * 0.8) + ray(s2, r2, L * 0.45, t * 0.8))
    I += 1.3 * np.exp(-(dx * dx + dy * dy) / (2 * (t * 1.6) ** 2))
    return I[..., None] * np.asarray(col, np.float32)[None, None, :] * strength


def _seg_dist(x, y, a, b):
    ab = b - a
    t = np.clip(((x - a[0]) * ab[0] + (y - a[1]) * ab[1]) / max(float(ab @ ab), 1e-6), 0, 1)
    return np.sqrt((x - a[0] - t * ab[0]) ** 2 + (y - a[1] - t * ab[1]) ** 2)


def _family_fx(f, g, S, c, R, hc, h2, rng):
    """Faint family-flavoured light behind the crystal (additive rgb)."""
    x, y = _grid(S)
    dx, dy = x - c[0], y - c[1]
    d = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)
    out = np.zeros((S, S, 3), np.float32)
    hcv, h2v = np.asarray(hc, np.float32), np.asarray(h2, np.float32)
    if f == "nova" or g == "orbital":
        # radiant rays: 4 long + 4 short for nova, 12 soft ones behind every orbital
        if f == "nova":
            k = 8
            amp = np.where((np.round((ang + math.pi / 2) / (math.pi / 4)) % 2) == 0, 1.0, 0.55)
            w = 0.07
        else:
            k = 12
            amp = 0.5
            w = 0.05
        a = (ang + math.pi / 2) % (2 * math.pi / k)
        a = np.minimum(a, 2 * math.pi / k - a)
        rays = np.exp(-(a / w) ** 2) * amp * np.exp(-((d / (R * (1.05 if f == "nova" else 0.95))) ** 2)) * np.clip(d / (R * 0.2), 0, 1)
        out += rays[..., None] * (h2v if f == "nova" else hcv)[None, None] * (0.55 if f == "nova" else 0.28)
    if f == "ember":
        for i in range(12):
            px = c[0] + (rng.random() - 0.5) * R * 1.4
            py = c[1] - R * (0.1 + 0.8 * rng.random())
            rr = 2.2 + 3.0 * rng.random()
            col = np.array([1.0, 0.45 + 0.4 * rng.random(), 0.1], np.float32)
            out += (np.exp(-((x - px) ** 2 + (y - py) ** 2) / (2 * rr * rr)) * (0.5 + 0.6 * rng.random()))[..., None] * col
    if f == "aqua":
        for i in range(7):
            a0 = rng.random() * 2 * math.pi
            rd = R * (0.55 + 0.35 * rng.random())
            px, py = c[0] + rd * math.cos(a0), c[1] + rd * math.sin(a0) * 0.9
            rb = 6 + 9 * rng.random()
            dd = np.sqrt((x - px) ** 2 + (y - py) ** 2)
            ring = np.exp(-((dd - rb) / 1.6) ** 2) + 0.35 * np.exp(-((x - px + rb * 0.35) ** 2 + (y - py + rb * 0.35) ** 2) / 6.0)
            out += ring[..., None] * h2v * 0.45
    if f == "thundra":
        for side in (-1, 1):
            p = np.array([c[0] + side * R * 0.35, c[1] - R * 0.2])
            pts = [p.copy()]
            for i in range(6):
                p = p + np.array([side * R * (0.08 + 0.05 * rng.random()), (rng.random() - 0.55) * R * 0.22])
                pts.append(p.copy())
            I = np.zeros((S, S), np.float32)
            for a, b in zip(pts[:-1], pts[1:]):
                dd = _seg_dist(x, y, a, b)
                I = np.maximum(I, np.exp(-(dd / 2.2) ** 2) + 0.35 * np.exp(-(dd / 8.0) ** 2))
            out += I[..., None] * h2v * 0.55
    if f in ("vipera", "bloodrift"):
        n = _blur(rng.random((S, S)).astype(np.float32), 18)
        n = (n - n.mean()) / (n.std() + 1e-6)
        mist = np.clip(n * 0.5 + 0.3, 0, 1) * np.exp(-((d / (R * 0.95)) ** 2)) * np.clip((y - c[1] + R * 0.3) / R, 0, 1)
        out += mist[..., None] * hcv * (0.35 if f == "vipera" else 0.45)
        if f == "bloodrift":
            for i in range(6):
                px = c[0] + (rng.random() - 0.5) * R * 1.5
                py = c[1] + R * (0.1 + 0.7 * rng.random())
                rr = 2.0 + 2.5 * rng.random()
                out += (np.exp(-((x - px) ** 2 + ((y - py) * 0.7) ** 2) / (2 * rr * rr)) * 0.8)[..., None] * np.array([1.0, 0.05, 0.05], np.float32)
    if f == "essencerift":
        for i in range(14):
            t = i / 14
            a0 = 2 * math.pi * t * 1.6 + 0.4
            rd = R * (0.35 + 0.6 * t)
            px, py = c[0] + rd * math.cos(a0), c[1] + rd * math.sin(a0) * 0.85
            rr = 1.8 + 2.6 * (1 - t)
            out += (np.exp(-((x - px) ** 2 + (y - py) ** 2) / (2 * rr * rr)))[..., None] * (h2v if i % 2 else hcv) * 0.9
    if f == "aetherift":
        hue = (ang / (2 * math.pi)) % 1.0
        rgb = np.stack([np.clip(np.abs(hue * 6 - 3) - 1, 0, 1), np.clip(2 - np.abs(hue * 6 - 2), 0, 1),
                        np.clip(2 - np.abs(hue * 6 - 4), 0, 1)], -1)
        ring = np.exp(-((d - R * 0.8) / (R * 0.07)) ** 2)
        out += ring[..., None] * rgb * 0.45
    return out


def compose_icon(iid, raw_dir=RAW, size=256):
    from PIL import Image
    f, g = iid.split("_")
    S = 512
    d = FAM[f]
    hc = np.array(d["halo"], np.float32) / 255.0
    h2 = np.array(d["halo2"], np.float32) / 255.0
    rng = np.random.default_rng(FSEED[f] * 7 + GRADES.index(g))
    raw = Image.open(os.path.join(raw_dir, iid + ".png")).convert("RGBA")
    # tight crop of the render, scaled to its grade's size in the frame
    bbox = raw.getbbox()
    cr = raw.crop(bbox)
    w, h = cr.size
    k = ICON_SCALE[g] * S / max(w, h)
    cr = cr.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ox, oy = (S - cr.size[0]) // 2, (S - cr.size[1]) // 2 + (6 if g != "orbital" else 0)
    lay.paste(cr, (ox, oy))
    L = np.asarray(lay, np.float32) / 255.0
    L[..., :3] *= L[..., 3:4]                       # premultiply
    A = L[..., 3]
    ys, xs = np.nonzero(A > 0.5)
    c = (float(xs.mean()), float(ys.mean()))
    R = S * 0.47
    x, y = _grid(S)
    dd = np.sqrt((x - S / 2) ** 2 + (y - S / 2) ** 2)
    canvas = np.zeros((S, S, 4), np.float32)
    # 1. the dark pool the game's item icons sit on
    canvas[..., 3] = 0.72 * np.clip(1 - dd / R, 0, 1) ** 0.75
    # 2. family halo behind the crystal
    gg = GRADE_GLOW[g]
    dc = np.sqrt((x - c[0]) ** 2 + (y - c[1]) ** 2)
    halo = 0.55 * np.exp(-(dc / (R * 0.55)) ** 2) + 0.22 * np.exp(-(dc / (R * 0.95)) ** 2)
    _add_light(canvas, (halo * gg)[..., None] * hc[None, None] * np.clip(1.05 - dd / R, 0, 1)[..., None])
    # 3. family flavour + grade ornament
    fx = _family_fx(f, g, S, c, R, hc, h2, rng) * gg
    _add_light(canvas, fx * np.clip(1.0 - dd / (R * 1.02), 0, 1)[..., None] ** 0.5)
    # 4. outer glow hugging the silhouette
    og = _blur(A, 14) * 0.85 + _blur(A, 5) * 0.4
    _add_light(canvas, og[..., None] * (0.5 * hc + 0.5 * h2)[None, None] * 0.75 * gg)
    # 5. a thin dark keyline so the crystal reads on any slot
    kl = np.zeros_like(canvas)
    kl[..., 3] = np.clip(_blur(A, 2.2) * 2.2, 0, 1) * 0.8
    _over(canvas, kl)
    # 6. the crystal
    _over(canvas, L)
    # 7. bloom from its bright parts
    lum = 0.2126 * L[..., 0] + 0.7152 * L[..., 1] + 0.0722 * L[..., 2]
    br = L[..., :3] * np.clip((lum - 0.5) / 0.4, 0, 1)[..., None]
    _add_light(canvas, _blur(br, 5) * 0.55 + _blur(br, 16) * 0.55)
    # 8. sparkles on the brightest points, favouring the top
    sc = _blur(lum * A, 3) * (1.2 - 0.6 * (y / S))
    cand = []
    for i in range(SPARKS[g]):
        j = int(np.argmax(sc))
        py, px = divmod(j, S)
        cand.append((px, py))
        sc[max(0, py - 70):py + 70, max(0, px - 70):px + 70] = 0
    for i, (px, py) in enumerate(cand):
        Ls = (60 if i == 0 else 38) * (1.0 if g != "fragment" else 0.8)
        col = 0.55 * np.ones(3, np.float32) + 0.45 * h2
        _add_light(canvas, _star(S, px, py, Ls, 1.6, col, 1.0 if i == 0 else 0.75))
    # premultiplied canvas -> 8 bit, downsample (still premultiplied), un-premultiply
    a = np.clip(canvas[..., 3], 0, 1)
    rgb = np.clip(np.minimum(canvas[..., :3], a[..., None]), 0, 1)
    im_p = Image.fromarray((np.dstack([rgb, a]) * 255 + 0.5).astype(np.uint8), "RGBA")
    small = np.asarray(im_p.resize((size, size), Image.LANCZOS), np.float32) / 255.0
    al = small[..., 3:4]
    col = np.where(al > 1e-4, small[..., :3] / np.maximum(al, 1e-4), 0)
    out = np.dstack([np.clip(col, 0, 1), al])
    return Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGBA")


def _font(n, bold=False):
    from PIL import ImageFont
    for name in (("arialbd.ttf", "arial.ttf") if bold else ("arial.ttf",)):
        try:
            return ImageFont.truetype(name, n)
        except OSError:
            continue
    return ImageFont.load_default()


def contact_sheet(src_dir, path, cell=256, label=True, bg=(22, 20, 26), slot=None, suffix=".png"):
    from PIL import Image, ImageDraw
    pad = 12 if cell > 100 else 8
    lh = 20 if label else 0
    left = 130 if cell > 100 else 96
    W = left + pad + 4 * (cell + pad)
    H = 30 + pad + 8 * (cell + lh + pad)
    img = Image.new("RGBA", (W, H), (*bg, 255))
    dr = ImageDraw.Draw(img)
    for c, gname in enumerate(GRADES):
        dr.text((left + pad + c * (cell + pad), 10), gname.capitalize(), fill=(220, 205, 170), font=_font(14 if cell > 100 else 11, True))
    for r, fam in enumerate(FAMILIES):
        y0 = 30 + pad + r * (cell + lh + pad)
        dr.text((8, y0 + cell // 2 - 8), fam.capitalize(), fill=tuple(FAM[fam]["halo2"]), font=_font(16 if cell > 100 else 12, True))
        for c, gname in enumerate(GRADES):
            iid = f"{fam}_{gname}"
            x0 = left + pad + c * (cell + pad)
            if slot:
                dr.rectangle((x0 - 1, y0 - 1, x0 + cell, y0 + cell), fill=slot, outline=(78, 68, 54))
            p = os.path.join(src_dir, iid + suffix)
            if os.path.exists(p):
                ic = Image.open(p).convert("RGBA")
                if ic.size != (cell, cell):
                    ic = ic.resize((cell, cell), Image.LANCZOS)
                img.alpha_composite(ic, (x0, y0))
            if label:
                dr.text((x0 + 4, y0 + cell + 3), display_name(iid), fill=(200, 190, 170), font=_font(12))
    img.convert("RGB").save(path)
    print(f"[crystals] sheet {path}")


def post(ids=None):
    os.makedirs(ICON_DIR, exist_ok=True)
    os.makedirs(EVID, exist_ok=True)
    for iid in (ids or IDS):
        compose_icon(iid).save(os.path.join(ICON_DIR, iid + ".png"))
        print(f"[crystals] icon {iid}")
    contact_sheet(ICON_DIR, os.path.join(EVID, "crystal_icons_sheet.png"), 256)
    contact_sheet(ICON_DIR, os.path.join(EVID, "crystal_icons_sheet_64px.png"), 64, label=False, slot=(40, 35, 31))
    if os.path.isdir(MODEL_RAW):
        contact_sheet(MODEL_RAW, os.path.join(EVID, "crystal_models_sheet.png"), 256, bg=(58, 56, 62))


if __name__ == "__main__" and "bpy" not in sys.modules:
    args = sys.argv[1:]
    if args and args[0] == "post":
        post([a for a in args[1:] if a in IDS] or None)
