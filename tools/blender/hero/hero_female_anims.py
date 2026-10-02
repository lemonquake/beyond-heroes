"""bh-031: the female body's own idle and gaits, layered over the hero's clips on the shared skeleton.

The female body (shape key "female") plays every library clip like the hero does. Out of combat she stands and walks
in her own clips (CharacterVisual picks fem_<clip> over hero_<clip> for a female look):

  fem_idle    the library idle with the weight on one leg: the pelvis tilts up on the standing side, the shoulders
              answer it, the free knee relaxes, the arms hang closer
  fem_walk    hero_walk with the pelvis swaying (it rises over the standing leg and turns with the stepping one), the
              shoulders counter-turning, feet stepping nearer one line and the arms swinging closer to the body
  fem_stroll  the same over hero_stroll, gentler
  fem_run     the same over hero_run, smaller

Clips are in the retarget format (hero_retarget: world rotation deltas W per bone, hips offset t), so they are baked
and measured exactly like the hero's own clips. After the layers are added the lowest foot is put back on the floor
every frame (gaits with a flight phase are only lifted out of the floor).
"""
import numpy as np

import bh_skeleton as S
import hero_retarget as RT


def _subtree(root):
    out = [root]
    for b in S.BONE_ORDER:
        p = S.PARENT.get(b)
        if p in out and b not in out:
            out.append(b)
    return out


def _rx(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[np.ones_like(a), 0 * a, 0 * a], [0 * a, c, -s], [0 * a, s, c]]).transpose(2, 0, 1)


def _ry(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0 * a, s], [0 * a, np.ones_like(a), 0 * a], [-s, 0 * a, c]]).transpose(2, 0, 1)


def _rz(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0 * a], [s, c, 0 * a], [0 * a, 0 * a, np.ones_like(a)]]).transpose(2, 0, 1)


def _turn(W, root, R):
    """Rotate the subtree from `root` by the per-frame world rotations R (n,3,3) about that bone's joint."""
    for b in _subtree(root):
        if b in W:
            W[b] = np.einsum("nij,njk->nik", R, W[b])


def _cyc_smooth(x, r, loop=True):
    n = len(x)
    out = np.zeros_like(x)
    for d in range(-r, r + 1):
        out += np.roll(x, d) if loop else x[np.clip(np.arange(n) + d, 0, n - 1)]
    return out / (2 * r + 1)


def _copy(rt):
    return dict(n=rt["n"], W={b: m.copy() for b, m in rt["W"].items()}, t=rt["t"].copy(), J=rt["J"])


def _floor(rt, both_ways):
    J = rt["J"]
    pos = RT.fk(rt["W"], rt["t"], J)
    low = np.minimum.reduce([pos[b][:, 2] for b in ("foot.L", "foot.R", "toe.L", "toe.R")] +
                            [pos["toe_tip." + s][:, 2] for s in "LR"])
    floor = min(J["toe.L"][0][2], J["toe.L"][1][2])
    off = low - floor
    if not both_ways:
        off = np.minimum(off, 0.0)
    rt["t"][:, 2] -= _cyc_smooth(off, 1)
    rt["pos"] = RT.fk(rt["W"], rt["t"], J)
    return rt


def gait(rt, roll=5.0, yaw=7.0, chest=0.75, adduct=3.0, arms=5.0, both_ways=True):
    """Layer a woman's walk over a gait clip (angles in degrees)."""
    out = _copy(rt)
    pos = RT.fk(rt["W"], rt["t"], rt["J"])
    n = rt["n"]
    sole = {s: np.minimum(pos["foot." + s][:, 2], pos["toe." + s][:, 2]) for s in "LR"}
    # 1 while the left foot carries the weight, 0 while the right does
    stance_l = 1.0 / (1.0 + np.exp(-(sole["R"] - sole["L"]) / 0.012))
    stance_l = _cyc_smooth(stance_l, 2)
    side = 2.0 * stance_l - 1.0
    # which leg is ahead: the pelvis turns with it (-Y is forward)
    lead = pos["toe.R"][:, 1] - pos["toe.L"][:, 1]
    lead = _cyc_smooth(lead / max(np.abs(lead).max(), 1e-6), 2)
    th = np.radians(-roll) * side           # the standing side's hip rises
    ps = np.radians(-yaw) * lead            # the leading leg's hip comes forward
    R = np.einsum("nij,njk->nik", _rz(ps), _ry(th))
    _turn(out["W"], "hips", R)
    # the trunk answers: shoulders counter-turn and counter-tilt (the head stays level)
    Rc = np.einsum("nij,njk->nik", _rz(-chest * ps), _ry(-chest * th))
    _turn(out["W"], "spine", Rc)
    Rn = np.einsum("nij,njk->nik", _rz(-(1 - chest) * ps), _ry(-(1 - chest) * th))
    _turn(out["W"], "neck", Rn)
    # the legs keep pointing where they did (only the pelvis moves) and step nearer one line
    Ri = np.transpose(R, (0, 2, 1))
    for s, sx in (("L", 1.0), ("R", -1.0)):
        _turn(out["W"], "thigh." + s, np.einsum("nij,njk->nik", _ry(np.full(n, np.radians(adduct) * sx)), Ri))
        # arms swing closer to the body
        _turn(out["W"], "upper_arm." + s, _ry(np.full(n, np.radians(arms) * sx)))
    return _floor(out, both_ways)


