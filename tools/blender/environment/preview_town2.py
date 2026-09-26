"""Headless Workbench previews for environment GLBs (works with the `bpy` pip module, no GPU / display).

    python3 tools/blender/environment/preview_town2.py -- <names...> [--res 420] [--out DIR] [--col]

For every asset it re-imports game/assets/environment/<name>.glb and renders one contact sheet
<out>/<name>.png with: front (from -Y), front 3/4, back 3/4 and the high "game" camera (from the south, looking
north-down). The ground shows a 4 m grid (dark lines at multiples of 4 m, origin cross in red). Socket empties are
drawn as magenta balls and labelled. With --col a 5th tile shows the collision boxes (orange) under a wireframe.
Workbench = material colours + cavity + shadow; it checks shape, grounding, facing and sockets, not final look.
"""
import argparse
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ENV = os.path.join(ROOT, "game", "assets", "environment")
DEF_OUT = os.path.join(ROOT, "work", "lemondev", "bh-003", "evidence", "architecture")


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--room", action="store_true", help="render the kit assembled as an 8 x 8 m tavern room")
    ap.add_argument("--res", type=int, default=420)
    ap.add_argument("--out", default=DEF_OUT)
    ap.add_argument("--col", action="store_true")
    ap.add_argument("--sheet", default="", help="also write an overview grid <out>/<sheet> of all names")
    ap.add_argument("--sheet-tag", default="front34")
    ap.add_argument("--detail", action="append", default=[],
                    help="extra close-up tile: x,y,z,dist[,yaw,pitch] (Blender coords of the target)")
    return ap.parse_args(argv)


def mat(name, col):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = col
    return m


