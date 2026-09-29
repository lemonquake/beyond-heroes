"""bh-022: dress a hero model in one or more boss collections (model space, textured) and render front/back views.

  blender -b --factory-startup --python tools/blender/items/boss_regalia_preview.py -- <out.png> <set>[,<set>...] [class]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import boss_regalia as R  # noqa: E402
import item_kit as K  # noqa: E402


def studio(res_x, res_y):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = res_x
    sc.render.resolution_y = res_y
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.05, 0.05, 0.065, 1)
    bg.inputs[1].default_value = 1.0
    for name, loc, e, col, size in (("Key", (-2.5, -3.5, 3.8), 900, (1.0, 0.9, 0.8), 2.5), ("Rim", (2.8, 3.0, 3.0), 1100, (0.6, 0.72, 1.0), 2.0),
                                     ("Fill", (3.2, -2.8, 1.0), 260, (0.85, 0.85, 0.95), 3.0)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.color, ld.size = e, col, size
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 1.0)) - lo.location).to_track_quat("-Z", "Y").to_euler()
    cd = bpy.data.cameras.new("C")
    cam = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cd.type = "ORTHO"
    cd.ortho_scale = 2.35
    return cam


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    out, sids = argv[0], argv[1].split(",")
    cls = argv[2] if len(argv) > 2 else None
    yaws = [int(a) for a in os.environ.get("BH_YAWS", "-28,200").split(",")]
    views = []
    for sid in sids:
        for yaw in yaws:
            views.append((sid, yaw))
    tiles = []
    tmp = os.path.join(os.path.dirname(out), "_regalia_tiles")
    os.makedirs(tmp, exist_ok=True)
    for sid, yaw in views:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        who = cls or {"knight": "knight", "ranger": "ranger", "mage": "mage", "shadowblade": "shadowblade"}[R.SETS[sid]["cls"]]
        bpy.ops.import_scene.gltf(filepath=os.path.join(R.ROOT, "game", "assets", "characters", who + ".glb"))
        for o in list(bpy.data.objects):
            if o.type == "MESH" and o.name.startswith("Icosphere"):
                bpy.data.objects.remove(o)
            elif o.type == "ARMATURE":
                o.data.pose_position = "REST"
                o.animation_data_clear()
        m = R.palette(sid)
        for slot in R.SLOTS:
            parts = R.piece_parts(sid, slot, m)
            R.objects_for("boss_%s_%s" % (sid, slot), parts, textured=True)
        cam = studio(int(os.environ.get("BH_W", "700")), int(os.environ.get("BH_H", "900")))
        cam.data.ortho_scale = float(os.environ.get("BH_ORTHO", "2.35"))
        p, y = math.radians(8), math.radians(yaw)
        d = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
        cam.location = Vector((0, 0, float(os.environ.get("BH_CZ", "1.08")))) + d * 8.0
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        path = os.path.join(tmp, "%s_%d.png" % (sid, yaw))
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        tiles.append(path)
    # contact sheet
    ims = [bpy.data.images.load(t) for t in tiles]
    w, h = ims[0].size
    cols = min(len(ims), 6)
    rows = (len(ims) + cols - 1) // cols
    sheet = bpy.data.images.new("sheet", w * cols, h * rows)
    import numpy as np
    buf = np.zeros((h * rows, w * cols, 4), np.float32)
    for i, im in enumerate(ims):
        px = np.array(im.pixels[:], np.float32).reshape(h, w, 4)
        r, c = i // cols, i % cols
        buf[(rows - 1 - r) * h:(rows - r) * h, c * w:(c + 1) * w] = px
    sheet.pixels = buf.ravel()
    sheet.filepath_raw = out
    sheet.file_format = "PNG"
    sheet.save()
    print("[preview]", out)


main()
