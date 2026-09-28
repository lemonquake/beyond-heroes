"""Rootback Boar evidence renders (Workbench, headless), reusing kit_b_evidence's scene helpers.

  blender -b --factory-startup --python boar_evidence.py -- rest|clips [--out DIR]
rest  -> rootback_boar_rest_iso.png (4 rest views, close-up, gameplay camera 16 / 24 m crops)
clips -> rootback_boar_clips.png (attacks + walk/run/death at 5 normalized times)
"""
import math
import os
import sys

ROOT = r"A:\Python\beyond-heroes"
sys.path.insert(0, os.path.join(ROOT, "tools", "blender", "characters"))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender", "creatures"))

import bpy  # noqa: E402
import kit_b_evidence as KB  # noqa: E402
import build_rootback_boar as BB  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
mode = argv[0]
out = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(ROOT, "work", "lemondev", "bh-012", "evidence",
                                                                           "models_warren")
tiles = os.path.join(ROOT, "work", "lemondev", "bh-012", "scratch", "warren", "tiles", "rootback_boar", mode)
os.makedirs(tiles, exist_ok=True)
RES = 400

arm, mesh, acts = BB.build_all()
KB.material_colors()
cam = KB.setup(RES)
paths, labels = [], []
if mode == "rest":
    lo, hi = KB.mesh_bounds(mesh)
    print(f"[evidence] rootback_boar rest bounds {lo.round(3)} {hi.round(3)}")
    for yaw in (90, 35, 0, 200):
        KB.place(cam, (0, 0, 0.6), 4.6, yaw, 8)
        paths.append(KB.render(os.path.join(tiles, f"rest_{yaw}.png")))
        labels.append(f"rest yaw {yaw}")
    KB.place(cam, (0, -0.9, 0.75), 1.6, 30, 10)
    paths.append(KB.render(os.path.join(tiles, "closeup.png")))
    labels.append("head close-up")
    KB.place(cam, (0, 0.1, 1.0), 2.2, 160, 45)
    paths.append(KB.render(os.path.join(tiles, "back.png")))
    labels.append("bark-plated back")
    for dist, yaw in ((16, 0), (16, 150), (24, 60)):
        KB.place(cam, (0, 0, 0.6), dist, 0, 54, fov=40)
        arm.rotation_euler.z = math.radians(yaw)
        p = KB.render(os.path.join(tiles, f"game_{dist}_{yaw}.png"), res=1080)
        KB.crop_center(p, RES)
        paths.append(p)
        labels.append(f"game cam {dist} m, facing {yaw} (1:1 px @1080p)")
    arm.rotation_euler.z = 0
    KB.compose(paths, labels, os.path.join(out, "rootback_boar_rest_iso.png"), 4,
               f"rootback_boar: rest / gameplay camera (shoulder ~{hi[2]:.2f} m top incl. spines, "
               f"length {hi[1] - lo[1]:.2f} m)", cell=RES)
else:
    bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = RES
    for name in ("boar_gore", "boar_charge", "boar_stomp", "run", "walk", "death"):
        c, act = acts[name]
        for fr in (0, 0.25, 0.5, 0.75, 1.0):
            f = int(round(fr * c.frames))
            KB.set_action(arm, act, f)
            KB.place(cam, (0, -0.2, 0.6), 4.8, 60, 12)
            paths.append(KB.render(os.path.join(tiles, f"{name}_{f}.png")))
            labels.append(f"{name}  f{f}/{c.frames}")
    KB.compose(paths, labels, os.path.join(out, "rootback_boar_clips.png"), 5, "rootback_boar: clips (3/4 view)",
               cell=RES)
