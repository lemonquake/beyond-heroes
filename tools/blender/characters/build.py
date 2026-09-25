"""Beyond Heroes character/weapon build entry point.

Usage (from anywhere):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b --factory-startup --python build.py -- [targets]
targets: all | weapons | meta | <character names...>   (default: all)
"""
import os
import sys
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CHAR_DIR = os.path.join(ROOT, "game", "assets", "characters")
WPN_DIR = os.path.join(ROOT, "game", "assets", "weapons")

import bpy  # noqa: E402
import bh_mesh as M  # noqa: E402
import bh_materials as MT  # noqa: E402
import bh_weapons as W  # noqa: E402


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)


def export_glb(path, objects):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
        export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True,
        export_anim_single_armature=True, export_reset_pose_bones=True, export_def_bones=False,
        export_cameras=False, export_lights=False, export_skins=True, export_influence_nb=4,
        export_optimize_animation_size=False, export_frame_step=1)


def build_weapon(name):
    mats = MT.make_materials("knight")
    parts = W.WEAPONS[name]()
    ob = M.build_static(name, parts, mats)
    return ob


def export_weapons(names=None):
    os.makedirs(WPN_DIR, exist_ok=True)
    report = {}
    for name in names or list(W.WEAPONS):
        reset()
        ob = build_weapon(name)
        path = os.path.join(WPN_DIR, name + ".glb")
        export_glb(path, [ob])
        tris = M.tri_count(ob)
        bb = [ob.matrix_world @ __import__("mathutils").Vector(c) for c in ob.bound_box]
        zs = [v.z for v in bb]
        report[name] = dict(tris=tris, length=round(max(zs) - min(zs), 3))
        print(f"[weapon] {name}: {tris} tris, length {max(zs) - min(zs):.3f} m -> {path}")
    return report


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    targets = argv or ["all"]
    t0 = time.time()
    if "all" in targets or "weapons" in targets:
        export_weapons()
    import build_chars as BC
    chars = [t for t in targets if t in BC.CHARACTERS]
    if "all" in targets:
        chars = list(BC.CHARACTERS)
    for c in chars:
        reset()
        BC.export_character(c, CHAR_DIR, export_glb)
    if "all" in targets or "meta" in targets or chars:
        import bh_library as L
        L.write_meta(os.path.join(CHAR_DIR, "anim_meta.json"))
    print(f"[build] done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
