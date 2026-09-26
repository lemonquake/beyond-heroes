"""GLB export used by Builder C's scripts.

Why not build.export_glb as-is: the glTF exporter bundled with the `bpy` 4.4 pip module has an off-by-one bug in
NLA_TRACKS mode (io_scene_gltf2/blender/exp/animation/tracks.py, __get_nla_tracks_obj: `current_exported_tracks`
is reset *before* the TrackData is built from it, so every animation gets the NAME of track i but the DATA / frame
range of track i+1, and the first track's data is lost). Blender 5.2 is not affected (knight.glb is correct).
ACTIONS mode exports one glTF animation per action, named after the action, which is what we want anyway.
"""
import bpy


def export_glb(path, objects, animations=True):
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.render.fps_base = 1.0
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
        export_animations=animations, export_animation_mode="ACTIONS", export_force_sampling=True,
        export_anim_single_armature=True, export_reset_pose_bones=True, export_def_bones=False,
        export_cameras=False, export_lights=False, export_skins=True, export_influence_nb=4,
        export_optimize_animation_size=False, export_frame_step=1, export_vertex_color="ACTIVE",
        export_all_vertex_colors=False, export_active_vertex_color_when_no_material=True,
        export_extras=False, export_tangents=False)


def check_lengths(path, expected, tol=0.02):
    """expected: {name: seconds}. Returns list of (name, got, want) mismatches (reads the GLB JSON directly)."""
    import json
    import struct
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + n])
    acc = j["accessors"]
    got = {a["name"]: max(acc[s["input"]]["max"][0] for s in a["samplers"]) for a in j.get("animations", [])}
    bad = [(k, got.get(k), v) for k, v in expected.items() if got.get(k) is None or abs(got[k] - v) > tol]
    return bad, got