def add_box(name, size, loc, m):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0] + loc[0], v.co.y * size[1] + loc[1], v.co.z * size[2] + loc[2]))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def ground(extent):
    g = mat("_ground", (0.34, 0.35, 0.33, 1))
    ln = mat("_grid", (0.12, 0.12, 0.13, 1))
    red = mat("_origin", (0.8, 0.1, 0.1, 1))
    add_box("_G", (extent * 2, extent * 2, 0.02), (0, 0, -0.011), g)
    n = int(extent // 4)
    for i in range(-n, n + 1):
        add_box("_gx%d" % i, (0.04, extent * 2, 0.004), (i * 4.0, 0, 0.001), ln)
        add_box("_gy%d" % i, (extent * 2, 0.04, 0.004), (0, i * 4.0, 0.001), ln)
    add_box("_ox", (0.8, 0.06, 0.01), (0, 0, 0.004), red)
    add_box("_oy", (0.06, 0.8, 0.01), (0, 0, 0.004), red)
    add_box("_front", (0.06, 0.6, 0.01), (0, -0.7, 0.004), red)  # arrow stub toward -Y (front)


def material_colors():
    """Workbench shows diffuse_color: take the BH_* colour from the kit table (the glTF import feeds the base colour
    through the vertex colour, so the imported node values are not usable). Unknown names show bright green."""
    sys.path.insert(0, HERE)
    import kit
    import assets_town2  # noqa  (registers the extra BH_* names in kit.MATERIALS)
    boost = {"BH_Glass": (1.0, 0.72, 0.32), "BH_Candle": (1.0, 0.82, 0.5), "BH_Flame": (1.0, 0.5, 0.1)}
    for m in bpy.data.materials:
        if m.name.startswith("_"):
            continue
        base = m.name.split(".")[0]
        if base in boost:
            col = boost[base]
        elif base in kit.MATERIALS:
            col = kit.MATERIALS[base][0]
            col = (col[0] ** 0.6, col[1] ** 0.6, col[2] ** 0.6)  # lift dark linear colours for readability
        else:
            col = (0.0, 1.0, 0.0)
        m.diffuse_color = (col[0], col[1], col[2], 1)


def setup_render(res):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.show_shadows = True
    sh.shadow_intensity = 0.55
    if os.environ.get("BH_PREVIEW_FLAT"):
        sh.show_cavity = False
        sh.show_specular_highlight = False
    sh.show_object_outline = False
    sc.display.light_direction = (0.45, -0.55, 0.7)
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.world.color = (0.16, 0.17, 0.2)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def place(cam, target, dist, yaw, pitch, lens=45):
    y, p = math.radians(yaw), math.radians(pitch)
    t = Vector(target)
    cam.location = t + Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p))) * dist
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.clip_start = 0.05
    cam.data.clip_end = 500


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def one(name, a):
    from PIL import Image, ImageDraw
    bpy.ops.wm.read_factory_settings(use_empty=True)
    path = os.path.join(ENV, name + ".glb")
    bpy.ops.import_scene.gltf(filepath=path)
    objs = list(bpy.context.scene.objects)
    meshes = [o for o in objs if o.type == "MESH" and "-colonly" not in o.name]
    cols = [o for o in objs if o.type == "MESH" and "-colonly" in o.name]
    sockets = [o for o in objs if o.type == "EMPTY" and o.parent is not None]
    material_colors()
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    lift = 0.0
    if mn.z < -0.05:  # hanging assets (origin at the rod): lift for display only, noted on the sheet
        lift = -mn.z
        for o in objs:
            if o.parent is None:
                o.location.z += lift
        bpy.context.view_layer.update()
        mn.z += lift
        mx.z += lift
    size = mx - mn
    diag = max(size.length, 0.6)
    ctr = (mn + mx) / 2
    ground(max(8.0, math.ceil((max(size.x, size.y) / 2 + 3) / 4) * 4))
    sm = mat("_sock", (1.0, 0.1, 0.9, 1))
    for s in sockets:
        me = bpy.data.meshes.new("_s")
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=max(0.05, diag * 0.012))
        bm.to_mesh(me)
        bm.free()
        me.materials.append(sm)
        so = bpy.data.objects.new("_s_" + s.name, me)
        so.location = s.matrix_world.translation
        bpy.context.scene.collection.objects.link(so)
    for c in cols:
        c.hide_render = True
    cam = setup_render(a.res)
    tmp = os.path.join(a.out, "_tiles")
    os.makedirs(tmp, exist_ok=True)
    tgt = (ctr.x, ctr.y, ctr.z * 0.9)
    views = [("front", 0, 8), ("front34", 35, 24), ("back34", 215, 24), ("game", 0, 58)]
    tiles = []
    for tag, yaw, pitch in views:
        dist = diag * (1.55 if tag != "game" else 1.9)
        place(cam, tgt, dist, yaw, pitch)
        p = os.path.join(tmp, f"{name}_{tag}.png")
        render(p)
        tiles.append((p, tag, [(s.name, world_to_camera_view(bpy.context.scene, cam, s.matrix_world.translation))
                               for s in sockets]))
    for di, dspec in enumerate(a.detail):
        v = [float(t) for t in dspec.split(",")]
        yaw, pitch = (v[4], v[5]) if len(v) >= 6 else (25, 15)
        place(cam, v[:3], v[3], yaw, pitch)
        p = os.path.join(tmp, f"{name}_detail{di}.png")
        render(p)
        tiles.append((p, f"detail {di}", [(s.name, world_to_camera_view(bpy.context.scene, cam, s.matrix_world.translation))
                                          for s in sockets]))
    if a.col and cols:
        for c in cols:
            c.hide_render = False
            c.data.materials.clear()
            c.data.materials.append(mat("_col", (1.0, 0.45, 0.05, 1)))
        sh = bpy.context.scene.display.shading
        sh.show_xray = True
        sh.xray_alpha = 0.55
        place(cam, tgt, diag * 1.55, 35, 24)
        p = os.path.join(tmp, f"{name}_col.png")
        render(p)
        tiles.append((p, "collision", []))
    R_ = a.res
    sheet = Image.new("RGB", (len(tiles) * R_, R_ + 22), (20, 20, 24))
    d = ImageDraw.Draw(sheet)
    for i, (p, tag, labels) in enumerate(tiles):
        im = Image.open(p).convert("RGB")
        sheet.paste(im, (i * R_, 22))
        d.text((i * R_ + 6, 5), f"{name} - {tag}" + (f"  (lifted {lift:.2f} m for display)" if lift else ""),
               fill=(230, 230, 230))
        for (sn, v) in labels:
            if 0 <= v.x <= 1 and 0 <= v.y <= 1 and v.z > 0:
                x, y = i * R_ + v.x * R_, 22 + (1 - v.y) * R_
                d.text((x + 6, y - 6), sn, fill=(255, 120, 250))
    out = os.path.join(a.out, f"{name}.png")
    sheet.save(out)
    socks = ", ".join(f"{s.name}=({s.matrix_world.translation.x:.2f},{s.matrix_world.translation.y:.2f},"
                      f"{s.matrix_world.translation.z:.2f})" for s in sockets)
    print(f"PREVIEW {out}  bbox=({size.x:.2f} x {size.y:.2f} x {size.z:.2f}) min=({mn.x:.2f},{mn.y:.2f},{mn.z:.2f}) "
          f"col={len(cols)} sockets: {socks}", flush=True)


