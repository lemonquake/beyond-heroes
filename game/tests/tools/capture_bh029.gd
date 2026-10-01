extends Node
## bh-029 evidence run (real renderer, real boot scene with HUD): Zarael Island.
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_bh029.tscn -- --class=knight --slot=95 --part=<p> --out=<dir>
## parts (comma-separated, default all):
##   ship     Wyman Outpost after Kethrax: the Marsh Jetty, the Sunwake, Captain Ilsa; sail to Agdao
##   terax    the landing at Agdao: frames from Terax's welcome cutscene
##   agdao    every named view of Agdao, plus the hero on the terraces, the pyramid top and the Wirekeeper
##   wilds    every named view of the Coilwood, the Barrens, the Bridge of Death and the Heart Citadel
##   vaults   floor 1 and the sanctum of each Vault
##   monsters every Zarael monster standing in a line on the Glasswire Barrens (--lineup_map=wyman_outpost: the Sand Arena) (and a close shot of each)
##   restored Agdao after the Dawn Engine wakes (gold Heartwire)

var args := {}
var out := ""
var parts: PackedStringArray
var main: Node
var p: Player

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-029/evidence/captures")))
	parts = String(args.get("part", "ship,terax,agdao,wilds,vaults,monsters,restored")).split(",")
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
	var h := Game.hero
	var lvl := int(args.get("level", "40"))
	h.progress.add_xp(maxi(0, XpCurve.total_xp_for_level(lvl) - h.progress.total_xp))
	QuakeBrain.spend_points(h)
	var rng := RandomNumberGenerator.new()
	rng.seed = 2029
	GuildSummons._gear_up(h, lvl, rng)
	for f in [&"south_gate_open", &"mq_maelis_orders", &"mq_shard_taken", &"mq_three_told", &"mq_marsh_gate_open", &"boss_kethrax_defeated",
			&"mq_kethrax_reported", &"chain_breaks_seen"]:
		h.world_flags[f] = true
	h.tier = 5
	h.stats_dirty.emit()
	Game.ui_root.close_all()
	p.invulnerable = true
	if "ship" in parts:
		await _ship()
	if "terax" in parts:
		await _terax()
	if "agdao" in parts:
		await _agdao()
	if "wilds" in parts:
		await _wilds()
	if "vaults" in parts:
		await _vaults()
	if "monsters" in parts:
		await _monsters()
	if "restored" in parts:
		await _restored()
	print("BH029 CAPTURE DONE -> ", out)
	get_tree().quit()

func _ship() -> void:
	await _go(&"wyman_outpost", &"jetty")
	print("BH029 objective: ", Objectives.current(Game.hero).get("id", ""))
	await _shot("01_wyman_jetty_arrival", 60)
	var cap := NpcDirectory.find(&"ilsa")
	print("BH029 captain present: ", cap != null)
	if cap:
		_place(cap.global_position + Vector3(-3.5, 0, 1.0), cap.global_position)
		await _shot("02_wyman_captain_ilsa", 30)
	await _orbit("03_wyman_ship", DataZarael.WY_SHIP + Vector3(0, 2, 0), 200.0, 34.0, 32.0)

func _terax() -> void:
	Game.hero.world_flags.erase(DataZarael.F_TERAX)
	ZaraelVoyage.sail(true)
	await _wait(5)
	for i in 1500:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == &"agdao":
			break
	p = Game.player as Player
	p.invulnerable = true
	var n := 10
	for i in 2400:
		await get_tree().process_frame
		if CutscenePlayer.is_playing():
			break
	if not CutscenePlayer.is_playing():
		print("BH029 terax cutscene did not start")
		return
	var cs := CutscenePlayer.active
	var shots := [1.5, 6.0, 12.5, 16.0, 21.0, 25.5, 30.0, 34.0, 41.0, 45.0]
	var t0 := Time.get_ticks_msec()
	for s in shots:
		while CutscenePlayer.is_playing() and (Time.get_ticks_msec() - t0) / 1000.0 < float(s):
			await get_tree().process_frame
		if not CutscenePlayer.is_playing():
			break
		await _shot("%02d_terax_%s" % [n, String(cs.scenes[clampi(cs.index, 0, cs.scenes.size() - 1)].name).to_snake_case()], 0)
		n += 1
	for i in 3000:
		if not CutscenePlayer.is_playing():
			break
		await get_tree().process_frame
	print("BH029 terax met: ", Game.has_flag(DataZarael.F_TERAX))
	await _wait(30)
	await _shot("20_agdao_after_welcome", 30)

