extends Node
## bh-015 evidence run (real renderer, real boot scene with HUD): HUD layout across maps and window sizes (the minimap
## pushed off screen), the minimap overhaul, generated names, the new weapons.
##   godot --path game --resolution 1916x1011 res://tests/tools/capture_bh015.tscn -- --class=knight --slot=97 --out=<dir>
## Optional --only=layout,minimap,names,weapons

var args := {}
var out := ""
var main: Node
var p: Player
var only: PackedStringArray = []

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-015/evidence/shots")))
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
	if _want("layout"):
		await _layout()
	if _want("minimap"):
		await _minimap()
	if _want("names"):
		await _names()
	if _want("weapons"):
		await _weapons()
	print("BH015 CAPTURE DONE -> ", out)
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
	print("BH015 SHOT ", label)

func _go(map_id: StringName, spawn: StringName) -> void:
	Game.travel(map_id, spawn)
	await _wait(5)
	for i in 1200:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == map_id:
			break
	await _wait(60)

func _hud() -> Hud:
	return Game.ui_root.hud if Game.ui_root and "hud" in Game.ui_root else null

func _report(tag: String) -> void:
	var h := _hud()
	var vp := get_viewport().get_visible_rect()
	var r: Rect2 = h._top_right.get_global_rect()
	var mm := h.minimap_rect()
	print("BH015 LAYOUT %s vp=%s col=%s minimap=%s inside=%s" % [tag, vp.size, r, mm, vp.encloses(mm.grow(-1))])

func _layout() -> void:
	_report("start")
	await _shot("layout_town")
	await _go(&"dg_warren_1", &"arrival")
	_report("warren")
	await _shot("layout_warren")
	# minimise and restore the window
	if DisplayServer.get_name() != "headless":
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_MINIMIZED)
		await _wait(30)
		_report("minimised")
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		await _wait(30)
		_report("restored")
		await _shot("layout_restored")

func _mm() -> MiniMap:
	return _hud()._minimap

## Zoom without touching the player's settings.cfg (MiniMap.set_zoom saves it).
func _zoom(i: int) -> void:
	_mm()._zoom_i = i
	await _wait(50)

func _crop_mm(label: String) -> void:
	await _wait(4)
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var r := _hud().minimap_rect()
	var s := get_viewport().get_visible_rect().size
	var k := float(img.get_width()) / s.x
	var rr := Rect2i(Vector2i((r.position - Vector2(70, 10)) * k), Vector2i((r.size + Vector2(94, 64)) * k))
	rr = rr.intersection(Rect2i(Vector2i.ZERO, img.get_size()))
	var crop := img.get_region(rr)
	crop.resize(crop.get_width() * 2, crop.get_height() * 2, Image.INTERPOLATE_LANCZOS)
	crop.save_png(out.path_join(label + ".png"))
	print("BH015 SHOT ", label)

func _ally(peer: int, nm: String, pos: Vector3, yaw: float, hp_frac := 1.0, fallen := false, tempo := false) -> NetAvatar:
	var a := NetAvatar.new().setup(peer, "t1" if tempo else "p", {"name": nm, "lvl": 6, "mhp": 200.0, "hp": 200.0 * hp_frac})
	Game.current_map.add_child(a)
	a.global_position = pos
	a.rotation.y = yaw
	a._target_pos = pos
	a._target_yaw = yaw
	a.hp = 200.0 * hp_frac
	if fallen:
		a.alive = false
	return a

