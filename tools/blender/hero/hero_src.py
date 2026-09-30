"""bh-023: the player's generic body (models/generic_body*) read into numpy.

The source is a Tripo export: one mesh skinned to a 28-joint rig, 1.70 m tall, facing -Y, left = +X, a drooping
T-pose with splayed legs and open hands. load() returns it welded, in Blender space (Z up).
"""
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC_DIR = os.path.join(ROOT, "models")
SRC_GLB = os.path.join(SRC_DIR, "generic_body_animation", "animation_alert.glb")
SRC_TEX = os.path.join(SRC_DIR, "generic_body.jpg")
ANIMS = {
    "Alert": "animation_alert.glb", "Attack": "animation_attack_axe_smash.glb", "Casual_Walk": "animation_casual_walk.glb",
    "Running": "animation_run.glb", "Walking": "animation_walk.glb",
}


def import_glb(path):
    """Import a source GLB into the current scene; returns (armature object, body mesh object)."""
    import bpy
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    mesh = max((o for o in new if o.type == "MESH"), key=lambda o: len(o.data.vertices))
    for o in new:      # the importer's bone-shape icosphere
        if o.type == "MESH" and o is not mesh:
            bpy.data.objects.remove(o)
    return arm, mesh


def load():
    """-> dict(V (n,3), T (m,3) vertex ids, UV (m,3,2), W {bone: (n,)}, joints {bone: (head, tail)}, parent {bone: name})."""
    import bmesh
    import bpy
    arm, ob = import_glb(SRC_GLB)
    arm.data.pose_position = "REST"
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    n = len(me.vertices)
    mw = np.array(ob.matrix_world)
    V = np.array([v.co[:] for v in me.vertices]) @ mw[:3, :3].T + mw[:3, 3]
    T = np.array([p.vertices[:] for p in me.polygons], dtype=int)
    uvl = me.uv_layers[0].data
    UV = np.array([[uvl[li].uv[:] for li in p.loop_indices] for p in me.polygons])
    W = {}
    names = {g.index: g.name for g in ob.vertex_groups}
    for v in me.vertices:
        for g in v.groups:
            W.setdefault(names[g.group], np.zeros(n))[v.index] = g.weight
    tot = sum(W.values())
    for k in W:
        W[k] = W[k] / np.maximum(tot, 1e-9)
    aw = np.array(arm.matrix_world)
    joints, parent = {}, {}
    for b in arm.data.bones:
        h = aw[:3, :3] @ np.array(b.head_local) + aw[:3, 3]
        t = aw[:3, :3] @ np.array(b.tail_local) + aw[:3, 3]
        joints[b.name] = (h, t)
        parent[b.name] = b.parent.name if b.parent else None
    bpy.data.objects.remove(ob)
    bpy.data.objects.remove(arm)
    return dict(V=V, T=T, UV=UV, W=W, joints=joints, parent=parent)
