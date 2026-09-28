extends Node
## bh-013 evidence run (real renderer, real boot scene with HUD): the map (M) with every dungeon gate on the Island view,
## a gate selected with its sidebar, the Underground list with raid states, the new monsters lined up on dungeon
## floors, their bosses, fights on new floors, and the new surface gates.
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_bh013.tscn -- --class=knight --slot=97 --level=30 --out=<dir>
## Optional --only=map,bestiary,bosses,fight,gates

var args := {}
var out := ""
var main: Node
var p: Player
var only: PackedStringArray = []

const LINEUPS := [
	[&"cellars", [&"gravecaller", &"riftcaller", &"mirage_weaver", &"bloodbinder", &"aegis_acolyte", &"storm_herald"]],
	[&"warcamp", [&"mirror_knight", &"warband_chieftain", &"soulbound_twin", &"briar_lasher", &"broodhost"]],
	[&"sump", [&"goblin_sapper", &"treasure_gremlin", &"gloam_ooze", &"tunnel_maw", &"stonegaze_basilisk", &"shellback_grinder"]],
	[&"geode", [&"hive_nest", &"hive_drone", &"gloomwraith", &"prism_sentinel", &"void_rift"]],
]

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-013/evidence/captures")))
	only = String(args.get("only", "")).split(",", false)
	DirAccess.make_dir_recursive_absolute(out)
	main = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 1500:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(60)
	p = Game.player as Player
	Game.god_mode = true
	if _want("map"):
		await _map()
	if _want("bestiary"):
		await _bestiary()
	if _want("bosses"):
		await _bosses()
	if _want("fight"):
		await _fight()
	if _want("gates"):
		await _gates()
	print("BH013 CAPTURE DONE -> ", out)
	get_tree().quit()

func _want(k: String) -> bool:
	return only.is_empty() or only.has(k)

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame

func _shot(label: String, frames := 6) -> void:
	await _wait(frames)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("BH013 SHOT ", label)

func _go(map_id: StringName, spawn: StringName) -> void:
	Game.travel(map_id, spawn)
	await _wait(5)
	for i in 1200:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == map_id:
			break
	await _wait(60)

func _clear_enemies() -> void:
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e is Enemy and Game.current_map.is_ancestor_of(e):
			e.queue_free()
	await _wait(3)

## Five monsters of a theme in a shallow arc in front of the hero, frozen in their idle.
func _lineup(ids: Array, center: Vector3, level: int) -> Array:
	var made := []
	for i in ids.size():
		var def := DB.enemy(ids[i])
		var off := Vector3((i - (ids.size() - 1) * 0.5) * 4.2, 0, -absf(i - (ids.size() - 1) * 0.5) * 0.9)
		var e := Spawner.spawn_enemy(Game.current_map, def, level, [], center + off, DataEnemies.DIFFICULTY[1])
		e.patrol_radius = 0.0
		e.rotation.y = 0.0
		made.append(e)
	await _wait(10)
	for e in made:
		e.set_physics_process(false)
		if e.visual:
			e.visual.set_stance(e._idle_anim())
	return made

## Centre of an open stretch of storey-0 floor on floor 1 of a dungeon: five cells in a row, with floor two rows south
## of the middle for the hero to stand on.
func _open_spot(d: StringName) -> Vector3:
	var plan: Array = DataDungeons.floor_def(d, 1).plan
	var at := func(c: int, r: int) -> String: return String(plan[r])[c] if r >= 0 and r < plan.size() and c >= 0 and c < String(plan[r]).length() else "."
	for r in range(plan.size() - 1, -1, -1):
		for c in range(2, String(plan[r]).length() - 2):
			var okk := true
			for k in range(-2, 3):
				if at.call(c + k, r) != "0" or at.call(c + k, r - 1) != "0":
					okk = false
			if okk and at.call(c, r + 1) == "0" and at.call(c, r + 2) == "0":
				var xz := DataDungeons.cell_xz(plan, Vector2i(c, r))
				return Vector3(xz.x, 0, xz.y - 2.0)
	return Game.current_map.spawns[&"arrival"].global_position

func _map() -> void:
	# one raid in progress and one recovered, so the Underground list shows every state
	DataDungeons.record_raid(Game.hero, &"hive", 47.0)
	var old := DataDungeons.record_raid(Game.hero, &"cellars", 30.0)
	old.until = DataDungeons.now() - 10.0
	Game.hero.world_flags[DataDungeons.seal_flag(&"warren", 1)] = true
	var w := Game.ui_root.window(&"world_map") as WorldMapWindow
	Game.ui_root.open(&"world_map")
	await _wait(20)
	w._set_view("island", false)
	await _shot("map_island", 30)
	w.select("wr_cellars")
	await _shot("map_gate_selected", 20)
	w._set_view("local", false)
	await _shot("map_local_westreach", 30)
	w.select("wr_cellars")
	w._directions()
	await _shot("map_directions_to_gate", 20)
	w._set_view("underground", false)
	await _shot("map_underground", 30)
	w.close_window()
	await _wait(20)

func _bestiary() -> void:
	for row in LINEUPS:
		var d: StringName = row[0]
		await _go(DataDungeons.map_id(d, 1), &"arrival")
		await _clear_enemies()
		var arr := _open_spot(d)
		p.global_position = arr + Vector3(0, 0.05, 3.6)
		var made := await _lineup(row[1], arr + Vector3(0, 0, 0.5), 20)
		await _shot("bestiary_%s" % d, 240)
		for e in made:
			e.queue_free()
		await _wait(3)

func _bosses() -> void:
	var ids := DataDungeonsX.ORDER
	for i in range(0, ids.size(), 3):
		var d: StringName = ids[i]
		await _go(DataDungeons.map_id(d, 1), &"arrival")
		await _clear_enemies()
		var arr := _open_spot(d)
		var group := []
		for k in range(i, mini(i + 3, ids.size())):
			group.append(DataDungeons.get_def(ids[k]).boss)
		var made := await _lineup(group, arr + Vector3(0, 0, -2.5), 20)
		p.global_position = arr + Vector3(0, 0.05, 5.0)
		await _shot("bosses_%d" % (i / 3 + 1), 120)
		for e in made:
			e.queue_free()
		await _wait(3)

func _fight() -> void:
	for id in (String(args.get("floors", "")).split(",", false) if args.has("floors") else ["dg_ossuary_1", "dg_briar_2", "dg_thunderwell_2", "dg_undercroft_1", "dg_maw_2"]):
		await _go(StringName(id), &"arrival")
		var zone: Node3D = Game.current_map.find_child("EnemyZone_camp_0", true, false)
		if zone and not args.has("stay"):
			p.global_position = zone.global_position + Vector3(0, 0.3, 5.0)
		await _wait(90)
		await _shot("fight_%s" % id, 10)

func _gates() -> void:
	for d in [&"cellars", &"burrows", &"dunemourn", &"geode"]:
		var sf: Dictionary = DataDungeons.get_def(d).surface
		await _go(sf.map, DataDungeons.gate_id(d))
		await _shot("gate_%s" % d, 30)
