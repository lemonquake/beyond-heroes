"""Re-import a GLB and print nodes, materials, tris, bounds, animations (name, frames) and skin groups.

  python3 glb_check.py <path.glb>
"""
import sys

import bpy
from mathutils import Vector


def main(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    tris = 0
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for ob in bpy.context.scene.objects:
        line = f"node {ob.name} type={ob.type} parent={ob.parent.name if ob.parent else None}"
        if ob.type == "MESH" and not ob.name.startswith("Icosphere"):
            me = ob.data
            t = sum(len(p.vertices) - 2 for p in me.polygons)
            tris += t
            for c in ob.bound_box:
                w = ob.matrix_world @ Vector(c)
                lo = Vector(map(min, lo, w))
                hi = Vector(map(max, hi, w))
            line += f" tris={t} mats={[m.name for m in me.materials]} groups={len(ob.vertex_groups)}"
            if ob.vertex_groups:
                line += " weapon groups: " + ",".join(g.name for g in ob.vertex_groups if g.name.startswith("weapon"))
        print(line)
    print(f"TOTAL tris={tris} bounds min={tuple(round(x, 3) for x in lo)} max={tuple(round(x, 3) for x in hi)}")
    for a in bpy.data.actions:
        print(f"anim {a.name} frames={tuple(round(x, 1) for x in a.frame_range)}")
    print("ANIMS", len(bpy.data.actions))


if __name__ == "__main__":
    main(sys.argv[-1])
