"""Shared humanoid skeleton for Beyond Heroes.

Rest pose: T-pose, character faces -Y (Blender), left = +X, Z up, meters, origin on the ground between the feet.
All humanoids use exactly the same bone names, hierarchy and rest orientations (bone directions + rolls);
only bone lengths/positions change per character (proportions dict).
"""
import numpy as np

BONE_ORDER = [
    "root", "hips", "spine", "chest", "neck", "head",
    "shoulder.L", "upper_arm.L", "forearm.L", "hand.L", "weapon.L",
    "shoulder.R", "upper_arm.R", "forearm.R", "hand.R", "weapon.R",
    "thigh.L", "shin.L", "foot.L", "toe.L",
    "thigh.R", "shin.R", "foot.R", "toe.R",
]

PARENT = {
    "root": None, "hips": "root", "spine": "hips", "chest": "spine", "neck": "chest", "head": "neck",
    "shoulder.L": "chest", "upper_arm.L": "shoulder.L", "forearm.L": "upper_arm.L", "hand.L": "forearm.L",
    "weapon.L": "hand.L",
    "shoulder.R": "chest", "upper_arm.R": "shoulder.R", "forearm.R": "upper_arm.R", "hand.R": "forearm.R",
    "weapon.R": "hand.R",
    "thigh.L": "hips", "shin.L": "thigh.L", "foot.L": "shin.L", "toe.L": "foot.L",
    "thigh.R": "hips", "shin.R": "thigh.R", "foot.R": "shin.R", "toe.R": "foot.R",
}

DEFORM_EXCLUDE = {"root", "weapon.L", "weapon.R"}

# Standard proportions of a 1.8 m human (meters).
STD = dict(
    pelvis_h=0.98,       # hips bone head
    hips_len=0.10,
    spine_len=0.18,
    chest_len=0.22,
    neck_len=0.12,
    head_len=0.20,
    clav_x0=0.035,       # shoulder bone head x
    clav_drop=0.04,      # shoulder line below chest tail
    shoulder_x=0.19,     # upper arm head x
    upper_len=0.28,
    fore_len=0.26,
    hand_len=0.10,
    grip_x=0.075,        # grip center along the hand from the wrist
    grip_drop=0.018,     # grip center below the hand bone axis (palm side, palm faces down in rest)
    hip_x=0.10,
    hip_h=0.94,          # thigh head height
    knee_h=0.51,
    ankle_h=0.08,
    ball_fwd=0.13,
    ball_h=0.025,
    toe_len=0.07,
    heel_back=0.055,     # heel behind the ankle (used by foot IK / pivots)
)


def proportions(scale=1.0, **over):
    p = {k: v * scale for k, v in STD.items()}
    p.update(over)
    return p


