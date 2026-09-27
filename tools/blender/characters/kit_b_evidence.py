"""Builder B (bh-010) evidence renders + deformation audit for enemy modules (Workbench, headless).

  blender -b --factory-startup --python kit_b_evidence.py -- <id> <mode> [options]
modes
  rest     T-pose rest (4 views) + stance idle (3 views + close-up) + gameplay-camera crops (54 deg pitch, 40 deg fov,
           in-game pixel scale at 1080p) + optional lineup with a reference enemy (--ref <id>)   -> <id>_rest_iso.png
  clips    rows of --clips, --frames normalized frames each, 3/4 view                           -> <id>_clips.png
  audit    every exported clip: max / p99.9 skin edge stretch vs rest, lowest vertex, frames      -> <id>_audit.txt
  tint     BH_Emissive recoloured to four element colours (runtime recolour check)             -> <id>_tint.png
options: --out DIR (default work/lemondev/bh-010/evidence/enemies_b) --res 400 --stance idle_1h --ref bandit_cutthroat
Tiles go to $BH_SCRATCH (default <out>/_tiles); sheets are composed by compose_sheets.py with $BH_PYTHON (python).
"""
import argparse
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
NL = chr(10)

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("character")
    ap.add_argument("mode", choices=["rest", "clips", "audit", "tint"])
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "lemondev", "bh-010", "evidence", "enemies_b"))
    ap.add_argument("--res", type=int, default=400)
    ap.add_argument("--clips", default="")
    ap.add_argument("--frames", default="0,0.25,0.5,0.75,1")
    ap.add_argument("--stance", default="idle")
    ap.add_argument("--ref", default="")
    ap.add_argument("--tag", default="")
    return ap.parse_args(argv)


# ------------------------------------------------------------------------------------------------ scene
def material_colors():
    for m in bpy.data.materials:
        if m.use_nodes and m.node_tree:
            b = m.node_tree.nodes.get("Principled BSDF")
            if b:
                c = b.inputs["Base Color"].default_value
                m.diffuse_color = (c[0], c[1], c[2], 1)
                em = b.inputs.get("Emission Color")
                st = b.inputs.get("Emission Strength")
                if em is not None and st is not None and st.default_value > 0.5:
                    e = em.default_value
                    m.diffuse_color = (min(1, e[0] * 1.2), min(1, e[1] * 1.2), min(1, e[2] * 1.2), 1)


def setup(res):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.show_shadows = True
    sh.shadow_intensity = 0.55
    sh.show_object_outline = True
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.world.color = (0.16, 0.17, 0.2)
    import bmesh
    me = bpy.data.meshes.new("Ground")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=16, y_segments=16, size=6.0)
    bm.to_mesh(me)
    bm.free()
    g = bpy.data.objects.new("Ground", me)
    sc.collection.objects.link(g)
    gm = bpy.data.materials.new("GroundMat")
    gm.diffuse_color = (0.24, 0.25, 0.22, 1)
    me.materials.append(gm)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def place(cam, target, dist, yaw, pitch, fov=None, lens=50):
    y, p = math.radians(yaw), math.radians(pitch)
    t = Vector(target)
    cam.location = t + Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p))) * dist
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    if fov:
        cam.data.sensor_fit = "VERTICAL"
        cam.data.angle = math.radians(fov)
    else:
        cam.data.sensor_fit = "AUTO"
        cam.data.lens = lens
    cam.data.clip_end = 300


def render(path, res=None):
    sc = bpy.context.scene
    if res:
        sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def set_action(arm, act, frame):
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = act
    try:
        if len(act.slots):
            ad.action_slot = act.slots[0]
    except Exception:
        pass
    bpy.context.scene.frame_set(int(frame))