def overview(names, out, sheet_name, cols=6, tag="front34"):
    """Grid of one tile per asset (reuses the _tiles renders)."""
    from PIL import Image, ImageDraw
    tiles = [(n, os.path.join(out, "_tiles", f"{n}_{tag}.png")) for n in names]
    tiles = [(n, p) for n, p in tiles if os.path.exists(p)]
    if not tiles:
        return
    R_ = Image.open(tiles[0][1]).size[0]
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * R_, rows * (R_ + 20)), (20, 20, 24))
    d = ImageDraw.Draw(sheet)
    for i, (n, p) in enumerate(tiles):
        x, y = (i % cols) * R_, (i // cols) * (R_ + 20)
        sheet.paste(Image.open(p).convert("RGB").resize((R_, R_)), (x, y + 20))
        d.text((x + 6, y + 4), n, fill=(235, 235, 235))
    sheet.save(os.path.join(out, sheet_name))
    print("OVERVIEW", os.path.join(out, sheet_name))


def main():
    a = args()
    os.makedirs(a.out, exist_ok=True)
    for n in a.names:
        one(n, a)
    if a.sheet:
        overview(a.names, a.out, a.sheet, tag=a.sheet_tag)


if __name__ == "__main__" and "--room" not in sys.argv:
    main()


# ---------------------------------------------------------------------------------------------------------------
ROOM = [  # (glb, x, y, rot_z_deg) - an 8 x 8 m tavern room on the 4 m grid, south side cut away (low walls)
    ("int_floor_planks", -2, -2, 0), ("int_floor_planks", 2, -2, 0), ("int_floor_planks", -2, 2, 0), ("int_floor_planks", 2, 2, 0),
    ("int_wall_plaster_window", -2, 4, 0), ("int_wall_plaster", 2, 4, 0),
    ("int_wall_plaster_low", -2, -4, 180), ("int_wall_plaster_low", 2, -4, 180),
    ("int_wall_plaster", -4, -2, 90), ("int_wall_plaster_door", -4, 2, 90),
    ("int_wall_stone", 4, -2, -90), ("int_wall_stone", 4, 2, -90),
    ("fireplace", 1.6, 4 - 0.15 - 0.45, 0), ("bar_counter", -1.6, 1.3, 0), ("bar_back_shelf", -2.3, 4 - 0.15 - 0.23, 0),
    ("keg_rack", 3.0, 0.2, -90), ("table_round", 1.2, -1.2, 0), ("stool", 0.4, -1.0, 0), ("stool", 1.9, -0.6, 0),
    ("table_long", -1.6, -2.2, 0), ("bench", -1.6, -1.55, 0), ("bench", -1.6, -2.85, 0), ("hanging_lantern", 0, 0, 0),
    ("rug_round", 1.4, 1.8, 0), ("guild_banner_lantern", 3.8, -2.4, -90),
]


def room(a):
    import bpy as _b
    from PIL import Image
    _b.ops.wm.read_factory_settings(use_empty=True)
    for (n, x, y, rz) in ROOM:
        before = set(_b.context.scene.objects)
        _b.ops.import_scene.gltf(filepath=os.path.join(ENV, n + ".glb"))
        for o in set(_b.context.scene.objects) - before:
            if "-colonly" in o.name:  # later imports get ".001" suffixes
                o.hide_render = True
            if o.parent is None:
                o.location = (x, y, 2.6 if n.startswith("guild_banner") else 0.0)
                o.rotation_mode = "XYZ"
                o.rotation_euler = (0, 0, math.radians(rz))
    material_colors()
    ground(12.0)
    cam = setup_render(a.res * 2)
    tiles = []
    for tag, yaw, pitch, dist in (("game", 0, 58, 17), ("iso", 30, 40, 16)):
        place(cam, (0, 0, 0.8), dist, yaw, pitch)
        p = os.path.join(a.out, "_tiles", f"room_{tag}.png")
        render(p)
        tiles.append(p)
    R_ = a.res * 2
    sheet = Image.new("RGB", (R_ * len(tiles), R_), (20, 20, 24))
    for i, p in enumerate(tiles):
        sheet.paste(Image.open(p).convert("RGB"), (i * R_, 0))
    out = os.path.join(a.out, "room_assembly.png")
    sheet.save(out)
    print("ROOM", out)


if __name__ == "__main__" and "--room" in sys.argv:
    room(args())
