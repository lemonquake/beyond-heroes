"""bh-042: contact sheet of a boss GLB's clips (Blender, Workbench). blender -b -P render_poses.py -- <glb> <out.png> clip,clip,..."""
import bpy, sys, math, mathutils, os
a = sys.argv[sys.argv.index("--") + 1:]
glb, out, clips = a[0], a[1], a[2].split(",")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "TEXTURE"
sc.render.resolution_x = 420
sc.render.resolution_y = 480
sc.render.film_transparent = False
sc.world = bpy.data.worlds.new("w") if sc.world is None else sc.world
meshes = [o for o in sc.objects if o.type == "MESH"]
lo = mathutils.Vector((1e9,) * 3); hi = -lo
for m in meshes:
    for v in m.bound_box:
        w = m.matrix_world @ mathutils.Vector(v); lo = mathutils.Vector(map(min, lo, w)); hi = mathutils.Vector(map(max, hi, w))
h = hi.z - lo.z
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = h * 1.6
cam.location = (h * 1.2, -h * 2.0, lo.z + h * 0.75)
d = mathutils.Vector((0, 0, lo.z + h * 0.45)) - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
arm.animation_data_create()
tracks = {t.name: t for t in arm.animation_data.nla_tracks} if arm.animation_data else {}
files = []
for i, c in enumerate(clips):
    act = bpy.data.actions.get(c)
    if act is None:
        act = next((x for x in bpy.data.actions if x.name.startswith(c)), None)
    if act is None:
        print("NOCLIP", c); continue
    for t in arm.animation_data.nla_tracks:
        t.mute = True
    arm.animation_data.action = act
    if getattr(act, 'slots', None) and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    sc.frame_set(int(f0 + (f1 - f0) * 0.45))
    dg = bpy.context.evaluated_depsgraph_get()
    lo = mathutils.Vector((1e9,) * 3); hi = -lo
    for m in meshes:
        ev = m.evaluated_get(dg)
        me = ev.to_mesh()
        for v in list(me.vertices)[::7]:
            w = m.matrix_world @ v.co; lo = mathutils.Vector(map(min, lo, w)); hi = mathutils.Vector(map(max, hi, w))
        ev.to_mesh_clear()
    ctr = (lo + hi) * 0.5; ext = max(hi.z - lo.z, (hi.x - lo.x) * 1.15, (hi.y - lo.y) * 1.15)
    cam.data.ortho_scale = ext * 1.15
    cam.location = ctr + mathutils.Vector((ext * 0.9, -ext * 1.6, ext * 0.35))
    cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
    p = os.path.join(os.path.dirname(out), "_pose_%d.png" % i)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    files.append((p, c))
print("FILES", ";".join(f + "|" + c for f, c in files))