def mesh_bounds(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    co = co.reshape(-1, 3) @ np.array(ob.matrix_world)[:3, :3].T + np.array(ob.matrix_world)[:3, 3]
    return co.min(0), co.max(0)


def compose(paths, labels, out, cols, title, cell=None):
    job = dict(paths=paths, labels=labels, out=out, cols=cols, title=title, cell=cell)
    jp = out + ".job.json"
    with open(jp, "w") as f:
        json.dump(job, f)
    py = os.environ.get("BH_PYTHON", "python")
    subprocess.run([py, os.path.join(HERE, "compose_sheets.py"), jp], check=True)
    os.remove(jp)


def crop_center(path, size, dy=0):
    """Crop the centre size x size of a rendered tile with Blender's image API (no PIL in Blender)."""
    im = bpy.data.images.load(path)
    w, h = im.size
    px = np.array(im.pixels[:]).reshape(h, w, 4)
    y0 = h // 2 - size // 2 + dy
    x0 = w // 2 - size // 2
    sub = px[y0:y0 + size, x0:x0 + size].copy()
    out = bpy.data.images.new("crop", size, size, alpha=True)
    out.pixels[:] = sub.ravel()
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(im)
    bpy.data.images.remove(out)
    return path


# ------------------------------------------------------------------------------------------------ modes
def build(name, clips):
    import build_chars as BC
    return BC.build_character(name, with_actions=True, only=set(clips))


def mode_rest(a, tiles):
    import build_chars as BC
    clips = [a.stance, "idle"]
    res = build(a.character, clips)
    arm, mesh = res["armature"], res["mesh"]
    ref = None
    for act in res["actions"].values():      # bake_action replaces same-named actions: keep ours out of the way
        act.name = act.name + "__main"
    if a.ref:
        ref = BC.build_character(a.ref, with_actions=True, only={"idle"})
        ref["armature"].location.x = -1.0
    material_colors()
    cam = setup(a.res)
    lo, hi = mesh_bounds(mesh)
    H = float(hi[2])
    print(f"[evidence] {a.character} rest height {H:.3f} m, width {hi[0] - lo[0]:.3f} m, depth {hi[1] - lo[1]:.3f} m")
    paths, labels = [], []
    if ref:
        ref["mesh"].hide_render = True
    for yaw in (0, 35, 90, 180):
        place(cam, (0, 0, H * 0.5), max(H, hi[0] - lo[0] + 0.3) * 2.25, yaw, 6)
        paths.append(render(os.path.join(tiles, f"rest_{yaw}.png")))
        labels.append(f"rest T-pose yaw {yaw}")
    set_action(arm, res["actions"][a.stance], 0)
    lo2, hi2 = mesh_bounds(mesh)
    Hs = float(hi2[2])
    print(f"[evidence] {a.character} {a.stance} height {Hs:.3f} m")
    for yaw in (30, 150, 270):
        place(cam, (0, 0, Hs * 0.5), Hs * 2.3, yaw, 10)
        paths.append(render(os.path.join(tiles, f"stance_{yaw}.png")))
        labels.append(f"{a.stance} yaw {yaw}")
    place(cam, (0, -0.1, Hs * 0.72), Hs * 1.05, 25, 8)
    paths.append(render(os.path.join(tiles, "closeup.png")))
    labels.append(f"{a.stance} close-up")
    # gameplay camera: pitch 54, vfov 40, distances 16 (default) and 24 (max zoom); crop = in-game pixels at 1080p
    for dist, yaw in ((16, 0), (16, 150), (24, 30)):
        place(cam, (0, 0, 1.1), dist, 0, 54, fov=40)
        arm.rotation_euler.z = math.radians(yaw)
        p = render(os.path.join(tiles, f"game_{dist}_{yaw}.png"), res=1080)
        crop_center(p, a.res)
        paths.append(p)
        labels.append(f"game cam {dist} m, facing {yaw} (1:1 px @1080p)")
    arm.rotation_euler.z = 0
    bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = a.res
    if ref:
        ref["mesh"].hide_render = False
        set_action(ref["armature"], ref["actions"]["idle"], 0)
        arm.location.x = 0.9 if H < 2.3 else 1.4
        ref["armature"].location.x = -0.7 if H < 2.3 else -1.0
        set_action(arm, res["actions"][a.stance], 0)
        place(cam, (0.2, 0, max(H, 2) * 0.5), max(H, 2.0) * 2.6, 15, 6)
        paths.append(render(os.path.join(tiles, "lineup.png")))
        labels.append(f"lineup: {a.ref} (left) vs {a.character}")
        place(cam, (0.2, 0, 1.1), 16, 0, 54, fov=40)
        p = render(os.path.join(tiles, "lineup_game.png"), res=1080)
        crop_center(p, a.res)
        paths.append(p)
        labels.append("lineup at game cam 16 m (1:1 px)")
    out = os.path.join(a.out, f"{a.character}_rest_iso.png")
    compose(paths, labels, out, 4, f"{a.character}: rest / stance / gameplay camera (height {H:.2f} m)", cell=a.res)


def mode_clips(a, tiles):
    clips = [c for c in a.clips.split(",") if c]
    res = build(a.character, clips)
    arm, mesh = res["armature"], res["mesh"]
    material_colors()
    cam = setup(a.res)
    lo, hi = mesh_bounds(mesh)
    H = float(hi[2])
    frames = [float(f) for f in a.frames.split(",")]
    paths, labels = [], []
    for c in clips:
        act = res["actions"].get(c)
        if act is None:
            print("[evidence] missing clip", c)
            continue
        n = int(act.frame_range[1])
        for fr in frames:
            f = int(round(fr * n))
            set_action(arm, act, f)
            place(cam, (0, -0.2, H * 0.42), H * 2.45, 35, 14)
            paths.append(render(os.path.join(tiles, f"{c}_{f}.png")))
            labels.append(f"{c}  f{f}/{n}")
    out = os.path.join(a.out, f"{a.character}_clips{a.tag}.png")
    compose(paths, labels, out, len(frames), f"{a.character}: clips (3/4 view)", cell=a.res)


def mode_audit(a, tiles):
    """Skin deformation audit. For every edge >= 1 cm: stretch = evaluated / rest length (> 1 elongated) and squash =
    rest / evaluated; plus the largest absolute change in cm. The dominant vertex group of the worst edge names the
    region. Exploding / mis-weighted vertices show up as large stretch AND large absolute change."""
    import build_chars as BC
    cm = BC.char_module(a.character)
    keep = BC.clip_filter(cm)
    res = BC.build_character(a.character, with_actions=True, only=keep)
    arm, mesh = res["armature"], res["mesh"]
    me = mesh.data
    E = np.empty(len(me.edges) * 2, dtype=np.int64)
    me.edges.foreach_get("vertices", E)
    E = E.reshape(-1, 2)
    co0 = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co0)
    co0 = co0.reshape(-1, 3)
    L0 = np.linalg.norm(co0[E[:, 0]] - co0[E[:, 1]], axis=1)
    ok = L0 >= 0.01
    E, L0 = E[ok], L0[ok]
    gnames = {g.index: g.name for g in mesh.vertex_groups}
    dom = []
    for v in me.vertices:
        best = max(v.groups, key=lambda g: g.weight, default=None)
        dom.append(gnames[best.group] if best else "-")
    lines = [f"{a.character}: {len(me.vertices)} verts, {M_tris(mesh)} tris, {len(E)} edges >= 1 cm audited; "
             f"stretch = evaluated/rest, squash = rest/evaluated, dL = largest absolute edge change"]
    tot = dict(st=0.0, sq=0.0, dl=0.0)
    for name in sorted(res["actions"]):
        act = res["actions"][name]
        n0, n1 = int(act.frame_range[0]), int(act.frame_range[1])
        st = sq = dl = 0.0
        where = ""
        zmin = 9.0
        for f in range(n0, n1 + 1):
            set_action(arm, act, f)
            dg = bpy.context.evaluated_depsgraph_get()
            ev = mesh.evaluated_get(dg)
            m2 = ev.to_mesh()
            co = np.empty(len(m2.vertices) * 3)
            m2.vertices.foreach_get("co", co)
            ev.to_mesh_clear()
            co = co.reshape(-1, 3)
            L = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1)
            r = L / L0
            i = int(np.argmax(r))
            if r[i] > st:
                st = float(r[i])
                mid = (co0[E[i, 0]] + co0[E[i, 1]]) / 2
                where = f"{dom[E[i, 0]]} f{f} @({mid[0]:+.2f},{mid[1]:+.2f},{mid[2]:.2f})"
            sq = max(sq, float((L0 / np.maximum(L, 1e-6)).max()))
            dl = max(dl, float(np.abs(L - L0).max()))
            zmin = min(zmin, float(co[:, 2].min()))
        tot["st"] = max(tot["st"], st)
        tot["sq"] = max(tot["sq"], sq)
        tot["dl"] = max(tot["dl"], dl)
        lines.append(f"  {name:14s} {n1 - n0 + 1:3d} fr  stretch {st:4.2f} ({where:34s}) squash {sq:4.2f}  "
                     f"dL {dl * 100:5.1f} cm  lowest z {zmin:+.2f} m")
    lines.append(f"worst over all clips: stretch {tot['st']:.2f}x, squash {tot['sq']:.2f}x, dL {tot['dl'] * 100:.1f} cm")
    out = os.path.join(a.out, f"{a.character}_audit.txt")
    with open(out, "w") as f:
        f.write(NL.join(lines) + NL)
    print(NL.join(lines))


