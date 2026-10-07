"""bh-042: put a downloaded CC0 creature on the game's shared hero skeleton so it plays every clip of the game's action
library (132 clips in game/assets/characters/hero.glb: locomotion, boss slams / sweeps / charges / summons, casts,
dodges, parries, hit reactions, deaths).  blender -b --factory-startup -P rig_to_hero.py -- <spec.json>

spec:
  src          .blend / .glb / .fbx / .dae of the creature (never written)
  objects      mesh object names to keep (default: every mesh skinned to the source armature, or every mesh)
  yaw          degrees about Z so the creature faces -Y like the hero (applied first)
  map          {source bone: hero bone}  (rigged sources). The source rig is posed into the hero's T-pose (each mapped
               bone turned to its hero bone's direction), the mesh is frozen in that pose, the hero skeleton's joints
               are moved onto the posed joints, and the source's own skin weights are renamed onto the hero bones
               (unmapped source groups go to their nearest mapped ancestor).
  keep         source bones that keep their own rest direction (a hunched back stays hunched); the hero bone takes it
  landmarks    {hero bone: [x, y, z]} joint positions (unrigged sources, in the normalised frame: feet on z = 0,
               centred, 1.8 m tall) -> automatic (bone heat) weights
  out          GLB to write (hero skeleton + creature mesh + every hero clip as its own NLA track)
"""
import bpy, json, sys, math, mathutils
from mathutils import Matrix, Vector

spec = json.load(open(sys.argv[sys.argv.index("--") + 1]))
HERO = "A:/Python/beyond-heroes/game/assets/characters/hero.glb"
H_TALL = 1.8
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def load(path):
    before = set(bpy.data.objects)
    ext = path.lower().rsplit(".", 1)[1]
    if ext == "blend":
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.objects = [n for n in src.objects]
        for o in dst.objects:
            if o is not None and o.type in ("MESH", "ARMATURE"):
                scene.collection.objects.link(o)
    elif ext == "fbx":
        bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=False)
    elif ext == "dae":
        bpy.ops.wm.collada_import(filepath=path)
    elif ext == "obj":
        bpy.ops.wm.obj_import(filepath=path)
    else:
        bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before and o.name in scene.objects]


# ---- the creature ---------------------------------------------------------------------------------------------------
objs = load(spec["src"])
arms = sorted([o for o in objs if o.type == "ARMATURE"], key=lambda o: -len(o.data.bones))
src_arm = arms[0] if spec.get("map") and arms else None
meshes = [o for o in objs if o.type == "MESH"]
if spec.get("objects"):
    meshes = [o for o in meshes if o.name in spec["objects"]]
elif src_arm:
    skinned = [o for o in meshes if any(m.type == "ARMATURE" and m.object == src_arm for m in o.modifiers) or o.parent == src_arm]
    meshes = skinned or meshes
for o in objs:
    if o not in meshes and o != src_arm:
        bpy.data.objects.remove(o, do_unlink=True)
print("MESHES", [m.name for m in meshes], "ARM", src_arm.name if src_arm else None)
# IK and other constraints would override the T-pose we set (a hand IK target keeps the arm hanging): drop them
if src_arm:
    for pb in src_arm.pose.bones:
        for c in list(pb.constraints):
            pb.constraints.remove(c)
# animation off the source rig: we pose it ourselves
if src_arm and src_arm.animation_data:
    src_arm.animation_data.action = None
    for t in list(src_arm.animation_data.nla_tracks):
        src_arm.animation_data.nla_tracks.remove(t)
for m in meshes:
    for mod in list(m.modifiers):
        if mod.type in ("SUBSURF", "MULTIRES"):
            m.modifiers.remove(mod)
        elif mod.type == "MIRROR":
            bpy.context.view_layer.objects.active = m
            bpy.ops.object.modifier_apply(modifier=mod.name)

# the source's own clips would collide with the hero's clip names (idle, walk ...): drop them before loading the hero
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)

