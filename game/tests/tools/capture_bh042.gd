extends Node
## bh-042 evidence run (real renderer, real boot scene with HUD).
##   godot --path game --resolution 1600x900 res://tests/tools/capture_bh042.tscn -- --class=knight --slot=97 --phase=<p> --out=<dir>
## phases: undercroft (the entrance in Malasugue and the five gates), floors (floor 1, a mid floor, the gatekeeper's hall
## and the sanctum of each dungeon), secret (a cracked wall before and after it breaks), bosses (all ten, side by side),
## fight (the bosses' Curse of Stillness, Armour Rip and bullet patterns, the Necro-Knight's aura), all.

var args := {}
var out := ""
var main: Node
var p: Player
var phase := "all"

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../output/bh-042/shots")))
	phase = String(args.get("phase", "all"))
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
	var lvl := int(args.get("level", "165"))
	h.progress.add_xp(maxi(0, XpCurve.total_xp_for_level(lvl) - h.progress.total_xp))
	QuakeBrain.spend_points(h)
	var rng := RandomNumberGenerator.new()
	rng.seed = 2042
	GuildSummons._gear_up(h, lvl, rng)
	h.tier = 6
	h.world_flags[&"boss_kethrax_defeated"] = true
	h.stats_dirty.emit()
	Game.ui_root.close_all()
	p.invulnerable = true
	if phase in ["undercroft", "all"]:
		await _undercroft()
	if phase in ["floors", "all"]:
		await _floors()
	if phase in ["secret", "all"]:
		await _secret()
	if phase in ["bosses", "all"]:
		await _bosses()
	if phase in ["fight", "all"]:
		await _fight()
	print("BH042 CAPTURE DONE -> ", out)
	get_tree().quit()

# ---- phases ---------------------------------------------------------------------------------------------------------

func _undercroft() -> void:
	await _go(&"sanctuary", &"door_int_delvers")
	await _shot("01_malasugue_undercroft_entrance", 60)
	await _go(&"int_delvers", &"start")
	await _shot("02_undercroft_inside", 60)
	await _view("03_undercroft_overview", "overview")
	var gate := Game.current_map.teleporter(DataDungeons.gate_id(&"throne_beneath"))
	if gate:
		_place(gate.global_position + Vector3(-4.0, 0, 2.0), gate.global_position)
		await _shot("04_undercroft_gate_throne", 40)

func _floors() -> void:
	var n := 10
	for id in DataDungeonsAbyss.ORDER:
		for f in [1, 7, DataDungeonsAbyss.GATEKEEPER_FLOOR, DataDungeons.floor_count(id)]:
			await _go(DataDungeons.map_id(id, f), &"arrival")
			Game.debug_freeze_ai = true
			print("BH042 %s floor %d enemies=%d lights=%d" % [id, f, get_tree().get_nodes_in_group(&"enemy").size(),
				Game.current_map.find_children("*", "OmniLight3D", true, false).size()])
			await _shot("%d_%s_f%02d" % [n, id, f], 40)
			if f == 7:
				await _view("%d_%s_f%02d_overview" % [n, id, f], "overview")
			n += 1
	Game.debug_freeze_ai = false

func _secret() -> void:
	var id: StringName = &"hollow_crown"
	for f in range(1, 6):
		await _go(DataDungeons.map_id(id, f), &"arrival")
		Game.debug_freeze_ai = true
		var walls := get_tree().get_nodes_in_group(&"secret_wall")
		if walls.is_empty():
			continue
		var w := walls[0] as SecretWall
		var front := w.global_position + (Vector3(0, 0, 3.2) if w.across_x else Vector3(3.2, 0, 0))
		_place(front, w.global_position)
		await _shot("40_secret_wall_cracked", 40)
		for i in SecretWall.BLOWS - 1:
			var req := DamageRequest.new()
			req.kind = DamageRequest.Kind.ATTACK
			w.receive_hit(req, p, w.center())
			await _wait(14)
		await _shot("41_secret_wall_giving", 6)
		var req2 := DamageRequest.new()
		req2.kind = DamageRequest.Kind.ATTACK
		w.receive_hit(req2, p, w.center())
		await _shot("42_secret_wall_broken", 18)
		await _shot("43_secret_room_open", 60)
		Game.debug_freeze_ai = false
		return

## Every boss of the Abyss in a row on the Throne Beneath's sanctum floor (AI frozen), then close-ups.
func _bosses() -> void:
	# the Glasswire Barrens by day: neutral light that shows the models as they are
	await _go(&"zr_barrens", &"start")
	Game.debug_freeze_ai = true
	for e in get_tree().get_nodes_in_group(&"enemy"):
		(e as Node).queue_free()
	await _wait(10)
	var ids := DataEnemiesAbyss.ids()
	var origin := p.global_position + Vector3(0, 0, -16)
	var made := []
	for i in ids.size():
		var def := DB.enemy(ids[i])
		var at := origin + Vector3(-27.0 + 6.0 * i, 0, 0)
		var e := Spawner.spawn_enemy(Game.current_map, def, 170, [], CombatQuery.ground_at(p.get_world_3d(), at + Vector3.UP * 4.0), {})
		made.append(e)
	await _wait(40)
	for e in made:
		(e as Enemy).rotation.y = 0.0
	var cam := Camera3D.new()
	Game.current_map.add_child(cam)
	cam.fov = 40.0
	cam.global_position = origin + Vector3(0, 13, 36)
	cam.look_at(origin + Vector3(0, 2.5, 0), Vector3.UP)
	cam.make_current()
	await _shot("50_bosses_lineup", 30)
	for i in made.size():
		var e: Enemy = made[i]
		var t := e.global_position + Vector3(0, e.def.body_height * 0.55, 0)
		cam.global_position = t + Vector3(e.def.body_height * 0.35, e.def.body_height * 0.35, e.def.body_height * 1.25 + 3.0)
		cam.look_at(t, Vector3.UP)
		await _shot("51_boss_%02d_%s" % [i + 1, e.def.id], 12)
	cam.queue_free()
	Game.debug_freeze_ai = false

