"""Preview renders (EEVEE) for evidence.

blender -b --factory-startup --python render_previews.py -- <mode> [args]
modes: weapons | char <name> | poses <name> <anim,...> | attacks <name> | loco <name> | all
Outputs to work/lemondev/bh-001/evidence/characters/ (or --out <dir>), frames are composed into sheets by
compose_sheets.py (system Python + PIL) which this script calls at the end if available.
"""
import os
import sys
import math
import json
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVID = os.path.join(ROOT, "work", "lemondev", "bh-001", "evidence", "characters")

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import numpy as np  # noqa: E402

import bh_mesh as M  # noqa: E402
import bh_materials as MT  # noqa: E402
import bh_weapons as W  # noqa: E402
import bh_render as RR  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = EVID
if "--out" in argv:
    i = argv.index("--out")
    OUT = argv[i + 1]
    del argv[i:i + 2]
RES = 1024
if "--res" in argv:
    i = argv.index("--res")
    RES = int(argv[i + 1])
    del argv[i:i + 2]
os.makedirs(OUT, exist_ok=True)
FRAMES = os.path.join(OUT, "_frames")
os.makedirs(FRAMES, exist_ok=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def render_weapons():
    reset()
    cam = RR.setup_scene(res=RES, samples=32)
    bpy.data.objects["Ground"].hide_render = True
    mats = MT.make_materials("knight")
    obs = {}
    for name in W.WEAPONS:
        ob = M.build_static(name, W.WEAPONS[name](), mats)
        obs[name] = ob
        ob.hide_render = True
    for name, ob in obs.items():
        ob.hide_render = False
        zs = [v.co.z for v in ob.data.vertices]
        L = max(zs) - min(zs)
        ob.location = (0, 0, 1.0 - (max(zs) + min(zs)) / 2)
        yaw = 25 if name == "shield" else (8 if name == "bow" else 30)
        RR.place_camera(cam, (0, 0, 1.0), 6.0, yaw, 12, ortho=max(L * 1.15, 0.45))
        RR.render(os.path.join(OUT, f"weapon_{name}.png"))
        ob.hide_render = True
        ob.location = (0, 0, 0)
    # lineup
    x = -2.2
    for name in ["greatsword", "sword", "axe", "dagger", "spear", "staff", "wand", "bow", "arrow", "shield"]:
        ob = obs[name]
        ob.hide_render = False
        zs = [v.co.z for v in ob.data.vertices]
        ob.location = (x, 0, -min(zs))
        x += 0.5
    RR.place_camera(cam, (0.0, 0, 1.1), 12.0, 20, 8, ortho=5.2)
    RR.render(os.path.join(OUT, "weapons_lineup.png"))


def main():
    mode = argv[0] if argv else "weapons"
    if mode in ("weapons", "all"):
        render_weapons()
    if mode != "weapons":
        import preview_chars as PC
        PC.run(mode, argv[1:], OUT, FRAMES, RES)


if __name__ == "__main__":
    main()
