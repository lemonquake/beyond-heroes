"""bh-023: build the player's hero body (game/assets/characters/hero.glb) from models/generic_body*.

  blender -b --factory-startup --python tools/blender/hero/hero_body.py -- [preview] [export] [--clips a,b,c]

  preview   renders of the rest pose and a few library poses -> work/lemondev/bh-023/scratch/
  export    hero.glb: the body skinned to the shared skeleton, shape keys (hero_shapes), every library clip plus the
            five source clips retargeted (hero_retarget), and the skin textures (hero_skin)
"""
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CHARS = os.path.abspath(os.path.join(HERE, "..", "characters"))
for p in (HERE, CHARS):
    if p not in sys.path:
        sys.path.insert(0, p)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT_DIR = os.path.join(ROOT, "game", "assets", "characters")
SCRATCH = os.path.join(ROOT, "work", "lemondev", "bh-023", "scratch")

import bpy  # noqa: E402

import bh_anim as A  # noqa: E402
import bh_skeleton as S  # noqa: E402
import hero_conform as HC  # noqa: E402
import hero_src as HS  # noqa: E402

DEFORM = [b for b in S.BONE_ORDER if b not in S.DEFORM_EXCLUDE]


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)


def make_mesh(name, V, T, UV):
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], T.tolist())
    me.validate(clean_customdata=False)
    uvl = me.uv_layers.new(name="UVMap")
    flat = UV.reshape(-1, 2)
    uvl.data.foreach_set("uv", flat.ravel())
    me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def auto_weights(ob, arm):
    """Heat weights from the shared armature; returns {bone: (n,)} normalised over the deform bones."""
    for o in bpy.context.scene.objects:
        o.select_set(False)
    ob.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    n = len(ob.data.vertices)
    names = {g.index: g.name for g in ob.vertex_groups}
    W = {b: np.zeros(n) for b in DEFORM}
    for v in ob.data.vertices:
        for g in v.groups:
            nm = names[g.group]
            if nm in W:
                W[nm][v.index] = g.weight
    return W


def mapped_weights(src_w):
    """The source rig's own weights carried to the shared bone names (fallback, and the hands / feet authority)."""
    m = {"Hips": "hips", "Spine02": "spine", "Spine01": "chest", "Spine": "chest", "neck": "neck", "Head": "head",
         "head_end": "head", "headfront": "head"}
    for side, k in (("L", "Left"), ("R", "Right")):
        m.update({k + "Shoulder": "shoulder." + side, k + "Arm": "upper_arm." + side, k + "ForeArm": "forearm." + side,
                  k + "Hand": "hand." + side, k + "Hand_End": "hand." + side, k + "UpLeg": "thigh." + side,
                  k + "Leg": "shin." + side, k + "Foot": "foot." + side, k + "ToeBase": "toe." + side,
                  k + "Toe_end": "toe." + side})
    n = len(next(iter(src_w.values())))
    W = {b: np.zeros(n) for b in DEFORM}
    for k, w in src_w.items():
        W[m[k]] += w
    return W


def smooth_weights(W, T, iters=2, keep=None):
    """Laplacian smoothing over the mesh edges (keep: bool mask of vertices left untouched)."""
    n = len(next(iter(W.values())))
    nb = [set() for _ in range(n)]
    for a, b, c in T:
        nb[a].update((b, c))
        nb[b].update((a, c))
        nb[c].update((a, b))
    idx = [np.fromiter(s, int) for s in nb]
    for _ in range(iters):
        for k in W:
            w = W[k]
            new = np.array([0.5 * w[i] + 0.5 * w[idx[i]].mean() if len(idx[i]) else w[i] for i in range(n)])
            if keep is not None:
                new[keep] = w[keep]
            W[k] = new
    return W


