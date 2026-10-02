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
    V, T, UV, W = refine(V, T, UV, W, chest_triangles(V, T))
    return dict(V=V, T=T, UV=UV, W=W, joints=joints, parent=parent)


def chest_triangles(V, T):
    """bh-031: the front of the chest, where the female shape key forms a bust (source space: 1.70 m, facing -Y)."""
    h = float(V[:, 2].max())
    c = V[T].mean(1)
    zr = c[:, 2] / h
    return (zr > 0.62) & (zr < 0.83) & (np.abs(c[:, 0]) < 0.15 * h) & (c[:, 1] < 0.03)


def refine(V, T, UV, W, mark):
    """Split the marked triangles 1 -> 4 (edge midpoints) and their neighbours 1 -> 2 / 3, so no crack opens at the
    border of the refined patch. UVs are per corner (seams survive), weights are averaged at the new vertices."""
    n0 = len(V)
    mids = {}

    def mid(a, b):
        k = (a, b) if a < b else (b, a)
        if k not in mids:
            mids[k] = n0 + len(mids)
        return mids[k]
    for t in np.where(mark)[0]:
        a, b, c = T[t]
        mid(a, b), mid(b, c), mid(c, a)
    if not mids:
        return V, T, UV, W
    keys = list(mids)
    newV = np.array([(V[a] + V[b]) * 0.5 for a, b in keys])
    W = {k: np.concatenate([w, np.array([(w[a] + w[b]) * 0.5 for a, b in keys])]) for k, w in W.items()}
    outT, outUV = [], []
    for t in range(len(T)):
        tri, uv = T[t], UV[t]
        e = []
        for i in range(3):
            a, b = int(tri[i]), int(tri[(i + 1) % 3])
            k = (a, b) if a < b else (b, a)
            e.append(mids.get(k))
        cnt = sum(x is not None for x in e)
        if cnt == 0:
            outT.append(tri)
            outUV.append(uv)
            continue
        P = [int(tri[0]), int(tri[1]), int(tri[2])]
        Q = [uv[0], uv[1], uv[2]]
        M = [e[i] for i in range(3)]
        MQ = [(uv[i] + uv[(i + 1) % 3]) * 0.5 for i in range(3)]
        if cnt == 3:
            for f in ((P[0], M[0], M[2], Q[0], MQ[0], MQ[2]), (P[1], M[1], M[0], Q[1], MQ[1], MQ[0]),
                      (P[2], M[2], M[1], Q[2], MQ[2], MQ[1]), (M[0], M[1], M[2], MQ[0], MQ[1], MQ[2])):
                outT.append(f[:3])
                outUV.append(f[3:])
            continue
        # rotate so the first split edge is edge 0 (P0-P1)
        r = next(i for i in range(3) if M[i] is not None)
        P, Q, M, MQ = P[r:] + P[:r], Q[r:] + Q[:r], M[r:] + M[:r], MQ[r:] + MQ[:r]
        if cnt == 1:
            outT += [(P[0], M[0], P[2]), (M[0], P[1], P[2])]
            outUV += [(Q[0], MQ[0], Q[2]), (MQ[0], Q[1], Q[2])]
        elif M[1] is not None:          # edges 0 and 1 split
            outT += [(P[0], M[0], P[2]), (M[0], M[1], P[2]), (M[0], P[1], M[1])]
            outUV += [(Q[0], MQ[0], Q[2]), (MQ[0], MQ[1], Q[2]), (MQ[0], Q[1], MQ[1])]
        else:                            # edges 0 and 2 split
            outT += [(P[0], M[0], M[2]), (M[0], P[2], M[2]), (M[0], P[1], P[2])]
            outUV += [(Q[0], MQ[0], MQ[2]), (MQ[0], Q[2], MQ[2]), (MQ[0], Q[1], Q[2])]
    print("[hero] refined %d chest triangles: %d -> %d verts" % (int(mark.sum()), n0, n0 + len(keys)))
    return np.vstack([V, newV]), np.array(outT, dtype=int), np.array(outUV, dtype=float), W