def joints(p):
    """Return dict bone -> (head, tail, z_axis_hint)."""
    J = {}
    up = np.array([0, 0, 1.0])
    fwd = np.array([0, -1.0, 0])
    ph = p["pelvis_h"]
    J["root"] = ((0, 0, 0), (0, 0, 0.25 * p["pelvis_h"] / 0.98), fwd)
    J["hips"] = ((0, 0, ph), (0, 0, ph + p["hips_len"]), fwd)
    s0 = ph + p["hips_len"]
    J["spine"] = ((0, 0, s0), (0, 0, s0 + p["spine_len"]), fwd)
    c0 = s0 + p["spine_len"]
    c1 = c0 + p["chest_len"]
    J["chest"] = ((0, 0, c0), (0, 0, c1), fwd)
    J["neck"] = ((0, 0, c1), (0, 0, c1 + p["neck_len"]), fwd)
    n1 = c1 + p["neck_len"]
    J["head"] = ((0, 0, n1), (0, 0, n1 + p["head_len"]), fwd)
    sh = c1 - p["clav_drop"]
    for side, sx in (("L", 1.0), ("R", -1.0)):
        x0 = p["clav_x0"] * sx
        xs = p["shoulder_x"] * sx
        xe = (p["shoulder_x"] + p["upper_len"]) * sx
        xw = (p["shoulder_x"] + p["upper_len"] + p["fore_len"]) * sx
        xh = xw + p["hand_len"] * sx
        J["shoulder." + side] = ((x0, 0, sh), (xs, 0, sh), up)
        J["upper_arm." + side] = ((xs, 0, sh), (xe, 0, sh), up)
        J["forearm." + side] = ((xe, 0, sh), (xw, 0, sh), up)
        J["hand." + side] = ((xw, 0, sh), (xh, 0, sh), up)
        xg = xw + p["grip_x"] * sx
        zg = sh - p["grip_drop"]
        # weapon socket: head = grip center in the closed fist, bone (+Y) = blade direction = forward (-Y) out of
        # the thumb side of the fist. Both sockets share the SAME rest frame: +Z = back of the hand (palm faces
        # down in the T-pose), X = Y x Z = -X world. Right hand: +X = knuckles/true edge (distal).
        # Left hand: -X = knuckles. With identity attachment a shield (face -Y in its GLB) faces outward from the
        # back of the left hand, and weapon flats (+-Y in the GLB) face +-Z.
        zhint = (0, 0, 1.0)
        J["weapon." + side] = ((xg, 0, zg), (xg, -0.15 * p["upper_len"] / 0.28, zg), zhint)
        hx = p["hip_x"] * sx
        J["thigh." + side] = ((hx, 0, p["hip_h"]), (hx, 0, p["knee_h"]), fwd)
        J["shin." + side] = ((hx, 0, p["knee_h"]), (hx, 0, p["ankle_h"]), fwd)
        J["foot." + side] = ((hx, 0, p["ankle_h"]), (hx, -p["ball_fwd"], p["ball_h"]), up)
        J["toe." + side] = ((hx, -p["ball_fwd"], p["ball_h"]), (hx, -p["ball_fwd"] - p["toe_len"], p["ball_h"] * 0.8), up)
    return {k: (np.array(h, float), np.array(t, float), np.array(z, float)) for k, (h, t, z) in J.items()}


def rest_frames(J):
    """Rest rotation matrices (columns = bone local X, Y, Z in armature space), matching Blender's
    edit bone with align_roll(z_hint)."""
    R = {}
    for name, (h, t, z) in J.items():
        y = t - h
        y = y / np.linalg.norm(y)
        zz = z - y * np.dot(z, y)
        zz = zz / np.linalg.norm(zz)
        x = np.cross(y, zz)
        R[name] = np.stack([x, y, zz], axis=1)
    return R


def build_armature(p, name="Armature", extra=None):
    """extra: list of (name, head, tail, parent, z_hint) optional bones (e.g. cape.1)."""
    import bpy
    J = joints(p)
    arm = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(ob)
    for o in bpy.context.scene.objects:
        if o is not None:
            o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = {}
    for bn in BONE_ORDER:
        h, t, z = J[bn]
        eb = arm.edit_bones.new(bn)
        eb.head = tuple(h)
        eb.tail = tuple(t)
        eb.align_roll(tuple(z))
        eb.use_deform = bn not in DEFORM_EXCLUDE
        ebs[bn] = eb
    for bn in BONE_ORDER:
        if PARENT[bn]:
            ebs[bn].parent = ebs[PARENT[bn]]
            ebs[bn].use_connect = False
    for (bn, h, t, par, z) in (extra or []):
        eb = arm.edit_bones.new(bn)
        eb.head = tuple(h)
        eb.tail = tuple(t)
        eb.align_roll(tuple(z))
        eb.parent = ebs[par] if par in ebs else arm.edit_bones[par]
        eb.use_connect = False
        ebs[bn] = eb
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in ob.pose.bones:
        pb.rotation_mode = "QUATERNION"
    arm.display_type = "STICK"
    return ob, J
