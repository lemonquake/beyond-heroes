"""bh-042: the Weeping Shroud's head: OpenGameArt 'skull prop' (CC0) with its texture set, 2.8 m tall, centred, facing -Y."""
import bpy, os
from mathutils import Matrix, Vector
D = "A:/Python/beyond-heroes/assets_src/bh042/oga/skull-prop/"
OUT = "A:/Python/beyond-heroes/game/assets/characters/bh042/weeping_shroud.glb"
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(D + "skull prop.blend") as (s, d):
    d.objects = ["Volume4"]
o = d.objects[0]
bpy.context.scene.collection.objects.link(o)
o.parent = None
bpy.context.view_layer.update()
pts = [o.matrix_world @ v.co for v in o.data.vertices]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
s = 2.8 / (hi.z - lo.z)
o.matrix_world = Matrix.Diagonal((s, s, s, 1)) @ Matrix.Translation(-(lo + hi) / 2) @ o.matrix_world
bpy.context.view_layer.objects.active = o
o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mt = bpy.data.materials.new("weeping_shroud")
mt.use_nodes = True
nt = mt.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
def tex(name, socket, noncolor=False):
    im = bpy.data.images.load(D + name)
    if max(im.size) > 1024:
        im.scale(1024, 1024)
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = im
    return t
c = tex("skull_Default_color.png", None)
nt.links.new(c.outputs["Color"], bsdf.inputs["Base Color"])
n = tex("skull_Default_nmap.png", None, True)
nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(n.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
r = tex("skull_Default_rough.jpg", None, True)
nt.links.new(r.outputs["Color"], bsdf.inputs["Roughness"])
o.data.materials.clear(); o.data.materials.append(mt)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_image_format="JPEG", export_jpeg_quality=88)
print("EXPORTED", OUT, os.path.getsize(OUT))
