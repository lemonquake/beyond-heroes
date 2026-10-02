extends Node
## bh-031 in the running game: townsfolk on the hero body, a conversation with their ID portrait, a shop, the HUD's
## ID picture, a line of humanoid monsters, Olivar, Agdao, and the save cards.
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_bh031_game.tscn -- --class=knight --slot=97 --phase=town
## Phases: town, monsters, olivar, agdao, cards (cards does not boot a hero).

var args := {}
var out := ""

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-031/evidence")))
	DirAccess.make_dir_recursive_absolute(out)
	Settings.control_mode = "pc"
	if String(args.get("phase", "town")) == "cards":
		_cards.call_deferred()
		return
	add_child(load("res://src/main.gd").new())
	_run.call_deferred()

func _wait(s: float) -> void:
	await get_tree().create_timer(s, true, false, true).timeout

func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(name + ".png"))
	print("SHOT ", name)

func _run() -> void:
	for i in 900:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await get_tree().process_frame
	await _wait(2.0)
	match String(args.get("phase", "town")):
		"town": await _town()
		"monsters": await _monsters()
		"olivar": await _visit(&"olivar", [&"paul_david", &"corvin", &"elsbeth", &"aldous", &"wren", &"pip"])
		"agdao": await _visit(&"agdao", [&"terax", &"wirekeeper", &"caius", &"ysenne", &"brisa", &"dorrit"])
	get_tree().quit()

func _near(id: StringName, dist := 3.2) -> Npc:
	var n := NpcDirectory.find(id)
	if n == null:
		return null
	var p: Player = Game.player
	var fwd := n.global_transform.basis.z
	p.global_position = n.global_position + fwd * dist
	p.velocity = Vector3.ZERO
	p.look_at(n.global_position, Vector3.UP)
	return n

func _town() -> void:
	var p: Player = Game.player
	await _wait(1.0)
	# the ID picture on the HUD (taken from the hero's own model a moment after arriving)
	await _shot("hud_id_picture")
	var n := _near(&"maelis", 4.5)
	await _wait(1.2)
	await _shot("town_maelis_world")
	if n:
		n.interact(p)
		await _wait(2.5)
		await _shot("dialogue_maelis")
		Game.ui_root.close_all() if Game.ui_root.has_method(&"close_all") else null
		n.end_talk()
	for pair in [[&"brannoc", "town_brannoc"], [&"hald", "town_hald"], [&"seris", "town_seris"]]:
		var m := _near(pair[0], 4.0)
		await _wait(1.0)
		await _shot(pair[1])
		if m and pair[0] == &"brannoc":
			m.interact(p)
			await _wait(2.0)
			await _shot("dialogue_brannoc")
			m.end_talk()
	print("BH031_TOWN_DONE")

func _visit(map: StringName, ids: Array) -> void:
	Game.travel(map, &"start")
	for i in 900:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map and Game.current_map.def.id == map:
			break
	await _wait(3.0)
	for id in ids:
		var n := _near(id, 4.0)
		if n == null:
			continue
		await _wait(1.0)
		await _shot("%s_%s" % [map, id])
	var first := NpcDirectory.find(ids[0])
	if first:
		_near(ids[0], 3.0)
		first.interact(Game.player)
		await _wait(2.5)
		await _shot("dialogue_%s" % ids[0])

func _monsters() -> void:
	Game.debug_freeze_ai = true
	var p: Player = Game.player
	var ids := [&"bandit_cutthroat", &"hollow_soldier", &"ashen_cultist", &"orc_reaver", &"goblin_skulker", &"drowned_deckhand",
		&"cinder_imp", &"chain_bearer", &"ogre_crusher"]
	var cam0 := get_viewport().get_camera_3d()
	var up := (-cam0.global_transform.basis.z).slide(Vector3.UP).normalized()
	var side := cam0.global_transform.basis.x.slide(Vector3.UP).normalized()
	var i := 0
	var mid := p.global_position + up * 3.5
	for id in ids:
		var e := Enemy.new()
		e.setup(DB.enemy(id), 10)
		Game.current_map.add_child(e)
		e.global_position = mid + side * (float(i) - (ids.size() - 1) * 0.5) * 1.7
		var face := e.global_position - up * 5.0
		e.look_at(Vector3(face.x, e.global_position.y, face.z), Vector3.UP)
		e.rotate_y(PI)
		i += 1
	await _wait(2.5)
	await _shot("monsters_line_game_camera")
	# a closer look from the front (a camera of our own; the game's follows the hero)
	var cam := Camera3D.new()
	cam.fov = 40.0
	Game.current_map.add_child(cam)
	cam.global_position = mid - up * 9.0 + Vector3.UP * 2.6
	cam.look_at(mid + Vector3.UP * 1.1)
	cam.make_current()
	await _wait(0.5)
	await _shot("monsters_line_close")
	print("BH031_MONSTERS_DONE")

func _cards() -> void:
	get_window().size = Vector2i(1280, 900)
	var bg := ColorRect.new()
	bg.color = Color("15191f")
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var v := VBoxContainer.new()
	v.position = Vector2(40, 40)
	v.custom_minimum_size = Vector2(1200, 0)
	add_child(v)
	v.theme = UITheme.theme()
	for s in SaveSystem.SLOTS:
		v.add_child(MainMenu.slot_card(s, func(_s): pass, Callable()))
	for f in 120:
		await get_tree().process_frame
	await _shot("save_cards")
	get_tree().quit()
