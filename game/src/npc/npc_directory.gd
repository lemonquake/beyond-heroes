class_name NpcDirectory
extends RefCounted
## Places each map's NPCs (those whose presence conditions hold for the current hero) standing on the ground.

static func populate(map: MapRoot) -> Array:
	var out: Array = []
	if map == null or map.def == null:
		return out
	var holder := Node3D.new()
	holder.name = "NPCs"
	map.add_child(holder)
	for def in DB.npcs.values():
		if def.map != map.def.id or not is_present(def, Game.hero):
			continue
		var n := Npc.new().setup(def)
		holder.add_child(n)
		n.global_position = map.to_global(def.position) + Vector3.UP * ground_height(map, def.position)
		out.append(n)
	return out

static func is_present(def: NpcDef, hero: HeroData) -> bool:
	if def.presence.is_empty():
		return true
	return hero != null and Dialogue.new(def.id, {}).check_all(def.presence, hero)

## Ground height under a map-local point (terrain, floors, stairs), from a downward ray.
static func ground_height(map: MapRoot, p: Vector3) -> float:
	if not map.is_inside_tree():
		return p.y
	var space := map.get_world_3d().direct_space_state
	var from := map.to_global(Vector3(p.x, p.y + 30.0, p.z))
	var q := PhysicsRayQueryParameters3D.create(from, from + Vector3.DOWN * 60.0, BH.LAYER_GROUND | BH.LAYER_WORLD)
	var hit := space.intersect_ray(q)
	return (hit.position.y - map.global_position.y) if not hit.is_empty() else p.y

static func find(id: StringName) -> Npc:
	if Game.current_map == null:
		return null
	for n in Game.current_map.get_tree().get_nodes_in_group(&"npc"):
		if n is Npc and n.def.id == id:
			return n
	return null