# ---- load the hero skeleton and its clip library --------------------------------------------------------------------
hero_objs = load(HERO)
HA = next(o for o in hero_objs if o.type == "ARMATURE")
for o in hero_objs:
    if o.type == "MESH":
        bpy.data.objects.remove(o, do_unlink=True)
hw = HA.matrix_world
h_rest = {b.name: hw @ b.matrix_local for b in HA.data.bones}
h_dir = {b.name: ((hw @ b.tail_local) - (hw @ b.head_local)).normalized() for b in HA.data.bones}
h_len = {b.name: b.length for b in HA.data.bones}

# ---- pose the source rig into the hero's T-pose and freeze the mesh -----------------------------------------------
yaw = Matrix.Rotation(math.radians(spec.get("yaw", 0.0)), 4, "Z")
landmarks = {}
tails = {}
if src_arm:
    mp = spec["map"]
    keep = set(spec.get("keep", []))
    src_arm.matrix_world = yaw @ src_arm.matrix_world
    bpy.context.view_layer.update()
    sw = src_arm.matrix_world
    s_rest = {b.name: sw @ b.matrix_local for b in src_arm.data.bones}
    order = []

    def visit(b):
        order.append(b)
        for c in b.children:
            visit(c)
    for b in src_arm.data.bones:
        if b.parent is None:
            visit(b)
    HERO_NEXT = {"hips": "spine", "spine": "chest", "chest": "neck", "neck": "head", "foot.L": "toe.L", "foot.R": "toe.R"}
    for sd in ("L", "R"):
        HERO_NEXT.update({"shoulder." + sd: "upper_arm." + sd, "upper_arm." + sd: "forearm." + sd, "forearm." + sd: "hand." + sd,
                          "thigh." + sd: "shin." + sd, "shin." + sd: "foot." + sd})

    def next_src(b, hb):
        goal = HERO_NEXT.get(hb)
        if goal is None:
            return None
        stack = list(b.children)
        while stack:
            c = stack.pop(0)
            if mp.get(c.name) == goal:
                return c
            stack.extend(c.children)
        return None
    SQUARE = {"hips": ("thigh.L", "thigh.R"), "chest": ("shoulder.L", "shoulder.R")}

    def src_with(b, goal):
        stack = list(b.children)
        while stack:
            c = stack.pop(0)
            if mp.get(c.name) == goal or (goal.startswith("shoulder") and mp.get(c.name) == goal.replace("shoulder", "upper_arm")):
                return c
            stack.extend(c.children)
        return None
    want = {}
    for b in order:
        pb = src_arm.pose.bones[b.name]
        pb.rotation_mode = "QUATERNION"
        rest = s_rest[b.name]
        m = (want[b.parent.name] @ (s_rest[b.parent.name].inverted() @ rest)) if b.parent else rest.copy()
        hb = mp.get(b.name)
        if hb and b.name not in keep:
            # the bone's chain direction: toward the source joint that carries the hero's next joint (a Mixamo hip bone
            # points away from its spine), else its own axis
            nxt = next_src(b, hb)
            local = (s_rest[b.name].inverted() @ s_rest[nxt.name]).to_translation() if nxt else Vector((0, 1, 0))
            if local.length < 1e-5:
                local = Vector((0, 1, 0))
            cur = (m.to_3x3() @ local).normalized()
            swing = cur.rotation_difference(h_dir[hb])
            rot3 = swing.to_matrix() @ m.to_3x3()
            # square the hips and the chest: their left/right joints must lie along +X (the body faces -Y)
            pair = SQUARE.get(hb)
            if pair:
                lft, rgt = src_with(b, pair[0]), src_with(b, pair[1])
                if lft and rgt:
                    across = rot3 @ ((s_rest[b.name].inverted() @ s_rest[lft.name]).to_translation()
                                     - (s_rest[b.name].inverted() @ s_rest[rgt.name]).to_translation())
                    axis = h_dir[hb]
                    a2 = (across - axis * across.dot(axis)).normalized()
                    want_x = (Vector((1, 0, 0)) - axis * axis.x).normalized()
                    ang = math.atan2(a2.cross(want_x).dot(axis), a2.dot(want_x))
                    rot3 = Matrix.Rotation(ang, 3, axis) @ rot3
            m = Matrix.Translation(m.to_translation()) @ rot3.to_4x4()
        if b.name in keep:
            # a kept bone holds its modelled direction in the world (the head of a hunched brute keeps looking ahead
            # when the back is straightened)
            m = Matrix.Translation(m.to_translation()) @ rest.to_3x3().to_4x4()
        want[b.name] = m
        ref = (want[b.parent.name] @ s_rest[b.parent.name].inverted() @ rest) if b.parent else rest
        basis = ref.inverted() @ m
        pb.location = basis.to_translation()
        pb.rotation_quaternion = basis.to_quaternion()
    bpy.context.view_layer.update()
    for b in order:
        hb = mp.get(b.name)
        if not hb:
            continue
        head = want[b.name].to_translation()
        nxt = next_src(b, hb)
        tail = want[nxt.name].to_translation() if nxt else want[b.name] @ Vector((0, b.length, 0))
        if hb not in landmarks:
            landmarks[hb] = head
        tails[hb] = tail
        if b.name in keep:
            h_dir[hb] = (tail - head).normalized()
    # freeze: apply the armature deformation, keep the vertex groups
    for m in meshes:
        bpy.context.view_layer.objects.active = m
        for mod in list(m.modifiers):
            if mod.type == "ARMATURE":
                mod.object = src_arm
                bpy.ops.object.modifier_apply(modifier=mod.name)
        mw = m.matrix_world.copy()
        m.parent = None
        m.matrix_world = mw
    # unmapped vertex groups -> nearest mapped ancestor
    group_to = {}
    for b in src_arm.data.bones:
        p = b
        while p is not None and p.name not in mp:
            p = p.parent
        group_to[b.name] = mp[p.name] if p is not None else "hips"
    bpy.data.objects.remove(src_arm, do_unlink=True)
