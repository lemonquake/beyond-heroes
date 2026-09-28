"""bh-013 Builder D kit: shared helpers for the static node models (hive_drone, gloomwraith, prism_sentinel,
void_rift, hive_nest). Conventions follow build_wisp.py / build_ice_wraith.py: meters, Blender Z-up (glTF Y-up),
creature faces -Y (= Godot +Z), creature's left is +X, all meshes, no armature, no clips (the game animates nodes).
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHAR = os.path.join(HERE, "..", "characters")
for _p in (CHAR, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

import numpy as np  # noqa: E402
import bpy  # noqa: E402

import bh_mesh as M  # noqa: E402
import bh_materials as MT  # noqa: E402
from bh_math import Rx, Ry, Rz, R_axis, normalize  # noqa: E402,F401


def P(V, F, mat, name="part"):
    return M.Part(V, F, mat, name=name)


def align_z(d, up_hint=(0, 0, 1)):
    """Rotation matrix whose +Z maps onto d."""
    z = normalize(d)
    x = np.asarray(up_hint, float)
    x = x - z * np.dot(x, z)
    if np.linalg.norm(x) < 1e-6:
        x = np.array([1.0, 0, 0]) - z * z[0]
    x = normalize(x)
    y = np.cross(z, x)
    return np.stack([x, y, z], 1)


def place(p, d, pos, up_hint=(0, 0, 1)):
    p.V = p.V @ align_z(d, up_hint).T + np.asarray(pos, float)
    return p


def orient(p, center, inward=False):
    """Flip faces so they face away from (or toward) center."""
    F = []
    c0 = np.asarray(center, float)
    for f in p.F:
        a, b, c = p.V[f[0]], p.V[f[1]], p.V[f[2]]
        n = np.cross(b - a, c - a)
        out = np.dot(n, p.V[list(f)].mean(0) - c0) >= 0
        F.append(f if out != inward else tuple(reversed(f)))
    p.F = F
    return p


def rag(u, seed, amp, teeth=5):
    v = 0.5 + 0.5 * math.sin(u * math.pi * 2 * teeth + seed) * math.cos(u * math.pi * 3.3 + 1.7 * seed)
    tooth = abs(((u * teeth * 2.0 + seed * 0.37) % 2.0) - 1.0)
    return amp * (0.55 * v + 0.45 * tooth)


def blob(c, s, mat, n=12, rings=8, name="blob"):
    V, F = M.sphere(1.0, n, rings, center=c, scale=s)
    return P(V, F, mat, name)


def shard(length, radius, sides=5, mat="BH_Stone", seed=0, jitter=0.3, name="shard"):
    """Irregular crystal / obsidian splinter along +Z (long tip up), roughly centred on its widest point."""
    rng = np.random.default_rng(seed)
    V, F = M.lathe([(0, -length * 0.3), (radius, 0.0), (radius * 0.6, length * 0.35), (0, length * 0.7)], sides,
                   a0=float(rng.random() * 60))
    V[:, :2] *= (1.0 + jitter * (rng.random(len(V)) - 0.5))[:, None]
    V[:, 2] += jitter * 0.15 * length * (rng.random(len(V)) - 0.5)
    return P(V, F, mat, name)


def sheet(fn, nu, nv, mat, thick, name="sheet", offset=0.0, closed_u=False):
    V, F = M.grid(fn, nu, nv, closed_u=closed_u)
    return M.solidify(P(V, F, mat, name), thick, offset=offset)


def node(name, parts, mats, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, sharp=35.0, ao=(12, 0.15, 0.4)):
    """One static mesh node; parts are in the node's LOCAL space, rot in degrees (XYZ euler)."""
    ob = M.build_static(name, parts, mats, sharp_angle=sharp)
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = tuple(math.radians(a) for a in rot)
    ob.location = loc
    if parent is not None:
        ob.parent = parent
    if ao:
        MT.bake_vertex_ao(ob, rays=ao[0], dist=ao[1], strength=ao[2])
    return ob


def world_bbox(obs):
    bpy.context.view_layer.update()
    pts = []
    for ob in obs:
        mw = ob.matrix_world
        pts.extend((mw @ v.co)[:] for v in ob.data.vertices)
    a = np.array(pts)
    return a.min(0), a.max(0)


