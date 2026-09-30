"""bh-023: extra checks for the worn armour and inner garments (hero_wear_torso.py).

  blender -b --factory-startup --python tools/blender/hero/hero_wear_torso_check.py -- poses <outfit> ...
        more animation poses than `hero_wear.py -- preview` (idle, walk, run x2, dodge, pickup, block, death ...)
  ... -- keys <outfit> ...
        the outfit on the body with each build slider pushed (muscle, belly, build, rear, and a thin body)
  ... -- close <outfit> ...
        close-ups of the rest pose (chest, hips, arm) as the character creator shows them
  ... -- count [ids]
        triangles and materials of each piece (no files written)

An outfit is "a+b+c" (pieces worn together). Renders go to work/lemondev/bh-023/scratch/wear/<outfit>_<tag>.png.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hero_wear as HW  # noqa: E402
import hero_wear_kit as WK  # noqa: E402

OUT = os.path.join(WK.SCRATCH, "wear")
POSES = (("idle", 0.0), ("walk", 0.25), ("run", 0.2), ("run", 0.7), ("sword_2", 0.5), ("cast_heavy", 0.5),
         ("dodge_roll", 0.5), ("interact_pickup", 0.5), ("block_loop", 0.5), ("bow_draw_hold", 0.5), ("death", 0.95),
         ("cs_aj_kneel", 0.6))
KEYS = (("muscle", 1.5), ("belly", 2.2), ("build", 2.0), ("rear", 2.5), ("thin", None))
THIN = {"muscle": -1.0, "belly": -0.6, "build": -1.0, "rear": -0.5}


def _setup():
    import hero_body as HB
    r = HB.build_body()
    HB._preview_material(r["ob"])
    return r, HB._stage()


def _rest(arm):
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)


def _wear(r, outfit):
    import bpy
    ids = outfit.split("+")
    obs = []
    for i in ids:
        obs += WK.build_item(i, r["arm"])
    HW._hide_body(r["ob"], r["V"], ids)
    return obs, outfit.replace("+", "__")


def poses(outfits):
    import bpy
    import bh_anim as A
    import bh_library as L
    r, shot = _setup()
    arm, rig = r["arm"], r["rig"]
    lib = {a.name: a for a in L.library()}
    acts = {}
    for outfit in outfits:
        obs, tag = _wear(r, outfit)
        for k, (c, f) in enumerate(POSES):
            if c not in acts:
                acts[c] = A.bake_action(arm, rig, lib[c])
            A.assign_action(arm, acts[c])
            bpy.context.scene.frame_set(int(round(lib[c].length * f)))
            shot(os.path.join(OUT, "%s_p%02d.png" % (tag, k)), (3.2, -5.0, 1.5), (0, 0, 0.9), 2.3, (640, 760))
        _rest(arm)
        for o in obs:
            bpy.data.objects.remove(o)
        print("[check] poses", outfit)


def keys(outfits):
    import bpy
    r, shot = _setup()
    body = r["ob"]
    b = WK.body()
    same = len(b.V) == len(r["V"]) and float(np.abs(b.V - r["V"]).max()) < 1e-4
    print("[check] body of the preview == hero_mesh.npz:", same)
    body.shape_key_add(name="Basis")
    for ki, kn in enumerate(WK.SH.BODY_KEYS):
        kb = body.shape_key_add(name=kn)
        kb.data.foreach_set("co", (r["V"] + b.D[ki]).ravel())
        kb.slider_min, kb.slider_max = -3.0, 6.0
        kb.value = 0.0
    for outfit in outfits:
        obs, tag = _wear(r, outfit)
        for kn, val in KEYS:
            vals = THIN if val is None else {kn: val}
            for o in [body] + obs:
                for kb in o.data.shape_keys.key_blocks[1:]:
                    kb.value = vals.get(kb.name, 0.0)
            shot(os.path.join(OUT, "%s_k_%s_front.png" % (tag, kn)), (0, -6, 1.0), (0, 0, 1.0), 1.75, (620, 800))
            shot(os.path.join(OUT, "%s_k_%s_side.png" % (tag, kn)), (6, -0.5, 1.0), (0, 0, 1.0), 1.75, (440, 800))
        for kb in body.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
        for o in obs:
            bpy.data.objects.remove(o)
        print("[check] keys", outfit)


def close(outfits):
    import bpy
    r, shot = _setup()
    for outfit in outfits:
        obs, tag = _wear(r, outfit)
        shot(os.path.join(OUT, tag + "_c_chest.png"), (1.5, -5.0, 1.75), (0, 0, 1.3), 0.78, (760, 760))
        shot(os.path.join(OUT, tag + "_c_hips.png"), (1.5, -5.0, 1.2), (0, 0, 0.85), 0.9, (760, 760))
        shot(os.path.join(OUT, tag + "_c_back.png"), (-1.5, 5.0, 1.7), (0, 0, 1.2), 1.0, (760, 760))
        shot(os.path.join(OUT, tag + "_c_arm.png"), (1.2, -4.0, 2.2), (0.48, 0, 1.42), 0.62, (760, 560))
        shot(os.path.join(OUT, tag + "_c_legs.png"), (2.0, -5.0, 0.8), (0, 0, 0.42), 0.95, (760, 760))
        for o in obs:
            bpy.data.objects.remove(o)
        print("[check] close", outfit)


def count(ids):
    import bpy
    import bh_skeleton as S
    import hero_conform as HC
    bad = 0
    for i in ids:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        arm, _ = S.build_armature(HC.PROPS, "Armature")
        obs = WK.build_item(i, arm)
        tris = sum(WK.tri_count(o) for o in obs)
        mats = sorted({m.name for o in obs for m in o.data.materials})
        keys_ok = all([kb.name for kb in o.data.shape_keys.key_blocks[1:]] == list(WK.SH.BODY_KEYS) for o in obs)
        spec = HW.WK.REGISTRY[i]
        print("[count] %-26s %5d tris  %d materials  keys=%s  hide=%s  %s" % (i, tris, len(mats), keys_ok, spec["hide"],
                                                                        ", ".join(m.split("__it_hw_")[-1] for m in mats)))
        bad += tris > 7000 or len(mats) > 5
    print("[count] over budget:", bad)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    os.makedirs(OUT, exist_ok=True)
    mode, rest = (argv[0], argv[1:]) if argv else ("count", [])
    if mode == "poses":
        poses(rest)
    elif mode == "keys":
        keys(rest)
    elif mode == "close":
        close(rest)
    else:
        import hero_wear_torso as T  # noqa: F401
        mine = [i for i, s in WK.REGISTRY.items() if s["fn"].__module__ == "hero_wear_torso"]
        count(rest or mine)


if __name__ == "__main__":
    main()
