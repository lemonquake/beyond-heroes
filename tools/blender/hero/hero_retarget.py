"""bh-023: the five source clips (models/generic_body_animation) carried onto the shared skeleton.

Each source bone's world rotation away from its own rest pose is applied to the matching shared bone, corrected by
the rotation hero_conform used to bring that limb onto the standard rest pose; so a source forearm pointing at the
ground still points at the ground on the shared rig. The hips' travel is scaled by the leg-length ratio (feet keep
reaching the floor) and any forward drift is removed (the game moves the hero; clips play in place).
"""
import os

import numpy as np

import bh_skeleton as S
import hero_src as HS
from bh_math import mat_to_quat

FPS = 30
BONE_MAP = {"hips": "Hips", "spine": "Spine02", "chest": "Spine", "neck": "neck", "head": "Head"}
for _side, _k in (("L", "Left"), ("R", "Right")):
    BONE_MAP.update({"shoulder." + _side: _k + "Shoulder", "upper_arm." + _side: _k + "Arm", "forearm." + _side: _k + "ForeArm",
                     "hand." + _side: _k + "Hand", "thigh." + _side: _k + "UpLeg", "shin." + _side: _k + "Leg",
                     "foot." + _side: _k + "Foot", "toe." + _side: _k + "ToeBase"})

# game clip name -> (source action, loops)
CLIPS = {
    "hero_walk": ("Walking", True), "hero_run": ("Running", True), "hero_stroll": ("Casual_Walk", True),
    "hero_alert": ("Alert", True), "hero_axe_smash": ("Attack", False),
}


def _orthonormal(M):
    u, _, vt = np.linalg.svd(M)
    R = u @ vt
    if np.linalg.det(R) < 0:
        u[:, -1] *= -1
        R = u @ vt
    return R


def sample(action_name):
    """-> dict(n, delta {src bone: (n,3,3)}, hips (n,3)) sampled at 30 fps in armature space."""
    import bpy
    sc = bpy.context.scene
    sc.render.fps = FPS
    arm, mesh = HS.import_glb(os.path.join(HS.SRC_DIR, "generic_body_animation", HS.ANIMS[action_name]))
    act = arm.animation_data.action
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    rest = {b.name: np.array(b.matrix_local) for b in arm.data.bones}
    n = f1 - f0 + 1
    delta = {b: np.zeros((n, 3, 3)) for b in rest}
    hips = np.zeros((n, 3))
    for i, f in enumerate(range(f0, f1 + 1)):
        sc.frame_set(f)
        for pb in arm.pose.bones:
            Mp = np.array(pb.matrix)
            delta[pb.name][i] = _orthonormal(Mp[:3, :3] @ rest[pb.name][:3, :3].T)
            if pb.name == "Hips":
                hips[i] = Mp[:3, 3] - rest["Hips"][:3, 3]
    bpy.data.objects.remove(mesh)
    bpy.data.objects.remove(arm)
    bpy.data.actions.remove(act)
    return dict(n=n, delta=delta, hips=hips)


def retarget(clip, info, loop):
    """-> dict(n, Wq {bh bone: (n,3,3) world delta}, t (n,3) hips offset, feet {side: (n,3)}) on the shared rig."""
    J = info["J"]
    A = info["R"]
    n = clip["n"]
    W = {"root": np.repeat(np.eye(3)[None], n, 0)}
    for b in S.BONE_ORDER:
        if b in BONE_MAP:
            sb = BONE_MAP[b]
            W[b] = clip["delta"][sb] @ A[sb].T
        elif b != "root":
            W[b] = W[S.PARENT[b]].copy()
    # leg-length ratio: shared legs are longer than the source's
    Js = info["Js"]
    src_leg = np.linalg.norm(Js["LeftUpLeg"][0] - Js["LeftLeg"][0]) + np.linalg.norm(Js["LeftLeg"][0] - Js["LeftFoot"][0])
    bh_leg = np.linalg.norm(J["thigh.L"][0] - J["shin.L"][0]) + np.linalg.norm(J["shin.L"][0] - J["foot.L"][0])
    k = bh_leg / src_leg
    t = clip["hips"] * info["scale"] * k
    if loop:
        # in place: remove the travel (a straight line through the horizontal drift)
        ramp = np.linspace(0.0, 1.0, n)[:, None]
        t[:, :2] -= t[:1, :2] + ramp * (t[-1:, :2] - t[:1, :2])
        t[:, :2] -= t[:, :2].mean(0)
    else:
        t[:, :2] -= t[:1, :2]
    # forward kinematics: where the feet end up (to keep them on the floor and measure the ground speed)
    pos = fk(W, t, J)
    low = np.minimum.reduce([pos[b][:, 2] for b in ("foot.L", "foot.R", "toe.L", "toe.R")] +
                            [pos["toe_tip." + s][:, 2] for s in "LR"])
    floor = min(J["toe.L"][0][2], J["toe.L"][1][2])
    sink = np.minimum(low - floor, 0.0)                      # below the floor: lift the hips by that much
    t[:, 2] -= _smooth(sink, 2, loop)
    pos = fk(W, t, J)
    return dict(n=n, W=W, t=t, pos=pos, J=J)


