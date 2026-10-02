class_name ArenaState
## bh-033: an arena's breakable fixtures, shared by everyone on the map — the Hollow Warden's impact pillars. A boss
## that charges into a standing pillar breaks it; once every pillar is gone the arena walls still stop him (shorter).
## The map owner breaks a pillar and tells the others (Net.arena_event); the broken set rides in the world checkpoint,
## so a late joiner or a new map owner sees the same arena. A map reload (a fresh attempt) rebuilds every pillar.

const META := &"arena_broken"

## Impact pillars in a stable order (by node name), so every machine numbers them alike.
static func pillars(map: Node) -> Array:
	if map == null or not map.is_inside_tree():
		return []
	var out := map.get_tree().get_nodes_in_group(&"arena_pillar").filter(func(n): return map.is_ancestor_of(n))
	out.sort_custom(func(a, b): return String(a.name) < String(b.name))
	return out

static func broken(map: Node) -> Array:
	return map.get_meta(META, []) if map else []

static func index_of(map: Node, node: Node) -> int:
	var all := pillars(map)
	var n := node
	while n != null and n != map:
		var i := all.find(n)
		if i >= 0:
			return i
		n = n.get_parent()
	return -1

static func intact_count(map: Node) -> int:
	return pillars(map).size() - broken(map).size()

static func has_pillars(map: Node) -> bool:
	return not pillars(map).is_empty()

## Break pillar `idx` (idempotent). `fx` plays the collapse; a checkpoint restore applies it silently.
static func break_pillar(map: Node, idx: int, fx := true) -> bool:
	var all := pillars(map)
	if idx < 0 or idx >= all.size():
		return false
	var done: Array = broken(map).duplicate()
	if done.has(idx):
		return false
	done.append(idx)
	map.set_meta(META, done)
	var p := all[idx] as Node3D
	var at := p.global_position
	p.visible = false
	for cs in p.find_children("*", "CollisionShape3D", true, false):
		(cs as CollisionShape3D).set_deferred(&"disabled", true)
	# what is left: a broken stump and a spill of stone (no collision: the way is open now)
	var stump: Node3D = MapBuilder.scene("pillar_broken").instantiate()
	stump.name = "PillarStump_%d" % idx
	map.add_child(stump)
	stump.global_position = at
	stump.rotation.y = p.rotation.y
	for cs in stump.find_children("*", "CollisionShape3D", true, false):
		(cs as CollisionShape3D).disabled = true
	MaterialLibrary.apply_environment(stump)
	if fx and FX.world:
		FX.spawn(VFXLib.particles(Color(0.55, 0.5, 0.48, 0.9), 40, 1.4, true, 1.2, 4.0, 160.0, Vector3(0, 2, 0), 1.0), at + Vector3.UP * 1.5)
		Events.camera_shake.emit(0.5)
		Audio.play_at(&"break_stone", at, 4.0)
	return true

static func capture(map: Node) -> Dictionary:
	return {"broken": broken(map).duplicate()} if map and not broken(map).is_empty() else {}

static func apply(map: Node, state: Dictionary) -> void:
	for idx in state.get("broken", []):
		break_pillar(map, int(idx), false)
