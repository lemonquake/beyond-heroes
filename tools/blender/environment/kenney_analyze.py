"""Map-design pass (2026-10-03): list the palette colours each Kenney source model actually uses.

  blender -b -P kenney_analyze.py -- <manifest.json> <out.json>

For flat-colour models it reports the material names and colours; for palette-textured models ("colormap") it samples
the palette at every face's UV centre and reports the distinct colours with face counts, so the preparation spec can
map each part to a shared game material instead of one blanket material. Read-only: no source file is written.
"""
import bpy, bmesh, json, sys, os, colorsys
from pathlib import Path

args = sys.argv[sys.argv.index("--") + 1:]
manifest = Path(args[0])
base = manifest.parent
out = {}


def sample(img, uv):
    w, h = img.size
    x = min(w - 1, max(0, int((uv[0] % 1.0) * w)))
    y = min(h - 1, max(0, int((uv[1] % 1.0) * h)))
    i = (y * w + x) * 4
    return tuple(round(c, 3) for c in img.pixels[i:i + 3])


for a in json.load(open(manifest))["assets"]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(base / a["model"]))
    rec = {"materials": {}, "palette": {}}
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
        me = o.data
        uv = me.uv_layers.active
        for p in me.polygons:
            mat = me.materials[p.material_index] if me.materials else None
            name = mat.name if mat else "none"
            rec["materials"][name] = rec["materials"].get(name, 0) + 1
            img = None
            if mat and mat.use_nodes:
                for n in mat.node_tree.nodes:
                    if n.type == "TEX_IMAGE" and n.image:
                        img = n.image
            if img and uv:
                u = [0.0, 0.0]
                for li in p.loop_indices:
                    u[0] += uv.data[li].uv[0]
                    u[1] += uv.data[li].uv[1]
                u = (u[0] / p.loop_total, u[1] / p.loop_total)
                c = sample(img, u)
                k = "%.3f,%.3f,%.3f" % c
                rec["palette"][k] = rec["palette"].get(k, 0) + 1
    out[a["id"]] = rec
    print("ANALYZED", a["id"], len(rec["palette"]))

json.dump(out, open(args[1], "w"), indent=1)
