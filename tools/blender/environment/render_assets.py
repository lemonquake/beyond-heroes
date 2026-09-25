"""Render every exported GLB with the same 3/4 camera + light rig (EEVEE) for contact sheets.

    blender -b --factory-startup --python tools/blender/environment/render_assets.py -- [names...] [--res 512]
Writes work/lemondev/bh-001/evidence/environment/renders/<name>.png (fragments are shown slightly exploded).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa
from mathutils import Vector  # noqa
import render_lib as rl  # noqa


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    res = 512
    front = "--front" in argv
    argv = [a for a in argv if a != "--front"]
    if "--res" in argv:
        i = argv.index("--res")
        res = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    files = sorted(f[:-4] for f in os.listdir(rl.ENV) if f.endswith(".glb"))
    names = argv or files
    outdir = os.path.join(rl.EVI, "renders")
    os.makedirs(outdir, exist_ok=True)
    for name in names:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        rl._img_cache.clear()
        rl.setup_scene((res, res))
        rl.standard_rig()
        objs = rl.import_glb(os.path.join(rl.ENV, name + ".glb"))
        if name.endswith("_fragments"):
            mn, mx = rl.world_bounds(objs)
            ctr = (mn + mx) / 2
            for o in objs:
                if o.type == "MESH" and o.name.startswith("frag_"):
                    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
                    c = sum(bb, Vector()) / 8
                    d = c - ctr
                    d.z = max(d.z, 0) * 0.5
                    o.location += d * 0.35
        mn, mx = rl.world_bounds(objs)
        size = max((mx - mn).x, (mx - mn).y, 1.0)
        rl.ground(size * 8)
        rl.camera_34(mn, mx, az=0, el=0, lens=80) if front else rl.camera_34(mn, mx)
        bpy.context.scene.render.filepath = os.path.join(outdir, name + ("_front" if front else "") + ".png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", name, flush=True)


main()
