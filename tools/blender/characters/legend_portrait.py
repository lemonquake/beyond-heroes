"""bh-021: dialogue portrait of a legend rendered from its model (EEVEE, transparent film, three-point light).

  blender -b --factory-startup --python legend_portrait.py -- paul_david --out <png> [--clip idle] [--yaw 22]
Then composite with legend_portrait_bg.py (system Python) over the portraits' dark radial backdrop.
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("character")
    ap.add_argument("--out", required=True)
    ap.add_argument("--clip", default="idle")
    ap.add_argument("--yaw", type=float, default=22.0)
    ap.add_argument("--target", type=float, default=1.62)
    ap.add_argument("--dist", type=float, default=1.25)
    ap.add_argument("--rim", default="0.4,0.7,1.0")
    a = ap.parse_args(argv)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import build_chars as BC
    import legend_preview as LP
    import bh_render as R
    res = BC.build_character(a.character, with_actions=True, only={a.clip})
    arm = res["armature"]
    act = res["actions"].get(a.clip)
    if act:
        ad = arm.animation_data or arm.animation_data_create()
        ad.action = act
        try:
            if ad.action_slot is None and len(act.slots):
                ad.action_slot = act.slots[0]
        except Exception:
            pass
        bpy.context.scene.frame_set(0)
    LP.texture_materials()
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = 768
    sc.render.resolution_y = 768
    sc.render.film_transparent = True
    try:
        sc.eevee.taa_render_samples = 64
    except Exception:
        pass
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = -0.6
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.025, 0.04, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.4
    t = Vector((0, 0, a.target))
    rim = tuple(float(x) for x in a.rim.split(","))
    for name, loc, energy, color, size in (
            ("Key", (-1.6, -2.4, 2.4), 260, (1.0, 0.86, 0.72), 1.2),
            ("Rim", (1.8, 1.6, 2.3), 520, rim, 0.8),
            ("Rim2", (-1.5, 1.8, 2.0), 180, rim, 0.8),
            ("Fill", (2.2, -2.0, 1.4), 60, (0.7, 0.75, 0.9), 2.0)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = energy
        ld.color = color
        ld.size = size
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        R.look_at(lo, t)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    R.place_camera(cam, t, a.dist, a.yaw, 4, lens=58)
    R.render(a.out)
    print("PORTRAIT", a.out)


if __name__ == "__main__":
    main()