def finish_weights(W, top=4):
    names = list(W)
    M = np.stack([W[k] for k in names], 1)
    order = np.argsort(-M, 1)
    mask = np.zeros_like(M, bool)
    np.put_along_axis(mask, order[:, :top], True, 1)
    M = np.where(mask, M, 0.0)
    M[M < 0.01] = 0.0
    M = M / np.maximum(M.sum(1, keepdims=True), 1e-9)
    return {k: M[:, i] for i, k in enumerate(names)}


def set_groups(ob, W):
    for g in list(ob.vertex_groups):
        ob.vertex_groups.remove(g)
    for b in S.BONE_ORDER:
        if b not in W:
            continue
        g = ob.vertex_groups.new(name=b)
        w = W[b]
        for i in np.nonzero(w > 0)[0]:
            g.add([int(i)], float(w[i]), "REPLACE")


def body_weights(ob, arm, src, V):
    """Heat weights, with the source rig's weights deciding the rigid ends (fists, feet) and the head."""
    J = S.joints(HC.PROPS)
    mw = mapped_weights(src["W"])
    try:
        W = auto_weights(ob, arm)
        ok = all(np.isfinite(w).all() for w in W.values()) and sum(W.values()).min() > 0.05
    except Exception as e:      # heat weighting can fail on a non-manifold mesh
        print("[hero] heat weights failed:", e)
        ok = False
    if not ok:
        print("[hero] using the source rig's weights")
        W = mw
        ob.parent = arm
        if not any(m.type == "ARMATURE" for m in ob.modifiers):
            ob.modifiers.new("Armature", "ARMATURE").object = arm
    tot = sum(W.values())
    for k in W:
        W[k] = W[k] / np.maximum(tot, 1e-9)
    keep = np.zeros(len(V), bool)
    for side, sx in (("L", 1.0), ("R", -1.0)):
        # the fist is one rigid block from just past the wrist
        wrist = J["hand." + side][0][0] * sx
        t = np.clip((V[:, 0] * sx - (wrist - 0.015)) / 0.05, 0.0, 1.0)
        for k in W:
            W[k] = W[k] * (1.0 - t)
        W["hand." + side] = W["hand." + side] + t
        keep |= t >= 1.0
    # the skull is rigid: above the jaw line everything follows the head bone
    hz = J["head"][0][2]
    t = np.clip((V[:, 2] - (hz - 0.02)) / 0.05, 0.0, 1.0) * (np.abs(V[:, 0]) < 0.14)
    for k in W:
        W[k] = W[k] * (1.0 - t)
    W["head"] = W["head"] + t
    keep |= t >= 1.0
    W = smooth_weights(W, src["T"], 2, keep)
    W = finish_weights(W)
    set_groups(ob, W)
    return W


def build_body(log=print):
    """-> dict(ob, arm, rig, src, V, W): the conformed, skinned body in a fresh scene."""
    reset()
    t0 = time.time()
    src = HS.load()
    V, info = HC.conform(src)
    V = HC.make_fists(V, src["W"])
    arm, J = S.build_armature(HC.PROPS, "Armature")
    ob = make_mesh("hero", V, src["T"], src["UV"])
    W = body_weights(ob, arm, src, V)
    log("[hero] body %d verts, %d tris, %.1fs" % (len(V), len(src["T"]), time.time() - t0))
    return dict(ob=ob, arm=arm, rig=A.Rig(HC.PROPS), src=src, V=V, W=W, info=info)


# ---- preview -------------------------------------------------------------------------------------------------------

def _preview_material(ob):
    mat = bpy.data.materials.new("hero_preview")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(HS.SRC_TEX)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.7
    ob.data.materials.clear()
    ob.data.materials.append(mat)


def _stage():
    from mathutils import Vector
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.2, 0.21, 0.25, 1)
    bg.inputs[1].default_value = 1.0
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sc.collection.objects.link(sun)
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"

    def shot(path, loc, target, scale, res=(900, 1200)):
        sc.render.resolution_x, sc.render.resolution_y = res
        cam.location = loc
        cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        cam.data.ortho_scale = scale
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
    return shot


