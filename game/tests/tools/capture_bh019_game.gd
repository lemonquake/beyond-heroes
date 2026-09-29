extends Node
## bh-019 evidence in the real game (boot scene, HUD, real camera): Lape the Ancient and his trading table (dishes,
## appraisal, offers), the practice dummy with its damage board, the Hero's Vault, and each town quarter. `overhead`
## writes an orthographic top view of each quarter (plus a JSON of the view rectangle) for layout work.
##   godot --path game --resolution 1916x1011 res://tests/tools/capture_bh019_game.tscn -- --class=knight --slot=97 --out=<dir>
## Optional --only=overhead,quarters,lape,dummy,vault

var args := {}
var out := ""
var p: Player
var only: PackedStringArray = []

const QUARTERS := {
	&"sanctuary": Rect2(0.0, 6.0, 30.0, 32.0),
	&"olivar": Rect2(-20.0, 10.0, 30.0, 26.0),
	&"wyman_outpost": Rect2(-8.0, 8.0, 26.0, 24.0),
}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-019/evidence/shots")))
	only = String(args.get("only", "")).split(",", false)
	DirAccess.make_dir_recursive_absolute(out)
	var main: Node = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 1500:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(60)
	p = Game.player as Player
	Game.god_mode = true
	if _want("overhead"):
		await _overhead()
	if _want("quarters"):
		await _quarters()
	if _want("dummy"):
		await _dummy()
	if _want("lape"):
		await _lape()
	if _want("vault"):
		await _vault()
	print("BH019 GAME CAPTURE DONE -> ", out)
	get_tree().quit()

func _want(k: String) -> bool:
	return only.is_empty() or only.has(k)

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame

func _shot(label: String, frames := 10) -> void:
	await _wait(frames)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("BH019 SHOT ", label)

func _go(map_id: StringName, spawn: StringName = &"start") -> void:
	if Game.current_map_id == map_id:
		return
	Game.travel(map_id, spawn)
	await _wait(5)
	for i in 1500:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == map_id:
			break
	await _wait(60)

func _at(x: float, z: float, face := 180.0) -> void:
	p.teleport_to(Game.current_map.to_global(Vector3(x, 0.3, z)))
	p.rotation.y = deg_to_rad(face)

func _overhead() -> void:
	for m in QUARTERS:
		await _go(m)
		var r: Rect2 = QUARTERS[m]
		var cam := Camera3D.new()
		cam.projection = Camera3D.PROJECTION_ORTHOGONAL
		cam.size = r.size.y
		cam.keep_aspect = Camera3D.KEEP_HEIGHT
		cam.far = 200.0
		Game.current_map.add_child(cam)
		var c := r.get_center()
		cam.global_transform = Transform3D(Basis.from_euler(Vector3(-PI / 2.0, 0, 0)), Game.current_map.to_global(Vector3(c.x, 60.0, c.y)))
		var sun := DirectionalLight3D.new()
		sun.rotation_degrees = Vector3(-70, 30, 0)
		sun.light_energy = 1.4
		Game.current_map.add_child(sun)
		cam.make_current()
		_at(c.x + 999.0, c.y)
		await _wait(30)
		await _shot("overhead_%s" % m, 10)
		var vp := get_viewport().get_visible_rect().size
		var f := FileAccess.open(out.path_join("overhead_%s.json" % m), FileAccess.WRITE)
		f.store_string(JSON.stringify({"center": [c.x, c.y], "height_m": r.size.y, "px": [vp.x, vp.y]}))
		f.close()
		cam.queue_free()
		sun.queue_free()
		await _wait(5)

func _quarters() -> void:
	for m in QUARTERS:
		await _go(m)
		for s in DataTownRows.row(m).stands:
			if not (String(s.kind) in [DataTownRows.SHOP, DataTownRows.VAULT, DataTownRows.DUMMY]) or not s.get("bh019", false):
				continue
			var c := DataTownRows.customer_spot(s)
			_at(c.x, c.z + 1.4)
			await _wait(40)
			await _shot("stand_%s_%s" % [m, s.id], 10)

func _dummy() -> void:
	await _go(&"sanctuary")
	var d := get_tree().get_first_node_in_group(&"practice_target") as PracticeDummy
	if d == null:
		push_error("no practice dummy")
		return
	var lp := Game.current_map.to_local(d.global_position)
	_at(lp.x, lp.z + 1.8, 180.0)
	p.face_toward(d.global_position)
	await _wait(20)
	# real attacks through the input action; then, if none landed (mouse aim off to the side), plain hits
	for i in 16:
		p.auto_target = d
		p.face_toward(d.global_position)
		Input.action_press(&"primary")
		await _wait(6)
		Input.action_release(&"primary")
		await _wait(14)
	print("BH019 dummy hits from real attacks: ", d._bout_hits)
	if d._bout_hits == 0:
		for i in 12:
			var req := DamageRequest.new()
			req.kind = DamageRequest.Kind.ATTACK
			req.attacker = p.stats
			req.base_min = 40.0 + i * 3.0
			req.base_max = 60.0 + i * 3.0
			d.receive_hit(req, p)
			await _wait(12)
	await _shot("dummy_hits", 2)

func _hero_bag() -> void:
	var h := Game.hero
	h.progress.level = 18
	h.inventory.gold = 20000
	var rng := RandomNumberGenerator.new()
	rng.seed = 1919
	for pair in [[&"weapon", BH.Rarity.ELITE], [&"armor", BH.Rarity.ADVANCED], [&"accessory", BH.Rarity.MASTER], [&"helm", BH.Rarity.BASIC]]:
		var b := ItemGenerator.random_base(rng, 18, [pair[0]], &"", 0.0)
		if b:
			var it := ItemGenerator.generate(b, 18, int(pair[1]), rng)
			if pair[0] == &"weapon":
				it.sockets = 2
				it.gems = ["ember_shard", ""]
			h.inventory.add(it)

func _lape() -> void:
	_hero_bag()
	await _go(&"sanctuary")
	var s := DataTownRows.stand_of_npc(&"lape")
	if not s.is_empty():
		var c := DataTownRows.customer_spot(s)
		_at(c.x, c.z + 1.2)
		await _wait(45)
		await _shot("lape_stand", 10)
	Game.ui_root.open_lape()
	await _wait(20)
	await _shot("lape_window_empty", 5)
	var w := Game.ui_root.window(&"lape") as LapeWindow
	var n := 0
	for it in Game.hero.inventory.cells:
		if it != null and it.is_equipment() and n < 3 and it.rarity >= BH.Rarity.BASIC:
			w._lay(it, -1)
			n += 1
	await _wait(10)
	await _shot("lape_window_laid", 5)
	w._appraise()
	await _wait(20)
	await _shot("lape_window_offer", 5)
	w.close_window()
	await _wait(20)

func _vault() -> void:
	await _go(&"sanctuary")
	var v := get_tree().get_first_node_in_group(&"vault_point") as Node3D
	if v:
		var lp := Game.current_map.to_local(v.global_position)
		_at(lp.x, lp.z + 1.6)
		await _wait(45)
		await _shot("vault_stand", 10)
	Game.ui_root.open(&"vault")
	await _wait(20)
	var w := Game.ui_root.window(&"vault") as VaultWindow
	var k := 0
	for it in Game.hero.inventory.cells.duplicate():
		if it != null and k < 3:
			w._put(it, -1)
			k += 1
	await _wait(20)
	await _shot("vault_window", 5)
	w.close_window()
	await _wait(20)
