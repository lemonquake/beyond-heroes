"""bh-042: export chosen objects of a .blend (modifiers applied, armature kept, every action as an NLA track) to GLB.
blender -b <file.blend> -P export_blend.py -- <out.glb> obj1,obj2,..."""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
out, keep = a[0], set(a[1].split(","))
arm = None
for o in list(bpy.data.objects):
    if o.type == "ARMATURE":
        arm = o
        continue
    if o.name not in keep:
        bpy.data.objects.remove(o, do_unlink=True)
if arm:
    arm.animation_data_create()
    for t in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(t)
    for act in bpy.data.actions:
        if any(fc.data_path.startswith("pose.bones") for fc in getattr(act, "fcurves", [])) or True:
            tr = arm.animation_data.nla_tracks.new(); tr.name = act.name
            tr.strips.new(act.name, int(act.frame_range[0]), act); tr.mute = True
    arm.animation_data.action = None
# bake geometry-node / mirror / subsurf modifiers into the mesh, keep the armature deform
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    bpy.context.view_layer.objects.active = o
    for mod in list(o.modifiers):
        if mod.type != "ARMATURE":
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as e:
                print("APPLY FAILED", mod.name, e)
for img in bpy.data.images:
    print("IMG", img.name, img.filepath, img.packed_file is not None, tuple(img.size))
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_animations=True, export_animation_mode="NLA_TRACKS",
                          export_force_sampling=True, export_apply=False, export_image_format="AUTO")
print("EXPORTED", out)