else:
    for m in meshes:
        m.parent = None                       # as measure.py reads it (a statue's base transform is not the figure's)
    bpy.context.view_layer.update()
    for m in meshes:
        m.matrix_world = yaw @ m.matrix_world
    group_to = None

# ---- normalise: feet on the ground, centred, hero height ------------------------------------------------------------
bpy.context.view_layer.update()
for m in meshes:
    bpy.context.view_layer.objects.active = m
    m.select_set(True)
lo = Vector((1e9,) * 3); hi = -lo
for m in meshes:
    for v in m.data.vertices:
        w = m.matrix_world @ v.co
        lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
tall = hi.z - lo.z
s = H_TALL / tall if not spec.get("landmarks") else 1.0
if spec.get("landmarks"):
    s = 1.0
off = Vector(((lo.x + hi.x) * 0.5, (lo.y + hi.y) * 0.5, lo.z))
norm = Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation(-off)
if spec.get("landmarks"):
    # landmarks are given in the normalised frame: normalise with the hero height too
    s = H_TALL / tall
    norm = Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation(-off)
for m in meshes:
    m.matrix_world = norm @ m.matrix_world
    bpy.context.view_layer.objects.active = m
    bpy.ops.object.select_all(action="DESELECT")
    m.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
landmarks = {k: norm @ v for k, v in landmarks.items()}
tails = {k: norm @ v for k, v in tails.items()}
for k, v in spec.get("landmarks", {}).items():
    landmarks[k] = Vector(v)
    if k.endswith(":tip"):
        continue
print("HEIGHT", round(tall, 3), "scale", round(s, 4), "LANDMARKS", {k: tuple(round(x, 2) for x in v) for k, v in landmarks.items()})

