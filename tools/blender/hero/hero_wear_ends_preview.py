"""bh-023: close-up previews of the hero's helms, gloves, boots and jewellery (hero_wear_ends.py).

  blender -b --factory-startup --python tools/blender/hero/hero_wear_ends_preview.py -- <kind> <outfit> [<outfit> ...]

kind: head | hand | foot | neck | hip | fist    outfit: "a+b+c" (pieces worn together), "none" = the bare body
Renders the rest pose from several sides and the library poses (camera on the bone the piece follows), with the
covered skin hidden as the game does -> work/lemondev/bh-023/scratch/wear/cu_<kind>_<outfit>_<nn>_<view>.png
(hero_wear.py -- preview gives the whole figure; these are the same outfits seen from close by.)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import hero_wear as HW  # noqa: E402  (registers every piece)
import hero_wear_kit as WK  # noqa: E402

# kind -> (target, ortho scale, [(view name, camera offset from the target)], bone the posed camera follows)
KINDS = {
    "head": ((0.0, -0.03, 1.665), 0.66, [("front", (0, -6, 0.1)), ("q", (2.6, -4.6, 1.1)), ("side", (6, 0, 0.1)), ("back", (0, 6, 0.4)),
                                         ("qback", (-3.0, 4.6, 1.6)), ("top", (0.0, -2.2, 5.5)), ("low", (1.6, -5.0, -2.2))], "head", 0.10),
    "hand": ((0.72, -0.01, 1.45), 0.40, [("top", (0.0, -0.4, 6)), ("front", (0, -6, 0.6)), ("q", (2.5, -4.0, 3.0)), ("end", (6, -1.5, 1.2)),
                                         ("below", (0.3, -2.0, -5)), ("back", (0.4, 6, 1.5))], "hand.L", 0.0),
    "fist": ((0.80, -0.015, 1.43), 0.20, [("top", (0.0, -0.2, 6)), ("front", (0, -6, 0.3)), ("q", (2.5, -4.0, 3.0)), ("end", (6, -0.4, 0.4)),
                                          ("below", (0.3, -1.0, -5)), ("back", (0.4, 6, 1.5))], "hand.L", 0.0),
    "foot": ((0.13, -0.04, 0.20), 0.62, [("front", (0.4, -6, 0.5)), ("q", (3.2, -4.6, 2.0)), ("side", (6, -0.3, 0.3)), ("back", (1.0, 6, 0.8)),
                                         ("top", (0.4, -1.6, 6))], "shin.L", -0.10),
    "neck": ((0.0, -0.05, 1.44), 0.62, [("front", (0, -6, 0.4)), ("q", (2.6, -4.6, 1.2)), ("side", (6, -0.5, 0.2)), ("back", (0.0, 6, 1.0)),
                                        ("top", (0.0, -3.0, 5.0))], "chest", 0.12),
    "hip": ((0.12, -0.03, 0.96), 0.56, [("front", (0, -6, 0.4)), ("q", (3.0, -4.6, 1.2)), ("side", (6, -0.5, 0.2)), ("back", (1.5, 6, 0.6))],
            "hips", 0.0),
}
POSED = [(0.55, -0.80, 0.30), (0.30, 0.85, 0.45)]        # posed shots: from the front-left and from behind


def closeups(kind, outfits, clips=("run", "sword_2", "cast_heavy"), res=460):
    import bpy
    from mathutils import Vector
    import bh_anim as A
    import bh_library as L
    import hero_body as HB
    target, scale, views, bone, lift = KINDS[kind]
    r = HB.build_body()
    body, arm, rig = r["ob"], r["arm"], r["rig"]
    HB._preview_material(body)
    shot = HB._stage()
    out = os.path.join(WK.SCRATCH, "wear")
    os.makedirs(out, exist_ok=True)
    lib = {a.name: a for a in L.library()}
    acts = {c: A.bake_action(arm, rig, lib[c]) for c in clips}
    for outfit in outfits:
        ids = [i for i in outfit.split("+") if i != "none"]
        obs = []
        for i in ids:
            obs += WK.build_item(i, arm)
        HW._hide_body(body, r["V"], ids)
        if arm.animation_data:
            arm.animation_data.action = None
        for pb in arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.location = (0, 0, 0)
        tag = "cu_%s_%s" % (kind, outfit.replace("+", "__"))
        n = 0
        t = Vector(target)
        for name, off in views:
            shot(os.path.join(out, "%s_%02d_%s.png" % (tag, n, name)), tuple(t + Vector(off)), tuple(t), scale, (res, res))
            n += 1
        for c in clips:
            A.assign_action(arm, acts[c])
            for frac in (0.3, 0.6):
                bpy.context.scene.frame_set(int(lib[c].length * frac))
                bpy.context.view_layer.update()
                pb = arm.pose.bones[bone]
                p = arm.matrix_world @ ((pb.head + pb.tail) * 0.5) + Vector((0, 0, lift))
                d = Vector(POSED[n % 2])
                shot(os.path.join(out, "%s_%02d_%s.png" % (tag, n, c)), tuple(p + d * 5.0), tuple(p), scale * 1.15, (res, res))
                n += 1
        for o in obs:
            bpy.data.objects.remove(o)
        print("[wear] close-ups", kind, outfit)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) < 2 or argv[0] not in KINDS:
        print(__doc__)
        return
    closeups(argv[0], argv[1:])


if __name__ == "__main__":
    main()