def M_tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def mode_tint(a, tiles):
    res = build(a.character, [a.stance])
    arm, mesh = res["armature"], res["mesh"]
    set_action(arm, res["actions"][a.stance], 0)
    cam = setup(a.res)
    lo, hi = mesh_bounds(mesh)
    H = float(hi[2])
    paths, labels = [], []
    tints = [("as exported (neutral)", None), ("fire", (1.0, 0.35, 0.08)), ("frost", (0.35, 0.75, 1.0)),
             ("storm", (1.0, 0.9, 0.3)), ("poison", (0.45, 1.0, 0.3))]
    em = [m for m in bpy.data.materials if m.name.startswith("BH_Emissive")]
    for lab, col in tints:
        material_colors()
        if col:
            for m in em:
                m.diffuse_color = (*col, 1)
        place(cam, (0, 0, H * 0.55), H * 1.9, 20, 12)
        paths.append(render(os.path.join(tiles, f"tint_{lab.split()[0]}.png")))
        labels.append(f"BH_Emissive -> {lab}")
    out = os.path.join(a.out, f"{a.character}_tint.png")
    compose(paths, labels, out, 5, f"{a.character}: runtime rune recolour check (only BH_Emissive changes)", cell=a.res)


def main():
    a = args()
    os.makedirs(a.out, exist_ok=True)
    tiles = os.environ.get("BH_SCRATCH") or os.path.join(a.out, "_tiles")
    tiles = os.path.join(tiles, a.character, a.mode)
    os.makedirs(tiles, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    {"rest": mode_rest, "clips": mode_clips, "audit": mode_audit, "tint": mode_tint}[a.mode](a, tiles)


if __name__ == "__main__":
    main()
