"""bh-042: front + side orthographic renders of a mesh normalised like rig_to_hero (feet on z=0, centred, 1.8 tall),
with a 0.1 m grid, for reading joint landmarks.  blender -b -P measure.py -- <src> <out_prefix> [yaw] [objects,..]"""
import bpy, sys, math, mathutils
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index("--") + 1:]
src, out = a[0], a[1]
yaw = float(a[2]) if len(a) > 2 else 0.0
keep = a[3].split(",") if len(a) > 3 and a[3] else None
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
ext = src.lower().rsplit(".", 1)[1]
if ext == "blend":
    with bpy.data.libraries.load(src) as (s, d):
        d.objects = list(s.objects)
    for o in d.objects:
        if o and o.type == "MESH":
            sc.collection.objects.link(o)
elif ext == "fbx":
    bpy.ops.import_scene.fbx(filepath=src)
else:
    bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in sc.objects if o.type == "MESH" and (keep is None or o.name in keep)]
for o in list(sc.objects):
    if o not in meshes:
        bpy.data.objects.remove(o, do_unlink=True)
for m in meshes:
    for mod in list(m.modifiers):
        if mod.type in ("SUBSURF", "ARMATURE"):
            m.modifiers.remove(mod)
    m.parent = None
bpy.context.view_layer.update()
Y = Matrix.Rotation(math.radians(yaw), 4, "Z")
lo = Vector((1e9,) * 3); hi = -lo
for m in meshes:
    for v in m.data.vertices:
        w = Y @ m.matrix_world @ v.co; lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
s = 1.8 / (hi.z - lo.z)
off = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
N = Matrix.Diagonal((s, s, s, 1)) @ Matrix.Translation(-off) @ Y
for m in meshes:
    m.matrix_world = N @ m.matrix_world
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.render.resolution_x = 900; sc.render.resolution_y = 900
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.4
for name, loc, rot in [("front", (0, -10, 0.9), (math.radians(90), 0, 0)), ("side", (10, 0, 0.9), (math.radians(90), 0, math.radians(90))), ("top", (0, 0, 10), (0, 0, 0))]:
    cam.location = loc; cam.rotation_euler = rot
    sc.render.filepath = out + "_" + name + ".png"
    bpy.ops.render.render(write_still=True)
print("DONE")
