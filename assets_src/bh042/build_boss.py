"""bh-042: prepare a downloaded CC0 boss model for the game (Blender 5.x, headless).
  blender -b --factory-startup -P build_boss.py -- <spec.json>

spec:
  src        the character (glTF/GLB, never written)
  out        GLB written to assets_src/bh042/out/ (then tests/tools/convert_creature.tscn renames clips, scales, tints)
  weapons    [{"src": glTF, "bone": "handslot.r", "loc": [x,y,z], "rot": [deg x,y,z], "scale": s}]: rigid props parented
             to a bone (KayKit weapons, crowns)
  retarget   {"src": a rig with the clip library (KayKit), "map": {"source bone": "target bone"}, "hips": ["src", "tgt"],
              "clips": [source action names to carry over]}: every listed clip is re-expressed on the target rig, so a
             model that shipped with a dozen clips gets the whole library
  drop       mesh names to delete (helpers)
  scale_bones {bone: factor}: a bigger head, longer horns ... (rest pose edit before skinning is evaluated)

Retargeting: both rigs stand in a T-pose facing -Y. For every mapped bone and frame the source bone's rotation away
from its rest (in world space) is applied to the target bone's rest; the hips also carry the source's movement, scaled
by leg length. Target bones with no source keep their rest relation to their parent, except bones listed in
"follow" ({target: target_chain_end}), which are placed at the end of a chain (Quaternius feet hang from the root and
must follow the shin)."""
import bpy, json, sys, math, mathutils

spec = json.load(open(sys.argv[sys.argv.index("--") + 1]))
bpy.ops.wm.read_factory_settings(use_empty=True)


def import_any(path):
    before = set(bpy.data.objects)
    if path.lower().endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def armature_of(objs):
    return next(o for o in objs if o.type == "ARMATURE")


tgt_objs = import_any(spec["src"])
T = armature_of(tgt_objs)
for name in spec.get("drop", []):
    for o in list(bpy.data.objects):
        if o.type == "MESH" and o.name.startswith(name):
            bpy.data.objects.remove(o, do_unlink=True)

# ---- weapons / props on bones -------------------------------------------------------------------------------------
for w in spec.get("weapons", []):
    objs = import_any(w["src"])
    meshes = [o for o in objs if o.type == "MESH"]
    for o in objs:
        if o.type != "MESH" and o.type != "EMPTY":
            continue
    for m in meshes:
        mw = m.matrix_world.copy()
        m.parent = T
        m.parent_type = "BONE"
        m.parent_bone = w["bone"]
        bone = T.data.bones[w["bone"]]
        # place in the bone's space: origin at the bone head, then the given offset / rotation / scale
        m.matrix_parent_inverse = mathutils.Matrix.Identity(4)
        r = [math.radians(a) for a in w.get("rot", [0, 0, 0])]
        m.matrix_basis = (mathutils.Matrix.Translation(w.get("loc", [0, 0, 0])) @ mathutils.Euler(r).to_matrix().to_4x4()
                          @ mathutils.Matrix.Diagonal((w.get("scale", 1.0),) * 3 + (1.0,)))
        # parent_type BONE measures from the bone's tail; shift back to the head
        m.matrix_basis = mathutils.Matrix.Translation((0, -bone.length, 0)) @ m.matrix_basis
    for o in objs:
        if o.type == "EMPTY" and not o.children:
            bpy.data.objects.remove(o, do_unlink=True)