def retime(rt, src_hit, dst_len, dst_hit):
    """Warp a one-shot clip in time so its strike lands on frame `dst_hit` of a `dst_len`-frame clip (frames at 30
    fps): the wind-up and the recovery are each stretched or squeezed evenly. The game times an attack's damage by
    the clip it replaces, so the replacement must strike at the same moment."""
    n = rt["n"]
    out_n = dst_len + 1
    src = np.empty(out_n)
    for f in range(out_n):
        if f <= dst_hit:
            src[f] = src_hit * f / max(dst_hit, 1)
        else:
            src[f] = src_hit + (n - 1 - src_hit) * (f - dst_hit) / max(dst_len - dst_hit, 1)
    i0 = np.clip(np.floor(src).astype(int), 0, n - 1)
    i1 = np.clip(i0 + 1, 0, n - 1)
    u = (src - i0)[:, None, None]
    W = {}
    for b, M in rt["W"].items():
        R = M[i0] * (1 - u) + M[i1] * u
        W[b] = np.stack([_orthonormal(r) for r in R], 0)
    t = rt["t"][i0] * (1 - u[:, :, 0]) + rt["t"][i1] * u[:, :, 0]
    return dict(n=out_n, W=W, t=t)


def _smooth(x, r, loop):
    out = np.zeros_like(x)
    n = len(x)
    for i in range(n):
        idx = [(i + d) % n if loop else min(max(i + d, 0), n - 1) for d in range(-r, r + 1)]
        out[i] = x[idx].min()
    return out


def fk(W, t, J):
    n = len(t)
    pos = {"root": np.zeros((n, 3))}
    for b in S.BONE_ORDER:
        if b == "root":
            continue
        p = S.PARENT[b]
        if b == "hips":
            pos[b] = J["hips"][0][None] + t
        else:
            off = J[b][0] - J[p][0]
            pos[b] = pos[p] + np.einsum("nij,j->ni", W[p], off)
    for s in "LR":
        pos["toe_tip." + s] = pos["toe." + s] + np.einsum("nij,j->ni", W["toe." + s], J["toe." + s][1] - J["toe." + s][0])
        pos["tip." + s] = pos["weapon." + s] + np.einsum("nij,j->ni", W["weapon." + s], np.array([0.0, -0.8, 0.0]))
    return pos


def bake(arm_ob, name, rt, loop):
    """Write the retargeted clip as an action on the shared armature (same layout as bh_anim.bake_action)."""
    import bpy
    Rb = {b.name: np.array(b.matrix_local)[:3, :3] for b in arm_ob.data.bones}
    n = rt["n"]
    W = rt["W"]
    quats = {}
    for b in Rb:
        q = np.zeros((n, 4))
        for f in range(n):
            if b in W and b != "root":
                Ql = W[S.PARENT[b]][f].T @ W[b][f]
            else:
                Ql = np.eye(3)
            qq = mat_to_quat(Rb[b].T @ Ql @ Rb[b])
            if f > 0 and np.dot(qq, q[f - 1]) < 0:
                qq = -qq
            q[f] = qq
        quats[b] = q
    locs = rt["t"] @ Rb["hips"]
    if loop:                 # close the loop exactly
        for b in quats:
            quats[b][-1] = quats[b][0] if np.dot(quats[b][-1], quats[b][0]) > 0 else -quats[b][0]
        locs[-1] = locs[0]
    act = bpy.data.actions.get(name)
    if act:
        bpy.data.actions.remove(act)
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    slot = act.slots.new(id_type="OBJECT", name=arm_ob.name)
    layer = act.layers.new("Layer")
    strip = layer.strips.new(type="KEYFRAME")
    cb = strip.channelbag(slot, ensure=True)
    frames = np.arange(n, dtype=float)

    def put(path, idx, vals, group):
        fc = cb.fcurves.new(path, index=idx, group_name=group)
        fc.keyframe_points.add(n)
        co = np.empty(2 * n)
        co[0::2] = frames
        co[1::2] = vals
        fc.keyframe_points.foreach_set("co", co)
        fc.keyframe_points.foreach_set("interpolation", [1] * n)
        fc.update()

    for b in quats:
        for i in range(4):
            put('pose.bones["%s"].rotation_quaternion' % b, i, quats[b][:, i], b)
    for i in range(3):
        put('pose.bones["hips"].location', i, locs[:, i], "hips")
    act.use_frame_range = True
    act.frame_start = 0
    act.frame_end = n - 1
    act.use_cyclic = bool(loop)
    return act


def measure(rt, loop, hit=False):
    """Metadata in the anim_meta.json schema: length, loop, ground speed and footsteps (gaits), hit window (attacks)."""
    n = rt["n"]
    out = {"length": round((n - 1) / FPS, 3), "loop": bool(loop)}
    pos = rt["pos"]
    if loop:
        speeds, steps = [], []
        for s in "LR":
            sole = np.minimum(pos["foot." + s][:, 2], pos["toe." + s][:, 2])
            planted = sole < sole.min() + 0.02
            v = np.gradient(pos["toe." + s][:, 1]) * FPS          # +y = backwards: a planted foot slides back
            if planted.sum() >= 2:
                speeds.append(float(np.median(v[planted])))
            starts = [f for f in range(n - 1) if planted[f] and not planted[f - 1]]
            steps += [round(f / FPS, 3) for f in starts[:1]]
        gs = float(np.mean(speeds)) if speeds else 0.0
        if gs > 0.3:
            out["ground_speed"] = round(gs, 3)
            out["footsteps"] = sorted(steps)
            out["direction_deg"] = 0.0
    if hit:
        tip = pos["tip.R"]
        v = np.linalg.norm(np.gradient(tip, axis=0), axis=1) * FPS
        pk = int(v.argmax())
        a = pk
        while a > 0 and v[a - 1] >= 0.55 * v[pk]:
            a -= 1
        b = pk
        while b < n - 1 and v[b + 1] >= 0.55 * v[pk]:
            b += 1
        out["hits"] = [[round(a / FPS, 3), round(max(b, a + 2) / FPS, 3)]]
        out["tip_speed_peak"] = round(float(v[pk]), 2)
        out["cancel_after"] = round(min((b + 12) / FPS, (n - 1) / FPS), 3)
        out["props"] = {"R": "axe", "L": None}
    return out