def preview(clips=("idle", "run", "sword_2", "cast_heavy", "block_loop", "death")):
    import bh_library as L
    r = build_body()
    ob, arm, rig = r["ob"], r["arm"], r["rig"]
    _preview_material(ob)
    shot = _stage()
    os.makedirs(SCRATCH, exist_ok=True)
    shot(os.path.join(SCRATCH, "hero_rest_front.png"), (0, -6, 0.92), (0, 0, 0.92), 2.0)
    shot(os.path.join(SCRATCH, "hero_rest_side.png"), (6, 0, 0.92), (0, 0, 0.92), 2.0)
    shot(os.path.join(SCRATCH, "hero_rest_back.png"), (0, 6, 0.92), (0, 0, 0.92), 2.0)
    shot(os.path.join(SCRATCH, "hero_hand.png"), (0.9, -2.0, 2.2), (0.78, 0, 1.43), 0.4, (900, 700))
    lib = {a.name: a for a in L.library()}
    for cn in clips:
        an = lib[cn]
        act = A.bake_action(arm, rig, an)
        A.assign_action(arm, act)
        for f in sorted({0, an.length // 3, (2 * an.length) // 3}):
            bpy.context.scene.frame_set(f)
            shot(os.path.join(SCRATCH, "hero_%s_%02d.png" % (cn, f)), (3.2, -5.0, 1.5), (0, 0, 0.95), 2.3, (800, 900))


def add_shapes(ob, V, T):
    import hero_shapes as SH
    keys = SH.shape_keys(V, T)
    ob.shape_key_add(name="Basis")
    for name, d in keys.items():
        kb = ob.shape_key_add(name=name)
        kb.data.foreach_set("co", (V + d).ravel())
        kb.slider_min, kb.slider_max = -3.0, 6.0
        kb.value = 0.0
    return keys


def preview_shapes():
    import hero_shapes as SH
    r = build_body()
    ob = r["ob"]
    _preview_material(ob)
    keys = add_shapes(ob, r["V"], r["src"]["T"])
    shot = _stage()
    kbs = ob.data.shape_keys.key_blocks
    for name in keys:
        for val in ((1.0, 2.5, -1.0) if name in SH.FACE_KEYS else (1.0, 2.0, -1.0)):
            for kb in kbs:
                kb.value = 0.0
            kbs[name].value = val
            tag = "%s_%s" % (name, ("p%d" % int(val * 10)) if val > 0 else "m10")
            if name in SH.FACE_KEYS:
                shot(os.path.join(SCRATCH, "sk_%s.png" % tag), (2.6, -5.0, 1.78), (0, -0.04, 1.675), 0.34, (500, 500))
            else:
                shot(os.path.join(SCRATCH, "sk_%s.png" % tag), (3.2, -5.0, 1.5), (0, 0, 0.95), 2.0, (500, 620))


def preview_retarget():
    import hero_retarget as RT
    r = build_body()
    ob, arm = r["ob"], r["arm"]
    _preview_material(ob)
    shot = _stage()
    # a floor line to judge foot contact
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    for name, (src_action, loop) in RT.CLIPS.items():
        rt = RT.retarget(RT.sample(src_action), r["info"], loop)
        act = RT.bake(arm, name, rt, loop)
        A.assign_action(arm, act)
        n = rt["n"]
        for i in range(6):
            f = int(round(i * (n - 1) / 6.0))
            bpy.context.scene.frame_set(f)
            shot(os.path.join(SCRATCH, "rt_%s_%d.png" % (name, i)), (5.5, -2.2, 1.0), (0, 0, 0.92), 2.4, (560, 640))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "preview" in argv:
        preview()
    if "shapes" in argv:
        preview_shapes()
    if "retarget" in argv:
        preview_retarget()
    if "export" in argv:
        import hero_export
        hero_export.export(argv)


if __name__ == "__main__":
    main()
