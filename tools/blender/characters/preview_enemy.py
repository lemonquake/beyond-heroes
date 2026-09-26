"""Quick headless preview for character modules (works with the `bpy` pip module, no GPU / display needed).

Renders with the Workbench engine (material colours, studio light, cavity + shadows), so it shows silhouette,
proportions, material zoning and pose readability; it is NOT a lighting / final-look render.

  python3 preview_enemy.py <character> [--clips idle,death_back] [--frames 0,0.5,1] [--views 30,150] [--res 360]
                           [--out /tmp/claude-0/preview] [--iso]

--frames are normalized clip times (0 = first frame, 1 = last). Without --clips it renders the rest model
(modeling pose, 4 views). Writes one contact sheet PNG per call: <out>/<character>_<tag>.png
--iso adds the in-game camera angle (high pitch, 26 m-ish framing) so readability at gameplay distance is visible.
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("character")
    ap.add_argument("--clips", default="")
    ap.add_argument("--frames", default="0,0.5,1")
    ap.add_argument("--views", default="25,155")
    ap.add_argument("--res", type=int, default=360)
    ap.add_argument("--out", default="/tmp/claude-0/preview")
    ap.add_argument("--iso", action="store_true")
    ap.add_argument("--tag", default="")
    return ap.parse_args(argv)


def setup(res):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_cavity = True
    sc.display.shading.cavity_type = "BOTH"
    sc.display.shading.show_shadows = True
    sc.display.shading.shadow_intensity = 0.6
    sc.display.shading.show_object_outline = True
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.world.color = (0.16, 0.17, 0.2)
    me = bpy.data.meshes.new("Ground")
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=8, y_segments=8, size=3.0)
    bm.to_mesh(me)
    bm.free()
    g = bpy.data.objects.new("Ground", me)
    sc.collection.objects.link(g)
    gm = bpy.data.materials.new("GroundMat")
    gm.diffuse_color = (0.3, 0.3, 0.32, 1)
    me.materials.append(gm)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def place(cam, target, dist, yaw, pitch, lens=50):
    y, p = math.radians(yaw), math.radians(pitch)
    t = Vector(target)
    cam.location = t + Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p))) * dist
    d = t - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.clip_end = 200


def material_colors():
    """Workbench shows diffuse_color; copy the principled base colour of the BH_* materials into it."""
    for m in bpy.data.materials:
        if m.use_nodes and m.node_tree:
            b = m.node_tree.nodes.get("Principled BSDF")
            if b:
                c = b.inputs["Base Color"].default_value
                m.diffuse_color = (c[0], c[1], c[2], 1)
                em = b.inputs.get("Emission Color") or b.inputs.get("Emission")
                st = b.inputs.get("Emission Strength")
                if em is not None and st is not None and st.default_value > 0.5:
                    e = em.default_value
                    m.diffuse_color = (min(1, e[0] * 1.2), min(1, e[1] * 1.2), min(1, e[2] * 1.2), 1)


def main():
    a = args()
    os.makedirs(a.out, exist_ok=True)
    import build_chars as BC
    bpy.ops.wm.read_factory_settings(use_empty=True)
    clips = [c for c in a.clips.split(",") if c]
    res = BC.build_character(a.character, with_actions=bool(clips), only=set(clips) if clips else None)
    material_colors()
    cam = setup(a.res)
    arm = res["armature"]
    height = float(res["module"].PROPS["pelvis_h"]) / 0.98 * 1.8
    scale_hint = getattr(res["module"], "PREVIEW_HEIGHT", None) or height * 1.15
    tiles = []
    views = [float(v) for v in a.views.split(",")]
    frames = [float(f) for f in a.frames.split(",")]
    tmp = os.path.join(a.out, "_tiles")
    os.makedirs(tmp, exist_ok=True)
    rows = []
    if not clips:
        views = views if len(views) > 2 else [0, 90, 180, 270]
        row = []
        for v in views:
            place(cam, (0, 0, scale_hint * 0.48), scale_hint * 2.3, v, 8)
            p = os.path.join(tmp, f"rest_{int(v)}.png")
            bpy.context.scene.render.filepath = p
            bpy.ops.render.render(write_still=True)
            row.append(p)
        if a.iso:
            place(cam, (0, 0, scale_hint * 0.4), 26.0, 20, 55, lens=50)
            p = os.path.join(tmp, "rest_iso.png")
            bpy.context.scene.render.filepath = p
            bpy.ops.render.render(write_still=True)
            row.append(p)
        rows.append(row)
    else:
        ad = arm.animation_data or arm.animation_data_create()
        for c in clips:
            act = res["actions"].get(c)
            if act is None:
                print("missing clip", c)
                continue
            ad.action = act
            try:
                if ad.action_slot is None and len(act.slots):
                    ad.action_slot = act.slots[0]
            except Exception:
                pass
            n = int(act.frame_range[1])
            for v in views:
                row = []
                for fr in frames:
                    f = int(round(fr * n))
                    bpy.context.scene.frame_set(f)
                    place(cam, (0, 0, scale_hint * 0.42), scale_hint * 2.5, v, 12)
                    p = os.path.join(tmp, f"{c}_{int(v)}_{f}.png")
                    bpy.context.scene.render.filepath = p
                    bpy.ops.render.render(write_still=True)
                    row.append(p)
                rows.append(row)
    from PIL import Image
    w = max(len(r) for r in rows) * a.res
    sheet = Image.new("RGB", (w, len(rows) * a.res), (20, 20, 24))
    for i, r in enumerate(rows):
        for j, p in enumerate(r):
            sheet.paste(Image.open(p).convert("RGB").resize((a.res, a.res)), (j * a.res, i * a.res))
    tag = a.tag or ("_".join(clips) if clips else "rest")
    out = os.path.join(a.out, f"{a.character}_{tag[:60]}.png")
    sheet.save(out)
    print("PREVIEW", out)


if __name__ == "__main__":
    main()