# ---- retarget ------------------------------------------------------------------------------------------------------
rt = spec.get("retarget")
if rt:
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    src_objs = import_any(rt["src"])
    S = armature_of(src_objs)
    for o in src_objs:
        if o.type == "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    mp = rt["map"]                          # source bone -> target bone
    inv = {v: k for k, v in mp.items()}
    follow = rt.get("follow", {})           # target bone -> target bone whose tail it sits on
    hips_s, hips_t = rt["hips"]
    sw = S.matrix_world
    tw = T.matrix_world
    s_rest = {b.name: sw @ b.matrix_local for b in S.data.bones}
    t_rest = {b.name: tw @ b.matrix_local for b in T.data.bones}
    leg_s = (s_rest[hips_s].to_translation().z - min(v.to_translation().z for v in s_rest.values())) or 1.0
    leg_t = (t_rest[hips_t].to_translation().z - min(v.to_translation().z for v in t_rest.values())) or 1.0
    ratio = leg_t / leg_s
    order = []

    def visit(b):
        order.append(b)
        for c in b.children:
            visit(c)
    for b in T.data.bones:
        if b.parent is None:
            visit(b)
    # bones that sit on another chain's end are placed after that chain is solved
    late = [b for b in order if b.name in follow or any(p.name in follow for p in b.parent_recursive)]
    order = [b for b in order if b not in late] + late
    T.animation_data_create()
    S.animation_data_create()
    made = []
    scene = bpy.context.scene
    for clip in rt["clips"]:
        src_action = bpy.data.actions.get(clip)
        if src_action is None:
            print("MISSING", clip)
            continue
        S.animation_data.action = src_action
        if getattr(src_action, 'slots', None) and len(src_action.slots):
            S.animation_data.action_slot = src_action.slots[0]
        f0, f1 = int(src_action.frame_range[0]), int(src_action.frame_range[1])
        act = bpy.data.actions.new(clip + "__rt")
        act.use_fake_user = True
        T.animation_data.action = act
        for pb in T.pose.bones:
            pb.rotation_mode = "QUATERNION"
        for f in range(f0, f1 + 1):
            scene.frame_set(f)
            want = {}                        # target bone -> armature-space (world) matrix
            for b in order:
                pb = T.pose.bones[b.name]
                rest_w = t_rest[b.name]
                parent_w = want.get(b.parent.name) if b.parent else tw
                # default: keep the rest relation to the parent
                if b.parent:
                    m = parent_w @ (t_rest[b.parent.name].inverted() @ rest_w)
                else:
                    m = rest_w.copy()
                sname = inv.get(b.name)
                if sname:
                    spb = S.pose.bones[sname]
                    pose_s = sw @ spb.matrix
                    delta = pose_s.to_quaternion() @ s_rest[sname].to_quaternion().inverted()
                    rot = delta @ rest_w.to_quaternion()
                    loc = m.to_translation()
                    if b.name == hips_t:
                        moved = pose_s.to_translation() - s_rest[sname].to_translation()
                        loc = rest_w.to_translation() + moved * ratio
                    m = mathutils.Matrix.Translation(loc) @ rot.to_matrix().to_4x4()
                if b.name in follow:
                    end = want.get(follow[b.name])
                    if end is not None:
                        tip = end @ mathutils.Vector((0, T.data.bones[follow[b.name]].length, 0))
                        m = mathutils.Matrix.Translation(tip) @ m.to_quaternion().to_matrix().to_4x4()
                want[b.name] = m
                # basis = (parent_pose @ parent_rest^-1 @ rest)^-1 @ want   (all in world space)
                ref = (want[b.parent.name] @ t_rest[b.parent.name].inverted() @ rest_w) if b.parent else rest_w
                basis = ref.inverted() @ m
                pb.location = basis.to_translation()
                pb.rotation_quaternion = basis.to_quaternion()
                pb.keyframe_insert("rotation_quaternion", frame=f)
                if b.name == hips_t or b.name in follow or not b.parent:
                    pb.keyframe_insert("location", frame=f)
        act.name = clip
        made.append(act)
    bpy.data.objects.remove(S, do_unlink=True)
    for a in list(bpy.data.actions):
        if a not in made:
            bpy.data.actions.remove(a)
    T.animation_data.action = None
    for pb in T.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
    for c in made:
        tr = T.animation_data.nla_tracks.new()
        tr.name = c.name
        tr.strips.new(c.name, int(c.frame_range[0]), c)
        tr.mute = True
    print("RETARGETED", len(made), "clips ratio", round(ratio, 3))
else:
    # keep the model's own clips: one muted NLA track each so the exporter writes them all
    T.animation_data_create()
    for a in list(bpy.data.actions):
        tr = T.animation_data.nla_tracks.new()
        tr.name = a.name
        tr.strips.new(a.name, int(a.frame_range[0]), a)
        tr.mute = True
    T.animation_data.action = None

bpy.ops.export_scene.gltf(filepath=spec["out"], export_format="GLB", export_animations=True, export_animation_mode="NLA_TRACKS",
                          export_force_sampling=True, export_apply=False, export_image_format="AUTO")
print("EXPORTED", spec["out"])
