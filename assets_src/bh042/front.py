import bpy, sys, mathutils, math
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
arm = next((o for o in sc.objects if o.type == "ARMATURE"), None)
if arm and arm.animation_data:
    act = bpy.data.actions.get("idle")
    if act:
        for t in arm.animation_data.nla_tracks: t.mute = True
        arm.animation_data.action = act
        if len(act.slots): arm.animation_data.action_slot = act.slots[0]
sc.frame_set(5)
meshes = [o for o in sc.objects if o.type == "MESH" and o.name != "Icosphere"]
dg = bpy.context.evaluated_depsgraph_get()
lo = mathutils.Vector((1e9,)*3); hi = -lo
for m in meshes:
    ev = m.evaluated_get(dg); me = ev.to_mesh()
    for v in list(me.vertices)[::5]:
        w = m.matrix_world @ v.co; lo = mathutils.Vector(map(min, lo, w)); hi = mathutils.Vector(map(max, hi, w))
    ev.to_mesh_clear()
print("BOUNDS", tuple(round(x,2) for x in lo), tuple(round(x,2) for x in hi), "meshes", [(m.name, len(m.data.vertices)) for m in meshes])
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.color_type = "TEXTURE"
sc.render.resolution_x = 400; sc.render.resolution_y = 400
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
c = (lo + hi) / 2; e = (hi - lo).length
cam.data.type = "ORTHO"; cam.data.ortho_scale = e
cam.location = c + mathutils.Vector((0, -e * 2, 0)); cam.rotation_euler = (math.radians(90), 0, 0)
sc.render.filepath = a[1]; bpy.ops.render.render(write_still=True)
