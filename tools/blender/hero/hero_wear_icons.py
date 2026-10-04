"""Inventory icons of worn pieces, rendered from their worn models: the piece alone (the body hidden) in the hero's idle
pose, three-quarter front view, transparent background, 128 px -> game/assets/ui/icons/items3d/<id>.png (the same
folder and size as the other rendered item icons).

  blender -b --factory-startup --python tools/blender/hero/hero_wear_icons.py -- <ids>
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hero_wear  # noqa: E402,F401  (registers every piece)
import hero_wear_kit as WK  # noqa: E402

OUT = os.path.join(WK.ROOT, "game", "assets", "ui", "icons", "items3d")
SIZE = 128


def main():
    import bpy
    from mathutils import Vector
    import bh_anim as A
    import bh_library as L
    import hero_body as HB
    ids = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    r = HB.build_body()
    body, arm, rig = r["ob"], r["arm"], r["rig"]
    body.hide_render = True
    lib = {a.name: a for a in L.library()}
    act = A.bake_action(arm, rig, lib["idle"])
    A.assign_action(arm, act)
    bpy.context.scene.frame_set(1)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = SIZE * 4
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.32, 0.33, 0.37, 1)
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    for name, energy, rot in (("key", 3.2, (50, 0, 35)), ("fill", 1.2, (60, 0, -60)), ("rim", 2.0, (110, 0, 180))):
        lt = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
        sc.collection.objects.link(lt)
        lt.data.energy = energy
        lt.rotation_euler = tuple(math.radians(a) for a in rot)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"
    os.makedirs(OUT, exist_ok=True)
    for i in ids:
        obs = WK.build_item(i, arm)
        bpy.context.view_layer.update()
        # frame what was built: its posed bounds
        pts = []
        dg = bpy.context.evaluated_depsgraph_get()
        for o in obs:
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            pts += [ev.matrix_world @ v.co for v in me.vertices]
            ev.to_mesh_clear()
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        c = (lo + hi) / 2
        size = max(hi.x - lo.x, hi.z - lo.z) * 1.08
        loc = c + Vector((1.6, -4.0, 0.9))
        cam.location = loc
        cam.rotation_euler = (c - loc).to_track_quat("-Z", "Y").to_euler()
        cam.data.ortho_scale = size
        big = os.path.join(OUT, "_%s_big.png" % i)
        sc.render.filepath = big
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(big)
        img.scale(SIZE, SIZE)
        img.filepath_raw = os.path.join(OUT, i + ".png")
        img.file_format = "PNG"
        img.save()
        bpy.data.images.remove(img)
        os.remove(big)
        for o in obs:
            bpy.data.objects.remove(o)
        print("[icon]", i)


main()
