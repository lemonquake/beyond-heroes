import bpy, sys, math, mathutils
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index("--") + 1:]
src, out, yaw, keep = a[0], a[1], float(a[2]), a[3].split(",")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
with bpy.data.libraries.load(src) as (s, d):
    d.objects = list(s.objects)
for o in d.objects:
    if o and o.name in keep:
        sc.collection.objects.link(o)
for o in sc.objects:
    for mod in list(o.modifiers):
        if mod.type == "SUBSURF": o.modifiers.remove(mod)
    o.matrix_world = Matrix.Rotation(math.radians(yaw), 4, "Z") @ o.matrix_world
bpy.context.view_layer.update()
lo = Vector((1e9,) * 3); hi = -lo
for o in sc.objects:
    for v in o.bound_box:
        w = o.matrix_world @ Vector(v); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
c = (lo + hi) / 2; e = (hi - lo).length
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.render.resolution_x = 800; sc.render.resolution_y = 800
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = e * 10; cam.data.clip_start = e * 0.001
for i, (dx, dy, dz) in enumerate([(0.5, -1.0, 0.35), (-0.9, -0.6, 0.2), (0.0, -0.3, 1.0)]):
    cam.location = c + Vector((dx, dy, dz)).normalized() * e * 1.3
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = out + "_%d.png" % i
    bpy.ops.render.render(write_still=True)
