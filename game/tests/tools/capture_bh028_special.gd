extends Node
## bh-028 evidence run (real renderer, real boot scene with HUD): the rift on the Sanctuary Terrace, The Sundered Reach
## and its five gates, and the first floor and sanctum of each special dungeon.
##   godot --path game --resolution 1600x900 res://tests/tools/capture_bh028_special.tscn -- --class=knight --slot=97 --out=<dir>

var args := {}
var out := ""
var main: Node
var p: Player

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-028/evidence/special")))
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
	h.progress.add_xp(maxi(0, XpCurve.total_xp_for_level(95) - h.progress.total_xp))
	QuakeBrain.spend_points(h)
	var rng := RandomNumberGenerator.new()
	rng.seed = 2028
	GuildSummons._gear_up(h, 95, rng)
	h.world_flags[&"boss_kethrax_defeated"] = true
	h.tier = 5
	h.stats_dirty.emit()
	Game.ui_root.close_all()
	p.invulnerable = true
	# the rift beside the waypoint, open now that Kethrax has fallen
	await _go(&"sanctuary", &"waypoint")
	var rift := Game.current_map.teleporter(&"sanctuary_rift")
	print("BH028S rift ", rift != null, " locked=", rift.is_locked() if rift else true)
	_place(rift.global_position + Vector3(-3.0, 0, 5.5), rift.global_position)
	await _shot("10_terrace_rift_open", 90)
	# The Sundered Reach
	await _go(&"sundered_reach", &"arrival")
	await _shot("11_reach_arrival", 60)
	await _view("12_reach_overview", "overview")
	await _view("13_reach_gates", "gates")
	# a Class B hero is turned away at a gate
	var gate := Game.current_map.teleporter(DataDungeons.gate_id(&"aetherreach"))
	h.tier = 4
	_place(gate.global_position + (Vector3.ZERO - gate.global_position).normalized() * 3.0, gate.global_position)
	await _wait(20)
	_place(gate.global_position + Vector3(0, 0.3, 0), gate.global_position + Vector3(0, 0, 1))
	print("BH028S class B locked=", gate.is_locked(), " text=", gate.lock_text())
	await _shot("14_gate_class_b_turned_away", 30)
	h.tier = 5
	var n := 15
	for id in DataDungeonsSpecial.ORDER:
		await _go(DataDungeons.map_id(id, 1), &"arrival")
		print("BH028S %s floor 1 enemies=%d" % [id, get_tree().get_nodes_in_group(&"enemy").size()])
		await _shot("%d_%s_floor1" % [n, id], 60)
		n += 1
		var last := DataDungeons.floor_count(id)
		await _go(DataDungeons.map_id(id, last), &"arrival")
		await _view("%d_%s_sanctum_overview" % [n, id], "overview")
		n += 1
	print("BH028S CAPTURE DONE -> ", out)
	get_tree().quit()

func _place(at: Vector3, look: Vector3) -> void:
	var spot := CombatQuery.ground_at(p.get_world_3d(), at + Vector3.UP * 2.0)
	var d := (look - at).slide(Vector3.UP)
	p.global_transform = Transform3D(Basis(Vector3.UP, atan2(d.x, d.z)), spot + Vector3.UP * 0.05)
	p.velocity = Vector3.ZERO
	p.on_teleported()

## A shot from one of the map's named views (MapBuilder.view).
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
	print("BH028S SHOT ", label)

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