def idle(rt, roll=4.5, shift_legs=2.2, knee=11.0):
    """Contrapposto over an idle: weight on the left leg, the right knee relaxed."""
    out = _copy(rt)
    n = rt["n"]
    t = np.linspace(0.0, 2.0 * np.pi, n)
    th = np.radians(-roll) * (1.0 + 0.08 * np.sin(t))
    R = _ry(th)
    _turn(out["W"], "hips", R)
    _turn(out["W"], "spine", _ry(-0.8 * th))
    _turn(out["W"], "neck", _ry(-0.25 * th + np.radians(2.0)))
    Ri = np.transpose(R, (0, 2, 1))
    _turn(out["W"], "thigh.L", np.einsum("nij,njk->nik", _ry(np.full(n, np.radians(shift_legs))), Ri))
    # the free leg: thigh a little forward and in, knee bent
    _turn(out["W"], "thigh.R", np.einsum("nij,njk->nik", _rx(np.full(n, np.radians(-5.0))),
                                         np.einsum("nij,njk->nik", _ry(np.full(n, np.radians(-shift_legs * 0.2))), Ri)))
    _turn(out["W"], "shin.R", _rx(np.full(n, np.radians(knee))))
    for s, sx in (("L", 1.0), ("R", -1.0)):
        _turn(out["W"], "upper_arm." + s, _ry(np.full(n, np.radians(4.0) * sx)))
    return _floor(out, True)


def sample_action(arm, act):
    """A baked action on the shared armature -> the retarget format (W, t)."""
    import bpy
    sc = bpy.context.scene
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = act
    try:
        ad.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    rest = {b.name: np.array(b.matrix_local) for b in arm.data.bones}
    n = f1 - f0 + 1
    W = {b: np.zeros((n, 3, 3)) for b in S.BONE_ORDER}
    t = np.zeros((n, 3))
    for i, f in enumerate(range(f0, f1 + 1)):
        sc.frame_set(f)
        for b in S.BONE_ORDER:
            pb = arm.pose.bones.get(b)
            if pb is None:
                W[b][i] = np.eye(3)
                continue
            Mp = np.array(pb.matrix)
            W[b][i] = RT._orthonormal(Mp[:3, :3] @ rest[b][:3, :3].T)
            if b == "hips":
                t[i] = Mp[:3, 3] - rest["hips"][:3, 3]
    ad.action = None
    return dict(n=n, W=W, t=t)


def make(arm, rts, acts, J, log=print):
    """-> {name: (rt, loop)} for the female clips. rts: the hero's retargeted gaits; acts: the baked library."""
    out = {}
    if "hero_walk" in rts:
        out["fem_walk"] = (gait(rts["hero_walk"]), True)
    if "hero_stroll" in rts:
        out["fem_stroll"] = (gait(rts["hero_stroll"], roll=4.0, yaw=6.0, adduct=2.5, arms=6.0), True)
    if "hero_run" in rts:
        out["fem_run"] = (gait(rts["hero_run"], roll=3.0, yaw=5.0, chest=0.6, adduct=2.0, arms=4.0, both_ways=False), True)
    if "idle" in acts:
        base = sample_action(arm, acts["idle"])
        base["J"] = J
        out["fem_idle"] = (idle(base), True)
    log("[hero] female clips: %s" % ", ".join(out))
    return out