# ---- fit the hero skeleton onto the landmarks -------------------------------------------------------------------------
bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active = HA
HA.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
eb = HA.data.edit_bones
orig = {b.name: (b.head.copy(), b.tail.copy(), b.length) for b in eb}
orig_mat = {b.name: b.matrix.copy() for b in eb}
bent = {}
inv = hw.inverted()
new_head = {}
new_len = {}


def chain_child(name):
    kids = [c for c in eb[name].children]
    for c in kids:
        if c.name in landmarks:
            return c.name
    return None


for b in eb:                                  # parents before children (edit_bones keeps file order: root first)
    pass
names = []


def walk(b):
    names.append(b.name)
    for c in b.children:
        walk(c)


for b in eb:
    if b.parent is None:
        walk(b)
for n in names:
    b = eb[n]
    oh, ot, ol = orig[n]
    if n in landmarks:
        head = inv @ landmarks[n]
    elif b.parent is not None:
        p = b.parent.name
        ph, pt, pl = orig[p]
        sc = new_len[p] / pl if pl > 1e-6 else 1.0
        head = new_head[p] + (oh - ph) * sc
    else:
        head = oh.copy()
    kid = chain_child(n)
    if kid:
        ln = (inv @ landmarks[kid] - head).length
    elif n in tails:
        ln = (inv @ tails[n] - head).length
    elif b.parent is not None:
        p = b.parent.name
        ln = ol * (new_len[p] / orig[p][2] if orig[p][2] > 1e-6 else 1.0)
    else:
        ln = ol
    tip = landmarks.get(n + ":tip")
    if tip is not None and not kid:
        ln = (inv @ tip - head).length
    ln = max(ln, 0.02)
    d = (inv.to_3x3() @ h_dir[n]).normalized()
    b.use_connect = False
    # an unrigged mesh stands in its own pose (an A-pose): the bone follows the limb as it is modelled, and is turned
    # back to the hero's T-pose after weighting (bent[n] holds that turn)
    actual = None
    if spec.get("landmarks") and n in landmarks:
        nxt = (inv @ landmarks[kid]) if kid else ((inv @ tip) if tip is not None else None)
        if nxt is not None and (nxt - head).length > 1e-4:
            actual = (nxt - head).normalized()
    if actual is not None and actual.dot(d) < 0.9999:
        rot = d.rotation_difference(actual).to_matrix()
        mat = orig_mat[n].to_3x3()
        b.matrix = Matrix.Translation(head) @ (rot @ mat).to_4x4()
        b.length = ln
        bent[n] = rot
    else:
        roll = b.roll
        b.head = head
        b.tail = head + d * ln
        b.roll = roll
    new_head[n] = head
    new_len[n] = ln
bpy.ops.object.mode_set(mode="OBJECT")

# ---- skin -----------------------------------------------------------------------------------------------------------------
for m in meshes:
    if group_to is not None:
        # rename / merge the source groups onto hero bones
        merged = {}
        for vg in list(m.vertex_groups):
            tgt = group_to.get(vg.name)
            if tgt is None:
                continue
            merged.setdefault(tgt, []).append(vg.index)
        wsum = {}
        for v in m.data.vertices:
            for g in v.groups:
                for tgt, idxs in merged.items():
                    if g.group in idxs:
                        wsum.setdefault(tgt, {})
                        wsum[tgt][v.index] = wsum[tgt].get(v.index, 0.0) + g.weight
        for vg in list(m.vertex_groups):
            m.vertex_groups.remove(vg)
        for tgt, vals in wsum.items():
            g = m.vertex_groups.new(name=tgt)
            for vi, w in vals.items():
                g.add([vi], min(1.0, w), "REPLACE")
        m.parent = HA
        mod = m.modifiers.new("Armature", "ARMATURE")
        mod.object = HA
    else:
        bpy.ops.object.select_all(action="DESELECT")
        m.select_set(True)
        HA.select_set(True)
        bpy.context.view_layer.objects.active = HA
        try:
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        except Exception as e:
            print("AUTO WEIGHTS FAILED", e, "-> envelopes")
            bpy.ops.object.parent_set(type="ARMATURE_ENVELOPE")
        empty = [vg.name for vg in m.vertex_groups if not any(g.group == vg.index for v in m.data.vertices[:2000] for g in v.groups)]
        print("WEIGHTED groups", len(m.vertex_groups))
    # the weapon sockets carry nothing
    for n in ("weapon.L", "weapon.R", "root"):
        vg = m.vertex_groups.get(n)
        if vg:
            m.vertex_groups.remove(vg)

