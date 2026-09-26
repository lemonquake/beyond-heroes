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
    "mage": "char_mage",
}

# Enemies and townsfolk (run bh-003): one module per character, `enemy_<id>.py` / `town_<id>.py`, discovered
# automatically (the GLB is named <id>.glb).
import glob as _glob
for _f in sorted(_glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "*_*.py"))):
    _b = os.path.basename(_f)[:-3]
    for _pre in ("enemy_", "town_"):
        if _b.startswith(_pre):
            CHARACTERS[_b[len(_pre):]] = _b

# Clips every enemy exports (locomotion, reactions, deaths). Enemy modules add their own attacks via CLIPS.
# Townsfolk modules set CLIPS_ONLY (idles, walk, talk) instead to skip the combat set.
ENEMY_BASE_CLIPS = (
    "idle idle_look idle_hurt idle_1h idle_shield idle_2h idle_dagger idle_bow idle_staff idle_spear "
    "walk run walk_back strafe_l strafe_r run_combat walk_hurt run_hurt "
    "hit_light hit_heavy hit_front hit_back hit_left hit_right stagger_small stagger_heavy knockback launch wall_impact "
    "knockdown getup death death_back death_fwd death_crumple revive charge_hold cast_channel alert taunt "
    "block_loop block_impact"
).split()


def clip_filter(cm):
    """None = export the whole library (heroes). Enemy modules list their attack clips in CLIPS."""
    only = getattr(cm, "CLIPS_ONLY", None)
    if only is not None:
        return set(only)
    extra = getattr(cm, "CLIPS", None)
    if extra is None:
        return None
    return set(ENEMY_BASE_CLIPS) | set(extra)


def char_module(name):
    return importlib.import_module(CHARACTERS[name])


def build_character(name, with_actions=True, only=None, log=print, preview=False):
    """Build armature + skinned mesh (+ baked actions). Returns dict with objects and rig."""
    import bpy
    cm = char_module(name)
    t0 = time.time()
    mats = MT.make_materials(getattr(cm, "PALETTE", name), vertex_color=preview,
                             extra=getattr(cm, "PALETTE_COLORS", None),
                             tintable=getattr(cm, "TINTABLE", ()))
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
        keep = clip_filter(cm)
        for an in lib:
            if only and an.name not in only:
                continue
            if keep is not None and an.name not in keep:
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
