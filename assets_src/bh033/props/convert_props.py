"""bh-033: Poly Haven props -> game GLBs (Blender 5.x, headless). Sources in assets_src/bh033/polyhaven are never written.
  blender -b -P convert_props.py -- <out_dir>
Per prop: decimate to a triangle budget, downsize textures (512 for small props), add a box collider named
`<name>-colonly` (Godot turns it into a StaticBody) when the prop should block movement, export one GLB with embedded
textures. Writes props_report.json (triangles before/after, texture size, collider, bounds)."""
import bpy, bmesh, json, os, sys, mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "polyhaven")
OUT = sys.argv[sys.argv.index("--") + 1]
# id: (triangle budget, texture size, collider)
PROPS = {
    "wooden_crate_01": (6600, 512, True), "wooden_crate_02": (5200, 1024, True), "wooden_bucket_01": (5200, 512, False),
    "wooden_bucket_02": (5200, 512, True), "wooden_lantern_01": (6000, 512, False), "wicker_basket_01": (4000, 512, False),
    "wicker_basket_02": (3000, 512, False), "wine_barrel_01": (6000, 1024, True), "painted_wooden_bench": (1000, 1024, True),
    "planter_box_01": (6000, 1024, True), "tree_stump_01": (6000, 1024, True), "WoodenTable_01": (1000, 1024, True),
    "round_wooden_table_01": (6000, 1024, True), "wooden_stool_01": (4000, 512, True), "wooden_stool_02": (3000, 512, False),
    "folding_wooden_stool": (4000, 512, True), "GothicBed_01": (10000, 1024, True), "GothicCabinet_01": (8000, 1024, True),
    "wooden_bookshelf_worn": (8000, 1024, True), "ceramic_pot": (3600, 512, False), "wooden_bowl_01": (2000, 512, False),
    "carved_wooden_plate": (2200, 512, False), "wooden_cutting_board": (2000, 512, False), "wooden_axe": (2500, 512, False),
    "treasure_chest": (8000, 1024, True),
}

def tris(objs):
    t = 0
    for o in objs:
        me = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
        me.calc_loop_triangles()
        t += len(me.loop_triangles)
        o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    return t

report = {}
os.makedirs(OUT, exist_ok=True)
for pid, (budget, tex, col) in PROPS.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, pid, pid + "_1k.gltf"))
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    before = tris(meshes)
    if before > budget:
        ratio = budget / before
        for o in meshes:
            m = o.modifiers.new("dec", "DECIMATE")
            m.ratio = max(0.02, ratio)
            m.use_collapse_triangulate = True
        for o in meshes:
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier="dec")
    after = tris(meshes)
    for img in bpy.data.images:
        if img.size[0] > tex:
            img.scale(tex, tex)
    lo = mathutils.Vector((1e9,) * 3); hi = mathutils.Vector((-1e9,) * 3)
    for o in meshes:
        for v in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(v)
            lo = mathutils.Vector(map(min, lo, w)); hi = mathutils.Vector(map(max, hi, w))
    size = hi - lo
    if col:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(lo + hi) * 0.5)
        c = bpy.context.active_object
        c.scale = size
        c.name = "ph_%s-colonly" % pid.lower()
    out = os.path.join(OUT, "ph_%s.glb" % pid.lower())
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_image_format="AUTO", export_apply=True)
    report[pid] = {"glb": os.path.basename(out), "triangles_before": before, "triangles_after": after, "texture": tex,
        "collider": col, "size_m": [round(size.x, 3), round(size.z, 3), round(size.y, 3)], "bytes": os.path.getsize(out)}
    print("PROP", pid, before, "->", after, "tex", tex, "col", col)
json.dump(report, open(os.path.join(HERE, "props_report.json"), "w"), indent=1)