func _minimap() -> void:
	var mm := _mm()
	print("BH015 QUEST before: ", Objectives.current(Game.hero).get("id", ""))
	mm._quest.resolve()
	print("BH015 QUEST has=%s final=%s path=%d world=%s hero=%s legs=%s" % [mm._quest.has, mm._quest.final, mm._quest.path.size(), mm._quest.world, p.global_position,
		(mm._quest._plan.get("legs", []) as Array).map(func(l): return "%s:%s:%d" % [l.kind, l.map, (l.get("points", []) as Array).size()])])
	for i in [1, 0, 2]:
		await _zoom(i)
		mm._quest.invalidate()
		await _wait(20)
		await _crop_mm("mm_town_zoom%d" % i)
	await _zoom(1)
	await _shot("mm_town_full")
	# hover a townsperson: the name appears
	for poi in mm._pois:
		if poi.kind == "shop" and poi.node:
			var q: Vector2 = mm._to_map(poi.node.global_position)
			if (q - mm._markers.size * 0.5).length() < mm._lim():
				mm._hover = q
				break
	await _wait(10)
	await _crop_mm("mm_town_hover")
	mm._hover = Vector2(-1, -1)
	# the party: one close, one far (on the rim), one fallen, a Tempo of theirs, and two pings
	var h := p.global_position
	_ally(2, "Taicho", h + Vector3(6, 0, -4), 0.8)
	_ally(3, "Greg", h + Vector3(60, 0, 25), -1.2)
	_ally(4, "Mirelle", h + Vector3(-8, 0, 7), 0.0, 0.0, true)
	_ally(2, "Taicho's Tempo", h + Vector3(8, 0, -2), 0.0, 1.0, false, true)
	_ally(3, "Low Health Friend", h + Vector3(-5, 0, -9), 2.5, 0.2)
	Net.show_ping(h + Vector3(3, 0, 9), "Taicho", Net.player_color(2))
	Net.show_ping(h + Vector3(-70, 0, -30), "Greg", Net.player_color(3))
	await _wait(30)
	await _crop_mm("mm_party")
	await _shot("mm_party_full")
	for a in get_tree().get_nodes_in_group(&"net_ally"):
		a.queue_free()
	# a fight on a combat map: camps, elites, champions, a tracked route
	await _go(&"ruined_forest", &"arrival")
	p = Game.player as Player
	await _zoom(2)
	await _crop_mm("mm_forest_wide")
	await _shot("mm_forest_full")
	Routes.set_route("rf_gate")
	await _wait(60)
	await _crop_mm("mm_forest_route")
	Routes.clear_route()
	await _go(&"dg_warren_1", &"arrival")
	p = Game.player as Player
	await _zoom(1)
	await _crop_mm("mm_warren")
	await _shot("mm_warren_full")

## The starter Tempo's rolled name in its frame and the guide.
func _names() -> void:
	print("BH015 STARTER ", Game.hero.starter_name)
	Game.open_intro()
	await _wait(40)
	await _shot("names_guide")
	Game.ui_root.dialogue.close()
	await _wait(10)

## New weapons on the ground (their models, forged names by rarity), then one of each type in the hero's hands.
func _weapons() -> void:
	await _go(&"ruined_forest", &"arrival")
	p = Game.player as Player
	for e in get_tree().get_nodes_in_group(&"enemy"):
		e.queue_free()
	var ids := [&"kingsbane", &"wavecrest_flamberge", &"sunreaver", &"skyrender", &"dawnspire_lance", &"heavenfall_pilum",
		&"starhammer", &"nightwhisper", &"wyrmqueen_talons", &"dawnfist_gauntlets", &"frostwing_bow", &"sunspire_staff", &"hoarfrost_wand"]
	var r := RandomNumberGenerator.new()
	for i in ids.size():
		r.seed = 4242 + i
		var rar: int = [BH.Rarity.COMMON, BH.Rarity.BASIC, BH.Rarity.ADVANCED, BH.Rarity.LICENSED][i % 4]
		var it := ItemGenerator.generate(DB.item_base(ids[i]), 40, rar, r)
		print("BH015 WEAPON %s -> %s" % [ids[i], it.display_name()])
		Loot.spawn_item(it, p.global_position, TAU * i / ids.size(), 3.2 + (i % 2) * 1.6)
	await _wait(90)
	await _shot("weapons_ground")
