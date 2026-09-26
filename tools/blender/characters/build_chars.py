"""Character assembly: body mesh + armature + baked action library -> GLB.

Each hero module (char_<name>.py) provides:
  PROPS        skeleton proportions dict (bh_skeleton.proportions)
  EXTRA_BONES  list of (name, head, tail, parent, z_hint) optional bones (cape, hood, crystals, coat)
  PALETTE      material palette key (bh_materials.OVERRIDES)
  build(body)  adds Parts to the bh_body.Body (model space)
  secondary(anim, frames) -> per-frame dict bone -> 3x3 armature-space rotation for EXTRA_BONES (optional)
"""
import importlib
import math
import os
import time

import numpy as np

import bh_anim as A
import bh_body as B
import bh_mesh as M
import bh_materials as MT
import bh_skeleton as S

CHARACTERS = {
    "knight": "char_knight",
    # "mage": "char_mage",
}


def char_module(name):
    return importlib.import_module(CHARACTERS[name])


def build_character(name, with_actions=True, only=None, log=print, preview=False):
    """Build armature + skinned mesh (+ baked actions). Returns dict with objects and rig."""
    import bpy
    cm = char_module(name)
    t0 = time.time()
    mats = MT.make_materials(getattr(cm, "PALETTE", name), vertex_color=preview)
    extra = list(getattr(cm, "EXTRA_BONES", []))
    body = B.Body(cm.PROPS, extra_bones=extra)
    cm.build(body)
    arm_ob, J = S.build_armature(cm.PROPS, "Armature", extra=extra)
    mesh_ob = M.build_skinned(name, body.parts, arm_ob, mats, sharp_angle=40.0)
    if hasattr(cm, "finish_mesh"):
        cm.finish_mesh(mesh_ob)
    MT.bake_vertex_ao(mesh_ob)
    log(f"[{name}] mesh {M.tri_count(mesh_ob)} tris, {len(body.parts)} parts, {time.time() - t0:.1f}s")
    rig = A.Rig(cm.PROPS)
    out = dict(armature=arm_ob, mesh=mesh_ob, rig=rig, body=body, module=cm, materials=mats)
    if with_actions:
        import bh_library as L
        t1 = time.time()
        lib = L.library()
        sec = getattr(cm, "secondary", None)
        acts = {}
        for an in lib:
            if only and an.name not in only:
                continue
            acts[an.name] = A.bake_action(arm_ob, rig, an, extra=sec)
        out["actions"] = acts
        log(f"[{name}] baked {len(acts)} actions in {time.time() - t1:.1f}s")
    return out


def export_character(name, out_dir, export_fn, log=print):
    import bpy
    os.makedirs(out_dir, exist_ok=True)
    res = build_character(name, log=log)
    arm, mesh = res["armature"], res["mesh"]
    # every action becomes one NLA track (exported as one glTF animation named after the track)
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = None
    for an_name, act in res["actions"].items():   # (do not shadow `name`: that exported boss_summon.glb)
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
    path = os.path.join(out_dir, name + ".glb")
    export_fn(path, [arm, mesh])
    log(f"[{name}] -> {path} ({os.path.getsize(path) / 1e6:.1f} MB)")
    return res
