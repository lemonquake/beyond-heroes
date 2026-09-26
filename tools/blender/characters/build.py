"""Beyond Heroes character/weapon build entry point.

Usage (from anywhere):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b --factory-startup --python build.py -- [targets]
targets: all | weapons | meta | validate | <character names...>   (default: all)
  all       = weapons + every character + anim_meta.json + validation.txt
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CHAR_DIR = os.path.join(ROOT, "game", "assets", "characters")
WPN_DIR = os.path.join(ROOT, "game", "assets", "weapons")
EVID_DIR = os.path.join(ROOT, "work", "lemondev", "bh-002", "evidence", "characters")

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import bh_materials as MT  # noqa: E402
import bh_mesh as M  # noqa: E402
import bh_weapons as W  # noqa: E402


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)


def export_glb(path, objects, animations=True):
    sc = bpy.context.scene
    sc.render.fps = 30          # the glTF exporter samples at the scene rate (Blender default 24 fps)
    sc.render.fps_base = 1.0
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    # Blender < 5 (the pip `bpy` 4.4 module): the NLA_TRACKS mode names each glTF animation after track i but fills
    # it with track i+1's data (io_scene_gltf2 tracks.py resets its track list too early). ACTIONS mode exports one
    # animation per action, named after the action (= the clip name), and is correct there. check_clip_lengths()
    # verifies every export either way.
    mode = "NLA_TRACKS" if bpy.app.version >= (5, 0, 0) else "ACTIONS"
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
        export_animations=animations, export_animation_mode=mode, export_force_sampling=True,
        export_anim_single_armature=True, export_reset_pose_bones=True, export_def_bones=False,
        export_cameras=False, export_lights=False, export_skins=True, export_influence_nb=4,
        export_optimize_animation_size=False, export_frame_step=1, export_vertex_color="ACTIVE",
        export_all_vertex_colors=False, export_active_vertex_color_when_no_material=True,
        export_extras=False, export_tangents=False)


def glb_clip_lengths(path):
    """{animation name: seconds} read straight from the GLB's JSON chunk (sampler input max)."""
    import json
    import struct
    with open(path, "rb") as f:
        b = f.read()
    n = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + n])
    out = {}
    for a in j.get("animations", []):
        out[a["name"]] = max(j["accessors"][s["input"]]["max"][0] for s in a["samplers"])
    return out


def check_clip_lengths(path, expected, tol=0.05):
    """Raise if any exported clip's length differs from its authored length (catches exporter mix-ups)."""
    got = glb_clip_lengths(path)
    bad = [(k, round(got.get(k, -1), 3), round(v, 3)) for k, v in expected.items() if abs(got.get(k, -1) - v) > tol]
    if bad:
        raise RuntimeError(f"{path}: {len(bad)} clips have the wrong length (name, exported, authored): {bad[:6]}")
    return len(got)


def build_weapon(name):
    mats = MT.make_materials("knight", vertex_color=False)
    ob = M.build_static(name, W.WEAPONS[name](), mats)
    MT.bake_vertex_ao(ob, rays=16, dist=0.12, strength=0.55)
    return ob


def export_weapons(names=None, log=print):
    os.makedirs(WPN_DIR, exist_ok=True)
    report = {}
    for name in names or list(W.WEAPONS):
        reset()
        ob = build_weapon(name)
        path = os.path.join(WPN_DIR, name + ".glb")
        export_glb(path, [ob], animations=False)
        tris = M.tri_count(ob)
        zs = [(ob.matrix_world @ Vector(c)).z for c in ob.bound_box]
        report[name] = dict(tris=tris, length=round(max(zs) - min(zs), 3))
        log(f"[weapon] {name}: {tris} tris, length {max(zs) - min(zs):.3f} m -> {path}")
    return report


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    targets = argv or ["all"]
    t0 = time.time()
    import build_chars as BC
    if "all" in targets or "weapons" in targets:
        export_weapons()
    chars = [t for t in targets if t in BC.CHARACTERS]
    if "all" in targets:
        chars = list(BC.CHARACTERS)
    for c in chars:
        reset()
        BC.export_character(c, CHAR_DIR, export_glb)
    if "all" in targets or "meta" in targets or any(c in ("knight", "mage") for c in chars):
        import bh_library as L
        L.write_meta(os.path.join(CHAR_DIR, "anim_meta.json"))
    if "all" in targets or "validate" in targets:
        import validate
        validate.run(CHAR_DIR, WPN_DIR, os.path.join(EVID_DIR, "validation.txt"))
    print(f"[build] done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