func _agdao() -> void:
	# the welcome cutscene has its own part (terax); here the hero has already met Terax
	Game.hero.world_flags[&"zr_ship_sailed"] = true
	Game.hero.world_flags[&"zr_terax_met"] = true
	if Game.current_map_id != &"agdao":
		await _go(&"agdao", &"pier")
	var k := 30
	for v in ["overview", "topdown", "harbour", "market", "terraces", "crown", "pyramid_top", "gate"]:
		await _view("%d_agdao_%s" % [k, v], v)
		k += 1
	_place(Vector3(0, 20, 6), Vector3(0, 0, -40))
	await _shot("%d_agdao_hero_grand_stair" % k, 40)
	k += 1
	var wk := NpcDirectory.find(&"wirekeeper")
	if wk:
		_place(wk.global_position + Vector3(0, 0, 4.0), wk.global_position)
		await _shot("%d_agdao_wirekeeper_top" % k, 40)

func _wilds() -> void:
	var k := 50
	for m in [&"zr_coilwood", &"zr_barrens", &"bridge_of_death", &"zr_citadel"]:
		if not ResourceLoader.exists("res://src/world/maps/%s.gd" % m):
			continue
		var def := DB.map_def(m)
		await _go(m, &"start" if def == null else _first_spawn(m))
		for v in Game.current_map.views.keys():
			await _view("%d_%s_%s" % [k, m, v], v)
			k += 1

func _first_spawn(m: StringName) -> StringName:
	return {&"zr_coilwood": &"agdao_road", &"zr_barrens": &"coil_road", &"bridge_of_death": &"barrens_road", &"zr_citadel": &"bridge_road"}.get(m, &"start")

func _vaults() -> void:
	var k := 80
	for id in DataDungeonsZarael.ORDER:
		await _go(DataDungeons.map_id(id, 1), &"arrival")
		await _shot("%d_%s_floor1" % [k, id], 60)
		k += 1
		await _go(DataDungeons.map_id(id, DataDungeons.floor_count(id)), &"arrival")
		await _view("%d_%s_sanctum" % [k, id], "overview")
		k += 1

## Every Zarael monster in a line (the Glasswire Barrens by default), frozen in its idle; then one close shot each.
func _monsters() -> void:
	# daylight on the Glasswire Barrens by default (Wyman's arena is a night map: every grey model read moon-blue there)
	var lm := StringName(args.get("lineup_map", "zr_barrens"))
	await _go(lm, &"barrens_shrine" if lm == &"zr_barrens" else &"start")
	var ids := DataEnemiesZarael.ids()
	var at0: Vector3 = Vector3(-40.0, 0.3, 66.0) if lm == &"zr_barrens" else Vector3(-35.0, 0.3, 44.0)
	var origin := Game.current_map.to_global(at0)
	var spawned := []
	for i in ids.size():
		var def := DB.enemy(ids[i])
		if def == null or not ResourceLoader.exists(def.model):
			print("BH029 monster missing model: ", ids[i])
			continue
		var row := i / 10
		var col := i % 10
		var at := origin + Vector3(-15.0 + col * 3.4, 0, -6.0 + row * 7.0)
		at = CombatQuery.ground_at(p.get_world_3d(), at + Vector3.UP * 6.0) + Vector3.UP * 0.05
		var e := Spawner.spawn_enemy(Game.current_map, def, 40, [], at, {})
		if e:
			e.set_physics_process(false)
			e.set_process(false)
			spawned.append(e)
	await _wait(30)
	var cam := Camera3D.new()
	Game.current_map.add_child(cam)
	cam.fov = 45.0
	cam.global_position = origin + Vector3(0, 16, 26)
	cam.look_at(origin + Vector3(0, 1, 0))
	cam.make_current()
	await _shot("90_monsters_lineup", 20)
	var n := 0
	for e in spawned:
		if not is_instance_valid(e):
			continue
		var ep: Vector3 = (e as Node3D).global_position
		var hgt := float((e as Enemy).def.body_height) * float((e as Enemy).def.model_scale)
		cam.global_position = ep + Vector3(0, hgt * 0.75 + 1.4, hgt * 1.3 + 3.2)
		cam.look_at(ep + Vector3(0, hgt * 0.5, 0))
		await _shot("91_monster_%02d_%s" % [n, (e as Enemy).def.id], 6)
		n += 1
	cam.queue_free()
	for e in spawned:
		if is_instance_valid(e):
			e.queue_free()

