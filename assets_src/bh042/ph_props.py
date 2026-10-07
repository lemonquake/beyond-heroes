"""bh-042: Poly Haven CC0 props for the Abyss dungeons.
  python ph_props.py fetch                         -> assets_src/bh042/polyhaven/<id>/ (glTF 1k + textures), sources.json
  blender -b -P ph_props.py -- convert             -> game/assets/environment/ph_<id>.glb (decimated, small textures,
                                                       a `-colonly` box when the prop blocks movement)
Same pipeline as bh-033 (assets_src/bh033/props/convert_props.py)."""
import datetime, hashlib, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "polyhaven")
OUT = os.path.join(HERE, "..", "..", "game", "assets", "environment")
# id: (triangle budget, texture size, collider)
PROPS = {
    "large_castle_door": (6000, 1024, True), "large_iron_gate": (9000, 1024, True), "gothic_statue": (9000, 1024, True),
    "lion_head": (6000, 512, False), "Chandelier_02": (9000, 512, False), "lantern_chandelier_01": (5000, 512, False),
    "brass_candleholders": (6000, 512, False), "wooden_candlestick": (3000, 512, False), "stone_fire_pit": (3800, 1024, True),
    "kite_shield": (4000, 512, False), "ornate_medieval_mace": (4000, 512, False), "ornate_medieval_dagger": (3000, 512, False),
    "marble_bust_01": (6000, 512, True), "rock_moss_set_01": (9000, 1024, True), "rock_07": (6000, 1024, True),
    "vintage_oil_lamp": (4000, 512, False), "Lantern_01": (6000, 512, False), "GothicCommode_01": (3900, 1024, True),
    "brass_goblets": (4000, 512, False), "metal_jug": (3000, 512, False),
}
UA = {"User-Agent": "BeyondHeroes-bh042-asset-fetch"}


def fetch():
    src_path = os.path.join(HERE, "sources.json")
    recs = json.load(open(src_path)) if os.path.exists(src_path) else []
    have = {r.get("url") for r in recs}

    def get(u):
        return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=180).read()
    for pid in PROPS:
        info = json.loads(get("https://api.polyhaven.com/info/" + pid))
        files = json.loads(get("https://api.polyhaven.com/files/" + pid))["gltf"]["1k"]["gltf"]
        todo = [(files["url"], os.path.basename(urllib.parse.urlparse(files["url"]).path))]
        todo += [(inc["url"], rel) for rel, inc in files.get("include", {}).items()]
        for url, rel in todo:
            dest = os.path.join(SRC, pid, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if not os.path.exists(dest):
                data = get(url)
                open(dest, "wb").write(data)
            data = open(dest, "rb").read()
            if url not in have:
                recs.append({"source": "Poly Haven", "url": url, "page": "https://polyhaven.com/a/" + pid, "model": pid,
                             "name": info.get("name"), "authors": list(info.get("authors", {}).keys()), "license": "CC0 1.0",
                             "path": os.path.relpath(dest, HERE).replace(os.sep, "/"), "bytes": len(data),
                             "sha256": hashlib.sha256(data).hexdigest(), "downloaded": datetime.date.today().isoformat()})
        print("fetched", pid)
    json.dump(recs, open(src_path, "w"), indent=1)


def convert():
    import bpy, mathutils

    def tris(objs):
        dg = bpy.context.evaluated_depsgraph_get()
        t = 0
        for o in objs:
            me = o.evaluated_get(dg).to_mesh()
            me.calc_loop_triangles()
            t += len(me.loop_triangles)
            o.evaluated_get(dg).to_mesh_clear()
        return t
    report = {}
    for pid, (budget, tex, col) in PROPS.items():
        gl = os.path.join(SRC, pid, pid + "_1k.gltf")
        if not os.path.exists(gl):
            print("missing", gl)
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=gl)
        meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        before = tris(meshes)
        if before > budget:
            for o in meshes:
                m = o.modifiers.new("dec", "DECIMATE")
                m.ratio = max(0.02, budget / before)
                m.use_collapse_triangulate = True
                bpy.context.view_layer.objects.active = o
                bpy.ops.object.modifier_apply(modifier="dec")
        after = tris(meshes)
        for img in bpy.data.images:
            if img.size[0] > tex:
                img.scale(tex, tex)
        lo = mathutils.Vector((1e9,) * 3); hi = -lo
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
        print("PROP", pid, before, "->", after, "size", report[pid]["size_m"])
    json.dump(report, open(os.path.join(HERE, "props_report.json"), "w"), indent=1)


if __name__ == "__main__":
    if "convert" in sys.argv:
        convert()
    else:
        fetch()
