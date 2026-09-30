"""bh-023: hero.glb = the conformed body + shape keys + shader attributes + every library clip + the source clips.

Also writes hero_meta.json (timing of the five source clips, anim_meta.json schema) and the mesh data the other hero
tools read (work/lemondev/bh-023/scratch/hero_mesh.npz: hero_skin.py, hero_wear.py, hero_hair.py).
"""
import json
import os
import time

import numpy as np

import bpy

import bh_anim as A
import bh_skeleton as S
import hero_body as HB
import hero_retarget as RT
import hero_shapes as SH


def export_glb(path, objects):
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.render.fps_base = 1.0
    for o in sc.objects:
        o.select_set(False)
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    # export_apply stays off: applying modifiers would drop the shape keys
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
        export_animations=True, export_animation_mode="NLA_TRACKS", export_force_sampling=True,
        export_anim_single_armature=True, export_reset_pose_bones=True, export_def_bones=False,
        export_cameras=False, export_lights=False, export_skins=True, export_influence_nb=4,
        export_optimize_animation_size=False, export_frame_step=1, export_vertex_color="ACTIVE",
        export_all_vertex_colors=False, export_active_vertex_color_when_no_material=True,
        export_extras=False, export_tangents=False, export_morph=True, export_morph_normal=True,
        export_morph_animation=False, export_texcoords=True, export_normals=True)


def skin_material():
    """One material; the game replaces it by name with the hero skin shader (HeroLook)."""
    m = bpy.data.materials.new("BH_HeroSkin")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.62, 0.42, 0.32, 1.0)
    b.inputs["Roughness"].default_value = 0.62
    return m


def add_attributes(ob, V):
    uv2, col = SH.shader_attributes(V)
    me = ob.data
    l2 = me.uv_layers.new(name="UV2")
    vi = np.zeros(len(me.loops), int)
    me.loops.foreach_get("vertex_index", vi)
    l2.data.foreach_set("uv", uv2[vi].ravel())
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    ca.data.foreach_set("color", col.ravel())
    me.color_attributes.active_color = ca
    me.color_attributes.render_color_index = me.color_attributes.find("Col")


def export(argv, log=print):
    import bh_library as L
    t0 = time.time()
    only = None
    for a in argv:
        if a.startswith("--clips="):
            only = set(a.split("=", 1)[1].split(","))
    r = HB.build_body(log)
    ob, arm, rig, V, src = r["ob"], r["arm"], r["rig"], r["V"], r["src"]
    keys = HB.add_shapes(ob, V, src["T"])
    add_attributes(ob, V)
    ob.data.materials.append(skin_material())
    os.makedirs(HB.SCRATCH, exist_ok=True)
    np.savez(os.path.join(HB.SCRATCH, "hero_mesh.npz"), V=V, T=src["T"], UV=src["UV"],
             N=SH.vertex_normals(V, src["T"]), bones=np.array(list(r["W"])), W=np.stack([r["W"][b] for b in r["W"]], 1),
             keys=np.array(list(keys)), deltas=np.stack([keys[k] for k in keys], 0))
    acts = {}
    for an in L.library():
        if an.name.startswith("cs_") or (only and an.name not in only):
            continue
        acts[an.name] = A.bake_action(arm, rig, an)
    log("[hero] baked %d library actions, %.1fs" % (len(acts), time.time() - t0))
    meta = {}
    for name, (src_action, loop) in RT.CLIPS.items():
        if only and name not in only:
            continue
        rt = RT.retarget(RT.sample(src_action), r["info"], loop)
        if name == "hero_axe_smash":
            # the two-handed smash stands in for the great axe's heavy attack (gs_heavy): same length, same strike
            # moment, so damage timing, combo windows and balance are untouched
            ref = L.measure(next(a for a in L.library() if a.name == "gs_heavy"))
            own = RT.measure(rt, loop, hit=True)
            src_hit = int(round(sum(own["hits"][0]) / 2 * 30))
            dst_len = int(round(ref["length"] * 30))
            dst_hit = int(round(sum(ref["hits"][0]) / 2 * 30))
            rt = RT.retime(rt, src_hit, dst_len, dst_hit)
            rt["pos"] = RT.fk(rt["W"], rt["t"], r["info"]["J"])
            acts[name] = RT.bake(arm, name, rt, loop)
            meta[name] = dict(ref)
            meta[name]["source_strike"] = own["hits"][0]
            log("[hero] %s <- %s retimed to gs_heavy: %s" % (name, src_action, meta[name]))
            continue
        acts[name] = RT.bake(arm, name, rt, loop)
        meta[name] = RT.measure(rt, loop, hit=False)
        log("[hero] %s <- %s: %s" % (name, src_action, meta[name]))
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = None
    for an_name, act in acts.items():
        tr = ad.nla_tracks.new()
        tr.name = an_name
        st = tr.strips.new(an_name, 0, act)
        try:
            st.action_slot = act.slots[0]
        except Exception:
            pass
        st.extrapolation = "NOTHING"
        tr.mute = False
    for pb in arm.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    for kb in ob.data.shape_keys.key_blocks:
        kb.value = 0.0
    path = os.path.join(HB.OUT_DIR, "hero.glb")
    export_glb(path, [arm, ob])
    import build as _B
    n = _B.check_clip_lengths(path, {k: (a.frame_range[1] - a.frame_range[0]) / 30.0 for k, a in acts.items()})
    with open(os.path.join(HB.OUT_DIR, "hero_meta.json"), "w") as f:
        json.dump({"fps": 30, "generator": "tools/blender/hero/hero_export.py",
                   "notes": "the player's own clips (models/generic_body_animation) on the shared skeleton",
                   "landmarks": {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in SH.LANDMARKS.items()},
                   "shape_keys": list(keys), "animations": meta}, f, indent=1)
    log("[hero] %d clips verified -> %s (%.1f MB), %.1fs" % (n, path, os.path.getsize(path) / 1e6, time.time() - t0))
