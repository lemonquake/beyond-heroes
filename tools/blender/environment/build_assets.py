"""Build + export every environment asset to game/assets/environment/<name>.glb.

    blender -b --factory-startup --python tools/blender/environment/build_assets.py -- [names or categories...]
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa
from mathutils import noise as mnoise  # noqa

import kit  # noqa
from registry import REG, ORDER  # noqa
import assets_arch, assets_nature, assets_props, assets_crypt, assets_town  # noqa
import assets_town2, assets_interior  # noqa  (bh-003)

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "game", "assets", "environment")


def tri_count(ob):
    me = ob.data
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = []
    for a in argv:
        if a in REG:
            names.append(a)
        else:
            names += [n for n in ORDER if REG[n]["cat"] == a]
    names = names or list(ORDER)
    os.makedirs(OUT, exist_ok=True)
    log = []
    for name in names:
        t0 = time.time()
        kit.clear_scene()
        k = kit.Kit(name)
        mnoise.seed_set(k.seed % 100000)
        opts = REG[name]["fn"](k) or {}
        ob = k.finish(recenter=opts.get("recenter", True), damp=opts.get("damp", 0.0), damp_h=opts.get("damp_h", 0.8))
        kit.export_glb(ob, os.path.join(OUT, name + ".glb"))
        tris = tri_count(ob)
        line = f"{name:22s} tris={tris:6d} mats={','.join(k.mats)} col={'yes' if k.cols else 'no'}"
        if k.groups:
            root, objs = k.finish_fragments(name + "_fragments")
            kit.export_glb(root, os.path.join(OUT, name + "_fragments.glb"))
            line += f" fragments={len(objs)}"
        line += f"  {time.time() - t0:.1f}s"
        print("BUILT", line, flush=True)
        log.append(line)
    with open(os.path.join(HERE, "build_log.txt"), "a") as f:
        f.write("\n".join(log) + "\n")


main()