func _restored() -> void:
	Game.hero.world_flags[DataZarael.F_RESTORED] = true
	await _go(&"agdao", &"pier")
	await _view("95_agdao_restored_overview", "overview")
	await _view("96_agdao_restored_crown", "crown")
	await _view("97_agdao_restored_market", "market")

# ------------------------------------------------------------------------------------------------------------

func _place(at: Vector3, look: Vector3) -> void:
	var spot := CombatQuery.ground_at(p.get_world_3d(), at + Vector3.UP * 2.0)
	var d := (look - at).slide(Vector3.UP)
	p.global_transform = Transform3D(Basis(Vector3.UP, atan2(d.x, d.z)), spot + Vector3.UP * 0.05)
	p.velocity = Vector3.ZERO
	p.on_teleported()

func _orbit(label: String, target_local: Vector3, yaw: float, pitch: float, dist: float) -> void:
	var cam := Camera3D.new()
	Game.current_map.add_child(cam)
	cam.fov = 45.0
	var t := Game.current_map.to_global(target_local)
	var off := Vector3(0, sin(deg_to_rad(pitch)), cos(deg_to_rad(pitch))) * dist
	cam.global_position = t + off.rotated(Vector3.UP, deg_to_rad(yaw))
	cam.look_at(t)
	var prev := get_viewport().get_camera_3d()
	cam.make_current()
	await _shot(label, 20)
	if prev:
		prev.make_current()
	cam.queue_free()

## A shot from one of the map's named views (MapBuilder.view).
func _view(label: String, view_name: String) -> void:
	var v: Dictionary = Game.current_map.views.get(view_name, {})
	if v.is_empty():
		return
	var cam := Camera3D.new()
	Game.current_map.add_child(cam)
	cam.fov = float(v.fov)
	cam.far = 900.0
	var pitch := deg_to_rad(float(v.pitch))
	var off := Vector3(0, sin(pitch), cos(pitch)) * float(v.dist)
	off = off.rotated(Vector3.UP, deg_to_rad(float(v.yaw)))
	cam.global_position = Game.current_map.to_global(v.target + off)
	cam.look_at(Game.current_map.to_global(v.target), Vector3.UP if absf(float(v.pitch)) < 85.0 else Vector3.FORWARD)
	var prev := get_viewport().get_camera_3d()
	cam.make_current()
	await _shot(label, 20)
	if prev:
		prev.make_current()
	cam.queue_free()

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame

func _shot(label: String, frames := 8) -> void:
	await _wait(frames)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("BH029 SHOT ", label)

func _go(map_id: StringName, spawn: StringName) -> void:
	Game.travel(map_id, spawn)
	await _wait(5)
	for i in 1500:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == map_id:
			break
	p = Game.player as Player
	p.invulnerable = true
	await _wait(60)
