"""bh-031: the female body scan (models/female_generic.obj, ~1M vertices with vertex colours, no rig) decimated and
written to numpy for the fitting step (hero_female.py).

  blender -b --factory-startup --python tools/blender/hero/hero_female_src.py
-> work/lemondev/bh-031/scratch/female/female_src.npz  (V (n,3) Blender space, Z up, faces -Y; T (m,3); C (n,3) colour)
"""
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC = os.path.join(ROOT, "models", "female_generic.obj")
OUT = os.path.join(ROOT, "work", "lemondev", "bh-031", "scratch", "female")
RATIO = float(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else 0.12


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=SRC, import_vertex_groups=False)
    ob = next(o for o in bpy.data.objects if o.type == "MESH")
    me = ob.data
    print("imported", len(me.vertices), "verts", len(me.polygons), "faces", "attrs", [a.name for a in me.attributes])
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    mod = ob.modifiers.new("dec", "DECIMATE")
    mod.ratio = RATIO
    bpy.ops.object.modifier_apply(modifier=mod.name)
    me = ob.data
    me.calc_loop_triangles()
    V = np.array([v.co[:] for v in me.vertices])
    T = np.array([t.vertices[:] for t in me.loop_triangles], dtype=np.int32)
    C = np.zeros((len(V), 3))
    col = me.color_attributes[0] if len(me.color_attributes) else None
    if col is not None:
        if col.domain == "POINT":
            C = np.array([c.color[:3] for c in col.data])
        else:
            acc = np.zeros((len(V), 3))
            cnt = np.zeros(len(V))
            for li, lp in enumerate(me.loops):
                acc[lp.vertex_index] += col.data[li].color[:3]
                cnt[lp.vertex_index] += 1
            C = acc / np.maximum(cnt, 1)[:, None]
    os.makedirs(OUT, exist_ok=True)
    np.savez(os.path.join(OUT, "female_src.npz"), V=V, T=T, C=C)
    print("FEMALE_SRC", V.shape, T.shape, V.min(0), V.max(0), "colour", col.name if col else None, col.domain if col else None)


main()
