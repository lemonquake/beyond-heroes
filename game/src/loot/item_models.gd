class_name ItemModels
## The 3D models of items (bh-006): every base has its own GLB in res://assets/items/<id>.glb (built by
## tools/blender/items). Weapons keep the hand-socket convention (origin at the grip, +Y along the blade/shaft, flats
## facing ±Z); shields face +Z (Blender -Y) with the handle at the origin; chest pieces and gloves stand upright facing +Z
## (laid flat when dropped); everything else stands upright on its base at the origin.

## Minimum on-ground size (largest extent, m) so a ring or a gem is still visible and clickable among the grass.
const GROUND_MIN_SIZE := 0.36
const GROUND_MAX_SIZE := 1.7
## Authored upright with the front toward +Z (Blender -Y): laid on their back when they lie on the ground.
const LAY_FLAT := [&"shield", &"armor", &"inner_garment", &"gloves"]

static var _scenes := {}

static func scene_of(base: ItemBaseDef) -> PackedScene:
	var path := base.model_path() if base else ""
	if path == "":
		return null
	if not _scenes.has(path):
		_scenes[path] = load(path) if ResourceLoader.exists(path) else null
	return _scenes[path]

## The item's model with the game's material set applied. `scale_to` > 0 rescales so the largest extent equals it.
static func instance(base: ItemBaseDef, scale_to := 0.0) -> Node3D:
	var ps := scene_of(base)
	var root := Node3D.new()
	var m: Node3D = ps.instantiate() if ps else _fallback(base)
	root.add_child(m)
	var ms: Array[MeshInstance3D] = []
	for n in m.find_children("*", "MeshInstance3D", true, false):
		ms.append(n)
	if m is MeshInstance3D:
		ms.append(m)
	MaterialLibrary.apply_character(ms, Color(0.55, 0.18, 0.16))
	if scale_to > 0.0:
		var bb := bounds(root)
		var ext := maxf(bb.size.x, maxf(bb.size.y, bb.size.z))
		if ext > 0.001:
			m.scale *= scale_to / ext
	return root

## An item as it lies on the ground: long things (weapons, shields) laid flat, everything else upright; centred on the
## origin, resting on y = 0, small items enlarged to GROUND_MIN_SIZE.
static func ground_instance(base: ItemBaseDef, yaw := 0.0) -> Node3D:
	var root := Node3D.new()
	var holder := Node3D.new()
	root.add_child(holder)
	var inner := instance(base)
	holder.add_child(inner)
	if base and (base.is_weapon() or base.category in LAY_FLAT):
		# lie flat: blade/shaft (+Y) along the ground, flats (±Z) / the shield's face (+Z) facing up
		inner.rotation = Vector3(-PI * 0.5, 0.0, 0.0)
	var bb := bounds(holder)
	var ext := maxf(bb.size.x, maxf(bb.size.y, bb.size.z))
	var s := 1.0
	if ext > 0.0001 and ext < GROUND_MIN_SIZE:
		s = GROUND_MIN_SIZE / ext
	elif ext > GROUND_MAX_SIZE:
		s = GROUND_MAX_SIZE / ext
	holder.scale = Vector3.ONE * s
	var c := bb.get_center() * s
	holder.position = Vector3(-c.x, -bb.position.y * s + 0.01, -c.z)
	root.rotation.y = yaw
	return root

const GOLD_MODEL := "res://assets/items/gold_pile.glb"

## A pile of coins on the ground (gold drops), or null when the model is missing.
static func gold_instance(yaw := 0.0) -> Node3D:
	if not ResourceLoader.exists(GOLD_MODEL):
		return null
	var root := Node3D.new()
	var m: Node3D = load(GOLD_MODEL).instantiate()
	root.add_child(m)
	var ms: Array[MeshInstance3D] = []
	for n in m.find_children("*", "MeshInstance3D", true, false):
		ms.append(n)
	MaterialLibrary.apply_character(ms, Color(0.55, 0.18, 0.16))
	root.rotation.y = yaw
	return root

## Combined AABB of every mesh under `n`, in n's local space.
static func bounds(n: Node3D) -> AABB:
	var out := AABB()
	var first := true
	var inv := n.global_transform.affine_inverse() if n.is_inside_tree() else Transform3D.IDENTITY
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if m.mesh == null:
			continue
		var xf := _local_xf(n, m) if not n.is_inside_tree() else inv * m.global_transform
		var bb := xf * m.mesh.get_aabb()
		out = bb if first else out.merge(bb)
		first = false
	return out

static func _local_xf(root: Node3D, n: Node3D) -> Transform3D:
	var xf := Transform3D.IDENTITY
	var cur: Node = n
	while cur != null and cur != root:
		if cur is Node3D:
			xf = (cur as Node3D).transform * xf
		cur = cur.get_parent()
	return xf

## Representative colour of an item (potion liquid, bomb flame ...) for effects and particles.
static func tint_of(base: ItemBaseDef) -> Color:
	if base == null:
		return Color(1, 1, 1)
	var id := String(base.id)
	for k in TINTS:
		if id.contains(k):
			return TINTS[k]
	if base.element != Elements.PHYSICAL:
		return Elements.color(base.element)
	return Color(0.95, 0.9, 0.8)

const TINTS := {
	"health": Color(0.95, 0.2, 0.18), "mana": Color(0.25, 0.45, 1.0), "rejuvenation": Color(0.75, 0.35, 0.95),
	"swift": Color(0.45, 0.95, 0.55), "ironskin": Color(0.7, 0.72, 0.78), "berserk": Color(1.0, 0.35, 0.15),
	"sage": Color(0.55, 0.5, 1.0), "ember": Color(1.0, 0.5, 0.15), "frost": Color(0.6, 0.9, 1.0), "storm": Color(1.0, 0.95, 0.4),
	"fortune": Color(1.0, 0.82, 0.3), "scholar": Color(0.75, 0.6, 0.35), "feather": Color(0.85, 0.95, 1.0),
	"whetstone": Color(0.65, 0.65, 0.7), "firebomb": Color(1.0, 0.45, 0.1), "smoke": Color(0.6, 0.6, 0.62),
	"phoenix": Color(1.0, 0.55, 0.15), "portal": Color(0.7, 0.4, 1.0), "antidote": Color(0.6, 0.95, 0.7),
	"return": Color(0.55, 0.95, 1.0),
}

## Stand-in when a model is missing (never expected once the pipeline has run): a small wrapped bundle.
static func _fallback(base: ItemBaseDef) -> Node3D:
	var mi := MeshInstance3D.new()
	var bm := SphereMesh.new()
	bm.radius = 0.14
	bm.height = 0.22
	bm.radial_segments = 8
	bm.rings = 4
	mi.mesh = bm
	var pm := StandardMaterial3D.new()
	pm.albedo_color = tint_of(base).darkened(0.4)
	pm.roughness = 0.8
	mi.material_override = pm
	mi.position.y = 0.11
	return mi
