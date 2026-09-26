extends Node
## End-to-end playtest of the map chain with real physics: the explorer pawn walks (navmesh path + CharacterBody
## collisions) from each arrival point to each objective, climbs onto teleporter daises, triggers exploration
## flags by walking into them, is refused by locked waypoints, and travels through Game.travel (loading screen).
##   godot --headless --path game res://tests/tools/playtest.tscn -- [--shots=<dir>]
## With a renderer (no --headless) it also saves gameplay-camera screenshots at each stop.
## Exit code 0 when every leg succeeds; a JSON report is written next to the map evidence.

var report := {"legs": [], "ok": true}
var shots := ""
var explorer: MapExplorer

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shots="):
			shots = a.get_slice("=", 1)
	if shots != "":
		DirAccess.make_dir_recursive_absolute(shots)
	var world := Node3D.new()
	add_child(world)
	Game.world_parent = world
	var h := HeroData.new()
	h.setup(DB.class_def(&"knight"), "Playtester")
	h.init_new()
	Game.hero = h
	explorer = MapExplorer.new()
	Game.player = explorer
	Game.load_map(&"sanctuary", &"start")
	await _settle()
	await _shot("01_sanctuary_start")
	# 1. Sanctuary: up the terrace stair onto the waypoint -> Ruined Forest
	await _leg("sanctuary: start -> waypoint dais", Game.current_map.teleporter(&"sanctuary_waypoint").arrival_point())
	await _shot("02_sanctuary_waypoint")
	await _use(&"sanctuary_waypoint", &"ruined_forest", &"arrival")
	# 2. Forest: through the village, over the bridge, through the grove to the catacomb gate
	await _shot("03_forest_arrival")
	await _leg("forest: arrival -> bridge", Vector3(0, 0, 4.0))
	await _shot("04_forest_bridge")
	await _leg("forest: bridge -> catacomb gate dais", Game.current_map.teleporter(&"catacomb_gate").arrival_point())
	await _use(&"catacomb_gate", &"catacombs", &"entrance")
	# 3. Catacombs: the exit is sealed until the ritual circle is found
	await _shot("05_catacombs_entrance")
	_check("catacombs exit starts locked", Game.current_map.teleporter(&"catacombs_exit").is_locked())
	await _leg("catacombs: entrance -> cistern dock", Vector3(32, -2.0, -5.0))
	await _shot("06_catacombs_dock")
	await _leg("catacombs: dock -> ritual circle", Vector3(0, 0, -38.5))
	_check("walking into the circle set catacombs_ritual_seen", Game.hero.world_flags.get(&"catacombs_ritual_seen", false))
	await _shot("07_catacombs_ritual")
	await _leg("catacombs: ritual -> exit dais", Game.current_map.teleporter(&"catacombs_exit").arrival_point())
	await _use(&"catacombs_exit", &"forgotten_temple", &"arrival")
	# 4. Temple: nave -> sanctum; gate refuses while sealed; the altar breaks the seal
	await _shot("08_temple_arrival")
	var gate := Game.current_map.teleporter(&"temple_throne_gate")
	await _leg("temple: arrival -> throne gate dais (sealed)", gate.arrival_point())
	_check("sealed throne gate refuses travel", not gate.activate_would_travel())
	await _shot("09_temple_sanctum")
	await _leg("temple: gate -> altar of the first oath", Vector3(0, 2.0, -31.8))
	_check("the altar broke the seal", Game.hero.world_flags.get(&"temple_seal_broken", false))
	await _leg("temple: altar -> throne gate dais", gate.arrival_point())
	await _use(&"temple_throne_gate", &"boss_arena", &"arrival")
	# 5. Arena: across the bridge and up to the throne; the return waypoint opens only after the Warden falls
	await _shot("10_arena_arrival")
	var boss: Node3D = get_tree().get_first_node_in_group(&"boss_spawn")
	await _leg("arena: arrival -> throne dais", boss.global_position + Vector3(0, 0, 1.5))
	await _shot("11_arena_throne")
	var ret := Game.current_map.teleporter(&"arena_return")
	_check("arena return sealed before the boss", not ret.activate_would_travel())
	Game.hero.world_flags[&"boss_warden_defeated"] = true
	Game.current_map.refresh_teleporters()
	await _leg("arena: throne -> return dais", ret.arrival_point())
	await _use(&"arena_return", &"sanctuary", &"waypoint")
	await _shot("12_sanctuary_return")
	_check("hero discovered all five maps", Game.hero.discovered_maps.size() == 5)
	var ids := Game.hero.unlocked_teleporters.keys()
	_check("waypoints registered on the hero (%d)" % ids.size(), ids.size() >= 6)
	var out := ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-001/evidence/maps")
	DirAccess.make_dir_recursive_absolute(out)
	var fa := FileAccess.open(out.path_join("playtest_report.json"), FileAccess.WRITE)
	fa.store_string(JSON.stringify(report, "  "))
	print("PLAYTEST ", "PASS" if report.ok else "FAIL")
	get_tree().quit(0 if report.ok else 1)

