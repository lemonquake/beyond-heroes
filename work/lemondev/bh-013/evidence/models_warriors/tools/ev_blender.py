"""Evidence renders + metrics for an enemy module (Workbench), run inside Blender.

blender -b --factory-startup --python ev_blender.py -- <char> --out DIR --mode rest|clips|metrics
        [--stance idle_staff] [--clips a,b] [--frames 0,0.35,0.6,1] [--res 360] [--view 30]
Writes tiles + <out>/<char>_<mode>.json manifest (composed by ev_compose.py with system Python / PIL).
"""
import argparse
import json
import math
import os
import sys

CHARS = r"A:\Python\beyond-heroes\tools\blender\characters"
sys.path.insert(0, CHARS)

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402


def args():
    argv = sys.argv[sys.argv.index("--") + 1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("character")
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", default="rest")
    ap.add_argument("--stance", default="idle")
    ap.add_argument("--clips", default="")
    ap.add_argument("--frames", default="0,0.3,0.5,0.7,1")
    ap.add_argument("--res", type=int, default=360)
    ap.add_argument("--view", type=float, default=30)
    ap.add_argument("--headz", type=float, default=0.0)
    ap.add_argument("--headviews", default="25:5,335:20")
    return ap.parse_args(argv)


def set_action(arm, act):
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = act
    try:
        if act is not None and ad.action_slot is None and len(act.slots):
            ad.action_slot = act.slots[0]
    except Exception:
        pass


def render(path, res_x, res_y=None):
    sc = bpy.context.scene
    sc.render.resolution_x = res_x
    sc.render.resolution_y = res_y or res_x
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def eval_coords(mesh):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    me = ev.to_mesh()
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    M = np.array(mesh.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]


def weapon_mask(mesh):
    n = len(mesh.data.vertices)
    mask = np.zeros(n, bool)
    gi = {g.index: g.name for g in mesh.vertex_groups}
    for v in mesh.data.vertices:
        for g in v.groups:
            if gi.get(g.group, "").startswith("weapon.") and g.weight > 0.5:
                mask[v.index] = True
    return mask


def main():
    a = args()
    os.makedirs(a.out, exist_ok=True)
    tiles = os.path.join(a.out, "_tiles_" + a.character)
    os.makedirs(tiles, exist_ok=True)
    import build_chars as BC
    import preview_enemy as PE
    bpy.ops.wm.read_factory_settings(use_empty=True)
    clips = [c for c in a.clips.split(",") if c]
    need = set(clips) | {a.stance}
    if a.mode == "metrics":
        need = None
    if a.mode == "parts":
        res = BC.build_character(a.character, with_actions=False)
        from collections import Counter
        c = Counter()
        for pt in res["body"].parts:
            c[pt.name + ":" + pt.mat] += sum(len(f) - 2 for f in pt.F)
        print("PARTS total", sum(c.values()))
        for k, v in c.most_common(25):
            print("PARTS", v, k)
        return
    res = BC.build_character(a.character, with_actions=True, only=need)
    PE.material_colors()
    # emissive palette entries (glows, the mirror) render at their emission colour in Workbench: in the game the
    # emission floor (energy >= 1) keeps them bright, the studio-light metallic reflection would show them black
    for m in bpy.data.materials:
        b = m.node_tree.nodes.get("Principled BSDF") if (m.use_nodes and m.node_tree) else None
        st = b.inputs.get("Emission Strength") if b else None
        if st is not None and st.default_value > 0.5:
            m.metallic = 0.0
            m.roughness = 0.4
    cam = PE.setup(a.res)
    arm, mesh = res["armature"], res["mesh"]
    acts = res["actions"]
    H = float(res["module"].PROPS["pelvis_h"]) / 0.98 * 1.8
    hint = getattr(res["module"], "PREVIEW_HEIGHT", None) or H * 1.15
    rows = []
    man = dict(character=a.character, res=a.res, rows=rows)
    if a.mode == "rest":
        # T-pose front + back, stance at 4 yaws, head close-up, gameplay camera
        row = []
        set_action(arm, None)
        for pb in arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.location = (0, 0, 0)
        bpy.context.view_layer.update()
        for yaw in (0, 180):
            PE.place(cam, (0, 0, hint * 0.48), hint * 2.3 * 1.08, yaw, 8)
            p = os.path.join(tiles, f"tpose_{yaw}.png")
            render(p, a.res)
            row.append(dict(path=p, label=f"rest T-pose yaw {yaw}"))
        rows.append(row)
        set_action(arm, acts[a.stance])
        bpy.context.scene.frame_set(0)
        row = []
        for yaw in (20, 90, 160, 250):
            PE.place(cam, (0, 0, hint * 0.46), hint * 2.3, yaw, 10)
            p = os.path.join(tiles, f"stance_{yaw}.png")
            render(p, a.res)
            row.append(dict(path=p, label=f"{a.stance} f0 yaw {yaw}"))
        rows.append(row)
        row = []
        co = eval_coords(mesh)
        wm = weapon_mask(mesh)
        top = float(co[~wm, 2].max())
        for yaw, pit in [tuple(float(x) for x in hv.split(":")) for hv in a.headviews.split(",")]:
            hz = a.headz or top * 0.87
            PE.place(cam, (0, -0.02, hz), top * 0.62, yaw, pit)
            p = os.path.join(tiles, f"head_{int(yaw)}_{int(pit)}.png")
            render(p, a.res)
            row.append(dict(path=p, label=f"head close-up yaw {int(yaw)} pitch {int(pit)}"))
        # gameplay camera: pitch 54, fov 40 (vertical), distance 16 and 22 m, 1920x1080 then cropped by compose
        for dist in (16, 22):
            c = Vector((0, 0, 1.1))
            pit = math.radians(54)
            cam.location = c + Vector((0, -math.cos(pit), math.sin(pit))) * dist
            cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
            cam.data.sensor_fit = "VERTICAL"
            cam.data.angle_y = math.radians(40)
            p = os.path.join(tiles, f"game_{dist}.png")
            render(p, 1920, 1080)
            row.append(dict(path=p, label=f"game cam 54deg {dist} m (1080p crop 1:1)", crop=[960 - 180, 540 - 180, 960 + 180,
                                                                                         540 + 180]))
        cam.data.sensor_fit = "AUTO"
        cam.data.lens = 50
        rows.append(row)
    elif a.mode == "clips":
        fr = [float(x) for x in a.frames.split(",")]
        for c in clips:
            act = acts.get(c)
            if act is None:
                print("MISSING CLIP", c)
                continue
            set_action(arm, act)
            n = int(act.frame_range[1])
            row = []
            for f01 in fr:
                f = int(round(f01 * n))
                bpy.context.scene.frame_set(f)
                PE.place(cam, (0, 0, hint * 0.42), hint * 2.6, a.view, 12)
                p = os.path.join(tiles, f"clip_{c}_{f}.png")
                render(p, a.res)
                row.append(dict(path=p, label=f"{c} f{f}/{n}"))
            rows.append(row)
    elif a.mode == "metrics":
        me = mesh.data
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        rest = np.array([v.co[:] for v in me.vertices])
        E = np.array([e.vertices[:] for e in me.edges])
        L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
        ok = L0 > 0.004
        wm = weapon_mask(mesh)
        gi = {g.index: g.name for g in mesh.vertex_groups}
        dom = []
        for v in me.vertices:
            best = max(v.groups, key=lambda g: g.weight, default=None)
            dom.append(gi.get(best.group, "?") if best else "?")
        out = dict(tris=tris, verts=len(me.vertices), materials=[m.name for m in me.materials], clips={})
        set_action(arm, None)
        for pb in arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
        bpy.context.view_layer.update()
        out["tpose_top"] = float(rest[~wm, 2].max())
        for name in sorted(acts):
            act = acts[name]
            set_action(arm, act)
            n = int(act.frame_range[1])
            worst, worst_e, worst_f, zmin, zmax_body = 0.0, -1, 0, 9.0, 0.0
            dmax, dmax_e = 0.0, -1
            shrink = 9.0
            for f in range(0, n + 1):
                bpy.context.scene.frame_set(f)
                co = eval_coords(mesh)
                L = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1)
                r = np.where(ok, L / np.maximum(L0, 1e-9), 1.0)
                i = int(np.argmax(r))
                if r[i] > worst:
                    worst, worst_e, worst_f = float(r[i]), i, f
                shrink = min(shrink, float(r[ok].min()))
                dl = L - L0
                j = int(np.argmax(dl))
                if dl[j] > dmax:
                    dmax, dmax_e = float(dl[j]), j
                zmin = min(zmin, float(co[:, 2].min()))
                zmax_body = max(zmax_body, float(co[~wm, 2].max()))
                if name == "idle" and f == 0:
                    out["idle_top"] = float(co[~wm, 2].max())
                    out["idle_bbox"] = [co.min(0).tolist(), co.max(0).tolist()]
            v0 = int(E[worst_e, 0]) if worst_e >= 0 else -1
            out["clips"][name] = dict(frames=n + 1, max_stretch=round(worst, 3), at_frame=worst_f,
                                      bone=dom[v0] if v0 >= 0 else "", min_ratio=round(shrink, 3),
                                      zmin=round(zmin, 3), zmax_body=round(zmax_body, 3),
                                      at_rest=[round(float(x), 3) for x in rest[v0]] if v0 >= 0 else [],
                                      abs_grow=round(dmax, 3),
                                      abs_at=[round(float(x), 3) for x in rest[int(E[dmax_e, 0])]] if dmax_e >= 0 else [],
                                      abs_bone=dom[int(E[dmax_e, 0])] if dmax_e >= 0 else "")
        p = os.path.join(a.out, f"{a.character}_metrics.json")
        with open(p, "w") as f:
            json.dump(out, f, indent=1)
        print("METRICS", p, "tris", tris)
        return
    p = os.path.join(a.out, f"{a.character}_{a.mode}.json")
    with open(p, "w") as f:
        json.dump(man, f, indent=1)
    print("MANIFEST", p)


if __name__ == "__main__":
    main()
