"""Write only work/lemondev/bh-023/scratch/hero_mesh.npz (the body surface the wear / hair / skin tools fit to),
without exporting hero.glb: the same steps as hero_export.export() up to the npz.

  blender -b --factory-startup --python tools/blender/hero/hero_mesh_only.py
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hero_body as HB  # noqa: E402
import hero_export as HX  # noqa: E402
import hero_shapes as SH  # noqa: E402


def main():
    r = HB.build_body()
    ob, V, src = r["ob"], r["V"], r["src"]
    keys = HB.add_shapes(ob, V, src["T"])
    HX.add_attributes(ob, V)
    os.makedirs(HB.SCRATCH, exist_ok=True)
    path = os.path.join(HB.SCRATCH, "hero_mesh.npz")
    np.savez(path, V=V, T=src["T"], UV=src["UV"],
             N=SH.vertex_normals(V, src["T"]), bones=np.array(list(r["W"])), W=np.stack([r["W"][b] for b in r["W"]], 1),
             keys=np.array(list(keys)), deltas=np.stack([keys[k] for k in keys], 0))
    print("[hero] wrote", path)


if __name__ == "__main__":
    main()