func _settle() -> void:
	for i in 3:
		await get_tree().physics_frame

func _check(what: String, cond: bool) -> void:
	report.legs.append({"check": what, "ok": cond})
	report.ok = report.ok and cond
	print("[%s] %s" % ["OK" if cond else "FAIL", what])

## Walk to `target` and report whether the pawn physically got there (within 1.3 m horizontally, 0.7 m vertically).
func _leg(name: String, target: Vector3, timeout := 60.0) -> void:
	await _settle()
	var start := explorer.global_position
	explorer.walk_to(target)
	var t := 0.0
	var stuck := 0.0
	var last := explorer.global_position
	while t < timeout:
		await get_tree().physics_frame
		t += 1.0 / Engine.physics_ticks_per_second
		var flat := Vector2(explorer.global_position.x - target.x, explorer.global_position.z - target.z).length()
		if flat < 1.0 and absf(explorer.global_position.y - target.y) < 0.8:
			break
		if explorer.global_position.distance_to(last) < 0.02:
			stuck += 1.0 / Engine.physics_ticks_per_second
			if stuck > 3.0:
				break
		else:
			stuck = 0.0
		last = explorer.global_position
	var d := Vector2(explorer.global_position.x - target.x, explorer.global_position.z - target.z).length()
	var dy := absf(explorer.global_position.y - target.y)
	var ok := d < 1.3 and dy < 0.8
	report.legs.append({"leg": name, "ok": ok, "seconds": snappedf(t, 0.1), "from": str(start.snapped(Vector3.ONE * 0.1)),
		"to": str(target.snapped(Vector3.ONE * 0.1)), "ended": str(explorer.global_position.snapped(Vector3.ONE * 0.1))})
	report.ok = report.ok and ok
	print("[%s] %s  (%.1fs, off by %.2f m / %.2f m)" % ["OK" if ok else "FAIL", name, t, d, dy])

## Activate a teleporter as the player would (standing on it) and verify arrival on the named spawn.
func _use(tid: StringName, dest_map: StringName, dest_spawn: StringName) -> void:
	var t := Game.current_map.teleporter(tid)
	var inside := t._player_inside == explorer
	var started := t.activate_would_travel()
	t.activate()
	var waited := 0.0
	while started and (Game.travelling or Game.current_map_id != dest_map) and waited < 15.0:
		await get_tree().process_frame
		waited += get_process_delta_time()
	await _settle()
	var marker: Marker3D = Game.current_map.spawns.get(dest_spawn) if Game.current_map_id == dest_map else null
	var want: Vector3 = marker.global_position if marker else Vector3.INF
	var ok := started and inside and marker != null and explorer.global_position.distance_to(want) < 0.6
	report.legs.append({"teleport": String(tid), "ok": ok, "player_on_pad": inside, "arrived": String(Game.current_map_id),
		"spawn_error_m": snappedf(explorer.global_position.distance_to(want), 0.01)})
	report.ok = report.ok and ok
	print("[%s] teleport %s -> %s/%s (on pad: %s, spawn error %.2f m)" % ["OK" if ok else "FAIL", tid, dest_map, dest_spawn, inside,
		explorer.global_position.distance_to(want)])

func _shot(name: String) -> void:
	if shots == "" or DisplayServer.get_name() == "headless":
		return
	for i in 10:
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png(shots.path_join(name + ".png"))