# ------------------------------------------------------------------------------------------------ preview
def _render(path, res):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def _game_cam(cam, c, dist, yaw=0.0, pitch=54.0):
    from mathutils import Vector
    y, p = math.radians(yaw), math.radians(pitch)
    c = Vector(c)
    cam.location = c + Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p))) * dist
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle_y = math.radians(40)
    cam.data.clip_end = 200


def preview(cid, out_dir, ground_z, look=(0, 0, 0), dist=4.4, close=None, game_look=(0, 0, 0)):
    """Workbench tiles + two manifests (<cid>_views.json, <cid>_iso.json) for tools/ev_compose.py.
    close = (target, dist, yaw, pitch) for a close-up tile."""
    import preview_enemy as PE
    PE.material_colors()
    cam = PE.setup(400)
    g = bpy.data.objects["Ground"]
    g.location.z = ground_z
    g.scale = (2.0, 2.0, 1.0)
    tiles = os.path.join(out_dir, "_tiles_" + cid)
    os.makedirs(tiles, exist_ok=True)
    row1, row2 = [], []
    for v, pitch in ((0, 6), (60, 22), (150, 10), (270, 6)):
        PE.place(cam, look, dist, v, pitch)
        cam.data.sensor_fit = "AUTO"
        p = os.path.join(tiles, f"v{v}_{pitch}.png")
        _render(p, (400, 400))
        row1.append(dict(path=p, label=f"yaw {v} pitch {pitch}"))
    PE.place(cam, look, dist, 30, 62)
    p = os.path.join(tiles, "top.png")
    _render(p, (400, 400))
    row2.append(dict(path=p, label="yaw 30 pitch 62 (from above)"))
    if close:
        PE.place(cam, close[0], close[1], close[2], close[3])
        p = os.path.join(tiles, "close.png")
        _render(p, (400, 400))
        row2.append(dict(path=p, label="close-up"))
    views = os.path.join(out_dir, f"{cid}_views.json")
    with open(views, "w") as f:
        json.dump(dict(character=cid, res=400, rows=[row1, row2]), f, indent=1)
    rows = [[], []]
    for yaw, dist_ in ((0, 16), (0, 22), (180, 16)):
        _game_cam(cam, game_look, dist_, yaw)
        p = os.path.join(tiles, f"game_{yaw}_{dist_}.png")
        _render(p, (1920, 1080))
        rows[0].append(dict(path=p, label=f"game cam 54deg {dist_} m yaw {yaw} (1:1)", crop=[780, 360, 1140, 720]))
    rows[1].append(dict(path=os.path.join(tiles, "game_0_16.png"), label="game cam 16 m, 2x zoom",
                        crop=[870, 450, 1050, 630], smooth=True))
    rows[1].append(dict(path=os.path.join(tiles, "game_180_16.png"), label="game cam 16 m back, 2x zoom",
                        crop=[870, 450, 1050, 630], smooth=True))
    _game_cam(cam, game_look, 7.0, 35)
    p = os.path.join(tiles, "game_35_7.png")
    _render(p, (1920, 1080))
    rows[1].append(dict(path=p, label="54deg pitch, 7 m, yaw 35", crop=[510, 90, 1410, 990], smooth=True))
    iso = os.path.join(out_dir, f"{cid}_iso.json")
    with open(iso, "w") as f:
        json.dump(dict(character=cid, res=400, rows=rows), f, indent=1)
    print("MANIFEST", views, iso)


def run(cid, build_fn, preview_kw=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "game", "assets", "characters", cid + ".glb"))
    ap.add_argument("--preview", default="")
    ap.add_argument("--no-export", action="store_true")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    obs = build_fn()
    for ob in obs:
        print(f"[{cid}] {ob.name}: {M.tri_count(ob)} tris, parent={ob.parent.name if ob.parent else '-'}, "
              f"loc={tuple(round(x, 3) for x in ob.location)}, "
              f"rot_deg={tuple(round(math.degrees(x), 1) for x in ob.rotation_euler)}")
    print(f"[{cid}] total {sum(M.tri_count(o) for o in obs)} tris")
    lo, hi = world_bbox(obs)
    print(f"[{cid}] bbox min {np.round(lo, 3).tolist()} max {np.round(hi, 3).tolist()} size {np.round(hi - lo, 3).tolist()}")
    if not a.no_export:
        import build as BLD
        BLD.export_glb(a.out, obs, animations=False)
        print(f"[{cid}] ->", a.out)
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        preview(cid, a.preview, **(preview_kw or {}))