# ---- an unrigged mesh: turn the bent bones back to the T-pose, freeze the mesh there, make that the rest pose -------
if bent:
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = HA
    HA.select_set(True)
    rest = {b.name: b.matrix_local.copy() for b in HA.data.bones}
    want = {}
    for n in names:
        bone = HA.data.bones[n]
        pb = HA.pose.bones[n]
        pb.rotation_mode = "QUATERNION"
        if bone.parent:
            ref = want[bone.parent.name] @ rest[bone.parent.name].inverted() @ rest[n]
        else:
            ref = rest[n].copy()
        # every bone ends in the hero's own orientation (a child of a straightened limb is carried, then squared)
        m = Matrix.Translation(ref.to_translation()) @ orig_mat[n].to_3x3().to_4x4()
        want[n] = m
        basis = ref.inverted() @ m
        pb.location = basis.to_translation()
        pb.rotation_quaternion = basis.to_quaternion()
    bpy.context.view_layer.update()
    for m in meshes:
        bpy.context.view_layer.objects.active = m
        for mod in list(m.modifiers):
            if mod.type == "ARMATURE":
                bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.context.view_layer.objects.active = HA
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    for m in meshes:
        mod = m.modifiers.new("Armature", "ARMATURE")
        mod.object = HA
    print("UNBENT", sorted(bent))

# ---- the texture set a source ships beside its model (FBX exports often lose it) ---------------------------------------
mat_spec = spec.get("material")
if mat_spec:
    mt = bpy.data.materials.new("bh042_" + spec["out"].rsplit("/", 1)[1].split(".")[0])
    mt.use_nodes = True
    nt = mt.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    if mat_spec.get("albedo"):
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image = bpy.data.images.load(mat_spec["albedo"])
        nt.links.new(tx.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = tuple(mat_spec.get("color", [0.3, 0.3, 0.3])) + (1.0,)
    if mat_spec.get("normal"):
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = bpy.data.images.load(mat_spec["normal"])
        tn.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = mat_spec.get("rough", 0.7)
    bsdf.inputs["Metallic"].default_value = mat_spec.get("metal", 0.0)
    keep_mats = set(mat_spec.get("except", []))
    for m in meshes:
        for i, slot in enumerate(m.material_slots):
            if slot.material is None or slot.material.name not in keep_mats:
                slot.material = mt
        if not m.material_slots:
            m.data.materials.append(mt)

# ---- every hero clip as its own muted NLA track ------------------------------------------------------------------------
HA.animation_data_create()
HA.animation_data.action = None
for t in list(HA.animation_data.nla_tracks):
    HA.animation_data.nla_tracks.remove(t)
clips = [a for a in bpy.data.actions]
only = spec.get("clips")
for a in clips:
    if only and a.name not in only:
        continue
    tr = HA.animation_data.nla_tracks.new()
    tr.name = a.name
    tr.strips.new(a.name, int(a.frame_range[0]), a)
    tr.mute = True
for o in list(scene.objects):
    if o.type not in ("ARMATURE", "MESH"):
        bpy.data.objects.remove(o, do_unlink=True)
if spec.get("save_blend"):
    bpy.ops.wm.save_as_mainfile(filepath=spec["save_blend"])
bpy.ops.export_scene.gltf(filepath=spec["out"], export_format="GLB", export_animations=True, export_animation_mode="NLA_TRACKS",
                          export_force_sampling=True, export_apply=False, export_image_format="AUTO")
print("EXPORTED", spec["out"], "clips", len(HA.animation_data.nla_tracks))