## The bosses' signature moves, fired on the hero (invulnerable) so the patterns and markers show.
func _fight() -> void:
	await _go(DataDungeons.map_id(&"hollow_crown", DataDungeons.floor_count(&"hollow_crown")), &"arrival")
	for e in get_tree().get_nodes_in_group(&"enemy"):
		(e as Node).queue_free()
	await _wait(10)
	var shots := [[&"fallen_necro_knight", &"nk_soul_spiral", "60_necro_knight_soul_spiral"], [&"morvhaal", &"grave_rings", "61_morvhaal_grave_rings"],
		[&"ysolde", &"thousand_knives", "62_ysolde_thousand_knives"], [&"flayed_archivist", &"page_storm", "63_archivist_page_storm"],
		[&"kharzul", &"slag_waves", "64_kharzul_slag_waves"], [&"weeping_shroud", &"wail_orbit", "65_shroud_wail_orbit"],
		[&"rimehorn", &"blizzard_spiral", "66_rimehorn_blizzard_spiral"], [&"vaelgor", &"name_unspoken", "67_vaelgor_name_unspoken"],
		[&"thalassor", &"stillness", "68_thalassor_curse_of_stillness"], [&"gorehelm", &"armour_rip", "69_gorehelm_armour_rip"]]
	for row in shots:
		var def := DB.enemy(row[0])
		var at := p.global_position + Vector3(0, 0, -9)
		var e := Spawner.spawn_enemy(Game.current_map, def, 170, [], CombatQuery.ground_at(p.get_world_3d(), at + Vector3.UP * 4.0), {})
		await _wait(30)
		e.target = p
		e._face_now(p.global_position)
		var a := {}
		for x in def.attacks:
			if x.id == row[1]:
				a = x
		e.phase = 3
		p.invulnerable = String(a.kind) != "armor_rip"     # the rip must land to show its plates flying
		e.brain.go(EnemyBrain.State.CHASE)
		e._dist = e.global_position.distance_to(p.global_position)
		e._start_attack(a)
		var wait_s := 2.2 if String(a.kind) in ["barrage"] else (2.4 if String(a.kind) == "curse_zone" else 1.4)
		await _wait(int(wait_s * 60.0))
		await _shot(row[2], 1)
		if String(a.kind) == "armor_rip":
			print("BH042 armour ripped=", p.status.has(&"armor_ripped"))
		if String(row[0]) == "fallen_necro_knight":
			var cam := Camera3D.new()
			Game.current_map.add_child(cam)
			cam.fov = 38.0
			var t := e.global_position + Vector3(0, 1.2, 0)
			cam.global_position = t + Vector3(1.6, 1.5, 4.6)
			cam.look_at(t, Vector3.UP)
			cam.make_current()
			await _shot("59_necro_knight_closeup", 30)
			cam.queue_free()
		p.invulnerable = true
		p.heal(p.max_hp(), false)
		e.queue_free()
		for n in get_tree().get_nodes_in_group(&"curse_zone"):
			n.queue_free()
		await _wait(30)
	print("BH042 silenced test: stilled=", p.status.has(&"stilled"))

# ---- helpers ------------------------------------------------------------------------------------------------------------

func _place(at: Vector3, look: Vector3) -> void:
	var spot := CombatQuery.ground_at(p.get_world_3d(), at + Vector3.UP * 2.0)
	var d := (look - at).slide(Vector3.UP)
	p.global_transform = Transform3D(Basis(Vector3.UP, atan2(d.x, d.z)), spot + Vector3.UP * 0.05)
	p.velocity = Vector3.ZERO
	p.on_teleported()

func _view(label: String, view_name: String) -> void:
	var v: Dictionary = Game.current_map.views.get(view_name, {})
	if v.is_empty():
		return
	var cam := Camera3D.new()
	Game.current_map.add_child(cam)
	cam.fov = float(v.fov)
	var pitch := deg_to_rad(float(v.pitch))
	var off := Vector3(0, sin(pitch), cos(pitch)) * float(v.dist)
	off = off.rotated(Vector3.UP, deg_to_rad(float(v.yaw)))
	cam.global_position = v.target + off
	cam.look_at(v.target, Vector3.UP if absf(float(v.pitch)) < 85.0 else Vector3.FORWARD)
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
	print("BH042 SHOT ", label)

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
