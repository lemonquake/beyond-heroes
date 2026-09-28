extends Node
## Monster placement audit (bh-011): boots the real game, loads every combat map, and checks each spawned monster
##   - stands on the ground under it (a ray from 8 m above lands within 1.2 m of its feet), not buried or floating;
##   - is still within 3 m of its spawn height after 4 s of physics (nothing falls through the world or off a deck);
##   - nothing died while nobody fought.
##   godot --headless --path game res://tests/tools/spawn_audit.tscn -- --class=knight --slot=97 [--lite=1]
## Prints SPAWNS PASS / SPAWNS FAIL and exits 0 / 1.

const MAPS := [&"westreach", &"ruined_forest", &"catacombs", &"forgotten_temple", &"boss_arena"]
var fails: Array = []
var deaths := 0

func _ready() -> void:
	add_child(load("res://src/main.gd").new())
	Events.actor_died.connect(func(a: Node, _k: Node) -> void:
		if a is Enemy:
			deaths += 1)
	_run.call_deferred()

func _run() -> void:
	for i in 900:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await get_tree().process_frame
	Game.god_mode = true
	(Game.player as Player).input_enabled = false
	for id in MAPS:
		Game.load_map(id, &"start")
		# park the hero far away so nobody aggroes or fights while we watch
		(Game.player as Node3D).global_position = Game.current_map.spawn_transform(&"start").origin + Vector3.UP * 0.1
		var start := {}
		var bad_ground := 0
		for e in get_tree().get_nodes_in_group(&"enemy"):
			var en := e as Enemy
			start[en] = en.global_position
			var g := _ground(en)
			if absf(g - en.global_position.y) > 1.2:
				bad_ground += 1
				fails.append("%s: %s spawned %.1f m from the ground under it (y %.2f, ground %.2f, camp %s)" % [id, en.name,
					en.global_position.y - g, en.global_position.y, g, en.zone.name if en.zone else "-"])
		deaths = 0
		await get_tree().create_timer(4.0).timeout
		var fell := 0
		for en in start:
			if not is_instance_valid(en):
				continue
			if (en as Enemy).global_position.y < float(start[en].y) - 3.0:
				fell += 1
				fails.append("%s: %s fell %.1f m" % [id, en.name, float(start[en].y) - (en as Enemy).global_position.y])
		if deaths > 0:
			fails.append("%s: %d monsters died with nobody fighting" % [id, deaths])
		print("MAP %-18s monsters %3d  off-ground %d  fell %d  deaths %d" % [id, start.size(), bad_ground, fell, deaths])
	for f in fails:
		print("  FAIL ", f)
	print("SPAWNS ", "PASS" if fails.is_empty() else "FAIL")
	get_tree().quit(0 if fails.is_empty() else 1)

## Height of the first ground/world surface below a point 8 m above the monster that belongs to the map.
func _ground(en: Enemy) -> float:
	var map := Game.current_map
	var space := en.get_world_3d().direct_space_state
	var from := en.global_position + Vector3.UP * 8.0
	var q := PhysicsRayQueryParameters3D.create(from, from + Vector3.DOWN * 40.0, BH.LAYER_GROUND | BH.LAYER_WORLD)
	var ex: Array[RID] = []
	for i in 10:
		q.exclude = ex
		var hit := space.intersect_ray(q)
		if hit.is_empty():
			return -INF
		var col = hit.get("collider")
		# stand-on surfaces only: roofs/canopies over the monster are skipped when it clearly stands under them
		if col is Node and map.is_ancestor_of(col) and hit.position.y <= en.global_position.y + 1.5:
			return hit.position.y
		ex.append(hit.rid)
	return -INF
