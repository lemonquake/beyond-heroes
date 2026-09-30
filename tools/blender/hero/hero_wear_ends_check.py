"""bh-023: counts and checks for the worn helms, gloves, boots and jewellery (hero_wear_ends.py).

  blender -b --factory-startup --python tools/blender/hero/hero_wear_ends_check.py -- stats [ids...]
      triangles per mesh (per side for sided pieces), materials, the budget verdict; for helms also how the skull
      sits inside (vertices of the head the helm's surface cuts off from the skull's centre = poking through, and
      the smallest clearance of the covered ones)
  blender -b --factory-startup --python tools/blender/hero/hero_wear_ends_check.py -- reimport <ids...>
      re-imports the exported GLBs: mesh names, triangles, materials, armature bones, shape keys and their values
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import hero_wear as HW  # noqa: E402,F401  (registers every piece)
import hero_wear_kit as WK  # noqa: E402
import hero_wear_ends as E  # noqa: E402
from hero_wear_kit import S, HC  # noqa: E402

BUDGET = {"helm": 1500, "glove": 1700, "boot": 1500, "jewel": 250}
KIND = {}
for _i in E.HELMS:
    KIND[_i] = "helm"
for _i in E.GLOVES:
    KIND[_i] = "glove"
for _i in E.BOOTS:
    KIND[_i] = "boot"
for _i in E.JEWELS:
    KIND[_i] = "jewel"


def head_cover(id):
    """-> (poking, min clearance, where): head vertices that lie outside the helm's surface though the helm passes
    between them and the skull's centre; the smallest gap between covered skin and the helm."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    parts = [p for p in WK.REGISTRY[id]["fn"]() if "black" not in p.mat]
    V, F, off = [], [], 0
    for p in parts:
        V += [tuple(v) for v in p.V]
        F += [tuple(i + off for i in f) for f in p.F]
        off += len(p.V)
    bvh = BVHTree.FromPolygons(V, F)
    b = WK.body()
    head = np.nonzero((b.V[:, 2] > 1.60) & (b.W[:, WK.BONES.index("head")] > 0.5))[0]
    c = Vector((0.0, -0.04, 1.69))
    poke, gap, where = 0, 9.0, None
    for i in head:
        v = Vector(b.V[i])
        d = v - c
        L = d.length
        d.normalize()
        if bvh.ray_cast(c, d, L - 0.0005)[0] is not None:
            poke += 1
            continue
        hit = bvh.ray_cast(v, d, 0.2)
        if hit[0] is not None and hit[3] < gap:
            gap, where = hit[3], tuple(round(float(x), 3) for x in b.V[i])
    return poke, gap, where


def stats(ids):
    import bpy
    rows = []
    for i in ids:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        arm, _ = S.build_armature(HC.PROPS, "Armature")
        obs = WK.build_item(i, arm)
        tris = [WK.tri_count(o) for o in obs]
        mats = sorted({m.name for o in obs for m in o.data.materials})
        kind = KIND.get(i, "?")
        ok = max(tris) <= BUDGET.get(kind, 10 ** 9) and len(mats) <= 4
        extra = ""
        if kind == "helm":
            poke, gap, where = head_cover(i)
            extra = " | skull: %d poking, clearance %.1f mm at %s" % (poke, gap * 1000, where)
        rows.append("[ends] %-26s %-5s %s tris %-11s %d mats %s%s%s" % (
            i, kind, "x2" if len(obs) == 2 else "  ", "/".join(str(t) for t in tris), len(mats), "OK " if ok else "OVER",
            " (" + ", ".join(m.split("__it_hw_")[-1] for m in mats) + ")", extra))
        print(rows[-1])
    print("\n".join(["", "[ends] ---- summary ----"] + rows))


def reimport(ids):
    import bpy
    for i in ids:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        path = os.path.join(WK.OUT_DIR, i + ".glb")
        bpy.ops.import_scene.gltf(filepath=path)
        print("[ends] reimport %s (%d bytes)" % (i, os.path.getsize(path)))
        for o in bpy.context.scene.objects:
            if o.type == "ARMATURE":
                names = [b.name for b in o.data.bones]
                shared = [b for b in S.BONE_ORDER if b in names]
                print("[ends]   armature %s: %d bones, %d of the shared %d names; e.g. %s" % (
                    o.name, len(names), len(shared), len(S.BONE_ORDER), ", ".join(names[:8])))
            elif o.type == "MESH":
                keys = o.data.shape_keys.key_blocks if o.data.shape_keys else []
                groups = [g.name for g in o.vertex_groups]
                mod = [m.type for m in o.modifiers]
                print("[ends]   mesh %s: %d tris, materials %s, groups %s, modifiers %s, parent %s" % (
                    o.name, WK.tri_count(o), [m.name for m in o.data.materials], groups, mod, o.parent.name if o.parent else None))
                print("[ends]     shape keys: %s" % ", ".join("%s=%.2f" % (k.name, k.value) for k in keys))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argv:
        print(__doc__)
        return
    if argv[0] == "reimport":
        reimport(argv[1:])
    else:
        ids = argv[1:] or [i for i in E.ALL if i in WK.REGISTRY]
        stats(ids)


if __name__ == "__main__":
    main()
