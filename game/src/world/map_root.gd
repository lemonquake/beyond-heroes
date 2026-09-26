class_name MapRoot
extends Node3D
## Root of a built map. Knows its definition, named spawn points, teleporters, camera bounds and preview views.

var def: MapDef
var spawns := {}              # StringName -> Marker3D
var views := {}               # name -> {target: Vector3, yaw: float, pitch: float, dist: float, fov: float}
var bounds := AABB()          # walkable area used by camera clamping and the world map
var nav_region: NavigationRegion3D
var environment: WorldEnvironment
var sun: DirectionalLight3D

func spawn_transform(id: StringName) -> Transform3D:
	var m: Marker3D = spawns.get(id)
	if m == null:
		m = spawns.get(&"start")
	if m == null:
		push_warning("Map %s has no spawn '%s'" % [def.id if def else &"?", id])
		return Transform3D.IDENTITY
	return m.global_transform

func teleporters() -> Array[Teleporter]:
	var out: Array[Teleporter] = []
	for n in find_children("*", "Teleporter", true, false):
		out.append(n)
	return out

func teleporter(id: StringName) -> Teleporter:
	for t in teleporters():
		if t.teleporter_id == id:
			return t
	return null

func refresh_teleporters() -> void:
	for t in teleporters():
		t.refresh_state()

## Nodes registered with MapBuilder.hide_when(flag) vanish once the hero has that world flag (seals, barriers). A hidden
## collider stops colliding too (the South Gate's bar), so the way is really open, not just invisible.
func apply_flag_visuals(flag: StringName = &"", animate := false) -> void:
	for n in get_tree().get_nodes_in_group(&"flag_visual") if is_inside_tree() else find_children("*", "", true, false):
		if not n.has_meta(&"hide_when_flag"):
			continue
		var f: StringName = n.get_meta(&"hide_when_flag")
		if flag != &"" and f != flag:
			continue
		if Game.hero == null or not Game.hero.world_flags.get(f, false):
			continue
		if animate and n is Node3D:
			var n3: Node3D = n
			n3.add_child(VFXLib.light_flash(Color(0.8, 0.5, 1.0), 8.0, 10.0, 0.6))
			var tw := n3.create_tween()
			tw.tween_property(n3, "scale", Vector3(1, 0.01, 1), 0.6).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
			tw.tween_callback(func(): n3.visible = false)
		else:
			n.visible = false
		_release_collision(n)

static func _release_collision(n: Node) -> void:
	var bodies: Array = n.find_children("*", "CollisionObject3D", true, false)
	if n is CollisionObject3D:
		bodies.append(n)
	for b: CollisionObject3D in bodies:
		b.collision_layer = 0
		b.collision_mask = 0
